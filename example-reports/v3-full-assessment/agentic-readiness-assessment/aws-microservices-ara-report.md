# Agentic Readiness Assessment Report

**Target**: ./services/aws-microservices
**Date**: 2026-04-27
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P0
**Tags**: microservices, serverless, event-driven
**Context**: Event-driven serverless microservices (product, basket, ordering) with Lambda, DynamoDB, EventBridge, SQS. The agent will invoke these as tools for order status lookups and return processing.

**Archetype Justification**: The services own persistent state in three DynamoDB tables (product, basket, order), expose Create/Update/Delete endpoints alongside Read, and manage entity lifecycle (product CRUD, basket CRUD with checkout, order creation and queries). This matches stateful-crud.

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 2 | **RISK-SAFETY**: 9 | **RISK-QUALITY**: 19 | **INFOs**: 13

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days. The two blockers (no authentication and unclassified PII/payment data) represent fundamental security gaps that must be addressed before any agent can safely interact with these services, even in read-only mode.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 2 |
| RISK-SAFETY | 9 |
| RISK-QUALITY | 19 |
| INFO | 13 |
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
- **Finding**: API Gateway has no authorizers configured. All three `LambdaRestApi` constructs in `lib/apigateway.ts` (`productApi`, `basketApi`, `orderApi`) use `proxy: false` with explicit routes but no `defaultMethodOptions`, no API key requirements, no Cognito authorizers, and no IAM authorization. All endpoints are publicly accessible. No service account definitions, no machine identity mechanism, no principal attribution in any layer.
- **Gap**: No authentication mechanism exists. Any caller — human, agent, or anonymous internet user — can invoke any endpoint without identity. There is no way to distinguish which agent made a call, and no audit trail for agent actions.
- **Remediation**:
  - **Immediate**: Add IAM authorization to API Gateway methods by setting `authorizationType: AuthorizationType.IAM` in the CDK `LambdaRestApi` constructs. Create dedicated IAM roles per agent identity with scoped permissions. Alternatively, add a Cognito User Pool with app clients for machine identity (client credentials flow).
  - **Target State**: Every API Gateway endpoint requires authenticated identity. Agent identities are distinguishable in CloudTrail and application logs. API keys or IAM roles are scoped per agent with least-privilege access.
  - **Estimated Effort**: Medium (2–4 weeks)
  - **Dependencies**: AUTH-Q2 (scoped permissions), AUTH-Q6 (audit logging), AUTH-Q7 (identity suspension) all depend on having an identity system in place first.
- **Evidence**: `lib/apigateway.ts` (no auth configuration), `lib/microservice.ts` (no authorizer references)

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: The order DynamoDB table stores PII and payment data without classification. The checkout flow in `src/basket/index.js` (`prepareOrderPayload`) aggregates `firstName`, `lastName`, `email`, `address`, `paymentMethod`, and `cardInfo` into the order payload, which is then stored in DynamoDB via `src/ordering/index.js` (`createOrder`). The `lib/database.ts` table definition has no data classification tags, no field-level encryption, and no column-level access controls. No Macie integration exists.
- **Gap**: PII (name, email, address) and payment card data (cardInfo, paymentMethod) are stored in DynamoDB without any classification, tagging, or field-level access controls. An agent querying `GET /order/{userName}` would receive all fields including payment card information with no filtering or redaction.
- **Remediation**:
  - **Immediate**: (1) Add data classification tags to the DynamoDB order table in `lib/database.ts` (e.g., `data_classification: 'confidential'`, `contains_pii: 'true'`, `contains_payment_data: 'true'`). (2) Implement field-level response filtering in `src/ordering/index.js` to exclude `cardInfo` and `paymentMethod` from API responses. (3) Consider encrypting sensitive fields with a customer-managed KMS key before storing.
  - **Target State**: All sensitive data fields are classified and tagged. Field-level access controls prevent agents from retrieving payment card data. PII fields are available only to authorized principals with explicit need.
  - **Estimated Effort**: Medium (2–4 weeks)
  - **Dependencies**: AUTH-Q1 (identity) must be resolved first — field-level access controls require knowing who is requesting the data.
- **Evidence**: `lib/database.ts` (no tags, no encryption config), `src/basket/index.js` (prepareOrderPayload with PII fields), `src/ordering/index.js` (createOrder stores all fields), `src/basket/checkoutbasketevents.json` (sample event structure)

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: `lib/microservice.ts` grants `grantReadWriteData` on DynamoDB tables to all three Lambda functions. The product Lambda gets read+write on the product table, basket Lambda gets read+write on the basket table, and ordering Lambda gets read+write on the order table. There are no scoped agent-specific IAM roles. No resource-level restrictions exist beyond table-level access. Even for read-only agent use cases, the Lambda functions themselves have write permissions.
- **Gap**: No ability to scope agent access to read-only for specific resources. All Lambda functions have full read/write access to their respective tables. An agent identity cannot be restricted to read-only operations at the IAM layer.
- **Compensating Controls**:
  - Restrict the agent to only invoke GET methods at the API Gateway level using IAM policy conditions (`execute-api:GET`).
  - Create a read-only API Gateway resource policy that limits agent IAM roles to GET methods only.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create separate IAM roles for read-only and read-write access patterns. Implement API Gateway resource policies that restrict agent identities to specific HTTP methods.
- **Evidence**: `lib/microservice.ts` (`grantReadWriteData` calls on lines for all three functions)

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No RBAC, ABAC, or action-level authorization exists in any Lambda handler (`src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js`). All handlers switch on `event.httpMethod` without checking caller permissions. API Gateway has no method-level authorization configured in `lib/apigateway.ts`. All HTTP methods (GET, POST, PUT, DELETE) are open to all callers.
- **Gap**: Any caller can execute any operation — including DELETE /product/{id} or POST /basket/checkout — without authorization checks. There is no mechanism to allow an agent to read records but prevent it from deleting them.
- **Compensating Controls**:
  - Add API Gateway IAM authorization with method-level policies (e.g., allow GET only for agent roles).
  - Implement a Lambda authorizer that checks action-level permissions based on caller identity.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add IAM authorization to API Gateway with per-method policies. For the read-only agent scope, restrict agent IAM roles to `execute-api:Invoke` on GET resources only.
- **Evidence**: `lib/apigateway.ts` (no auth on any method), `src/product/index.js` (no permission checks), `src/basket/index.js` (no permission checks), `src/ordering/index.js` (no permission checks)

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No CloudTrail configuration exists in any CDK construct. No audit logging infrastructure is defined. Lambda functions use `console.log` for operational logging but produce no structured audit trail. No immutable log storage (no S3 bucket with object lock, no CloudWatch log retention policies). Since no authentication exists (AUTH-Q1), there is no principal attribution in any log.
- **Gap**: Cannot trace who made what API call. No immutable audit trail exists. If an agent (or any caller) reads sensitive order data, there is no forensic record.
- **Compensating Controls**:
  - Enable API Gateway access logging to CloudWatch as an immediate measure.
  - Enable CloudTrail for the AWS account (account-level, not per-stack) to capture API Gateway invocations.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add CloudTrail configuration to the CDK stack. Configure API Gateway access logging. Set up CloudWatch log groups with retention policies and export to S3 with object lock for immutability.
- **Evidence**: `lib/aws-microservices-stack.ts` (no CloudTrail construct), `lib/apigateway.ts` (no access logging), `src/product/index.js` (console.log only)

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No identity management system exists. No API key management, no IAM role deactivation procedures, no Cognito user pool, no service account disable mechanisms. Since AUTH-Q1 identified that no authentication exists at all, there is no identity to suspend.
- **Gap**: If an agent identity is compromised or behaves anomalously, there is no mechanism to suspend or revoke it without taking down the entire API. Cannot isolate a misbehaving agent.
- **Compensating Controls**:
  - Implement API Gateway API keys as a first step — keys can be deleted individually to revoke access.
  - Use IAM roles per agent with the ability to attach deny policies for immediate suspension.
- **Remediation Timeline**: 30–60 days (dependent on AUTH-Q1 resolution)
- **Recommendation**: As part of AUTH-Q1 remediation, ensure the chosen identity mechanism supports individual suspension (Cognito user disable, IAM role policy attachment, API key deletion).
- **Evidence**: `lib/apigateway.ts` (no API keys, no authorizers), `lib/aws-microservices-stack.ts` (no Cognito, no identity constructs)

#### STATE-Q1: Compensation and Rollback ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The checkout flow in `src/basket/index.js` performs a 3-step sequence: (1) `getBasket` retrieves the basket, (2) `publishCheckoutBasketEvent` sends an event to EventBridge, (3) `deleteBasket` removes the basket from DynamoDB. If EventBridge publish fails after step 1, the basket is intact (safe). But if `deleteBasket` (step 3) fails after the event is published (step 2), the order will be created in the ordering service while the basket remains, creating an inconsistent state. Conversely, if the ordering Lambda fails to create the order after the basket is deleted, the basket is lost with no order created. No saga pattern, no Step Functions, no undo endpoints exist.
- **Gap**: No compensation or rollback logic for the multi-step checkout flow. Partial failures leave the system in inconsistent states.
- **Compensating Controls**:
  - Implement a dead letter queue (DLQ) on the SQS OrderQueue to capture failed order creation attempts for manual remediation.
  - Add a status field to the basket table to mark baskets as "checkout-in-progress" rather than immediately deleting them.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Refactor the checkout flow to use AWS Step Functions with error handling and compensation steps. Alternatively, implement the saga pattern with compensating transactions.
- **Evidence**: `src/basket/index.js` (checkoutBasket function — 3-step sequence without compensation), `lib/queue.ts` (no DLQ configured on OrderQueue)

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No circuit breaker library exists in any dependency manifest. No retry logic in application code. DynamoDB clients in `src/product/ddbClient.js`, `src/basket/ddbClient.js`, and `src/ordering/ddbClient.js` are created with `new DynamoDBClient()` using default configuration — no timeout settings, no retry configuration. The EventBridge client in `src/basket/eventBridgeClient.js` is similarly unconfigured. When the basket Lambda calls EventBridge during checkout, there are no circuit breakers to prevent cascading failures.
- **Gap**: No resilience patterns exist. A downstream failure (DynamoDB throttling, EventBridge outage) will cascade through the services without any protection.
- **Compensating Controls**:
  - Configure DynamoDB client retry settings with exponential backoff and max retries.
  - Add Lambda function timeout configuration in `lib/microservice.ts` to prevent runaway executions.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure AWS SDK retry strategies on all DynamoDB and EventBridge clients. Add Lambda timeout settings. Consider implementing the circuit breaker pattern for the EventBridge call in the checkout flow.
- **Evidence**: `src/product/ddbClient.js` (default DynamoDBClient), `src/basket/ddbClient.js` (default DynamoDBClient), `src/basket/eventBridgeClient.js` (default EventBridgeClient), `lib/microservice.ts` (no timeout configuration)

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No API Gateway throttling configuration exists in `lib/apigateway.ts`. No usage plans, no API keys, no method-level throttling. No WAF rules in any CDK construct. No application-level rate limiting middleware in any Lambda handler. Default API Gateway account-level throttle limits apply (10,000 requests/second) but are not explicitly configured or scoped per consumer.
- **Gap**: No explicit rate limiting exists. A runaway agent loop making rapid GET requests could overwhelm DynamoDB read capacity or hit API Gateway account limits, affecting all consumers.
- **Compensating Controls**:
  - Add API Gateway usage plans with throttle settings (e.g., 100 requests/second per API key) in the CDK stack.
  - Configure Lambda reserved concurrency to limit concurrent executions per function.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add `UsagePlan` and `ApiKey` constructs to `lib/apigateway.ts` with per-key throttle limits. Configure Lambda reserved concurrency in `lib/microservice.ts`.
- **Evidence**: `lib/apigateway.ts` (no usage plans, no throttle settings), `lib/microservice.ts` (no reserved concurrency)

#### DATA-Q2: Data Residency and Sovereignty ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No region is specified in the CDK stack. `bin/aws-microservices.ts` has the environment configuration commented out (`// env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: process.env.CDK_DEFAULT_REGION }`). DynamoDB tables are created without region specification — they deploy to whatever region the CDK CLI defaults to. No data residency documentation exists. No GDPR/LGPD compliance references. The order table contains PII (email, address) and payment data that may be subject to residency requirements.
- **Gap**: No explicit data residency controls. An agent sending order data (PII, payment info) to an LLM provider in a different region could create compliance violations depending on applicable regulations. The deployment region is implicit and undocumented.
- **Compensating Controls**:
  - Document the intended deployment region and data residency requirements.
  - Configure the agent to use a region-local LLM endpoint (e.g., Amazon Bedrock in the same region as DynamoDB).
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Uncomment and configure the `env` property in `bin/aws-microservices.ts` to explicitly set the deployment region. Document data residency requirements for PII and payment data stored in the order table.
- **Evidence**: `bin/aws-microservices.ts` (commented-out env configuration), `lib/database.ts` (no region-specific settings)

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: All Lambda handlers use `console.log` to log full request payloads and DynamoDB response items. In `src/basket/index.js`, the checkout flow logs the complete `checkoutRequest` object which contains `firstName`, `lastName`, `email`, `address`, `paymentMethod`, and `cardInfo`: `console.log("Success prepareOrderPayload, orderPayload:", checkoutRequest)` and `console.log("publishCheckoutBasketEvent with payload :", checkoutPayload)`. In `src/ordering/index.js`, `console.log(basketCheckoutEvent)` logs the full order with PII. No log scrubbing middleware, no PII masking libraries, no CloudWatch log filters exist.
- **Gap**: PII (including payment card information) is logged in plaintext to CloudWatch Logs via console.log in the checkout and order creation flows. This is a compliance violation for PCI DSS (card data in logs) and potentially GDPR (PII in uncontrolled log storage).
- **Compensating Controls**:
  - Implement a logging wrapper that redacts sensitive fields (cardInfo, email, address) before logging.
  - Set CloudWatch Logs retention to a short period (e.g., 7 days) to limit PII exposure window.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Replace `console.log` with a structured logger that automatically redacts fields matching PII patterns (email, card numbers, addresses). Remove or redact `cardInfo` from all log statements in `src/basket/index.js` and `src/ordering/index.js`.
- **Evidence**: `src/basket/index.js` (console.log of checkoutRequest with PII), `src/ordering/index.js` (console.log of basketCheckoutEvent with PII), `src/product/index.js` (console.log of request payloads)

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, Swagger, GraphQL schema, or Smithy specification files exist in the repository. API routes are defined only in CDK code (`lib/apigateway.ts`) and Lambda handler switch statements.
- **Gap**: No machine-readable spec exists. Agent tool definitions must be authored manually by reading CDK code and Lambda handlers. Specs will drift from implementation without automated generation.
- **Compensating Controls**:
  - Manually author an OpenAPI spec based on the routes defined in `lib/apigateway.ts` and handler logic.
  - Use CDK OpenAPI extensions to auto-generate specs from the API Gateway definition.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Generate an OpenAPI 3.0 specification from the existing API Gateway configuration. Consider using `@aws-cdk/aws-apigateway` OpenAPI spec export or manually documenting the 3 APIs (product, basket, order) with request/response schemas.
- **Evidence**: No spec files found. Routes defined in `lib/apigateway.ts`, handler logic in `src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js`.

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: All three Lambda handlers return identical error structures: `{ statusCode: 500, body: JSON.stringify({ message: "Failed to perform operation.", errorMsg: e.message, errorStack: e.stack }) }`. No structured error codes (e.g., `PRODUCT_NOT_FOUND`, `BASKET_EMPTY`). No retryable boolean or error category. Only HTTP 200 (success) and 500 (error) status codes are used — no 400, 404, or 429 responses. Stack traces are exposed in production responses.
- **Gap**: Agents cannot distinguish retriable errors (DynamoDB throttle) from terminal errors (invalid input). All failures return HTTP 500 with a stack trace. No error taxonomy exists.
- **Compensating Controls**:
  - Agent tool definitions can include retry logic for all 500 errors with exponential backoff.
  - Parse `errorMsg` field for known patterns (e.g., "ProvisionedThroughputExceededException" = retriable).
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Implement structured error responses with error codes, HTTP status code mapping (400 for bad input, 404 for not found, 429 for throttle, 500 for internal), and a retryable boolean. Remove stack traces from production responses.
- **Evidence**: `src/product/index.js` (catch block), `src/basket/index.js` (catch block), `src/ordering/index.js` (catch block)

#### API-Q6: Asynchronous Operation Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The checkout flow is asynchronous: `POST /basket/checkout` publishes an event to EventBridge which routes through SQS to the ordering Lambda. However, the endpoint returns HTTP 200 synchronously after publishing the event and deleting the basket — it provides no job ID, no polling endpoint, and no webhook callback. The caller has no way to determine when or whether the order was successfully created.
- **Gap**: Agent cannot track the completion status of checkout operations. After calling `POST /basket/checkout`, the agent has no programmatic way to confirm the order was created without polling `GET /order/{userName}` and matching by timestamp.
- **Compensating Controls**:
  - Agent can poll `GET /order/{userName}?orderDate=<timestamp>` after checkout to verify order creation.
  - Implement a correlation ID in the checkout response that maps to the order record.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Return a correlation ID or order reference in the checkout response. Add a `GET /order/status/{correlationId}` endpoint for polling. Consider adding webhook callback support for async completion notification.
- **Evidence**: `src/basket/index.js` (checkoutBasket function — no return value after async flow), `lib/eventbus.ts` (EventBridge → SQS routing), `lib/queue.ts` (SQS → ordering Lambda)

#### AUTH-Q4: Identity Propagation and Delegation — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No JWT parsing, no OAuth2 integration, no token exchange, no user context headers. Lambda handlers receive raw API Gateway events with no authenticated principal. No Cognito or Okta integration. No distinction between agent-as-self and agent-on-behalf-of-user calls. The `userName` field in basket and order operations is a business data field (passed in request body/path), not an authenticated identity.
- **Gap**: No identity propagation exists. The system cannot distinguish between an agent acting under its own identity vs. acting on behalf of a user. The `userName` path parameter is unauthenticated — any caller can query any user's basket or orders.
- **Compensating Controls**:
  - For the read-only pilot, restrict agent access to specific `userName` values via API Gateway resource policy conditions.
  - Implement a mapping between agent identity and authorized `userName` values at the agent orchestration layer.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement Cognito or IAM authorization with identity propagation. Map the authenticated principal to authorized `userName` values. Ensure agent-on-behalf-of-user calls are bounded by that user's permissions.
- **Evidence**: `lib/apigateway.ts` (no auth), `src/basket/index.js` (userName from path/body, not auth context), `src/ordering/index.js` (userName from path parameters)

#### AUTH-Q5: Credential Management — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No hardcoded credentials found in any source file. Environment variables in `lib/microservice.ts` contain only non-sensitive values: `PRIMARY_KEY`, `DYNAMODB_TABLE_NAME`, `EVENT_SOURCE`, `EVENT_DETAILTYPE`, `EVENT_BUSNAME`. Lambda functions use IAM execution roles (implicit credentials from `grantReadWriteData`) for DynamoDB and EventBridge access. No Secrets Manager or Vault integration exists, but no secrets are currently needed.
- **Gap**: No secrets management infrastructure exists. The current architecture uses IAM roles (good), but if API keys, external service credentials, or database passwords are added in the future, there is no established pattern for secrets management.
- **Compensating Controls**:
  - The current IAM role-based credential model is acceptable for DynamoDB/EventBridge access.
  - When adding external credentials (e.g., for agent auth), establish Secrets Manager integration from the start.
- **Remediation Timeline**: 30–60 days (when new credentials are needed)
- **Recommendation**: When implementing AUTH-Q1 (machine identity), use AWS Secrets Manager for any API keys or client secrets. Add Secrets Manager constructs to the CDK stack proactively.
- **Evidence**: `lib/microservice.ts` (environment variables — non-sensitive only), `src/product/ddbClient.js` (implicit credentials), `src/basket/eventBridgeClient.js` (implicit credentials)

#### STATE-Q2: Queryable Current State — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: GET endpoints exist for all entities: `GET /product` (all products), `GET /product/{id}` (single product), `GET /basket/{userName}` (user's basket), `GET /order` (all orders), `GET /order/{userName}?orderDate=<timestamp>` (specific order). State is queryable via REST API for all three microservices.
- **Gap**: Positive finding — minimal gap. However, basket state is not queryable by product or item (only by userName), and order queries require both userName and orderDate.
- **Compensating Controls**:
  - Existing query endpoints are sufficient for the read-only agent use case (order status lookups).
- **Remediation Timeline**: No immediate action needed
- **Recommendation**: Consider adding query flexibility (e.g., query orders by date range, or basket by product ID) to support broader agent use cases.
- **Evidence**: `lib/apigateway.ts` (route definitions), `src/product/index.js` (GET handlers), `src/basket/index.js` (GET handlers), `src/ordering/index.js` (GET handlers)

#### STATE-Q7: Infrastructure Capacity for Agent Traffic — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: DynamoDB tables use `BillingMode.PAY_PER_REQUEST` (on-demand auto-scaling) in `lib/database.ts`. Lambda functions have no reserved or provisioned concurrency configured in `lib/microservice.ts`. SQS OrderQueue has default visibility timeout of 30 seconds with batch size of 1 in `lib/queue.ts`. No load testing evidence exists in the repository. No capacity planning documentation.
- **Gap**: DynamoDB scales automatically (positive), but Lambda concurrency is unbounded — agent traffic could trigger hundreds of concurrent Lambda invocations. No load testing has validated the system under agent-like traffic patterns (rapid, exploratory queries).
- **Compensating Controls**:
  - DynamoDB PAY_PER_REQUEST handles variable read loads well for the read-only agent use case.
  - Add Lambda reserved concurrency as a safety ceiling.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure Lambda reserved concurrency in `lib/microservice.ts`. Conduct load testing simulating agent traffic patterns (burst reads, rapid sequential queries). Monitor DynamoDB consumed capacity metrics.
- **Evidence**: `lib/database.ts` (PAY_PER_REQUEST billing), `lib/microservice.ts` (no concurrency settings), `lib/queue.ts` (default SQS settings)

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No separate environment configurations exist. `bin/aws-microservices.ts` has commented-out environment configuration. No staging, sandbox, or dev CDK stacks. No docker-compose for local testing. No seed data scripts. No synthetic data generators. Only a single stack definition (`AwsMicroservicesStack`) exists for all environments.
- **Gap**: No sandbox or staging environment for agent testing. The first time an agent is tested against realistic conditions will be in production.
- **Compensating Controls**:
  - Deploy a separate CDK stack with a different stack name (e.g., `AwsMicroservicesStack-staging`) to the same or different account.
  - Use DynamoDB local for offline agent integration testing.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Create environment-specific CDK stack configurations with separate table names and API endpoints. Add seed data scripts for testing. Consider using AWS CDK stages for multi-environment deployment.
- **Evidence**: `bin/aws-microservices.ts` (single stack, commented-out env), `lib/aws-microservices-stack.ts` (no environment parameterization)

#### DATA-Q3: Selective Query Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: `GET /product` uses `ScanCommand` with no `Limit` or `ExclusiveStartKey` parameters — returns all products. `GET /basket` uses `ScanCommand` with no pagination — returns all baskets. `GET /order` uses `ScanCommand` with no pagination — returns all orders. `GET /order/{userName}` uses `QueryCommand` with `KeyConditionExpression` but no pagination. `GET /product/{id}?category=Phone` uses `QueryCommand` with `FilterExpression` but no result limit.
- **Gap**: No pagination, no result size limits, no cursor-based pagination. Agent queries against large datasets would return unbounded result sets, potentially exhausting LLM context windows and increasing token costs.
- **Compensating Controls**:
  - Agent tool definitions can limit result processing to the first N items from the response.
  - Implement client-side truncation in the agent orchestration layer.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add `Limit` and `ExclusiveStartKey` parameters to all `ScanCommand` and `QueryCommand` operations. Expose `limit` and `nextToken` query parameters in the API. Return pagination metadata (`nextToken`, `count`, `total`) in responses.
- **Evidence**: `src/product/index.js` (ScanCommand without Limit), `src/basket/index.js` (ScanCommand without Limit), `src/ordering/index.js` (ScanCommand without Limit)

#### DATA-Q4: System of Record Designations — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No system-of-record documentation exists. No master data management references. Each microservice owns its DynamoDB table (product service → product table, basket service → basket table, ordering service → order table), which is a reasonable microservice data ownership pattern, but there is no formal documentation establishing these as authoritative data sources.
- **Gap**: No formal system-of-record designations. An agent querying multiple services would not know which is authoritative for product pricing (product table? basket item price? order line item price?).
- **Compensating Controls**:
  - Document that the product service is the system of record for product data, and the order service is the system of record for completed orders.
- **Remediation Timeline**: 7–14 days (documentation only)
- **Recommendation**: Create a data ownership document that designates each service as the system of record for its domain entities. Clarify which service is authoritative for overlapping data (e.g., product price).
- **Evidence**: `lib/database.ts` (3 separate tables), `lib/aws-microservices-stack.ts` (service-per-table pattern)

#### DATA-Q5: Temporal Metadata and Freshness — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The order table has `orderDate` set via `new Date().toISOString()` in `src/ordering/index.js`. Product and basket tables have no `created_at`, `updated_at`, or timestamp fields defined in `lib/database.ts` or used in handler code. No `Cache-Control` headers are returned. No data freshness signaling (no `X-Data-Age`, no `last_refreshed`). No consistency level indicators.
- **Gap**: Only the ordering service has temporal metadata (orderDate). Product and basket data have no timestamps — an agent cannot determine when a product was last updated or when a basket was last modified.
- **Compensating Controls**:
  - Agent can treat product data as eventually consistent and refresh periodically.
  - DynamoDB Streams could be used to track change timestamps externally.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add `createdAt` and `updatedAt` fields to product and basket entities. Set timestamps in create/update handlers. Return `Last-Modified` or `Cache-Control` headers from GET endpoints.
- **Evidence**: `src/ordering/index.js` (orderDate = new Date().toISOString()), `src/product/index.js` (no timestamps), `src/basket/index.js` (no timestamps), `lib/database.ts` (no timestamp fields in schema comments)

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No API versioning exists — routes are unversioned (`/product`, `/basket`, `/order` — no `/v1/` prefix). No JSON Schema files, no Avro/Protobuf schemas. No schema registry. No database migration files. No changelog or deprecation notices. No breaking change detection tools. No consumer-driven contract tests (no Pact). DynamoDB schemas are implicit in code (defined only in CDK comments and handler logic).
- **Gap**: Agent tool bindings would break silently on any API change. No mechanism exists to detect or communicate breaking changes. Any schema or route change could invalidate agent tool definitions without warning.
- **Compensating Controls**:
  - Pin agent tool definitions to known API behavior and re-validate after any deployment.
  - Add API versioning (e.g., `/v1/product`) before agent integration.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add API versioning to all routes (`/v1/product`, `/v1/basket`, `/v1/order`). Implement OpenAPI spec validation in CI. Consider consumer-driven contract testing (Pact) to detect breaking changes before deployment.
- **Evidence**: `lib/apigateway.ts` (unversioned routes), no schema files found, no changelog found

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No OpenTelemetry SDK in any dependency manifest. No X-Ray instrumentation — Lambda tracing is not enabled in `lib/microservice.ts` (no `tracing: Tracing.ACTIVE`). No `traceparent` header propagation. Logs are unstructured `console.log` output (not JSON). No `request_id` or `correlation_id` fields in log output. API Gateway request IDs are available in the Lambda event but not logged.
- **Gap**: Agent-initiated failures would be extremely difficult to debug. No way to trace a request across API Gateway → Lambda → DynamoDB → EventBridge → SQS → ordering Lambda. No structured logs to filter or search.
- **Compensating Controls**:
  - Enable Lambda X-Ray tracing in `lib/microservice.ts` (`tracing: Tracing.ACTIVE`) as a quick win.
  - Log the API Gateway requestId from the Lambda event context.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Enable X-Ray tracing on all Lambda functions. Replace `console.log` with a structured JSON logger (e.g., `@aws-lambda-powertools/logger`). Include `requestId`, `correlationId`, and `traceId` in every log entry.
- **Evidence**: `lib/microservice.ts` (no tracing configuration), `src/product/index.js` (console.log), `src/basket/index.js` (console.log), `src/ordering/index.js` (console.log)

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No CloudWatch alarms defined in any CDK construct. No anomaly detection. No PagerDuty, OpsGenie, or SNS notification integration. No SLO-based alerting. No composite alarms. Lambda and API Gateway default metrics are collected by CloudWatch but no alarms are configured to act on them.
- **Gap**: Target system degradation (high error rates, increased latency) would not be detected. Agents consuming degraded APIs would cascade failures without operational awareness.
- **Compensating Controls**:
  - CloudWatch default metrics for Lambda (errors, duration) and API Gateway (4xx, 5xx, latency) are collected automatically — add alarms manually in the console as a stopgap.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add CloudWatch alarms in CDK for: Lambda error count > 0, Lambda duration > 80% of timeout, API Gateway 5xx rate > 1%, API Gateway p99 latency > 5s. Configure SNS topic for alarm notifications.
- **Evidence**: `lib/aws-microservices-stack.ts` (no CloudWatch alarm constructs), `lib/microservice.ts` (no alarm configuration)

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Infrastructure is defined as CDK (IaC exists — positive). API Gateway, Lambda, DynamoDB, EventBridge, and SQS are all defined as CDK constructs in `lib/`. However, no branch protection or PR review requirements are evidenced in the repository. No AWS Config rules or CloudFormation drift detection is configured. No automated plan review before deployment.
- **Gap**: IaC exists (1 of 3 sub-checks passes), but change review enforcement and drift detection are absent. Infrastructure changes could be deployed without peer review, and deployed resources could drift from code without detection.
- **Compensating Controls**:
  - Run `cdk diff` before every deployment to manually review changes.
  - Enable CloudFormation drift detection via the AWS Console.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add CI/CD pipeline with `cdk diff` output as a PR check. Enable CloudFormation drift detection. Configure AWS Config rules for critical resources (API Gateway, DynamoDB, Lambda).
- **Evidence**: `lib/` directory (CDK constructs — IaC exists), no CI/CD configuration found, no AWS Config rules in CDK

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No CI/CD pipeline configuration exists. No `.github/workflows/` directory, no `buildspec.yml`, no `Jenkinsfile`, no CodePipeline definition in CDK. Deployment is manual via `cdk deploy` (per README.md). No contract tests, no OpenAPI spec validation, no breaking change detection.
- **Gap**: No CI/CD pipeline exists at all. API changes are deployed manually without any automated testing or contract validation. Agent-facing API breaks would not be caught before production.
- **Compensating Controls**:
  - Manual `cdk diff` review before deployment provides minimal change awareness.
  - Manual API testing before deployment.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a CI/CD pipeline (GitHub Actions, CodePipeline, or similar) with: (1) CDK synth and diff, (2) unit tests, (3) API contract test stage, (4) automated deployment with approval gate.
- **Evidence**: No CI/CD files found. `README.md` documents manual `cdk deploy`.

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No blue/green deployment, no CodeDeploy, no canary deployment, no feature flags, no rollback triggers. Deployment is manual `cdk deploy`. CDK/CloudFormation supports automatic rollback on deployment failure, but no explicit rollback strategy exists for breaking API changes or data schema issues.
- **Gap**: No rollback capability for a deployment that breaks agent-facing APIs. Rolling back requires manual `cdk deploy` with a previous version — there is no automated rollback trigger or process.
- **Compensating Controls**:
  - CloudFormation automatically rolls back failed deployments (built-in CDK behavior).
  - Git revert + `cdk deploy` for manual rollback.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement Lambda versioning with aliases and traffic shifting. Add CodeDeploy integration for Lambda with automatic rollback on CloudWatch alarm triggers. Consider API Gateway canary releases.
- **Evidence**: `bin/aws-microservices.ts` (single stack deployment), `README.md` (manual cdk deploy)

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: `test/aws-microservices.test.ts` exists but is entirely commented out — the only active line is an empty `test('SQS Queue Created', () => {})`. No API test suites, no Postman/Newman collections, no integration tests, no contract tests. The `jest.config.js` is configured but there are no active test files.
- **Gap**: Zero test coverage. No automated tests validate API behavior, input handling, output format, or error responses. Any code change could break agent-facing APIs without detection.
- **Compensating Controls**:
  - Manual API testing via curl or Postman before deployment.
  - Agent integration tests at the orchestration layer can catch some regressions.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Uncomment and expand the CDK test. Add API integration tests for each endpoint. Create Postman/Newman collections for the product, basket, and order APIs. Add test execution to the CI/CD pipeline.
- **Evidence**: `test/aws-microservices.test.ts` (fully commented out), `jest.config.js` (test configuration exists but no active tests)

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: DynamoDB tables in `lib/database.ts` have no explicit encryption configuration. DynamoDB encrypts at rest by default using AWS-owned keys (free, no configuration required). However, no customer-managed KMS keys (CMK) are configured. The order table stores PII and payment data that warrants stronger encryption controls.
- **Gap**: Default AWS-owned key encryption exists (basic compliance), but customer-managed KMS keys are not used. This limits key rotation control, access auditing, and the ability to revoke access to encrypted data.
- **Compensating Controls**:
  - DynamoDB default encryption with AWS-owned keys provides baseline at-rest encryption.
  - For the read-only pilot, this is acceptable as a compensating control.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Configure customer-managed KMS keys for the order DynamoDB table (which contains PII and payment data). Add `encryption: TableEncryption.CUSTOMER_MANAGED` with a dedicated KMS key in `lib/database.ts`. This enables key rotation control and access auditing via CloudTrail.
- **Evidence**: `lib/database.ts` (no encryption property on table constructs)

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO (Pass)
- **Finding**: The application exposes three documented REST APIs via API Gateway (`lib/apigateway.ts`): Product Service (GET/POST/PUT/DELETE /product), Basket Service (GET/POST/DELETE /basket, POST /basket/checkout), and Order Service (GET /order). All APIs are implemented as `LambdaRestApi` with explicit resource and method definitions. No direct database access, file-based exchange, or UI automation is required for integration.
- **Implication**: REST APIs exist and are well-structured for agent tool integration. The agent can bind to these APIs for order status lookups (GET /order/{userName}) and product queries (GET /product/{id}).
- **Recommendation**: Document the API endpoints in an OpenAPI specification to formalize the integration surface (see API-Q2).
- **Evidence**: `lib/apigateway.ts` (3 LambdaRestApi constructs with explicit routes)

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: POST endpoints use `PutItemCommand` without idempotency keys. Product creation (`src/product/index.js`) generates a uuid but does not use conditional puts. Basket creation (`src/basket/index.js`) uses `PutItemCommand` without conditions — overwrites existing baskets. Checkout (`src/basket/index.js`) has no idempotency protection — a duplicate checkout could publish duplicate EventBridge events.
- **Implication**: For the current read-only agent scope, idempotency is not a concern. However, if the agent scope expands to write-enabled (e.g., processing returns), this becomes a BLOCKER. The lack of idempotency means duplicate writes would create duplicate orders.
- **Recommendation**: Before expanding to write-enabled scope, add idempotency key support to POST endpoints using DynamoDB conditional writes or an idempotency middleware.
- **Evidence**: `src/product/index.js` (PutItemCommand without conditions), `src/basket/index.js` (PutItemCommand without conditions, checkout without idempotency)

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: All API responses are JSON. Every Lambda handler returns `JSON.stringify({ message, body })` for success and `JSON.stringify({ message, errorMsg, errorStack })` for errors. API Gateway default content-type is `application/json`.
- **Implication**: JSON responses are well-suited for agent consumption. LLMs can parse JSON natively. No binary or complex XML parsing required.
- **Recommendation**: No action needed. JSON is the preferred format for agent tool responses.
- **Evidence**: `src/product/index.js` (JSON.stringify), `src/basket/index.js` (JSON.stringify), `src/ordering/index.js` (JSON.stringify)

### API-Q7: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: EventBridge integration exists for the checkout flow. `src/basket/index.js` publishes events with source `com.swn.basket.checkoutbasket` and detail type `CheckoutBasket` to the `SwnEventBus`. The event is routed via a rule in `lib/eventbus.ts` to the SQS OrderQueue, which triggers the ordering Lambda. However, other state changes (product CRUD, basket create/delete) do not emit events.
- **Implication**: Event-driven patterns exist for the checkout flow, which is the most complex state change. This could support proactive agent patterns (e.g., agent reacts to new order events). Product and basket CRUD events are not emitted, limiting reactive agent use cases for those domains.
- **Recommendation**: Consider adding EventBridge events for product and basket state changes if reactive agent use cases emerge (e.g., inventory monitoring, basket abandonment detection).
- **Evidence**: `src/basket/index.js` (publishCheckoutBasketEvent), `lib/eventbus.ts` (SwnEventBus, CheckoutBasketRule)

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No API Gateway usage plans, throttle settings, or WAF rules exist. No rate limiting middleware in Lambda handlers. No `X-RateLimit-Remaining` or `Retry-After` headers are returned. Default API Gateway account limits apply but are undocumented.
- **Implication**: Agents calling these APIs at machine speed have no visibility into rate limits. They cannot self-throttle based on remaining quota. If rate limiting is added (STATE-Q5), corresponding headers should be added to API responses.
- **Recommendation**: When implementing rate limiting (STATE-Q5), also return `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `Retry-After` headers in API responses so agents can self-throttle.
- **Evidence**: `lib/apigateway.ts` (no usage plans), `src/product/index.js` (no rate limit headers)

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No optimistic locking, no version fields, no ETags, no `If-Match` headers, no DynamoDB conditional writes (`ConditionExpression`). `PutItemCommand` is used without conditions in all handlers — existing items are overwritten silently. No conflict detection or resolution logic.
- **Implication**: For the current read-only agent scope, concurrency controls are not a concern. If the scope expands to write-enabled, concurrent agent writes would overwrite each other silently, risking data loss.
- **Recommendation**: Before expanding to write-enabled scope, add version fields to DynamoDB items and use DynamoDB conditional writes (`ConditionExpression: 'attribute_not_exists(id) OR version = :expectedVersion'`).
- **Evidence**: `src/product/index.js` (PutItemCommand without conditions), `src/basket/index.js` (PutItemCommand without conditions)

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits exist. No max-records-per-operation limits. `ScanCommand` in all services returns all items without `Limit` parameters. No per-identity action quotas.
- **Implication**: For read-only scope, the blast radius concern is limited to read amplification (unbounded scans consuming DynamoDB read capacity). If scope expands to write-enabled, there are no guardrails to prevent an agent from deleting all products or checking out all baskets in a loop.
- **Recommendation**: Add `Limit` parameters to all `ScanCommand` operations. Before write-enabled scope expansion, implement per-identity action quotas.
- **Evidence**: `src/product/index.js` (ScanCommand without Limit), `src/basket/index.js` (ScanCommand without Limit), `src/ordering/index.js` (ScanCommand without Limit)

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No draft or pending status fields in any DynamoDB table schema. Product table has `id/name/description/imageFile/price/category` — no status field. Basket table has `userName/items` — no status. Order table has `userName/orderDate` plus checkout fields — no draft status. All creates are immediate and final.
- **Implication**: For read-only scope, draft states are not needed. If scope expands to write-enabled, the absence of draft states means agent-initiated writes would be immediately committed with no human review opportunity.
- **Recommendation**: Before write-enabled scope expansion, add a `status` field to the order table (e.g., `draft`, `pending_approval`, `confirmed`) to support human-in-the-loop approval for agent-initiated orders.
- **Evidence**: `lib/database.ts` (table schemas in comments), `src/product/index.js` (no status handling), `src/basket/index.js` (no status handling)

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No approval endpoints, no configurable operation-level flags, no Step Functions human approval tasks (`waitForTaskToken`), no two-step confirmation patterns in any handler or CDK construct.
- **Implication**: For read-only scope, approval gates are not needed. If write-enabled operations are added (e.g., processing returns, updating inventory), the absence of approval gates means all agent-initiated operations execute immediately without human oversight.
- **Recommendation**: Before write-enabled scope expansion, implement configurable approval gates using Step Functions with `waitForTaskToken` for high-risk operations (e.g., order cancellation, bulk updates).
- **Evidence**: `lib/aws-microservices-stack.ts` (no Step Functions), `src/basket/index.js` (no approval logic)

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality dashboards, profiling reports, or completeness metrics exist. No null rate monitoring. No duplicate detection logic. No data freshness SLAs. Input validation is minimal — only `userName` null check in checkout (`src/basket/index.js`). Product creation accepts any JSON body without field validation.
- **Implication**: Agents acting on incomplete or invalid data will propagate errors. For order status lookups (the primary use case), data quality depends on the checkout flow populating all required fields. No mechanism exists to alert on data quality degradation.
- **Recommendation**: Add input validation to all write endpoints. Implement data quality monitoring for the order table (null rates for required fields, duplicate detection).
- **Evidence**: `src/basket/index.js` (minimal validation — userName check only), `src/product/index.js` (no input validation)

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Field names across all services are human-readable and semantically meaningful: `userName`, `orderDate`, `totalPrice`, `firstName`, `lastName`, `email`, `address`, `productId`, `productName`, `quantity`, `color`, `price`, `category`, `imageFile`, `paymentMethod`, `cardInfo`. No legacy abbreviations or cryptic codes.
- **Implication**: Positive finding. LLM-based agents can reason about these fields without a data dictionary. Agent tool descriptions will be self-documenting.
- **Recommendation**: No action needed. Maintain the current naming convention for new fields.
- **Evidence**: `src/product/index.js` (field names), `src/basket/index.js` (checkout fields), `src/ordering/index.js` (order fields), `lib/database.ts` (schema comments)

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No data catalog (no AWS Glue Data Catalog, no Collibra, no DataHub). No formal metadata files. Schema information exists only in CDK code comments in `lib/database.ts` (e.g., `product : PK: id -- name - description - imageFile - price - category`).
- **Implication**: Building agent tools requires reading CDK code and Lambda handlers to understand data schemas. No centralized discovery mechanism exists for what data the system holds.
- **Recommendation**: Consider creating a lightweight data dictionary (markdown file) documenting each table's schema, field types, and relationships. For portfolio-level discovery, consider AWS Glue Data Catalog.
- **Evidence**: `lib/database.ts` (schema comments as the only metadata)

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No custom CloudWatch metrics. No `put_metric_data` calls in any Lambda handler. No business KPI dashboards or alarms (e.g., checkout success rate, order volume, average basket value).
- **Implication**: When agents consume these services, there will be no business-level signal for whether agent interactions produce good outcomes (e.g., is the agent-initiated return flow resulting in correct order updates?).
- **Recommendation**: Add custom CloudWatch metrics for key business events: checkout completions, order creation success/failure, product query volume. These metrics become the primary signal for agent effectiveness monitoring.
- **Evidence**: `src/product/index.js` (no metric publishing), `src/basket/index.js` (no metric publishing), `src/ordering/index.js` (no metric publishing)

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO (Pass)
- **Finding**: Three REST APIs exist via API Gateway (`lib/apigateway.ts`): Product Service (GET/POST/PUT/DELETE /product, GET/PUT/DELETE /product/{id}), Basket Service (GET/POST /basket, GET/DELETE /basket/{userName}, POST /basket/checkout), Order Service (GET /order, GET /order/{userName}). All implemented as `LambdaRestApi` with explicit resource/method definitions. No direct database access or file-based integration for external consumers.
- **Gap**: APIs exist — no gap. Documentation is limited to code comments (see API-Q2 for machine-readable spec gap).
- **Recommendation**: Formalize the API surface in an OpenAPI specification.
- **Evidence**: `lib/apigateway.ts`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, Swagger, GraphQL schema, or Smithy specification files exist in the repository. API structure is defined only in `lib/apigateway.ts` (CDK code) and Lambda handler switch statements.
- **Gap**: No machine-readable spec. Agent tool generation requires manual authoring from code.
- **Recommendation**: Generate an OpenAPI 3.0 specification. Use CDK API Gateway export or write manually.
- **Evidence**: No spec files found in repository scan.

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: All handlers return `{ statusCode: 500, body: JSON.stringify({ message, errorMsg, errorStack }) }` for errors. Only HTTP 200 and 500 are used. No structured error codes, no retryable boolean, no error categories. Stack traces are exposed in responses.
- **Gap**: Agents cannot distinguish retriable from terminal errors. Stack traces leak implementation details.
- **Recommendation**: Implement structured error responses with error codes, appropriate HTTP status codes (400, 404, 429, 500), and retryable classification. Remove stack traces.
- **Evidence**: `src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js` (catch blocks)

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: POST endpoints use `PutItemCommand` without idempotency keys or conditional writes. Product creation uses uuid but no conditional put. Checkout has no idempotency protection.
- **Gap**: No idempotency for write operations. Informational for read-only scope.
- **Recommendation**: Add idempotency key support before write-enabled scope expansion.
- **Evidence**: `src/product/index.js` (PutItemCommand), `src/basket/index.js` (PutItemCommand, checkoutBasket)

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: All responses are JSON via `JSON.stringify`. API Gateway defaults to `application/json` content-type. No binary, XML, or Protobuf formats used.
- **Gap**: No gap. JSON is optimal for agent consumption.
- **Recommendation**: No action needed.
- **Evidence**: `src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js`

#### API-Q6: Asynchronous Operation Support
- **Severity**: RISK-QUALITY
- **Finding**: Checkout flow is async (EventBridge → SQS → ordering Lambda) but `POST /basket/checkout` returns 200 synchronously with no job ID, no polling endpoint, no webhook callback. Caller cannot track order creation status.
- **Gap**: No async tracking mechanism for the checkout operation.
- **Recommendation**: Return a correlation ID in the checkout response. Add a status polling endpoint.
- **Evidence**: `src/basket/index.js` (checkoutBasket), `lib/eventbus.ts`, `lib/queue.ts`

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: EventBridge events emitted for checkout flow (`com.swn.basket.checkoutbasket` → `CheckoutBasket`). SQS queue routes to ordering service. Product CRUD and basket CRUD do not emit events.
- **Gap**: Events exist for checkout only. Other state changes are not observable via events.
- **Recommendation**: Consider EventBridge events for product and basket state changes.
- **Evidence**: `src/basket/index.js` (publishCheckoutBasketEvent), `lib/eventbus.ts`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No API Gateway usage plans, throttle settings, WAF rules, or rate limit headers (`X-RateLimit-Remaining`, `Retry-After`). Default API Gateway account limits apply undocumented.
- **Gap**: No rate limit documentation or headers for agent self-throttling.
- **Recommendation**: Add rate limit headers when implementing STATE-Q5 rate limiting.
- **Evidence**: `lib/apigateway.ts` (no usage plans)

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: API Gateway has no authorizers. All three `LambdaRestApi` constructs in `lib/apigateway.ts` have no `defaultMethodOptions`, no API key requirements, no Cognito/IAM authorization. All endpoints are publicly accessible without identity.
- **Gap**: No authentication mechanism exists. Any caller can invoke any endpoint.
- **Recommendation**: Add IAM authorization or Cognito app client authentication to API Gateway. Create per-agent IAM roles.
- **Evidence**: `lib/apigateway.ts`, `lib/microservice.ts`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: `lib/microservice.ts` grants `grantReadWriteData` on DynamoDB tables to all Lambda functions. No scoped agent-specific roles. No resource-level restrictions beyond table-level.
- **Gap**: No ability to scope agent access to read-only. All Lambda functions have full read/write access.
- **Recommendation**: Create separate IAM roles for read-only and read-write access. Use API Gateway resource policies for method-level restriction.
- **Evidence**: `lib/microservice.ts` (grantReadWriteData)

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: No RBAC, ABAC, or action-level authorization in any handler. No middleware checks. API Gateway has no method-level authorization. All HTTP methods open to all callers.
- **Gap**: No action-level authorization. Any caller can DELETE products or POST orders.
- **Recommendation**: Add IAM authorization with per-method policies. Restrict agent roles to GET methods only for read-only scope.
- **Evidence**: `lib/apigateway.ts`, `src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: RISK-QUALITY
- **Finding**: No JWT parsing, OAuth2 integration, token exchange, or user context headers. Lambda handlers receive raw API Gateway events with no authenticated principal. `userName` path parameter is unauthenticated business data.
- **Gap**: No identity propagation. System cannot distinguish agent-as-self from agent-on-behalf-of-user. Any caller can query any user's data.
- **Recommendation**: Implement Cognito or IAM authorization with identity propagation. Map authenticated principal to authorized userName values.
- **Evidence**: `lib/apigateway.ts`, `src/basket/index.js`, `src/ordering/index.js`

#### AUTH-Q5: Credential Management
- **Severity**: RISK-QUALITY
- **Finding**: No hardcoded credentials found. Environment variables contain non-sensitive values only (table names, event bus names). Lambda uses IAM execution roles. No Secrets Manager or Vault integration, but no secrets currently needed.
- **Gap**: No secrets management infrastructure. Acceptable for current IAM-role-based architecture but no pattern for future credentials.
- **Recommendation**: Establish Secrets Manager integration when adding authentication credentials (AUTH-Q1).
- **Evidence**: `lib/microservice.ts` (environment variables), `src/product/ddbClient.js` (implicit credentials)

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No CloudTrail configuration. No audit logging. Lambda functions use `console.log` only. No immutable log storage. No principal attribution (no auth exists).
- **Gap**: Cannot trace who made what call. No immutable audit trail.
- **Recommendation**: Add CloudTrail configuration. Configure API Gateway access logging. Set up immutable log storage.
- **Evidence**: `lib/aws-microservices-stack.ts`, `lib/apigateway.ts`, `src/product/index.js`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: No identity management system. No API key management, no IAM role deactivation, no Cognito. No identity to suspend since no authentication exists (AUTH-Q1).
- **Gap**: No mechanism to suspend or revoke agent identities.
- **Recommendation**: Ensure the identity mechanism chosen for AUTH-Q1 supports individual suspension.
- **Evidence**: `lib/apigateway.ts`, `lib/aws-microservices-stack.ts`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Checkout flow in `src/basket/index.js` performs 3 steps: (1) getBasket, (2) publishCheckoutBasketEvent to EventBridge, (3) deleteBasket from DynamoDB. No compensation if ordering Lambda fails after basket is deleted. No saga pattern, no Step Functions, no undo endpoints.
- **Gap**: No compensation or rollback for multi-step checkout. Partial failures create inconsistent state.
- **Recommendation**: Refactor checkout to use Step Functions with compensation. Add DLQ to SQS OrderQueue.
- **Evidence**: `src/basket/index.js` (checkoutBasket), `lib/queue.ts` (no DLQ)

#### STATE-Q2: Queryable Current State
- **Severity**: RISK-QUALITY
- **Finding**: GET endpoints exist for all entities: GET /product, GET /product/{id}, GET /basket/{userName}, GET /order, GET /order/{userName}. State is queryable via REST API.
- **Gap**: Positive finding. Minor gap: order queries require both userName and orderDate.
- **Recommendation**: Consider more flexible query parameters (date range, status filters).
- **Evidence**: `lib/apigateway.ts`, `src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js`

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No optimistic locking, no version fields, no ETags, no DynamoDB conditional writes. PutItemCommand overwrites existing items silently.
- **Gap**: No concurrency controls. Informational for read-only scope.
- **Recommendation**: Add version fields and conditional writes before write-enabled scope expansion.
- **Evidence**: `src/product/index.js`, `src/basket/index.js`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: No circuit breaker libraries. No retry logic. DynamoDB and EventBridge clients created with default configuration — no timeouts, no retries. Basket checkout calls EventBridge without circuit breakers.
- **Gap**: No resilience patterns. Downstream failures cascade without protection.
- **Recommendation**: Configure SDK retry strategies. Add Lambda timeout settings. Implement circuit breaker for EventBridge call.
- **Evidence**: `src/product/ddbClient.js`, `src/basket/ddbClient.js`, `src/basket/eventBridgeClient.js`, `lib/microservice.ts`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No API Gateway throttling in `lib/apigateway.ts`. No usage plans, WAF rules, or application-level rate limiting. Default API Gateway account limits (10,000 rps) apply but are not configured per consumer.
- **Gap**: No explicit rate limiting. Runaway agent loops could overwhelm services.
- **Recommendation**: Add API Gateway usage plans with per-key throttle limits. Configure Lambda reserved concurrency.
- **Evidence**: `lib/apigateway.ts`, `lib/microservice.ts`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits. ScanCommand returns all items without Limit parameters. No per-identity action quotas.
- **Gap**: No transaction limits. Informational for read-only scope.
- **Recommendation**: Add Limit parameters to ScanCommand operations. Implement per-identity quotas before write-enabled expansion.
- **Evidence**: `src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: RISK-QUALITY
- **Finding**: DynamoDB uses PAY_PER_REQUEST (auto-scaling). Lambda has no reserved or provisioned concurrency. SQS OrderQueue has default settings (30s visibility, batch 1). No load testing evidence.
- **Gap**: DynamoDB scales well, but Lambda concurrency is unbounded. No load testing for agent traffic patterns.
- **Recommendation**: Configure Lambda reserved concurrency. Conduct load testing simulating agent traffic.
- **Evidence**: `lib/database.ts` (PAY_PER_REQUEST), `lib/microservice.ts` (no concurrency), `lib/queue.ts`

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No draft or pending status fields in any DynamoDB table schema. Product: id/name/description/imageFile/price/category — no status. Basket: userName/items — no status. Order: userName/orderDate + checkout fields — no draft status. All creates are immediate.
- **Gap**: No draft/pending state capability. Informational for read-only scope.
- **Recommendation**: Add status field to order table before write-enabled expansion.
- **Evidence**: `lib/database.ts`, `src/product/index.js`, `src/basket/index.js`

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No approval endpoints, no configurable operation-level flags, no Step Functions human approval tasks, no two-step confirmation patterns.
- **Gap**: No approval gate capability. Informational for read-only scope.
- **Recommendation**: Implement Step Functions with waitForTaskToken before write-enabled expansion.
- **Evidence**: `lib/aws-microservices-stack.ts`, `src/basket/index.js`

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: No separate environment configurations. `bin/aws-microservices.ts` has commented-out env config. Single stack definition. No docker-compose, no seed data scripts, no synthetic data generators.
- **Gap**: No sandbox or staging environment for agent testing.
- **Recommendation**: Create environment-specific CDK stack configurations. Add seed data scripts.
- **Evidence**: `bin/aws-microservices.ts`, `lib/aws-microservices-stack.ts`

<!-- TODO: DETAILED_FINDINGS_DATA -->

<!-- TODO: DETAILED_FINDINGS_DISC -->

<!-- TODO: DETAILED_FINDINGS_OBS -->

<!-- TODO: DETAILED_FINDINGS_ENG -->

<!-- TODO: EVIDENCE_INDEX -->
