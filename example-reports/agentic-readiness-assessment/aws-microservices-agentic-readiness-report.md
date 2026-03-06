# Agentic Readiness Assessment Report
**Target**: ./services/aws-microservices
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

This aws-microservices project demonstrates a solid event-driven serverless foundation with three well-separated microservices (product, basket, ordering) using AWS Lambda, DynamoDB, EventBridge, and SQS — all defined in CDK. However, the application has critical gaps in security (no API authentication, no secret management), operations (no CI/CD, no observability, no testing), and application resilience (no idempotency, no retry/circuit breaker patterns, no API versioning). The deprecated Node.js 14.x Lambda runtime is an immediate security and support risk. While the architecture is well-decomposed for agentic workloads, the absence of DevOps foundations, security controls, and AI/data capabilities means significant investment is needed before agents can be safely deployed.

### Overall Score: 1.8 / 4.0

| Category | Score | Status |
|----------|-------|--------|
| Infrastructure & Platform | 2.6 / 4.0 | 🟡 |
| Application Architecture | 1.8 / 4.0 | 🟠 |
| Data Foundations | 2.0 / 4.0 | 🟠 |
| Identity, Security & Governance | 1.4 / 4.0 | ❌ |
| Operations & Observability | 1.1 / 4.0 | ❌ |

## Top Priorities (Critical Gaps)

**1. No CI/CD Pipeline (INF-Q6 — Score: 1/4)**
There are no CI/CD definitions (no `.github/workflows/`, no `buildspec.yml`, no `Jenkinsfile`) in the repository. Deployments rely on manual `cdk deploy`. For agentic workloads, automated pipelines are essential because agents require frequent, safe iteration on prompts, tools, and guardrails — manual deployments create unacceptable risk and slow velocity. **First step**: Create a GitHub Actions workflow or AWS CodePipeline with `cdk diff` → `cdk deploy` stages, including automated CDK snapshot tests.

**2. No API Authentication or Authorization (SEC-Q9 — Score: 1/4)**
All three API Gateway endpoints (`productApi`, `basketApi`, `orderApi`) in `lib/apigateway.ts` have no authorizers, no API keys, and no usage plans configured. Any internet-connected client can invoke all operations including DELETE and checkout. Agents must interact with authenticated APIs to ensure identity propagation and access control. **First step**: Add a Cognito User Pool authorizer or Lambda authorizer to all API Gateway methods in `lib/apigateway.ts`.

**3. No Distributed Tracing or Structured Observability (OPS-Q1 — Score: 1/4)**
No X-Ray tracing, OpenTelemetry, or any tracing SDK is present. Lambda handlers use bare `console.log` and `console.error` with no correlation IDs. When agents orchestrate multi-step workflows across product, basket, and ordering services, tracing the full execution path is critical for debugging and safety. **First step**: Enable X-Ray active tracing on all Lambda functions in `lib/microservice.ts` by adding `tracing: Tracing.ACTIVE` to the function props.

**4. No Resilience Patterns — Retry, Circuit Breaker, Timeout (APP-Q9 — Score: 1/4)**
None of the three Lambda handlers (`src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js`) implement retry logic, circuit breakers, or explicit timeout handling. The `checkoutBasket` function in `src/basket/index.js` calls DynamoDB, EventBridge, and DynamoDB again sequentially with no error recovery — a partial failure could publish an event but fail to delete the basket. Agents retry by default, and without idempotency and resilience patterns, retries will cause duplicate orders and data corruption. **First step**: Add the `@aws-sdk/middleware-retry` configuration with exponential backoff and implement idempotency on the `createOrder` function using DynamoDB conditional writes.

**5. Deprecated Lambda Runtime — Node.js 14.x End-of-Life (INF-Q1 related)**
All three Lambda functions in `lib/microservice.ts` use `Runtime.NODEJS_14_X`, which reached AWS end-of-life and no longer receives security patches. The `bundling.externalModules: ['aws-sdk']` configuration is also incorrect for Node.js 18+ which uses AWS SDK v3 bundled differently. Running agents on an unsupported runtime introduces security vulnerabilities and compatibility risks. **First step**: Update all three Lambda functions in `lib/microservice.ts` from `Runtime.NODEJS_14_X` to `Runtime.NODEJS_20_X` and remove the `aws-sdk` external modules configuration.

## Readiness Roadmap

> The architecture is already well-decomposed into three microservices (product, basket, ordering) with clear service boundaries, separate DynamoDB tables, and event-driven communication via EventBridge + SQS. The Microservices Decomposition Strategy section below focuses on strengthening these existing boundaries rather than decomposition.

### Microservices Decomposition Strategy

The application already scores 4/4 on APP-Q4 (Microservices) — three independently deployable Lambda functions with per-service DynamoDB tables and async decoupling via EventBridge. No decomposition is needed. The focus should be on hardening the existing boundaries:

**Current Architecture Strengths:**
- ✅ Three separate Lambda functions: `productLambdaFunction`, `basketLambdaFunction`, `orderingLambdaFunction` (in `lib/microservice.ts`)
- ✅ Per-service DynamoDB tables: `product`, `basket`, `order` (in `lib/database.ts`)
- ✅ Async decoupling via EventBridge → SQS for checkout flow (in `lib/eventbus.ts`, `lib/queue.ts`)
- ✅ Separate API Gateway endpoints per service (in `lib/apigateway.ts`)

**Recommended: Strengthen Existing Boundaries**
- **LoE**: Low | **Risk**: Low | **Time to Value**: Fast
- **Focus Areas**: Add API versioning, OpenAPI specs, idempotency, resilience patterns, and service-level observability to each microservice independently
- **Pattern**: [API Gateway Routing](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/api-routing.html) for adding throttling and auth per service

**Pattern Recommendations Based on Your Architecture:**

- **Event-Driven Hardening**: The existing EventBridge → SQS checkout flow should implement [Transactional Outbox](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html) pattern to prevent the partial failure in `checkoutBasket` (event published but basket not deleted)
  - **Why**: The `checkoutBasket` function in `src/basket/index.js` performs 3 sequential operations (get basket → publish event → delete basket) with no atomicity guarantee

- **Resilience First**: Implement [Circuit Breaker](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/circuit-breaker.html) + [Retry with Backoff](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/retry-backoff.html) on all DynamoDB and EventBridge calls
  - **Why**: Agent-driven traffic patterns are bursty; without resilience, DynamoDB throttling or EventBridge failures will cascade

- **Saga Orchestration**: Consider [Saga Orchestration](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga-orchestration.html) via Step Functions for the checkout workflow to replace the current fire-and-forget EventBridge pattern
  - **Why**: The current checkout flow has no compensation logic if order creation fails after basket deletion; Step Functions would provide built-in retry, rollback, and visibility

### Phase 1 — Quick Wins (Days 1–30)

1. **Upgrade Lambda Runtime**: Update all three Lambda functions from `Runtime.NODEJS_14_X` to `Runtime.NODEJS_20_X` in `lib/microservice.ts`; remove the `externalModules: ['aws-sdk']` bundling config (not needed with Node.js 18+ which bundles SDK v3)
2. **Set Up CI/CD Pipeline**: Create a GitHub Actions workflow (or CodePipeline) with stages: lint → CDK synth → CDK diff → CDK deploy to dev → integration tests → CDK deploy to prod
3. **Add API Gateway Authentication**: Configure Cognito User Pool or IAM authorizer on all API methods in `lib/apigateway.ts`; at minimum add API keys and usage plans for rate limiting
4. **Enable X-Ray Tracing**: Add `tracing: Tracing.ACTIVE` to all Lambda function props in `lib/microservice.ts` and enable X-Ray on API Gateway stages
5. **Add Structured Logging**: Replace `console.log`/`console.error` in all handlers with a structured logging library (e.g., `@aws-lambda-powertools/logger`) that outputs JSON with correlation IDs
6. **Remove Stack Traces from Error Responses**: Remove `errorStack: e.stack` from all three handlers' catch blocks to prevent information leakage

### Phase 2 — Foundation (Months 1–3)

1. **Implement Resilience Patterns**: Add retry with exponential backoff, timeouts, and error handling to all DynamoDB and EventBridge SDK calls using AWS Lambda Powertools or custom middleware
2. **Add Idempotency**: Implement idempotency on `createProduct` (`src/product/index.js`), `createBasket` (`src/basket/index.js`), `createOrder` (`src/ordering/index.js`) using `@aws-lambda-powertools/idempotency` with DynamoDB backend
3. **Create OpenAPI Specifications**: Document all three APIs (product, basket, ordering) with OpenAPI 3.0 specs; configure API Gateway to use these specs for request validation
4. **Add API Versioning**: Implement URL path versioning (`/v1/product`, `/v1/basket`, `/v1/order`) in `lib/apigateway.ts`
5. **Implement Workflow Orchestration**: Replace the fire-and-forget checkout flow with AWS Step Functions to orchestrate the checkout saga (validate basket → reserve inventory → publish event → create order → delete basket) with compensation steps
6. **Configure Network Security**: Add VPC configuration for Lambda functions with private subnets and VPC endpoints for DynamoDB and EventBridge
7. **Set Up CloudWatch Alarms and SLOs**: Define SLOs for API latency (p99 < 1s) and error rate (< 1%); create CloudWatch alarms for each service
8. **Enable Encryption**: Add customer-managed KMS keys for DynamoDB tables in `lib/database.ts`
9. **Write Integration Tests**: Uncomment and expand `test/aws-microservices.test.ts`; add CDK assertion tests and API integration tests

### Phase 3 — Agent Enablement (Months 3–6)

1. **Introduce Vector Database**: Add Amazon OpenSearch Service with k-NN plugin or Amazon Bedrock Knowledge Bases for product search and recommendation capabilities
2. **Implement RAG Pipeline**: Create an embedding pipeline for product catalog data; enable semantic search across products
3. **Add Agent Framework**: Integrate Strands Agents SDK or Amazon Bedrock Agents to create an e-commerce assistant agent that can query products, manage baskets, and process orders via the existing APIs
4. **Implement Automated Evals**: Create golden datasets for agent interactions; set up eval pipelines to measure agent accuracy on product queries and checkout flows
5. **Add LLM Cost Tracking**: Implement per-request token usage tracking with CloudWatch custom metrics and attribution by user/workflow
6. **Set Up Business Metrics**: Publish custom CloudWatch metrics for checkout success rate, average order value, basket abandonment rate
7. **Implement Human Approval Workflow**: Add Step Functions with human approval tasks for high-value orders or bulk operations that agents might trigger
8. **Add Anomaly Detection**: Enable CloudWatch anomaly detection on error rates and latency for all three services

## Recommended Modernization Pathways

Based on the assessment findings, the following AWS Modernization Pathways are recommended for this application. Multiple pathways can execute in parallel because modern applications comprise multiple interconnected components — each requiring its own modernization approach.

### Pathway Summary

| Pathway | Triggered | Priority | Key Trigger Criteria | Est. Effort |
|---------|-----------|----------|---------------------|-------------|
| Move to Cloud Native | Yes | Medium | APP-Q3=2 (sync-heavy), APP-Q10=2 (no async for long-running) | Medium |
| Move to Containers | No | N/A | Already fully serverless Lambda (INF-Q1=4); no Dockerfile but not needed | N/A |
| Move to Open Source | No | N/A | DynamoDB (no commercial DB), no proprietary SQL (DATA-Q11=4) | N/A |
| Move to Managed Databases | No | N/A | Already fully managed DynamoDB (INF-Q2=4, DATA-Q10=4) | N/A |
| Move to Managed Analytics | Yes | Low | INF-Q8=2 (no managed streaming) | Low |
| Move to Modern DevOps | Yes | High | INF-Q6=1 (no CI/CD), OPS-Q1=1 (no tracing), OPS-Q9=1 (no deployment strategy), OPS-Q10=1 (no testing) | High |
| Move to AI | Yes | Medium | APP-Q13=1 (no agent frameworks), DATA-Q1=1 (no vector DB), DATA-Q3=1 (no RAG), OPS-Q3=1 (no evals) | Medium |

### Parallel Execution Plan

**Parallel Track 1 — Immediate (Phase 1)**: Move to Modern DevOps — CI/CD, tracing, structured logging, deployment strategy. No dependencies.

**Parallel Track 2 — Foundation (Phase 2)**: Move to Cloud Native — Step Functions for workflow orchestration, expand async patterns. Can run in parallel with Track 1.

**Parallel Track 3 — Data & AI (Phase 3)**: Move to AI + Move to Managed Analytics — Vector DB, RAG, agent frameworks, streaming.

**Sequential Dependencies**:
- Move to Modern DevOps should be substantially complete before Move to AI (agents need CI/CD, observability, and testing infrastructure)
- Move to Cloud Native (Step Functions) should precede Move to AI (agents benefit from orchestrated workflows)
- Move to Managed Analytics is independent and low priority; can run anytime

---

### Move to Cloud Native

- **Priority**: Medium
- **Trigger Criteria Met**:
  - APP-Q3: Score 2/4 — Only ~20% of communication is async (checkout flow only); all CRUD operations are synchronous API Gateway → Lambda → DynamoDB
  - APP-Q10: Score 2/4 — Checkout is async via EventBridge but has no status polling endpoint or callback mechanism
- **Current State**: The application is already serverless (Lambda + DynamoDB + EventBridge + SQS) and microservices-based (3 independent services). However, it is sync-heavy and lacks workflow orchestration. The checkout flow is async but has no compensation, status tracking, or saga pattern.
- **Target State**: Step Functions orchestrating the checkout saga; async patterns for all operations over 30 seconds; status polling APIs for long-running operations; expanded EventBridge usage for inter-service communication beyond checkout.
- **Key Activities**:
  1. Introduce AWS Step Functions for checkout workflow orchestration with compensation steps
  2. Add status polling endpoint for checkout operations in ordering service
  3. Expand EventBridge patterns for product catalog change events (e.g., price updates, inventory changes)
  4. Implement async notification patterns for order status updates
- **Dependencies**: None (already serverless)
- **Estimated Effort**: Medium
- **Roadmap Phase Alignment**: Phase 2 (Foundation) and Phase 3 (Agent Enablement)
- **Relevant Learning Materials**: Module 2 — Move to Cloud Native (Containers and Serverless)

### Move to Modern DevOps

- **Priority**: High
- **Trigger Criteria Met**:
  - INF-Q6: Score 1/4 — No CI/CD pipeline exists; deployment is manual `cdk deploy`
  - OPS-Q1: Score 1/4 — No distributed tracing (no X-Ray, no OpenTelemetry)
  - OPS-Q9: Score 1/4 — No deployment strategy; direct `cdk deploy` to production
  - OPS-Q10: Score 1/4 — Test file (`test/aws-microservices.test.ts`) is entirely commented out
  - INF-Q5: Score 3/4 — CDK IaC is solid but missing network resources
- **Current State**: No CI/CD automation, no observability stack, no testing, no deployment safety. CDK IaC provides good infrastructure coverage but is deployed manually with no guardrails.
- **Target State**: Full CI/CD pipeline with automated test, build, and deploy stages; X-Ray distributed tracing across all services; structured JSON logging with correlation IDs; canary deployments with automated rollback; comprehensive integration test suite.
- **Key Activities**:
  1. Create CI/CD pipeline (GitHub Actions or CodePipeline) with CDK synth → test → diff → deploy stages
  2. Enable X-Ray active tracing on all Lambda functions and API Gateway
  3. Implement structured logging with `@aws-lambda-powertools/logger`
  4. Add CDK assertion tests and API integration tests
  5. Configure Lambda alias-based traffic shifting for canary deployments
  6. Set up CloudWatch dashboards and alarms for each service
  7. Create CloudWatch Synthetics canaries for API health monitoring
- **Dependencies**: None — this is the foundation for all other pathways
- **Estimated Effort**: High
- **Roadmap Phase Alignment**: Phase 1 (Quick Wins) for CI/CD and tracing, Phase 2 for advanced deployment and testing
- **Relevant Learning Materials**: Module 6 — Move to Modern DevOps

### Move to Managed Analytics

- **Priority**: Low
- **Trigger Criteria Met**:
  - INF-Q8: Score 2/4 — EventBridge provides event routing but no managed streaming service (Kinesis, MSK) for real-time data analytics
- **Current State**: EventBridge handles event routing for checkout flow. No streaming analytics for real-time order tracking, inventory monitoring, or user behavior analysis.
- **Target State**: Kinesis Data Streams or MSK Serverless for real-time order event streaming; analytics pipeline for business intelligence on order patterns and product trends.
- **Key Activities**:
  1. Evaluate need for real-time streaming (order analytics, inventory tracking)
  2. If needed, add Kinesis Data Streams for order events alongside existing EventBridge flow
  3. Set up Kinesis Data Firehose to S3 for order analytics data lake
- **Dependencies**: None
- **Estimated Effort**: Low
- **Roadmap Phase Alignment**: Phase 2 (Foundation) if needed
- **Relevant Learning Materials**: Module 5 — Move to Managed Analytics

### Move to AI

- **Priority**: Medium
- **Trigger Criteria Met**:
  - APP-Q13: Score 1/4 — No AI/agent frameworks in any `package.json`; no Bedrock, LangChain, or Strands Agents SDK
  - DATA-Q1: Score 1/4 — No vector database for semantic product search
  - DATA-Q3: Score 1/4 — No RAG pipeline for product catalog
  - OPS-Q3: Score 1/4 — No automated evaluation framework
  - OPS-Q6: Score 1/4 — No LLM cost tracking
- **Current State**: No AI capabilities. The application is a traditional e-commerce CRUD system with no semantic search, product recommendations, or conversational interfaces.
- **Target State**: AI-powered product discovery via RAG on product catalog; conversational checkout agent using Strands Agents or Bedrock Agents; automated eval pipeline with golden datasets; per-request LLM cost tracking with user attribution.
- **Key Activities**:
  1. Add Amazon Bedrock Knowledge Base backed by DynamoDB product catalog or S3 product data
  2. Implement vector embeddings for product catalog using Bedrock Titan Embeddings
  3. Create agent tools wrapping existing product, basket, and ordering APIs
  4. Integrate Strands Agents SDK or Amazon Bedrock Agents for conversational e-commerce
  5. Build eval datasets for product search accuracy and checkout flow completion
  6. Implement LLM token usage tracking with CloudWatch custom metrics
- **Dependencies**: Move to Modern DevOps (need CI/CD and observability first); Move to Cloud Native (Step Functions for agent workflow orchestration)
- **Estimated Effort**: Medium
- **Roadmap Phase Alignment**: Phase 3 (Agent Enablement)
- **Relevant Learning Materials**: Module 7 — Move to AI

## Recommended Self-Paced Learning Materials

**Module 2: Move to Cloud Native (Containers and Serverless):**
- Cloud Design Patterns, Architectures, and Implementations — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html
  - Essential reference for strengthening microservices boundaries: Strangler Fig, Saga Orchestration, Transactional Outbox, Circuit Breaker, Retry with Backoff patterns directly applicable to the checkout flow improvements
- AWS Modernization Pathways: Move to Cloud Native Serverless — https://skillbuilder.aws/learning-plan/CMK2J48MVN/aws-modernization-pathways-move-to-cloud-native-serverless-includes-labs/EFUPP53B4Q
- Lambda Foundations — https://skillbuilder.aws/learn/XHRS91KKK6/aws-lambda-foundations/R85JRN3APC
- Architecting Serverless Applications — https://skillbuilder.aws/learn/MRWENY7FSX/architecting-serverless-applications/QVFY2JHVEH
- Amazon API Gateway for Serverless Applications — https://skillbuilder.aws/learn/GQA6FHWPJD/amazon-api-gateway-for-serverless-applications/JVRZ3PSW4H
- Deploying Serverless Applications — https://skillbuilder.aws/learn/M531VCW415/deploying-serverless-applications/SMY21G7FYZ
- Amazon DynamoDB for Serverless Architecture — https://skillbuilder.aws/learn/SY1Y83VKTB/amazon-dynamodb-for-serverless-architectures/K9NM3PHH3S

**Module 5: Move to Managed Analytics:**
- AWS Modernization Pathways: Move to Managed Analytics — https://skillbuilder.aws/learning-plan/RWZA84NMVV/aws-modernization-pathways-move-to-managed-analytics--includes-labs/9BAKK2QQQU

**Module 6: Move to Modern DevOps:**
- AWS Modernization Pathways: Move to Modern DevOps — https://skillbuilder.aws/learning-plan/1FGEQKGPQD/aws-modernization-pathways-move-to-modern-devops-includes-labs/MNQZ2KPVCK
- Getting Started with DevOps on AWS — https://skillbuilder.aws/learn/R4B13K95YQ/getting-started-with-devops-on-aws/38NHHYRV1R
- Create a CI/CD Pipeline to Deploy Your App to AWS Fargate (ECS) — https://skillbuilder.aws/learn/H61B17Z8R7/create-a-cicd-pipeline-to-deploy-your-app-to-aws-fargate/T66BGGGHV5
- AWS CloudFormation Getting Started — https://skillbuilder.aws/learn/RH22P2RXU4/aws-cloudformation-getting-started/KEK5BT6HSE
- Advanced Testing Practices Using AWS DevOps Tools — https://skillbuilder.aws/learn/1YC7UXUWBR/advanced-testing-practices-using-aws-devops-tools/A32U6G7NEQ
- AWS Developer: CI/CD Automation — https://skillbuilder.aws/learn/C1KF8ZJ1D8/aws-developer--cicd-automation/KY1E1JS9FA

**Module 7: Move to AI:**
- AWS Modernization Pathways: Move to AI — https://skillbuilder.aws/learning-plan/VDFEE4ACCV/aws-modernization-pathways-move-to-ai-pathways-includes-labs/P3DAWPTN63
- Introduction to Generative AI: Art of the Possible — https://skillbuilder.aws/learn/ZEVZZ1D4AS/introduction-to-generative-ai--art-of-the-possible/Y7MTGJCW1U
- Planning a Generative AI Project — https://skillbuilder.aws/learn/HU1FQRGDDZ/planning-a-generative-ai-project/SYR3SCPSHC
- Amazon Bedrock Getting Started — https://skillbuilder.aws/learn/63KTRM86DQ/amazon-bedrock-getting-started/SC2Y3HMAUE
- Essentials for Prompt Engineering — https://skillbuilder.aws/learn/XBNAVKA88J/essentials-of-prompt-engineering/9T9Q45EDTV
- Build and Evaluate Retrieval Augmented Generation (RAG) Applications using Knowledge Bases for Amazon Bedrock (Lab) — https://skillbuilder.aws/learn/JRGWCFYT67/lab--build-and-evaluate-retrieval-augmented-generation-rag-applications-using-knowledge-bases-for-amazon-bedrock/A4MN58JB7A
- Introduction to Agentic AI on AWS — https://skillbuilder.aws/learn/DNBD5MT8ZD/introduction-to-agentic-ai-on-aws/WAKAFK6UFY
- Creating an AWS DevOps AI Agent with the Strands Agents SDK (Lab) — https://skillbuilder.aws/learn/AH1GD8AJY3/lab--creating-an-aws-devops-ai-agent-with-the-strands-agents-sdk/A9SKJNMPJ2
- AWS PartnerCast: Deep Dive: Building Observable AI Agents with Strands, Amazon Bedrock Agent Core & SageMaker MLflow — https://skillbuilder.aws/learn/1EN76TZBB6/aws-partnercast--deep-dive-building-observable-ai-agents-with-strands-amazon-bedrock-agent-core--sagemaker-mlflow--technical/CX2K6XAT84

## Detailed Findings

### Infrastructure & Platform

#### INF-Q1: Compute
- **Score**: 4/4 ✅
- **Finding**: All compute is 100% AWS Lambda serverless. Three `NodejsFunction` Lambda functions are defined in `lib/microservice.ts`: `productLambdaFunction`, `basketLambdaFunction`, and `orderingLambdaFunction`. No EC2 instances, ECS tasks, or EKS clusters are present. However, all three functions use `Runtime.NODEJS_14_X`, which is past end-of-life and no longer receives security patches. The `bundling.externalModules: ['aws-sdk']` config is a V2 SDK pattern incompatible with Node.js 18+.
- **Gap**: Lambda runtime is deprecated (Node.js 14.x EOL). No reserved/provisioned concurrency configured.
- **Recommendation**: Upgrade all Lambda functions to `Runtime.NODEJS_20_X` in `lib/microservice.ts`; remove the `externalModules: ['aws-sdk']` bundling config; consider adding reserved concurrency limits for production safety.

#### INF-Q2: Databases
- **Score**: 4/4 ✅
- **Finding**: All three databases are fully managed DynamoDB tables defined in `lib/database.ts`: `product` (PK: `id`), `basket` (PK: `userName`), and `order` (PK: `userName`, SK: `orderDate`). All use `BillingMode.PAY_PER_REQUEST` for auto-scaling capacity. No self-managed database software detected anywhere in the repository.
- **Gap**: No customer-managed KMS encryption configured (uses AWS-managed default encryption). `RemovalPolicy.DESTROY` is set on all tables, which is dangerous for production data.
- **Recommendation**: Add `encryption: TableEncryption.CUSTOMER_MANAGED` with a KMS key in `lib/database.ts`; change `RemovalPolicy.DESTROY` to `RemovalPolicy.RETAIN` for production environments; add point-in-time recovery.

#### INF-Q3: Workflow Orchestration
- **Score**: 2/4 🟠
- **Finding**: No dedicated workflow orchestration service is present. The checkout flow uses EventBridge → SQS → Lambda as a basic async pipeline (`lib/eventbus.ts`, `lib/queue.ts`), which provides event routing but not workflow orchestration. The `checkoutBasket` function in `src/basket/index.js` performs a 4-step sequence (get basket → prepare payload → publish event → delete basket) with no state management or compensation logic. No Step Functions, Temporal, or other orchestration service found.
- **Gap**: No dedicated workflow orchestration. The checkout saga has no compensation, retry, or visibility. If `publishCheckoutBasketEvent` succeeds but `deleteBasket` fails, the basket remains while an order is created — leading to potential duplicate orders.
- **Recommendation**: Introduce AWS Step Functions to orchestrate the checkout workflow with explicit states for each step, error handling, retry policies, and compensation (re-create basket if order creation fails). This aligns with the preferred patterns: saga and event-driven.

#### INF-Q4: Async Messaging
- **Score**: 4/4 ✅
- **Finding**: Managed async messaging is well-implemented. EventBridge custom bus `SwnEventBus` with `CheckoutBasketRule` is defined in `lib/eventbus.ts`. SQS `OrderQueue` with 30-second visibility timeout and batch size 1 is defined in `lib/queue.ts`. The basket Lambda publishes `CheckoutBasket` events to EventBridge (`src/basket/index.js` → `publishCheckoutBasketEvent`), which routes them via rule to SQS, consumed by the ordering Lambda (`src/ordering/index.js` → `sqsInvocation`). EventBridge grant (`grantPutEventsTo`) is properly configured.
- **Gap**: No dead-letter queue (DLQ) configured on the SQS `OrderQueue` for failed message processing. No message deduplication.
- **Recommendation**: Add a DLQ to `OrderQueue` in `lib/queue.ts` for failed checkout events; implement SQS message deduplication using `ContentBasedDeduplication` or explicit deduplication IDs.

#### INF-Q5: Infrastructure as Code
- **Score**: 3/4 🟡
- **Finding**: CDK IaC covers all deployed resources: compute (Lambda in `lib/microservice.ts`), databases (DynamoDB in `lib/database.ts`), messaging (EventBridge + SQS in `lib/eventbus.ts`, `lib/queue.ts`), and API Gateway (`lib/apigateway.ts`). The stack is composed in `lib/aws-microservices-stack.ts` using well-structured CDK constructs. Configuration is in `cdk.json` and `tsconfig.json`.
- **Gap**: No network resources (VPC, subnets, security groups) are defined in IaC — Lambda functions run in the default VPC/no VPC. No CloudWatch alarms, dashboards, or monitoring resources. No IAM roles explicitly defined (CDK generates them via grants, which is acceptable but less visible). CDK version 2.17.0 is outdated.
- **Recommendation**: Add VPC construct with private subnets and VPC endpoints for DynamoDB; add CloudWatch alarm constructs for Lambda errors and API Gateway 5xx rates; upgrade `aws-cdk-lib` from `2.17.0` to latest stable version.

#### INF-Q6: CI/CD
- **Score**: 1/4 ❌
- **Finding**: No CI/CD definitions found in the repository. There are no `.github/workflows/` directory, no `buildspec.yml`, no `Jenkinsfile`, no `.gitlab-ci.yml`, no CodePipeline definitions in CDK. The only deployment mechanism is manual `cdk deploy` via the CLI. The `package.json` scripts include `build`, `watch`, `test`, and `cdk` but no deploy or pipeline scripts.
- **Gap**: Completely manual deployment process. No automated testing in pipeline, no environment separation, no approval gates.
- **Recommendation**: Create a CI/CD pipeline (GitHub Actions recommended for simplicity, or AWS CodePipeline for AWS-native). Minimum stages: `npm install` → `npm run build` → `npm test` → `cdk synth` → `cdk diff` → manual approval → `cdk deploy`. Add environment separation (dev/staging/prod).

#### INF-Q7: API Entry Point
- **Score**: 2/4 🟠
- **Finding**: Three separate `LambdaRestApi` API Gateway REST APIs are defined in `lib/apigateway.ts`: `Product Service`, `Basket Service`, and `Order Service`. Each has properly defined resources and methods (GET, POST, PUT, DELETE). The `proxy: false` setting ensures explicit route definitions.
- **Gap**: No throttling or usage plans configured on any API Gateway. No request validation. No WAF. No authorizers (no auth at all). No CORS configuration. No custom domain names. Three separate API Gateways create management overhead — could be consolidated.
- **Recommendation**: Add throttle settings (`{ rateLimit: 100, burstLimit: 50 }`) and usage plans on each API; add request body validation via API Gateway models; add a Cognito or Lambda authorizer; consider consolidating into a single API Gateway with path-based routing (`/product`, `/basket`, `/order`).

#### INF-Q8: Real-time Streaming
- **Score**: 2/4 🟠
- **Finding**: EventBridge provides event routing for the checkout flow, but it is an event bus, not a streaming service. No Kinesis Data Streams, Kinesis Firehose, or MSK (Managed Streaming for Apache Kafka) resources are defined. No streaming consumer patterns found in application code.
- **Gap**: No real-time streaming capability for order analytics, inventory updates, or event replay. EventBridge has limited replay and no persistent stream storage.
- **Recommendation**: For the current use case, EventBridge is sufficient. If real-time analytics are needed (order trends, inventory tracking), add Kinesis Data Streams as an additional EventBridge target with Kinesis Firehose to S3 for analytics.

#### INF-Q9: Network Security
- **Score**: 1/4 ❌
- **Finding**: No VPC, subnet, security group, or NACL definitions found anywhere in the CDK code or configuration. Lambda functions run outside a VPC (default configuration). DynamoDB is accessed via public AWS endpoints. API Gateway endpoints are publicly accessible with no IP restrictions.
- **Gap**: No network segmentation. No private subnets. No security groups. All services publicly accessible. No VPC endpoints for AWS service access.
- **Recommendation**: Create a VPC with public/private subnets in `lib/aws-microservices-stack.ts`; place Lambda functions in private subnets; add VPC endpoints for DynamoDB, EventBridge, and SQS; configure security groups to restrict traffic between services.

#### INF-Q10: Auto-scaling
- **Score**: 3/4 🟡
- **Finding**: Lambda functions have built-in auto-scaling (concurrent executions scale automatically). DynamoDB tables use `BillingMode.PAY_PER_REQUEST` (on-demand), which auto-scales read/write capacity. SQS auto-scales by design.
- **Gap**: No Lambda reserved concurrency or provisioned concurrency configured in `lib/microservice.ts`. Without concurrency limits, a traffic spike to one Lambda could consume the account-level concurrency limit (default 1000), starving other functions. No DynamoDB auto-scaling alarms.
- **Recommendation**: Add `reservedConcurrentExecutions` to each Lambda function to prevent one service from consuming all account concurrency. Consider provisioned concurrency for latency-sensitive endpoints. Add CloudWatch alarms for DynamoDB throttling events.

### Application Architecture

#### APP-Q1: Programming Languages
- **Score**: 3/4 🟡
- **Finding**: Application source code is JavaScript (ES module syntax with `import`/`export` in `src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js`). CDK infrastructure is TypeScript (`lib/*.ts`). Dependencies: `@aws-sdk/client-dynamodb`, `@aws-sdk/client-eventbridge`, `@aws-sdk/util-dynamodb` in service `package.json` files. Root `package.json` uses `aws-cdk-lib` 2.17.0 with TypeScript 3.9.7.
- **Gap**: JavaScript Lambda handlers lack TypeScript type safety. TypeScript version 3.9.7 is outdated (current stable is 5.x). Node.js has good but not best-in-class agent framework ecosystem (Python and TypeScript are stronger for Strands Agents, LangChain).
- **Recommendation**: Migrate Lambda handlers from JavaScript to TypeScript for type safety and better agent SDK compatibility. Upgrade TypeScript from 3.9.7 to 5.x in root `package.json`.

#### APP-Q2: API Documentation
- **Score**: 1/4 ❌
- **Finding**: No OpenAPI, Swagger, or any API specification files found in the repository. No `openapi.yaml`, `swagger.json`, or API documentation generation tools. API routes are defined only in CDK code (`lib/apigateway.ts`) with inline comments describing endpoints but no formal spec. No API documentation annotations in Lambda handlers.
- **Gap**: Complete absence of API documentation. Agents need machine-readable API specs to understand available operations, parameters, and response schemas.
- **Recommendation**: Create OpenAPI 3.0 specifications for all three services (product, basket, ordering); configure API Gateway to import these specs for automatic request/response validation; use the specs as agent tool definitions.

#### APP-Q3: Async vs Sync Communication
- **Score**: 2/4 🟠
- **Finding**: Only the checkout flow is async: `checkoutBasket` in `src/basket/index.js` publishes to EventBridge, routed via SQS to ordering Lambda. All other operations are synchronous: API Gateway → Lambda → DynamoDB → response. Product service: 5 sync operations (GET, POST, PUT, DELETE, query by category). Basket service: 4 sync operations + 1 async checkout. Ordering service: 2 sync GET operations + 1 async SQS consumer. Approximately 80% sync, 20% async.
- **Gap**: Heavy synchronous coupling for most operations. No async patterns for potentially long-running operations like bulk product updates or batch order queries.
- **Recommendation**: Expand async patterns using EventBridge for product catalog change notifications (price updates, new products); add async processing for batch operations; implement status polling for checkout operations. This aligns with preferred patterns: event-driven and async-messaging.

#### APP-Q4: Monolith vs Microservices
- **Score**: 4/4 ✅
- **Finding**: The application is well-decomposed into three independent microservices: (1) **Product service**: `src/product/index.js` + `src/product/ddbClient.js` + own `package.json` → `product` DynamoDB table, (2) **Basket service**: `src/basket/index.js` + `src/basket/ddbClient.js` + `eventBridgeClient.js` + own `package.json` → `basket` DynamoDB table + EventBridge publisher, (3) **Ordering service**: `src/ordering/index.js` + `src/ordering/ddbClient.js` + own `package.json` → `order` DynamoDB table + SQS consumer. Each service has its own Lambda function, DynamoDB table, API Gateway, and dependency manifest. Inter-service communication is via EventBridge (no shared databases, no direct invocations).
- **Gap**: No service contracts or shared schema definitions between services. The `checkoutPayload` structure is implicitly agreed upon between basket and ordering services without a formal contract.
- **Recommendation**: Define event schemas using EventBridge Schema Registry or JSON Schema for the `CheckoutBasket` event contract; this becomes critical when agents generate or consume these events.

#### APP-Q5: API Response Format
- **Score**: 4/4 ✅
- **Finding**: All API responses are structured JSON. Every handler returns `{ statusCode: 200, body: JSON.stringify({ message: "...", body: ... }) }` for success and `{ statusCode: 500, body: JSON.stringify({ message: "...", errorMsg: e.message, errorStack: e.stack }) }` for errors. Response bodies contain nested data under a `body` key. DynamoDB items are unmarshalled from DynamoDB format to plain JSON using `@aws-sdk/util-dynamodb`.
- **Gap**: Error responses include `errorStack` (stack traces), which leaks implementation details. Response format is consistent but non-standard (nested `body` inside response body).
- **Recommendation**: Remove `errorStack` from error responses; standardize response envelope (consider `{ data: ..., error: null }` pattern); add proper HTTP status codes (404 for not found, 400 for bad request) instead of generic 500.

#### APP-Q6: Workflow Logic
- **Score**: 1/4 ❌
- **Finding**: All business logic is implemented as hardcoded `switch`/`case` statements inside Lambda handlers. Product service (`src/product/index.js`) switches on `event.httpMethod` (GET/POST/PUT/DELETE). Basket service (`src/basket/index.js`) switches on `event.httpMethod` with additional `event.path` check for `/basket/checkout`. Ordering service (`src/ordering/index.js`) uses `if/else` to distinguish between SQS, EventBridge, and API Gateway invocations. The checkout workflow logic is procedural code in `checkoutBasket()` with no state machine or orchestration.
- **Gap**: No workflow orchestration. Business logic is embedded in routing code. The checkout saga (get basket → prepare order → publish event → delete basket) is a sequential procedure with no error compensation.
- **Recommendation**: Implement AWS Step Functions for the checkout workflow; extract business logic from routing code into dedicated handler functions; use Step Functions for any multi-step operations that agents might trigger.

#### APP-Q7: Idempotency
- **Score**: 1/4 ❌
- **Finding**: No idempotency patterns found in any Lambda handler. `createProduct` in `src/product/index.js` generates a UUID for each call (`uuidv4()`) but does not check for duplicate submissions. `createBasket` in `src/basket/index.js` uses `PutItemCommand` which overwrites existing items by `userName` (unintentional idempotency via primary key). `createOrder` in `src/ordering/index.js` uses `PutItemCommand` with `userName` + `orderDate` (ISO timestamp), meaning duplicate SQS messages could create duplicate orders with slightly different timestamps. No `Idempotency-Key` headers, no deduplication IDs on SQS, no conditional writes.
- **Gap**: Critical gap for agentic workloads. Agents retry failed API calls automatically. Without idempotency, retries on `createProduct` create duplicate products, retries on checkout create duplicate orders.
- **Recommendation**: Implement `@aws-lambda-powertools/idempotency` with DynamoDB persistence for all write operations; add deduplication ID to SQS messages in `lib/queue.ts`; use DynamoDB conditional expressions to prevent duplicate order creation.

#### APP-Q8: Rate Limiting & Throttling
- **Score**: 1/4 ❌
- **Finding**: No rate limiting configured at any layer. API Gateway in `lib/apigateway.ts` uses `LambdaRestApi` with no `deployOptions.throttlingRateLimit` or `deployOptions.throttlingBurstLimit`. No usage plans or API keys. No WAF rules. No application-level rate limiting middleware in any Lambda handler.
- **Gap**: APIs are unprotected against abuse. Agents can generate high request volumes; without rate limiting, a malfunctioning agent could overwhelm the system.
- **Recommendation**: Add API Gateway stage throttling (`deployOptions: { throttlingRateLimit: 100, throttlingBurstLimit: 200 }`); create usage plans with API keys for client-level quotas; consider AWS WAF for additional protection.

#### APP-Q9: Resilience Patterns
- **Score**: 1/4 ❌
- **Finding**: No retry, circuit breaker, or timeout patterns in any Lambda handler. All DynamoDB calls use default AWS SDK settings with no explicit retry configuration. The `checkoutBasket` function in `src/basket/index.js` chains 4 operations (getBasket → prepareOrderPayload → publishCheckoutBasketEvent → deleteBasket) with no error recovery — if the EventBridge publish succeeds but deleteBasket fails, the basket persists while an order is created. No explicit timeout configuration on Lambda functions (default 3-second timeout applies, which may be too short for the checkout flow).
- **Gap**: No resilience patterns. Partial failure in checkout creates inconsistent state. No timeout management.
- **Recommendation**: Configure explicit timeouts on all Lambda functions in `lib/microservice.ts` (30s for checkout, 10s for CRUD); add retry with exponential backoff for DynamoDB and EventBridge calls; implement the transactional outbox pattern for the checkout flow to prevent partial failures.

#### APP-Q10: Long-running Processes
- **Score**: 2/4 🟠
- **Finding**: The checkout flow is handled asynchronously: basket Lambda publishes an event to EventBridge, which routes to SQS, consumed by ordering Lambda. This is the correct pattern for operations that may take longer. However, there is no status polling endpoint — the client that calls `POST /basket/checkout` receives a 200 response but has no way to check if the order was actually created. The ordering service provides `GET /order/{userName}?orderDate=timestamp` but the client doesn't know the `orderDate` value assigned during order creation.
- **Gap**: No order status API. No callback mechanism. Client cannot confirm checkout completion.
- **Recommendation**: Add an order status endpoint (e.g., `GET /order/status/{checkoutId}`) that returns order creation status; consider WebSocket or SNS notification for real-time checkout completion notification; return a `checkoutId` from the checkout endpoint for tracking.

#### APP-Q11: API Versioning
- **Score**: 1/4 ❌
- **Finding**: No API versioning strategy found. URLs are unversioned: `/product`, `/basket`, `/order`. No `Accept-Version` headers. No version-specific routing. No changelog or version history. API Gateway stage names are not used for versioning.
- **Gap**: No versioning means breaking changes cannot be introduced safely. Agents built against current APIs will break if response formats change.
- **Recommendation**: Implement URL path versioning (`/v1/product`, `/v1/basket`, `/v1/order`) in `lib/apigateway.ts`; establish backward compatibility policy; create an API changelog.

#### APP-Q12: Service Discovery & Mesh
- **Score**: 2/4 🟠
- **Finding**: Services communicate via EventBridge bus name, configured as an environment variable `EVENT_BUSNAME: "SwnEventBus"` in `lib/microservice.ts`. The event source (`EVENT_SOURCE: "com.swn.basket.checkoutbasket"`) and detail type (`EVENT_DETAILTYPE: "CheckoutBasket"`) are also passed via environment variables. No service registry, no Cloud Map, no App Mesh. API Gateway endpoints are not discoverable programmatically.
- **Gap**: Hard-coded event bus name. No service catalog or API registry for agents to discover available services and their capabilities.
- **Recommendation**: Register services in AWS Cloud Map or create an API catalog; use SSM Parameter Store for service configuration instead of hard-coded environment variables; create a service manifest that agents can query to discover available APIs and event types.

#### APP-Q13: AI/Agent Frameworks
- **Score**: 1/4 ❌
- **Finding**: No AI or agent frameworks found in any `package.json` file. No imports of `@aws-sdk/client-bedrock-runtime`, `langchain`, `langgraph`, `strands-agents`, `openai`, `anthropic`, or any AI SDK in any source file. No MCP (Model Context Protocol) server implementations. The application is a traditional CRUD e-commerce system with no AI capabilities.
- **Gap**: Complete absence of AI/agent infrastructure. No integration points for agent tools.
- **Recommendation**: Start with Strands Agents SDK or Amazon Bedrock Agents to create a conversational e-commerce agent; wrap existing API Gateway endpoints as agent tools; the well-defined microservices boundaries make tool isolation straightforward.

### Data Foundations

#### DATA-Q1: Vector Database Presence
- **Score**: 1/4 ❌
- **Finding**: No vector database found in the repository. No OpenSearch, Aurora pgvector, S3 Vectors, Bedrock Knowledge Bases, Pinecone, Weaviate, or Chroma references in any CDK file, `package.json`, or source code. Product search in `src/product/index.js` uses DynamoDB `ScanCommand` (full table scan) and `QueryCommand` with `FilterExpression` for category — no semantic or similarity search.
- **Gap**: No vector search capability. Product discovery is limited to exact-match queries. Agents cannot perform semantic product search.
- **Recommendation**: Add Amazon Bedrock Knowledge Base or Amazon OpenSearch Service with k-NN plugin for semantic product search; index product catalog with vector embeddings for natural language product queries from agents.

#### DATA-Q2: Vector DB Management
- **Score**: 1/4 ❌
- **Finding**: No vector database present (see DATA-Q1). No managed or self-hosted vector storage of any kind.
- **Gap**: No vector storage infrastructure to support RAG or semantic search.
- **Recommendation**: Use a fully managed option: Amazon Bedrock Knowledge Bases (fully managed end-to-end) or Amazon OpenSearch Serverless with vector search (managed infrastructure, flexible configuration).

#### DATA-Q3: RAG Implementation
- **Score**: 1/4 ❌
- **Finding**: No RAG (Retrieval Augmented Generation) pipeline found. No embedding model calls, no document chunking or splitting code, no similarity search patterns. No Bedrock, Titan Embeddings, or OpenAI embedding imports. Product data is queried only via DynamoDB primary key lookups and table scans.
- **Gap**: No semantic retrieval capability. Agents cannot provide contextual product recommendations or answer natural language product questions.
- **Recommendation**: Implement a RAG pipeline using Amazon Bedrock Knowledge Bases backed by the product catalog; embed product descriptions, categories, and attributes; enable semantic product search as an agent tool.

#### DATA-Q4: Data Source Sprawl
- **Score**: 3/4 🟡
- **Finding**: Three distinct DynamoDB tables, each owned by a single service: `product` table → product Lambda, `basket` table → basket Lambda, `order` table → ordering Lambda. No cross-service data access detected — each Lambda only accesses its own table (verified by CDK grants in `lib/microservice.ts` and Lambda code). The basket service also writes to EventBridge, and ordering service reads from SQS, but these are messaging channels not data stores.
- **Gap**: Three data sources is manageable but there is no unified data access layer or API that abstracts all three. An agent would need to call three separate APIs to get a complete customer view (products + basket + orders).
- **Recommendation**: Consider a BFF (Backend for Frontend) or aggregation Lambda that combines data from all three services for agent queries; alternatively, ensure the agent has tools for each service with clear documentation.

#### DATA-Q5: Data Access Pattern
- **Score**: 2/4 🟠
- **Finding**: Each Lambda handler directly imports `ddbClient` and executes DynamoDB commands inline. For example, `src/product/index.js` imports `{ ddbClient }` from `./ddbClient` and directly calls `ddbClient.send(new GetItemCommand(params))`. The `ddbClient.js` files in each service are identical one-liners: `new DynamoDBClient()`. Business logic (marshalling, unmarshalling, query construction) is mixed with data access in the handler code.
- **Gap**: No repository/DAO pattern. No data access abstraction. Business logic coupled with database operations. Difficult to swap data source or add caching.
- **Recommendation**: Extract data access into repository modules per service (e.g., `productRepository.js` with `getProduct()`, `createProduct()`, etc.); separate business logic from data access; this makes it easier to wrap services as agent tools with clear interfaces.

#### DATA-Q6: Unstructured Data
- **Score**: 1/4 ❌
- **Finding**: No S3 buckets, no unstructured data storage, no document parsing (Textract, Tika). Product data is structured in DynamoDB. The `checkoutbasketevents.json` fixture file in `src/basket/` is a test fixture, not application data. No image/PDF/document processing.
- **Gap**: No capability to handle product images, PDFs, or other unstructured content that agents might need to process.
- **Recommendation**: If product images or descriptions exist externally, add S3 storage and parsing pipeline; for agent use cases, consider adding product image analysis via Bedrock multimodal models.

#### DATA-Q7: Schema Documentation
- **Score**: 2/4 🟠
- **Finding**: DynamoDB table schemas are partially documented in CDK code (`lib/database.ts`): `product` has `partitionKey: id (STRING)`, `basket` has `partitionKey: userName (STRING)`, `order` has `partitionKey: userName (STRING), sortKey: orderDate (STRING)`. Additional attributes are documented in CDK comments (e.g., "product: PK: id -- name - description - imageFile - price - category"). However, there are no formal JSON Schema files, no Avro/Protobuf definitions, no database migration files, and no schema versioning.
- **Gap**: Schemas only documented as inline CDK comments. No machine-readable schema definitions. No schema versioning or migration strategy.
- **Recommendation**: Create JSON Schema files for each DynamoDB table's item structure; add EventBridge schema definitions for the `CheckoutBasket` event; register schemas in EventBridge Schema Registry for agent consumption.

#### DATA-Q8: Data Access Layer
- **Score**: 2/4 🟠
- **Finding**: Each service has its own `ddbClient.js` file, but these are identical thin wrappers (just `new DynamoDBClient()`). The actual data access logic (table name, key construction, marshalling, query expressions) is scattered throughout handler functions in each `index.js`. No centralized repository pattern, no ORM, no shared data access utilities.
- **Gap**: No unified data access abstraction. Data access patterns are duplicated across services (e.g., the scan/query/get/put pattern appears in all three handlers).
- **Recommendation**: Create repository modules per service (e.g., `productRepository.js`, `basketRepository.js`, `orderRepository.js`) that encapsulate DynamoDB operations; extract shared utilities for marshalling/unmarshalling; consider using DynamoDB Toolbox or ElectroDB for type-safe data access.

#### DATA-Q9: Embedding Freshness
- **Score**: 1/4 ❌
- **Finding**: No embedding generation or refresh mechanism exists because no vector database or RAG pipeline is present (see DATA-Q1, DATA-Q3). No DynamoDB Streams configured for change detection. No event-driven index update triggers. No scheduled re-indexing.
- **Gap**: No embedding infrastructure to maintain or refresh.
- **Recommendation**: When implementing vector search (Phase 3), enable DynamoDB Streams on the `product` table to trigger automatic re-embedding when products are added, updated, or deleted; configure Bedrock Knowledge Base sync for scheduled index updates.

#### DATA-Q10: Database Engine Version & EOL
- **Score**: 4/4 ✅
- **Finding**: All databases are DynamoDB, which is a fully managed, serverless NoSQL service. DynamoDB has no user-facing engine version — AWS manages the engine lifecycle, patching, and upgrades transparently. No version pinning is required or possible. No EOL concerns.
- **Gap**: None for DynamoDB. However, the `aws-cdk-lib` version (2.17.0 in `package.json`) is significantly outdated and may not support latest DynamoDB CDK features.
- **Recommendation**: Upgrade `aws-cdk-lib` from 2.17.0 to latest stable version to ensure access to latest DynamoDB CDK constructs and security fixes.

#### DATA-Q11: Stored Procedures & Schema Complexity
- **Score**: 4/4 ✅
- **Finding**: No stored procedures, triggers, or proprietary SQL constructs detected. DynamoDB is a NoSQL database that does not support stored procedures. All business logic is in the application layer (Lambda handlers). No `.sql` files found. No ORM bypass patterns. No raw SQL execution. The `checkoutBasket` business logic (total price calculation, payload preparation) is entirely in `src/basket/index.js`.
- **Gap**: None. All business logic is properly in the application layer.
- **Recommendation**: Maintain this pattern. When adding agent capabilities, keep all business logic in Lambda functions (agent tools) rather than pushing logic into the data layer.

### Identity, Security & Governance

#### SEC-Q1: Secret Management
- **Score**: 2/4 🟠
- **Finding**: No AWS Secrets Manager or HashiCorp Vault references found in CDK code or application code. Environment variables in `lib/microservice.ts` pass non-sensitive configuration: `DYNAMODB_TABLE_NAME`, `PRIMARY_KEY`, `SORT_KEY`, `EVENT_SOURCE`, `EVENT_DETAILTYPE`, `EVENT_BUSNAME`. No database passwords, API keys, or credentials are visible in the codebase. No `.env` files committed. No hardcoded secrets detected.
- **Gap**: While no secrets are currently needed (DynamoDB access is via IAM roles, EventBridge via grants), there is no Secrets Manager infrastructure for future needs (e.g., third-party API keys for payment processing, AI model API keys). The `EVENT_BUSNAME` is a configuration value that could be managed via SSM Parameter Store.
- **Recommendation**: Set up AWS Secrets Manager for any future secrets (payment gateway keys, third-party API credentials); migrate configuration values to SSM Parameter Store; establish a secrets rotation policy for when Bedrock API keys or agent credentials are added.

#### SEC-Q2: IAM Least Privilege
- **Score**: 3/4 🟡
- **Finding**: CDK grants provide scoped IAM permissions: `productTable.grantReadWriteData(productFunction)`, `basketTable.grantReadWriteData(basketFunction)`, `orderTable.grantReadWriteData(orderFunction)`, and `bus.grantPutEventsTo(basketFunction)` in `lib/microservice.ts` and `lib/eventbus.ts`. Each Lambda function only has access to its own DynamoDB table (no cross-service data access). EventBridge publish permission is only granted to the basket function.
- **Gap**: `grantReadWriteData` grants both read AND write access, which is broader than needed for read-only operations (e.g., the product GET endpoint doesn't need write access). The ordering Lambda has write access to the order table but could be restricted to specific operations. No condition keys or resource-level granularity within tables.
- **Recommendation**: Use `grantReadData` where only read access is needed; add condition keys for specific DynamoDB actions (e.g., ordering Lambda only needs `PutItem`, not `DeleteItem`); create separate IAM policies for read and write operations.

#### SEC-Q3: Identity Propagation
- **Score**: 1/4 ❌
- **Finding**: No JWT, OAuth, or token-based identity propagation found. No authentication middleware in any Lambda handler. No Cognito User Pool, Okta, or OIDC configuration. The `userName` field used in basket and order services comes directly from the request body (`event.body`) — it is a client-provided value with no server-side validation or identity verification. Anyone can operate on any user's basket or orders by providing a different `userName`.
- **Gap**: Critical security gap. No user identity verification. User context is client-provided and untrusted. No token exchange between services. An agent would have no way to verify it's acting on behalf of the correct user.
- **Recommendation**: Implement Cognito User Pool with API Gateway authorizer; extract `userName` from the JWT token's `sub` or `cognito:username` claim instead of request body; propagate user identity through EventBridge events for the checkout flow.

#### SEC-Q4: Audit Logging
- **Score**: 1/4 ❌
- **Finding**: No CloudTrail configuration in CDK. No audit logging infrastructure defined. Lambda functions write to CloudWatch Logs by default (via `console.log`), but these are application logs, not audit trails. No log file validation, no immutable storage, no log retention policies defined.
- **Gap**: No audit trail for API calls, data access, or infrastructure changes. Cannot track who did what, when. Critical for agent accountability — must be able to audit agent actions.
- **Recommendation**: Add CloudTrail trail in CDK stack for API activity logging; enable CloudTrail log file validation; configure S3 bucket with object lock for immutable audit log storage; set CloudWatch Logs retention policies on all Lambda log groups.

#### SEC-Q5: API Rate Limits
- **Score**: 1/4 ❌
- **Finding**: No rate limiting at any level. API Gateway has no throttle configuration in `lib/apigateway.ts`. No usage plans. No API keys for client identification. No WAF rules. No application-level rate limiting in Lambda handlers. Default API Gateway throttle limits apply (10,000 requests per second account-wide), but no per-client or per-API limits are configured.
- **Gap**: No rate limiting protection. A malfunctioning agent or malicious client could flood all three APIs. No per-client quotas for fair usage.
- **Recommendation**: Add API Gateway throttle settings per stage; create usage plans with API keys for per-client quotas; add AWS WAF with rate-based rules for DDoS protection; implement per-user rate limiting for agent-initiated requests.

#### SEC-Q6: PII Redaction
- **Score**: 1/4 ❌
- **Finding**: All three Lambda handlers expose stack traces in error responses: `errorStack: e.stack` in `src/product/index.js`, `src/basket/index.js`, and `src/ordering/index.js`. Application logs include full request bodies via `console.log("request:", JSON.stringify(event, undefined, 2))`, which will log PII such as `userName`, `firstName`, `lastName`, `email`, `address`, `paymentMethod`, and `cardInfo` (as referenced in `lib/database.ts` comments for the order table schema). No log scrubbing, no PII masking, no Macie enabled.
- **Gap**: Stack traces leaked in API responses expose internal implementation details. PII (names, email, address, payment info) logged in plaintext to CloudWatch. No data classification or masking.
- **Recommendation**: Remove `errorStack: e.stack` from all error responses immediately; implement log scrubbing to mask PII fields before logging; add field-level encryption for sensitive order attributes (email, address, payment info); consider Amazon Macie for automated PII detection.

#### SEC-Q7: Human Approval Workflows
- **Score**: 1/4 ❌
- **Finding**: No human approval workflows found. No Step Functions with `waitForTaskToken` patterns. No manual approval stages. No approval APIs or UI. The checkout flow (`POST /basket/checkout`) executes fully automatically with no human verification. Product deletion (`DELETE /product/{id}`) is also unguarded.
- **Gap**: No human-in-the-loop for high-risk operations. Agents could trigger bulk deletions or fraudulent checkouts without approval.
- **Recommendation**: Implement Step Functions with human approval tasks for high-value orders (over a threshold); add approval gates for bulk product deletions; create an approval API that agents can invoke when they detect high-risk actions.

#### SEC-Q8: Encryption at Rest
- **Score**: 2/4 🟠
- **Finding**: DynamoDB tables in `lib/database.ts` have no explicit encryption configuration — they use AWS-managed default encryption (AES-256). No `aws_kms_key` resources defined. No customer-managed keys (CMK). SQS queue in `lib/queue.ts` has no encryption configured. EventBridge events are encrypted by default with AWS-managed keys.
- **Gap**: Only AWS-managed encryption. No customer-managed KMS keys. No control over key rotation or key policies. Cannot restrict key usage to specific services.
- **Recommendation**: Create customer-managed KMS keys for DynamoDB tables and SQS queue; configure key policies to restrict decryption to specific Lambda function roles; enable automatic key rotation.

#### SEC-Q9: API Authentication
- **Score**: 1/4 ❌
- **Finding**: All three API Gateway REST APIs in `lib/apigateway.ts` have no authorization configured. No `authorizer` property on any method. No `apiKeyRequired: true`. No `AuthorizationType.COGNITO` or `AuthorizationType.IAM`. All endpoints are publicly accessible: `GET /product`, `POST /product`, `DELETE /product/{id}`, `POST /basket/checkout`, etc. Any client can invoke any operation.
- **Gap**: Complete absence of API authentication. All endpoints are open to the internet. Data manipulation (create, update, delete) and checkout are unprotected.
- **Recommendation**: Add Cognito User Pool authorizer for user-facing endpoints; add IAM authorization for service-to-service calls; require API keys for all endpoints at minimum; implement OAuth2 scopes for fine-grained access control.

#### SEC-Q10: Centralized Identity
- **Score**: 1/4 ❌
- **Finding**: No centralized identity provider found. No `aws_cognito_user_pool`, `aws_cognito_identity_pool`, or any OIDC/SAML configuration in CDK. No Okta, Auth0, Ping, or other IdP integration. User identity (`userName`) is an arbitrary string passed in request bodies with no verification.
- **Gap**: No identity provider. No SSO. No user management. No credential issuance.
- **Recommendation**: Implement Amazon Cognito User Pool as centralized identity provider; configure user pool with email/password authentication and MFA; integrate with API Gateway authorizers; add user groups for role-based access control (admin, customer, agent).

### Operations & Observability

#### OPS-Q1: Distributed Tracing
- **Score**: 1/4 ❌
- **Finding**: No distributed tracing found. No X-Ray tracing configuration in Lambda function props in `lib/microservice.ts` (no `tracing: Tracing.ACTIVE`). No OpenTelemetry SDK in any `package.json`. No trace context propagation headers. No `@aws-lambda-powertools/tracer` imports. No Datadog, Jaeger, or Zipkin SDKs. API Gateway has no `tracingEnabled: true` setting. The checkout flow crosses three services (basket Lambda → EventBridge → SQS → ordering Lambda) with no trace correlation.
- **Gap**: Cannot trace requests across services. The checkout flow spans basket and ordering services with no way to correlate a checkout request to its resulting order. Agent workflows would be completely opaque.
- **Recommendation**: Add `tracing: Tracing.ACTIVE` to all Lambda functions in `lib/microservice.ts`; enable X-Ray tracing on API Gateway stages; add `@aws-lambda-powertools/tracer` for custom subsegments around DynamoDB and EventBridge calls; propagate trace IDs through EventBridge event metadata.

#### OPS-Q2: Structured Logging
- **Score**: 2/4 🟠
- **Finding**: Lambda handlers use `console.log` with `JSON.stringify` for request logging: `console.log("request:", JSON.stringify(event, undefined, 2))`. Some operations log results: `console.log(Item)`, `console.log(createResult)`. Error logging uses `console.error(e)`. Output is partially structured (JSON when `JSON.stringify` is used) but inconsistent — some logs are plain strings, some are JSON objects. No correlation IDs, no request IDs, no structured log format library.
- **Gap**: No consistent structured logging format. No correlation IDs to link related log entries. No log levels (info/warn/error). Cannot correlate logs across the checkout flow (basket → ordering).
- **Recommendation**: Adopt `@aws-lambda-powertools/logger` for all Lambda handlers; configure JSON output with consistent fields (requestId, correlationId, service, operation); add correlation ID middleware that generates/propagates IDs through EventBridge events.

#### OPS-Q3: Automated Evals
- **Score**: 1/4 ❌
- **Finding**: No agent evaluation framework found. No eval datasets, no scoring scripts, no LLM-as-judge patterns, no golden dataset files, no RAGAS imports, no A/B test infrastructure. The application has no AI components to evaluate.
- **Gap**: No eval infrastructure. When agents are introduced, there will be no way to measure quality, accuracy, or regression.
- **Recommendation**: Prepare eval infrastructure alongside agent development (Phase 3); create golden datasets for expected agent interactions (product search queries, checkout flows); implement scoring metrics (task completion rate, tool accuracy, latency).

#### OPS-Q4: SLOs
- **Score**: 1/4 ❌
- **Finding**: No SLO definitions found anywhere. No CloudWatch alarms in CDK. No `aws_cloudwatch_metric_alarm` resources. No error budget tracking. No SLO dashboards. No p99/p95 latency targets documented. The CDK stack defines no monitoring resources at all.
- **Gap**: No defined performance targets. No alerting on degradation. Cannot measure if the system meets user expectations. Essential for agent SLOs (task success rate, response time).
- **Recommendation**: Define SLOs for each service: API latency (p99 < 1s for CRUD, p99 < 3s for checkout), error rate (< 0.1%), availability (99.9%); create CloudWatch alarms for these thresholds; set up a CloudWatch dashboard per service.

#### OPS-Q5: Rollback Capability
- **Score**: 1/4 ❌
- **Finding**: No rollback mechanisms configured. No CodeDeploy configuration. No Lambda alias-based traffic shifting. No blue/green deployment setup. No feature flags. CDK deploy performs a direct CloudFormation stack update — rollback is only via CloudFormation stack rollback on failure, which is reactive not proactive. No prompt or configuration versioning.
- **Gap**: No proactive rollback capability. A bad deployment to any Lambda function immediately affects all traffic. No canary or gradual rollout.
- **Recommendation**: Configure Lambda function aliases with CodeDeploy for traffic shifting (canary: 10% → 100% over 30 minutes); add CloudWatch alarms as deployment rollback triggers; implement feature flags for agent capabilities that can be toggled without deployment.

#### OPS-Q6: LLM Cost Tracking
- **Score**: 1/4 ❌
- **Finding**: No LLM usage in the application. No Bedrock, OpenAI, or any LLM API calls. No token counting, no cost attribution, no usage metrics. No observability data retention policies.
- **Gap**: No LLM cost tracking infrastructure. When agents are introduced, token usage must be tracked per request with user/feature attribution.
- **Recommendation**: When implementing agents (Phase 3), add per-request token usage logging; publish CloudWatch custom metrics for input/output tokens by service/user/workflow; implement tiered retention policies for observability data; set cost alerting thresholds.

#### OPS-Q7: Business Metrics
- **Score**: 1/4 ❌
- **Finding**: No custom business metrics published. No `cloudwatch.putMetricData` calls in any Lambda handler. No custom dashboards. Metrics are limited to default Lambda metrics (invocations, errors, duration) and API Gateway metrics (4xx, 5xx, latency). No business KPIs tracked: no checkout success rate, no basket abandonment rate, no order volume, no revenue metrics.
- **Gap**: No business outcome visibility. Cannot correlate infrastructure performance with business results. Agents need business metrics to optimize their behavior.
- **Recommendation**: Add CloudWatch custom metrics for: checkout success/failure rate, average order value, basket creation rate, product search result count, order fulfillment time; create a business metrics dashboard.

#### OPS-Q8: Anomaly Detection
- **Score**: 1/4 ❌
- **Finding**: No anomaly detection or alerting configured. No CloudWatch anomaly detection. No static threshold alarms. No PagerDuty/OpsGenie integration. No composite alarms. The application has zero proactive alerting — failures are only discovered when users report issues.
- **Gap**: No anomaly detection. A malfunctioning agent could generate hundreds of incorrect orders before anyone notices. No behavioral baseline monitoring.
- **Recommendation**: Enable CloudWatch anomaly detection on Lambda error rates and p99 latency for all three services; create composite alarms for correlated failures (e.g., basket errors + ordering errors = checkout degradation); integrate with SNS for alert notification.

#### OPS-Q9: Deployment Strategy
- **Score**: 1/4 ❌
- **Finding**: No deployment strategy configured. Deployment is manual `cdk deploy` which performs CloudFormation stack update — all changes go directly to production. No canary deployment. No blue/green. No traffic shifting. No feature flags. No A/B testing infrastructure. No separate environments (dev/staging/prod).
- **Gap**: Direct-to-production deployment with no safety net. Any bad change immediately affects all users and agent-driven traffic.
- **Recommendation**: Implement Lambda alias-based traffic shifting with CodeDeploy: `LINEAR_10_PERCENT_EVERY_1_MINUTE` or `CANARY_10_PERCENT_5_MINUTES`; add pre/post deployment hooks for integration tests; set up separate CDK stacks for dev/staging/prod environments.

#### OPS-Q10: Integration Testing
- **Score**: 1/4 ❌
- **Finding**: The test file `test/aws-microservices.test.ts` exists but is entirely commented out — the only active line is `test('SQS Queue Created', () => {})` which is an empty test that always passes. Jest is configured (`jest.config.js`) with `ts-jest` transform. No integration tests, no API tests, no contract tests, no end-to-end tests. No test containers. No Postman/Newman collections.
- **Gap**: Zero test coverage. No regression protection. Deploying agent integrations without tests is extremely risky — agents amplify bugs by automating interactions.
- **Recommendation**: Uncomment and fix the CDK assertion test in `test/aws-microservices.test.ts`; add unit tests for each Lambda handler's business logic; add integration tests using CDK `Template.fromStack()` assertions; add API integration tests using a test environment.

#### OPS-Q11: Incident Response Automation
- **Score**: 1/4 ❌
- **Finding**: No runbooks, no SSM Automation documents, no Lambda-based remediation functions, no Step Functions for incident workflows found in the repository. No incident response documentation. No self-healing patterns. No auto-restart or auto-scaling on failure events (beyond Lambda's built-in retry for async invocations).
- **Gap**: No incident response automation. No machine-readable runbooks for agent-driven incident response. Manual incident response for an automated system creates dangerous latency.
- **Recommendation**: Create runbook documents (Markdown or SSM Automation documents) for common failure modes: DynamoDB throttling, EventBridge delivery failures, SQS poison messages; implement DLQ processing Lambda for automatic retry of failed checkout events; add CloudWatch alarm actions that trigger remediation.

#### OPS-Q12: Observability Governance & Ownership
- **Score**: 1/4 ❌
- **Finding**: No CODEOWNERS file. No team ownership files. No SLO definition files. No observability governance documentation. No platform team tooling. No per-service dashboards or alarms. No evidence of any observability ownership model.
- **Gap**: No observability ownership. No one is accountable for service reliability, agent quality, or incident response. No SLO-driven culture.
- **Recommendation**: Create a CODEOWNERS file assigning ownership for each service; define service-level SLOs with named owners; establish an observability-as-a-product mindset with centralized dashboards and per-service alarm ownership; when agents are introduced, assign ownership for agent-level SLOs (task success rate, hallucination rate).

---

## Appendix: Evidence Index

| # | File Path | Key Findings |
|---|-----------|-------------|
| 1 | `lib/aws-microservices-stack.ts` | CDK stack composition — database, microservices, API gateway, queue, event bus constructs; single-stack architecture |
| 2 | `lib/microservice.ts` | 3 Lambda functions (`NodejsFunction`) with `Runtime.NODEJS_14_X` (deprecated); `externalModules: ['aws-sdk']` (V2 pattern); CDK grants for DynamoDB access; environment variables for config |
| 3 | `lib/database.ts` | 3 DynamoDB tables (product, basket, order) with `PAY_PER_REQUEST` billing; `RemovalPolicy.DESTROY`; no KMS encryption; schema documented in comments |
| 4 | `lib/eventbus.ts` | Custom EventBridge bus `SwnEventBus`; `CheckoutBasketRule` routing to SQS; `grantPutEventsTo` for basket Lambda |
| 5 | `lib/queue.ts` | SQS `OrderQueue` with 30s visibility timeout, batch size 1; no DLQ configured |
| 6 | `lib/apigateway.ts` | 3 separate `LambdaRestApi` instances (Product, Basket, Order); `proxy: false`; no auth, no throttling, no CORS, no validation |
| 7 | `src/product/index.js` | Product Lambda handler; switch/case routing; CRUD operations; `uuidv4()` for product IDs; `e.stack` in error response; `ScanCommand` for list all |
| 8 | `src/basket/index.js` | Basket Lambda handler; checkout flow: getBasket → prepareOrderPayload → publishCheckoutBasketEvent → deleteBasket; no error compensation; `PutEventsCommand` to EventBridge |
| 9 | `src/ordering/index.js` | Ordering Lambda handler; tri-mode: SQS invocation, EventBridge invocation, API Gateway invocation; `createOrder` with auto-generated `orderDate`; `e.stack` in error response |
| 10 | `src/product/ddbClient.js` | Thin DynamoDB client wrapper — `new DynamoDBClient()` with no configuration |
| 11 | `src/basket/ddbClient.js` | Identical DynamoDB client wrapper as product service |
| 12 | `src/basket/eventBridgeClient.js` | EventBridge client — `new EventBridgeClient()` with no configuration |
| 13 | `src/ordering/ddbClient.js` | Identical DynamoDB client wrapper as product/basket services |
| 14 | `package.json` | Root dependencies: `aws-cdk-lib` 2.17.0, TypeScript 3.9.7, Jest 26.4.2 — all significantly outdated |
| 15 | `src/product/package.json` | Product Lambda deps: `@aws-sdk/client-dynamodb` ^3.55.0, `@aws-sdk/util-dynamodb` ^3.55.0 |
| 16 | `src/basket/package.json` | Basket Lambda deps: `@aws-sdk/client-dynamodb` ^3.55.0, `@aws-sdk/client-eventbridge` ^3.58.0 |
| 17 | `src/ordering/package.json` | Ordering Lambda deps: `@aws-sdk/client-dynamodb` ^3.58.0 |
| 18 | `test/aws-microservices.test.ts` | Entirely commented out — single empty test `'SQS Queue Created'` that always passes |
| 19 | `src/basket/checkoutbasketevents.json` | Test fixture with 2 sample EventBridge events for checkout flow testing |
| 20 | `bin/aws-microservices.ts` | CDK app entry point; `AwsMicroservicesStack` instantiation; no environment specification (environment-agnostic) |
