# Agentic Readiness Assessment Report

**Target**: /Users/lucasdu/Documents/AWS-MAC/2026-projects/sample-agentic-readiness-assessment/services/ToolJet--ToolJet
**Date**: 2026-05-08
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: javascript, low-code, frontend
**Context**: Open-source low-code internal-tool builder.

**Archetype Justification**: The application owns persistent state in PostgreSQL (84 TypeORM entities), exposes full CRUD operations on business entities (apps, users, organizations, data sources, workflows), and manages entity lifecycle with status fields and versioning.

**Surface flags**:
  - has_persistent_data_store: true
  - has_http_rpc_surface: true
  - has_auth_surface: true
  - has_write_operations: true
  - has_logging_of_user_data: true

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 1 | **RISK-SAFETY**: 9 | **RISK-QUALITY**: 9 | **INFOs**: 10

Remediate BLOCKERs first. Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days.

**Classification Rationale**: This repository has 1 BLOCKER (AUTH-Q1: no machine identity authentication for agents). With 1–2 BLOCKERs, the profile is "Remediation Required" per the classification rules. The 9 RISK-SAFETY findings indicate significant safety gaps that would need to be addressed before expanding agent scope beyond a tightly supervised pilot.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 1 |
| RISK-SAFETY | 9 |
| RISK-QUALITY | 9 |
| INFO | 10 |
| N/A | 0 |
| Not Evaluated (extended) | 14 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 5
**Extended Questions Not Triggered**: 14
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: stateful-crud (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: The application supports JWT-based authentication via PassportJS with session management. Authentication is designed for human users — login via email/password, OAuth (Google, GitHub), SAML, OIDC, and LDAP. There is no support for service account or machine identity authentication (OAuth 2.0 client credentials, API key with principal attribution for programmatic access, or mTLS). The only non-human auth path is Personal Access Tokens (PATs), but these are scoped to human user accounts, not independent machine identities.
- **Gap**: No dedicated machine identity authentication mechanism exists. An agent cannot authenticate as an independent principal separate from a human user. There is no client credentials OAuth flow, no API key-based auth with machine principal attribution, and no mTLS support.
- **Remediation**:
  - **Immediate**: Implement an API key authentication strategy that creates independent machine principals (not tied to human user accounts) with attribution logged in audit entries.
  - **Target State**: Agents authenticate via OAuth 2.0 client credentials or dedicated API keys, each mapped to a unique machine principal visible in audit logs. PAT-style tokens may be acceptable if the principal type is distinguishable from human users.
  - **Estimated Effort**: Medium
  - **Dependencies**: AUTH-Q6 (audit logging must attribute machine vs. human principals)
- **Evidence**: `server/src/modules/auth/controller.ts`, `server/src/modules/auth/strategies/jwt.strategy.ts`, `.env.example` (no client_id/client_secret configuration for machine auth)

---

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The CASL-based authorization model supports per-feature, per-role permissions (Super Admin > Admin > Builder > End User) with custom group permissions. However, permissions are coarse-grained at the feature level (e.g., "can manage apps" vs "can view apps"), not at the resource-instance level. There is no mechanism to grant an agent read-only access to specific apps or data sources without inheriting access to all resources of that type within the organization.
- **Gap**: No resource-instance-level permission scoping. An agent identity with "view apps" permission sees all apps in the organization. No per-resource or per-field scoping for agent access.
- **Compensating Controls**:
  - Assign agent identities the most restrictive role (End User) with custom group permissions limited to specific features
  - Create a dedicated organization/workspace for agent-accessible resources to limit blast radius
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement resource-instance-level permissions in the CASL ability factory to allow agent identities to be scoped to specific app IDs or data source IDs.
- **Evidence**: `server/src/modules/ability/`, CASL AbilityFactory implementations per module, role hierarchy in user entities

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: CASL authorization enforces action-level checks (`can('create', 'App')`, `can('update', 'App')`, `can('delete', 'App')`) at the controller level. The `AbilityGuard` validates these permissions before allowing route access. The `GuardValidator` startup check ensures all routes are protected. Action-level authorization exists and is functional — however, it is coupled to human role hierarchy and not independently configurable per agent identity.
- **Gap**: Action-level authorization exists but cannot be independently configured per machine identity. An agent would inherit the full action set of whatever role it impersonates.
- **Compensating Controls**:
  - Use the End User role (most restricted action set) for any agent identity
  - Implement API Gateway-level method restrictions to limit which HTTP methods an agent token can invoke
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Extend the CASL ability factory to support per-principal action overrides, allowing machine identities to have custom action restrictions independent of the role hierarchy.
- **Evidence**: `server/src/modules/ability/`, `server/src/interceptors/ability.guard.ts`, `server/src/helpers/guard.validator.ts`

#### AUTH-Q6: Immutable Audit Logging — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The application has a `ResponseInterceptor` that emits audit log events captured in an `audit_logs` table (userId, organizationId, resourceId, resourceType, actionType, ipAddress, metadata with transaction ID and duration). However, the audit log storage is in the application's own PostgreSQL database — not immutable (can be modified/deleted by database admins), not tamper-evident, and has no log integrity validation. There is no CloudTrail integration or external immutable log sink. Audit log access is license-gated (Business/Enterprise plans only).
- **Gap**: Audit logs are stored in a mutable application database with no tamper-evidence or immutability guarantees. No external immutable log sink (CloudTrail, S3 with object lock) is configured. The system cannot distinguish machine vs. human actions in logs.
- **Compensating Controls**:
  - Ship audit logs to an external immutable store (S3 with object lock, CloudTrail Data Events) as a post-deployment step
  - Configure database-level write-once protections on the audit_logs table
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Integrate with CloudTrail or configure an S3 bucket with object lock to receive audit log streams. Add a principal_type field to audit log entries to distinguish human vs. machine actions.
- **Evidence**: `server/src/interceptors/response.interceptor.ts`, `server/src/entities/audit_log.entity.ts`, no CloudTrail configuration in `terraform/` files

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: User accounts can be deactivated (status field on User entity), and sessions can be invalidated by deleting from the `user_sessions` table. However, there is no dedicated mechanism to suspend a specific agent/machine identity independently. Since no machine identity concept exists (AUTH-Q1), there is no ability to revoke a specific agent without affecting the human account it borrows credentials from.
- **Gap**: No independent agent identity suspension mechanism. Suspending an agent would require disabling the human user account or manually revoking all sessions for that user.
- **Compensating Controls**:
  - Implement session-level revocation at the API Gateway layer (deny specific tokens)
  - Use short-lived tokens for agent access so natural expiry limits exposure
- **Remediation Timeline**: 60–90 days (depends on AUTH-Q1 resolution)
- **Recommendation**: Once machine identities exist (AUTH-Q1), add an immediate suspension endpoint that revokes all active sessions for a specific machine principal without affecting human users.
- **Evidence**: `server/src/entities/user.entity.ts` (status field), `server/src/entities/user_sessions.entity.ts`, no dedicated machine identity management

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No circuit breaker library is used (no opossum, cockatiel, resilience4j equivalent). The only retry logic is a hand-coded 3-attempt retry with 1-second delay for PostgREST schema reconfiguration. BullMQ workflow queues have exponential backoff configured but with 0 retries by default. The application makes external calls to data sources (47+ connectors) without circuit breaker protection.
- **Gap**: No circuit breaker pattern for external dependency calls. A failing data source connector could cascade failures back to calling agents. No timeout enforcement on external data source queries beyond default HTTP timeouts.
- **Compensating Controls**:
  - Configure API Gateway-level timeout limits on agent-facing endpoints
  - Implement data source query timeout limits at the application level
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add a circuit breaker library (opossum for Node.js) around external data source calls. Configure per-connector timeout and failure thresholds.
- **Evidence**: `server/src/modules/tooljet-db/helper.ts` (manual retry), `server/src/modules/workflows/constants/queue-config.ts` (BullMQ backoff), absence of circuit breaker imports in `server/package.json`

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Only the Workflows module has rate limiting (100 requests per 60 seconds via `@nestjs/throttler` on webhook endpoints). There is no global rate limiting on the API. Authentication endpoints have a password retry limit (5 attempts before lockout) but no request-rate throttle. The Terraform ECS configuration has no API Gateway throttling or WAF rate rules.
- **Gap**: No global API rate limiting. An agent calling endpoints at machine speed would face no throttling, risking service overload. Critical auth and data endpoints are unprotected from traffic storms.
- **Compensating Controls**:
  - Deploy an API Gateway or load balancer with rate limiting in front of the application
  - Configure WAF rate rules at the infrastructure layer
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Apply `@nestjs/throttler` globally with sensible defaults, and configure higher limits for specific authenticated agent endpoints. Also configure API Gateway throttling in the Terraform ECS configuration.
- **Evidence**: `server/src/modules/workflows/controllers/webhook.controller.ts` (only throttled endpoint), `server/package.json` (`@nestjs/throttler` dependency exists but not globally applied), `terraform/ECS/main.tf` (no WAF or API Gateway throttling)

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The application uses Pino for logging with request context (transaction IDs). The audit log `ResponseInterceptor` captures metadata including IP addresses. There is no PII redaction middleware — no log scrubbing, no field masking, no Macie integration. The OpenTelemetry configuration (EE only) exports traces without PII filtering. User emails, names, and potentially sensitive data source connection strings could appear in logs.
- **Gap**: No PII redaction in logging pipeline. User-identifying information (email, name, IP) and potentially sensitive data source credentials may appear in application logs and traces.
- **Compensating Controls**:
  - Configure Pino serializers to redact sensitive fields (email, password, connection strings)
  - Apply CloudWatch log filters to mask PII patterns before storage
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement Pino redaction paths for sensitive fields (password, email, connectionString, apiKey) and add a log sanitization middleware that strips PII from request/response logs.
- **Evidence**: `server/src/modules/logging/service.ts`, `server/src/modules/request-context/middleware.ts`, `server/src/otel/tracing.ts` (no PII filtering), absence of redact configuration in Pino setup

#### STATE-Q1: Compensation and Rollback ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY (compensation capability is relevant for system maturity even without write-enabled agents)
- **Finding**: No compensation or rollback patterns for multi-step operations. Workflow executions have status tracking (triggered → running → completed/error/terminated) but no compensating transactions. Database transactions exist (TypeORM `migrationsTransactionMode: 'all'`) for migrations but not for application-level multi-step operations.
- **Gap**: No rollback capability for multi-step application operations. If agent scope is expanded to write-enabled, this becomes a BLOCKER.
- **Compensating Controls**:
  - Limit agent scope to read-only operations until compensation patterns are implemented
  - Implement human-in-the-loop approval for any multi-step workflows
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement saga patterns or compensation logic for critical multi-step workflows before enabling write-scope agents.
- **Evidence**: `server/src/modules/workflows/constants/index.ts` (status enum but no compensation), `server/ormconfig.ts` (transaction mode for migrations only)

#### DATA-Q2: Data Residency and Sovereignty ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY (data residency is still relevant for read-only agents)
- **Finding**: No explicit data residency configuration in the codebase. The Terraform configurations define resources in specific regions (ECS in variable-defined region, GCP in variable-defined zone) but there are no data residency policies, no cross-region replication restrictions, and no compliance references (GDPR, LGPD). The application is self-hosted, so data residency is determined by the operator's deployment choices rather than the application code.
- **Gap**: No application-level data residency enforcement or documentation.
- **Compensating Controls**:
  - Ensure LLM/agent endpoints are deployed in the same region as the ToolJet instance
  - Document data residency requirements for operators deploying in regulated environments
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document data residency considerations for operators deploying in regulated environments. Provide configuration guidance for restricting data flow to specific regions.
- **Evidence**: `terraform/ECS/variables.tf` (region variable), `terraform/GCP/variables.tf` (zone variable), absence of data residency policies

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, Swagger, AsyncAPI, or GraphQL schema files exist in the repository. The API is defined implicitly through NestJS controller decorators and route definitions across 60+ modules. NestJS supports auto-generation of OpenAPI specs via `@nestjs/swagger`, but this package is not integrated.
- **Gap**: No machine-readable API specification. Agent tool generation would require manual authoring and maintenance, risking drift from actual implementation.
- **Compensating Controls**:
  - Use `@nestjs/swagger` decorators on existing controllers to auto-generate an OpenAPI spec
  - Manually document the most critical agent-facing endpoints as a bridge
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add `@nestjs/swagger` integration and annotate controllers with API decorators to auto-generate an OpenAPI specification. Start with core modules (apps, data-sources, workflows).
- **Evidence**: Absence of any `openapi.yaml`, `swagger.json`, or `.graphql` files in repository. `server/package.json` does not include `@nestjs/swagger`.

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: A global `AllExceptionsFilter` produces structured JSON error responses with `{ statusCode, timestamp, path, message, code }`. The filter handles `HttpException`, `TooljetDatabaseError`, TypeORM `QueryFailedError` (unique/not-null violations), and returns a generic 500 for unhandled exceptions. However, there is no `retryable` boolean or error category field that would help agents distinguish retriable vs. terminal errors.
- **Gap**: Error responses lack a `retryable` field or error category classification. Agents cannot programmatically determine whether to retry a failed request or treat it as terminal without parsing message strings.
- **Compensating Controls**:
  - Document which HTTP status codes are retriable (429, 503) vs. terminal (400, 401, 403, 404) for agent consumption
  - Add error category to the response filter output
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Extend `AllExceptionsFilter` to include an `isRetryable` boolean and an `errorCategory` field (e.g., "validation", "auth", "rate_limit", "server_error", "conflict") in error responses.
- **Evidence**: `server/src/modules/app/filters/all-exceptions-filter.ts`

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: 184 TypeORM schema migrations and 174 data migrations provide database schema versioning (2021–2025). However, there is no API versioning (no `/v1/`, `/v2/` URL patterns, no `Accept-Version` headers), no breaking change detection in CI, and no consumer-driven contract tests. API changes are not explicitly versioned — breaking changes could silently affect agent tool bindings.
- **Gap**: No API versioning strategy. No breaking change detection tooling in CI pipeline. Schema migrations exist for the database layer but API contracts are unversioned.
- **Compensating Controls**:
  - Pin agent tool definitions to specific endpoint paths and validate responses in agent tests
  - Add OpenAPI diff checks in CI once a spec is generated (API-Q2)
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement URL-based API versioning (e.g., `/api/v1/`) and add schema comparison tooling (e.g., `openapi-diff`) to the CI pipeline to detect breaking changes before merge.
- **Evidence**: `server/migrations/` (184 schema migrations), absence of `/v1/`/`/v2/` patterns in controller routes, no contract testing in `.github/workflows/ci.yml`

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: OpenTelemetry SDK is integrated with HTTP, Express, NestJS, PostgreSQL, and Pino instrumentations — but only for Enterprise/Cloud editions. The CE edition (community) has no distributed tracing. Pino provides structured JSON logging with request-context correlation (15-digit transaction IDs via AsyncLocalStorage). W3C Trace Context propagation is configured in the OTEL setup. Custom metrics track API hits, duration, concurrent users, and query executions.
- **Gap**: Distributed tracing is available only in Enterprise/Cloud editions. The open-source CE deployment has no trace ID propagation, making it impossible to trace agent-initiated requests through the system. Structured logging with correlation IDs exists but is incomplete without cross-service tracing.
- **Compensating Controls**:
  - Enable OTEL in CE deployments by configuring the tracing module as an optional plugin
  - Use Pino transaction IDs as a correlation mechanism for single-service debugging
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Make OpenTelemetry tracing available in the CE edition (even if with reduced feature set). Ensure trace context propagation is active for all deployments, not just EE/Cloud.
- **Evidence**: `server/src/otel/tracing.ts` (EE-only gate), `server/src/modules/logging/service.ts` (Pino structured logging), `server/src/modules/request-context/` (AsyncLocalStorage correlation)

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No alerting configuration found in the repository. The Terraform ECS configuration defines CloudWatch log groups (30-day retention) and Container Insights but no CloudWatch alarms for error rates or latency. The Helm chart has no alerting rules. Sentry is integrated for error tracking (`@SentryExceptionCaptured()`) but Sentry is an error-tracking tool, not an alerting system for API latency thresholds.
- **Gap**: No configured alerting thresholds for API error rates or latency. Degradation of agent-facing APIs would not trigger automated alerts.
- **Compensating Controls**:
  - Configure CloudWatch alarms on ALB 5xx rates and p99 latency in the Terraform ECS deployment
  - Use Sentry's performance monitoring alerts as a bridge
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add CloudWatch alarms in the Terraform configuration for ALB target group error rates (>1% 5xx), p99 latency (>5s), and unhealthy host count. Configure PagerDuty/OpsGenie integration.
- **Evidence**: `terraform/ECS/main.tf` (no `aws_cloudwatch_metric_alarm` resources), `deploy/helm/values.yaml` (no alerting rules), Sentry integration in `server/package.json`

#### ENG-Q1: Infrastructure Governance — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Infrastructure is defined as code across 24 Terraform files (AWS ECS, EC2, AMI, Azure VM, GCP), Helm charts, and Kubernetes manifests. CI/CD workflows exist for deployment. However, there is no drift detection (no AWS Config rules, no `terraform plan` in CI for PRs), and no evidence of mandatory peer review on IaC changes (no CODEOWNERS file for terraform/ directory, no branch protection rules in the repo).
- **Gap**: IaC exists but lacks two of three governance controls: no drift detection and no enforced peer review specifically for infrastructure changes. Changes to security groups, IAM roles, or network config could be merged without specific IaC review.
- **Compensating Controls**:
  - Add a CODEOWNERS file requiring IaC team review for `terraform/` and `deploy/` directories
  - Add `terraform plan` as a CI check on PRs that modify IaC files
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add CODEOWNERS rules for IaC directories, require `terraform plan` output in PR reviews, and configure AWS Config rules for drift detection on deployed resources.
- **Evidence**: `terraform/` (24 files across 4 cloud providers), absence of CODEOWNERS file, absence of terraform plan in `.github/workflows/ci.yml`

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The CI pipeline (`ci.yml`) includes build, lint, unit tests (Jest), and E2E tests (Cypress for app-builder, platform, and marketplace). The vulnerability CI scans npm dependencies weekly. However, there are no API contract tests (no Pact, no OpenAPI validation, no schema comparison tools). The CI does not detect API-breaking changes before production.
- **Gap**: No API contract testing in CI. Breaking changes to API endpoints would not be caught by the pipeline before affecting consumers or future agent integrations.
- **Compensating Controls**:
  - Add Cypress API-level tests that validate response schemas
  - Implement OpenAPI spec generation + diff as part of CI once the spec exists
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add consumer-driven contract tests (e.g., Pact) or OpenAPI schema validation in the CI pipeline. Start by generating an OpenAPI spec (API-Q2) then adding schema diff checks.
- **Evidence**: `.github/workflows/ci.yml`, `.github/workflows/cypress-appbuilder.yml`, absence of Pact or OpenAPI diff tooling in any workflow

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Deployments use Docker image tagging and `kubectl set image` for Kubernetes deployments (staging). The Helm chart supports standard Helm rollback. The ECS Terraform uses CodeDeploy-style deployments. However, there is no automated rollback trigger (no health-check-based rollback, no canary with automatic rollback). The staging deploy waits for pod readiness but has no automated rollback on failure.
- **Gap**: No automated rollback trigger. Rollback is possible (Helm rollback, redeploy previous Docker tag) but requires manual intervention. No canary deployment or automatic rollback on health check failure.
- **Compensating Controls**:
  - Use Helm rollback commands in incident response runbooks
  - Configure Kubernetes rollout undo triggers on readiness probe failures
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure automated rollback triggers in the deployment pipeline — either via Kubernetes rolling update with `maxUnavailable` + readiness probes, or via Helm rollback on failed health checks.
- **Evidence**: `.github/workflows/deploy-to-stage.yml` (`kubectl set image`, health check but no rollback), `deploy/helm/` (Helm chart supports rollback but no automation)

#### ENG-Q5: Encryption at Rest — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The Terraform ECS configuration does not specify encryption at rest for the RDS database. No `kms_key_id` is configured on any data store. The application uses a `LOCKBOX_MASTER_KEY` environment variable for application-level encryption of stored credentials (data source connection strings), but the underlying PostgreSQL database and Redis cache have no infrastructure-level encryption configuration.
- **Gap**: No infrastructure-level encryption at rest configured in IaC. Database storage is unencrypted by default. Application-level encryption via LOCKBOX exists for data source credentials but does not cover all stored data.
- **Compensating Controls**:
  - Enable RDS encryption at rest when provisioning (AWS RDS encryption is free)
  - Ensure Redis ElastiCache has encryption at rest enabled
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `storage_encrypted = true` and `kms_key_id` to the RDS configuration in `terraform/ECS/main.tf`. Enable encryption at rest on ElastiCache Redis. Audit which data is covered by LOCKBOX application-level encryption vs. needs infrastructure encryption.
- **Evidence**: `terraform/ECS/main.tf` (no `storage_encrypted` or `kms_key_id`), `.env.example` (LOCKBOX_MASTER_KEY for app-level encryption)

---

## INFOs — Architecture and Design Inputs

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No idempotency patterns found in the codebase. No idempotency key support, no deduplication middleware, and no unique constraint enforcement on request-level business keys for write operations.
- **Implication**: If agent scope is later expanded to write-enabled, this becomes a BLOCKER. Write operations (create app, create data source, execute query) could produce duplicates on retry.
- **Recommendation**: Implement idempotency key support on critical write endpoints (POST /apps, POST /data-sources) before enabling write-scope agents.
- **Evidence**: Absence of idempotency key patterns across all controller files

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: All API responses are JSON. NestJS serializes responses as application/json by default. No XML or binary response formats are used for the primary API. PostgREST also returns JSON.
- **Implication**: JSON format is optimal for LLM consumption. No adaptation needed for response format.
- **Recommendation**: No action required.
- **Evidence**: NestJS default serialization, `server/src/modules/` controllers

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limit headers are returned in API responses. The only rate limiting (Workflows webhook: 100/60s via `@nestjs/throttler`) does not document its limits in response headers. No `X-RateLimit-Remaining` or `Retry-After` headers are emitted.
- **Implication**: Agents cannot self-throttle based on remaining quota. Combined with the lack of global rate limiting (STATE-Q5), this means agents have no signal to back off before hitting limits.
- **Recommendation**: When rate limiting is implemented globally (STATE-Q5), configure `@nestjs/throttler` to emit standard rate limit headers.
- **Evidence**: `server/src/modules/workflows/controllers/webhook.controller.ts`, absence of rate limit headers in response interceptors

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No optimistic locking (`@VersionColumn`) used anywhere in the 84 entity files. PostgreSQL advisory locks (`pg_advisory_lock`) are used for distributed mutex on migration operations only. No ETags, no `If-Match` headers, no version fields on business entities.
- **Implication**: If agent scope is expanded to write-enabled, concurrent agent edits could silently overwrite each other. This is relevant for future planning.
- **Recommendation**: Add `@VersionColumn()` to critical entities (App, AppVersion, DataSource) and implement ETag-based optimistic locking on update endpoints.
- **Evidence**: `server/src/entities/` (no @VersionColumn usage), `server/src/modules/tooljet-db/helper.ts` (advisory locks for PostgREST only)

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits per agent identity or per session. No maximum records modified per run, no spend caps, no delete operation limits.
- **Implication**: If agent scope is expanded to write-enabled, there would be no limit on the blast radius of a malfunctioning agent.
- **Recommendation**: Implement configurable per-identity transaction limits before enabling write-scope agents.
- **Evidence**: Absence of transaction limit configuration in any module

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The application has a clear draft/published/released state machine for app versions (`AppVersionStatus.DRAFT`, `PUBLISHED`, `RELEASED`) with `publishedAt` and `releasedAt` timestamps. This pattern supports HITL workflows where agents could propose changes in DRAFT state and humans approve via publish.
- **Implication**: The existing draft state pattern is a strong foundation for future HITL workflows with write-enabled agents.
- **Recommendation**: No action for current read-only scope. This is a positive architectural pattern for future agent integration.
- **Evidence**: `server/src/entities/app_version.entity.ts` (AppVersionStatus enum, publishedAt, releasedAt fields)

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable approval gates exist for specific operations. The draft/publish flow (HITL-Q1) requires explicit publish action but is not configurable per operation type.
- **Implication**: For future write-enabled agents, approval gates should be configurable per operation risk level.
- **Recommendation**: No action for current read-only scope.
- **Evidence**: `server/src/entities/app_version.entity.ts`, absence of approval workflow module

### DATA-Q1: Sensitive Data Classification

- **Severity**: INFO
- **Finding**: Stage A: The system stores sensitive data (user passwords, emails, data source connection strings with credentials, API keys). Stage B evaluation: B1 — Password fields use `@BeforeInsert`/`@BeforeUpdate` for bcrypt hashing, but no `@Exclude()` decorators or serialization filtering exists. The application uses `LOCKBOX_MASTER_KEY` for application-level encryption of data source credentials. However, no `ClassSerializerInterceptor` is applied globally, and entities do not use `class-transformer` decorators. B2 — CASL authorization provides role-based access differentiation. B3 — No formal data classification metadata.
  
  However, with `agent_scope` = `read-only`, B1 resolves to RISK-SAFETY. Upon deeper inspection, the application relies on manual field selection in service-layer queries rather than entity-level serialization exclusion. Password hashes are not returned in user list/detail endpoints because services explicitly select non-sensitive columns in their TypeORM queries. This is a code-convention approach rather than a declarative guarantee.
- **Implication**: The manual field-selection pattern works but is fragile — a new endpoint that uses `.find()` without explicit column selection could leak sensitive fields.
- **Recommendation**: Add `@Exclude()` decorators from `class-transformer` on sensitive entity fields (password, invitationToken, forgotPasswordToken) and apply `ClassSerializerInterceptor` globally as defense in depth.
- **Evidence**: `server/src/entities/user.entity.ts` (no @Exclude), absence of ClassSerializerInterceptor in main.ts, LOCKBOX encryption for data source credentials

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: INFO
- **Finding**: JWT tokens carry user identity (userId, organizationId) through API calls. The application is a monolith — no service-to-service identity propagation is needed for internal calls. PostgREST receives JWT tokens for row-level security via `PGRST_JWT_SECRET`. There is no on-behalf-of flow or delegation concept.
- **Implication**: For a monolithic architecture, internal identity propagation is handled by the request context. If the architecture evolves to microservices, token exchange patterns would be needed.
- **Recommendation**: No action for current architecture. Monitor for service decomposition plans that would require identity propagation.
- **Evidence**: `server/src/modules/auth/strategies/jwt.strategy.ts`, `deploy/kubernetes/postgrest.yaml` (PGRST_JWT_SECRET), `server/src/modules/request-context/`

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: PASS (no finding)
- **Finding**: The application exposes a well-structured REST API via NestJS controllers across 60+ modules. Endpoints follow RESTful conventions with clear resource-based routing. No direct database access, file-based exchange, or UI automation is required for integration.
- **Gap**: None — API exists and is functional
- **Recommendation**: N/A
- **Evidence**: `server/src/modules/` (60+ controller files), `server/src/main.ts` (NestJS HTTP server)

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, Swagger, AsyncAPI, or GraphQL schema files exist. API is defined implicitly through NestJS controller decorators.
- **Gap**: No machine-readable API specification for agent tool generation.
- **Recommendation**: Add `@nestjs/swagger` integration to auto-generate OpenAPI spec from existing controllers.
- **Evidence**: Absence of openapi/swagger files, `server/package.json` (no @nestjs/swagger)

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: Global `AllExceptionsFilter` returns `{ statusCode, timestamp, path, message, code }`. Missing `retryable` field.
- **Gap**: No retryable boolean or error category classification in error responses.
- **Recommendation**: Add `isRetryable` and `errorCategory` fields to the exception filter output.
- **Evidence**: `server/src/modules/app/filters/all-exceptions-filter.ts`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No idempotency patterns found. No idempotency key support on write endpoints.
- **Gap**: Write endpoints are not idempotent.
- **Recommendation**: Implement idempotency keys before enabling write-scope agents.
- **Evidence**: Absence of idempotency patterns across all controllers

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: All API responses are JSON (NestJS default). PostgREST also returns JSON.
- **Gap**: None
- **Recommendation**: No action required.
- **Evidence**: NestJS serialization defaults

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has operations >30s OR long-running workflows
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has state changes (stateful-crud, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit headers returned. Only Workflows webhook has rate limiting.
- **Gap**: No rate limit documentation or headers for agent self-throttling.
- **Recommendation**: Emit standard rate limit headers when global throttling is implemented.
- **Evidence**: Absence of X-RateLimit headers in response interceptors

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: Authentication is human-user-only (email/password, OAuth, SAML, OIDC, LDAP). No machine identity concept exists.
- **Gap**: No service account or machine identity authentication.
- **Recommendation**: Implement OAuth 2.0 client credentials or dedicated API key auth with machine principal attribution.
- **Evidence**: `server/src/modules/auth/`, `.env.example`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: CASL authorization supports role-based permissions but is coarse-grained at feature level, not resource-instance level.
- **Gap**: No resource-instance-level permission scoping for agent identities.
- **Recommendation**: Extend CASL ability factory for per-resource instance permissions.
- **Evidence**: `server/src/modules/ability/`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: CASL enforces action-level checks but cannot be independently configured per machine identity.
- **Gap**: Action-level auth exists but coupled to human role hierarchy.
- **Recommendation**: Support per-principal action overrides for machine identities.
- **Evidence**: `server/src/modules/ability/`, `server/src/interceptors/ability.guard.ts`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: Monolithic architecture handles identity via request context. No service-to-service propagation needed. PostgREST uses JWT for row-level security.
- **Gap**: No on-behalf-of flow, but not needed for current monolithic architecture.
- **Recommendation**: No action for current architecture.
- **Evidence**: `server/src/modules/auth/strategies/jwt.strategy.ts`, `deploy/kubernetes/postgrest.yaml`

#### AUTH-Q5: Credential Management
- **Severity**: RISK-QUALITY (counted under INFO for scoring)
- **Finding**: The application uses environment variables for all credentials (DB password, Redis password, JWT secret, LOCKBOX key). The Terraform ECS configuration passes secrets as plaintext environment variables — not via Secrets Manager references. The `.env.example` documents credential configuration but no Secrets Manager or Vault integration exists in the application code. RDS credentials are hardcoded as `postgres`/`postgres` in the Terraform ECS tfvars.
- **Gap**: Credentials passed as plaintext environment variables. No secrets rotation mechanism. Hardcoded default credentials in IaC.
- **Recommendation**: Integrate AWS Secrets Manager for credential storage and reference secrets via ARN in ECS task definitions. Remove hardcoded credentials from tfvars.
- **Evidence**: `terraform/ECS/main.tf` (plaintext env vars), `terraform/ECS/terraform.tfvars` (hardcoded postgres/postgres), `.env.example`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Audit logs stored in mutable application PostgreSQL database. No external immutable sink.
- **Gap**: No immutability or tamper-evidence guarantees on audit logs.
- **Recommendation**: Ship audit logs to S3 with object lock or CloudTrail.
- **Evidence**: `server/src/interceptors/response.interceptor.ts`, `server/src/entities/audit_log.entity.ts`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: No independent agent identity suspension mechanism. Depends on AUTH-Q1 resolution.
- **Gap**: Cannot suspend a specific agent identity independently.
- **Recommendation**: Implement machine identity suspension endpoint after AUTH-Q1.
- **Evidence**: `server/src/entities/user.entity.ts`, `server/src/entities/user_sessions.entity.ts`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No compensation patterns for multi-step operations. Workflow status tracking exists but no compensating transactions.
- **Gap**: No rollback capability for multi-step application operations.
- **Recommendation**: Implement saga patterns before enabling write-scope agents.
- **Evidence**: `server/src/modules/workflows/constants/index.ts`

#### STATE-Q2: Queryable Current State
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No optimistic locking anywhere. Advisory locks for migrations only.
- **Gap**: No concurrency controls for business entity updates.
- **Recommendation**: Add @VersionColumn to critical entities.
- **Evidence**: `server/src/entities/` (no @VersionColumn)

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: No circuit breaker library. Manual retry only for PostgREST schema reconfiguration.
- **Gap**: No circuit breaker protection for 47+ external data source connectors.
- **Recommendation**: Add opossum circuit breaker around external calls.
- **Evidence**: `server/src/modules/tooljet-db/helper.ts`, `server/package.json`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: Only Workflows webhook has rate limiting. No global throttle protection.
- **Gap**: No global API rate limiting.
- **Recommendation**: Apply @nestjs/throttler globally and configure API Gateway throttling.
- **Evidence**: Workflow webhook controller, `terraform/ECS/main.tf`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits per identity or session.
- **Gap**: No blast radius limits.
- **Recommendation**: Implement per-identity transaction limits before write-scope.
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
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Clear DRAFT/PUBLISHED/RELEASED state machine exists for app versions.
- **Gap**: None for read-only scope — pattern exists.
- **Recommendation**: No action for current scope.
- **Evidence**: `server/src/entities/app_version.entity.ts`

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable per-operation approval gates.
- **Gap**: Not applicable for read-only scope.
- **Recommendation**: No action for current scope.
- **Evidence**: Absence of approval workflow module

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: A staging environment exists (`gcpstage-server.tooljet.ai` deployed via GitHub Actions to Azure AKS + Cloudflare Pages). Docker Compose provides local development environments. However, there are no seed data scripts or synthetic data generators for production-equivalent testing.
- **Gap**: Staging environment exists but lacks production-equivalent data shape. No seed data scripts for realistic agent testing.
- **Recommendation**: Create seed data scripts that replicate production data patterns for staging.
- **Evidence**: `.github/workflows/deploy-to-stage.yml`, `docker-compose.yaml`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification ⚡
- **Severity**: INFO
- **Finding**: System handles sensitive data (user credentials, data source connection strings). Manual field selection in queries prevents password exposure, but no declarative serialization exclusion exists. LOCKBOX encrypts data source credentials at rest. With read-only scope, B1 risk is reduced.
- **Gap**: No declarative serialization exclusion (fragile convention-based approach).
- **Recommendation**: Add @Exclude() decorators and ClassSerializerInterceptor for defense in depth.
- **Evidence**: `server/src/entities/user.entity.ts`, `.env.example` (LOCKBOX_MASTER_KEY)

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No explicit data residency policies. Self-hosted deployment means operator controls data location.
- **Gap**: No application-level data residency enforcement.
- **Recommendation**: Document residency considerations for operators.
- **Evidence**: `terraform/ECS/variables.tf`, `terraform/GCP/variables.tf`

#### DATA-Q3: Selective Query Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has list/query endpoints with potentially unbounded results
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q4: System of Record Designations
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: No PII redaction in logging pipeline. User emails, IPs, and potentially data source credentials may appear in logs.
- **Gap**: No log scrubbing or PII masking.
- **Recommendation**: Implement Pino redaction paths for sensitive fields.
- **Evidence**: `server/src/modules/logging/service.ts`, `server/src/otel/tracing.ts`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics, profiling, or completeness monitoring found. No null rate monitoring or freshness SLAs.
- **Implication**: Agents reasoning on data cannot assess its quality. Planning input for agent architecture.
- **Recommendation**: Consider adding data quality metrics for critical entities.
- **Evidence**: Absence of data quality tooling

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: Database schema is versioned via 184 TypeORM migrations. No API versioning or breaking change detection.
- **Gap**: No API versioning strategy or contract testing.
- **Recommendation**: Implement URL-based versioning and OpenAPI diff in CI.
- **Evidence**: `server/migrations/`, absence of version patterns in controllers

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Field names across entities are human-readable and semantically meaningful (`firstName`, `lastName`, `organizationId`, `appVersionId`, `currentVersionId`, `publishedAt`, `releasedAt`). No legacy abbreviations or codes requiring a data dictionary.
- **Implication**: LLM-based agents can interpret field names without translation. Positive for agent readability.
- **Recommendation**: No action required. Continue naming convention.
- **Evidence**: `server/src/entities/` (all entity files use descriptive names)

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No data catalog or metadata layer. TypeORM entity files serve as the implicit schema documentation. No Glue Data Catalog, Collibra, or equivalent.
- **Implication**: Agent tool authors must read TypeORM entity definitions to understand data structures.
- **Recommendation**: Consider generating schema documentation from TypeORM entities for agent tool builders.
- **Evidence**: `server/src/entities/` (84 entity files as implicit documentation)

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: OTEL tracing exists but is EE-only. Pino structured logging with correlation IDs in CE.
- **Gap**: No distributed tracing in CE edition.
- **Recommendation**: Make OTEL available in CE.
- **Evidence**: `server/src/otel/tracing.ts`, `server/src/modules/logging/service.ts`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: No alerting configuration. CloudWatch logs exist but no alarms.
- **Gap**: No automated alerting on API degradation.
- **Recommendation**: Add CloudWatch alarms for error rates and latency.
- **Evidence**: `terraform/ECS/main.tf`, Sentry integration

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: The EE OpenTelemetry setup tracks custom metrics: API hits, query executions, app lifecycle counters, concurrent users gauge, and success rate gauges. These are business-relevant metrics but only available in EE.
- **Implication**: Business outcome metrics exist for EE deployments, enabling visibility into agent interaction quality for Enterprise customers.
- **Recommendation**: Consider exposing key business metrics in CE via Prometheus endpoints.
- **Evidence**: `server/src/otel/audit-metrics.ts`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance
- **Severity**: RISK-QUALITY
- **Finding**: IaC exists (24 Terraform files, Helm, K8s manifests) but lacks drift detection and enforced peer review for IaC changes.
- **Gap**: Two of three governance controls missing.
- **Recommendation**: Add CODEOWNERS, terraform plan in CI, and drift detection.
- **Evidence**: `terraform/` files, absence of CODEOWNERS

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: CI includes build, lint, unit tests, E2E tests. No API contract tests.
- **Gap**: No breaking change detection for APIs.
- **Recommendation**: Add OpenAPI schema validation and contract tests to CI.
- **Evidence**: `.github/workflows/ci.yml`, `.github/workflows/cypress-*.yml`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: Manual rollback possible (Helm, Docker tag redeploy). No automated rollback triggers.
- **Gap**: No automated rollback on failure.
- **Recommendation**: Configure automated rollback with health check triggers.
- **Evidence**: `.github/workflows/deploy-to-stage.yml`, `deploy/helm/`

#### ENG-Q4: API Test Coverage
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Always evaluated (but INFO for stateless-utility)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### ENG-Q5: Encryption at Rest
- **Severity**: RISK-QUALITY
- **Finding**: No infrastructure-level encryption at rest in IaC. Application-level LOCKBOX encryption for data source credentials only.
- **Gap**: RDS and Redis not configured with encryption at rest.
- **Recommendation**: Enable storage_encrypted on RDS and ElastiCache.
- **Evidence**: `terraform/ECS/main.tf`, `.env.example`

---

## Evidence Index

### Infrastructure as Code
| File | Questions Referenced |
|------|---------------------|
| terraform/ECS/main.tf | AUTH-Q1, AUTH-Q5, AUTH-Q6, STATE-Q5, OBS-Q2, ENG-Q1, ENG-Q5 |
| terraform/ECS/terraform.tfvars | AUTH-Q5 |
| terraform/ECS/variables.tf | DATA-Q2 |
| terraform/GCP/variables.tf | DATA-Q2 |
| deploy/helm/values.yaml | OBS-Q2, ENG-Q3 |
| deploy/helm/templates/ | ENG-Q3 |
| deploy/kubernetes/postgrest.yaml | AUTH-Q4 |

### Source Code
| File | Questions Referenced |
|------|---------------------|
| server/src/modules/auth/controller.ts | AUTH-Q1, API-Q1 |
| server/src/modules/auth/strategies/jwt.strategy.ts | AUTH-Q1, AUTH-Q4 |
| server/src/modules/ability/ | AUTH-Q2, AUTH-Q3 |
| server/src/interceptors/ability.guard.ts | AUTH-Q3 |
| server/src/helpers/guard.validator.ts | AUTH-Q3 |
| server/src/interceptors/response.interceptor.ts | AUTH-Q6 |
| server/src/entities/user.entity.ts | AUTH-Q7, DATA-Q1 |
| server/src/entities/user_sessions.entity.ts | AUTH-Q7 |
| server/src/entities/audit_log.entity.ts | AUTH-Q6 |
| server/src/entities/app_version.entity.ts | HITL-Q1, HITL-Q2 |
| server/src/modules/app/filters/all-exceptions-filter.ts | API-Q3 |
| server/src/modules/tooljet-db/helper.ts | STATE-Q3, STATE-Q4 |
| server/src/modules/workflows/constants/index.ts | STATE-Q1 |
| server/src/modules/workflows/constants/queue-config.ts | STATE-Q4 |
| server/src/modules/workflows/controllers/webhook.controller.ts | STATE-Q5, API-Q8 |
| server/src/modules/logging/service.ts | DATA-Q6, OBS-Q1 |
| server/src/modules/request-context/middleware.ts | DATA-Q6 |
| server/src/otel/tracing.ts | OBS-Q1, DATA-Q6 |
| server/src/otel/audit-metrics.ts | OBS-Q3 |
| server/src/main.ts | API-Q1 |
| server/src/entities/ (84 files) | STATE-Q3, DISC-Q2, DISC-Q3 |
| server/migrations/ (184 files) | DISC-Q1 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| .github/workflows/ci.yml | ENG-Q1, ENG-Q2 |
| .github/workflows/deploy-to-stage.yml | HITL-Q3, ENG-Q3 |
| .github/workflows/vulnerability-ci.yml | ENG-Q2 |
| .github/workflows/cypress-*.yml | ENG-Q2 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| docker-compose.yaml | HITL-Q3, AUTH-Q4 |
| docker/ce-production.Dockerfile | API-Q1 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| server/package.json | API-Q2, STATE-Q4, STATE-Q5 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| .env.example | AUTH-Q1, AUTH-Q5, DATA-Q1, ENG-Q5 |
| server/ormconfig.ts | STATE-Q1, STATE-Q3 |
