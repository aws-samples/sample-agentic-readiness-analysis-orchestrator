# Agentic Readiness Assessment Report

**Target**: ./monolith
**Date**: 2026-04-15
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Agent Scope**: write-enabled
**Priority**: P0
**Tags**: monolith, php, containers
**Context**: PHP monolith with Docker and CloudFormation on App Runner — containerize and expose inventory APIs the agent needs for restocking decisions.

---

## Readiness Profile: Not Agent-Integrable

**BLOCKERs**: 7 | **RISKs**: 33 | **INFOs**: 9

Exclude from agent toolset or plan major remediation before re-evaluation. With 7 open BLOCKERs spanning authentication, data safety, transactional integrity, idempotency, audit compliance, and network security, this application cannot safely support autonomous agent operations — including supervised pilots. A structured remediation program (estimated 120–180 days) is required before re-assessment.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 7 |
| RISK | 33 |
| INFO | 9 |
| N/A | 0 |
| **Total** | **49** |

**Questions Evaluated**: 49
**Questions N/A (repo_type: application)**: 0

## BLOCKERs — Must Resolve Before Agent Deployment

**Remediation Prioritization:** Resolve AUTH-Q1 (machine identity) first — it is the fastest to address (add API key auth) and unblocks all other auth and audit controls. Then address DATA-Q1 (data classification) and DATA-Q2 (data residency) together. Then tackle API-Q4 (idempotency), STATE-Q1 (compensation), AUTH-Q7 (audit logging), and ENG-Q6 (network policies). Consider scoping an initial agent to read-only operations while write-safety blockers (API-Q4, STATE-Q1) are remediated.

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: BLOCKER
- **Conditional**: agent_scope is "write-enabled" — evaluated as BLOCKER
- **Finding**: Write endpoints (`POST /api/orders`, `POST /api/orders/{id}/validate`, `POST /api/orders/{id}/assign-warehouse`, `POST /api/orders/{id}/pick`, `POST /api/orders/{id}/pack`, `POST /api/orders/{id}/quality-check`, `POST /api/orders/{id}/ship`, `POST /api/orders/{id}/deliver`, `POST /api/returns`, `POST /api/admin/approve-return`) do not accept or enforce idempotency keys. Order IDs are generated via `uniqid('order-')` which produces time-based unique IDs with no business-key deduplication. The `POST /api/orders` endpoint creates a new order on every call with no duplicate detection.
- **Gap**: No idempotency key support on any write endpoint. No unique constraint on business keys for order creation. No idempotency middleware or decorators. An agent retrying a failed `POST /api/orders` call will create duplicate orders.
- **Remediation**:
  - **Immediate**: Add an `Idempotency-Key` header to the `POST /api/orders` endpoint. Store the key in a deduplication table and check before processing. Return the cached response for duplicate keys.
  - **Target State**: All write endpoints accept and enforce idempotency keys. Duplicate requests return the original response without re-executing side effects.
  - **Estimated Effort**: Medium
  - **Dependencies**: None
- **Evidence**: `index.php` — `POST /api/orders` handler (line ~170), `uniqid('order-')` ID generation, no idempotency checks on any POST endpoint.

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: Authentication is exclusively session-based using PHP `session_start()` with username/password login via `POST /login`. All API endpoints check `$_SESSION['user']` and return 401 if no session exists. There is no OAuth2 client credentials flow, no API key authentication, no mTLS, and no service account mechanism. The system has no concept of machine identity — it only recognizes human users authenticated via browser sessions.
- **Gap**: No machine identity authentication mechanism exists. Agents cannot obtain a session without simulating a browser login form submission, which is UI automation (the integration anti-pattern). There is no way to attribute API calls to a specific agent principal.
- **Remediation**:
  - **Immediate**: Implement API key authentication as an alternative auth path. Add an `Authorization: Bearer <api-key>` check before the session check in the API route handler. Store API keys in the `users` table with a `key_type` field distinguishing agent vs human principals.
  - **Target State**: OAuth2 client credentials flow with Cognito or API Gateway authorizer. Each agent has a unique client ID with principal attribution in audit logs.
  - **Estimated Effort**: Medium
  - **Dependencies**: AUTH-Q7 (audit logging must record the authenticated agent principal)
- **Evidence**: `index.php` — `session_start()`, `$_SESSION['user']` check in API route handler, `POST /login` form-based authentication, no `Authorization` header parsing.

### AUTH-Q7: Immutable Audit Logging ⚡

- **Severity**: BLOCKER
- **Conditional**: agent_scope is "write-enabled" — evaluated as BLOCKER
- **Finding**: The application has an `order_status_history` table that records status changes with a `changed_by` field. However, this is an application-level history table in the same mutable MySQL database — it is not an immutable audit log. Records can be modified or deleted. There is no CloudTrail integration, no immutable log storage (e.g., S3 with Object Lock), no log file validation, and no tamper-evident logging mechanism. The `changed_by` field records usernames (e.g., 'system', `$_SESSION['user']['username']`) but has no concept of agent identity.
- **Gap**: No immutable, tamper-evident audit log. The `order_status_history` table is mutable and lives in the same database as business data. No external audit trail service. No compliance-grade logging for write operations.
- **Remediation**:
  - **Immediate**: Enable CloudTrail for the AWS account (if deploying to AWS). Configure an S3 bucket with Object Lock for log storage. Enable CloudTrail log file validation.
  - **Target State**: All write operations logged to an immutable, tamper-evident audit trail (CloudTrail + S3 Object Lock or CloudWatch Logs with retention policy). Each log entry includes the authenticated principal (human or agent), the action performed, the resource affected, and a timestamp.
  - **Estimated Effort**: Medium
  - **Dependencies**: AUTH-Q1 (machine identity must exist before agent actions can be attributed in audit logs)
- **Evidence**: `index.php` — `order_status_history` table schema, `update_order_status()` function with `changed_by` parameter, no CloudTrail or immutable log references.

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: BLOCKER
- **Conditional**: agent_scope is "write-enabled" — evaluated as BLOCKER
- **Finding**: The application uses database transactions (`beginTransaction`/`commit`/`rollBack`) for individual operations like order creation and return approval. However, the multi-step fulfillment workflow (confirmed → validated → warehouse_assigned → picking → packed → quality_checked → shipped) consists of separate API calls, each committing independently. If an agent executes steps 1–4 and step 5 fails, there is no saga pattern, no compensation logic, and no mechanism to undo the previously committed steps. The `assign-warehouse` endpoint increments `warehouses.current_load` with no compensating decrement on failure.
- **Gap**: No saga pattern. No compensation endpoints (e.g., `POST /api/orders/{id}/undo-warehouse-assignment`). No rollback mechanism for the multi-step fulfillment workflow. Partial state corruption is possible if agent workflows fail mid-sequence.
- **Remediation**:
  - **Immediate**: Implement compensation endpoints for each fulfillment step (e.g., reverse warehouse assignment, reverse pick status). Add a workflow state machine that tracks completed steps and can trigger compensating actions on failure.
  - **Target State**: Saga pattern with compensating transactions for each step, or Step Functions orchestration with error handling and rollback states.
  - **Estimated Effort**: High
  - **Dependencies**: None
- **Evidence**: `index.php` — `POST /api/orders/{id}/assign-warehouse` commits warehouse load increment with no undo, each fulfillment step is a separate committed transaction, no saga or compensation pattern.

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: The application stores PII including `customer_name`, `customer_email`, `shipping_address` (in the `orders` table), and `password` (in the `users` table). Passwords are hashed with bcrypt (`password_hash($data['password'], PASSWORD_BCRYPT)`), but all other PII fields are stored as plaintext with no field-level encryption, no classification tags, and no access controls beyond the coarse-grained admin/customer role check. There are no data classification policies, no AWS Macie integration, and no field-level access restrictions. API responses for orders include full PII (customer name, email, shipping address) with no redaction.
- **Gap**: No field-level data classification. No PII tagging or labeling. No field-level encryption for PII. No access controls preventing an agent from retrieving customer PII without explicit authorization. An agent with read access to the orders API retrieves all customer PII by default.
- **Remediation**:
  - **Immediate**: Classify PII fields in the database schema (customer_name, customer_email, shipping_address, password). Implement field-level redaction in API responses — return masked PII by default and require an explicit scope/claim to access full PII.
  - **Target State**: All PII fields classified and tagged at the schema level. Field-level encryption (AWS KMS) for high-sensitivity fields. API responses include only the PII necessary for the agent's scoped task. AWS Macie scanning for PII detection.
  - **Estimated Effort**: High
  - **Dependencies**: AUTH-Q1 (agent identity must exist to enforce per-agent PII access controls)
- **Evidence**: `index.php` — `orders` table schema with `customer_name VARCHAR(255)`, `customer_email VARCHAR(255)`, `shipping_address TEXT`; `users` table with `password VARCHAR(255)`; API responses include full PII in JSON output.

### DATA-Q2: Data Residency and Sovereignty ⚡

- **Severity**: BLOCKER
- **Conditional**: agent_scope is "write-enabled" — evaluated as BLOCKER
- **Finding**: The application stores customer PII (names, emails, shipping addresses including full street addresses with city, state, and ZIP) and financial data (order amounts, payment records) with no data residency or sovereignty configuration. There are no region-specific data storage configurations, no GDPR or LGPD compliance references, no cross-region replication policies, and no data sovereignty controls. The `docker-compose.yml` deploys MySQL with no region awareness. A write-enabled agent transmitting customer PII and shipping addresses to an LLM provider in a different jurisdiction creates potential legal exposure.
- **Gap**: No data residency policy. No region-specific deployment configuration. No data sovereignty controls. No documentation of which data fields are subject to residency requirements. A write-enabled agent sending customer shipping addresses (with full street, city, state, ZIP) to an LLM endpoint in another region may create a compliance violation.
- **Remediation**:
  - **Immediate**: Document which data fields are subject to residency requirements. Identify the jurisdictions of LLM endpoints the agent will use. Implement a data residency policy that specifies where PII can be transmitted.
  - **Target State**: Data residency policy documented and enforced. LLM endpoints deployed in the same region as data storage. PII redacted or anonymized before transmission to LLM providers. AWS region-specific deployment via IaC.
  - **Estimated Effort**: Medium
  - **Dependencies**: DATA-Q1 (data classification must exist before residency controls can be applied per field)
- **Evidence**: `index.php` — `orders` table stores `customer_name`, `customer_email`, `shipping_address`; `docker-compose.yml` has no region configuration; no GDPR/LGPD references in any file.

### ENG-Q6: Cross-Origin and Network Policies

- **Severity**: BLOCKER
- **Finding**: There is no CORS configuration in the application code (`index.php` does not set `Access-Control-Allow-Origin` or other CORS headers) or in any infrastructure configuration. There are no security group rules, no firewall rules, no API Gateway access policies, no WAF rules, and no network policies. The application is exposed on port 8080 via `docker-compose.yml` with no network security layer. The `docker-compose.yml` uses `security_opt: no-new-privileges` and `read_only: true` (good container hardening), but there is no network-level security configuration. No IaC exists to define security groups or network ACLs.
- **Gap**: No CORS policy defined. No network security configuration documented or discoverable. No API Gateway, no WAF, no security groups, no firewall rules. An agent running on a cloud platform will have no documented network path to this service. Additionally, the absence of CORS means browser-based agent UIs cannot interact with the API from different origins.
- **Remediation**:
  - **Immediate**: Add CORS headers to the PHP API handler (`Access-Control-Allow-Origin`, `Access-Control-Allow-Methods`, `Access-Control-Allow-Headers`). Document the intended network topology.
  - **Target State**: API Gateway with WAF in front of the application. Security groups defined in IaC (Terraform/CloudFormation). CORS policy configured at the API Gateway level. Network policies documented and enforced.
  - **Estimated Effort**: Medium
  - **Dependencies**: ENG-Q1 (IaC governance should define the network security infrastructure)
- **Evidence**: `index.php` — no CORS headers set; `docker-compose.yml` — port 8080 exposed with no network security; no IaC files defining security groups or WAF; no `.tf`, `.cfn.yaml`, or CDK files in repository.

## RISKs — Proceed with Compensating Controls

### API-Q1: Documented API Interface

- **Severity**: RISK
- **Finding**: The application exposes REST-like endpoints under the `/api/` prefix returning JSON responses. Endpoints include `GET /api/products`, `POST /api/orders`, `GET /api/orders/me`, and a full fulfillment workflow (`/api/orders/{id}/validate`, `/api/orders/{id}/assign-warehouse`, etc.). However, the API is gated behind PHP session-based authentication — agents cannot consume it without first simulating a browser login. There is no formal API documentation beyond the code itself.
- **Gap**: REST endpoints exist but are not directly consumable by agents due to session-based auth. No formal API documentation. Integration does not require direct database access or UI automation, but the session requirement is a significant barrier.
- **Compensating Controls**:
  - Implement API key auth (resolves AUTH-Q1 blocker) to make the REST endpoints agent-consumable
  - Generate an OpenAPI spec from the existing route definitions to document the API surface
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Once AUTH-Q1 (machine identity) is resolved, these REST endpoints become directly consumable. Generate an OpenAPI spec to formalize the interface.
- **Evidence**: `index.php` — `if (strpos($request_uri, '/api/') === 0)` route handler, `header('Content-Type: application/json')`, `json_encode()` responses, session check `if (!isset($_SESSION['user']))`.

### API-Q2: Machine-Readable API Specification

- **Severity**: RISK
- **Finding**: No OpenAPI, AsyncAPI, GraphQL schema, Smithy, or any other machine-readable API specification file exists in the repository. The API surface is defined only in PHP code via `preg_match` patterns in `index.php`. There are no API documentation files, no Swagger UI, and no auto-generation from annotations.
- **Gap**: No machine-readable spec. Agent tool definitions must be manually authored from code inspection, which will drift from actual behavior as the code changes.
- **Compensating Controls**:
  - Manually author tool definitions from code analysis for the initial pilot
  - Use API recording/proxy tools to capture request/response pairs and generate a spec
- **Remediation Timeline**: 30 days
- **Recommendation**: Generate an OpenAPI 3.0 specification from the existing route definitions. Consider using PHP annotations (e.g., swagger-php) to keep the spec in sync with code.
- **Evidence**: No `openapi.yaml`, `openapi.json`, `swagger.yaml`, `swagger.json`, `*.graphql`, `*.gql`, or `*.smithy` files found in repository.

### API-Q3: Structured Error Responses

- **Severity**: RISK
- **Finding**: Error responses use `json_encode(['error' => $e->getMessage()])` with appropriate HTTP status codes (400, 401, 403, 404, 500). However, the error format is inconsistent — some return `{'error': 'message'}`, others return `{'success': false, 'message': 'text'}`. There are no structured error codes, no retryable boolean, no error categories, and no machine-readable error classification.
- **Gap**: No structured error code enum. No `retryable` field. No consistent error body format. Agents cannot distinguish between retriable errors (server overload) and terminal errors (invalid input) without parsing error message text.
- **Compensating Controls**:
  - Map known HTTP status codes to retry behavior in the agent tool definition (e.g., 500 → retry, 400 → do not retry)
  - Implement a thin error-mapping middleware before the agent
- **Remediation Timeline**: 30 days
- **Recommendation**: Standardize all error responses to `{"error": {"code": "ORDER_NOT_FOUND", "message": "...", "retryable": false}}`. Use a consistent error code enum.
- **Evidence**: `index.php` — `json_encode(['error' => $e->getMessage()])` pattern in catch blocks, `json_encode(['error' => 'Unauthorized'])` for 401, `json_encode(['error' => 'Order not found'])` for 404.

### API-Q5: API Versioning and Deprecation

- **Severity**: RISK
- **Finding**: No API versioning exists. Endpoints are unversioned (`/api/products`, not `/api/v1/products`). No `Accept-Version` headers. No changelog. No deprecation policy or downstream notification mechanism.
- **Gap**: Any API change is a breaking change with no versioning buffer. Agent tool definitions will break silently when endpoints change behavior.
- **Compensating Controls**:
  - Freeze the current API surface during initial agent integration
  - Add contract tests (ENG-Q2) to detect breaking changes before deployment
- **Remediation Timeline**: 60 days
- **Recommendation**: Add URL-based versioning (`/api/v1/`) to all endpoints. Implement a deprecation policy with minimum 90-day notice and sunset headers.
- **Evidence**: `index.php` — all routes use `/api/` prefix with no version segment; no changelog files in repository.

### API-Q7: Asynchronous Operation Support

- **Severity**: RISK
- **Finding**: All API endpoints are synchronous request/response. The multi-step fulfillment workflow (validate → assign-warehouse → pick → pack → quality-check → ship) is executed as sequential synchronous calls. No background job frameworks (Celery, Bull, SQS workers), no async/polling patterns, no job status APIs, and no webhook callback endpoints exist.
- **Gap**: No async pattern for long-running operations. If warehouse assignment or shipping label generation takes more than 30 seconds in a production environment, agents will time out.
- **Compensating Controls**:
  - Set generous timeouts on agent HTTP clients for the initial pilot
  - Monitor actual response times and implement async only for operations exceeding 5s
- **Remediation Timeline**: 60–90 days
- **Recommendation**: For operations that may exceed 30 seconds in production (warehouse assignment with external API calls, shipping label generation), implement a job submission + polling pattern: return a `202 Accepted` with a job ID, and provide a `GET /api/jobs/{id}` status endpoint.
- **Evidence**: `index.php` — all route handlers execute synchronously, no background job or queue references, no polling endpoints.

### AUTH-Q2: Scoped Permissions (Least Privilege)

- **Severity**: RISK
- **Finding**: Authorization uses a coarse-grained role model with two roles: `admin` and `customer`. Role checks are performed via `$_SESSION['user']['role']`. Admin role has full access to all admin endpoints. Customer role is restricted from admin endpoints. There are no IAM policies, no API Gateway resource policies, no condition keys, and no resource-level permission scoping.
- **Gap**: No fine-grained scoping. An agent identity would need to be either admin (full access to all operations) or customer (limited to customer-facing operations). No mechanism to grant an agent read-only access to inventory without also granting order creation ability within the customer role.
- **Compensating Controls**:
  - Create a dedicated "agent" role with only the specific permissions needed for inventory restocking decisions
  - Restrict the agent to specific endpoints at the API Gateway level
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement a fine-grained RBAC model with permissions per endpoint (e.g., `inventory:read`, `orders:write`, `fulfillment:execute`). Create dedicated agent roles with least-privilege scoping.
- **Evidence**: `index.php` — `$_SESSION['user']['role'] !== 'admin'` checks, only two roles in `users` table (`admin`, `customer`), no permission matrix.

### AUTH-Q3: Action-Level Authorization

- **Severity**: RISK
- **Finding**: The application does not enforce action-level authorization. Within the admin role, all admin endpoints are accessible — there is no mechanism to allow an agent to read orders but not delete users, or to assign warehouses but not approve returns. Within the customer role, all customer endpoints are accessible uniformly.
- **Gap**: No ABAC policies. No fine-grained RBAC with action-level checks. No permission checks like `canRead`, `canWrite`, `canDelete` in middleware.
- **Compensating Controls**:
  - Restrict the agent's accessible endpoints at the API Gateway or reverse proxy level
  - Implement an application-level middleware that checks a permissions array for the agent's identity
- **Remediation Timeline**: 60 days
- **Recommendation**: Add action-level permission checks: for each API endpoint, check the authenticated principal's permissions array rather than just role. Example: `['orders:read', 'inventory:read', 'warehouse:assign']`.
- **Evidence**: `index.php` — admin endpoints check `$_SESSION['user']['role'] !== 'admin'` but not per-action permissions; no middleware for action-level auth.

### AUTH-Q4: Identity Propagation

- **Severity**: RISK
- **Finding**: The application is a monolith with no service-to-service calls, so identity propagation is not currently needed. User context is maintained in the PHP session (`$_SESSION['user']`). However, there is no JWT/OAuth token exchange, no on-behalf-of flows, and no mechanism to carry originating user context through external service calls if the application were to be decomposed.
- **Gap**: No technical identity propagation mechanism. If the monolith calls external services (e.g., shipping carrier APIs, payment processors), the originating user context is not passed through.
- **Compensating Controls**:
  - For the initial pilot, the monolith's single-process architecture means user context is inherently available
  - Log the originating user in all operations to maintain traceability
- **Remediation Timeline**: 60–90 days (becomes critical during decomposition)
- **Recommendation**: Implement JWT-based identity propagation. When an agent calls the API on behalf of a user, pass a JWT that includes the originating user's identity. The application validates the JWT and applies the user's permissions.
- **Evidence**: `index.php` — `$_SESSION['user']` for user context, no JWT parsing, no `Authorization: Bearer` header handling, no token exchange logic.

### AUTH-Q5: Agent-as-Self vs Agent-on-Behalf-of-User

- **Severity**: RISK
- **Finding**: The system has no concept of agent identity and cannot distinguish between an agent acting under its own service identity and an agent acting on behalf of a specific human user. The only identity model is session-based human users with two roles (admin, customer). There are no separate auth flows for service-to-service vs user-delegated calls.
- **Gap**: No distinction between agent-as-self and agent-on-behalf-of-user. No separate IAM roles or API keys for these two modes. No audit log fields distinguishing them.
- **Compensating Controls**:
  - For the initial pilot, restrict the agent to agent-as-self mode with a dedicated service account
  - Log all actions as agent-initiated to maintain a clear audit trail
- **Remediation Timeline**: 60 days
- **Recommendation**: Implement two auth flows: (1) agent-as-self using client credentials with a dedicated agent service account, (2) agent-on-behalf-of-user using token exchange (OAuth2 on-behalf-of flow) that carries the user's identity. Audit logs must record which mode was used.
- **Evidence**: `index.php` — only `$_SESSION['user']` identity model, no service account concept, no agent identity fields in `order_status_history.changed_by`.

### AUTH-Q6: Credential Management

- **Severity**: RISK
- **Finding**: Database credentials are configured via environment variables in `docker-compose.yml` (`DB_PASS` from `MYSQL_PASSWORD`). However, `index.php` contains a hardcoded fallback: `getenv('DB_PASS') ?: 'ecommerce_pass'`, meaning if the environment variable is not set, the application falls back to a default plaintext password. No AWS Secrets Manager, HashiCorp Vault, or any secrets management system is used. The `docker-compose.yml` uses variable substitution with `${MYSQL_PASSWORD:?Set MYSQL_PASSWORD}` (good — requires the env var), but the PHP fallback undermines this.
- **Gap**: Hardcoded credential fallback in application code. No secrets management system. No secret rotation. Credential compromise would require manual intervention to rotate.
- **Compensating Controls**:
  - Remove the hardcoded fallback password immediately
  - Use Docker secrets or environment-specific `.env` files with restricted permissions
- **Remediation Timeline**: 30 days
- **Recommendation**: Remove the hardcoded password fallback from `index.php`. Integrate AWS Secrets Manager for all credentials. Implement automatic secret rotation with a rotation Lambda. Ensure the application retrieves credentials from Secrets Manager at startup.
- **Evidence**: `index.php` — `getenv('DB_PASS') ?: 'ecommerce_pass'` hardcoded fallback; `docker-compose.yml` — `MYSQL_PASSWORD` environment variable; no Secrets Manager or Vault references.

### AUTH-Q8: Agent Identity Suspension

- **Severity**: RISK
- **Finding**: There is no mechanism to suspend or revoke an individual agent identity. The application has no API key management, no service account disable functionality, no Cognito user pool integration, and no IAM role deactivation procedures. Users can be deleted via `DELETE /api/admin/users/{id}`, but this is a destructive action, not a suspension. There is no "disable" flag on user accounts.
- **Gap**: No immediate suspension mechanism for a misbehaving agent. The only option is to delete the user account, which is irreversible and loses audit history. No API key revocation.
- **Compensating Controls**:
  - Add an `active` boolean field to the users table for suspension without deletion
  - Implement IP-based blocking at the reverse proxy level as an emergency kill switch
- **Remediation Timeline**: 30 days
- **Recommendation**: Add an `is_active` field to the `users` table. Check this field during authentication. Implement an admin endpoint to suspend/reactivate agent identities without deletion. For API key auth (once implemented), add key revocation.
- **Evidence**: `index.php` — `DELETE /api/admin/users/{id}` only option to remove access, no `is_active` field in users table, no suspension mechanism.

### STATE-Q2: Queryable Current State

- **Severity**: RISK
- **Finding**: Partial queryable state exists. `GET /api/products` returns inventory with stock quantities. `GET /api/orders/me` returns customer orders with status. `GET /api/orders/{id}/history` returns order status history. `GET /api/admin/orders/pending-fulfillment` returns orders in fulfillment. However, there is no general-purpose order lookup by ID (only customer-scoped), no inventory query by product ID, and no warehouse state endpoint for current load.
- **Gap**: Incomplete queryable state. An agent cannot query a specific order by ID without a customer session. No inventory-level query for a single product. No real-time warehouse capacity endpoint beyond what's embedded in the assignment-options response.
- **Compensating Controls**:
  - Add `GET /api/orders/{id}` and `GET /api/products/{id}` endpoints for targeted queries
  - Use the existing `GET /api/warehouses/assignment-options` to infer warehouse state
- **Remediation Timeline**: 30 days
- **Recommendation**: Add resource-level GET endpoints (`GET /api/orders/{id}`, `GET /api/products/{id}`, `GET /api/warehouses/{id}`) with appropriate authorization. Ensure agents can inspect current state before taking action.
- **Evidence**: `index.php` — `GET /api/products` (all products), `GET /api/orders/me` (customer-scoped), `GET /api/admin/orders/pending-fulfillment` (admin-scoped), no `GET /api/orders/{id}` endpoint.

### STATE-Q3: Concurrency Controls

- **Severity**: RISK
- **Finding**: No optimistic locking or concurrency controls exist. The inventory decrement in the order creation handler uses `UPDATE inventory SET stock_quantity = stock_quantity - ? WHERE product_id = ?` — this is a blind decrement with no version check, no ETag, no `If-Match` header, and no conditional update. Multiple concurrent agent instances could race on the same inventory item, potentially decrementing stock below zero (though the pre-check `if ($product['stock_quantity'] < $item['quantity'])` is non-atomic with the update).
- **Gap**: No optimistic locking (no version fields, no ETags). No pessimistic locking (`SELECT FOR UPDATE` not used). Race condition between stock check and stock decrement in order creation. DynamoDB conditional writes not applicable (MySQL only).
- **Compensating Controls**:
  - Add `FOR UPDATE` to the inventory SELECT during order creation to serialize concurrent access
  - Add a `version` column to frequently modified tables for optimistic locking
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement optimistic locking with a `version` column on the `inventory` and `orders` tables. Use `UPDATE ... WHERE version = ?` and return a 409 Conflict if the version has changed. Add `ETag` response headers for GET endpoints.
- **Evidence**: `index.php` — `UPDATE inventory SET stock_quantity = stock_quantity - ?` without version check, no `SELECT FOR UPDATE`, no ETag headers.

### STATE-Q4: Circuit Breakers and Resilience

- **Severity**: RISK
- **Finding**: No circuit breakers, retry logic, or resilience patterns exist. The monolith has a direct dependency on MySQL with no fallback. If the database becomes slow or unreachable, all requests fail with unhandled PDO exceptions. The `get_db()` function calls `die()` on connection failure — terminating the PHP process.
- **Gap**: No circuit breaker pattern. No retry logic with exponential backoff. No timeout configuration on database connections. No fallback for database unavailability. The `die()` call on DB failure provides no structured error response to the agent.
- **Compensating Controls**:
  - Configure MySQL connection timeouts in the PDO connection string
  - Add a health check endpoint that agents can query before initiating workflows
- **Remediation Timeline**: 60 days
- **Recommendation**: Replace `die()` with structured error responses. Add connection timeout and retry logic to `get_db()`. Implement a circuit breaker pattern that opens after N consecutive failures and returns a structured 503 response.
- **Evidence**: `index.php` — `die("Database connection failed: " . $e->getMessage())` in `get_db()`, no retry logic, no circuit breaker, no timeout configuration.

### STATE-Q5: Rate Limiting and Throttling

- **Severity**: RISK
- **Finding**: No rate limiting exists at any layer. There is no API Gateway, no WAF rate rules, and no application-level rate limiting middleware. The application directly accepts all requests from port 8080. A runaway agent loop could send unlimited requests at machine speed.
- **Gap**: No rate limiting. No throttling. No `X-RateLimit-Remaining` headers. No usage plans. A misbehaving agent or retry loop can overwhelm the single-instance application.
- **Compensating Controls**:
  - Deploy an nginx reverse proxy with `limit_req_zone` rate limiting in front of the application
  - Implement per-agent rate limits at the agent orchestration layer
- **Remediation Timeline**: 30 days
- **Recommendation**: Deploy API Gateway in front of the application with throttling configuration and usage plans per agent identity. As an interim measure, add application-level rate limiting middleware that tracks requests per session/API key per time window.
- **Evidence**: `docker-compose.yml` — `ports: "8080:80"` with no rate limiting layer; `index.php` — no rate limiting checks; no API Gateway or WAF configuration files.

### STATE-Q6: Blast Radius and Transaction Limits

- **Severity**: RISK
- **Finding**: No configurable transaction limits exist. There are no maximum records per operation, no spend limits per hour, no maximum delete operations per session, and no blast radius controls. The `POST /api/orders` endpoint accepts any number of items with any total amount. The `DELETE /api/admin/users/{id}` endpoint has no batch protection. The `POST /api/admin/approve-return` endpoint processes refunds of any amount.
- **Gap**: No per-agent transaction limits. No spend caps. No bulk operation limits. An agent error could issue unlimited refunds, create unlimited orders, or delete all users.
- **Compensating Controls**:
  - Implement transaction limits in the agent orchestration layer (e.g., max 10 orders per hour, max $1000 in refunds per session)
  - Add approval gates for operations exceeding configurable thresholds
- **Remediation Timeline**: 60 days
- **Recommendation**: Add configurable per-identity limits: `max_orders_per_hour`, `max_refund_amount_per_day`, `max_bulk_operations_per_call`. Store limits per agent identity and check before executing operations.
- **Evidence**: `index.php` — `POST /api/orders` accepts unlimited items/amount, `POST /api/admin/approve-return` processes any refund amount, no limit checks in any endpoint.

### STATE-Q7: Infrastructure Capacity for Agent Traffic

- **Severity**: RISK
- **Finding**: The application runs as a single Docker container via `docker-compose.yml` with no auto-scaling, no load balancing, and no capacity planning. The `Dockerfile` defines a single Apache process. There are no load test results, no capacity planning documentation, and no auto-scaling policies. The MySQL instance is also a single container with no read replicas.
- **Gap**: Single-instance deployment with no horizontal scaling. No load testing. No auto-scaling. Agent-generated traffic (concurrent API calls, retry loops) will hit the single instance's capacity ceiling quickly.
- **Compensating Controls**:
  - Add Apache worker configuration tuning for concurrent connections
  - Monitor container resource usage and add alerts for capacity thresholds
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Deploy on AWS App Runner or ECS with auto-scaling. Add an RDS MySQL instance with read replicas. Conduct load testing simulating agent traffic patterns (concurrent requests, retry bursts). Configure auto-scaling based on request latency and CPU utilization.
- **Evidence**: `docker-compose.yml` — single `monolith` service, single `mysql` service, no replicas, no scaling configuration; `Dockerfile` — single Apache instance; no load test results in repository.

### HITL-Q1: Draft/Pending State

- **Severity**: RISK
- **Finding**: The application has partial draft/pending state support. The fulfillment workflow uses a multi-step status chain (confirmed → validated → warehouse_assigned → picking → packed → quality_checked → shipped → delivered). Returns use a `pending_review` status that requires explicit admin approval before processing. These are conceptually similar to draft states — the order exists but is not finalized until the next step is completed.
- **Gap**: The status transitions are hardcoded — there is no general-purpose "draft" state that agents can write to before human approval. The fulfillment workflow steps auto-commit; they do not wait for human confirmation. Only the return approval flow has a true pending-approval pattern.
- **Compensating Controls**:
  - For the initial pilot, restrict agents to proposing fulfillment actions (recording recommendations) rather than executing them directly
  - Use the existing return approval pattern as a template for adding approval gates to other workflows
- **Remediation Timeline**: 60 days
- **Recommendation**: Add a `proposed` status to the fulfillment workflow where the agent records a recommended action (e.g., recommended warehouse, recommended carrier) and a human approves before execution.
- **Evidence**: `index.php` — `pending_review` status for returns, status transitions in fulfillment workflow, `POST /api/admin/approve-return` approval endpoint.

### HITL-Q2: Configurable Approval Gates

- **Severity**: RISK
- **Finding**: The return approval workflow (`POST /api/admin/approve-return`) requires explicit human action. The fulfillment workflow steps (validate, assign-warehouse, pick, pack, quality-check, ship) each require an API call to advance — conceptually, each is a manual step. However, these are not configurable approval gates — they are hardcoded workflow steps with no mechanism to add or remove approval requirements per operation type.
- **Gap**: No configurable approval gates. Cannot dynamically require human approval for specific operations (e.g., require approval for orders over $500 but auto-approve orders under $100). No Step Functions with `waitForTaskToken`.
- **Compensating Controls**:
  - Implement approval logic in the agent orchestration layer (e.g., "if order total > $500, request human approval before calling ship endpoint")
  - Use the existing multi-step workflow structure as approval checkpoints
- **Remediation Timeline**: 60 days
- **Recommendation**: Add a configurable approval gate system: define rules (e.g., `{action: 'ship', condition: 'total_amount > 500', requires_approval: true}`) and check them before executing operations. Use Step Functions with human approval tasks for high-value operations.
- **Evidence**: `index.php` — `POST /api/admin/approve-return` hardcoded approval, fulfillment steps are sequential API calls with no configurable gates.

### HITL-Q3: Sandbox/Staging Environment

- **Severity**: RISK
- **Finding**: `docker-compose.yml` provides a local development environment with MySQL and the monolith service. The `seed_data()` function in `index.php` creates sample data (2 users, 5 products, 3 warehouses, 1 sample order). However, there is no separate staging or sandbox environment configuration, no environment-specific IaC, no synthetic data generator, and no production-equivalent data shape.
- **Gap**: No staging or sandbox environment. The local Docker environment is the only non-production environment. No mechanism to test agents against realistic data without risking live systems. The seed data is minimal (5 products, 1 order) and does not represent production scale.
- **Compensating Controls**:
  - Use the existing docker-compose environment with enhanced seed data for agent testing
  - Create a separate docker-compose file (e.g., `docker-compose.staging.yml`) with production-scale seed data
- **Remediation Timeline**: 30 days
- **Recommendation**: Create a staging environment with production-equivalent data shape (hundreds of orders, diverse fulfillment statuses, multiple concurrent workflows). Use a synthetic data generator to populate the staging database. Deploy the staging environment on the same infrastructure (App Runner) as production to match behavior.
- **Evidence**: `docker-compose.yml` — single environment configuration; `index.php` — `seed_data()` function with 5 products and 1 order; no `docker-compose.staging.yml` or environment-specific files.

### DATA-Q3: Selective Query Support

- **Severity**: RISK
- **Finding**: No pagination, filtering, or sorting is implemented on API endpoints. `GET /api/products` executes `SELECT * FROM inventory` and returns all products. `GET /api/orders/me` executes `SELECT * FROM orders WHERE customer_id = ? ORDER BY created_at DESC` and returns all customer orders. No `limit`, `offset`, `cursor`, `page`, `filter`, or `sort` query parameters are accepted.
- **Gap**: No pagination. No filtering. No result size limits. An agent retrieving all orders or products will exhaust LLM context windows and increase costs as data grows.
- **Compensating Controls**:
  - Limit the number of records processed by the agent at the orchestration layer
  - Pre-filter data in the agent tool definition (e.g., only retrieve orders with specific statuses)
- **Remediation Timeline**: 30 days
- **Recommendation**: Add `limit`, `offset`, and `filter` query parameters to all list endpoints. Default `limit` to 50 with a maximum of 200. Add cursor-based pagination for large result sets.
- **Evidence**: `index.php` — `SELECT * FROM inventory` with no LIMIT, `SELECT * FROM orders WHERE customer_id = ?` with no LIMIT; no pagination parameters in any route handler.

### DATA-Q4: System of Record Designations

- **Severity**: RISK
- **Finding**: The application uses a single shared MySQL database as the implicit system of record for all domains (orders, inventory, payments, returns, interactions, users, warehouses). There is no explicit system-of-record designation documented anywhere. No master data management process exists. No conflict resolution logic.
- **Gap**: No documented SoR designations. The shared database is the de facto SoR but this is undocumented. If the monolith is decomposed into microservices, ownership of shared tables will be ambiguous.
- **Compensating Controls**:
  - Document the current MySQL database as the authoritative SoR for all entities in the agent tool documentation
  - Establish clear ownership boundaries before any service decomposition
- **Remediation Timeline**: 30 days (documentation only)
- **Recommendation**: Document system-of-record designations for each entity: orders, inventory, payments, returns, users, warehouses. Specify which service will own each entity if the monolith is decomposed.
- **Evidence**: `index.php` — single `$db` connection used for all tables, all domains share the `ecommerce` MySQL database; no data ownership documentation.

### DATA-Q5: Reliable Timestamps

- **Severity**: RISK
- **Finding**: `created_at` and `updated_at` fields exist on orders, returns, interactions, and order_status_history tables. Timestamps are generated using PHP's `date('Y-m-d H:i:s')` which uses the server's default timezone — there is no explicit UTC configuration, no `date_default_timezone_set('UTC')` call, and no timezone storage. The `payments` table uses `transaction_date`. No `event_time` fields exist to distinguish event time from processing time.
- **Gap**: No explicit timezone handling. Timestamps depend on the server's local timezone which may vary across deployments. No UTC guarantee. No event-time vs processing-time distinction.
- **Compensating Controls**:
  - Set the PHP timezone to UTC in the Dockerfile or php.ini
  - Document that all timestamps are in the server's local timezone for agent tool definitions
- **Remediation Timeline**: 30 days
- **Recommendation**: Add `date_default_timezone_set('UTC')` at the top of `index.php`. Use MySQL's `UTC_TIMESTAMP()` for database operations. Store all timestamps in UTC and convert to local time only for display.
- **Evidence**: `index.php` — `date('Y-m-d H:i:s')` calls throughout, no `date_default_timezone_set()`, no UTC references.

### DATA-Q6: Data Freshness Signaling

- **Severity**: RISK
- **Finding**: No data freshness signaling exists. API responses include no `Cache-Control` headers, no `X-Data-Age` headers, no `last_refreshed` fields, and no consistency guarantees. All responses are served directly from MySQL queries — data is real-time from a single-node MySQL instance with no caching layer.
- **Gap**: No mechanism for agents to know whether returned data is current, stale, cached, or eventually consistent. If a caching layer is added later, agents will have no signal for data freshness.
- **Compensating Controls**:
  - For the initial pilot, document that all data is served directly from MySQL with no caching (strong consistency)
  - Add `Cache-Control: no-cache` headers to confirm data is always fresh
- **Remediation Timeline**: 30 days
- **Recommendation**: Add `Cache-Control: no-cache` and `X-Data-Source: primary` headers to API responses. If caching is added in the future, include `X-Data-Age` and `X-Consistency-Level` headers.
- **Evidence**: `index.php` — `header('Content-Type: application/json')` only header set, no `Cache-Control` or data freshness headers; all queries run directly against MySQL.

### DATA-Q7: PII Redaction in Logs

- **Severity**: RISK
- **Finding**: PHP error logging is enabled (`ini_set('log_errors', '1')`) and display errors are disabled (`ini_set('display_errors', '0')`). However, there is no PII scrubbing or log redaction. Exception messages (e.g., from PDOException) may contain query strings with PII. The `die("Database connection failed: " . $e->getMessage())` call exposes connection details in error output. No log scrubbing middleware, no PII masking libraries, and no CloudWatch log filters exist.
- **Gap**: No PII redaction in logs. Exception messages may contain PII from SQL queries. No log scrubbing or masking. If agent interactions are logged (which they must be per AUTH-Q7), PII in prompts/responses could leak into log storage.
- **Compensating Controls**:
  - Add a custom error handler that sanitizes exception messages before logging
  - Configure log retention policies to limit PII exposure window
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement a custom PHP error handler that redacts PII patterns (email, phone, address) from log messages. Use structured JSON logging with explicit field-level redaction rules. Integrate Amazon Macie to scan log storage for PII.
- **Evidence**: `index.php` — `ini_set('log_errors', '1')`, `die("Database connection failed: " . $e->getMessage())`, `json_encode(['error' => $e->getMessage()])` exposing raw exception text.

### DISC-Q1: Schema Documentation and Versioning

- **Severity**: RISK
- **Finding**: The database schema is defined in the `init_db()` function via inline `CREATE TABLE IF NOT EXISTS` SQL statements. There are no external schema files (no JSON Schema, no Avro, no Protobuf), no schema registry, no database migration framework (no Flyway, Liquibase, Laravel migrations, or Doctrine migrations), and no schema versioning. Schema changes are applied via `ALTER TABLE` statements wrapped in try/catch to handle "already exists" errors — a fragile, non-versioned approach.
- **Gap**: No versioned schema. No migration framework. Schema changes are ad-hoc and not tracked. Agent tool definitions that depend on specific field names or types will break silently if the schema changes.
- **Compensating Controls**:
  - Extract the current schema into a standalone SQL file as documentation
  - Implement a simple migration numbering system for tracking schema changes
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Adopt a database migration framework (e.g., Flyway, Liquibase, or PHP Phinx). Export the current schema as the baseline migration. Version all future schema changes as numbered migration files. Publish the schema definition for agent tool authors.
- **Evidence**: `index.php` — `init_db()` function with `CREATE TABLE IF NOT EXISTS` statements, `ALTER TABLE` wrapped in try/catch for ad-hoc changes, no migration files in repository.

### OBS-Q1: Distributed Tracing and Structured Logging

- **Severity**: RISK
- **Finding**: No distributed tracing exists — no AWS X-Ray, no OpenTelemetry, no `traceparent` header propagation. Logging uses PHP's built-in error logging (`ini_set('log_errors', '1')`) which produces unstructured text logs. There are no JSON-formatted logs, no correlation IDs, no `request_id` fields, and no trace ID propagation. When an agent-initiated request fails inside the application, there is no mechanism to trace the request through the system.
- **Gap**: No distributed tracing. No structured logging. No correlation IDs. Agent-initiated failures are not debuggable beyond basic PHP error logs. No way to correlate an agent's request with the application's internal processing.
- **Compensating Controls**:
  - Add a request ID middleware that generates and logs a UUID for each request
  - Include the request ID in API error responses for agent-side correlation
- **Remediation Timeline**: 60 days
- **Recommendation**: Implement structured JSON logging with a request ID for each API call. Add OpenTelemetry SDK for distributed tracing. Propagate `traceparent` headers. Send traces to AWS X-Ray. Include the trace ID in API response headers for agent-side correlation.
- **Evidence**: `index.php` — `ini_set('log_errors', '1')` only logging config, no JSON logging, no correlation IDs, no tracing SDK; `Dockerfile` — no tracing agent or SDK installed.

### OBS-Q2: Alerting on Error Rates and Latency

- **Severity**: RISK
- **Finding**: No alerting configuration exists. The `Dockerfile` includes a `HEALTHCHECK` (curl against localhost) and the `docker-compose.yml` includes healthchecks for both the monolith and MySQL. However, these are container-level liveness checks, not API-level alerting on error rates or latency. There are no CloudWatch alarms, no anomaly detection, no PagerDuty/OpsGenie integration, no SLO-based alerting, and no composite alarms.
- **Gap**: No alerting on API error rates or latency. If the agent-facing APIs degrade, no alert fires. Agents will experience failures with no operational team notification.
- **Compensating Controls**:
  - Monitor Docker container health status as a basic liveness signal
  - Implement agent-side alerting on error rates and response times
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Deploy CloudWatch alarms for: (1) API error rate > 5% over 5 minutes, (2) P95 latency > 2 seconds, (3) healthcheck failures. Integrate with SNS for notification. Add anomaly detection for traffic pattern changes (agent-induced load spikes).
- **Evidence**: `Dockerfile` — `HEALTHCHECK --interval=30s --timeout=5s`; `docker-compose.yml` — healthcheck for monolith and mysql; no CloudWatch alarms, no alerting configuration files.

### ENG-Q1: Infrastructure Governance for Agent-Facing Surface

- **Severity**: RISK
- **Finding**: No infrastructure-as-code exists for the agent-facing surface. There are no Terraform, CloudFormation, or CDK files. The deployment is defined only in `Dockerfile` and `docker-compose.yml` with a manual `deploy.sh` script that runs `docker-compose build` and `docker-compose up -d`. There is no peer review enforcement for infrastructure changes, no drift detection, and no automated plan review.
- **Gap**: No IaC for API gateways, IAM roles, secrets, or networking. No peer review on infrastructure changes. No drift detection. Changes to the deployment are manual and unaudited.
- **Compensating Controls**:
  - Require PR review for all changes to Dockerfile, docker-compose.yml, and deploy.sh
  - Document the current infrastructure topology manually
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Define the infrastructure in Terraform or CloudFormation: VPC, security groups, App Runner service, RDS MySQL, API Gateway, IAM roles, Secrets Manager. Enforce PR review on IaC changes. Enable AWS Config for drift detection.
- **Evidence**: No `.tf`, `.cfn.yaml`, `.cfn.json`, or CDK files in repository; `deploy.sh` — manual `docker-compose build && docker-compose up -d`; no CI/CD pipeline to enforce review.

### ENG-Q2: CI/CD with API Contract Testing

- **Severity**: RISK
- **Finding**: No CI/CD pipeline exists. There are no GitHub Actions workflows (`.github/workflows/`), no GitLab CI (`.gitlab-ci.yml`), no Jenkins (`Jenkinsfile`), and no CodeBuild (`buildspec.yml`). There is no automated testing, no API contract testing, no consumer-driven contract testing (Pact), no OpenAPI spec validation, and no breaking change detection.
- **Gap**: No CI/CD pipeline. No automated testing of any kind. No API contract testing. Breaking changes to agent-facing APIs cannot be caught before deployment.
- **Compensating Controls**:
  - Implement manual testing procedures before each deployment
  - Run API smoke tests from the agent after each deployment to detect breaking changes
- **Remediation Timeline**: 60 days
- **Recommendation**: Create a GitHub Actions pipeline with: (1) API contract tests validating endpoints against an OpenAPI spec, (2) integration tests exercising the fulfillment workflow, (3) schema validation preventing breaking changes. Use Pact for consumer-driven contract testing when agents are defined as consumers.
- **Evidence**: No `.github/`, `.gitlab-ci.yml`, `Jenkinsfile`, or `buildspec.yml` files in repository.

### ENG-Q3: Rollback Capability

- **Severity**: RISK
- **Finding**: No rollback capability exists. `deploy.sh` runs `docker-compose build` and `docker-compose up -d` with no version tagging, no blue/green deployment, no canary deployment, no feature flags, and no rollback triggers. There is no mechanism to revert to a previous known-good state if a deployment breaks agent-facing APIs. Docker images are not tagged with versions.
- **Gap**: No rollback mechanism. A bad deployment that breaks agent-facing APIs requires manually rebuilding and redeploying the previous version. No automated rollback on health check failure.
- **Compensating Controls**:
  - Tag Docker images with version numbers before each deployment
  - Keep the previous Docker image available for manual rollback
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Tag Docker images with git commit SHA or semantic version. Deploy via App Runner or ECS with blue/green deployment. Configure automatic rollback on health check failure. Target: rollback within 15 minutes.
- **Evidence**: `deploy.sh` — `docker-compose build && docker-compose up -d` with no versioning, no rollback logic, no health-check-triggered rollback.

### ENG-Q4: API Test Coverage

- **Severity**: RISK
- **Finding**: No automated tests of any kind exist. There are no test files, no test framework (no PHPUnit, no Pest, no Postman/Newman collections), no API test suites, no integration tests, and no unit tests. The repository contains only application code and deployment files.
- **Gap**: Zero test coverage. No API tests validating input handling, output format, error responses, or edge cases. Agent-facing APIs are completely untested.
- **Compensating Controls**:
  - Implement manual API testing via curl scripts or Postman collections
  - Add smoke tests to the agent orchestration layer to validate API behavior on each deployment
- **Remediation Timeline**: 60 days
- **Recommendation**: Create a PHPUnit or Pest test suite covering: (1) each API endpoint's happy path, (2) error responses for invalid input, (3) authentication/authorization checks, (4) the complete fulfillment workflow end-to-end. Add these tests to a CI pipeline.
- **Evidence**: No test files, no `tests/` directory, no `phpunit.xml`, no `*.test.php` files, no Postman collections in repository.

### ENG-Q5: Encryption at Rest for Agent-Accessible Data

- **Severity**: RISK
- **Finding**: No encryption at rest is configured. The MySQL data volume (`mysql_data`) in `docker-compose.yml` is a standard Docker volume with no encryption. There are no KMS key references, no encrypted volume configurations, and no encryption settings in the MySQL service definition. Customer PII (names, emails, addresses) and payment data are stored unencrypted at rest.
- **Gap**: No encryption at rest for any data store. PII and financial data are stored in plaintext on disk. A disk-level breach exposes all agent-accessible data.
- **Compensating Controls**:
  - Enable filesystem-level encryption on the Docker host (e.g., LUKS or EBS encryption)
  - Use MySQL's InnoDB tablespace encryption as an application-level control
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Deploy MySQL on RDS with encryption at rest enabled (AWS KMS). Use customer-managed KMS keys. If staying on Docker, enable MySQL InnoDB tablespace encryption. Encrypt the Docker volume at the host level using EBS encryption.
- **Evidence**: `docker-compose.yml` — `mysql_data` volume with no encryption configuration; no KMS references in any file; no MySQL encryption settings.

## INFOs — Architecture and Design Inputs

### API-Q6: Structured Response Format

- **Severity**: INFO
- **Finding**: All API responses are JSON, serialized via PHP's `json_encode()`. The `Content-Type: application/json` header is set for all API routes. Response structures are consistent within endpoint categories: list endpoints return `{"products": [...]}` or `{"orders": [...]}`, action endpoints return `{"success": true, ...}`, and error responses return `{"error": "message"}`.
- **Implication**: JSON responses are ideal for LLM consumption. No XML, binary, or protobuf parsing is needed. Agent tool definitions can directly consume the JSON output.
- **Recommendation**: Formalize the JSON response structures in an OpenAPI spec to ensure consistency as the API evolves.
- **Evidence**: `index.php` — `header('Content-Type: application/json')`, `json_encode()` throughout all API handlers.

### API-Q8: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: No event emission exists. There are no webhooks, no SNS/EventBridge/SQS integration, no Kafka topics, and no CDC pipelines. All state changes are stored in the MySQL database and can only be discovered by polling the API endpoints.
- **Implication**: Agents must poll for state changes (e.g., poll `GET /api/admin/orders/pending-fulfillment` to discover new orders). This increases API load and introduces latency between state changes and agent awareness. Event-driven patterns would unlock proactive agent behavior.
- **Recommendation**: Consider adding EventBridge integration for order status changes. Publish events when orders transition between fulfillment states. This enables agents to react to changes without polling.
- **Evidence**: `index.php` — `update_order_status()` writes to database only, no event publishing; no SNS, SQS, or EventBridge references.

### API-Q9: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limits are documented. API responses do not include `X-RateLimit-Remaining`, `X-RateLimit-Limit`, or `Retry-After` headers. There is no API Gateway throttle configuration, no WAF rate rules, and no usage plan documentation.
- **Implication**: Agents calling endpoints at machine speed have no signal for self-throttling. Without rate limit headers, agents cannot proactively back off before hitting limits (once limits are implemented).
- **Recommendation**: When rate limiting is implemented (STATE-Q5), include `X-RateLimit-Remaining` and `Retry-After` headers in responses. Document rate limits in the API specification.
- **Evidence**: `index.php` — no rate limit headers set; no API Gateway or WAF configuration files.

### API-Q10: API Latency Profile

- **Severity**: INFO
- **Finding**: No performance benchmarks, load test results, CloudWatch latency metrics, or APM dashboards exist. The application's P95 response time is unknown. Since all operations are direct MySQL queries in a single-process PHP application, response times likely depend on database performance and query complexity.
- **Implication**: An agent calling 5 fulfillment endpoints sequentially with unknown latency cannot estimate total workflow duration. This shapes whether synchronous or asynchronous patterns are needed for agent workflows.
- **Recommendation**: Conduct baseline latency measurements for each API endpoint. Add response time logging. Target sub-second P95 for read operations and under 2 seconds for write operations. Operations exceeding 5 seconds should use async patterns (API-Q7).
- **Evidence**: No load test results, no performance benchmarks, no APM configuration in repository.

### DATA-Q8: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality metrics, profiling, or monitoring exist. There are no data quality dashboards, no null rate monitoring, no duplicate detection logic, no data freshness SLAs, and no completeness metrics. The seed data is minimal and does not exercise data quality scenarios.
- **Implication**: Agents acting on incomplete or inconsistent data will propagate errors. For inventory restocking decisions, data quality (accurate stock counts, up-to-date product information) directly affects decision quality.
- **Recommendation**: Add data quality monitoring for critical fields: inventory stock_quantity accuracy, order status consistency, and timestamp completeness. Consider implementing a data quality score for inventory data that the agent can check before making restocking decisions.
- **Evidence**: `index.php` — no data quality checks, no validation beyond basic nulls; no data profiling or monitoring configuration.

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Field names are generally semantically meaningful and human-readable. Examples: `customer_name`, `customer_email`, `stock_quantity`, `tracking_number`, `shipping_address`, `warehouse_location`, `total_amount`, `payment_method`, `refund_amount`. No legacy abbreviations or cryptic codes were found. This is a positive finding.
- **Implication**: LLM-based agent reasoning will work well with these field names. No data dictionary or translation layer is needed for field name interpretation.
- **Recommendation**: Maintain this naming convention as the application evolves. Document naming conventions for new developers.
- **Evidence**: `index.php` — `CREATE TABLE` definitions with readable field names throughout `init_db()`.

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No data catalog or metadata layer exists. There is no AWS Glue Data Catalog, no Collibra, Alation, or DataHub integration, no metadata files, and no data dictionaries. The schema is defined only in application code within the `init_db()` function.
- **Implication**: Agent tool authors must inspect PHP source code to understand available data. This slows tool development and increases the risk of misunderstanding data semantics.
- **Recommendation**: Create a data dictionary documenting each table, field, data type, and business meaning. Consider publishing the schema to AWS Glue Data Catalog when migrating to RDS.
- **Evidence**: `index.php` — `init_db()` is the only schema definition; no data catalog or metadata files in repository.

### DISC-Q4: Data Lineage

- **Severity**: INFO
- **Finding**: No data lineage exists. There are no lineage tools (AWS Glue DataBrew, Apache Atlas), no ETL documentation, no data flow diagrams, no transformation logs, and no source-to-target mappings. Data enters the system via API endpoints and is stored directly in MySQL with no transformation pipeline.
- **Implication**: When an agent produces incorrect output due to bad data, there is no lineage trace to identify the data source or transformation that caused the error. For a monolithic application with direct database writes, lineage is relatively simple (API → MySQL), but this changes if the application is decomposed.
- **Recommendation**: Document the current data flow (API input → validation → MySQL storage) as the baseline lineage. Implement lineage tracking as the architecture evolves.
- **Evidence**: `index.php` — data flows directly from API input to MySQL INSERT/UPDATE statements, no transformation pipeline, no lineage tools.

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No custom business metrics are published. There are no `cloudwatch.put_metric_data` calls, no business KPI tracking, no custom dashboards, and no business outcome measurements. The application tracks order status changes in the `order_status_history` table but does not publish metrics for fulfillment time, order conversion rate, or customer satisfaction.
- **Implication**: When agents consume the system for restocking decisions, business metrics (inventory accuracy, restocking success rate, stockout frequency) become the primary signal for whether agent interactions produce good outcomes. Without these metrics, agent effectiveness cannot be measured.
- **Recommendation**: Add CloudWatch custom metrics for: (1) orders processed per hour, (2) average fulfillment time, (3) stockout events, (4) return rate. These will serve as the baseline for measuring agent impact.
- **Evidence**: `index.php` — no metrics publishing, no CloudWatch SDK, no business KPI tracking.

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: RISK
- **Finding**: The application exposes REST-like endpoints under `/api/` returning JSON. Endpoints include `GET /api/products`, `POST /api/orders`, `GET /api/orders/me`, and a full fulfillment workflow. However, the API is gated behind PHP session-based authentication, making it not directly agent-consumable.
- **Gap**: REST endpoints exist but require session-based auth. No formal documentation.
- **Recommendation**: Implement API key auth (AUTH-Q1) and generate an OpenAPI spec.
- **Evidence**: `index.php` — route handler, JSON responses, session check.

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK
- **Finding**: No OpenAPI, AsyncAPI, GraphQL schema, or Smithy files exist. API surface defined only in PHP code.
- **Gap**: No machine-readable spec. Tool definitions must be manually authored.
- **Recommendation**: Generate OpenAPI 3.0 spec from route definitions.
- **Evidence**: No spec files in repository.

#### API-Q3: Structured Error Responses
- **Severity**: RISK
- **Finding**: Error responses use `json_encode(['error' => ...])` with HTTP status codes but no structured error codes, retryable boolean, or consistent format.
- **Gap**: No structured error classification. Agents cannot distinguish retriable from terminal errors.
- **Recommendation**: Standardize to `{"error": {"code": "...", "message": "...", "retryable": false}}`.
- **Evidence**: `index.php` — inconsistent error formats across endpoints.

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: BLOCKER
- **Conditional**: agent_scope is "write-enabled" — evaluated as BLOCKER
- **Finding**: Write endpoints do not support idempotency keys. Order IDs use `uniqid()` with no deduplication. Retried writes create duplicates.
- **Gap**: No idempotency support on any write endpoint.
- **Recommendation**: Add `Idempotency-Key` header support and deduplication table.
- **Evidence**: `index.php` — `POST /api/orders` handler, `uniqid('order-')`.

#### API-Q5: API Versioning and Deprecation
- **Severity**: RISK
- **Finding**: No versioning (`/api/products` not `/api/v1/products`). No `Accept-Version` headers. No changelog.
- **Gap**: Any change is a breaking change with no version buffer.
- **Recommendation**: Add URL-based versioning `/api/v1/` and deprecation policy.
- **Evidence**: `index.php` — unversioned route patterns.

#### API-Q6: Structured Response Format
- **Severity**: INFO
- **Finding**: All API responses are JSON via `json_encode()` with `Content-Type: application/json`.
- **Gap**: N/A — JSON is ideal for agent consumption.
- **Recommendation**: Formalize response structures in an OpenAPI spec.
- **Evidence**: `index.php` — `header('Content-Type: application/json')`.

#### API-Q7: Asynchronous Operation Support
- **Severity**: RISK
- **Finding**: All endpoints are synchronous. No background jobs, polling, or webhook patterns.
- **Gap**: No async support for long-running operations.
- **Recommendation**: Add job submission + polling pattern for operations exceeding 30s.
- **Evidence**: `index.php` — synchronous handlers only.

#### API-Q8: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: No event emission. No webhooks, SNS, EventBridge, SQS, or Kafka.
- **Gap**: Agents must poll for state changes.
- **Recommendation**: Add EventBridge integration for order status changes.
- **Evidence**: `index.php` — `update_order_status()` writes to DB only.

#### API-Q9: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limits documented. No `X-RateLimit-Remaining` or `Retry-After` headers.
- **Gap**: No self-throttling signal for agents.
- **Recommendation**: Include rate limit headers when rate limiting is implemented.
- **Evidence**: `index.php` — no rate limit headers; no API Gateway config.

#### API-Q10: API Latency Profile
- **Severity**: INFO
- **Finding**: No performance benchmarks or latency data. P95 response time unknown.
- **Gap**: Cannot estimate agent workflow duration.
- **Recommendation**: Conduct baseline latency measurements for all endpoints.
- **Evidence**: No load test results or APM config in repository.

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: Authentication is exclusively session-based via PHP `session_start()` with username/password form login. No OAuth2 client credentials, no API key auth, no mTLS, no service accounts.
- **Gap**: No machine identity mechanism. Agents cannot authenticate without UI automation.
- **Recommendation**: Implement API key authentication as an alternative auth path.
- **Evidence**: `index.php` — `session_start()`, `$_SESSION['user']` check, `POST /login` form-based.

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK
- **Finding**: Coarse-grained roles: `admin` (full access) and `customer` (limited). No fine-grained permission scoping.
- **Gap**: Cannot grant an agent read-only inventory access without also granting order creation.
- **Recommendation**: Implement fine-grained RBAC with per-endpoint permissions.
- **Evidence**: `index.php` — `$_SESSION['user']['role']` checks, two roles only.

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK
- **Finding**: No action-level authorization. Admin role accesses all admin endpoints uniformly.
- **Gap**: No ABAC, no per-action permission checks.
- **Recommendation**: Add action-level permission checks per API endpoint.
- **Evidence**: `index.php` — role-level checks only, no action-level middleware.

#### AUTH-Q4: Identity Propagation
- **Severity**: RISK
- **Finding**: No JWT/OAuth token exchange. User context in PHP session only. No identity propagation for external service calls.
- **Gap**: No technical identity propagation mechanism.
- **Recommendation**: Implement JWT-based identity propagation.
- **Evidence**: `index.php` — `$_SESSION['user']`, no JWT parsing, no token exchange.

#### AUTH-Q5: Agent-as-Self vs Agent-on-Behalf-of-User
- **Severity**: RISK
- **Finding**: No concept of agent identity. Cannot distinguish agent-as-self from agent-on-behalf-of-user.
- **Gap**: No separate auth flows or audit fields for these two modes.
- **Recommendation**: Implement two auth flows with separate audit logging.
- **Evidence**: `index.php` — only `$_SESSION['user']` identity model.

#### AUTH-Q6: Credential Management
- **Severity**: RISK
- **Finding**: DB credentials via env vars with hardcoded fallback `getenv('DB_PASS') ?: 'ecommerce_pass'`. No Secrets Manager or Vault.
- **Gap**: Hardcoded credential fallback. No secret rotation.
- **Recommendation**: Remove hardcoded fallback. Integrate AWS Secrets Manager.
- **Evidence**: `index.php` — hardcoded password fallback; `docker-compose.yml` — env vars.

#### AUTH-Q7: Immutable Audit Logging ⚡
- **Severity**: BLOCKER
- **Conditional**: agent_scope is "write-enabled" — evaluated as BLOCKER
- **Finding**: `order_status_history` table records changes with `changed_by` field but is mutable MySQL table. No CloudTrail, no immutable storage, no tamper-evident logging.
- **Gap**: No immutable audit log. No compliance-grade logging for write operations.
- **Recommendation**: Enable CloudTrail with S3 Object Lock for immutable audit storage.
- **Evidence**: `index.php` — `order_status_history` table, `update_order_status()`, no CloudTrail.

#### AUTH-Q8: Agent Identity Suspension
- **Severity**: RISK
- **Finding**: No suspension mechanism. Users can only be deleted (irreversible). No `is_active` flag.
- **Gap**: Cannot suspend a misbehaving agent without losing audit history.
- **Recommendation**: Add `is_active` field to users table and check during auth.
- **Evidence**: `index.php` — `DELETE /api/admin/users/{id}` only, no disable mechanism.

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: BLOCKER
- **Conditional**: agent_scope is "write-enabled" — evaluated as BLOCKER
- **Finding**: Database transactions exist for individual operations but the multi-step fulfillment workflow (validate → assign-warehouse → pick → pack → quality-check → ship) has no saga pattern or compensation logic. Each step commits independently.
- **Gap**: No compensation endpoints. No rollback for multi-step workflows. Partial state corruption possible.
- **Recommendation**: Implement compensation endpoints for each fulfillment step and a workflow state machine.
- **Evidence**: `index.php` — separate committed transactions per step, no saga pattern.

#### STATE-Q2: Queryable Current State
- **Severity**: RISK
- **Finding**: Partial queryable state: `GET /api/products` (inventory), `GET /api/orders/me` (customer orders), `GET /api/orders/{id}/history`. No general-purpose order lookup by ID.
- **Gap**: Incomplete queryable state. No single-resource GET endpoints.
- **Recommendation**: Add `GET /api/orders/{id}`, `GET /api/products/{id}`, `GET /api/warehouses/{id}`.
- **Evidence**: `index.php` — list endpoints exist, no resource-level GET by ID.

#### STATE-Q3: Concurrency Controls
- **Severity**: RISK
- **Finding**: No optimistic locking. Inventory decrement `stock_quantity - ?` is a blind update with no version check. Race condition between stock check and decrement.
- **Gap**: No version fields, no ETags, no `SELECT FOR UPDATE`.
- **Recommendation**: Add `version` column with conditional updates. Add ETags.
- **Evidence**: `index.php` — `UPDATE inventory SET stock_quantity = stock_quantity - ?` without version check.

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK
- **Finding**: No circuit breakers or retry logic. `get_db()` calls `die()` on failure. Direct MySQL dependency with no fallback.
- **Gap**: No resilience patterns. DB failure crashes the application.
- **Recommendation**: Replace `die()` with structured errors. Add retry logic and circuit breaker.
- **Evidence**: `index.php` — `die("Database connection failed: ...")`, no retry/fallback logic.

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK
- **Finding**: No rate limiting at any layer. No API Gateway, WAF, or application middleware.
- **Gap**: Runaway agent loops can overwhelm the application.
- **Recommendation**: Deploy API Gateway with throttling and usage plans.
- **Evidence**: `docker-compose.yml` — port 8080 exposed with no limiting; no rate limit code.

#### STATE-Q6: Blast Radius and Transaction Limits
- **Severity**: RISK
- **Finding**: No transaction limits. No max records, spend caps, or per-agent operation limits.
- **Gap**: Agent errors can issue unlimited refunds or create unlimited orders.
- **Recommendation**: Add configurable per-identity transaction limits.
- **Evidence**: `index.php` — no limit checks on any write endpoint.

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: RISK
- **Finding**: Single Docker container, no auto-scaling, no load balancing. No load test results.
- **Gap**: Single-instance deployment cannot handle agent traffic patterns.
- **Recommendation**: Deploy on App Runner/ECS with auto-scaling. Conduct load testing.
- **Evidence**: `docker-compose.yml` — single service instances; no scaling config.

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State
- **Severity**: RISK
- **Finding**: Partial support. Returns use `pending_review` status requiring admin approval. Fulfillment workflow has multi-step status chain. However, fulfillment steps auto-commit without human confirmation.
- **Gap**: No general-purpose draft state. Only return approval has true pending-approval pattern.
- **Recommendation**: Add a `proposed` status for agent-recommended fulfillment actions before human approval.
- **Evidence**: `index.php` — `pending_review` for returns, fulfillment status transitions.

#### HITL-Q2: Configurable Approval Gates
- **Severity**: RISK
- **Finding**: Return approval requires explicit human action. Fulfillment steps are hardcoded sequential API calls, not configurable approval gates.
- **Gap**: Cannot dynamically require approval for high-value operations.
- **Recommendation**: Implement configurable approval rules (e.g., require approval for orders over $500).
- **Evidence**: `index.php` — `POST /api/admin/approve-return` hardcoded, no configurable gates.

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK
- **Finding**: `docker-compose.yml` provides local dev environment. `seed_data()` creates minimal test data (5 products, 1 order). No separate staging or sandbox config.
- **Gap**: No production-equivalent staging environment for agent testing.
- **Recommendation**: Create staging environment with production-scale synthetic data.
- **Evidence**: `docker-compose.yml` — single environment; `index.php` — minimal seed data.

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: PII stored (customer_name, customer_email, shipping_address, password). Passwords bcrypt-hashed, all other PII plaintext. No field-level classification, no tagging, no Macie.
- **Gap**: No data classification. Agent retrieves all PII by default. No field-level access control.
- **Recommendation**: Classify PII fields. Implement field-level redaction in API responses.
- **Evidence**: `index.php` — `orders` table with PII fields, `users` table with password, no classification.

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: BLOCKER
- **Conditional**: agent_scope is "write-enabled" — evaluated as BLOCKER
- **Finding**: Customer PII and financial data stored with no residency configuration. No region-specific deployment. No GDPR/LGPD references.
- **Gap**: No data residency policy. Write-enabled agent may transmit PII to LLM in different jurisdiction.
- **Recommendation**: Document residency requirements. Deploy LLM endpoints in same region as data.
- **Evidence**: `index.php` — PII in orders table; `docker-compose.yml` — no region config.

#### DATA-Q3: Selective Query Support
- **Severity**: RISK
- **Finding**: No pagination, filtering, or sorting. `SELECT * FROM inventory` returns all products. No `limit`/`offset` parameters.
- **Gap**: Unbounded result sets exhaust LLM context windows.
- **Recommendation**: Add `limit`, `offset`, and `filter` parameters to list endpoints.
- **Evidence**: `index.php` — `SELECT *` queries with no LIMIT clause.

#### DATA-Q4: System of Record Designations
- **Severity**: RISK
- **Finding**: Single shared MySQL database as implicit SoR. No documented designations.
- **Gap**: Undocumented data ownership. Ambiguous during decomposition.
- **Recommendation**: Document SoR for each entity.
- **Evidence**: `index.php` — single `$db` connection for all domains.

#### DATA-Q5: Reliable Timestamps
- **Severity**: RISK
- **Finding**: `created_at`/`updated_at` fields exist but use `date('Y-m-d H:i:s')` with no timezone configuration. No UTC guarantee.
- **Gap**: Server-dependent timezone. No event-time distinction.
- **Recommendation**: Set `date_default_timezone_set('UTC')`. Use `UTC_TIMESTAMP()` in MySQL.
- **Evidence**: `index.php` — `date('Y-m-d H:i:s')` calls, no timezone setting.

#### DATA-Q6: Data Freshness Signaling
- **Severity**: RISK
- **Finding**: No `Cache-Control`, `X-Data-Age`, or consistency headers. All data served directly from MySQL.
- **Gap**: No freshness signal for agents. Unknown consistency guarantees.
- **Recommendation**: Add `Cache-Control: no-cache` headers. Document consistency model.
- **Evidence**: `index.php` — only `Content-Type` header set.

#### DATA-Q7: PII Redaction in Logs
- **Severity**: RISK
- **Finding**: Error logging enabled, display errors disabled. No PII scrubbing. Exception messages may contain PII from SQL queries.
- **Gap**: PII may leak into logs. No redaction mechanism.
- **Recommendation**: Implement custom error handler with PII pattern redaction.
- **Evidence**: `index.php` — `ini_set('log_errors', '1')`, `$e->getMessage()` in error responses.

#### DATA-Q8: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics, profiling, or monitoring. No null rate monitoring or completeness tracking.
- **Gap**: Cannot assess data quality for agent decision-making.
- **Recommendation**: Add monitoring for inventory accuracy and data completeness.
- **Evidence**: `index.php` — no data quality checks or monitoring.

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Documentation and Versioning
- **Severity**: RISK
- **Finding**: Schema defined in `init_db()` via inline `CREATE TABLE` statements. No external schema files, no migration framework, no versioning. Ad-hoc `ALTER TABLE` changes wrapped in try/catch.
- **Gap**: No versioned schema. No migration framework.
- **Recommendation**: Adopt migration framework (Phinx/Flyway). Export baseline schema.
- **Evidence**: `index.php` — `init_db()` function, `ALTER TABLE` try/catch pattern.

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Field names are semantically meaningful: `customer_name`, `stock_quantity`, `tracking_number`, `shipping_address`. No legacy abbreviations. Positive finding.
- **Gap**: N/A — naming is clear.
- **Recommendation**: Maintain naming convention. Document for new developers.
- **Evidence**: `index.php` — `CREATE TABLE` definitions with readable field names.

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No data catalog or metadata layer. Schema defined only in application code.
- **Gap**: Tool authors must inspect source code to understand data.
- **Recommendation**: Create data dictionary. Consider Glue Data Catalog on RDS migration.
- **Evidence**: `index.php` — `init_db()` only schema definition.

#### DISC-Q4: Data Lineage
- **Severity**: INFO
- **Finding**: No lineage tools or documentation. Data flows directly from API to MySQL.
- **Gap**: No lineage trace for debugging data issues.
- **Recommendation**: Document current data flow as baseline lineage.
- **Evidence**: `index.php` — direct INSERT/UPDATE from API handlers.

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK
- **Finding**: No X-Ray, OpenTelemetry, or structured logging. PHP built-in error logging only. No JSON logs, no correlation IDs.
- **Gap**: Agent-initiated failures not debuggable. No request tracing.
- **Recommendation**: Add OpenTelemetry SDK, structured JSON logging, and request IDs.
- **Evidence**: `index.php` — `ini_set('log_errors', '1')` only; `Dockerfile` — no tracing SDK.

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK
- **Finding**: No alerting. Dockerfile HEALTHCHECK and docker-compose healthchecks are container-level only. No CloudWatch alarms.
- **Gap**: No API-level alerting. Degradation undetected.
- **Recommendation**: Deploy CloudWatch alarms for error rate and latency.
- **Evidence**: `Dockerfile` — HEALTHCHECK; no alerting config files.

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics. No CloudWatch put_metric_data, no KPI dashboards.
- **Gap**: Agent effectiveness cannot be measured.
- **Recommendation**: Add custom metrics for fulfillment time, stockout events, return rate.
- **Evidence**: `index.php` — no metrics publishing.

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK
- **Finding**: No IaC (Terraform/CloudFormation/CDK). Deployment via manual `deploy.sh` script. No peer review, no drift detection.
- **Gap**: Infrastructure changes are manual and unaudited.
- **Recommendation**: Define infrastructure in Terraform/CloudFormation. Enable Config for drift detection.
- **Evidence**: No IaC files; `deploy.sh` — manual deployment.

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK
- **Finding**: No CI/CD pipeline. No automated testing, no contract testing, no breaking change detection.
- **Gap**: Breaking API changes undetected before deployment.
- **Recommendation**: Create GitHub Actions pipeline with API contract tests.
- **Evidence**: No `.github/`, `Jenkinsfile`, `buildspec.yml` in repository.

#### ENG-Q3: Rollback Capability
- **Severity**: RISK
- **Finding**: No rollback. `deploy.sh` runs `docker-compose up` with no versioning, no blue/green, no canary.
- **Gap**: Bad deployments require manual recovery.
- **Recommendation**: Tag Docker images. Deploy with blue/green on App Runner/ECS.
- **Evidence**: `deploy.sh` — no version tagging, no rollback logic.

#### ENG-Q4: API Test Coverage
- **Severity**: RISK
- **Finding**: Zero automated tests. No test files, no test framework, no API test suites.
- **Gap**: Agent-facing APIs completely untested.
- **Recommendation**: Create PHPUnit/Pest test suite covering all API endpoints.
- **Evidence**: No test files or `tests/` directory in repository.

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: RISK
- **Finding**: No encryption at rest. MySQL docker volume unencrypted. No KMS configuration.
- **Gap**: PII and financial data stored unencrypted on disk.
- **Recommendation**: Deploy MySQL on RDS with KMS encryption. Enable volume encryption.
- **Evidence**: `docker-compose.yml` — `mysql_data` volume, no encryption settings.

#### ENG-Q6: Cross-Origin and Network Policies
- **Severity**: BLOCKER
- **Finding**: No CORS configuration. No security groups, firewall rules, API Gateway, WAF, or network policies. Port 8080 exposed directly. Good container hardening (`no-new-privileges`, `read_only`) but no network security.
- **Gap**: No CORS. No network security documentation. Agent has no documented network path.
- **Recommendation**: Add CORS headers. Deploy API Gateway with WAF. Define security groups in IaC.
- **Evidence**: `index.php` — no CORS headers; `docker-compose.yml` — port 8080 exposed; no IaC.

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `index.php` | API-Q1, API-Q2, API-Q3, API-Q4, API-Q5, API-Q6, API-Q7, API-Q8, API-Q9, API-Q10, AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q6, AUTH-Q7, AUTH-Q8, STATE-Q1, STATE-Q2, STATE-Q3, STATE-Q4, STATE-Q5, STATE-Q6, STATE-Q7, HITL-Q1, HITL-Q2, HITL-Q3, DATA-Q1, DATA-Q2, DATA-Q3, DATA-Q4, DATA-Q5, DATA-Q6, DATA-Q7, DATA-Q8, DISC-Q1, DISC-Q2, DISC-Q3, DISC-Q4, OBS-Q1, OBS-Q3, ENG-Q6 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `Dockerfile` | STATE-Q7, OBS-Q1, OBS-Q2, ENG-Q6 |
| `docker-compose.yml` | AUTH-Q6, STATE-Q5, STATE-Q7, HITL-Q3, DATA-Q2, DATA-Q6, ENG-Q5, ENG-Q6, OBS-Q2 |

### Deployment Scripts
| File | Questions Referenced |
|------|---------------------|
| `deploy.sh` | ENG-Q1, ENG-Q3 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `.htaccess` | API-Q1 (URL rewriting for API routing) |

### Notable Absences (files NOT found — absence is evidence)
| Expected File Type | Questions Referenced |
|------|---------------------|
| No OpenAPI/Swagger spec files | API-Q2 |
| No Terraform/CloudFormation/CDK files | AUTH-Q7, ENG-Q1, ENG-Q6 |
| No CI/CD configuration files (`.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`, `buildspec.yml`) | ENG-Q2 |
| No test files (`tests/`, `phpunit.xml`, `*.test.php`) | ENG-Q4 |
| No dependency manifests (`composer.json`, `package.json`) | API-Q2 (no spec generation tooling) |
| No API Gateway, WAF, or network security configuration | STATE-Q5, ENG-Q6, API-Q9 |
| No CloudWatch, X-Ray, or alerting configuration | OBS-Q1, OBS-Q2, OBS-Q3 |
| No Secrets Manager or Vault configuration | AUTH-Q6 |

---

*End of Agentic Readiness Assessment Report*
