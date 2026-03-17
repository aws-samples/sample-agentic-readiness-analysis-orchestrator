# Agentic Readiness Assessment Report
**Target**: ./services/books-api
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

This Books API is a well-architected serverless application built on AWS Lambda, API Gateway, and DynamoDB with a robust CI/CD pipeline — providing an excellent foundation for agent tool integration. The clean JSON API surface, fully managed infrastructure, and mature deployment pipeline (with linear deployments, pre-traffic hooks, and automated rollback) mean that an AI agent for order status inquiries, returns processing, and inventory management can immediately leverage this service as a catalog lookup tool. However, critical gaps block agentic use-case enablement: there is no OpenAPI specification for agent tool discovery, no AI/agent framework integration, no vector database or RAG pipeline for semantic search, and no observability infrastructure for monitoring agent behavior. Addressing these gaps — starting with API documentation and agent framework adoption — is the fastest path to enabling the target agentic use case.

### Overall Score: 2.0 / 4.0

| Category | Score | Status |
|----------|-------|--------|
| Infrastructure & Platform | 2.6 / 4.0 | 🟡 |
| Application Architecture | 1.8 / 4.0 | 🟠 |
| Data Foundations | 1.9 / 4.0 | 🟠 |
| Identity, Security & Governance | 1.9 / 4.0 | 🟠 |
| Operations & Observability | 1.7 / 4.0 | 🟠 |

---

## Top Priorities (Critical Gaps)

**1. APP-Q2 — API Documentation (Score: 1/4)** ❌
An AI agent needs machine-readable API specifications to discover and invoke tools autonomously. This Books API has no OpenAPI/Swagger specification — meaning an agent cannot programmatically learn what endpoints exist, what parameters they accept, or what responses to expect. Without this, the agent cannot be configured to perform catalog lookups for order status inquiries or inventory queries.
→ **First step**: Generate an OpenAPI 3.0 specification from the existing `template.yml` API Gateway definition and Lambda handler schemas. Use SAM's built-in OpenAPI support or manually author `openapi.yaml` to document `/books` GET and POST endpoints.

**2. APP-Q13 — AI/Agent Frameworks (Score: 1/4)** ❌
No AI or agent framework dependencies exist in the codebase. There is no Bedrock SDK, LangChain, Strands Agents, or any agent orchestration library. The agent for order status, returns, and inventory management needs a framework to coordinate tool calls to this API and other services.
→ **First step**: Add `@aws-sdk/client-bedrock-runtime` or `strands-agents` to a new agent service. Use the Books API as the first tool, wrapping the `/books` endpoints as agent-callable functions.

**3. DATA-Q1 — Vector Database Presence (Score: 1/4)** ❌
No vector database is configured. For the target agentic use case — handling order inquiries and inventory restocking — semantic search over product catalogs, order histories, and return policies requires vector embeddings. Without a vector store, the agent cannot perform natural-language queries against the book catalog beyond exact-match DynamoDB lookups.
→ **First step**: Provision Amazon OpenSearch Service with k-NN plugin or configure Amazon Bedrock Knowledge Bases backed by the existing DynamoDB book data.

**4. DATA-Q3 — RAG Implementation (Score: 1/4)** ❌
No Retrieval-Augmented Generation pipeline exists. An agent answering questions about order status, return policies, or inventory levels needs to retrieve contextually relevant information from knowledge bases before generating responses. Without RAG, the agent would rely entirely on its training data and direct API calls with no contextual grounding.
→ **First step**: Implement a RAG pipeline using Amazon Bedrock Knowledge Bases with an S3 data source for product documentation, return policies, and inventory guidelines. Use Titan Embeddings for chunking and indexing.

**5. OPS-Q3 — Automated Evals (Score: 1/4)** ❌
No agent evaluation framework exists. When deploying an agent that processes returns or manages inventory, you need automated evaluation to ensure the agent consistently selects the correct tools, provides accurate order status, and does not hallucinate inventory levels. Without evals, regressions in agent quality go undetected.
→ **First step**: Create golden test datasets with expected agent behaviors for order status inquiries, return processing, and inventory queries. Implement scoring scripts using RAGAS or a custom eval harness that tests tool selection accuracy and response quality.

---

## Detailed Findings

### Infrastructure & Platform

#### INF-Q1: Compute
- **Score**: 4/4 ✅
- **Finding**: All compute is serverless Lambda. `template.yml` defines three `AWS::Serverless::Function` resources: `GetAllBooks` (line ~35), `CreateBook` (line ~62), and `CreateBookPreTraffic` (line ~115). Runtime is `nodejs22.x` with 512 MB memory and 5-second timeout. No EC2 instances, no ECS tasks, no EKS clusters. 100% serverless compute.
- **Gap**: None. Compute is fully managed and auto-scaling.
- **Recommendation**: Maintain serverless-first approach. When adding agent orchestration, consider Lambda for short tool calls and Step Functions for multi-step agent workflows.

#### INF-Q2: Databases
- **Score**: 4/4 ✅
- **Finding**: `template.yml` defines `AWS::Serverless::SimpleTable` resource `BooksTable` — a fully managed DynamoDB table with `PrimaryKey: isbn (String)`, `SSEEnabled: true`, and on-demand capacity (default for SimpleTable). No self-managed databases detected anywhere in the repository. No database software in Dockerfiles (no Dockerfiles exist).
- **Gap**: None. Database is fully managed with automatic failover and scaling.
- **Recommendation**: DynamoDB is well-suited for the book catalog. For the broader e-commerce agent use case (orders, returns, inventory), consider adding Amazon DynamoDB tables for order and inventory data, or Amazon RDS/Aurora if relational queries are needed.

#### INF-Q3: Workflow Orchestration
- **Score**: 1/4 ❌
- **Finding**: No workflow orchestration service found. No `aws_sfn_*` resources, no Step Functions state machine definitions, no Temporal SDK imports, no workflow YAML definitions. Lambda functions handle individual requests directly (API Gateway → Lambda → DynamoDB).
- **Gap**: No dedicated orchestration for multi-step workflows. An agent handling returns processing requires coordination across multiple steps (validate return, update inventory, process refund, notify customer).
- **Recommendation**: Add AWS Step Functions to orchestrate multi-step agent workflows. Define state machines for return processing and inventory restocking that the agent can invoke as tools. Use CDK or SAM to define Step Functions resources in `template.yml`.

#### INF-Q4: Async Messaging
- **Score**: 1/4 ❌
- **Finding**: No SQS, SNS, EventBridge, or any messaging service defined in `template.yml` or the CDK pipeline stack. All communication is synchronous: API Gateway → Lambda → DynamoDB → response. No event-driven patterns detected in source code.
- **Gap**: No async messaging infrastructure. Agent workflows for order processing and inventory restocking benefit from event-driven architecture (e.g., "return requested" event → inventory update → customer notification).
- **Recommendation**: Add Amazon EventBridge for domain events (e.g., `BookCreated`, `OrderReturned`, `InventoryRestocked`) and Amazon SQS for async processing. This aligns with the stated preference for EventBridge and SQS.

#### INF-Q5: Infrastructure as Code
- **Score**: 4/4 ✅
- **Finding**: Excellent IaC coverage. `template.yml` (SAM/CloudFormation) defines all application resources: API Gateway, 3 Lambda functions, DynamoDB table, Cognito UserPool/Client/Domain, CloudWatch alarms, and CodeDeploy deployment preferences. `pipeline/lib/pipeline-stack.ts` (CDK) defines the complete CI/CD pipeline including CodePipeline, CodeBuild projects, S3 artifact buckets, and IAM roles. Over 90% of infrastructure is defined in code.
- **Gap**: None significant. All infrastructure is code-defined.
- **Recommendation**: Maintain IaC discipline. When adding new resources (Step Functions, EventBridge, vector databases), define them in SAM/CDK templates. Consider migrating to CDK for the application stack as well to have a unified IaC approach.

#### INF-Q6: CI/CD
- **Score**: 4/4 ✅
- **Finding**: Full CI/CD pipeline defined in `pipeline/lib/pipeline-stack.ts` (CDK). Pipeline stages: Source (CodeStar GitHub connection) → Build (unit tests + sam build via `pipeline/buildspec.json`) → Staging (deploy + end-to-end tests via `pipeline/buildspec-test.json`) → Production (manual approval + deploy). Build runs `npm test` for both create and get-all functions. Deploy uses `sam deploy` via `pipeline/buildspec-deploy.json`. E2E tests create Cognito users, exercise both endpoints, and validate responses.
- **Gap**: None for current scope. Pipeline is comprehensive with test, build, deploy, and approval stages.
- **Recommendation**: When adding agent-related components, extend the pipeline to include agent eval tests in the staging stage. Add a dedicated test stage for agent integration tests.

#### INF-Q7: API Entry Point
- **Score**: 3/4 🟡
- **Finding**: `template.yml` defines `AWS::Serverless::Api` resource `BooksApi` with API Gateway REST API. Features include: `LoggingLevel: INFO` for all resources/methods, `TracingEnabled: true` for X-Ray, and `CognitoAuth` authorizer configured for CreateBook. Stage variables pass the Lambda alias.
- **Gap**: No explicit throttling or rate limiting configured on API Gateway. No request validation models defined. No WAF integration. Default API Gateway throttling applies (10,000 RPS account-wide) but no per-endpoint or per-client limits.
- **Recommendation**: Add `ThrottlingBurstLimit` and `ThrottlingRateLimit` to API Gateway method settings. Define request validation models to reject malformed requests before they reach Lambda. Add WAF for additional protection when exposing APIs as agent tools.

#### INF-Q8: Real-time Streaming
- **Score**: 1/4 ❌
- **Finding**: No Kinesis, MSK, or any streaming service found in `template.yml` or elsewhere. No streaming SDK imports in source code. No event stream consumers or producers.
- **Gap**: No real-time streaming infrastructure. For the broader e-commerce agent use case, real-time order events and inventory changes would benefit from streaming to enable reactive agent behaviors.
- **Recommendation**: Consider Amazon Kinesis Data Streams or EventBridge for real-time event streaming when the agent needs to react to order status changes or inventory level alerts. Start with EventBridge for simpler event routing.

#### INF-Q9: Network Security
- **Score**: 1/4 ❌
- **Finding**: No VPC, subnet, or security group definitions in `template.yml` or the CDK pipeline stack. Lambda functions run without VPC configuration (AWS-managed networking). No network segmentation, no private subnets, no NACLs.
- **Gap**: Lambda functions are not placed in a VPC. While acceptable for DynamoDB access (via AWS service endpoints), adding agent-related services that require VPC (e.g., OpenSearch, RDS) will need network infrastructure.
- **Recommendation**: When adding VPC-dependent resources (OpenSearch for vector search, RDS for relational data), define VPC with public/private subnet tiers, NAT gateways, and security groups. Place Lambda functions in private subnets with VPC endpoints for DynamoDB and other AWS services.

#### INF-Q10: Auto-scaling
- **Score**: 3/4 🟡
- **Finding**: Lambda functions auto-scale inherently (up to account concurrency limits). DynamoDB `SimpleTable` uses on-demand capacity mode (default), which auto-scales read/write throughput. No explicit `ReservedConcurrentExecutions` or `ProvisionedConcurrencyConfig` on Lambda functions. No Application Auto Scaling policies.
- **Gap**: No explicit concurrency governance on Lambda. Under heavy agent-driven load, uncontrolled Lambda scaling could overwhelm downstream services or exceed cost budgets. No provisioned concurrency for latency-sensitive agent tool calls.
- **Recommendation**: Set `ReservedConcurrentExecutions` on each Lambda to prevent runaway scaling. Consider `ProvisionedConcurrency` for agent-facing functions to reduce cold start latency. Add DynamoDB auto-scaling alerts for cost monitoring.

### Application Architecture

#### APP-Q1: Programming Languages
- **Score**: 3/4 🟡
- **Finding**: TypeScript is the primary language. Lambda runtime is `nodejs22.x` as specified in `template.yml` Globals. Source files are `.ts` (e.g., `src/books/get-all/index.ts`, `src/books/create/index.ts`). Build uses esbuild for compilation. Dependencies include `aws-sdk v2.1692.0` and `aws-xray-sdk-core`. Pipeline is also TypeScript/CDK.
- **Gap**: TypeScript has a strong agent ecosystem (LangChain.js, Vercel AI SDK, Strands Agents SDK for Node.js) but Python remains the richest ecosystem for agent frameworks with the broadest library support.
- **Recommendation**: TypeScript is a solid choice — no language change needed. Use `@aws-sdk/client-bedrock-runtime` (AWS SDK v3) and LangChain.js or Strands Agents SDK for TypeScript when building the agent. Note: the codebase currently uses AWS SDK v2 (`aws-sdk v2.1692.0`) — migrating to AWS SDK v3 is recommended for better tree-shaking and Bedrock support.

#### APP-Q2: API Documentation
- **Score**: 1/4 ❌
- **Finding**: No OpenAPI/Swagger specification files found in the repository. `template.yml` references `OpenApiVersion: 3.0.1` in the `Globals.Api` section, but this is solely to prevent the default stage creation — it does not define an actual OpenAPI document. No `openapi.yaml`, `swagger.json`, or API documentation annotations exist. No API documentation in source code.
- **Gap**: Critical gap for agentic use case. Without an OpenAPI spec, an agent cannot programmatically discover API endpoints, understand request/response schemas, or auto-generate tool definitions. This is the #1 blocker for using this API as an agent tool.
- **Recommendation**: Create an `openapi.yaml` specification documenting the `/books` GET and POST endpoints, including request/response schemas (isbn, title, year, author, publisher, rating, pages), authentication requirements (Cognito for POST), and error responses. Integrate the spec into `template.yml` using SAM's `DefinitionBody` property for the API Gateway resource.

#### APP-Q3: Async vs Sync Communication
- **Score**: 1/4 ❌
- **Finding**: All communication is synchronous. `src/books/get-all/index.ts` performs a synchronous DynamoDB scan and returns. `src/books/create/index.ts` performs a synchronous DynamoDB putItem and returns. API Gateway → Lambda → DynamoDB → HTTP response. No message publishing patterns, no event-driven handlers, no SQS/SNS/EventBridge usage.
- **Gap**: No async communication patterns. Agent workflows for returns processing and inventory restocking are inherently multi-step and benefit from async event-driven patterns (e.g., emit "return requested" event, process asynchronously, notify when complete).
- **Recommendation**: Introduce EventBridge for domain events. When a book is created, emit a `BookCreated` event. For the broader agent use case, implement async patterns for return processing (SQS queue for return requests) and inventory updates (EventBridge rules triggering Lambda consumers).

#### APP-Q4: Monolith vs Microservices
- **Score**: 4/4 ✅
- **Finding**: Serverless architecture with well-decomposed functions. `GetAllBooks` and `CreateBook` are separate Lambda functions with independent code directories (`src/books/get-all/`, `src/books/create/`), separate `package.json` files, and individual deployment preferences. `CreateBookPreTraffic` is a separate deployment validation function. Each function has a single responsibility and clear domain boundary.
- **Gap**: None. The architecture is already decomposed with clear function boundaries suitable for agent tool isolation.
- **Recommendation**: Maintain this decomposition pattern when adding new capabilities. Each new agent tool (e.g., get-book-by-isbn, update-inventory, process-return) should be a separate Lambda function with its own directory, dependencies, and IAM policies.

#### APP-Q5: API Response Format
- **Score**: 4/4 ✅
- **Finding**: Both Lambda handlers return structured JSON responses. `src/books/get-all/index.ts` returns `{ statusCode: 200, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(bookDtos) }` where `bookDtos` is an array of book objects with typed fields (isbn, title, year, author, publisher, rating, pages). `src/books/create/index.ts` returns `{ statusCode: 201, headers: { 'Content-Type': 'application/json' }, body: '' }`.
- **Gap**: None. JSON responses are ideal for agent tool integration — agents can parse and reason over structured JSON directly.
- **Recommendation**: Maintain JSON as the response format. When adding new endpoints, ensure consistent response envelope (e.g., `{ data: [...], pagination: {...} }`) for easier agent parsing.

#### APP-Q6: Workflow Logic
- **Score**: 1/4 ❌
- **Finding**: No workflow orchestration in the application layer. Business logic is simple request-response: `get-all/index.ts` scans DynamoDB, `create/index.ts` puts an item. No saga patterns, no state machines, no process orchestration beyond individual Lambda handlers.
- **Gap**: No framework for orchestrating multi-step agent workflows. The target use case (returns processing: validate → check inventory → issue refund → update stock → notify customer) requires workflow coordination.
- **Recommendation**: Add AWS Step Functions for agent workflow orchestration. Define Express Workflows for synchronous tool calls and Standard Workflows for longer-running return/inventory processes. Step Functions integrates natively with Lambda, DynamoDB, SQS, and SNS.

#### APP-Q7: Idempotency
- **Score**: 2/4 🟠
- **Finding**: Partial natural idempotency via DynamoDB. `src/books/create/index.ts` uses `putItem` with `isbn` as the primary key — re-submitting the same ISBN overwrites with identical data (naturally idempotent for identical payloads). However, there are no explicit idempotency keys in API requests, no Idempotency-Key headers, and no deduplication mechanism for different payloads with the same intent.
- **Gap**: No explicit idempotency for agent retry scenarios. Agents frequently retry failed tool calls — without idempotency tokens, a retried "create book" with a different ISBN could create duplicate entries. For returns processing, duplicate return requests without idempotency could issue double refunds.
- **Recommendation**: Implement idempotency-key middleware using DynamoDB for token storage (e.g., `@middy/idempotency` or AWS Lambda Powertools for TypeScript). Require `Idempotency-Key` header on all write operations to enable safe agent retries.

#### APP-Q8: Rate Limiting & Throttling
- **Score**: 1/4 ❌
- **Finding**: No explicit rate limiting configured. API Gateway `BooksApi` in `template.yml` has no `ThrottlingBurstLimit` or `ThrottlingRateLimit` settings in `MethodSettings`. No AWS WAF rules. No usage plans or API keys for client-level throttling. Default API Gateway account-level throttle (10,000 RPS) applies implicitly.
- **Gap**: No per-client or per-endpoint rate limiting. An agent making rapid tool calls could exhaust API capacity or trigger cost overruns. Without rate limits, a misbehaving agent loop could send thousands of requests per second.
- **Recommendation**: Add throttling to API Gateway `MethodSettings` in `template.yml`. Create usage plans with API keys for agent clients to enforce per-agent rate limits. Consider AWS WAF rate-based rules for additional protection.

#### APP-Q9: Resilience Patterns
- **Score**: 1/4 ❌
- **Finding**: Minimal resilience patterns. Both Lambda handlers (`get-all/index.ts`, `create/index.ts`) use basic `try/catch` that returns `{ statusCode: 500, body: '' }` on any error. Lambda timeout is 5 seconds (set in `template.yml` Globals). No circuit breakers, no retry with exponential backoff, no timeout configuration for DynamoDB calls, no error classification (transient vs permanent).
- **Gap**: No resilience patterns for agent tool reliability. When an agent calls this API and receives a 500 error, it has no way to distinguish between transient (DynamoDB throttling) and permanent (invalid request) failures. No retry guidance in error responses.
- **Recommendation**: Add AWS Lambda Powertools for TypeScript for structured error handling. Implement retry-after headers for throttled requests. Add DynamoDB client timeout configuration. Return error codes that help the agent decide whether to retry (429 for throttle, 400 for bad request, 503 for temporary unavailability).

#### APP-Q10: Long-running Processes
- **Score**: 3/4 🟡
- **Finding**: No long-running processes exist. Lambda timeout is 5 seconds (configured in `template.yml` Globals). All operations are quick DynamoDB reads (`scan`) and writes (`putItem`) that complete well under the timeout. The `CreateBookPreTraffic` hook uses a 1.5-second wait (`wait()` function in `create-pre-traffic/index.ts`) for eventual consistency but this is a deployment utility, not a user-facing process.
- **Gap**: No async pattern for potentially long operations. While current operations are fast, the broader agent use case (returns processing, inventory restocking) may require longer-running operations that exceed Lambda's limits.
- **Recommendation**: When adding agent workflows that involve multi-step processes (return validation → refund → inventory update), implement Step Functions for orchestration with status polling endpoints. Use the async invocation pattern: accept the request, return a job ID, and provide a status endpoint for the agent to poll.

#### APP-Q11: API Versioning
- **Score**: 1/4 ❌
- **Finding**: No API versioning strategy. API paths are `/books` (GET and POST) with no version prefix. No `Accept-Version` headers. No versioning annotations in code. No changelog or migration documentation. API Gateway stage name is used for environment (`staging`/`production`) but not for versioning.
- **Gap**: No versioning means API changes can break existing agent tool definitions. When the agent's tool schema references specific request/response formats, any breaking API change requires simultaneous agent reconfiguration.
- **Recommendation**: Implement URL path versioning (`/v1/books`) in `template.yml`. This is the simplest pattern for agent tool integration — the agent's tool definition can pin to a specific API version while new versions are developed in parallel.

#### APP-Q12: Service Discovery & Mesh
- **Score**: 1/4 ❌
- **Finding**: No service discovery mechanism. DynamoDB table name is passed via environment variable `TABLE` in `template.yml`. API endpoint is a CloudFormation output (`ApiEndpoint`). E2E tests receive the endpoint via CodeBuild environment variables from deployment outputs. No service registry, no API catalog, no service mesh.
- **Gap**: No service registry for agent tool discovery. An agent needs to discover available tools (API endpoints) dynamically. Hard-coded endpoints in agent configuration are fragile.
- **Recommendation**: For immediate needs, document the API endpoint in a centralized configuration store (SSM Parameter Store or AppConfig). Long-term, implement an API catalog that the agent can query to discover available tools and their capabilities.

#### APP-Q13: AI/Agent Frameworks
- **Score**: 1/4 ❌
- **Finding**: No AI or agent framework dependencies found. Searched all `package.json` files (`src/books/get-all/package.json`, `src/books/create/package.json`, `src/books/create-pre-traffic/package.json`, `pipeline/package.json`). No `@aws-sdk/client-bedrock-runtime`, no `langchain`, no `strands-agents`, no `openai`, no `anthropic`, no AI-related imports in any source file.
- **Gap**: Critical gap for the target agentic use case. No foundation exists for building an agent that handles order inquiries, returns, or inventory management. The entire AI/agent stack needs to be introduced.
- **Recommendation**: Create a new agent service alongside this Books API. Use Amazon Bedrock as the LLM provider and Strands Agents SDK (TypeScript) or LangChain.js as the agent framework. Define the Books API endpoints as agent tools with JSON schema descriptions. Deploy the agent service via the existing CDK pipeline pattern.

### Data Foundations

#### DATA-Q1: Vector Database Presence
- **Score**: 1/4 ❌
- **Finding**: No vector database found in the repository. No OpenSearch Service, pgvector, Pinecone, Weaviate, Chroma, S3 Vectors, or Bedrock Knowledge Bases references in `template.yml`, source code, or dependency manifests. Searched all `package.json` files and IaC definitions.
- **Gap**: No vector store for semantic search. The agent for order status inquiries and product lookups cannot perform natural-language queries like "find me a book about machine learning" — only exact DynamoDB key lookups are possible.
- **Recommendation**: Provision Amazon OpenSearch Service with k-NN plugin for vector search over the book catalog, or use Amazon Bedrock Knowledge Bases for a fully managed RAG solution. DynamoDB data can be synced to the vector store via DynamoDB Streams.

#### DATA-Q2: Vector DB Management
- **Score**: 1/4 ❌
- **Finding**: No vector database exists (see DATA-Q1), so there is no managed or self-hosted vector DB to evaluate.
- **Gap**: When a vector database is introduced, it must be a managed service to minimize operational overhead and ensure availability for agent queries.
- **Recommendation**: Use Amazon Bedrock Knowledge Bases (fully managed) or Amazon OpenSearch Serverless (managed) rather than self-hosted alternatives. This aligns with the serverless-first approach of the existing architecture.

#### DATA-Q3: RAG Implementation
- **Score**: 1/4 ❌
- **Finding**: No RAG pipeline components found. No embedding model calls, no document chunking/splitting code, no similarity search patterns, no Bedrock Knowledge Base integration. No embedding-related imports in any `package.json`. No vector search queries in source code.
- **Gap**: The agent cannot retrieve contextually relevant information for answering questions about return policies, inventory guidelines, or product details beyond what's in the DynamoDB table. Without RAG, the agent relies solely on its training data and direct API calls.
- **Recommendation**: Implement a RAG pipeline using Amazon Bedrock Knowledge Bases with S3 as the data source for product documentation, return policies, and operational guides. Use Amazon Titan Embeddings for vectorization. Sync book catalog metadata from DynamoDB to the knowledge base for enriched product lookups.

#### DATA-Q4: Data Source Sprawl
- **Score**: 4/4 ✅
- **Finding**: Single data source — DynamoDB table `${Stage}-books` defined in `template.yml`. Both Lambda functions (`get-all/index.ts` and `create/index.ts`) access only this one table via the `TABLE` environment variable. No other database connections, no external API calls, no file system access.
- **Gap**: None for current scope. Clean single-source architecture. The broader agent use case will introduce additional data sources (orders, returns, inventory) that must be managed.
- **Recommendation**: As new data sources are added for the e-commerce agent (order database, inventory system, return tracking), implement a unified data access pattern. Use separate DynamoDB tables per domain with consistent access patterns to prevent sprawl.

#### DATA-Q5: Data Access Pattern
- **Score**: 2/4 🟠
- **Finding**: Lambda functions access DynamoDB directly via AWS SDK. `src/books/get-all/index.ts` creates a `new AWS.DynamoDB(ddbOptions)` client and calls `client.scan()`. `src/books/create/index.ts` creates a client and calls `client.putItem()`. No data access abstraction layer — each Lambda instantiates its own DynamoDB client with inline configuration. The test helper `src/books/tests/books-manager.js` provides a data access pattern but is only used in tests.
- **Gap**: Direct DynamoDB access from handler code with no abstraction layer. Duplicated client configuration across functions. No shared data model or validation layer. When the agent needs to access book data, it should go through a well-defined API rather than duplicating DynamoDB access logic.
- **Recommendation**: Extract a shared data access module that both Lambda handlers import. Define a `BooksRepository` class with typed methods (`getAll()`, `create(book)`, `getByIsbn(isbn)`). This provides a clean interface for agent tools and reduces code duplication.

#### DATA-Q6: Unstructured Data
- **Score**: 1/4 ❌
- **Finding**: No S3 storage, no Textract, no document parsing capabilities. No S3 bucket definitions in `template.yml` (only in pipeline CDK for CI/CD artifacts). Book data is fully structured in DynamoDB (isbn, title, year, author, publisher, rating, pages). No PDF, image, or document processing.
- **Gap**: No ability to ingest or search unstructured data (book descriptions, cover images, PDF catalogs). The agent for the broader e-commerce platform would need to process return forms, shipping labels, or product documentation.
- **Recommendation**: Add an S3 bucket for unstructured content (product documentation, return policies, FAQs). Integrate Amazon Textract for document parsing if needed. Use this content as a data source for the Bedrock Knowledge Base RAG pipeline.

#### DATA-Q7: Schema Documentation
- **Score**: 1/4 ❌
- **Finding**: No schema documentation. Book schema is implicitly defined in Lambda source code — both `get-all/index.ts` (response mapping) and `create/index.ts` (request parsing) reference fields: `isbn` (String), `title` (String), `year` (Number), `author` (String), `publisher` (String), `rating` (Number), `pages` (Number). No JSON Schema files, no Avro/Protobuf definitions, no database migration files, no schema registry.
- **Gap**: Schema is implicit and defined only in code. No formal data contract. An agent tool definition requires explicit schemas to validate inputs/outputs. Schema changes in code could break agent integrations silently.
- **Recommendation**: Create a JSON Schema definition for the Book entity. Include it in the OpenAPI specification (APP-Q2). Use TypeScript interfaces as the source of truth and generate JSON Schema from them using `typescript-json-schema` or similar tools.

#### DATA-Q8: Data Access Layer
- **Score**: 1/4 ❌
- **Finding**: No unified data access layer. Each Lambda function independently creates a DynamoDB client and performs raw SDK operations. `get-all/index.ts` uses `client.scan()` with raw attribute marshalling. `create/index.ts` uses `client.putItem()` with manual attribute construction. The `books-manager.js` test utility provides a data access pattern but is not used in production code.
- **Gap**: Scattered, duplicated data access code. Each function handles DynamoDB marshalling/unmarshalling independently. No single point of data contract. Adding new Lambda functions (e.g., get-by-isbn, update-book, delete-book) would require duplicating DynamoDB client setup and marshalling logic.
- **Recommendation**: Create a shared `books-repository.ts` module in a common directory. Use DynamoDB Document Client (AWS SDK v3) for automatic marshalling. Export typed methods: `getAllBooks()`, `createBook(book)`, `getBookByIsbn(isbn)`. Import this module in all Lambda handlers.

#### DATA-Q9: Embedding Freshness
- **Score**: 1/4 ❌
- **Finding**: No embeddings exist (see DATA-Q1 and DATA-Q3), so there is no embedding refresh mechanism to evaluate. No DynamoDB Streams configured. No event-driven indexing pipelines. No scheduled re-indexing jobs.
- **Gap**: When a vector store and RAG pipeline are implemented, book catalog changes (new books, updated metadata) must be reflected in the vector index in near-real-time. Without automated refresh, the agent could return stale results.
- **Recommendation**: Enable DynamoDB Streams on the `BooksTable` and create a Lambda trigger that generates embeddings for new/updated books and upserts them into the vector store. This provides near-real-time embedding freshness aligned with the event-driven architecture.

#### DATA-Q10: Database Engine Version & EOL
- **Score**: 4/4 ✅
- **Finding**: DynamoDB is a fully managed serverless database service. There is no engine version to pin or manage — AWS handles all version management, patching, and upgrades transparently. `template.yml` uses `AWS::Serverless::SimpleTable` which abstracts all DynamoDB configuration. No EOL concerns.
- **Gap**: None. DynamoDB has no version lifecycle management requirements.
- **Recommendation**: No action needed. If additional databases are introduced (e.g., RDS for relational data, OpenSearch for vector search), ensure engine versions are explicitly pinned in IaC and monitored for EOL dates.

#### DATA-Q11: Stored Procedures & Schema Complexity
- **Score**: 4/4 ✅
- **Finding**: No stored procedures, triggers, or proprietary SQL constructs. DynamoDB is a NoSQL key-value/document store with no SQL execution engine. All business logic is in the application layer (Lambda functions). No `.sql` files found in the repository. No ORM bypass patterns or raw SQL execution.
- **Gap**: None. All business logic resides in the application layer, making it easily accessible for agent tool integration.
- **Recommendation**: Maintain this pattern. Keep business logic in Lambda functions rather than pushing it to the database layer. This ensures agent tools can invoke business logic via API calls.

### Identity, Security & Governance

#### SEC-Q1: Secret Management
- **Score**: 3/4 🟡
- **Finding**: No hardcoded secrets in source code. DynamoDB access uses IAM roles via SAM built-in policies (`DynamoDBReadPolicy`, `DynamoDBWritePolicy`, `DynamoDBCrudPolicy`) defined in `template.yml`. The GitHub connection ARN is stored in AWS SSM Parameter Store and retrieved in `pipeline/lib/pipeline-stack.ts` via `StringParameter.fromStringParameterName(this, 'GithubConnectionArn', 'github_connection_arn')`. No `.env` files committed. No API keys or passwords in code.
- **Gap**: No AWS Secrets Manager usage. While current secrets are minimal (IAM roles handle AWS access), the broader agent use case may require API keys for external services, LLM provider tokens, or database credentials that need rotation and centralized management.
- **Recommendation**: When adding external service integrations (Bedrock API keys, third-party APIs), use AWS Secrets Manager with automatic rotation. Continue using IAM roles for AWS service access. Store agent configuration secrets (model IDs, tool credentials) in Secrets Manager rather than environment variables.

#### SEC-Q2: IAM Least Privilege
- **Score**: 2/4 🟠
- **Finding**: Lambda functions follow least privilege via SAM built-in policies in `template.yml`: `DynamoDBReadPolicy` scoped to `BooksTable` for `GetAllBooks`, `DynamoDBWritePolicy` scoped to `BooksTable` for `CreateBook`, and `DynamoDBCrudPolicy` for `CreateBookPreTraffic` plus specific `codedeploy:PutLifecycleEventHookExecutionStatus` and `lambda:InvokeFunction` permissions scoped to specific resources. **However**, `pipeline/lib/pipeline-stack.ts` grants broad `FullAccess` managed policies to the CodeBuild deploy role: `AWSCloudFormationFullAccess`, `AmazonDynamoDBFullAccess`, `AWSLambda_FullAccess`, `AmazonAPIGatewayAdministrator`, `IAMFullAccess`, `AWSCodeDeployFullAccess`, `AmazonCognitoPowerUser`.
- **Gap**: Pipeline IAM roles use overly broad `*FullAccess` policies. These grant permissions far beyond what's needed for `sam deploy`. `IAMFullAccess` is particularly risky — it allows the pipeline to create any IAM role with any permission.
- **Recommendation**: Replace `FullAccess` managed policies with scoped inline policies that grant only the specific CloudFormation, Lambda, DynamoDB, API Gateway, CodeDeploy, and Cognito actions needed for `sam deploy`. Use `IAMPassRole` instead of `IAMFullAccess` scoped to the specific roles SAM creates.

#### SEC-Q3: Identity Propagation
- **Score**: 2/4 🟠
- **Finding**: Cognito UserPool is defined in `template.yml` with OAuth2 implicit flow. `CreateBook` endpoint has a `CognitoAuth` authorizer with scopes (`email`, conditionally `aws.cognito.signin.user.admin`). `GetAllBooks` is a public endpoint with no authentication. Token is validated at the API Gateway layer but not propagated further — Lambda handlers do not access the caller's identity from the event context.
- **Gap**: No end-to-end identity propagation. The Lambda handler for `CreateBook` does not extract or use the caller's identity (user ID, email) from the Cognito token. For agent use cases, knowing which user the agent is acting on behalf of is critical for authorization decisions (e.g., "can this user return this order?").
- **Recommendation**: Extract the Cognito user identity from the API Gateway event context (`event.requestContext.authorizer.claims`) in Lambda handlers. Propagate user identity through all downstream service calls. When adding agent orchestration, pass the user context to ensure the agent acts within the user's authorization scope.

#### SEC-Q4: Audit Logging
- **Score**: 1/4 ❌
- **Finding**: API Gateway logging is enabled (`LoggingLevel: INFO`) with a CloudWatch logging role (`ApiGatewayLoggingRole`) in `template.yml`. Lambda functions have X-Ray tracing. However, no CloudTrail configuration exists in the IaC. No immutable log storage (S3 bucket with object lock). No log retention policies defined. No audit trail for data mutations.
- **Gap**: No CloudTrail for API-level audit logging. No immutable log storage. For agent-initiated actions (creating orders, processing returns, updating inventory), a complete audit trail is essential for compliance and debugging agent decisions.
- **Recommendation**: Add CloudTrail configuration in IaC with log file validation enabled. Store logs in an S3 bucket with object lock for immutability. Define CloudWatch log retention policies for Lambda function logs. When adding agent capabilities, log all agent actions (tool calls, decisions, user context) for auditability.

#### SEC-Q5: API Rate Limits
- **Score**: 1/4 ❌
- **Finding**: No explicit rate limiting configured on API Gateway. `template.yml` `BooksApi` resource has no `ThrottlingBurstLimit`, `ThrottlingRateLimit`, or usage plan definitions. No AWS WAF integration. No per-client rate limiting. API Gateway default account-level throttle (10,000 RPS) applies but is not customized.
- **Gap**: No rate limiting for agent tool calls. An agent in a retry loop or a misconfigured agent workflow could generate excessive API requests. Without per-client throttling, there's no way to isolate the blast radius of a misbehaving agent.
- **Recommendation**: Add API Gateway usage plans with API keys for agent clients. Configure per-method throttle limits in `MethodSettings`. Deploy AWS WAF with rate-based rules. This is critical before exposing this API as an agent tool.

#### SEC-Q6: PII Redaction
- **Score**: 1/4 ❌
- **Finding**: No PII redaction mechanisms found. No log scrubbing middleware, no PII masking libraries, no Amazon Macie configuration. Error handlers in `get-all/index.ts` and `create/index.ts` return empty bodies on error (which prevents error message leakage, a positive pattern), but no proactive PII detection in logs or responses. Book data (author names) could be considered personal data.
- **Gap**: No PII protection in logging or responses. When the agent handles order inquiries with customer names, emails, and addresses, PII redaction becomes critical to prevent sensitive data from appearing in agent logs, LLM context windows, or trace data.
- **Recommendation**: Add PII detection and redaction middleware to Lambda handlers. Use Amazon Comprehend for automated PII detection or implement regex-based scrubbing for known PII patterns (email, phone, address). Configure CloudWatch log data protection policies.

#### SEC-Q7: Human Approval Workflows
- **Score**: 2/4 🟠
- **Finding**: Pipeline has a `ManualApprovalAction` in `pipeline/lib/pipeline-stack.ts` for production deployments: `new ManualApprovalAction({ actionName: 'Review', additionalInformation: 'Ensure Books API works correctly in Staging and release date is agreed with Product Owners' })`. This gates code releases with human review. However, there is no human-in-the-loop mechanism for application-level high-risk actions.
- **Gap**: Human approval exists for deployments but not for agent-initiated high-risk actions. The target agent for returns processing and inventory management should require human approval for bulk operations, high-value refunds, or inventory write-offs.
- **Recommendation**: Add Step Functions with `waitForTaskToken` patterns for human-in-the-loop approval of high-risk agent actions. Define approval thresholds (e.g., refunds > $100 require approval). Integrate with SNS for approval notifications and a simple approval UI.

#### SEC-Q8: Encryption at Rest
- **Score**: 2/4 🟠
- **Finding**: DynamoDB table has `SSESpecification: SSEEnabled: true` in `template.yml` — this uses AWS-managed encryption keys. Pipeline S3 buckets in `pipeline/lib/pipeline-stack.ts` use `BucketEncryption.S3_MANAGED`. No customer-managed KMS keys (`aws_kms_key`) defined anywhere. No `kms_key_id` references on any resource.
- **Gap**: Encryption uses AWS-managed keys rather than customer-managed KMS keys. For agent workloads handling sensitive customer data (order details, payment information, PII), customer-managed keys provide additional control over key rotation, access policies, and cross-account restrictions.
- **Recommendation**: Create customer-managed KMS keys and apply them to DynamoDB SSE, S3 bucket encryption, and future resources (CloudWatch logs, SNS, SQS). Define key policies that restrict access to specific IAM roles.

#### SEC-Q9: API Authentication
- **Score**: 2/4 🟠
- **Finding**: `CreateBook` endpoint uses Cognito authorizer with OAuth2 scopes (`email` and conditionally `aws.cognito.signin.user.admin`) defined in `template.yml` under `Auth.Authorizers.CognitoAuth`. `GetAllBooks` endpoint has no authentication — it is publicly accessible. OAuth2 implicit flow is configured on the Cognito UserPoolClient.
- **Gap**: Partial authentication coverage. `GetAllBooks` is publicly accessible, which may be acceptable for a catalog but is a concern when the API is used as an agent tool — any unauthenticated client can query the full book catalog. OAuth2 implicit flow is also deprecated in favor of authorization code flow with PKCE.
- **Recommendation**: Add authentication to all endpoints when used as agent tools. Migrate from OAuth2 implicit flow to authorization code flow with PKCE. For agent-to-API authentication, use IAM authentication or API keys with usage plans in addition to Cognito tokens.

#### SEC-Q10: Centralized Identity
- **Score**: 3/4 🟡
- **Finding**: Amazon Cognito UserPool is defined in `template.yml` as the centralized identity provider. Configuration includes: `UserPoolName: ${Stage}-books-api-user-pool`, password policies, email-based username, UserPoolClient with OAuth2 implicit flow, and UserPoolDomain for hosted UI. E2E tests in `src/books/tests/index.js` demonstrate programmatic user creation and authentication via Cognito SDK.
- **Gap**: Cognito is configured but limited. Only implicit flow is supported. No SSO integration, no SAML/OIDC federation, no multi-factor authentication. For agent use cases, service-to-service authentication (agent calling this API) may need client credentials flow or IAM auth rather than user-based tokens.
- **Recommendation**: Add Cognito client credentials flow for machine-to-machine authentication (agent → API). Enable MFA for user-facing authentication. Consider federation with an enterprise IdP if the e-commerce platform has an existing identity provider.

### Operations & Observability

#### OPS-Q1: Distributed Tracing
- **Score**: 3/4 🟡
- **Finding**: AWS X-Ray tracing is enabled. `template.yml` sets `Tracing: Active` in the `Globals.Function` section for all Lambda functions, and `TracingEnabled: true` on the `BooksApi` API Gateway resource. Source code in `src/books/get-all/index.ts` and `src/books/create/index.ts` imports `aws-xray-sdk-core` and wraps the AWS SDK: `AWS = AWSXRay.captureAWS(AWSCore)`. The README references the X-Ray service map. Dependencies include `aws-xray-sdk-core v3.10.3`.
- **Gap**: X-Ray provides basic distributed tracing but lacks custom segments, no custom annotations for business context, no trace ID propagation in application headers, and no OpenTelemetry integration. For agent workflows, traces need to capture tool call chains, LLM invocations, and decision points — not just AWS SDK calls.
- **Recommendation**: Migrate from X-Ray SDK to OpenTelemetry (ADOT Lambda layer) for richer instrumentation. Add custom spans for business logic (book creation, catalog queries). When adding agent workflows, instrument tool calls with `gen_ai.*` semantic conventions for LLM span tracking.

#### OPS-Q2: Structured Logging
- **Score**: 1/4 ❌
- **Finding**: No structured logging framework. `src/books/create-pre-traffic/index.ts` uses `console.log('Entering PreTraffic Hook!')` and `console.log('DynamoDB item', JSON.stringify(Item, null, 2))`. The main Lambda handlers (`get-all/index.ts`, `create/index.ts`) have no logging at all — errors are silently caught and return empty 500 responses. No JSON log formatters, no correlation IDs, no `structlog` or similar.
- **Gap**: No structured logging infrastructure. Agent workflows generate complex execution traces that require JSON-formatted logs with correlation IDs, trace IDs, tool names, and user context to debug failures. Current silent error handling makes debugging impossible.
- **Recommendation**: Add AWS Lambda Powertools for TypeScript Logger. Configure JSON-format output with automatic correlation ID injection. Add logging to all Lambda handlers for request received, DynamoDB operation, and response returned events. Emit structured log entries that include trace IDs from X-Ray for log-trace correlation.

#### OPS-Q3: Automated Evals
- **Score**: 1/4 ❌
- **Finding**: No agent evaluation framework. No eval datasets, no scoring scripts, no LLM-as-judge patterns. Unit tests exist (`src/books/get-all/tests/index.spec.ts`, `src/books/create/tests/index.spec.ts`) and E2E tests exist (`src/books/tests/index.js`), but these test traditional API behavior, not agent tool selection accuracy or response quality.
- **Gap**: Critical gap for agentic use case. Without automated evals, there is no way to measure whether the agent correctly selects the Books API tool for catalog queries, accurately interprets responses, or handles edge cases (empty results, errors, rate limits). Agent regressions go undetected.
- **Recommendation**: Build an eval framework with golden datasets: (1) tool selection tests (given a user query, does the agent call the correct API?), (2) response accuracy tests (does the agent extract correct book details?), (3) error handling tests (does the agent retry on 500, report "not found" on empty results?). Integrate into the CI/CD pipeline's staging stage.

#### OPS-Q4: SLOs
- **Score**: 1/4 ❌
- **Finding**: CloudWatch alarms exist for Lambda errors — `CreateBookAliasErrorMetricGreaterThanZeroAlarm` and `GetAllBooksAliasErrorMetricGreaterThanZeroAlarm` in `template.yml` — but these are deployment safety checks (Errors > 0 triggers rollback), not SLO definitions. No latency SLOs, no availability targets, no error budget tracking, no SLO dashboards.
- **Gap**: No SLO definitions for the API. Agent tool calls have latency requirements — if the Books API responds in > 3 seconds, the agent's overall response time degrades. Without SLOs, there's no way to measure whether the API meets agent tool latency and availability requirements.
- **Recommendation**: Define SLOs for the Books API: availability > 99.9%, p99 latency < 500ms for GET /books, p99 latency < 1000ms for POST /books. Create CloudWatch alarms and dashboards for these SLOs. Add error budget tracking.

#### OPS-Q5: Rollback Capability
- **Score**: 3/4 🟡
- **Finding**: Excellent code rollback via CodeDeploy. `template.yml` configures `DeploymentPreference` with `Linear10PercentEvery1Minute` for production and `AllAtOnce` for staging. CloudWatch error alarms (`ErrorMetricGreaterThanZeroAlarm`) trigger automatic rollback during deployment. `CreateBookPreTraffic` Lambda performs a smoke test (creates and verifies a test book in DynamoDB) before traffic is shifted to the new version.
- **Gap**: Code rollback is solid, but no configuration or prompt rollback capability. When agent prompts, tool definitions, or model configurations are updated, there's no mechanism to roll back those changes independently of code deployments.
- **Recommendation**: When adding agent capabilities, version agent configurations (prompts, tool schemas, model selection) separately from code. Store them in S3 or DynamoDB with version history. Implement a configuration rollback mechanism alongside code rollback.

#### OPS-Q6: LLM Cost Tracking
- **Score**: 1/4 ❌
- **Finding**: No LLM usage in the application. No token counting, no cost attribution, no usage metrics. No CloudWatch custom metrics for any AI/LLM-related operations. No tiered retention policies for observability data.
- **Gap**: Critical gap for the target agentic use case. LLM API calls (Bedrock) have per-token costs that can scale rapidly with agent usage. Without cost tracking, the agent could incur unexpected costs through verbose prompts, unnecessary tool calls, or reasoning loops.
- **Recommendation**: When adding Bedrock integration, implement token usage tracking per request using the `usage` field from Bedrock API responses. Publish CloudWatch custom metrics for input/output token counts with dimensions for user, workflow, and tool. Set billing alerts and budget limits. Implement tiered log retention for LLM prompt/response pairs.

#### OPS-Q7: Business Metrics
- **Score**: 1/4 ❌
- **Finding**: No custom business metrics. No `cloudwatch.put_metric_data` calls in any Lambda function. Only infrastructure-level alarms exist (Lambda error count). No tracking of books created, books queried, unique users, or any business KPIs.
- **Gap**: No visibility into business outcomes. For the agent use case, business metrics (order inquiries resolved, returns processed successfully, inventory restocking accuracy) are essential to measure agent effectiveness and ROI.
- **Recommendation**: Add CloudWatch custom metrics for business events: `BooksCreated`, `BooksQueried`, `QueryLatency`. When adding agent workflows, track `AgentTasksCompleted`, `ReturnProcessingRate`, `InventoryRestockAccuracy`. Create dashboards combining infrastructure and business metrics.

#### OPS-Q8: Anomaly Detection
- **Score**: 1/4 ❌
- **Finding**: CloudWatch alarms use simple threshold-based detection (Errors > 0). No anomaly detection enabled. No latency alarms, no composite alarms, no PagerDuty/OpsGenie integration. The alarms in `template.yml` (`CreateBookAliasErrorMetricGreaterThanZeroAlarm`, `GetAllBooksAliasErrorMetricGreaterThanZeroAlarm`) only monitor during deployments.
- **Gap**: No anomaly detection for operational monitoring. Static thresholds are poorly suited for agent workloads — an agent suddenly calling the API 100x more than usual could indicate a reasoning loop, but a fixed threshold won't detect this behavioral change.
- **Recommendation**: Enable CloudWatch anomaly detection on API Gateway latency and Lambda invocation count. Create composite alarms that combine error rate + latency anomalies. When adding agent capabilities, monitor tool call frequency and response patterns for behavioral anomalies.

#### OPS-Q9: Deployment Strategy
- **Score**: 3/4 🟡
- **Finding**: Production uses `Linear10PercentEvery1Minute` deployment via CodeDeploy (configured in `template.yml` `DeploymentPreference`). This gradually shifts traffic to the new Lambda version over 10 minutes. CloudWatch alarms automatically trigger rollback if errors are detected. Staging uses `AllAtOnce` for faster iteration. Manual approval gate in pipeline before production deployment.
- **Gap**: Linear deployment is close to canary but not a true canary with synthetic traffic testing. No feature flags for gradual rollout of new capabilities. No A/B testing infrastructure for agent prompt variations.
- **Recommendation**: The current linear deployment strategy is solid. When adding agent capabilities, implement feature flags (AWS AppConfig) for gradual rollout of new agent tools and prompts. Add canary synthetic tests that exercise the API as an agent tool would.

#### OPS-Q10: Integration Testing
- **Score**: 3/4 🟡
- **Finding**: Comprehensive testing suite. Unit tests: `src/books/get-all/tests/index.spec.ts` (3 tests: get all books, get no books, DynamoDB error) and `src/books/create/tests/index.spec.ts` (3 tests: create book, invalid body, DynamoDB error) using mocha/chai/sinon with aws-sdk-mock. E2E tests: `src/books/tests/index.js` tests both endpoints against a live staging deployment — creates Cognito users, authenticates, creates books, retrieves books, tests auth failures. Run in pipeline via `pipeline/buildspec-test.json`.
- **Gap**: No contract tests between services. No load tests. No agent-specific integration tests (testing the API as an agent tool with realistic agent request patterns). E2E tests don't cover edge cases like pagination, large payloads, or concurrent writes.
- **Recommendation**: Add contract tests defining the API contract the agent depends on. Add load tests simulating agent traffic patterns (burst reads for catalog queries). When adding agent capabilities, add agent integration tests that exercise the full agent → API → DynamoDB flow.

#### OPS-Q11: Incident Response Automation
- **Score**: 1/4 ❌
- **Finding**: No runbooks found in the repository. No SSM Automation documents. No Lambda-based remediation functions. No self-healing patterns beyond CodeDeploy rollback. No incident response workflows or links to runbooks in alarm configurations. The CloudWatch alarms in `template.yml` trigger deployment rollback but not operational incident response.
- **Gap**: No incident response automation. When the agent's tools fail (API 500 errors, DynamoDB throttling), there's no automated remediation or structured incident response. For agentic workloads, incident response must be faster than human reaction time because agents can cause harm at machine speed.
- **Recommendation**: Create runbooks (Markdown or SSM documents) for common failure scenarios: DynamoDB throttling, Lambda cold start issues, API Gateway 5xx spikes. Implement Lambda-based self-healing for known issues (e.g., auto-increase DynamoDB capacity on throttling events). Link runbooks to CloudWatch alarms.

#### OPS-Q12: Observability Governance & Ownership
- **Score**: 1/4 ❌
- **Finding**: No SLO definition files. No CODEOWNERS file referencing observability assets. No platform team tooling evidence. No shared responsibility model documentation. Tags exist (`project: my-project`, `environment: ${Stage}`) on Lambda functions and DynamoDB table in `template.yml` but no observability-specific ownership tags.
- **Gap**: No observability governance. When agent workloads are added, there must be clear ownership of agent-level SLOs (task success rate, tool error rate, hallucination rate) and responsibility for monitoring agent behavior in production.
- **Recommendation**: Define observability ownership in a CODEOWNERS file or team charter. Establish SLO definitions as code (YAML files in the repo). When adding agent capabilities, define agent-specific SLOs and assign ownership to product teams (agent quality) and platform teams (infrastructure reliability).

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
| Move to Modern DevOps | Not Triggered | High | — | — | — |
| Move to AI | Triggered | High | High | APP-Q13: 1/4, DATA-Q1: 1/4, DATA-Q3: 1/4, OPS-Q3: 1/4, OPS-Q6: 1/4 | High |

### Parallel Execution Plan

**Parallel Track 1**: Move to AI — this is the sole triggered pathway and the primary focus for enabling the agentic use case.

**Sequential Dependencies**: None currently. The existing serverless foundation (Lambda, DynamoDB, API Gateway, CI/CD) is already modern and well-managed. The Move to AI pathway can proceed independently without requiring infrastructure modernization first.

**Note**: While only Move to AI is triggered, the AI pathway activities will naturally introduce elements from other pathways as prerequisites (e.g., adding EventBridge for async messaging, Step Functions for workflow orchestration). These are addressed as part of the AI pathway roadmap rather than as separate pathway initiatives.

### Move to AI

- **Priority**: High
- **Goal Alignment**: High
- **Trigger Criteria Met**:
  - APP-Q13: Score 1/4 — No AI/agent frameworks. No Bedrock, LangChain, Strands Agents, or any agent SDK in any `package.json`.
  - DATA-Q1: Score 1/4 — No vector database. No OpenSearch, pgvector, or Bedrock Knowledge Bases configured.
  - DATA-Q3: Score 1/4 — No RAG implementation. No embeddings, chunking, or semantic search pipelines.
  - OPS-Q3: Score 1/4 — No automated eval framework. No golden datasets, scoring scripts, or agent quality metrics.
  - OPS-Q6: Score 1/4 — No LLM cost tracking. No token usage metrics or cost attribution.
- **Current State**: The Books API is a clean serverless REST API with JSON responses, Cognito authentication, and a mature CI/CD pipeline. It has zero AI/agent capabilities — no LLM integration, no vector search, no RAG, and no agent framework. The API can serve as an agent tool for catalog lookups, but no orchestration exists to make it one.
- **Target State**: An AI agent powered by Amazon Bedrock that uses the Books API as a tool for product catalog queries. The agent handles order status inquiries, processes returns, and manages inventory restocking. Semantic search over product data via RAG. Automated eval pipeline validates agent behavior. LLM costs tracked and attributed per user/workflow.
- **Key Activities**:
  1. Create an OpenAPI specification for the Books API (prerequisite for agent tool definition)
  2. Build a new agent service using Strands Agents SDK or LangChain.js with Amazon Bedrock
  3. Define the Books API `/books` endpoints as agent tools with JSON schema descriptions
  4. Provision Amazon Bedrock Knowledge Bases with S3 data source for product documentation and return policies
  5. Implement automated eval framework with golden test datasets
  6. Add LLM token usage tracking via CloudWatch custom metrics
  7. Implement structured logging (Lambda Powertools) across all services for agent observability
- **Dependencies**: None — existing infrastructure is ready
- **Estimated Effort**: High — requires new agent service, RAG pipeline, eval framework, and observability infrastructure
- **Roadmap Phase Alignment**: Phases 1, 2, and 3 (spans entire roadmap)
- **Relevant Learning Materials**: Module 7 — Move to AI

---

## Quick Agent Wins

Even before completing the full modernization roadmap, these agent opportunities are available based on your current architecture:

1. **Book Catalog Query Agent Tool** — Your existing `GET /books` endpoint returns structured JSON responses with typed fields (isbn, title, year, author, publisher, rating, pages). An agent can immediately use this as a tool for product catalog lookups to support order inquiries and inventory queries.
   - **Leverages**: Structured JSON API response from `src/books/get-all/index.ts` with `Content-Type: application/json`
   - **Effort**: Low
   - **Value**: Enables the agent to answer "What books do you have?" and "Tell me about book X" queries for your e-commerce customer support use case

2. **Documentation-Grounded Knowledge Agent** — Your comprehensive `README.md` (300+ lines) documents the architecture, API usage, authentication flow, deployment process, and project structure. This documentation can be ingested into a Bedrock Knowledge Base for RAG-powered responses about the platform.
   - **Leverages**: Existing `README.md`, `CONTRIBUTING.md`, and inline code documentation
   - **Effort**: Low
   - **Value**: Provides the agent with grounded knowledge about the platform architecture, enabling it to answer developer and support questions about how the e-commerce system works

3. **CI/CD Pipeline Status Agent** — Your CDK-defined CodePipeline (`pipeline/lib/pipeline-stack.ts`) with Source → Build → Staging → Production stages can be queried by a DevOps agent to check deployment status, trigger builds, and monitor pipeline health.
   - **Leverages**: Full CI/CD pipeline defined in `pipeline/lib/pipeline-stack.ts` with CodePipeline, CodeBuild projects
   - **Effort**: Medium
   - **Value**: Enables a DevOps agent to provide deployment status updates and trigger catalog service deployments as part of the inventory management workflow

> These opportunities can be pursued in parallel with the modernization roadmap.
> They demonstrate agent value early while foundations are being built.

---

## Readiness Roadmap

### Phase 1 — Agent Quick Wins (Days 1–30)

Low-effort, high-impact items that establish the foundation for agent integration:

1. **Create OpenAPI 3.0 specification** for the Books API documenting `/books` GET and POST endpoints, request/response schemas, authentication requirements, and error responses. Integrate into `template.yml` using SAM's `DefinitionBody` property. This unblocks agent tool definition.
2. **Add structured logging** using AWS Lambda Powertools for TypeScript across all Lambda functions. Configure JSON-format output with correlation IDs and X-Ray trace ID injection. Replace silent `catch` blocks with structured error logging.
3. **Implement API versioning** — prefix all routes with `/v1/` (e.g., `/v1/books`) in `template.yml`. This protects agent tool definitions from breaking API changes.
4. **Add rate limiting** to API Gateway: configure `ThrottlingBurstLimit` and `ThrottlingRateLimit` in `MethodSettings`. Create a usage plan with API key for the future agent client.
5. **Migrate to AWS SDK v3** — replace `aws-sdk v2.1692.0` with modular `@aws-sdk/client-dynamodb` and `@aws-sdk/lib-dynamodb` for better tree-shaking, smaller bundle sizes, and Bedrock client support.

### Phase 2 — Agent Foundations (Months 1–3)

Structural improvements that build the agent infrastructure:

1. **Build the agent service** — create a new Lambda-based service using Strands Agents SDK or LangChain.js with Amazon Bedrock. Define the Books API endpoints as agent tools using the OpenAPI spec from Phase 1. Deploy via CDK alongside the existing pipeline.
2. **Provision Amazon Bedrock Knowledge Bases** with S3 as the data source. Ingest product documentation, return policies, and inventory guidelines. Configure Amazon Titan Embeddings for vectorization. This enables semantic search for order inquiries and return policy lookups.
3. **Add EventBridge for domain events** — emit `BookCreated`, `BookQueried` events from Lambda handlers. Create event rules for async processing. Add SQS queues for return request processing. This enables event-driven agent workflows.
4. **Implement Step Functions** for multi-step agent workflows — define state machines for return processing (validate → check inventory → issue refund → notify customer) and inventory restocking (detect low stock → generate order → approve → submit).
5. **Add human-in-the-loop approval** — implement Step Functions `waitForTaskToken` pattern for high-risk agent actions (refunds > threshold, bulk inventory changes). Integrate with SNS for approval notifications.
6. **Tighten pipeline IAM** — replace `FullAccess` managed policies in `pipeline/lib/pipeline-stack.ts` with scoped inline policies. This is essential before adding agent-related IAM roles.
7. **Enable DynamoDB Streams** for embedding freshness — trigger a Lambda function on book catalog changes that updates the vector store in near-real-time.

### Phase 3 — Agent Scale & Optimization (Months 3–6)

Advanced capabilities for production-ready agent operations:

1. **Implement automated eval framework** — create golden test datasets for order status inquiries, return processing, and inventory queries. Build scoring scripts that test tool selection accuracy, response quality, and edge case handling. Integrate into CI/CD staging stage.
2. **Add LLM cost tracking** — implement per-request token usage tracking using Bedrock API response `usage` fields. Publish CloudWatch custom metrics with dimensions for user, workflow, and tool. Set billing alerts and budget limits.
3. **Define SLOs** for the Books API and agent service — availability > 99.9%, p99 latency < 500ms for tool calls, agent task success rate > 95%. Create CloudWatch dashboards and error budget tracking.
4. **Enable anomaly detection** — CloudWatch anomaly detection on API latency, Lambda invocation count, and agent tool call frequency. Create composite alarms for multi-signal anomaly detection.
5. **Add business metrics** — track agent effectiveness: orders resolved, returns processed, inventory restocking accuracy, customer satisfaction proxy metrics. Create executive dashboards.
6. **Implement VPC and network security** — when adding OpenSearch or RDS for the broader e-commerce platform, define VPC with private subnets, security groups, and VPC endpoints.
7. **Build observability governance** — define agent-specific SLOs, assign ownership (product teams for agent quality, platform teams for infrastructure reliability), create CODEOWNERS for observability assets.

---

## Recommended Self-Paced Learning Materials

**Module 7: Move to AI** *(Primary — triggered pathway)*

These resources are directly relevant to enabling the agentic use case for order status inquiries, returns processing, and inventory management:

- AWS Modernization Pathways: Move to AI — https://skillbuilder.aws/learning-plan/VDFEE4ACCV/aws-modernization-pathways-move-to-ai-pathways-includes-labs/P3DAWPTN63
  - Comprehensive learning plan covering the full AI modernization journey
- Introduction to Generative AI: Art of the Possible — https://skillbuilder.aws/learn/ZEVZZ1D4AS/introduction-to-generative-ai--art-of-the-possible/Y7MTGJCW1U
  - Understand the landscape of generative AI use cases relevant to e-commerce
- Amazon Bedrock Getting Started — https://skillbuilder.aws/learn/63KTRM86DQ/amazon-bedrock-getting-started/SC2Y3HMAUE
  - Foundation for building the agent service with Amazon Bedrock
- Essentials for Prompt Engineering — https://skillbuilder.aws/learn/XBNAVKA88J/essentials-of-prompt-engineering/9T9Q45EDTV
  - Critical for designing effective agent prompts for order inquiries and returns
- Build and Evaluate Retrieval Augmented Generation (RAG) Applications using Knowledge Bases for Amazon Bedrock (Lab) — https://skillbuilder.aws/learn/JRGWCFYT67/lab--build-and-evaluate-retrieval-augmented-generation-rag-applications-using-knowledge-bases-for-amazon-bedrock/A4MN58JB7A
  - Hands-on lab for implementing RAG — directly applicable to DATA-Q1 and DATA-Q3 gaps
- Introduction to Agentic AI on AWS — https://skillbuilder.aws/learn/DNBD5MT8ZD/introduction-to-agentic-ai-on-aws/WAKAFK6UFY
  - Core concepts for building the target agent for order management
- Creating an AWS DevOps AI Agent with the Strands Agents SDK (Lab) — https://skillbuilder.aws/learn/AH1GD8AJY3/lab--creating-an-aws-devops-ai-agent-with-the-strands-agents-sdk/A9SKJNMPJ2
  - Practical lab for building agents with the Strands SDK — same framework recommended for this project
- AWS PartnerCast: Deep Dive: Building Observable AI Agents with Strands, Amazon Bedrock Agent Core & SageMaker MLflow — https://skillbuilder.aws/learn/1EN76TZBB6/aws-partnercast--deep-dive-building-observable-ai-agents-with-strands-amazon-bedrock-agent-core--sagemaker-mlflow--technical/CX2K6XAT84
  - Covers agent observability — addresses OPS-Q3 and OPS-Q6 gaps

**Module 6: Move to Modern DevOps** *(Supporting — for observability improvements)*

These resources support the observability and operational maturity improvements needed for agent reliability:

- AWS Modernization Pathways: Move to Modern DevOps — https://skillbuilder.aws/learning-plan/1FGEQKGPQD/aws-modernization-pathways-move-to-modern-devops-includes-labs/MNQZ2KPVCK
  - Comprehensive DevOps modernization learning plan
- Advanced Testing Practices Using AWS DevOps Tools — https://skillbuilder.aws/learn/1YC7UXUWBR/advanced-testing-practices-using-aws-devops-tools/A32U6G7NEQ
  - Relevant for improving integration testing and adding agent eval tests
- Monitor Python Applications Using Amazon CloudWatch Application Signals — https://skillbuilder.aws/learn/JMPDZD64MV/monitor-python-applications-using-amazon-cloudwatch-application-signals/2JP3J2MPCK
  - Application Signals concepts applicable to agent monitoring
- DevOps and AI on AWS: CloudWatch Anomaly Detection (Lab) — https://skillbuilder.aws/learn/RWYVJ73MXP/lab--devops-and-ai-on-aws-cloudwatch-anomaly-detection/BRPDNZUGU7
  - Directly addresses OPS-Q8 anomaly detection gap

**Module 2: Move to Cloud Native** *(Supporting — for API Gateway and serverless patterns)*

These resources support API Gateway hardening and serverless patterns for agent tool APIs:

- Amazon API Gateway for Serverless Applications — https://skillbuilder.aws/learn/GQA6FHWPJD/amazon-api-gateway-for-serverless-applications/JVRZ3PSW4H
  - Relevant for adding rate limiting, request validation, and usage plans to the Books API
- Architecting Serverless Applications — https://skillbuilder.aws/learn/MRWENY7FSX/architecting-serverless-applications/QVFY2JHVEH
  - Best practices for serverless architectures that serve as agent tools
- Lambda Foundations — https://skillbuilder.aws/learn/XHRS91KKK6/aws-lambda-foundations/R85JRN3APC
  - Foundation for optimizing Lambda functions as agent tool backends

---

## Appendix: Evidence Index

| # | File | Key Evidence |
|---|------|-------------|
| 1 | `template.yml` | SAM template: 3 Lambda functions (nodejs22.x), API Gateway with Cognito auth, DynamoDB SimpleTable with SSE, CloudWatch error alarms, CodeDeploy `Linear10PercentEvery1Minute` production deployment, X-Ray tracing enabled |
| 2 | `pipeline/lib/pipeline-stack.ts` | CDK pipeline: Source → Build → Staging (Deploy + Test) → Production (Manual Approval + Deploy). FullAccess IAM policies on deploy role. S3 buckets with S3_MANAGED encryption |
| 3 | `src/books/get-all/index.ts` | GetAllBooks handler: DynamoDB scan, X-Ray SDK wrapping (`AWSXRay.captureAWS`), JSON response with typed book DTO, basic try/catch error handling, no logging |
| 4 | `src/books/create/index.ts` | CreateBook handler: DynamoDB putItem with ISBN key, X-Ray SDK wrapping, JSON 201 response, basic try/catch, no input validation, no idempotency key |
| 5 | `src/books/create-pre-traffic/index.ts` | Pre-traffic hook: smoke test creating/verifying/deleting a test book in DynamoDB, CodeDeploy lifecycle status reporting, `console.log` logging |
| 6 | `src/books/get-all/package.json` | Dependencies: aws-sdk v2.1692.0, aws-xray-sdk-core v3.10.3. DevDeps: mocha, chai, sinon, aws-sdk-mock, typescript |
| 7 | `src/books/create/package.json` | Dependencies: aws-sdk v2.1692.0, aws-xray-sdk-core v3.10.3. Same dev dependencies as get-all |
| 8 | `src/books/create-pre-traffic/package.json` | Minimal deps: aws-sdk v2.1692.0 only (no X-Ray SDK) |
| 9 | `src/books/tests/index.js` | E2E tests: Cognito user creation/authentication, GET /books (public, 200), POST /books (authenticated, 201, 401 without token), payload validation (500 on missing fields) |
| 10 | `src/books/tests/books-manager.js` | DynamoDB test helper: batchWriteItem, getItem, deleteItem operations — demonstrates a data access pattern not used in production |
| 11 | `src/books/tests/package.json` | E2E test deps: aws-sdk, axios, uuid, mocha, chai |
| 12 | `src/books/get-all/tests/index.spec.ts` | Unit tests: 3 test cases using aws-sdk-mock for DynamoDB scan — success, empty results, error handling |
| 13 | `src/books/create/tests/index.spec.ts` | Unit tests: 3 test cases — successful put, invalid body, DynamoDB error |
| 14 | `pipeline/buildspec.json` | Build spec: installs SAM CLI, runs unit tests for create and get-all, sam build, sam package to S3 |
| 15 | `pipeline/buildspec-deploy.json` | Deploy spec: sam deploy with stack name and environment parameters, exports CloudFormation outputs |
| 16 | `pipeline/buildspec-test.json` | Test spec: runs E2E tests against deployed staging environment |
| 17 | `pipeline/bin/pipeline.ts` | CDK app entry point: instantiates PipelineStack |
| 18 | `pipeline/package.json` | CDK deps: aws-cdk-lib v2.189.1, constructs v10.4.2 |
| 19 | `README.md` | Comprehensive documentation: architecture overview, project structure, deployment instructions, monitoring, tracing, CI/CD pipeline, local testing with Docker, Cognito token acquisition |
| 20 | `events/create-book-request.json` | Sample API Gateway event for local testing: POST with book JSON body (isbn, title, year, author, publisher, rating, pages) |
