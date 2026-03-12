# Agentic Readiness Assessment Report
**Target**: ./services/aws-microservices
**Date**: 2026-03-12
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

This serverless e-commerce application has a strong architectural foundation for agentic AI enablement — its event-driven microservices pattern with clear service boundaries (Product, Basket, Ordering), fully managed DynamoDB databases, and EventBridge/SQS async messaging align well with agent tool design patterns. However, the application is critically unprepared for agent integration: there are no API specifications for agent tool discovery, no AI/agent frameworks, no vector database or RAG pipeline for knowledge retrieval, and the entire Operations & Observability layer is absent. Security is the second weakest category with no authentication, no identity propagation, and no human approval workflows — all essential guardrails before deploying customer-facing AI agents for support and order management. The path forward leverages the existing microservices architecture as the agent tool surface while building the missing AI, DevOps, and security foundations.

### Overall Score: 1.7 / 4.0

| Category | Score | Status |
|----------|-------|--------|
| Infrastructure & Platform | 2.4 / 4.0 | 🟡 |
| Application Architecture | 1.9 / 4.0 | 🟠 |
| Data Foundations | 2.0 / 4.0 | 🟠 |
| Identity, Security & Governance | 1.4 / 4.0 | ❌ |
| Operations & Observability | 1.0 / 4.0 | ❌ |

---

## Top Priorities (Critical Gaps)

1. **APP-Q2 — API Documentation (Score: 1/4)**: No OpenAPI/Swagger specifications exist for any of the three API Gateway services (Product, Basket, Order). Without machine-readable API specs, agents cannot discover available endpoints, understand request/response schemas, or invoke tools autonomously. This is the single biggest blocker for building a customer support agent — the agent literally cannot know what actions it can perform. **First step**: Generate OpenAPI 3.0 specs from the existing `lib/apigateway.ts` route definitions and deploy them alongside each API Gateway stage.

2. **APP-Q13 — AI/Agent Frameworks (Score: 1/4)**: No AI or agent framework (Bedrock SDK, LangChain, Strands Agents, MCP SDK) is present in any of the three Lambda functions or the CDK stack. There is zero agent integration infrastructure. **First step**: Add `@aws-sdk/client-bedrock-runtime` to the dependency manifests and create a proof-of-concept agent Lambda that can invoke the existing Product and Order APIs as tools.

3. **DATA-Q1 — Vector Database (Score: 1/4)**: No vector database (OpenSearch with k-NN, Aurora pgvector, Pinecone, Bedrock Knowledge Bases) exists. A customer support agent needs semantic search over product catalogs, order history, and support documentation to answer questions. **First step**: Provision an Amazon Bedrock Knowledge Base backed by OpenSearch Serverless and index product data from the DynamoDB `product` table.

4. **DATA-Q3 — RAG Implementation (Score: 1/4)**: No document chunking, embedding generation, or semantic search pipeline exists. Without RAG, the customer support agent cannot retrieve relevant product information, order details, or support articles to ground its responses. **First step**: Implement a RAG pipeline using Bedrock Knowledge Bases with Titan embeddings, starting with product catalog data as the first knowledge source.

5. **OPS-Q3 — Automated Evals (Score: 1/4)**: No agent evaluation framework, golden datasets, or scoring pipelines exist. Without automated evals, there is no way to measure whether the customer support agent is providing accurate order information or correct product recommendations before deploying to customers. **First step**: Create a golden dataset of 50+ customer support Q&A pairs covering product queries, order status lookups, and checkout scenarios, then build an eval pipeline using RAGAS or LLM-as-judge scoring.

---

## Detailed Findings

### Infrastructure & Platform

#### INF-Q1: Compute
- **Score**: 3/4 🟡
- **Finding**: All three microservices (Product, Basket, Ordering) are deployed as AWS Lambda functions using `NodejsFunction` with `Runtime.NODEJS_14_X`, as defined in `lib/microservice.ts`. This is 100% serverless compute — no EC2 instances. However, Node.js 14.x reached end-of-life in April 2023, presenting a runtime upgrade risk.
- **Gap**: Lambda runtime `NODEJS_14_X` is past EOL. No explicit Lambda concurrency limits or provisioned concurrency configured.
- **Recommendation**: Upgrade all three Lambda functions to `Runtime.NODEJS_20_X` or later in `lib/microservice.ts`. Consider adding `reservedConcurrentExecutions` to protect downstream DynamoDB tables from burst traffic when agents scale invocations.

#### INF-Q2: Databases
- **Score**: 4/4 ✅
- **Finding**: All three databases (product, basket, order) are Amazon DynamoDB tables with `BillingMode.PAY_PER_REQUEST`, defined in `lib/database.ts`. DynamoDB is fully managed with automatic failover, backups, and scaling. No self-managed database software detected anywhere.
- **Gap**: None — all databases are fully managed.
- **Recommendation**: Enable DynamoDB Point-in-Time Recovery (PITR) for the order table to support agent conversation state recovery.

#### INF-Q3: Workflow Orchestration
- **Score**: 1/4 ❌
- **Finding**: No dedicated workflow orchestration service (Step Functions, Temporal, Camunda) found. The checkout flow is implemented as a direct sequence in `src/basket/index.js` (checkoutBasket → prepareOrderPayload → publishCheckoutBasketEvent → deleteBasket) with event routing via EventBridge. While event-driven, this is not a managed workflow.
- **Gap**: No Step Functions or equivalent orchestration service. The checkout flow has no built-in compensation, retry, or rollback logic. Agent workflows will require multi-step orchestration (e.g., check inventory → place order → confirm payment → send notification).
- **Recommendation**: Implement AWS Step Functions for the checkout workflow and future agent orchestration. Step Functions provides built-in retry, error handling, and human approval integration — all critical for agent workflows that manage customer orders.

#### INF-Q4: Async Messaging
- **Score**: 4/4 ✅
- **Finding**: Amazon EventBridge (`SwnEventBus`) and Amazon SQS (`OrderQueue`) are configured in `lib/eventbus.ts` and `lib/queue.ts`. The checkout flow publishes events from the Basket service via EventBridge (source: `com.swn.basket.checkoutbasket`, detailType: `CheckoutBasket`), which routes to SQS, consumed by the Ordering Lambda with `batchSize: 1`.
- **Gap**: None — fully managed async messaging in place.
- **Recommendation**: Add a Dead Letter Queue (DLQ) to `OrderQueue` for failed message handling. This becomes critical when agents trigger checkout flows — failed orders need to be captured and retried.

#### INF-Q5: Infrastructure as Code
- **Score**: 4/4 ✅
- **Finding**: All infrastructure is defined in AWS CDK (TypeScript) across 6 construct files: `lib/aws-microservices-stack.ts` (orchestrator), `lib/database.ts` (DynamoDB), `lib/microservice.ts` (Lambda), `lib/apigateway.ts` (API Gateway), `lib/eventbus.ts` (EventBridge), `lib/queue.ts` (SQS). Coverage includes compute, databases, API gateway, event bus, and message queue.
- **Gap**: None — comprehensive IaC coverage via CDK.
- **Recommendation**: Add CDK stack tags for cost allocation and environment identification. Add CDK Nag for security/compliance validation.

#### INF-Q6: CI/CD
- **Score**: 1/4 ❌
- **Finding**: No CI/CD pipeline definitions found. No `.github/workflows/`, `buildspec.yml`, `Jenkinsfile`, `.gitlab-ci.yml`, or CodePipeline resources in CDK. The README instructs manual `cdk deploy`. The `package.json` has `build`, `watch`, and `test` scripts but no deployment automation.
- **Gap**: Deployments are entirely manual. No automated testing, building, or deployment. This is a critical blocker for agent deployments — prompt changes, model updates, and agent configuration changes need automated, safe deployment pipelines with rollback.
- **Recommendation**: Create a GitHub Actions workflow with CDK diff, CDK deploy, and integration test stages. Use OIDC for AWS authentication. Implement separate dev/staging/prod stages.

#### INF-Q7: API Entry Point
- **Score**: 2/4 🟠
- **Finding**: Three separate `LambdaRestApi` instances are created in `lib/apigateway.ts` (Product Service, Basket Service, Order Service) with explicit resource and method definitions. However, no throttling configuration, no API key requirements, no request validation models, and no authorization are configured on any API Gateway.
- **Gap**: APIs lack throttling, authentication, request validation, and usage plans. When agents invoke these APIs at machine speed, there are no safeguards against excessive calls.
- **Recommendation**: Add API Gateway usage plans with throttle settings (burst/rate limits) and request validators in `lib/apigateway.ts`. Add a Cognito or Lambda authorizer for agent-to-API authentication.

#### INF-Q8: Real-time Streaming
- **Score**: 1/4 ❌
- **Finding**: No Kinesis Data Streams, MSK, or streaming services found. EventBridge provides event routing (not streaming). No real-time data streaming for analytics or agent context.
- **Gap**: No real-time streaming infrastructure. For a customer support agent, real-time order status updates and inventory changes would improve response accuracy.
- **Recommendation**: Evaluate whether DynamoDB Streams (which can be enabled on existing tables) would serve agent context needs — e.g., streaming order status changes to update agent knowledge in real-time. This aligns with the preferred event-driven architecture.

#### INF-Q9: Network Security
- **Score**: 1/4 ❌
- **Finding**: No VPC, subnets, security groups, or network configuration found in the CDK stack. Lambda functions run in the default AWS-managed network. No `aws_vpc`, `aws_subnet`, or `aws_security_group` resources.
- **Gap**: No network segmentation. Lambda functions access DynamoDB and EventBridge over public endpoints. While Lambda's default networking is acceptable for public API workloads, agent-integrated services handling customer PII (order data includes firstName, lastName, email, address, cardInfo per `lib/database.ts` comments) should have network-level controls.
- **Recommendation**: Deploy Lambda functions in a VPC with private subnets and VPC endpoints for DynamoDB and EventBridge. This provides network-level isolation for PII-handling services.

#### INF-Q10: Auto-scaling
- **Score**: 3/4 🟡
- **Finding**: All compute is Lambda (inherently auto-scaling) and all databases are DynamoDB with `PAY_PER_REQUEST` (inherently auto-scaling), as defined in `lib/microservice.ts` and `lib/database.ts`. SQS also scales automatically.
- **Gap**: No explicit Lambda concurrency limits (`reservedConcurrentExecutions`) configured. No provisioned concurrency for latency-sensitive agent interactions. SQS `batchSize: 1` in `lib/queue.ts` may not be optimal for high-throughput agent workflows.
- **Recommendation**: Set `reservedConcurrentExecutions` on each Lambda to prevent runaway agent invocations from consuming account-wide concurrency. Add provisioned concurrency for the agent-facing Lambda functions to reduce cold start latency.

### Application Architecture

#### APP-Q1: Programming Languages
- **Score**: 3/4 🟡
- **Finding**: Lambda microservices are written in JavaScript (ES6 modules) in `src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js`. CDK infrastructure is TypeScript. Dependencies use `@aws-sdk/client-dynamodb` (v3.55+) and `@aws-sdk/client-eventbridge` (v3.58+) per service-level `package.json` files. The JS/TS ecosystem has strong agent framework support (LangChain.js, OpenAI SDK, Strands Agents).
- **Gap**: JavaScript (not TypeScript) used for Lambda source code — lacks type safety for complex agent tool definitions. Python ecosystem is richer for AI/ML libraries.
- **Recommendation**: Consider migrating Lambda source from JavaScript to TypeScript for type safety in agent tool interfaces. The CDK is already TypeScript, so the tooling is in place. Alternatively, new agent-specific Lambda functions can be written in Python if the team prefers the richer AI ecosystem.

#### APP-Q2: API Documentation
- **Score**: 1/4 ❌
- **Finding**: No OpenAPI/Swagger specifications found anywhere in the repository. No `openapi.yaml`, `swagger.json`, or API documentation annotations. API routes are defined programmatically in `lib/apigateway.ts` (e.g., `product.addMethod('GET')`, `basketCheckout.addMethod('POST')`) but not documented in a machine-readable format.
- **Gap**: Agents cannot discover or invoke APIs without machine-readable API specs. This is the #1 blocker for agentic AI enablement — a customer support agent needs to know available operations (list products, get basket, place order), their parameters, and response schemas.
- **Recommendation**: Generate OpenAPI 3.0 specifications for each API Gateway service. CDK can export these via `api.deploymentStage.urlForPath()`. Define request/response models with JSON Schema for each endpoint. Deploy specs as API Gateway documentation parts.

#### APP-Q3: Async vs Sync Communication
- **Score**: 2/4 🟠
- **Finding**: The checkout flow is async: `src/basket/index.js` publishes to EventBridge (`publishCheckoutBasketEvent`), routed via `lib/eventbus.ts` (CheckoutBasketRule) to SQS (`OrderQueue` in `lib/queue.ts`), consumed by Ordering Lambda. All CRUD operations (Product GET/POST/PUT/DELETE, Basket GET/POST/DELETE, Order GET) are synchronous API Gateway → Lambda → DynamoDB.
- **Gap**: Only 1 out of ~12 API operations is async (checkout). Long-running agent operations (bulk order queries, product search across categories) would benefit from async patterns.
- **Recommendation**: Implement async patterns for operations that agents may need to chain or that could exceed Lambda timeout (product catalog refresh, bulk order history retrieval). Use the existing EventBridge/SQS infrastructure to add async variants of heavy operations.

#### APP-Q4: Monolith vs Microservices
- **Score**: 4/4 ✅
- **Finding**: Three separate Lambda functions with clear domain boundaries: Product (CRUD on product table), Basket (CRUD + checkout on basket table), Ordering (order creation from events + order queries on order table). Each service has its own DynamoDB table, source code directory (`src/product/`, `src/basket/`, `src/ordering/`), and dependency manifest. Inter-service communication is event-driven via EventBridge/SQS — no direct service-to-service HTTP calls.
- **Gap**: None — clean microservices architecture with proper domain separation.
- **Recommendation**: These well-defined service boundaries map directly to agent tools: a "Product Tool" (search/get products), a "Basket Tool" (manage cart), and an "Order Tool" (place/query orders). Define MCP-compatible tool interfaces on each service boundary.

#### APP-Q5: API Response Format
- **Score**: 4/4 ✅
- **Finding**: All Lambda functions return structured JSON responses with consistent format: `{ statusCode: 200, body: JSON.stringify({ message: "...", body: ... }) }`. Error responses also return structured JSON: `{ statusCode: 500, body: JSON.stringify({ message: "...", errorMsg: "...", errorStack: "..." }) }`. Observed in `src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js`.
- **Gap**: None — all APIs return structured JSON.
- **Recommendation**: Standardize the response envelope schema and document it in the OpenAPI specs. Remove `errorStack` from production responses (security concern — see SEC-Q6).

#### APP-Q6: Workflow Logic
- **Score**: 1/4 ❌
- **Finding**: The checkout workflow is hardcoded in `src/basket/index.js` (`checkoutBasket` function): (1) get basket → (2) `prepareOrderPayload` (calculate total, merge data) → (3) `publishCheckoutBasketEvent` → (4) `deleteBasket`. No dedicated orchestration service. The ordering Lambda in `src/ordering/index.js` simply creates an order record via `createOrder` with a `PutItemCommand`.
- **Gap**: No workflow orchestration for multi-step operations. A customer support agent handling order management needs orchestrated workflows: verify inventory → validate payment → create order → send confirmation → update status. The current hardcoded sequence has no compensation logic if step 3 succeeds but step 4 fails.
- **Recommendation**: Implement AWS Step Functions for the checkout workflow. Design agent orchestration as Step Functions state machines with built-in retry, error handling, and human approval tasks (SEC-Q7).

#### APP-Q7: Idempotency
- **Score**: 1/4 ❌
- **Finding**: No idempotency keys or deduplication mechanisms found. Product creation in `src/product/index.js` generates a `uuidv4()` ID but uses `PutItemCommand` which will silently overwrite on retry. Basket checkout in `src/basket/index.js` has no idempotency protection — a retry could publish duplicate EventBridge events and delete the basket twice. SQS `OrderQueue` in `lib/queue.ts` is a standard queue (not FIFO) with no deduplication.
- **Gap**: Agent retries can cause duplicate orders, duplicate event publications, and data corruption. Agents inherently retry on transient failures — without idempotency, every retry is a potential duplicate operation on a customer's order.
- **Recommendation**: Add idempotency keys to all write operations. Use `@aws-lambda-powertools/idempotency` with DynamoDB as the persistence layer. Convert `OrderQueue` to FIFO with content-based deduplication. Add `Idempotency-Key` header support to POST endpoints.

#### APP-Q8: Rate Limiting & Throttling
- **Score**: 1/4 ❌
- **Finding**: No rate limiting at any layer. API Gateway in `lib/apigateway.ts` has no usage plans, no throttle settings, no API keys. No application-level rate limiting middleware in Lambda functions. No WAF rules.
- **Gap**: APIs are completely unprotected against traffic spikes. Agents can invoke APIs at machine speed — without rate limits, a misconfigured agent could overwhelm the service or generate excessive DynamoDB costs.
- **Recommendation**: Add API Gateway usage plans with per-client throttle limits in `lib/apigateway.ts`. Set default method throttling (e.g., 100 requests/second burst, 50 sustained). Add per-agent API keys for attribution and quota management.

#### APP-Q9: Resilience Patterns
- **Score**: 1/4 ❌
- **Finding**: No circuit breakers, retry logic with backoff, or timeout configurations in any Lambda function. AWS SDK has default retry behavior but no custom configuration. No dead letter queues on Lambda functions or SQS. The `OrderQueue` in `lib/queue.ts` has `visibilityTimeout: Duration.seconds(30)` but no DLQ. Error handling is basic try/catch with console.error.
- **Gap**: No resilience patterns for external dependency calls. Agent workflows spanning multiple services will fail cascading without circuit breakers. Failed SQS messages are retried indefinitely without a DLQ.
- **Recommendation**: Add `@aws-lambda-powertools` for structured error handling. Configure DLQs on all SQS queues and Lambda functions. Implement retry with exponential backoff for DynamoDB calls. Add Lambda function timeouts appropriate for each operation.

#### APP-Q10: Long-running Processes
- **Score**: 2/4 🟠
- **Finding**: The checkout flow is asynchronous: basket service publishes to EventBridge, consumed asynchronously by ordering service via SQS (defined in `lib/eventbus.ts` and `lib/queue.ts`). However, there is no status polling endpoint or callback mechanism. The `POST /basket/checkout` in `src/basket/index.js` returns void after publishing the event — the caller has no way to know if the order was successfully created.
- **Gap**: No job status API or callback pattern for async operations. A customer support agent that initiates checkout on behalf of a customer cannot confirm order completion or report failures.
- **Recommendation**: Add an order status endpoint (e.g., `GET /order/{userName}/status/{orderId}`) and implement a callback or polling pattern. Consider using Step Functions with a `waitForTaskToken` pattern for agent-initiated checkout flows.

#### APP-Q11: API Versioning
- **Score**: 1/4 ❌
- **Finding**: No API versioning strategy found. API Gateway resources in `lib/apigateway.ts` define root paths as `/product`, `/basket`, `/order` without version prefixes. No `Accept-Version` headers, no `/v1/` path segments, no versioning annotations or changelog.
- **Gap**: No backward compatibility guarantees. When agent tool definitions reference specific API contracts, breaking changes will silently break agent functionality. Agents that were trained or configured against a specific API version will fail if the API changes.
- **Recommendation**: Implement URL path versioning (e.g., `/v1/product`, `/v1/basket`, `/v1/order`) in `lib/apigateway.ts`. Establish a versioning policy that maintains backward compatibility for at least one prior version.

#### APP-Q12: Service Discovery & Mesh
- **Score**: 3/4 🟡
- **Finding**: Services communicate via EventBridge event bus name (`EVENT_BUSNAME: "SwnEventBus"` environment variable in `lib/microservice.ts`). No hard-coded service endpoints — services are decoupled through event-driven patterns. The basket service publishes events; the ordering service consumes them via SQS. No direct HTTP calls between services.
- **Gap**: No formal service registry or API catalog. Agents need to discover available services and their capabilities programmatically.
- **Recommendation**: Create an API catalog (e.g., using API Gateway's built-in documentation features or a service registry) that agents can query to discover available tools. The existing event-driven decoupling is excellent — extend it with a service manifest.

#### APP-Q13: AI/Agent Frameworks
- **Score**: 1/4 ❌
- **Finding**: No AI or agent framework imports found in any source file. No `@aws-sdk/client-bedrock-runtime`, `langchain`, `openai`, `strands-agents`, `anthropic`, or MCP SDK references in any `package.json` (`src/product/package.json`, `src/basket/package.json`, `src/ordering/package.json`, root `package.json`). No Bedrock, SageMaker, or AI service configurations in CDK.
- **Gap**: Zero AI/agent infrastructure. Building a customer support agent for order and inventory data requires agent frameworks, LLM integration, and tool-use patterns — none of which exist.
- **Recommendation**: Start with Amazon Bedrock and the Strands Agents SDK. Create a new agent Lambda function that uses the existing Product, Basket, and Order APIs as tools. Define tool schemas based on the API endpoints and deploy via CDK.

### Data Foundations

#### DATA-Q1: Vector Database Presence
- **Score**: 1/4 ❌
- **Finding**: No vector database found in the repository. No OpenSearch with k-NN, Aurora pgvector, Pinecone, Weaviate, Chroma, or Bedrock Knowledge Base configurations in CDK (`lib/`) or source code (`src/`). Only DynamoDB tables are present.
- **Gap**: No vector store for semantic search. A customer support agent needs to perform semantic search over product catalogs ("find me a phone under $500"), order history ("show my recent orders"), and support documentation to provide relevant, grounded responses.
- **Recommendation**: Provision an Amazon Bedrock Knowledge Base with OpenSearch Serverless as the vector store. Index product catalog data from the DynamoDB `product` table (name, description, category, price) as the first knowledge source for the customer support agent.

#### DATA-Q2: Vector DB Management
- **Score**: 1/4 ❌
- **Finding**: No vector database exists (see DATA-Q1), so no management infrastructure is present. No managed or self-hosted vector database configurations found.
- **Gap**: No vector database to manage. When implementing vector search for agent knowledge, the management approach needs to be fully managed from the start.
- **Recommendation**: Use Amazon Bedrock Knowledge Bases (fully managed) rather than self-hosting OpenSearch or Chroma. This aligns with the serverless architecture pattern and eliminates operational overhead.

#### DATA-Q3: RAG Implementation
- **Score**: 1/4 ❌
- **Finding**: No document chunking, embedding model calls, similarity search, or semantic search patterns found in any source file. No Bedrock Titan, OpenAI ada, or any embedding model references. No `knn_search` or `similarity_search` patterns.
- **Gap**: No RAG pipeline. The customer support agent cannot retrieve relevant context from product catalogs or order data to ground its responses. Without RAG, the agent would rely solely on its training data, which won't include your specific product inventory or customer order information.
- **Recommendation**: Build a RAG pipeline: (1) Export product data from DynamoDB to S3, (2) Configure Bedrock Knowledge Base with Titan Embeddings, (3) Implement retrieval-augmented generation in the agent Lambda. Start with product catalog RAG, then extend to order history and support FAQs.

#### DATA-Q4: Data Source Sprawl
- **Score**: 3/4 🟡
- **Finding**: Three DynamoDB tables (product, basket, order) defined in `lib/database.ts`, each accessed exclusively by its own Lambda function. Product Lambda reads/writes only the product table. Basket Lambda reads/writes only the basket table. Ordering Lambda reads/writes only the order table. Clean data ownership boundaries.
- **Gap**: Three data sources is at the threshold. An agent querying across product and order data needs a unified view, but each service only sees its own table.
- **Recommendation**: The clean service boundaries are ideal for agent tool design — each service becomes a dedicated tool. For cross-service agent queries (e.g., "what's the status of my order for that blue phone?"), implement a thin API aggregation layer or let the agent chain tool calls (Product search → Order lookup).

#### DATA-Q5: Data Access Pattern
- **Score**: 2/4 🟠
- **Finding**: Each Lambda directly imports `DynamoDBClient` via service-specific `ddbClient.js` files (`src/product/ddbClient.js`, `src/basket/ddbClient.js`, `src/ordering/ddbClient.js`) and executes raw DynamoDB commands inline in `index.js` files. No repository pattern, no data access layer abstraction. Operations are directly embedded: `GetItemCommand`, `PutItemCommand`, `ScanCommand`, `QueryCommand`, `DeleteItemCommand`, `UpdateItemCommand`.
- **Gap**: No abstracted data access layer. Direct DynamoDB commands in business logic make it harder to add caching, logging, or agent-specific data access patterns (e.g., natural language to DynamoDB queries).
- **Recommendation**: Refactor data access into a repository/DAO pattern within each service. This creates a clean interface for agent tools to invoke — the agent calls the API, the API calls the repository, the repository talks to DynamoDB. This layering simplifies future data source migrations and enables caching.

#### DATA-Q6: Unstructured Data
- **Score**: 1/4 ❌
- **Finding**: No S3 storage, no document parsing (Textract, Tika, PDF processing). Only structured DynamoDB data is present. The product table includes an `imageFile` field (per `lib/database.ts` comments) but no S3 bucket for storing product images or documents.
- **Gap**: No unstructured data handling. Customer support agents often need to process and understand unstructured content: product manuals, warranty documents, return policies, customer-uploaded images of damaged products.
- **Recommendation**: Add an S3 bucket for product images and support documents. Implement a document processing pipeline using Textract for text extraction, feeding into the RAG knowledge base for the customer support agent.

#### DATA-Q7: Schema Documentation
- **Score**: 2/4 🟠
- **Finding**: DynamoDB table schemas are partially documented in CDK comments in `lib/database.ts`: product (PK: id — name, description, imageFile, price, category), basket (PK: userName — items SET-MAP with quantity, color, price, productId, productName), order (PK: userName, SK: orderDate — totalPrice, firstName, lastName, email, address, paymentMethod, cardInfo). Partition/sort keys are defined in CDK Table constructs. No formal JSON Schema, no schema registry, no versioned migration files.
- **Gap**: Schemas exist only as code comments and CDK attribute definitions. No formal schema documentation that agents can reference to understand data structures. The `checkoutbasketevents.json` sample in `src/basket/` provides a partial event schema but is not comprehensive.
- **Recommendation**: Create JSON Schema definitions for each DynamoDB table's item structure. Document the EventBridge event schema (`com.swn.basket.checkoutbasket` / `CheckoutBasket`). Use EventBridge Schema Registry to auto-discover and document event schemas.

#### DATA-Q8: Data Access Layer
- **Score**: 2/4 🟠
- **Finding**: Each microservice has its own `ddbClient.js` file, but this is only a DynamoDB client instantiation (5 lines of code). Actual data access logic (queries, puts, deletes, updates) is inline in each `index.js`. No repository/DAO pattern, no query abstraction, no centralized data contract.
- **Gap**: Data access logic is scattered across handler functions. No single point of data contract definition. Agent tools need clean, well-documented data operations — the current inline approach makes it difficult to expose consistent tool interfaces.
- **Recommendation**: Extract data operations into repository modules (e.g., `productRepository.js`, `basketRepository.js`, `orderRepository.js`) with clear method signatures. These become the natural tool function definitions for the agent.

#### DATA-Q9: Embedding Freshness
- **Score**: 1/4 ❌
- **Finding**: No embeddings exist (see DATA-Q1/Q3), so no freshness mechanism is present. No event-driven embedding refresh triggers, no scheduled re-indexing, no CDC patterns for DynamoDB-to-vector-store synchronization.
- **Gap**: When vector search is implemented, product catalog changes (new products, price updates, discontinued items) need to be reflected in the vector store in near-real-time for the agent to provide accurate information.
- **Recommendation**: Implement DynamoDB Streams on the product table to trigger embedding updates when products are added/modified/deleted. Use a Lambda function to process stream events and update the Bedrock Knowledge Base. This leverages the existing event-driven architecture pattern.

#### DATA-Q10: Database Engine Version & EOL
- **Score**: 4/4 ✅
- **Finding**: All databases are Amazon DynamoDB (defined in `lib/database.ts`), a fully managed serverless service. DynamoDB has no engine version to pin — AWS manages all underlying engine upgrades transparently. No RDS, DocumentDB, ElastiCache, or other versioned database engines are present.
- **Gap**: None — DynamoDB is evergreen with no EOL concerns.
- **Recommendation**: No action needed for database engine versions. Note: the Lambda runtime `NODEJS_14_X` is past EOL (addressed in INF-Q1).

#### DATA-Q11: Stored Procedures & Schema Complexity
- **Score**: 4/4 ✅
- **Finding**: DynamoDB does not support stored procedures, triggers, or proprietary SQL constructs. All business logic resides in application code: product CRUD in `src/product/index.js`, basket operations and checkout in `src/basket/index.js`, order creation and queries in `src/ordering/index.js`. No `.sql` files found. No ORM bypass patterns.
- **Gap**: None — all business logic is in the application layer, making it fully portable and agent-accessible.
- **Recommendation**: No action needed. This clean separation is ideal for agentic AI — agents interact with business logic through APIs, not through database-level procedures.

### Identity, Security & Governance

#### SEC-Q1: Secret Management
- **Score**: 2/4 🟠
- **Finding**: No hardcoded secrets (passwords, API keys, tokens) found in any source file. Environment variables in `lib/microservice.ts` pass non-sensitive configuration only: `DYNAMODB_TABLE_NAME`, `PRIMARY_KEY`, `SORT_KEY`, `EVENT_SOURCE`, `EVENT_DETAILTYPE`, `EVENT_BUSNAME`. No `.env` files committed. No Secrets Manager or SSM Parameter Store usage in CDK.
- **Gap**: No secrets management infrastructure established. When agent integrations are added (Bedrock API keys, external service credentials, agent-specific tokens), there is no pattern for secure secret storage and rotation.
- **Recommendation**: Add AWS Secrets Manager integration in CDK for future credentials (Bedrock API keys, third-party service tokens). Establish the pattern now before agent integrations introduce secrets.

#### SEC-Q2: IAM Least Privilege
- **Score**: 3/4 🟡
- **Finding**: CDK uses scoped grant methods: `productTable.grantReadWriteData(productFunction)`, `basketTable.grantReadWriteData(basketFunction)`, `orderTable.grantReadWriteData(orderFunction)` in `lib/microservice.ts`, and `bus.grantPutEventsTo(props.publisherFuntion)` in `lib/eventbus.ts`. Each service role is scoped to its own table. No wildcard `Action: "*"` or `Resource: "*"` policies.
- **Gap**: `grantReadWriteData` is broader than necessary — the Product GET endpoint only needs read access, not write. The ordering service only needs `PutItem`, not full read-write. Per-operation IAM scoping is not implemented.
- **Recommendation**: Refine IAM grants: use `grantReadData` for read-only operations and `grantWriteData` for write operations where possible. For the agent Lambda (when created), define the narrowest possible IAM role — agents should only invoke specific API Gateway endpoints, not directly access DynamoDB.

#### SEC-Q3: Identity Propagation
- **Score**: 1/4 ❌
- **Finding**: No JWT/OAuth token exchange, no Cognito integration, no auth middleware in any Lambda function. User identity is passed as a URL path parameter (`{userName}` in basket and order APIs per `lib/apigateway.ts`) — anyone can access any user's basket or orders by knowing the username. No token validation, no user context propagation across service boundaries.
- **Gap**: No authenticated identity propagation. A customer support agent handling order management must authenticate as a specific customer or service account — the current path-parameter approach allows impersonation. This is a critical security gap for customer-facing agents.
- **Recommendation**: Implement Amazon Cognito with JWT tokens. Add a Cognito User Pool authorizer to all API Gateway endpoints in `lib/apigateway.ts`. Extract user identity from the JWT token in Lambda handlers instead of relying on the `{userName}` path parameter. Implement agent-specific service credentials with limited scope.

#### SEC-Q4: Audit Logging
- **Score**: 1/4 ❌
- **Finding**: No CloudTrail configuration in CDK. No audit logging infrastructure. Lambda functions use `console.log` for request logging (e.g., `console.log("request:", JSON.stringify(event, undefined, 2))` in all three index.js files) but this is debug logging, not audit logging. No structured audit trail for who did what and when.
- **Gap**: No audit trail for API operations. When agents perform actions on behalf of customers (modifying baskets, placing orders), every action must be auditable: which agent, which customer, what action, what outcome. Without audit logging, there is no accountability for agent actions.
- **Recommendation**: Enable CloudTrail for API Gateway and Lambda invocations. Implement structured audit logging in each Lambda with fields: userId, agentId, action, resource, outcome, timestamp. Store audit logs in CloudWatch Logs with immutable retention.

#### SEC-Q5: API Rate Limits
- **Score**: 1/4 ❌
- **Finding**: No rate limiting at the API Gateway layer. No usage plans, no throttle configurations, no WAF rules found in `lib/apigateway.ts`. No application-level rate limiting in Lambda functions.
- **Gap**: No protection against API abuse. Agent-initiated API calls at machine speed with no rate limits could cause denial of service, excessive costs, or data corruption (e.g., an agent in a retry loop creating hundreds of orders).
- **Recommendation**: Add API Gateway usage plans with per-API-key throttling. Create separate API keys for human users and agents with different rate limits. Add WAF with rate-based rules for DDoS protection.

#### SEC-Q6: PII Redaction
- **Score**: 1/4 ❌
- **Finding**: Error responses in all three Lambda functions include full stack traces: `errorStack: e.stack` (visible in `src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js`). `console.log` statements output entire request payloads which include customer PII: userName, firstName, lastName, email, address, paymentMethod, cardInfo (per the checkout payload in `src/basket/index.js`). No log scrubbing, no PII masking.
- **Gap**: PII is logged in plaintext and exposed in error responses. Customer data (names, emails, addresses, card info) flows through agent interactions and gets logged without redaction. This is a data protection violation risk, especially for a customer-facing support agent handling payment information.
- **Recommendation**: Remove `errorStack` from all production error responses. Implement PII redaction middleware that masks sensitive fields (email, address, cardInfo) in logs. Use CloudWatch Logs data protection policies to automatically detect and mask PII patterns.

#### SEC-Q7: Human Approval Workflows
- **Score**: 1/4 ❌
- **Finding**: No human approval workflows found. The checkout flow in `src/basket/index.js` proceeds automatically: get basket → prepare payload → publish event → delete basket. No approval gates, no confirmation steps, no human-in-the-loop mechanisms. No Step Functions with `waitForTaskToken` patterns.
- **Gap**: No guardrails for high-risk agent actions. A customer support agent that can place orders, modify baskets, or initiate refunds on behalf of customers must have human approval gates for high-value or irreversible operations. Without these, a malfunctioning agent could process unauthorized transactions.
- **Recommendation**: Implement Step Functions with human approval tasks for high-risk operations: orders above a threshold, refund requests, account modifications. Use SNS to notify support staff for approval. This is critical before deploying customer-facing agents.

#### SEC-Q8: Encryption at Rest
- **Score**: 2/4 🟠
- **Finding**: DynamoDB tables in `lib/database.ts` are created without explicit KMS key configuration. DynamoDB applies AWS-managed encryption at rest by default (AWS owned key). No customer-managed KMS keys (CMK) configured. No `encryptionKey` property set on any Table construct.
- **Gap**: Default AWS-managed encryption is applied, but no customer-managed KMS keys. Customer-managed keys provide key rotation control, usage auditing via CloudTrail, and the ability to revoke access — important for an agent handling customer payment and personal data.
- **Recommendation**: Add customer-managed KMS keys for the order and basket tables (which contain PII and payment data). Configure automatic key rotation. This provides auditable encryption for data the agent accesses.

#### SEC-Q9: API Authentication
- **Score**: 1/4 ❌
- **Finding**: No API Gateway authorizers configured in `lib/apigateway.ts`. No Cognito user pools, no Lambda authorizers, no API keys required. All three API Gateways (Product, Basket, Order) are publicly accessible without any authentication. The `LambdaRestApi` constructs use default settings with no authorization configuration.
- **Gap**: APIs are completely unauthenticated. Anyone with the API URL can read/write products, access any user's basket, and query any user's orders. This is the most critical security gap — deploying agents against unauthenticated APIs is dangerous.
- **Recommendation**: Add Cognito User Pool authorizer to all API Gateway endpoints as an immediate priority. Define separate authorization scopes for human users and agent service accounts. Implement API keys for agent-to-API authentication with usage tracking.

#### SEC-Q10: Centralized Identity
- **Score**: 1/4 ❌
- **Finding**: No Cognito, Okta, Ping, or any identity provider configuration found. No OIDC/SAML federation. No SSO configuration. User identity is a simple string (`userName`) passed as a URL parameter with no validation against any identity store.
- **Gap**: No centralized identity provider. Customer-facing agents need to authenticate customers, manage sessions, and enforce authorization policies. Without a centralized IdP, agent identity management becomes ad-hoc and insecure.
- **Recommendation**: Implement Amazon Cognito as the centralized identity provider. Create user pools for customers and separate identity pools for agent service accounts. Enable MFA for admin operations. This provides the foundation for SEC-Q3 (identity propagation) and SEC-Q9 (API authentication).

### Operations & Observability

#### OPS-Q1: Distributed Tracing
- **Score**: 1/4 ❌
- **Finding**: No X-Ray, OpenTelemetry, or any tracing SDK found. No `tracing: lambda.Tracing.ACTIVE` configuration in `lib/microservice.ts`. No trace ID propagation in Lambda code. No `traceparent` or `X-Amzn-Trace-Id` header handling. No tracing imports in any `package.json`.
- **Gap**: No distributed tracing. When a customer support agent chains tool calls (Product lookup → Basket update → Checkout), there is no way to trace the full request path across services. Agent debugging is impossible without end-to-end trace visibility.
- **Recommendation**: Enable X-Ray tracing on all Lambda functions by adding `tracing: lambda.Tracing.ACTIVE` in `lib/microservice.ts`. Add the `@aws-lambda-powertools/tracer` package to each service. Propagate trace IDs across EventBridge → SQS → Lambda for full checkout flow visibility.

#### OPS-Q2: Structured Logging
- **Score**: 1/4 ❌
- **Finding**: Lambda functions use `console.log` and `console.error` for logging. The event input is logged as `JSON.stringify(event, undefined, 2)` in all three index.js files. However, there is no structured logging library (winston JSON, pino, @aws-lambda-powertools/logger), no correlation IDs, no log levels, and no consistent log format across services.
- **Gap**: No structured logging. Agent interactions generate high-volume, multi-step logs that need correlation IDs to trace a single customer conversation across multiple tool invocations. Current console.log output cannot be efficiently queried or correlated.
- **Recommendation**: Add `@aws-lambda-powertools/logger` to all Lambda functions. Configure JSON-structured output with correlation IDs, service name, and log levels. Implement a middleware pattern that automatically adds trace context to all log entries.

#### OPS-Q3: Automated Evals
- **Score**: 1/4 ❌
- **Finding**: No evaluation framework, no golden datasets, no scoring scripts, no LLM-as-judge patterns found. No test datasets for agent quality measurement. The `test/aws-microservices.test.ts` file exists but is entirely commented out — no active tests of any kind.
- **Gap**: No way to measure agent quality. Before deploying a customer support agent, you must validate: Does it answer product questions correctly? Does it look up the right orders? Does it handle edge cases (empty baskets, invalid usernames)? Without automated evals, agent quality is unknown.
- **Recommendation**: Build an eval pipeline: (1) Create a golden dataset of 50+ customer support Q&A pairs covering product queries, order lookups, and checkout scenarios, (2) Implement scoring using RAGAS or LLM-as-judge, (3) Run evals in CI pipeline on every agent prompt or tool change.

#### OPS-Q4: SLOs
- **Score**: 1/4 ❌
- **Finding**: No SLO definitions found. No CloudWatch alarms in CDK. No error budget tracking. No `aws_cloudwatch_metric_alarm` resources. No dashboards.
- **Gap**: No service-level objectives. Agent-powered customer support has different latency and availability requirements than direct API access — customers expect sub-second responses from a chat agent. Without SLOs, there is no baseline to measure against.
- **Recommendation**: Define SLOs for critical paths: Product API p99 latency < 200ms, Checkout success rate > 99.5%, Order query p99 < 500ms. Create CloudWatch alarms for these thresholds. When agents are added, define agent-specific SLOs: task success rate, response latency, hallucination rate.

#### OPS-Q5: Rollback Capability
- **Score**: 1/4 ❌
- **Finding**: No deployment strategy or rollback mechanism. Deployments are manual `cdk deploy` per README. No blue/green, canary, or rolling deployment configuration. No CodeDeploy, no Lambda versions/aliases for traffic shifting, no feature flags.
- **Gap**: No safe rollback. When agent behavior degrades (wrong product recommendations, incorrect order lookups), there is no mechanism to quickly roll back to a known-good version. Agent prompt changes, model updates, and tool configuration changes all need safe deployment with rollback.
- **Recommendation**: Implement Lambda aliases with weighted traffic shifting for canary deployments. Use CDK Pipelines with manual approval gates. Add feature flags for agent capabilities so individual features can be disabled without full rollback.

#### OPS-Q6: LLM Cost Tracking
- **Score**: 1/4 ❌
- **Finding**: No LLM usage anywhere in the application, so no token tracking or cost attribution exists. No Bedrock, OpenAI, or any LLM SDK found. No custom CloudWatch metrics for token usage.
- **Gap**: No LLM cost tracking infrastructure. When the customer support agent is deployed, every conversation generates LLM token costs. Without per-request attribution, costs cannot be allocated to specific customers, features, or agent workflows.
- **Recommendation**: When implementing the agent, track token usage from the first day: log input/output tokens per Bedrock invocation, tag by customer session and workflow type, publish custom CloudWatch metrics. Implement tiered log retention policies for agent telemetry data.

#### OPS-Q7: Business Metrics
- **Score**: 1/4 ❌
- **Finding**: No custom CloudWatch metrics found. No business outcome tracking. Only `console.log` statements for debugging. No metrics for order success rates, basket conversion rates, product search effectiveness, or any business KPIs.
- **Gap**: No business metrics. Agent effectiveness must be measured in business terms: customer issue resolution rate, order completion rate, average handle time, customer satisfaction. Without baseline business metrics, agent impact cannot be quantified.
- **Recommendation**: Publish custom CloudWatch metrics for: checkout success/failure counts, product search result counts, order query latency, basket abandonment rates. These become the baseline against which agent-driven improvements are measured.

#### OPS-Q8: Anomaly Detection
- **Score**: 1/4 ❌
- **Finding**: No CloudWatch anomaly detection, no error rate alarms, no latency monitoring, no alerting integration (PagerDuty, OpsGenie, SNS). No composite alarms or anomaly detection models.
- **Gap**: No anomaly detection. Agents can silently degrade — an agent might start recommending out-of-stock products, giving incorrect order statuses, or entering retry loops. Without anomaly detection on error rates and latency, degradation goes unnoticed until customers complain.
- **Recommendation**: Enable CloudWatch anomaly detection on Lambda error rates and duration for all three functions. Set up composite alarms that trigger when error rate spikes or latency increases. Add behavioral anomaly detection for agent-specific patterns (e.g., sudden increase in tool invocations per conversation).

#### OPS-Q9: Deployment Strategy
- **Score**: 1/4 ❌
- **Finding**: Manual `cdk deploy` is the only deployment method per README. No CodeDeploy, no canary or blue/green configurations, no Lambda traffic shifting, no feature flags. No deployment pipeline of any kind.
- **Gap**: Direct-to-production deployments with no gradual rollout. Agent changes (prompt updates, tool modifications, model upgrades) are high-risk and should never go straight to all users simultaneously.
- **Recommendation**: Implement canary deployments using Lambda aliases with `CodeDeployLambdaAlias` in CDK. Route 10% of traffic to new version, monitor for errors, then shift to 100%. This is essential for safe agent rollouts.

#### OPS-Q10: Integration Testing
- **Score**: 1/4 ❌
- **Finding**: `test/aws-microservices.test.ts` exists but is entirely commented out. No active unit tests, integration tests, or end-to-end tests. The `package.json` has a `test` script (`jest`) but no test files are active. No Postman/Newman collections, no contract tests, no test containers.
- **Gap**: No automated testing. Agent tool integrations must be tested end-to-end: does the agent correctly invoke the Product API? Does the checkout flow complete when triggered by an agent? Without integration tests, agent releases are untested.
- **Recommendation**: Uncomment and update `test/aws-microservices.test.ts`. Add integration tests for each API endpoint. Add agent-specific tests: tool invocation tests, multi-step workflow tests, error handling tests. Run all tests in CI pipeline.

#### OPS-Q11: Incident Response Automation
- **Score**: 1/4 ❌
- **Finding**: No runbooks, no SSM Automation documents, no Lambda-based remediation functions, no self-healing patterns found. No dead letter queues on any Lambda function or on the SQS queue for error capture. No alerting or escalation configuration.
- **Gap**: No incident response automation. When an agent fails (e.g., checkout loop, wrong order lookups), there is no automated response — no circuit breaker, no auto-disable, no alert to operations. Agent incidents can cause harm at machine speed.
- **Recommendation**: Add DLQs to all Lambda functions and SQS queues. Create SSM runbooks for common agent failure scenarios. Implement auto-disable patterns: if agent error rate exceeds threshold, automatically disable agent capabilities and fall back to human support.

#### OPS-Q12: Observability Governance & Ownership
- **Score**: 1/4 ❌
- **Finding**: No CODEOWNERS file, no team ownership definitions, no SLO ownership models, no observability governance. No evidence of platform engineering or shared responsibility model for monitoring.
- **Gap**: No observability ownership. When agents are deployed, someone needs to own agent quality, reliability, and safety metrics. Without clear ownership, agent monitoring gaps go unaddressed and incidents have unclear accountability.
- **Recommendation**: Create a CODEOWNERS file defining ownership for each service and the future agent layer. Establish an observability ownership model: platform team owns infrastructure metrics, product team owns agent quality metrics (success rate, hallucination rate, customer satisfaction). Define agent-level SLOs with named owners.

---

## Recommended Modernization Pathways

Based on the assessment findings, the following AWS Modernization Pathways are evaluated for this application. Multiple pathways can execute in parallel because modern applications comprise multiple interconnected components — each requiring its own modernization approach.

### Pathway Summary

| Pathway | Status | Goal Alignment | Priority | Key Trigger Criteria | Est. Effort |
|---------|--------|---------------|----------|---------------------|-------------|
| Move to Cloud Native | Not Triggered | Medium | — | — | — |
| Move to Containers | Not Triggered | Medium | — | — | — |
| Move to Open Source | Not Triggered | Low | — | — | — |
| Move to Managed Databases | Not Triggered | High | — | — | — |
| Move to Managed Analytics | Not Triggered | Low | — | — | — |
| Move to Modern DevOps | Triggered | High | High | INF-Q6: 1/4, OPS-Q9: 1/4, OPS-Q10: 1/4, OPS-Q1: 1/4 | High |
| Move to AI | Triggered | High | High | APP-Q13: 1/4, DATA-Q1: 1/4, DATA-Q3: 1/4, OPS-Q3: 1/4, OPS-Q6: 1/4 | High |

### Parallel Execution Plan

**Parallel Track 1 — Modern DevOps**: CI/CD pipeline, deployment strategies, testing, observability — can execute immediately and independently.

**Parallel Track 2 — Move to AI**: Agent framework integration, vector database, RAG pipeline, eval framework — can execute in parallel with DevOps modernization.

**Sequential Dependencies**: None between the two triggered pathways. Modern DevOps improvements (CI/CD, testing, deployment strategies) enhance the safety of AI deployments but are not strict prerequisites. Both tracks can start simultaneously.

### Move to Modern DevOps

- **Priority**: High
- **Goal Alignment**: High
- **Trigger Criteria Met**:
  - INF-Q6: Score 1/4 — No CI/CD pipeline; manual `cdk deploy` only
  - OPS-Q9: Score 1/4 — No deployment strategy; direct-to-production via manual deployment
  - OPS-Q10: Score 1/4 — No integration tests; `test/aws-microservices.test.ts` entirely commented out
  - OPS-Q1: Score 1/4 — No distributed tracing; no X-Ray or OpenTelemetry
- **Current State**: All deployments are manual `cdk deploy`. No testing, no tracing, no deployment safety. The test file exists but is commented out. No CI/CD pipeline of any kind.
- **Target State**: Automated CI/CD pipeline with test → build → deploy stages, canary deployments with automatic rollback, distributed tracing across all Lambda functions and EventBridge flows, integration test suites covering all API endpoints and the checkout workflow.
- **Key Activities**:
  1. Create GitHub Actions workflow with CDK diff, test, and deploy stages
  2. Enable X-Ray tracing on all Lambda functions via `lib/microservice.ts`
  3. Add `@aws-lambda-powertools` (logger, tracer, metrics) to all Lambda functions
  4. Uncomment and expand `test/aws-microservices.test.ts` with integration tests
  5. Implement Lambda alias-based canary deployments with auto-rollback
  6. Define CloudWatch alarms and SLOs for all critical paths
- **Dependencies**: None
- **Estimated Effort**: High — requires building CI/CD, testing, observability, and deployment strategy from scratch across 3 services
- **Roadmap Phase Alignment**: Phase 1 (Agent Quick Wins) for CI/CD and tracing; Phase 2 (Agent Foundations) for advanced deployment strategies and SLOs
- **Relevant Learning Materials**: Module 6 — Move to Modern DevOps

### Move to AI

- **Priority**: High
- **Goal Alignment**: High
- **Trigger Criteria Met**:
  - APP-Q13: Score 1/4 — No AI/agent frameworks in any service
  - DATA-Q1: Score 1/4 — No vector database for semantic search
  - DATA-Q3: Score 1/4 — No RAG implementation for knowledge retrieval
  - OPS-Q3: Score 1/4 — No automated evaluation framework
  - OPS-Q6: Score 1/4 — No LLM cost tracking
- **Current State**: Zero AI/agent infrastructure. No Bedrock, LangChain, or agent SDKs. No vector database or RAG pipeline. No eval framework. The application has no AI capabilities of any kind.
- **Target State**: Customer-facing AI agent for support and order management using Amazon Bedrock with Strands Agents SDK, backed by Bedrock Knowledge Bases (OpenSearch Serverless) for product and order knowledge retrieval, with automated eval pipelines and per-request LLM cost tracking.
- **Key Activities**:
  1. Generate OpenAPI specs for all three API Gateways (APP-Q2 prerequisite)
  2. Create agent Lambda function with Bedrock and Strands Agents SDK
  3. Define tool interfaces for Product, Basket, and Order services
  4. Provision Bedrock Knowledge Base with OpenSearch Serverless for product catalog RAG
  5. Build eval pipeline with golden dataset of customer support scenarios
  6. Implement LLM token tracking with CloudWatch custom metrics
  7. Add human approval workflow (Step Functions) for high-risk agent actions (orders, refunds)
- **Dependencies**: API authentication (SEC-Q9) should be implemented before agents are deployed to production. OpenAPI specs (APP-Q2) are prerequisite for agent tool discovery.
- **Estimated Effort**: High — requires building entire AI stack from scratch: agent framework, vector database, RAG pipeline, eval framework, safety guardrails
- **Roadmap Phase Alignment**: Phase 1 (Agent Quick Wins) for proof-of-concept agent; Phase 2 (Agent Foundations) for RAG and evals; Phase 3 (Agent Scale & Optimization) for production hardening
- **Relevant Learning Materials**: Module 7 — Move to AI

---

## Quick Agent Wins

Even before completing the full modernization roadmap, these agent opportunities are available based on your current architecture:

1. **Customer Support Agent with JSON API Tools** — Your existing APIs return structured JSON responses (`{ statusCode, body: JSON.stringify({message, body}) }` in all three Lambda services), making them immediately usable as agent tools. A customer support agent can invoke the Product API to search inventory, the Basket API to check cart contents, and the Order API to look up order status — all without any API changes.
   - **Leverages**: Structured JSON responses across all three API Gateway services (`lib/apigateway.ts`)
   - **Effort**: Medium
   - **Value**: Enables a proof-of-concept customer support agent that can answer "What products do you have?", "What's in my cart?", and "Where is my order?" using existing endpoints

2. **Product Knowledge Agent with RAG** — Your `README.md` and product catalog data (DynamoDB `product` table with name, description, category, price fields per `lib/database.ts`) can be indexed into a Bedrock Knowledge Base to build a knowledge-grounded agent that answers product questions accurately.
   - **Leverages**: Existing product data schema in DynamoDB (`lib/database.ts`), `README.md` documentation
   - **Effort**: Medium
   - **Value**: Customers can ask "Do you have phones under $500?" or "What's the difference between product X and Y?" and get accurate, grounded responses from your actual product catalog

3. **Order Inquiry Agent with Natural Language to DynamoDB** — Your order table has a clear schema (PK: userName, SK: orderDate with totalPrice, firstName, lastName, email, address, paymentMethod per `lib/database.ts` comments). A data query agent can translate natural language questions ("Show me orders from last week" or "What did customer swn order?") into DynamoDB queries against the existing Order API.
   - **Leverages**: Well-documented DynamoDB schema in `lib/database.ts` comments, existing Order API (`GET /order/{userName}`)
   - **Effort**: Low
   - **Value**: Customer support staff or customers can query order history in natural language instead of needing exact userName and orderDate parameters

> These opportunities can be pursued in parallel with the modernization roadmap.
> They demonstrate agent value early while foundations are being built.

---

## Readiness Roadmap

### Phase 1 — Agent Quick Wins (Days 1–30)

Low-effort, high-impact actions that establish agent foundations and demonstrate value quickly:

1. **Generate OpenAPI 3.0 specs** for all three API Gateways (Product, Basket, Order) from the existing route definitions in `lib/apigateway.ts`. This unlocks agent tool discovery and is the single highest-priority action.
2. **Upgrade Lambda runtime** from `NODEJS_14_X` (EOL) to `NODEJS_20_X` in `lib/microservice.ts` across all three functions.
3. **Enable X-Ray tracing** on all Lambda functions by adding `tracing: lambda.Tracing.ACTIVE` to each `NodejsFunctionProps` in `lib/microservice.ts`.
4. **Add `@aws-lambda-powertools`** (logger, tracer, metrics) to all three Lambda services for structured logging and observability.
5. **Create CI/CD pipeline** — GitHub Actions workflow with `cdk diff`, `npm test`, and `cdk deploy` stages. Use OIDC for AWS authentication.
6. **Build proof-of-concept agent** — Create a new Lambda function with `@aws-sdk/client-bedrock-runtime` and Strands Agents SDK that can invoke the Product and Order APIs as tools. Deploy via CDK.
7. **Add DLQs** to `OrderQueue` in `lib/queue.ts` and all Lambda functions for error capture.

### Phase 2 — Agent Foundations (Months 1–3)

Structural improvements that establish the security, data, and operational foundations for production agents:

1. **Implement API authentication** — Add Amazon Cognito User Pool with JWT authorizer to all API Gateway endpoints in `lib/apigateway.ts`. Define separate scopes for customers and agent service accounts.
2. **Provision Bedrock Knowledge Base** with OpenSearch Serverless. Index product catalog data from DynamoDB `product` table. Implement RAG pipeline with Titan Embeddings for the customer support agent.
3. **Build automated eval pipeline** — Create golden dataset of 50+ customer support Q&A pairs. Implement RAGAS or LLM-as-judge scoring. Run evals in CI pipeline.
4. **Implement idempotency** — Add `@aws-lambda-powertools/idempotency` to all write operations. Convert `OrderQueue` to FIFO with deduplication.
5. **Add API Gateway throttling** — Configure usage plans with per-client rate limits. Create separate API keys for human users and agents.
6. **Implement human approval workflows** — Add Step Functions with `waitForTaskToken` for high-risk agent operations (checkout above threshold, account modifications).
7. **Add PII redaction** — Remove `errorStack` from error responses. Implement CloudWatch Logs data protection policies. Mask PII in logs.
8. **Implement LLM cost tracking** — Log input/output tokens per Bedrock invocation with customer session and workflow attribution. Publish CloudWatch custom metrics.
9. **Enable DynamoDB Streams** on the product table for event-driven embedding freshness. Create a Lambda function to update Knowledge Base when products change.

### Phase 3 — Agent Scale & Optimization (Months 3–6)

Advanced capabilities that optimize agent performance, safety, and operational maturity at scale:

1. **Implement canary deployments** — Lambda aliases with weighted traffic shifting for all functions, including the agent Lambda. Auto-rollback on error rate threshold.
2. **Define and monitor agent SLOs** — Task success rate > 95%, response latency p99 < 3s, hallucination rate < 5%. Create CloudWatch dashboards and alarms with named owners.
3. **Add anomaly detection** — CloudWatch anomaly detection on Lambda error rates, agent tool invocation counts, and conversation length. Alert on behavioral baseline deviations.
4. **Implement Step Functions orchestration** — Migrate the checkout workflow from hardcoded sequence to Step Functions. Add agent workflow orchestration (multi-tool chains with retry and compensation).
5. **Add VPC and network security** — Deploy Lambda functions in VPC with private subnets and VPC endpoints for DynamoDB and EventBridge. This isolates PII-handling services.
6. **Build service catalog for agent tool discovery** — Formalize API catalog with versioned tool definitions, input/output schemas, and capability descriptions that agents can query at runtime.
7. **Implement observability governance** — Create CODEOWNERS file, establish SLO ownership model, define shared responsibility for agent quality metrics between platform and product teams.
8. **Expand RAG to order history and support FAQs** — Extend Knowledge Base to include order data, returns policies, and customer support FAQs for comprehensive agent grounding.

---

## Recommended Self-Paced Learning Materials

### Module 6: Move to Modern DevOps
Critical for building the CI/CD, testing, and observability foundations needed before deploying agents to production.

- **Getting Started with DevOps on AWS** — https://skillbuilder.aws/learn/R4B13K95YQ/getting-started-with-devops-on-aws/38NHHYRV1R
  - Foundational overview of AWS DevOps practices, directly applicable to establishing CI/CD for this CDK-based application.
- **Create a CI/CD Pipeline to Deploy Your App to AWS Fargate (ECS)** — https://skillbuilder.aws/learn/H61B17Z8R7/create-a-cicd-pipeline-to-deploy-your-app-to-aws-fargate/T66BGGGHV5
  - Hands-on pipeline creation applicable to Lambda deployment patterns.
- **AWS CloudFormation Getting Started** — https://skillbuilder.aws/learn/RH22P2RXU4/aws-cloudformation-getting-started/KEK5BT6HSE
  - Relevant since CDK synthesizes to CloudFormation — understanding the underlying framework improves troubleshooting.
- **Advanced Testing Practices Using AWS DevOps Tools** — https://skillbuilder.aws/learn/1YC7UXUWBR/advanced-testing-practices-using-aws-devops-tools/A32U6G7NEQ
  - Essential for building the integration test suite this application lacks (OPS-Q10).
- **Monitor Python Applications Using Amazon CloudWatch Application Signals** — https://skillbuilder.aws/learn/JMPDZD64MV/monitor-python-applications-using-amazon-cloudwatch-application-signals/2JP3J2MPCK
  - Applicable observability patterns for establishing SLOs and monitoring (OPS-Q4, OPS-Q8).
- **AWS Developer: CI/CD Automation** — https://skillbuilder.aws/learn/C1KF8ZJ1D8/aws-developer--cicd-automation/KY1E1JS9FA
  - Comprehensive CI/CD automation course addressing the INF-Q6 gap.
- **AWS Modernization Pathways: Move to Modern DevOps** — https://skillbuilder.aws/learning-plan/1FGEQKGPQD/aws-modernization-pathways-move-to-modern-devops-includes-labs/MNQZ2KPVCK
  - Complete learning plan covering the full DevOps modernization pathway.

### Module 7: Move to AI
Core learning path for building the customer support agent with Bedrock, RAG, and agent frameworks.

- **Introduction to Agentic AI on AWS** — https://skillbuilder.aws/learn/DNBD5MT8ZD/introduction-to-agentic-ai-on-aws/WAKAFK6UFY
  - Essential starting point — covers agentic AI concepts, patterns, and AWS services.
- **Amazon Bedrock Getting Started** — https://skillbuilder.aws/learn/63KTRM86DQ/amazon-bedrock-getting-started/SC2Y3HMAUE
  - Foundation for all Bedrock-based agent development.
- **Build and Evaluate Retrieval Augmented Generation (RAG) Applications using Knowledge Bases for Amazon Bedrock (Lab)** — https://skillbuilder.aws/learn/JRGWCFYT67/lab--build-and-evaluate-retrieval-augmented-generation-rag-applications-using-knowledge-bases-for-amazon-bedrock/A4MN58JB7A
  - Directly applicable to building the product catalog RAG pipeline (DATA-Q1, DATA-Q3).
- **Essentials for Prompt Engineering** — https://skillbuilder.aws/learn/XBNAVKA88J/essentials-of-prompt-engineering/9T9Q45EDTV
  - Critical for crafting effective customer support agent prompts.
- **Planning a Generative AI Project** — https://skillbuilder.aws/learn/HU1FQRGDDZ/planning-a-generative-ai-project/SYR3SCPSHC
  - Strategic planning for the agent project, including eval framework design (OPS-Q3).
- **Creating an AWS DevOps AI Agent with the Strands Agents SDK (Lab)** — https://skillbuilder.aws/learn/AH1GD8AJY3/lab--creating-an-aws-devops-ai-agent-with-the-strands-agents-sdk/A9SKJNMPJ2
  - Hands-on agent development with Strands Agents SDK — directly applicable to building the customer support agent.
- **DevOps and AI on AWS: CloudWatch Anomaly Detection (Lab)** — https://skillbuilder.aws/learn/RWYVJ73MXP/lab--devops-and-ai-on-aws-cloudwatch-anomaly-detection/BRPDNZUGU7
  - Applicable to implementing anomaly detection for agent behavior monitoring (OPS-Q8).
- **AWS PartnerCast: Deep Dive: Building Observable AI Agents with Strands, Amazon Bedrock Agent Core & SageMaker MLflow** — https://skillbuilder.aws/learn/1EN76TZBB6/aws-partnercast--deep-dive-building-observable-ai-agents-with-strands-amazon-bedrock-agent-core--sagemaker-mlflow--technical/CX2K6XAT84
  - Advanced observability for agent systems — addresses OPS-Q1, OPS-Q6, and OPS-Q3 gaps.
- **AWS Modernization Pathways: Move to AI** — https://skillbuilder.aws/learning-plan/VDFEE4ACCV/aws-modernization-pathways-move-to-ai-pathways-includes-labs/P3DAWPTN63
  - Complete learning plan for the AI modernization pathway.

### Module 2: Move to Cloud Native (Containers and Serverless)
Relevant for deepening serverless patterns and event-driven architecture skills.

- **Cloud Design Patterns, Architectures, and Implementations** — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html
  - Essential reference for event-driven patterns (Saga, Event Sourcing), resilience patterns (Circuit Breaker, Retry with Backoff), and API routing patterns directly applicable to agent workflow design.
- **Lambda Foundations** — https://skillbuilder.aws/learn/XHRS91KKK6/aws-lambda-foundations/R85JRN3APC
  - Strengthens Lambda best practices relevant to the existing serverless architecture.

### Module 4: Move to Managed Databases
Relevant for vector database and Knowledge Base provisioning.

- **AWS PartnerCast: Vector Databases for Generative AI Applications** — https://skillbuilder.aws/learn/UQ74USQJHU/aws-partnercast--vector-databases-for-generative-ai-applications--technical/7DKMBAPCST
  - Directly relevant to DATA-Q1 and DATA-Q2 gaps — understanding vector database options for the RAG pipeline.

---

## Appendix: Evidence Index

| # | File | Key Evidence |
|---|------|-------------|
| 1 | `lib/aws-microservices-stack.ts` | Main CDK stack orchestrating all constructs: Database, Microservices, ApiGateway, Queue, EventBus |
| 2 | `lib/microservice.ts` | Lambda function definitions for all 3 services; Runtime.NODEJS_14_X (EOL); environment variables; grantReadWriteData permissions |
| 3 | `lib/apigateway.ts` | Three LambdaRestApi instances (Product, Basket, Order); resource/method definitions; no auth, throttling, or validation |
| 4 | `lib/database.ts` | Three DynamoDB tables (product, basket, order); PAY_PER_REQUEST billing; schema comments documenting attributes |
| 5 | `lib/eventbus.ts` | EventBridge bus (SwnEventBus); CheckoutBasketRule routing to SQS; grantPutEventsTo for basket Lambda |
| 6 | `lib/queue.ts` | SQS OrderQueue; visibilityTimeout 30s; batchSize 1; no DLQ configured |
| 7 | `src/product/index.js` | Product Lambda handler: GET/POST/PUT/DELETE operations; uuidv4 for creation; ScanCommand for list; errorStack in responses |
| 8 | `src/product/ddbClient.js` | DynamoDB client instantiation — 5-line thin wrapper |
| 9 | `src/product/package.json` | Dependencies: @aws-sdk/client-dynamodb ^3.55.0, @aws-sdk/util-dynamodb ^3.55.0 |
| 10 | `src/basket/index.js` | Basket Lambda handler: CRUD + checkout; checkoutBasket flow (get→prepare→publish→delete); EventBridge event publishing |
| 11 | `src/basket/eventBridgeClient.js` | EventBridge client instantiation for checkout event publishing |
| 12 | `src/basket/package.json` | Dependencies: @aws-sdk/client-dynamodb, @aws-sdk/client-eventbridge, @aws-sdk/util-dynamodb |
| 13 | `src/basket/checkoutbasketevents.json` | Sample EventBridge events: source=com.swn.basket.checkoutbasket, detailType=CheckoutBasket |
| 14 | `src/ordering/index.js` | Ordering Lambda handler: SQS invocation, EventBridge invocation, API Gateway invocation; createOrder with PutItemCommand |
| 15 | `src/ordering/package.json` | Dependencies: @aws-sdk/client-dynamodb ^3.58.0, @aws-sdk/util-dynamodb ^3.58.0 |
| 16 | `bin/aws-microservices.ts` | CDK app entry point; single AwsMicroservicesStack; no env configuration |
| 17 | `package.json` | Root CDK package: aws-cdk-lib 2.17.0, TypeScript ~3.9.7; scripts: build, test, cdk; no AI/agent dependencies |
| 18 | `test/aws-microservices.test.ts` | Test file entirely commented out — no active tests |
| 19 | `README.md` | Project documentation: serverless e-commerce, manual cdk deploy instructions, API endpoint examples |
| 20 | `cdk.json` | CDK configuration with feature flags; no custom context for agent or observability settings |
