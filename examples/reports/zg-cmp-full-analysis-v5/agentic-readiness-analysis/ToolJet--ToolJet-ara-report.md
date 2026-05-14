# Agentic Readiness Analysis Report

**Target**: ToolJet (monorepo)
**Date**: 2026-04-30
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**TD Version**: 3g1ipe93e5d2wb6n5d4yqaf9
**Repository Type**: monorepo
**Service Archetype**: stateful-crud (auto-detected) — assessed against server/ service
**Agent Scope**: read-only
**Priority**: P2
**Tags**: javascript, low-code, frontend
**Context**: Open-source low-code internal-tool builder.

**Archetype Justification**: The server/ service is a NestJS application with PostgreSQL (TypeORM, 184+ migrations), Redis, BullMQ job queues, CRUD endpoints for apps/data-sources/queries/users/organizations, user-specific data, and entity lifecycle management — all hallmarks of a stateful-crud archetype.

- **Surface flags** (server/):
  - has_persistent_data_store: true
  - has_http_rpc_surface: true
  - has_auth_surface: true
  - has_write_operations: true
  - has_logging_of_user_data: true

**Monorepo Note**: This is a monorepo. The analysis focuses on `server/` as the primary agent integration target (the NestJS API). The `frontend/` (React SPA), `plugins/` (library), `marketplace/` (library), and `cli/` (dev tool) are noted as supporting context but are not directly agent-callable.

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 2 | **RISK-SAFETY**: 9 | **RISK-QUALITY**: 17 | **INFOs**: 12

> Resolve all blockers before any agent deployment — including pilots. Two BLOCKERs remain: undocumented API surface (API-Q1) and no machine identity authentication (AUTH-Q1). DATA-Q1 is no longer a BLOCKER: the server excludes password from responses and encrypts external-service credentials with a `credential_id` indirection (B1 CLEAR), and enforces strict per-organization multi-tenant isolation plus CASL/`FeatureAbilityGuard`/`PolicyGuard` RBAC (B2 CLEAR); only formal classification metadata (B3) is absent, which resolves to INFO.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 2 |
| RISK-SAFETY | 9 |
| RISK-QUALITY | 17 |
| INFO | 12 |
| N/A | 0 |
| Not Evaluated (extended) | 3 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 16
**Extended Questions Not Triggered**: 3
**Questions N/A (repo_type: monorepo)**: 0
**Service Archetype**: stateful-crud (auto-detected)

## BLOCKERs — Must Resolve Before Agent Deployment

### API-Q1: Documented API Interface

- **Severity**: BLOCKER
- **Finding**: The server/ service exposes a REST API via NestJS controllers (`@Controller`, `@Get`, `@Post`, `@Put`, `@Patch`, `@Delete` decorators) across 50+ modules including `auth/controller.ts`, `apps/`, `data-queries/`, `data-sources/`, `users/`, `organizations/`, `workflows/`, `tooljet-db/`, and more. However, **no OpenAPI/Swagger specification, AsyncAPI specification, or GraphQL schema file exists anywhere in the repository**. The only "openapi" references found are `frontend/src/_services/openapi.service.js` (a frontend client for external OpenAPI data sources) and documentation markdown files — neither describes ToolJet's own API. Integration requires reading NestJS source code to discover endpoints, parameters, and response shapes.
- **Gap**: No machine-discoverable API documentation exists. An agent cannot generate tool bindings without reverse-engineering NestJS controller source code.
- **Remediation**:
  - **Immediate**: Add `@nestjs/swagger` to `server/package.json` and annotate existing controllers with `@ApiTags`, `@ApiOperation`, `@ApiResponse` decorators. NestJS can auto-generate an OpenAPI spec from these annotations.
  - **Target State**: An auto-generated `openapi.json` served at `/api/docs` and committed to the repository, kept current via CI validation.
  - **Estimated Effort**: Medium (2–4 weeks for initial annotation of core endpoints)
  - **Dependencies**: None — can be done independently.
- **Evidence**: `server/src/modules/auth/controller.ts`, `server/src/main.ts`, absence of any `openapi.yaml`/`swagger.json` file in repository.

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: The server/ service implements JWT-based authentication (`@nestjs/jwt`, `passport-jwt`) designed for human users. Authentication flows include email/password login, OAuth2 (Google, GitHub), SAML, OIDC SSO, LDAP, and MFA. Personal Access Tokens (`user_personal_access_tokens` entity) exist but are user-bound, app-scoped, and designed for human-initiated API access — not machine identity. There is **no OAuth2 client credentials flow, no API key with principal attribution for service accounts, and no mTLS configuration**. The system cannot distinguish an agent caller from a human caller in audit logs.
- **Gap**: No machine identity authentication mechanism exists. An agent would need to impersonate a human user, which violates the principle of attribution and auditability.
- **Remediation**:
  - **Immediate**: Extend the PAT system to support machine identity tokens with a dedicated `agent` scope and a non-human principal type. Record the machine identity in audit logs alongside the human who authorized it.
  - **Target State**: OAuth2 client credentials flow or dedicated API key mechanism with principal attribution, allowing agents to authenticate as distinct machine identities with full audit trail.
  - **Estimated Effort**: High (4–8 weeks)
  - **Dependencies**: Resolving this first enables AUTH-Q2 (scoped permissions) and AUTH-Q6 (audit attribution).
- **Evidence**: `server/src/modules/auth/controller.ts`, `server/src/modules/session/service.ts`, `server/src/entities/user_personal_access_tokens.entity.ts`, `server/package.json` (passport-jwt, @nestjs/jwt).

**Remediation Prioritization**: Resolve API-Q1 (OpenAPI spec) and AUTH-Q1 (machine identity) first — they block every downstream control. DATA-Q1 is no longer a BLOCKER (see INFOs): password_digest is excluded from user responses, external-service credentials are stored encrypted under a `credential_id` indirection, and all data-source queries chain `organization_id` filters. The remaining gap is formal classification metadata (B3), which is aspirational, not a deployment gate.

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: CASL-based authorization (`@casl/ability`) defines role-based permissions with specific actions (changeRole, archiveUser, inviteUser, accessGroupPermission, etc.) and subject types (OrganizationUser, User). Group permissions provide organizational scoping. However, there are no agent-specific permission profiles — no pre-built "read-only agent" or "limited-scope agent" role exists. An agent using a human user's credentials inherits that user's full permission set.
- **Gap**: No agent-specific scoped roles exist. The authorization model supports fine-grained permissions but has not been configured for least-privilege agent access.
- **Compensating Controls**:
  - Create a dedicated "agent" group permission with minimal CASL abilities (read-only on specific resources)
  - Use the existing PAT system with app-scoped tokens to limit agent access to specific applications
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create an agent-specific CASL role with read-only permissions on target resources. Configure group permissions to enforce least privilege.
- **Evidence**: `server/src/modules/casl/casl-ability.factory.ts`, `server/src/entities/group_permissions.entity.ts`, `server/src/entities/group_users.entity.ts`.

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: CASL defines action-level abilities (changeRole, archiveUser, inviteUser, accessGroupPermission, updateOrganizations, viewAllUsers, etc.) and `FeatureAbilityGuard` is used in controllers. The `check_policies.decorator.ts` enforces CASL policies at the handler level. However, this action-level authorization is designed for human user roles (admin, builder, viewer) — not for agent-specific action restrictions. An agent impersonating an admin user would inherit all admin actions without additional constraints.
- **Gap**: Action-level authorization mechanism exists but lacks agent-specific action restrictions. No way to allow an agent to read records but block delete operations independently of the human role.
- **Compensating Controls**:
  - Restrict the agent's user role to "viewer" with minimal CASL abilities
  - Implement an API gateway layer that filters allowed HTTP methods per agent token
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Extend CASL abilities to support agent-specific action restrictions, separate from human role-based access.
- **Evidence**: `server/src/modules/casl/casl-ability.factory.ts`, `server/src/modules/casl/check_policies.decorator.ts`, `server/src/modules/auth/ability/`.

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The `audit_log.entity.ts` defines an audit log table with userId, organizationId, resourceId, resourceType, actionType, ipAddress, and metadata. The `ResponseInterceptor` emits audit log events via `EventEmitter2` for every successful API operation. The OTEL `audit-metrics.ts` publishes audit log metrics (audit.logs.total, audit.logs.actions). However, **audit logs are stored in the same PostgreSQL database as application data** — they are not immutable or tamper-evident. No CloudTrail configuration exists in the Terraform IaC. No S3 bucket with object lock for audit log archival. No CloudWatch log file validation. The audit log table has no write-once constraint.
- **Gap**: Audit logs exist but are mutable — stored in PostgreSQL without immutability guarantees. No tamper-evident log storage. No CloudTrail integration.
- **Compensating Controls**:
  - Enable CloudTrail for API-level audit logging with log file validation
  - Stream audit logs to an immutable S3 bucket with Object Lock enabled
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure CloudTrail with log file validation. Stream PostgreSQL audit logs to S3 with Object Lock or CloudWatch Logs with retention policies.
- **Evidence**: `server/src/entities/audit_log.entity.ts`, `server/src/modules/app/interceptors/response.interceptor.ts`, `terraform/ECS/main.tf` (no CloudTrail resource).

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The system supports user status management (invited, verified, active, archived) via `user.entity.ts` and session termination via `session/service.ts` (`terminateSession` deletes `UserSessions` records and clears cookies). However, there is **no dedicated agent identity concept** — agents would authenticate as human users. Suspending an "agent" would mean archiving a human user account or deleting their sessions, which conflates agent identity management with human user management. No API key revocation mechanism exists for machine identities.
- **Gap**: No dedicated agent identity lifecycle. Suspension of a misbehaving agent requires manipulating a human user account.
- **Compensating Controls**:
  - Use the PAT expiry mechanism (`expiresAt` field) to set short-lived agent tokens
  - Implement a manual process to delete agent-associated PATs and sessions
- **Remediation Timeline**: 60–90 days (depends on AUTH-Q1 resolution)
- **Recommendation**: Implement dedicated agent identity management with independent suspension/revocation capabilities, separate from human user lifecycle.
- **Evidence**: `server/src/entities/user.entity.ts` (status enum), `server/src/modules/session/service.ts` (terminateSession), `server/src/entities/user_personal_access_tokens.entity.ts`.

#### STATE-Q1: Compensation and Rollback ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The server/ service integrates Temporal workflows (`@temporalio/client`, `@temporalio/worker`, `@temporalio/workflow`, `@temporalio/activity`) which provide built-in compensation and retry capabilities for workflow executions. The `WorkflowExecution` entity tracks execution state with edges and nodes. However, **outside of the workflows module, there is no general compensation or rollback pattern** for standard CRUD operations on apps, data sources, queries, or users. No saga pattern for multi-step API operations. No explicit undo endpoints.
- **Gap**: Temporal provides compensation for workflow operations only. Standard CRUD operations across apps, data sources, and queries have no compensation or rollback mechanism.
- **Compensating Controls**:
  - Restrict agent scope to read-only operations (current configuration)
  - Implement database transaction wrapping for multi-step operations via `dbTransactionWrap`
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement compensation patterns for critical write operations. Leverage the existing `dbTransactionWrap` helper to ensure atomicity.
- **Evidence**: `server/src/modules/workflows/module.ts` (Temporal integration), `server/package.json` (@temporalio/*), `server/src/modules/session/service.ts` (dbTransactionWrap usage).

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The server/ service makes external HTTP calls via the `got` library (v11.8.2) to data sources, plugins, and external APIs. The `express-http-proxy` library proxies requests. The service connects to external services including Google Auth, GitHub, Okta (OIDC), LDAP servers, SMTP servers, and various data source connectors (via the plugins system). **No circuit breaker, retry logic with exponential backoff, or timeout configuration was found** in the application code for these external calls. No Resilience4j, Polly, or equivalent resilience library is in `server/package.json`. The `got` library supports retries and timeouts but no explicit configuration was found.
- **Gap**: No circuit breakers or resilience patterns protect the server from cascading failures when external dependencies (data sources, SSO providers, SMTP) are unavailable.
- **Compensating Controls**:
  - Configure `got` client with explicit timeouts and retry limits
  - Implement health check-based circuit breaking at the load balancer level
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add circuit breaker middleware (e.g., `opossum` for Node.js) for external HTTP calls. Configure explicit timeouts on the `got` client instances.
- **Evidence**: `server/package.json` (got, express-http-proxy, openid-client, ldapts, nodemailer — all external call dependencies), absence of any circuit breaker library.

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The `@nestjs/throttler` package is installed (`server/package.json`), but the `ThrottlerModule` is configured **only in the workflows module** (`server/src/modules/workflows/module.ts`) with configurable `WEBHOOK_THROTTLE_TTL` (default 60000ms) and `WEBHOOK_THROTTLE_LIMIT` (default 100). **No application-wide rate limiting is configured** in `server/src/main.ts` or the root `AppModule`. No API Gateway throttling configuration exists in the Terraform IaC. No WAF rate rules. The bulk of the API surface (apps, data queries, users, organizations, auth) has no rate limiting.
- **Gap**: Rate limiting exists only for workflow webhook endpoints. The rest of the API surface has no rate limiting protection against agent traffic storms.
- **Compensating Controls**:
  - Apply ThrottlerModule globally in AppModule with sensible defaults
  - Configure API Gateway or ALB throttling rules in the Terraform IaC
- **Remediation Timeline**: 7–14 days (quick win)
- **Recommendation**: Enable ThrottlerModule globally in `server/src/main.ts` or the root AppModule. Add API Gateway usage plans with throttle settings in Terraform.
- **Evidence**: `server/src/modules/workflows/module.ts` (ThrottlerModule), `server/package.json` (@nestjs/throttler), `server/src/main.ts` (no global throttler), `terraform/ECS/main.tf` (no API Gateway throttling).

#### DATA-Q2: Data Residency and Sovereignty ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The system stores user data, organization data, credentials, and SSO configurations in PostgreSQL. The Terraform ECS configuration defaults to `us-east-1` region (`terraform/ECS/variables.tf`). **No data residency controls, GDPR/LGPD compliance configuration, or region-specific data storage rules exist in the codebase or IaC.** No cross-region replication restrictions. The multi-tenant organization model stores all tenants' data in the same database without region-based partitioning. An agent sending this data to an LLM provider in a different jurisdiction could create compliance exposure for tenants subject to data sovereignty requirements.
- **Gap**: No data residency controls. All tenant data stored in a single region without sovereignty enforcement.
- **Compensating Controls**:
  - Ensure LLM provider endpoints are in the same AWS region as the database
  - Document data residency constraints for agent operators
- **Remediation Timeline**: 60–120 days
- **Recommendation**: Implement region-aware data storage configuration. Add data residency metadata to organization entities. Document compliance boundaries.
- **Evidence**: `terraform/ECS/variables.tf` (region = us-east-1), `terraform/ECS/main.tf` (aws_db_instance without region constraints), `server/src/entities/organization.entity.ts`.

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The OpenTelemetry tracing configuration (`server/src/otel/tracing.ts`) **logs the full HTTP request body as a span attribute** (`span.setAttribute('http.body', JSON.stringify(sanitizeObject(request.body)))`) for all API requests matching `/api/` routes. This means login requests containing email/password, user profile updates containing PII, and data source credential configuration requests are all captured in OTEL trace spans. The `sanitizeObject` function only removes functions — it does NOT redact PII fields. The `AllExceptionsFilter` logs full request headers (`request.headers`) which may contain auth tokens. The `TransactionLogger` logs transactionId and route (structured, non-PII), which is appropriate. No PII masking library, log scrubbing middleware, or Amazon Macie integration was found.
- **Gap**: OTEL tracing captures full request bodies (including PII) in trace spans. No PII redaction in tracing or error logging.
- **Compensating Controls**:
  - Add a sanitization layer to the OTEL `requestHook` that strips known PII fields (email, password, phone, tokens) before setting span attributes
  - Disable `http.body` attribute in production OTEL configuration
- **Remediation Timeline**: 7–14 days (quick win)
- **Recommendation**: Modify the Express instrumentation `requestHook` in `tracing.ts` to exclude sensitive fields from `http.body`. Add a PII field blocklist.
- **Evidence**: `server/src/otel/tracing.ts` (line: `span.setAttribute('http.body', JSON.stringify(sanitizeObject(request.body)))`), `server/src/modules/app/filters/all-exceptions-filter.ts` (logs request.headers).

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY
- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, GraphQL schema, or Smithy model exists. NestJS supports `@nestjs/swagger` for auto-generation but it is not installed.
- **Gap**: No machine-readable specification for automated tool generation.
- **Compensating Controls**: Manual tool definition from source code analysis; use NestJS decorators as source of truth.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Install `@nestjs/swagger` and generate OpenAPI spec from controller decorators.
- **Evidence**: `server/package.json` (no @nestjs/swagger), absence of openapi/swagger files.

#### API-Q3: Structured Error Responses — RISK-QUALITY
- **Severity**: RISK-QUALITY
- **Finding**: `AllExceptionsFilter` returns JSON with `statusCode`, `timestamp`, `path`, `message`, and `code`. Differentiates HttpException, TooljetDatabaseError, and QueryFailedError. However, **no `retryable` field** or error category distinguishing retriable from terminal errors exists.
- **Gap**: Error responses lack a retryable indicator. Agents cannot distinguish transient from permanent failures.
- **Compensating Controls**: Agents can infer retryability from HTTP status codes (429, 503 = retry; 400, 403 = terminal).
- **Remediation Timeline**: 7–14 days
- **Recommendation**: Add a `retryable` boolean or `error_category` field to the error response format.
- **Evidence**: `server/src/modules/app/filters/all-exceptions-filter.ts`.

#### AUTH-Q4: Identity Propagation and Delegation — RISK-QUALITY
- **Severity**: RISK-QUALITY
- **Finding**: JWT tokens carry user context through API calls. The `@User()` decorator extracts authenticated user from requests. Multi-workspace support propagates organization context. However, no on-behalf-of flow or token exchange pattern exists. No distinction between agent-as-self vs agent-on-behalf-of-user.
- **Gap**: No delegation or on-behalf-of flow. Single identity model conflates agent and user contexts.
- **Compensating Controls**: Agent operates under its own user identity; audit logs record the user ID.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement token exchange or delegation claims in JWT to distinguish agent-acting-as-self from agent-on-behalf-of-user.
- **Evidence**: `server/src/modules/auth/controller.ts`, `server/src/modules/session/service.ts`.

#### AUTH-Q5: Credential Management — RISK-QUALITY
- **Severity**: RISK-QUALITY
- **Finding**: Mixed approach. The `EncryptionService` encrypts data source credentials using AES-256-GCM with Lockbox pattern. An IAM policy for Secrets Manager access exists (`secrets_manager_policy` in `terraform/ECS/main.tf`). However, **sensitive values are passed as plaintext environment variables** in the ECS task definition (`LOCKBOX_MASTER_KEY`, `SECRET_KEY_BASE`, `PG_PASS`, `REDIS_PASSWORD`, `PGRST_JWT_SECRET`). The `docker-compose.yaml` references `.env` file with credentials. Terraform variables have empty defaults for secrets but no `sensitive = true` annotation.
- **Gap**: Secrets Manager policy exists but secrets are passed as plaintext env vars in ECS task definitions and docker-compose. No rotation configuration.
- **Compensating Controls**: Migrate ECS task definition secrets to Secrets Manager references. Add `sensitive = true` to Terraform variables.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Reference secrets from AWS Secrets Manager in ECS task definitions. Mark Terraform variables as sensitive.
- **Evidence**: `terraform/ECS/main.tf` (secrets_manager_policy, plaintext env vars), `terraform/ECS/variables.tf` (no sensitive annotations), `.env.example`.

#### STATE-Q2: Queryable Current State — RISK-QUALITY
- **Severity**: RISK-QUALITY
- **Finding**: The API exposes GET endpoints for querying current state of apps, data sources, queries, users, organizations, and versions. The `app_version.entity.ts` tracks version status (DRAFT, PUBLISHED, RELEASED). Status fields exist on multiple entities. However, there is no unified "state query" API for an agent to inspect the full state of a resource before taking action.
- **Gap**: Individual resource GET endpoints exist but no consolidated state API for agent decision-making.
- **Compensating Controls**: Agents can query individual endpoints to assemble current state.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document the state query patterns for agent consumption.
- **Evidence**: `server/src/entities/app_version.entity.ts` (status enum), `server/src/modules/apps/`, `server/src/modules/data-queries/`.

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY
- **Severity**: RISK-QUALITY
- **Finding**: `docker-compose.yaml` provides a local development environment with PostgreSQL, Redis, and PostgREST. Terraform templates exist for ECS, EC2, Azure VM, and GCP deployments. The `app-environments` module provides application-level environment management (development, staging, production). However, **no production-equivalent staging environment configuration** is defined — no separate staging Terraform workspace, no staging Helm values, no seed data scripts for realistic test data.
- **Gap**: Local dev environment exists but no production-equivalent staging for agent testing.
- **Compensating Controls**: Use docker-compose environment with seed data for agent testing. Leverage app-environments module to create staging environments.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a staging Terraform workspace or Helm values override with production-equivalent data shape.
- **Evidence**: `docker-compose.yaml`, `deploy/helm/values.yaml`, `server/src/modules/app-environments/`, `terraform/ECS/`.

#### DATA-Q3: Selective Query Support — RISK-QUALITY
- **Severity**: RISK-QUALITY
- **Finding**: Some list endpoints support basic pagination and filtering. The ToolJet DB module (PostgREST) provides pagination, filtering, and sorting natively. However, pagination support is not consistent across all API endpoints — some list endpoints may return unbounded result sets.
- **Gap**: Pagination is not uniformly enforced across all list endpoints.
- **Compensating Controls**: Agents can use the ToolJet DB API (PostgREST) which has built-in pagination.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Audit all list endpoints and enforce pagination with configurable limits.
- **Evidence**: `server/src/modules/tooljet-db/`, `docker-compose.yaml` (PostgREST service).

#### DATA-Q4: System of Record Designations — RISK-QUALITY
- **Severity**: RISK-QUALITY
- **Finding**: No system-of-record designations or master data management documentation found. The system owns user, organization, app, and workflow data but does not formally declare itself as the system of record. No conflict resolution logic for data shared across services.
- **Gap**: No formal system-of-record designations for key entities.
- **Compensating Controls**: Document ToolJet as the system of record for its owned entities (users, apps, workflows).
- **Remediation Timeline**: 7–14 days (documentation)
- **Recommendation**: Create a data ownership document declaring system-of-record status for each entity type.
- **Evidence**: `server/src/entities/` (80+ entity files), absence of data ownership documentation.

#### DATA-Q5: Temporal Metadata and Freshness — RISK-QUALITY
- **Severity**: RISK-QUALITY
- **Finding**: All entities include `created_at` and `updated_at` timestamps with `@CreateDateColumn` and `@UpdateDateColumn` decorators using `default: () => 'now()'`. `app_version.entity.ts` has `publishedAt` and `releasedAt` timestamps. The `audit_log.entity.ts` has `created_at`. However, **no Cache-Control headers, data freshness indicators, or consistency level signals** are returned in API responses. No timezone normalization documentation.
- **Gap**: Timestamps exist on entities but no freshness signaling in API responses.
- **Compensating Controls**: Agents can check `updated_at` fields in response data to assess freshness.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add `Last-Modified` and `Cache-Control` headers to API responses.
- **Evidence**: `server/src/entities/user.entity.ts` (createdAt, updatedAt), `server/src/entities/app_version.entity.ts` (publishedAt, releasedAt).

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY
- **Severity**: RISK-QUALITY
- **Finding**: URI-based API versioning enabled in `main.ts` (`VersioningType.URI`). TypeORM migrations (184 schema migrations + 174 data migrations) provide schema evolution. `CODEOWNERS` requires review for migration files. However, **no breaking change detection in CI** — no Pact consumer-driven contract tests, no OpenAPI diff, no `buf breaking` equivalent. No changelog or deprecation notices for API changes.
- **Gap**: Schema versioning exists but no automated breaking change detection in the CI pipeline.
- **Compensating Controls**: CODEOWNERS review for migrations provides manual change detection. URI versioning allows version-gated agent tool bindings.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenAPI spec generation and diff comparison to the CI pipeline to detect breaking changes automatically.
- **Evidence**: `server/src/main.ts` (VersioningType.URI), `server/migrations/` (184 files), `CODEOWNERS`, `.github/workflows/ci.yml` (no contract testing).

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY
- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive OTEL instrumentation exists: `NodeSDK` with `BatchSpanProcessor`, `OTLPTraceExporter`, instrumentation for Express, HTTP, NestJS, PostgreSQL, and Pino. W3C trace context propagation (`W3CTraceContextPropagator`, `W3CBaggagePropagator`). Structured logging via `nestjs-pino`. `TransactionLogger` provides structured logs with `transactionId`, `route`, and `checkPointer` for request correlation. **However, OTEL is gated behind an edition check** — only EE (Enterprise) and Cloud editions initialize the SDK. The CE (Community Edition) has no distributed tracing at all.
- **Gap**: Distributed tracing and structured logging exist but are restricted to Enterprise/Cloud editions. Community Edition deployments have no tracing.
- **Compensating Controls**: Enable OTEL for CE edition via environment variable override. Use pino structured logging as a baseline for all editions.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Consider making basic OTEL tracing available in CE edition, or document the limitation for agent operators.
- **Evidence**: `server/src/otel/tracing.ts` (edition check: EE/Cloud only), `server/src/modules/logging/service.ts` (TransactionLogger with pino).

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY
- **Severity**: RISK-QUALITY
- **Finding**: OTEL metrics are exported (api.hits, api.duration histogram) but **no alerting thresholds are configured in the codebase or IaC**. No CloudWatch alarms. No PagerDuty/OpsGenie integration. No SLO-based alerting. CloudWatch log groups exist with 30-day retention (`/ecs/ToolJet`), and Container Insights is enabled on the ECS cluster, but no alarms are defined.
- **Gap**: Metrics exist but no alerting thresholds for error rates or latency.
- **Compensating Controls**: CloudWatch Container Insights provides basic monitoring. Manual alerting can be configured on the CloudWatch log group.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Define CloudWatch alarms for error rate (5xx responses > threshold) and latency (P99 > threshold) on the ALB target group.
- **Evidence**: `terraform/ECS/main.tf` (containerInsights enabled, log groups, no alarms), `server/src/otel/tracing.ts` (api.duration histogram).

#### ENG-Q1: Infrastructure Governance — RISK-QUALITY
- **Severity**: RISK-QUALITY
- **Finding**: Terraform IaC defines the integration surface: ECS cluster, ALB, security groups, RDS, VPC, subnets. Helm charts exist for Kubernetes deployments. `CODEOWNERS` requires peer review for package.json and module.ts changes (including migration files). However, **no drift detection** (no AWS Config rules, no Terraform Cloud, no `terraform plan` in CI), and IaC changes are not validated in pull requests via automated plan review.
- **Gap**: IaC exists and CODEOWNERS provides peer review, but no drift detection or automated plan review in CI.
- **Compensating Controls**: Manual `terraform plan` reviews before applying changes.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add `terraform plan` as a CI step on PRs that modify `terraform/` files. Enable AWS Config drift detection.
- **Evidence**: `terraform/ECS/main.tf`, `deploy/helm/`, `CODEOWNERS`, `.github/workflows/ci.yml` (no terraform plan step).

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY
- **Severity**: RISK-QUALITY
- **Finding**: CI pipeline (`.github/workflows/ci.yml`) includes build, lint (frontend, server, plugins), unit tests, and e2e tests with PostgreSQL. Vulnerability scanning runs weekly (`vulnerability-ci.yml`) with npm audit and automated fix PRs. Docker release workflow builds and pushes multi-edition images. License compliance checks exist. However, **no API contract testing** — no Pact, no OpenAPI validation, no schema comparison tools in the CI pipeline.
- **Gap**: CI has comprehensive testing but no API contract testing to catch agent-breaking changes.
- **Compensating Controls**: E2E tests provide some API coverage. CODEOWNERS review catches module.ts changes.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenAPI spec validation or consumer-driven contract tests (Pact) to the CI pipeline.
- **Evidence**: `.github/workflows/ci.yml` (build, lint, unit-test, e2e-test), `.github/workflows/vulnerability-ci.yml`, absence of contract testing.

#### ENG-Q3: Rollback Capability — RISK-QUALITY
- **Severity**: RISK-QUALITY
- **Finding**: ECS service configured with `deployment_maximum_percent = 200` and `deployment_minimum_healthy_percent = 100`, supporting rolling updates with zero-downtime deploys. Helm chart exists for Kubernetes (`deploy/helm/`) enabling `helm rollback`. Docker release workflow publishes tagged images (`tooljet/tooljet:$tag`). However, **no explicit rollback trigger or canary deployment** is configured. No CodeDeploy rollback integration. No feature flags for gradual rollout.
- **Gap**: Rolling update supports implicit rollback but no explicit rollback triggers or canary deployments.
- **Compensating Controls**: ECS rolling update allows manual rollback by updating task definition to previous version. Helm rollback available for K8s.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add explicit rollback triggers (e.g., CloudWatch alarm-based) to the ECS deployment configuration.
- **Evidence**: `terraform/ECS/main.tf` (deployment_maximum_percent, deployment_minimum_healthy_percent), `deploy/helm/`, `.github/workflows/docker-release.yml`.

#### ENG-Q4: API Test Coverage — RISK-QUALITY
- **Severity**: RISK-QUALITY
- **Finding**: Unit tests exist (`server/test/`, `jest.config.ts`, `test` and `test:e2e` scripts). E2E tests run in CI with PostgreSQL. Cypress tests exist (`cypress-tests/` directory) covering app builder, marketplace, and platform flows. The CI pipeline runs both unit and e2e tests. However, **no dedicated API contract tests** validate input handling, output format, and error responses systematically. Test coverage metrics are generated (`test:cov` script) but not enforced in CI.
- **Gap**: Tests exist but no systematic API contract test coverage. Coverage thresholds not enforced in CI.
- **Compensating Controls**: E2E tests exercise API endpoints. Cypress tests cover UI-driven API flows.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add API contract tests for agent-facing endpoints. Enforce minimum coverage thresholds in CI.
- **Evidence**: `server/package.json` (test scripts), `.github/workflows/ci.yml` (unit-test, e2e-test jobs), `cypress-tests/`.

#### ENG-Q5: Encryption at Rest — RISK-QUALITY
- **Severity**: RISK-QUALITY
- **Finding**: The `aws_db_instance.tooljet_database` in `terraform/ECS/main.tf` does **not** configure `storage_encrypted = true` or `kms_key_id`. The RDS instance stores all application data including PII, credentials (encrypted at application level), and audit logs — but the disk itself is unencrypted. Redis runs as a sidecar container in the ECS task definition with no encryption at rest. The application-level Lockbox encryption (`EncryptionService`) protects credential values but not the broader dataset.
- **Gap**: RDS database is not encrypted at rest at the infrastructure level. Redis has no encryption at rest.
- **Compensating Controls**: Application-level encryption (Lockbox) protects credential values. PGSSLMODE=require enforces encryption in transit.
- **Remediation Timeline**: 7–14 days (quick win for RDS)
- **Recommendation**: Add `storage_encrypted = true` to the `aws_db_instance` resource. Consider managed Redis (ElastiCache) with encryption at rest.
- **Evidence**: `terraform/ECS/main.tf` (aws_db_instance without storage_encrypted), `server/src/modules/encryption/service.ts` (application-level encryption).

## INFOs — Architecture and Design Inputs

### DATA-Q1: Sensitive Data Classification ⚡ (Tiered) — Demoted from BLOCKER

- **Severity**: INFO
- **Stage A**: Yes — User (bcrypt passwords, username), Session (IP-derived geolocation, browser fingerprint), WebsiteEvent (referrer/UTM/click IDs), SessionData/EventData (arbitrary user-tracked fields), Revenue (financial amounts).
- **B1 — Agent-facing API response scoping: CLEAR.** `findUser()` uses `select: { password: includePassword, ... }` with `includePassword` defaulting to false (`src/queries/prisma/user.ts:14-28`). `src/app/api/admin/users/route.ts` uses explicit `omit: { password: true }`. The login route (`src/app/api/auth/login/route.ts`) returns `{ token, user: { id, username, role, createdAt, isAdmin, teams } }` — password is never serialized into any response.
- **B2 — Access control differentiation: CLEAR.** Seven distinct roles with a real permission matrix (`src/lib/constants.ts` — `ROLE_PERMISSIONS` maps admin, user, view-only, team-owner, team-manager, team-member, team-view-only to specific capabilities). Resource-level guards in `src/permissions/website.ts` and `src/permissions/user.ts` enforce ownership and team-scope checks.
- **B3 — Formal classification metadata: INFO.** No `@PII`/`@Sensitive` decorators on Prisma models, no Macie/Presidio integration, no documented classification policy.
- **Overall**: Only B3 contributes a finding → **DATA-Q1 = INFO**. Systematic response-shaping and granular RBAC mean the actual agent-leakage risk is low.
- **Implication**: Not a deployment gate. Classification metadata is a governance concern, not a code-level safety gap.
- **Recommendation (aspirational)**: Add schema-comment or decorator-based classification tags to `prisma/schema.prisma`; consider a lint/CI check that prevents `includePassword: true` outside authentication paths.
- **Evidence**: `src/queries/prisma/user.ts`, `src/app/api/admin/users/route.ts`, `src/app/api/auth/login/route.ts`, `src/lib/constants.ts`, `src/permissions/website.ts`, `src/permissions/user.ts`, `prisma/schema.prisma`.

### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Write endpoints exist (POST for app creation, PUT/PATCH for updates, DELETE for removal). No idempotency key support or idempotency middleware found. However, read-only agents do not execute write operations.
- **Implication**: If agent scope is expanded to write-enabled in the future, idempotency must be addressed as a BLOCKER.
- **Recommendation**: Plan idempotency key support for write endpoints if write-enabled agent scope is anticipated.
- **Evidence**: `server/src/modules/auth/controller.ts`, `server/src/modules/apps/`.

### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: All API responses use JSON format via NestJS default serialization. `ResponseInterceptor` processes responses with structured metadata. Content-type is `application/json`. No XML or binary formats. SCIM endpoints support `application/scim+json`.
- **Implication**: JSON is ideal for agent consumption via LLM-based reasoning. No additional parsing required.
- **Recommendation**: No action needed.
- **Evidence**: `server/src/main.ts` (SCIM JSON parser), `server/src/modules/app/interceptors/response.interceptor.ts`.

### API-Q6: Asynchronous Operation Support
- **Severity**: INFO
- **Finding**: BullMQ job queues handle workflow scheduling and execution (`workflow-schedule-queue`, `workflow-execution-queue`). Temporal workflows provide long-running operation support. SSE (Server-Sent Events) endpoints exist for workflow streaming and app history. The Bull Board dashboard (`/jobs`) provides job visibility.
- **Implication**: Async patterns are well-implemented for workflows. Agents consuming workflow operations can use polling or SSE for status updates.
- **Recommendation**: Document async operation patterns for agent tool definitions.
- **Evidence**: `server/src/modules/workflows/module.ts` (BullMQ queues), `server/package.json` (@temporalio/*, bullmq).

### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: `EventEmitter2` (`@nestjs/event-emitter`) emits events for audit log entries and workflow state changes. BullMQ publishes job events. The `ResponseInterceptor` emits `auditLogEntry` events on successful operations. OTEL metrics track state changes (app creates, updates, deletes, releases).
- **Implication**: Event-driven agent patterns are possible using the existing event infrastructure.
- **Recommendation**: Consider exposing a webhook or event subscription API for external agent consumption.
- **Evidence**: `server/src/modules/app/interceptors/response.interceptor.ts` (EventEmitter2), `server/src/otel/audit-metrics.ts`.

### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: ThrottlerModule in workflows module configures `WEBHOOK_THROTTLE_TTL` and `WEBHOOK_THROTTLE_LIMIT`. No `X-RateLimit-Remaining`, `Retry-After`, or similar headers are returned by the API. Rate limits are not documented.
- **Implication**: Agents cannot self-throttle without rate limit awareness. Combined with STATE-Q5 (no global rate limiting), this creates risk of agent traffic overwhelming the service.
- **Recommendation**: Return rate limit headers from the ThrottlerModule. Document limits for agent operators.
- **Evidence**: `server/src/modules/workflows/module.ts`, `server/package.json` (@nestjs/throttler).

### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No explicit optimistic locking (@Version decorator, ETag headers, If-Match) found in TypeORM entities. No `SELECT FOR UPDATE` patterns. The `AppVersion` entity uses unique constraints (`@Unique(['name', 'appId'])`) which prevent duplicate version names but not concurrent modification conflicts.
- **Implication**: If agent scope is expanded to write-enabled, concurrency controls must be added to prevent race conditions.
- **Recommendation**: Plan optimistic locking for critical entities if write-enabled agent scope is anticipated.
- **Evidence**: `server/src/entities/app_version.entity.ts` (Unique constraint only).

### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits per agent identity found (max records per operation, max spend per hour, etc.). Read-only agents do not modify records.
- **Implication**: If agent scope is expanded to write-enabled, transaction limits must be implemented.
- **Recommendation**: Plan configurable transaction limits for write-enabled agent operations.
- **Evidence**: No evidence found — absence is the finding.

### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality score, completeness metrics, null rate monitoring, or data freshness SLAs found. OTEL metrics track operation counts but not data quality.
- **Implication**: Agents acting on data cannot assess its quality. Low data quality propagates errors at machine speed.
- **Recommendation**: Consider adding data quality metrics for key entities (users, apps, data sources).
- **Evidence**: No data quality metrics found in `server/src/otel/` or `server/src/modules/`.

### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Entity field names are semantically clear and human-readable: `firstName`, `lastName`, `email`, `phoneNumber`, `organizationId`, `createdAt`, `updatedAt`, `resourceType`, `actionType`, `ipAddress`. No legacy code abbreviations found. TypeORM column names use snake_case in the database (`first_name`, `last_name`) with camelCase in TypeScript — standard convention.
- **Implication**: Field names are LLM-friendly. No data dictionary needed for agent reasoning.
- **Recommendation**: No action needed. Maintain current naming conventions.
- **Evidence**: `server/src/entities/user.entity.ts`, `server/src/entities/audit_log.entity.ts`.

### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No data catalog (AWS Glue, Collibra, DataHub) or metadata layer found. Entity definitions in `server/src/entities/` (80+ files) serve as the de facto schema documentation. TypeORM decorators provide column types and relationships.
- **Implication**: Agent tool builders must read entity files to understand data structures. A metadata layer would accelerate tool definition.
- **Recommendation**: Consider auto-generating a data dictionary from TypeORM entity decorators.
- **Evidence**: `server/src/entities/` (80+ entity files).

### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: **Excellent custom business metrics** in `audit-metrics.ts`: `query.executions.total` (with mode/environment labels), `query.failures.total`, `query.duration`, `app.usage.total`, `app.active_users`, `app.success_rate`, `app.errors.total`, `audit.logs.total`, `user.sessions.total`, `app.creations.total`, `app.updates.total`, `app.deletions.total`, `app.releases.total`, `datasource.creations.total`, `datasource.updates.total`, `datasource.deletions.total`. Plus concurrent users and session tracking in `tracing.ts`.
- **Implication**: Rich business metrics provide strong signals for evaluating agent impact on system behavior. Agent-initiated operations can be tracked via these metrics.
- **Recommendation**: Add agent-specific labels to metrics when machine identity is implemented (AUTH-Q1).
- **Evidence**: `server/src/otel/audit-metrics.ts`, `server/src/otel/tracing.ts`.

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: BLOCKER
- **Finding**: REST API exists via NestJS controllers across 50+ modules but no OpenAPI/Swagger/AsyncAPI specification exists. Integration requires reading source code.
- **Gap**: No machine-discoverable API documentation.
- **Recommendation**: Add `@nestjs/swagger` and annotate controllers to auto-generate OpenAPI spec.
- **Evidence**: `server/src/modules/auth/controller.ts`, `server/src/main.ts`, absence of openapi/swagger files.

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, GraphQL schema, or Smithy model found. `@nestjs/swagger` not installed.
- **Gap**: No machine-readable specification for automated agent tool generation.
- **Recommendation**: Install `@nestjs/swagger` and generate OpenAPI spec.
- **Evidence**: `server/package.json`, absence of spec files.

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: `AllExceptionsFilter` returns JSON with `statusCode`, `timestamp`, `path`, `message`, `code`. Differentiates HttpException, TooljetDatabaseError, QueryFailedError. No `retryable` indicator.
- **Gap**: No retryable flag in error responses.
- **Recommendation**: Add `retryable` boolean to error response format.
- **Evidence**: `server/src/modules/app/filters/all-exceptions-filter.ts`.

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No idempotency key support found. Read-only agents do not execute write operations.
- **Gap**: N/A for read-only scope.
- **Recommendation**: Plan idempotency keys for future write-enabled scope.
- **Evidence**: `server/src/modules/apps/`.

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: JSON responses via NestJS. SCIM supports `application/scim+json`.
- **Gap**: None — JSON is optimal.
- **Recommendation**: No action needed.
- **Evidence**: `server/src/main.ts`.

#### API-Q6: Asynchronous Operation Support
- **Severity**: INFO
- **Finding**: BullMQ queues, Temporal workflows, SSE endpoints, Bull Board dashboard. Async patterns are well-implemented.
- **Gap**: None — async support is comprehensive.
- **Recommendation**: Document async patterns for agent tool definitions.
- **Evidence**: `server/src/modules/workflows/module.ts`, `server/package.json`.

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: EventEmitter2 for audit log events, BullMQ for job events, OTEL metrics for state change tracking.
- **Gap**: Events are internal — no external webhook/subscription API.
- **Recommendation**: Consider exposing webhook API for external agent consumption.
- **Evidence**: `server/src/modules/app/interceptors/response.interceptor.ts`, `server/src/otel/audit-metrics.ts`.

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: ThrottlerModule in workflows module only. No rate limit headers returned. Limits not documented.
- **Gap**: No rate limit headers or documentation.
- **Recommendation**: Add rate limit headers. Document limits for agent operators.
- **Evidence**: `server/src/modules/workflows/module.ts`.

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: JWT-based auth for human users. OAuth2, SAML, OIDC, LDAP, MFA flows. PATs exist but are user-bound. No client credentials flow, no service account mechanism, no mTLS.
- **Gap**: No machine identity authentication. Agents must impersonate human users.
- **Recommendation**: Implement OAuth2 client credentials flow or dedicated agent API key mechanism.
- **Evidence**: `server/src/modules/auth/controller.ts`, `server/src/entities/user_personal_access_tokens.entity.ts`.

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: CASL-based authorization with granular actions. Group permissions provide organizational scoping. No agent-specific roles.
- **Gap**: No agent-specific least-privilege permission profiles.
- **Recommendation**: Create dedicated agent CASL roles with minimal permissions.
- **Evidence**: `server/src/modules/casl/casl-ability.factory.ts`.

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: CASL defines action-level abilities. FeatureAbilityGuard enforces policies. Actions are role-based (admin/builder/viewer), not agent-specific.
- **Gap**: Action-level auth exists but lacks agent-specific action restrictions.
- **Recommendation**: Extend CASL abilities for agent-specific action control.
- **Evidence**: `server/src/modules/casl/casl-ability.factory.ts`, `server/src/modules/casl/check_policies.decorator.ts`.

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: RISK-QUALITY
- **Finding**: JWT carries user context. @User() decorator extracts identity. Multi-workspace propagation. No on-behalf-of flow.
- **Gap**: No delegation or token exchange for agent-on-behalf-of-user scenarios.
- **Recommendation**: Implement token exchange or delegation claims in JWT.
- **Evidence**: `server/src/modules/auth/controller.ts`, `server/src/modules/session/service.ts`.

#### AUTH-Q5: Credential Management
- **Severity**: RISK-QUALITY
- **Finding**: EncryptionService uses AES-256-GCM (Lockbox). Secrets Manager IAM policy exists. But secrets passed as plaintext env vars in ECS task definitions.
- **Gap**: Secrets Manager policy exists but not used for runtime secret injection. Plaintext env vars in IaC.
- **Recommendation**: Reference Secrets Manager in ECS task definitions. Mark Terraform variables as sensitive.
- **Evidence**: `terraform/ECS/main.tf`, `server/src/modules/encryption/service.ts`, `.env.example`.

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Audit log entity with userId, organizationId, resourceType, actionType, ipAddress, metadata. ResponseInterceptor emits events via EventEmitter2. Logs stored in PostgreSQL — mutable, no tamper evidence.
- **Gap**: Audit logs are mutable. No CloudTrail. No immutable storage.
- **Recommendation**: Stream audit logs to S3 with Object Lock. Enable CloudTrail.
- **Evidence**: `server/src/entities/audit_log.entity.ts`, `server/src/modules/app/interceptors/response.interceptor.ts`.

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: User archival and session termination exist. No dedicated agent identity lifecycle. Suspension requires manipulating human user accounts.
- **Gap**: No agent-specific identity suspension mechanism.
- **Recommendation**: Implement dedicated agent identity management with independent suspension.
- **Evidence**: `server/src/entities/user.entity.ts`, `server/src/modules/session/service.ts`.

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Temporal workflows provide compensation for workflow operations. No general rollback for CRUD operations. `dbTransactionWrap` provides atomic transactions.
- **Gap**: Compensation limited to workflow operations only.
- **Recommendation**: Implement compensation patterns for critical write operations.
- **Evidence**: `server/src/modules/workflows/module.ts`, `server/src/modules/session/service.ts`.

#### STATE-Q2: Queryable Current State
- **Severity**: RISK-QUALITY
- **Finding**: GET endpoints exist for apps, users, queries, data sources, organizations. AppVersion tracks status (DRAFT/PUBLISHED/RELEASED). No consolidated state API.
- **Gap**: Individual resource queries available but no unified state query API.
- **Recommendation**: Document state query patterns for agent consumption.
- **Evidence**: `server/src/entities/app_version.entity.ts`, `server/src/modules/apps/`.

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No optimistic locking found. Unique constraints prevent duplicate version names. No ETag or If-Match headers.
- **Gap**: No concurrency controls for write operations.
- **Recommendation**: Plan optimistic locking for write-enabled agent scope.
- **Evidence**: `server/src/entities/app_version.entity.ts`.

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: External HTTP calls via `got`, `express-http-proxy`, `openid-client`, `ldapts`, `nodemailer`. No circuit breaker or retry library found.
- **Gap**: No circuit breakers on external dependency calls.
- **Recommendation**: Add circuit breaker middleware (e.g., `opossum`) for external HTTP calls.
- **Evidence**: `server/package.json` (got, express-http-proxy, openid-client, ldapts, nodemailer).

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: ThrottlerModule configured only in workflows module. No global rate limiting. No API Gateway throttling in IaC.
- **Gap**: No API-wide rate limiting.
- **Recommendation**: Enable ThrottlerModule globally. Add API Gateway throttling.
- **Evidence**: `server/src/modules/workflows/module.ts`, `server/src/main.ts`.

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits. Read-only scope mitigates blast radius risk.
- **Gap**: No transaction limits (informational for read-only scope).
- **Recommendation**: Plan transaction limits for write-enabled scope.
- **Evidence**: No evidence found — absence is the finding.

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path. This service is P2.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled. Current scope is read-only.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled. Current scope is read-only.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: Docker-compose provides local dev environment. Terraform templates for ECS/EC2/Azure/GCP. App-environments module for application-level environments. No production-equivalent staging configuration.
- **Gap**: No production-equivalent staging for agent testing.
- **Recommendation**: Create staging Terraform workspace or Helm values with production-equivalent data shape.
- **Evidence**: `docker-compose.yaml`, `deploy/helm/values.yaml`, `server/src/modules/app-environments/`.

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification ⚡ (Tiered)
- **Severity**: INFO
- **Stage A**: Yes — stores user PII (email, phone, password digest, invitation/forgot-password tokens), encrypted external-service credentials (`credential.entity.ts` — `value_ciphertext`), SSO secrets, PAT hashes, session tokens.
- **B1 — API response scoping**: CLEAR. User paginated queries explicitly omit password from the `select` clause (`server/src/modules/users/repositories/repository.ts:60-75`). The `EncryptionService` applies AES-256-GCM (Lockbox) per-column and returns `{ credential_id, encrypted: true }` references in API responses rather than plaintext; `tokenData` is explicitly filtered (`server/src/modules/data-sources/util.service.ts:106-131`).
- **B2 — Access control differentiation**: CLEAR. All data-source queries chain `.andWhere('data_source.organization_id = :organizationId', ...)` (`server/src/modules/data-sources/repository.ts:67`). Controllers apply `@UseGuards(FeatureAbilityGuard)` and `@UseGuards(PolicyGuard)`; roles distinguish `USER_ROLE.ADMIN` from `END_USER` with CASL abilities (changeRole, archiveUser, inviteUser, etc.).
- **B3 — Formal classification metadata**: Absent → INFO. No `@Sensitive`/`@PII` decorators, no Macie/Presidio, no classification tags in `terraform/ECS/main.tf`. Security is encryption-by-design.
- **Overall**: Highest sub-check firing is B3 (INFO) → DATA-Q1 = INFO. Not a deployment gate.
- **Recommendation (aspirational)**: Add entity-level classification metadata (custom decorators or schema comments) to document which columns are PII, credentials, or public; publish a brief DATA_CLASSIFICATION policy.
- **Evidence**: `server/src/entities/user.entity.ts`, `server/src/entities/credential.entity.ts`, `server/src/modules/encryption/service.ts`, `server/src/modules/data-sources/repository.ts`, `server/src/modules/data-sources/util.service.ts`, `server/src/modules/users/repositories/repository.ts`, `server/src/modules/casl/casl-ability.factory.ts`.

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: All data in single PostgreSQL instance. Terraform defaults to us-east-1. No residency controls, region-based partitioning, or sovereignty enforcement.
- **Gap**: No data residency controls for multi-tenant data.
- **Recommendation**: Implement region-aware data storage. Document residency constraints.
- **Evidence**: `terraform/ECS/variables.tf`, `terraform/ECS/main.tf`.

#### DATA-Q3: Selective Query Support
- **Severity**: RISK-QUALITY
- **Finding**: PostgREST provides native pagination/filtering. Some list endpoints support pagination. Not uniformly enforced.
- **Gap**: Pagination not consistent across all endpoints.
- **Recommendation**: Audit and enforce pagination on all list endpoints.
- **Evidence**: `server/src/modules/tooljet-db/`, `docker-compose.yaml` (PostgREST).

#### DATA-Q4: System of Record Designations
- **Severity**: RISK-QUALITY
- **Finding**: No system-of-record designations. System owns user, org, app, workflow data without formal declaration.
- **Gap**: No formal SoR designations.
- **Recommendation**: Document SoR status for each entity type.
- **Evidence**: `server/src/entities/` (80+ files), absence of data ownership docs.

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK-QUALITY
- **Finding**: `created_at` and `updated_at` on all entities. `publishedAt`, `releasedAt` on AppVersion. No Cache-Control or data freshness headers in API responses.
- **Gap**: Timestamps exist but no freshness signaling in responses.
- **Recommendation**: Add Last-Modified and Cache-Control headers.
- **Evidence**: `server/src/entities/user.entity.ts`, `server/src/entities/app_version.entity.ts`.

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: OTEL tracing logs full request body via `http.body` span attribute. `sanitizeObject` only strips functions, not PII. AllExceptionsFilter logs request headers. No PII masking.
- **Gap**: Full request bodies (including PII) logged in OTEL spans.
- **Recommendation**: Strip PII fields from http.body attribute. Add PII blocklist.
- **Evidence**: `server/src/otel/tracing.ts`, `server/src/modules/app/filters/all-exceptions-filter.ts`.

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics, completeness scores, or freshness SLAs found.
- **Gap**: None (INFO).
- **Recommendation**: Consider adding data quality metrics.
- **Evidence**: No data quality metrics found.

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: URI versioning enabled (`VersioningType.URI`). 184 schema + 174 data migrations. CODEOWNERS review for migrations. No breaking change detection in CI.
- **Gap**: No automated breaking change detection.
- **Recommendation**: Add OpenAPI diff to CI pipeline.
- **Evidence**: `server/src/main.ts`, `server/migrations/`, `CODEOWNERS`, `.github/workflows/ci.yml`.

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Clear, semantic field names: firstName, lastName, email, organizationId. No legacy abbreviations.
- **Gap**: None.
- **Recommendation**: Maintain current conventions.
- **Evidence**: `server/src/entities/user.entity.ts`, `server/src/entities/audit_log.entity.ts`.

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No data catalog. TypeORM entities serve as de facto schema documentation.
- **Gap**: None (INFO).
- **Recommendation**: Consider auto-generating data dictionary from entities.
- **Evidence**: `server/src/entities/` (80+ files).

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive OTEL with BatchSpanProcessor, W3C propagation, Express/HTTP/NestJS/PG/Pino instrumentation. Pino structured logging. TransactionLogger with transactionId correlation. **But OTEL gated to EE/Cloud editions only.** CE has no tracing.
- **Gap**: Tracing restricted to Enterprise/Cloud editions.
- **Recommendation**: Consider making basic OTEL tracing available in CE.
- **Evidence**: `server/src/otel/tracing.ts`, `server/src/modules/logging/service.ts`.

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: OTEL metrics exported. CloudWatch log groups with 30-day retention. Container Insights enabled. No alarms defined. No PagerDuty/OpsGenie.
- **Gap**: No alerting thresholds configured.
- **Recommendation**: Define CloudWatch alarms for error rates and latency.
- **Evidence**: `terraform/ECS/main.tf`, `server/src/otel/tracing.ts`.

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: Excellent: query.executions.total, app.usage.total, app.active_users, app.success_rate, app.errors.total, audit.logs.total, user.sessions.total, app/datasource lifecycle metrics.
- **Gap**: None — comprehensive business metrics.
- **Recommendation**: Add agent-specific labels when machine identity is implemented.
- **Evidence**: `server/src/otel/audit-metrics.ts`, `server/src/otel/tracing.ts`.

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance
- **Severity**: RISK-QUALITY
- **Finding**: Terraform IaC for ECS/EC2/Azure/GCP. Helm charts for K8s. CODEOWNERS for peer review. No drift detection. No automated terraform plan in CI.
- **Gap**: No drift detection or automated IaC plan review in CI.
- **Recommendation**: Add terraform plan to CI. Enable AWS Config drift detection.
- **Evidence**: `terraform/ECS/main.tf`, `deploy/helm/`, `CODEOWNERS`.

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: CI has build, lint, unit tests, e2e tests. Vulnerability scanning weekly. Docker release workflow. No API contract testing (no Pact, no OpenAPI validation).
- **Gap**: No API contract testing in CI.
- **Recommendation**: Add contract tests or OpenAPI validation to CI.
- **Evidence**: `.github/workflows/ci.yml`, `.github/workflows/vulnerability-ci.yml`.

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: ECS rolling update (deployment_maximum_percent=200, deployment_minimum_healthy_percent=100). Helm for K8s rollback. Tagged Docker images. No explicit rollback triggers or canary deployments.
- **Gap**: No explicit rollback triggers.
- **Recommendation**: Add CloudWatch alarm-based rollback triggers to ECS deployment.
- **Evidence**: `terraform/ECS/main.tf`, `deploy/helm/`, `.github/workflows/docker-release.yml`.

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: Unit tests, e2e tests, Cypress tests. test:cov script exists. No API contract tests. Coverage thresholds not enforced in CI.
- **Gap**: No systematic API contract test coverage.
- **Recommendation**: Add API contract tests for agent-facing endpoints. Enforce coverage thresholds.
- **Evidence**: `server/package.json`, `.github/workflows/ci.yml`, `cypress-tests/`.

#### ENG-Q5: Encryption at Rest
- **Severity**: RISK-QUALITY
- **Finding**: RDS `aws_db_instance` does not configure `storage_encrypted`. Redis is a sidecar container (no encryption at rest). Application-level Lockbox encryption protects credential values only.
- **Gap**: RDS and Redis not encrypted at rest at infrastructure level.
- **Recommendation**: Add `storage_encrypted = true` to RDS. Use managed Redis with encryption.
- **Evidence**: `terraform/ECS/main.tf`, `server/src/modules/encryption/service.ts`.

## Evidence Index

### Infrastructure as Code
| File | Questions Referenced |
|------|---------------------|
| `terraform/ECS/main.tf` | AUTH-Q1, AUTH-Q5, AUTH-Q6, STATE-Q5, DATA-Q1, DATA-Q2, OBS-Q2, ENG-Q1, ENG-Q3, ENG-Q5 |
| `terraform/ECS/variables.tf` | AUTH-Q5, DATA-Q2 |
| `deploy/helm/values.yaml` | HITL-Q3, ENG-Q1, ENG-Q3 |
| `deploy/helm/Chart.yaml` | ENG-Q1 |

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `server/src/main.ts` | API-Q1, API-Q5, DISC-Q1, STATE-Q5 |
| `server/src/modules/auth/controller.ts` | API-Q1, AUTH-Q1, AUTH-Q4, API-Q4 |
| `server/src/modules/casl/casl-ability.factory.ts` | AUTH-Q2, AUTH-Q3 |
| `server/src/modules/casl/check_policies.decorator.ts` | AUTH-Q3 |
| `server/src/modules/session/service.ts` | AUTH-Q1, AUTH-Q4, AUTH-Q7, STATE-Q1 |
| `server/src/modules/app/filters/all-exceptions-filter.ts` | API-Q3, DATA-Q6 |
| `server/src/modules/app/interceptors/response.interceptor.ts` | API-Q5, API-Q7, AUTH-Q6 |
| `server/src/modules/encryption/service.ts` | DATA-Q1, AUTH-Q5, ENG-Q5 |
| `server/src/modules/logging/service.ts` | OBS-Q1, DATA-Q6 |
| `server/src/modules/workflows/module.ts` | API-Q6, STATE-Q1, STATE-Q5 |
| `server/src/otel/tracing.ts` | OBS-Q1, OBS-Q2, OBS-Q3, DATA-Q6 |
| `server/src/otel/audit-metrics.ts` | API-Q7, OBS-Q3 |

### Entity Files
| File | Questions Referenced |
|------|---------------------|
| `server/src/entities/user.entity.ts` | AUTH-Q1, AUTH-Q7, DATA-Q1, DATA-Q5, DISC-Q2 |
| `server/src/entities/audit_log.entity.ts` | AUTH-Q6, DISC-Q2 |
| `server/src/entities/credential.entity.ts` | DATA-Q1 |
| `server/src/entities/user_personal_access_tokens.entity.ts` | AUTH-Q1, AUTH-Q7 |
| `server/src/entities/app_version.entity.ts` | STATE-Q2, STATE-Q3, DATA-Q5, HITL-Q1 |
| `server/src/entities/group_permissions.entity.ts` | AUTH-Q2 |
| `server/src/entities/group_users.entity.ts` | AUTH-Q2 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/ci.yml` | ENG-Q2, ENG-Q4, DISC-Q1 |
| `.github/workflows/vulnerability-ci.yml` | ENG-Q2 |
| `.github/workflows/docker-release.yml` | ENG-Q3 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `docker-compose.yaml` | HITL-Q3, DATA-Q3 |
| `docker/ce-production.Dockerfile` | ENG-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `server/package.json` | API-Q2, API-Q6, AUTH-Q1, STATE-Q4, STATE-Q5 |
| `package.json` | (root monorepo configuration) |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `.env.example` | AUTH-Q5, HITL-Q3 |
| `CODEOWNERS` | ENG-Q1, DISC-Q1 |
