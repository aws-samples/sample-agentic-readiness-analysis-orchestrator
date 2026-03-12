# Agentic Readiness Assessment Report

**Target**: ./services/books-api
**Date**: 2026-03-12
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Assessment Goal**: agentic-ai-enablement
**Goal Context**: Building customer-facing AI agents for support and order management
**Repository Type**: application (auto-detected)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Score Table](#score-table)
3. [Top Priorities (Critical Gaps)](#top-priorities-critical-gaps)
4. [Detailed Findings](#detailed-findings)
   - [Infrastructure & Platform](#infrastructure--platform)
   - [Application Architecture](#application-architecture)
   - [Data Foundations](#data-foundations)
   - [Identity, Security & Governance](#identity-security--governance)
   - [Operations & Observability](#operations--observability)
5. [Recommended Modernization Pathways](#recommended-modernization-pathways)
6. [Microservices Decomposition Strategy](#microservices-decomposition-strategy)
7. [Quick Agent Wins](#quick-agent-wins)
8. [Readiness Roadmap](#readiness-roadmap)
9. [Recommended Self-Paced Learning Materials](#recommended-self-paced-learning-materials)
10. [Appendix: Evidence Index](#appendix-evidence-index)

---

## Executive Summary

The Books API has a solid serverless foundation — Lambda, DynamoDB, API Gateway, and a fully automated CI/CD pipeline with canary deployments — that positions it well as infrastructure for customer-facing AI agents. However, the application currently lacks every core capability needed for agentic AI enablement: there are no API documentation specs for agent tool discovery, no vector database or RAG pipeline for knowledge retrieval, no AI/agent framework integration, and no evaluation or cost-tracking infrastructure for LLM workloads. To build customer-facing AI agents for support and order management on top of this book catalog API, the immediate priorities are generating an OpenAPI specification, integrating an agent framework (e.g., Strands Agents SDK or LangChain.js), and establishing a vector store with Amazon Bedrock Knowledge Bases for semantic search over catalog data.

### Overall Score: 2.0 / 4.0

| Category | Score | Status |
|----------|-------|--------|
| Infrastructure & Platform | 2.7 / 4.0 | 🟡 |
| Application Architecture | 1.8 / 4.0 | 🟠 |
| Data Foundations | 1.9 / 4.0 | 🟠 |
| Identity, Security & Governance | 2.0 / 4.0 | 🟠 |
| Operations & Observability | 1.8 / 4.0 | 🟠 |

---

## Top Priorities (Critical Gaps)

The following 5 gaps are the most critical blockers for building customer-facing AI agents for support and order management. They are weighted by the agentic-ai-enablement priority criteria (APP-Q2, APP-Q13, DATA-Q1, DATA-Q2, DATA-Q3, SEC-Q7, OPS-Q3, OPS-Q6).

### 1. APP-Q2: No API Documentation (OpenAPI Spec) — Score 1/4 ❌
Agents discover and invoke tools through machine-readable API specifications. Without an OpenAPI spec, an AI agent cannot autonomously discover the `/books` endpoints, understand request schemas, or validate responses. The `OpenApiVersion: 3.0.1` in `template.yml` is cosmetic (prevents default API Gateway stage creation) and does not generate an actual spec.
- **First step**: Generate an OpenAPI 3.0 specification from the existing API Gateway configuration and Lambda handler contracts. Add it to the SAM template using the `DefinitionBody` property or create a standalone `openapi.yaml` file.

### 2. APP-Q13: No AI/Agent Frameworks — Score 1/4 ❌
No AI/agent framework dependencies (Bedrock SDK, LangChain, Strands Agents SDK, OpenAI) were found in any `package.json` file. Without agent framework integration, customer-facing AI agents cannot be built on this service.
- **First step**: Add `@aws-sdk/client-bedrock-runtime` and an agent orchestration SDK (e.g., `strands-agents` or `@langchain/core`) to the project. Create an initial agent Lambda function that wraps the existing Books API as a tool.

### 3. DATA-Q1/Q2/Q3: No Vector Database or RAG Pipeline — Scores 1/4 ❌
There is no vector database (OpenSearch, pgvector, Bedrock Knowledge Bases), no embedding generation, and no semantic search capability. Customer support agents need RAG to answer questions about the book catalog, order policies, and contextual information that goes beyond simple CRUD queries.
- **First step**: Create an Amazon Bedrock Knowledge Base backed by Amazon OpenSearch Serverless. Ingest book catalog data and any support documentation as embeddings. This enables agents to answer natural language queries like "Find science fiction books published after 2020."

### 4. OPS-Q3: No Automated Agent Evaluation Framework — Score 1/4 ❌
No eval datasets, scoring scripts, or LLM-as-judge patterns exist. Without automated evaluations, there is no way to measure whether customer-facing agents are providing correct, helpful, and safe responses before deploying them.
- **First step**: Create a golden dataset of expected agent interactions (e.g., "What books do you have by Author X?" → expected book list). Implement an eval pipeline using Amazon Bedrock's evaluation capabilities or a custom scoring script in the CI/CD pipeline.

### 5. OPS-Q6: No LLM Cost Tracking — Score 1/4 ❌
No token usage tracking, cost attribution, or observability retention policies exist. Customer-facing agents can generate significant LLM costs that are invisible without per-request token tracking and user/feature attribution.
- **First step**: Instrument agent Lambda functions to log Bedrock response `usage` metadata (input tokens, output tokens, model ID) as structured CloudWatch metrics with dimensions for user, workflow, and feature.

---

## Detailed Findings

### Infrastructure & Platform

#### INF-Q1: Compute
- **Score**: 4/4 ✅
- **Finding**: All compute is AWS Lambda (serverless). `template.yml` defines three `AWS::Serverless::Function` resources: `GetAllBooks`, `CreateBook`, and `CreateBookPreTraffic`, all running `nodejs22.x` runtime with 512MB memory and 5-second timeout. No EC2 instances, ECS tasks, or other non-serverless compute detected.
- **Gap**: None. 100% serverless compute.
- **Recommendation**: Current Lambda-based compute is agent-ready. When adding agent functions, consider increasing the memory and timeout for LLM-invoking Lambdas (Bedrock calls may need 30s+ timeout and 1024MB+ memory).

#### INF-Q2: Databases
- **Score**: 4/4 ✅
- **Finding**: `template.yml` defines `BooksTable` as `AWS::Serverless::SimpleTable` (DynamoDB) with SSE enabled. DynamoDB is fully managed with automatic failover and scaling. No self-managed databases detected anywhere in the codebase.
- **Gap**: None. Database is fully managed.
- **Recommendation**: DynamoDB is a strong choice for the existing book catalog. For agent conversation history and session state, consider adding a dedicated DynamoDB table with TTL for automatic session cleanup.

#### INF-Q3: Workflow Orchestration
- **Score**: 1/4 ❌
- **Finding**: No Step Functions, Temporal, Camunda, or any workflow orchestration service found. The `CreateBookPreTraffic` function is a simple smoke-test Lambda, not a workflow orchestrator. Business logic is inline in Lambda handlers.
- **Gap**: No dedicated workflow orchestration. Agent workflows requiring multi-step tool invocation, conditional branching, or human-in-the-loop approvals have no orchestration layer.
- **Recommendation**: Add AWS Step Functions for agent workflow orchestration. Step Functions can coordinate multi-step agent tasks (e.g., "look up book → check inventory → place order") with built-in retry, timeout, and human approval capabilities.

#### INF-Q4: Async Messaging
- **Score**: 1/4 ❌
- **Finding**: No SQS, SNS, EventBridge, or any messaging service detected in `template.yml` or source code. All communication is synchronous: API Gateway → Lambda → DynamoDB.
- **Gap**: No async messaging capability. Agent workflows that trigger background tasks (e.g., order processing, notification sending) cannot be decoupled from the request path.
- **Recommendation**: Add Amazon EventBridge for domain events (e.g., `BookCreated`, `OrderPlaced`) and SQS for background task processing. This enables agents to trigger asynchronous workflows and receive callbacks.

#### INF-Q5: Infrastructure as Code
- **Score**: 4/4 ✅
- **Finding**: 100% of infrastructure is defined in IaC. `template.yml` (AWS SAM/CloudFormation) covers all application resources: Lambda functions, DynamoDB table, API Gateway, Cognito User Pool, CloudWatch alarms, and IAM roles. `pipeline/lib/pipeline-stack.ts` (AWS CDK) defines the complete CI/CD pipeline with CodePipeline, CodeBuild, S3 artifact buckets.
- **Gap**: None. Full IaC coverage.
- **Recommendation**: Maintain current IaC discipline. When adding agent infrastructure (Bedrock, Knowledge Bases, vector stores), define them in the SAM template or a dedicated CDK stack.

#### INF-Q6: CI/CD
- **Score**: 4/4 ✅
- **Finding**: `pipeline/lib/pipeline-stack.ts` defines a 4-stage CodePipeline: Source (GitHub via CodeStar Connections) → Build (SAM build + unit tests via `pipeline/buildspec.json`) → Staging (deploy + end-to-end tests via `pipeline/buildspec-test.json`) → Production (manual approval + deploy). Unit tests run for both `create` and `get-all` functions. E2E tests validate actual API endpoints with Cognito authentication.
- **Gap**: None. Full CI/CD automation with test, build, and deploy stages.
- **Recommendation**: When adding agent capabilities, extend the pipeline with an agent evaluation stage between Staging and Production that runs golden dataset evals against the deployed agent.

#### INF-Q7: API Entry Point
- **Score**: 3/4 🟡
- **Finding**: `template.yml` defines `BooksApi` as `AWS::Serverless::Api` with Cognito authorizer (`CognitoAuth`), method-level logging (`LoggingLevel: INFO`), and X-Ray tracing (`TracingEnabled: true`). API Gateway acts as the managed entry point for all Lambda functions.
- **Gap**: No explicit throttling configuration (burst/rate limits), no usage plans, no WAF rules. Relies on API Gateway default throttling only.
- **Recommendation**: Add explicit throttle settings and usage plans to `BooksApi` in `template.yml`. For agent access, create a dedicated API key and usage plan with appropriate rate limits to prevent runaway agent invocations.

#### INF-Q8: Real-time Streaming
- **Score**: 1/4 ❌
- **Finding**: No Kinesis, MSK, or streaming services detected in `template.yml` or any source code. No stream consumer patterns.
- **Gap**: No real-time streaming capability. Agents cannot subscribe to real-time data changes (e.g., new book additions, order status updates) for event-driven responses.
- **Recommendation**: For the current book catalog scope, streaming is not critical. If expanding to order management, consider DynamoDB Streams with EventBridge Pipes to enable agents to react to data changes in real time.

#### INF-Q9: Network Security
- **Score**: 2/4 🟠
- **Finding**: Lambda functions run in the AWS-managed VPC (no VPC configuration in `template.yml`). DynamoDB is accessed via the public AWS endpoint. API Gateway is internet-facing. No VPC, private subnets, security groups, or VPC endpoints are configured.
- **Gap**: No network segmentation. If the API expands to handle sensitive customer data (order management, PII), the lack of VPC isolation and private endpoints becomes a security concern.
- **Recommendation**: For the current public book catalog, this is acceptable. Before adding agent capabilities that handle customer PII (support queries, order data), configure Lambda VPC access with private subnets and DynamoDB VPC endpoints.

#### INF-Q10: Auto-scaling
- **Score**: 3/4 🟡
- **Finding**: Lambda functions auto-scale inherently (concurrent executions scale to account limits). DynamoDB `SimpleTable` defaults to on-demand capacity mode (auto-scaling by default). No reserved concurrency limits or provisioned concurrency configured for Lambda.
- **Gap**: No Lambda reserved concurrency limits to prevent one function from consuming all account concurrency. No provisioned concurrency for latency-sensitive agent endpoints.
- **Recommendation**: Set reserved concurrency on each Lambda function. For agent-facing Lambda functions that invoke Bedrock, configure provisioned concurrency to minimize cold start latency for customer-facing interactions.

### Application Architecture

#### APP-Q1: Programming Languages
- **Score**: 3/4 🟡
- **Finding**: TypeScript is the primary language, running on `nodejs22.x` runtime. All Lambda function source code (`src/books/get-all/index.ts`, `src/books/create/index.ts`, `src/books/create-pre-traffic/index.ts`) and pipeline code (`pipeline/lib/pipeline-stack.ts`) are TypeScript. E2E tests use JavaScript.
- **Gap**: TypeScript has a good agent framework ecosystem (LangChain.js, Strands Agents SDK) but it is not as mature as Python's (which has the broadest agent framework ecosystem).
- **Recommendation**: TypeScript is a solid choice. Use `strands-agents` (TypeScript SDK) or `@langchain/core` for agent development. No language migration needed.

#### APP-Q2: API Documentation
- **Score**: 1/4 ❌
- **Finding**: `template.yml` sets `OpenApiVersion: 3.0.1` in the `Globals.Api` section, but this is only to prevent API Gateway from creating a default stage — it does not generate an OpenAPI specification. No `openapi.yaml`, `swagger.json`, or API documentation files exist anywhere in the repository. No `@OpenAPIDefinition` or documentation annotations in source code.
- **Gap**: No machine-readable API specification. Agents cannot discover available endpoints, request/response schemas, or parameter constraints. This is the most critical blocker for agentic tool integration.
- **Recommendation**: Create an `openapi.yaml` file documenting the `GET /books` and `POST /books` endpoints with full request/response schemas. Reference it in `template.yml` using `DefinitionBody` to keep the spec and deployment in sync.

#### APP-Q3: Async vs Sync Communication
- **Score**: 1/4 ❌
- **Finding**: All communication is synchronous. `src/books/create/index.ts` performs a synchronous `putItem` to DynamoDB. `src/books/get-all/index.ts` performs a synchronous `scan`. No message publishing, no event-driven handlers, no async patterns detected.
- **Gap**: 100% synchronous communication. No ability to decouple long-running agent operations from the API request path.
- **Recommendation**: Introduce EventBridge events for domain actions (e.g., emit a `BookCreated` event after successful creation). This enables agent workflows to subscribe to events and react asynchronously.

#### APP-Q4: Monolith vs Microservices
- **Score**: 3/4 🟡
- **Finding**: The application uses a serverless architecture with function-level separation. `GetAllBooks` and `CreateBook` are separate Lambda functions in separate directories (`src/books/get-all/`, `src/books/create/`) with their own `package.json` and `tsconfig.json`. They share a single DynamoDB table (`BooksTable`). The `CreateBookPreTraffic` function is a deployment utility, not a business function.
- **Gap**: While functions are separated, they share a database table and have no clear domain boundary enforcement. Only 2 business endpoints exist.
- **Recommendation**: The current architecture is adequate for the book catalog domain. As the system grows to support order management, define clear bounded contexts (Books, Orders, Customers) with separate DynamoDB tables per domain.

#### APP-Q5: API Response Format
- **Score**: 4/4 ✅
- **Finding**: Both Lambda functions return structured JSON responses with `Content-Type: application/json` headers. `src/books/get-all/index.ts` returns an array of book objects with typed fields (isbn, title, year, author, publisher, rating, pages). `src/books/create/index.ts` returns a 201 status code.
- **Gap**: None. All APIs return structured JSON.
- **Recommendation**: JSON responses are agent-ready. Ensure all future endpoints maintain this pattern and include consistent error response schemas.

#### APP-Q6: Workflow Logic
- **Score**: 1/4 ❌
- **Finding**: No workflow orchestration service or framework in use. Business logic is simple CRUD operations directly in Lambda handlers with inline try/catch blocks. `src/books/create/index.ts` parses the request body, constructs DynamoDB params, and calls `putItem` — all in a single function.
- **Gap**: No orchestration for multi-step workflows. Agent tasks requiring sequential tool invocations (e.g., "validate book → check duplicates → create → notify") cannot be orchestrated reliably.
- **Recommendation**: Introduce AWS Step Functions for agent workflow orchestration. Define state machines for complex agent tasks, with built-in retry logic, error handling, and human approval steps.

#### APP-Q7: Idempotency
- **Score**: 1/4 ❌
- **Finding**: `src/books/create/index.ts` performs a `putItem` on DynamoDB using the `isbn` as the partition key. There is no idempotency key header, no conditional write (`ConditionExpression`), and no deduplication logic. Duplicate requests with the same ISBN will silently overwrite existing data.
- **Gap**: No idempotency protection. Agent retries (common in agentic workflows due to LLM non-determinism and network issues) may cause duplicate or corrupted data.
- **Recommendation**: Add a `ConditionExpression: "attribute_not_exists(isbn)"` to the `putItem` call for true create semantics. Support an `Idempotency-Key` header for agent-initiated requests using the AWS Lambda Powertools idempotency utility.

#### APP-Q8: Rate Limiting & Throttling
- **Score**: 1/4 ❌
- **Finding**: No explicit rate limiting configured. `template.yml` does not define throttle settings, usage plans, API keys, or WAF rules for `BooksApi`. Default API Gateway account-level throttling applies (10,000 requests/second) but no per-client or per-endpoint limits.
- **Gap**: No protection against agent-driven request storms. A misconfigured agent loop could overwhelm the API and exhaust Lambda concurrency.
- **Recommendation**: Add `ThrottlingBurstLimit` and `ThrottlingRateLimit` to the API Gateway stage. Create usage plans with API keys for agent clients to enforce per-agent quotas.

#### APP-Q9: Resilience Patterns
- **Score**: 1/4 ❌
- **Finding**: No circuit breaker, retry, or timeout configuration beyond the default Lambda 5-second timeout in `template.yml`. No resilience libraries (Polly, retry decorators) in any `package.json`. Error handling is a generic try/catch returning 500 with empty body in both `src/books/create/index.ts` and `src/books/get-all/index.ts`.
- **Gap**: No resilience patterns for external dependency calls. Agent workflows that call multiple services will have no fault isolation.
- **Recommendation**: Add retry with exponential backoff for DynamoDB calls using the AWS SDK built-in retry configuration. Implement circuit breaker patterns for any new external service calls (Bedrock, external APIs). Return meaningful error messages instead of empty bodies.

#### APP-Q10: Long-running Processes
- **Score**: 3/4 🟡
- **Finding**: Lambda functions have a 5-second timeout. Current operations are simple DynamoDB reads/writes that complete in milliseconds. No operations exceed 30 seconds. The architecture is appropriate for the current CRUD scope.
- **Gap**: No async processing pattern for future long-running operations. Agent interactions with LLMs can exceed 30 seconds, especially for complex reasoning tasks.
- **Recommendation**: When adding Bedrock-invoking agent functions, implement async invocation patterns: return a job ID immediately, process in the background, and provide a status polling endpoint.

#### APP-Q11: API Versioning
- **Score**: 1/4 ❌
- **Finding**: API paths are `/books` with no versioning. No `/v1/` prefix, no `Accept-Version` headers, no versioning strategy documented. `template.yml` defines the path as `/books` directly.
- **Gap**: No API versioning strategy. Agent integrations will break on API changes with no backward compatibility mechanism.
- **Recommendation**: Add path-based versioning (e.g., `/v1/books`) in `template.yml`. This is critical for agent tool stability — agents rely on consistent API contracts.

#### APP-Q12: Service Discovery & Mesh
- **Score**: 2/4 🟠
- **Finding**: API Gateway serves as the single entry point for the Books API. There is no inter-service communication. The API endpoint URL is output from CloudFormation (`Outputs.ApiEndpoint`) and passed to tests via environment variables. No service mesh, API catalog, or service registry configured.
- **Gap**: No service discovery mechanism. When expanding to multiple services (orders, customers), agents will need a catalog of available tools/services.
- **Recommendation**: API Gateway is a suitable service catalog for the current scope. As services expand, consider AWS Cloud Map or a centralized API catalog that agents can query to discover available tools.

#### APP-Q13: AI/Agent Frameworks
- **Score**: 1/4 ❌
- **Finding**: No AI/agent framework dependencies found in any `package.json` file. No imports of `@aws-sdk/client-bedrock-runtime`, `langchain`, `@langchain/core`, `strands-agents`, `openai`, or `anthropic` in any source file. No MCP SDK or agent tool definitions.
- **Gap**: No agent framework integration. The application cannot serve as a tool for AI agents or host agent logic.
- **Recommendation**: Add an agent orchestration layer using the Strands Agents SDK or LangChain.js. Define the Books API endpoints as agent tools with descriptions and parameter schemas. Create a new Lambda function for the agent endpoint that uses Amazon Bedrock for LLM inference.

### Data Foundations

#### DATA-Q1: Vector Database Presence
- **Score**: 1/4 ❌
- **Finding**: No vector database found. No OpenSearch, pgvector, Pinecone, Weaviate, Chroma, S3 Vectors, or Amazon Bedrock Knowledge Bases configured in `template.yml` or referenced in any `package.json` dependency.
- **Gap**: No semantic search capability. Customer support agents cannot perform similarity-based queries (e.g., "find books similar to X" or "what books match this description?").
- **Recommendation**: Deploy an Amazon Bedrock Knowledge Base backed by Amazon OpenSearch Serverless as the vector store. Ingest book catalog data (titles, descriptions, authors) as embeddings using Amazon Titan Embeddings.

#### DATA-Q2: Vector DB Management
- **Score**: 1/4 ❌
- **Finding**: No vector database exists (see DATA-Q1). There is nothing to evaluate for management.
- **Gap**: No vector database infrastructure, managed or otherwise.
- **Recommendation**: Use Amazon Bedrock Knowledge Bases, which provides a fully managed vector store with automatic embedding synchronization — no infrastructure to manage.

#### DATA-Q3: RAG Implementation
- **Score**: 1/4 ❌
- **Finding**: No document chunking, embedding generation, or semantic search code found in any source file or dependency. No Bedrock Titan Embeddings, OpenAI ada, or any embedding model references. No similarity_search or knn_search patterns.
- **Gap**: No RAG pipeline. Agents cannot augment their responses with domain-specific book catalog knowledge, support documentation, or order policies.
- **Recommendation**: Implement a RAG pipeline using Amazon Bedrock Knowledge Bases: (1) export book catalog data from DynamoDB to S3, (2) configure a Knowledge Base with chunking strategy, (3) use the `RetrieveAndGenerate` API in the agent Lambda to ground responses in catalog data.

#### DATA-Q4: Data Source Sprawl
- **Score**: 4/4 ✅
- **Finding**: Single data source: DynamoDB `BooksTable`. All Lambda functions interact with this one table. `src/books/create/index.ts` writes to it; `src/books/get-all/index.ts` reads from it; `src/books/create-pre-traffic/index.ts` performs smoke test reads/writes. No other databases, APIs, or external data sources.
- **Gap**: None. Clean, single data source.
- **Recommendation**: Maintain this simplicity. When adding order management, create separate DynamoDB tables per domain rather than expanding the books table.

#### DATA-Q5: Data Access Pattern
- **Score**: 2/4 🟠
- **Finding**: Lambda functions access DynamoDB directly via the AWS SDK. `src/books/get-all/index.ts` creates a `new AWS.DynamoDB(ddbOptions)` and calls `client.scan()`. `src/books/create/index.ts` creates its own DynamoDB client and calls `client.putItem()`. There is no shared data access layer or repository pattern.
- **Gap**: No data access abstraction. Each Lambda function has its own DynamoDB client creation and raw DynamoDB API usage. Book schema mapping (DynamoDB AttributeValues ↔ domain objects) is duplicated across functions.
- **Recommendation**: Extract a shared `books-repository` module that encapsulates DynamoDB operations and schema mapping. This creates a clean data access contract that agent tools can also use.

#### DATA-Q6: Unstructured Data
- **Score**: 1/4 ❌
- **Finding**: No S3 storage, Textract, Tika, or document parsing detected in `template.yml` or any source code. The application handles only structured DynamoDB data (book records).
- **Gap**: No unstructured data processing. Customer support agents may need to process documents (book descriptions, order receipts, support tickets).
- **Recommendation**: Add an S3 bucket for document storage (book descriptions, cover images, support documents). Integrate with Amazon Textract for document parsing if needed for order management.

#### DATA-Q7: Schema Documentation
- **Score**: 1/4 ❌
- **Finding**: The book schema is implicitly defined in Lambda code — `src/books/create/index.ts` destructures `{ isbn, title, year, author, publisher, rating, pages }` from the request body and maps them to DynamoDB AttributeValues. The same schema appears in `src/books/get-all/index.ts` for response mapping and in `src/books/tests/books-manager.js`. No JSON Schema file, Avro/Protobuf definitions, or formal schema documentation exists.
- **Gap**: No formal schema documentation. Agents cannot discover the data model without reading source code. Schema changes risk silent breakage across multiple files.
- **Recommendation**: Create a JSON Schema definition for the Book entity and reference it in the OpenAPI specification. Store schemas in a `schemas/` directory and use them for request validation in the Lambda functions.

#### DATA-Q8: Data Access Layer
- **Score**: 1/4 ❌
- **Finding**: Each Lambda function creates its own DynamoDB client and performs raw DynamoDB API calls. `src/books/get-all/index.ts` contains its own client instantiation, scan call, and AttributeValue-to-DTO mapping. `src/books/create/index.ts` has separate client creation and putItem logic. The test helper `src/books/tests/books-manager.js` has yet another DynamoDB client with identical schema mapping code.
- **Gap**: No unified data access layer. Schema mapping logic is duplicated in 3+ files. Adding new data operations (get by ID, update, delete) requires duplicating the same patterns.
- **Recommendation**: Create a shared `books-repository` module with typed methods (`getAll()`, `create(book)`, `getByIsbn(isbn)`) that encapsulate DynamoDB operations. This becomes a clean tool interface for agents.

#### DATA-Q9: Embedding Freshness
- **Score**: 1/4 ❌
- **Finding**: No embeddings exist (see DATA-Q1/Q3). No event-driven embedding refresh, scheduled re-indexing, or CDC patterns detected.
- **Gap**: No mechanism to keep vector embeddings synchronized with the book catalog data.
- **Recommendation**: When implementing the RAG pipeline, configure DynamoDB Streams → EventBridge Pipe → Lambda → Bedrock Knowledge Base sync to automatically refresh embeddings when books are added or updated.

#### DATA-Q10: Database Engine Version & EOL
- **Score**: 4/4 ✅
- **Finding**: DynamoDB is a fully managed serverless database. AWS manages all versioning, patching, and engine updates. There is no engine version to pin and no EOL concerns. `template.yml` uses `AWS::Serverless::SimpleTable` which abstracts all version management.
- **Gap**: None. DynamoDB has no EOL concerns.
- **Recommendation**: No action needed. Continue using DynamoDB for its zero-maintenance posture.

#### DATA-Q11: Stored Procedures & Schema Complexity
- **Score**: 4/4 ✅
- **Finding**: DynamoDB does not support stored procedures, triggers, or proprietary SQL constructs. No `.sql` files exist in the repository. All business logic (data validation, schema mapping) resides in the application layer (`src/books/create/index.ts`, `src/books/get-all/index.ts`).
- **Gap**: None. No stored procedure or proprietary SQL coupling.
- **Recommendation**: No action needed. Maintaining all business logic in the application layer is the correct pattern for agent-ready architectures.

### Identity, Security & Governance

#### SEC-Q1: Secret Management
- **Score**: 3/4 🟡
- **Finding**: No hardcoded secrets found in any source code. Environment variables in `template.yml` contain only non-sensitive values (`TABLE` for DynamoDB table name). Lambda functions access DynamoDB via IAM roles — no database credentials needed. The pipeline in `pipeline/lib/pipeline-stack.ts` retrieves the GitHub connection ARN from SSM Parameter Store (`StringParameter.fromStringParameterName`).
- **Gap**: No AWS Secrets Manager usage. While no secrets currently need to be stored, the pattern for secret management is not established for future needs (API keys for external services, LLM provider keys).
- **Recommendation**: When adding Bedrock or external API integrations, store any API keys in AWS Secrets Manager and retrieve them at runtime. Avoid environment variables for sensitive values.

#### SEC-Q2: IAM Least Privilege
- **Score**: 2/4 🟠
- **Finding**: Lambda function IAM policies in `template.yml` are well-scoped: `GetAllBooks` uses `DynamoDBReadPolicy` scoped to `BooksTable`; `CreateBook` uses `DynamoDBWritePolicy` scoped to `BooksTable`; `CreateBookPreTraffic` uses `DynamoDBCrudPolicy` (broader, but for deployment smoke testing only). However, `pipeline/lib/pipeline-stack.ts` grants the deploy CodeBuild role extremely broad permissions: `IAMFullAccess`, `AWSCloudFormationFullAccess`, `AmazonDynamoDBFullAccess`, `AWSLambda_FullAccess`, `AmazonAPIGatewayAdministrator`, `AWSCodeDeployFullAccess`, `AmazonCognitoPowerUser`.
- **Gap**: Pipeline deploy role uses wildcard managed policies. A compromised pipeline could access any IAM, Lambda, DynamoDB, or API Gateway resource in the account.
- **Recommendation**: Replace broad managed policies on the deploy role with custom IAM policies scoped to the specific resources the pipeline deploys (the `BooksApi*` stack resources only). Use `cdk-nag` to catch overly permissive policies.

#### SEC-Q3: Identity Propagation
- **Score**: 2/4 🟠
- **Finding**: `template.yml` configures a `CognitoAuth` authorizer on the `CreateBook` endpoint with `AuthorizationScopes: [email]`. Cognito validates the OAuth2 token at the API Gateway layer. The Cognito user identity is available in the Lambda event `requestContext.authorizer.claims` but is not extracted or used in `src/books/create/index.ts` — the function creates books without recording who created them.
- **Gap**: User identity is validated but not propagated into the data layer. No audit trail of which user created which book. Agent actions will lack user attribution.
- **Recommendation**: Extract the user identity from the Cognito claims in the Lambda event and store it with the book record (e.g., `createdBy` field). This enables agent action attribution — "Agent acting on behalf of user X created book Y."

#### SEC-Q4: Audit Logging
- **Score**: 1/4 ❌
- **Finding**: No CloudTrail configuration in `template.yml`. API Gateway logging is enabled (`LoggingLevel: INFO` in `MethodSettings`). CloudWatch alarms exist for Lambda errors. No immutable log storage (no S3 bucket with object lock for logs). No centralized log aggregation.
- **Gap**: No CloudTrail for API-level audit logging. No immutable log storage. Agent actions will not be auditable.
- **Recommendation**: Enable CloudTrail with log file validation and ship logs to an S3 bucket with object lock. For agent auditing, log every tool invocation with user context, action, and outcome.

#### SEC-Q5: API Rate Limits
- **Score**: 1/4 ❌
- **Finding**: No explicit rate limiting in `template.yml`. No `ThrottlingBurstLimit`, `ThrottlingRateLimit`, usage plans, API keys, or WAF rules configured on `BooksApi`. Default API Gateway account-level throttling (10,000 RPS) is the only protection.
- **Gap**: No per-client rate limiting. Agent clients could consume all available throughput without controls.
- **Recommendation**: Add usage plans with API keys for different client types (web frontend, mobile app, agent). Set per-key throttle limits to prevent any single agent from monopolizing the API.

#### SEC-Q6: PII Redaction
- **Score**: 1/4 ❌
- **Finding**: No log scrubbing, PII masking, or data classification found. Lambda functions in `src/books/create-pre-traffic/index.ts` use `console.log` to log DynamoDB items and CodeDeploy events without any PII filtering. Error handlers in `src/books/create/index.ts` and `src/books/get-all/index.ts` catch exceptions silently without logging — but also without redaction logic.
- **Gap**: No PII protection framework. When expanding to customer support and order management, agent interactions will contain customer PII (names, emails, order details) that must be redacted from logs.
- **Recommendation**: Implement structured logging with a PII redaction middleware. Use Amazon Macie or CloudWatch Logs data protection to detect and mask PII in logs automatically.

#### SEC-Q7: Human Approval Workflows
- **Score**: 2/4 🟠
- **Finding**: `pipeline/lib/pipeline-stack.ts` includes a `ManualApprovalAction` in the Production stage that gates production deployments with the note: "Ensure Books API works correctly in Staging and release date is agreed with Product Owners." This provides human-in-the-loop for deployments but no application-level approval for high-risk actions.
- **Gap**: No human approval workflow for application-level high-risk actions (e.g., bulk book deletions, customer data modifications). Agent-initiated actions that modify data have no human approval gate.
- **Recommendation**: Implement human-in-the-loop approval for high-risk agent actions using Step Functions with `waitForTaskToken`. For example, an agent requesting to delete a book or modify an order should trigger an approval workflow that notifies a human reviewer.

#### SEC-Q8: Encryption at Rest
- **Score**: 3/4 🟡
- **Finding**: DynamoDB table has `SSESpecification.SSEEnabled: true` in `template.yml` (AWS-managed encryption). S3 artifact buckets in `pipeline/lib/pipeline-stack.ts` use `BucketEncryption.S3_MANAGED`. All data at rest is encrypted with AWS-managed keys.
- **Gap**: No customer-managed KMS keys. AWS-managed encryption provides good baseline but no key rotation control or cross-account access management.
- **Recommendation**: For sensitive customer data (support tickets, order details), consider customer-managed KMS keys on DynamoDB and S3. This provides fine-grained access control via key policies and automatic annual rotation.

#### SEC-Q9: API Authentication
- **Score**: 2/4 🟠
- **Finding**: `CreateBook` endpoint requires Cognito authentication (`CognitoAuth` authorizer with `email` scope). `GetAllBooks` endpoint is public — no authentication required. `template.yml` defines the auth configuration with scopes differentiated by environment (`aws.cognito.signin.user.admin` scope added in staging for testing).
- **Gap**: Mixed authentication posture. The read endpoint is open to the public. While this may be intentional for a book catalog, agent endpoints should all require authentication to ensure action attribution and access control.
- **Recommendation**: Add authentication to all endpoints that agents will invoke. Create a dedicated OAuth2 client for agent authentication with specific scopes (e.g., `agent:read`, `agent:write`) that differ from human user scopes.

#### SEC-Q10: Centralized Identity
- **Score**: 3/4 🟡
- **Finding**: `template.yml` defines an `AWS::Cognito::UserPool` (`CognitoUserPool`) with email-based sign-up, a `UserPoolClient` supporting OAuth2 implicit grant, and a `UserPoolDomain` for hosted UI. This provides centralized identity management for the Books API.
- **Gap**: No SSO configuration. No federation with external identity providers (SAML/OIDC). Cognito is configured but limited to direct user registration. Agent-to-service authentication patterns are not defined.
- **Recommendation**: Configure Cognito identity federation for SSO if integrating with corporate identity providers. For agent authentication, use Cognito machine-to-machine (M2M) auth with client credentials grant instead of implicit grant.

### Operations & Observability

#### OPS-Q1: Distributed Tracing
- **Score**: 3/4 🟡
- **Finding**: X-Ray tracing is enabled across the stack. `template.yml` sets `Tracing: Active` in the `Globals.Function` section for all Lambda functions and `TracingEnabled: true` on `BooksApi`. `src/books/get-all/index.ts` and `src/books/create/index.ts` both import `aws-xray-sdk-core` and instrument the AWS SDK with `AWSXRay.captureAWS(AWSCore)`. Trace IDs propagate from API Gateway through Lambda to DynamoDB via the X-Amzn-Trace-Id header.
- **Gap**: No `gen_ai.*` semantic conventions for LLM span tracing. X-Ray captures AWS SDK calls but will not automatically trace Bedrock model invocations with input/output token details. No OpenTelemetry integration.
- **Recommendation**: When adding agent capabilities, extend tracing to capture LLM spans with `gen_ai.*` semantic conventions (model ID, input tokens, output tokens, latency). Consider migrating to OpenTelemetry with the AWS X-Ray exporter for richer instrumentation.

#### OPS-Q2: Structured Logging
- **Score**: 1/4 ❌
- **Finding**: `src/books/create-pre-traffic/index.ts` uses `console.log()` for all logging (e.g., `console.log('Entering PreTraffic Hook!')`, `console.log('DynamoDB item', JSON.stringify(Item, null, 2))`). The main Lambda handlers (`src/books/create/index.ts`, `src/books/get-all/index.ts`) have no logging at all — errors are silently caught and return empty 500 responses. No JSON log formatters (winston, pino, structlog), no correlation ID middleware, no structured log fields.
- **Gap**: No structured logging. Debugging agent interactions will be extremely difficult without JSON-formatted logs with correlation IDs, request context, and trace IDs.
- **Recommendation**: Adopt AWS Lambda Powertools for TypeScript which provides structured JSON logging with automatic correlation ID injection, X-Ray trace ID inclusion, and log level control. Apply to all Lambda handlers.

#### OPS-Q3: Automated Evals
- **Score**: 1/4 ❌
- **Finding**: No agent evaluation framework, eval datasets, scoring scripts, LLM-as-judge patterns, or golden dataset files found anywhere in the repository. The existing test suites (unit tests in `src/books/create/tests/index.spec.ts` and `src/books/get-all/tests/index.spec.ts`; e2e tests in `src/books/tests/index.js`) test CRUD operations only.
- **Gap**: No mechanism to evaluate agent response quality, accuracy, or safety. Customer-facing agents require automated evaluation before deployment to prevent hallucinations and incorrect responses.
- **Recommendation**: Create an `evals/` directory with golden datasets for expected agent interactions. Implement an eval pipeline that runs after staging deployment (add a new buildspec stage) using Amazon Bedrock evaluation APIs or a custom scoring script that validates agent outputs against expected responses.

#### OPS-Q4: SLOs
- **Score**: 2/4 🟠
- **Finding**: `template.yml` defines two CloudWatch alarms: `CreateBookAliasErrorMetricGreaterThanZeroAlarm` and `GetAllBooksAliasErrorMetricGreaterThanZeroAlarm`. These monitor Lambda function errors (Errors > 0 over 2 evaluation periods of 60 seconds). These trigger deployment rollback but are not SLO definitions.
- **Gap**: No formal SLO definitions with error budgets. No latency SLOs (p99/p95). No SLO dashboards or burn-rate alerts. Basic error threshold alarms are reactive, not SLO-driven.
- **Recommendation**: Define SLOs for critical user journeys: "GET /books responds within 200ms at p99 with 99.9% availability" and "POST /books responds within 500ms at p99 with 99.9% availability." Create CloudWatch SLO dashboards and burn-rate alarms.

#### OPS-Q5: Rollback Capability
- **Score**: 3/4 🟡
- **Finding**: `template.yml` configures `DeploymentPreference: Linear10PercentEvery1Minute` for production with CloudWatch alarm-based rollback. `CreateBook` has a `PreTraffic` hook (`CreateBookPreTraffic` Lambda) that performs a smoke test before traffic shifting. Staging uses `AllAtOnce` deployment. The pipeline includes manual approval before production.
- **Gap**: Rollback covers code deployments only. No configuration rollback (e.g., DynamoDB table schema changes) and no prompt/template rollback mechanism for future agent configurations.
- **Recommendation**: When adding agent capabilities, implement prompt versioning with rollback (store prompt templates in DynamoDB with version numbers, enable rollback by switching to previous version). Consider feature flags for gradual agent feature rollout.

#### OPS-Q6: LLM Cost Tracking
- **Score**: 1/4 ❌
- **Finding**: No LLM usage in the current application, so no token tracking, cost attribution, or telemetry retention policies exist. No Bedrock, OpenAI, or any LLM API calls found.
- **Gap**: No infrastructure for LLM cost tracking. Customer-facing agents will generate significant LLM costs that need per-request, per-user, and per-workflow attribution.
- **Recommendation**: When integrating Bedrock, instrument every LLM call to capture `inputTokens`, `outputTokens`, `modelId`, and `latencyMs`. Publish as CloudWatch custom metrics with dimensions for `userId`, `agentName`, and `workflowType`. Implement tiered log retention (30 days for agent traces, 90 days for cost data).

#### OPS-Q7: Business Metrics
- **Score**: 1/4 ❌
- **Finding**: No custom business metrics found. Only infrastructure metrics (Lambda error counts) are tracked via CloudWatch alarms. No `cloudwatch.put_metric_data` calls, no business KPI dashboards, no tracking of books created, books retrieved, or user engagement.
- **Gap**: No business outcome visibility. Agent effectiveness cannot be measured without business metrics (resolution rate, customer satisfaction, task completion rate).
- **Recommendation**: Add custom CloudWatch metrics for key business events: `BooksCreated`, `BooksRetrieved`, `APIErrors` by type. For agents, add `AgentTaskCompleted`, `AgentTaskFailed`, `AgentResponseTime`, `CustomerSatisfactionScore`.

#### OPS-Q8: Anomaly Detection
- **Score**: 1/4 ❌
- **Finding**: CloudWatch alarms use static thresholds only (Errors > 0). No CloudWatch anomaly detection, no latency alarms, no behavioral baseline monitoring. No PagerDuty, OpsGenie, or alerting integration found.
- **Gap**: No anomaly detection. Agents can silently degrade (increased hallucination rate, slower responses, reasoning loops) without triggering static threshold alerts. Machine-speed harm from misconfigured agents requires fast MTTD.
- **Recommendation**: Enable CloudWatch anomaly detection on key metrics (latency p99, error rate, invocation count). For agent workloads, add anomaly detection on tool call count per request (detect reasoning loops), response token count (detect verbose/hallucinating agents), and task success rate.

#### OPS-Q9: Deployment Strategy
- **Score**: 4/4 ✅
- **Finding**: Production deployments use `Linear10PercentEvery1Minute` canary deployment with CloudWatch alarm-triggered rollback in `template.yml`. `CreateBook` has a `PreTraffic` hook for smoke testing. `pipeline/lib/pipeline-stack.ts` includes `ManualApprovalAction` before production deployment. Staging uses `AllAtOnce` for rapid iteration.
- **Gap**: None. Excellent deployment strategy with canary, smoke testing, alarm-based rollback, and manual approval.
- **Recommendation**: Extend the canary deployment pattern to agent Lambda functions. Consider adding specific agent eval checks (golden dataset pass rate) as rollback criteria alongside error rate alarms.

#### OPS-Q10: Integration Testing
- **Score**: 3/4 🟡
- **Finding**: End-to-end test suite exists in `src/books/tests/index.js` with 5 tests covering both endpoints: GET /books (public access, returns books), POST /books (requires auth, creates book, validates schema). Tests use real API endpoints, Cognito authentication, and DynamoDB. Tests run automatically in the CI pipeline via `pipeline/buildspec-test.json` as part of the Staging stage. Unit tests exist for `create` and `get-all` functions using Mocha, Sinon, and aws-sdk-mock.
- **Gap**: No contract tests. No agent-specific integration tests. Test coverage is limited to CRUD operations.
- **Recommendation**: When adding agent capabilities, create integration tests that validate agent tool invocations end-to-end (agent receives query → calls correct tool → returns accurate response). Add contract tests to ensure API changes don't break agent tool definitions.

#### OPS-Q11: Incident Response Automation
- **Score**: 1/4 ❌
- **Finding**: No runbooks, SSM Automation documents, or Lambda-based remediation functions found. The only automated responses are deployment rollback (triggered by CloudWatch alarms) and the pre-traffic smoke test. No self-healing patterns, no incident workflow automation.
- **Gap**: No incident response automation. Agent failures will require manual investigation and remediation. No machine-readable runbooks for agent-specific failure modes (model timeouts, token limit exceeded, tool failures).
- **Recommendation**: Create runbooks for common failure scenarios (DynamoDB throttling, Lambda timeouts, API Gateway 5xx spikes). For agent-specific incidents, create SSM Automation documents for "agent response degradation" (auto-switch to fallback model) and "agent cost spike" (auto-reduce max token limits).

#### OPS-Q12: Observability Governance & Ownership
- **Score**: 1/4 ❌
- **Finding**: No SLO definition files, no CODEOWNERS file, no platform team tooling, no per-service dashboards defined in IaC. No evidence of observability ownership model or shared responsibility.
- **Gap**: No observability governance. When adding agent capabilities, there will be no established ownership for agent-level SLOs (task success rate, hallucination rate, tool error rate) or accountability for agent quality in production.
- **Recommendation**: Create a CODEOWNERS file. Define an observability-as-code approach: CloudWatch dashboards and alarms defined in `template.yml`. Establish ownership for agent-level SLOs alongside existing service-level metrics.

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

**Parallel Track 1**: Move to AI (the only triggered pathway — can proceed immediately)

**Sequential Dependencies**: None. The existing serverless infrastructure (Lambda, DynamoDB, API Gateway, CI/CD) is already well-suited for AI integration. No prerequisite pathways need to be completed before beginning the Move to AI pathway.

**Note on untriggered pathways**: The remaining 6 pathways are not triggered because the existing serverless architecture already satisfies their criteria:
- **Move to Cloud Native**: APP-Q4 = 3 (already modular serverless architecture). Guard fails.
- **Move to Containers**: INF-Q1 = 4 (already serverless Lambda). Guard fails. Absence of Dockerfile is expected for serverless workloads.
- **Move to Open Source**: No commercial databases (DynamoDB is AWS-native). DATA-Q11 = 4.
- **Move to Managed Databases**: All databases are fully managed DynamoDB. Guard fails.
- **Move to Managed Analytics**: No data processing, ETL, analytics, or self-managed streaming detected. Guard fails.
- **Move to Modern DevOps**: INF-Q5 = 4, INF-Q6 = 4, OPS-Q9 = 4, OPS-Q10 = 3, OPS-Q1 = 3 — all trigger criteria ≥ 3.

### Move to AI

- **Priority**: High
- **Goal Alignment**: High
- **Trigger Criteria Met**:
  - APP-Q13: Score 1/4 — No AI/agent framework dependencies found in any package.json
  - DATA-Q1: Score 1/4 — No vector database (OpenSearch, pgvector, Bedrock Knowledge Bases)
  - DATA-Q3: Score 1/4 — No RAG pipeline (no embeddings, chunking, or semantic search)
  - OPS-Q3: Score 1/4 — No automated agent evaluation framework
  - OPS-Q6: Score 1/4 — No LLM cost tracking infrastructure
- **Current State**: The Books API is a serverless CRUD application with no AI capabilities. It has strong infrastructure foundations (Lambda, DynamoDB, API Gateway, full CI/CD) but no agent integration, knowledge base, or AI observability.
- **Target State**: A customer-facing AI agent that can discover and invoke the Books API tools via OpenAPI spec, answer semantic queries about the book catalog using RAG, handle support inquiries with grounded responses, and be monitored via automated evals and cost tracking.
- **Key Activities**:
  1. Generate an OpenAPI specification for the Books API endpoints
  2. Add agent orchestration framework (Strands Agents SDK or LangChain.js)
  3. Deploy Amazon Bedrock Knowledge Base with book catalog embeddings
  4. Create an agent Lambda function that uses Bedrock for inference and the Books API as tools
  5. Implement agent evaluation pipeline with golden datasets
  6. Add LLM cost tracking with per-user attribution
  7. Implement human-in-the-loop approval for high-risk agent actions
- **Dependencies**: None — existing infrastructure is already suitable
- **Estimated Effort**: High (all 5 trigger criteria scored 1/4, requiring net-new capabilities)
- **Roadmap Phase Alignment**: Phase 1 (Agent Quick Wins), Phase 2 (Agent Foundations), Phase 3 (Agent Scale & Optimization)
- **Relevant Learning Materials**: Module 7 — Move to AI

---

## Microservices Decomposition Strategy

This serverless architecture with function-level separation (separate Lambda functions for `GetAllBooks` and `CreateBook`) would benefit from service extraction to create clear agent tool boundaries as the system grows to support order management. See the Move to Cloud Native pathway for detailed decomposition guidance. For now, agents can interact with the application via its existing API surface — the `GET /books` and `POST /books` endpoints provide clean, invocable tool interfaces for an AI agent.

---

## Quick Agent Wins

Even before completing the full modernization roadmap, these agent opportunities are available based on your current architecture:

1. **Customer Support Agent with JSON API Tools** — Your Books API returns structured JSON responses (`Content-Type: application/json`) from both endpoints, making it straightforward to wrap `GET /books` and `POST /books` as agent tools. A customer support agent could use these to answer questions like "What books do you have?" or "Add this book to the catalog."
   - **Leverages**: Structured JSON responses from `src/books/get-all/index.ts` and `src/books/create/index.ts`
   - **Effort**: Low
   - **Value**: Demonstrates agent-powered customer interaction with the book catalog immediately

2. **Knowledge Agent Using Existing Documentation** — Your `README.md` contains detailed architecture documentation, API usage instructions, authentication flows, and local testing guides. This documentation can be ingested into a RAG pipeline to build a developer support agent that answers questions about the Books API.
   - **Leverages**: `README.md` with comprehensive architecture and usage documentation
   - **Effort**: Low-Medium
   - **Value**: Internal developer support agent that reduces onboarding time and answers "how do I use the Books API?" questions

3. **DevOps Agent for Deployment Management** — Your fully automated CI/CD pipeline (CodePipeline with Source → Build → Staging → Production stages) can be wrapped as agent tools. A DevOps agent could trigger deployments, check pipeline status, and report on deployment health.
   - **Leverages**: CDK-defined CodePipeline in `pipeline/lib/pipeline-stack.ts` with 4 automated stages
   - **Effort**: Medium
   - **Value**: Enables natural language deployment management: "Deploy the latest version to staging" or "What's the status of the last production deployment?"

> These opportunities can be pursued in parallel with the modernization roadmap.
> They demonstrate agent value early while foundations are being built.

---

## Readiness Roadmap

### Phase 1 — Agent Quick Wins (Days 1–30)

Low-effort, high-impact actions that establish the foundation for customer-facing AI agents:

1. **Generate OpenAPI Specification** — Create an `openapi.yaml` documenting `GET /books` (response schema: array of Book objects) and `POST /books` (request schema: Book object with isbn, title, year, author, publisher, rating, pages). Reference it in `template.yml` using `DefinitionBody`. This is the single most impactful action — it enables agent tool discovery.

2. **Add Structured Logging** — Adopt AWS Lambda Powertools for TypeScript across all Lambda handlers. Replace `console.log` with structured JSON logging that includes correlation IDs, X-Ray trace IDs, and request context. This is foundational for debugging agent interactions.

3. **Add API Versioning** — Rename API paths from `/books` to `/v1/books` in `template.yml`. This ensures agent tool definitions remain stable across API changes.

4. **Add Idempotency to CreateBook** — Add `ConditionExpression: "attribute_not_exists(isbn)"` to the DynamoDB `putItem` call in `src/books/create/index.ts`. This prevents agent retries from corrupting data.

5. **Add Rate Limiting** — Configure explicit throttle settings and usage plans on `BooksApi` in `template.yml`. Create API keys for different client types (human users, agents).

### Phase 2 — Agent Foundations (Months 1–3)

Structural investments that enable robust agent capabilities:

1. **Deploy Agent Framework** — Add Strands Agents SDK (or LangChain.js) as a dependency. Create a new Lambda function (`AgentHandler`) that uses Amazon Bedrock for inference and defines the Books API endpoints as callable tools using the OpenAPI spec from Phase 1.

2. **Build Knowledge Base (RAG Pipeline)** — Create an Amazon Bedrock Knowledge Base backed by OpenSearch Serverless. Export book catalog data from DynamoDB to S3 (as JSON documents). Configure automated embedding generation using Amazon Titan Embeddings. This enables the customer support agent to answer semantic queries like "Find science fiction books published after 2020."

3. **Implement Agent Evaluation Pipeline** — Create an `evals/` directory with golden datasets for expected agent interactions. Add a new buildspec stage after staging deployment that runs agent evals. Define pass/fail criteria (e.g., 90% accuracy on golden dataset) as a deployment gate.

4. **Add Human-in-the-Loop Approvals** — Implement Step Functions with `waitForTaskToken` for high-risk agent actions (book creation, bulk operations). Agent requests for write operations are routed through an approval workflow that notifies a human reviewer via SNS.

5. **Improve Security Posture** — Enable CloudTrail with immutable log storage. Scope down pipeline IAM policies in `pipeline/lib/pipeline-stack.ts`. Add Cognito M2M auth for agent clients. Implement PII redaction in logging middleware.

6. **Implement Embedding Freshness** — Configure DynamoDB Streams on `BooksTable` → EventBridge Pipe → Lambda → Bedrock Knowledge Base sync to automatically refresh embeddings when books are added or updated.

### Phase 3 — Agent Scale & Optimization (Months 3–6)

Advanced capabilities that optimize agent quality, cost, and reliability at scale:

1. **LLM Cost Tracking & Attribution** — Instrument all Bedrock calls to capture token usage (input/output tokens, model ID, latency). Publish as CloudWatch custom metrics with dimensions for userId, agentName, and workflowType. Implement tiered log retention policies.

2. **Anomaly Detection for Agent Behavior** — Enable CloudWatch anomaly detection on agent metrics: tool call count per request (detect reasoning loops), response token count (detect verbose outputs), task success rate, and latency p99. Configure alerts for behavioral anomalies.

3. **Define Agent-Level SLOs** — Establish SLOs for agent interactions: "Customer support agent responds within 5 seconds at p99", "Agent task success rate ≥ 95%", "Agent hallucination rate ≤ 2%." Create CloudWatch dashboards and burn-rate alarms.

4. **Expand to Order Management Domain** — Add new DynamoDB tables (Orders, Customers) with separate Lambda functions per domain. Define new agent tools for order lookup, order status, and customer support actions. Maintain clear bounded contexts for each domain.

5. **Implement Incident Response Automation** — Create SSM Automation runbooks for agent-specific failure modes: model timeout (auto-switch to fallback model), cost spike (auto-reduce max token limits), degraded accuracy (auto-disable agent, route to human support).

6. **Observability Governance** — Create a CODEOWNERS file. Define all dashboards and alarms in IaC. Establish shared responsibility model for agent SLOs between platform and product teams.

---

## Recommended Self-Paced Learning Materials

**Module 7: Move to AI** *(Primary — directly addresses the triggered pathway)*

- AWS Modernization Pathways: Move to AI — https://skillbuilder.aws/learning-plan/VDFEE4ACCV/aws-modernization-pathways-move-to-ai-pathways-includes-labs/P3DAWPTN63
  - Comprehensive learning plan covering AI integration patterns for modernized applications
- Introduction to Generative AI: Art of the Possible — https://skillbuilder.aws/learn/ZEVZZ1D4AS/introduction-to-generative-ai--art-of-the-possible/Y7MTGJCW1U
  - Understand generative AI capabilities and identify use cases for customer support agents
- Planning a Generative AI Project — https://skillbuilder.aws/learn/HU1FQRGDDZ/planning-a-generative-ai-project/SYR3SCPSHC
  - Framework for planning the customer-facing AI agent project
- Amazon Bedrock Getting Started — https://skillbuilder.aws/learn/63KTRM86DQ/amazon-bedrock-getting-started/SC2Y3HMAUE
  - Essential for integrating Bedrock as the LLM inference layer for agents
- Essentials for Prompt Engineering — https://skillbuilder.aws/learn/XBNAVKA88J/essentials-of-prompt-engineering/9T9Q45EDTV
  - Critical for designing effective prompts for customer support agent interactions
- Build and Evaluate Retrieval Augmented Generation (RAG) Applications using Knowledge Bases for Amazon Bedrock (Lab) — https://skillbuilder.aws/learn/JRGWCFYT67/lab--build-and-evaluate-retrieval-augmented-generation-rag-applications-using-knowledge-bases-for-amazon-bedrock/A4MN58JB7A
  - Hands-on lab directly applicable to building the book catalog RAG pipeline
- Introduction to Agentic AI on AWS — https://skillbuilder.aws/learn/DNBD5MT8ZD/introduction-to-agentic-ai-on-aws/WAKAFK6UFY
  - Covers agentic AI concepts and AWS-native agent building approaches
- Creating an AWS DevOps AI Agent with the Strands Agents SDK (Lab) — https://skillbuilder.aws/learn/AH1GD8AJY3/lab--creating-an-aws-devops-ai-agent-with-the-strands-agents-sdk/A9SKJNMPJ2
  - Practical lab for building agents with the Strands SDK, directly applicable to this project
- AWS PartnerCast: Deep Dive: Building Observable AI Agents with Strands, Amazon Bedrock Agent Core & SageMaker MLflow — https://skillbuilder.aws/learn/1EN76TZBB6/aws-partnercast--deep-dive-building-observable-ai-agents-with-strands-amazon-bedrock-agent-core--sagemaker-mlflow--technical/CX2K6XAT84
  - Covers agent observability patterns needed for OPS-Q3 and OPS-Q6 gaps

**Module 6: Move to Modern DevOps** *(Supporting — addresses observability and operational gaps)*

- AWS Modernization Pathways: Move to Modern DevOps — https://skillbuilder.aws/learning-plan/1FGEQKGPQD/aws-modernization-pathways-move-to-modern-devops-includes-labs/MNQZ2KPVCK
  - Covers modern DevOps practices for improving observability and deployment patterns
- Advanced Testing Practices Using AWS DevOps Tools — https://skillbuilder.aws/learn/1YC7UXUWBR/advanced-testing-practices-using-aws-devops-tools/A32U6G7NEQ
  - Useful for building the agent evaluation pipeline and extending the CI/CD pipeline
- DevOps and AI on AWS: CloudWatch Anomaly Detection (Lab) — https://skillbuilder.aws/learn/RWYVJ73MXP/lab--devops-and-ai-on-aws-cloudwatch-anomaly-detection/BRPDNZUGU7
  - Directly applicable to OPS-Q8 (anomaly detection for agent behavior monitoring)
- Introduction to AWS DevOps Agent (Lab) — https://skillbuilder.aws/learn/2BMGKG58ZU/introduction-to-aws-devops-agent/S61EE8J7S9
  - Demonstrates how to use AI agents for DevOps tasks, relevant to the DevOps Agent quick win

**Module 4: Move to Managed Databases** *(Supporting — vector database knowledge)*

- AWS PartnerCast: Vector Databases for Generative AI Applications — https://skillbuilder.aws/learn/UQ74USQJHU/aws-partnercast--vector-databases-for-generative-ai-applications--technical/7DKMBAPCST
  - Covers vector database concepts directly relevant to DATA-Q1 and DATA-Q2 gaps

---

## Appendix: Evidence Index

| # | File | Key Findings |
|---|------|-------------|
| 1 | `template.yml` | SAM template defining all infrastructure: 3 Lambda functions (nodejs22.x), DynamoDB SimpleTable with SSE, API Gateway with Cognito auth, CloudWatch alarms, canary deployment configuration, X-Ray tracing enabled |
| 2 | `pipeline/lib/pipeline-stack.ts` | CDK-defined 4-stage CodePipeline (Source → Build → Staging → Production), ManualApprovalAction for production, overly permissive IAM (IAMFullAccess, etc.) on deploy role |
| 3 | `src/books/get-all/index.ts` | Lambda handler for GET /books. Direct DynamoDB scan via AWS SDK. X-Ray instrumentation with `AWSXRay.captureAWS()`. Returns JSON array of books. No structured logging. |
| 4 | `src/books/create/index.ts` | Lambda handler for POST /books. Direct DynamoDB putItem. No idempotency (no ConditionExpression). No input validation. Silent 500 on error with empty body. |
| 5 | `src/books/create-pre-traffic/index.ts` | Pre-traffic hook for canary deployment. Invokes new Lambda version, verifies DynamoDB write, cleans up. Uses `console.log` for logging. |
| 6 | `src/books/get-all/package.json` | Dependencies: aws-sdk, aws-xray-sdk-core. DevDeps: mocha, sinon, chai, typescript. No AI/agent/resilience libraries. |
| 7 | `src/books/create/package.json` | Dependencies: aws-sdk, aws-xray-sdk-core. Same pattern as get-all. No idempotency or validation libraries. |
| 8 | `src/books/create-pre-traffic/package.json` | Dependencies: aws-sdk only. Minimal deployment utility. |
| 9 | `src/books/tests/index.js` | E2E test suite: 5 tests covering GET /books (public, returns books) and POST /books (auth required, creates book). Uses Cognito programmatic auth. |
| 10 | `src/books/tests/books-manager.js` | DynamoDB test helper with save/remove/get functions. Shows duplicated schema mapping logic (same Book schema as Lambda handlers). |
| 11 | `src/books/tests/package.json` | E2E test deps: axios, aws-sdk, uuid, mocha, chai. No agent testing frameworks. |
| 12 | `pipeline/buildspec.json` | Build stage: installs SAM CLI, runs unit tests for create and get-all, builds with SAM, packages artifacts to S3. |
| 13 | `pipeline/buildspec-deploy.json` | Deploy stage: pulls artifacts from S3, runs sam deploy, exports CloudFormation outputs (API endpoint, UserPoolId, etc.). |
| 14 | `pipeline/buildspec-test.json` | Test stage: runs E2E tests against deployed staging environment. Confirms integration testing in CI. |
| 15 | `pipeline/package.json` | CDK pipeline deps: aws-cdk-lib, constructs. No agent or AI infrastructure libraries. |
| 16 | `events/create-book-request.json` | Sample API Gateway event for local testing. Shows book schema: isbn, title, year, author, publisher, rating, pages. |
| 17 | `events/env.json` | Environment variable overrides for local testing. TABLE=books for both functions. |
| 18 | `README.md` | Comprehensive documentation: architecture, deployment, testing, CI/CD, Cognito auth flow. No OpenAPI spec reference. |
| 19 | `src/books/create/tests/index.spec.ts` | Unit tests for CreateBook: 3 tests covering happy path, invalid body, DynamoDB failure. Uses aws-sdk-mock. |
| 20 | `src/books/get-all/tests/index.spec.ts` | Unit tests for GetAllBooks: 3 tests covering books returned, empty result, DynamoDB failure. Uses aws-sdk-mock. |
