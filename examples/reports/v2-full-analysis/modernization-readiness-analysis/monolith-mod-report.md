# Modernization Readiness Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | monolith |
| **Date** | 2025-07-17 |
| **Repo Type** | application |
| **Priority** | P0 |
| **Tags** | monolith, php, containers |
| **Context** | PHP monolith with Docker and CloudFormation on App Runner — containerize and expose inventory APIs the agent needs for restocking decisions. |
| **Overall Score** | **1.90 / 4.0** |

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 2.55 / 4.0 | 🟡 Partial |
| Application Architecture (APP) | 1.33 / 4.0 | ❌ Not Present |
| Data Platform Modernization (DATA) | 2.50 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 2.00 / 4.0 | 🟠 Needs Work |
| Operations & Observability (OPS) | 1.11 / 4.0 | ❌ Not Present |
| **Overall** | **1.90 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | APP-Q2: Monolith vs Microservices | 1 | Tightly-coupled monolith — all business logic in a single `index.php` with shared MySQL database, no module boundaries, pervasive shared state. | Blocks independent scaling, deployment, and team autonomy. Primary trigger for Move to Cloud Native pathway. Prevents exposing clean inventory APIs for agent restocking decisions. |
| 2 | INF-Q11: CI/CD Automation | 1 | No CI/CD pipeline exists. `deploy.sh` is a manual `docker-compose` script for local deployment only. | Manual deployments are error-prone, slow, and block modern DevOps practices. Primary trigger for Move to Modern DevOps pathway. |
| 3 | OPS-Q1–Q8: Operations & Observability (multiple) | 1 | No distributed tracing, no SLOs, no business metrics, no alerting, no deployment strategy, no integration tests, no runbooks, no observability ownership. | Complete absence of operational practices. Cannot detect or respond to issues. Blind to system health and business outcomes. |
| 4 | APP-Q3: Async vs Sync Communication | 1 | All communication is synchronous HTTP request-response. No message queues, no event-driven patterns. | Tight coupling, cascading failure risk, no decoupled processing for long-running operations like order fulfillment. |
| 5 | SEC-Q4: Centralized Identity Integration | 1 | Application manages its own authentication entirely — `users` table with bcrypt passwords and PHP sessions. No Cognito, OIDC, or SAML integration. | Security risk from isolated auth system. Cannot integrate with enterprise SSO. Blocks unified access policies for agent identity. |

---

## Quick Agent Wins

### Data Query Agent

- **Prerequisite:** DATA-Q2 ≥ 2 (scored 2) and database with clear, documented schema detected.
- **Evidence:** The `init_db()` function in `index.php` defines 9 well-structured tables (`orders`, `order_items`, `inventory`, `payments`, `returns`, `interactions`, `order_status_history`, `warehouses`, `users`) with clear column names, types, foreign keys, and indexes. The `get_db()` function provides a centralized PDO connection.
- **What it enables:** A natural-language-to-SQL agent that can query inventory levels, order status, warehouse capacity, and customer history — directly supporting the restocking decisions mentioned in the project context. For example, an agent could answer "Which products have stock below 10?" or "Show orders pending fulfillment at Seattle warehouse."
- **Additional steps:** Generate a schema documentation file from the `init_db()` DDL statements. Consider read-replica for agent queries to avoid production load. Add row-level security to prevent agent from accessing sensitive fields (passwords, payment details).
- **Effort:** Medium — schema is clear but needs documentation generation and access controls before agent integration.

> **Note:** The remaining 5 Quick Agent Win prerequisites are not met:
> - **API-aware agent** (APP-Q5 ≥ 2): APP-Q5 = 1 — no API versioning or OpenAPI spec exists.
> - **DevOps agent** (INF-Q11 ≥ 2): INF-Q11 = 1 — no CI/CD pipeline to orchestrate.
> - **RAG knowledge agent** (documentation exists): No README, wiki, or documentation files found in the repository.
> - **Workflow automation agent** (INF-Q3 ≥ 2): INF-Q3 = 1 — no workflow orchestration service.
> - **Observability agent** (OPS-Q1 ≥ 2): OPS-Q1 = 1 — no distributed tracing or structured logging.
>
> Address the gaps identified in this analysis — particularly CI/CD pipeline creation (INF-Q11), API documentation (APP-Q5), and observability instrumentation (OPS-Q1) — to unlock additional agent opportunities.

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | **Triggered** | High | High | APP-Q2 = 1 (monolith), APP-Q3 = 1 (all sync), APP-Q4 = 1 (no async processing) |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1 = 3 — compute already on managed App Runner with Docker containers. Contextual guard: App Runner is managed compute. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 (no stored procedures). MySQL is already open source. No commercial DB engines detected. |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 = 3 — production database is already managed RDS MySQL with Multi-AZ, encryption, and automated backups. |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 = 1 but no data processing workloads (ETL, streaming, analytics) exist. Contextual guard prevents trigger. |
| 6 | Move to Modern DevOps | **Triggered** | High | Medium | INF-Q11 = 1 (no CI/CD), OPS-Q5 = 1 (direct deployment), OPS-Q6 = 1 (no integration tests) |
| 7 | Move to AI | **Triggered** | Medium | Medium | Context mentions "agent needs for restocking decisions" (AI signal: "agent"). No AI/agent frameworks, no vector DB, no RAG patterns found. |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:**
The application is a tightly-coupled monolith (APP-Q2 = 1). All business logic — orders, inventory, payments, returns, shipping/fulfillment, user management, warehouse assignment, and quality checks — resides in a single `index.php` file (~2,400 lines). There are no module boundaries, no separation of concerns beyond inline code comments, and a single shared MySQL database serves all domains. The UI (HTML/CSS/JS) is also embedded directly in the PHP file.

**Compute Model:**
Compute is on AWS App Runner (INF-Q1 = 3), which is already managed. However, all domains scale together as a single unit — the inventory API and the fulfillment workflow share the same compute allocation. This prevents independent scaling of high-traffic read endpoints (e.g., product catalog) from write-heavy operations (e.g., order processing).

**Communication Pattern Gaps:**
- All inter-domain communication is synchronous function calls within a single process (APP-Q3 = 1).
- All operations are blocking — return processing, fulfillment steps, and payment processing all happen synchronously (APP-Q4 = 1).
- The order creation endpoint performs inventory check → order insert → item inserts → inventory deduction → payment processing → status update in a single database transaction.

**Recommended Decomposition Approach:**
See the [Decomposition Strategy](#decomposition-strategy) section below for detailed approach options, pattern recommendations, and effort estimates.

**Representative AWS Services (aligned with preferences):**
- **Amazon EKS** — Container orchestration for decomposed microservices (preferred over ECS per technology preferences)
- **Amazon API Gateway** — Entry point with throttling, authentication, and request validation for each service (preferred)
- **Amazon EventBridge** — Async event-driven communication between services (preferred over self-managed Kafka)
- **Amazon Aurora MySQL** — Managed database per service where needed (preferred, drop-in MySQL compatible)
- **Amazon DynamoDB** — For services needing key-value access patterns (e.g., inventory stock levels, session management) (preferred)
- **AWS Step Functions** — Orchestrate multi-step fulfillment workflows (validate → assign warehouse → pick → pack → QC → ship)
- **Amazon Bedrock** — AI agent for restocking decisions once inventory APIs are exposed (preferred)

**Recommended Patterns:**
- [Strangler Fig](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) — Incrementally extract services while keeping the monolith running
- [Anti-corruption Layer](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) — Isolate new services from monolith data model
- [Saga Pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga.html) — Distributed transactions for order→payment→inventory
- [Event Sourcing](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/event-sourcing.html) — Order status history (already tracked in `order_status_history` table)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10 = 3):**
CloudFormation (`infrastructure/monolith-apprunner.yaml`) covers: VPC, subnets, security groups, RDS, App Runner, ECR, WAF, IAM roles, auto-scaling, KMS keys, VPC Flow Logs. This is good coverage for infrastructure provisioning. However, the IaC does not include CI/CD pipeline definitions, monitoring/alerting resources, or operational runbooks.

**Current CI/CD State (INF-Q11 = 1):**
No CI/CD pipeline exists. The only deployment mechanism is `deploy.sh`, which runs `docker-compose build` and `docker-compose up -d` for local development. The CloudFormation outputs include manual `aws ecr` and `aws cloudformation update-stack` commands — all manual, error-prone steps. No `.github/workflows/`, no `buildspec.yml`, no `Jenkinsfile`, no `GitLab CI` configuration.

**Deployment Strategy Gaps (OPS-Q5 = 1):**
Direct-to-production deployment with no staged rollout. No blue/green, no canary, no rolling updates. No automated rollback capability.

**Testing Gaps (OPS-Q6 = 1):**
Zero test files in the repository. No unit tests, no integration tests, no API contract tests. No test framework configured. This creates high regression risk during any modernization effort.

**Recommended DevOps Toolchain (aligned with preferences):**

1. **Terraform** (preferred over CloudFormation) — Migrate IaC to Terraform for multi-provider support, state management, and module reuse. Start with `terraform import` of existing CloudFormation resources.
2. **GitOps with ArgoCD or Flux** (preferred) — Declarative deployment automation. Git as the single source of truth for desired state.
3. **GitHub Actions** — CI pipeline with build, test, security scan, and container image push stages.
4. **Amazon ECR** — Container registry (already provisioned with image scanning).
5. **AWS CodeDeploy** — Blue/green deployments for EKS workloads when the architecture evolves.

**Recommended Implementation Order:**
1. **Week 1–2:** Set up GitHub Actions pipeline with `docker build`, `docker push` to ECR, and `aws cloudformation deploy`.
2. **Week 3–4:** Add PHPUnit test framework and write integration tests for critical API endpoints.
3. **Week 5–6:** Add security scanning (Semgrep for SAST, `composer audit` for dependencies, ECR image scanning gate).
4. **Week 7–8:** Migrate CloudFormation to Terraform. Implement GitOps deployment model.
5. **Ongoing:** Add blue/green deployment strategy as architecture evolves toward EKS.

---

### Pathway: Move to AI

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**AI Intent Confirmation:**
The service context explicitly mentions "agent needs for restocking decisions" — the term "agent" is an AI-related signal term. AI/agent intent is confirmed.

**Current AI/Agent Infrastructure State:**
- **AI/Agent Frameworks:** None detected. No imports of Bedrock SDK, LangChain, Strands, OpenAI, or any AI framework in `index.php`.
- **Vector Database:** None. No OpenSearch, Pinecone, pgvector, or vector DB infrastructure.
- **RAG Implementation:** None. No embedding generation, vector store queries, or retrieval chains.
- **Agent Evaluation:** None. No Ragas, DeepEval, or evaluation harness.

**Application Domain and AI Use Cases:**
The e-commerce monolith has rich business data and clear decision points that are ideal for AI agent integration:

1. **Inventory Restocking Agent** (primary use case from context) — An agent that monitors inventory levels via the `/api/products` endpoint and triggers restocking orders when stock falls below thresholds. The `inventory` table already tracks `stock_quantity` per product.
2. **Order Fulfillment Agent** — The fulfillment workflow (validate → assign warehouse → pick → pack → QC → ship) is currently fully manual. An agent could automate warehouse assignment (using the `/api/warehouses/assignment-options` endpoint data) and shipping carrier selection (using `/api/carriers/shipping-options` endpoint data).
3. **Fraud Detection Agent** — The `/api/orders/{orderId}/validation-data` endpoint already computes fraud scores and risk factors. An agent could automate validation decisions for low-risk orders.
4. **Returns Processing Agent** — Returns currently require "manual CS review (24-48 hours)" as noted in the UI. An agent could auto-approve returns matching clear policies.

**Foundation Requirements (what needs to be in place first):**
- **API Documentation:** Generate OpenAPI spec from existing API routes (APP-Q5 = 1, no API docs exist). This is prerequisite for agent tool discovery.
- **API Gateway with Auth:** Add API Gateway with OAuth2/JWT auth (SEC-Q3 = 2, currently session-based). Agents cannot use session-based auth.
- **CI/CD Pipeline:** Establish automated deployment (INF-Q11 = 1) before adding AI services.
- **Observability:** Add distributed tracing (OPS-Q1 = 1) to monitor agent interactions.

**Quick Wins (see Quick Agent Wins section above):**
The Data Query Agent is the most immediately actionable AI integration — the database schema is well-defined and the `get_db()` function provides a centralized connection point.

**Representative AWS Services (aligned with preferences):**
- **Amazon Bedrock** (preferred) — Foundation models for restocking decisions, fraud analysis, and returns processing
- **Amazon Bedrock AgentCore** — Agent runtime for tool-use agents that call existing API endpoints
- **Amazon DynamoDB** (preferred) — Agent session state and conversation history
- **Amazon API Gateway** (preferred) — Expose inventory and fulfillment APIs as agent tools with proper auth
- **Amazon EventBridge** (preferred) — Event-driven triggers for inventory threshold alerts

## Decomposition Strategy

> **Condition met:** APP-Q2 = 1 (tightly-coupled monolith with no clear module boundaries).

### Recommended Approach: Strangler Fig (Parallel Track)

| Approach | Description | When to Use | Level of Effort | Recommendation |
|----------|-------------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | Incrementally extract services from the monolith while keeping the monolith running. New features are built as services; existing features are migrated over time. | The monolith has recognizable business domains despite being in a single file. Team can sustain parallel development. | **Medium to High** — 6–18 months depending on monolith size. | ✅ **Recommended.** Lowest risk, incremental value delivery. |
| **Conditional / Adaptive** | Containerize the monolith as-is (already done via App Runner), then selectively extract high-value services based on business priority. | Team has limited capacity for full decomposition. Quick wins needed first. | **Low to Medium** — selective extraction over 3–12 months. | ✅ **Alternative if capacity is constrained.** |
| **Big-Bang Rewrite** | Rewrite the entire application as microservices from scratch. | Almost never. Only when monolith is truly unmaintainable. | **Very High** — 12–24+ months. | ⚠️ **Recommended against.** The monolith is functional; Strangler Fig is safer. |

### Candidate Service Boundaries

Based on analysis of API routes, database tables, and business domains in `index.php`:

| Service | Extracted From | Database Tables | Key API Endpoints | Priority |
|---------|---------------|-----------------|-------------------|----------|
| **Inventory Service** | Product catalog & stock management | `inventory` | `GET /api/products` | **P0** — Required for agent restocking decisions |
| **Order Service** | Order creation, status tracking | `orders`, `order_items`, `order_status_history` | `POST /api/orders`, `GET /api/orders/me`, `GET /api/orders/{id}/history` | P1 |
| **Fulfillment Service** | Warehouse assignment, picking, packing, QC, shipping | `warehouses` + order status transitions | `POST /api/orders/{id}/assign-warehouse`, `/pick`, `/pack`, `/quality-check`, `/ship` | P1 |
| **Payment Service** | Payment processing, refunds | `payments` | Embedded in order creation and return approval | P2 |
| **Returns Service** | Return requests, approval workflow | `returns`, `interactions` | `POST /api/returns`, `POST /api/admin/approve-return` | P2 |
| **User/Auth Service** | Authentication, user management | `users` | `POST /login`, `GET /api/admin/users`, CRUD endpoints | P2 |

### Pattern Recommendations

| Pattern | Purpose | When to Apply | AWS Prescriptive Guidance |
|---------|---------|---------------|---------------------------|
| **Anti-corruption Layer (ACL)** | Isolate extracted services from the monolith's data model. The monolith's 9-table shared schema should not leak into new services. | Every extraction — place an ACL between the new service and the monolith. | [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) |
| **Saga Pattern** | The order creation flow currently does inventory check → order insert → payment processing → inventory deduction in a single DB transaction. When Order, Payment, and Inventory become separate services, this must become a distributed saga. | When extracting Order, Payment, and Inventory services. | [Saga pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga.html) |
| **Event Sourcing** | The `order_status_history` table already captures state transitions. Formalize this as event sourcing for the Order and Fulfillment services. | Order and Fulfillment service extraction. Enables audit trails and event-driven integration via EventBridge (preferred). | [Event sourcing pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/event-sourcing.html) |
| **Hexagonal Architecture** | Structure each new service with clear ports and adapters. Ensures testability and decoupling from infrastructure. | Every new service — use this as the internal architecture template. | [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |

### Calibrated Effort Estimate

| Factor | Analysis | Impact on Effort |
|--------|-----------|-----------------|
| Module boundaries | APP-Q2 = 1 — No module structure; all code in single file. Business domains identifiable only by inline comments and route grouping. | **High effort** — Boundaries must be identified and enforced from scratch. |
| Data coupling | DATA-Q2 = 2 — Single shared MySQL database with 9 tables. Cross-domain queries exist (e.g., joins between `orders`, `order_items`, and `inventory`). | **High effort** — Database-per-service requires data migration, query rewriting, and eventual consistency handling. |
| Stored procedures | DATA-Q4 = 4 — No stored procedures. All logic in PHP. | **Low effort** — No database logic extraction needed. Clean separation possible. |
| Communication patterns | APP-Q3 = 1 — All synchronous. | **Medium effort** — Must introduce async patterns (EventBridge preferred) for inter-service communication. |
| CI/CD maturity | INF-Q11 = 1 — No pipeline. | **High risk** — Must establish CI/CD before decomposition to support multi-service deployment. |
| Test coverage | OPS-Q6 = 1 — Zero tests. | **High risk** — No safety net for regression during extraction. Must add tests as a prerequisite. |

**Overall Effort Estimate:** **12–18 months** for full decomposition using Strangler Fig approach. Recommend starting with Inventory Service extraction (P0 — enables agent restocking decisions) while building CI/CD pipeline and test coverage in parallel.

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Production compute uses AWS App Runner (`AWS::AppRunner::Service` in `infrastructure/monolith-apprunner.yaml`), which is a fully managed container service. App Runner pulls images from ECR, handles TLS termination, and auto-scales. Local development uses `docker-compose` with self-managed containers. The Dockerfile builds a PHP 8.2 Apache image. |
| **Gap** | App Runner is managed but limited in orchestration capabilities compared to EKS. All domains share a single compute unit — no independent scaling per service. Local development environment uses raw `docker-compose` (not managed). |
| **Recommendation** | When decomposing into microservices, migrate to **Amazon EKS** (preferred) for full container orchestration with service mesh, advanced deployment strategies, and per-service scaling. Continue using App Runner for the monolith during the transition period. |
| **Evidence** | `infrastructure/monolith-apprunner.yaml` — `AppRunnerService` resource; `Dockerfile` — PHP 8.2 Apache image; `docker-compose.yml` — local development setup |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Production database is RDS MySQL 8.4.8 (`AWS::RDS::DBInstance` in CloudFormation) with: `MultiAZ: true`, `StorageEncrypted: true`, `BackupRetentionPeriod: 7`, `AutoMinorVersionUpgrade: true`, `DeletionProtection: true`, `EnableIAMDatabaseAuthentication: true`, custom port 3307, enhanced monitoring (`MonitoringInterval: 60`). Local development uses self-managed MySQL 8.0 in docker-compose. |
| **Gap** | Production RDS is well-configured. The local docker-compose MySQL is self-managed but only for development. No read replicas configured. Single database for all domains (shared state risk). |
| **Recommendation** | Migrate to **Amazon Aurora MySQL** (preferred) for better performance, automatic failover, and read replicas. As services are decomposed, implement database-per-service pattern. Consider **Amazon DynamoDB** (preferred) for high-throughput key-value patterns (inventory stock levels, session management). |
| **Evidence** | `infrastructure/monolith-apprunner.yaml` — `DBInstance` resource with `Engine: mysql`, `EngineVersion: '8.4.8'`, `MultiAZ: true`; `docker-compose.yml` — `mysql:8.0` image |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No workflow orchestration service detected. No `aws_sfn_*`, no Temporal, no Camunda, no workflow YAML definitions. The order fulfillment workflow (validate → assign warehouse → pick → pack → QC → ship) is implemented as sequential manual API calls with status transitions hardcoded in `index.php`. The `update_order_status()` function logs transitions to `order_status_history` table but does not orchestrate them. |
| **Gap** | All workflow logic is hardcoded — no visual management, no automated retry/error handling, no state machine. Fulfillment steps are manually triggered by admin users through the UI. |
| **Recommendation** | Implement **AWS Step Functions** to orchestrate the fulfillment workflow. Model the validate → assign → pick → pack → QC → ship flow as a state machine with error handling, retries, and parallel paths. Step Functions integrates natively with **EventBridge** (preferred) for event-driven triggers and **Bedrock** (preferred) for AI-assisted decision points. |
| **Evidence** | `index.php` — `update_order_status()` function; manual fulfillment endpoints (`/api/orders/{id}/validate`, `/assign-warehouse`, `/pick`, `/pack`, `/quality-check`, `/ship`); no Step Functions or workflow service in IaC |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No messaging or streaming infrastructure detected. No SQS, SNS, EventBridge, MSK, or Kinesis resources in CloudFormation. No message publishing or consuming patterns in `index.php`. All API endpoints are synchronous request-response. No event-driven handlers. |
| **Gap** | All communication is synchronous HTTP. No decoupling between domains. No event-driven architecture. Inventory changes, order status updates, and fulfillment events are not published as events. |
| **Recommendation** | Introduce **Amazon EventBridge** (preferred) as the central event bus. Publish domain events (OrderCreated, InventoryUpdated, PaymentProcessed, ReturnRequested) to enable decoupled, event-driven integration. Avoid self-managed Kafka (per preferences). EventBridge enables inventory threshold alerts that trigger the restocking agent. |
| **Evidence** | `infrastructure/monolith-apprunner.yaml` — no messaging resources; `index.php` — all endpoints are synchronous `echo json_encode(...)` responses with no event publishing |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Strong network security configuration: VPC (`10.0.0.0/16`) with two private subnets across two AZs. RDS in private subnets with security group allowing only MySQL traffic from App Runner SG on custom port 3307. App Runner SG allows only MySQL outbound to VPC and HTTPS outbound. WAFv2 Web ACL with IP whitelist (default block) and AWS Managed Rules for known bad inputs (Log4j protection). RDS is `PubliclyAccessible: false`. |
| **Gap** | No significant gaps. Network segmentation is well-implemented with least-privilege security groups, private subnets, and WAF protection. |
| **Recommendation** | Maintain current network security posture. When migrating to EKS, implement Kubernetes Network Policies and consider AWS App Mesh or Istio service mesh for service-to-service mTLS. |
| **Evidence** | `infrastructure/monolith-apprunner.yaml` — `VPC`, `PrivateSubnet1`, `PrivateSubnet2`, `DBSecurityGroup` (port 3307, source: AppRunnerSecurityGroup), `AppRunnerSecurityGroup`, `WebACL` (default block + IP whitelist + AWSManagedRulesKnownBadInputsRuleSet) |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | App Runner provides a managed entry point with automatic TLS and a public URL. WAFv2 is associated with the App Runner service for IP whitelisting and known-bad-input protection. However, there is no API Gateway — no throttling configuration, no request validation, no per-route authentication. All auth is handled by PHP session checks in the application code. |
| **Gap** | No dedicated API Gateway with throttling, request validation, or API key management. App Runner + WAF provides basic protection but lacks the fine-grained API management features needed for production APIs, especially for agent tool integration. |
| **Recommendation** | Add **Amazon API Gateway** (preferred) as the primary API entry point. Configure per-route throttling, request validation (JSON schema), and OAuth2/JWT authorizers. API Gateway also provides usage plans and API keys for agent access, and generates OpenAPI specs automatically. Route traffic from API Gateway to App Runner (or EKS when migrated). |
| **Evidence** | `infrastructure/monolith-apprunner.yaml` — `AppRunnerService` with `HealthCheckConfiguration`; `WebACL` with `WebACLAssociation` to App Runner; no `AWS::ApiGateway::*` or `AWS::ApiGatewayV2::*` resources |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | App Runner auto-scaling is configured via `AWS::AppRunner::AutoScalingConfiguration` with `MinSize: 1`, `MaxSize: 3`, `MaxConcurrency: 100`. This provides basic auto-scaling — App Runner automatically scales instances based on concurrent request count. |
| **Gap** | Auto-scaling is configured but with conservative defaults (max 3 instances). No custom scaling policies based on business metrics. MaxConcurrency of 100 may be insufficient for traffic spikes. All domains share the same scaling unit — cannot scale inventory reads independently from order processing. |
| **Recommendation** | Adjust `MaxSize` and `MaxConcurrency` based on load testing. When migrating to **EKS** (preferred), implement Horizontal Pod Autoscaler (HPA) with custom metrics for per-service scaling. |
| **Evidence** | `infrastructure/monolith-apprunner.yaml` — `AutoScalingConfiguration` resource with `MinSize`, `MaxSize`, `MaxConcurrency` parameters |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | RDS has `BackupRetentionPeriod: 7` with `PreferredBackupWindow: '03:00-04:00'`. CloudFormation `DeletionPolicy: Snapshot` and `UpdateReplacePolicy: Snapshot` ensure snapshots on deletion/replacement. `DeletionProtection: true` prevents accidental deletion. |
| **Gap** | No Point-in-Time Recovery (PITR) explicitly configured (RDS automated backups enable PITR by default when retention > 0, but this is not explicitly declared). No documented restore procedures or tested restore runbook. No AWS Backup plan for centralized backup management. No S3 versioning (no S3 buckets exist). |
| **Recommendation** | Add `AWS::Backup::BackupPlan` for centralized backup management. Document and test restore procedures. When migrating to **Aurora** (preferred), leverage Aurora's automatic backups, backtracking, and cloning for rapid restore testing. |
| **Evidence** | `infrastructure/monolith-apprunner.yaml` — `DBInstance` with `BackupRetentionPeriod: 7`, `DeletionPolicy: Snapshot`, `DeletionProtection: true` |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | RDS is `MultiAZ: true` — automatic failover across AZs. VPC Connector connects App Runner to two private subnets across two AZs (`PrivateSubnet1` in AZ-0, `PrivateSubnet2` in AZ-1). App Runner itself is a managed service that distributes across AZs automatically. |
| **Gap** | No significant gaps for the current architecture. HA is well-configured at both the compute and database layers. |
| **Recommendation** | Maintain Multi-AZ configuration. When migrating to **EKS** (preferred), ensure pod anti-affinity rules and topology spread constraints distribute workloads across AZs. Aurora (preferred) provides even better Multi-AZ failover than RDS MySQL. |
| **Evidence** | `infrastructure/monolith-apprunner.yaml` — `DBInstance` with `MultiAZ: true`; `VPCConnector` with `Subnets: [PrivateSubnet1, PrivateSubnet2]` across two AZs |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | CloudFormation template (`infrastructure/monolith-apprunner.yaml`, ~430 lines) defines: VPC, 2 subnets, 2 security groups, RDS instance, RDS monitoring role, DB subnet group, App Runner service, App Runner access/instance roles, auto-scaling config, VPC connector, ECR repository, 2 KMS keys, WAF Web ACL, IP set, WAF association, VPC Flow Log with log group and IAM role. This represents comprehensive coverage of the production infrastructure. |
| **Gap** | No CI/CD pipeline resources defined in IaC. No monitoring/alerting resources (CloudWatch alarms, dashboards, SNS topics). `deploy.sh` is a manual bash script, not declarative IaC. No environment parity — CloudFormation defines production, docker-compose defines local dev, with no staging/testing environment. |
| **Recommendation** | Migrate to **Terraform** (preferred) for better state management, module reuse, and multi-environment support. Define CI/CD pipeline, monitoring, and alerting resources in IaC. Implement **GitOps** (preferred) with Terraform + ArgoCD for declarative infrastructure and application deployment. |
| **Evidence** | `infrastructure/monolith-apprunner.yaml` — 20+ CloudFormation resources covering VPC, RDS, App Runner, ECR, WAF, IAM, KMS; `deploy.sh` — manual deployment script; no `.github/workflows/`, no `buildspec.yml` |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CI/CD pipeline exists anywhere in the repository. No `.github/workflows/`, no `.gitlab-ci.yml`, no `Jenkinsfile`, no `buildspec.yml`, no CodePipeline definitions in IaC. The only deployment mechanism is `deploy.sh`, which runs `docker-compose build` and `docker-compose up -d` — this is local development only, not a production deployment pipeline. The CloudFormation output `DeploymentInstructions` lists 6 manual steps for ECR push and CloudFormation stack update. |
| **Gap** | Complete absence of CI/CD automation. All deployments are manual. No automated build, test, or deploy stages. No quality gates. No automated rollback. This is a critical gap that blocks all other modernization efforts. |
| **Recommendation** | **Immediate priority.** Create a GitHub Actions pipeline (or equivalent) with stages: lint → test → security scan → docker build → ECR push → deploy. Avoid manual deployments (per preferences). Implement **GitOps** (preferred) with ArgoCD for declarative deployment. See Move to Modern DevOps pathway for detailed implementation plan. |
| **Evidence** | `deploy.sh` — `docker-compose build && docker-compose up -d`; `infrastructure/monolith-apprunner.yaml` — `DeploymentInstructions` output with manual CLI commands; no CI/CD config files in repository |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The application is written in PHP 8.2 (`FROM php:8.2-apache` in Dockerfile). Single language across the entire codebase. PHP 8.2 is a current version with modern features (typed properties, enums, fibers), but PHP's cloud-native ecosystem is limited compared to Python, Go, Java, or TypeScript. The front-end uses vanilla JavaScript embedded in PHP. |
| **Gap** | PHP has limited cloud-native tooling — fewer serverless frameworks, less container orchestration support, and a smaller ecosystem for microservices patterns compared to Go, Python, or TypeScript. No dependency manifest (`composer.json`) exists, so no PHP package management is in use. |
| **Recommendation** | For new microservices extracted from the monolith, consider Python, TypeScript, or Go for better cloud-native ecosystem support (AWS SDKs, Lambda runtime, EKS tooling). The existing PHP monolith can continue running during the transition. If staying with PHP, add `composer.json` for dependency management and adopt a framework (Laravel or Symfony) for the monolith before extraction. |
| **Evidence** | `Dockerfile` — `FROM php:8.2-apache`; `index.php` — PHP 8.2 syntax throughout; no `composer.json`, `composer.lock`, or `vendor/` directory |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The entire application is a single `index.php` file (~2,400 lines) containing ALL business domains: product catalog, order management, payment processing, returns handling, fulfillment workflow (warehouse assignment, picking, packing, QC, shipping), user management/authentication, and the complete HTML/CSS/JS UI. All domains share a single MySQL database with 9 tables. API routes are defined as inline `if` statements matching `$request_uri` patterns. There are no classes, no modules, no service boundaries — only procedural PHP functions and inline route handlers. |
| **Gap** | Tightly-coupled monolith with no clear module boundaries. Pervasive shared state through the global `$db` PDO connection. Cross-domain coupling: order creation directly modifies `inventory`, `payments`, and `order_items` tables in a single transaction. Cannot scale, deploy, or evolve any domain independently. All domains fail together. |
| **Recommendation** | Decompose using Strangler Fig pattern. Extract Inventory Service first (P0 — enables agent restocking decisions). See Decomposition Strategy section for detailed approach. Target architecture: independently deployable services on **EKS** (preferred) with **API Gateway** (preferred) entry points and **EventBridge** (preferred) for inter-service communication. |
| **Evidence** | `index.php` — single file with all routes (`/api/products`, `/api/orders`, `/api/returns`, `/api/admin/*`, `/api/orders/{id}/validate`, `/assign-warehouse`, `/pick`, `/pack`, `/quality-check`, `/ship`); 9 database tables in `init_db()`; embedded HTML/CSS/JS UI |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All communication is synchronous HTTP request-response. Every API endpoint processes the request completely and returns a JSON response synchronously. No message queues, no event publishing, no async handlers, no background job processing. The order creation endpoint performs 6+ database operations (inventory check, order insert, item inserts, inventory deduction, payment insert, status update) synchronously in a single HTTP request. |
| **Gap** | No async patterns exist. Every operation blocks the request until completion. No decoupling between domains. No resilience against slow downstream operations. |
| **Recommendation** | Introduce **Amazon EventBridge** (preferred) for async domain events. Decouple order confirmation from payment processing and inventory deduction. Use **SQS** for work queues (e.g., return processing queue). Implement async request-reply pattern for long-running fulfillment steps. |
| **Evidence** | `index.php` — all route handlers end with `echo json_encode(...)` synchronous responses; order creation endpoint uses `$db->beginTransaction()` / `$db->commit()` for atomic synchronous processing; no `SQS`, `SNS`, or event publishing patterns |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All operations are synchronous regardless of duration. The fulfillment workflow (validate → assign warehouse → pick → pack → QC → ship) requires multiple manual steps, each triggered as a separate HTTP request. Return processing is submitted and waits for "manual CS review (24-48 hours)" but the submission itself is synchronous. No background job frameworks, no async job queues, no status polling endpoints. |
| **Gap** | No async job processing. Operations that could take significant time (warehouse assignment optimization, carrier rate calculation, fraud scoring) are all computed synchronously in the request. No status polling or callback patterns. |
| **Recommendation** | Implement **AWS Step Functions** for orchestrating multi-step workflows. Use **SQS** or **EventBridge** (preferred) for async job processing. Add status polling endpoints (`GET /api/jobs/{id}/status`) for long-running operations. Consider Lambda-based async invocation for compute-intensive operations like fraud scoring. |
| **Evidence** | `index.php` — all fulfillment endpoints return immediately with synchronous results; `/api/returns` POST returns synchronously with `status: pending_review`; no background worker patterns, no job queue imports |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API versioning exists. All routes use unversioned paths: `/api/products`, `/api/orders`, `/api/returns`, `/api/admin/*`. No `/v1/` prefix, no `Accept-Version` headers, no query parameter versioning. No changelog file. No API documentation or OpenAPI specification. |
| **Gap** | Any API change breaks all consumers immediately. No backward compatibility guarantees. No mechanism for gradual migration. This is a critical blocker for agent integration — agents need stable, versioned APIs with documented contracts. |
| **Recommendation** | Add API versioning (URL path: `/v1/api/products`). Generate an OpenAPI specification from existing routes — this is prerequisite for agent tool discovery. When adding **API Gateway** (preferred), leverage its built-in stage management for versioning and its ability to export OpenAPI specs. |
| **Evidence** | `index.php` — route patterns: `/api/products`, `/api/orders`, `/api/returns`, `/api/orders/{orderId}/validate`, etc. — all unversioned; no OpenAPI, Swagger, AsyncAPI, or GraphQL schema files in repository |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | As a monolith, there is only one service. The database endpoint is configured via environment variables (`DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASS`) set in both `docker-compose.yml` and the App Runner CloudFormation configuration. The `get_db()` function reads these environment variables with hardcoded defaults (`'mysql'`, `'ecommerce'`, `'ecommerce_user'`, `'ecommerce_pass'`). |
| **Gap** | Environment variables with hardcoded fallback defaults are used for configuration. No dynamic service discovery. Hardcoded default credentials in `get_db()` are a security concern. When decomposed into microservices, service-to-service communication will need dynamic discovery. |
| **Recommendation** | When decomposing, implement AWS Cloud Map for service discovery or leverage **EKS** (preferred) built-in Kubernetes DNS for service-to-service communication. Use **API Gateway** (preferred) as the service catalog for external consumers and agents. Remove hardcoded default credentials from source code. |
| **Evidence** | `index.php` — `get_db()` function with `getenv('DB_HOST') ?: 'mysql'` and hardcoded defaults; `docker-compose.yml` — environment variables `DB_HOST: mysql`; `infrastructure/monolith-apprunner.yaml` — `RuntimeEnvironmentVariables` with `DB_HOST: !GetAtt DBInstance.Endpoint.Address` |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No S3 buckets or object storage defined in IaC. No document/file storage patterns in application code. Product images reference URL paths (`/images/tshirt.jpg`, `/images/jeans.jpg`, etc.) in seed data but there is no actual image upload, storage, or retrieval implementation. No Textract, no document parsing libraries. |
| **Gap** | No unstructured data storage strategy. Product images are referenced but not stored. No document processing capability. If the application needs to handle product images, shipping labels, or return documentation, there is no infrastructure for it. |
| **Recommendation** | Add **Amazon S3** for product images, shipping labels, and return documentation. Implement pre-signed URLs for secure image upload/download. When adding AI capabilities, use **Amazon Textract** for parsing shipping labels and return forms. S3 provides the document corpus for future RAG-based knowledge agents. |
| **Evidence** | `index.php` — `seed_data()` function references `/images/tshirt.jpg` etc. as `image_url` in inventory table; `infrastructure/monolith-apprunner.yaml` — no `AWS::S3::Bucket` resources; no file upload/download code patterns |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | The `get_db()` function provides a centralized PDO connection to MySQL. However, SQL queries are scattered directly throughout inline route handlers — there is no Repository/DAO pattern, no ORM, no data access abstraction layer. Raw SQL statements (`SELECT`, `INSERT`, `UPDATE`, `JOIN`) appear in 25+ locations across `index.php`. Multiple route handlers directly access multiple tables (e.g., order creation touches `inventory`, `orders`, `order_items`, `payments`, `order_status_history`). |
| **Gap** | Centralized connection but scattered query execution. No single point of data contract enforcement. Cross-domain data access is pervasive — route handlers directly query tables from other domains. This makes database-per-service decomposition difficult. |
| **Recommendation** | Before decomposition, introduce a Repository/DAO pattern to centralize data access per domain. This creates the natural module boundaries needed for service extraction. Each domain's repository becomes the foundation for that service's data access layer. Use an ORM or query builder to standardize data access patterns. |
| **Evidence** | `index.php` — `get_db()` function (centralized connection); raw SQL in route handlers for `/api/products` (SELECT inventory), `/api/orders` POST (INSERT orders, order_items, payments; UPDATE inventory), `/api/returns` POST (SELECT orders; INSERT returns, interactions), `/api/orders/{id}/validation-data` (SELECT orders; aggregate query on orders for customer stats) |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | CloudFormation explicitly pins MySQL `EngineVersion: '8.4.8'` on the production RDS instance. MySQL 8.4 is an Innovation Release (current, not EOL). `AutoMinorVersionUpgrade: true` ensures automatic patching. Docker-compose uses `mysql:8.0` for local development — MySQL 8.0 reached end of Premier Support in April 2025 but Extended Support continues. |
| **Gap** | Production version is current and explicitly pinned. Development version (8.0) is older and approaching end of extended support. Version mismatch between production (8.4) and development (8.0) environments could cause behavior differences. |
| **Recommendation** | Update `docker-compose.yml` to use `mysql:8.4` to match production. When migrating to **Aurora MySQL** (preferred), target Aurora MySQL 3.x (MySQL 8.0 compatible) or Aurora MySQL 4.x when available. Aurora provides automatic version lifecycle management. |
| **Evidence** | `infrastructure/monolith-apprunner.yaml` — `DBInstance` with `EngineVersion: '8.4.8'`, `AutoMinorVersionUpgrade: true`; `docker-compose.yml` — `image: mysql:8.0` |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, functions, or proprietary SQL constructs. All business logic resides in the PHP application layer. The `init_db()` function uses standard ANSI SQL for table creation (`CREATE TABLE IF NOT EXISTS`). All queries use standard SQL (`SELECT`, `INSERT`, `UPDATE`, `JOIN`) with PDO prepared statements. No T-SQL, PL/SQL, or MySQL-specific procedural extensions. |
| **Gap** | No gaps. The absence of stored procedures is a significant positive for modernization — all business logic is in the application layer, which makes database engine migration straightforward. |
| **Recommendation** | Maintain this approach. As services are extracted, continue keeping business logic in the application layer. This enables future database engine migration (e.g., to **Aurora** (preferred) or **DynamoDB** (preferred) for specific services) without stored procedure extraction. |
| **Evidence** | `index.php` — `init_db()` function with 9 `CREATE TABLE` statements using standard SQL; all route handlers use PDO prepared statements with standard SQL; no `.sql` migration files with `CREATE PROCEDURE`, `CREATE TRIGGER`, or `CREATE FUNCTION` |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | VPC Flow Logs are configured (`AWS::EC2::FlowLog`) with CloudWatch destination, KMS encryption (`VPCFlowLogKMSKey` with key rotation enabled), and 30-day retention. RDS Enhanced Monitoring is enabled (`MonitoringInterval: 60`). However, no CloudTrail is defined in IaC. No application-level audit logging — the PHP application only uses `ini_set('log_errors', '1')` for error logging. No structured audit trail for API actions. |
| **Gap** | No CloudTrail for AWS API audit logging. No application-level audit trail for business actions (who created which order, who approved which return). VPC Flow Logs provide network-level visibility only. |
| **Recommendation** | Add `AWS::CloudTrail::Trail` to IaC with log file validation and S3 destination with object lock for immutability. Add structured application audit logging (JSON format) for all state-changing API operations. Ship application logs to CloudWatch Logs with defined retention. |
| **Evidence** | `infrastructure/monolith-apprunner.yaml` — `VPCFlowLog`, `VPCFlowLogGroup` (30-day retention), `VPCFlowLogKMSKey`; no `AWS::CloudTrail::Trail`; `index.php` — `ini_set('log_errors', '1')` only |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | RDS `StorageEncrypted: true` (AWS-managed encryption key — no customer-managed KMS key specified for RDS). ECR repository encrypted with customer-managed KMS key (`ECRKMSKey` with key rotation). VPC Flow Log CloudWatch log group encrypted with customer-managed KMS key (`VPCFlowLogKMSKey` with key rotation). Both KMS keys have root account access enabled. |
| **Gap** | RDS uses AWS-managed encryption (not customer-managed KMS). No S3 buckets to encrypt (no unstructured data storage). Mixed encryption approach — ECR and Flow Logs use customer-managed KMS, but RDS does not. |
| **Recommendation** | Create a customer-managed KMS key for RDS encryption to enable key rotation control and fine-grained access policies. When migrating to **Aurora** (preferred), configure customer-managed KMS from the start. Ensure all future data stores (S3, DynamoDB) use customer-managed KMS keys. |
| **Evidence** | `infrastructure/monolith-apprunner.yaml` — `DBInstance` with `StorageEncrypted: true` (no `KmsKeyId`); `ECRRepository` with `EncryptionConfiguration.KmsKey: !GetAtt ECRKMSKey.Arn`; `VPCFlowLogGroup` with `KmsKeyId: !GetAtt VPCFlowLogKMSKey.Arn`; both KMS keys have `EnableKeyRotation: true` |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Session-based authentication using PHP sessions (`session_start()`). Login endpoint (`POST /login`) validates username/password against `users` table with `password_verify()` (bcrypt). All API routes check `$_SESSION['user']` and return 401 if not set. Admin endpoints additionally check `$_SESSION['user']['role'] !== 'admin'` and return 403. Passwords are hashed with `PASSWORD_BCRYPT`. |
| **Gap** | No OAuth2/JWT token-based authentication. PHP sessions are not suitable for API consumers, mobile clients, or AI agents. Session-based auth requires cookies and is not stateless. No API keys or bearer tokens for programmatic access. RDS has `EnableIAMDatabaseAuthentication: true` but the application uses password-based DB connection. |
| **Recommendation** | Implement OAuth2/JWT authentication via **Amazon Cognito** or through **API Gateway** (preferred) authorizers. Replace session-based auth with bearer token validation. Issue API keys through API Gateway usage plans for agent access. Leverage RDS IAM authentication for database connections. |
| **Evidence** | `index.php` — `session_start()`, `$_SESSION['user']` checks on all `/api/*` routes, `password_verify()` for login, `password_hash($data['password'], PASSWORD_BCRYPT)` for user creation; `infrastructure/monolith-apprunner.yaml` — `EnableIAMDatabaseAuthentication: true` on RDS |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The application manages its own authentication entirely. The `users` table stores usernames, bcrypt-hashed passwords, names, emails, and roles. Login is handled by a `POST /login` endpoint with form-based username/password submission. User management (CRUD) is handled by admin API endpoints. No Cognito, no OIDC, no SAML, no external IdP integration. |
| **Gap** | Standalone authentication system with no external IdP integration. Cannot participate in SSO. No federation capability. User credentials are managed entirely within the application database. This is a security risk and makes enterprise identity integration impossible. |
| **Recommendation** | Migrate authentication to **Amazon Cognito** user pools with OIDC/SAML federation support. This enables SSO, MFA, and integration with enterprise identity providers. Cognito also provides machine-to-machine OAuth2 flows for agent authentication via client credentials grant. |
| **Evidence** | `index.php` — `users` table DDL with `username`, `password`, `role` columns; `POST /login` handler with `password_verify()`; admin CRUD endpoints for user management; no Cognito, OIDC, or SAML configuration anywhere |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Database credentials are passed as CloudFormation `NoEcho` parameters (`DBUsername`, `DBPassword`) and injected as App Runner environment variables. Docker-compose uses environment variables with required validation (`${MYSQL_PASSWORD:?Set MYSQL_PASSWORD}`). However, the `get_db()` function contains hardcoded default credentials: `$user = getenv('DB_USER') ?: 'ecommerce_user'` and `$pass = getenv('DB_PASS') ?: 'ecommerce_pass'`. No AWS Secrets Manager, no HashiCorp Vault, no secret rotation. |
| **Gap** | Hardcoded default credentials in source code. No dedicated secrets management service. No secret rotation. Environment variables are the sole mechanism for secret injection. CloudFormation `NoEcho` prevents display but credentials are still stored as plaintext in the parameter store or CLI history. |
| **Recommendation** | Migrate secrets to **AWS Secrets Manager** with automatic rotation. Remove hardcoded default credentials from `get_db()`. Reference Secrets Manager ARNs in App Runner configuration instead of plaintext environment variables. When migrating to **EKS** (preferred), use External Secrets Operator to sync Secrets Manager with Kubernetes secrets. |
| **Evidence** | `index.php` — `get_db()` with `getenv('DB_PASS') ?: 'ecommerce_pass'` hardcoded defaults; `infrastructure/monolith-apprunner.yaml` — `DBPassword` as `NoEcho` parameter, `DB_PASS: !Ref DBPassword` in RuntimeEnvironmentVariables; `docker-compose.yml` — `${MYSQL_PASSWORD:?Set MYSQL_PASSWORD}`; no `AWS::SecretsManager::*` resources |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Dockerfile creates a non-root user (`appuser`) and runs Apache as that user. Docker-compose applies `security_opt: no-new-privileges:true` and `read_only: true` for both the monolith and MySQL containers. ECR has `ImageScanningConfiguration.ScanOnPush: true` and `ImageTagMutability: IMMUTABLE`. RDS has `AutoMinorVersionUpgrade: true` for automatic patching. |
| **Gap** | No SSM Patch Manager (no EC2 instances to patch — App Runner is managed). No AWS Inspector for runtime vulnerability scanning. ECR scan-on-push is basic scanning — no continuous scanning. Dockerfile uses `php:8.2-apache` base image without a hardened variant (no CIS benchmark, no Bottlerocket). No security scanning gate in pipeline (no pipeline exists). |
| **Recommendation** | Enable ECR continuous scanning. Add **Amazon Inspector** for runtime vulnerability analysis. When migrating to **EKS** (preferred), use Bottlerocket AMIs for worker nodes and implement pod security standards. Add container image scanning as a gate in the CI/CD pipeline (when created). |
| **Evidence** | `Dockerfile` — `RUN groupadd -r appuser && useradd -r -g appuser`, `USER appuser`; `docker-compose.yml` — `security_opt: no-new-privileges:true`, `read_only: true`; `infrastructure/monolith-apprunner.yaml` — `ECRRepository` with `ScanOnPush: true`, `ImageTagMutability: IMMUTABLE`; `DBInstance` with `AutoMinorVersionUpgrade: true` |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CI/CD pipeline exists, so no security scanning is integrated. No SAST tools (SonarQube, Semgrep, CodeGuru). No DAST tools. No dependency vulnerability scanning (no `composer audit`, no Dependabot, no Snyk). ECR scan-on-push provides basic container image scanning but this is not integrated into a pipeline with blocking gates. No `.snyk` policy file, no Dependabot configuration. |
| **Gap** | Complete absence of automated security scanning. Vulnerabilities in PHP code, base image dependencies, or application dependencies reach production undetected. No security quality gates. |
| **Recommendation** | When creating the CI/CD pipeline (see Move to Modern DevOps), add: Semgrep for PHP SAST, `composer audit` for dependency scanning (requires adding `composer.json`), ECR image scanning gate (block deployment on critical findings), and WAF rule testing. Consider **Amazon CodeGuru Reviewer** for automated code review in the pipeline. |
| **Evidence** | No `.github/workflows/`, `buildspec.yml`, or pipeline config; no `.snyk`, `.semgrep.yml`, or Dependabot config; `infrastructure/monolith-apprunner.yaml` — `ECRRepository.ScanOnPush: true` (only scanning present, not gated) |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing instrumented. No X-Ray SDK, no OpenTelemetry SDK, no tracing libraries in the codebase. No trace ID propagation headers (`traceparent`, `X-Amzn-Trace-Id`). No tracing configuration in Dockerfile or docker-compose. App Runner supports X-Ray tracing but it is not enabled in the CloudFormation configuration. |
| **Gap** | Complete absence of tracing. Cannot trace requests through the application. When decomposed into microservices, cross-service request tracing will be essential for debugging and performance analysis. |
| **Recommendation** | Enable X-Ray tracing on App Runner. For the PHP monolith, add the AWS X-Ray SDK for PHP. When migrating to **EKS** (preferred), deploy the OpenTelemetry Collector as a DaemonSet and instrument services with OpenTelemetry SDKs. This is prerequisite for the Observability Agent win. |
| **Evidence** | `index.php` — no tracing imports or middleware; `Dockerfile` — no tracing agent installed; `infrastructure/monolith-apprunner.yaml` — no `ObservabilityConfiguration` on AppRunnerService |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLOs defined anywhere in the repository. No CloudWatch alarms for availability, latency (p99/p95), or error rates. No error budget tracking. No SLO definition files. The only monitoring is RDS Enhanced Monitoring (`MonitoringInterval: 60`) which provides infrastructure metrics, not service-level objectives. |
| **Gap** | No formal definition of acceptable service levels. Cannot measure whether the system is meeting user expectations. No error budget to drive modernization prioritization. |
| **Recommendation** | Define SLOs for critical user journeys: product catalog availability (99.9%), order creation success rate (99.5%), order creation p99 latency (< 2s). Create CloudWatch alarms and dashboards. When migrating to **EKS** (preferred), implement SLO monitoring with Prometheus and Grafana. |
| **Evidence** | No SLO files; no `AWS::CloudWatch::Alarm` resources in `infrastructure/monolith-apprunner.yaml`; `DBInstance.MonitoringInterval: 60` (infra metrics only) |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom CloudWatch metrics published. No business metric instrumentation in the application code. No `cloudwatch.put_metric_data` calls. Only basic PHP error logging (`ini_set('log_errors', '1')`). WAF CloudWatch metrics are enabled (`CloudWatchMetricsEnabled: true`) but these are infrastructure metrics, not business outcomes. |
| **Gap** | No visibility into business outcomes — order conversion rates, average order value, fulfillment time, return rates, inventory turnover. Cannot make data-driven modernization decisions. |
| **Recommendation** | Instrument key business metrics: orders per hour, average order value, fulfillment cycle time, return rate, inventory stock levels. Publish to CloudWatch custom metrics. Create dashboards for business KPIs. These metrics also feed into the restocking agent's decision-making. |
| **Evidence** | `index.php` — no metric publishing code; no CloudWatch SDK imports; `infrastructure/monolith-apprunner.yaml` — `WebACL.VisibilityConfig.CloudWatchMetricsEnabled: true` (WAF metrics only) |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudWatch alarms configured. No anomaly detection. No alerting integration (PagerDuty, OpsGenie). WAF has CloudWatch metrics enabled but no alarms are defined on those metrics. RDS Enhanced Monitoring provides OS-level metrics but no alarms are set. No composite alarms. |
| **Gap** | No alerting of any kind. System failures, performance degradation, and security events go undetected until users report them. |
| **Recommendation** | Add CloudWatch alarms for: App Runner 5xx error rate, RDS CPU utilization, RDS connections, WAF blocked requests. Enable CloudWatch anomaly detection on error rates and latency. Integrate with SNS → PagerDuty/OpsGenie for on-call alerting. |
| **Evidence** | `infrastructure/monolith-apprunner.yaml` — no `AWS::CloudWatch::Alarm` resources; `WebACL.VisibilityConfig.CloudWatchMetricsEnabled: true` (metrics exist but no alarms); `DBInstance.MonitoringInterval: 60` (monitoring without alerting) |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | `deploy.sh` runs `docker-compose build` and `docker-compose up -d` — direct deployment with no staged rollout. No blue/green, no canary, no rolling updates. No automated rollback. The CloudFormation `DeploymentInstructions` output describes a manual 6-step process: build → authenticate → tag → push → update stack. App Runner supports automatic deployments from ECR but no deployment configuration is specified. |
| **Gap** | Direct-to-production deployment with no safety net. Any deployment error affects all users immediately. No traffic shifting, no health-check-based rollback. |
| **Recommendation** | When creating the CI/CD pipeline, implement blue/green deployments. App Runner supports automatic deployment with health checks. For **EKS** (preferred), use Argo Rollouts for canary deployments with automated analysis and rollback. Implement **GitOps** (preferred) with ArgoCD for declarative deployment management. |
| **Evidence** | `deploy.sh` — `docker-compose build && docker-compose up -d`; `infrastructure/monolith-apprunner.yaml` — `DeploymentInstructions` output with manual steps; no CodeDeploy, no Argo Rollouts, no deployment strategy configuration |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Zero test files in the repository. No test directories (`tests/`, `test/`, `spec/`). No test configuration files (`phpunit.xml`, `phpunit.dist.xml`). No test framework dependencies. No test commands in any configuration. No API contract tests (Postman, Newman). No end-to-end test pipelines. |
| **Gap** | Complete absence of automated testing. No safety net for code changes. Any modification risks breaking existing functionality without detection. This is a critical blocker for safe decomposition — extracting services without regression tests is extremely risky. |
| **Recommendation** | **Immediate priority (alongside CI/CD).** Add PHPUnit and write integration tests for critical API endpoints: product listing, order creation, return submission, admin fulfillment workflow. Target 80% coverage of API routes before beginning service extraction. Add API contract tests to validate request/response schemas. |
| **Evidence** | No `tests/` directory; no `phpunit.xml`; no test framework references; no `composer.json` with test dependencies; `.gitignore` has no test-related exclusions |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks (markdown, YAML, or JSON). No Systems Manager Automation documents. No Lambda-based remediation functions. No Step Functions for incident workflows. No self-healing patterns. No escalation procedures documented. |
| **Gap** | Incident response is entirely ad hoc. No documented procedures for common incidents (database connection failures, high error rates, deployment rollback). No automated remediation. |
| **Recommendation** | Create runbooks for common incidents: database failover, application restart, deployment rollback, WAF rule updates. Implement as Systems Manager Automation documents for executable runbooks. Add Lambda-based auto-remediation for common failure modes (e.g., auto-restart on repeated health check failures). |
| **Evidence** | No runbook files in repository; no `AWS::SSM::Document` resources; no remediation Lambda functions; no incident response documentation |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CODEOWNERS file. No per-service dashboards (no dashboards at all). No named alarm owners (no alarms exist). No SLO definitions with team attribution. No team tags on monitoring resources. |
| **Gap** | No observability ownership. No accountability for monitoring coverage. When decomposed into microservices, each service team must own their observability stack — dashboards, alarms, SLOs, and on-call rotation. |
| **Recommendation** | Add a `CODEOWNERS` file. Create a CloudWatch dashboard for the monolith with key metrics. Assign ownership of alarms and SLOs to specific team members. When migrating to **EKS** (preferred), implement per-namespace dashboards in Grafana with team-based access control. |
| **Evidence** | No `CODEOWNERS` file; no `AWS::CloudWatch::Dashboard` resources; no alarm or SLO ownership documentation |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | CloudFormation resources have `Name` and `Environment` tags. Examples: `Key: Name, Value: !Sub '${ServiceName}-vpc'` and `Key: Environment, Value: Production` on ECR and App Runner. Most resources have Name tags. Some resources lack Environment tags. |
| **Gap** | No cost allocation tags (CostCenter, Project, Budget). No ownership tags (Owner, Team). No tagging standard document. No enforcement via AWS Config rules or SCPs. Inconsistent tagging — some resources have both Name and Environment, others have only Name. |
| **Recommendation** | Implement a tagging standard with required keys: `Name`, `Environment`, `CostCenter`, `Owner`, `Team`, `Project`. Add `default_tags` when migrating to **Terraform** (preferred). Enforce tagging via AWS Config `required-tags` rule. Activate cost allocation tags in AWS Billing. |
| **Evidence** | `infrastructure/monolith-apprunner.yaml` — `Tags: [{Key: Name, Value: ...}, {Key: Environment, Value: Production}]` on `ECRRepository`, `AppRunnerService`; `Tags: [{Key: Name, Value: ...}]` only on `VPC`, subnets, security groups, KMS keys, WAF; no `CostCenter`, `Owner`, or `Team` tags |

## Learning Materials

The following learning resources are mapped to the **3 triggered pathways**:

### Move to Cloud Native
- [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN)
- [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)
- [Strangler Fig Pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html)
- [Saga Pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga.html)
- [Event Sourcing Pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/event-sourcing.html)

### Move to Modern DevOps
- [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

### Move to AI
- [Move to AI](https://skillbuilder.aws/learning-plan/VDFEE4ACCV)
- [Amazon Bedrock Getting Started](https://skillbuilder.aws/learn/63KTRM86DQ)
- [Introduction to Agentic AI on AWS](https://skillbuilder.aws/learn/DNBD5MT8ZD)

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `index.php` | APP-Q1, APP-Q2, APP-Q3, APP-Q4, APP-Q5, APP-Q6, DATA-Q1, DATA-Q2, DATA-Q3, DATA-Q4, SEC-Q1, SEC-Q3, SEC-Q4, SEC-Q5, INF-Q3, INF-Q4, OPS-Q1, OPS-Q3 | Single PHP file containing all application business logic, API routes, database schema, authentication, and UI. ~2,400 lines. 9 database tables defined in `init_db()`. 20+ API endpoints. Session-based auth. |
| `Dockerfile` | APP-Q1, INF-Q1, SEC-Q6, OPS-Q1 | PHP 8.2 Apache container image. Non-root user (`appuser`). Health check. No tracing agent. |
| `docker-compose.yml` | INF-Q1, INF-Q2, DATA-Q3, SEC-Q5, SEC-Q6 | Local development setup with MySQL 8.0 and PHP monolith. Security options: `no-new-privileges`, `read_only`. Environment variable configuration with required validation. |
| `infrastructure/monolith-apprunner.yaml` | INF-Q1 through INF-Q11, SEC-Q1, SEC-Q2, SEC-Q3, SEC-Q5, SEC-Q6, SEC-Q7, OPS-Q2, OPS-Q3, OPS-Q4, OPS-Q5, OPS-Q8, OPS-Q9, DATA-Q3 | CloudFormation template (~430 lines). Defines: VPC, 2 private subnets, 2 security groups, RDS MySQL 8.4.8 (Multi-AZ, encrypted), App Runner service, ECR repo (KMS, scan-on-push, immutable tags), WAFv2 (IP whitelist + managed rules), VPC Flow Logs (KMS encrypted), auto-scaling config, IAM roles. |
| `deploy.sh` | INF-Q10, INF-Q11, OPS-Q5 | Manual deployment script. `docker-compose build && docker-compose up -d`. Not a production deployment pipeline. |
| `.htaccess` | APP-Q2 | Apache rewrite rules routing all requests to `index.php`. Single entry point pattern. |
| `.gitignore` | OPS-Q6 | Standard ignores for database files, logs, OS files, IDE configs. No test-related exclusions. |

### Notable Absences (files NOT found)

| Expected File/Pattern | Referenced By | Impact |
|----------------------|--------------|--------|
| `.github/workflows/*.yml`, `buildspec.yml`, `Jenkinsfile` | INF-Q11, SEC-Q7, OPS-Q5 | No CI/CD pipeline — all deployments manual |
| `openapi.yaml`, `swagger.json` | APP-Q5 | No API documentation — blocks agent tool discovery |
| `composer.json`, `composer.lock` | APP-Q1, SEC-Q7 | No PHP dependency management |
| `tests/`, `phpunit.xml` | OPS-Q6 | No automated tests |
| `README.md`, `docs/` | Quick Agent Wins | No documentation for RAG knowledge agent |
| `CODEOWNERS` | OPS-Q8 | No observability ownership |
| Kubernetes manifests, Helm charts | INF-Q1 | No K8s infrastructure (using App Runner instead) |
| AI/agent framework imports | Move to AI pathway | No AI/agent capabilities |
