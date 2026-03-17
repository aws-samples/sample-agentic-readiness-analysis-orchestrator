# Agentic Readiness Assessment Report

**Target**: goal-agentic-readiness/services/aws-microservices
**Date**: 2026-03-17
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Assessment Goal**: agentic-readiness
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
6. Quick Agent Wins
7. Readiness Roadmap
   - Phase 1 — Quick Wins (Days 1–30)
   - Phase 2 — Foundation (Months 1–3)
   - Phase 3 — Advanced Capabilities (Months 3–6)
8. Recommended Self-Paced Learning Materials
9. Appendix: Evidence Index

---

## Executive Summary

This serverless e-commerce microservices application demonstrates a solid foundation in modern compute and data architecture — 100% Lambda-based serverless compute, fully managed DynamoDB databases, and event-driven decoupling via EventBridge and SQS, all defined as Infrastructure as Code using AWS CDK. However, the application has critical gaps across operations, security, and AI readiness that must be addressed before it can support agentic workloads. The operations category scores 1.0/4.0 with zero observability, no CI/CD pipeline, and no testing — the lowest of any category. Security is equally concerning at 1.4/4.0 with no API authentication, no identity propagation, and no audit logging. No AI/agent frameworks, vector databases, or RAG capabilities are present. The strong serverless and event-driven foundations provide an excellent starting point for modernization, but significant investment is needed in DevOps, security, and AI enablement.

### Overall Score: 1.73 / 4.0

| Category | Score | Status |
|----------|-------|--------|
| Infrastructure & Platform | 2.5 / 4.0 | 🟡 |
| Application Architecture | 1.85 / 4.0 | 🟠 |
| Data Foundations | 1.91 / 4.0 | 🟠 |
| Identity, Security & Governance | 1.4 / 4.0 | ❌ |
| Operations & Observability | 1.0 / 4.0 | ❌ |

## Top Priorities (Critical Gaps)

### 1. Zero Operations & Observability (Category Score: 1.0/4.0)
All 12 operations criteria score 1/4. There is no distributed tracing (no X-Ray or OpenTelemetry), no structured logging (only unstructured `console.log`), no CI/CD pipeline, no integration tests, no CloudWatch alarms, no deployment strategy beyond manual `cdk deploy`, and no incident response automation. **Why it matters for agentic readiness**: Agent workflows span multiple Lambda functions, DynamoDB tables, EventBridge, and SQS — without end-to-end tracing and structured logging, debugging agent failures is impossible. **First step**: Add AWS X-Ray tracing to all Lambda functions via CDK and implement structured JSON logging with correlation IDs using a lightweight logging library.

### 2. No API Authentication (SEC-Q9: 1/4)
All three API Gateway endpoints (Product, Basket, Order) are publicly accessible with no authentication. No API Gateway authorizers, no Cognito integration, no API keys, and no JWT validation are configured in `lib/apigateway.ts`. **Why it matters for agentic readiness**: Agents making API calls must authenticate; unauthenticated APIs are exploitable and cannot track which agent or user is making requests. **First step**: Add a Cognito User Pool authorizer or Lambda authorizer to all API Gateway endpoints in `lib/apigateway.ts`.

### 3. No CI/CD Pipeline (INF-Q6: 1/4)
No CI/CD pipeline definitions exist — no `.github/workflows/`, no `buildspec.yml`, no `Jenkinsfile`, no CodePipeline in CDK. Deployment is manual via `cdk deploy`. **Why it matters for agentic readiness**: Agent systems require rapid, safe iteration with automated testing and deployment; manual deployments cannot support the velocity needed for prompt tuning, tool updates, and model version upgrades. **First step**: Create a GitHub Actions workflow or AWS CodePipeline definition with lint, test, `cdk synth`, and `cdk deploy` stages.

### 4. No API Documentation (APP-Q2: 1/4)
No OpenAPI/Swagger specifications exist for any of the three APIs (Product, Basket, Order). No `openapi.yaml`, `swagger.json`, or API documentation annotations found. API routes are defined only in `lib/apigateway.ts` code. **Why it matters for agentic readiness**: Agents need machine-readable API specifications to discover and invoke tools. Without OpenAPI specs, agents cannot auto-discover available endpoints or understand request/response schemas. **First step**: Generate OpenAPI 3.0 specifications for all three APIs documenting routes, request bodies, and response schemas.

### 5. No Identity Propagation (SEC-Q3: 1/4)
No JWT, OAuth2, or Cognito integration exists. User identity (`userName`) is passed as a URL path parameter (e.g., `/basket/{userName}`, `/order/{userName}`) with no authentication or verification. No token exchange between services. **Why it matters for agentic readiness**: Agents acting on behalf of users must propagate authenticated identity end-to-end to ensure actions are authorized and auditable. Path-parameter-based user identification is trivially spoofable. **First step**: Implement Cognito or an OIDC provider with JWT tokens, and extract user identity from the token in Lambda handlers instead of path parameters.

## Detailed Findings

### Infrastructure & Platform

#### INF-Q1: Compute
- **Score**: 4/4 ✅
- **Finding**: All compute is 100% AWS Lambda (serverless). Three `NodejsFunction` constructs are defined in `lib/microservice.ts` using `Runtime.NODEJS_14_X` — one each for product, basket, and ordering microservices. No EC2 instances, ECS tasks, or EKS clusters are used.
- **Gap**: The Lambda runtime `NODEJS_14_X` is end-of-life (EOL'd November 2023). While compute is fully serverless, the runtime version is outdated and no longer receives security patches.
- **Recommendation**: Upgrade Lambda runtime from `NODEJS_14_X` to `NODEJS_20_X` or later in `lib/microservice.ts`. This is a single-line change per function and should be done immediately.

#### INF-Q2: Databases
- **Score**: 4/4 ✅
- **Finding**: All three databases are Amazon DynamoDB tables defined in `lib/database.ts` — `product` (PK: id), `basket` (PK: userName), and `order` (PK: userName, SK: orderDate). All use `BillingMode.PAY_PER_REQUEST` (on-demand). Fully managed with automated failover and no operational overhead.
- **Gap**: None. All databases are fully managed services.
- **Recommendation**: No action needed for database management. Consider enabling DynamoDB point-in-time recovery (PITR) for production workloads.

#### INF-Q3: Workflow Orchestration
- **Score**: 1/4 ❌
- **Finding**: No dedicated workflow orchestration service found. No Step Functions, Temporal, Camunda, or workflow engine. The checkout workflow is hardcoded in `src/basket/index.js` as a sequence: `getBasket()` → `prepareOrderPayload()` → `publishCheckoutBasketEvent()` → `deleteBasket()`. This is imperative code, not a declarative workflow.
- **Gap**: No workflow orchestration for multi-step business processes. The checkout flow has no error handling for partial failures (e.g., if event publish succeeds but basket delete fails).
- **Recommendation**: Implement AWS Step Functions for the checkout workflow. Define a state machine that orchestrates basket retrieval, order event publishing, and basket cleanup with error handling, retries, and compensation logic.

#### INF-Q4: Async Messaging
- **Score**: 4/4 ✅
- **Finding**: Two managed messaging services are in use: Amazon EventBridge (custom bus `SwnEventBus` defined in `lib/eventbus.ts`) and Amazon SQS (`OrderQueue` defined in `lib/queue.ts`). EventBridge rules route `CheckoutBasket` events from the basket service to the SQS queue, which triggers the ordering Lambda. The basket Lambda publishes events via `PutEventsCommand` in `src/basket/index.js`.
- **Gap**: None. Async messaging is fully managed.
- **Recommendation**: No action needed. Consider adding a Dead Letter Queue (DLQ) to the SQS queue for failed message processing.

#### INF-Q5: Infrastructure as Code
- **Score**: 4/4 ✅
- **Finding**: 100% of infrastructure is defined in AWS CDK (TypeScript) across six files in `lib/`: `aws-microservices-stack.ts` (orchestrator), `database.ts` (DynamoDB tables), `microservice.ts` (Lambda functions), `apigateway.ts` (API Gateway), `eventbus.ts` (EventBridge), and `queue.ts` (SQS). The CDK entry point is `bin/aws-microservices.ts`. All compute, databases, messaging, and API Gateway are fully covered.
- **Gap**: None. IaC coverage is comprehensive.
- **Recommendation**: No action needed for IaC coverage. Consider adding CDK tags for cost allocation and environment identification.

#### INF-Q6: CI/CD
- **Score**: 1/4 ❌
- **Finding**: No CI/CD pipeline definitions found. No `.github/workflows/` directory, no `buildspec.yml`, no `Jenkinsfile`, no `.gitlab-ci.yml`, no CodePipeline or CodeBuild resources in CDK. The only deployment method is manual `cdk deploy` as documented in `README.md`.
- **Gap**: Entirely missing CI/CD automation. No automated testing, building, or deployment.
- **Recommendation**: Implement a CI/CD pipeline using GitHub Actions or AWS CodePipeline. Define stages for linting, unit testing, `cdk synth` (synthesis validation), and `cdk deploy` with environment-specific stacks (dev, staging, prod).

#### INF-Q7: API Entry Point
- **Score**: 2/4 🟠
- **Finding**: API Gateway is present — three `LambdaRestApi` constructs in `lib/apigateway.ts` (Product Service, Basket Service, Order Service) with `proxy: false` and explicit route definitions. Routes include GET/POST/PUT/DELETE for product, GET/POST/DELETE for basket, POST for basket/checkout, and GET for order.
- **Gap**: No throttling configuration, no authentication/authorization, and no request validation on any API Gateway. The APIs are created with CDK defaults — no usage plans, no API keys, no WAF integration.
- **Recommendation**: Add throttling via `deployOptions` with `throttlingRateLimit` and `throttlingBurstLimit`. Add request validators for POST/PUT endpoints. Integrate a Cognito authorizer or Lambda authorizer for authentication.

#### INF-Q8: Real-time Streaming
- **Score**: 1/4 ❌
- **Finding**: No real-time streaming services found. No Amazon Kinesis Data Streams, Kinesis Data Firehose, or Amazon MSK. EventBridge and SQS are used for event-driven messaging but are not streaming services.
- **Gap**: No streaming capability for real-time data processing.
- **Recommendation**: If real-time analytics or streaming use cases emerge (e.g., real-time inventory tracking, clickstream analysis), implement Amazon Kinesis Data Streams or MSK Serverless. For the current e-commerce use case, this is a lower priority.

#### INF-Q9: Network Security
- **Score**: 1/4 ❌
- **Finding**: No VPC, subnets, security groups, or NACLs defined in any CDK file. Lambda functions in `lib/microservice.ts` have no `vpc` property in `NodejsFunctionProps`, meaning they run in the default Lambda execution environment outside any VPC. DynamoDB is accessed via public AWS endpoints.
- **Gap**: No network segmentation, no private subnets, no security groups. All Lambda functions run outside a VPC with no network-level access controls.
- **Recommendation**: For production workloads handling sensitive data (payment info in orders), deploy Lambda functions inside a VPC with private subnets. Use VPC endpoints for DynamoDB and other AWS services to keep traffic on the AWS network. Add security groups with least-privilege rules.

#### INF-Q10: Auto-scaling
- **Score**: 3/4 🟡
- **Finding**: DynamoDB tables use `BillingMode.PAY_PER_REQUEST` (defined in `lib/database.ts`), which provides automatic scaling. Lambda functions auto-scale by default with AWS-managed concurrency. SQS scales consumers automatically.
- **Gap**: No explicit Lambda reserved or provisioned concurrency limits are configured in `lib/microservice.ts`. No Lambda function concurrency controls to prevent runaway scaling or protect downstream resources.
- **Recommendation**: Configure reserved concurrency on Lambda functions to prevent a single function from consuming all account-level concurrency. Consider provisioned concurrency for latency-sensitive endpoints (product catalog GET).

### Application Architecture

#### APP-Q1: Programming Languages
- **Score**: 3/4 🟡
- **Finding**: JavaScript is used for Lambda handlers (`src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js`) and TypeScript for CDK IaC (`lib/*.ts`). Dependencies include `@aws-sdk/client-dynamodb` and `@aws-sdk/client-eventbridge`. The root `package.json` uses `aws-cdk-lib 2.17.0` with TypeScript `~3.9.7`.
- **Gap**: JavaScript (not TypeScript) is used for Lambda handlers, missing type safety benefits. TypeScript 3.9.7 is significantly outdated (current is 5.x). The JS ecosystem has decent agent framework support (LangChain.js, Vercel AI SDK) but Python remains the stronger ecosystem for AI/agent development.
- **Recommendation**: Migrate Lambda handlers from JavaScript to TypeScript for type safety. Upgrade TypeScript version to 5.x. Consider Python for any new AI/agent-focused services.

#### APP-Q2: API Documentation
- **Score**: 1/4 ❌
- **Finding**: No OpenAPI/Swagger specifications found. No `openapi.yaml`, `swagger.json`, or API documentation files exist anywhere in the repository. API routes are defined only in CDK code (`lib/apigateway.ts`) — Product API has GET/POST/PUT/DELETE, Basket API has GET/POST/DELETE plus POST /checkout, Order API has GET.
- **Gap**: Completely missing API documentation. Agents cannot discover or understand available endpoints and their schemas.
- **Recommendation**: Create OpenAPI 3.0 specifications for all three APIs. Document request/response schemas, path parameters, query parameters (e.g., `category` for products, `orderDate` for orders), and error responses. Use tools like `swagger-jsdoc` or manual YAML authoring.

#### APP-Q3: Async vs Sync Communication
- **Score**: 2/4 🟠
- **Finding**: The checkout flow is async: basket Lambda publishes to EventBridge → SQS → ordering Lambda (defined in `lib/eventbus.ts`, `lib/queue.ts`). All other operations are synchronous: API Gateway → Lambda → DynamoDB (product CRUD, basket CRUD, order queries). Approximately 1 out of ~12 operations is async (~8%).
- **Gap**: Only the checkout operation uses async communication. All CRUD operations are synchronous request-response. The async ratio is well below the 50% threshold for agent-ready.
- **Recommendation**: Identify operations that could benefit from async processing (e.g., bulk product imports, order status updates). Use EventBridge for more inter-service events beyond checkout.

#### APP-Q4: Monolith vs Microservices
- **Score**: 4/4 ✅
- **Finding**: Three independently structured microservices exist: Product (`src/product/`), Basket (`src/basket/`), and Ordering (`src/ordering/`). Each has its own Lambda function, DynamoDB table, `package.json`, and data access client. Services communicate via EventBridge events, not direct calls. The architecture is defined in `lib/aws-microservices-stack.ts` with clear separation of concerns.
- **Gap**: None. Clean microservices architecture with event-driven decoupling.
- **Recommendation**: No decomposition needed. Maintain the current service boundaries. Consider extracting a dedicated checkout service if the checkout workflow grows in complexity.

#### APP-Q5: API Response Format
- **Score**: 4/4 ✅
- **Finding**: All Lambda handlers return structured JSON responses using `JSON.stringify()`. Consistent response format across all services: `{ message: "Successfully finished operation...", body: <data> }` for success, and `{ message: "Failed to perform operation.", errorMsg: <message>, errorStack: <stack> }` for errors. Seen in `src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js`.
- **Gap**: None. All APIs return structured JSON.
- **Recommendation**: Remove `errorStack` from error responses (security concern — exposes internal stack traces). Standardize on a consistent error response schema with error codes.

#### APP-Q6: Workflow Logic
- **Score**: 1/4 ❌
- **Finding**: The checkout workflow in `src/basket/index.js` is hardcoded as sequential function calls: `checkoutBasket()` calls `getBasket()` → `prepareOrderPayload()` → `publishCheckoutBasketEvent()` → `deleteBasket()`. No Step Functions, no workflow engine, no saga pattern. If `publishCheckoutBasketEvent` succeeds but `deleteBasket` fails, the basket remains and the order is duplicated on retry.
- **Gap**: No dedicated workflow orchestration. Business logic is tightly coupled to imperative code with no compensation or rollback for partial failures.
- **Recommendation**: Implement AWS Step Functions for the checkout workflow. Define states for each step with error handling, retries with exponential backoff, and a compensation branch to handle partial failures.

#### APP-Q7: Idempotency
- **Score**: 1/4 ❌
- **Finding**: No idempotency patterns implemented. `PutItemCommand` is used for creates in all three services (`src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js`) — these overwrites existing items without conditional checks. No `Idempotency-Key` headers in API design. No deduplication IDs on SQS messages. The ordering Lambda processes SQS records with `batchSize: 1` (`lib/queue.ts`) but has no deduplication.
- **Gap**: Retry of any write operation can cause data corruption. The checkout flow is especially vulnerable — retrying a checkout can create duplicate orders.
- **Recommendation**: Add conditional writes (ConditionExpression) for DynamoDB PutItem operations. Implement idempotency keys for the checkout flow. Use SQS FIFO queue with deduplication for the order queue, or implement application-level deduplication in the ordering Lambda.

#### APP-Q8: Rate Limiting & Throttling
- **Score**: 1/4 ❌
- **Finding**: No rate limiting configured at any layer. API Gateway in `lib/apigateway.ts` uses `LambdaRestApi` with default settings — no `deployOptions` with throttle configuration, no usage plans, no API keys. No WAF rules. No application-level rate limiting middleware in Lambda handlers.
- **Gap**: APIs are completely unthrottled. A burst of requests could exhaust Lambda concurrency or DynamoDB capacity.
- **Recommendation**: Configure API Gateway throttling via `deployOptions: { throttlingRateLimit: X, throttlingBurstLimit: Y }`. Create usage plans with API keys for programmatic access. Consider adding WAF for DDoS protection.

#### APP-Q9: Resilience Patterns
- **Score**: 1/4 ❌
- **Finding**: No resilience patterns implemented. Lambda handlers in `src/product/index.js`, `src/basket/index.js`, and `src/ordering/index.js` have basic `try/catch` blocks that return 500 errors but no retries, circuit breakers, or timeouts. No resilience libraries (e.g., `cockatiel`, `p-retry`) in any `package.json`. AWS SDK has default retry behavior but no custom configuration.
- **Gap**: No circuit breakers, no explicit retries with backoff, no timeout configurations. External dependency failures (DynamoDB, EventBridge) will cascade without mitigation.
- **Recommendation**: Implement explicit retry logic with exponential backoff for DynamoDB and EventBridge calls. Add timeout configurations to Lambda functions. Consider using the `@middy/core` middleware framework with retry and timeout middlewares.

#### APP-Q10: Long-running Processes
- **Score**: 2/4 🟠
- **Finding**: The checkout operation uses async processing via EventBridge → SQS → ordering Lambda (`lib/eventbus.ts`, `lib/queue.ts`). This is a good pattern for long-running order processing. However, there is no status polling endpoint, no job status API, and no callback mechanism — the client has no way to know when the order was created.
- **Gap**: Async checkout exists but lacks observability. No order status API to check if the async order creation succeeded. The client's `POST /basket/checkout` returns immediately but the client cannot track the outcome.
- **Recommendation**: Add an order status endpoint that allows polling for order completion. Consider implementing WebSocket notifications via API Gateway WebSocket API for real-time order status updates.

#### APP-Q11: API Versioning
- **Score**: 1/4 ❌
- **Finding**: No API versioning strategy. Routes in `lib/apigateway.ts` are `/product`, `/basket`, `/order` with no version prefix (e.g., no `/v1/product`). No `Accept-Version` headers. No changelog files. No versioning annotations.
- **Gap**: No versioning strategy means any breaking API change will break all consumers simultaneously.
- **Recommendation**: Implement URL path versioning (e.g., `/v1/product`) for all API routes. Add API Gateway stage variables for version management. Establish a deprecation policy.

#### APP-Q12: Service Discovery & Mesh
- **Score**: 2/4 🟠
- **Finding**: Services communicate via EventBridge events — the basket service publishes events to `SwnEventBus` using environment variables for the bus name (`EVENT_BUSNAME`, `EVENT_SOURCE`, `EVENT_DETAILTYPE` defined in `lib/microservice.ts`). No hard-coded service URLs for inter-service communication. However, there is no formal service discovery (no AWS Cloud Map, App Mesh, or service registry).
- **Gap**: While event-driven communication avoids hard-coded endpoints, there is no API catalog or service discovery mechanism for direct service-to-service calls if needed.
- **Recommendation**: For the current event-driven architecture, the existing pattern is adequate. If direct service calls are needed in the future, implement AWS Cloud Map for service discovery. Document the event schemas as a service contract.

#### APP-Q13: AI/Agent Frameworks
- **Score**: 1/4 ❌
- **Finding**: No AI or agent frameworks found. No imports for `langchain`, `@langchain/core`, `openai`, `@anthropic-ai/sdk`, `strands-agents`, or `@aws-sdk/client-bedrock-runtime` in any `package.json` or source file. No MCP SDK, no embedding models, no prompt templates.
- **Gap**: No AI/agent capabilities present. The application has no integration points for LLM-based features.
- **Recommendation**: Start with Amazon Bedrock integration for a specific use case (e.g., product description generation, order inquiry agent). Add `@aws-sdk/client-bedrock-runtime` to begin LLM integration. Explore Strands Agents SDK for building agent tools backed by the existing APIs.

### Data Foundations

#### DATA-Q1: Vector Database Presence
- **Score**: 1/4 ❌
- **Finding**: No vector database found. No Amazon OpenSearch with k-NN plugin, no Aurora with pgvector, no S3 Vectors, no Bedrock Knowledge Bases, and no third-party vector stores (Pinecone, Weaviate, Chroma) in any dependency manifest or IaC definition.
- **Gap**: No vector search capability. Required for semantic search, RAG, and agent memory/retrieval.
- **Recommendation**: Implement Amazon OpenSearch Serverless with vector search or use Bedrock Knowledge Bases for managed vector storage. Start with a product catalog semantic search use case.

#### DATA-Q2: Vector DB Management
- **Score**: 1/4 ❌
- **Finding**: No vector database exists, so there is no management configuration. No managed or self-hosted vector DB found.
- **Gap**: No vector database to manage. This is a prerequisite gap.
- **Recommendation**: When adding a vector DB (see DATA-Q1), use a fully managed option — Amazon OpenSearch Serverless or Bedrock Knowledge Bases — to avoid operational overhead.

#### DATA-Q3: RAG Implementation
- **Score**: 1/4 ❌
- **Finding**: No RAG (Retrieval-Augmented Generation) pipeline found. No embedding model calls (no Bedrock Titan, OpenAI ada), no document chunking/splitting code, no similarity search patterns, and no Bedrock Knowledge Base integration in any source file or dependency.
- **Gap**: No RAG capability. Required for agents to access contextual knowledge from product catalogs, order history, or documentation.
- **Recommendation**: Implement a RAG pipeline for the product catalog: embed product descriptions using Amazon Bedrock Titan Embeddings, store vectors in OpenSearch Serverless, and build a retrieval function for product search agents.

#### DATA-Q4: Data Source Sprawl
- **Score**: 3/4 🟡
- **Finding**: Exactly 3 DynamoDB tables (product, basket, order), one per microservice. Each service accesses only its own table — product Lambda reads/writes `product` table, basket Lambda reads/writes `basket` table, ordering Lambda reads/writes `order` table. No cross-service database access. Clean data ownership.
- **Gap**: While the number of data sources is manageable (3), there is no unified data access layer or API for cross-cutting queries (e.g., "show me orders with product details"). Each service is a silo.
- **Recommendation**: Maintain the current data ownership model. For cross-service queries, implement an aggregation API or use DynamoDB Streams to replicate relevant data between services (e.g., denormalize product names into order records).

#### DATA-Q5: Data Access Pattern
- **Score**: 2/4 🟠
- **Finding**: Each service directly accesses DynamoDB via AWS SDK client. Each service has a `ddbClient.js` module (`src/product/ddbClient.js`, `src/basket/ddbClient.js`, `src/ordering/ddbClient.js`) that creates a `DynamoDBClient`. Lambda handlers directly execute DynamoDB commands (GetItemCommand, PutItemCommand, ScanCommand, etc.) in the handler code.
- **Gap**: DynamoDB access is mixed directly into API handler code — no repository pattern, no data access layer abstraction. Business logic and data access are tightly coupled in the handler functions.
- **Recommendation**: Refactor data access into a repository/DAO pattern within each service. Separate DynamoDB operations from handler logic. This improves testability and makes it easier to expose data via agent-friendly APIs later.

#### DATA-Q6: Unstructured Data
- **Score**: 1/4 ❌
- **Finding**: No S3 storage, no Textract, no document parsing libraries, no PDF/image processing. The application deals only with structured DynamoDB data. No `aws_s3_bucket` in CDK, no `@aws-sdk/client-s3` in any dependency.
- **Gap**: No unstructured data handling. Product images referenced in schema comments (`imageFile` field in product table) are not stored or processed.
- **Recommendation**: If product images or documents are part of the business domain, add S3 for storage. For agentic use cases, consider storing product manuals, FAQs, or support documents in S3 with Textract for parsing to enable a knowledge agent.

#### DATA-Q7: Schema Documentation
- **Score**: 1/4 ❌
- **Finding**: No schema documentation found. No JSON Schema files, no Avro/Protobuf schemas, no schema registry. DynamoDB table schemas are implicitly defined in CDK code comments in `lib/database.ts` (e.g., `// product : PK: id -- name - description - imageFile - price - category`) and in the `marshall`/`unmarshall` patterns in handler code. No migration files (DynamoDB is schemaless).
- **Gap**: Schema is undocumented. Only CDK comments and code inspection reveal the data model. No formal schema contracts.
- **Recommendation**: Create JSON Schema definitions for each entity (product, basket item, order). Document the DynamoDB access patterns (partition key, sort key, GSI usage). Add schema validation in Lambda handlers using a library like `ajv` or `zod`.

#### DATA-Q8: Data Access Layer
- **Score**: 2/4 🟠
- **Finding**: Each service has a dedicated `ddbClient.js` module that creates a `DynamoDBClient` instance. This provides a consistent client creation pattern per service. However, there is no shared repository layer, no unified data access abstraction, and no service-level API for data retrieval.
- **Gap**: The `ddbClient.js` modules are thin wrappers that only create clients — actual query logic is scattered across handler functions. No consistent error handling, no retry logic, no data validation at the data access layer.
- **Recommendation**: Build a repository layer per service (e.g., `productRepository.js`, `basketRepository.js`, `orderRepository.js`) that encapsulates all DynamoDB operations with consistent error handling, input validation, and retry logic.

#### DATA-Q9: Embedding Freshness
- **Score**: 1/4 ❌
- **Finding**: No embeddings exist, so no freshness mechanism. No DynamoDB Streams for change data capture, no scheduled re-indexing, no Bedrock Knowledge Base sync configuration.
- **Gap**: No embedding pipeline exists. This is a prerequisite gap.
- **Recommendation**: When implementing embeddings (see DATA-Q1, DATA-Q3), use DynamoDB Streams to trigger automatic re-embedding when product data changes. Configure a Lambda function that processes stream events and updates the vector store.

#### DATA-Q10: Database Engine Version & EOL
- **Score**: 4/4 ✅
- **Finding**: All databases are Amazon DynamoDB, a fully managed serverless service. DynamoDB does not have engine versions — AWS manages all versioning, patching, and upgrades automatically. No version pinning is needed or possible. Defined in `lib/database.ts`.
- **Gap**: None. DynamoDB is evergreen with no EOL concerns.
- **Recommendation**: No action needed.

#### DATA-Q11: Stored Procedures & Schema Complexity
- **Score**: 4/4 ✅
- **Finding**: No stored procedures, triggers, or proprietary SQL constructs. DynamoDB is a NoSQL database with no SQL support. All business logic resides in the application layer (Lambda handlers in `src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js`). No `.sql` files found in the repository.
- **Gap**: None. All business logic is in the application layer.
- **Recommendation**: No action needed. Continue keeping business logic in the application layer.

### Identity, Security & Governance

#### SEC-Q1: Secret Management
- **Score**: 2/4 🟠
- **Finding**: No hardcoded secrets (passwords, API keys) found in source code. Environment variables in `lib/microservice.ts` contain only non-sensitive configuration: `DYNAMODB_TABLE_NAME`, `PRIMARY_KEY`, `SORT_KEY`, `EVENT_SOURCE`, `EVENT_DETAILTYPE`, `EVENT_BUSNAME`. However, no AWS Secrets Manager integration exists — there are no `@aws-sdk/client-secrets-manager` imports and no `aws_secretsmanager` resources in CDK.
- **Gap**: While no secrets are currently hardcoded (the application uses IAM roles for AWS service access), there is no Secrets Manager pattern in place for future secrets (e.g., third-party API keys, webhook secrets).
- **Recommendation**: Establish a Secrets Manager pattern in CDK for any future secrets. For current architecture, the IAM role-based access via CDK grants is adequate.

#### SEC-Q2: IAM Least Privilege
- **Score**: 3/4 🟡
- **Finding**: CDK grant methods are used consistently: `productTable.grantReadWriteData(productFunction)` and `basketTable.grantReadWriteData(basketFunction)` in `lib/microservice.ts`, and `bus.grantPutEventsTo(props.publisherFuntion)` in `lib/eventbus.ts`. These CDK grants generate IAM policies scoped to specific resources with specific actions — no wildcard permissions.
- **Gap**: `grantReadWriteData()` grants all read/write DynamoDB actions. The product GET Lambda doesn't need write access, and the ordering Lambda only writes. Permissions could be more granular (read-only vs write-only).
- **Recommendation**: Use `grantReadData()` for read-only operations and `grantWriteData()` for write-only operations where applicable. Split Lambda functions by operation if needed for more granular IAM.

#### SEC-Q3: Identity Propagation
- **Score**: 1/4 ❌
- **Finding**: No JWT, OAuth2, or Cognito integration. User identity is passed as a URL path parameter — `{userName}` in `/basket/{userName}` and `/order/{userName}` routes (defined in `lib/apigateway.ts`). The basket checkout extracts `userName` from the request body (`src/basket/index.js`). No token validation, no user authentication verification.
- **Gap**: No authenticated identity propagation. Any caller can impersonate any user by changing the `userName` parameter. Critical for an e-commerce application handling orders and personal data.
- **Recommendation**: Implement Amazon Cognito for user authentication. Add a Cognito authorizer to API Gateway. Extract the authenticated user identity from the JWT token's `sub` claim in Lambda handlers instead of path parameters.

#### SEC-Q4: Audit Logging
- **Score**: 1/4 ❌
- **Finding**: No CloudTrail configuration in CDK. No `aws_cloudtrail` constructs. Lambda functions use `console.log` and `console.error` for basic logging (`src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js`), but these are unstructured application logs, not audit logs. No log retention policies configured.
- **Gap**: No audit trail for API calls, data access, or administrative actions. No immutable log storage.
- **Recommendation**: Enable CloudTrail for the AWS account (if not already enabled at the organization level). Add CloudWatch Logs log group retention policies in CDK. Implement structured audit logging for business-critical operations (checkout, order creation, product deletion).

#### SEC-Q5: API Rate Limits
- **Score**: 1/4 ❌
- **Finding**: No rate limiting at any layer. API Gateway in `lib/apigateway.ts` has no throttle configuration, no usage plans, no API keys. No AWS WAF integration. No application-level rate limiting in Lambda handlers.
- **Gap**: APIs are completely unprotected against abuse. No per-client or per-endpoint rate limits.
- **Recommendation**: Add API Gateway deployment stage throttling. Create usage plans with API keys for rate-limited access. Deploy AWS WAF with rate-based rules for DDoS protection.

#### SEC-Q6: PII Redaction
- **Score**: 1/4 ❌
- **Finding**: Error responses in all three Lambda handlers expose `e.message` and `e.stack` (internal stack traces). The checkout flow in `src/basket/index.js` processes PII (firstName, lastName, email, address, cardInfo as seen in `lib/database.ts` order table comments) with no redaction. These fields are logged via `console.log(checkoutPayload)` in `publishCheckoutBasketEvent`. No log scrubbing middleware.
- **Gap**: PII (names, email, address, payment info) is logged in plaintext. Internal stack traces are exposed to API callers. No PII detection or redaction mechanism.
- **Recommendation**: Remove `errorStack` from all error responses immediately. Implement a logging middleware that redacts PII fields (email, cardInfo, address) before logging. Consider Amazon Macie for S3-based PII detection if S3 is added later.

#### SEC-Q7: Human Approval Workflows
- **Score**: 1/4 ❌
- **Finding**: No human approval workflows found. No Step Functions with `waitForTaskToken` patterns, no approval Lambda functions, no manual approval gates. The checkout process executes fully automatically — basket checkout publishes an event directly to EventBridge without any approval step.
- **Gap**: No human-in-the-loop for high-risk operations. In an agentic context, agents could trigger bulk orders or deletions without human review.
- **Recommendation**: For agentic readiness, implement a Step Functions workflow with a human approval task for high-risk operations (e.g., high-value orders, bulk deletions, account modifications). Use a `waitForTaskToken` callback pattern.

#### SEC-Q8: Encryption at Rest
- **Score**: 2/4 🟠
- **Finding**: DynamoDB tables in `lib/database.ts` use default encryption (DynamoDB encrypts all data at rest by default using AWS-managed keys). No customer-managed KMS keys (`kms_key_id`) are configured on any DynamoDB table. No explicit encryption configuration in CDK.
- **Gap**: AWS-managed encryption is enabled by default, but customer-managed KMS keys are not used. This limits key rotation control, access auditing, and cross-account access patterns.
- **Recommendation**: For the order table (which stores payment and personal data), configure a customer-managed KMS key via `encryptionKey` property in the CDK `Table` construct. This enables key access auditing via CloudTrail and granular key policies.

#### SEC-Q9: API Authentication
- **Score**: 1/4 ❌
- **Finding**: No authentication on any API endpoint. All three API Gateways in `lib/apigateway.ts` are created without authorizers — no `defaultMethodOptions` with `authorizationType`, no Cognito User Pool authorizer, no Lambda authorizer, no API keys required. All endpoints (including write operations like POST /product, POST /basket, POST /basket/checkout) are publicly accessible.
- **Gap**: All APIs are unauthenticated. Any internet user can create products, create baskets, trigger checkouts, and view all orders. This is a critical security vulnerability.
- **Recommendation**: Implement authentication immediately. Add a Cognito User Pool authorizer or a Lambda authorizer to all API Gateway endpoints. At minimum, require API keys for programmatic access as a stopgap measure.

#### SEC-Q10: Centralized Identity
- **Score**: 1/4 ❌
- **Finding**: No centralized identity provider. No `aws_cognito_user_pool`, `aws_cognito_identity_pool`, OIDC, or SAML configuration in CDK. No Okta, Auth0, or Ping Identity integration. No SSO configuration.
- **Gap**: No identity infrastructure exists. This blocks authentication (SEC-Q9), identity propagation (SEC-Q3), and agent-level authorization.
- **Recommendation**: Implement Amazon Cognito User Pool as the centralized identity provider. Configure user pools with MFA, password policies, and app clients for the e-commerce application. Federate with corporate identity if needed via OIDC/SAML.

### Operations & Observability

#### OPS-Q1: Distributed Tracing
- **Score**: 1/4 ❌
- **Finding**: No distributed tracing configured. No AWS X-Ray integration — no `tracing: lambda.Tracing.ACTIVE` in `lib/microservice.ts`, no `@aws-sdk/client-xray` dependency, no OpenTelemetry SDK. No trace context propagation headers (`traceparent`, `X-Amzn-Trace-Id`) in Lambda handlers. No Datadog, Jaeger, or Zipkin SDKs in any `package.json`.
- **Gap**: No ability to trace requests across the three microservices, EventBridge, SQS, and DynamoDB. Debugging cross-service issues (e.g., failed checkout → order not created) requires manual log correlation.
- **Recommendation**: Enable X-Ray active tracing on all Lambda functions by adding `tracing: lambda.Tracing.ACTIVE` to `NodejsFunctionProps` in `lib/microservice.ts`. X-Ray automatically traces Lambda, DynamoDB, SQS, and EventBridge with minimal code changes. Add the X-Ray SDK for fine-grained subsegment tracing.

#### OPS-Q2: Structured Logging
- **Score**: 1/4 ❌
- **Finding**: All Lambda handlers use unstructured `console.log()` and `console.error()` calls. Examples: `console.log("request:", JSON.stringify(event, undefined, 2))` in all handlers, `console.log("getProduct")` as string messages. No structured log formatter (winston JSON, pino, structlog). No correlation IDs. No `traceId` or `requestId` fields in log output.
- **Gap**: Logs are unstructured text, impossible to query efficiently in CloudWatch Log Insights. No correlation between logs across services (e.g., correlating a basket checkout event with the resulting order creation).
- **Recommendation**: Adopt a structured logging library (e.g., `@aws-lambda-powertools/logger` or `pino`) for JSON-formatted logs. Include the Lambda request ID, X-Ray trace ID, and a custom correlation ID in every log entry. Use the Middy middleware framework for consistent logging setup.

#### OPS-Q3: Automated Evals
- **Score**: 1/4 ❌
- **Finding**: No agent evaluation framework found. No eval datasets, no scoring scripts, no LLM-as-judge patterns, no RAGAS, no golden dataset files. No AI/agent functionality exists to evaluate.
- **Gap**: No automated evaluation pipeline for agent quality. This is a prerequisite gap — agents must exist before they can be evaluated.
- **Recommendation**: When agents are introduced, implement an evaluation framework from day one. Use golden datasets for testing agent responses, implement automated scoring, and integrate evals into the CI/CD pipeline.

#### OPS-Q4: SLOs
- **Score**: 1/4 ❌
- **Finding**: No SLO definitions found. No CloudWatch alarms in CDK — no `aws_cloudwatch` constructs. No latency or availability targets documented. No error budget tracking. No CloudWatch dashboards.
- **Gap**: No service level objectives for any API endpoint. No alerting on degraded performance or availability.
- **Recommendation**: Define SLOs for critical user journeys (e.g., product search p99 < 200ms, checkout success rate > 99.9%). Create CloudWatch alarms for API Gateway 5XX rates and Lambda error rates. Build a CloudWatch dashboard for each microservice.

#### OPS-Q5: Rollback Capability
- **Score**: 1/4 ❌
- **Finding**: No rollback configuration. No blue/green deployment, no canary deployment, no CodeDeploy integration. No Lambda alias with traffic shifting. No feature flags. No prompt versioning (no AI features). Only manual `cdk deploy` which performs in-place CloudFormation stack updates.
- **Gap**: No automated rollback mechanism. A bad deployment requires manual CDK rollback or CloudFormation stack update. No way to gradually shift traffic.
- **Recommendation**: Configure Lambda aliases with CodeDeploy for traffic shifting (canary or linear). Add CloudWatch alarms as rollback triggers. Use CDK's `currentVersion` and `alias` properties on Lambda functions with `AutoRollbackConfig`.

#### OPS-Q6: LLM Cost Tracking
- **Score**: 1/4 ❌
- **Finding**: No LLM usage in the application. No Bedrock, OpenAI, or other LLM API calls. No token counting, no cost attribution, no usage metrics.
- **Gap**: No LLM cost tracking infrastructure. This is a prerequisite gap — LLM integration must exist first.
- **Recommendation**: When LLM integration is added, implement token usage tracking from day one. Log input/output token counts per request. Publish CloudWatch custom metrics for token usage with dimensions for user, feature, and model.

#### OPS-Q7: Business Metrics
- **Score**: 1/4 ❌
- **Finding**: No custom business metrics. No `cloudwatch.put_metric_data` calls or CloudWatch `putMetricData` SDK usage in any Lambda handler. No business KPI tracking (e.g., checkout conversion rate, average order value, product views). Only basic `console.log` messages.
- **Gap**: No business outcome metrics. Cannot measure business impact of changes or agent-driven actions.
- **Recommendation**: Publish custom CloudWatch metrics for key business events: orders placed, checkouts started, products viewed. Add dimensions for time period and category. Create a business metrics CloudWatch dashboard.

#### OPS-Q8: Anomaly Detection
- **Score**: 1/4 ❌
- **Finding**: No anomaly detection. No CloudWatch alarms of any kind — no error rate monitoring, no latency monitoring, no composite alarms. No PagerDuty, OpsGenie, or SNS alerting integration. No CloudWatch anomaly detection configuration.
- **Gap**: No alerting on any metric. Service degradation or outages would go undetected until a user reports them.
- **Recommendation**: Create CloudWatch alarms for Lambda error rates, API Gateway 5XX rates, SQS queue depth (for ordering backlog), and DynamoDB throttle events. Enable CloudWatch anomaly detection for baseline-aware alerting. Configure SNS topics for alarm notifications.

#### OPS-Q9: Deployment Strategy
- **Score**: 1/4 ❌
- **Finding**: Deployment is manual `cdk deploy` as documented in `README.md`. This performs a direct CloudFormation stack update — no canary rollout, no blue/green deployment, no traffic shifting. No CodeDeploy configuration, no Argo Rollouts, no feature flags.
- **Gap**: Direct-to-production deployments with no gradual rollout. Any deployment issue affects 100% of traffic immediately.
- **Recommendation**: Implement Lambda deployment preferences using CDK: configure `deploymentConfig: lambda.CfnDeploymentConfig.CANARY_10PERCENT_5MINUTES` with rollback alarms. This enables automated canary deployments with rollback on alarm triggers.

#### OPS-Q10: Integration Testing
- **Score**: 1/4 ❌
- **Finding**: A test file exists at `test/aws-microservices.test.ts` with a Jest configuration in `jest.config.js`. However, the test file is entirely commented out — the single test `'SQS Queue Created'` has all assertions commented out and is a no-op. No functional tests exist. No API integration tests, no contract tests, no end-to-end tests.
- **Gap**: Zero functional tests. The test infrastructure (Jest) is configured but unused. No confidence in deployment correctness.
- **Recommendation**: Uncomment and update the CDK construct test. Add integration tests for each Lambda handler using mocked DynamoDB calls. Add API integration tests using tools like `supertest` or `newman`. Integrate tests into a CI/CD pipeline.

#### OPS-Q11: Incident Response Automation
- **Score**: 1/4 ❌
- **Finding**: No runbooks, SSM documents, or automated remediation. No Lambda-based remediation functions. No Step Functions for incident workflows. No self-healing patterns. No links to runbooks in any configuration.
- **Gap**: No incident response automation. All incidents require manual investigation and remediation.
- **Recommendation**: Create runbooks for common failure scenarios (DynamoDB throttling, Lambda timeout, SQS dead letter queue messages). Implement SSM Automation documents for common remediation steps. Add DLQ alarms with Lambda-based auto-remediation for the SQS OrderQueue.

#### OPS-Q12: Observability Governance & Ownership
- **Score**: 1/4 ❌
- **Finding**: No CODEOWNERS file. No SLO definitions with named owners. No team ownership documentation. No platform team observability tooling. No per-service dashboards. No observability-as-a-product practices.
- **Gap**: No observability governance structure. No defined ownership for service reliability.
- **Recommendation**: Create a CODEOWNERS file assigning ownership per service (product, basket, ordering). Define SLOs per service with named owners. Establish an observability stack (X-Ray, CloudWatch dashboards, structured logging) as a shared platform capability.

## Recommended Modernization Pathways

Based on the assessment findings, the following AWS Modernization Pathways are evaluated for this application. Multiple pathways can execute in parallel because modern applications comprise multiple interconnected components — each requiring its own modernization approach.

### Pathway Summary

| Pathway | Status | Goal Alignment | Priority | Key Trigger Criteria | Est. Effort |
|---------|--------|---------------|----------|---------------------|-------------|
| Move to Cloud Native | Not Triggered | Medium | — | — | — |
| Move to Containers | Not Triggered | Medium | — | — | — |
| Move to Open Source | Not Triggered | Medium | — | — | — |
| Move to Managed Databases | Not Triggered | Medium | — | — | — |
| Move to Managed Analytics | Not Triggered | Medium | — | — | — |
| Move to Modern DevOps | Triggered | Medium | High | INF-Q6: 1/4, OPS-Q9: 1/4, OPS-Q10: 1/4, OPS-Q1: 1/4 | High |
| Move to AI | Triggered | Medium | High | APP-Q13: 1/4, DATA-Q1: 1/4, DATA-Q3: 1/4, OPS-Q3: 1/4, OPS-Q6: 1/4 | High |

### Parallel Execution Plan

**Parallel Track 1**: Move to Modern DevOps — CI/CD, observability, testing, and deployment strategies can be implemented independently.

**Parallel Track 2**: Move to AI — Vector database, RAG pipeline, and agent framework integration can proceed in parallel with DevOps improvements.

**Sequential Dependencies**: Move to Modern DevOps should be at least partially in place (CI/CD + observability) before deploying AI/agent features to production, as agents require robust monitoring and safe deployment pipelines.

### Move to Modern DevOps

- **Priority**: High
- **Goal Alignment**: Medium
- **Trigger Criteria Met**:
  - INF-Q6: Score 1/4 — No CI/CD pipeline exists; deployment is manual `cdk deploy`
  - OPS-Q9: Score 1/4 — Direct-to-production deployments with no canary or blue/green strategy
  - OPS-Q10: Score 1/4 — Test file at `test/aws-microservices.test.ts` is entirely commented out; zero functional tests
  - OPS-Q1: Score 1/4 — No distributed tracing; no X-Ray, OpenTelemetry, or tracing SDK configured
- **Current State**: Infrastructure is well-defined in CDK but has no CI/CD automation, no testing, no observability, and no safe deployment strategy. All deployments are manual `cdk deploy` directly to production.
- **Target State**: Fully automated CI/CD pipeline with linting, unit tests, integration tests, CDK synth validation, and canary deployments. X-Ray tracing across all services with structured JSON logging and CloudWatch dashboards. Automated rollback on alarm triggers.
- **Key Activities**:
  1. Create a CI/CD pipeline (GitHub Actions or CodePipeline) with lint → test → synth → deploy stages
  2. Enable X-Ray active tracing on all Lambda functions via CDK
  3. Implement structured JSON logging using `@aws-lambda-powertools/logger`
  4. Write CDK construct tests and Lambda unit tests
  5. Add API integration tests
  6. Configure Lambda canary deployments with CloudWatch alarm rollback triggers
  7. Create CloudWatch dashboards and alarms for each microservice
  8. Define SLOs for critical API endpoints
- **Dependencies**: None — this is a foundational pathway
- **Estimated Effort**: High
- **Roadmap Phase Alignment**: Phase 1 (Quick Wins) for CI/CD and tracing; Phase 2 (Foundation) for advanced deployment strategies and comprehensive observability
- **Relevant Learning Materials**: Module 6 — Move to Modern DevOps

### Move to AI

- **Priority**: High
- **Goal Alignment**: Medium
- **Trigger Criteria Met**:
  - APP-Q13: Score 1/4 — No AI/agent frameworks; no LangChain, Bedrock, or agent SDK imports
  - DATA-Q1: Score 1/4 — No vector database present
  - DATA-Q3: Score 1/4 — No RAG implementation; no embedding, chunking, or semantic search
  - OPS-Q3: Score 1/4 — No automated eval framework for agent quality
  - OPS-Q6: Score 1/4 — No LLM cost tracking (no LLM usage exists)
- **Current State**: No AI or agent capabilities exist. The application is a pure CRUD e-commerce platform with no LLM integration, no vector database, no RAG, and no agent tools. The existing APIs return structured JSON, which is a positive foundation for agent tool integration.
- **Target State**: AI-enhanced e-commerce with agent capabilities — product search agent with semantic search (RAG over product catalog), order inquiry agent with natural language queries, and automated eval pipeline for agent quality assurance.
- **Key Activities**:
  1. Add Amazon Bedrock integration (`@aws-sdk/client-bedrock-runtime`) for LLM capabilities
  2. Deploy a vector database (OpenSearch Serverless or Bedrock Knowledge Bases) for product catalog embeddings
  3. Build a RAG pipeline: embed product descriptions, enable semantic product search
  4. Create agent tools backed by existing Product, Basket, and Order APIs
  5. Implement LLM token usage tracking with CloudWatch custom metrics
  6. Build an automated eval framework with golden datasets for agent testing
  7. Add observability for agent interactions (trace LLM calls, log tool invocations)
- **Dependencies**: Move to Modern DevOps should be partially complete (CI/CD, observability) before deploying agents to production
- **Estimated Effort**: High
- **Roadmap Phase Alignment**: Phase 2 (Foundation) for data foundations (vector DB, RAG); Phase 3 (Advanced Capabilities) for agent framework integration and eval pipeline
- **Relevant Learning Materials**: Module 7 — Move to AI

## Quick Agent Wins

Even before completing the full modernization roadmap, these agent opportunities are available based on your current architecture:

1. **API-Aware E-commerce Agent** — Build an agent that can discover and invoke your existing Product, Basket, and Order API endpoints for natural language interactions (e.g., "Show me all products", "Add item to basket", "Check my orders").
   - **Leverages**: API Gateway endpoints for all three services defined in `lib/apigateway.ts` (Product CRUD, Basket CRUD + checkout, Order queries)
   - **Effort**: Medium
   - **Value**: Enables natural language interaction with the e-commerce platform; demonstrates agent value with existing infrastructure

2. **Agent Tool Integration via Structured JSON APIs** — Your APIs already return clean structured JSON (`{ message: ..., body: ... }` format), making them immediately usable as agent tools without response parsing complexity.
   - **Leverages**: Structured JSON responses from all Lambda handlers (`src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js`)
   - **Effort**: Low
   - **Value**: Zero-friction agent tool integration — agents can parse and act on API responses immediately

3. **Knowledge Agent from Documentation** — Build a RAG-based knowledge agent using the existing README.md and Medium article links to answer developer questions about the architecture.
   - **Leverages**: `README.md` with architecture documentation, CDK code comments in `lib/database.ts` describing table schemas
   - **Effort**: Low
   - **Value**: Provides developer onboarding assistance and architecture knowledge retrieval

4. **Product Data Query Agent** — Build a natural language to DynamoDB query agent that can search products by category, retrieve product details, or list all products using the existing Product service schema.
   - **Leverages**: Product DynamoDB table with clear schema (PK: id, attributes: name, description, imageFile, price, category) defined in `lib/database.ts`
   - **Effort**: Medium
   - **Value**: Enables natural language product catalog queries without building new APIs

> These opportunities can be pursued in parallel with the modernization roadmap.
> They demonstrate agent value early while foundations are being built.

## Readiness Roadmap

### Phase 1 — Quick Wins (Days 1–30)

1. **Add API Authentication** — Implement Amazon Cognito User Pool with authorizers on all three API Gateways in `lib/apigateway.ts`. This is the most critical security gap and blocks agent identity propagation.
2. **Enable X-Ray Tracing** — Add `tracing: lambda.Tracing.ACTIVE` to all Lambda functions in `lib/microservice.ts`. Single property addition per function, instant distributed tracing across Lambda → DynamoDB → EventBridge → SQS.
3. **Implement Structured Logging** — Add `@aws-lambda-powertools/logger` to all Lambda handlers. Replace `console.log` with structured JSON logging including request IDs and correlation IDs.
4. **Create CI/CD Pipeline** — Set up a GitHub Actions workflow or AWS CodePipeline with stages: `npm install` → `npm test` → `cdk synth` → `cdk deploy`. Start with a single environment (dev).
5. **Remove Stack Traces from Error Responses** — Remove `errorStack: e.stack` from all Lambda handler error responses to stop exposing internal details to API callers.
6. **Upgrade Lambda Runtime** — Change `Runtime.NODEJS_14_X` to `Runtime.NODEJS_20_X` in `lib/microservice.ts` to exit EOL runtime.

### Phase 2 — Foundation (Months 1–3)

1. **Build Observability Stack** — Create CloudWatch dashboards per microservice. Add CloudWatch alarms for Lambda errors, API Gateway 5XX rates, and SQS queue depth. Enable CloudWatch anomaly detection.
2. **Implement API Documentation** — Create OpenAPI 3.0 specifications for Product, Basket, and Order APIs. Document all routes, request/response schemas, and error codes. These specs become agent tool definitions.
3. **Add Integration Tests** — Uncomment and update `test/aws-microservices.test.ts`. Add Lambda handler unit tests with mocked DynamoDB. Add API integration test suite. Integrate into CI/CD pipeline.
4. **Configure Canary Deployments** — Add Lambda aliases with CodeDeploy canary deployment configurations. Set CloudWatch alarm triggers for automatic rollback.
5. **Implement Identity Propagation** — Replace path-parameter-based user identity with JWT token-based identity. Extract authenticated user from Cognito tokens in Lambda handlers.
6. **Add Rate Limiting** — Configure API Gateway throttling and usage plans. Deploy AWS WAF with rate-based rules.
7. **Deploy Vector Database** — Set up Amazon OpenSearch Serverless with vector search or Bedrock Knowledge Bases. Embed product catalog data for semantic search.
8. **Implement Schema Documentation** — Create JSON Schema definitions for all DynamoDB entities. Add input validation using `zod` or `ajv` in Lambda handlers.

### Phase 3 — Advanced Capabilities (Months 3–6)

1. **Integrate Amazon Bedrock** — Add `@aws-sdk/client-bedrock-runtime` for LLM integration. Build product description generation and natural language query capabilities.
2. **Build RAG Pipeline** — Implement embedding pipeline for product catalog using Bedrock Titan Embeddings. Enable DynamoDB Streams to auto-refresh embeddings on product changes. Build semantic search function.
3. **Create Agent Tools** — Build agent tools backed by existing APIs using Strands Agents SDK or LangChain.js. Define tool schemas from OpenAPI specs created in Phase 2.
4. **Implement Step Functions Workflows** — Replace the hardcoded checkout workflow with Step Functions. Add human approval steps for high-value orders. Implement saga pattern for error compensation.
5. **Build Agent Evaluation Framework** — Create golden datasets for agent testing. Implement automated scoring pipeline. Add eval metrics to CloudWatch dashboards. Integrate evals into CI/CD.
6. **Implement LLM Cost Tracking** — Add token usage tracking per request. Publish CloudWatch custom metrics with user/feature/model dimensions. Set cost alert thresholds.
7. **Establish Observability Governance** — Create CODEOWNERS file. Define per-service SLOs with named owners. Implement agent-specific SLOs (task success rate, tool error rate, latency).

## Recommended Self-Paced Learning Materials

### Module 6: Move to Modern DevOps
*Addresses the critical gaps in CI/CD (INF-Q6), deployment strategy (OPS-Q9), testing (OPS-Q10), and observability (OPS-Q1, OPS-Q2).*

- AWS Modernization Pathways: Move to Modern DevOps — https://skillbuilder.aws/learning-plan/1FGEQKGPQD/aws-modernization-pathways-move-to-modern-devops-includes-labs/MNQZ2KPVCK
- Getting Started with DevOps on AWS — https://skillbuilder.aws/learn/R4B13K95YQ/getting-started-with-devops-on-aws/38NHHYRV1R
- AWS CloudFormation Getting Started — https://skillbuilder.aws/learn/RH22P2RXU4/aws-cloudformation-getting-started/KEK5BT6HSE
  - *Relevant because CDK synthesizes to CloudFormation; understanding CFN helps debug deployment issues*
- Advanced Testing Practices Using AWS DevOps Tools — https://skillbuilder.aws/learn/1YC7UXUWBR/advanced-testing-practices-using-aws-devops-tools/A32U6G7NEQ
  - *Directly addresses the OPS-Q10 gap (zero functional tests)*
- AWS Developer: CI/CD Automation — https://skillbuilder.aws/learn/C1KF8ZJ1D8/aws-developer--cicd-automation/KY1E1JS9FA
  - *Covers CI/CD pipeline setup for the INF-Q6 gap*

### Module 2: Move to Cloud Native (Containers and Serverless)
*Addresses workflow orchestration (INF-Q3) and async communication patterns (APP-Q3, APP-Q6).*

- Cloud Design Patterns, Architectures, and Implementations — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html
  - *Essential for understanding event-driven patterns, saga orchestration, and resilience patterns needed for this application*
- Lambda Foundations — https://skillbuilder.aws/learn/XHRS91KKK6/aws-lambda-foundations/R85JRN3APC
  - *Deepens understanding of Lambda execution model, concurrency, and error handling relevant to INF-Q10 and APP-Q9*
- Architecting Serverless Applications — https://skillbuilder.aws/learn/MRWENY7FSX/architecting-serverless-applications/QVFY2JHVEH
  - *Covers Step Functions integration and serverless best practices for the INF-Q3 gap*
- Amazon API Gateway for Serverless Applications — https://skillbuilder.aws/learn/GQA6FHWPJD/amazon-api-gateway-for-serverless-applications/JVRZ3PSW4H
  - *Covers API Gateway throttling, auth, and validation — addresses INF-Q7, SEC-Q5, SEC-Q9 gaps*

### Module 7: Move to AI
*Addresses all AI/agent readiness gaps (APP-Q13, DATA-Q1, DATA-Q3, OPS-Q3, OPS-Q6).*

- AWS Modernization Pathways: Move to AI — https://skillbuilder.aws/learning-plan/VDFEE4ACCV/aws-modernization-pathways-move-to-ai-pathways-includes-labs/P3DAWPTN63
- Introduction to Generative AI: Art of the Possible — https://skillbuilder.aws/learn/ZEVZZ1D4AS/introduction-to-generative-ai--art-of-the-possible/Y7MTGJCW1U
- Amazon Bedrock Getting Started — https://skillbuilder.aws/learn/63KTRM86DQ/amazon-bedrock-getting-started/SC2Y3HMAUE
  - *Essential first step for the APP-Q13 gap — introduces Bedrock models and API integration*
- Planning a Generative AI Project — https://skillbuilder.aws/learn/HU1FQRGDDZ/planning-a-generative-ai-project/SYR3SCPSHC
- Essentials for Prompt Engineering — https://skillbuilder.aws/learn/XBNAVKA88J/essentials-of-prompt-engineering/9T9Q45EDTV
- Build and Evaluate Retrieval Augmented Generation (RAG) Applications using Knowledge Bases for Amazon Bedrock (Lab) — https://skillbuilder.aws/learn/JRGWCFYT67/lab--build-and-evaluate-retrieval-augmented-generation-rag-applications-using-knowledge-bases-for-amazon-bedrock/A4MN58JB7A
  - *Directly addresses the DATA-Q1, DATA-Q3, and OPS-Q3 gaps — hands-on RAG and evaluation*
- Introduction to Agentic AI on AWS — https://skillbuilder.aws/learn/DNBD5MT8ZD/introduction-to-agentic-ai-on-aws/WAKAFK6UFY
  - *Covers agentic AI concepts and AWS services for building agents*
- Creating an AWS DevOps AI Agent with the Strands Agents SDK (Lab) — https://skillbuilder.aws/learn/AH1GD8AJY3/lab--creating-an-aws-devops-ai-agent-with-the-strands-agents-sdk/A9SKJNMPJ2
  - *Hands-on lab for building an agent with the Strands SDK — directly applicable*
- AWS PartnerCast: Deep Dive: Building Observable AI Agents with Strands, Amazon Bedrock Agent Core & SageMaker MLflow — https://skillbuilder.aws/learn/1EN76TZBB6/aws-partnercast--deep-dive-building-observable-ai-agents-with-strands-amazon-bedrock-agent-core--sagemaker-mlflow--technical/CX2K6XAT84
  - *Covers agent observability — addresses OPS-Q6 and agent monitoring needs*

## Appendix: Evidence Index

| # | File | Key Evidence |
|---|------|-------------|
| 1 | `lib/microservice.ts` | Lambda function definitions using `NodejsFunction` with `Runtime.NODEJS_14_X`; IAM grants via `grantReadWriteData()`; environment variables for DynamoDB table names and EventBridge config; no VPC, no tracing, no concurrency limits |
| 2 | `lib/database.ts` | Three DynamoDB tables (product, basket, order) with `BillingMode.PAY_PER_REQUEST`; partition keys and sort keys defined; `RemovalPolicy.DESTROY`; no encryption key configuration; schema documented only in code comments |
| 3 | `lib/apigateway.ts` | Three `LambdaRestApi` constructs (Product, Basket, Order); explicit route definitions with `proxy: false`; no authorizers, no throttling, no request validation, no usage plans |
| 4 | `lib/eventbus.ts` | EventBridge custom bus (`SwnEventBus`); `CheckoutBasketRule` routing to SQS target; `grantPutEventsTo()` for basket Lambda IAM |
| 5 | `lib/queue.ts` | SQS `OrderQueue` with 30s visibility timeout; Lambda event source with `batchSize: 1`; no DLQ configured |
| 6 | `lib/aws-microservices-stack.ts` | CDK stack orchestrator connecting database → microservices → API Gateway → queue → eventbus; clean modular CDK structure |
| 7 | `src/product/index.js` | Product Lambda handler with CRUD operations (GET/POST/PUT/DELETE); direct DynamoDB SDK calls; unstructured `console.log`; error responses expose `e.stack`; no auth, no idempotency |
| 8 | `src/basket/index.js` | Basket Lambda handler with CRUD and checkout; hardcoded checkout workflow (`getBasket` → `prepareOrderPayload` → `publishCheckoutBasketEvent` → `deleteBasket`); EventBridge event publishing; PII logged in plaintext |
| 9 | `src/ordering/index.js` | Ordering Lambda handler; dual invocation (SQS + EventBridge + API Gateway); `createOrder` writes to DynamoDB; no idempotency or deduplication |
| 10 | `src/product/ddbClient.js` | DynamoDB client instantiation for product service; minimal wrapper pattern |
| 11 | `src/basket/ddbClient.js` | DynamoDB client instantiation for basket service; identical pattern to product |
| 12 | `src/basket/eventBridgeClient.js` | EventBridge client instantiation for basket service event publishing |
| 13 | `src/ordering/ddbClient.js` | DynamoDB client instantiation for ordering service |
| 14 | `src/product/package.json` | Dependencies: `@aws-sdk/client-dynamodb ^3.55.0`, `@aws-sdk/util-dynamodb ^3.55.0`; no AI, logging, or testing libraries |
| 15 | `src/basket/package.json` | Dependencies: `@aws-sdk/client-dynamodb ^3.55.0`, `@aws-sdk/client-eventbridge ^3.58.0`; no AI or agent libraries |
| 16 | `src/ordering/package.json` | Dependencies: `@aws-sdk/client-dynamodb ^3.58.0`; minimal dependency set |
| 17 | `package.json` | Root CDK project; `aws-cdk-lib 2.17.0`, TypeScript `~3.9.7`; Jest configured but no test scripts beyond `jest` |
| 18 | `test/aws-microservices.test.ts` | Single test file entirely commented out; no functional assertions; Jest infrastructure configured but unused |
| 19 | `README.md` | Documentation confirming manual `cdk deploy` workflow; architecture description; API endpoint patterns; no CI/CD instructions |
| 20 | `src/basket/checkoutbasketevents.json` | Sample EventBridge event payloads for testing checkout flow; confirms event schema (Source, Detail, DetailType, EventBusName) |
