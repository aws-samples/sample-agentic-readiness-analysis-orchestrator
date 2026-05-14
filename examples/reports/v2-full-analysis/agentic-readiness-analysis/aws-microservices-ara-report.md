# Agentic Readiness Analysis Report

**Target**: ./services/aws-microservices
**Date**: 2026-04-17
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**Repository Type**: application
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P0
**Tags**: microservices, serverless, event-driven
**Context**: Event-driven serverless microservices (product, basket, ordering) with Lambda, DynamoDB, EventBridge, SQS. The agent will invoke these as tools for order status lookups and return processing.

**Archetype Justification**: All three microservices own DynamoDB tables with CRUD operations on business entities (products, baskets, orders). User-specific data keyed by userName. Full entity lifecycle management in checkout flow (basket → EventBridge → SQS → order creation → basket deletion).

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 2 | **RISK-SAFETY**: 9 | **RISK-QUALITY**: 16 | **INFOs**: 16

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 2 |
| RISK-SAFETY | 9 |
| RISK-QUALITY | 16 |
| INFO | 16 |
| N/A | 0 |
| Not Evaluated (extended) | 0 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 19
**Extended Questions Not Triggered**: 0
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: stateful-crud (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: `lib/apigateway.ts` creates three `LambdaRestApi` instances (productApi, basketApi, orderApi) with **no authorizer configured**. No Cognito user pool, no API key requirement, no IAM authorization, no Lambda authorizer. All API Gateway endpoints are completely open and unauthenticated. Any caller — agent or otherwise — can invoke any endpoint without presenting identity.
- **Gap**: No authentication mechanism exists on any API Gateway endpoint. The system cannot identify which agent (or caller) made a request. There is no principal to attribute in audit logs.
- **Remediation**:
  - **Immediate**: Add API Gateway API key authentication to all three REST APIs with usage plans. Create distinct API keys per agent identity for attribution. This can be done in CDK by adding `apiKeyRequired: true` to methods and creating `UsagePlan` + `ApiKey` resources.
  - **Target State**: All API endpoints require authentication via API keys (short-term) or OAuth2 client credentials (long-term). Each agent identity has a unique API key or client credential, logged and attributable.
  - **Estimated Effort**: Medium (2–4 weeks for API key setup with CDK; 4–8 weeks for OAuth2/Cognito integration)
  - **Dependencies**: AUTH-Q2 (scoped permissions) and AUTH-Q7 (identity suspension) cannot be implemented until identity exists.
- **Evidence**: `lib/apigateway.ts` (lines creating LambdaRestApi with no `defaultMethodOptions` authorizer), `lib/aws-microservices-stack.ts`

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: The order DynamoDB table stores PII and payment card information: `firstName`, `lastName`, `email`, `address`, `paymentMethod`, `cardInfo` (documented in `lib/database.ts` comments: `order : PK: userName - SK: orderDate -- totalPrice - firstName - lastName - email - address - paymentMethod - cardInfo`). The `src/basket/index.js` `prepareOrderPayload` function aggregates this data from checkout requests. No data classification tags exist on any DynamoDB table in `lib/database.ts`. No field-level encryption. No Macie integration. No column-level access controls.
- **Gap**: Sensitive data (PII, payment card info) is stored without classification, tagging, or field-level protection. An agent reading from the order table would receive unprotected PII including card information with no access controls distinguishing sensitive from non-sensitive fields.
- **Remediation**:
  - **Immediate**: Add resource-level tags to all DynamoDB tables in `lib/database.ts` classifying data sensitivity (e.g., `DataClassification: Confidential` for the order table). Implement field-level encryption for `cardInfo` and `email` using DynamoDB client-side encryption with KMS.
  - **Target State**: All tables are tagged with data classification levels. PII and payment fields are encrypted at the field level with customer-managed KMS keys. Agent-facing GET endpoints redact or exclude sensitive fields based on caller permissions.
  - **Estimated Effort**: High (4–8 weeks — field-level encryption requires application code changes in all three services plus KMS key provisioning)
  - **Dependencies**: AUTH-Q1 (machine identity) must be resolved first to enforce field-level access controls per caller.
- **Evidence**: `lib/database.ts` (order table schema comments), `src/basket/index.js` (`prepareOrderPayload` function), `src/ordering/index.js` (`createOrder` function marshalling full payload)

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: `lib/microservice.ts` grants `grantReadWriteData()` to all Lambda functions on their respective DynamoDB tables. This provides table-level DynamoDB read/write access. No API-level authorization exists (AUTH-Q1 found no auth layer). No resource-level IAM policies. No agent-specific scoped permissions are possible since there is no authentication layer to differentiate callers.
- **Gap**: No mechanism to grant an agent read-only access to specific resources without inheriting broader privileges. All callers have equal access to all operations.
- **Compensating Controls**:
  - Deploy a read-only API Gateway stage or separate API that only exposes GET methods, with the agent's DNS pointing exclusively to that stage.
  - Use API Gateway resource policies to restrict write methods (POST/PUT/DELETE) to specific source IPs or VPC endpoints.
- **Remediation Timeline**: 30–60 days (dependent on AUTH-Q1 resolution)
- **Recommendation**: After implementing API key auth (AUTH-Q1), create usage plans with method-level throttling. Long-term, implement IAM authorization or Cognito scopes to enforce least-privilege per agent identity.
- **Evidence**: `lib/microservice.ts` (`grantReadWriteData` calls), `lib/apigateway.ts` (no authorization on methods)

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No authorization middleware exists in any Lambda handler (`src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js`). All HTTP methods are routed purely by `event.httpMethod` switch statements with no permission checks. An agent (or anyone) can call `DELETE /product/{id}` as easily as `GET /product`. No ABAC, no RBAC, no action-level checks.
- **Gap**: No action-level authorization. Cannot enforce read-only access for an agent at the application layer.
- **Compensating Controls**:
  - Create a separate read-only API Gateway deployment that only exposes GET method resources.
  - Add Lambda@Edge or API Gateway request validators that reject non-GET methods for agent-designated API keys.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add authorization middleware to Lambda handlers that checks the caller's identity (once AUTH-Q1 is resolved) against an action permission matrix. Alternatively, deploy separate read-only and read-write API Gateway stages.
- **Evidence**: `src/product/index.js` (switch on httpMethod with no auth checks), `src/basket/index.js`, `src/ordering/index.js`

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No CloudTrail configuration in CDK IaC. No CloudWatch log retention policies defined. Lambda functions use `console.log` and `console.error` for logging (unstructured). No structured audit logging with principal attribution. No log immutability configuration (no S3 bucket with object lock, no CloudTrail log file validation). CloudWatch Logs exist by default for Lambda but are not configured for retention or immutability.
- **Gap**: No immutable audit trail. Cannot prove which caller performed which action. Default CloudWatch logs have no retention policy and no immutability guarantees.
- **Compensating Controls**:
  - Enable CloudTrail for the AWS account (account-level, outside this repo) to capture API Gateway invocations.
  - Set CloudWatch log retention policies manually via AWS Console for all three Lambda function log groups.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add CloudTrail configuration in CDK with log file validation enabled and S3 bucket with object lock. Set CloudWatch log retention policies in CDK for all Lambda functions. Add structured JSON logging with caller identity fields.
- **Evidence**: `lib/microservice.ts` (no log retention configuration on Lambda), `lib/aws-microservices-stack.ts` (no CloudTrail resource)

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No API key management, no Cognito user pool, no service account definitions exist in the codebase. Since AUTH-Q1 found no authentication mechanism, there is no agent identity to suspend or revoke. If an agent misbehaves, the only option is to take down the entire API Gateway or modify security groups — affecting all consumers.
- **Gap**: Cannot suspend or revoke an individual agent identity without disrupting all other callers.
- **Compensating Controls**:
  - Implement API Gateway resource policies to block specific source IPs as an emergency measure.
  - Use WAF rules to block specific user agents or request patterns associated with a misbehaving agent.
- **Remediation Timeline**: 30–60 days (dependent on AUTH-Q1 resolution)
- **Recommendation**: After implementing API key auth (AUTH-Q1), agent identities can be suspended by disabling or deleting individual API keys. Long-term, implement Cognito app clients with immediate revocation capability.
- **Evidence**: `lib/apigateway.ts` (no API key or auth configuration), `lib/aws-microservices-stack.ts`

#### STATE-Q1: Compensation and Rollback ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The checkout flow in `src/basket/index.js` executes a multi-step sequence: (1) get basket, (2) prepare order payload, (3) publish to EventBridge via `publishCheckoutBasketEvent`, (4) delete basket via `deleteBasket`. If step 3 succeeds but step 4 fails, the basket remains but the order event is in-flight. If EventBridge delivery fails after basket deletion in step 4, the basket is permanently lost with no order created. No saga pattern, no compensating transactions, no undo endpoints, no Step Functions error handling.
- **Gap**: No compensation or rollback for the multi-step checkout operation. Partial failures leave the system in inconsistent states.
- **Compensating Controls**:
  - Reverse the order: delete basket after confirming order creation (requires synchronous confirmation from ordering service).
  - Add a DLQ on the SQS queue (already partially in place with `OrderQueue`) and monitor for failed order creation events.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement a Step Functions workflow for the checkout flow with explicit error handling and rollback states. Alternatively, implement a saga pattern with compensating transactions (re-create basket if order creation fails).
- **Evidence**: `src/basket/index.js` (`checkoutBasket` function — sequential steps with no error compensation), `lib/queue.ts` (SQS queue with no DLQ configured)

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No resilience patterns found in any service. `src/product/ddbClient.js`, `src/basket/ddbClient.js`, `src/basket/eventBridgeClient.js`, and `src/ordering/ddbClient.js` all create AWS SDK clients with default configuration — no custom timeout, no retry configuration, no circuit breaker logic. No resilience libraries (Resilience4j, Polly, retry decorators) in any `package.json`. No exponential backoff patterns in application code.
- **Gap**: No circuit breakers, custom retry logic, or timeout configuration on external dependency calls. A DynamoDB or EventBridge outage cascades directly to API consumers including agents.
- **Compensating Controls**:
  - Configure API Gateway integration timeouts to prevent long-hanging requests.
  - Set Lambda function timeout explicitly in CDK (currently defaults) to bound execution time.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure AWS SDK client timeouts and retry strategies in all `ddbClient.js` and `eventBridgeClient.js` files. Add circuit breaker middleware or use AWS SDK built-in retry configuration with exponential backoff.
- **Evidence**: `src/product/ddbClient.js`, `src/basket/ddbClient.js`, `src/basket/eventBridgeClient.js`, `src/ordering/ddbClient.js` (all default client configuration)

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No API Gateway throttling configuration in `lib/apigateway.ts`. No usage plans (`UsagePlan`), no throttle settings, no method-level throttling. No WAF rules defined anywhere in CDK IaC. No application-level rate limiting middleware in any Lambda handler. API Gateway default throttling (10,000 requests/second account-wide) is the only protection, shared across all three APIs.
- **Gap**: No rate limiting at any layer. A runaway agent loop could overwhelm DynamoDB tables and Lambda concurrency limits, affecting all consumers.
- **Compensating Controls**:
  - API Gateway has default account-level throttling (10,000 RPS) which provides minimal protection.
  - DynamoDB PAY_PER_REQUEST billing absorbs traffic spikes but at unbounded cost.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add API Gateway usage plans with throttle limits per API key in `lib/apigateway.ts`. Set method-level throttling on write endpoints. Consider adding WAF rate-based rules for additional protection.
- **Evidence**: `lib/apigateway.ts` (no usage plans or throttle configuration), `lib/aws-microservices-stack.ts`

#### DATA-Q2: Data Residency and Sovereignty ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: `bin/aws-microservices.ts` has the `env` property commented out — no region or account is specified. The CDK stack is "environment-agnostic" per the inline comment. No data residency documentation exists. No GDPR/LGPD compliance references. DynamoDB tables are created without explicit region constraints. The deployment region is determined entirely at deploy-time with no guardrails.
- **Gap**: No data residency configuration. The order table containing PII and payment card info could be deployed in any region. An agent sending this data to an LLM endpoint in a different jurisdiction could create compliance violations.
- **Compensating Controls**:
  - Document the intended deployment region and enforce it via CDK environment configuration.
  - Use AWS Organizations SCPs to restrict resource creation to approved regions.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Uncomment and set the `env` property in `bin/aws-microservices.ts` to pin the deployment region. Add data residency documentation. For P0 services handling PII, document which regions are approved for deployment.
- **Evidence**: `bin/aws-microservices.ts` (commented-out env configuration), `lib/database.ts` (no region-specific configuration)

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: All three Lambda handlers log full request events with `console.log("request:", JSON.stringify(event, undefined, 2))` at the top of each handler. `src/basket/index.js` logs `checkoutPayload` which contains `firstName`, `lastName`, `email`, `address`, `paymentMethod`, `cardInfo`. `src/ordering/index.js` logs `basketCheckoutEvent` with the same PII fields via `console.log(basketCheckoutEvent)`. No log scrubbing middleware. No PII masking libraries. No CloudWatch log filters. No Macie integration.
- **Gap**: PII (names, email, address, payment card info) is logged in plaintext to CloudWatch Logs. Agent-initiated requests containing or returning PII will have that PII persisted in logs.
- **Compensating Controls**:
  - Add CloudWatch log metric filters to detect PII patterns and alert on exposure.
  - Implement aggressive CloudWatch log retention (7 days) to limit PII exposure window.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add log scrubbing middleware to all Lambda handlers that redacts PII fields before logging. Remove `console.log(checkoutPayload)` and `console.log(basketCheckoutEvent)` that log full PII payloads. Use structured JSON logging with explicit field inclusion (allowlist) rather than logging entire objects.
- **Evidence**: `src/basket/index.js` (lines logging checkoutPayload with PII), `src/ordering/index.js` (lines logging basketCheckoutEvent with PII), `src/product/index.js` (logs full request events)

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, GraphQL, or Smithy specification files found anywhere in the repository. The API structure is defined only in CDK code (`lib/apigateway.ts`) and Lambda handler switch statements. Agent tool definitions must be manually authored by reading the source code.
- **Gap**: No machine-readable API specification. Automated tool generation for agents is not possible.
- **Compensating Controls**:
  - Manually author agent tool definitions based on the CDK route definitions in `lib/apigateway.ts`.
  - Export API Gateway specifications post-deployment via AWS Console or CLI.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Generate an OpenAPI specification from the deployed API Gateway stages (AWS Console → Export). Commit the spec to the repository and integrate spec generation into the CDK deployment process.
- **Evidence**: No OpenAPI/AsyncAPI/GraphQL/Smithy files found. `lib/apigateway.ts` (API routes defined only in CDK)

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: All three Lambda handlers return the same error format: `{ statusCode: 500, body: JSON.stringify({ message, errorMsg, errorStack }) }`. No structured error codes (e.g., `PRODUCT_NOT_FOUND`, `VALIDATION_ERROR`). No retryable boolean or error categorization. Error stacks (`e.stack`) are exposed in production responses — a security concern and unhelpful for agent decision-making.
- **Gap**: Agents cannot distinguish retriable errors (timeout, throttle) from terminal errors (validation failure, not found). Error stacks are leaked in production.
- **Compensating Controls**:
  - Agents can use HTTP status code 500 as a generic retry signal with exponential backoff.
  - API Gateway can be configured to return structured error responses for common cases (4xx, 5xx).
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Implement structured error responses with error codes, error categories (retriable vs terminal), and remove error stack traces from production responses. Use consistent error schema across all three services.
- **Evidence**: `src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js` (catch blocks returning errorStack)

#### API-Q6: Asynchronous Operation Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The checkout flow is asynchronous: `POST /basket/checkout` publishes to EventBridge → SQS → ordering Lambda creates the order. However, the checkout endpoint returns immediately after publishing the event and deleting the basket — no job ID is returned, no polling endpoint exists, no webhook callback is configured. An agent has no way to track whether the checkout completed successfully.
- **Gap**: Async operation exists but has no tracking mechanism. Agent cannot determine checkout completion status.
- **Compensating Controls**:
  - Agent can poll `GET /order/{userName}` to check if the order appeared after checkout.
  - Add CloudWatch metrics for successful order creation events.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Return a checkout correlation ID from `POST /basket/checkout`. Add a `GET /checkout/{correlationId}/status` endpoint. Alternatively, add the order to the order table in a "pending" state synchronously and update it when the SQS consumer processes it.
- **Evidence**: `src/basket/index.js` (`checkoutBasket` function), `lib/eventbus.ts`, `lib/queue.ts`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Lambda functions use default concurrent execution limits (1,000 per region). DynamoDB tables use `BillingMode.PAY_PER_REQUEST` which auto-scales but at unbounded cost. No load test configurations or results found. No auto-scaling policies beyond DynamoDB on-demand. SQS queue has default settings with `visibilityTimeout: Duration.seconds(30)`.
- **Gap**: Infrastructure capacity is untested for agent traffic patterns. Lambda default concurrency may be insufficient for traffic spikes. DynamoDB on-demand scaling could incur unexpected costs.
- **Compensating Controls**:
  - DynamoDB PAY_PER_REQUEST provides automatic scaling for read/write capacity.
  - Lambda scales automatically up to the account concurrency limit.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Conduct load testing with agent-like traffic patterns (burst reads, rapid sequential queries). Set reserved concurrency on Lambda functions. Consider provisioned concurrency for latency-sensitive agent operations. Add cost alerting for DynamoDB.
- **Evidence**: `lib/database.ts` (PAY_PER_REQUEST billing), `lib/microservice.ts` (no reserved concurrency), `lib/queue.ts` (default queue settings)

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No separate environment configurations found. `bin/aws-microservices.ts` defines a single `AwsMicroservicesStack` with no environment specification. No staging or sandbox CDK stacks. No docker-compose for local testing. No seed data scripts. No synthetic data generators. No `cdk.json` context for multiple environments.
- **Gap**: No sandbox or staging environment. Agents can only be tested against production.
- **Compensating Controls**:
  - Deploy a second CDK stack with a different stack name (e.g., `AwsMicroservicesStack-staging`) using a separate AWS account or region.
  - Use DynamoDB local for development-time testing.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Parameterize the CDK stack with environment context (staging/production). Deploy a staging stack. Create seed data scripts for realistic test scenarios.
- **Evidence**: `bin/aws-microservices.ts` (single stack, env commented out), `lib/aws-microservices-stack.ts`

#### DATA-Q3: Selective Query Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: `GET /product` uses `ScanCommand` returning ALL products with no pagination. `GET /basket` uses `ScanCommand` returning ALL baskets. `GET /order` uses `ScanCommand` returning ALL orders. Only `GET /order/{userName}?orderDate=timestamp` uses `QueryCommand` with key conditions. No `limit`, `offset`, `cursor`, or pagination parameters on any list endpoint. No result size limits.
- **Gap**: Unbounded result sets on list endpoints. An agent querying products, baskets, or orders receives everything — exhausting LLM context windows and increasing token cost.
- **Compensating Controls**:
  - Agent tool definitions can specify result size expectations in prompts.
  - Use specific GET endpoints (e.g., `GET /product/{id}`) rather than list endpoints where possible.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add pagination support to all ScanCommand-based endpoints using DynamoDB `Limit` and `ExclusiveStartKey`. Return pagination tokens in response bodies. Add `limit` query parameter support.
- **Evidence**: `src/product/index.js` (`getAllProducts` with ScanCommand), `src/basket/index.js` (`getAllBaskets`), `src/ordering/index.js` (`getAllOrders`)

#### DATA-Q4: System of Record Designations — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No master data management documentation. No system-of-record designations. No data ownership definitions. DynamoDB tables serve as de facto authoritative sources for their domains (product catalog, shopping baskets, orders), but this is not formally documented.
- **Gap**: No formal system-of-record designations. An agent cannot determine which data source is authoritative for a given entity.
- **Compensating Controls**:
  - Document in agent tool descriptions that each microservice is the SoR for its domain.
  - Include data source attribution in agent responses.
- **Remediation Timeline**: 7–14 days
- **Recommendation**: Document system-of-record designations in a `DATA_GOVERNANCE.md` file. Each DynamoDB table is the SoR for its domain: product table for catalog, basket table for cart state, order table for order history.
- **Evidence**: `lib/database.ts` (three DynamoDB tables with no ownership metadata), `README.md` (no data governance documentation)

#### DATA-Q5: Temporal Metadata and Freshness — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Only the order table has timestamps: `orderDate` is set to `new Date().toISOString()` in `src/ordering/index.js`. The product table has no `created_at` or `updated_at` fields. The basket table has no temporal metadata. No `Cache-Control` headers in any API response. No `X-Data-Age` or `last_refreshed` headers. No data freshness signaling.
- **Gap**: Incomplete temporal metadata. Products and baskets have no timestamps. An agent cannot reason about data freshness for 2 out of 3 services.
- **Compensating Controls**:
  - DynamoDB is strongly consistent for reads after writes (default for GetItem). Agent can assume data is current for direct reads.
  - Add `Cache-Control: no-cache` headers to API Gateway responses to indicate fresh data.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add `created_at` and `updated_at` fields to all DynamoDB items. Set them in create and update operations in all Lambda handlers. Return `Last-Modified` headers in API responses.
- **Evidence**: `src/ordering/index.js` (orderDate set), `src/product/index.js` (no timestamps), `src/basket/index.js` (no timestamps)

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No schema files (JSON Schema, Avro, Protobuf). No API versioning (`/v1/`, `/v2/` patterns) — routes are `/product`, `/basket`, `/order` with no version prefix. No `Accept-Version` headers. No changelog files. No breaking change detection tools. No consumer-driven contract tests. No database migration files. API Gateway routes have no versioning.
- **Gap**: No schema versioning or API contracts. Agent tool bindings can break silently when API changes are deployed.
- **Compensating Controls**:
  - Pin agent tool definitions to known API behavior and re-validate after each deployment.
  - Export and diff API Gateway specs before/after deployments.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add API versioning (e.g., `/v1/product`). Implement OpenAPI spec generation and commit to repo. Add breaking change detection in CI (when CI is established per ENG-Q2).
- **Evidence**: `lib/apigateway.ts` (no versioning in routes), no schema files found in repository

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No X-Ray tracing configuration in CDK (no `tracing: lambda.Tracing.ACTIVE` in `lib/microservice.ts`). No OpenTelemetry SDK in any `package.json`. No `traceparent` header propagation. Logging is `console.log` / `console.error` — unstructured plaintext with no JSON formatting, no correlation IDs, no `request_id` fields. Lambda auto-generates request IDs in the context but handlers don't extract or propagate them.
- **Gap**: No distributed tracing. Unstructured logging. Cannot trace an agent-initiated request across the basket→EventBridge→SQS→ordering flow.
- **Compensating Controls**:
  - CloudWatch Logs Insights can query across log groups with keyword search.
  - API Gateway access logs (if enabled) provide basic request tracing.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Enable X-Ray tracing on all Lambda functions in CDK (`tracing: Tracing.ACTIVE`). Switch from `console.log` to a structured JSON logger (e.g., `@aws-lambda-powertools/logger`). Propagate correlation IDs through EventBridge and SQS message attributes.
- **Evidence**: `lib/microservice.ts` (no tracing configuration), `src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js` (console.log logging), `src/product/package.json` (no logging libraries)

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No CloudWatch alarms defined anywhere in CDK IaC. No anomaly detection configuration. No PagerDuty/OpsGenie integration. No SLO-based alerting. No composite alarms. The only monitoring available is default CloudWatch metrics for Lambda (invocations, errors, duration) and API Gateway (4xx, 5xx, latency) — but no alarms are configured on them.
- **Gap**: No alerting on error rates or latency. Target system degradation affecting agents will not be detected until agents fail.
- **Compensating Controls**:
  - Manually create CloudWatch alarms via AWS Console for Lambda error rates and API Gateway 5xx rates.
  - Use CloudWatch automatic dashboards for visual monitoring.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add CloudWatch alarms in CDK for Lambda error rate > 1%, API Gateway 5xx rate > 1%, and P99 latency > 3 seconds. Integrate with SNS for notifications. Consider CloudWatch anomaly detection for adaptive thresholds.
- **Evidence**: `lib/aws-microservices-stack.ts` (no alarm resources), `lib/microservice.ts` (no alarm configuration)

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: CDK IaC in the `lib/` directory defines all infrastructure (API Gateway, Lambda, DynamoDB, EventBridge, SQS) — sub-check 1 (IaC defined) PASSES. No CODEOWNERS file, no branch protection configuration, no PR review requirements visible in the repo — sub-check 2 (peer review) FAILS. No AWS Config rules, no drift detection configuration in CDK — sub-check 3 (drift detection) FAILS. 1 of 3 sub-checks pass.
- **Gap**: Infrastructure is defined as code but has no peer review enforcement or drift detection.
- **Compensating Controls**:
  - CDK provides `cdk diff` to compare deployed vs. desired state manually.
  - Use AWS CloudFormation drift detection manually via Console.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add CODEOWNERS file requiring review for `lib/` directory changes. Enable branch protection on the main branch. Add AWS Config rules for drift detection on API Gateway and IAM resources.
- **Evidence**: `lib/` directory (CDK IaC files), no CODEOWNERS file, no AWS Config in CDK

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No CI/CD configuration files found: no `.github/workflows/`, no `.gitlab-ci.yml`, no `Jenkinsfile`, no `buildspec.yml`, no CodePipeline definition in CDK. Deployment is manual via `cdk deploy` per `README.md`. No contract tests. No schema validation in any pipeline.
- **Gap**: No CI/CD pipeline. API-breaking changes cannot be caught before production deployment.
- **Compensating Controls**:
  - Manual `cdk diff` before deployment provides some change visibility.
  - Manual testing before deployment.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement GitHub Actions or CodePipeline with stages: lint → test → cdk diff → approval → cdk deploy. Add API contract tests using Pact or OpenAPI spec validation.
- **Evidence**: No CI/CD files found in repository. `README.md` (deployment instructions: `cdk deploy`)

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No deployment configuration beyond `cdk deploy`. No blue/green deployment. No canary deployment. No CodeDeploy integration. No rollback triggers. No feature flags. No traffic shifting at API Gateway or Lambda level. `cdk deploy` overwrites CloudFormation stacks in-place. Rollback requires manually running `cdk deploy` with a previous version of the code.
- **Gap**: No automated rollback capability. A broken deployment affecting agent-facing APIs requires manual intervention.
- **Compensating Controls**:
  - CloudFormation automatically rolls back stack updates on failure.
  - Git revert + `cdk deploy` provides manual rollback path.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement Lambda versioning with aliases and CodeDeploy traffic shifting. Add canary deployments with automatic rollback on error rate thresholds. Consider API Gateway stage-based deployments.
- **Evidence**: `README.md` (manual cdk deploy), no CodeDeploy or deployment config in CDK

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: `test/aws-microservices.test.ts` exists but is **entirely commented out**. The only test (`'SQS Queue Created'`) has all assertions commented. `jest.config.js` is configured but there are no active tests. No API tests, no contract tests, no integration tests, no unit tests for Lambda handlers. Zero test coverage.
- **Gap**: No test coverage. API behavior changes affecting agents will not be caught before deployment.
- **Compensating Controls**:
  - Manual testing of API endpoints before deployment.
  - Post-deployment smoke tests (manual).
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Uncomment and update the CDK infrastructure test. Add Lambda handler unit tests for all three services. Add API integration tests using a test stack. Add contract tests for the EventBridge event schema.
- **Evidence**: `test/aws-microservices.test.ts` (all tests commented out), `jest.config.js` (configured but unused)

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: DynamoDB tables in `lib/database.ts` have no explicit encryption configuration — no `encryption` property, no `encryptionKey` with KMS. DynamoDB encrypts at rest by default with AWS-owned keys (no additional configuration needed). However, the order table contains PII and payment card information (`cardInfo`) which warrants customer-managed KMS keys for regulatory compliance and key rotation control.
- **Gap**: Default encryption only (AWS-owned keys). No customer-managed KMS keys for tables containing PII and payment data.
- **Compensating Controls**:
  - AWS-owned key encryption meets baseline encryption-at-rest requirements.
  - DynamoDB default encryption is always enabled and cannot be disabled.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add customer-managed KMS keys for the order table (and optionally basket table) in `lib/database.ts` using CDK's `encryption: TableEncryption.CUSTOMER_MANAGED` with a KMS key. This provides key rotation control and audit trail via CloudTrail.
- **Evidence**: `lib/database.ts` (no encryption property on Table constructs)

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO (no issue — PASS)
- **Finding**: `lib/apigateway.ts` defines REST API endpoints via three `LambdaRestApi` instances. Product Service: `GET/POST /product`, `GET/PUT/DELETE /product/{id}`. Basket Service: `GET/POST /basket`, `GET/DELETE /basket/{userName}`, `POST /basket/checkout`. Order Service: `GET /order`, `GET /order/{userName}`. All routes are backed by Lambda functions with API Gateway proxy integration disabled (`proxy: false`). Integration is via documented REST API, not direct database access.
- **Implication**: The REST API surface is well-suited for agent tool binding. Three separate APIs provide natural tool boundaries per domain.
- **Recommendation**: No action needed. API surface is suitable for agent integration.
- **Evidence**: `lib/apigateway.ts`, `src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js`

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: `POST /product` generates a `uuidv4()` for each new product and uses `PutItemCommand` (overwrites on duplicate key). `POST /basket` uses `PutItemCommand` with `userName` as key — idempotent by nature since the same userName overwrites the same basket. `POST /basket/checkout` has no idempotency key and could trigger duplicate orders on retry. No idempotency middleware or decorators exist.
- **Implication**: When agent scope expands to write-enabled, the lack of idempotency on checkout will become a BLOCKER. Plan for idempotency key support on write endpoints before scope expansion.
- **Recommendation**: Pre-plan idempotency key middleware for write endpoints, prioritizing the checkout flow.
- **Evidence**: `src/product/index.js` (`createProduct` with uuid), `src/basket/index.js` (`checkoutBasket` — no idempotency key)

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: All Lambda handlers return JSON via `JSON.stringify()`. Response format is consistent: `{ message: string, body: <data> }`. API Gateway defaults `Content-Type` to `application/json`. No binary, XML, or protobuf responses.
- **Implication**: JSON responses are well-suited for agent consumption. LLMs can parse the response structure directly. The `body` wrapper adds a layer of nesting that agent tools should account for.
- **Recommendation**: Consider flattening the response structure (remove `message` wrapper for GET responses) to simplify agent parsing.
- **Evidence**: `src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js` (return statements)

### API-Q7: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: EventBridge integration exists via `lib/eventbus.ts`. The `com.swn.basket.checkoutbasket` source emits `CheckoutBasket` events when a basket checkout occurs. These events route via SQS to the ordering service. However, no events are emitted for product CRUD operations (create, update, delete) or direct order queries. Event emission is limited to the checkout flow only.
- **Implication**: For an agent needing to react to state changes (e.g., new order created, product price changed), only checkout completion is observable via events. Product catalog changes and order status updates are not event-driven.
- **Recommendation**: Consider adding EventBridge events for product CRUD operations and order status changes if reactive agent behavior is planned.
- **Evidence**: `lib/eventbus.ts` (CheckoutBasketRule), `src/basket/index.js` (`publishCheckoutBasketEvent`)

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limiting configuration found in CDK IaC. No API Gateway usage plans or throttle settings in `lib/apigateway.ts`. No WAF rate-based rules. No `X-RateLimit-Remaining` or `Retry-After` headers in Lambda responses. API Gateway applies default account-level throttling (10,000 RPS) but this is not documented or surfaced to consumers.
- **Implication**: Agents calling these APIs have no way to self-throttle. Undocumented limits cause unpredictable failures when agent traffic approaches account-level limits.
- **Recommendation**: When rate limiting is implemented (per STATE-Q5), include `X-RateLimit-Remaining` and `Retry-After` headers in API responses. Document rate limits in API specifications.
- **Evidence**: `lib/apigateway.ts` (no usage plans), Lambda handlers (no rate limit headers in responses)

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: INFO
- **Finding**: No JWT parsing, no OAuth token exchange, no user context headers (`X-User-Id`, `Authorization Bearer`) in any Lambda handler. No identity propagation between services in the basket→EventBridge→SQS→ordering flow. The ordering service processes events with no knowledge of which caller initiated the checkout. No distinction between agent-as-self and agent-on-behalf-of-user.
- **Implication**: When identity is established (AUTH-Q1), the system will need to propagate caller context through the event-driven flow. EventBridge event detail and SQS message attributes can carry identity context.
- **Recommendation**: Plan identity propagation architecture: include caller identity in EventBridge event detail, propagate through SQS message attributes, and log in ordering service.
- **Evidence**: `src/basket/index.js` (no identity context in checkout flow), `src/ordering/index.js` (no identity extraction from events)

### AUTH-Q5: Credential Management

- **Severity**: INFO
- **Finding**: No hardcoded credentials found in any source file. AWS SDK clients (`DynamoDBClient`, `EventBridgeClient`) use Lambda execution role credentials (implicit via the runtime environment). Environment variables contain only configuration values: `DYNAMODB_TABLE_NAME`, `PRIMARY_KEY`, `EVENT_SOURCE`, `EVENT_DETAILTYPE`, `EVENT_BUSNAME` — no secrets. No `.env` files committed. No Secrets Manager or Vault integration needed for current architecture.
- **Implication**: Current credential management is sound for the serverless architecture. Lambda execution roles provide automatic credential rotation.
- **Recommendation**: No action needed. If external service integrations are added in the future, use AWS Secrets Manager for non-IAM credentials.
- **Evidence**: `src/product/ddbClient.js`, `src/basket/ddbClient.js`, `src/basket/eventBridgeClient.js`, `lib/microservice.ts` (environment variables)

### STATE-Q2: Queryable Current State

- **Severity**: INFO (no issue — PASS)
- **Finding**: All three services expose current DynamoDB state via GET endpoints. `GET /product` and `GET /product/{id}` return product state. `GET /basket/{userName}` returns basket state. `GET /order/{userName}?orderDate=timestamp` and `GET /order` return order state. All endpoints read directly from DynamoDB with strong consistency (default for GetItem).
- **Implication**: An agent can inspect current state before deciding next steps. This supports the agent use case of order status lookups directly.
- **Recommendation**: No action needed. State is queryable via well-defined endpoints.
- **Evidence**: `src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js` (GET handlers)

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No optimistic locking (no version fields, no ETags, no `If-Match` headers). `PutItemCommand` overwrites existing items without conditions. `UpdateItemCommand` in product service has no conditional expressions. No pessimistic locking (`SELECT FOR UPDATE` equivalent). No DynamoDB conditional writes.
- **Implication**: When agent scope expands to write-enabled, concurrent writes will be a risk. Plan for optimistic locking with version fields and DynamoDB conditional expressions.
- **Recommendation**: Pre-plan concurrency controls: add `version` fields to DynamoDB items and use `ConditionExpression` in write operations.
- **Evidence**: `src/product/index.js` (PutItemCommand, UpdateItemCommand without conditions), `src/basket/index.js` (PutItemCommand without conditions)

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits per agent identity. No maximum records modified per run. No maximum spend per hour. No maximum delete operations per session. No blast radius controls exist at any layer.
- **Implication**: When agent scope expands to write-enabled, transaction limits will be critical. Without them, an agent error could delete all products or trigger unlimited checkouts.
- **Recommendation**: Pre-plan transaction limits: add configurable per-agent limits in API Gateway usage plans and application-layer middleware.
- **Evidence**: `lib/apigateway.ts` (no usage plans), Lambda handlers (no transaction limit logic)

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No draft or pending status fields in any DynamoDB table schema. Product table has no status field — products are either present or absent. Basket is either active (exists in table) or deleted. Order table has no approval or pending state — orders are created directly from checkout events. No two-step commit patterns.
- **Implication**: When agent scope expands to write-enabled, draft states will enable safer agent-initiated writes. Without them, all writes are immediately committed.
- **Recommendation**: Pre-plan draft states for the order creation flow (pending → confirmed) when write scope is introduced.
- **Evidence**: `lib/database.ts` (table schemas), `src/ordering/index.js` (direct order creation)

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No approval workflow endpoints. No confirmation steps. The checkout flow goes directly from basket to EventBridge to order creation with no human approval gate. No Step Functions with `waitForTaskToken`. No configurable operation-level approval flags.
- **Implication**: When agent scope expands to write-enabled, approval gates on high-risk operations (checkout, bulk delete) will provide defense in depth.
- **Recommendation**: Consider Step Functions with human approval tasks for the checkout flow when write scope is introduced.
- **Evidence**: `src/basket/index.js` (direct checkout flow), `lib/eventbus.ts` (no approval gate)

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality dashboards, data profiling reports, null rate monitoring, duplicate detection logic, data freshness SLAs, or data quality metrics in observability. No data validation beyond basic null checks (e.g., `checkoutRequest.userName == null` in basket checkout).
- **Implication**: An agent reasoning on this data cannot assess its quality. For the order status lookup use case, stale or incomplete data would propagate to agent responses without any quality signal.
- **Recommendation**: Add basic data quality metrics: null rate per field, duplicate detection for orders, freshness SLA for product catalog. Publish as CloudWatch custom metrics.
- **Evidence**: `src/basket/index.js` (minimal validation), `src/product/index.js` (no validation), `src/ordering/index.js` (no validation)

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: DynamoDB field names are human-readable and semantically meaningful: `id`, `userName`, `orderDate`, `totalPrice`, `firstName`, `lastName`, `email`, `address`, `paymentMethod`, `cardInfo`, `category`, `price`, `productId`, `productName`, `quantity`, `color`. No legacy abbreviations or codes. API response fields mirror DynamoDB field names.
- **Implication**: Field names are well-suited for LLM-based reasoning. No data dictionary is needed for agent tool descriptions.
- **Recommendation**: No action needed. Maintain the current naming conventions.
- **Evidence**: `lib/database.ts` (schema comments), `src/basket/index.js` (`prepareOrderPayload` field names)

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No Glue Data Catalog, no Collibra/Alation/DataHub. No metadata files or data dictionaries. Schema documentation exists only in code comments in `lib/database.ts` (e.g., `product : PK: id -- name - description - imageFile - price - category`).
- **Implication**: Agent tool builders must read CDK code to understand data schemas. A lightweight data dictionary would accelerate tool definition.
- **Recommendation**: Create a `SCHEMA.md` file documenting each table's fields, types, and relationships. This serves as a lightweight data catalog for agent tool builders.
- **Evidence**: `lib/database.ts` (inline schema comments), no data catalog files found

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No custom CloudWatch metrics. No `putMetricData` calls in any Lambda handler. No business outcome dashboards (order completion rate, checkout success rate, product catalog metrics). Only default Lambda/API Gateway metrics (invocations, errors, duration, 4xx/5xx rates) are available.
- **Implication**: When agents consume these services, business metrics become the primary signal for whether agent interactions produce good outcomes. Without them, you can only monitor technical health, not business impact.
- **Recommendation**: Add custom CloudWatch metrics for key business events: orders created per hour, checkout success/failure rate, product lookup hit rate. These become agent effectiveness KPIs.
- **Evidence**: `src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js` (no custom metric calls)

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO (no issue — PASS)
- **Finding**: `lib/apigateway.ts` defines REST API endpoints via three `LambdaRestApi` instances: Product Service (`GET/POST /product`, `GET/PUT/DELETE /product/{id}`), Basket Service (`GET/POST /basket`, `GET/DELETE /basket/{userName}`, `POST /basket/checkout`), Order Service (`GET /order`, `GET /order/{userName}`). Integration is via API Gateway REST APIs, not direct database access or UI automation.
- **Gap**: No gap. REST API interface exists and is well-structured.
- **Recommendation**: No action needed.
- **Evidence**: `lib/apigateway.ts`, `src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, GraphQL, or Smithy specification files found in the repository. API structure is defined only in CDK code (`lib/apigateway.ts`) and Lambda handler switch statements.
- **Gap**: No machine-readable API specification exists. Agent tool definitions must be manually authored.
- **Recommendation**: Generate an OpenAPI specification from the deployed API Gateway stages. Commit to the repository.
- **Evidence**: No spec files found. `lib/apigateway.ts` (routes defined only in CDK code)

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: All three Lambda handlers return `{ statusCode: 500, body: JSON.stringify({ message, errorMsg, errorStack }) }` on error. No structured error codes, no retryable boolean, no error categorization. Error stacks (`e.stack`) leaked in production responses.
- **Gap**: Agents cannot distinguish retriable from terminal errors. Error stacks exposed in production.
- **Recommendation**: Implement structured error codes, error categories (retriable/terminal), remove error stacks from production.
- **Evidence**: `src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js` (catch blocks)

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: `POST /product` uses `uuidv4()` for ID with `PutItemCommand`. `POST /basket` uses `PutItemCommand` with `userName` key (idempotent by nature). `POST /basket/checkout` has no idempotency key. No idempotency middleware.
- **Gap**: Checkout endpoint lacks idempotency. Informational for read-only scope.
- **Recommendation**: Pre-plan idempotency key support for write endpoints before scope expansion.
- **Evidence**: `src/product/index.js`, `src/basket/index.js` (`checkoutBasket`)

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: All handlers return JSON via `JSON.stringify()`. Consistent format: `{ message: string, body: <data> }`. API Gateway defaults `Content-Type` to `application/json`.
- **Gap**: No gap. JSON format is agent-friendly.
- **Recommendation**: Consider flattening response structure for simpler agent parsing.
- **Evidence**: `src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js`

#### API-Q6: Asynchronous Operation Support
- **Severity**: RISK-QUALITY
- **Finding**: Checkout flow is async (basket→EventBridge→SQS→ordering). `POST /basket/checkout` returns immediately with no job ID, no polling endpoint, no webhook callback. Agent cannot track checkout completion.
- **Gap**: Async flow exists but no tracking mechanism for agents.
- **Recommendation**: Return correlation ID from checkout. Add status polling endpoint.
- **Evidence**: `src/basket/index.js` (`checkoutBasket`), `lib/eventbus.ts`, `lib/queue.ts`

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: EventBridge emits `CheckoutBasket` events via `com.swn.basket.checkoutbasket` source. Only checkout triggers events — no events for product CRUD or order creation.
- **Gap**: Partial event emission. Only checkout flow is event-driven.
- **Recommendation**: Add events for product CRUD and order status changes if reactive agent behavior is needed.
- **Evidence**: `lib/eventbus.ts`, `src/basket/index.js` (`publishCheckoutBasketEvent`)

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limiting configuration in CDK IaC. No usage plans, no throttle settings, no WAF rules. No `X-RateLimit-Remaining` headers. Default account-level API Gateway throttling (10,000 RPS) is undocumented.
- **Gap**: No documented rate limits. Agents cannot self-throttle.
- **Recommendation**: Document and implement rate limits. Add rate limit headers to responses.
- **Evidence**: `lib/apigateway.ts` (no usage plans)

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: `lib/apigateway.ts` creates three `LambdaRestApi` instances with NO authorizer. No Cognito, no API keys, no IAM auth, no Lambda authorizer. All endpoints are completely open.
- **Gap**: No authentication mechanism. Cannot identify agent callers.
- **Recommendation**: Add API key authentication with usage plans. Long-term, implement OAuth2 client credentials via Cognito.
- **Evidence**: `lib/apigateway.ts` (no authorizer configuration)

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: `lib/microservice.ts` grants `grantReadWriteData()` on respective DynamoDB tables. No API-level authorization. No agent-specific scoped permissions possible without an auth layer.
- **Gap**: No mechanism for least-privilege agent access.
- **Recommendation**: After AUTH-Q1, create usage plans with method-level throttling. Implement IAM authorization or Cognito scopes.
- **Evidence**: `lib/microservice.ts` (`grantReadWriteData` calls), `lib/apigateway.ts`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: No authorization middleware in any Lambda handler. HTTP methods routed by switch statement with no permission checks. `DELETE /product/{id}` is as accessible as `GET /product`.
- **Gap**: No action-level authorization. Cannot enforce read-only access.
- **Recommendation**: Add authorization middleware. Deploy separate read-only API Gateway stage for agents.
- **Evidence**: `src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js` (no auth checks)

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: No JWT parsing, no OAuth token exchange, no user context headers. No identity propagation in basket→EventBridge→SQS→ordering flow. No distinction between agent-as-self and agent-on-behalf-of-user.
- **Gap**: No identity propagation. Ordering service cannot identify checkout initiator.
- **Recommendation**: Plan identity propagation via EventBridge event detail and SQS message attributes.
- **Evidence**: `src/basket/index.js`, `src/ordering/index.js` (no identity context)

#### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: No hardcoded credentials. AWS SDK clients use Lambda execution role credentials. Environment variables contain only configuration values (table names, event source). No `.env` files committed. No external secrets needed.
- **Gap**: No gap for current architecture.
- **Recommendation**: No action needed. Use Secrets Manager for future external integrations.
- **Evidence**: `src/product/ddbClient.js`, `src/basket/ddbClient.js`, `src/basket/eventBridgeClient.js`, `lib/microservice.ts`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No CloudTrail in CDK IaC. No CloudWatch log retention policies. Lambda uses `console.log`/`console.error` — unstructured, no principal attribution. No log immutability configuration.
- **Gap**: No immutable audit trail. Cannot prove which caller performed which action.
- **Recommendation**: Add CloudTrail with log file validation. Set CloudWatch log retention. Add structured JSON logging.
- **Evidence**: `lib/microservice.ts`, `lib/aws-microservices-stack.ts` (no CloudTrail or log config)

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: No API key management, no Cognito user pool, no service accounts. No identity mechanism exists to suspend. Only option is take down entire API Gateway.
- **Gap**: Cannot suspend individual agent identity.
- **Recommendation**: After AUTH-Q1, implement API key-based identity with immediate revocation capability.
- **Evidence**: `lib/apigateway.ts`, `lib/aws-microservices-stack.ts`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Checkout flow in `src/basket/index.js`: (1) get basket, (2) prepare payload, (3) publish to EventBridge, (4) delete basket. No saga pattern, no compensating transactions, no undo endpoints. Partial failures leave inconsistent state.
- **Gap**: No compensation or rollback for multi-step checkout operation.
- **Recommendation**: Implement Step Functions workflow or saga pattern for checkout flow.
- **Evidence**: `src/basket/index.js` (`checkoutBasket`), `lib/queue.ts` (no DLQ)

#### STATE-Q2: Queryable Current State
- **Severity**: INFO (no issue — PASS)
- **Finding**: All services expose current DynamoDB state via GET endpoints. `GET /product`, `GET /product/{id}`, `GET /basket/{userName}`, `GET /order/{userName}?orderDate=timestamp`, `GET /order` all return current state.
- **Gap**: No gap. State is queryable.
- **Recommendation**: No action needed.
- **Evidence**: `src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js` (GET handlers)

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No optimistic locking, no ETags, no `If-Match` headers. `PutItemCommand` overwrites without conditions. `UpdateItemCommand` has no conditional expressions. No DynamoDB conditional writes.
- **Gap**: No concurrency controls. Informational for read-only scope.
- **Recommendation**: Pre-plan version fields and `ConditionExpression` for write operations.
- **Evidence**: `src/product/index.js`, `src/basket/index.js` (unconditional writes)

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: All AWS SDK clients created with default configuration — no custom timeouts, no retry configuration, no circuit breaker logic. No resilience libraries in dependencies. No exponential backoff patterns.
- **Gap**: No circuit breakers or resilience patterns. DynamoDB/EventBridge outages cascade to agents.
- **Recommendation**: Configure SDK client timeouts and retry strategies. Add resilience middleware.
- **Evidence**: `src/product/ddbClient.js`, `src/basket/ddbClient.js`, `src/basket/eventBridgeClient.js`, `src/ordering/ddbClient.js`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No API Gateway throttling in `lib/apigateway.ts`. No usage plans. No WAF rules. No application-level rate limiting. Default account-level throttling (10,000 RPS) is the only protection.
- **Gap**: No rate limiting. Runaway agent loops could overwhelm services.
- **Recommendation**: Add API Gateway usage plans with per-key throttle limits. Add WAF rate-based rules.
- **Evidence**: `lib/apigateway.ts` (no throttle configuration)

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits per agent identity. No max records, no max spend, no max deletes.
- **Gap**: No blast radius controls. Informational for read-only scope.
- **Recommendation**: Pre-plan transaction limits for write scope expansion.
- **Evidence**: `lib/apigateway.ts`, Lambda handlers (no limit logic)

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: RISK-QUALITY
- **Finding**: Lambda uses default concurrency (1,000/region). DynamoDB uses `PAY_PER_REQUEST` (auto-scaling at unbounded cost). No load tests found. SQS queue has default settings.
- **Gap**: Untested capacity for agent traffic patterns.
- **Recommendation**: Load test with agent traffic patterns. Set reserved/provisioned concurrency. Add cost alerting.
- **Evidence**: `lib/database.ts` (PAY_PER_REQUEST), `lib/microservice.ts` (no concurrency config), `lib/queue.ts`

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No draft/pending status fields in any DynamoDB schema. Products exist or don't. Baskets are active or deleted. Orders are created directly with no pending state.
- **Gap**: No draft states. Informational for read-only scope.
- **Recommendation**: Pre-plan draft states for order creation when write scope is introduced.
- **Evidence**: `lib/database.ts`, `src/ordering/index.js`

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No approval workflows. Checkout goes directly to EventBridge/SQS with no human gate. No Step Functions with `waitForTaskToken`.
- **Gap**: No approval gates. Informational for read-only scope.
- **Recommendation**: Consider Step Functions approval tasks for write scope expansion.
- **Evidence**: `src/basket/index.js`, `lib/eventbus.ts`

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: Single `AwsMicroservicesStack` with no environment specification. No staging/sandbox stacks. No docker-compose. No seed data scripts.
- **Gap**: No sandbox or staging environment for agent testing.
- **Recommendation**: Parameterize CDK stack for multiple environments. Deploy staging stack.
- **Evidence**: `bin/aws-microservices.ts` (single stack), `lib/aws-microservices-stack.ts`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: Order table stores PII: `firstName`, `lastName`, `email`, `address`, `paymentMethod`, `cardInfo`. No classification tags on DynamoDB tables. No field-level encryption. No Macie integration. No access controls per field.
- **Gap**: Unclassified sensitive data including PII and payment card info.
- **Recommendation**: Tag tables with classification levels. Implement field-level encryption for sensitive fields with KMS.
- **Evidence**: `lib/database.ts` (order table schema), `src/basket/index.js` (`prepareOrderPayload`), `src/ordering/index.js` (`createOrder`)

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: `bin/aws-microservices.ts` has `env` commented out. Stack is environment-agnostic. No data residency documentation. No GDPR/LGPD references. Region determined at deploy-time with no guardrails.
- **Gap**: No data residency configuration. PII could be deployed in any region.
- **Recommendation**: Set `env` property in CDK. Document approved deployment regions. Add SCPs for region restriction.
- **Evidence**: `bin/aws-microservices.ts` (commented-out env), `lib/database.ts`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK-QUALITY
- **Finding**: `GET /product`, `GET /basket`, `GET /order` all use `ScanCommand` returning ALL records. No pagination, filtering, or result size limits. Only `GET /order/{userName}?orderDate=timestamp` uses `QueryCommand`.
- **Gap**: Unbounded result sets on list endpoints.
- **Recommendation**: Add pagination with DynamoDB `Limit` and `ExclusiveStartKey`. Add `limit` query parameter.
- **Evidence**: `src/product/index.js` (`getAllProducts`), `src/basket/index.js` (`getAllBaskets`), `src/ordering/index.js` (`getAllOrders`)

#### DATA-Q4: System of Record Designations
- **Severity**: RISK-QUALITY
- **Finding**: No formal system-of-record designations or data ownership documentation. DynamoDB tables serve as de facto SoRs.
- **Gap**: No formal SoR designations.
- **Recommendation**: Document SoR designations in `DATA_GOVERNANCE.md`.
- **Evidence**: `lib/database.ts`, `README.md`

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK-QUALITY
- **Finding**: Order table has `orderDate` (set to `new Date().toISOString()`). Product and basket tables have no `created_at` or `updated_at` fields. No `Cache-Control` or freshness headers.
- **Gap**: Incomplete temporal metadata. 2 of 3 services lack timestamps.
- **Recommendation**: Add `created_at` and `updated_at` to all DynamoDB items. Add `Last-Modified` headers.
- **Evidence**: `src/ordering/index.js` (orderDate), `src/product/index.js` (no timestamps), `src/basket/index.js` (no timestamps)

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: All handlers log full request events with `console.log("request:", JSON.stringify(event, undefined, 2))`. `src/basket/index.js` logs `checkoutPayload` with PII (firstName, lastName, email, address, paymentMethod, cardInfo). `src/ordering/index.js` logs `basketCheckoutEvent` with same PII. No log scrubbing or PII masking.
- **Gap**: PII logged in plaintext to CloudWatch.
- **Recommendation**: Add log scrubbing middleware. Remove full payload logging. Use structured JSON with field allowlists.
- **Evidence**: `src/basket/index.js`, `src/ordering/index.js`, `src/product/index.js` (console.log statements)

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality dashboards, profiling, null rate monitoring, duplicate detection, or freshness SLAs. Minimal validation (null check on `userName` in checkout).
- **Gap**: No data quality metrics or monitoring.
- **Recommendation**: Add basic data quality metrics as CloudWatch custom metrics.
- **Evidence**: `src/basket/index.js` (minimal validation), `src/product/index.js`, `src/ordering/index.js`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: No schema files. No API versioning (`/v1/` patterns). No `Accept-Version` headers. No changelogs. No breaking change detection. No contract tests. No database migrations.
- **Gap**: No schema versioning or API contracts. Agent tool bindings break silently on API changes.
- **Recommendation**: Add API versioning. Generate and commit OpenAPI specs. Add breaking change detection in CI.
- **Evidence**: `lib/apigateway.ts` (no versioning), no schema files in repository

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Field names are human-readable: `id`, `userName`, `orderDate`, `totalPrice`, `firstName`, `lastName`, `email`, `address`, `paymentMethod`, `cardInfo`, `category`, `price`, `productId`, `productName`, `quantity`, `color`. No legacy codes.
- **Gap**: No gap. Names are semantically meaningful.
- **Recommendation**: Maintain current naming conventions.
- **Evidence**: `lib/database.ts`, `src/basket/index.js`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No Glue Data Catalog, no external metadata tools. Schema documented only in `lib/database.ts` code comments.
- **Gap**: No data catalog. Schema exists only in CDK code.
- **Recommendation**: Create `SCHEMA.md` documenting table fields, types, and relationships.
- **Evidence**: `lib/database.ts` (inline comments)

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: No X-Ray tracing in CDK. No OpenTelemetry in dependencies. No `traceparent` header propagation. Logging is unstructured `console.log`/`console.error`. No correlation IDs.
- **Gap**: No distributed tracing. Unstructured logging. Cannot trace agent requests across services.
- **Recommendation**: Enable X-Ray tracing (`tracing: Tracing.ACTIVE`). Switch to `@aws-lambda-powertools/logger`. Propagate correlation IDs.
- **Evidence**: `lib/microservice.ts`, `src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: No CloudWatch alarms in CDK. No anomaly detection. No PagerDuty/OpsGenie. No SLO alerting.
- **Gap**: No alerting. System degradation affecting agents goes undetected.
- **Recommendation**: Add CloudWatch alarms for Lambda error rates, API Gateway 5xx rates, P99 latency.
- **Evidence**: `lib/aws-microservices-stack.ts`, `lib/microservice.ts`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom CloudWatch metrics. No `putMetricData` calls. No business outcome dashboards. Only default Lambda/API Gateway metrics.
- **Gap**: No business outcome metrics for agent effectiveness monitoring.
- **Recommendation**: Add custom metrics for orders/hour, checkout success rate, product lookup hit rate.
- **Evidence**: `src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK-QUALITY
- **Finding**: CDK IaC defines all infrastructure (PASS sub-check 1). No CODEOWNERS or branch protection (FAIL sub-check 2). No AWS Config drift detection (FAIL sub-check 3). 1 of 3 sub-checks pass.
- **Gap**: IaC exists but governance is incomplete (no peer review, no drift detection).
- **Recommendation**: Add CODEOWNERS. Enable branch protection. Add AWS Config rules.
- **Evidence**: `lib/` directory (CDK IaC), no CODEOWNERS file

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: No CI/CD files found (no GitHub Actions, GitLab CI, Jenkinsfile, buildspec.yml, CodePipeline). Deployment is manual `cdk deploy`. No contract tests.
- **Gap**: No CI/CD pipeline. No API contract testing.
- **Recommendation**: Implement CI/CD pipeline with lint → test → cdk diff → approval → cdk deploy. Add contract tests.
- **Evidence**: No CI/CD files. `README.md` (`cdk deploy` instructions)

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: No blue/green, canary, or CodeDeploy configuration. `cdk deploy` overwrites in-place. Rollback requires manual git revert + redeploy.
- **Gap**: No automated rollback. Broken deployments require manual intervention.
- **Recommendation**: Implement Lambda versioning with aliases and CodeDeploy traffic shifting. Add canary deployments.
- **Evidence**: `README.md`, no deployment config in CDK

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: `test/aws-microservices.test.ts` is entirely commented out. `jest.config.js` configured but no active tests. Zero test coverage.
- **Gap**: No test coverage. API behavior changes affecting agents are not caught.
- **Recommendation**: Uncomment and update CDK tests. Add Lambda handler unit tests. Add API integration tests.
- **Evidence**: `test/aws-microservices.test.ts` (commented out), `jest.config.js`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: RISK-QUALITY
- **Finding**: DynamoDB tables have no explicit encryption config. Default AWS-owned key encryption is in effect. Order table with PII/payment data lacks customer-managed KMS keys.
- **Gap**: Default encryption only. No customer-managed KMS for sensitive data.
- **Recommendation**: Add customer-managed KMS keys for order table using `encryption: TableEncryption.CUSTOMER_MANAGED`.
- **Evidence**: `lib/database.ts` (no encryption property on tables)

## Evidence Index

### Infrastructure as Code
| File | Questions Referenced |
|------|---------------------|
| `lib/aws-microservices-stack.ts` | AUTH-Q1, AUTH-Q6, AUTH-Q7, STATE-Q5, OBS-Q2, ENG-Q1 |
| `lib/apigateway.ts` | API-Q1, API-Q2, API-Q8, AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q7, STATE-Q5, STATE-Q6 |
| `lib/database.ts` | DATA-Q1, DATA-Q2, DATA-Q3, DATA-Q4, DATA-Q5, DISC-Q1, DISC-Q2, DISC-Q3, ENG-Q5, HITL-Q1, STATE-Q7 |
| `lib/eventbus.ts` | API-Q6, API-Q7, HITL-Q2, STATE-Q1 |
| `lib/microservice.ts` | AUTH-Q2, AUTH-Q5, AUTH-Q6, STATE-Q4, STATE-Q7, OBS-Q1, OBS-Q2, ENG-Q1 |
| `lib/queue.ts` | API-Q6, STATE-Q1, STATE-Q7 |
| `bin/aws-microservices.ts` | DATA-Q2, HITL-Q3, ENG-Q1 |
| `cdk.json` | ENG-Q1 |

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `src/product/index.js` | API-Q1, API-Q3, API-Q5, AUTH-Q3, STATE-Q2, STATE-Q3, DATA-Q3, DATA-Q5, DATA-Q6, DATA-Q7, OBS-Q1, OBS-Q3 |
| `src/product/ddbClient.js` | STATE-Q4, AUTH-Q5 |
| `src/basket/index.js` | API-Q1, API-Q3, API-Q4, API-Q5, API-Q6, API-Q7, AUTH-Q3, AUTH-Q4, STATE-Q1, STATE-Q2, STATE-Q3, DATA-Q1, DATA-Q3, DATA-Q5, DATA-Q6, DATA-Q7, DISC-Q2, HITL-Q1, HITL-Q2, OBS-Q1, OBS-Q3 |
| `src/basket/ddbClient.js` | STATE-Q4, AUTH-Q5 |
| `src/basket/eventBridgeClient.js` | STATE-Q4, AUTH-Q5 |
| `src/ordering/index.js` | API-Q1, API-Q3, API-Q5, AUTH-Q3, AUTH-Q4, STATE-Q2, DATA-Q1, DATA-Q3, DATA-Q5, DATA-Q6, DATA-Q7, OBS-Q1, OBS-Q3 |
| `src/ordering/ddbClient.js` | STATE-Q4 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| No CI/CD files found | ENG-Q2 (absence is evidence) |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| No container files found | — (absence noted in discovery) |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `package.json` | OBS-Q1 (no tracing libraries), ENG-Q4 (jest configured) |
| `src/product/package.json` | OBS-Q1 (no logging libraries), STATE-Q4 (no resilience libraries) |
| `src/basket/package.json` | OBS-Q1 (no logging libraries), STATE-Q4 (no resilience libraries) |
| `src/ordering/package.json` | OBS-Q1 (no logging libraries), STATE-Q4 (no resilience libraries) |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `tsconfig.json` | — (build configuration) |
| `jest.config.js` | ENG-Q4 (test framework configured but unused) |
| `src/basket/checkoutbasketevents.json` | API-Q7 (EventBridge event sample) |

### Test Files
| File | Questions Referenced |
|------|---------------------|
| `test/aws-microservices.test.ts` | ENG-Q4 (entirely commented out) |

### Documentation
| File | Questions Referenced |
|------|---------------------|
| `README.md` | ENG-Q2, ENG-Q3, DATA-Q4 |
