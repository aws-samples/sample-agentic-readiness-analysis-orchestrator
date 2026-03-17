# Agentic Readiness Assessment Report
**Target**: ./services/aws-microservices
**Date**: 2026-03-17
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Assessment Goal**: cost-optimization
**Goal Context**: Reducing licensing costs and migrating to managed and open-source services
**Repository Type**: application (auto-detected)

---

## Table of Contents

1. Executive Summary
2. Score Table
3. Top Priorities (Critical Gaps)
4. Detailed Findings
   - Infrastructure & Platform
   - Application Architecture
   - Data Foundations
   - Identity, Security & Governance
   - Operations & Observability
5. Recommended Modernization Pathways
   - Pathway Summary Table
   - Pathway Details (for Triggered pathways)
6. Readiness Roadmap
   - Phase 1 — License & Quick Savings (Days 1–30)
   - Phase 2 — Managed Service Migration (Months 1–3)
   - Phase 3 — Optimization & Governance (Months 3–6)
7. Recommended Self-Paced Learning Materials
8. Appendix: Evidence Index

---

## Executive Summary

This serverless e-commerce application built with AWS Lambda, DynamoDB (on-demand), EventBridge, and SQS already represents a **strong cost-optimized foundation** — there are no commercial database licenses, no self-managed infrastructure, and no EC2 instances to right-size. All compute and data services are fully managed and pay-per-use. However, the application has critical operational gaps that introduce **hidden cost risks**: Lambda functions run on the **EOL Node.js 14.x runtime** (which loses security patches and will eventually be force-deprecated, risking emergency migration costs), there is **no CI/CD pipeline** (manual `cdk deploy` increases deployment time and human error), **no API authentication** (exposing endpoints publicly creates risk of abuse and unexpected Lambda invocation costs), and **no observability** (making it impossible to identify cost anomalies, over-provisioned resources, or failing requests). Security and operations categories score critically low at 1.4/4.0 and 1.0/4.0 respectively, representing the primary areas where investment will prevent cost escalation and operational incidents.

### Overall Score: 1.8 / 4.0

| Category | Score | Status |
|----------|-------|--------|
| Infrastructure & Platform | 2.6 / 4.0 | 🟡 |
| Application Architecture | 2.1 / 4.0 | 🟠 |
| Data Foundations | 2.0 / 4.0 | 🟠 |
| Identity, Security & Governance | 1.4 / 4.0 | ❌ |
| Operations & Observability | 1.0 / 4.0 | ❌ |

---

## Top Priorities (Critical Gaps)

### 1. No CI/CD Pipeline (INF-Q6: 1/4) — Cost Impact: High
**What**: No CI/CD definitions exist in the repository — no GitHub Actions, no CodePipeline, no buildspec.yml, no Jenkinsfile. Deployments rely on manual `cdk deploy`.
**Why it matters for cost**: Manual deployments increase mean-time-to-deploy and human error rates. Failed deployments waste developer hours. Without automated testing in a pipeline, broken code reaches production, causing incident response costs and potential revenue loss. Automation reduces toil and enables cost-governance checks (e.g., `cdk diff` cost estimation) before deployment.
**First step**: Create a GitHub Actions workflow (or AWS CodePipeline) with `cdk diff`, `npm test`, and `cdk deploy` stages. Add a cost estimation step using `cdk diff` output.

### 2. No API Authentication (SEC-Q9: 1/4) — Cost Impact: Critical
**What**: All three API Gateway endpoints (Product Service, Basket Service, Order Service) in `lib/apigateway.ts` are publicly accessible with no authorizers, no API keys, and no authentication of any kind.
**Why it matters for cost**: Unauthenticated public APIs are vulnerable to abuse — bots, scrapers, and denial-of-wallet attacks can invoke Lambda functions and write to DynamoDB at scale, generating unbounded AWS costs. A single malicious actor could run up thousands of dollars in Lambda invocations and DynamoDB write capacity.
**First step**: Add a Cognito User Pool authorizer or Lambda authorizer to all API Gateway endpoints in `lib/apigateway.ts`. At minimum, add API keys with usage plans to throttle unauthenticated access.

### 3. EOL Lambda Runtime — Node.js 14.x (INF-Q1/APP-Q1) — Cost Impact: Medium
**What**: All three Lambda functions in `lib/microservice.ts` use `Runtime.NODEJS_14_X`, which reached end-of-life. AWS SDK v3 bundles `aws-sdk` as external, and the runtime itself no longer receives security patches.
**Why it matters for cost**: EOL runtimes are force-deprecated by AWS, which will eventually prevent new deployments and then disable the functions entirely. Emergency migration under pressure costs significantly more than planned migration. Additionally, Node.js 14.x cannot run on ARM64/Graviton processors, which offer 20% lower cost at equivalent or better performance.
**First step**: Update `runtime: Runtime.NODEJS_14_X` to `Runtime.NODEJS_20_X` in `lib/microservice.ts` for all three functions. Add `architecture: Architecture.ARM_64` to enable Graviton, saving ~20% on Lambda compute costs.

### 4. No Observability Stack (OPS-Q1 through OPS-Q12: all 1/4) — Cost Impact: High
**What**: Zero observability infrastructure — no distributed tracing (X-Ray), no structured logging, no CloudWatch alarms, no SLOs, no anomaly detection, no business metrics. All 12 Operations criteria scored 1/4.
**Why it matters for cost**: Without observability, cost anomalies go undetected. A misconfigured function running in a retry loop, a DynamoDB scan growing unbounded, or a sudden traffic spike can escalate costs for hours or days before anyone notices. CloudWatch alarms on Lambda invocation costs and DynamoDB consumed capacity are essential cost-governance controls.
**First step**: Enable AWS X-Ray tracing on all Lambda functions by adding `tracing: Tracing.ACTIVE` in `lib/microservice.ts`. Add CloudWatch alarms for Lambda error rates, DynamoDB consumed capacity, and API Gateway 4xx/5xx rates.

### 5. No API Rate Limiting (SEC-Q5/APP-Q8: 1/4) — Cost Impact: High
**What**: No throttling, no WAF, no usage plans configured on any of the three API Gateway REST APIs in `lib/apigateway.ts`. Default API Gateway throttle limits apply but are very high (10,000 req/s per account).
**Why it matters for cost**: Without rate limiting, a traffic spike (legitimate or malicious) can trigger massive Lambda invocations and DynamoDB operations. Combined with no authentication (SEC-Q9), the application is fully exposed to denial-of-wallet attacks. Rate limiting is the first line of defense against unexpected cost escalation.
**First step**: Add `deployOptions: { throttlingRateLimit: 100, throttlingBurstLimit: 200 }` to each `LambdaRestApi` in `lib/apigateway.ts`. Create usage plans with per-client quotas.

---

## Detailed Findings

### Infrastructure & Platform

#### INF-Q1: Compute
- **Score**: 4/4 ✅
- **Finding**: All compute is 100% AWS Lambda (serverless). Three `NodejsFunction` constructs defined in `lib/microservice.ts`: `productLambdaFunction`, `basketLambdaFunction`, and `orderingLambdaFunction`. No EC2 instances, no ECS tasks, no EKS clusters. Runtime is `Runtime.NODEJS_14_X` (EOL concern addressed separately).
- **Gap**: Lambda runtime is Node.js 14.x, which is end-of-life. Functions do not specify ARM64 architecture (defaulting to x86_64), missing Graviton cost savings.
- **Recommendation**: Upgrade to `Runtime.NODEJS_20_X` and add `architecture: Architecture.ARM_64` for ~20% Lambda cost reduction via Graviton processors.

#### INF-Q2: Databases
- **Score**: 4/4 ✅
- **Finding**: All three databases are DynamoDB with `BillingMode.PAY_PER_REQUEST` (on-demand), defined in `lib/database.ts`: `product` table (PK: id), `basket` table (PK: userName), `order` table (PK: userName, SK: orderDate). Fully managed, no self-managed databases, no commercial licenses. No Oracle, SQL Server, or any other commercial database detected.
- **Gap**: No gap for managed database criterion. However, `RemovalPolicy.DESTROY` on all tables is a data-loss risk in production.
- **Recommendation**: Change `RemovalPolicy.DESTROY` to `RemovalPolicy.RETAIN` for production environments to prevent accidental data loss during stack deletion. Evaluate DynamoDB reserved capacity for predictable workloads to reduce costs vs. on-demand pricing.

#### INF-Q3: Workflow Orchestration
- **Score**: 1/4 ❌
- **Finding**: No dedicated workflow orchestration service found. No Step Functions, no Temporal, no Camunda. The checkout flow in `src/basket/index.js` implements a sequential workflow in application code: `getBasket` → `prepareOrderPayload` → `publishCheckoutBasketEvent` → `deleteBasket`. If any step fails mid-execution, the workflow is left in an inconsistent state.
- **Gap**: No dedicated orchestration. The checkout workflow has no error recovery — if `publishCheckoutBasketEvent` succeeds but `deleteBasket` fails, the basket remains and the order is duplicated on retry.
- **Recommendation**: Implement the checkout workflow as an AWS Step Functions state machine with error handling, retry logic, and compensating transactions. This adds reliability without significant cost (Step Functions pricing is per-state-transition, minimal for checkout volumes).

#### INF-Q4: Async Messaging
- **Score**: 4/4 ✅
- **Finding**: Managed messaging services in use: Amazon EventBridge (`SwnEventBus` in `lib/eventbus.ts`) and Amazon SQS (`OrderQueue` in `lib/queue.ts`). EventBridge rule `CheckoutBasketRule` routes checkout events from source `com.swn.basket.checkoutbasket` to SQS queue. SQS queue triggers the ordering Lambda with `batchSize: 1`.
- **Gap**: No dead-letter queue (DLQ) configured on the SQS queue for failed message processing. SQS `visibilityTimeout` is only 30 seconds.
- **Recommendation**: Add a DLQ to `OrderQueue` in `lib/queue.ts` to capture failed checkout events. Consider increasing `visibilityTimeout` to accommodate processing time and retries.

#### INF-Q5: Infrastructure as Code
- **Score**: 4/4 ✅
- **Finding**: 100% of infrastructure is defined in AWS CDK (TypeScript). Six CDK construct files in `lib/`: `aws-microservices-stack.ts` (stack orchestrator), `database.ts` (DynamoDB tables), `microservice.ts` (Lambda functions), `apigateway.ts` (API Gateway), `eventbus.ts` (EventBridge), `queue.ts` (SQS). All compute, databases, messaging, and API resources are IaC-defined.
- **Gap**: No gap in IaC coverage. CDK version is 2.17.0 (from `package.json`), which is significantly outdated (current is 2.170+).
- **Recommendation**: Update `aws-cdk-lib` from 2.17.0 to the latest version in `package.json` for latest construct features, security patches, and cost-optimization features.

#### INF-Q6: CI/CD
- **Score**: 1/4 ❌
- **Finding**: No CI/CD pipeline definitions found anywhere in the repository. No `.github/workflows/`, no `buildspec.yml`, no `Jenkinsfile`, no `.gitlab-ci.yml`, no CodePipeline definition in CDK. Deployment is manual via `cdk deploy` as documented in `README.md`.
- **Gap**: Entire CI/CD capability is missing. No automated testing, building, or deployment. No cost-governance checks before deployment.
- **Recommendation**: Create a CI/CD pipeline (GitHub Actions or AWS CodePipeline) with stages: lint → test → `cdk diff` (with cost estimation) → manual approval → `cdk deploy`. This prevents costly misconfigurations from reaching production.

#### INF-Q7: API Entry Point
- **Score**: 2/4 🟠
- **Finding**: Three separate `LambdaRestApi` instances defined in `lib/apigateway.ts`: "Product Service", "Basket Service", and "Order Service". Each has well-defined REST routes (`/product`, `/basket`, `/order`) with proper HTTP method configuration. However, no throttling, no authorization, no request validation, and no usage plans are configured.
- **Gap**: API Gateway is present but unconfigured for production use — no throttling, no auth, no request validation, no WAF integration, no usage plans.
- **Recommendation**: Add `deployOptions` with throttling settings, add request validators for POST/PUT methods, and configure usage plans with API keys for cost tracking per consumer.

#### INF-Q8: Real-time Streaming
- **Score**: 1/4 ❌
- **Finding**: No real-time streaming services detected. No Kinesis Data Streams, no Kinesis Firehose, no MSK. EventBridge and SQS are messaging services, not streaming. No stream consumer patterns in any source code.
- **Gap**: No streaming capability. For an e-commerce application, real-time streaming could enable inventory updates, price changes, and order status notifications.
- **Recommendation**: Evaluate whether real-time streaming is needed for the business use case. If real-time analytics or notifications are required, consider Kinesis Data Streams for event streaming or DynamoDB Streams for change data capture.

#### INF-Q9: Network Security
- **Score**: 1/4 ❌
- **Finding**: No VPC, private subnets, security groups, or NACLs defined in any CDK construct. Lambda functions run in the default AWS-managed VPC (no customer VPC configuration). DynamoDB access is over the public DynamoDB endpoint.
- **Gap**: No network segmentation. While Lambda + DynamoDB do not strictly require VPC for functionality, there are no VPC endpoints configured for private API access, and all API Gateway endpoints are public.
- **Recommendation**: For a serverless architecture, add VPC endpoints for DynamoDB and Lambda if private network access is needed. Add a WAF to API Gateway endpoints to protect against common web exploits. For cost-optimization, note that VPC-attached Lambda adds cold start latency — evaluate whether the security benefit justifies the performance cost.

#### INF-Q10: Auto-scaling
- **Score**: 4/4 ✅
- **Finding**: All compute and data services auto-scale natively. Lambda functions scale automatically per invocation. DynamoDB tables use `BillingMode.PAY_PER_REQUEST` (on-demand) in `lib/database.ts`, which auto-scales read/write capacity to match demand. SQS and EventBridge are inherently scalable managed services.
- **Gap**: No Lambda reserved concurrency or provisioned concurrency configured. No DynamoDB auto-scaling policies (not needed with on-demand, but relevant if switching to provisioned for cost optimization).
- **Recommendation**: Set Lambda reserved concurrency limits to prevent runaway costs from unexpected traffic spikes. Evaluate DynamoDB provisioned capacity with auto-scaling for tables with predictable traffic patterns — this can reduce costs by 50-70% compared to on-demand pricing.

### Application Architecture

#### APP-Q1: Programming Languages
- **Score**: 3/4 🟡
- **Finding**: Lambda handlers are written in JavaScript (ES6 modules) in `src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js`. CDK IaC is TypeScript (`lib/*.ts`). AWS SDK v3 is used (`@aws-sdk/client-dynamodb`, `@aws-sdk/client-eventbridge`). The JS/TS ecosystem has strong agent framework support (LangChain.js, Strands Agents SDK).
- **Gap**: Lambda runtime is Node.js 14.x (EOL). Source code uses `exports.handler` syntax mixed with ES6 imports, indicating inconsistent module patterns.
- **Recommendation**: Upgrade Lambda runtime to Node.js 20.x. Standardize on ES module syntax throughout. Consider migrating Lambda handlers to TypeScript for type safety (matching the CDK code).

#### APP-Q2: API Documentation
- **Score**: 1/4 ❌
- **Finding**: No OpenAPI or Swagger specification files found in the repository. No `openapi.yaml`, no `swagger.json`. API routes are defined programmatically in `lib/apigateway.ts` but no spec is generated or maintained. Route comments exist in `apigateway.ts` but are not machine-readable.
- **Gap**: No API documentation. Consumers have no way to discover available endpoints, request/response schemas, or error codes without reading source code.
- **Recommendation**: Generate an OpenAPI 3.0 spec from the existing API Gateway routes. Document request/response schemas, error codes, and examples. This is a prerequisite for API-aware agent tooling.

#### APP-Q3: Async vs Sync Communication
- **Score**: 3/4 🟡
- **Finding**: The critical checkout workflow is fully asynchronous: `src/basket/index.js` publishes a `CheckoutBasket` event to EventBridge → routed via SQS → consumed by `src/ordering/index.js`. The ordering service handles both SQS and EventBridge invocations (backward compatible). CRUD operations (GET/POST/PUT/DELETE on product, basket, order) are synchronous via API Gateway → Lambda.
- **Gap**: No async pattern for bulk operations (e.g., batch product updates). The SQS consumer processes with `batchSize: 1`, not leveraging batch efficiency.
- **Recommendation**: Consider increasing SQS `batchSize` for the ordering Lambda to improve throughput and reduce Lambda invocation costs. Evaluate whether product catalog updates should be event-driven.

#### APP-Q4: Monolith vs Microservices
- **Score**: 4/4 ✅
- **Finding**: Three clearly separated microservices, each with its own: Lambda function (`lib/microservice.ts`), DynamoDB table (`lib/database.ts`), API Gateway (`lib/apigateway.ts`), and source directory (`src/product/`, `src/basket/`, `src/ordering/`). Inter-service communication is event-driven via EventBridge/SQS (not direct HTTP calls). Each service owns its own data — no shared database tables.
- **Gap**: No gap. Architecture is already well-decomposed with clear service boundaries.
- **Recommendation**: Maintain this clean separation. As services grow, consider separate CDK stacks per service for independent deployment.

#### APP-Q5: API Response Format
- **Score**: 4/4 ✅
- **Finding**: All API responses use structured JSON. Every handler in `src/product/index.js`, `src/basket/index.js`, and `src/ordering/index.js` returns `JSON.stringify({ message: ..., body: ... })`. DynamoDB items are properly unmarshalled to plain JSON objects using `@aws-sdk/util-dynamodb`.
- **Gap**: Error responses also return JSON but include `errorStack` (full stack traces), which is a security concern but not a format issue.
- **Recommendation**: Standardize error response schema (remove stack traces in production). Consider adding pagination support for list endpoints (`getAllProducts`, `getAllBaskets`, `getAllOrders`) which currently return unbounded DynamoDB `Scan` results.

#### APP-Q6: Workflow Logic
- **Score**: 2/4 🟠
- **Finding**: The checkout workflow in `src/basket/index.js` implements business logic as sequential imperative code: `checkoutBasket()` calls `getBasket()` → `prepareOrderPayload()` → `publishCheckoutBasketEvent()` → `deleteBasket()`. No dedicated workflow engine or state machine. Price calculation (`totalPrice`) is hardcoded in the `prepareOrderPayload` function.
- **Gap**: Workflow logic is embedded in application code with no error recovery. If any step fails after event publication, the system is left in an inconsistent state (event sent but basket not deleted, or vice versa).
- **Recommendation**: Extract the checkout workflow into AWS Step Functions for visibility, error handling, and retry logic. This provides audit trails and state management at low cost for e-commerce checkout volumes.

#### APP-Q7: Idempotency
- **Score**: 1/4 ❌
- **Finding**: No idempotency mechanisms found. No idempotency keys in API schemas, no deduplication IDs in SQS message publishing, no conditional writes in DynamoDB operations. `PutItemCommand` in `src/product/index.js` and `src/basket/index.js` overwrites existing items unconditionally. The ordering service creates orders with `new Date().toISOString()` as sort key — replaying an SQS message creates duplicate orders.
- **Gap**: Complete absence of idempotency. SQS message replay or API retry will create duplicate orders and overwrite products/baskets without detection.
- **Recommendation**: Add DynamoDB conditional expressions to prevent duplicate writes. Add `MessageDeduplicationId` when publishing to SQS. Implement idempotency tokens for POST endpoints using a DynamoDB-based idempotency store or the Powertools for AWS Lambda idempotency utility.

#### APP-Q8: Rate Limiting & Throttling
- **Score**: 1/4 ❌
- **Finding**: No rate limiting configured at any layer. API Gateway in `lib/apigateway.ts` uses default `LambdaRestApi` settings with no `deployOptions` for throttling. No WAF rules. No usage plans. No application-level rate limiting middleware in any Lambda handler.
- **Gap**: APIs are completely unthrottled. Default API Gateway account-level limits (10,000 req/s) are the only protection.
- **Recommendation**: Add `deployOptions: { throttlingRateLimit: 100, throttlingBurstLimit: 200 }` to each `LambdaRestApi`. Create usage plans with quotas. Consider adding AWS WAF for bot protection — this directly prevents denial-of-wallet attacks.

#### APP-Q9: Resilience Patterns
- **Score**: 1/4 ❌
- **Finding**: No resilience patterns implemented. No circuit breakers, no explicit retry logic, no timeout configurations. AWS SDK v3 has built-in retry behavior (3 retries by default), but no application-level resilience. SQS `visibilityTimeout` is 30 seconds in `lib/queue.ts`, but no DLQ for failed processing. Error handling in all handlers is basic try/catch that re-throws or returns 500.
- **Gap**: No circuit breakers, no explicit retry with backoff, no timeout configuration. Failed external calls (DynamoDB, EventBridge) rely solely on SDK defaults.
- **Recommendation**: Add DLQ to SQS queue. Implement retry with exponential backoff for EventBridge `PutEventsCommand` in `src/basket/index.js`. Set explicit timeout on Lambda functions. Use Powertools for AWS Lambda for structured error handling.

#### APP-Q10: Long-running Processes
- **Score**: 2/4 🟠
- **Finding**: The checkout process is asynchronous: basket service publishes to EventBridge, SQS buffers, ordering service consumes. This correctly handles the potentially long-running order creation asynchronously. However, there is no mechanism for the client to check order status — `POST /basket/checkout` returns immediately with no order ID or status URL.
- **Gap**: No status polling endpoint or callback mechanism for the async checkout operation. Clients have no way to know if the order was successfully created after checkout.
- **Recommendation**: Return an order reference ID from `POST /basket/checkout`. Add a `GET /order/status/{orderId}` endpoint. Consider WebSocket API for real-time order status notifications.

#### APP-Q11: API Versioning
- **Score**: 1/4 ❌
- **Finding**: No API versioning strategy. Routes are unversioned: `/product`, `/basket`, `/order` (defined in `lib/apigateway.ts`). No `/v1/` prefix, no `Accept-Version` headers, no versioning annotations. No changelog files.
- **Gap**: No versioning means any API change is a breaking change for consumers. No backward compatibility guarantees.
- **Recommendation**: Add `/v1/` prefix to all API routes in `lib/apigateway.ts`. Establish a versioning policy. This is low-effort (route prefix change) and prevents costly consumer breakage.

#### APP-Q12: Service Discovery & Mesh
- **Score**: 3/4 🟡
- **Finding**: Services communicate via EventBridge (event-driven), not direct HTTP calls. The basket service publishes events with `EVENT_BUSNAME: "SwnEventBus"` (configured via environment variable in `lib/microservice.ts`). EventBridge rules in `lib/eventbus.ts` route events to SQS, which triggers the ordering service. No hard-coded service endpoints between microservices.
- **Gap**: Event bus name is a hard-coded string "SwnEventBus" passed as environment variable. No formal service registry or API catalog.
- **Recommendation**: Use CDK cross-stack references or SSM Parameter Store for service discovery values. Document the event schema in a shared location for service catalog purposes.

#### APP-Q13: AI/Agent Frameworks
- **Score**: 1/4 ❌
- **Finding**: No AI or agent framework dependencies found. No Bedrock SDK, no LangChain, no Strands Agents, no OpenAI, no Anthropic SDK in any `package.json` (root, product, basket, or ordering). No MCP SDK imports. No AI-related code patterns.
- **Gap**: No AI/agent integration. The application has no AI capabilities.
- **Recommendation**: For cost-optimization goal, AI integration is low priority. When ready, the existing API Gateway endpoints and JSON responses provide a solid foundation for agent tool integration via Amazon Bedrock Agents.

### Data Foundations

#### DATA-Q1: Vector Database Presence
- **Score**: 1/4 ❌
- **Finding**: No vector database found. No OpenSearch domain, no Aurora with pgvector, no Pinecone, no Weaviate, no Chroma imports. No Bedrock Knowledge Bases configuration. Only DynamoDB tables are used for data storage.
- **Gap**: No vector search capability. Not required for current e-commerce CRUD operations.
- **Recommendation**: Low priority for cost-optimization goal. If product search needs semantic capabilities in the future, consider Amazon OpenSearch Serverless with vector search for pay-per-use pricing.

#### DATA-Q2: Vector DB Management
- **Score**: 1/4 ❌
- **Finding**: No vector database exists, so there is no vector DB management to evaluate.
- **Gap**: No vector DB present.
- **Recommendation**: Not applicable until a vector database is introduced. When needed, use a managed service (OpenSearch Serverless, Bedrock Knowledge Bases) aligned with cost-optimization preferences.

#### DATA-Q3: RAG Implementation
- **Score**: 1/4 ❌
- **Finding**: No RAG implementation. No embedding model calls, no document chunking, no semantic search patterns in any source file.
- **Gap**: No RAG capability.
- **Recommendation**: Low priority for cost-optimization. When needed for product search or customer support, leverage Bedrock Knowledge Bases for a managed RAG pipeline.

#### DATA-Q4: Data Source Sprawl
- **Score**: 4/4 ✅
- **Finding**: Three DynamoDB tables, each owned by exactly one microservice: `product` table accessed only by `src/product/index.js`, `basket` table accessed only by `src/basket/index.js`, `order` table accessed only by `src/ordering/index.js`. Clean service-per-table ownership. No cross-service data access.
- **Gap**: No gap. Clean data ownership.
- **Recommendation**: Maintain this pattern as the application grows. Document table ownership in a data catalog.

#### DATA-Q5: Data Access Pattern
- **Score**: 2/4 🟠
- **Finding**: Each microservice accesses DynamoDB directly via its own `ddbClient.js` module. The product service handler (`src/product/index.js`) directly constructs DynamoDB commands (`GetItemCommand`, `PutItemCommand`, `ScanCommand`, `QueryCommand`, `UpdateItemCommand`, `DeleteItemCommand`). Business logic (price calculation in `prepareOrderPayload`) and data access are mixed in the same handler files.
- **Gap**: No separation between business logic and data access. DynamoDB-specific marshalling/unmarshalling code is spread throughout handlers. `ScanCommand` is used for `getAllProducts()` and `getAllBaskets()`, which is costly at scale (reads every item in the table).
- **Recommendation**: Extract data access into repository modules separate from handler logic. Replace `ScanCommand` with `QueryCommand` using GSIs for list operations — DynamoDB Scans consume read capacity proportional to total table size, which is a direct cost concern at scale.

#### DATA-Q6: Unstructured Data
- **Score**: 1/4 ❌
- **Finding**: No S3 storage, no document parsing (Textract, Tika), no unstructured data handling. All data is structured and stored in DynamoDB. The product schema includes an `imageFile` field (from comments in `lib/database.ts`) but no S3 integration for actual image storage.
- **Gap**: No unstructured data capability. Product images referenced but not stored in S3.
- **Recommendation**: If product images are needed, add S3 bucket for image storage with CDK. Use CloudFront for image delivery to reduce S3 transfer costs.

#### DATA-Q7: Schema Documentation
- **Score**: 1/4 ❌
- **Finding**: Schema is defined only in code comments in `lib/database.ts`: `product: PK: id -- name - description - imageFile - price - category`, `basket: PK: userName -- items (SET-MAP object)`, `order: PK: userName - SK: orderDate -- totalPrice - firstName - lastName - email - address - paymentMethod - cardInfo`. No JSON Schema files, no Avro/Protobuf definitions, no formal schema documentation.
- **Gap**: Schema exists only as code comments. No versioned, machine-readable schema definitions. The `order` table stores PII (email, address, cardInfo) with no documentation of data sensitivity classification.
- **Recommendation**: Create formal JSON Schema definitions for each table. Document PII fields and data sensitivity classification — this is critical for compliance and prevents costly data governance incidents.

#### DATA-Q8: Data Access Layer
- **Score**: 2/4 🟠
- **Finding**: Each microservice has a `ddbClient.js` module (`src/product/ddbClient.js`, `src/basket/ddbClient.js`, `src/ordering/ddbClient.js`) that creates a `DynamoDBClient` instance. However, all three files are identical — the same 4-line module duplicated across services. Data operations (CRUD) are implemented directly in each handler's `index.js` with DynamoDB-specific marshalling.
- **Gap**: Data client is abstracted into a module, but the actual data operations (queries, puts, scans) are not abstracted. Switching from DynamoDB to another data store would require rewriting every handler.
- **Recommendation**: Create a data access abstraction layer (repository pattern) per service that encapsulates DynamoDB-specific commands. This enables future data store optimization (e.g., DynamoDB → Aurora PostgreSQL for complex queries) without rewriting business logic.

#### DATA-Q9: Embedding Freshness
- **Score**: 1/4 ❌
- **Finding**: No embeddings, no vector indexes, no indexing pipelines. No embedding refresh mechanism.
- **Gap**: No embeddings to refresh.
- **Recommendation**: Not applicable until RAG is implemented. When implemented, use DynamoDB Streams to trigger embedding updates on data changes.

#### DATA-Q10: Database Engine Version & EOL
- **Score**: 4/4 ✅
- **Finding**: All databases are Amazon DynamoDB, a fully managed serverless service. DynamoDB has no engine version to pin — AWS manages all updates transparently. No EOL concerns.
- **Gap**: No gap. DynamoDB is always current.
- **Recommendation**: No action needed. DynamoDB's serverless model eliminates version management overhead, which is a cost-optimization advantage.

#### DATA-Q11: Stored Procedures & Schema Complexity
- **Score**: 4/4 ✅
- **Finding**: No stored procedures, no triggers, no proprietary SQL constructs. DynamoDB is a NoSQL database that does not support stored procedures. All business logic resides in Lambda functions (`src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js`). No `.sql` files in the repository.
- **Gap**: No gap. All business logic is in the application layer.
- **Recommendation**: Maintain this pattern. Application-layer business logic is portable across data stores, supporting future cost-optimization migrations if needed.

### Identity, Security & Governance

#### SEC-Q1: Secret Management
- **Score**: 2/4 🟠
- **Finding**: No hardcoded secrets found in any source file. Environment variables in `lib/microservice.ts` contain non-secret configuration: `PRIMARY_KEY`, `DYNAMODB_TABLE_NAME`, `EVENT_SOURCE`, `EVENT_DETAILTYPE`, `EVENT_BUSNAME`. DynamoDB access uses IAM role credentials (via `grantReadWriteData()` in CDK), not embedded credentials. However, no Secrets Manager or Vault integration exists.
- **Gap**: No formal secret management infrastructure. While no secrets are currently needed (IAM roles handle auth), the application has no mechanism to manage secrets if future integrations require API keys, third-party credentials, or database passwords.
- **Recommendation**: Acceptable for current architecture (IAM-only auth). Add AWS Secrets Manager integration when external service credentials are needed. Budget for Secrets Manager costs ($0.40/secret/month) in future planning.

#### SEC-Q2: IAM Least Privilege
- **Score**: 3/4 🟡
- **Finding**: CDK uses fine-grained grant methods: `productTable.grantReadWriteData(productFunction)` in `lib/microservice.ts` grants only DynamoDB read/write to the specific table. `bus.grantPutEventsTo(props.publisherFuntion)` in `lib/eventbus.ts` grants only EventBridge put-events permission. No wildcard `Action: "*"` or `Resource: "*"` policies. Each Lambda has its own execution role.
- **Gap**: `grantReadWriteData()` grants both read and write — the ordering service only needs write access (it only creates orders via `PutItemCommand`). The product GET endpoint has write permissions it doesn't need.
- **Recommendation**: Use `grantReadData()` for read-only Lambda functions and `grantWriteData()` for write-only functions where applicable. Reducing IAM scope reduces blast radius of compromised functions.

#### SEC-Q3: Identity Propagation
- **Score**: 1/4 ❌
- **Finding**: No authentication or identity propagation. No JWT parsing, no OAuth2, no Cognito integration, no user token exchange. The `userName` field in basket and order operations is passed in the request body/path (`/basket/{userName}`, `/order/{userName}`) with no identity verification — any caller can access any user's basket or orders.
- **Gap**: Complete absence of identity. Any caller can impersonate any user by specifying their `userName`. This is a critical security and potential compliance cost risk.
- **Recommendation**: Add Amazon Cognito User Pool with API Gateway authorizer. Map `userName` from the Cognito JWT token `sub` claim instead of accepting it from request parameters. This prevents unauthorized access and the associated regulatory/breach costs.

#### SEC-Q4: Audit Logging
- **Score**: 1/4 ❌
- **Finding**: No CloudTrail configuration in CDK. No CloudWatch log retention policies. Lambda functions log to CloudWatch Logs by default, but with no structured format and no log retention configuration (logs retained indefinitely by default, which incurs cost).
- **Gap**: No audit trail infrastructure. CloudWatch Logs have no retention policy — default infinite retention accumulates storage costs over time.
- **Recommendation**: Set CloudWatch Logs retention to 30-90 days via CDK `logRetention` property on Lambda functions. Enable CloudTrail for API-level audit logging. Configure S3 lifecycle policies for log archival. Indefinite log retention is a hidden cost that grows linearly with traffic.

#### SEC-Q5: API Rate Limits
- **Score**: 1/4 ❌
- **Finding**: No rate limiting on any API endpoint. No `throttlingRateLimit`, no `throttlingBurstLimit` in API Gateway `deployOptions`. No usage plans, no API keys, no WAF rules. All three APIs in `lib/apigateway.ts` use default settings.
- **Gap**: APIs are unprotected against traffic spikes. Combined with no authentication, this creates a direct cost exposure.
- **Recommendation**: Configure throttling on each API Gateway: add `deployOptions` with rate/burst limits. Create usage plans for different consumer tiers. Add WAF with rate-based rules for DDoS protection. Cost: WAF is $5/ACL/month + $1/rule/month — minimal compared to the potential cost of a denial-of-wallet attack.

#### SEC-Q6: PII Redaction
- **Score**: 1/4 ❌
- **Finding**: Error responses in all three handlers include `e.stack` (full error stack traces exposed to API consumers). All handlers log full request bodies with `console.log("request:", JSON.stringify(event, undefined, 2))`, which includes PII data: email, address, cardInfo (from checkout payload), and userName. No log scrubbing, no PII masking, no Macie integration.
- **Gap**: PII is logged in plaintext (email, address, payment card info from checkout events). Error stack traces are exposed to clients. No PII detection or redaction.
- **Recommendation**: Remove `errorStack` from error responses (only return in non-production). Add PII masking to log statements — redact email, address, and cardInfo fields before logging. Non-compliance with PCI-DSS for card data logging can result in substantial fines.

#### SEC-Q7: Human Approval Workflows
- **Score**: 1/4 ❌
- **Finding**: No approval workflows for any operation. `DELETE /product/{id}` and `DELETE /basket/{userName}` are directly executable without confirmation. Checkout (`POST /basket/checkout`) processes immediately without verification. No Step Functions human approval tasks, no manual gates.
- **Gap**: No human approval for destructive or high-value operations.
- **Recommendation**: Low priority for cost-optimization unless business risk of accidental deletions is high. Consider adding confirmation steps for bulk operations if they are added in the future.

#### SEC-Q8: Encryption at Rest
- **Score**: 2/4 🟠
- **Finding**: DynamoDB tables encrypt data at rest by default using AWS-owned keys (free). No customer-managed KMS keys (`encryption` property not set in `lib/database.ts`). No explicit encryption configuration on any resource.
- **Gap**: Using AWS-owned encryption (free) rather than customer-managed KMS keys. For cost-optimization, AWS-owned encryption is actually the most cost-effective choice.
- **Recommendation**: AWS-owned encryption is appropriate for cost-optimization. Only add customer-managed KMS keys ($1/key/month + $0.03/10K requests) if regulatory requirements mandate it. Current setup is cost-optimal.

#### SEC-Q9: API Authentication
- **Score**: 1/4 ❌
- **Finding**: No authorizers on any API Gateway endpoint in `lib/apigateway.ts`. All three APIs (Product, Basket, Order) are publicly accessible. No Cognito authorizer, no Lambda authorizer, no IAM authorization, no API keys. Any internet user can invoke any endpoint.
- **Gap**: Complete absence of authentication. Public APIs with write access (POST, PUT, DELETE) are a critical cost and security risk.
- **Recommendation**: Add Cognito User Pool authorizer to all endpoints. At minimum, add API keys with usage plans to track and limit access. Unauthenticated write APIs are the single highest cost risk in this application.

#### SEC-Q10: Centralized Identity
- **Score**: 1/4 ❌
- **Finding**: No identity provider configured. No Amazon Cognito, no Okta, no SAML/OIDC federation, no SSO. No user management of any kind.
- **Gap**: No centralized identity. User identity (`userName`) is self-asserted by API callers.
- **Recommendation**: Deploy Amazon Cognito User Pool with the CDK stack. Cognito's free tier (50,000 MAU) covers significant usage before costs begin — cost-effective for establishing identity.

### Operations & Observability

#### OPS-Q1: Distributed Tracing
- **Score**: 1/4 ❌
- **Finding**: No distributed tracing. No AWS X-Ray configuration, no OpenTelemetry SDK, no tracing libraries in any `package.json`. No trace ID propagation between services. The EventBridge → SQS → Lambda chain has no correlation mechanism — a checkout event cannot be traced from basket to ordering service.
- **Gap**: Zero tracing capability across the three-service event-driven architecture.
- **Recommendation**: Enable X-Ray on Lambda functions by adding `tracing: Tracing.ACTIVE` in `lib/microservice.ts`. This is a one-line CDK change with minimal cost (~$5/million traces). X-Ray enables identification of slow DynamoDB queries and failed events that waste compute costs.

#### OPS-Q2: Structured Logging
- **Score**: 1/4 ❌
- **Finding**: All logging uses `console.log()` and `console.error()` with unstructured string messages. Example from `src/product/index.js`: `console.log("request:", JSON.stringify(event, undefined, 2))`. No JSON log formatters, no correlation IDs, no log levels beyond console.log/error. No structlog, no winston, no pino.
- **Gap**: Unstructured logs make it impossible to query, filter, or correlate across services in CloudWatch Logs Insights. Debugging cross-service issues requires manually correlating timestamps.
- **Recommendation**: Add Powertools for AWS Lambda Logger (Node.js) for structured JSON logging with automatic correlation IDs, service name, and cold start detection. Enables CloudWatch Logs Insights queries for cost analysis (e.g., identify most-invoked functions).

#### OPS-Q3: Automated Evals
- **Score**: 1/4 ❌
- **Finding**: No evaluation framework. No scoring scripts, no golden datasets, no LLM assertions. No AI components exist in the application.
- **Gap**: No automated eval capability. Not currently needed as there are no AI components.
- **Recommendation**: Not a priority until AI/agent capabilities are introduced. Low relevance for cost-optimization goal.

#### OPS-Q4: SLOs
- **Score**: 1/4 ❌
- **Finding**: No SLO definitions anywhere. No CloudWatch alarms, no error budget tracking, no SLO dashboards. No `aws_cloudwatch_metric_alarm` or equivalent in CDK.
- **Gap**: No SLOs means no measurable reliability targets and no alerts when service quality degrades.
- **Recommendation**: Define SLOs for each API: p99 latency < 1s, error rate < 1%, availability > 99.9%. Add CloudWatch alarms for Lambda errors, API Gateway 5xx rates, and SQS DLQ depth. Alerts prevent prolonged outages that cost revenue.

#### OPS-Q5: Rollback Capability
- **Score**: 1/4 ❌
- **Finding**: No rollback mechanism. No CI/CD pipeline means no automated rollback triggers. No blue/green or canary deployment configuration. No Lambda versioning or aliases configured. Manual `cdk deploy` is the only deployment method.
- **Gap**: Failed deployments require manual intervention. No ability to quickly revert to a previous working version.
- **Recommendation**: Configure Lambda aliases with weighted traffic shifting via CDK. Add `currentVersion` and alias configuration to Lambda functions. Integrate with CodeDeploy for automatic rollback on CloudWatch alarm trigger.

#### OPS-Q6: LLM Cost Tracking
- **Score**: 1/4 ❌
- **Finding**: No LLM usage, no token tracking, no AI cost attribution.
- **Gap**: No LLM cost tracking. Not applicable as there are no AI components.
- **Recommendation**: Not a priority for cost-optimization. Implement when AI services are adopted — Bedrock provides per-request cost attribution natively.

#### OPS-Q7: Business Metrics
- **Score**: 1/4 ❌
- **Finding**: No custom CloudWatch metrics published. No business outcome tracking (orders placed, checkout conversion rate, revenue per transaction). Only default Lambda metrics (invocations, errors, duration) are available.
- **Gap**: No business metrics. Cannot correlate infrastructure costs to business outcomes.
- **Recommendation**: Publish custom CloudWatch metrics from Lambda handlers: `OrdersPlaced`, `CheckoutRevenue`, `BasketSize`. Enable cost-per-transaction analysis by correlating business metrics with Lambda cost metrics.

#### OPS-Q8: Anomaly Detection
- **Score**: 1/4 ❌
- **Finding**: No anomaly detection. No CloudWatch anomaly detection alarms, no error rate alerts, no latency monitoring. No PagerDuty, OpsGenie, or SNS alerting integration.
- **Gap**: No alerting of any kind. Cost anomalies, error spikes, and service degradation go completely undetected.
- **Recommendation**: Enable CloudWatch anomaly detection on Lambda invocation count and DynamoDB consumed capacity. Set billing alarms on the AWS account. Anomaly detection catches cost spikes early — a DynamoDB Scan bug could consume massive read capacity without anyone knowing.

#### OPS-Q9: Deployment Strategy
- **Score**: 1/4 ❌
- **Finding**: No deployment strategy. No blue/green, no canary, no traffic shifting. Deployment is manual `cdk deploy` as documented in `README.md`. No CodeDeploy integration. No feature flags.
- **Gap**: Direct-to-production deployments with no gradual rollout or automated rollback.
- **Recommendation**: Add Lambda aliases with CodeDeploy linear/canary deployment configuration. Example: deploy new version to 10% of traffic, monitor error rate, automatically roll back if errors exceed threshold. Prevents full-production outages from bad deployments.

#### OPS-Q10: Integration Testing
- **Score**: 1/4 ❌
- **Finding**: Test file exists at `test/aws-microservices.test.ts` but all test logic is commented out. The test contains only an empty `test('SQS Queue Created', () => {})` assertion that does nothing. Jest is configured (`jest.config.js`) but no functional tests exist. No API integration tests, no contract tests, no end-to-end tests.
- **Gap**: Zero functional tests. The test infrastructure exists (Jest configured) but contains no actual tests.
- **Recommendation**: Uncomment and fix the CDK infrastructure test. Add unit tests for each Lambda handler. Add API integration tests using tools like `supertest` or Postman/Newman. Untested code increases deployment failure risk and associated recovery costs.

#### OPS-Q11: Incident Response Automation
- **Score**: 1/4 ❌
- **Finding**: No runbooks, no SSM Automation documents, no remediation Lambda functions, no incident response workflows. No self-healing patterns.
- **Gap**: No incident response automation. Manual incident response increases mean-time-to-resolve (MTTR) and associated costs.
- **Recommendation**: Create basic runbooks for common scenarios: Lambda throttling, DynamoDB throttling, SQS DLQ accumulation. Automate SQS DLQ replay. Low priority for cost-optimization — focus on alerting (OPS-Q8) first.

#### OPS-Q12: Observability Governance & Ownership
- **Score**: 1/4 ❌
- **Finding**: No observability ownership model. No CODEOWNERS file, no SLO definition files, no platform team tooling. No per-service dashboards or alarms.
- **Gap**: No observability governance. No ownership of monitoring or reliability for any service.
- **Recommendation**: Assign service ownership per microservice. Create CDK constructs for standard observability per Lambda function (dashboard + alarms). Establish a simple SLO framework. This is a governance prerequisite before scaling the service count.

---

## Recommended Modernization Pathways

Based on the assessment findings, the following AWS Modernization Pathways are evaluated for this application. Multiple pathways can execute in parallel because modern applications comprise multiple interconnected components — each requiring its own modernization approach.

### Pathway Summary

| Pathway | Status | Goal Alignment | Priority | Key Trigger Criteria | Est. Effort |
|---------|--------|---------------|----------|---------------------|-------------|
| Move to Cloud Native | Not Triggered | Low | — | — | — |
| Move to Containers | Not Triggered | Medium | — | — | — |
| Move to Open Source | Not Triggered | High | — | — | — |
| Move to Managed Databases | Not Triggered | High | — | — | — |
| Move to Managed Analytics | Not Triggered | High | — | — | — |
| Move to Modern DevOps | Triggered | Medium | High | INF-Q6: 1/4, OPS-Q9: 1/4, OPS-Q10: 1/4, OPS-Q1: 1/4 | Medium |
| Move to AI | Triggered | Low | Low | APP-Q13: 1/4, DATA-Q1: 1/4, DATA-Q3: 1/4, OPS-Q3: 1/4 | Medium |

### Parallel Execution Plan

**Parallel Track 1**: Move to Modern DevOps — can begin immediately, no dependencies on other pathways. CI/CD, testing, observability, and deployment strategies are all independent improvements.

**Parallel Track 2**: Move to AI — can begin after Modern DevOps foundations are in place (CI/CD needed to safely deploy AI features).

**Sequential Dependencies**: Move to AI benefits from Move to Modern DevOps completing first (Phase 1) — CI/CD and observability should be in place before adding AI service integrations that introduce new cost vectors (Bedrock API calls, token usage).

### Move to Modern DevOps

- **Priority**: High
- **Goal Alignment**: Medium
- **Trigger Criteria Met**:
  - INF-Q6: Score 1/4 — No CI/CD pipeline exists; deployment is manual `cdk deploy`
  - OPS-Q9: Score 1/4 — No deployment strategy; no blue/green or canary deployments
  - OPS-Q10: Score 1/4 — No integration tests; test file exists but all assertions are commented out
  - OPS-Q1: Score 1/4 — No distributed tracing; no X-Ray or OpenTelemetry
- **Current State**: All infrastructure is defined in CDK (strong IaC foundation), but there is zero CI/CD automation, no testing, no deployment strategy, no tracing, and no observability. Deployments are manual and untested.
- **Target State**: Automated CI/CD pipeline with lint → test → diff → deploy stages, canary deployments with automatic rollback, integration test suites, X-Ray distributed tracing across all three microservices, and structured logging with CloudWatch dashboards.
- **Key Activities**:
  1. Create CI/CD pipeline (GitHub Actions or CodePipeline) with automated test, build, and deploy stages
  2. Enable X-Ray tracing on all Lambda functions (one-line CDK change per function)
  3. Add structured logging with Powertools for AWS Lambda
  4. Implement Lambda alias-based canary deployments with CodeDeploy
  5. Write CDK infrastructure tests and Lambda handler unit tests
  6. Add CloudWatch alarms for error rates, latency, and DynamoDB capacity
  7. Set CloudWatch Logs retention policies to control storage costs
- **Dependencies**: None — can begin immediately
- **Estimated Effort**: Medium
- **Roadmap Phase Alignment**: Phase 1 (CI/CD, tracing, logging) and Phase 2 (deployment strategies, testing, alarms)
- **Relevant Learning Materials**: Module 6 — Move to Modern DevOps

### Move to AI

- **Priority**: Low
- **Goal Alignment**: Low
- **Trigger Criteria Met**:
  - APP-Q13: Score 1/4 — No AI/agent frameworks in any dependency manifest
  - DATA-Q1: Score 1/4 — No vector database for semantic search
  - DATA-Q3: Score 1/4 — No RAG implementation
  - OPS-Q3: Score 1/4 — No automated evaluation framework
  - OPS-Q6: Score 1/4 — No LLM cost tracking
- **Current State**: No AI capabilities exist. The application is a traditional CRUD e-commerce system with no machine learning, no embeddings, no semantic search, and no agent integration.
- **Target State**: AI-enhanced product search (semantic), conversational checkout assistant, and operational AI for anomaly detection. All with cost tracking and evaluation frameworks.
- **Key Activities**:
  1. Evaluate specific AI use cases that deliver ROI (e.g., product search improvement, customer support automation)
  2. Add Amazon Bedrock SDK to Lambda functions for targeted AI features
  3. Implement vector search for product catalog using OpenSearch Serverless (if semantic search ROI is justified)
  4. Add LLM cost tracking via CloudWatch custom metrics for token usage attribution
  5. Establish evaluation framework before deploying AI features to production
- **Dependencies**: Move to Modern DevOps (CI/CD and observability should be in place before adding AI cost vectors)
- **Estimated Effort**: Medium
- **Roadmap Phase Alignment**: Phase 3 (Optimization & Governance)
- **Relevant Learning Materials**: Module 7 — Move to AI

---

## Readiness Roadmap

### Phase 1 — License & Quick Savings (Days 1–30)

These are high-impact, low-effort changes that deliver immediate cost savings and risk reduction:

1. **Upgrade Lambda Runtime to Node.js 20.x + ARM64/Graviton** — Update `runtime: Runtime.NODEJS_14_X` to `Runtime.NODEJS_20_X` and add `architecture: Architecture.ARM_64` in `lib/microservice.ts` for all three functions. **Saves ~20% on Lambda compute costs** and eliminates EOL runtime risk. Effort: 1 day.

2. **Add API Gateway Throttling** — Add `deployOptions: { throttlingRateLimit: 100, throttlingBurstLimit: 200 }` to each `LambdaRestApi` in `lib/apigateway.ts`. **Prevents denial-of-wallet attacks** that could cause unbounded Lambda and DynamoDB costs. Effort: 1 day.

3. **Set CloudWatch Logs Retention** — Add `logRetention: RetentionDays.ONE_MONTH` to Lambda function definitions to prevent indefinite log accumulation. **Stops silently growing CloudWatch Logs storage costs.** Effort: 1 hour.

4. **Enable X-Ray Tracing** — Add `tracing: Tracing.ACTIVE` to all Lambda functions in `lib/microservice.ts`. **Enables identification of slow DynamoDB queries and failed events** that waste compute costs. Effort: 1 hour.

5. **Add Structured Logging** — Add Powertools for AWS Lambda Logger to each microservice's `package.json`. Replace `console.log` with structured JSON logging. **Enables CloudWatch Logs Insights queries for cost analysis.** Effort: 2-3 days.

6. **Remove Error Stack Traces from API Responses** — Remove `errorStack: e.stack` from error responses in all three handlers. **Eliminates security risk and reduces response payload sizes.** Effort: 1 hour.

7. **Set Lambda Reserved Concurrency** — Add `reservedConcurrentExecutions` to Lambda functions to cap maximum concurrent executions. **Prevents runaway Lambda scaling costs.** Effort: 1 hour.

### Phase 2 — Managed Service Migration (Months 1–3)

Structural improvements that require more planning but deliver significant operational and cost benefits:

1. **Create CI/CD Pipeline** — Implement GitHub Actions or AWS CodePipeline with stages: `npm install` → `npm test` → `cdk diff` → manual approval → `cdk deploy`. Add cost estimation via `cdk diff` output review. **Reduces deployment failure risk and enables cost-governance checks.**

2. **Add API Authentication (Cognito)** — Deploy Amazon Cognito User Pool via CDK. Add `CognitoUserPoolsAuthorizer` to all API Gateway endpoints in `lib/apigateway.ts`. Map `userName` from JWT token claims. **Eliminates unauthorized API access cost risk.** Cognito free tier covers 50,000 MAU.

3. **DynamoDB Capacity Optimization Analysis** — Analyze DynamoDB usage patterns using CloudWatch metrics (after Phase 1 enables observability). If traffic patterns are predictable, switch from `PAY_PER_REQUEST` to provisioned capacity with auto-scaling for tables with steady traffic. **Can reduce DynamoDB costs by 50-70%** for predictable workloads.

4. **Add SQS Dead-Letter Queue** — Add DLQ to `OrderQueue` in `lib/queue.ts`. **Prevents silent order loss and the associated customer service costs.**

5. **Implement CDK Infrastructure Tests** — Uncomment and expand the test in `test/aws-microservices.test.ts`. Add assertions for all resources. Write unit tests for Lambda handlers. **Reduces deployment failure costs.**

6. **Add CloudWatch Alarms** — Create alarms for Lambda errors, API Gateway 5xx rates, DynamoDB throttling, SQS DLQ depth, and AWS billing thresholds. **Catches cost anomalies early.**

7. **Increase SQS Batch Size** — Change `batchSize: 1` to `batchSize: 10` in `lib/queue.ts` for the ordering Lambda event source. **Reduces Lambda invocation count and costs** for checkout processing.

### Phase 3 — Optimization & Governance (Months 3–6)

Advanced capabilities that establish cost governance and optimize the fully operational system:

1. **DynamoDB Query Optimization** — Replace `ScanCommand` with `QueryCommand` using Global Secondary Indexes (GSIs) for `getAllProducts()` and `getAllBaskets()` operations. **Reduces DynamoDB read capacity consumption** from full-table scans.

2. **Implement SLOs and Error Budgets** — Define SLOs (p99 latency, error rate, availability) for each microservice. Create CloudWatch dashboards. **Enables cost-vs-quality tradeoff decisions.**

3. **Add Business Metrics** — Publish custom CloudWatch metrics: `OrdersPlaced`, `CheckoutRevenue`, `AverageBasketSize`. **Enables cost-per-transaction analysis** and ROI measurement.

4. **Implement Canary Deployments** — Add Lambda aliases with CodeDeploy canary deployment configuration. **Prevents full-outage deployment failures** that cost revenue.

5. **Add AWS Billing Anomaly Detection** — Configure AWS Cost Anomaly Detection for the account. Set up alerts for unexpected spending increases. **Provides automated cost governance.**

6. **Schema Documentation** — Create formal JSON Schema definitions for DynamoDB table schemas. Document PII fields. **Prevents compliance-related costs and enables future data migration planning.**

7. **Evaluate AI Use Cases** — Based on 3 months of operational data, evaluate whether AI features (product search, recommendations) deliver ROI sufficient to justify Bedrock API costs. **Ensure AI investments are cost-justified.**

---

## Recommended Self-Paced Learning Materials

### Module 6: Move to Modern DevOps
*Highest priority — addresses the most critical gaps in CI/CD, observability, testing, and deployment strategy.*

- **AWS Modernization Pathways: Move to Modern DevOps** — https://skillbuilder.aws/learning-plan/1FGEQKGPQD/aws-modernization-pathways-move-to-modern-devops-includes-labs/MNQZ2KPVCK
  - Comprehensive learning path covering CI/CD, IaC, testing, and deployment strategies — directly addresses INF-Q6, OPS-Q9, OPS-Q10 gaps.
- **Getting Started with DevOps on AWS** — https://skillbuilder.aws/learn/R4B13K95YQ/getting-started-with-devops-on-aws/38NHHYRV1R
  - Foundation course for establishing DevOps practices — relevant for teams new to CI/CD automation.
- **Create a CI/CD Pipeline to Deploy Your App to AWS Fargate (ECS)** — https://skillbuilder.aws/learn/H61B17Z8R7/create-a-cicd-pipeline-to-deploy-your-app-to-aws-fargate/T66BGGGHV5
  - Hands-on lab for CI/CD pipeline creation — applicable patterns for Lambda deployment pipelines.
- **AWS CloudFormation Getting Started** — https://skillbuilder.aws/learn/RH22P2RXU4/aws-cloudformation-getting-started/KEK5BT6HSE
  - Understanding CloudFormation underpins CDK usage — helps teams understand what CDK generates.
- **Advanced Testing Practices Using AWS DevOps Tools** — https://skillbuilder.aws/learn/1YC7UXUWBR/advanced-testing-practices-using-aws-devops-tools/A32U6G7NEQ
  - Addresses the testing gap (OPS-Q10) with practical testing strategies for AWS applications.
- **Monitor Python Applications Using Amazon CloudWatch Application Signals** — https://skillbuilder.aws/learn/JMPDZD64MV/monitor-python-applications-using-amazon-cloudwatch-application-signals/2JP3J2MPCK
  - Observability patterns applicable to Node.js applications — addresses OPS-Q1, OPS-Q2, OPS-Q4 gaps.
- **AWS Developer: CI/CD Automation** — https://skillbuilder.aws/learn/C1KF8ZJ1D8/aws-developer--cicd-automation/KY1E1JS9FA
  - Detailed CI/CD automation course — directly addresses INF-Q6 gap.

### Module 2: Move to Cloud Native (Containers and Serverless)
*Relevant for deepening serverless architecture skills and understanding Cloud Design Patterns for the existing architecture.*

- **Cloud Design Patterns, Architectures, and Implementations** — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html
  - Essential reference for patterns applicable to the current serverless architecture: Circuit Breaker, Retry with Backoff, Event Sourcing — addresses APP-Q9 resilience gap.
- **Lambda Foundations** — https://skillbuilder.aws/learn/XHRS91KKK6/aws-lambda-foundations/R85JRN3APC
  - Core Lambda concepts — helps optimize runtime configuration, concurrency, and cost for the existing Lambda functions.
- **Amazon API Gateway for Serverless Applications** — https://skillbuilder.aws/learn/GQA6FHWPJD/amazon-api-gateway-for-serverless-applications/JVRZ3PSW4H
  - Covers API Gateway throttling, authorization, and usage plans — directly addresses INF-Q7, APP-Q8, SEC-Q5, SEC-Q9 gaps.
- **Amazon DynamoDB for Serverless Architecture** — https://skillbuilder.aws/learn/SY1Y83VKTB/amazon-dynamodb-for-serverless-architectures/K9NM3PHH3S
  - DynamoDB optimization patterns — addresses cost optimization for DynamoDB capacity, query patterns, and GSI design.

### Module 7: Move to AI
*Lower priority — relevant for Phase 3 when AI use cases are evaluated.*

- **AWS Modernization Pathways: Move to AI** — https://skillbuilder.aws/learning-plan/VDFEE4ACCV/aws-modernization-pathways-move-to-ai-pathways-includes-labs/P3DAWPTN63
  - Overview of AI integration pathways — relevant when evaluating AI ROI in Phase 3.
- **Amazon Bedrock Getting Started** — https://skillbuilder.aws/learn/63KTRM86DQ/amazon-bedrock-getting-started/SC2Y3HMAUE
  - Foundation for understanding Bedrock pricing and capabilities — helps evaluate cost impact before committing to AI features.
- **Planning a Generative AI Project** — https://skillbuilder.aws/learn/HU1FQRGDDZ/planning-a-generative-ai-project/SYR3SCPSHC
  - Project planning for AI initiatives — ensures AI investments are cost-justified with clear ROI targets.

---

## Appendix: Evidence Index

| # | File | Key Finding |
|---|------|-------------|
| 1 | `lib/microservice.ts` | All Lambda functions use `Runtime.NODEJS_14_X` (EOL); no ARM64 architecture; `grantReadWriteData()` for all functions |
| 2 | `lib/database.ts` | 3 DynamoDB tables with `BillingMode.PAY_PER_REQUEST` and `RemovalPolicy.DESTROY`; schema documented in comments only |
| 3 | `lib/apigateway.ts` | 3 `LambdaRestApi` instances with no throttling, no auth, no request validation, no usage plans |
| 4 | `lib/eventbus.ts` | EventBridge `SwnEventBus` with `CheckoutBasketRule` routing to SQS; `grantPutEventsTo()` for basket function |
| 5 | `lib/queue.ts` | SQS `OrderQueue` with `visibilityTimeout: 30s`, `batchSize: 1`, no DLQ configured |
| 6 | `lib/aws-microservices-stack.ts` | Single CDK stack orchestrating all constructs; clean dependency injection pattern |
| 7 | `src/product/index.js` | CRUD handler with `ScanCommand` for list (cost concern), `PutItemCommand` without idempotency, error stacks exposed |
| 8 | `src/basket/index.js` | Checkout workflow: `getBasket → prepareOrderPayload → publishCheckoutBasketEvent → deleteBasket`; no error recovery |
| 9 | `src/ordering/index.js` | Handles SQS + EventBridge + API Gateway invocations; creates orders with `new Date().toISOString()` sort key (duplicate risk) |
| 10 | `src/product/ddbClient.js` | 4-line DynamoDB client module — identical across all 3 services |
| 11 | `src/basket/eventBridgeClient.js` | EventBridge client instantiation — used for checkout event publishing |
| 12 | `src/product/package.json` | `@aws-sdk/client-dynamodb@^3.55.0`, `@aws-sdk/util-dynamodb@^3.55.0` — AWS SDK v3 |
| 13 | `src/basket/package.json` | Adds `@aws-sdk/client-eventbridge@^3.58.0` for EventBridge integration |
| 14 | `src/ordering/package.json` | `@aws-sdk/client-dynamodb@^3.58.0` — slightly different SDK version than product service |
| 15 | `package.json` | CDK `aws-cdk-lib@2.17.0` (significantly outdated); `aws-cdk@2.17.0` dev dependency |
| 16 | `cdk.json` | CDK app configuration; feature flags for CDK construct behavior |
| 17 | `bin/aws-microservices.ts` | CDK app entry point; environment not specified (environment-agnostic stack) |
| 18 | `test/aws-microservices.test.ts` | All test assertions commented out; empty test body; Jest configured but non-functional |
| 19 | `README.md` | Documents manual `cdk deploy` workflow; no CI/CD instructions; references Docker Desktop requirement |
| 20 | `src/basket/checkoutbasketevents.json` | Sample EventBridge event payloads for testing checkout flow — not used in code |
