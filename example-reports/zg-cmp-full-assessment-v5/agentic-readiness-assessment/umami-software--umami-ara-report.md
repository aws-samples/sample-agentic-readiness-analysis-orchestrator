# Agentic Readiness Assessment Report

**Target**: umami (.)
**Date**: 2026-04-30
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: monorepo (treated as single application — see note below)
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: typescript, analytics, web-app
**Context**: Self-hosted privacy-focused web analytics.
**Archetype Justification**: Umami owns persistent state in PostgreSQL (via Prisma) and ClickHouse, exposes full CRUD operations on business entities (websites, users, teams, reports, links, pixels), and includes substantial business logic (auth, permissions, team management, analytics aggregation). While it has heavy read-analytics queries, the CRUD surface disqualifies it from data-gateway.

> **Note**: Although `repo_type` is `monorepo`, this repository (Umami) is effectively a single full-stack Next.js application — not multiple independent services. It is assessed as a single application service. All 43 questions apply.

- **Surface flags**:
  - has_persistent_data_store: true (PostgreSQL via Prisma, ClickHouse, Redis)
  - has_http_rpc_surface: true (Next.js API routes under src/app/api/)
  - has_auth_surface: true (JWT auth, bearer tokens, role-based permissions)
  - has_write_operations: true (POST/DELETE endpoints, event collection)
  - has_logging_of_user_data: true (debug logging includes auth tokens and user payloads)

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 1 | **RISK-SAFETY**: 9 | **RISK-QUALITY**: 16 | **INFOs**: 16

Resolve the remaining blocker (AUTH-Q1) before any agent deployment — including pilots. Estimated runway: 30–90 days.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 1 |
| RISK-SAFETY | 9 |
| RISK-QUALITY | 16 |
| INFO | 16 |
| N/A | 0 |
| Not Evaluated (extended) | 1 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 8
**Extended Questions Not Triggered**: 1
**Questions N/A (repo_type: monorepo)**: 0
**Service Archetype**: stateful-crud (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: Umami uses JWT-based authentication exclusively designed for human users. The login endpoint (`POST /api/auth/login`) accepts username/password and returns an encrypted JWT token. Bearer token authentication via `checkAuth()` in `src/lib/auth.ts`. There is no OAuth2 client credentials flow, no API key with principal attribution for machine-to-machine auth, and no mTLS support. Share tokens exist for public dashboards but are not machine identity — they provide anonymous access to a specific website's data.
- **Gap**: No machine identity authentication mechanism exists. An agent would need to use a human user's credentials (username/password) to obtain a JWT token, which violates the principle of separate machine identity and makes audit attribution impossible.
- **Remediation**:
  - **Immediate**: Create an API key authentication mechanism with principal attribution. Add an `api_keys` table to the Prisma schema with fields: `id`, `userId`, `key` (hashed), `name`, `permissions`, `createdAt`, `lastUsedAt`, `expiresAt`, `isActive`. Add middleware to `checkAuth()` to accept `X-API-Key` header alongside Bearer tokens.
  - **Target State**: Agents authenticate via API keys tied to a specific user/service account with principal attribution in all request contexts. Each agent instance has its own key, revocable independently.
  - **Estimated Effort**: Medium (2–4 weeks)
  - **Dependencies**: AUTH-Q7 (agent identity suspension depends on having machine identities to suspend)
- **Evidence**: `src/lib/auth.ts`, `src/lib/jwt.ts`, `src/lib/crypto.ts`, `src/app/api/auth/login/route.ts`

**Remediation Prioritization**: Resolve AUTH-Q1 (machine identity) first — you cannot enforce per-agent access controls without knowing who is calling. DATA-Q1 is no longer a BLOCKER (see INFOs); the application's Prisma projections already exclude password fields from API responses, and its RBAC provides access-control differentiation. After AUTH-Q1 is resolved, a scoped read-only pilot is viable.

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Application-level RBAC exists with well-defined roles: `admin` (all permissions), `user` (website/team CRUD), `view-only` (no permissions), and team-level roles (`team-owner`, `team-manager`, `team-member`, `team-view-only`). The `view-only` role provides a read-only scope. However, there is no agent-specific role or permission model — an agent would need to be assigned one of the human roles. The `admin` role has wildcard `all` permission which is too broad for any agent.
- **Gap**: While RBAC exists with granular roles, there is no mechanism to create agent-specific permission sets that scope access to specific resources (e.g., "read analytics for website X only, not website Y"). The `view-only` role is the closest fit for a read-only agent but applies globally.
- **Compensating Controls**:
  - Assign the `view-only` role to read-only agent identities to limit permissions scope
  - Use team-level `team-view-only` role to restrict agent access to specific website groups
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement agent-specific roles with resource-level scoping (e.g., "agent can read analytics for websiteId X only"). Extend the permission model to support per-resource grants.
- **Evidence**: `src/lib/constants.ts` (ROLE_PERMISSIONS), `src/permissions/website.ts`, `src/permissions/user.ts`, `src/permissions/team.ts`

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Fine-grained permission checks exist: `canViewWebsite`, `canUpdateWebsite`, `canDeleteWebsite`, `canCreateWebsite`, `canViewUser`, `canUpdateUser`, `canDeleteUser`, `canViewTeam`, `canUpdateTeam`, `canDeleteTeam`. Action-level checks are performed before each API operation. However, the permission system is designed for human roles, not agent scoping — an agent could be granted `view-only` but there is no mechanism to restrict to specific resource types (e.g., "can view websites but not users").
- **Gap**: Action-level authorization exists and is well-implemented, but it is scoped by human role, not by agent capability. Cannot restrict an agent to specific resource types within a role.
- **Compensating Controls**:
  - Use `view-only` role to prevent all write operations for read-only agents
  - Use team-level roles to restrict access scope to specific website groups
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add capability-based permissions that allow scoping agent access to specific resource types and actions beyond what role-level RBAC provides.
- **Evidence**: `src/permissions/website.ts`, `src/permissions/user.ts`, `src/permissions/team.ts`

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No structured audit logging exists for any operations. The only logging is via the `debug` npm package (`debug('umami:auth')`) which outputs to stderr when the `DEBUG` environment variable is set. In `src/lib/auth.ts`, the debug log includes `{ token, payload, authKey, shareToken, user }` which is diagnostic, not audit. No CloudTrail configuration. No immutable log storage. No log file validation.
- **Gap**: No audit trail exists for agent-initiated or any other operations. Cannot prove who accessed what data or when. No immutable storage prevents log tampering.
- **Compensating Controls**:
  - Deploy a reverse proxy (e.g., nginx, API Gateway) in front of Umami that logs all API requests with principal attribution
  - Enable structured access logging at the Next.js middleware level with write-once storage
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement structured audit logging middleware that captures: timestamp, authenticated principal, action (HTTP method + path), resource ID, and outcome (status code). Store logs in an immutable destination (S3 with Object Lock, CloudWatch Logs with retention policy).
- **Evidence**: `src/lib/auth.ts` (debug logging only), absence of any audit logging configuration

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: User accounts can be soft-deleted via the `deletedAt` field in the Prisma schema, and admins can manage users via `/api/admin/users`. However, there is no immediate suspension mechanism — soft deletion sets a timestamp but the `checkAuth()` function in `src/lib/auth.ts` does not check `deletedAt`. Redis-based auth keys have optional expiration but no forced revocation endpoint. No API key revocation mechanism exists (no API keys exist per AUTH-Q1).
- **Gap**: Cannot immediately suspend a misbehaving agent identity. Even if a user is soft-deleted, existing JWT tokens remain valid until they expire. No forced token invalidation.
- **Compensating Controls**:
  - Add a `deletedAt` check to the `checkAuth()` function to reject requests from soft-deleted users
  - If using Redis auth, implement a key deletion endpoint for immediate session invalidation
- **Remediation Timeline**: 15–30 days
- **Recommendation**: Add `deletedAt` validation to `checkAuth()`. Implement a force-logout endpoint that deletes all Redis auth keys for a given user. When API keys are implemented (AUTH-Q1), include an `isActive` flag with an admin toggle endpoint.
- **Evidence**: `src/lib/auth.ts` (checkAuth function), `prisma/schema.prisma` (User model with deletedAt), `src/lib/redis.ts`

#### STATE-Q1: Compensation and Rollback ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No saga pattern, two-phase commit, or compensating transaction mechanisms exist. Prisma's `transaction()` function in `src/lib/prisma.ts` provides database-level transactions for atomicity but not multi-step workflow compensation. The `deleteWebsite` operation uses soft delete (`deletedAt` timestamp) which provides limited undo capability. The website reset endpoint (`/api/websites/[websiteId]/reset`) sets `resetAt` timestamp rather than deleting data.
- **Gap**: No compensation or rollback capability for multi-step operations. If a read-only agent were later expanded to write scope, partial failures would leave the system in inconsistent state.
- **Compensating Controls**:
  - Maintain read-only agent scope — compensation is not needed for read operations
  - Soft delete patterns already exist for websites, users, teams — extend to other entities
- **Remediation Timeline**: 60–90 days (when write scope is planned)
- **Recommendation**: Before expanding to write-enabled agent scope, implement explicit undo/compensation endpoints for all write operations. The existing soft-delete pattern is a good foundation — extend it to all state-changing operations.
- **Evidence**: `src/lib/prisma.ts` (transaction function), `src/app/api/websites/[websiteId]/route.ts` (soft delete), `prisma/schema.prisma` (deletedAt fields)

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No circuit breaker patterns found. No retry decorators, no exponential backoff, no `@CircuitBreaker` annotations. Kafka client has connection timeout (`CONNECT_TIMEOUT=5000`) and send timeout (`SEND_TIMEOUT=3000`) but no circuit breaker. Prisma and Redis clients have no explicit timeout or resilience configuration. ClickHouse client has no timeout configuration in the codebase.
- **Gap**: If a database or external dependency fails, the application will propagate failures to all callers including agents. No graceful degradation. Agent-initiated requests could cascade failures through the database layer.
- **Compensating Controls**:
  - Deploy database connection pooling (PgBouncer) to limit connection exhaustion from agent traffic
  - Configure timeouts at the reverse proxy / load balancer level
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add connection timeout configuration to Prisma and ClickHouse clients. Implement retry with exponential backoff for transient database errors. Add a circuit breaker pattern for the ClickHouse connection (which is optional and can degrade gracefully).
- **Evidence**: `src/lib/kafka.ts` (timeout constants only), `src/lib/prisma.ts` (no timeout config), `src/lib/clickhouse.ts` (no timeout config), `src/lib/redis.ts` (no timeout config)

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No rate limiting exists at any layer. No API Gateway throttle settings. No WAF rate rules. No application-level rate limiting middleware. The application has bot detection (`isbot` check in `/api/send`) and IP blocking (`IGNORE_IP` env var) but these are not rate limits. CORS is configured with `Access-Control-Allow-Origin: *` in `next.config.ts`, allowing unrestricted cross-origin access. The `Cache-Control: no-cache` header on API routes means every request hits the backend.
- **Gap**: A runaway agent loop or misconfigured agent could send unlimited requests at machine speed, overwhelming PostgreSQL and ClickHouse. No protection against traffic storms.
- **Compensating Controls**:
  - Deploy a reverse proxy (nginx, CloudFront, API Gateway) with rate limiting before the Umami instance
  - Add `express-rate-limit` or equivalent middleware to the Next.js API routes
- **Remediation Timeline**: 15–30 days
- **Recommendation**: Implement rate limiting at two layers: (1) infrastructure layer via reverse proxy or API Gateway with per-IP and per-API-key throttling, and (2) application layer via middleware with configurable limits per route and per identity.
- **Evidence**: `next.config.ts` (CORS config, no rate limiting), `src/app/api/send/route.ts` (bot check only), absence of any rate limiting middleware

#### DATA-Q2: Data Residency and Sovereignty ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No data residency configuration exists. The database URL is environment-configured (`DATABASE_URL` env var) but no region enforcement or validation. No GDPR/LGPD compliance references in code. No cross-region replication settings. The privacy-focused design of Umami (IP hashing for session IDs, no direct IP storage in PostgreSQL) mitigates some residency concerns. However, geolocation data (country, region, city), browser fingerprints, and arbitrary event/session data are stored without residency controls.
- **Gap**: No data residency controls. An agent reading data from Umami and transmitting it to an LLM provider in a different region could create compliance issues for deployments subject to GDPR/LGPD.
- **Compensating Controls**:
  - Deploy Umami and any agent/LLM infrastructure in the same region
  - Use Amazon Bedrock with in-region inference to avoid cross-region data transmission
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document data residency requirements based on deployment jurisdiction. Configure database-level region constraints. If agents will send data to LLM providers, implement data filtering to exclude geolocation and any potentially PII fields from LLM prompts.
- **Evidence**: `docker-compose.yml` (no region config), `prisma/schema.prisma` (no residency metadata), `src/lib/detect.ts` (geolocation processing)

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Debug logging in `src/lib/auth.ts` logs the full auth context: `log({ token, payload, authKey, shareToken, user })` — this includes JWT tokens and user objects. The error handler in `src/app/api/send/route.ts` uses `serializeError(e)` and `console.log(error)` which could include request payload data (URLs, referrers, user agents). The Kafka error handler also logs `serializeError(e)`. No log scrubbing middleware. No PII masking libraries. No CloudWatch log filters or Macie integration.
- **Gap**: Auth tokens, user objects, and potentially request data containing visitor information (URLs, referrers, geolocation) can leak into logs. While Umami's privacy-focused design minimizes PII collection, the logging pipeline has no redaction controls.
- **Compensating Controls**:
  - Restrict `DEBUG` environment variable to development only — do not enable `umami:auth` in production
  - Replace `console.log(error)` in `/api/send` with a sanitized error logger that strips request data
- **Remediation Timeline**: 15–30 days
- **Recommendation**: Implement a centralized logging utility that redacts sensitive fields (tokens, passwords, user objects, IP addresses) before output. Replace all `debug()` calls that include auth tokens with sanitized versions. Replace `console.log(error)` in catch blocks with structured logging that excludes request payloads.
- **Evidence**: `src/lib/auth.ts` (line: `log({ token, payload, authKey, shareToken, user })`), `src/app/api/send/route.ts` (line: `console.log(error)`), `src/lib/kafka.ts` (line: `console.log('KAFKA ERROR:', serializeError(e))`)

### RISK-QUALITY — Address as Capacity Allows

#### AUTH-Q5: Credential Management — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: `APP_SECRET` is sourced from environment variables (`process.env.APP_SECRET || process.env.DATABASE_URL`). The fallback to `DATABASE_URL` as encryption secret is a security concern. No AWS Secrets Manager or HashiCorp Vault. `docker-compose.yml` has hardcoded defaults: `POSTGRES_USER=umami`, `POSTGRES_PASSWORD=umami`, `APP_SECRET='replace-me-with-a-random-string'`.
- **Gap**: No secrets management system. Hardcoded defaults in docker-compose. APP_SECRET falls back to DATABASE_URL.
- **Compensating Controls**:
  - Ensure APP_SECRET is always explicitly set in production
  - Use deployment-level secrets management (AWS Secrets Manager, Vault) external to the application
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Remove DATABASE_URL fallback from `secret()` function. Integrate with a secrets management system. Document that APP_SECRET must be unique, random, and never the same as DATABASE_URL.
- **Evidence**: `src/lib/crypto.ts` (secret function), `docker-compose.yml` (hardcoded credentials)

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, Swagger, AsyncAPI, or Smithy specification files found in the repository. API contracts exist only as Zod validation schemas in `src/lib/schema.ts` and inline schemas in individual route files. These provide typed validation but are not machine-readable API specifications that agent frameworks can consume.
- **Gap**: Without a machine-readable API spec, every agent tool integration requires manual authoring. API behavior changes cannot be detected automatically.
- **Compensating Controls**:
  - Generate OpenAPI spec from Zod schemas using `zod-to-openapi` or similar library
  - Manually document the most critical read endpoints for initial agent integration
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `@asteasolutions/zod-to-openapi` to generate an OpenAPI spec from existing Zod schemas. Publish the spec at `/api/openapi.json`. This leverages existing validation schemas rather than maintaining a separate spec.
- **Evidence**: `src/lib/schema.ts` (Zod schemas), absence of any OpenAPI/Swagger files in the repository

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Consistent structured error responses exist in `src/lib/response.ts` with format: `{ error: { message, code, status } }`. Error codes include `bad-request` (400), `unauthorized` (401), `forbidden` (403), `not-found` (404), `server-error` (500). Zod validation errors are returned via `badRequest(z.treeifyError(result.error))` providing detailed field-level error information.
- **Gap**: Missing `retryable` boolean or error category field. Agents cannot programmatically distinguish retriable errors (server overload, timeout) from terminal errors (invalid input, permission denied) without parsing the status code.
- **Compensating Controls**:
  - Agents can use HTTP status codes as a proxy: 4xx = terminal, 5xx = retriable
  - Document retry guidance per error code in API documentation
- **Remediation Timeline**: 15–30 days
- **Recommendation**: Add a `retryable: boolean` field to all error responses. 400/401/403/404 → `retryable: false`. 429/500/502/503 → `retryable: true`. This is a small change to `src/lib/response.ts`.
- **Evidence**: `src/lib/response.ts`, `src/lib/request.ts` (Zod error handling)

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: `docker-compose.yml` provides a local testing environment with PostgreSQL. Cypress e2e tests exist in `cypress/` directory with test fixtures for users, teams, and websites. Seed data scripts exist (`scripts/seed-data.ts`, `scripts/seed/`) with synthetic data generators for blog and SaaS site profiles. No separate staging environment configuration in the repo. Docker compose uses default credentials (`POSTGRES_USER=umami`, `POSTGRES_PASSWORD=umami`).
- **Gap**: No production-equivalent staging environment configuration. Docker compose provides a functional local environment but not a staging environment with production-like data shape. Seed scripts generate synthetic data but not at production scale.
- **Compensating Controls**:
  - Use docker-compose with seed data for initial agent testing
  - Create a dedicated staging deployment with anonymized production data shape
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a `docker-compose.staging.yml` with production-equivalent PostgreSQL and ClickHouse configurations. Extend seed scripts to generate data at production-representative scale. Add staging environment to CI/CD pipeline.
- **Evidence**: `docker-compose.yml`, `cypress/` directory, `scripts/seed-data.ts`, `scripts/seed/`

#### STATE-Q2: Queryable Current State — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: GET endpoints exist for all major entities (websites, users, teams, reports, sessions, events) with extensive filter, pagination, and date range support. State is fully queryable via REST API. `pagedQuery()` and `pagedRawQuery()` provide structured paginated access with `DEFAULT_PAGE_SIZE=20`.
- **Gap**: Minimal — state is well-exposed. Some entities require multiple API calls to reconstruct full context. No aggregate/summary endpoints optimized for agent consumption patterns.
- **Compensating Controls**:
  - Agents can use existing paginated endpoints with appropriate filters
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Consider adding aggregate/summary endpoints for common agent query patterns (e.g., "website overview" combining stats, top pages, and recent events in one call).
- **Evidence**: `src/app/api/websites/route.ts`, `src/lib/prisma.ts` (pagedQuery), `src/lib/clickhouse.ts` (pagedRawQuery)

#### DATA-Q3: Selective Query Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Well-implemented pagination, filtering, and sorting. Pagination parameters (`page`, `pageSize`) defined in `src/lib/schema.ts` with `DEFAULT_PAGE_SIZE=20`. Extensive filter parameters: path, referrer, title, query, os, browser, device, country, region, city, tag, hostname, language, event. Date range filtering (`startAt`, `endAt`, `unit`, `timezone`). Sorting (`orderBy`, `sortDescending`). Both Prisma and ClickHouse implement paged queries via `pagedQuery()` and `pagedRawQuery()`.
- **Gap**: Minimal — the implementation is solid. Minor gap: no maximum `pageSize` enforcement — an agent could request `pageSize=999999` to retrieve unbounded results.
- **Compensating Controls**:
  - Add `pageSize` maximum validation (e.g., max 1000) in the schema
- **Remediation Timeline**: 7–15 days
- **Recommendation**: Add `.max(1000)` to the `pageSize` Zod schema parameter to prevent unbounded result sets.
- **Evidence**: `src/lib/schema.ts` (pagingParams, filterParams), `src/lib/prisma.ts` (pagedQuery, pagedRawQuery), `src/lib/clickhouse.ts` (pagedRawQuery)

#### DATA-Q4: System of Record Designations — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Umami is a self-contained application — PostgreSQL is the authoritative store for metadata (users, websites, teams, reports, segments, links, pixels) and ClickHouse is the authoritative store for analytics data (events, sessions). The `runQuery()` function in `src/lib/db.ts` routes queries to either Prisma (PostgreSQL) or ClickHouse based on configuration. No external master data management process or system-of-record documentation.
- **Gap**: No explicit documentation of which data store is authoritative for which entities. When both PostgreSQL and ClickHouse are enabled, session data may exist in both stores with potential inconsistencies.
- **Compensating Controls**:
  - Document the data store ownership: PostgreSQL = metadata, ClickHouse = analytics events
- **Remediation Timeline**: 7–15 days
- **Recommendation**: Add a data architecture document clarifying system-of-record designations for each entity type.
- **Evidence**: `src/lib/db.ts` (runQuery routing), `prisma/schema.prisma`, `db/clickhouse/schema.sql`

#### DATA-Q5: Temporal Metadata and Freshness — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Good temporal metadata: `createdAt` (default `now()`) and `updatedAt` (`@updatedAt`) fields on most Prisma models. Timestamps use `Timestamptz(6)` for timezone awareness in PostgreSQL. ClickHouse uses `DateTime('UTC')` for consistent UTC storage. ClickHouse materialized views aggregate data hourly. API routes return `Cache-Control: no-cache` header, meaning data is always fetched fresh.
- **Gap**: No data freshness signaling headers (no `X-Data-Age`, `last_refreshed`, or `consistency_level` fields in API responses). ClickHouse materialized views introduce eventual consistency — agents cannot determine if aggregated data is up-to-date. No `Cache-Control` with `max-age` for data endpoints.
- **Compensating Controls**:
  - Agents can treat all Umami API responses as near-real-time (no caching, `Cache-Control: no-cache`)
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add response headers or metadata fields indicating data freshness. For ClickHouse-backed endpoints, include a `dataAge` or `lastAggregated` field. For real-time endpoints, include `consistency: strong`.
- **Evidence**: `prisma/schema.prisma` (createdAt, updatedAt fields), `db/clickhouse/schema.sql` (DateTime('UTC')), `next.config.ts` (Cache-Control: no-cache)

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Prisma migration files exist (`prisma/migrations/` with 14 versioned migrations from `01_init` through `14_add_link_and_pixel`). Zod validation schemas provide typed API contracts. Package version tracked as `3.0.3` with semver. No URL versioning (`/v1/`, `/v2/` patterns). No `Accept-Version` headers. No breaking change detection in CI. No consumer-driven contract tests (Pact). No OpenAPI diff tools.
- **Gap**: Database schema is versioned via migrations, but API contracts have no versioning strategy. Breaking API changes cannot be detected automatically before deployment. Agent tool bindings could break silently.
- **Compensating Controls**:
  - Pin agent integrations to specific Docker image versions (semver-tagged)
  - Monitor API response structure changes manually during upgrades
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement API versioning (URL prefix `/v1/` or `Accept-Version` header). Add OpenAPI spec diff to CI pipeline to detect breaking changes. Consider consumer-driven contract testing if agents become regular consumers.
- **Evidence**: `prisma/migrations/` (14 versioned migrations), `src/lib/schema.ts` (Zod schemas), `package.json` (version 3.0.3)

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No distributed tracing. No OpenTelemetry SDK. No X-Ray instrumentation. No `traceparent` header propagation. Logging uses the `debug` npm package (e.g., `debug('umami:auth')`, `debug('umami:prisma')`, `debug('umami:clickhouse')`) which outputs text to stderr, not structured JSON. No correlation IDs or request IDs in logs. Prisma query logging is available via `LOG_QUERY` env var but outputs to debug channel.
- **Gap**: Cannot trace agent-initiated requests through the system. When an agent request fails, there is no trace ID to correlate the failure across database queries, auth checks, and response generation.
- **Compensating Controls**:
  - Add a request ID middleware that generates and logs a UUID per request
  - Use reverse proxy access logs as a basic trace mechanism
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenTelemetry instrumentation with auto-instrumentors for Next.js, Prisma, and HTTP clients. Implement structured JSON logging with correlation IDs. Add `X-Request-ID` header to all responses.
- **Evidence**: `src/lib/auth.ts` (debug package), `src/lib/prisma.ts` (debug package), `src/lib/clickhouse.ts` (debug package)

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No alerting configuration. No CloudWatch alarms. No anomaly detection. No PagerDuty/OpsGenie integration. No SLO-based alerting. The only health monitoring is the Docker healthcheck: `curl http://localhost:3000/api/heartbeat` which provides basic liveness only (returns `{ ok: true }`).
- **Gap**: No alerting for error rate spikes or latency degradation. If agent traffic causes performance issues, there is no automated detection or notification.
- **Compensating Controls**:
  - Deploy external uptime monitoring (e.g., Uptime Robot, Pingdom) against the heartbeat endpoint
  - Monitor Docker container resource usage for anomalies
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement application-level metrics (request count, error rate, latency percentiles) and configure alerting thresholds. Use Prometheus/Grafana or CloudWatch depending on deployment environment.
- **Evidence**: `docker-compose.yml` (healthcheck), `src/app/api/heartbeat/route.ts`, absence of any monitoring configuration

#### ENG-Q1: Infrastructure Governance — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No Infrastructure-as-Code files found in the repository. No Terraform, CloudFormation, CDK, Helm, Kustomize, or Ansible. The `Dockerfile` and `docker-compose.yml` define container packaging and local development environment but not production infrastructure provisioning. No API Gateway, IAM, or network configuration defined in code. No drift detection.
- **Gap**: Infrastructure is not defined as code. Any agent-facing infrastructure (reverse proxy, load balancer, database, monitoring) must be provisioned and managed outside this repository with no audit trail in code.
- **Compensating Controls**:
  - Use a separate IaC repository for Umami infrastructure provisioning
  - Document the deployment architecture and required infrastructure components
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Create IaC definitions (Terraform, CDK, or Helm) for production deployment infrastructure including: database (RDS/ClickHouse), load balancer, container orchestration (ECS/EKS), monitoring, and networking. This is typical for self-hosted applications — the Dockerfile is the handoff point.
- **Evidence**: `Dockerfile`, `docker-compose.yml`, absence of any IaC files

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: CI pipeline exists (`.github/workflows/ci.yml`) with `pnpm install`, `pnpm test`, and `pnpm build` steps. CD pipeline (`.github/workflows/cd.yml`) builds and pushes multi-architecture Docker images to GHCR and Docker Hub on tag push. Cloud CD pipeline (`.github/workflows/cd-cloud.yml`) pushes cloud-specific images. No API contract tests. No consumer-driven contract testing (Pact). No OpenAPI spec validation. No breaking change detection.
- **Gap**: CI runs tests and builds but does not verify API contract stability. Breaking API changes could be deployed without detection.
- **Compensating Controls**:
  - Add API endpoint smoke tests to the CI pipeline
  - Pin agent integrations to specific versions
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add API contract testing to CI: (1) Generate OpenAPI spec in build step, (2) Diff against previous version, (3) Fail on breaking changes. Add integration tests for critical API endpoints.
- **Evidence**: `.github/workflows/ci.yml`, `.github/workflows/cd.yml`, `.github/workflows/cd-cloud.yml`

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Docker images are tagged with semver version numbers (e.g., `3.0.3`, `3.0`, `3`), `latest`, and `postgresql-latest`. No blue/green deployment. No canary deployment with automatic rollback. No CodeDeploy rollback triggers. No feature flags. Rollback requires manually deploying a previous Docker image version. Prisma migrations are forward-only (no down migrations).
- **Gap**: No automated rollback capability. Recovery from a bad deployment requires manual intervention to pull a previous image tag. Database migrations cannot be reversed.
- **Compensating Controls**:
  - Pin deployments to specific Docker image tags (not `latest`)
  - Test upgrades in staging before production
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement deployment automation with rollback triggers (e.g., health check failure → auto-rollback to previous image). Add down migrations to Prisma migration files. Consider blue/green or canary deployment patterns.
- **Evidence**: `.github/workflows/cd.yml` (versioned tags), `docker-compose.yml` (uses `latest` tag), `prisma/migrations/` (no down migrations)

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Jest is configured (`jest.config.ts`) with 3 unit test files: `src/lib/__tests__/charts.test.ts`, `detect.test.ts`, `format.test.ts` — all testing utility functions, not API endpoints. Cypress e2e tests exist (`cypress/e2e/`) with 6 test files: `api-team.cy.ts`, `api-user.cy.ts`, `api-website.cy.ts`, `login.cy.ts`, `user.cy.ts`, `website.cy.ts`. No Postman/Newman collections. No REST Assured. No dedicated API integration test suite.
- **Gap**: Unit test coverage is minimal (3 utility test files). Cypress e2e tests cover some API flows but are not comprehensive. No tests for error handling, edge cases, or agent-specific scenarios (pagination boundaries, filter combinations).
- **Compensating Controls**:
  - Cypress e2e tests provide some API coverage
  - Zod schemas provide runtime input validation as a safety net
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add API integration tests for all read endpoints that agents will consume. Test pagination boundaries, filter combinations, error responses, and authentication edge cases. Add tests to CI pipeline.
- **Evidence**: `jest.config.ts`, `src/lib/__tests__/` (3 test files), `cypress/e2e/` (6 test files)

#### ENG-Q5: Encryption at Rest — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No encryption-at-rest configuration in the repository. No KMS key references. No IaC to configure encrypted storage. `docker-compose.yml` PostgreSQL uses a Docker volume with no encryption settings. Passwords are hashed with bcrypt (`src/lib/password.ts`). JWT tokens are encrypted with AES-256-GCM (`src/lib/crypto.ts`). But data at rest in PostgreSQL and ClickHouse is not encrypted at the repository level.
- **Gap**: Encryption at rest depends entirely on the deployment environment. The repository provides no guidance or configuration for encrypted storage. Self-hosted deployments may have unencrypted databases.
- **Compensating Controls**:
  - Deploy on cloud providers with default encryption at rest (e.g., RDS with encryption enabled, EBS encrypted volumes)
  - Document encryption requirements in deployment guide
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add IaC or deployment documentation specifying encryption at rest requirements. For cloud deployments, use RDS with KMS encryption and encrypted EBS volumes. For self-hosted, document filesystem encryption requirements.
- **Evidence**: `docker-compose.yml` (no encryption config), `src/lib/crypto.ts` (application-level encryption for tokens), `src/lib/password.ts` (bcrypt for passwords)

## INFOs — Architecture and Design Inputs

### DATA-Q1: Sensitive Data Classification ⚡ (Tiered) — Demoted from BLOCKER

- **Severity**: INFO
- **Stage A**: Yes — stores User (bcrypt passwords, username), Session (IP-derived geolocation, browser fingerprint), WebsiteEvent (referrer/UTM/click IDs), SessionData/EventData (arbitrary user-tracked fields), Revenue (financial amounts).
- **B1 — Agent-facing API response scoping: CLEAR.** `findUser()` uses `select: { password: includePassword, ... }` with `includePassword` defaulting to false (`src/queries/prisma/user.ts:14-28`). The admin users list uses explicit `omit: { password: true }` (`src/app/api/admin/users/route.ts`). Login returns `{ token, user: { id, username, role, createdAt, isAdmin, teams } }` — password is never serialized.
- **B2 — Access control differentiation: CLEAR.** Seven distinct roles with a real permission matrix (`src/lib/constants.ts` — `ROLE_PERMISSIONS` maps admin, user, view-only, team-owner, team-manager, team-member, team-view-only to specific capabilities). Resource-level guards in `src/permissions/website.ts` and `src/permissions/user.ts` enforce ownership and team-scope checks.
- **B3 — Formal classification metadata: INFO.** No `@PII`/`@Sensitive` decorators, no Macie/Presidio integration, no documented classification policy.
- **Overall**: Only B3 contributes a finding → **DATA-Q1 = INFO**. Systematic Prisma projections and granular RBAC mean the actual agent-leakage risk is low.
- **Implication**: Not a deployment gate. Classification metadata is a governance concern, not a code-level safety gap.
- **Recommendation (aspirational)**: Add schema-comment or decorator-based classification tags to `prisma/schema.prisma`; add a lint/CI check preventing `includePassword: true` outside authentication paths.
- **Evidence**: `src/queries/prisma/user.ts`, `src/app/api/admin/users/route.ts`, `src/app/api/auth/login/route.ts`, `src/lib/constants.ts`, `src/permissions/website.ts`, `src/permissions/user.ts`, `prisma/schema.prisma`.

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: POST endpoints for websites, users, teams, and reports do not have explicit idempotency keys. The `/api/send` event collection endpoint does not check for duplicate events. The website creation endpoint accepts an optional `id` field (`z.uuid().nullable().optional()`) which could serve as a client-generated idempotency key, but this is not enforced.
- **Implication**: If agent scope is later expanded to write-enabled, idempotency keys will be needed to prevent duplicate creates on retry. The existing optional `id` parameter on website creation is a good pattern to extend.
- **Recommendation**: When planning write-enabled agent scope, add idempotency key support to all POST endpoints.
- **Evidence**: `src/app/api/websites/route.ts` (optional id field), `src/app/api/send/route.ts` (no dedup)

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: All API endpoints return JSON via `Response.json()`. Success responses use `json(data)` which returns the data directly. Error responses use structured `{ error: { message, code, status } }` format. No XML, binary, or Protobuf formats. The tracker script (`/script.js`) is the only non-JSON endpoint.
- **Implication**: JSON-only API surface is ideal for agent consumption. LLMs consume JSON effectively with minimal parsing overhead.
- **Recommendation**: No action needed. JSON is the optimal format for agent integration.
- **Evidence**: `src/lib/response.ts`, `src/app/api/websites/route.ts`

### API-Q6: Asynchronous Operation Support

- **Severity**: INFO
- **Finding**: The export endpoint (`/api/websites/[websiteId]/export`) generates ZIP files synchronously. ClickHouse queries with large date ranges could be long-running. No background job framework (no Celery, Bull, or SQS workers). No polling/callback patterns. No Step Functions. Kafka producer in `src/lib/kafka.ts` is used for event ingestion to ClickHouse, not for async operation management.
- **Implication**: Long-running analytics queries could timeout for agents. If agent use cases include data export or large date-range analytics, async patterns will be needed.
- **Recommendation**: Consider adding async query support with job status polling for heavy analytics operations.
- **Evidence**: `src/lib/kafka.ts`, absence of background job framework

### API-Q7: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: Kafka integration exists (`src/lib/kafka.ts`) for event ingestion to ClickHouse as an alternative data pipeline. No webhook callback endpoints. No SNS/EventBridge integration. No event emission for state changes (website created/updated/deleted, user management, team changes). Event emission is only for analytics data pipeline, not for downstream notification.
- **Implication**: Agents cannot subscribe to state change events. Reactive agent patterns (respond when a website is added or analytics thresholds are crossed) require polling.
- **Recommendation**: Consider adding webhook support for key state changes (website created, analytics threshold alerts) to enable event-driven agent patterns.
- **Evidence**: `src/lib/kafka.ts`, `src/lib/db.ts` (runQuery routing)

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limit headers (`X-RateLimit-Remaining`, `Retry-After`) in any API response code. No API Gateway throttle settings. No rate limiting middleware. No usage plan configuration. CORS headers are the only access control headers configured in `next.config.ts`.
- **Implication**: Agents have no programmatic way to self-throttle. Without `Retry-After` headers, agents must implement arbitrary backoff strategies on 429/503 responses (which the application never sends).
- **Recommendation**: When rate limiting is implemented (STATE-Q5), include rate limit headers in all API responses.
- **Evidence**: `next.config.ts` (apiHeaders — no rate limit headers), `src/lib/response.ts` (no rate limit headers)

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: INFO
- **Finding**: Umami is a monolithic application — no inter-service calls exist. User context is maintained in the JWT token throughout the request lifecycle. The `checkAuth()` function extracts user identity from the JWT and makes it available to all downstream functions. No on-behalf-of flows or token exchange patterns. No distinction between agent-as-self vs agent-on-behalf-of-user.
- **Implication**: As a monolith, identity propagation is handled implicitly through the request context. If Umami is decomposed into microservices in the future, identity propagation will need to be explicitly implemented.
- **Recommendation**: No immediate action needed. Document the auth context flow for future reference.
- **Evidence**: `src/lib/auth.ts` (checkAuth), `src/lib/request.ts` (parseRequest)

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No optimistic locking (no version fields in Prisma schema, no ETags, no `If-Match` headers). Prisma uses `@updatedAt` for tracking but not for conflict detection. ClickHouse uses `ReplacingMergeTree` for `session_data` which provides eventual consistency deduplication. No pessimistic locking (`SELECT FOR UPDATE`) patterns found.
- **Implication**: When agent scope expands to write-enabled, concurrent write operations risk data corruption. The `@updatedAt` field is a foundation for optimistic locking.
- **Recommendation**: Before enabling write scope, add version fields and `If-Match` / ETag support to all write endpoints.
- **Evidence**: `prisma/schema.prisma` (no version fields), `db/clickhouse/schema.sql` (ReplacingMergeTree)

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits per agent identity. No `max_records_per_operation`, `max_spend_per_session`, or `max_delete_operations_per_session` controls. The application has no agent-specific operational limits.
- **Implication**: For read-only agents, blast radius is limited to query load (addressed by STATE-Q5 rate limiting). If write scope is enabled, transaction limits will be critical.
- **Recommendation**: When planning write-enabled scope, implement per-identity transaction limits configurable by role.
- **Evidence**: Absence of any transaction limit configuration

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No draft/pending status fields in the Prisma schema. Entities (websites, users, teams, reports) transition directly from creation to active state. Soft delete (`deletedAt`) exists but is not a draft/pending mechanism. No two-step commit patterns (create-then-confirm). No approval workflow endpoints.
- **Implication**: Read-only agents do not need draft states. If write scope is planned, draft states would allow agents to propose changes for human review.
- **Recommendation**: Consider adding draft/pending states to key entities (website creation, report configuration) before enabling write scope.
- **Evidence**: `prisma/schema.prisma` (no status/draft fields)

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No approval API endpoints. No status-based workflows requiring explicit human confirmation. No Step Functions with human approval tasks. No configurable operation-level approval flags.
- **Implication**: Read-only agents do not require approval gates. For write scope, approval gates would provide defense in depth for high-risk operations (bulk data operations, user management).
- **Recommendation**: Before enabling write scope, implement configurable approval requirements per operation type.
- **Evidence**: Absence of any approval workflow in API routes

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality dashboards, profiling reports, or completeness metrics. No null rate monitoring. No duplicate detection logic. No data freshness SLAs. ClickHouse materialized views (`website_event_stats_hourly_mv`) provide data aggregation but no explicit quality metrics. The `ReplacingMergeTree` engine for `session_data` provides eventual deduplication.
- **Implication**: Agents cannot assess data quality before reasoning on it. Missing or incomplete analytics data could lead to incorrect agent conclusions.
- **Recommendation**: Consider adding a data quality API endpoint that reports completeness, freshness, and row counts for key tables.
- **Evidence**: `db/clickhouse/schema.sql` (materialized views), absence of data quality tooling

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Field names are descriptive and human-readable: `websiteId`, `sessionId`, `visitId`, `createdAt`, `urlPath`, `referrerDomain`, `pageTitle`, `eventName`, `eventType`, `distinctId`. Prisma schema maps TypeScript camelCase names to snake_case database columns (e.g., `@map('website_id')`). Some abbreviated fields exist: `os`, `utm_source`, `gclid`, `fbclid`, `msclkid`, `ttclid`, `twclid` — all are industry-standard abbreviations recognized by analytics professionals.
- **Implication**: Field names are well-suited for LLM-based reasoning. No data dictionary needed for most fields. Industry-standard abbreviations (UTM parameters, click IDs) are widely understood.
- **Recommendation**: No action needed. Field naming is good.
- **Evidence**: `prisma/schema.prisma`, `db/clickhouse/schema.sql`, `src/lib/constants.ts` (FILTER_COLUMNS)

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No data catalog (no Glue Data Catalog, Collibra, Alation, DataHub). Prisma schema (`prisma/schema.prisma`) serves as the primary metadata definition for PostgreSQL entities. ClickHouse schema (`db/clickhouse/schema.sql`) documents the analytics data model. No external data dictionary or metadata API.
- **Implication**: Agent tool builders must reference Prisma schema and ClickHouse schema files directly. No programmatic metadata discovery available.
- **Recommendation**: Consider exposing a `/api/meta/schema` endpoint that returns entity descriptions, field types, and relationships to accelerate agent tool definition.
- **Evidence**: `prisma/schema.prisma`, `db/clickhouse/schema.sql`

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No custom metrics for business outcomes. No `cloudwatch.put_metric_data` or equivalent. No business KPI dashboards for the Umami application itself. Umami IS the analytics platform — it tracks business metrics for its users' websites but has no observability of its own operational business outcomes (e.g., successful event collection rate, query latency distribution, concurrent user count).
- **Implication**: When agents interact with Umami, there is no way to measure whether agent interactions produce good business outcomes for the Umami operator.
- **Recommendation**: Implement basic operational metrics: event ingestion rate, query success rate, average response time by endpoint, concurrent active sessions.
- **Evidence**: Absence of any business metrics in the codebase

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO (requirement met — no gap found)
- **Finding**: Umami exposes a comprehensive REST API via Next.js App Router API routes under `src/app/api/`. Endpoints include: `/api/auth/login` (POST), `/api/auth/verify` (GET), `/api/auth/logout` (POST), `/api/websites` (GET/POST), `/api/websites/[websiteId]` (GET/POST/DELETE), `/api/websites/[websiteId]/stats` (GET), `/api/websites/[websiteId]/pageviews` (GET), `/api/websites/[websiteId]/events` (GET), `/api/websites/[websiteId]/metrics` (GET), `/api/websites/[websiteId]/sessions` (GET), `/api/users` (GET/POST), `/api/teams` (GET/POST), `/api/send` (POST — event collection), `/api/admin/*`, `/api/share/*`, `/api/config` (GET), `/api/heartbeat` (GET), `/api/reports/*`, `/api/links/*`, `/api/pixels/*`, `/api/realtime/*`, and `/api/batch` (POST). All endpoints use Zod validation schemas for input validation. No direct database access or UI automation is required for integration.
- **Gap**: None — a documented REST API surface exists. Integration does not require direct database access, file-based exchange, or UI automation.
- **Recommendation**: None — requirement met. The API surface is the minimum viable integration point for agents.
- **Evidence**: `src/app/api/` (60+ route files), `src/lib/request.ts` (parseRequest), `src/lib/schema.ts` (Zod schemas)

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, Swagger, AsyncAPI, or Smithy specification files found. API contracts exist as Zod schemas in `src/lib/schema.ts` and inline in route files.
- **Gap**: No machine-readable specification for agent framework consumption.
- **Recommendation**: Generate OpenAPI spec from Zod schemas using `zod-to-openapi`.
- **Evidence**: `src/lib/schema.ts`, absence of OpenAPI files

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: Consistent structured errors: `{ error: { message, code, status } }`. Codes: `bad-request`, `unauthorized`, `forbidden`, `not-found`, `server-error`. Missing `retryable` field.
- **Gap**: No retryable indicator for agent decision-making.
- **Recommendation**: Add `retryable: boolean` to error response structure.
- **Evidence**: `src/lib/response.ts`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No explicit idempotency keys on POST endpoints. Website creation accepts optional `id` field.
- **Gap**: No idempotency enforcement — informational for read-only scope.
- **Recommendation**: Add idempotency key support when write scope is planned.
- **Evidence**: `src/app/api/websites/route.ts`, `src/app/api/send/route.ts`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: All endpoints return JSON via `Response.json()`. No XML, binary, or Protobuf.
- **Gap**: None.
- **Recommendation**: No action needed.
- **Evidence**: `src/lib/response.ts`

#### API-Q6: Asynchronous Operation Support
- **Severity**: INFO
- **Finding**: Export endpoint is synchronous. No background job framework. Kafka is for data pipeline, not async operations.
- **Trigger**: Service has operations >30s (export, large ClickHouse queries). Triggered but no async support found.
- **Gap**: Long-running operations may timeout.
- **Recommendation**: Consider async query support for heavy analytics.
- **Evidence**: `src/lib/kafka.ts`, absence of job queue

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: Kafka exists for analytics data pipeline only. No webhooks or event emission for CRUD state changes.
- **Trigger**: Service has state changes (stateful-crud). Triggered.
- **Gap**: No event-driven integration capability.
- **Recommendation**: Consider webhooks for key state changes.
- **Evidence**: `src/lib/kafka.ts`, `src/lib/db.ts`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit headers. No rate limiting middleware. No usage plan documentation.
- **Gap**: Agents cannot self-throttle.
- **Recommendation**: Add rate limit headers when rate limiting is implemented.
- **Evidence**: `next.config.ts`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: JWT-based auth for human users only. No OAuth2 client credentials, no API keys, no mTLS.
- **Gap**: No machine identity support.
- **Recommendation**: Implement API key authentication with principal attribution.
- **Evidence**: `src/lib/auth.ts`, `src/lib/jwt.ts`, `src/app/api/auth/login/route.ts`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: RBAC with 7 roles including `view-only` and `team-view-only`. No agent-specific permission model. Admin has wildcard `all` permission.
- **Gap**: No resource-level scoping for agent identities.
- **Recommendation**: Implement agent-specific roles with per-resource grants.
- **Evidence**: `src/lib/constants.ts`, `src/permissions/website.ts`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: Fine-grained permission checks exist: `canViewWebsite`, `canUpdateWebsite`, `canDeleteWebsite`, `canCreateWebsite`, `canViewUser`, `canUpdateUser`, `canDeleteUser`, `canViewTeam`, `canUpdateTeam`, `canDeleteTeam`. Action-level checks are performed before each API operation. However, the permission system is designed for human roles, not agent scoping — an agent could be granted `view-only` but there is no mechanism to restrict to specific resource types (e.g., "can view websites but not users").
- **Gap**: Action-level authorization exists but is scoped by role, not by agent capability. Cannot restrict an agent to specific resource types within a role.
- **Recommendation**: Add capability-based permissions that allow scoping agent access to specific resource types and actions beyond what role-level RBAC provides.
- **Evidence**: `src/permissions/website.ts`, `src/permissions/user.ts`, `src/permissions/team.ts`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: Monolithic application — no inter-service calls. User context maintained in JWT throughout request lifecycle.
- **Gap**: N/A for monolith architecture.
- **Recommendation**: No immediate action needed.
- **Evidence**: `src/lib/auth.ts`, `src/lib/request.ts`

#### AUTH-Q5: Credential Management
- **Severity**: RISK-QUALITY
- **Finding**: `APP_SECRET` sourced from environment variable (`process.env.APP_SECRET || process.env.DATABASE_URL`). No AWS Secrets Manager or HashiCorp Vault. `docker-compose.yml` has hardcoded defaults: `POSTGRES_USER=umami`, `POSTGRES_PASSWORD=umami`, `APP_SECRET='replace-me-with-a-random-string'`. Environment variables are the sole credential management mechanism.
- **Gap**: No secrets management system. Hardcoded defaults in docker-compose. APP_SECRET falls back to DATABASE_URL if not set — using the database connection string as the encryption secret is a security risk.
- **Recommendation**: Integrate with a secrets management system. Remove hardcoded defaults from docker-compose. Ensure APP_SECRET is always explicitly set and never falls back to DATABASE_URL.
- **Evidence**: `src/lib/crypto.ts` (secret function), `docker-compose.yml` (hardcoded credentials)

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No structured audit logging. Debug logging only via `debug` package.
- **Gap**: No audit trail for any operations.
- **Recommendation**: Implement structured audit logging with immutable storage.
- **Evidence**: `src/lib/auth.ts`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: Soft-delete exists but `checkAuth()` does not validate `deletedAt`. No forced token revocation.
- **Gap**: Cannot immediately suspend agent identities.
- **Recommendation**: Add `deletedAt` check to `checkAuth()`. Implement force-logout.
- **Evidence**: `src/lib/auth.ts`, `prisma/schema.prisma`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No saga/compensation patterns. Prisma transactions provide atomicity only. Soft delete provides limited undo.
- **Gap**: No multi-step workflow compensation.
- **Recommendation**: Extend soft-delete patterns before enabling write scope.
- **Evidence**: `src/lib/prisma.ts`, `prisma/schema.prisma`

#### STATE-Q2: Queryable Current State
- **Severity**: RISK-QUALITY
- **Finding**: GET endpoints exist for all major entities with filters, pagination, and date ranges. State is fully queryable via REST API. `pagedQuery()` and `pagedRawQuery()` functions provide structured paginated access.
- **Trigger**: Service has persistent state (stateful-crud). Triggered.
- **Gap**: Minimal — state is well-exposed. Some entities (e.g., individual session data) require multiple API calls to reconstruct full context.
- **Recommendation**: Consider adding aggregate/summary endpoints for common agent query patterns.
- **Evidence**: `src/app/api/websites/route.ts`, `src/lib/prisma.ts` (pagedQuery)

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No optimistic locking. No ETags. `@updatedAt` exists but not used for conflict detection.
- **Gap**: Informational for read-only scope.
- **Recommendation**: Add version fields before write scope expansion.
- **Evidence**: `prisma/schema.prisma`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: No circuit breakers. Kafka has basic timeouts. Prisma, ClickHouse, and Redis have no resilience config.
- **Gap**: Failures cascade to all callers.
- **Recommendation**: Add timeouts and circuit breakers for database connections.
- **Evidence**: `src/lib/kafka.ts`, `src/lib/prisma.ts`, `src/lib/clickhouse.ts`, `src/lib/redis.ts`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No rate limiting at any layer. Bot detection and IP blocking are not rate limits.
- **Gap**: No protection against agent traffic storms.
- **Recommendation**: Implement rate limiting at infrastructure and application layers.
- **Evidence**: `next.config.ts`, `src/app/api/send/route.ts`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No transaction limits per identity.
- **Gap**: Informational for read-only scope.
- **Recommendation**: Implement transaction limits before write scope expansion.
- **Evidence**: Absence of transaction limit configuration

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path. Priority is P2 — trigger not met.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No draft/pending states. Entities are active immediately on creation.
- **Gap**: Informational for read-only scope.
- **Recommendation**: Add draft states before write scope expansion.
- **Evidence**: `prisma/schema.prisma`

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No approval workflows or configurable gates.
- **Gap**: Informational for read-only scope.
- **Recommendation**: Add approval gates before write scope expansion.
- **Evidence**: Absence of approval workflows

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: Docker-compose provides local environment. Cypress tests and seed data scripts exist. No staging configuration.
- **Gap**: No production-equivalent staging environment.
- **Recommendation**: Create staging environment with production-scale seed data.
- **Evidence**: `docker-compose.yml`, `cypress/`, `scripts/seed-data.ts`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification ⚡ (Tiered)
- **Severity**: INFO
- **Stage A**: Yes — stores User (bcrypt passwords, username), Session (IP-derived geolocation, browser fingerprint), WebsiteEvent (referrer, UTM, click IDs), SessionData/EventData (arbitrary user-tracked fields), Revenue (financial amounts).
- **B1 — API response scoping**: CLEAR. `findUser()` uses `select: { password: includePassword, ... }` with `includePassword` defaulting to false (`src/queries/prisma/user.ts:14-28`). The admin users list uses explicit `omit: { password: true }` (`src/app/api/admin/users/route.ts`). Login returns `{ token, user: { id, username, role, createdAt, isAdmin, teams } }` — password never serialized.
- **B2 — Access control differentiation**: CLEAR. Seven distinct roles with a real permission matrix (`src/lib/constants.ts` — `ROLE_PERMISSIONS` maps admin, user, view-only, team-owner, team-manager, team-member, team-view-only to specific capabilities). Resource-level guards in `src/permissions/website.ts` and `src/permissions/user.ts` enforce ownership and team-scope checks.
- **B3 — Formal classification metadata**: Absent → INFO. No `@PII`/`@Sensitive` decorators, no Macie/Presidio integration, no documented classification policy.
- **Overall**: Highest sub-check firing is B3 (INFO) → DATA-Q1 = INFO. Not a deployment gate.
- **Recommendation (aspirational)**: Add decorator-based or schema-comment classification tags on Prisma models to document sensitivity levels; consider adding a CI check that prevents `includePassword: true` outside authentication paths.
- **Evidence**: `src/queries/prisma/user.ts`, `src/app/api/admin/users/route.ts`, `src/app/api/auth/login/route.ts`, `src/lib/constants.ts`, `src/permissions/website.ts`, `src/permissions/user.ts`, `prisma/schema.prisma` (no classification annotations).

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No data residency configuration. Database URL is environment-configured with no region enforcement.
- **Gap**: No residency controls for regulated data.
- **Recommendation**: Document residency requirements. Deploy agent infrastructure in same region.
- **Evidence**: `docker-compose.yml`, `prisma/schema.prisma`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK-QUALITY
- **Finding**: Well-implemented pagination (DEFAULT_PAGE_SIZE=20), extensive filtering, date ranges, sorting. Minor gap: no pageSize maximum.
- **Trigger**: Service has list/query endpoints with potentially unbounded results. Triggered.
- **Gap**: No maximum pageSize enforcement.
- **Recommendation**: Add `.max(1000)` to pageSize validation.
- **Evidence**: `src/lib/schema.ts`, `src/lib/prisma.ts`, `src/lib/clickhouse.ts`

#### DATA-Q4: System of Record Designations
- **Severity**: RISK-QUALITY
- **Finding**: PostgreSQL = metadata, ClickHouse = analytics. Self-contained but not documented.
- **Trigger**: Service has persistent state (stateful-crud). Triggered.
- **Gap**: No explicit system-of-record documentation.
- **Recommendation**: Document data store ownership per entity.
- **Evidence**: `src/lib/db.ts`, `prisma/schema.prisma`, `db/clickhouse/schema.sql`

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK-QUALITY
- **Finding**: Good temporal metadata (createdAt, updatedAt, Timestamptz, DateTime('UTC')). No freshness signaling headers.
- **Trigger**: Service has persistent state. Triggered.
- **Gap**: No data freshness indicators in API responses.
- **Recommendation**: Add freshness headers for ClickHouse-backed endpoints.
- **Evidence**: `prisma/schema.prisma`, `db/clickhouse/schema.sql`, `next.config.ts`

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: Auth tokens and user objects logged via debug. Error serialization logs full error context. No log scrubbing.
- **Gap**: Sensitive data can leak into logs.
- **Recommendation**: Implement centralized log redaction.
- **Evidence**: `src/lib/auth.ts`, `src/app/api/send/route.ts`, `src/lib/kafka.ts`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics or dashboards. ClickHouse materialized views provide aggregation.
- **Gap**: No quality awareness for agent reasoning.
- **Recommendation**: Add data quality API endpoint.
- **Evidence**: `db/clickhouse/schema.sql`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: 14 Prisma migrations. Zod schemas. Semver in package.json. No API versioning or breaking change detection.
- **Gap**: No API version strategy. Agent bindings could break silently.
- **Recommendation**: Implement API versioning and add OpenAPI diff to CI.
- **Evidence**: `prisma/migrations/`, `src/lib/schema.ts`, `package.json`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Descriptive field names. Industry-standard abbreviations. CamelCase in TypeScript, snake_case in database.
- **Gap**: None.
- **Recommendation**: No action needed.
- **Evidence**: `prisma/schema.prisma`, `db/clickhouse/schema.sql`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No data catalog. Prisma schema and ClickHouse schema serve as metadata.
- **Gap**: No programmatic metadata discovery.
- **Recommendation**: Consider metadata API endpoint.
- **Evidence**: `prisma/schema.prisma`, `db/clickhouse/schema.sql`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: No OpenTelemetry, X-Ray, or traceparent propagation. Debug package logging, not structured JSON. No correlation IDs.
- **Gap**: Cannot trace agent requests through the system.
- **Recommendation**: Add OpenTelemetry instrumentation and structured JSON logging.
- **Evidence**: `src/lib/auth.ts`, `src/lib/prisma.ts`, `src/lib/clickhouse.ts`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: No alerting. Docker healthcheck only. No CloudWatch, PagerDuty, or SLO alerting.
- **Gap**: No automated detection of agent-caused performance issues.
- **Recommendation**: Implement application metrics and alerting thresholds.
- **Evidence**: `docker-compose.yml`, `src/app/api/heartbeat/route.ts`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No business outcome metrics for Umami itself. It tracks metrics for its users' websites.
- **Gap**: No visibility into agent interaction outcomes.
- **Recommendation**: Add operational metrics.
- **Evidence**: Absence of business metrics

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance
- **Severity**: RISK-QUALITY
- **Finding**: No IaC. Dockerfile and docker-compose only. No drift detection.
- **Gap**: Infrastructure not defined as code.
- **Recommendation**: Create IaC for production deployment.
- **Evidence**: `Dockerfile`, `docker-compose.yml`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: CI with test + build. CD with Docker image push. No API contract tests.
- **Gap**: No API contract stability verification.
- **Recommendation**: Add API contract testing to CI.
- **Evidence**: `.github/workflows/ci.yml`, `.github/workflows/cd.yml`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: Semver-tagged Docker images. No automated rollback. Forward-only Prisma migrations.
- **Gap**: Manual rollback only.
- **Recommendation**: Implement automated rollback with health check triggers.
- **Evidence**: `.github/workflows/cd.yml`, `prisma/migrations/`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: 3 Jest unit tests (utility functions). 6 Cypress e2e tests. No dedicated API test suite.
- **Gap**: Minimal API test coverage.
- **Recommendation**: Add API integration tests for all read endpoints.
- **Evidence**: `jest.config.ts`, `src/lib/__tests__/`, `cypress/e2e/`

#### ENG-Q5: Encryption at Rest
- **Severity**: RISK-QUALITY
- **Finding**: No encryption-at-rest configuration. Depends on deployment environment.
- **Trigger**: Service has persistent data stores. Triggered.
- **Gap**: No encryption guidance in repository.
- **Recommendation**: Document and configure encryption at rest requirements.
- **Evidence**: `docker-compose.yml`, `src/lib/crypto.ts`

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `src/lib/auth.ts` | AUTH-Q1, AUTH-Q2, AUTH-Q4, AUTH-Q6, AUTH-Q7, DATA-Q6, OBS-Q1 |
| `src/lib/jwt.ts` | AUTH-Q1 |
| `src/lib/crypto.ts` | AUTH-Q1, AUTH-Q5, ENG-Q5 |
| `src/lib/password.ts` | ENG-Q5 |
| `src/lib/constants.ts` | AUTH-Q2, AUTH-Q3, DISC-Q2 |
| `src/lib/response.ts` | API-Q3, API-Q5, API-Q8 |
| `src/lib/schema.ts` | API-Q2, DATA-Q3, DISC-Q1 |
| `src/lib/request.ts` | API-Q3, AUTH-Q4 |
| `src/lib/prisma.ts` | STATE-Q1, STATE-Q4, DATA-Q3, OBS-Q1 |
| `src/lib/clickhouse.ts` | STATE-Q4, DATA-Q3, OBS-Q1 |
| `src/lib/redis.ts` | AUTH-Q7, STATE-Q4 |
| `src/lib/kafka.ts` | API-Q6, API-Q7, STATE-Q4, DATA-Q6 |
| `src/lib/db.ts` | API-Q7, DATA-Q4 |
| `src/lib/detect.ts` | DATA-Q1, DATA-Q2 |
| `src/permissions/website.ts` | AUTH-Q2, AUTH-Q3 |
| `src/permissions/user.ts` | AUTH-Q2, AUTH-Q3 |
| `src/permissions/team.ts` | AUTH-Q2, AUTH-Q3 |
| `src/app/api/auth/login/route.ts` | AUTH-Q1 |
| `src/app/api/websites/route.ts` | API-Q1, API-Q4, API-Q5, STATE-Q2 |
| `src/app/api/websites/[websiteId]/route.ts` | STATE-Q1 |
| `src/app/api/send/route.ts` | API-Q4, DATA-Q1, DATA-Q6, STATE-Q5 |
| `src/app/api/heartbeat/route.ts` | OBS-Q2 |
| `src/app/api/config/route.ts` | API-Q1 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/ci.yml` | ENG-Q2, ENG-Q4 |
| `.github/workflows/cd.yml` | ENG-Q2, ENG-Q3 |
| `.github/workflows/cd-cloud.yml` | ENG-Q2 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `Dockerfile` | ENG-Q1 |
| `docker-compose.yml` | AUTH-Q5, DATA-Q2, ENG-Q1, ENG-Q3, ENG-Q5, HITL-Q3, OBS-Q2, STATE-Q5 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `package.json` | DISC-Q1 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `next.config.ts` | API-Q8, STATE-Q5, DATA-Q5 |
| `prisma/schema.prisma` | AUTH-Q7, STATE-Q1, STATE-Q3, DATA-Q1, DATA-Q2, DATA-Q4, DATA-Q5, DISC-Q1, DISC-Q2, HITL-Q1 |
| `db/clickhouse/schema.sql` | DATA-Q1, DATA-Q4, DATA-Q5, DATA-Q7, DISC-Q2, DISC-Q3, STATE-Q3 |
| `jest.config.ts` | ENG-Q4 |
| `prisma/migrations/` | DISC-Q1, ENG-Q3 |

### Test Files
| File | Questions Referenced |
|------|---------------------|
| `src/lib/__tests__/charts.test.ts` | ENG-Q4 |
| `src/lib/__tests__/detect.test.ts` | ENG-Q4 |
| `src/lib/__tests__/format.test.ts` | ENG-Q4 |
| `cypress/e2e/` | ENG-Q4, HITL-Q3 |

### Seed / Scripts
| File | Questions Referenced |
|------|---------------------|
| `scripts/seed-data.ts` | HITL-Q3 |
| `scripts/seed/` | HITL-Q3 |
