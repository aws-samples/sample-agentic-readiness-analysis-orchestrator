# Agentic Readiness Assessment Report

**Target**: umami-software--umami
**Date**: 2025-01-08
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: typescript, analytics, web-app
**Context**: Self-hosted privacy-focused web analytics.

**Archetype Justification**: The application owns persistent state in PostgreSQL and ClickHouse, exposes full CRUD operations for users, websites, teams, links, pixels, and reports through REST API endpoints, and manages entity lifecycle with soft deletes.

**Surface flags**:
  - has_persistent_data_store: true
  - has_http_rpc_surface: true
  - has_auth_surface: true
  - has_write_operations: true
  - has_logging_of_user_data: true

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 2 | **RISK-SAFETY**: 7 | **RISK-QUALITY**: 13 | **INFOs**: 13

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days.

**Classification Rationale**: This repo has 2 BLOCKERs (API-Q1, AUTH-Q1), 7 RISK-SAFETY findings, and 13 RISK-QUALITY findings. The 2 BLOCKERs trigger the "Remediation Required" profile (1–2 High → Remediation Required). The V6 unified severity maps BLOCKER to High, RISK-SAFETY to Medium (safety_impact=true), and RISK-QUALITY to Medium (safety_impact=false). Under V6 classification: 2 High findings → Remediation Required.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 2 |
| RISK-SAFETY | 7 |
| RISK-QUALITY | 13 |
| INFO | 13 |
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

### API-Q1: Documented API Interface

- **Severity**: BLOCKER
- **Finding**: The application exposes 70+ REST API route handlers under `src/app/api/` implemented as Next.js App Router route handlers. However, these APIs are code-first with no formal documentation. There is no OpenAPI specification, no Swagger documentation, no API documentation site, and no README section documenting API endpoints, their parameters, or response shapes.
- **Gap**: No documented API interface exists. An agent integrating with this system would need to reverse-engineer the API surface from source code — reading individual route files, Zod schemas, and permission checks to understand available operations.
- **Remediation**:
  - **Immediate**: Generate an OpenAPI 3.x specification from the existing route handlers and Zod schemas. Tools like `next-swagger-doc` or manual authoring can produce a baseline spec.
  - **Target State**: A machine-readable OpenAPI specification that documents all API endpoints, request/response schemas, authentication requirements, and error responses. Kept in sync with implementation via CI validation.
  - **Estimated Effort**: Medium
  - **Dependencies**: None
- **Evidence**: `src/app/api/` (70+ route handler files), absence of any `openapi.yaml`, `swagger.json`, or API documentation files in repository.

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: The application supports bearer token authentication via encrypted JWTs designed for human user login flows (username/password → JWT token). There is no OAuth2 client credentials flow, no API key authentication with principal attribution, no mTLS, and no service account concept. An agent would need to use a human user's credentials to authenticate, and there is no way to distinguish agent principals from human principals in audit.
- **Gap**: No machine identity authentication mechanism. Agents must authenticate using human-style username/password login. No per-agent principal attribution possible.
- **Remediation**:
  - **Immediate**: Implement API key authentication with per-key principal attribution for agent identities.
  - **Target State**: Machine identity authentication that distinguishes agent principals from human principals, with per-agent API keys or OAuth2 client credentials, and identity attribution in audit logs.
  - **Estimated Effort**: High
  - **Dependencies**: AUTH-Q6 (audit logging to record agent principal)
- **Evidence**: `src/lib/auth.ts`, `src/lib/jwt.ts`, `src/app/api/auth/login/route.ts`

---

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The authorization model uses a role-based system with roles (`admin`, `user`, `view-only`, `team-owner`, `team-manager`, `team-member`, `team-view-only`). Permissions are defined in `ROLE_PERMISSIONS` in `src/lib/constants.ts`. However, the permission model is coarse-grained — the `admin` role has `all` permissions, and the `user` role has broad access to all website and team CRUD operations. There is no mechanism for scoping an agent identity to a subset of operations (e.g., read-only access to specific websites).
- **Gap**: No support for fine-grained, per-resource permission scoping. An agent identity would inherit the full `user` or `admin` role permissions with no ability to restrict to specific resources or read-only operations.
- **Compensating Controls**:
  - Create a dedicated `agent` role with restricted permissions in `ROLE_PERMISSIONS`
  - Use the existing `view-only` role for read-only agent access and restrict team membership scope
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Introduce a dedicated agent role with minimal permissions, or leverage the existing `view-only` role for initial read-only agent integration. Consider adding resource-level scoping (specific website IDs) for agent identities.
- **Evidence**: `src/lib/constants.ts` (ROLE_PERMISSIONS), `src/permissions/user.ts`, `src/permissions/website.ts`

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The application implements action-level permission checks (`canViewWebsite`, `canUpdateWebsite`, `canDeleteWebsite`, etc.) in `src/permissions/`. Team roles have differentiated permissions (team-member can view but not delete). However, the base `user` role has all website CRUD permissions bundled together — a user who can read a website can also update and delete it. There is no mechanism to grant an agent read-without-write access to a resource it owns.
- **Gap**: While action-level functions exist in code, the role model does not support granting read-only access to owned resources without also granting write/delete access at the user role level.
- **Compensating Controls**:
  - Assign agent identities the `view-only` role or a team `team-view-only` role to restrict to read operations
  - Implement API Gateway-level method restrictions (allow GET only) for agent traffic
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Leverage the existing `view-only` role for agent identities. For team-scoped access, use `team-view-only` role which inherits no write permissions.
- **Evidence**: `src/permissions/website.ts`, `src/permissions/user.ts`, `src/lib/constants.ts`

#### AUTH-Q6: Immutable Audit Logging — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The application uses the `debug` library for internal diagnostic logging (`debug('umami:auth')`, `debug('umami:prisma')`, etc.). There is no structured audit logging that records authenticated principal identity, action performed, resource accessed, or timestamp for API operations. No CloudTrail, CloudWatch Logs, or immutable log storage configuration exists. The `debug` output is developer-diagnostic only and not persisted.
- **Gap**: No audit trail exists for agent (or human) actions. Cannot determine after the fact who performed which operation.
- **Compensating Controls**:
  - Implement request-level access logging at a reverse proxy or API gateway layer
  - Add structured audit logging middleware that captures principal, action, resource, and timestamp
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Introduce audit logging middleware in `parseRequest()` that logs the authenticated user ID, HTTP method, endpoint path, and timestamp to a structured, append-only log store.
- **Evidence**: `src/lib/auth.ts` (debug-only logging), `src/lib/request.ts` (no audit logging in parseRequest), absence of any logging infrastructure configuration

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: User accounts can be deleted (soft-deleted via `deletedAt` field), and the admin can manage users via `src/app/api/admin/users/`. However, there is no mechanism for immediate identity suspension that invalidates active sessions/tokens without full deletion. The Redis-based auth keys have optional expiry but no revocation endpoint. JWT tokens remain valid until expiry regardless of user state.
- **Gap**: No immediate suspension mechanism for agent identities. Soft-deleting a user does not invalidate existing auth tokens already issued. There is no token revocation list or session invalidation endpoint.
- **Compensating Controls**:
  - Implement short-lived tokens (reduce JWT/session expiry to minutes)
  - Add a check against `deletedAt` in the `checkAuth()` function to reject requests from soft-deleted users
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `deletedAt` check in `checkAuth()` to immediately reject requests from suspended users. Implement a Redis-based token blacklist or reduce token TTL.
- **Evidence**: `src/lib/auth.ts` (checkAuth does not check deletedAt), `prisma/schema.prisma` (User.deletedAt field), `src/queries/prisma/user.ts` (deleteUser with soft delete)

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No rate limiting middleware or configuration exists in the application. No API Gateway throttling, no WAF rate rules, no application-level rate limiting libraries (e.g., `express-rate-limit`). The `next.config.ts` configures CORS headers but no rate limit headers. A runaway agent or attacker could call API endpoints at unlimited speed.
- **Gap**: No rate limiting at any layer. Agent traffic could overwhelm the application and its PostgreSQL/ClickHouse/Redis backends.
- **Compensating Controls**:
  - Deploy behind an API gateway or reverse proxy (nginx, Cloudflare) with rate limiting configured
  - Add application-level rate limiting middleware for the Next.js API routes
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement rate limiting at the application layer (e.g., `next-rate-limit` or custom middleware using Redis) and/or deploy behind an API gateway with per-client throttling.
- **Evidence**: `next.config.ts` (no rate limit configuration), `package.json` (no rate-limiting dependencies), absence of any rate limit middleware in `src/`

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The application uses the `debug` library which outputs to stderr when `DEBUG` env var is set. In `src/lib/auth.ts`, the debug log statement `log({ token, payload, authKey, shareToken, user })` outputs the full auth token, payload, and user object to debug output. The Kafka error handler in `src/lib/kafka.ts` uses `console.log('KAFKA ERROR:', serializeError(e))` which may serialize request context. There is no PII masking or log scrubbing.
- **Gap**: When debug logging is enabled, authentication tokens and user objects (including user IDs) are logged without redaction. No log scrubbing middleware exists.
- **Compensating Controls**:
  - Ensure `DEBUG` environment variable is not set in production
  - Add log filtering at the infrastructure level to prevent sensitive data from reaching persistent log stores
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Remove or redact sensitive fields from debug log statements. Replace `log({ token, payload, authKey, shareToken, user })` with `log({ userId: user?.id, hasToken: !!token })`. Add a log sanitization layer.
- **Evidence**: `src/lib/auth.ts` (line: `log({ token, payload, authKey, shareToken, user })`), `src/lib/kafka.ts` (line: `console.log('KAFKA ERROR:', serializeError(e))`)

#### DATA-Q1: Sensitive Data Classification — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: Stage A = Yes. agent_scope is "read-only" — B2 fires as RISK-SAFETY.
- **Finding**: The system stores user passwords (bcrypt hashed), usernames, and IP-derived geolocation. Passwords are properly excluded from API responses (B1 = CLEAR). However, no access control differentiation exists between sensitive and non-sensitive data domains (B2 = RISK-SAFETY). No formal classification metadata (B3 = INFO).
- **Gap**: No OAuth scopes or fine-grained permissions differentiating access levels for analytics data vs user management data.
- **Compensating Controls**:
  - Assign agent identities the `view-only` role limiting scope
  - Implement per-team data isolation for agent access
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement OAuth scopes or fine-grained permissions that distinguish access levels for analytics data vs user management data.
- **Evidence**: `src/queries/prisma/user.ts` (password exclusion), `src/app/api/admin/users/route.ts` (omit password), `prisma/schema.prisma`

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, GraphQL schema, or Smithy specification file exists in the repository. The API is implemented code-first using Next.js App Router route handlers with Zod validation schemas defined inline in each route file.
- **Gap**: No machine-readable API specification. Agent tool generation requires manual authoring of tool definitions from source code inspection.
- **Compensating Controls**:
  - Generate an OpenAPI spec from existing Zod schemas and route structure
  - Use API exploration tools to auto-document the surface
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Auto-generate an OpenAPI 3.x specification from the existing Zod schemas and Next.js route structure. Tools like `zod-to-openapi` can accelerate this.
- **Evidence**: Absence of any `openapi.yaml`, `swagger.json`, `.graphql`, or `.smithy` files in repository. API implemented in `src/app/api/` with inline Zod schemas.

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The application has a consistent structured error response format in `src/lib/response.ts` with `{error: {message, code, status}}` for 400, 401, 403, 404, and 500 errors. Each error includes a machine-readable code (e.g., `'bad-request'`, `'unauthorized'`, `'forbidden'`, `'not-found'`, `'server-error'`). This is a good pattern for agent consumption.
- **Gap**: Error responses lack a `retryable` field or category that would help agents distinguish retriable errors (rate limit, timeout) from terminal errors (invalid input, permission denied). All 500 errors look the same to an agent.
- **Compensating Controls**:
  - Agents can use HTTP status codes heuristically (5xx = retryable, 4xx = terminal)
  - Add a `retryable` boolean to the error response schema
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a `retryable: boolean` field to the error response structure. Mark 429 (if added) and 503 as retryable; mark 400/401/403/404 as non-retryable.
- **Evidence**: `src/lib/response.ts`

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The API has no versioning scheme (no `/v1/` prefix, no `Accept-Version` header). The Prisma schema has 14 migrations showing schema evolution but no formal API versioning or breaking change detection. The CI pipeline runs tests and builds but does not validate API contracts or detect breaking changes.
- **Gap**: No API versioning. No breaking change detection in CI. Agent tool bindings could break silently on any deployment.
- **Compensating Controls**:
  - Pin agent integrations to specific application versions (Docker image tags)
  - Add API contract tests (e.g., Pact or OpenAPI diff) to CI
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Introduce URL-based API versioning (`/api/v1/...`) and add breaking-change detection tooling to the CI pipeline.
- **Evidence**: `src/app/api/` (no version prefix), `.github/workflows/ci.yml` (no contract testing), `prisma/migrations/` (14 migrations with no API contract tests)

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No distributed tracing (OpenTelemetry, X-Ray) is configured. No trace ID propagation. Logging uses the `debug` library which outputs unstructured text to stderr and is disabled by default in production. No JSON structured logging. No correlation IDs linking requests.
- **Gap**: Agent-initiated requests are not traceable through the system. If a request fails, there is no mechanism to reconstruct the execution path.
- **Compensating Controls**:
  - Add request ID generation middleware that includes a unique ID in response headers
  - Deploy with a reverse proxy that adds trace headers
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Integrate OpenTelemetry SDK for Node.js with trace ID propagation. Replace `debug` library with structured JSON logging (e.g., `pino`) with correlation IDs.
- **Evidence**: `package.json` (no tracing dependencies), `src/lib/auth.ts` (debug library usage), absence of any tracing configuration

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No alerting configuration exists. No CloudWatch alarms, no PagerDuty/OpsGenie integration, no anomaly detection. The Docker Compose healthcheck (`curl http://localhost:3000/api/heartbeat`) provides basic liveness but no error rate or latency monitoring.
- **Gap**: No alerting for API degradation. An agent experiencing elevated error rates would not trigger any notification to operators.
- **Compensating Controls**:
  - Configure infrastructure-level monitoring at the deployment platform (e.g., Docker healthchecks, Heroku metrics)
  - Add an external uptime monitor (e.g., UptimeRobot) as a baseline
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement application-level metrics (request count, error rate, latency percentiles) and configure alerting thresholds.
- **Evidence**: `docker-compose.yml` (basic healthcheck only), absence of any monitoring/alerting configuration

#### ENG-Q1: Infrastructure Governance — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No infrastructure-as-code exists. The deployment infrastructure is defined only through Docker Compose files and PaaS configuration (Heroku `app.json`, Netlify `netlify.toml`). There are no Terraform, CloudFormation, CDK, or Kubernetes manifests. No IAM policy definitions, no API Gateway configuration, no secrets management infrastructure.
- **Gap**: Infrastructure is not defined as code, not subject to peer review as infrastructure changes, and has no drift detection. The agent-facing surface (API, network, auth) is not governed by IaC.
- **Compensating Controls**:
  - Use platform-managed infrastructure (Heroku, Railway, Render) which provides basic governance
  - Document deployment architecture and require manual review for infrastructure changes
- **Remediation Timeline**: 90–180 days
- **Recommendation**: Define deployment infrastructure as code (Terraform or CDK) including networking, secrets management, and observability configuration.
- **Evidence**: Absence of any `.tf`, `cdk.json`, `template.yaml`, or Kubernetes manifests. Deployment defined only in `docker-compose.yml`, `app.json`, `netlify.toml`.

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: CI pipeline (`.github/workflows/ci.yml`) runs `pnpm test` (3 unit tests) and `pnpm build` on push. CD pipeline (`.github/workflows/cd.yml`) builds and pushes Docker images on version tags. No API contract testing, no consumer-driven contract tests, no OpenAPI validation, no breaking change detection.
- **Gap**: API changes are not validated against contracts in CI. Breaking changes to agent-facing APIs would not be caught before production deployment.
- **Compensating Controls**:
  - Add API integration tests that validate response shapes
  - Pin agent tool bindings to specific API versions
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add API contract tests (Postman/Newman collections or Pact tests) to the CI pipeline. Validate that API responses match expected schemas.
- **Evidence**: `.github/workflows/ci.yml` (no contract tests), `.github/workflows/cd.yml` (no validation gates)

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The CD pipeline builds and pushes versioned Docker images (semver tags). This provides a basic rollback mechanism (revert to previous image tag). However, there is no automated rollback trigger, no canary deployment, no blue/green deployment, and no feature flags. Database migrations are forward-only with no documented rollback procedure.
- **Gap**: Rollback requires manual intervention (update Docker image tag). No automated rollback on error rate increase. Database migrations complicate rollback.
- **Compensating Controls**:
  - Pin deployments to specific image tags and maintain a "last known good" tag
  - Test database migration backward compatibility before deployment
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement automated rollback triggers (e.g., health check failures reverting to previous image). Add database migration rollback scripts.
- **Evidence**: `.github/workflows/cd.yml` (versioned image tags), `prisma/migrations/` (forward-only migrations)

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Test coverage is minimal: 3 unit tests in `src/lib/__tests__/` (charts, detect, format utilities) and 6 Cypress E2E tests covering login, user management, and basic API operations (team, user, website CRUD). The 70+ API route handlers have very limited automated test coverage.
- **Gap**: Most API endpoints used by agents have no automated test coverage. Input validation, error responses, and edge cases are not systematically tested.
- **Compensating Controls**:
  - Prioritize API tests for the endpoints agents will consume most
  - Use the existing Cypress E2E framework to add API-level tests
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Expand the Cypress API test suite to cover all agent-facing endpoints. Add unit tests for permission logic and query functions.
- **Evidence**: `src/lib/__tests__/` (3 unit tests), `cypress/e2e/` (6 E2E tests), `jest.config.ts`, `.github/workflows/ci.yml`

#### ENG-Q5: Encryption at Rest — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No encryption-at-rest configuration is defined in the repository. The PostgreSQL instance in `docker-compose.yml` uses default settings without encryption configuration. No KMS key references, no encrypted volume definitions, no database encryption settings. Encryption at rest would depend entirely on the deployment platform's defaults.
- **Gap**: No explicit encryption-at-rest configuration. Data stored in PostgreSQL and ClickHouse is not guaranteed to be encrypted unless the hosting platform provides it by default.
- **Compensating Controls**:
  - Deploy on platforms that provide encryption at rest by default (AWS RDS, managed PostgreSQL services)
  - Configure volume-level encryption at the infrastructure layer
- **Remediation Timeline**: 30–60 days
- **Recommendation**: When deploying to production, use managed database services with encryption at rest enabled (e.g., RDS with KMS). Document encryption requirements for self-hosted deployments.
- **Evidence**: `docker-compose.yml` (no encryption config), absence of KMS or encryption configuration in any file

---

## INFOs — Architecture and Design Inputs

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Write endpoints (POST/PUT/DELETE) do not implement idempotency keys. No `Idempotency-Key` header support, no deduplication logic. However, since agent_scope is read-only, this is informational.
- **Implication**: If agent scope expands to write-enabled in the future, idempotency must be implemented for all write endpoints to prevent duplicate operations from agent retries.
- **Recommendation**: Plan for idempotency key support on write endpoints if write-enabled agent access is needed.
- **Evidence**: `src/app/api/websites/[websiteId]/route.ts` (no idempotency logic), absence of idempotency middleware

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: All API responses use JSON format with consistent serialization via `Response.json()`. No XML or binary formats. Well-structured for LLM consumption.
- **Implication**: JSON responses are optimal for agent consumption. No format adaptation needed.
- **Recommendation**: Maintain JSON as the standard response format.
- **Evidence**: `src/lib/response.ts`, `src/app/api/websites/[websiteId]/route.ts`

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limit headers (`X-RateLimit-Remaining`, `Retry-After`) are returned in API responses. No rate limit documentation exists. The `next.config.ts` configures CORS and cache headers but no rate limit headers.
- **Implication**: Agents cannot self-throttle based on rate limit feedback from the API.
- **Recommendation**: When rate limiting is implemented (STATE-Q5), include standard rate limit headers in responses.
- **Evidence**: `next.config.ts` (no rate limit headers configured)

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO (read-only agents do not execute write workflows)
- **Finding**: No saga pattern, compensation logic, or explicit undo endpoints exist. The user deletion in `src/queries/prisma/user.ts` uses a transaction for cascading deletes but no compensation for partial failures in multi-step operations.
- **Implication**: If agent scope expands to write-enabled, compensation/rollback mechanisms must be implemented for multi-step workflows.
- **Recommendation**: Plan for compensation patterns if write-enabled agent access is needed.
- **Evidence**: `src/queries/prisma/user.ts` (transaction-based deletion, no compensation)

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered (agent_scope read-only).

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits, maximum records per operation, or spend limits. Bulk operations are not bounded. However, read-only agents cannot modify records.
- **Implication**: If agent scope expands to write-enabled, transaction limits are needed to prevent catastrophic bulk operations.
- **Recommendation**: Plan for configurable per-agent operation limits if write scope is introduced.
- **Evidence**: Absence of any transaction limit configuration in source code

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered (agent_scope read-only).

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered (agent_scope read-only).

### DATA-Q2: Data Residency and Sovereignty ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY for read-only scope, but downgraded to INFO based on analysis.
- **Finding**: No data residency configuration or region constraints are defined in the repository. The application can be deployed anywhere (Docker-based). Data residency depends entirely on where the operator deploys the instance. The application itself is privacy-focused (no cookies, hashed session IDs) but does collect IP-derived geolocation data (country, region, city) which could be subject to GDPR.
- **Implication**: Operators deploying in EU regions must ensure the database is co-located. An agent sending analytics data to an LLM in a different region may have compliance implications for EU deployments.
- **Recommendation**: Document data residency requirements for operators. Consider adding region-awareness configuration for agent integrations.
- **Evidence**: `prisma/schema.prisma` (Session model with country, region, city fields), `docker-compose.yml` (no region configuration), `src/app/api/send/route.ts` (collects geo data)

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality scoring, completeness metrics, or freshness SLAs are defined. The application relies on Zod validation for input quality but has no monitoring of data completeness or staleness.
- **Implication**: Agents reasoning on analytics data have no signal about data quality or completeness.
- **Recommendation**: Consider adding data freshness indicators to API responses for analytics endpoints.
- **Evidence**: `src/app/api/send/route.ts` (Zod input validation), absence of data quality monitoring

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: BLOCKER
- **Finding**: The application exposes 70+ REST API route handlers under `src/app/api/` covering auth, admin, websites, teams, users, links, pixels, reports, realtime, and data collection. All implemented as Next.js App Router route handlers. No API documentation, no endpoint catalog, no usage examples.
- **Gap**: No documented API interface. Integration requires source code reverse-engineering.
- **Recommendation**: Generate an OpenAPI 3.x specification from existing routes and Zod schemas.
- **Evidence**: `src/app/api/` directory structure (70+ route files)

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, GraphQL schema, or equivalent machine-readable specification exists.
- **Gap**: Agent tool generation requires manual work — no automated tool definition generation possible.
- **Recommendation**: Generate OpenAPI spec using `zod-to-openapi` or similar tooling.
- **Evidence**: Absence of spec files in repository

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: Consistent `{error: {message, code, status}}` structure across all error responses (400, 401, 403, 404, 500). Machine-readable error codes provided.
- **Gap**: Missing `retryable` field to distinguish retriable from terminal errors.
- **Recommendation**: Add `retryable: boolean` to error response schema.
- **Evidence**: `src/lib/response.ts`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No idempotency key support on write endpoints.
- **Gap**: Write endpoints are not idempotent (informational for read-only scope).
- **Recommendation**: Plan for idempotency if write scope is introduced.
- **Evidence**: `src/app/api/websites/[websiteId]/route.ts`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: All responses are JSON via `Response.json()`. Well-structured for agent consumption.
- **Gap**: None — JSON is optimal.
- **Recommendation**: Maintain JSON format.
- **Evidence**: `src/lib/response.ts`

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has operations >30s OR long-running workflows
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: The application integrates with Kafka for event streaming (`src/lib/kafka.ts`) and publishes analytics events to Kafka topics. However, these events are internal data pipeline events (analytics ingestion), not state-change webhooks or notifications that external consumers (agents) can subscribe to.
- **Gap**: Event streaming exists for internal analytics pipeline but no webhook or event notification system for external consumers to subscribe to state changes.
- **Recommendation**: Consider adding webhook support or EventBridge integration if agents need to react to state changes (e.g., new website added, report completed).
- **Evidence**: `src/lib/kafka.ts`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit headers or documentation. No `X-RateLimit-Remaining` or `Retry-After` in responses.
- **Gap**: Agents cannot self-throttle based on API feedback.
- **Recommendation**: Add rate limit headers when rate limiting is implemented.
- **Evidence**: `next.config.ts`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: The application supports bearer token authentication via encrypted JWTs. Authentication flow: login with username/password → receive encrypted JWT token → pass as `Authorization: Bearer <token>` on subsequent requests. Redis-backed session keys provide alternative auth path. However, this is designed for human user login flows — there is no OAuth2 client credentials flow, no API key authentication with principal attribution, no mTLS, and no service account concept. An agent would need to use a human user's credentials to authenticate.
- **Gap**: No machine identity authentication. Agents must authenticate using human-style username/password login. No way to distinguish agent principals from human principals in audit. No client credentials grant or API key mechanism.
- **Recommendation**: Implement API key authentication with per-key principal attribution, or add an OAuth2 client credentials flow for machine-to-machine access.
- **Evidence**: `src/lib/auth.ts`, `src/lib/jwt.ts`, `src/app/api/auth/login/route.ts`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: Role-based permissions exist but are coarse-grained. The `view-only` role provides read-only access but the standard `user` role grants all website/team CRUD.
- **Gap**: No fine-grained per-resource scoping for agent identities.
- **Recommendation**: Create dedicated agent roles with minimal permissions.
- **Evidence**: `src/lib/constants.ts`, `src/permissions/`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: Action-level permission functions exist (`canView`, `canUpdate`, `canDelete`) but the role model bundles read+write for the `user` role.
- **Gap**: Cannot grant read-without-write at the user role level for owned resources.
- **Recommendation**: Use `view-only` or `team-view-only` roles for agent identities.
- **Evidence**: `src/permissions/website.ts`, `src/lib/constants.ts`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: The application supports bearer token propagation and extracts user identity from JWT tokens. However, there is no concept of "acting on behalf of" another user, no token exchange flows, and no distinction between agent-as-self vs agent-on-behalf-of-user.
- **Gap**: No identity delegation or on-behalf-of flows. Single-identity model only.
- **Recommendation**: Consider OAuth2 token exchange if on-behalf-of agent scenarios are needed.
- **Evidence**: `src/lib/auth.ts`, `src/lib/jwt.ts`

#### AUTH-Q5: Credential Management
- **Severity**: RISK-QUALITY
- **Finding**: Application secret (`APP_SECRET`) is passed via environment variable. The `docker-compose.yml` contains hardcoded placeholder credentials (`POSTGRES_PASSWORD: umami`, `APP_SECRET: replace-me-with-a-random-string`). No secrets manager integration (no Secrets Manager, no Vault client). Production deployments rely on environment variables for all secrets.
- **Gap**: No secrets management system. Credentials are in environment variables and Docker Compose files. No rotation mechanism.
- **Recommendation**: Integrate a secrets manager (AWS Secrets Manager or HashiCorp Vault) for production deployments. Remove hardcoded credentials from `docker-compose.yml`.
- **Evidence**: `docker-compose.yml` (hardcoded credentials), `src/lib/crypto.ts` (reads APP_SECRET from env), `podman/env.sample`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No structured audit logging. Only `debug` library diagnostic output.
- **Gap**: No audit trail for actions performed via the API.
- **Recommendation**: Add audit logging middleware to `parseRequest()`.
- **Evidence**: `src/lib/auth.ts`, `src/lib/request.ts`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: Soft-delete exists but `checkAuth()` does not validate `deletedAt`. No token revocation.
- **Gap**: Cannot immediately suspend an agent identity and invalidate its active sessions.
- **Recommendation**: Add `deletedAt` check in `checkAuth()`. Implement token blacklisting.
- **Evidence**: `src/lib/auth.ts`, `prisma/schema.prisma`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No compensation/rollback patterns. Transactions used for cascading deletes only.
- **Gap**: No multi-step operation rollback (informational for read-only scope).
- **Recommendation**: Plan compensation patterns for write-enabled scope.
- **Evidence**: `src/queries/prisma/user.ts`

#### STATE-Q2: Queryable Current State
- **Severity**: PASS (no finding)
- **Finding**: The application exposes GET endpoints for all resources (websites, users, teams, reports, segments, links, pixels) that allow querying current state. Each entity has standard read operations accessible via the REST API with proper authentication.
- **Gap**: None — current state is queryable via REST API.
- **Recommendation**: None needed.
- **Evidence**: `src/app/api/websites/[websiteId]/route.ts` (GET), `src/app/api/admin/users/route.ts` (GET with pagination)

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Trigger requires agent_scope write-enabled AND persistent state; agent_scope is `read-only`.
- **Trigger**: agent_scope is write-enabled AND service has persistent state
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has external dependencies (calls other services or external APIs)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No rate limiting at any layer — no middleware, no API gateway throttling, no WAF rules.
- **Gap**: Unlimited request rate. Agent or attacker traffic could overwhelm the system.
- **Recommendation**: Implement rate limiting middleware using Redis as a backing store.
- **Evidence**: `package.json`, `next.config.ts`, absence of rate limiting code

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No transaction limits configured.
- **Gap**: No per-agent operation limits (informational for read-only scope).
- **Recommendation**: Plan for transaction limits if write scope is introduced.
- **Evidence**: Absence of limit configuration

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. agent_scope is `read-only`.
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. agent_scope is `read-only`.
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: A Docker Compose-based testing environment exists in `cypress/docker-compose.yml` with PostgreSQL and the umami application for E2E testing. Seed data scripts exist in `scripts/seed/`. However, there is no production-equivalent staging environment configuration, no synthetic data generators for realistic scale, and no documented sandbox environment.
- **Gap**: Testing environment exists but is not production-equivalent. No staging environment with production data shape.
- **Recommendation**: Document a staging environment setup process. Enhance seed data generators to produce production-scale data shapes.
- **Evidence**: `cypress/docker-compose.yml`, `scripts/seed/`, `scripts/seed-data.ts`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: Stage A = Yes (stores user passwords, usernames; collects IP-derived geo data). agent_scope is "read-only".
- **Finding**: The system stores sensitive data: user passwords (bcrypt hashed), usernames, and IP-derived geolocation (country, region, city). The application is privacy-focused and implements good practices — passwords are excluded from query results by default (`findUser` uses explicit `select` excluding password unless `includePassword: true`), admin user list endpoint uses `omit: { password: true }`. Session data uses hashed identifiers rather than raw IPs.
- **Gap**: B1 (API response scoping): Password is properly excluded. Good practice. B1 = CLEAR. B2 (Access differentiation): The role system differentiates admin from user, but all authenticated users have access to the same analytics data for their websites — no differentiation between sensitive and non-sensitive data access scopes. B2 = RISK-SAFETY. B3 (Classification metadata): No formal data classification tags or field-level sensitivity annotations. B3 = INFO.
- **Recommendation**: Implement OAuth scopes or fine-grained permissions that distinguish access levels for analytics data vs user management data.
- **Evidence**: `src/queries/prisma/user.ts` (password exclusion), `prisma/schema.prisma` (User.password field), `src/app/api/admin/users/route.ts` (omit password)

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO based on analysis. The application is self-hosted (operators choose deployment region). Privacy-focused design minimizes PII collection.
- **Finding**: No data residency configuration. Deployment region is operator's choice. Analytics data includes IP-derived geolocation but not raw IPs.
- **Gap**: No explicit residency constraints defined. Operator responsibility.
- **Recommendation**: Document data residency considerations for operators in EU/regulated environments.
- **Evidence**: `prisma/schema.prisma` (Session geo fields), `docker-compose.yml`

#### DATA-Q3: Selective Query Support
- **Severity**: PASS (no finding)
- **Finding**: The application supports pagination via `DEFAULT_PAGE_SIZE` constant, `take`/`skip` parameters in Prisma queries, and accepts `page`/`pageSize` query parameters on list endpoints. The admin users endpoint and website list endpoints implement pagination. Analytics queries accept date range filters, limiting result sets.
- **Gap**: None — pagination and filtering are implemented.
- **Recommendation**: None needed.
- **Evidence**: `src/lib/request.ts` (DEFAULT_PAGE_SIZE), `src/app/api/admin/users/route.ts` (pagination), `src/queries/sql/` (date range filters)

#### DATA-Q4: System of Record Designations
- **Severity**: INFO
- **Finding**: This is a single self-hosted application that serves as its own system of record for analytics data, user accounts, websites, teams, and reports. There are no multi-system conflicts or competing data sources — all data originates and resides within this application.
- **Gap**: No formal SoR designations documented, though conflicts are unlikely given the single-system architecture.
- **Recommendation**: Document that this application is the authoritative source for its own analytics and configuration data if it becomes part of a larger ecosystem.
- **Evidence**: `prisma/schema.prisma` (all entity models), single-application architecture

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK-QUALITY
- **Finding**: All database models include `createdAt` (Timestamptz) and most include `updatedAt` (auto-managed by Prisma). Timestamps use UTC with timezone awareness. However, API responses do not include freshness signaling — no `Cache-Control` headers with data age, no `X-Data-Age` headers, no `consistency_level` field. The `next.config.ts` sets `Cache-Control: no-cache` on API routes, preventing stale cached data but providing no freshness context.
- **Gap**: Timestamps exist in data but API responses lack freshness signaling for agents to assess data currency.
- **Recommendation**: Add `X-Data-Age` or `last_refreshed` headers to analytics endpoints. Consider adding `consistency_level` field for ClickHouse queries (which may be eventually consistent).
- **Evidence**: `prisma/schema.prisma` (createdAt/updatedAt on all models), `next.config.ts` (Cache-Control: no-cache on API)

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: Debug logging outputs auth tokens and user objects without redaction. Kafka error handler serializes full errors.
- **Gap**: No PII masking in logs when debug mode is active.
- **Recommendation**: Redact sensitive fields from all log statements.
- **Evidence**: `src/lib/auth.ts`, `src/lib/kafka.ts`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics or freshness indicators.
- **Gap**: No data quality signaling to agents.
- **Recommendation**: Consider adding freshness indicators to analytics API responses.
- **Evidence**: Absence of data quality monitoring

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: No API versioning. No breaking change detection in CI. 14 Prisma migrations document schema evolution.
- **Gap**: Agent tool bindings could break silently on any deployment.
- **Recommendation**: Introduce API versioning and contract testing.
- **Evidence**: `src/app/api/` (no versioning), `prisma/migrations/`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Field names are semantically meaningful and human-readable. Database columns use descriptive names (`website_id`, `created_at`, `page_title`, `referrer_domain`, `utm_source`). API response fields are camelCase and self-explanatory (`websiteId`, `createdAt`, `pageTitle`). No legacy code abbreviations.
- **Implication**: LLM-based agents can reason about data fields without requiring a data dictionary.
- **Recommendation**: Maintain current naming conventions.
- **Evidence**: `prisma/schema.prisma` (field naming)

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal data catalog or metadata layer. The Prisma schema serves as implicit documentation of data structure.
- **Implication**: Agent tool builders must reference the Prisma schema to understand data models.
- **Recommendation**: Consider auto-generating data documentation from the Prisma schema.
- **Evidence**: `prisma/schema.prisma`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: No distributed tracing or structured logging. `debug` library for diagnostic output only.
- **Gap**: Agent-initiated requests cannot be traced through the system.
- **Recommendation**: Integrate OpenTelemetry and structured JSON logging.
- **Evidence**: `package.json` (no tracing deps), `src/lib/auth.ts` (debug library)

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: No alerting configuration. Basic Docker healthcheck only.
- **Gap**: No operational alerting for API degradation.
- **Recommendation**: Implement metrics collection and alerting thresholds.
- **Evidence**: `docker-compose.yml`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business outcome metrics are published. The application tracks analytics data (pageviews, events, sessions) as its core function, but does not emit metrics about its own operational outcomes (e.g., data ingestion success rate, report generation completion rate, user engagement with dashboards).
- **Gap**: No self-referential business metrics for monitoring agent interaction outcomes.
- **Recommendation**: Consider publishing custom metrics for data ingestion success rates, API response quality, and report generation completion as the system becomes agent-integrated.
- **Evidence**: Absence of custom metrics publishing code, no `cloudwatch.put_metric_data` or equivalent

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance
- **Severity**: RISK-QUALITY
- **Finding**: No IaC. Deployment via Docker Compose and PaaS configs only.
- **Gap**: Agent-facing infrastructure not governed by code, review, or drift detection.
- **Recommendation**: Define infrastructure as code.
- **Evidence**: Absence of IaC files, `docker-compose.yml`, `app.json`, `netlify.toml`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: CI runs tests and build. No API contract testing or breaking change detection.
- **Gap**: API changes not validated against contracts.
- **Recommendation**: Add contract tests to CI pipeline.
- **Evidence**: `.github/workflows/ci.yml`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: Versioned Docker images provide basic rollback mechanism. No automated triggers.
- **Gap**: Manual rollback only. Database migrations complicate rollback.
- **Recommendation**: Implement automated rollback on health check failures.
- **Evidence**: `.github/workflows/cd.yml`, `prisma/migrations/`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: 3 unit tests, 6 E2E tests for 70+ API routes. Minimal coverage.
- **Gap**: Most agent-facing endpoints untested.
- **Recommendation**: Expand API test suite.
- **Evidence**: `src/lib/__tests__/`, `cypress/e2e/`

#### ENG-Q5: Encryption at Rest
- **Severity**: RISK-QUALITY
- **Finding**: No encryption-at-rest configuration defined. Depends on deployment platform defaults.
- **Gap**: No explicit encryption guarantee for stored data.
- **Recommendation**: Use managed database services with encryption at rest.
- **Evidence**: `docker-compose.yml`

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| src/lib/auth.ts | AUTH-Q1, AUTH-Q2, AUTH-Q6, AUTH-Q7, DATA-Q6, OBS-Q1 |
| src/lib/jwt.ts | AUTH-Q1, AUTH-Q4 |
| src/lib/crypto.ts | AUTH-Q5 |
| src/lib/request.ts | AUTH-Q6, API-Q3 |
| src/lib/response.ts | API-Q3, API-Q5 |
| src/lib/constants.ts | AUTH-Q2, AUTH-Q3 |
| src/lib/kafka.ts | DATA-Q6 |
| src/lib/redis.ts | AUTH-Q7 |
| src/lib/password.ts | AUTH-Q1 |
| src/permissions/index.ts | AUTH-Q2, AUTH-Q3 |
| src/permissions/user.ts | AUTH-Q2, AUTH-Q3 |
| src/permissions/website.ts | AUTH-Q2, AUTH-Q3 |
| src/queries/prisma/user.ts | DATA-Q1, AUTH-Q7 |
| src/app/api/auth/login/route.ts | AUTH-Q1 |
| src/app/api/websites/[websiteId]/route.ts | API-Q1, API-Q4 |
| src/app/api/admin/users/route.ts | DATA-Q1 |
| src/app/api/send/route.ts | DATA-Q2, DATA-Q7 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| .github/workflows/ci.yml | ENG-Q2, ENG-Q4 |
| .github/workflows/cd.yml | ENG-Q3 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| Dockerfile | ENG-Q3 |
| docker-compose.yml | AUTH-Q5, ENG-Q5, OBS-Q2, STATE-Q5 |
| cypress/docker-compose.yml | HITL-Q3 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| next.config.ts | STATE-Q5, API-Q8 |
| prisma/schema.prisma | AUTH-Q7, STATE-Q3, DATA-Q1, DATA-Q2, DISC-Q2, DISC-Q3, HITL-Q1 |
| package.json | STATE-Q5, OBS-Q1 |
| app.json | ENG-Q1 |
| netlify.toml | ENG-Q1 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| package.json | OBS-Q1, STATE-Q5 |

### Test Files
| File | Questions Referenced |
|------|---------------------|
| src/lib/__tests__/ | ENG-Q4 |
| cypress/e2e/ | ENG-Q4 |
| scripts/seed/ | HITL-Q3 |
