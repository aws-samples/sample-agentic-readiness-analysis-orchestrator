# Agentic Readiness Assessment Report

**Target**: ./services/books-api
**Date**: 2026-04-17
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P1
**Tags**: serverless, cdk, api, dynamodb
**Context**: Serverless REST API with CDK infrastructure for book catalog management. Clean API surface the agent can use as a tool for product lookups.

**Archetype Justification**: Service has DynamoDB persistent state with CRUD operations (POST /books creates records, GET /books reads records) keyed on `isbn`, qualifying as a stateful-crud service that owns and manages business entities.

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 2 | **RISK-SAFETY**: 8 | **RISK-QUALITY**: 15 | **INFOs**: 12

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 2 |
| RISK-SAFETY | 8 |
| RISK-QUALITY | 15 |
| INFO | 12 |
| N/A | 0 |
| Not Evaluated (extended) | 6 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 13
**Extended Questions Not Triggered**: 6
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: stateful-crud (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: The application uses Amazon Cognito User Pool with OAuth2 **implicit flow** configured for human users (email/password authentication). The `UserPoolClient` in `template.yml` defines `AllowedOAuthFlows: [implicit]` with `SupportedIdentityProviders: [COGNITO]`. There is no client credentials OAuth2 flow, no API key authentication with principal attribution, and no mTLS configuration. The Cognito setup is entirely user-oriented — agents cannot authenticate using email/password through a browser-based implicit flow.
- **Gap**: No machine identity authentication mechanism exists. An agent cannot obtain a token programmatically through a standard service-to-service flow (OAuth2 client credentials). The only authentication path requires human interaction (browser-based implicit grant or, in staging only, `USER_PASSWORD_AUTH` with `ALLOW_USER_PASSWORD_AUTH`).
- **Remediation**:
  - **Immediate**: Add a Cognito App Client configured with `client_credentials` OAuth2 flow and define a resource server with custom scopes (e.g., `books-api/read`, `books-api/write`). This enables machine-to-machine authentication with scoped access tokens.
  - **Target State**: A dedicated Cognito App Client for agent identities using client credentials flow, with custom scopes that map to read and write operations. Each agent identity gets its own app client credentials for attribution.
  - **Estimated Effort**: Low (1–2 days for Cognito configuration changes in `template.yml`)
  - **Dependencies**: AUTH-Q2 (scoped permissions) and AUTH-Q3 (action-level authorization) depend on this being resolved first.
- **Evidence**: `template.yml` (CognitoUserPool, UserPoolClient, UserPoolDomain resources)

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: The DynamoDB `BooksTable` in `template.yml` has tags limited to `project: my-project` and `environment: !Ref Stage`. No data classification tags exist (e.g., `data-classification: public`, `contains-pii: false`). The book schema includes fields: `isbn`, `title`, `year`, `author`, `publisher`, `rating`, `pages` — this is catalog/reference data that does not appear to contain PII, PHI, or financial records. However, there is no explicit classification, no field-level encryption beyond DynamoDB SSE, and no data classification policy documented anywhere in the repository.
- **Gap**: No data classification exists at the table or field level. Without explicit classification, an agent integration cannot programmatically verify that the data it accesses is safe to process, cache, or transmit. Even though the book catalog data is likely non-sensitive reference data, the absence of classification means there is no auditable proof of this determination.
- **Remediation**:
  - **Immediate**: Add data classification tags to the DynamoDB table in `template.yml`: `data-classification: public` and `contains-pii: false`. Document the data classification decision in the repository (e.g., `DATA_CLASSIFICATION.md`).
  - **Target State**: All data stores have explicit classification tags. A data classification document exists that maps each field to its sensitivity level. Automated scanning (e.g., Amazon Macie for S3, or custom tagging policies) enforces classification.
  - **Estimated Effort**: Low (hours for tagging, 1–2 days for documentation)
  - **Dependencies**: DATA-Q2 (data residency) benefits from this classification being in place.
- **Evidence**: `template.yml` (BooksTable resource, Tags section), `src/books/create/index.ts` (book schema fields)

**Remediation Prioritization**: Resolve AUTH-Q1 first — machine identity is a prerequisite for enforcing any access controls. DATA-Q1 can be resolved in parallel since it is primarily a tagging and documentation exercise. Both blockers are low effort and can be resolved within 1–2 weeks. Once both are resolved, the assessment moves to Pilot-Ready (Safety Concerns) given the 8 RISK-SAFETY findings.

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Lambda IAM policies use SAM policy templates scoped to the specific DynamoDB table: `DynamoDBReadPolicy` for GetAllBooks and `DynamoDBWritePolicy` for CreateBook (defined in `template.yml`). This is good least-privilege at the Lambda level. However, the GET /books endpoint is **entirely public** — no authentication required. Any caller, including an agent, can read all books without presenting credentials. The POST /books endpoint requires Cognito authorization with `email` scope. There is no mechanism to scope an agent identity to specific resources or operations beyond what Cognito scopes provide.
- **Gap**: GET /books is unauthenticated — there is no way to enforce least-privilege for agent read access because there is no identity to scope. Cognito scopes (`email`, `openid`) do not map to application-level permissions (read vs write).
- **Compensating Controls**:
  - Limit agent to GET /books only (read-only scope aligns with unauthenticated access pattern)
  - Add API Gateway resource policies to restrict access by source IP or VPC endpoint for agent callers
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add Cognito authorization to GET /books endpoint and define custom resource server scopes (e.g., `books-api/read`) that map to read-only access.
- **Evidence**: `template.yml` (GetAllBooks Events section — no Auth block; CreateBook Events section — Auth with CognitoAuth)

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Authorization is binary: GET /books is public (no auth), POST /books requires any valid Cognito token with `email` scope. There is no fine-grained RBAC that distinguishes between read-only and read-write agent identities. The Cognito `AuthorizationScopes` on POST /books use `email` and conditionally `aws.cognito.signin.user.admin` — these are identity scopes, not action-level permission scopes. No middleware in the Lambda handlers checks for specific permissions or roles.
- **Gap**: No action-level authorization exists. An authenticated user/agent can perform any operation that requires the `email` scope. There is no mechanism to allow an agent to read but not write, or to restrict specific operations within the authenticated surface.
- **Compensating Controls**:
  - Scope agent to read-only operations (GET /books is public and does not require auth)
  - Implement API Gateway resource policies to block agent access to POST /books
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Define a Cognito Resource Server with custom scopes (`books-api/read`, `books-api/write`) and assign scopes per endpoint. This enables action-level authorization where an agent identity can be granted read-only access.
- **Evidence**: `template.yml` (CreateBook Auth section, CognitoAuth authorizer definition)

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: API Gateway logging is enabled at `LoggingLevel: INFO` for all resources and methods (`template.yml`). However, there is no CloudTrail configuration in the IaC. No immutable log storage (S3 bucket with object lock, CloudTrail log file validation) is defined. API Gateway access logs will capture request metadata, but these logs are stored in CloudWatch without immutability guarantees.
- **Gap**: No immutable, tamper-evident audit trail exists. API Gateway CloudWatch logs can be modified or deleted. There is no CloudTrail trail defined to capture API-level events with log file validation enabled.
- **Compensating Controls**:
  - Enable CloudTrail at the AWS account level (outside this repository) with log file validation
  - Configure CloudWatch Logs with retention policies and restrict log group delete permissions
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `AWS::CloudTrail::Trail` resource to `template.yml` with `EnableLogFileValidation: true` and an S3 bucket with object lock for immutable storage. Alternatively, ensure account-level CloudTrail is configured and documented.
- **Evidence**: `template.yml` (BooksApi MethodSettings — LoggingLevel: INFO; no CloudTrail resource)

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Cognito User Pool supports disabling individual users via `adminDisableUser` API. However, GET /books has no authentication — there is no identity to suspend for read operations. For POST /books, a Cognito user could be disabled, but there is no agent-specific identity mechanism (no dedicated service accounts, no API keys). The pipeline uses SSM parameter for GitHub connection but no agent identity management is defined.
- **Gap**: No agent-specific identity exists to suspend. GET /books is unauthenticated, so misbehaving read-only agents cannot be individually isolated. Even for authenticated endpoints, there are no agent-specific Cognito users or app client credentials that could be revoked independently.
- **Compensating Controls**:
  - Use API Gateway resource policies or WAF rules to block specific agent source IPs
  - Implement API Gateway API keys per agent identity with the ability to delete/disable specific keys
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create dedicated Cognito App Clients per agent identity (aligns with AUTH-Q1 remediation). This enables disabling a specific agent's credentials without affecting other agents or human users.
- **Evidence**: `template.yml` (CognitoUserPool, UserPoolClient — single client for all users)

#### STATE-Q1: Compensation and Rollback ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The CreateBook Lambda performs a simple `DynamoDB.putItem` with no saga pattern, no compensating transactions, no undo endpoints, and no multi-step workflow coordination. The `create-pre-traffic` hook (`src/books/create-pre-traffic/index.ts`) creates a test item, verifies it, and deletes it — but this is a deployment smoke test, not a business compensation mechanism. There is no Step Functions workflow. Write operations are single-step (create a book record).
- **Gap**: No compensation or rollback mechanism exists for write operations. For the current simple PutItem pattern this is low-impact, but as the API grows to support updates and deletes, the absence of compensation patterns becomes critical.
- **Compensating Controls**:
  - Current write operations are single-step PutItem (inherently atomic at DynamoDB level), limiting partial-state risk
  - Agent is scoped to read-only, so compensation for write operations is not immediately needed
- **Remediation Timeline**: 60–90 days (as write complexity grows)
- **Recommendation**: For the current single-step writes, document the idempotent nature of PutItem with isbn key. Plan compensation patterns (soft-delete with status fields, audit trail of changes) before adding multi-step write workflows.
- **Evidence**: `src/books/create/index.ts` (simple putItem, no compensation), `src/books/create-pre-traffic/index.ts` (smoke test only)

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No API Gateway usage plan, no throttling configuration, and no WAF rate rules are defined in `template.yml` or the pipeline CDK stack. No application-level rate limiting middleware exists in the Lambda handlers. The API Gateway has default AWS account-level throttling (10,000 requests/second), but no service-specific or agent-specific rate limits are configured.
- **Gap**: No rate limiting is enforced. A runaway agent loop could exhaust DynamoDB read capacity (the table uses on-demand pricing based on `SimpleTable` default) and generate excessive Lambda invocations.
- **Compensating Controls**:
  - AWS account-level API Gateway throttling provides a coarse safety net
  - Lambda concurrency limits can be set at the function level to cap invocations
- **Remediation Timeline**: 7–14 days
- **Recommendation**: Add an API Gateway Usage Plan with throttle settings in `template.yml`. Define per-API-key rate limits so that agent identities can be throttled independently of human users.
- **Evidence**: `template.yml` (BooksApi resource — no UsagePlan, no ThrottlingBurstLimit, no ThrottlingRateLimit)

#### DATA-Q2: Data Residency and Sovereignty ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No data residency requirements are documented in the repository. The DynamoDB table is deployed to a single region (determined by the deployment region). No cross-region replication is configured. No GDPR, LGPD, or HIPAA references exist in the codebase. The book catalog data (isbn, title, year, author, publisher, rating, pages) is reference/catalog data unlikely to be subject to data sovereignty regulations.
- **Gap**: No data residency policy is documented. While the book catalog data is likely non-regulated reference data, there is no explicit documentation confirming this. If an agent sends book data to an LLM endpoint in another region, there is no documented basis for confirming this is permissible.
- **Compensating Controls**:
  - Book catalog data (isbn, title, year, author, publisher, rating, pages) contains no PII, PHI, or financial records — low regulatory risk
  - Document data residency posture as part of DATA-Q1 classification exercise
- **Remediation Timeline**: 7–14 days (documentation exercise)
- **Recommendation**: Document data residency posture: "Book catalog data is public reference data with no residency restrictions. Data may be transmitted to LLM endpoints in any region." Include this in the data classification document recommended in DATA-Q1.
- **Evidence**: `template.yml` (BooksTable — no replication, single region), `src/books/create/index.ts` (book schema fields)

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The `create-pre-traffic` Lambda (`src/books/create-pre-traffic/index.ts`) uses `console.log` to output DynamoDB item content: `console.log('DynamoDB item', JSON.stringify(Item, null, 2))`. This logs the full book record including all fields. The `create` and `get-all` handlers have no logging statements. Error responses return empty bodies (`body: ''`), so no PII leaks through error responses. No log scrubbing middleware or PII masking libraries are used anywhere in the codebase.
- **Gap**: No log scrubbing or PII redaction is implemented. While the book catalog data (isbn, title, author) does not contain customer PII, the `console.log` pattern in the pre-traffic hook logs full database records without filtering. If the schema were to include customer PII in the future, it would be logged automatically.
- **Compensating Controls**:
  - Current book data fields (isbn, title, year, author, publisher, rating, pages) do not contain customer PII
  - Pre-traffic hook is a deployment-time function, not a runtime API handler — it runs only during deployments
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Replace `console.log` with a structured logging library that supports field-level redaction. Add a log sanitization utility that can be applied to all log output. This prevents future PII leakage as the schema evolves.
- **Evidence**: `src/books/create-pre-traffic/index.ts` (lines with `console.log('DynamoDB item', ...)`)

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, GraphQL schema, or Smithy specification file exists in the repository. The SAM template declares `OpenApiVersion: 3.0.1` in the Globals section, but this is a SAM configuration directive to avoid default stage creation — it does not generate an OpenAPI spec. API endpoints are defined implicitly through SAM `Events` blocks on Lambda functions. The README provides human-readable API documentation but no machine-readable specification.
- **Gap**: No machine-readable API specification exists. Agent tool definitions must be manually authored based on code inspection, which will drift from actual behavior over time.
- **Compensating Controls**:
  - SAM template provides endpoint definitions (path, method) that can be used as a reference
  - Book schema is documented implicitly through code (`isbn`, `title`, `year`, `author`, `publisher`, `rating`, `pages`)
- **Remediation Timeline**: 7–14 days
- **Recommendation**: Generate an OpenAPI 3.0 specification from the SAM template and Lambda handlers. Add it to the repository and configure SAM to use the `DefinitionBody` property on the API Gateway to keep the spec synchronized with the implementation.
- **Evidence**: `template.yml` (Globals Api OpenApiVersion: 3.0.1 — configuration only; BooksApi — no DefinitionBody), repository root (no openapi.yaml/json, no swagger.yaml/json)

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Both Lambda handlers (`create/index.ts` and `get-all/index.ts`) return `statusCode: 500` with `body: ''` (empty string) and `headers: {}` on error. No structured error codes, error messages, error categories, or retryable indicators are returned. Success responses include `Content-Type: application/json` header, but error responses have no content type and no body.
- **Gap**: An agent receiving a 500 response cannot distinguish between a retriable error (DynamoDB throttling) and a terminal error (malformed input). The empty error body provides no diagnostic information.
- **Compensating Controls**:
  - Agent can implement retry-with-backoff for all 500 errors as a conservative strategy
  - Error type can be inferred from HTTP status codes alone (500 = server error)
- **Remediation Timeline**: 7–14 days
- **Recommendation**: Implement structured error responses: `{ "error": { "code": "INTERNAL_ERROR", "message": "...", "retryable": true/false } }`. Distinguish between input validation errors (400), authentication errors (401), and server errors (500).
- **Evidence**: `src/books/create/index.ts` (catch block — statusCode: 500, body: ''), `src/books/get-all/index.ts` (catch block — statusCode: 500, body: '')

#### STATE-Q2: Queryable Current State — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: GET /books returns all books via DynamoDB scan. There is no single-record GET endpoint (e.g., GET /books/{isbn}) to query the state of a specific book. The scan returns all records without filtering, pagination, or sorting capability.
- **Gap**: An agent cannot query the state of a specific book by ISBN. The only read operation returns the entire collection. For an agent performing lookups ("does this book exist?", "what is this book's rating?"), a full table scan is inefficient and may exceed LLM context windows as the collection grows.
- **Compensating Controls**:
  - For small catalogs, the full scan is workable — agent can filter client-side
  - DynamoDB supports GetItem by primary key (isbn), so adding a single-record endpoint is straightforward
- **Remediation Timeline**: 7–14 days
- **Recommendation**: Add a GET /books/{isbn} endpoint backed by a DynamoDB GetItem operation. This gives agents targeted lookup capability without scanning the full table.
- **Evidence**: `src/books/get-all/index.ts` (DynamoDB scan with no filters), `template.yml` (only GET /books and POST /books endpoints)

#### DATA-Q3: Selective Query Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: GET /books performs an unfiltered, unpaginated DynamoDB `scan` operation. The `ScanInput` params contain only `TableName` — no `Limit`, no `ExclusiveStartKey`, no `FilterExpression`, no `ProjectionExpression`. The response returns all items in the table as a single JSON array. No pagination parameters (`limit`, `offset`, `cursor`) are accepted in the API request. No sorting options exist.
- **Gap**: An agent retrieving book data gets all records regardless of how many exist. As the catalog grows, this will exhaust LLM context windows, increase latency, and increase cost. DynamoDB scans also have a 1MB per-page limit — the current code does not handle pagination internally, so results beyond 1MB would be silently truncated.
- **Compensating Controls**:
  - For small catalogs (< 1MB), the full scan works without truncation
  - Agent can implement client-side filtering if the result set is small enough
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add pagination support to GET /books: accept `limit` and `cursor` (ExclusiveStartKey) query parameters. Return a `nextCursor` in the response for subsequent pages. Consider adding filter parameters (e.g., `author`, `year`) and a GET /books/{isbn} endpoint for targeted lookups.
- **Evidence**: `src/books/get-all/index.ts` (ScanInput with TableName only, no Limit/ExclusiveStartKey/FilterExpression)

#### DATA-Q4: System of Record Designations — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: DynamoDB is the sole data store for book records. There is no documented system-of-record designation, no master data management process, and no conflict resolution logic. The book data appears to be self-contained within this service — no references to external data sources or synchronization with other systems.
- **Gap**: No formal system-of-record designation exists. While DynamoDB is the de facto source of truth (the only store), this is not documented. If the book catalog were to be consumed by multiple services or synchronized with an external catalog provider, the lack of explicit SoR designation could lead to data conflicts.
- **Compensating Controls**:
  - Single data store (DynamoDB) means there is no conflicting source by default
  - Book data appears to be self-contained — no external synchronization observed
- **Remediation Timeline**: 7–14 days (documentation)
- **Recommendation**: Document DynamoDB as the system of record for book catalog data. If external catalog sources exist (publisher feeds, ISBN databases), document the synchronization strategy and conflict resolution approach.
- **Evidence**: `template.yml` (BooksTable — sole data store), `src/books/create/index.ts` (writes only to DynamoDB)

#### DATA-Q5: Temporal Metadata and Freshness — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The book schema contains no temporal fields. The DynamoDB `PutItem` in `create/index.ts` stores: `isbn`, `title`, `year`, `author`, `publisher`, `rating`, `pages`. There is no `created_at`, `updated_at`, `last_modified`, or `event_time` field. The GET /books response returns no `Cache-Control`, `X-Data-Age`, or `last_refreshed` headers — only `Content-Type: application/json`. DynamoDB does not automatically add timestamps to items.
- **Gap**: An agent cannot determine when a book record was created or last updated. For time-sensitive reasoning (e.g., "show me books added this month"), there is no data to support the query. The agent has no way to know if the data is fresh or stale.
- **Compensating Controls**:
  - Book catalog data is relatively static — freshness is less critical than for transactional data
  - DynamoDB Streams could be enabled to capture temporal change events without modifying the schema
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add `created_at` and `updated_at` fields (ISO 8601, UTC) to the book schema in `create/index.ts`. Return `Cache-Control` headers in GET /books response to signal data freshness to agents.
- **Evidence**: `src/books/create/index.ts` (PutItem params — no temporal fields), `src/books/get-all/index.ts` (response headers — Content-Type only)

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No API versioning exists. The API path is simply `/books` — no `/v1/` prefix, no `Accept-Version` header support. No OpenAPI spec exists to version. No schema registry, no changelog, no deprecation notices. No breaking change detection tools in the CI pipeline (no `buf breaking`, no OpenAPI diff, no Pact contract tests). The buildspec.json runs unit tests but does not validate API contracts.
- **Gap**: API changes (e.g., renaming a field from `isbn` to `book_id`, adding required fields) would break agent tool bindings silently. There is no mechanism to detect or prevent breaking changes before they reach production.
- **Compensating Controls**:
  - The API surface is small (2 endpoints) — manual review can catch breaking changes for now
  - E2e tests in the pipeline (`src/books/tests/index.js`) would catch some structural changes
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add API path versioning (`/v1/books`). Create an OpenAPI spec and add breaking-change detection to the CI pipeline (e.g., `openapi-diff` or Pact consumer-driven contract tests). This protects agent tool bindings from silent breakage.
- **Evidence**: `template.yml` (API path `/books` — no versioning), `pipeline/buildspec.json` (no contract test step)

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: X-Ray tracing is enabled: `Tracing: Active` on Lambda functions and `TracingEnabled: true` on the API Gateway (in `template.yml`). The Lambda handlers import `aws-xray-sdk-core` and wrap the AWS SDK with `AWSXRay.captureAWS(AWSCore)` for automatic trace propagation. However, application logging is minimal: only the pre-traffic hook uses `console.log` (unstructured). The `create` and `get-all` handlers have no logging at all. No structured JSON logging library is used. No correlation IDs are set in application logs.
- **Gap**: Distributed tracing is present (X-Ray), but structured logging is absent. When an agent-initiated request fails, X-Ray traces show the call flow, but there are no application-level logs to correlate with the trace. The `create` and `get-all` handlers silently catch errors and return 500 with no logging.
- **Compensating Controls**:
  - X-Ray traces provide request-level diagnostic information for agent-initiated requests
  - API Gateway access logs (LoggingLevel: INFO) capture request metadata
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add a structured logging library (e.g., `@aws-lambda-powertools/logger`) to Lambda handlers. Log request/response summaries with trace IDs. Log caught errors with context before returning 500 responses.
- **Evidence**: `template.yml` (Tracing: Active, TracingEnabled: true), `src/books/create/index.ts` (AWSXRay.captureAWS, no logging in catch block), `src/books/get-all/index.ts` (AWSXRay.captureAWS, no logging in catch block)

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: CloudWatch Alarms are configured for Lambda error metrics: `CreateBookAliasErrorMetricGreaterThanZeroAlarm` and `GetAllBooksAliasErrorMetricGreaterThanZeroAlarm` (in `template.yml`). These trigger when Lambda `Errors > 0` over 2 evaluation periods of 60 seconds. These alarms are tied to CodeDeploy deployment preferences for automatic rollback. However, there are no latency alarms, no anomaly detection, and no integration with incident management tools (PagerDuty, OpsGenie, SNS topics for notifications).
- **Gap**: Error rate alerting exists but is deployment-focused (triggers rollback), not operational (triggers human notification). No latency alerting exists. No anomaly detection is configured. An agent experiencing elevated error rates or latency would not trigger operational alerts.
- **Compensating Controls**:
  - Deployment-time error alarms provide some protection during rollout
  - API Gateway default CloudWatch metrics provide latency data, but no alarms are defined on them
- **Remediation Timeline**: 7–14 days
- **Recommendation**: Add CloudWatch Alarms for API Gateway latency (p99 > threshold) and 5xx error rates. Add SNS notification targets to alarms for operational alerting. Consider composite alarms that combine error rate and latency signals.
- **Evidence**: `template.yml` (CreateBookAliasErrorMetricGreaterThanZeroAlarm, GetAllBooksAliasErrorMetricGreaterThanZeroAlarm — error only, no latency)

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Infrastructure is fully defined as code: SAM template (`template.yml`) defines the API Gateway, Lambda functions, DynamoDB table, Cognito, and CloudWatch alarms. The CI/CD pipeline is defined as CDK (`pipeline/lib/pipeline-stack.ts`). The pipeline includes a `ManualApprovalAction` before production deployment, ensuring human review of changes. However, no drift detection is configured (no AWS Config rules, no CloudFormation drift detection scheduled). No explicit PR review requirements are codified (relies on GitHub branch protection, which is outside this repository).
- **Gap**: IaC definition and deployment review (manual approval) are present. Drift detection is absent. If the API Gateway, IAM roles, or DynamoDB table are modified outside CloudFormation, the change would not be detected.
- **Compensating Controls**:
  - SAM/CloudFormation provides a baseline — manual changes would be overwritten on next deployment
  - Manual approval step provides human review before production
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Enable CloudFormation drift detection on a schedule (AWS Config rule `cloudformation-stack-drift-detection-check`). Add branch protection rules to the GitHub repository to require PR reviews for IaC changes.
- **Evidence**: `template.yml` (full IaC definition), `pipeline/lib/pipeline-stack.ts` (ManualApprovalAction, Pipeline stages)

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: A full CI/CD pipeline is defined: Source → Build (with unit tests) → Staging (deploy + e2e tests) → Production (manual approval + deploy). Unit tests in `buildspec.json` run `npm test` for create and get-all functions. E2e tests in `buildspec-test.json` run Mocha tests against the deployed staging API. However, no API contract tests exist — no Pact, no OpenAPI validation, no schema comparison tools. The e2e tests validate behavior but not API schema stability.
- **Gap**: The CI/CD pipeline cannot detect API-breaking changes (field renames, type changes, removed endpoints) before they affect agent tool bindings. E2e tests verify functional behavior but not structural contracts.
- **Compensating Controls**:
  - E2e tests verify response structure implicitly (tests check for specific fields)
  - Manual approval step before production provides a human checkpoint
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add API contract validation to the build step: create an OpenAPI spec, add a schema validation step that compares the spec against the previous version, and fail the build on breaking changes.
- **Evidence**: `pipeline/buildspec.json` (unit test step, no contract tests), `pipeline/buildspec-test.json` (e2e tests, no contract validation), `src/books/tests/index.js` (behavioral tests, not contract tests)

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Production deployment uses `Linear10PercentEvery1Minute` with CloudWatch alarm-based automatic rollback via CodeDeploy. Pre-traffic hooks (`CreateBookPreTraffic`) validate new Lambda versions before shifting traffic. Staging uses `AllAtOnce` (blue-green). Manual approval gate (`ManualApprovalAction`) before production deployment. This is a strong rollback capability.
- **Gap**: Rollback is automated and effective at the Lambda version level. Minor gap: no feature flag system for granular rollback of specific behaviors without full version rollback.
- **Compensating Controls**:
  - Linear deployment with alarm-based rollback catches errors quickly
  - Pre-traffic hook validates function correctness before any traffic shift
- **Remediation Timeline**: Low priority — current capability is strong
- **Recommendation**: Current rollback capability is adequate. Consider feature flags if agent-specific features require independent rollback granularity.
- **Evidence**: `template.yml` (DeploymentPreference: Linear10PercentEvery1Minute, Alarms, Hooks), `src/books/create-pre-traffic/index.ts` (pre-traffic validation)

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Unit tests exist for both Lambda functions: create (`index.spec.ts` — 3 tests: success, invalid input, DynamoDB failure) and get-all (`index.spec.ts` — 3 tests: success, empty results, DynamoDB failure). E2e tests (`tests/index.js` — 4 tests: GET without auth, books returned, POST requires auth, POST with invalid payload, POST creates book). Tests cover success paths, error handling, and authentication requirements.
- **Gap**: Good test coverage for existing endpoints. No API contract tests (addressed in ENG-Q2). No pagination edge case tests (pagination doesn't exist yet). No concurrent access tests.
- **Compensating Controls**:
  - E2e tests run against deployed staging environment, catching integration issues
  - Unit tests with mocked DynamoDB validate handler logic
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add contract tests when OpenAPI spec is created. Expand test coverage for edge cases as API features grow.
- **Evidence**: `src/books/create/tests/index.spec.ts`, `src/books/get-all/tests/index.spec.ts`, `src/books/tests/index.js`, `pipeline/buildspec.json`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: DynamoDB `BooksTable` has `SSEEnabled: true` (server-side encryption with AWS-managed key). Pipeline S3 buckets use `BucketEncryption.S3_MANAGED`. All data at rest is encrypted. No customer-managed KMS keys (CMK) are used.
- **Gap**: Encryption uses AWS-managed keys, not customer-managed keys. For non-sensitive book catalog data, this is adequate. CMK would be required for regulated or sensitive data.
- **Compensating Controls**:
  - AWS-managed SSE provides encryption at rest by default
  - Book catalog data is reference data with no regulatory encryption requirements
- **Remediation Timeline**: Low priority for current data classification
- **Recommendation**: Current encryption is adequate. Migrate to CMK if data classification changes to include sensitive data.
- **Evidence**: `template.yml` (BooksTable SSESpecification: SSEEnabled: true), `pipeline/lib/pipeline-stack.ts` (BucketEncryption.S3_MANAGED)

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: A staging environment exists and is fully integrated into the CI/CD pipeline. `template.yml` defines a `Stage` parameter (`staging`/`production`). Pipeline deploys to staging first, runs e2e tests, then requires manual approval before production. Local testing with Docker and DynamoDB Local documented in README. Staging uses `AllAtOnce` deployment and `ALLOW_USER_PASSWORD_AUTH` for programmatic testing.
- **Gap**: Staging is deployment-focused, not agent-testing-focused. No documented process for testing agent interactions. No seed data scripts for representative catalog data.
- **Compensating Controls**:
  - Staging is functionally equivalent to production (same SAM template)
  - E2e tests demonstrate programmatic API interaction patterns similar to agent usage
- **Remediation Timeline**: 7–14 days
- **Recommendation**: Document agent integration testing process in staging. Create seed data scripts for representative book catalog data.
- **Evidence**: `template.yml` (Parameters Stage), `pipeline/lib/pipeline-stack.ts` (Staging stage), `pipeline/buildspec-test.json`, `README.md` — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO
- **Finding**: The application exposes a documented REST API via Amazon API Gateway with two endpoints: GET /books (retrieve all books) and POST /books (create a book). The API is defined in `template.yml` using SAM and deployed via API Gateway. The README.md provides human-readable documentation of the API, architecture, and usage instructions.
- **Implication**: The REST API surface is clean and well-suited for agent tool binding. An agent can use GET /books as a product lookup tool. The API Gateway provides a stable, managed integration layer.
- **Recommendation**: The API surface is agent-ready from an interface perspective. Consider adding GET /books/{isbn} for targeted lookups, which would be more efficient for agent tool usage.
- **Evidence**: `template.yml` (BooksApi, GetAllBooks ApiEvent, CreateBook ApiEvent), `README.md` (Architecture section)

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The CreateBook Lambda uses DynamoDB `PutItem` with `isbn` as the primary key. PutItem is naturally idempotent — calling it multiple times with the same `isbn` overwrites the record with identical data, not creating duplicates. However, there is no explicit idempotency key header support (no `Idempotency-Key` header parsing). The isbn serves as a de facto idempotency key at the data layer.
- **Implication**: For read-only agent scope, idempotency of write operations is informational. If scope expands to write-enabled, the natural idempotency of PutItem with isbn key provides a baseline, but explicit idempotency key support should be added for robustness.
- **Recommendation**: No action needed for read-only scope. If expanding to write-enabled, add explicit `Idempotency-Key` header support using AWS Lambda Powertools idempotency utility.
- **Evidence**: `src/books/create/index.ts` (PutItem with isbn as primary key), `template.yml` (BooksTable PrimaryKey: isbn)

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: API responses use JSON format with `Content-Type: application/json` headers. GET /books returns a JSON array of book objects. POST /books returns an empty body with status 201. Error responses return empty bodies with no content type. No Protobuf, XML, or binary formats are used.
- **Implication**: JSON responses are ideal for agent consumption. LLMs can parse JSON natively. The response format requires no special adaptation for agent tool integration.
- **Recommendation**: Consider returning the created book object in the POST /books response body (currently empty) to provide confirmation data to agents.
- **Evidence**: `src/books/create/index.ts` (headers: {'Content-Type': 'application/json'}, body: ''), `src/books/get-all/index.ts` (headers: {'Content-Type': 'application/json'}, body: JSON.stringify(bookDtos))

### API-Q7: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: No event emission for state changes exists. There are no SNS topics, EventBridge rules, SQS queues, Kafka topics, or webhook endpoints defined in the repository. The CreateBook function writes to DynamoDB but does not emit any event on successful creation. DynamoDB Streams are not enabled on the BooksTable.
- **Implication**: Agents cannot react proactively to new book additions. Any agent needing to know about new books must poll the GET /books endpoint. For the current use case (product lookups), this is acceptable.
- **Recommendation**: If future use cases require agents to react to new book additions (e.g., update recommendations), enable DynamoDB Streams and publish events to EventBridge.
- **Evidence**: `template.yml` (BooksTable — no StreamSpecification; no SNS/SQS/EventBridge resources), `src/books/create/index.ts` (no event emission after putItem)

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limit documentation exists. No `X-RateLimit-Remaining` or `Retry-After` headers are returned in API responses. No API Gateway usage plan is defined. No WAF rate rules are configured. API Gateway default throttling exists at the account level but is not documented or surfaced to API consumers.
- **Implication**: An agent calling this API has no programmatic way to detect when it is approaching rate limits. Without rate limit headers, agents cannot self-throttle and will only discover limits through 429 errors.
- **Recommendation**: After adding an API Gateway Usage Plan (STATE-Q5), configure response headers to include `X-RateLimit-Remaining` and `Retry-After` so agents can self-regulate.
- **Evidence**: `template.yml` (BooksApi — no UsagePlan), `src/books/get-all/index.ts` (response headers — no rate limit headers)

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: INFO
- **Finding**: The Cognito authorizer on POST /books passes user context through `requestContext` (standard API Gateway behavior with Cognito). However, the CreateBook Lambda handler does not access `requestContext` or extract the caller's identity — it only reads `event.body` for the book data. GET /books has no authentication, so no identity context is available. No token exchange or on-behalf-of flows exist. No user context headers are defined.
- **Implication**: For the read-only agent scope targeting GET /books (which is unauthenticated), identity propagation is not applicable. If expanding to write operations, the Cognito-provided identity context in `requestContext` can be extracted to attribute writes to specific agents.
- **Recommendation**: When adding agent authentication (AUTH-Q1), extract and log the caller identity from `requestContext.authorizer.claims` in Lambda handlers.
- **Evidence**: `template.yml` (CognitoAuth authorizer), `src/books/create/index.ts` (handler reads event.body only, not requestContext)

### AUTH-Q5: Credential Management

- **Severity**: INFO
- **Finding**: No hardcoded credentials exist in source code. Environment variables are used for configuration: `TABLE` (DynamoDB table name) is passed via Lambda environment variables defined in `template.yml`. The pipeline uses AWS SSM Parameter Store for the GitHub connection ARN (`StringParameter.fromStringParameterName(this, 'GithubConnectionArn', 'github_connection_arn')`). No Secrets Manager or Vault integration exists. No `.env` files are committed. Lambda functions use IAM execution roles for AWS SDK authentication (no explicit credentials).
- **Implication**: Credential management is adequate for the current setup. Lambda execution roles provide automatic credential rotation. SSM Parameter Store is used for pipeline secrets. If agent-specific credentials are added (AUTH-Q1), they should be stored in Secrets Manager with rotation.
- **Recommendation**: When adding agent credentials (Cognito client secrets), store them in AWS Secrets Manager with automatic rotation configured.
- **Evidence**: `template.yml` (Lambda Environment Variables — TABLE only), `pipeline/lib/pipeline-stack.ts` (SSM Parameter for github_connection_arn), `src/books/create/index.ts` (no hardcoded credentials)

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled AND service has persistent state. Current scope is read-only.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits exist. No per-agent limits on records modified, spend, or delete operations. The API has no Usage Plan or per-key throttling. Read-only agents cannot modify records, but there are no limits on read volume beyond AWS defaults.
- **Implication**: For read-only scope, blast radius is limited to read amplification (excessive DynamoDB scan operations). No data modification risk exists. If scope expands to write-enabled, transaction limits become critical.
- **Recommendation**: No action needed for read-only scope. Address as part of STATE-Q5 (rate limiting) to limit read amplification.
- **Evidence**: `template.yml` (no UsagePlan, no per-key throttling)

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: All field names are human-readable and semantically meaningful: `isbn`, `title`, `year`, `author`, `publisher`, `rating`, `pages`. No legacy abbreviations, no encoded field names, no data dictionary required. The DynamoDB schema and API response format use the same clear field names.
- **Implication**: Agent LLMs can reason about book data fields without requiring a mapping layer or data dictionary. Field names are self-documenting, which simplifies agent tool definition.
- **Recommendation**: Maintain this naming convention as the schema evolves. Avoid introducing abbreviated or encoded field names.
- **Evidence**: `src/books/create/index.ts` (isbn, title, year, author, publisher, rating, pages), `src/books/get-all/index.ts` (same field names in response mapping)

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No data catalog, AWS Glue Data Catalog, or formal metadata layer exists. The README provides high-level API documentation and architecture description. The book schema is implicitly documented through the Lambda handler code. No data dictionary, no schema documentation, no API catalog.
- **Implication**: When building agent tools against this API, developers must inspect source code to understand the data model. A metadata layer would accelerate tool definition and improve agent reasoning about available data.
- **Recommendation**: Create a lightweight data dictionary (e.g., `SCHEMA.md`) documenting the book entity fields, types, constraints, and relationships. This serves as the foundation for agent tool definition.
- **Evidence**: `README.md` (architecture description, no schema details), `src/books/create/index.ts` (implicit schema)

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No custom business outcome metrics are published. No `cloudwatch.put_metric_data` calls exist in the Lambda handlers. Only infrastructure metrics are available through Lambda and API Gateway defaults (invocation count, error count, duration, throttles). No dashboards tracking business KPIs (books created per day, catalog growth rate, popular queries) are defined.
- **Implication**: When agents consume this API, there will be no business-level signal to determine whether agent interactions produce good outcomes. Infrastructure metrics alone cannot distinguish between "agent successfully retrieved relevant books" and "agent retrieved all books but none were relevant."
- **Recommendation**: Add custom CloudWatch metrics for business events: `BooksCreated`, `BooksRetrieved`, `CatalogSize`. These metrics will be valuable for measuring agent effectiveness once integrated.
- **Evidence**: `src/books/create/index.ts` (no put_metric_data), `src/books/get-all/index.ts` (no put_metric_data), `template.yml` (no custom metrics)

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality metrics, dashboards, null rate monitoring, duplicate detection, or freshness SLAs exist. The book schema has no validation beyond what DynamoDB enforces (string type for isbn, title, author, publisher; number type for year, rating, pages). There is no check for data completeness, no validation that `isbn` follows ISO 2108 format, and no rating range enforcement.
- **Implication**: Agents acting on incomplete or invalid book data (e.g., missing author, invalid ISBN, rating outside expected range) would propagate errors. For a read-only product lookup use case, this is low-risk but should be addressed as the catalog grows.
- **Recommendation**: Add input validation to the CreateBook Lambda (validate ISBN format, rating range 1–5, required fields). Consider a periodic data quality scan that reports completeness metrics.
- **Evidence**: `src/books/create/index.ts` (no input validation beyond JSON parsing)

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: The application exposes a documented REST API via Amazon API Gateway with two endpoints: GET /books (retrieve all books) and POST /books (create a book). The API is defined in `template.yml` using SAM. The README.md provides human-readable documentation. No direct database access, file-based exchange, or UI automation is required for integration.
- **Gap**: No gap — REST API exists and is well-documented.
- **Recommendation**: Consider adding GET /books/{isbn} for targeted lookups, which would be more efficient for agent tool usage.
- **Evidence**: `template.yml` (BooksApi, GetAllBooks, CreateBook), `README.md`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, GraphQL schema, or Smithy specification file exists. The SAM `OpenApiVersion: 3.0.1` is a configuration directive only. API endpoints are defined implicitly through SAM Events blocks.
- **Gap**: No machine-readable spec. Agent tool definitions must be manually authored.
- **Recommendation**: Generate an OpenAPI 3.0 specification and use SAM `DefinitionBody` to keep it synchronized.
- **Evidence**: `template.yml` (Globals Api OpenApiVersion — config only; no DefinitionBody)

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: Both Lambda handlers return `statusCode: 500` with `body: ''` and `headers: {}` on error. No structured error codes, messages, or retryable indicators.
- **Gap**: Agent cannot distinguish retriable from terminal errors.
- **Recommendation**: Implement structured error responses with error code, message, and retryable boolean.
- **Evidence**: `src/books/create/index.ts` (catch block), `src/books/get-all/index.ts` (catch block)

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: DynamoDB PutItem with isbn primary key provides natural idempotency. No explicit idempotency key header support.
- **Gap**: No explicit idempotency key mechanism, but natural idempotency exists via isbn key.
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: `src/books/create/index.ts` (PutItem), `template.yml` (BooksTable PrimaryKey: isbn)

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: JSON responses with `Content-Type: application/json`. GET /books returns JSON array. POST /books returns empty body with 201. No XML or binary formats.
- **Gap**: N/A — JSON format is ideal for agents.
- **Recommendation**: Consider returning created book in POST response body.
- **Evidence**: `src/books/create/index.ts`, `src/books/get-all/index.ts`

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has operations >30s OR long-running workflows. Lambda timeout is 5 seconds. No long-running workflows detected.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: No event emission exists. No SNS, EventBridge, SQS, or webhook endpoints. DynamoDB Streams not enabled. CreateBook writes to DynamoDB without emitting events.
- **Gap**: No event-driven integration surface for agents.
- **Recommendation**: Enable DynamoDB Streams and EventBridge if proactive agent patterns are needed.
- **Evidence**: `template.yml` (no event resources), `src/books/create/index.ts` (no event emission)

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit documentation. No X-RateLimit-Remaining or Retry-After headers. No API Gateway Usage Plan. No WAF rate rules.
- **Gap**: Agents cannot self-throttle without rate limit headers.
- **Recommendation**: Add Usage Plan and rate limit headers.
- **Evidence**: `template.yml` (no UsagePlan), `src/books/get-all/index.ts` (no rate limit headers)

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: Cognito User Pool with OAuth2 implicit flow for human users only. `AllowedOAuthFlows: [implicit]`. No client credentials flow, no API key authentication, no mTLS. Agents cannot authenticate programmatically.
- **Gap**: No machine identity authentication. Agent cannot obtain token through service-to-service flow.
- **Recommendation**: Add Cognito App Client with `client_credentials` flow and resource server with custom scopes.
- **Evidence**: `template.yml` (CognitoUserPool, UserPoolClient, UserPoolDomain)

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: Lambda IAM uses scoped SAM policies (DynamoDBReadPolicy, DynamoDBWritePolicy). However, GET /books is entirely public — no auth. Cognito scopes (email, openid) don't map to application permissions.
- **Gap**: No way to enforce least-privilege for read access — no identity to scope.
- **Recommendation**: Add authentication to GET /books and define custom Cognito scopes.
- **Evidence**: `template.yml` (GetAllBooks — no Auth; CreateBook — CognitoAuth with email scope)

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: Authorization is binary: GET is public, POST requires any valid Cognito token with email scope. No fine-grained RBAC distinguishing read vs write. No middleware checks for specific permissions.
- **Gap**: No action-level authorization. Cannot restrict agent to read-only within authenticated surface.
- **Recommendation**: Define Cognito Resource Server with custom scopes per endpoint.
- **Evidence**: `template.yml` (CognitoAuth authorizer, AuthorizationScopes: email)

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: Cognito authorizer passes user context via requestContext on POST /books. CreateBook Lambda does not extract caller identity. GET /books has no auth. No token exchange or on-behalf-of flows.
- **Gap**: Caller identity not extracted or logged in write operations.
- **Recommendation**: Extract and log caller identity from requestContext when adding agent authentication.
- **Evidence**: `template.yml` (CognitoAuth), `src/books/create/index.ts` (reads event.body only)

#### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: No hardcoded credentials. TABLE env var for DynamoDB name. SSM Parameter Store for GitHub connection ARN in pipeline. Lambda functions use IAM execution roles. No Secrets Manager integration.
- **Gap**: No secrets management for application-level credentials (currently none exist).
- **Recommendation**: Store agent credentials in Secrets Manager when added.
- **Evidence**: `template.yml` (Environment Variables), `pipeline/lib/pipeline-stack.ts` (SSM Parameter)

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: API Gateway logging at LoggingLevel: INFO. No CloudTrail in IaC. No immutable log storage. CloudWatch logs lack immutability guarantees.
- **Gap**: No immutable, tamper-evident audit trail.
- **Recommendation**: Add CloudTrail with log file validation or ensure account-level CloudTrail is configured.
- **Evidence**: `template.yml` (BooksApi MethodSettings LoggingLevel: INFO; no CloudTrail)

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: Cognito supports user disable. GET /books is unauthenticated — no identity to suspend for reads. No agent-specific identity mechanism exists.
- **Gap**: No agent-specific identity to suspend. Unauthenticated endpoints cannot isolate misbehaving agents.
- **Recommendation**: Create dedicated Cognito App Clients per agent (aligns with AUTH-Q1).
- **Evidence**: `template.yml` (CognitoUserPool, UserPoolClient — single client)

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Simple DynamoDB PutItem with no saga pattern, no undo endpoints, no compensating transactions. Pre-traffic hook is a deployment smoke test, not business compensation.
- **Gap**: No compensation or rollback for write operations.
- **Recommendation**: Document PutItem idempotency. Plan compensation patterns before adding complex writes.
- **Evidence**: `src/books/create/index.ts`, `src/books/create-pre-traffic/index.ts`

#### STATE-Q2: Queryable Current State
- **Severity**: RISK-QUALITY
- **Finding**: GET /books returns all books via DynamoDB scan. No single-record GET endpoint exists (no GET /books/{isbn}). State is queryable but only as a full collection.
- **Gap**: Cannot query state of a specific book by ISBN.
- **Recommendation**: Add GET /books/{isbn} endpoint.
- **Evidence**: `src/books/get-all/index.ts` (scan), `template.yml` (only GET /books)

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled AND service has persistent state. Current scope is read-only.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has external dependencies (calls other services or external APIs). Lambda functions call only DynamoDB (AWS managed service with built-in resilience). No external API calls detected.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No API Gateway Usage Plan, no WAF rate rules, no application-level rate limiting. Only AWS account-level default throttling.
- **Gap**: No rate limiting enforced. Runaway agent loop could overwhelm service.
- **Recommendation**: Add API Gateway Usage Plan with throttle settings.
- **Evidence**: `template.yml` (no UsagePlan, no ThrottlingBurstLimit)

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits. No per-agent limits on any operations.
- **Gap**: No transaction limits. Read-only blast radius limited to read amplification.
- **Recommendation**: Address via STATE-Q5 rate limiting.
- **Evidence**: `template.yml` (no UsagePlan, no per-key throttling)

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path. Priority is P1, not P0.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled. Current scope is read-only.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled. Current scope is read-only.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: A staging environment exists and is fully integrated into the CI/CD pipeline. The `template.yml` defines a `Stage` parameter with `AllowedValues: [staging, production]`. The pipeline deploys to staging first, runs e2e tests against the staging deployment, then requires manual approval before production. Local testing with Docker and DynamoDB Local is documented in README.md. The staging environment uses the same SAM template as production with different parameter values.
- **Gap**: The staging environment is deployment-focused, not agent-testing-focused. There is no documented process for testing agent interactions in staging. No seed data scripts exist to populate staging with representative book catalog data for agent testing. The staging Cognito pool uses `ALLOW_USER_PASSWORD_AUTH` for testing, which is a reasonable accommodation.
- **Recommendation**: Document a process for agent integration testing in staging. Create seed data scripts to populate the staging DynamoDB table with representative book catalog data.
- **Evidence**: `template.yml` (Parameters Stage, Conditions IsProduction), `pipeline/lib/pipeline-stack.ts` (Staging stage with deploy + test), `pipeline/buildspec-test.json` (e2e tests), `README.md` (local testing)

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: DynamoDB BooksTable has tags limited to `project: my-project` and `environment`. No data classification tags. Book schema (isbn, title, year, author, publisher, rating, pages) is catalog/reference data with no apparent PII/PHI/financial records, but no explicit classification exists.
- **Gap**: No data classification at table or field level. No auditable proof that data is safe for agent processing.
- **Recommendation**: Add classification tags to DynamoDB table. Document data classification decision.
- **Evidence**: `template.yml` (BooksTable Tags), `src/books/create/index.ts` (book schema)

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No data residency documentation. Single-region DynamoDB. No cross-region replication. No GDPR/LGPD/HIPAA references. Book catalog data is unlikely regulated.
- **Gap**: No documented data residency posture.
- **Recommendation**: Document data residency posture confirming book catalog data has no residency restrictions.
- **Evidence**: `template.yml` (BooksTable — single region)

#### DATA-Q3: Selective Query Support
- **Severity**: RISK-QUALITY
- **Finding**: GET /books performs unfiltered, unpaginated DynamoDB scan. No Limit, ExclusiveStartKey, FilterExpression, or ProjectionExpression. Returns all items as single JSON array. No pagination, filtering, or sorting in API.
- **Gap**: Unbounded result sets. Silent truncation at 1MB DynamoDB limit. Agent gets all records regardless of need.
- **Recommendation**: Add pagination (limit/cursor), filtering, and GET /books/{isbn} endpoint.
- **Evidence**: `src/books/get-all/index.ts` (ScanInput with TableName only)

#### DATA-Q4: System of Record Designations
- **Severity**: RISK-QUALITY
- **Finding**: DynamoDB is sole data store. No documented SoR designation. No master data management. No external data source references or synchronization.
- **Gap**: No formal SoR designation, though DynamoDB is de facto sole source.
- **Recommendation**: Document DynamoDB as system of record for book catalog data.
- **Evidence**: `template.yml` (BooksTable), `src/books/create/index.ts` (writes to DynamoDB only)

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK-QUALITY
- **Finding**: No temporal fields in book schema. No created_at, updated_at, or event_time. No Cache-Control or freshness headers in responses. DynamoDB does not add timestamps automatically.
- **Gap**: Agent cannot determine when records were created or updated.
- **Recommendation**: Add created_at and updated_at fields (ISO 8601, UTC). Add Cache-Control headers.
- **Evidence**: `src/books/create/index.ts` (no temporal fields), `src/books/get-all/index.ts` (no freshness headers)

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: Pre-traffic hook logs full DynamoDB items via `console.log('DynamoDB item', JSON.stringify(Item, null, 2))`. Create and get-all handlers have no logging. Error responses return empty bodies (no PII in errors). No log scrubbing or PII masking.
- **Gap**: No log scrubbing. Full database records logged in pre-traffic hook.
- **Recommendation**: Replace console.log with structured logging library with field-level redaction.
- **Evidence**: `src/books/create-pre-traffic/index.ts` (console.log of DynamoDB items)

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics, dashboards, or monitoring. No input validation beyond DynamoDB type enforcement. No ISBN format validation, no rating range checks, no required field validation.
- **Gap**: No data quality monitoring or input validation.
- **Recommendation**: Add input validation. Consider periodic data quality scans.
- **Evidence**: `src/books/create/index.ts` (no validation beyond JSON parse)

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: No API versioning (/v1/ prefix, Accept-Version header). No OpenAPI spec to version. No schema registry. No breaking change detection in CI. No Pact or contract tests. API path is simply /books.
- **Gap**: API changes break agent tool bindings silently. No detection mechanism.
- **Recommendation**: Add API path versioning and breaking-change detection to CI.
- **Evidence**: `template.yml` (path /books — no versioning), `pipeline/buildspec.json` (no contract tests)

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: All field names are human-readable and semantically meaningful: isbn, title, year, author, publisher, rating, pages. No legacy abbreviations or encoded names.
- **Gap**: No gap — field names are self-documenting.
- **Recommendation**: Maintain this naming convention.
- **Evidence**: `src/books/create/index.ts`, `src/books/get-all/index.ts`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No data catalog, Glue Data Catalog, or metadata layer. README provides architecture docs. Book schema documented implicitly in code only.
- **Gap**: Schema requires source code inspection to understand.
- **Recommendation**: Create SCHEMA.md documenting entity fields, types, and constraints.
- **Evidence**: `README.md`, `src/books/create/index.ts`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: X-Ray tracing enabled (Tracing: Active, TracingEnabled: true). aws-xray-sdk-core in Lambda handlers with AWSXRay.captureAWS. No structured JSON logging — only console.log in pre-traffic hook. No correlation IDs in application logs. Create and get-all handlers have zero logging.
- **Gap**: Tracing present but structured logging absent. Errors caught silently with no logging.
- **Recommendation**: Add @aws-lambda-powertools/logger for structured logging with trace IDs.
- **Evidence**: `template.yml` (Tracing: Active, TracingEnabled: true), `src/books/create/index.ts` (AWSXRay, no logging), `src/books/get-all/index.ts` (AWSXRay, no logging)

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: CloudWatch Alarms for Lambda Errors > 0 on both functions. Tied to CodeDeploy rollback. No latency alarms. No anomaly detection. No incident management integration.
- **Gap**: Error alerting is deployment-focused only. No operational or latency alerting.
- **Recommendation**: Add latency alarms and SNS notification targets for operational alerting.
- **Evidence**: `template.yml` (CreateBookAliasErrorMetricGreaterThanZeroAlarm, GetAllBooksAliasErrorMetricGreaterThanZeroAlarm)

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics. No put_metric_data calls. Only infrastructure metrics via Lambda/API Gateway defaults.
- **Gap**: No business-level visibility into agent interaction outcomes.
- **Recommendation**: Add custom metrics: BooksCreated, BooksRetrieved, CatalogSize.
- **Evidence**: `src/books/create/index.ts` (no metrics), `src/books/get-all/index.ts` (no metrics)

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK-QUALITY
- **Finding**: Full IaC: SAM template (template.yml) + CDK pipeline (pipeline-stack.ts). ManualApprovalAction before production. No drift detection (no AWS Config rules). No codified PR review requirements.
- **Gap**: IaC and review present. Drift detection absent.
- **Recommendation**: Enable CloudFormation drift detection. Add branch protection rules.
- **Evidence**: `template.yml`, `pipeline/lib/pipeline-stack.ts` (ManualApprovalAction)

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: Full CI/CD: Source → Build (unit tests) → Staging (deploy + e2e) → Production (approval + deploy). No API contract tests. No Pact, OpenAPI validation, or schema comparison.
- **Gap**: Cannot detect API-breaking changes before affecting agent tool bindings.
- **Recommendation**: Add OpenAPI spec validation and breaking-change detection to build step.
- **Evidence**: `pipeline/buildspec.json`, `pipeline/buildspec-test.json`, `src/books/tests/index.js`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: Production uses `Linear10PercentEvery1Minute` with CloudWatch alarm-based automatic rollback. Pre-traffic hooks validate new versions before traffic shift. Staging uses AllAtOnce (blue-green). CodeDeploy manages traffic shifting. Manual approval gate before production.
- **Gap**: Rollback is strong and automated. Minor gap: no feature flag system for granular rollback of specific behaviors. Rollback granularity is at the Lambda version level.
- **Recommendation**: Rollback capability is adequate. Consider feature flags for finer-grained control if agent-specific features are added.
- **Evidence**: `template.yml` (DeploymentPreference: Linear10PercentEvery1Minute, Alarms, Hooks), `src/books/create-pre-traffic/index.ts`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: Unit tests exist for create (`index.spec.ts`: 3 tests covering success, invalid input, DynamoDB failure) and get-all (`index.spec.ts`: 3 tests covering success, empty results, DynamoDB failure). E2e tests exist (`tests/index.js`: 4 tests covering no-auth required for GET, books returned, auth required for POST, invalid payload, and successful creation). Tests cover success paths, error handling, and auth requirements.
- **Gap**: Test coverage is good for existing endpoints. No contract tests (addressed in ENG-Q2). No explicit pagination edge case tests (because pagination doesn't exist). No test for concurrent access patterns.
- **Recommendation**: Add contract tests when OpenAPI spec is created. Add edge case tests for large result sets when pagination is implemented.
- **Evidence**: `src/books/create/tests/index.spec.ts`, `src/books/get-all/tests/index.spec.ts`, `src/books/tests/index.js`, `pipeline/buildspec.json` (npm test steps)

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: RISK-QUALITY
- **Finding**: DynamoDB BooksTable has `SSEEnabled: true` (server-side encryption with AWS-managed key). Pipeline S3 buckets use `BucketEncryption.S3_MANAGED`. No customer-managed KMS keys (CMK) are used. All data at rest is encrypted with AWS-managed keys.
- **Gap**: Encryption at rest is enabled but uses AWS-managed keys, not customer-managed keys. For book catalog data (non-sensitive reference data), AWS-managed encryption is adequate. CMK would be required for regulated data.
- **Recommendation**: Current encryption is adequate for catalog data. If the schema expands to include sensitive data, migrate to customer-managed KMS keys.
- **Evidence**: `template.yml` (BooksTable SSESpecification: SSEEnabled: true), `pipeline/lib/pipeline-stack.ts` (BucketEncryption.S3_MANAGED)

---

## Evidence Index

### Infrastructure as Code
| File | Questions Referenced |
|------|---------------------|
| `template.yml` | API-Q1, API-Q2, API-Q3, API-Q4, API-Q5, API-Q7, API-Q8, AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q2, STATE-Q5, STATE-Q6, DATA-Q1, DATA-Q2, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q3, ENG-Q5, HITL-Q3 |
| `pipeline/lib/pipeline-stack.ts` | AUTH-Q5, ENG-Q1, ENG-Q2, ENG-Q5, HITL-Q3 |
| `pipeline/bin/pipeline.ts` | ENG-Q1 |

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `src/books/create/index.ts` | API-Q1, API-Q3, API-Q4, API-Q5, STATE-Q1, DATA-Q1, DATA-Q3, DATA-Q5, DATA-Q7, DISC-Q2, AUTH-Q4, OBS-Q1, OBS-Q3 |
| `src/books/get-all/index.ts` | API-Q1, API-Q3, API-Q5, API-Q8, STATE-Q2, DATA-Q3, DATA-Q5, DISC-Q2, OBS-Q1, OBS-Q3 |
| `src/books/create-pre-traffic/index.ts` | STATE-Q1, DATA-Q6, OBS-Q1 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `pipeline/buildspec.json` | ENG-Q2, ENG-Q4, DISC-Q1 |
| `pipeline/buildspec-deploy.json` | ENG-Q2 |
| `pipeline/buildspec-test.json` | ENG-Q2, ENG-Q4, HITL-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `src/books/create/package.json` | OBS-Q1 (aws-xray-sdk-core dependency) |
| `src/books/get-all/package.json` | OBS-Q1 (aws-xray-sdk-core dependency) |
| `src/books/tests/package.json` | ENG-Q4 (e2e test dependencies) |
| `pipeline/package.json` | ENG-Q1 (CDK dependencies) |

### Test Files
| File | Questions Referenced |
|------|---------------------|
| `src/books/create/tests/index.spec.ts` | ENG-Q4 |
| `src/books/get-all/tests/index.spec.ts` | ENG-Q4 |
| `src/books/tests/index.js` | ENG-Q2, ENG-Q4 |
| `src/books/tests/books-manager.js` | ENG-Q4 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `events/env.json` | AUTH-Q5 |
| `events/create-book-request.json` | API-Q5 |
| `events/get-all-books-request.json` | API-Q5 |
| `pipeline/cdk.json` | ENG-Q1 |
| `README.md` | API-Q1, DISC-Q3, HITL-Q3 |
