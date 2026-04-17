# Agentic Readiness Assessment Report

**Target**: ./monolith
**Date**: 2025-07-17
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P0
**Tags**: monolith, php, containers
**Context**: PHP monolith with Docker and CloudFormation on App Runner — containerize and expose inventory APIs the agent needs for restocking decisions.

**Archetype Justification**: The application connects to MySQL with CRUD operations across 9 tables (orders, order_items, inventory, payments, returns, interactions, order_status_history, warehouses, users), manages entity lifecycle (order status workflow from pending → delivered), and handles user-specific data — all hallmarks of a stateful-crud service.

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 2 | **RISK-SAFETY**: 8 | **RISK-QUALITY**: 14 | **INFOs**: 17

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days. The two BLOCKERs (AUTH-Q1: no machine identity authentication, DATA-Q1: unclassified PII) must be resolved before any agent — even a read-only pilot — can safely consume this system's APIs.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 2 |
| RISK-SAFETY | 8 |
| RISK-QUALITY | 14 |
| INFO | 17 |
| N/A | 0 |
| Not Evaluated (extended) | 2 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 17
**Extended Questions Not Triggered**: 2
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: stateful-crud (auto-detected)

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: The application uses PHP session-based authentication exclusively (`session_start()`, `$_SESSION['user']`). Login is via `POST /login` with username/password verified using `password_verify()`. API endpoints check `isset($_SESSION['user'])` for authentication. There is no support for OAuth2 client credentials, API key authentication with principal attribution, mTLS, or any other machine identity mechanism.
- **Gap**: No machine identity authentication exists. An agent cannot authenticate without a human session cookie. There is no way to attribute API calls to a specific agent identity in audit logs.
- **Remediation**:
  - **Immediate**: Implement API key authentication as a parallel auth path alongside session auth. Each API key should map to a named principal (e.g., `agent-restocking-v1`) and be logged with every request. This can be done by adding a middleware check for `Authorization: Bearer <api-key>` header before the session check in `index.php`.
  - **Target State**: OAuth2 client credentials flow with per-agent client IDs, scoped to specific API endpoints. Each agent call is attributable by client_id in structured logs.
  - **Estimated Effort**: Medium (2–4 weeks for API key path; 6–8 weeks for full OAuth2)
  - **Dependencies**: AUTH-Q6 (audit logging) — machine identity is a prerequisite for meaningful audit trails.
- **Evidence**: `index.php` (lines containing `session_start()`, `$_SESSION['user']`, `isset($_SESSION['user'])`)

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: The MySQL database schema in `init_db()` contains PII across multiple tables with no classification, tagging, or field-level access controls:
  - `orders` table: `customer_name` (VARCHAR 255), `customer_email` (VARCHAR 255), `shipping_address` (TEXT)
  - `users` table: `email` (VARCHAR 255), `password` (VARCHAR 255, bcrypt hashed)
  - `interactions` table: `customer_id`, `notes` (TEXT — may contain PII)
  - `order_status_history` table: `changed_by` (VARCHAR 100)
  The API endpoint `GET /api/products` requires authentication but returns inventory data. `GET /api/orders/me` returns full order records including `customer_name`, `customer_email`, and `shipping_address` with no field-level filtering. Admin endpoints return all customer data without restriction. No Amazon Macie integration. No field-level encryption. No data classification tags on RDS or S3.
- **Gap**: Sensitive data (PII) is stored unclassified in MySQL. An agent with read access to the orders API would receive customer PII (names, emails, addresses) with no controls preventing retrieval. No data classification policy exists.
- **Remediation**:
  - **Immediate**: Create a data classification inventory documenting which fields contain PII/sensitive data across all 9 tables. Implement API response filtering to exclude PII fields from agent-facing endpoints (e.g., return `customer_id` but not `customer_name` or `customer_email` in inventory/restocking contexts).
  - **Target State**: Field-level classification tags in a data catalog, column-level access controls or view-based access for agent identities, and Amazon Macie scanning for PII detection.
  - **Estimated Effort**: Medium (2–3 weeks for classification inventory and API response filtering; 4–6 weeks for Macie + column-level controls)
  - **Dependencies**: AUTH-Q1 (machine identity) — field-level access controls require agent identity to enforce scoped data access.
- **Evidence**: `index.php` (`init_db()` function with CREATE TABLE statements), `infrastructure/monolith-apprunner.yaml` (no data classification tags on RDS resource)

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The application implements a binary role model: `admin` and `customer`. Admin users (`$_SESSION['user']['role'] === 'admin'`) have unrestricted access to all admin endpoints including user management (CRUD), return approvals, and fulfillment workflow actions. Customer users can access product listings, their own orders, and submit returns. There is no intermediate permission level. IAM roles in CloudFormation (`AppRunnerInstanceRole`, `AppRunnerAccessRole`) are scoped to specific resources (CloudWatch logs, ECR pull) — but these are infrastructure-level, not application-level permissions.
- **Gap**: No mechanism to grant an agent read-only access to inventory data without also exposing customer orders, PII, and admin functions. An agent identity would need to be either `admin` (overly broad) or `customer` (insufficient for restocking decisions).
- **Compensating Controls**:
  - Create a dedicated `agent` role in the application with access scoped to `GET /api/products` and inventory-related endpoints only.
  - Use API Gateway with IAM authorization in front of App Runner to enforce endpoint-level access control before requests reach the application.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement a role-based access control (RBAC) system with at least 3 roles (customer, agent, admin) and endpoint-level permission mapping.
- **Evidence**: `index.php` (role checks: `$_SESSION['user']['role'] !== 'admin'`), `infrastructure/monolith-apprunner.yaml` (IAM roles)

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Authorization is role-based at the endpoint level but not action-level. Admin endpoints check `$_SESSION['user']['role'] !== 'admin'` and return 403 if not admin. However, once authenticated as admin, there is no distinction between read and write operations — an admin can both view orders AND delete users. There is no ABAC, no permission matrix, and no action-level middleware (e.g., `canRead`, `canWrite`, `canDelete`).
- **Gap**: Cannot grant an agent read access to fulfillment data while denying write access to user management or return approvals. All admin-level actions are bundled together.
- **Compensating Controls**:
  - Restrict agent identity to `customer` role and create dedicated read-only API endpoints for agent consumption.
  - Implement API Gateway resource policies that only allow specific HTTP methods (GET) for agent IAM roles.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement action-level authorization middleware that checks both role AND action type per endpoint.
- **Evidence**: `index.php` (admin checks on fulfillment, returns, and user management endpoints)

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The application tracks order status changes in the `order_status_history` table with `changed_by`, `status`, `notes`, and `created_at` fields. However, this table is in the same mutable MySQL database — it can be modified or deleted by any user with database access. There is no CloudTrail configuration for application-level actions in the CloudFormation template. VPC Flow Logs are configured with KMS encryption, but these capture network-level traffic, not application-level API calls. CloudWatch log groups exist for App Runner but no structured audit events are emitted by the application.
- **Gap**: No immutable, tamper-evident audit trail for API operations. The `order_status_history` table is mutable and could be altered. No way to prove which identity (human or agent) performed a specific action.
- **Compensating Controls**:
  - Enable AWS CloudTrail for the account with S3 bucket using object lock (immutable storage).
  - Add application-level logging that emits structured JSON audit events to CloudWatch Logs with agent identity, action, timestamp, and affected resources.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement structured audit logging in the application that writes to CloudWatch Logs (immutable retention). Include: principal identity, action, resource, timestamp, and request correlation ID.
- **Evidence**: `index.php` (`order_status_history` table, `update_order_status()` function), `infrastructure/monolith-apprunner.yaml` (VPCFlowLogGroup, AppRunnerInstanceRole with CloudWatch permissions — but no CloudTrail)

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The application uses PHP sessions for authentication. There is no mechanism to suspend or revoke an individual agent identity. User accounts in the `users` table have no `active`/`suspended` status field. The only way to prevent access is to delete the user record. There is no API key revocation endpoint, no Cognito user pool, and no IAM role deactivation procedure defined.
- **Gap**: Cannot isolate a misbehaving agent without taking down the broader platform or deleting the account entirely. No graceful suspension mechanism.
- **Compensating Controls**:
  - Add an `is_active` boolean field to the `users` table and check it during authentication.
  - If API keys are implemented (per AUTH-Q1 remediation), include a key revocation endpoint.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add a status field to user/agent identities and check it at authentication time. Implement a revocation API for agent API keys.
- **Evidence**: `index.php` (`users` table schema — no status/active field, login logic)

#### STATE-Q1: Compensation and Rollback ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The application uses MySQL transactions (`$db->beginTransaction()`, `$db->commit()`, `$db->rollBack()`) for atomic operations like order creation and return approval. However, the multi-step fulfillment workflow (validate → assign warehouse → pick → pack → quality check → ship) has NO compensation or rollback logic. Each step is an independent POST request that advances the order status. If the workflow fails at step 4 (packing), there is no mechanism to undo the warehouse assignment (step 2) or restore inventory (step 3). The `order_status_history` table records history but does not support reversal.
- **Gap**: No saga pattern, no compensating transactions, no explicit undo endpoints for the fulfillment workflow. A failure mid-workflow leaves the order in an inconsistent state.
- **Compensating Controls**:
  - For read-only agent scope, this risk is reduced since the agent would not be executing write workflows directly.
  - Implement manual rollback procedures documented for operations staff.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Design compensating actions for each fulfillment step (e.g., un-assign warehouse, restore inventory on pick cancellation) as a prerequisite for any future write-enabled agent scope.
- **Evidence**: `index.php` (fulfillment endpoints: `/api/orders/{id}/validate`, `/api/orders/{id}/assign-warehouse`, `/api/orders/{id}/pick`, `/api/orders/{id}/pack`, `/api/orders/{id}/quality-check`, `/api/orders/{id}/ship`)

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The CloudFormation template defines a WAF Web ACL (`WebACL`) with IP whitelisting (allow specific IP, block all others) and AWS Managed Rules for known bad inputs (Log4j protection). However, there are NO rate limiting rules in the WAF configuration — no `RateBasedStatement` rules. There is no application-level rate limiting middleware in the PHP code — no `express-rate-limit` equivalent, no request counting, no throttling headers. The App Runner autoscaling is configured with `MaxConcurrency: 100` per instance, which provides some natural back-pressure, but this is not a deliberate rate limiting control.
- **Gap**: No rate limits enforced at any layer. A runaway agent loop (even read-only — repeatedly querying inventory) could overwhelm the application at machine speed. No `X-RateLimit-Remaining` or `Retry-After` headers.
- **Compensating Controls**:
  - Add a WAF `RateBasedStatement` rule limiting requests per IP to a reasonable threshold (e.g., 1000 requests per 5-minute window).
  - App Runner's MaxConcurrency provides partial protection (100 concurrent requests per instance).
- **Remediation Timeline**: 7–14 days (WAF rate rule); 30 days (application-level rate limiting)
- **Recommendation**: Add a WAF rate-based rule immediately. Follow up with application-level rate limiting per agent identity.
- **Evidence**: `infrastructure/monolith-apprunner.yaml` (WebACL resource — no rate rules, AutoScalingConfiguration with MaxConcurrency: 100)

#### DATA-Q2: Data Residency and Sovereignty ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The CloudFormation template deploys RDS to the stack's AWS region (parameterized, not hardcoded). The database contains customer PII (names, emails, shipping addresses). There is no documentation of data residency requirements, no GDPR/LGPD/HIPAA compliance references anywhere in the repository, no cross-region replication configuration, and no data sovereignty policy. If an agent sends customer data to an LLM endpoint in a different region or jurisdiction, this could create compliance exposure — but the requirements are unknown because no data residency policy exists.
- **Gap**: No documented data residency requirements or controls. Cannot determine whether sending data to an LLM in a different region would violate compliance obligations.
- **Compensating Controls**:
  - Document data residency requirements for the customer data stored in this system.
  - If the agent is read-only and only accesses inventory/product data (not customer PII), residency risk is mitigated by data classification (DATA-Q1 remediation).
- **Remediation Timeline**: 14–30 days (documentation and policy); ongoing (enforcement)
- **Recommendation**: Conduct a data residency assessment with the legal/compliance team. Document which data fields have residency constraints. Ensure agent-accessible endpoints do not return residency-restricted data.
- **Evidence**: `infrastructure/monolith-apprunner.yaml` (RDS deployment, no region restrictions documented), `index.php` (PII in orders table)

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The application has multiple paths where PII can leak into logs and error messages:
  1. `die("Database connection failed: " . $e->getMessage())` — PDO exception messages may include connection strings with credentials.
  2. Error responses echo exception messages directly: `json_encode(['error' => $e->getMessage()])` — exception messages may contain SQL queries with customer data.
  3. The `order_status_history` table stores `changed_by` and `notes` fields which may contain PII.
  4. No log scrubbing middleware, no PII masking libraries, no CloudWatch log filters for PII.
  5. PHP error logging (`ini_set('log_errors', '1')`) writes unfiltered errors to Apache error log.
  6. The validation data endpoint returns customer PII (name, email, account age, total orders) in API responses that would appear in any request/response logging.
- **Gap**: PII is not redacted from error messages, logs, or observability data. Agent-initiated requests that trigger errors could expose customer data in log streams.
- **Compensating Controls**:
  - Implement a generic error handler that catches all exceptions and returns sanitized error messages (error code + generic message, not raw exception text).
  - Add PII masking to CloudWatch log group subscriptions.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Replace all `$e->getMessage()` in error responses with generic error codes. Implement a centralized error handler. Add log scrubbing for PII patterns (email, phone, address).
- **Evidence**: `index.php` (`die()` with `$e->getMessage()`, `json_encode(['error' => $e->getMessage()])` in multiple catch blocks, validation-data endpoint returning customer PII)

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, Swagger, AsyncAPI, GraphQL schema, or any other machine-readable API specification file exists in the repository. The API surface is defined only in PHP code within `index.php` as regex-matched route patterns (e.g., `preg_match('#^/api/orders/([^/]+)/validate$#', ...)`). There are approximately 25+ API endpoints spanning products, orders, fulfillment workflow, warehouse assignment, carrier shipping, quality checks, returns, and user management.
- **Gap**: No machine-readable spec means agent tool definitions must be manually authored by reading PHP source code. Tool definitions will drift from actual behavior as the codebase evolves.
- **Compensating Controls**:
  - Generate an OpenAPI spec manually from the PHP route definitions as a one-time effort.
  - Use API testing tools (Postman collection) as an interim machine-readable interface document.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Generate an OpenAPI 3.0 specification from the existing PHP routes. Consider adopting a PHP framework with built-in OpenAPI generation (e.g., API Platform, Laravel with Scribe).
- **Evidence**: `index.php` (all route patterns), absence of any `openapi.yaml`, `swagger.json`, or `.graphql` files in the repository

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Error responses use `json_encode(['error' => $message])` consistently across endpoints. However, the error structure lacks: (1) machine-readable error codes (only human-readable strings), (2) a `retryable` boolean or error category, (3) consistent HTTP status codes (most errors return 500 via exception handling, some return 400/403/404). Error messages are raw exception text (e.g., `$e->getMessage()`) which varies unpredictably.
- **Gap**: An agent cannot distinguish retriable errors (database timeout, transient failure) from terminal errors (invalid input, permission denied) without parsing human-readable strings. No error taxonomy exists.
- **Compensating Controls**:
  - Implement a standardized error response envelope: `{"error_code": "ORDER_NOT_FOUND", "message": "...", "retryable": false, "http_status": 404}`.
  - Map common exceptions to specific error codes in a centralized error handler.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Implement a centralized error handler with structured error codes and retryable classification. Apply consistently across all API endpoints.
- **Evidence**: `index.php` (error responses: `json_encode(['error' => 'Unauthorized'])`, `json_encode(['error' => $e->getMessage()])`, `json_encode(['error' => 'Order not found'])`)

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The repository includes `docker-compose.yml` which provisions a local MySQL database and the PHP application for development. This provides a functional local environment. However, there is no separate staging or sandbox environment configuration. The CloudFormation template (`monolith-apprunner.yaml`) defines a single production deployment with no environment parameterization (no `Environment` parameter, no conditional resources for staging). No seed data scripts beyond the hardcoded `seed_data()` function in `index.php`. No synthetic data generators.
- **Gap**: No staging environment with production-equivalent data shape. Agent testing would occur either locally (docker-compose, limited to seeded demo data) or directly in production. First-time agent bugs would be discovered in production.
- **Compensating Controls**:
  - Use docker-compose as a local sandbox for initial agent testing with the built-in seed data.
  - Deploy a second CloudFormation stack with a `staging` suffix for pre-production testing.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Create a staging environment by parameterizing the CloudFormation template with an `Environment` parameter. Deploy a staging stack with anonymized production data.
- **Evidence**: `docker-compose.yml` (local dev environment), `infrastructure/monolith-apprunner.yaml` (single environment), `index.php` (`seed_data()` function with demo data)

#### DATA-Q3: Selective Query Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The primary list endpoints return all records without pagination, filtering, or sorting:
  - `GET /api/products`: `SELECT * FROM inventory` — returns all products as a flat array.
  - `GET /api/orders/me`: `SELECT * FROM orders WHERE customer_id = ? ORDER BY created_at DESC` — returns all customer orders with no limit.
  - `GET /api/admin/orders/pending-fulfillment`: returns all pending orders.
  - `GET /api/admin/pending-returns`: returns all pending returns.
  No `limit`, `offset`, `cursor`, or filter parameters are accepted on any endpoint.
- **Gap**: An agent querying inventory or orders will receive unbounded result sets. As the database grows, this will exhaust LLM context windows and increase token cost.
- **Compensating Controls**:
  - Add `?limit=N&offset=M` query parameters to list endpoints.
  - For the restocking agent use case, the product catalog is likely small enough initially that unbounded results are acceptable.
- **Remediation Timeline**: 7–14 days
- **Recommendation**: Add pagination support (`limit`, `offset`, `cursor`) to all list endpoints. Default to `limit=50` if no parameter is provided.
- **Evidence**: `index.php` (SQL queries in `/api/products`, `/api/orders/me`, `/api/admin/orders/pending-fulfillment`, `/api/admin/pending-returns`)

#### DATA-Q5: Temporal Metadata and Freshness — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Orders have `created_at` and `updated_at` DATETIME fields. `order_status_history` has `created_at`. Returns have `created_at` and `processed_at`. The `inventory` table has NO timestamp fields — there is no way to know when stock quantities were last updated. Timestamps are generated using PHP `date('Y-m-d H:i:s')` with no explicit timezone normalization (relies on server default). No `Cache-Control` headers, no `X-Data-Age` headers, no freshness signaling in API responses.
- **Gap**: An agent making restocking decisions based on inventory data has no way to know if the stock_quantity is current, stale, or cached. The inventory table lacks `updated_at` entirely. No API response signals data freshness.
- **Compensating Controls**:
  - Add `updated_at` timestamp to the `inventory` table.
  - Include `Last-Modified` or `X-Data-Age` headers in inventory API responses.
- **Remediation Timeline**: 7–14 days
- **Recommendation**: Add `updated_at` column to the `inventory` table. Set all timestamps to UTC explicitly. Return `Last-Modified` headers on GET responses.
- **Evidence**: `index.php` (CREATE TABLE statements — `inventory` table has no timestamps, `orders` table has `created_at`/`updated_at`, `date('Y-m-d H:i:s')` usage)

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The database schema is defined inline in the `init_db()` function using `CREATE TABLE IF NOT EXISTS` statements. Schema modifications use `ALTER TABLE` with try/catch to silently ignore errors if columns already exist. There are no migration files, no schema version tracking, no changelog. API routes have no versioning — no `/v1/` prefix, no `Accept-Version` headers. No breaking change detection tools, no consumer-driven contract tests (Pact), no OpenAPI diff.
- **Gap**: Schema changes and API changes are not versioned or tracked. Agent tool bindings could break silently when the schema or API changes without notice. No way to detect breaking changes before deployment.
- **Compensating Controls**:
  - Introduce database migration tooling (e.g., Phinx for PHP) to track schema versions.
  - Add API version prefix (`/v1/api/`) to enable future non-breaking evolution.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement database migration tooling. Add API versioning. Set up OpenAPI diff in CI/CD (once CI/CD exists — see ENG-Q2).
- **Evidence**: `index.php` (`init_db()` function with inline CREATE TABLE and ALTER TABLE statements)

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No distributed tracing is configured — no AWS X-Ray SDK, no OpenTelemetry instrumentation, no `traceparent` header propagation in the PHP code. Logging is via PHP's built-in `error_log` mechanism (`ini_set('log_errors', '1')`). Logs are unstructured Apache error format, not JSON. No `request_id` or `correlation_id` is generated or propagated. CloudFormation defines CloudWatch log groups for App Runner and VPC Flow Logs, but these capture infrastructure logs, not structured application events.
- **Gap**: Cannot trace an agent-initiated request through the system. If an agent's API call fails, there is no trace ID to correlate the request across application logs, database queries, and infrastructure events. Debugging agent failures requires manual log correlation.
- **Compensating Controls**:
  - Add a request ID middleware that generates a UUID per request, includes it in the response header, and logs it with every PHP log statement.
  - CloudWatch log groups already exist — structured JSON logging would be queryable via CloudWatch Insights.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Implement request ID generation middleware. Switch to structured JSON logging. Evaluate OpenTelemetry PHP SDK for distributed tracing.
- **Evidence**: `index.php` (`ini_set('log_errors', '1')`, no trace/correlation ID logic), `infrastructure/monolith-apprunner.yaml` (CloudWatch log groups, no X-Ray configuration)

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No CloudWatch alarms are defined in the CloudFormation template. RDS has Enhanced Monitoring enabled (`MonitoringInterval: 60`) which provides OS-level metrics, but no alerting thresholds are configured on those metrics. WAF has CloudWatch metrics enabled (`CloudWatchMetricsEnabled: true`) for visibility but no alarms are set on those metrics. No PagerDuty, OpsGenie, or SNS topic integration for alerting.
- **Gap**: No automated alerting when the APIs that agents consume degrade. An agent hitting elevated error rates or latency would continue retrying without any operational awareness.
- **Compensating Controls**:
  - Add CloudWatch alarms for App Runner 5xx error rate, latency P99, and RDS CPU utilization.
  - Configure SNS topic for alert notifications.
- **Remediation Timeline**: 7–14 days
- **Recommendation**: Define CloudWatch alarms in the CloudFormation template for: App Runner error rate > 5%, latency P99 > 2s, RDS CPU > 80%, and WAF blocked request rate anomalies.
- **Evidence**: `infrastructure/monolith-apprunner.yaml` (no AWS::CloudWatch::Alarm resources, MonitoringInterval: 60 on RDS, CloudWatchMetricsEnabled on WAF)

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Infrastructure is defined as CloudFormation IaC in `monolith-apprunner.yaml` — covering VPC, RDS, App Runner, WAF, IAM roles, ECR, KMS keys, and security groups. This is comprehensive IaC coverage. However: (1) No evidence of PR/peer review requirements on IaC changes — no CODEOWNERS file, no branch protection configuration, no PR template. (2) No drift detection — no AWS Config rules defined, no `cloudformation drift-detection` automation. (3) The deploy script (`deploy.sh`) runs `docker-compose build` and `docker-compose up` — manual execution with no review gate.
- **Gap**: IaC exists (good), but changes to the integration surface can be made without peer review and deployed without drift detection. A misconfiguration in IAM roles or security groups would not be caught.
- **Compensating Controls**:
  - Enable AWS Config drift detection for CloudFormation stacks.
  - Add a CODEOWNERS file requiring approval for changes to `infrastructure/` directory.
- **Remediation Timeline**: 7–14 days
- **Recommendation**: Implement branch protection requiring PR reviews for infrastructure changes. Enable AWS Config with CloudFormation drift detection rules.
- **Evidence**: `infrastructure/monolith-apprunner.yaml` (comprehensive IaC), `deploy.sh` (manual deployment script), absence of CODEOWNERS, `.github/` directory, or Config rules

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No CI/CD pipeline exists. The deployment process is a manual shell script (`deploy.sh`) that runs `docker-compose build` and `docker-compose up -d`. The CloudFormation template outputs manual deployment instructions (build → push to ECR → update stack). No GitHub Actions, GitLab CI, Jenkins, CodeBuild, or CodePipeline configuration files exist in the repository. No API contract tests, no OpenAPI validation, no schema comparison tools.
- **Gap**: API-breaking changes cannot be detected before production. There is no automated pipeline to catch contract violations. Manual deployment is error-prone and unrepeatable.
- **Compensating Controls**:
  - Create a minimal CI pipeline (GitHub Actions or CodeBuild) that runs basic health checks against the application.
  - Add OpenAPI spec generation and diff checking once the spec exists (API-Q2 remediation).
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement a CI/CD pipeline with: (1) Docker image build and push to ECR, (2) CloudFormation stack update, (3) API contract validation against OpenAPI spec, (4) basic smoke tests.
- **Evidence**: `deploy.sh` (manual deployment), absence of `.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`, `buildspec.yml`

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No explicit rollback capability is configured. App Runner supports auto-rollback on failed deployments natively, but no deployment configuration triggers are defined in the template. The RDS instance has `DeletionPolicy: Snapshot` and `BackupRetentionPeriod: 7` — providing database backup capability but not fast application rollback. No blue/green deployment, no CodeDeploy with rollback triggers, no feature flags, no canary deployment configuration. ECR has `ImageTagMutability: IMMUTABLE` which preserves previous image versions for manual rollback.
- **Gap**: If a deployment breaks agent-facing APIs, rollback is manual. No automated rollback on error rate increase. Estimated manual rollback time: 30+ minutes (re-push previous ECR image, update CloudFormation stack).
- **Compensating Controls**:
  - App Runner's native rollback capability can be triggered manually via console.
  - ECR immutable tags preserve previous images for rollback.
  - RDS snapshots provide database recovery.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Configure App Runner deployment with automatic rollback on health check failure. Implement a rollback script that reverts to the previous ECR image tag. Consider CodeDeploy with automatic rollback triggers.
- **Evidence**: `infrastructure/monolith-apprunner.yaml` (App Runner service, RDS DeletionPolicy: Snapshot, ECR ImageTagMutability: IMMUTABLE), `deploy.sh` (no rollback commands)

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No test files exist anywhere in the repository. Zero automated tests — no unit tests, no integration tests, no API tests, no contract tests. No test directories, no test configuration files (no phpunit.xml, no behat.yml, no Postman collections, no pytest, no jest). The application has approximately 25+ API endpoints with no test coverage.
- **Gap**: API behavior changes will not be caught by automated tests. Agent tool bindings rely on undocumented, untested API behavior that could change without detection.
- **Compensating Controls**:
  - Create a Postman/Newman collection exercising the core agent-facing endpoints (GET /api/products) as a first step.
  - Run the collection against docker-compose in a manual pre-deployment check.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement API tests for agent-facing endpoints using PHPUnit or a Postman/Newman collection. Prioritize inventory endpoints (GET /api/products) for the restocking agent use case.
- **Evidence**: Absence of any test files, test directories, or test configuration files in the repository

#### STATE-Q2: Queryable Current State — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: GET endpoints exist for order state, inventory, warehouse options, picking details, packing options, quality checklists, and shipping options. The application supports read-before-write patterns through decision-making endpoints. Current state is queryable for all major entities.
- **Gap**: While state is queryable, the `inventory` table lacks an `updated_at` timestamp, so an agent cannot determine when the stock data was last modified. Additionally, there is no way to query the current stock state with a "last changed" indicator.
- **Compensating Controls**:
  - Add `updated_at` to inventory table to signal freshness.
  - The existing GET endpoints are sufficient for read-only agent consumption.
- **Remediation Timeline**: 7–14 days
- **Recommendation**: Add `updated_at` timestamp to the inventory table. Otherwise, the state queryability posture is adequate for the restocking agent use case.
- **Evidence**: `index.php` (GET endpoints for validation-data, warehouse options, picking-details, packing-options, quality-checklist, shipping-options, `/api/products`)

#### STATE-Q7: Infrastructure Capacity for Agent Traffic — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: App Runner autoscaling: MinSize 1, MaxSize 3, MaxConcurrency 100. RDS is db.t3.micro (2 vCPU, 1 GB RAM) with Multi-AZ. No load test results. No capacity planning documentation. Infrastructure is sized for human-paced interaction, not agent traffic patterns.
- **Gap**: No load testing for agent traffic. db.t3.micro may be undersized for rapid sequential queries. MaxSize 3 may not absorb burst traffic.
- **Compensating Controls**:
  - App Runner autoscaling provides basic elasticity.
  - RDS Multi-AZ provides availability but not additional read capacity.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Conduct load testing simulating agent query patterns. Consider RDS read replicas or instance upsizing for agent workloads.
- **Evidence**: `infrastructure/monolith-apprunner.yaml` (AutoScalingConfiguration, DBInstance db.t3.micro Multi-AZ)

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO (see note)
- **Finding**: The application exposes a REST API under the `/api/` prefix with approximately 25+ endpoints. Routes are defined in PHP code using `preg_match()` patterns in `index.php`, with Apache `mod_rewrite` directing all requests to `index.php` via `.htaccess`. The API surface covers: products (GET), orders (POST, GET), fulfillment workflow (POST for each step), warehouse assignment (GET options, POST assign), carrier shipping (GET options), quality checks (GET checklist, POST result), returns (POST, GET pending), and user management (CRUD). Responses are JSON (`header('Content-Type: application/json')`). The API is functional and well-structured for a monolith — endpoints are logically organized and return consistent JSON.
- **Note**: API-Q1 is a BLOCKER question by default, but the application DOES expose a documented REST interface (via code). The API surface exists and is functional. The concern is that it is documented only in code, not in a formal specification — which is covered by API-Q2 (RISK-QUALITY). API-Q1 evaluates to a passing finding (no gap on the BLOCKER criteria: the app does NOT require direct database access, file-based exchange, or UI automation for integration).
- **Implication**: Agents can consume this API via standard HTTP tooling. The existing endpoint structure is suitable for agent tool definitions once machine-readable specs are created (API-Q2).
- **Recommendation**: No immediate action required. The API exists and is structured for programmatic consumption.
- **Evidence**: `index.php` (all `/api/` route handlers), `.htaccess` (URL rewriting to index.php)

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Write endpoints (`POST /api/orders`, `POST /api/orders/{id}/validate`, `POST /api/orders/{id}/assign-warehouse`, `POST /api/orders/{id}/pick`, `POST /api/orders/{id}/pack`, `POST /api/orders/{id}/quality-check`, `POST /api/orders/{id}/ship`, `POST /api/returns`, `POST /api/admin/approve-return`) do not support idempotency keys. Order IDs are generated with `uniqid()` on each request — duplicate POST requests would create duplicate orders. No `Idempotency-Key` header support, no unique constraint enforcement on business keys for write operations.
- **Implication**: If agent scope is ever expanded to write-enabled, idempotency must be implemented first. Without it, agent retries would create duplicate records.
- **Recommendation**: Plan for idempotency key support on write endpoints before expanding agent scope beyond read-only.
- **Evidence**: `index.php` (`uniqid('order-')`, `uniqid('return-')`, `uniqid('pay-')` — all non-idempotent ID generation)

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: All API responses are JSON, set via `header('Content-Type: application/json')`. Responses use `json_encode()` consistently. Response structures are nested JSON objects with clear property names (e.g., `{"products": [...]}`, `{"order": {...}, "warehouses": [...]}`, `{"success": true, "order_id": "..."}`. No XML, binary, or Protobuf formats.
- **Implication**: JSON is ideal for LLM consumption. Agent tool responses can be fed directly to LLMs without format conversion.
- **Recommendation**: No action required. JSON response format is well-suited for agent integration.
- **Evidence**: `index.php` (`header('Content-Type: application/json')`, `json_encode()` throughout)

### API-Q7: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: The application does not emit events or webhooks for state changes. Order status changes are recorded in the `order_status_history` table but no external notification is triggered. No SNS, EventBridge, SQS, Kafka, or webhook integration exists. State changes require polling the API (e.g., `GET /api/orders/{id}/history`).
- **Implication**: Agents cannot react proactively to order status changes — they must poll. For the restocking use case, polling inventory levels is sufficient. For future fulfillment automation, event-driven patterns would be more efficient.
- **Recommendation**: Consider adding SNS/EventBridge event emission for order status changes when expanding to event-driven agent patterns.
- **Evidence**: `index.php` (`update_order_status()` function — writes to DB only, no event emission)

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limit headers are returned in API responses — no `X-RateLimit-Remaining`, no `Retry-After`, no `X-RateLimit-Limit`. The WAF Web ACL exists but does not include rate limiting rules (see STATE-Q5). No API usage plan or rate limit documentation exists.
- **Implication**: Agents have no way to self-throttle based on server-side limits. They would discover rate limits only through failures.
- **Recommendation**: When rate limiting is implemented (STATE-Q5 remediation), include `X-RateLimit-Remaining` and `Retry-After` headers in API responses.
- **Evidence**: `index.php` (no rate limit headers in response code), `infrastructure/monolith-apprunner.yaml` (WAF with no rate rules)

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: INFO
- **Finding**: No identity propagation mechanism exists. The application uses PHP sessions — there is no JWT parsing, no OAuth2 on-behalf-of flows, no token exchange, no user context headers passed through service calls. The monolith does not call external services, so identity propagation is not currently needed. IAM roles are defined for infrastructure (App Runner → ECR, App Runner → CloudWatch) but not for application-level identity delegation.
- **Implication**: If the application is decomposed into microservices in the future, identity propagation will need to be designed. For the current monolith architecture with read-only agent scope, this is not a concern.
- **Recommendation**: Design identity propagation as part of any future microservices decomposition. For now, no action required.
- **Evidence**: `index.php` (session-only auth, no JWT/OAuth2 middleware), `infrastructure/monolith-apprunner.yaml` (IAM roles for infrastructure only)

### AUTH-Q5: Credential Management

- **Severity**: INFO
- **Finding**: Database credentials are passed as environment variables: `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASS` in both `docker-compose.yml` and CloudFormation (App Runner `RuntimeEnvironmentVariables`). In docker-compose, passwords use environment variable references with required validation (`${MYSQL_PASSWORD:?Set MYSQL_PASSWORD}`). In CloudFormation, `DBUsername` and `DBPassword` are parameters with `NoEcho: true`. However, there is no AWS Secrets Manager integration, no HashiCorp Vault, and no credential rotation mechanism. The `get_db()` function falls back to hardcoded defaults: `$user = getenv('DB_USER') ?: 'ecommerce_user'` and `$pass = getenv('DB_PASS') ?: 'ecommerce_pass'`.
- **Implication**: Credentials are not rotated and fallback defaults in code are a security concern. A prompt injection or agent bug could potentially extract environment variables.
- **Recommendation**: Migrate to AWS Secrets Manager for database credentials. Remove hardcoded fallback credentials from source code. Enable automatic secret rotation.
- **Evidence**: `index.php` (`get_db()` function with env var fallbacks), `docker-compose.yml` (environment variables), `infrastructure/monolith-apprunner.yaml` (RuntimeEnvironmentVariables with DB credentials)

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No optimistic locking, version fields, ETags, `If-Match` headers, or conditional writes exist. Inventory updates use direct `UPDATE inventory SET stock_quantity = stock_quantity - ? WHERE product_id = ?` without any concurrency check. Multiple simultaneous order submissions for the same product could result in overselling (stock_quantity going negative). No `SELECT FOR UPDATE`, no DynamoDB conditional writes (N/A — MySQL).
- **Implication**: Relevant only for write-enabled scope. Read-only agents querying inventory are not affected by write concurrency issues.
- **Recommendation**: Implement optimistic locking (version field + conditional UPDATE) on the inventory table before expanding agent scope to write-enabled.
- **Evidence**: `index.php` (inventory update SQL: `UPDATE inventory SET stock_quantity = stock_quantity - ?`)

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits per agent identity. No maximum records per operation, no spend limits per session, no delete limits per hour. The bulk operations available (return approvals, fulfillment actions) have no safeguards against mass execution.
- **Implication**: Relevant only for write-enabled scope. Read-only agents cannot trigger bulk modifications.
- **Recommendation**: Design configurable transaction limits per agent identity as part of write-enabled scope planning.
- **Evidence**: `index.php` (no transaction limit logic in any endpoint)

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The application implements pending/draft-like states: orders begin as `pending` status, returns begin as `pending_review` status requiring admin approval. The fulfillment workflow has explicit human-driven steps (validate → assign → pick → pack → QC → ship) where each transition is a deliberate action. These states function as human-in-the-loop gates for write operations.
- **Implication**: The existing pending/draft pattern is well-suited for future write-enabled agent scope — an agent could propose actions (set to pending) while humans confirm.
- **Recommendation**: No action required for read-only scope. Leverage existing pending states if agent scope expands to write-enabled.
- **Evidence**: `index.php` (order status workflow: `pending` → `confirmed` → `validated` → ..., return status: `pending_review`)

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The fulfillment workflow enforces sequential status transitions — each step requires an explicit POST request to advance (validate, assign warehouse, pick, pack, quality check, ship). Return approvals require admin action via `POST /api/admin/approve-return`. These are implicit approval gates but are not configurable per operation type — they are hardcoded in the workflow sequence.
- **Implication**: The existing sequential workflow provides natural approval gates for write operations. For write-enabled scope, making these configurable (e.g., auto-approve for low-risk orders, require human approval for high-value orders) would be valuable.
- **Recommendation**: No action required for read-only scope. Consider making approval gates configurable by operation risk level for future write-enabled scope.
- **Evidence**: `index.php` (fulfillment workflow endpoints, return approval endpoint)

### DATA-Q4: System of Record Designations

- **Severity**: INFO
- **Finding**: The single MySQL database is the de facto system of record for all business domains — orders, inventory, payments, returns, users, and warehouses. There is no conflict between multiple data sources because the monolith owns all data in one database. However, there is no explicit system-of-record designation documented.
- **Implication**: For the restocking agent use case, the inventory table in this database IS the system of record. When the monolith is decomposed, explicit system-of-record designations per domain will be needed.
- **Recommendation**: Document that this MySQL database is the system of record for inventory, orders, and customer data. Plan for explicit ownership when decomposing into microservices.
- **Evidence**: `index.php` (single `get_db()` connection to one MySQL database, all tables in `init_db()`)

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality metrics, profiling, monitoring, or freshness SLAs exist. No null rate monitoring, no duplicate detection logic, no data quality dashboards. The `seed_data()` function creates demo data with hardcoded values that may not represent production data quality. Inventory has basic constraints (NOT NULL on key fields) but no business rule validation beyond stock quantity checks.
- **Implication**: An agent making restocking decisions on data with unknown quality (missing products, incorrect prices, stale quantities) will propagate errors at machine speed.
- **Recommendation**: Implement basic data quality monitoring — track null rates, duplicate records, and data freshness for the inventory table.
- **Evidence**: `index.php` (seed_data function, inventory schema constraints)

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Field names across all database tables are human-readable and semantically meaningful: `customer_name`, `customer_email`, `shipping_address`, `stock_quantity`, `product_name`, `total_amount`, `tracking_number`, `warehouse_location`, `weight_lbs`, `dimensions`, `created_at`, `updated_at`. No legacy abbreviations (no `CUST_TYP_CD` patterns). API response field names match database field names.
- **Implication**: LLM-based agents can interpret field names directly without a data dictionary. This accelerates tool definition authoring.
- **Recommendation**: No action required. Maintain the current naming convention in future development.
- **Evidence**: `index.php` (CREATE TABLE statements, API response JSON structures)

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No data catalog or metadata layer exists — no AWS Glue Data Catalog, no Collibra, no DataHub, no metadata files, no data dictionary. The database schema is defined only in PHP code (`init_db()` function). Table relationships are defined via FOREIGN KEY constraints but not documented externally.
- **Implication**: Agent tool authors must read PHP source code to understand available data. A data catalog would accelerate tool definition and improve discoverability.
- **Recommendation**: Consider documenting the data model in a schema documentation file or implementing AWS Glue Data Catalog when the restocking agent integration begins.
- **Evidence**: `index.php` (`init_db()` function), absence of any data catalog configuration or metadata files

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No custom business metrics are published. No `cloudwatch.put_metric_data` calls, no custom dashboards, no business KPI tracking. WAF metrics are enabled (`CloudWatchMetricsEnabled: true`) but these are security metrics, not business outcomes. The application tracks order status transitions in the database but does not emit metrics for fulfillment throughput, order completion rates, inventory turnover, or restocking frequency.
- **Implication**: When agents consume the inventory APIs for restocking decisions, there will be no business metrics to evaluate whether agent decisions produce good outcomes (e.g., right restock quantities, fewer stockouts).
- **Recommendation**: Implement custom CloudWatch metrics for: inventory turnover rate, stockout frequency, order fulfillment time, and restocking accuracy.
- **Evidence**: `index.php` (no metrics emission), `infrastructure/monolith-apprunner.yaml` (WAF metrics only)

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO (passing — no BLOCKER gap)
- **Finding**: The application exposes a functional REST API under `/api/` with 25+ endpoints serving JSON responses. Routes are defined via PHP regex patterns in `index.php` with Apache mod_rewrite. The API covers products, orders, fulfillment workflow, warehouse assignment, carrier shipping, quality checks, returns, and user management. No direct database access, file-based exchange, or UI automation is required for integration.
- **Gap**: API is documented in code only, not in a formal specification (addressed by API-Q2).
- **Recommendation**: No immediate action. The API surface is suitable for agent tool consumption.
- **Evidence**: `index.php` (all `/api/` route handlers), `.htaccess`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, Swagger, AsyncAPI, GraphQL schema, Smithy, or any machine-readable specification exists. The API surface is defined only in PHP regex patterns in `index.php`.
- **Gap**: Agent tool definitions must be manually authored from source code. No automated tool generation is possible.
- **Recommendation**: Generate an OpenAPI 3.0 specification from existing PHP routes.
- **Evidence**: Absence of `openapi.yaml`, `swagger.json`, `.graphql`, or `.smithy` files in the repository

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: Error responses use `json_encode(['error' => $message])` pattern. No machine-readable error codes, no retryable classification, inconsistent HTTP status codes. Error messages are raw exception text via `$e->getMessage()`.
- **Gap**: Agents cannot distinguish retriable from terminal errors without parsing human-readable strings.
- **Recommendation**: Implement structured error envelope with error_code, message, and retryable boolean.
- **Evidence**: `index.php` (error response patterns across all endpoints)

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Write endpoints use `uniqid()` for ID generation with no idempotency key support. Duplicate POST requests create duplicate records.
- **Gap**: Non-idempotent write endpoints (informational for read-only scope).
- **Recommendation**: Plan idempotency key support before expanding to write-enabled scope.
- **Evidence**: `index.php` (`uniqid('order-')`, `uniqid('return-')`, `uniqid('pay-')`)

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: All API responses are JSON via `header('Content-Type: application/json')` and `json_encode()`. Well-structured nested objects with clear property names.
- **Gap**: None.
- **Recommendation**: No action required.
- **Evidence**: `index.php` (Content-Type headers, json_encode throughout)

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has operations >30s OR long-running workflows. No evidence of operations exceeding 30 seconds — all endpoints are synchronous database queries.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: No event emission, webhooks, SNS, EventBridge, or Kafka integration. State changes are recorded in `order_status_history` table only. Polling required.
- **Gap**: Agents cannot react proactively to state changes.
- **Recommendation**: Consider event emission for order status changes when expanding to event-driven agent patterns.
- **Evidence**: `index.php` (`update_order_status()` function — DB writes only)

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit headers (`X-RateLimit-Remaining`, `Retry-After`) in API responses. WAF exists but has no rate limiting rules.
- **Gap**: Agents cannot self-throttle based on server-side limits.
- **Recommendation**: Include rate limit headers when rate limiting is implemented (STATE-Q5).
- **Evidence**: `index.php` (no rate limit headers), `infrastructure/monolith-apprunner.yaml` (WAF without rate rules)

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: PHP session-based authentication only (`session_start()`, `$_SESSION['user']`). Login via `POST /login` with username/password. No OAuth2 client credentials, no API key authentication, no mTLS, no service account support.
- **Gap**: Agents cannot authenticate without a human session cookie. No machine identity attribution.
- **Recommendation**: Implement API key authentication with principal attribution as a parallel auth path.
- **Evidence**: `index.php` (`session_start()`, `isset($_SESSION['user'])` checks)

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: Binary role model: `admin` (unrestricted) and `customer` (limited). IAM roles in CloudFormation are scoped but application-level permissions are coarse-grained.
- **Gap**: No mechanism to grant an agent read-only inventory access without exposing admin functions or customer PII.
- **Recommendation**: Implement RBAC with at least 3 roles (customer, agent, admin) and endpoint-level mapping.
- **Evidence**: `index.php` (role checks), `infrastructure/monolith-apprunner.yaml` (IAM roles)

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization. Admin role has unrestricted access to all operations (read, write, delete). No ABAC, no permission matrix, no action-level middleware.
- **Gap**: Cannot restrict agent to read-only within admin-accessible resources.
- **Recommendation**: Implement action-level authorization middleware.
- **Evidence**: `index.php` (admin role checks — no action differentiation)

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: No JWT, OAuth2, or token exchange. Session cookies only. Monolith does not call external services — propagation not currently needed.
- **Gap**: No identity propagation mechanism (informational for monolith architecture).
- **Recommendation**: Design identity propagation for future microservices decomposition.
- **Evidence**: `index.php` (session-only auth), `infrastructure/monolith-apprunner.yaml` (infrastructure IAM only)

#### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: DB credentials via environment variables with `NoEcho: true` in CloudFormation. Hardcoded fallback defaults in `get_db()`. No Secrets Manager, no Vault, no rotation.
- **Gap**: Credentials not rotated; fallback defaults in source code.
- **Recommendation**: Migrate to AWS Secrets Manager. Remove hardcoded fallbacks.
- **Evidence**: `index.php` (`get_db()`), `docker-compose.yml`, `infrastructure/monolith-apprunner.yaml`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: `order_status_history` table tracks changes with `changed_by` field but is in mutable MySQL. No CloudTrail for application actions. VPC Flow Logs capture network traffic, not API calls.
- **Gap**: No immutable, tamper-evident audit trail for API operations.
- **Recommendation**: Implement structured audit logging to CloudWatch Logs with immutable retention.
- **Evidence**: `index.php` (`order_status_history`, `update_order_status()`), `infrastructure/monolith-apprunner.yaml` (VPCFlowLogGroup — no CloudTrail)

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: No mechanism to suspend/revoke individual identities. Users table has no `is_active`/`suspended` field. Only option is full account deletion.
- **Gap**: Cannot isolate a misbehaving agent without platform-wide impact.
- **Recommendation**: Add status field to user/agent identities. Implement API key revocation.
- **Evidence**: `index.php` (`users` table schema, login logic)

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: MySQL transactions exist for atomic operations (order creation, return approval). However, the multi-step fulfillment workflow (validate → assign → pick → pack → QC → ship) has no compensation or rollback logic. Each step is an independent POST with no undo capability.
- **Gap**: No saga pattern, no compensating transactions, no undo endpoints for the fulfillment workflow.
- **Recommendation**: Design compensating actions for each fulfillment step before expanding to write-enabled scope.
- **Evidence**: `index.php` (fulfillment endpoints, `$db->beginTransaction()` / `$db->rollBack()` in order creation only)

#### STATE-Q2: Queryable Current State
- **Severity**: RISK-QUALITY
- **Finding**: GET endpoints exist for order state (`/api/orders/{id}/history`), inventory (`/api/products`), warehouse options (`/api/warehouses/assignment-options`), picking details, packing options, quality checklists, and shipping options. The application supports read-before-write patterns through these decision-making endpoints. Current state is queryable for all major entities.
- **Gap**: While state is queryable, the `inventory` table lacks an `updated_at` timestamp, so an agent cannot determine when the stock data was last modified (see DATA-Q5).
- **Recommendation**: Add `updated_at` to the inventory table. State queryability is otherwise sufficient.
- **Evidence**: `index.php` (GET endpoints for validation-data, warehouse options, picking-details, packing-options, quality-checklist, shipping-options)

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No optimistic locking, no version fields, no ETags, no conditional writes. Inventory stock updated with direct `UPDATE SET stock_quantity = stock_quantity - ?` without concurrency protection.
- **Gap**: No concurrency controls on write operations (informational for read-only scope).
- **Recommendation**: Implement optimistic locking on inventory table before expanding to write-enabled scope.
- **Evidence**: `index.php` (inventory UPDATE statement without version check)

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has external dependencies (calls other services or external APIs). The monolith is self-contained — it only connects to its own MySQL database and does not call any external services or APIs.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: WAF has IP whitelisting and managed rules but NO rate limiting rules (`RateBasedStatement`). No application-level rate limiting middleware. App Runner MaxConcurrency: 100 provides partial back-pressure.
- **Gap**: No rate limits at any layer. Runaway agent loops could overwhelm the application.
- **Recommendation**: Add WAF rate-based rule immediately. Follow with application-level rate limiting.
- **Evidence**: `infrastructure/monolith-apprunner.yaml` (WebACL — no rate rules, AutoScalingConfiguration)

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits per agent identity. No maximum records per operation, no spend limits, no delete limits.
- **Gap**: No transaction limits (informational for read-only scope).
- **Recommendation**: Design transaction limits per agent identity for future write-enabled scope.
- **Evidence**: `index.php` (no transaction limit logic)

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: RISK-QUALITY
- **Finding**: App Runner autoscaling is configured: MinSize: 1, MaxSize: 3, MaxConcurrency: 100 per instance. RDS is db.t3.micro (2 vCPU, 1 GB RAM) with Multi-AZ for availability. No load test results or capacity planning documentation exists. The infrastructure is sized for a small application, not for high-frequency agent traffic patterns.
- **Gap**: No evidence of load testing. db.t3.micro may be insufficient for agent traffic patterns (rapid sequential queries). MaxSize: 3 instances may not absorb burst agent traffic.
- **Recommendation**: Conduct load testing simulating agent query patterns against the inventory API. Consider RDS instance sizing for agent workloads.
- **Evidence**: `infrastructure/monolith-apprunner.yaml` (AutoScalingConfiguration, DBInstance db.t3.micro)

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Orders begin as `pending`, returns as `pending_review`. Fulfillment workflow has explicit human-driven step transitions. Pending/draft states exist and function as approval gates.
- **Gap**: None for read-only scope.
- **Recommendation**: Leverage existing pending states for future write-enabled scope.
- **Evidence**: `index.php` (order status workflow, return `pending_review` status)

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Sequential fulfillment workflow enforces explicit step transitions. Return approvals require admin action. Gates exist but are not configurable per operation type — hardcoded in workflow sequence.
- **Gap**: Approval gates are implicit and non-configurable (informational for read-only scope).
- **Recommendation**: Consider making approval gates configurable by risk level for future write-enabled scope.
- **Evidence**: `index.php` (fulfillment workflow, return approval endpoint)

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: `docker-compose.yml` provides local dev environment with MySQL and seed data. No separate staging/sandbox deployment. CloudFormation template has single environment with no parameterization.
- **Gap**: No staging environment with production-equivalent data shape for agent testing.
- **Recommendation**: Parameterize CloudFormation template. Deploy staging stack with anonymized data.
- **Evidence**: `docker-compose.yml`, `infrastructure/monolith-apprunner.yaml`, `index.php` (`seed_data()`)

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: PII stored unclassified across multiple MySQL tables (customer_name, customer_email, shipping_address in orders; email, password in users). No field-level encryption, no data classification tags, no access controls preventing agent from retrieving PII.
- **Gap**: Sensitive data is unclassified. Agent with read access receives customer PII with no controls.
- **Recommendation**: Create data classification inventory. Implement API response filtering to exclude PII from agent-facing endpoints.
- **Evidence**: `index.php` (`init_db()` CREATE TABLE statements), `infrastructure/monolith-apprunner.yaml`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: RDS deployed to stack's AWS region. Database contains customer PII. No documented data residency requirements, no GDPR/compliance references, no cross-region controls.
- **Gap**: No documented data residency requirements or controls.
- **Recommendation**: Conduct data residency assessment with legal/compliance team.
- **Evidence**: `infrastructure/monolith-apprunner.yaml` (RDS), `index.php` (PII in tables)

#### DATA-Q3: Selective Query Support
- **Severity**: RISK-QUALITY
- **Finding**: `GET /api/products` returns all products (`SELECT * FROM inventory`). `GET /api/orders/me` returns all customer orders. No pagination, filtering, or sorting parameters on any list endpoint.
- **Gap**: Unbounded result sets from list endpoints.
- **Recommendation**: Add pagination support (limit, offset, cursor) to all list endpoints.
- **Evidence**: `index.php` (SQL queries on list endpoints)

#### DATA-Q4: System of Record Designations
- **Severity**: INFO
- **Finding**: Single MySQL database is the de facto system of record for all domains. No explicit designation documented.
- **Gap**: No explicit system-of-record documentation.
- **Recommendation**: Document system-of-record designations. Plan ownership for microservices decomposition.
- **Evidence**: `index.php` (single `get_db()` connection, all tables in `init_db()`)

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK-QUALITY
- **Finding**: Orders have `created_at`/`updated_at`. Inventory table has NO timestamp fields. Timestamps use PHP `date()` with no explicit timezone. No Cache-Control or freshness headers.
- **Gap**: Agent cannot determine inventory data freshness. No timezone normalization.
- **Recommendation**: Add `updated_at` to inventory table. Set timestamps to UTC. Return `Last-Modified` headers.
- **Evidence**: `index.php` (CREATE TABLE statements — inventory has no timestamps)

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: PII leaks via `die()` with `$e->getMessage()`, error responses echoing exception text, validation endpoint returning customer PII, and unfiltered PHP error logging. No log scrubbing, no PII masking.
- **Gap**: PII not redacted from error messages, logs, or observability data.
- **Recommendation**: Implement centralized error handler with sanitized messages. Add PII log scrubbing.
- **Evidence**: `index.php` (`die()`, `$e->getMessage()` in error responses, validation-data endpoint)

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics, profiling, or freshness SLAs. Basic NOT NULL constraints only.
- **Gap**: No data quality monitoring.
- **Recommendation**: Implement basic data quality monitoring for inventory table.
- **Evidence**: `index.php` (schema constraints, seed_data function)

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: Database schema defined inline in `init_db()` with `CREATE TABLE IF NOT EXISTS`. Schema modifications via `ALTER TABLE` with silent error suppression. No migration files, no version tracking, no changelog. No API versioning (no `/v1/` prefix, no `Accept-Version`). No breaking change detection.
- **Gap**: Schema and API changes not versioned or tracked. Agent tool bindings could break silently.
- **Recommendation**: Implement database migration tooling (Phinx). Add API version prefix. Set up breaking change detection.
- **Evidence**: `index.php` (`init_db()` function, ALTER TABLE statements)

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: All field names are human-readable and semantically meaningful: `customer_name`, `stock_quantity`, `product_name`, `total_amount`, `tracking_number`, etc. No legacy abbreviations.
- **Gap**: None.
- **Recommendation**: Maintain current naming convention.
- **Evidence**: `index.php` (CREATE TABLE statements, API response structures)

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No data catalog, metadata layer, AWS Glue, or data dictionary. Schema defined only in PHP code.
- **Gap**: No external schema documentation or data catalog.
- **Recommendation**: Document data model. Consider AWS Glue Data Catalog.
- **Evidence**: `index.php` (`init_db()`), absence of metadata files

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: No distributed tracing (no X-Ray, no OpenTelemetry). PHP error logging only (`ini_set('log_errors', '1')`). Unstructured Apache error format. No request_id or correlation_id. CloudWatch log groups exist for infrastructure but no structured application events.
- **Gap**: Cannot trace agent-initiated requests through the system.
- **Recommendation**: Implement request ID middleware. Switch to structured JSON logging. Evaluate OpenTelemetry PHP SDK.
- **Evidence**: `index.php` (logging config), `infrastructure/monolith-apprunner.yaml` (CloudWatch log groups — no X-Ray)

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: No CloudWatch alarms defined. RDS Enhanced Monitoring enabled but no alerting thresholds. WAF metrics enabled but no alarms. No PagerDuty/OpsGenie/SNS integration.
- **Gap**: No automated alerting for API degradation.
- **Recommendation**: Define CloudWatch alarms for error rate, latency, RDS CPU, and WAF anomalies.
- **Evidence**: `infrastructure/monolith-apprunner.yaml` (no Alarm resources, MonitoringInterval: 60, CloudWatchMetricsEnabled)

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics. No `cloudwatch.put_metric_data`. WAF metrics only (security, not business). No business KPI dashboards.
- **Gap**: No business outcome visibility for agent-initiated actions.
- **Recommendation**: Implement custom CloudWatch metrics for inventory turnover, stockout frequency, fulfillment time.
- **Evidence**: `index.php` (no metrics emission), `infrastructure/monolith-apprunner.yaml` (WAF metrics only)

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK-QUALITY
- **Finding**: CloudFormation IaC covers VPC, RDS, App Runner, WAF, IAM, ECR, KMS. Comprehensive IaC. However: no PR review requirements (no CODEOWNERS), no drift detection (no AWS Config rules), manual deployment via `deploy.sh`.
- **Gap**: IaC exists but changes not subject to review and no drift detection.
- **Recommendation**: Add branch protection for infrastructure changes. Enable AWS Config drift detection.
- **Evidence**: `infrastructure/monolith-apprunner.yaml`, `deploy.sh`, absence of CODEOWNERS

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: No CI/CD pipeline. Manual deployment via `deploy.sh` (docker-compose build/up). No API contract tests, no OpenAPI validation, no breaking change detection.
- **Gap**: API-breaking changes cannot be detected before production.
- **Recommendation**: Implement CI/CD pipeline with Docker build, ECR push, CloudFormation update, and API contract validation.
- **Evidence**: `deploy.sh`, absence of CI/CD configuration files

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: No explicit rollback. App Runner supports native rollback but not configured with triggers. RDS has DeletionPolicy: Snapshot and 7-day backups. ECR ImageTagMutability: IMMUTABLE preserves previous images. No blue/green, no CodeDeploy, no feature flags.
- **Gap**: Rollback is manual and slow (30+ minutes estimated).
- **Recommendation**: Configure App Runner auto-rollback on health check failure. Create rollback script for ECR image revert.
- **Evidence**: `infrastructure/monolith-apprunner.yaml` (App Runner, RDS DeletionPolicy, ECR IMMUTABLE), `deploy.sh`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: Zero test files in the repository. No unit tests, integration tests, API tests, or contract tests. No test configuration (no phpunit.xml, no Postman collections). 25+ endpoints with zero coverage.
- **Gap**: API behavior changes uncaught by tests. Agent tool bindings rely on untested behavior.
- **Recommendation**: Create API tests for agent-facing endpoints (GET /api/products). Use PHPUnit or Postman/Newman.
- **Evidence**: Absence of test files, directories, and configuration

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: INFO
- **Finding**: Strong encryption-at-rest posture: RDS `StorageEncrypted: true`, ECR with KMS encryption (`EncryptionType: KMS`), VPC Flow Log CloudWatch group with KMS key (`KmsKeyId`), KMS keys with automatic rotation enabled (`EnableKeyRotation: true`). All persistent data stores are encrypted with customer-managed KMS keys.
- **Gap**: None. Encryption at rest is comprehensive.
- **Recommendation**: No action required. Maintain current encryption posture.
- **Evidence**: `infrastructure/monolith-apprunner.yaml` (DBInstance `StorageEncrypted: true`, ECRRepository `EncryptionConfiguration`, VPCFlowLogKMSKey, ECRKMSKey with `EnableKeyRotation: true`)

---

## Evidence Index

### Infrastructure as Code
| File | Questions Referenced |
|------|---------------------|
| `infrastructure/monolith-apprunner.yaml` | AUTH-Q1, AUTH-Q2, AUTH-Q4, AUTH-Q5, AUTH-Q6, STATE-Q5, STATE-Q7, DATA-Q1, DATA-Q2, OBS-Q1, OBS-Q2, OBS-Q3, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q5, API-Q8 |

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `index.php` | API-Q1, API-Q2, API-Q3, API-Q4, API-Q5, API-Q7, API-Q8, AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q2, STATE-Q3, STATE-Q5, STATE-Q6, HITL-Q1, HITL-Q2, HITL-Q3, DATA-Q1, DATA-Q2, DATA-Q3, DATA-Q4, DATA-Q5, DATA-Q6, DATA-Q7, DISC-Q1, DISC-Q2, DISC-Q3, OBS-Q1, OBS-Q3, ENG-Q4 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `Dockerfile` | ENG-Q3 |
| `docker-compose.yml` | AUTH-Q5, HITL-Q3, STATE-Q7 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `.htaccess` | API-Q1 |
| `deploy.sh` | ENG-Q1, ENG-Q2, ENG-Q3 |
| `.gitignore` | (repository hygiene — no questions directly reference) |

### Notable Absences (Files NOT Found)
| Absent File Type | Questions Impacted |
|------------------|-------------------|
| OpenAPI/Swagger/AsyncAPI specs | API-Q2, DISC-Q1 |
| CI/CD configuration (GitHub Actions, GitLab CI, Jenkinsfile, buildspec.yml) | ENG-Q2 |
| Test files (phpunit.xml, test directories, Postman collections) | ENG-Q4 |
| Dependency manifests (composer.json, package.json) | (PHP extensions installed via Dockerfile) |
| CODEOWNERS, branch protection config | ENG-Q1 |
| AWS Config rules | ENG-Q1 |
| CloudTrail configuration | AUTH-Q6 |
| Secrets Manager references | AUTH-Q5 |
| Database migration files | DISC-Q1 |


