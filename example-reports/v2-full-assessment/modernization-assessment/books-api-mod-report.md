# Modernization Readiness Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | books-api |
| **Date** | 2026-04-15 |
| **Repo Type** | application |
| **Priority** | P1 |
| **Tags** | serverless, cdk, api, dynamodb |
| **Context** | Serverless REST API with CDK infrastructure for book catalog management. Clean API surface the agent can use as a tool for product lookups. |
| **Preferences** | Prefer: eks, aurora, dynamodb, api-gateway, eventbridge, bedrock, terraform, gitops · Avoid: self-managed-kafka, self-managed-kubernetes, oracle, manual-deployments |
| **Overall Score** | **2.64 / 4.0** |

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 3.00 / 4.0 | 🟡 Partial |
| Application Architecture (APP) | 2.50 / 4.0 | 🟡 Partial |
| Data Platform Modernization (DATA) | 2.75 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 2.86 / 4.0 | 🟡 Partial |
| Operations & Observability (OPS) | 2.11 / 4.0 | 🟠 Needs Work |
| **Overall** | **2.64 / 4.0** | **🟡 Partial** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | INF-Q3: Workflow Orchestration | 1 | No workflow orchestration service — all orchestration logic hardcoded in Lambda handlers | Cannot manage multi-step business workflows with visibility, retry logic, or error handling at scale |
| 2 | INF-Q4: Async Messaging and Streaming | 1 | No messaging or streaming infrastructure — all communication is synchronous HTTP | Tight coupling between API consumers and backend; no event-driven patterns; limited resilience to downstream failures |
| 3 | APP-Q3: Async vs Sync Communication | 1 | 100% synchronous HTTP communication through API Gateway → Lambda → DynamoDB | Cascading failure risk; no decoupling between producers and consumers; blocking calls for all operations |
| 4 | APP-Q5: API Versioning Strategy | 1 | No API versioning — endpoint is /books with no version prefix, headers, or strategy | Breaking changes affect all consumers simultaneously; no backward compatibility guarantees for agent or third-party integrations |
| 5 | SEC-Q7: Application Security Pipeline | 1 | No SAST, DAST, or dependency vulnerability scanning in CI/CD pipeline | Dependency vulnerabilities and code security issues reach production undetected; critical gap for a P1 service |

> **Additional score-1 gaps:** OPS-Q2 (SLO Definitions), OPS-Q3 (Business Metrics), OPS-Q7 (Incident Response), OPS-Q8 (Observability Ownership), DATA-Q1 (Unstructured Data Storage).

---

## Quick Agent Wins

### Data Query Agent

- **Prerequisite:** DATA-Q2 ≥ 2 (scored 2). DynamoDB `BooksTable` has a clear, well-defined schema: `isbn` (String, PK), `title`, `year`, `author`, `publisher`, `rating`, `pages`. Schema visible in `src/books/create/index.ts` PutItemInput.
- **What it enables:** A natural language to DynamoDB query agent powered by Amazon Bedrock that translates questions like "Find all books by author X with rating above 4" into DynamoDB queries against the books table.
- **Additional steps:** Generate formal data model documentation. The current raw DynamoDB API (low-level `putItem`/`scan`) would benefit from a query translation layer. Consider adding a Global Secondary Index (GSI) on `author` or `rating` to support richer queries beyond full-table scans.
- **Effort:** Medium

### DevOps Agent

- **Prerequisite:** INF-Q11 ≥ 2 (scored 3). Full CI/CD pipeline exists: Source → Build → Staging (Deploy + E2E Test) → Production (Manual Approval + Deploy). Pipeline defined in CDK (`pipeline/lib/pipeline-stack.ts`).
- **What it enables:** A DevOps agent that can trigger deployments, check build status, approve or reject manual approval gates, and report on pipeline health via the CodePipeline API.
- **Additional steps:** Add Pipeline notification rules (SNS topics) for agent consumption. Expose pipeline state via EventBridge events for real-time agent monitoring. Consider adding a chatbot integration (e.g., AWS Chatbot to Slack) that the agent can interact with.
- **Effort:** Low

### RAG-Based Knowledge Agent

- **Prerequisite:** README.md exists with comprehensive documentation covering architecture, deployment, local testing, monitoring, tracing, CI/CD setup, and token management (220+ lines of structured content).
- **What it enables:** A RAG-based knowledge agent powered by Amazon Bedrock that indexes the repository documentation and answers developer questions about the architecture, deployment procedures, API usage, and troubleshooting.
- **Additional steps:** Index `README.md` and `template.yml` as the initial knowledge base. Consider adding Architecture Decision Records (ADRs) and runbooks for richer context. An Amazon Bedrock Knowledge Base with S3 data source would be the recommended implementation.
- **Effort:** Low

### Observability Agent

- **Prerequisite:** OPS-Q1 ≥ 2 (scored 3). X-Ray Active tracing instrumented on all Lambda functions and API Gateway. Application code uses `aws-xray-sdk-core` to capture AWS SDK calls (`AWSXRay.captureAWS(AWSCore)`).
- **What it enables:** An observability agent that queries X-Ray traces and CloudWatch logs to identify performance bottlenecks, trace request flows, correlate errors across Lambda invocations, and suggest root causes for failures.
- **Additional steps:** Add structured logging (currently basic `console.log` in pre-traffic hook). Configure CloudWatch Logs Insights saved queries for agent consumption. Consider adding custom X-Ray annotations (e.g., `isbn`, `operation`) to enable agent-driven trace filtering.
- **Effort:** Medium

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 3 (≥ 3). Application already uses cloud-native serverless patterns (Lambda, API Gateway, DynamoDB). |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1 = 4. Compute is 100% Lambda/serverless. Contextual guard: compute is already Lambda/Fargate, not EC2/VM-based. |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4. No stored procedures or proprietary SQL. No commercial database engines (DynamoDB is AWS-native). |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 = 4. Database is already fully managed DynamoDB with SSE. |
| 5 | Move to Managed Analytics | Not Triggered | — | — | Contextual guard: No data processing workloads exist. Application is a CRUD API with no analytics, streaming, or ETL. |
| 6 | Move to Modern DevOps | Not Triggered | — | — | INF-Q10 = 4, INF-Q11 = 3. Both primary conditions ≥ 3. Full IaC coverage and automated CI/CD pipeline in place. |
| 7 | Move to AI | **Triggered** | Medium | Medium | No AI/agent frameworks detected. No Bedrock SDK, LangChain, Strands, OpenAI, vector DB, RAG, or eval frameworks in source code. |

---

### Pathway: Move to AI

**Status:** Triggered  
**Priority:** Medium  
**Estimated Effort:** Medium

#### Current AI/Agent Infrastructure State

The repository has **zero AI/agent infrastructure**:

- **AI/Agent Frameworks:** No imports of Amazon Bedrock SDK, LangChain, Strands Agents SDK, OpenAI SDK, Spring AI, HuggingFace, or SageMaker SDK found in any source file or dependency manifest.
- **Vector Database:** No OpenSearch with vector engine, Pinecone, pgvector, Weaviate, or Qdrant infrastructure detected.
- **RAG Implementation:** No embedding generation, vector store queries, retrieval chains, or document chunking logic found.
- **Agent Evaluation:** No Ragas, DeepEval, or custom evaluation harness detected.

#### Application Domain and AI Use Cases

The Books API is a catalog management service with a clean REST interface (GET /books, POST /books) and structured data in DynamoDB. This domain is well-suited for several AI integration opportunities:

1. **Natural Language Book Search** — An Amazon Bedrock-powered agent that translates natural language queries ("Find sci-fi books published after 2020 with high ratings") into DynamoDB queries against the `BooksTable`.
2. **Book Recommendations** — A Bedrock foundation model that generates personalized book recommendations based on catalog data (author, genre, rating patterns).
3. **AI-Powered Book Cataloging** — Use Amazon Bedrock to auto-generate book descriptions, categorize books by genre, or extract metadata from book covers (with Amazon Textract + Bedrock).
4. **Agent Tool Interface** — The existing REST API (GET /books, POST /books) can serve as a tool interface for an AI agent. An agent built with Amazon Bedrock AgentCore or Strands Agents SDK could invoke these endpoints as tools for product lookups and catalog management.

#### Quick Wins for AI Integration

See the [Quick Agent Wins](#quick-agent-wins) section above for 4 identified opportunities that can be pursued with the current architecture.

#### Recommended AI Services

Given the preference for **Amazon Bedrock**:

- **Amazon Bedrock** — Foundation model access for natural language understanding, book recommendations, and agent reasoning
- **Amazon Bedrock AgentCore** — Managed agent runtime for building agents that use the Books API as a tool
- **Amazon Bedrock Knowledge Bases** — RAG implementation using repository documentation and book catalog data
- **Amazon OpenSearch Service (vector engine)** — Vector search for semantic book discovery (similarity-based recommendations)
- **Amazon Q Developer** — AI-powered development assistance for the team

#### Foundation Requirements Before AI Integration

1. **API Versioning (APP-Q5)** — Add API versioning (e.g., `/v1/books`) before exposing the API as an agent tool. This ensures agent integrations don't break when the API evolves.
2. **OpenAPI Specification** — Generate a standalone OpenAPI spec from the SAM template. Agents need machine-readable API descriptions for tool discovery.
3. **Structured Logging** — Enhance logging beyond basic `console.log` to support observability of AI agent interactions.
4. **Data Model Documentation** — Document the DynamoDB schema formally to support data query agent development.

#### Learning Resources

- [Move to AI Learning Plan](https://skillbuilder.aws/learning-plan/VDFEE4ACCV)
- [Amazon Bedrock Getting Started](https://skillbuilder.aws/learn/63KTRM86DQ)
- [Introduction to Agentic AI on AWS](https://skillbuilder.aws/learn/DNBD5MT8ZD)

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | 100% of compute is AWS Lambda (serverless). Three Lambda functions defined: `GetAllBooks`, `CreateBook`, and `CreateBookPreTraffic`, all running `nodejs22.x` runtime. No EC2 instances, no ECS tasks, no EKS pods. Compute is fully managed by AWS with no operational overhead for patching, scaling, or capacity planning. |
| **Gap** | None — compute is fully managed serverless. |
| **Recommendation** | No action needed. Current serverless architecture is optimal for this workload. |
| **Evidence** | `template.yml` — `AWS::Serverless::Function` resources: GetAllBooks, CreateBook, CreateBookPreTraffic. Runtime: nodejs22.x. |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | DynamoDB (`AWS::Serverless::SimpleTable`) is the sole data store. Fully managed with server-side encryption (SSE) enabled. On-demand capacity mode (no provisioned throughput specified). Primary key: `isbn` (String). No self-managed databases detected. |
| **Gap** | None — database is fully managed DynamoDB. |
| **Recommendation** | No action needed. DynamoDB is well-suited for this key-value access pattern. Consider enabling DynamoDB Point-in-Time Recovery (PITR) for backup protection (see INF-Q8). |
| **Evidence** | `template.yml` — `BooksTable` resource with `SSESpecification.SSEEnabled: true`. |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No workflow orchestration service detected. No Step Functions, Temporal, Camunda, or other orchestration tools. All logic is implemented directly in Lambda function handlers. The pre-traffic hook (`CreateBookPreTraffic`) contains a sequential workflow (invoke Lambda → wait → verify DynamoDB → cleanup) that would benefit from Step Functions orchestration. |
| **Gap** | No dedicated workflow orchestration. If the API grows to include multi-step workflows (e.g., book ordering, inventory management, publisher notifications), orchestration logic will be hardcoded in Lambda functions without visibility, retry semantics, or state management. |
| **Recommendation** | For the current simple CRUD API, this is acceptable. As the application evolves, consider AWS Step Functions for multi-step operations. The pre-traffic validation hook is a natural candidate for a Step Functions Express Workflow. Aligns with preference for EventBridge for event-driven patterns. |
| **Evidence** | No `AWS::StepFunctions::*` or `aws_sfn_*` resources in `template.yml`. No Temporal SDK imports in source code. |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No messaging or streaming infrastructure. No SQS queues, SNS topics, EventBridge rules, Kinesis streams, or MSK clusters. All communication flows through synchronous HTTP: API Gateway → Lambda → DynamoDB. No event-driven patterns detected. |
| **Gap** | No async communication layer. The system cannot emit domain events (e.g., "book created") for downstream consumers. Adding features like notifications, search indexing, or analytics requires synchronous coupling. |
| **Recommendation** | Add Amazon EventBridge (preferred) to emit domain events on book creation. This enables decoupled downstream processing (search indexing, notifications, analytics) without modifying the core Lambda handlers. Start with a `BookCreated` event on the POST /books path. Avoid self-managed Kafka per preferences. |
| **Evidence** | No `AWS::SQS::*`, `AWS::SNS::*`, `AWS::Events::*`, `AWS::Kinesis::*` in `template.yml`. No SQS/SNS SDK imports in source code. |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | API Gateway provides the managed network entry point with Cognito OAuth2 authentication on the POST /books endpoint. Lambda functions run in the AWS-managed VPC by default, providing implicit network isolation. No explicit VPC, security groups, or NACLs are defined — this is standard for public-facing serverless APIs. GET /books is intentionally public (no auth). |
| **Gap** | No explicit VPC configuration. While acceptable for the current serverless architecture, if the API needs to access private resources (e.g., RDS in a VPC, internal services), a VPC configuration with private subnets would be required. The GET /books endpoint lacks rate limiting beyond API Gateway defaults. |
| **Recommendation** | For the current serverless-only architecture, the implicit network isolation is sufficient. If private resource access is needed in the future, configure Lambda VPC access with private subnets. Consider adding WAF on API Gateway for additional protection (rate limiting, IP filtering, SQL injection protection). |
| **Evidence** | `template.yml` — `BooksApi` with `CognitoAuth` authorizer on POST. No `AWS::EC2::VPC`, `AWS::EC2::Subnet`, or `AWS::EC2::SecurityGroup` resources. |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Amazon API Gateway (`AWS::Serverless::Api`) serves as the managed entry point. Configured with: stage-based logging at INFO level for all methods, X-Ray tracing enabled, Cognito authorizer for write operations. API Gateway provides built-in DDoS protection, SSL termination, and request routing. |
| **Gap** | No explicit throttling configuration (API Gateway defaults apply). No request validation defined (e.g., request body schema validation via API Gateway models). No explicit CORS configuration. Missing WAF integration. |
| **Recommendation** | Add explicit throttling settings on the API Gateway stage (rate limit + burst limit). Enable API Gateway request validation using models to validate request bodies before they reach Lambda. Add WAF rules for defense-in-depth. Consider adding a CloudFront distribution in front of API Gateway for caching GET /books responses and edge-level protection. |
| **Evidence** | `template.yml` — `BooksApi` (AWS::Serverless::Api) with `MethodSettings`, `TracingEnabled: true`, `Auth.Authorizers.CognitoAuth`. |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Lambda auto-scales natively with concurrent execution management by AWS. No manual capacity provisioning needed. DynamoDB SimpleTable uses on-demand capacity mode by default (no `ProvisionedThroughput` specified), which auto-scales reads and writes. API Gateway scales automatically. All compute and data tiers handle variable load without configuration. |
| **Gap** | None — serverless architecture provides automatic scaling. |
| **Recommendation** | No action needed. Consider setting Lambda reserved concurrency limits if the API needs to protect downstream resources from throttling during traffic spikes. |
| **Evidence** | `template.yml` — Lambda functions (no ReservedConcurrentExecutions specified = unlimited scaling). BooksTable as SimpleTable (no ProvisionedThroughput = on-demand mode). |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | DynamoDB SSE is enabled, but Point-in-Time Recovery (PITR) is not explicitly enabled on the `BooksTable`. No `AWS::Backup::BackupPlan` resources found. No S3 data backup configuration. The SimpleTable resource type does not include `PointInTimeRecoverySpecification` property. |
| **Gap** | DynamoDB PITR not enabled — data loss risk in case of accidental deletion or corruption. No backup plan for the data store. No documented restore procedure. For a P1 service, this is a significant gap. |
| **Recommendation** | Enable DynamoDB PITR by migrating from `AWS::Serverless::SimpleTable` to `AWS::DynamoDB::Table` with `PointInTimeRecoverySpecification.PointInTimeRecoveryEnabled: true`. Alternatively, add an `AWS::Backup::BackupPlan` resource. Consider DynamoDB on-demand backups as a complementary strategy. |
| **Evidence** | `template.yml` — `BooksTable` has `SSESpecification.SSEEnabled: true` but no `PointInTimeRecoverySpecification`. No `AWS::Backup::*` resources. |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | All resources are AWS-managed serverless services that provide inherent multi-AZ availability: Lambda (runs across multiple AZs automatically), DynamoDB (data replicated across 3 AZs), API Gateway (regionally distributed), Cognito (regionally distributed). No single-AZ risk exists in this architecture. |
| **Gap** | None — serverless architecture provides inherent multi-AZ fault isolation. |
| **Recommendation** | No action needed. For disaster recovery across regions, consider DynamoDB Global Tables if multi-region resilience is needed for this P1 service. |
| **Evidence** | `template.yml` — All resources are managed services: `AWS::Serverless::Function` (Lambda), `AWS::Serverless::SimpleTable` (DynamoDB), `AWS::Serverless::Api` (API Gateway), `AWS::Cognito::UserPool`. |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | ~100% IaC coverage. Application infrastructure defined in `template.yml` (SAM/CloudFormation): Lambda functions, API Gateway, DynamoDB, Cognito User Pool, CloudWatch Alarms, IAM roles/policies, CodeDeploy preferences. CI/CD infrastructure defined in `pipeline/lib/pipeline-stack.ts` (CDK): CodePipeline, CodeBuild projects, S3 artifact buckets, IAM roles. |
| **Gap** | None — all infrastructure is defined as code. |
| **Recommendation** | No action needed. Current IaC coverage is comprehensive. Consider migrating from SAM to CDK for the application stack (aligning with the pipeline's CDK approach) for a unified IaC framework. If Terraform is preferred (per preferences), evaluate CDK for Terraform (CDKTF) as a migration path. |
| **Evidence** | `template.yml` (SAM/CloudFormation), `pipeline/lib/pipeline-stack.ts` (CDK), `pipeline/cdk.json`, `pipeline/bin/pipeline.ts`. |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Full CI/CD pipeline defined in CDK: Source (GitHub via CodeStar Connection) → Build (npm install, unit tests, sam build, sam package) → Staging (sam deploy + E2E tests) → Production (Manual Approval + sam deploy). Production deployments use `Linear10PercentEvery1Minute` traffic shifting with CloudWatch alarm-based rollback and pre-traffic hooks. |
| **Gap** | Manual approval gate before production deployment (intentional but reduces full automation). No automated rollback trigger beyond CodeDeploy alarm-based rollback. Build stage uses broad IAM policies (FullAccess managed policies) on deploy role. No GitOps pattern (per preferences). |
| **Recommendation** | The manual approval gate is appropriate for a P1 service. To move toward GitOps (preferred), consider adopting a GitOps workflow where merging to main triggers automated deployment through the existing pipeline without manual approval for staging, with promotion to production gated by automated health checks rather than manual review. Tighten IAM policies on the deploy CodeBuild role to least-privilege. |
| **Evidence** | `pipeline/lib/pipeline-stack.ts` — Pipeline stages: Source, Build, Staging, Production. `pipeline/buildspec.json` — Build with tests. `pipeline/buildspec-deploy.json` — Deploy with sam deploy. `pipeline/buildspec-test.json` — E2E tests. |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | TypeScript with Node.js 22.x runtime. Mature cloud-native ecosystem with excellent Lambda, serverless, and AWS SDK support. TypeScript provides static typing, rich IDE support, and a large package ecosystem. The application uses esbuild for bundling (modern, fast build tool). |
| **Gap** | None — TypeScript/Node.js is a top-tier choice for serverless development. |
| **Recommendation** | No action needed. Consider migrating from `aws-sdk` v2 to `@aws-sdk/client-dynamodb` v3 (modular SDK) for smaller bundle sizes and improved tree-shaking. |
| **Evidence** | `template.yml` — `Runtime: nodejs22.x`. `.ts` source files in `src/books/`. `package.json` files with TypeScript, esbuild dependencies. |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Well-structured serverless application with multiple independently deployable Lambda functions: `CreateBook` (POST /books), `GetAllBooks` (GET /books), `CreateBookPreTraffic` (pre-traffic validation). Each function has its own directory, `package.json`, and source code. Functions share a DynamoDB table (`BooksTable`) but access it independently with separate IAM policies (DynamoDBWritePolicy vs DynamoDBReadPolicy). |
| **Gap** | Functions share a single DynamoDB table. While appropriate for this bounded context (book catalog), this creates data-level coupling. Each function duplicates DynamoDB client initialization code. No shared library for common data access patterns. |
| **Recommendation** | Current structure is appropriate for the domain size. If the API grows beyond the book catalog (e.g., users, orders, reviews), consider separate DynamoDB tables per domain context. Extract common DynamoDB client initialization into a shared Lambda Layer to reduce code duplication. |
| **Evidence** | `src/books/create/`, `src/books/get-all/`, `src/books/create-pre-traffic/` — separate directories with independent `package.json`. `template.yml` — separate `AWS::Serverless::Function` resources with individual IAM policies. |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | 100% synchronous HTTP communication. The entire flow is: API Gateway HTTP request → Lambda function → DynamoDB API call → HTTP response. No asynchronous patterns, no event-driven communication, no message queues, no pub/sub topics. Even the pre-traffic hook uses synchronous Lambda invocation. |
| **Gap** | No async communication infrastructure. The API cannot emit domain events, process operations asynchronously, or decouple producers from consumers. All operations block until DynamoDB responds. |
| **Recommendation** | Add Amazon EventBridge (preferred) integration to the `CreateBook` Lambda function to emit `BookCreated` events after successful book creation. This enables downstream consumers (search indexing, notifications, analytics) without modifying the request/response flow. For future growth, consider DynamoDB Streams as an alternative event source that captures all table changes automatically. |
| **Evidence** | `src/books/create/index.ts` — synchronous `client.putItem(params).promise()`. `src/books/get-all/index.ts` — synchronous `client.scan(params).promise()`. No SQS/SNS/EventBridge SDK imports. |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Lambda functions have a 5-second timeout (configured in Globals), appropriate for the current operations (DynamoDB putItem and scan are fast). No long-running operations detected — book creation and retrieval complete well within the timeout. The pre-traffic hook has a 1.5-second `setTimeout` wait for DynamoDB consistency, which is handled appropriately within the Lambda execution. |
| **Gap** | No async job infrastructure for potential future long-running operations (e.g., bulk book imports, catalog synchronization, report generation). If the API scope grows, there's no pattern for handling operations over 30 seconds. |
| **Recommendation** | Current implementation is appropriate for the existing use case. If long-running operations are added, use Step Functions (preferred) or SQS + Lambda for async processing with status polling via a job status API endpoint. |
| **Evidence** | `template.yml` — `Globals.Function.Timeout: 5`. `src/books/create-pre-traffic/index.ts` — `wait(1500)` function for DynamoDB consistency. |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API versioning strategy. The API endpoint is `/books` with no version prefix (e.g., `/v1/books`). No `Accept-Version` headers configured. No API changelog or versioning documentation. The SAM template references `OpenApiVersion: 3.0.1` in Globals, but this is the OpenAPI specification version for SAM, not an API versioning strategy. |
| **Gap** | Breaking changes to the API schema (e.g., renaming fields, removing attributes, changing response format) would affect all consumers simultaneously with no migration path. This is a critical gap for agent integration — agents built against this API have no version guarantee. |
| **Recommendation** | Implement URL-based versioning (`/v1/books`) as the simplest approach for API Gateway. Add versioning to the API path in `template.yml`. Generate a standalone OpenAPI specification file for agent and consumer discovery. Add a CHANGELOG.md to document API changes. |
| **Evidence** | `template.yml` — API events: `Path: /books` (no version prefix). No `Accept-Version` header configuration. No CHANGELOG.md file. |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Environment variables are used for configuration injection: `TABLE` environment variable references the DynamoDB table name via CloudFormation `!Ref BooksTable`. Lambda functions resolve the table name at runtime from `process.env.TABLE`. The pre-traffic hook also receives `FN_NEW_VERSION` (Lambda function ARN) via environment variable. API Gateway is the sole entry point — no service-to-service communication requiring discovery. |
| **Gap** | No dynamic service discovery mechanism. While environment variables via CloudFormation are appropriate for the current architecture, this pattern does not scale to multi-service communication. If additional services are added, hard-coded environment variables become a maintenance burden. |
| **Recommendation** | Current approach is appropriate for a single-service API. If the architecture grows to multiple services, consider AWS Cloud Map for service discovery or API Gateway as a service registry. CloudFormation Outputs already export key values (ApiEndpoint, UserPoolId, etc.) which could be consumed by other stacks. |
| **Evidence** | `template.yml` — `Environment.Variables.TABLE: !Ref BooksTable` on Lambda functions. `src/books/create/index.ts` — `process.env.TABLE || 'books'`. CloudFormation Outputs section exports ApiEndpoint, UserPoolId, UserPoolClientId, BooksTable. |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No unstructured data storage detected. No S3 buckets defined for document or unstructured data storage in `template.yml`. S3 buckets exist only in the CDK pipeline stack for build artifacts. No Textract, document parsing libraries, or file processing capabilities. The application handles only structured book data (isbn, title, year, author, publisher, rating, pages) in DynamoDB. |
| **Gap** | No capability to store or process unstructured data (e.g., book cover images, PDF excerpts, review documents). If the book catalog needs to support rich media or document storage, there is no infrastructure for it. |
| **Recommendation** | Add an S3 bucket for book-related unstructured data (cover images, PDF samples, reviews). Consider Amazon Textract for extracting metadata from book documents. This also enables AI integration — Amazon Bedrock can process book descriptions and cover images for enhanced catalog features. |
| **Evidence** | `template.yml` — No `AWS::S3::Bucket` resources for data storage. `pipeline/lib/pipeline-stack.ts` — S3 buckets for pipeline artifacts only. No document processing libraries in any `package.json`. |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Database access is direct DynamoDB client calls in each Lambda function with no centralized data access layer. Each function creates its own DynamoDB client instance and makes direct API calls: `CreateBook` uses `putItem()`, `GetAllBooks` uses `scan()`, `CreateBookPreTraffic` uses `getItem()` and `deleteItem()`. The DynamoDB client initialization code (including X-Ray instrumentation and local development fallback) is duplicated across `create/index.ts` and `get-all/index.ts`. |
| **Gap** | No repository/DAO pattern. Data access logic is scattered across Lambda functions with duplicated client initialization. Schema mapping (DynamoDB attribute types to application objects) is inconsistent — `get-all/index.ts` maps DynamoDB items to DTOs while `create/index.ts` does not. Adding new data operations requires duplicating the client setup pattern. |
| **Recommendation** | Extract a shared `BooksRepository` module (or Lambda Layer) that centralizes DynamoDB client initialization, X-Ray instrumentation, and data access operations (create, getAll, getByIsbn, delete). This eliminates code duplication and provides a single point to enforce data contracts, add caching, or switch to DynamoDB Document Client. |
| **Evidence** | `src/books/create/index.ts` — `new AWS.DynamoDB(ddbOptions)` with `putItem()`. `src/books/get-all/index.ts` — `new AWS.DynamoDB(ddbOptions)` with `scan()`. `src/books/create-pre-traffic/index.ts` — `new DynamoDB()` with `getItem()` and `deleteItem()`. Duplicated X-Ray setup in create and get-all. |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | DynamoDB is a fully managed, versionless NoSQL service. There is no engine version to pin, no EOL lifecycle to track, and no version upgrade process. AWS manages all updates, patches, and feature rollouts transparently. The `AWS::Serverless::SimpleTable` resource type has no engine version parameter. |
| **Gap** | None — DynamoDB's managed lifecycle eliminates version and EOL concerns. |
| **Recommendation** | No action needed. DynamoDB's serverless nature means no version management overhead. |
| **Evidence** | `template.yml` — `BooksTable` (`AWS::Serverless::SimpleTable`) with no engine version parameter. DynamoDB documentation confirms no customer-managed engine versions. |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | No stored procedures, triggers, or proprietary SQL. All business logic resides in the application layer (TypeScript Lambda functions). DynamoDB is a NoSQL service that does not support stored procedures, triggers, or SQL. Data operations are simple key-value puts and scans using the DynamoDB API. No `.sql` migration files, no ORM configurations. |
| **Gap** | None — all business logic is in the application layer with no database coupling. |
| **Recommendation** | No action needed. This clean separation between application logic and data storage is a modernization strength. |
| **Evidence** | `src/books/create/index.ts` — business logic in Lambda handler. `src/books/get-all/index.ts` — data retrieval in Lambda handler. No `.sql` files in repository. No `CREATE PROCEDURE`, `CREATE TRIGGER`, or `CREATE FUNCTION` patterns. |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | API Gateway access logging is enabled at INFO level for all resources and methods (`MethodSettings` in `BooksApi`). CloudWatch logging role configured via `ApiGwAccountConfig` and `ApiGatewayLoggingRole`. However, no CloudTrail configuration exists in IaC — CloudTrail may be enabled at the account level but is not codified. No immutable log storage (S3 Object Lock). No CloudWatch log retention policies defined (logs retained indefinitely by default, creating cost risk). |
| **Gap** | No CloudTrail configuration in IaC. No immutable log storage for audit trails. No log retention policy. For a P1 service, audit logging should be explicitly codified in IaC to ensure it survives stack updates and account changes. |
| **Recommendation** | Add `AWS::CloudTrail::Trail` to the SAM template targeting API Gateway and Lambda events. Configure S3 bucket with Object Lock for immutable audit storage. Set CloudWatch Logs retention policies on Lambda log groups (e.g., 90 days for staging, 365 days for production). |
| **Evidence** | `template.yml` — `MethodSettings` with `LoggingLevel: INFO`. `ApiGwAccountConfig` with `CloudWatchRoleArn`. No `AWS::CloudTrail::Trail` resource. No `RetentionInDays` on log groups. |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | DynamoDB SSE is enabled using AWS-managed encryption (`SSESpecification.SSEEnabled: true`). S3 pipeline artifact buckets use `S3_MANAGED` encryption in the CDK stack. Lambda environment variables are encrypted by default with the AWS Lambda service key. All data stores have encryption enabled, but using AWS-managed keys rather than customer-managed KMS keys. |
| **Gap** | No customer-managed KMS keys. AWS-managed encryption provides baseline protection but does not give the organization control over key rotation policies, key access policies, or cross-account key sharing. Cannot enforce key-level access controls for granular data governance. |
| **Recommendation** | For a P1 service, create customer-managed KMS keys for DynamoDB and S3 encryption. This provides key rotation control, audit trails via CloudTrail, and the ability to revoke access by disabling keys. Update `BooksTable` to use `SSESpecification.SSEType: KMS` with a `KMSMasterKeyId`. |
| **Evidence** | `template.yml` — `BooksTable.SSESpecification.SSEEnabled: true` (AWS-managed). `pipeline/lib/pipeline-stack.ts` — `BucketEncryption.S3_MANAGED`. No `AWS::KMS::Key` resources in template. |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Cognito OAuth2/JWT authentication is configured on the POST /books endpoint via `CognitoAuth` authorizer with `AuthorizationScopes: [email]`. GET /books is intentionally public (no authentication) — this is a design choice for read-only catalog access. The Cognito User Pool supports email-based user registration with password policies. |
| **Gap** | GET /books is unauthenticated. While this is intentional for public catalog browsing, it means any consumer can access the full book catalog without identification. This limits the ability to enforce rate limiting per consumer, track API usage, or implement field-level access control. |
| **Recommendation** | Consider adding optional API key-based identification on GET /books (not for security, but for usage tracking and per-consumer rate limiting). This would enable usage plans and throttling per API key. For agent integration, API keys provide a lightweight mechanism to track which agents are consuming the API. |
| **Evidence** | `template.yml` — `CreateBook.Events.ApiEvent.Auth.Authorizer: CognitoAuth` with `AuthorizationScopes`. `GetAllBooks.Events.ApiEvent` — no `Auth` section. `CognitoUserPool` with password policy. |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Application integrates with Amazon Cognito User Pool as the centralized identity provider. OAuth2 implicit grant flow configured with `UserPoolClient`, `UserPoolDomain`, and callback URLs. OIDC scopes include `email` and `openid`. Staging environment additionally supports `USER_PASSWORD_AUTH` for programmatic testing. Production restricts to `ALLOW_REFRESH_TOKEN_AUTH` only. |
| **Gap** | None — Cognito is the centralized IdP with OAuth2/OIDC flows. |
| **Recommendation** | No action needed for identity integration. Consider migrating from OAuth2 implicit grant to authorization code flow with PKCE (recommended by OAuth 2.1 spec). The implicit grant is considered less secure as tokens are exposed in browser URLs. |
| **Evidence** | `template.yml` — `CognitoUserPool`, `UserPoolClient` (AllowedOAuthFlows: implicit, AllowedOAuthScopes: email, openid), `UserPoolDomain`. Conditional `ALLOW_USER_PASSWORD_AUTH` for staging. |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | GitHub connection ARN is stored in AWS Systems Manager Parameter Store (`StringParameter.fromStringParameterName` in CDK pipeline stack). DynamoDB table name is injected via CloudFormation references (`!Ref BooksTable`), not hardcoded. No hardcoded secrets found in source code. Cognito User Pool Client ID and API endpoint are exported as CloudFormation Outputs (not secrets, but configuration values). |
| **Gap** | No AWS Secrets Manager usage with automated rotation. SSM Parameter Store is used (appropriate for non-rotating configuration) but the application has no secrets that require rotation (DynamoDB uses IAM-based access, not credentials). If the application adds external integrations requiring API keys or database credentials, there is no established pattern for secrets with rotation. |
| **Recommendation** | Current approach is appropriate — Lambda uses IAM roles for DynamoDB access (no database credentials). If external service integrations are added (e.g., third-party APIs, Aurora databases), use AWS Secrets Manager with automated rotation. Avoid storing secrets in environment variables for any future integrations. |
| **Evidence** | `pipeline/lib/pipeline-stack.ts` — `StringParameter.fromStringParameterName(this, 'GithubConnectionArn', 'github_connection_arn')`. `template.yml` — `Environment.Variables.TABLE: !Ref BooksTable`. No hardcoded credentials in `src/` files. |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | All compute is AWS Lambda, which is fully managed by AWS. The execution environment (OS, runtime, security patches) is maintained by AWS. Runtime is `nodejs22.x` — a current, actively maintained Node.js LTS version. No EC2 instances, containers, or VMs to patch. Lambda functions use esbuild for bundling, producing minimal deployment packages. |
| **Gap** | None — Lambda's managed execution environment eliminates compute hardening and patching concerns. |
| **Recommendation** | No action needed. Monitor for Node.js runtime deprecation notifications from AWS and plan runtime upgrades accordingly. The current `nodejs22.x` runtime is well within its support lifecycle. |
| **Evidence** | `template.yml` — `Globals.Function.Runtime: nodejs22.x`. All compute is `AWS::Serverless::Function` (Lambda). No EC2 or container resources. |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SAST, DAST, or dependency vulnerability scanning in the CI/CD pipeline. The build stage (`pipeline/buildspec.json`) runs unit tests (`npm test`) and builds with SAM, but has no security scanning steps. No Dependabot configuration (`.github/dependabot.yml`). No Snyk policy (`.snyk`). No `npm audit` in buildspec. No SonarQube or CodeGuru Reviewer integration. No container scanning (not applicable since there are no containers). |
| **Gap** | Dependency vulnerabilities in `aws-sdk`, `aws-xray-sdk-core`, `axios`, and other npm packages reach production undetected. No code-level security analysis. The `aws-sdk` v2 dependency is on version `^2.1692.0` — a legacy SDK version that may have known vulnerabilities. For a P1 service, this is a critical gap. |
| **Recommendation** | Add `npm audit --audit-level=high` to the build phase in `pipeline/buildspec.json`. Add a Dependabot configuration (`.github/dependabot.yml`) for automated dependency update PRs. Integrate Amazon CodeGuru Reviewer or Semgrep into the CI pipeline for SAST. Consider adding `pip-audit` for the Python 3.8 dependency in the build environment. |
| **Evidence** | `pipeline/buildspec.json` — phases: install (sam-cli), pre_build (npm install, npm test), build (sam build), post_build (sam package). No security scanning commands. No `.github/dependabot.yml`. No `.snyk` file. |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | X-Ray tracing is enabled on all Lambda functions (`Tracing: Active` in Globals) and API Gateway (`TracingEnabled: true` on `BooksApi`). Application code uses `aws-xray-sdk-core` to capture all AWS SDK calls (`AWSXRay.captureAWS(AWSCore)`) in both `create/index.ts` and `get-all/index.ts`. Trace IDs propagate automatically from API Gateway through Lambda to DynamoDB. Local development correctly skips X-Ray instrumentation (conditional on `AWS_SAM_LOCAL`). |
| **Gap** | This is a single-service API, so cross-service trace propagation is not demonstrated. The pre-traffic hook (`create-pre-traffic/index.ts`) does NOT use `aws-xray-sdk-core` — X-Ray instrumentation is missing on this function. No custom X-Ray annotations or metadata for business-level trace filtering. |
| **Recommendation** | Add `aws-xray-sdk-core` to the pre-traffic hook for complete trace coverage. Add custom X-Ray annotations (e.g., `isbn`, `operation`) to enable filtering traces by business context. If additional services are added, ensure trace context propagation via `traceparent` or `X-Amzn-Trace-Id` headers. |
| **Evidence** | `template.yml` — `Globals.Function.Tracing: Active`, `BooksApi.TracingEnabled: true`. `src/books/create/index.ts` — `AWSXRay.captureAWS(AWSCore)`. `src/books/get-all/index.ts` — `AWSXRay.captureAWS(AWSCore)`. `src/books/create-pre-traffic/index.ts` — no X-Ray SDK import. |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No SLO definitions found in the repository. No error budget tracking. The CloudWatch alarms defined (`CreateBookAliasErrorMetricGreaterThanZeroAlarm`, `GetAllBooksAliasErrorMetricGreaterThanZeroAlarm`) monitor Lambda error count > 0 — these are operational deployment alarms for CodeDeploy rollback, not SLO-based availability or latency targets. No p99/p95 latency targets defined. |
| **Gap** | No formal definition of acceptable service levels. Cannot measure whether the API is meeting user expectations or degrading over time. Without SLOs, modernization investments cannot be prioritized based on user impact. For a P1 service, this is a significant operational maturity gap. |
| **Recommendation** | Define SLOs for the two API endpoints: availability (e.g., 99.9% success rate for GET /books, 99.5% for POST /books) and latency (e.g., p99 < 500ms for GET, p99 < 1000ms for POST). Implement CloudWatch metric math or CloudWatch Application Signals for SLO monitoring. Track error budgets monthly. |
| **Evidence** | `template.yml` — CloudWatch Alarms monitor `Errors > 0` only. No SLO definition files. No p99/p95 latency alarms. No error budget configuration. |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metrics published. Lambda functions (`create/index.ts`, `get-all/index.ts`) do not emit custom CloudWatch metrics. No `cloudwatch.putMetricData()` calls for business events (books created, books retrieved, book creation failures). Only default Lambda metrics (Invocations, Duration, Errors, Throttles) and API Gateway metrics (Count, Latency, 4xx, 5xx) are available. |
| **Gap** | Cannot measure business outcomes — no visibility into how many books are created per day, which API consumers are most active, or what error patterns affect the book catalog. Infrastructure metrics tell you the API is running, not whether it's delivering value. |
| **Recommendation** | Add custom CloudWatch metrics in Lambda handlers: `BooksCreated` (count per invocation), `BooksRetrieved` (count per scan), `BookCreationErrors` (count by error type). Publish metrics using the CloudWatch Embedded Metrics Format (EMF) for zero-latency metric emission from Lambda. Create a CloudWatch dashboard combining business and infrastructure metrics. |
| **Evidence** | `src/books/create/index.ts` — no `cloudwatch.putMetricData()` or EMF logging. `src/books/get-all/index.ts` — no custom metrics. No CloudWatch dashboard resources in `template.yml`. |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Two static threshold CloudWatch alarms exist: `CreateBookAliasErrorMetricGreaterThanZeroAlarm` and `GetAllBooksAliasErrorMetricGreaterThanZeroAlarm`. Both monitor Lambda `Errors` metric with threshold > 0 over 2 evaluation periods of 60 seconds. These alarms are connected to CodeDeploy for deployment rollback. No anomaly detection, no latency alarms, no composite alarms, no PagerDuty/OpsGenie integration. |
| **Gap** | Alarms only detect errors during deployments (for rollback). No steady-state alerting for error rate spikes, latency degradation, or throttling. No anomaly detection to catch gradual degradation. No notification integration — alarms trigger CodeDeploy rollback but do not notify humans. |
| **Recommendation** | Add CloudWatch anomaly detection on API Gateway latency and error rates. Add latency alarms (p99 > threshold). Create composite alarms combining error rate + latency for holistic health monitoring. Integrate with SNS → PagerDuty/OpsGenie for human notification. Add throttling alarms on Lambda concurrent executions. |
| **Evidence** | `template.yml` — Two `AWS::CloudWatch::Alarm` resources with `ComparisonOperator: GreaterThanThreshold`, `Threshold: 0`, `Period: 60`, `EvaluationPeriods: 2`. No anomaly detection alarms. No SNS topic for notifications. |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Production deployments use `Linear10PercentEvery1Minute` traffic shifting — a canary-style gradual deployment that shifts 10% of traffic every minute to the new Lambda version. Staging uses `AllAtOnce`. The `CreateBook` function has a pre-traffic hook (`CreateBookPreTraffic`) that performs a smoke test before any traffic shifts: it invokes the new function version, verifies the book was written to DynamoDB, and cleans up the test data. CloudWatch alarms are configured to trigger automatic rollback if errors are detected during traffic shifting. |
| **Gap** | None — deployment strategy is mature with progressive traffic shifting, pre-traffic validation, and alarm-based rollback. |
| **Recommendation** | No action needed. Current deployment strategy is a best practice for serverless applications. Consider adding `GetAllBooks` pre-traffic hook for parity with `CreateBook`. |
| **Evidence** | `template.yml` — `DeploymentPreference.Type: Linear10PercentEvery1Minute` (production, via `!If [IsProduction]`). `Hooks.PreTraffic: !Ref CreateBookPreTraffic`. `Alarms` section for rollback. `src/books/create-pre-traffic/index.ts` — smoke test implementation. |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Comprehensive E2E test suite (`src/books/tests/index.js`) runs in the CI pipeline after staging deployment (`pipeline/buildspec-test.json`). Tests cover 5 critical scenarios: (1) GET /books without auth succeeds, (2) GET /books returns data, (3) POST /books without token returns 401, (4) POST /books with invalid payload returns 500, (5) POST /books creates a book and verifies in DynamoDB. Tests use real Cognito tokens (programmatic auth via `USER_PASSWORD_AUTH`), real API endpoint, and real DynamoDB table. Test data is cleaned up after each test. |
| **Gap** | None — integration test coverage is comprehensive for the current API surface. |
| **Recommendation** | No action needed. Consider adding a test for pagination (when GET /books returns large result sets) and a test for DynamoDB throttling behavior. Migrate test suite from JavaScript to TypeScript for consistency with the application code. |
| **Evidence** | `src/books/tests/index.js` — Mocha test suite with 5 test cases. `src/books/tests/books-manager.js` — DynamoDB test helper for setup/teardown. `pipeline/buildspec-test.json` — runs tests after staging deploy. `pipeline/lib/pipeline-stack.ts` — Staging stage with Deploy (runOrder 1) + Test (runOrder 2). |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks, no SSM Automation documents, no self-healing automation, no incident response workflows. The only automated response is CodeDeploy rollback triggered by CloudWatch alarms during deployment (which is a deployment safety mechanism, not incident response). No runbook files (markdown, YAML, JSON) found in the repository. |
| **Gap** | No documented incident response procedures. When an incident occurs outside of a deployment window (e.g., DynamoDB throttling, Cognito issues, API Gateway 5xx spikes), there is no documented procedure for diagnosis, mitigation, or escalation. For a P1 service, this is a significant operational gap. |
| **Recommendation** | Create runbooks for common incident scenarios: DynamoDB throttling, Lambda cold start spikes, Cognito authentication failures, API Gateway 5xx errors. Start with markdown runbooks in a `runbooks/` directory, then evolve to SSM Automation documents for self-healing. Consider Lambda-based auto-remediation for DynamoDB capacity adjustments. |
| **Evidence** | No `runbooks/` directory. No `*.runbook.yml` or `*.runbook.md` files. No `AWS::SSM::Document` resources in `template.yml`. Only automated response: CodeDeploy rollback via alarm triggers. |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No per-service CloudWatch dashboards defined in IaC. No `CODEOWNERS` file in the repository. No named owners on CloudWatch alarms. No team attribution on observability assets. Alarms exist but have generic descriptions ("Lambda Function Error > 0") with no ownership tags or escalation paths. |
| **Gap** | No observability ownership. When an alarm fires, there is no documented owner or escalation path. No centralized dashboard for the Books API service health. For a P1 service, unclear ownership leads to delayed incident response. |
| **Recommendation** | Add a `CODEOWNERS` file mapping observability configs to a specific team. Create a CloudWatch dashboard in IaC (`AWS::CloudWatch::Dashboard`) showing Lambda invocations, errors, duration, DynamoDB reads/writes, and API Gateway latency. Add owner tags to CloudWatch alarms. Define an escalation path in the dashboard or a separate on-call document. |
| **Evidence** | No `CODEOWNERS` file. No `AWS::CloudWatch::Dashboard` in `template.yml`. CloudWatch alarms have generic `AlarmDescription` with no owner reference. |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Tags are present on Lambda functions (`Globals.Function.Tags`) and DynamoDB table (`BooksTable.Tags`) with two keys: `project: my-project` and `environment: {Stage}`. The `CreateBookPreTraffic` function has explicit tags (same keys). However, tags are not applied to all resources — API Gateway, Cognito User Pool, Cognito User Pool Client, Cognito Domain, IAM roles, and CloudWatch alarms are untagged. No tag enforcement (AWS Config rules, Service Control Policies). No cost allocation tags activated. |
| **Gap** | Inconsistent tagging across resources. Critical resources (API Gateway, Cognito, IAM roles) are untagged. The `project` tag uses a generic value (`my-project`) that does not uniquely identify the workload. No tag enforcement mechanism to prevent drift. Cannot track costs per workload or identify resource ownership during incidents. |
| **Recommendation** | Define a tagging standard with required keys: `project` (specific value, e.g., `books-api`), `environment`, `team`, `cost-center`. Apply tags to all resources using SAM `Globals` where possible and explicit tags elsewhere. Add AWS Config `required-tags` rule for enforcement. Activate cost allocation tags in the AWS Billing console. |
| **Evidence** | `template.yml` — `Globals.Function.Tags: { project: my-project, environment: !Ref Stage }`. `BooksTable.Tags` — same keys. No tags on `BooksApi`, `CognitoUserPool`, `UserPoolClient`, `UserPoolDomain`, `ApiGatewayLoggingRole`, CloudWatch Alarms. No `AWS::Config::ConfigRule` resources. |

## Learning Materials

The following learning resources are mapped to the **Move to AI** pathway (the only triggered pathway):

| Resource | Link |
|----------|------|
| Move to AI Learning Plan | [https://skillbuilder.aws/learning-plan/VDFEE4ACCV](https://skillbuilder.aws/learning-plan/VDFEE4ACCV) |
| Amazon Bedrock Getting Started | [https://skillbuilder.aws/learn/63KTRM86DQ](https://skillbuilder.aws/learn/63KTRM86DQ) |
| Introduction to Agentic AI on AWS | [https://skillbuilder.aws/learn/DNBD5MT8ZD](https://skillbuilder.aws/learn/DNBD5MT8ZD) |

**General cloud architecture training:** [AWS SkillBuilder](https://skillbuilder.aws/) — recommended for the operational maturity gaps identified in the OPS category.

## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `template.yml` | INF-Q1, INF-Q2, INF-Q3, INF-Q4, INF-Q5, INF-Q6, INF-Q7, INF-Q8, INF-Q9, INF-Q10, INF-Q11, APP-Q1, APP-Q2, APP-Q3, APP-Q4, APP-Q5, APP-Q6, DATA-Q1, DATA-Q2, DATA-Q3, DATA-Q4, SEC-Q1, SEC-Q2, SEC-Q3, SEC-Q4, SEC-Q5, SEC-Q6, SEC-Q7, OPS-Q1, OPS-Q2, OPS-Q4, OPS-Q5, OPS-Q7, OPS-Q8, OPS-Q9 | SAM/CloudFormation template defining all application infrastructure: Lambda functions, API Gateway, DynamoDB, Cognito, CloudWatch Alarms, IAM roles, CodeDeploy preferences |
| `pipeline/lib/pipeline-stack.ts` | INF-Q10, INF-Q11, SEC-Q2, SEC-Q5, OPS-Q6 | CDK stack defining CI/CD pipeline: CodePipeline stages, CodeBuild projects, S3 artifact buckets, IAM roles |
| `pipeline/bin/pipeline.ts` | INF-Q10 | CDK app entry point for pipeline stack |
| `pipeline/cdk.json` | INF-Q10 | CDK configuration file |
| `pipeline/package.json` | INF-Q10 | CDK pipeline dependencies (aws-cdk-lib, constructs) |
| `pipeline/buildspec.json` | INF-Q11, SEC-Q7 | Build stage: npm install, unit tests, sam build, sam package |
| `pipeline/buildspec-deploy.json` | INF-Q11 | Deploy stage: sam deploy with CloudFormation exports |
| `pipeline/buildspec-test.json` | INF-Q11, OPS-Q6 | E2E test stage: runs Mocha tests after staging deployment |
| `src/books/create/index.ts` | APP-Q1, APP-Q2, APP-Q3, APP-Q4, DATA-Q2, DATA-Q4, OPS-Q1, OPS-Q3 | CreateBook Lambda handler: DynamoDB putItem, X-Ray instrumentation, synchronous HTTP handler |
| `src/books/create/package.json` | APP-Q1, OPS-Q1, SEC-Q7 | CreateBook dependencies: aws-sdk v2, aws-xray-sdk-core, mocha, sinon, chai |
| `src/books/get-all/index.ts` | APP-Q1, APP-Q2, APP-Q3, DATA-Q2, OPS-Q1, OPS-Q3 | GetAllBooks Lambda handler: DynamoDB scan, X-Ray instrumentation, DTO mapping |
| `src/books/get-all/package.json` | APP-Q1, SEC-Q7 | GetAllBooks dependencies: aws-sdk v2, aws-xray-sdk-core |
| `src/books/create-pre-traffic/index.ts` | APP-Q2, APP-Q4, DATA-Q2, OPS-Q1, OPS-Q5 | Pre-traffic hook: smoke test with Lambda invocation, DynamoDB verification, cleanup |
| `src/books/create-pre-traffic/package.json` | APP-Q1 | Pre-traffic hook dependencies: aws-sdk v2 |
| `src/books/tests/index.js` | OPS-Q6 | E2E test suite: 5 test cases covering auth, validation, CRUD operations |
| `src/books/tests/books-manager.js` | OPS-Q6 | E2E test helper: DynamoDB batch write/delete for test data management |
| `src/books/tests/package.json` | OPS-Q6 | E2E test dependencies: aws-sdk, axios, uuid, chai, mocha |
| `README.md` | Quick Agent Wins (RAG Knowledge Agent) | Comprehensive documentation: architecture, deployment, testing, CI/CD, token management |
| `events/env.json` | Step 1 (Discovery) | Local test environment configuration: TABLE variable mapping |
| `events/create-book-request.json` | Step 1 (Discovery) | Sample API Gateway event for local Lambda testing (POST /books) |
| `events/get-all-books-request.json` | Step 1 (Discovery) | Sample API Gateway event for local Lambda testing (GET /books) |

---

*Report generated by Modernization Readiness Assessment. Assessment date: 2026-04-15.*
