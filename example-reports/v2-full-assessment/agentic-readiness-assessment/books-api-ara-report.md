# Agentic Readiness Assessment Report

**Target**: ./services/books-api
**Date**: 2026-04-15
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Agent Scope**: write-enabled
**Priority**: P1
**Tags**: serverless, cdk, api, dynamodb
**Context**: Serverless REST API with CDK infrastructure for book catalog management. Clean API surface the agent can use as a tool for product lookups.

---

## Readiness Profile: Not Agent-Integrable

**BLOCKERs**: 6 | **RISKs**: 32 | **INFOs**: 11

Exclude from agent toolset or plan major remediation before re-evaluation. Six blockers must be resolved before any agent deployment — including pilots. The system lacks machine identity authentication, idempotent write operations, immutable audit logging, compensation/rollback capability, data residency documentation for write-enabled agent scope, and CORS/network policy documentation. These gaps create data integrity risk, compliance exposure, and integration failure risk at agent speed.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 6 |
| RISK | 32 |
| INFO | 11 |
| N/A | 0 |
| **Total** | **49** |

**Questions Evaluated**: 49
**Questions N/A (repo_type: application)**: 0

---

## BLOCKERs — Must Resolve Before Agent Deployment

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: BLOCKER
- **Conditional**: agent_scope is "write-enabled" — evaluated as BLOCKER
- **Finding**: The `POST /books` endpoint in `src/books/create/index.ts` uses `DynamoDB.putItem()` with no idempotency controls. The `PutItem` call uses only the `isbn` primary key as the item identifier. If an agent retries a failed request or an LLM non-deterministically issues a duplicate tool call, `PutItem` will silently overwrite the existing record with potentially different data (e.g., different rating or pages values). There is no idempotency key header, no `ConditionExpression` to prevent overwrites, and no deduplication mechanism.
- **Gap**: No idempotency key support on write endpoints. No conditional writes to prevent duplicate or conflicting operations. No unique constraint enforcement beyond the `isbn` primary key.
- **Remediation**:
  - **Immediate**: Add a `ConditionExpression: "attribute_not_exists(isbn)"` to the `PutItem` call in `src/books/create/index.ts` to prevent silent overwrites. Return HTTP 409 Conflict when the condition fails.
  - **Target State**: Write endpoints accept an `Idempotency-Key` header. Duplicate requests with the same key return the original response without re-executing the operation. Consider using AWS Lambda Powertools idempotency utility.
  - **Estimated Effort**: Medium
  - **Dependencies**: API-Q3 (structured error responses needed to communicate 409 Conflict to agents)
- **Evidence**: `src/books/create/index.ts` (lines 28–38, PutItem with no ConditionExpression), `template.yml` (CreateBook function definition)

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: The application uses Amazon Cognito User Pool for authentication on the `POST /books` endpoint via the `CognitoAuth` authorizer defined in `template.yml`. The `UserPoolClient` is configured with OAuth implicit grant flow and `USER_PASSWORD_AUTH` — both designed for human browser-based authentication. The Cognito User Pool requires email-based sign-up with password. The `GET /books` endpoint has no authentication at all. There is no OAuth2 client credentials flow, no API key authentication with principal attribution, no mTLS configuration, and no service account definitions anywhere in the codebase.
- **Gap**: No machine identity authentication pathway exists. An agent cannot authenticate using service credentials — it would need to impersonate a human user through the Cognito User Pool, which is not auditable or attributable as agent activity.
- **Remediation**:
  - **Immediate**: Add a Cognito App Client configured with OAuth2 client credentials grant (`AllowedOAuthFlows: client_credentials`) and define custom scopes (e.g., `books/read`, `books/write`) on a Cognito Resource Server. This enables machine-to-machine authentication with attributable principal identity.
  - **Target State**: Agent identities authenticate via client credentials flow with scoped permissions. Each agent instance has its own client ID, and all API calls are logged with the agent's client ID as the principal.
  - **Estimated Effort**: Medium
  - **Dependencies**: AUTH-Q7 (audit logging must capture the machine identity principal)
- **Evidence**: `template.yml` (CognitoUserPool, UserPoolClient with implicit grant, CognitoAuth authorizer), `src/books/create/index.ts` (no auth context extraction)

### AUTH-Q7: Immutable Audit Logging ⚡

- **Severity**: BLOCKER
- **Conditional**: agent_scope is "write-enabled" — evaluated as BLOCKER
- **Finding**: API Gateway access logging is configured (`LoggingLevel: INFO` in `template.yml` MethodSettings) and a CloudWatch role is set up via `ApiGatewayLoggingRole`. X-Ray tracing is enabled on both the API Gateway (`TracingEnabled: true`) and Lambda functions (`Tracing: Active`). However: (1) No CloudTrail configuration exists in the IaC — no `AWS::CloudTrail::Trail` resource. (2) No immutable log storage — no S3 bucket with object lock or write-once policies for logs. (3) The `CreateBook` Lambda function (`src/books/create/index.ts`) does not log the authenticated principal (Cognito user identity) for write operations — it processes the book data without any audit trail of who performed the action. (4) CloudWatch log retention policies are not configured — logs may be retained indefinitely or deleted without governance.
- **Gap**: No immutable, tamper-evident audit trail for write operations. The authenticated principal is not logged at the application level. No CloudTrail configuration for API-level audit. Logs are not stored in immutable storage.
- **Remediation**:
  - **Immediate**: Extract the Cognito user identity from `event.requestContext.authorizer.claims` in `src/books/create/index.ts` and log it with every write operation. Add a `AWS::CloudTrail::Trail` resource to `template.yml` writing to an S3 bucket with object lock enabled.
  - **Target State**: Every write operation logs: timestamp, authenticated principal (human or agent), action performed, resource affected, and request ID. Logs are stored in S3 with object lock (WORM) and CloudWatch Logs with defined retention. CloudTrail captures all API Gateway and Lambda invocations.
  - **Estimated Effort**: Medium
  - **Dependencies**: AUTH-Q1 (machine identity must exist before it can be logged)
- **Evidence**: `template.yml` (API Gateway logging config, no CloudTrail resource), `src/books/create/index.ts` (no principal logging in handler)

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: BLOCKER
- **Conditional**: agent_scope is "write-enabled" — evaluated as BLOCKER
- **Finding**: The application has no compensation or rollback capability. The `CreateBook` Lambda performs a single `DynamoDB.putItem()` operation — there are no multi-step workflows, no saga pattern, no Step Functions, no compensating transactions, and no undo/delete endpoints. The `GET /books` endpoint is read-only. The `POST /books` endpoint creates a book record directly with no intermediate state. If an agent performs a sequence of book creation operations and one fails, there is no mechanism to roll back the previously successful operations.
- **Gap**: No compensation logic, no rollback endpoints, no saga pattern, no undo capability. An agent performing multi-step write workflows has no way to reverse completed steps if a subsequent step fails.
- **Remediation**:
  - **Immediate**: Implement a `DELETE /books/{isbn}` endpoint to enable explicit rollback of created books. Add a `ConditionExpression` to the `PutItem` to prevent accidental overwrites (related to API-Q4).
  - **Target State**: The API supports full CRUD operations (Create, Read, Update, Delete) with conditional writes. For multi-step agent workflows, implement a saga coordinator using AWS Step Functions with error handling and compensation states.
  - **Estimated Effort**: Medium
  - **Dependencies**: API-Q4 (idempotency), AUTH-Q1 (machine identity for authorized deletions)
- **Evidence**: `src/books/create/index.ts` (single PutItem, no compensation), `template.yml` (no Step Functions, no delete endpoint)

### DATA-Q2: Data Residency and Sovereignty ⚡

- **Severity**: BLOCKER
- **Conditional**: agent_scope is "write-enabled" — evaluated as BLOCKER
- **Finding**: No data residency or sovereignty requirements are documented. No GDPR, LGPD, or HIPAA compliance references exist in the codebase. No region-specific data storage configurations beyond the implicit AWS region in which the stack is deployed. No cross-region replication is configured. The data stored (book metadata: isbn, title, year, author, publisher, rating, pages) is bibliographic metadata with no PII, PHI, GDPR-regulated personal data, or sector-specific regulated content. While the actual data risk is low, the TD conditional rule requires BLOCKER evaluation for write-enabled agent scope because an agent transmitting data to an LLM provider in a different region requires a documented residency assessment regardless of data content.
- **Gap**: No formal documentation confirming data residency assessment. No data sovereignty policy document. The absence of a documented residency determination means the system cannot demonstrate compliance readiness for write-enabled agent operations, even though the actual data (public book catalog information) carries no regulatory residency requirements. If the schema evolves to include customer data (e.g., purchase history, user reviews with PII), residency controls would need to be established.
- **Remediation**:
  - **Immediate**: Create a `DATA_CLASSIFICATION.md` file documenting the data residency assessment: book catalog data has no residency requirements, no PII, no GDPR applicability. Include a policy trigger: "If the schema is extended to include personal data, re-evaluate data residency requirements before deployment."
  - **Target State**: Formal data residency documentation exists and is reviewed when the data schema changes. Data classification tags on DynamoDB tables indicate residency status. Policy triggers enforce re-assessment when new data types are added.
  - **Estimated Effort**: Low
  - **Dependencies**: DATA-Q1 (data classification should be completed alongside residency documentation)
- **Evidence**: `template.yml` (BooksTable with no cross-region replication, no residency tags), `src/books/create/index.ts` (book schema contains only bibliographic metadata)

### ENG-Q6: Cross-Origin and Network Policies

- **Severity**: BLOCKER
- **Finding**: No CORS configuration exists anywhere in the codebase. The `BooksApi` resource in `template.yml` has no `Cors` property defined. The Lambda function responses in `src/books/create/index.ts` and `src/books/get-all/index.ts` do not include CORS headers (`Access-Control-Allow-Origin`, `Access-Control-Allow-Methods`, `Access-Control-Allow-Headers`). No WAF rules are configured. No API Gateway resource policies exist. No network policies or security group rules are defined (expected for serverless, but no documentation of the network security posture exists). An agent running from a different origin or platform will be blocked by browser CORS policies, and there is no documentation of what network boundaries the API is accessible from.
- **Gap**: No CORS configuration on API Gateway or in Lambda responses. No WAF rules. No network access policy documentation. Agents and agent orchestrators calling this API from different origins will encounter CORS failures.
- **Remediation**:
  - **Immediate**: Add CORS configuration to the `BooksApi` SAM resource using the `Cors` property: `Cors: {AllowMethods: "'GET,POST,OPTIONS'", AllowHeaders: "'Content-Type,Authorization'", AllowOrigin: "'*'"}` (restrict AllowOrigin to specific agent platform domains in production).
  - **Target State**: CORS is explicitly configured with allowlisted origins for agent platforms. A WAF WebACL is attached to the API Gateway stage for rate limiting and IP-based access control. Network security posture is documented.
  - **Estimated Effort**: Low
  - **Dependencies**: None — this is the fastest blocker to resolve.
- **Evidence**: `template.yml` (BooksApi resource with no Cors property), `src/books/create/index.ts` (no CORS headers in response), `src/books/get-all/index.ts` (no CORS headers in response)

## RISKs — Proceed with Compensating Controls

### API-Q2: Machine-Readable API Specification

- **Severity**: RISK
- **Finding**: No OpenAPI, Swagger, AsyncAPI, GraphQL schema, or Smithy model files exist in the repository. The SAM template sets `OpenApiVersion: 3.0.1` in the Globals section, but this only prevents SAM from creating a default API stage — no actual OpenAPI specification file is generated or maintained. The API contract (GET /books, POST /books) is defined only in the SAM template Events sections and the Lambda function code.
- **Gap**: No machine-readable API specification exists for agent tool generation. Agent frameworks cannot auto-generate tool definitions from a spec file.
- **Compensating Controls**:
  - Manually author tool definitions based on the SAM template Events sections and Lambda function code.
  - Use API Gateway's built-in export feature to extract an OpenAPI spec from the deployed stage.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Create an `openapi.yaml` file co-located with `template.yml` and reference it in the SAM template using the `DefinitionBody` property. Auto-generate from annotations or maintain alongside code changes.
- **Evidence**: `template.yml` (OpenApiVersion: 3.0.1 with no DefinitionBody), repository-wide search found no `.yaml`/`.json` files matching OpenAPI/Swagger patterns.

### API-Q3: Structured Error Responses

- **Severity**: RISK
- **Finding**: Both Lambda functions use generic catch blocks that return HTTP 500 with an empty body. In `src/books/create/index.ts`: `catch (e) { response = { statusCode: 500, headers: {}, body: '' }; }`. Identical pattern in `src/books/get-all/index.ts`. No error code, no error message, no retryable indication. An agent receiving a 500 response cannot distinguish between a transient DynamoDB timeout (retryable) and a malformed request (terminal).
- **Gap**: No structured error response format. No error codes, no machine-readable error bodies, no retryable indication.
- **Compensating Controls**:
  - Configure agent tool definitions to treat all 500 errors as retryable with exponential backoff (accept false retries on terminal errors).
  - Add API Gateway response mapping templates to provide basic error structure.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Implement a standardized error response format: `{ "error": { "code": "DYNAMODB_TIMEOUT", "message": "...", "retryable": true } }`. Differentiate input validation errors (400), auth errors (401/403), conflict errors (409), and server errors (500).
- **Evidence**: `src/books/create/index.ts` (catch block, lines 41–45), `src/books/get-all/index.ts` (catch block, lines 37–41)

### API-Q5: API Versioning and Deprecation

- **Severity**: RISK
- **Finding**: No API versioning scheme is implemented. The API path is `/books` with no version prefix (`/v1/books`). No `Accept-Version` headers are supported. No changelog or deprecation policy documentation exists. The SAM template does not reference API versioning. No version metadata is returned in API responses.
- **Gap**: No versioning strategy. API contract changes will break agent tool schemas silently.
- **Compensating Controls**:
  - Pin agent tool definitions to the current API behavior with explicit integration tests.
  - Use the CI/CD pipeline's staging environment to validate agent compatibility before production deployment.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add URL-based versioning (`/v1/books`) to the API Gateway route definitions. Establish a deprecation policy requiring 90-day notice before breaking changes.
- **Evidence**: `template.yml` (API paths: `/books` with no version prefix)

### API-Q7: Asynchronous Operation Support

- **Severity**: RISK
- **Finding**: No asynchronous operation patterns found. Both Lambda functions are synchronous with a 5-second timeout. No background job frameworks (no SQS workers, no Step Functions, no Celery/Bull). No polling endpoints or job status APIs. No webhook callback endpoints. For a simple book CRUD API with DynamoDB, synchronous operations are likely sufficient (sub-second response times expected), but no async fallback exists for potential future long-running operations.
- **Gap**: No async patterns for operations that might exceed agent timeout thresholds. No webhook support for event-driven agent patterns.
- **Compensating Controls**:
  - Agent tool definitions can set a 5-second timeout matching the Lambda configuration.
  - DynamoDB operations are typically sub-second, so sync patterns are acceptable for current scope.
- **Remediation Timeline**: 60–90 days (when needed for new operations)
- **Recommendation**: If the API expands to include operations like bulk imports or report generation, implement async patterns using SQS + Lambda or Step Functions with a polling status endpoint.
- **Evidence**: `template.yml` (Timeout: 5 on Lambda functions), `src/books/create/index.ts` (synchronous handler), `src/books/get-all/index.ts` (synchronous handler)

### AUTH-Q2: Scoped Permissions (Least Privilege)

- **Severity**: RISK
- **Finding**: Lambda execution roles use SAM policy templates scoped to the specific `BooksTable`: `DynamoDBReadPolicy` for GetAllBooks and `DynamoDBWritePolicy` for CreateBook. These are well-scoped at the infrastructure level. However, agent-facing permissions are not scoped — the Cognito authorizer only checks for a valid token with the `email` scope. Any authenticated user can call `POST /books` regardless of role or intent. The pipeline CDK stack (`pipeline/lib/pipeline-stack.ts`) uses overly broad managed policies: `AWSCloudFormationFullAccess`, `AmazonDynamoDBFullAccess`, `AWSLambda_FullAccess`, `AmazonAPIGatewayAdministrator`, `IAMFullAccess`, `AWSCodeDeployFullAccess`, `AmazonCognitoPowerUser`.
- **Gap**: No agent-specific permission scoping. No fine-grained scopes beyond `email`. Pipeline roles use wildcard FullAccess policies.
- **Compensating Controls**:
  - Limit agent pilot to GET /books (public, read-only) until scoped permissions are implemented.
  - Define custom OAuth scopes on a Cognito Resource Server for agent-specific access control.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Define a Cognito Resource Server with custom scopes (`books/read`, `books/write`, `books/admin`). Assign agent clients specific scopes. Narrow pipeline IAM policies to least-privilege.
- **Evidence**: `template.yml` (DynamoDBReadPolicy, DynamoDBWritePolicy, CognitoAuth with email scope), `pipeline/lib/pipeline-stack.ts` (FullAccess managed policies)

### AUTH-Q3: Action-Level Authorization

- **Severity**: RISK
- **Finding**: The API provides endpoint-level authorization: GET /books is public (no auth), POST /books requires a Cognito token. However, there is no fine-grained action-level authorization within a resource type. The system cannot distinguish between an agent that should be allowed to create books but not delete them, or read specific categories but not others. There is no ABAC policy, no fine-grained RBAC, no permission matrix in code, and no method-level authorization beyond the Cognito authorizer on POST.
- **Gap**: No action-level authorization. Cannot restrict agent operations to specific actions within the same resource type.
- **Compensating Controls**:
  - Limit agent scope to read-only operations (GET /books is public and requires no auth) while building action-level controls.
  - Use API Gateway resource policies to restrict specific HTTP methods per caller identity.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement custom OAuth scopes per operation (e.g., `books:create`, `books:read`) and enforce them at the API Gateway authorizer level. Add Lambda authorizer logic for fine-grained action-level checks if needed.
- **Evidence**: `template.yml` (GET /books has no auth, POST /books uses CognitoAuth with email scope only)

### AUTH-Q4: Identity Propagation

- **Severity**: RISK
- **Finding**: The Cognito authorizer passes user identity claims in `event.requestContext.authorizer.claims` to the Lambda function. However, the `CreateBook` Lambda (`src/books/create/index.ts`) does not extract, use, or propagate user identity — it only processes `event.body` for the book data. User context is available but completely ignored at the application layer. No `X-User-Id` headers, no JWT parsing middleware, no on-behalf-of flows.
- **Gap**: Identity context is available from Cognito but not extracted or propagated by the application. No end-to-end user context flow.
- **Compensating Controls**:
  - API Gateway access logs capture the Cognito identity at the gateway level even though the Lambda ignores it.
  - X-Ray traces include request metadata that can be correlated with Cognito auth.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Extract `event.requestContext.authorizer.claims.sub` (Cognito user ID) in the Lambda handler and include it in DynamoDB records as `created_by` field, and in structured log entries.
- **Evidence**: `src/books/create/index.ts` (handler accesses only `event.body`, ignores `event.requestContext`)

### AUTH-Q5: Agent-as-Self vs Agent-on-Behalf-of-User

- **Severity**: RISK
- **Finding**: No distinction between agent-as-self and agent-on-behalf-of-user modes. The Cognito User Pool is designed for human users with email-based registration. There is no separate service identity mechanism, no separate IAM roles for agents, and no separate auth flows for service-to-service vs user-delegated calls. The system cannot distinguish whether an API call comes from a human, an agent acting autonomously, or an agent acting on behalf of a human.
- **Gap**: No support for dual identity modes. No separate auth paths or audit fields distinguishing agent-as-self from agent-on-behalf-of-user.
- **Compensating Controls**:
  - During pilot, use a dedicated Cognito user account for agent operations and manually track agent-initiated actions.
  - Use naming conventions in agent user accounts (e.g., `agent-bookbot@service.internal`) to distinguish in logs.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a Cognito App Client with client credentials grant for agent-as-self operations. For agent-on-behalf-of-user, implement token exchange or pass user context headers that the Lambda extracts and logs separately.
- **Evidence**: `template.yml` (single CognitoUserPool with implicit grant only, no service identity)

### AUTH-Q6: Credential Management

- **Severity**: RISK
- **Finding**: No secrets management system (AWS Secrets Manager, HashiCorp Vault) is configured in the IaC. Lambda environment variables contain only the `TABLE` name (non-sensitive). The pipeline uses SSM Parameter Store for `github_connection_arn` — stored as a plain StringParameter, not a SecureString. No hardcoded credentials, API keys, or passwords were found in source code. No `.env` files are committed. However, no formal secrets management exists for future agent API keys or service credentials.
- **Gap**: No secrets management infrastructure for agent credentials. SSM parameter for GitHub connection is not encrypted (StringParameter, not SecureString).
- **Compensating Controls**:
  - Current Lambda functions use IAM role-based authentication to DynamoDB (no credentials in code).
  - SSM Parameter Store provides basic secret storage capability.
- **Remediation Timeline**: 30 days
- **Recommendation**: Use AWS Secrets Manager for any agent API keys or service credentials. Convert the `github_connection_arn` SSM parameter to SecureString. Configure automatic secret rotation.
- **Evidence**: `template.yml` (Environment Variables: TABLE only), `pipeline/lib/pipeline-stack.ts` (StringParameter.fromStringParameterName for github_connection_arn)

### AUTH-Q8: Agent Identity Suspension

- **Severity**: RISK
- **Finding**: The Cognito User Pool supports disabling individual users via `adminDisableUser` API, which could disable an agent user. API Gateway usage plans could revoke API keys if they were configured (they are not). However, no explicit agent identity suspension mechanism exists because no agent identities are defined. The system has no concept of agent-specific accounts that can be individually suspended.
- **Gap**: No agent-specific identity suspension capability. No kill switch for individual agent instances.
- **Compensating Controls**:
  - Cognito `adminDisableUser` can serve as an emergency kill switch if agent accounts are created in the User Pool.
  - API Gateway can deploy a stage variable or Lambda authorizer to block specific principals.
- **Remediation Timeline**: 30 days
- **Recommendation**: When implementing agent identities (AUTH-Q1), include the ability to revoke individual agent client credentials immediately. Consider an API Gateway Lambda authorizer that checks a blocklist stored in DynamoDB or Parameter Store.
- **Evidence**: `template.yml` (CognitoUserPool with no agent-specific configuration)

### STATE-Q2: Queryable Current State

- **Severity**: RISK
- **Finding**: The `GET /books` endpoint performs a DynamoDB `Scan` operation and returns all books. This provides queryable current state at the collection level. However, there is no `GET /books/{isbn}` endpoint to query individual book state by key. An agent cannot check the current state of a specific book before deciding to update or create it. The only option is to scan the entire table and filter client-side.
- **Gap**: No individual resource query endpoint. Only full table scan available. Agent cannot perform efficient read-before-write checks.
- **Compensating Controls**:
  - Agent can call GET /books and filter results client-side by isbn (inefficient but functional for small datasets).
  - DynamoDB table structure supports individual GetItem queries — only the API endpoint is missing.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add a `GET /books/{isbn}` endpoint backed by a DynamoDB `GetItem` operation. This enables efficient state queries for individual records.
- **Evidence**: `src/books/get-all/index.ts` (DynamoDB Scan, no individual GetItem), `template.yml` (only GET /books and POST /books routes)

### STATE-Q3: Concurrency Controls

- **Severity**: RISK
- **Finding**: The `PutItem` operation in `src/books/create/index.ts` has no `ConditionExpression`, no version field, and no ETags. Two concurrent agents writing to the same `isbn` key will result in a last-write-wins scenario where the second write silently overwrites the first. No optimistic locking pattern is implemented. No `If-Match` headers are supported. DynamoDB supports conditional writes natively, but this capability is not used.
- **Gap**: No concurrency controls. Silent data loss on concurrent writes to the same key.
- **Compensating Controls**:
  - For a book catalog, concurrent writes to the same isbn are unlikely during initial pilot.
  - Limit agent concurrency to a single instance during pilot to prevent race conditions.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add a `version` attribute to book records and use `ConditionExpression: "attribute_not_exists(isbn) OR version = :expected_version"` on PutItem. Return the current version in GET responses for optimistic locking.
- **Evidence**: `src/books/create/index.ts` (PutItem with no ConditionExpression or version field)

### STATE-Q4: Circuit Breakers and Resilience

- **Severity**: RISK
- **Finding**: No circuit breaker patterns, retry logic with backoff, or timeout configurations exist in the Lambda function code. Both Lambda functions call DynamoDB directly without resilience wrappers. The AWS SDK has built-in retry logic (3 retries by default) but no circuit breaker. No Resilience4j, Polly, or equivalent library is used. The Lambda 5-second timeout acts as a coarse timeout boundary.
- **Gap**: No explicit circuit breaker or resilience patterns. DynamoDB failures cascade directly to the API response.
- **Compensating Controls**:
  - DynamoDB is a highly available managed service with built-in retry — circuit breakers are less critical for single-service-to-DynamoDB patterns.
  - Lambda 5-second timeout prevents indefinite hangs.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add explicit error handling that classifies DynamoDB errors (throttling vs. service unavailable vs. client error). Use AWS SDK retry configuration to implement exponential backoff with jitter.
- **Evidence**: `src/books/create/index.ts` (direct DynamoDB call, no resilience wrapper), `src/books/get-all/index.ts` (same pattern)

### STATE-Q5: Rate Limiting and Throttling

- **Severity**: RISK
- **Finding**: No explicit rate limiting or throttling is configured. The `BooksApi` in `template.yml` has no `ThrottlingBurstLimit` or `ThrottlingRateLimit` in MethodSettings. No API Gateway usage plan (`AWS::ApiGateway::UsagePlan`) is defined. No WAF rate-based rules exist. No application-level rate limiting middleware. API Gateway has default account-level throttling (10,000 requests/second burst, 5,000 steady-state) but no per-client or per-endpoint limits.
- **Gap**: No explicit rate limiting. A runaway agent loop could consume the entire API Gateway account-level quota, affecting other APIs in the same account.
- **Compensating Controls**:
  - API Gateway's default account-level throttling provides a coarse safety net.
  - Lambda concurrency limits can be set per function to cap throughput.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add API Gateway usage plans with rate limits per API key/client. Configure WAF rate-based rules. Set Lambda reserved concurrency to prevent runaway invocations.
- **Evidence**: `template.yml` (no ThrottlingBurstLimit, ThrottlingRateLimit, or UsagePlan resources)

### STATE-Q6: Blast Radius and Transaction Limits

- **Severity**: RISK
- **Finding**: No configurable transaction limits per agent identity. No maximum records per operation, no spend limits, no operation caps. The `POST /books` endpoint creates one book per request (no bulk endpoint), which naturally limits blast radius per API call. However, an agent could rapidly create thousands of books in a loop with no system-enforced limit.
- **Gap**: No configurable limits on agent-initiated actions. No max operations per session or per time window.
- **Compensating Controls**:
  - Single-record-per-request pattern naturally limits per-call blast radius.
  - DynamoDB on-demand capacity has a default initial throughput of 4,000 WCUs, providing a soft ceiling.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement agent-specific rate limits via API Gateway usage plans. Add application-level counters (e.g., max 100 books created per agent per hour) enforced in Lambda or via a DynamoDB counter.
- **Evidence**: `src/books/create/index.ts` (single PutItem per request, no limits), `template.yml` (no usage plans)

### STATE-Q7: Infrastructure Capacity for Agent Traffic

- **Severity**: RISK
- **Finding**: Lambda functions are configured with 512MB memory and 5-second timeout. DynamoDB uses `AWS::Serverless::SimpleTable` which defaults to on-demand capacity mode. Serverless architecture inherently handles traffic bursts better than fixed-capacity infrastructure. However, no load test results exist, no auto-scaling policies are explicitly configured (on-demand DynamoDB scales automatically), and no capacity planning documentation addresses agent traffic patterns. The GET /books endpoint performs a full table Scan which will become increasingly expensive as the table grows.
- **Gap**: No load testing for agent traffic patterns. No documentation of capacity limits. Full table scan on GET /books will not scale.
- **Compensating Controls**:
  - Serverless architecture (Lambda + DynamoDB on-demand) handles burst traffic well.
  - Lambda concurrency can be limited per function as a safety valve.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Run load tests simulating agent traffic patterns (burst writes, concurrent reads). Replace the full DynamoDB Scan in GET /books with a Query using pagination for scalability. Document capacity limits and expected agent throughput.
- **Evidence**: `template.yml` (MemorySize: 512, Timeout: 5, SimpleTable), `src/books/get-all/index.ts` (full DynamoDB Scan)

### HITL-Q1: Draft/Pending State

- **Severity**: RISK
- **Finding**: No draft or pending state concept exists. The `POST /books` endpoint in `src/books/create/index.ts` writes directly to DynamoDB with no intermediate state. There is no approval workflow, no two-step commit pattern (create-then-confirm), no status field in the book schema, and no state machine. A book is immediately live upon creation.
- **Gap**: No draft/pending state for agent-created records. All writes are immediately committed and visible.
- **Compensating Controls**:
  - Limit agent pilot to read-only operations (GET /books) until draft state is implemented.
  - Implement human review workflow externally (e.g., agent creates books in staging, human promotes to production).
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a `status` field to the book schema (`draft`, `published`, `archived`). Agent-created books default to `draft`. A separate `PATCH /books/{isbn}/publish` endpoint requires human approval to set status to `published`.
- **Evidence**: `src/books/create/index.ts` (direct PutItem, no status field), `template.yml` (no approval workflow resources)

### HITL-Q2: Configurable Approval Gates

- **Severity**: RISK
- **Finding**: The CI/CD pipeline has a `ManualApprovalAction` in `pipeline/lib/pipeline-stack.ts` for production deployment promotion. However, this is a deployment-time gate, not a runtime operation approval gate. No application-level approval endpoints exist. No Step Functions with human approval tasks (`waitForTaskToken`). No configurable operation-level flags to require human confirmation before execution.
- **Gap**: No runtime approval gates for high-risk agent operations. Deployment approval exists but runtime approval does not.
- **Compensating Controls**:
  - Use the staging environment as a manual review checkpoint — agents operate in staging, humans verify before production data changes.
  - Implement external approval workflows using SNS notifications + manual confirmation.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: For high-risk write operations, implement a Step Functions workflow with a `waitForTaskToken` human approval step. The agent submits a request, a human reviews and approves, and the Step Function completes the operation.
- **Evidence**: `pipeline/lib/pipeline-stack.ts` (ManualApprovalAction for deployment only)

### HITL-Q3: Sandbox/Staging Environment

- **Severity**: RISK
- **Finding**: The SAM template supports staging and production environments via the `Stage` parameter. The CI/CD pipeline (`pipeline/lib/pipeline-stack.ts`) deploys to staging first, runs end-to-end tests, then promotes to production with manual approval. The staging environment uses the same SAM template, creating an identical API Gateway + Lambda + DynamoDB architecture. The README documents local testing using Docker with a local DynamoDB container. However, there is no synthetic data generator or seed data script — the E2E tests create and clean up their own test data. The staging environment's data shape may differ from production.
- **Gap**: Staging environment exists with production-equivalent architecture but no production-equivalent data. No seed data scripts or synthetic data generators for realistic testing.
- **Compensating Controls**:
  - E2E tests create realistic test data dynamically (UUID-based isbns, structured book objects).
  - Local DynamoDB testing is documented in README.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Create seed data scripts that populate the staging DynamoDB table with a representative dataset matching production data distribution. Document the staging environment's endpoint for agent testing.
- **Evidence**: `template.yml` (Stage parameter: staging/production), `pipeline/lib/pipeline-stack.ts` (Staging → Test → Production pipeline), `README.md` (local DynamoDB testing instructions)

### DATA-Q1: Sensitive Data Classification

- **Severity**: RISK
- **Finding**: The DynamoDB `BooksTable` has tags for `project` and `environment` but no data classification tags (no sensitivity level, no PII tagging, no data-classification tag). The book schema contains: `isbn`, `title`, `year`, `author`, `publisher`, `rating`, `pages` — all bibliographic metadata with no PII, PHI, financial records, or credentials. SSE is enabled (`SSESpecification: SSEEnabled: true`). While the actual data is non-sensitive book catalog information, no formal data classification has been performed or documented.
- **Gap**: No formal data classification tags or documentation. Even though the book data appears non-sensitive, the absence of classification means there is no formal assertion that can be validated.
- **Compensating Controls**:
  - Book catalog data (isbn, title, year, author, publisher, rating, pages) contains no PII, PHI, or financial data — low inherent risk.
  - DynamoDB SSE provides encryption at rest.
- **Remediation Timeline**: 14 days
- **Recommendation**: Add a `data-classification: public` tag to the BooksTable in `template.yml`. Document the data classification decision in a `DATA_CLASSIFICATION.md` file. If the schema evolves to include customer data, re-classify.
- **Evidence**: `template.yml` (BooksTable tags: project, environment — no classification tag), `src/books/create/index.ts` (book schema: isbn, title, year, author, publisher, rating, pages)

### DATA-Q3: Selective Query Support

- **Severity**: RISK
- **Finding**: The `GET /books` endpoint in `src/books/get-all/index.ts` performs a DynamoDB `Scan` with no parameters — no pagination (`Limit`, `ExclusiveStartKey`), no filters (`FilterExpression`), no sorting, and no field selection. The entire table is returned in a single response. For a small book catalog this works, but as the table grows, responses will exceed LLM context window limits and increase token costs. No GraphQL field selection is available.
- **Gap**: No pagination, filtering, sorting, or result size limits. Unbounded result sets will exhaust agent context windows.
- **Compensating Controls**:
  - For small datasets (< 100 books), full scan responses are manageable within LLM context windows.
  - Agent tool definitions can post-process results client-side.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add query parameters to GET /books: `?limit=N`, `?cursor=LAST_KEY`, `?author=X`, `?year=Y`. Implement DynamoDB pagination using `Limit` and `ExclusiveStartKey`. Add a GSI for common query patterns.
- **Evidence**: `src/books/get-all/index.ts` (DynamoDB Scan with no Limit, FilterExpression, or ExclusiveStartKey)

### DATA-Q5: Reliable Timestamps

- **Severity**: RISK
- **Finding**: The book schema contains no timestamp fields. DynamoDB items contain only: `isbn`, `title`, `year`, `author`, `publisher`, `rating`, `pages`. No `created_at`, `updated_at`, or `event_time` fields. An agent cannot determine when a book record was created or last modified. The `year` field is the book's publication year, not a record timestamp.
- **Gap**: No record-level timestamps. Agent cannot perform time-sensitive reasoning about data currency.
- **Compensating Controls**:
  - DynamoDB Streams could provide event timestamps retroactively if enabled.
  - CloudTrail API logs capture operation timestamps at the infrastructure level.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add `created_at` and `updated_at` ISO 8601 UTC timestamp fields to the book schema. Set `created_at` on PutItem and `updated_at` on any updates. Return timestamps in GET responses.
- **Evidence**: `src/books/create/index.ts` (PutItem with isbn, title, year, author, publisher, rating, pages — no timestamps), `src/books/get-all/index.ts` (response maps same fields — no timestamps)

### DATA-Q6: Data Freshness Signaling

- **Severity**: RISK
- **Finding**: No data freshness signaling exists. Lambda responses do not include `Cache-Control` headers, `X-Data-Age` headers, or `last_refreshed` fields. No `consistency_level` field is returned. The `GET /books` endpoint uses DynamoDB `Scan` which defaults to eventually consistent reads — but this is not communicated to the caller. The agent has no way to know whether the data is current, stale, or cached.
- **Gap**: No data freshness metadata in API responses. No indication of consistency guarantees.
- **Compensating Controls**:
  - DynamoDB eventually consistent reads are typically milliseconds behind — freshness is generally not an issue for catalog data.
  - Agent tool definitions can document the expected consistency model.
- **Remediation Timeline**: 30 days
- **Recommendation**: Add `Cache-Control: no-cache` and `X-Consistency: eventual` headers to GET responses. For time-sensitive use cases, add `ConsistentRead: true` to the DynamoDB Scan parameters and return `X-Consistency: strong`.
- **Evidence**: `src/books/get-all/index.ts` (response headers include only Content-Type, no Cache-Control or freshness headers)

### DATA-Q7: PII Redaction in Logs

- **Severity**: RISK
- **Finding**: No PII redaction framework exists. Lambda error handlers return empty bodies (no PII leakage in error responses). The `create-pre-traffic` function logs DynamoDB items to `console.log` including test book data. API Gateway logging is set to `INFO` level for all resources and methods, which may capture full request/response bodies including any data submitted. No log scrubbing middleware, no PII masking libraries, no CloudWatch log filters for PII detection. The book data itself contains no PII (bibliographic metadata only), but the logging infrastructure has no PII protection if the schema evolves.
- **Gap**: No PII redaction framework. API Gateway INFO-level logging may capture request bodies. No Macie integration. No log scrubbing.
- **Compensating Controls**:
  - Current book data (isbn, title, year, author, publisher, rating, pages) contains no PII — low immediate risk.
  - Lambda error handlers return empty bodies, preventing PII leakage in error responses.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement structured logging with a PII redaction utility. Reduce API Gateway logging level to ERROR for production. If PII is added to the schema in the future, enable Amazon Macie for PII detection in logs.
- **Evidence**: `template.yml` (LoggingLevel: INFO for all resources), `src/books/create-pre-traffic/index.ts` (console.log of DynamoDB items)

### DISC-Q1: Schema Documentation and Versioning

- **Severity**: RISK
- **Finding**: No formal schema documentation or versioning exists. The book schema is implicitly defined in two Lambda functions (`src/books/create/index.ts` and `src/books/get-all/index.ts`) as: `isbn` (String), `title` (String), `year` (Number), `author` (String), `publisher` (String), `rating` (Number), `pages` (Number). The DynamoDB table definition in `template.yml` only declares the primary key (`isbn: String`). No JSON Schema files, no Avro/Protobuf schemas, no database migration files, no schema registry. Schema changes would require updating both Lambda functions manually with no versioning or migration path.
- **Gap**: No versioned schema definition. Schema is embedded in application code, not externalized. No migration path for schema changes.
- **Compensating Controls**:
  - The schema is simple (7 fields) and consistent between create and get-all functions.
  - Agent tool definitions can embed the schema directly.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Create a shared JSON Schema file (`schemas/book.json`) defining the book entity. Reference it in an OpenAPI specification. Version the schema (e.g., `v1`) and implement schema validation in the Lambda functions using a library like `ajv`.
- **Evidence**: `src/books/create/index.ts` (implicit schema in PutItem params), `src/books/get-all/index.ts` (implicit schema in response mapping), `template.yml` (SimpleTable with only PrimaryKey defined)

### OBS-Q1: Distributed Tracing and Structured Logging

- **Severity**: RISK
- **Finding**: X-Ray tracing is enabled: Lambda functions have `Tracing: Active` and API Gateway has `TracingEnabled: true` in `template.yml`. X-Ray SDK is imported and used in both Lambda functions (`aws-xray-sdk-core` captures AWS SDK calls). This provides distributed tracing with trace ID propagation through API Gateway → Lambda → DynamoDB. However, application-level logging uses unstructured `console.log` (seen in `src/books/create-pre-traffic/index.ts`). The main Lambda handlers (`create/index.ts`, `get-all/index.ts`) have no logging at all — not even error logging in catch blocks. No correlation ID or request_id field propagation in application logs. No structured JSON log format.
- **Gap**: Distributed tracing exists (X-Ray) but structured logging is absent. No application-level logging in main handlers. No correlation IDs in logs.
- **Compensating Controls**:
  - X-Ray provides full request-level tracing including DynamoDB call details and latency.
  - API Gateway access logs capture request metadata.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Adopt AWS Lambda Powertools for TypeScript, which provides structured JSON logging with automatic correlation ID injection, X-Ray trace ID in log entries, and log level management. Add logging to all handlers including error details in catch blocks.
- **Evidence**: `template.yml` (Tracing: Active, TracingEnabled: true), `src/books/create/index.ts` (no logging), `src/books/get-all/index.ts` (no logging), `src/books/create-pre-traffic/index.ts` (unstructured console.log)

### OBS-Q2: Alerting on Error Rates and Latency

- **Severity**: RISK
- **Finding**: CloudWatch Alarms are configured for Lambda Error metrics: `CreateBookAliasErrorMetricGreaterThanZeroAlarm` and `GetAllBooksAliasErrorMetricGreaterThanZeroAlarm`. These trigger when Lambda errors exceed 0, which is used by CodeDeploy to automatically rollback failed deployments. However, these alarms are designed for deployment safety, not operational monitoring. No latency alarms are configured (no P95/P99 latency thresholds). No anomaly detection. No integration with PagerDuty, OpsGenie, or SNS notification targets for on-call alerting. No composite alarms combining error rates and latency.
- **Gap**: Error rate alarms exist for deployment rollback only. No latency alarms. No operational alerting integration. No anomaly detection.
- **Compensating Controls**:
  - CloudWatch automatically captures Lambda duration and API Gateway latency metrics — alarms can be added without code changes.
  - X-Ray provides latency insights at the trace level.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add CloudWatch Alarms for API Gateway 5xx error rate, 4xx error rate, and P95 latency. Configure SNS topics for alarm notifications. Consider CloudWatch Anomaly Detection for baseline drift.
- **Evidence**: `template.yml` (CreateBookAliasErrorMetricGreaterThanZeroAlarm, GetAllBooksAliasErrorMetricGreaterThanZeroAlarm — deployment-focused only)

### ENG-Q1: Infrastructure Governance for Agent-Facing Surface

- **Severity**: RISK
- **Finding**: Infrastructure is defined as code: SAM template (`template.yml`) for application infrastructure (API Gateway, Lambda, DynamoDB, Cognito) and CDK (`pipeline/lib/pipeline-stack.ts`) for CI/CD pipeline. Changes flow through Git (GitHub → CodeStarConnectionsSourceAction in CodePipeline). Sub-check assessment: (1) **IaC defined** ✅ — full stack defined in SAM/CDK. (2) **Peer review** ⚠️ — implied by GitHub source integration but not enforced in the repository (no branch protection rules visible, no CODEOWNERS file). (3) **Drift detection** ❌ — no AWS Config rules, no `aws cloudformation detect-stack-drift` in pipeline, no drift detection configuration.
- **Gap**: Drift detection is missing. Peer review enforcement is not visible in the repository. 2 of 3 governance sub-checks are present or partially present.
- **Compensating Controls**:
  - All infrastructure is IaC-defined, reducing manual configuration drift risk.
  - CodePipeline ensures consistent deployment from source control.
- **Remediation Timeline**: 30 days
- **Recommendation**: Enable AWS Config rules for API Gateway, Lambda, DynamoDB, and IAM drift detection. Add a CODEOWNERS file requiring review for `template.yml` and `pipeline/` changes. Consider adding `aws cloudformation detect-stack-drift` as a pipeline step.
- **Evidence**: `template.yml` (full IaC definition), `pipeline/lib/pipeline-stack.ts` (CodePipeline from GitHub source, no drift detection)

### ENG-Q2: CI/CD with API Contract Testing

- **Severity**: RISK
- **Finding**: A comprehensive CI/CD pipeline exists: Source → Build (unit tests) → Staging (deploy + E2E tests) → Production (manual approval + deploy). Unit tests run via mocha (`pipeline/buildspec.json`: `npm test` in create/ and get-all/ directories). E2E tests (`pipeline/buildspec-test.json`) run against the staging deployment testing actual API endpoints with Cognito authentication. However, no API contract testing exists — no Pact tests, no OpenAPI spec validation in the build, no schema comparison tools. Breaking API changes (e.g., renaming a response field from `title` to `bookTitle`) would not be caught by contract tests.
- **Gap**: No API contract testing. No OpenAPI validation step. Breaking API changes are not automatically detected before they affect agents.
- **Compensating Controls**:
  - E2E tests validate API behavior at the integration level, catching some contract breaks.
  - Unit tests validate DynamoDB interactions and response structure.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add an OpenAPI specification and validate it in the build step. Implement consumer-driven contract testing using Pact. Add a CI step that compares the current API response schema against a baseline and fails on breaking changes.
- **Evidence**: `pipeline/buildspec.json` (npm test for unit tests), `pipeline/buildspec-test.json` (E2E tests), `src/books/tests/index.js` (E2E test suite — no contract testing)

### ENG-Q3: Rollback Capability

- **Severity**: RISK
- **Finding**: The deployment uses CodeDeploy with gradual traffic shifting: `Linear10PercentEvery1Minute` for production and `AllAtOnce` for staging. CloudWatch Alarms on Lambda errors trigger automatic rollback during gradual deployment. The `CreateBookPreTraffic` Lambda performs a smoke test before traffic is shifted to the new version. This is a robust rollback capability. However, `Linear10PercentEvery1Minute` means a full deployment takes ~10 minutes, and a rollback during this period reverts to the previous version. There is no instant rollback mechanism (no blue/green deployment, no feature flags).
- **Gap**: Rollback is deployment-time only (CodeDeploy). No runtime rollback mechanism (no feature flags). Full deployment takes ~10 minutes. No instant traffic shifting.
- **Compensating Controls**:
  - CodeDeploy automatic rollback on error alarms is a strong deployment safety mechanism.
  - Pre-traffic hooks validate new versions before any traffic shift.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Consider adding feature flags for agent-facing functionality to enable instant runtime kill switches. Evaluate Canary deployment type (e.g., `Canary10Percent5Minutes`) for faster initial validation.
- **Evidence**: `template.yml` (DeploymentPreference: Linear10PercentEvery1Minute, PreTraffic hooks, CloudWatch Alarms), `src/books/create-pre-traffic/index.ts` (smoke test logic)

### ENG-Q4: API Test Coverage

- **Severity**: RISK
- **Finding**: Unit tests exist for both Lambda functions: `src/books/create/tests/index.spec.ts` (3 tests: successful PutItem, invalid body handling, DynamoDB failure handling) and `src/books/get-all/tests/index.spec.ts` (3 tests: successful scan, empty results, DynamoDB failure handling). E2E tests exist in `src/books/tests/index.js` (4 tests: unauthenticated GET, GET with data, POST without token returns 401, POST with invalid payload returns 500, POST successful creation). Tests run in CI (buildspec.json for unit, buildspec-test.json for E2E). This provides reasonable coverage of happy paths and basic error scenarios. However, no explicit API contract tests exist, no edge case testing (e.g., oversized payloads, special characters, boundary values), and no load/performance tests.
- **Gap**: No API contract tests. No edge case or boundary testing. No load/performance tests. Test coverage is functional but not comprehensive for agent-generated inputs which may be unpredictable.
- **Compensating Controls**:
  - Unit and E2E tests cover core API functionality.
  - Pre-traffic hooks provide deployment-time validation.
- **Remediation Timeline**: 30 days
- **Recommendation**: Add API contract tests validating request/response schemas. Add edge case tests for malformed inputs, oversized payloads, and concurrent requests. Add load tests simulating agent traffic patterns.
- **Evidence**: `src/books/create/tests/index.spec.ts` (3 unit tests), `src/books/get-all/tests/index.spec.ts` (3 unit tests), `src/books/tests/index.js` (4 E2E tests), `pipeline/buildspec.json` (unit test execution), `pipeline/buildspec-test.json` (E2E test execution)

### ENG-Q5: Encryption at Rest for Agent-Accessible Data

- **Severity**: RISK
- **Finding**: DynamoDB table has `SSESpecification: SSEEnabled: true` — server-side encryption is enabled using AWS-managed keys. S3 artifact buckets in the CDK pipeline use `BucketEncryption.S3_MANAGED`. All data at rest is encrypted. However, no customer-managed KMS keys (CMK) are used — all encryption uses AWS-managed keys, which provides less control over key rotation, access policies, and key lifecycle management.
- **Gap**: Encryption at rest is enabled but uses AWS-managed keys, not customer-managed KMS keys. No KMS key policies for fine-grained access control.
- **Compensating Controls**:
  - AWS-managed SSE provides baseline encryption for all data at rest.
  - Book catalog data is non-sensitive bibliographic metadata — CMK may be over-engineering for this use case.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: For non-sensitive book data, AWS-managed SSE is acceptable. If the data model evolves to include sensitive data, migrate to customer-managed KMS keys with key policies restricting access to authorized principals only.
- **Evidence**: `template.yml` (SSESpecification: SSEEnabled: true on BooksTable), `pipeline/lib/pipeline-stack.ts` (BucketEncryption.S3_MANAGED on artifact buckets)

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO
- **Finding**: The application exposes a documented REST API via Amazon API Gateway with two endpoints: `GET /books` (public, no auth) and `POST /books` (Cognito-authenticated). Endpoints are defined in `template.yml` as SAM Events on Lambda functions. The API is served through API Gateway with stage-based deployment (staging/production). The README provides architectural documentation and usage instructions. No direct database access, file-based exchange, or UI automation patterns exist — this is a clean REST interface.
- **Implication**: The REST API surface is suitable for agent tool binding. Two well-defined endpoints with clear HTTP semantics (GET for retrieval, POST for creation) provide a predictable integration surface.
- **Recommendation**: This finding is positive — the REST interface exists. Complement it with an OpenAPI specification (API-Q2) for automated tool generation.
- **Evidence**: `template.yml` (GET /books ApiEvent, POST /books ApiEvent, BooksApi resource), `README.md` (architecture documentation)

### API-Q6: Structured Response Format

- **Severity**: INFO
- **Finding**: Both endpoints return JSON responses. `GET /books` returns `Content-Type: application/json` with a JSON array of book objects. `POST /books` returns `Content-Type: application/json` with HTTP 201 and an empty body on success. No XML, binary, or protobuf formats are used. JSON is the optimal format for LLM-based agent consumption.
- **Implication**: JSON responses are directly consumable by agent frameworks without additional parsing. The response format is agent-friendly.
- **Recommendation**: Consider returning the created book object in the POST /books response body (currently empty) to eliminate the need for a follow-up GET call.
- **Evidence**: `src/books/create/index.ts` (response headers: Content-Type: application/json), `src/books/get-all/index.ts` (JSON.stringify response body)

### API-Q8: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: No event emission capability exists. No SNS topics, EventBridge rules, SQS queues, Kafka topics, or webhook endpoints are configured. The `POST /books` endpoint creates a record in DynamoDB but does not publish an event when a book is created. No DynamoDB Streams are configured on the BooksTable. No CDC (Change Data Capture) pipelines.
- **Implication**: The API is request/response only. Proactive agent patterns (reacting to new books, catalog changes) are not possible without polling. For the current "product lookups" use case, request/response is sufficient.
- **Recommendation**: Consider enabling DynamoDB Streams and publishing book creation events to EventBridge for future event-driven agent patterns.
- **Evidence**: `template.yml` (no SNS, EventBridge, SQS, or DynamoDB Stream resources)

### API-Q9: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limit headers are returned in API responses (`X-RateLimit-Remaining`, `Retry-After`). No rate limit documentation exists. API Gateway has default account-level throttling but no per-API or per-client limits are configured. No `aws_api_gateway_usage_plan` resource exists in the IaC. Agents calling at machine speed have no way to self-throttle based on server-provided rate information.
- **Implication**: Without rate limit headers, agent tool definitions must implement client-side rate limiting based on assumed limits rather than server-provided signals.
- **Recommendation**: Configure API Gateway usage plans with documented rate limits. Add Lambda middleware to return `X-RateLimit-Remaining` and `Retry-After` headers in responses.
- **Evidence**: `template.yml` (no usage plans or throttling configuration), `src/books/create/index.ts` (no rate limit headers), `src/books/get-all/index.ts` (no rate limit headers)

### API-Q10: API Latency Profile

- **Severity**: INFO
- **Finding**: No performance benchmarks, load test results, or latency metrics documentation exists. Lambda functions are configured with 512MB memory and 5-second timeout. X-Ray tracing is enabled, which captures latency data at runtime (but no historical baseline is available in the repository). Expected latency: DynamoDB GetItem/PutItem operations are typically single-digit milliseconds; a full table Scan grows with table size. Lambda cold starts add ~100-500ms for Node.js runtimes.
- **Implication**: For a simple DynamoDB CRUD API, sub-second P95 latency is expected (excluding cold starts). This is well within acceptable range for synchronous agent tool calls. As the table grows, the full Scan on GET /books will increase in latency.
- **Recommendation**: Review X-Ray traces after deployment to establish a P95 latency baseline. Consider enabling Lambda Provisioned Concurrency to eliminate cold start latency for agent-critical endpoints.
- **Evidence**: `template.yml` (MemorySize: 512, Timeout: 5, Tracing: Active)

### DATA-Q4: System of Record Designations

- **Severity**: INFO
- **Finding**: The DynamoDB `BooksTable` is the single data store for book records — there is only one system of record. No other databases, caches, or external data sources are referenced. No master data management process is documented. No data ownership or system-of-record designations exist in documentation. The simple single-service architecture makes system-of-record designations less critical.
- **Implication**: With a single data store, system-of-record conflicts are unlikely. If the architecture evolves to include additional services or data stores, system-of-record designations will become necessary.
- **Recommendation**: Document the DynamoDB BooksTable as the authoritative system of record for book catalog data. Establish data ownership in a README or data governance document.
- **Evidence**: `template.yml` (single BooksTable resource), `src/books/create/index.ts` (writes to BooksTable only), `src/books/get-all/index.ts` (reads from BooksTable only)

### DATA-Q8: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality monitoring exists. No data profiling reports, no null rate monitoring, no duplicate detection, no data freshness SLAs, no data quality dashboards. The `POST /books` endpoint performs no input validation — if required fields are missing, the Lambda catches the error and returns HTTP 500 (as demonstrated in unit tests). No schema validation library (e.g., `ajv`, `joi`) is used.
- **Implication**: Without input validation, agents may insert incomplete or malformed book records. Without data quality monitoring, degradation would be undetected.
- **Recommendation**: Add input validation using a schema validation library (e.g., `ajv` with the JSON Schema from DISC-Q1). Add CloudWatch custom metrics for validation error rates and data completeness.
- **Evidence**: `src/books/create/index.ts` (no input validation, generic catch block), `src/books/create/tests/index.spec.ts` (test confirms invalid body returns 500)

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Field names are human-readable and semantically meaningful: `isbn`, `title`, `year`, `author`, `publisher`, `rating`, `pages`. No legacy abbreviations, no cryptic codes, no fields requiring a data dictionary to interpret. An LLM can reason about these field names without additional context.
- **Implication**: The data model is agent-friendly. LLMs can understand the schema from field names alone, reducing the need for additional schema documentation in tool definitions.
- **Recommendation**: Maintain this naming convention as the schema evolves. Avoid abbreviations in new fields.
- **Evidence**: `src/books/create/index.ts` (field names in PutItem), `src/books/get-all/index.ts` (field names in response mapping)

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No data catalog or metadata layer exists. No AWS Glue Data Catalog, no Collibra, Alation, or DataHub references. No metadata files beyond the README. The data model is simple enough (one table, seven fields) that a formal data catalog may be over-engineering for the current scope.
- **Implication**: Without a data catalog, agent tool builders must reverse-engineer the data model from source code. For a simple API, this is manageable. For larger systems, a catalog accelerates tool definition.
- **Recommendation**: Document the data model in the OpenAPI specification (API-Q2). For the current scope, formal catalog tooling is not required.
- **Evidence**: Repository-wide search found no data catalog configuration files or metadata definitions.

### DISC-Q4: Data Lineage

- **Severity**: INFO
- **Finding**: No data lineage records exist. No ETL pipeline documentation, no data flow diagrams (beyond the architecture image in README), no transformation logs, no source-to-target mappings. The data flow is simple: API Gateway → Lambda → DynamoDB (create) and DynamoDB → Lambda → API Gateway (read). No data transformations occur — book data is stored as received.
- **Implication**: The simple request → store → retrieve pattern has no data transformations that could introduce errors. Lineage tracking is not critical for the current scope but becomes important if data enrichment or ETL pipelines are added.
- **Recommendation**: Document the data flow in the OpenAPI specification or a separate architecture document. No formal lineage tooling is needed for the current scope.
- **Evidence**: `README.md` (architecture diagram reference), `src/books/create/index.ts` (direct PutItem, no transformation), `src/books/get-all/index.ts` (direct Scan, no transformation)

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No custom business outcome metrics are published. No `cloudwatch.put_metric_data` calls exist in the Lambda function code. No custom dashboards for business KPIs (books created per day, API adoption, catalog growth rate). Only infrastructure-level metrics exist (Lambda errors via CloudWatch Alarms).
- **Implication**: When agents consume the API, there will be no business-level signal to assess whether agent interactions produce good outcomes (e.g., catalog quality, creation accuracy). Only infrastructure metrics (errors, latency) will be available.
- **Recommendation**: Add custom CloudWatch metrics for business events: `BooksCreated` (count), `ValidationErrors` (count), `CatalogSize` (gauge). Create a CloudWatch dashboard combining infrastructure and business metrics.
- **Evidence**: `src/books/create/index.ts` (no custom metrics), `src/books/get-all/index.ts` (no custom metrics), `template.yml` (only Lambda Error alarms)

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: The application exposes REST endpoints via Amazon API Gateway: `GET /books` (public) and `POST /books` (Cognito-authenticated). Defined in `template.yml` as SAM Events. Clean REST interface with no direct database access, file-based exchange, or UI automation.
- **Gap**: N/A — REST API exists and is documented.
- **Recommendation**: Complement with an OpenAPI specification (API-Q2) for automated agent tool generation.
- **Evidence**: `template.yml`, `README.md`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK
- **Finding**: No OpenAPI, Swagger, AsyncAPI, GraphQL schema, or Smithy model files exist. `OpenApiVersion: 3.0.1` in Globals only prevents default stage creation — no actual spec file exists.
- **Gap**: No machine-readable API specification for agent tool generation.
- **Recommendation**: Create `openapi.yaml` and reference in SAM template via `DefinitionBody`.
- **Evidence**: `template.yml`

#### API-Q3: Structured Error Responses
- **Severity**: RISK
- **Finding**: Both Lambda functions return HTTP 500 with empty body on any error. No structured error codes, messages, or retryable indicators.
- **Gap**: No structured error response format. Agents cannot distinguish retryable from terminal errors.
- **Recommendation**: Implement standardized error responses with error code, message, and retryable flag.
- **Evidence**: `src/books/create/index.ts`, `src/books/get-all/index.ts`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: BLOCKER
- **Conditional**: agent_scope is "write-enabled" — evaluated as BLOCKER
- **Finding**: `POST /books` uses DynamoDB `PutItem` with no idempotency controls. No `ConditionExpression`, no idempotency key header, no deduplication. Agent retries will silently overwrite existing records.
- **Gap**: No idempotency on write operations.
- **Recommendation**: Add `ConditionExpression: "attribute_not_exists(isbn)"` and implement idempotency key support.
- **Evidence**: `src/books/create/index.ts`, `template.yml`

#### API-Q5: API Versioning and Deprecation
- **Severity**: RISK
- **Finding**: No versioning scheme. API path is `/books` with no version prefix. No changelog or deprecation policy.
- **Gap**: No API versioning. Breaking changes will silently break agent tool schemas.
- **Recommendation**: Add URL-based versioning (`/v1/books`) and establish deprecation policy.
- **Evidence**: `template.yml`

#### API-Q6: Structured Response Format
- **Severity**: INFO
- **Finding**: Both endpoints return JSON with `Content-Type: application/json`. Optimal for LLM-based agent consumption.
- **Gap**: N/A — JSON format is agent-friendly.
- **Recommendation**: Return created book in POST response body (currently empty).
- **Evidence**: `src/books/create/index.ts`, `src/books/get-all/index.ts`

#### API-Q7: Asynchronous Operation Support
- **Severity**: RISK
- **Finding**: No async patterns. Both Lambda functions synchronous with 5-second timeout. No SQS workers, Step Functions, or webhook callbacks.
- **Gap**: No async support for operations exceeding agent timeout thresholds.
- **Recommendation**: Implement async patterns if API expands to long-running operations.
- **Evidence**: `template.yml`, `src/books/create/index.ts`, `src/books/get-all/index.ts`

#### API-Q8: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: No event emission. No SNS, EventBridge, SQS, DynamoDB Streams, or webhook endpoints.
- **Gap**: No event-driven patterns for proactive agent workflows.
- **Recommendation**: Enable DynamoDB Streams and publish events to EventBridge.
- **Evidence**: `template.yml`

#### API-Q9: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit headers returned. No usage plans configured. No rate limit documentation.
- **Gap**: Agents cannot self-throttle based on server-provided rate limits.
- **Recommendation**: Configure usage plans and return rate limit headers.
- **Evidence**: `template.yml`, `src/books/create/index.ts`, `src/books/get-all/index.ts`

#### API-Q10: API Latency Profile
- **Severity**: INFO
- **Finding**: No performance benchmarks or latency metrics. Lambda timeout 5s, X-Ray tracing enabled. Expected sub-second P95 for DynamoDB operations.
- **Gap**: No documented latency baseline.
- **Recommendation**: Establish P95 baseline from X-Ray traces post-deployment.
- **Evidence**: `template.yml`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: Cognito User Pool with implicit grant and `USER_PASSWORD_AUTH` — human-oriented only. No client credentials flow, no API key auth with principal attribution, no mTLS.
- **Gap**: No machine identity authentication pathway for agents.
- **Recommendation**: Add Cognito App Client with client credentials grant and custom scopes.
- **Evidence**: `template.yml`, `src/books/create/index.ts`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK
- **Finding**: Lambda roles scoped via SAM policies (DynamoDBReadPolicy, DynamoDBWritePolicy). Agent-facing permissions unscoped — only `email` OAuth scope. Pipeline uses FullAccess managed policies.
- **Gap**: No agent-specific permission scoping.
- **Recommendation**: Define Cognito Resource Server with custom scopes. Narrow pipeline IAM policies.
- **Evidence**: `template.yml`, `pipeline/lib/pipeline-stack.ts`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK
- **Finding**: Endpoint-level auth only (GET public, POST requires token). No fine-grained RBAC/ABAC within resource types.
- **Gap**: Cannot restrict agent to specific actions within same resource type.
- **Recommendation**: Implement custom OAuth scopes per operation.
- **Evidence**: `template.yml`

#### AUTH-Q4: Identity Propagation
- **Severity**: RISK
- **Finding**: Cognito claims available in `event.requestContext.authorizer.claims` but Lambda ignores them entirely. User identity not extracted or propagated.
- **Gap**: Identity context available but unused. No end-to-end user context flow.
- **Recommendation**: Extract Cognito user ID and include in records and logs.
- **Evidence**: `src/books/create/index.ts`

#### AUTH-Q5: Agent-as-Self vs Agent-on-Behalf-of-User
- **Severity**: RISK
- **Finding**: No distinction between agent identity modes. Single Cognito User Pool for humans only. No service identity mechanism.
- **Gap**: Cannot distinguish agent-as-self from agent-on-behalf-of-user.
- **Recommendation**: Create separate client credentials flow for agent-as-self.
- **Evidence**: `template.yml`

#### AUTH-Q6: Credential Management
- **Severity**: RISK
- **Finding**: No Secrets Manager or Vault. Lambda env vars contain only TABLE name. Pipeline uses SSM StringParameter (not SecureString). No hardcoded credentials found.
- **Gap**: No secrets management for agent credentials.
- **Recommendation**: Use Secrets Manager for agent API keys with automatic rotation.
- **Evidence**: `template.yml`, `pipeline/lib/pipeline-stack.ts`

#### AUTH-Q7: Immutable Audit Logging ⚡
- **Severity**: BLOCKER
- **Conditional**: agent_scope is "write-enabled" — evaluated as BLOCKER
- **Finding**: API Gateway logging and X-Ray tracing enabled. No CloudTrail, no immutable log storage, no application-level audit logging of authenticated principal for writes.
- **Gap**: No immutable audit trail. No principal logging for write operations.
- **Recommendation**: Add CloudTrail, S3 object lock for logs, and principal logging in Lambda.
- **Evidence**: `template.yml`, `src/books/create/index.ts`

#### AUTH-Q8: Agent Identity Suspension
- **Severity**: RISK
- **Finding**: Cognito supports `adminDisableUser`. No agent-specific suspension mechanism because no agent identities exist.
- **Gap**: No agent-specific kill switch.
- **Recommendation**: Include identity revocation when implementing agent identities.
- **Evidence**: `template.yml`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: BLOCKER
- **Conditional**: agent_scope is "write-enabled" — evaluated as BLOCKER
- **Finding**: No compensation or rollback capability. Single PutItem operation, no delete endpoint, no saga pattern, no Step Functions.
- **Gap**: No rollback mechanism for multi-step agent workflows.
- **Recommendation**: Add DELETE endpoint and Step Functions for multi-step workflows.
- **Evidence**: `src/books/create/index.ts`, `template.yml`

#### STATE-Q2: Queryable Current State
- **Severity**: RISK
- **Finding**: GET /books returns all books via DynamoDB Scan. No GET /books/{isbn} for individual queries.
- **Gap**: No individual resource query endpoint.
- **Recommendation**: Add GET /books/{isbn} backed by DynamoDB GetItem.
- **Evidence**: `src/books/get-all/index.ts`, `template.yml`

#### STATE-Q3: Concurrency Controls
- **Severity**: RISK
- **Finding**: PutItem with no ConditionExpression. Last-write-wins on concurrent writes. No optimistic locking.
- **Gap**: Silent data loss on concurrent writes.
- **Recommendation**: Add version field and conditional writes.
- **Evidence**: `src/books/create/index.ts`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK
- **Finding**: No circuit breakers or retry logic. Direct DynamoDB calls without resilience wrappers. AWS SDK built-in retry only.
- **Gap**: No explicit resilience patterns.
- **Recommendation**: Add error classification and SDK retry configuration.
- **Evidence**: `src/books/create/index.ts`, `src/books/get-all/index.ts`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK
- **Finding**: No usage plans, no throttling config, no WAF rate rules. Default API Gateway account-level limits only.
- **Gap**: No per-client rate limiting to prevent runaway agents.
- **Recommendation**: Add API Gateway usage plans and Lambda reserved concurrency.
- **Evidence**: `template.yml`

#### STATE-Q6: Blast Radius and Transaction Limits
- **Severity**: RISK
- **Finding**: No transaction limits per agent. Single-record-per-request limits per-call blast radius, but no session/time-window caps.
- **Gap**: No configurable limits on agent-initiated actions.
- **Recommendation**: Implement agent-specific rate limits and application-level counters.
- **Evidence**: `src/books/create/index.ts`, `template.yml`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: RISK
- **Finding**: Serverless architecture (Lambda + DynamoDB on-demand) handles bursts. No load tests. Full table Scan on GET /books won't scale.
- **Gap**: No load testing for agent patterns. Scan-based reads won't scale.
- **Recommendation**: Load test with agent traffic patterns. Replace Scan with paginated Query.
- **Evidence**: `template.yml`, `src/books/get-all/index.ts`

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State
- **Severity**: RISK
- **Finding**: No draft/pending state. POST /books writes directly to DynamoDB with no intermediate state.
- **Gap**: All writes immediately committed and visible.
- **Recommendation**: Add status field (draft/published) to book schema.
- **Evidence**: `src/books/create/index.ts`, `template.yml`

#### HITL-Q2: Configurable Approval Gates
- **Severity**: RISK
- **Finding**: Pipeline has ManualApprovalAction for deployment. No runtime approval gates for agent operations.
- **Gap**: No runtime approval gates.
- **Recommendation**: Implement Step Functions with human approval tasks.
- **Evidence**: `pipeline/lib/pipeline-stack.ts`

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK
- **Finding**: Staging environment exists via Stage parameter with production-equivalent architecture. No seed data. E2E tests create own test data.
- **Gap**: Staging exists but lacks production-equivalent data.
- **Recommendation**: Create seed data scripts for staging.
- **Evidence**: `template.yml`, `pipeline/lib/pipeline-stack.ts`, `README.md`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: RISK
- **Finding**: No classification tags on BooksTable. Book data (isbn, title, year, author, publisher, rating, pages) is non-sensitive bibliographic metadata. SSE enabled.
- **Gap**: No formal data classification despite low inherent risk.
- **Recommendation**: Add `data-classification: public` tag to BooksTable.
- **Evidence**: `template.yml`, `src/books/create/index.ts`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: BLOCKER
- **Conditional**: agent_scope is "write-enabled" — evaluated as BLOCKER
- **Finding**: No residency requirements documented. Book catalog data is not subject to GDPR/LGPD/HIPAA. Single-region DynamoDB deployment. While the actual data (bibliographic metadata) carries no regulatory residency requirements, write-enabled agent scope requires a documented residency assessment before agent deployment.
- **Gap**: No formal documentation of data residency assessment. Write-enabled agents transmitting data to LLM providers require documented confirmation that no residency restrictions apply.
- **Recommendation**: Create DATA_CLASSIFICATION.md documenting residency assessment confirming no regulatory requirements for book catalog data. Include policy trigger for re-assessment if schema evolves.
- **Evidence**: `template.yml`, `src/books/create/index.ts`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK
- **Finding**: GET /books performs full DynamoDB Scan with no pagination, filters, or sorting. Unbounded result sets.
- **Gap**: No pagination or filtering. Responses will exceed agent context windows as table grows.
- **Recommendation**: Add pagination (limit, cursor), filters, and GSIs.
- **Evidence**: `src/books/get-all/index.ts`

#### DATA-Q4: System of Record Designations
- **Severity**: INFO
- **Finding**: Single DynamoDB table is the sole data store. No system-of-record conflicts possible in single-service architecture.
- **Gap**: Not formally documented but architecturally implicit.
- **Recommendation**: Document BooksTable as authoritative system of record.
- **Evidence**: `template.yml`, `src/books/create/index.ts`, `src/books/get-all/index.ts`

#### DATA-Q5: Reliable Timestamps
- **Severity**: RISK
- **Finding**: No timestamp fields in book schema. No created_at, updated_at, or event_time.
- **Gap**: Agent cannot determine data currency.
- **Recommendation**: Add created_at and updated_at ISO 8601 UTC timestamp fields.
- **Evidence**: `src/books/create/index.ts`, `src/books/get-all/index.ts`

#### DATA-Q6: Data Freshness Signaling
- **Severity**: RISK
- **Finding**: No Cache-Control headers, no X-Data-Age, no consistency signaling. DynamoDB Scan uses eventually consistent reads by default.
- **Gap**: Agent cannot determine data freshness.
- **Recommendation**: Add Cache-Control and consistency headers to GET responses.
- **Evidence**: `src/books/get-all/index.ts`

#### DATA-Q7: PII Redaction in Logs
- **Severity**: RISK
- **Finding**: No PII redaction framework. API Gateway logs at INFO level (may capture request bodies). Book data is non-PII but no protection if schema evolves.
- **Gap**: No PII protection in logging infrastructure.
- **Recommendation**: Implement structured logging with PII redaction. Reduce API Gateway log level for production.
- **Evidence**: `template.yml`, `src/books/create-pre-traffic/index.ts`

#### DATA-Q8: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality monitoring. No input validation. Invalid payloads produce HTTP 500.
- **Gap**: No data quality tracking or input validation.
- **Recommendation**: Add input validation with schema library and quality metrics.
- **Evidence**: `src/books/create/index.ts`, `src/books/create/tests/index.spec.ts`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Documentation and Versioning
- **Severity**: RISK
- **Finding**: Schema implicitly defined in Lambda code (7 fields). DynamoDB table defines only primary key. No JSON Schema, no migration files, no schema registry.
- **Gap**: No externalized, versioned schema definition.
- **Recommendation**: Create shared JSON Schema file and reference in OpenAPI spec.
- **Evidence**: `src/books/create/index.ts`, `src/books/get-all/index.ts`, `template.yml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Field names are human-readable and semantically clear: isbn, title, year, author, publisher, rating, pages. No legacy abbreviations.
- **Gap**: N/A — field names are agent-friendly.
- **Recommendation**: Maintain naming convention as schema evolves.
- **Evidence**: `src/books/create/index.ts`, `src/books/get-all/index.ts`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No data catalog. Simple schema (one table, 7 fields) may not warrant formal catalog tooling.
- **Gap**: No metadata layer for agent tool builders.
- **Recommendation**: Document data model in OpenAPI specification.
- **Evidence**: No catalog configuration files found.

#### DISC-Q4: Data Lineage
- **Severity**: INFO
- **Finding**: No data lineage records. Simple API Gateway → Lambda → DynamoDB flow with no transformations.
- **Gap**: No formal lineage documentation.
- **Recommendation**: Document data flow in architecture documentation.
- **Evidence**: `README.md`, `src/books/create/index.ts`, `src/books/get-all/index.ts`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK
- **Finding**: X-Ray tracing enabled (Lambda + API Gateway). Lambda functions have no application-level logging (no console.log, no structured logs). No correlation IDs. Pre-traffic hook uses unstructured console.log.
- **Gap**: Tracing exists but structured logging absent. No correlation IDs.
- **Recommendation**: Adopt AWS Lambda Powertools for structured JSON logging with X-Ray trace correlation.
- **Evidence**: `template.yml`, `src/books/create/index.ts`, `src/books/get-all/index.ts`, `src/books/create-pre-traffic/index.ts`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK
- **Finding**: CloudWatch Alarms for Lambda errors (deployment rollback triggers). No latency alarms. No anomaly detection. No operational alerting integration.
- **Gap**: Deployment-focused alerting only. No operational monitoring.
- **Recommendation**: Add API Gateway error rate and latency alarms with SNS notification.
- **Evidence**: `template.yml`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics. Only infrastructure-level Lambda error alarms.
- **Gap**: No business-level signal for agent interaction quality.
- **Recommendation**: Add CloudWatch custom metrics for BooksCreated, ValidationErrors, CatalogSize.
- **Evidence**: `src/books/create/index.ts`, `src/books/get-all/index.ts`, `template.yml`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK
- **Finding**: Full IaC (SAM + CDK). Git-based source control via CodePipeline. No drift detection. No CODEOWNERS file for peer review enforcement.
- **Gap**: Drift detection missing. Peer review not enforced.
- **Recommendation**: Enable AWS Config drift detection. Add CODEOWNERS file.
- **Evidence**: `template.yml`, `pipeline/lib/pipeline-stack.ts`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK
- **Finding**: Full CI/CD: Source → Build (unit tests) → Staging (deploy + E2E) → Production. No API contract testing (no Pact, no OpenAPI validation).
- **Gap**: Breaking API changes not caught by contract tests.
- **Recommendation**: Add OpenAPI validation and consumer-driven contract tests.
- **Evidence**: `pipeline/buildspec.json`, `pipeline/buildspec-test.json`, `src/books/tests/index.js`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK
- **Finding**: CodeDeploy Linear10PercentEvery1Minute with alarm-based automatic rollback. Pre-traffic hooks. ~10 minute deployment. No instant rollback or feature flags.
- **Gap**: No runtime rollback mechanism. Deployment-time only.
- **Recommendation**: Add feature flags for agent-facing functionality.
- **Evidence**: `template.yml`, `src/books/create-pre-traffic/index.ts`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK
- **Finding**: 3 unit tests per Lambda, 4 E2E tests. Tests run in CI. No API contract tests, no edge case tests, no load tests.
- **Gap**: Functional coverage but no contract, edge case, or performance tests.
- **Recommendation**: Add contract tests, edge case tests, and load tests.
- **Evidence**: `src/books/create/tests/index.spec.ts`, `src/books/get-all/tests/index.spec.ts`, `src/books/tests/index.js`, `pipeline/buildspec.json`, `pipeline/buildspec-test.json`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: RISK
- **Finding**: DynamoDB SSE enabled (AWS-managed keys). S3 buckets use S3_MANAGED encryption. No customer-managed KMS keys.
- **Gap**: AWS-managed encryption only. No CMK key policies.
- **Recommendation**: Acceptable for non-sensitive data. Migrate to CMK if schema evolves to include sensitive data.
- **Evidence**: `template.yml`, `pipeline/lib/pipeline-stack.ts`

#### ENG-Q6: Cross-Origin and Network Policies
- **Severity**: BLOCKER
- **Finding**: No CORS configuration on API Gateway or in Lambda responses. No WAF rules. No network policy documentation. No API Gateway resource policies.
- **Gap**: Agents calling from different origins will encounter CORS failures. No network security documentation.
- **Recommendation**: Add CORS to BooksApi SAM resource. Attach WAF WebACL. Document network posture.
- **Evidence**: `template.yml`, `src/books/create/index.ts`, `src/books/get-all/index.ts`

## Evidence Index

### Infrastructure as Code
| File | Questions Referenced |
|------|---------------------|
| `template.yml` | API-Q1, API-Q2, API-Q4, API-Q5, API-Q6, API-Q7, API-Q8, API-Q9, API-Q10, AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q5, AUTH-Q6, AUTH-Q7, AUTH-Q8, STATE-Q1, STATE-Q2, STATE-Q3, STATE-Q5, STATE-Q6, STATE-Q7, HITL-Q1, HITL-Q2, HITL-Q3, DATA-Q1, DATA-Q2, DATA-Q3, DATA-Q5, DATA-Q6, DATA-Q7, DISC-Q1, OBS-Q1, OBS-Q2, OBS-Q3, ENG-Q1, ENG-Q3, ENG-Q5, ENG-Q6 |
| `pipeline/lib/pipeline-stack.ts` | AUTH-Q2, AUTH-Q6, HITL-Q2, HITL-Q3, ENG-Q1, ENG-Q5 |
| `pipeline/bin/pipeline.ts` | ENG-Q1 |

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `src/books/create/index.ts` | API-Q3, API-Q4, API-Q6, API-Q7, AUTH-Q1, AUTH-Q4, AUTH-Q7, STATE-Q1, STATE-Q3, STATE-Q5, STATE-Q6, HITL-Q1, DATA-Q1, DATA-Q2, DATA-Q5, DISC-Q1, DISC-Q2, OBS-Q1, OBS-Q3, ENG-Q6 |
| `src/books/get-all/index.ts` | API-Q3, API-Q6, API-Q7, API-Q9, STATE-Q2, STATE-Q4, STATE-Q7, DATA-Q3, DATA-Q5, DATA-Q6, DISC-Q1, DISC-Q2, DISC-Q4, OBS-Q1, OBS-Q3, ENG-Q6 |
| `src/books/create-pre-traffic/index.ts` | DATA-Q7, OBS-Q1, ENG-Q3 |
| `src/books/tests/books-manager.js` | ENG-Q4 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `pipeline/buildspec.json` | ENG-Q2, ENG-Q4 |
| `pipeline/buildspec-deploy.json` | ENG-Q2 |
| `pipeline/buildspec-test.json` | ENG-Q2, ENG-Q4 |

### Test Files
| File | Questions Referenced |
|------|---------------------|
| `src/books/create/tests/index.spec.ts` | DATA-Q8, ENG-Q4 |
| `src/books/get-all/tests/index.spec.ts` | ENG-Q4 |
| `src/books/tests/index.js` | ENG-Q2, ENG-Q4 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `events/env.json` | (Inventory — local testing configuration) |
| `events/create-book-request.json` | (Inventory — sample API event) |
| `events/get-all-books-request.json` | (Inventory — sample API event) |
| `pipeline/cdk.json` | (Inventory — CDK configuration) |

### Documentation
| File | Questions Referenced |
|------|---------------------|
| `README.md` | API-Q1, HITL-Q3, DISC-Q4 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `src/books/create/package.json` | (Inventory — dependencies: aws-sdk, aws-xray-sdk-core) |
| `src/books/get-all/package.json` | (Inventory — dependencies: aws-sdk, aws-xray-sdk-core) |
| `src/books/create-pre-traffic/package.json` | (Inventory — dependencies: aws-sdk) |
| `src/books/tests/package.json` | (Inventory — dependencies: aws-sdk, axios, mocha, chai) |
| `pipeline/package.json` | (Inventory — dependencies: aws-cdk-lib, constructs) |

### Notable Absences — Files Not Found
| Expected Artifact | Impact |
|-------------------|--------|
| OpenAPI/Swagger specification file | API-Q2, DISC-Q1, ENG-Q2 |
| CloudTrail configuration | AUTH-Q7 |
| WAF / CORS configuration | ENG-Q6, STATE-Q5 |
| Secrets Manager resources | AUTH-Q6 |
| Data classification documentation | DATA-Q1, DATA-Q2 |
| Load test results | STATE-Q7, API-Q10 |
| CODEOWNERS file | ENG-Q1 |
| AWS Config rules | ENG-Q1 |

