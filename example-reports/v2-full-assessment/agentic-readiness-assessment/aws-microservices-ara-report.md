# Agentic Readiness Assessment Report

**Target**: ./services/aws-microservices
**Date**: 2026-04-15
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Agent Scope**: write-enabled
**Priority**: P0
**Tags**: microservices, serverless, event-driven
**Context**: Event-driven serverless microservices (product, basket, ordering) with Lambda, DynamoDB, EventBridge, SQS. The agent will invoke these as tools for order status lookups and return processing.

---

## Readiness Profile: Not Agent-Integrable

**BLOCKERs**: 7 | **RISKs**: 32 | **INFOs**: 10

Exclude from agent toolset or plan major remediation before re-evaluation. With 7 unresolved BLOCKERs spanning authentication, data protection, transactional integrity, and network security, this system cannot safely support autonomous agent integration — including scoped pilots. A structured remediation program (estimated 90–180 days) is required before re-assessment.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 7 |
| RISK | 32 |
| INFO | 10 |
| N/A | 0 |
| **Total** | **49** |

**Questions Evaluated**: 49
**Questions N/A (repo_type: application)**: 0

---

## BLOCKERs — Must Resolve Before Agent Deployment

**Remediation Prioritization:** Resolve AUTH-Q1 (machine identity) first — without knowing who is calling, no other security control can function. Then address DATA-Q1 (data classification) and AUTH-Q7 (audit logging) to establish the compliance foundation. API-Q4 and STATE-Q1 can be deferred if the agent is initially scoped to read-only operations while write safety is remediated. ENG-Q6 and DATA-Q2 should be addressed in parallel with infrastructure hardening.

---

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: All three API Gateways (productApi, basketApi, orderApi) are created via `LambdaRestApi` in `lib/apigateway.ts` with no authorizer configured. No Cognito user pool, no API key requirement, no Lambda authorizer, no IAM authorization. The APIs are completely open and unauthenticated. Any caller on the internet can invoke any endpoint. No principal attribution exists in any logging — `console.log` captures the event payload but not the identity of the caller.
- **Gap**: No authentication mechanism exists. No machine identity support. No principal attribution in audit trail.
- **Remediation**:
  - **Immediate**: Add API Gateway API key requirements to all three APIs using `apiKeyRequired: true` on each method, create a usage plan, and issue separate API keys per agent identity. This provides immediate caller identification and the ability to revoke individual agents.
  - **Target State**: Implement OAuth 2.0 client credentials flow using Amazon Cognito with app clients per agent identity. Each agent call carries a JWT token with principal claims logged in CloudWatch. API Gateway authorizer validates tokens and passes principal context to Lambda.
  - **Estimated Effort**: Medium (2–4 weeks for API key; 4–8 weeks for Cognito OAuth)
  - **Dependencies**: AUTH-Q7 (audit logging requires principal identity), AUTH-Q8 (suspension requires identity mechanism)
- **Evidence**: `lib/apigateway.ts` (lines 32–39, 57–64, 82–89 — `LambdaRestApi` constructors with no auth config)

---

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: BLOCKER
- **Conditional**: agent_scope is "write-enabled" — evaluated as BLOCKER
- **Finding**: `POST /product` in `src/product/index.js` generates a new UUID (`uuidv4()`) for every call — no idempotency key support; retries create duplicate products. `POST /basket` in `src/basket/index.js` uses `PutItemCommand` keyed on `userName` — naturally idempotent (upsert). `POST /basket/checkout` in `src/basket/index.js` has no idempotency protection — a retry publishes duplicate EventBridge events via `PutEventsCommand`, creating duplicate orders. `PUT /product/{id}` is naturally idempotent. `DELETE` operations are idempotent by nature.
- **Gap**: Checkout flow (`POST /basket/checkout`) and product creation (`POST /product`) lack idempotency keys. Agent retries or LLM non-determinism will create duplicate orders and duplicate products.
- **Remediation**:
  - **Immediate**: Add an idempotency key header (`X-Idempotency-Key`) to `POST /basket/checkout`. Use DynamoDB conditional writes with the idempotency key to prevent duplicate event publication. Consider AWS Lambda Powertools idempotency utility.
  - **Target State**: All write endpoints accept and enforce idempotency keys. Idempotency records stored in DynamoDB with TTL. Product creation uses client-supplied idempotency key instead of server-generated UUID.
  - **Estimated Effort**: Medium (2–4 weeks)
  - **Dependencies**: None
- **Evidence**: `src/product/index.js` (createProduct function — `uuidv4()` generates new id per call), `src/basket/index.js` (checkoutBasket function — no idempotency check before `PutEventsCommand`)

---

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: BLOCKER
- **Conditional**: agent_scope is "write-enabled" — evaluated as BLOCKER
- **Finding**: The checkout flow in `src/basket/index.js` (`checkoutBasket` function) executes 4 sequential steps: (1) `getBasket` — read basket from DynamoDB, (2) `prepareOrderPayload` — calculate total price and merge data, (3) `publishCheckoutBasketEvent` — publish to EventBridge via `PutEventsCommand`, (4) `deleteBasket` — remove basket from DynamoDB. If step 3 succeeds but step 4 fails, the order event is published but the basket is not deleted (ghost basket). If EventBridge delivers to SQS but the ordering Lambda fails (`src/ordering/index.js` `createOrder`), there is no compensation — the event is consumed, the order is partially created or not created, and no rollback occurs. No saga pattern, no undo endpoints, no Step Functions with error handling.
- **Gap**: Multi-step checkout flow has no compensation or rollback logic. Partial failures leave the system in inconsistent state.
- **Remediation**:
  - **Immediate**: Add a dead-letter queue (DLQ) to the SQS `OrderQueue` to capture failed order creation events. Implement retry logic in the ordering Lambda. Add error handling in `checkoutBasket` that restores the basket if event publication fails.
  - **Target State**: Replace the inline checkout flow with AWS Step Functions implementing a saga pattern: (1) reserve basket, (2) publish order event, (3) confirm order creation, (4) delete basket — with compensating actions for each step on failure. DLQ monitoring with alerts.
  - **Estimated Effort**: High (4–8 weeks)
  - **Dependencies**: OBS-Q2 (alerting needed to detect compensation failures)
- **Evidence**: `src/basket/index.js` (checkoutBasket function — sequential steps with no error compensation), `src/ordering/index.js` (createOrder — no rollback on failure), `lib/queue.ts` (OrderQueue with no DLQ configured)

---

### AUTH-Q7: Immutable Audit Logging ⚡

- **Severity**: BLOCKER
- **Conditional**: agent_scope is "write-enabled" — evaluated as BLOCKER
- **Finding**: No CloudTrail configuration in any CDK construct. No CloudWatch log retention policies configured on any Lambda function. Lambda functions log full event payloads via `console.log("request:", JSON.stringify(event, undefined, 2))` — unstructured, not immutable, and not protected from deletion. No S3 bucket with object lock for log storage. No audit trail identifying which principal made which write operation (because no authentication exists — see AUTH-Q1). Logs include sensitive data (PII in checkout payloads) without redaction.
- **Gap**: No immutable audit logging. No principal attribution on write operations. No log retention policy. No tamper-evident log storage.
- **Remediation**:
  - **Immediate**: Enable CloudTrail for API Gateway and Lambda in the CDK stack. Set CloudWatch log retention to at least 365 days on all Lambda log groups. Enable CloudTrail log file validation.
  - **Target State**: CloudTrail enabled with log file validation and S3 bucket with object lock (WORM). Structured JSON logging with principal identity, action, resource, and timestamp fields. CloudWatch Logs Insights queries for audit trail reconstruction. PII redacted from logs (see DATA-Q7).
  - **Estimated Effort**: Medium (2–4 weeks)
  - **Dependencies**: AUTH-Q1 (principal identity must exist before it can be logged)
- **Evidence**: `lib/microservice.ts` (no tracing or logging configuration in NodejsFunctionProps), `src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js` (all use `console.log` with full event payloads)

---

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: The order DynamoDB table stores PII fields: `firstName`, `lastName`, `email`, `address`, `paymentMethod`, `cardInfo` — as documented in `lib/database.ts` comments (`order : PK: userName - SK: orderDate -- totalPrice - firstName - lastName - email - address - paymentMethod - cardInfo`) and confirmed in the checkout flow (`src/basket/index.js` `prepareOrderPayload` merges all basket and user data into the order record). No data classification tags on any of the three DynamoDB tables in `lib/database.ts`. No field-level encryption. No column-level access controls. No Macie integration. The `cardInfo` field suggests payment card data is stored in plain text — potential PCI DSS violation.
- **Gap**: Sensitive data (PII, payment card info) is stored unclassified, untagged, and without field-level protection. An agent with read access to the order table retrieves all PII including payment information.
- **Remediation**:
  - **Immediate**: Classify the order table as containing PII and PCI data. Add resource tags to DynamoDB tables in CDK (`Tags.of(orderTable).add('DataClassification', 'PII-PCI')`). Remove `cardInfo` storage or tokenize it via a payment processor. Enable DynamoDB encryption with customer-managed KMS key.
  - **Target State**: All DynamoDB tables tagged with data classification. Sensitive fields (email, address, cardInfo) encrypted at the field level using KMS. Agent access scoped to exclude PII fields unless explicitly authorized. Macie enabled for ongoing PII detection.
  - **Estimated Effort**: High (4–8 weeks — payment card remediation may require architecture changes)
  - **Dependencies**: AUTH-Q2 (scoped permissions needed to restrict field-level access)
- **Evidence**: `lib/database.ts` (order table schema comment listing PII fields, no encryption config, no tags), `src/basket/index.js` (prepareOrderPayload — `Object.assign(checkoutRequest, basket)` copies all fields into order payload)

---

### DATA-Q2: Data Residency and Sovereignty ⚡

- **Severity**: BLOCKER
- **Conditional**: agent_scope is "write-enabled" — evaluated as BLOCKER
- **Finding**: The CDK stack in `bin/aws-microservices.ts` has the `env` property commented out — the stack is "environment-agnostic" per the inline comment. No region is specified, meaning the stack deploys to whatever region the CLI is configured for. No data residency requirements are documented anywhere in the repository. The order table contains PII (email, address, payment info) that may be subject to GDPR, LGPD, or other data residency regulations. A write-enabled agent sending this PII to an LLM endpoint in a different region or jurisdiction could create a legal violation.
- **Gap**: No explicit region pinning. No data residency policy. No documentation of applicable regulations for the PII stored. No controls preventing cross-region data transmission to LLM providers.
- **Remediation**:
  - **Immediate**: Uncomment and set the `env` property in `bin/aws-microservices.ts` to pin the stack to a specific region. Document which data residency regulations apply to the order data (GDPR if EU customers, LGPD if Brazilian customers, etc.).
  - **Target State**: Stack deployed to a specific region with documented data residency compliance. Agent integration architecture documented showing data flow boundaries — PII does not leave the designated region. LLM calls use Amazon Bedrock in the same region or use data anonymization before cross-region transmission.
  - **Estimated Effort**: Low (1–2 weeks for region pinning; Medium for full compliance documentation)
  - **Dependencies**: DATA-Q1 (data classification determines which fields have residency requirements)
- **Evidence**: `bin/aws-microservices.ts` (env commented out — `// env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: process.env.CDK_DEFAULT_REGION }`), `lib/database.ts` (order table with PII fields)

---

### ENG-Q6: Cross-Origin and Network Policies

- **Severity**: BLOCKER
- **Finding**: All three API Gateways in `lib/apigateway.ts` are created via `LambdaRestApi` without `defaultCorsPreflightOptions` — no CORS configuration exists. Lambda functions in `lib/microservice.ts` are not VPC-attached — no security groups. No WAF rules in any CDK construct. No API Gateway resource policies restricting access by IP, VPC endpoint, or AWS account. No network policies. The APIs are publicly accessible on the internet with no network-level restrictions. For agent integration, this means any entity can call these APIs, and there is no mechanism to restrict access to authorized agent infrastructure.
- **Gap**: No CORS policies, no network security controls, no API Gateway resource policies, no WAF. APIs are completely open at the network level.
- **Remediation**:
  - **Immediate**: Add API Gateway resource policies restricting access to known IP ranges or VPC endpoints. Add `defaultCorsPreflightOptions` to each `LambdaRestApi` construct. Deploy AWS WAF with rate limiting rules on each API Gateway.
  - **Target State**: API Gateways accessible only via VPC endpoints (private APIs) or restricted by resource policies to known CIDR ranges. WAF with rate limiting and IP reputation filtering. CORS configured to allow only authorized origins. Lambda functions deployed in VPC with security groups for backend access control.
  - **Estimated Effort**: Medium (2–4 weeks)
  - **Dependencies**: STATE-Q5 (rate limiting overlaps with WAF configuration)
- **Evidence**: `lib/apigateway.ts` (three `LambdaRestApi` constructors — no CORS, no resource policies), `lib/microservice.ts` (NodejsFunctionProps — no VPC config, no security groups)

## RISKs — Proceed with Compensating Controls

### API-Q2: Machine-Readable API Specification

- **Severity**: RISK
- **Finding**: No OpenAPI, Swagger, AsyncAPI, GraphQL schema, or Smithy files exist anywhere in the repository. The API surface is defined only in CDK code (`lib/apigateway.ts`) via `LambdaRestApi` constructs and in Lambda handler switch statements. No machine-readable specification is available for agent tool generation.
- **Gap**: No machine-readable API specification. Agent tool definitions must be manually authored by inspecting CDK code and Lambda handlers.
- **Compensating Controls**:
  - Manually author agent tool definitions from the CDK route definitions in `lib/apigateway.ts` and Lambda handler code
  - Use API Gateway's auto-generated export feature (`aws apigateway get-export`) to extract an OpenAPI spec from the deployed API
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Generate OpenAPI specifications from the deployed API Gateways using the AWS CLI export feature. Add these specs to the repository and set up a process to regenerate them on each deployment.
- **Evidence**: `lib/apigateway.ts` (API routes defined in code only), absence of any `openapi.yaml`, `swagger.json`, or `.graphql` files in the repository

### API-Q3: Structured Error Responses

- **Severity**: RISK
- **Finding**: All three Lambda handlers (`src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js`) return error responses with `statusCode: 500` and a JSON body containing `message`, `errorMsg`, and `errorStack`. No structured error codes (e.g., `PRODUCT_NOT_FOUND`, `BASKET_EMPTY`). No retryable boolean or error category. Error stack traces are leaked in responses — a security concern and useless to agents.
- **Gap**: No structured error codes. No retryable signal. Stack traces leaked in error responses. Agents cannot distinguish retriable errors from terminal errors.
- **Compensating Controls**:
  - Agent wrapper layer parses error messages to infer retryability (fragile but functional for pilot)
  - Limit agent to read operations where error impact is lower
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement a standardized error response format across all handlers with error codes, retryable boolean, and error category. Remove stack traces from production responses.
- **Evidence**: `src/product/index.js` (catch block — `errorStack: e.stack`), `src/basket/index.js` (same pattern), `src/ordering/index.js` (same pattern)

### API-Q5: API Versioning and Deprecation

- **Severity**: RISK
- **Finding**: No API versioning in URL patterns (routes are `/product`, `/basket`, `/order` — no `/v1/` prefix). No `Accept-Version` headers. No changelog. API Gateway stage name is `prod` (default). No deprecation policy or downstream notification mechanism.
- **Gap**: No API versioning. Breaking changes to API contracts will silently break agent tool definitions.
- **Compensating Controls**:
  - Pin agent tool definitions to current API behavior and monitor for changes manually
  - Use API Gateway stage deployment to create a stable snapshot
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `/v1/` prefix to all API routes. Implement a changelog. Configure API Gateway deployment stages for version management.
- **Evidence**: `lib/apigateway.ts` (routes without version prefix), absence of changelog or versioning documentation

### API-Q7: Asynchronous Operation Support

- **Severity**: RISK
- **Finding**: The checkout flow uses an async pattern: `POST /basket/checkout` → EventBridge → SQS → Ordering Lambda. However, there is no job status polling endpoint or webhook callback. The caller receives a 200 response from the basket checkout but has no way to verify that the order was actually created in the ordering service. The order can only be queried via `GET /order/{userName}?orderDate=timestamp`, which requires knowing the exact `orderDate` — a value set server-side in the ordering Lambda.
- **Gap**: Async checkout flow has no status tracking. Agents cannot verify order completion without guessing the orderDate timestamp.
- **Compensating Controls**:
  - Agent polls `GET /order/{userName}` (all orders) after checkout and checks for new entries
  - Accept fire-and-forget for pilot scope with manual verification
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a `GET /order/{userName}/latest` endpoint or return an order reference ID from the checkout response. Implement a job status endpoint for async operations.
- **Evidence**: `src/basket/index.js` (checkoutBasket — no return value after event publication), `src/ordering/index.js` (getOrder requires exact orderDate)

### AUTH-Q2: Scoped Permissions (Least Privilege)

- **Severity**: RISK
- **Finding**: CDK grants in `lib/microservice.ts` use `table.grantReadWriteData(function)` for all three Lambda functions — creating DynamoDB IAM policies scoped to specific tables per function. `bus.grantPutEventsTo(basketFunction)` in `lib/eventbus.ts` is properly scoped to the basket function only. However, all grants are `ReadWrite` — no function has read-only grants even when it only needs read access (e.g., ordering Lambda only reads orders via API Gateway but has write permissions for SQS-triggered order creation on the same function).
- **Gap**: IAM grants are table-scoped but not action-scoped. All Lambda functions have ReadWrite access. No separate read-only vs write roles.
- **Compensating Controls**:
  - Current table-level isolation prevents cross-service data access (product Lambda cannot access order table)
  - Agent-level scoping can be enforced at the API Gateway layer when auth is added
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Split ordering Lambda into separate read (API Gateway) and write (SQS consumer) functions with different IAM roles. Use `grantReadData()` where only read access is needed.
- **Evidence**: `lib/microservice.ts` (`productTable.grantReadWriteData(productFunction)`, `basketTable.grantReadWriteData(basketFunction)`, `orderTable.grantReadWriteData(orderFunction)`)

### AUTH-Q3: Action-Level Authorization

- **Severity**: RISK
- **Finding**: No action-level authorization in any Lambda handler. No middleware checking permissions per HTTP method. API Gateway methods have no authorization type configured (default `NONE`). Any caller can execute any operation — `GET`, `POST`, `PUT`, `DELETE` — on any endpoint without restriction.
- **Gap**: No action-level authorization. An agent granted access to the product API can delete products as easily as it can list them.
- **Compensating Controls**:
  - Scope agent to specific HTTP methods at the API Gateway level using IAM execute-api permissions
  - Implement method-level API key restrictions
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add API Gateway authorizers with method-level policies. Implement RBAC or ABAC in Lambda middleware to enforce action-level permissions.
- **Evidence**: `lib/apigateway.ts` (all methods added without authorization), `src/product/index.js` (switch on httpMethod with no permission check)

### AUTH-Q4: Identity Propagation

- **Severity**: RISK
- **Finding**: No JWT parsing middleware. No OAuth2 flows. No token exchange patterns. No Cognito integration. No user context headers propagated between services. The `userName` field in basket and order operations is a request body parameter — not derived from an authenticated identity. An agent or any caller can specify any `userName` and access or modify any user's basket and orders.
- **Gap**: No identity propagation. User context is self-asserted in request body, not derived from authentication. This enables impersonation.
- **Compensating Controls**:
  - Validate userName against authenticated identity at API Gateway layer when auth is added
  - Limit agent pilot to non-user-specific operations (product catalog only)
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement Cognito authentication and derive userName from JWT claims, not from request body. Pass user context via API Gateway context variables to Lambda.
- **Evidence**: `src/basket/index.js` (getBasket uses `event.pathParameters.userName` — not derived from auth), `src/ordering/index.js` (getOrder uses `event.pathParameters.userName`)

### AUTH-Q5: Agent-as-Self vs Agent-on-Behalf-of-User

- **Severity**: RISK
- **Finding**: No authentication exists, so there is no distinction between agent-as-self and agent-on-behalf-of-user modes. No separate IAM roles or API keys for different access patterns. No audit log fields distinguishing the two modes. The system cannot determine whether a call is made by an agent autonomously or on behalf of a specific user.
- **Gap**: No mechanism to distinguish agent acting autonomously from agent acting on behalf of a user. Cannot enforce different permission boundaries for each mode.
- **Compensating Controls**:
  - Define agent convention to include `X-On-Behalf-Of` header for user-delegated calls (application must be updated to read it)
  - Limit pilot to agent-as-self operations only (product catalog queries)
- **Remediation Timeline**: 90–120 days
- **Recommendation**: After implementing authentication (AUTH-Q1), define separate OAuth scopes or API keys for agent-as-self vs agent-on-behalf-of-user. Log the mode in every request.
- **Evidence**: `lib/apigateway.ts` (no auth config), `src/basket/index.js` (no identity context in any handler)

### AUTH-Q6: Credential Management

- **Severity**: RISK
- **Finding**: No hardcoded credentials in source code. Lambda functions use IAM execution roles implicitly via CDK grants — no AWS access keys or secrets in code or environment variables. Environment variables in `lib/microservice.ts` contain only table names (`DYNAMODB_TABLE_NAME`), event configuration (`EVENT_SOURCE`, `EVENT_DETAILTYPE`, `EVENT_BUSNAME`), and key names (`PRIMARY_KEY`, `SORT_KEY`). No `.env` files committed. No Secrets Manager or Vault integration — but no secrets are currently needed beyond IAM roles. No credential rotation mechanism configured.
- **Gap**: Credential management is adequate for current scope (IAM roles only). However, no Secrets Manager integration exists for future secrets (e.g., API keys for agent auth, database credentials). No rotation mechanism.
- **Compensating Controls**:
  - Current IAM role-based credentials rotate automatically (no action needed for existing scope)
  - When API keys are added (AUTH-Q1), store them in Secrets Manager from the start
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Integrate AWS Secrets Manager for any new credentials (API keys, OAuth client secrets). Implement automatic rotation.
- **Evidence**: `lib/microservice.ts` (environment variables — table names and event config only, no secrets)

### AUTH-Q8: Agent Identity Suspension

- **Severity**: RISK
- **Finding**: No API key configuration on any API Gateway. No Cognito user pool. No mechanism to suspend or revoke access for a specific agent identity — because no authentication exists (AUTH-Q1). The only way to stop an agent from calling the APIs is to delete or disable the entire API Gateway, which affects all consumers including legitimate users.
- **Gap**: Cannot suspend individual agent identities. No granular access revocation. All-or-nothing access control.
- **Compensating Controls**:
  - Add IP-based blocking via API Gateway resource policy as an emergency kill switch
  - Implement WAF IP blacklisting for immediate agent suspension
- **Remediation Timeline**: 30–60 days (dependent on AUTH-Q1)
- **Recommendation**: After implementing API keys or Cognito (AUTH-Q1), configure per-agent key revocation capability. Add a usage plan with the ability to disable individual API keys.
- **Evidence**: `lib/apigateway.ts` (no API key or auth config on any API Gateway)

### STATE-Q2: Queryable Current State

- **Severity**: RISK
- **Finding**: GET endpoints exist for all three services: `GET /product`, `GET /product/{id}`, `GET /basket/{userName}`, `GET /order`, `GET /order/{userName}?orderDate=timestamp`. State is queryable before taking action. However, the order query at `GET /order/{userName}` requires an exact `orderDate` timestamp as a query parameter — this is a DynamoDB sort key used in a `KeyConditionExpression`. Without knowing the exact `orderDate`, an agent cannot query a specific order. `GET /order` returns all orders (unbounded scan), which is the only alternative.
- **Gap**: Order querying requires exact `orderDate` timestamp (sort key). No way to list all orders for a user without scanning the entire table or knowing exact timestamps.
- **Compensating Controls**:
  - Agent uses `GET /order` (all orders scan) and filters client-side — inefficient but functional for pilot with small datasets
  - Cache order timestamps from checkout responses for subsequent lookups
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a `GET /order/{userName}` endpoint that queries by partition key only (all orders for a user). Add pagination support. Consider adding a GSI for alternative query patterns.
- **Evidence**: `src/ordering/index.js` (getOrder — `KeyConditionExpression: "userName = :userName and orderDate = :orderDate"`)

### STATE-Q3: Concurrency Controls

- **Severity**: RISK
- **Finding**: No optimistic locking in any DynamoDB operation. No version fields. No ETags. No `If-Match` headers. `PutItemCommand` in `src/product/index.js` (createProduct) and `src/basket/index.js` (createBasket) silently overwrite existing items. `UpdateItemCommand` in `src/product/index.js` (updateProduct) has no condition expression to check for concurrent modifications. No DynamoDB conditional writes. No conflict resolution logic.
- **Gap**: No concurrency controls. Multiple agents modifying the same product or basket simultaneously will silently overwrite each other's changes (last-writer-wins).
- **Compensating Controls**:
  - Limit write operations to a single agent instance during pilot
  - Implement agent-side locking (external coordination) for write operations
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a `version` attribute to DynamoDB items. Use `ConditionExpression: "version = :expectedVersion"` on all write operations. Return 409 Conflict when the condition fails.
- **Evidence**: `src/product/index.js` (PutItemCommand and UpdateItemCommand — no condition expressions), `src/basket/index.js` (PutItemCommand — no condition expressions)

### STATE-Q4: Circuit Breakers and Resilience

- **Severity**: RISK
- **Finding**: No circuit breaker libraries imported in any Lambda function. No retry logic with exponential backoff. No timeout configurations on DynamoDB clients (`new DynamoDBClient()` with default config in all three `ddbClient.js` files) or EventBridge client (`new EventBridgeClient()` in `src/basket/eventBridgeClient.js`). No resilience patterns implemented. If DynamoDB or EventBridge is throttled or degraded, Lambda functions will fail without retry or graceful degradation.
- **Gap**: No circuit breakers, no retry logic, no timeout configuration on SDK clients. External dependency failures cascade directly to API consumers.
- **Compensating Controls**:
  - Lambda built-in retry for async invocations (SQS trigger has automatic retry via visibility timeout)
  - DynamoDB on-demand (PAY_PER_REQUEST) auto-scales to handle burst traffic
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure SDK client timeouts. Add retry logic with exponential backoff for DynamoDB and EventBridge calls. Consider AWS Lambda Powertools for structured error handling and retry patterns.
- **Evidence**: `src/product/ddbClient.js`, `src/basket/ddbClient.js`, `src/ordering/ddbClient.js` (all `new DynamoDBClient()` with no config), `src/basket/eventBridgeClient.js` (`new EventBridgeClient()` with no config)

### STATE-Q5: Rate Limiting and Throttling

- **Severity**: RISK
- **Finding**: No API Gateway throttling configuration in CDK. No usage plans defined. No WAF rate rules. No application-level rate limiting in Lambda handlers. Default API Gateway limits (10,000 RPS per region account-level) apply but are not explicitly configured or documented. DynamoDB uses `PAY_PER_REQUEST` billing which auto-scales but has account-level throughput limits. A runaway agent loop could generate thousands of requests per second.
- **Gap**: No explicit rate limiting. Default API Gateway limits are the only protection, shared across all consumers.
- **Compensating Controls**:
  - API Gateway default throttling provides basic protection
  - DynamoDB on-demand billing absorbs burst but at potentially high cost
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add API Gateway usage plans with explicit throttle settings per API key. Deploy AWS WAF with rate-based rules. Set per-agent rate limits.
- **Evidence**: `lib/apigateway.ts` (no throttling config), `lib/database.ts` (`billingMode: BillingMode.PAY_PER_REQUEST` — no explicit capacity limits)

### STATE-Q6: Blast Radius and Transaction Limits

- **Severity**: RISK
- **Finding**: No configurable transaction limits. `getAllProducts()` in `src/product/index.js`, `getAllBaskets()` in `src/basket/index.js`, and `getAllOrders()` in `src/ordering/index.js` all use `ScanCommand` with no `Limit` parameter — returning all records in the table. `deleteProduct()` accepts any product ID. `deleteBasket()` accepts any userName. No max_records_per_operation, no spend limits, no delete limits per session. An agent could scan entire tables (exhausting LLM context windows and increasing cost) or delete all products/baskets in a loop.
- **Gap**: No transaction limits. Unbounded scans and unrestricted delete operations create unlimited blast radius.
- **Compensating Controls**:
  - Scope agent tool definitions to exclude delete operations and getAllX endpoints during pilot
  - Set DynamoDB Scan Limit parameter in agent wrapper layer
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add `Limit` parameter to all ScanCommand operations. Implement per-agent operation quotas (max deletes per session, max records per query). Consider removing bulk delete capability from agent-facing APIs.
- **Evidence**: `src/product/index.js` (getAllProducts — `ScanCommand` with no Limit), `src/basket/index.js` (getAllBaskets — same), `src/ordering/index.js` (getAllOrders — same)

### STATE-Q7: Infrastructure Capacity for Agent Traffic

- **Severity**: RISK
- **Finding**: Lambda functions in `lib/microservice.ts` use `Runtime.NODEJS_14_X` (deprecated runtime — EOL April 2024). No explicit memory configuration (default 128MB). No provisioned concurrency configured. DynamoDB uses `PAY_PER_REQUEST` which auto-scales but has no explicit capacity planning. SQS `OrderQueue` has default visibility timeout (30s) and `batchSize: 1`. No load test results or capacity planning documentation found. No auto-scaling policies beyond DynamoDB on-demand.
- **Gap**: Deprecated Lambda runtime. No capacity planning. No load testing. No provisioned concurrency for predictable agent traffic patterns.
- **Compensating Controls**:
  - Serverless architecture auto-scales by default (Lambda + DynamoDB on-demand)
  - Low-volume pilot will not stress infrastructure limits
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Upgrade Lambda runtime to NODEJS_20_X. Configure Lambda memory based on workload profiling. Add provisioned concurrency for latency-sensitive endpoints. Conduct load testing simulating agent traffic patterns.
- **Evidence**: `lib/microservice.ts` (`runtime: Runtime.NODEJS_14_X` — deprecated), `lib/queue.ts` (batchSize: 1), `lib/database.ts` (`BillingMode.PAY_PER_REQUEST`)

### HITL-Q1: Draft/Pending State

- **Severity**: RISK
- **Finding**: No draft or pending state concept in any microservice. `POST /product` immediately persists products to DynamoDB. `POST /basket` immediately saves basket state. `POST /basket/checkout` immediately triggers the full order pipeline (EventBridge → SQS → order creation). The ordering Lambda immediately writes orders to DynamoDB. No two-step commit patterns. No status fields that could represent draft/pending/confirmed states.
- **Gap**: No draft or pending states. All write operations are immediately committed. An agent cannot propose changes for human review before execution.
- **Compensating Controls**:
  - Add agent-level approval gate in the orchestration layer before calling write endpoints
  - Restrict agent to read-only operations during pilot (no write access)
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add a `status` field to product and order records (draft/pending/confirmed). Modify write endpoints to create records in draft status. Add separate confirmation endpoint to move from draft to confirmed.
- **Evidence**: `src/product/index.js` (createProduct — immediate PutItemCommand), `src/basket/index.js` (checkoutBasket — immediate event publication)

### HITL-Q2: Configurable Approval Gates

- **Severity**: RISK
- **Finding**: No approval workflow endpoints. No status-based workflows requiring explicit confirmation. No configurable operation-level flags. No Step Functions with human approval tasks (`waitForTaskToken`). All operations execute immediately upon API invocation with no approval step.
- **Gap**: No configurable approval gates. High-risk operations (checkout, product deletion) execute without human oversight.
- **Compensating Controls**:
  - Implement approval gates in the agent orchestration layer (external to this system)
  - Use agent-side confirmation prompts for high-risk operations during pilot
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement Step Functions workflows with `waitForTaskToken` for high-risk operations (checkout, delete). Add an approval API that queues operations for human review.
- **Evidence**: `lib/aws-microservices-stack.ts` (no Step Functions), `src/basket/index.js` (checkoutBasket — no approval step)

### HITL-Q3: Sandbox/Staging Environment

- **Severity**: RISK
- **Finding**: No separate environment configurations. `bin/aws-microservices.ts` deploys a single stack (`AwsMicroservicesStack`) with no environment-specific parameters. The `env` property is commented out. No staging or sandbox CDK stacks. No docker-compose for local testing. No seed data scripts. No synthetic data generators. `jest.config.js` exists but the only test file (`test/aws-microservices.test.ts`) is entirely commented out.
- **Gap**: No sandbox or staging environment. No local testing capability. The first time an agent is tested against this system will be in production.
- **Compensating Controls**:
  - Deploy a separate CDK stack with a different stack name for staging
  - Use DynamoDB local for offline testing
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Parameterize the CDK stack to accept environment name. Create a staging stack with separate DynamoDB tables. Add seed data scripts for realistic test data. Add docker-compose with DynamoDB local for development.
- **Evidence**: `bin/aws-microservices.ts` (single stack, env commented out), `test/aws-microservices.test.ts` (entirely commented out)

### DATA-Q3: Selective Query Support

- **Severity**: RISK
- **Finding**: No pagination in any API endpoint. `getAllProducts()`, `getAllBaskets()`, `getAllOrders()` use DynamoDB `ScanCommand` with no `Limit`, offset, or cursor parameters. No filter query parameters on list endpoints (except product category filter which requires both `id` and `category`). No sorting options. No result size limits. `getOrder()` requires exact `userName + orderDate` composite key — no range queries.
- **Gap**: No pagination, no filtering, no result size limits. Unbounded result sets will exhaust LLM context windows.
- **Compensating Controls**:
  - Agent wrapper layer adds artificial result limits by truncating responses
  - Use specific item queries (`GET /product/{id}`) instead of list endpoints during pilot
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `limit` and `lastEvaluatedKey` pagination parameters to all list endpoints. Add filter query parameters. Return `nextToken` for cursor-based pagination.
- **Evidence**: `src/product/index.js` (getAllProducts — ScanCommand no Limit), `src/basket/index.js` (getAllBaskets — same), `src/ordering/index.js` (getAllOrders — same)

### DATA-Q4: System of Record Designations

- **Severity**: RISK
- **Finding**: No system-of-record designations documented. No master data management references. DynamoDB tables are implicitly the system of record for each domain (product table for products, basket table for baskets, order table for orders), but this is not formally documented. No data ownership definitions. The checkout flow copies basket data into the order record (`Object.assign(checkoutRequest, basket)` in `src/basket/index.js`), creating a denormalized copy — no designated golden record.
- **Gap**: No formal system-of-record designations. Data duplication during checkout without clear ownership or conflict resolution.
- **Compensating Controls**:
  - Treat each DynamoDB table as the system of record for its domain entity during pilot
  - Document data ownership as part of agent tool definitions
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Document each DynamoDB table as the system of record for its domain. Define data ownership for cross-service data (e.g., order records that contain basket item data). Add `sourceSystem` field to order records.
- **Evidence**: `lib/database.ts` (three separate tables — implicit SoR), `src/basket/index.js` (prepareOrderPayload — `Object.assign` creates denormalized copy)

### DATA-Q5: Reliable Timestamps

- **Severity**: RISK
- **Finding**: Order records include `orderDate` set to `new Date().toISOString()` in `src/ordering/index.js` — ISO 8601 format in UTC. However, product records have no `created_at` or `updated_at` timestamps. Basket records have no timestamps. Only the order service has timestamps, used as a DynamoDB sort key. No timezone normalization documentation. Lambda execution time is the only source of time — no NTP synchronization concerns in serverless (handled by AWS).
- **Gap**: Only order records have timestamps. Product and basket records have no temporal data. An agent cannot determine when a product was last updated or when a basket was modified.
- **Compensating Controls**:
  - DynamoDB Streams could be enabled to capture modification timestamps externally
  - Agent tracks timestamps in its own state for recently modified records
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `createdAt` and `updatedAt` fields (ISO 8601 UTC) to all product and basket records. Set these fields in the Lambda handlers on create and update operations.
- **Evidence**: `src/ordering/index.js` (`const orderDate = new Date().toISOString()`), `src/product/index.js` (createProduct — no timestamp), `src/basket/index.js` (createBasket — no timestamp)

### DATA-Q6: Data Freshness Signaling

- **Severity**: RISK
- **Finding**: No `Cache-Control` headers in any API response. No `X-Data-Age` headers. No `last_refreshed` fields. No `consistency_level` fields. API responses are plain JSON with `message` and `body` fields. DynamoDB `GetItemCommand` uses strong consistency by default, but `ScanCommand` uses eventually consistent reads — this difference is not signaled to the caller. An agent has no way to know if the data it received is strongly consistent or eventually consistent.
- **Gap**: No data freshness signaling. Agents cannot distinguish between strongly consistent reads and eventually consistent scans.
- **Compensating Controls**:
  - Document consistency model in agent tool definitions (GET by ID = strongly consistent, GET all = eventually consistent)
  - Agent treats all data as potentially stale and re-reads before critical decisions
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `Cache-Control` and `X-Consistency-Level` headers to API responses. Use consistent reads for ScanCommand when freshness is critical. Add `lastModified` timestamps to response bodies.
- **Evidence**: `src/product/index.js` (no cache/freshness headers in response), `src/basket/index.js` (same), `src/ordering/index.js` (same)

### DATA-Q7: PII Redaction in Logs

- **Severity**: RISK
- **Finding**: All three Lambda handlers log full event payloads with `console.log("request:", JSON.stringify(event, undefined, 2))`. The checkout flow in `src/basket/index.js` logs the full `checkoutPayload` including PII: `firstName`, `lastName`, `email`, `address`, `cardInfo`, and `paymentMethod`. The `prepareOrderPayload` function logs `console.log("Success prepareOrderPayload, orderPayload:", checkoutRequest)` — the full order payload with all PII. Error responses include `errorStack` which may contain PII from request processing. No log scrubbing middleware. No PII masking libraries. No CloudWatch log filters.
- **Gap**: PII (including payment card info) is logged to CloudWatch in plain text. Compliance violation risk for GDPR, PCI DSS, and other regulations.
- **Compensating Controls**:
  - Add CloudWatch Logs metric filter to detect PII patterns and alert
  - Reduce log verbosity in production (remove event payload logging)
- **Remediation Timeline**: 30–60 days (urgent due to PCI DSS implications)
- **Recommendation**: Remove full event payload logging. Implement structured logging with PII field redaction. Use a logging library that supports field-level masking. Add CloudWatch Logs data protection policy for PII detection.
- **Evidence**: `src/basket/index.js` (`console.log("publishCheckoutBasketEvent with payload :", checkoutPayload)` — logs PII), `src/product/index.js` (`console.log("request:", JSON.stringify(event, undefined, 2))`), `src/ordering/index.js` (same pattern)

### DISC-Q1: Schema Documentation and Versioning

- **Severity**: RISK
- **Finding**: No JSON Schema files. No Avro/Protobuf schemas. No database migration files (DynamoDB tables defined in CDK with no migration tooling). No schema registry. No OpenAPI schema definitions. DynamoDB table schemas are defined only in CDK code comments (e.g., `// product : PK: id -- name - description - imageFile - price - category` and `// order : PK: userName - SK: orderDate -- totalPrice - firstName - lastName - email - address - paymentMethod - cardInfo`). Actual schema is implicit in Lambda handler code.
- **Gap**: No formal schema documentation. No schema versioning. Schema changes (adding/removing fields) have no tracking or notification mechanism.
- **Compensating Controls**:
  - CDK code comments serve as informal schema documentation
  - Agent tool definitions can document expected schemas
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Create JSON Schema files for each entity (product, basket, order). Add schema validation in Lambda handlers. Version schemas and maintain a changelog.
- **Evidence**: `lib/database.ts` (schema in code comments only), absence of any schema files in the repository

### OBS-Q1: Distributed Tracing and Structured Logging

- **Severity**: RISK
- **Finding**: No X-Ray tracing enabled on Lambda functions — `tracing` property not set in `NodejsFunctionProps` in `lib/microservice.ts`. No OpenTelemetry SDK imported. No `traceparent` header propagation. Logs use `console.log` and `console.error` — unstructured text, not JSON. No correlation IDs or `request_id` fields in log output. API Gateway does not have tracing enabled. When an agent-initiated request fails in the checkout flow (basket → EventBridge → SQS → ordering), there is no way to trace the request across services.
- **Gap**: No distributed tracing. No structured logging. No correlation IDs. Agent-initiated failures across the event-driven flow are not debuggable.
- **Compensating Controls**:
  - API Gateway automatically generates request IDs (visible in CloudWatch Logs)
  - SQS message IDs provide partial correlation for the async flow
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Enable X-Ray tracing on all Lambda functions (`tracing: Tracing.ACTIVE` in CDK). Enable X-Ray on API Gateway. Adopt structured JSON logging (e.g., AWS Lambda Powertools Logger). Add correlation IDs that propagate through EventBridge → SQS → ordering.
- **Evidence**: `lib/microservice.ts` (NodejsFunctionProps — no `tracing` property), `src/product/index.js` (`console.log` — unstructured), `lib/apigateway.ts` (no tracing config)

### OBS-Q2: Alerting on Error Rates and Latency

- **Severity**: RISK
- **Finding**: No CloudWatch alarms defined in any CDK construct. No anomaly detection configuration. No PagerDuty/OpsGenie integration. No composite alarms. No SLO-based alerting. No alerting thresholds configured anywhere in the codebase. If API error rates spike or latency degrades (affecting agent operations), there is no automated detection or notification.
- **Gap**: No alerting on error rates or latency. Agent-impacting degradation will go undetected until users report issues.
- **Compensating Controls**:
  - CloudWatch automatically captures Lambda error metrics and API Gateway 4xx/5xx counts
  - Manual CloudWatch dashboard monitoring during pilot
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add CloudWatch alarms for Lambda error rates, API Gateway 5xx rates, API Gateway latency P95, SQS DLQ message count, and DynamoDB throttled requests. Integrate with SNS for notification.
- **Evidence**: `lib/aws-microservices-stack.ts` (no CloudWatch alarms), absence of any alerting configuration in the entire codebase

### ENG-Q1: Infrastructure Governance for Agent-Facing Surface

- **Severity**: RISK
- **Finding**: Infrastructure is defined as CDK code in `lib/*.ts` — IaC exists (sub-check 1 of 3 met). However, no PR review requirements are visible in the repository — no `CODEOWNERS` file, no branch protection configuration, no CI/CD pipeline to enforce reviews (sub-check 2 of 3 not met). No drift detection configuration — no AWS Config rules, no `cdk diff` automation (sub-check 3 of 3 not met).
- **Gap**: IaC exists but without peer review enforcement or drift detection. Infrastructure changes to the agent-facing surface (API Gateways, IAM roles) can be made without oversight.
- **Compensating Controls**:
  - CDK code is in version control (Git), providing change history
  - Manual `cdk diff` before deployment
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add CODEOWNERS file requiring review for `lib/*.ts` changes. Implement CI/CD pipeline with `cdk diff` output in PR. Enable AWS Config rules for drift detection on API Gateway and IAM resources.
- **Evidence**: `lib/*.ts` (IaC exists), absence of `.github/`, `CODEOWNERS`, `buildspec.yml`, or any CI/CD configuration

### ENG-Q2: CI/CD with API Contract Testing

- **Severity**: RISK
- **Finding**: No CI/CD pipeline definitions found — no GitHub Actions workflows (`.github/workflows/`), no GitLab CI (`.gitlab-ci.yml`), no Jenkinsfile, no `buildspec.yml`, no CodePipeline in CDK. No API contract tests. No consumer-driven contract testing (Pact). No OpenAPI spec validation in build. No breaking change detection. The repository has a `build` script (`tsc`) and a `test` script (`jest`) in `package.json`, but the only test file is entirely commented out.
- **Gap**: No CI/CD pipeline. No API contract testing. API-breaking changes cannot be detected before agents are affected.
- **Compensating Controls**:
  - Manual `cdk deploy` provides a deployment mechanism
  - Manual testing before deployment
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement GitHub Actions or CodePipeline CI/CD. Add API contract tests that validate endpoint behavior. Integrate OpenAPI spec export and diff into the pipeline. Add CDK snapshot tests.
- **Evidence**: Absence of `.github/`, `.gitlab-ci.yml`, `Jenkinsfile`, `buildspec.yml`. `test/aws-microservices.test.ts` (entirely commented out). `package.json` (test script exists but no tests to run)

### ENG-Q3: Rollback Capability

- **Severity**: RISK
- **Finding**: No deployment pipeline found. No blue/green configuration. No CodeDeploy rollback triggers. No canary deployment. No feature flags. No traffic shifting. No Lambda versioning or alias configuration. CDK deploy is manual (`cdk deploy` per README). Rollback would require manually running `cdk deploy` with a previous version of the code — no automated rollback mechanism. DynamoDB tables have `removalPolicy: RemovalPolicy.DESTROY` — a stack rollback could delete tables and lose data.
- **Gap**: No automated rollback capability. Manual rollback process. DynamoDB DESTROY removal policy risks data loss on rollback.
- **Compensating Controls**:
  - Git history allows checking out previous versions for manual redeployment
  - CloudFormation stack rollback provides basic protection (but DESTROY policy risks data)
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement automated deployment pipeline with rollback triggers. Change DynamoDB `removalPolicy` to `RETAIN`. Add Lambda versioning and aliases with traffic shifting for safe deployments. Add CloudFormation stack policy to prevent table deletion.
- **Evidence**: `lib/database.ts` (`removalPolicy: RemovalPolicy.DESTROY` on all three tables), `README.md` (manual `cdk deploy` instructions), absence of deployment pipeline

### ENG-Q4: API Test Coverage

- **Severity**: RISK
- **Finding**: The `test/` directory contains only `test/aws-microservices.test.ts`, which is entirely commented out — zero functional test coverage. `jest.config.js` exists but there are no runnable tests. No API test suites (Postman/Newman, REST Assured). No integration tests. No contract tests. No test directories in any service (`src/product/`, `src/basket/`, `src/ordering/` have no test files). The `package.json` includes `jest` and `ts-jest` as devDependencies, but they are unused.
- **Gap**: Zero test coverage. No automated tests for any API endpoint. Changes to Lambda handlers or CDK constructs have no safety net.
- **Compensating Controls**:
  - Manual API testing via curl/Postman during pilot
  - CDK snapshot testing can be quickly added
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Uncomment and update the CDK infrastructure test. Add API integration tests for each Lambda handler. Add Postman/Newman collections for automated API testing. Integrate tests into CI/CD pipeline.
- **Evidence**: `test/aws-microservices.test.ts` (entirely commented out), `jest.config.js` (configured but unused), absence of any test files in `src/` directories

### ENG-Q5: Encryption at Rest for Agent-Accessible Data

- **Severity**: RISK
- **Finding**: DynamoDB tables in `lib/database.ts` have no explicit encryption configuration. DynamoDB encrypts data at rest by default using AWS-owned keys, but no customer-managed KMS keys are specified. The order table stores PII (`firstName`, `lastName`, `email`, `address`, `cardInfo`) without customer-managed encryption — AWS-owned keys provide basic encryption but do not allow customer key management, rotation control, or audit via CloudTrail. SQS `OrderQueue` in `lib/queue.ts` has no encryption configuration — SQS does not encrypt at rest by default. Checkout event payloads (containing PII) pass through SQS unencrypted at rest.
- **Gap**: No customer-managed encryption. SQS queue unencrypted at rest. PII in transit through SQS is not encrypted at rest. No KMS key management or rotation.
- **Compensating Controls**:
  - DynamoDB default AWS-owned encryption provides basic at-rest protection
  - Data in transit is encrypted via HTTPS (API Gateway) and AWS service endpoints
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Enable customer-managed KMS encryption on all DynamoDB tables (`encryption: TableEncryption.CUSTOMER_MANAGED`). Enable SQS server-side encryption with KMS (`encryptionMasterKey`). Use the same KMS key across services for simplified key management.
- **Evidence**: `lib/database.ts` (no encryption config on any table), `lib/queue.ts` (no encryption config on OrderQueue)

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO
- **Finding**: The application exposes REST APIs via three separate API Gateway instances defined in `lib/apigateway.ts`. Product service: `GET /product`, `POST /product`, `GET /product/{id}`, `PUT /product/{id}`, `DELETE /product/{id}`. Basket service: `GET /basket`, `POST /basket`, `GET /basket/{userName}`, `DELETE /basket/{userName}`, `POST /basket/checkout`. Order service: `GET /order`, `GET /order/{userName}`. The REST API surface is well-structured and does NOT require direct database access, file-based exchange, or UI automation — the core BLOCKER criteria are met.
- **Implication**: Agents can bind to these REST endpoints as tools. The API surface exists and is functional. However, API documentation is limited to CDK code comments and README.md — no formal API documentation for consumers.
- **Recommendation**: Generate and publish API documentation (OpenAPI spec — see API-Q2) to accelerate agent tool definition authoring.
- **Evidence**: `lib/apigateway.ts` (three `LambdaRestApi` constructs with explicit route definitions)

### API-Q6: Structured Response Format

- **Severity**: INFO
- **Finding**: All APIs return structured JSON responses via `JSON.stringify()`. Success responses follow a consistent format: `{ message: "Successfully finished operation: ...", body: <result> }`. Error responses follow: `{ message: "Failed to perform operation.", errorMsg: <message>, errorStack: <stack> }`. No XML, binary, or protobuf formats. All Lambda handlers use the same response structure.
- **Implication**: JSON responses are directly consumable by LLM-based agents. The consistent format simplifies agent tool parsing. The `body` field contains the actual data, which is predictable across all endpoints.
- **Recommendation**: Formalize the response envelope (message + body) as a documented contract. Remove `errorStack` from error responses (security concern — see API-Q3).
- **Evidence**: `src/product/index.js` (response: `JSON.stringify({ message: ..., body: body })`), `src/basket/index.js` (same pattern), `src/ordering/index.js` (same pattern)

### API-Q8: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: EventBridge integration exists for checkout events. The basket service publishes events to `SwnEventBus` with source `com.swn.basket.checkoutbasket` and detail type `CheckoutBasket` (defined in `lib/eventbus.ts`). EventBridge rule routes to SQS `OrderQueue`, which triggers the ordering Lambda. No webhook callback endpoints exist. No events emitted for product CRUD operations or basket modifications — only checkout triggers events.
- **Implication**: The event-driven architecture provides a foundation for proactive agent patterns. An agent could subscribe to EventBridge events to react to order creation. However, the current event surface is limited to checkout only — product catalog changes and basket updates do not emit events.
- **Recommendation**: Expand event emission to product CRUD (new product, price change, product deleted) and basket operations. This enables proactive agents that react to catalog changes or abandoned baskets.
- **Evidence**: `lib/eventbus.ts` (SwnEventBus, CheckoutBasketRule), `src/basket/index.js` (publishCheckoutBasketEvent), `src/basket/checkoutbasketevents.json` (sample events)

### API-Q9: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No API Gateway throttling configuration in CDK code. No WAF rate rules. No rate limiting middleware in Lambda handlers. No usage plan defined. No `X-RateLimit-Remaining` or `Retry-After` headers in API responses. Default API Gateway limits (10,000 RPS per region account-level, 5,000 RPS per method) apply but are not documented or exposed to consumers. Agents calling these APIs have no visibility into rate limits.
- **Implication**: Agents cannot self-throttle because rate limit information is not available. This increases the risk of hitting default limits and receiving 429 responses that agents may not handle gracefully.
- **Recommendation**: Configure explicit throttle settings in API Gateway usage plans. Add `X-RateLimit-Remaining` and `Retry-After` headers to API responses. Document rate limits in API specifications.
- **Evidence**: `lib/apigateway.ts` (no throttling config), absence of rate limit headers in any Lambda handler response

### API-Q10: API Latency Profile

- **Severity**: INFO
- **Finding**: No performance benchmarks, load test results, or latency metrics found in the repository. Lambda functions use `Runtime.NODEJS_14_X` (deprecated). No provisioned concurrency configured — cold starts will affect P95 latency. DynamoDB uses `PAY_PER_REQUEST` billing (on-demand) which provides consistent single-digit millisecond performance at any scale. The async checkout flow adds latency through EventBridge → SQS → Lambda chain — not measurable without runtime metrics.
- **Implication**: Without latency data, agent orchestration cannot estimate total response time for multi-tool workflows. An agent calling product lookup + basket update + checkout involves 3 synchronous calls plus an async chain. Cold start latency on NODEJS_14_X Lambda could add 500ms–2s per call.
- **Recommendation**: Conduct load testing to establish P95 baselines. Add provisioned concurrency for agent-facing Lambdas. Upgrade runtime to reduce cold start latency. Publish latency metrics to CloudWatch.
- **Evidence**: `lib/microservice.ts` (`runtime: Runtime.NODEJS_14_X`, no provisioned concurrency), `lib/database.ts` (`BillingMode.PAY_PER_REQUEST`)

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Field names are generally readable and semantically meaningful: `userName`, `productId`, `productName`, `totalPrice`, `firstName`, `lastName`, `email`, `address`, `paymentMethod`, `orderDate`, `imageFile`, `price`, `category`, `description`. DynamoDB internal key names (`PK`, `SK`) are mapped to descriptive names (`id`, `userName`, `orderDate`) in code. Table names are clear: `product`, `basket`, `order`. No legacy abbreviations requiring a data dictionary.
- **Implication**: LLM-based agents can reason about field semantics without a data dictionary. Field names are self-documenting, reducing the risk of agent misinterpretation.
- **Recommendation**: Maintain current naming conventions. Add a data dictionary for edge cases (e.g., `cardInfo` structure is unclear — what fields does it contain?).
- **Evidence**: `lib/database.ts` (table and key naming), `src/product/index.js` (field names in code), `src/basket/index.js` (field names), `src/ordering/index.js` (field names)

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No AWS Glue Data Catalog. No Collibra, Alation, or DataHub integration. No metadata files. No data dictionaries. No API catalogs. The only documentation of data structures is inline CDK code comments in `lib/database.ts` describing table schemas (e.g., `// product : PK: id -- name - description - imageFile - price - category`).
- **Implication**: Agent tool builders must inspect source code to understand what data exists. No centralized metadata layer accelerates this process. For three microservices this is manageable; at scale it would become a bottleneck.
- **Recommendation**: Create a lightweight data dictionary (markdown or JSON) documenting each table's schema, field types, and descriptions. Consider AWS Glue Data Catalog for DynamoDB tables if the dataset grows.
- **Evidence**: `lib/database.ts` (schema comments only), absence of any metadata files or data catalog configuration

### DISC-Q4: Data Lineage

- **Severity**: INFO
- **Finding**: No data lineage tools (AWS Glue DataBrew, Apache Atlas). The event flow from basket checkout → EventBridge → SQS → ordering is visible in CDK code (`lib/eventbus.ts`, `lib/queue.ts`, `lib/aws-microservices-stack.ts`) but not documented as a formal lineage record. No ETL pipeline documentation. No data flow diagrams beyond the README.md architecture references. No transformation logs documenting how basket data is transformed into order data.
- **Implication**: When an agent produces incorrect output due to bad data, there is no lineage to trace the data's origin. The basket→order transformation in `prepareOrderPayload` is a data derivation that is not tracked.
- **Recommendation**: Document the data flow (basket → EventBridge → SQS → order) as a formal lineage diagram. Add transformation logging in the ordering Lambda to record source event IDs and transformation steps.
- **Evidence**: `lib/eventbus.ts` (event flow definition), `lib/queue.ts` (SQS to ordering), `src/basket/index.js` (prepareOrderPayload — data transformation)

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No `cloudwatch.put_metric_data` calls in any Lambda function. No custom dashboards. No business KPI alarms. No custom metrics published for order completion rates, checkout success/failure rates, basket abandonment, or other business events. CloudWatch captures only default Lambda metrics (invocations, errors, duration) and API Gateway metrics (4xx, 5xx, latency).
- **Implication**: When agents consume this system, business metrics are the primary signal for whether agent interactions produce good outcomes. Without custom business metrics, you cannot measure agent effectiveness (e.g., "did the agent-assisted checkout succeed?").
- **Recommendation**: Add custom CloudWatch metrics for checkout completion rate, order creation success rate, and basket conversion rate. Create a CloudWatch dashboard for business KPIs.
- **Evidence**: `src/basket/index.js` (no custom metrics on checkout), `src/ordering/index.js` (no custom metrics on order creation), `lib/aws-microservices-stack.ts` (no CloudWatch dashboard)

### DATA-Q8: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality dashboards. No data profiling reports. No null rate monitoring. No duplicate detection logic. No data freshness SLAs. No data quality metrics published to CloudWatch. The application performs minimal input validation — `checkoutBasket` validates that `userName` exists in the request and that the basket has items, but no other field validation exists across any handler.
- **Implication**: Agents acting on incomplete or low-quality data will propagate errors. For example, a product record with no `price` field could cause the checkout `totalPrice` calculation to return NaN, which would be stored in the order record.
- **Recommendation**: Add input validation to all Lambda handlers. Implement data quality checks (null detection, type validation) at write time. Publish data quality metrics to CloudWatch.
- **Evidence**: `src/basket/index.js` (minimal validation — only userName and basket.items checks), `src/product/index.js` (no input validation on createProduct), `src/ordering/index.js` (no validation on createOrder)

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: The application exposes REST APIs via three `LambdaRestApi` constructs in `lib/apigateway.ts`: Product (`GET/POST /product`, `GET/PUT/DELETE /product/{id}`), Basket (`GET/POST /basket`, `GET/DELETE /basket/{userName}`, `POST /basket/checkout`), and Order (`GET /order`, `GET /order/{userName}`). Integration does NOT require direct database access, file-based exchange, or UI automation. REST API surface exists and is functional.
- **Gap**: API documentation exists only in CDK code comments and README.md. No formal consumer-facing documentation.
- **Recommendation**: Generate OpenAPI specifications from deployed API Gateways. Publish formal API docs.
- **Evidence**: `lib/apigateway.ts`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK
- **Finding**: No OpenAPI, Swagger, AsyncAPI, GraphQL schema, or Smithy files found. API surface defined only in CDK code and Lambda handler switch statements.
- **Gap**: No machine-readable spec. Agent tool definitions must be manually authored.
- **Recommendation**: Generate OpenAPI specs from deployed APIs. Add to repository.
- **Evidence**: `lib/apigateway.ts`, absence of spec files

#### API-Q3: Structured Error Responses
- **Severity**: RISK
- **Finding**: All handlers return `statusCode: 500` with `{ message, errorMsg, errorStack }`. No structured error codes. No retryable boolean. Stack traces leaked in responses.
- **Gap**: Agents cannot distinguish retriable from terminal errors.
- **Recommendation**: Implement structured error codes, retryable flag, remove stack traces.
- **Evidence**: `src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: BLOCKER
- **Conditional**: agent_scope is "write-enabled" — evaluated as BLOCKER
- **Finding**: `POST /product` generates new UUID per call (no idempotency). `POST /basket/checkout` has no idempotency protection — retries create duplicate EventBridge events and orders. `POST /basket` is naturally idempotent (upsert by userName). `PUT /product/{id}` is naturally idempotent.
- **Gap**: Checkout and product creation lack idempotency keys.
- **Recommendation**: Add idempotency key support using AWS Lambda Powertools idempotency utility.
- **Evidence**: `src/product/index.js` (uuidv4), `src/basket/index.js` (checkoutBasket)

#### API-Q5: API Versioning and Deprecation
- **Severity**: RISK
- **Finding**: No `/v1/` URL patterns. No `Accept-Version` headers. No changelog. Routes are unversioned (`/product`, `/basket`, `/order`).
- **Gap**: No API versioning or deprecation policy.
- **Recommendation**: Add version prefix to routes. Implement changelog.
- **Evidence**: `lib/apigateway.ts`

#### API-Q6: Structured Response Format
- **Severity**: INFO
- **Finding**: All APIs return JSON. Consistent format: `{ message: "...", body: <data> }`. No XML or binary formats.
- **Gap**: N/A — JSON format is agent-friendly.
- **Recommendation**: Formalize response envelope as documented contract.
- **Evidence**: `src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js`

#### API-Q7: Asynchronous Operation Support
- **Severity**: RISK
- **Finding**: Checkout uses async pattern (EventBridge → SQS → ordering). No job status polling endpoint or webhook callback. Caller cannot verify order creation.
- **Gap**: Fire-and-forget async with no status tracking.
- **Recommendation**: Add order status endpoint. Return order reference from checkout.
- **Evidence**: `src/basket/index.js` (checkoutBasket), `lib/eventbus.ts`, `lib/queue.ts`

#### API-Q8: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: EventBridge events emitted for checkout only (`com.swn.basket.checkoutbasket`). No events for product CRUD or basket operations. No webhook callbacks.
- **Gap**: Limited event surface — only checkout triggers events.
- **Recommendation**: Expand event emission to all state changes.
- **Evidence**: `lib/eventbus.ts`, `src/basket/index.js`

#### API-Q9: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No explicit throttling config. No usage plans. No `X-RateLimit-Remaining` headers. Default API Gateway limits apply undocumented.
- **Gap**: Rate limits not documented or exposed to consumers.
- **Recommendation**: Configure usage plans. Add rate limit headers.
- **Evidence**: `lib/apigateway.ts`

#### API-Q10: API Latency Profile
- **Severity**: INFO
- **Finding**: No benchmarks or load tests. NODEJS_14_X runtime (deprecated). No provisioned concurrency. DynamoDB PAY_PER_REQUEST provides consistent latency.
- **Gap**: No latency data available.
- **Recommendation**: Conduct load testing. Add provisioned concurrency. Upgrade runtime.
- **Evidence**: `lib/microservice.ts`, `lib/database.ts`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: All three API Gateways created with no authorizer. No Cognito, no API keys, no Lambda authorizer, no IAM auth. APIs are completely open and unauthenticated.
- **Gap**: No authentication. No machine identity. No principal attribution.
- **Recommendation**: Implement API keys immediately, then migrate to Cognito OAuth 2.0 client credentials.
- **Evidence**: `lib/apigateway.ts`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK
- **Finding**: CDK uses `grantReadWriteData()` per table per function. Table-level isolation exists. All grants are ReadWrite — no read-only grants.
- **Gap**: No action-level scoping. All functions have full ReadWrite.
- **Recommendation**: Use `grantReadData()` where only reads needed. Split ordering Lambda.
- **Evidence**: `lib/microservice.ts`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK
- **Finding**: No action-level authorization in handlers or API Gateway. Any caller executes any operation (GET, POST, PUT, DELETE).
- **Gap**: No action-level controls.
- **Recommendation**: Add API Gateway authorizers with method-level policies.
- **Evidence**: `lib/apigateway.ts`, `src/product/index.js`

#### AUTH-Q4: Identity Propagation
- **Severity**: RISK
- **Finding**: No JWT, OAuth, or token exchange. `userName` is self-asserted in request body — not from authenticated identity. Enables impersonation.
- **Gap**: No identity propagation. Self-asserted user context.
- **Recommendation**: Derive userName from JWT claims via Cognito.
- **Evidence**: `src/basket/index.js`, `src/ordering/index.js`

#### AUTH-Q5: Agent-as-Self vs Agent-on-Behalf-of-User
- **Severity**: RISK
- **Finding**: No authentication exists. No distinction between access modes. No audit fields for mode differentiation.
- **Gap**: Cannot distinguish agent-as-self from agent-on-behalf-of-user.
- **Recommendation**: Define separate OAuth scopes per mode after implementing auth.
- **Evidence**: `lib/apigateway.ts`, `src/basket/index.js`

#### AUTH-Q6: Credential Management
- **Severity**: RISK
- **Finding**: No hardcoded credentials. Lambda uses IAM execution roles via CDK grants. Environment variables contain only table names and event config. No Secrets Manager integration.
- **Gap**: Adequate for current scope but no Secrets Manager for future credentials.
- **Recommendation**: Integrate Secrets Manager for any new secrets.
- **Evidence**: `lib/microservice.ts`

#### AUTH-Q7: Immutable Audit Logging ⚡
- **Severity**: BLOCKER
- **Conditional**: agent_scope is "write-enabled" — evaluated as BLOCKER
- **Finding**: No CloudTrail in CDK. No log retention policies. Lambda uses unstructured `console.log` with full event payloads. No immutable log storage. No principal attribution.
- **Gap**: No immutable audit logging. No principal attribution on writes.
- **Recommendation**: Enable CloudTrail. Set log retention. Implement structured logging.
- **Evidence**: `lib/microservice.ts`, `src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js`

#### AUTH-Q8: Agent Identity Suspension
- **Severity**: RISK
- **Finding**: No API keys. No Cognito. No mechanism to suspend individual agent access. Only option is disabling entire API Gateway.
- **Gap**: Cannot suspend individual agent identities.
- **Recommendation**: Implement per-agent API key revocation after adding auth (AUTH-Q1).
- **Evidence**: `lib/apigateway.ts`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: BLOCKER
- **Conditional**: agent_scope is "write-enabled" — evaluated as BLOCKER
- **Finding**: Checkout flow executes 4 sequential steps with no compensation. EventBridge event publication is not reversible. No saga pattern, undo endpoints, or Step Functions. SQS OrderQueue has no DLQ.
- **Gap**: No compensation or rollback for multi-step checkout.
- **Recommendation**: Implement saga pattern with Step Functions. Add DLQ to OrderQueue.
- **Evidence**: `src/basket/index.js`, `src/ordering/index.js`, `lib/queue.ts`

#### STATE-Q2: Queryable Current State
- **Severity**: RISK
- **Finding**: GET endpoints exist for all services. Order query requires exact `orderDate` sort key — cannot list all orders for a user without full table scan.
- **Gap**: Order querying requires exact timestamp knowledge.
- **Recommendation**: Add partition-key-only query for orders by user. Add pagination.
- **Evidence**: `src/ordering/index.js`

#### STATE-Q3: Concurrency Controls
- **Severity**: RISK
- **Finding**: No optimistic locking. No version fields. No ETags. No conditional writes. PutItemCommand silently overwrites. Last-writer-wins semantics.
- **Gap**: No concurrency controls. Silent overwrites on concurrent access.
- **Recommendation**: Add version attribute with conditional writes.
- **Evidence**: `src/product/index.js`, `src/basket/index.js`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK
- **Finding**: No circuit breakers. No retry logic. No timeout configuration on SDK clients. Default DynamoDBClient and EventBridgeClient configs.
- **Gap**: No resilience patterns. External dependency failures cascade.
- **Recommendation**: Configure SDK timeouts. Add retry with exponential backoff.
- **Evidence**: `src/product/ddbClient.js`, `src/basket/ddbClient.js`, `src/basket/eventBridgeClient.js`, `src/ordering/ddbClient.js`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK
- **Finding**: No explicit rate limiting. No usage plans. No WAF. Default API Gateway limits only.
- **Gap**: No agent-specific rate limits. Runaway loops unprotected.
- **Recommendation**: Add usage plans with per-agent throttling. Deploy WAF.
- **Evidence**: `lib/apigateway.ts`, `lib/database.ts`

#### STATE-Q6: Blast Radius and Transaction Limits
- **Severity**: RISK
- **Finding**: All scan operations unbounded (no Limit). No delete limits. No per-agent quotas. Agent could delete all records or scan all tables.
- **Gap**: Unlimited blast radius on all operations.
- **Recommendation**: Add Limit to scans. Implement per-agent operation quotas.
- **Evidence**: `src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: RISK
- **Finding**: NODEJS_14_X deprecated runtime. Default Lambda memory. No provisioned concurrency. No load tests. DynamoDB on-demand auto-scales.
- **Gap**: Deprecated runtime. No capacity planning or load testing.
- **Recommendation**: Upgrade runtime. Add provisioned concurrency. Conduct load tests.
- **Evidence**: `lib/microservice.ts`, `lib/queue.ts`, `lib/database.ts`

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State
- **Severity**: RISK
- **Finding**: No draft/pending state in any service. All writes immediately committed. Checkout immediately triggers order pipeline.
- **Gap**: No draft states. Agent cannot propose changes for human review.
- **Recommendation**: Add status field with draft/pending/confirmed states.
- **Evidence**: `src/product/index.js`, `src/basket/index.js`

#### HITL-Q2: Configurable Approval Gates
- **Severity**: RISK
- **Finding**: No approval workflows. No Step Functions with human tasks. All operations execute immediately.
- **Gap**: No approval gates for high-risk operations.
- **Recommendation**: Implement Step Functions with `waitForTaskToken`.
- **Evidence**: `lib/aws-microservices-stack.ts`, `src/basket/index.js`

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK
- **Finding**: Single stack deployment. No staging. No docker-compose. No seed data. Tests entirely commented out. env commented out.
- **Gap**: No sandbox or staging environment.
- **Recommendation**: Parameterize stack for multi-environment. Add local testing.
- **Evidence**: `bin/aws-microservices.ts`, `test/aws-microservices.test.ts`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: Order table stores PII (firstName, lastName, email, address, paymentMethod, cardInfo) with no classification tags, no field-level encryption, no access controls. Potential PCI DSS violation with cardInfo storage.
- **Gap**: PII unclassified and unprotected. Payment card data in plain text.
- **Recommendation**: Classify tables. Tokenize cardInfo. Enable KMS encryption.
- **Evidence**: `lib/database.ts`, `src/basket/index.js`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: BLOCKER
- **Conditional**: agent_scope is "write-enabled" — evaluated as BLOCKER
- **Finding**: CDK stack env property commented out. No region pinning. No data residency documentation. Order data with PII could be deployed to any region.
- **Gap**: No region pinning. No data residency controls.
- **Recommendation**: Set env property. Document applicable regulations.
- **Evidence**: `bin/aws-microservices.ts`, `lib/database.ts`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK
- **Finding**: No pagination. All list endpoints use unbounded ScanCommand. No filters, no sorting, no result limits. Order query requires exact composite key.
- **Gap**: No pagination or filtering. Unbounded results.
- **Recommendation**: Add pagination with limit and cursor parameters.
- **Evidence**: `src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js`

#### DATA-Q4: System of Record Designations
- **Severity**: RISK
- **Finding**: No formal SoR designations. DynamoDB tables implicitly SoR per domain. Checkout copies basket data into orders (denormalization).
- **Gap**: No documented SoR. Data duplication without ownership clarity.
- **Recommendation**: Document SoR per entity. Add sourceSystem field.
- **Evidence**: `lib/database.ts`, `src/basket/index.js`

#### DATA-Q5: Reliable Timestamps
- **Severity**: RISK
- **Finding**: Only order records have timestamps (`orderDate` in ISO 8601 UTC). Product and basket records have no temporal fields.
- **Gap**: Incomplete timestamp coverage.
- **Recommendation**: Add createdAt/updatedAt to all records.
- **Evidence**: `src/ordering/index.js`, `src/product/index.js`, `src/basket/index.js`

#### DATA-Q6: Data Freshness Signaling
- **Severity**: RISK
- **Finding**: No Cache-Control, X-Data-Age, or consistency_level headers. Scan uses eventually consistent reads; GetItem uses strong consistency — not signaled.
- **Gap**: No data freshness signals in responses.
- **Recommendation**: Add freshness headers. Document consistency model.
- **Evidence**: `src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js`

#### DATA-Q7: PII Redaction in Logs
- **Severity**: RISK
- **Finding**: Full event payloads logged including PII (cardInfo, email, address). `checkoutPayload` with PII logged to CloudWatch. No masking or redaction.
- **Gap**: PII in logs. PCI DSS and GDPR compliance risk.
- **Recommendation**: Remove payload logging. Implement PII redaction.
- **Evidence**: `src/basket/index.js`, `src/product/index.js`, `src/ordering/index.js`

#### DATA-Q8: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics. Minimal input validation. No null monitoring. No duplicate detection. Missing price fields could cause NaN in calculations.
- **Gap**: No data quality awareness.
- **Recommendation**: Add input validation. Publish quality metrics.
- **Evidence**: `src/basket/index.js`, `src/product/index.js`, `src/ordering/index.js`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Documentation and Versioning
- **Severity**: RISK
- **Finding**: No schema files. No migration tooling. Schemas in CDK code comments only. No versioning.
- **Gap**: No formal schema documentation or versioning.
- **Recommendation**: Create JSON Schema files per entity. Add versioning.
- **Evidence**: `lib/database.ts`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Field names are readable: userName, productId, productName, totalPrice, firstName, etc. No legacy abbreviations. Table names clear.
- **Gap**: N/A — naming is good.
- **Recommendation**: Maintain conventions. Document cardInfo structure.
- **Evidence**: `lib/database.ts`, `src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No Glue Catalog, Collibra, or data dictionaries. Schema documentation in CDK comments only.
- **Gap**: No centralized metadata layer.
- **Recommendation**: Create lightweight data dictionary. Consider Glue Catalog.
- **Evidence**: `lib/database.ts`

#### DISC-Q4: Data Lineage
- **Severity**: INFO
- **Finding**: No lineage tools. Event flow visible in CDK code but not formally documented. No transformation logs for basket→order derivation.
- **Gap**: No formal data lineage.
- **Recommendation**: Document data flow. Add transformation logging.
- **Evidence**: `lib/eventbus.ts`, `lib/queue.ts`, `src/basket/index.js`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK
- **Finding**: No X-Ray tracing. No OpenTelemetry. No structured logging (console.log only). No correlation IDs. Cross-service failures not debuggable.
- **Gap**: No tracing, no structured logging, no correlation.
- **Recommendation**: Enable X-Ray. Adopt Lambda Powertools Logger. Add correlation IDs.
- **Evidence**: `lib/microservice.ts`, `src/product/index.js`, `src/basket/index.js`, `src/ordering/index.js`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK
- **Finding**: No CloudWatch alarms. No anomaly detection. No alerting thresholds. Degradation goes undetected.
- **Gap**: No alerting on API error rates or latency.
- **Recommendation**: Add CloudWatch alarms for errors, latency, DLQ depth, throttling.
- **Evidence**: `lib/aws-microservices-stack.ts`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom metrics. No business dashboards. Only default Lambda/API Gateway metrics.
- **Gap**: Cannot measure agent effectiveness on business outcomes.
- **Recommendation**: Add custom metrics for checkout rate, order success, basket conversion.
- **Evidence**: `src/basket/index.js`, `src/ordering/index.js`, `lib/aws-microservices-stack.ts`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK
- **Finding**: IaC exists (CDK in `lib/*.ts`). No CODEOWNERS, no branch protection, no CI/CD for review enforcement. No drift detection (no AWS Config rules).
- **Gap**: 1 of 3 governance sub-checks met. No review or drift detection.
- **Recommendation**: Add CODEOWNERS. Implement CI/CD with cdk diff. Enable Config rules.
- **Evidence**: `lib/*.ts`, absence of CI/CD and CODEOWNERS

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK
- **Finding**: No CI/CD pipeline. No contract tests. No Pact. No OpenAPI validation. Tests commented out. Build script is manual `tsc`.
- **Gap**: No CI/CD. No contract testing.
- **Recommendation**: Implement CI/CD pipeline. Add API contract tests.
- **Evidence**: `package.json`, `test/aws-microservices.test.ts`, absence of pipeline configs

#### ENG-Q3: Rollback Capability
- **Severity**: RISK
- **Finding**: Manual `cdk deploy`. No blue/green. No canary. No feature flags. No Lambda versioning. DynamoDB DESTROY removal policy risks data loss.
- **Gap**: No automated rollback. DESTROY policy risks data loss.
- **Recommendation**: Implement deployment pipeline. Change to RETAIN removal policy. Add Lambda aliases.
- **Evidence**: `lib/database.ts` (RemovalPolicy.DESTROY), `README.md`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK
- **Finding**: Zero test coverage. Only test file entirely commented out. No API tests, integration tests, or contract tests.
- **Gap**: No test coverage for any API endpoint.
- **Recommendation**: Add API tests. Uncomment CDK tests. Add Newman collections.
- **Evidence**: `test/aws-microservices.test.ts`, `jest.config.js`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: RISK
- **Finding**: DynamoDB uses default AWS-owned encryption (no customer-managed KMS). SQS OrderQueue has no encryption. Order PII (cardInfo, email) not encrypted with customer-managed keys.
- **Gap**: No customer-managed encryption. SQS unencrypted at rest.
- **Recommendation**: Enable KMS encryption on DynamoDB and SQS.
- **Evidence**: `lib/database.ts`, `lib/queue.ts`

#### ENG-Q6: Cross-Origin and Network Policies
- **Severity**: BLOCKER
- **Finding**: No CORS on any API Gateway. No VPC attachment for Lambdas. No WAF. No API Gateway resource policies. No security groups. APIs publicly accessible with no network restrictions.
- **Gap**: No CORS, no network security, no access restrictions.
- **Recommendation**: Add resource policies. Configure CORS. Deploy WAF. Consider VPC endpoints.
- **Evidence**: `lib/apigateway.ts`, `lib/microservice.ts`

## Evidence Index

### Infrastructure as Code
| File | Questions Referenced |
|------|---------------------|
| `lib/aws-microservices-stack.ts` | HITL-Q2, OBS-Q2, OBS-Q3, ENG-Q1 |
| `lib/apigateway.ts` | API-Q1, API-Q2, API-Q5, API-Q9, AUTH-Q1, AUTH-Q3, AUTH-Q5, AUTH-Q8, STATE-Q5, ENG-Q6 |
| `lib/database.ts` | DATA-Q1, DATA-Q2, DATA-Q4, DATA-Q5, DISC-Q1, DISC-Q2, ENG-Q3, ENG-Q5, STATE-Q5, STATE-Q7 |
| `lib/eventbus.ts` | API-Q8, AUTH-Q2, DISC-Q4 |
| `lib/microservice.ts` | API-Q10, AUTH-Q2, AUTH-Q6, AUTH-Q7, OBS-Q1, STATE-Q7, ENG-Q6 |
| `lib/queue.ts` | API-Q7, STATE-Q1, STATE-Q7, ENG-Q5 |
| `bin/aws-microservices.ts` | DATA-Q2, HITL-Q3 |
| `cdk.json` | ENG-Q1 |

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `src/product/index.js` | API-Q1, API-Q3, API-Q4, API-Q6, AUTH-Q3, STATE-Q3, STATE-Q6, DATA-Q3, DATA-Q5, DATA-Q7, DATA-Q8, DISC-Q2, OBS-Q1 |
| `src/product/ddbClient.js` | STATE-Q4 |
| `src/basket/index.js` | API-Q1, API-Q3, API-Q4, API-Q6, API-Q7, API-Q8, AUTH-Q4, AUTH-Q5, STATE-Q1, STATE-Q3, STATE-Q6, DATA-Q1, DATA-Q3, DATA-Q4, DATA-Q5, DATA-Q7, DATA-Q8, DISC-Q2, DISC-Q4, HITL-Q1, HITL-Q2, OBS-Q1, OBS-Q3 |
| `src/basket/ddbClient.js` | STATE-Q4 |
| `src/basket/eventBridgeClient.js` | STATE-Q4 |
| `src/ordering/index.js` | API-Q1, API-Q3, API-Q6, API-Q7, AUTH-Q4, STATE-Q1, STATE-Q2, STATE-Q6, DATA-Q3, DATA-Q5, DATA-Q7, DATA-Q8, DISC-Q2, OBS-Q1, OBS-Q3 |
| `src/ordering/ddbClient.js` | STATE-Q4 |

### CI/CD Configurations
No CI/CD configuration files found. This absence is itself evidence for: ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4.

### Container Definitions
No container definition files found. This absence is noted for infrastructure assessment.

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `package.json` | ENG-Q2, ENG-Q4, STATE-Q7 |
| `src/product/package.json` | STATE-Q7 |
| `src/basket/package.json` | STATE-Q7 |
| `src/ordering/package.json` | STATE-Q7 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `tsconfig.json` | ENG-Q1 |
| `jest.config.js` | ENG-Q4 |
| `src/basket/checkoutbasketevents.json` | API-Q8 |
| `README.md` | API-Q1, ENG-Q3, DISC-Q4 |

### Test Files
| File | Questions Referenced |
|------|---------------------|
| `test/aws-microservices.test.ts` | ENG-Q4, HITL-Q3 |

### API Specifications
No API specification files found. This absence is evidence for: API-Q2, DISC-Q1.

---

*End of Agentic Readiness Assessment Report*
