# Agentic Readiness Analysis Report

**Target**: monolith
**Date**: 2026-05-18
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**TD Version**: agentic-readiness-analysis
**Repository Type**: application
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P0
**Tags**: monolith, php, containers
**Context**: PHP monolith with Docker and CloudFormation on App Runner — containerize and expose inventory APIs the agent needs for restocking decisions.

**Archetype Justification**: The application owns a MySQL database with 9 tables, exposes CRUD operations on business entities (orders, inventory, users, returns), and manages entity lifecycle (order status flow from pending through delivered). This matches the stateful-crud archetype.

**Surface flags**:
  - has_persistent_data_store: true
  - has_http_rpc_surface: true
  - has_auth_surface: true
  - has_write_operations: true
  - has_logging_of_user_data: true

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 1 | **RISK-SAFETY**: 9 | **RISK-QUALITY**: 13 | **INFOs**: 12

This repo has 1 BLOCKER finding and 9 RISK-SAFETY findings. Rule matched: "1-2 BLOCKER → Remediation Required".

Resolve all blockers before any agent deployment — including pilots. The system's lack of machine identity authentication (AUTH-Q1) is the primary deployment gate.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 1 |
| RISK-SAFETY | 9 |
| RISK-QUALITY | 13 |
| INFO | 12 |
| N/A | 0 |
| Not Evaluated (extended) | 2 |
| **Total** | **43** |

**Core Questions Evaluated**: 25
**Extended Questions Triggered**: 16
**Extended Questions Not Triggered**: 2
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: stateful-crud (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: The application uses session-based authentication only (PHP `session_start()` with cookie-based session tracking). Login requires POST /login with username/password, and session state is validated via `$_SESSION['user']`. There is no support for machine identity — no OAuth2 client credentials, no API key authentication with principal attribution, no mTLS, and no service account mechanism. An agent cannot authenticate via session cookies.
- **Gap**: No machine identity authentication mechanism exists. The system cannot distinguish which agent made a call, and cannot support autonomous agent authentication without browser-like session management.
- **Remediation**:
  - **Immediate**: Implement API key authentication with principal attribution alongside existing session auth. Add an `Authorization: Bearer <api-key>` header check that maps keys to named service accounts stored in the users table with role=agent.
  - **Target State**: OAuth2 client credentials flow or API key authentication with per-agent principal identity, logged in every request for audit attribution.
  - **Estimated Effort**: Medium
  - **Dependencies**: AUTH-Q6 (audit logging) depends on this — cannot log agent identity without machine identity.
- **Evidence**: index.php lines 236-240 (session-based auth check for all /api/* routes), infrastructure/monolith-apprunner.yaml (no API Gateway authorizer, no Cognito app client)

---

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q4: Identity Propagation and Delegation — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No identity propagation mechanism exists. The application has no JWT parsing, no OAuth2 on-behalf-of flows, no token exchange patterns. All requests are authenticated via PHP sessions with no distinction between agent-as-self vs agent-on-behalf-of-user.
- **Gap**: Cannot distinguish an agent acting under its own identity vs acting on behalf of a specific user. No mechanism to bound agent permissions to the delegating user's permissions.
- **Compensating Controls**:
  - Limit agent to its own service account with explicit, scoped permissions (no delegation)
  - Add X-On-Behalf-Of header support with server-side validation
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement JWT-based auth with token exchange support. The agent should be issued a scoped token that carries both agent identity and (optionally) delegated user context.
- **Evidence**: index.php (no JWT libraries, no token parsing middleware, session-only auth)

#### AUTH-Q5: Credential Management — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Database credentials are passed directly as environment variables in both docker-compose.yml (`DB_PASS: ${MYSQL_PASSWORD}`) and CloudFormation (`DB_PASS` in RuntimeEnvironmentVariables from `!Ref DBPassword`). No secrets management system is used — no AWS Secrets Manager, no HashiCorp Vault, no credential rotation mechanism.
- **Gap**: Credentials are not managed through a secrets management system with rotation. Environment variables in App Runner configuration are not encrypted at rest with customer-managed keys and cannot be rotated without redeployment.
- **Compensating Controls**:
  - CloudFormation uses NoEcho for password parameters (prevents display in console)
  - RDS has IAM database authentication enabled (`EnableIAMDatabaseAuthentication: true`) but is not used by the application
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Migrate database credentials to AWS Secrets Manager with automatic rotation. Update the application to fetch credentials from Secrets Manager at runtime or use RDS IAM authentication (already enabled on the RDS instance).
- **Evidence**: docker-compose.yml (DB_PASS environment variable), infrastructure/monolith-apprunner.yaml (DBPassword passed as runtime env var), index.php lines 15-19 (getenv('DB_PASS') with hardcoded fallback 'ecommerce_pass')

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No immutable audit logging exists. The `order_status_history` table records who changed an order status (`changed_by` field), but this is mutable database storage — not tamper-evident. No CloudTrail configuration exists in the IaC. No S3 bucket with object lock for logs. VPC Flow Logs exist (encrypted with KMS, 30-day retention) but capture network traffic, not application-level audit events.
- **Gap**: No immutable, tamper-evident audit trail for API actions. Cannot prove whether an action was taken by a human or an agent. Application-level status history is stored in the same mutable database.
- **Compensating Controls**:
  - VPC Flow Logs capture network-level activity (infrastructure/monolith-apprunner.yaml)
  - App Runner sends stdout/stderr to CloudWatch Logs (via AppRunnerInstanceRole)
  - order_status_history table provides basic application-level change tracking
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add CloudTrail configuration to the CloudFormation template. Implement structured application-level audit logging that writes to CloudWatch Logs with a separate, immutable log group (S3 export with object lock).
- **Evidence**: infrastructure/monolith-apprunner.yaml (VPCFlowLog configured but no CloudTrail), index.php (order_status_history table in mutable MySQL)

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No mechanism exists to suspend or revoke individual agent identities without affecting other users. The only auth mechanism is session-based — there are no API keys to revoke, no service accounts to disable, and no mechanism to invalidate a specific agent's access independently.
- **Gap**: Cannot isolate a misbehaving agent without taking down the application or destroying all sessions.
- **Compensating Controls**:
  - WAF IP whitelist could be updated to block a specific agent's IP (slow, manual process)
  - Could delete the agent's user account from the database (requires direct DB access)
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement API key-based auth (prerequisite: AUTH-Q1) with per-key revocation. Add an admin endpoint to disable individual service accounts immediately.
- **Evidence**: index.php (session-based auth only), infrastructure/monolith-apprunner.yaml (WAF IP whitelist — coarse-grained)

#### STATE-Q1: Compensation and Rollback ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Database transactions with rollback exist for individual multi-step operations (order creation at line ~302 and return approval at line ~1390). However, the 7-step fulfillment workflow (validate → assign-warehouse → pick → pack → quality-check → ship → deliver) has no workflow-level compensation. Each step is an independent API call with no saga pattern or compensating actions if a downstream step fails.
- **Gap**: No workflow-level compensation. If the fulfillment workflow fails at step 5 (quality-check), steps 1-4 (validate, assign-warehouse, pick, pack) cannot be automatically rolled back.
- **Compensating Controls**:
  - Individual operations use database transactions (`beginTransaction()`/`rollBack()`)
  - Order status tracking allows manual intervention (order_status_history table)
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement a saga pattern for the fulfillment workflow with explicit compensating actions for each step (e.g., un-assign warehouse, release inventory reservation).
- **Evidence**: index.php lines 302-350 (transaction for order creation), lines 1045-1200 (independent fulfillment steps without compensation)

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No rate limiting exists at the application level. The WAF configuration uses IP whitelisting (allow specific IP, block all others) but contains no rate-based rules. App Runner's MaxConcurrency (100) is a resource limit, not rate limiting. No application-level rate limiting middleware is present.
- **Gap**: No rate limits to prevent a runaway agent loop from overwhelming the application. An agent making rapid requests within the allowed IP range would not be throttled.
- **Compensating Controls**:
  - WAF IP whitelist limits access to known IPs only
  - App Runner MaxConcurrency (100) provides a hard ceiling on concurrent requests per instance
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add WAF rate-based rules (e.g., 100 requests/5 minutes per IP). Additionally, implement application-level rate limiting middleware or add an API Gateway in front of App Runner with usage plans and throttling.
- **Evidence**: infrastructure/monolith-apprunner.yaml (WebACL with IP whitelist only, no rate rules; AutoScaling MaxConcurrency: 100), index.php (no rate limiting middleware)

#### DATA-Q1: Sensitive Data Classification ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — B1 evaluated as RISK-SAFETY
- **Finding**: Stage A: System stores sensitive data — customer PII (names, emails, addresses), payment records, and password hashes. Stage B evaluation:
  - **B1 (RISK-SAFETY)**: API responses include customer PII (email, name, shipping address) in general order endpoints that an inventory/restocking agent has no business retrieving. `GET /api/admin/orders/pending-fulfillment` returns full customer details. Password field IS properly excluded from user list endpoint (`SELECT id, username, name, email, role, created_at FROM users`) and from session storage (`unset($user['password'])`).
  - **B2 (CLEAR)**: Access control differentiation exists — admin vs customer roles restrict endpoint access. Admin sees all orders; customers see only their own.
  - **B3 (INFO)**: No formal data classification metadata, no sensitivity tags, no Macie integration.
- **Gap**: Agent-facing API responses include customer PII fields (email, name, shipping_address) that are not needed for inventory/restocking decisions. No field-level filtering or separate DTOs for agent consumers.
- **Compensating Controls**:
  - Create a dedicated read-only inventory endpoint that returns only product/stock data without customer PII
  - Implement field-level response filtering based on caller role
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create agent-specific API endpoints or response DTOs that exclude customer PII. For the restocking use case, the agent only needs inventory data (product_id, stock_quantity, warehouse_location) — not customer details.
- **Evidence**: index.php line 1280 (`SELECT * FROM orders` returns customer_name, customer_email, shipping_address), index.php line 1437 (user list excludes password), index.php lines 170-175 (password excluded from session)

#### DATA-Q2: Data Residency and Sovereignty ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The system stores customer PII and payment data with no explicit data residency documentation or policy. RDS is deployed in a single region (determined by CloudFormation stack deployment region) but there are no controls preventing data from being transmitted to an LLM provider in another jurisdiction. No GDPR/LGPD compliance references, no data sovereignty policies, no cross-region transfer controls.
- **Gap**: No data residency policy defined. No technical controls prevent customer data from being sent cross-region to an LLM endpoint.
- **Compensating Controls**:
  - Limit agent to use Amazon Bedrock in the same region as the RDS deployment
  - Use VPC endpoints for Bedrock to ensure data stays within the AWS network
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Document data residency requirements. Configure the agent to use region-local LLM endpoints (Amazon Bedrock in the same region). Implement data classification tags on the RDS instance and add data processing policies.
- **Evidence**: infrastructure/monolith-apprunner.yaml (no region constraints beyond stack deployment region, no data residency tags)

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No PII redaction in logs. PHP error logging is enabled (`ini_set('log_errors', '1')`) and exceptions that include customer data (e.g., PDOException with query context) could be logged without redaction. No log scrubbing middleware, no PII masking libraries, no CloudWatch log filters for PII detection.
- **Gap**: Customer PII (names, emails, addresses) could appear in error logs if exceptions occur during request processing. No automated PII detection or redaction.
- **Compensating Controls**:
  - PHP `display_errors` is disabled (errors go to logs, not responses)
  - App Runner CloudWatch Logs have limited access (scoped IAM role)
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement structured logging with PII field exclusion. Add CloudWatch Logs data protection policies to detect and mask PII patterns (emails, names, addresses) before storage.
- **Evidence**: index.php lines 9-11 (error_reporting and log_errors enabled, display_errors disabled), infrastructure/monolith-apprunner.yaml (no log data protection configuration)

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, GraphQL schema, or any machine-readable API specification exists. The 26+ REST endpoints are defined only in PHP source code (index.php) with no accompanying specification file. Searched for: openapi.*, swagger.*, *.graphql, *.gql, *.smithy — none found.
- **Gap**: Agent tool generation requires manual authoring of tool definitions by reading source code. No machine-readable spec to auto-generate agent tools.
- **Compensating Controls**:
  - Manually document the API surface for agent tool generation
  - Use API testing tools to reverse-engineer an OpenAPI spec from the running application
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Generate an OpenAPI 3.0 specification documenting all endpoints, request/response schemas, and error codes. Tools like swagger-php annotations or manual authoring can produce this from the existing code.
- **Evidence**: Repository root (no openapi.yaml, no swagger.json, no API spec files of any kind)

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Error responses are JSON with an `error` field and appropriate HTTP status codes (400, 401, 403, 404, 500), but lack structured error codes, retryable indicators, and consistent error categorization. Format is simply `{"error": "message string"}` — no error code, no retryable flag, no field-level detail.
- **Gap**: Agents cannot distinguish retriable errors from terminal errors. No machine-readable error categorization beyond HTTP status codes.
- **Compensating Controls**:
  - HTTP status codes provide basic error categorization (4xx vs 5xx)
  - Error messages are human-readable and reasonably descriptive
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement structured error responses: `{"error": {"code": "INSUFFICIENT_INVENTORY", "message": "...", "retryable": false, "field": "quantity"}}`.
- **Evidence**: index.php (multiple instances of `json_encode(['error' => $e->getMessage()])` and `json_encode(['error' => 'Order not found'])`)

#### STATE-Q7: Graceful Degradation Signaling — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No degraded mode signaling. The application has no health headers, no `X-Degraded` response headers, no `Cache-Control` headers, no `Retry-After` headers on errors. App Runner health checks only detect complete failure (up/down), not degraded state.
- **Gap**: An agent cannot detect whether it is receiving stale, partial, or fallback responses. If the database is slow or a dependency is degraded, responses appear normal.
- **Compensating Controls**:
  - App Runner health checks will take instances out of rotation on complete failure
  - Database connection failures result in immediate 500 errors (clear failure signal)
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add response headers indicating data freshness (`X-Data-Age`, `Cache-Control`). Implement a /health endpoint returning granular states (healthy, degraded, read-only).
- **Evidence**: index.php (no Cache-Control or custom headers in any response), infrastructure/monolith-apprunner.yaml (health check is HTTP GET / only)

#### DATA-Q3: Selective Query Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No pagination, filtering, or result set limiting. All query endpoints return complete result sets: `GET /api/products` returns all inventory (`SELECT * FROM inventory`), `GET /api/orders/me` returns all customer orders, `GET /api/admin/orders/pending-fulfillment` returns all pending orders. No `LIMIT`, `OFFSET`, cursor, or filter parameters.
- **Gap**: Agent retrieving product inventory or order lists will receive unbounded result sets that grow with data volume. Exhausts LLM context windows and increases cost.
- **Compensating Controls**:
  - Current data set is small (5 products, few orders) — won't hit limits immediately
  - Agent can filter results client-side
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add pagination parameters (`?limit=50&offset=0`) to list endpoints. Add filter support (`?category=Clothing&in_stock=true`) for inventory queries relevant to the restocking agent.
- **Evidence**: index.php line 244 (`SELECT * FROM inventory` — no LIMIT), line 1280 (`SELECT * FROM orders WHERE status IN (...)` — no pagination)

#### DATA-Q4: Input Validation and Schema Enforcement — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Minimal input validation exists. Some required field checks (`empty($data['username'])`) and inventory stock validation, but no systematic validation framework. No input length limits, no email format validation, no type checking on JSON fields. SQL injection is prevented (prepared statements used consistently), but business rule validation is sparse. Error responses for validation failures are unstructured (`{"error": "All fields are required"}`) with no field-level detail.
- **Gap**: An LLM constructing API calls could send malformed payloads (oversized strings, wrong types, missing nested fields) without structured rejection. No field-level error feedback for self-correction.
- **Compensating Controls**:
  - Prepared statements prevent SQL injection
  - Stock quantity validation prevents overselling
  - Unique constraints on username/email prevent duplicates
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a validation layer (PHP validation library or manual schema validation) that validates all input fields and returns structured errors with field name, constraint violated, and accepted format.
- **Evidence**: index.php lines 1430-1445 (basic empty checks for user creation), line 316 (stock quantity check), no validation library in use

#### DATA-Q5: Temporal Metadata and Freshness — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Database tables include `created_at` and `updated_at` DATETIME fields on orders and order_status_history. However, no timezone handling is documented (MySQL defaults to server timezone), no `Cache-Control` headers are set on API responses, and no freshness/staleness signaling exists. An agent cannot determine whether data is current or stale.
- **Gap**: No API-level freshness signaling. No `Cache-Control`, `X-Data-Age`, or consistency-level metadata in responses. Timestamps exist in data but timezone normalization is not explicit.
- **Compensating Controls**:
  - All queries go directly to the database (no caching layer), so responses are always current
  - created_at/updated_at fields enable client-side freshness calculation
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `Last-Modified` or `X-Data-Freshness: current` headers to API responses. Store timestamps in UTC explicitly. Document the data consistency model (always-current from single MySQL).
- **Evidence**: index.php (schema definitions with created_at/updated_at DATETIME fields, no Cache-Control headers in responses)

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No API versioning — endpoints have no version prefix (e.g., `/api/orders` not `/v1/api/orders`). No schema files (JSON Schema, Avro, Protobuf). No database migration files (schema created via `CREATE TABLE IF NOT EXISTS`). No changelog, no deprecation notices, no breaking change detection. No consumer-driven contract tests.
- **Gap**: Any API change will silently break agent tool bindings. No mechanism to detect or communicate breaking changes.
- **Compensating Controls**:
  - Small team/single repo makes unannounced breaking changes less likely
  - Agent tool definitions can be manually updated when API changes
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add API version prefix (`/v1/`). Generate and commit an OpenAPI spec. Add schema comparison in CI to detect breaking changes before deployment.
- **Evidence**: index.php (all routes unversioned: `/api/products`, `/api/orders`), repository root (no schema files, no changelog)

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No distributed tracing (no OpenTelemetry, no X-Ray SDK). No structured logging — only PHP's built-in `error_log()` producing unstructured text. No correlation IDs, no request IDs, no trace context propagation. App Runner provides basic stdout/stderr log forwarding to CloudWatch but with no structure.
- **Gap**: Cannot reconstruct what happened inside the application when an agent-initiated request fails. No way to trace a request across the system.
- **Compensating Controls**:
  - App Runner forwards application logs to CloudWatch
  - VPC Flow Logs capture network-level traffic
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add structured JSON logging with a request_id generated per request. Integrate AWS X-Ray SDK for PHP to enable distributed tracing. Pass trace context in response headers.
- **Evidence**: index.php lines 9-11 (error_reporting/log_errors only), infrastructure/monolith-apprunner.yaml (no X-Ray configuration)

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No alerting thresholds configured. The CloudFormation template defines no CloudWatch Alarms. WAF metrics are enabled (`CloudWatchMetricsEnabled: true`) but no alarms trigger on them. No PagerDuty/OpsGenie integration. No SLO-based alerting.
- **Gap**: Target system degradation affecting agents will not be detected until users report issues. No automated alerts for error rate spikes or latency increases.
- **Compensating Controls**:
  - WAF CloudWatch metrics exist (can be alarmed on manually post-deployment)
  - App Runner provides basic service health monitoring in console
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add CloudWatch Alarms for: HTTP 5xx rate > 5%, P99 latency > 5s, WAF blocked request spike. Configure SNS notifications.
- **Evidence**: infrastructure/monolith-apprunner.yaml (no AWS::CloudWatch::Alarm resources)

#### ENG-Q1: Infrastructure Governance — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Infrastructure is defined as CloudFormation IaC (monolith-apprunner.yaml). However, no CI/CD pipeline enforces review before deployment. No PR/CR review requirements are configured (no branch protection, no required reviewers). No drift detection (no AWS Config rules, no CloudFormation drift detection automation). Deploy is via manual `deploy.sh` script.
- **Gap**: IaC exists but changes are not subject to automated review or drift monitoring. Manual deployment process bypasses peer review.
- **Compensating Controls**:
  - CloudFormation provides declarative state management (prevents ad-hoc changes via console)
  - Git history provides an audit trail of IaC changes
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add a CI/CD pipeline with required PR approval for infrastructure changes. Enable CloudFormation drift detection on a schedule. Add cfn-lint/cfn-nag to validate templates before deployment.
- **Evidence**: infrastructure/monolith-apprunner.yaml (IaC exists), deploy.sh (manual deployment), no CI/CD configuration files

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No CI/CD pipeline exists. No GitHub Actions, no GitLab CI, no Jenkinsfile, no buildspec.yml. Deployment is manual via `deploy.sh` (docker-compose build + up). No API contract tests, no schema validation in build, no breaking change detection.
- **Gap**: API contract changes cannot be caught before agents are affected. No automated testing or deployment pipeline.
- **Compensating Controls**:
  - Docker Compose health checks validate the app starts and responds
  - Manual testing before deployment
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Create a CI/CD pipeline (GitHub Actions or CodePipeline) with API contract testing. Add OpenAPI spec validation and response schema tests.
- **Evidence**: Repository root (no .github/workflows, no .gitlab-ci.yml, no Jenkinsfile, no buildspec.yml), deploy.sh (manual deployment only)

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No automated rollback capability configured. App Runner supports manual rollback by redeploying a previous ECR image (immutable tags enabled), but no automatic rollback triggers exist. No blue/green deployment, no canary, no CodeDeploy, no traffic shifting.
- **Gap**: A broken deployment affecting agents requires manual intervention to roll back. No automated detection or rollback on failure.
- **Compensating Controls**:
  - ECR immutable tags allow deploying a previous known-good image
  - App Runner supports manual revision rollback via console/CLI
  - Health checks will prevent unhealthy instances from receiving traffic
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Configure App Runner auto-rollback on health check failure. Alternatively, add CodeDeploy with automatic rollback triggers or implement blue/green deployment.
- **Evidence**: infrastructure/monolith-apprunner.yaml (no rollback configuration, no canary deployment), ECRRepository (ImageTagMutability: IMMUTABLE — supports previous image selection)

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No automated tests exist whatsoever. No test files, no PHPUnit, no API test suites, no integration tests, no contract tests. The repository contains zero test infrastructure.
- **Gap**: No verification that API behavior matches expectations. Changes can silently break agent tool contracts with no detection.
- **Compensating Controls**:
  - Docker Compose health check validates basic endpoint availability
  - Manual testing before deployment
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add PHPUnit with API integration tests covering core endpoints: inventory listing, order creation, status transitions. Prioritize tests for agent-facing endpoints (GET /api/products, GET /api/orders/{id}/validation-data).
- **Evidence**: Repository (no test files, no PHPUnit configuration, no *Test.php files)

---

## INFOs — Architecture and Design Inputs

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Write endpoints are not idempotent. Order IDs are generated with `uniqid()` (not guaranteed unique under concurrency). No idempotency key support on POST endpoints. Repeated POST /api/orders creates duplicate orders.
- **Implication**: If agent scope expands to write-enabled, this becomes a BLOCKER. Retry logic would create duplicate orders/records.
- **Recommendation**: When write-enabled scope is planned, implement idempotency keys on POST endpoints (accept client-generated request ID, deduplicate within a time window).
- **Evidence**: index.php line 305 (`$order_id = uniqid('order-')` — no idempotency key)

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: All API responses use structured JSON format (`Content-Type: application/json`). Responses are well-structured with meaningful key names and appropriate data types.
- **Implication**: JSON format is ideal for LLM consumption. No extra parsing required for agent tool responses.
- **Recommendation**: No action needed — JSON is the preferred format for agent integration.
- **Evidence**: index.php line 233 (`header('Content-Type: application/json')`)

### API-Q7: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: No event emission capability. No webhooks, no SNS/EventBridge integration, no Kafka topics. All state changes are synchronous and stored only in the database. The order_status_history table captures transitions but does not emit events.
- **Implication**: Agents cannot react proactively to state changes (e.g., when inventory drops below restock threshold). Polling is the only detection mechanism.
- **Recommendation**: For the restocking use case, consider adding EventBridge events when stock_quantity drops below a threshold, enabling proactive restocking decisions.
- **Evidence**: index.php (no event publishing code, no SNS/SQS/EventBridge SDK usage)

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limit documentation. No `X-RateLimit-Remaining` or `Retry-After` headers in responses. WAF does not include rate-based rules. App Runner MaxConcurrency (100) is not communicated to callers.
- **Implication**: An agent has no visibility into system capacity limits. Cannot self-throttle before hitting limits.
- **Recommendation**: Add rate limit headers to responses once rate limiting (STATE-Q5) is implemented.
- **Evidence**: index.php (no rate limit headers), infrastructure/monolith-apprunner.yaml (MaxConcurrency: 100 not exposed to callers)

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No optimistic locking. No version fields, no ETags, no `If-Match` headers. Inventory updates use `stock_quantity = stock_quantity - ?` (atomic SQL decrement) which provides basic concurrency safety for decrements, but no broader concurrency control pattern.
- **Implication**: If agent scope expands to write-enabled, concurrent agent instances could create race conditions on order status updates and warehouse assignments.
- **Recommendation**: Add version fields to orders and inventory tables. Implement optimistic locking with conditional updates when write-enabled scope is planned.
- **Evidence**: index.php line 338 (atomic SQL decrement for inventory — basic safety), no version/ETag fields in schema

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No transaction limits exist. No per-caller limits on records modified, no spend caps, no operation count limits. A write-enabled agent could theoretically process unlimited orders or approve unlimited returns.
- **Implication**: If agent scope expands to write-enabled, there are no business-domain caps on agent action volume.
- **Recommendation**: When planning write-enabled scope, add configurable per-agent transaction limits (e.g., max_orders_per_hour, max_refund_amount_per_session).
- **Evidence**: index.php (no transaction limit checks in any endpoint)

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The returns system has a `pending_review` status that serves as a draft/approval state — return requests must be manually approved by an admin before processing. Orders start as `pending` then move to `confirmed`. These represent existing reviewable intermediate states.
- **Implication**: The pattern exists for returns but not for other operations. Could be extended for agent-proposed actions if scope expands.
- **Recommendation**: No action needed for read-only scope. The existing pending_review pattern is a good foundation if write-enabled scope is planned.
- **Evidence**: index.php line 1320 (return status = 'pending_review'), order status flow starts with 'pending'

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The return approval flow requires explicit admin action (`POST /api/admin/approve-return`). This is a hard-coded approval gate for one operation type. Not configurable per operation — only returns require approval.
- **Implication**: Approval gates exist for returns but are not configurable or extensible to other operations.
- **Recommendation**: No action for read-only scope. If expanding to write-enabled, make approval requirements configurable per operation type.
- **Evidence**: index.php lines 1356-1420 (admin approve-return endpoint with explicit approval flow)

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality metrics, no completeness scores, no null rate monitoring, no freshness SLAs. Seed data provides initial state but no ongoing quality monitoring.
- **Implication**: An agent cannot assess whether inventory data is reliable before making restocking decisions.
- **Recommendation**: Add basic data quality checks: inventory last-updated timestamps, stock count accuracy verification.
- **Evidence**: index.php (no data quality logic), no monitoring configuration

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Field names are semantically meaningful and human-readable: `customer_name`, `stock_quantity`, `shipping_address`, `total_amount`, `warehouse_location`, `tracking_number`, `payment_method`. No legacy abbreviations or cryptic codes.
- **Implication**: LLM-based reasoning can interpret field names directly without a data dictionary. Good for agent tool comprehension.
- **Recommendation**: No action needed — naming conventions are already agent-friendly.
- **Evidence**: index.php database schema definitions (all field names are self-descriptive)

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No data catalog, no metadata layer. Schema is defined only in PHP code (`CREATE TABLE` statements). No AWS Glue Data Catalog, no schema documentation files, no data dictionary.
- **Implication**: Building agent tools requires reading source code to understand data structures. No automated metadata discovery.
- **Recommendation**: Generate a data dictionary document or integrate with AWS Glue Data Catalog when the database is migrated to a more formal schema management approach.
- **Evidence**: index.php lines 32-130 (schema defined only in inline CREATE TABLE statements)

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No custom business metrics published. No `cloudwatch.put_metric_data` calls, no business KPI tracking, no order fulfillment rate metrics, no inventory turnover metrics.
- **Implication**: Cannot measure whether agent-driven restocking decisions produce good business outcomes. Need manual reporting.
- **Recommendation**: Add CloudWatch custom metrics for: orders_fulfilled_per_hour, inventory_stockout_events, average_fulfillment_time. These become the primary signal for agent effectiveness.
- **Evidence**: index.php (no CloudWatch SDK usage), infrastructure/monolith-apprunner.yaml (no custom metric configuration)

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: PASS
- **Finding**: The application exposes 26+ REST endpoints with JSON responses, accessible via HTTP on port 80. Endpoints cover inventory, orders, fulfillment workflow, returns, and user management. All API routes are defined in index.php with consistent JSON response formatting.
- **Gap**: N/A — API surface exists
- **Recommendation**: N/A — passes
- **Evidence**: index.php (routes defined from line 232 onwards, JSON Content-Type header set for all /api/* routes)

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: No machine-readable API specification. Searched: openapi.*, swagger.*, *.graphql, *.gql, *.smithy, *.proto — none found. No composer.json with swagger-php dependency.
- **Gap**: No machine-readable spec for agent tool auto-generation.
- **Recommendation**: Generate OpenAPI 3.0 specification from code analysis.
- **Evidence**: Repository root (no spec files)

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: Error format is `{"error": "message"}` with HTTP status codes. No error codes, no retryable field, no field-level validation detail.
- **Gap**: Agents cannot distinguish retriable from terminal errors programmatically.
- **Recommendation**: Add structured error codes and retryable indicators.
- **Evidence**: index.php (multiple instances of simple error JSON responses)

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No idempotency keys. `uniqid()` used for ID generation.
- **Gap**: Duplicate creation risk on retry.
- **Recommendation**: Implement when write scope is planned.
- **Evidence**: index.php line 305

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: All responses are structured JSON.
- **Gap**: None — format is ideal.
- **Recommendation**: No action needed.
- **Evidence**: index.php line 233

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has operations >30s OR long-running workflows. All operations are synchronous database queries completing in milliseconds.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: No event emission. State changes stored only in database.
- **Gap**: No proactive notification mechanism for agents.
- **Recommendation**: Add EventBridge events for inventory threshold crossings.
- **Evidence**: index.php (no event publishing code)

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit headers or documentation.
- **Gap**: Agents cannot self-throttle.
- **Recommendation**: Add rate limit headers when rate limiting is implemented.
- **Evidence**: index.php (no X-RateLimit headers)

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: Session-based authentication only. No machine identity support.
- **Gap**: Agents cannot authenticate without browser-like session management.
- **Recommendation**: Implement API key or OAuth2 client credentials authentication.
- **Evidence**: index.php lines 236-240

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: PASS
- **Finding**: The authorization model supports two distinct roles (admin/customer) with different endpoint access. IAM roles in CloudFormation are scoped (AppRunnerInstanceRole: CloudWatch only; AppRunnerAccessRole: ECR pull only). The system can differentiate access levels.
- **Gap**: N/A — scoped permissions exist.
- **Recommendation**: N/A — passes. Consider adding an "agent" role with further-scoped permissions when machine identity is implemented.
- **Evidence**: index.php (admin role checks on admin endpoints), infrastructure/monolith-apprunner.yaml (scoped IAM policies)

#### AUTH-Q3: Action-Level Authorization
- **Severity**: PASS
- **Finding**: Action-level authorization exists. Customers can create orders but cannot approve returns. Admin endpoints enforce role checks before allowing write/delete operations (create user, update user, delete user, approve return). Customer role can read their own orders but not access admin functions.
- **Gap**: N/A — action-level auth exists.
- **Recommendation**: N/A — passes. Extend with more granular permissions for agent roles.
- **Evidence**: index.php (role checks: `$_SESSION['user']['role'] !== 'admin'` gates on destructive operations)

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: RISK-SAFETY
- **Finding**: No identity propagation mechanism.
- **Gap**: Cannot distinguish agent-as-self vs agent-on-behalf-of-user.
- **Recommendation**: Implement JWT-based auth with token exchange.
- **Evidence**: index.php (session-only auth, no JWT)

#### AUTH-Q5: Credential Management
- **Severity**: RISK-SAFETY
- **Finding**: Credentials via environment variables with hardcoded fallbacks. No secrets manager.
- **Gap**: No credential rotation without redeployment.
- **Recommendation**: Migrate to Secrets Manager. Enable RDS IAM auth in the application.
- **Evidence**: index.php line 18, docker-compose.yml, infrastructure/monolith-apprunner.yaml

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No immutable audit logging. order_status_history is mutable.
- **Gap**: No tamper-evident audit trail.
- **Recommendation**: Add CloudTrail and immutable application-level logging.
- **Evidence**: infrastructure/monolith-apprunner.yaml (no CloudTrail)

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: No mechanism for individual identity suspension.
- **Gap**: Cannot isolate misbehaving agents.
- **Recommendation**: Implement per-agent API key revocation.
- **Evidence**: index.php (session-only auth)

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: DB transactions exist for individual operations. No workflow-level compensation.
- **Gap**: Multi-step fulfillment workflow lacks saga/compensation pattern.
- **Recommendation**: Implement saga pattern for fulfillment workflow.
- **Evidence**: index.php lines 302-350 (transaction), lines 1045-1200 (independent steps)

#### STATE-Q2: Queryable Current State
- **Severity**: PASS
- **Finding**: Current state is queryable via GET endpoints: products, orders, order history, validation data, warehouse options, picking details.
- **Gap**: N/A — state is queryable.
- **Recommendation**: N/A — passes.
- **Evidence**: index.php (GET endpoints expose full entity state)

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No optimistic locking. Atomic SQL decrements provide basic safety.
- **Gap**: No broad concurrency control pattern.
- **Recommendation**: Add version fields when write scope is planned.
- **Evidence**: index.php line 338

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has external dependencies (calls other services or external APIs). This service only communicates with its own MySQL database.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No rate limiting at application level. WAF provides IP whitelist only.
- **Gap**: Runaway agent loops not throttled.
- **Recommendation**: Add WAF rate-based rules and application-level rate limiting.
- **Evidence**: infrastructure/monolith-apprunner.yaml (WAF with IP whitelist, no rate rules)

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No transaction limits.
- **Gap**: No business-domain caps on agent operations.
- **Recommendation**: Add per-agent transaction limits when write scope is planned.
- **Evidence**: index.php (no limit checks)

#### STATE-Q7: Graceful Degradation Signaling
- **Severity**: RISK-QUALITY
- **Finding**: No degraded mode signaling. No health headers, no freshness indicators.
- **Gap**: Agent cannot detect degraded responses.
- **Recommendation**: Add health endpoint with granular states and response freshness headers.
- **Evidence**: index.php (no degradation headers)

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Returns use `pending_review` status. Orders start as `pending`.
- **Gap**: Pattern exists for returns only.
- **Recommendation**: No action for read-only scope.
- **Evidence**: index.php line 1320

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Return approval requires explicit admin action. Not configurable per operation.
- **Gap**: Hard-coded approval for one operation only.
- **Recommendation**: No action for read-only scope.
- **Evidence**: index.php lines 1356-1420

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: PASS
- **Finding**: docker-compose.yml provides a complete local development environment with production-equivalent data shape (same MySQL schema, seed data, health checks). Supports local testing of all API endpoints without risk to production.
- **Gap**: N/A — sandbox exists.
- **Recommendation**: N/A — passes. Consider adding synthetic data generation for more realistic testing volumes.
- **Evidence**: docker-compose.yml (full local environment), index.php seed_data() function

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — B1 evaluated as RISK-SAFETY
- **Finding**: System stores customer PII. B1: Order endpoints return customer email/name/address without scoping. B2: Role-based access differentiation exists. B3: No formal classification metadata.
- **Gap**: Agent-facing APIs expose customer PII unnecessary for restocking decisions.
- **Recommendation**: Create agent-specific endpoints that exclude customer PII.
- **Evidence**: index.php line 1280 (full customer details in order responses)

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No data residency policy. No cross-region transfer controls.
- **Gap**: No controls preventing customer data transmission to LLM in another region.
- **Recommendation**: Document residency requirements. Use region-local Bedrock endpoints.
- **Evidence**: infrastructure/monolith-apprunner.yaml (no residency configuration)

#### DATA-Q3: Selective Query Support
- **Severity**: RISK-QUALITY
- **Finding**: No pagination or filtering. All queries return full result sets.
- **Gap**: Unbounded result sets will exhaust LLM context.
- **Recommendation**: Add pagination parameters to list endpoints.
- **Evidence**: index.php line 244 (SELECT * without LIMIT)

#### DATA-Q4: Input Validation and Schema Enforcement
- **Severity**: RISK-QUALITY
- **Finding**: Minimal validation. Prepared statements prevent injection but no systematic schema enforcement.
- **Gap**: Malformed agent payloads not rejected with field-level detail.
- **Recommendation**: Add validation layer with structured error responses.
- **Evidence**: index.php lines 1430-1445

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK-QUALITY
- **Finding**: created_at/updated_at fields exist. No API-level freshness signaling.
- **Gap**: No Cache-Control or freshness headers.
- **Recommendation**: Add Last-Modified headers. Document UTC storage.
- **Evidence**: index.php schema definitions

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: No PII redaction in error logs. Customer data could appear in exceptions.
- **Gap**: No log scrubbing or PII masking.
- **Recommendation**: Add structured logging with PII exclusion. Add CloudWatch data protection.
- **Evidence**: index.php lines 9-11

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics or monitoring.
- **Gap**: Agent cannot assess data reliability.
- **Recommendation**: Add basic quality checks for inventory data.
- **Evidence**: index.php (no quality logic)

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: No versioning, no schema files, no breaking change detection.
- **Gap**: Silent breaking changes to agent tool bindings.
- **Recommendation**: Add API version prefix and OpenAPI spec with CI validation.
- **Evidence**: index.php (unversioned routes), repository (no schema files)

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: All field names are human-readable and semantically meaningful.
- **Gap**: None — names are clear.
- **Recommendation**: No action needed.
- **Evidence**: index.php schema definitions

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No data catalog or metadata layer.
- **Gap**: Schema understanding requires reading source code.
- **Recommendation**: Generate data dictionary documentation.
- **Evidence**: index.php (schema in CREATE TABLE only)

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: No tracing, no structured logging, no correlation IDs.
- **Gap**: Cannot debug agent-initiated request failures.
- **Recommendation**: Add X-Ray and structured JSON logging.
- **Evidence**: index.php lines 9-11

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: No CloudWatch Alarms configured.
- **Gap**: Degradation not detected automatically.
- **Recommendation**: Add alarms for error rates and latency.
- **Evidence**: infrastructure/monolith-apprunner.yaml (no alarms)

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics.
- **Gap**: Cannot measure agent effectiveness.
- **Recommendation**: Add metrics for fulfillment rate, stockout events.
- **Evidence**: index.php (no CloudWatch SDK)

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance
- **Severity**: RISK-QUALITY
- **Finding**: IaC exists (CloudFormation) but no review process or drift detection.
- **Gap**: Changes not subject to peer review or drift monitoring.
- **Recommendation**: Add CI/CD pipeline with required approvals and drift detection.
- **Evidence**: infrastructure/monolith-apprunner.yaml, deploy.sh

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: No CI/CD pipeline. Manual deployment only.
- **Gap**: API breaking changes not caught before production.
- **Recommendation**: Create CI/CD with contract testing.
- **Evidence**: Repository (no pipeline configs)

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: No automated rollback. ECR immutable tags allow manual previous-image deployment.
- **Gap**: No automatic rollback on failure.
- **Recommendation**: Configure auto-rollback on health check failure.
- **Evidence**: infrastructure/monolith-apprunner.yaml (no rollback config)

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: Zero test files. No PHPUnit, no API tests of any kind.
- **Gap**: No verification of API behavior.
- **Recommendation**: Add PHPUnit integration tests for agent-facing endpoints.
- **Evidence**: Repository (no test files)

#### ENG-Q5: Encryption at Rest
- **Severity**: PASS
- **Finding**: RDS has `StorageEncrypted: true`. ECR uses KMS encryption (`EncryptionType: KMS` with customer-managed key). VPC Flow Logs encrypted with KMS. All persistent data stores are encrypted at rest.
- **Gap**: N/A — encryption at rest is properly configured.
- **Recommendation**: N/A — passes.
- **Evidence**: infrastructure/monolith-apprunner.yaml (StorageEncrypted: true on DBInstance, EncryptionConfiguration on ECRRepository, KmsKeyId on VPCFlowLogGroup)

---

## Evidence Index

### Infrastructure as Code
| File | Questions Referenced |
|------|---------------------|
| infrastructure/monolith-apprunner.yaml | AUTH-Q1, AUTH-Q2, AUTH-Q5, AUTH-Q6, AUTH-Q7, STATE-Q5, DATA-Q2, DATA-Q6, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q3, ENG-Q5 |

### Source Code
| File | Questions Referenced |
|------|---------------------|
| index.php | API-Q1, API-Q2, API-Q3, API-Q4, API-Q5, API-Q7, API-Q8, AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q2, STATE-Q3, STATE-Q5, STATE-Q6, STATE-Q7, HITL-Q1, HITL-Q2, DATA-Q1, DATA-Q3, DATA-Q4, DATA-Q5, DATA-Q6, DATA-Q7, DISC-Q1, DISC-Q2, DISC-Q3, OBS-Q1, OBS-Q3, ENG-Q4 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| Dockerfile | HITL-Q3 |
| docker-compose.yml | AUTH-Q5, HITL-Q3 |

### Scripts
| File | Questions Referenced |
|------|---------------------|
| deploy.sh | ENG-Q1, ENG-Q2 |
