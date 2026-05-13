# Agentic Readiness Assessment Report

**Target**: angular-realworld-example-app
**Date**: 2025-07-16
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Service Archetype**: stateless-utility (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: typescript, frontend, angular
**Context**: Angular reference implementation of the RealWorld spec.
**Archetype Justification**: This is a pure frontend SPA (Angular) with no database connections, no persistent state, and no backend runtime. All data is fetched from an external REST API (https://api.realworld.show/api) via HttpClient. The application has no server-side component — it is a client-side-only Single Page Application that runs in the browser.

---

## Readiness Profile: Not Agent-Integrable

**BLOCKERs**: 3 | **RISK-SAFETY**: 9 | **RISK-QUALITY**: 11 | **INFOs**: 11

Exclude from agent toolset or plan major remediation before re-evaluation. This Angular frontend SPA is a browser-only application with no server-side API, no infrastructure-as-code, and no machine identity support. It is fundamentally a UI layer — not an integration surface that agents can call. Agent integration should target the backend API (https://api.realworld.show/api) that this frontend consumes, not the frontend itself.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 3 |
| RISK-SAFETY | 9 |
| RISK-QUALITY | 11 |
| INFO | 11 |
| N/A | 0 |
| Not Evaluated (extended) | 9 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 10
**Extended Questions Not Triggered**: 9
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: stateless-utility (auto-detected)

## BLOCKERs — Must Resolve Before Agent Deployment

### API-Q1: Documented API Interface

- **Severity**: BLOCKER
- **Finding**: This application is a frontend Angular SPA that does not expose any programmatic API. It is a browser-based UI that consumes an external REST API at `https://api.realworld.show/api` via Angular's HttpClient. The only "interface" is the set of browser routes defined in `app.routes.ts` (e.g., `/`, `/login`, `/register`, `/editor`, `/article/:slug`, `/profile`). There is no REST, GraphQL, or AsyncAPI interface exposed by this application. The application is an API consumer, not an API provider.
- **Gap**: No programmatic API surface exists for agent consumption. Agents cannot interact with a browser-only SPA without UI automation (RPA), which is fragile and unscalable.
- **Remediation**:
  - **Immediate**: Redirect agent integration efforts to the backend API (https://api.realworld.show/api) which is the actual service this SPA consumes. Assess that backend independently.
  - **Target State**: If this frontend must be agent-accessible, implement a BFF (Backend-for-Frontend) layer or expose the backend API's OpenAPI spec directly for agent tool binding.
  - **Estimated Effort**: High (architectural change — the frontend itself is not the right target)
  - **Dependencies**: None
- **Evidence**: `src/app/app.routes.ts`, `src/app/core/interceptors/api.interceptor.ts` (URL prefix to external API), all service files under `src/app/features/*/services/`

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: The application supports only user-based JWT authentication. Users log in via email/password at `/users/login`, receive a JWT token, and store it in browser `localStorage` via `JwtService`. The `tokenInterceptor` attaches this token as `Authorization: Token <jwt>` to outgoing requests. There is no support for service accounts, client credentials OAuth 2.0, API keys with principal attribution, or mTLS. Authentication is designed exclusively for human users in a browser context.
- **Gap**: No machine identity authentication mechanism exists. An agent cannot authenticate without using human credentials or browser-based login flows.
- **Remediation**:
  - **Immediate**: Agent integration should target the backend API directly, which may support machine identity. Evaluate the backend API's authentication capabilities independently.
  - **Target State**: If agents must interact through this frontend's domain, implement a server-side BFF with OAuth 2.0 client credentials support for agent identities.
  - **Estimated Effort**: High (requires backend or BFF changes)
  - **Dependencies**: API-Q1 (no API surface to authenticate against)
- **Evidence**: `src/app/core/auth/services/jwt.service.ts` (localStorage-based token storage), `src/app/core/interceptors/token.interceptor.ts` (Token header attachment), `src/app/core/auth/services/user.service.ts` (login/register flows)

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: The `User` model (`user.model.ts`) includes `email` and `token` (JWT) fields — both are sensitive. User email is PII. The JWT token is a credential. There is no data classification at the field level, no tagging of sensitive fields, no field-level encryption, and no controls preventing these fields from being exposed to agents. The `settingsComponent` displays email in an editable form field. Article and comment data also contain author profile information (username, bio, image). No data classification taxonomy exists anywhere in the codebase.
- **Gap**: Sensitive data (PII: email; credential: JWT token) is unclassified and unprotected. No field-level access controls or data classification tags exist.
- **Remediation**:
  - **Immediate**: Document a data classification taxonomy identifying PII fields (email), credentials (token), and public fields (username, bio, image, article content). Apply this to the backend API, not just the frontend.
  - **Target State**: Field-level classification tags on all data models. Sensitive fields redacted or masked when exposed to agent consumers. JWT tokens never exposed in agent-accessible responses.
  - **Estimated Effort**: Medium
  - **Dependencies**: None
- **Evidence**: `src/app/core/auth/user.model.ts` (email, token fields), `src/app/features/settings/settings.component.ts` (email in form), `src/app/features/profile/models/profile.model.ts` (username, bio, image)

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The frontend has no authorization model of its own. It relies entirely on the external backend API for permission enforcement. The frontend distinguishes only between "authenticated" and "unauthenticated" states via `UserService.isAuthenticated` and the `requireAuth` route guard. All authenticated users have identical access to all API endpoints — there is no concept of scoped permissions, IAM policies, or role-based access control in the frontend. No IAM policies exist (no IaC present).
- **Gap**: No scoped permission model exists. An agent identity would inherit the same broad permissions as any authenticated user.
- **Compensating Controls**:
  - Implement scoped permissions at the backend API layer (API Gateway authorizer or application-level RBAC)
  - Use API Gateway resource policies to restrict agent identities to read-only endpoints
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement scoped permissions at the backend API level where authorization can be enforced server-side.
- **Evidence**: `src/app/app.routes.ts` (requireAuth guard — binary auth check only), `src/app/core/auth/if-authenticated.directive.ts` (show/hide UI elements based on auth state only)

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The frontend performs no action-level authorization. Route guards check only whether the user is authenticated, not what actions they can perform. The `canModify` check in `article.component.ts` compares `currentUser.username === article.author.username` to show/hide edit/delete buttons, but this is a UI-only check — the actual enforcement happens server-side. There are no ABAC policies, no fine-grained RBAC, and no action-level permission checks (e.g., canRead vs. canDelete) in the frontend.
- **Gap**: No action-level authorization. The frontend cannot restrict an agent to read-only operations at the application layer.
- **Compensating Controls**:
  - Enforce action-level authorization at the backend API or API Gateway (e.g., method-level authorization per HTTP verb)
  - Create agent-specific API keys with read-only scope at the API Gateway level
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement action-level authorization at the backend API layer. Create agent-specific roles with explicit read/write permissions per resource type.
- **Evidence**: `src/app/app.routes.ts` (requireAuth only), `src/app/features/article/pages/article/article.component.ts` (UI-only canModify check)

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No audit logging infrastructure exists in this frontend application. There are no CloudTrail configurations, no CloudWatch log streams, no immutable log storage, and no log retention policies. The only logging is `console.error` in `main.ts` for bootstrap failures. No write operations log the authenticated principal. There is no IaC in the repository that could define audit logging infrastructure.
- **Gap**: No audit logging of any kind. Agent-initiated actions would be completely untracked.
- **Compensating Controls**:
  - Implement audit logging at the backend API layer (the actual service that processes requests)
  - Enable CloudTrail for any AWS infrastructure the backend uses
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Audit logging must be implemented at the backend API level where server-side operations occur. Frontend-only logging is insufficient for audit trails.
- **Evidence**: `src/main.ts` (only console.error), absence of any IaC files, absence of any logging configuration

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No mechanism exists to suspend or revoke individual agent identities. The frontend supports only token-based authentication via localStorage. Token invalidation requires the backend to reject the token — there are no API key revocation endpoints, no IAM role deactivation, no service account disable mechanisms, and no Cognito user pool integration visible in the frontend code. The `purgeAuth()` method in `UserService` only clears the local token — it does not invalidate it server-side.
- **Gap**: Cannot isolate or revoke a misbehaving agent identity without backend-level intervention.
- **Compensating Controls**:
  - Implement token revocation at the backend API (token blacklist or short-lived tokens with refresh)
  - Use API Gateway API key management for agent identities with instant revocation capability
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement agent identity management with instant revocation at the backend API or API Gateway layer.
- **Evidence**: `src/app/core/auth/services/user.service.ts` (purgeAuth only clears local state), `src/app/core/auth/services/jwt.service.ts` (destroyToken removes from localStorage only)

#### STATE-Q1: Compensation and Rollback ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The frontend has no compensation or rollback patterns. Write operations in `articles.service.ts` (create, update, delete), `comments.service.ts` (add, delete), and `user.service.ts` (update) are fire-and-forget HTTP calls with no undo capability. The editor component (`editor.component.ts`) submits articles via `articleService.create()` or `articleService.update()` with no draft/undo mechanism. There are no saga patterns, no two-phase commits, no compensating transactions, and no Step Functions.
- **Gap**: No rollback or compensation capability for any write operation.
- **Compensating Controls**:
  - Since agent_scope is read-only, this risk is mitigated for the current use case — agents will not execute write operations
  - For future write-enabled scope: implement compensation at the backend API layer
- **Remediation Timeline**: 60–90 days
- **Recommendation**: For read-only agents, this is acceptable. If scope expands to write-enabled, compensation must be implemented at the backend API level.
- **Evidence**: `src/app/features/article/services/articles.service.ts`, `src/app/features/article/services/comments.service.ts`, `src/app/features/article/pages/editor/editor.component.ts`

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The application has limited resilience patterns. The `UserService` implements exponential backoff retry for authentication failures (5XX errors on GET /user — retries at 2s, 4s, 8s, 16s intervals). However, there are no circuit breakers, no general retry logic, no timeout configurations on HTTP clients, and no resilience libraries (Resilience4j, Polly, etc.). The `errorInterceptor` catches errors and normalizes them but does not implement retry or circuit-breaking logic. All service calls (articles, comments, tags, profiles) have no resilience patterns.
- **Gap**: No circuit breakers or general retry logic for external API calls. A cascading failure from the backend API would propagate unmitigated.
- **Compensating Controls**:
  - Implement circuit breakers at the API Gateway or load balancer level fronting the backend API
  - Add HttpClient timeout configurations and retry interceptors to the Angular app
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add an HTTP interceptor with configurable retry logic, timeouts, and circuit-breaking for all outgoing API calls.
- **Evidence**: `src/app/core/auth/services/user.service.ts` (retry logic for auth only), `src/app/core/interceptors/error.interceptor.ts` (error normalization, no retry), `src/app/core/interceptors/api.interceptor.ts` (URL prefix only)

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No rate limiting exists at any layer in this application. There is no API Gateway configuration, no WAF rate rules, no application-level rate limiting middleware, and no IaC defining throttling. The `apiInterceptor` simply prefixes URLs with the backend API base URL. There are no `X-RateLimit-Remaining` headers handled. Since this is a frontend SPA, rate limiting would need to be implemented at the backend API or an intermediary layer.
- **Gap**: No rate limiting to prevent agent traffic storms from overwhelming the backend API.
- **Compensating Controls**:
  - Implement rate limiting at the backend API layer (API Gateway throttling, WAF rate rules)
  - Add client-side request throttling in a custom HTTP interceptor
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Rate limiting must be enforced at the backend API layer. This frontend has no server-side component to enforce limits.
- **Evidence**: `src/app/core/interceptors/api.interceptor.ts` (no throttling), absence of any IaC files, absence of any API Gateway configuration

#### DATA-Q2: Data Residency and Sovereignty ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The application sends all data to `https://api.realworld.show/api` — a third-party hosted backend API. There are no data residency controls, no GDPR/LGPD compliance references, no region-specific configurations, and no documentation of data sovereignty requirements. The API base URL is hardcoded in `api.interceptor.ts`. User data including email addresses is transmitted to this external API. There is no control over where this external API stores or processes data.
- **Gap**: No data residency controls. User PII is transmitted to a third-party API with no documented data residency guarantees.
- **Compensating Controls**:
  - Document data residency requirements and verify the backend API's compliance
  - If data residency is a concern, deploy a self-hosted backend with known data residency guarantees
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document where the backend API stores data and whether it meets residency requirements for the target deployment context.
- **Evidence**: `src/app/core/interceptors/api.interceptor.ts` (hardcoded `https://api.realworld.show/api`)

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No PII redaction exists in any logging pathway. The only logging in the application is `console.error(err)` in `main.ts` which could log error objects containing user data. The `errorInterceptor` normalizes error responses including the full HTTP error body, which could contain PII (email, username) in validation error messages. There are no log scrubbing libraries, no PII masking utilities, no CloudWatch log filters, and no Macie integration.
- **Gap**: PII could leak into browser console logs or error tracking systems. No redaction controls exist.
- **Compensating Controls**:
  - Add PII scrubbing to the error interceptor before logging
  - Configure any error tracking tools (Sentry, etc.) with PII scrubbing rules
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add a PII redaction utility to the error interceptor that strips email, username, and token values from error objects before they reach any logging destination.
- **Evidence**: `src/main.ts` (console.error), `src/app/core/interceptors/error.interceptor.ts` (error bodies passed through without PII scrubbing)

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, GraphQL schema, Smithy, or any other machine-readable API specification exists in this repository. The API endpoints are defined implicitly in service files as URL path strings (e.g., `/articles`, `/articles/:slug`, `/users/login`, `/tags`, `/profiles/:username`). The external backend API may have its own spec (the RealWorld spec defines the API contract at docs.realworld.show), but no machine-readable spec file is present in this repository.
- **Gap**: No machine-readable spec for agent tool generation. Agent tool definitions would require manual authoring.
- **Compensating Controls**:
  - Reference the RealWorld API specification at docs.realworld.show for tool definitions
  - Generate an OpenAPI spec from the backend API and include it in this repository
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add the RealWorld API's OpenAPI specification to this repository as a reference artifact.
- **Evidence**: Absence of any `openapi.yaml`, `swagger.json`, `*.graphql`, or `*.smithy` files in the repository

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The `errorInterceptor` normalizes error responses to a consistent format: `{ errors: { [key]: string[] }, status: number }`. This provides structured error bodies with HTTP status codes. However, there is no retryable boolean or error category classification (retriable vs. terminal). The error format comes from the RealWorld API spec convention. Network errors get a fallback message: `{ errors: { network: ['Unable to connect...'] } }`. The 401 handling distinguishes between auth endpoint errors and other endpoint errors.
- **Gap**: Error responses lack a retryable indicator. Agents cannot programmatically distinguish retriable (timeout, rate limit) from terminal (invalid input, forbidden) errors.
- **Compensating Controls**:
  - Map HTTP status codes to retry behavior in agent tool definitions (e.g., 429/503 → retry, 400/403/404 → terminal)
  - Add a retryable boolean to the error normalization in the interceptor
- **Remediation Timeline**: 7–14 days
- **Recommendation**: Enhance the error interceptor to classify errors as retriable vs. terminal based on HTTP status code.
- **Evidence**: `src/app/core/interceptors/error.interceptor.ts` (structured error format but no retry classification), `src/app/core/models/errors.model.ts`

#### AUTH-Q5: Credential Management — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: JWT tokens are stored in browser `localStorage` via `JwtService`. This is the standard pattern for SPA authentication but has security implications: localStorage is accessible to any JavaScript running on the same origin, making it vulnerable to XSS attacks. There is no secrets management system (no AWS Secrets Manager, no HashiCorp Vault). No credentials are hardcoded in source code. No `.env` files are committed to the repository. The `deploy.yml` workflow references GitHub secrets for AWS credentials and API keys (`secrets.AWS_ACCESS_KEY_ID`, `secrets.ATXCI_API_KEY`) which is appropriate.
- **Gap**: JWT tokens stored in localStorage (XSS-vulnerable). No server-side secrets management for the frontend app itself.
- **Compensating Controls**:
  - The XSS security tests in `e2e/xss-security.spec.ts` provide some mitigation by detecting common XSS vectors
  - Consider httpOnly cookies for token storage if a BFF is implemented
- **Remediation Timeline**: 30–60 days
- **Recommendation**: If a BFF is introduced, store tokens in httpOnly cookies instead of localStorage. For the current SPA architecture, ensure robust XSS protection.
- **Evidence**: `src/app/core/auth/services/jwt.service.ts` (localStorage storage), `.github/workflows/deploy.yml` (GitHub secrets used correctly for CI/CD), `e2e/xss-security.spec.ts` (XSS mitigation tests)

#### DATA-Q3: Selective Query Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The article list supports pagination via `limit` and `offset` parameters, as defined in `ArticleListConfig.filters` and used in `ArticleListComponent.runQuery()`. The `ArticlesService.query()` method passes these filters as URL query parameters. The article list component calculates total pages from `articlesCount`. Tag filtering and author filtering are also supported. However, comment lists (`CommentsService.getAll()`) have no pagination — they return all comments for an article. Tags (`TagsService.getAll()`) also return an unbounded list.
- **Gap**: Article lists support pagination, but comments and tags are returned without pagination controls. Large comment threads or tag lists could overwhelm agent context windows.
- **Compensating Controls**:
  - Limit agent queries to article listing (which has pagination) and individual article/profile retrieval
  - Implement client-side result truncation for unbounded endpoints
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add pagination support to the comments endpoint (backend change) or implement client-side truncation for agent consumption.
- **Evidence**: `src/app/features/article/models/article-list-config.model.ts` (limit/offset filters), `src/app/features/article/components/article-list.component.ts` (pagination logic), `src/app/features/article/services/comments.service.ts` (getAll — no pagination)

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No schema versioning or API contract management exists. API endpoint paths are hardcoded as string literals in service files (e.g., `/articles`, `/users/login`, `/profiles/:username`). There is no URL versioning (`/v1/`, `/v2/`), no `Accept-Version` headers, no changelog, no breaking change detection tools, no consumer-driven contract tests (Pact), and no OpenAPI diff in CI. The RealWorld spec provides an external contract but there is no automated validation that this codebase conforms to it.
- **Gap**: API contracts are implicit and unversioned. Schema changes in the backend API would silently break agent tool bindings.
- **Compensating Controls**:
  - Pin agent tool definitions to a specific RealWorld API version
  - Add contract tests (Pact) that validate the frontend's API expectations against the backend
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add consumer-driven contract tests in CI to detect backend API changes that break frontend expectations.
- **Evidence**: `src/app/features/article/services/articles.service.ts` (hardcoded paths), `src/app/features/article/services/comments.service.ts` (hardcoded paths), absence of any schema versioning or contract testing configuration

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No distributed tracing or structured logging exists. There is no OpenTelemetry SDK, no X-Ray instrumentation, no `traceparent` header propagation, no JSON structured logs, and no correlation IDs. The only logging is `console.error` in `main.ts`. HTTP requests via Angular's HttpClient do not carry trace IDs. Error responses are logged to the browser console in an unstructured format.
- **Gap**: Agent-initiated requests cannot be traced through the system. No correlation between frontend actions and backend processing.
- **Compensating Controls**:
  - Implement tracing at the backend API level (the system that actually processes requests)
  - Add a correlation ID interceptor to the Angular HttpClient that generates and propagates trace IDs
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add an HTTP interceptor that generates a correlation ID for each request and passes it to the backend API.
- **Evidence**: `src/main.ts` (console.error only), absence of any tracing libraries in `package.json`

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No alerting infrastructure exists. There are no CloudWatch alarms, no error rate monitoring, no latency tracking, no anomaly detection, and no PagerDuty/OpsGenie integration. The application has no server-side component where alerting could be configured. As a client-side SPA, monitoring would need to be implemented via a frontend observability tool (e.g., Sentry, Datadog RUM) or at the backend API layer.
- **Gap**: No alerting for API degradation. Agent failures due to backend issues would go undetected.
- **Compensating Controls**:
  - Implement alerting at the backend API layer
  - Add frontend error tracking (Sentry, Datadog RUM) for client-side error visibility
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement alerting at the backend API level and consider adding frontend error tracking.
- **Evidence**: Absence of any monitoring/alerting configuration in the repository

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The only non-production environment is the local development server (`ng serve` on `localhost:4200`). The `playwright.config.ts` configures E2E tests against this local dev server. The `deploy.yml` builds for production and creates a GitHub release. There is no separate staging or sandbox environment configuration, no staging-specific IaC, no synthetic data generators, and no seed data scripts. E2E tests run against the live `api.realworld.show` backend, which is a shared demo environment — not a true isolated staging environment.
- **Gap**: No isolated staging/sandbox environment. Testing against a shared demo backend is insufficient for agent behavior validation.
- **Compensating Controls**:
  - Use the local dev server with a mock backend for initial agent testing
  - Set up a dedicated staging environment with the backend API for agent validation
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Create a docker-compose configuration that spins up both the frontend and a local backend instance for isolated agent testing.
- **Evidence**: `playwright.config.ts` (localhost:4200 dev server), `.github/workflows/deploy.yml` (production build only), absence of staging environment configuration

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No infrastructure-as-code exists in this repository. There are no Terraform files, no CloudFormation templates, no CDK stacks, no Helm charts, and no Kubernetes manifests. The deployment process creates a zip file of the build output and publishes it as a GitHub release. There is no defined infrastructure for API gateways, IAM roles, secrets management, or network configuration. No drift detection is configured.
- **Gap**: No IaC governance. The infrastructure exposing this application (if any) is managed outside this repository with no visibility.
- **Compensating Controls**:
  - If deployed to a CDN/hosting platform, ensure that platform's configuration is managed as code in a separate repository
  - Add IaC for the deployment infrastructure (e.g., S3 + CloudFront for SPA hosting)
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add IaC defining the hosting infrastructure (CDN, S3 bucket, CloudFront distribution) with peer review requirements.
- **Evidence**: Absence of any `.tf`, `.cfn.yaml`, `cdk.json`, or `Chart.yaml` files; `.github/workflows/deploy.yml` (zip + GitHub release only)

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Four CI/CD workflows exist: `deploy.yml` (build, release, optional ATX transform), `playwright.yml` (E2E tests), `lint.yml` (Prettier format check), `security-tests.yml` (XSS security E2E tests). The E2E tests validate UI behavior including CRUD operations against the live backend API. However, there are no API contract tests (no Pact, no OpenAPI spec validation, no schema comparison tools). Breaking changes in the backend API would be caught only if they break E2E test assertions — there is no systematic contract testing.
- **Gap**: No API contract testing in CI. Backend API changes could silently break agent tool bindings without detection.
- **Compensating Controls**:
  - E2E tests provide partial coverage of API contract expectations
  - Add OpenAPI spec validation or Pact consumer tests to the CI pipeline
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add consumer-driven contract tests (Pact) or OpenAPI spec validation to the CI pipeline.
- **Evidence**: `.github/workflows/playwright.yml`, `.github/workflows/lint.yml`, `.github/workflows/security-tests.yml`, `.github/workflows/deploy.yml`

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Deployment creates tagged GitHub releases (`build-<run_number>`) with build artifacts (zip file). Old releases are cleaned up after 7 days (keeping at least 5). There is no blue/green deployment, no canary deployment, no CodeDeploy rollback triggers, no feature flags, and no traffic shifting. Rollback would require manually identifying a previous release and redeploying. The infrastructure for serving the built SPA is not defined in this repository, so rollback mechanisms depend on the hosting platform.
- **Gap**: No automated rollback capability. Recovery from a bad deployment is manual.
- **Compensating Controls**:
  - GitHub releases provide versioned build artifacts for manual rollback
  - If deployed to S3/CloudFront, CloudFront invalidation + S3 version rollback is achievable
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add automated rollback triggers to the deployment pipeline, or implement blue/green deployment at the hosting layer.
- **Evidence**: `.github/workflows/deploy.yml` (GitHub releases with versioned tags, cleanup of old releases)

## INFOs — Architecture and Design Inputs

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Write operations exist in the service layer: `articles.service.ts` (create via POST, update via PUT, delete via DELETE, favorite via POST, unfavorite via DELETE), `comments.service.ts` (add via POST, delete via DELETE), `user.service.ts` (register via POST, login via POST, update via PUT), `profile.service.ts` (follow via POST, unfollow via DELETE). None of these implement idempotency keys or idempotency middleware. The backend API may or may not support idempotency — this is not visible from the frontend code.
- **Implication**: For read-only agents, idempotency of write operations is not a concern. If agent scope expands to write-enabled, this becomes a BLOCKER.
- **Recommendation**: Document idempotency behavior of the backend API before expanding agent scope to write-enabled.
- **Evidence**: `src/app/features/article/services/articles.service.ts`, `src/app/features/article/services/comments.service.ts`, `src/app/core/auth/services/user.service.ts`, `src/app/features/profile/services/profile.service.ts`

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: All API responses are JSON. The Angular HttpClient is configured with typed generics (e.g., `http.get<{ article: Article }>(...)`). Responses are wrapped in domain-specific envelopes: `{ article: Article }`, `{ articles: Article[], articlesCount: number }`, `{ comments: Comment[] }`, `{ tags: string[] }`, `{ profile: Profile }`, `{ user: User }`. No XML, binary, or protobuf formats are used. The `marked` library is used to render Markdown article bodies as HTML on the client side.
- **Implication**: JSON responses are ideal for LLM consumption. The RealWorld API envelope format is consistent and predictable, making agent tool definition straightforward.
- **Recommendation**: No action needed. JSON format is well-suited for agent consumption.
- **Evidence**: `src/app/features/article/services/articles.service.ts` (typed JSON responses), `package.json` (marked library for Markdown rendering)

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limit documentation or rate limit header handling exists in the frontend code. The `apiInterceptor` does not read or propagate `X-RateLimit-Remaining`, `Retry-After`, or similar headers. The backend API at `api.realworld.show` may have rate limits, but they are not documented in this repository. No `aws_api_gateway_usage_plan` or similar IaC exists.
- **Implication**: Agents calling the backend API have no visibility into rate limits. They cannot self-throttle based on remaining quota.
- **Recommendation**: Document the backend API's rate limits. Add rate limit header reading to the HTTP interceptor for agent awareness.
- **Evidence**: `src/app/core/interceptors/api.interceptor.ts` (no rate limit header handling)

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: INFO
- **Finding**: The `tokenInterceptor` attaches the JWT token from localStorage to all outgoing requests as `Authorization: Token <jwt>`. This is user-identity propagation — the backend API uses the JWT to identify the calling user. There is no distinction between "agent acting as itself" vs. "agent acting on behalf of a user". No OAuth2 on-behalf-of flows, no token exchange, no separate IAM roles for different calling contexts. All requests carry the same user identity regardless of context. For a stateless-utility frontend SPA that only consumes a public API, identity propagation complexity is minimal.
- **Implication**: For stateless-utility services returning public/reference data, identity propagation is less critical. If agent delegation patterns are needed, they should be implemented at the backend API layer.
- **Recommendation**: No action needed for current scope. If agent delegation is required, implement OAuth2 token exchange at the backend.
- **Evidence**: `src/app/core/interceptors/token.interceptor.ts` (single token propagation for all requests)

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No concurrency controls exist in the frontend. There are no optimistic locking patterns (version fields, ETags, `If-Match` headers), no pessimistic locking, no DynamoDB conditional writes, and no conflict resolution logic. The frontend performs optimistic UI updates (e.g., incrementing `favoritesCount` on favorite) but does not handle concurrent modification conflicts.
- **Implication**: For read-only agents, concurrency controls are not applicable. If scope expands to write-enabled, concurrent agent writes could cause data integrity issues.
- **Recommendation**: No action needed for read-only scope. If write-enabled, implement ETags or version-based optimistic locking at the backend.
- **Evidence**: `src/app/features/article/pages/article/article.component.ts` (optimistic UI updates without server-side locking)

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No transaction limits or blast radius controls exist. There are no configurable limits on records modified per run, no spend limits, and no delete operation caps. Since this is a frontend SPA with no server-side component, such controls would need to be implemented at the backend API layer.
- **Implication**: For read-only agents, transaction limits are not applicable (no modifications occur). If scope expands to write-enabled, the absence of transaction limits creates unbounded blast radius risk.
- **Recommendation**: No action needed for read-only scope. If write-enabled, implement transaction limits at the backend API layer.
- **Evidence**: Absence of any transaction limit configuration in the codebase

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality metrics, completeness scores, or freshness SLAs exist. There are no data quality dashboards, no null rate monitoring, no duplicate detection, and no data profiling reports. The application consumes data from the external backend API with no quality validation beyond TypeScript type checking on the response shapes.
- **Implication**: Agents acting on potentially incomplete or stale data from the backend API have no visibility into data quality.
- **Recommendation**: Document data quality expectations for the backend API. Consider adding response validation in the HTTP interceptor.
- **Evidence**: Absence of any data quality configuration or monitoring in the repository

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: All field names are human-readable and semantically meaningful. The `Article` model uses: `slug`, `title`, `description`, `body`, `tagList`, `createdAt`, `updatedAt`, `favorited`, `favoritesCount`, `author`. The `User` model uses: `email`, `token`, `username`, `bio`, `image`. The `Profile` model uses: `username`, `bio`, `image`, `following`. The `Comment` model uses: `id`, `body`, `createdAt`, `author`. No legacy codes or abbreviations requiring a data dictionary.
- **Implication**: Field names are LLM-friendly. Agents can interpret field semantics without a lookup table.
- **Recommendation**: No action needed. Naming conventions are already agent-friendly.
- **Evidence**: `src/app/features/article/models/article.model.ts`, `src/app/core/auth/user.model.ts`, `src/app/features/profile/models/profile.model.ts`, `src/app/features/article/models/comment.model.ts`

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No data catalog or metadata layer exists. There is no AWS Glue Data Catalog, no Collibra/Alation/DataHub, no metadata files, no data dictionaries, and no API catalogs. The TypeScript interfaces in model files serve as informal schema documentation but are not discoverable via a catalog system.
- **Implication**: Agent tool definitions must be authored manually from the TypeScript model files. No automated schema discovery is available.
- **Recommendation**: Consider publishing TypeScript model interfaces as a lightweight data dictionary for agent tool development.
- **Evidence**: `src/app/features/article/models/article.model.ts`, `src/app/core/auth/user.model.ts` (TypeScript interfaces as informal schema)

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No business outcome metrics are published. There are no `cloudwatch.put_metric_data` calls, no custom dashboards, no business KPI tracking, and no resolution/conversion/satisfaction metrics. The application has no server-side component where business metrics could be collected.
- **Implication**: When agents consume this system, there are no metrics to determine whether agent interactions produce good outcomes.
- **Recommendation**: Implement business outcome metrics at the backend API level (e.g., article creation rate, comment engagement, user retention).
- **Evidence**: Absence of any metrics or analytics configuration in the repository

### ENG-Q4: API Test Coverage

- **Severity**: INFO
- **Finding**: The application has comprehensive test coverage. Unit tests (Vitest): `jwt.service.spec.ts` (37 tests), `user.service.spec.ts` (20+ tests), `articles.service.spec.ts` (15+ tests), `comments.service.spec.ts` (25+ tests), `tags.service.spec.ts` (30+ tests), `profile.service.spec.ts` (25+ tests). E2E tests (Playwright): 12 spec files covering authentication, articles CRUD, comments, settings, social interactions, navigation, error handling, null field handling, URL navigation, user fetch errors, health checks, and XSS security. The E2E tests run against a live backend API. For a stateless-utility frontend, this represents good coverage.
- **Implication**: Test coverage is solid for a frontend SPA. E2E tests provide indirect validation of API behavior expectations. However, no tests specifically validate agent consumption patterns.
- **Recommendation**: For a stateless-utility frontend, current coverage is adequate. If agent integration is planned, add agent-specific test scenarios.
- **Evidence**: `src/app/core/auth/services/jwt.service.spec.ts`, `src/app/core/auth/services/user.service.spec.ts`, `src/app/features/article/services/articles.service.spec.ts`, `e2e/auth.spec.ts`, `e2e/articles.spec.ts`, `e2e/xss-security.spec.ts`, `vitest.config.ts`, `playwright.config.ts`

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: BLOCKER
- **Finding**: This Angular SPA exposes no programmatic API. It is a browser-based frontend that consumes an external REST API at `https://api.realworld.show/api`. The only "interface" is browser routes (e.g., `/`, `/login`, `/article/:slug`). Integration requires UI automation (RPA), which is fragile and unscalable.
- **Gap**: No REST, GraphQL, or AsyncAPI interface exposed. This application is a consumer, not a provider.
- **Recommendation**: Redirect agent integration to the backend API. If this frontend must be agent-accessible, implement a BFF layer.
- **Evidence**: `src/app/app.routes.ts`, `src/app/core/interceptors/api.interceptor.ts`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, GraphQL schema, or Smithy files exist. API endpoints are defined as URL path strings in service files. The RealWorld spec at docs.realworld.show defines the contract externally.
- **Gap**: No machine-readable spec for agent tool generation.
- **Recommendation**: Add the RealWorld API's OpenAPI specification to this repository.
- **Evidence**: Absence of any `openapi.yaml`, `swagger.json`, `*.graphql`, or `*.smithy` files

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: The `errorInterceptor` normalizes errors to `{ errors: { [key]: string[] }, status: number }`. Network errors get a fallback message. No retryable boolean or error category classification exists.
- **Gap**: No retryable indicator in error responses.
- **Recommendation**: Enhance the error interceptor to classify errors as retriable vs. terminal based on HTTP status code.
- **Evidence**: `src/app/core/interceptors/error.interceptor.ts`, `src/app/core/models/errors.model.ts`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Write operations (create, update, delete, favorite, follow) exist in service files but have no idempotency keys. Backend idempotency behavior is unknown from frontend code.
- **Gap**: No idempotency support visible. Informational for read-only scope.
- **Recommendation**: Document backend API idempotency before expanding to write-enabled scope.
- **Evidence**: `src/app/features/article/services/articles.service.ts`, `src/app/features/article/services/comments.service.ts`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: All responses are JSON with consistent envelope format (`{ article: ... }`, `{ articles: [...], articlesCount: N }`, etc.). Typed via Angular HttpClient generics. Markdown rendering via `marked` library.
- **Gap**: N/A — JSON format is well-suited for agent consumption.
- **Recommendation**: No action needed.
- **Evidence**: `src/app/features/article/services/articles.service.ts`, `package.json`

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has operations >30s OR long-running workflows. This frontend SPA has no long-running operations.
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
- **Finding**: No rate limit documentation or header handling exists in the frontend. The `apiInterceptor` does not read `X-RateLimit-Remaining` or `Retry-After` headers.
- **Gap**: No rate limit visibility for agents.
- **Recommendation**: Document backend API rate limits and add header reading to the HTTP interceptor.
- **Evidence**: `src/app/core/interceptors/api.interceptor.ts`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: Only user-based JWT authentication via email/password login. JWT stored in localStorage, attached as `Authorization: Token <jwt>`. No service accounts, client credentials, API keys with attribution, or mTLS.
- **Gap**: No machine identity authentication. Agents cannot authenticate without human credentials.
- **Recommendation**: Target the backend API directly for agent auth. Implement OAuth 2.0 client credentials if a BFF is added.
- **Evidence**: `src/app/core/auth/services/jwt.service.ts`, `src/app/core/interceptors/token.interceptor.ts`, `src/app/core/auth/services/user.service.ts`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: No authorization model in the frontend. Binary authenticated/unauthenticated distinction only. All authenticated users have identical access. No IAM policies, RBAC, or scoped permissions.
- **Gap**: No scoped permission model. Agent identity inherits broad permissions.
- **Recommendation**: Implement scoped permissions at the backend API level.
- **Evidence**: `src/app/app.routes.ts` (requireAuth guard), `src/app/core/auth/if-authenticated.directive.ts`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization. Route guards check auth status, not action permissions. `canModify` in `article.component.ts` is a UI-only ownership check.
- **Gap**: Cannot restrict agents to read-only at the application layer.
- **Recommendation**: Implement action-level authorization at the backend API (method-level authorization per HTTP verb).
- **Evidence**: `src/app/app.routes.ts`, `src/app/features/article/pages/article/article.component.ts`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: Single JWT token propagated via `tokenInterceptor` for all requests. No distinction between agent-as-self vs. agent-on-behalf-of-user. No OAuth2 token exchange. Archetype calibration: downgraded to INFO for stateless-utility.
- **Gap**: No identity delegation patterns, but acceptable for stateless-utility.
- **Recommendation**: No action needed for current scope.
- **Evidence**: `src/app/core/interceptors/token.interceptor.ts`

#### AUTH-Q5: Credential Management
- **Severity**: RISK-QUALITY
- **Finding**: JWT tokens stored in browser localStorage (XSS-vulnerable). No secrets management system. CI/CD correctly uses GitHub secrets (`secrets.AWS_ACCESS_KEY_ID`, `secrets.ATXCI_API_KEY`). No credentials hardcoded in source. No `.env` files committed.
- **Gap**: localStorage token storage is vulnerable to XSS.
- **Recommendation**: If BFF is introduced, switch to httpOnly cookies. Maintain XSS protection via security tests.
- **Evidence**: `src/app/core/auth/services/jwt.service.ts`, `.github/workflows/deploy.yml`, `e2e/xss-security.spec.ts`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No audit logging infrastructure. Only `console.error` in `main.ts`. No CloudTrail, CloudWatch, or immutable log storage. No IaC to define logging infrastructure.
- **Gap**: Agent actions completely untracked.
- **Recommendation**: Implement audit logging at the backend API level.
- **Evidence**: `src/main.ts`, absence of IaC files

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: No identity suspension mechanism. `purgeAuth()` clears local token only — does not server-side invalidate. No API key revocation, no IAM deactivation, no Cognito integration.
- **Gap**: Cannot revoke a misbehaving agent without backend intervention.
- **Recommendation**: Implement token revocation and agent identity management at the backend API.
- **Evidence**: `src/app/core/auth/services/user.service.ts`, `src/app/core/auth/services/jwt.service.ts`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No compensation or rollback patterns. Write operations are fire-and-forget HTTP calls. No saga patterns, two-phase commits, or compensating transactions. No undo endpoints.
- **Gap**: No rollback capability for any write operation.
- **Recommendation**: Mitigated by read-only scope. Implement compensation at the backend for write-enabled expansion.
- **Evidence**: `src/app/features/article/services/articles.service.ts`, `src/app/features/article/services/comments.service.ts`

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
- **Finding**: No concurrency controls. No optimistic locking (version fields, ETags), no pessimistic locking, no conflict resolution. Frontend performs optimistic UI updates without server-side coordination.
- **Gap**: No concurrency controls, but acceptable for read-only scope.
- **Recommendation**: No action for read-only. Implement at backend for write-enabled scope.
- **Evidence**: `src/app/features/article/pages/article/article.component.ts`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: Limited resilience. `UserService` has exponential backoff retry for auth failures (2s→4s→8s→16s). No general circuit breakers, no retry logic for other endpoints, no timeout configurations, no resilience libraries.
- **Gap**: No circuit breakers for external API calls. Cascading failures propagate unmitigated.
- **Recommendation**: Add HTTP interceptor with retry logic, timeouts, and circuit-breaking.
- **Evidence**: `src/app/core/auth/services/user.service.ts` (auth retry only), `src/app/core/interceptors/error.interceptor.ts`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No rate limiting at any layer. No API Gateway, WAF, or application-level throttling. The `apiInterceptor` only prefixes URLs.
- **Gap**: No protection against agent traffic storms.
- **Recommendation**: Enforce rate limiting at the backend API layer.
- **Evidence**: `src/app/core/interceptors/api.interceptor.ts`, absence of IaC

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No transaction limits or blast radius controls. No configurable limits on records modified, spend, or delete operations.
- **Gap**: No transaction limits, but not applicable for read-only scope.
- **Recommendation**: No action for read-only. Implement at backend for write-enabled scope.
- **Evidence**: Absence of transaction limit configuration

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path. This is P2 priority.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled. Current scope is read-only.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q2: Configurable Approval Gates
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled. Current scope is read-only.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: Only local dev server (`localhost:4200`). E2E tests run against shared demo backend (`api.realworld.show`). No isolated staging environment, no synthetic data generators, no seed data scripts.
- **Gap**: No isolated staging/sandbox for agent testing.
- **Recommendation**: Create docker-compose configuration with local frontend + backend for isolated testing.
- **Evidence**: `playwright.config.ts`, `.github/workflows/deploy.yml`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: `User` model has `email` (PII) and `token` (credential). No data classification tags, no field-level encryption, no access controls on sensitive fields. Settings page displays email in editable form.
- **Gap**: Sensitive data unclassified and unprotected.
- **Recommendation**: Document data classification taxonomy. Apply at backend API level.
- **Evidence**: `src/app/core/auth/user.model.ts`, `src/app/features/settings/settings.component.ts`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: All data transmitted to `https://api.realworld.show/api` — a third-party hosted API. No residency controls, no GDPR/LGPD references, no region-specific configs. API base URL hardcoded.
- **Gap**: No data residency controls for PII transmitted to external API.
- **Recommendation**: Document backend API data residency. Deploy self-hosted backend if residency is required.
- **Evidence**: `src/app/core/interceptors/api.interceptor.ts`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK-QUALITY
- **Finding**: Article lists support pagination (`limit`/`offset`) and filtering (`tag`, `author`, `favorited`). Comments and tags endpoints return unbounded lists.
- **Gap**: Partial pagination. Comments and tags unbounded.
- **Recommendation**: Add pagination to comments endpoint (backend change) or client-side truncation.
- **Evidence**: `src/app/features/article/models/article-list-config.model.ts`, `src/app/features/article/services/comments.service.ts`

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
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator). This frontend has no persistent state.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: No PII redaction. `console.error` in `main.ts` could log user data. `errorInterceptor` passes full error bodies (which may contain email/username) without scrubbing. No log scrubbing libraries, PII masking, or Macie integration.
- **Gap**: PII could leak into console logs or error tracking.
- **Recommendation**: Add PII redaction utility to the error interceptor.
- **Evidence**: `src/main.ts`, `src/app/core/interceptors/error.interceptor.ts`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics, completeness scores, or freshness SLAs. Data consumed from external API with no quality validation beyond TypeScript types.
- **Gap**: No data quality visibility.
- **Recommendation**: Document data quality expectations for the backend API.
- **Evidence**: Absence of data quality configuration

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: No schema versioning or API contract management. Endpoints hardcoded as string literals. No URL versioning, no Accept-Version headers, no changelog, no breaking change detection, no contract tests.
- **Gap**: API contracts implicit and unversioned.
- **Recommendation**: Add consumer-driven contract tests (Pact) in CI.
- **Evidence**: `src/app/features/article/services/articles.service.ts`, `src/app/features/article/services/comments.service.ts`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: All field names are human-readable: `slug`, `title`, `description`, `body`, `tagList`, `createdAt`, `updatedAt`, `favorited`, `favoritesCount`, `author`, `email`, `username`, `bio`, `image`, `following`. No legacy codes or abbreviations.
- **Gap**: None — field names are LLM-friendly.
- **Recommendation**: No action needed.
- **Evidence**: `src/app/features/article/models/article.model.ts`, `src/app/core/auth/user.model.ts`, `src/app/features/profile/models/profile.model.ts`, `src/app/features/article/models/comment.model.ts`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No data catalog (Glue, Collibra, DataHub). TypeScript interfaces in model files serve as informal schema documentation.
- **Gap**: No automated schema discovery.
- **Recommendation**: Publish TypeScript model interfaces as a lightweight data dictionary.
- **Evidence**: `src/app/features/article/models/article.model.ts`, `src/app/core/auth/user.model.ts`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: No tracing or structured logging. No OpenTelemetry, X-Ray, traceparent headers, JSON logs, or correlation IDs. Only `console.error` in `main.ts`.
- **Gap**: Agent-initiated requests cannot be traced. No correlation between frontend and backend.
- **Recommendation**: Add correlation ID HTTP interceptor. Implement tracing at backend.
- **Evidence**: `src/main.ts`, absence of tracing libraries in `package.json`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: No alerting infrastructure. No CloudWatch alarms, no error rate monitoring, no PagerDuty/OpsGenie. No server-side component for alerting.
- **Gap**: No alerting for API degradation.
- **Recommendation**: Implement alerting at backend API. Add frontend error tracking (Sentry, Datadog RUM).
- **Evidence**: Absence of monitoring/alerting configuration

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No business outcome metrics. No custom dashboards, KPI tracking, or metric publishing. No server-side component for metric collection.
- **Gap**: No visibility into agent interaction outcomes.
- **Recommendation**: Implement business metrics at backend API level.
- **Evidence**: Absence of metrics/analytics configuration

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK-QUALITY
- **Finding**: No IaC. No Terraform, CloudFormation, CDK, Helm, or Kubernetes manifests. Deployment produces a zip file published as a GitHub release. No defined infrastructure for API gateways, IAM, secrets, or networking.
- **Gap**: No IaC governance. Hosting infrastructure managed outside this repository.
- **Recommendation**: Add IaC for hosting infrastructure (S3 + CloudFront) with peer review.
- **Evidence**: Absence of IaC files, `.github/workflows/deploy.yml`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: Four workflows: `deploy.yml` (build+release), `playwright.yml` (E2E tests), `lint.yml` (Prettier), `security-tests.yml` (XSS). E2E tests validate UI behavior against live backend. No API contract tests (Pact, OpenAPI validation).
- **Gap**: No systematic API contract testing in CI.
- **Recommendation**: Add consumer-driven contract tests or OpenAPI spec validation.
- **Evidence**: `.github/workflows/playwright.yml`, `.github/workflows/lint.yml`, `.github/workflows/security-tests.yml`, `.github/workflows/deploy.yml`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: GitHub releases with `build-<run_number>` tags. 7-day cleanup keeping 5+ releases. No blue/green, no canary, no rollback triggers, no feature flags.
- **Gap**: No automated rollback. Manual recovery only.
- **Recommendation**: Add automated rollback or blue/green deployment at hosting layer.
- **Evidence**: `.github/workflows/deploy.yml`

#### ENG-Q4: API Test Coverage
- **Severity**: INFO
- **Finding**: Comprehensive unit tests (Vitest): 6 service spec files with 100+ tests total. Comprehensive E2E tests (Playwright): 12 spec files covering auth, CRUD, comments, settings, social, navigation, error handling, XSS security. Good coverage for a frontend SPA. Downgraded to INFO for stateless-utility archetype.
- **Gap**: No agent-specific test scenarios, but general coverage is strong.
- **Recommendation**: Current coverage is adequate. Add agent-specific tests if integration is planned.
- **Evidence**: `src/app/core/auth/services/jwt.service.spec.ts`, `src/app/core/auth/services/user.service.spec.ts`, `src/app/features/article/services/articles.service.spec.ts`, `src/app/features/article/services/comments.service.spec.ts`, `src/app/features/article/services/tags.service.spec.ts`, `src/app/features/profile/services/profile.service.spec.ts`, `e2e/auth.spec.ts`, `e2e/articles.spec.ts`, `e2e/comments.spec.ts`, `e2e/xss-security.spec.ts`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent data stores. This frontend SPA has no database, S3 buckets, or persistent storage.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `src/main.ts` | AUTH-Q6, DATA-Q6, OBS-Q1 |
| `src/app/app.config.ts` | AUTH-Q1 |
| `src/app/app.routes.ts` | API-Q1, AUTH-Q2, AUTH-Q3 |
| `src/app/app.component.ts` | API-Q1 |
| `src/app/core/interceptors/api.interceptor.ts` | API-Q1, API-Q8, STATE-Q5, DATA-Q2 |
| `src/app/core/interceptors/error.interceptor.ts` | API-Q3, STATE-Q4, DATA-Q6 |
| `src/app/core/interceptors/token.interceptor.ts` | AUTH-Q1, AUTH-Q4 |
| `src/app/core/auth/services/jwt.service.ts` | AUTH-Q1, AUTH-Q5, AUTH-Q7 |
| `src/app/core/auth/services/user.service.ts` | AUTH-Q1, AUTH-Q7, STATE-Q1, STATE-Q4 |
| `src/app/core/auth/if-authenticated.directive.ts` | AUTH-Q2 |
| `src/app/core/auth/user.model.ts` | DATA-Q1, DISC-Q2 |
| `src/app/core/models/errors.model.ts` | API-Q3 |
| `src/app/features/article/services/articles.service.ts` | API-Q1, API-Q4, STATE-Q1, DISC-Q1 |
| `src/app/features/article/services/comments.service.ts` | API-Q1, API-Q4, STATE-Q1, DATA-Q3, DISC-Q1 |
| `src/app/features/article/services/tags.service.ts` | API-Q1 |
| `src/app/features/profile/services/profile.service.ts` | API-Q1, API-Q4 |
| `src/app/features/article/models/article.model.ts` | DISC-Q2 |
| `src/app/features/article/models/article-list-config.model.ts` | DATA-Q3 |
| `src/app/features/article/models/comment.model.ts` | DISC-Q2 |
| `src/app/features/profile/models/profile.model.ts` | DATA-Q1, DISC-Q2 |
| `src/app/features/article/components/article-list.component.ts` | DATA-Q3 |
| `src/app/features/article/pages/article/article.component.ts` | AUTH-Q3, STATE-Q3 |
| `src/app/features/article/pages/editor/editor.component.ts` | STATE-Q1 |
| `src/app/features/settings/settings.component.ts` | DATA-Q1 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/deploy.yml` | AUTH-Q5, HITL-Q3, ENG-Q1, ENG-Q2, ENG-Q3 |
| `.github/workflows/playwright.yml` | ENG-Q2, ENG-Q4 |
| `.github/workflows/lint.yml` | ENG-Q2 |
| `.github/workflows/security-tests.yml` | ENG-Q2 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `package.json` | API-Q5, OBS-Q1 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `playwright.config.ts` | HITL-Q3, ENG-Q4 |
| `vitest.config.ts` | ENG-Q4 |
| `angular.json` | API-Q1 |
| `tsconfig.json` | API-Q1 |

### Test Files
| File | Questions Referenced |
|------|---------------------|
| `src/app/core/auth/services/jwt.service.spec.ts` | ENG-Q4 |
| `src/app/core/auth/services/user.service.spec.ts` | ENG-Q4 |
| `src/app/features/article/services/articles.service.spec.ts` | ENG-Q4 |
| `src/app/features/article/services/comments.service.spec.ts` | ENG-Q4 |
| `src/app/features/article/services/tags.service.spec.ts` | ENG-Q4 |
| `src/app/features/profile/services/profile.service.spec.ts` | ENG-Q4 |
| `e2e/auth.spec.ts` | ENG-Q4 |
| `e2e/articles.spec.ts` | ENG-Q4 |
| `e2e/comments.spec.ts` | ENG-Q4 |
| `e2e/xss-security.spec.ts` | AUTH-Q5, ENG-Q4 |
