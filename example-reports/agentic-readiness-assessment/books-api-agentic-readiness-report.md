# Agentic Readiness Assessment Report
**Target**: ./services/books-api
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
6. Microservices Decomposition Strategy
7. Quick Agent Wins
8. Readiness Roadmap
   - Phase 1 — Agent Quick Wins (Days 1–30)
   - Phase 2 — Agent Foundations (Months 1–3)
   - Phase 3 — Agent Scale & Optimization (Months 3–6)
9. Recommended Self-Paced Learning Materials
10. Appendix: Evidence Index

---

## Executive Summary

This Books API is a well-architected serverless application with strong foundations in compute (100% Lambda), managed data (DynamoDB), CI/CD (CodePipeline with gradual deployment), and testing (unit + end-to-end). However, it is not yet ready for agentic AI enablement: there are no AI/agent frameworks, no vector database or RAG pipeline, no OpenAPI specification for agent tool discovery, and no structured logging or observability infrastructure to monitor agent behavior. To enable customer-facing AI agents for support and order management, the immediate priorities are generating an OpenAPI spec, introducing a vector database for semantic search, and adopting an agent framework such as Strands Agents or LangChain.js.

### Overall Score: 2.1 / 4.0

| Category | Score | Status |
|----------|-------|--------|
| Infrastructure & Platform | 2.7 / 4.0 | 🟡 |
| Application Architecture | 1.9 / 4.0 | 🟠 |
| Data Foundations | 2.0 / 4.0 | 🟠 |
| Identity, Security & Governance | 2.1 / 4.0 | 🟠 |
| Operations & Observability | 1.9 / 4.0 | 🟠 |

---

## Top Priorities (Critical Gaps)

**1. APP-Q13 — No AI/Agent Frameworks (Score: 1/4)** ⭐ *Agentic Priority*
No AI or agent framework imports found in any `package.json`. Dependencies are limited to `aws-sdk` and `aws-xray-sdk-core`. Without Bedrock, LangChain, or Strands Agents integration, there is no foundation for building customer-facing AI agents for support and order management. **First step**: Add `@aws-sdk/client-bedrock-runtime` and `strands-agents` to the project; create a proof-of-concept agent Lambda that can invoke the existing Books API endpoints as tools.

**2. APP-Q2 — No API Documentation (Score: 1/4)** ⭐ *Agentic Priority*
No OpenAPI or Swagger specification found. The `template.yml` references `OpenApiVersion: 3.0.1` in Globals but defines no actual spec. Agents rely on API descriptions to discover and invoke tools — without an OpenAPI spec, an agent cannot understand what endpoints exist, what parameters they accept, or what responses to expect. **First step**: Generate an OpenAPI 3.0 specification from the SAM template's API event definitions (GET /books, POST /books with request body schema).

**3. DATA-Q1 — No Vector Database (Score: 1/4)** ⭐ *Agentic Priority*
No vector database (OpenSearch, pgvector, Pinecone, Chroma, Bedrock Knowledge Base) found in IaC or dependencies. For customer support and order management agents, semantic search over book catalog data and support documentation is essential for RAG-based responses. **First step**: Create an Amazon Bedrock Knowledge Base backed by S3 and OpenSearch Serverless for catalog and support document retrieval.

**4. DATA-Q3 — No RAG Implementation (Score: 1/4)** ⭐ *Agentic Priority*
No embedding model calls, document chunking, or similarity search patterns found anywhere in the codebase. RAG is the primary mechanism for grounding agent responses in actual catalog data and support policies. **First step**: Implement a RAG pipeline using Bedrock Knowledge Bases with Titan Embeddings, chunking book catalog data and any support documentation for semantic retrieval.

**5. OPS-Q3 — No Automated Eval Framework (Score: 1/4)** ⭐ *Agentic Priority*
No agent evaluation framework, golden datasets, or scoring scripts found. Before deploying customer-facing AI agents, you need automated evaluation to measure response quality, hallucination rates, and task completion accuracy. **First step**: Create a golden evaluation dataset of customer support queries with expected answers; implement an automated eval pipeline using LLM-as-judge scoring.

---

## Detailed Findings

### Infrastructure & Platform

#### INF-Q1: Compute
- **Score**: 4/4 ✅
- **Finding**: All compute is AWS Lambda (serverless) with Node.js 22.x runtime. Three Lambda functions defined in `template.yml`: `CreateBook`, `GetAllBooks`, and `CreateBookPreTraffic`. No EC2 instances, no ECS/EKS. 100% serverless compute.
- **Gap**: None. Serverless compute is agent-ready.
- **Recommendation**: Maintain serverless-first approach. When adding agent Lambda functions, consider Provisioned Concurrency for latency-sensitive agent endpoints.

#### INF-Q2: Databases
- **Score**: 4/4 ✅
- **Finding**: `BooksTable` is defined as `AWS::Serverless::SimpleTable` (DynamoDB) in `template.yml` with `SSESpecification.SSEEnabled: true`. DynamoDB is fully managed with automatic failover, no maintenance windows, and on-demand scaling. No self-managed database software detected.
- **Gap**: None. Fully managed database.
- **Recommendation**: Maintain DynamoDB for transactional data. For agent conversation history, consider DynamoDB with TTL for session management.

#### INF-Q3: Workflow Orchestration
- **Score**: 1/4 ❌
- **Finding**: No workflow orchestration service found. No `AWS::StepFunctions::StateMachine`, no Temporal SDK imports, no workflow YAML definitions. Lambda handlers contain straightforward CRUD logic in `src/books/create/index.ts` and `src/books/get-all/index.ts`.
- **Gap**: No dedicated workflow orchestration. Agent workflows that span multiple tools (e.g., search catalog → check order → issue refund) will need coordinated orchestration.
- **Recommendation**: Introduce AWS Step Functions for multi-step agent workflows. Define agent task orchestration as state machines with error handling, retries, and human approval states.

#### INF-Q4: Async Messaging
- **Score**: 1/4 ❌
- **Finding**: No SQS, SNS, or EventBridge resources in `template.yml` or `pipeline-stack.ts`. No message queue SDK imports in Lambda handlers. All communication follows synchronous API Gateway → Lambda → DynamoDB pattern.
- **Gap**: No async messaging infrastructure. Agent workflows benefit from async processing for long-running tasks (e.g., order processing, bulk catalog updates).
- **Recommendation**: Add SQS queues for async agent task processing and EventBridge for event-driven agent triggers (e.g., new order events). SNS for notification workflows.

#### INF-Q5: Infrastructure as Code
- **Score**: 4/4 ✅
- **Finding**: `template.yml` (SAM/CloudFormation) defines all application infrastructure: Lambda functions, DynamoDB table, API Gateway, Cognito User Pool, CloudWatch Alarms, IAM roles. `pipeline/lib/pipeline-stack.ts` (CDK) defines the entire CI/CD pipeline: CodePipeline, CodeBuild projects, S3 artifact buckets. 100% IaC coverage.
- **Gap**: None. All infrastructure is code-defined.
- **Recommendation**: Continue IaC-first approach. When adding agent infrastructure (Bedrock, Knowledge Bases, vector stores), define them in SAM/CDK templates.

#### INF-Q6: CI/CD
- **Score**: 4/4 ✅
- **Finding**: Full CodePipeline defined in `pipeline/lib/pipeline-stack.ts` with 4 stages: Source (GitHub via CodeStar Connections) → Build (unit tests + SAM build via `buildspec.json`) → Staging (deploy + e2e tests via `buildspec-test.json`) → Production (manual approval + deploy via `buildspec-deploy.json`). Automated testing at both build and staging stages.
- **Gap**: None. Full CI/CD automation.
- **Recommendation**: Extend pipeline to include agent evaluation tests in the staging stage. Add a dedicated eval buildspec for running golden dataset evaluations against agent endpoints.

#### INF-Q7: API Entry Point
- **Score**: 3/4 🟡
- **Finding**: `BooksApi` (`AWS::Serverless::Api`) in `template.yml` provides API Gateway as the entry point with `CognitoAuth` authorizer on POST /books, `TracingEnabled: true`, and `MethodSettings` with `LoggingLevel: INFO`. API endpoint exposed via CloudFormation Output `ApiEndpoint`.
- **Gap**: No explicit throttling or rate limiting configuration. No WAF rules. No request validation at the gateway level.
- **Recommendation**: Add `ThrottlingBurstLimit` and `ThrottlingRateLimit` to the API stage. Add `RequestValidator` for POST /books to validate request body schema at the gateway layer before hitting Lambda.

#### INF-Q8: Real-time Streaming
- **Score**: 1/4 ❌
- **Finding**: No Kinesis, MSK, or streaming resources in IaC. No streaming SDK imports in application code. No event-driven streaming patterns.
- **Gap**: No real-time streaming. For customer support agents, real-time event streams (order status changes, inventory updates) would enable proactive agent notifications.
- **Recommendation**: Consider adding DynamoDB Streams or EventBridge for change-data-capture patterns. For real-time agent interactions, Kinesis Data Streams could stream agent conversation events for monitoring and analytics.

#### INF-Q9: Network Security
- **Score**: 2/4 🟠
- **Finding**: No VPC configuration in `template.yml`. Lambda functions run in AWS-managed networking (default). No explicit security groups, NACLs, or private subnet configurations. For a simple Lambda→DynamoDB architecture, VPC is not required (DynamoDB accessed via public endpoints with IAM auth).
- **Gap**: No network segmentation. When adding agent infrastructure that requires VPC (e.g., OpenSearch for vector DB, RDS for additional data stores), network security will need to be established.
- **Recommendation**: When expanding to VPC-bound resources, define VPC with public/private subnets, security groups with least-privilege rules, and VPC endpoints for AWS services (DynamoDB, S3, Bedrock).

#### INF-Q10: Auto-scaling
- **Score**: 3/4 🟡
- **Finding**: Lambda functions auto-scale automatically (inherent). DynamoDB `SimpleTable` uses on-demand billing mode by default (automatic scaling). No explicit Lambda reserved concurrency or provisioned concurrency configured in `template.yml`.
- **Gap**: No Lambda concurrency limits configured. Agent workloads can generate burst traffic; without reserved concurrency, a runaway agent could consume all account Lambda concurrency.
- **Recommendation**: Set `ReservedConcurrentExecutions` on Lambda functions to prevent noisy-neighbor issues. Consider Provisioned Concurrency for agent-facing Lambda functions to reduce cold start latency.

### Application Architecture

#### APP-Q1: Programming Languages
- **Score**: 3/4 🟡
- **Finding**: TypeScript is the primary language. Lambda handlers (`src/books/create/index.ts`, `src/books/get-all/index.ts`, `src/books/create-pre-traffic/index.ts`) and CDK pipeline (`pipeline/lib/pipeline-stack.ts`) are all TypeScript. E2E tests (`src/books/tests/index.js`) use JavaScript. Node.js 22.x runtime.
- **Gap**: TypeScript has a good agent framework ecosystem (LangChain.js, Strands Agents SDK) but Python has the most mature and broadest agent framework support.
- **Recommendation**: TypeScript is viable for agent development. Use `strands-agents` (TypeScript SDK) or `langchain-js` for agent implementation. No language migration needed.

#### APP-Q2: API Documentation
- **Score**: 1/4 ❌
- **Finding**: No OpenAPI/Swagger specification files found in the repository. `template.yml` sets `OpenApiVersion: 3.0.1` in `Globals.Api` but this is only to prevent SAM from creating a default stage — no actual OpenAPI definition body exists. API endpoints are defined implicitly through SAM `Events` sections on Lambda functions.
- **Gap**: No API documentation for agent tool discovery. Agents need machine-readable API descriptions to understand available operations, parameters, and response schemas. This is a critical blocker for agentic AI enablement.
- **Recommendation**: Generate an OpenAPI 3.0 specification defining GET /books and POST /books with request/response schemas. Embed it in `template.yml` via `DefinitionBody` or maintain a standalone `openapi.yaml`. Include detailed operation descriptions for agent consumption.

#### APP-Q3: Async vs Sync Communication
- **Score**: 1/4 ❌
- **Finding**: All communication is synchronous. `src/books/create/index.ts` performs synchronous `putItem` to DynamoDB. `src/books/get-all/index.ts` performs synchronous `scan`. API Gateway → Lambda → DynamoDB is a fully synchronous request-response chain. No SQS consumers, no EventBridge handlers, no async patterns.
- **Gap**: 100% synchronous communication. No async capability for long-running agent operations (e.g., batch catalog updates, complex order processing workflows).
- **Recommendation**: Introduce async patterns for operations that may exceed API Gateway's 29-second timeout when agent workflows are added. Use SQS for task queuing with status polling endpoints, or Step Functions for orchestrated async workflows.

#### APP-Q4: Monolith vs Microservices
- **Score**: 3/4 🟡
- **Finding**: The application uses a modular serverless architecture with independently deployable Lambda functions: `CreateBook` (write operations) and `GetAllBooks` (read operations), each with their own IAM policies scoped to specific DynamoDB operations (`DynamoDBWritePolicy` vs `DynamoDBReadPolicy`). Functions share a single `BooksTable` and a single SAM template (`template.yml`) for deployment. `CreateBookPreTraffic` serves as a deployment smoke test function. Clear function-level separation with no circular dependencies.
- **Gap**: Single deployment unit (one SAM template). Functions share a DynamoDB table directly. Not a microservices architecture, but the serverless function model provides natural modularity.
- **Recommendation**: The current serverless modular design provides good agent tool boundaries — each Lambda function can serve as a distinct agent tool. No immediate decomposition needed.

#### APP-Q5: API Response Format
- **Score**: 4/4 ✅
- **Finding**: Both handlers return structured JSON responses. `src/books/create/index.ts` returns `statusCode: 201` with `Content-Type: application/json`. `src/books/get-all/index.ts` returns `statusCode: 200` with `Content-Type: application/json` and a JSON array of book DTOs with fields: isbn, title, year, author, publisher, rating, pages.
- **Gap**: None. Structured JSON is ideal for agent consumption.
- **Recommendation**: Maintain JSON response format. When adding agent endpoints, use consistent JSON schemas with clear field descriptions.

#### APP-Q6: Workflow Logic
- **Score**: 2/4 🟠
- **Finding**: No workflow orchestration service. Lambda handlers contain straightforward single-operation CRUD logic: `create/index.ts` parses JSON body and calls `putItem`; `get-all/index.ts` calls `scan` and maps results. No complex business logic, no state machines, no multi-step processes.
- **Gap**: No orchestration for multi-step operations. Agent workflows for customer support (e.g., look up order → check inventory → process refund → notify customer) will require coordinated orchestration.
- **Recommendation**: Add AWS Step Functions for agent workflow orchestration. Express Workflows for synchronous agent tasks; Standard Workflows for long-running async operations with human approval gates.

#### APP-Q7: Idempotency
- **Score**: 2/4 🟠
- **Finding**: `src/books/create/index.ts` uses DynamoDB `putItem` with `isbn` as the primary key, which provides natural idempotency by key (re-putting the same isbn overwrites with identical data). However, no explicit `Idempotency-Key` header handling exists in the Lambda handler. No deduplication mechanism for API Gateway requests.
- **Gap**: No explicit idempotency support at the API layer. Agent retries on transient failures could create duplicate side effects for operations that don't have natural key-based idempotency.
- **Recommendation**: Add Powertools for AWS Lambda `@idempotent` decorator for write operations. Use DynamoDB-based idempotency store to track processed request IDs.

#### APP-Q8: Rate Limiting & Throttling
- **Score**: 1/4 ❌
- **Finding**: No API Gateway throttling configuration in `template.yml`. No `ThrottlingBurstLimit` or `ThrottlingRateLimit` on the API stage. No WAF rules. No rate limiting middleware in Lambda code. No `aws_api_gateway_usage_plan` equivalent.
- **Gap**: No rate limiting. Agent-generated traffic can be bursty and high-volume; without throttling, a malfunctioning agent could overwhelm the API and DynamoDB.
- **Recommendation**: Add throttling to `BooksApi` via `MethodSettings` or a usage plan. Set per-client rate limits. Consider adding AWS WAF for additional protection against abuse.

#### APP-Q9: Resilience Patterns
- **Score**: 1/4 ❌
- **Finding**: Lambda handlers in `src/books/create/index.ts` and `src/books/get-all/index.ts` use basic `try/catch` blocks that return `statusCode: 500` with empty body on any error. No circuit breakers, no retry logic with exponential backoff, no timeout configuration beyond the Lambda 5-second timeout. AWS SDK has default retry behavior but no custom retry configuration.
- **Gap**: No explicit resilience patterns. Agent tool calls that encounter transient DynamoDB errors will fail without intelligent retry. No circuit breaker to prevent cascade failures.
- **Recommendation**: Add Powertools for AWS Lambda for structured error handling. Configure AWS SDK retry with exponential backoff. Add circuit breaker pattern for external service calls when agent integrations are added.

#### APP-Q10: Long-running Processes
- **Score**: 3/4 🟡
- **Finding**: All operations are fast DynamoDB reads/writes. Lambda `Timeout` is set to 5 seconds in `template.yml` Globals. `CreateBook` performs a single `putItem`, `GetAllBooks` performs a single `scan`. No operations approach the 30-second threshold. `CreateBookPreTraffic` has a `wait(1500)` function for eventual consistency but this is only used during deployment smoke tests.
- **Gap**: No async pattern for potentially long-running operations. As the API grows (e.g., batch imports, order processing), async handling will be needed.
- **Recommendation**: Maintain current synchronous approach for simple CRUD. When adding agent operations that may be long-running (e.g., multi-step agent workflows), implement async with Step Functions or SQS + polling.

#### APP-Q11: API Versioning
- **Score**: 1/4 ❌
- **Finding**: No API versioning detected. Endpoints are `/books` with no version prefix. No `Accept-Version` headers. No versioning annotations or changelog files. API Gateway stage name is used for environment separation (staging/production), not versioning.
- **Gap**: No versioning strategy. When agents are built against the API, breaking changes would disrupt agent tool integrations with no backward compatibility guarantee.
- **Recommendation**: Introduce URL path versioning (`/v1/books`). Update SAM template API events to include version prefix. Establish a backward compatibility policy for agent-consumed APIs.

#### APP-Q12: Service Discovery & Mesh
- **Score**: 2/4 🟠
- **Finding**: DynamoDB table name is passed via environment variable `TABLE` from CloudFormation (`Environment.Variables.TABLE: !Ref BooksTable`). No hard-coded service endpoints. However, no service discovery mechanism (AWS Cloud Map, App Mesh) exists. The API endpoint is output via `ApiEndpoint` CloudFormation Output but not registered in a service catalog.
- **Gap**: No service discovery or API catalog. Agents need to discover available services and their endpoints programmatically.
- **Recommendation**: Register the Books API in an API catalog or service registry. Output the API endpoint and OpenAPI spec location to a central configuration store that agents can query for tool discovery.

#### APP-Q13: AI/Agent Frameworks
- **Score**: 1/4 ❌
- **Finding**: No AI or agent framework imports in any `package.json`. Dependencies are limited to `aws-sdk` (v2), `aws-xray-sdk-core`, and test libraries (mocha, chai, sinon). No `@aws-sdk/client-bedrock-runtime`, no `langchain`, no `strands-agents`, no `openai`, no MCP SDK imports.
- **Gap**: No AI/agent framework integration. This is the most critical gap for the agentic-ai-enablement goal. Without agent frameworks, there is no foundation for building customer support or order management agents.
- **Recommendation**: Add `strands-agents` SDK (TypeScript) and `@aws-sdk/client-bedrock-runtime` as dependencies. Create an agent Lambda function that uses the Books API as tools. Start with a simple catalog query agent as proof of concept.

### Data Foundations

#### DATA-Q1: Vector Database Presence
- **Score**: 1/4 ❌
- **Finding**: No vector database found. No OpenSearch domain (`aws_opensearch_domain`), no Aurora pgvector, no Pinecone/Weaviate/Chroma imports in any `package.json`. No Bedrock Knowledge Base configuration in `template.yml`. No S3 Vectors configuration.
- **Gap**: No vector database for semantic search. Customer support agents need vector search to find relevant book information, order context, and support documentation based on natural language queries.
- **Recommendation**: Deploy Amazon Bedrock Knowledge Base with OpenSearch Serverless as the vector store. Index book catalog data and any customer support documentation. This enables RAG-based agent responses grounded in actual catalog data.

#### DATA-Q2: Vector DB Management
- **Score**: 1/4 ❌
- **Finding**: No vector database exists (see DATA-Q1). No managed or self-hosted vector DB detected.
- **Gap**: No vector database infrastructure at all. Agents cannot perform semantic search over catalog or support data.
- **Recommendation**: Use Amazon Bedrock Knowledge Bases (fully managed) — it handles vector storage, embedding generation, and retrieval in a single managed service, eliminating the need to manage OpenSearch infrastructure directly.

#### DATA-Q3: RAG Implementation
- **Score**: 1/4 ❌
- **Finding**: No RAG implementation found. No embedding model calls (no Bedrock Titan Embeddings, no OpenAI ada). No document chunking or splitting code. No similarity search or knn_search patterns in any source file. No Bedrock Knowledge Base integration.
- **Gap**: No RAG pipeline. Customer support agents need RAG to answer questions about book availability, order policies, and product details with grounded, accurate responses.
- **Recommendation**: Implement a RAG pipeline: (1) Ingest book catalog data and support docs into S3, (2) Configure Bedrock Knowledge Base with Titan Embeddings for chunking and indexing, (3) Query the Knowledge Base from agent Lambda functions for context-grounded responses.

#### DATA-Q4: Data Source Sprawl
- **Score**: 4/4 ✅
- **Finding**: Single data source: DynamoDB `BooksTable` defined in `template.yml`. Both Lambda functions (`CreateBook`, `GetAllBooks`) access only this one table. `events/env.json` confirms single table reference: `{"TABLE": "books"}`. No additional databases, no external API clients.
- **Gap**: None for current scope. Single data source is clean and simple.
- **Recommendation**: As agent capabilities are added (conversation history, order data, support tickets), plan a unified data access strategy to prevent sprawl. Use DynamoDB for operational data and Bedrock Knowledge Bases for semantic search.

#### DATA-Q5: Data Access Pattern
- **Score**: 2/4 🟠
- **Finding**: Lambda functions access DynamoDB directly via AWS SDK DynamoDB client. `src/books/create/index.ts` instantiates `new AWS.DynamoDB(ddbOptions)` and calls `putItem` directly. `src/books/get-all/index.ts` instantiates its own `new AWS.DynamoDB(ddbOptions)` and calls `scan` directly. No repository pattern, no data access layer abstraction.
- **Gap**: Direct database access from handler functions. No abstraction layer that agents could use as a data contract. Each handler creates its own DynamoDB client instance.
- **Recommendation**: Extract a shared Books repository module that encapsulates DynamoDB operations. Expose data access through well-defined functions (createBook, getAllBooks, getBookByIsbn). This becomes the data contract for agent tools.

#### DATA-Q6: Unstructured Data
- **Score**: 1/4 ❌
- **Finding**: No S3 storage for documents. No Textract, Tika, or PDF/image processing libraries in any `package.json`. Application handles only structured book metadata (isbn, title, year, author, publisher, rating, pages).
- **Gap**: No unstructured data handling. Customer support agents may need to process support tickets, emails, or product documentation in various formats.
- **Recommendation**: Add S3 bucket for support documents and product descriptions. Use Amazon Textract for document extraction if PDF/image processing is needed. Feed unstructured content into the RAG pipeline for agent retrieval.

#### DATA-Q7: Schema Documentation
- **Score**: 2/4 🟠
- **Finding**: No formal schema documentation. Book schema is implicitly defined in `src/books/create/index.ts` (isbn, title, year, author, publisher, rating, pages extracted from request body). `events/create-book-request.json` provides a sample request payload. `src/books/get-all/tests/index.spec.ts` defines a `Book` TypeScript interface. No JSON Schema files, no Avro/Protobuf schemas, no database migration files.
- **Gap**: Schema exists only in code and test files. No machine-readable schema documentation that agents could use to understand data structure.
- **Recommendation**: Create a formal JSON Schema for the Book resource. Include it in the OpenAPI specification (see APP-Q2). Maintain TypeScript interfaces in a shared types module.

#### DATA-Q8: Data Access Layer
- **Score**: 1/4 ❌
- **Finding**: No unified data access layer. `src/books/create/index.ts` and `src/books/get-all/index.ts` each create their own DynamoDB client and perform operations directly. `src/books/tests/books-manager.js` contains a separate test utility with `save`, `remove`, `get`, and `findBookInList` functions — this is closer to a data access layer but is only used in tests.
- **Gap**: Duplicated data access code across handlers. No shared data contract. The test utility `books-manager.js` demonstrates the pattern needed but isn't used in production code.
- **Recommendation**: Refactor the production code to use a shared repository module similar to the pattern in `src/books/tests/books-manager.js`. Create a `books-repository.ts` with typed functions for all DynamoDB operations.

#### DATA-Q9: Embedding Freshness
- **Score**: 1/4 ❌
- **Finding**: No embeddings exist. No vector database, no indexing pipeline, no CDC (Change Data Capture) patterns. No DynamoDB Streams configured for change propagation. No scheduled re-indexing.
- **Gap**: No embedding infrastructure to keep fresh. When RAG is implemented, a freshness mechanism will be needed to keep embeddings synchronized with catalog data changes.
- **Recommendation**: When implementing RAG (see DATA-Q3), enable DynamoDB Streams on `BooksTable` and configure an event-driven Lambda to update embeddings when books are created or updated. Alternatively, use Bedrock Knowledge Base automatic sync with S3 data source.

#### DATA-Q10: Database Engine Version & EOL
- **Score**: 4/4 ✅
- **Finding**: DynamoDB is an evergreen managed service with no engine version to pin and no EOL concerns. It is defined as `AWS::Serverless::SimpleTable` in `template.yml`. AWS manages all versioning, patching, and upgrades transparently.
- **Gap**: None. DynamoDB has no EOL risk.
- **Recommendation**: No action needed. DynamoDB's evergreen model is ideal for long-lived agent infrastructure.

#### DATA-Q11: Stored Procedures & Schema Complexity
- **Score**: 4/4 ✅
- **Finding**: No stored procedures, triggers, or proprietary SQL. DynamoDB is a NoSQL key-value/document store with no SQL dialect. All business logic is in the application layer (Lambda functions). No `.sql` files in the repository. No ORM bypass patterns.
- **Gap**: None. All logic in application code.
- **Recommendation**: Maintain application-layer business logic. This clean separation makes it easy to expose operations as agent tools without database-layer coupling.

### Identity, Security & Governance

#### SEC-Q1: Secret Management
- **Score**: 3/4 🟡
- **Finding**: No hardcoded secrets in source code. Environment variables contain only non-sensitive values: `TABLE` (DynamoDB table name) and `FN_NEW_VERSION` (Lambda function ARN) in `template.yml`. `.gitignore` excludes `.aws-sam` and `node_modules`. Lambda functions use IAM role-based authentication to access DynamoDB — no database credentials needed. No `.env` files committed.
- **Gap**: No Secrets Manager integration. While not currently needed (IAM roles handle all auth), adding agent integrations (third-party APIs, LLM API keys) will require a secrets management strategy.
- **Recommendation**: Establish Secrets Manager usage pattern before adding agent integrations. Store any future API keys, tokens, or connection strings in Secrets Manager. Add `@aws-sdk/client-secrets-manager` to dependencies proactively.

#### SEC-Q2: IAM Least Privilege
- **Score**: 2/4 🟠
- **Finding**: Lambda function IAM policies in `template.yml` are well-scoped: `DynamoDBReadPolicy` for `GetAllBooks`, `DynamoDBWritePolicy` for `CreateBook`, `DynamoDBCrudPolicy` for `CreateBookPreTraffic` — all scoped to specific `TableName: !Ref BooksTable`. However, `pipeline/lib/pipeline-stack.ts` grants the deploy CodeBuild role extremely broad managed policies: `AWSCloudFormationFullAccess`, `AmazonDynamoDBFullAccess`, `AWSLambda_FullAccess`, `AmazonAPIGatewayAdministrator`, `IAMFullAccess`, `AWSCodeDeployFullAccess`, `AmazonCognitoPowerUser`. The test role also gets `AmazonCognitoPowerUser` and `AmazonDynamoDBFullAccess`.
- **Gap**: Pipeline deployment roles use wildcard *FullAccess policies. While Lambda runtime policies are well-scoped, the deployment pipeline has excessive permissions that could be exploited if compromised.
- **Recommendation**: Replace *FullAccess managed policies on the deploy role with custom IAM policies scoped to the specific resources created by the SAM template. Use resource-level ARN patterns and condition keys.

#### SEC-Q3: Identity Propagation
- **Score**: 2/4 🟠
- **Finding**: `CognitoAuth` authorizer configured on POST /books in `template.yml` with `AuthorizationScopes: [email]`. Cognito User Pool validates the OAuth token at API Gateway. However, Lambda handlers (`src/books/create/index.ts`) do not parse the JWT claims or extract user identity from `event.requestContext.authorizer.claims`. User identity is validated at the gateway but not propagated into the application logic.
- **Gap**: No identity propagation beyond API Gateway. Agent workflows need user context to enforce per-user permissions (e.g., "show me MY orders" should only return the requesting user's data).
- **Recommendation**: Extract user identity from `event.requestContext.authorizer.claims` in Lambda handlers. Pass user context (sub, email) through the call chain. When adding agent endpoints, enforce per-user data access based on token claims.

#### SEC-Q4: Audit Logging
- **Score**: 2/4 🟠
- **Finding**: API Gateway has `MethodSettings` with `LoggingLevel: INFO` in `template.yml`, logging all API requests to CloudWatch. Lambda functions have X-Ray `Tracing: Active`. `ApiGwAccountConfig` and `ApiGatewayLoggingRole` enable CloudWatch logging for API Gateway. However, no CloudTrail configuration in IaC. No log file validation. No immutable log storage.
- **Gap**: No CloudTrail in IaC for auditing AWS API calls. No immutable log storage. Agent actions (tool invocations, data modifications) need comprehensive audit trails for accountability and compliance.
- **Recommendation**: Add CloudTrail with log file validation and S3 object lock for immutable storage. Configure CloudWatch Logs retention policies. For agent workflows, log all tool invocations with user context and agent reasoning.

#### SEC-Q5: API Rate Limits
- **Score**: 1/4 ❌
- **Finding**: No API Gateway throttling configuration in `template.yml`. No `ThrottlingBurstLimit`, `ThrottlingRateLimit`, or usage plans defined. No WAF rules. No application-level rate limiting middleware in Lambda code.
- **Gap**: No rate limiting at any layer. Agent-generated traffic can be high-volume and bursty. Without rate limits, a misconfigured agent could flood the API, causing DynamoDB throttling and service degradation.
- **Recommendation**: Configure API Gateway stage-level throttling. Add usage plans with API keys for different consumers (human users vs agents). Add WAF rate-based rules for DDoS protection. Critical for agent safety.

#### SEC-Q6: PII Redaction
- **Score**: 1/4 ❌
- **Finding**: No PII redaction or masking in logging. Lambda handlers do not perform any log scrubbing. `src/books/create-pre-traffic/index.ts` logs DynamoDB items via `console.log('DynamoDB item', JSON.stringify(Item, null, 2))`. Error handlers return empty body on 500 (good practice — no error details leaked to clients).
- **Gap**: No PII handling strategy. While book data may not contain PII, customer support and order management agents will handle customer names, emails, addresses, and payment information. Without PII redaction, sensitive data could appear in CloudWatch Logs.
- **Recommendation**: Add a logging middleware that automatically redacts PII fields before writing to CloudWatch. Use Amazon Macie for S3-stored data classification. Define a PII handling policy before building customer-facing agents.

#### SEC-Q7: Human Approval Workflows
- **Score**: 2/4 🟠
- **Finding**: `pipeline/lib/pipeline-stack.ts` defines a `ManualApprovalAction` before production deployment: `"Ensure Books API works correctly in Staging and release date is agreed with Product Owners"`. This gates production releases requiring human review. However, no in-application human approval workflow exists for high-risk data mutations.
- **Gap**: CI/CD approval exists, but no in-app approval for high-risk agent actions. Customer support agents performing refunds, order cancellations, or bulk data changes should require human approval before execution.
- **Recommendation**: Implement Step Functions with human approval tasks (`waitForTaskToken`) for high-risk agent actions. Define a risk classification for agent tools (low-risk: read operations, high-risk: writes, refunds, deletions) and route high-risk actions through human-in-the-loop approval.

#### SEC-Q8: Encryption at Rest
- **Score**: 3/4 🟡
- **Finding**: DynamoDB table has `SSESpecification.SSEEnabled: true` in `template.yml` (AWS-managed KMS encryption). S3 buckets in `pipeline/lib/pipeline-stack.ts` use `BucketEncryption.S3_MANAGED`. All data at rest is encrypted, but using AWS-managed keys rather than customer-managed KMS keys.
- **Gap**: No customer-managed KMS keys. For customer data in agent workflows (conversation history, order details), customer-managed keys provide additional control and audit capabilities.
- **Recommendation**: Create customer-managed KMS keys for sensitive data stores. Apply them to DynamoDB, S3, and any future data stores used by agent workflows. Enable KMS key rotation.

#### SEC-Q9: API Authentication
- **Score**: 2/4 🟠
- **Finding**: POST /books requires `CognitoAuth` with `AuthorizationScopes: [email]` in `template.yml`. GET /books is public — no authentication required. The Cognito User Pool supports OAuth implicit grant with email and openid scopes. `UserPoolClient` in staging also allows `ALLOW_USER_PASSWORD_AUTH` for automated testing.
- **Gap**: Not all endpoints are authenticated. GET /books (read all books) is public. While this may be intentional for the current API, agent endpoints must require authentication to ensure only authorized agents and users can invoke tools.
- **Recommendation**: Add authentication to all agent-facing endpoints. Use Cognito machine-to-machine credentials (client_credentials grant) for agent-to-API authentication. Consider API keys with usage plans for agent rate tracking.

#### SEC-Q10: Centralized Identity
- **Score**: 3/4 🟡
- **Finding**: Amazon Cognito User Pool configured in `template.yml` as the centralized identity provider: `CognitoUserPool` with email-based usernames, `UserPoolClient` with OAuth flows, `UserPoolDomain` for hosted UI. Single IdP for the Books API.
- **Gap**: Cognito is configured but uses implicit grant flow only. No federation with external IdPs (SAML, OIDC). No SSO configuration for organization-wide access.
- **Recommendation**: Migrate from implicit grant to authorization code grant with PKCE (more secure). Add federation with organizational IdP if agents will be used by internal support staff. Configure Cognito Identity Pool if agents need AWS credential-based access.

### Operations & Observability

#### OPS-Q1: Distributed Tracing
- **Score**: 3/4 🟡
- **Finding**: X-Ray tracing is enabled: `TracingEnabled: true` on `BooksApi` and `Tracing: Active` on all Lambda functions in `template.yml` Globals. `aws-xray-sdk-core` is imported in `src/books/create/index.ts` and `src/books/get-all/index.ts` via `AWSXRay.captureAWS(AWSCore)`, instrumenting all AWS SDK calls. `X-Amzn-Trace-Id` is automatically propagated through API Gateway to Lambda. Service map available in X-Ray console.
- **Gap**: X-Ray tracing is solid but not OpenTelemetry. No `gen_ai.*` semantic conventions for future LLM span tracking. No custom subsegments for business logic. Agent workflows will need enhanced tracing to track LLM calls, tool invocations, and reasoning steps.
- **Recommendation**: Migrate from X-Ray SDK to OpenTelemetry with X-Ray exporter for vendor-neutral instrumentation. Add custom spans for agent tool invocations and LLM calls. Plan for `gen_ai.*` semantic conventions when agent framework is added.

#### OPS-Q2: Structured Logging
- **Score**: 1/4 ❌
- **Finding**: No structured JSON logging. Lambda handlers (`src/books/create/index.ts`, `src/books/get-all/index.ts`) do not log at all — they only return response objects. `src/books/create-pre-traffic/index.ts` uses basic `console.log()` for deployment smoke test logging. No JSON log formatters, no winston/pino/structlog configuration. No correlation ID middleware. No `traceId` or `correlationId` fields in logs.
- **Gap**: No structured logging infrastructure. Agent workflows generate complex execution traces that need structured, queryable logs with correlation IDs to debug issues. Without structured logging, troubleshooting agent behavior in production will be extremely difficult.
- **Recommendation**: Add Powertools for AWS Lambda Logger for structured JSON logging with automatic X-Ray trace ID correlation. Configure log levels per function. Add correlation ID middleware for request tracking across agent tool invocations.

#### OPS-Q3: Automated Evals
- **Score**: 1/4 ❌
- **Finding**: No agent evaluation framework found. No eval datasets, no scoring scripts, no LLM-as-judge patterns, no RAGAS configuration, no golden dataset files. The existing test suite covers API functionality (unit tests + e2e tests) but not AI/agent quality metrics.
- **Gap**: No automated evaluation for agent quality. Before deploying customer-facing AI agents, you need automated evaluation to measure response accuracy, hallucination rate, task completion, and customer satisfaction proxy metrics.
- **Recommendation**: Create a golden dataset of customer support queries with expected responses. Implement automated eval pipeline (can be a CodeBuild stage in the existing pipeline) using LLM-as-judge for response quality scoring. Track eval metrics over time to catch regressions.

#### OPS-Q4: SLOs
- **Score**: 1/4 ❌
- **Finding**: CloudWatch Alarms exist in `template.yml` (`CreateBookAliasErrorMetricGreaterThanZeroAlarm`, `GetAllBooksAliasErrorMetricGreaterThanZeroAlarm`) but these monitor Lambda errors for deployment rollback — not SLO tracking. No p99/p95 latency alarms. No error budget tracking. No SLO dashboards.
- **Gap**: No SLO definitions for critical user journeys. Agent interactions have distinct SLO requirements: response latency (p95 < 5s for support queries), task completion rate (> 90%), and hallucination rate (< 5%).
- **Recommendation**: Define SLOs for API latency (p99 < 1s for GET, p99 < 2s for POST). When agents are added, define agent-specific SLOs: response latency, task success rate, escalation rate to human. Create CloudWatch dashboards and error budget alarms.

#### OPS-Q5: Rollback Capability
- **Score**: 4/4 ✅
- **Finding**: Excellent rollback capability. `template.yml` configures `DeploymentPreference` with `Linear10PercentEvery1Minute` for production (gradual traffic shifting). `CreateBookPreTraffic` Lambda function performs a smoke test before any traffic is shifted to the new version. CloudWatch Alarms trigger automatic rollback on errors. Staging uses `AllAtOnce` for faster iteration.
- **Gap**: None for code rollback. However, no prompt or model version rollback capability (will be needed when agents are added).
- **Recommendation**: Extend rollback capability to cover agent configuration: prompt versions, model selection, and tool definitions. Consider feature flags for gradual agent capability rollout.

#### OPS-Q6: LLM Cost Tracking
- **Score**: 1/4 ❌
- **Finding**: No LLM usage in the application. No token counting, no cost attribution, no per-user usage tracking. No custom CloudWatch metrics for AI costs. No observability data retention policies.
- **Gap**: No LLM cost tracking infrastructure. Customer-facing AI agents can incur significant costs from LLM API calls; without per-request cost attribution, costs will be opaque and uncontrollable.
- **Recommendation**: When adding Bedrock integration, implement per-request token counting and cost attribution. Log `usage` object from Bedrock responses. Create CloudWatch custom metrics for token consumption by user/feature. Set budget alarms. Define log retention policies for agent conversation data.

#### OPS-Q7: Business Metrics
- **Score**: 1/4 ❌
- **Finding**: No custom CloudWatch metrics for business outcomes. The only CloudWatch alarms in `template.yml` monitor Lambda errors (infrastructure metric). No metrics for books created, API usage patterns, or user engagement. No business KPI dashboards.
- **Gap**: No business outcome tracking. For customer support agents, business metrics (resolution rate, customer satisfaction, escalation rate, average handling time) are essential to measure agent value.
- **Recommendation**: Add CloudWatch custom metrics for: books_created, api_requests_by_endpoint, unique_users. When agents are added: agent_resolution_rate, agent_escalation_rate, customer_satisfaction_score, average_response_time.

#### OPS-Q8: Anomaly Detection
- **Score**: 1/4 ❌
- **Finding**: CloudWatch Alarms in `template.yml` use static threshold: `ComparisonOperator: GreaterThanThreshold`, `Threshold: 0` for Lambda errors. No anomaly detection. No latency p99 alarms. No behavioral baseline monitoring. No PagerDuty/OpsGenie integration.
- **Gap**: Static threshold alerting only. Agents exhibit non-deterministic behavior — an agent making 15 tool calls instead of the usual 3 indicates a reasoning loop. Static thresholds cannot catch behavioral anomalies.
- **Recommendation**: Enable CloudWatch anomaly detection on error rates and latency. Add p99 latency alarms. When agents are added, monitor tool invocation counts per request, response length distribution, and completion token usage for behavioral anomaly detection.

#### OPS-Q9: Deployment Strategy
- **Score**: 4/4 ✅
- **Finding**: Production deployment uses `Linear10PercentEvery1Minute` (canary-like gradual traffic shifting) configured in `template.yml`. `CreateBookPreTraffic` hook validates the new version by invoking it and verifying DynamoDB write success before allowing traffic shift. CloudWatch Alarms auto-rollback on errors. `ManualApprovalAction` in `pipeline/lib/pipeline-stack.ts` gates production releases. Staging uses `AllAtOnce` for rapid iteration.
- **Gap**: None. Excellent deployment safety.
- **Recommendation**: Extend this deployment pattern to agent Lambda functions. Use pre-traffic hooks to run agent eval tests against the new version before shifting traffic.

#### OPS-Q10: Integration Testing
- **Score**: 4/4 ✅
- **Finding**: Comprehensive test suite. Unit tests: `src/books/create/tests/index.spec.ts` (3 tests: successful put, invalid body, DynamoDB error) and `src/books/get-all/tests/index.spec.ts` (3 tests: get books, empty results, DynamoDB error) using mocha + sinon + aws-sdk-mock. E2E tests: `src/books/tests/index.js` (5 tests: no auth required for GET, returns books, POST requires auth, invalid schema, create book) using mocha + axios with real Cognito auth flow. Pipeline runs unit tests in Build stage (`pipeline/buildspec.json`) and e2e tests in Staging stage (`pipeline/buildspec-test.json`).
- **Gap**: None for current functionality. Agent evaluation tests will be needed when agent capabilities are added (different from functional integration tests).
- **Recommendation**: Extend test suite to include agent integration tests: agent tool invocation tests, RAG retrieval quality tests, end-to-end agent conversation tests. Add a dedicated eval buildspec to the pipeline.

#### OPS-Q11: Incident Response Automation
- **Score**: 1/4 ❌
- **Finding**: No runbook files found. No SSM Automation documents. No Lambda-based remediation functions. No Step Functions for incident workflows. The only automated response is the deployment rollback mechanism (CloudWatch Alarm → CodeDeploy rollback). No self-healing patterns for runtime incidents.
- **Gap**: No incident response automation. Agent incidents (hallucination spikes, tool failures, cost overruns) need automated responses: circuit-breaking, fallback to human support, rate limiting.
- **Recommendation**: Create machine-readable runbooks for common failure scenarios. Implement Lambda-based auto-remediation for agent safety (e.g., auto-disable agent if error rate exceeds threshold). Add SSM Automation for infrastructure incident response.

#### OPS-Q12: Observability Governance & Ownership
- **Score**: 1/4 ❌
- **Finding**: No CODEOWNERS file. No SLO definition files. No observability ownership documentation. No team ownership mapping for services or dashboards. No platform engineering or observability-as-a-product patterns.
- **Gap**: No observability ownership model. Agent systems require clear ownership of quality, reliability, and safety metrics. Without defined ownership, agent monitoring will be ad-hoc and accountability for failures will be unclear.
- **Recommendation**: Add CODEOWNERS file defining ownership of the Books API and future agent components. Define SLOs with named owners. Establish a shared responsibility model: platform team owns observability infrastructure, product team owns service-level and agent-level SLOs.

---

## Recommended Modernization Pathways

Based on the assessment findings, the following AWS Modernization Pathways are evaluated for this application. Multiple pathways can execute in parallel because modern applications comprise multiple interconnected components — each requiring its own modernization approach.

### Pathway Summary

| Pathway | Status | Goal Alignment | Priority | Key Trigger Criteria | Est. Effort |
|---------|--------|---------------|----------|---------------------|-------------|
| Move to Cloud Native | Triggered | Medium | Medium | APP-Q3: 1/4, APP-Q10: 3/4 | Medium |
| Move to Containers | Not Triggered | Medium | — | — | — |
| Move to Open Source | Not Triggered | Low | — | — | — |
| Move to Managed Databases | Not Triggered | High | — | — | — |
| Move to Managed Analytics | Triggered | Low | Low | INF-Q8: 1/4 | Low |
| Move to Modern DevOps | Triggered | High | Medium | OPS-Q1: 3/4 (partial tracing) | Medium |
| Move to AI | Triggered | High | High | APP-Q13: 1/4, DATA-Q1: 1/4, DATA-Q3: 1/4, OPS-Q3: 1/4, OPS-Q6: 1/4 | High |

### Parallel Execution Plan

**Parallel Track 1**: Move to AI + Move to Modern DevOps (no dependencies — can pursue agent framework integration while improving observability and logging simultaneously)

**Parallel Track 2**: Move to Cloud Native (async patterns, Step Functions) can execute in parallel with Track 1 once agent architecture design is established

**Sequential Dependencies**: Move to AI depends on improving observability (structured logging from Move to Modern DevOps) to effectively monitor agent behavior. Move to Cloud Native async patterns are more valuable after agent workflows are defined (so you know which workflows need async orchestration).

### Move to AI

- **Priority**: High
- **Goal Alignment**: High
- **Trigger Criteria Met**:
  - APP-Q13: Score 1/4 — No AI/agent framework imports in any dependency manifest
  - DATA-Q1: Score 1/4 — No vector database for semantic search
  - DATA-Q3: Score 1/4 — No RAG implementation for grounded responses
  - OPS-Q3: Score 1/4 — No automated evaluation framework for agent quality
  - OPS-Q6: Score 1/4 — No LLM cost tracking infrastructure
- **Current State**: Zero AI/agent capabilities. The Books API is a traditional CRUD REST API with no AI integration points. Dependencies include only `aws-sdk` and `aws-xray-sdk-core`.
- **Target State**: Agent-enabled application with Bedrock integration, vector database for RAG, automated eval pipeline, and LLM cost monitoring. Customer support and order management agents can discover and invoke Books API operations as tools.
- **Key Activities**:
  1. Add `strands-agents` SDK and `@aws-sdk/client-bedrock-runtime` to project
  2. Generate OpenAPI specification for agent tool discovery
  3. Deploy Bedrock Knowledge Base with book catalog data for RAG
  4. Create proof-of-concept catalog query agent Lambda
  5. Implement automated eval pipeline with golden datasets
  6. Add LLM cost tracking with CloudWatch custom metrics
- **Dependencies**: Benefits from Move to Modern DevOps (structured logging to monitor agent behavior)
- **Estimated Effort**: High
- **Roadmap Phase Alignment**: Phase 1 (quick wins: OpenAPI spec, PoC agent), Phase 2 (foundations: Knowledge Base, RAG, eval), Phase 3 (scale: production agents, cost optimization)
- **Relevant Learning Materials**: Module 7 — Move to AI

### Move to Modern DevOps

- **Priority**: Medium
- **Goal Alignment**: High
- **Trigger Criteria Met**:
  - OPS-Q1: Score 3/4 — X-Ray tracing present but not OpenTelemetry; no gen_ai semantic conventions for future LLM tracking
- **Current State**: Strong CI/CD pipeline with CodePipeline, automated testing, and gradual deployment. X-Ray tracing active. However, no structured logging, no SLOs, no anomaly detection, and no observability governance. These gaps are critical for monitoring agent behavior.
- **Target State**: Structured JSON logging with correlation IDs, OpenTelemetry instrumentation with gen_ai spans, defined SLOs for API and agent endpoints, anomaly detection for behavioral monitoring, and observability ownership model.
- **Key Activities**:
  1. Add Powertools for AWS Lambda (Logger, Tracer, Metrics)
  2. Implement structured JSON logging across all Lambda functions
  3. Define SLOs for API latency and availability
  4. Enable CloudWatch anomaly detection
  5. Add CODEOWNERS and observability ownership documentation
  6. Add agent eval stage to CI/CD pipeline
- **Dependencies**: None
- **Estimated Effort**: Medium
- **Roadmap Phase Alignment**: Phase 1 (quick wins: structured logging, Powertools), Phase 2 (SLOs, anomaly detection)
- **Relevant Learning Materials**: Module 6 — Move to Modern DevOps

### Move to Cloud Native

- **Priority**: Medium
- **Goal Alignment**: Medium
- **Trigger Criteria Met**:
  - APP-Q3: Score 1/4 — 100% synchronous communication, no async patterns
  - APP-Q10: Score 3/4 — No async handling for potentially long-running operations
- **Current State**: Serverless Lambda functions with synchronous API Gateway → DynamoDB pattern. No async messaging (SQS/SNS/EventBridge), no workflow orchestration (Step Functions). The modular Lambda design (APP-Q4: 3/4) is already partially cloud-native.
- **Target State**: Event-driven architecture with SQS for async task processing, EventBridge for event routing, and Step Functions for multi-step agent workflow orchestration. Existing Lambda functions remain as the compute layer.
- **Key Activities**:
  1. Add Step Functions for agent workflow orchestration
  2. Introduce SQS for async agent task processing
  3. Add EventBridge for event-driven patterns (e.g., new book added → update embeddings)
  4. Implement async status polling endpoints for long-running operations
- **Dependencies**: Agent architecture design (from Move to AI) informs which async patterns are needed
- **Estimated Effort**: Medium
- **Roadmap Phase Alignment**: Phase 2 (foundations: Step Functions, SQS), Phase 3 (optimization: EventBridge, advanced orchestration)
- **Relevant Learning Materials**: Module 2 — Move to Cloud Native (Containers and Serverless)

### Move to Managed Analytics

- **Priority**: Low
- **Goal Alignment**: Low
- **Trigger Criteria Met**:
  - INF-Q8: Score 1/4 — No managed streaming or analytics services
- **Current State**: No streaming or analytics infrastructure. Data resides only in DynamoDB with no analytics layer.
- **Target State**: Agent conversation analytics via Kinesis Data Streams or DynamoDB Streams, with optional Athena for ad-hoc analysis of agent behavior logs.
- **Key Activities**:
  1. Enable DynamoDB Streams for change data capture
  2. Add Kinesis Data Streams for agent conversation event streaming (when agents are added)
  3. Consider Athena for analyzing agent conversation logs stored in S3
- **Dependencies**: Move to AI (agents must exist before their analytics are needed)
- **Estimated Effort**: Low
- **Roadmap Phase Alignment**: Phase 3 (agent analytics and optimization)
- **Relevant Learning Materials**: Module 5 — Move to Managed Analytics

---

## Microservices Decomposition Strategy

> This serverless application uses a modular Lambda architecture with clear function boundaries (CreateBook, GetAllBooks). Each Lambda function can serve as a distinct agent tool without further decomposition. See the Move to Cloud Native pathway for guidance on adding async communication patterns (SQS, EventBridge) and workflow orchestration (Step Functions) as agent capabilities grow. For now, agents can interact with the application via its existing REST API surface (GET /books, POST /books).

---

## Quick Agent Wins

Even before completing the full modernization roadmap, these agent opportunities are available based on your current architecture:

1. **Customer Support Catalog Query Agent** — Build an agent that queries the Books API to answer customer questions like "Do you have any books by [author]?" or "What books are available about [topic]?"
   - **Leverages**: Existing GET /books endpoint returning structured JSON (APP-Q5: 4/4), DynamoDB BooksTable with book metadata
   - **Effort**: Low
   - **Value**: Immediate customer-facing value for catalog browsing; proves agent concept with minimal infrastructure changes

2. **Agent Tool Integration via JSON APIs** — Your API already returns structured JSON responses, making it straightforward for agents to parse and use API responses as tool outputs
   - **Leverages**: Structured JSON responses with Content-Type: application/json from both Lambda handlers (`src/books/create/index.ts`, `src/books/get-all/index.ts`)
   - **Effort**: Low
   - **Value**: Agent tool integration requires no response format changes; agents can consume API outputs directly

3. **Knowledge Agent from README and Documentation** — Build a RAG-based knowledge agent using the comprehensive README.md and code documentation to answer developer and internal support questions about the Books API
   - **Leverages**: Detailed `README.md` covering architecture, deployment, testing, and API usage; code comments; `CONTRIBUTING.md`
   - **Effort**: Low-Medium
   - **Value**: Internal support agent that can answer "How do I deploy?" or "How do I get an auth token?" reducing onboarding time

4. **DevOps Agent for Deployment and Pipeline Status** — Build an agent that can trigger the existing CI/CD pipeline and check deployment status
   - **Leverages**: Full CodePipeline (INF-Q6: 4/4) with Source → Build → Staging → Production stages, manual approval gate
   - **Effort**: Medium
   - **Value**: Automates deployment workflows; agents can check pipeline status, trigger builds, and report test results

> These opportunities can be pursued in parallel with the modernization roadmap.
> They demonstrate agent value early while foundations are being built.

---

## Readiness Roadmap

### Phase 1 — Agent Quick Wins (Days 1–30)

1. **Generate OpenAPI 3.0 specification** for GET /books and POST /books with full request/response schemas. Embed in SAM template via `DefinitionBody` or maintain standalone `openapi.yaml`. This is the single highest-impact action for agent tool discovery.
2. **Add Powertools for AWS Lambda** (Logger, Tracer, Metrics) to all Lambda functions for structured JSON logging with correlation IDs and X-Ray trace integration. Addresses OPS-Q2 immediately.
3. **Add API Gateway throttling** — configure `ThrottlingBurstLimit` and `ThrottlingRateLimit` on the `BooksApi` stage. Add a usage plan. This protects the API from agent-generated burst traffic.
4. **Create a proof-of-concept agent** — add `strands-agents` and `@aws-sdk/client-bedrock-runtime` as dependencies. Build a simple catalog query agent Lambda that calls GET /books and answers natural language questions about the book catalog.
5. **Migrate from aws-sdk v2 to @aws-sdk v3** — the existing `aws-sdk` (v2) dependency is approaching EOL. Migrating to modular v3 clients reduces bundle size and provides better TypeScript support for agent integrations.

### Phase 2 — Agent Foundations (Months 1–3)

1. **Deploy Bedrock Knowledge Base** with OpenSearch Serverless as the vector store. Ingest book catalog data and any customer support documentation. Configure automatic sync for embedding freshness.
2. **Implement RAG pipeline** in the agent Lambda function — query Bedrock Knowledge Base for context-grounded responses to customer support queries about book availability, order policies, and product details.
3. **Add Step Functions** for multi-step agent workflows (e.g., search catalog → check order → issue refund → notify customer). Implement human approval tasks for high-risk operations.
4. **Create automated eval pipeline** — build golden dataset of customer support queries with expected responses. Add eval buildspec to CI/CD pipeline. Track response quality, hallucination rate, and task completion.
5. **Define SLOs** for API endpoints (p99 latency < 1s) and agent interactions (p95 response time < 5s, task success rate > 90%). Create CloudWatch dashboards and error budget alarms.
6. **Implement LLM cost tracking** — log Bedrock token usage per request, create CloudWatch custom metrics for cost attribution by user/feature, set budget alarms.
7. **Add SQS queues** for async agent task processing and EventBridge for event-driven triggers (e.g., new book added → update embeddings).
8. **Tighten pipeline IAM** — replace *FullAccess managed policies on the deploy role with resource-scoped custom IAM policies.

### Phase 3 — Agent Scale & Optimization (Months 3–6)

1. **Production agent deployment** — deploy customer-facing support agent with gradual rollout using existing Linear10PercentEvery1Minute deployment strategy. Add pre-traffic hooks that run agent eval suite.
2. **Advanced observability** — migrate from X-Ray SDK to OpenTelemetry with gen_ai semantic conventions for LLM span tracking. Enable CloudWatch anomaly detection for agent behavioral monitoring. Implement incident response automation with Lambda-based auto-remediation.
3. **Agent conversation analytics** — add DynamoDB Streams or Kinesis for streaming agent conversation events. Use Athena for ad-hoc analysis of agent behavior patterns.
4. **Business metrics and optimization** — track agent resolution rate, customer satisfaction, escalation rate. Optimize agent prompts and tool selection based on eval data. Implement token budget optimization.
5. **Identity and governance** — add identity propagation (JWT claims in Lambda handlers) for per-user agent context. Add PII redaction middleware. Implement CODEOWNERS and observability governance model.
6. **API versioning** — introduce `/v1/` prefix for backward compatibility as agent-consumed API surface stabilizes.

---

## Recommended Self-Paced Learning Materials

### Module 7: Move to AI
These resources are critical for the primary pathway — enabling agentic AI capabilities on top of the existing Books API.

- Introduction to Generative AI: Art of the Possible — https://skillbuilder.aws/learn/ZEVZZ1D4AS/introduction-to-generative-ai--art-of-the-possible/Y7MTGJCW1U
  - Understand the landscape of generative AI possibilities before building customer support agents
- Planning a Generative AI Project — https://skillbuilder.aws/learn/HU1FQRGDDZ/planning-a-generative-ai-project/SYR3SCPSHC
  - Framework for planning the agent project for support and order management
- Amazon Bedrock Getting Started — https://skillbuilder.aws/learn/63KTRM86DQ/amazon-bedrock-getting-started/SC2Y3HMAUE
  - Foundation for all Bedrock-based agent development
- Essentials for Prompt Engineering — https://skillbuilder.aws/learn/XBNAVKA88J/essentials-of-prompt-engineering/9T9Q45EDTV
  - Critical skill for designing effective agent prompts for customer support workflows
- Build and Evaluate Retrieval Augmented Generation (RAG) Applications using Knowledge Bases for Amazon Bedrock (Lab) — https://skillbuilder.aws/learn/JRGWCFYT67/lab--build-and-evaluate-retrieval-augmented-generation-rag-applications-using-knowledge-bases-for-amazon-bedrock/A4MN58JB7A
  - Hands-on lab directly applicable to building the RAG pipeline for catalog data
- Introduction to Agentic AI on AWS — https://skillbuilder.aws/learn/DNBD5MT8ZD/introduction-to-agentic-ai-on-aws/WAKAFK6UFY
  - Core concepts for building autonomous agents for customer support
- Creating an AWS DevOps AI Agent with the Strands Agents SDK (Lab) — https://skillbuilder.aws/learn/AH1GD8AJY3/lab--creating-an-aws-devops-ai-agent-with-the-strands-agents-sdk/A9SKJNMPJ2
  - Hands-on experience with Strands Agents SDK — the recommended framework for this project
- AWS PartnerCast: Deep Dive: Building Observable AI Agents with Strands, Amazon Bedrock Agent Core & SageMaker MLflow — https://skillbuilder.aws/learn/1EN76TZBB6/aws-partnercast--deep-dive-building-observable-ai-agents-with-strands-amazon-bedrock-agent-core--sagemaker-mlflow--technical/CX2K6XAT84
  - Agent observability patterns needed for production agent monitoring

### Module 6: Move to Modern DevOps
These resources address the observability and DevOps gaps that are prerequisites for safe agent deployment.

- Getting Started with DevOps on AWS — https://skillbuilder.aws/learn/R4B13K95YQ/getting-started-with-devops-on-aws/38NHHYRV1R
  - Foundational DevOps practices for the existing pipeline
- Advanced Testing Practices Using AWS DevOps Tools — https://skillbuilder.aws/learn/1YC7UXUWBR/advanced-testing-practices-using-aws-devops-tools/A32U6G7NEQ
  - Extend testing practices to include agent evaluation tests
- Monitor Python Applications Using Amazon CloudWatch Application Signals — https://skillbuilder.aws/learn/JMPDZD64MV/monitor-python-applications-using-amazon-cloudwatch-application-signals/2JP3J2MPCK
  - Application Signals for SLO tracking (concept applies to Node.js as well)
- DevOps and AI on AWS: CloudWatch Anomaly Detection (Lab) — https://skillbuilder.aws/learn/RWYVJ73MXP/lab--devops-and-ai-on-aws-cloudwatch-anomaly-detection/BRPDNZUGU7
  - Directly applicable for setting up anomaly detection for agent behavioral monitoring

### Module 2: Move to Cloud Native (Containers and Serverless)
These resources support adding async patterns and workflow orchestration for agent workflows.

- Cloud Design Patterns, Architectures, and Implementations — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html
  - Essential reference for event-driven patterns, saga orchestration, and circuit breaker patterns needed for agent workflows
- Architecting Serverless Applications — https://skillbuilder.aws/learn/MRWENY7FSX/architecting-serverless-applications/QVFY2JHVEH
  - Deepen serverless architecture knowledge for adding Step Functions and EventBridge
- Amazon API Gateway for Serverless Applications — https://skillbuilder.aws/learn/GQA6FHWPJD/amazon-api-gateway-for-serverless-applications/JVRZ3PSW4H
  - API Gateway throttling, request validation, and usage plans — critical gaps to address
- Amazon DynamoDB for Serverless Architecture — https://skillbuilder.aws/learn/SY1Y83VKTB/amazon-dynamodb-for-serverless-architectures/K9NM3PHH3S
  - DynamoDB Streams, advanced patterns for agent data access

### Module 4: Move to Managed Databases
Relevant for adding vector database capabilities alongside the existing DynamoDB infrastructure.

- AWS PartnerCast: Vector Databases for Generative AI Applications — https://skillbuilder.aws/learn/UQ74USQJHU/aws-partnercast--vector-databases-for-generative-ai-applications--technical/7DKMBAPCST
  - Directly applicable to selecting and deploying a vector database for RAG

---

## Appendix: Evidence Index

| # | File | Key Evidence |
|---|------|-------------|
| 1 | `template.yml` | SAM template defining all infrastructure: Lambda functions (Node.js 22.x), DynamoDB table (SSE enabled), API Gateway (Cognito auth, X-Ray tracing, INFO logging), CloudWatch Alarms, Cognito User Pool. Deployment preferences with Linear10PercentEvery1Minute. |
| 2 | `pipeline/lib/pipeline-stack.ts` | CDK pipeline definition: CodePipeline with 4 stages (Source → Build → Staging → Production), ManualApprovalAction, S3 buckets with S3_MANAGED encryption. *FullAccess IAM policies on deploy role. |
| 3 | `src/books/create/index.ts` | CreateBook Lambda handler: direct DynamoDB putItem, X-Ray SDK instrumentation, basic try/catch error handling, JSON response with Content-Type header. No structured logging. |
| 4 | `src/books/get-all/index.ts` | GetAllBooks Lambda handler: DynamoDB scan with DTO mapping, X-Ray SDK instrumentation, JSON array response. No structured logging, no pagination. |
| 5 | `src/books/create-pre-traffic/index.ts` | Pre-traffic hook: invokes new Lambda version, verifies DynamoDB write, reports to CodeDeploy. Uses console.log for logging. |
| 6 | `src/books/create/package.json` | Dependencies: aws-sdk v2 (^2.1692.0), aws-xray-sdk-core (^3.10.3). No AI/agent frameworks. Dev dependencies: mocha, chai, sinon, aws-sdk-mock for testing. |
| 7 | `src/books/get-all/package.json` | Same production dependencies as create. Additional dev dependency: uuid for test data generation. |
| 8 | `src/books/create-pre-traffic/package.json` | Minimal: aws-sdk only. No X-Ray SDK (deployment utility, not production handler). |
| 9 | `src/books/create/tests/index.spec.ts` | Unit tests: 3 test cases covering successful putItem, invalid body error, and DynamoDB failure. Uses aws-sdk-mock for DynamoDB stubbing. |
| 10 | `src/books/get-all/tests/index.spec.ts` | Unit tests: 3 test cases covering successful scan, empty results, and DynamoDB failure. Uses aws-sdk-mock. |
| 11 | `src/books/tests/index.js` | E2E tests: 5 test cases with real API calls, Cognito auth flow (create user → get token → test endpoints → delete user). Tests auth requirements, schema validation, and CRUD operations. |
| 12 | `src/books/tests/books-manager.js` | Test utility: DynamoDB batch operations (save, remove, get). Closest thing to a data access layer but only used in tests. |
| 13 | `src/books/tests/package.json` | E2E test dependencies: aws-sdk, axios (HTTP client), uuid, mocha, chai. |
| 14 | `pipeline/buildspec.json` | Build stage: installs esbuild, runs npm-recursive-install, executes unit tests for create and get-all, runs sam build, packages and uploads artifacts to S3. |
| 15 | `pipeline/buildspec-deploy.json` | Deploy stage: downloads SAM artifacts from S3, runs sam deploy with stage parameter, exports CloudFormation outputs (API_ENDPOINT, USER_POOL_ID, TABLE). |
| 16 | `pipeline/buildspec-test.json` | Test stage: installs e2e test dependencies, runs mocha tests against deployed staging environment. |
| 17 | `pipeline/package.json` | CDK pipeline dependencies: aws-cdk-lib (^2.189.1), constructs (^10.4.2). TypeScript project. |
| 18 | `events/create-book-request.json` | Sample API Gateway event with book payload: isbn, title, year, author, publisher, rating, pages. Defines implicit API schema. |
| 19 | `README.md` | Comprehensive documentation: architecture description, local testing instructions, CI/CD pipeline explanation, Cognito token acquisition guide. No OpenAPI spec referenced. |
| 20 | `.gitignore` | Excludes: node_modules, dist, .vscode, .aws-sam. No .env files committed. |
