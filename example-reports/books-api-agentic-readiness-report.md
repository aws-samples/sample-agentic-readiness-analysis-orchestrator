# Agentic Readiness Assessment Report
**Target**: ./services/books-api
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

The Books API is a well-architected serverless CRUD application built on AWS Lambda, API Gateway, DynamoDB, and Cognito — with strong foundations in Infrastructure as Code and CI/CD automation. However, it is **not yet ready for agentic workloads**. Critical gaps exist across API documentation (no OpenAPI spec for agent tool discovery), observability (no structured logging or correlation IDs), data foundations (no vector store, RAG pipeline, or unified data access layer), and application resilience (no idempotency, circuit breakers, or async messaging). The strongest areas are compute (100% serverless) and CI/CD (full pipeline with progressive deployments). The most urgent modernization priorities center on making APIs machine-discoverable, adding observability for agent debugging, and establishing resilience patterns that agentic systems depend on.

### Overall Score: 2.0 / 4.0

| Category | Score | Status |
|----------|-------|--------|
| Infrastructure & Platform | 2.6 / 4.0 | 🟡 |
| Application Architecture | 1.7 / 4.0 | 🟠 |
| Data Foundations | 1.9 / 4.0 | 🟠 |
| Identity, Security & Governance | 1.9 / 4.0 | 🟠 |
| Operations & Observability | 1.7 / 4.0 | 🟠 |

## Top Priorities (Critical Gaps)

**1. No API Documentation (OpenAPI Spec) — APP-Q2: Score 1/4**
Agents discover and invoke tools via machine-readable API specifications. The Books API has no OpenAPI/Swagger spec — routes are defined inline in `template.yml` via SAM Events. Without an OpenAPI spec, an agent cannot programmatically understand available endpoints, request/response schemas, or authentication requirements. **First step:** Generate an OpenAPI 3.0 spec from the existing SAM template routes and add it as a `DefinitionBody` in the `BooksApi` resource.

**2. No Structured Logging or Correlation IDs — OPS-Q2: Score 1/4**
Agentic workflows span multiple components and require end-to-end traceability. The Lambda handlers in `create/index.ts` and `get-all/index.ts` have zero logging statements. The pre-traffic hook uses basic `console.log`. There are no JSON formatters, no correlation IDs, and no structured fields. When an agent-driven request fails, there is no way to reconstruct what happened. **First step:** Add AWS Lambda Powertools for TypeScript with structured JSON logging and inject `X-Amzn-Trace-Id` as a correlation ID in every log entry.

**3. No Vector Database or RAG Pipeline — DATA-Q1/Q2/Q3: Score 1/4**
Agentic systems rely on semantic search and retrieval-augmented generation (RAG) to ground LLM responses in domain-specific data. No vector database (OpenSearch, pgvector, Pinecone) or embedding pipeline exists. The book catalog data is only accessible via a DynamoDB scan — no semantic query capability. **First step:** Evaluate Amazon Bedrock Knowledge Bases with the existing DynamoDB book data as a data source, or add an OpenSearch Serverless collection with the k-NN plugin.

**4. No Idempotency or Resilience Patterns — APP-Q7/Q9: Score 1/4**
Agents retry failed operations automatically. Without idempotency keys on the CreateBook endpoint (`create/index.ts` does a raw `putItem` with no deduplication), retries can create duplicate records. No circuit breakers or retry-with-backoff patterns exist for external calls. **First step:** Implement idempotency using AWS Lambda Powertools idempotency middleware with the existing DynamoDB table as a persistence layer.

**5. No Async Messaging or Event-Driven Patterns — INF-Q4/APP-Q3: Score 1/4**
All communication is synchronous (API Gateway → Lambda → DynamoDB). Agentic workflows frequently involve long-running operations, fan-out scenarios, and event-driven triggers that require async messaging. There is no SQS, SNS, or EventBridge infrastructure. **First step:** Add an EventBridge event bus and publish domain events (e.g., `BookCreated`) from the CreateBook Lambda to enable event-driven extensions without modifying existing synchronous flows.

## Readiness Roadmap

### Microservices Decomposition Strategy

The Books API (APP-Q4 score: 3) is a **modular serverless monolith** — individual Lambda functions per endpoint with separate `package.json` files, but deployed as a single SAM stack sharing a DynamoDB table. This architecture is already well-suited for incremental decomposition.

**Recommended Approach: Conditional/Adaptive (Option C)**
- **LoE**: Low | **Risk**: Low | **Time to Value**: Fastest
- **Strategy**: The existing Lambda-per-function architecture already provides logical separation. Containerize or further modularize only as agent use cases demand. Focus on adding a shared data access layer and event-driven communication between functions.
- **Pattern**: [Hexagonal Architecture](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/hexagonal-architecture.html) + [Anti-corruption Layer](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/anti-corruption-layer.html)
- **Starting Point**: Extract a shared `books-repository` module used by all Lambda functions to eliminate duplicated DynamoDB access code. This is the natural first boundary to formalize.
- **When to Use**: Serverless monolith with independent functions but shared data access patterns; want fastest path to agent tooling.

**Alternative: Parallel Track (Option B)**
- **LoE**: Medium | **Risk**: Low-Medium | **Time to Value**: Fast
- **Strategy**: Add new agent-related capabilities (e.g., book search, recommendations) as separate SAM stacks or services while the existing Books API remains as-is.
- **Pattern**: [Strangler Fig](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) + [API Gateway Routing](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/api-routing.html)
- **Starting Point**: Deploy a new "Book Search" service backed by a vector database as a separate stack, routing via the existing API Gateway.
- **When to Use**: When adding entirely new agent capabilities alongside the existing CRUD API.

**Not Recommended: Big-Bang Decomposition (Option A)**
- **LoE**: Very High | **Risk**: High | **Time to Value**: Slow
- **Strategy**: Decompose the entire monolith before any modernization.
- **Only Consider If**: Complete rewrite is already planned, funded, and business-approved; existing system is being sunset.

**Pattern Recommendations Based on Your Architecture:**

- **Incremental Extraction**: Start with [Strangler Fig](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) + [API Gateway Routing Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/api-routing.html) (path-based routing) to add new agent-facing endpoints alongside existing ones without disruption.
  - **Why**: The existing API Gateway (`BooksApi`) already provides path-based routing to Lambda functions. New agent endpoints can be added to the same gateway or a new one without touching existing code.

- **Data Consistency**: Implement [Anti-corruption Layer](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/anti-corruption-layer.html) + [Transactional Outbox](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html) before extracting services.
  - **Why**: Without idempotency (APP-Q7 score: 1), service extraction risks data inconsistency. A shared data access layer with outbox pattern provides safety during transition.

- **Resilience First**: Implement [Circuit Breaker](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/circuit-breaker.html) + [Retry with Backoff](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/retry-backoff.html) before decomposition.
  - **Why**: Resilience patterns (APP-Q9 score: 1) must be in place before increasing system distribution. Agent workflows amplify failure modes.

### Phase 1 — Quick Wins (Days 1–30)

1. **Generate OpenAPI 3.0 spec** from existing SAM template routes (`template.yml`). Add `DefinitionBody` to `BooksApi` resource with full request/response schemas for `/books` GET and POST. This is the single most impactful change for agent discoverability.
2. **Add AWS Lambda Powertools for TypeScript** to all Lambda handlers (`create/index.ts`, `get-all/index.ts`, `create-pre-traffic/index.ts`). Enable structured JSON logging with correlation IDs and add request/response logging middleware.
3. **Configure API Gateway throttling** on `BooksApi` — add `ThrottlingBurstLimit` and `ThrottlingRateLimit` to `MethodSettings` in `template.yml`. Create a usage plan for API consumers.
4. **Add Lambda reserved concurrency limits** to `template.yml` for `GetAllBooks` and `CreateBook` to prevent runaway agent invocations from exhausting account-level Lambda concurrency.
5. **Extract shared data access module** — create a `books-repository` TypeScript module with DynamoDB operations (putItem, scan, getItem, deleteItem) to eliminate code duplication across Lambda functions and tests.

### Phase 2 — Foundation (Months 1–3)

1. **Implement idempotency** on CreateBook using AWS Lambda Powertools idempotency middleware with DynamoDB as the persistence store. Add `Idempotency-Key` header support.
2. **Add EventBridge integration** — publish `BookCreated` domain events from CreateBook Lambda to an EventBridge event bus. This establishes the event-driven foundation without breaking existing synchronous flows.
3. **Migrate from aws-sdk v2 to @aws-sdk v3** — all Lambda functions use `aws-sdk ^2.1692.0` which is in maintenance mode. Migrate to modular AWS SDK v3 for smaller bundle sizes and improved TypeScript support.
4. **Implement API versioning** — prefix API routes with `/v1/` (e.g., `/v1/books`) in the OpenAPI spec and SAM template to enable backward-compatible API evolution.
5. **Add SLOs and latency alarms** — define p99 latency and error rate SLOs for `/books` endpoints. Replace binary error alarms with anomaly detection alarms.
6. **Tighten CI/CD IAM** — replace broad managed policies (`IAMFullAccess`, `AWSCloudFormationFullAccess`) in `pipeline/lib/pipeline-stack.ts` with scoped custom policies.
7. **If Option C (Conditional)**: Formalize module boundaries — each Lambda function gets its own SAM template or nested stack. Add anti-corruption layers at data access boundaries.

### Phase 3 — Agent Enablement (Months 3–6)

1. **Deploy vector database** — add Amazon OpenSearch Serverless with k-NN plugin or Amazon Bedrock Knowledge Bases. Index book data for semantic search capability.
2. **Implement RAG pipeline** — create an embedding pipeline triggered by `BookCreated` EventBridge events to keep vector indices fresh as books are added.
3. **Build agent tools layer** — create Lambda-based tools (book search, book creation, book retrieval) with MCP or Strands Agents SDK, backed by the OpenAPI spec from Phase 1.
4. **Add human approval workflow** — implement Step Functions workflow with `waitForTaskToken` for high-risk operations (e.g., bulk book deletion) that agents might trigger.
5. **Implement distributed tracing for agent workflows** — add OpenTelemetry with `gen_ai.*` semantic conventions to trace agent reasoning chains, tool calls, and LLM interactions end-to-end.
6. **Continue service extraction** based on agent use case requirements — deploy recommendation engine, search service, or catalog management as independent services with their own data stores.

## Recommended Self-Paced Learning Materials

**Module 2: Move to Cloud Native (Containers and Serverless):**
- Cloud Design Patterns, Architectures, and Implementations — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html
  - Essential reference for microservices decomposition: Strangler Fig, Anti-corruption Layer, Saga patterns, Event Sourcing, Circuit Breaker, API routing, Hexagonal Architecture, and more. Directly applicable to the decomposition strategy recommended for this codebase.
- Architecting Serverless Applications — https://skillbuilder.aws/learn/MRWENY7FSX/architecting-serverless-applications/QVFY2JHVEH
  - Strengthen serverless architecture patterns for the existing Lambda-based API, especially around event-driven design and async messaging gaps identified in this assessment.
- Amazon API Gateway for Serverless Applications — https://skillbuilder.aws/learn/GQA6FHWPJD/amazon-api-gateway-for-serverless-applications/JVRZ3PSW4H
  - Addresses gaps in API Gateway configuration: throttling, usage plans, request validation, and OpenAPI integration — all critical gaps found in INF-Q7, APP-Q2, APP-Q8, and SEC-Q5.
- Amazon DynamoDB for Serverless Architecture — https://skillbuilder.aws/learn/SY1Y83VKTB/amazon-dynamodb-for-serverless-architectures/K9NM3PHH3S
  - Deepens DynamoDB patterns including single-table design, streams for event-driven architectures, and data access patterns relevant to DATA-Q5 and DATA-Q8 gaps.

**Module 4: Move to Managed Databases:**
- AWS PartnerCast: Vector Databases for Generative AI Applications — https://skillbuilder.aws/learn/UQ74USQJHU/aws-partnercast--vector-databases-for-generative-ai-applications--technical/7DKMBAPCST
  - Directly addresses DATA-Q1/Q2/Q3 gaps: understanding vector databases, embeddings, and RAG pipelines needed for agentic readiness.

**Module 6: Move to Modern DevOps:**
- AWS Modernization Pathways: Move to Modern DevOps — https://skillbuilder.aws/learning-plan/1FGEQKGPQD/aws-modernization-pathways-move-to-modern-devops-includes-labs/MNQZ2KPVCK
  - Covers CI/CD best practices, testing strategies, and deployment automation. While CI/CD is strong (score 4), observability and SLO gaps (OPS-Q2, OPS-Q4, OPS-Q8) require DevOps maturity improvements.
- Getting Started with DevOps on AWS — https://skillbuilder.aws/learn/R4B13K95YQ/getting-started-with-devops-on-aws/38NHHYRV1R
  - Foundational DevOps concepts including observability, monitoring, and incident response — addressing OPS-Q2, OPS-Q4, OPS-Q7, OPS-Q8, and OPS-Q11 gaps.
- Advanced Testing Practices Using AWS DevOps Tools — https://skillbuilder.aws/learn/1YC7UXUWBR/advanced-testing-practices-using-aws-devops-tools/A32U6G7NEQ
  - Expand on the existing E2E test foundation (OPS-Q10 score: 3) with contract testing, performance testing, and chaos engineering practices needed for agent resilience.
- Monitor Python Applications Using Amazon CloudWatch Application Signals — https://skillbuilder.aws/learn/JMPDZD64MV/monitor-python-applications-using-amazon-cloudwatch-application-signals/2JP3J2MPCK
  - Learn Application Signals for SLO monitoring and service-level observability — directly addresses OPS-Q4 and OPS-Q12 gaps.

**Module 7: Move to AI:**
- AWS Modernization Pathways: Move to AI — https://skillbuilder.aws/learning-plan/VDFEE4ACCV/aws-modernization-pathways-move-to-ai-pathways-includes-labs/P3DAWPTN63
  - Comprehensive learning path covering generative AI foundations, Bedrock, and agent development — addresses the entire AI/agent readiness gap (APP-Q13, DATA-Q1–Q3, OPS-Q3, OPS-Q6).
- Amazon Bedrock Getting Started — https://skillbuilder.aws/learn/63KTRM86DQ/amazon-bedrock-getting-started/SC2Y3HMAUE
  - Foundation for integrating LLM capabilities into the Books API, including Bedrock Knowledge Bases for RAG and agent tool use.
- Build and Evaluate Retrieval Augmented Generation (RAG) Applications using Knowledge Bases for Amazon Bedrock (Lab) — https://skillbuilder.aws/learn/JRGWCFYT67/lab--build-and-evaluate-retrieval-augmented-generation-rag-applications-using-knowledge-bases-for-amazon-bedrock/A4MN58JB7A
  - Hands-on lab directly addressing DATA-Q1/Q2/Q3 gaps — building and evaluating RAG pipelines using Bedrock Knowledge Bases.
- Introduction to Agentic AI on AWS — https://skillbuilder.aws/learn/DNBD5MT8ZD/introduction-to-agentic-ai-on-aws/WAKAFK6UFY
  - Overview of agentic AI patterns on AWS, including tool use, orchestration, and safety — directly relevant to the Phase 3 agent enablement roadmap.
- Creating an AWS DevOps AI Agent with the Strands Agents SDK (Lab) — https://skillbuilder.aws/learn/AH1GD8AJY3/lab--creating-an-aws-devops-ai-agent-with-the-strands-agents-sdk/A9SKJNMPJ2
  - Practical lab for building agents using Strands SDK — the recommended framework for TypeScript-based agent development on this codebase.
- AWS PartnerCast: Deep Dive: Building Observable AI Agents with Strands, Amazon Bedrock Agent Core & SageMaker MLflow — https://skillbuilder.aws/learn/1EN76TZBB6/aws-partnercast--deep-dive-building-observable-ai-agents-with-strands-amazon-bedrock-agent-core--sagemaker-mlflow--technical/CX2K6XAT84
  - Addresses OPS-Q1, OPS-Q3, and OPS-Q6 gaps — observability, evaluation, and cost tracking for agent workloads.

## Detailed Findings

### Infrastructure & Platform

#### INF-Q1: Compute
- **Score**: 4/4 ✅
- **Finding**: 100% serverless compute. `template.yml` defines three `AWS::Serverless::Function` resources: `GetAllBooks`, `CreateBook`, and `CreateBookPreTraffic`. All use `Runtime: nodejs22.x` with `MemorySize: 512` and `Timeout: 5`. No EC2 instances, ECS tasks, or EKS clusters found anywhere in IaC or source code. esbuild is used for TypeScript compilation (defined in each function's `Metadata.BuildProperties`).
- **Gap**: None. Compute is fully serverless and agent-ready.
- **Recommendation**: Maintain serverless-first approach. When adding agent workloads, consider Lambda response streaming for long-running agent interactions.

#### INF-Q2: Databases
- **Score**: 4/4 ✅
- **Finding**: Single DynamoDB table (`BooksTable`) defined as `AWS::Serverless::SimpleTable` in `template.yml` with `PrimaryKey: isbn (String)` and `SSESpecification: SSEEnabled: true`. DynamoDB is fully managed with automatic failover, backups, and scaling. No self-managed database software detected in any compute environment, Dockerfile, or configuration file.
- **Gap**: None. Database is fully managed.
- **Recommendation**: Consider enabling DynamoDB Streams to support event-driven patterns needed for agent workflows (e.g., triggering embedding updates when books are created).

#### INF-Q3: Workflow Orchestration
- **Score**: 1/4 ❌
- **Finding**: No Step Functions, Temporal, Camunda, or any workflow orchestration service found in `template.yml` or `pipeline/lib/pipeline-stack.ts`. The `CreateBookPreTraffic` Lambda is invoked by CodeDeploy as a deployment hook — not a general-purpose workflow orchestrator. No `aws_sfn_*` resources, no Temporal SDK imports, no workflow YAML definitions.
- **Gap**: No workflow orchestration exists. Agentic systems require multi-step orchestration for tool chains, approval flows, and complex reasoning sequences.
- **Recommendation**: Add AWS Step Functions for multi-step agent workflows. Start with a simple workflow that chains book creation with validation and notification steps.

#### INF-Q4: Async Messaging
- **Score**: 1/4 ❌
- **Finding**: No SQS queues, SNS topics, EventBridge event buses, or MSK clusters found in `template.yml` or CDK stack. All communication follows a synchronous path: API Gateway → Lambda → DynamoDB. No event-driven handlers, no message publishing patterns in source code (`create/index.ts`, `get-all/index.ts`).
- **Gap**: No async messaging infrastructure. Agentic workflows need event-driven patterns for decoupled tool execution, fan-out operations, and reliable message delivery.
- **Recommendation**: Add Amazon EventBridge as the event bus. Publish domain events (`BookCreated`, `BookRetrieved`) from Lambda functions. This enables downstream consumers (embedding pipelines, notification systems, agent event handlers) without coupling.

#### INF-Q5: Infrastructure as Code
- **Score**: 4/4 ✅
- **Finding**: `template.yml` (SAM/CloudFormation) defines all application infrastructure: 3 Lambda functions, DynamoDB table, API Gateway, Cognito User Pool, IAM roles, CloudWatch alarms, and CodeDeploy deployment preferences. `pipeline/lib/pipeline-stack.ts` (CDK) defines the complete CI/CD pipeline: CodePipeline with 4 stages, 3 CodeBuild projects, 2 S3 buckets, and SSM parameter reference. Approximately 100% of infrastructure is defined in code.
- **Gap**: None. IaC coverage is comprehensive.
- **Recommendation**: As new infrastructure is added (EventBridge, Step Functions, vector databases), maintain the IaC-first approach. Consider consolidating SAM and CDK into a single CDK application for consistency.

#### INF-Q6: CI/CD
- **Score**: 4/4 ✅
- **Finding**: Full CI/CD pipeline defined in `pipeline/lib/pipeline-stack.ts` with 4 stages: Source (CodeStar connection to GitHub), Build (`pipeline/buildspec.json` — installs dependencies, runs unit tests, SAM build, SAM package), Staging (`pipeline/buildspec-deploy.json` for deploy + `pipeline/buildspec-test.json` for E2E tests), Production (`ManualApprovalAction` + deploy). Unit tests run in build stage; E2E tests run post-staging-deploy.
- **Gap**: None for current CI/CD maturity. Consider adding automated security scanning (SAST/DAST) and dependency vulnerability checks.
- **Recommendation**: Add `npm audit` or Snyk to the build stage. Add contract testing for API consumers in the test stage.

#### INF-Q7: API Entry Point
- **Score**: 3/4 🟡
- **Finding**: `AWS::Serverless::Api` (`BooksApi`) in `template.yml` provides API Gateway as the entry point. Configured with `CognitoAuth` authorizer, `MethodSettings` with `LoggingLevel: INFO` for all methods, `TracingEnabled: true`, and stage variables for Lambda alias routing. However, `MethodSettings` lacks `ThrottlingBurstLimit` and `ThrottlingRateLimit`. No `AWS::ApiGateway::UsagePlan` or WAF integration.
- **Gap**: No throttling or rate limiting on API Gateway. Agents can generate high request volumes; unthrottled APIs risk DynamoDB capacity exhaustion and account-level Lambda concurrency limits.
- **Recommendation**: Add `ThrottlingBurstLimit: 100` and `ThrottlingRateLimit: 50` to `MethodSettings` in `template.yml`. Create a usage plan with API keys for programmatic (agent) consumers.

#### INF-Q8: Real-time Streaming
- **Score**: 1/4 ❌
- **Finding**: No Kinesis Data Streams, Kinesis Data Firehose, MSK (Managed Streaming for Apache Kafka), or any streaming resources found in `template.yml` or CDK stack. No Kafka or Kinesis SDK imports in any `package.json`.
- **Gap**: No real-time streaming capability. Agentic systems benefit from streaming for real-time data ingestion, change data capture, and event replay.
- **Recommendation**: If real-time book catalog updates become critical for agent freshness, consider DynamoDB Streams (built-in) as a lightweight CDC mechanism rather than introducing a separate streaming service.

#### INF-Q9: Network Security
- **Score**: 1/4 ❌
- **Finding**: No VPC (`AWS::EC2::VPC`), subnets, security groups, or NACLs defined in `template.yml` or CDK stack. Lambda functions have no `VpcConfig` property — they run in the AWS-managed VPC. This is a common and acceptable pattern for simple serverless applications accessing only AWS-managed services (DynamoDB, CloudWatch).
- **Gap**: No network segmentation. While Lambda-to-DynamoDB communication doesn't require VPC, future agent workloads may need VPC access for private resources (OpenSearch, RDS, private APIs).
- **Recommendation**: Defer VPC configuration until a private resource (e.g., OpenSearch Serverless with VPC endpoint) is introduced. When needed, create a VPC with private subnets, NAT Gateway, and VPC endpoints for DynamoDB and other AWS services.

#### INF-Q10: Auto-scaling
- **Score**: 3/4 🟡
- **Finding**: Lambda functions auto-scale inherently (up to account-level concurrency). DynamoDB `SimpleTable` uses on-demand capacity by default (auto-scales reads/writes). `AutoPublishAlias` with `DeploymentPreference` (`Linear10PercentEvery1Minute` for production) manages gradual traffic shifting during deployments. However, no explicit `ReservedConcurrentExecutions` is configured on any Lambda function.
- **Gap**: No explicit Lambda concurrency limits. An agent generating burst traffic could exhaust the account's Lambda concurrency pool, impacting other workloads.
- **Recommendation**: Add `ReservedConcurrentExecutions` to `GetAllBooks` and `CreateBook` in `template.yml`. Set appropriate limits based on expected traffic patterns (e.g., 100 concurrent executions per function).

### Application Architecture

#### APP-Q1: Programming Languages
- **Score**: 3/4 🟡
- **Finding**: TypeScript is the primary language for all Lambda handlers (`src/books/create/index.ts`, `src/books/get-all/index.ts`, `src/books/create-pre-traffic/index.ts`) and CDK infrastructure (`pipeline/lib/pipeline-stack.ts`). JavaScript is used for E2E tests (`src/books/tests/index.js`, `src/books/tests/books-manager.js`). Runtime is Node.js v22.x. TypeScript has a strong and growing agent framework ecosystem (LangChain.js, Strands Agents SDK, Vercel AI SDK).
- **Gap**: TypeScript is well-supported but Python currently has the richest agent framework ecosystem (langchain, crewai, strands-agents Python SDK, boto3 Bedrock).
- **Recommendation**: TypeScript is a solid choice — no language change needed. Leverage Strands Agents SDK for TypeScript or LangChain.js for agent development. The existing TypeScript expertise is a strength.

#### APP-Q2: API Documentation
- **Score**: 1/4 ❌
- **Finding**: No OpenAPI/Swagger spec files found in the repository. The SAM template `Globals.Api` sets `OpenApiVersion: 3.0.1` (to avoid default stage creation) but does not define a `DefinitionBody` with an actual OpenAPI specification. API routes are defined inline via `Events` properties on Lambda functions: `GET /books` (GetAllBooks) and `POST /books` (CreateBook). No `@OpenAPIDefinition` annotations, no swagger.json, no api-docs directory.
- **Gap**: Critical for agentic readiness. Agents discover and invoke tools via machine-readable API specifications. Without an OpenAPI spec, agents cannot programmatically understand endpoints, parameters, request/response schemas, or authentication requirements.
- **Recommendation**: Create an OpenAPI 3.0 spec documenting both endpoints with full request/response schemas (Book object: isbn, title, year, author, publisher, rating, pages). Add it as `DefinitionBody` in the `BooksApi` resource in `template.yml`. Include authentication requirements (Cognito authorizer for POST).

#### APP-Q3: Async vs Sync Communication
- **Score**: 1/4 ❌
- **Finding**: 100% synchronous communication. The only flow is API Gateway → Lambda → DynamoDB (request/response). `create/index.ts` calls `client.putItem()` synchronously. `get-all/index.ts` calls `client.scan()` synchronously. No message publishing (SQS `sendMessage`, SNS `publish`, EventBridge `putEvents`), no event-driven handlers, no async invocation patterns found in any source file.
- **Gap**: No async capability. Agentic workflows often involve operations that exceed API timeout limits and need fire-and-forget or callback patterns.
- **Recommendation**: Start by adding EventBridge `putEvents` calls after successful book creation in `create/index.ts`. This doesn't change the synchronous API response but enables downstream async consumers.

#### APP-Q4: Monolith vs Microservices
- **Score**: 3/4 🟡
- **Finding**: The application follows a serverless modular pattern: separate Lambda functions per API endpoint (CreateBook, GetAllBooks), each with its own `package.json` and code directory. `DeploymentPreference` enables independent deployment rollback per function. However, all functions share a single DynamoDB table (`BooksTable`) and are deployed as a single SAM stack (`template.yml`). The CDK pipeline treats the entire application as one deployable unit. Functions cannot be independently scaled or deployed to different accounts/regions without stack changes.
- **Gap**: Functions are logically independent but operationally coupled via shared stack and table. For agentic workloads, each agent tool ideally maps to an independently deployable service with clear API contracts.
- **Recommendation**: For the current scale, the modular serverless pattern is adequate. As agent tools are added, consider splitting into nested stacks or separate SAM applications per domain. Extract the shared DynamoDB access into a common library first.

#### APP-Q5: API Response Format
- **Score**: 4/4 ✅
- **Finding**: All API responses use structured JSON. `create/index.ts` returns `headers: { 'Content-Type': 'application/json' }` with `body: ''` (201 Created). `get-all/index.ts` returns `headers: { 'Content-Type': 'application/json' }` with `body: JSON.stringify(bookDtos)` where `bookDtos` is an array of typed book objects with isbn, title, year, author, publisher, rating, pages.
- **Gap**: None. JSON is the standard format for agent tool responses.
- **Recommendation**: Maintain JSON responses. When adding agent-facing endpoints, consider adding pagination metadata (total count, next token) to GET responses — the current DynamoDB scan returns all items without pagination.

#### APP-Q6: Workflow Logic
- **Score**: 1/4 ❌
- **Finding**: No workflow orchestration. Business logic in `create/index.ts` is a single step: parse body → putItem to DynamoDB. Business logic in `get-all/index.ts` is a single step: scan DynamoDB → return results. No Step Functions, no saga patterns, no workflow engine, no state machine patterns. The pre-traffic hook (`create-pre-traffic/index.ts`) follows a simple sequential pattern (invoke Lambda → getItem → assert → deleteItem) but this is deployment validation, not business workflow.
- **Gap**: No workflow orchestration. Agentic systems need multi-step orchestration for tool chaining (e.g., search → retrieve → summarize → recommend).
- **Recommendation**: Add Step Functions when agent workflows require multi-step operations. Start with a book recommendation workflow: search books → filter by criteria → generate summary using LLM → return results.

#### APP-Q7: Idempotency
- **Score**: 1/4 ❌
- **Finding**: No idempotency patterns. `create/index.ts` performs `client.putItem(params)` without any deduplication check, idempotency key header parsing, or conditional write (no `ConditionExpression`). DynamoDB `putItem` is inherently a blind overwrite — if the same ISBN is submitted twice, the second write silently overwrites the first. No `Idempotency-Key` header handling in any Lambda function. No deduplication IDs in any messaging patterns (no messaging exists).
- **Gap**: Critical for agentic readiness. Agents automatically retry failed requests. Without idempotency, retries create duplicate or silently overwritten records with no way to detect the issue.
- **Recommendation**: Implement idempotency using AWS Lambda Powertools for TypeScript `@idempotent` decorator. Use a dedicated DynamoDB table for idempotency records. Add `ConditionExpression: 'attribute_not_exists(isbn)'` to `putItem` in `create/index.ts` to prevent silent overwrites.

#### APP-Q8: Rate Limiting & Throttling
- **Score**: 1/4 ❌
- **Finding**: No rate limiting at any layer. API Gateway `MethodSettings` in `template.yml` configures `LoggingLevel: INFO` but does not include `ThrottlingBurstLimit` or `ThrottlingRateLimit`. No `AWS::ApiGateway::UsagePlan` resource. No WAF (`AWS::WAFv2::WebACL`) association. No rate-limiting middleware in Lambda code (no express-rate-limit, no custom throttling logic).
- **Gap**: No protection against burst traffic from agents or malicious actors. Agents can generate high request rates during tool exploration or retry loops.
- **Recommendation**: Add throttling to `MethodSettings` in `template.yml`. Create a usage plan with API keys for agent consumers. Consider adding WAF with rate-based rules for additional protection.

#### APP-Q9: Resilience Patterns
- **Score**: 1/4 ❌
- **Finding**: No resilience patterns. No circuit breakers, no retry logic with backoff, no timeout configurations beyond the Lambda function timeout (5 seconds, set in `Globals.Function.Timeout`). No resilience libraries (resilience4j, cockatiel, p-retry) in any `package.json`. `aws-xray-sdk-core` provides tracing instrumentation but not resilience. Error handling in `create/index.ts` and `get-all/index.ts` is a bare `catch (e)` that returns a 500 status with no error details, no retry guidance, no circuit breaking.
- **Gap**: No resilience against downstream failures. When agents call these APIs and DynamoDB experiences latency, there is no graceful degradation, retry guidance, or circuit breaking.
- **Recommendation**: Add AWS Lambda Powertools for TypeScript with retry and timeout utilities. Implement the `Retry-After` header in 500 responses. For future external service calls, add circuit breaker patterns using libraries like `cockatiel` or `opossum`.

#### APP-Q10: Long-running Processes
- **Score**: 2/4 🟠
- **Finding**: All Lambda functions have a 5-second timeout (`Globals.Function.Timeout: 5`). Current operations are simple DynamoDB reads/writes that complete well within this limit. However, no async processing framework exists — no background job queues, no polling endpoints, no Step Functions for long operations. The `get-all/index.ts` performs a full DynamoDB `scan` which will become slow as the table grows, with no pagination implemented.
- **Gap**: No framework for handling operations that might exceed the 5-second timeout as the application grows or when agent operations (e.g., batch imports, complex queries, LLM calls) are added.
- **Recommendation**: Implement pagination for the scan operation in `get-all/index.ts` (use `ExclusiveStartKey`/`LastEvaluatedKey`). For future long-running operations, use Step Functions or SQS with Lambda workers and a status-polling API pattern.

#### APP-Q11: API Versioning
- **Score**: 1/4 ❌
- **Finding**: No API versioning strategy. Routes are defined as `/books` (GET and POST) in `template.yml` without any version prefix. No `/v1/`, `/v2/` URL patterns. No `Accept-Version` headers. No versioning annotations or changelog files. The API Gateway stage name (`staging` or `production`) is used for environment routing, not API versioning.
- **Gap**: No backward compatibility guarantee. When agent tool contracts change, existing agents will break without a versioning strategy.
- **Recommendation**: Add `/v1/` prefix to all routes (e.g., `/v1/books`). Document the versioning strategy in the OpenAPI spec. Use API Gateway stage variables or path-based routing for version management.

#### APP-Q12: Service Discovery & Mesh
- **Score**: 2/4 🟠
- **Finding**: Lambda functions reference DynamoDB via the `TABLE` environment variable set from CloudFormation (`!Ref BooksTable`). API Gateway provides the service entry point. No AWS Service Discovery, App Mesh, or Istio. No hard-coded service endpoints to other services (this is a single-service application). The CDK pipeline uses CloudFormation outputs to pass API endpoint, UserPoolId, and other values between stages.
- **Gap**: No service discovery mechanism. As additional services are added for agent capabilities, hard-coded environment variables will not scale.
- **Recommendation**: Acceptable for current single-service architecture. When adding services, use AWS Cloud Map (Service Discovery) or API Gateway as a service registry. Store service endpoints in SSM Parameter Store rather than hard-coding them.

#### APP-Q13: AI/Agent Frameworks
- **Score**: 1/4 ❌
- **Finding**: No AI or agent framework dependencies in any `package.json`. Searched for: `@aws-sdk/client-bedrock-runtime`, `@aws-sdk/client-bedrock-agent`, `langchain`, `@langchain/core`, `openai`, `@anthropic-ai/sdk`, `strands-agents`, `@modelcontextprotocol/sdk`, `ai` (Vercel AI SDK). None found. No LLM, embedding, or agent-related imports in any source file.
- **Gap**: No AI/agent capability exists. The application is a traditional CRUD API with no AI integration points.
- **Recommendation**: Start with Amazon Bedrock integration. Add `@aws-sdk/client-bedrock-runtime` for LLM access. Evaluate Strands Agents SDK for TypeScript agent development. The existing Lambda + API Gateway architecture provides natural tool endpoints for agent frameworks.

### Data Foundations

#### DATA-Q1: Vector Database Presence
- **Score**: 1/4 ❌
- **Finding**: No vector database found. Searched `template.yml` and CDK stack for: `AWS::OpenSearchService::Domain`, `AWS::OpenSearchServerless::Collection`, Aurora with pgvector extension, Bedrock Knowledge Bases, S3 Vectors. Searched `package.json` files for: `@opensearch-project/opensearch`, `@pinecone-database/pinecone`, `weaviate-ts-client`, `chromadb`. None found.
- **Gap**: No semantic search or vector similarity capability. Agents need vector databases to perform RAG, semantic tool discovery, and knowledge retrieval.
- **Recommendation**: Add Amazon OpenSearch Serverless with the k-NN plugin, or use Amazon Bedrock Knowledge Bases with S3 as a data source. For the book catalog, Bedrock Knowledge Bases provides the simplest path — export book data to S3 and configure automatic sync.

#### DATA-Q2: Vector DB Management
- **Score**: 1/4 ❌
- **Finding**: No vector database exists (see DATA-Q1). No managed or self-hosted vector DB infrastructure.
- **Gap**: No vector DB to manage. This gap is a prerequisite blocker — DATA-Q1 must be addressed first.
- **Recommendation**: When adding a vector database, use a fully managed service (OpenSearch Serverless, Bedrock Knowledge Bases) to avoid operational overhead.

#### DATA-Q3: RAG Implementation
- **Score**: 1/4 ❌
- **Finding**: No RAG pipeline components found. No embedding model calls (Bedrock Titan Embeddings, OpenAI ada). No document chunking or splitting code. No `similarity_search`, `knn_search`, or semantic query patterns. No Bedrock Knowledge Base integration. The only data retrieval is a full DynamoDB `scan` in `get-all/index.ts`.
- **Gap**: No RAG capability. Agents cannot ground their responses in the book catalog data through semantic retrieval.
- **Recommendation**: Build a RAG pipeline: (1) Use Bedrock Titan Embeddings to embed book metadata (title, author, publisher). (2) Store embeddings in OpenSearch Serverless or Bedrock Knowledge Bases. (3) Create a semantic search Lambda function as an agent tool. (4) Use DynamoDB Streams + EventBridge to trigger re-embedding when books are created.

#### DATA-Q4: Data Source Sprawl
- **Score**: 4/4 ✅
- **Finding**: Single data source — DynamoDB table `BooksTable` (defined in `template.yml`). All Lambda functions (`create/index.ts`, `get-all/index.ts`, `create-pre-traffic/index.ts`) and test utilities (`tests/books-manager.js`) connect to this same table via the `TABLE` environment variable. No additional databases, external APIs, or data stores.
- **Gap**: None. Single data source simplifies agent data access.
- **Recommendation**: Maintain simplicity. As vector databases and external services are added, create a unified data access layer or API aggregation pattern to prevent sprawl.

#### DATA-Q5: Data Access Pattern
- **Score**: 2/4 🟠
- **Finding**: DynamoDB is accessed directly via `aws-sdk` `DynamoDB` client (v2) in Lambda handlers. `create/index.ts` uses `client.putItem()` directly. `get-all/index.ts` uses `client.scan()` directly. No repository pattern, no data access layer abstraction, no ORM/ODM. Business logic is interleaved with data access in handler functions.
- **Gap**: Direct database access from handler code. Agent tools should call well-defined data APIs, not interact with databases directly. The tight coupling makes it difficult to swap data stores or add caching.
- **Recommendation**: Extract a `BooksRepository` TypeScript class with methods like `createBook()`, `getAllBooks()`, `getBookByIsbn()`. Lambda handlers should call this repository, not DynamoDB directly. This abstraction enables future data source changes (e.g., adding a cache layer, switching to API calls) without modifying agent tool code.

#### DATA-Q6: Unstructured Data
- **Score**: 1/4 ❌
- **Finding**: No S3 buckets for document storage in `template.yml` (S3 buckets in CDK pipeline are for CI/CD artifacts only). No Textract, Tika, or document parsing libraries. No PDF/image processing. The application stores only structured book metadata (isbn, title, year, author, publisher, rating, pages) in DynamoDB.
- **Gap**: No unstructured data handling. Agent use cases like "analyze book covers" or "extract information from book PDFs" are not supported.
- **Recommendation**: Add an S3 bucket for book-related documents (covers, PDFs, reviews). Integrate Amazon Textract for document parsing if unstructured data becomes part of the agent's knowledge base.

#### DATA-Q7: Schema Documentation
- **Score**: 1/4 ❌
- **Finding**: No formal schema documentation. The book schema is implicitly defined in: (1) `create/index.ts` handler code where fields are destructured: `{ isbn, title, year, author, publisher, rating, pages }`. (2) `template.yml` DynamoDB table definition (`PrimaryKey: isbn, String`). (3) TypeScript `Book` interface in test files (`create/tests/index.spec.ts`, `get-all/tests/index.spec.ts`) — but these are test-only interfaces, not shared schema definitions. No JSON Schema, no Avro/Protobuf, no migration files, no schema registry.
- **Gap**: No versioned, documented schema. Agents need schema definitions to construct valid API requests and interpret responses correctly.
- **Recommendation**: Create a shared `book-schema.ts` TypeScript file with exported interfaces and Zod validation schemas. Generate JSON Schema from these types for the OpenAPI spec. Version the schema alongside the API.

#### DATA-Q8: Data Access Layer
- **Score**: 1/4 ❌
- **Finding**: No unified data access layer. DynamoDB operations are duplicated across 4 files, each creating its own `DynamoDB` client: `create/index.ts` (putItem), `get-all/index.ts` (scan), `create-pre-traffic/index.ts` (getItem, deleteItem), `tests/books-manager.js` (batchWriteItem, getItem). The X-Ray wrapping logic (`AWSXRay.captureAWS(AWSCore)`) is also duplicated in `create/index.ts` and `get-all/index.ts`. DynamoDB attribute marshaling (e.g., `isbn: { S: isbn }`) is manually repeated in every file.
- **Gap**: Code duplication and no single point of data access. Changes to data access patterns (adding caching, tracing, validation) must be replicated across all files. Agent tools will inherit this fragmentation.
- **Recommendation**: Create a `src/books/shared/books-repository.ts` module that encapsulates all DynamoDB operations, X-Ray instrumentation, and attribute marshaling. All Lambda handlers and tests should import from this single module.

#### DATA-Q9: Embedding Freshness
- **Score**: 1/4 ❌
- **Finding**: No embeddings exist (see DATA-Q1/Q3). No event-driven embedding refresh triggers, no scheduled re-indexing pipelines, no CDC (Change Data Capture) patterns. DynamoDB Streams are not enabled on `BooksTable`.
- **Gap**: No mechanism to keep vector indices fresh. If embeddings are added, they will become stale as books are created or updated.
- **Recommendation**: When implementing RAG (DATA-Q3), enable DynamoDB Streams on `BooksTable` and create a Lambda function triggered by stream events to re-embed modified records. Alternatively, use Bedrock Knowledge Bases with automatic S3 sync.

#### DATA-Q10: Database Engine Version & EOL
- **Score**: 4/4 ✅
- **Finding**: DynamoDB is a fully managed serverless NoSQL service. There is no engine version to pin — AWS manages the engine lifecycle, patches, and upgrades automatically. No EOL risk. The `AWS::Serverless::SimpleTable` definition in `template.yml` does not require (or support) an engine version parameter.
- **Gap**: None. DynamoDB has no EOL concerns.
- **Recommendation**: No action needed. DynamoDB's serverless nature eliminates version management entirely.

#### DATA-Q11: Stored Procedures & Schema Complexity
- **Score**: 4/4 ✅
- **Finding**: No SQL files, stored procedures, triggers, or proprietary SQL constructs found in the repository. DynamoDB is a NoSQL service that does not support stored procedures or triggers at the database layer. All business logic resides in the application layer (Lambda handlers). No `.sql` files found. No `CREATE PROCEDURE`, `CREATE TRIGGER`, or `CREATE FUNCTION` patterns detected.
- **Gap**: None. All business logic is in the application layer, making it portable and agent-accessible.
- **Recommendation**: Maintain this pattern. Keep business logic in Lambda functions (application layer) rather than pushing it into database constructs.

### Identity, Security & Governance

#### SEC-Q1: Secret Management
- **Score**: 2/4 🟠
- **Finding**: No AWS Secrets Manager resources (`AWS::SecretsManager::Secret`) in `template.yml` or CDK stack. No `secretsmanager` SDK imports in any Lambda handler. Environment variables are used only for non-sensitive configuration: `TABLE` (DynamoDB table name) and `FN_NEW_VERSION` (Lambda function ARN). No hardcoded passwords, API keys, or secrets detected in source code. `.gitignore` excludes `node_modules` and `.aws-sam` but no `.env` files were found committed.
- **Gap**: No secrets management infrastructure. While current non-sensitive config doesn't require it, agent workloads will need LLM API keys, tool credentials, and per-user secrets that must be stored securely.
- **Recommendation**: Add AWS Secrets Manager for future agent credentials (Bedrock API keys if using external models, third-party API keys for agent tools). Reference secrets from Lambda environment variables using dynamic references in CloudFormation.

#### SEC-Q2: IAM Least Privilege
- **Score**: 2/4 🟠
- **Finding**: **Application IAM (Good)**: SAM template uses scoped policies — `DynamoDBReadPolicy` for GetAllBooks, `DynamoDBWritePolicy` for CreateBook, `DynamoDBCrudPolicy` for CreateBookPreTraffic — all scoped to `!Ref BooksTable`. Pre-traffic hook has specific `codedeploy:PutLifecycleEventHookExecutionStatus` and `lambda:InvokeFunction` permissions scoped to specific ARNs. **Pipeline IAM (Overly Broad)**: `pipeline/lib/pipeline-stack.ts` attaches 7 broad managed policies to the deploy CodeBuild role: `AWSCloudFormationFullAccess`, `AmazonDynamoDBFullAccess`, `AWSLambda_FullAccess`, `AmazonAPIGatewayAdministrator`, `IAMFullAccess`, `AWSCodeDeployFullAccess`, `AmazonCognitoPowerUser`. `IAMFullAccess` alone grants full IAM control.
- **Gap**: CI/CD pipeline roles have overly permissive IAM policies. A compromised pipeline could create admin users or escalate privileges via `IAMFullAccess`. For agentic workloads, every IAM role (including agent execution roles) must follow least privilege.
- **Recommendation**: Replace broad managed policies with scoped custom policies in `pipeline/lib/pipeline-stack.ts`. Create an IAM policy that allows only the specific CloudFormation, Lambda, DynamoDB, API Gateway, CodeDeploy, and Cognito actions needed for deployment. Remove `IAMFullAccess` entirely and scope IAM permissions to only `iam:PassRole` for specific roles.

#### SEC-Q3: Identity Propagation
- **Score**: 2/4 🟠
- **Finding**: Cognito User Pool (`CognitoUserPool` in `template.yml`) with OAuth2 implicit grant flow. `CognitoAuth` authorizer on CreateBook endpoint with `AuthorizationScopes: [email]`. JWT tokens from Cognito authorize API access. However, Lambda handler code (`create/index.ts`) does not extract or use user identity from the event context — `event.requestContext.authorizer.claims` is not accessed. The handler does not log who created a book.
- **Gap**: User identity is validated at the gateway but not propagated into the application. Agent actions cannot be attributed to specific users. No audit trail of which user (or agent acting on behalf of a user) created which book.
- **Recommendation**: Extract user identity from `event.requestContext.authorizer.claims` in `create/index.ts`. Store the creator's identity (email/sub) as a book attribute. Propagate identity context through all service calls for agent-level audit trails.

#### SEC-Q4: Audit Logging
- **Score**: 2/4 🟠
- **Finding**: API Gateway has `LoggingLevel: INFO` with a dedicated logging role (`ApiGatewayLoggingRole` with `AmazonAPIGatewayPushToCloudWatchLogs`). Lambda functions have `Tracing: Active` (X-Ray). API Gateway has `TracingEnabled: true`. However, no `AWS::CloudTrail::Trail` resource in any IaC file. No CloudTrail log file validation. No S3 bucket with object lock for immutable log storage. No CloudWatch log retention policies defined.
- **Gap**: No CloudTrail for API-level audit logging. Agent actions (creating books, accessing data) are not captured in an immutable audit trail. CloudWatch logs exist but without retention policies, they use the default (never expire) which incurs cost.
- **Recommendation**: Add a CloudTrail trail in `template.yml` with log file validation enabled. Store logs in an S3 bucket with object lock. Set CloudWatch log retention policies (e.g., 90 days) on all Lambda log groups.

#### SEC-Q5: API Rate Limits
- **Score**: 1/4 ❌
- **Finding**: No rate limits configured. API Gateway `MethodSettings` in `template.yml` does not include `ThrottlingBurstLimit` or `ThrottlingRateLimit`. No `AWS::ApiGateway::UsagePlan` resource. No WAF (`AWS::WAFv2::WebACL`). No per-client quotas. API Gateway's default account-level limits apply (10,000 requests/second) but these are not customized.
- **Gap**: No protection against API abuse. Agents operating in loops or multiple agents hitting the API simultaneously can overwhelm backend resources.
- **Recommendation**: Add `ThrottlingBurstLimit` and `ThrottlingRateLimit` to `MethodSettings`. Create a `AWS::ApiGateway::UsagePlan` with per-client API keys and quotas. Add WAF with rate-based rules for IP-level protection.

#### SEC-Q6: PII Redaction
- **Score**: 1/4 ❌
- **Finding**: No PII redaction mechanisms. No log scrubbing middleware, no PII masking libraries, no CloudWatch log filters for PII detection, no Amazon Macie. Error handling returns empty body (`body: ''`) in both `create/index.ts` and `get-all/index.ts` — this prevents PII from leaking in error responses (a good practice), but there is no proactive PII detection or redaction in request logging or successful responses.
- **Gap**: No PII protection framework. Agent interactions may contain or generate PII (user emails from Cognito, book content) that must be redacted from logs and traces.
- **Recommendation**: Add AWS Lambda Powertools log redaction utilities. Configure PII masking patterns for email addresses, ISBNs (if sensitive), and user identifiers in structured logs. Consider enabling Amazon Macie on S3 buckets if document storage is added.

#### SEC-Q7: Human Approval Workflows
- **Score**: 2/4 🟠
- **Finding**: CDK pipeline has `ManualApprovalAction` (in `pipeline/lib/pipeline-stack.ts`) gating production deployments with the message: "Ensure Books API works correctly in Staging and release date is agreed with Product Owners". This is a code deployment gate, not a runtime data operation gate. No Step Functions with `waitForTaskToken` or human approval Lambda patterns for high-risk data operations (e.g., bulk deletion, data modification).
- **Gap**: No human-in-the-loop workflow for runtime operations. Agents performing high-risk actions (deleting books, modifying large datasets) have no approval mechanism.
- **Recommendation**: Implement Step Functions workflows with `waitForTaskToken` for high-risk agent actions. Create an approval API that agents call before executing destructive operations. Integrate with SNS/email for approval notifications.

#### SEC-Q8: Encryption at Rest
- **Score**: 2/4 🟠
- **Finding**: DynamoDB table has `SSESpecification: SSEEnabled: true` in `template.yml` (AWS-managed encryption with AWS-owned keys). S3 buckets in CDK pipeline use `BucketEncryption.S3_MANAGED` (SSE-S3). No `AWS::KMS::Key` resources defined. No customer-managed KMS keys (CMKs) used on any data store. No `kms_key_id` properties on any resource.
- **Gap**: Using AWS-managed encryption (default) rather than customer-managed KMS keys. While data is encrypted, customers cannot control key rotation, cross-account access policies, or key deletion — important for agentic workloads handling sensitive data.
- **Recommendation**: Create a customer-managed KMS key and apply it to the DynamoDB table (`SSESpecification.KMSMasterKeyId`) and S3 buckets. This enables key rotation policies, CloudTrail key usage logging, and granular access controls.

#### SEC-Q9: API Authentication
- **Score**: 2/4 🟠
- **Finding**: CreateBook (POST /books) has Cognito authorizer (`CognitoAuth`) with `AuthorizationScopes: [email]` and conditional `aws.cognito.signin.user.admin` scope for non-production. GetAllBooks (GET /books) is intentionally public — no authentication required (per README: "Getting all books is a public operation that everyone can call"). Not all endpoints are authenticated.
- **Gap**: Public read endpoint is a design choice but creates risk for agentic workloads — unauthenticated agents can scrape the entire book catalog without rate limits or identity tracking.
- **Recommendation**: Consider adding optional authentication (API key or Cognito) for the GET endpoint to enable per-consumer tracking and rate limiting for agent consumers, while keeping the endpoint functionally public. Add API keys via a usage plan for programmatic consumers.

#### SEC-Q10: Centralized Identity
- **Score**: 3/4 🟡
- **Finding**: Amazon Cognito User Pool (`CognitoUserPool`) is provisioned in `template.yml` with `UserPoolClient` (OAuth2 implicit grant, OpenID + email scopes) and `UserPoolDomain` (`book-api-{stage}-{accountId}`). This provides a centralized identity provider for the Books API with user registration, authentication, and JWT token issuance.
- **Gap**: Cognito is scoped to this single API. No SSO configuration, no SAML/OIDC federation, no cross-application identity sharing. For agentic workloads, agents need a consistent identity across multiple services and tools.
- **Recommendation**: Evaluate AWS IAM Identity Center (SSO) for cross-application identity. Configure Cognito as a federated identity provider if integrating with an existing enterprise IdP. Add machine-to-machine credentials (client_credentials grant) for agent service accounts.

### Operations & Observability

#### OPS-Q1: Distributed Tracing
- **Score**: 3/4 🟡
- **Finding**: AWS X-Ray is enabled across the stack. `template.yml` sets `Tracing: Active` in `Globals.Function` (all Lambda functions) and `TracingEnabled: true` on `BooksApi` (API Gateway). Source code in `create/index.ts` and `get-all/index.ts` uses `aws-xray-sdk-core` to wrap the AWS SDK: `AWSXRay.captureAWS(AWSCore)`, which automatically instruments DynamoDB calls with trace context propagation. `X-Amzn-Trace-Id` is propagated through API Gateway → Lambda → DynamoDB via X-Ray SDK.
- **Gap**: No OpenTelemetry integration. No `gen_ai.*` semantic conventions for LLM tracing. No service mesh for cross-service trace propagation. X-Ray provides good baseline tracing but lacks the extensibility needed for agentic workload observability (tool call traces, LLM reasoning chains).
- **Recommendation**: Migrate from X-Ray SDK to AWS Distro for OpenTelemetry (ADOT) for Lambda. This preserves X-Ray integration while enabling OpenTelemetry instrumentation, custom span attributes, and future `gen_ai.*` semantic conventions for agent observability.

#### OPS-Q2: Structured Logging
- **Score**: 1/4 ❌
- **Finding**: No structured logging. `create/index.ts` and `get-all/index.ts` have zero log statements. `create-pre-traffic/index.ts` uses basic `console.log` (e.g., `console.log('Entering PreTraffic Hook!')`, `console.log('DynamoDB item', JSON.stringify(Item, null, 2))`). No JSON log formatter (no `winston`, `pino`, `structlog`, or AWS Lambda Powertools Logger). No correlation ID middleware. No `traceId` or `correlationId` fields in log output. No CloudWatch Log Insights queries defined.
- **Gap**: Critical for agentic observability. When an agent-driven request fails, there is no way to correlate logs across Lambda invocations, trace tool call outcomes, or debug agent reasoning chains. Console.log produces unstructured plaintext that is difficult to query.
- **Recommendation**: Add AWS Lambda Powertools for TypeScript Logger to all Lambda functions. Configure JSON output format with automatic injection of `X-Amzn-Trace-Id`, function name, cold start indicator, and custom correlation IDs. Add request/response logging middleware.

#### OPS-Q3: Automated Evals
- **Score**: 1/4 ❌
- **Finding**: No AI evaluation framework. No eval datasets, no scoring scripts, no LLM-as-judge patterns, no RAGAS evaluation, no golden dataset files. No A/B testing infrastructure for prompts. The testing infrastructure (mocha unit tests and E2E tests) covers application functionality but not AI/agent quality.
- **Gap**: No evaluation capability. Before deploying agents, an eval pipeline is essential to measure agent accuracy, hallucination rates, and tool selection quality.
- **Recommendation**: When building agents (Phase 3), implement an eval pipeline: create golden datasets of expected book queries and responses, use LLM-as-judge scoring, and integrate evals into the CI/CD pipeline. Leverage the existing mocha test infrastructure to run eval suites.

#### OPS-Q4: SLOs
- **Score**: 1/4 ❌
- **Finding**: CloudWatch alarms exist in `template.yml`: `CreateBookAliasErrorMetricGreaterThanZeroAlarm` and `GetAllBooksAliasErrorMetricGreaterThanZeroAlarm`. Both monitor `Errors > 0` on Lambda functions with `EvaluationPeriods: 2`, `Period: 60`. However, these are deployment rollback triggers (referenced in `DeploymentPreference.Alarms`), not SLO definitions. No p99/p95 latency alarms, no error rate SLOs (e.g., 99.9% success), no error budget tracking, no SLO dashboards.
- **Gap**: No SLOs defined. Binary error alarms trigger deployment rollback but don't measure ongoing service quality. Agentic workloads require SLOs for agent task success rate, latency, and tool reliability.
- **Recommendation**: Define SLOs: (1) API latency p99 < 500ms for GET /books. (2) API error rate < 0.1% for POST /books. (3) Availability > 99.9%. Create CloudWatch alarms and dashboards tracking these SLOs. Use CloudWatch Application Signals when available.

#### OPS-Q5: Rollback Capability
- **Score**: 3/4 🟡
- **Finding**: Strong code deployment rollback. `template.yml` configures `DeploymentPreference` on Lambda functions: `Linear10PercentEvery1Minute` for production (gradual traffic shifting), `AllAtOnce` for staging. CloudWatch error alarms automatically trigger CodeDeploy rollback during deployment. `CreateBookPreTraffic` Lambda performs a smoke test (creates test book → verifies in DynamoDB → cleans up) before allowing traffic to shift to new version.
- **Gap**: No configuration rollback, no prompt versioning, no feature flag system. Only code deployments can be rolled back. For agentic workloads, prompt changes and model configuration changes also need rollback capability.
- **Recommendation**: Implement feature flags (AWS AppConfig) for gradual feature rollout including agent capabilities. Add prompt versioning in a configuration store (SSM Parameter Store or DynamoDB) with rollback capability. Extend the deployment strategy to cover configuration changes.

#### OPS-Q6: LLM Cost Tracking
- **Score**: 1/4 ❌
- **Finding**: No LLM usage in the application. No token counting, no cost attribution, no usage tracking metrics, no CloudWatch custom metrics for LLM consumption. No tiered retention policies for observability data.
- **Gap**: No LLM cost infrastructure. When agents are added, token usage must be tracked per request, per user, and per workflow to manage costs and optimize prompt engineering.
- **Recommendation**: When integrating Bedrock, implement token counting from LLM response metadata (`inputTokens`, `outputTokens`). Publish custom CloudWatch metrics with dimensions for user, feature, and workflow. Set up CloudWatch dashboards for cost monitoring. Define retention policies for observability data.

#### OPS-Q7: Business Metrics
- **Score**: 1/4 ❌
- **Finding**: No custom business metrics. No `cloudwatch.put_metric_data` calls in any Lambda handler. No business KPI tracking (books created per day, API usage patterns, popular authors, search frequency). Only AWS-managed infrastructure metrics exist (Lambda duration, invocations, errors; API Gateway request count, latency).
- **Gap**: No business outcome visibility. Agentic systems need business metrics to measure agent effectiveness — e.g., book recommendation acceptance rate, catalog coverage, user satisfaction.
- **Recommendation**: Add CloudWatch custom metrics in Lambda handlers: `BooksCreated` count, `BooksRetrieved` count, API response time by endpoint. Create a CloudWatch dashboard combining infrastructure and business metrics. When agents are added, track agent-specific KPIs.

#### OPS-Q8: Anomaly Detection
- **Score**: 1/4 ❌
- **Finding**: CloudWatch alarms use static binary thresholds: `Errors > 0` (`ComparisonOperator: GreaterThanThreshold`, `Threshold: 0`). No anomaly detection (`AnomalyDetectionModel`). No p99/p95 latency alarms. No PagerDuty/OpsGenie integration. No composite alarms. The existing alarms are deployment-specific rollback triggers, not operational monitoring.
- **Gap**: No behavioral baseline monitoring. Agents exhibit non-deterministic behavior — an agent suddenly calling tools excessively or generating abnormal response patterns won't be detected by static threshold alarms.
- **Recommendation**: Add CloudWatch anomaly detection alarms on Lambda invocation count, duration p99, and error rate. Create composite alarms combining multiple metrics. Integrate with SNS for alerting. When agents are added, create anomaly detection for tool call frequency and LLM token consumption.

#### OPS-Q9: Deployment Strategy
- **Score**: 3/4 🟡
- **Finding**: Progressive deployment strategy using CodeDeploy via SAM `DeploymentPreference`. Production: `Linear10PercentEvery1Minute` (shifts 10% traffic every minute — 10-minute full rollout). Staging: `AllAtOnce` (immediate full deployment). Pre-traffic hook (`CreateBookPreTraffic`) validates new version before any traffic shift. CloudWatch alarms trigger automatic rollback on errors. Pipeline has manual approval gate for production in CDK (`ManualApprovalAction`).
- **Gap**: Linear deployment is good but not canary (which tests with a small fixed percentage before proceeding). No feature flag system for gradual capability rollout independent of deployments.
- **Recommendation**: Consider upgrading to `Canary10Percent5Minutes` for production Lambda deployments (tests with 10% for 5 minutes before shifting all traffic). Add AWS AppConfig for feature flags to decouple feature rollout from deployment.

#### OPS-Q10: Integration Testing
- **Score**: 3/4 🟡
- **Finding**: **Unit tests**: `src/books/create/tests/index.spec.ts` (3 tests: successful putItem, invalid body, DynamoDB failure) and `src/books/get-all/tests/index.spec.ts` (3 tests: successful scan, empty results, DynamoDB failure). Use mocha, chai, sinon, aws-sdk-mock. Run in build stage via `pipeline/buildspec.json`. **E2E tests**: `src/books/tests/index.js` (4 tests: unauthenticated GET, authenticated POST, book retrieval with verification, error handling). Use mocha, axios, aws-sdk for Cognito auth. Run post-staging-deploy via `pipeline/buildspec-test.json`. Tests create real Cognito users, create books via API, verify in DynamoDB, and clean up.
- **Gap**: Good coverage for current functionality. Missing: contract tests for API consumers, load/performance tests, chaos engineering tests. No test coverage for concurrent access or DynamoDB throttling scenarios.
- **Recommendation**: Add API contract tests using Pact or similar. Add load tests for DynamoDB scan performance as data grows. When agents are added, create integration tests for agent tool invocations with golden datasets.

#### OPS-Q11: Incident Response Automation
- **Score**: 1/4 ❌
- **Finding**: No runbooks (markdown, YAML, or JSON). No SSM Automation documents. No Lambda-based remediation functions. No Step Functions for incident workflows. No self-healing patterns beyond CodeDeploy rollback during deployments. No links to runbooks in alarm configurations. The CloudWatch alarms only trigger deployment rollback, not operational remediation.
- **Gap**: No incident response automation. When an agent causes a production issue (e.g., overwhelming DynamoDB, creating invalid data), there is no automated response or documented remediation procedure.
- **Recommendation**: Create runbooks in markdown for common failure scenarios (DynamoDB throttling, Lambda timeouts, Cognito auth failures). Add SSM Automation documents for automated remediation (e.g., scale DynamoDB provisioned capacity). Link runbooks to CloudWatch alarm actions.

#### OPS-Q12: Observability Governance & Ownership
- **Score**: 1/4 ❌
- **Finding**: No CODEOWNERS file. No SLO ownership files or dashboards with named owners. Resource tags exist (`project: my-project`, `environment: Stage`) on Lambda functions and DynamoDB table in `template.yml`, which provides basic resource organization. No platform team tooling configuration. No per-service dashboards defined in IaC. No observability-as-code patterns.
- **Gap**: No observability ownership model. No one is explicitly responsible for monitoring service health, investigating failures, or maintaining SLOs. For agentic workloads, clear ownership of agent quality, reliability, and safety is essential.
- **Recommendation**: Add a CODEOWNERS file assigning observability ownership. Define SLOs with named owners. Create CloudWatch dashboards in IaC (`template.yml`) with per-endpoint metrics. Establish a shared responsibility model between platform and product teams for agent observability.

## Appendix: Evidence Index

| # | File | Key Evidence |
|---|------|-------------|
| 1 | `template.yml` | SAM/CloudFormation template — defines all application infrastructure: 3 Lambda functions (nodejs22.x), DynamoDB SimpleTable (SSE enabled), API Gateway with Cognito auth, CloudWatch error alarms, CodeDeploy linear deployment, API Gateway logging role |
| 2 | `pipeline/lib/pipeline-stack.ts` | CDK pipeline — 4-stage CodePipeline (Source → Build → Staging → Production), ManualApprovalAction for production, overly broad IAM managed policies (IAMFullAccess, etc.), S3 buckets with S3-managed encryption |
| 3 | `src/books/create/index.ts` | CreateBook Lambda — TypeScript, aws-sdk v2, X-Ray instrumentation, direct DynamoDB putItem, no logging, no idempotency, no error details, JSON response |
| 4 | `src/books/get-all/index.ts` | GetAllBooks Lambda — TypeScript, aws-sdk v2, X-Ray instrumentation, direct DynamoDB scan (no pagination), no logging, JSON response with Content-Type header |
| 5 | `src/books/create-pre-traffic/index.ts` | Pre-traffic hook — smoke test Lambda for CodeDeploy, uses console.log, creates/verifies/deletes test book in DynamoDB, reports deployment status |
| 6 | `src/books/create/package.json` | Dependencies: aws-sdk ^2.1692.0, aws-xray-sdk-core ^3.10.3. No AI/agent, resilience, or logging frameworks |
| 7 | `src/books/get-all/package.json` | Dependencies: aws-sdk ^2.1692.0, aws-xray-sdk-core ^3.10.3. Identical to create function dependencies |
| 8 | `src/books/create-pre-traffic/package.json` | Dependencies: aws-sdk ^2.1692.0 only. No X-Ray (pre-traffic hook) |
| 9 | `src/books/tests/index.js` | E2E test suite — mocha, axios, Cognito auth flow, 4 tests covering GET/POST endpoints with real API calls |
| 10 | `src/books/tests/books-manager.js` | Test utility — direct DynamoDB operations (batchWriteItem, getItem), duplicated data access patterns |
| 11 | `src/books/tests/package.json` | Test dependencies: aws-sdk, axios, uuid, mocha, chai |
| 12 | `src/books/create/tests/index.spec.ts` | Unit tests — 3 tests with aws-sdk-mock, Book TypeScript interface (test-only) |
| 13 | `src/books/get-all/tests/index.spec.ts` | Unit tests — 3 tests with aws-sdk-mock, Book TypeScript interface (test-only) |
| 14 | `pipeline/buildspec.json` | Build stage — installs SAM CLI, runs unit tests, SAM build + package, exports artifact path |
| 15 | `pipeline/buildspec-deploy.json` | Deploy stage — SAM deploy with stack name and environment parameter, exports CloudFormation outputs |
| 16 | `pipeline/buildspec-test.json` | Test stage — npm ci + mocha E2E tests in staging environment |
| 17 | `pipeline/package.json` | CDK dependencies: aws-cdk-lib ^2.189.1, constructs ^10.4.2 |
| 18 | `README.md` | Architecture documentation — confirms serverless pattern, public GET endpoint by design, Cognito auth for POST, local DynamoDB testing with Docker |
| 19 | `events/env.json` | Local test config — TABLE environment variable set to "books" for SAM local |
| 20 | `.gitignore` | Excludes node_modules, dist, .vscode, .aws-sam — no sensitive files committed |
