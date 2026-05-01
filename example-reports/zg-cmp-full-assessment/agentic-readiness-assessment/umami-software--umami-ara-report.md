# Agentic Readiness Assessment Report

**Target**: umami (https://github.com/umami-software/umami)
**Date**: 2026-04-29
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: monorepo
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: typescript, analytics, web-app
**Context**: Self-hosted privacy-focused web analytics.

**Archetype Justification**: Umami has PostgreSQL database connections (Prisma ORM), CRUD endpoints for websites/users/teams/reports/links/pixels/segments, session management, and user-specific data — classifying as `stateful-crud`. Optional ClickHouse for analytics and Kafka for event streaming are secondary data paths.

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 2 | **RISK-SAFETY**: 9 | **RISK-QUALITY**: 15 | **INFOs**: 16

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 2 |
| RISK-SAFETY | 9 |
| RISK-QUALITY | 15 |
| INFO | 16 |
| N/A | 0 |
| Not Evaluated (extended) | 1 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 18
**Extended Questions Not Triggered**: 1
**Questions N/A (repo_type: monorepo)**: 0
**Service Archetype**: stateful-crud (auto-detected)

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: Umami's authentication relies exclusively on username/password login to obtain a JWT token (`src/app/api/auth/login/route.ts`). There is no OAuth2 client credentials flow, no API key mechanism with principal attribution, no mTLS, and no service account support. An agent would need to authenticate by sending a username and password to `/api/auth/login`, receiving an encrypted JWT token, and using it as a Bearer token. This provides no way to distinguish agent calls from human calls in audit logs.
- **Gap**: No machine identity authentication mechanism exists. No OAuth2 client credentials, no API keys, no service accounts. Agent identity cannot be attributed in audit logs. The only authentication path requires sharing human credentials with the agent.
- **Remediation**:
  - **Immediate**: Implement API key authentication with principal attribution — create an `api_key` table in the Prisma schema with fields for key hash, associated user/team, permissions scope, and creation metadata. Add an API key validation path in `src/lib/auth.ts` alongside the existing JWT path.
  - **Target State**: Agents authenticate via API keys that carry principal identity (agent name, owner, scope). All API requests from agent keys are attributable in logs.
  - **Estimated Effort**: Medium (2–4 weeks)
  - **Dependencies**: AUTH-Q6 (audit logging) should be addressed concurrently to ensure agent actions are logged.
- **Evidence**: `src/app/api/auth/login/route.ts`, `src/lib/auth.ts`, `src/lib/jwt.ts`

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: Umami stores visitor session data including IP-derived geolocation (country, region, city), browser fingerprint data (browser, OS, device, screen, language), page URLs, referrer URLs, and user agent strings in both PostgreSQL (`prisma/schema.prisma`) and ClickHouse (`db/clickhouse/schema.sql`). While Umami is marketed as "privacy-focused" and hashes IPs to generate session IDs (not storing raw IPs in the database by default), there is no formal data classification, no field-level tagging, no access controls that distinguish sensitive from non-sensitive fields, and no PII detection tooling (e.g., Amazon Macie).
- **Gap**: No data classification tags on any database tables or fields. No field-level encryption. No field-level access controls. No PII detection tooling. The `Session` model stores browser, OS, device, screen, language, country, region, city, and `distinctId` — all potentially identifying when combined. User passwords are stored hashed (bcrypt) but no other fields receive special treatment.
- **Remediation**:
  - **Immediate**: Create a data classification document mapping each Prisma model and ClickHouse table to sensitivity levels (public, internal, confidential, restricted). Tag the `Session` model fields (country, region, city, distinctId) as "internal-PII-adjacent". Tag `User.password` as "restricted".
  - **Target State**: All data fields are classified with sensitivity levels. Field-level access controls prevent agents from retrieving restricted fields without explicit authorization. Classification metadata is machine-readable.
  - **Estimated Effort**: Medium (2–3 weeks for classification; 4–6 weeks for enforcement)
  - **Dependencies**: AUTH-Q2 (scoped permissions) must be in place to enforce field-level access.
- **Evidence**: `prisma/schema.prisma`, `db/clickhouse/schema.sql`, `src/app/api/send/route.ts`, `src/lib/detect.ts`

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Umami has a role-based permission system with 7 roles defined in `src/lib/constants.ts`: admin, user, view-only, team-owner, team-manager, team-member, team-view-only. The admin role grants `PERMISSIONS.all` — unrestricted access to all resources. There is no mechanism to create a scoped agent identity that can only access specific websites or specific data types. The `view-only` role blocks write operations but still grants read access to all resources the user owns — there is no way to restrict an agent to a subset of websites.
- **Gap**: No per-resource scoping beyond ownership. No way to create an agent identity with access to only specific websites or data subsets. Admin role is all-or-nothing. No IAM-style policies with resource-level conditions.
- **Compensating Controls**:
  - Create a dedicated `view-only` user for the agent with access limited to specific team(s) containing only the websites the agent should access.
  - Implement an API gateway or reverse proxy in front of Umami that filters agent requests to only allowed endpoints and website IDs.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Extend the permission model to support resource-level scoping — allow API keys or service accounts to be bound to specific website IDs, with configurable read/write permissions per resource.
- **Evidence**: `src/lib/constants.ts` (ROLES, PERMISSIONS, ROLE_PERMISSIONS), `src/permissions/website.ts`

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Umami implements action-level authorization checks in `src/permissions/`. Functions like `canViewWebsite`, `canCreateWebsite`, `canUpdateWebsite`, `canDeleteWebsite` enforce different permission levels per action type. The `view-only` role has no write permissions. However, all authorization is tied to the human user role system — there is no agent-specific authorization layer. An agent using a `user` role credential could create, update, and delete websites even if the intended agent scope is read-only.
- **Gap**: Action-level authorization exists for human users but cannot be configured independently for agents. No agent-specific permission profiles. The enforcement depends entirely on the role assigned to the credential the agent uses — no defense in depth.
- **Compensating Controls**:
  - Assign the agent a `view-only` role to enforce read-only access at the application layer.
  - Use a team with `team-view-only` role for the agent user to restrict to read operations only.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create an `agent` role type with configurable action-level permissions that can be set per API key, independent of the human role system.
- **Evidence**: `src/permissions/website.ts`, `src/permissions/team.ts`, `src/permissions/user.ts`, `src/lib/constants.ts`

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Umami has no audit logging infrastructure. There is no CloudTrail integration, no immutable log storage, no write operation logging with principal attribution. The only logging present is debug-level logging using the `debug` npm package (`debug('umami:auth')`, `debug('umami:prisma')`) which outputs to stderr and is not structured, not immutable, and not retained. The `console.log(error)` in `src/app/api/send/route.ts` logs errors to stdout with no principal attribution.
- **Gap**: No audit trail of any kind. No ability to determine which user or agent performed which action. No immutable log storage. No CloudTrail or equivalent.
- **Compensating Controls**:
  - Deploy Umami behind a reverse proxy (nginx, API Gateway) that logs all requests with headers, providing a basic audit trail.
  - Enable PostgreSQL query logging with user attribution as a temporary audit mechanism.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement structured audit logging middleware that captures principal identity, action, resource, and timestamp for every mutating API call. Store logs in an append-only store (e.g., S3 with Object Lock, CloudWatch Logs with retention policies).
- **Evidence**: `src/lib/auth.ts` (debug logging only), `src/app/api/send/route.ts` (console.log), `src/lib/prisma.ts` (debug logging only)

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Umami has no mechanism to suspend or revoke an individual agent identity. The JWT tokens created at login (`src/app/api/auth/login/route.ts`) have no expiry by default. When Redis is enabled, auth keys are stored in Redis and can theoretically be deleted, but there is no API endpoint or administrative interface to revoke a specific token or disable a specific user session without deleting the user entirely. The `deletedAt` field on the User model provides soft-delete but not temporary suspension.
- **Gap**: No token revocation endpoint. No session invalidation API. No ability to disable a specific agent identity without deleting the user. JWT tokens without Redis have no expiry and cannot be revoked.
- **Compensating Controls**:
  - Enable Redis and set short token expiry (e.g., 1 hour) so compromised tokens expire quickly.
  - Implement an admin API to delete Redis auth keys matching a specific user ID for immediate revocation.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a user suspension flag (`suspendedAt` field on the User model), check it in `src/lib/auth.ts#checkAuth`, and add an admin API endpoint to suspend/unsuspend users.
- **Evidence**: `src/lib/auth.ts`, `src/lib/jwt.ts`, `src/lib/redis.ts`, `src/app/api/auth/login/route.ts`

#### STATE-Q1: Compensation and Rollback ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Umami has basic Prisma `$transaction` support exposed via `src/lib/prisma.ts#transaction`, but no saga pattern, no compensation logic, no explicit undo endpoints, and no multi-step workflow rollback. The `deleteWebsite` operation performs a soft delete (setting `deletedAt`) which is reversible at the database level, but there is no API to undo it. Analytics data deletion in ClickHouse is not reversible.
- **Gap**: No compensation or rollback mechanisms for multi-step operations. No undo endpoints. Prisma transactions are limited to single-database atomic operations — they do not span PostgreSQL and ClickHouse.
- **Compensating Controls**:
  - Agent scope is read-only, so write operations are not expected. This risk materializes only if scope is expanded.
  - Soft-delete pattern (deletedAt) provides a manual recovery path for entity deletions.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Before expanding to write-enabled agent scope, implement compensation endpoints (e.g., restore-from-soft-delete) and add saga-like coordination for operations spanning PostgreSQL and ClickHouse.
- **Evidence**: `src/lib/prisma.ts` (transaction function), `prisma/schema.prisma` (deletedAt fields), `src/app/api/websites/[websiteId]/route.ts`

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Umami has no circuit breaker, retry logic, or timeout configuration for its external dependency calls. The ClickHouse client (`src/lib/clickhouse.ts`) connects without timeout settings. The Kafka producer (`src/lib/kafka.ts`) has a `CONNECT_TIMEOUT` of 5000ms and `SEND_TIMEOUT` of 3000ms but no circuit breaker. The Prisma client (`src/lib/prisma.ts`) has no retry or timeout configuration. The Redis client (`src/lib/redis.ts`) has no resilience settings. If ClickHouse or PostgreSQL becomes unavailable, all API requests will fail with unhandled errors.
- **Gap**: No circuit breakers on any dependency call. No retry logic with exponential backoff. No timeout enforcement on database queries. No fallback behavior when dependencies are unavailable.
- **Compensating Controls**:
  - Deploy a service mesh or API gateway with circuit breaker capabilities in front of Umami.
  - Monitor dependency health with external health checks and fail fast at the load balancer level.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add circuit breaker patterns for ClickHouse and Kafka connections. Configure query timeouts on the Prisma PostgreSQL adapter. Implement health check endpoints that verify all dependency connections.
- **Evidence**: `src/lib/clickhouse.ts`, `src/lib/kafka.ts`, `src/lib/prisma.ts`, `src/lib/redis.ts`

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Umami has no rate limiting at any layer. There is no API Gateway throttling configuration, no WAF rate rules, no application-level rate limiting middleware, and no `express-rate-limit` or equivalent. The `/api/send` endpoint (event collection) is publicly accessible without authentication (`skipAuth: true`) and has no rate protection — making it vulnerable to traffic storms. The CORS configuration in `next.config.ts` allows all origins (`Access-Control-Allow-Origin: '*'`).
- **Gap**: No rate limiting of any kind. No throttling configuration. No API usage plans. No protection against agent-generated traffic storms. The event collection endpoint is completely unprotected.
- **Compensating Controls**:
  - Deploy Umami behind a reverse proxy (nginx, Cloudflare, AWS ALB) with rate limiting rules.
  - Use Cloudflare rate limiting or AWS WAF rate-based rules as an external protection layer.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add rate limiting middleware to the Next.js application or deploy behind an API gateway with configurable throttle rates. Priority: protect `/api/send` and `/api/batch` first.
- **Evidence**: `src/app/api/send/route.ts` (skipAuth: true, no rate limiting), `next.config.ts` (CORS: Access-Control-Allow-Origin: '*'), `docker/middleware.ts` (no rate limiting)

#### DATA-Q2: Data Residency and Sovereignty ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Umami processes visitor data that includes IP-derived geolocation (country, region, city), browser fingerprint data, and browsing behavior. As a self-hosted application, the data resides wherever the operator deploys it — but there are no data residency controls in the application itself. The ClickHouse configuration supports only a single instance URL. There is no region-specific data storage, no data sovereignty policy enforcement, and no controls preventing an agent from transmitting visitor behavioral data to an LLM provider in a different jurisdiction.
- **Gap**: No data residency configuration. No region-aware data routing. No data sovereignty enforcement. Self-hosted deployments inherit the residency of the hosting infrastructure, but the application provides no guardrails for multi-region or cross-border data handling.
- **Compensating Controls**:
  - Deploy Umami in the same AWS region as the LLM endpoint (e.g., Amazon Bedrock in the same region) to avoid cross-region data transfer.
  - Configure the agent to never send raw visitor data to the LLM — only aggregated, anonymized analytics.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Document data residency requirements for each deployment. If GDPR applies, ensure the deployment region is in the EU and configure the agent to use EU-based LLM endpoints. Add configuration for data residency zones.
- **Evidence**: `docker-compose.yml`, `src/lib/clickhouse.ts`, `src/lib/detect.ts` (geolocation processing)

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Umami has no PII redaction in logs. The `src/app/api/send/route.ts` catch block serializes the entire error object with `serializeError(e)` and logs it via `console.log(error)` — this may include request payloads containing visitor IP addresses, user agents, and URL paths. The `src/lib/auth.ts` debug logging (`log({ token, payload, authKey, shareToken, user })`) includes full authentication tokens and user objects. The `src/lib/kafka.ts` error handler logs serialized errors via `console.log('KAFKA ERROR:', serializeError(e))`. There is no log scrubbing middleware, no PII masking library, and no CloudWatch log filters.
- **Gap**: No PII redaction in any log output. Authentication tokens and user objects are logged in debug mode. Error serialization may expose request payloads containing visitor data. No log masking middleware.
- **Compensating Controls**:
  - Disable debug logging in production (the `debug` package is inactive unless the `DEBUG` environment variable is set).
  - Configure log aggregation to filter/mask PII patterns (IP addresses, email addresses) at the log pipeline level.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Replace `console.log(error)` in API routes with a structured logger that redacts sensitive fields. Add a PII scrubbing utility that masks IP addresses, tokens, and user agent strings before logging. Remove user objects and tokens from debug log statements.
- **Evidence**: `src/app/api/send/route.ts` (console.log of serialized errors), `src/lib/auth.ts` (debug logging of tokens/user), `src/lib/kafka.ts` (console.log of errors)

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Umami has no OpenAPI, AsyncAPI, GraphQL schema, or Swagger specification. The API surface is defined entirely through Next.js App Router file-based routing in `src/app/api/`. Request validation is implemented with Zod schemas in individual route files and `src/lib/schema.ts`, but these are not exported as a machine-readable specification. An agent framework would need to manually author tool definitions for each endpoint.
- **Gap**: No machine-readable API specification of any kind. Zod schemas exist but are not compiled into OpenAPI. No auto-generated documentation.
- **Compensating Controls**:
  - Use the Zod schemas as a reference to manually create agent tool definitions.
  - Generate an OpenAPI spec from the route structure and Zod schemas using tools like `zod-to-openapi`.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Adopt `zod-to-openapi` or `@asteasolutions/zod-to-openapi` to auto-generate an OpenAPI specification from existing Zod schemas. Publish the spec as part of the build pipeline.
- **Evidence**: `src/lib/schema.ts`, `src/app/api/` (route files with inline Zod schemas)

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Umami has a consistent structured error response format defined in `src/lib/response.ts`. Error responses include `message`, `code`, and `status` fields. Examples: `{ error: { message: 'Bad request', code: 'bad-request', status: 400 } }`, `{ error: { message: 'Unauthorized', code: 'unauthorized', status: 401 } }`. However, there is no `retryable` boolean or error category field that would help an agent distinguish retriable from terminal errors.
- **Gap**: Error responses are structured with code/message/status but lack a `retryable` field or error category. Agents cannot programmatically determine if a 500 error is transient or permanent.
- **Compensating Controls**:
  - Define retry logic in the agent tool definition based on HTTP status codes (retry on 429, 502, 503, 504; do not retry on 400, 401, 403, 404).
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add a `retryable: boolean` field to the error response structure in `src/lib/response.ts`. Mark `serverError` as retryable and `badRequest`/`unauthorized`/`forbidden`/`notFound` as not retryable.
- **Evidence**: `src/lib/response.ts`

#### API-Q6: Asynchronous Operation Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Umami has no explicit async operation patterns (no job submission, no polling endpoints, no webhook callbacks). Complex analytics report generation (funnel analysis, journey mapping, retention reports) runs synchronously in API handlers. For large datasets, these operations could exceed 30 seconds. The ClickHouse queries for reports like `getJourney` and `getFunnel` are executed synchronously. Kafka integration provides optional async event ingestion but no async result delivery.
- **Gap**: No async patterns for potentially long-running report generation. No job queue, no polling endpoints, no callback mechanisms. Agents calling complex report endpoints risk timeout failures.
- **Compensating Controls**:
  - Set appropriate timeout values in agent tool configurations for report endpoints.
  - Limit date ranges in agent queries to reduce query execution time.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: For complex report endpoints (`/api/reports/journey`, `/api/reports/funnel`, `/api/reports/retention`), implement async patterns: accept request → return job ID → poll for completion.
- **Evidence**: `src/app/api/reports/journey/route.ts`, `src/queries/sql/reports/`, `src/lib/kafka.ts`

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Umami's API has no versioning. There are no `/v1/`, `/v2/` URL patterns, no `Accept-Version` headers, no changelog files for API changes, and no breaking change detection in CI. The database schema has 14 Prisma migrations (`prisma/migrations/01_init` through `prisma/migrations/14_add_link_and_pixel`) showing active schema evolution. The CI pipeline (`ci.yml`) runs `pnpm test` and `pnpm build` but has no API contract tests, no OpenAPI diff, and no consumer-driven contract testing (e.g., Pact).
- **Gap**: No API versioning. No breaking change detection. No contract testing. Schema evolution is tracked via Prisma migrations but API changes are unversioned. Agent tool bindings could break silently on any deployment.
- **Compensating Controls**:
  - Pin agent tool definitions to a specific Umami Docker image version tag to avoid unexpected API changes.
  - Manually test agent tools after each Umami version upgrade.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Introduce API versioning (URL prefix `/api/v1/` or header-based). Add OpenAPI spec generation to the build pipeline with breaking change detection (e.g., `openapi-diff` in CI). Add consumer-driven contract tests.
- **Evidence**: `src/app/api/` (no versioning), `.github/workflows/ci.yml` (no contract tests), `prisma/migrations/` (14 migrations)

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Umami has no distributed tracing. There is no OpenTelemetry SDK, no AWS X-Ray instrumentation, no `traceparent` header propagation. Logging uses the `debug` npm package (`debug('umami:auth')`, `debug('umami:prisma')`, etc.) which outputs unstructured text to stderr. There are no correlation IDs, no request IDs, and no JSON structured logging. Error logging in `src/app/api/send/route.ts` uses `console.log` with serialized error objects.
- **Gap**: No distributed tracing. No structured logging. No correlation IDs. Agent-initiated requests are completely undebugable once they enter the application.
- **Compensating Controls**:
  - Deploy a reverse proxy that generates and logs request IDs for all incoming requests.
  - Use external APM tools (Datadog, New Relic) that can instrument the Node.js runtime without code changes.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenTelemetry instrumentation to the Next.js application. Replace `debug` and `console.log` with a structured JSON logger (e.g., `pino`) that includes request IDs. Propagate trace context through ClickHouse and Redis calls.
- **Evidence**: `src/lib/auth.ts`, `src/lib/prisma.ts`, `src/lib/clickhouse.ts`, `src/lib/kafka.ts`, `package.json` (debug dependency)

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Umami has no alerting configuration of any kind. There are no CloudWatch alarms, no PagerDuty/OpsGenie integration, no anomaly detection, no SLO-based alerting. The Docker healthcheck in `docker-compose.yml` checks `curl http://localhost:3000/api/heartbeat` for liveness but this is a simple up/down check — not error rate or latency monitoring.
- **Gap**: No alerting infrastructure. No error rate monitoring. No latency monitoring. Target system degradation would go undetected until agents report failures.
- **Compensating Controls**:
  - Deploy external uptime monitoring (e.g., UptimeRobot, Pingdom) against the `/api/heartbeat` endpoint.
  - Configure container orchestrator health checks with alerting on restart frequency.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Deploy application-level metrics (Prometheus, CloudWatch) for error rates and p95/p99 latency on API endpoints. Configure alerts for degradation thresholds.
- **Evidence**: `docker-compose.yml` (healthcheck only), `src/app/api/heartbeat/route.ts`

#### ENG-Q1: Infrastructure Governance — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Umami has no Infrastructure-as-Code beyond `docker-compose.yml` and `Dockerfile`. There is no Terraform, CloudFormation, CDK, Helm, or Kustomize. The Docker Compose file defines the database and application service but there is no API gateway, no IAM roles, no secrets management, no network configuration, no drift detection. Infrastructure changes (e.g., changing database credentials, adding environment variables) are made by editing `docker-compose.yml` directly.
- **Gap**: No IaC for the agent-facing integration surface. No peer review enforcement on infrastructure changes. No drift detection. API gateway, IAM, secrets, and networking are not codified.
- **Compensating Controls**:
  - Store `docker-compose.yml` in version control with branch protection rules requiring PR review.
  - Document the deployment architecture and maintain a manual change log.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Define the deployment infrastructure in Terraform or CDK — including API gateway (if added), database, networking, secrets, and IAM. Enable drift detection with AWS Config or equivalent.
- **Evidence**: `docker-compose.yml`, `Dockerfile` (no IaC files found)

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Umami has a CI pipeline (`.github/workflows/ci.yml`) that runs `pnpm test` (Jest) and `pnpm build` (Next.js build). The CD pipeline (`.github/workflows/cd.yml`) builds and pushes Docker images with version tags. However, there are no API contract tests, no OpenAPI validation, no breaking change detection, and no consumer-driven contract testing. The CI pipeline would not catch an API response schema change that breaks agent tool definitions.
- **Gap**: CI/CD exists but has no API contract testing capability. Breaking changes to agent-facing APIs are not detected before production deployment.
- **Compensating Controls**:
  - Add Cypress API tests to the CI pipeline (tests exist in `cypress/e2e/api-website.cy.ts` but are not run in CI).
  - Manually verify agent tool compatibility after each deployment.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Generate an OpenAPI spec from Zod schemas and add OpenAPI diff to the CI pipeline. Run the existing Cypress API tests in CI. Add Pact or similar consumer-driven contract tests for agent tool schemas.
- **Evidence**: `.github/workflows/ci.yml`, `.github/workflows/cd.yml`, `cypress/e2e/api-website.cy.ts`

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Umami's CD pipeline (`cd.yml`) publishes Docker images with semantic version tags (e.g., `3.0.3`, `3.0`, `3`, `latest`, `postgresql-latest`). Rollback is possible by changing the Docker image tag in `docker-compose.yml` to a previous version. However, there is no automated rollback mechanism, no blue/green deployment, no canary deployment, no feature flags, and no CodeDeploy rollback triggers. Database migrations (Prisma) are forward-only — there are no down migrations.
- **Gap**: Manual rollback via image tag is possible but not automated. No blue/green or canary deployment. No automated rollback triggers. Database migrations are not reversible.
- **Compensating Controls**:
  - Maintain a record of the last known-good image tag for quick manual rollback.
  - Test new versions in a staging environment before updating production.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement automated rollback — use Docker Compose with health check-based rollback, or migrate to Kubernetes with rolling update and rollback capabilities. Add down migrations to Prisma.
- **Evidence**: `.github/workflows/cd.yml`, `docker-compose.yml`, `prisma/migrations/`

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Umami has limited test coverage. Unit tests exist for 3 utility modules: `src/lib/__tests__/charts.test.ts`, `src/lib/__tests__/detect.test.ts`, `src/lib/__tests__/format.test.ts`. Cypress E2E tests exist for API endpoints (`cypress/e2e/api-website.cy.ts`, `cypress/e2e/api-user.cy.ts`, `cypress/e2e/api-team.cy.ts`) covering CRUD operations. However, Cypress tests are not run in the CI pipeline — CI only runs `pnpm test` (Jest unit tests). There are no API contract tests validating input handling, output format, or error responses systematically.
- **Gap**: Minimal unit test coverage (3 test files). Cypress API tests exist but are not in CI. No systematic API contract tests. No error response validation tests. No edge case coverage for agent consumption patterns.
- **Compensating Controls**:
  - Add Cypress API tests to the CI pipeline.
  - Manually test critical API endpoints used by agents after each deployment.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add the Cypress API tests to the CI pipeline. Create dedicated API contract tests for the endpoints agents will consume, validating response schemas, error codes, and edge cases (empty results, invalid params).
- **Evidence**: `jest.config.ts`, `src/lib/__tests__/`, `cypress/e2e/`, `.github/workflows/ci.yml`

#### ENG-Q5: Encryption at Rest — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Umami's `docker-compose.yml` provisions a PostgreSQL database with no encryption-at-rest configuration. The PostgreSQL volume (`umami-db-data`) stores data unencrypted on the host filesystem. There is no KMS integration, no customer-managed encryption keys, and no encryption configuration for ClickHouse. User passwords are hashed with bcrypt (`src/lib/password.ts`) and JWT tokens are encrypted with AES-256-GCM (`src/lib/crypto.ts`), but data at rest in the database is unencrypted.
- **Gap**: No encryption at rest for PostgreSQL data volume. No KMS integration. No encryption configuration for ClickHouse. Self-hosted deployments rely entirely on host-level disk encryption.
- **Compensating Controls**:
  - Deploy on infrastructure with full-disk encryption (e.g., AWS EBS with default encryption, encrypted EC2 instances).
  - Use managed database services (RDS, ClickHouse Cloud) with encryption at rest enabled.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: For AWS deployments, use RDS PostgreSQL with encryption at rest (KMS). For Docker deployments, ensure the host filesystem uses LUKS or equivalent disk encryption. Document encryption requirements in the deployment guide.
- **Evidence**: `docker-compose.yml`, `src/lib/crypto.ts` (application-level encryption only), `src/lib/password.ts` (bcrypt for passwords)

#### DATA-Q3: Selective Query Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Umami supports pagination, filtering, sorting, and search across its API. The `src/lib/schema.ts` defines `pagingParams` (page, pageSize), `searchParams` (search), `sortingParams` (orderBy), and `filterParams` (path, referrer, title, query, os, browser, device, country, region, city, tag, hostname, language, event). The `src/lib/prisma.ts#pagedQuery` function implements pagination with configurable `pageSize` (default 20 via `DEFAULT_PAGE_SIZE`). ClickHouse queries also support pagination via `pagedRawQuery`. Result set sizes are bounded by `pageSize`.
- **Gap**: Pagination and filtering are well-implemented, but there is no explicit maximum page size enforcement — an agent could request `pageSize=10000` and receive very large result sets. No GraphQL-style field selection to limit response payload.
- **Compensating Controls**:
  - Configure agent tool definitions with explicit pageSize limits (e.g., max 100).
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add a maximum `pageSize` validation (e.g., max 200) in the pagination schema. Consider adding field selection support for large response objects.
- **Evidence**: `src/lib/schema.ts` (pagingParams, filterParams), `src/lib/prisma.ts` (pagedQuery), `src/lib/request.ts`

#### DATA-Q4: System of Record Designations — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Umami serves as the system of record for its own analytics data (pageviews, events, sessions) and user management (users, teams, websites). There is no formal documentation of system-of-record designations. When both PostgreSQL and ClickHouse are enabled, the same event data exists in both stores with different schemas and query characteristics — there is no documented master data designation or conflict resolution between them.
- **Gap**: No documented system-of-record designations. Dual-store (PostgreSQL + ClickHouse) creates ambiguity about which store is authoritative. No master data management.
- **Compensating Controls**:
  - Document that PostgreSQL is the system of record for entities (users, teams, websites) and ClickHouse is the system of record for analytics events (when enabled).
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Create a data ownership document specifying which store is authoritative for each data domain. Establish conflict resolution rules for the PostgreSQL/ClickHouse dual-store pattern.
- **Evidence**: `src/lib/prisma.ts`, `src/lib/clickhouse.ts`, `prisma/schema.prisma`, `db/clickhouse/schema.sql`

#### DATA-Q5: Temporal Metadata and Freshness — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Umami includes comprehensive temporal metadata. All Prisma models have `createdAt` fields with `@db.Timestamptz(6)` (UTC timestamptz). Most mutable models also have `updatedAt` with `@updatedAt` annotation for automatic update tracking. ClickHouse tables use `DateTime('UTC')` for `created_at`. The application handles timezone conversion via `date-fns-tz`. However, there are no `Cache-Control` headers indicating data freshness, no `X-Data-Age` headers, and no consistency level indicators in API responses.
- **Gap**: Temporal metadata exists in the database schema but is not exposed in API responses as freshness signals. No cache headers for data freshness. No consistency level indicators (strong vs eventual vs cached).
- **Compensating Controls**:
  - Agent tool definitions can document that analytics data is eventually consistent (when ClickHouse is used) and entity data is strongly consistent (PostgreSQL).
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `Last-Modified` or `X-Data-Age` response headers to analytics API endpoints. Document the consistency model (PostgreSQL = strong, ClickHouse = eventual) in API documentation.
- **Evidence**: `prisma/schema.prisma` (createdAt, updatedAt fields), `db/clickhouse/schema.sql` (created_at DateTime('UTC'))

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Umami provides a Docker Compose setup (`docker-compose.yml`) that creates a complete local development environment with PostgreSQL. The `scripts/seed-data.ts` script generates realistic sample data (30 days of analytics data for two demo websites: a blog and a SaaS app). Cypress E2E tests (`cypress.config.ts`) are configured against `http://localhost:3000` with default credentials. There is no dedicated staging environment configuration or production-equivalent data shape documentation.
- **Gap**: Local development environment exists with seed data, but no dedicated staging environment with production-equivalent data shape. No environment isolation between testing and production.
- **Compensating Controls**:
  - Use the Docker Compose setup with seed data as a sandbox for agent testing.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Create a staging Docker Compose configuration that mimics production topology (including ClickHouse and Redis if used in production). Document the seed data generation process for creating production-equivalent test data.
- **Evidence**: `docker-compose.yml`, `scripts/seed-data.ts`, `cypress.config.ts`

## INFOs — Architecture and Design Inputs

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Umami's write endpoints (POST for creating websites, users, teams, reports) do not implement idempotency keys. The `/api/send` endpoint generates deterministic session IDs from IP + user agent + salt hashes, providing natural idempotency for session creation. However, POST `/api/websites` generates new UUIDs for each call unless a fixed `id` is provided in the body.
- **Implication**: If agent scope is expanded to write-enabled, idempotency keys should be added to write endpoints to prevent duplicate resource creation on retries.
- **Recommendation**: Before enabling write scope, add idempotency key support to write endpoints.
- **Evidence**: `src/app/api/send/route.ts` (deterministic session IDs), `src/app/api/websites/route.ts` (POST creates new UUID)

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: All Umami API responses use JSON format via `Response.json()`. The response serialization is consistent across all endpoints. No XML, binary, or protobuf formats are used. JSON responses are well-structured with consistent field naming conventions.
- **Implication**: JSON format is optimal for LLM consumption. No format transformation needed for agent tool integration.
- **Recommendation**: No action required. JSON format is ideal for agent consumption.
- **Evidence**: `src/lib/response.ts` (json(), ok(), badRequest(), etc.)

### API-Q7: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: Umami has optional Kafka integration (`src/lib/kafka.ts`) that enables event streaming for analytics events. When `KAFKA_URL` and `KAFKA_BROKER` environment variables are configured, analytics events can be published to Kafka topics. However, this is limited to analytics data ingestion — there are no webhooks or event emission for entity state changes (website created/updated/deleted, user changes, team changes).
- **Implication**: Agents could subscribe to Kafka topics for real-time analytics event streams if Kafka is enabled. Entity state change notifications would need to be built separately.
- **Recommendation**: Consider adding webhook support for entity lifecycle events if agent use cases require reactive behavior.
- **Evidence**: `src/lib/kafka.ts`

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: Umami has no rate limit documentation and does not return rate limit headers (`X-RateLimit-Remaining`, `Retry-After`). There are no `aws_api_gateway_usage_plan` configurations. The CORS headers include `Access-Control-Max-Age: 86400` in `next.config.ts` but this is for preflight caching, not rate limiting.
- **Implication**: Agents have no way to self-throttle based on rate limit information. If rate limiting is added (see STATE-Q5), rate limit headers should be included in responses.
- **Recommendation**: When rate limiting is implemented, include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `Retry-After` headers in API responses.
- **Evidence**: `next.config.ts` (CORS headers only)

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: INFO
- **Finding**: Umami is a single-service application — there are no downstream service calls that require identity propagation. The JWT token carries `userId` and `role`, which are verified on each request in `src/lib/auth.ts#checkAuth`. The share token mechanism (`x-umami-share-token` header) provides a limited delegation model for public dashboard sharing. There is no distinction between agent-as-self and agent-on-behalf-of-user.
- **Implication**: As a single-service application, identity propagation is not a current concern. If Umami is deployed as part of a larger service mesh, propagation of the agent identity to downstream services should be planned.
- **Recommendation**: No immediate action. If integrating with other services, ensure the agent JWT can be forwarded or exchanged.
- **Evidence**: `src/lib/auth.ts`, `src/lib/constants.ts` (SHARE_TOKEN_HEADER)

### AUTH-Q5: Credential Management

- **Severity**: INFO
- **Finding**: Umami's credentials are managed via environment variables: `APP_SECRET` (used for JWT encryption), `DATABASE_URL` (PostgreSQL connection string), `REDIS_URL`, `CLICKHOUSE_URL`, `KAFKA_URL`. The `docker-compose.yml` contains plaintext default credentials (`APP_SECRET: replace-me-with-a-random-string`, `POSTGRES_PASSWORD: umami`). There is no integration with AWS Secrets Manager, HashiCorp Vault, or any secrets management system. The `src/lib/crypto.ts#secret()` function derives the encryption key from `APP_SECRET` or falls back to `DATABASE_URL`.
- **Implication**: Hardcoded default credentials in `docker-compose.yml` are a security risk if not changed. Environment variable-based secrets are adequate for self-hosted deployments but do not support rotation without restart.
- **Recommendation**: Document that `APP_SECRET` must be changed from the default. Consider integrating with AWS Secrets Manager or Docker secrets for production deployments. Implement secret rotation support.
- **Evidence**: `docker-compose.yml` (plaintext defaults), `src/lib/crypto.ts` (APP_SECRET usage), `Dockerfile`

### STATE-Q2: Queryable Current State

- **Severity**: INFO
- **Finding**: Umami exposes comprehensive queryable state through its REST API. GET endpoints exist for all resource types: websites (`/api/websites`, `/api/websites/:id`), users (`/api/users/:id`), teams (`/api/teams/:id`), reports (`/api/reports`), sessions (`/api/websites/:id/sessions`), stats (`/api/websites/:id/stats`), events (`/api/websites/:id/events`), and more. All entity state is retrievable via the API before any action.
- **Implication**: Agents can query current state before making decisions. The rich query surface supports agent reasoning about analytics data.
- **Recommendation**: No action required. The queryable state surface is comprehensive.
- **Evidence**: `src/app/api/websites/[websiteId]/route.ts`, `src/app/api/websites/[websiteId]/stats/route.ts`

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Umami has no optimistic locking, no version fields, no ETags, and no `If-Match` headers. The Prisma schema has no `version` field on any model. The `updatedAt` field uses `@updatedAt` for automatic tracking but is not used for conflict detection. Write operations in `src/app/api/websites/[websiteId]/route.ts` perform direct updates without checking for concurrent modifications.
- **Implication**: Not relevant for read-only agent scope. If write scope is enabled, concurrent agent writes could cause data inconsistency.
- **Recommendation**: Before enabling write scope, add a `version` field to mutable models and implement optimistic locking.
- **Evidence**: `prisma/schema.prisma` (no version fields), `src/app/api/websites/[websiteId]/route.ts`

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Umami has no configurable transaction limits. There are no `max_records_per_operation`, `max_spend_per_hour`, or similar limits. The batch endpoint (`/api/batch`) processes all items in the request array sequentially without a maximum batch size limit.
- **Implication**: Not relevant for read-only agent scope. If write scope is enabled, transaction limits should be added to prevent agent-caused mass operations.
- **Recommendation**: Before enabling write scope, add configurable limits to batch operations and per-session action counts.
- **Evidence**: `src/app/api/batch/route.ts` (no batch size limit)

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Umami has no draft or pending state concept. Entities (websites, users, teams, reports) are created directly in their final state. The `deletedAt` field provides soft-delete functionality but not a draft/pending workflow. There are no approval endpoints or two-step commit patterns.
- **Implication**: Not relevant for read-only agent scope. If write scope is enabled, draft states would provide a safety mechanism for agent-proposed changes.
- **Recommendation**: Before enabling write scope, consider adding a `status` field (draft/active/archived) to critical entities.
- **Evidence**: `prisma/schema.prisma` (no status/draft fields)

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Umami has no configurable approval gates. No operations require human approval before execution. No Step Functions with human approval tasks. No status-based workflows requiring explicit confirmation.
- **Implication**: Not relevant for read-only agent scope. If write scope is enabled, approval gates for high-risk operations (user deletion, website deletion, data reset) should be implemented.
- **Recommendation**: Before enabling write scope, implement approval gates for destructive operations.
- **Evidence**: `src/app/api/` (no approval endpoints)

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: Umami has no data quality scoring, completeness metrics, or data profiling. There are no data quality dashboards, no null rate monitoring, no duplicate detection logic, and no data freshness SLAs. The analytics data quality depends on the tracker JavaScript being properly integrated on monitored websites.
- **Implication**: Agents reasoning on Umami data should treat analytics numbers as estimates, not exact figures. Bot filtering (`isbot` library in `src/app/api/send/route.ts`) provides some quality protection.
- **Recommendation**: Consider adding data quality indicators to API responses (e.g., sample rate, bot filter rate) for agent decision-making context.
- **Evidence**: `src/app/api/send/route.ts` (isbot check), `package.json` (isbot dependency)

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Umami uses semantically meaningful field names throughout. Prisma models use camelCase with clear naming: `websiteId`, `createdAt`, `eventName`, `referrerDomain`, `pageTitle`, `distinctId`. The database columns use snake_case equivalents (`website_id`, `created_at`, `event_name`). ClickHouse columns follow the same snake_case pattern. Some fields use abbreviated but still readable names: `os`, `utm_source`, `gclid`, `fbclid`. The abbreviations are industry-standard (UTM parameters, click IDs) and would be understood by agents with web analytics context.
- **Implication**: Field names are LLM-readable and do not require a data dictionary for basic interpretation. Industry-standard abbreviations (UTM, gclid) are well-documented.
- **Recommendation**: No immediate action. Consider adding field descriptions to the OpenAPI spec (when created) for completeness.
- **Evidence**: `prisma/schema.prisma`, `db/clickhouse/schema.sql`

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: Umami has no data catalog, no metadata layer, and no data dictionary. The Prisma schema (`prisma/schema.prisma`) serves as the de facto schema documentation for PostgreSQL entities, and the ClickHouse SQL schema (`db/clickhouse/schema.sql`) documents the analytics data structure. Zod validation schemas in `src/lib/schema.ts` provide informal API contracts. There is no Glue Data Catalog, Collibra, or similar tool.
- **Implication**: Building agent tools requires reading the Prisma schema and Zod schemas directly. An auto-generated data catalog would accelerate tool definition.
- **Recommendation**: Generate a machine-readable data dictionary from the Prisma schema and Zod schemas. Consider publishing this as part of the build pipeline.
- **Evidence**: `prisma/schema.prisma`, `db/clickhouse/schema.sql`, `src/lib/schema.ts`

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: Umami does not publish custom business outcome metrics. There are no `cloudwatch.put_metric_data` calls, no Prometheus metric exports, and no custom dashboards in the codebase. Umami is itself an analytics tool — its business metrics are the analytics data it collects (pageviews, sessions, events, revenue). There is an optional telemetry system (`scripts/telemetry.js`, `/api/scripts/telemetry/route.ts`) that phones home to `umami.is` for version tracking.
- **Implication**: When agents consume Umami, the analytics data is both the product and the metric. Agent interaction quality should be monitored at the orchestration layer, not within Umami itself.
- **Recommendation**: If agents are processing analytics data, track agent-specific metrics (queries per minute, response latency, error rate) at the agent orchestration layer.
- **Evidence**: `scripts/telemetry.js`, `src/app/api/scripts/telemetry/route.ts`

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: BLOCKER question — control present, no gap. Umami exposes a comprehensive REST API through Next.js App Router file-based routing in `src/app/api/`. The API surface includes: authentication (`/api/auth/login`, `/api/auth/verify`, `/api/auth/logout`, `/api/auth/sso`), websites CRUD (`/api/websites`, `/api/websites/:id`), users management (`/api/users`, `/api/users/:id`), teams (`/api/teams`, `/api/teams/:id`), reports (`/api/reports`), analytics data collection (`/api/send`, `/api/batch`), website analytics (`/api/websites/:id/stats`, `/api/websites/:id/pageviews`, `/api/websites/:id/events`, `/api/websites/:id/metrics`), session data, event data, realtime data, links, pixels, segments, and admin endpoints. All endpoints return JSON. No direct database access, file-based exchange, or UI automation is required. This is a well-structured REST API.
- **Gap**: N/A — API surface exists and is comprehensive.
- **Recommendation**: Generate an OpenAPI specification from the existing route structure to formalize the API documentation.
- **Evidence**: `src/app/api/` (60+ route files), `src/lib/response.ts`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, GraphQL schema, or Swagger specification exists. Zod schemas in `src/lib/schema.ts` and inline route schemas serve as informal contracts.
- **Gap**: No machine-readable API specification. Agent tool definitions must be authored manually.
- **Recommendation**: Adopt `zod-to-openapi` to auto-generate an OpenAPI specification from existing Zod schemas.
- **Evidence**: `src/lib/schema.ts`, `src/app/api/` (no spec files found)

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: Consistent structured error format in `src/lib/response.ts` with `message`, `code`, and `status` fields. Missing `retryable` boolean.
- **Gap**: No retryable/non-retryable distinction in error responses.
- **Recommendation**: Add `retryable: boolean` to error response structure.
- **Evidence**: `src/lib/response.ts`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Write endpoints lack idempotency keys. `/api/send` has natural idempotency via deterministic session ID hashing.
- **Gap**: No idempotency key support on write endpoints.
- **Recommendation**: Add idempotency key support before enabling write scope.
- **Evidence**: `src/app/api/send/route.ts`, `src/app/api/websites/route.ts`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: All API responses use JSON format via `Response.json()`. Consistent and LLM-friendly.
- **Gap**: N/A
- **Recommendation**: No action required.
- **Evidence**: `src/lib/response.ts`

#### API-Q6: Asynchronous Operation Support
- **Severity**: RISK-QUALITY
- **Finding**: No async patterns for long-running report generation. Complex ClickHouse queries run synchronously.
- **Gap**: No job queue, polling, or callback mechanisms.
- **Recommendation**: Implement async patterns for complex report endpoints.
- **Evidence**: `src/queries/sql/reports/`, `src/lib/kafka.ts`

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: Optional Kafka integration for analytics events. No entity state change events or webhooks.
- **Gap**: No entity lifecycle event emission.
- **Recommendation**: Consider webhooks for entity state changes.
- **Evidence**: `src/lib/kafka.ts`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit documentation or headers. No `X-RateLimit-Remaining` or `Retry-After`.
- **Gap**: No rate limit visibility for agents.
- **Recommendation**: Add rate limit headers when rate limiting is implemented.
- **Evidence**: `next.config.ts`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: Username/password login only. No OAuth2 client credentials, no API keys, no service accounts, no mTLS. Agent cannot be attributed in logs.
- **Gap**: No machine identity authentication mechanism.
- **Recommendation**: Implement API key authentication with principal attribution.
- **Evidence**: `src/app/api/auth/login/route.ts`, `src/lib/auth.ts`, `src/lib/jwt.ts`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: 7 roles exist but no resource-level scoping. Admin is all-or-nothing. No way to restrict an agent to specific websites.
- **Gap**: No per-resource permission scoping for agents.
- **Recommendation**: Extend permission model with resource-level scoping.
- **Evidence**: `src/lib/constants.ts`, `src/permissions/website.ts`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: `canView/canCreate/canUpdate/canDelete` checks exist but are tied to human roles, not agent-specific profiles.
- **Gap**: No agent-specific authorization configuration.
- **Recommendation**: Create agent role with configurable per-action permissions.
- **Evidence**: `src/permissions/website.ts`, `src/permissions/team.ts`, `src/lib/constants.ts`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: Single-service application. JWT carries userId/role. Share token provides limited delegation. No agent-as-self vs agent-on-behalf-of-user distinction.
- **Gap**: No identity propagation needed for single service.
- **Recommendation**: No immediate action.
- **Evidence**: `src/lib/auth.ts`, `src/lib/constants.ts`

#### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: Environment variable-based credentials. Default credentials in `docker-compose.yml`. No secrets manager integration.
- **Gap**: No secrets management. Default credentials are a risk if unchanged.
- **Recommendation**: Integrate with AWS Secrets Manager for production. Document mandatory credential changes.
- **Evidence**: `docker-compose.yml`, `src/lib/crypto.ts`, `Dockerfile`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No audit logging. Only debug-level logging via `debug` npm package. No immutable log storage.
- **Gap**: No audit trail. No principal attribution in logs.
- **Recommendation**: Implement structured audit logging middleware with immutable storage.
- **Evidence**: `src/lib/auth.ts`, `src/app/api/send/route.ts`, `src/lib/prisma.ts`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: No token revocation endpoint. No session invalidation API. JWT tokens have no expiry without Redis.
- **Gap**: Cannot suspend or revoke agent identity without deleting the user.
- **Recommendation**: Add user suspension flag and admin revocation endpoint.
- **Evidence**: `src/lib/auth.ts`, `src/lib/jwt.ts`, `src/lib/redis.ts`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Basic Prisma `$transaction` support. No saga pattern, no compensation logic, no undo endpoints. Soft-delete provides manual recovery.
- **Gap**: No compensation or rollback for multi-step operations.
- **Recommendation**: Implement compensation endpoints before enabling write scope.
- **Evidence**: `src/lib/prisma.ts`, `prisma/schema.prisma`

#### STATE-Q2: Queryable Current State
- **Severity**: INFO
- **Finding**: Comprehensive GET endpoints for all resource types. All entity state is queryable via REST API.
- **Gap**: N/A — queryable state is comprehensive.
- **Recommendation**: No action required.
- **Evidence**: `src/app/api/websites/[websiteId]/route.ts`, `src/app/api/websites/[websiteId]/stats/route.ts`

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No optimistic locking, no version fields, no ETags. Direct updates without conflict detection.
- **Gap**: No concurrency controls on write operations.
- **Recommendation**: Add version fields and optimistic locking before enabling write scope.
- **Evidence**: `prisma/schema.prisma`, `src/app/api/websites/[websiteId]/route.ts`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: No circuit breakers, no retry logic, no timeouts on ClickHouse, Prisma, or Redis clients. Kafka has connect/send timeouts but no circuit breaker.
- **Gap**: No resilience patterns on any dependency call.
- **Recommendation**: Add circuit breakers and timeout configuration for all external dependencies.
- **Evidence**: `src/lib/clickhouse.ts`, `src/lib/kafka.ts`, `src/lib/prisma.ts`, `src/lib/redis.ts`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No rate limiting at any layer. `/api/send` is publicly accessible without authentication or rate protection.
- **Gap**: No rate limiting or throttling. Vulnerable to traffic storms.
- **Recommendation**: Add rate limiting middleware. Priority: protect `/api/send` and `/api/batch`.
- **Evidence**: `src/app/api/send/route.ts`, `next.config.ts`, `docker/middleware.ts`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits. Batch endpoint has no maximum size limit.
- **Gap**: No blast radius controls.
- **Recommendation**: Add transaction limits before enabling write scope.
- **Evidence**: `src/app/api/batch/route.ts`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path. Umami is P2 priority.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No draft or pending state. Entities created in final state. `deletedAt` provides soft-delete but not draft workflow.
- **Gap**: No draft/pending states.
- **Recommendation**: Add status field to critical entities before enabling write scope.
- **Evidence**: `prisma/schema.prisma`

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No approval gates. No operations require human confirmation.
- **Gap**: No approval workflows.
- **Recommendation**: Implement approval gates for destructive operations before enabling write scope.
- **Evidence**: `src/app/api/`

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: Docker Compose provides local dev environment with PostgreSQL. Seed data generator (`scripts/seed-data.ts`) creates realistic test data. Cypress tests configured against localhost. No dedicated staging environment.
- **Gap**: Local dev exists but no production-equivalent staging environment.
- **Recommendation**: Create staging Docker Compose with production topology.
- **Evidence**: `docker-compose.yml`, `scripts/seed-data.ts`, `cypress.config.ts`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: No data classification tags, no field-level encryption, no PII detection tooling. Session data (country, region, city, browser, OS, distinctId) is potentially identifying when combined. User passwords are hashed but no other fields receive special treatment.
- **Gap**: No data classification. No field-level access controls.
- **Recommendation**: Create data classification document. Implement field-level access controls.
- **Evidence**: `prisma/schema.prisma`, `db/clickhouse/schema.sql`, `src/app/api/send/route.ts`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Self-hosted application — data resides wherever deployed. No application-level residency controls. No region-aware routing.
- **Gap**: No data residency enforcement. No cross-border data handling guardrails.
- **Recommendation**: Document residency requirements per deployment. Deploy in same region as LLM endpoint.
- **Evidence**: `docker-compose.yml`, `src/lib/clickhouse.ts`, `src/lib/detect.ts`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK-QUALITY
- **Finding**: Pagination (`page`, `pageSize`), filtering (14+ filter parameters), sorting (`orderBy`), and search supported. Default page size 20. No maximum page size enforcement.
- **Gap**: No maximum page size validation. No field selection.
- **Recommendation**: Add maximum `pageSize` validation.
- **Evidence**: `src/lib/schema.ts`, `src/lib/prisma.ts`, `src/lib/request.ts`

#### DATA-Q4: System of Record Designations
- **Severity**: RISK-QUALITY
- **Finding**: PostgreSQL + ClickHouse dual-store with no documented system-of-record designations. Same event data exists in both stores.
- **Gap**: No documented data ownership. Dual-store ambiguity.
- **Recommendation**: Document PostgreSQL as SoR for entities, ClickHouse for analytics events.
- **Evidence**: `src/lib/prisma.ts`, `src/lib/clickhouse.ts`, `prisma/schema.prisma`

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK-QUALITY
- **Finding**: All models have `createdAt` (Timestamptz). Mutable models have `updatedAt`. ClickHouse uses `DateTime('UTC')`. No freshness headers in API responses.
- **Gap**: Temporal metadata exists but not exposed as API response headers.
- **Recommendation**: Add `Last-Modified` headers and document consistency model.
- **Evidence**: `prisma/schema.prisma`, `db/clickhouse/schema.sql`

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: No PII redaction. `console.log(serializeError(e))` may expose visitor data. Debug logging includes tokens and user objects.
- **Gap**: No log scrubbing. No PII masking.
- **Recommendation**: Implement structured logging with PII redaction.
- **Evidence**: `src/app/api/send/route.ts`, `src/lib/auth.ts`, `src/lib/kafka.ts`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality scoring or completeness metrics. Bot filtering via `isbot` library provides some quality protection.
- **Gap**: No data quality indicators.
- **Recommendation**: Add quality indicators (bot filter rate, sample rate) to API responses.
- **Evidence**: `src/app/api/send/route.ts`, `package.json`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: No API versioning. No `/v1/`, `/v2/` patterns. No breaking change detection in CI. 14 Prisma migrations show active schema evolution. No contract testing.
- **Gap**: No API versioning or breaking change detection. Agent bindings could break silently.
- **Recommendation**: Introduce API versioning. Add OpenAPI diff and contract tests to CI.
- **Evidence**: `src/app/api/`, `.github/workflows/ci.yml`, `prisma/migrations/`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Semantically clear field naming throughout. CamelCase in Prisma models, snake_case in database. Industry-standard abbreviations (UTM, gclid). LLM-readable.
- **Gap**: N/A — names are clear.
- **Recommendation**: Add field descriptions to OpenAPI spec when created.
- **Evidence**: `prisma/schema.prisma`, `db/clickhouse/schema.sql`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No data catalog. Prisma schema and Zod schemas serve as de facto documentation. No Glue Data Catalog or equivalent.
- **Gap**: No machine-readable data catalog.
- **Recommendation**: Generate data dictionary from Prisma/Zod schemas.
- **Evidence**: `prisma/schema.prisma`, `src/lib/schema.ts`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: No OpenTelemetry, no X-Ray, no trace propagation. Logging via `debug` npm package (unstructured text). No correlation IDs. No JSON structured logging.
- **Gap**: No distributed tracing. No structured logging. Agent requests undebugable.
- **Recommendation**: Add OpenTelemetry instrumentation. Replace `debug`/`console.log` with structured JSON logger.
- **Evidence**: `src/lib/auth.ts`, `src/lib/prisma.ts`, `src/lib/clickhouse.ts`, `package.json`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: No alerting configuration. Docker healthcheck provides only liveness check. No error rate or latency monitoring.
- **Gap**: No alerting infrastructure. System degradation undetectable.
- **Recommendation**: Deploy Prometheus/CloudWatch metrics with error rate and latency alerts.
- **Evidence**: `docker-compose.yml`, `src/app/api/heartbeat/route.ts`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics published. Umami is itself an analytics tool — its data is the business metric. Optional telemetry phones home to umami.is.
- **Gap**: No application-level business outcome metrics.
- **Recommendation**: Track agent interaction metrics at the orchestration layer.
- **Evidence**: `scripts/telemetry.js`, `src/app/api/scripts/telemetry/route.ts`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance
- **Severity**: RISK-QUALITY
- **Finding**: No IaC beyond `docker-compose.yml` and `Dockerfile`. No Terraform, CloudFormation, CDK. No drift detection. No peer review enforcement on infrastructure changes.
- **Gap**: No IaC for integration surface. No drift detection.
- **Recommendation**: Define deployment infrastructure in Terraform/CDK.
- **Evidence**: `docker-compose.yml`, `Dockerfile`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: CI runs Jest tests and Next.js build. CD publishes Docker images. No API contract tests, no OpenAPI validation, no breaking change detection.
- **Gap**: No API contract testing in CI/CD.
- **Recommendation**: Add OpenAPI spec generation and diff. Run Cypress API tests in CI.
- **Evidence**: `.github/workflows/ci.yml`, `.github/workflows/cd.yml`, `cypress/e2e/api-website.cy.ts`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: Docker images tagged with semantic versions enable manual rollback. No automated rollback. No blue/green or canary deployment. Prisma migrations are forward-only.
- **Gap**: Manual rollback only. No automation. No reversible migrations.
- **Recommendation**: Implement automated rollback. Add down migrations.
- **Evidence**: `.github/workflows/cd.yml`, `docker-compose.yml`, `prisma/migrations/`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: 3 Jest unit test files. Cypress API tests exist but not in CI. No systematic API contract tests.
- **Gap**: Minimal test coverage. Cypress not in CI pipeline.
- **Recommendation**: Add Cypress API tests to CI. Create dedicated API contract tests.
- **Evidence**: `jest.config.ts`, `src/lib/__tests__/`, `cypress/e2e/`, `.github/workflows/ci.yml`

#### ENG-Q5: Encryption at Rest
- **Severity**: RISK-QUALITY
- **Finding**: PostgreSQL data volume unencrypted in Docker Compose. No KMS integration. Application-level encryption exists for JWT tokens (AES-256-GCM) and passwords (bcrypt) but not for data at rest.
- **Gap**: No encryption at rest for database volumes.
- **Recommendation**: Use managed databases with encryption at rest or ensure host-level disk encryption.
- **Evidence**: `docker-compose.yml`, `src/lib/crypto.ts`, `src/lib/password.ts`

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `src/lib/auth.ts` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q6, AUTH-Q7, OBS-Q1, DATA-Q6 |
| `src/lib/jwt.ts` | AUTH-Q1, AUTH-Q7 |
| `src/lib/crypto.ts` | AUTH-Q5, ENG-Q5 |
| `src/lib/password.ts` | ENG-Q5 |
| `src/lib/constants.ts` | AUTH-Q2, AUTH-Q3, AUTH-Q4 |
| `src/lib/response.ts` | API-Q1, API-Q3, API-Q5 |
| `src/lib/request.ts` | DATA-Q3 |
| `src/lib/schema.ts` | API-Q2, DATA-Q3, DISC-Q1, DISC-Q3 |
| `src/lib/prisma.ts` | STATE-Q1, STATE-Q2, STATE-Q4, AUTH-Q6, OBS-Q1, DATA-Q3, DATA-Q4 |
| `src/lib/clickhouse.ts` | STATE-Q4, DATA-Q2, DATA-Q4, OBS-Q1 |
| `src/lib/redis.ts` | AUTH-Q7, STATE-Q4 |
| `src/lib/kafka.ts` | API-Q6, API-Q7, STATE-Q4, DATA-Q6, OBS-Q1 |
| `src/lib/detect.ts` | DATA-Q1, DATA-Q2 |
| `src/lib/ip.ts` | DATA-Q6 |
| `src/permissions/website.ts` | AUTH-Q2, AUTH-Q3 |
| `src/permissions/team.ts` | AUTH-Q3 |
| `src/permissions/user.ts` | AUTH-Q3 |
| `src/app/api/auth/login/route.ts` | AUTH-Q1, AUTH-Q7 |
| `src/app/api/auth/sso/route.ts` | AUTH-Q1 |
| `src/app/api/send/route.ts` | API-Q4, DATA-Q1, DATA-Q6, AUTH-Q6, STATE-Q5, DATA-Q7 |
| `src/app/api/batch/route.ts` | STATE-Q6 |
| `src/app/api/websites/route.ts` | API-Q4 |
| `src/app/api/websites/[websiteId]/route.ts` | STATE-Q1, STATE-Q2, STATE-Q3 |
| `src/app/api/websites/[websiteId]/stats/route.ts` | STATE-Q2 |
| `src/app/api/heartbeat/route.ts` | OBS-Q2 |
| `src/app/api/reports/route.ts` | API-Q6 |
| `src/app/api/scripts/telemetry/route.ts` | OBS-Q3 |
| `src/lib/__tests__/charts.test.ts` | ENG-Q4 |
| `src/lib/__tests__/detect.test.ts` | ENG-Q4 |
| `src/lib/__tests__/format.test.ts` | ENG-Q4 |
| `scripts/telemetry.js` | OBS-Q3 |
| `scripts/seed-data.ts` | HITL-Q3 |

### Database Schemas
| File | Questions Referenced |
|------|---------------------|
| `prisma/schema.prisma` | DATA-Q1, DATA-Q5, STATE-Q1, STATE-Q3, HITL-Q1, DISC-Q1, DISC-Q2 |
| `db/clickhouse/schema.sql` | DATA-Q1, DATA-Q5, DISC-Q2 |
| `prisma/migrations/` (14 migration files) | DISC-Q1, ENG-Q3 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/ci.yml` | ENG-Q2, ENG-Q4, DISC-Q1 |
| `.github/workflows/cd.yml` | ENG-Q2, ENG-Q3 |
| `.github/workflows/cd-cloud.yml` | ENG-Q2 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `Dockerfile` | AUTH-Q5, ENG-Q1 |
| `docker-compose.yml` | AUTH-Q5, DATA-Q2, ENG-Q1, ENG-Q3, ENG-Q5, OBS-Q2, HITL-Q3, STATE-Q5 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `package.json` | OBS-Q1, DATA-Q7 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `next.config.ts` | API-Q8, STATE-Q5 |
| `docker/middleware.ts` | STATE-Q5 |
| `jest.config.ts` | ENG-Q4 |
| `cypress.config.ts` | HITL-Q3, ENG-Q4 |

### Test Files
| File | Questions Referenced |
|------|---------------------|
| `cypress/e2e/api-website.cy.ts` | ENG-Q2, ENG-Q4 |
| `cypress/e2e/api-user.cy.ts` | ENG-Q4 |
| `cypress/e2e/api-team.cy.ts` | ENG-Q4 |
