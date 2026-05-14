# Modernization Readiness Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | aws-microservices |
| **Date** | 2026-04-27 |
| **Repo Type** | application |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P0 |
| **Tags** | microservices, serverless, event-driven |
| **Context** | Event-driven serverless microservices (product, basket, ordering) with Lambda, DynamoDB, EventBridge, SQS. The agent will invoke these as tools for order status lookups and return processing. |
| **Overall Score** | 2.24 / 4.0 |

**Archetype Justification**: All three microservices (product, basket, ordering) own DynamoDB tables with read and write operations (CRUD). Each service manages persistent state through its own DynamoDB table. No high fan-out to 3+ downstream services detected (orchestrator), and no event-processor-only pattern — the ordering service consumes SQS events but also exposes API Gateway GET endpoints. Classified as stateful-crud.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 2.55 / 4.0 | 🟡 Partial |
| Application Architecture (APP) | 2.67 / 4.0 | 🟡 Partial |
| Data Platform Modernization (DATA) | 3.25 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 1.71 / 4.0 | 🟠 Needs Work |
| Operations & Observability (OPS) | 1.00 / 4.0 | ❌ Not Present |
| **Overall** | **2.24 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q11: CI/CD Automation | 1 | No CI/CD pipeline — all deployments are manual `cdk deploy`. | Blocks safe, repeatable deployments; prevents adoption of canary/blue-green strategies; triggers Move to Modern DevOps pathway. |
| 2 | OPS-Q5: Deployment Strategy | 1 | No deployment strategy — direct-to-production with no staged rollout. | Regressions reach all users instantly; no rollback capability; high blast radius for every change. |
| 3 | INF-Q5: Network Security | 1 | No VPC, subnets, or security groups — Lambda functions run in default AWS networking with public API Gateway. | Services are exposed to the internet without network-level isolation; no blast radius containment. |
| 4 | SEC-Q3: API Authentication | 1 | No authentication on any API Gateway endpoint — all endpoints are publicly accessible. | Any actor can invoke product, basket, and ordering APIs; critical for an e-commerce platform handling user data. |
| 5 | INF-Q8: Backup and Recovery | 1 | No DynamoDB PITR enabled; `removalPolicy: DESTROY` on all tables; no backup plans. | A table deletion or data corruption event results in permanent data loss for products, baskets, and orders. |

## Quick Agent Wins

### Data Query Agent

- **Prerequisite:** Database with clear, documented schema (DATA-Q2 ≥ 2). DATA-Q2 = 3 — each microservice has a centralized `ddbClient.js` module and well-defined DynamoDB table schemas (product: `id`/`name`/`description`/`price`/`category`, basket: `userName`/`items`, order: `userName`/`orderDate`/`totalPrice`/`firstName`/`lastName`/`email`).
- **What it enables:** A data query agent powered by Amazon Bedrock that translates natural language queries into DynamoDB operations. The agent could handle order status lookups ("What orders does user swn have?"), product searches ("Show me all products under $50"), and basket contents queries — aligning directly with the stated goal of agent-based order status lookups and return processing.
- **Additional steps:** Generate an API specification (OpenAPI) from the CDK-defined API Gateway routes to enable full tool discovery. Add a status field to the order table schema for return processing workflows.
- **Effort:** Medium

### RAG-Based Knowledge Agent

- **Prerequisite:** Documentation exists in the repository. README.md provides architecture description, API endpoint examples, deployment instructions, and links to detailed Medium articles explaining the event-driven architecture.
- **What it enables:** A RAG-based knowledge agent that indexes the README, CDK construct definitions, and API route definitions to answer developer questions about the architecture — "How does checkout work?", "What events does the basket service publish?", "How do I add a new API endpoint?"
- **Additional steps:** Expand documentation corpus beyond the README — add ADRs (Architecture Decision Records), API endpoint documentation, and event schema documentation (the `checkoutbasketevents.json` is a good starting point).
- **Effort:** Low

### Workflow Automation Agent

- **Prerequisite:** Workflow orchestration in place (INF-Q3 ≥ 2). INF-Q3 = 2 — EventBridge + SQS checkout flow exists with a defined event pattern (`com.swn.basket.checkoutbasket` → `CheckoutBasketRule` → `OrderQueue` → ordering Lambda).
- **What it enables:** A workflow automation agent that monitors the EventBridge checkout event flow and SQS queue, detects failed order processing (DLQ messages, Lambda errors), and triggers remediation actions. The agent could also provide real-time checkout pipeline status to support agents handling customer inquiries.
- **Additional steps:** Add a dead-letter queue (DLQ) to the SQS OrderQueue for failed message capture. Instrument the ordering Lambda with structured logging for agent consumption. Add CloudWatch metrics for checkout success/failure rates.
- **Effort:** Medium

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 3 — application already has microservices architecture with well-defined service boundaries. |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1 = 4 — compute already runs on Lambda (serverless managed compute). Contextual guard: compute is already Lambda/serverless. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 — no stored procedures or proprietary SQL. No commercial database engines detected (DynamoDB only). |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 = 4 — all databases are DynamoDB (fully managed, serverless). |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 = 3 — managed messaging in place. No data processing workloads detected (no ETL, Glue, Kinesis, or analytics artifacts). |
| 6 | Move to Modern DevOps | **Triggered** | High | Medium | INF-Q11 = 1 (no CI/CD automation). OPS-Q5 = 1 (no deployment strategy). OPS-Q6 = 1 (no integration tests). |
| 7 | Move to AI | **Triggered** | Medium | Medium | AI intent detected in context ("agent"). No AI/agent frameworks, vector DB, RAG, or eval frameworks found in repository. |

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

**Current IaC Coverage (INF-Q10 = 3):**
All primary infrastructure is defined in AWS CDK (TypeScript): 3 DynamoDB tables, 3 Lambda functions, 3 API Gateway REST APIs, 1 EventBridge custom bus with rule, 1 SQS queue. However, no operational resources are defined in IaC — no CloudWatch alarms, no backup plans, no health checks, no dashboards. IaC coverage is approximately 70-80% of the total infrastructure surface.

**Current CI/CD State (INF-Q11 = 1):**
No CI/CD pipeline exists. Deployment is entirely manual via `cdk deploy` from a developer's local machine. No build automation, no test gates, no approval workflows, no deployment tracking. This is the most critical gap — every other DevOps improvement depends on having an automated pipeline.

**Deployment Strategy Gaps (OPS-Q5 = 1):**
No deployment strategy. Changes go directly to production with no staged rollout, no canary analysis, no blue/green switching, and no automated rollback. Lambda alias traffic shifting is not configured.

**Testing Gaps (OPS-Q6 = 1):**
The test file (`test/aws-microservices.test.ts`) exists but is entirely commented out. Jest is configured but no runnable tests exist. No unit tests, no integration tests, no API contract tests.

**Recommended DevOps Toolchain (aligned with preferences: prefer Terraform, GitOps; avoid manual deployments):**

1. **CI/CD Pipeline — GitHub Actions with CDK Pipelines or AWS CodePipeline:**
   - Create a GitHub Actions workflow (`.github/workflows/deploy.yml`) with stages: lint → test → cdk synth → cdk diff → cdk deploy
   - Alternatively, adopt [CDK Pipelines](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.pipelines-readme.html) for a self-mutating pipeline defined in CDK
   - Add approval gates for production deployments
   - Future state: migrate IaC to Terraform with GitOps workflow using Terraform Cloud or Atlantis (aligned with preference for Terraform and GitOps)

2. **Deployment Strategy — Lambda Alias Traffic Shifting:**
   - Configure Lambda aliases with weighted traffic shifting for canary deployments
   - Use CodeDeploy with Lambda deployment configuration (`LambdaCanary10Percent5Minutes`)
   - Add CloudWatch alarms as deployment health checks (rollback on elevated error rates)

3. **Testing Foundation:**
   - Uncomment and implement the CDK infrastructure test (`test/aws-microservices.test.ts`)
   - Add integration tests for each API endpoint using Jest + `supertest` or Postman/Newman
   - Add contract tests for the EventBridge event schema (`checkoutbasketevents.json`)

4. **IaC Operational Resources:**
   - Add CloudWatch alarms for Lambda errors, DynamoDB throttling, SQS dead-letter queue depth
   - Add DynamoDB backup plans (PITR)
   - Add resource tagging via CDK `Tags.of()` or `default_tags`

**Representative AWS Services:** CodePipeline, CodeBuild, CodeDeploy, CloudFormation (via CDK), CloudWatch, X-Ray

**Links:**
- [AWS CDK Pipelines](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.pipelines-readme.html)
- [AWS Lambda Deployment with CodeDeploy](https://docs.aws.amazon.com/lambda/latest/dg/lambda-rolling-deployments.html)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

### Pathway: Move to AI

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

**Current AI/Agent Infrastructure State:**
No AI or agent infrastructure exists in the repository. The discovery scan found:
- ❌ No AI/agent framework imports (no Bedrock SDK, LangChain, Strands, OpenAI, Spring AI, HuggingFace, SageMaker)
- ❌ No vector database infrastructure (no OpenSearch vector engine, Pinecone, pgvector, Weaviate, Qdrant)
- ❌ No RAG implementation (no embedding generation, no vector store queries, no retrieval chains)
- ❌ No agent evaluation framework (no Ragas, DeepEval, or custom eval harness)

**AI Intent from Context:**
The portfolio context explicitly states: *"The team is building a customer support agent that handles order inquiries, processes returns, and manages inventory restocking."* The service context confirms: *"The agent will invoke these as tools for order status lookups and return processing."* This represents a clear AI/agent use case with the microservices serving as agent tools.

**Application Domain and Potential AI Use Cases:**
Given the e-commerce microservices architecture (product catalog, basket, ordering), the following AI use cases are directly applicable:

1. **Customer Support Agent** — An Amazon Bedrock-powered agent that handles order status inquiries by invoking the Order API (`GET /order/{userName}`), processes returns by creating return events on EventBridge, and answers product questions by querying the Product API.
2. **Inventory Restocking Agent** — An agent that monitors order patterns and product catalog to recommend or trigger inventory restocking actions.
3. **Checkout Assistance** — An agent that helps customers complete checkout by querying basket contents and providing recommendations.

**Quick Wins:** See the [Quick Agent Wins](#quick-agent-wins) section above — the Data Query Agent, RAG Knowledge Agent, and Workflow Automation Agent are immediately actionable.

**Recommended AI Services (aligned with preferences: prefer Bedrock, EventBridge, API Gateway, DynamoDB):**

1. **Amazon Bedrock Agents** — Define agent actions that map to existing API Gateway endpoints (product CRUD, order query, basket operations). Each API endpoint becomes an agent tool.
2. **Amazon Bedrock AgentCore** — For production-grade agent deployment with built-in observability, session management, and guardrails.
3. **Amazon Bedrock Knowledge Bases** — Index product catalog data from DynamoDB for RAG-based product recommendations and search.
4. **Amazon EventBridge** — Already in place for the checkout flow. Extend with new event patterns for agent-initiated actions (return requests, restocking triggers).

**Foundation Requirements (what needs to be in place before AI integration):**
1. **API Specification (OpenAPI)** — Generate OpenAPI specs from the CDK-defined API Gateway routes. Bedrock Agents require OpenAPI schemas to discover and invoke tools. *Currently missing (APP-Q5 = 1).*
2. **API Authentication** — Add Cognito or IAM-based authentication to API Gateway endpoints. Agent invocations must be authenticated and authorized. *Currently missing (SEC-Q3 = 1).*
3. **Order Status Field** — Add an `orderStatus` field to the order DynamoDB table schema to support return processing workflows (pending → processing → shipped → delivered → return-requested → returned).
4. **Structured Logging** — Instrument Lambda functions with structured JSON logging and X-Ray tracing for agent action observability. *Currently missing (OPS-Q1 = 1).*

**Links:**
- [Amazon Bedrock Agents](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)
- [Amazon Bedrock AgentCore](https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore.html)
- [Introduction to Agentic AI on AWS](https://skillbuilder.aws/learn/DNBD5MT8ZD)

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | All compute workloads run on AWS Lambda (serverless). Three `NodejsFunction` Lambda functions are defined in `lib/microservice.ts`: `productLambdaFunction`, `basketLambdaFunction`, and `orderingLambdaFunction`. No EC2 instances, no self-managed containers. Lambda is fully managed serverless compute with automatic scaling, patching, and HA. |
| **Gap** | No gaps — all compute is on managed serverless. |
| **Recommendation** | Maintain current Lambda-based compute. Consider upgrading the Lambda runtime from `NODEJS_14_X` (EOL) to `NODEJS_20_X` or later for performance improvements and continued security support. |
| **Evidence** | `lib/microservice.ts` (3 NodejsFunction definitions with `Runtime.NODEJS_14_X`) |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | All three databases are DynamoDB tables defined in `lib/database.ts`: `product` (PK: `id`), `basket` (PK: `userName`), and `order` (PK: `userName`, SK: `orderDate`). All use `BillingMode.PAY_PER_REQUEST` (serverless). DynamoDB is fully managed with automatic multi-AZ replication, no patching, and no maintenance windows. |
| **Gap** | No gaps — all databases are fully managed DynamoDB. |
| **Recommendation** | Maintain DynamoDB. Current PAY_PER_REQUEST billing is appropriate for variable workloads. Consider adding DynamoDB Global Tables for multi-region resilience if the e-commerce platform requires cross-region availability. |
| **Evidence** | `lib/database.ts` (3 DynamoDB Table definitions with `BillingMode.PAY_PER_REQUEST`) |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No dedicated workflow orchestration service (no Step Functions, Temporal, MWAA). The checkout flow is implemented as a basic event chain: basket Lambda publishes to EventBridge → `CheckoutBasketRule` routes to SQS `OrderQueue` → ordering Lambda consumes and creates order. This is a two-step event chain, not a multi-step orchestrated workflow. No error handling, retry logic, or compensating actions are structured. The checkout process in `src/basket/index.js` performs: (1) get basket, (2) prepare order payload, (3) publish to EventBridge, (4) delete basket — with no rollback if step 4 fails after step 3 succeeds. |
| **Gap** | The checkout process is a multi-step business transaction (get basket → calculate total → publish event → delete basket → create order) without dedicated orchestration. If the EventBridge publish succeeds but basket deletion fails, the system enters an inconsistent state. No compensating actions or saga pattern. For stateful-crud archetype, this represents a significant gap. |
| **Recommendation** | Introduce AWS Step Functions to orchestrate the checkout workflow. Use a Step Functions Express Workflow to coordinate: validate basket → calculate total → publish checkout event → wait for order confirmation → delete basket. This provides built-in error handling, retry logic, and visual debugging. Align with EventBridge for event-driven triggers. |
| **Evidence** | `lib/eventbus.ts` (EventBridge bus + rule), `lib/queue.ts` (SQS queue), `src/basket/index.js` (`checkoutBasket` function with sequential steps and no rollback) |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Managed messaging infrastructure is in place: EventBridge custom bus (`SwnEventBus`) with the `CheckoutBasketRule` routing checkout events to SQS `OrderQueue`. The ordering Lambda is configured as an SQS event source consumer (`batchSize: 1`). Both EventBridge and SQS are AWS managed services. The basket-to-ordering communication uses async event-driven patterns (EventBridge → SQS). Product service is sync-only (correct for CRUD). |
| **Gap** | Async messaging covers the key checkout flow but no other cross-service communication paths. Product catalog changes (price updates, new products) do not emit events that other services could react to. No dead-letter queue (DLQ) configured on the SQS OrderQueue for failed message handling. |
| **Recommendation** | Add a DLQ to the SQS OrderQueue for failed order processing messages. Consider emitting product change events on EventBridge (e.g., `ProductUpdated`, `ProductCreated`) for downstream consumers. No need to adopt self-managed Kafka or RabbitMQ — EventBridge + SQS is the correct managed messaging stack for this architecture. |
| **Evidence** | `lib/eventbus.ts` (EventBridge `SwnEventBus`, `CheckoutBasketRule`), `lib/queue.ts` (SQS `OrderQueue`, `visibilityTimeout: 30s`, `batchSize: 1`), `src/basket/index.js` (`publishCheckoutBasketEvent`), `src/ordering/index.js` (`sqsInvocation`) |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnet, security group, or network segmentation is defined in the CDK stack. Lambda functions run in default AWS Lambda networking (not attached to a VPC). API Gateway endpoints are public-facing with no WAF, no API keys, no authentication. No VPC endpoints or PrivateLink configurations. No network policies. |
| **Gap** | Services are deployed with no network-level security. API Gateway endpoints accept traffic from any source. Lambda functions access DynamoDB over the public AWS network (not through VPC endpoints). This is a fundamental security gap for a P0 e-commerce platform handling user data (names, emails, payment info). |
| **Recommendation** | Add API Gateway resource policies or WAF to restrict access. For Lambda-to-DynamoDB communication, consider VPC deployment with VPC endpoints for DynamoDB if data sensitivity requires private networking. At minimum, add API Gateway throttling and usage plans to prevent abuse. |
| **Evidence** | `lib/aws-microservices-stack.ts` (no VPC construct), `lib/apigateway.ts` (no auth/throttling config), `lib/microservice.ts` (no VPC config on Lambda functions) |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | API Gateway (`LambdaRestApi`) is configured as the entry point for all three microservices: `productApi` (Product Service), `basketApi` (Basket Service), and `orderApi` (Order Service). Each API has resource-based routing (not proxy mode). However, no throttling, no authentication, no request validation, and no usage plans are configured on any API Gateway. |
| **Gap** | API Gateway exists as a load balancer/router but lacks the security and traffic management features that make it an effective entry point: no auth, no throttling, no request validation, no usage plans. |
| **Recommendation** | Add API Gateway features: (1) Cognito authorizers or Lambda authorizers for authentication (prefer Cognito for alignment with centralized identity), (2) Usage plans with API keys for rate limiting, (3) Request validators using JSON Schema models, (4) WAF integration for DDoS and bot protection. Consider consolidating the three separate API Gateways into a single API Gateway with service-specific resource paths for unified management. |
| **Evidence** | `lib/apigateway.ts` (3 `LambdaRestApi` instances with `proxy: false`, resource-based routing, no auth/throttling/validation) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | DynamoDB tables use `PAY_PER_REQUEST` billing mode, which provides automatic scaling without capacity planning. Lambda functions auto-scale by default (concurrent executions). SQS and EventBridge are inherently scalable managed services. The architecture is serverless, so auto-scaling is largely built-in. |
| **Gap** | No Lambda reserved or provisioned concurrency configured. No DynamoDB capacity alarms. No API Gateway throttling limits tuned for expected traffic patterns. While serverless auto-scaling is inherent, the absence of concurrency limits means a traffic spike could consume all available Lambda concurrency in the account, affecting other workloads. |
| **Recommendation** | Configure Lambda reserved concurrency on each function to prevent account-level concurrency exhaustion. Add CloudWatch alarms for DynamoDB throttling events. Configure API Gateway usage plans with appropriate rate limits. Consider Lambda provisioned concurrency for the product service if cold start latency is a concern. |
| **Evidence** | `lib/database.ts` (`BillingMode.PAY_PER_REQUEST`), `lib/microservice.ts` (no concurrency config on Lambda functions), `lib/apigateway.ts` (no throttling config) |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration found. All three DynamoDB tables have `removalPolicy: RemovalPolicy.DESTROY`, meaning CloudFormation stack deletion permanently destroys the tables and all data. DynamoDB Point-in-Time Recovery (PITR) is not enabled (CDK default is disabled). No AWS Backup plans defined. No S3 versioning (no S3 buckets exist). |
| **Gap** | Complete absence of backup and recovery. A `cdk destroy` or accidental stack deletion permanently destroys all product, basket, and order data. Without PITR, there is no way to recover from accidental data deletion or corruption within DynamoDB. This is a critical gap for a P0 e-commerce platform. |
| **Recommendation** | Immediately enable DynamoDB PITR on all three tables (`pointInTimeRecovery: true` in CDK). Change `removalPolicy` from `DESTROY` to `RETAIN` for production tables. Create an AWS Backup plan with defined retention periods for DynamoDB tables. Document and test restore procedures. |
| **Evidence** | `lib/database.ts` (`removalPolicy: RemovalPolicy.DESTROY` on all 3 tables, no `pointInTimeRecovery` property) |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | All infrastructure components are inherently multi-AZ: DynamoDB replicates data across multiple AZs automatically. Lambda runs across multiple AZs within a region. SQS, EventBridge, and API Gateway are regional services spanning all AZs. The serverless architecture eliminates single-AZ failure risks. |
| **Gap** | No gaps — the fully serverless architecture provides inherent multi-AZ high availability. |
| **Recommendation** | Maintain current serverless architecture. For enhanced resilience, consider DynamoDB Global Tables for multi-region availability if the e-commerce platform requires cross-region failover. |
| **Evidence** | `lib/database.ts` (DynamoDB — inherently multi-AZ), `lib/microservice.ts` (Lambda — inherently multi-AZ), `lib/queue.ts` (SQS — regional), `lib/eventbus.ts` (EventBridge — regional) |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | All primary infrastructure is defined in AWS CDK (TypeScript): 3 DynamoDB tables (`lib/database.ts`), 3 Lambda functions (`lib/microservice.ts`), 3 API Gateway REST APIs (`lib/apigateway.ts`), 1 EventBridge custom bus with rule (`lib/eventbus.ts`), 1 SQS queue (`lib/queue.ts`). CDK handles IAM role creation and permission grants (`grantReadWriteData`, `grantPutEventsTo`). |
| **Gap** | No operational or DR resources in IaC: no CloudWatch alarms, no CloudWatch dashboards, no DynamoDB backup plans, no VPC/networking resources, no WAF rules, no resource tags. Estimated IaC coverage: 70-80% (primary resources covered, operational resources absent). |
| **Recommendation** | Extend CDK stack to include: CloudWatch alarms (Lambda errors, DynamoDB throttling, SQS age of oldest message), DynamoDB PITR backup configuration, resource tagging, API Gateway WAF integration. Consider splitting into multiple CDK stacks (one per service) for independent deployment lifecycle. Future state: migrate to Terraform for alignment with GitOps preferences. |
| **Evidence** | `lib/aws-microservices-stack.ts` (single stack wiring all constructs), `lib/database.ts`, `lib/microservice.ts`, `lib/apigateway.ts`, `lib/eventbus.ts`, `lib/queue.ts` — no CloudWatch, no Backup, no VPC constructs |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CI/CD pipeline exists. No `.github/workflows/`, no `.gitlab-ci.yml`, no `Jenkinsfile`, no `buildspec.yml`, no `appspec.yml`, no CodePipeline definitions in CDK. The only deployment method is manual `cdk deploy` from a developer workstation. The `package.json` scripts section defines `build`, `watch`, `test`, and `cdk` commands but no deployment automation. |
| **Gap** | Complete absence of deployment automation. Every deployment requires a developer to manually run `cdk deploy`, which is error-prone, unrepeatable, and blocks adoption of deployment strategies (canary, blue/green). No test gates, no approval workflows, no deployment audit trail. |
| **Recommendation** | Create a CI/CD pipeline as the highest-priority modernization action. Start with GitHub Actions (`.github/workflows/deploy.yml`) with stages: (1) install dependencies, (2) lint, (3) run tests (`npm test`), (4) `cdk synth` + `cdk diff`, (5) manual approval for production, (6) `cdk deploy`. Alternatively, use CDK Pipelines for a self-mutating pipeline. Avoid manual deployments entirely (aligned with preferences). |
| **Evidence** | Repository root — no `.github/`, no CI/CD config files. `package.json` (no deploy scripts). `README.md` (deployment instructions: "run `cdk deploy`") |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | TypeScript and JavaScript. CDK infrastructure is written in TypeScript (~3.9.7). Lambda function handlers are in JavaScript using ES module imports with AWS SDK v3 (`@aws-sdk/client-dynamodb ^3.55.0`, `@aws-sdk/client-eventbridge ^3.58.0`). TypeScript/JavaScript has first-class AWS SDK coverage, broad cloud-native tooling, and a mature ecosystem for serverless development. |
| **Gap** | No gaps — TypeScript/JavaScript is a top-tier language for AWS cloud-native development. |
| **Recommendation** | Consider migrating Lambda handler code from JavaScript (`.js`) to TypeScript (`.ts`) for type safety and better developer experience, especially as the codebase grows. Update TypeScript from ~3.9.7 to 5.x for modern language features. |
| **Evidence** | `package.json` (`typescript: ~3.9.7`), `src/product/package.json`, `src/basket/package.json`, `src/ordering/package.json` (all use `@aws-sdk` v3) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Three independently deployable Lambda functions with clear service boundaries: (1) **Product** — CRUD operations on product catalog (`src/product/index.js`, DynamoDB `product` table), (2) **Basket** — basket management + checkout event emission (`src/basket/index.js`, DynamoDB `basket` table, EventBridge publish), (3) **Ordering** — SQS event consumption + order queries (`src/ordering/index.js`, DynamoDB `order` table). Each service has its own `package.json` with separate dependencies and its own DynamoDB table (no shared database). Services communicate via EventBridge events, not direct HTTP calls. |
| **Gap** | All three services are deployed from a single CDK stack (`AwsMicroservicesStack` in `lib/aws-microservices-stack.ts`), which couples their deployment lifecycle. A change to the product service requires redeployment of the basket and ordering infrastructure. This limits independent deployment velocity. |
| **Recommendation** | Split the single CDK stack into per-service stacks (product stack, basket stack, ordering stack) with shared infrastructure in a common stack (EventBridge bus, VPC if added). This enables independent deployment of each service. Consider separate repositories per service for full decoupling if the team grows. |
| **Evidence** | `lib/aws-microservices-stack.ts` (single stack), `lib/database.ts` (3 separate tables), `lib/microservice.ts` (3 separate Lambda functions), `src/product/package.json`, `src/basket/package.json`, `src/ordering/package.json` (independent dependency manifests) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The checkout flow (basket → ordering) uses fully async communication: basket Lambda publishes a `CheckoutBasket` event to EventBridge, which routes through the `CheckoutBasketRule` to SQS `OrderQueue`, consumed by the ordering Lambda. This is the only cross-service communication path. Product and basket services are sync API Gateway-driven (appropriate for direct CRUD). The ordering service handles both async (SQS/EventBridge consumption) and sync (API Gateway GET for order queries). |
| **Gap** | Only one async communication path exists (checkout). Product catalog changes are not propagated as events — if basket or ordering services need to reference product data, they would need to call the product API synchronously. For stateful-crud archetype, the current mix is adequate but could benefit from additional event-driven patterns. |
| **Recommendation** | Add EventBridge events for product lifecycle changes (`ProductCreated`, `ProductUpdated`, `ProductDeleted`) to enable downstream services to react to catalog changes without synchronous coupling. This aligns with the existing EventBridge infrastructure and avoids introducing self-managed messaging. |
| **Evidence** | `src/basket/index.js` (`publishCheckoutBasketEvent` — async publish to EventBridge), `src/ordering/index.js` (`sqsInvocation` — async consumption, `apiGatewayInvocation` — sync queries), `lib/eventbus.ts` (EventBridge rule routing to SQS) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The checkout process is the only potentially long-running operation. It is handled asynchronously: the basket Lambda publishes a checkout event to EventBridge and returns immediately (fire-and-forget). The ordering Lambda consumes the event from SQS and creates the order. All other operations are sub-second DynamoDB CRUD operations. |
| **Gap** | No status tracking or callback mechanism for checkout. After `POST /basket/checkout`, the caller receives a 200 response but has no way to verify that the order was successfully created. No order status endpoint exists — `GET /order/{userName}` retrieves orders but the caller must know to query after an unknown delay. For stateful-crud archetype, adding status tracking would improve the checkout experience. |
| **Recommendation** | Add an order status field to the order table schema and expose a `GET /order/{userName}/status` endpoint. Consider returning the expected `orderDate` timestamp from the checkout endpoint so callers know when to poll. Alternatively, implement WebSocket notifications via API Gateway WebSocket for real-time checkout status updates. |
| **Evidence** | `src/basket/index.js` (`checkoutBasket` — publishes event, returns immediately), `src/ordering/index.js` (`createOrder` — creates order with `orderDate` but no status field) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API versioning strategy. API routes are `/product`, `/basket`, `/order` with no version prefix (`/v1/`), no version headers (`Accept-Version`), no query parameter versioning. No changelog or API evolution documentation. Breaking changes would affect all consumers simultaneously. |
| **Gap** | Complete absence of versioning. Any breaking API change (field renames, removed endpoints, changed response formats) will break all consumers. This is critical for AI agent integration — agents need stable API contracts to function as tools. |
| **Recommendation** | Implement URL-based versioning (`/v1/product`, `/v1/basket`, `/v1/order`) as the simplest and most discoverable approach. Define an API evolution policy (additive changes without version bump, breaking changes require new version). Generate OpenAPI specifications from CDK API definitions — this serves both versioning documentation and Bedrock agent tool discovery. |
| **Evidence** | `lib/apigateway.ts` (routes: `/product`, `/basket/{userName}`, `/basket/checkout`, `/order`, `/order/{userName}` — no version prefix) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Service-to-resource communication uses CDK-injected environment variables: `DYNAMODB_TABLE_NAME` (each Lambda knows its own table name), `EVENT_BUSNAME` (basket Lambda knows the EventBridge bus). Services do not call each other via HTTP — the only inter-service communication is event-driven via EventBridge, which provides inherent decoupling (publisher doesn't know the consumer). |
| **Gap** | Environment variables are statically set at deploy time. If table names or bus names change, redeployment is required. No API catalog or service registry exists for the three API Gateway endpoints. While EventBridge provides event-driven decoupling, there is no mechanism for dynamic endpoint discovery if services need to call each other directly in the future. |
| **Recommendation** | For the current event-driven architecture, the environment variable approach is acceptable. If direct service-to-service communication is needed in the future, use AWS Cloud Map (Service Discovery) or API Gateway as a service catalog. Generate and publish OpenAPI specs for each API Gateway to serve as an API catalog (also required for Bedrock agent integration). |
| **Evidence** | `lib/microservice.ts` (environment variables: `DYNAMODB_TABLE_NAME`, `EVENT_BUSNAME`, `EVENT_SOURCE`, `EVENT_DETAILTYPE`), `lib/eventbus.ts` (EventBridge decoupled communication) |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | No S3 buckets or unstructured data storage defined. Product data is stored in DynamoDB with structured attributes (`id`, `name`, `description`, `imageFile`, `price`, `category`). The `imageFile` field in the product schema suggests image references, but no S3 bucket exists for actual image storage. No document parsing pipeline (no Textract, Tika). No file upload handling in any Lambda function. |
| **Gap** | Product images are referenced (`imageFile` field) but have no managed storage location. If images are stored externally, there is no integration. No S3 bucket for unstructured data (product images, order receipts, return documentation). For an e-commerce platform, image and document storage is a fundamental need. |
| **Recommendation** | Add an S3 bucket for product images with CDN (CloudFront) for delivery. For the AI agent use case (return processing), add S3 storage for return documentation and receipts. Consider Amazon Textract for automated document parsing if return forms need to be processed. |
| **Evidence** | `lib/database.ts` (DynamoDB tables only, no S3), `src/product/index.js` (product schema includes `imageFile` field but no S3 integration) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Each microservice has a centralized DynamoDB client module (`ddbClient.js`) that instantiates a `DynamoDBClient` and exports it for use by the handler. Within each service, all DynamoDB operations go through this shared client. Each service accesses only its own table — no cross-service data access. The pattern provides service-level data isolation. |
| **Gap** | The data access pattern is basic — raw DynamoDB commands (`GetItemCommand`, `PutItemCommand`, `ScanCommand`, `QueryCommand`) are used directly in handler functions with manual `marshall`/`unmarshall` calls. No repository/DAO abstraction layer. No data validation layer. Business logic and data access are interleaved in the handler functions. |
| **Recommendation** | Introduce a repository pattern within each service — separate data access logic from business logic. Create a `productRepository.js`, `basketRepository.js`, and `orderRepository.js` that encapsulate DynamoDB operations with typed interfaces. This improves testability, maintainability, and prepares for potential database changes. |
| **Evidence** | `src/product/ddbClient.js`, `src/basket/ddbClient.js`, `src/ordering/ddbClient.js` (centralized clients), `src/product/index.js` (raw DynamoDB commands in handler), `src/basket/index.js`, `src/ordering/index.js` |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | All databases are DynamoDB — a fully managed serverless database with no engine version to pin or manage. DynamoDB is continuously updated by AWS with no EOL concerns, no maintenance windows, and no version-specific security patches. No RDS, Aurora, or other versioned database engines exist in the repository. |
| **Gap** | No gaps — DynamoDB eliminates engine version management entirely. |
| **Recommendation** | No action needed. DynamoDB's managed lifecycle eliminates version management concerns. |
| **Evidence** | `lib/database.ts` (3 DynamoDB tables, no versioned database engines) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs. All business logic resides in the Lambda application layer (JavaScript). DynamoDB is a NoSQL database with no SQL constructs. No `.sql` migration files, no ORM configurations. The checkout business logic (total price calculation, order payload preparation) is entirely in `src/basket/index.js`. |
| **Gap** | No gaps — all business logic is in the application layer with no database coupling. |
| **Recommendation** | Maintain the current pattern of keeping business logic in the application layer. This is a strength of the architecture — it enables database technology changes without business logic migration. |
| **Evidence** | `src/basket/index.js` (`prepareOrderPayload` — business logic in Lambda), `src/product/index.js`, `src/ordering/index.js` — no SQL files, no stored procedures |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail configuration in CDK. No audit logging resources defined. Lambda functions write to CloudWatch Logs by default (implicit), but no explicit CloudTrail trail, no log file validation, no immutable storage. No centralized logging configuration. |
| **Gap** | No audit trail for API calls, DynamoDB data access, or EventBridge event publishing. For a P0 e-commerce platform processing user data and orders, audit logging is a compliance requirement. Without CloudTrail, there is no forensic capability after security incidents. |
| **Recommendation** | Add CloudTrail trail in CDK with log file validation enabled and S3 bucket with Object Lock for immutable storage. Enable CloudTrail data events for DynamoDB and Lambda for granular data access auditing. Add CloudWatch log retention policies for Lambda function logs. |
| **Evidence** | `lib/aws-microservices-stack.ts` (no CloudTrail construct), all CDK files (no logging configuration) |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | DynamoDB tables use AWS-managed encryption at rest by default (AWS-owned keys). All three tables (`product`, `basket`, `order`) are encrypted without explicit configuration. SQS `OrderQueue` uses default encryption. No customer-managed KMS keys are defined. No explicit encryption configuration in any CDK construct. |
| **Gap** | No customer-managed KMS keys. AWS-managed encryption is functional but provides less control over key rotation policies, access audit trails, and cross-account key sharing. For a P0 e-commerce platform handling payment info (`cardInfo` field in order table), customer-managed keys provide stronger compliance posture. |
| **Recommendation** | Create customer-managed KMS keys for DynamoDB tables storing sensitive data (especially the `order` table which contains `email`, `address`, `paymentMethod`, `cardInfo`). Configure automatic key rotation. Apply KMS keys to SQS queue for encrypted message storage. |
| **Evidence** | `lib/database.ts` (no `encryption` or `encryptionKey` properties on DynamoDB tables), `lib/queue.ts` (no encryption config on SQS queue) |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No authentication configured on any API Gateway endpoint. No authorizers (Cognito, Lambda, IAM), no API keys, no OAuth2/JWT validation. All 14 API endpoints across the three services are publicly accessible without any authentication. The `lib/apigateway.ts` creates `LambdaRestApi` instances with resource-based routing but no authorization configuration. |
| **Gap** | All API endpoints are completely open. Anyone can create products (`POST /product`), delete baskets (`DELETE /basket/{userName}`), trigger checkouts (`POST /basket/checkout`), and query all orders (`GET /order`). This is a critical security vulnerability for a P0 e-commerce platform. User data (names, emails, payment information) is accessible without authentication. |
| **Recommendation** | Add Cognito User Pool authorizers to all API Gateway endpoints for customer-facing authentication. Use IAM authorization for service-to-service calls (e.g., agent-to-API communication). For the Bedrock agent integration, use IAM-based authorization with the agent's execution role. This is the highest-priority security action alongside backup and recovery. |
| **Evidence** | `lib/apigateway.ts` (no `defaultMethodOptions`, no authorizers, no API keys on any of the 3 API Gateways) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No identity provider integration. No Cognito User Pool, no Okta, no SAML, no OIDC configuration. The application has no authentication system at all — APIs are fully open. No user identity management exists; `userName` in the basket and order tables is passed as a request parameter without verification. |
| **Gap** | No centralized identity. The `userName` field used across basket and ordering services is user-supplied with no verification — any caller can impersonate any user by passing their `userName`. No SSO, no federated identity, no multi-factor authentication. |
| **Recommendation** | Implement Amazon Cognito as the centralized identity provider. Create a Cognito User Pool with appropriate password policies and optional MFA. Add Cognito authorizers to API Gateway. Extract `userName` from the authenticated JWT token instead of accepting it as a request parameter. This prevents user impersonation and enables proper identity-based access control. |
| **Evidence** | `lib/apigateway.ts` (no Cognito integration), `src/basket/index.js` (`checkoutRequest.userName` from request body), `src/ordering/index.js` (`event.pathParameters.userName` from URL) |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | No Secrets Manager or Vault usage. However, the current architecture has minimal secret surface: Lambda functions access DynamoDB, EventBridge, and SQS via IAM roles managed by CDK grants (`grantReadWriteData`, `grantPutEventsTo`). Environment variables contain non-secret configuration (table names, event bus name, event source/detail type). No database passwords, no API keys to external services, no hardcoded credentials found in code. |
| **Gap** | While the current architecture has no application-level secrets (IAM roles handle all service-to-service auth), there is no Secrets Manager integration for future needs. As the platform grows (external payment gateway keys, third-party API credentials), secrets management infrastructure will be needed. No rotation capability exists. |
| **Recommendation** | Maintain IAM role-based authentication for AWS service access. When external service credentials are needed (payment gateways, shipping APIs), use AWS Secrets Manager with automatic rotation. Do not store credentials in environment variables or code. |
| **Evidence** | `lib/microservice.ts` (environment variables: `DYNAMODB_TABLE_NAME`, `EVENT_BUSNAME` — non-secret), `lib/database.ts` (`grantReadWriteData` — IAM-based access), `lib/eventbus.ts` (`grantPutEventsTo` — IAM-based access) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Lambda functions use `Runtime.NODEJS_14_X`, which reached end of standard support on November 27, 2023. Lambda manages runtime patching within a major version, but NODEJS_14_X no longer receives security updates. No vulnerability scanning tools configured (no AWS Inspector, no Snyk, no Dependabot). Lambda uses managed runtime (no custom AMIs, no EC2 instances to patch). |
| **Gap** | Using a deprecated Lambda runtime (`NODEJS_14_X`) that no longer receives security patches. No dependency vulnerability scanning — the `@aws-sdk` packages at `^3.55.0` / `^3.58.0` are significantly outdated (current is 3.500+). No container scanning (N/A — no containers). |
| **Recommendation** | Upgrade Lambda runtime from `NODEJS_14_X` to `NODEJS_20_X` or `NODEJS_22_X`. Update `@aws-sdk` dependencies to latest v3 versions. Add Dependabot or Snyk for automated dependency vulnerability scanning. This is a prerequisite for the CI/CD pipeline — add `npm audit` as a pipeline gate. |
| **Evidence** | `lib/microservice.ts` (`Runtime.NODEJS_14_X` on all 3 functions), `src/product/package.json` (`@aws-sdk/client-dynamodb: ^3.55.0`), `src/basket/package.json`, `src/ordering/package.json` |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No security scanning tools configured. No SAST tools (no SonarQube, Semgrep, CodeGuru). No dependency scanning (no Dependabot, no Snyk, no `npm audit` in any script). No container scanning (N/A). No CI/CD pipeline exists to integrate security scanning into. No `.snyk` policy file, no `.github/dependabot.yml`. |
| **Gap** | Complete absence of automated security validation. Dependency vulnerabilities in `@aws-sdk` packages and other dependencies are not detected. Code-level vulnerabilities (injection, XSS in API responses) are not scanned. No security gates in the build process (no build process exists). |
| **Recommendation** | When creating the CI/CD pipeline (INF-Q11): (1) Add `npm audit` as a pipeline step with fail-on-critical, (2) Add Dependabot (`.github/dependabot.yml`) for automated dependency updates, (3) Add a SAST tool (Amazon CodeGuru Reviewer or Semgrep) for code scanning, (4) Add `cdk-nag` for CDK-specific security and best-practice checks. |
| **Evidence** | Repository root — no `.github/dependabot.yml`, no `.snyk`, no security config files. No CI/CD pipeline to integrate scanning into. |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing instrumentation. No X-Ray SDK, no OpenTelemetry SDK in any dependency manifest. No `traceparent` or `X-Amzn-Trace-Id` header propagation. Lambda functions use only `console.log` and `console.error` for logging. The checkout flow crosses three service boundaries (basket → EventBridge → SQS → ordering) with no trace correlation. |
| **Gap** | No ability to trace a checkout request from basket through EventBridge/SQS to ordering. Debugging cross-service issues requires manual log correlation. For AI agent integration, agent action tracing through the microservices is impossible without distributed tracing infrastructure. |
| **Recommendation** | Enable AWS X-Ray tracing on all Lambda functions (set `tracing: Tracing.ACTIVE` in CDK). X-Ray integrates natively with Lambda, API Gateway, DynamoDB, SQS, and EventBridge. Add the X-Ray SDK to Lambda function dependencies for custom subsegments. For the agent use case, X-Ray traces provide end-to-end visibility of agent-initiated API calls. |
| **Evidence** | `src/product/package.json`, `src/basket/package.json`, `src/ordering/package.json` (no X-Ray or OpenTelemetry dependencies), `lib/microservice.ts` (no `tracing` property on Lambda functions) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions found. No CloudWatch alarms for latency percentiles (p50, p95, p99), error rates, or availability targets. No error budget tracking. No formal definition of acceptable service levels for any of the three microservices. |
| **Gap** | No measurable service level targets. Cannot determine if the e-commerce platform is meeting user expectations or degrading. No data to prioritize modernization investments. For agent integration, SLOs on API response times are critical — agent tools must respond within acceptable latency bounds. |
| **Recommendation** | Define SLOs for each microservice: (1) Product API: p99 latency < 200ms, availability > 99.9%, (2) Basket API: p99 latency < 300ms, availability > 99.9%, (3) Order API: p99 latency < 500ms, availability > 99.95%. Create CloudWatch alarms for each SLO. Track error budgets. Use Lambda Insights for detailed function-level metrics. |
| **Evidence** | All CDK files — no CloudWatch alarm constructs, no SLO definitions |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metrics published. No `PutMetricData` calls in any Lambda function. Only default Lambda metrics (invocations, errors, duration, throttles) are available — provided automatically by AWS, not configured by the application. No business outcome tracking: no checkout conversion rates, no order success rates, no product catalog metrics. |
| **Gap** | Cannot measure business outcomes. No way to answer: "How many checkouts succeeded today?", "What is the average order value?", "Which products are most viewed?" Infrastructure metrics alone don't indicate business health. |
| **Recommendation** | Add CloudWatch custom metrics via the Embedded Metrics Format (EMF) in Lambda functions: (1) Checkout success/failure count, (2) Average order value (from `totalPrice`), (3) Products created/updated per day, (4) Basket abandonment rate. EMF enables zero-cost metric publishing from Lambda without additional SDK dependencies. |
| **Evidence** | `src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js` — no `PutMetricData` or EMF calls, only `console.log` |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No alerting configured. No CloudWatch alarms (static or anomaly detection). No PagerDuty, OpsGenie, or SNS topic for alert notifications. No composite alarms. The application operates with no automated failure detection. |
| **Gap** | Complete absence of alerting. Lambda errors, DynamoDB throttling, SQS message age, and API Gateway 5xx responses go unnoticed until users report issues. For a P0 e-commerce platform, this means data loss or service degradation can persist indefinitely without detection. |
| **Recommendation** | Add CloudWatch alarms in CDK: (1) Lambda error count > 0, (2) Lambda throttle count > 0, (3) DynamoDB `UserErrors` > 0, (4) SQS `ApproximateAgeOfOldestMessage` > 60s, (5) API Gateway 5xx count > threshold. Add SNS topic for alert delivery. Consider CloudWatch Anomaly Detection on Lambda duration metrics for gradual degradation detection. |
| **Evidence** | All CDK files — no CloudWatch alarm constructs, no SNS topics for alerts |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No deployment strategy defined. No CI/CD pipeline exists. The only deployment method is manual `cdk deploy` from a developer workstation, which deploys all three services simultaneously with no staged rollout. No Lambda alias configuration, no CodeDeploy integration, no traffic shifting, no canary analysis, no feature flags. |
| **Gap** | Every deployment goes directly to production affecting all users immediately. No ability to detect regressions before full rollout. No automated rollback capability. Combined with the absence of monitoring (OPS-Q4 = 1), a bad deployment persists until manual detection and manual rollback. |
| **Recommendation** | Implement Lambda alias traffic shifting with CodeDeploy: (1) Configure Lambda function aliases (`prod`), (2) Use `LambdaCanary10Percent5Minutes` or `LambdaLinear10PercentEvery1Minute` deployment configurations, (3) Add CloudWatch alarms as automatic rollback triggers. This is dependent on first creating a CI/CD pipeline (INF-Q11). |
| **Evidence** | `README.md` (deployment: "run `cdk deploy`"), `lib/microservice.ts` (no alias/version config on Lambda functions), no CI/CD config files |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The test file `test/aws-microservices.test.ts` exists but is entirely commented out — the test body is empty (`test('SQS Queue Created', () => { })`). Jest is configured (`jest.config.js` with `ts-jest` transform), but no runnable tests exist. No unit tests for Lambda handlers, no integration tests for API endpoints, no contract tests for EventBridge events. |
| **Gap** | Zero automated test coverage. Any code change is deployed without validation. No regression detection. The commented-out test suggests testing was intended but never implemented. No EventBridge event schema validation — the checkout event contract between basket and ordering is implicit, not tested. |
| **Recommendation** | (1) Implement CDK infrastructure tests (`Template.fromStack` assertions for resource types and properties), (2) Add unit tests for each Lambda handler with mocked DynamoDB and EventBridge clients, (3) Add integration tests using API Gateway test invocations, (4) Add contract tests for the EventBridge `CheckoutBasket` event schema using the `checkoutbasketevents.json` as the baseline. |
| **Evidence** | `test/aws-microservices.test.ts` (all test code commented out), `jest.config.js` (Jest configured but no tests to run) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, no SSM Automation documents, no Lambda-based remediation, no incident response automation of any kind. No documented procedures for common incidents (checkout failures, DynamoDB throttling, Lambda cold start spikes). No self-healing patterns. |
| **Gap** | All incident response is ad hoc and manual. Given the absence of monitoring (OPS-Q4 = 1), incidents are not even detected automatically — response begins only when users report problems. No documented escalation paths, no on-call procedures. |
| **Recommendation** | Create runbooks (markdown or SSM documents) for common incidents: (1) checkout pipeline failure (SQS message stuck), (2) DynamoDB throttling, (3) Lambda error spike, (4) API Gateway 5xx surge. Add self-healing Lambda functions for common issues (e.g., retry failed SQS messages from DLQ). Integrate with incident management tooling (PagerDuty, OpsGenie). |
| **Evidence** | Repository root — no `runbooks/` directory, no SSM documents, no incident response automation |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No per-service dashboards, no alarms with named owners, no CODEOWNERS file, no team attribution on any observability asset. No observability configuration exists at all — there is nothing to own. |
| **Gap** | No observability ownership because no observability exists. When monitoring is added, there is no framework for assigning ownership — who is on-call, who maintains dashboards, who reviews alerts. |
| **Recommendation** | When adding observability infrastructure: (1) Create per-service CloudWatch dashboards (product, basket, ordering), (2) Add a CODEOWNERS file mapping CDK files and observability configs to team members, (3) Tag CloudWatch alarms and dashboards with team/service ownership tags, (4) Define on-call rotation and escalation paths. |
| **Evidence** | Repository root — no CODEOWNERS file, no dashboard definitions, no alarm configurations |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No resource tags on any CDK construct. No `Tags.of()` calls, no default tags, no tag enforcement. DynamoDB tables, Lambda functions, API Gateways, EventBridge bus, and SQS queue are all deployed without tags. No tagging standard documented. |
| **Gap** | No cost allocation by service. No ownership identification on resources. No environment tagging (dev/staging/prod). Cannot track costs for product vs basket vs ordering services. No tag-based access policies or automation triggers. |
| **Recommendation** | Add a tagging strategy in CDK using `Tags.of(this).add()` at the stack level with minimum tags: `Environment` (dev/staging/prod), `Service` (product/basket/ordering), `Team`, `CostCenter`, `Project` (aws-microservices). Apply tags at the stack level for automatic propagation to all resources. Enforce tagging with AWS Config rules or AWS Organizations Tag Policies. |
| **Evidence** | `lib/aws-microservices-stack.ts` (no `Tags.of()` calls), `lib/database.ts`, `lib/microservice.ts`, `lib/queue.ts`, `lib/eventbus.ts` — no tags on any construct |

## Learning Materials

Learning resources for triggered pathways:

### Move to Modern DevOps

- [Move to Modern DevOps — AWS SkillBuilder Learning Plan](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS — AWS SkillBuilder](https://skillbuilder.aws/learn/R4B13K95YQ)
- [AWS CDK Pipelines Documentation](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.pipelines-readme.html)
- [AWS Lambda Deployment with CodeDeploy](https://docs.aws.amazon.com/lambda/latest/dg/lambda-rolling-deployments.html)

### Move to AI

- [Move to AI — AWS SkillBuilder Learning Plan](https://skillbuilder.aws/learning-plan/VDFEE4ACCV)
- [Amazon Bedrock Getting Started — AWS SkillBuilder](https://skillbuilder.aws/learn/63KTRM86DQ)
- [Introduction to Agentic AI on AWS — AWS SkillBuilder](https://skillbuilder.aws/learn/DNBD5MT8ZD)
- [Amazon Bedrock Agents Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `lib/aws-microservices-stack.ts` | INF-Q5, INF-Q10, SEC-Q1, OPS-Q9 | Main CDK stack wiring all constructs; no VPC, no CloudTrail, no tags |
| `lib/apigateway.ts` | INF-Q5, INF-Q6, INF-Q7, APP-Q5, SEC-Q3, SEC-Q4 | 3 LambdaRestApi instances with no auth, throttling, or validation |
| `lib/database.ts` | INF-Q2, INF-Q7, INF-Q8, INF-Q9, DATA-Q1, DATA-Q3, SEC-Q2, OPS-Q9 | 3 DynamoDB tables with PAY_PER_REQUEST, RemovalPolicy.DESTROY, no PITR |
| `lib/eventbus.ts` | INF-Q3, INF-Q4, INF-Q9, APP-Q3, APP-Q6, OPS-Q9 | EventBridge SwnEventBus with CheckoutBasketRule routing to SQS |
| `lib/microservice.ts` | INF-Q1, INF-Q7, APP-Q6, SEC-Q5, SEC-Q6, OPS-Q1, OPS-Q5, OPS-Q9 | 3 Lambda functions with NODEJS_14_X, env vars, no tracing, no concurrency |
| `lib/queue.ts` | INF-Q3, INF-Q4, INF-Q9, SEC-Q2, OPS-Q9 | SQS OrderQueue with 30s visibility timeout, no DLQ |
| `bin/aws-microservices.ts` | INF-Q10 | CDK app entry point |
| `src/product/index.js` | APP-Q1, APP-Q2, DATA-Q1, DATA-Q2, DATA-Q4, OPS-Q3 | Product CRUD Lambda handler with raw DynamoDB commands |
| `src/product/ddbClient.js` | DATA-Q2 | Product DynamoDB client module |
| `src/product/package.json` | APP-Q1, SEC-Q6, OPS-Q1 | @aws-sdk/client-dynamodb ^3.55.0 |
| `src/basket/index.js` | INF-Q3, INF-Q4, APP-Q2, APP-Q3, APP-Q4, DATA-Q4, SEC-Q4, OPS-Q3 | Basket CRUD + checkout with EventBridge publish |
| `src/basket/ddbClient.js` | DATA-Q2 | Basket DynamoDB client module |
| `src/basket/eventBridgeClient.js` | INF-Q4, APP-Q3 | EventBridge client for checkout event publishing |
| `src/basket/package.json` | APP-Q1, SEC-Q6, OPS-Q1 | @aws-sdk/client-dynamodb, @aws-sdk/client-eventbridge |
| `src/basket/checkoutbasketevents.json` | OPS-Q6 | Sample EventBridge checkout event payload |
| `src/ordering/index.js` | INF-Q4, APP-Q2, APP-Q3, APP-Q4, DATA-Q2, OPS-Q3 | Ordering Lambda: SQS consumer + API Gateway GET |
| `src/ordering/ddbClient.js` | DATA-Q2 | Ordering DynamoDB client module |
| `src/ordering/package.json` | APP-Q1, SEC-Q6, OPS-Q1 | @aws-sdk/client-dynamodb ^3.58.0 |
| `package.json` | APP-Q1, INF-Q11 | Root package: CDK 2.17.0, TypeScript ~3.9.7, no deploy scripts |
| `cdk.json` | INF-Q10 | CDK configuration and feature flags |
| `tsconfig.json` | APP-Q1 | TypeScript compiler configuration |
| `jest.config.js` | OPS-Q6 | Jest test configuration (no runnable tests) |
| `test/aws-microservices.test.ts` | OPS-Q6 | Test file with all code commented out |
| `README.md` | INF-Q11, OPS-Q5 | Deployment instructions ("run cdk deploy"), architecture description |
