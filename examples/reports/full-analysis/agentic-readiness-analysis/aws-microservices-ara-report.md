# Agentic Readiness Analysis Report

**Target**: services/aws-microservices
**Date**: 2026-05-18
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**Repository Type**: application
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P0
**Tags**: microservices, serverless, event-driven
**Context**: Event-driven serverless microservices (product, basket, ordering) with Lambda, DynamoDB, EventBridge, SQS. The agent will invoke these as tools for order status lookups and return processing.

**Archetype Justification**: The system owns persistent state in DynamoDB (product, basket, order tables) and exposes CRUD operations (POST, PUT, DELETE) on business entities via API Gateway. While it has event-driven patterns (EventBridge/SQS for checkout), the primary interaction model is synchronous CRUD with user-specific data.

**Surface flags**:
- has_persistent_data_store: true
- has_http_rpc_surface: true
- has_auth_surface: false
- has_write_operations: true
- has_logging_of_user_data: true

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 1 | **RISK-SAFETY**: 9 | **RISK-QUALITY**: 13 | **INFOs**: 12

This repo has 1 BLOCKER finding and 9 RISK-SAFETY findings. Rule matched: "1-2 BLOCKER → Remediation Required".

Resolve all blockers before any agent deployment — including pilots.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 1 |
| RISK-SAFETY | 9 |
| RISK-QUALITY | 13 |
| INFO | 12 |
| N/A | 0 |
| Not Evaluated (extended) | 1 |
| **Total** | **43** |

**Core Questions Evaluated**: 25
**Extended Questions Triggered**: 7
**Extended Questions Not Triggered**: 1
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: stateful-crud (auto-detected)

Questions that PASS (no finding emitted): API-Q1, AUTH-Q5, STATE-Q2, DISC-Q2 (4 questions)
Findings emitted: 35 questions
Not Evaluated: API-Q6 (1 question)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: The API Gateway resources defined in `lib/apigateway.ts` use `LambdaRestApi` with no authorization configured. No OAuth2 client credentials, API key authentication, mTLS, Cognito authorizers, IAM authorization, or any other machine identity mechanism is present. All three REST APIs (Product Service, Basket Service, Order Service) are publicly accessible without authentication.
- **Gap**: No machine identity authentication exists. Cannot attribute API calls to any principal. Cannot distinguish which agent (or any caller) made a request.
- **Remediation**:
  - **Immediate**: Add IAM authorization or API key requirements to all API Gateway methods in `lib/apigateway.ts`. Example: `product.addMethod('GET', integration, { authorizationType: AuthorizationType.IAM })`.
  - **Target State**: Every API call requires a machine-identifiable credential (IAM SigV4, API key with usage plan, or Cognito app client) that is logged and attributable in CloudTrail.
  - **Estimated Effort**: Medium
  - **Dependencies**: None — this is the foundational blocker that must be resolved first.
- **Evidence**: `lib/apigateway.ts` — no `authorizationType`, no `apiKeyRequired`, no authorizer configurations on any `addMethod` call.

---

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: CDK grants `grantReadWriteData` to all Lambda functions in `lib/microservice.ts`. No mechanism exists to create a scoped agent identity with differentiated access levels. All API Gateway endpoints are accessible equally — no resource policies, no per-method authorization differentiation.
- **Gap**: Cannot create a read-only agent identity that can query products/orders without also having write access to the backing Lambda's permissions.
- **Compensating Controls**:
  - The API Gateway routes only expose GET methods for the ordering service, limiting the agent's HTTP-level options even though Lambda has full DynamoDB access.
  - Create separate API Gateway resources with IAM authorization that scopes to specific methods.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: When implementing AUTH-Q1, use IAM authorization with resource-level policies that differentiate read vs write access per endpoint.
- **Evidence**: `lib/microservice.ts` — `productTable.grantReadWriteData(productFunction)`, `basketTable.grantReadWriteData(basketFunction)`, `orderTable.grantReadWriteData(orderFunction)`.

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization exists anywhere in the system. No auth middleware in Lambda handlers, no per-method authorization in API Gateway, no RBAC or ABAC implementation. Any caller can invoke any HTTP method on any endpoint.
- **Gap**: Cannot enforce "agent can GET but not DELETE" within the same resource type.
- **Compensating Controls**:
  - API Gateway IAM authorization can enforce per-method access via IAM policy conditions on `execute-api:method`.
  - Ordering API only exposes GET methods, inherently limiting actions for that service.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement IAM authorization with policies scoped to specific HTTP methods: `arn:aws:execute-api:*:*:*/GET/*` for read-only agents.
- **Evidence**: `lib/apigateway.ts` — no per-method auth; Lambda handlers perform no permission checks.

#### AUTH-Q4: Identity Propagation and Delegation — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No identity propagation mechanism exists. No JWT parsing, no token exchange, no on-behalf-of flows, no user context headers processed in any Lambda handler. The system cannot distinguish between an agent acting under its own identity vs. acting on behalf of a specific user.
- **Gap**: Cannot determine whose data an agent is accessing or on whose behalf an operation is performed. The ordering service returns data by userName but does not verify the caller has authority to access that user's data.
- **Compensating Controls**:
  - For read-only scope, limit agent to querying only specific userNames via tool-level constraints.
  - Implement API Gateway request context propagation with IAM caller identity.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Design on-behalf-of flow when implementing AUTH-Q1. Propagate caller identity to Lambda via API Gateway context and enforce data-level access controls.
- **Evidence**: `src/ordering/index.js` — `getOrder` reads userName from path parameter without verifying caller authority; no auth headers processed.

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No authentication mechanism exists (AUTH-Q1 blocker), therefore no mechanism to suspend or revoke an individual agent identity exists. Cannot isolate a misbehaving agent without shutting down the entire API.
- **Gap**: No per-agent revocation capability.
- **Compensating Controls**:
  - WAF rules can block specific IP addresses as an emergency measure.
  - When API keys are implemented, individual keys can be revoked via AWS API.
- **Remediation Timeline**: 30–60 days (dependent on AUTH-Q1)
- **Recommendation**: Implement API key authentication with usage plans, providing per-key revocation via `aws apigateway delete-api-key`.
- **Evidence**: `lib/apigateway.ts` — no API keys, no authorizers, no usage plans.

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The basket service calls EventBridge (`PutEventsCommand`) and DynamoDB without any circuit breaker, explicit retry configuration, or timeout settings. The SQS queue has no dead-letter queue (DLQ) configured. Lambda functions use default timeout. No resilience patterns (circuit breakers, bulkheads, retry decorators) exist.
- **Gap**: A cascading failure from EventBridge or DynamoDB throttling propagates uncontrolled to the caller. Failed SQS messages are retried indefinitely without DLQ routing.
- **Compensating Controls**:
  - AWS SDK v3 includes default retry logic (3 retries with exponential backoff) for transient AWS errors.
  - SQS visibility timeout (30s) provides implicit retry.
  - Lambda timeout provides a ceiling on execution time.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add DLQ to SQS queue in `lib/queue.ts`. Configure explicit Lambda timeouts. Consider AWS Lambda Powertools for structured error handling.
- **Evidence**: `src/basket/index.js` — no retry/timeout for PutEventsCommand; `lib/queue.ts` — no `deadLetterQueue` property; `lib/microservice.ts` — no `timeout` property.

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No rate limiting or throttling is configured on any API Gateway endpoint. CDK constructs use `LambdaRestApi` defaults without `deployOptions.throttlingRateLimit`, usage plans, or WAF association.
- **Gap**: A runaway agent loop can invoke endpoints at machine speed. Only AWS account-level API Gateway limits (10,000 RPS) provide protection.
- **Compensating Controls**:
  - API Gateway account-level throttle defaults provide a ceiling.
  - Lambda concurrency limits (1000 per account) provide backpressure.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add `deployOptions: { throttlingRateLimit: 100, throttlingBurstLimit: 200 }` to LambdaRestApi constructs. Create usage plans with per-API-key throttle limits.
- **Evidence**: `lib/apigateway.ts` — no throttle settings, no usage plan, no WAF.

#### DATA-Q1: Sensitive Data Classification ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — B1 evaluated as RISK-SAFETY
- **Finding**: Stage A = Yes — the order table stores PII (firstName, lastName, email, address, paymentMethod, cardInfo). Stage B: B1 — Agent-facing GET /order and GET /order/{userName} endpoints return ALL fields from DynamoDB including PII without filtering. The `getOrder` and `getAllOrders` functions in `src/ordering/index.js` unmarshall and return complete records. B2 — No access control differentiation exists (no OAuth scopes, no RBAC). B3 — No formal classification metadata.
- **Gap**: B1: GET /order endpoints return sensitive PII fields (cardInfo, address, email, paymentMethod) in API responses without field filtering. Under read-only scope, this is RISK-SAFETY. B2: No access differentiation (RISK-SAFETY).
- **Compensating Controls**:
  - Restrict agent tool bindings at the orchestration layer to only expose non-PII fields from responses.
  - Implement response mapping templates in API Gateway to exclude sensitive fields.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add response projection in `src/ordering/index.js` to exclude PII fields (cardInfo, address, email) from GET responses. Create separate agent-facing endpoints with reduced field sets.
- **Evidence**: `src/ordering/index.js` — `getOrder` and `getAllOrders` return full `unmarshall(item)` without field filtering; `lib/database.ts` comment: "order: PK: userName - SK: orderDate -- totalPrice - firstName - lastName - email - address - paymentMethod - cardInfo".

#### DATA-Q2: Data Residency and Sovereignty ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The order table stores PII (names, email, address, payment info) in DynamoDB. No data residency documentation, no explicit region configuration, no cross-region replication restrictions are defined. CDK stack does not pin to a specific region.
- **Gap**: No documented data residency controls for customer PII. An agent reading order data could transmit PII to an LLM provider in a different jurisdiction without restriction.
- **Compensating Controls**:
  - Configure Bedrock agents in the same AWS region as DynamoDB tables.
  - Implement response filtering (DATA-Q1 remediation) to exclude PII before it reaches the agent.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document data residency requirements. Pin CDK stack to specific region. Implement field-level filtering to prevent PII from reaching agent context.
- **Evidence**: `lib/database.ts` — tables created without region restriction; no data residency documentation; `bin/aws-microservices.ts` — no explicit `env: { region: ... }`.

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: All three Lambda handlers log the full event payload on every request: `console.log("request:", JSON.stringify(event, undefined, 2))`. The basket checkout flow additionally logs checkout payloads containing PII (firstName, lastName, email, address, cardInfo). The ordering service logs SQS records containing the same PII via `console.log('Record: %j', record)`.
- **Gap**: Customer PII (names, email, addresses, payment card info) is written to CloudWatch Logs without any redaction, masking, or filtering.
- **Compensating Controls**:
  - Apply CloudWatch Logs data protection policies to detect and mask PII automatically.
  - Reduce log verbosity in production.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Remove full event logging from production code. Implement structured logging that explicitly excludes PII fields. Apply CloudWatch Logs data protection policies as an additional safety net.
- **Evidence**: `src/product/index.js` line 7; `src/basket/index.js` line 7; `src/ordering/index.js` line 7 — all: `console.log("request:", JSON.stringify(event, undefined, 2))`.

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, Swagger, AsyncAPI, GraphQL schema, or Smithy specification files exist in the repository. API routes are defined only in CDK constructs and Lambda handler code.
- **Gap**: Agent tool generation requires manual work — no machine-readable spec exists to auto-generate tool definitions.
- **Compensating Controls**:
  - Export OpenAPI spec from deployed API Gateway via `aws apigateway get-export`.
  - Manually define tool schemas based on code analysis.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Create an `openapi.yaml` documenting all endpoints, request/response schemas, and error codes.
- **Evidence**: No `openapi.*`, `swagger.*`, `asyncapi.*`, `.graphql`, `.smithy` files found.

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Error responses return JSON `{ message, errorMsg, errorStack }` with HTTP 500 for all errors. No error code classification, no retryable indicator, no differentiation between client errors (400) and server errors (500). Stack traces are exposed.
- **Gap**: Agents cannot distinguish retriable errors from terminal errors. Stack trace exposure is a security concern.
- **Compensating Controls**:
  - Agent tools can treat all 500 errors as retriable with exponential backoff.
  - Remove stack traces and add error codes at the handler level.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Implement structured error responses: `{ error_code, message, retryable }`. Differentiate 400 from 500. Remove `errorStack` from responses.
- **Evidence**: `src/product/index.js` lines 42-49; `src/basket/index.js` lines 44-51; `src/ordering/index.js` lines 72-80.

#### STATE-Q7: Graceful Degradation Signaling — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No degradation signaling mechanism exists. No health endpoints, no X-Degraded headers, no Cache-Control headers. When DynamoDB is throttled or EventBridge is unavailable, callers receive a generic 500 error with no indication of degraded mode.
- **Gap**: Agents cannot detect when receiving degraded responses vs authoritative data.
- **Compensating Controls**:
  - API Gateway can add custom headers in integration responses.
  - Agent tools can interpret 500 responses as potential degradation.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a /health endpoint returning granular status. Include Cache-Control and degradation headers in responses.
- **Evidence**: No health endpoints; Lambda handlers return generic 500 on any error; no response headers beyond defaults.

#### DATA-Q3: Selective Query Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: GET /product and GET /order perform full DynamoDB table scans without pagination, filtering, or result size limits. No `limit`, `offset`, or `cursor` parameters are supported. `getAllProducts` and `getAllOrders` use `ScanCommand` without `Limit` parameter.
- **Gap**: Agents retrieving all products or orders get unbounded result sets that can exhaust LLM context windows and increase cost.
- **Compensating Controls**:
  - Agent tools can implement client-side pagination by limiting response processing.
  - DynamoDB scans are eventually limited by table size.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add `Limit` and `ExclusiveStartKey` parameters to scan endpoints for cursor-based pagination. Accept `?limit=N&nextToken=X` query parameters.
- **Evidence**: `src/product/index.js` — `ScanCommand` with no Limit; `src/ordering/index.js` — `getAllOrders` uses ScanCommand without Limit.

#### DATA-Q4: Input Validation and Schema Enforcement — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No input validation in any Lambda handler. `createProduct` and `createBasket` parse the request body and write directly to DynamoDB without field validation, type checking, or schema enforcement. The only validation is a null-check on `userName` in checkout.
- **Gap**: Malformed agent payloads are persisted without rejection. No structured validation error responses.
- **Compensating Controls**:
  - API Gateway request validators can be configured without code changes.
  - Agent tool schemas enforce input constraints at the orchestration layer.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add API Gateway request validators with JSON schemas for POST/PUT endpoints. Add `models` to API methods in CDK.
- **Evidence**: `src/product/index.js` — `JSON.parse(event.body)` with no validation; `src/basket/index.js` — same pattern.

#### DATA-Q5: Temporal Metadata and Freshness — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Orders have an `orderDate` field set server-side as ISO string. Products have no `created_at` or `updated_at` fields. Baskets have no temporal metadata. No Cache-Control or freshness headers in responses.
- **Gap**: Agents cannot determine data freshness for products or baskets. No staleness signaling.
- **Compensating Controls**:
  - Order data has orderDate for temporal context.
  - DynamoDB responses are strongly consistent (not stale) for GetItem operations.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `createdAt` and `updatedAt` fields to product and basket tables. Include `Last-Modified` headers in responses.
- **Evidence**: `src/ordering/index.js` — `orderDate = new Date().toISOString()`; product/basket handlers — no temporal fields.

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No API versioning (`/v1/` prefix, `Accept-Version` header), no schema versioning, no changelog, no breaking change detection in CI, no consumer-driven contract tests.
- **Gap**: API changes break agent tool bindings silently. No mechanism detects breaking changes.
- **Compensating Controls**:
  - CDK code in git provides change history.
  - Manual diff review before `cdk deploy`.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `/v1/` prefix to API routes. Create OpenAPI spec with CI validation.
- **Evidence**: `lib/apigateway.ts` — no version prefix; no schema files; no CI config.

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No distributed tracing (X-Ray, OpenTelemetry) configured. Lambda functions use unstructured `console.log`/`console.error` without correlation IDs or trace ID propagation. No X-Ray tracing enabled in CDK.
- **Gap**: Agent-initiated requests cannot be traced end-to-end across API Gateway → Lambda → DynamoDB → EventBridge → SQS → Lambda.
- **Compensating Controls**:
  - Lambda auto-includes requestId in CloudWatch log prefix.
  - CloudWatch Logs Insights can query across log groups by time window.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Enable X-Ray: add `tracing: Tracing.ACTIVE` to Lambda constructs and API Gateway. Add structured JSON logging with `@aws-lambda-powertools/logger`.
- **Evidence**: `lib/microservice.ts` — no `tracing` property; `src/*/index.js` — `console.log` only.

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No CloudWatch alarms, anomaly detection, or alerting configuration exists in the CDK stack or anywhere in the repository.
- **Gap**: System degradation affecting agent consumers goes undetected.
- **Compensating Controls**:
  - Lambda publishes Errors/Duration metrics and API Gateway publishes 4XX/5XX metrics by default.
  - Alarms can be added without code changes.
- **Remediation Timeline**: 7–14 days
- **Recommendation**: Add CloudWatch alarms for Lambda error rate >1%, API Gateway 5xx rate >5%, and P99 latency >5s.
- **Evidence**: No CloudWatch alarm constructs in any CDK file.

#### ENG-Q1: Infrastructure Governance — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: IaC exists (CDK). However, no CI/CD pipeline enforces peer review on IaC changes, and no drift detection is configured (no AWS Config rules, no automated `cdk diff`).
- **Gap**: IaC present but changes unreviewed and drift undetected. Deployment is manual `cdk deploy`.
- **Compensating Controls**:
  - CDK code in git enables PR-based review if branch protection is configured.
  - `cdk diff` can be run manually.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add CI pipeline running `cdk diff` on PRs. Enable branch protection. Add AWS Config drift detection.
- **Evidence**: CDK files in `lib/`; no `.github/workflows/`; no `buildspec.yml`; no Config rules.

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No CI/CD pipeline exists. The only test file (`test/aws-microservices.test.ts`) is entirely commented out. No contract testing, no OpenAPI validation, no automated testing runs on changes.
- **Gap**: API-breaking changes cannot be caught before production.
- **Compensating Controls**:
  - Manual testing before deployment.
  - CDK synth validates IaC structure.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create GitHub Actions workflow: `cdk synth` + API integration tests + OpenAPI validation.
- **Evidence**: `test/aws-microservices.test.ts` — all code commented out; no CI configuration files.

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No controlled rollback mechanism. Manual `cdk deploy` with CloudFormation default rollback on failed deployments. No blue/green, no canary, no CodeDeploy, no feature flags.
- **Gap**: Cannot quickly roll back a successfully deployed but behaviorally broken change.
- **Compensating Controls**:
  - CloudFormation maintains stack history for rollback of failed deployments.
  - Can redeploy previous git commit manually.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement Lambda aliases + CodeDeploy with automatic rollback on CloudWatch alarm triggers.
- **Evidence**: No aliases, no CodeDeploy, no canary config in CDK.

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Zero effective test coverage. The single test file is entirely commented out. No API tests, integration tests, or contract tests exist.
- **Gap**: No automated verification of API behavior for agent consumers.
- **Compensating Controls**:
  - Manual testing.
  - CDK synth provides structural validation of IaC.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Write integration tests for all API endpoints using Jest + supertest or AWS SDK calls against a deployed stack.
- **Evidence**: `test/aws-microservices.test.ts` — all assertions commented out; no other test files.

#### ENG-Q5: Encryption at Rest — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: DynamoDB tables do not specify encryption configuration in CDK. DynamoDB encrypts at rest by default with AWS-owned keys. No customer-managed KMS keys configured for the order table containing PII.
- **Gap**: Data encrypted with AWS-owned keys (default) rather than customer-managed KMS. For PII data in the order table, CMK provides additional audit trail and access control.
- **Compensating Controls**:
  - AWS-owned encryption provides baseline protection.
  - DynamoDB default encryption meets most compliance requirements.
- **Remediation Timeline**: 7–14 days
- **Recommendation**: Add `encryption: TableEncryption.CUSTOMER_MANAGED` with KMS key to the order table in `lib/database.ts`.
- **Evidence**: `lib/database.ts` — no `encryption` property on Table constructs.

---

## INFOs — Architecture and Design Inputs

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Write endpoints lack idempotency keys. Product creation generates UUID server-side. Basket checkout has no idempotency protection. Basket PUT uses PutItem which is naturally idempotent (overwrite by key).
- **Implication**: If agent scope expands to write-enabled, duplicate orders could be created on retry.
- **Recommendation**: Add idempotency key support to POST /basket/checkout before enabling write-enabled agent scope.
- **Evidence**: `src/product/index.js` — `uuidv4()` server-side generation; `src/basket/index.js` — no idempotency check in `checkoutBasket`.

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: All API responses are structured JSON with consistent envelope: `{ message: string, body: object }`. Responses are well-suited for LLM consumption.
- **Implication**: No format conversion needed for agent tool integration. JSON is directly parseable.
- **Recommendation**: Document response schemas in OpenAPI spec when created.
- **Evidence**: All Lambda handlers return `JSON.stringify({ message, body })`.

### API-Q7: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: Basket checkout emits EventBridge events (source: `com.swn.basket.checkoutbasket`, detail type: `CheckoutBasket`). Product CRUD and order creation do not emit events.
- **Implication**: Event-reactive agents can subscribe to checkout events. Product and order changes are not observable via events.
- **Recommendation**: Add DynamoDB Streams or EventBridge events for product/order state changes if event-reactive agents are planned.
- **Evidence**: `src/basket/index.js` — `publishCheckoutBasketEvent`; `lib/eventbus.ts` — bus and rule configuration.

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limit documentation. No rate limit response headers returned. API Gateway default limits apply silently.
- **Implication**: Agents cannot self-throttle based on remaining quota.
- **Recommendation**: Configure usage plans and return `X-RateLimit-Remaining` headers.
- **Evidence**: `lib/apigateway.ts` — no throttle config or usage plans.

### AUTH-Q6: Immutable Audit Logging ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO (has_auth_surface is false, no write operations invoked by agent)
- **Finding**: No CloudTrail configuration in CDK. No immutable audit log storage. Lambda console.log statements are not immutable or tamper-evident.
- **Implication**: When authentication is implemented, immutable audit logging must be added simultaneously.
- **Recommendation**: Enable CloudTrail with log file validation and S3 object lock as part of AUTH-Q1 remediation.
- **Evidence**: No CloudTrail construct; no S3 audit bucket; no log integrity configuration.

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The checkout flow is multi-step (get basket → prepare payload → publish to EventBridge → delete basket) with no compensation logic. If EventBridge publish succeeds but basket deletion fails, the system is inconsistent.
- **Implication**: Write-enabled agents would need saga patterns before executing checkout.
- **Recommendation**: Implement compensation logic before expanding agent scope to write-enabled.
- **Evidence**: `src/basket/index.js` — `checkoutBasket` function: sequential steps without rollback.

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No optimistic locking, version fields, or conditional writes. PutItem overwrites without condition. UpdateItem has no ConditionExpression.
- **Implication**: Multiple write-enabled agent instances would create race conditions.
- **Recommendation**: Add DynamoDB conditional writes (version attribute + ConditionExpression) before enabling concurrent write-enabled agents.
- **Evidence**: `src/product/index.js` — PutItemCommand/UpdateItemCommand without conditions.

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No per-caller operation caps. Scan operations (getAllProducts, getAllBaskets, getAllOrders) return unbounded result sets. No bulk operation limits.
- **Implication**: Read-only agents receive large result sets. Write-enabled agents would have unbounded blast radius.
- **Recommendation**: Add pagination limits. Design per-caller transaction caps before enabling writes.
- **Evidence**: `src/product/index.js` — ScanCommand without Limit; `src/ordering/index.js` — same.

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No draft/pending state mechanism. All writes are immediately committed (PutItem, DeleteItem). No reviewable intermediate state.
- **Implication**: Write-enabled agents would commit changes without human review.
- **Recommendation**: Add status fields to support PENDING/CONFIRMED states for future write agents.
- **Evidence**: No status-based workflows; PutItemCommand persists immediately.

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No approval workflow, no confirmation steps, no human-in-the-loop gates exist.
- **Implication**: No mechanism for human oversight of agent operations exists.
- **Recommendation**: Consider Step Functions with human approval tasks for high-risk operations when expanding scope.
- **Evidence**: No approval-related code or configuration.

### HITL-Q3: Sandbox/Staging Environment

- **Severity**: INFO
- **Finding**: No staging environment configuration. Single CDK stack. No docker-compose for local testing. No seed data scripts. No LocalStack configuration.
- **Implication**: Agent behavior can only be tested against production. First-time integration bugs affect live data.
- **Recommendation**: Create a separate staging stack. Consider DynamoDB Local or LocalStack for local agent testing.
- **Evidence**: Single stack in `lib/aws-microservices-stack.ts`; no environment differentiation.

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality monitoring, completeness metrics, or profiling. No DynamoDB TTL. No data lifecycle management.
- **Implication**: Agents may reason on stale basket data (abandoned carts) without awareness.
- **Recommendation**: Implement DynamoDB TTL on basket table. Add data freshness metrics.
- **Evidence**: `lib/database.ts` — no TTL; no quality monitoring.

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: PASS
- **Finding**: The application exposes REST APIs via three API Gateway instances (Product Service, Basket Service, Order Service) with well-defined routes. Integration is through HTTP endpoints — not direct database access, file-based exchange, or UI automation.
- **Gap**: None — API surface exists and is the integration mechanism.
- **Recommendation**: N/A
- **Evidence**: `lib/apigateway.ts` — three LambdaRestApi instances with explicit route definitions.

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: No machine-readable API specification exists.
- **Gap**: No OpenAPI, AsyncAPI, or equivalent spec for agent tool generation.
- **Recommendation**: Create OpenAPI spec.
- **Evidence**: No spec files found in repository.

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: Errors return HTTP 500 with `{ message, errorMsg, errorStack }`. No error codes, no retryable indicators. Stack traces exposed.
- **Gap**: Agents cannot distinguish error types. Security risk from stack trace exposure.
- **Recommendation**: Add error codes and retryable boolean. Remove stack traces. Differentiate 400/500.
- **Evidence**: Error handlers in all three Lambda functions.

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Write operations lack idempotency keys. Checkout has no duplicate protection.
- **Gap**: Non-idempotent writes risk duplication on retry.
- **Recommendation**: Add idempotency keys before expanding to write-enabled scope.
- **Evidence**: `src/product/index.js`, `src/basket/index.js` — no idempotency mechanisms.

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: JSON responses with consistent `{ message, body }` envelope.
- **Implication**: Ideal for LLM consumption.
- **Recommendation**: Document in OpenAPI spec.
- **Evidence**: All Lambda handler success responses.

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has operations >30s OR long-running workflows
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: Partial event coverage — basket checkout emits EventBridge events; product/order CRUD does not.
- **Implication**: Only checkout is observable via events for reactive agents.
- **Recommendation**: Consider adding events for product/order changes.
- **Evidence**: `src/basket/index.js`, `lib/eventbus.ts`.

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit documentation or headers.
- **Implication**: Agents cannot self-throttle.
- **Recommendation**: Add usage plans and rate limit headers.
- **Evidence**: `lib/apigateway.ts` — no throttle config.

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: No authentication on any API Gateway endpoint. All endpoints publicly accessible.
- **Gap**: No machine identity mechanism. Cannot attribute calls.
- **Recommendation**: Implement API Gateway authorization (IAM, Cognito, or API keys).
- **Evidence**: `lib/apigateway.ts` — no auth config on any method.

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: All Lambda functions get `grantReadWriteData`. No differentiated access levels for callers.
- **Gap**: Cannot create read-only agent identity.
- **Recommendation**: Implement per-method IAM authorization.
- **Evidence**: `lib/microservice.ts` — `grantReadWriteData` on all tables.

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization. Any caller can invoke any method.
- **Gap**: Cannot enforce read-only access for agents.
- **Recommendation**: Implement IAM authorization with per-method policy conditions.
- **Evidence**: `lib/apigateway.ts` — no per-method auth.

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: RISK-SAFETY
- **Finding**: No identity propagation. Cannot distinguish agent-as-self from agent-on-behalf-of-user.
- **Gap**: Cannot determine whose data an agent accesses on behalf of.
- **Recommendation**: Design on-behalf-of flow with AUTH-Q1 implementation.
- **Evidence**: No auth processing in Lambda handlers.

#### AUTH-Q5: Credential Management
- **Severity**: PASS
- **Finding**: The system uses IAM roles for all AWS service access (DynamoDB, EventBridge, SQS). No credentials are hardcoded, embedded in code, or stored in environment variables. This is the recommended approach for Lambda-based services.
- **Gap**: None — IAM roles eliminate credential management concerns for current integrations.
- **Recommendation**: N/A for current state. When adding external integrations requiring credentials, use Secrets Manager.
- **Evidence**: `lib/microservice.ts` — `grantReadWriteData` and `grantPutEventsTo` provide IAM-based access; environment variables contain only table names and event config.

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO (has_auth_surface=false)
- **Finding**: No CloudTrail, no immutable audit storage, no principal attribution.
- **Gap**: No audit trail for API calls.
- **Recommendation**: Enable CloudTrail with log validation when auth is implemented.
- **Evidence**: No CloudTrail construct in CDK.

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: No auth mechanism exists, so no per-agent suspension capability.
- **Gap**: Cannot isolate misbehaving agent without shutting down entire API.
- **Recommendation**: Implement API keys with per-key revocation.
- **Evidence**: `lib/apigateway.ts` — no API keys or authorizers.

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Multi-step checkout without compensation logic.
- **Gap**: Partial failures leave inconsistent state.
- **Recommendation**: Add saga pattern before write-enabled agents.
- **Evidence**: `src/basket/index.js` — `checkoutBasket` sequential steps.

#### STATE-Q2: Queryable Current State
- **Severity**: PASS
- **Finding**: GET endpoints exist for all resource types: GET /product, GET /product/{id}, GET /basket/{userName}, GET /order/{userName}. Agents can inspect current state before deciding actions.
- **Gap**: None — state is queryable.
- **Recommendation**: N/A
- **Evidence**: `lib/apigateway.ts` — GET methods on all resources.

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No optimistic locking or conditional writes.
- **Gap**: No concurrency protection for writes.
- **Recommendation**: Add conditional writes before write-enabled agents.
- **Evidence**: `src/product/index.js` — no ConditionExpression.

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: No circuit breakers, no explicit retry config, no timeouts, no DLQ on SQS queue.
- **Gap**: Cascading failures propagate uncontrolled.
- **Recommendation**: Add DLQ to SQS. Configure Lambda timeouts. Consider Powertools.
- **Evidence**: `lib/queue.ts` — no DLQ; `lib/microservice.ts` — no timeout.

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No rate limiting on API Gateway. No usage plans or WAF.
- **Gap**: Runaway agent loops can overwhelm services.
- **Recommendation**: Add throttle settings and usage plans.
- **Evidence**: `lib/apigateway.ts` — no throttle config.

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No per-caller caps. Unbounded scan results.
- **Gap**: No business-domain limits.
- **Recommendation**: Add pagination and caps.
- **Evidence**: Unbounded ScanCommand in product/ordering handlers.

#### STATE-Q7: Graceful Degradation Signaling
- **Severity**: RISK-QUALITY
- **Finding**: No degradation signaling. Generic 500 on all failures. No health endpoints.
- **Gap**: Agents cannot detect degraded responses.
- **Recommendation**: Add health endpoint and degradation headers.
- **Evidence**: No health endpoints; generic error responses.

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No draft/pending mechanism. Writes immediately committed.
- **Gap**: No reviewable intermediate state.
- **Recommendation**: Add status fields for future write agents.
- **Evidence**: No status workflows in code.

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No approval gates or confirmation steps.
- **Gap**: No human oversight mechanism.
- **Recommendation**: Consider Step Functions approval tasks.
- **Evidence**: No approval code or configuration.

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: INFO
- **Finding**: No staging environment. Single CDK stack. No local testing setup.
- **Gap**: Agent testing only possible in production.
- **Recommendation**: Create staging stack with synthetic data.
- **Evidence**: Single stack; no environment config.

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — B1 fires as RISK-SAFETY
- **Finding**: Order table stores PII. GET /order endpoints return all fields including PII without filtering.
- **Gap**: Agent-facing APIs leak sensitive fields.
- **Recommendation**: Implement field filtering to exclude PII from agent responses.
- **Evidence**: `src/ordering/index.js` — full unmarshall return; `lib/database.ts` — PII schema.

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: PII stored without region pinning or residency documentation.
- **Gap**: No data residency controls for customer PII.
- **Recommendation**: Document requirements; pin region; filter PII from agent access.
- **Evidence**: `lib/database.ts`; no region configuration.

#### DATA-Q3: Selective Query Support
- **Severity**: RISK-QUALITY
- **Finding**: Unbounded DynamoDB scans without pagination.
- **Gap**: Agents get unbounded result sets.
- **Recommendation**: Add pagination parameters.
- **Evidence**: `src/product/index.js`, `src/ordering/index.js` — ScanCommand without Limit.

#### DATA-Q4: Input Validation and Schema Enforcement
- **Severity**: RISK-QUALITY
- **Finding**: No input validation. Request bodies written directly to DynamoDB.
- **Gap**: Malformed payloads accepted without rejection.
- **Recommendation**: Add API Gateway request validators.
- **Evidence**: `src/product/index.js`, `src/basket/index.js` — no validation.

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK-QUALITY
- **Finding**: Orders have orderDate. Products/baskets lack temporal metadata. No freshness headers.
- **Gap**: Cannot determine data freshness for products/baskets.
- **Recommendation**: Add created_at/updated_at fields.
- **Evidence**: `src/ordering/index.js` — orderDate; product/basket — no temporal fields.

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: Full event payloads including PII logged to CloudWatch.
- **Gap**: Customer PII in logs without redaction.
- **Recommendation**: Remove full event logging; add log scrubbing.
- **Evidence**: All `src/*/index.js` — `console.log("request:", JSON.stringify(event...))`.

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality monitoring or metrics.
- **Implication**: Agent may reason on incomplete data.
- **Recommendation**: Add TTL for stale baskets.
- **Evidence**: No data quality tooling.

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: No API versioning, no schema docs, no breaking change detection.
- **Gap**: Silent breaking changes to agent tools.
- **Recommendation**: Add version prefix and OpenAPI validation.
- **Evidence**: `lib/apigateway.ts` — no versioning.

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: PASS
- **Finding**: Field names are human-readable and semantically meaningful: `userName`, `orderDate`, `totalPrice`, `firstName`, `lastName`, `productId`, `productName`, `quantity`, `price`, `category`, `id`. No legacy abbreviations.
- **Gap**: None — naming is clear.
- **Recommendation**: N/A
- **Evidence**: `lib/database.ts` schemas; `src/basket/checkoutbasketevents.json`.

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No data catalog. DynamoDB schemas documented only in CDK code comments.
- **Implication**: Agent tool builders must read source for data semantics.
- **Recommendation**: Create schema reference documentation.
- **Evidence**: `lib/database.ts` — comments only.

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: No X-Ray or OpenTelemetry. Unstructured console.log without correlation IDs.
- **Gap**: Cannot trace agent requests end-to-end.
- **Recommendation**: Enable X-Ray; add structured logging.
- **Evidence**: `lib/microservice.ts` — no tracing; `src/*/index.js` — console.log.

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: No CloudWatch alarms or alerting.
- **Gap**: Degradation undetected.
- **Recommendation**: Add alarms for error rates and latency.
- **Evidence**: No alarm resources in CDK.

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics. No PutMetricData calls.
- **Implication**: Cannot measure agent interaction quality.
- **Recommendation**: Publish order completion and checkout success metrics.
- **Evidence**: No metric publishing in Lambda handlers.

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance
- **Severity**: RISK-QUALITY
- **Finding**: IaC (CDK) present. No CI/CD enforcement or drift detection.
- **Gap**: Unreviewed changes; no drift detection.
- **Recommendation**: Add CI pipeline with cdk diff; enable branch protection.
- **Evidence**: CDK files; no CI config.

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: No CI/CD. Test file commented out.
- **Gap**: No automated API testing.
- **Recommendation**: Create CI pipeline with tests.
- **Evidence**: `test/aws-microservices.test.ts` — commented out.

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: No controlled rollback beyond CloudFormation default.
- **Gap**: Cannot roll back behaviorally broken deployments.
- **Recommendation**: Add Lambda aliases + CodeDeploy.
- **Evidence**: No aliases, CodeDeploy, or canary config.

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: Zero effective test coverage.
- **Gap**: No automated API verification.
- **Recommendation**: Write integration tests for all endpoints.
- **Evidence**: `test/aws-microservices.test.ts` — commented out.

#### ENG-Q5: Encryption at Rest
- **Severity**: RISK-QUALITY
- **Finding**: DynamoDB default encryption (AWS-owned keys). No CMK for PII data.
- **Gap**: No customer-managed encryption for sensitive data.
- **Recommendation**: Add CMK encryption to order table.
- **Evidence**: `lib/database.ts` — no encryption property.

---

## Evidence Index

### Infrastructure as Code
| File | Questions Referenced |
|------|---------------------|
| lib/apigateway.ts | API-Q1, API-Q2, API-Q8, AUTH-Q1, AUTH-Q3, AUTH-Q7, STATE-Q5, DISC-Q1, ENG-Q3 |
| lib/database.ts | DATA-Q1, DATA-Q2, DATA-Q5, DATA-Q7, DISC-Q2, ENG-Q5 |
| lib/microservice.ts | AUTH-Q2, AUTH-Q5, OBS-Q1, STATE-Q4, ENG-Q3 |
| lib/eventbus.ts | API-Q7 |
| lib/queue.ts | STATE-Q4 |
| lib/aws-microservices-stack.ts | HITL-Q3, OBS-Q2 |
| bin/aws-microservices.ts | DATA-Q2 |

### Source Code
| File | Questions Referenced |
|------|---------------------|
| src/product/index.js | API-Q3, API-Q4, API-Q5, STATE-Q3, STATE-Q6, DATA-Q3, DATA-Q4, DATA-Q6 |
| src/basket/index.js | API-Q3, API-Q4, API-Q5, API-Q7, STATE-Q1, STATE-Q3, STATE-Q4, DATA-Q4, DATA-Q6 |
| src/ordering/index.js | API-Q3, API-Q5, DATA-Q1, DATA-Q3, DATA-Q5, DATA-Q6 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| src/basket/checkoutbasketevents.json | DISC-Q2 |
| cdk.json | ENG-Q1 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| package.json | ENG-Q2 |

### Test Files
| File | Questions Referenced |
|------|---------------------|
| test/aws-microservices.test.ts | ENG-Q2, ENG-Q4 |
