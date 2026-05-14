# Modernization Readiness Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | aws-microservices |
| **Date** | 2026-04-17 |
| **Repo Type** | application |
| **Priority** | P0 |
| **Tags** | microservices, serverless, event-driven |
| **Context** | Event-driven serverless microservices (product, basket, ordering) with Lambda, DynamoDB, EventBridge, SQS. The agent will invoke these as tools for order status lookups and return processing. |
| **Overall Score** | 2.27 / 4.0 |

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 2.64 / 4.0 | 🟡 Partial |
| Application Architecture (APP) | 3.00 / 4.0 | 🟡 Partial |
| Data Platform Modernization (DATA) | 3.00 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 1.71 / 4.0 | 🟠 Needs Work |
| Operations & Observability (OPS) | 1.00 / 4.0 | ❌ Not Present |
| **Overall** | **2.27 / 4.0** | **🟠 Needs Work** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q11: CI/CD Automation | 1 | No CI/CD pipeline — all deployments are manual `cdk deploy` | Blocks safe, repeatable deployments; triggers Move to Modern DevOps pathway |
| 2 | INF-Q5: Network Security | 1 | No VPC, security groups, or network segmentation configured | Lambda functions and API Gateway endpoints lack network-level protection |
| 3 | SEC-Q3: API Authentication | 1 | No authentication on any API Gateway endpoint | All REST endpoints are publicly accessible without auth — critical security gap |
| 4 | OPS-Q5: Deployment Strategy | 1 | Manual `cdk deploy` with no blue/green, canary, or rolling strategy | No safe rollback; production changes are all-or-nothing; supports Move to Modern DevOps |
| 5 | SEC-Q1: Audit Logging | 1 | No CloudTrail or audit logging configured in IaC | No ability to trace API calls, diagnose incidents, or meet compliance requirements |

---

## Quick Agent Wins

### Data Query Agent

- **Prerequisite:** DATA-Q2 = 3 (≥ 2). DynamoDB tables have clear, well-defined schemas in `lib/database.ts` — product (PK: id), basket (PK: userName), order (PK: userName, SK: orderDate). Each service has a dedicated `ddbClient.js` module.
- **What it enables:** A natural-language-to-DynamoDB query agent that translates user questions like "What orders has user X placed?" or "Show me product details for ID Y" into DynamoDB `GetItem`, `Query`, or `Scan` operations. This directly supports the stated goal of agents invoking these services as tools for order status lookups and return processing.
- **Additional steps:** No OpenAPI spec exists — generate OpenAPI specifications for the three API Gateway endpoints (Product, Basket, Order) to enable full tool discovery. Consider adding Amazon Bedrock SDK (`@aws-sdk/client-bedrock-runtime`) to a new agent Lambda function.
- **Effort:** Medium — DynamoDB schemas are clean but API documentation needs to be generated; agent Lambda function needs to be created with Bedrock integration.

### RAG-Based Knowledge Agent

- **Prerequisite:** README.md exists with architecture documentation, API endpoint descriptions, and deployment instructions. `src/basket/checkoutbasketevents.json` provides event schema examples.
- **What it enables:** A RAG-based knowledge agent that indexes the existing documentation (README, code comments, event schemas) to answer developer questions about the architecture, API usage, and checkout flow without reading source code directly.
- **Additional steps:** Current documentation corpus is limited (README.md only). Expand with generated API documentation, architecture decision records, and operational runbooks. Index documentation into Amazon Bedrock Knowledge Base with S3 as the data source.
- **Effort:** Medium — documentation corpus needs expansion; Bedrock Knowledge Base setup required.

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 3 — application already uses microservices with Lambda, DynamoDB, EventBridge, SQS |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1 = 4 — compute is already serverless (Lambda); contextual guard: SHALL NOT trigger for Lambda/Fargate |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 — no stored procedures or proprietary SQL; no commercial DB engines (DynamoDB is AWS-native) |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 = 4 — all databases are fully managed DynamoDB |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 = 4 — messaging is managed (EventBridge, SQS); no data processing workloads detected |
| 6 | Move to Modern DevOps | **Triggered** | High | Medium | INF-Q11 = 1 (< 3) — no CI/CD automation; OPS-Q5 = 1 — no deployment strategy; OPS-Q6 = 1 — no integration tests |
| 7 | Move to AI | **Triggered** | Medium | Medium | No AI/agent frameworks detected; context mentions "agent" for order status lookups and return processing |

---

### Pathway: Move to Modern DevOps

**Status:** Triggered
**Priority:** High
**Estimated Effort:** Medium

#### Current State

- **IaC Coverage (INF-Q10 = 4):** All infrastructure is defined in AWS CDK (TypeScript) — Lambda functions, DynamoDB tables, API Gateway, EventBridge bus, SQS queue. This is a strong foundation.
- **CI/CD State (INF-Q11 = 1):** No CI/CD pipeline exists. The only deployment method is manual `cdk deploy` from a developer workstation, as documented in `README.md`. No `.github/workflows/`, no `buildspec.yml`, no `Jenkinsfile`, no CodePipeline resource in CDK.
- **Deployment Strategy (OPS-Q5 = 1):** No blue/green, canary, or rolling deployment. Manual `cdk deploy` deploys all resources at once with no staged rollout or automated rollback.
- **Testing (OPS-Q6 = 1):** The test file `test/aws-microservices.test.ts` has all tests commented out. No integration tests, no API contract tests, no automated test execution.

#### Recommendations

1. **Implement CI/CD Pipeline with GitOps:**
   - Create a GitHub Actions workflow (`.github/workflows/deploy.yml`) or AWS CodePipeline with CodeBuild for automated build, test, and deploy stages.
   - Adopt a GitOps model: changes merged to `main` trigger automated `cdk diff` → `cdk deploy` with approval gates for production.
   - Use CDK Pipelines (`aws-cdk-lib/pipelines`) to define the deployment pipeline as CDK code — keeping everything in IaC.
   - Consider migrating IaC to Terraform (per preferences) with Terraform Cloud or Atlantis for GitOps-based infrastructure management.

2. **Add Deployment Safety:**
   - Configure Lambda function aliases with weighted traffic shifting for canary deployments using AWS CodeDeploy.
   - Implement CloudWatch alarms as deployment rollback triggers (error rate, latency thresholds).
   - Add pre-deployment `cdk diff` review step in the pipeline.

3. **Enable Automated Testing:**
   - Uncomment and implement CDK assertion tests in `test/aws-microservices.test.ts` to validate infrastructure changes.
   - Add integration tests using tools like Newman (Postman CLI) or custom test scripts that validate API Gateway endpoints after deployment.
   - Implement contract tests for the EventBridge event schema (`com.swn.basket.checkoutbasket` / `CheckoutBasket`).

4. **Add Security Scanning to Pipeline:**
   - Integrate `npm audit` for dependency vulnerability scanning.
   - Add CDK-nag for IaC security and compliance validation.
   - Consider Semgrep or SonarQube for SAST scanning of Lambda handler code.

#### Representative AWS Services
- AWS CodePipeline, AWS CodeBuild, AWS CodeDeploy
- CDK Pipelines (`aws-cdk-lib/pipelines`)
- AWS CloudFormation (CDK backend)
- Amazon CloudWatch (deployment alarms and rollback triggers)

---

### Pathway: Move to AI

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

#### Current AI/Agent Infrastructure State

No AI/agent infrastructure exists in the repository:
- **AI Frameworks:** No imports of Bedrock SDK, LangChain, Strands, OpenAI, Spring AI, HuggingFace, or SageMaker SDK in any source file.
- **Vector Database:** No OpenSearch with vector engine, Pinecone, pgvector, Weaviate, or Qdrant.
- **RAG Implementation:** No embedding generation, vector store queries, or retrieval chain patterns.
- **Agent Evaluation:** No Ragas, DeepEval, or custom evaluation harnesses.

#### Contextual Trigger

The analysis context explicitly states: *"The agent will invoke these as tools for order status lookups and return processing."* The term "agent" is an AI-related signal term that confirms AI/agent intent for this service.

#### Application Domain and AI Use Cases

The e-commerce microservices architecture presents natural agent integration opportunities:

1. **Order Status Lookup Agent:** An Amazon Bedrock-powered agent that queries the Order service API (`GET /order/{userName}`) to provide natural-language order status responses.
2. **Return Processing Agent:** An agent that orchestrates the checkout-in-reverse flow — querying orders, initiating returns via the Basket service, and creating refund records.
3. **Product Discovery Agent:** An agent that uses the Product service API (`GET /product?category=...`) to help customers find products through conversational search.

#### Recommendations

1. **Start with Amazon Bedrock Agents:**
   - Create Bedrock agent action groups that map to the existing API Gateway endpoints (Product, Basket, Order).
   - Define OpenAPI specs for each service to enable Bedrock Agents tool discovery.
   - Use Amazon Bedrock with Claude or Nova models for natural language understanding.

2. **Generate API Specifications:**
   - Create OpenAPI 3.0 specs for the three API Gateway REST APIs. This is a prerequisite for both Bedrock Agents and the API-aware Quick Agent Win.
   - Document request/response schemas based on the DynamoDB table structures defined in `lib/database.ts`.

3. **Add Agent Infrastructure to CDK:**
   - Add `@aws-sdk/client-bedrock-runtime` and `@aws-sdk/client-bedrock-agent-runtime` to a new agent Lambda function.
   - Define Bedrock Agent resources in CDK (or consider Amazon Bedrock AgentCore for managed agent hosting).
   - Configure IAM roles with least-privilege access to invoke the existing Lambda functions or API Gateway endpoints.

4. **Implement Agent Evaluation:**
   - Set up an evaluation framework (e.g., Ragas or DeepEval) to measure agent accuracy on order status lookups and return processing scenarios.
   - Create a test dataset of sample queries and expected responses.

#### Representative AWS Services
- Amazon Bedrock (foundation models, agents, knowledge bases)
- Amazon Bedrock AgentCore (managed agent hosting)
- Amazon API Gateway (existing — used as tool endpoints for agents)
- Amazon DynamoDB (existing — data source for agent queries)
- Amazon EventBridge (existing — event-driven orchestration for return processing)

#### Foundation Requirements
Before AI integration, address these prerequisites:
- **API Documentation:** Generate OpenAPI specs (currently absent — APP-Q5 = 1).
- **API Authentication:** Add Cognito or IAM-based auth to API Gateway (currently absent — SEC-Q3 = 1). Agent requests must be authenticated.
- **Observability:** Add distributed tracing (OPS-Q1 = 1) to trace agent invocations through the microservice chain.

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | All compute workloads use AWS Lambda (100% serverless). Three Lambda functions are defined via `NodejsFunction` in `lib/microservice.ts`: `productLambdaFunction`, `basketLambdaFunction`, and `orderingLambdaFunction`. Runtime is `Runtime.NODEJS_14_X`. No EC2 instances, ECS tasks, or EKS workloads. |
| **Gap** | Lambda runtime `NODEJS_14_X` is end-of-life (since November 2023). While this doesn't affect the managed compute score (Lambda is fully managed), it is a runtime currency issue scored under SEC-Q6. |
| **Recommendation** | Upgrade Lambda runtime to `Runtime.NODEJS_20_X` or `Runtime.NODEJS_22_X` in `lib/microservice.ts`. Consider configuring Lambda reserved concurrency to protect downstream DynamoDB tables from traffic spikes. |
| **Evidence** | `lib/microservice.ts` — `Runtime.NODEJS_14_X`, `NodejsFunction` construct |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | All three databases are Amazon DynamoDB tables with `BillingMode.PAY_PER_REQUEST` (on-demand). Defined in `lib/database.ts`: `product` (PK: id), `basket` (PK: userName), `order` (PK: userName, SK: orderDate). No self-managed databases on EC2 or in containers. |
| **Gap** | None for managed database status. DynamoDB is fully managed with automated failover. However, `RemovalPolicy.DESTROY` is set on all tables — production data would be deleted on stack deletion. |
| **Recommendation** | Change `RemovalPolicy.DESTROY` to `RemovalPolicy.RETAIN` for production tables. Enable Point-in-Time Recovery (PITR) for data protection (see INF-Q8). |
| **Evidence** | `lib/database.ts` — `Table` construct, `BillingMode.PAY_PER_REQUEST`, `RemovalPolicy.DESTROY` |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No workflow orchestration service is used. The checkout flow follows a simple event chain: Basket Lambda → EventBridge (`PutEventsCommand`) → SQS (`OrderQueue`) → Ordering Lambda. This is a linear event-driven flow, not a multi-step orchestrated workflow with error handling, retries, or branching logic. No Step Functions, Temporal, or Camunda detected. |
| **Gap** | The checkout flow lacks explicit error handling, retry logic, compensation actions, and state management. If the ordering Lambda fails after the basket is deleted, there is no recovery mechanism. |
| **Recommendation** | Implement AWS Step Functions to orchestrate the checkout workflow with explicit error handling, retry policies, and compensation steps. This would provide visual workflow management and a clear audit trail. Use EventBridge as the trigger and Step Functions for orchestration. |
| **Evidence** | `lib/eventbus.ts` — EventBridge rule targets SQS directly; `src/basket/index.js` — `checkoutBasket` deletes basket before confirming order creation |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Managed messaging services are used for inter-service communication. Amazon EventBridge (`SwnEventBus`) is defined in `lib/eventbus.ts` with a rule (`CheckoutBasketRule`) that routes `CheckoutBasket` events from source `com.swn.basket.checkoutbasket` to an SQS queue. Amazon SQS (`OrderQueue`) is defined in `lib/queue.ts` with `visibilityTimeout: 30s` and `batchSize: 1`. The Basket service publishes events via `PutEventsCommand` in `src/basket/index.js`, and the Ordering service consumes from SQS via `SqsEventSource` in `lib/queue.ts`. |
| **Gap** | No dead-letter queue (DLQ) configured on the SQS queue for failed message handling. No EventBridge archive for event replay. |
| **Recommendation** | Add a dead-letter queue to `OrderQueue` for failed messages. Enable EventBridge archive on `SwnEventBus` for event replay capability. Consider adding EventBridge schema registry for event contract documentation. |
| **Evidence** | `lib/eventbus.ts` — `EventBus`, `Rule`, `SqsQueue` target; `lib/queue.ts` — `Queue`, `SqsEventSource`; `src/basket/eventBridgeClient.js` — `EventBridgeClient` |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC, subnets, security groups, or NACLs are defined in the CDK stack. Lambda functions run in the default AWS Lambda service VPC (no customer VPC configuration). API Gateway has no WAF association, no throttling configuration, and no network-level access controls. No `aws_vpc`, `aws_subnet`, or `aws_security_group` equivalent CDK constructs found. |
| **Gap** | Lambda functions accessing DynamoDB traverse the public AWS network rather than VPC endpoints. API Gateway endpoints are publicly accessible with no network restrictions. No WAF protection against common web exploits. |
| **Recommendation** | For a serverless architecture, configure VPC endpoints for DynamoDB to keep traffic within the AWS network. Add AWS WAF to API Gateway for protection against SQL injection, XSS, and rate-based attacks. Configure API Gateway throttling limits. Consider VPC Lambda configuration if the services need to access private resources in the future. |
| **Evidence** | `lib/aws-microservices-stack.ts` — no VPC constructs; `lib/apigateway.ts` — `LambdaRestApi` with no WAF, throttling, or network config |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Three separate API Gateway REST APIs (`LambdaRestApi`) serve as entry points in `lib/apigateway.ts`: Product Service (`/product`), Basket Service (`/basket`, `/basket/{userName}`, `/basket/checkout`), and Order Service (`/order`, `/order/{userName}`). API Gateway provides basic routing and Lambda proxy integration. |
| **Gap** | No authentication (no authorizers configured). No throttling or usage plans. No request validation. No WAF protection. Three separate API Gateway instances instead of a unified gateway with consolidated routing. `proxy: false` is set but no request/response models are defined for validation. |
| **Recommendation** | Consolidate to a single API Gateway with path-based routing to reduce management overhead. Add Cognito authorizer or Lambda authorizer for authentication. Configure usage plans and throttling limits. Add request models for input validation. Associate AWS WAF for web exploit protection. |
| **Evidence** | `lib/apigateway.ts` — three `LambdaRestApi` instances with `proxy: false` but no authorizers, throttling, or validation |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Lambda functions auto-scale by default (managed by AWS with up to 1000 concurrent executions per region). DynamoDB tables use `BillingMode.PAY_PER_REQUEST` (on-demand mode) which scales automatically. API Gateway scales automatically. SQS and EventBridge scale automatically. All compute and data tiers benefit from serverless auto-scaling. |
| **Gap** | No Lambda reserved concurrency or provisioned concurrency configured. No explicit concurrency limits to protect downstream services from traffic spikes. No SQS `maxReceiveCount` for retry limiting. |
| **Recommendation** | Configure Lambda reserved concurrency on each function to prevent one service's traffic from consuming the account-wide concurrency pool. Consider provisioned concurrency for latency-sensitive endpoints. Set `maxReceiveCount` on SQS queue with a DLQ for retry management. |
| **Evidence** | `lib/microservice.ts` — `NodejsFunction` with no concurrency settings; `lib/database.ts` — `BillingMode.PAY_PER_REQUEST`; `lib/queue.ts` — `Queue` with no DLQ or maxReceiveCount |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | All three DynamoDB tables are created with `RemovalPolicy.DESTROY` and no backup configuration. No Point-in-Time Recovery (PITR) enabled. No `aws_backup_plan` or equivalent CDK constructs. No S3 buckets with versioning (no S3 in the stack). Stack deletion would permanently destroy all data. |
| **Gap** | Complete absence of backup and recovery strategy. Production data loss risk on stack deletion. No ability to restore to any point in time. No documented restore procedures. |
| **Recommendation** | Enable DynamoDB Point-in-Time Recovery (PITR) on all three tables by adding `pointInTimeRecovery: true` in `lib/database.ts`. Change `RemovalPolicy.DESTROY` to `RemovalPolicy.RETAIN` for production. Consider adding AWS Backup plans for cross-region backup replication. |
| **Evidence** | `lib/database.ts` — `removalPolicy: RemovalPolicy.DESTROY` on all three tables; no `pointInTimeRecovery` setting; no backup resources |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | All services are fully serverless and inherently multi-AZ. AWS Lambda executes across multiple AZs automatically. DynamoDB replicates data across multiple AZs within a region. API Gateway, EventBridge, and SQS are all regional services with built-in multi-AZ availability. No single-AZ compute or data store configurations. |
| **Gap** | No multi-region configuration for disaster recovery (DR). Single-region deployment only. |
| **Recommendation** | For a P0 service, consider DynamoDB global tables for multi-region replication. Add cross-region backup replication for disaster recovery. |
| **Evidence** | `lib/microservice.ts` — Lambda (multi-AZ by default); `lib/database.ts` — DynamoDB (multi-AZ by default); `lib/apigateway.ts` — API Gateway (regional, multi-AZ) |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | 100% of infrastructure is defined in AWS CDK (TypeScript). The complete stack includes: 3 DynamoDB tables (`lib/database.ts`), 3 Lambda functions (`lib/microservice.ts`), 3 API Gateway REST APIs (`lib/apigateway.ts`), 1 EventBridge bus with rule (`lib/eventbus.ts`), 1 SQS queue with event source (`lib/queue.ts`). All resources are composed in `lib/aws-microservices-stack.ts` and deployed via `bin/aws-microservices.ts`. IAM permissions are granted using CDK grant methods (e.g., `grantReadWriteData`, `grantPutEventsTo`). |
| **Gap** | CDK version 2.17.0 is outdated (current CDK is 2.170+). The CDK code uses well-structured constructs but could benefit from Stack-level tags and environment-specific configuration. No CDK Pipelines construct for automated deployment. |
| **Recommendation** | Upgrade `aws-cdk-lib` from 2.17.0 to the latest version. Add CDK Pipelines for automated deployment (supports GitOps model). Consider migrating to Terraform (per preferences) for broader IaC ecosystem compatibility and GitOps tooling. Add `cdk.Tags.of(this).add()` for resource tagging. |
| **Evidence** | `lib/aws-microservices-stack.ts`, `lib/database.ts`, `lib/microservice.ts`, `lib/apigateway.ts`, `lib/eventbus.ts`, `lib/queue.ts`, `package.json` — `aws-cdk-lib: 2.17.0` |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CI/CD pipeline exists. No `.github/workflows/` directory, no `.gitlab-ci.yml`, no `Jenkinsfile`, no `buildspec.yml`, no CodePipeline resource in CDK. The README instructs developers to run `cdk deploy` manually from their workstation. The `package.json` defines `build` (tsc), `test` (jest), and `cdk` scripts but no deployment automation. |
| **Gap** | All deployments are manual. No automated build, test, or deploy pipeline. No deployment gates, no automated rollback, no environment promotion. This is the most impactful gap in the repository — it blocks all other operational improvements. |
| **Recommendation** | Implement CI/CD pipeline immediately. Option 1: CDK Pipelines (stays in CDK ecosystem, GitOps-friendly). Option 2: GitHub Actions with `cdk deploy` steps (align with GitOps preferences). Option 3: AWS CodePipeline + CodeBuild with `buildspec.yml`. Include stages: lint → build → unit test → cdk diff → approval → cdk deploy → integration test → canary promote. |
| **Evidence** | No CI/CD files found in repository; `README.md` — manual `cdk deploy` instructions; `package.json` — no deploy script |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | JavaScript (ES6 modules) is used for all Lambda handler source code (`src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js`, `src/*/ddbClient.js`). TypeScript is used for CDK infrastructure code (`lib/*.ts`, `bin/aws-microservices.ts`). Both are mature cloud-native languages with excellent AWS SDK v3 support. Dependencies use `@aws-sdk/client-dynamodb`, `@aws-sdk/client-eventbridge`, and `@aws-sdk/util-dynamodb` (AWS SDK v3 modular packages). |
| **Gap** | Lambda handlers are JavaScript, not TypeScript — no compile-time type safety for application logic. TypeScript version pinned at `~3.9.7` which is outdated. |
| **Recommendation** | Migrate Lambda handlers from JavaScript to TypeScript for type safety. Upgrade TypeScript from 3.9.7 to 5.x. Update `@aws-sdk` packages from ^3.55.0 to latest v3. |
| **Evidence** | `src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js` — JavaScript ES6; `tsconfig.json` — TypeScript config; `package.json` — `typescript: ~3.9.7` |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Three independently-scoped microservices with clear domain boundaries: Product (CRUD operations), Basket (cart management + checkout), Ordering (order creation + queries). Each service has its own Lambda function, DynamoDB table, `package.json`, and `ddbClient.js`. No shared database access — each service owns its data. Inter-service communication is event-driven via EventBridge/SQS (not synchronous HTTP). |
| **Gap** | All three services are deployed as a single CDK stack (`AwsMicroservicesStack`), creating a shared deployment lifecycle. A change to one service requires redeploying the entire stack. No independent deployment pipelines per service. This is a shared deployment coupling, not a data or logic coupling. |
| **Recommendation** | Split into three CDK stacks (one per service) with shared infrastructure (EventBridge bus) in a separate stack. This enables independent deployment lifecycles. Use CDK stack outputs and cross-stack references for shared resources. |
| **Evidence** | `lib/aws-microservices-stack.ts` — single stack; `src/product/`, `src/basket/`, `src/ordering/` — separate service directories; `lib/database.ts` — separate tables per service |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The checkout flow is fully asynchronous: Basket Lambda publishes a `CheckoutBasket` event to EventBridge → EventBridge rule routes to SQS `OrderQueue` → Ordering Lambda consumes from SQS. The Ordering Lambda handles both async invocations (SQS events via `sqsInvocation`, EventBridge events via `eventBridgeInvocation`) and sync invocations (API Gateway via `apiGatewayInvocation`). Product and Basket services handle sync API Gateway requests only (no inter-service HTTP calls). |
| **Gap** | No async patterns for product queries or basket operations. The checkout flow has a fire-and-forget pattern — the Basket service deletes the basket immediately after publishing the event without waiting for order confirmation (no status callback or polling). Clients have no way to check checkout status. |
| **Recommendation** | Add an order status endpoint that clients can poll after checkout (e.g., `GET /order/{userName}/status`). Consider adding a checkout status field to the basket or order table. For future inter-service queries, use EventBridge request-response pattern or Step Functions. |
| **Evidence** | `src/basket/index.js` — `publishCheckoutBasketEvent` + `deleteBasket`; `src/ordering/index.js` — `sqsInvocation` and `eventBridgeInvocation` handlers; `lib/eventbus.ts` — EventBridge → SQS routing |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | The checkout is the primary long-running operation and it is handled asynchronously. The Basket service publishes a `CheckoutBasket` event to EventBridge, which routes via SQS to the Ordering Lambda. All other operations (product CRUD, basket CRUD, order queries) are fast DynamoDB operations that complete well within Lambda timeout limits. No synchronous blocking calls for long-running operations. |
| **Gap** | No explicit timeout configuration on Lambda functions (defaults apply). No explicit status tracking for the async checkout flow — clients must query the Order service to determine if checkout completed. |
| **Recommendation** | Add explicit Lambda timeout configuration appropriate for each service. Implement checkout status tracking (e.g., a status field in the order record that transitions from "pending" to "confirmed"). |
| **Evidence** | `src/basket/index.js` — async checkout via EventBridge; `src/ordering/index.js` — SQS event processing; `lib/microservice.ts` — no explicit timeout config |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API versioning strategy. API Gateway routes are defined as `/product`, `/product/{id}`, `/basket`, `/basket/{userName}`, `/basket/checkout`, `/order`, `/order/{userName}` — no version prefix (e.g., `/v1/product`). No `Accept-Version` headers. No changelog or API evolution documentation. |
| **Gap** | Any breaking API change will affect all consumers immediately with no migration path. No backward compatibility guarantees. No mechanism for API deprecation. |
| **Recommendation** | Add API versioning using URL path prefix (e.g., `/v1/product`, `/v1/basket`, `/v1/order`). Define this in `lib/apigateway.ts` by adding a version resource before service resources. Alternatively, use API Gateway stage variables for version management. Create OpenAPI specs for each API version. |
| **Evidence** | `lib/apigateway.ts` — routes defined without version prefix: `addResource('product')`, `addResource('basket')`, `addResource('order')` |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Services communicate via EventBridge events — no direct HTTP calls between services. The Basket service uses environment variables for EventBridge configuration: `EVENT_SOURCE`, `EVENT_DETAILTYPE`, `EVENT_BUSNAME` (set in `lib/microservice.ts`). DynamoDB table names are passed via `DYNAMODB_TABLE_NAME` environment variable. Services do not hard-code each other's endpoints — the event-driven architecture avoids the need for service-to-service endpoint discovery. |
| **Gap** | Environment variables for EventBridge configuration contain hard-coded string values (e.g., `EVENT_BUSNAME: "SwnEventBus"`) rather than dynamic references. API Gateway endpoints per service are separate and not discoverable through a service registry or API catalog. |
| **Recommendation** | Use CDK cross-stack references or SSM Parameter Store for service configuration instead of hard-coded environment variable values. Consider adding an API catalog (e.g., API Gateway export or Backstage service catalog) for endpoint documentation. |
| **Evidence** | `lib/microservice.ts` — environment variables: `EVENT_BUSNAME: "SwnEventBus"`, `DYNAMODB_TABLE_NAME: basketTable.tableName`; `src/basket/index.js` — `process.env.EVENT_BUSNAME` |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No unstructured data storage capability detected. No S3 buckets defined in CDK. No file upload handlers in Lambda functions. No document processing (no Textract, no PDF parsing). The application exclusively uses DynamoDB for structured data (product catalog, baskets, orders). |
| **Gap** | No capability to store or process unstructured data (documents, images, files). Product items reference `imageFile` in the schema comments (`lib/database.ts`), but there is no S3 bucket or image storage infrastructure. |
| **Recommendation** | If product images or documents are needed, create an S3 bucket with CloudFront distribution for image serving. Add pre-signed URL generation in the Product Lambda for secure uploads. Consider Amazon Textract if document processing is needed for returns/invoices. |
| **Evidence** | `lib/database.ts` — schema comment mentions `imageFile` field but no S3 bucket; no S3 constructs in any CDK file |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Each microservice has a dedicated `ddbClient.js` module that creates a DynamoDB client (`src/product/ddbClient.js`, `src/basket/ddbClient.js`, `src/ordering/ddbClient.js`). Each service imports its client and uses DynamoDB SDK v3 commands directly in the handler (e.g., `GetItemCommand`, `PutItemCommand`, `ScanCommand`). The pattern is consistent across services — dedicated client module + direct SDK usage in handler with `marshall`/`unmarshall` utilities. |
| **Gap** | No abstraction layer or repository pattern. DynamoDB commands are constructed directly in handler functions, mixing business logic with data access concerns. Each handler builds `params` objects with `TableName`, `Key`, and expression attributes inline. Duplicate patterns exist across services (e.g., scan-all-items pattern appears in all three services). |
| **Recommendation** | Extract a repository/DAO layer per service (e.g., `productRepository.js`, `basketRepository.js`, `orderRepository.js`) that encapsulates DynamoDB operations. This improves testability, reduces duplication, and creates a cleaner separation of concerns. |
| **Evidence** | `src/product/ddbClient.js`, `src/basket/ddbClient.js`, `src/ordering/ddbClient.js` — identical DynamoDB client pattern; `src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js` — inline DynamoDB command construction |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | All databases are Amazon DynamoDB — a fully managed, serverless database service with no engine version to manage. DynamoDB does not have version pinning, EOL dates, or engine upgrade cycles. AWS manages all underlying infrastructure, patching, and feature updates transparently. |
| **Gap** | None. DynamoDB's serverless model eliminates engine version lifecycle management concerns entirely. |
| **Recommendation** | No action needed for DynamoDB engine versioning. Continue using DynamoDB on-demand mode for cost efficiency at current scale. |
| **Evidence** | `lib/database.ts` — DynamoDB `Table` construct with no engine version parameter (not applicable for DynamoDB) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL constructs. All business logic resides in the Lambda application layer (JavaScript handler functions). DynamoDB is a NoSQL database — it does not support stored procedures, triggers, or SQL. Data access uses DynamoDB API operations (`GetItem`, `PutItem`, `Scan`, `Query`, `UpdateItem`, `DeleteItem`) via AWS SDK v3. No `.sql` files found in the repository. |
| **Gap** | None. The application architecture cleanly separates business logic (Lambda) from data storage (DynamoDB). |
| **Recommendation** | No action needed. Continue keeping business logic in the application layer. |
| **Evidence** | `src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js` — all business logic in Lambda handlers; no `.sql` files in repository |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CloudTrail configuration in any CDK file. No `aws_cloudtrail` or equivalent CDK construct. No log file validation, no immutable log storage (S3 Object Lock), no CloudWatch log retention policies defined. Lambda functions produce CloudWatch Logs by default, but there is no structured audit logging or centralized log management. |
| **Gap** | No ability to audit API Gateway requests, Lambda invocations, DynamoDB operations, or EventBridge events at the infrastructure level. No immutable log trail for compliance or incident investigation. |
| **Recommendation** | Add CloudTrail with S3 log storage and log file validation enabled. Enable DynamoDB Streams for data change audit logging. Configure CloudWatch Logs retention policies for Lambda function logs (currently unlimited retention = unnecessary cost). Consider CloudWatch Logs Insights for log analysis. |
| **Evidence** | No CloudTrail resources in `lib/aws-microservices-stack.ts` or any CDK file; no logging configuration in any construct |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | DynamoDB tables in `lib/database.ts` do not specify an `encryption` property. By default, DynamoDB encrypts all data at rest using AWS-owned keys (no additional configuration needed). This provides encryption at rest but with AWS-managed keys, not customer-managed KMS keys. No explicit `aws_kms_key` resources defined in CDK. SQS queue in `lib/queue.ts` does not specify encryption. |
| **Gap** | Using AWS-owned keys rather than customer-managed KMS keys. No control over key rotation policies, key access policies, or audit trails. SQS queue messages are not encrypted at rest. No explicit encryption configuration on any resource. |
| **Recommendation** | Create customer-managed KMS keys and apply them to DynamoDB tables (`encryption: TableEncryption.CUSTOMER_MANAGED`) and SQS queue (`encryptionMasterKey`). This provides key rotation control, access policies, and CloudTrail key usage audit trails. |
| **Evidence** | `lib/database.ts` — no `encryption` property on Table constructs; `lib/queue.ts` — no encryption on Queue; no `aws_kms_key` in any CDK file |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No authentication configured on any of the three API Gateway REST APIs. No Cognito authorizers, no Lambda authorizers, no API key requirements, no IAM authorization. All methods (`GET`, `POST`, `PUT`, `DELETE`) are publicly accessible. The `addMethod()` calls in `lib/apigateway.ts` do not specify any `authorizationType` or `authorizer` options. |
| **Gap** | Critical security vulnerability — all CRUD endpoints are publicly accessible. Anyone can create, read, update, and delete products, baskets, and orders. The checkout endpoint (`POST /basket/checkout`) is also unauthenticated. Error responses in Lambda handlers expose stack traces (`errorStack: e.stack`) which leaks implementation details. |
| **Recommendation** | Implement Amazon Cognito User Pool with API Gateway authorizer for user authentication. Add `authorizationType: AuthorizationType.COGNITO` to all API methods. Remove error stack traces from production error responses. Consider API key requirements for partner/service-to-service access. |
| **Evidence** | `lib/apigateway.ts` — `addMethod('GET')`, `addMethod('POST')`, etc. with no authorization parameters; `src/product/index.js` — `errorStack: e.stack` in error responses |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No identity provider integration. No Amazon Cognito User Pool, no OIDC/SAML configuration, no SSO setup. The application uses `userName` as a plain string parameter (e.g., `GET /basket/{userName}`, `GET /order/{userName}`) with no identity verification — any caller can query any user's basket or orders by guessing usernames. |
| **Gap** | No centralized identity management. No user authentication or identity verification. The `userName` parameter in basket and order operations is not tied to an authenticated identity — it is a freeform string passed in the URL path. |
| **Recommendation** | Implement Amazon Cognito User Pool for user identity management. Map `userName` to authenticated Cognito identity (e.g., `event.requestContext.authorizer.claims.sub`). Enforce that users can only access their own baskets and orders by validating the authenticated identity against the `userName` parameter. |
| **Evidence** | No Cognito resources in any CDK file; `lib/apigateway.ts` — `{userName}` path parameter with no identity binding; `src/basket/index.js` — `event.pathParameters.userName` used without auth validation |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | No hardcoded secrets detected in source code. Lambda functions use environment variables for non-sensitive configuration: `DYNAMODB_TABLE_NAME`, `PRIMARY_KEY`, `SORT_KEY`, `EVENT_SOURCE`, `EVENT_DETAILTYPE`, `EVENT_BUSNAME`. DynamoDB access uses IAM roles (CDK `grantReadWriteData`) — no database credentials needed. EventBridge access uses IAM roles (`grantPutEventsTo`). |
| **Gap** | While no secrets are currently needed (IAM-based authentication for all AWS services), there is no Secrets Manager or Vault infrastructure for future secrets needs (e.g., third-party API keys for payment processing, email service credentials). No secrets rotation capability. |
| **Recommendation** | When external service credentials are needed (payment gateways, email providers), use AWS Secrets Manager with automatic rotation. Define Secrets Manager resources in CDK proactively. Lambda functions can retrieve secrets via the Secrets Manager SDK or Lambda layer. |
| **Evidence** | `lib/microservice.ts` — environment variables contain non-sensitive config only; `src/product/ddbClient.js` — `new DynamoDBClient()` uses IAM credentials; no hardcoded secrets in any source file |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Lambda runtime `NODEJS_14_X` is specified in `lib/microservice.ts` for all three functions. Node.js 14.x reached end-of-life in April 2023. AWS Lambda deprecated the Node.js 14 runtime, meaning it no longer receives security patches. No vulnerability scanning configured (no AWS Inspector, no Snyk integration). Lambda manages the runtime environment, but the selected runtime is past EOL. |
| **Gap** | All three Lambda functions run on an EOL runtime with no security patches. No vulnerability scanning for Lambda function code or dependencies. No hardened runtime configuration. AWS SDK v3 dependencies (`^3.55.0`) are significantly outdated (current is 3.700+). |
| **Recommendation** | Immediately upgrade Lambda runtime from `NODEJS_14_X` to `NODEJS_20_X` or `NODEJS_22_X` in `lib/microservice.ts`. Update `@aws-sdk` dependencies to latest v3 in all three service `package.json` files. Enable AWS Inspector for Lambda function vulnerability scanning. Run `npm audit` regularly on all service packages. |
| **Evidence** | `lib/microservice.ts` — `runtime: Runtime.NODEJS_14_X` on all three functions; `src/product/package.json` — `@aws-sdk/client-dynamodb: ^3.55.0`; `src/basket/package.json` — `@aws-sdk/client-eventbridge: ^3.58.0` |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CI/CD pipeline exists, therefore no security scanning is integrated into any pipeline. No SAST tools (no SonarQube, Semgrep, CodeGuru). No dependency scanning (no Dependabot configuration, no `.snyk` file, no `npm audit` in any script). No container scanning (no containers to scan). No CDK-nag for IaC security validation. |
| **Gap** | Complete absence of automated security scanning. Vulnerabilities in dependencies or application code reach production undetected. No security gates in any workflow. |
| **Recommendation** | Implement security scanning as part of the CI/CD pipeline (see INF-Q11). Add `npm audit` step in build pipeline. Add CDK-nag (`cdk-nag`) as a CDK aspect for IaC security compliance. Configure Dependabot or Renovate for automated dependency updates. Consider Semgrep for SAST scanning of Lambda handler code. |
| **Evidence** | No CI/CD files in repository; no `.snyk`, no `.dependabot/`, no security scanning configuration; `package.json` — no security-related scripts |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No distributed tracing instrumentation. No X-Ray SDK, no OpenTelemetry SDK, no tracing libraries in any `package.json`. Lambda functions use only `console.log` for logging. No trace ID propagation between services. The EventBridge → SQS → Lambda flow has no correlation ID to trace a checkout request from the Basket service through to the Ordering service. |
| **Gap** | No ability to trace requests across service boundaries. Debugging the checkout flow (Basket → EventBridge → SQS → Ordering) requires manually correlating CloudWatch Logs from multiple Lambda functions with no shared trace ID. |
| **Recommendation** | Enable AWS X-Ray tracing on Lambda functions (`tracing: Tracing.ACTIVE` in CDK). Add `@aws-sdk/client-xray` or use the Lambda X-Ray active tracing feature. Alternatively, adopt OpenTelemetry with the AWS Lambda OpenTelemetry layer for vendor-neutral instrumentation. Propagate a correlation ID through the EventBridge event detail for end-to-end tracing. |
| **Evidence** | `src/product/package.json`, `src/basket/package.json`, `src/ordering/package.json` — no tracing SDK dependencies; `lib/microservice.ts` — no `tracing` property on Lambda functions |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions found. No CloudWatch alarms, no error rate thresholds, no latency percentile targets, no error budget tracking. No SLO configuration files or dashboards. For a P0 service, this is a critical gap — there is no way to measure whether the service is meeting user expectations. |
| **Gap** | No formal service level objectives. No measurement of availability, latency, or error rate targets. No error budget to guide operational investment decisions. |
| **Recommendation** | Define SLOs for each service: e.g., Product API p99 latency < 200ms, Order API availability > 99.9%, Checkout success rate > 99.5%. Create CloudWatch alarms for SLO indicators. Implement error budget tracking. Use CloudWatch Application Signals or create custom SLO dashboards. |
| **Evidence** | No CloudWatch alarm resources in any CDK file; no SLO definition files in repository |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metrics published. Lambda functions use `console.log` for operational logging but do not emit CloudWatch custom metrics. No `putMetricData` calls. No tracking of business outcomes such as: orders created per minute, checkout success/failure rate, basket abandonment rate, total order value. Only default Lambda metrics (invocations, duration, errors) are available. |
| **Gap** | No business outcome visibility. Cannot measure whether the e-commerce platform is delivering value. Default infrastructure metrics (CPU, memory, invocations) indicate system health but not business health. |
| **Recommendation** | Add CloudWatch custom metrics for key business events: `OrderCreated`, `CheckoutInitiated`, `CheckoutFailed`, `BasketAbandoned`, `TotalOrderValue`. Use CloudWatch Embedded Metric Format (EMF) in Lambda for zero-overhead metric publishing. Create a business dashboard showing order volume, revenue, and error rates. |
| **Evidence** | `src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js` — only `console.log` and `console.error` statements; no `putMetricData` or EMF format logging |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No alerting configured. No CloudWatch alarms, no anomaly detection, no composite alarms. No PagerDuty, OpsGenie, or SNS notification integration. No error rate or latency thresholds defined. A failed deployment, Lambda error spike, or SQS DLQ growth would go unnoticed. |
| **Gap** | Complete absence of alerting. Production issues are only discoverable through manual log inspection. No proactive notification for error spikes, latency degradation, or checkout failures. |
| **Recommendation** | Create CloudWatch alarms for: Lambda error rate > 1%, Lambda p99 duration > 5s, SQS `ApproximateNumberOfMessagesVisible` > 100 (queue backup), DynamoDB throttled requests > 0. Add SNS topic for alarm notifications. Consider CloudWatch anomaly detection for baseline-adaptive alerting on key metrics. |
| **Evidence** | No CloudWatch alarm resources in any CDK file; no SNS topics; no alerting configuration |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No deployment strategy configured. The only deployment method is manual `cdk deploy` from a developer workstation (documented in `README.md`: "run below command: `cdk deploy`"). No blue/green, canary, or rolling deployments. No Lambda aliases with traffic shifting. No CodeDeploy configuration. No feature flags. A deployment updates all three services simultaneously with no staged rollout. |
| **Gap** | All-or-nothing production deployments with no safety net. A bad deployment affects all services simultaneously. No automated rollback capability. No canary to detect regressions before full traffic cutover. |
| **Recommendation** | Implement Lambda alias-based canary deployments using AWS CodeDeploy. Configure `LambdaDeploymentGroup` with `Linear10PercentEvery1Minute` or `Canary10Percent5Minutes` traffic shifting. Add pre/post deployment hooks for automated validation. Use CloudWatch alarms as automatic rollback triggers. |
| **Evidence** | `README.md` — "run below command: `cdk deploy`"; no CodeDeploy resources in CDK; no deployment configuration files |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | The test file `test/aws-microservices.test.ts` has all test code commented out. The only active test is an empty placeholder: `test('SQS Queue Created', () => {})`. Jest is configured (`jest.config.js`, `ts-jest`) but no tests execute. No integration tests, no API contract tests, no end-to-end tests. No test scripts that validate deployed endpoints. |
| **Gap** | Zero automated test coverage. No regression detection capability. Changes to Lambda handlers, DynamoDB access patterns, or EventBridge event schemas cannot be validated automatically. The commented-out test was a CDK assertion test for SQS queue properties — even infrastructure validation is not active. |
| **Recommendation** | Implement three layers of testing: 1) CDK assertion tests (uncomment and expand `test/aws-microservices.test.ts`) to validate infrastructure. 2) Unit tests for Lambda handler business logic (e.g., `prepareOrderPayload`, `checkoutBasket` logic). 3) Integration tests that invoke deployed API Gateway endpoints and validate responses. Use EventBridge test events (`src/basket/checkoutbasketevents.json` provides sample events). |
| **Evidence** | `test/aws-microservices.test.ts` — all tests commented out; `jest.config.js` — jest configured but no tests pass; `src/basket/checkoutbasketevents.json` — sample events available but not used in tests |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No incident response automation. No runbooks (markdown, YAML, or JSON). No SSM Automation documents. No self-healing patterns. No Lambda-based remediation functions. No Step Functions for incident workflows. No on-call integration (PagerDuty, OpsGenie). |
| **Gap** | All incident response is ad hoc. When production issues occur, there is no documented procedure, no automated remediation, and no escalation path. For a P0 service, this is a significant operational risk. |
| **Recommendation** | Create operational runbooks for common scenarios: Lambda throttling, DynamoDB throttling, SQS queue backup, API Gateway 5xx spike. Implement SSM Automation documents for common remediations. Define incident escalation procedures. Consider adding a DLQ consumer Lambda that automatically retries or alerts on failed orders. |
| **Evidence** | No runbook files in repository; no SSM resources in CDK; no incident response documentation |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No observability ownership defined. No CODEOWNERS file. No per-service dashboards. No alarm ownership attribution. No team tags on any resources. No SLO definitions with team ownership. The repository has a single author (per README) with no team structure indicated. |
| **Gap** | No clear ownership of monitoring, alerting, or incident response. No team attribution for observability assets. When alarms fire (once they exist), there is no defined owner to respond. |
| **Recommendation** | Create a CODEOWNERS file mapping service directories to team members. Define observability ownership per service. Create per-service CloudWatch dashboards (Product, Basket, Ordering). Add owner tags to resources. Establish on-call rotation for P0 service ownership. |
| **Evidence** | No CODEOWNERS file; no dashboard definitions; no team tags on any resource |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No resource tags defined on any CDK construct. No `cdk.Tags.of(this).add()` calls. No `default_tags` equivalent. No tag enforcement. DynamoDB tables, Lambda functions, API Gateway, EventBridge bus, and SQS queue are all untagged. No cost allocation tags, no environment tags, no ownership tags. |
| **Gap** | No ability to track costs per service, identify resource ownership during incidents, or enforce budget controls. Resources are not identifiable by environment (dev/staging/prod), service, team, or cost center. |
| **Recommendation** | Add resource tags using CDK's `cdk.Tags.of(this).add()` at the stack level. Define standard tags: `Environment`, `Service`, `Team`, `CostCenter`, `Priority`. Apply tags in `lib/aws-microservices-stack.ts` constructor. Consider AWS Config rules for tag enforcement (`required-tags`). |
| **Evidence** | `lib/aws-microservices-stack.ts` — no tag definitions; `lib/database.ts`, `lib/microservice.ts`, `lib/queue.ts`, `lib/eventbus.ts`, `lib/apigateway.ts` — no tags on any construct |

---

## Learning Materials

### Move to Modern DevOps (Triggered)

- [Move to Modern DevOps — AWS SkillBuilder Learning Plan](https://skillbuilder.aws/learning-plan/1FGEQKGPQD)
- [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ)
- [AWS CDK Pipelines Documentation](https://docs.aws.amazon.com/cdk/v2/guide/cdk_pipeline.html)
- [GitOps on AWS — EKS Workshop](https://www.eksworkshop.com/docs/automation/gitops/) (applicable patterns for CDK/Terraform GitOps)

### Move to AI (Triggered)

- [Move to AI — AWS SkillBuilder Learning Plan](https://skillbuilder.aws/learning-plan/VDFEE4ACCV)
- [Amazon Bedrock Getting Started](https://skillbuilder.aws/learn/63KTRM86DQ)
- [Introduction to Agentic AI on AWS](https://skillbuilder.aws/learn/DNBD5MT8ZD)
- [Building with Amazon Bedrock Agents](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)
- [Amazon Bedrock AgentCore Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore.html)

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `lib/aws-microservices-stack.ts` | INF-Q5, INF-Q10, OPS-Q9 | Main CDK stack composing all constructs; no VPC, no tags |
| `lib/database.ts` | INF-Q2, INF-Q8, INF-Q9, DATA-Q1, DATA-Q2, DATA-Q3, DATA-Q4 | DynamoDB table definitions (product, basket, order); RemovalPolicy.DESTROY; PAY_PER_REQUEST; no PITR |
| `lib/microservice.ts` | INF-Q1, INF-Q7, APP-Q2, APP-Q6, SEC-Q6, OPS-Q1 | Lambda function definitions; Runtime.NODEJS_14_X; environment variables; no concurrency config; no tracing |
| `lib/apigateway.ts` | INF-Q5, INF-Q6, APP-Q5, SEC-Q3, SEC-Q4 | Three API Gateway REST APIs; no auth, no throttling, no versioning, no WAF |
| `lib/eventbus.ts` | INF-Q3, INF-Q4, APP-Q3, APP-Q6 | EventBridge bus + CheckoutBasketRule; SQS target; no DLQ; no archive |
| `lib/queue.ts` | INF-Q4, INF-Q7 | SQS OrderQueue; visibilityTimeout 30s; batchSize 1; no DLQ; no encryption |
| `bin/aws-microservices.ts` | INF-Q10 | CDK app entry point; no environment-specific configuration |
| `src/product/index.js` | APP-Q1, APP-Q3, DATA-Q2, DATA-Q4, SEC-Q3, OPS-Q3 | Product Lambda handler; CRUD operations; inline DynamoDB commands; error stack exposure |
| `src/product/ddbClient.js` | DATA-Q2 | Product DynamoDB client module |
| `src/product/package.json` | APP-Q1, SEC-Q6, OPS-Q1 | @aws-sdk/client-dynamodb ^3.55.0; no tracing SDK |
| `src/basket/index.js` | APP-Q3, APP-Q4, INF-Q3, DATA-Q2, DATA-Q4, OPS-Q3 | Basket Lambda handler; checkout flow; EventBridge publish; async pattern |
| `src/basket/ddbClient.js` | DATA-Q2 | Basket DynamoDB client module |
| `src/basket/eventBridgeClient.js` | INF-Q4, APP-Q3 | EventBridge client for checkout event publishing |
| `src/basket/package.json` | APP-Q1, SEC-Q6 | @aws-sdk/client-eventbridge ^3.58.0 |
| `src/basket/checkoutbasketevents.json` | OPS-Q6 | Sample EventBridge events for testing (not used in automated tests) |
| `src/ordering/index.js` | APP-Q3, APP-Q4, DATA-Q2, DATA-Q4, OPS-Q3 | Ordering Lambda handler; SQS + EventBridge + API Gateway invocation patterns |
| `src/ordering/ddbClient.js` | DATA-Q2 | Ordering DynamoDB client module |
| `src/ordering/package.json` | APP-Q1, SEC-Q6 | @aws-sdk/client-dynamodb ^3.58.0 |
| `test/aws-microservices.test.ts` | OPS-Q6 | Test file with all tests commented out; empty placeholder test only |
| `jest.config.js` | OPS-Q6 | Jest configuration; test runner configured but no tests execute |
| `package.json` | INF-Q10, INF-Q11, APP-Q1 | Root package.json; aws-cdk-lib 2.17.0; typescript ~3.9.7; no deploy script |
| `README.md` | INF-Q11, OPS-Q5 | Manual `cdk deploy` instructions; architecture documentation |
| `cdk.json` | INF-Q10 | CDK configuration; feature flags; app entry point |
| `tsconfig.json` | APP-Q1 | TypeScript compiler configuration; ES2018 target |





