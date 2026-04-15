# Modernization Readiness Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | monolith |
| **Date** | 2026-04-15 |
| **Repo Type** | application |
| **Priority** | P0 |
| **Tags** | monolith, php, containers |
| **Context** | PHP monolith with Docker and CloudFormation on App Runner — containerize and expose inventory APIs the agent needs for restocking decisions. |
| **Overall Score** | **1.29 / 4.0** |

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 1.00 / 4.0 | ❌ Not Present |
| Application Architecture (APP) | 1.17 / 4.0 | ❌ Not Present |
| Data Platform Modernization (DATA) | 2.00 / 4.0 | 🟠 Needs Work |
| Security Baseline (SEC) | 1.29 / 4.0 | ❌ Not Present |
| Operations & Observability (OPS) | 1.00 / 4.0 | ❌ Not Present |
| **Overall** | **1.29 / 4.0** | **❌ Not Present** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q10: Infrastructure as Code Coverage | 1 | Zero IaC — all infrastructure is manually defined in docker-compose.yml with no Terraform, CloudFormation, or CDK | Blocks reproducible environments, disaster recovery, and automated provisioning. Foundation for all other modernization pathways. |
| 2 | INF-Q11: CI/CD Automation | 1 | No CI/CD pipeline — only a manual `deploy.sh` script running docker-compose commands | Blocks safe deployments, automated testing, and continuous delivery. Every deployment is manual and error-prone. |
| 3 | APP-Q2: Monolith vs Microservices | 1 | Entire application in single index.php (~2000+ lines) with all business domains tightly coupled and sharing one MySQL database | Prevents independent scaling, deployment, and team autonomy. Blocks agent integration for inventory restocking. |
| 4 | INF-Q2: Managed Databases | 1 | MySQL 8.0 running as self-managed container in docker-compose with no backups, failover, or lifecycle management | Single point of failure for all data. No automated backups, no PITR, no failover. Data loss risk is critical. |
| 5 | OPS-Q6: Integration Testing | 1 | No automated tests of any kind — no unit tests, integration tests, or test framework | Regression risk during any code change or modernization effort. No safety net for decomposition. |

---

## Quick Agent Wins

No Quick Agent Wins identified. The system lacks the foundational capabilities needed to support agent integration:

- **API documentation** — No OpenAPI spec exists (APP-Q5 = 1). The API surface exists with structured JSON responses but is undocumented and unversioned.
- **CI/CD automation** — No pipeline exists (INF-Q11 = 1). A DevOps agent requires an existing pipeline to orchestrate.
- **Structured logging/tracing** — No observability infrastructure (OPS-Q1 = 1). An observability agent requires traces and structured logs.
- **Workflow orchestration** — No orchestration service (INF-Q3 = 1). A workflow agent requires an existing execution surface.
- **Documentation** — No README, wiki, or architecture docs exist. A RAG agent requires a knowledge corpus.
- **Data access layer** — Queries are scattered throughout index.php (DATA-Q2 = 1). A data query agent works best with a centralized access layer.

**Near-term opportunity:** The existing API routes (`/api/products`, `/api/orders`, `/api/warehouses/assignment-options`, etc.) return well-structured JSON responses. Once an OpenAPI specification is generated from these routes and the API is versioned (even a simple `/v1/` prefix), an **API-aware agent** becomes immediately viable — particularly for the inventory and warehouse assignment endpoints that are critical for agent-driven restocking decisions. This should be prioritized alongside the Move to Modern DevOps pathway.

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Triggered | High | High | APP-Q2 = 1 (tightly-coupled monolith), INF-Q1 = 1 (no managed compute), APP-Q3 = 1 (all synchronous), APP-Q4 = 1 (no async patterns) |
| 2 | Move to Containers | Not Triggered | — | — | Dockerfile and docker-compose.yml already exist — the application is already containerized locally. Contextual guard: container definitions found. |
| 3 | Move to Open Source | Not Triggered | — | — | MySQL 8.0 is already open source. DATA-Q4 = 4 (no stored procedures). No commercial database engines detected. |
| 4 | Move to Managed Databases | Triggered | High | Medium | INF-Q2 = 1 (self-managed MySQL in Docker container), DATA-Q3 = 2 (version pinned only in docker-compose, no IaC lifecycle) |
| 5 | Move to Managed Analytics | Not Triggered | — | — | No data processing workloads detected. No streaming, ETL, data pipeline, or analytics artifacts found. Contextual guard prevents trigger. |
| 6 | Move to Modern DevOps | Triggered | High | Medium | INF-Q10 = 1 (zero IaC), INF-Q11 = 1 (no CI/CD), OPS-Q5 = 1 (no deployment strategy), OPS-Q6 = 1 (no tests) |
| 7 | Move to AI | Triggered | Medium | Medium | No AI/agent frameworks, no vector DB, no RAG implementation, no agent evaluation frameworks detected in repository |

---

### Pathway: Move to Cloud Native

**Status:** Triggered
**Priority:** High
**Estimated Effort:** High

**Current Architecture State:**
The application is a tightly-coupled PHP monolith (`index.php`, ~2000+ lines) containing all business domains — orders, inventory, payments, returns, shipping, user management, warehouse operations, and quality checks — in a single file. The frontend (HTML/CSS/JS) is also embedded. A single shared MySQL 8.0 database (self-managed in Docker) is used for all domains. There are no module boundaries, no service separation, and pervasive shared state through direct SQL queries scattered throughout the file.

**Compute Model Gaps (INF-Q1 = 1):**
No managed compute infrastructure exists. The application runs as a local Docker container via docker-compose with no orchestration, no auto-scaling, and no managed container service (ECS, EKS, Fargate, or Lambda).

**Communication Pattern Gaps (APP-Q3 = 1, APP-Q4 = 1):**
All communication is synchronous in-process PHP request/response. No message queues, event bus, or async patterns. Long-running operations (e.g., return processing requiring 24-48 hour manual review) are handled synchronously with no background job framework or status polling.

**Recommended Decomposition Approach:**
See the **Decomposition Strategy** section below for detailed approach options. The recommended starting point is extracting the **Inventory Service** to expose inventory APIs for agent-driven restocking decisions, as specified in the repository context.

**Recommended AWS Services:**
- **Amazon EKS** (preferred) for container orchestration — deploy extracted services as EKS pods with Helm charts
- **Amazon API Gateway** (preferred) as the unified entry point with throttling, auth, and request validation
- **Amazon EventBridge** (preferred) for event-driven communication between extracted services
- **AWS Step Functions** for orchestrating multi-step workflows (order fulfillment, return processing)
- **AWS Lambda** for lightweight event handlers and integration glue

**Recommended Patterns:**
- **Strangler Fig** — Incrementally extract services while keeping the monolith running
- **Anti-corruption Layer** — Isolate new services from the monolith's data model
- **Saga Pattern** — Manage distributed transactions (order → payment → inventory)
- **Event Sourcing** — The `order_status_history` table already captures state changes; evolve this into a proper event store

**AWS Prescriptive Guidance:**
- [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html)
- [Decompose monoliths into microservices](https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-decomposing-monoliths/welcome.html)

---

### Pathway: Move to Managed Databases

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current Database Topology (INF-Q2 = 1):**
MySQL 8.0 runs as a self-managed container defined in `docker-compose.yml` (`image: mysql:8.0`). Data is stored in a Docker volume (`mysql_data`) with no backups, no point-in-time recovery, no failover, and no encryption at rest. Database credentials are passed as environment variables with fallback defaults hardcoded in the `get_db()` function.

**Engine Versions and EOL Status (DATA-Q3 = 2):**
MySQL 8.0 is explicitly pinned in docker-compose.yml. MySQL 8.0 LTS has support through April 2026 but the self-managed deployment model means no automated lifecycle management, no automated patching, and no upgrade path defined.

**Data Access Patterns (DATA-Q2 = 1):**
SQL queries are scattered throughout `index.php` with inline PDO prepared statements in every API route handler. There is no repository pattern, no DAO layer, and no ORM. The schema includes 9 tables with proper foreign key relationships and indexes.

**Positive Factor (DATA-Q4 = 4):**
No stored procedures, triggers, or proprietary SQL. All business logic is in the PHP application layer using standard SQL. This significantly reduces migration complexity — no schema conversion tool (SCT) work is needed for SQL compatibility.

**Recommended Migration Target:**
- **Amazon Aurora MySQL** (preferred) — Drop-in MySQL compatibility with up to 5x throughput improvement, automated backups, Multi-AZ failover, and read replicas. Aurora is the recommended target given the MySQL 8.0 source engine and the `prefer: ["aurora"]` preference.
- **Amazon DynamoDB** (preferred) — Consider for the inventory domain (product catalog, stock quantities) as a service is extracted during decomposition. DynamoDB provides single-digit millisecond performance ideal for high-frequency inventory lookups required by restocking agents.

**Migration Approach:**
1. Provision Aurora MySQL using Terraform (aligned with Move to Modern DevOps pathway)
2. Use AWS DMS for continuous replication from self-managed MySQL to Aurora during cutover
3. Update connection strings (currently environment variables in docker-compose) to Aurora endpoint
4. Enable automated backups, PITR, and Multi-AZ failover
5. As services are extracted (Move to Cloud Native pathway), consider purpose-built databases per service (Aurora for orders/payments, DynamoDB for inventory)

**AWS Services:**
- Amazon Aurora MySQL, Amazon DynamoDB, AWS DMS, AWS Secrets Manager (for credential management)

**AWS Prescriptive Guidance:**
- [Migrate from MySQL to Amazon Aurora](https://docs.aws.amazon.com/prescriptive-guidance/latest/patterns/migrate-from-mysql-to-amazon-aurora-mysql.html)

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10 = 1):**
Zero infrastructure-as-code files exist in the repository. There are no Terraform files, no CloudFormation templates, no CDK stacks, and no Helm charts. All infrastructure is defined exclusively in `docker-compose.yml` for local development. There is no mechanism to reproduce the production environment, no drift detection, and no infrastructure audit trail.

**Current CI/CD State (INF-Q11 = 1):**
No CI/CD pipeline exists. The only deployment mechanism is `deploy.sh`, a 25-line bash script that runs `docker-compose build` and `docker-compose up -d`. There are no build stages, no test stages, no artifact management, no deployment gates, and no automated rollback.

**Deployment Strategy Gaps (OPS-Q5 = 1):**
`deploy.sh` performs a direct-to-production replacement with no staged rollout, no canary deployment, no blue/green strategy, and no health check validation beyond a basic `curl` test after deployment.

**Testing Gaps (OPS-Q6 = 1):**
No automated tests of any kind exist — no unit tests, no integration tests, no end-to-end tests, no test framework, and no test configuration. There is zero safety net for any code change.

**Recommended DevOps Toolchain:**
- **Terraform** (preferred) for all infrastructure provisioning — VPC, EKS cluster, Aurora, API Gateway, EventBridge, secrets, IAM roles
- **GitOps with ArgoCD or Flux** (preferred) for Kubernetes deployment management — declarative, auditable, self-healing deployments to EKS
- **GitHub Actions** for CI pipeline — build, test, security scan, container image build and push to ECR
- **Amazon ECR** for container image registry
- **AWS CodeDeploy** with EKS for blue/green or canary deployment strategies

**Recommended Implementation Order:**
1. **Week 1-2:** Initialize Terraform project structure. Define VPC, networking, and EKS cluster. Store state in S3 with DynamoDB locking.
2. **Week 2-3:** Create GitHub Actions CI pipeline — lint, build Docker image, push to ECR, run security scans (Snyk/Trivy).
3. **Week 3-4:** Configure GitOps (ArgoCD on EKS) for deployment. Define Helm chart for the monolith as-is.
4. **Week 4-6:** Add automated testing framework (PHPUnit for unit tests, Postman/Newman for API integration tests). Wire into CI pipeline.
5. **Week 6-8:** Implement blue/green deployment strategy. Add deployment gates and automated rollback.

**AWS Services:**
- AWS CodeBuild, AWS CodePipeline, Amazon ECR, AWS CloudFormation/CDK (alternative to Terraform), Amazon EKS, AWS X-Ray, Amazon CloudWatch

**AWS Prescriptive Guidance:**
- [Getting Started with DevOps on AWS](https://docs.aws.amazon.com/prescriptive-guidance/latest/strategy-devops/welcome.html)

---

### Pathway: Move to AI

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current AI/Agent Infrastructure State:**
No AI or agent infrastructure exists in the repository:
- ❌ No AI/agent framework imports (no Bedrock SDK, LangChain, Strands, OpenAI, Spring AI, HuggingFace, or SageMaker SDK)
- ❌ No vector database infrastructure (no OpenSearch vector engine, Pinecone, pgvector, Weaviate, or Qdrant)
- ❌ No RAG implementation (no embedding generation, vector store queries, or retrieval chains)
- ❌ No agent evaluation frameworks (no Ragas, DeepEval, or custom eval harness)

**Application Domain and AI Use Cases:**
The e-commerce fulfillment application has high potential for AI-driven automation based on the business domains discovered:

1. **Inventory Restocking Agent** (primary — per user context) — An agent that monitors inventory levels via the `/api/products` endpoint and makes autonomous restocking decisions. The existing inventory table with `stock_quantity` tracking provides the data foundation.
2. **Order Validation Agent** — The `/api/orders/{orderId}/validation-data` endpoint already returns fraud scores, risk factors, and recommendations. An agent using Amazon Bedrock could automate the manual validation step currently requiring human review.
3. **Warehouse Assignment Agent** — The `/api/warehouses/assignment-options` endpoint returns scored warehouse options with distance, cost, and delivery time. An agent could make optimal assignments autonomously.
4. **Return Processing Agent** — Returns currently require 24-48 hour manual CS review. An agent could evaluate return requests against policy rules and process straightforward returns automatically.

**Foundation Requirements Before AI Integration:**
- **API surface** (Move to Cloud Native) — Extract and version inventory APIs to create stable tool interfaces for agents
- **Managed database** (Move to Managed Databases) — Move to Aurora for reliable data access; consider DynamoDB for real-time inventory lookups
- **CI/CD pipeline** (Move to Modern DevOps) — Required to deploy and iterate on agent services
- **Observability** — Add structured logging and tracing before deploying autonomous agents

**Recommended AI Services:**
- **Amazon Bedrock** (preferred) — Foundation model access for reasoning, decision-making, and natural language processing in agent workflows
- **Amazon Bedrock AgentCore** — Managed infrastructure for deploying and orchestrating AI agents
- **Amazon Bedrock Knowledge Bases** — RAG capability using product catalog and order data as knowledge sources
- **Amazon OpenSearch Service** (vector engine) — Vector search for product similarity, recommendation, and inventory matching

**Quick Wins (post-foundation):**
Once the inventory API is extracted and versioned (Move to Cloud Native + Modern DevOps), the first AI integration should be an **inventory restocking agent** using Bedrock that calls the inventory API as a tool, monitors stock levels, and triggers restock orders — directly addressing the stated context.

**AWS Prescriptive Guidance:**
- [Amazon Bedrock Getting Started](https://docs.aws.amazon.com/bedrock/latest/userguide/what-is-bedrock.html)
- [Building AI Agents](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)

## Decomposition Strategy

> **Condition:** APP-Q2 = 1 (< 3). The application is a tightly-coupled PHP monolith with no module boundaries.

### Approach Options

| Approach | Description | When to Use | Level of Effort | Recommendation |
|----------|-------------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | Incrementally extract services from `index.php` while keeping the monolith running. New features built as services; existing features migrated over time. Start with the **Inventory Service** to expose APIs for agent-driven restocking. | This monolith has identifiable business domains (orders, inventory, payments, returns, shipping, user management, warehouse operations) despite being in one file. These can be extracted one at a time. | **High** — 12-18 months given the severity of coupling (single file, shared DB, no tests, no CI/CD). Each extraction is bounded but requires building foundational capabilities first. | ✅ **Recommended.** Lowest risk, incremental value delivery. Start with Inventory Service extraction to unlock agent integration immediately. |
| **Conditional / Adaptive** | Deploy the monolith as-is to EKS (Dockerfile already exists), then selectively extract high-value services based on business priority. Not all domains need to become services. | Team has limited capacity. Business pressure requires quick wins (get the monolith running on managed infrastructure) before full decomposition. | **Low to Medium** initial (2-4 weeks to deploy to EKS), then **Medium** per extraction (3-6 months each). | ✅ **Recommended when capacity is constrained.** Gets the monolith onto managed compute quickly, then prioritize Inventory Service extraction. |
| **Big-Bang Rewrite** | Rewrite the entire application as microservices from scratch. | Almost never. Only if the monolith is truly unmaintainable. | **Very High** — 18-24+ months. High risk of scope creep and feature parity gaps. | ⚠️ **Recommended against.** The monolith is functional with well-structured API endpoints. Strangler Fig is safer. |

### Recommended Starting Point: Inventory Service

Per the assessment context ("expose inventory APIs the agent needs for restocking decisions"), the **Inventory Service** should be the first extraction target:

1. **Extract scope:** The `/api/products` GET endpoint and the `inventory` table (product_id, product_name, description, price, stock_quantity, category, warehouse_location, weight_lbs, dimensions).
2. **New service:** Deploy as an independent EKS pod with its own Aurora MySQL or DynamoDB table.
3. **API Gateway:** Place behind Amazon API Gateway with versioning (`/v1/inventory/products`), authentication (Cognito), and throttling.
4. **Anti-corruption Layer:** Route inventory reads to the new service; the monolith continues to handle inventory writes initially. Use EventBridge to sync inventory changes.
5. **Agent integration:** Once the versioned Inventory API is live, the Bedrock-powered restocking agent can call it as a tool.

### Pattern Recommendations

| Pattern | Purpose | When to Apply | AWS Prescriptive Guidance |
|---------|---------|---------------|---------------------------|
| **Anti-corruption Layer (ACL)** | Isolate new Inventory Service from the monolith's data model. Prevent monolith schema leaking into the new service. | First extraction — place ACL between Inventory Service and monolith to translate between models. | [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) |
| **Saga Pattern** | Manage distributed transactions for order creation (order → payment → inventory deduction) that are currently a single DB transaction in `index.php`. | When extracting Orders or Payments service — cross-service transactions need coordination. | [Saga pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga.html) |
| **Event Sourcing** | Capture inventory changes and order status transitions as events. The `order_status_history` table already captures state changes — evolve into a proper event store on EventBridge. | When extracting services that need to react to inventory changes (restocking agent, warehouse assignment). | [Event sourcing pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/event-sourcing.html) |
| **Hexagonal Architecture (Ports and Adapters)** | Structure each new service with clear boundaries between business logic, API interfaces, and infrastructure adapters. | Every new service — ensures testability, portability, and decoupling from specific infrastructure. | [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |

### Effort Estimation Factors

| Factor | Signal | Evidence | Impact |
|--------|--------|----------|--------|
| Module boundaries | 🔴 HIGH effort | No boundaries — all logic in single `index.php` file. All business domains interleaved. | Must identify and draw service boundaries from scratch. |
| Data coupling | 🔴 HIGH effort | Single shared MySQL database with 9 tables. Cross-domain queries exist (e.g., `JOIN order_items oi ... JOIN inventory i` in picking-details and packing-options endpoints). | Database-per-service requires data migration and query refactoring. |
| Stored procedures | 🟢 LOW effort | Zero stored procedures, triggers, or proprietary SQL (DATA-Q4 = 4). All logic in PHP. | No database-level logic to extract. Clean separation possible. |
| Communication patterns | 🔴 HIGH effort | All synchronous in-process (APP-Q3 = 1). No event bus or message queue. | Must introduce EventBridge for inter-service communication. |
| CI/CD maturity | 🔴 HIGH effort | No CI/CD pipeline (INF-Q11 = 1). Only manual deploy.sh. | Must build CI/CD foundation before safe extraction. |
| Test coverage | 🔴 HIGH effort | Zero automated tests (OPS-Q6 = 1). No unit, integration, or API tests. | Regression risk during extraction. Must add tests before and during extraction. |

**Calibrated Estimate:** **HIGH** effort for the Strangler Fig approach. The combination of zero module boundaries, single shared database, no CI/CD, and no tests creates compounding risk. However, the **absence of stored procedures** (DATA-Q4 = 4) and the use of **standard SQL** means database separation is mechanically simpler than typical legacy systems. The **Conditional/Adaptive approach** (deploy to EKS first, then extract) is recommended to deliver early wins while building the foundational capabilities needed for safe decomposition.

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All compute runs as local Docker containers via `docker-compose.yml`. The `Dockerfile` uses `php:8.2-apache` base image. The `docker-compose.yml` defines two services: `mysql` and `monolith`. No AWS managed compute resources exist — no ECS tasks, EKS pods, Lambda functions, Fargate services, or EC2 instances defined in IaC (no IaC exists). The context mentions "App Runner" but no App Runner configuration exists in the repository. |
| **Gap** | No managed container orchestration or serverless compute. The application runs only as local Docker containers with no production-grade compute platform. |
| **Recommendation** | Deploy the containerized monolith to **Amazon EKS** (preferred) as the first step. The existing Dockerfile provides the foundation. Create a Helm chart, push the image to ECR, and deploy to an EKS cluster provisioned via Terraform. This enables auto-scaling, rolling deployments, and managed infrastructure immediately. |
| **Evidence** | `Dockerfile` (FROM php:8.2-apache), `docker-compose.yml` (services: mysql, monolith) |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | MySQL 8.0 runs as a self-managed Docker container (`image: mysql:8.0` in `docker-compose.yml`). Data is stored in a Docker volume (`mysql_data`). Database credentials passed via environment variables (`${MYSQL_ROOT_PASSWORD}`, `${MYSQL_PASSWORD}`). No managed database services (RDS, Aurora, DynamoDB, DocumentDB) are defined. |
| **Gap** | The database is entirely self-managed with no automated backups, no failover, no encryption at rest, and no patching. A Docker volume failure would result in complete data loss. |
| **Recommendation** | Migrate to **Amazon Aurora MySQL** (preferred). Aurora provides MySQL compatibility, automated backups with PITR, Multi-AZ failover, read replicas, and encryption at rest. Use AWS DMS for migration. Store credentials in AWS Secrets Manager with automatic rotation. |
| **Evidence** | `docker-compose.yml` (image: mysql:8.0, volumes: mysql_data), `index.php` (get_db() function with env var connection) |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No workflow orchestration service exists. The order fulfillment workflow (validate → assign warehouse → pick → pack → quality check → ship → deliver) is implemented as sequential API endpoints in `index.php`. Each step is a separate HTTP endpoint that must be called manually by the admin UI. No Step Functions, Temporal, or any state machine implementation. |
| **Gap** | All workflow logic is hardcoded as individual API endpoints with no orchestration, no retry logic, no error compensation, and no visibility into workflow state. Each step requires manual human intervention via the admin UI. |
| **Recommendation** | Implement **AWS Step Functions** to orchestrate the fulfillment workflow. Define the validate → assign → pick → pack → QC → ship pipeline as a Step Functions state machine with error handling, retries, and parallel execution. This becomes the execution surface for AI agents to trigger workflow steps. |
| **Evidence** | `index.php` (fulfillment endpoints: /api/orders/{id}/validate, /assign-warehouse, /pick, /pack, /quality-check, /ship, /deliver) |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No messaging or streaming infrastructure exists. No SQS, SNS, EventBridge, MSK, or Kinesis resources. No message queue or event bus patterns in the code. All communication is synchronous in-process PHP function calls within the monolith. Inventory updates, payment processing, and order status changes all happen in synchronous database transactions. |
| **Gap** | No event-driven patterns. Domain events (order placed, inventory updated, return requested) are not published — they only exist as database state changes. No decoupling between business domains. |
| **Recommendation** | Introduce **Amazon EventBridge** (preferred) as the central event bus. Publish domain events (OrderPlaced, InventoryUpdated, ReturnRequested) from each service as they are extracted. EventBridge enables the restocking agent to react to inventory changes in real-time. |
| **Evidence** | `index.php` (all API routes use synchronous database transactions), `docker-compose.yml` (no messaging services defined) |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, or NACL configuration exists. No IaC defines any networking resources. `docker-compose.yml` exposes port 8080 (application) and port 3306 (MySQL) directly. The MySQL port is exposed to the host network with no access control beyond the Docker bridge network. |
| **Gap** | No network segmentation, no private subnets, no security groups, no network access controls. The MySQL database is directly accessible on port 3306. |
| **Recommendation** | Define a VPC with public and private subnets in **Terraform** (preferred). Place the EKS cluster and Aurora database in private subnets. Use security groups with least-privilege rules. Only the API Gateway or ALB should be in public subnets. MySQL (Aurora) should never be directly accessible from the internet. |
| **Evidence** | `docker-compose.yml` (ports: "8080:80", "3306:3306") |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API Gateway, ALB, or CloudFront exists. The application is accessed directly on port 8080 via the Docker container. The `.htaccess` file configures Apache mod_rewrite to route all requests to `index.php`. No throttling, no rate limiting, no request validation, and no authentication at the gateway level. |
| **Gap** | No managed entry point. All traffic hits the application directly with no protection against abuse, no request validation, and no centralized authentication. |
| **Recommendation** | Deploy **Amazon API Gateway** (preferred) as the entry point. Configure throttling, request validation, and Cognito-based authentication. API Gateway provides the tool discovery surface that agents need to invoke inventory APIs. |
| **Evidence** | `docker-compose.yml` (ports: "8080:80"), `.htaccess` (RewriteRule to index.php) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No auto-scaling configuration exists. The application runs as a single Docker container instance with static capacity. No ASG, no ECS service auto-scaling, no Lambda concurrency configuration, and no Kubernetes HPA. |
| **Gap** | No ability to respond to traffic spikes or scale down during low demand. Single container instance means any spike in restocking agent queries could overwhelm the application. |
| **Recommendation** | Configure Kubernetes Horizontal Pod Autoscaler (HPA) on EKS deployment based on CPU/memory utilization and request latency. For the extracted Inventory Service, configure auto-scaling based on API request volume. |
| **Evidence** | `docker-compose.yml` (single instance per service, no scaling configuration) |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration exists. MySQL data is stored in a Docker volume (`mysql_data`) with no backup plan, no snapshot schedule, no PITR, and no tested restore procedure. There is no `backup_retention_period`, no `aws_backup_plan`, and no S3 versioning. |
| **Gap** | A Docker volume failure, host failure, or accidental data deletion would result in complete, irrecoverable data loss. No restore procedure exists or has been tested. |
| **Recommendation** | Aurora MySQL (recommended target) provides automated daily backups with configurable retention (up to 35 days) and continuous PITR. Enable both immediately upon migration. Test restore procedures quarterly. |
| **Evidence** | `docker-compose.yml` (volumes: mysql_data — no backup configuration) |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Single container instance for the application and single MySQL container. No multi-AZ deployment, no replica configuration, no cross-zone load balancing. No fault isolation of any kind. |
| **Gap** | Any single failure (container crash, host failure, disk failure) takes down the entire application and database with no automatic recovery. |
| **Recommendation** | Deploy to EKS with pods across multiple Availability Zones. Configure Aurora MySQL with Multi-AZ deployment for automatic database failover. Use ALB or API Gateway with cross-zone load balancing. |
| **Evidence** | `docker-compose.yml` (single instance per service), absence of any HA configuration |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Zero IaC files exist in the repository. No Terraform (`.tf`), no CloudFormation (`template.yaml`), no CDK (`cdk.json`), no Helm charts (`Chart.yaml`), and no Kustomize (`kustomization.yaml`). The only infrastructure definition is `docker-compose.yml` which is a local development tool, not production IaC. |
| **Gap** | 100% of infrastructure is manually created or undefined. No reproducible environments, no drift detection, no infrastructure audit trail, no disaster recovery capability. |
| **Recommendation** | Initialize a **Terraform** (preferred) project to define all infrastructure: VPC, subnets, security groups, EKS cluster, Aurora MySQL, API Gateway, EventBridge, ECR, IAM roles, and Secrets Manager. Store Terraform state in S3 with DynamoDB locking. Implement GitOps (preferred) for deployment management. |
| **Evidence** | Repository file listing: no `.tf`, `.cfn.yaml`, `cdk.json`, `Chart.yaml`, or `kustomization.yaml` files found |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CI/CD pipeline exists. No GitHub Actions (`.github/workflows/`), no GitLab CI (`.gitlab-ci.yml`), no Jenkins (`Jenkinsfile`), no CodeBuild (`buildspec.yml`), and no CodePipeline. The only deployment mechanism is `deploy.sh`, a manual bash script that runs `docker-compose build` followed by `docker-compose up -d` with a basic curl health check. |
| **Gap** | All deployments are manual with no automated testing, no security scanning, no artifact management, no deployment gates, and no rollback capability. |
| **Recommendation** | Create a GitHub Actions CI/CD pipeline with stages: lint → test → build Docker image → push to ECR → security scan (Snyk/Trivy) → deploy to EKS via GitOps (ArgoCD). Add deployment gates and automated rollback on health check failure. |
| **Evidence** | `deploy.sh` (docker-compose build/up), absence of `.github/workflows/`, `buildspec.yml`, `Jenkinsfile`, `.gitlab-ci.yml` |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | PHP 8.2 detected from `Dockerfile` (`FROM php:8.2-apache`). The entire application is written in PHP with embedded HTML/CSS/JavaScript for the frontend. PHP 8.2 is a modern version with type hints, named arguments, fibers, and readonly properties. However, per the assessment rubric, PHP has a more limited cloud-native ecosystem compared to Python, TypeScript, Go, or Java. |
| **Gap** | PHP has fewer cloud-native frameworks, limited serverless support (no native Lambda runtime, though custom runtimes exist), and a smaller ecosystem of AWS SDK integrations compared to Python or TypeScript. No PHP package manager (Composer) is used — dependencies are installed directly via `apt-get` in the Dockerfile. |
| **Recommendation** | As services are extracted during decomposition, consider using languages with stronger cloud-native ecosystems (Python, TypeScript, or Go) for new services, while keeping the PHP monolith stable during migration. The extracted Inventory Service could be implemented in Python or TypeScript with richer Bedrock SDK support for agent integration. |
| **Evidence** | `Dockerfile` (FROM php:8.2-apache), `index.php` (PHP source code) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The entire application is a single PHP file (`index.php`, ~2000+ lines) containing ALL business domains: orders (creation, validation, fulfillment workflow), inventory (products, stock management), payments (processing, refunds), returns (submission, review, approval), shipping (carrier selection, tracking), user management (CRUD, authentication), warehouse operations (assignment, picking, packing, quality checks), and the complete HTML/CSS/JavaScript frontend. All domains share a single MySQL database with 9 tables. All API routes are defined in one routing block using regex pattern matching. There are no module boundaries, no namespace separation, no service directories, and no independent deployable units. |
| **Gap** | Tightly-coupled monolith with no clear module boundaries and pervasive shared state. Cannot scale domains independently. Cannot deploy changes to inventory without risking payments. Cannot assign separate teams to different domains. The tight coupling directly blocks the stated goal of exposing inventory APIs for agent-driven restocking. |
| **Recommendation** | Implement the Strangler Fig decomposition strategy (see Decomposition Strategy section). Extract the Inventory Service first to expose versioned APIs for the restocking agent. Use the Anti-corruption Layer pattern to isolate the new service from the monolith. |
| **Evidence** | `index.php` (single file with all domains), `docker-compose.yml` (single monolith service), `index.php:init_db()` (shared 9-table schema) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All communication is synchronous. The monolith processes everything in-process via synchronous PHP request/response cycles. Order creation atomically deducts inventory and processes payment in a single database transaction (`$db->beginTransaction()` / `$db->commit()`). The fulfillment workflow requires sequential manual HTTP calls from the admin UI. No message queues, event bus, or async patterns exist. No SQS, SNS, EventBridge, or any pub/sub mechanism. |
| **Gap** | No async patterns for any operation. Synchronous processing means cascading failures — if the payment portion of order creation fails, the entire transaction rolls back including inventory changes. No ability to react to domain events asynchronously. |
| **Recommendation** | Introduce **Amazon EventBridge** (preferred) for inter-service event publishing as services are extracted. The order creation flow should publish `OrderCreated` events that trigger downstream processes (payment, inventory deduction) asynchronously via the Saga pattern. |
| **Evidence** | `index.php` (POST /api/orders — synchronous transaction), `index.php` (all fulfillment endpoints — synchronous HTTP) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All operations are synchronous and blocking. The return processing flow requires 24-48 hours of manual CS review but has no async pattern — the return is created synchronously and the customer is told to wait for an email. The order fulfillment workflow has multiple steps (validate, assign warehouse, pick, pack, QC, ship) but each is a separate synchronous API call requiring manual intervention. No background job framework (no Celery, Bull, or PHP-based queue workers), no status polling APIs, no webhook callbacks. |
| **Gap** | No mechanism for handling operations that take more than a few seconds. No job queue, no async status tracking, no callback mechanisms. The manual fulfillment workflow is the most obvious candidate for automation. |
| **Recommendation** | Implement **AWS Step Functions** for the fulfillment workflow with async step execution and status polling. For return processing, use an SQS queue with a Lambda consumer that evaluates return requests against policy rules. Expose status polling endpoints (`GET /api/returns/{id}/status`) for long-running processes. |
| **Evidence** | `index.php` (POST /api/returns — synchronous with "24-48 hours" message), `index.php` (fulfillment endpoints — each requires manual HTTP call) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API versioning exists. All API routes are unversioned: `/api/products`, `/api/orders`, `/api/returns`, `/api/admin/pending-returns`, `/api/orders/{id}/validate`, etc. No `/v1/` prefix, no `Accept-Version` headers, no query parameter versioning. No API changelog or deprecation policy. No OpenAPI specification. |
| **Gap** | Any API change breaks all consumers immediately. When the restocking agent is integrated, API changes could break agent tool invocations with no graceful migration path. |
| **Recommendation** | Add API versioning as part of service extraction. The extracted Inventory Service should launch with `/v1/` prefix (e.g., `/v1/inventory/products`). Define versioning strategy in the API Gateway configuration. Generate an OpenAPI specification for each versioned API to enable agent tool discovery. |
| **Evidence** | `index.php` (all routes: /api/products, /api/orders, /api/returns — no version prefix) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No service discovery mechanism exists. The monolith connects to MySQL via hardcoded environment variables (`DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASS`) with fallback defaults in the `get_db()` function (`$host = getenv('DB_HOST') ?: 'mysql'`). No AWS Service Discovery, no App Mesh, no Istio, no Consul, and no API catalog. Since the application is a monolith, inter-service communication is in-process — there are no external service calls. |
| **Gap** | All endpoint configuration is hardcoded. As services are extracted, there is no mechanism for dynamic service-to-service routing. Agent integration requires discoverable API endpoints. |
| **Recommendation** | Implement Kubernetes DNS-based service discovery on EKS for extracted services. Register APIs in **Amazon API Gateway** (preferred) which serves as both the entry point and the API catalog. For agent tool discovery, publish OpenAPI specs to API Gateway. |
| **Evidence** | `index.php` (get_db() with hardcoded env var fallbacks: `$host = getenv('DB_HOST') ?: 'mysql'`) |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No unstructured data storage exists. No S3 buckets, no document management system, no file upload handling. Product images are referenced as static URL paths (`/images/tshirt.jpg`, `/images/jeans.jpg`, etc.) in seed data but no actual image storage or serving infrastructure is configured. No Textract, Tika, or document parsing capabilities. |
| **Gap** | No managed object storage for unstructured data. Product images have no actual storage backend. No document parsing capability for potential AI-driven content analysis. |
| **Recommendation** | Create an S3 bucket for product images and unstructured assets. Configure CloudFront for image delivery. As AI capabilities are added, S3 provides the storage layer for Amazon Bedrock Knowledge Bases to index product documentation and catalog data. |
| **Evidence** | `index.php` (seed_data: image_url references like '/images/tshirt.jpg' with no storage backend) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The `get_db()` function provides a single PDO connection, but there is no unified data access layer. SQL queries are scattered throughout the entire `index.php` file — every API route handler contains inline SQL using `$db->prepare()` and `$db->query()`. Queries span all 9 tables across all business domains: orders, order_items, inventory, payments, returns, interactions, order_status_history, warehouses, and users. There is no repository pattern, no DAO layer, no ORM (no Doctrine, no Eloquent), and no query builder abstraction. Cross-domain joins exist (e.g., `SELECT oi.*, i.warehouse_location FROM order_items oi LEFT JOIN inventory i` in the picking-details endpoint). |
| **Gap** | Database access is completely scattered with no abstraction. Every endpoint directly constructs and executes SQL. No data contracts, no access control at the data layer, and no way to enforce consistent query patterns. This makes database separation during decomposition extremely difficult. |
| **Recommendation** | Before extracting services, introduce a repository pattern for each business domain (OrderRepository, InventoryRepository, PaymentRepository, etc.). This creates the seam along which services can be separated. Each repository becomes the foundation of its extracted service's data access layer. |
| **Evidence** | `index.php` (get_db() function, inline SQL in every route: SELECT * FROM inventory, SELECT * FROM orders, INSERT INTO payments, UPDATE inventory SET stock_quantity, etc.) |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | MySQL 8.0 is explicitly pinned in `docker-compose.yml` (`image: mysql:8.0`). This provides version awareness. However, the version is only defined in docker-compose (a development tool), not in production IaC (which does not exist). MySQL 8.0 LTS has extended support, but the self-managed deployment model means there is no automated patching, no lifecycle management, and no upgrade path defined. The `get_db()` function connects without specifying engine version requirements. |
| **Gap** | Version is pinned only in docker-compose.yml, not in production infrastructure. No IaC exists to enforce version constraints in production. No upgrade path defined. Self-managed deployment means manual patching responsibility. |
| **Recommendation** | When migrating to Aurora MySQL (Move to Managed Databases pathway), explicitly pin the Aurora engine version in Terraform. Enable Aurora automatic minor version upgrades. Establish a quarterly review cadence for major version upgrades. |
| **Evidence** | `docker-compose.yml` (image: mysql:8.0), `index.php` (get_db() — no version constraint in connection) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or functions exist. All business logic is in the PHP application layer (`index.php`). The schema uses standard SQL DDL (`CREATE TABLE IF NOT EXISTS`) with InnoDB engine, UTF8MB4 charset, foreign keys, and indexes. All queries use standard ANSI SQL compatible with MySQL — no proprietary SQL dialects (no T-SQL, no PL/SQL). All queries use PDO prepared statements with parameterized inputs. The schema is clean: 9 tables with clear relationships, proper foreign keys, and meaningful indexes. |
| **Gap** | None — this is the highest-scoring question. The absence of stored procedures and proprietary SQL is a significant positive factor for database migration and decomposition. |
| **Recommendation** | Maintain this practice as services are extracted. Keep all business logic in the application layer. When migrating to Aurora MySQL, the clean SQL means no schema conversion tool (SCT) work is needed — the schema can migrate as-is with DMS. |
| **Evidence** | `index.php` (init_db() function — 9 CREATE TABLE statements, all standard SQL; all queries use PDO prepared statements with no stored procedure calls) |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail or equivalent audit logging exists. No IaC defines logging resources. PHP error reporting is configured in `index.php` (`error_reporting(E_ALL); ini_set('display_errors', '0'); ini_set('log_errors', '1')`) which logs PHP errors to Apache error log but provides no structured audit trail. No log aggregation, no centralized logging, and no log retention policy. |
| **Gap** | No audit trail for API calls, authentication events, data changes, or administrative actions. No ability to investigate security incidents or demonstrate compliance. The `order_status_history` table captures order state changes but is not an audit log — it does not capture who accessed what or when. |
| **Recommendation** | Enable AWS CloudTrail for API-level audit logging. Implement structured application-level audit logging using CloudWatch Logs. Log all authentication events, data mutations, and administrative actions with timestamps, user IDs, and request context. Configure log retention and immutable storage in S3. |
| **Evidence** | `index.php` (error_reporting/ini_set at top of file), absence of any CloudTrail or logging IaC |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No encryption at rest is configured. MySQL data stored in a Docker volume (`mysql_data`) with no encryption. No KMS keys defined. No `encryption_configuration` on any resource. The Docker volume uses the host filesystem's default settings with no explicit encryption. |
| **Gap** | All data at rest (customer PII, payment information, order details) is unencrypted. This is a critical security gap for an e-commerce application handling payment data. |
| **Recommendation** | When migrating to Aurora MySQL, enable encryption at rest with a customer-managed KMS key. Enable encryption on all data stores (S3 buckets, EBS volumes, Secrets Manager). Define a KMS key policy with least-privilege access in Terraform. |
| **Evidence** | `docker-compose.yml` (volumes: mysql_data — no encryption), absence of any KMS or encryption configuration |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Session-based authentication exists. PHP sessions are used with login/password authentication. Passwords are hashed with bcrypt (`password_hash($password, PASSWORD_BCRYPT)`). API routes check `$_SESSION['user']` and return HTTP 401 if not authenticated. Admin routes additionally check `$_SESSION['user']['role'] === 'admin'` and return HTTP 403 if not authorized. The login flow validates credentials against the `users` table. However, this is basic session auth — no OAuth2, no JWT, no token-based auth, no API keys, no token refresh/expiry. |
| **Gap** | Session-based auth is not suitable for API consumers (agents, external services). No token-based auth means no stateless authentication, no token expiry, and no fine-grained scopes. The restocking agent cannot authenticate via sessions. |
| **Recommendation** | Implement **Amazon Cognito** for centralized authentication with OAuth2/JWT. Configure API Gateway authorizers with Cognito User Pools. Issue JWT tokens with scopes for different API operations (read-inventory, manage-orders, admin). Agent authentication should use machine-to-machine client credentials flow. |
| **Evidence** | `index.php` (session_start(), $_SESSION['user'] checks, password_hash with PASSWORD_BCRYPT, HTTP 401/403 responses) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The application manages its own authentication entirely. A `users` table in MySQL stores usernames, bcrypt-hashed passwords, names, emails, and roles. The login form posts to `/login` which validates against the database. No Cognito, Okta, Auth0, OIDC, SAML, or any external identity provider integration. No SSO capability. |
| **Gap** | Standalone authentication with no centralized identity management. Cannot participate in SSO, cannot federate with corporate directories, cannot enforce organization-wide security policies. User management is a manual process through the admin UI. |
| **Recommendation** | Migrate to **Amazon Cognito** User Pools as the centralized identity provider. Configure OIDC federation for corporate directory integration. Enable MFA for admin users. Use Cognito for both human users and machine-to-machine (M2M) agent credentials. |
| **Evidence** | `index.php` (users table schema, login form, password_verify, session-based auth), absence of any IdP configuration |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Database credentials are managed via environment variables in `docker-compose.yml` using `${MYSQL_ROOT_PASSWORD}`, `${MYSQL_PASSWORD}`, and `${MYSQL_USER}` syntax with required/default values. However, the `get_db()` function in `index.php` contains fallback defaults: `$user = getenv('DB_USER') ?: 'ecommerce_user'` and `$pass = getenv('DB_PASS') ?: 'ecommerce_pass'`. These fallback credentials are hardcoded in the source code. No Secrets Manager, no Vault, no credential rotation, and no audit trail for secret access. |
| **Gap** | Fallback credentials hardcoded in source code. No secrets management system. No credential rotation. Environment variables are passed in plaintext. Any developer with repository access can see the fallback database credentials. |
| **Recommendation** | Store all secrets in **AWS Secrets Manager** with automatic rotation. Remove hardcoded fallback credentials from source code. Configure EKS pods to retrieve secrets via the Secrets Store CSI driver. Define rotation schedules for database credentials and API keys. |
| **Evidence** | `index.php` (get_db(): `$pass = getenv('DB_PASS') ?: 'ecommerce_pass'`), `docker-compose.yml` (environment variables for credentials) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Good container security practices exist: the `Dockerfile` creates a non-root user (`appuser`) and switches to it (`USER appuser`). The `docker-compose.yml` configures both containers with `security_opt: no-new-privileges:true` and `read_only: true` with tmpfs for writable directories. Container healthchecks are configured. However, the base image is stock `php:8.2-apache` (not a hardened image like Bottlerocket or CIS-benchmarked). No vulnerability scanning (no Inspector, Snyk, or Trivy). No patching strategy. No ECR image scanning. Dependencies are installed via `apt-get` with no version pinning. |
| **Gap** | Container security basics are good but no vulnerability scanning, no patching strategy, and no hardened base images. Dependencies installed via `apt-get` may contain vulnerabilities that are never detected or remediated. |
| **Recommendation** | Add container image scanning (Trivy or Snyk) to the CI pipeline. Consider switching to a hardened base image (e.g., Chainguard PHP image). Pin `apt-get` package versions in the Dockerfile. Enable ECR image scanning for the production registry. Implement a quarterly base image update cadence. |
| **Evidence** | `Dockerfile` (USER appuser, non-root), `docker-compose.yml` (security_opt: no-new-privileges, read_only: true) |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No security scanning of any kind. No SAST (SonarQube, Semgrep, CodeGuru), no DAST, no dependency vulnerability scanning (Dependabot, Snyk, npm audit), no container scanning, and no security gates. No CI/CD pipeline exists to integrate security scanning into. No `.snyk` policy file, no `.dependabot` configuration, no `security.md`. |
| **Gap** | Vulnerabilities in PHP code, Docker base image, or apt-get packages reach production completely undetected. No security feedback loop. |
| **Recommendation** | When building the CI/CD pipeline (Move to Modern DevOps), integrate: (1) SAST — Semgrep or SonarQube for PHP code analysis, (2) dependency scanning — Trivy for container image vulnerabilities, (3) container scanning — ECR image scanning with blocking on critical/high findings, (4) secrets detection — git-secrets or gitleaks to prevent credential commits. |
| **Evidence** | Absence of `.github/workflows/`, `.snyk`, `.dependabot/config.yml`, `sonar-project.properties`, or any security scanning configuration |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing is instrumented. No X-Ray SDK, no OpenTelemetry SDK, no trace ID propagation. No tracing library in dependencies (no dependency manifest exists). No `traceparent` or `X-Amzn-Trace-Id` header handling. The application has no observability instrumentation of any kind. |
| **Gap** | No ability to trace requests through the system. When services are extracted, debugging cross-service failures will be impossible without tracing. Agent-driven workflows require trace correlation to monitor agent decision chains. |
| **Recommendation** | Instrument with **AWS X-Ray** or OpenTelemetry. Add the X-Ray SDK to the PHP application. When deploying to EKS, use the ADOT (AWS Distro for OpenTelemetry) sidecar for automatic trace propagation across services. |
| **Evidence** | Absence of any tracing SDK in `Dockerfile` dependencies or `index.php` imports |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLOs are defined. No availability targets, no latency budgets, no error rate thresholds. No CloudWatch alarms for p99/p95 latency. No error budget tracking. No SLO definition files or dashboards. The only health indicator is a basic Docker healthcheck (`curl -f http://localhost/api/products`). |
| **Gap** | No way to measure whether the system is meeting user expectations. No data to drive modernization prioritization. The restocking agent SLOs (response time, availability) cannot be defined without a baseline. |
| **Recommendation** | Define SLOs for critical user journeys: (1) Product listing availability ≥ 99.9%, (2) Order creation latency p99 < 2s, (3) Inventory API response time p99 < 500ms (critical for agent). Implement SLO monitoring with CloudWatch composite alarms and error budget tracking. |
| **Evidence** | `docker-compose.yml` (healthcheck: curl -f — basic health only), absence of any SLO definitions |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metrics are published. No CloudWatch `put_metric_data` calls. No business dashboards. No tracking of conversion rates, order fulfillment times, return rates, or inventory turnover. The only metrics are Docker-level healthchecks (binary up/down). |
| **Gap** | No visibility into business outcomes. Cannot measure fulfillment efficiency, inventory health, or customer satisfaction. Cannot evaluate the impact of agent-driven automation. |
| **Recommendation** | Publish custom CloudWatch metrics for: orders per hour, average fulfillment time, return rate, inventory stockout frequency, and agent decision accuracy (once agents are deployed). Create business dashboards in CloudWatch or Grafana. |
| **Evidence** | `index.php` (no metrics publishing code), absence of any CloudWatch or metrics configuration |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No alerting is configured. No CloudWatch alarms, no anomaly detection, no PagerDuty/OpsGenie integration. No static threshold alarms (CPU, memory, error rate). No notification mechanism for any operational event. |
| **Gap** | Failures go undetected until users report them. No proactive alerting for degradation, error spikes, or resource exhaustion. |
| **Recommendation** | Configure CloudWatch alarms for: (1) error rate > 1% (critical), (2) p99 latency > 2s (warning), (3) database connection failures (critical), (4) inventory stockout events (warning — for restocking agent triggers). Enable CloudWatch anomaly detection on error rates and latency. |
| **Evidence** | Absence of any alerting, monitoring, or notification configuration |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | Direct-to-production deployment with no staged rollout. `deploy.sh` runs `docker-compose build` then `docker-compose up -d`, which replaces the running container immediately. A basic health check (`curl -f http://localhost:8080/api/products`) runs after deployment with no automated rollback if it fails. No blue/green, no canary, no rolling deployment, no traffic shifting. |
| **Gap** | Every deployment is a full-risk, all-or-nothing replacement. A bad deployment takes down the entire application with no automatic recovery. No ability to test changes with a subset of traffic. |
| **Recommendation** | Implement blue/green or canary deployments on EKS using ArgoCD Rollouts or AWS CodeDeploy. Configure automated rollback based on health check failures and error rate increases. Start with rolling deployments with health checks, then evolve to canary with traffic shifting. |
| **Evidence** | `deploy.sh` (docker-compose build && docker-compose up -d, curl health check) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No automated tests of any kind exist. No PHPUnit, no Pest, no test directories, no test configuration files, no test fixtures. No integration tests, no unit tests, no end-to-end tests, no API tests (Postman/Newman), no contract tests. The repository contains zero test files. |
| **Gap** | Zero test coverage means every code change carries full regression risk. Decomposition without tests is extremely dangerous — extracting a service could break the monolith with no detection until production. The restocking agent cannot be validated without integration tests. |
| **Recommendation** | Before starting decomposition: (1) Add PHPUnit for unit tests targeting the business logic in index.php, (2) Add Postman/Newman API integration tests for all critical endpoints (/api/products, /api/orders, /api/returns), (3) Wire tests into the CI pipeline as a blocking gate. Focus test effort on the inventory domain first (extraction target). |
| **Evidence** | Absence of any test files, test directories, test configuration, or test framework in repository |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No incident response automation exists. No runbooks (markdown, YAML, or JSON). No Systems Manager Automation documents. No Lambda-based remediation. No self-healing patterns. No on-call rotation configuration. No incident management tool integration (PagerDuty, OpsGenie, Jira Service Management). |
| **Gap** | Incident response is entirely ad hoc. No documented procedures for common failure scenarios (database connection failure, container crash, deployment rollback). No automated remediation for any failure mode. |
| **Recommendation** | Create runbooks for common incidents: (1) database connection failure, (2) container crash loop, (3) deployment rollback procedure, (4) data recovery from backup. Implement Lambda-based auto-remediation for EKS pod restart and Aurora failover notification. Store runbooks in the repository as versioned markdown. |
| **Evidence** | Absence of any runbook files, SSM documents, or incident response configuration |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership exists. No per-service dashboards, no alarms with named owners, no CODEOWNERS file, no team attribution on any resource. No observability assets exist to own. |
| **Gap** | No accountability for system health. No clear ownership of monitoring, alerting, or incident response. When multiple services exist post-decomposition, unclear ownership will lead to monitoring gaps. |
| **Recommendation** | Define CODEOWNERS for observability assets. Create per-service CloudWatch dashboards with named team owners. Assign alarm ownership in PagerDuty/OpsGenie. Tag all observability resources with `team` and `service` tags. |
| **Evidence** | Absence of CODEOWNERS file, dashboards, alarms, or any observability configuration |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No AWS resource tagging exists because no AWS resources exist. No IaC resources to tag. No `default_tags` in Terraform provider (no Terraform exists). No `tags` on any resource. Docker-compose services have no tagging capability. |
| **Gap** | When AWS resources are provisioned (Move to Modern DevOps pathway), there is no tagging standard, no cost allocation framework, and no ownership attribution. |
| **Recommendation** | Define a tagging standard before provisioning infrastructure. Required tags: `Environment` (dev/staging/prod), `Service` (monolith/inventory/orders), `Team` (owner), `CostCenter`, `Project`. Configure `default_tags` in the Terraform AWS provider. Enforce tagging via AWS Config `required-tags` rules. |
| **Evidence** | Absence of any AWS resources or tagging configuration |

## Learning Materials

The following learning resources are mapped to the 4 triggered modernization pathways:

### Move to Cloud Native
- [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN)
- [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html)
- [Decompose monoliths into microservices](https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-decomposing-monoliths/welcome.html)

### Move to Managed Databases
- [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC)
- [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W)
- [Migrate from MySQL to Amazon Aurora](https://docs.aws.amazon.com/prescriptive-guidance/latest/patterns/migrate-from-mysql-to-amazon-aurora-mysql.html)

### Move to Modern DevOps
- [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)
- [EKS Workshop](https://www.eksworkshop.com/)

### Move to AI
- [Move to AI](https://skillbuilder.aws/learning-plan/VDFEE4ACCV)
- [Amazon Bedrock Getting Started](https://skillbuilder.aws/learn/63KTRM86DQ)
- [Introduction to Agentic AI on AWS](https://skillbuilder.aws/learn/DNBD5MT8ZD)

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `Dockerfile` | INF-Q1, APP-Q1, SEC-Q6, SEC-Q7 | PHP 8.2-apache base image; non-root user (appuser); dependency installation via apt-get; container build definition |
| `docker-compose.yml` | INF-Q1, INF-Q2, INF-Q4, INF-Q5, INF-Q6, INF-Q7, INF-Q8, INF-Q9, DATA-Q3, SEC-Q2, SEC-Q5, SEC-Q6, OPS-Q2 | Service definitions (mysql:8.0, monolith); port exposure (8080, 3306); Docker volumes (mysql_data); environment variables for credentials; security_opt; read_only; healthchecks |
| `index.php` | All 37 questions | Single monolith file containing: get_db() database connection, init_db() schema (9 tables), seed_data(), session auth, API routing, all business logic (orders, inventory, payments, returns, shipping, warehouse, users, quality checks), and full HTML/CSS/JS frontend |
| `deploy.sh` | INF-Q11, OPS-Q5 | Manual deployment script: docker-compose build, docker-compose up -d, basic curl health check |
| `.htaccess` | INF-Q6 | Apache mod_rewrite configuration routing all requests to index.php |
| `.gitignore` | Discovery | Standard gitignore; no .env files committed; no sensitive files excluded |
| `build.log` | Discovery | Contains "Analysis task - no build required" — no build artifacts |
