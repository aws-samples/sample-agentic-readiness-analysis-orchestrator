# Modernization Readiness Analysis Report

| Field | Value |
|-------|-------|
| **Repository** | books-api |
| **Date** | 2026-04-27 |
| **Repo Type** | application |
| **Service Archetype** | stateful-crud (auto-detected) |
| **Priority** | P1 |
| **Tags** | serverless, cdk, api, dynamodb |
| **Context** | Serverless REST API with CDK infrastructure for book catalog management. Clean API surface the agent can use as a tool for product lookups. |
| **Overall Score** | **2.65 / 4.0** |

**Archetype Justification**: DynamoDB writes detected (putItem in `src/books/create/index.ts`) and reads (scan in `src/books/get-all/index.ts`) — service owns persistent state via the DynamoDB books table and exposes CRUD operations (POST /books, GET /books). No message queue consumers or fan-out to downstream services. Classified as stateful-crud.

---

## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | 3.00 / 4.0 | 🟡 Partial |
| Application Architecture (APP) | 2.83 / 4.0 | 🟡 Partial |
| Data Platform Modernization (DATA) | 2.75 / 4.0 | 🟡 Partial |
| Security Baseline (SEC) | 2.57 / 4.0 | 🟡 Partial |
| Operations & Observability (OPS) | 2.11 / 4.0 | 🟠 Needs Work |
| **Overall** | **2.65 / 4.0** | **🟡 Partial** |

---

## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | SEC-Q7: Application Security Pipeline | 1 | No SAST, dependency scanning, or security gates in CI/CD pipeline | Vulnerabilities in dependencies or code reach production undetected; critical for P1 service in e-commerce portfolio |
| 2 | INF-Q5: Network Security | 1 | Lambda functions run outside VPC with no network segmentation or private subnets | No network-level isolation for DynamoDB access; broader blast radius if credentials are compromised |
| 3 | INF-Q8: Backup and Recovery | 1 | No DynamoDB Point-in-Time Recovery (PITR) or backup plan configured | Data loss from accidental deletion or corruption has no recovery path; single-table design amplifies risk |
| 4 | OPS-Q7: Incident Response Automation | 1 | No runbooks, SSM Automation documents, or self-healing patterns | Incident response is entirely manual; MTTR increases for a P1 service in the e-commerce platform |
| 5 | OPS-Q3: Business Metrics | 1 | No custom business metrics published; only default infrastructure metrics | Cannot measure business outcomes (book creation rates, API error rates by operation) to inform modernization decisions |

---

## Quick Agent Wins

### Data Query Agent

- **Prerequisite:** DATA-Q2 = 2 (≥ 2). DynamoDB `books` table has a clear, simple schema (isbn, title, year, author, publisher, rating, pages) defined in `src/books/create/index.ts` and `src/books/get-all/index.ts`.
- **What it enables:** A natural-language-to-DynamoDB agent that allows product managers or support agents to query the book catalog without writing code. For example: "Find all books by author X" or "How many books were published after 2020?"
- **Additional steps:** Generate a schema document describing the DynamoDB table structure, key schema, and attribute types. Consider adding a GSI for author-based queries to support richer agent interactions. Integrate Amazon Bedrock for natural language understanding.
- **Effort:** Medium — DynamoDB schema is simple, but a query translation layer (PartiQL or DynamoDB SDK wrapper) needs to be built as an agent tool.

### DevOps Agent

- **Prerequisite:** INF-Q11 = 4 (≥ 2). Full CI/CD pipeline exists via CodePipeline with Source → Build → Staging → Production stages, defined in `pipeline/lib/pipeline-stack.ts`.
- **What it enables:** An agent that triggers deployments, checks build status, monitors canary deployment progress, and manages release approvals. The existing CodePipeline API surface provides all necessary actions.
- **Additional steps:** Create an agent tool wrapper around the CodePipeline and CodeDeploy APIs. Define guardrails to prevent the agent from approving production deployments without human review.
- **Effort:** Low — pipeline automation surface already exists via AWS APIs; agent needs SDK integration with Amazon Bedrock for natural language orchestration.

### RAG-Based Knowledge Agent

- **Prerequisite:** Comprehensive README.md exists (200+ lines) covering architecture, project structure, deployment procedures, monitoring, tracing, CI/CD, and testing instructions.
- **What it enables:** A RAG-based knowledge agent that indexes the repository documentation and answers developer questions about the books-api service — deployment procedures, architecture decisions, testing approaches, and troubleshooting.
- **Additional steps:** Index README.md and code comments into a vector store (Amazon OpenSearch Service with vector engine or Amazon Bedrock Knowledge Bases). Add API documentation (currently missing — generating an OpenAPI spec would significantly enhance the knowledge base).
- **Effort:** Medium — documentation exists but needs indexing infrastructure; Amazon Bedrock Knowledge Bases with S3 data source can accelerate setup.

### Observability Agent

- **Prerequisite:** OPS-Q1 = 3 (≥ 2). X-Ray distributed tracing is enabled on Lambda functions (`Tracing: Active` in `template.yml`) and API Gateway (`TracingEnabled: true`). The `aws-xray-sdk-core` library captures DynamoDB calls in both `create/index.ts` and `get-all/index.ts`.
- **What it enables:** An agent that queries X-Ray traces, correlates API Gateway and Lambda execution data, identifies latency outliers, and suggests root causes for errors. Can also query CloudWatch logs for Lambda function errors.
- **Additional steps:** Add structured logging (JSON format) to Lambda functions to improve log queryability. Create CloudWatch Logs Insights saved queries that the agent can invoke as tools. Consider adding custom metrics for richer signal.
- **Effort:** Medium — tracing data exists but Lambda functions use unstructured console.log; structured logging would significantly improve agent effectiveness.

---

## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | Not Triggered | — | — | APP-Q2 = 3 (≥ 3) — application is already serverless with independent Lambda functions and API Gateway |
| 2 | Move to Containers | Not Triggered | — | — | INF-Q1 = 4 — compute is already Lambda/serverless; contextual guard prevents trigger |
| 3 | Move to Open Source | Not Triggered | — | — | DATA-Q4 = 4 — no stored procedures or proprietary SQL; DynamoDB is AWS-native (not a commercial licensed product) |
| 4 | Move to Managed Databases | Not Triggered | — | — | INF-Q2 = 4 — DynamoDB is fully managed with automated failover |
| 5 | Move to Managed Analytics | Not Triggered | — | — | INF-Q4 = 3 (≥ 3); no data processing workloads detected — contextual guard prevents trigger |
| 6 | Move to Modern DevOps | Not Triggered | — | — | INF-Q10 = 3 (≥ 3), INF-Q11 = 4 (≥ 3) — IaC and CI/CD automation meet thresholds |
| 7 | Move to AI | Triggered | Medium | Medium | No AI/agent frameworks detected; portfolio context confirms AI intent ("building a customer support agent") |

---

### Pathway: Move to AI

**Status:** Triggered
**Priority:** Medium
**Estimated Effort:** Medium

#### Current AI/Agent Infrastructure State

No AI/agent infrastructure exists in the books-api repository:
- **AI/Agent Frameworks:** No imports of Amazon Bedrock SDK, LangChain, Strands, OpenAI, Spring AI, HuggingFace, or SageMaker SDK detected in any source file (`src/books/create/index.ts`, `src/books/get-all/index.ts`, `src/books/create-pre-traffic/index.ts`).
- **Vector Database:** No OpenSearch with vector engine, Pinecone, pgvector, Weaviate, or Qdrant detected.
- **RAG Implementation:** No embedding generation, vector store queries, or retrieval chain patterns found.
- **Agent Evaluation:** No Ragas, DeepEval, or custom evaluation framework detected.

#### AI Intent and Use Cases

The portfolio context explicitly states: *"building a customer support agent that handles order inquiries, processes returns, and manages inventory restocking."* The books-api service is described as providing a *"clean API surface the agent can use as a tool for product lookups."*

**Identified AI integration opportunities for books-api:**

1. **Book Catalog Tool for Customer Support Agent** — Expose the GET /books endpoint as a tool that the customer support agent can invoke to look up book details (title, author, ISBN, availability). The existing API Gateway + Lambda architecture is well-suited as an agent tool backend.

2. **Natural Language Book Search** — Add a Bedrock-powered search capability that allows customers or agents to query the book catalog using natural language (e.g., "Find science fiction books by Isaac Asimov").

3. **Book Recommendation Agent** — Leverage Amazon Bedrock to build a recommendation engine based on book attributes (genre, author, rating) stored in DynamoDB.

#### Foundation Requirements

Before AI integration, the following foundations should be in place:

| Requirement | Current State | Action Needed |
|-------------|---------------|---------------|
| API Documentation | No OpenAPI spec exists (APP-Q5 = 1) | Generate OpenAPI 3.0 spec from SAM template for agent tool discovery |
| Structured Logging | Unstructured console.log in Lambda | Add JSON structured logging for agent observability |
| API Versioning | No versioning (APP-Q5 = 1) | Add /v1/ path prefix to protect agent integrations from breaking changes |
| Error Handling | Basic try/catch returning 500 | Add structured error responses with error codes for agent error handling |

#### Recommended AWS Services

- **Amazon Bedrock** — Foundation model access for natural language understanding and generation (preferred per technology preferences)
- **Amazon Bedrock AgentCore** — Agent runtime for building and deploying AI agents
- **Amazon Bedrock Knowledge Bases** — RAG implementation using existing documentation and book catalog data
- **Amazon OpenSearch Service** (vector engine) — Vector store for semantic book search
- **Amazon EventBridge** — Event-driven integration between books-api and the customer support agent (preferred per technology preferences)

#### Quick Wins

See the [Quick Agent Wins](#quick-agent-wins) section above for immediate AI integration opportunities that leverage the existing architecture.

#### Learning Resources

- [Move to AI Learning Plan](https://skillbuilder.aws/learning-plan/VDFEE4ACCV)
- [Amazon Bedrock Getting Started](https://skillbuilder.aws/learn/63KTRM86DQ)
- [Introduction to Agentic AI on AWS](https://skillbuilder.aws/learn/DNBD5MT8ZD)

---

## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | All compute workloads run on AWS Lambda (serverless). `template.yml` defines three `AWS::Serverless::Function` resources: `GetAllBooks` (GET /books), `CreateBook` (POST /books), and `CreateBookPreTraffic` (pre-traffic smoke test hook). Runtime is `nodejs22.x` with 512MB memory and 5-second timeout. No EC2 instances, ECS tasks, or other self-managed compute found anywhere in the repository. |
| **Gap** | None. All compute is fully managed serverless. |
| **Recommendation** | No action needed. Lambda is the correct compute model for this API's traffic patterns and simplicity. The current configuration is well-aligned with serverless best practices. |
| **Evidence** | `template.yml` — `AWS::Serverless::Function` resources (GetAllBooks, CreateBook, CreateBookPreTraffic); `Globals.Function.Runtime: nodejs22.x` |

#### INF-Q2: Managed Databases

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | DynamoDB is the only database, defined as `AWS::Serverless::SimpleTable` (`BooksTable`) in `template.yml`. DynamoDB is fully managed by AWS with automatic multi-AZ replication, automated backups (if PITR enabled), and no patching required. SSE is enabled (`SSESpecification.SSEEnabled: true`). Primary key is `isbn` (String). |
| **Gap** | None. Database is fully managed with automated failover inherent to DynamoDB. |
| **Recommendation** | No action needed. DynamoDB is the correct choice for this simple key-value access pattern (preferred per technology preferences). Consider enabling PITR for data protection (see INF-Q8). |
| **Evidence** | `template.yml` — `BooksTable: AWS::Serverless::SimpleTable` with `PrimaryKey: {Name: isbn, Type: String}`, `SSESpecification: {SSEEnabled: true}` |

#### INF-Q3: Workflow Orchestration

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | No dedicated workflow orchestration service (Step Functions, MWAA, Temporal) is used. The application has two operations: create book (single DynamoDB putItem) and get all books (single DynamoDB scan). The pre-traffic hook (`CreateBookPreTraffic`) performs a sequential smoke test (invoke Lambda → getItem → deleteItem) but this is a deployment safety check, not a business workflow. For this stateful-crud service with only two simple operations, no multi-step business workflows currently exist that would warrant dedicated orchestration. |
| **Gap** | No orchestration infrastructure exists. As the service grows (e.g., book creation with validation, notification, indexing), multi-step operations will emerge that need orchestration rather than inline sequential code. |
| **Recommendation** | Plan for AWS Step Functions when operations become multi-step. The current pre-traffic hook pattern (`create-pre-traffic/index.ts`) already shows sequential operation patterns that could benefit from Step Functions as they grow in complexity. EventBridge integration (preferred) would complement Step Functions for event-driven workflow triggers. |
| **Evidence** | `template.yml` — no `AWS::StepFunctions::*` resources; `src/books/create-pre-traffic/index.ts` — sequential Lambda invoke → DynamoDB getItem → deleteItem pattern (deployment check, not business workflow) |

#### INF-Q4: Async Messaging and Streaming

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | No messaging or streaming infrastructure (SQS, SNS, EventBridge, MSK, Kinesis) is defined. The application is a single-service API with no cross-service communication. All operations are synchronous: API Gateway → Lambda → DynamoDB → response. For this stateful-crud archetype as a single service, synchronous communication is currently appropriate. However, as part of the e-commerce portfolio, book creation events should be published for downstream consumers (e.g., search indexing, recommendations, inventory systems). |
| **Gap** | No event publication on state changes. When a book is created (POST /books), no event is emitted for downstream consumers. This limits integration with the broader e-commerce platform (e.g., the customer support agent mentioned in portfolio context). |
| **Recommendation** | Add Amazon EventBridge (preferred per technology preferences) to publish `BookCreated` events when new books are added. This enables event-driven integration with the customer support agent and other portfolio services without tight coupling. Avoid self-managed Kafka (per preferences). |
| **Evidence** | `template.yml` — no `AWS::SQS::*`, `AWS::SNS::*`, `AWS::Events::*` resources; `src/books/create/index.ts` — putItem with no event emission after successful write |

#### INF-Q5: Network Security

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No VPC configuration found. Lambda functions run in the default Lambda-managed network (outside any customer VPC). No private subnets, security groups, NACLs, or network segmentation defined. DynamoDB is accessed via the public AWS endpoint. API Gateway is the only entry point, providing some isolation, but there are no VPC endpoints or PrivateLink configurations. |
| **Gap** | Services deployed without VPC isolation. DynamoDB access occurs over the AWS public network rather than through VPC endpoints. No network segmentation exists between tiers. |
| **Recommendation** | For a serverless API accessing only DynamoDB, VPC configuration is optional but recommended for defense-in-depth: (1) Configure Lambda functions in a VPC with private subnets, (2) Add a DynamoDB VPC Gateway Endpoint to keep traffic off the public internet, (3) Apply security groups to Lambda ENIs restricting outbound traffic. Note: VPC-attached Lambda adds cold start latency — evaluate trade-off for this use case. |
| **Evidence** | `template.yml` — no `VpcConfig` on any Lambda function; no `AWS::EC2::VPC`, `AWS::EC2::Subnet`, `AWS::EC2::SecurityGroup`, or `AWS::EC2::VPCEndpoint` resources |

#### INF-Q6: API Entry Point

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | API Gateway (`AWS::Serverless::Api`) serves as the managed entry point with Cognito authorization, method-level CloudWatch logging (`LoggingLevel: INFO`), and X-Ray tracing (`TracingEnabled: true`). The API is named `books-api-{Stage}` with stage-specific deployment. Cognito auth is configured on POST /books; GET /books is intentionally public. |
| **Gap** | No throttling configuration (no `ThrottlingBurstLimit` or `ThrottlingRateLimit`), no request validation (no `RequestModel` or `RequestParameters`), and no WAF integration. The API relies on API Gateway default throttling limits. |
| **Recommendation** | Add explicit throttling limits per method, request validation models to reject malformed payloads before they reach Lambda, and consider AWS WAF for IP-based rate limiting and common attack pattern protection. API Gateway (preferred per technology preferences) already provides the foundation — these are configuration enhancements. |
| **Evidence** | `template.yml` — `BooksApi: AWS::Serverless::Api` with `MethodSettings: [{LoggingLevel: INFO, TracingEnabled: true}]`, `Auth.Authorizers.CognitoAuth` |

#### INF-Q7: Auto-Scaling

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Lambda functions auto-scale inherently with no configuration required — each invocation runs in its own execution environment. DynamoDB `SimpleTable` in SAM defaults to on-demand capacity (PAY_PER_REQUEST), which auto-scales read/write capacity automatically. No explicit `ReservedConcurrentExecutions` or `ProvisionedConcurrencyConfig` on Lambda functions. |
| **Gap** | No explicit Lambda concurrency limits configured. Without `ReservedConcurrentExecutions`, a traffic spike on one function could consume the account's concurrency limit (default 1000), starving other functions. No provisioned concurrency for latency-sensitive operations. |
| **Recommendation** | Set `ReservedConcurrentExecutions` on each Lambda function to prevent a single function from consuming the account's concurrency pool. Consider `ProvisionedConcurrency` for the GET /books function if consistent low-latency is required for the customer support agent integration. |
| **Evidence** | `template.yml` — `AWS::Serverless::Function` with no `ReservedConcurrentExecutions` or `ProvisionedConcurrencyConfig`; `AWS::Serverless::SimpleTable` defaults to on-demand |

#### INF-Q8: Backup and Recovery

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No backup configuration found anywhere in the repository. The DynamoDB `SimpleTable` does not enable Point-in-Time Recovery (PITR). No `AWS::DynamoDB::Table` with `PointInTimeRecoverySpecification` enabled. No `AWS::Backup::BackupPlan` resources. SAM `SimpleTable` does not support PITR — a full `AWS::DynamoDB::Table` resource is needed to enable it. |
| **Gap** | No backup or recovery capability. Accidental data deletion or corruption in the books table has no recovery path. For a P1 service in the e-commerce platform, this is a significant risk. |
| **Recommendation** | Replace `AWS::Serverless::SimpleTable` with `AWS::DynamoDB::Table` and enable `PointInTimeRecoverySpecification: {PointInTimeRecoveryEnabled: true}`. Additionally, consider adding an `AWS::Backup::BackupPlan` for cross-region backup replication of the books catalog data. |
| **Evidence** | `template.yml` — `BooksTable: AWS::Serverless::SimpleTable` with no PITR; no `AWS::Backup::*` resources in any IaC file |

#### INF-Q9: High Availability and Fault Isolation

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | All production resources are inherently multi-AZ: Lambda functions execute across multiple AZs transparently, DynamoDB replicates data across multiple AZs within a region, and API Gateway is a regional service spanning multiple AZs. No single point of failure exists at the AZ level. |
| **Gap** | None. The serverless architecture provides inherent multi-AZ high availability. |
| **Recommendation** | No action needed. Consider multi-region active-active or active-passive setup if the e-commerce platform requires regional disaster recovery, but this is beyond the current single-region scope. |
| **Evidence** | `template.yml` — Lambda (`AWS::Serverless::Function`), DynamoDB (`AWS::Serverless::SimpleTable`), and API Gateway (`AWS::Serverless::Api`) are all inherently multi-AZ AWS services |

#### INF-Q10: Infrastructure as Code Coverage

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | SAM template (`template.yml`) defines compute (Lambda functions), API (API Gateway), database (DynamoDB table), authentication (Cognito User Pool, Client, Domain), deployment alarms (CloudWatch), and IAM roles. CDK (`pipeline/lib/pipeline-stack.ts`) defines the complete CI/CD pipeline (CodePipeline, CodeBuild projects, S3 artifact buckets). All primary infrastructure is in IaC. |
| **Gap** | No operational/DR resources in IaC: no CloudWatch dashboards, no operational alarms (beyond deployment rollback alarms), no Route 53 health checks, no Backup plans, no SNS topics for alert routing. Deployment alarms (`CreateBookAliasErrorMetricGreaterThanZeroAlarm`, `GetAllBooksAliasErrorMetricGreaterThanZeroAlarm`) exist but serve only as deployment safety gates, not ongoing operational monitoring. |
| **Recommendation** | Add IaC definitions for: CloudWatch dashboards per function, operational alarms (p99 latency, error rate thresholds), SNS topics for alarm routing, and DynamoDB backup plans. Consider migrating from SAM/CDK to Terraform (preferred per technology preferences) with a GitOps workflow (preferred) for infrastructure changes. |
| **Evidence** | `template.yml` — SAM resources covering compute, API, DB, auth, deployment alarms; `pipeline/lib/pipeline-stack.ts` — CDK pipeline definition; absence of CloudWatch dashboards, operational alarms, Backup plans in both files |

#### INF-Q11: CI/CD Automation

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Full CI/CD automation via CodePipeline with 4 stages: Source (GitHub via CodeStar Connections) → Build (SAM build + unit tests) → Staging (SAM deploy + e2e tests) → Production (manual approval + SAM deploy with canary). Build stage runs unit tests (`npm test` in `buildspec.json`). Staging runs e2e tests after deployment (`buildspec-test.json`). Production uses `Linear10PercentEvery1Minute` canary deployment with CloudWatch alarm-based automatic rollback. Pre-traffic hooks perform smoke tests before traffic shifting. |
| **Gap** | None significant. Manual approval gate for production is a valid safety measure. Minor: no security scanning in the pipeline (covered in SEC-Q7). |
| **Recommendation** | Add security scanning steps to the pipeline (see SEC-Q7). Consider adopting a GitOps approach (preferred per technology preferences) with ArgoCD or Flux for declarative deployment management. |
| **Evidence** | `pipeline/lib/pipeline-stack.ts` — CodePipeline with Source/Build/Staging/Production stages; `pipeline/buildspec.json` — SAM build + unit tests; `pipeline/buildspec-test.json` — e2e tests; `template.yml` — `DeploymentPreference: {Type: Linear10PercentEvery1Minute}` with alarm-based rollback |

### Application Architecture

#### APP-Q1: Programming Languages

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | TypeScript is the primary language, running on Node.js 22.x (`Globals.Function.Runtime: nodejs22.x` in `template.yml`). TypeScript/JavaScript has first-class AWS SDK coverage (`aws-sdk` v2.1692.0 in dependencies), broad cloud-native tooling, and a mature serverless framework ecosystem (SAM, CDK, esbuild for bundling). The pipeline CDK app also uses TypeScript. |
| **Gap** | None. TypeScript/Node.js is a tier-1 language for AWS cloud-native development. |
| **Recommendation** | Consider migrating from `aws-sdk` v2 to `@aws-sdk/client-dynamodb` v3 (modular SDK) for smaller bundle sizes and improved tree-shaking with esbuild. The v2 SDK is in maintenance mode. |
| **Evidence** | `template.yml` — `Runtime: nodejs22.x`; `src/books/create/package.json` — `aws-sdk: ^2.1692.0`, `aws-xray-sdk-core: ^3.10.3`; `pipeline/package.json` — `aws-cdk-lib: ^2.189.1` |

#### APP-Q2: Monolith vs Microservices

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | The application is a well-structured serverless API with separate Lambda functions per API operation. `GetAllBooks` and `CreateBook` are independently deployable (each has its own `CodeUri`, `Handler`, `AutoPublishAlias`, and `DeploymentPreference`). They share a single DynamoDB table (`BooksTable`) but have separate IAM policies (`DynamoDBReadPolicy` vs `DynamoDBWritePolicy`). The pre-traffic hook (`CreateBookPreTraffic`) is a deployment utility, not a business service. This is a modular serverless application with well-defined function boundaries and least-privilege access — not a monolith, but also not a multi-service microservices architecture. |
| **Gap** | Single SAM template deploys all functions together. While functions are independently scalable and deployable to aliases, they share a deployment lifecycle (single `sam deploy` creates/updates all resources). No separate service boundaries for different business domains (e.g., book management vs. catalog search vs. book reviews). |
| **Recommendation** | The current structure is appropriate for the scope (2 endpoints on 1 entity). As the API grows, consider extracting distinct business domains into separate SAM applications or separate services. The existing pattern of separate CodeUri per function provides a clean extraction boundary. |
| **Evidence** | `template.yml` — separate `AWS::Serverless::Function` resources with independent `CodeUri` (`src/books/create/`, `src/books/get-all/`), separate IAM policies, separate deployment preferences |

#### APP-Q3: Async vs Sync Communication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | All communication is synchronous HTTP: API Gateway → Lambda → DynamoDB → HTTP response. No inter-service communication exists — this is a single-service API within the e-commerce portfolio. No message publishing (SQS, SNS, EventBridge) on state changes. For this stateful-crud archetype as a standalone service, synchronous request/response is currently the appropriate primary pattern. However, the service should emit events for downstream integration. |
| **Gap** | No async event emission on state mutations. The `CreateBook` function completes a DynamoDB write and returns a 201 response without publishing an event. In the e-commerce portfolio context, downstream services (search, recommendations, customer support agent) have no way to react to new books being added. |
| **Recommendation** | Add EventBridge (preferred) event emission after successful book creation. Pattern: Lambda → DynamoDB putItem → EventBridge PutEvents(`BookCreated`) → HTTP 201 response. This enables downstream consumers without changing the synchronous API contract. |
| **Evidence** | `src/books/create/index.ts` — synchronous putItem → return 201; `src/books/get-all/index.ts` — synchronous scan → return 200; no event publishing imports or patterns in any source file |

#### APP-Q4: Long-Running Process Handling

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Lambda timeout is 5 seconds (`Globals.Function.Timeout: 5`). All operations are fast DynamoDB operations: `putItem` (single item write, sub-100ms) and `scan` (full table scan, fast for small tables). No operations approach 30 seconds. The pre-traffic hook includes a 1.5-second wait (`wait()` function in `create-pre-traffic/index.ts`) but this is a deployment utility, not a user-facing operation. For this stateful-crud with fast DynamoDB operations, all operations complete well within the timeout. |
| **Gap** | None for current scope. The `scan` operation in `get-all/index.ts` performs a full table scan without pagination — this will become slow as the table grows (O(n) with table size), potentially exceeding the 5-second timeout. |
| **Recommendation** | Add pagination to the `GetAllBooks` scan operation (`ExclusiveStartKey` / `LastEvaluatedKey` pattern) to prevent timeout as the books table grows. Consider adding GSIs for filtered queries to avoid full scans. |
| **Evidence** | `template.yml` — `Globals.Function.Timeout: 5`; `src/books/create/index.ts` — `putItem` (single item); `src/books/get-all/index.ts` — `scan` without `Limit` or `ExclusiveStartKey`; `src/books/create-pre-traffic/index.ts` — `wait(1500)` in deployment hook |

#### APP-Q5: API Versioning Strategy

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No API versioning strategy implemented. The API path is `/books` with no version prefix (`/v1/books`). No `Accept-Version` headers. No versioning annotations. The SAM template's `OpenApiVersion: 3.0.1` in Globals is a SAM configuration parameter to avoid default stage creation, not an API version. |
| **Gap** | No versioning means any breaking change to the API contract (request/response schema, behavior) will break all consumers simultaneously. This is critical if the customer support agent will use this API as a tool — breaking changes to the API surface will break the agent. |
| **Recommendation** | Implement URL path versioning (`/v1/books`) as the simplest approach compatible with API Gateway. Update the SAM template's API event paths to include version prefixes. Establish a versioning policy: new versions for breaking changes, backward-compatible changes within existing versions. |
| **Evidence** | `template.yml` — API events use path `/books` with no version prefix; no version headers or annotations in source code; `Globals.Api.OpenApiVersion: 3.0.1` is SAM config, not API versioning |

#### APP-Q6: Service Discovery

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | DynamoDB table name is passed via environment variable (`TABLE: !Ref BooksTable` in `template.yml`). Lambda function version is passed via `FN_NEW_VERSION: !Ref CreateBook.Version` for the pre-traffic hook. The API endpoint is exported as a CloudFormation Output. No downstream service endpoints exist (single-service API). No service registry, service mesh, or dynamic discovery mechanism. |
| **Gap** | Environment variables for endpoint configuration with no dynamic discovery. Currently acceptable for a single service, but as the e-commerce portfolio grows and this service needs to discover other services (or be discovered by them, including the customer support agent), a discovery mechanism will be needed. |
| **Recommendation** | Register the API in AWS Service Discovery or use API Gateway as the service catalog. Export the API endpoint via CloudFormation Outputs (already done) and consider AWS Cloud Map for service-to-service discovery as the portfolio grows. |
| **Evidence** | `template.yml` — `Environment.Variables.TABLE: !Ref BooksTable`; CloudFormation `Outputs.ApiEndpoint`; no AWS Cloud Map, Consul, or service mesh resources |

### Data Platform Modernization

#### DATA-Q1: Unstructured Data Storage

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No unstructured data storage detected. DynamoDB is the only data store, used for structured book records (isbn, title, year, author, publisher, rating, pages). No S3 buckets for application data (pipeline artifact buckets in `pipeline-stack.ts` are CI/CD artifacts, not application data). No file upload endpoints. No document/image processing. |
| **Gap** | No capability to store or process unstructured data (book covers, PDF excerpts, review documents). For a book catalog service, unstructured data storage would enable richer product information and support AI-powered features (e.g., book cover image analysis, full-text search of book descriptions). |
| **Recommendation** | Add an S3 bucket for book-related unstructured data (cover images, descriptions, sample chapters). Use Amazon Textract for document parsing if PDF content is needed. This would also enhance the RAG knowledge base for the customer support agent. |
| **Evidence** | `template.yml` — only `AWS::Serverless::SimpleTable` (DynamoDB); no `AWS::S3::Bucket` for application data; `pipeline/lib/pipeline-stack.ts` — S3 buckets (`ci-cd-pipeline-artifacts-*`, `books-api-artifacts-*`) are CI/CD only |

#### DATA-Q2: Unified Data Access Layer

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | DynamoDB access is directly in each Lambda handler via the `aws-sdk` DynamoDB client. Each function creates its own client instance and executes queries directly: `src/books/create/index.ts` uses `client.putItem()`, `src/books/get-all/index.ts` uses `client.scan()`, `src/books/create-pre-traffic/index.ts` uses `ddbClient.getItem()` and `ddbClient.deleteItem()`, and `src/books/tests/books-manager.js` uses `client.batchWriteItem()` and `client.getItem()`. Data marshalling (DynamoDB attribute maps to/from plain objects) is duplicated across files. |
| **Gap** | No centralized repository/DAO layer. Data access code and DynamoDB attribute marshalling logic are duplicated across 4 files. The item schema (isbn, title, year, author, publisher, rating, pages) is implicitly defined in each function rather than in a shared model. This increases the risk of schema drift between read and write operations. |
| **Recommendation** | Extract a shared `BooksRepository` module with methods for `create(book)`, `getAll()`, `getByIsbn(isbn)`, `delete(isbn)`. Centralize DynamoDB client creation, attribute marshalling, and error handling. Use the AWS SDK v3 `@aws-sdk/lib-dynamodb` DocumentClient for simplified marshalling. |
| **Evidence** | `src/books/create/index.ts` — `new AWS.DynamoDB()`, `client.putItem()`; `src/books/get-all/index.ts` — `new AWS.DynamoDB()`, `client.scan()`; `src/books/create-pre-traffic/index.ts` — `new DynamoDB()`, `ddbClient.getItem()`, `ddbClient.deleteItem()`; `src/books/tests/books-manager.js` — `new AWS.DynamoDB()`, `client.batchWriteItem()`, `client.getItem()` |

#### DATA-Q3: Database Engine Version and EOL

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | DynamoDB is a fully serverless, version-managed database service. There is no database engine version to pin — AWS manages all versioning, patching, and upgrades transparently. No EOL risk exists. The DynamoDB API version specified in code (`apiVersion: '2012-08-10'`) is the AWS SDK API version, not a database engine version. |
| **Gap** | None. DynamoDB's managed nature eliminates version management and EOL concerns entirely. |
| **Recommendation** | No action needed. If additional databases are added in the future, ensure engine versions are explicitly pinned in IaC. |
| **Evidence** | `template.yml` — `AWS::Serverless::SimpleTable` (DynamoDB, no engine version parameter); `src/books/create/index.ts` — `apiVersion: '2012-08-10'` (SDK API version, not engine version) |

#### DATA-Q4: Stored Procedures and Schema Complexity

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | DynamoDB does not support stored procedures, triggers, or proprietary SQL. All business logic resides in the Lambda application layer. The data access pattern is simple: `putItem` for creates and `scan` for reads. No SQL migration files, no ORM configurations, no database-side business logic of any kind. |
| **Gap** | None. All logic is in the application layer — no database coupling. |
| **Recommendation** | No action needed. Continue keeping all business logic in the Lambda functions. If complex queries are needed in the future, use DynamoDB PartiQL or GSIs rather than moving logic to the database layer. |
| **Evidence** | `src/books/create/index.ts` — `putItem` only; `src/books/get-all/index.ts` — `scan` only; no `.sql` files, no stored procedure definitions, no ORM configs in repository |

### Security Baseline

#### SEC-Q1: Audit Logging

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | API Gateway has CloudWatch logging enabled (`LoggingLevel: INFO` on all methods) with a dedicated IAM role (`ApiGatewayLoggingRole`). Lambda functions have X-Ray tracing enabled (`Tracing: Active`). API Gateway tracing is also enabled (`TracingEnabled: true`). However, no CloudTrail resource is defined in IaC. No immutable log storage (S3 Object Lock). No log retention policies specified. |
| **Gap** | No CloudTrail configuration in IaC — reliance on account-level CloudTrail (if it exists). No immutable log storage. No explicit log retention policies. API-level logging exists but audit trail for AWS API calls (who created/modified/deleted resources) is not defined in this stack. |
| **Recommendation** | Add CloudTrail configuration in IaC with log file validation enabled and S3 bucket with Object Lock for immutable storage. Set CloudWatch log retention policies for Lambda and API Gateway log groups. Consider centralizing logs with CloudWatch Logs cross-account subscriptions for the e-commerce portfolio. |
| **Evidence** | `template.yml` — `MethodSettings: [{LoggingLevel: INFO}]`, `TracingEnabled: true`, `ApiGatewayLoggingRole`; `Globals.Function.Tracing: Active`; no `AWS::CloudTrail::Trail` resource; no S3 Object Lock configuration |

#### SEC-Q2: Encryption at Rest

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | DynamoDB table has server-side encryption enabled (`SSESpecification.SSEEnabled: true`), using AWS-managed encryption keys by default. Pipeline S3 buckets use S3-managed encryption (`BucketEncryption.S3_MANAGED` in `pipeline-stack.ts`). No customer-managed KMS keys are defined anywhere. All data stores have encryption enabled, but with AWS-managed rather than customer-managed keys. |
| **Gap** | No customer-managed KMS keys. AWS-managed encryption is enabled across all data stores, which is acceptable for most workloads, but customer-managed keys provide additional control over key rotation policies and access auditing. |
| **Recommendation** | For a P1 service, consider adding customer-managed KMS keys for the DynamoDB table to enable fine-grained key policies and rotation schedules. Replace `SSEEnabled: true` with `SSESpecification: {SSEEnabled: true, SSEType: KMS, KMSMasterKeyId: !Ref BooksTableKey}`. |
| **Evidence** | `template.yml` — `BooksTable.SSESpecification.SSEEnabled: true` (AWS-managed); `pipeline/lib/pipeline-stack.ts` — `BucketEncryption.S3_MANAGED`; no `AWS::KMS::Key` resources |

#### SEC-Q3: API Authentication

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Cognito User Pool authorizer configured on POST /books endpoint with `AuthorizationScopes: [email]`. GET /books is intentionally public — no authentication required (documented design decision: "Getting all books is a public operation that everyone can call"). OAuth2 implicit grant flow configured via `UserPoolClient` with `AllowedOAuthFlows: [implicit]`. In staging, `ALLOW_USER_PASSWORD_AUTH` is enabled for automated testing. |
| **Gap** | GET /books has no authentication. While documented as intentional, this means anyone can query the full book catalog. The OAuth2 implicit grant flow is considered less secure than authorization code flow with PKCE. No API key or rate limiting on the public endpoint to prevent abuse. |
| **Recommendation** | Add API Gateway usage plans with API keys and throttling on the public GET /books endpoint to prevent abuse. Migrate from OAuth2 implicit grant to authorization code flow with PKCE for improved security. Consider adding optional authentication on GET /books for personalized responses. |
| **Evidence** | `template.yml` — POST /books: `Auth.Authorizer: CognitoAuth, AuthorizationScopes: [email]`; GET /books: no Auth block; `UserPoolClient.AllowedOAuthFlows: [implicit]`; `ExplicitAuthFlows: [ALLOW_USER_PASSWORD_AUTH]` conditional on staging |

#### SEC-Q4: Centralized Identity Integration

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Amazon Cognito User Pool (`CognitoUserPool`) serves as the identity provider with OAuth2 configuration including user pool client, domain (`book-api-{env}-{accountId}`), and callback URLs. Password policy is defined (`MinimumLength: 6, RequireNumbers: true`). User attributes include email. The User Pool acts as both the identity store and the OAuth2 authorization server. |
| **Gap** | No SSO federation with external identity providers (Okta, Azure AD, Google Workspace). The Cognito pool is self-contained — users must register directly. Password policy is weak (minimum length 6, no uppercase or symbols required). No MFA configured. |
| **Recommendation** | If the e-commerce platform has a corporate IdP, configure SAML or OIDC federation in the Cognito User Pool. Strengthen the password policy (minimum 8 characters, require uppercase and symbols). Enable MFA for production users. Consider Amazon Verified Permissions for fine-grained authorization as the API surface grows. |
| **Evidence** | `template.yml` — `CognitoUserPool` with `PasswordPolicy: {MinimumLength: 6}`, `UsernameAttributes: [email]`; `UserPoolClient` with OAuth2 config; `UserPoolDomain`; no federation or MFA configuration |

#### SEC-Q5: Secrets Management

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | GitHub connection ARN is stored in AWS Systems Manager Parameter Store (`StringParameter.fromStringParameterName(this, 'GithubConnectionArn', 'github_connection_arn')` in `pipeline-stack.ts`). No hardcoded credentials found in any source file. DynamoDB table name is passed via environment variable (not a secret — it's a resource reference). No AWS Secrets Manager usage. No secret rotation configured. |
| **Gap** | SSM Parameter Store is used but not AWS Secrets Manager. No secret rotation. The GitHub connection ARN in SSM is a reference, not a credential — but if additional secrets are added in the future, a Secrets Manager pattern should be established. The weak Cognito password policy (SEC-Q4) is a related credential concern. |
| **Recommendation** | Establish an AWS Secrets Manager pattern for any future secrets (third-party API keys, database credentials if RDS is added). Enable automatic rotation for credentials. For the current serverless architecture with only DynamoDB, the secret management needs are minimal — no database passwords exist. |
| **Evidence** | `pipeline/lib/pipeline-stack.ts` — `StringParameter.fromStringParameterName(this, 'GithubConnectionArn', 'github_connection_arn')`; `template.yml` — `Environment.Variables.TABLE: !Ref BooksTable` (not a secret); no hardcoded credentials in `src/books/create/index.ts` or `src/books/get-all/index.ts` |

#### SEC-Q6: Compute Hardening and Patching

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | Lambda runtime (`nodejs22.x`) is fully managed by AWS — runtime patching is automatic and transparent. No EC2 instances or self-managed compute to patch. esbuild minifies and bundles code, reducing the deployed artifact surface. However, no vulnerability scanning (AWS Inspector, Snyk, Trivy) is configured for Lambda functions or dependencies. |
| **Gap** | No vulnerability scanning for Lambda function dependencies. The `aws-sdk` v2 is in maintenance mode (still receives security patches but no new features). No Lambda function URL signing or function-level security policies beyond IAM. |
| **Recommendation** | Enable AWS Inspector for Lambda function scanning (scans dependencies for known CVEs). Add `npm audit` to the build pipeline (`buildspec.json`). Consider Snyk or Dependabot for proactive dependency vulnerability alerts. Migrate from `aws-sdk` v2 to v3 modular SDK. |
| **Evidence** | `template.yml` — `Runtime: nodejs22.x` (managed patching); `src/books/create/package.json` — `aws-sdk: ^2.1692.0` (v2 maintenance mode); no Inspector, Snyk, or Trivy configuration; `pipeline/buildspec.json` — no `npm audit` step |

#### SEC-Q7: Application Security Pipeline

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No security scanning tools are integrated into the CI/CD pipeline. No SAST tools (SonarQube, Semgrep, CodeGuru Reviewer). No dependency scanning (Dependabot, npm audit, Snyk). No container scanning (not applicable — no containers). The pipeline (`buildspec.json`) runs `npm test` for unit tests only. No `.snyk` policy file. No Dependabot configuration (`.github/dependabot.yml`). |
| **Gap** | Pipeline has no security validation step. Vulnerabilities in dependencies (`aws-sdk`, `axios`, `uuid`, `mocha`, etc.) and application code reach production undetected. This is a critical gap for a P1 service in the e-commerce platform. |
| **Recommendation** | Add to `pipeline/buildspec.json` pre_build phase: (1) `npm audit --audit-level=high` to fail builds on high-severity dependency vulnerabilities, (2) Configure Dependabot or Renovate for automated dependency updates, (3) Add CodeGuru Reviewer or Semgrep SAST scanning, (4) Enable AWS Inspector Lambda scanning for runtime vulnerability detection. |
| **Evidence** | `pipeline/buildspec.json` — only `npm test` in pre_build, no security scanning commands; no `.github/dependabot.yml`; no `.snyk`; no SonarQube/Semgrep configuration files; `pipeline/lib/pipeline-stack.ts` — no security scanning CodeBuild project |

### Operations & Observability

#### OPS-Q1: Distributed Tracing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | X-Ray distributed tracing is enabled on all Lambda functions (`Tracing: Active` in `Globals.Function`) and API Gateway (`TracingEnabled: true` on `BooksApi`). The `aws-xray-sdk-core` library is imported in both `create/index.ts` and `get-all/index.ts` with `AWSXRay.captureAWS(AWSCore)` to automatically trace DynamoDB calls. Trace context propagation from API Gateway to Lambda to DynamoDB is configured. Local development bypasses X-Ray (`if (process.env.AWS_SAM_LOCAL)` conditional). |
| **Gap** | This is a single-service application — no cross-service trace propagation to evaluate. Tracing is comprehensive within the service boundary (API Gateway → Lambda → DynamoDB). However, there is no outbound trace context propagation to other services in the e-commerce portfolio. |
| **Recommendation** | As the portfolio grows, ensure trace context (X-Amzn-Trace-Id header) is propagated to downstream services. When EventBridge integration is added (INF-Q4 recommendation), configure trace context forwarding in event metadata. Consider migrating to OpenTelemetry for vendor-neutral instrumentation. |
| **Evidence** | `template.yml` — `Globals.Function.Tracing: Active`, `BooksApi.TracingEnabled: true`; `src/books/create/index.ts` — `import * as AWSXRay from 'aws-xray-sdk-core'`, `AWSXRay.captureAWS(AWSCore)`; `src/books/get-all/index.ts` — same X-Ray instrumentation; `src/books/create/package.json` — `aws-xray-sdk-core: ^3.10.3` |

#### OPS-Q2: SLO Definitions

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | CloudWatch alarms exist for Lambda error metrics (`CreateBookAliasErrorMetricGreaterThanZeroAlarm` and `GetAllBooksAliasErrorMetricGreaterThanZeroAlarm`), configured with `ComparisonOperator: GreaterThanThreshold`, `Threshold: 0`, `Period: 60`, `EvaluationPeriods: 2`. However, these alarms serve only as deployment safety gates (triggering rollback during canary deployments), not as SLO monitors. No p99/p95 latency alarms. No error budget tracking. No SLO definitions. |
| **Gap** | No formal SLO definitions for the API. The deployment alarms are binary (any error triggers rollback) rather than SLO-based (error rate exceeds budget). No latency targets defined. No error budget tracking. |
| **Recommendation** | Define SLOs for critical operations: (1) GET /books availability ≥ 99.9%, (2) GET /books p99 latency < 500ms, (3) POST /books availability ≥ 99.9%. Add CloudWatch alarms for p99 latency and error rate percentages. Implement error budget tracking using CloudWatch math expressions or a dedicated SLO tool. |
| **Evidence** | `template.yml` — `CreateBookAliasErrorMetricGreaterThanZeroAlarm` and `GetAllBooksAliasErrorMetricGreaterThanZeroAlarm` with `Threshold: 0` (deployment safety, not SLOs); no SLO definitions, no latency alarms |

#### OPS-Q3: Business Metrics

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No custom business metrics published. Lambda functions in `create/index.ts` and `get-all/index.ts` do not call `cloudwatch.putMetricData()` or emit any custom metrics. The application relies entirely on default infrastructure metrics from Lambda (invocations, errors, duration, throttles) and API Gateway (count, latency, 4xx, 5xx). |
| **Gap** | No business outcome metrics. Cannot measure: books created per hour, unique books viewed, API error rates by operation type, book creation success/failure rates, or any business KPIs. This limits the ability to make data-driven modernization decisions. |
| **Recommendation** | Add custom CloudWatch metrics in Lambda handlers: (1) `BooksCreated` counter in `create/index.ts` after successful putItem, (2) `BooksRetrieved` counter with book count dimension in `get-all/index.ts`, (3) `CreateBookValidationErrors` for malformed requests. Use CloudWatch Embedded Metrics Format (EMF) for zero-latency metric emission from Lambda. |
| **Evidence** | `src/books/create/index.ts` — no `putMetricData` or EMF calls; `src/books/get-all/index.ts` — no custom metrics; no CloudWatch dashboard definitions in IaC |

#### OPS-Q4: Anomaly Detection and Alerting

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Static threshold alarms exist: `CreateBookAliasErrorMetricGreaterThanZeroAlarm` and `GetAllBooksAliasErrorMetricGreaterThanZeroAlarm` trigger on `Errors > 0` with 2 evaluation periods of 60 seconds each. These are deployment rollback alarms, not operational alerting. No anomaly detection (`AWS::CloudWatch::AnomalyDetector`). No latency-based alarms. No composite alarms. No PagerDuty/OpsGenie integration. |
| **Gap** | No anomaly detection on error rates or latency. Static threshold alarms (error > 0) are binary and designed for deployment, not operational monitoring. Gradual degradation (increasing latency, rising error rate below 100%) would not be detected. |
| **Recommendation** | Add CloudWatch anomaly detection on Lambda duration and error rate metrics for both functions. Add latency p99 alarms on API Gateway. Configure SNS topics for alarm notification routing to an on-call team. Consider composite alarms that combine error rate and latency signals. |
| **Evidence** | `template.yml` — `CreateBookAliasErrorMetricGreaterThanZeroAlarm`: `ComparisonOperator: GreaterThanThreshold, Threshold: 0, Period: 60`; same for `GetAllBooksAliasErrorMetricGreaterThanZeroAlarm`; no `AWS::CloudWatch::AnomalyDetector`; no SNS alarm actions |

#### OPS-Q5: Deployment Strategy

| Field | Value |
|-------|-------|
| **Score** | 4 |
| **Finding** | Production uses `Linear10PercentEvery1Minute` canary deployment via CodeDeploy (configured per Lambda function's `DeploymentPreference`). Traffic gradually shifts from the old version to the new version over 10 minutes. CloudWatch alarms monitor for errors during deployment — any error triggers automatic rollback. The `CreateBook` function has a pre-traffic hook (`CreateBookPreTraffic`) that performs a smoke test before any traffic is shifted: it invokes the new Lambda version, verifies the book was created in DynamoDB, and cleans up test data. Staging uses `AllAtOnce` for faster iteration. |
| **Gap** | None. The deployment strategy is mature: canary with automated rollback and pre-traffic validation. |
| **Recommendation** | No action needed for the current service. As the portfolio grows, consider adopting a GitOps approach (preferred per technology preferences) for coordinated deployments across services. |
| **Evidence** | `template.yml` — `DeploymentPreference.Type: !If [IsProduction, Linear10PercentEvery1Minute, AllAtOnce]`; `Hooks.PreTraffic: !Ref CreateBookPreTraffic`; `Alarms: [!Ref CreateBookAliasErrorMetricGreaterThanZeroAlarm]`; `src/books/create-pre-traffic/index.ts` — smoke test with Lambda invoke, DynamoDB getItem verification, and cleanup |

#### OPS-Q6: Integration Testing

| Field | Value |
|-------|-------|
| **Score** | 3 |
| **Finding** | End-to-end tests exist in `src/books/tests/index.js` using Mocha and Chai. Tests interact with the live API: create Cognito user, obtain OAuth2 token, test GET /books (public access, returns books), test POST /books (requires auth, rejects without token, validates schema, creates book and verifies in DynamoDB). Tests run in the CI pipeline after staging deployment (`pipeline/buildspec-test.json`). Unit tests run during build stage (`buildspec.json` — `npm test` in create/ and get-all/). Test helper `books-manager.js` manages test data in DynamoDB. |
| **Gap** | E2e tests cover the 2 existing endpoints but with limited edge case coverage. No load testing. No contract testing. No test coverage reporting. The test timeout is 5 seconds (`--timeout 5000`), which may be tight for cold-start scenarios. |
| **Recommendation** | Add test coverage reporting to the pipeline. Consider contract tests (Pact) as the customer support agent begins consuming this API. Add load testing (Artillery or k6) to validate performance under the expected e-commerce traffic patterns. |
| **Evidence** | `src/books/tests/index.js` — Mocha/Chai e2e tests with Cognito auth, API calls via axios, DynamoDB verification; `src/books/tests/books-manager.js` — test data helper; `pipeline/buildspec-test.json` — `npm test` after staging deploy; `pipeline/buildspec.json` — `npm test` for unit tests in build stage |

#### OPS-Q7: Incident Response Automation

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No runbooks found in the repository (no markdown, YAML, or JSON runbook files). No SSM Automation documents. No Lambda-based remediation functions (beyond the pre-traffic hook, which is a deployment utility). No incident response automation. No self-healing patterns. The deployment rollback via CloudWatch alarms is the only automated recovery mechanism. |
| **Gap** | Incident response is entirely manual and ad hoc. No documented procedures for common incidents (DynamoDB throttling, Lambda cold start spikes, API Gateway 5xx errors). No automated remediation for any failure scenario. |
| **Recommendation** | Create runbooks (markdown or SSM Automation documents) for: (1) DynamoDB throttling — switch to provisioned capacity or increase on-demand limits, (2) Lambda error spike — check recent deployment, trigger rollback, (3) API Gateway 5xx — check Lambda errors, DynamoDB health. Consider automated remediation via EventBridge rules triggering Lambda functions for common failure patterns. |
| **Evidence** | No runbook files in repository; no `AWS::SSM::Document` resources in `template.yml`; no remediation Lambda functions; deployment rollback alarms are the only automated recovery |

#### OPS-Q8: Observability Ownership

| Field | Value |
|-------|-------|
| **Score** | 1 |
| **Finding** | No CODEOWNERS file in the repository. No per-service CloudWatch dashboards defined in IaC. CloudWatch alarms exist (`CreateBookAliasErrorMetricGreaterThanZeroAlarm`, `GetAllBooksAliasErrorMetricGreaterThanZeroAlarm`) but have no named owners, team attribution, or SNS notification targets. No SLO definitions with team attribution. No alarm action configured (no SNS topic ARN in alarm actions). |
| **Gap** | No observability ownership. Alarms exist but route to nobody — they only serve as deployment rollback triggers. No team is explicitly responsible for monitoring the books-api health. No dashboards to visualize service health at a glance. |
| **Recommendation** | Add a CODEOWNERS file assigning the books-api team to observability configs. Create a CloudWatch dashboard in IaC with Lambda metrics (invocations, errors, duration, throttles), API Gateway metrics (count, latency, 4xx, 5xx), and DynamoDB metrics (consumed capacity, throttled requests). Add SNS topics as alarm actions to route alerts to the on-call team. Tag alarms with `owner: books-api-team`. |
| **Evidence** | No `.github/CODEOWNERS` file; `template.yml` — CloudWatch alarms with no `AlarmActions` (no SNS topic); no `AWS::CloudWatch::Dashboard` resources |

#### OPS-Q9: Resource Tagging Governance

| Field | Value |
|-------|-------|
| **Score** | 2 |
| **Finding** | Tags are present on Lambda functions via `Globals.Function.Tags: {project: my-project, environment: !Ref Stage}` and on the DynamoDB table (`BooksTable.Tags: {project: my-project, environment: !Ref Stage}`). The `CreateBookPreTraffic` function has explicit tags matching the global pattern. However, only 2 tag keys exist (`project`, `environment`). No cost allocation tags (e.g., `cost-center`, `business-unit`). No ownership tags. Pipeline S3 buckets in `pipeline-stack.ts` have no tags. No tag enforcement (no Config rules, no Tag Policies). |
| **Gap** | Inconsistent tagging — only 2 tag keys on Lambda and DynamoDB, zero tags on pipeline S3 buckets. No cost allocation, ownership, or compliance tags. The `project: my-project` value is a placeholder, not meaningful for cost attribution. No tag enforcement mechanism. |
| **Recommendation** | Define a tagging standard for the e-commerce portfolio with required keys: `project`, `environment`, `cost-center`, `owner`, `service`. Apply tags to all resources including pipeline S3 buckets. Add `default_tags` in CDK or SAM `Globals`. Consider AWS Config `required-tags` rule and AWS Organizations Tag Policies for enforcement. |
| **Evidence** | `template.yml` — `Globals.Function.Tags: {project: my-project, environment: !Ref Stage}`; `BooksTable.Tags: {project: my-project, environment: !Ref Stage}`; `pipeline/lib/pipeline-stack.ts` — S3 buckets with no tags; no Config rules or Tag Policies |

---

## Learning Materials

| Pathway | Learning Resources |
|---------|-------------------|
| **Move to AI** | [Move to AI Learning Plan](https://skillbuilder.aws/learning-plan/VDFEE4ACCV) · [Amazon Bedrock Getting Started](https://skillbuilder.aws/learn/63KTRM86DQ) · [Introduction to Agentic AI on AWS](https://skillbuilder.aws/learn/DNBD5MT8ZD) |

Only the Move to AI pathway was triggered. No other pathway-specific learning materials are applicable. For general cloud architecture training, refer to the [AWS SkillBuilder](https://skillbuilder.aws/) catalog.

---

## Evidence Index

### Root Directory

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `template.yml` | INF-Q1, INF-Q2, INF-Q3, INF-Q4, INF-Q5, INF-Q6, INF-Q7, INF-Q8, INF-Q9, INF-Q10, INF-Q11, APP-Q2, APP-Q3, APP-Q4, APP-Q5, APP-Q6, DATA-Q1, DATA-Q3, DATA-Q4, SEC-Q1, SEC-Q2, SEC-Q3, SEC-Q4, SEC-Q5, OPS-Q1, OPS-Q2, OPS-Q4, OPS-Q5, OPS-Q8, OPS-Q9 | SAM/CloudFormation template defining all application infrastructure: Lambda functions, API Gateway, DynamoDB table, Cognito User Pool, CloudWatch alarms, deployment preferences |
| `README.md` | Quick Agent Wins (RAG) | Comprehensive project documentation (200+ lines) covering architecture, deployment, testing, monitoring, tracing, and CI/CD |

### Source Code (`src/books/`)

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `src/books/create/index.ts` | INF-Q4, APP-Q1, APP-Q3, APP-Q4, DATA-Q2, DATA-Q4, OPS-Q1, OPS-Q3, SEC-Q5 | CreateBook Lambda handler — DynamoDB putItem with X-Ray tracing |
| `src/books/create/package.json` | APP-Q1, SEC-Q6 | Dependencies: aws-sdk v2.1692.0, aws-xray-sdk-core v3.10.3 |
| `src/books/get-all/index.ts` | INF-Q4, APP-Q1, APP-Q3, APP-Q4, DATA-Q2, DATA-Q4, OPS-Q1, OPS-Q3 | GetAllBooks Lambda handler — DynamoDB scan with X-Ray tracing |
| `src/books/get-all/package.json` | APP-Q1 | Dependencies: aws-sdk v2.1692.0, aws-xray-sdk-core v3.10.3 |
| `src/books/create-pre-traffic/index.ts` | INF-Q3, APP-Q4, DATA-Q2, OPS-Q5 | Pre-traffic smoke test hook — Lambda invoke, DynamoDB getItem/deleteItem |
| `src/books/create-pre-traffic/package.json` | APP-Q1 | Dependencies: aws-sdk v2.1692.0 |
| `src/books/tests/index.js` | OPS-Q6 | E2E tests — Mocha/Chai testing API endpoints with Cognito auth via axios |
| `src/books/tests/books-manager.js` | DATA-Q2, OPS-Q6 | Test data helper — DynamoDB batchWriteItem, getItem, deleteItem |
| `src/books/tests/package.json` | OPS-Q6 | Test dependencies: aws-sdk, axios, uuid, chai, mocha |

### Pipeline (`pipeline/`)

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `pipeline/lib/pipeline-stack.ts` | INF-Q10, INF-Q11, DATA-Q1, SEC-Q2, SEC-Q5, OPS-Q9 | CDK pipeline definition: CodePipeline with Source/Build/Staging/Production stages, S3 buckets |
| `pipeline/buildspec.json` | INF-Q11, SEC-Q6, SEC-Q7, OPS-Q6 | Build stage: SAM build, unit tests (npm test), package to S3 |
| `pipeline/buildspec-deploy.json` | INF-Q11 | Deploy stage: SAM deploy with stage parameter, export CloudFormation outputs |
| `pipeline/buildspec-test.json` | INF-Q11, OPS-Q6 | Test stage: E2E tests after staging deployment |
| `pipeline/package.json` | APP-Q1 | CDK dependencies: aws-cdk-lib v2.189.1, TypeScript v5.7.3 |
| `pipeline/cdk.json` | INF-Q10 | CDK app entry point configuration |

### Events (`events/`)

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| `events/env.json` | APP-Q6 | Local development environment variables (TABLE: books) |
