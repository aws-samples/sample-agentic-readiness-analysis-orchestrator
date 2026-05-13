# Agentic Readiness Assessment Report

**Target**: ToolJet (monorepo)
**Date**: 2025-07-11
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: monorepo
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: javascript, low-code, frontend
**Context**: Open-source low-code internal-tool builder.

**Archetype Justification**: Server owns persistent state in PostgreSQL with 70+ TypeORM entities, exposes full CRUD operations for apps, users, organizations, data sources, and workflows with entity lifecycle management.

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 1 | **RISK-SAFETY**: 9 | **RISK-QUALITY**: 17 | **INFOs**: 15

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 1 |
| RISK-SAFETY | 9 |
| RISK-QUALITY | 17 |
| INFO | 15 |
| N/A | 0 |
| Not Evaluated (extended) | 1 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 18
**Extended Questions Not Triggered**: 1
**Questions N/A (repo_type: monorepo)**: 0
**Service Archetype**: stateful-crud (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### DATA-Q1: Sensitive Data Classification — BLOCKER

- **Severity**: BLOCKER
- **Finding**: The ToolJet server stores extensive PII in PostgreSQL: `user.entity.ts` contains `firstName`, `lastName`, `email`, `phoneNumber`, `password` (hashed via bcrypt), `invitationToken`, `forgotPasswordToken`. The `data_source_options.entity.ts` stores encrypted credentials (database passwords, API keys) via the application-level encryption service (`server/src/modules/encryption/service.ts` using AES-256-GCM with `LOCKBOX_MASTER_KEY`). However, there is **no field-level data classification** — no tags on entities indicating PII sensitivity, no Macie integration, no data classification policies in IaC, and no field-level access controls preventing an agent from retrieving sensitive fields without explicit authorization.
- **Gap**: No formal data classification system exists. Sensitive fields (PII, credentials) are not tagged or classified at the field level. No mechanism exists to prevent an agent with read access from retrieving PII fields.
- **Remediation**:
  - **Immediate**: Create a data classification inventory mapping all PII fields across entities (user, organization, data_source_options). Implement field-level response filtering for agent-facing endpoints.
  - **Target State**: All PII fields tagged with sensitivity classification (e.g., `@Sensitive('PII')` decorators). Agent-facing API responses exclude or mask PII unless explicitly authorized.
  - **Estimated Effort**: Medium (30–60 days)
  - **Dependencies**: AUTH-Q2 (scoped permissions must support field-level exclusion)
- **Evidence**: `server/src/entities/user.entity.ts`, `server/src/entities/data_source_options.entity.ts`, `server/src/modules/encryption/service.ts`

---

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The server implements CASL-based ABAC with fine-grained actions (`changeRole`, `archiveUser`, `inviteUser`, `accessGroupPermission`, etc.) via `server/src/modules/casl/casl-ability.factory.ts`. Group permissions (`granular_permissions.entity.ts`, `group_permissions.entity.ts`) support per-group resource access. However, the Terraform IAM policy for Secrets Manager uses a scoped resource ARN (`arn:aws:secretsmanager:${var.region}:${account_id}:secret:tooljet-secret`), but the SSM policy uses `Resource: "*"` (wildcard). No agent-specific IAM roles or permission scopes exist.
- **Gap**: No agent-specific permission scope exists. Application-level CASL permissions are user-oriented, not machine-identity-oriented. IAM SSM policy uses wildcard resource.
- **Compensating Controls**:
  - Create a dedicated "agent" group with read-only CASL permissions scoped to specific resources
  - Use API Gateway or proxy layer to restrict agent access to a subset of endpoints
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Define an agent-specific CASL role with least-privilege permissions (read-only access to app metadata, no access to user PII or credential data).
- **Evidence**: `server/src/modules/casl/casl-ability.factory.ts`, `server/src/entities/granular_permissions.entity.ts`, `terraform/ECS/main.tf`

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The server uses NestJS `@UseGuards(FeatureAbilityGuard)` extensively across controllers. Multiple modules have dedicated `ability/` directories with fine-grained guards (auth, external-apis, workflows, audit-logs). The CASL ability factory defines granular actions including `changeRole`, `archiveUser`, `inviteUser`, `accessGroupPermission`, `updateOrganizations`, `viewAllUsers`. This provides strong action-level authorization at the application layer.
- **Gap**: Action-level auth exists but is designed for human users. No agent-specific action restrictions (e.g., an agent can read but not invoke data queries) are defined. No separate guard validates agent-vs-user action permissions.
- **Compensating Controls**:
  - Restrict agent PATs to specific scopes using the `PersonalAccessTokenScope` enum
  - Implement an agent-specific middleware that filters allowed actions
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Extend the existing CASL framework to define agent-specific ability sets with explicit action allowlists.
- **Evidence**: `server/src/modules/auth/ability/`, `server/src/modules/casl/check_policies.decorator.ts`, `server/src/modules/external-apis/ability/guard.ts`

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The server has a comprehensive audit logging system: `audit_log.entity.ts` records `userId`, `organizationId`, `resourceId`, `resourceType`, `actionType`, `ipAddress`, and `metadata` with `@CreateDateColumn`. The `ResponseInterceptor` emits `auditLogEntry` events via EventEmitter2. OTEL integration in `audit-metrics.ts` publishes audit metrics to an OTEL collector. CloudWatch log groups are defined in Terraform with 30-day retention. **However**: No `aws_cloudtrail` resource exists in Terraform. No immutable log storage (S3 with object lock) is configured. Audit logs are stored in PostgreSQL which is mutable.
- **Gap**: Audit logs exist but are not immutable or tamper-evident. Logs stored in PostgreSQL can be modified or deleted. No CloudTrail or immutable S3 storage configured.
- **Compensating Controls**:
  - Export audit logs to a separate, append-only data store (e.g., S3 with object lock)
  - Enable CloudTrail for the AWS account and ensure log file validation is enabled
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `aws_cloudtrail` resource to Terraform and configure S3 bucket with object lock for immutable audit log storage. Pipe application audit logs from PostgreSQL to immutable storage.
- **Evidence**: `server/src/entities/audit_log.entity.ts`, `server/src/modules/app/interceptors/response.interceptor.ts`, `server/src/otel/audit-metrics.ts`, `terraform/ECS/main.tf`

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: User accounts can be set to `status: 'archived'` (user.entity.ts enum: invited, verified, active, archived). The external APIs controller has `updateUser` endpoint. Personal Access Tokens (`user_personal_access_tokens.entity.ts`) have `expiresAt` timestamps and `scope` enums. User sessions (`user_sessions.entity.ts`) can be invalidated. **However**, there is no documented instant-revocation mechanism for agent identities specifically, and PAT revocation requires database-level deletion.
- **Gap**: No dedicated agent identity suspension API. PAT revocation is not instant — requires database update. No automated anomaly-based suspension.
- **Compensating Controls**:
  - Use short-lived PAT session expiry (`sessionExpiryMinutes` field exists, default 60)
  - Implement a PAT revocation endpoint that invalidates active sessions immediately
- **Remediation Timeline**: 30 days
- **Recommendation**: Create a dedicated PAT revocation endpoint and ensure session invalidation is immediate upon PAT deletion.
- **Evidence**: `server/src/entities/user.entity.ts`, `server/src/entities/user_personal_access_tokens.entity.ts`, `server/src/entities/user_sessions.entity.ts`

#### STATE-Q1: Compensation and Rollback ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The server uses Temporal workflows (`@temporalio/*` dependencies) which inherently support compensation and error handling. Database transaction support exists via TypeORM. **However**, no explicit saga pattern, compensation endpoints, or undo operations are documented in the codebase. The workflow execution entity tracks status but no compensation logic is visible.
- **Gap**: No explicit compensation or rollback endpoints for multi-step operations. Temporal provides infrastructure but no compensation logic is implemented in application code.
- **Compensating Controls**:
  - Temporal workflows can be extended with compensation activities
  - Database transactions provide atomicity for single-service operations
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement compensation activities in Temporal workflows for critical multi-step operations (app creation, data source provisioning).
- **Evidence**: `server/package.json` (@temporalio/* dependencies), `server/src/modules/workflows/`, `server/src/entities/workflow_execution.entity.ts`

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The server calls external dependencies: PostgREST (via HTTP), Temporal (via gRPC client), Redis (via ioredis), and PostgreSQL (via TypeORM). The `got` HTTP client library is used for external calls. **No circuit breaker library** (Resilience4j, opossum, cockatiel) is present in `server/package.json`. No retry decorators, exponential backoff, or timeout configurations were found in the source code beyond default library settings.
- **Gap**: No circuit breakers, retry policies, or explicit timeout configurations on external dependency calls. A cascading failure in PostgREST or Temporal could propagate back to agents.
- **Compensating Controls**:
  - Add got request timeouts for PostgREST calls
  - Implement connection pool limits for PostgreSQL and Redis
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `opossum` or `cockatiel` circuit breaker library. Configure explicit timeouts on all HTTP clients and database connections.
- **Evidence**: `server/package.json`, `docker-compose.yaml` (PostgREST, Redis services)

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: `@nestjs/throttler` (v6.2.1) is configured via `ThrottlerModule.forRootAsync()` in the app module. **However**, the throttle configuration uses `WEBHOOK_THROTTLE_TTL` environment variable, suggesting it may only be applied to webhook endpoints. No `@Throttle()` decorators were found on individual controllers. No API Gateway throttling exists in Terraform (the ECS deployment uses ALB directly, which has no built-in rate limiting). No WAF rate rules are configured.
- **Gap**: ThrottlerModule is present but may only protect webhook endpoints. No global API rate limiting. No infrastructure-layer rate limiting (API Gateway, WAF). Agent traffic could overwhelm the application.
- **Compensating Controls**:
  - Apply `@Throttle()` decorator to all API controllers
  - Add AWS WAF with rate-based rules in front of the ALB
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Configure ThrottlerModule globally for all API endpoints with sensible defaults. Add WAF rate rules to the ALB in Terraform.
- **Evidence**: `server/package.json` (@nestjs/throttler), `terraform/ECS/main.tf` (ALB with no WAF)

#### DATA-Q2: Data Residency and Sovereignty ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: ToolJet stores user PII (names, emails, phone numbers) and organization data in PostgreSQL. Terraform ECS uses `var.region` for deployment region but no data residency constraints are enforced. No GDPR or data sovereignty policies are referenced in the codebase. No cross-region replication restrictions exist. If an agent sends PII to an LLM endpoint in a different region, it could violate data residency requirements.
- **Gap**: No data residency controls or documentation. PII storage region is configurable but not enforced. No mechanism prevents data from being transmitted across jurisdictional boundaries.
- **Compensating Controls**:
  - Document data residency requirements per deployment
  - Ensure LLM endpoints are in the same region as data storage
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document data residency requirements. Implement region-aware API responses that redact PII when the consumer is in a different jurisdiction.
- **Evidence**: `terraform/ECS/main.tf` (var.region), `.env.example`, `server/src/entities/user.entity.ts`

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The OTEL tracing configuration (`server/src/otel/tracing.ts`) records HTTP request bodies in spans: `span.setAttribute('http.body', JSON.stringify(sanitizeObject(request.body)))`. This means any PII submitted in POST/PATCH request bodies (user creation with email, name, phone) is recorded in traces. The `AllExceptionsFilter` logs request headers (`headers: request.headers`) which may contain authorization tokens. Audit metrics include `userId` and `organizationId`. **No PII scrubbing middleware or log masking was found.**
- **Gap**: Request bodies containing PII are recorded in OTEL traces. Exception logs include request headers. No PII redaction or masking middleware exists.
- **Compensating Controls**:
  - Add a sanitization function that removes PII fields from request body before recording in spans
  - Configure OTEL collector to drop sensitive attributes
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Implement a request body sanitizer in the OTEL tracing configuration that removes known PII fields (email, firstName, lastName, phoneNumber, password) before `span.setAttribute('http.body', ...)`.
- **Evidence**: `server/src/otel/tracing.ts` (line: `span.setAttribute('http.body', ...)`), `server/src/modules/app/filters/all-exceptions-filter.ts`

---

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, Swagger, AsyncAPI, or GraphQL schema files exist anywhere in the repository. `@nestjs/swagger` is not in `server/package.json` dependencies. No auto-generated API documentation is available.
- **Gap**: No machine-readable API specification exists. Agent tool definitions must be manually authored and maintained.
- **Compensating Controls**:
  - Use NestJS Swagger module to auto-generate OpenAPI spec from controller decorators
  - Manually create an OpenAPI spec for agent-facing endpoints only
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `@nestjs/swagger` and annotate controllers with `@ApiOperation`, `@ApiResponse` decorators. Auto-generate OpenAPI spec as build artifact.
- **Evidence**: `server/package.json` (no @nestjs/swagger), repository-wide search for openapi/swagger files (none found)

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The `AllExceptionsFilter` returns structured JSON error responses with `statusCode`, `timestamp`, `path`, `message`, and `code` fields. It distinguishes between `HttpException`, `TooljetDatabaseError`, `QueryFailedError`, and generic errors. The `ValidationPipe` provides structured validation error messages. **However**, no `retryable` boolean or error category field exists in responses to help agents distinguish retriable from terminal errors.
- **Gap**: Error responses are structured but lack a `retryable` indicator or error category taxonomy for agent consumption.
- **Compensating Controls**:
  - Add `retryable` boolean and `errorCategory` (e.g., `validation`, `auth`, `rate_limit`, `server_error`) to error responses
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Extend AllExceptionsFilter to include `retryable` and `errorCategory` fields in error response body.
- **Evidence**: `server/src/modules/app/filters/all-exceptions-filter.ts`

#### API-Q6: Asynchronous Operation Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: BullMQ (`bullmq`, `@nestjs/bullmq`) is used for background job processing with a Bull Board dashboard at `/jobs`. Temporal (`@temporalio/*`) is used for workflow execution. The `workflow_execution.entity.ts` tracks execution status. **However**, no standardized async API pattern (job submission → polling endpoint → callback) is documented for external consumers.
- **Gap**: Async infrastructure exists internally but no standardized async API pattern (polling endpoint with job ID, webhook callbacks) is exposed for external agent consumption.
- **Compensating Controls**:
  - Expose workflow execution status as a polling endpoint
  - Document expected execution times for long-running operations
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a `/api/jobs/:id/status` polling endpoint for agent-facing async operations.
- **Evidence**: `server/package.json` (bullmq, @temporalio/*), `server/src/modules/workflows/`

#### AUTH-Q4: Identity Propagation and Delegation — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: JWT-based authentication is used (`@nestjs/jwt`, `passport-jwt`). The `@User()` decorator extracts user context from JWT tokens. Organization context propagation exists (login vs organization-specific login at `/authenticate/:organizationId`). The `ExternalApiSecurityGuard` validates external API access via `Basic` authorization header with `EXTERNAL_API_ACCESS_TOKEN`. **However**, no distinction exists between an agent acting under its own identity vs. acting on behalf of a user (no on-behalf-of flow or token exchange).
- **Gap**: No identity propagation distinguishing agent-as-self vs. agent-on-behalf-of-user. External API uses a shared access token, not per-agent identity.
- **Compensating Controls**:
  - Use PATs (Personal Access Tokens) with per-user scoping for agent identity
  - Log the PAT ID alongside the user ID in audit trails
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement per-agent PATs with user delegation context. Log both the agent identity and the delegating user in audit logs.
- **Evidence**: `server/src/modules/auth/guards/external-api-security.guard.ts`, `server/src/entities/user_personal_access_tokens.entity.ts`

#### AUTH-Q5: Credential Management — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: AWS Secrets Manager IAM policy exists (`aws_iam_policy.secrets_manager_policy`) scoped to `tooljet-secret`. **However**, secrets are passed as plaintext environment variables in Terraform ECS task definitions (`LOCKBOX_MASTER_KEY`, `SECRET_KEY_BASE`, `PG_PASS`, database credentials). Helm chart `values.yaml` contains plaintext `pg_password: "postgresql"` and `lockbox_key: "0123456789ABCDEF"`. Kubernetes `deployment.yaml` references secrets via `secretKeyRef` (correct), but some env vars like `TOOLJET_DB_PASS` use plaintext `value:`. `.env.example` uses placeholder patterns.
- **Gap**: Secrets Manager policy exists but is not used for actual secret injection. Secrets are passed as env vars in IaC. Helm values contain plaintext defaults. No secret rotation is configured.
- **Compensating Controls**:
  - Use AWS Secrets Manager for all secrets in ECS task definitions via `secrets` block
  - Replace Helm plaintext secrets with external secrets operator
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Migrate all secrets from environment variables to AWS Secrets Manager references in ECS task definition. Use ExternalSecrets operator for Kubernetes deployments.
- **Evidence**: `terraform/ECS/main.tf` (environment block with plaintext secrets), `deploy/helm/values.yaml` (plaintext pg_password), `deploy/kubernetes/deployment.yaml`

#### STATE-Q2: Queryable Current State — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The server exposes GET endpoints for resource state: `GET /ext/users`, `GET /ext/user/:id`, `GET /ext/workspaces`. NestJS controllers have `@Get` decorators for apps, organizations, data sources, and workflows. **However**, the external API controller (`external-apis/controller.ts`) throws `NotFoundException` for all endpoints (community edition stubs), suggesting the external API is an enterprise-only feature.
- **Gap**: External API endpoints are stubs in the community edition. State queryability depends on internal API endpoints which are designed for the frontend, not for programmatic agent access.
- **Compensating Controls**:
  - Use internal API endpoints with appropriate authentication for agent access
  - Document the internal API surface for agent consumption
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement or enable the external API endpoints for community edition, or document internal API endpoints suitable for agent integration.
- **Evidence**: `server/src/modules/external-apis/controller.ts` (NotFoundException stubs)

#### DATA-Q3: Selective Query Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The ToolJet DB (PostgREST) supports pagination, filtering, and sorting natively through PostgREST query parameters. Internal API endpoints likely support query parameters for listing resources. **However**, no evidence of explicit pagination, cursor-based pagination, or result size limits was found in the external API controller stubs or documented in the codebase.
- **Gap**: No documented pagination or result size limits on agent-facing API endpoints. PostgREST provides pagination but application endpoints may return unbounded result sets.
- **Compensating Controls**:
  - Configure PostgREST default page size limits
  - Add pagination middleware to application endpoints
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Implement mandatory pagination on all list endpoints with a default page size and maximum limit.
- **Evidence**: `server/src/modules/external-apis/controller.ts`, `docker-compose.yaml` (PostgREST service)

#### DATA-Q4: System of Record Designations — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: ToolJet's PostgreSQL database is the authoritative system of record for app definitions, user accounts, organizations, data source configurations, and workflow definitions. This is implicit in the architecture (single database, no data replication to external systems). **However**, no formal system-of-record documentation exists. No master data management process or conflict resolution logic was found.
- **Gap**: No formal system-of-record designations. No documentation specifying which data entities are authoritative.
- **Compensating Controls**:
  - Document ToolJet's PostgreSQL as the system of record for all managed entities
- **Remediation Timeline**: 7–14 days
- **Recommendation**: Create a data ownership document identifying ToolJet's database as the authoritative source for app, user, organization, and configuration entities.
- **Evidence**: `server/src/entities/` (70+ entity definitions), `docker-compose.yaml` (single PostgreSQL database)

#### DATA-Q5: Temporal Metadata and Freshness — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: All major entities use `@CreateDateColumn` (`created_at`) and `@UpdateDateColumn` (`updated_at`) with `default: () => 'now()'`. PostgreSQL stores timestamps in UTC by default. The app_version entity has `publishedAt` and `releasedAt` timestamps. **However**, no `Cache-Control`, `X-Data-Age`, or freshness headers are returned in API responses. No consistency-level signaling exists.
- **Gap**: Temporal metadata exists in the database layer but is not surfaced in API response headers. Agents cannot determine data freshness from API responses.
- **Compensating Controls**:
  - Add `Last-Modified` and `ETag` headers to GET responses using entity `updatedAt` timestamps
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add `Last-Modified` header to GET responses using the entity's `updatedAt` field.
- **Evidence**: `server/src/entities/user.entity.ts` (createdAt, updatedAt), `server/src/entities/app.entity.ts` (createdAt, updatedAt)

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Database schema versioning is excellent: `server/migrations/` contains 170+ TypeORM migrations with timestamps, tracked in order. API versioning is configured via `VersioningType.URI` in `main.ts`. JSON Schema files exist (`server/src/dto/validators/schemas/`). CODEOWNERS protects migration and module files with required reviewers. **However**, no API contract testing (Pact, OpenAPI diff, buf breaking) exists in CI pipelines. No breaking change detection tools are configured.
- **Gap**: Database schema versioning is strong but API contract testing is absent. Breaking API changes could affect agent tool bindings without detection.
- **Compensating Controls**:
  - Add OpenAPI spec generation and diff checking in CI
  - Implement consumer-driven contract tests (Pact) for agent-facing endpoints
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `@nestjs/swagger` for OpenAPI generation and integrate `openapi-diff` in CI to detect breaking changes.
- **Evidence**: `server/migrations/` (170+ migrations), `server/src/main.ts` (VersioningType.URI), `.github/workflows/ci.yml` (no contract testing), `CODEOWNERS`

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: CloudWatch log groups with 30-day retention and Container Insights are enabled in ECS Terraform. Vulnerability CI sends Slack notifications. **However**, no CloudWatch alarms for error rates, latency, or anomaly detection are defined in Terraform. No PagerDuty/OpsGenie integration. No SLO-based alerting.
- **Gap**: No runtime alerting on API error rates or latency. Target system degradation would not be detected until agents start cascading failures.
- **Compensating Controls**:
  - Add CloudWatch alarms for 5xx error rate and P99 latency on the ALB
  - Integrate OTEL metrics with a Grafana dashboard and alerting
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Define CloudWatch alarms in Terraform for ALB 5xx rate > 1% and P99 latency > 5s.
- **Evidence**: `terraform/ECS/main.tf` (CloudWatch log groups, no alarms), `.github/workflows/vulnerability-ci.yml`

#### ENG-Q1: Infrastructure Governance — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: (1) IaC exists: Terraform for ECS/EC2/GCP/Azure, Helm charts, Kubernetes manifests — **YES**. (2) Peer review: CODEOWNERS enforces code review on `module.ts`, `package.json`, and migration files; CI triggers on PRs — **PARTIAL** (CODEOWNERS doesn't cover all Terraform files). (3) Drift detection: No `aws_config_configuration_recorder`, no `terraform plan -detailed-exitcode` in CI, no drift detection — **NO**.
- **Gap**: Drift detection is absent. CODEOWNERS coverage is incomplete for IaC files.
- **Compensating Controls**:
  - Add Terraform plan output review as a PR check
  - Add CODEOWNERS entry for `terraform/**`
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add `terraform/` to CODEOWNERS. Implement scheduled `terraform plan` drift detection in CI.
- **Evidence**: `terraform/ECS/main.tf`, `CODEOWNERS`, `.github/workflows/ci.yml`

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: CI pipeline includes build, lint (frontend/server/plugins), unit tests, and e2e tests. Cypress tests exist for UI testing. **However**, no API contract testing (Pact, OpenAPI validation, schema comparison) exists. No breaking change detection tools are configured.
- **Gap**: No API contract testing in CI. Breaking API changes are not caught before production.
- **Compensating Controls**:
  - Add supertest-based API integration tests in the existing e2e test suite
  - Implement OpenAPI spec validation in CI once spec is generated
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add API contract test suite using supertest with schema validation against generated OpenAPI spec.
- **Evidence**: `.github/workflows/ci.yml`, `.github/workflows/cypress-appbuilder.yml`

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Kubernetes deployment uses `RollingUpdate` (maxUnavailable:1, maxSurge:1). ECS uses `deployment_maximum_percent:200, deployment_minimum_healthy_percent:100`. Docker images are tagged via release workflow. **However**, no blue/green deployment, canary deployment, automatic rollback triggers, or feature flags were found. Rollback requires manual `kubectl rollout undo` or ECS task definition revert.
- **Gap**: No automated rollback capability. Manual intervention required to roll back a broken deployment.
- **Compensating Controls**:
  - Use Kubernetes rollout undo for quick manual rollback
  - Tag Docker images with git SHA for deterministic rollback targets
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add health-check-based automatic rollback triggers in Kubernetes and ECS deployments.
- **Evidence**: `deploy/kubernetes/deployment.yaml` (RollingUpdate), `terraform/ECS/main.tf` (ECS service), `.github/workflows/docker-release.yml`

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Server has unit tests (`npm run test`), e2e tests (`npm run test:e2e`), and Polly.js for HTTP recording/playback. CI runs both unit and e2e tests with a 30-minute timeout. Cypress tests cover frontend UI flows. **However**, no dedicated API test suites (Postman/Newman collections, REST Assured equivalent) or API-specific contract tests exist.
- **Gap**: Test coverage exists but is not API-specific. No dedicated API test suite validates input handling, output format, error responses, and edge cases for agent-facing endpoints.
- **Compensating Controls**:
  - Extend existing e2e tests to cover all external API endpoints
  - Add response schema validation to e2e tests
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a dedicated API test suite for agent-facing endpoints using supertest with JSON schema validation.
- **Evidence**: `.github/workflows/ci.yml` (unit-test, e2e-test jobs), `server/package.json` (test scripts)

#### ENG-Q5: Encryption at Rest — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Application-level encryption exists for data source credentials via `EncryptionService` (AES-256-GCM with LOCKBOX_MASTER_KEY). **However**, the RDS instance in Terraform has no `storage_encrypted = true` or `kms_key_id` setting. No customer-managed KMS keys are defined. The database stores unencrypted PII (user names, emails, phone numbers) at rest.
- **Gap**: No infrastructure-layer encryption at rest for RDS. PII in the database is not encrypted at the storage layer.
- **Compensating Controls**:
  - Enable RDS storage encryption (default encryption uses AWS-managed key)
  - Add `storage_encrypted = true` to the `aws_db_instance` resource
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add `storage_encrypted = true` and optionally `kms_key_id` to `aws_db_instance` in Terraform.
- **Evidence**: `terraform/ECS/main.tf` (aws_db_instance without storage_encrypted), `server/src/modules/encryption/service.ts`

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: `docker-compose.yaml` provides a local development environment with PostgreSQL, Redis, and PostgREST. `render.yaml` defines preview environments. The `app_environments.entity.ts` supports multiple environments per application. Database seed scripts exist (`server/scripts/seeds.ts`). Cypress tests run against test environments. **However**, no production-equivalent staging environment is defined in IaC. Render preview is for PR review, not persistent staging.
- **Gap**: No persistent staging environment with production-equivalent data shape. Local docker-compose and Render previews are not suitable for agent testing.
- **Compensating Controls**:
  - Use docker-compose environment for initial agent testing
  - Create a dedicated staging Terraform deployment
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Define a staging environment in Terraform with production-equivalent configuration and synthetic data.
- **Evidence**: `docker-compose.yaml`, `render.yaml`, `server/src/entities/app_environments.entity.ts`

---

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO
- **Finding**: ToolJet exposes a documented REST interface. NestJS `@Controller` decorators define REST routes at `/api/*` prefix. PostgREST provides a RESTful interface for ToolJet DB at port 3002. External API surface exists at `/ext/*`. SCIM endpoints at `/api/scim`. The REST interface is functional and well-structured for agent integration.
- **Implication**: The REST API provides a viable integration surface for agent tools. No database-direct or file-based integration is required.
- **Recommendation**: Document the complete API surface in an OpenAPI spec for agent tool generation.
- **Evidence**: `server/src/main.ts` (global prefix configuration), `server/src/modules/auth/controller.ts`, `server/src/modules/external-apis/controller.ts`

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No idempotency key support was found in write endpoints. No idempotency middleware, decorators, or unique constraint enforcement on business keys for POST operations. Write endpoints (user creation, app creation) do not support idempotency keys.
- **Implication**: If agent scope is later expanded to write-enabled, idempotency must be addressed as a BLOCKER.
- **Recommendation**: Plan idempotency key support for write endpoints before expanding agent scope to write-enabled.
- **Evidence**: `server/src/modules/external-apis/controller.ts`, `server/src/modules/auth/controller.ts`

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: JSON is the primary response format (NestJS default serialization). SCIM endpoints support `application/scim+json`. No XML, binary, or protobuf response formats. Well-documented JSON APIs can be exposed as agent tools with minimal adaptation.
- **Implication**: JSON responses are ideal for LLM consumption. No additional parsing logic required.
- **Evidence**: `server/src/main.ts` (SCIM body parser), `server/package.json`

### API-Q7: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: `@nestjs/event-emitter` (EventEmitter2) is used for internal events (audit log entries, email notifications). WebSocket support exists (`@nestjs/websockets`, `y-websocket` for multiplayer editing). **However**, no external webhook or event stream (SNS/SQS/Kafka) endpoints exist for external consumers.
- **Implication**: Event emission is internal only. Proactive agent patterns (react to state changes) would require adding webhook or event stream capabilities.
- **Recommendation**: Consider adding webhook support for key state changes (app released, workflow completed) when event-driven agent patterns are needed.
- **Evidence**: `server/package.json` (@nestjs/event-emitter, @nestjs/websockets)

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: `@nestjs/throttler` is configured but rate limits are not documented. No `X-RateLimit-Remaining` or `Retry-After` headers were found in response handling code. No API Gateway usage plans exist in Terraform.
- **Implication**: Agents cannot self-throttle based on rate limit headers. Undocumented limits cause unpredictable failures.
- **Recommendation**: Document rate limits and return standard rate limit headers in API responses.
- **Evidence**: `server/package.json` (@nestjs/throttler)

### AUTH-Q1: Machine Identity Authentication

- **Severity**: INFO
- **Finding**: JWT-based auth with `@nestjs/jwt` and `passport-jwt`. Personal Access Tokens (`user_personal_access_tokens.entity.ts`) with scoped permissions and expiry. External API uses Basic auth with `EXTERNAL_API_ACCESS_TOKEN`. SCIM provisioning exists. PAT sessions tracked separately (`sessionType: PAT`). Machine identity is **supported** through PATs — a non-human principal can authenticate.
- **Implication**: PATs provide machine identity support for agent integration. However, PATs are app-scoped (not agent-scoped), and the external API uses a single shared token without per-agent attribution. Dedicated agent identity types would improve auditability.
- **Recommendation**: Create agent-specific PAT scopes and ensure audit attribution includes the PAT ID.
- **Evidence**: `server/src/entities/user_personal_access_tokens.entity.ts`, `server/src/modules/auth/guards/external-api-security.guard.ts`

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No `@VersionColumn`, ETag headers, or `If-Match` header handling was found. TypeORM entities do not use optimistic locking. `updatedAt` fields exist but are not used for concurrency control. DynamoDB conditional writes are not applicable (PostgreSQL only).
- **Implication**: If agent scope is expanded to write-enabled, concurrency controls must be addressed.
- **Evidence**: `server/src/entities/app.entity.ts`, `server/src/entities/app_version.entity.ts`

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits per agent identity exist. No `max_records_per_operation` or `max_spend_per_session` controls were found. No per-identity rate limiting beyond the global throttler.
- **Implication**: If agent scope is expanded to write-enabled, transaction limits must be implemented.
- **Evidence**: `server/package.json`, `server/src/modules/external-apis/controller.ts`

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: `AppVersionStatus` enum in `app_version.entity.ts` supports `DRAFT`, `PUBLISHED`, and `RELEASED` states. App lifecycle includes versioning with draft-to-release workflow. The OTEL audit metrics track `APP_RELEASE` events. This provides a strong foundation for human-in-the-loop patterns.
- **Implication**: Draft/released states exist and could support agent-proposes/human-confirms patterns when write scope is enabled.
- **Evidence**: `server/src/entities/app_version.entity.ts` (AppVersionStatus enum)

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable approval gate mechanism was found. The app release process (DRAFT → PUBLISHED → RELEASED) is a built-in workflow but not configurable per operation type for external agent actions.
- **Implication**: Approval gates would need to be built if write-enabled agent operations require human oversight.
- **Evidence**: `server/src/entities/app_version.entity.ts`, `server/src/modules/workflows/`

### OBS-Q1: Distributed Tracing and Structured Logging

- **Severity**: INFO
- **Finding**: **Excellent observability implementation.** OpenTelemetry SDK with comprehensive instrumentation: `OTLPTraceExporter`, `OTLPMetricExporter`, `W3CTraceContextPropagator`, `W3CBaggagePropagator`, `HttpInstrumentation`, `ExpressInstrumentation`, `NestInstrumentation`, `PgInstrumentation`, `PinoInstrumentation`, `RuntimeNodeInstrumentation`. Structured JSON logging via `nestjs-pino`. Sentry integration for error tracking. Custom metrics for API hits, duration, concurrent users, and sessions.
- **Implication**: Agent-initiated requests are fully traceable. This is a strength — tracing and logging infrastructure is production-grade.
- **Recommendation**: Ensure OTEL is enabled for agent-facing deployments (currently EE/Cloud edition only based on edition check).
- **Evidence**: `server/src/otel/tracing.ts`, `server/package.json` (@opentelemetry/*)

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: **Excellent business metrics.** `audit-metrics.ts` implements: `app.creations.total`, `app.updates.total`, `app.deletions.total`, `app.releases.total`, `query.executions.total`, `query.failures.total`, `query.duration`, `app.success_rate`, `app.active_users`, `datasource.creations.total`, `user.sessions.total`, `audit.logs.active_users`. Metrics are split across `tooljet-platform` and `tooljet-app` meters.
- **Implication**: Rich business metrics exist for monitoring agent interaction outcomes. This is a notable strength for agent observability.
- **Evidence**: `server/src/otel/audit-metrics.ts`

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: TypeORM entities use clear, semantic camelCase field names: `firstName`, `lastName`, `organizationId`, `currentVersionId`, `createdAt`, `updatedAt`. Database columns use snake_case (`first_name`, `last_name`). The `humps` library is used for case conversion. No legacy abbreviations or cryptic codes found.
- **Implication**: Field names are agent-friendly and LLM-interpretable without a data dictionary.
- **Evidence**: `server/src/entities/user.entity.ts`, `server/src/entities/app.entity.ts`

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No formal data catalog (Glue, Collibra, DataHub) exists. The `docs/` directory contains documentation but not a data catalog. TypeORM entity files serve as the de facto schema documentation. Migration files document schema evolution.
- **Implication**: Agent tool builders must read TypeORM entities to understand data structures. A formal catalog would accelerate tool definition.
- **Recommendation**: Generate data dictionary documentation from TypeORM entities.
- **Evidence**: `server/src/entities/`, `server/migrations/`, `docs/`

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No formal data quality scores, completeness metrics, or data profiling reports exist. No null rate monitoring, duplicate detection, or data freshness SLAs were found. OTEL metrics track query success rates but not data quality.
- **Implication**: Agents cannot assess data quality before acting on it. Data quality is a planning input for agent design.
- **Evidence**: `server/src/otel/audit-metrics.ts` (query metrics but no data quality metrics)

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: ToolJet exposes REST API at `/api/*` prefix via NestJS controllers. PostgREST at port 3002 for ToolJet DB. External API at `/ext/*`. SCIM at `/api/scim`. No direct database access, file-based exchange, or UI automation required.
- **Gap**: REST interface exists and is well-structured. However, no comprehensive API documentation exists beyond code.
- **Recommendation**: Generate OpenAPI documentation from NestJS decorators.
- **Evidence**: `server/src/main.ts`, `server/src/modules/auth/controller.ts`, `server/src/modules/external-apis/controller.ts`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, Swagger, AsyncAPI, or GraphQL schema files found. No `@nestjs/swagger` dependency.
- **Gap**: No machine-readable API specification exists.
- **Recommendation**: Add `@nestjs/swagger` and generate OpenAPI spec.
- **Evidence**: `server/package.json`

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: AllExceptionsFilter returns `{statusCode, timestamp, path, message, code}`. Distinguishes HttpException, TooljetDatabaseError, QueryFailedError. Missing `retryable` indicator.
- **Gap**: No retryable indicator or error category for agent consumption.
- **Recommendation**: Add `retryable` and `errorCategory` fields.
- **Evidence**: `server/src/modules/app/filters/all-exceptions-filter.ts`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No idempotency key support found in write endpoints.
- **Gap**: Write endpoints lack idempotency. Not a blocker for read-only scope.
- **Recommendation**: Plan idempotency before expanding to write-enabled scope.
- **Evidence**: `server/src/modules/external-apis/controller.ts`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: JSON primary format. SCIM supports application/scim+json. No binary/XML.
- **Gap**: None for agent consumption.
- **Recommendation**: Maintain JSON as the response format.
- **Evidence**: `server/src/main.ts`

#### API-Q6: Asynchronous Operation Support
- **Severity**: RISK-QUALITY
- **Finding**: BullMQ and Temporal exist but no standardized async API pattern for external consumers.
- **Gap**: No polling endpoint or webhook callback for async operations.
- **Recommendation**: Expose async operation status endpoints.
- **Evidence**: `server/package.json`, `server/src/modules/workflows/`

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: Internal EventEmitter2 and WebSockets exist. No external webhook/event stream.
- **Gap**: Event emission is internal only.
- **Recommendation**: Add webhook support for key state changes.
- **Evidence**: `server/package.json`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: ThrottlerModule configured but rate limits undocumented. No rate limit headers.
- **Gap**: No rate limit documentation or headers for agent self-throttling.
- **Recommendation**: Document rate limits and return standard headers.
- **Evidence**: `server/package.json`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: JWT-based auth with `@nestjs/jwt` and `passport-jwt`. Personal Access Tokens (`user_personal_access_tokens.entity.ts`) with scoped permissions and expiry. External API uses Basic auth with `EXTERNAL_API_ACCESS_TOKEN`. SCIM provisioning exists. PAT sessions tracked separately (`sessionType: PAT`). Machine identity is **supported** through PATs — a non-human principal can authenticate.
- **Gap**: PATs exist but are app-scoped, not agent-scoped. External API uses a single shared token. No dedicated agent identity type.
- **Recommendation**: Create agent-specific PAT scopes and ensure audit attribution includes the PAT ID.
- **Evidence**: `server/src/entities/user_personal_access_tokens.entity.ts`, `server/src/modules/auth/guards/external-api-security.guard.ts`

#### AUTH-Q2: Scoped Permissions
- **Severity**: RISK-SAFETY
- **Finding**: CASL ABAC with fine-grained actions. Group permissions system. IAM SSM policy uses wildcard. No agent-specific scope.
- **Gap**: No agent-specific permission scope. IAM SSM wildcard.
- **Recommendation**: Define agent-specific CASL role.
- **Evidence**: `server/src/modules/casl/casl-ability.factory.ts`, `terraform/ECS/main.tf`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: FeatureAbilityGuard used extensively. Multiple ability directories. CASL defines granular actions.
- **Gap**: No agent-specific action restrictions.
- **Recommendation**: Extend CASL for agent ability sets.
- **Evidence**: `server/src/modules/auth/ability/`, `server/src/modules/casl/check_policies.decorator.ts`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: RISK-QUALITY
- **Finding**: JWT tokens with User decorator. Organization-specific login. No on-behalf-of flow.
- **Gap**: No agent-as-self vs agent-on-behalf-of-user distinction.
- **Recommendation**: Implement per-agent PATs with delegation context.
- **Evidence**: `server/src/modules/auth/guards/external-api-security.guard.ts`

#### AUTH-Q5: Credential Management
- **Severity**: RISK-QUALITY
- **Finding**: Secrets Manager policy exists. Secrets passed as env vars. Helm plaintext defaults.
- **Gap**: Secrets Manager not used for injection. No rotation.
- **Recommendation**: Migrate to Secrets Manager references.
- **Evidence**: `terraform/ECS/main.tf`, `deploy/helm/values.yaml`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Audit logs in PostgreSQL with OTEL integration. No CloudTrail. No immutable storage.
- **Gap**: Audit logs are mutable.
- **Recommendation**: Add CloudTrail and S3 object lock.
- **Evidence**: `server/src/entities/audit_log.entity.ts`, `terraform/ECS/main.tf`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: User archival, PAT expiry, session invalidation exist. No instant agent revocation.
- **Gap**: No dedicated agent suspension API.
- **Recommendation**: Create PAT revocation endpoint.
- **Evidence**: `server/src/entities/user_personal_access_tokens.entity.ts`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Temporal workflows and TypeORM transactions exist. No explicit compensation logic.
- **Gap**: No compensation endpoints.
- **Recommendation**: Implement compensation activities in Temporal.
- **Evidence**: `server/package.json`, `server/src/modules/workflows/`

#### STATE-Q2: Queryable Current State
- **Severity**: RISK-QUALITY
- **Finding**: GET endpoints exist but external API stubs throw NotFoundException in CE edition.
- **Gap**: External API is enterprise-only.
- **Recommendation**: Enable external API or document internal endpoints.
- **Evidence**: `server/src/modules/external-apis/controller.ts`

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No optimistic locking or ETags. updatedAt exists but not used for concurrency.
- **Gap**: No concurrency controls for write operations.
- **Recommendation**: Address before expanding to write-enabled scope.
- **Evidence**: `server/src/entities/app.entity.ts`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: No circuit breaker library. No retry policies or timeouts on external calls.
- **Gap**: No resilience patterns for external dependencies.
- **Recommendation**: Add opossum circuit breaker library.
- **Evidence**: `server/package.json`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: ThrottlerModule present but may be webhook-only. No global API rate limiting. No WAF.
- **Gap**: Insufficient rate limiting for agent traffic.
- **Recommendation**: Configure global throttling and add WAF rules.
- **Evidence**: `server/package.json`, `terraform/ECS/main.tf`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits per agent identity.
- **Gap**: No blast radius controls.
- **Recommendation**: Implement before expanding to write-enabled scope.
- **Evidence**: `server/src/modules/external-apis/controller.ts`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path. ToolJet is P2 priority.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: AppVersionStatus enum: DRAFT, PUBLISHED, RELEASED. Strong foundation for HITL patterns.
- **Gap**: Draft states exist but not designed for agent-proposes patterns.
- **Recommendation**: Leverage existing draft/release workflow for agent HITL.
- **Evidence**: `server/src/entities/app_version.entity.ts`

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable approval gate mechanism. App release is built-in but not externally configurable.
- **Gap**: No approval gate API.
- **Recommendation**: Build approval gates when write-enabled agents are planned.
- **Evidence**: `server/src/modules/workflows/`

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: docker-compose for local dev. Render previews for PR review. No persistent staging.
- **Gap**: No production-equivalent staging environment.
- **Recommendation**: Define staging environment in IaC.
- **Evidence**: `docker-compose.yaml`, `render.yaml`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: Extensive PII stored. Application-level encryption for credentials. No field-level classification.
- **Gap**: No data classification system.
- **Recommendation**: Implement field-level data classification.
- **Evidence**: `server/src/entities/user.entity.ts`, `server/src/modules/encryption/service.ts`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: PII in PostgreSQL. Region configurable but not enforced. No data residency controls.
- **Gap**: No data residency enforcement.
- **Recommendation**: Document and enforce data residency requirements.
- **Evidence**: `terraform/ECS/main.tf`, `server/src/entities/user.entity.ts`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK-QUALITY
- **Finding**: PostgREST supports pagination. Application endpoints lack documented pagination.
- **Gap**: No documented pagination on agent-facing endpoints.
- **Recommendation**: Implement mandatory pagination.
- **Evidence**: `server/src/modules/external-apis/controller.ts`

#### DATA-Q4: System of Record Designations
- **Severity**: RISK-QUALITY
- **Finding**: PostgreSQL is implicit system of record. No formal documentation.
- **Gap**: No formal system-of-record designations.
- **Recommendation**: Document data ownership.
- **Evidence**: `server/src/entities/`

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK-QUALITY
- **Finding**: createdAt/updatedAt on all entities. No freshness headers in responses.
- **Gap**: Temporal metadata not surfaced in API.
- **Recommendation**: Add Last-Modified headers.
- **Evidence**: `server/src/entities/user.entity.ts`

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: OTEL traces record request bodies with PII. Exception logs include headers. No PII scrubbing.
- **Gap**: PII leaks into traces and logs.
- **Recommendation**: Implement PII sanitizer in OTEL tracing.
- **Evidence**: `server/src/otel/tracing.ts`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics or profiling. OTEL tracks query success but not data quality.
- **Gap**: No data quality awareness.
- **Recommendation**: Consider data quality metrics for critical entities.
- **Evidence**: `server/src/otel/audit-metrics.ts`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: 170+ migrations. URI versioning. CODEOWNERS. No API contract testing in CI.
- **Gap**: No API contract testing or breaking change detection.
- **Recommendation**: Add OpenAPI generation and diff checking.
- **Evidence**: `server/migrations/`, `server/src/main.ts`, `.github/workflows/ci.yml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Clear camelCase field names. humps library for conversion. No legacy abbreviations.
- **Gap**: None. Field names are agent-friendly.
- **Recommendation**: Maintain current naming conventions.
- **Evidence**: `server/src/entities/user.entity.ts`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal data catalog. TypeORM entities serve as schema documentation.
- **Gap**: No formal catalog for agent tool builders.
- **Recommendation**: Generate data dictionary from entities.
- **Evidence**: `server/src/entities/`, `docs/`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: INFO
- **Finding**: Comprehensive OTEL with W3C propagation, HTTP/Express/Nest/Pg/Pino instrumentation. JSON logging via nestjs-pino. Sentry integration. This is production-grade observability.
- **Gap**: OTEL is EE/Cloud edition only. CE edition may lack tracing.
- **Recommendation**: Enable OTEL for all editions or ensure agent deployments use EE.
- **Evidence**: `server/src/otel/tracing.ts`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: CloudWatch logs and Container Insights. No alarms. No PagerDuty/OpsGenie.
- **Gap**: No runtime alerting on error rates or latency.
- **Recommendation**: Add CloudWatch alarms for ALB metrics.
- **Evidence**: `terraform/ECS/main.tf`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: Extensive custom metrics: app lifecycle, query execution, active users, success rates.
- **Gap**: None. Business metrics are comprehensive.
- **Recommendation**: Use these metrics to monitor agent interaction outcomes.
- **Evidence**: `server/src/otel/audit-metrics.ts`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance
- **Severity**: RISK-QUALITY
- **Finding**: IaC exists. CODEOWNERS. CI on PRs. No drift detection.
- **Gap**: No drift detection. CODEOWNERS incomplete for IaC.
- **Recommendation**: Add terraform/ to CODEOWNERS. Implement drift detection.
- **Evidence**: `terraform/ECS/main.tf`, `CODEOWNERS`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: CI with build, lint, unit tests, e2e tests, Cypress. No API contract testing.
- **Gap**: No API contract testing or breaking change detection.
- **Recommendation**: Add contract testing with OpenAPI validation.
- **Evidence**: `.github/workflows/ci.yml`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: RollingUpdate strategy. Docker image tagging. No automated rollback.
- **Gap**: Manual rollback only.
- **Recommendation**: Add automated rollback triggers.
- **Evidence**: `deploy/kubernetes/deployment.yaml`, `terraform/ECS/main.tf`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: Unit and e2e tests exist. Cypress for frontend. No dedicated API test suite.
- **Gap**: No API-specific test coverage.
- **Recommendation**: Create dedicated API test suite.
- **Evidence**: `.github/workflows/ci.yml`

#### ENG-Q5: Encryption at Rest
- **Severity**: RISK-QUALITY
- **Finding**: Application-level encryption for credentials. RDS has no storage_encrypted. No KMS keys.
- **Gap**: No infrastructure-level encryption at rest for RDS.
- **Recommendation**: Add storage_encrypted = true to aws_db_instance.
- **Evidence**: `terraform/ECS/main.tf`

---

## Evidence Index

### Infrastructure as Code
| File | Questions Referenced |
|------|---------------------|
| terraform/ECS/main.tf | AUTH-Q1, AUTH-Q2, AUTH-Q5, AUTH-Q6, STATE-Q5, DATA-Q2, OBS-Q2, ENG-Q1, ENG-Q3, ENG-Q5 |
| deploy/helm/values.yaml | AUTH-Q5, HITL-Q3 |
| deploy/kubernetes/deployment.yaml | AUTH-Q5, ENG-Q3 |

### Source Code
| File | Questions Referenced |
|------|---------------------|
| server/src/main.ts | API-Q1, API-Q5, API-Q8, DISC-Q1 |
| server/src/modules/auth/controller.ts | API-Q1, AUTH-Q1 |
| server/src/modules/external-apis/controller.ts | API-Q1, API-Q4, STATE-Q2, DATA-Q3 |
| server/src/modules/app/filters/all-exceptions-filter.ts | API-Q3, DATA-Q6 |
| server/src/modules/app/interceptors/response.interceptor.ts | AUTH-Q6 |
| server/src/modules/casl/casl-ability.factory.ts | AUTH-Q2, AUTH-Q3 |
| server/src/modules/encryption/service.ts | DATA-Q1 |
| server/src/modules/auth/guards/external-api-security.guard.ts | AUTH-Q1, AUTH-Q4 |
| server/src/otel/tracing.ts | OBS-Q1, DATA-Q6 |
| server/src/otel/audit-metrics.ts | AUTH-Q6, OBS-Q3, DATA-Q7 |
| server/src/entities/user.entity.ts | DATA-Q1, DATA-Q2, DATA-Q5, AUTH-Q7, DISC-Q2 |
| server/src/entities/app.entity.ts | API-Q1, DISC-Q2 |
| server/src/entities/app_version.entity.ts | HITL-Q1, STATE-Q3 |
| server/src/entities/audit_log.entity.ts | AUTH-Q6 |
| server/src/entities/user_personal_access_tokens.entity.ts | AUTH-Q1, AUTH-Q7 |
| server/src/entities/user_sessions.entity.ts | AUTH-Q7 |
| server/src/entities/data_source_options.entity.ts | DATA-Q1 |
| server/src/entities/granular_permissions.entity.ts | AUTH-Q2 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| .github/workflows/ci.yml | ENG-Q1, ENG-Q2, ENG-Q4, DISC-Q1 |
| .github/workflows/docker-release.yml | ENG-Q3 |
| .github/workflows/vulnerability-ci.yml | OBS-Q2 |
| .github/workflows/cypress-appbuilder.yml | ENG-Q2, ENG-Q4 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| docker-compose.yaml | STATE-Q4, DATA-Q3, HITL-Q3, DATA-Q4 |
| docker/ce-production.Dockerfile | ENG-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| server/package.json | API-Q2, API-Q6, API-Q7, API-Q8, AUTH-Q1, STATE-Q1, STATE-Q4, STATE-Q5, OBS-Q1 |
| package.json | ENG-Q1 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| .env.example | AUTH-Q5, DATA-Q2 |
| render.yaml | HITL-Q3 |
| CODEOWNERS | ENG-Q1, DISC-Q1 |
