# Agentic Readiness Assessment Report
**Target**: ./services/aws-microservices
**Date**: 2026-03-05
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment

---

## Table of Contents

1. Executive Summary
2. Top Priorities (Critical Gaps)
3. Readiness Roadmap
   - Phase 1 — Quick Wins (Days 1–30)
   - Phase 2 — Foundation (Months 1–3)
   - Phase 3 — Agent Enablement (Months 3–6)
4. Recommended Self-Paced Learning Materials
5. Detailed Findings
   - Infrastructure & Platform
   - Application Architecture
   - Data Foundations
   - Identity, Security & Governance
   - Operations & Observability
6. Appendix: Evidence Index

---

## Executive Summary

This serverless microservices application has a solid architectural foundation — 100% Lambda compute, fully managed DynamoDB databases, event-driven communication via EventBridge and SQS, and complete infrastructure-as-code via CDK. However, it is not yet ready for agentic workloads. Critical gaps in API authentication (all endpoints are publicly accessible), zero observability infrastructure (no tracing, structured logging, or alerting), no CI/CD pipeline, no API documentation (OpenAPI specs), and absent resilience patterns (no idempotency, retries, or circuit breakers) must be addressed before introducing autonomous agent behavior. The strongest area is the microservices architecture itself; the weakest is operations and observability, which scored the minimum possible.

### Overall Score: 1.8 / 4.0

| Category | Score | Status |
|----------|-------|--------|
| Infrastructure & Platform | 2.5 / 4.0 | 🟡 |
| Application Architecture | 1.8 / 4.0 | 🟠 |
| Data Foundations | 2.1 / 4.0 | 🟠 |
| Identity, Security & Governance | 1.4 / 4.0 | ❌ |
| Operations & Observability | 1.0 / 4.0 | ❌ |

---

## Top Priorities (Critical Gaps)

### 1. No API Authentication — All Endpoints Publicly Accessible (SEC-Q9, SEC-Q10)
**What**: All three API Gateway REST APIs (`productApi`, `basketApi`, `orderApi` in `lib/apigateway.ts`) have zero authentication. No authorizers, no Cognito, no API keys. Any internet user can create, read, update, and delete products, baskets, and orders.
**Why it matters for agents**: Agentic systems make autonomous API calls at machine speed. Without authentication, an agent cannot be scoped to a user identity, and any malicious actor can exploit the same endpoints. Agent actions must be attributable to authenticated identities for audit, rate limiting, and access control.
**First step**: Add a Cognito User Pool and attach a `CognitoUserPoolsAuthorizer` to all API Gateway methods in `lib/apigateway.ts`. This provides JWT-based authentication with minimal code changes.

### 2. No CI/CD Pipeline — Manual Deployments Only (INF-Q6)
**What**: No `.github/workflows/`, `buildspec.yml`, `Jenkinsfile`, or CodePipeline definitions exist anywhere in the repository. Deployments are manual `cdk deploy` commands.
**Why it matters for agents**: Agentic systems require rapid, safe, repeatable deployments. Prompt changes, model updates, and guardrail configurations must be deployed through automated pipelines with testing gates. Manual deployments are error-prone and cannot support the iteration speed that agent development demands.
**First step**: Create a GitHub Actions workflow (`.github/workflows/deploy.yml`) with `cdk synth`, `cdk diff`, and `cdk deploy` stages, plus a test step to run CDK snapshot tests.

### 3. No Observability Stack — No Tracing, Structured Logging, or Alerting (OPS-Q1, OPS-Q2, OPS-Q4, OPS-Q8)
**What**: All 12 Operations & Observability criteria scored 1/4. Lambda functions use `console.log` with no structured format, no correlation IDs, no X-Ray tracing, no CloudWatch alarms, and no dashboards.
**Why it matters for agents**: Agentic workflows span multiple services — an agent calling the Product API, then Basket API, then triggering checkout is a distributed trace. Without end-to-end tracing and structured logging with correlation IDs, debugging agent failures is impossible. Without alerting, a malfunctioning agent can silently degrade or cause harm at machine speed.
**First step**: Enable X-Ray tracing on all Lambda functions by adding `tracing: lambda.Tracing.ACTIVE` in `lib/microservice.ts`, and replace `console.log` with a structured JSON logger (e.g., `@aws-lambda-powertools/logger`).

### 4. No API Documentation — No OpenAPI Specs for Agent Tool Integration (APP-Q2)
**What**: No `openapi.yaml`, `swagger.json`, or API specification files exist. API routes are defined only in `lib/apigateway.ts` CDK code with no exported documentation.
**Why it matters for agents**: Agents need machine-readable API descriptions to understand what tools are available, what parameters they accept, and what responses to expect. OpenAPI specs are the standard input for agent tool definitions. Without them, agents cannot discover or correctly invoke these APIs.
**First step**: Generate OpenAPI specs from the existing API Gateway definitions. Export the deployed API spec using `aws apigateway get-export`, or manually create `openapi.yaml` files that document all endpoints, request/response schemas, and error codes.

### 5. No Resilience Patterns — No Idempotency, Retries, or Circuit Breakers (APP-Q7, APP-Q9)
**What**: No idempotency keys on write operations (`PutItemCommand` in all handlers uses no condition expressions). No retry logic beyond AWS SDK defaults. No circuit breakers or timeout configurations. Error handling is a generic try/catch returning HTTP 500 with stack traces.
**Why it matters for agents**: Agents retry failed operations autonomously. Without idempotency, a retried `POST /basket/checkout` could process the same order multiple times. Without circuit breakers, an agent hitting a degraded downstream service will keep retrying and amplify the failure. Resilience patterns are the safety net that prevents autonomous agents from causing cascading damage.
**First step**: Add idempotency to the checkout flow using `@aws-lambda-powertools/idempotency` with DynamoDB as the persistence layer. Add condition expressions to `PutItemCommand` calls to prevent duplicate writes.

---

## Readiness Roadmap

This application is already a microservices architecture (APP-Q4 score: 4) with clear service boundaries, so no decomposition strategy is needed. The roadmap focuses on hardening the existing architecture for agentic workloads.

### Phase 1 — Quick Wins (Days 1–30)

1. **Upgrade Lambda runtime from NODEJS_14_X to NODEJS_20_X** — Node.js 14 is EOL and no longer receives security patches. Update the `runtime` property in all three function definitions in `lib/microservice.ts`. This is a one-line change per function. Also update the CDK version from 2.17.0 to the latest 2.x in `package.json`.
2. **Add API Gateway authentication** — Create a Cognito User Pool in CDK and attach a `CognitoUserPoolsAuthorizer` to all API methods in `lib/apigateway.ts`. This immediately secures all endpoints.
3. **Add API Gateway throttling** — Configure `deployOptions` with `throttlingRateLimit` and `throttlingBurstLimit` on each `LambdaRestApi` in `lib/apigateway.ts`. Add a usage plan with per-client quotas.
4. **Implement structured logging** — Replace `console.log`/`console.error` in all Lambda handlers (`src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js`) with `@aws-lambda-powertools/logger`. Configure JSON output with correlation IDs.
5. **Remove stack traces from error responses** — All three Lambda handlers return `errorStack: e.stack` in HTTP 500 responses. Remove this to prevent information leakage. Log the stack trace server-side only.

### Phase 2 — Foundation (Months 1–3)

1. **Set up CI/CD pipeline** — Create a GitHub Actions workflow or AWS CodePipeline with stages for lint, test, `cdk synth`, `cdk diff`, and `cdk deploy`. Re-enable and expand the commented-out tests in `test/aws-microservices.test.ts`.
2. **Enable distributed tracing** — Add `tracing: lambda.Tracing.ACTIVE` to all Lambda functions in `lib/microservice.ts`. Instrument the AWS SDK v3 clients with X-Ray to trace DynamoDB and EventBridge calls end-to-end.
3. **Create OpenAPI specifications** — Document all three APIs (Product, Basket, Order) with complete OpenAPI 3.0 specs. Include request/response schemas, error codes, and example payloads. These become the foundation for agent tool definitions.
4. **Implement idempotency on write operations** — Add `@aws-lambda-powertools/idempotency` to the checkout flow in `src/basket/index.js` and product creation in `src/product/index.js`. Use DynamoDB condition expressions to prevent duplicate writes.
5. **Add CloudWatch alarms and SLOs** — Define alarms for Lambda error rates, API Gateway 5xx rates, and p99 latency in CDK. Establish SLO targets for each API (e.g., 99.9% availability, < 500ms p99 latency).
6. **Configure CloudWatch log retention** — Add explicit log group definitions with retention policies (e.g., 30 days) for all Lambda functions to control costs and comply with data retention requirements.
7. **Add integration tests** — Write integration tests using the CDK assertion library and API test suites for critical flows (product CRUD, basket checkout, order query). Run in CI pipeline.

### Phase 3 — Agent Enablement (Months 3–6)

1. **Implement workflow orchestration with Step Functions** — Replace the hardcoded checkout sequence in `src/basket/index.js` (getBasket → preparePayload → publishEvent → deleteBasket) with an AWS Step Functions state machine. This provides built-in retry, error handling, timeout, and human approval capabilities.
2. **Add vector database for RAG** — Deploy Amazon OpenSearch Service with k-NN plugin or use Amazon Bedrock Knowledge Bases to enable semantic search over product catalog data. This enables agents to find products by natural language description.
3. **Implement AI/agent integration** — Add Amazon Bedrock integration with Strands Agents SDK or LangChain. Define agent tools based on the OpenAPI specs created in Phase 2. Implement an agent that can query products, manage baskets, and initiate checkout.
4. **Set up automated eval framework** — Create golden test datasets for agent behavior (e.g., "add iPhone to cart" should call Product API then Basket API). Implement scoring scripts to measure agent accuracy, latency, and cost per request.
5. **Add human approval for high-risk operations** — Use Step Functions `waitForTaskToken` pattern to gate destructive operations (bulk deletes, large orders) with human approval via SNS notifications or a simple approval UI.
6. **Implement deployment safety** — Configure Lambda traffic shifting with CodeDeploy for canary deployments. Add rollback triggers based on CloudWatch alarm thresholds. Implement feature flags for gradual agent feature rollout.

---

## Recommended Self-Paced Learning Materials

**Module 2: Move to Cloud Native (Containers and Serverless):**
- Cloud Design Patterns, Architectures, and Implementations — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html
  - Essential reference for resilience patterns (Circuit Breaker, Retry with Backoff), event-driven patterns (Event Sourcing, Saga), and API design patterns relevant to hardening this serverless architecture
- AWS Modernization Pathways: Move to Cloud Native Serverless — https://skillbuilder.aws/learning-plan/CMK2J48MVN/aws-modernization-pathways-move-to-cloud-native-serverless-includes-labs/EFUPP53B4Q
- Lambda Foundations — https://skillbuilder.aws/learn/XHRS91KKK6/aws-lambda-foundations/R85JRN3APC
- Architecting Serverless Applications — https://skillbuilder.aws/learn/MRWENY7FSX/architecting-serverless-applications/QVFY2JHVEH
- Amazon API Gateway for Serverless Applications — https://skillbuilder.aws/learn/GQA6FHWPJD/amazon-api-gateway-for-serverless-applications/JVRZ3PSW4H
  - Directly relevant to addressing gaps in API authentication, throttling, and request validation (INF-Q7, SEC-Q5, SEC-Q9)
- Deploying Serverless Applications — https://skillbuilder.aws/learn/M531VCW415/deploying-serverless-applications/SMY21G7FYZ
  - Covers deployment strategies (canary, blue/green) needed for OPS-Q5 and OPS-Q9
- Amazon DynamoDB for Serverless Architecture — https://skillbuilder.aws/learn/SY1Y83VKTB/amazon-dynamodb-for-serverless-architectures/K9NM3PHH3S
  - Relevant for optimizing the existing DynamoDB data access patterns and implementing idempotency

**Module 4: Move to Managed Databases:**
- AWS PartnerCast: Vector Databases for Generative AI Applications — https://skillbuilder.aws/learn/UQ74USQJHU/aws-partnercast--vector-databases-for-generative-ai-applications--technical/7DKMBAPCST
  - Directly relevant to Phase 3 RAG enablement — understanding vector database options for product catalog semantic search

**Module 6: Move to Modern DevOps:**
- AWS Modernization Pathways: Move to Modern DevOps — https://skillbuilder.aws/learning-plan/1FGEQKGPQD/aws-modernization-pathways-move-to-modern-devops-includes-labs/MNQZ2KPVCK
- Getting Started with DevOps on AWS — https://skillbuilder.aws/learn/R4B13K95YQ/getting-started-with-devops-on-aws/38NHHYRV1R
  - Critical for addressing the CI/CD gap (INF-Q6) — the most impactful operational improvement
- AWS CloudFormation Getting Started — https://skillbuilder.aws/learn/RH22P2RXU4/aws-cloudformation-getting-started/KEK5BT6HSE
  - Complements CDK knowledge; useful for understanding synthesized CloudFormation templates
- Advanced Testing Practices Using AWS DevOps Tools — https://skillbuilder.aws/learn/1YC7UXUWBR/advanced-testing-practices-using-aws-devops-tools/A32U6G7NEQ
  - Addresses the testing gap (OPS-Q10) — all tests are currently commented out
- Monitor Python Applications Using Amazon CloudWatch Application Signals — https://skillbuilder.aws/learn/JMPDZD64MV/monitor-python-applications-using-amazon-cloudwatch-application-signals/2JP3J2MPCK
  - Concepts applicable to Node.js; demonstrates CloudWatch Application Signals for structured observability
- AWS Developer: CI/CD Automation — https://skillbuilder.aws/learn/C1KF8ZJ1D8/aws-developer--cicd-automation/KY1E1JS9FA
  - Directly addresses the missing CI/CD pipeline (INF-Q6)

**Module 7: Move to AI:**
- AWS Modernization Pathways: Move to AI — https://skillbuilder.aws/learning-plan/VDFEE4ACCV/aws-modernization-pathways-move-to-ai-pathways-includes-labs/P3DAWPTN63
- Introduction to Generative AI: Art of the Possible — https://skillbuilder.aws/learn/ZEVZZ1D4AS/introduction-to-generative-ai--art-of-the-possible/Y7MTGJCW1U
  - Foundational understanding of what agentic AI can do for this e-commerce platform
- Amazon Bedrock Getting Started — https://skillbuilder.aws/learn/63KTRM86DQ/amazon-bedrock-getting-started/SC2Y3HMAUE
  - Essential for Phase 3 agent integration using Amazon Bedrock
- Essentials for Prompt Engineering — https://skillbuilder.aws/learn/XBNAVKA88J/essentials-of-prompt-engineering/9T9Q45EDTV
  - Critical skill for designing agent prompts that interact with Product, Basket, and Order APIs
- Build and Evaluate Retrieval Augmented Generation (RAG) Applications using Knowledge Bases for Amazon Bedrock (Lab) — https://skillbuilder.aws/learn/JRGWCFYT67/lab--build-and-evaluate-retrieval-augmented-generation-rag-applications-using-knowledge-bases-for-amazon-bedrock/A4MN58JB7A
  - Directly relevant to Phase 3 vector database and RAG implementation for product search
- Introduction to Agentic AI on AWS — https://skillbuilder.aws/learn/DNBD5MT8ZD/introduction-to-agentic-ai-on-aws/WAKAFK6UFY
  - Core learning for understanding agentic patterns this application will adopt
- DevOps and AI on AWS: CloudWatch Anomaly Detection (Lab) — https://skillbuilder.aws/learn/RWYVJ73MXP/lab--devops-and-ai-on-aws-cloudwatch-anomaly-detection/BRPDNZUGU7
  - Addresses the anomaly detection gap (OPS-Q8) with hands-on CloudWatch experience
- Creating an AWS DevOps AI Agent with the Strands Agents SDK (Lab) — https://skillbuilder.aws/learn/AH1GD8AJY3/lab--creating-an-aws-devops-ai-agent-with-the-strands-agents-sdk/A9SKJNMPJ2
  - Hands-on agent development using the Strands SDK — directly applicable to Phase 3 agent implementation
- AWS PartnerCast: Deep Dive: Building Observable AI Agents with Strands, Amazon Bedrock Agent Core & SageMaker MLflow — https://skillbuilder.aws/learn/1EN76TZBB6/aws-partnercast--deep-dive-building-observable-ai-agents-with-strands-amazon-bedrock-agent-core--sagemaker-mlflow--technical/CX2K6XAT84
  - Advanced agent observability — combines agent development with the observability improvements needed across OPS criteria

---

## Detailed Findings

### Infrastructure & Platform

#### INF-Q1: Compute
- **Score**: 4/4 ✅
- **Finding**: All compute is AWS Lambda using `NodejsFunction` constructs defined in `lib/microservice.ts`. Three Lambda functions are defined: `productLambdaFunction`, `basketLambdaFunction`, and `orderingLambdaFunction`. Runtime is `Runtime.NODEJS_14_X` for all three. No EC2 instances, ECS tasks, or EKS clusters. 100% serverless compute.
- **Gap**: The `NODEJS_14_X` runtime is end-of-life (EOL) and no longer receives security patches from AWS. This is a security and supportability risk, though not an architectural gap.
- **Recommendation**: Upgrade all three Lambda functions to `Runtime.NODEJS_20_X` or `Runtime.NODEJS_22_X` in `lib/microservice.ts`. Also remove the `aws-sdk` from `externalModules` bundling config since AWS SDK v3 is already explicitly imported.

#### INF-Q2: Databases
- **Score**: 4/4 ✅
- **Finding**: All three databases are DynamoDB tables defined in `lib/database.ts`: `product` (PK: `id`), `basket` (PK: `userName`), and `order` (PK: `userName`, SK: `orderDate`). All use `BillingMode.PAY_PER_REQUEST` (on-demand). No self-managed databases detected anywhere in the codebase.
- **Gap**: None for agentic readiness. Tables use `RemovalPolicy.DESTROY` which is appropriate for dev but risky for production.
- **Recommendation**: Change `RemovalPolicy.DESTROY` to `RemovalPolicy.RETAIN` for production environments. Consider enabling point-in-time recovery (PITR) for the order table.

#### INF-Q3: Workflow Orchestration
- **Score**: 1/4 ❌
- **Finding**: No Step Functions, Temporal, Camunda, or any workflow orchestration service is defined in IaC or referenced in code. The checkout flow in `src/basket/index.js` is a hardcoded sequence: `getBasket()` → `prepareOrderPayload()` → `publishCheckoutBasketEvent()` → `deleteBasket()`. If any step fails mid-sequence, partial state can result (e.g., event published but basket not deleted).
- **Gap**: No dedicated workflow orchestration. Business-critical checkout flow lacks retry, compensation, and error recovery logic.
- **Recommendation**: Implement the checkout flow as an AWS Step Functions state machine with explicit error handling, retries, and compensation steps. This also enables future human-in-the-loop approval for high-value orders.

#### INF-Q4: Async Messaging
- **Score**: 4/4 ✅
- **Finding**: EventBridge custom bus (`SwnEventBus`) defined in `lib/eventbus.ts` with a rule (`CheckoutBasketRule`) matching source `com.swn.basket.checkoutbasket` and detail type `CheckoutBasket`. SQS queue (`OrderQueue`) defined in `lib/queue.ts` with 30-second visibility timeout and batch size of 1. Basket checkout publishes events → EventBridge rule routes to SQS → Ordering Lambda consumes from SQS.
- **Gap**: None. Managed messaging services are properly used for the async checkout flow.
- **Recommendation**: Consider adding a dead-letter queue (DLQ) to the `OrderQueue` for failed message handling. The current configuration has no DLQ, so poison messages will be retried indefinitely.

#### INF-Q5: Infrastructure as Code
- **Score**: 4/4 ✅
- **Finding**: All infrastructure is defined in AWS CDK (TypeScript) across 6 construct files in `lib/`: `database.ts` (DynamoDB), `microservice.ts` (Lambda), `apigateway.ts` (API Gateway), `eventbus.ts` (EventBridge), `queue.ts` (SQS), and `aws-microservices-stack.ts` (orchestration). CDK version 2.17.0 in `package.json`. Complete coverage of compute, databases, API, messaging.
- **Gap**: None for IaC coverage. CDK version 2.17.0 is outdated (current is 2.170+).
- **Recommendation**: Upgrade `aws-cdk-lib` from 2.17.0 to the latest 2.x version. Consider adding CDK Nag for security and best-practice compliance checks.

#### INF-Q6: CI/CD
- **Score**: 1/4 ❌
- **Finding**: No CI/CD pipeline definitions found. No `.github/workflows/` directory, no `buildspec.yml`, no `Jenkinsfile`, no CodePipeline definitions in IaC. The single test file `test/aws-microservices.test.ts` has all test code commented out. Deployments are manual `cdk deploy` via CLI.
- **Gap**: Entirely missing. No automated testing, building, or deployment pipeline.
- **Recommendation**: Create a CI/CD pipeline (GitHub Actions or AWS CodePipeline) with stages: install → lint → test → `cdk synth` → `cdk diff` (PR) → `cdk deploy` (merge to main). Re-enable the CDK snapshot tests.

#### INF-Q7: API Entry Point
- **Score**: 2/4 🟠
- **Finding**: Three `LambdaRestApi` instances defined in `lib/apigateway.ts`: `productApi` (Product Service), `basketApi` (Basket Service), `orderApi` (Order Service). Routes are explicitly defined (not proxy). However, no throttling configuration (`deployOptions`), no authorizers, no request validation models, and no WAF integration.
- **Gap**: API Gateway exists but lacks throttling, authentication, and request validation. Three separate API Gateways instead of a unified gateway increases management overhead.
- **Recommendation**: Add `deployOptions` with throttling limits to each API. Add request validation models for POST/PUT methods. Consider consolidating into a single API Gateway with separate resource paths for unified management, or add a shared usage plan.

#### INF-Q8: Real-time Streaming
- **Score**: 1/4 ❌
- **Finding**: No Kinesis Data Streams, Kinesis Firehose, or MSK (Managed Streaming for Apache Kafka) resources found in IaC or referenced in code. EventBridge and SQS provide asynchronous messaging but not real-time streaming.
- **Gap**: No real-time streaming capability. This is acceptable if the application does not require stream processing, but it limits future agent capabilities (e.g., real-time product updates, streaming analytics).
- **Recommendation**: Evaluate whether real-time streaming is needed for agentic use cases. If agents need to react to product changes or order events in real-time, consider adding Kinesis Data Streams or enabling EventBridge Pipes.

#### INF-Q9: Network Security
- **Score**: 1/4 ❌
- **Finding**: No VPC, subnet, security group, or NACL definitions in any CDK construct. Lambda functions are deployed without VPC configuration (default public Lambda execution environment). DynamoDB is accessed via public AWS endpoints.
- **Gap**: No network segmentation or security group controls. Lambda functions are not isolated in private subnets.
- **Recommendation**: For this serverless architecture, VPC is not strictly required for DynamoDB access (IAM-based). However, if the application adds RDS or other VPC-bound resources in the future, define a VPC with private subnets. Consider adding VPC endpoints for DynamoDB to keep traffic within the AWS network.

#### INF-Q10: Auto-scaling
- **Score**: 3/4 🟡
- **Finding**: Lambda functions inherently auto-scale with concurrent executions. DynamoDB tables use `BillingMode.PAY_PER_REQUEST` (on-demand) which auto-scales read/write capacity. No explicit Lambda reserved or provisioned concurrency configured in `lib/microservice.ts`. No SQS scaling configuration beyond batch size of 1.
- **Gap**: No explicit concurrency controls on Lambda functions. Under load, uncontrolled Lambda scaling could overwhelm downstream services or exceed account-level concurrency limits.
- **Recommendation**: Add `reservedConcurrentExecutions` to Lambda functions in `lib/microservice.ts` to prevent any single function from consuming all account concurrency. Consider provisioned concurrency for latency-sensitive endpoints.

### Application Architecture

#### APP-Q1: Programming Languages
- **Score**: 3/4 🟡
- **Finding**: CDK infrastructure is written in TypeScript (`lib/*.ts`, `tsconfig.json` targeting ES2018). Lambda functions are written in JavaScript with ES module syntax (`src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js`). AWS SDK v3 is used (`@aws-sdk/client-dynamodb ^3.55.0`, `@aws-sdk/client-eventbridge ^3.58.0`). TypeScript 3.9.7 in root `package.json`.
- **Gap**: Lambda functions use JavaScript instead of TypeScript, losing type safety. TypeScript 3.9.7 is significantly outdated (current is 5.x). The JavaScript/TypeScript ecosystem has excellent agent framework support (LangChain.js, Strands Agents SDK).
- **Recommendation**: Migrate Lambda handlers from JavaScript to TypeScript for type safety and better IDE support. Upgrade TypeScript from 3.9.7 to 5.x.

#### APP-Q2: API Documentation
- **Score**: 1/4 ❌
- **Finding**: No `openapi.yaml`, `swagger.json`, or any API specification files found in the repository. API routes are defined programmatically in `lib/apigateway.ts` but there is no machine-readable API documentation. No API annotations in source code.
- **Gap**: Entirely missing. Agents cannot discover API capabilities without machine-readable specifications.
- **Recommendation**: Create OpenAPI 3.0 specifications for all three APIs. Document all endpoints (GET/POST/PUT/DELETE for Product; GET/POST/DELETE for Basket; GET for Order), request/response schemas, error codes, and authentication requirements. These specs become the tool definitions for agent integration.

#### APP-Q3: Async vs Sync Communication
- **Score**: 2/4 🟠
- **Finding**: The basket checkout flow is asynchronous: `src/basket/index.js` publishes to EventBridge → SQS → `src/ordering/index.js` consumes and creates order. All other operations are synchronous: API Gateway → Lambda → DynamoDB → response. Approximately 1 out of ~12 API operations uses async communication.
- **Gap**: The majority of inter-service communication is synchronous. Only the checkout-to-ordering flow is event-driven.
- **Recommendation**: Identify operations that could benefit from async patterns (e.g., product catalog updates, order status notifications). Consider DynamoDB Streams + Lambda triggers for real-time reactions to data changes.

#### APP-Q4: Monolith vs Microservices
- **Score**: 4/4 ✅
- **Finding**: Three independently deployable microservices: Product (`src/product/`), Basket (`src/basket/`), and Ordering (`src/ordering/`). Each has its own `package.json`, `index.js` handler, and dedicated DynamoDB table. Communication between Basket and Ordering is via EventBridge/SQS events. No shared database tables, no circular dependencies.
- **Gap**: None. Clean microservices boundaries with proper event-driven communication.
- **Recommendation**: Maintain these boundaries as the application grows. Consider adding API contracts (OpenAPI specs) between services to formalize interfaces.

#### APP-Q5: API Response Format
- **Score**: 4/4 ✅
- **Finding**: All Lambda functions return structured JSON responses using `JSON.stringify()`. Response format is consistent: `{ message: "Successfully finished operation: ...", body: <data> }`. Error responses also use JSON: `{ message: "Failed to perform operation.", errorMsg: ..., errorStack: ... }`.
- **Gap**: None for format. Error responses include `errorStack` which should be removed (security concern, not a format gap).
- **Recommendation**: Standardize error response schema across all services. Remove `errorStack` from client-facing responses. Consider adopting RFC 7807 (Problem Details for HTTP APIs) for error responses.

#### APP-Q6: Workflow Logic
- **Score**: 1/4 ❌
- **Finding**: The checkout flow in `src/basket/index.js` `checkoutBasket()` function is a hardcoded sequential chain: (1) `getBasket(userName)` → (2) `prepareOrderPayload(checkoutRequest, basket)` → (3) `publishCheckoutBasketEvent(checkoutPayload)` → (4) `deleteBasket(userName)`. No Step Functions, SAGA pattern, or workflow engine. No compensation logic if step 3 succeeds but step 4 fails.
- **Gap**: Business-critical checkout workflow is fragile. No retry, compensation, or visibility into workflow state. If the Lambda times out between step 3 and step 4, the order is created but the basket remains.
- **Recommendation**: Implement this flow as a Step Functions Express Workflow or Standard Workflow. Each step becomes a state with explicit error handling and retries. This also provides built-in execution history for debugging.

#### APP-Q7: Idempotency
- **Score**: 1/4 ❌
- **Finding**: No idempotency keys, tokens, or deduplication mechanisms found in any Lambda handler. `PutItemCommand` in `src/product/index.js` creates products without condition expressions. `src/basket/index.js` checkout has no idempotency — a retry would create duplicate orders. `OrderQueue` in `lib/queue.ts` is a standard SQS queue (not FIFO), so no message deduplication.
- **Gap**: All write operations are non-idempotent. Duplicate requests create duplicate resources. The checkout flow is especially dangerous: a retry publishes duplicate events to EventBridge.
- **Recommendation**: Add `@aws-lambda-powertools/idempotency` to critical write operations (checkout, create product). Convert `OrderQueue` to a FIFO queue with content-based deduplication. Add DynamoDB condition expressions to prevent duplicate writes.

#### APP-Q8: Rate Limiting & Throttling
- **Score**: 1/4 ❌
- **Finding**: No throttling configuration on any API Gateway in `lib/apigateway.ts`. No `deployOptions` with throttle settings. No usage plans or API keys. No WAF rules. No application-level rate limiting middleware in Lambda handlers.
- **Gap**: APIs are completely unthrottled. An agent or malicious client can send unlimited requests, potentially causing DynamoDB throttling or Lambda concurrency exhaustion.
- **Recommendation**: Add `deployOptions: { throttlingRateLimit: X, throttlingBurstLimit: Y }` to each `LambdaRestApi`. Create usage plans with API keys for per-client rate limiting. Consider adding AWS WAF for additional protection.

#### APP-Q9: Resilience Patterns
- **Score**: 1/4 ❌
- **Finding**: No circuit breaker, retry, or timeout patterns in any Lambda handler. Error handling is a generic `try/catch` that returns HTTP 500 with the error message and stack trace. AWS SDK v3 has built-in retry (3 attempts by default) but no custom retry configuration. No timeout settings on DynamoDB or EventBridge client calls. No graceful degradation patterns.
- **Gap**: No application-level resilience. A DynamoDB throttle or EventBridge failure results in an immediate 500 error to the client with no retry or fallback.
- **Recommendation**: Configure explicit timeouts on SDK client calls. Add retry with exponential backoff for transient failures. Implement circuit breaker patterns for the EventBridge publish in checkout (e.g., using `cockatiel` or a simple state-based circuit breaker). Return appropriate HTTP status codes (429, 503) instead of generic 500.

#### APP-Q10: Long-running Processes
- **Score**: 2/4 🟠
- **Finding**: The checkout flow is asynchronous — basket checkout publishes to EventBridge/SQS, and the ordering Lambda processes asynchronously. However, there is no status polling endpoint or callback mechanism. The client receives a 200 response from `POST /basket/checkout` but has no way to check if the order was successfully created. The `GET /order/{userName}` endpoint can be used to query orders, but it is not linked to the checkout flow as a status endpoint.
- **Gap**: Async processing exists but no way for clients (or agents) to track the status of the checkout operation. An agent cannot determine if a checkout succeeded or failed.
- **Recommendation**: Add an order status endpoint or return a correlation ID from the checkout that can be used to poll for order completion. Consider implementing the async request-reply pattern with a status endpoint.

#### APP-Q11: API Versioning
- **Score**: 1/4 ❌
- **Finding**: No URL path versioning (`/v1/`, `/v2/`), no `Accept-Version` headers, no query parameter versioning, and no changelog. API routes are `/product`, `/basket`, `/order` with no version prefix. No backward compatibility strategy documented.
- **Gap**: APIs are completely unversioned. Any breaking change will affect all consumers simultaneously, including agents that depend on specific response schemas.
- **Recommendation**: Add URL path versioning (e.g., `/v1/product`) to all API resources in `lib/apigateway.ts`. Establish a versioning policy before agents are integrated, as agents are sensitive to API contract changes.

#### APP-Q12: Service Discovery & Mesh
- **Score**: 1/4 ❌
- **Finding**: Inter-service communication uses hardcoded values. The EventBridge bus name (`SwnEventBus`) is passed via environment variable `EVENT_BUSNAME` in `lib/microservice.ts`. Event source (`com.swn.basket.checkoutbasket`) and detail type (`CheckoutBasket`) are also hardcoded environment variables. No AWS Cloud Map, App Mesh, or service catalog.
- **Gap**: No service discovery mechanism. Adding new services requires manual environment variable configuration. No centralized API catalog for agent tool discovery.
- **Recommendation**: For this serverless architecture, consider using AWS Systems Manager Parameter Store or AppConfig for service endpoint configuration. Create an API catalog (even a simple JSON file) that agents can reference for tool discovery.

#### APP-Q13: AI/Agent Frameworks
- **Score**: 1/4 ❌
- **Finding**: No AI or agent framework dependencies found in any `package.json`. No Amazon Bedrock, LangChain, OpenAI, Anthropic, Strands Agents SDK, or MCP SDK imports. No AI-related code or configuration in any file. Dependencies are limited to AWS SDK v3 for DynamoDB and EventBridge.
- **Gap**: No AI or agent framework integration exists. The application has no connection to any LLM or agent orchestration system.
- **Recommendation**: Start with Amazon Bedrock for LLM access. Add the Strands Agents SDK or LangChain.js as the agent orchestration framework. Define agent tools based on the OpenAPI specs (created in Phase 2). The existing microservices architecture with clear API boundaries is well-suited for tool-based agent integration.

### Data Foundations

#### DATA-Q1: Vector Database Presence
- **Score**: 1/4 ❌
- **Finding**: No vector database found. No Amazon OpenSearch Service, Aurora with pgvector, S3 Vectors, Pinecone, Weaviate, Chroma, or Bedrock Knowledge Base configuration in any IaC or source file. No vector-related dependencies in any `package.json`.
- **Gap**: No vector search capability exists. Agents cannot perform semantic search over product catalog or order history.
- **Recommendation**: For agent-powered product discovery, deploy Amazon OpenSearch Service with k-NN plugin or use Amazon Bedrock Knowledge Bases. The product catalog in DynamoDB could be indexed with embeddings to enable natural language product search.

#### DATA-Q2: Vector DB Management
- **Score**: 1/4 ❌
- **Finding**: No vector database exists (see DATA-Q1). Therefore, no management evaluation is possible.
- **Gap**: No vector database to manage.
- **Recommendation**: When implementing a vector database (Phase 3), use a managed service — Amazon OpenSearch Serverless or Bedrock Knowledge Bases — to minimize operational overhead.

#### DATA-Q3: RAG Implementation
- **Score**: 1/4 ❌
- **Finding**: No RAG (Retrieval-Augmented Generation) components found. No embedding model calls, no document chunking or splitting code, no similarity search patterns, no Bedrock Knowledge Base integration. No references to Titan Embeddings, OpenAI ada, or any embedding model.
- **Gap**: No RAG pipeline. Agents cannot augment their responses with data from the product catalog or order history.
- **Recommendation**: Implement a RAG pipeline for the product catalog: (1) generate embeddings for product descriptions using Amazon Titan Embeddings, (2) store in OpenSearch or Bedrock Knowledge Base, (3) implement semantic search endpoint that agents can query.

#### DATA-Q4: Data Source Sprawl
- **Score**: 4/4 ✅
- **Finding**: Three DynamoDB tables, each accessed by exactly one dedicated Lambda function: `product` table → `productLambdaFunction`, `basket` table → `basketLambdaFunction`, `order` table → `orderingLambdaFunction`. Each microservice's `ddbClient.js` connects only to its own table via the `DYNAMODB_TABLE_NAME` environment variable. No cross-service data access.
- **Gap**: None. Clean data ownership with single-purpose accessors per table.
- **Recommendation**: Maintain this clean data ownership as the application grows. If agents need cross-domain data, route through service APIs rather than direct database access.

#### DATA-Q5: Data Access Pattern
- **Score**: 2/4 🟠
- **Finding**: Each microservice has a `ddbClient.js` module that creates a `DynamoDBClient` instance. However, data access logic (queries, scans, puts, deletes) is directly in the Lambda handler `index.js` files, not in a separate repository or data access layer. For example, `src/product/index.js` directly constructs `ScanCommand`, `GetItemCommand`, `PutItemCommand`, `DeleteItemCommand`, and `UpdateItemCommand` with DynamoDB-specific parameters (marshalling, expression attributes).
- **Gap**: No abstraction between business logic and data access. DynamoDB SDK specifics are mixed into handler functions. Changing the data store would require rewriting all handler logic.
- **Recommendation**: Extract data access operations into dedicated repository modules (e.g., `productRepository.js`) that expose domain-level methods (`getProduct`, `createProduct`). This decouples business logic from DynamoDB specifics and makes the code more testable and agent-friendly.

#### DATA-Q6: Unstructured Data
- **Score**: 1/4 ❌
- **Finding**: No S3 buckets defined in any CDK construct. No Textract, Tika, or any document parsing library in dependencies. No file upload or processing capabilities. Product images are referenced in the DynamoDB schema comment (`imageFile`) but no actual image storage or processing infrastructure exists.
- **Gap**: No unstructured data handling. If agents need to process documents, images, or PDFs (e.g., product manuals, invoices), there is no infrastructure for it.
- **Recommendation**: Add an S3 bucket for unstructured data storage. If product images need processing, add Amazon Rekognition or Textract integration. This is lower priority unless specific agent use cases require document processing.

#### DATA-Q7: Schema Documentation
- **Score**: 2/4 🟠
- **Finding**: DynamoDB table schemas are partially documented in `lib/database.ts` via CDK code comments: `product` (PK: id, attributes: name, description, imageFile, price, category), `basket` (PK: userName, items as SET-MAP with quantity, color, price, productId, productName), `order` (PK: userName, SK: orderDate, attributes: totalPrice, firstName, lastName, email, address, paymentMethod, cardInfo). However, these are informal comments, not formal schema definitions.
- **Gap**: No JSON Schema files, no Avro/Protobuf definitions, no schema registry. Schema is implicit in code comments and inferred from `marshall`/`unmarshall` patterns. DynamoDB's schemaless nature means the actual data shape is determined at write time, not enforced.
- **Recommendation**: Create JSON Schema files documenting each table's expected item structure. Add input validation in Lambda handlers to enforce schema on writes. These schemas can be referenced in OpenAPI specs and used by agents to understand data structure.

#### DATA-Q8: Data Access Layer
- **Score**: 2/4 🟠
- **Finding**: Each microservice has a `ddbClient.js` module (identical across all three: `src/product/ddbClient.js`, `src/basket/ddbClient.js`, `src/ordering/ddbClient.js`) that exports a `DynamoDBClient` instance. The basket service also has `eventBridgeClient.js` for EventBridge. However, these are just client instantiations — the actual data access logic (CRUD operations) is in the handler files, not in a separate data access layer.
- **Gap**: Data access logic is scattered across handler functions. No repository pattern, no data access abstraction. Duplicated client module code across three services.
- **Recommendation**: Create per-service repository modules that encapsulate all DynamoDB operations. Extract CRUD operations from handlers into `productRepository.js`, `basketRepository.js`, and `orderRepository.js`. Share the `ddbClient.js` pattern but add proper error handling and retry configuration.

#### DATA-Q9: Embedding Freshness
- **Score**: 1/4 ❌
- **Finding**: No embeddings or vector indexing exists in the application (see DATA-Q1). No event-driven or scheduled re-indexing pipelines. No DynamoDB Streams configured for change data capture (CDC).
- **Gap**: No embedding infrastructure to assess freshness for.
- **Recommendation**: When implementing the vector database (Phase 3), use DynamoDB Streams on the product table to trigger automatic re-indexing when products are created, updated, or deleted. This ensures the vector index stays current with the source of truth.

#### DATA-Q10: Database Engine Version & EOL
- **Score**: 4/4 ✅
- **Finding**: All databases are DynamoDB, a fully managed serverless service. DynamoDB has no user-managed engine version — AWS manages all infrastructure, patching, and upgrades transparently. No RDS, DocumentDB, ElastiCache, or any versioned database engine in the stack.
- **Gap**: None. DynamoDB eliminates version management and EOL concerns entirely.
- **Recommendation**: No action needed. Continue using DynamoDB for its operational simplicity. If future needs require relational databases, use Aurora Serverless v2 to maintain the serverless, version-managed approach.

#### DATA-Q11: Stored Procedures & Schema Complexity
- **Score**: 4/4 ✅
- **Finding**: No SQL files, stored procedures, triggers, or proprietary SQL constructs found anywhere in the repository. DynamoDB is a NoSQL database that does not support stored procedures. All business logic resides in the Lambda function application layer (`src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js`).
- **Gap**: None. All business logic is in the application layer, not in the database.
- **Recommendation**: Maintain this pattern. Keep business logic in application code where it can be tested, versioned, and exposed to agents via APIs.

### Identity, Security & Governance

#### SEC-Q1: Secret Management
- **Score**: 2/4 🟠
- **Finding**: No hardcoded secrets, passwords, or API keys found in any source file. Environment variables in `lib/microservice.ts` contain only non-sensitive configuration: table names (`DYNAMODB_TABLE_NAME`), key names (`PRIMARY_KEY`, `SORT_KEY`), and event configuration (`EVENT_SOURCE`, `EVENT_DETAILTYPE`, `EVENT_BUSNAME`). No AWS Secrets Manager, SSM Parameter Store, or Vault references. No `.env` files committed. Authentication to DynamoDB uses IAM roles (implicit via Lambda execution role).
- **Gap**: While no secrets are currently hardcoded (DynamoDB uses IAM, not credentials), there is no secret management infrastructure for when the application needs external API keys, database passwords, or third-party credentials (e.g., for LLM API access in Phase 3).
- **Recommendation**: Add AWS Secrets Manager or SSM Parameter Store integration proactively. When adding Bedrock or external API integrations, store API keys and credentials in Secrets Manager with automatic rotation.

#### SEC-Q2: IAM Least Privilege
- **Score**: 3/4 🟡
- **Finding**: CDK uses scoped IAM grants: `productTable.grantReadWriteData(productFunction)` in `lib/microservice.ts` generates IAM policies with actions limited to the specific table. `bus.grantPutEventsTo(props.publisherFuntion)` in `lib/eventbus.ts` scopes EventBridge permissions to the specific bus. SQS consumer permissions are auto-granted by `addEventSource()` in `lib/queue.ts`. No wildcard (`*`) actions or resources in the generated policies.
- **Gap**: `grantReadWriteData()` grants full read and write access to each table. The product GET Lambda only needs read access but has write permissions. The ordering Lambda (which only creates orders and reads) has full read-write including delete. This is broader than necessary.
- **Recommendation**: Use `grantReadData()` for read-only operations and `grantWriteData()` for write-only operations where possible. For the ordering service, separate the API Gateway handler (read-only) from the SQS consumer (write-only) into two Lambda functions with different permissions.

#### SEC-Q3: Identity Propagation
- **Score**: 1/4 ❌
- **Finding**: No JWT, OAuth2, Cognito, or identity token handling in any Lambda handler. User identity is passed as a URL path parameter (`{userName}`) in `lib/apigateway.ts` for basket and order APIs (e.g., `GET /basket/{userName}`, `GET /order/{userName}`). Any client can access any user's basket or orders by guessing or iterating usernames. No user context propagation between services.
- **Gap**: No authenticated identity. No user context. Any user can access any other user's data via the path parameter. The checkout flow passes `userName` from the request body, not from an authenticated token.
- **Recommendation**: Implement Cognito User Pool authentication. Extract `userName` from the JWT token's claims (e.g., `event.requestContext.authorizer.claims.sub`) instead of from path parameters. Propagate user context through EventBridge events to the ordering service.

#### SEC-Q4: Audit Logging
- **Score**: 1/4 ❌
- **Finding**: No CloudTrail configuration in any CDK construct. No CloudWatch Logs log group definitions with retention policies. Lambda functions create log groups automatically but with default infinite retention. No audit trail for API calls, data access, or administrative actions. No S3 bucket for log storage.
- **Gap**: No audit logging infrastructure. Cannot trace who accessed what data or when. Compliance and forensics capabilities are absent.
- **Recommendation**: Add CloudTrail in CDK with log file validation and S3 storage with object lock. Define explicit CloudWatch Log Groups for each Lambda with retention policies (e.g., 90 days for compliance). Add API Gateway access logging.

#### SEC-Q5: API Rate Limits
- **Score**: 1/4 ❌
- **Finding**: No throttling configuration on any API Gateway. No `deployOptions` with `throttlingRateLimit` or `throttlingBurstLimit` in `lib/apigateway.ts`. No usage plans, no API keys, no per-client quotas. No AWS WAF integration. No application-level rate limiting in Lambda handlers.
- **Gap**: APIs accept unlimited requests. Vulnerable to abuse, DDoS, and runaway agent loops. An agent in an infinite retry loop would consume unlimited Lambda concurrency.
- **Recommendation**: Add API Gateway throttling (e.g., 1000 requests/second default, 2000 burst). Create usage plans with API keys for per-client rate limiting. Add WAF rate-based rules to block abusive IPs.

#### SEC-Q6: PII Redaction
- **Score**: 1/4 ❌
- **Finding**: All Lambda handlers log the full event payload: `console.log("request:", JSON.stringify(event, undefined, 2))` in `src/product/index.js`, `src/basket/index.js`, and `src/ordering/index.js`. The order data includes PII fields (firstName, lastName, email, address, cardInfo — as documented in `lib/database.ts` comments). Error responses include stack traces: `errorStack: e.stack`. No PII masking or redaction in any logging path.
- **Gap**: PII (names, email, address, payment info) is logged in plain text to CloudWatch Logs. Stack traces are returned to clients. No Macie integration for PII detection.
- **Recommendation**: Implement a structured logger (e.g., `@aws-lambda-powertools/logger`) with PII masking for sensitive fields. Remove `errorStack` from all client-facing error responses. Add log scrubbing for fields like email, address, and cardInfo before writing to CloudWatch.

#### SEC-Q7: Human Approval Workflows
- **Score**: 1/4 ❌
- **Finding**: No Step Functions with human approval tasks. No `waitForTaskToken` patterns. No approval API endpoints. No manual approval gates in any workflow. The checkout flow in `src/basket/index.js` executes the full sequence (get basket → prepare → publish event → delete basket) without any approval step.
- **Gap**: All operations execute automatically without human oversight. No mechanism to gate high-risk actions (e.g., large orders, bulk product deletions) with human approval.
- **Recommendation**: When implementing Step Functions for the checkout flow (INF-Q3), add a human approval step for orders exceeding a value threshold. Use the `waitForTaskToken` pattern with SNS notification to an approver. This is essential for agentic workloads where agents may initiate high-value transactions.

#### SEC-Q8: Encryption at Rest
- **Score**: 2/4 🟠
- **Finding**: DynamoDB tables in `lib/database.ts` have no explicit KMS key configuration. DynamoDB uses AWS-owned encryption by default (encryption at rest is enabled by default with AWS-managed keys). No `aws_kms_key` resources in any CDK construct. No customer-managed KMS keys (CMK).
- **Gap**: Data is encrypted at rest with AWS-managed keys, but no customer-managed KMS keys are used. The order table stores PII (names, email, addresses, payment info) that warrants stronger encryption controls.
- **Recommendation**: Create a customer-managed KMS key in CDK and configure it on the DynamoDB tables (especially the order table with PII). This provides key rotation control, key policy management, and CloudTrail audit of key usage.

#### SEC-Q9: API Authentication
- **Score**: 1/4 ❌
- **Finding**: No API Gateway authorizers configured on any of the three REST APIs in `lib/apigateway.ts`. No Cognito User Pool resources. No API keys required. No Lambda authorizers. All 12 API endpoints (5 Product, 5 Basket, 2 Order) are publicly accessible without any authentication.
- **Gap**: All APIs are completely open to the internet. Anyone can create/modify/delete products, access any user's basket, trigger checkout, and view any user's orders. This is the most critical security gap.
- **Recommendation**: Immediately add a Cognito User Pool authorizer. In `lib/apigateway.ts`, create a `CognitoUserPoolsAuthorizer` and attach it to all API methods with `authorizationType: AuthorizationType.COGNITO`. This is a high-priority Phase 1 action.

#### SEC-Q10: Centralized Identity
- **Score**: 1/4 ❌
- **Finding**: No Cognito User Pool, Cognito Identity Pool, Okta, OIDC, SAML, or any identity provider configuration found in any CDK construct or source file. No SSO configuration. User identity is represented only by a `userName` string passed as a path parameter.
- **Gap**: No identity provider. No user registration, login, or session management. No federation or SSO. Users are identified by a plain string that anyone can forge.
- **Recommendation**: Deploy a Cognito User Pool with sign-up/sign-in flows. Configure OAuth2/OIDC endpoints. Use the Cognito Hosted UI or integrate with a frontend authentication flow. This is a prerequisite for SEC-Q3 (identity propagation) and SEC-Q9 (API authentication).

### Operations & Observability

#### OPS-Q1: Distributed Tracing
- **Score**: 1/4 ❌
- **Finding**: No X-Ray tracing enabled on any Lambda function — no `tracing` property set in `lib/microservice.ts`. No OpenTelemetry SDK in any `package.json`. No trace context propagation headers. No `aws-xray-sdk`, `@aws-lambda-powertools/tracer`, or any tracing library in dependencies. No Datadog, Jaeger, or Zipkin integration.
- **Gap**: Zero distributed tracing. Cannot correlate requests across the three microservices. The checkout flow (Basket → EventBridge → SQS → Ordering) is completely opaque — there is no way to trace a single checkout from API request to order creation.
- **Recommendation**: Add `tracing: lambda.Tracing.ACTIVE` to all Lambda functions in `lib/microservice.ts`. Add `@aws-lambda-powertools/tracer` to each Lambda's dependencies for automatic instrumentation of AWS SDK calls. This provides end-to-end X-Ray traces with minimal code changes.

#### OPS-Q2: Structured Logging
- **Score**: 1/4 ❌
- **Finding**: All Lambda handlers use `console.log()` and `console.error()` for logging. Examples: `console.log("request:", JSON.stringify(event, undefined, 2))` in all three handlers, `console.log("getProduct")` as method markers, `console.log(Items)` for DynamoDB results. No structured JSON log format. No correlation IDs. No log levels beyond console.log/error.
- **Gap**: Unstructured plain-text logs. No correlation IDs to link related log entries across services. Cannot use CloudWatch Log Insights effectively. Agent workflow debugging requires structured logs with trace context.
- **Recommendation**: Replace `console.log` with `@aws-lambda-powertools/logger` in all Lambda handlers. Configure JSON output format, inject correlation IDs automatically, and set appropriate log levels. This enables CloudWatch Log Insights queries and correlating logs with X-Ray traces.

#### OPS-Q3: Automated Evals
- **Score**: 1/4 ❌
- **Finding**: No eval framework, scoring scripts, golden datasets, LLM-as-judge patterns, or any AI testing infrastructure. No agent evaluation code. No RAGAS integration. No A/B test infrastructure. No AI is currently in use.
- **Gap**: No evaluation infrastructure exists. This is expected since no AI/agent integration exists yet, but it must be planned for Phase 3.
- **Recommendation**: When implementing AI agents (Phase 3), build an eval framework from day one. Create golden test datasets for agent behavior, implement automated scoring (task completion rate, response quality), and integrate eval runs into the CI/CD pipeline.

#### OPS-Q4: SLOs
- **Score**: 1/4 ❌
- **Finding**: No SLO definitions in any file. No CloudWatch alarms defined in CDK. No error budget tracking. No latency monitoring configuration. No `aws_cloudwatch_metric_alarm` resources. Default Lambda and API Gateway metrics exist but are not monitored.
- **Gap**: No service level objectives defined. No alerting on error rates or latency. Cannot measure or guarantee service reliability.
- **Recommendation**: Define SLOs for each API: availability (e.g., 99.9%), latency (e.g., p99 < 500ms), and error rate (e.g., < 0.1%). Create CloudWatch alarms in CDK for Lambda errors, API Gateway 5xx responses, and DynamoDB throttles. Create a CloudWatch dashboard for real-time visibility.

#### OPS-Q5: Rollback Capability
- **Score**: 1/4 ❌
- **Finding**: No deployment strategy configured. CDK deploy is direct-to-production with no blue/green, canary, or traffic shifting. No CodeDeploy integration. No feature flags. No Lambda version aliases or traffic shifting. No `RollbackConfiguration` in any CDK construct. No prompt versioning or configuration rollback capability.
- **Gap**: No automated rollback. A bad deployment requires manual intervention or re-running `cdk deploy` with a previous version. No canary analysis to detect bad deployments automatically.
- **Recommendation**: Add Lambda version aliases with CodeDeploy integration for canary deployments. Configure rollback triggers based on CloudWatch alarms (error rate increase). Use `currentVersion.addAlias('live')` with `deploymentConfig: LambdaDeploymentConfig.CANARY_10PERCENT_5MINUTES`.

#### OPS-Q6: LLM Cost Tracking
- **Score**: 1/4 ❌
- **Finding**: No LLM usage in the application. No token counting, cost attribution, or usage tracking infrastructure. No custom CloudWatch metrics for AI-related costs. No tiered retention policies for observability data.
- **Gap**: No LLM cost tracking infrastructure. When agents are introduced (Phase 3), there will be no mechanism to track token usage, cost per request, or per-user cost attribution.
- **Recommendation**: When integrating Bedrock (Phase 3), implement token usage tracking from day one. Log the `usage` object from LLM responses as custom CloudWatch metrics with dimensions for user, feature, and workflow. Set retention policies for LLM prompt/response logs.

#### OPS-Q7: Business Metrics
- **Score**: 1/4 ❌
- **Finding**: No custom CloudWatch metrics published. No business outcome tracking (e.g., orders completed, checkout conversion rate, average order value). Only default AWS service metrics (Lambda invocations, duration, errors; API Gateway request count, latency) are available.
- **Gap**: No business metrics. Cannot measure the impact of agent interactions on business outcomes (e.g., did the agent increase checkout completion rate?).
- **Recommendation**: Publish custom CloudWatch metrics for business events: orders created, checkout success/failure rate, average order value, products added to basket. Use `@aws-lambda-powertools/metrics` for clean metric publishing from Lambda handlers.

#### OPS-Q8: Anomaly Detection
- **Score**: 1/4 ❌
- **Finding**: No CloudWatch anomaly detection configured. No error rate alarms. No latency threshold alarms. No PagerDuty, OpsGenie, or SNS alerting integration. No composite alarms. No behavioral baseline monitoring.
- **Gap**: No anomaly detection or alerting. Silent failures go unnoticed. An agent causing elevated error rates or unusual API call patterns would not trigger any alert.
- **Recommendation**: Enable CloudWatch anomaly detection on Lambda error rates and API Gateway latency. Create composite alarms that fire when error rates AND latency both degrade. Configure SNS notifications for on-call engineers. This is critical for agentic workloads that can cause harm at machine speed.

#### OPS-Q9: Deployment Strategy
- **Score**: 1/4 ❌
- **Finding**: No deployment strategy defined. `cdk deploy` performs direct-to-production deployment. No CodeDeploy configuration. No Lambda traffic shifting or canary analysis. No feature flags. No Argo Rollouts or similar progressive delivery. No ALB weighted target groups (no ALB exists).
- **Gap**: Direct-to-production deployments with no safety net. A bad deployment affects 100% of traffic immediately.
- **Recommendation**: Implement canary deployments using Lambda aliases with CodeDeploy. Configure 10% traffic shift with 5-minute monitoring before full rollout. Add automatic rollback triggers based on CloudWatch alarm evaluation.

#### OPS-Q10: Integration Testing
- **Score**: 1/4 ❌
- **Finding**: `test/aws-microservices.test.ts` exists but all test code is commented out. The single test `'SQS Queue Created'` has an empty body. `jest.config.js` is configured but there are no active tests. No integration test suites, no API test collections (Postman/Newman), no contract tests, no end-to-end test pipelines.
- **Gap**: Zero active tests. The application has no automated verification of correctness at any level — unit, integration, or end-to-end.
- **Recommendation**: Re-enable and expand the CDK snapshot tests. Add integration tests for critical flows: (1) product CRUD via API, (2) basket operations, (3) checkout → order creation end-to-end. Use `@aws-cdk/assert` for CDK construct testing and a local DynamoDB for Lambda handler unit tests.

#### OPS-Q11: Incident Response Automation
- **Score**: 1/4 ❌
- **Finding**: No runbooks (markdown, YAML, or JSON) in the repository. No SSM Automation documents. No Lambda-based remediation functions. No Step Functions for incident workflows. No self-healing patterns (auto-restart, auto-scaling on failure). No links to runbooks in any configuration.
- **Gap**: No incident response automation. All incidents require manual investigation and resolution. No machine-readable runbooks for future agent-assisted incident response.
- **Recommendation**: Create runbooks for common failure scenarios (DynamoDB throttling, Lambda timeout, EventBridge delivery failure). Start with markdown runbooks in the repository, then graduate to SSM Automation documents for automated remediation. Add self-healing patterns (e.g., DLQ with automatic retry Lambda).

#### OPS-Q12: Observability Governance & Ownership
- **Score**: 1/4 ❌
- **Finding**: No `CODEOWNERS` file in the repository. No SLO definition files with named owners. No observability ownership model. No dashboards defined in CDK. No team ownership files referencing observability assets. No platform team tooling.
- **Gap**: No observability governance. No one is accountable for service reliability or observability quality. No SLO-driven culture to extend to agent-level SLOs.
- **Recommendation**: Create a `CODEOWNERS` file. Define service ownership with on-call responsibilities. Establish SLOs with named owners for each API. Create CloudWatch dashboards per service. This organizational foundation is necessary before agent SLOs (task success rate, hallucination rate) can be defined.

---

## Appendix: Evidence Index

| # | File | Key Evidence |
|---|------|-------------|
| 1 | `lib/aws-microservices-stack.ts` | CDK stack orchestration — shows all constructs (Database, Microservices, ApiGateway, Queue, EventBus) and their wiring |
| 2 | `lib/microservice.ts` | Lambda function definitions — NODEJS_14_X runtime, grantReadWriteData IAM, environment variables, no tracing/concurrency config |
| 3 | `lib/database.ts` | DynamoDB tables — product/basket/order with PAY_PER_REQUEST, RemovalPolicy.DESTROY, no KMS, schema in comments |
| 4 | `lib/apigateway.ts` | API Gateway — three LambdaRestApi instances, explicit routes, no auth/throttling/validation |
| 5 | `lib/eventbus.ts` | EventBridge — SwnEventBus, CheckoutBasketRule, SQS target, grantPutEventsTo |
| 6 | `lib/queue.ts` | SQS — OrderQueue with 30s visibility timeout, batch size 1, no DLQ |
| 7 | `src/product/index.js` | Product Lambda handler — CRUD operations, console.log logging, errorStack in responses, no idempotency |
| 8 | `src/basket/index.js` | Basket Lambda handler — hardcoded checkout sequence, EventBridge publish, PII in logs, no auth |
| 9 | `src/ordering/index.js` | Ordering Lambda handler — SQS/EventBridge/API Gateway invocation paths, createOrder without idempotency |
| 10 | `src/product/ddbClient.js` | DynamoDB client module — minimal, no retry config, duplicated across services |
| 11 | `src/basket/eventBridgeClient.js` | EventBridge client module — no retry/timeout config |
| 12 | `src/product/package.json` | Product dependencies — @aws-sdk/client-dynamodb ^3.55.0, no observability/resilience libraries |
| 13 | `src/basket/package.json` | Basket dependencies — @aws-sdk/client-dynamodb, @aws-sdk/client-eventbridge, no observability libraries |
| 14 | `src/ordering/package.json` | Ordering dependencies — @aws-sdk/client-dynamodb ^3.58.0 only |
| 15 | `package.json` | Root CDK project — aws-cdk-lib 2.17.0, TypeScript 3.9.7, both outdated |
| 16 | `cdk.json` | CDK configuration — standard feature flags, no custom context for environment/security |
| 17 | `tsconfig.json` | TypeScript config — ES2018 target, strict mode enabled |
| 18 | `test/aws-microservices.test.ts` | Test file — all test code commented out, zero active tests |
| 19 | `jest.config.js` | Jest configuration — configured for TypeScript tests but no active tests to run |
| 20 | `bin/aws-microservices.ts` | CDK app entry point — no environment-specific configuration (account/region commented out) |
