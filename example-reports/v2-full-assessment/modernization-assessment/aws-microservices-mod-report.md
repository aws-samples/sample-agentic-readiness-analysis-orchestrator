# Modernization Readiness Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | aws-microservices |
| **Date** | 2026-04-15 |
| **Repo Type** | application |
| **Priority** | P0 |
| **Tags** | microservices, serverless, event-driven |
| **Context** | Event-driven serverless microservices (product, basket, ordering) with Lambda, DynamoDB, EventBridge, SQS. The agent will invoke these as tools for order status lookups and return processing. |
| **Overall Score** | **2.24 / 4.0** |

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 2.64 / 4.0 | 🟡 Partial |
| Application Architecture (APP) | 3.00 / 4.0 | 🟡 Partial |
| Data Platform Modernization (DATA) | 3.00 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 1.57 / 4.0 | 🟠 Needs Work |
| Operations & Observability (OPS) | 1.00 / 4.0 | ❌ Not Present |
| **Overall** | **2.24 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q11: CI/CD Automation | 1 | No CI/CD pipeline exists — all deployments are manual `cdk deploy` | Triggers Move to Modern DevOps pathway. Manual deployments are error-prone, slow, and prevent safe iterative modernization of this P0 service. |
| 2 | SEC-Q3: API Authentication | 1 | All three API Gateway endpoints (Product, Basket, Order) are completely open with no authentication | Critical security vulnerability — any internet-facing endpoint can be invoked without authorization. Blocks production readiness and agent integration. |
| 3 | OPS-Q5: Deployment Strategy | 1 | No canary, blue/green, or staged deployment strategy — direct-to-production via `cdk deploy` | No safety net for regressions. A bad deployment affects all users instantly with no rollback mechanism. |
| 4 | INF-Q8: Backup and Recovery | 1 | No DynamoDB point-in-time recovery (PITR) enabled; `removalPolicy: DESTROY` on all tables — data is deleted on stack deletion | Data loss risk — a stack deletion or corruption event destroys all product, basket, and order data with no recovery path. |
| 5 | SEC-Q1: Audit Logging | 1 | No CloudTrail or structured audit logging configured in CDK | No ability to trace API calls, detect unauthorized access, or perform forensic analysis. Compliance gap. |

---

## Quick Agent Wins

### Data Query Agent

- **Prerequisite:** Database with clear, documented schema (DATA-Q2 = 3). Each microservice has a dedicated `ddbClient.js` module with consistent DynamoDB access patterns via `@aws-sdk/client-dynamodb`. Three well-defined DynamoDB tables: `product` (PK: id), `basket` (PK: userName), `order` (PK: userName, SK: orderDate).
- **What it enables:** An AI agent (powered by Amazon Bedrock) can query DynamoDB tables as tools for order status lookups, product catalog searches, and basket content retrieval. The existing `getOrder`, `getProduct`, `getBasket` functions provide natural tool interfaces that an agent can invoke.
- **Additional steps:** Generate data schema documentation describing each table's key schema, attributes, and access patterns. Create OpenAPI specifications for the existing API Gateway endpoints to enable full agent tool discovery. Add API Gateway authentication before exposing to agent workloads.
- **Effort:** Medium

### RAG-based Knowledge Agent

- **Prerequisite:** Documentation exists in repository. `README.md` contains architecture description, API endpoint documentation (Product, Basket, Order URLs), prerequisite instructions, and useful CDK commands. Code comments in `lib/apigateway.ts` and `lib/database.ts` document API routes and DynamoDB schemas.
- **What it enables:** A RAG-based knowledge agent (using Amazon Bedrock with knowledge bases) can index the README, code comments, and inline documentation to answer developer questions about the architecture, API endpoints, deployment procedures, and data models.
- **Additional steps:** Enrich documentation — the current README is minimal. Add architecture decision records (ADRs), API documentation with request/response examples, and operational runbooks. Store enriched documentation in S3 for Bedrock Knowledge Base indexing.
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 4 — application is already decomposed into independently deployable serverless microservices with event-driven communication. |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1 = 4 — compute is already 100% serverless (Lambda). Contextual guard: compute is Lambda/Fargate-class, not EC2/VM-based. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 — no stored procedures or proprietary SQL. No commercial database engines detected (DynamoDB is AWS-native NoSQL). |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 = 4 — all databases are fully managed DynamoDB with PAY_PER_REQUEST billing. |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 = 3 — messaging is already managed (EventBridge + SQS). No data processing workloads detected (no ETL, data pipelines, or analytics). |
| 6 | Move to Modern DevOps | **Triggered** | High | Medium | INF-Q11 = 1 (no CI/CD pipeline). Supporting: OPS-Q5 = 1 (no deployment strategy), OPS-Q6 = 1 (no integration testing). |
| 7 | Move to AI | **Triggered** | Medium | Medium | No AI/agent framework usage detected in source code or dependencies. No vector DB, no RAG, no agent eval framework. |

---

### Pathway: Move to Modern DevOps

**Status:** Triggered  
**Priority:** High  
**Estimated Effort:** Medium

#### Current State

- **IaC Coverage (INF-Q10 = 4):** All infrastructure is defined in AWS CDK (TypeScript) across 6 construct files: `lib/aws-microservices-stack.ts`, `lib/database.ts`, `lib/microservice.ts`, `lib/apigateway.ts`, `lib/eventbus.ts`, `lib/queue.ts`. IaC is a strength — 100% of provisioned resources are in code.
- **CI/CD State (INF-Q11 = 1):** No CI/CD pipeline exists anywhere in the repository. No `.github/workflows/`, no `buildspec.yml`, no `Jenkinsfile`, no `CodePipeline` definition in CDK. All deployments are performed manually via `cdk deploy` from a developer workstation.
- **Deployment Strategy (OPS-Q5 = 1):** `cdk deploy` performs a direct CloudFormation stack update with no staged rollout, no canary analysis, and no automated rollback. Lambda function updates are deployed to all traffic immediately.
- **Integration Testing (OPS-Q6 = 1):** The test file `test/aws-microservices.test.ts` exists but is entirely commented out. Jest configuration is present (`jest.config.js`) but no runnable tests exist. No API tests, no contract tests, no end-to-end tests.

#### Recommendations

Given the preferences for **Terraform** and **GitOps**, and the preference to **avoid manual deployments**:

1. **Implement CI/CD Pipeline with GitOps:**
   - Create a GitHub Actions workflow (or AWS CodePipeline) that triggers on pull request merges to the main branch.
   - Pipeline stages: lint → unit test → `cdk synth` → `cdk diff` (plan review) → `cdk deploy` to staging → integration test → `cdk deploy` to production.
   - Consider migrating from CDK to **Terraform** (preferred) for infrastructure definition to align with organizational preferences and enable Terraform-native GitOps tooling.
   - Adopt a GitOps model where infrastructure changes flow through pull requests with automated plan previews.

2. **Add Deployment Safety:**
   - Configure Lambda function aliases with **AWS CodeDeploy** traffic shifting (canary or linear deployment) to enable gradual rollouts with automatic rollback on CloudWatch alarm triggers.
   - Use API Gateway stage variables to route traffic between canary and production Lambda versions.

3. **Establish Testing Foundation:**
   - Uncomment and extend the existing CDK test in `test/aws-microservices.test.ts` to validate CloudFormation template correctness.
   - Add integration tests that invoke API Gateway endpoints with test data and validate responses.
   - Add contract tests for the EventBridge event schema (`com.swn.basket.checkoutbasket` / `CheckoutBasket`).

4. **Add Security Scanning to Pipeline:**
   - Integrate `npm audit` for dependency vulnerability scanning.
   - Add Dependabot or Snyk for automated dependency updates.
   - Integrate SAST tooling (e.g., Semgrep, Amazon CodeGuru Reviewer) for code quality and security analysis.

#### Representative AWS Services
- AWS CodePipeline, AWS CodeBuild, AWS CodeDeploy
- GitHub Actions (alternative)
- AWS CloudFormation / Terraform (IaC)
- Amazon CloudWatch (deployment alarms for canary rollbacks)

#### Learning Resources
- [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)

---

### Pathway: Move to AI

**Status:** Triggered  
**Priority:** Medium  
**Estimated Effort:** Medium

#### Current AI/Agent Infrastructure State

No AI or agent infrastructure exists in the repository:
- **AI/Agent Frameworks:** No Bedrock SDK, LangChain, Strands, OpenAI, or SageMaker SDK imports detected in any source file or dependency manifest.
- **Vector Database:** No OpenSearch, Pinecone, pgvector, Weaviate, or Qdrant infrastructure or client libraries.
- **RAG Implementation:** No embedding generation, vector store queries, or retrieval chain patterns.
- **Agent Evaluation:** No Ragas, DeepEval, or custom evaluation harness.

#### Application Domain and AI Opportunities

The e-commerce domain (product catalog, shopping basket, order management) offers strong AI integration opportunities, particularly given the stated context that "the agent will invoke these as tools for order status lookups and return processing":

1. **Agent Tool Integration (Highest Priority):**
   - The existing API Gateway endpoints (`/product`, `/basket`, `/order`) are natural tool interfaces for an AI agent.
   - An **Amazon Bedrock Agent** can invoke these endpoints as tools for conversational order status lookups, product search, and basket management.
   - **Prerequisite:** Add API Gateway authentication (SEC-Q3 gap) before exposing endpoints as agent tools. Generate OpenAPI specifications for tool discovery.

2. **Customer Service Agent:**
   - Build a Bedrock-powered agent that handles order status inquiries, product recommendations, and return processing via the existing microservices.
   - Use EventBridge to publish agent action events (e.g., `com.swn.agent.returnrequest`) that flow through the existing event-driven architecture.

3. **Product Recommendation Engine:**
   - Use Amazon Bedrock foundation models to generate product recommendations based on basket contents and order history.
   - DynamoDB's basket and order tables provide the data foundation.

4. **RAG Knowledge Base:**
   - Index product catalog data and order policies into an Amazon Bedrock Knowledge Base for retrieval-augmented generation.
   - Enable natural language queries against product and order data.

#### Foundation Requirements Before AI Integration

Before adding AI capabilities, address these foundational gaps:
- **API Authentication (SEC-Q3):** Agent tool invocation requires authenticated endpoints.
- **API Specifications (APP-Q5):** Generate OpenAPI specs for agent tool discovery and schema validation.
- **Observability (OPS-Q1):** Add distributed tracing (X-Ray) to track agent-initiated request flows across microservices.
- **CI/CD Pipeline (INF-Q11):** Automated deployment is needed to safely iterate on AI features.

#### Representative AWS Services
- Amazon Bedrock (foundation models, agents, knowledge bases)
- Amazon Bedrock AgentCore (agent runtime and tool orchestration)
- Amazon Q (developer productivity)
- Amazon OpenSearch Service (vector engine for RAG)
- Amazon S3 (knowledge base document storage)

#### Learning Resources
- [Move to AI](https://skillbuilder.aws/learning-plan/VDFEE4ACCV)
- [Amazon Bedrock Getting Started](https://skillbuilder.aws/learn/63KTRM86DQ)
- [Introduction to Agentic AI on AWS](https://skillbuilder.aws/learn/DNBD5MT8ZD)

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | 100% of compute workloads use AWS Lambda (serverless). Three `NodejsFunction` Lambda functions are defined in `lib/microservice.ts`: `productLambdaFunction`, `basketLambdaFunction`, `orderingLambdaFunction`. All use `Runtime.NODEJS_14_X`. No EC2 instances, no ECS tasks, no EKS pods. The application is fully serverless. |
| **Gap** | The Lambda runtime `NODEJS_14_X` is past end-of-life (EOL April 2023). While compute is fully managed, the runtime version is a significant technical debt item. |
| **Recommendation** | Upgrade Lambda runtime from `NODEJS_14_X` to `NODEJS_20_X` or `NODEJS_22_X` in `lib/microservice.ts`. Update the `aws-sdk` external module bundling configuration since newer runtimes use AWS SDK v3 natively. |
| **Evidence** | `lib/microservice.ts` — `runtime: Runtime.NODEJS_14_X` on lines for all three Lambda functions. |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | All three databases are fully managed DynamoDB tables defined in `lib/database.ts`: `product` (PK: id), `basket` (PK: userName), `order` (PK: userName, SK: orderDate). All use `BillingMode.PAY_PER_REQUEST` (on-demand, auto-scaling). No self-managed databases. |
| **Gap** | No gaps for managed database criterion. DynamoDB is fully managed with automated failover across AZs. |
| **Recommendation** | Consider enabling DynamoDB global tables for multi-region resilience if the workload expands internationally. Current single-region setup is appropriate for the current scale. |
| **Evidence** | `lib/database.ts` — `new Table(this, 'product', {...})`, `new Table(this, 'basket', {...})`, `new Table(this, 'order', {...})` all with `billingMode: BillingMode.PAY_PER_REQUEST`. |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No dedicated workflow orchestration service is used. The checkout flow is an event chain: basket Lambda → EventBridge (`SwnEventBus`) → SQS (`OrderQueue`) → ordering Lambda. This is event-driven choreography, not orchestration. No Step Functions, Temporal, Camunda, or other workflow service detected. |
| **Gap** | The checkout workflow (basket checkout → order creation) has no centralized state management, error handling with compensation, or retry orchestration. If the ordering Lambda fails to process an SQS message after retries, there is no dead-letter queue configured and no compensating action (e.g., restoring the deleted basket). |
| **Recommendation** | Implement AWS Step Functions to orchestrate the checkout workflow: (1) validate basket, (2) calculate total, (3) publish event, (4) create order, (5) delete basket. Step Functions provides built-in retry, error handling, compensation, and visual workflow monitoring. Use EventBridge for inter-service events but Step Functions for multi-step business workflows. |
| **Evidence** | `lib/eventbus.ts` — EventBridge rule `CheckoutBasketRule` routes to SQS. `lib/queue.ts` — `OrderQueue` with `visibilityTimeout: 30s` but no dead-letter queue. `src/basket/index.js` — `checkoutBasket()` deletes basket after publishing event (no compensation on failure). |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Managed messaging infrastructure is in use: EventBridge (`SwnEventBus`) for event publishing and SQS (`OrderQueue`) for message queuing, both defined in CDK. The checkout flow is fully asynchronous: basket Lambda publishes `CheckoutBasket` event → EventBridge rule → SQS queue → ordering Lambda. However, API Gateway calls to all three Lambda functions are synchronous HTTP request/response. |
| **Gap** | Messaging is managed but limited to one flow (checkout). Product CRUD and basket CRUD operations are entirely synchronous. No streaming infrastructure (Kinesis, MSK) for real-time data flows. |
| **Recommendation** | The current mix of sync API calls and async checkout flow is appropriate for this e-commerce pattern. Consider adding EventBridge events for product catalog changes and basket updates to enable downstream consumers (analytics, recommendations, audit). |
| **Evidence** | `lib/eventbus.ts` — `new EventBus(this, 'SwnEventBus')`, `new Rule(this, 'CheckoutBasketRule')`. `lib/queue.ts` — `new Queue(this, 'OrderQueue')`. `src/basket/index.js` — `publishCheckoutBasketEvent()` uses `PutEventsCommand`. |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC configuration found in any CDK construct. Lambda functions are deployed without VPC attachment — they run in the AWS Lambda service VPC with internet access by default. DynamoDB is accessed via public endpoints (no VPC endpoint). API Gateway has no WAF, no IP restrictions, no resource policies. No security groups, no private subnets, no network segmentation defined. |
| **Gap** | All services operate on public AWS endpoints with no network-level access controls. While Lambda-to-DynamoDB communication uses IAM for authorization, there is no defense-in-depth at the network layer. API Gateway endpoints are internet-facing with no WAF protection. |
| **Recommendation** | Add a WAF WebACL to the API Gateway endpoints to protect against common web exploits (SQL injection, XSS, rate limiting). For defense-in-depth, consider configuring Lambda functions within a VPC with VPC endpoints for DynamoDB and EventBridge to eliminate internet traversal for internal service communication. Add API Gateway resource policies to restrict access to known IP ranges or VPC endpoints. |
| **Evidence** | `lib/microservice.ts` — No `vpc` property on `NodejsFunctionProps`. `lib/apigateway.ts` — No WAF, no resource policy on `LambdaRestApi`. `lib/aws-microservices-stack.ts` — No `Vpc` construct imported or instantiated. |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Three separate `LambdaRestApi` gateways are defined in `lib/apigateway.ts`: "Product Service", "Basket Service", "Order Service". API Gateway serves as the HTTP entry point with defined routes (`/product`, `/product/{id}`, `/basket`, `/basket/{userName}`, `/basket/checkout`, `/order`, `/order/{userName}`). However, configuration is minimal — no throttling, no authentication, no request validation, no usage plans. |
| **Gap** | API Gateway is present but under-configured. No throttling to prevent abuse, no request body validation to reject malformed input, no authentication to restrict access. Three separate API Gateways instead of a consolidated entry point create management overhead. |
| **Recommendation** | Consolidate into a single API Gateway (preferred) with resource-based routing, or keep per-service gateways with shared configuration. Add throttling limits, request validators (JSON schema), and usage plans. Consider migrating to HTTP API (API Gateway v2) for lower latency and cost if REST API features are not needed. |
| **Evidence** | `lib/apigateway.ts` — `new LambdaRestApi(this, 'productApi', { restApiName: 'Product Service', handler: productMicroservice, proxy: false })` and similar for basket and order. No `requestValidator`, no `apiKey`, no `usagePlan`, no `throttle` properties. |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | All compute and data tiers auto-scale inherently via serverless managed services. Lambda functions auto-scale concurrency based on incoming requests (default account concurrency limit). DynamoDB uses `BillingMode.PAY_PER_REQUEST` (on-demand), which auto-scales read/write capacity to match traffic. SQS auto-scales message processing via Lambda event source mapping. No manual capacity provisioning is required. |
| **Gap** | No explicit Lambda reserved concurrency or provisioned concurrency configured — functions rely on default account-level limits. No DynamoDB auto-scaling alarms for capacity monitoring. |
| **Recommendation** | Consider setting Lambda reserved concurrency limits to prevent one service from starving others during traffic spikes. Add CloudWatch alarms on Lambda concurrent executions and DynamoDB consumed capacity for visibility. |
| **Evidence** | `lib/microservice.ts` — `NodejsFunction` with no `reservedConcurrentExecutions`. `lib/database.ts` — `billingMode: BillingMode.PAY_PER_REQUEST`. `lib/queue.ts` — `SqsEventSource` with `batchSize: 1`. |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration exists for any data store. All three DynamoDB tables are created with `removalPolicy: RemovalPolicy.DESTROY`, which deletes the table and all data when the CloudFormation stack is deleted. No point-in-time recovery (PITR) is enabled. No AWS Backup plan is defined. No S3 backup buckets. |
| **Gap** | Critical data loss risk. A `cdk destroy` or accidental stack deletion will permanently delete all product catalog, basket, and order data. No PITR means no recovery from accidental item-level deletions or corruption. For a P0 service handling order data, this is a high-severity gap. |
| **Recommendation** | Immediately enable DynamoDB PITR on all three tables by adding `pointInTimeRecovery: true` to each Table construct in `lib/database.ts`. Change `removalPolicy` to `RemovalPolicy.RETAIN` for production tables to prevent accidental data deletion. Consider adding an AWS Backup plan with daily backups and 30-day retention. |
| **Evidence** | `lib/database.ts` — `removalPolicy: RemovalPolicy.DESTROY` on all three tables (`product`, `basket`, `order`). No `pointInTimeRecovery` property. No `aws_backup` constructs in any CDK file. |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | All services are inherently multi-AZ through AWS managed services. Lambda functions execute across multiple AZs within the region automatically. DynamoDB replicates data across 3 AZs within the region by default. API Gateway is a regional service with multi-AZ redundancy. EventBridge and SQS are also regionally distributed across AZs. |
| **Gap** | No multi-region fault isolation. All resources are in a single region (region not explicitly specified in `bin/aws-microservices.ts` — defaults to CLI-configured region). For a P0 service, consider multi-region resilience. |
| **Recommendation** | For regional resilience, the current architecture is well-positioned — all services are multi-AZ by default. For additional resilience, consider enabling DynamoDB global tables and deploying a secondary region stack for disaster recovery. |
| **Evidence** | `lib/microservice.ts` — Lambda (inherently multi-AZ). `lib/database.ts` — DynamoDB (inherently multi-AZ). `lib/apigateway.ts` — API Gateway (regional, multi-AZ). `bin/aws-microservices.ts` — No explicit `env` (region) configuration. |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | 100% of infrastructure is defined in AWS CDK (TypeScript). Six CDK construct files comprehensively cover all resources: DynamoDB tables (`lib/database.ts`), Lambda functions (`lib/microservice.ts`), API Gateways (`lib/apigateway.ts`), EventBridge bus and rules (`lib/eventbus.ts`), SQS queue (`lib/queue.ts`), and stack orchestration (`lib/aws-microservices-stack.ts`). CDK configuration is in `cdk.json` with feature flags. |
| **Gap** | IaC coverage is excellent. Minor gap: CDK version is `2.17.0` (early 2022 release), which is significantly outdated. Many CDK improvements, security fixes, and new construct features have been released since. |
| **Recommendation** | Update `aws-cdk-lib` from `2.17.0` to the latest v2 release in `package.json`. Consider migrating to Terraform if organizational preferences favor Terraform-based GitOps workflows. |
| **Evidence** | `lib/aws-microservices-stack.ts` — Stack composition. `package.json` — `"aws-cdk-lib": "2.17.0"`. `cdk.json` — CDK app configuration. All 6 `lib/*.ts` files define CDK constructs. |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CI/CD pipeline exists in the repository. No `.github/workflows/` directory, no `buildspec.yml`, no `Jenkinsfile`, no CodePipeline definition in CDK, no GitLab CI config. The `package.json` scripts section contains only `build`, `watch`, `test`, and `cdk` — no deploy automation scripts. Deployment is performed manually via `cdk deploy` from a developer workstation. |
| **Gap** | All deployments are manual, requiring a developer to run `cdk deploy` locally. This creates inconsistency (different developer environments), no audit trail of deployments, no automated quality gates, and no rollback mechanism. For a P0 service, manual deployment is a critical operational risk. |
| **Recommendation** | Implement a CI/CD pipeline (GitHub Actions or AWS CodePipeline) with stages: lint → test → synth → diff → deploy-staging → integration-test → deploy-production. Adopt GitOps practices where infrastructure changes are reviewed via pull requests before deployment. Add deployment notifications to track who deployed what and when. Avoid manual `cdk deploy` for production environments. |
| **Evidence** | No `.github/workflows/` directory. No `buildspec.yml`. No `Jenkinsfile`. No CodePipeline in CDK. `package.json` — `"scripts": { "build": "tsc", "watch": "tsc -w", "test": "jest", "cdk": "cdk" }`. |


### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | JavaScript (Node.js ES6 modules) is used for all three Lambda functions (`src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js`). TypeScript is used for CDK infrastructure code (`lib/*.ts`). Node.js/JavaScript has a mature cloud-native ecosystem with excellent AWS SDK support, Lambda runtime availability, and extensive community libraries. |
| **Gap** | Lambda source code uses JavaScript (not TypeScript), missing type safety benefits. TypeScript is used only for IaC. |
| **Recommendation** | Consider migrating Lambda function source code from JavaScript to TypeScript for type safety, better IDE support, and consistency with the CDK codebase. The CDK `NodejsFunction` construct already supports TypeScript Lambda functions natively with built-in bundling. |
| **Evidence** | `src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js` — JavaScript with ES6 imports. `lib/*.ts` — TypeScript CDK constructs. `package.json` — `typescript: ~3.9.7`. |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | The application is decomposed into three independently deployable microservices: **Product** (CRUD operations on product catalog), **Basket** (shopping cart management + checkout event publishing), and **Ordering** (order creation from events + order queries). Each service has its own: (1) Lambda function entry point, (2) `package.json` with independent dependencies, (3) dedicated DynamoDB table, (4) dedicated API Gateway. Cross-service communication uses EventBridge events (not shared database queries), enforcing loose coupling. No circular dependencies detected. |
| **Gap** | All three services are deployed as a single CloudFormation stack (`AwsMicroservicesStack`). True independent deployability would require separate stacks per service. The current single-stack approach means a change to the product service redeploys the entire infrastructure. |
| **Recommendation** | Consider splitting into per-service CDK stacks (e.g., `ProductStack`, `BasketStack`, `OrderingStack`) with cross-stack references for shared resources (EventBridge bus). This enables independent deployment and reduces blast radius of changes. |
| **Evidence** | `src/product/` — Independent service directory with own `package.json`. `src/basket/` — Independent service with EventBridge integration. `src/ordering/` — Independent service consuming SQS events. `lib/database.ts` — Per-service DynamoDB tables. `lib/apigateway.ts` — Per-service API Gateways. |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The checkout flow (the primary cross-service workflow) is fully asynchronous: basket Lambda publishes a `CheckoutBasket` event to EventBridge → EventBridge rule routes to SQS `OrderQueue` → ordering Lambda consumes from SQS. API Gateway invocations to all three Lambdas are synchronous HTTP request/response. The ordering service handles both async (SQS/EventBridge) and sync (API Gateway) invocations via runtime detection (`event.Records` vs `event.httpMethod`). |
| **Gap** | Only one cross-service flow (checkout) is async. Product and basket CRUD operations are synchronous. If additional cross-service communication is needed in the future (e.g., inventory updates, price changes), there is no established pattern for adding more async flows. |
| **Recommendation** | The current mix is appropriate for this architecture. For future growth, publish domain events for product catalog changes (`ProductCreated`, `ProductUpdated`, `PriceChanged`) and basket mutations to EventBridge to enable event-driven downstream processing. |
| **Evidence** | `src/basket/index.js` — `publishCheckoutBasketEvent()` publishes to EventBridge. `src/ordering/index.js` — `sqsInvocation()` and `eventBridgeInvocation()` handle async events; `apiGatewayInvocation()` handles sync HTTP. `lib/eventbus.ts` — `CheckoutBasketRule` event pattern. |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The checkout process (the most complex operation) is handled asynchronously: the basket Lambda publishes an event and immediately returns a 200 response, while order creation happens asynchronously via SQS → ordering Lambda. Lambda functions are inherently short-lived (15-minute maximum). No long-running synchronous operations were detected — all DynamoDB operations complete in milliseconds. |
| **Gap** | The async checkout flow is fire-and-forget — the basket Lambda returns a 200 response after publishing the event but provides no mechanism for the client to track order creation status. There is no status polling endpoint (e.g., `GET /order/status/{orderId}`) or callback/webhook mechanism. |
| **Recommendation** | Add an order status tracking mechanism: (1) Generate an orderId in the basket Lambda before publishing the event, (2) include orderId in the EventBridge event payload, (3) create a `GET /order/status/{orderId}` endpoint for status polling. This enables both human users and AI agents to track order completion. |
| **Evidence** | `src/basket/index.js` — `checkoutBasket()` publishes event then deletes basket, returns no orderId. `src/ordering/index.js` — `createOrder()` generates orderDate as sort key but no unique orderId for tracking. |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API versioning strategy detected. API Gateway routes are unversioned: `/product`, `/product/{id}`, `/basket`, `/basket/{userName}`, `/basket/checkout`, `/order`, `/order/{userName}`. No `/v1/` URL prefix, no `Accept-Version` headers, no versioning annotations, no changelog files. The API Gateway deploys to a single `prod` stage. |
| **Gap** | Any breaking API change (request/response format, route changes) will break all consumers simultaneously with no migration path. No OpenAPI specification exists to document the API contract. This is critical for agent integration — agents need stable, versioned API contracts to function as tools. |
| **Recommendation** | Implement URL-based versioning (e.g., `/v1/product`) in `lib/apigateway.ts`. Generate an OpenAPI specification documenting all endpoints, request/response schemas, and error formats. Use API Gateway stages (`v1`, `v2`) to manage versioned deployments. This is a prerequisite for exposing these APIs as agent tools. |
| **Evidence** | `lib/apigateway.ts` — Routes defined without version prefix: `apigw.root.addResource('product')`, `apigw.root.addResource('basket')`, `apigw.root.addResource('order')`. No OpenAPI import. No changelog. |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Cross-service communication uses EventBridge (event-driven, not direct service calls), which naturally decouples services — the basket service publishes to EventBridge bus name `SwnEventBus` via environment variable, not to a hard-coded ordering service endpoint. Within each service, DynamoDB table names are injected via CDK environment variables (`DYNAMODB_TABLE_NAME`, `EVENT_BUSNAME`). No hard-coded service-to-service endpoints exist. |
| **Gap** | No formal service registry or API catalog. Three separate API Gateways mean consumers must know each gateway's URL independently. No AWS Cloud Map, no App Mesh, no centralized API catalog for discovering available services. |
| **Recommendation** | Register services in AWS Cloud Map for DNS-based service discovery. Consider publishing an API catalog (using API Gateway's built-in export capabilities) that lists all available endpoints. For agent integration, generate a unified tool catalog documenting all three services' capabilities. |
| **Evidence** | `lib/microservice.ts` — Environment variables: `DYNAMODB_TABLE_NAME`, `EVENT_BUSNAME`, `EVENT_SOURCE`, `EVENT_DETAILTYPE`. `src/basket/index.js` — `process.env.EVENT_BUSNAME` (not hard-coded). `lib/eventbus.ts` — EventBridge decouples basket→ordering communication. |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No unstructured data storage patterns found. No S3 buckets defined in any CDK construct. No file upload handling in any Lambda function. No Textract, Tika, or document parsing libraries in any dependency manifest. The application stores only structured data (product catalog, basket items, orders) in DynamoDB. |
| **Gap** | No capability to handle unstructured data (product images, order documents, invoices, receipts). The product table schema includes an `imageFile` attribute (per comments in `lib/database.ts`) but no S3 storage or CDN is configured for serving images. |
| **Recommendation** | Add an S3 bucket for product images and order-related documents. Configure CloudFront for image delivery. For future AI integration, S3-stored product images and documents can be processed by Amazon Textract or indexed into a Bedrock Knowledge Base. |
| **Evidence** | `lib/database.ts` — Comment: `product : PK: id -- name - description - imageFile - price - category` (references imageFile but no S3). No S3 bucket in any CDK file. No file handling in Lambda functions. |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Each microservice has a dedicated `ddbClient.js` module that creates and exports a `DynamoDBClient()` instance. All DynamoDB operations within each service use this shared client. The product service has 6 data access functions, the basket service has 5, and the ordering service has 4 — all using consistent `marshall`/`unmarshall` patterns with the `@aws-sdk/client-dynamodb` and `@aws-sdk/util-dynamodb` packages. Per-service data ownership is maintained (each service accesses only its own table). |
| **Gap** | No DAO/repository abstraction layer — DynamoDB `marshall`/`unmarshall` calls and raw `TableName`, `Key`, `ExpressionAttributeValues` parameters are spread throughout each service's `index.js`. This creates duplication and makes it harder to change the data access pattern (e.g., adding caching, switching to DynamoDB Document Client). |
| **Recommendation** | Extract data access logic into per-service repository modules (e.g., `productRepository.js`, `basketRepository.js`, `orderRepository.js`) that encapsulate DynamoDB operations behind a clean interface. This improves testability, reduces duplication, and makes future data layer changes easier. |
| **Evidence** | `src/product/ddbClient.js`, `src/basket/ddbClient.js`, `src/ordering/ddbClient.js` — Shared DynamoDB client modules. `src/product/index.js` — Direct DynamoDB operations (GetItemCommand, ScanCommand, etc.) with marshall/unmarshall. |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | All databases are DynamoDB — a fully managed serverless database service with no user-configurable engine version. AWS manages all engine versioning, patching, and lifecycle concerns. There is no version to pin and no EOL risk. No RDS, DocumentDB, ElastiCache, or other versioned database engines are used. |
| **Gap** | No gaps. DynamoDB's serverless model eliminates engine version management entirely. |
| **Recommendation** | No action needed. DynamoDB's managed lifecycle is a strength. If relational data needs emerge in the future, consider Amazon Aurora Serverless v2 (preferred per preferences) with explicit engine version pinning. |
| **Evidence** | `lib/database.ts` — DynamoDB `Table` constructs with no engine version parameter (DynamoDB does not have one). No RDS or other versioned database in any CDK file. |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | DynamoDB is a NoSQL database with no support for stored procedures, triggers, or proprietary SQL. All business logic resides in the application layer (Lambda functions): price calculation (`prepareOrderPayload` in `src/basket/index.js`), data transformation (`marshall`/`unmarshall`), and query construction. No `.sql` files, no stored procedures, no proprietary SQL constructs anywhere in the repository. |
| **Gap** | No gaps. All business logic is in the application layer, which is the desired state for cloud-native applications. |
| **Recommendation** | No action needed. Maintain the pattern of keeping business logic in Lambda functions rather than introducing database-level logic. |
| **Evidence** | `src/basket/index.js` — `prepareOrderPayload()` calculates totalPrice in application code. `src/product/index.js` — All CRUD logic in JavaScript. No `.sql` files in repository. |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail configuration found in any CDK construct. No `aws_cloudtrail.Trail` or equivalent logging infrastructure. Lambda functions use `console.log()` for application-level logging (which flows to CloudWatch Logs by default), but there is no structured audit trail for API calls, data access, or administrative actions. |
| **Gap** | No CloudTrail means no record of who called which API, who deployed stack changes, or who accessed DynamoDB data. For a P0 e-commerce service handling order and payment data, this is a compliance and security gap. |
| **Recommendation** | Add a CloudTrail trail in CDK with log file validation enabled and S3 bucket with object lock for immutable storage. Enable CloudTrail data events for DynamoDB to track all read/write operations on the product, basket, and order tables. Enable API Gateway access logging. |
| **Evidence** | `lib/aws-microservices-stack.ts` — No CloudTrail import or construct. No `Trail` resource in any CDK file. `src/*/index.js` — Only `console.log()` and `console.error()` (no structured audit logging). |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | DynamoDB provides AWS-managed encryption at rest by default using an AWS-owned key. All three tables (`product`, `basket`, `order`) benefit from this default encryption without explicit configuration. However, no customer-managed KMS keys (CMKs) are configured on any resource. |
| **Gap** | No customer-managed KMS keys. AWS-owned encryption provides baseline protection but does not offer customer control over key rotation, access policies, or audit trails via CloudTrail KMS events. For a P0 service handling order data (payment methods, addresses), customer-managed encryption provides better governance. |
| **Recommendation** | Create a customer-managed KMS key and apply it to all DynamoDB tables via the `encryption` and `encryptionKey` properties in `lib/database.ts`. Configure key rotation and key policies with least-privilege access. |
| **Evidence** | `lib/database.ts` — No `encryption` or `encryptionKey` property on Table constructs. DynamoDB default encryption applies automatically. |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No authentication is configured on any API Gateway endpoint. All three REST APIs (Product Service, Basket Service, Order Service) are completely open to the internet. No Cognito authorizer, no Lambda authorizer, no API key requirement, no IAM authorization, no OAuth2/JWT validation. Any entity can invoke any endpoint without credentials. |
| **Gap** | Critical security vulnerability. All CRUD operations (including POST /product, DELETE /product/{id}, POST /basket/checkout) are accessible without authentication. An attacker can create/delete products, manipulate baskets, and trigger checkout flows. This blocks production readiness and agent integration (agents need authenticated endpoints). |
| **Recommendation** | Implement API Gateway authentication immediately. Options (in order of preference): (1) Amazon Cognito authorizer for user-facing endpoints with JWT validation, (2) IAM authorization for service-to-service and agent-to-service calls, (3) Lambda authorizer for custom auth logic. At minimum, add API keys with usage plans for rate limiting while implementing full auth. |
| **Evidence** | `lib/apigateway.ts` — `new LambdaRestApi(this, 'productApi', {...})` — no `defaultMethodOptions` with authorization. No `addAuthorizer()` calls. No Cognito user pool in any CDK file. |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No identity provider integration exists. No Amazon Cognito user pool, no OIDC configuration, no SAML federation, no SSO setup. The application has no concept of user authentication — the `userName` field in basket and order operations is a client-provided string with no identity verification. |
| **Gap** | No centralized identity means no user authentication, no session management, no access control. The `userName` parameter in basket/order operations is trusted from the client without verification — any caller can claim any userName. |
| **Recommendation** | Implement Amazon Cognito User Pool for user authentication. Configure Cognito as API Gateway authorizer. Use Cognito tokens to derive userName from authenticated identity rather than trusting client-provided values. For agent access, configure IAM-based authorization with Cognito identity pools. |
| **Evidence** | `lib/apigateway.ts` — No Cognito authorizer. `src/basket/index.js` — `event.pathParameters.userName` used without identity verification. `src/ordering/index.js` — `event.pathParameters.userName` trusted from client. No Cognito in any CDK file. |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Environment variables used in Lambda functions contain only non-sensitive configuration: DynamoDB table names (`DYNAMODB_TABLE_NAME`), DynamoDB key names (`PRIMARY_KEY`, `SORT_KEY`), and EventBridge configuration (`EVENT_SOURCE`, `EVENT_DETAILTYPE`, `EVENT_BUSNAME`). No hardcoded credentials, API keys, or connection strings found in source code. DynamoDB access uses IAM roles (granted via `table.grantReadWriteData()`). |
| **Gap** | While no secrets are currently hardcoded, no secrets management infrastructure exists. If the application needs to integrate with external services (payment processing, email, third-party APIs), there is no Secrets Manager or Vault to store those credentials securely. The `removalPolicy: DESTROY` on tables could be considered a form of "insecure configuration." |
| **Recommendation** | Provision AWS Secrets Manager infrastructure in CDK now, even if not immediately needed. Establish the pattern for future secret storage with automated rotation. This is especially important for agent integration — agents may need API keys or tokens to authenticate with these services. |
| **Evidence** | `lib/microservice.ts` — `environment: { PRIMARY_KEY: 'id', DYNAMODB_TABLE_NAME: productTable.tableName }` (non-sensitive). IAM grants: `productTable.grantReadWriteData(productFunction)`. No Secrets Manager in CDK. No hardcoded passwords in source code. |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Lambda is managed compute — AWS handles OS-level patching and security updates for the underlying execution environment. However, all three Lambda functions use `Runtime.NODEJS_14_X`, which reached end-of-life in April 2023 and end-of-support in March 2024. No vulnerability scanning is configured (no Dependabot, no Snyk, no AWS Inspector). No dependency audit process exists. |
| **Gap** | EOL Lambda runtime is a significant security gap. Node.js 14 no longer receives security patches. The `@aws-sdk/client-dynamodb: ^3.55.0` and related packages are from early 2022 and may contain known vulnerabilities. CDK version `2.17.0` is also outdated. |
| **Recommendation** | Upgrade Lambda runtime to `NODEJS_20_X` or `NODEJS_22_X`. Update all `@aws-sdk/*` dependencies to latest v3 versions. Update `aws-cdk-lib` to latest v2. Enable Dependabot or Snyk for automated dependency vulnerability scanning. Consider using Lambda Powertools for Node.js which includes security best practices. |
| **Evidence** | `lib/microservice.ts` — `runtime: Runtime.NODEJS_14_X` on all three functions. `src/product/package.json` — `@aws-sdk/client-dynamodb: ^3.55.0`. `package.json` — `aws-cdk-lib: 2.17.0`, `typescript: ~3.9.7`. |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No security scanning tools are integrated into any pipeline (no pipeline exists). No Dependabot configuration (`.github/dependabot.yml`), no Snyk policy (`.snyk`), no SonarQube configuration, no npm audit in build scripts, no SAST tools. The `package.json` `test` script runs Jest but there are no security-focused tests. |
| **Gap** | Dependencies with known vulnerabilities can be deployed without detection. No automated security gates exist at any point in the development or deployment process. |
| **Recommendation** | When implementing the CI/CD pipeline (INF-Q11 recommendation): add `npm audit --audit-level=high` as a pipeline stage, configure Dependabot for automated dependency updates, integrate Amazon CodeGuru Reviewer or Semgrep for SAST analysis, and add a security gate that blocks deployment on critical findings. |
| **Evidence** | No `.github/dependabot.yml`. No `.snyk`. No security scanning in `package.json` scripts. No SonarQube or CodeGuru configuration. No security-related test files. |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing is instrumented. No AWS X-Ray SDK, no OpenTelemetry SDK, no tracing libraries in any Lambda function dependency manifest. No tracing configuration on API Gateway. No trace ID propagation between services. The checkout flow (basket → EventBridge → SQS → ordering) has no mechanism to correlate a request across the three services. |
| **Gap** | Debugging cross-service failures is impossible without tracing. If a checkout event fails in the ordering Lambda, there is no way to trace it back to the original basket API call. For agent-initiated requests (future state), tracing is essential to understand end-to-end request flows. |
| **Recommendation** | Enable AWS X-Ray tracing on all Lambda functions (add `tracing: Tracing.ACTIVE` in CDK) and API Gateway stages. Add X-Ray SDK to Lambda dependencies for trace propagation. Propagate trace IDs through EventBridge event metadata and SQS message attributes. Consider adopting Lambda Powertools for Node.js which provides built-in X-Ray integration. |
| **Evidence** | `src/product/package.json`, `src/basket/package.json`, `src/ordering/package.json` — No X-Ray or OpenTelemetry dependencies. `lib/microservice.ts` — No `tracing` property on `NodejsFunctionProps`. `lib/apigateway.ts` — No `deployOptions.tracingEnabled`. |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions found anywhere in the repository. No CloudWatch alarms, no SLO configuration files, no error budget tracking, no availability or latency targets defined. |
| **Gap** | Without SLOs, there is no objective measure of whether the service is meeting user expectations. For a P0 service, SLOs are critical for prioritizing operational investments and detecting degradation. |
| **Recommendation** | Define SLOs for critical user journeys: (1) Product listing latency (p99 < 500ms), (2) Checkout success rate (> 99.5%), (3) Order query availability (> 99.9%). Implement as CloudWatch composite alarms with error budget tracking. |
| **Evidence** | No CloudWatch alarm resources in any CDK file. No SLO definition files. No error budget configuration. |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metrics are published. All three Lambda functions use `console.log()` for logging, which generates CloudWatch Logs but no custom CloudWatch metrics. No `PutMetricData` calls, no EMF (Embedded Metric Format) logs, no custom dashboards. Only default Lambda metrics (invocations, errors, duration) are available. |
| **Gap** | No visibility into business outcomes: checkout conversion rates, average order value, product catalog size, basket abandonment. Only infrastructure metrics (Lambda invocations, errors) are available. |
| **Recommendation** | Publish custom business metrics using CloudWatch EMF (Embedded Metric Format) in Lambda functions: checkouts per minute, average order value, products created, basket add-to-cart events. Use Lambda Powertools for Node.js metrics utility for simplified EMF integration. Create a CloudWatch dashboard for business KPIs. |
| **Evidence** | `src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js` — Only `console.log()` and `console.error()` calls. No CloudWatch metrics SDK imports. No `PutMetricData` or EMF patterns. |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No alerting or anomaly detection configured. No CloudWatch alarms in any CDK construct. No SNS topics for notifications. No PagerDuty, OpsGenie, or other incident management integration. No composite alarms, no anomaly detection models. |
| **Gap** | No proactive detection of issues. If error rates spike, latency increases, or the checkout flow breaks, there is no automated notification. Issues are discovered only when users report them. |
| **Recommendation** | Add CloudWatch alarms for: (1) Lambda error rate > 1% per function, (2) Lambda p99 duration > 3 seconds, (3) SQS `ApproximateAgeOfOldestMessage` > 60 seconds (checkout backlog), (4) DynamoDB throttled requests > 0. Route alarms to an SNS topic connected to a team notification channel. Enable CloudWatch anomaly detection on error rates for adaptive alerting. |
| **Evidence** | No `Alarm` construct in any CDK file. No `aws_cloudwatch` imports beyond what CDK uses internally. No SNS topic for alerting. No incident management configuration. |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No deployment strategy exists. Deployment is performed manually via `cdk deploy`, which performs a direct CloudFormation stack update. Lambda function code is updated to all traffic immediately with no canary, blue/green, or linear deployment. No CodeDeploy configuration, no Lambda aliases, no traffic shifting, no automated rollback. |
| **Gap** | Any deployment goes directly to all production traffic with no safety net. If a code change introduces a regression, all users are impacted immediately with no automated rollback. For a P0 e-commerce service, this is a high-risk operational gap. |
| **Recommendation** | Implement Lambda deployment preferences using AWS CodeDeploy integration: configure `currentVersionOptions` and `autoDeploymentGroup` in CDK for canary deployments (10% traffic for 5 minutes, then 100%). Add CloudWatch alarms on error rates as rollback triggers. Use API Gateway canary deployments for routing-level traffic shifting. |
| **Evidence** | No CodeDeploy configuration in CDK. No Lambda aliases or versions. No deployment preferences on `NodejsFunction`. `package.json` — Only `cdk deploy` via manual CLI. |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | A test file exists at `test/aws-microservices.test.ts` but is entirely commented out. The file contains a single test case (`'SQS Queue Created'`) with all assertions commented. Jest configuration exists (`jest.config.js`) pointing to the `test/` directory with `ts-jest` transform, but there are no runnable tests. No integration tests, no API contract tests, no end-to-end tests. |
| **Gap** | Zero automated test coverage. No regression detection for CDK template changes, API behavior changes, or event schema changes. The EventBridge event contract (`com.swn.basket.checkoutbasket` / `CheckoutBasket`) is undocumented and untested. |
| **Recommendation** | Implement a testing pyramid: (1) **CDK snapshot tests** — Uncomment and extend `test/aws-microservices.test.ts` to validate CloudFormation template output. (2) **Unit tests** — Test Lambda handler logic (data transformation, error handling) with mocked DynamoDB client. (3) **Integration tests** — Test API Gateway endpoints with test data using real deployed infrastructure. (4) **Contract tests** — Validate EventBridge event schema (`checkoutbasketevents.json` provides a starting point). |
| **Evidence** | `test/aws-microservices.test.ts` — Entirely commented out. `jest.config.js` — Configured but no runnable tests. `src/basket/checkoutbasketevents.json` — Sample event payload (could serve as contract test fixture). |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No incident response automation exists. No runbooks (markdown, YAML, or SSM Automation documents), no self-healing patterns, no automated remediation Lambda functions, no Step Functions for incident workflows. No DLQ (dead-letter queue) for failed SQS messages — failed checkout events are silently dropped after SQS retry exhaustion. |
| **Gap** | All incident response is ad hoc. Failed checkout events (SQS messages that can't be processed) are lost with no notification or remediation. No documented procedures for common failure scenarios (DynamoDB throttling, Lambda timeouts, EventBridge delivery failures). |
| **Recommendation** | Add a dead-letter queue (DLQ) for the `OrderQueue` to capture failed checkout events. Create an alarm on DLQ message count. Write operational runbooks for: (1) failed checkout remediation, (2) DynamoDB throttling response, (3) Lambda error spike investigation. Implement SSM Automation documents for automated remediation of common issues. |
| **Evidence** | `lib/queue.ts` — `new Queue(this, 'OrderQueue', {...})` — No `deadLetterQueue` property. No runbook files in repository. No SSM documents. No remediation Lambda functions. |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership structure exists. No per-service dashboards, no alarms with named owners, no CODEOWNERS file, no team attribution on any resources. No SLO definitions with team ownership. No documentation of who is responsible for each service's operational health. |
| **Gap** | No clear ownership means monitoring gaps are not detected and addressed. When the checkout flow fails, there is no defined escalation path or on-call rotation. |
| **Recommendation** | Create a CODEOWNERS file mapping each service directory to a team. Define per-service CloudWatch dashboards with key metrics. Tag all resources with `team` and `service` tags. Define on-call ownership for each service. |
| **Evidence** | No `.github/CODEOWNERS` file. No CloudWatch dashboard definitions in CDK. No team tags on any resources. No ownership documentation. |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No tags are applied to any CDK resource. DynamoDB tables, Lambda functions, API Gateways, EventBridge bus, SQS queue — all created without any tags. No `Tags.of()` calls in CDK, no default tags, no tag enforcement. |
| **Gap** | No cost allocation, no ownership attribution, no environment identification. AWS cost reports cannot attribute costs to this service. During incidents, there is no way to identify which team owns which resources. |
| **Recommendation** | Add default tags at the stack level in `bin/aws-microservices.ts` using `Tags.of(app).add()`: `Environment` (prod/staging/dev), `Service` (aws-microservices), `Team` (owning team), `CostCenter`, `Priority` (P0). This propagates tags to all resources automatically. Add AWS Config rule `required-tags` for enforcement. |
| **Evidence** | `lib/aws-microservices-stack.ts` — No `Tags` import or usage. `lib/database.ts` — No tags on Table constructs. `lib/microservice.ts` — No tags on Lambda functions. `bin/aws-microservices.ts` — No `Tags.of()` calls. |


## Learning Materials

Learning materials are included for the 2 triggered pathways: **Move to Modern DevOps** and **Move to AI**.

| Pathway | Learning Resources |
|---------|-------------------|
| **Move to Modern DevOps** | [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ) |
| **Move to AI** | [Move to AI](https://skillbuilder.aws/learning-plan/VDFEE4ACCV) · [Amazon Bedrock Getting Started](https://skillbuilder.aws/learn/63KTRM86DQ) · [Introduction to Agentic AI on AWS](https://skillbuilder.aws/learn/DNBD5MT8ZD) |

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `bin/aws-microservices.ts` | INF-Q9, INF-Q10 | CDK app entry point; no explicit region configuration |
| `cdk.json` | INF-Q10 | CDK configuration with feature flags |
| `jest.config.js` | OPS-Q6 | Jest configuration (tests exist but are commented out) |
| `package.json` | INF-Q10, INF-Q11, SEC-Q6, SEC-Q7 | Root dependencies: aws-cdk-lib 2.17.0, TypeScript ~3.9.7; no security scanning scripts |
| `lib/apigateway.ts` | INF-Q5, INF-Q6, SEC-Q3, SEC-Q4, APP-Q5, APP-Q6 | Three LambdaRestApi gateways with no auth, no throttling, no versioning, no WAF |
| `lib/aws-microservices-stack.ts` | INF-Q10, SEC-Q1, OPS-Q8, OPS-Q9 | Stack composition; no CloudTrail, no tags, no observability |
| `lib/database.ts` | INF-Q2, INF-Q8, SEC-Q2, DATA-Q1, DATA-Q3, OPS-Q9 | Three DynamoDB tables with PAY_PER_REQUEST, DESTROY removal policy, no PITR, no KMS, no tags |
| `lib/eventbus.ts` | INF-Q3, INF-Q4, APP-Q3, APP-Q6 | EventBridge bus (SwnEventBus) and CheckoutBasketRule routing to SQS |
| `lib/microservice.ts` | INF-Q1, INF-Q7, SEC-Q5, SEC-Q6, OPS-Q9 | Three Lambda functions with NODEJS_14_X runtime, environment variables, no tracing, no tags |
| `lib/queue.ts` | INF-Q4, OPS-Q7 | SQS OrderQueue with 30s visibility timeout, no DLQ |
| `src/basket/checkoutbasketevents.json` | OPS-Q6 | Sample EventBridge event payload (potential contract test fixture) |
| `src/basket/ddbClient.js` | DATA-Q2 | DynamoDB client module for basket service |
| `src/basket/eventBridgeClient.js` | INF-Q4, APP-Q3 | EventBridge client module for async event publishing |
| `src/basket/index.js` | APP-Q2, APP-Q3, APP-Q4, DATA-Q4, OPS-Q1, OPS-Q3 | Basket Lambda handler: CRUD + checkout with EventBridge publish, console.log only |
| `src/basket/package.json` | APP-Q1, OPS-Q1 | Basket dependencies: @aws-sdk/client-dynamodb ^3.55.0, @aws-sdk/client-eventbridge ^3.58.0 |
| `src/ordering/ddbClient.js` | DATA-Q2 | DynamoDB client module for ordering service |
| `src/ordering/index.js` | APP-Q2, APP-Q3, APP-Q4, DATA-Q4, OPS-Q1, OPS-Q3 | Ordering Lambda handler: SQS/EventBridge/API Gateway invocation routing, console.log only |
| `src/ordering/package.json` | APP-Q1, OPS-Q1 | Ordering dependencies: @aws-sdk/client-dynamodb ^3.58.0 |
| `src/product/ddbClient.js` | DATA-Q2 | DynamoDB client module for product service |
| `src/product/index.js` | APP-Q2, APP-Q3, DATA-Q2, DATA-Q4, OPS-Q1, OPS-Q3 | Product Lambda handler: full CRUD with DynamoDB, console.log only |
| `src/product/package.json` | APP-Q1, OPS-Q1 | Product dependencies: @aws-sdk/client-dynamodb ^3.55.0 |
| `test/aws-microservices.test.ts` | OPS-Q6 | Entirely commented-out test file — no runnable tests |
| `README.md` | Quick Agent Wins (RAG) | Architecture description, API endpoint documentation, deployment instructions |
| `tsconfig.json` | APP-Q1 | TypeScript configuration (ES2018 target) |
