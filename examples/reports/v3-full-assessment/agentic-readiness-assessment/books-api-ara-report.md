# Agentic Readiness Assessment Report

**Target**: ./services/books-api
**Date**: 2026-04-27
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P1
**Tags**: serverless, cdk, api, dynamodb
**Context**: Serverless REST API with CDK infrastructure for book catalog management. Clean API surface the agent can use as a tool for product lookups.

**Archetype Justification**: Application has a DynamoDB table (BooksTable) with both read (scan via GET /books) and write (putItem via POST /books) operations exposed via REST API endpoints, managing book entity lifecycle. Matches stateful-crud pattern.

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 2 | **RISK-SAFETY**: 8 | **RISK-QUALITY**: 13 | **INFOs**: 15

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days. The two BLOCKERs (AUTH-Q1: Machine Identity Authentication, DATA-Q1: Sensitive Data Classification) must be remediated before this Books API can be safely integrated as an agent tool in the e-commerce platform customer support agent workflow.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 2 |
| RISK-SAFETY | 8 |
| RISK-QUALITY | 13 |
| INFO | 15 |
| N/A | 0 |
| Not Evaluated (extended) | 5 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 14
**Extended Questions Not Triggered**: 5
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: stateful-crud (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: The application uses Amazon Cognito User Pool (`CognitoUserPool` in `template.yml`) with `UserPoolClient` configured for OAuth implicit flow and `ALLOW_USER_PASSWORD_AUTH` (staging only). The Cognito pool is configured for human users with email/password authentication. The `CognitoAuth` authorizer is applied only to `POST /books`; `GET /books` has no authentication at all. No service account, client credentials OAuth 2.0 flow, API key with principal attribution, or mTLS configuration was found. There is no mechanism for an agent to authenticate with a machine identity that can be attributed in audit logs.
- **Gap**: No machine identity authentication mechanism exists. Cognito is configured exclusively for human users (email-based signup). An agent cannot authenticate as a distinct machine principal. The GET /books endpoint is completely unauthenticated, which means any caller — agent or otherwise — can access it without identity attribution.
- **Remediation**:
  - **Immediate**: Add an API Gateway API Key or IAM authorization to the GET /books endpoint. For agent integration, configure a Cognito App Client with `client_credentials` grant type (requires a Cognito Resource Server) or add API Gateway IAM authorization with a dedicated IAM role for the agent.
  - **Target State**: A dedicated machine identity (service account or API key with principal attribution) that the agent uses to authenticate. All API calls — including GET /books — require authentication, and the authenticated principal is recorded in API Gateway access logs and CloudWatch.
  - **Estimated Effort**: Medium (2–4 weeks)
  - **Dependencies**: AUTH-Q6 (audit logging) — once machine identity exists, audit logs must capture it.
- **Evidence**: `template.yml` (CognitoUserPool, UserPoolClient, BooksApi Auth section, GetAllBooks Events — no Auth block)

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: The DynamoDB table `BooksTable` in `template.yml` has tags for `project` and `environment` but no data classification tags (e.g., `data-classification: public`, `contains-pii: false`). The book data schema includes fields: `isbn`, `title`, `year`, `author`, `publisher`, `rating`, `pages`. While these fields appear to be non-PII reference/catalog data, there is no formal classification confirming this. No Amazon Macie integration was found. No field-level encryption or access controls exist beyond table-level IAM policies. SSE is enabled (`SSEEnabled: true`) but this is encryption at rest, not data classification.
- **Gap**: Sensitive data is not classified or tagged at the field level. Without formal classification, there is no enforceable control preventing an agent from retrieving data that may be reclassified as sensitive in the future. In the context of the e-commerce platform portfolio, the book catalog data must be explicitly classified to confirm it is safe for agent consumption without data handling restrictions.
- **Remediation**:
  - **Immediate**: Add data classification tags to the DynamoDB table in `template.yml`: `data-classification: public` (or appropriate level), `contains-pii: false`, `data-owner: <team>`. Document the data classification decision.
  - **Target State**: All data stores have classification tags. A data classification policy defines what agents can access at each classification level. If future data additions introduce PII (e.g., customer reviews with names), field-level controls are in place.
  - **Estimated Effort**: Low (1–2 weeks for tagging; medium for establishing classification policy)
  - **Dependencies**: DATA-Q6 (PII in logs) — classification informs what must be redacted.
- **Evidence**: `template.yml` (BooksTable resource — tags section has only `project` and `environment`)

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Lambda function-level IAM policies in `template.yml` are reasonably scoped: `GetAllBooks` uses `DynamoDBReadPolicy` (read-only) and `CreateBook` uses `DynamoDBWritePolicy` (write-only). However, `CreateBookPreTraffic` uses `DynamoDBCrudPolicy` (full CRUD — broader than needed for a smoke test). Pipeline CDK (`pipeline/lib/pipeline-stack.ts`) grants `FullAccess` managed policies to the deploy project role: `AWSCloudFormationFullAccess`, `AmazonDynamoDBFullAccess`, `AWSLambda_FullAccess`, `AmazonAPIGatewayAdministrator`, `IAMFullAccess`, `AWSCodeDeployFullAccess`, `AmazonCognitoPowerUser`. These are wildcard permissions with no resource scoping.
- **Gap**: No agent-specific IAM role with scoped permissions exists. Pipeline permissions are excessively broad (`*FullAccess`). There is no mechanism to grant an agent read-only access to specific resources without inheriting broader privileges.
- **Compensating Controls**:
  - Create a dedicated IAM role for agent access with only `dynamodb:Scan` and `dynamodb:GetItem` on the specific BooksTable ARN.
  - Use API Gateway resource policies to restrict agent access to GET /books only.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a dedicated agent IAM role with least-privilege permissions scoped to the BooksTable. Narrow pipeline permissions to specific resource ARNs.
- **Evidence**: `template.yml` (DynamoDBReadPolicy, DynamoDBWritePolicy, DynamoDBCrudPolicy), `pipeline/lib/pipeline-stack.ts` (FullAccess managed policies)

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: `POST /books` requires Cognito authorization with `email` scope. `GET /books` is public with no authorization. IAM policies on Lambda functions are action-scoped (read vs. write). However, there is no fine-grained ABAC or action-level middleware within the Lambda code itself. The Cognito authorization uses OAuth scopes (`email`, `aws.cognito.signin.user.admin`) but these are user identity scopes, not action-level permission scopes (e.g., `books:read`, `books:write`).
- **Gap**: No action-level authorization that could allow an agent to read records but not write/delete them within the same API. Authorization is binary: either no auth (GET) or Cognito token required (POST). No fine-grained permission model.
- **Compensating Controls**:
  - For read-only agent scope, restrict agent access to GET endpoints only via API Gateway resource policy.
  - Define custom Cognito resource scopes (`books:read`, `books:write`) to enable action-level authorization.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Define Cognito Resource Server with custom scopes (`books:read`, `books:write`). Add authorization to GET /books. Configure agent's app client to only have `books:read` scope.
- **Evidence**: `template.yml` (BooksApi Auth section, CreateBook Auth with `email` scope, GetAllBooks with no Auth)

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: API Gateway access logging is configured in `template.yml` with `LoggingLevel: INFO` on all resources/methods, and a `CloudWatchRoleArn` is set via `ApiGatewayLoggingRole`. Lambda functions have X-Ray tracing enabled (`Tracing: Active`). However, no CloudTrail configuration exists in the IaC. No immutable log storage (S3 bucket with object lock) is configured. No CloudTrail log file validation is enabled. API Gateway logs are sent to CloudWatch but CloudWatch logs are mutable and have no tamper-evident protections.
- **Gap**: No immutable, tamper-evident audit trail exists. API Gateway logs go to CloudWatch (mutable). No CloudTrail captures API-level events. No S3 bucket with object lock for log archival.
- **Compensating Controls**:
  - Enable CloudTrail at the AWS account level (outside this stack) to capture API Gateway management events.
  - Configure CloudWatch log retention policies with appropriate retention periods.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add CloudTrail trail to the SAM template or reference an account-level trail. Configure S3 bucket with object lock for log immutability. Enable CloudTrail log file validation.
- **Evidence**: `template.yml` (ApiGwAccountConfig, ApiGatewayLoggingRole, MethodSettings LoggingLevel)

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Cognito User Pool exists (`CognitoUserPool` in `template.yml`) and supports `adminDisableUser` to disable individual users. However, since no machine identity authentication exists (see AUTH-Q1 BLOCKER), there is no agent identity to suspend. If an agent were to use a Cognito user account, it could be disabled via `adminDisableUser`. No API key-based authentication is configured, so API key revocation is not available. No dedicated agent identity suspension mechanism exists.
- **Gap**: No agent-specific identity exists to suspend. The prerequisite (AUTH-Q1) must be resolved first. Once machine identity is established, a suspension mechanism must be defined.
- **Compensating Controls**:
  - When AUTH-Q1 is resolved: if using API key auth, configure API Gateway to support key revocation. If using IAM roles, define a runbook for role deactivation.
  - Implement CloudWatch alarm on agent traffic anomalies to trigger suspension.
- **Remediation Timeline**: 60–90 days (dependent on AUTH-Q1 resolution)
- **Recommendation**: Resolve AUTH-Q1 first. Then define agent identity suspension runbook: API key deletion, IAM role deactivation, or Cognito app client disable — depending on chosen auth mechanism.
- **Evidence**: `template.yml` (CognitoUserPool — supports adminDisableUser but no agent identity configured)

#### STATE-Q1: Compensation and Rollback ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No application-level compensation or rollback logic was found. `src/books/create/index.ts` performs a DynamoDB `putItem` with no conditional expressions, no saga pattern, and no undo endpoint. The `CreateBookPreTraffic` function (`src/books/create-pre-traffic/index.ts`) performs a smoke test with cleanup (inserts and deletes a test book), but this is deployment-level validation, not application-level compensation. No Step Functions, no compensating transactions, no explicit undo endpoints exist.
- **Gap**: No compensation or rollback mechanism for multi-step operations. If a write operation partially succeeds (in a future multi-step workflow), the system cannot undo it.
- **Compensating Controls**:
  - For read-only agent scope, this risk is mitigated: the agent will not execute write operations that require rollback.
  - DynamoDB `putItem` is inherently idempotent (overwrites), which reduces data corruption risk.
- **Remediation Timeline**: 60–90 days (when agent scope expands to write-enabled)
- **Recommendation**: Before expanding agent scope to write-enabled, implement conditional writes with version tracking in DynamoDB. Consider adding a `DELETE /books/{isbn}` endpoint for explicit compensation.
- **Evidence**: `src/books/create/index.ts` (putItem with no conditional logic), `src/books/create-pre-traffic/index.ts` (deployment-only smoke test)

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No explicit rate limiting or throttling configuration was found in `template.yml`. The API Gateway (`BooksApi`) does not define a usage plan, throttle settings, or API keys for rate control. No WAF rate rules are configured. No application-level rate limiting middleware exists in the Lambda functions. API Gateway provides default account-level throttling (10,000 requests/second, 5,000 burst) but no custom per-client or per-endpoint limits are defined.
- **Gap**: No rate limiting prevents a runaway agent loop from overwhelming the API. Default API Gateway account-level limits exist but are not customized for this API and provide no per-client differentiation.
- **Compensating Controls**:
  - API Gateway default account-level throttling provides a baseline safety net.
  - Lambda concurrency limits (not currently configured) could cap invocations.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `UsagePlan` and `ApiKey` resources to `template.yml` with per-key throttle settings. Define agent-specific usage plans. Consider adding Lambda reserved concurrency to cap function invocations.
- **Evidence**: `template.yml` (BooksApi — no ThrottleSettings, no UsagePlan, no ApiKey resources)

#### DATA-Q2: Data Residency and Sovereignty ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No data residency or sovereignty requirements are documented. The DynamoDB table is deployed to the region specified during `sam deploy` (via `--region $AWS_REGION` in `pipeline/buildspec-deploy.json`). No cross-region replication is configured. No GDPR, LGPD, or HIPAA references exist in the codebase. The book catalog data (isbn, title, year, author, publisher, rating, pages) appears to be public reference data not subject to data residency requirements.
- **Gap**: No explicit data residency policy is documented. While book catalog data is likely not regulated, the absence of formal documentation means there is no enforceable control preventing future data additions from violating residency requirements when consumed by an agent that forwards data to an LLM endpoint.
- **Compensating Controls**:
  - Book catalog data (titles, ISBNs, authors) is public reference data — residency risk is minimal.
  - Document the data residency classification as part of DATA-Q1 remediation.
- **Remediation Timeline**: 30 days (as part of data classification effort)
- **Recommendation**: Document data residency classification alongside DATA-Q1. If the agent sends book data to Bedrock (same region), residency concerns are mitigated. If using external LLM providers, confirm no residency constraints apply.
- **Evidence**: `template.yml` (BooksTable — single-region DynamoDB), `pipeline/buildspec-deploy.json` (region-based deployment)

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No log scrubbing or PII masking middleware exists. In `src/books/create-pre-traffic/index.ts`, DynamoDB items are logged directly: `console.log('DynamoDB item', JSON.stringify(Item, null, 2))` — this outputs book data (isbn, title, author) to CloudWatch Logs without filtering. The main Lambda functions (`create/index.ts`, `get-all/index.ts`) have empty catch blocks that do not log errors, so they do not leak data through error logging. However, there are no CloudWatch log filters for PII detection, no log masking libraries, and no Amazon Macie integration.
- **Gap**: No PII redaction controls exist in the logging pipeline. While current book data (isbn, title, author) is not PII, the logging pattern of dumping full DynamoDB items to CloudWatch would expose PII if the data schema ever includes customer information (e.g., reviewer names, email addresses). No preventive controls exist.
- **Compensating Controls**:
  - Current book catalog data does not contain PII — immediate risk is low.
  - Restrict CloudWatch log access to authorized principals only.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add structured logging that explicitly selects which fields to log (allowlist approach) rather than dumping full items. Add CloudWatch Logs data protection policies to detect and mask PII patterns. Remove `console.log('DynamoDB item', JSON.stringify(Item))` from pre-traffic hook or replace with selective field logging.
- **Evidence**: `src/books/create-pre-traffic/index.ts` (line: `console.log('DynamoDB item', JSON.stringify(Item, null, 2))`), `src/books/create/index.ts` (empty catch block), `src/books/get-all/index.ts` (empty catch block)

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, GraphQL schema, or Smithy model files were found in the repository. The `template.yml` sets `OpenApiVersion: 3.0.1` in the Globals section but this is only to prevent SAM from creating a default API Gateway stage — it does not define an inline OpenAPI specification. The API endpoints are defined implicitly through SAM event sources (`Path: /books`, `Method: get/post`) but there is no standalone machine-readable specification document.
- **Gap**: No machine-readable API specification exists. Agent tool definitions must be manually authored by inspecting the SAM template and Lambda code. The specification will drift from implementation over time.
- **Compensating Controls**:
  - SAM template defines the API structure — an OpenAPI spec can be generated from the template and code.
  - The API surface is small (2 endpoints) — manual tool definition is feasible for initial pilot.
- **Remediation Timeline**: 30 days
- **Recommendation**: Add an inline OpenAPI definition to `template.yml` under `BooksApi.Properties.DefinitionBody` or create a standalone `openapi.yaml` file. Define request/response schemas for both endpoints.
- **Evidence**: `template.yml` (OpenApiVersion: 3.0.1 — not an actual spec), repository root (no openapi.yaml/json, no swagger files)

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Both Lambda functions return unstructured error responses. In `src/books/create/index.ts`, the catch block returns `{ statusCode: 500, headers: {}, body: '' }` — an empty body with no error code, message, or retryable indicator. In `src/books/get-all/index.ts`, the same pattern: `{ statusCode: 500, headers: {}, body: '' }`. An agent receiving a 500 with an empty body cannot distinguish between a transient DynamoDB timeout (retryable) and a permanent schema error (terminal).
- **Gap**: No structured error response format. No error codes, no error messages, no retryable boolean. Agents must treat all 500 errors identically.
- **Compensating Controls**:
  - The API surface is simple enough that most errors will be DynamoDB failures (typically retryable).
  - Agent orchestration layer can implement retry-with-backoff for all 500s.
- **Remediation Timeline**: 30 days
- **Recommendation**: Define a standard error response format: `{ "error": { "code": "DYNAMODB_ERROR", "message": "...", "retryable": true } }`. Implement in both Lambda handlers. Differentiate between input validation errors (400), auth errors (401/403), and server errors (500).
- **Evidence**: `src/books/create/index.ts` (catch block — statusCode 500, empty body), `src/books/get-all/index.ts` (catch block — statusCode 500, empty body)

#### AUTH-Q4: Identity Propagation and Delegation — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The `CognitoAuth` authorizer validates tokens at the API Gateway layer for `POST /books`, but the Lambda function code (`src/books/create/index.ts`) does not extract or propagate the caller's identity. The `event` parameter is typed as `any` and only `event.body` is accessed — `event.requestContext.authorizer` claims are ignored. No user context is passed to DynamoDB operations. The `GET /books` endpoint has no authentication, so no identity exists to propagate.
- **Gap**: Caller identity is not propagated from API Gateway to the Lambda function or data layer. The system cannot distinguish between an agent acting under its own identity vs. acting on behalf of a user.
- **Compensating Controls**:
  - For read-only agent scope accessing public catalog data, identity propagation is low-priority.
  - API Gateway access logs capture the caller's source IP and authorization header.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Extract `event.requestContext.authorizer.claims` in Lambda handlers to identify the caller. Log the caller identity for audit purposes. Pass user context to DynamoDB operations via condition expressions or audit fields.
- **Evidence**: `src/books/create/index.ts` (event.body parsed, no requestContext access), `template.yml` (CognitoAuth authorizer on POST /books)

#### AUTH-Q5: Credential Management — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No hardcoded credentials were found in source code. Lambda environment variables contain only non-sensitive configuration (`TABLE` = DynamoDB table name). The pipeline CDK (`pipeline/lib/pipeline-stack.ts`) uses SSM Parameter Store for the GitHub connection ARN: `StringParameter.fromStringParameterName(this, 'GithubConnectionArn', 'github_connection_arn')`. No `.env` files are committed. No AWS Secrets Manager or HashiCorp Vault integration exists. No secret rotation configuration.
- **Gap**: No formal secrets management system is in use for application secrets. While the current application has no application-level secrets (DynamoDB access is via IAM roles, Cognito is via resource references), there is no established pattern for secrets management if future features require API keys, third-party credentials, or other secrets.
- **Compensating Controls**:
  - IAM roles provide credential-free DynamoDB access — no application secrets needed currently.
  - SSM Parameter Store is used for pipeline secrets.
- **Remediation Timeline**: 30 days (establish pattern before secrets are needed)
- **Recommendation**: When agent machine identity is established (AUTH-Q1 resolution), use AWS Secrets Manager with automatic rotation for any API keys or client secrets. Document the secrets management pattern for the team.
- **Evidence**: `src/books/create/index.ts` (TABLE env var only), `pipeline/lib/pipeline-stack.ts` (SSM for GitHub ARN), repository-wide search (no hardcoded secrets)

#### STATE-Q2: Queryable Current State — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: `GET /books` performs a DynamoDB `scan` and returns all books. There is no `GET /books/{isbn}` endpoint for querying a specific book's current state. An agent can retrieve the full list but cannot query a single book by ISBN without fetching the entire table.
- **Gap**: Limited queryability — only a full table scan is available. No single-item query endpoint exists. An agent needing to check if a specific book exists or retrieve its current state must scan all records.
- **Compensating Controls**:
  - The full scan includes all books — an agent can filter client-side for a specific ISBN.
  - For a small catalog, full scan is acceptable in terms of performance.
- **Remediation Timeline**: 30 days
- **Recommendation**: Add a `GET /books/{isbn}` endpoint backed by DynamoDB `getItem` for single-item queries. This enables agents to check specific book state without full table scans.
- **Evidence**: `src/books/get-all/index.ts` (DynamoDB scan, no item-level query), `template.yml` (only `/books` path, no `/{isbn}` path)

#### DATA-Q3: Selective Query Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The `GET /books` endpoint (`src/books/get-all/index.ts`) performs an unbounded DynamoDB `scan` with no pagination, filtering, or sorting parameters. The scan parameters are: `{ TableName: process.env.TABLE || 'books' }` — no `Limit`, `ExclusiveStartKey`, `FilterExpression`, or `ProjectionExpression`. All records are returned in a single response. For large catalogs, this would exhaust LLM context windows and increase token cost.
- **Gap**: No pagination (`limit`, `offset`, `cursor`), no filtering, no sorting. Results are unbounded. DynamoDB scan returns up to 1MB per call — with no `LastEvaluatedKey` handling, large tables would silently return partial results.
- **Compensating Controls**:
  - For a small book catalog, unbounded scan is functionally acceptable.
  - Agent orchestration layer can truncate large responses before sending to LLM.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add pagination support: accept `limit` and `cursor` (LastEvaluatedKey) query parameters. Add `FilterExpression` support for server-side filtering by author, title, or year. Return pagination metadata in the response body.
- **Evidence**: `src/books/get-all/index.ts` (DynamoDB scan — no Limit, no ExclusiveStartKey, no FilterExpression)

#### DATA-Q4: System of Record Designations — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No system-of-record designation was found for the book entity. The DynamoDB table (`BooksTable`) is the only data store for book data. No documentation identifies this service as the authoritative source for book catalog information. No master data management process exists. No conflict resolution logic.
- **Gap**: No formal system-of-record designation. In the e-commerce platform portfolio, if multiple services store book data (e.g., inventory service, recommendation service), an agent querying across services will encounter conflicting records with no way to determine the authoritative source.
- **Compensating Controls**:
  - This service appears to be the only book data store — de facto system of record.
  - Small API surface reduces cross-system conflict risk.
- **Remediation Timeline**: 30 days
- **Recommendation**: Document the Books API as the system of record for book catalog data in the portfolio architecture documentation. Add this designation to the API specification or README.
- **Evidence**: `template.yml` (BooksTable — single data store), README.md (no system-of-record designation)

#### DATA-Q5: Temporal Metadata and Freshness — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The DynamoDB item schema includes: `isbn`, `title`, `year`, `author`, `publisher`, `rating`, `pages`. No temporal metadata fields exist — no `created_at`, `updated_at`, or `event_time`. The `year` field is the book's publication year, not a record timestamp. No `Cache-Control`, `ETag`, or `Last-Modified` headers are returned in API responses. No freshness signaling (e.g., `X-Data-Age`, `consistency_level`).
- **Gap**: No temporal metadata on records. An agent cannot determine when a book record was created, last updated, or whether the data is current. No cache headers to signal data freshness.
- **Compensating Controls**:
  - Book catalog data is relatively static — temporal concerns are lower than for transactional data.
  - DynamoDB consistent reads can be used if added to the scan.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `created_at` and `updated_at` fields (ISO 8601 UTC) to the DynamoDB item schema. Set `updated_at` on every putItem. Return `Last-Modified` and `Cache-Control` headers in GET responses.
- **Evidence**: `src/books/create/index.ts` (Item schema — no timestamp fields), `src/books/get-all/index.ts` (response — no cache headers)

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No API versioning exists — endpoints are `/books` with no version prefix (`/v1/books`). No OpenAPI spec is maintained (see API-Q2). No schema registry. No breaking change detection in the CI pipeline. No consumer-driven contract tests (Pact). The CI pipeline runs unit tests and e2e tests but does not validate API contract stability. No changelog or deprecation notice mechanism exists.
- **Gap**: No schema versioning, no API contracts, no breaking change detection. Agent tool bindings would break silently if the API response schema changes (e.g., field renamed from `isbn` to `book_isbn`).
- **Compensating Controls**:
  - The API surface is small and stable (2 endpoints) — breaking changes are unlikely in the short term.
  - E2E tests validate response schema implicitly (tests check specific fields).
- **Remediation Timeline**: 60 days
- **Recommendation**: Add URL-based versioning (`/v1/books`). Create an OpenAPI spec (linked to API-Q2 remediation). Add OpenAPI diff checking to CI pipeline to detect breaking changes before deployment.
- **Evidence**: `template.yml` (Path: /books — no version prefix), `pipeline/buildspec.json` (no contract test step), `src/books/tests/index.js` (e2e tests — implicit schema validation only)

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: X-Ray tracing is properly configured: `Tracing: Active` on both Lambda functions (Globals section in `template.yml`), `TracingEnabled: true` on the API Gateway (`BooksApi`). Both `create/index.ts` and `get-all/index.ts` use `AWSXRay.captureAWS(AWSCore)` to instrument AWS SDK calls. Trace ID propagation through API Gateway → Lambda → DynamoDB is enabled. However, application logging uses unstructured `console.log` (in `create-pre-traffic/index.ts`) with no JSON formatting, no correlation IDs, and no request_id fields. The main Lambda handlers have no application-level logging at all.
- **Gap**: Distributed tracing is well-implemented. Structured logging is absent — no JSON log format, no correlation IDs linking logs to traces. Agent-initiated requests can be traced via X-Ray but application-level log correlation is missing.
- **Compensating Controls**:
  - X-Ray provides full request tracing from API Gateway through Lambda to DynamoDB.
  - Lambda automatically adds requestId to CloudWatch Logs — basic correlation is available.
- **Remediation Timeline**: 30 days
- **Recommendation**: Add a structured logging library (e.g., `@aws-lambda-powertools/logger`) to emit JSON-formatted logs with X-Ray trace ID, request ID, and custom fields. This enables correlating logs with traces for agent-initiated requests.
- **Evidence**: `template.yml` (Tracing: Active, TracingEnabled: true), `src/books/create/index.ts` (AWSXRay.captureAWS), `src/books/get-all/index.ts` (AWSXRay.captureAWS), `src/books/create-pre-traffic/index.ts` (console.log — unstructured)

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Two CloudWatch alarms are configured in `template.yml`: `CreateBookAliasErrorMetricGreaterThanZeroAlarm` and `GetAllBooksAliasErrorMetricGreaterThanZeroAlarm`. Both monitor Lambda `Errors` metric with threshold > 0, evaluated over 2 periods of 60 seconds. These alarms are wired to CodeDeploy `DeploymentPreference.Alarms` for automatic deployment rollback. No latency alarms exist. No anomaly detection. No PagerDuty, OpsGenie, or SNS notification integration for operational alerting.
- **Gap**: Error alarms exist but are deployment-scoped (rollback triggers), not operational alerting. No latency alarms. No anomaly detection for unusual traffic patterns (e.g., agent-generated traffic spikes). No notification channel for ops teams.
- **Compensating Controls**:
  - Deployment alarms provide automatic rollback for error spikes — this protects against broken deploys.
  - API Gateway metrics are available in CloudWatch for manual monitoring.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add operational CloudWatch alarms: (1) API Gateway 5xx rate > threshold, (2) API Gateway p99 latency > threshold, (3) Lambda throttle count > 0. Connect alarms to SNS topic for team notification.
- **Evidence**: `template.yml` (CreateBookAliasErrorMetricGreaterThanZeroAlarm, GetAllBooksAliasErrorMetricGreaterThanZeroAlarm — deployment-scoped)

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Infrastructure is fully defined as code: SAM template (`template.yml`) for the application stack and CDK (`pipeline/lib/pipeline-stack.ts`) for the CI/CD pipeline. Sub-checks: (1) **IaC defined**: YES — all resources (API Gateway, Lambda, DynamoDB, Cognito, CloudWatch alarms) are in `template.yml`. (2) **Peer review**: The repository is GitHub-based with a CodeStar connection for source control. The pipeline has a manual approval step before production deployment. However, no branch protection rules or PR review requirements are configured in the repository (not enforceable from IaC). (3) **Drift detection**: No AWS Config rules or CloudFormation drift detection is configured.
- **Gap**: IaC is present. Peer review and drift detection are not enforced. Two of three sub-checks are gaps.
- **Compensating Controls**:
  - Manual approval step in pipeline provides a human gate before production deployment.
  - SAM/CloudFormation deployments provide declarative state management — drift requires manual intervention.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Enable GitHub branch protection rules requiring PR reviews for `main` branch. Enable CloudFormation drift detection via AWS Config rules or scheduled drift detection checks.
- **Evidence**: `template.yml` (full IaC), `pipeline/lib/pipeline-stack.ts` (ManualApprovalAction), repository config (no branch protection rules visible)

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: A full CI/CD pipeline exists (`pipeline/lib/pipeline-stack.ts`): Source → Build (unit tests + SAM build) → Staging (deploy + e2e tests) → Production (manual approval + deploy). Unit tests (`src/books/create/tests/index.spec.ts`, `src/books/get-all/tests/index.spec.ts`) run in the Build phase via `pipeline/buildspec.json`. E2E tests (`src/books/tests/index.js`) run against staging via `pipeline/buildspec-test.json`. However, no API contract tests (Pact), no OpenAPI spec validation, no schema comparison tools, and no breaking change detection exist in the pipeline.
- **Gap**: CI/CD pipeline exists with good unit and e2e test coverage but no API contract testing. API-breaking changes would not be caught until e2e tests detect behavioral differences — and only if test assertions cover the affected fields.
- **Compensating Controls**:
  - E2E tests validate API behavior including response schema fields (isbn, title, year, etc.).
  - Manual approval gate before production provides human verification.
- **Remediation Timeline**: 60 days
- **Recommendation**: Add OpenAPI spec validation to the Build phase. Implement contract testing (Pact or similar) for agent consumers. Add schema diff checking when OpenAPI spec is introduced (linked to API-Q2).
- **Evidence**: `pipeline/lib/pipeline-stack.ts` (full pipeline), `pipeline/buildspec.json` (unit tests), `pipeline/buildspec-test.json` (e2e tests), `src/books/tests/index.js` (e2e test assertions)

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO (Passed — not a blocker)
- **Finding**: The application exposes a documented REST API via Amazon API Gateway (`BooksApi` in `template.yml`). Two endpoints are defined: `GET /books` (retrieve all books) and `POST /books` (create a book). Lambda functions serve as handlers: `GetAllBooks` and `CreateBook`. No direct database access, file-based exchange, or UI automation patterns were found. The API is the sole integration surface.
- **Implication**: The API surface is clean and agent-compatible. Two REST endpoints with JSON responses provide a straightforward integration surface for agent tool binding. The `GET /books` endpoint is the primary tool for a read-only product lookup agent.
- **Recommendation**: This question is satisfied. Consider adding a `GET /books/{isbn}` endpoint for single-item lookups (related to STATE-Q2).
- **Evidence**: `template.yml` (BooksApi, GetAllBooks Events, CreateBook Events)

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: `src/books/create/index.ts` uses DynamoDB `putItem` with `isbn` as the partition key. DynamoDB `putItem` is inherently idempotent — calling it twice with the same `isbn` overwrites the record rather than creating a duplicate. No explicit idempotency key support (e.g., `Idempotency-Key` header) exists in the API. No conditional write expressions are used.
- **Implication**: For read-only agent scope, idempotency is informational only. If agent scope expands to write-enabled, the inherent idempotency of `putItem` provides baseline safety, but an explicit idempotency key mechanism should be added for richer write operations.
- **Recommendation**: If scope expands to write-enabled, add explicit idempotency key support for the POST endpoint.
- **Evidence**: `src/books/create/index.ts` (DynamoDB putItem with isbn as key)

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: `GET /books` returns `Content-Type: application/json` with `JSON.stringify(bookDtos)` — well-structured JSON array of book objects. `POST /books` returns `Content-Type: application/json` with an empty body and status 201. All responses are JSON-formatted and text-based.
- **Implication**: JSON responses are ideal for LLM consumption. The response format requires no special parsing. Agent tools can bind directly to the JSON response schema: `{ isbn, title, year, author, publisher, rating, pages }`.
- **Recommendation**: Add response body to POST /books (return the created book object) for confirmation. This helps agents verify successful writes.
- **Evidence**: `src/books/get-all/index.ts` (JSON.stringify with Content-Type: application/json), `src/books/create/index.ts` (empty body with 201)

### API-Q7: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: No event emission for state changes was found. The `POST /books` endpoint writes to DynamoDB but does not publish events to SNS, EventBridge, SQS, or Kafka. No DynamoDB Streams are enabled on `BooksTable`. No webhook endpoints exist.
- **Implication**: The system is request/response only. A proactive agent that needs to react to new book additions (e.g., notify customers about new inventory) would need to poll the GET endpoint. Consider adding DynamoDB Streams with EventBridge integration if event-driven agent workflows are needed.
- **Recommendation**: Enable DynamoDB Streams on `BooksTable` and publish change events to EventBridge for future event-driven agent patterns.
- **Evidence**: `template.yml` (BooksTable — no StreamSpecification, no SNS/EventBridge resources)

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limit documentation or headers are configured. The API Gateway does not define custom throttle settings or usage plans. No `X-RateLimit-Remaining`, `X-RateLimit-Limit`, or `Retry-After` headers are returned in API responses. API Gateway default account-level throttling (10,000 rps / 5,000 burst) applies but is not documented or surfaced to clients.
- **Implication**: Agents calling this API at machine speed have no visibility into rate limits. They will receive 429 responses without `Retry-After` guidance when limits are hit. This forces agents to implement blind backoff strategies.
- **Recommendation**: When rate limiting is added (STATE-Q5 remediation), include `X-RateLimit-Remaining` and `Retry-After` response headers. Document rate limits in the API specification (API-Q2).
- **Evidence**: `template.yml` (BooksApi — no throttle settings), `src/books/get-all/index.ts` (response headers — no rate limit headers)

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No concurrency controls exist. DynamoDB `putItem` in `src/books/create/index.ts` has no conditional expressions (`ConditionExpression`), no version field, and no `If-Match`/ETag support. Multiple simultaneous writes to the same `isbn` would silently overwrite each other (last-writer-wins).
- **Implication**: For read-only agent scope, concurrency controls for write operations are informational only. If agent scope expands to write-enabled, optimistic locking should be implemented.
- **Recommendation**: Before expanding to write-enabled scope, add a `version` attribute to DynamoDB items and use `ConditionExpression` on putItem to implement optimistic locking.
- **Evidence**: `src/books/create/index.ts` (putItem — no ConditionExpression)

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits exist. No `max_records_per_operation`, `max_spend_per_hour`, or `max_deletes_per_session` configuration. The `GET /books` scan returns all records without limits. The `POST /books` endpoint has no per-identity or per-session write caps.
- **Implication**: For read-only agent scope, transaction limits for write operations are informational only. The unbounded `GET /books` scan is addressed in DATA-Q3 (pagination).
- **Recommendation**: Before expanding to write-enabled scope, implement per-agent-identity limits on write operations.
- **Evidence**: `template.yml` (no transaction limit configuration), `src/books/create/index.ts` (no per-identity limits)

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality metrics, dashboards, profiling reports, or freshness SLAs were found. No null rate monitoring, duplicate detection, or data completeness checks exist. The DynamoDB schema does not enforce field validation (all attributes are accepted as-is in `putItem`).
- **Implication**: An agent consuming book data has no signal about data quality. If records have missing fields (e.g., no publisher), the agent may propagate incomplete information to customers. Planning input for agent design — consider adding input validation.
- **Recommendation**: Add input validation in the `create/index.ts` handler to enforce required fields. Consider adding DynamoDB item-level validation or a data quality check Lambda.
- **Evidence**: `src/books/create/index.ts` (no field validation — destructures and writes directly)

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: All field names are human-readable and semantically meaningful: `isbn`, `title`, `year`, `author`, `publisher`, `rating`, `pages`. No legacy abbreviations or coded values (e.g., `CUST_TYP_CD`). Field names are consistent between the DynamoDB schema, Lambda handlers, and API responses.
- **Implication**: LLM-based agents can interpret field names directly without a data dictionary lookup. This is a positive finding — no remediation needed. The field names are self-documenting and suitable for agent tool description generation.
- **Recommendation**: Maintain current naming conventions. Document field semantics in an OpenAPI spec (linked to API-Q2).
- **Evidence**: `src/books/create/index.ts` (isbn, title, year, author, publisher, rating, pages), `src/books/get-all/index.ts` (same field names in response DTO)

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No data catalog (AWS Glue Data Catalog, Collibra, Alation, DataHub) was found. No metadata files, data dictionaries, or schema documentation exist beyond the DynamoDB table definition in `template.yml` and the field names in source code.
- **Implication**: When building agent tools for this API, developers must inspect source code to understand data semantics. A metadata layer would accelerate tool definition and enable automated tool generation.
- **Recommendation**: Create a lightweight data dictionary (README section or standalone document) describing each field's meaning, type, constraints, and example values. Consider registering the book entity in a centralized data catalog for the e-commerce platform portfolio.
- **Evidence**: Repository root (no data catalog files), `template.yml` (BooksTable — PrimaryKey definition only)

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No custom CloudWatch metrics for business outcomes were found. No `cloudwatch.put_metric_data` calls in Lambda code. No business KPI dashboards (e.g., books created per day, most queried categories, API usage by consumer type). Only infrastructure metrics (Lambda errors) are monitored via CloudWatch alarms.
- **Implication**: When agents consume the Books API, there is no visibility into whether agent interactions produce good business outcomes (e.g., successful product lookups leading to customer satisfaction). Business metrics would help calibrate agent effectiveness.
- **Recommendation**: Add custom CloudWatch metrics: `BooksQueried` (count per request), `BooksCreated` (count per create), `AgentApiCalls` (when agent identity is established). Create a CloudWatch dashboard for business outcomes.
- **Evidence**: `src/books/create/index.ts` (no put_metric_data), `src/books/get-all/index.ts` (no put_metric_data), `template.yml` (no custom metric resources)

### ENG-Q3: Rollback Capability

- **Severity**: INFO (Satisfied)
- **Finding**: Strong rollback capability exists. For production deployments, `DeploymentPreference` is set to `Linear10PercentEvery1Minute` in `template.yml`, enabling gradual traffic shifting with automatic rollback. CloudWatch alarms (`CreateBookAliasErrorMetricGreaterThanZeroAlarm`, `GetAllBooksAliasErrorMetricGreaterThanZeroAlarm`) trigger automatic deployment rollback if errors exceed threshold. The `CreateBookPreTraffic` function performs a pre-traffic smoke test before shifting traffic to the new Lambda version. CodeDeploy manages the deployment lifecycle with rollback triggers.
- **Implication**: The system can be rolled back to the previous version within minutes if a deployment breaks agent-facing APIs. This is a strong engineering practice that exceeds the 15–30 minute target.
- **Recommendation**: This question is well-satisfied. Consider adding integration tests that specifically validate agent-facing API contracts as part of the pre-traffic hook.
- **Evidence**: `template.yml` (DeploymentPreference, Alarms, Hooks), `src/books/create-pre-traffic/index.ts` (smoke test)

### ENG-Q4: API Test Coverage

- **Severity**: INFO (Largely Satisfied)
- **Finding**: Unit tests exist for both Lambda functions: `src/books/create/tests/index.spec.ts` (3 tests: success, invalid body, DynamoDB failure) and `src/books/get-all/tests/index.spec.ts` (3 tests: success, empty result, DynamoDB failure). E2E tests exist in `src/books/tests/index.js` covering: unauthenticated GET, authenticated POST, unauthorized POST rejection, invalid payload handling, and full CRUD flow. Tests run in the CI pipeline (unit tests in Build phase, e2e tests in Staging phase). No API contract tests (Pact) exist.
- **Implication**: Functional test coverage is good for the current API surface. Missing contract tests mean API schema changes could break agent tool bindings without being caught in CI.
- **Recommendation**: Add consumer-driven contract tests for agent consumers when agent integration begins. This ensures agent tool definitions stay in sync with API behavior.
- **Evidence**: `src/books/create/tests/index.spec.ts`, `src/books/get-all/tests/index.spec.ts`, `src/books/tests/index.js`, `pipeline/buildspec.json` (unit tests in CI), `pipeline/buildspec-test.json` (e2e tests in CI)

### ENG-Q5: Encryption at Rest for Agent-Accessible Data

- **Severity**: INFO (Satisfied)
- **Finding**: DynamoDB table `BooksTable` has `SSESpecification: SSEEnabled: true` in `template.yml`, enabling encryption at rest with AWS-managed keys. S3 buckets in the pipeline CDK (`pipeline/lib/pipeline-stack.ts`) use `BucketEncryption.S3_MANAGED` for artifact storage. No customer-managed KMS keys (CMK) are used — all encryption uses AWS-managed keys.
- **Implication**: Data at rest is encrypted. AWS-managed encryption is sufficient for non-regulated book catalog data. If data classification (DATA-Q1) reveals sensitive data, consider upgrading to customer-managed KMS keys for additional key control.
- **Recommendation**: No immediate action needed. If the data classification review identifies sensitive data requiring CMK control, add `SSESpecification.KMSMasterKeyId` to the DynamoDB table definition.
- **Evidence**: `template.yml` (BooksTable SSESpecification: SSEEnabled: true), `pipeline/lib/pipeline-stack.ts` (BucketEncryption.S3_MANAGED)

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO (Passed — BLOCKER criteria satisfied)
- **Finding**: REST API exposed via Amazon API Gateway (`BooksApi` in `template.yml`) with `GET /books` and `POST /books` endpoints. Lambda handlers `GetAllBooks` and `CreateBook` serve requests. No database-direct, file-based, or UI automation integration patterns.
- **Gap**: N/A — API exists and is the sole integration surface.
- **Recommendation**: Add `GET /books/{isbn}` for single-item lookups.
- **Evidence**: `template.yml` (BooksApi, GetAllBooks, CreateBook)

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, GraphQL schema, or Smithy model found. `OpenApiVersion: 3.0.1` in Globals is a SAM configuration directive, not an API specification.
- **Gap**: No machine-readable specification. Agent tool definitions must be manually authored.
- **Recommendation**: Create `openapi.yaml` or add inline OpenAPI definition to `template.yml`.
- **Evidence**: `template.yml` (OpenApiVersion — not a spec), repository root (no spec files)

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: Both handlers return `{ statusCode: 500, headers: {}, body: '' }` on error. No structured error codes, messages, or retryable indicators.
- **Gap**: Empty error bodies. Agents cannot distinguish error types.
- **Recommendation**: Implement structured error format: `{ "error": { "code": "...", "message": "...", "retryable": true/false } }`.
- **Evidence**: `src/books/create/index.ts`, `src/books/get-all/index.ts` (catch blocks)

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: DynamoDB `putItem` with `isbn` as partition key is inherently idempotent. No explicit idempotency key header support.
- **Gap**: No explicit idempotency mechanism (informational for read-only scope).
- **Recommendation**: Add idempotency key support if scope expands to write-enabled.
- **Evidence**: `src/books/create/index.ts` (putItem with isbn key)

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: JSON responses with `Content-Type: application/json`. GET returns JSON array of book objects. POST returns empty body with 201.
- **Gap**: POST returns empty body — no confirmation payload.
- **Recommendation**: Return created book object in POST response body.
- **Evidence**: `src/books/get-all/index.ts`, `src/books/create/index.ts`

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has operations >30s OR long-running workflows. Lambda timeout is 5 seconds; no long-running operations detected.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: No event emission found. POST /books writes to DynamoDB with no SNS, EventBridge, SQS, Kafka, or DynamoDB Streams integration.
- **Gap**: No event-driven capability for state changes.
- **Recommendation**: Enable DynamoDB Streams and EventBridge for event-driven agent patterns.
- **Evidence**: `template.yml` (BooksTable — no StreamSpecification)

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit documentation, usage plans, or rate limit response headers configured. Default API Gateway account-level throttling applies.
- **Gap**: Rate limits not documented or surfaced to clients.
- **Recommendation**: Add usage plans and rate limit headers when rate limiting is implemented.
- **Evidence**: `template.yml` (BooksApi — no throttle settings)

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: Cognito configured for human users (email/password). No machine identity: no client_credentials flow, no API keys with principal attribution, no mTLS. GET /books has no authentication.
- **Gap**: No machine identity authentication. Agent cannot authenticate as a distinct principal.
- **Recommendation**: Add Cognito Resource Server with client_credentials flow or API Gateway IAM/API Key authorization.
- **Evidence**: `template.yml` (CognitoUserPool, UserPoolClient, BooksApi Auth)

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: Lambda IAM policies are function-scoped (DynamoDBReadPolicy, DynamoDBWritePolicy). PreTraffic uses DynamoDBCrudPolicy (broader). Pipeline uses FullAccess managed policies.
- **Gap**: No agent-specific scoped IAM role. Pipeline permissions are wildcard.
- **Recommendation**: Create dedicated agent IAM role with least-privilege permissions.
- **Evidence**: `template.yml` (IAM policies), `pipeline/lib/pipeline-stack.ts` (FullAccess policies)

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: POST requires Cognito auth with `email` scope. GET is public. No fine-grained ABAC, no action-level middleware, no custom OAuth scopes for read/write differentiation.
- **Gap**: No action-level authorization for agent access.
- **Recommendation**: Define Cognito Resource Server with `books:read` and `books:write` scopes.
- **Evidence**: `template.yml` (CreateBook Auth, GetAllBooks — no Auth)

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: RISK-QUALITY
- **Finding**: Cognito authorizer validates tokens at API Gateway. Lambda code does not extract caller identity from `event.requestContext.authorizer.claims`. No identity propagation to data layer.
- **Gap**: Caller identity not propagated from API Gateway to Lambda or DynamoDB.
- **Recommendation**: Extract and log `event.requestContext.authorizer.claims` in Lambda handlers.
- **Evidence**: `src/books/create/index.ts` (only event.body accessed), `template.yml` (CognitoAuth)

#### AUTH-Q5: Credential Management
- **Severity**: RISK-QUALITY
- **Finding**: No hardcoded credentials. TABLE env var is non-sensitive. SSM used for GitHub connection ARN. No Secrets Manager or Vault integration. No secret rotation.
- **Gap**: No formal secrets management pattern for future application secrets.
- **Recommendation**: Establish Secrets Manager pattern for API keys and client secrets.
- **Evidence**: `src/books/create/index.ts`, `pipeline/lib/pipeline-stack.ts` (SSM parameter)

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: API Gateway logging configured (LoggingLevel: INFO, CloudWatch role). No CloudTrail in IaC. No immutable log storage. CloudWatch logs are mutable.
- **Gap**: No immutable, tamper-evident audit trail.
- **Recommendation**: Add CloudTrail with S3 bucket object lock for immutable logging.
- **Evidence**: `template.yml` (ApiGwAccountConfig, ApiGatewayLoggingRole)

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: Cognito supports adminDisableUser but no machine identity exists (AUTH-Q1 dependency). No API key or agent-specific suspension mechanism.
- **Gap**: No agent identity to suspend. Prerequisite AUTH-Q1 must be resolved.
- **Recommendation**: Define agent identity suspension runbook after AUTH-Q1 resolution.
- **Evidence**: `template.yml` (CognitoUserPool)

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No application-level compensation, saga patterns, or undo endpoints. putItem has no conditional logic. PreTraffic hook is deployment-only, not application-level.
- **Gap**: No rollback mechanism for write operations.
- **Recommendation**: Implement before expanding to write-enabled scope.
- **Evidence**: `src/books/create/index.ts`, `src/books/create-pre-traffic/index.ts`

#### STATE-Q2: Queryable Current State
- **Severity**: RISK-QUALITY
- **Finding**: GET /books returns all books via DynamoDB scan. No single-item GET /books/{isbn} endpoint.
- **Gap**: No item-level query capability.
- **Recommendation**: Add GET /books/{isbn} endpoint.
- **Evidence**: `src/books/get-all/index.ts`, `template.yml`

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No optimistic locking, ETags, or version fields. putItem has no ConditionExpression.
- **Gap**: No concurrency controls (informational for read-only scope).
- **Recommendation**: Add version field and ConditionExpression before write-enabled scope.
- **Evidence**: `src/books/create/index.ts`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has external dependencies (calls other services or external APIs). Lambda functions call DynamoDB (infrastructure dependency, not external service API).
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No explicit rate limiting. No usage plans, throttle settings, or WAF rules. Default API Gateway account-level throttling only.
- **Gap**: No per-client or per-endpoint rate limiting.
- **Recommendation**: Add UsagePlan and ApiKey resources with per-key throttle settings.
- **Evidence**: `template.yml` (BooksApi — no throttle configuration)

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No transaction limits configured. GET scan is unbounded. POST has no per-identity caps.
- **Gap**: No transaction limits (informational for read-only scope).
- **Recommendation**: Implement per-agent limits before write-enabled scope.
- **Evidence**: `template.yml`, `src/books/create/index.ts`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR on critical path. Priority is P1.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled. Current agent_scope is read-only.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled. Current agent_scope is read-only.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: INFO (Largely Satisfied)
- **Finding**: Staging environment exists as a full deployment target. Pipeline deploys to staging first with e2e tests before production. Docker-based local testing with DynamoDB Local is documented in README. Manual approval gate exists before production. E2E tests validate both endpoints against staging.
- **Gap**: No synthetic data generator or production-equivalent data seeding for staging. Test data is generated in tests using UUID-based book records.
- **Recommendation**: Add production-representative seed data for staging to improve agent testing realism.
- **Evidence**: `template.yml` (Stage parameter), `pipeline/lib/pipeline-stack.ts` (staging deploy + test + approval), `README.md` (local testing instructions)

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: DynamoDB table `BooksTable` has tags for `project` and `environment` but no data classification tags. Book data (isbn, title, year, author, publisher, rating, pages) appears to be non-PII reference data but is not formally classified. SSE enabled but that is encryption, not classification. No Macie integration.
- **Gap**: No data classification tags or policy.
- **Recommendation**: Add data classification tags. Document classification decision.
- **Evidence**: `template.yml` (BooksTable tags)

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No data residency requirements documented. DynamoDB deployed to SAM deploy region. No cross-region replication. No GDPR/LGPD/HIPAA references. Book catalog data is public reference data.
- **Gap**: No explicit data residency policy documented.
- **Recommendation**: Document data residency classification alongside DATA-Q1.
- **Evidence**: `template.yml` (BooksTable), `pipeline/buildspec-deploy.json`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK-QUALITY
- **Finding**: GET /books performs unbounded DynamoDB scan. No Limit, ExclusiveStartKey, FilterExpression, or ProjectionExpression.
- **Gap**: No pagination, filtering, or sorting.
- **Recommendation**: Add pagination, filtering, and sorting parameters.
- **Evidence**: `src/books/get-all/index.ts`

#### DATA-Q4: System of Record Designations
- **Severity**: RISK-QUALITY
- **Finding**: No system-of-record designation. DynamoDB is sole data store. No master data management.
- **Gap**: No formal SoR designation.
- **Recommendation**: Document as system of record for book catalog data.
- **Evidence**: `template.yml` (BooksTable), `README.md`

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK-QUALITY
- **Finding**: No temporal fields (created_at, updated_at). No Cache-Control or Last-Modified headers. `year` is publication year, not record timestamp.
- **Gap**: No temporal metadata or freshness signaling.
- **Recommendation**: Add timestamp fields and cache headers.
- **Evidence**: `src/books/create/index.ts`, `src/books/get-all/index.ts`

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: No log scrubbing. PreTraffic logs full DynamoDB items. Main handlers have empty catch blocks. No CloudWatch data protection.
- **Gap**: No PII redaction controls.
- **Recommendation**: Use allowlist logging. Add CloudWatch Logs data protection.
- **Evidence**: `src/books/create-pre-traffic/index.ts`, `src/books/create/index.ts`, `src/books/get-all/index.ts`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics or dashboards. No field validation in putItem. No null rate monitoring.
- **Gap**: No data quality awareness.
- **Recommendation**: Add input validation and quality monitoring.
- **Evidence**: `src/books/create/index.ts`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: No API versioning. No OpenAPI spec. No schema registry. No breaking change detection. No contract tests.
- **Gap**: No versioning or contract management.
- **Recommendation**: Add URL versioning, create OpenAPI spec, add contract testing.
- **Evidence**: `template.yml`, `pipeline/buildspec.json`, `src/books/tests/index.js`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: All field names are human-readable and semantically meaningful: isbn, title, year, author, publisher, rating, pages. No legacy codes.
- **Gap**: None.
- **Recommendation**: Maintain naming conventions.
- **Evidence**: `src/books/create/index.ts`, `src/books/get-all/index.ts`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No data catalog. No metadata files or data dictionary. Schema known only from source code.
- **Gap**: No metadata layer.
- **Recommendation**: Create data dictionary. Register in portfolio catalog.
- **Evidence**: Repository root, `template.yml`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: X-Ray tracing properly configured. AWSXRay.captureAWS() in both handlers. No structured JSON logging. No correlation IDs in app logs.
- **Gap**: Tracing strong. Structured logging absent.
- **Recommendation**: Add @aws-lambda-powertools/logger.
- **Evidence**: `template.yml`, `src/books/create/index.ts`, `src/books/get-all/index.ts`, `src/books/create-pre-traffic/index.ts`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: Two CloudWatch alarms for Lambda errors (deployment rollback triggers). No latency alarms. No anomaly detection. No operational notification.
- **Gap**: Deployment-scoped alarms only.
- **Recommendation**: Add operational alarms with SNS notification.
- **Evidence**: `template.yml` (alarm resources)

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics. No put_metric_data. No business dashboards.
- **Gap**: No business outcome visibility.
- **Recommendation**: Add custom CloudWatch metrics for business events.
- **Evidence**: `src/books/create/index.ts`, `src/books/get-all/index.ts`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK-QUALITY
- **Finding**: Full IaC (SAM + CDK). Manual approval gate. No branch protection. No drift detection.
- **Gap**: Peer review and drift detection not enforced.
- **Recommendation**: Enable branch protection and drift detection.
- **Evidence**: `template.yml`, `pipeline/lib/pipeline-stack.ts`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: Full pipeline with unit and e2e tests. No API contract tests, OpenAPI validation, or schema diff tools.
- **Gap**: No contract testing.
- **Recommendation**: Add OpenAPI validation and contract testing.
- **Evidence**: `pipeline/lib/pipeline-stack.ts`, `pipeline/buildspec.json`, `pipeline/buildspec-test.json`

#### ENG-Q3: Rollback Capability
- **Severity**: INFO (Satisfied)
- **Finding**: Linear10PercentEvery1Minute with alarm-triggered rollback. PreTraffic smoke test. CodeDeploy lifecycle management. Rollback within minutes.
- **Gap**: None.
- **Recommendation**: Add agent-specific contract validation to pre-traffic hook.
- **Evidence**: `template.yml`, `src/books/create-pre-traffic/index.ts`

#### ENG-Q4: API Test Coverage
- **Severity**: INFO (Largely Satisfied)
- **Finding**: 6 unit tests + 5 e2e tests. Run in CI. No contract tests.
- **Gap**: No contract tests for agent consumers.
- **Recommendation**: Add contract tests when agent integration begins.
- **Evidence**: `src/books/create/tests/index.spec.ts`, `src/books/get-all/tests/index.spec.ts`, `src/books/tests/index.js`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: INFO (Satisfied)
- **Finding**: DynamoDB SSEEnabled: true. S3 uses S3_MANAGED encryption. AWS-managed keys throughout.
- **Gap**: No CMK, but AWS-managed encryption is sufficient for current data classification.
- **Recommendation**: Upgrade to CMK if data reclassified as sensitive.
- **Evidence**: `template.yml` (BooksTable SSESpecification), `pipeline/lib/pipeline-stack.ts` (BucketEncryption)

---

## Evidence Index

### Infrastructure as Code
| File | Questions Referenced |
|------|---------------------|
| `template.yml` | API-Q1, API-Q2, API-Q4, API-Q5, API-Q7, API-Q8, AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q2, STATE-Q5, STATE-Q6, HITL-Q3, DATA-Q1, DATA-Q2, DATA-Q3, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q3, ENG-Q5 |
| `pipeline/lib/pipeline-stack.ts` | AUTH-Q2, AUTH-Q5, ENG-Q1, ENG-Q2, ENG-Q5, HITL-Q3 |
| `pipeline/bin/pipeline.ts` | ENG-Q2 |

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `src/books/create/index.ts` | API-Q1, API-Q3, API-Q4, API-Q5, AUTH-Q4, AUTH-Q5, STATE-Q1, STATE-Q3, STATE-Q6, DATA-Q3, DATA-Q5, DATA-Q6, DATA-Q7, DISC-Q2, OBS-Q1, OBS-Q3 |
| `src/books/get-all/index.ts` | API-Q1, API-Q3, API-Q5, API-Q8, STATE-Q2, DATA-Q3, DATA-Q5, DATA-Q6, DISC-Q2, OBS-Q1, OBS-Q3 |
| `src/books/create-pre-traffic/index.ts` | STATE-Q1, DATA-Q6, OBS-Q1, ENG-Q3 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `pipeline/buildspec.json` | ENG-Q2, ENG-Q4, DISC-Q1 |
| `pipeline/buildspec-deploy.json` | DATA-Q2, ENG-Q2 |
| `pipeline/buildspec-test.json` | ENG-Q2, ENG-Q4 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `src/books/create/package.json` | OBS-Q1 (aws-xray-sdk-core dependency) |
| `src/books/get-all/package.json` | OBS-Q1 (aws-xray-sdk-core dependency) |
| `src/books/tests/package.json` | ENG-Q4 (test dependencies) |
| `pipeline/package.json` | ENG-Q1, ENG-Q2 (CDK dependencies) |

### Test Files
| File | Questions Referenced |
|------|---------------------|
| `src/books/create/tests/index.spec.ts` | ENG-Q4 |
| `src/books/get-all/tests/index.spec.ts` | ENG-Q4 |
| `src/books/tests/index.js` | ENG-Q4, DISC-Q1 |
| `src/books/tests/books-manager.js` | ENG-Q4 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `pipeline/cdk.json` | ENG-Q1 |
| `events/create-book-request.json` | API-Q5 |
| `events/env.json` | AUTH-Q5 |
| `README.md` | API-Q1, HITL-Q3, DATA-Q4 |
