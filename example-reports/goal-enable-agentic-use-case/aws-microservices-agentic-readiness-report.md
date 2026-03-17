# Agentic Readiness Assessment Report
**Target**: ./services/aws-microservices
**Date**: 2026-03-17
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Assessment Goal**: enable-agentic-use-case
**Goal Context**: Building an AI agent that handles order status inquiries, processes returns, and manages inventory restocking across the e-commerce platform
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

This serverless e-commerce platform has a **strong foundational architecture** for agentic use cases — three independent microservices (product, basket, ordering) built on AWS Lambda, DynamoDB, API Gateway, EventBridge, and SQS, all defined in CDK Infrastructure as Code. The microservices pattern with clear service boundaries and event-driven communication via EventBridge provides natural "tool" boundaries for an AI agent handling order inquiries, returns, and inventory restocking. However, **critical gaps block agent integration today**: no API documentation (OpenAPI specs) for agent tool discovery, no authentication or authorization on any endpoint, no AI/agent frameworks integrated, no vector database or RAG pipeline for knowledge retrieval, no CI/CD pipeline for safe iterative deployment, and near-zero observability infrastructure. The security posture is particularly concerning — all API endpoints are publicly accessible with no auth, no PII redaction, and no human approval gates for high-risk agent actions like processing returns. Addressing API documentation, security, and CI/CD are the highest-priority prerequisites before connecting an agent to these services.

### Overall Score: 1.73 / 4.0

| Category | Score | Status |
|----------|-------|--------|
| Infrastructure & Platform | 2.5 / 4.0 | 🟡 |
| Application Architecture | 1.85 / 4.0 | 🟡 |
| Data Foundations | 1.91 / 4.0 | 🟡 |
| Identity, Security & Governance | 1.4 / 4.0 | ❌ |
| Operations & Observability | 1.0 / 4.0 | ❌ |

---

## Top Priorities (Critical Gaps)

### 1. APP-Q2 — API Documentation (Score: 1/4) ❌
**Why it blocks your agent**: An AI agent that handles order status inquiries, returns, and inventory restocking needs to discover and understand your API endpoints programmatically. Without OpenAPI specs, the agent cannot auto-discover available tools (product CRUD, basket operations, order queries), understand request/response schemas, or validate its own API calls. This is the single highest-impact gap for your agentic use case.
**First step**: Generate OpenAPI 3.0 specs for all three API Gateways (Product, Basket, Order) — start by exporting the current API Gateway definitions and enriching them with request/response schemas.

### 2. APP-Q13 — AI/Agent Frameworks (Score: 1/4) ❌
**Why it blocks your agent**: No agent SDK, LLM integration, or tool-use framework exists in the codebase. The agent needs a framework (e.g., Strands Agents SDK, LangChain.js, or Amazon Bedrock Agents) to orchestrate multi-step workflows like "check order status → determine if eligible for return → process return → trigger restocking."
**First step**: Add the Strands Agents SDK or Amazon Bedrock Agent integration as a new Lambda function that acts as the agent orchestrator, using the existing microservice APIs as tools.

### 3. DATA-Q1 — Vector Database Presence (Score: 1/4) ❌
**Why it blocks your agent**: The agent needs semantic search to answer natural language questions about products, orders, and return policies. Without a vector database, the agent cannot perform RAG (Retrieval Augmented Generation) to ground its responses in your actual product catalog, order history, or policy documents.
**First step**: Add an Amazon OpenSearch Serverless collection with vector search enabled, or configure a Bedrock Knowledge Base backed by S3 for product documentation and return policies.

### 4. OPS-Q3 — Automated Evals (Score: 1/4) ❌
**Why it blocks your agent**: Without an evaluation framework, you cannot measure whether the agent correctly identifies order statuses, processes returns accurately, or makes appropriate restocking decisions. Agent quality degrades silently without automated evaluation against golden datasets.
**First step**: Create a golden dataset of 50+ test cases covering order status inquiries, return eligibility checks, and restocking triggers. Implement automated eval scripts that score agent responses against expected outcomes.

### 5. SEC-Q7 — Human Approval Workflows (Score: 1/4) ❌
**Why it blocks your agent**: Processing returns and managing inventory restocking are high-risk financial operations. Without human-in-the-loop approval gates, an agent could autonomously process fraudulent returns or trigger inappropriate restocking orders at scale. This is a safety-critical gap.
**First step**: Implement a Step Functions workflow with a human approval task (waitForTaskToken) that gates return processing and large restocking orders above a configurable threshold.

---

## Detailed Findings

### Infrastructure & Platform

#### INF-Q1: Compute
- **Score**: 4/4 ✅
- **Finding**: All three microservices (product, basket, ordering) are deployed as AWS Lambda functions using `NodejsFunction` construct in `lib/microservice.ts`. Runtime is `Runtime.NODEJS_14_X`. No EC2, ECS, or EKS resources are defined anywhere in the CDK stack. Compute is 100% serverless Lambda.
- **Gap**: The Node.js 14.x runtime is end-of-life (EOL as of April 2023). While compute is fully serverless (score 4), the EOL runtime is a maintenance and security risk that should be upgraded.
- **Recommendation**: Upgrade all three Lambda functions from `Runtime.NODEJS_14_X` to `Runtime.NODEJS_20_X` or `Runtime.NODEJS_22_X` in `lib/microservice.ts`. Update the AWS SDK v3 imports accordingly.

#### INF-Q2: Databases
- **Score**: 4/4 ✅
- **Finding**: All three data stores are DynamoDB tables defined in `lib/database.ts` using `aws-cdk-lib/aws-dynamodb.Table`: `product` (PK: id), `basket` (PK: userName), `order` (PK: userName, SK: orderDate). All use `BillingMode.PAY_PER_REQUEST`. No self-managed databases detected anywhere.
- **Gap**: None. All databases are fully managed with automatic scaling and no operational overhead.
- **Recommendation**: No database migration needed. Consider enabling DynamoDB Point-in-Time Recovery (PITR) for the order table to support agent audit requirements.

#### INF-Q3: Workflow Orchestration
- **Score**: 1/4 ❌
- **Finding**: No Step Functions, Temporal, Camunda, or any dedicated workflow orchestration service found in the CDK stack. The checkout flow (`basket/index.js` → `checkoutBasket` function) is a hardcoded sequential process: get basket → prepare payload → publish EventBridge event → delete basket. There is no state machine managing this flow.
- **Gap**: No dedicated workflow orchestration. The checkout flow is fragile — if the EventBridge publish succeeds but the basket delete fails, there is no compensation or retry logic.
- **Recommendation**: Implement AWS Step Functions for the checkout workflow and for the planned agent orchestration (order inquiry → return processing → restocking). Step Functions integrates natively with Lambda, DynamoDB, SQS, and EventBridge. Add it to the CDK stack using `aws-cdk-lib/aws-stepfunctions`.

#### INF-Q4: Async Messaging
- **Score**: 4/4 ✅
- **Finding**: EventBridge (`SwnEventBus` in `lib/eventbus.ts`) and SQS (`OrderQueue` in `lib/queue.ts`) are both present and actively used. The checkout flow publishes a `CheckoutBasket` event to EventBridge, which routes it via `CheckoutBasketRule` to the SQS queue, which triggers the ordering Lambda. Both are fully managed AWS services.
- **Gap**: None for messaging infrastructure. The EventBridge + SQS pattern is well-suited for agent-driven async operations.
- **Recommendation**: Extend the EventBridge event bus to support additional agent-triggered events (e.g., `ReturnRequested`, `RestockTriggered`). Add SNS for notification patterns where the agent needs to alert humans.

#### INF-Q5: Infrastructure as Code
- **Score**: 4/4 ✅
- **Finding**: 100% of infrastructure is defined in AWS CDK across 6 construct files: `lib/aws-microservices-stack.ts` (orchestration), `lib/database.ts` (DynamoDB tables), `lib/microservice.ts` (Lambda functions), `lib/apigateway.ts` (API Gateways), `lib/eventbus.ts` (EventBridge), `lib/queue.ts` (SQS). All resources — compute, databases, API Gateway, messaging — are IaC-defined.
- **Gap**: None. Full IaC coverage achieved.
- **Recommendation**: Consider adding CDK stack tags for cost allocation and environment differentiation. Add CDK Nag for security compliance checks in the pipeline (once CI/CD is established).

#### INF-Q6: CI/CD
- **Score**: 1/4 ❌
- **Finding**: No CI/CD pipeline definitions found anywhere in the repository. No `.github/workflows/`, no `buildspec.yml`, no `Jenkinsfile`, no `CodePipeline` definitions in CDK. Deployment is entirely manual via `cdk deploy` as documented in the README.
- **Gap**: Manual deployment blocks safe iterative agent development. Without CI/CD, there is no automated testing, no staged rollouts, and no ability to safely deploy agent updates.
- **Recommendation**: Create a GitHub Actions workflow (or AWS CodePipeline in CDK) with stages: lint → unit test → CDK synth → CDK diff → CDK deploy (to staging) → integration test → CDK deploy (to production). This is a Phase 1 priority.

#### INF-Q7: API Entry Point
- **Score**: 2/4 🟠
- **Finding**: Three separate `LambdaRestApi` instances are created in `lib/apigateway.ts` — `productApi` (Product Service), `basketApi` (Basket Service), `orderApi` (Order Service). Each exposes REST endpoints with explicit resource definitions (not proxy mode). However, no throttling configuration, no authorizers, no request validation, and no WAF integration are configured on any gateway.
- **Gap**: API Gateways exist but lack throttling, authentication, and request validation. An agent making rapid API calls could overwhelm the service, and there are no guardrails to prevent abuse.
- **Recommendation**: Add `deployOptions` with throttling (e.g., `{ throttlingBurstLimit: 100, throttlingRateLimit: 50 }`) to each `LambdaRestApi`. Add a Cognito or Lambda authorizer. Add request validators with models for POST/PUT operations.

#### INF-Q8: Real-time Streaming
- **Score**: 1/4 ❌
- **Finding**: No Kinesis Data Streams, Kinesis Data Firehose, or Amazon MSK found in the CDK stack. EventBridge is used for event routing (not streaming). No streaming consumer patterns in Lambda code.
- **Gap**: No real-time streaming capability. For the agent use case, real-time order status updates and inventory change streams would enable proactive agent behavior (e.g., notifying customers of order updates automatically).
- **Recommendation**: Evaluate whether DynamoDB Streams could provide change data capture for the order and product tables. If real-time inventory monitoring is needed for the restocking agent, add Kinesis Data Streams to capture inventory change events.

#### INF-Q9: Network Security
- **Score**: 1/4 ❌
- **Finding**: No VPC, subnet, security group, or NACL configuration found in the CDK stack. All Lambda functions run in the default AWS Lambda execution environment without custom VPC configuration. API Gateways are publicly accessible with no WAF.
- **Gap**: No network-level security controls. While Lambda in default VPC has internet access for DynamoDB (which uses HTTPS endpoints), there are no network isolation controls to limit blast radius.
- **Recommendation**: For the agent use case, add VPC configuration with private subnets and VPC endpoints for DynamoDB and EventBridge. This prevents data exfiltration and ensures all traffic stays within the AWS network. Add WAF to API Gateways.

#### INF-Q10: Auto-scaling
- **Score**: 3/4 🟡
- **Finding**: Lambda provides implicit auto-scaling (concurrent executions scale automatically). DynamoDB with `PAY_PER_REQUEST` billing mode provides implicit on-demand scaling. No explicit auto-scaling policies are needed for either service. However, no Lambda reserved or provisioned concurrency limits are configured in `lib/microservice.ts`.
- **Gap**: No Lambda concurrency limits configured. An agent making many concurrent API calls could trigger runaway Lambda invocations, leading to unexpected costs and potential DynamoDB throttling.
- **Recommendation**: Set `reservedConcurrentExecutions` on each Lambda function in `lib/microservice.ts` to prevent runaway invocations. Consider provisioned concurrency for latency-sensitive agent-facing endpoints.

### Application Architecture

#### APP-Q1: Programming Languages
- **Score**: 3/4 🟡
- **Finding**: Lambda function source code is JavaScript (ES module syntax) in `src/product/index.js`, `src/basket/index.js`, and `src/ordering/index.js`. CDK infrastructure is TypeScript (`lib/*.ts`). Dependencies use AWS SDK v3 (`@aws-sdk/client-dynamodb@^3.55.0`, `@aws-sdk/client-eventbridge@^3.58.0`). The root `package.json` uses TypeScript 3.9.7 and CDK 2.17.0.
- **Gap**: JavaScript has a decent agent framework ecosystem (LangChain.js, Strands Agents SDK) but is not as mature as Python for AI/agent development. TypeScript would be preferred over plain JavaScript for type safety in agent tool definitions.
- **Recommendation**: Consider migrating Lambda source code from JavaScript to TypeScript for type safety and better IDE support when defining agent tools. This also aligns with the CDK codebase which is already TypeScript.

#### APP-Q2: API Documentation
- **Score**: 1/4 ❌
- **Finding**: No OpenAPI/Swagger specification files found anywhere in the repository. No `openapi.yaml`, `swagger.json`, or API documentation files. API routes are defined in `lib/apigateway.ts` via CDK code comments (e.g., `// GET /product`, `// POST /basket/checkout`) but there are no formal API specs with request/response schemas.
- **Gap**: Complete absence of API documentation. The agent cannot programmatically discover available endpoints, understand request payloads, or validate response schemas. This is the most critical gap for the agentic use case.
- **Recommendation**: Generate OpenAPI 3.0 specifications for all three API Gateways. Define request/response models in CDK using `apigateway.Model` and add `requestValidator` to methods. Export specs from API Gateway or create them manually based on the route definitions in `lib/apigateway.ts`.

#### APP-Q3: Async vs Sync Communication
- **Score**: 2/4 🟠
- **Finding**: The checkout flow is async: `basket/index.js` publishes a `CheckoutBasket` event to EventBridge (`publishCheckoutBasketEvent`), which routes to SQS (`OrderQueue`), which triggers `ordering/index.js`. All other operations are synchronous API Gateway → Lambda → DynamoDB: product CRUD (5 operations), basket CRUD (4 operations), order queries (2 operations). Approximately 1 out of 12 distinct operations uses async communication.
- **Gap**: Heavy reliance on sync API calls. For the agent use case, operations like return processing and restocking should be async to prevent agent timeouts and enable status tracking.
- **Recommendation**: Add async patterns for return processing and restocking operations. Use EventBridge events (e.g., `ReturnRequested`, `RestockTriggered`) following the existing checkout pattern. Implement status polling endpoints so the agent can check async operation progress.

#### APP-Q4: Monolith vs Microservices
- **Score**: 4/4 ✅
- **Finding**: Three independent microservices with clear domain boundaries: **Product** (`src/product/`) manages product catalog with its own DynamoDB table and API Gateway, **Basket** (`src/basket/`) manages shopping carts with its own table and gateway, **Ordering** (`src/ordering/`) manages orders with its own table and gateway. Inter-service communication is via EventBridge events (not direct API calls). Each service has its own `package.json` with independent dependencies.
- **Gap**: None. The microservices architecture with clear boundaries is ideal for agent tool definition — each service maps naturally to an agent tool.
- **Recommendation**: Maintain this clean service boundary pattern when adding agent capabilities. Define agent tools per service: `ProductTool`, `BasketTool`, `OrderTool`.

#### APP-Q5: API Response Format
- **Score**: 4/4 ✅
- **Finding**: All three Lambda functions return structured JSON responses with a consistent format: `{ statusCode: 200, body: JSON.stringify({ message: "...", body: <data> }) }`. Error responses also follow a consistent structure: `{ statusCode: 500, body: JSON.stringify({ message: "...", errorMsg: e.message, errorStack: e.stack }) }`. DynamoDB items are unmarshalled via `@aws-sdk/util-dynamodb` before returning.
- **Gap**: None for response format. The consistent JSON structure is ideal for agent parsing. However, error responses include `errorStack` which should be removed for security.
- **Recommendation**: Remove `errorStack` from error responses in all three Lambda functions. Add response envelope versioning (e.g., `{ version: "1.0", ... }`) to support future schema evolution.

#### APP-Q6: Workflow Logic
- **Score**: 1/4 ❌
- **Finding**: The checkout workflow in `src/basket/index.js` is hardcoded as a sequential function (`checkoutBasket`): (1) `getBasket` → (2) `prepareOrderPayload` → (3) `publishCheckoutBasketEvent` → (4) `deleteBasket`. There is no dedicated orchestration service, no retry logic, and no compensation if a step fails. If step 3 succeeds but step 4 fails, the basket is not deleted but an order event was already published.
- **Gap**: Hardcoded workflow with no error handling between steps, no rollback capability, and no visibility into workflow state. Agent workflows (return processing, restocking) will require multi-step orchestration with error handling.
- **Recommendation**: Move the checkout workflow to AWS Step Functions. Design the agent orchestration workflow (order inquiry → eligibility check → return process → restocking trigger) as a Step Functions state machine with error handling, retries, and human approval steps.

#### APP-Q7: Idempotency
- **Score**: 1/4 ❌
- **Finding**: No idempotency keys, deduplication tokens, or idempotent write patterns found. Product creation in `src/product/index.js` generates a `uuidv4()` for each request (line: `const productId = uuidv4()`), which means duplicate POST requests create duplicate products. SQS `OrderQueue` in `lib/queue.ts` has no deduplication configuration. Basket creation uses `PutItemCommand` which overwrites existing items without checking.
- **Gap**: No idempotency protection. An agent retrying a failed return or restocking request could create duplicate orders, double-process returns, or duplicate restocking events.
- **Recommendation**: Add idempotency keys to all write APIs. Use `@middy/core` with `@middy/idempotency` middleware, or implement DynamoDB conditional writes. For SQS, switch to a FIFO queue with `MessageDeduplicationId` for the order queue.

#### APP-Q8: Rate Limiting & Throttling
- **Score**: 1/4 ❌
- **Finding**: No API Gateway throttling configuration in `lib/apigateway.ts`. No `deployOptions` with throttle settings, no usage plans, no API keys, no WAF rate rules. The `LambdaRestApi` is created with default settings only: `{ restApiName: 'Product Service', handler: productMicroservice, proxy: false }`.
- **Gap**: No rate limiting. An agent could make unlimited API calls, potentially causing Lambda throttling, DynamoDB hot partition issues, and unexpected costs.
- **Recommendation**: Add `deployOptions: { throttlingBurstLimit: 100, throttlingRateLimit: 50 }` to each API Gateway. Create usage plans with API keys for the agent service. Consider adding AWS WAF with rate-based rules for DDoS protection.

#### APP-Q9: Resilience Patterns
- **Score**: 1/4 ❌
- **Finding**: No circuit breakers, retry logic, or explicit timeout configurations in any Lambda function source code. AWS SDK v3 has default retry behavior (3 retries) but no explicit configuration. No resilience libraries (Resilience4j, Polly, or equivalent) in `package.json` dependencies. Lambda functions have no configured timeout in `lib/microservice.ts` (uses default 3-second Lambda timeout).
- **Gap**: No application-level resilience patterns. Agent workflows spanning multiple services will amplify failure cascading without circuit breakers and retries.
- **Recommendation**: Add explicit Lambda timeout configuration (e.g., 30 seconds) in `lib/microservice.ts`. Implement retry with exponential backoff for DynamoDB calls. Add circuit breaker patterns using `cockatiel` or custom middleware for the agent-facing API layer.

#### APP-Q10: Long-running Processes
- **Score**: 2/4 🟠
- **Finding**: The checkout operation (the longest operation) IS handled asynchronously: the basket service publishes an EventBridge event and returns immediately. The ordering service processes asynchronously via SQS. However, there is no status polling endpoint — the client has no way to check if the order was successfully created after checkout. No callback mechanism exists.
- **Gap**: Async processing exists but no status tracking. An agent that triggers a return or restocking needs to poll for completion status or receive a callback.
- **Recommendation**: Add a status endpoint (e.g., `GET /order/status/{orderId}`) that the agent can poll. Alternatively, implement WebSocket notifications via API Gateway WebSocket API so the agent receives real-time completion events.

#### APP-Q11: API Versioning
- **Score**: 1/4 ❌
- **Finding**: No API versioning found. URLs are unversioned (`/product`, `/basket`, `/order`). No `Accept-Version` headers, no versioning annotations, no changelog. API Gateway stage is the default `prod` stage with no version management.
- **Gap**: No API versioning. Changes to API schemas will break agent tool definitions. Agent tool contracts must be stable and versioned.
- **Recommendation**: Implement URL path versioning (e.g., `/v1/product`, `/v1/basket`, `/v1/order`) in `lib/apigateway.ts`. This ensures agent tools built against v1 continue working when v2 is introduced.

#### APP-Q12: Service Discovery & Mesh
- **Score**: 2/4 🟠
- **Finding**: Services communicate via EventBridge with event bus name `SwnEventBus` passed as environment variable in `lib/microservice.ts`. DynamoDB table names are passed via CDK environment variables (`DYNAMODB_TABLE_NAME`). There is no service discovery mechanism (no AWS Cloud Map, no App Mesh, no Consul). API Gateway URLs are not dynamically discoverable.
- **Gap**: No service discovery. The agent needs to discover API Gateway endpoints dynamically rather than hardcoding URLs. EventBridge event bus name is hardcoded in environment variables.
- **Recommendation**: Use AWS Cloud Map for service discovery or maintain an API catalog (e.g., a DynamoDB table listing all service endpoints). At minimum, use SSM Parameter Store to store API Gateway URLs so the agent can discover them at runtime.

#### APP-Q13: AI/Agent Frameworks
- **Score**: 1/4 ❌
- **Finding**: No AI or agent framework dependencies found in any `package.json`. No imports of `@aws-sdk/client-bedrock-runtime`, `langchain`, `@langchain/core`, `openai`, `@anthropic-ai/sdk`, `strands-agents`, or any MCP SDK. No Bedrock, SageMaker, or AI service references in CDK stack. No agent tool definitions, prompt templates, or LLM integration code.
- **Gap**: Complete absence of AI/agent capabilities. This is a foundational gap for the agentic use case — the entire agent layer needs to be built from scratch.
- **Recommendation**: Add an agent orchestrator as a new Lambda function (or ECS service for long-running agents) using the Strands Agents SDK or Amazon Bedrock Agents. Define the three existing microservices as agent tools. Start with a simple tool-use agent that can query order status via the Order API.

### Data Foundations

#### DATA-Q1: Vector Database Presence
- **Score**: 1/4 ❌
- **Finding**: No vector database found in the CDK stack or any configuration file. No OpenSearch, pgvector, Pinecone, Weaviate, Chroma, or Bedrock Knowledge Base references. No vector search imports or k-NN configurations.
- **Gap**: No vector store for semantic search. The agent cannot perform natural language queries over product catalogs, order history, or return policies without a vector database.
- **Recommendation**: Add Amazon OpenSearch Serverless with vector search or configure a Bedrock Knowledge Base. For the e-commerce agent use case, index product descriptions, return policies, and FAQ content as embeddings for RAG-based customer support.

#### DATA-Q2: Vector DB Management
- **Score**: 1/4 ❌
- **Finding**: No vector database exists (see DATA-Q1). No managed or self-hosted vector DB infrastructure.
- **Gap**: No vector DB of any kind to evaluate management posture.
- **Recommendation**: When implementing the vector store (DATA-Q1), use a fully managed option — Amazon OpenSearch Serverless or Bedrock Knowledge Base — to avoid operational overhead.

#### DATA-Q3: RAG Implementation
- **Score**: 1/4 ❌
- **Finding**: No RAG pipeline components found. No embedding model calls (Bedrock Titan, OpenAI ada), no document chunking or splitting code, no similarity_search or knn_search patterns, no Bedrock Knowledge Base integration. No document processing or knowledge ingestion pipeline.
- **Gap**: No RAG capability. The agent cannot ground its responses in actual product data, order history, or return policy documents without a RAG pipeline.
- **Recommendation**: Implement a RAG pipeline: (1) Create an S3 bucket for knowledge documents (return policies, product guides, FAQs), (2) Use Bedrock Knowledge Base with Titan embeddings to index documents, (3) Integrate retrieval into the agent orchestrator to ground responses in company data.

#### DATA-Q4: Data Source Sprawl
- **Score**: 3/4 🟡
- **Finding**: Three DynamoDB tables (`product`, `basket`, `order`) each accessed by a dedicated Lambda function. The architecture is clean — each service owns exactly one table. The ordering service receives checkout data via EventBridge events (not by querying other services' tables). No external API dependencies.
- **Gap**: Three distinct data sources with no unified access layer. While the separation is clean, the agent will need to query across all three to fulfill requests like "What items are in this customer's basket and what's the status of their last order?"
- **Recommendation**: Build a thin unified data access API (or use the existing API Gateways as the unified layer for the agent). The agent should access data through the service APIs rather than directly querying DynamoDB tables.

#### DATA-Q5: Data Access Pattern
- **Score**: 2/4 🟠
- **Finding**: Each Lambda function directly accesses its own DynamoDB table via `ddbClient.js` using `DynamoDBClient` from `@aws-sdk/client-dynamodb`. Data access is in the same Lambda handler that processes API requests — there is no repository pattern or data access layer abstraction. The ordering service does receive basket data via EventBridge events (not via direct DB access), which is positive.
- **Gap**: Direct DB access in handlers with no abstraction layer. When adding agent capabilities, there's a risk of the agent code also bypassing APIs and accessing DynamoDB directly.
- **Recommendation**: Refactor each service to have a dedicated data access module (repository pattern) that abstracts DynamoDB operations. Ensure the agent accesses data exclusively through the REST APIs, not through direct DynamoDB calls.

#### DATA-Q6: Unstructured Data
- **Score**: 1/4 ❌
- **Finding**: No S3 buckets, no document parsing libraries (Textract, Tika, pdf-parse), no image or document processing. Product table has an `imageFile` field (per CDK comments in `lib/database.ts`) but no actual file storage infrastructure.
- **Gap**: No unstructured data handling. Return policy documents, product images, and customer communication history cannot be processed by the agent.
- **Recommendation**: Add an S3 bucket for product images, return policy PDFs, and other unstructured data. Use Textract for document parsing in the RAG pipeline. Store product images in S3 and reference them from the product DynamoDB table.

#### DATA-Q7: Schema Documentation
- **Score**: 1/4 ❌
- **Finding**: No JSON Schema files, no Avro/Protobuf schemas, no formal schema documentation. DynamoDB table schemas are only documented in CDK code comments in `lib/database.ts`: `// product : PK: id -- name - description - imageFile - price - category`, `// basket : PK: userName -- items (SET-MAP object)`, `// order : PK: userName - SK: orderDate -- totalPrice - firstName - lastName - email - address - paymentMethod - cardInfo`. No migration files exist (DynamoDB is schema-less).
- **Gap**: No formal schema documentation. The agent needs to understand data schemas to generate correct queries and interpret results. The only documentation is CDK code comments.
- **Recommendation**: Create JSON Schema definitions for each DynamoDB table's item structure. Publish these as part of the OpenAPI spec (reuse in request/response models). Add a `schemas/` directory with versioned schema definitions.

#### DATA-Q8: Data Access Layer
- **Score**: 2/4 🟠
- **Finding**: Each microservice has its own `ddbClient.js` module that creates a `DynamoDBClient` instance — this provides a consistent pattern within each service. However, all DynamoDB operations (scan, get, put, update, delete, query) are implemented directly in the handler `index.js` files, not abstracted into a separate data access layer. No shared data access library across services.
- **Gap**: No proper data access layer abstraction. DynamoDB operations are mixed with HTTP request handling logic in the same functions.
- **Recommendation**: Create a repository/DAO module in each service that encapsulates all DynamoDB operations. For example, `src/product/productRepository.js` would export `getProduct`, `createProduct`, `updateProduct`, etc. This separation makes it easier to add caching, logging, and metrics for agent operations.

#### DATA-Q9: Embedding Freshness
- **Score**: 1/4 ❌
- **Finding**: No embeddings exist (see DATA-Q1, DATA-Q3). No embedding refresh mechanism, no scheduled re-indexing, no CDC (Change Data Capture) patterns for keeping embeddings current.
- **Gap**: No embedding freshness mechanism. When RAG is implemented, product catalog and order data changes must be reflected in the vector store.
- **Recommendation**: When implementing the RAG pipeline, use DynamoDB Streams to trigger embedding re-indexing whenever product data changes. For order data, schedule periodic re-indexing. Configure Bedrock Knowledge Base sync schedules if using that approach.

#### DATA-Q10: Database Engine Version & EOL
- **Score**: 4/4 ✅
- **Finding**: All three databases are DynamoDB (defined in `lib/database.ts`). DynamoDB is a fully managed service with no engine version to pin or upgrade. There are no RDS, DocumentDB, ElastiCache, or other versioned database engines in the stack. DynamoDB does not have EOL concerns.
- **Gap**: None. DynamoDB is evergreen — no version management required.
- **Recommendation**: No action needed. If RDS or other versioned databases are added in the future (e.g., for the vector database), ensure engine versions are explicitly pinned in CDK.

#### DATA-Q11: Stored Procedures & Schema Complexity
- **Score**: 4/4 ✅
- **Finding**: DynamoDB has no stored procedures, triggers, or proprietary SQL constructs. All business logic resides in the Lambda function application code (`src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js`). No `.sql` files found in the repository. Data operations use DynamoDB's native API (GetItem, PutItem, Query, Scan, UpdateItem, DeleteItem).
- **Gap**: None. All business logic is in the application layer, which is ideal for agent integration.
- **Recommendation**: No action needed. Maintain this pattern — keep business logic in Lambda functions where the agent can interact with it via APIs.

### Identity, Security & Governance

#### SEC-Q1: Secret Management
- **Score**: 2/4 🟠
- **Finding**: No AWS Secrets Manager, SSM Parameter Store SecureString, or HashiCorp Vault usage found. No hardcoded secrets, passwords, or API keys detected in source code. Environment variables in `lib/microservice.ts` contain non-sensitive configuration: `PRIMARY_KEY`, `DYNAMODB_TABLE_NAME`, `EVENT_SOURCE`, `EVENT_DETAILTYPE`, `EVENT_BUSNAME`. No `.env` files committed.
- **Gap**: No secrets management framework is in place. While no sensitive secrets are currently stored, the agent use case will require managing LLM API keys, Bedrock credentials, and potentially customer authentication tokens — all of which need a secrets management solution.
- **Recommendation**: Add AWS Secrets Manager to the CDK stack for storing agent-related secrets (Bedrock API keys, third-party integrations). Use `aws-cdk-lib/aws-secretsmanager.Secret` and grant Lambda functions read access via IAM.

#### SEC-Q2: IAM Least Privilege
- **Score**: 3/4 🟡
- **Finding**: CDK uses scoped IAM grants: `productTable.grantReadWriteData(productFunction)` in `lib/microservice.ts` (each Lambda gets access only to its own DynamoDB table), `bus.grantPutEventsTo(props.publisherFuntion)` in `lib/eventbus.ts` (only basket Lambda can publish to EventBridge). These are CDK best-practice grants that generate least-privilege IAM policies — no wildcard `Action: "*"` or `Resource: "*"`.
- **Gap**: While CDK grants are scoped, there are no explicit IAM policy boundaries. `grantReadWriteData` grants both read AND write to the entire table — the ordering Lambda only needs read access (it queries orders for the API) and write (for creating orders from SQS). More granular permissions could be applied.
- **Recommendation**: Consider splitting ordering Lambda permissions: grant write for SQS-triggered creates, read-only for API Gateway queries. Add IAM policy boundaries to prevent privilege escalation when adding agent Lambdas.

#### SEC-Q3: Identity Propagation
- **Score**: 1/4 ❌
- **Finding**: No JWT, OAuth2, or Cognito integration found. User identity is passed as a path parameter (`{userName}` in basket and order APIs) or in the request body (checkout payload). No token validation, no identity propagation between services. The `userName` in EventBridge events comes from the unvalidated request body in `src/basket/index.js`: `const checkoutRequest = JSON.parse(event.body)`.
- **Gap**: No authenticated identity propagation. Anyone can query any user's basket (`GET /basket/{userName}`) or orders (`GET /order/{userName}`) by guessing usernames. An agent processing returns needs verified customer identity — not just a username string.
- **Recommendation**: Add Amazon Cognito user pool with JWT authorizer on all API Gateways. Extract authenticated user identity from the JWT `sub` claim instead of relying on path parameters. Propagate the JWT token through EventBridge events for audit.

#### SEC-Q4: Audit Logging
- **Score**: 1/4 ❌
- **Finding**: No CloudTrail configuration in CDK stack. Lambda functions log to CloudWatch via `console.log` and `console.error` statements (found in all three `index.js` files). These are unstructured logs with no audit metadata (no who, what, when, why). No immutable log storage, no log retention policies configured.
- **Gap**: No audit trail. Agent actions (returns, restocking) must be auditable to detect and investigate misuse. Without CloudTrail and structured audit logs, there is no way to trace what the agent did and why.
- **Recommendation**: Enable CloudTrail for API Gateway and DynamoDB data events in CDK. Add structured audit logging middleware to Lambda functions that records: action, actor (user/agent), resource, timestamp, and outcome. Store audit logs in S3 with Object Lock for immutability.

#### SEC-Q5: API Rate Limits
- **Score**: 1/4 ❌
- **Finding**: No API Gateway throttling settings, no usage plans, no API keys, no WAF rate-based rules found in `lib/apigateway.ts` or anywhere in the CDK stack. Default API Gateway account-level throttling (10,000 requests/second) applies but is not explicitly configured.
- **Gap**: No per-client rate limiting. An agent making rapid requests during order status polling or inventory checks could exhaust API capacity or trigger unintended DynamoDB throttling.
- **Recommendation**: Add usage plans with rate limits and quotas per API key in `lib/apigateway.ts`. Assign a dedicated API key to the agent service. Add WAF with rate-based rules on all three API Gateways.

#### SEC-Q6: PII Redaction
- **Score**: 1/4 ❌
- **Finding**: Error responses in all three Lambda functions include full stack traces: `errorStack: e.stack` (found in `src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js`). Request bodies containing PII (firstName, lastName, email, address, cardInfo — per the order schema in `lib/database.ts` comments) are logged in full via `console.log("request:", JSON.stringify(event, undefined, 2))` in all handlers. No PII masking, no log scrubbing, no Macie integration.
- **Gap**: PII exposure in logs and error responses. Order data includes email, address, and card info that will be logged unredacted. Agent interactions will amplify PII exposure in logs.
- **Recommendation**: Remove `errorStack` from all error responses. Add PII redaction middleware that masks email, address, and card information in logs. Use CloudWatch Logs data protection to automatically detect and mask PII patterns.

#### SEC-Q7: Human Approval Workflows
- **Score**: 1/4 ❌
- **Finding**: No human approval workflows found. No Step Functions with waitForTaskToken, no approval Lambda patterns, no manual gates in any workflow. The checkout flow runs autonomously with no human intervention. No CI/CD approval stages exist (no CI/CD pipeline at all).
- **Gap**: No human-in-the-loop safeguards. An agent processing returns or triggering restocking orders operates without any human approval gate. High-risk actions (bulk returns, large restocking orders, deleting products) have no safety net.
- **Recommendation**: Implement a Step Functions state machine with a human approval step (`waitForTaskToken`) for high-risk agent actions: return processing above a dollar threshold, restocking orders above a quantity threshold, and product deletions. Route approval requests to SNS → email/Slack notification.

#### SEC-Q8: Encryption at Rest
- **Score**: 2/4 🟠
- **Finding**: DynamoDB tables in `lib/database.ts` use AWS-managed encryption by default (no explicit `encryption` property, so CDK applies `TableEncryption.DEFAULT` = AWS-owned key). SQS queue in `lib/queue.ts` has no KMS configuration. No explicit KMS key definitions in the entire CDK stack.
- **Gap**: AWS-managed encryption is present by default but no customer-managed KMS keys. This limits key rotation control and cross-account access management. Order data contains sensitive PII (card info, addresses) that warrants customer-managed encryption.
- **Recommendation**: Add customer-managed KMS keys for the order DynamoDB table and SQS queue. Create a `aws_kms.Key` in CDK and pass it to the DynamoDB table's `encryptionKey` property and the SQS queue's `encryptionMasterKey` property.

#### SEC-Q9: API Authentication
- **Score**: 1/4 ❌
- **Finding**: No API Gateway authorizers configured on any endpoint in `lib/apigateway.ts`. No Cognito user pool authorizer, no Lambda authorizer, no API key requirement, no IAM authorization. All 12 API endpoints (5 product, 5 basket, 2 order) are publicly accessible without any authentication.
- **Gap**: All APIs are unauthenticated. Any internet user can create, modify, and delete products; access any user's basket; view any user's orders. This is a critical security vulnerability that must be fixed before exposing these APIs to an agent.
- **Recommendation**: Add a Cognito user pool authorizer to all API Gateway methods. For the agent, use a machine-to-machine OAuth2 client credentials flow. At minimum, add API key authentication as an interim measure.

#### SEC-Q10: Centralized Identity
- **Score**: 1/4 ❌
- **Finding**: No identity provider found. No Amazon Cognito user pool, no Okta, no Auth0, no SAML/OIDC federation. User identity is a plain string (`userName`) passed in path parameters and request bodies without any validation or authentication source.
- **Gap**: No centralized identity management. The agent needs authenticated identity for each customer interaction — it must know who it's serving and that the identity is verified.
- **Recommendation**: Add Amazon Cognito as the centralized identity provider. Create a user pool for customer authentication and a separate app client for the agent service (client credentials flow). Integrate Cognito with all three API Gateways.

### Operations & Observability

#### OPS-Q1: Distributed Tracing
- **Score**: 1/4 ❌
- **Finding**: No X-Ray, OpenTelemetry, Datadog, or any tracing SDK found in Lambda source code or dependencies. No trace context propagation headers (traceparent, X-Amzn-Trace-Id) in code. No tracing configuration in `lib/microservice.ts` (Lambda `tracing` property is not set). Only basic `console.log` statements exist for debugging.
- **Gap**: No distributed tracing. Agent workflows spanning product lookup → basket check → order query → return processing will be invisible — when something fails, there's no way to reconstruct the execution path across services.
- **Recommendation**: Enable X-Ray tracing on all Lambda functions by adding `tracing: lambda.Tracing.ACTIVE` in `lib/microservice.ts`. Add the AWS X-Ray SDK to Lambda dependencies. For agent orchestration, use OpenTelemetry with `gen_ai.*` semantic conventions to trace LLM calls alongside service calls.

#### OPS-Q2: Structured Logging
- **Score**: 1/4 ❌
- **Finding**: All three Lambda functions use `console.log` and `console.error` for logging. Event payloads are logged via `console.log("request:", JSON.stringify(event, undefined, 2))`. No structured JSON logging library (winston, pino, structlog). No correlation IDs, no traceId fields, no request-scoped logging context.
- **Gap**: Unstructured logs with no correlation capability. Cannot correlate logs across the checkout flow (basket → EventBridge → SQS → ordering). Agent interactions will generate logs across multiple services with no way to tie them together.
- **Recommendation**: Replace `console.log` with a structured logging library (e.g., `@aws-lambda-powertools/logger` from AWS Lambda Powertools for TypeScript). Add correlation ID middleware that propagates a unique requestId through EventBridge event detail and SQS message attributes.

#### OPS-Q3: Automated Evals
- **Score**: 1/4 ❌
- **Finding**: No evaluation framework, golden datasets, scoring scripts, or LLM assertion tests found. No RAGAS, no pytest with LLM assertions, no A/B test infrastructure. No AI components exist yet, so no evals are possible.
- **Gap**: No agent evaluation capability. Without automated evals, there's no way to measure agent accuracy for order status inquiries, return eligibility decisions, or restocking recommendations. Agent quality will be unmeasurable.
- **Recommendation**: Before deploying the agent, create golden datasets with expected inputs/outputs: (1) order status inquiry test cases, (2) return eligibility edge cases, (3) restocking trigger scenarios. Use a scoring framework to evaluate agent responses against expected outcomes. Integrate into CI/CD pipeline.

#### OPS-Q4: SLOs
- **Score**: 1/4 ❌
- **Finding**: No SLO definitions found. No CloudWatch alarms, no latency/error rate targets, no error budget tracking, no SLO dashboards configured in CDK. Only default Lambda CloudWatch metrics exist (invocations, errors, duration) but no alarms are defined on them.
- **Gap**: No service-level objectives. Without SLOs, there are no defined acceptable latency or error rate thresholds for the agent to meet when making API calls. Agent performance is unmonitored.
- **Recommendation**: Define SLOs for each service: p99 latency < 500ms, error rate < 1%, availability > 99.9%. Create CloudWatch alarms for these thresholds. For the agent, add SLOs for task success rate (> 95%), response latency (< 5s), and hallucination rate (< 5%).

#### OPS-Q5: Rollback Capability
- **Score**: 1/4 ❌
- **Finding**: No deployment strategy or rollback mechanism found. No CodeDeploy, no blue/green configuration, no canary deployments, no Lambda versioning or aliases. Deployment is manual `cdk deploy` which performs in-place CloudFormation updates. No feature flags for gradual rollout.
- **Gap**: No rollback capability. A bad agent deployment (incorrect tool definitions, broken prompts, faulty business logic) would affect all users immediately with no way to quickly revert.
- **Recommendation**: Configure Lambda aliases with weighted traffic shifting in CDK. Use CodeDeploy with automatic rollback triggers (e.g., rollback if error rate exceeds 5%). Add feature flags for gradual agent rollout.

#### OPS-Q6: LLM Cost Tracking
- **Score**: 1/4 ❌
- **Finding**: No LLM usage in the current codebase, so no cost tracking exists. No token counting, no per-request attribution, no CloudWatch custom metrics for AI usage. No observability data retention policies.
- **Gap**: No LLM cost tracking infrastructure. When the agent starts using Bedrock, each conversation could cost $0.01-$1.00+ depending on model and token usage. Without tracking, costs will be unpredictable and unattributable.
- **Recommendation**: When implementing the agent, add LLM cost tracking from day one: log token counts (input/output) per request, tag requests by customer/workflow type, publish CloudWatch custom metrics for token usage and cost. Set billing alarms for unexpected cost spikes.

#### OPS-Q7: Business Metrics
- **Score**: 1/4 ❌
- **Finding**: No custom CloudWatch metrics published from any Lambda function. No business outcome tracking (order conversion rate, basket abandonment rate, checkout success rate). Only default Lambda infrastructure metrics are available.
- **Gap**: No business metrics. Cannot measure agent effectiveness — order inquiry resolution rate, return processing accuracy, restocking decision quality. Without business metrics, the agent's ROI is unmeasurable.
- **Recommendation**: Add `cloudwatch.putMetricData` calls to Lambda functions for business events: orders created, checkouts completed, product queries. For the agent, track: inquiries resolved, returns processed, restocking orders triggered, customer satisfaction scores.

#### OPS-Q8: Anomaly Detection
- **Score**: 1/4 ❌
- **Finding**: No CloudWatch anomaly detection, no error rate alarms, no latency alarms, no PagerDuty/OpsGenie integration. No composite alarms. No behavioral baseline monitoring.
- **Gap**: No anomaly detection. An agent in a reasoning loop (calling the same API repeatedly), or a surge in return processing (potential fraud), would go undetected until financial damage occurs.
- **Recommendation**: Enable CloudWatch anomaly detection on Lambda invocation counts, error rates, and duration. Create composite alarms that detect agent-specific anomalies: unusual tool call patterns, sudden spikes in return requests, or order query volume exceeding 3x baseline.

#### OPS-Q9: Deployment Strategy
- **Score**: 1/4 ❌
- **Finding**: Manual `cdk deploy` as documented in README. No blue/green, canary, or traffic shifting. No CodeDeploy configuration. No Lambda aliases or versioning for gradual rollout. `cdk deploy` performs immediate CloudFormation stack update.
- **Gap**: Direct-to-production deployment with no safety net. Agent updates (prompt changes, tool definition changes, business logic changes) would instantly affect all users.
- **Recommendation**: Implement canary deployments using Lambda aliases with CodeDeploy. Configure 10% traffic to the new version for 10 minutes, then gradual rollout. Add automatic rollback if error rate exceeds threshold.

#### OPS-Q10: Integration Testing
- **Score**: 1/4 ❌
- **Finding**: A test file exists at `test/aws-microservices.test.ts` but all test code is commented out — only an empty test shell remains: `test('SQS Queue Created', () => { })`. Jest is configured (`jest.config.js`) but no actual tests run. No integration test suites, no API test collections (Postman/Newman), no contract tests.
- **Gap**: No working tests of any kind. Cannot validate that API endpoints work correctly, that the checkout flow creates orders, or that EventBridge events are properly routed. Agent tool integration cannot be tested.
- **Recommendation**: Uncomment and complete the CDK test in `test/aws-microservices.test.ts`. Add integration tests that deploy to a test environment and validate: product CRUD operations, basket checkout flow end-to-end, order creation from EventBridge. Add API contract tests for each service.

#### OPS-Q11: Incident Response Automation
- **Score**: 1/4 ❌
- **Finding**: No runbooks (markdown, YAML, or JSON), no SSM Automation documents, no Lambda-based remediation functions, no Step Functions for incident workflows. No self-healing patterns, no auto-restart configurations beyond Lambda's built-in retry on failure.
- **Gap**: No incident response capability. When the agent encounters errors (DynamoDB throttling, EventBridge delivery failures, invalid customer data), there is no automated remediation and no documented response procedures.
- **Recommendation**: Create runbooks for common failure scenarios: DynamoDB throttling (auto-scale or switch billing mode), Lambda errors (investigate and rollback), agent hallucination (disable agent, fall back to manual). Implement SSM Automation documents for automated remediation.

#### OPS-Q12: Observability Governance & Ownership
- **Score**: 1/4 ❌
- **Finding**: No CODEOWNERS file, no team ownership definitions, no SLO ownership model. No observability governance documentation. No platform team tooling, no centralized observability stack configuration. No per-service dashboards or alarms.
- **Gap**: No ownership model for observability. When the agent is deployed, it's unclear who owns agent quality, who monitors agent SLOs, and who responds to agent-related incidents.
- **Recommendation**: Create a CODEOWNERS file assigning team ownership per service. Define an observability ownership model: platform team owns infrastructure monitoring, product team owns agent quality metrics (task success rate, hallucination rate). Establish agent-specific SLOs with named owners.

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

**Parallel Track 1**: Move to Modern DevOps — CI/CD pipeline, observability, deployment strategy (can start immediately)
**Parallel Track 2**: Move to AI — Agent framework integration, vector database, RAG pipeline, eval framework (can start immediately)
**Sequential Dependencies**: None — both tracks can execute in parallel. However, Move to Modern DevOps should establish CI/CD and observability foundations early (Phase 1), as Move to AI deployments will benefit from the CI/CD pipeline and tracing infrastructure.

### Move to Modern DevOps

- **Priority**: High
- **Goal Alignment**: High
- **Trigger Criteria Met**:
  - INF-Q6: Score 1/4 — No CI/CD pipeline; deployment is manual `cdk deploy`
  - OPS-Q9: Score 1/4 — No deployment strategy; direct-to-production via `cdk deploy`
  - OPS-Q10: Score 1/4 — All tests commented out in `test/aws-microservices.test.ts`; no integration tests
  - OPS-Q1: Score 1/4 — No distributed tracing; no X-Ray or OpenTelemetry
- **Current State**: Manual deployment via `cdk deploy`, no CI/CD pipeline, no tests, no tracing, no observability. Development velocity is limited to manual processes with no safety gates.
- **Target State**: Fully automated CI/CD pipeline with test → build → deploy stages, canary deployments with automatic rollback, distributed tracing across all services, structured logging with correlation IDs, and CloudWatch alarms on SLOs.
- **Key Activities**:
  1. Create GitHub Actions CI/CD pipeline with lint → test → CDK synth → CDK deploy stages
  2. Enable X-Ray tracing on all Lambda functions and API Gateways
  3. Add structured logging with `@aws-lambda-powertools/logger`
  4. Implement Lambda alias-based canary deployments with CodeDeploy
  5. Uncomment and complete CDK tests; add integration test suite
  6. Define SLOs and create CloudWatch alarms for all services
- **Dependencies**: None — can start immediately
- **Estimated Effort**: High (significant foundational work across CI/CD, observability, and testing)
- **Roadmap Phase Alignment**: Phase 1 (CI/CD, tracing, logging), Phase 2 (canary deployments, SLOs, integration tests)
- **Relevant Learning Materials**: Module 6 — Move to Modern DevOps

### Move to AI

- **Priority**: High
- **Goal Alignment**: High
- **Trigger Criteria Met**:
  - APP-Q13: Score 1/4 — No AI/agent frameworks in any dependency manifest
  - DATA-Q1: Score 1/4 — No vector database for semantic search
  - DATA-Q3: Score 1/4 — No RAG pipeline for grounding agent responses
  - OPS-Q3: Score 1/4 — No automated evaluation framework for agent quality
  - OPS-Q6: Score 1/4 — No LLM cost tracking infrastructure
- **Current State**: No AI or agent capabilities exist. No vector database, no embeddings, no RAG pipeline, no agent framework, no eval infrastructure. The application is purely a CRUD microservices platform.
- **Target State**: AI agent that handles customer order status inquiries, processes returns, and manages inventory restocking using the existing microservices as tools. The agent uses RAG with a vector database for knowledge retrieval, has automated evals measuring accuracy, and tracks LLM costs per request.
- **Key Activities**:
  1. Add Amazon Bedrock Agent or Strands Agents SDK as the agent orchestrator
  2. Define Product, Basket, and Order APIs as agent tools with OpenAPI specs
  3. Set up Amazon OpenSearch Serverless or Bedrock Knowledge Base for vector storage
  4. Implement RAG pipeline: S3 → embeddings → vector store → retrieval
  5. Create golden dataset and automated eval pipeline for agent accuracy
  6. Add LLM cost tracking with per-request token counting and CloudWatch metrics
  7. Implement human approval workflow via Step Functions for return processing
- **Dependencies**: Requires API documentation (APP-Q2) to define agent tools. Benefits from CI/CD (Move to Modern DevOps) for safe agent deployment.
- **Estimated Effort**: High (full agent stack build-out including vector DB, RAG, evals, and safety mechanisms)
- **Roadmap Phase Alignment**: Phase 1 (OpenAPI specs, tool definitions), Phase 2 (agent framework, vector DB, RAG), Phase 3 (evals, cost tracking, human approval)
- **Relevant Learning Materials**: Module 7 — Move to AI

---

## Quick Agent Wins

Even before completing the full modernization roadmap, these agent opportunities are available based on your current architecture:

1. **Order Status Inquiry Agent via JSON APIs** — Your three microservices already return structured JSON (APP-Q5 score 4/4) with consistent `{ message, body }` format. An agent can invoke `GET /order/{userName}` and `GET /product/{id}` today to answer customer questions like "What's the status of my last order?" and "What products are available in this category?"
   - **Leverages**: Structured JSON API responses from all three services (`src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js`)
   - **Effort**: Low — requires only writing agent tool definitions against existing API endpoints
   - **Value**: Immediate customer-facing capability for order status inquiries without any infrastructure changes

2. **Knowledge Agent from Existing Documentation** — The repository includes a detailed README with architecture description, API endpoint documentation, and operational guides. Combined with the CDK code comments documenting DynamoDB schemas, this content can be indexed for a RAG-based knowledge agent.
   - **Leverages**: `README.md` (architecture docs, API URLs, deployment guide), CDK code comments in `lib/database.ts` (schema definitions)
   - **Effort**: Medium — requires setting up S3 bucket and Bedrock Knowledge Base for document indexing
   - **Value**: Internal developer support agent that answers questions about the e-commerce platform architecture, API contracts, and deployment procedures

3. **Basket Operations Agent** — The basket service supports full CRUD operations plus a checkout flow. An agent could manage the entire customer basket lifecycle: "Add this product to my cart", "What's in my basket?", "Proceed to checkout."
   - **Leverages**: Basket API endpoints (`POST /basket`, `GET /basket/{userName}`, `POST /basket/checkout`, `DELETE /basket/{userName}`)
   - **Effort**: Low — tool definitions against existing basket API endpoints
   - **Value**: Enables conversational commerce — customers interact with the basket through natural language instead of UI clicks

> These opportunities can be pursued in parallel with the modernization roadmap.
> They demonstrate agent value early while foundations are being built.

---

## Readiness Roadmap

### Phase 1 — Agent Quick Wins (Days 1–30)

Low-effort, high-impact items that establish critical foundations for agent integration:

1. **Generate OpenAPI 3.0 specs** for all three API Gateways (Product, Basket, Order). Export from API Gateway or create manually based on route definitions in `lib/apigateway.ts`. This unblocks agent tool definition.
2. **Create CI/CD pipeline** — Add a GitHub Actions workflow with stages: lint → test → `cdk synth` → `cdk diff` → `cdk deploy`. Start with a single environment (staging). This enables safe iterative development.
3. **Enable X-Ray tracing** — Add `tracing: lambda.Tracing.ACTIVE` to all Lambda functions in `lib/microservice.ts`. One-line change per function with immediate observability gains.
4. **Add structured logging** — Replace `console.log` with `@aws-lambda-powertools/logger` in all Lambda functions. Add correlation ID propagation through EventBridge and SQS.
5. **Upgrade Lambda runtime** — Change `Runtime.NODEJS_14_X` to `Runtime.NODEJS_20_X` in `lib/microservice.ts`. EOL runtime is a security risk.
6. **Remove stack traces from error responses** — Remove `errorStack: e.stack` from all three Lambda handlers to prevent information leakage.

### Phase 2 — Agent Foundations (Months 1–3)

Structural improvements that establish the agent platform:

1. **Add API Gateway authentication** — Create an Amazon Cognito user pool and add JWT authorizer to all API Gateway endpoints. Create a machine-to-machine app client for the agent service. This is a prerequisite for safe agent deployment.
2. **Implement agent orchestrator** — Add Amazon Bedrock Agent or Strands Agents SDK as a new Lambda function. Define the three existing microservices as tools using the OpenAPI specs from Phase 1. Start with read-only operations (order status inquiry, product search).
3. **Set up vector database** — Add Amazon OpenSearch Serverless collection or Bedrock Knowledge Base in CDK. Index product catalog data and return policy documents. Enable RAG for the agent.
4. **Add Step Functions workflow orchestration** — Replace the hardcoded checkout flow with a Step Functions state machine. Design the return processing workflow with a human approval step (`waitForTaskToken`) for high-value returns.
5. **Implement API throttling and rate limiting** — Add `deployOptions` with throttling to each API Gateway. Create usage plans with dedicated API keys for the agent service.
6. **Add idempotency to write APIs** — Implement idempotency keys for product creation, basket operations, and order processing using DynamoDB conditional writes or `@middy/idempotency`.
7. **Build integration test suite** — Uncomment and expand tests in `test/aws-microservices.test.ts`. Add end-to-end tests for checkout flow and agent tool invocations.

### Phase 3 — Agent Scale & Optimization (Months 3–6)

Capabilities that enable production-grade agent operations:

1. **Implement automated agent evals** — Create golden datasets for order inquiries, return processing, and restocking decisions. Build an eval pipeline that scores agent accuracy, runs in CI/CD, and blocks deployments that degrade quality below thresholds.
2. **Add LLM cost tracking** — Implement per-request token counting with customer/workflow attribution. Publish CloudWatch custom metrics for LLM costs. Set billing alarms for cost anomalies.
3. **Implement canary deployments** — Configure Lambda aliases with CodeDeploy for gradual rollout. Set automatic rollback triggers on error rate and latency thresholds. Critical for safe agent prompt and logic updates.
4. **Add anomaly detection** — Enable CloudWatch anomaly detection on Lambda metrics. Create composite alarms for agent-specific anomalies (reasoning loops, excessive tool calls, return processing spikes).
5. **Implement RAG embedding freshness** — Add DynamoDB Streams on the product table to trigger automatic re-indexing when product data changes. Configure Bedrock Knowledge Base sync schedules for policy documents.
6. **Add PII redaction** — Implement CloudWatch Logs data protection. Add PII masking middleware to Lambda functions. Ensure agent conversation logs do not contain customer PII.
7. **Define SLOs and ownership model** — Create SLOs for each service and for the agent: task success rate > 95%, p99 latency < 5s, hallucination rate < 5%. Create a CODEOWNERS file and assign observability ownership per service.

---

## Recommended Self-Paced Learning Materials

The following learning resources are selected based on the gaps identified in this assessment — specifically targeting the two triggered pathways (Move to Modern DevOps and Move to AI) and the serverless architecture foundation.

**Module 2: Move to Cloud Native (Containers and Serverless):**
- Cloud Design Patterns, Architectures, and Implementations — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html
  - Essential reference for async messaging patterns (Event Sourcing, Saga), resilience patterns (Circuit Breaker, Retry with Backoff), and API routing patterns used in your EventBridge + SQS architecture
- Architecting Serverless Applications — https://skillbuilder.aws/learn/MRWENY7FSX/architecting-serverless-applications/QVFY2JHVEH
  - Directly relevant to optimizing your Lambda + API Gateway + DynamoDB architecture for agent workloads
- Amazon API Gateway for Serverless Applications — https://skillbuilder.aws/learn/GQA6FHWPJD/amazon-api-gateway-for-serverless-applications/JVRZ3PSW4H
  - Covers throttling, authorization, and request validation — all critical gaps in your API Gateway configuration
- Amazon DynamoDB for Serverless Architecture — https://skillbuilder.aws/learn/SY1Y83VKTB/amazon-dynamodb-for-serverless-architectures/K9NM3PHH3S
  - Relevant for optimizing DynamoDB access patterns, streams for CDC, and capacity management for agent workloads

**Module 6: Move to Modern DevOps:**
- AWS Modernization Pathways: Move to Modern DevOps — https://skillbuilder.aws/learning-plan/1FGEQKGPQD/aws-modernization-pathways-move-to-modern-devops-includes-labs/MNQZ2KPVCK
  - Comprehensive learning plan covering CI/CD, IaC, and observability — all priority gaps
- Getting Started with DevOps on AWS — https://skillbuilder.aws/learn/R4B13K95YQ/getting-started-with-devops-on-aws/38NHHYRV1R
  - Foundation for establishing your CI/CD pipeline and deployment automation
- Create a CI/CD Pipeline to Deploy Your App to AWS Fargate (ECS) — https://skillbuilder.aws/learn/H61B17Z8R7/create-a-cicd-pipeline-to-deploy-your-app-to-aws-fargate/T66BGGGHV5
  - Hands-on lab for CI/CD pipeline creation patterns applicable to your CDK deployment workflow
- Advanced Testing Practices Using AWS DevOps Tools — https://skillbuilder.aws/learn/1YC7UXUWBR/advanced-testing-practices-using-aws-devops-tools/A32U6G7NEQ
  - Covers integration testing and test automation — critical for agent quality assurance
- AWS Developer: CI/CD Automation — https://skillbuilder.aws/learn/C1KF8ZJ1D8/aws-developer--cicd-automation/KY1E1JS9FA
  - End-to-end CI/CD automation including canary deployments and rollback strategies

**Module 7: Move to AI:**
- AWS Modernization Pathways: Move to AI — https://skillbuilder.aws/learning-plan/VDFEE4ACCV/aws-modernization-pathways-move-to-ai-pathways-includes-labs/P3DAWPTN63
  - Comprehensive learning plan for adding AI capabilities to existing applications
- Amazon Bedrock Getting Started — https://skillbuilder.aws/learn/63KTRM86DQ/amazon-bedrock-getting-started/SC2Y3HMAUE
  - Foundation for integrating Bedrock as the LLM backend for your agent
- Planning a Generative AI Project — https://skillbuilder.aws/learn/HU1FQRGDDZ/planning-a-generative-ai-project/SYR3SCPSHC
  - Helps scope and plan the agent implementation for order management
- Essentials for Prompt Engineering — https://skillbuilder.aws/learn/XBNAVKA88J/essentials-of-prompt-engineering/9T9Q45EDTV
  - Critical for designing effective agent prompts for order status, returns, and restocking workflows
- Build and Evaluate Retrieval Augmented Generation (RAG) Applications using Knowledge Bases for Amazon Bedrock (Lab) — https://skillbuilder.aws/learn/JRGWCFYT67/lab--build-and-evaluate-retrieval-augmented-generation-rag-applications-using-knowledge-bases-for-amazon-bedrock/A4MN58JB7A
  - Hands-on lab directly applicable to building your RAG pipeline for product and policy knowledge
- Introduction to Agentic AI on AWS — https://skillbuilder.aws/learn/DNBD5MT8ZD/introduction-to-agentic-ai-on-aws/WAKAFK6UFY
  - Covers agentic patterns (tool use, multi-step reasoning) directly relevant to your use case
- Creating an AWS DevOps AI Agent with the Strands Agents SDK (Lab) — https://skillbuilder.aws/learn/AH1GD8AJY3/lab--creating-an-aws-devops-ai-agent-with-the-strands-agents-sdk/A9SKJNMPJ2
  - Hands-on lab for building agents with the Strands SDK — applicable to building your order management agent
- AWS PartnerCast: Deep Dive: Building Observable AI Agents with Strands, Amazon Bedrock Agent Core & SageMaker MLflow — https://skillbuilder.aws/learn/1EN76TZBB6/aws-partnercast--deep-dive-building-observable-ai-agents-with-strands-amazon-bedrock-agent-core--sagemaker-mlflow--technical/CX2K6XAT84
  - Covers agent observability including tracing and evaluation — critical for production agent monitoring

---

## Appendix: Evidence Index

| # | File | Key Evidence |
|---|------|-------------|
| 1 | `lib/aws-microservices-stack.ts` | CDK stack orchestration — reveals 5 construct dependencies: Database → Microservices → ApiGateway, Queue, EventBus |
| 2 | `lib/microservice.ts` | Lambda function definitions — Runtime.NODEJS_14_X (EOL), NodejsFunction construct, environment variables, grantReadWriteData IAM grants |
| 3 | `lib/database.ts` | DynamoDB table definitions — 3 tables (product, basket, order), PAY_PER_REQUEST billing, RemovalPolicy.DESTROY, schema in comments only |
| 4 | `lib/apigateway.ts` | API Gateway configuration — 3 LambdaRestApi instances, explicit resource/method definitions, no throttling/auth/validation |
| 5 | `lib/eventbus.ts` | EventBridge configuration — SwnEventBus, CheckoutBasketRule, SQS target, grantPutEventsTo IAM grant |
| 6 | `lib/queue.ts` | SQS configuration — OrderQueue with 30s visibility timeout, batchSize: 1, no DLQ, no encryption |
| 7 | `src/product/index.js` | Product Lambda handler — CRUD operations, uuidv4 for IDs, no auth, errorStack in responses, console.log logging |
| 8 | `src/basket/index.js` | Basket Lambda handler — CRUD + checkout flow, EventBridge publish, hardcoded workflow logic, no idempotency |
| 9 | `src/ordering/index.js` | Ordering Lambda handler — SQS and EventBridge invocation paths, API Gateway queries, order creation from events |
| 10 | `src/product/ddbClient.js` | DynamoDB client — simple DynamoDBClient instantiation, no retry config, no custom settings |
| 11 | `src/basket/eventBridgeClient.js` | EventBridge client — simple EventBridgeClient instantiation, no custom configuration |
| 12 | `src/product/package.json` | Product dependencies — @aws-sdk/client-dynamodb@^3.55.0, @aws-sdk/util-dynamodb@^3.55.0, no agent/AI libraries |
| 13 | `src/basket/package.json` | Basket dependencies — adds @aws-sdk/client-eventbridge@^3.58.0, no agent/AI libraries |
| 14 | `src/ordering/package.json` | Ordering dependencies — @aws-sdk/client-dynamodb@^3.58.0 only, no agent/AI libraries |
| 15 | `package.json` | Root CDK dependencies — aws-cdk-lib@2.17.0, TypeScript 3.9.7, jest for testing |
| 16 | `test/aws-microservices.test.ts` | Test file — all tests commented out, only empty test shell remains, jest configured but no tests run |
| 17 | `cdk.json` | CDK configuration — feature flags, no custom context for environments or stages |
| 18 | `README.md` | Documentation — architecture description, API endpoint examples, deployment via `cdk deploy`, no OpenAPI specs referenced |
| 19 | `tsconfig.json` | TypeScript config — ES2018 target, strict mode enabled, standard CDK configuration |
| 20 | `src/basket/checkoutbasketevents.json` | Sample EventBridge events — shows event structure for CheckoutBasket, useful for understanding inter-service contract |
