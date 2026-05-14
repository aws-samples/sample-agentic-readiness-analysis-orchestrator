# Modernization Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | books-api |
| **Date** | 2026-04-17 |
| **Repo Type** | application |
| **Priority** | P1 |
| **Tags** | serverless, cdk, api, dynamodb |
| **Context** | Serverless REST API with CDK infrastructure for book catalog management. Clean API surface the agent can use as a tool for product lookups. |
| **Overall Score** | **2.71 / 4.0** |

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 2.82 / 4.0 | 🟡 Partial |
| Application Architecture (APP) | 2.83 / 4.0 | 🟡 Partial |
| Data Platform Modernization (DATA) | 2.75 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 2.71 / 4.0 | 🟡 Partial |
| Operations & Observability (OPS) | 2.44 / 4.0 | 🟠 Needs Work |
| **Overall** | **2.71 / 4.0** | **🟡 Partial** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q3: Workflow Orchestration | 1 | No workflow orchestration service — all logic hardcoded in Lambda functions | Limits ability to manage complex multi-step business processes; increases debugging difficulty for orchestrated workflows |
| 2 | INF-Q4: Async Messaging and Streaming | 1 | No async messaging (SQS, SNS, EventBridge) — all communication is synchronous HTTP | Tight coupling between API consumers and backend; no event-driven patterns for decoupled processing |
| 3 | APP-Q5: API Versioning Strategy | 1 | No API versioning — no /v1/ paths, no version headers, no versioning strategy | Breaking changes will affect all consumers simultaneously; blocks safe API evolution |
| 4 | SEC-Q7: Application Security Pipeline | 1 | No SAST, dependency scanning, or security gates in CI/CD pipeline | Vulnerabilities in dependencies (aws-sdk, aws-xray-sdk-core) or code reach production undetected |
| 5 | OPS-Q3: Business Metrics | 1 | No custom business metrics — only default Lambda error alarms | Cannot measure business outcomes (books created, catalog queries); modernization decisions lack data |

---

## Quick Agent Wins

### Data Query Agent

- **Prerequisite:** DATA-Q2 = 2 (≥ 2). DynamoDB table `BooksTable` with direct SDK access provides queryable structured data (isbn, title, year, author, publisher, rating, pages).
- **What it enables:** A natural-language-to-DynamoDB agent that can look up books by ISBN, search by author or title, and return structured JSON responses. Useful for product lookups as described in the repository context.
- **Additional steps:** Create an OpenAPI specification for the existing GET /books and POST /books endpoints to enable full tool discovery. Consider adding a GET /books/{isbn} endpoint for single-item lookup to improve agent efficiency (currently only scan is available).
- **Effort:** Medium

### DevOps Agent

- **Prerequisite:** INF-Q11 = 3 (≥ 2). Full CI/CD pipeline exists in CDK (`pipeline/lib/pipeline-stack.ts`) with CodePipeline stages: Source → Build → Staging (Deploy + Test) → Production (Manual Approval + Deploy).
- **What it enables:** An agent that can trigger pipeline executions, check build status, monitor deployment progress through CodeDeploy traffic shifting, and report on e2e test results — all via AWS CodePipeline and CodeBuild APIs.
- **Additional steps:** Expose pipeline status via a lightweight API or use AWS SDK directly. Consider adding pipeline event notifications via EventBridge to enable proactive agent monitoring.
- **Effort:** Low

### RAG-based Knowledge Agent

- **Prerequisite:** Comprehensive documentation exists. `README.md` (300+ lines) covers architecture, project structure, deployment instructions, local testing, monitoring, tracing, CI/CD pipeline, and OAuth token management. Additional docs: `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`.
- **What it enables:** A knowledge agent powered by Amazon Bedrock that indexes the README, code comments, and inline documentation to answer developer questions about the Books API — deployment procedures, architecture decisions, testing approaches, and troubleshooting.
- **Additional steps:** Index README.md and source code comments into a vector store (Amazon Bedrock Knowledge Bases with OpenSearch Serverless). Add JSDoc/TSDoc comments to Lambda functions for richer context.
- **Effort:** Medium

### Observability Agent

- **Prerequisite:** OPS-Q1 = 4 (≥ 2). X-Ray distributed tracing is fully instrumented: `Tracing: Active` on all Lambda functions, `TracingEnabled: true` on API Gateway, `aws-xray-sdk-core` wrapping all AWS SDK calls with `AWSXRay.captureAWS(AWSCore)`.
- **What it enables:** An agent that queries X-Ray traces to identify slow DynamoDB operations, correlates API Gateway latency with Lambda cold starts, and surfaces error patterns from CloudWatch Logs. Can proactively alert on performance degradation.
- **Additional steps:** Add structured logging (JSON format) to Lambda functions to improve log queryability. Current error handling catches exceptions silently — add contextual error logging for richer agent analysis.
- **Effort:** Low

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 3 — application already uses serverless micro-function pattern (Lambda + API Gateway + DynamoDB) |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1 = 4 — all compute is Lambda (serverless). Contextual guard: compute is already serverless, not EC2/VM-based |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 — no stored procedures. DynamoDB is not a commercial licensed engine |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 = 4 — DynamoDB is fully managed with automated scaling, backup capabilities, and no operational overhead |
| 5 | Move to Managed Analytics | Not Triggered | — | — | Contextual guard prevents trigger: no data processing workloads, ETL pipelines, or streaming infrastructure detected. This is a CRUD API with no analytics responsibilities |
| 6 | Move to Modern DevOps | Not Triggered | — | — | INF-Q10 = 4, INF-Q11 = 3 — both primary triggers ≥ 3. IaC coverage is comprehensive and CI/CD pipeline is automated |
| 7 | Move to AI | Triggered | Medium | Medium | No AI/agent framework imports detected. Context contains AI signal term "agent" ("Clean API surface the agent can use as a tool for product lookups") |

---

### Pathway: Move to AI

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

#### Current AI/Agent Infrastructure State

No AI or agent framework artifacts were detected in the repository:

- **AI/Agent Frameworks:** No imports of Amazon Bedrock SDK, LangChain, Strands, OpenAI, Spring AI, HuggingFace, or SageMaker SDK in any source file. Dependencies are limited to `aws-sdk`, `aws-xray-sdk-core`, and test libraries.
- **Vector Database:** No OpenSearch, Pinecone, pgvector, Weaviate, or Qdrant configuration found. The only data store is DynamoDB (`BooksTable`).
- **RAG Implementation:** No embedding generation, vector store queries, or retrieval chain patterns detected.
- **Agent Evaluation:** No Ragas, DeepEval, or custom evaluation frameworks found.

#### Contextual Guard Evidence

The analysis context explicitly mentions AI/agent intent: *"Clean API surface the agent can use as a tool for product lookups."* The term **"agent"** is an AI-related signal term, confirming that AI integration is a stated goal for this service.

#### Application Domain and AI Use Cases

The Books API is a catalog management service with structured data (isbn, title, year, author, publisher, rating, pages) exposed via REST endpoints. This presents several AI integration opportunities:

1. **Product Lookup Agent Tool:** The existing GET /books endpoint returns structured JSON — ideal as an agent tool for catalog queries. An Amazon Bedrock agent could invoke this endpoint to answer natural language questions about the book catalog.
2. **Smart Catalog Enrichment:** Use Amazon Bedrock foundation models to auto-generate book summaries, category tags, or reading-level analyses from book metadata.
3. **Conversational Book Search:** Build a conversational interface using Amazon Bedrock that translates natural language queries ("Find science fiction books published after 2020") into DynamoDB queries.

#### Recommended AI Services

Aligned with user preferences (`prefer: ["bedrock"]`):

- **Amazon Bedrock** — Foundation model access for natural language understanding and generation. Use Bedrock Agents to expose the Books API as agent tools.
- **Amazon Bedrock Knowledge Bases** — Index the README documentation and API response schemas for RAG-based developer assistance.
- **Amazon Bedrock AgentCore** — Managed infrastructure for deploying and scaling agents that interact with the Books API.

#### Foundation Requirements

Before AI integration, the following foundations should be in place:

1. **OpenAPI Specification** — Generate a formal OpenAPI spec for the Books API endpoints. This enables Bedrock Agents to discover and invoke API tools automatically. Currently no OpenAPI spec exists (APP-Q5 = 1).
2. **GET /books/{isbn} Endpoint** — Add a single-item lookup endpoint. The current API only supports full table scan (GET /books) and create (POST /books). Single-item lookup is essential for efficient agent tool invocation.
3. **Input Validation** — Add request body validation on the POST /books endpoint. Currently the Lambda function parses the body without validation, returning 500 on malformed input. Agents need predictable error responses.
4. **Structured Error Responses** — Return JSON error bodies with error codes and messages instead of empty bodies on 500 errors. This enables agents to understand and recover from failures.

#### AWS Prescriptive Guidance

- [Amazon Bedrock Agents Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)
- [Build AI Agents with Amazon Bedrock](https://aws.amazon.com/bedrock/agents/)
- [Amazon Bedrock Knowledge Bases](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html)

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | 100% of compute workloads use AWS Lambda (serverless). Three Lambda functions are defined in `template.yml`: `GetAllBooks`, `CreateBook`, and `CreateBookPreTraffic`. All use `nodejs22.x` runtime with `MemorySize: 512` and `Timeout: 5`. No EC2 instances, ECS tasks, or EKS pods are defined anywhere in the repository. Build operations use managed CodeBuild (`LinuxBuildImage.STANDARD_7_0`). |
| **Gap** | No gaps. All compute is fully managed serverless. |
| **Recommendation** | Maintain current serverless-first approach. If workload complexity grows and longer-running compute is needed, consider AWS Fargate tasks or EKS (preferred per user preferences) rather than EC2. |
| **Evidence** | `template.yml` (GetAllBooks, CreateBook, CreateBookPreTraffic resources); `pipeline/lib/pipeline-stack.ts` (PipelineProject with LinuxBuildImage.STANDARD_7_0) |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | The sole database is `BooksTable`, an `AWS::Serverless::SimpleTable` (DynamoDB) defined in `template.yml`. DynamoDB is a fully managed, serverless NoSQL database with automatic scaling, built-in replication across multiple AZs, and zero operational overhead. SSE is enabled (`SSESpecification.SSEEnabled: true`). Primary key is `isbn` (String). |
| **Gap** | No gaps. Database is fully managed with encryption at rest enabled. |
| **Recommendation** | DynamoDB is well-aligned with the serverless architecture and user preferences (`prefer: ["dynamodb"]`). For future growth, consider DynamoDB Global Tables for multi-region resilience if the API serves a global audience. |
| **Evidence** | `template.yml` (BooksTable: AWS::Serverless::SimpleTable with SSESpecification) |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No workflow orchestration service is used. No Step Functions, Temporal, Camunda, or other workflow definitions found. The `CreateBookPreTraffic` Lambda performs a smoke test sequence (invoke → getItem → wait → deleteItem) with all orchestration logic hardcoded in the function. The API itself is simple CRUD without multi-step business workflows. |
| **Gap** | No dedicated workflow orchestration for any operations. All sequenced logic is hardcoded in Lambda functions. |
| **Recommendation** | For current scope (simple CRUD), the absence of workflow orchestration is acceptable. As the API evolves to support complex operations (e.g., book ordering, inventory management, multi-step catalog workflows), adopt AWS Step Functions to orchestrate Lambda functions. Consider EventBridge (preferred per user preferences) for event-driven workflow triggers. |
| **Evidence** | `template.yml` (no `AWS::StepFunctions::*` resources); `src/books/create-pre-traffic/index.ts` (hardcoded orchestration logic) |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No messaging or streaming infrastructure is present. No SQS queues, SNS topics, EventBridge rules, Kinesis streams, or MSK clusters are defined. All communication follows the synchronous pattern: API Gateway → Lambda → DynamoDB → HTTP response. No event-driven patterns detected in any source file. |
| **Gap** | All communication is synchronous HTTP with no async patterns. No event-driven architecture capability. |
| **Recommendation** | Introduce Amazon EventBridge (preferred per user preferences) to publish domain events when books are created (e.g., `BookCreated` event). This enables downstream consumers (notifications, analytics, search indexing) without coupling them to the API. Avoid self-managed Kafka or RabbitMQ (per user preferences). |
| **Evidence** | `template.yml` (no SQS, SNS, EventBridge, Kinesis resources); `src/books/create/index.ts` (synchronous putItem with no event publishing); `src/books/get-all/index.ts` (synchronous scan) |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Lambda functions are not deployed in a VPC — no `VpcConfig` is present on any function in `template.yml`. API Gateway (`BooksApi`) is publicly accessible with Cognito auth on the POST endpoint. The GET /books endpoint is public with no authentication. No VPC, subnet, security group, or NACL resources are defined. The API relies on Cognito authorization and IAM policies rather than network-level controls. |
| **Gap** | No VPC deployment for Lambda functions. No network segmentation. GET endpoint is publicly accessible without authentication. |
| **Recommendation** | For a serverless API accessing only DynamoDB (which supports VPC endpoints), VPC deployment is not strictly required but adds defense-in-depth. Consider: (1) Add a DynamoDB VPC endpoint if Lambda functions are placed in a VPC in the future. (2) Add WAF rules on the API Gateway for rate limiting and IP filtering. (3) Evaluate whether the GET /books endpoint should require authentication. |
| **Evidence** | `template.yml` (no VpcConfig on Lambda functions; BooksApi with no WAF; GET /books with no Auth block) |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Amazon API Gateway (`AWS::Serverless::Api`) is the single entry point for all traffic. Configuration includes: Cognito authorization (`CognitoAuth` authorizer with `UserPoolArn`), CloudWatch logging (`LoggingLevel: INFO` on all resources/methods), X-Ray tracing (`TracingEnabled: true`), and stage variables for Lambda alias routing. OAuth2 scopes (`email`) are enforced on the POST endpoint. |
| **Gap** | No explicit throttling configuration on the API Gateway. Default API Gateway throttling limits apply but are not explicitly tuned. No request validation defined. |
| **Recommendation** | Add explicit throttling settings (`ThrottlingBurstLimit`, `ThrottlingRateLimit`) on the API Gateway stage to protect against traffic spikes. Add request body validation using API Gateway request models to reject malformed requests before they reach Lambda. This aligns with the API Gateway preference (`prefer: ["api-gateway"]`). |
| **Evidence** | `template.yml` (BooksApi: AWS::Serverless::Api with Auth.Authorizers.CognitoAuth, MethodSettings with LoggingLevel: INFO, TracingEnabled: true) |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Lambda functions auto-scale automatically with AWS-managed concurrency. No explicit `ReservedConcurrentExecutions` or `ProvisionedConcurrencyConfig` is set. DynamoDB `SimpleTable` uses on-demand capacity mode by default (no provisioned throughput specified), which auto-scales transparently. API Gateway scales automatically. |
| **Gap** | No explicit concurrency limits on Lambda functions to protect downstream resources (DynamoDB). No provisioned concurrency configuration for consistent cold-start performance. |
| **Recommendation** | Add `ReservedConcurrentExecutions` to Lambda functions to prevent runaway scaling from impacting DynamoDB or account-level Lambda concurrency limits. Consider `ProvisionedConcurrencyConfig` on the production alias for latency-sensitive endpoints to minimize cold starts. |
| **Evidence** | `template.yml` (Lambda functions without ReservedConcurrentExecutions; BooksTable as SimpleTable with no ProvisionedThroughput — defaults to on-demand) |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration is present. The DynamoDB `BooksTable` is defined as `AWS::Serverless::SimpleTable` which does not configure Point-in-Time Recovery (PITR) or on-demand backups. No `AWS::Backup::BackupPlan` resources exist. No S3 versioning for artifact buckets. The CDK pipeline S3 buckets (`CiCdPipelineArtifacts`, `ApiArtifacts`) have `removalPolicy: DESTROY` and no versioning. |
| **Gap** | No PITR on DynamoDB table. No backup plan. No restore procedures documented. Data loss from accidental deletion or application bugs would be unrecoverable. |
| **Recommendation** | Enable DynamoDB Point-in-Time Recovery (PITR) on the `BooksTable` — this is a single property addition: `PointInTimeRecoverySpecification.PointInTimeRecoveryEnabled: true`. Consider migrating from `SimpleTable` to `AWS::DynamoDB::Table` for full control over backup settings. Add an `AWS::Backup::BackupPlan` for automated backup scheduling. |
| **Evidence** | `template.yml` (BooksTable: AWS::Serverless::SimpleTable with no PITR config); `pipeline/lib/pipeline-stack.ts` (S3 buckets with removalPolicy: DESTROY, no versioning) |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | All services are inherently multi-AZ: Lambda functions execute across multiple AZs automatically. DynamoDB replicates data across multiple AZs within the region by default. API Gateway is a regional, multi-AZ managed service. No single-AZ bottleneck exists in the architecture. |
| **Gap** | No gaps. The serverless architecture provides built-in multi-AZ availability without explicit configuration. |
| **Recommendation** | Maintain current architecture. For disaster recovery across regions, consider DynamoDB Global Tables and a multi-region API Gateway deployment pattern if the service becomes business-critical. |
| **Evidence** | `template.yml` (Lambda, DynamoDB, API Gateway — all inherently multi-AZ AWS managed services) |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | 100% of infrastructure is defined in code. `template.yml` (SAM/CloudFormation) defines all application resources: 3 Lambda functions, DynamoDB table, API Gateway, Cognito User Pool + Client + Domain, IAM roles, CloudWatch Alarms. `pipeline/lib/pipeline-stack.ts` (CDK) defines the CI/CD pipeline: CodePipeline, 3 CodeBuild projects, S3 artifact buckets, IAM policies, and stage configurations. No evidence of manually created (ClickOps) resources. |
| **Gap** | No gaps in IaC coverage. Note: user preferences include `prefer: ["terraform"]`, but current IaC (SAM + CDK) is comprehensive and well-structured. Migration to Terraform would be an optional preference alignment, not a gap. |
| **Recommendation** | Maintain current SAM + CDK approach. If standardizing on Terraform across the organization (per preferences), consider migrating IaC to Terraform with the AWS provider — but this is a preference, not a maturity gap. Consider adopting a GitOps workflow (preferred per user preferences) for infrastructure changes. |
| **Evidence** | `template.yml` (all application resources); `pipeline/lib/pipeline-stack.ts` (all pipeline resources); `pipeline/cdk.json` (CDK configuration) |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Full CI/CD pipeline is defined in CDK with 4 stages: Source (GitHub via CodeStar Connection) → Build (SAM build + unit tests) → Staging (SAM deploy + e2e tests) → Production (manual approval + SAM deploy). Unit tests run in `pre_build` phase of `buildspec.json`. E2e tests run via `buildspec-test.json` against the staging environment. Production deployment uses CodeDeploy with `Linear10PercentEvery1Minute` traffic shifting and CloudWatch alarm-based rollback. |
| **Gap** | Manual approval gate before production deployment (not fully automated). No automated rollback testing. No security scanning stage. Build stage installs `esbuild` globally each time (`npm i -g recursive-install esbuild`) rather than using a cached build image. |
| **Recommendation** | Consider replacing the manual approval gate with automated quality gates (canary metrics, e2e test pass rate) to enable continuous deployment. Add a security scanning stage with `npm audit` or Snyk (see SEC-Q7). Cache build dependencies to reduce build times. Align with GitOps practices (preferred per user preferences) by triggering pipeline from git events only. Avoid manual deployment processes (per user preferences: avoid `manual-deployments`). |
| **Evidence** | `pipeline/lib/pipeline-stack.ts` (Pipeline with 4 stages, ManualApprovalAction); `pipeline/buildspec.json` (pre_build: npm test); `pipeline/buildspec-test.json` (e2e test execution); `pipeline/buildspec-deploy.json` (sam deploy); `template.yml` (DeploymentPreference: Linear10PercentEvery1Minute) |

---

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | All application code is written in TypeScript, running on Node.js 22.x (`Runtime: nodejs22.x`). TypeScript provides type safety, excellent IDE support, and a mature cloud-native ecosystem. Lambda functions use ESBuild for transpilation and bundling (`BuildMethod: esbuild`, `Target: es2020`, `Format: cjs`). E2e tests are written in JavaScript. CDK pipeline is also TypeScript. |
| **Gap** | No gaps. TypeScript on Node.js 22.x is one of the most mature ecosystems for serverless development. |
| **Recommendation** | Maintain TypeScript. Consider upgrading from `aws-sdk` v2 to `@aws-sdk/client-dynamodb` v3 (modular AWS SDK) for smaller bundle sizes and modern API patterns. The current `aws-sdk` v2 (`^2.1692.0`) is a full SDK bundle. |
| **Evidence** | `template.yml` (Runtime: nodejs22.x); `src/books/create/index.ts`, `src/books/get-all/index.ts` (TypeScript source); `src/books/create/package.json` (aws-sdk ^2.1692.0, typescript ^5.7.3); `pipeline/package.json` (typescript ^5.7.3) |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The application follows a serverless micro-function pattern with well-defined boundaries. Two business functions (`CreateBook`, `GetAllBooks`) have separate code directories (`src/books/create/`, `src/books/get-all/`), independent `package.json` files, and independent deployment configurations (separate CodeDeploy preferences and alarms). A third function (`CreateBookPreTraffic`) handles deployment smoke testing. They share a single DynamoDB table (`BooksTable`) which is appropriate for this bounded context. |
| **Gap** | Functions share a DynamoDB table with direct SDK access — no data ownership boundary between functions. The `CreateBook` function writes to the same table that `GetAllBooks` reads. For the current scope (single resource CRUD), this coupling is acceptable, but it would become a problem if the API grows significantly. |
| **Recommendation** | Maintain current function-per-endpoint pattern. If the API grows beyond basic CRUD, consider decomposing into separate services with dedicated data stores per the single-table design pattern. Introduce a shared data access layer to abstract DynamoDB interactions (see DATA-Q2). |
| **Evidence** | `template.yml` (separate Lambda functions: GetAllBooks, CreateBook, CreateBookPreTraffic with independent configs); `src/books/create/package.json`, `src/books/get-all/package.json` (separate dependency manifests) |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | All communication is synchronous HTTP. The flow is: Client → API Gateway (HTTP) → Lambda (synchronous invoke) → DynamoDB (synchronous SDK call) → HTTP response. No asynchronous messaging patterns (SQS, SNS, EventBridge), no event publishing, no background job processing. The pre-traffic hook uses synchronous Lambda invoke + DynamoDB operations. |
| **Gap** | 100% synchronous communication with no async patterns. No event publishing when books are created. No ability for downstream systems to react to catalog changes without polling the API. |
| **Recommendation** | Introduce Amazon EventBridge (preferred per user preferences) to publish `BookCreated` events after successful DynamoDB writes. This enables decoupled consumers (e.g., search indexing, notifications, analytics) without modifying the API contract. Pattern: Lambda → DynamoDB putItem → EventBridge putEvents. Avoid self-managed Kafka (per user preferences). |
| **Evidence** | `src/books/create/index.ts` (synchronous putItem with no event publishing); `src/books/get-all/index.ts` (synchronous scan); `template.yml` (no SQS/SNS/EventBridge resources) |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | All operations are short-lived CRUD operations completing well within the 5-second Lambda timeout. `CreateBook` performs a single DynamoDB putItem. `GetAllBooks` performs a single DynamoDB scan. The pre-traffic hook has a 1.5-second wait but completes within Lambda limits. No long-running processes exist that require async handling. |
| **Gap** | No gaps. All operations are appropriately short-lived for the serverless pattern. |
| **Recommendation** | Maintain current approach. If future operations require longer processing (e.g., bulk import, image processing, catalog enrichment), implement them as async jobs using SQS + Lambda or Step Functions rather than extending Lambda timeouts. |
| **Evidence** | `template.yml` (Timeout: 5 seconds for all functions); `src/books/create/index.ts` (single putItem); `src/books/get-all/index.ts` (single scan); `src/books/create-pre-traffic/index.ts` (wait of 1500ms) |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API versioning strategy is implemented. Endpoints are `/books` (GET) and `/books` (POST) with no version prefix. The `OpenApiVersion: 3.0.1` in the Globals section is used to avoid default stage creation in API Gateway, not for API versioning. No version headers (`Accept-Version`, `X-API-Version`) are used. No changelog or versioning documentation exists. |
| **Gap** | No versioning strategy. Any breaking change to the API contract (request/response schema) will affect all consumers simultaneously with no migration path. |
| **Recommendation** | Implement URL-based API versioning: `/v1/books` (GET, POST). Add an API Gateway stage variable or base path mapping for version routing. Create an OpenAPI specification to document the API contract and enable version management. This is also a prerequisite for the Move to AI pathway (Bedrock Agents require OpenAPI specs for tool discovery). |
| **Evidence** | `template.yml` (API paths: /books with no version prefix; OpenApiVersion: 3.0.1 used for stage behavior, not versioning) |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Lambda functions use environment variables for service endpoints: `TABLE` env var references the DynamoDB table name (injected via `!Ref BooksTable`). `FN_NEW_VERSION` env var references the Lambda function version for pre-traffic testing. API Gateway serves as the single entry point — no direct Lambda-to-Lambda invocation from the business functions. No hard-coded service endpoints in business logic. |
| **Gap** | Environment variables provide static configuration injection but not dynamic service discovery. The local development override (`if (process.env.AWS_SAM_LOCAL)`) hard-codes `http://dynamodb:8000` for the local DynamoDB endpoint. |
| **Recommendation** | Current approach is appropriate for the serverless pattern — environment variables injected via CloudFormation references are the standard pattern for Lambda service configuration. If the API grows to multiple services, consider API Gateway as a service catalog or AWS Cloud Map for dynamic discovery. |
| **Evidence** | `template.yml` (Environment.Variables.TABLE: !Ref BooksTable); `src/books/create/index.ts` (process.env.TABLE); `src/books/get-all/index.ts` (process.env.TABLE); `src/books/create-pre-traffic/index.ts` (process.env.TABLE, process.env.FN_NEW_VERSION) |

---

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No unstructured data handling capability exists. The API stores only structured book records (isbn, title, year, author, publisher, rating, pages) in DynamoDB. No S3 buckets for document/image storage. No Textract, Tika, or document parsing libraries. No image processing for book covers. No PDF or file upload capability. |
| **Gap** | No capability to store or process unstructured data (book covers, PDF excerpts, review documents). If the catalog needs to support rich media or document content, there is no foundation. |
| **Recommendation** | If unstructured data (book covers, excerpts, reviews) is a future requirement, add an S3 bucket for object storage with a Lambda-triggered processing pipeline. For AI-powered document understanding (e.g., extracting metadata from uploaded book PDFs), consider Amazon Textract integrated with Amazon Bedrock. |
| **Evidence** | `template.yml` (no S3 bucket resources for data); `src/books/create/index.ts` (structured fields only: isbn, title, year, author, publisher, rating, pages) |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | DynamoDB access is direct and duplicated across Lambda functions. Each function creates its own `AWS.DynamoDB` client with identical configuration (`apiVersion: '2012-08-10'`). `CreateBook` (`src/books/create/index.ts`) uses `client.putItem()`. `GetAllBooks` (`src/books/get-all/index.ts`) uses `client.scan()`. `CreateBookPreTraffic` (`src/books/create-pre-traffic/index.ts`) uses `getItem()` and `deleteItem()`. The e2e test helper (`src/books/tests/books-manager.js`) implements its own data access with `batchWriteItem()` and `getItem()`. No shared repository/DAO layer, no data access abstraction. |
| **Gap** | Data access logic is scattered across 4 files with no shared abstraction. The DynamoDB client configuration (apiVersion, X-Ray wrapping, local endpoint override) is duplicated in `create/index.ts` and `get-all/index.ts`. No consistent error handling pattern across data operations. |
| **Recommendation** | Extract a shared `BooksRepository` module that encapsulates all DynamoDB operations (get, getAll, create, delete). This centralizes client configuration, X-Ray instrumentation, error handling, and data marshalling. It also simplifies testing and provides a single point of change for data access patterns. |
| **Evidence** | `src/books/create/index.ts` (new AWS.DynamoDB, putItem); `src/books/get-all/index.ts` (new AWS.DynamoDB, scan); `src/books/create-pre-traffic/index.ts` (new DynamoDB, getItem, deleteItem); `src/books/tests/books-manager.js` (new AWS.DynamoDB, batchWriteItem, getItem) |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | DynamoDB is a fully managed, serverless database service with no user-managed engine version. AWS manages all engine updates, patches, and lifecycle transparently. There is no concept of EOL for DynamoDB — it is a continuously evolving service. No other database engines are used in the repository. |
| **Gap** | No gaps. DynamoDB has no engine version management concern. |
| **Recommendation** | Maintain DynamoDB. No engine version management needed. |
| **Evidence** | `template.yml` (BooksTable: AWS::Serverless::SimpleTable — DynamoDB with no engine version parameter) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or SQL of any kind. DynamoDB does not support stored procedures — all business logic resides in Lambda function application code. No `.sql` files found in the repository. No ORM configurations. Data operations use the raw DynamoDB SDK API (`putItem`, `scan`, `getItem`, `deleteItem`, `batchWriteItem`). |
| **Gap** | No gaps. All business logic is in the application layer with no database coupling. |
| **Recommendation** | Maintain current approach. Application-layer business logic in Lambda functions is the correct pattern for DynamoDB and enables maximum portability. |
| **Evidence** | `src/books/create/index.ts` (putItem); `src/books/get-all/index.ts` (scan); No `.sql` files in repository |

---

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | API Gateway access logging is enabled (`LoggingLevel: INFO` on all resources and methods in `template.yml`). CloudWatch Logs capture Lambda function execution logs. However, no CloudTrail resource is defined in the IaC templates. No CloudTrail log file validation or immutable storage (S3 Object Lock) is configured. CloudTrail may be enabled at the account level, but this repository's IaC does not provision or configure it. |
| **Gap** | No CloudTrail configuration in IaC. API-level logging exists but AWS API-level audit logging (who created/modified/deleted resources) is not provisioned by this stack. No log file validation. No immutable log storage. |
| **Recommendation** | Add CloudTrail configuration to the IaC, or verify it is provisioned at the organization/account level. Enable CloudTrail log file validation and configure an S3 bucket with Object Lock for immutable log storage. Add CloudWatch Log retention policies to Lambda log groups to control log storage costs. |
| **Evidence** | `template.yml` (BooksApi: MethodSettings with LoggingLevel: INFO); No `AWS::CloudTrail::Trail` resource in template.yml or pipeline-stack.ts |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | AWS-managed encryption is enabled on data stores. DynamoDB `BooksTable` has `SSESpecification.SSEEnabled: true` (uses AWS-owned key by default). CDK pipeline S3 buckets use `BucketEncryption.S3_MANAGED`. No customer-managed KMS keys (`aws_kms_key`) are defined anywhere. Lambda environment variables are encrypted at rest by default using AWS-managed keys. |
| **Gap** | No customer-managed KMS keys. All encryption uses AWS-managed or AWS-owned keys, which limits control over key rotation policies, access policies, and audit trails for key usage. |
| **Recommendation** | For enhanced security posture, create customer-managed KMS keys for DynamoDB SSE (`SSEType: KMS` with explicit `KMSMasterKeyId`). This provides key rotation control, CloudTrail audit of key usage, and granular key access policies. Use the same KMS key for S3 bucket encryption in the pipeline. |
| **Evidence** | `template.yml` (BooksTable: SSESpecification.SSEEnabled: true); `pipeline/lib/pipeline-stack.ts` (BucketEncryption.S3_MANAGED on pipelineArtifactBucket and apiArtifactBucket) |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Cognito authorizer is configured on the POST /books endpoint with OAuth2 scopes (`email`; `aws.cognito.signin.user.admin` added in non-production). The GET /books endpoint is intentionally public — no authentication required to read the book catalog. The Cognito authorizer (`CognitoAuth`) references the `CognitoUserPool` ARN. The UserPoolClient supports OAuth implicit grant flow. |
| **Gap** | GET /books endpoint is public (no authentication). While this is a design choice for a public catalog, it means the endpoint lacks attribution and rate limiting per user. OAuth implicit flow is used, which is deprecated in OAuth 2.1 in favor of PKCE-based authorization code flow. |
| **Recommendation** | Consider requiring authentication on GET /books if user attribution is needed. Migrate from OAuth implicit flow to authorization code flow with PKCE for improved security (implicit flow exposes tokens in URLs). Add API Gateway throttling per API key or Cognito identity to prevent abuse of the public endpoint. |
| **Evidence** | `template.yml` (CreateBook: Auth.AuthorizationScopes: [email]; GetAllBooks: no Auth block; CognitoAuth authorizer; UserPoolClient: AllowedOAuthFlows: [implicit]) |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Amazon Cognito User Pool is the identity provider, defined in `template.yml`. Resources include: `CognitoUserPool` (email-based registration, password policy), `UserPoolClient` (OAuth implicit flow, refresh token auth), and `UserPoolDomain` (hosted UI domain). SSO is provided through the Cognito hosted UI. The User Pool supports email as the username attribute. |
| **Gap** | Cognito is configured but limited: OAuth implicit flow (deprecated), simple password policy (MinimumLength: 6, no uppercase, no symbols), and no MFA configuration. No federation with external IdPs (Google, SAML, OIDC). The setup is Cognito-native without enterprise IdP integration. |
| **Recommendation** | Strengthen the Cognito configuration: enable MFA (`MfaConfiguration: ON`), enforce stronger password policies, migrate to authorization code flow with PKCE, and add external IdP federation if enterprise SSO is needed. Consider Cognito Advanced Security for adaptive authentication. |
| **Evidence** | `template.yml` (CognitoUserPool, UserPoolClient, UserPoolDomain; PasswordPolicy: MinimumLength: 6, RequireLowercase: false) |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No hardcoded secrets, API keys, or credentials in any source file. DynamoDB access uses IAM role-based authentication (SAM policies: `DynamoDBReadPolicy`, `DynamoDBWritePolicy`, `DynamoDBCrudPolicy`). Cognito integration is IAM-based. Environment variables contain only the table name (`TABLE`) and Lambda version ARN (`FN_NEW_VERSION`) — neither are secrets. Pipeline GitHub connection uses SSM Parameter Store (`github_connection_arn`). No `.env` files committed. |
| **Gap** | No gaps for current scope. No Secrets Manager usage, but none is needed — all authentication is IAM-based with no external credentials. |
| **Recommendation** | Maintain current IAM-based authentication pattern. If external service integrations are added in the future (third-party APIs, external databases), use AWS Secrets Manager with automated rotation rather than environment variables. |
| **Evidence** | `src/books/create/index.ts` (no hardcoded credentials; TABLE from env var); `src/books/get-all/index.ts` (same); `template.yml` (IAM policies for DynamoDB access); `pipeline/lib/pipeline-stack.ts` (StringParameter for github_connection_arn) |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Lambda runtime (`nodejs22.x`) is managed and patched by AWS automatically. No EC2 instances requiring manual patching. CodeBuild uses `LinuxBuildImage.STANDARD_7_0` (AWS-managed). No vulnerability scanning tools (AWS Inspector, Snyk, Trivy) are configured. The Lambda functions use `aws-sdk` v2 (`^2.1692.0`) which is maintained but approaching end-of-support — v3 is the current generation. |
| **Gap** | No vulnerability scanning for Lambda dependencies. `aws-sdk` v2 is maintained but should be migrated to v3. No container image scanning (not applicable — no containers). |
| **Recommendation** | Add dependency vulnerability scanning to the CI/CD pipeline (see SEC-Q7). Migrate from `aws-sdk` v2 to `@aws-sdk/client-dynamodb` v3 for modular imports and long-term support. Enable Lambda runtime deprecation notifications. |
| **Evidence** | `template.yml` (Runtime: nodejs22.x — current and supported); `src/books/create/package.json` (aws-sdk: ^2.1692.0); `pipeline/lib/pipeline-stack.ts` (LinuxBuildImage.STANDARD_7_0) |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No security scanning tools are integrated into the CI/CD pipeline. The `buildspec.json` runs `npm test` (unit tests) but no `npm audit`, no SAST (SonarQube, Semgrep, CodeGuru), no dependency scanning (Snyk, Dependabot), and no container scanning. No `.snyk` policy file. No Dependabot configuration (`.github/dependabot.yml`). No security gates that block deployment on critical vulnerabilities. |
| **Gap** | Zero security scanning in the CI/CD pipeline. Vulnerable dependencies and code-level security issues reach production undetected. Given that `aws-sdk` v2 and `axios` are in the dependency tree, vulnerability monitoring is important. |
| **Recommendation** | Add `npm audit --production` to the `pre_build` phase of `buildspec.json` to catch known vulnerabilities before deployment. Integrate a SAST tool (Amazon CodeGuru Reviewer, Semgrep, or SonarQube) into the build stage. Add Dependabot or Snyk for automated dependency vulnerability alerting. Configure security gates that fail the build on critical/high vulnerabilities. |
| **Evidence** | `pipeline/buildspec.json` (pre_build: npm test only, no npm audit or security scanning); No `.snyk`, `.github/dependabot.yml`, or security tool configuration files in repository |

---

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | End-to-end X-Ray distributed tracing is fully instrumented. All Lambda functions have `Tracing: Active` set in the `Globals.Function` section of `template.yml`. API Gateway has `TracingEnabled: true`. Both Lambda source files (`create/index.ts`, `get-all/index.ts`) import `aws-xray-sdk-core` and wrap the AWS SDK with `AWSXRay.captureAWS(AWSCore)`, ensuring all downstream DynamoDB calls are traced. Trace IDs propagate from API Gateway → Lambda → DynamoDB. X-Ray SDK is a runtime dependency (`aws-xray-sdk-core: ^3.10.3`). |
| **Gap** | No gaps. Tracing covers the full request path from API Gateway through Lambda to DynamoDB. |
| **Recommendation** | Maintain current tracing setup. Consider adding custom X-Ray subsegments for business logic sections within Lambda functions to provide finer-grained performance visibility. When migrating to AWS SDK v3, use `@aws-sdk/client-xray` or OpenTelemetry for tracing. |
| **Evidence** | `template.yml` (Globals.Function.Tracing: Active; BooksApi.TracingEnabled: true); `src/books/create/index.ts` (import * as AWSXRay from 'aws-xray-sdk-core'; AWSXRay.captureAWS); `src/books/get-all/index.ts` (same); `src/books/create/package.json` (aws-xray-sdk-core: ^3.10.3) |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | CloudWatch Alarms exist for Lambda function errors (`CreateBookAliasErrorMetricGreaterThanZeroAlarm`, `GetAllBooksAliasErrorMetricGreaterThanZeroAlarm`) with threshold `Errors > 0`. These alarms are used for deployment rollback but not as SLO monitors. No formal SLO definitions (availability targets, latency percentile targets, error budget calculations) exist. No p99/p95 latency alarms. No SLO dashboard. |
| **Gap** | No formal SLO definitions. Error alarms exist but are not framed as SLOs with error budgets. No latency targets. No availability targets documented. |
| **Recommendation** | Define SLOs for critical user journeys: e.g., GET /books availability ≥ 99.9%, GET /books p99 latency < 500ms, POST /books availability ≥ 99.9%. Add CloudWatch alarms on API Gateway latency (p99, p95) and 4xx/5xx error rates. Implement error budget tracking to inform deployment velocity decisions. |
| **Evidence** | `template.yml` (CreateBookAliasErrorMetricGreaterThanZeroAlarm, GetAllBooksAliasErrorMetricGreaterThanZeroAlarm — Errors > 0, no latency alarms, no SLO definitions) |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metrics are published. The only metrics are default AWS/Lambda namespace metrics (invocations, errors, duration) used by the CloudWatch Alarms. No `cloudwatch.putMetricData()` calls in any Lambda function. No business KPI tracking (books created per day, catalog size, popular authors, API usage by consumer). |
| **Gap** | Zero business metrics. Cannot measure business outcomes or track catalog health. Modernization and product decisions lack data. |
| **Recommendation** | Add custom CloudWatch metrics for key business events: `BooksCreated` (count), `CatalogSize` (gauge), `ApiUsageByEndpoint` (count by path). Publish metrics from Lambda functions using `cloudwatch.putMetricData()` or use CloudWatch Embedded Metric Format (EMF) for zero-latency metric publishing. Create a CloudWatch dashboard for business KPIs. |
| **Evidence** | `src/books/create/index.ts` (no metric publishing); `src/books/get-all/index.ts` (no metric publishing); `template.yml` (alarms use AWS/Lambda namespace only) |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Static threshold CloudWatch Alarms exist: `CreateBookAliasErrorMetricGreaterThanZeroAlarm` and `GetAllBooksAliasErrorMetricGreaterThanZeroAlarm` both alert when Lambda Errors > 0 (EvaluationPeriods: 2, Period: 60 seconds). No anomaly detection band configured. No latency alarms. No composite alarms. No PagerDuty/OpsGenie integration defined in IaC. |
| **Gap** | Only static error alarms. No anomaly detection for latency degradation or unusual error patterns. No latency-based alerting. No alarm notification targets (SNS topics, incident management). |
| **Recommendation** | Add CloudWatch Anomaly Detection on API Gateway latency and Lambda duration metrics to catch gradual performance degradation. Add latency alarms (p99 > threshold). Configure alarm actions with SNS topics for notification routing. Consider composite alarms that combine error rate + latency signals. |
| **Evidence** | `template.yml` (two Alarm resources: Errors > 0, static thresholds, no AlarmActions, no anomaly detection configuration) |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Production deployment uses `Linear10PercentEvery1Minute` traffic shifting via AWS CodeDeploy (defined in `DeploymentPreference` on each Lambda function). This shifts 10% of traffic to the new version every minute over 10 minutes. Pre-traffic hooks validate the new version before any traffic shift (`CreateBookPreTraffic` performs a smoke test: invoke → getItem → validate → deleteItem). CloudWatch error alarms trigger automatic rollback if the new version produces errors. Staging uses `AllAtOnce` for faster iteration. |
| **Gap** | No gaps. The deployment strategy is mature with linear traffic shifting, pre-traffic validation, and alarm-based automatic rollback. |
| **Recommendation** | Maintain current deployment strategy. Consider adding post-traffic hooks for additional validation after full traffic shift. Evaluate canary deployment (e.g., `Canary10Percent5Minutes`) as an alternative for faster initial validation with smaller blast radius. |
| **Evidence** | `template.yml` (DeploymentPreference.Type: Linear10PercentEvery1Minute for production; Hooks.PreTraffic: CreateBookPreTraffic; Alarms for rollback); `src/books/create-pre-traffic/index.ts` (smoke test implementation) |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Two levels of testing are implemented: (1) **Unit tests** — mocha/chai/sinon with `aws-sdk-mock` for both `CreateBook` (3 test cases) and `GetAllBooks` (3 test cases), run in `pre_build` of `buildspec.json`. (2) **End-to-end tests** — mocha/chai/axios tests in `src/books/tests/` that run against the deployed staging environment via `buildspec-test.json`. E2e tests create Cognito users, obtain OAuth tokens, and test both GET and POST endpoints with real DynamoDB data. |
| **Gap** | E2e tests run only against staging, not production. No contract tests. No load tests. The pre-traffic hook provides a basic smoke test in production but not full integration test coverage. |
| **Recommendation** | Add contract tests for the API schema to catch breaking changes. Consider running a subset of e2e tests against production after deployment (synthetic monitoring). Add performance/load testing to the pipeline to validate scaling behavior before production. |
| **Evidence** | `src/books/create/tests/index.spec.ts` (3 unit tests); `src/books/get-all/tests/index.spec.ts` (3 unit tests); `src/books/tests/index.js` (5 e2e tests); `pipeline/buildspec.json` (pre_build: npm test); `pipeline/buildspec-test.json` (e2e test execution) |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | CodeDeploy provides automatic rollback when CloudWatch error alarms fire during deployment — this is a form of self-healing during deployments. No runbooks (markdown, YAML, SSM Automation documents) exist. No Lambda-based remediation. No Step Functions for incident workflows. No documented incident response procedures. |
| **Gap** | No runbooks. No incident response procedures beyond deployment rollback. No self-healing for runtime issues (e.g., DynamoDB throttling, Cognito service degradation). |
| **Recommendation** | Create SSM Automation runbooks for common incidents: DynamoDB throttling (increase on-demand capacity), Lambda throttling (request concurrency increase), API Gateway 5xx spike (check Lambda errors + DynamoDB health). Document incident escalation procedures. Consider EventBridge rules (preferred per user preferences) that trigger automated remediation Lambda functions. |
| **Evidence** | `template.yml` (DeploymentPreference with Alarms for automatic rollback); No runbook files, no SSM Automation documents, no incident response documentation in repository |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | CloudWatch Alarms exist for Lambda errors but have no named owners, no notification targets (`AlarmActions` not configured), and no team attribution. Resource tags include `project: my-project` and `environment: {Stage}` but no `team` or `owner` tags. No CODEOWNERS file for observability configuration. No per-service CloudWatch dashboards defined in IaC. No SLO definitions with team ownership. |
| **Gap** | No observability ownership. Alarms exist but nobody is assigned to respond. No dashboards for service health visibility. No team attribution on monitoring resources. |
| **Recommendation** | Add `AlarmActions` to CloudWatch Alarms pointing to an SNS topic for the responsible team. Add `owner` and `team` tags to all resources. Create a CloudWatch dashboard in the SAM template with widgets for API Gateway metrics (request count, latency, errors), Lambda metrics (invocations, errors, duration, concurrent executions), and DynamoDB metrics (read/write capacity, throttles). Add a CODEOWNERS file with team ownership for observability configs. |
| **Evidence** | `template.yml` (Alarms without AlarmActions; Tags: project, environment — no team/owner); No CODEOWNERS file; No CloudWatch Dashboard resources |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Tags are applied but inconsistently and with limited scope. `Globals.Function` applies `project: my-project` and `environment: {Stage}` to all Lambda functions. `BooksTable` has the same two tags applied explicitly. `CreateBookPreTraffic` has tags applied explicitly (same values). CDK pipeline S3 buckets and CodeBuild projects do not have explicit tags. No `owner`, `team`, `cost-center`, or `service` tags. No tag enforcement (AWS Config rules, SCPs, Organization tag policies). |
| **Gap** | Limited tag set (only `project` and `environment`). No cost allocation tags. No ownership tags. Pipeline resources are untagged. No tag enforcement policies. |
| **Recommendation** | Expand the tag set to include: `owner`, `team`, `cost-center`, `service: books-api`. Apply tags to all resources including CDK pipeline resources. Add `default_tags` equivalent in CDK (using `Tags.of(app).add()`). Consider AWS Config rules (`required-tags`) or Organization tag policies for enforcement. Activate cost allocation tags in the AWS Billing console. |
| **Evidence** | `template.yml` (Globals.Function.Tags: project, environment; BooksTable.Tags: project, environment); `pipeline/lib/pipeline-stack.ts` (no tags on S3 buckets, CodeBuild projects, or Pipeline) |

---

## Learning Materials

### Move to AI

- [Move to AI — AWS SkillBuilder Learning Plan](https://skillbuilder.aws/learning-plan/VDFEE4ACCV)
- [Amazon Bedrock Getting Started](https://skillbuilder.aws/learn/63KTRM86DQ)
- [Introduction to Agentic AI on AWS](https://skillbuilder.aws/learn/DNBD5MT8ZD)
- [Amazon Bedrock Agents Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)
- [Amazon Bedrock Knowledge Bases](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html)

---

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `template.yml` | INF-Q1, INF-Q2, INF-Q3, INF-Q4, INF-Q5, INF-Q6, INF-Q7, INF-Q8, INF-Q9, INF-Q10, INF-Q11, APP-Q1, APP-Q2, APP-Q3, APP-Q4, APP-Q5, APP-Q6, DATA-Q1, DATA-Q2, DATA-Q3, DATA-Q4, SEC-Q1, SEC-Q2, SEC-Q3, SEC-Q4, SEC-Q5, SEC-Q6, OPS-Q1, OPS-Q2, OPS-Q4, OPS-Q5, OPS-Q6, OPS-Q8, OPS-Q9 | SAM/CloudFormation template defining all application infrastructure: Lambda functions, DynamoDB table, API Gateway, Cognito, CloudWatch Alarms, deployment preferences |
| `pipeline/lib/pipeline-stack.ts` | INF-Q8, INF-Q10, INF-Q11, SEC-Q2, SEC-Q5 | CDK stack defining CI/CD pipeline: CodePipeline stages, CodeBuild projects, S3 artifact buckets, IAM policies |
| `pipeline/buildspec.json` | INF-Q11, SEC-Q7, OPS-Q6 | Build specification: SAM build, unit test execution, packaging — no security scanning |
| `pipeline/buildspec-deploy.json` | INF-Q11 | Deploy specification: SAM deploy with stack outputs for environment variables |
| `pipeline/buildspec-test.json` | INF-Q11, OPS-Q6 | Test specification: e2e test execution against staging environment |
| `src/books/create/index.ts` | APP-Q1, APP-Q2, APP-Q3, APP-Q4, DATA-Q1, DATA-Q2, SEC-Q5, OPS-Q1, OPS-Q3 | CreateBook Lambda: DynamoDB putItem, X-Ray instrumentation, synchronous flow |
| `src/books/get-all/index.ts` | APP-Q1, APP-Q2, APP-Q3, APP-Q4, DATA-Q2, SEC-Q5, OPS-Q1, OPS-Q3 | GetAllBooks Lambda: DynamoDB scan, X-Ray instrumentation, JSON response |
| `src/books/create-pre-traffic/index.ts` | INF-Q3, APP-Q6, DATA-Q2, OPS-Q5 | Pre-traffic hook: smoke test via Lambda invoke + DynamoDB validation |
| `src/books/create/package.json` | APP-Q1, SEC-Q6, OPS-Q1 | Dependencies: aws-sdk v2, aws-xray-sdk-core, test libraries (mocha, chai, sinon) |
| `src/books/get-all/package.json` | APP-Q1 | Dependencies: aws-sdk v2, aws-xray-sdk-core, test libraries |
| `src/books/create/tests/index.spec.ts` | OPS-Q6 | Unit tests for CreateBook: 3 test cases with aws-sdk-mock |
| `src/books/get-all/tests/index.spec.ts` | OPS-Q6 | Unit tests for GetAllBooks: 3 test cases with aws-sdk-mock |
| `src/books/tests/index.js` | OPS-Q6 | E2e tests: 5 test cases against live staging API with Cognito auth |
| `src/books/tests/books-manager.js` | DATA-Q2 | Test helper: DynamoDB operations for test data management |
| `src/books/tests/package.json` | OPS-Q6 | E2e test dependencies: axios, aws-sdk, uuid, mocha, chai |
| `pipeline/package.json` | INF-Q10 | CDK pipeline dependencies: aws-cdk-lib, constructs |
| `pipeline/cdk.json` | INF-Q10 | CDK app configuration |
| `pipeline/bin/pipeline.ts` | INF-Q10 | CDK app entry point |
| `README.md` | Quick Agent Wins (RAG) | Comprehensive documentation: architecture, deployment, testing, CI/CD, tracing |
| `events/create-book-request.json` | APP-Q4 | Sample API Gateway POST event for local testing |
| `events/get-all-books-request.json` | APP-Q4 | Sample API Gateway GET event for local testing |
| `events/env.json` | APP-Q6 | Local environment variable configuration |
