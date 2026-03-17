# Agentic Readiness Assessment Report
**Target**: goal-agentic-readiness/services/books-api
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

This serverless REST API for book catalog management has a solid cloud-native foundation — running entirely on AWS Lambda, DynamoDB, and API Gateway with comprehensive Infrastructure as Code (SAM + CDK) and a full CI/CD pipeline with staged deployments. However, significant gaps exist across AI readiness, data foundations, security hardening, and operational observability. No AI/agent frameworks, vector databases, or RAG pipelines are present. API documentation, rate limiting, structured logging, and resilience patterns are missing. The overall agentic readiness score of **2.0 / 4.0** reflects a well-architected serverless service that requires targeted investment in AI capabilities, API hardening, and observability maturity to support agentic workloads.

### Overall Score: 2.0 / 4.0

| Category | Score | Status |
|----------|-------|--------|
| Infrastructure & Platform | 2.5 / 4.0 | 🟡 |
| Application Architecture | 1.9 / 4.0 | 🟡 |
| Data Foundations | 1.9 / 4.0 | 🟡 |
| Identity, Security & Governance | 2.0 / 4.0 | 🟡 |
| Operations & Observability | 1.7 / 4.0 | 🟡 |

---

## Top Priorities (Critical Gaps)

**1. No AI/Agent Frameworks (APP-Q13: 1/4)**
No AI or agent SDKs (Bedrock, LangChain, Strands, OpenAI) are present in any `package.json`. Without agent framework integration, this API cannot participate in agentic workflows as a tool provider or orchestrator. **First step**: Add `@aws-sdk/client-bedrock-runtime` to dependencies and create a proof-of-concept agent tool that wraps the existing books API endpoints.

**2. No API Documentation / OpenAPI Spec (APP-Q2: 1/4)**
While `OpenApiVersion: 3.0.1` is set in `template.yml` Globals, no actual OpenAPI specification file exists (no `openapi.yaml`, `swagger.json`, or inline API body). Agents cannot discover or invoke APIs without machine-readable documentation. **First step**: Generate an OpenAPI 3.0 spec from the existing API Gateway definition and maintain it alongside `template.yml`.

**3. No Structured Logging (OPS-Q2: 1/4)**
Lambda functions use `console.log()` (in `src/books/create-pre-traffic/index.ts`) without JSON formatting or correlation IDs. The `create/index.ts` and `get-all/index.ts` handlers have no logging at all. Agentic systems require structured, correlated logs to trace multi-step tool invocations. **First step**: Add a structured JSON logging library (e.g., `@aws-lambda-powertools/logger`) with correlation ID middleware to all Lambda functions.

**4. No Vector Database (DATA-Q1: 1/4)**
No vector database (OpenSearch with k-NN, Aurora pgvector, Bedrock Knowledge Bases, Pinecone, Chroma) is configured. Semantic search over the book catalog — a natural agent capability — is not possible without vector storage. **First step**: Evaluate Amazon Bedrock Knowledge Bases or OpenSearch Serverless with vector search for book catalog semantic retrieval.

**5. No API Rate Limiting (APP-Q8: 1/4, SEC-Q5: 1/4)**
The `BooksApi` API Gateway in `template.yml` has no throttling configuration, no WAF rules, no usage plans, and no per-client rate limits. Unprotected APIs are vulnerable to abuse, especially when exposed as agent tools where automated callers can generate high request volumes. **First step**: Add `ThrottlingBurstLimit` and `ThrottlingRateLimit` to the API Gateway `MethodSettings` in `template.yml`.

---

## Detailed Findings

### Infrastructure & Platform

#### INF-Q1: Compute
- **Score**: 4/4 ✅
- **Finding**: All compute is AWS Lambda. `template.yml` defines three `AWS::Serverless::Function` resources: `GetAllBooks`, `CreateBook`, and `CreateBookPreTraffic`, all running Node.js 22.x with 512 MB memory and 5-second timeout. No EC2 instances or self-managed compute detected anywhere in the repository.
- **Gap**: None. Compute is fully serverless.
- **Recommendation**: No action needed. Consider monitoring Lambda cold start latency as the service grows.

#### INF-Q2: Databases
- **Score**: 4/4 ✅
- **Finding**: `template.yml` defines `BooksTable` as `AWS::Serverless::SimpleTable` (DynamoDB) with `SSESpecification.SSEEnabled: true`. DynamoDB is a fully managed serverless database with automatic failover, no patching, and no version management required. Primary key is `isbn` (String).
- **Gap**: None. Database is fully managed.
- **Recommendation**: No action needed. Consider enabling DynamoDB point-in-time recovery (PITR) for additional data protection.

#### INF-Q3: Workflow Orchestration
- **Score**: 1/4 ❌
- **Finding**: No workflow orchestration service found. No `aws_sfn_*` resources in `template.yml`, no Temporal or Camunda SDK imports in any `package.json`. The application follows a simple request-response pattern: API Gateway → Lambda → DynamoDB.
- **Gap**: No dedicated workflow orchestration for multi-step processes. Agentic workflows require orchestration for tool chaining, retries, and state management.
- **Recommendation**: Introduce AWS Step Functions for orchestrating multi-step agent workflows. Start with a simple Express Workflow wrapping the existing create and get-all operations to establish the pattern.

#### INF-Q4: Async Messaging
- **Score**: 1/4 ❌
- **Finding**: No SQS, SNS, EventBridge, or any messaging resources found in `template.yml` or `pipeline/lib/pipeline-stack.ts`. All communication is synchronous HTTP via API Gateway.
- **Gap**: No async messaging infrastructure. Agents that trigger long-running operations need async patterns for reliable execution.
- **Recommendation**: Add an EventBridge event bus for book lifecycle events (created, updated, deleted). This enables event-driven integrations and decoupled agent tool patterns.

#### INF-Q5: Infrastructure as Code
- **Score**: 4/4 ✅
- **Finding**: `template.yml` (SAM/CloudFormation) defines all application infrastructure: Lambda functions, DynamoDB table, API Gateway, Cognito User Pool, CloudWatch Alarms, and IAM policies. `pipeline/lib/pipeline-stack.ts` (CDK) defines the complete CI/CD pipeline including CodePipeline, CodeBuild projects, S3 artifact buckets, and IAM roles. Coverage is comprehensive — no resource requires manual creation.
- **Gap**: None. IaC coverage is comprehensive.
- **Recommendation**: No action needed. Consider migrating the SAM template to CDK for a unified IaC language across application and pipeline.

#### INF-Q6: CI/CD
- **Score**: 4/4 ✅
- **Finding**: Full CI/CD pipeline defined in `pipeline/lib/pipeline-stack.ts` with four stages: Source (GitHub via CodeStar Connections), Build (`pipeline/buildspec.json` — runs unit tests + SAM build + SAM package), Staging (deploy via `buildspec-deploy.json` + e2e tests via `buildspec-test.json`), Production (manual approval + deploy). Unit tests run in the Build stage. End-to-end tests run against the deployed staging environment.
- **Gap**: None. Full CI/CD automation with test, build, and deploy stages.
- **Recommendation**: No action needed. Consider adding security scanning (SAST/SCA) to the Build stage.

#### INF-Q7: API Entry Point
- **Score**: 3/4 🟡
- **Finding**: `BooksApi` (`AWS::Serverless::Api`) in `template.yml` provides API Gateway with `CognitoAuth` authorizer, `LoggingLevel: INFO`, and `TracingEnabled: true`. The API serves as the single entry point with stage variables for Lambda alias routing.
- **Gap**: No throttling configuration (`ThrottlingBurstLimit`/`ThrottlingRateLimit`), no request validation models, no WAF integration.
- **Recommendation**: Add throttling settings to the API Gateway `MethodSettings`, define request validation models for the POST /books endpoint, and attach a WAF WebACL for additional protection.

#### INF-Q8: Real-time Streaming
- **Score**: 1/4 ❌
- **Finding**: No Kinesis, MSK, or any streaming service found in `template.yml` or any IaC file. No streaming SDK imports in any `package.json`.
- **Gap**: No real-time streaming capability. Not currently needed for the simple CRUD API, but would be required for real-time book catalog event processing in an agentic context.
- **Recommendation**: If event-driven patterns are adopted (see INF-Q4), consider DynamoDB Streams to capture table changes and propagate them to downstream consumers.

#### INF-Q9: Network Security
- **Score**: 1/4 ❌
- **Finding**: No VPC configuration found in `template.yml`. Lambda functions run in default AWS-managed networking without VPC attachment. No `aws_vpc`, `aws_subnet`, or `aws_security_group` resources. The API Gateway is publicly accessible.
- **Gap**: No network segmentation, no private subnets, no security groups. Lambda functions access DynamoDB over the public AWS network.
- **Recommendation**: For the current serverless architecture, add a VPC with private subnets and a DynamoDB VPC endpoint for enhanced network isolation. Alternatively, if the security posture requires it, attach Lambda functions to a VPC with a DynamoDB gateway endpoint.

#### INF-Q10: Auto-scaling
- **Score**: 2/4 🟠
- **Finding**: Lambda inherently auto-scales per invocation. `template.yml` defines `DeploymentPreference` with `Linear10PercentEvery1Minute` for production deployments. However, no explicit `ReservedConcurrentExecutions` or `ProvisionedConcurrencyConfig` is set on any Lambda function. The DynamoDB table (`AWS::Serverless::SimpleTable`) defaults to on-demand billing, which auto-scales.
- **Gap**: No explicit Lambda concurrency limits to prevent runaway scaling or protect downstream resources (DynamoDB). No provisioned concurrency for predictable cold start performance.
- **Recommendation**: Set `ReservedConcurrentExecutions` on Lambda functions to cap maximum concurrency and protect DynamoDB throughput. Consider `ProvisionedConcurrencyConfig` on the production alias if cold start latency becomes a concern for agent tool response times.

### Application Architecture

#### APP-Q1: Programming Languages
- **Score**: 3/4 🟡
- **Finding**: TypeScript is the primary language, running on Node.js 22.x (`Runtime: nodejs22.x` in `template.yml` Globals). Dependencies in `src/books/create/package.json` and `src/books/get-all/package.json` include `aws-sdk`, `aws-xray-sdk-core`, and TypeScript 5.7.3. The pipeline CDK app also uses TypeScript.
- **Gap**: TypeScript has a good but not best-in-class agent framework ecosystem. Python has the richest agent tooling (LangChain, Strands, CrewAI), though TypeScript support is growing rapidly.
- **Recommendation**: TypeScript is a strong choice. When adding agent capabilities, leverage TypeScript-compatible frameworks like LangChain.js or the AWS SDK for JavaScript with Bedrock.

#### APP-Q2: API Documentation
- **Score**: 1/4 ❌
- **Finding**: `OpenApiVersion: 3.0.1` is set in `template.yml` under `Globals.Api` to suppress default stage creation, but no actual OpenAPI specification file exists. No `openapi.yaml`, `swagger.json`, `api-docs/` directory, or inline `DefinitionBody` in the `BooksApi` resource. No `@ApiOperation` or similar annotations in source code.
- **Gap**: No machine-readable API documentation. Agents require OpenAPI specs to discover available operations, understand request/response schemas, and auto-generate tool definitions.
- **Recommendation**: Create an `openapi.yaml` file documenting both endpoints (GET /books, POST /books), including request body schema for the book object (`isbn`, `title`, `year`, `author`, `publisher`, `rating`, `pages`), response schemas, and Cognito auth requirements. Reference it in the SAM template using `DefinitionBody`.

#### APP-Q3: Async vs Sync Communication
- **Score**: 1/4 ❌
- **Finding**: All communication is synchronous. The application follows a request-response pattern: API Gateway → Lambda → DynamoDB. `src/books/create/index.ts` performs a synchronous `putItem` call; `src/books/get-all/index.ts` performs a synchronous `scan` call. No SQS publishing, SNS notifications, or EventBridge event emission found in any source file.
- **Gap**: 100% synchronous communication. No async patterns available for long-running or event-driven agent interactions.
- **Recommendation**: For the current two-endpoint API, sync is appropriate. When adding agent capabilities, introduce async patterns for operations that may take longer (e.g., batch book imports, AI-powered book recommendations). Use SQS or EventBridge for decoupled processing.

#### APP-Q4: Monolith vs Microservices
- **Score**: 4/4 ✅
- **Finding**: This is a single-purpose serverless microservice with clear boundaries. It manages one domain (books) with two Lambda functions (`CreateBook`, `GetAllBooks`) sharing a single DynamoDB table (`BooksTable`). Each Lambda has its own `package.json`, dependencies, and test suite. The `CreateBookPreTraffic` function is a deployment hook, not a business function.
- **Gap**: None. The service is already well-decomposed as a focused microservice.
- **Recommendation**: No action needed. Maintain the current single-responsibility design. When new domains are added (e.g., users, recommendations), create separate services rather than expanding this one.

#### APP-Q5: API Response Format
- **Score**: 4/4 ✅
- **Finding**: All API responses use JSON. `src/books/get-all/index.ts` returns `JSON.stringify(bookDtos)` with `headers: { 'Content-Type': 'application/json' }`. `src/books/create/index.ts` returns status 201 with `Content-Type: application/json`. Error responses return empty body strings.
- **Gap**: None. Structured JSON responses across all endpoints.
- **Recommendation**: No action needed. Consider adding structured error response bodies (e.g., `{ "error": "message", "code": "ERROR_CODE" }`) to aid agent error handling.

#### APP-Q6: Workflow Logic
- **Score**: 1/4 ❌
- **Finding**: No workflow orchestration. Lambda handlers contain direct, single-step business logic: `create/index.ts` parses the request body and calls `client.putItem()`; `get-all/index.ts` calls `client.scan()`. No Step Functions, no saga patterns, no workflow engine SDK imports.
- **Gap**: No orchestration for multi-step processes. Agentic workflows that chain multiple tools (e.g., search books → check availability → place order) require dedicated orchestration.
- **Recommendation**: Introduce AWS Step Functions for future multi-step workflows. Define a simple Express Workflow that demonstrates tool chaining with the existing endpoints.

#### APP-Q7: Idempotency
- **Score**: 2/4 🟠
- **Finding**: `src/books/create/index.ts` uses DynamoDB `putItem` with `isbn` as the primary key. If the same `isbn` is submitted twice, the item is overwritten (DynamoDB's native upsert behavior), providing database-level idempotency. However, there is no `Idempotency-Key` header processing, no application-level deduplication, and no idempotency token in the API schema.
- **Gap**: No explicit API-layer idempotency mechanism. The `putItem` behavior is a side effect of the data model, not an intentional idempotency pattern. If the schema changes, idempotency could be lost.
- **Recommendation**: Implement explicit idempotency using `@aws-lambda-powertools/idempotency` with a DynamoDB-backed idempotency store. Accept an `Idempotency-Key` header on the POST /books endpoint.

#### APP-Q8: Rate Limiting & Throttling
- **Score**: 1/4 ❌
- **Finding**: No rate limiting found. The `BooksApi` in `template.yml` has `MethodSettings` with `LoggingLevel: INFO` but no `ThrottlingBurstLimit` or `ThrottlingRateLimit`. No WAF WebACL attached. No application-level rate limiting middleware in Lambda code. No `AWS::ApiGateway::UsagePlan` resource.
- **Gap**: API is completely unprotected against request floods. Agent-driven traffic can generate high request volumes.
- **Recommendation**: Add `ThrottlingBurstLimit` and `ThrottlingRateLimit` to the API Gateway MethodSettings. Create a UsagePlan with API keys for agent clients. Consider adding AWS WAF with rate-based rules.

#### APP-Q9: Resilience Patterns
- **Score**: 1/4 ❌
- **Finding**: Lambda handlers use basic try/catch blocks. `src/books/create/index.ts` catches all exceptions and returns 500. `src/books/get-all/index.ts` does the same. No circuit breakers, retry decorators, timeout configurations, or exponential backoff in application code. The AWS SDK v2 (`aws-sdk: ^2.1692.0`) has built-in retry with exponential backoff for DynamoDB calls, but this is not explicitly configured.
- **Gap**: No application-level resilience patterns. When this API becomes an agent tool, failures will propagate directly to the agent without graceful degradation.
- **Recommendation**: Migrate from AWS SDK v2 to AWS SDK v3 (`@aws-sdk/client-dynamodb`) which is modular and the current standard. Configure explicit retry strategies and timeouts. Add structured error responses to help agents understand and recover from failures.

#### APP-Q10: Long-running Processes
- **Score**: 3/4 🟡
- **Finding**: Lambda timeout is 5 seconds (`Timeout: 5` in Globals). Both business functions perform single DynamoDB operations (putItem, scan) that complete well within this timeout. The `CreateBookPreTraffic` hook has a `wait()` function with a 1.5-second delay for eventual consistency, which is appropriate for a deployment check.
- **Gap**: No operations exceed 30 seconds, so async handling is not currently needed. However, the `scan` operation in `get-all/index.ts` could become slow as the table grows (no pagination implemented).
- **Recommendation**: Implement pagination for the `GetAllBooks` endpoint to prevent timeouts as the table scales. If future operations exceed 30 seconds (e.g., batch imports, AI processing), implement async job patterns with SQS.

#### APP-Q11: API Versioning
- **Score**: 1/4 ❌
- **Finding**: No API versioning found. API paths are `/books` (GET and POST) with no version prefix. No `/v1/` or `/v2/` URL patterns in `template.yml`. No `Accept-Version` header handling. No changelog file for API changes.
- **Gap**: No versioning strategy. Breaking changes to the API will affect all agent tool consumers simultaneously.
- **Recommendation**: Introduce URL path versioning (e.g., `/v1/books`) in the API Gateway path definitions. Establish a versioning policy and changelog before exposing this API as an agent tool.

#### APP-Q12: Service Discovery & Mesh
- **Score**: 2/4 🟠
- **Finding**: This is a single service. The DynamoDB table name is passed via environment variable (`TABLE: !Ref BooksTable` in `template.yml`). The API endpoint is exported as a CloudFormation Output (`ApiEndpoint`). No hard-coded service endpoints in Lambda code. However, there is no service registry, API catalog, or discovery mechanism.
- **Gap**: No service discovery. The CloudFormation output is the only way other services discover this API. Agents need a programmatic way to discover available tools.
- **Recommendation**: For a single service, the current approach is adequate. When adding more services, implement AWS Cloud Map or an API catalog. The OpenAPI spec (from APP-Q2) can serve as the initial tool catalog for agents.

#### APP-Q13: AI/Agent Frameworks
- **Score**: 1/4 ❌
- **Finding**: No AI or agent frameworks found. Dependencies in `src/books/create/package.json` and `src/books/get-all/package.json` contain only `aws-sdk` and `aws-xray-sdk-core`. No `@aws-sdk/client-bedrock-runtime`, `langchain`, `@langchain/core`, `openai`, `anthropic`, `strands-agents`, or any AI SDK detected. No MCP server or tool definitions.
- **Gap**: No AI/agent integration capability. The API cannot serve as an agent tool or invoke AI services.
- **Recommendation**: Start with `@aws-sdk/client-bedrock-runtime` to add AI capabilities. Create an MCP (Model Context Protocol) tool definition that wraps the existing REST endpoints. Consider Strands Agents SDK or LangChain.js for agent orchestration.

### Data Foundations

#### DATA-Q1: Vector Database Presence
- **Score**: 1/4 ❌
- **Finding**: No vector database found. `template.yml` contains only a DynamoDB table (`AWS::Serverless::SimpleTable`). No OpenSearch domain, no Aurora with pgvector, no S3 Vectors configuration, no Bedrock Knowledge Bases. No vector database SDK imports in any `package.json` (no Pinecone, Weaviate, Chroma, or similar).
- **Gap**: No vector storage capability. Semantic search over the book catalog (e.g., "find books similar to science fiction classics") is not possible.
- **Recommendation**: Evaluate Amazon Bedrock Knowledge Bases for a managed RAG solution, or add OpenSearch Serverless with vector search capability for the book catalog. Start with a proof-of-concept embedding book titles and descriptions.

#### DATA-Q2: Vector DB Management
- **Score**: 1/4 ❌
- **Finding**: No vector database exists (see DATA-Q1). No managed or self-hosted vector DB detected.
- **Gap**: No vector DB to manage.
- **Recommendation**: When adding a vector DB (see DATA-Q1), choose a fully managed option: Amazon Bedrock Knowledge Bases or Amazon OpenSearch Serverless.

#### DATA-Q3: RAG Implementation
- **Score**: 1/4 ❌
- **Finding**: No RAG pipeline components found. No embedding model calls (no Bedrock Titan Embeddings, no OpenAI ada), no document chunking/splitting code, no `similarity_search` or `knn_search` patterns in any source file. No Bedrock Knowledge Base integration.
- **Gap**: No semantic search or retrieval-augmented generation capability.
- **Recommendation**: Implement a RAG pipeline for the book catalog: (1) Generate embeddings for book metadata using Amazon Bedrock Titan Embeddings, (2) Store embeddings in a vector database, (3) Create a semantic search endpoint that agents can use for natural language book discovery.

#### DATA-Q4: Data Source Sprawl
- **Score**: 4/4 ✅
- **Finding**: Single data source — DynamoDB table `BooksTable` (defined as `AWS::Serverless::SimpleTable` in `template.yml`). Both Lambda functions (`create/index.ts` and `get-all/index.ts`) connect to the same table via the `TABLE` environment variable. No other databases, APIs, or external data sources.
- **Gap**: None. Clean single-source architecture.
- **Recommendation**: No action needed. Maintain the single data source pattern as long as it meets requirements.

#### DATA-Q5: Data Access Pattern
- **Score**: 2/4 🟠
- **Finding**: Lambda handlers make direct DynamoDB SDK calls. `src/books/create/index.ts` instantiates `new AWS.DynamoDB()` and calls `client.putItem()` directly. `src/books/get-all/index.ts` does the same with `client.scan()`. `src/books/create-pre-traffic/index.ts` uses `getItem` and `deleteItem` directly. No data access abstraction layer, no repository pattern.
- **Gap**: Business logic and data access are tightly coupled in the same handler files. DynamoDB client initialization code is duplicated across `create/index.ts` and `get-all/index.ts` (identical X-Ray wrapping logic).
- **Recommendation**: Extract DynamoDB operations into a shared data access module (repository pattern). This creates a clean interface that agents can invoke without coupling to the database implementation.

#### DATA-Q6: Unstructured Data
- **Score**: 1/4 ❌
- **Finding**: No S3 storage for documents. No Textract, Tika, or document parsing libraries in any `package.json`. The application only handles structured book metadata (isbn, title, year, author, publisher, rating, pages).
- **Gap**: No unstructured data processing capability. If book descriptions, reviews, or PDF catalogs need to be processed by agents, there is no pipeline.
- **Recommendation**: If book-related documents (PDFs, reviews, images) are needed in the future, add an S3 bucket with a document processing pipeline using Amazon Textract or a lightweight parsing library.

#### DATA-Q7: Schema Documentation
- **Score**: 1/4 ❌
- **Finding**: No formal schema documentation. The book schema is implicitly defined in the Lambda code — `src/books/create/index.ts` destructures `{ isbn, title, year, author, publisher, rating, pages }` from the request body. The DynamoDB table only defines the primary key (`isbn: String`). No JSON Schema files, no Avro/Protobuf definitions, no database migration files.
- **Gap**: Schema is not documented or versioned. Changes to the book schema are not tracked. Agents need schema information to construct valid requests.
- **Recommendation**: Define a JSON Schema for the book entity and reference it in the OpenAPI spec (see APP-Q2). Add input validation using a schema validation library (e.g., `zod` or `ajv`) in the Lambda handlers.

#### DATA-Q8: Data Access Layer
- **Score**: 1/4 ❌
- **Finding**: DynamoDB SDK calls are embedded directly in Lambda handler files. `create/index.ts` and `get-all/index.ts` each independently initialize the DynamoDB client (with identical X-Ray wrapping logic) and make direct API calls. There is no shared repository, DAO, or data access layer module. The test utility `src/books/tests/books-manager.js` implements a rudimentary data access pattern but is only used for e2e tests, not in production code.
- **Gap**: No unified data access layer. Code duplication between handlers. Adding new operations requires re-implementing DynamoDB client setup.
- **Recommendation**: Create a shared `books-repository.ts` module that encapsulates all DynamoDB operations (get, getAll, create, delete). Use this module in Lambda handlers and as the foundation for agent tool implementations.

#### DATA-Q9: Embedding Freshness
- **Score**: 1/4 ❌
- **Finding**: No embeddings exist (see DATA-Q1 and DATA-Q3). No event-driven embedding refresh triggers, no scheduled re-indexing pipelines, no CDC patterns.
- **Gap**: No embedding pipeline to keep fresh.
- **Recommendation**: When implementing embeddings (see DATA-Q3), use DynamoDB Streams to trigger automatic re-embedding when book records are created or updated, ensuring the vector index stays current.

#### DATA-Q10: Database Engine Version & EOL
- **Score**: 4/4 ✅
- **Finding**: DynamoDB is a fully managed serverless database service. There is no engine version to pin — AWS manages all versioning, patching, and lifecycle. The `BooksTable` in `template.yml` uses `AWS::Serverless::SimpleTable` which abstracts away all engine management.
- **Gap**: None. DynamoDB has no EOL concerns.
- **Recommendation**: No action needed. DynamoDB is evergreen.

#### DATA-Q11: Stored Procedures & Schema Complexity
- **Score**: 4/4 ✅
- **Finding**: DynamoDB does not support stored procedures, triggers, or proprietary SQL. All business logic resides in the Lambda application layer (`src/books/create/index.ts` and `src/books/get-all/index.ts`). No `.sql` files found in the repository. No ORM bypass patterns or raw SQL execution.
- **Gap**: None. All logic is in the application layer.
- **Recommendation**: No action needed. Continue keeping business logic in the application layer.

### Identity, Security & Governance

#### SEC-Q1: Secret Management
- **Score**: 3/4 🟡
- **Finding**: No hardcoded secrets found in any source file. DynamoDB table name is passed via environment variable (`TABLE: !Ref BooksTable`). The GitHub connection ARN for the CI/CD pipeline is stored in AWS SSM Parameter Store (`StringParameter.fromStringParameterName(this, 'GithubConnectionArn', 'github_connection_arn')` in `pipeline/lib/pipeline-stack.ts`). DynamoDB access uses IAM role-based authentication, not credentials.
- **Gap**: No Secrets Manager usage, though the current architecture has no secrets to manage. If external API keys or database credentials are added, there is no established pattern for Secrets Manager.
- **Recommendation**: Establish a Secrets Manager pattern proactively. When adding Bedrock or external AI APIs, store API keys in Secrets Manager from day one. Add `.env` to `.gitignore` (currently `.gitignore` excludes `node_modules`, `dist`, `.vscode`, `.aws-sam` but not `.env`).

#### SEC-Q2: IAM Least Privilege
- **Score**: 2/4 🟠
- **Finding**: Lambda function IAM policies in `template.yml` use SAM policy templates that are resource-scoped: `DynamoDBReadPolicy` for `GetAllBooks`, `DynamoDBWritePolicy` for `CreateBook`, `DynamoDBCrudPolicy` for `CreateBookPreTraffic`. These are good practice. However, the CI/CD pipeline in `pipeline/lib/pipeline-stack.ts` attaches broad AWS-managed policies to the deploy project role: `AWSCloudFormationFullAccess`, `AmazonDynamoDBFullAccess`, `AWSLambda_FullAccess`, `AmazonAPIGatewayAdministrator`, `IAMFullAccess`, `AWSCodeDeployFullAccess`, `AmazonCognitoPowerUser`.
- **Gap**: Pipeline IAM roles use wildcard `FullAccess` managed policies — 7 overly-permissive policies attached to the deploy project. This violates least-privilege and creates a blast radius risk.
- **Recommendation**: Replace the broad managed policies on the deploy CodeBuild role with custom IAM policies scoped to the specific resources deployed by the SAM template. Use `iam:PassRole` with specific role ARNs instead of `IAMFullAccess`.

#### SEC-Q3: Identity Propagation
- **Score**: 2/4 🟠
- **Finding**: Cognito User Pool (`CognitoUserPool` in `template.yml`) provides OAuth2 implicit flow for the `CreateBook` endpoint. The `CognitoAuth` authorizer validates tokens at the API Gateway level. `UserPoolClient` supports `implicit` flow and `ALLOW_REFRESH_TOKEN_AUTH`. For staging, `ALLOW_USER_PASSWORD_AUTH` is enabled for automated testing.
- **Gap**: Token-based auth exists only at the API Gateway boundary. No user identity is propagated from the JWT into the Lambda function (the handler does not extract or use the caller's identity). Single service, so cross-service propagation is not yet needed.
- **Recommendation**: Extract the Cognito user identity from the API Gateway event context (`event.requestContext.authorizer.claims`) in Lambda handlers. This establishes the pattern for identity-aware agent actions (e.g., "who created this book").

#### SEC-Q4: Audit Logging
- **Score**: 2/4 🟠
- **Finding**: API Gateway has `LoggingLevel: INFO` and `TracingEnabled: true` configured in `template.yml`. The `ApiGatewayLoggingRole` IAM role enables CloudWatch logging for the API. X-Ray tracing is active on all Lambda functions (Globals `Tracing: Active`).
- **Gap**: No CloudTrail configuration in any IaC file. No log file validation or immutable storage. API Gateway logging captures request/response but CloudTrail is needed for a complete audit trail of API and data plane activity.
- **Recommendation**: Add CloudTrail configuration to `template.yml` with log file validation enabled and an S3 bucket with Object Lock for immutable audit log storage.

#### SEC-Q5: API Rate Limits
- **Score**: 1/4 ❌
- **Finding**: No throttling configuration on the `BooksApi` API Gateway. The `MethodSettings` in `template.yml` only sets `LoggingLevel`. No `ThrottlingBurstLimit`, `ThrottlingRateLimit`, or `AWS::ApiGateway::UsagePlan` defined. No WAF WebACL attached. No application-level rate limiting.
- **Gap**: API is completely unprotected against rate abuse. When exposed as an agent tool, automated callers can generate unlimited requests.
- **Recommendation**: Add `ThrottlingBurstLimit: 100` and `ThrottlingRateLimit: 50` (adjust to expected load) to MethodSettings. Create a UsagePlan with API keys for agent clients to enable per-client quotas.

#### SEC-Q6: PII Redaction
- **Score**: 1/4 ❌
- **Finding**: No PII redaction or log scrubbing found in any source file. `src/books/create-pre-traffic/index.ts` uses `console.log('DynamoDB item', JSON.stringify(Item, null, 2))` which logs full database items to CloudWatch. Error handlers in `create/index.ts` and `get-all/index.ts` return empty bodies (good — no PII in error responses), but no explicit PII filtering or masking middleware exists.
- **Gap**: No PII detection or redaction pipeline. Book author names and potentially sensitive metadata could be logged or exposed.
- **Recommendation**: Add PII redaction to logging. Use `@aws-lambda-powertools/logger` with custom serializers to mask sensitive fields. Consider enabling Amazon Macie on any S3 buckets storing logs.

#### SEC-Q7: Human Approval Workflows
- **Score**: 2/4 🟠
- **Finding**: `ManualApprovalAction` in `pipeline/lib/pipeline-stack.ts` gates production deployments with human review: `additionalInformation: 'Ensure Books API works correctly in Staging and release date is agreed with Product Owners'`. This provides deployment-level human-in-the-loop.
- **Gap**: No human approval for data operations (e.g., bulk book deletions, data modifications). The current scope is limited to deployment approval. No approval workflow for agent-initiated actions.
- **Recommendation**: When adding agent capabilities, implement human approval gates for high-risk data operations using Step Functions with `waitForTaskToken` pattern. Start with agent-initiated bulk operations.

#### SEC-Q8: Encryption at Rest
- **Score**: 2/4 🟠
- **Finding**: DynamoDB table has `SSESpecification.SSEEnabled: true` in `template.yml` (uses AWS-managed encryption keys). S3 buckets in `pipeline/lib/pipeline-stack.ts` use `BucketEncryption.S3_MANAGED`. All data at rest is encrypted with AWS-managed keys.
- **Gap**: No customer-managed KMS keys (CMKs). AWS-managed keys provide encryption but do not allow key rotation control, cross-account access control, or key usage auditing through CloudTrail.
- **Recommendation**: Create customer-managed KMS keys for the DynamoDB table and S3 buckets. This enables key rotation policies, fine-grained access control, and key usage auditing — important for compliance when agents access sensitive data.

#### SEC-Q9: API Authentication
- **Score**: 2/4 🟠
- **Finding**: `CognitoAuth` authorizer is configured on the `CreateBook` endpoint (POST /books) with OAuth scope `email`. The `GetAllBooks` endpoint (GET /books) has no authentication — it is publicly accessible. The `UserPoolClient` supports OAuth implicit flow with `openid` and `email` scopes.
- **Gap**: Only 50% of API endpoints are authenticated. The GET /books endpoint is public, meaning anyone (or any agent) can read the entire book catalog without authentication.
- **Recommendation**: Add Cognito authentication to the GET /books endpoint. If public read access is intentional, document it as a security decision and add rate limiting as compensating control. For agent access, create a machine-to-machine client credentials flow.

#### SEC-Q10: Centralized Identity
- **Score**: 3/4 🟡
- **Finding**: `CognitoUserPool` with `UserPoolClient` and `UserPoolDomain` in `template.yml`. Single Cognito User Pool serves as the identity provider for the API. The domain is configured as `book-api-{stage}-{accountId}`. Users authenticate with email-based accounts.
- **Gap**: OAuth implicit flow is used (considered less secure than authorization code flow with PKCE). No federation with external identity providers (Okta, Azure AD). No SSO configuration. Password policy is weak (`MinimumLength: 6`, no lowercase, no symbols, no uppercase required).
- **Recommendation**: Upgrade to authorization code flow with PKCE. Strengthen the password policy. Consider federation with an enterprise IdP if this API serves an organizational context. Add a machine-to-machine client credentials flow for agent authentication.

### Operations & Observability

#### OPS-Q1: Distributed Tracing
- **Score**: 3/4 🟡
- **Finding**: AWS X-Ray is integrated throughout. `template.yml` sets `Tracing: Active` in Lambda Globals and `TracingEnabled: true` on the `BooksApi`. Both business Lambda functions (`src/books/create/index.ts` and `src/books/get-all/index.ts`) use `aws-xray-sdk-core` to instrument the AWS SDK: `AWSXRay.captureAWS(AWSCore)`. This captures DynamoDB call traces. X-Ray SDK is in both `package.json` dependencies (`aws-xray-sdk-core: ^3.10.3`).
- **Gap**: No OpenTelemetry integration. No `gen_ai.*` semantic conventions for future LLM span tracking. Tracing is limited to AWS SDK calls — custom business logic is not instrumented with custom subsegments. No service map configuration beyond automatic X-Ray.
- **Recommendation**: Add custom X-Ray subsegments for business logic (e.g., request parsing, validation). When adding AI capabilities, integrate OpenTelemetry with `gen_ai.*` semantic conventions for LLM call tracing. Consider migrating to AWS Distro for OpenTelemetry (ADOT) for vendor-neutral telemetry.

#### OPS-Q2: Structured Logging
- **Score**: 1/4 ❌
- **Finding**: `src/books/create-pre-traffic/index.ts` uses `console.log()` for logging (e.g., `console.log('Entering PreTraffic Hook!')`, `console.log('DynamoDB item', JSON.stringify(Item, null, 2))`). The business handlers (`create/index.ts` and `get-all/index.ts`) have no logging at all — errors are caught silently and return 500. No structured logging library (no winston, pino, @aws-lambda-powertools/logger). No correlation IDs. No JSON log formatting.
- **Gap**: No structured logs. No correlation IDs. Cannot trace agent requests across Lambda invocations. Silent error handling means failures are invisible in logs.
- **Recommendation**: Add `@aws-lambda-powertools/logger` to all Lambda functions. Configure JSON output format with automatic correlation ID injection. Add logging for all request/response cycles and error details.

#### OPS-Q3: Automated Evals
- **Score**: 1/4 ❌
- **Finding**: No agent evaluation framework found. No eval datasets, no scoring scripts, no LLM-as-judge patterns, no golden dataset files, no RAGAS integration. Unit tests (`src/books/create/tests/index.spec.ts`, `src/books/get-all/tests/index.spec.ts`) and e2e tests (`src/books/tests/index.js`) test the API but not AI/agent behavior.
- **Gap**: No agent evaluation pipeline. When agents are introduced, there is no framework to measure agent quality, accuracy, or safety.
- **Recommendation**: When building agent capabilities, establish an eval framework from day one. Use golden datasets for expected agent responses, implement LLM-as-judge scoring, and integrate eval runs into the CI/CD pipeline.

#### OPS-Q4: SLOs
- **Score**: 1/4 ❌
- **Finding**: CloudWatch alarms exist for Lambda errors: `CreateBookAliasErrorMetricGreaterThanZeroAlarm` and `GetAllBooksAliasErrorMetricGreaterThanZeroAlarm` in `template.yml`. These are binary threshold alarms (error count > 0) used for deployment rollback, not SLO tracking. No SLO definitions, no p99/p95 latency alarms, no error budget tracking, no availability targets.
- **Gap**: No SLOs defined for any user journey. The existing alarms are deployment safety mechanisms, not service-level objectives.
- **Recommendation**: Define SLOs for the books API: availability target (e.g., 99.9%), p99 latency target (e.g., < 500ms), error rate target (e.g., < 0.1%). Create CloudWatch composite alarms and dashboards to track these.

#### OPS-Q5: Rollback Capability
- **Score**: 3/4 🟡
- **Finding**: `template.yml` defines `DeploymentPreference` for production: `Linear10PercentEvery1Minute` with CloudWatch alarm-based rollback. `CreateBookPreTraffic` Lambda performs a smoke test before traffic shifting — it invokes the new version, verifies the book was written to DynamoDB, then cleans up the test data. If the smoke test fails, `CodeDeploy.putLifecycleEventHookExecutionStatus` reports `Failed` and traffic is not shifted. Staging uses `AllAtOnce`.
- **Gap**: No rollback for configuration changes or prompts (not currently applicable, but will be when AI is added). No feature flags for gradual feature rollout independent of deployment.
- **Recommendation**: Maintain the current deployment rollback pattern. When adding AI capabilities, implement prompt versioning with rollback capability. Consider adding AWS AppConfig for feature flags.

#### OPS-Q6: LLM Cost Tracking
- **Score**: 1/4 ❌
- **Finding**: No LLM usage in the application. No token counting, no cost attribution, no per-request LLM cost metrics. No CloudWatch custom metrics for AI usage.
- **Gap**: No LLM cost tracking infrastructure. When agents are introduced, there will be no visibility into token usage or cost per request.
- **Recommendation**: When integrating Bedrock or other LLMs, implement token usage tracking from day one. Log the `usage` object from LLM responses, publish custom CloudWatch metrics for tokens consumed per function/feature, and tag costs by workflow.

#### OPS-Q7: Business Metrics
- **Score**: 1/4 ❌
- **Finding**: No custom business metrics found. No `cloudwatch.putMetricData()` calls in any Lambda function. No custom dashboards tracking business outcomes (books created per day, catalog size, API usage patterns). Only infrastructure-level alarms exist (Lambda error count).
- **Gap**: No business outcome visibility. Cannot measure the value of the books API or track agent effectiveness when agents are introduced.
- **Recommendation**: Add custom CloudWatch metrics for business events: `BooksCreated`, `BooksRetrieved`, `CatalogSize`. Create a CloudWatch dashboard combining business and infrastructure metrics. When agents are added, track `AgentTasksCompleted`, `AgentToolCalls`.

#### OPS-Q8: Anomaly Detection
- **Score**: 1/4 ❌
- **Finding**: CloudWatch alarms in `template.yml` use static thresholds (error count > 0) only. No anomaly detection on error rates or latency. No p99/p95 latency alarms. No PagerDuty, OpsGenie, or SNS integration for alerting. No composite alarms.
- **Gap**: No anomaly detection. Gradual degradation (increasing latency, rising error rates) will go undetected. Agentic systems can silently degrade without anomaly detection.
- **Recommendation**: Enable CloudWatch Anomaly Detection on Lambda invocation duration and error rate. Add p99 latency alarms. Configure SNS notifications for alarm state changes. When agents are added, monitor for behavioral anomalies (unusual tool call patterns).

#### OPS-Q9: Deployment Strategy
- **Score**: 3/4 🟡
- **Finding**: Production deployments use `Linear10PercentEvery1Minute` (gradual traffic shifting) with CloudWatch alarm-based rollback. `CreateBookPreTraffic` hook validates the new version before any traffic shift. Staging uses `AllAtOnce` for fast iteration. The CI/CD pipeline has a `ManualApprovalAction` before production deployment.
- **Gap**: Not a full canary deployment (no synthetic canary tests during traffic shift). No feature flags for independent feature rollout. No blue/green at the infrastructure level.
- **Recommendation**: The current linear deployment strategy is solid. Consider adding CloudWatch Synthetics canaries to continuously test the API during deployment. Add feature flags (AWS AppConfig) for agent feature rollout independent of code deployment.

#### OPS-Q10: Integration Testing
- **Score**: 3/4 🟡
- **Finding**: Comprehensive test coverage: Unit tests in `src/books/create/tests/index.spec.ts` (3 tests: putItem success, invalid body, DynamoDB failure) and `src/books/get-all/tests/index.spec.ts` (3 tests: scan success, empty results, DynamoDB failure) using Mocha, Chai, Sinon, and aws-sdk-mock. End-to-end tests in `src/books/tests/index.js` (4 tests: public GET, authenticated POST, missing auth, full CRUD flow) that run against the deployed staging API via `pipeline/buildspec-test.json`. Unit tests run in the Build stage; e2e tests run in the Staging stage.
- **Gap**: No contract tests. No load/performance tests. No security testing (e.g., OWASP ZAP). E2e tests could be expanded to cover edge cases (pagination, concurrent writes).
- **Recommendation**: Add contract tests for API schema validation. Add load tests to validate Lambda concurrency and DynamoDB throughput under agent-level traffic. Add security scanning to the CI pipeline.

#### OPS-Q11: Incident Response Automation
- **Score**: 1/4 ❌
- **Finding**: No runbook files in the repository (no markdown, YAML, or JSON runbooks). No SSM Automation documents. No Lambda-based remediation functions. No self-healing patterns beyond the deployment rollback mechanism. No links to runbooks in alarm configurations.
- **Gap**: No incident response automation. If the API fails, response is entirely manual. Agentic systems need rapid, automated incident response because they can cause harm at machine speed.
- **Recommendation**: Create runbooks for common failure scenarios (DynamoDB throttling, Lambda timeout spikes, API Gateway 5xx spikes). Implement SSM Automation documents for automated remediation. Link runbooks to CloudWatch alarms via SNS.

#### OPS-Q12: Observability Governance & Ownership
- **Score**: 1/4 ❌
- **Finding**: No CODEOWNERS file in the repository. No SLO definition files or dashboards with named owners. No evidence of observability ownership model. No platform team tooling or centralized observability stack configuration. Tags exist (`project: my-project`, `environment: !Ref Stage`) but no ownership tags.
- **Gap**: No observability ownership model. No defined responsibility for monitoring, alerting, or incident response. When agents are introduced, there will be no clear owner for agent-level SLOs.
- **Recommendation**: Add a CODEOWNERS file. Define service ownership and on-call responsibilities. Create an observability charter that covers SLOs, alerting, and dashboards. Add ownership tags to all resources.

---

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
| Move to Modern DevOps | Not Triggered | Medium | — | — | — |
| Move to AI | Triggered | Medium | High | APP-Q13: 1/4, DATA-Q1: 1/4, DATA-Q3: 1/4, OPS-Q3: 1/4, OPS-Q6: 1/4 | High |

### Parallel Execution Plan

Only one pathway (Move to AI) is triggered. No parallel execution or sequential dependency analysis is required.

**Single Track**: Move to AI — This is the primary modernization pathway for the books API. All other pathways are Not Triggered because the serverless architecture is already well-suited for cloud-native, containerized, managed database, and modern DevOps patterns.

### Move to AI

- **Priority**: High
- **Goal Alignment**: Medium
- **Trigger Criteria Met**:
  - APP-Q13: Score 1/4 — No AI/agent frameworks found in any dependency manifest
  - DATA-Q1: Score 1/4 — No vector database configured for semantic search
  - DATA-Q3: Score 1/4 — No RAG pipeline (no embeddings, no chunking, no similarity search)
  - OPS-Q3: Score 1/4 — No agent evaluation framework or automated eval pipeline
  - OPS-Q6: Score 1/4 — No LLM cost tracking or token usage metrics
- **Current State**: A clean serverless REST API with no AI capabilities. The API returns structured JSON responses and has a well-defined domain (books catalog) but no agent framework integration, no vector search, and no AI-powered features.
- **Target State**: An agent-ready books API where: (1) the existing REST endpoints are exposed as agent tools via OpenAPI spec and MCP definitions, (2) a vector database enables semantic book discovery, (3) a RAG pipeline provides natural language book search, (4) LLM cost tracking and agent evaluations are integrated into the CI/CD pipeline.
- **Key Activities**:
  1. Generate an OpenAPI spec for the existing API (enables agent tool discovery)
  2. Add `@aws-sdk/client-bedrock-runtime` and create a proof-of-concept agent tool wrapping the books API
  3. Deploy a vector database (Bedrock Knowledge Bases or OpenSearch Serverless) for semantic book search
  4. Build a RAG pipeline with Titan Embeddings for book metadata
  5. Implement an agent evaluation framework with golden datasets
  6. Add LLM cost tracking and token usage metrics to CloudWatch
- **Dependencies**: None — this is the only triggered pathway
- **Estimated Effort**: High — requires new infrastructure (vector DB), new code (agent framework, embeddings, eval framework), and new operational patterns (LLM monitoring)
- **Roadmap Phase Alignment**: Phase 2 (Foundation) for vector DB and RAG; Phase 3 (Advanced Capabilities) for full agent integration and evals
- **Relevant Learning Materials**: Module 7 — Move to AI

---

## Quick Agent Wins

Even before completing the full modernization roadmap, these agent opportunities are available based on your current architecture:

1. **JSON API Agent Tool Integration** — Your API already returns structured JSON responses (Content-Type: application/json) from both GET /books and POST /books endpoints. Agent tool integration is straightforward — a tool wrapper can parse responses directly without format conversion.
   - **Leverages**: Structured JSON responses in `src/books/get-all/index.ts` and `src/books/create/index.ts`
   - **Effort**: Low
   - **Value**: Immediate agent tool capability for book catalog operations

2. **Documentation-Powered Knowledge Agent** — Build a RAG-based knowledge agent using the existing `README.md` which contains detailed architecture, deployment, testing, and usage documentation. This demonstrates AI value without modifying the API itself.
   - **Leverages**: Comprehensive `README.md` (300+ lines covering architecture, local development, CI/CD, testing, token management)
   - **Effort**: Low
   - **Value**: Self-service developer assistant that can answer questions about the books API architecture and usage

3. **DevOps Agent for CI/CD** — Your fully automated CI/CD pipeline (Source → Build → Staging → Production) with CloudFormation outputs provides programmatic access to deployment status. Build a DevOps agent that can trigger deployments, check pipeline status, and report deployment health.
   - **Leverages**: Full CI/CD pipeline in `pipeline/lib/pipeline-stack.ts` with exported CloudFormation outputs (`ApiEndpoint`, `UserPoolId`, `BooksTable`)
   - **Effort**: Medium
   - **Value**: Automated deployment management and status reporting via natural language

> These opportunities can be pursued in parallel with the modernization roadmap.
> They demonstrate agent value early while foundations are being built.

---

## Readiness Roadmap

### Phase 1 — Quick Wins (Days 1–30)

1. **Generate OpenAPI Spec** — Create an `openapi.yaml` documenting GET /books and POST /books with full request/response schemas. Reference it in `template.yml` using `DefinitionBody`. This enables agent tool auto-discovery (addresses APP-Q2).
2. **Add Structured Logging** — Install `@aws-lambda-powertools/logger` in all three Lambda functions. Configure JSON output with correlation IDs. Replace `console.log` in `create-pre-traffic/index.ts` and add logging to `create/index.ts` and `get-all/index.ts` (addresses OPS-Q2).
3. **Add API Rate Limiting** — Configure `ThrottlingBurstLimit` and `ThrottlingRateLimit` in the API Gateway `MethodSettings` in `template.yml`. Create a `UsagePlan` with API keys (addresses APP-Q8, SEC-Q5).
4. **Define JSON Schema** — Create a JSON Schema for the book entity and add input validation using `zod` or `ajv` in the CreateBook Lambda handler (addresses DATA-Q7).
5. **Tighten Pipeline IAM** — Replace the 7 `FullAccess` managed policies on the deploy CodeBuild role in `pipeline/lib/pipeline-stack.ts` with custom least-privilege policies (addresses SEC-Q2).

### Phase 2 — Foundation (Months 1–3)

1. **Create Data Access Layer** — Extract DynamoDB operations from `create/index.ts` and `get-all/index.ts` into a shared `books-repository.ts` module. Eliminate code duplication for client initialization and X-Ray wrapping (addresses DATA-Q5, DATA-Q8).
2. **Migrate to AWS SDK v3** — Replace `aws-sdk` v2 with `@aws-sdk/client-dynamodb` and `@aws-sdk/lib-dynamodb`. This reduces bundle size, enables tree-shaking, and is the current standard (addresses APP-Q9).
3. **Deploy Vector Database** — Set up Amazon Bedrock Knowledge Bases or OpenSearch Serverless with vector search for the book catalog. Start with Titan Embeddings for book metadata (addresses DATA-Q1, DATA-Q2).
4. **Build RAG Pipeline** — Implement document embedding for book records using DynamoDB Streams → Lambda → Titan Embeddings → vector store. Add a semantic search endpoint (addresses DATA-Q3, DATA-Q9).
5. **Define SLOs and Alarms** — Create SLOs for availability (99.9%), p99 latency (< 500ms), and error rate (< 0.1%). Add CloudWatch composite alarms and anomaly detection (addresses OPS-Q4, OPS-Q8).
6. **Add API Versioning** — Introduce `/v1/books` URL path versioning and establish a backward-compatibility policy (addresses APP-Q11).
7. **Strengthen Authentication** — Add Cognito auth to GET /books, upgrade from implicit to authorization code flow with PKCE, strengthen password policy (addresses SEC-Q9, SEC-Q10).

### Phase 3 — Advanced Capabilities (Months 3–6)

1. **Integrate Agent Framework** — Add Amazon Bedrock Agent or Strands Agents SDK. Create MCP tool definitions wrapping the books API endpoints. Build a book catalog assistant agent (addresses APP-Q13).
2. **Implement Agent Evaluation** — Create golden datasets for expected agent responses. Build an automated eval pipeline with LLM-as-judge scoring. Integrate eval runs into the CI/CD pipeline (addresses OPS-Q3).
3. **Add LLM Observability** — Implement token usage tracking per request, publish CloudWatch custom metrics for AI usage, add cost attribution tags per workflow (addresses OPS-Q6).
4. **Introduce Workflow Orchestration** — Deploy AWS Step Functions for multi-step agent workflows (e.g., semantic search → fetch details → recommend similar books). Add human approval gates for high-risk operations (addresses INF-Q3, SEC-Q7).
5. **Add Business Metrics** — Publish custom CloudWatch metrics for `BooksCreated`, `BooksRetrieved`, `AgentToolCalls`, `SemanticSearchQueries`. Create a unified business + infrastructure dashboard (addresses OPS-Q7).
6. **Create Runbooks** — Write machine-readable runbooks for common incidents. Implement SSM Automation for self-healing scenarios. Link runbooks to CloudWatch alarms (addresses OPS-Q11, OPS-Q12).

---

## Recommended Self-Paced Learning Materials

**Module 7: Move to AI** *(Primary — Triggered Pathway)*

- AWS Modernization Pathways: Move to AI — https://skillbuilder.aws/learning-plan/VDFEE4ACCV/aws-modernization-pathways-move-to-ai-pathways-includes-labs/P3DAWPTN63
  - Comprehensive learning plan covering the full Move to AI pathway
- Introduction to Generative AI: Art of the Possible — https://skillbuilder.aws/learn/ZEVZZ1D4AS/introduction-to-generative-ai--art-of-the-possible/Y7MTGJCW1U
  - Understand what generative AI can do for your books API (semantic search, recommendations, content generation)
- Amazon Bedrock Getting Started — https://skillbuilder.aws/learn/63KTRM86DQ/amazon-bedrock-getting-started/SC2Y3HMAUE
  - Essential for integrating Bedrock models with the books API Lambda functions
- Essentials for Prompt Engineering — https://skillbuilder.aws/learn/XBNAVKA88J/essentials-of-prompt-engineering/9T9Q45EDTV
  - Learn effective prompt design for book catalog agent tools
- Build and Evaluate Retrieval Augmented Generation (RAG) Applications using Knowledge Bases for Amazon Bedrock (Lab) — https://skillbuilder.aws/learn/JRGWCFYT67/lab--build-and-evaluate-retrieval-augmented-generation-rag-applications-using-knowledge-bases-for-amazon-bedrock/A4MN58JB7A
  - Directly applicable — build a RAG pipeline for semantic book search
- Introduction to Agentic AI on AWS — https://skillbuilder.aws/learn/DNBD5MT8ZD/introduction-to-agentic-ai-on-aws/WAKAFK6UFY
  - Foundational course for understanding how to build agents that use the books API as a tool
- Creating an AWS DevOps AI Agent with the Strands Agents SDK (Lab) — https://skillbuilder.aws/learn/AH1GD8AJY3/lab--creating-an-aws-devops-ai-agent-with-the-strands-agents-sdk/A9SKJNMPJ2
  - Hands-on lab for building agents with the Strands SDK — applicable to creating a books catalog agent
- AWS PartnerCast: Deep Dive: Building Observable AI Agents with Strands, Amazon Bedrock Agent Core & SageMaker MLflow — https://skillbuilder.aws/learn/1EN76TZBB6/aws-partnercast--deep-dive-building-observable-ai-agents-with-strands-amazon-bedrock-agent-core--sagemaker-mlflow--technical/CX2K6XAT84
  - Covers agent observability — directly relevant to OPS-Q3 (eval framework) and OPS-Q6 (LLM cost tracking)

**Module 6: Move to Modern DevOps** *(Supporting — Observability Improvements)*

- AWS Modernization Pathways: Move to Modern DevOps — https://skillbuilder.aws/learning-plan/1FGEQKGPQD/aws-modernization-pathways-move-to-modern-devops-includes-labs/MNQZ2KPVCK
  - Comprehensive DevOps pathway covering CI/CD, observability, and deployment strategies
- Advanced Testing Practices Using AWS DevOps Tools — https://skillbuilder.aws/learn/1YC7UXUWBR/advanced-testing-practices-using-aws-devops-tools/A32U6G7NEQ
  - Applicable to improving the test suite (OPS-Q10) with contract tests and security scanning
- DevOps and AI on AWS: CloudWatch Anomaly Detection (Lab) — https://skillbuilder.aws/learn/RWYVJ73MXP/lab--devops-and-ai-on-aws-cloudwatch-anomaly-detection/BRPDNZUGU7
  - Directly applicable to OPS-Q8 (anomaly detection) improvement
- Monitor Python Applications Using Amazon CloudWatch Application Signals — https://skillbuilder.aws/learn/JMPDZD64MV/monitor-python-applications-using-amazon-cloudwatch-application-signals/2JP3J2MPCK
  - Applicable concepts for structured observability (OPS-Q1, OPS-Q2 improvements)

**Module 4: Move to Managed Databases** *(Supporting — Vector Database Knowledge)*

- AWS PartnerCast: Vector Databases for Generative AI Applications — https://skillbuilder.aws/learn/UQ74USQJHU/aws-partnercast--vector-databases-for-generative-ai-applications--technical/7DKMBAPCST
  - Directly relevant to DATA-Q1 (vector database) — understand options for semantic book search

---

## Appendix: Evidence Index

| # | File | Key Findings |
|---|------|-------------|
| 1 | `template.yml` | SAM/CloudFormation template: 3 Lambda functions (Node.js 22.x), DynamoDB table with SSE, API Gateway with Cognito auth, X-Ray tracing, CloudWatch alarms, deployment preferences |
| 2 | `pipeline/lib/pipeline-stack.ts` | CDK pipeline: 4-stage CI/CD (Source → Build → Staging → Production), ManualApprovalAction, 7 FullAccess managed policies on deploy role |
| 3 | `src/books/create/index.ts` | CreateBook Lambda: Direct DynamoDB putItem, X-Ray SDK instrumentation, basic try/catch, JSON response, no logging |
| 4 | `src/books/get-all/index.ts` | GetAllBooks Lambda: Direct DynamoDB scan, X-Ray SDK instrumentation, JSON response, no pagination, no logging |
| 5 | `src/books/create-pre-traffic/index.ts` | Pre-traffic hook: Smoke test (invoke → verify → cleanup), console.log logging, CodeDeploy lifecycle integration |
| 6 | `src/books/create/package.json` | Dependencies: aws-sdk v2.1692.0, aws-xray-sdk-core 3.10.3; Dev: mocha, chai, sinon, aws-sdk-mock, TypeScript 5.7.3 |
| 7 | `src/books/get-all/package.json` | Dependencies: aws-sdk v2.1692.0, aws-xray-sdk-core 3.10.3; Dev: mocha, chai, sinon, uuid, TypeScript 5.7.3 |
| 8 | `src/books/tests/index.js` | E2e tests: 4 tests covering public GET, authenticated POST, missing auth, CRUD flow with Cognito user creation |
| 9 | `src/books/tests/books-manager.js` | Test utility: DynamoDB save/remove/get operations — demonstrates repository pattern (test-only) |
| 10 | `src/books/tests/package.json` | E2e test dependencies: aws-sdk, axios, uuid, chai, mocha |
| 11 | `src/books/create/tests/index.spec.ts` | Unit tests: 3 tests — putItem success, invalid body, DynamoDB failure with aws-sdk-mock |
| 12 | `src/books/get-all/tests/index.spec.ts` | Unit tests: 3 tests — scan success, empty results, DynamoDB failure with aws-sdk-mock |
| 13 | `pipeline/buildspec.json` | Build stage: installs esbuild, runs unit tests for create and get-all, SAM build + package |
| 14 | `pipeline/buildspec-deploy.json` | Deploy stage: SAM deploy with stack name and stage parameter, exports CloudFormation outputs |
| 15 | `pipeline/buildspec-test.json` | Test stage: installs e2e test dependencies, runs mocha tests against deployed staging API |
| 16 | `pipeline/package.json` | CDK pipeline dependencies: aws-cdk-lib 2.189.1, constructs 10.4.2, TypeScript 5.7.3 |
| 17 | `pipeline/bin/pipeline.ts` | CDK app entry point: creates BooksApiPipeline stack |
| 18 | `README.md` | Comprehensive documentation: architecture, requirements, project structure, deployment, monitoring, CI/CD, token management |
| 19 | `.gitignore` | Excludes: node_modules, dist, .vscode, .aws-sam (does not exclude .env) |
| 20 | `events/create-book-request.json` | Sample API Gateway event for local testing with book payload |
