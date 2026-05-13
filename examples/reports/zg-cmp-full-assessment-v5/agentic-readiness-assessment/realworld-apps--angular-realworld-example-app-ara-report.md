# Agentic Readiness Assessment Report

**Target**: angular-realworld
**Date**: 2025-07-17
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**TD Version**: 3g1ipe93e5d2wb6n5d4yqaf9
**Repository Type**: application
**Service Archetype**: stateless-utility (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: typescript, frontend, angular
**Context**: Angular reference implementation of the RealWorld spec.

**Archetype Justification**: This is a client-side Angular SPA with no backend server, no database connections, no message queue consumers, and no server-side write endpoints. It consumes an external REST API at `https://api.realworld.show/api` but does not expose any HTTP/RPC surface of its own.

**Surface flags**:
- has_persistent_data_store: false
- has_http_rpc_surface: false
- has_auth_surface: false
- has_write_operations: false
- has_logging_of_user_data: false

> **INFO — Dev-Library-Application Override Applied**: This repository classifies as `application` (repo_type) but functions as a browser-only SPA/frontend scaffold with `service_archetype = stateless-utility` and all five surface flags = `false`. Per the ARA transformation definition, the dev-library-application override applies: surface-flag calibrations downgrade most questions to INFO since the system exposes no agent-callable server surface, holds no persistent data, and enforces no auth. The original `repo_type = application` is preserved in metadata above. This override reduces false-positive findings that would otherwise penalize a frontend app for lacking server-side controls it has no reason to implement.

---

## Readiness Profile: Agent-Ready

**BLOCKERs**: 0 | **RISK-SAFETY**: 0 | **RISK-QUALITY**: 1 | **INFOs**: 31

Cleared for autonomous operation. Instrument observability. Define scope explicitly. Run controlled pilot first.

> **Note**: This "Agent-Ready" profile reflects the fact that this frontend SPA has no agent-callable server surface. An agent would not interact directly with this repository's runtime — it would interact with the backend API at `https://api.realworld.show/api`. The backend API should be assessed separately. This assessment confirms the frontend codebase poses no blockers or safety risks as an integration target.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 0 |
| RISK-SAFETY | 0 |
| RISK-QUALITY | 1 |
| INFO | 31 |
| N/A | 0 |
| Not Evaluated (extended) | 11 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 8
**Extended Questions Not Triggered**: 11
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: stateless-utility (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

No BLOCKERs identified.

---

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

No RISK-SAFETY findings identified.

### RISK-QUALITY — Address as Capacity Allows

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The repository includes an OpenAPI 3.1.0 specification at `realworld/specs/api/openapi.yml` (via git submodule) that documents the backend API this frontend consumes. TypeScript model interfaces (`user.model.ts`, `article.model.ts`, `comment.model.ts`, `profile.model.ts`) define typed contracts matching the API schemas. However, there is no schema versioning mechanism (no `/v1/`, `/v2/` URL patterns — all routes are unversioned), no breaking change detection in CI pipelines, and no consumer-driven contract testing (e.g., Pact). The OpenAPI spec version field shows `2.0.0` but this is the spec document version, not an API versioning strategy. The API base URL is hardcoded as `https://api.realworld.show/api` in `api.interceptor.ts` with no version prefix.
- **Gap**: No API versioning strategy, no breaking change detection in CI, no consumer-driven contract tests. If the backend API changes, the frontend TypeScript interfaces may drift silently.
- **Compensating Controls**:
  - TypeScript strict mode (`strict: true` in `tsconfig.json`) catches type mismatches at compile time if models drift from actual API responses — but only after manual model updates.
  - The Playwright e2e tests (`e2e/auth.spec.ts`, `e2e/articles.spec.ts`, `e2e/comments.spec.ts`) run against the live backend API and would catch breaking changes at the integration level.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenAPI schema validation to the CI pipeline (e.g., `openapi-diff` or `oasdiff`) to detect breaking changes in the `realworld` submodule. Consider adding Pact consumer-driven contract tests between the Angular frontend and the RealWorld backend API.
- **Evidence**: `realworld/specs/api/openapi.yml`, `src/app/core/interceptors/api.interceptor.ts`, `src/app/core/auth/user.model.ts`, `src/app/features/article/models/article.model.ts`, `tsconfig.json`

---

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: This Angular SPA does not expose an HTTP/RPC server surface. It is a browser-only frontend application that *consumes* the RealWorld backend REST API at `https://api.realworld.show/api` (configured in `api.interceptor.ts`). The backend API is documented via an OpenAPI 3.1.0 specification at `realworld/specs/api/openapi.yml` (included as a git submodule). The frontend itself has no server entry point — `src/main.ts` calls `bootstrapApplication()` which runs in the browser.
- **Implication**: An agent would not call this frontend directly; it would call the backend API. The frontend is not a direct integration target for agents.
- **Recommendation**: If agent integration is desired, assess the backend API at `https://api.realworld.show/api` separately.
- **Evidence**: `src/main.ts`, `src/app/core/interceptors/api.interceptor.ts`, `realworld/specs/api/openapi.yml`, `angular.json`

### API-Q2: Machine-Readable API Specification
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — machine-readable spec is not applicable. The repository does include `realworld/specs/api/openapi.yml` (OpenAPI 3.1.0) but this describes the backend API this frontend consumes, not an API this repo exposes. As a dev-library-application with `has_http_rpc_surface = false`, there is nothing for a machine-readable spec to describe.
- **Implication**: No agent tool definitions can be generated from this frontend repository. Tool definitions should be generated from the backend API's OpenAPI spec.
- **Recommendation**: No action needed for this frontend repository.
- **Evidence**: `realworld/specs/api/openapi.yml`, `src/app/core/interceptors/api.interceptor.ts`

### API-Q3: Structured Error Responses
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — structured error responses are not applicable. The frontend's `error.interceptor.ts` does normalize error responses from the backend API into a consistent `{ errors: {...}, status: number }` format for UI components, including a fallback for network errors. This demonstrates good client-side error handling, but there is no server surface emitting these errors.
- **Implication**: Error handling patterns exist client-side but are not relevant for agent integration. Agent error handling depends on the backend API's error response structure.
- **Recommendation**: No action needed for this frontend repository. The error normalization pattern in `error.interceptor.ts` is a good practice for frontend resilience.
- **Evidence**: `src/app/core/interceptors/error.interceptor.ts`

### API-Q4: Idempotent Write Operations
- **Severity**: INFO
- **Finding**: Agent scope is read-only; idempotency of write operations is informational only. The frontend service layer does include write operations (`ArticlesService.create()`, `ArticlesService.update()`, `ArticlesService.delete()`, etc.), but these are HTTP calls to the external backend API — the backend owns idempotency enforcement. No idempotency keys are sent by the frontend.
- **Implication**: Idempotency enforcement is a backend concern. If agent scope changes to write-enabled, the backend API must be assessed for idempotency support.
- **Recommendation**: If write-enabled agent integration is planned, assess the backend API for idempotency support.
- **Evidence**: `src/app/features/article/services/articles.service.ts`, `src/app/features/article/services/comments.service.ts`, `src/app/features/profile/services/profile.service.ts`

### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: The backend API returns structured JSON responses. All frontend service methods use typed `HttpClient` calls expecting JSON bodies: `http.get<{ article: Article }>()`, `http.post<{ user: User }>()`, etc. Response schemas are defined in the OpenAPI spec with `content: application/json`.
- **Implication**: JSON format is agent-friendly. If an agent were to consume the backend API directly, no parsing adaptation would be needed.
- **Recommendation**: No action needed.
- **Evidence**: `realworld/specs/api/openapi.yml`, `src/app/features/article/services/articles.service.ts`, `src/app/core/auth/services/user.service.ts`

### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: The frontend does not document or handle rate limit headers from the backend API. No `X-RateLimit-Remaining` or `Retry-After` header parsing exists in the HTTP interceptors. The OpenAPI spec does not document rate limits for any endpoint.
- **Implication**: If an agent consumed the backend API directly, it would not have rate limit awareness. The backend API should be assessed for rate limit header support.
- **Recommendation**: If the backend API enforces rate limits, document them in the OpenAPI spec and add `Retry-After` handling in the frontend error interceptor for improved resilience.
- **Evidence**: `src/app/core/interceptors/api.interceptor.ts`, `src/app/core/interceptors/error.interceptor.ts`, `realworld/specs/api/openapi.yml`

### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: This frontend SPA delegates all authentication to the backend API. The `JwtService` stores a JWT token in `localStorage` and the `tokenInterceptor` attaches it as an `Authorization: Token <jwt>` header on outbound requests. No machine identity mechanism exists in this repository — and none should, because this is a browser-based UI consumed by humans, not a server-side service called by agents. As a dev-library-application with `has_auth_surface = false`, machine identity authentication is a backend concern.
- **Implication**: Agent identity management must be assessed on the backend API. This frontend is not an agent-callable surface.
- **Recommendation**: Assess the backend API for machine identity support if agent integration is planned.
- **Evidence**: `src/app/core/auth/services/jwt.service.ts`, `src/app/core/interceptors/token.interceptor.ts`, `src/app/core/auth/services/user.service.ts`

### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: INFO
- **Finding**: System does not enforce authorization — it is a browser-only frontend. Authorization decisions are enforced by the backend API. The frontend has client-side route guards (`requireAuth` in `app.routes.ts`) and `IfAuthenticatedDirective` for conditional UI rendering, but these are UX conveniences, not security controls. As a dev-library-application with `has_auth_surface = false`, scoped permissions are a backend concern.
- **Implication**: Permission scoping for agents must be assessed on the backend API. Frontend guards do not provide security enforcement.
- **Recommendation**: No action needed for this repository. Assess the backend API for scoped permission support.
- **Evidence**: `src/app/app.routes.ts`, `src/app/core/auth/if-authenticated.directive.ts`

### AUTH-Q3: Action-Level Authorization
- **Severity**: INFO
- **Finding**: Action-level authorization is enforced by the backend API, not the frontend. The frontend conditionally renders edit/delete buttons based on article authorship, but actual enforcement is server-side (403 Forbidden responses documented in `openapi.yml`). As a dev-library-application with `has_auth_surface = false`, action-level authorization is a backend concern.
- **Implication**: Action-level authorization for agent operations must be assessed on the backend API.
- **Recommendation**: No action needed for this repository. Assess the backend API for action-level authorization.
- **Evidence**: `realworld/specs/api/openapi.yml` (403 Forbidden responses), `e2e/articles.spec.ts`

### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: The frontend propagates the user's JWT token to the backend API via the `Authorization: Token <jwt>` header (implemented in `token.interceptor.ts`). This is a simple token-forwarding pattern — there is no multi-service identity propagation. Archetype is `stateless-utility` — downgraded to INFO per archetype calibration.
- **Implication**: Identity propagation across service boundaries is not applicable for a single-purpose frontend SPA. Multi-service identity concerns relate to the backend architecture.
- **Recommendation**: No action needed.
- **Evidence**: `src/app/core/interceptors/token.interceptor.ts`

### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: The JWT token is stored in browser `localStorage` via `JwtService`. No secrets manager integration exists — and none is expected for a browser-based SPA. No hardcoded credentials were found in the codebase. The `deploy.yml` workflow references GitHub secrets for CI/CD operations, which is appropriate secret management for CI pipelines.
- **Implication**: localStorage is accessible to any JavaScript running in the same origin. This is a known limitation of SPAs and is standard for the RealWorld spec.
- **Recommendation**: Consider migrating to `httpOnly` cookies for token storage to reduce XSS exposure (requires backend changes). The current approach is standard for SPAs.
- **Evidence**: `src/app/core/auth/services/jwt.service.ts`, `.github/workflows/deploy.yml`

### AUTH-Q6: Immutable Audit Logging
- **Severity**: INFO
- **Finding**: System does not execute agent-invoked write operations — audit logging is a consumer responsibility. This browser-only frontend has no server-side logging infrastructure. The only logging is `console.error(err)` in `src/main.ts` for Angular bootstrap failures. No CloudTrail, no structured logging, no audit trail configuration exists. The backend API is responsible for audit logging.
- **Implication**: Audit logging for agent operations must be assessed on the backend API. The frontend has no operations to audit.
- **Recommendation**: No action needed for this repository. Ensure the backend API has immutable audit logging for all write operations.
- **Evidence**: `src/main.ts`

### AUTH-Q7: Agent Identity Suspension
- **Severity**: INFO
- **Finding**: System does not issue or enforce agent identities — suspension is a consumer responsibility. This frontend SPA does not manage agent identities. The `UserService.purgeAuth()` and `UserService.logout()` methods are user-facing session management, not agent identity controls. As a dev-library-application with `has_auth_surface = false`, agent identity suspension is a backend concern.
- **Implication**: Agent identity lifecycle management must be assessed on the backend API.
- **Recommendation**: No action needed for this repository. Assess the backend API for agent identity suspension capabilities.
- **Evidence**: `src/app/core/auth/services/user.service.ts`

### STATE-Q1: Compensation and Rollback
- **Severity**: INFO
- **Finding**: System exposes no write operations — compensation logic is not applicable. This frontend SPA has no server-side multi-step write workflows. All state mutations are HTTP calls to the external backend API. The backend API owns transactional integrity and compensation logic. The `UserService` does implement retry logic with exponential backoff (2s → 4s → 8s → 16s cap) for auth recovery — client-side UX resilience, not server-side compensation.
- **Implication**: Compensation and rollback capabilities must be assessed on the backend API if write-enabled agent integration is planned.
- **Recommendation**: No action needed for this repository. Assess the backend API for compensation and rollback capabilities.
- **Evidence**: `src/app/core/auth/services/user.service.ts`, `src/app/features/article/services/articles.service.ts`

### STATE-Q3: Concurrency Controls
- **Severity**: INFO
- **Finding**: Agent scope is read-only; concurrency controls for write operations are informational only. The frontend services do not implement optimistic locking, ETags, or version fields. Write operations send PUT requests without concurrency tokens. This is a backend concern.
- **Implication**: Concurrency control enforcement is a backend API concern. Relevant only if agent scope changes to write-enabled.
- **Recommendation**: If write-enabled agent scope is planned, assess the backend API for optimistic locking support.
- **Evidence**: `src/app/features/article/services/articles.service.ts`, `src/app/core/auth/services/user.service.ts`

### STATE-Q5: Rate Limiting and Throttling
- **Severity**: INFO
- **Finding**: System exposes no HTTP/RPC surface — API-layer rate limiting is not applicable. This frontend SPA does not serve requests; it runs in the user's browser. Rate limiting for the backend API is a backend concern. As a dev-library-application with `has_http_rpc_surface = false`, API-layer rate limiting does not apply.
- **Implication**: Rate limiting must be assessed on the backend API. The frontend has no surface to rate-limit.
- **Recommendation**: No action needed. Assess the backend API for rate limiting configuration.
- **Evidence**: `src/app/core/interceptors/api.interceptor.ts`

### STATE-Q6: Blast Radius and Transaction Limits
- **Severity**: INFO
- **Finding**: Agent scope is read-only; transaction limits for write operations are informational only. The frontend does not enforce transaction limits. All write operations are proxied to the backend API. As a read-only agent scope, no agent would be executing write operations through this frontend.
- **Implication**: Transaction limits are relevant only for future write-enabled scope and must be assessed on the backend API.
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: `src/app/features/article/services/articles.service.ts`

### HITL-Q3: Sandbox/Staging Environment
- **Severity**: INFO
- **Finding**: No deployed HTTP/RPC surface and no persistent data store — sandbox/staging is a consumer concern. The repository has excellent local testing infrastructure: Playwright e2e tests configured with a local dev server (`http://localhost:4200`), Vitest unit tests, and CI pipelines. The e2e tests run against the live `https://api.realworld.show/api` backend, providing a de facto sandbox for validating frontend behavior.
- **Implication**: The Playwright + live backend testing pattern provides a de facto integration testing surface. For agent testing, the backend API's staging environment is the relevant surface.
- **Recommendation**: No action needed for this frontend. If agent integration targets the backend API, ensure it has a staging environment.
- **Evidence**: `playwright.config.ts`, `vitest.config.ts`, `.github/workflows/playwright.yml`, `package.json`

### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO
- **Finding**: Dev-library-application override applies — not a data-handling target. This frontend SPA does not own any persistent data store. User data (email, username, bio, image, token) flows through the frontend as transient in-memory state, but is persisted only in the backend API database and the browser's `localStorage` (JWT token only). The `User` model defines fields containing PII but these are stored and classified by the backend, not the frontend.
- **Implication**: PII classification is a backend concern. The frontend handles user data transiently in browser memory.
- **Recommendation**: Ensure the backend API has field-level data classification for user PII.
- **Evidence**: `src/app/core/auth/user.model.ts`, `src/app/core/auth/services/jwt.service.ts`, `src/app/core/auth/services/user.service.ts`

### DATA-Q2: Data Residency and Sovereignty
- **Severity**: INFO
- **Finding**: No persistent data store and no user-data logging — residency requirements do not apply. This frontend SPA stores no user data persistently. The backend API stores all user data and is subject to data residency requirements. The frontend runs in the user's browser, so data residency concerns relate to where the browser communicates with (the backend API's region).
- **Implication**: Data residency compliance must be assessed on the backend API, not the frontend.
- **Recommendation**: Assess the backend API for data residency compliance.
- **Evidence**: `src/app/core/interceptors/api.interceptor.ts`

### DATA-Q6: PII Redaction in Logs
- **Severity**: INFO
- **Finding**: System does not log user data and holds no user data — PII-in-logs risk is not applicable. The only logging is `console.error(err)` in `src/main.ts` for Angular bootstrap failures. No request/response body logging, no structured logging middleware, no telemetry. The `error.interceptor.ts` normalizes errors but does not log them. As a dev-library-application with `has_logging_of_user_data = false`, PII-in-logs risk does not apply.
- **Implication**: No PII-in-logs concern for this frontend. PII logging risks should be assessed on the backend API.
- **Recommendation**: No action needed.
- **Evidence**: `src/main.ts`, `src/app/core/interceptors/error.interceptor.ts`

### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality score or completeness metrics exist in this frontend codebase. The frontend renders data received from the backend API without quality assessment. Data quality is a backend concern — the backend API owns the data store and is responsible for data profiling, null rate monitoring, and freshness SLAs.
- **Implication**: If agents consume the backend API, data quality metrics should be assessed there.
- **Recommendation**: No action needed for this frontend.
- **Evidence**: No evidence found — absence is itself a finding.

### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: All TypeScript model interfaces use clear, human-readable, semantically meaningful field names: `username`, `email`, `title`, `description`, `body`, `createdAt`, `updatedAt`, `favoritesCount`, `tagList`, `following`, `favorited`, `slug`, `bio`, `image`. No legacy abbreviations or cryptic codes. The OpenAPI spec uses the same names.
- **Implication**: Field names are LLM-friendly and require no data dictionary for interpretation. This accelerates agent tool definition.
- **Recommendation**: No action needed. Excellent naming practices.
- **Evidence**: `src/app/core/auth/user.model.ts`, `src/app/features/article/models/article.model.ts`, `src/app/features/article/models/comment.model.ts`, `src/app/features/profile/models/profile.model.ts`, `src/app/features/article/models/article-list-config.model.ts`

### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No data catalog or metadata layer found. No AWS Glue Data Catalog, no Collibra/Alation/DataHub, no metadata files. The OpenAPI spec at `realworld/specs/api/openapi.yml` serves as de facto schema documentation for the backend API. The TypeScript interfaces serve as the frontend's typed contract documentation.
- **Implication**: For agent tool definition, the OpenAPI spec and TypeScript interfaces provide sufficient schema documentation for the RealWorld API surface.
- **Recommendation**: No action needed for this frontend. The OpenAPI spec is adequate for tool definition purposes.
- **Evidence**: `realworld/specs/api/openapi.yml`

### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: INFO
- **Finding**: Library/utility — tracing and correlation are consumer concerns. No OpenTelemetry SDK, no X-Ray instrumentation, no `traceparent` header propagation, no structured JSON logging. The only logging is `console.error(err)` in `main.ts`. This is expected for a browser-only SPA — distributed tracing for frontend applications is typically handled by browser RUM tools.
- **Implication**: If debugging agent-initiated requests through the backend API, tracing must be assessed on the backend, not the frontend.
- **Recommendation**: No action needed for this frontend. Consider adding browser RUM for production monitoring.
- **Evidence**: `src/main.ts`

### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: INFO
- **Finding**: Library/utility — alerting on error rates and latency is a consumer concern. No CloudWatch alarms, no anomaly detection, no PagerDuty/OpsGenie integration. This is a browser-only SPA deployed as static files. The frontend CI does include Playwright test reporting, but this is CI-level quality gating, not production alerting.
- **Implication**: Production monitoring of the RealWorld API error rates should be assessed on the backend.
- **Recommendation**: No action needed for this frontend.
- **Evidence**: `.github/workflows/playwright.yml`

### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business outcome metrics are published. No `cloudwatch.put_metric_data`, no custom dashboards, no business KPI tracking. This is a reference implementation / demo application — business outcome metrics are not expected. The frontend tracks UI state (loading states, auth states) but these are internal component state, not published metrics.
- **Implication**: If this were a production application, business metrics (article creation rate, user engagement, error rates by feature) would be valuable for assessing agent impact.
- **Recommendation**: No action needed for a reference implementation.
- **Evidence**: `src/app/core/models/loading-state.model.ts`, `src/app/core/auth/services/user.service.ts`

### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface and no auth surface — infrastructure governance is a consumer concern. This frontend SPA has no IaC. It is deployed as static files via `deploy.yml` (builds Angular app and creates a GitHub Release with a zip file). No API Gateway, IAM roles, secrets management, or networking configuration exists in IaC because there is no server-side infrastructure to govern.
- **Implication**: The deployment model (static file hosting) is inherently simple and has a minimal attack surface. Infrastructure governance for the backend API should be assessed separately.
- **Recommendation**: No action needed for this frontend.
- **Evidence**: `.github/workflows/deploy.yml`

### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — API contract testing is not applicable. The repository has a robust CI pipeline: Playwright e2e tests, format checking, security tests, and build+release. However, there is no API contract testing (no Pact, no OpenAPI validation in CI). The Playwright e2e tests run against the live backend API, providing integration validation but not contract-level breaking change detection.
- **Implication**: The Playwright e2e tests serve as de facto integration tests. For contract-level stability, see DISC-Q1 finding.
- **Recommendation**: No action needed for this frontend's CI. Consider adding OpenAPI diff to CI to catch backend breaking changes (see DISC-Q1).
- **Evidence**: `.github/workflows/playwright.yml`, `.github/workflows/lint.yml`, `.github/workflows/security-tests.yml`, `.github/workflows/deploy.yml`

### ENG-Q3: Rollback Capability
- **Severity**: INFO
- **Finding**: No deployed HTTP/RPC surface — deployment rollback is a consumer concern. The `deploy.yml` creates GitHub Releases with tagged build artifacts, which allows rollback by redeploying a previous release zip. No blue/green deployment, no canary, no CodeDeploy rollback configuration. The deployment model is a static file upload, so "rollback" means serving an older zip.
- **Implication**: Static file deployments have inherently fast rollback (serve previous version). This is adequate for a frontend SPA.
- **Recommendation**: No action needed. The GitHub Release tagging provides version history for rollback.
- **Evidence**: `.github/workflows/deploy.yml`

### ENG-Q4: API Test Coverage
- **Severity**: INFO
- **Finding**: The repository has comprehensive test coverage: (1) **Vitest unit tests** — `jwt.service.spec.ts` (40+ test cases), `user.service.spec.ts` (20+ test cases), `articles.service.spec.ts` (15+ test cases), plus comments, tags, and profile service specs. (2) **Playwright e2e tests** — auth, articles, comments, XSS security, error handling, navigation tests. All run in CI. However, this is frontend test coverage — the "APIs agents will consume" are the backend APIs.
- **Implication**: Excellent test coverage for a frontend application. The e2e tests provide real integration validation against the backend API. For agent-facing API test coverage, assess the backend.
- **Recommendation**: No action needed. Test infrastructure is mature.
- **Evidence**: `src/app/core/auth/services/jwt.service.spec.ts`, `src/app/core/auth/services/user.service.spec.ts`, `src/app/features/article/services/articles.service.spec.ts`, `e2e/auth.spec.ts`, `e2e/articles.spec.ts`, `e2e/comments.spec.ts`, `e2e/xss-security.spec.ts`, `vitest.config.ts`, `playwright.config.ts`

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: This Angular SPA does not expose an HTTP/RPC server surface. It is a browser-only frontend application that *consumes* the RealWorld backend REST API at `https://api.realworld.show/api` (configured in `api.interceptor.ts`). The backend API is documented via an OpenAPI 3.1.0 specification at `realworld/specs/api/openapi.yml` (included as a git submodule). The frontend itself has no server entry point — `src/main.ts` calls `bootstrapApplication()` which runs in the browser. An agent would not call this frontend directly; it would call the backend API.
- **Gap**: No agent-callable API surface is exposed by this repository. The assessed system is a UI layer.
- **Recommendation**: If agent integration is desired, assess the backend API at `https://api.realworld.show/api` separately. This frontend is not a direct integration target for agents.
- **Evidence**: `src/main.ts`, `src/app/core/interceptors/api.interceptor.ts`, `realworld/specs/api/openapi.yml`, `angular.json`

#### API-Q2: Machine-Readable API Specification
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — machine-readable spec is not applicable. The repository does include `realworld/specs/api/openapi.yml` (OpenAPI 3.1.0) but this describes the backend API this frontend consumes, not an API this repo exposes. As a dev-library-application with `has_http_rpc_surface = false`, there is nothing for a machine-readable spec to describe.
- **Gap**: N/A — no API surface to specify.
- **Recommendation**: No action needed for this frontend repository.
- **Evidence**: `realworld/specs/api/openapi.yml`, `src/app/core/interceptors/api.interceptor.ts`

#### API-Q3: Structured Error Responses
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — structured error responses are not applicable. The frontend's `error.interceptor.ts` does normalize error responses from the backend API into a consistent `{ errors: {...}, status: number }` format for UI components, including a fallback for network errors. This demonstrates good client-side error handling, but there is no server surface emitting these errors.
- **Gap**: N/A — no API surface to return errors from.
- **Recommendation**: No action needed for this frontend repository. The error normalization pattern in `error.interceptor.ts` is a good practice for frontend resilience.
- **Evidence**: `src/app/core/interceptors/error.interceptor.ts`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Agent scope is read-only; idempotency of write operations is informational only. The frontend service layer does include write operations (`ArticlesService.create()`, `ArticlesService.update()`, `ArticlesService.delete()`, `CommentsService.add()`, `CommentsService.delete()`, `ProfileService.follow()`, `ProfileService.unfollow()`), but these are HTTP calls to the external backend API — the backend owns idempotency enforcement. No idempotency keys are sent by the frontend.
- **Gap**: No idempotency keys in frontend write requests. Relevant only if agent_scope changes to write-enabled and the backend is the target.
- **Recommendation**: If write-enabled agent integration is planned, assess the backend API for idempotency support.
- **Evidence**: `src/app/features/article/services/articles.service.ts`, `src/app/features/article/services/comments.service.ts`, `src/app/features/profile/services/profile.service.ts`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: The backend API returns structured JSON responses. All frontend service methods use typed `HttpClient` calls expecting JSON bodies: `http.get<{ article: Article }>()`, `http.post<{ user: User }>()`, etc. Response schemas are defined in the OpenAPI spec with `content: application/json`. The frontend parses these via Angular's `HttpClient` which handles JSON deserialization natively.
- **Implication**: JSON format is agent-friendly. If an agent were to consume the backend API directly, no parsing adaptation would be needed.
- **Recommendation**: No action needed.
- **Evidence**: `realworld/specs/api/openapi.yml`, `src/app/features/article/services/articles.service.ts`, `src/app/core/auth/services/user.service.ts`

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has operations >30s OR long-running workflows. This browser-only SPA has no server-side operations.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has state changes (stateful-crud, orchestrator). This is a stateless-utility frontend.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: The frontend does not document or handle rate limit headers from the backend API. No `X-RateLimit-Remaining` or `Retry-After` header parsing exists in the HTTP interceptors (`api.interceptor.ts`, `token.interceptor.ts`, `error.interceptor.ts`). The OpenAPI spec at `realworld/specs/api/openapi.yml` does not document rate limits for any endpoint.
- **Implication**: If an agent consumed the backend API directly, it would not have rate limit awareness. The backend API should be assessed for rate limit header support.
- **Recommendation**: If the backend API enforces rate limits, document them in the OpenAPI spec and add `Retry-After` handling in the frontend error interceptor for improved resilience.
- **Evidence**: `src/app/core/interceptors/api.interceptor.ts`, `src/app/core/interceptors/error.interceptor.ts`, `realworld/specs/api/openapi.yml`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: This frontend SPA delegates all authentication to the backend API. The `JwtService` stores a JWT token in `localStorage` and the `tokenInterceptor` attaches it as an `Authorization: Token <jwt>` header on outbound requests. The `UserService` handles login (`POST /users/login`), registration (`POST /users`), and session validation (`GET /user`). No machine identity mechanism exists in this repository — and none should, because this is a browser-based UI consumed by humans, not a server-side service called by agents. The backend API at `https://api.realworld.show/api` owns the authentication surface. As a dev-library-application with `has_auth_surface = false`, machine identity authentication is a backend concern.
- **Gap**: No machine identity authentication — expected for a browser-only frontend. The backend API is the correct assessment target for this question.
- **Recommendation**: Assess the backend API for machine identity support if agent integration is planned. This frontend is not an agent-callable surface.
- **Evidence**: `src/app/core/auth/services/jwt.service.ts`, `src/app/core/interceptors/token.interceptor.ts`, `src/app/core/auth/services/user.service.ts`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: INFO
- **Finding**: System does not enforce authorization — it is a browser-only frontend. Authorization decisions (scoped permissions, role-based access) are enforced by the backend API. The frontend has client-side route guards (`requireAuth` in `app.routes.ts`) that redirect unauthenticated users, and `IfAuthenticatedDirective` for conditional UI rendering, but these are UX conveniences, not security controls. The actual permission enforcement happens server-side. As a dev-library-application with `has_auth_surface = false`, scoped permissions are a backend concern.
- **Gap**: No server-side authorization in this repo — expected for a frontend SPA.
- **Recommendation**: No action needed for this repository. Assess the backend API for scoped permission support.
- **Evidence**: `src/app/app.routes.ts`, `src/app/core/auth/if-authenticated.directive.ts`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: INFO
- **Finding**: Same as AUTH-Q2 — action-level authorization is enforced by the backend API, not the frontend. The frontend conditionally renders edit/delete buttons based on article authorship (visible in e2e test `e2e/articles.spec.ts` — "should only allow author to edit/delete article"), but actual enforcement is server-side (403 Forbidden responses documented in `openapi.yml`). As a dev-library-application with `has_auth_surface = false`, action-level authorization is a backend concern.
- **Gap**: No server-side action-level authorization in this repo — expected for a frontend SPA.
- **Recommendation**: No action needed for this repository. Assess the backend API for action-level authorization.
- **Evidence**: `realworld/specs/api/openapi.yml` (403 Forbidden responses), `e2e/articles.spec.ts`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: The frontend propagates the user's JWT token to the backend API via the `Authorization: Token <jwt>` header (implemented in `token.interceptor.ts`). This is a simple token-forwarding pattern — there is no identity propagation between services, no on-behalf-of flows, and no distinction between agent-as-self vs agent-on-behalf-of-user. Archetype is `stateless-utility` — downgraded to INFO per archetype calibration. Additionally, as a browser SPA, identity propagation across service boundaries is not applicable.
- **Gap**: No multi-service identity propagation — expected for a single-purpose frontend SPA.
- **Recommendation**: No action needed.
- **Evidence**: `src/app/core/interceptors/token.interceptor.ts`

#### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: The JWT token is stored in browser `localStorage` via `JwtService` (`window.localStorage['jwtToken']`). No secrets manager integration exists — and none is expected for a browser-based SPA. No hardcoded credentials were found in the codebase. The `deploy.yml` workflow references GitHub secrets (`secrets.AWS_ACCESS_KEY_ID`, `secrets.AWS_SECRET_ACCESS_KEY`, `secrets.AWS_SESSION_TOKEN`, `secrets.ATXCI_API_KEY`) for CI/CD operations, which is appropriate secret management for CI pipelines. No `.env` files are committed to the repository.
- **Implication**: localStorage is accessible to any JavaScript running in the same origin. This is a known limitation of SPAs and is standard for the RealWorld spec. The token has an expiry managed by the backend.
- **Recommendation**: Consider migrating to `httpOnly` cookies for token storage to reduce XSS exposure (though this requires backend changes). The current approach is standard for SPAs.
- **Evidence**: `src/app/core/auth/services/jwt.service.ts`, `.github/workflows/deploy.yml`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity RISK-SAFETY, but `has_auth_surface` is false AND `has_write_operations` is false → INFO per surface-flag calibration.
- **Finding**: System does not execute agent-invoked write operations — audit logging is a consumer responsibility. The library/utility is called by applications that own the audit context. This browser-only frontend has no server-side logging infrastructure. The only logging is `console.error(err)` in `src/main.ts` for bootstrap failures. No CloudTrail, no structured logging, no audit trail configuration exists in this repository. The backend API is responsible for audit logging of API operations.
- **Gap**: No audit logging — expected for a browser-only frontend SPA with no server-side operations.
- **Recommendation**: No action needed for this repository. Ensure the backend API has immutable audit logging for all write operations.
- **Evidence**: `src/main.ts`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: INFO
- **Finding**: System does not issue or enforce agent identities — suspension is a consumer responsibility. Libraries and utilities are invoked by applications that own identity lifecycle. This frontend SPA does not manage agent identities. The `UserService.purgeAuth()` method clears the JWT token from localStorage and the `UserService.logout()` method navigates to the home page — these are user-facing session management, not agent identity controls. The backend API owns agent identity lifecycle. As a dev-library-application with `has_auth_surface = false`, agent identity suspension is a backend concern.
- **Gap**: No agent identity management — expected for a browser-only frontend.
- **Recommendation**: No action needed for this repository. Assess the backend API for agent identity suspension capabilities.
- **Evidence**: `src/app/core/auth/services/user.service.ts`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity RISK-SAFETY. But `has_write_operations` is false AND `has_http_rpc_surface` is false → INFO per surface-flag calibration. Also archetype = stateless-utility → INFO.
- **Finding**: System exposes no write operations — compensation logic is not applicable. This frontend SPA has no server-side multi-step write workflows. All state mutations are HTTP calls to the external backend API (e.g., `ArticlesService.create()`, `UserService.update()`). The backend API owns transactional integrity and compensation logic. The `UserService` does implement retry logic with exponential backoff for auth recovery (2s → 4s → 8s → 16s cap), but this is client-side UX resilience, not server-side compensation.
- **Gap**: No compensation/rollback logic — expected for a frontend SPA with no server-side write operations.
- **Recommendation**: No action needed for this repository. Assess the backend API for compensation and rollback capabilities.
- **Evidence**: `src/app/core/auth/services/user.service.ts`, `src/app/features/article/services/articles.service.ts`

#### STATE-Q2: Queryable Current State
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator). This is a stateless-utility frontend with no persistent state.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Agent scope is read-only; concurrency controls for write operations are informational only. The frontend services do not implement optimistic locking, ETags, or version fields. Write operations (`ArticlesService.update()`, `UserService.update()`) send PUT requests without concurrency tokens. This is a backend concern — the backend API should enforce concurrency controls.
- **Gap**: No concurrency controls in frontend write requests — relevant only for future write-enabled scope.
- **Recommendation**: If write-enabled agent scope is planned, assess the backend API for optimistic locking support.
- **Evidence**: `src/app/features/article/services/articles.service.ts`, `src/app/core/auth/services/user.service.ts`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has external dependencies (calls other services or external APIs). While the frontend does call the backend API, as a browser-based SPA this is a client-server relationship, not a service-to-service dependency. The frontend does implement resilience patterns: `UserService` has exponential backoff retry (2s → 4s → 8s → 16s cap) for auth recovery, and `error.interceptor.ts` handles 401 errors globally. However, this is client-side UX resilience, not server-side circuit breaking.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: INFO
- **Finding**: System exposes no HTTP/RPC surface — API-layer rate limiting is not applicable. This frontend SPA does not serve requests; it runs in the user's browser. Rate limiting for the backend API at `https://api.realworld.show/api` is a backend concern. As a dev-library-application with `has_http_rpc_surface = false`, API-layer rate limiting does not apply.
- **Gap**: No rate limiting surface — expected for a frontend SPA.
- **Recommendation**: No action needed. Assess the backend API for rate limiting configuration.
- **Evidence**: `src/app/core/interceptors/api.interceptor.ts`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Agent scope is read-only; transaction limits for write operations are informational only. The frontend does not enforce transaction limits (max records, max spend, max deletes per session). All write operations are proxied to the backend API. As a read-only agent scope, no agent would be executing write operations through this frontend.
- **Gap**: No transaction limits — relevant only for future write-enabled scope.
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: `src/app/features/article/services/articles.service.ts`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path. Priority is P2.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled. Current agent_scope is read-only.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q2: Configurable Approval Gates
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled. Current agent_scope is read-only.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: INFO
- **Finding**: No deployed HTTP/RPC surface and no persistent data store — sandbox/staging is a consumer concern. However, the repository does have excellent local testing infrastructure: Playwright e2e tests configured in `playwright.config.ts` with a local dev server (`http://localhost:4200`), Vitest unit tests configured in `vitest.config.ts`, and CI pipelines that run both (`.github/workflows/playwright.yml`, `.github/workflows/security-tests.yml`). The e2e tests run against the live `https://api.realworld.show/api` backend (demo environment), providing a real integration testing surface.
- **Implication**: The Playwright + live backend testing pattern provides a de facto sandbox for validating frontend behavior. For agent testing, the backend API's staging environment is the relevant surface.
- **Recommendation**: No action needed for this frontend. If agent integration targets the backend API, ensure it has a staging environment.
- **Evidence**: `playwright.config.ts`, `vitest.config.ts`, `.github/workflows/playwright.yml`, `package.json`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO
- **Finding**: Dev-library-application override applies — skip to INFO. This frontend SPA does not own any persistent data store. User data (email, username, bio, image, token) flows through the frontend as transient in-memory state via `UserService.currentUser` observable, but is persisted only in the backend API database and the browser's `localStorage` (JWT token only). The `User` model (`user.model.ts`) defines fields `email`, `token`, `username`, `bio`, `image` — these contain PII but are stored and classified by the backend, not the frontend.
- **Implication**: PII classification is a backend concern. The frontend handles user data transiently in browser memory.
- **Recommendation**: Ensure the backend API has field-level data classification for user PII.
- **Evidence**: `src/app/core/auth/user.model.ts`, `src/app/core/auth/services/jwt.service.ts`, `src/app/core/auth/services/user.service.ts`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity RISK-SAFETY. But `has_persistent_data_store` is false AND `has_logging_of_user_data` is false → INFO per surface-flag calibration. Also archetype = stateless-utility → INFO.
- **Finding**: No persistent data store and no user-data logging — residency requirements do not apply. This frontend SPA stores no user data persistently. The backend API at `https://api.realworld.show/api` stores all user data and is subject to data residency requirements. The frontend runs in the user's browser, so data residency concerns relate to where the browser communicates with (the backend API's region), not the frontend code itself.
- **Gap**: No data residency concerns for this frontend — all data is stored by the backend.
- **Recommendation**: Assess the backend API for data residency compliance.
- **Evidence**: `src/app/core/interceptors/api.interceptor.ts`

#### DATA-Q3: Selective Query Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has list/query endpoints with potentially unbounded results. This frontend consumes paginated APIs (limit/offset parameters in `ArticleListConfig` model and `ArticlesService.query()`) but does not serve them. The frontend correctly passes `limit` and `offset` parameters to the backend API.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q4: System of Record Designations
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway). This frontend has no persistent state.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator). Additionally, archetype calibration for stateless-utility → INFO. The Article model does include `createdAt` and `updatedAt` fields from the backend API, and the Comment model includes `createdAt`.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q6: PII Redaction in Logs
- **Severity**: INFO
- **Finding**: System does not log user data and holds no user data — PII-in-logs risk is not applicable. The only logging in the entire codebase is `console.error(err)` in `src/main.ts` for Angular bootstrap failures. No request/response body logging, no structured logging middleware, no telemetry. The `error.interceptor.ts` normalizes errors but does not log them — it re-throws them for UI component handling. As a dev-library-application with `has_logging_of_user_data = false` and archetype `stateless-utility`, PII-in-logs risk does not apply.
- **Gap**: No PII-in-logs concern — expected for a frontend SPA with no server-side logging.
- **Recommendation**: No action needed.
- **Evidence**: `src/main.ts`, `src/app/core/interceptors/error.interceptor.ts`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality score or completeness metrics exist in this frontend codebase. The frontend renders data received from the backend API without quality assessment. Data quality is a backend concern — the backend API owns the data store and is responsible for data profiling, null rate monitoring, and freshness SLAs.
- **Implication**: If agents consume the backend API, data quality metrics should be assessed there.
- **Recommendation**: No action needed for this frontend.
- **Evidence**: No evidence found — absence is itself a finding.

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: The repository includes an OpenAPI 3.1.0 specification at `realworld/specs/api/openapi.yml` (via git submodule) that documents the backend API this frontend consumes. TypeScript model interfaces (`user.model.ts`, `article.model.ts`, `comment.model.ts`, `profile.model.ts`) define typed contracts matching the API schemas. However, there is no schema versioning mechanism (no `/v1/`, `/v2/` URL patterns — all routes are unversioned), no breaking change detection in CI pipelines, and no consumer-driven contract testing (e.g., Pact). The OpenAPI spec version field shows `2.0.0` but this is the spec document version, not an API versioning strategy. The API base URL is hardcoded as `https://api.realworld.show/api` in `api.interceptor.ts` with no version prefix.
- **Gap**: No API versioning strategy, no breaking change detection in CI, no consumer-driven contract tests. If the backend API changes, the frontend TypeScript interfaces may drift silently.
- **Recommendation**: Add OpenAPI schema validation to the CI pipeline (e.g., `openapi-diff` or `oasdiff`) to detect breaking changes in the `realworld` submodule. Consider adding Pact consumer-driven contract tests between the Angular frontend and the RealWorld backend API.
- **Evidence**: `realworld/specs/api/openapi.yml`, `src/app/core/interceptors/api.interceptor.ts`, `src/app/core/auth/user.model.ts`, `src/app/features/article/models/article.model.ts`, `tsconfig.json`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: All TypeScript model interfaces use clear, human-readable, semantically meaningful field names: `username`, `email`, `title`, `description`, `body`, `createdAt`, `updatedAt`, `favoritesCount`, `tagList`, `following`, `favorited`, `slug`, `bio`, `image`. No legacy abbreviations or cryptic codes. The OpenAPI spec uses the same names. The naming convention is consistent across all models.
- **Implication**: Field names are LLM-friendly and require no data dictionary for interpretation.
- **Recommendation**: No action needed. Excellent naming practices.
- **Evidence**: `src/app/core/auth/user.model.ts`, `src/app/features/article/models/article.model.ts`, `src/app/features/article/models/comment.model.ts`, `src/app/features/profile/models/profile.model.ts`, `src/app/features/article/models/article-list-config.model.ts`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No data catalog or metadata layer found. No AWS Glue Data Catalog, no Collibra/Alation/DataHub, no metadata files. The OpenAPI spec at `realworld/specs/api/openapi.yml` serves as de facto schema documentation for the backend API. The TypeScript interfaces serve as the frontend's typed contract documentation.
- **Implication**: For agent tool definition, the OpenAPI spec and TypeScript interfaces provide sufficient schema documentation for the RealWorld API surface.
- **Recommendation**: No action needed for this frontend. The OpenAPI spec is adequate for tool definition purposes.
- **Evidence**: `realworld/specs/api/openapi.yml`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: INFO
- **Finding**: Library/utility — tracing and correlation are consumer concerns. No OpenTelemetry SDK, no X-Ray instrumentation, no `traceparent` header propagation, no structured JSON logging, no `request_id` or `correlation_id` fields. The only logging is `console.error(err)` in `main.ts`. This is expected for a browser-only SPA — distributed tracing for frontend applications is typically handled by browser RUM (Real User Monitoring) tools, not application-level instrumentation. As a dev-library-application with `has_http_rpc_surface = false`, tracing and structured logging are backend concerns.
- **Implication**: If debugging agent-initiated requests through the backend API, tracing must be assessed on the backend, not the frontend.
- **Recommendation**: No action needed for this frontend. Consider adding browser RUM for production monitoring.
- **Evidence**: `src/main.ts`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: INFO
- **Finding**: Library/utility — alerting on error rates and latency is a consumer concern. No CloudWatch alarms, no anomaly detection, no PagerDuty/OpsGenie integration, no SLO-based alerting in this repository. This is a browser-only SPA deployed as static files. Alerting on API error rates and latency is a backend concern. The frontend CI does include Playwright test reporting (`.github/workflows/playwright.yml` uploads reports as artifacts), but this is CI-level quality gating, not production alerting.
- **Implication**: Production monitoring of the RealWorld API error rates should be assessed on the backend.
- **Recommendation**: No action needed for this frontend.
- **Evidence**: `.github/workflows/playwright.yml`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business outcome metrics are published. No `cloudwatch.put_metric_data`, no custom dashboards, no business KPI tracking in the codebase. This is a reference implementation / demo application — business outcome metrics are not expected. The frontend tracks UI state (loading states via `LoadingState` enum, auth states via `AuthState` type) but these are internal component state, not published metrics.
- **Implication**: If this were a production application, business metrics (article creation rate, user engagement, error rates by feature) would be valuable for assessing agent impact.
- **Recommendation**: No action needed for a reference implementation.
- **Evidence**: `src/app/core/models/loading-state.model.ts`, `src/app/core/auth/services/user.service.ts`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface and no auth surface — infrastructure governance is a consumer concern. This frontend SPA has no IaC (no Terraform, CloudFormation, CDK, Helm, or Kubernetes manifests). It is deployed as static files via `deploy.yml` (builds Angular app and creates a GitHub Release with a zip file). No API Gateway, IAM roles, secrets management, or networking configuration exists in IaC because there is no server-side infrastructure to govern. As a dev-library-application with `has_http_rpc_surface = false` AND `has_auth_surface = false`, infrastructure governance is a backend concern.
- **Implication**: The deployment model (static file hosting) is inherently simple and has a minimal attack surface. Infrastructure governance for the backend API should be assessed separately.
- **Recommendation**: No action needed for this frontend.
- **Evidence**: `.github/workflows/deploy.yml`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — API contract testing is not applicable. Library contract stability is evaluated by DISC-Q1 (schema/typed-export versioning). The repository has a robust CI pipeline: Playwright e2e tests (`.github/workflows/playwright.yml`), format checking (`.github/workflows/lint.yml`), security tests (`.github/workflows/security-tests.yml`), and build+release (`.github/workflows/deploy.yml`). However, there is no API contract testing (no Pact, no OpenAPI validation in CI, no schema diff). The Playwright e2e tests run against the live backend API, which provides integration validation but not contract-level breaking change detection.
- **Implication**: The Playwright e2e tests serve as de facto integration tests. For contract-level stability, see DISC-Q1 finding.
- **Recommendation**: No action needed for this frontend's CI. Consider adding OpenAPI diff to CI to catch backend breaking changes (see DISC-Q1).
- **Evidence**: `.github/workflows/playwright.yml`, `.github/workflows/lint.yml`, `.github/workflows/security-tests.yml`, `.github/workflows/deploy.yml`

#### ENG-Q3: Rollback Capability
- **Severity**: INFO
- **Finding**: No deployed HTTP/RPC surface — deployment rollback is a consumer concern. Library rollback is handled via package version pinning by consumers. The `deploy.yml` creates GitHub Releases with tagged build artifacts (`build-${{ github.run_number }}`), which allows rollback by redeploying a previous release zip. However, there is no blue/green deployment, no canary, no CodeDeploy rollback configuration, and no feature flags. The deployment model is a static file upload, so "rollback" means serving an older zip — straightforward but manual.
- **Implication**: Static file deployments have inherently fast rollback (serve previous version). This is adequate for a frontend SPA.
- **Recommendation**: No action needed. The GitHub Release tagging provides version history for rollback.
- **Evidence**: `.github/workflows/deploy.yml`

#### ENG-Q4: API Test Coverage
- **Severity**: INFO
- **Finding**: The repository has comprehensive test coverage via two testing layers: (1) **Vitest unit tests** — `jwt.service.spec.ts` (40+ test cases), `user.service.spec.ts` (20+ test cases), `articles.service.spec.ts` (15+ test cases), `comments.service.spec.ts`, `tags.service.spec.ts`, `profile.service.spec.ts` — testing all HTTP service methods with `HttpTestingController` mocks. (2) **Playwright e2e tests** — `e2e/auth.spec.ts` (8 tests: register, login, logout, session persistence, invalid token handling), `e2e/articles.spec.ts` (9 tests: CRUD, favorites, authorization), `e2e/comments.spec.ts` (8 tests: add, delete, permissions), `e2e/xss-security.spec.ts` (15+ security tests for XSS vectors), `e2e/error-handling.spec.ts`, `e2e/navigation.spec.ts`, etc. All run in CI. However, this is frontend test coverage — the "APIs agents will consume" are the backend APIs. As a dev-library-application with `has_http_rpc_surface = false`, API test coverage is assessed differently — the frontend tests validate the client-side contract, not a server-side API surface.
- **Implication**: Excellent test coverage for a frontend application. The e2e tests provide real integration validation against the backend API. For agent-facing API test coverage, assess the backend.
- **Recommendation**: No action needed. Test infrastructure is mature.
- **Evidence**: `src/app/core/auth/services/jwt.service.spec.ts`, `src/app/core/auth/services/user.service.spec.ts`, `src/app/features/article/services/articles.service.spec.ts`, `e2e/auth.spec.ts`, `e2e/articles.spec.ts`, `e2e/comments.spec.ts`, `e2e/xss-security.spec.ts`, `vitest.config.ts`, `playwright.config.ts`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent data stores. This frontend SPA has no persistent data stores (only browser localStorage for JWT token).
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

---

## Evidence Index

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| realworld/specs/api/openapi.yml | API-Q1, API-Q2, API-Q3, API-Q5, API-Q8, AUTH-Q3, DISC-Q1, DISC-Q2, DISC-Q3 |

### Source Code
| File | Questions Referenced |
|------|---------------------|
| src/main.ts | API-Q1, AUTH-Q6, DATA-Q6, OBS-Q1 |
| src/app/app.config.ts | API-Q1 |
| src/app/app.routes.ts | AUTH-Q2 |
| src/app/core/interceptors/api.interceptor.ts | API-Q1, API-Q2, API-Q8, DATA-Q2, DISC-Q1, STATE-Q5 |
| src/app/core/interceptors/token.interceptor.ts | AUTH-Q1, AUTH-Q4 |
| src/app/core/interceptors/error.interceptor.ts | API-Q3, API-Q8, DATA-Q6 |
| src/app/core/auth/services/jwt.service.ts | AUTH-Q1, AUTH-Q5, DATA-Q1 |
| src/app/core/auth/services/user.service.ts | AUTH-Q1, AUTH-Q7, API-Q5, STATE-Q1, STATE-Q3, OBS-Q3, DATA-Q1 |
| src/app/core/auth/auth.component.ts | AUTH-Q1 |
| src/app/core/auth/user.model.ts | AUTH-Q1, DATA-Q1, DISC-Q1, DISC-Q2 |
| src/app/core/auth/if-authenticated.directive.ts | AUTH-Q2 |
| src/app/core/models/errors.model.ts | API-Q3 |
| src/app/core/models/loading-state.model.ts | OBS-Q3 |
| src/app/features/article/services/articles.service.ts | API-Q4, API-Q5, STATE-Q1, STATE-Q3, STATE-Q6 |
| src/app/features/article/services/comments.service.ts | API-Q4 |
| src/app/features/profile/services/profile.service.ts | API-Q4 |
| src/app/features/article/services/tags.service.ts | API-Q5 |
| src/app/features/article/models/article.model.ts | DISC-Q1, DISC-Q2 |
| src/app/features/article/models/comment.model.ts | DISC-Q2 |
| src/app/features/article/models/article-list-config.model.ts | DISC-Q2 |
| src/app/features/profile/models/profile.model.ts | DISC-Q2 |
| src/app/features/article/components/article-list.component.ts | DATA-Q3 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| .github/workflows/deploy.yml | AUTH-Q5, ENG-Q1, ENG-Q2, ENG-Q3 |
| .github/workflows/playwright.yml | HITL-Q3, OBS-Q2, ENG-Q2, ENG-Q4 |
| .github/workflows/lint.yml | ENG-Q2 |
| .github/workflows/security-tests.yml | ENG-Q2 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| package.json | API-Q1, HITL-Q3 |
| angular.json | API-Q1 |
| tsconfig.json | DISC-Q1 |
| vitest.config.ts | HITL-Q3, ENG-Q4 |
| playwright.config.ts | HITL-Q3, ENG-Q4 |
| .gitmodules | DISC-Q1 |

### Test Files
| File | Questions Referenced |
|------|---------------------|
| e2e/auth.spec.ts | AUTH-Q3, ENG-Q4 |
| e2e/articles.spec.ts | AUTH-Q3, ENG-Q4 |
| e2e/comments.spec.ts | ENG-Q4 |
| e2e/xss-security.spec.ts | ENG-Q4 |
| e2e/playwright.base.ts | ENG-Q4 |
| src/app/core/auth/services/jwt.service.spec.ts | ENG-Q4 |
| src/app/core/auth/services/user.service.spec.ts | ENG-Q4 |
| src/app/features/article/services/articles.service.spec.ts | ENG-Q4 |
