# Agentic Readiness Assessment Report
**Target**: ./services/books-api
**Date**: 2026-03-06
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment

---

## Table of Contents

1. Executive Summary
2. Top Priorities (Critical Gaps)
3. Readiness Roadmap
   - Phase 1 — Quick Wins (Days 1–30)
   - Phase 2 — Foundation (Months 1–3)
   - Phase 3 — Agent Enablement (Months 3–6)
4. Recommended Modernization Pathways
5. Recommended Self-Paced Learning Materials
6. Detailed Findings
   - Infrastructure & Platform
   - Application Architecture
   - Data Foundations
   - Identity, Security & Governance
   - Operations & Observability
7. Appendix: Evidence Index

---

## Executive Summary

The books-api is a well-architected serverless REST API built on AWS Lambda, API Gateway, DynamoDB, and Cognito — providing a strong foundation for agentic readiness in compute, IaC, and CI/CD. However, the application lacks critical capabilities required for agentic workloads: no async messaging or event-driven patterns, no API documentation (OpenAPI specs), no AI/agent framework integration, no vector database or RAG pipeline, and minimal observability beyond X-Ray tracing. The strongest areas are serverless compute (100% Lambda), fully managed database (DynamoDB), and mature CI/CD with progressive deployments. The most critical gaps center on the complete absence of AI/agent infrastructure, structured logging, rate limiting, and async communication patterns that agents require for reliable, observable, and safe operation.

### Overall Score: 2.2 / 4.0

| Category | Score | Status |
|----------|-------|--------|
| Infrastructure & Platform | 2.7 / 4.0 | 🟡 |
| Application Architecture | 2.1 / 4.0 | 🟠 |
| Data Foundations | 2.0 / 4.0 | 🟠 |
| Identity, Security & Governance | 2.1 / 4.0 | 🟠 |
| Operations & Observability | 1.9 / 4.0 | 🟠 |

---

## Top Priorities (Critical Gaps)

**1. No AI/Agent Framework Integration (APP-Q13: 1/4, DATA-Q1: 1/4, DATA-Q3: 1/4)**
The application has zero AI or agent framework integration — no Amazon Bedrock, LangChain, Strands, or any AI SDK. No vector database exists for semantic search, and no RAG pipeline is implemented. This is the foundational blocker for agentic readiness. **First step**: Add `@aws-sdk/client-bedrock-runtime` to `src/books/create/package.json` and prototype a book recommendation agent using Amazon Bedrock with the existing DynamoDB book catalog as a tool.

**2. No API Documentation / OpenAPI Specification (APP-Q2: 1/4)**
No OpenAPI or Swagger spec exists. The SAM template sets `OpenApiVersion: 3.0.1` in `template.yml` only to suppress default stage creation — no actual API definition is present. Agents rely on API specs to understand available tools, parameters, and response formats. Without documentation, an agent cannot discover or reliably invoke the books API. **First step**: Generate an OpenAPI 3.0 spec for the `/books` GET and POST endpoints directly in `template.yml` using SAM's inline API definition, including request/response schemas for the book model.

**3. No Async Messaging or Event-Driven Patterns (INF-Q4: 1/4, APP-Q3: 1/4)**
All communication is synchronous REST (API Gateway → Lambda → DynamoDB). No SQS, SNS, EventBridge, or any async messaging exists in `template.yml`. Agentic workflows need event-driven patterns for reliable multi-step operations, fan-out, and decoupled processing. **First step**: Add an EventBridge rule in `template.yml` that emits a `BookCreated` event after successful DynamoDB putItem, enabling downstream consumers (notifications, indexing, agent triggers).

**4. No Structured Logging or Observability Foundation (OPS-Q2: 1/4, OPS-Q7: 1/4, OPS-Q12: 1/4)**
Lambda functions have no structured logging — `create-pre-traffic/index.ts` uses basic `console.log` and the main handlers have no logging at all. No JSON formatters, no correlation IDs, no business metrics. Agent workflows generate complex execution traces that are impossible to debug without structured, correlated logs. **First step**: Add a lightweight structured logging library (e.g., `@aws-lambda-powertools/logger`) to all Lambda functions with JSON output and correlation ID propagation.

**5. No API Rate Limiting or Throttling (APP-Q8: 1/4, SEC-Q5: 1/4)**
No API Gateway usage plans, throttling configuration, or WAF rate rules exist in `template.yml`. No application-level rate limiting. Agents can generate high-frequency API calls, and without rate limiting, a misbehaving agent could overwhelm the API, exhaust DynamoDB capacity, or cause cascading failures. **First step**: Add an API Gateway usage plan with throttle settings (burst and rate limits) in `template.yml` and configure per-method throttling on the `BooksApi` resource.

---

## Readiness Roadmap

> Cross-dependencies: Phase 2 items (API documentation, async patterns, data access layer) are prerequisites for Phase 3 agent enablement. Phase 1 observability improvements should be completed before adding agent workloads to ensure visibility into agent behavior from day one.

### Microservices Decomposition Strategy

The books-api is a simple serverless application with two Lambda functions (GetAllBooks, CreateBook) behind a single API Gateway. With an APP-Q4 score of 3 (clear function boundaries but single-service scope), it does not require traditional monolith decomposition. Instead, the focus should be on expanding service boundaries to support agentic workloads.

**Recommended Approach: Parallel Track (Option B)**
- **LoE**: Low-Medium | **Risk**: Low | **Time to Value**: Fast
- **Strategy**: Keep existing serverless architecture, add new capabilities as separate Lambda functions/services using event-driven patterns
- **Pattern**: [Strangler Fig](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) + [API Gateway Routing](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/api-routing.html)
- **Starting Point**: Add a new `books-search` Lambda function for semantic search and a `books-recommend` agent Lambda, deployed alongside existing functions via the same SAM template or a new service
- **When to Use**: Best approach for this application — the serverless architecture already provides function-level isolation and independent deployability

**Alternative: Conditional/Adaptive (Option C)**
- **LoE**: Low | **Risk**: Low | **Time to Value**: Fastest
- **Strategy**: Extend existing service with new endpoints and event handlers; split into separate services only when complexity warrants it
- **Pattern**: [Hexagonal Architecture](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/hexagonal-architecture.html) + [Anti-corruption Layer](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/anti-corruption-layer.html)
- **Starting Point**: Add a shared data access layer, then add new Lambda functions for agent capabilities within the same SAM template
- **When to Use**: If the scope of agentic features remains small and tightly coupled to the book domain

**Not Recommended: Big-Bang Decomposition (Option A)**
- **LoE**: Very High | **Risk**: High | **Time to Value**: Slow
- **Strategy**: Decompose entire application before any modernization
- **Only Consider If**: Not applicable — the application is already serverless with function-level boundaries

**Pattern Recommendations Based on Your Architecture:**

- **Event-Driven Extension**: Use [Event Sourcing](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/event-sourcing.html) to emit DynamoDB stream events for book creation/updates, enabling downstream agent consumers
- **Why**: The existing synchronous API Gateway → Lambda → DynamoDB pattern can be extended with DynamoDB Streams or EventBridge to add async event-driven capabilities without modifying existing function code

- **Resilience First**: Implement [Circuit Breaker](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/circuit-breaker.html) + [Retry with Backoff](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/retry-backoff.html) before adding agent-to-API integrations
- **Why**: Agent workflows will call the books API programmatically; resilience patterns must be in place before increasing call frequency and adding external dependencies (Bedrock, vector DB)

### Phase 1 — Quick Wins (Days 1–30)

1. **Add structured logging with AWS Lambda Powertools** — Install `@aws-lambda-powertools/logger` in all Lambda functions. Replace `console.log` with structured JSON logging. Add correlation IDs via X-Ray trace ID propagation. Estimated effort: 1–2 days.

2. **Generate OpenAPI specification** — Define the OpenAPI 3.0 spec for `/books` GET and POST endpoints in `template.yml` using SAM's `DefinitionBody`. Include request/response schemas for the book model (isbn, title, year, author, publisher, rating, pages). Estimated effort: 1–2 days.

3. **Add API Gateway throttling and usage plans** — Configure throttle settings (burst: 100, rate: 50 rps) on the `BooksApi` resource in `template.yml`. Create a usage plan with API key requirement for write operations. Estimated effort: 1 day.

4. **Scope down pipeline IAM policies** — Replace `FullAccess` managed policies in `pipeline/lib/pipeline-stack.ts` deploy role with least-privilege inline policies specifying only required actions and resource ARNs. Estimated effort: 2–3 days.

5. **Add authentication to GetAllBooks endpoint** — Extend the CognitoAuth authorizer to the GET `/books` endpoint in `template.yml` to ensure all API endpoints are authenticated before agent integration. Estimated effort: 0.5 days.

### Phase 2 — Foundation (Months 1–3)

1. **Implement event-driven patterns with EventBridge** — Add EventBridge integration to emit `BookCreated` and `BookRetrieved` events from Lambda functions. Add DynamoDB Streams for change data capture. This creates the async messaging foundation for agent workflows.

2. **Build a shared data access layer** — Extract DynamoDB client setup and data mapping from individual Lambda handlers into a shared library (`src/books/lib/`). Implement the repository pattern with typed interfaces for book CRUD operations. Migrate `aws-sdk` v2 to `@aws-sdk/client-dynamodb` v3.

3. **Add API versioning** — Implement URL path versioning (`/v1/books`) in `template.yml` API definition. Create a migration plan for existing consumers. Document backward compatibility guarantees.

4. **Implement idempotency patterns** — Add idempotency-key header handling to the CreateBook Lambda using `@aws-lambda-powertools/idempotency` with DynamoDB as the persistence layer.

5. **Define SLOs and business metrics** — Create CloudWatch dashboards with p99 latency, error rates, and book creation/retrieval counts. Define SLOs: 99.9% availability, <200ms p99 latency for GetAllBooks, <500ms for CreateBook. Add CloudWatch anomaly detection on error rates.

6. **Add PII awareness** — While the current book model contains no PII, add log scrubbing patterns as a foundation for future agent interactions that may involve user data.

### Phase 3 — Agent Enablement (Months 3–6)

1. **Integrate Amazon Bedrock** — Add `@aws-sdk/client-bedrock-runtime` dependency. Create a new `books-recommend` Lambda function that uses Bedrock to generate book recommendations based on the DynamoDB catalog. Expose via a new `/books/recommend` API Gateway endpoint.

2. **Add vector database for semantic search** — Provision an Amazon OpenSearch Serverless collection with vector search capability or use Amazon Bedrock Knowledge Bases. Index book metadata (title, author, publisher) as vector embeddings for semantic search.

3. **Implement RAG pipeline** — Build a document processing pipeline: DynamoDB Streams → Lambda → Bedrock Titan Embeddings → OpenSearch vector index. Enable semantic search queries like "find books about cloud architecture."

4. **Build agent evaluation framework** — Create golden datasets for book recommendation quality. Implement automated eval pipelines with scoring metrics (relevance, accuracy, hallucination detection). Run evals in CI pipeline.

5. **Add LLM cost tracking and observability** — Track Bedrock token usage per request with CloudWatch custom metrics. Add cost attribution by endpoint and user. Implement tiered retention for agent telemetry data.

---

## Recommended Modernization Pathways

Based on the assessment findings, the following AWS Modernization Pathways are recommended for this application. Multiple pathways can execute in parallel because modern applications comprise multiple interconnected components — each requiring its own modernization approach.

### Pathway Summary

| Pathway | Triggered | Priority | Key Trigger Criteria | Est. Effort |
|---------|-----------|----------|---------------------|-------------|
| Move to Cloud Native | Yes | Medium | APP-Q4=3 (<4), APP-Q3=1 (<3), APP-Q10=3 (borderline) | Medium |
| Move to Containers | No | N/A | INF-Q1=4 (already serverless) | N/A |
| Move to Open Source | No | N/A | DATA-Q11=4, no proprietary SQL | N/A |
| Move to Managed Databases | No | N/A | INF-Q2=4, DATA-Q10=4 (managed DynamoDB) | N/A |
| Move to Managed Analytics | Yes | Low | INF-Q8=1 (<3, no streaming) | Low |
| Move to Modern DevOps | No | N/A | INF-Q5=4, INF-Q6=4, OPS-Q9=3, OPS-Q10=3, OPS-Q1=3 (all ≥3) | N/A |
| Move to AI | Yes | High | APP-Q13=1, DATA-Q1=1, DATA-Q3=1, OPS-Q3=1, OPS-Q6=1 (all <3) | High |

### Parallel Execution Plan

**Parallel Track 1**: Move to Cloud Native + Move to AI — These pathways can execute concurrently. Adding EventBridge/SQS async patterns (Cloud Native) can proceed alongside Bedrock integration and vector DB setup (AI). Event-driven patterns actually accelerate AI integration by providing the async infrastructure agents need.

**Parallel Track 2**: Move to Managed Analytics — This is low priority and can be deferred until Phase 3 or executed opportunistically alongside Track 1 if streaming needs arise during AI integration.

**Sequential Dependencies**: Move to Cloud Native (async patterns) should ideally reach basic maturity before Move to AI reaches Phase 3 (agent enablement), as agents benefit from event-driven communication patterns.

### Move to Cloud Native

- **Priority**: Medium
- **Trigger Criteria Met**:
  - APP-Q4: Score 3/4 — Single-service serverless API with clear function boundaries but not a full microservices architecture
  - APP-Q3: Score 1/4 — 100% synchronous communication (API Gateway → Lambda → DynamoDB), no async patterns
  - APP-Q10: Score 3/4 — Current operations are fast but no async infrastructure for future long-running agent operations
- **Current State**: Well-architected serverless application using Lambda, API Gateway, and DynamoDB. All compute is serverless (score 4 on INF-Q1). However, the architecture is purely synchronous request-response with no event-driven patterns.
- **Target State**: Event-driven serverless architecture with EventBridge for domain events (BookCreated, BookUpdated), SQS for reliable async processing, and Step Functions for multi-step agent workflows. New agent capabilities deployed as independent Lambda functions.
- **Key Activities**:
  1. Add EventBridge integration for domain events (BookCreated, BookRetrieved)
  2. Implement DynamoDB Streams for change data capture
  3. Add Step Functions for multi-step agent workflows (book recommendation, semantic search)
  4. Create new Lambda functions for agent capabilities alongside existing CRUD functions
- **Dependencies**: None — can start immediately
- **Estimated Effort**: Medium
- **Roadmap Phase Alignment**: Phase 2 (EventBridge, DynamoDB Streams) and Phase 3 (Step Functions for agents)
- **Relevant Learning Materials**: Module 2 — Move to Cloud Native (Containers and Serverless)

### Move to Managed Analytics

- **Priority**: Low
- **Trigger Criteria Met**:
  - INF-Q8: Score 1/4 — No managed streaming services (Kinesis, MSK) detected
- **Current State**: No real-time streaming or analytics infrastructure. Data flows are purely request-response. DynamoDB is the only data store.
- **Target State**: Event streaming pipeline for book catalog changes, enabling real-time analytics and feeding the embedding refresh pipeline for agent RAG.
- **Key Activities**:
  1. Evaluate whether EventBridge (from Cloud Native pathway) satisfies streaming needs
  2. If higher-throughput streaming is needed, add Kinesis Data Streams for book catalog change events
  3. Consider Athena for ad-hoc analytics on book catalog data stored in S3
- **Dependencies**: Move to Cloud Native pathway (EventBridge) may satisfy basic streaming needs
- **Estimated Effort**: Low
- **Roadmap Phase Alignment**: Phase 2–3 (evaluate after EventBridge is in place)
- **Relevant Learning Materials**: Module 5 — Move to Managed Analytics

### Move to AI

- **Priority**: High
- **Trigger Criteria Met**:
  - APP-Q13: Score 1/4 — No AI/agent frameworks in any package.json or source code
  - DATA-Q1: Score 1/4 — No vector database for semantic search
  - DATA-Q3: Score 1/4 — No RAG pipeline, embedding model calls, or semantic search
  - OPS-Q3: Score 1/4 — No agent evaluation framework or golden datasets
  - OPS-Q6: Score 1/4 — No LLM cost tracking or token usage monitoring
- **Current State**: Zero AI or agent capabilities. The application is a traditional CRUD API with no AI integration points. No vector database, no embeddings, no agent frameworks.
- **Target State**: Amazon Bedrock-powered book recommendation agent with semantic search via vector database. RAG pipeline for book catalog. Automated eval framework with golden datasets. LLM cost tracking with per-request attribution.
- **Key Activities**:
  1. Add Amazon Bedrock integration for book recommendations and natural language queries
  2. Provision vector database (OpenSearch Serverless or Bedrock Knowledge Bases) for semantic book search
  3. Build RAG pipeline: DynamoDB Streams → Lambda → Bedrock Titan Embeddings → vector index
  4. Create agent evaluation framework with book recommendation golden datasets
  5. Implement LLM cost tracking with CloudWatch custom metrics for token usage
  6. Add agent-specific observability (gen_ai semantic conventions in traces)
- **Dependencies**: Benefits from Move to Cloud Native (async patterns for embedding refresh pipeline)
- **Estimated Effort**: High
- **Roadmap Phase Alignment**: Phase 3 (Agent Enablement) primarily, Phase 2 for data foundations (vector DB)
- **Relevant Learning Materials**: Module 7 — Move to AI

---

## Recommended Self-Paced Learning Materials

**Module 2: Move to Cloud Native (Containers and Serverless):**
- Cloud Design Patterns, Architectures, and Implementations — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html
  - Essential reference for extending the serverless architecture with event-driven patterns: Event Sourcing, Strangler Fig, Circuit Breaker, and API routing patterns directly applicable to the books-api modernization
- AWS Modernization Pathways: Move to Cloud Native Serverless — https://skillbuilder.aws/learning-plan/CMK2J48MVN/aws-modernization-pathways-move-to-cloud-native-serverless-includes-labs/EFUPP53B4Q
- Lambda Foundations — https://skillbuilder.aws/learn/XHRS91KKK6/aws-lambda-foundations/R85JRN3APC
- Architecting Serverless Applications — https://skillbuilder.aws/learn/MRWENY7FSX/architecting-serverless-applications/QVFY2JHVEH
- Amazon API Gateway for Serverless Applications — https://skillbuilder.aws/learn/GQA6FHWPJD/amazon-api-gateway-for-serverless-applications/JVRZ3PSW4H
  - Directly relevant for adding throttling, usage plans, and OpenAPI integration to the BooksApi
- Amazon DynamoDB for Serverless Architecture — https://skillbuilder.aws/learn/SY1Y83VKTB/amazon-dynamodb-for-serverless-architectures/K9NM3PHH3S
  - Covers DynamoDB Streams and event-driven patterns needed for CDC and embedding refresh pipelines

**Module 5: Move to Managed Analytics:**
- AWS Modernization Pathways: Move to Managed Analytics — https://skillbuilder.aws/learning-plan/RWZA84NMVV/aws-modernization-pathways-move-to-managed-analytics--includes-labs/9BAKK2QQQU
  - Relevant for understanding Kinesis and EventBridge streaming options for the book catalog event pipeline

**Module 6: Move to Modern DevOps:**
- Getting Started with DevOps on AWS — https://skillbuilder.aws/learn/R4B13K95YQ/getting-started-with-devops-on-aws/38NHHYRV1R
  - Although the Modern DevOps pathway was not triggered, the structured logging and SLO gaps make these resources valuable
- Advanced Testing Practices Using AWS DevOps Tools — https://skillbuilder.aws/learn/1YC7UXUWBR/advanced-testing-practices-using-aws-devops-tools/A32U6G7NEQ
  - Helpful for expanding the E2E test suite to cover agent evaluation scenarios
- Monitor Python Applications Using Amazon CloudWatch Application Signals — https://skillbuilder.aws/learn/JMPDZD64MV/monitor-python-applications-using-amazon-cloudwatch-application-signals/2JP3J2MPCK
  - Applicable concepts for adding Application Signals to the Lambda functions for SLO monitoring

**Module 7: Move to AI:**
- AWS Modernization Pathways: Move to AI — https://skillbuilder.aws/learning-plan/VDFEE4ACCV/aws-modernization-pathways-move-to-ai-pathways-includes-labs/P3DAWPTN63
- Introduction to Generative AI: Art of the Possible — https://skillbuilder.aws/learn/ZEVZZ1D4AS/introduction-to-generative-ai--art-of-the-possible/Y7MTGJCW1U
- Planning a Generative AI Project — https://skillbuilder.aws/learn/HU1FQRGDDZ/planning-a-generative-ai-project/SYR3SCPSHC
  - Critical for planning the book recommendation agent project scope and architecture
- Amazon Bedrock Getting Started — https://skillbuilder.aws/learn/63KTRM86DQ/amazon-bedrock-getting-started/SC2Y3HMAUE
  - Foundational for integrating Bedrock into the Lambda functions
- Essentials for Prompt Engineering — https://skillbuilder.aws/learn/XBNAVKA88J/essentials-of-prompt-engineering/9T9Q45EDTV
  - Needed for designing effective prompts for book recommendation and search agents
- Build and Evaluate Retrieval Augmented Generation (RAG) Applications using Knowledge Bases for Amazon Bedrock (Lab) — https://skillbuilder.aws/learn/JRGWCFYT67/lab--build-and-evaluate-retrieval-augmented-generation-rag-applications-using-knowledge-bases-for-amazon-bedrock/A4MN58JB7A
  - Directly applicable for building the RAG pipeline over the book catalog
- Introduction to Agentic AI on AWS — https://skillbuilder.aws/learn/DNBD5MT8ZD/introduction-to-agentic-ai-on-aws/WAKAFK6UFY
  - Core learning for understanding agentic patterns applicable to the books-api
- Creating an AWS DevOps AI Agent with the Strands Agents SDK (Lab) — https://skillbuilder.aws/learn/AH1GD8AJY3/lab--creating-an-aws-devops-ai-agent-with-the-strands-agents-sdk/A9SKJNMPJ2
  - Hands-on lab for building agents using Strands SDK, applicable to the TypeScript ecosystem
- AWS PartnerCast: Deep Dive: Building Observable AI Agents with Strands, Amazon Bedrock Agent Core & SageMaker MLflow — https://skillbuilder.aws/learn/1EN76TZBB6/aws-partnercast--deep-dive-building-observable-ai-agents-with-strands-amazon-bedrock-agent-core--sagemaker-mlflow--technical/CX2K6XAT84
  - Advanced observability patterns for agent workloads, addressing the OPS gaps identified

---

## Detailed Findings

### Infrastructure & Platform

#### INF-Q1: Compute
- **Score**: 4/4 ✅
- **Finding**: 100% serverless compute. `template.yml` defines three `AWS::Serverless::Function` resources: `GetAllBooks`, `CreateBook`, and `CreateBookPreTraffic`. All run on Node.js 22.x Lambda runtime with 512MB memory and 5-second timeout. No EC2 instances, no ECS tasks, no EKS clusters.
- **Gap**: None. Compute is fully agent-ready.
- **Recommendation**: When adding agent Lambda functions (Phase 3), consider increasing memory/timeout for Bedrock-calling functions (1024MB+, 30s+) as LLM invocations are more resource-intensive than DynamoDB CRUD.

#### INF-Q2: Databases
- **Score**: 4/4 ✅
- **Finding**: `template.yml` defines `BooksTable` as `AWS::Serverless::SimpleTable` — a fully managed DynamoDB table with SSE enabled (`SSESpecification.SSEEnabled: true`). Primary key is `isbn` (String). No self-managed database software detected in any file. No database installations in Dockerfiles or scripts.
- **Gap**: None. Database is fully managed.
- **Recommendation**: When agent state persistence is needed, use DynamoDB for conversation history and session state, leveraging the existing managed infrastructure pattern.

#### INF-Q3: Workflow Orchestration
- **Score**: 1/4 ❌
- **Finding**: No Step Functions, Temporal, Camunda, or any workflow orchestration service found in `template.yml` or source code. `CreateBookPreTraffic` in `src/books/create-pre-traffic/index.ts` is a CodeDeploy lifecycle hook (smoke test), not a workflow orchestration mechanism.
- **Gap**: No dedicated workflow orchestration for multi-step operations. Agent workflows (e.g., "find similar books, compare ratings, generate recommendation") require orchestration to manage state, retries, and human-in-the-loop approvals.
- **Recommendation**: Add AWS Step Functions for agent workflows. Define a state machine for the book recommendation workflow: receive query → search catalog → call Bedrock → format response → return. Step Functions provides built-in retry, error handling, and waitForTaskToken for human approvals.

#### INF-Q4: Async Messaging
- **Score**: 1/4 ❌
- **Finding**: No SQS, SNS, EventBridge, or MSK resources in `template.yml`. No messaging SDK imports in any Lambda function source code. All communication is synchronous: API Gateway → Lambda → DynamoDB.
- **Gap**: No async messaging infrastructure. Agent workflows need event-driven patterns for: emitting domain events (BookCreated), triggering downstream processes (embedding refresh), and decoupling long-running operations.
- **Recommendation**: Add EventBridge to `template.yml` with a custom event bus. Emit `BookCreated` events from the CreateBook Lambda after successful DynamoDB write. Add SQS dead-letter queues for reliable event processing. This is a prerequisite for the embedding refresh pipeline needed for RAG.

#### INF-Q5: Infrastructure as Code
- **Score**: 4/4 ✅
- **Finding**: Comprehensive IaC coverage. `template.yml` (SAM/CloudFormation) defines: 3 Lambda functions, API Gateway, DynamoDB table, Cognito User Pool/Client/Domain, CloudWatch Alarms, IAM roles. `pipeline/lib/pipeline-stack.ts` (CDK) defines: CodePipeline, CodeBuild projects, S3 artifact buckets, IAM roles. Estimated 95%+ of infrastructure is defined in code.
- **Gap**: None significant. Minor: some pipeline configuration (GitHub connection ARN) stored in SSM Parameter Store rather than IaC, which is acceptable.
- **Recommendation**: Maintain this IaC discipline as new agent infrastructure is added. Define Bedrock agent configurations, vector database resources, and Step Functions state machines in the same SAM template.

#### INF-Q6: CI/CD
- **Score**: 4/4 ✅
- **Finding**: Full CI/CD pipeline defined in `pipeline/lib/pipeline-stack.ts` with four stages: Source (GitHub via CodeStar Connection) → Build (unit tests + SAM build/package per `pipeline/buildspec.json`) → Staging (deploy + E2E tests per `pipeline/buildspec-test.json`) → Production (manual approval + deploy). Unit tests run in `pre_build` phase. E2E tests run after staging deployment. Manual approval gates production.
- **Gap**: None for current scope. Pipeline is well-structured.
- **Recommendation**: Add agent evaluation tests to the pipeline. In Phase 3, extend `buildspec-test.json` to include agent eval golden dataset tests after staging deployment.

#### INF-Q7: API Entry Point
- **Score**: 3/4 🟡
- **Finding**: `BooksApi` (`AWS::Serverless::Api`) in `template.yml` provides API Gateway with: Cognito authorizer (`CognitoAuth`), INFO-level method logging, X-Ray tracing (`TracingEnabled: true`), stage-based deployment. API Gateway acts as the single entry point with authentication on the POST endpoint.
- **Gap**: No explicit throttling or rate limiting configuration. No request validation schemas. No WAF integration. The `Auth` block only applies CognitoAuth to CreateBook — GetAllBooks is public.
- **Recommendation**: Add `ThrottlingBurstLimit` and `ThrottlingRateLimit` to the `MethodSettings` in `template.yml`. Add request validation using `Models` and `RequestValidator` for the POST `/books` endpoint. Consider adding WAF for bot protection when agent traffic increases.

#### INF-Q8: Real-time Streaming
- **Score**: 1/4 ❌
- **Finding**: No Kinesis, MSK, or any streaming resources in `template.yml`. No streaming SDK imports in source code. No Kafka, Redis Streams, or any event streaming patterns detected.
- **Gap**: No real-time streaming capability. Agent RAG pipelines need streaming for real-time embedding refresh when books are added or updated. Event streaming also enables real-time analytics on agent interaction patterns.
- **Recommendation**: Start with DynamoDB Streams (available on the existing `BooksTable`) for change data capture. If higher-throughput streaming is needed later, add Kinesis Data Streams. DynamoDB Streams is the lowest-effort path to streaming given the existing architecture.

#### INF-Q9: Network Security
- **Score**: 2/4 🟠
- **Finding**: No VPC, subnet, or security group resources in `template.yml`. Lambda functions run in the default AWS-managed network (not inside a VPC). No network segmentation. This is common and acceptable for simple serverless APIs, but limits network-level controls.
- **Gap**: No VPC isolation. When adding vector databases (OpenSearch) or other backend services, network isolation becomes important. No security group rules to restrict Lambda-to-backend traffic.
- **Recommendation**: For the current DynamoDB-only architecture, VPC is not required (DynamoDB has VPC endpoints). When adding OpenSearch Serverless or other backend services in Phase 3, configure VPC with private subnets and security groups. Use VPC endpoints for AWS service access.

#### INF-Q10: Auto-scaling
- **Score**: 3/4 🟡
- **Finding**: Lambda provides built-in auto-scaling (concurrent executions scale automatically). `BooksTable` (`AWS::Serverless::SimpleTable`) uses DynamoDB on-demand capacity by default, providing automatic scaling. No explicit reserved concurrency or provisioned concurrency configured for Lambda functions.
- **Gap**: No explicit Lambda concurrency limits configured. A sudden spike in agent traffic could consume all account-level Lambda concurrency, affecting other services. No provisioned concurrency for predictable agent workload latency.
- **Recommendation**: Add `ReservedConcurrentExecutions` to Lambda functions in `template.yml` to protect against runaway scaling. For agent-facing Lambda functions added in Phase 3, consider `ProvisionedConcurrency` to eliminate cold starts for latency-sensitive agent interactions.

### Application Architecture

#### APP-Q1: Programming Languages
- **Score**: 4/4 ✅
- **Finding**: TypeScript is the primary language across all Lambda functions (`src/books/get-all/index.ts`, `src/books/create/index.ts`, `src/books/create-pre-traffic/index.ts`) and CDK pipeline (`pipeline/lib/pipeline-stack.ts`). Runtime is Node.js 22.x (specified in `template.yml` Globals). E2E tests in JavaScript (`src/books/tests/index.js`). All `package.json` files confirm TypeScript toolchain (typescript ^5.7.3, ts-node, esbuild).
- **Gap**: None. TypeScript has an excellent agent framework ecosystem (LangChain.js, Strands Agents SDK, Vercel AI SDK).
- **Recommendation**: Continue with TypeScript for new agent Lambda functions. Consider using Strands Agents SDK (TypeScript) or LangChain.js for Bedrock integration.

#### APP-Q2: API Documentation
- **Score**: 1/4 ❌
- **Finding**: No OpenAPI or Swagger specification files found anywhere in the repository. `template.yml` sets `OpenApiVersion: 3.0.1` in the Globals section, but this is only to prevent SAM from creating a default "Stage" stage — no actual OpenAPI definition body exists. No API documentation annotations in Lambda function source code. No `api-docs`, `swagger.json`, or `openapi.yaml` files.
- **Gap**: Complete absence of API documentation. Agents require machine-readable API specs to understand available tools, parameters, response schemas, and error formats. Without OpenAPI specs, an agent cannot programmatically discover or validate API interactions.
- **Recommendation**: Generate an OpenAPI 3.0 specification. Use SAM's `DefinitionBody` property on the `BooksApi` resource to inline the spec in `template.yml`, or create a separate `openapi.yaml` file. Define schemas for the book model (isbn: string, title: string, year: number, author: string, publisher: string, rating: number, pages: number), request/response formats, error responses, and authentication requirements.

#### APP-Q3: Async vs Sync Communication
- **Score**: 1/4 ❌
- **Finding**: 100% synchronous communication. API Gateway receives HTTP requests synchronously, invokes Lambda synchronously, and Lambda makes synchronous DynamoDB calls (scan, putItem, getItem). Both `src/books/get-all/index.ts` and `src/books/create/index.ts` follow the same pattern: receive event → call DynamoDB → return HTTP response. No message publishing, no event emitting, no queue-based patterns.
- **Gap**: No async communication patterns at all. Agent workflows involving multiple steps (search → analyze → recommend → notify) need async patterns to avoid tight coupling and timeout constraints.
- **Recommendation**: Introduce EventBridge for domain events. After successful book creation in `src/books/create/index.ts`, emit a `BookCreated` event to EventBridge. This enables downstream consumers (embedding pipeline, notifications, analytics) without modifying the synchronous API contract.

#### APP-Q4: Monolith vs Microservices
- **Score**: 3/4 🟡
- **Finding**: Two independently deployable Lambda functions (`GetAllBooks`, `CreateBook`) behind a single `BooksApi` API Gateway, defined in `template.yml`. Each function has its own `package.json`, code directory, IAM policies, and deployment configuration. Functions share only the DynamoDB table name via environment variable. `CreateBookPreTraffic` is a deployment hook. This is a well-structured serverless application with clear function boundaries per endpoint.
- **Gap**: It is a single-service API (books domain only), not a microservices architecture. No inter-service communication, no service boundaries beyond function-level separation. As agent capabilities are added, the single SAM template could become a monolithic deployment unit.
- **Recommendation**: As new capabilities are added (semantic search, recommendations, agent orchestration), evaluate whether they should be separate SAM applications or separate stacks. Use the Parallel Track approach: add new Lambda functions alongside existing ones, and split into separate services when complexity warrants it.

#### APP-Q5: API Response Format
- **Score**: 4/4 ✅
- **Finding**: JSON responses confirmed in both Lambda functions. `src/books/get-all/index.ts` returns `{ statusCode: 200, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(bookDtos) }`. `src/books/create/index.ts` returns `{ statusCode: 201, headers: { 'Content-Type': 'application/json' }, body: '' }`. All responses use structured JSON with appropriate HTTP status codes and Content-Type headers.
- **Gap**: None. JSON is the preferred format for agent tool integration.
- **Recommendation**: Ensure new agent-facing endpoints follow the same JSON response pattern. Consider adding structured error response schemas (error code, message, details) for better agent error handling.

#### APP-Q6: Workflow Logic
- **Score**: 2/4 🟠
- **Finding**: No dedicated workflow orchestration. Business logic is simple CRUD operations: `src/books/get-all/index.ts` performs a DynamoDB scan, and `src/books/create/index.ts` performs a putItem. The pre-traffic hook (`src/books/create-pre-traffic/index.ts`) has a multi-step workflow (invoke Lambda → wait → getItem → deleteItem) but this is implemented as procedural code, not orchestrated via a workflow engine.
- **Gap**: No workflow engine for multi-step operations. The pre-traffic hook's sequential steps (invoke → wait → verify → cleanup) is a hand-coded workflow that would benefit from Step Functions for retry handling and error management.
- **Recommendation**: Add Step Functions for agent workflows. Start with the pre-traffic validation pattern as a proof-of-concept migration to Step Functions, then use Step Functions for new agent orchestration workflows.

#### APP-Q7: Idempotency
- **Score**: 2/4 🟠
- **Finding**: No explicit idempotency key handling in the CreateBook Lambda (`src/books/create/index.ts`). DynamoDB `putItem` with ISBN as the primary key provides natural idempotency for the same ISBN value (overwrites existing item). However, there is no `Idempotency-Key` HTTP header handling, no conditional writes (`ConditionExpression`), and no deduplication mechanism for preventing duplicate book creation with different ISBNs.
- **Gap**: No explicit idempotency pattern. Agent retries could create duplicate books with different ISBNs if the agent regenerates the ISBN on retry. No conditional writes to prevent overwriting existing books unintentionally.
- **Recommendation**: Add `@aws-lambda-powertools/idempotency` to the CreateBook function. Use a DynamoDB-based idempotency store with client-provided idempotency keys. Add `ConditionExpression: 'attribute_not_exists(isbn)'` to prevent accidental overwrites.

#### APP-Q8: Rate Limiting & Throttling
- **Score**: 1/4 ❌
- **Finding**: No API Gateway usage plans, no throttling configuration, no burst/rate limits in `template.yml`. No WAF rules. No application-level rate limiting middleware in Lambda functions. The `MethodSettings` in `template.yml` only configure logging level, not throttling.
- **Gap**: Complete absence of rate limiting. Agent-driven API calls can be high-frequency and bursty. Without rate limiting, a misbehaving agent loop could overwhelm the API, exhaust DynamoDB throughput, and cause service degradation.
- **Recommendation**: Add throttling to the `BooksApi` `MethodSettings` in `template.yml`: `ThrottlingBurstLimit: 100`, `ThrottlingRateLimit: 50`. Create API Gateway usage plans with API keys for agent consumers. Consider adding AWS WAF with rate-based rules for additional protection.

#### APP-Q9: Resilience Patterns
- **Score**: 2/4 🟠
- **Finding**: Lambda functions have a 5-second timeout configured in `template.yml` Globals. Both `src/books/get-all/index.ts` and `src/books/create/index.ts` have try/catch blocks that return 500 status on errors. AWS SDK v2 (`aws-sdk ^2.1692.0`) has built-in retry behavior with exponential backoff. However, no explicit retry configuration, no circuit breaker patterns, and no timeout tuning per function.
- **Gap**: No explicit resilience patterns. No circuit breakers for external service calls. No configurable retry policies. When Bedrock integration is added, LLM calls can be slow or fail, and without circuit breakers, cascading failures are likely.
- **Recommendation**: Implement resilience patterns before adding agent dependencies. Add `@aws-lambda-powertools` for middleware-based timeout enforcement. Add circuit breaker library (e.g., `opossum` for Node.js) for external calls. Configure explicit AWS SDK retry settings.

#### APP-Q10: Long-running Processes
- **Score**: 3/4 🟡
- **Finding**: Current operations are fast — DynamoDB scan and putItem complete well within the 5-second Lambda timeout. The pre-traffic hook (`src/books/create-pre-traffic/index.ts`) includes a 1500ms `wait()` function and multiple sequential DynamoDB/Lambda calls, but still completes within the default timeout. No operations currently exceed 30 seconds.
- **Gap**: No async infrastructure for future long-running operations. Agent workflows involving Bedrock calls (2-30 seconds per invocation), vector search, and multi-step reasoning will likely exceed the current 5-second timeout.
- **Recommendation**: Plan for async patterns: implement Lambda async invocations with callback URLs for agent workflows, or use Step Functions for orchestrating multi-step operations. Increase Lambda timeout to 30s+ for Bedrock-calling functions.

#### APP-Q11: API Versioning
- **Score**: 1/4 ❌
- **Finding**: No URL path versioning (`/v1/books`), no Accept-Version headers, no query parameter versioning, and no versioning annotations in `template.yml` or source code. The API path is simply `/books` with no version prefix. No changelog files found.
- **Gap**: No versioning strategy. When the API evolves to support agent-facing endpoints (semantic search, recommendations), breaking changes without versioning will disrupt existing consumers and agent integrations.
- **Recommendation**: Implement URL path versioning. Update `template.yml` API paths from `/books` to `/v1/books`. Add new agent endpoints under the same version (`/v1/books/search`, `/v1/books/recommend`). Document the versioning policy and backward compatibility guarantees.

#### APP-Q12: Service Discovery & Mesh
- **Score**: 2/4 🟠
- **Finding**: Single-service application — no inter-service communication required currently. DynamoDB table name is passed via environment variable (`TABLE: !Ref BooksTable` in `template.yml`), which is a good practice. API endpoint is output from CloudFormation (`Outputs.ApiEndpoint`). No hardcoded endpoints in Lambda function code (table name from `process.env.TABLE`).
- **Gap**: No service discovery mechanism for future multi-service architecture. No API catalog. As agent services are added, they will need to discover the books API endpoint.
- **Recommendation**: Continue using CloudFormation outputs and SSM Parameter Store for service endpoint discovery. When multiple services exist, consider AWS Cloud Map for service discovery. Use API Gateway as the service catalog for agent tool discovery.

#### APP-Q13: AI/Agent Frameworks
- **Score**: 1/4 ❌
- **Finding**: No AI or agent framework dependencies in any `package.json`. No imports of `@aws-sdk/client-bedrock-runtime`, `langchain`, `@langchain/*`, `openai`, `anthropic`, `strands-agents`, or any AI SDK. No Bedrock, SageMaker, or AI service references in `template.yml`. No MCP SDK imports. Zero AI/agent integration.
- **Gap**: Complete absence of AI/agent framework integration. This is the primary blocker for agentic readiness. The application cannot participate in agent workflows as either an agent or a tool without AI framework integration.
- **Recommendation**: Start with `@aws-sdk/client-bedrock-runtime` for direct Bedrock access. Evaluate Strands Agents SDK (TypeScript) for higher-level agent patterns. Create a proof-of-concept agent Lambda that uses the existing DynamoDB book catalog as a tool. The existing clean API (JSON responses, structured data) provides a solid foundation for tool integration.

### Data Foundations

#### DATA-Q1: Vector Database Presence
- **Score**: 1/4 ❌
- **Finding**: No vector database present in `template.yml` or any configuration file. No OpenSearch, Aurora pgvector, S3 Vectors, Bedrock Knowledge Bases, Pinecone, Weaviate, or Chroma references found in IaC or `package.json` dependencies. No k-NN search patterns in source code.
- **Gap**: No vector database for semantic search. Agent-powered book discovery (e.g., "find books similar to X" or "books about cloud computing") requires vector embeddings and similarity search, which DynamoDB cannot provide.
- **Recommendation**: Provision Amazon OpenSearch Serverless with vector search capability, or use Amazon Bedrock Knowledge Bases (managed RAG). For the simplest path, Bedrock Knowledge Bases can be configured to index DynamoDB data via S3 export, requiring minimal custom code.

#### DATA-Q2: Vector DB Management
- **Score**: 1/4 ❌
- **Finding**: No vector database exists, therefore no management to assess. No self-hosted or managed vector DB detected.
- **Gap**: Prerequisite (DATA-Q1) not met.
- **Recommendation**: When adding a vector database, use a fully managed option: Amazon OpenSearch Serverless (managed, no cluster management) or Amazon Bedrock Knowledge Bases (fully managed RAG service). Avoid self-hosted options to maintain the fully managed infrastructure pattern established with DynamoDB and Lambda.

#### DATA-Q3: RAG Implementation
- **Score**: 1/4 ❌
- **Finding**: No RAG pipeline components found. No embedding model calls (Bedrock Titan, OpenAI ada), no document chunking or splitting code, no similarity_search or knn_search patterns, no Bedrock Knowledge Base integration in any file.
- **Gap**: No RAG capability. Agents need semantic search over the book catalog to answer natural language queries ("what are the highest-rated science fiction books?"). Without RAG, the agent would rely solely on DynamoDB scan operations, which don't support semantic queries.
- **Recommendation**: Implement a RAG pipeline: (1) Export book data from DynamoDB to S3 as JSON documents, (2) Configure Bedrock Knowledge Base with Titan Embeddings model, (3) Set up automated sync when books are added/updated using DynamoDB Streams → Lambda → S3 → Knowledge Base sync.

#### DATA-Q4: Data Source Sprawl
- **Score**: 4/4 ✅
- **Finding**: Single data source — DynamoDB `BooksTable` defined in `template.yml`. All Lambda functions access only this one table. `src/books/get-all/index.ts` reads from `process.env.TABLE`. `src/books/create/index.ts` writes to `process.env.TABLE`. `src/books/create-pre-traffic/index.ts` reads/writes to `process.env.TABLE`. E2E tests (`src/books/tests/books-manager.js`) access the same table. Clean, simple data architecture.
- **Gap**: None. Single data source is agent-ready.
- **Recommendation**: Maintain this simplicity. When adding a vector database, create a unified data access layer that abstracts both DynamoDB (structured queries) and the vector store (semantic queries) behind a common interface.

#### DATA-Q5: Data Access Pattern
- **Score**: 2/4 🟠
- **Finding**: Lambda functions access DynamoDB directly via AWS SDK v2 (`aws-sdk ^2.1692.0`). Each handler creates its own DynamoDB client instance: `new AWS.DynamoDB(ddbOptions)` in `src/books/get-all/index.ts` and `src/books/create/index.ts`. The client setup pattern (including X-Ray wrapping and local development endpoint) is duplicated across both functions. Raw DynamoDB API calls (scan, putItem) are directly in handler functions. No repository pattern, no data access layer, no abstraction.
- **Gap**: Duplicated DynamoDB client setup across functions. Raw API calls in handlers mix data access with request handling. Uses deprecated AWS SDK v2 instead of v3 modular SDK. This pattern will become increasingly unmaintainable as more functions are added for agent workflows.
- **Recommendation**: Create a shared data access layer in `src/books/lib/books-repository.ts`. Implement the repository pattern with typed Book interface. Migrate from `aws-sdk` v2 to `@aws-sdk/client-dynamodb` v3 (modular, tree-shakeable). This layer will also be the integration point for the vector database.

#### DATA-Q6: Unstructured Data
- **Score**: 1/4 ❌
- **Finding**: No S3 storage, no Textract integration, no document parsing libraries (Tika, pdf-parse), no image/PDF processing. The application only handles structured book metadata (isbn, title, year, author, publisher, rating, pages) in DynamoDB. No `aws_s3_bucket` resources in `template.yml`.
- **Gap**: No unstructured data handling. If the books API evolves to include book covers, summaries, or full-text content, S3 storage with parsing capabilities will be needed for agent consumption.
- **Recommendation**: Low priority for current scope. When book content (PDFs, images) needs to be indexed, add S3 bucket for storage and Textract for document parsing. This feeds into the RAG pipeline for full-text semantic search.

#### DATA-Q7: Schema Documentation
- **Score**: 1/4 ❌
- **Finding**: No JSON Schema files, no Avro or Protobuf schemas, no database migration files, no schema registry. The book data schema (isbn, title, year, author, publisher, rating, pages) is implicitly defined across multiple files: `src/books/create/index.ts` (putItem params), `src/books/get-all/index.ts` (scan result mapping), `src/books/tests/books-manager.js` (test data structure), and `events/create-book-request.json` (sample event). No single source of truth for the schema.
- **Gap**: Schema is scattered across code files with no formal documentation or versioning. Agent tools need schema definitions to understand data structure, validate inputs, and format outputs correctly.
- **Recommendation**: Define a TypeScript interface for the Book type in a shared `src/books/lib/types.ts`. Create a JSON Schema for the book model that can be referenced in the OpenAPI spec. This becomes the single source of truth for agent tool parameter definitions.

#### DATA-Q8: Data Access Layer
- **Score**: 2/4 🟠
- **Finding**: No unified data access layer. DynamoDB is accessed directly in each Lambda handler. `src/books/get-all/index.ts` creates `new AWS.DynamoDB(ddbOptions)` and calls `client.scan()`. `src/books/create/index.ts` creates a separate DynamoDB client and calls `client.putItem()`. `src/books/create-pre-traffic/index.ts` creates yet another client (`new DynamoDB()`) for getItem and deleteItem. `src/books/tests/books-manager.js` creates a fourth client for test data management. Four separate DynamoDB client instances across the codebase.
- **Gap**: Scattered data access with duplicated client configuration. No centralized error handling for data operations. No data validation layer. Adding a vector database will exacerbate this pattern if not addressed.
- **Recommendation**: Create `src/books/lib/books-repository.ts` implementing the repository pattern. Centralize DynamoDB client creation, X-Ray wrapping, error handling, and data mapping. All Lambda handlers should use this repository. This single data contract point will simplify adding vector database operations alongside DynamoDB.

#### DATA-Q9: Embedding Freshness
- **Score**: 1/4 ❌
- **Finding**: No embedding pipeline exists. No event-driven embedding refresh triggers, no scheduled re-indexing, no Bedrock Knowledge Base sync configuration, no CDC (Change Data Capture) patterns detected. No DynamoDB Streams configured on `BooksTable` in `template.yml`.
- **Gap**: No mechanism to keep embeddings up to date. When books are added or updated, the vector index will become stale unless there is an automated refresh mechanism.
- **Recommendation**: Enable DynamoDB Streams on `BooksTable` in `template.yml`. Create a Lambda function triggered by stream events that generates embeddings for new/updated books and writes them to the vector store. Alternatively, use Bedrock Knowledge Base automated sync with a schedule.

#### DATA-Q10: Database Engine Version & EOL
- **Score**: 4/4 ✅
- **Finding**: DynamoDB is a fully managed serverless database — AWS manages all engine versions, patches, and lifecycle. There is no engine version to pin or monitor for EOL. `AWS::Serverless::SimpleTable` in `template.yml` requires no version specification. DynamoDB has no EOL risk.
- **Gap**: None. Fully managed.
- **Recommendation**: No action needed. DynamoDB's serverless model eliminates version management concerns entirely.

#### DATA-Q11: Stored Procedures & Schema Complexity
- **Score**: 4/4 ✅
- **Finding**: No stored procedures, triggers, proprietary SQL constructs, or database-side business logic. DynamoDB is a NoSQL key-value/document store with no SQL layer. All business logic resides in Lambda function application code (`src/books/create/index.ts` and `src/books/get-all/index.ts`). No `.sql` files found in the repository. No ORM bypass patterns or raw SQL execution.
- **Gap**: None. All business logic is cleanly in the application layer.
- **Recommendation**: Maintain this pattern. Keep all business logic in Lambda functions, including any future agent orchestration logic. This ensures clean separation and portability.

### Identity, Security & Governance

#### SEC-Q1: Secret Management
- **Score**: 3/4 🟡
- **Finding**: No Secrets Manager or SSM SecureString usage in `template.yml`. However, no hardcoded secrets found in any source code file. Environment variables contain only non-sensitive values: `TABLE` (DynamoDB table reference via `!Ref BooksTable`) and `FN_NEW_VERSION` (Lambda function version ARN). Cognito tokens are obtained at runtime via OAuth flow. The GitHub connection ARN is stored in SSM Parameter Store (`StringParameter.fromStringParameterName` in `pipeline/lib/pipeline-stack.ts`). No `.env` files committed (`.gitignore` excludes `.vscode` but not `.env` — however, no `.env` files exist).
- **Gap**: No secret management infrastructure for future needs. When Bedrock API keys, external service credentials, or database connection strings are needed for agent integrations, there is no established pattern for secret retrieval.
- **Recommendation**: Establish Secrets Manager pattern now. Add `aws_secretsmanager_secret` resource in `template.yml` as a template for future secrets. Document the pattern for retrieving secrets in Lambda functions using `@aws-sdk/client-secrets-manager`.

#### SEC-Q2: IAM Least Privilege
- **Score**: 2/4 🟠
- **Finding**: **Application IAM (good)**: SAM template uses scoped SAM policy templates: `DynamoDBReadPolicy` for `GetAllBooks`, `DynamoDBWritePolicy` for `CreateBook`, `DynamoDBCrudPolicy` for `CreateBookPreTraffic` — all scoped to `!Ref BooksTable`. Custom inline policies for `CreateBookPreTraffic` scope `codedeploy:PutLifecycleEventHookExecutionStatus` to the specific deployment group and `lambda:InvokeFunction` to the specific function version. **Pipeline IAM (poor)**: `pipeline/lib/pipeline-stack.ts` deploy role uses 7 `FullAccess` managed policies: `AWSCloudFormationFullAccess`, `AmazonDynamoDBFullAccess`, `AWSLambda_FullAccess`, `AmazonAPIGatewayAdministrator`, `IAMFullAccess`, `AWSCodeDeployFullAccess`, `AmazonCognitoPowerUser`. Test role uses `AmazonCognitoPowerUser` and `AmazonDynamoDBFullAccess`.
- **Gap**: Pipeline IAM roles have wildcard permissions across all resources. `IAMFullAccess` on the deploy role is particularly dangerous — it can create/modify any IAM role in the account. This violates least privilege and poses a significant security risk, especially when agents will be granted IAM roles.
- **Recommendation**: Replace `FullAccess` managed policies with custom inline policies specifying only the required actions and resources. Scope CloudFormation permissions to the specific stack. Scope DynamoDB permissions to the books table. Scope Lambda permissions to the books-* functions. Remove `IAMFullAccess` and replace with specific IAM actions needed for SAM deployment.

#### SEC-Q3: Identity Propagation
- **Score**: 2/4 🟠
- **Finding**: Cognito User Pool configured in `template.yml` with OAuth2 implicit grant flow. `CognitoAuth` authorizer applied to the `CreateBook` POST endpoint with `AuthorizationScopes: [email]`. However, the `CreateBook` Lambda handler (`src/books/create/index.ts`) does not extract or use the authenticated user identity from the JWT token — it only parses `event.body` for book data. The `GetAllBooks` endpoint has no authentication.
- **Gap**: User identity is verified at the API Gateway level but not propagated into the application logic. The Lambda function does not know who created a book. When agents act on behalf of users, the system cannot attribute actions to specific users.
- **Recommendation**: Extract user identity from `event.requestContext.authorizer.claims` in the CreateBook Lambda. Log the authenticated user for audit purposes. Store the `userId` alongside book records in DynamoDB for ownership tracking. This is essential for agent accountability — knowing which user's agent created each book.

#### SEC-Q4: Audit Logging
- **Score**: 2/4 🟠
- **Finding**: API Gateway has INFO-level logging configured in `template.yml` (`LoggingLevel: INFO` with `CloudWatchRoleArn`). X-Ray tracing is enabled for API-to-Lambda-to-DynamoDB call chain. Lambda functions have `Tracing: Active` globally. However, no CloudTrail configuration in IaC. No immutable log storage (no S3 bucket with Object Lock for logs). No log retention policies configured. No audit trail for data modifications.
- **Gap**: No CloudTrail for API-level audit trail. No immutable log storage. No data access audit logging. When agents perform actions, there must be an immutable record of every action taken, by whom, and when.
- **Recommendation**: Add CloudTrail configuration in `template.yml` with log file validation enabled. Configure CloudWatch log retention policies for all Lambda log groups. For agent audit trails, implement structured logging of every agent action with user identity, timestamp, and action details.

#### SEC-Q5: API Rate Limits
- **Score**: 1/4 ❌
- **Finding**: No API Gateway usage plans in `template.yml`. No throttling configuration on `BooksApi`. No WAF rate-based rules. No per-client quotas. The `MethodSettings` only configure logging, not throttling. No application-level rate limiting in Lambda code.
- **Gap**: Complete absence of rate limiting at any layer. Agent API calls are typically high-frequency and programmatic. Without rate limits, a single misbehaving agent could exhaust all available capacity.
- **Recommendation**: Add API Gateway throttling in `template.yml`: set `ThrottlingBurstLimit` and `ThrottlingRateLimit` on `MethodSettings`. Create usage plans with API keys for different consumer tiers (human users vs. agents). Add WAF with rate-based rules for DDoS protection.

#### SEC-Q6: PII Redaction
- **Score**: 1/4 ❌
- **Finding**: No PII redaction in any Lambda function. Error handling in `src/books/get-all/index.ts` and `src/books/create/index.ts` catches exceptions but returns empty body `''` — no PII leakage in error responses currently. The pre-traffic hook (`src/books/create-pre-traffic/index.ts`) logs full DynamoDB items (`console.log('DynamoDB item', JSON.stringify(Item, null, 2))`) and full events (`console.log('CodeDeploy event', event)`) without any redaction. No log scrubbing middleware. No Macie integration.
- **Gap**: No PII redaction patterns. While the current book model (isbn, title, author) has minimal PII risk, agent interactions will involve user queries, preferences, and potentially personal data that must be redacted from logs.
- **Recommendation**: Add a logging middleware that automatically redacts sensitive fields. Use `@aws-lambda-powertools/logger` with custom serializers to mask PII fields. Establish a PII field registry that all agent-facing functions reference. Consider Amazon Macie for automated PII discovery in logs.

#### SEC-Q7: Human Approval Workflows
- **Score**: 2/4 🟠
- **Finding**: Pipeline has `ManualApprovalAction` in `pipeline/lib/pipeline-stack.ts` for production deployment with informational text: "Ensure Books API works correctly in Staging and release date is agreed with Product Owners." This gates code deployment to production. However, no human approval mechanism exists for application-level high-risk operations (bulk data deletion, bulk data modification).
- **Gap**: Human approval exists only for deployments, not for runtime operations. Agent workflows that perform high-risk actions (deleting books, bulk updates) need human-in-the-loop approval gates.
- **Recommendation**: Add Step Functions with `waitForTaskToken` for human approval of high-risk agent actions. For example, if an agent recommends deleting duplicate books, the workflow should pause for human confirmation before executing. Start with identifying which operations should require approval.

#### SEC-Q8: Encryption at Rest
- **Score**: 3/4 🟡
- **Finding**: DynamoDB table has `SSESpecification.SSEEnabled: true` in `template.yml` — encrypted at rest with AWS-managed keys. S3 artifact buckets in `pipeline/lib/pipeline-stack.ts` use `BucketEncryption.S3_MANAGED`. All data stores are encrypted. However, no customer-managed KMS keys (CMK) are used. No `aws_kms_key` resources defined.
- **Gap**: Using AWS-managed encryption only, not customer-managed KMS keys. While AWS-managed encryption is sufficient for many use cases, customer-managed keys provide additional control (key rotation policies, cross-account access, granular key policies).
- **Recommendation**: For the current scope, AWS-managed encryption is acceptable. When handling sensitive agent data (user queries, LLM responses), upgrade to customer-managed KMS keys for DynamoDB, S3, and any new data stores. This provides fine-grained access control over who can decrypt agent conversation data.

#### SEC-Q9: API Authentication
- **Score**: 2/4 🟠
- **Finding**: `CreateBook` POST endpoint has Cognito authorization via `CognitoAuth` authorizer with `AuthorizationScopes: [email]` (and `aws.cognito.signin.user.admin` in staging). `GetAllBooks` GET endpoint has **no authentication** — it is publicly accessible. Partial authentication coverage: 1 of 2 API endpoints is authenticated.
- **Gap**: Read endpoint is unauthenticated. Anyone can list all books without authentication. When agents interact with the API, all endpoints should be authenticated to ensure proper attribution and access control.
- **Recommendation**: Add CognitoAuth to the GetAllBooks endpoint. Implement different OAuth scopes for read vs. write operations. For agent consumers, consider using Cognito client credentials flow (machine-to-machine) instead of the current implicit grant flow which is designed for browser-based apps.

#### SEC-Q10: Centralized Identity
- **Score**: 3/4 🟡
- **Finding**: `CognitoUserPool` configured in `template.yml` as the identity provider. `UserPoolClient` supports OAuth2 implicit grant with `email` and `openid` scopes. `UserPoolDomain` provides a hosted UI for authentication. Single centralized identity provider for the API. Password policy configured (minimum 6 chars, requires numbers).
- **Gap**: No SSO or external identity federation (SAML, OIDC with corporate identity provider). Implicit grant flow is deprecated in OAuth 2.1. No service-to-service authentication pattern for agent consumers. Password policy is weak (6 chars, no uppercase required).
- **Recommendation**: Strengthen password policy (12+ chars, mixed case). Migrate from implicit grant to authorization code flow with PKCE. Add client credentials grant for machine-to-machine (agent) authentication. Consider federation with corporate identity provider if applicable.

### Operations & Observability

#### OPS-Q1: Distributed Tracing
- **Score**: 3/4 🟡
- **Finding**: X-Ray tracing is enabled globally in `template.yml` (`Function.Tracing: Active`) and on API Gateway (`TracingEnabled: true`). Lambda functions import and use `aws-xray-sdk-core` for SDK instrumentation: `AWSXRay.captureAWS(AWSCore)` in both `src/books/get-all/index.ts` and `src/books/create/index.ts`. This provides end-to-end trace propagation from API Gateway → Lambda → DynamoDB. X-Ray SDK is listed as a dependency in `src/books/get-all/package.json` and `src/books/create/package.json` (`aws-xray-sdk-core: ^3.10.3`).
- **Gap**: No OpenTelemetry integration. No `gen_ai.*` semantic conventions for LLM tracing. No service mesh or APM service map. Tracing is X-Ray only — when agent workloads are added, gen_ai semantic conventions will be needed to trace LLM calls, tool invocations, and agent reasoning steps.
- **Recommendation**: Migrate to OpenTelemetry (ADOT Lambda layer) for vendor-neutral tracing. When adding Bedrock integration, add gen_ai semantic conventions to traces for LLM call duration, token counts, model ID, and prompt/response tracking. This enables unified observability across traditional and agent workloads.

#### OPS-Q2: Structured Logging
- **Score**: 1/4 ❌
- **Finding**: No structured logging in any Lambda function. `src/books/create-pre-traffic/index.ts` uses basic `console.log()` for 6 log statements (e.g., `console.log('Entering PreTraffic Hook!')`, `console.log('DynamoDB item', JSON.stringify(Item, null, 2))`). `src/books/get-all/index.ts` and `src/books/create/index.ts` have **no logging at all** — errors are silently caught and a 500 status code is returned. No JSON log formatters (winston, pino, structlog). No correlation IDs. No request/response logging.
- **Gap**: Complete absence of structured logging. Agent workflows generate complex execution paths that are impossible to debug without structured, correlated, searchable logs. Silent error swallowing in the main handlers means failures are invisible.
- **Recommendation**: Install `@aws-lambda-powertools/logger` in all Lambda functions. Configure JSON output with log level, timestamp, request ID, X-Ray trace ID, and function name. Add request/response logging middleware. Log errors with full context (not just catch-and-return-500). This is the highest-priority Phase 1 item.

#### OPS-Q3: Automated Evals
- **Score**: 1/4 ❌
- **Finding**: No agent evaluation framework. No eval datasets, no scoring scripts, no LLM-as-judge patterns, no golden dataset files, no RAGAS integration, no pytest with LLM assertions. The existing test suites (`src/books/tests/index.js` and unit tests) test HTTP API behavior only, not AI/agent quality.
- **Gap**: No evaluation infrastructure for agent quality. When agents are added, there is no way to measure recommendation quality, detect hallucinations, track accuracy over time, or run regression tests on prompt changes.
- **Recommendation**: Build an eval framework in Phase 3. Create golden datasets for book recommendation quality (input query → expected results). Implement scoring functions that measure relevance, accuracy, and safety. Integrate eval runs into the CI/CD pipeline alongside E2E tests. Use Bedrock model evaluation APIs or custom scoring Lambda functions.

#### OPS-Q4: SLOs
- **Score**: 2/4 🟠
- **Finding**: Two CloudWatch alarms defined in `template.yml`: `CreateBookAliasErrorMetricGreaterThanZeroAlarm` and `GetAllBooksAliasErrorMetricGreaterThanZeroAlarm`. Both alarm on Lambda errors > 0 with 60-second periods and 2 evaluation periods. These alarms are used as rollback triggers for CodeDeploy progressive deployment. No SLO definitions, no error budget tracking, no latency targets (p99/p95), no availability targets.
- **Gap**: Basic error alarms exist but are not SLO definitions. No latency monitoring (p99 could degrade without triggering an alarm). No error budget tracking. No SLO dashboards. Agents require strict SLOs — a slow recommendation endpoint can cause agent timeout cascades.
- **Recommendation**: Define SLOs: 99.9% availability for both endpoints, <200ms p99 latency for GetAllBooks, <500ms p99 for CreateBook. Add CloudWatch alarms on p99 latency using `Duration` metric. Create a CloudWatch dashboard with SLO tracking. When agent endpoints are added, define agent-specific SLOs (task success rate, tool error rate, response latency).

#### OPS-Q5: Rollback Capability
- **Score**: 3/4 🟡
- **Finding**: Production deployment uses `Linear10PercentEvery1Minute` progressive deployment in `template.yml` for both `GetAllBooks` and `CreateBook` functions. CloudWatch alarms (`*AliasErrorMetricGreaterThanZeroAlarm`) trigger automatic rollback if errors occur during deployment. `CreateBook` has a pre-traffic hook (`CreateBookPreTraffic`) that validates the new version before traffic is shifted — if the smoke test fails, deployment is aborted. Staging uses `AllAtOnce` deployment.
- **Gap**: Rollback covers code deployments only, not configuration or prompts. No feature flag infrastructure for gradual rollout of agent features. No prompt versioning mechanism for rolling back agent behavior changes.
- **Recommendation**: Add feature flag infrastructure (e.g., AWS AppConfig or LaunchDarkly) for gradual rollout of agent features. Implement prompt versioning alongside code versioning — store prompt templates in a versioned location (S3, DynamoDB) with rollback capability. Extend the canary deployment pattern to agent-specific metrics.

#### OPS-Q6: LLM Cost Tracking
- **Score**: 1/4 ❌
- **Finding**: No LLM usage in the application. No Bedrock, SageMaker, or any LLM service integration. No token counting, no cost attribution, no usage tracking. No CloudWatch custom metrics for AI-related costs.
- **Gap**: No LLM cost tracking infrastructure. When Bedrock is integrated, token usage per request must be tracked to prevent cost overruns and enable attribution to specific users, features, or agent workflows.
- **Recommendation**: When adding Bedrock integration, extract `usage` data from Bedrock API responses (input tokens, output tokens). Publish CloudWatch custom metrics with dimensions for endpoint, user, and workflow. Set CloudWatch alarms on daily token spend. Implement tiered log retention policies for agent traces (retain summaries long-term, detailed traces short-term).

#### OPS-Q7: Business Metrics
- **Score**: 1/4 ❌
- **Finding**: No custom business metrics. The only metrics are infrastructure-level CloudWatch alarms on Lambda errors. No tracking of: books created per day, most popular books, API usage patterns, user engagement, search queries, or any business KPIs. No `cloudwatch.putMetricData` calls in any Lambda function.
- **Gap**: No business outcome visibility. When agents are added, business metrics (recommendation acceptance rate, user satisfaction, task completion rate) are essential for measuring agent effectiveness and justifying investment.
- **Recommendation**: Add CloudWatch custom metrics for business events: `BooksCreated` count, `BooksRetrieved` count, API response times by endpoint. Create a business dashboard. In Phase 3, add agent-specific business metrics: recommendation acceptance rate, query satisfaction, task completion rate.

#### OPS-Q8: Anomaly Detection
- **Score**: 2/4 🟠
- **Finding**: CloudWatch alarms use static thresholds: Lambda errors > 0 triggers alarm. No anomaly detection models. No behavioral baselines. No composite alarms. No PagerDuty/OpsGenie integration detected.
- **Gap**: Static threshold alarms (error > 0) are basic. No anomaly detection for latency patterns or traffic spikes. Agents exhibit non-deterministic behavior — an agent calling 15 tools instead of 3 may indicate a reasoning loop, which static thresholds won't catch.
- **Recommendation**: Enable CloudWatch anomaly detection on key metrics (invocation count, duration, error rate). Add composite alarms that combine error rate + latency anomaly + invocation count anomaly. In Phase 3, add agent-specific anomaly detection: tool call frequency, reasoning step count, token usage per request.

#### OPS-Q9: Deployment Strategy
- **Score**: 3/4 🟡
- **Finding**: Production deployments use `Linear10PercentEvery1Minute` progressive traffic shifting in `template.yml`. Pre-traffic hooks validate new versions before traffic shift. CloudWatch alarms automatically roll back failed deployments. Staging uses `AllAtOnce` for faster iteration. Pipeline includes manual approval gate before production deployment (`ManualApprovalAction` in `pipeline/lib/pipeline-stack.ts`).
- **Gap**: No canary deployment with automatic metric analysis. No feature flags for gradual rollout. No multi-region deployment strategy. The linear deployment shifts traffic at a fixed rate regardless of metric health — a true canary would analyze metrics at each step.
- **Recommendation**: Current strategy is good for the application's scope. For agent workloads, consider adding feature flags for prompt/behavior changes that don't require code deployment. Evaluate `Canary10Percent5Minutes` for agent Lambda functions to allow more time for metric evaluation between shifts.

#### OPS-Q10: Integration Testing
- **Score**: 3/4 🟡
- **Finding**: E2E test suite in `src/books/tests/index.js` using Mocha and Chai. Tests cover: (1) GET /books returns 200 without auth, (2) GET /books returns correct book data after insertion, (3) POST /books returns 401 without token, (4) POST /books returns 500 with invalid payload, (5) POST /books creates book with valid auth. Tests create/delete Cognito users programmatically. Test data managed via `src/books/tests/books-manager.js`. Tests run in CI pipeline after staging deployment (`pipeline/buildspec-test.json`). Unit tests run in build phase per function (`pipeline/buildspec.json`).
- **Gap**: Tests cover HTTP API behavior only. No contract tests. No load tests. No chaos engineering. When agents are added, test coverage must extend to agent behavior: recommendation quality, tool invocation correctness, error handling, and multi-step workflow completion.
- **Recommendation**: Add contract tests for the book API schema. Add load tests to validate auto-scaling behavior. In Phase 3, add agent integration tests: end-to-end tests for recommendation workflows, tool invocation tests, and failure scenario tests (Bedrock timeout, DynamoDB throttling).

#### OPS-Q11: Incident Response Automation
- **Score**: 2/4 🟠
- **Finding**: Automated rollback via CodeDeploy alarm triggers provides basic incident response for deployment failures. Pre-traffic hooks prevent bad deployments from receiving traffic. However, no runbook files (markdown, YAML, or JSON) found in the repository. No SSM Automation documents. No Lambda-based remediation functions. No self-healing patterns beyond deployment rollback. No incident response workflows.
- **Gap**: Incident response is limited to deployment rollback. No operational runbooks for common issues (DynamoDB throttling, Lambda cold start spikes, Cognito issues). No automated remediation for runtime failures. Agent incidents (hallucination, infinite loops, unauthorized actions) require specialized runbooks.
- **Recommendation**: Create operational runbooks in the repository as markdown files. Define incident response procedures for: API errors > threshold, DynamoDB throttling, Lambda concurrency exhaustion. In Phase 3, create agent-specific runbooks: agent loop detection, hallucination response, cost runaway mitigation. Consider SSM Automation documents for automated remediation.

#### OPS-Q12: Observability Governance & Ownership
- **Score**: 1/4 ❌
- **Finding**: No CODEOWNERS file in the repository. No SLO definition files. No per-service dashboards defined in IaC. No observability ownership model documented. No team ownership files referencing observability assets. Tags in `template.yml` indicate `project: my-project` and `environment: !Ref Stage` but no team ownership tags.
- **Gap**: No observability governance. No ownership model for monitoring, alerting, and SLO management. When agent workloads are added, clear ownership of agent quality, reliability, and safety metrics is essential — otherwise, agent failures will have no accountable owner.
- **Recommendation**: Add a CODEOWNERS file defining ownership of `template.yml`, Lambda functions, and pipeline. Create an SLO document defining target SLOs, owners, and escalation paths. Add `team` and `owner` tags to all resources in `template.yml`. In Phase 3, define agent SLO ownership: who owns task success rate, who owns hallucination rate, who responds to agent safety incidents.

---

## Appendix: Evidence Index

| # | File | What It Revealed |
|---|------|------------------|
| 1 | `template.yml` | SAM/CloudFormation template defining all infrastructure: 3 Lambda functions (Node.js 22.x), API Gateway with Cognito auth, DynamoDB table with SSE, CloudWatch alarms, CodeDeploy progressive deployment. Primary evidence source for INF and SEC criteria. |
| 2 | `pipeline/lib/pipeline-stack.ts` | CDK-defined CI/CD pipeline: 4-stage CodePipeline (Source→Build→Staging→Production), ManualApprovalAction for production, overly permissive IAM with 7 FullAccess managed policies on deploy role. |
| 3 | `src/books/get-all/index.ts` | Lambda handler for GET /books: DynamoDB scan operation, X-Ray SDK instrumentation, JSON response with book DTOs, try/catch with silent 500 errors, no logging, uses aws-sdk v2. |
| 4 | `src/books/create/index.ts` | Lambda handler for POST /books: DynamoDB putItem, X-Ray instrumentation, JSON parsing of request body, no idempotency handling, no user identity extraction, no logging. |
| 5 | `src/books/create-pre-traffic/index.ts` | CodeDeploy pre-traffic hook: smoke test that invokes CreateBook Lambda, verifies DynamoDB write, cleans up test data. Uses console.log (only function with logging). Multi-step procedural workflow. |
| 6 | `src/books/get-all/package.json` | Dependencies: aws-sdk ^2.1692.0, aws-xray-sdk-core ^3.10.3. Dev dependencies: TypeScript, Mocha, Sinon, Chai for unit testing. No AI/agent framework dependencies. |
| 7 | `src/books/create/package.json` | Dependencies: aws-sdk ^2.1692.0, aws-xray-sdk-core ^3.10.3. Same pattern as get-all. Confirms consistent dependency management. |
| 8 | `src/books/create-pre-traffic/package.json` | Dependencies: aws-sdk ^2.1692.0 only (no X-Ray SDK). Dev dependencies: TypeScript, esbuild. No test framework. |
| 9 | `src/books/tests/index.js` | E2E test suite: Mocha/Chai tests covering GET (public) and POST (authenticated) endpoints. Creates/deletes Cognito users programmatically. Tests auth enforcement and schema validation. |
| 10 | `src/books/tests/books-manager.js` | Test data manager: DynamoDB batch write/delete for test books. Creates fourth separate DynamoDB client instance. Confirms data schema pattern. |
| 11 | `src/books/tests/package.json` | E2E test dependencies: aws-sdk, axios, uuid, mocha, chai. Confirms JavaScript (not TypeScript) for tests. |
| 12 | `pipeline/buildspec.json` | Build spec: installs SAM CLI, runs npm install recursively, executes unit tests per function, runs sam build + sam package. Exports ARTIFACTS_PATH to S3. |
| 13 | `pipeline/buildspec-deploy.json` | Deploy spec: downloads SAM package from S3, runs sam deploy with stack name and stage parameter. Exports CloudFormation outputs (API endpoint, Cognito IDs, table name). |
| 14 | `pipeline/buildspec-test.json` | Test spec: installs E2E test dependencies, runs mocha tests against staging deployment. Uses environment variables from deploy stage. |
| 15 | `pipeline/package.json` | CDK pipeline dependencies: aws-cdk-lib ^2.189.1, constructs ^10.4.2, TypeScript ^5.7.3. Confirms CDK v2 usage. |
| 16 | `pipeline/bin/pipeline.ts` | CDK app entry point: instantiates PipelineStack. Minimal file confirming CDK app structure. |
| 17 | `pipeline/cdk.json` | CDK configuration: uses ts-node for TypeScript compilation, enables new-style stack synthesis. |
| 18 | `events/env.json` | Local development environment variables for SAM local invoke. Maps TABLE env var to "books" for both functions. |
| 19 | `events/create-book-request.json` | Sample API Gateway event for local testing. Confirms book schema in request body: isbn, title, year, author, publisher, rating, pages. |
| 20 | `README.md` | Comprehensive documentation covering architecture, local development, testing, CI/CD, and authentication flow. Confirms X-Ray tracing, DynamoDB usage, and OAuth2 implicit grant pattern. |
