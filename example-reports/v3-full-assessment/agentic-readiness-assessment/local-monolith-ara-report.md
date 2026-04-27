# Agentic Readiness Assessment Report

**Target**: ./monolith
**Date**: 2026-04-27
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P0
**Tags**: monolith, php, containers
**Context**: PHP monolith with Docker and CloudFormation on App Runner — containerize and expose inventory APIs the agent needs for restocking decisions.
**Archetype Justification**: MySQL database via PDO with CRUD endpoints (orders, inventory, users, returns), user-specific data, and entity lifecycle management (order status workflow). No external service calls, not primarily read-heavy — classic stateful-crud pattern.

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 2 | **RISK-SAFETY**: 8 | **RISK-QUALITY**: 16 | **INFOs**: 15

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days. The two BLOCKERs (AUTH-Q1: no machine identity authentication, DATA-Q1: unclassified PII) must be remediated before any agent — even a read-only pilot — can safely consume this system's APIs. Additionally, 8 RISK-SAFETY findings indicate significant safety gaps across authentication, state management, and data protection that must be addressed for safe agent operation.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 2 |
| RISK-SAFETY | 8 |
| RISK-QUALITY | 16 |
| INFO | 15 |
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
- **Finding**: The application uses session-based authentication exclusively (`session_start()`, `$_SESSION['user']`). Login is via username/password POST to `/login`. API auth check is `if (!isset($_SESSION['user']))` returning HTTP 401. No OAuth2 client credentials flow, no API key authentication, no mTLS, no service account support. The WAF provides IP whitelisting but no identity-level authentication.
- **Gap**: No machine identity authentication mechanism exists. An agent cannot authenticate without browser-based session cookies. There is no way to attribute API calls to a specific agent principal.
- **Remediation**:
  - **Immediate**: Implement API key authentication with principal attribution as a parallel auth path alongside session-based auth. Add an `X-API-Key` header check that maps to a registered machine identity with audit fields.
  - **Target State**: OAuth2 client credentials flow via Amazon Cognito app client, or API Gateway with IAM authorization, allowing agents to authenticate with scoped, attributable machine identities.
  - **Estimated Effort**: Medium (2–4 weeks)
  - **Dependencies**: AUTH-Q2 (scoped permissions) and AUTH-Q7 (identity suspension) depend on having machine identity before they can be addressed.
- **Evidence**: `index.php` (lines with `session_start()`, `$_SESSION['user']`, auth check at API routes), `infrastructure/monolith-apprunner.yaml` (WAF IP whitelist only)

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: Customer PII (names, emails, shipping addresses) is stored in the `orders`, `users`, and `interactions` tables with no classification tags, no field-level encryption, and no access controls beyond coarse admin/customer role checks. User passwords are bcrypt-hashed (good). RDS has `StorageEncrypted: true` (disk-level encryption). However, there is no field-level classification, no Amazon Macie integration, and no data classification policy. An agent with read access to `/api/orders/me` or `/api/admin/orders/pending-fulfillment` retrieves unclassified PII directly.
- **Gap**: PII fields (`customer_name`, `customer_email`, `shipping_address`) are not classified or tagged. No controls prevent an agent from retrieving sensitive customer data without explicit authorization. No data classification policy exists.
- **Remediation**:
  - **Immediate**: Create a data classification inventory mapping all PII fields across all tables. Implement field-level access controls that exclude PII from agent-facing API responses unless explicitly authorized.
  - **Target State**: Field-level classification tags on all PII fields, Amazon Macie scanning for PII in data stores, API response filtering that redacts PII for agent identities unless explicitly scoped.
  - **Estimated Effort**: Medium (3–6 weeks)
  - **Dependencies**: AUTH-Q1 (machine identity) must be resolved first — you cannot enforce field-level access controls for agents without knowing which principal is calling.
- **Evidence**: `index.php` (CREATE TABLE statements for `orders`, `users`, `interactions` with PII fields; API endpoints returning `customer_name`, `customer_email`), `infrastructure/monolith-apprunner.yaml` (`StorageEncrypted: true` on RDS — disk-level only)

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: IaC IAM roles are well-scoped: `AppRunnerInstanceRole` has CloudWatch Logs permissions scoped to specific log groups; `AppRunnerAccessRole` has ECR pull permissions scoped to the specific repository ARN. However, application-level authorization is coarse-grained — only two roles exist (`admin` and `customer`). Role check is binary: `$_SESSION['user']['role'] !== 'admin'`. There is no mechanism to grant an agent read-only access to specific resources (e.g., inventory only, not orders).
- **Gap**: Cannot scope an agent identity to specific resources or operations. An agent authenticated as "customer" gets all customer capabilities; as "admin" gets all admin capabilities. No intermediate or custom scopes.
- **Compensating Controls**:
  - Limit agent to a dedicated "customer" role with restricted session, reducing blast radius to customer-level operations only
  - Deploy an API Gateway in front of App Runner with resource-level IAM policies that restrict agent access to specific endpoints
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement RBAC with custom roles (e.g., `agent-inventory-reader`, `agent-order-viewer`) or deploy API Gateway with route-level authorization policies.
- **Evidence**: `index.php` (role checks: `$_SESSION['user']['role'] !== 'admin'`), `infrastructure/monolith-apprunner.yaml` (IAM roles with scoped policies)

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization exists. Within the `admin` role, a user can validate orders, assign warehouses, approve returns, and delete users — all with the same authorization level. Within the `customer` role, a user can place orders, submit returns, and view all their data. There are no `canRead`/`canWrite`/`canDelete` distinctions within either role.
- **Gap**: Cannot restrict an agent to read-only operations within a role. An agent with admin access could delete users or approve returns even if intended only for order viewing.
- **Compensating Controls**:
  - Deploy API Gateway with method-level (GET-only) restrictions for agent identities
  - Implement a middleware layer that checks operation type against agent permissions before executing
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add action-level permission checks in PHP middleware, or use API Gateway method-level authorization to restrict agents to GET requests only.
- **Evidence**: `index.php` (admin endpoints use only `$_SESSION['user']['role'] !== 'admin'` check with no further action-level granularity)

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The `order_status_history` table records status changes with a `changed_by` field (set to `$_SESSION['user']['username']` or `'system'`). However, this audit trail is stored in the same mutable MySQL database — it can be altered or deleted. No CloudTrail configuration exists in the CloudFormation template. VPC Flow Logs capture network traffic only. CloudWatch Logs capture App Runner stdout/stderr but not structured audit events.
- **Gap**: No immutable audit trail. Application-level audit is in a mutable database. No CloudTrail for AWS API-level auditing. Cannot prove compliance or conduct forensics on agent actions.
- **Compensating Controls**:
  - Enable CloudTrail in a separate stack with S3 bucket object lock for log immutability
  - Stream application audit events from CloudWatch Logs to an immutable S3 bucket with retention policies
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add CloudTrail configuration to the CloudFormation template with log file validation enabled and S3 object lock. Implement structured audit logging in the PHP application that writes to CloudWatch Logs with agent identity fields.
- **Evidence**: `index.php` (`order_status_history` table, `update_order_status()` function), `infrastructure/monolith-apprunner.yaml` (no CloudTrail resource, VPC Flow Logs only)

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No agent identity concept exists in the application. The `DELETE /api/admin/users/{id}` endpoint operates on session-based user accounts, not machine identities. There is no mechanism to suspend, revoke, or disable a specific agent identity without taking down broader access.
- **Gap**: Cannot isolate a misbehaving agent. If an agent credential is compromised, the only options are to change the shared database password or block IP addresses at the WAF — both affect all consumers.
- **Compensating Controls**:
  - Use API Gateway API keys that can be individually revoked without affecting other consumers
  - Implement WAF IP-based blocking rules to isolate specific agent traffic sources
- **Remediation Timeline**: 30–60 days (depends on AUTH-Q1 resolution)
- **Recommendation**: Implement machine identity (AUTH-Q1 prerequisite) with per-agent API keys or Cognito app clients that support individual revocation.
- **Evidence**: `index.php` (user deletion endpoint, no machine identity concept), `infrastructure/monolith-apprunner.yaml` (WAF IP whitelist — no per-identity controls)

#### STATE-Q1: Compensation and Rollback ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Database-level transactions exist for atomic operations: `$db->beginTransaction()`, `$db->commit()`, `$db->rollBack()` are used in order creation and return approval. However, the multi-step fulfillment workflow (confirmed → validated → warehouse_assigned → picking → packed → quality_checked → shipped → delivered) has no compensation or undo logic. Once an order is moved to `shipped` status, there is no reverse operation. Each step is an independent `UPDATE` with no saga pattern.
- **Gap**: No compensation for multi-step workflows. A partially completed fulfillment sequence leaves the order in an intermediate state with no automated recovery.
- **Compensating Controls**:
  - Implement status-based guards that prevent advancing to the next step if the previous step hasn't been verified
  - Add manual rollback endpoints for each fulfillment step as compensating actions
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement a saga pattern with compensating actions for each fulfillment step, or use AWS Step Functions to orchestrate the workflow with built-in error handling and rollback states.
- **Evidence**: `index.php` (`$db->beginTransaction()`/`$db->commit()`/`$db->rollBack()` in order creation; `update_order_status()` function with no compensation logic)

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No rate limiting exists at any layer. The WAF in CloudFormation has IP whitelist and bad input rules but no rate-based rules (`AWS::WAFv2::WebACL` has `AllowSpecificIP` and `BlockLog4jExploits` rules only). App Runner AutoScaling (min=1, max=3, maxConcurrency=100) provides capacity protection but is not rate limiting — it scales up rather than rejecting excess requests. No application-level rate limiting middleware exists in the PHP code.
- **Gap**: A runaway agent loop or misconfigured agent could overwhelm the application at machine speed. No per-identity or per-endpoint throttling.
- **Compensating Controls**:
  - Add a WAF rate-based rule (e.g., 100 requests/5 minutes per IP) to the CloudFormation template
  - Deploy API Gateway in front of App Runner with usage plans and throttling configuration
- **Remediation Timeline**: 7–14 days (WAF rate rule is a quick win)
- **Recommendation**: Add `AWS::WAFv2::RateBasedStatement` to the WAF WebACL as an immediate mitigation. For per-identity throttling, deploy API Gateway with usage plans.
- **Evidence**: `infrastructure/monolith-apprunner.yaml` (WAF rules — no rate-based rules; AutoScaling config), `index.php` (no rate limiting middleware)

#### DATA-Q2: Data Residency and Sovereignty ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No data residency configuration or documentation exists. The CloudFormation template uses `${AWS::Region}` for region-parameterized resources, but no data residency constraints are defined. Customer PII (names, emails, shipping addresses) is stored in RDS without any residency controls. If EU customers exist, GDPR data residency requirements may apply. No documentation addresses whether data can be transmitted to an LLM provider in a different region.
- **Gap**: No data residency controls. No documentation of residency requirements. Customer PII may be subject to GDPR or other residency regulations.
- **Compensating Controls**:
  - Document the data residency posture and confirm deployment region aligns with customer base
  - Use Amazon Bedrock with in-region inference endpoints to avoid cross-region data transmission
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Conduct a data residency assessment. Document which customer data is subject to residency requirements. Configure the agent to use in-region LLM endpoints (e.g., Amazon Bedrock in the same region as RDS).
- **Evidence**: `infrastructure/monolith-apprunner.yaml` (`${AWS::Region}` usage, no residency constraints), `index.php` (PII fields in orders and users tables)

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: PHP error logging is enabled (`ini_set('log_errors', '1')`) but no PII redaction exists. Error responses include `$e->getMessage()` which may contain database error messages with PII (e.g., duplicate key violations including email addresses). API responses include `customer_name`, `customer_email`, and `shipping_address` which will appear in App Runner stdout logs captured by CloudWatch. No log scrubbing middleware, no Amazon Macie integration for log scanning.
- **Gap**: PII can leak into error logs and CloudWatch Logs. No redaction, masking, or filtering of sensitive data in log outputs.
- **Compensating Controls**:
  - Wrap exception messages in a sanitizer that strips PII before logging
  - Configure CloudWatch Logs metric filters to alert on PII patterns
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Implement a log sanitization layer that masks PII fields before writing to logs. Use generic error messages in API responses instead of raw exception messages. Consider Amazon Macie for automated PII detection in log data.
- **Evidence**: `index.php` (`ini_set('log_errors', '1')`, `json_encode(['error' => $e->getMessage()])` in catch blocks, PII fields in API responses)

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No machine-readable API specification exists in the repository. No OpenAPI/Swagger, AsyncAPI, GraphQL schema, or Smithy files found. The API surface is defined entirely through `preg_match` route patterns in `index.php` with no external documentation.
- **Gap**: Agent tool definitions must be manually authored. No automated tool generation possible. API contract drift will be undetectable.
- **Compensating Controls**:
  - Manually create tool definitions for the agent based on code analysis
  - Generate an OpenAPI spec from the existing routes as a one-time documentation effort
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Generate an OpenAPI 3.0 specification documenting all API endpoints, request/response schemas, and error codes. Integrate spec generation into the deployment process.
- **Evidence**: Repository root (no `openapi.yaml`, `swagger.json`, or `.graphql` files found)

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Error responses follow a partial pattern: HTTP status codes (401, 403, 404, 400, 500) are set correctly, and a JSON body with an `error` field containing a message string is returned (e.g., `json_encode(['error' => $e->getMessage()])`). However, there is no structured error code, no retryable indicator, and no error category. Agents cannot programmatically distinguish retriable errors from terminal errors.
- **Gap**: No structured error codes or retryable boolean. Agents must parse error message strings to determine retry strategy.
- **Compensating Controls**:
  - Define retry logic in the agent based on HTTP status codes (retry on 500/503, don't retry on 400/401/403/404)
  - Add error code mapping in agent tool definitions
- **Remediation Timeline**: 7–14 days
- **Recommendation**: Standardize error responses to include `{error_code, message, retryable}` in all error JSON bodies. Define an error code taxonomy (e.g., `INSUFFICIENT_INVENTORY`, `ORDER_NOT_FOUND`, `UNAUTHORIZED`).
- **Evidence**: `index.php` (error response patterns: `json_encode(['error' => $e->getMessage()])`, HTTP status code usage)

#### AUTH-Q4: Identity Propagation and Delegation — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Session-based authentication only. No JWT, no OAuth2 on-behalf-of flows, no token exchange patterns. The `changed_by` field in `order_status_history` records `$_SESSION['user']['username']` or `'system'` but cannot distinguish between an agent acting on its own identity versus on behalf of a specific human user. No separate auth flows for service-to-service versus user-delegated calls.
- **Gap**: Cannot distinguish agent-as-self from agent-on-behalf-of-user. All requests are attributed to session user only.
- **Compensating Controls**:
  - Add `X-On-Behalf-Of` header support that the agent passes to indicate delegation context
  - Log both agent identity and delegated user identity in audit records
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement JWT-based authentication with claims that distinguish agent identity from delegated user identity. Add `actor` and `subject` fields to audit log entries.
- **Evidence**: `index.php` (`$_SESSION['user']` auth pattern, `changed_by` field in `update_order_status()`)

#### AUTH-Q5: Credential Management — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Database credentials have hardcoded fallback defaults in `index.php`: `getenv('DB_PASS') ?: 'ecommerce_pass'` and `getenv('DB_USER') ?: 'ecommerce_user'`. Seed data contains hardcoded demo passwords: `password_hash('customer123', PASSWORD_BCRYPT)`. In CloudFormation, `DBUsername` and `DBPassword` are `NoEcho` parameters passed directly as App Runner environment variables — not via Secrets Manager. Docker-compose uses required environment variables (`MYSQL_PASSWORD: ${MYSQL_PASSWORD:?Set MYSQL_PASSWORD}`) which is better but still plaintext env vars. No Secrets Manager or Vault integration.
- **Gap**: Hardcoded fallback credentials in code. No secrets rotation. DB password in plaintext environment variables.
- **Compensating Controls**:
  - Remove hardcoded fallback defaults from `index.php` — fail fast if environment variables are not set
  - Use AWS Secrets Manager to store and rotate database credentials
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Migrate database credentials to AWS Secrets Manager. Remove hardcoded fallbacks from `index.php`. Update CloudFormation to reference Secrets Manager secrets in App Runner configuration. Enable automatic rotation.
- **Evidence**: `index.php` (`getenv('DB_PASS') ?: 'ecommerce_pass'`, `password_hash('customer123', ...)`), `docker-compose.yml` (env vars), `infrastructure/monolith-apprunner.yaml` (`DBPassword` as NoEcho parameter passed to env vars)

#### STATE-Q7: Infrastructure Capacity for Agent Traffic — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: App Runner AutoScaling is configured with min=1, max=3 instances, maxConcurrency=100. RDS uses `db.t3.micro` (single instance, Multi-AZ). No load test configurations or results found. No capacity planning documentation. The `db.t3.micro` instance class is appropriate for development/testing but undersized for production agent traffic patterns which are unpredictable and bursty.
- **Gap**: Minimal scaling headroom. No load testing evidence. Database is undersized for production agent traffic.
- **Compensating Controls**:
  - Increase App Runner max instances and RDS instance class before any agent pilot
  - Run load tests simulating agent traffic patterns before enabling agent access
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Upgrade RDS to at least `db.t3.medium` for production. Increase App Runner max instances to 10+. Conduct load testing simulating agent query patterns (rapid sequential reads, concurrent requests).
- **Evidence**: `infrastructure/monolith-apprunner.yaml` (AutoScaling: min=1, max=3, maxConcurrency=100; RDS: `db.t3.micro`, Multi-AZ: true)

#### DATA-Q3: Selective Query Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No pagination, filtering, or result size limits on any endpoint. `GET /api/products` executes `SELECT * FROM inventory` returning all products. `GET /api/orders/me` returns all customer orders. `GET /api/admin/orders/pending-fulfillment` returns all pending orders. No `limit`, `offset`, `cursor`, or filter query parameters are supported.
- **Gap**: Unbounded result sets. An agent querying products or orders gets everything, exhausting LLM context windows and increasing cost.
- **Compensating Controls**:
  - Implement client-side result truncation in the agent tool definition
  - Add `LIMIT` clauses to SQL queries as a default cap (e.g., 100 records)
- **Remediation Timeline**: 7–14 days
- **Recommendation**: Add pagination parameters (`limit`, `offset` or `cursor`) to all list endpoints. Enforce a maximum result size (e.g., 100 records) with a default of 20.
- **Evidence**: `index.php` (`SELECT * FROM inventory`, `SELECT * FROM orders WHERE customer_id = ?` — no LIMIT clauses)

#### DATA-Q4: System of Record Designations — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The monolith is the de facto system of record for all entities (orders, inventory, payments, returns, users, warehouses). Single database, single application. No formal system-of-record designations or data ownership documentation exist.
- **Gap**: No formal SoR designations. When the monolith is decomposed into microservices, data ownership will need to be explicitly defined to prevent conflicting records.
- **Compensating Controls**:
  - Document current data ownership (monolith owns all entities) as baseline
  - Define SoR designations as part of the microservice decomposition plan
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a data ownership matrix mapping each entity to its authoritative source. This becomes critical during microservice decomposition.
- **Evidence**: `index.php` (all tables defined in `init_db()`, all CRUD operations in single application)

#### DATA-Q5: Temporal Metadata and Freshness — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Timestamps exist on key entities: `orders` has `created_at DATETIME` and `updated_at DATETIME`; `order_status_history` has `created_at`; `returns` has `created_at` and `processed_at`; `users` has `created_at`. Timestamps use PHP `date('Y-m-d H:i:s')` — server local time with no explicit UTC normalization. No `Cache-Control`, `X-Data-Age`, or consistency-level headers in API responses.
- **Gap**: No timezone normalization (timestamps may drift with server timezone). No freshness headers for agent data-currency reasoning.
- **Compensating Controls**:
  - Set PHP timezone to UTC explicitly (`date_default_timezone_set('UTC')`)
  - Document the timezone assumption for agent tool definitions
- **Remediation Timeline**: 7–14 days
- **Recommendation**: Set server timezone to UTC in PHP configuration. Add `Cache-Control` and `Last-Modified` headers to GET responses. Include `updated_at` in all entity API responses.
- **Evidence**: `index.php` (`created_at DATETIME`, `updated_at DATETIME` in table definitions; `date('Y-m-d H:i:s')` without timezone)

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Database schema is defined inline in the `init_db()` function in `index.php` with `CREATE TABLE IF NOT EXISTS` statements. Schema modifications use `ALTER TABLE` wrapped in try/catch (e.g., adding `warehouse_location`, `weight_lbs`, `dimensions` columns). No formal migration system (no Flyway, no Phinx, no Laravel migrations). No API versioning — no `/v1/` or `/v2/` URL patterns, no `Accept-Version` headers. No changelog files. No breaking change detection tools.
- **Gap**: Schema and API changes are unversioned. Agent tool bindings can break silently when the schema changes. No migration history.
- **Compensating Controls**:
  - Pin agent tool definitions to specific expected response schemas
  - Add schema validation tests that alert on response structure changes
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement a database migration system (e.g., Phinx for PHP). Add API versioning (URL-based `/v1/` prefix). Implement OpenAPI spec diff in CI to detect breaking changes.
- **Evidence**: `index.php` (`init_db()` function with inline CREATE TABLE, ALTER TABLE with try/catch)

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No distributed tracing (no X-Ray, no OpenTelemetry). PHP error logging is enabled via `ini_set('log_errors', '1')` but logs are unstructured text written to Apache error log. No correlation IDs or request IDs in API responses or log entries. App Runner captures stdout/stderr to CloudWatch but no structured (JSON) log format is used. RDS Enhanced Monitoring is enabled (MonitoringInterval: 60) — infrastructure-level only.
- **Gap**: Cannot trace an agent-initiated request through the system. Cannot correlate log entries for a single request. Agent failures are not debuggable.
- **Compensating Controls**:
  - Generate a request ID in PHP and include it in all API responses and log entries
  - Use CloudWatch Logs Insights to query unstructured logs by timestamp
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Implement structured JSON logging with request IDs. Add X-Ray SDK for PHP or OpenTelemetry instrumentation. Include `X-Request-Id` header in all API responses.
- **Evidence**: `index.php` (`ini_set('log_errors', '1')`, no correlation ID generation), `infrastructure/monolith-apprunner.yaml` (RDS MonitoringInterval: 60, no X-Ray config)

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No CloudWatch alarms defined in the CloudFormation template. WAF has `CloudWatchMetricsEnabled: true` (metrics are collected but no alarms trigger on them). App Runner has health checks configured (HTTP, interval: 10s, timeout: 5s) but no alarm integration. No PagerDuty, OpsGenie, or SNS notification configuration.
- **Gap**: No alerting for error rates or latency. Target system degradation affecting agents will go undetected until users report issues.
- **Compensating Controls**:
  - Add CloudWatch alarms for App Runner 5xx error rate and P99 latency
  - Configure SNS topic for alarm notifications
- **Remediation Timeline**: 7–14 days
- **Recommendation**: Add CloudWatch alarms to the CloudFormation template for App Runner HTTP 5xx rate > 1%, P99 latency > 2s, and RDS CPU utilization > 80%. Connect to SNS for notifications.
- **Evidence**: `infrastructure/monolith-apprunner.yaml` (WAF CloudWatchMetricsEnabled: true, HealthCheckConfiguration, no CloudWatch Alarm resources)

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Sub-check 1 (IaC definition): YES — CloudFormation template defines VPC, RDS, App Runner, WAF, IAM roles, ECR, and KMS keys. Sub-check 2 (Peer review): UNKNOWN — no branch protection rules, no PR requirements visible in the repository. Sub-check 3 (Drift detection): NO — no AWS Config rules or CloudFormation drift detection configuration.
- **Gap**: IaC exists but governance is incomplete. No evidence of mandatory peer review for infrastructure changes. No drift detection to ensure deployed state matches IaC definitions.
- **Compensating Controls**:
  - Enable CloudFormation drift detection manually or via scheduled Lambda
  - Implement branch protection rules requiring PR approval for IaC changes
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Enable CloudFormation drift detection. Add AWS Config rules for critical resources. Implement branch protection requiring at least one reviewer for changes to `infrastructure/`.
- **Evidence**: `infrastructure/monolith-apprunner.yaml` (comprehensive IaC), repository root (no `.github/`, no branch protection config)

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No CI/CD pipeline configuration exists. No `.github/workflows/`, no `.gitlab-ci.yml`, no `Jenkinsfile`, no `buildspec.yml`. The only deployment mechanism is `deploy.sh` — a manual script that runs `docker-compose build` and `docker-compose up -d`. No automated testing, no contract testing, no breaking change detection.
- **Gap**: No CI/CD pipeline. No automated testing. API changes go directly to production without validation. Agent tool breakage is not caught before deployment.
- **Compensating Controls**:
  - Implement a minimal CI pipeline with API smoke tests before deployment
  - Add manual pre-deployment checklist including API contract verification
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a CI/CD pipeline (GitHub Actions or AWS CodePipeline) with API contract tests, OpenAPI spec validation, and automated deployment to App Runner via ECR image push.
- **Evidence**: `deploy.sh` (manual docker-compose deployment), repository root (no CI/CD config files)

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Partial rollback capability exists. App Runner supports automatic rollback on failed deployments (built-in platform behavior). RDS has `DeletionPolicy: Snapshot` and `BackupRetentionPeriod: 7` days. ECR has `ImageTagMutability: IMMUTABLE` preserving image history for rollback. However, no explicit rollback strategy is defined, no blue/green or canary deployment configuration, and `deploy.sh` has no rollback logic.
- **Gap**: No explicit rollback automation. Rollback depends on App Runner built-in behavior and manual ECR image tag selection. Database rollback requires manual snapshot restoration.
- **Compensating Controls**:
  - Document manual rollback procedure using ECR immutable image tags
  - Test App Runner's built-in rollback behavior before agent deployment
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Document and test the rollback procedure. Add rollback step to `deploy.sh`. Consider implementing blue/green deployment with App Runner traffic splitting.
- **Evidence**: `infrastructure/monolith-apprunner.yaml` (ECR: IMMUTABLE, RDS: DeletionPolicy: Snapshot, BackupRetentionPeriod: 7), `deploy.sh` (no rollback logic)

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Zero test coverage. No test files exist anywhere in the repository. No `phpunit.xml`, no `tests/` directory, no Postman/Newman collections, no integration test scripts, no API test configurations. No test steps in any deployment process.
- **Gap**: No automated verification of API behavior. Input handling, output format, error responses, and edge cases are untested. Any code change could break agent-facing APIs without detection.
- **Compensating Controls**:
  - Create a minimal Postman collection validating core API endpoints used by the agent
  - Implement smoke tests as part of deployment
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a PHPUnit test suite covering API endpoints, particularly those the agent will consume (GET /api/products, GET /api/orders/me, GET /api/orders/{id}/validation-data). Add test execution to CI/CD pipeline.
- **Evidence**: Repository root (no test files, no test configuration, no test directories)

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: `docker-compose.yml` provides a local development environment with MySQL 8.0 + PHP monolith. The `seed_data()` function in `index.php` creates sample data (products, warehouses, users, sample orders). However, no separate staging or sandbox environment configuration exists. The CloudFormation template defines a single production environment. No environment-specific configuration files (no `staging.yaml`, no environment parameter files).
- **Gap**: No dedicated staging/sandbox environment with production-equivalent data shape. Agents must be tested against either the local docker-compose environment (limited) or production directly.
- **Compensating Controls**:
  - Use docker-compose as a local sandbox for initial agent testing
  - Deploy a second CloudFormation stack with "staging" parameters for pre-production testing
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Create a staging environment by deploying the CloudFormation stack with staging-specific parameters. Add synthetic data generation that mirrors production data shape (volume, variety, edge cases).
- **Evidence**: `docker-compose.yml` (local dev environment), `index.php` (`seed_data()` function), `infrastructure/monolith-apprunner.yaml` (single environment definition)

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO
- **Finding**: The application exposes a comprehensive REST API surface with 27+ JSON endpoints covering products, orders, fulfillment workflow, returns, user management, and administrative operations. All endpoints return `Content-Type: application/json`. Integration does not require direct database access, file-based exchange, or UI automation. The API exists and is functional but lacks external documentation (see API-Q2).
- **Implication**: An agent can integrate via REST APIs. The API surface is broad enough to support inventory queries, order inquiries, and fulfillment monitoring — all relevant to the restocking agent use case.
- **Recommendation**: While the API exists, create formal documentation (API-Q2) to enable automated tool generation for the agent.
- **Evidence**: `index.php` (27+ API route definitions via `preg_match`, `header('Content-Type: application/json')`)

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No idempotency support on write endpoints. Order IDs are generated via `uniqid('order-')`. POST `/api/orders` with the same payload will create duplicate orders. No idempotency key headers or middleware. However, agent_scope is read-only — write operations are not in scope.
- **Implication**: If agent scope expands to write-enabled in the future, idempotency must be implemented before allowing agent-initiated writes. This is a prerequisite for write-enabled promotion.
- **Recommendation**: Plan idempotency key support for POST endpoints as part of the write-enabled readiness roadmap.
- **Evidence**: `index.php` (`uniqid('order-')` for order IDs, no idempotency key support)

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: All API responses use JSON via `json_encode()`. Responses are well-structured with nested objects (e.g., `{order: {...}, customer: {...}, risk_factors: [...]}` for validation data). No XML, binary, or protobuf formats. JSON is the universal format — no parsing complexity for agent consumption.
- **Implication**: JSON responses are ideal for LLM-based agent consumption. No format conversion required.
- **Recommendation**: No action needed. JSON format is well-suited for agent integration.
- **Evidence**: `index.php` (`json_encode()` in all API responses, `header('Content-Type: application/json')`)

### API-Q7: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: No event emission. State changes (order status transitions, return submissions, inventory updates) are recorded in the `order_status_history` database table but no events are published to external consumers. No SNS, EventBridge, SQS, Kafka, or webhook integrations exist.
- **Implication**: The restocking agent cannot receive proactive notifications when inventory changes. It must poll the `GET /api/products` endpoint to detect stock level changes. This limits the agent to reactive patterns.
- **Recommendation**: Consider adding EventBridge integration for inventory-level-change events as part of the microservice decomposition. This would enable proactive restocking triggers.
- **Evidence**: `index.php` (`order_status_history` table, no SNS/EventBridge/SQS integration)

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limit documentation or headers. WAF exists in CloudFormation but has no rate-based rules (only IP whitelist + bad input protection). No `X-RateLimit-Remaining`, `X-RateLimit-Limit`, or `Retry-After` headers in PHP responses. API Gateway (which would provide rate limit headers) is not deployed.
- **Implication**: The agent has no way to self-throttle based on server-signaled limits. Combined with STATE-Q5 (no rate limiting), this creates a risk of the agent overwhelming the system without feedback.
- **Recommendation**: When rate limiting is implemented (STATE-Q5), include rate limit headers in API responses to enable agent self-throttling.
- **Evidence**: `infrastructure/monolith-apprunner.yaml` (WAF rules — no rate-based), `index.php` (no rate limit headers)

### STATE-Q2: Queryable Current State

- **Severity**: INFO
- **Finding**: State is queryable via multiple GET endpoints: `GET /api/products` (inventory with stock quantities), `GET /api/orders/me` (customer orders with status), `GET /api/orders/{id}/history` (order status history), `GET /api/orders/{id}/validation-data` (fraud/risk context), `GET /api/admin/orders/pending-fulfillment` (admin order queue). The restocking agent can query current inventory levels and order statuses before making decisions.
- **Implication**: Positive finding. The agent can read current state before deciding on restocking actions. The `stock_quantity` field in inventory is directly usable for restocking threshold decisions.
- **Recommendation**: No action needed. Consider adding a dedicated `/api/inventory/low-stock` endpoint that filters products below a configurable threshold.
- **Evidence**: `index.php` (GET endpoints for products, orders, order history, validation data, pending fulfillment)

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No concurrency controls exist. No optimistic locking (no version fields, no ETags, no `If-Match` headers). No pessimistic locking (`SELECT FOR UPDATE`). Updates use direct `UPDATE ... WHERE id = ?` without conflict detection. DynamoDB conditional writes are not applicable (MySQL is used).
- **Implication**: Not a concern for read-only agent scope. If scope expands to write-enabled, concurrent agent writes (e.g., multiple agents adjusting inventory) will create race conditions.
- **Recommendation**: Plan optimistic locking (version fields or ETags) for write-enabled scope expansion.
- **Evidence**: `index.php` (UPDATE statements without version checks or locking)

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits exist. No per-identity limits, no maximum records per operation, no spend limits. All write operations execute without bounds.
- **Implication**: Not a concern for read-only scope. If scope expands to write-enabled, uncapped operations could cause significant damage (e.g., an agent approving all returns in a loop).
- **Recommendation**: Plan transaction limits as part of write-enabled scope expansion. Define maximum operations per session/hour for agent identities.
- **Evidence**: `index.php` (no limit checks on any write operations)

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Draft/pending states exist in the application. The order fulfillment workflow has multiple intermediate states (pending → confirmed → validated → warehouse_assigned → picking → packed → quality_checked → shipped → delivered). Returns use `pending_review` status requiring admin approval before processing. These patterns support human-in-the-loop workflows.
- **Implication**: Positive for future write-enabled scope. The existing workflow states could be leveraged for agent draft/review patterns where an agent proposes an action and a human approves.
- **Recommendation**: No action needed for read-only scope. For write-enabled expansion, consider adding an `agent_proposed` intermediate status for agent-initiated actions.
- **Evidence**: `index.php` (order status workflow, `pending_review` status for returns)

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Manual approval steps exist in the workflow: returns require admin approval (`POST /api/admin/approve-return`), order validation requires manual approval (`POST /api/orders/{id}/validate`), quality check requires manual pass/fail (`POST /api/orders/{id}/quality-check`). However, these are hardcoded workflow steps — not configurable per operation type or per identity.
- **Implication**: Approval gates exist but are rigid. For write-enabled agent scope, these gates would need to be configurable (e.g., auto-approve for low-value returns, require human approval for high-value).
- **Recommendation**: No action needed for read-only scope. For write-enabled expansion, make approval thresholds configurable per operation and per identity.
- **Evidence**: `index.php` (`POST /api/admin/approve-return`, `POST /api/orders/{id}/validate`, `POST /api/orders/{id}/quality-check`)

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality metrics, dashboards, or monitoring exist. No null rate monitoring, no duplicate detection, no data freshness SLAs. The `seed_data()` function provides consistent sample data for development, but no production data quality mechanisms are in place.
- **Implication**: The restocking agent will consume inventory data (stock quantities) without knowing its accuracy or completeness. Stale or incorrect stock quantities could lead to under- or over-ordering.
- **Recommendation**: Implement data quality monitoring for inventory data — track null rates, detect anomalous stock level changes, and establish freshness SLAs for inventory counts.
- **Evidence**: `index.php` (no data quality metrics, `seed_data()` for dev only)

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Database fields use clear, human-readable names throughout: `customer_id`, `customer_name`, `customer_email`, `stock_quantity`, `product_name`, `total_amount`, `tracking_number`, `warehouse_location`, `shipping_address`, `refund_amount`, `payment_method`. No legacy abbreviations or cryptic codes.
- **Implication**: Positive finding. LLM-based agents can reason about field names without a lookup table. This reduces tool definition complexity and improves agent reasoning quality.
- **Recommendation**: No action needed. Maintain this naming convention as the system evolves.
- **Evidence**: `index.php` (CREATE TABLE statements with descriptive field names)

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No data catalog, metadata layer, or data dictionary exists. Schema documentation exists only as SQL `CREATE TABLE IF NOT EXISTS` statements within the `init_db()` function in `index.php`. No AWS Glue Data Catalog, Collibra, Alation, or DataHub integration.
- **Implication**: Agent tool builders must read the source code to understand what data the system holds. A data catalog would accelerate tool definition and improve agent context about available data.
- **Recommendation**: Create a simple data dictionary documenting tables, fields, relationships, and data types. Consider AWS Glue Data Catalog if the data is also accessed by analytics workloads.
- **Evidence**: `index.php` (`init_db()` function with SQL CREATE TABLE statements — only schema documentation)

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No custom business metrics are published. No `put_metric_data` calls, no custom CloudWatch dashboards, no business KPI tracking (order completion rates, return rates, inventory turnover, restocking efficiency).
- **Implication**: When the restocking agent is deployed, there will be no baseline metrics to compare against. Cannot measure whether agent-initiated restocking decisions improve inventory turnover or reduce stockouts.
- **Recommendation**: Implement business metrics for inventory levels, stockout rates, and order fulfillment times before agent deployment. This provides the baseline needed to measure agent effectiveness.
- **Evidence**: `index.php` (no CloudWatch metric publishing), `infrastructure/monolith-apprunner.yaml` (no custom metric resources)

### ENG-Q5: Encryption at Rest

- **Severity**: INFO
- **Finding**: Encryption at rest is well-configured. RDS has `StorageEncrypted: true` (AWS-managed encryption). ECR uses a customer-managed KMS key (`ECRKMSKey`) with `EnableKeyRotation: true`. VPC Flow Log CloudWatch Log Group is encrypted with a customer-managed KMS key (`VPCFlowLogKMSKey`) with `EnableKeyRotation: true`. Both KMS keys have proper key policies.
- **Implication**: Positive finding. Data at rest is encrypted across all persistent stores. This meets encryption requirements for agent-accessible data.
- **Recommendation**: No action needed. Consider upgrading RDS encryption to a customer-managed KMS key (currently using AWS-managed default) for additional control.
- **Evidence**: `infrastructure/monolith-apprunner.yaml` (`StorageEncrypted: true` on RDS, `ECRKMSKey` with `EnableKeyRotation: true`, `VPCFlowLogKMSKey` with `EnableKeyRotation: true`)

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: The application exposes 27+ REST endpoints returning JSON. Integration does not require direct database access, file-based exchange, or UI automation. Endpoints include: GET /api/products, POST /api/orders, GET /api/orders/me, POST /api/returns, GET /api/orders/{id}/validation-data, GET /api/warehouses/assignment-options, GET /api/orders/{id}/picking-details, GET /api/orders/{id}/packing-options, GET /api/orders/{id}/quality-checklist, GET /api/carriers/shipping-options, and 17+ more. The API surface is functional but undocumented externally.
- **Gap**: APIs exist but lack formal external documentation (addressed in API-Q2).
- **Recommendation**: Create formal API documentation. The API surface is sufficient for agent integration.
- **Evidence**: `index.php` (all `preg_match` route definitions, `header('Content-Type: application/json')`)

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: No machine-readable API specification found. No OpenAPI, Swagger, AsyncAPI, GraphQL schema, or Smithy files exist in the repository.
- **Gap**: Agent tool definitions must be manually authored. No automated tool generation possible.
- **Recommendation**: Generate an OpenAPI 3.0 specification from existing routes.
- **Evidence**: Repository root (absence — no spec files found)

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: Partial structured errors. HTTP status codes (401, 403, 404, 400, 500) are used correctly. JSON error body: `{"error": "<message>"}`. No error code, no retryable indicator, no error category.
- **Gap**: No structured error codes or retryable boolean for agent retry logic.
- **Recommendation**: Add `{error_code, message, retryable}` to all error responses.
- **Evidence**: `index.php` (`json_encode(['error' => $e->getMessage()])`)

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No idempotency support. `uniqid()` generates order IDs. Duplicate POSTs create duplicate records. Agent scope is read-only — not a current concern.
- **Gap**: No idempotency keys on write endpoints.
- **Recommendation**: Plan idempotency support for write-enabled scope expansion.
- **Evidence**: `index.php` (`uniqid('order-')`, no idempotency key middleware)

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: All responses use JSON via `json_encode()`. Well-structured nested objects. No XML/binary/protobuf complexity.
- **Gap**: N/A — JSON is well-suited for agents.
- **Recommendation**: No action needed.
- **Evidence**: `index.php` (`json_encode()` throughout)

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has operations >30s OR long-running workflows. All PHP operations are synchronous and complete within seconds. The "24-48 hour" return review is a manual delay, not a long-running async operation.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: No event emission. State changes recorded in `order_status_history` table only. No SNS, EventBridge, SQS, Kafka, or webhooks.
- **Gap**: No external event publication. Agent must poll for state changes.
- **Recommendation**: Consider EventBridge integration for inventory change events.
- **Evidence**: `index.php` (`order_status_history` insert, no event publishing)

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit documentation or headers. WAF has no rate-based rules. No `X-RateLimit-*` or `Retry-After` headers.
- **Gap**: Agent cannot self-throttle based on server signals.
- **Recommendation**: Add rate limit headers when rate limiting is implemented (STATE-Q5).
- **Evidence**: `infrastructure/monolith-apprunner.yaml` (WAF config), `index.php` (no rate limit headers)

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: Session-based authentication only. `session_start()`, `$_SESSION['user']` for auth. Login via POST /login with username/password. API check: `if (!isset($_SESSION['user']))` → 401. No OAuth2, no API keys, no mTLS, no service accounts.
- **Gap**: No machine identity authentication. Agent cannot authenticate without browser session cookies.
- **Recommendation**: Implement API key or OAuth2 client credentials authentication.
- **Evidence**: `index.php` (`session_start()`, `$_SESSION['user']`, login handler)

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: Two application roles only: `admin` and `customer`. Binary role check. IaC IAM roles are well-scoped (specific ARNs, no wildcards).
- **Gap**: Cannot scope agent to specific resources or operations at the application level.
- **Recommendation**: Implement custom roles or API Gateway route-level authorization.
- **Evidence**: `index.php` (role checks), `infrastructure/monolith-apprunner.yaml` (IAM policies)

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: No action-level auth. Admin can do all admin operations. Customer can do all customer operations. No canRead/canWrite/canDelete distinctions.
- **Gap**: Cannot restrict agent to read-only within a role.
- **Recommendation**: Add method-level authorization checks or API Gateway GET-only restrictions.
- **Evidence**: `index.php` (all admin endpoints use same `role !== 'admin'` check)

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: RISK-QUALITY
- **Finding**: Session-based only. No JWT, no on-behalf-of flows, no token exchange. `changed_by` field records username but cannot distinguish agent from human.
- **Gap**: Cannot distinguish agent-as-self from agent-on-behalf-of-user.
- **Recommendation**: Implement JWT with actor/subject claims.
- **Evidence**: `index.php` (`$_SESSION['user']`, `changed_by` in `update_order_status()`)

#### AUTH-Q5: Credential Management
- **Severity**: RISK-QUALITY
- **Finding**: Hardcoded fallback: `getenv('DB_PASS') ?: 'ecommerce_pass'`. Demo passwords in seed data. DB creds as CloudFormation NoEcho params passed to env vars. No Secrets Manager.
- **Gap**: Hardcoded credentials, no secrets rotation, no secrets management.
- **Recommendation**: Migrate to AWS Secrets Manager. Remove hardcoded fallbacks.
- **Evidence**: `index.php` (fallback creds), `docker-compose.yml` (env vars), `infrastructure/monolith-apprunner.yaml` (NoEcho params)

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: `order_status_history` records changes in mutable MySQL table. No CloudTrail. VPC Flow Logs for network only. No immutable audit trail.
- **Gap**: Audit trail is mutable and incomplete. Cannot prove compliance.
- **Recommendation**: Add CloudTrail with S3 object lock. Implement structured audit logging.
- **Evidence**: `index.php` (`order_status_history`), `infrastructure/monolith-apprunner.yaml` (no CloudTrail)

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: No agent identity concept. User deletion exists but operates on session accounts. No mechanism to suspend/revoke agent identity.
- **Gap**: Cannot isolate misbehaving agent without affecting all consumers.
- **Recommendation**: Implement per-agent API keys or Cognito app clients with revocation support.
- **Evidence**: `index.php` (DELETE /api/admin/users — session accounts only)

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: DB transactions for atomic ops (`beginTransaction`/`commit`/`rollBack`). No saga pattern for multi-step fulfillment workflow. No compensation/undo endpoints.
- **Gap**: No compensation for multi-step workflows.
- **Recommendation**: Implement saga pattern or Step Functions for workflow orchestration.
- **Evidence**: `index.php` (transaction usage, `update_order_status()`)

#### STATE-Q2: Queryable Current State
- **Severity**: INFO
- **Finding**: State is queryable via GET /api/products, GET /api/orders/me, GET /api/orders/{id}/history, GET /api/admin/orders/pending-fulfillment, and more. Inventory stock quantities and order statuses are accessible.
- **Gap**: No gap — state is queryable. Consider adding low-stock filter endpoint.
- **Recommendation**: Add dedicated low-stock inventory endpoint for the restocking agent.
- **Evidence**: `index.php` (GET endpoints for all major entities)

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No optimistic locking, no version fields, no ETags, no SELECT FOR UPDATE. Direct UPDATE without conflict detection.
- **Gap**: No concurrency controls. Not a concern for read-only scope.
- **Recommendation**: Plan optimistic locking for write-enabled expansion.
- **Evidence**: `index.php` (UPDATE statements without version checks)

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has external dependencies (calls other services or external APIs). This monolith has no external HTTP service dependencies — it calls only its own MySQL database.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No rate limiting at any layer. WAF has no rate-based rules. App Runner AutoScaling is not rate limiting. No PHP rate limiting middleware.
- **Gap**: Runaway agent loop can overwhelm service at machine speed.
- **Recommendation**: Add WAF rate-based rule immediately. Deploy API Gateway with usage plans.
- **Evidence**: `infrastructure/monolith-apprunner.yaml` (WAF, AutoScaling), `index.php` (no middleware)

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits. No per-identity limits.
- **Gap**: No transaction limits. Not a concern for read-only scope.
- **Recommendation**: Plan transaction limits for write-enabled expansion.
- **Evidence**: `index.php` (no limit enforcement on any operations)

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: RISK-QUALITY
- **Finding**: App Runner: min=1, max=3, maxConcurrency=100. RDS: db.t3.micro, Multi-AZ. No load testing evidence. No capacity planning.
- **Gap**: Undersized for production agent traffic. No load testing.
- **Recommendation**: Upgrade RDS and increase App Runner max. Conduct load testing.
- **Evidence**: `infrastructure/monolith-apprunner.yaml` (scaling and RDS config)

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Multi-step order status workflow with intermediate states. Returns use `pending_review` status. These support HITL patterns.
- **Gap**: Workflow states exist but are not designed for agent draft/review patterns.
- **Recommendation**: For write-enabled expansion, add `agent_proposed` intermediate status.
- **Evidence**: `index.php` (order status workflow, `pending_review` for returns)

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Manual approval steps exist (return approval, order validation, quality check) but are hardcoded, not configurable per operation or identity.
- **Gap**: Approval gates are rigid, not configurable.
- **Recommendation**: For write-enabled expansion, make approval thresholds configurable.
- **Evidence**: `index.php` (approval endpoints: approve-return, validate, quality-check)

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: docker-compose.yml provides local dev environment. seed_data() creates sample data. No separate staging/sandbox environment. Single CloudFormation environment.
- **Gap**: No dedicated staging with production-equivalent data shape.
- **Recommendation**: Deploy second CloudFormation stack for staging. Add synthetic data generation.
- **Evidence**: `docker-compose.yml`, `index.php` (`seed_data()`), `infrastructure/monolith-apprunner.yaml`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: PII (customer_name, customer_email, shipping_address) in orders, users, interactions tables. No classification tags, no field-level encryption, no Macie. RDS StorageEncrypted: true (disk-level only).
- **Gap**: PII is unclassified. No controls prevent agent from retrieving unclassified PII.
- **Recommendation**: Create data classification inventory. Implement field-level access controls for agent identities.
- **Evidence**: `index.php` (table definitions, API responses with PII), `infrastructure/monolith-apprunner.yaml` (RDS encryption)

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No data residency controls. Region parameterized via `${AWS::Region}` but no constraints. Customer PII stored without residency documentation.
- **Gap**: No data residency controls or documentation.
- **Recommendation**: Conduct data residency assessment. Use in-region LLM endpoints.
- **Evidence**: `infrastructure/monolith-apprunner.yaml` (region config), `index.php` (PII fields)

#### DATA-Q3: Selective Query Support
- **Severity**: RISK-QUALITY
- **Finding**: No pagination, filtering, or result size limits. `SELECT * FROM inventory` returns all. No limit/offset/cursor parameters.
- **Gap**: Unbounded result sets exhaust LLM context windows.
- **Recommendation**: Add pagination to all list endpoints. Enforce max result size.
- **Evidence**: `index.php` (SQL queries without LIMIT, no pagination parameters)

#### DATA-Q4: System of Record Designations
- **Severity**: RISK-QUALITY
- **Finding**: Monolith is de facto SoR for all entities. Single database, single app. No formal designations.
- **Gap**: No formal SoR documentation. Critical for microservice decomposition.
- **Recommendation**: Create data ownership matrix.
- **Evidence**: `index.php` (all tables and CRUD in single application)

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK-QUALITY
- **Finding**: Timestamps exist (created_at, updated_at on orders; created_at on status history). PHP date() without explicit UTC. No Cache-Control or freshness headers.
- **Gap**: No timezone normalization. No freshness signals.
- **Recommendation**: Set UTC timezone. Add Cache-Control and Last-Modified headers.
- **Evidence**: `index.php` (DATETIME fields, `date('Y-m-d H:i:s')` without timezone)

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: PHP error logging enabled. No PII redaction. `$e->getMessage()` may include PII. Customer names/emails in API responses appear in App Runner logs.
- **Gap**: PII leaks into logs. No scrubbing or masking.
- **Recommendation**: Implement log sanitization. Use generic error messages.
- **Evidence**: `index.php` (`ini_set('log_errors', '1')`, `$e->getMessage()` in responses)

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics, dashboards, or monitoring. seed_data() for dev only.
- **Gap**: No visibility into data accuracy or completeness.
- **Recommendation**: Implement inventory data quality monitoring.
- **Evidence**: `index.php` (no quality metrics)

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: Schema inline in init_db(). ALTER TABLE with try/catch for modifications. No migration system, no API versioning, no breaking change detection.
- **Gap**: Unversioned schemas and APIs. Agent tool bindings break silently.
- **Recommendation**: Implement migration system and API versioning.
- **Evidence**: `index.php` (`init_db()`, ALTER TABLE statements)

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: All fields use clear names: customer_id, product_name, stock_quantity, shipping_address, etc. No legacy abbreviations.
- **Gap**: No gap — positive finding.
- **Recommendation**: Maintain naming conventions.
- **Evidence**: `index.php` (CREATE TABLE statements)

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No data catalog or metadata layer. Schema exists only as SQL in init_db().
- **Gap**: No discoverable metadata for agent tool builders.
- **Recommendation**: Create data dictionary. Consider Glue Data Catalog.
- **Evidence**: `index.php` (`init_db()`)

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: No distributed tracing (X-Ray/OpenTelemetry). Unstructured PHP error logging. No correlation IDs. RDS Enhanced Monitoring for infrastructure only.
- **Gap**: Agent-initiated requests not traceable or debuggable.
- **Recommendation**: Add structured JSON logging and X-Ray/OpenTelemetry instrumentation.
- **Evidence**: `index.php` (`ini_set('log_errors', '1')`), `infrastructure/monolith-apprunner.yaml` (MonitoringInterval)

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: No CloudWatch alarms. WAF metrics collected but no alarms. App Runner health checks without alarm integration.
- **Gap**: No alerting for system degradation.
- **Recommendation**: Add CloudWatch alarms for error rates and latency.
- **Evidence**: `infrastructure/monolith-apprunner.yaml` (CloudWatchMetricsEnabled, no Alarm resources)

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics. No put_metric_data calls. No KPI dashboards.
- **Gap**: No baseline for measuring agent effectiveness.
- **Recommendation**: Implement inventory and fulfillment business metrics.
- **Evidence**: `index.php` (no metric publishing), `infrastructure/monolith-apprunner.yaml`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK-QUALITY
- **Finding**: IaC exists (CloudFormation). No evidence of peer review. No drift detection.
- **Gap**: Incomplete governance — missing 2 of 3 sub-checks.
- **Recommendation**: Enable drift detection. Implement branch protection.
- **Evidence**: `infrastructure/monolith-apprunner.yaml` (IaC exists), repository root (no review config)

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: No CI/CD pipeline. Manual deploy.sh only. No testing.
- **Gap**: No automated deployment, testing, or contract verification.
- **Recommendation**: Create CI/CD pipeline with API contract tests.
- **Evidence**: `deploy.sh`, repository root (no CI/CD config)

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: Partial. App Runner built-in rollback. RDS snapshots. ECR immutable tags. No explicit rollback strategy.
- **Gap**: No automated rollback procedure.
- **Recommendation**: Document and test rollback procedure. Add to deploy.sh.
- **Evidence**: `infrastructure/monolith-apprunner.yaml` (ECR, RDS config), `deploy.sh`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: Zero test coverage. No test files, no test config, no test directories anywhere in repository.
- **Gap**: No automated API testing. Changes can break agent APIs undetected.
- **Recommendation**: Create PHPUnit test suite for API endpoints.
- **Evidence**: Repository root (no test files)

#### ENG-Q5: Encryption at Rest
- **Severity**: INFO
- **Finding**: Well-configured. RDS StorageEncrypted: true. ECR with customer-managed KMS (EnableKeyRotation: true). VPC Flow Logs with KMS encryption.
- **Gap**: No gap — encryption is properly configured. RDS uses AWS-managed key (minor improvement opportunity).
- **Recommendation**: Consider customer-managed KMS key for RDS.
- **Evidence**: `infrastructure/monolith-apprunner.yaml` (encryption configs)

## Evidence Index

### Infrastructure as Code
| File | Questions Referenced |
|------|---------------------|
| `infrastructure/monolith-apprunner.yaml` | AUTH-Q1, AUTH-Q2, AUTH-Q5, AUTH-Q6, AUTH-Q7, STATE-Q5, STATE-Q7, DATA-Q1, DATA-Q2, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q3, ENG-Q5, API-Q8 |

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `index.php` | API-Q1, API-Q2, API-Q3, API-Q4, API-Q5, API-Q7, API-Q8, AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q2, STATE-Q3, STATE-Q5, STATE-Q6, HITL-Q1, HITL-Q2, HITL-Q3, DATA-Q1, DATA-Q2, DATA-Q3, DATA-Q4, DATA-Q5, DATA-Q6, DATA-Q7, DISC-Q1, DISC-Q2, DISC-Q3, OBS-Q1, OBS-Q3, ENG-Q4 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `Dockerfile` | AUTH-Q1 (deployment context) |
| `docker-compose.yml` | AUTH-Q5, HITL-Q3 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `.htaccess` | API-Q1 (URL rewriting) |
| `deploy.sh` | ENG-Q2, ENG-Q3 |

### Notable Absences (Absence as Evidence)
| Expected Artifact | Questions Affected |
|-------------------|-------------------|
| No OpenAPI/Swagger specification | API-Q2 |
| No CI/CD pipeline configuration | ENG-Q2, ENG-Q4 |
| No test files or test configuration | ENG-Q4 |
| No CloudTrail configuration | AUTH-Q6 |
| No Secrets Manager integration | AUTH-Q5 |
| No data classification documentation | DATA-Q1 |
| No data residency documentation | DATA-Q2 |
| No data catalog or data dictionary | DISC-Q3 |
| No migration system | DISC-Q1 |
| No CloudWatch alarms | OBS-Q2 |
| No distributed tracing instrumentation | OBS-Q1 |
| No staging/sandbox environment configuration | HITL-Q3 |

---

*End of Agentic Readiness Assessment Report*
