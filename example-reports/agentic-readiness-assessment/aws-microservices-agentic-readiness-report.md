# Agentic Readiness Assessment Report
**Target**: ./services/aws-microservices
**Date**: 2026-03-11
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Assessment Goal**: agentic-ai-enablement
**Goal Context**: Building customer-facing AI agents for support and order management
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
   - Phase 1 — Agent Quick Wins (Days 1–30)
   - Phase 2 — Agent Foundations (Months 1–3)
   - Phase 3 — Agent Scale & Optimization (Months 3–6)
8. Recommended Self-Paced Learning Materials
9. Appendix: Evidence Index

---

## Executive Summary

This serverless e-commerce application — comprising product, basket, and ordering microservices on AWS Lambda with DynamoDB, EventBridge, and SQS — has a solid event-driven foundation but is **not yet ready for agentic AI workflows** needed for customer-facing support and order management agents. The strongest areas are the microservices architecture (score 4/4) with clean service boundaries, fully managed DynamoDB databases (score 4/4), and comprehensive CDK Infrastructure as Code (score 4/4). However, critical gaps block agent enablement: there are no API documentation (OpenAPI specs), no AI/agent frameworks, no vector database or RAG pipeline for knowledge retrieval, no API authentication or identity propagation, and the entire Operations & Observability category scores 1.0/4.0 — meaning there is no tracing, no structured logging, no CI/CD, and no monitoring to support autonomous agent operations. Immediate priorities should focus on securing the API layer, generating OpenAPI specs for agent tool discovery, and establishing a CI/CD pipeline before introducing agent capabilities.

### Overall Score: 1.8 / 4.0

| Category | Score | Status |
|----------|-------|--------|
| Infrastructure & Platform | 2.5 / 4.0 | 🟡 |
| Application Architecture | 1.9 / 4.0 | 🟠 |
| Data Foundations | 2.0 / 4.0 | 🟠 |
| Identity, Security & Governance | 1.4 / 4.0 | ❌ |
| Operations & Observability | 1.0 / 4.0 | ❌ |

---

## Top Priorities (Critical Gaps)

**1. APP-Q2 — No API Documentation (Score: 1/4)** ❌
Agents discover and invoke tools through API specifications. No OpenAPI/Swagger specs exist anywhere in this repository — API routes are defined only in CDK code (`lib/apigateway.ts`). Without machine-readable API documentation, a customer support agent cannot auto-discover available endpoints for product lookups, basket management, or order queries. **First step**: Generate OpenAPI specs from the existing API Gateway definitions using `cdk synth` output or manually create `openapi.yaml` files for each service (product, basket, ordering).

**2. APP-Q13 — No AI/Agent Frameworks (Score: 1/4)** ❌
No AI or agent SDK imports exist in any dependency manifest (`src/*/package.json`). There is no Amazon Bedrock, LangChain, Strands Agents, or OpenAI integration. Building customer-facing AI agents for support and order management requires agent framework integration as the foundational capability. **First step**: Add `@aws-sdk/client-bedrock-runtime` to a new agent Lambda function that can orchestrate calls to the existing product, basket, and ordering APIs.

**3. DATA-Q1 — No Vector Database (Score: 1/4)** ❌
No vector database (OpenSearch with k-NN, Aurora pgvector, Pinecone, Chroma, or Bedrock Knowledge Bases) is present. A customer support agent needs semantic search over product catalogs, order history, and support documentation to provide relevant answers. Without vector storage, RAG-based knowledge retrieval is impossible. **First step**: Create an Amazon Bedrock Knowledge Base backed by OpenSearch Serverless to index product data and support documentation.

**4. DATA-Q3 — No RAG Implementation (Score: 1/4)** ❌
No document chunking, embedding generation, or semantic search patterns exist in the codebase. For an order management agent, RAG is essential to retrieve relevant customer order context, product details, and policy documents when responding to support queries. **First step**: Implement a RAG pipeline using Amazon Bedrock Knowledge Bases with Titan Embeddings to index product catalog and order FAQ data from DynamoDB.

**5. SEC-Q9 — No API Authentication (Score: 1/4)** ❌
All three API Gateway endpoints (Product, Basket, Order) in `lib/apigateway.ts` have zero authorizers configured — they are publicly accessible. Deploying an agent that can read customer orders and modify baskets on completely unauthenticated endpoints is a critical security risk. Agent-to-API calls must be authenticated to enforce per-user data access boundaries. **First step**: Add a Cognito User Pool authorizer to all API Gateway endpoints in `lib/apigateway.ts` and implement JWT validation.

---

## Detailed Findings

### Infrastructure & Platform

#### INF-Q1: Compute
- **Score**: 3/4 🟡
- **Finding**: All compute is AWS Lambda via `NodejsFunction` in `lib/microservice.ts`. Three Lambda functions are defined: `productLambdaFunction`, `basketLambdaFunction`, and `orderingLambdaFunction`. This is fully serverless — no EC2 instances. However, all functions use `Runtime.NODEJS_14_X`, which reached end-of-life in November 2023.
- **Gap**: Lambda runtime `NODEJS_14_X` is EOL. No Lambda reserved/provisioned concurrency configured for predictable agent response times.
- **Recommendation**: Upgrade all Lambda functions to `Runtime.NODEJS_20_X` or `Runtime.NODEJS_22_X` in `lib/microservice.ts`. Consider provisioned concurrency for the agent-facing Lambda to ensure low cold-start latency for real-time customer support interactions.

#### INF-Q2: Databases
- **Score**: 4/4 ✅
- **Finding**: All three databases are DynamoDB tables defined in `lib/database.ts`: `product` (PK: id), `basket` (PK: userName), and `order` (PK: userName, SK: orderDate). All use `BillingMode.PAY_PER_REQUEST` for automatic scaling. DynamoDB is fully managed with automatic failover, backups, and encryption.
- **Gap**: None. All databases are fully managed.
- **Recommendation**: Enable DynamoDB Point-in-Time Recovery (PITR) for the order table to support agent conversation state recovery and audit requirements.

#### INF-Q3: Workflow Orchestration
- **Score**: 1/4 ❌
- **Finding**: No Step Functions, Temporal, or workflow orchestration service found. The checkout flow in `src/basket/index.js` is a hardcoded linear sequence: (1) get basket → (2) prepare order payload → (3) publish EventBridge event → (4) delete basket. If step 3 succeeds but step 4 fails, the basket remains but the order is created — no compensation logic.
- **Gap**: No dedicated orchestration service. The checkout workflow has no error compensation, no retry orchestration, and no visibility into workflow state. Agent workflows (e.g., "process a return and refund") will require multi-step orchestration with human approval gates.
- **Recommendation**: Implement AWS Step Functions for the checkout flow using the saga pattern. This directly supports agent-driven order management workflows where the agent needs to orchestrate multi-step processes (check order → validate return → process refund → notify customer) with visibility and rollback capabilities. Prefer EventBridge integration with Step Functions for event-driven saga orchestration.

#### INF-Q4: Async Messaging
- **Score**: 4/4 ✅
- **Finding**: Amazon EventBridge custom event bus (`SwnEventBus`) defined in `lib/eventbus.ts` with a rule `CheckoutBasketRule` routing `com.swn.basket.checkoutbasket` events to an SQS queue. Amazon SQS queue (`OrderQueue`) defined in `lib/queue.ts` with 30-second visibility timeout and batch size 1. The basket Lambda publishes checkout events via `PutEventsCommand` in `src/basket/index.js`, and the ordering Lambda consumes from SQS via `SqsEventSource` in `src/ordering/index.js`.
- **Gap**: None. Managed messaging with EventBridge + SQS is present and well-architected.
- **Recommendation**: Add a Dead Letter Queue (DLQ) to the `OrderQueue` for failed message handling. For agent workflows, consider adding SNS for fan-out notifications (e.g., order confirmation to customer, order alert to support dashboard).

#### INF-Q5: Infrastructure as Code
- **Score**: 4/4 ✅
- **Finding**: Full AWS CDK (TypeScript) IaC covering all infrastructure: compute (`lib/microservice.ts`), databases (`lib/database.ts`), API Gateway (`lib/apigateway.ts`), EventBridge (`lib/eventbus.ts`), SQS (`lib/queue.ts`), and stack orchestration (`lib/aws-microservices-stack.ts`). CDK version 2.17.0 defined in `package.json`. All resources are IaC-managed.
- **Gap**: CDK version 2.17.0 is significantly outdated (current is 2.170+). No CDK Nag or security scanning integrated.
- **Recommendation**: Upgrade CDK to latest v2. Add `cdk-nag` for automated security and best-practice checks on synthesized CloudFormation templates.

#### INF-Q6: CI/CD
- **Score**: 1/4 ❌
- **Finding**: No CI/CD pipeline files exist. No `.github/workflows/`, no `buildspec.yml`, no `Jenkinsfile`, no `.gitlab-ci.yml`, no CodePipeline definition in CDK. Deployment is manual via `cdk deploy` as documented in `README.md`.
- **Gap**: Entirely missing. No automated testing, building, or deployment. Manual deployment is incompatible with agent-driven development where prompt changes and tool configurations need safe, automated rollout.
- **Recommendation**: Create a GitHub Actions workflow or AWS CodePipeline with stages: lint → unit test → `cdk synth` → `cdk diff` → deploy to staging → integration test → deploy to production. This is a prerequisite for safe agent deployment iteration.

#### INF-Q7: API Entry Point
- **Score**: 2/4 🟠
- **Finding**: Three separate `LambdaRestApi` instances defined in `lib/apigateway.ts`: Product Service, Basket Service, and Order Service. API Gateway is present with explicitly defined routes (not proxy). However, no throttling (`deployOptions.throttle`), no request validation (`requestValidator`), and no authorizers are configured.
- **Gap**: API Gateway exists but lacks throttling, authentication, and request validation — all critical for agent interactions where an autonomous agent could overwhelm APIs or access unauthorized data.
- **Recommendation**: Add `deployOptions: { throttlingBurstLimit: 100, throttlingRateLimit: 50 }` to each `LambdaRestApi`. Add request models and validators. Add Cognito or Lambda authorizer. Consider consolidating the three separate API Gateways into one with path-based routing for simpler agent tool configuration.

#### INF-Q8: Real-time Streaming
- **Score**: 1/4 ❌
- **Finding**: No Kinesis Data Streams, Kinesis Firehose, or MSK (Managed Kafka) present. EventBridge is used for event routing but is not a streaming service.
- **Gap**: No real-time data streaming capability. For customer support agents, real-time order status updates and inventory changes would improve agent response accuracy.
- **Recommendation**: If real-time agent awareness of inventory/order changes is needed, consider DynamoDB Streams (zero additional infrastructure) to trigger Lambda functions that update agent context. For higher-volume scenarios, add Kinesis Data Streams.

#### INF-Q9: Network Security
- **Score**: 2/4 🟠
- **Finding**: All compute is Lambda (serverless) and all data stores are DynamoDB (serverless). No VPC, subnets, or security groups are defined in CDK — Lambda functions run in the default AWS-managed VPC. While this is acceptable for a purely serverless architecture, there are no network-level controls.
- **Gap**: No VPC configuration for Lambda functions. When agent infrastructure is added (potentially including vector databases like OpenSearch), VPC placement and security groups will be required. No WAF configured on API Gateway.
- **Recommendation**: Add AWS WAF to the API Gateway endpoints for IP-based filtering and bot protection. When adding OpenSearch or other VPC-resident resources for agent infrastructure, place Lambda functions in a VPC with private subnets.

#### INF-Q10: Auto-scaling
- **Score**: 3/4 🟡
- **Finding**: Lambda auto-scales inherently (up to 1000 concurrent executions by default). DynamoDB uses `PAY_PER_REQUEST` billing mode (`lib/database.ts`), which auto-scales throughput. No explicit Lambda reserved concurrency or provisioned concurrency configured.
- **Gap**: No Lambda concurrency limits set — a traffic spike (or agent loop) could exhaust the account-level Lambda concurrency limit, affecting all services. No DynamoDB auto-scaling alarms.
- **Recommendation**: Set `reservedConcurrentExecutions` on each Lambda function to prevent one service from starving others. Add provisioned concurrency for agent-facing Lambdas to eliminate cold starts during customer interactions.

### Application Architecture

#### APP-Q1: Programming Languages
- **Score**: 3/4 🟡
- **Finding**: Lambda functions are written in JavaScript (ES module syntax with `import` statements) in `src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js`. CDK infrastructure is TypeScript (`lib/*.ts`). JavaScript/TypeScript has a growing agent ecosystem with LangChain.js, Vercel AI SDK, and AWS SDK for Bedrock support.
- **Gap**: JavaScript (not TypeScript) for Lambda functions means no type safety for agent tool interfaces. Python has the most mature agent framework ecosystem (LangChain, Strands Agents, CrewAI).
- **Recommendation**: Consider TypeScript for new agent Lambda functions to get type safety. For the agent orchestration layer specifically, evaluate Python with Strands Agents SDK or continue with TypeScript using `@aws-sdk/client-bedrock-runtime`.

#### APP-Q2: API Documentation
- **Score**: 1/4 ❌
- **Finding**: No OpenAPI/Swagger specification files found anywhere in the repository. No `openapi.yaml`, `swagger.json`, or API documentation annotations in source code. API routes are defined only programmatically in `lib/apigateway.ts` (product: GET/POST/PUT/DELETE, basket: GET/POST/DELETE/checkout, order: GET).
- **Gap**: Completely missing. Without OpenAPI specs, an agent cannot discover available tools or understand request/response schemas. This is the #1 blocker for agent tool integration — agents need machine-readable API descriptions to know what actions they can perform.
- **Recommendation**: Generate OpenAPI 3.0 specs for all three APIs. Export from API Gateway after deployment, or create manually using the route definitions in `lib/apigateway.ts`. Include request/response schemas derived from the DynamoDB table schemas in `lib/database.ts`. This is the single highest-impact action for agent enablement.

#### APP-Q3: Async vs Sync Communication
- **Score**: 2/4 🟠
- **Finding**: The checkout flow is async: basket Lambda → EventBridge (`PutEventsCommand` in `src/basket/index.js`) → SQS (`OrderQueue` in `lib/queue.ts`) → ordering Lambda. All other operations (product CRUD, basket CRUD, order queries) are synchronous API Gateway → Lambda → DynamoDB. Approximately 1 out of 12 API operations uses async communication (~8%).
- **Gap**: Most operations are synchronous. For agent workflows, long-running operations like order processing, returns, and refunds should be async with status polling, so the agent doesn't time out waiting.
- **Recommendation**: Extend the EventBridge event-driven pattern to more operations. Add async processing for bulk operations (e.g., inventory updates) with status polling endpoints. Leverage the existing EventBridge + SQS architecture as a template for new async flows.

#### APP-Q4: Monolith vs Microservices
- **Score**: 4/4 ✅
- **Finding**: Three separate Lambda microservices with independent concerns: (1) Product service (`src/product/index.js`) owns the `product` DynamoDB table, (2) Basket service (`src/basket/index.js`) owns the `basket` table and publishes checkout events, (3) Ordering service (`src/ordering/index.js`) owns the `order` table and consumes checkout events. Services communicate via EventBridge events — no direct Lambda-to-Lambda calls. Each has its own `package.json` with independent dependencies.
- **Gap**: None. Clean microservices boundaries with event-driven communication. Each service maps naturally to an agent tool domain (product lookup tool, basket management tool, order query tool).
- **Recommendation**: Maintain these service boundaries when adding agent capabilities. Each microservice becomes a distinct agent tool — the product service for catalog queries, basket service for cart operations, and ordering service for order status and history.

#### APP-Q5: API Response Format
- **Score**: 4/4 ✅
- **Finding**: All Lambda handlers return JSON responses via `JSON.stringify()`. Response format is consistent across all three services: `{ message: "Successfully finished operation: ...", body: <data> }`. Error responses also return JSON: `{ message: "Failed to perform operation.", errorMsg: ..., errorStack: ... }`.
- **Gap**: None for format. However, error responses expose `errorStack` which is a security concern (addressed in SEC-Q6).
- **Recommendation**: Standardize response schemas across all services. Add pagination support to list endpoints (`getAllProducts`, `getAllBaskets`, `getAllOrders`) which currently use DynamoDB `ScanCommand` without limits — an agent querying all products could receive massive payloads.

#### APP-Q6: Workflow Logic
- **Score**: 1/4 ❌
- **Finding**: Checkout workflow logic is hardcoded in `src/basket/index.js` in the `checkoutBasket` function: (1) `getBasket()` → (2) `prepareOrderPayload()` → (3) `publishCheckoutBasketEvent()` → (4) `deleteBasket()`. This is sequential imperative code with no orchestration service, no state management, and no compensation/rollback logic.
- **Gap**: No workflow orchestration. If the EventBridge publish succeeds but basket deletion fails, the system is in an inconsistent state. Agent-driven order management workflows (returns, cancellations, refund processing) will require orchestrated multi-step workflows with rollback capability.
- **Recommendation**: Refactor the checkout flow into an AWS Step Functions state machine using the saga pattern. Define compensation actions (e.g., cancel order if basket deletion fails). This pattern extends naturally to agent-driven workflows: the agent triggers a Step Function execution and polls for completion.

#### APP-Q7: Idempotency
- **Score**: 1/4 ❌
- **Finding**: No idempotency keys, conditional writes, or deduplication found. `PutItemCommand` in all three services uses unconditional puts — `src/product/index.js` (`createProduct`), `src/basket/index.js` (`createBasket`), `src/ordering/index.js` (`createOrder`). The SQS queue `OrderQueue` has no deduplication configured (standard queue, not FIFO). EventBridge `PutEventsCommand` has no idempotency token.
- **Gap**: Agents will retry failed tool calls. Without idempotency, a retry on `POST /basket/checkout` could create duplicate orders. A retry on `POST /product` could create duplicate products. This is a critical reliability gap for autonomous agent operations.
- **Recommendation**: Add `ConditionExpression: "attribute_not_exists(id)"` to `PutItemCommand` for product creation. Implement an idempotency key header on the checkout endpoint. Consider switching `OrderQueue` to a FIFO queue with deduplication ID based on checkout request hash.

#### APP-Q8: Rate Limiting & Throttling
- **Score**: 1/4 ❌
- **Finding**: No throttling configured on any of the three `LambdaRestApi` instances in `lib/apigateway.ts`. No `deployOptions.throttle` settings. No WAF rules. No application-level rate limiting middleware in any Lambda handler.
- **Gap**: An agent in a reasoning loop could send unlimited requests. No protection against abuse or runaway agent behavior. API Gateway default throttling (10,000 RPS account-level) provides no per-client control.
- **Recommendation**: Add `deployOptions: { throttlingBurstLimit: 50, throttlingRateLimit: 25 }` to each API Gateway. Create usage plans with API keys for agent clients vs human clients with different rate limits. Add WAF rate rules for additional protection.

#### APP-Q9: Resilience Patterns
- **Score**: 1/4 ❌
- **Finding**: No circuit breakers, retry logic, or timeout configurations in any Lambda handler. No Resilience4j, no retry decorators, no exponential backoff. The AWS SDK v3 in `src/*/ddbClient.js` has built-in retries for DynamoDB calls, but application-level resilience is absent. No try/catch with retry around the EventBridge `PutEventsCommand` in `src/basket/index.js`.
- **Gap**: If DynamoDB or EventBridge is temporarily unavailable, all operations fail with no retry at the application level. Agent tool calls will fail without graceful degradation, causing the agent to either retry blindly or give up entirely.
- **Recommendation**: Add explicit timeout configuration to Lambda functions in CDK (`timeout: Duration.seconds(10)`). Implement retry with exponential backoff for EventBridge publishes. Add circuit breaker logic for cross-service calls when agent orchestration is introduced.

#### APP-Q10: Long-running Processes
- **Score**: 2/4 🟠
- **Finding**: The checkout operation is handled asynchronously via EventBridge → SQS → ordering Lambda. This is a good pattern. However, there is no status polling endpoint — the checkout endpoint (`POST /basket/checkout`) publishes the event and returns immediately, but there is no way to query whether the order was successfully created.
- **Gap**: No status polling API for async operations. An agent processing a customer checkout cannot determine if the order was actually created without querying the order service separately and correlating by userName/time.
- **Recommendation**: Add a checkout status endpoint (e.g., `GET /basket/checkout/{checkoutId}`) that returns the status of the async order creation. Generate a unique checkout ID, include it in the EventBridge event, and store the status in DynamoDB. This enables agents to poll for completion: "Your order is being processed... Order confirmed!"

#### APP-Q11: API Versioning
- **Score**: 1/4 ❌
- **Finding**: No API versioning detected. No `/v1/` URL path prefixes in `lib/apigateway.ts`. No `Accept-Version` headers. No version annotations. API routes are `/product`, `/basket`, `/order` with no version segment.
- **Gap**: When agent tool schemas change (new fields, modified behavior), unversioned APIs will break existing agents. Versioning is essential for safe agent tool evolution.
- **Recommendation**: Add `/v1/` prefix to all API routes in `lib/apigateway.ts`. When adding agent-specific endpoints, start with `/v1/agent/` namespace to separate agent tool APIs from human-facing APIs.

#### APP-Q12: Service Discovery & Mesh
- **Score**: 3/4 🟡
- **Finding**: Services communicate via EventBridge events — no direct service-to-service HTTP calls. The basket Lambda references the event bus name via environment variable `EVENT_BUSNAME: "SwnEventBus"` set in `lib/microservice.ts`. This is a reasonable discovery pattern for event-driven serverless architectures.
- **Gap**: Event bus name is a hardcoded string `"SwnEventBus"` in CDK, not dynamically discovered. No API catalog or service registry for agent tool discovery.
- **Recommendation**: Use CDK to pass the event bus name dynamically (`bus.eventBusName`) instead of the hardcoded string. When adding agent capabilities, create an API catalog (e.g., via OpenAPI specs in S3) that agents can query to discover available tools.

#### APP-Q13: AI/Agent Frameworks
- **Score**: 1/4 ❌
- **Finding**: No AI or agent SDK imports found in any source file or dependency manifest. No `@aws-sdk/client-bedrock-runtime`, no `langchain`, no `openai`, no `strands-agents`, no `@anthropic-ai/sdk` in `src/product/package.json`, `src/basket/package.json`, or `src/ordering/package.json`. No MCP (Model Context Protocol) server implementations.
- **Gap**: Completely absent. This is the core gap for the agentic-ai-enablement goal. No foundation exists for building customer-facing AI agents for support and order management.
- **Recommendation**: Create a new agent microservice (e.g., `src/agent/`) with `@aws-sdk/client-bedrock-runtime` and `strands-agents` (or LangChain.js). Define agent tools that call the existing product, basket, and ordering APIs. Start with a read-only support agent that can answer product questions and look up order status.

### Data Foundations

#### DATA-Q1: Vector Database Presence
- **Score**: 1/4 ❌
- **Finding**: No vector database detected. No OpenSearch domain (`aws_opensearch_domain`), no Aurora with pgvector, no Pinecone/Weaviate/Chroma imports, no Bedrock Knowledge Bases, no S3 Vectors in any CDK file or dependency manifest.
- **Gap**: A customer support agent needs semantic search to match customer queries to relevant product information, order policies, and FAQ content. Without a vector database, the agent cannot perform RAG-based retrieval and must rely on exact keyword matching against DynamoDB.
- **Recommendation**: Create an Amazon Bedrock Knowledge Base backed by OpenSearch Serverless. Index product catalog data from the `product` DynamoDB table and any support documentation. This is the fastest path to semantic search for the customer support agent.

#### DATA-Q2: Vector DB Management
- **Score**: 1/4 ❌
- **Finding**: No vector database exists — nothing to evaluate for management approach.
- **Gap**: When a vector database is introduced for the customer support agent, it must be fully managed to avoid operational overhead.
- **Recommendation**: Use Amazon Bedrock Knowledge Bases (fully managed RAG) or OpenSearch Serverless (managed vector search). Avoid self-hosted Chroma or Weaviate for production agent workloads.

#### DATA-Q3: RAG Implementation
- **Score**: 1/4 ❌
- **Finding**: No document chunking, embedding generation, or semantic search patterns in any source file. No Bedrock Titan Embeddings calls, no `similarity_search`, no `knn_search`. No embedding model references in any dependency manifest.
- **Gap**: The customer support agent cannot retrieve contextual information from product descriptions, order histories, or support documentation without RAG. Direct DynamoDB queries require exact key lookups — a customer asking "What's your return policy for electronics?" cannot be answered.
- **Recommendation**: Implement a RAG pipeline: (1) Export product catalog and FAQ data to S3, (2) Create a Bedrock Knowledge Base with Titan Embeddings for chunking and indexing, (3) Add a `retrieve` tool to the agent that queries the Knowledge Base for relevant context before generating responses.

#### DATA-Q4: Data Source Sprawl
- **Score**: 3/4 🟡
- **Finding**: Three DynamoDB tables: `product`, `basket`, and `order` — all using the same DynamoDB technology. Each Lambda function accesses only its own table via its `ddbClient.js` module. No external API calls, no cross-database joins, no mixed database technologies.
- **Gap**: Clean separation, but the agent will need to query across all three tables to serve a customer (product details + basket contents + order history). No unified data access layer exists for cross-service queries.
- **Recommendation**: For the agent, create API-level aggregation rather than direct cross-table queries. The agent should call each service's API independently — this preserves service boundaries while giving the agent access to all data domains.

#### DATA-Q5: Data Access Pattern
- **Score**: 2/4 🟠
- **Finding**: DynamoDB operations are called directly in Lambda handlers using `ddbClient.send(new GetItemCommand(...))`, `ddbClient.send(new PutItemCommand(...))`, etc. in `src/product/index.js`, `src/basket/index.js`, and `src/ordering/index.js`. Business logic (e.g., `prepareOrderPayload` in basket) is intermixed with database operations in the same handler file.
- **Gap**: No data access abstraction layer. Business logic and data access are tightly coupled. When the agent needs to access data, it must go through the API layer (correct approach), but the internal code structure makes it difficult to add new data access patterns (e.g., search, filtering) without modifying handler logic.
- **Recommendation**: Extract data access operations into a repository/DAO module per service (e.g., `src/product/productRepository.js`). This separates business logic from data access and makes it easier to add agent-specific query patterns (e.g., product search by description for the support agent).

#### DATA-Q6: Unstructured Data
- **Score**: 1/4 ❌
- **Finding**: No S3 buckets, no Textract calls, no document parsing libraries. No PDF/image processing. Product data is structured in DynamoDB only.
- **Gap**: Customer support agents often need to reference unstructured documents (return policies, product manuals, warranty terms). No infrastructure exists for storing or parsing such documents.
- **Recommendation**: Create an S3 bucket for support documentation (PDFs, markdown files). Use Amazon Bedrock Knowledge Bases to ingest and index these documents for RAG-based retrieval by the support agent.

#### DATA-Q7: Schema Documentation
- **Score**: 2/4 🟠
- **Finding**: DynamoDB table schemas are implicitly defined in `lib/database.ts` via CDK: `product` (PK: `id` STRING), `basket` (PK: `userName` STRING), `order` (PK: `userName` STRING, SK: `orderDate` STRING). Additional attributes are documented in code comments (e.g., "product: PK: id -- name - description - imageFile - price - category"). The sample event `src/basket/checkoutbasketevents.json` shows the EventBridge event schema.
- **Gap**: Schemas are only in code comments — no formal schema documentation, no JSON Schema files, no data dictionary. The `checkoutbasketevents.json` provides a sample but not a formal schema. Agent tool definitions need formal request/response schemas.
- **Recommendation**: Create formal JSON Schema files for each service's data model. These schemas serve dual purpose: (1) request validation on API Gateway and (2) agent tool parameter definitions for structured input/output.

#### DATA-Q8: Data Access Layer
- **Score**: 2/4 🟠
- **Finding**: Each Lambda service has a `ddbClient.js` module (`src/product/ddbClient.js`, `src/basket/ddbClient.js`, `src/ordering/ddbClient.js`) that creates and exports the DynamoDB client. However, all database operations (get, put, scan, query, delete, update) are implemented directly in the handler `index.js` files, not in a separate repository layer.
- **Gap**: The DynamoDB client is extracted, but operations remain in handlers. No unified data access pattern. Each handler has its own bespoke query construction.
- **Recommendation**: Create a data access layer per service (e.g., `productRepository.js`, `basketRepository.js`, `orderRepository.js`) that encapsulates all DynamoDB operations. This enables reuse when adding agent-specific query endpoints and simplifies testing.

#### DATA-Q9: Embedding Freshness
- **Score**: 1/4 ❌
- **Finding**: No embeddings exist to refresh. No embedding generation, no indexing pipeline, no CDC (Change Data Capture) patterns. DynamoDB Streams are not enabled on any table.
- **Gap**: When embeddings are created for the customer support agent's knowledge base, they must stay current as products are added/updated and orders are placed. Without an automated refresh mechanism, the agent's knowledge will become stale.
- **Recommendation**: Enable DynamoDB Streams on the `product` table. Create a Lambda function triggered by stream events to update the Bedrock Knowledge Base when products are added, modified, or removed. This ensures the support agent always has current product information.

#### DATA-Q10: Database Engine Version & EOL
- **Score**: 4/4 ✅
- **Finding**: All databases are DynamoDB — a fully managed serverless service with no engine version to pin. DynamoDB is evergreen; AWS manages all version updates transparently. No RDS, DocumentDB, or ElastiCache instances to evaluate.
- **Gap**: None. DynamoDB has no EOL concerns.
- **Recommendation**: No action needed. Maintain DynamoDB for the core transactional data stores.

#### DATA-Q11: Stored Procedures & Schema Complexity
- **Score**: 4/4 ✅
- **Finding**: DynamoDB is NoSQL — no stored procedures, triggers, or proprietary SQL constructs. All business logic is in the application layer (Lambda functions). No `.sql` files in the repository. No ORM bypass patterns.
- **Gap**: None. All business logic is in the application layer, which is the ideal pattern for agent-accessible services.
- **Recommendation**: No action needed. Continue keeping all business logic in the application layer to maintain agent accessibility.

### Identity, Security & Governance

#### SEC-Q1: Secret Management
- **Score**: 2/4 🟠
- **Finding**: No hardcoded secrets (passwords, API keys) found in any source file. Environment variables set in `lib/microservice.ts` contain non-sensitive values: `PRIMARY_KEY`, `DYNAMODB_TABLE_NAME`, `EVENT_SOURCE`, `EVENT_DETAILTYPE`, `EVENT_BUSNAME`. No AWS Secrets Manager or Parameter Store usage. No `.env` files committed.
- **Gap**: No established secret management pattern. When agent infrastructure is added (Bedrock API keys, third-party integration secrets, webhook signing keys), there is no pattern for secure secret storage and retrieval.
- **Recommendation**: Establish a Secrets Manager pattern in CDK now, even if current secrets are minimal. When adding Bedrock agent configuration, store model IDs, guardrail configurations, and any API keys in Secrets Manager with Lambda access via CDK `Secret.fromSecretNameV2()`.

#### SEC-Q2: IAM Least Privilege
- **Score**: 3/4 🟡
- **Finding**: CDK uses `grantReadWriteData()` in `lib/microservice.ts` to give each Lambda function DynamoDB access scoped to its own table. `grantPutEventsTo()` scopes EventBridge access to the basket Lambda. These are CDK high-level grants — better than wildcard policies but broader than strictly necessary.
- **Gap**: `grantReadWriteData()` gives full read/write to the entire table. The product Lambda could use read-only for GET operations. The ordering Lambda's SQS event source permissions are implicitly granted by `addEventSource()` — correct but not explicitly documented. No per-function IAM policy audit.
- **Recommendation**: For the ordering Lambda, use `grantWriteData()` instead of `grantReadWriteData()` since it only writes orders. For agent Lambda functions, create highly scoped IAM roles: read-only for product lookups, write access only for specific operations that the agent is authorized to perform.

#### SEC-Q3: Identity Propagation
- **Score**: 1/4 ❌
- **Finding**: No JWT, OAuth, Cognito, or any identity propagation mechanism. The `userName` parameter in basket and ordering services is passed as a URL path parameter (`{userName}`) — this is user-supplied, unauthenticated input. Any caller can access any user's basket or orders by guessing usernames.
- **Gap**: Critical. An agent acting on behalf of a customer must propagate the customer's authenticated identity through all service calls. Currently, the agent (or any caller) can access any user's data by specifying any `userName` in the URL path.
- **Recommendation**: Implement Amazon Cognito User Pool with JWT tokens. Replace the `{userName}` path parameter with the authenticated user identity from the JWT claims (`event.requestContext.authorizer.claims.sub`). The agent must pass the customer's JWT token when making API calls on their behalf.

#### SEC-Q4: Audit Logging
- **Score**: 1/4 ❌
- **Finding**: No CloudTrail configuration in CDK. Lambda functions use `console.log` for basic request logging (e.g., `console.log("request:", JSON.stringify(event, undefined, 2))` in all handlers). No structured audit trail, no immutable log storage, no CloudWatch Log retention policies configured.
- **Gap**: No audit trail for agent actions. When an autonomous agent modifies baskets, processes checkouts, or deletes products, there must be an immutable audit log showing what the agent did, on behalf of which customer, and when.
- **Recommendation**: Add CloudTrail in CDK with S3 log storage and log file validation. Configure CloudWatch Log retention policies for Lambda log groups. For agent actions specifically, implement structured audit events published to EventBridge with agent ID, customer ID, action, and outcome.

#### SEC-Q5: API Rate Limits
- **Score**: 1/4 ❌
- **Finding**: No throttling configured on any `LambdaRestApi` in `lib/apigateway.ts`. No `deployOptions.throttle` property. No API Gateway usage plans or API keys. No WAF rate-based rules.
- **Gap**: No per-client rate limiting. An agent in a tool-calling loop or a malicious actor could make unlimited API calls. No differentiation between agent traffic and human traffic.
- **Recommendation**: Add throttle settings to API Gateway: `deployOptions: { throttlingBurstLimit: 100, throttlingRateLimit: 50 }`. Create separate usage plans with different rate limits for agent clients (higher, but bounded) and human clients. Implement API keys for agent authentication.

#### SEC-Q6: PII Redaction
- **Score**: 1/4 ❌
- **Finding**: All three Lambda handlers log full request payloads including PII: `console.log("request:", JSON.stringify(event, undefined, 2))`. Error responses in `src/product/index.js`, `src/basket/index.js`, and `src/ordering/index.js` expose `errorMsg` and `errorStack` to API consumers. The order data includes `firstName`, `lastName`, `email`, `address`, `paymentMethod`, `cardInfo` (per `lib/database.ts` comments).
- **Gap**: PII (names, emails, addresses, payment information) is logged to CloudWatch without redaction. Error stack traces are returned to API consumers. When agents process customer data, PII exposure in logs becomes a compliance risk (GDPR, PCI-DSS).
- **Recommendation**: Implement a log sanitization utility that redacts PII fields (email, address, cardInfo, paymentMethod) before logging. Remove `errorStack` from error responses — return generic error messages to API consumers. Add CloudWatch Log data protection policies to detect and mask PII automatically.

#### SEC-Q7: Human Approval Workflows
- **Score**: 1/4 ❌
- **Finding**: No human approval gates for any operation. `DELETE /product/{id}`, `DELETE /basket/{userName}`, and `POST /basket/checkout` execute immediately without confirmation. No Step Functions with human approval tasks. No approval API endpoints.
- **Gap**: Critical for agentic AI. An agent that can delete products, clear baskets, and process checkouts without human approval is a high-risk deployment. Agent actions with financial impact (checkout) or destructive consequences (delete) must require human-in-the-loop confirmation.
- **Recommendation**: Implement a Step Functions workflow with a `waitForTaskToken` state for high-risk agent actions: product deletion, checkout processing, and bulk operations. The agent initiates the action, a human approves via a notification (Slack, email, dashboard), and the workflow continues. Start with checkout approval for the customer support agent.

#### SEC-Q8: Encryption at Rest
- **Score**: 2/4 🟠
- **Finding**: DynamoDB tables in `lib/database.ts` do not specify `encryption` property — DynamoDB encrypts at rest by default using AWS-owned keys. No customer-managed KMS keys (`aws_kms_key`) configured. No S3 buckets exist to evaluate.
- **Gap**: AWS-managed encryption is the minimum. Customer-managed KMS keys provide additional control (key rotation, access policies, audit via CloudTrail) for sensitive order and payment data.
- **Recommendation**: Add `encryption: TableEncryption.CUSTOMER_MANAGED` with a dedicated KMS key for the `order` table, which contains PII and payment information. This is especially important when agents access customer data — KMS key policies can restrict which IAM roles (including agent roles) can decrypt data.

#### SEC-Q9: API Authentication
- **Score**: 1/4 ❌
- **Finding**: All three `LambdaRestApi` instances in `lib/apigateway.ts` have no authorizers configured. No `defaultMethodOptions.authorizationType`, no Cognito authorizer, no Lambda authorizer, no API keys required. All endpoints are publicly accessible without any authentication.
- **Gap**: Critical. All product, basket, and order data is accessible to anyone with the API URL. An agent interacting with these APIs cannot verify customer identity. Deploying a customer support agent on unauthenticated APIs means the agent could access and modify any customer's data.
- **Recommendation**: Add a Cognito User Pool and configure JWT authorizer on all API Gateway endpoints: `defaultMethodOptions: { authorizationType: AuthorizationType.COGNITO, authorizer: new CognitoUserPoolsAuthorizer(...) }`. The agent service should use service-to-service auth (IAM or client credentials) while customer-facing requests use Cognito JWT tokens.

#### SEC-Q10: Centralized Identity
- **Score**: 1/4 ❌
- **Finding**: No identity provider configured anywhere. No `aws_cognito_user_pool`, no OIDC/SAML federation, no SSO. User identity is represented only as a `userName` string passed in URL path parameters.
- **Gap**: No centralized identity management. Customer support agents must authenticate customers and maintain session context. Without a centralized IdP, there is no way to verify customer identity, manage agent service accounts, or implement role-based access control for agent capabilities.
- **Recommendation**: Deploy Amazon Cognito User Pool for customer authentication. Create a Cognito app client for the agent service with appropriate OAuth scopes. Implement user pools for customers and service accounts, enabling the agent to authenticate customers and operate within their permission scope.

### Operations & Observability

#### OPS-Q1: Distributed Tracing
- **Score**: 1/4 ❌
- **Finding**: No X-Ray, OpenTelemetry, or any distributed tracing SDK in any dependency manifest or source file. No `aws-xray-sdk` in any `package.json`. No trace ID propagation headers. No `tracing: lambda.Tracing.ACTIVE` in CDK Lambda configuration (`lib/microservice.ts`).
- **Gap**: No ability to trace requests across the product → basket → EventBridge → SQS → ordering flow. When an agent orchestrates calls across all three services, there is no way to reconstruct the complete execution path if something fails.
- **Recommendation**: Enable X-Ray tracing on all Lambda functions by adding `tracing: lambda.Tracing.ACTIVE` in `lib/microservice.ts`. Enable X-Ray on API Gateway. This provides automatic trace propagation across Lambda, DynamoDB, EventBridge, and SQS with minimal code changes.

#### OPS-Q2: Structured Logging
- **Score**: 1/4 ❌
- **Finding**: All Lambda handlers use `console.log()` and `console.error()` for logging. Example from `src/product/index.js`: `console.log("request:", JSON.stringify(event, undefined, 2))`. Logs are unstructured text with no consistent JSON format, no correlation IDs, no request IDs, and no log levels.
- **Gap**: No structured logging. CloudWatch Log Insights queries will be difficult. When an agent makes multiple API calls, there is no correlation ID to link related log entries across services.
- **Recommendation**: Replace `console.log` with a structured logger (e.g., `@aws-lambda-powertools/logger` for Node.js). This provides automatic JSON formatting, correlation IDs, request context injection, and log level support. Lambda Powertools is the fastest path to structured logging for Lambda functions.

#### OPS-Q3: Automated Evals
- **Score**: 1/4 ❌
- **Finding**: No evaluation framework, no golden datasets, no LLM testing infrastructure. No AI/agent code exists to evaluate. No eval scripts, scoring functions, or RAGAS integration.
- **Gap**: When the customer support agent is built, there is no infrastructure for evaluating agent quality: response accuracy, hallucination rate, tool-calling success rate, or customer satisfaction scores.
- **Recommendation**: Create an agent evaluation pipeline before deploying the customer support agent to production. Define golden datasets of customer queries with expected responses. Implement automated scoring using Amazon Bedrock model evaluation or custom eval scripts that measure: (1) tool selection accuracy, (2) response relevance, (3) PII handling compliance, (4) customer satisfaction proxy metrics.

#### OPS-Q4: SLOs
- **Score**: 1/4 ❌
- **Finding**: No SLO definitions in any configuration file or CDK construct. No CloudWatch alarms (`aws_cloudwatch_metric_alarm`). No latency targets, error rate budgets, or availability objectives defined.
- **Gap**: No performance baselines or objectives. When agent traffic is added, there is no way to detect if agent calls are degrading API performance for human users, or if agent response times exceed acceptable thresholds for customer support interactions.
- **Recommendation**: Define SLOs for each API: p99 latency < 500ms, error rate < 1%, availability > 99.9%. Add CloudWatch alarms in CDK for Lambda duration, error count, and throttle count. For the agent, add agent-specific SLOs: tool call success rate > 95%, end-to-end response time < 5 seconds.

#### OPS-Q5: Rollback Capability
- **Score**: 1/4 ❌
- **Finding**: No deployment pipeline exists (see INF-Q6). No blue/green deployment, no canary deployment, no CodeDeploy configuration. No Lambda versioning or alias-based traffic shifting. No feature flags. Manual `cdk deploy` is the only deployment mechanism.
- **Gap**: No safe rollback. A bad deployment affecting agent behavior (wrong prompt, broken tool, regression) cannot be quickly reversed. Agent prompt and configuration changes need the same rollback capability as code changes.
- **Recommendation**: Implement Lambda aliases with CodeDeploy traffic shifting for canary deployments. Store agent prompts and tool configurations in versioned locations (S3 with versioning, or DynamoDB with version attribute) so they can be rolled back independently of code.

#### OPS-Q6: LLM Cost Tracking
- **Score**: 1/4 ❌
- **Finding**: No LLM usage in the application. No token counting, no cost attribution, no usage tracking. No CloudWatch custom metrics for any billing-related data.
- **Gap**: When Bedrock is introduced for the customer support agent, token usage per conversation, per customer, and per tool call must be tracked to manage costs and detect anomalies (e.g., an agent stuck in a reasoning loop consuming excessive tokens).
- **Recommendation**: When implementing the agent, log the `usage` object from Bedrock responses (inputTokens, outputTokens, totalTokens). Publish CloudWatch custom metrics: tokens per conversation, tokens per tool call, cost per customer interaction. Set budget alarms for daily token spend. Implement tiered log retention: keep full agent traces for 7 days, summaries for 90 days.

#### OPS-Q7: Business Metrics
- **Score**: 1/4 ❌
- **Finding**: No custom CloudWatch metrics for business outcomes. No metrics published for order count, checkout success rate, basket abandonment rate, average order value, or any business KPI. Only default Lambda metrics (invocations, duration, errors) exist.
- **Gap**: No business outcome tracking. For the customer support agent, metrics like resolution rate, escalation rate, customer satisfaction, and revenue impact of agent-assisted purchases are essential to measure agent value.
- **Recommendation**: Add `cloudwatch.putMetricData` calls for: orders created, checkout success/failure, product queries. For the agent, add: conversations resolved, escalations to human, customer satisfaction score, order modifications by agent. These metrics demonstrate agent ROI.

#### OPS-Q8: Anomaly Detection
- **Score**: 1/4 ❌
- **Finding**: No CloudWatch alarms of any kind. No anomaly detection. No error rate monitoring. No PagerDuty/OpsGenie integration. No composite alarms.
- **Gap**: No alerting for any failure condition. A broken Lambda, a DynamoDB throttle, or an EventBridge delivery failure would go unnoticed until customers report issues. Agents can cause harm at machine speed — a misconfigured agent could place hundreds of incorrect orders before anyone notices.
- **Recommendation**: Add CloudWatch alarms for: Lambda error rate > 5%, Lambda p99 duration > 3 seconds, SQS dead letter queue depth > 0, API Gateway 5xx rate > 1%. For the agent, add anomaly detection on: tool calls per conversation (detect reasoning loops), error rate per tool, response latency spikes.

#### OPS-Q9: Deployment Strategy
- **Score**: 1/4 ❌
- **Finding**: No deployment pipeline. Deployment is manual `cdk deploy` as documented in `README.md`. No staging environment, no canary deployment, no blue/green switching. No CodeDeploy, Argo Rollouts, or feature flags.
- **Gap**: All deployments go directly to production with no gradual rollout or automated rollback. When iterating on agent behavior (prompts, tools, guardrails), every change is immediately exposed to all customers.
- **Recommendation**: Create a multi-stage deployment pipeline: dev → staging → production with manual approval gate before production. Use Lambda weighted aliases for canary deployment of agent Lambda functions (route 10% of traffic to new version, monitor, then promote). This enables safe agent iteration.

#### OPS-Q10: Integration Testing
- **Score**: 1/4 ❌
- **Finding**: `test/aws-microservices.test.ts` exists but all test code is commented out. The only active line is `test('SQS Queue Created', () => {});` — an empty test. Jest configuration exists in `jest.config.js` but runs no meaningful tests. No integration tests, no API tests, no contract tests.
- **Gap**: No test coverage. Changes to any Lambda handler could break API contracts without detection. When adding agent tools that depend on specific API response schemas, any undetected schema change breaks the agent.
- **Recommendation**: Implement integration tests that verify: (1) product CRUD operations, (2) basket lifecycle (create → add items → checkout), (3) EventBridge event delivery to SQS, (4) order creation from SQS events. Use `aws-cdk-lib/assertions` for CDK stack tests. Add these to the CI/CD pipeline as a gate before deployment.

#### OPS-Q11: Incident Response Automation
- **Score**: 1/4 ❌
- **Finding**: No runbooks (markdown, YAML, or JSON). No SSM Automation documents. No Lambda-based remediation functions. No self-healing patterns. No incident response workflow of any kind.
- **Gap**: No automated incident response. When the agent causes an issue (e.g., processes a batch of incorrect orders), there is no automated remediation, no runbook to follow, and no escalation workflow.
- **Recommendation**: Create runbooks for common failure scenarios: SQS DLQ messages (manual order creation), Lambda throttling (increase concurrency limits), DynamoDB capacity alerts. Store as markdown in the repository. When the agent is deployed, create agent-specific runbooks: agent reasoning loop (kill agent session), agent making incorrect modifications (rollback recent changes via DynamoDB point-in-time recovery).

#### OPS-Q12: Observability Governance & Ownership
- **Score**: 1/4 ❌
- **Finding**: No CODEOWNERS file. No SLO ownership definitions. No observability dashboards. No platform team tooling. No service ownership model documented.
- **Gap**: No ownership model for observability. When agent issues arise, there is no clear escalation path — who owns the agent's behavior? Who owns the APIs the agent calls? Who monitors agent quality?
- **Recommendation**: Create a CODEOWNERS file mapping service ownership. Define an agent quality owner responsible for monitoring agent SLOs (response accuracy, tool success rate, customer satisfaction). Establish a shared responsibility model: platform team owns infrastructure observability, product team owns agent behavior observability.

---

## Recommended Modernization Pathways

Based on the assessment findings, the following AWS Modernization Pathways are evaluated for this application. Multiple pathways can execute in parallel because modern applications comprise multiple interconnected components — each requiring its own modernization approach.

### Pathway Summary

| Pathway | Status | Goal Alignment | Priority | Key Trigger Criteria | Est. Effort |
|---------|--------|---------------|----------|---------------------|-------------|
| Move to Cloud Native | Triggered | Medium | Low | APP-Q3: 2/4, APP-Q10: 2/4 | Low |
| Move to Containers | Triggered | Medium | Low | No Dockerfile found | Low |
| Move to Open Source | Not Triggered | Low | — | — | — |
| Move to Managed Databases | Triggered | High | High | DATA-Q2: 1/4 | Medium |
| Move to Managed Analytics | Triggered | Low | High | INF-Q8: 1/4 | Low |
| Move to Modern DevOps | Triggered | High | High | INF-Q6: 1/4, OPS-Q9: 1/4, OPS-Q10: 1/4, OPS-Q1: 1/4 | High |
| Move to AI | Triggered | High | High | APP-Q13: 1/4, DATA-Q1: 1/4, DATA-Q3: 1/4, OPS-Q3: 1/4, OPS-Q6: 1/4 | High |

### Parallel Execution Plan

**Parallel Track 1 (Immediate — Days 1–30)**: Move to Modern DevOps + Move to AI (initial setup) — CI/CD pipeline creation and agent framework prototyping can proceed simultaneously with no dependencies.

**Parallel Track 2 (Months 1–3)**: Move to Managed Databases (vector DB) + Move to Cloud Native (async patterns) + Move to Containers (Dockerfile creation) — these can run concurrently.

**Sequential Dependencies**: Move to AI depends on Move to Managed Databases (vector database must exist before RAG pipeline). Move to Cloud Native (Step Functions orchestration) should precede advanced agent workflow patterns. Move to Modern DevOps (CI/CD) should be established before deploying agent services to production.

### Move to Modern DevOps

- **Priority**: High
- **Goal Alignment**: High
- **Trigger Criteria Met**:
  - INF-Q6: Score 1/4 — No CI/CD pipeline exists; deployment is manual `cdk deploy`
  - OPS-Q9: Score 1/4 — No deployment strategy; no canary or blue/green deployments
  - OPS-Q10: Score 1/4 — All tests commented out in `test/aws-microservices.test.ts`
  - OPS-Q1: Score 1/4 — No distributed tracing; no X-Ray or OpenTelemetry
- **Current State**: Manual `cdk deploy` with no test automation, no CI/CD, no monitoring, and no safe deployment patterns. Changes go directly to production with no validation.
- **Target State**: Automated CI/CD pipeline with lint → test → synth → deploy stages, canary deployments via Lambda aliases, distributed tracing with X-Ray, and structured logging with Lambda Powertools.
- **Key Activities**:
  1. Create GitHub Actions or CodePipeline CI/CD pipeline
  2. Implement CDK stack tests and Lambda integration tests
  3. Enable X-Ray tracing on all Lambda functions and API Gateway
  4. Add Lambda Powertools for structured logging with correlation IDs
  5. Configure Lambda aliases with CodeDeploy for canary deployments
- **Dependencies**: None — this should be the first pathway started
- **Estimated Effort**: High
- **Roadmap Phase Alignment**: Phase 1 (Agent Quick Wins) for CI/CD and tracing; Phase 2 for advanced deployment strategies
- **Relevant Learning Materials**: Module 6 — Move to Modern DevOps

### Move to AI

- **Priority**: High
- **Goal Alignment**: High
- **Trigger Criteria Met**:
  - APP-Q13: Score 1/4 — No AI/agent frameworks in any dependency
  - DATA-Q1: Score 1/4 — No vector database for semantic search
  - DATA-Q3: Score 1/4 — No RAG implementation
  - OPS-Q3: Score 1/4 — No agent evaluation framework
  - OPS-Q6: Score 1/4 — No LLM cost tracking
- **Current State**: No AI capabilities whatsoever. No Bedrock integration, no vector database, no embeddings, no agent frameworks. The application is a traditional CRUD e-commerce system.
- **Target State**: Customer-facing AI agent for support and order management using Amazon Bedrock, with RAG pipeline for product/policy knowledge retrieval, agent tools mapped to existing microservice APIs, automated evaluation pipeline, and LLM cost tracking.
- **Key Activities**:
  1. Create agent microservice with Amazon Bedrock and Strands Agents SDK
  2. Generate OpenAPI specs for existing APIs to enable agent tool discovery
  3. Set up Amazon Bedrock Knowledge Base with OpenSearch Serverless for product/policy RAG
  4. Define agent tools: product lookup, order status query, basket management
  5. Build agent evaluation pipeline with golden datasets for customer support scenarios
  6. Implement LLM cost tracking with CloudWatch custom metrics
- **Dependencies**: Move to Managed Databases (for vector database), Move to Modern DevOps (for safe agent deployment)
- **Estimated Effort**: High
- **Roadmap Phase Alignment**: Phase 1 for initial agent prototype; Phase 2 for RAG and tools; Phase 3 for production agent with evals
- **Relevant Learning Materials**: Module 7 — Move to AI

### Move to Managed Databases

- **Priority**: High
- **Goal Alignment**: High
- **Trigger Criteria Met**:
  - DATA-Q2: Score 1/4 — No vector database exists (managed or otherwise)
- **Current State**: Core transactional databases are already DynamoDB (fully managed — score 4/4). However, the vector database capability needed for agent RAG does not exist.
- **Target State**: DynamoDB for transactional data (already in place) + managed vector database (OpenSearch Serverless or Bedrock Knowledge Base) for semantic search.
- **Key Activities**:
  1. Create Amazon Bedrock Knowledge Base with OpenSearch Serverless collection
  2. Configure data source sync from product DynamoDB table to Knowledge Base
  3. Enable DynamoDB Streams for real-time embedding updates
- **Dependencies**: None — DynamoDB is already managed; this adds the vector database layer
- **Estimated Effort**: Medium
- **Roadmap Phase Alignment**: Phase 2 (Agent Foundations) for Knowledge Base setup
- **Relevant Learning Materials**: Module 4 — Move to Managed Databases

### Move to Cloud Native

- **Priority**: Low
- **Goal Alignment**: Medium
- **Trigger Criteria Met**:
  - APP-Q3: Score 2/4 — Only ~8% of operations are async; most are synchronous API Gateway → Lambda → DynamoDB
  - APP-Q10: Score 2/4 — Checkout is async but no status polling endpoint
- **Current State**: Architecture is already serverless (Lambda + DynamoDB + API Gateway) with event-driven checkout via EventBridge + SQS. Three independently deployable microservices.
- **Target State**: Extended async patterns with Step Functions orchestration for multi-step agent workflows, status polling APIs for all async operations, and expanded EventBridge event patterns.
- **Key Activities**:
  1. Add Step Functions for checkout workflow (saga pattern with compensation)
  2. Add status polling endpoint for async checkout operations
  3. Extend EventBridge patterns for agent-triggered events (returns, refunds)
  4. Add DLQ to SQS OrderQueue for failed message handling
- **Dependencies**: None — builds on existing EventBridge + SQS foundation
- **Estimated Effort**: Low
- **Roadmap Phase Alignment**: Phase 2 (Agent Foundations) for Step Functions; Phase 3 for extended event patterns
- **Relevant Learning Materials**: Module 2 — Move to Cloud Native (Containers and Serverless)

### Move to Containers

- **Priority**: Low
- **Goal Alignment**: Medium
- **Trigger Criteria Met**:
  - No Dockerfile found — while the application is serverless (Lambda), containerization enables local development, testing, and potential ECS/Fargate deployment for the agent service
- **Current State**: All functions are Lambda-deployed via CDK `NodejsFunction`. No Dockerfiles or container definitions exist. Docker is listed as a prerequisite in `README.md` but only for CDK bundling.
- **Target State**: Dockerfiles for local development and testing. Optionally, ECS Fargate for the agent service if Lambda's 15-minute timeout is insufficient for complex agent conversations.
- **Key Activities**:
  1. Create Dockerfiles for local Lambda testing using Lambda container images
  2. Add docker-compose for local development environment (LocalStack or SAM local)
  3. Evaluate ECS Fargate for the agent orchestration service if conversation length exceeds Lambda timeout
- **Dependencies**: None
- **Estimated Effort**: Low
- **Roadmap Phase Alignment**: Phase 1 (Agent Quick Wins) for local development; Phase 3 if ECS migration needed
- **Relevant Learning Materials**: Module 3 — Move to Containers with Amazon ECS and EKS

### Move to Managed Analytics

- **Priority**: Low (secondary to agent enablement)
- **Goal Alignment**: Low
- **Trigger Criteria Met**:
  - INF-Q8: Score 1/4 — No real-time streaming services (Kinesis, MSK)
- **Current State**: No analytics or streaming infrastructure. EventBridge provides event routing but not data streaming. No data lake, no analytics pipeline.
- **Target State**: DynamoDB Streams for CDC, optional Kinesis for real-time analytics on agent interactions and customer behavior.
- **Key Activities**:
  1. Enable DynamoDB Streams on all tables for CDC
  2. Add Kinesis Data Firehose for agent interaction analytics to S3
  3. Optional: Athena for ad-hoc analysis of agent conversation logs
- **Dependencies**: Move to AI (agent must exist before analytics on agent interactions are useful)
- **Estimated Effort**: Low
- **Roadmap Phase Alignment**: Phase 3 (Agent Scale & Optimization)
- **Relevant Learning Materials**: Module 5 — Move to Managed Analytics

---

## Quick Agent Wins

Even before completing the full modernization roadmap, these agent opportunities are available based on your current architecture:

1. **Customer Support Agent with Existing APIs** — Your three microservice APIs (product, basket, ordering) already expose structured JSON endpoints that an agent can invoke as tools. Build a customer support agent that can look up product details (`GET /product/{id}`), check order status (`GET /order/{userName}`), and view basket contents (`GET /basket/{userName}`).
   - **Leverages**: Existing API Gateway endpoints defined in `lib/apigateway.ts` with structured JSON responses
   - **Effort**: Medium (requires generating OpenAPI specs and creating an agent Lambda)
   - **Value**: Enables automated customer support for "Where is my order?" and "What products do you have?" queries

2. **Agent Tool Integration via JSON APIs** — All three services return structured JSON responses (e.g., `{ message: "...", body: <data> }`). This consistent format means agent tool parsers can be standardized across all services without custom response handling.
   - **Leverages**: Consistent JSON response format across `src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js`
   - **Effort**: Low
   - **Value**: Simplifies agent tool development — one response parser works for all services

3. **Order Management Knowledge Agent** — Your `README.md` contains architecture documentation, and the `lib/database.ts` comments describe the complete data model (product schema, basket schema, order schema with customer details). Build a RAG-based knowledge agent using this documentation to answer internal team questions about the system.
   - **Leverages**: `README.md` with architecture description, code comments in `lib/database.ts` with schema documentation
   - **Effort**: Low
   - **Value**: Accelerates onboarding and reduces internal support load for "How does checkout work?" questions

4. **Natural Language Order Query Agent** — The `order` DynamoDB table has a clear schema (PK: `userName`, SK: `orderDate`) with customer details. Build a customer support agent that translates natural language queries ("Show me recent orders for customer Jane") into DynamoDB queries via the existing `GET /order/{userName}?orderDate=timestamp` endpoint.
   - **Leverages**: Well-defined order table schema in `lib/database.ts`, existing order query API in `src/ordering/index.js`
   - **Effort**: Medium
   - **Value**: Enables customer support agents to quickly look up order information using natural language instead of navigating admin tools

5. **DevOps Deployment Agent** — Once a CI/CD pipeline is established (Phase 1 priority), build a DevOps agent that can trigger `cdk diff`, check deployment status, and report on stack changes. The existing CDK IaC provides a clear interface for deployment operations.
   - **Leverages**: Comprehensive CDK IaC in `lib/aws-microservices-stack.ts` covering the complete infrastructure
   - **Effort**: Medium (requires CI/CD pipeline first)
   - **Value**: Enables "Deploy latest changes to staging" and "What changed in the last deployment?" conversational DevOps

> These opportunities can be pursued in parallel with the modernization roadmap.
> They demonstrate agent value early while foundations are being built.

---

## Readiness Roadmap

### Phase 1 — Agent Quick Wins (Days 1–30)

These items are low-effort, high-impact actions that establish the foundation for agent development:

1. **Generate OpenAPI 3.0 specs** for all three APIs (product, basket, ordering) from the route definitions in `lib/apigateway.ts`. Include request/response schemas derived from the DynamoDB table definitions in `lib/database.ts`. This is the #1 enabler for agent tool integration.
2. **Create a CI/CD pipeline** using GitHub Actions or AWS CodePipeline with stages: lint → `npm test` → `cdk synth` → `cdk diff` → deploy. Uncomment and implement the CDK stack tests in `test/aws-microservices.test.ts`.
3. **Enable X-Ray tracing** on all Lambda functions by adding `tracing: lambda.Tracing.ACTIVE` in `lib/microservice.ts`. Enable X-Ray on all three API Gateway instances in `lib/apigateway.ts`.
4. **Upgrade Lambda runtime** from `NODEJS_14_X` (EOL) to `NODEJS_20_X` or `NODEJS_22_X` in `lib/microservice.ts` for all three functions.
5. **Add API Gateway authentication** — deploy Amazon Cognito User Pool and configure authorizers on all endpoints in `lib/apigateway.ts`. This is a security prerequisite before any agent can be deployed.
6. **Prototype a read-only support agent** — create a new `src/agent/` directory with a Lambda function using `@aws-sdk/client-bedrock-runtime` that can call the existing product and order GET APIs to answer "What products are available?" and "What is the status of my order?" queries.

### Phase 2 — Agent Foundations (Months 1–3)

Structural improvements that enable production-ready agent capabilities:

1. **Set up Amazon Bedrock Knowledge Base** with OpenSearch Serverless for RAG. Index product catalog data from the `product` DynamoDB table and support documentation (return policies, FAQ). Enable DynamoDB Streams on the `product` table for automated embedding updates.
2. **Implement Step Functions** for the checkout workflow using the saga pattern. Replace the hardcoded sequence in `src/basket/index.js` (`checkoutBasket` function) with a state machine that includes compensation logic and can be triggered by agents. Add a `waitForTaskToken` state for human approval of agent-initiated checkouts.
3. **Add idempotency** to all write operations. Add `ConditionExpression: "attribute_not_exists(id)"` to product creation. Implement idempotency keys on the checkout endpoint. Consider FIFO SQS queue with deduplication for order processing.
4. **Implement structured logging** with `@aws-lambda-powertools/logger` across all Lambda functions. Add PII redaction for order data (email, address, cardInfo). Remove `errorStack` from API error responses.
5. **Add API Gateway throttling** — configure `deployOptions.throttle` on all three API Gateways. Create separate usage plans for agent and human traffic.
6. **Define SLOs** — add CloudWatch alarms for Lambda error rates, duration p99, and API Gateway 5xx rates. Define agent-specific SLOs: tool call success rate, response latency.
7. **Build agent tools** that wrap each microservice API: `lookupProduct`, `searchProducts`, `getOrderStatus`, `getOrderHistory`, `viewBasket`, `processCheckout`. Include proper error handling and retry logic.

### Phase 3 — Agent Scale & Optimization (Months 3–6)

Advanced capabilities that optimize the agent for production customer support:

1. **Deploy production customer support agent** with full tool suite: product search, order lookup, basket management, checkout with human approval. Implement Bedrock Guardrails for content filtering and topic control.
2. **Build agent evaluation pipeline** — create golden datasets of 100+ customer support scenarios with expected tool calls and responses. Implement automated scoring for tool selection accuracy, response relevance, and PII handling compliance. Run evals in CI/CD before deploying agent changes.
3. **Implement LLM cost tracking** — log token usage per conversation from Bedrock responses. Publish CloudWatch custom metrics for tokens per interaction, cost per customer. Set budget alarms. Implement tiered log retention.
4. **Add business metrics** — track agent resolution rate, escalation-to-human rate, customer satisfaction scores, and revenue from agent-assisted purchases. Create CloudWatch dashboards showing agent ROI.
5. **Implement anomaly detection** — configure CloudWatch anomaly detection on agent tool call patterns (detect reasoning loops), error rates, and latency. Set up alerting via SNS to on-call teams.
6. **Extend event-driven patterns** — add EventBridge events for agent actions (agent_checkout_initiated, agent_order_queried) for audit trail and analytics. Enable DynamoDB Streams on all tables for real-time analytics via Kinesis Data Firehose.
7. **Create agent-specific runbooks** — document procedures for: agent reasoning loop (kill session, review conversation), agent making incorrect modifications (DynamoDB PITR rollback), agent PII exposure (log purge procedure). Store as machine-readable YAML for future automation.

---

## Recommended Self-Paced Learning Materials

**Module 2: Move to Cloud Native (Containers and Serverless):**
- Cloud Design Patterns, Architectures, and Implementations — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html
  - Essential reference for microservices patterns: Saga orchestration for checkout workflow, Event Sourcing for event-driven communication, Circuit Breaker for resilience
- AWS Modernization Pathways: Move to Cloud Native Serverless — https://skillbuilder.aws/learning-plan/CMK2J48MVN/aws-modernization-pathways-move-to-cloud-native-serverless-includes-labs/EFUPP53B4Q
- Lambda Foundations — https://skillbuilder.aws/learn/XHRS91KKK6/aws-lambda-foundations/R85JRN3APC
- Architecting Serverless Applications — https://skillbuilder.aws/learn/MRWENY7FSX/architecting-serverless-applications/QVFY2JHVEH
- Amazon API Gateway for Serverless Applications — https://skillbuilder.aws/learn/GQA6FHWPJD/amazon-api-gateway-for-serverless-applications/JVRZ3PSW4H
- Amazon DynamoDB for Serverless Architecture — https://skillbuilder.aws/learn/SY1Y83VKTB/amazon-dynamodb-for-serverless-architectures/K9NM3PHH3S

**Module 4: Move to Managed Databases:**
- AWS Modernization Pathways: Move to Managed Databases — https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC/aws-modernization-pathways-move-to-managed-databases-includes-labs/2S2QZKG9DV
- Introduction to Building with AWS Databases — https://skillbuilder.aws/learn/HYKKWEN9ZS/introduction-to-building-with-aws-databases/V7RVH2KY91
  - Relevant for understanding DynamoDB best practices and adding vector database capabilities
- AWS PartnerCast: Vector Databases for Generative AI Applications — https://skillbuilder.aws/learn/UQ74USQJHU/aws-partnercast--vector-databases-for-generative-ai-applications--technical/7DKMBAPCST
  - Directly applicable: understanding vector databases for the agent's RAG knowledge base

**Module 6: Move to Modern DevOps:**
- AWS Modernization Pathways: Move to Modern DevOps — https://skillbuilder.aws/learning-plan/1FGEQKGPQD/aws-modernization-pathways-move-to-modern-devops-includes-labs/MNQZ2KPVCK
- Getting Started with DevOps on AWS — https://skillbuilder.aws/learn/R4B13K95YQ/getting-started-with-devops-on-aws/38NHHYRV1R
  - Critical: establishing CI/CD pipeline is a Phase 1 priority
- AWS CloudFormation Getting Started — https://skillbuilder.aws/learn/RH22P2RXU4/aws-cloudformation-getting-started/KEK5BT6HSE
  - Relevant for understanding CDK-synthesized CloudFormation templates
- Advanced Testing Practices Using AWS DevOps Tools — https://skillbuilder.aws/learn/1YC7UXUWBR/advanced-testing-practices-using-aws-devops-tools/A32U6G7NEQ
  - Addresses the complete lack of testing (OPS-Q10)
- AWS Developer: CI/CD Automation — https://skillbuilder.aws/learn/C1KF8ZJ1D8/aws-developer--cicd-automation/KY1E1JS9FA
  - Directly applicable: automating the currently manual `cdk deploy` process

**Module 7: Move to AI:**
- AWS Modernization Pathways: Move to AI — https://skillbuilder.aws/learning-plan/VDFEE4ACCV/aws-modernization-pathways-move-to-ai-pathways-includes-labs/P3DAWPTN63
- Introduction to Generative AI: Art of the Possible — https://skillbuilder.aws/learn/ZEVZZ1D4AS/introduction-to-generative-ai--art-of-the-possible/Y7MTGJCW1U
- Planning a Generative AI Project — https://skillbuilder.aws/learn/HU1FQRGDDZ/planning-a-generative-ai-project/SYR3SCPSHC
  - Relevant for planning the customer support agent project
- Amazon Bedrock Getting Started — https://skillbuilder.aws/learn/63KTRM86DQ/amazon-bedrock-getting-started/SC2Y3HMAUE
  - Essential: Bedrock is the recommended foundation for the agent
- Essentials for Prompt Engineering — https://skillbuilder.aws/learn/XBNAVKA88J/essentials-of-prompt-engineering/9T9Q45EDTV
  - Critical for designing effective customer support agent prompts
- Build and Evaluate Retrieval Augmented Generation (RAG) Applications using Knowledge Bases for Amazon Bedrock (Lab) — https://skillbuilder.aws/learn/JRGWCFYT67/lab--build-and-evaluate-retrieval-augmented-generation-rag-applications-using-knowledge-bases-for-amazon-bedrock/A4MN58JB7A
  - Directly applicable: building the RAG pipeline for product/policy knowledge
- Introduction to Agentic AI on AWS — https://skillbuilder.aws/learn/DNBD5MT8ZD/introduction-to-agentic-ai-on-aws/WAKAFK6UFY
  - Core learning material for the agentic-ai-enablement goal
- Creating an AWS DevOps AI Agent with the Strands Agents SDK (Lab) — https://skillbuilder.aws/learn/AH1GD8AJY3/lab--creating-an-aws-devops-ai-agent-with-the-strands-agents-sdk/A9SKJNMPJ2
  - Hands-on lab for building agents with Strands SDK — directly relevant
- AWS PartnerCast: Deep Dive: Building Observable AI Agents with Strands, Amazon Bedrock Agent Core & SageMaker MLflow — https://skillbuilder.aws/learn/1EN76TZBB6/aws-partnercast--deep-dive-building-observable-ai-agents-with-strands-amazon-bedrock-agent-core--sagemaker-mlflow--technical/CX2K6XAT84
  - Addresses agent observability — critical for production agent deployment
- DevOps and AI on AWS: CloudWatch Anomaly Detection (Lab) — https://skillbuilder.aws/learn/RWYVJ73MXP/lab--devops-and-ai-on-aws-cloudwatch-anomaly-detection/BRPDNZUGU7
  - Addresses the complete lack of anomaly detection (OPS-Q8)

---

## Appendix: Evidence Index

| # | File | Role | Key Findings |
|---|------|------|-------------|
| 1 | `lib/aws-microservices-stack.ts` | CDK Main Stack | Orchestrates all constructs: Database → Microservices → API Gateway → Queue → EventBus |
| 2 | `lib/database.ts` | DynamoDB IaC | 3 tables (product, basket, order) with PAY_PER_REQUEST, DESTROY removal policy, schema comments |
| 3 | `lib/microservice.ts` | Lambda IaC | 3 NodejsFunction Lambdas, NODEJS_14_X (EOL), grantReadWriteData, environment variables |
| 4 | `lib/apigateway.ts` | API Gateway IaC | 3 separate LambdaRestApi instances, explicit routes (not proxy), NO auth/throttle/validation |
| 5 | `lib/eventbus.ts` | EventBridge IaC | SwnEventBus with CheckoutBasketRule → SQS target, grantPutEventsTo for basket Lambda |
| 6 | `lib/queue.ts` | SQS IaC | OrderQueue with 30s visibility timeout, SqsEventSource with batchSize 1, NO DLQ |
| 7 | `src/product/index.js` | Product Lambda | CRUD handler with GET/POST/PUT/DELETE, DynamoDB Scan/Get/Put/Update/Delete, JSON responses |
| 8 | `src/basket/index.js` | Basket Lambda | CRUD + checkout handler, EventBridge PutEventsCommand, hardcoded checkout sequence |
| 9 | `src/ordering/index.js` | Ordering Lambda | SQS consumer + API handler, createOrder from event.detail, GET order queries |
| 10 | `src/product/ddbClient.js` | DynamoDB Client | Shared DynamoDB client module (duplicated across services) |
| 11 | `src/basket/eventBridgeClient.js` | EventBridge Client | EventBridgeClient instance for checkout event publishing |
| 12 | `src/product/package.json` | Product Dependencies | @aws-sdk/client-dynamodb ^3.55.0, @aws-sdk/util-dynamodb ^3.55.0 |
| 13 | `src/basket/package.json` | Basket Dependencies | DynamoDB SDK + @aws-sdk/client-eventbridge ^3.58.0 |
| 14 | `src/ordering/package.json` | Ordering Dependencies | @aws-sdk/client-dynamodb ^3.58.0, @aws-sdk/util-dynamodb ^3.58.0 |
| 15 | `package.json` | CDK Project Config | aws-cdk-lib 2.17.0 (outdated), TypeScript ~3.9.7, Jest ^26.4.2 |
| 16 | `cdk.json` | CDK Configuration | Feature flags, app entrypoint, watch config |
| 17 | `tsconfig.json` | TypeScript Config | ES2018 target, strict mode, commonjs modules |
| 18 | `test/aws-microservices.test.ts` | Test File | All test code commented out — single empty test case |
| 19 | `src/basket/checkoutbasketevents.json` | Event Sample | Sample EventBridge CheckoutBasket events with source and detail structure |
| 20 | `README.md` | Documentation | Architecture description, API URLs, deployment instructions, prerequisites |
