# Agentic Readiness Assessment Report

**Target**: Prowlarr--Prowlarr
**Date**: 2025-05-08
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: csharp, media, desktop
**Context**: Indexer manager/proxy for the *arr suite.

**Archetype Justification**: Prowlarr owns persistent state in SQLite/PostgreSQL databases, exposes full CRUD operations on business entities (indexers, applications, tags, notifications), and manages user-specific configuration data.

**Surface flags**:
  - has_persistent_data_store: true
  - has_http_rpc_surface: true
  - has_auth_surface: true
  - has_write_operations: true
  - has_logging_of_user_data: true

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 1 | **RISK-SAFETY**: 7 | **RISK-QUALITY**: 10 | **INFOs**: 10

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days.

**V6 Classification Rationale**: This repo has 1 High finding (AUTH-Q1 BLOCKER), 17 Medium findings (7 safety-impact + 10 quality), and 10 Low findings. The matched rule is "1-2 High → Remediation Required." The V5 Readiness Profile and V6 Classification agree: the single BLOCKER gates all agent deployment until resolved.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 1 |
| RISK-SAFETY | 7 |
| RISK-QUALITY | 10 |
| INFO | 10 |
| N/A | 0 |
| Not Evaluated (extended) | 15 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 4
**Extended Questions Not Triggered**: 15
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: stateful-crud (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: Prowlarr uses a single shared API key for all programmatic access (`X-Api-Key` header, `apikey` query param, or `Authorization: Bearer` value). The same API key is used by all consumers — there is no mechanism to issue distinct machine identities per agent or per consumer. Authentication validates that the caller possesses the API key, but cannot distinguish *which* agent instance made a call for audit or attribution purposes.
- **Gap**: No support for per-agent machine identity. A single shared API key cannot provide principal attribution in audit logs. All API consumers authenticate as the same identity.
- **Remediation**:
  - **Immediate**: Implement multiple API key support with principal labels — each agent or integration gets its own key that is logged in the Auth logger with its label/name.
  - **Target State**: Each agent identity has a unique credential with attribution in audit logs, and individual keys can be revoked without affecting other consumers.
  - **Estimated Effort**: Medium
  - **Dependencies**: AUTH-Q7 (agent identity suspension requires per-agent keys to exist first)
- **Evidence**: `src/Prowlarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`

---

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The application has no scoped permission model. Authentication is binary — a valid API key grants full access to all endpoints and all operations (read, write, delete). There is no concept of roles, scopes, or permission levels differentiating agent access from full admin access.
- **Gap**: No least-privilege enforcement. An agent with the API key can perform any operation, including destructive ones (delete indexers, reset configuration).
- **Compensating Controls**:
  - Deploy an API Gateway in front of Prowlarr that restricts which endpoints an agent identity can reach (method + path filtering)
  - Limit agent access to read-only operations via a reverse proxy that blocks non-GET HTTP methods
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement role-based access control (RBAC) with at least read-only and admin roles. Add scope claims to API keys that restrict accessible endpoints per key.
- **Evidence**: `src/Prowlarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/NzbDrone.Host/Startup.cs`

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization exists. The `FallbackPolicy` requires authentication on all endpoints, but once authenticated, there is no distinction between read and write operations. A caller authenticated with the API key can GET, POST, PUT, and DELETE on any resource.
- **Gap**: Cannot restrict an agent to read-only operations at the application level. No middleware or attribute-based authorization differentiates between HTTP methods or operation types.
- **Compensating Controls**:
  - Use an API Gateway or reverse proxy to enforce method-level restrictions per API key
  - Implement a custom authorization middleware that checks HTTP method against a per-key permission set
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Introduce an authorization policy that distinguishes read (GET) from write (POST/PUT/DELETE) operations, enforceable per authenticated principal.
- **Evidence**: `src/NzbDrone.Host/Startup.cs` (FallbackPolicy), `src/Prowlarr.Http/Authentication/UiAuthorizationHandler.cs`

#### AUTH-Q6: Immutable Audit Logging — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Authentication events (login success/failure/logout) are logged via a dedicated "Auth" NLog logger with IP addresses. However, there is no immutable audit trail for API operations. API calls are logged at debug level only, with no principal attribution beyond "authenticated". Logs are written to local rotating files with no integrity protection — they can be modified or deleted by anyone with filesystem access.
- **Gap**: No immutable, tamper-evident audit log for API operations. No centralized audit logging (no CloudTrail, no SIEM integration). API operation logs do not record which principal performed the action.
- **Compensating Controls**:
  - Ship NLog output to an immutable log destination (CloudWatch Logs with retention lock, S3 with Object Lock)
  - Add structured audit logging middleware that records principal, action, resource, and timestamp for every mutating API call
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add an audit logging middleware that logs principal identity, HTTP method, resource path, and timestamp for all state-changing operations. Ship logs to an immutable store.
- **Evidence**: `src/Prowlarr.Http/Authentication/AuthenticationService.cs`, `src/NzbDrone.Common/Instrumentation/NzbDroneLogger.cs`

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: There is only one API key for the entire application. It cannot be selectively revoked for one agent without revoking access for all consumers. Changing the API key requires restarting the application and updating all integrations simultaneously.
- **Gap**: No per-agent identity suspension. Revoking the single API key is an all-or-nothing operation that takes down all integrations.
- **Compensating Controls**:
  - Place an API Gateway in front with per-consumer API keys that can be individually revoked
  - Use a reverse proxy with allowlisting that can block individual agent IPs
- **Remediation Timeline**: 60–90 days (dependent on AUTH-Q1 remediation)
- **Recommendation**: Implement multi-key support where individual keys can be disabled without affecting others. Requires AUTH-Q1 to be resolved first.
- **Evidence**: `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`, `src/Prowlarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: There is no server-side rate limiting on the Prowlarr API. The existing `RateLimitService` is client-side only — it rate-limits Prowlarr's outbound requests to external indexers, not inbound API calls. No API Gateway, WAF, or application-level middleware restricts request rates from consumers.
- **Gap**: A runaway agent loop could overwhelm the application at machine speed. No protection against brute-force API key guessing or denial-of-service from a single consumer.
- **Compensating Controls**:
  - Deploy an API Gateway or reverse proxy with per-client rate limiting (e.g., nginx rate_limit, AWS API Gateway throttling)
  - Add ASP.NET Core rate limiting middleware (`Microsoft.AspNetCore.RateLimiting`)
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add server-side rate limiting middleware. ASP.NET Core 8 has built-in `RateLimiter` middleware that can be configured per-endpoint or globally.
- **Evidence**: `src/NzbDrone.Common/TPL/RateLimitService.cs` (outbound only), `src/NzbDrone.Host/Startup.cs` (no rate limiting middleware)

#### DATA-Q1: Sensitive Data Classification — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — B1 evaluated as RISK-SAFETY
- **Finding**: Stage A = Yes — the system stores sensitive data including API keys, indexer credentials (usernames/passwords), proxy credentials, and SSL certificate passwords. Stage B evaluation: B1 fires (RISK-SAFETY) because `HostConfigResource` returns `ApiKey`, `SslCertPassword`, `ProxyUsername`, and `ProxyPassword` directly in the API response. The mapper in `HostConfigController.cs` maps these sensitive fields without filtering. B2 fires (RISK-SAFETY) because there is no access control differentiation — the same API key grants access to all data including credentials. B3 absent (INFO) — no formal classification metadata.
- **Gap**: Agent-facing API responses include plaintext secrets (API key, proxy password, SSL cert password). No field-level filtering or DTO separation for sensitive vs non-sensitive data in API responses.
- **Compensating Controls**:
  - Add `[JsonIgnore]` attributes to sensitive fields in resource classes, or create separate read-only DTOs that exclude credentials
  - Restrict the `/api/v1/config/host` endpoint to local-only access
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create separate response DTOs for sensitive config endpoints that exclude credential fields. Mark sensitive fields with `[JsonIgnore]` in public-facing resources.
- **Evidence**: `src/Prowlarr.Api.V1/Config/HostConfigResource.cs`, `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The application has comprehensive log cleansing via `CleanseLogMessage.cs` with 40+ regex patterns covering API keys, tokens, passwords, download client credentials, and file path usernames. This is applied to all log outputs (file, console, CLEF, Sentry). However, log cleansing is pattern-based — novel credential formats or user-submitted data not matching existing patterns could leak. Additionally, the redaction patterns are reactive (regex match-and-replace) rather than proactive (allowlist of safe-to-log fields).
- **Gap**: Reactive pattern-based redaction rather than proactive field-allowlisting. No formal guarantee that all PII/credential patterns are covered. New credential formats added by indexer definitions may not be captured by existing regex patterns.
- **Compensating Controls**:
  - Extend CleanseLogMessage patterns when new credential types are added
  - Add structured logging with explicit field allowlists rather than full-message regex scrubbing
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Migrate to a proactive allowlist-based logging model for sensitive contexts. Ensure new indexer definition credential fields are automatically covered by the cleansing pipeline.
- **Evidence**: `src/NzbDrone.Common/Instrumentation/CleanseLogMessage.cs`

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: An OpenAPI 3.0.4 JSON specification exists at `src/Prowlarr.Api.V1/openapi.json`. It is generated via Swashbuckle annotations on the API controllers. The spec documents all 31 API controllers and their operations.
- **Gap**: The spec is committed to the repository but it is unclear if it is auto-generated on each build or manually updated. There is no CI step that validates spec-code synchronization.
- **Compensating Controls**:
  - Add an OpenAPI diff check in CI to detect spec drift
  - Auto-generate the spec as part of the build pipeline
- **Remediation Timeline**: 30 days
- **Recommendation**: Add a CI step that generates the OpenAPI spec and fails if it differs from the committed version, ensuring the spec stays current.
- **Evidence**: `src/Prowlarr.Api.V1/openapi.json`

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The application has a global error pipeline (`ProwlarrErrorPipeline`) that maps exceptions to HTTP status codes and returns structured error bodies: `{ message, description, content }`. FluentValidation errors return as JSON arrays. However, error responses lack a `retryable` indicator or error code classification that would help an agent distinguish transient from terminal failures.
- **Gap**: No retryable/terminal classification in error responses. No machine-readable error codes (only HTTP status codes and free-text messages).
- **Compensating Controls**:
  - Agent-side heuristic: treat 429/503/500 as retryable, 400/401/404/409 as terminal
  - Document error response patterns in agent tool definitions
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a structured error code (e.g., `error_code` field) and `retryable` boolean to error responses. Standardize on a consistent error envelope across all endpoints.
- **Evidence**: `src/Prowlarr.Http/ErrorManagement/ProwlarrErrorPipeline.cs`

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The API is versioned at the URL level (`/api/v1/`). An OpenAPI spec is committed. However, there is no breaking change detection in CI, no consumer-driven contract tests, and no schema registry. The API version has remained at v1 throughout development without formal deprecation or changelog tracking.
- **Gap**: No breaking change detection. No contract testing. Agent tool schemas could break silently if the API response shape changes without version increment.
- **Compensating Controls**:
  - Pin agent tool definitions to specific response fields and add integration tests that validate field presence
  - Add OpenAPI diff tooling to CI
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add an OpenAPI diff tool (e.g., `oasdiff`) to CI that flags breaking changes. Consider consumer-driven contract testing for critical agent-consumed endpoints.
- **Evidence**: `src/Prowlarr.Api.V1/openapi.json`, `azure-pipelines.yml`

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No distributed tracing exists — no OpenTelemetry, no X-Ray, no trace ID propagation, no correlation IDs in request handling. Logging uses NLog with a pipe-delimited format (`date|level|logger|message`) by default. CLEF (JSON) format is available via environment variable but disabled by default. No `request_id` or `correlation_id` is generated or propagated through the request pipeline.
- **Gap**: Cannot trace an agent-initiated request through the system. No structured logging by default. No correlation between related log entries for a single request.
- **Compensating Controls**:
  - Enable CLEF JSON logging via `PROWLARR__LOG__CONSOLEFORMAT=Clef` environment variable
  - Add request correlation middleware that generates a unique ID per request
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add OpenTelemetry instrumentation or at minimum a correlation ID middleware. Enable structured JSON logging by default for machine-parseable log analysis.
- **Evidence**: `src/NzbDrone.Common/Instrumentation/NzbDroneLogger.cs`

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No alerting is configured for API error rates or latency. The application has a custom health check system (`GET /api/v1/health`) that monitors indexer connectivity and system status, but this is application-health focused, not API-performance focused. No CloudWatch alarms, no PagerDuty integration, no SLO-based alerting exists in the codebase.
- **Gap**: No alerting infrastructure for API error rates or latency degradation. If agent traffic causes elevated errors, there is no automated detection.
- **Compensating Controls**:
  - Monitor the health endpoint externally (Uptime Kuma, Healthchecks.io)
  - Deploy external APM tooling (Datadog, New Relic) with alert thresholds
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Integrate with an external monitoring system or add Prometheus metrics export with alert rules for 5xx rates and P99 latency.
- **Evidence**: `src/Prowlarr.Api.V1/Health/HealthController.cs`, `src/NzbDrone.Core/HealthCheck/HealthCheckService.cs`

#### ENG-Q1: Infrastructure Governance — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No infrastructure as code exists in this repository. The application is distributed as self-contained archives (zip/tar.gz) and deployed manually or via community-maintained packages. There is no Terraform, CloudFormation, CDK, Helm chart, or Kubernetes manifest defining the deployment infrastructure.
- **Gap**: No IaC governance. Infrastructure changes (networking, IAM, API gateway) would need to be managed externally. No drift detection, no peer review on infrastructure changes.
- **Compensating Controls**:
  - Define deployment infrastructure externally in a separate IaC repository
  - Use community container images (linuxserver/prowlarr) with IaC-managed orchestration
- **Remediation Timeline**: 90–180 days
- **Recommendation**: Create IaC definitions for the deployment infrastructure — at minimum, define networking, reverse proxy, and access control configuration as code subject to version control and review.
- **Evidence**: Repository root (no IaC files present)

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: A comprehensive CI/CD pipeline exists (Azure Pipelines with 10 stages, including unit tests, integration tests against SQLite and PostgreSQL, SonarCloud analysis). However, there are no API contract tests, no consumer-driven contract testing (Pact), and no OpenAPI spec validation step that would detect breaking API changes before they reach production.
- **Gap**: No API contract testing in CI. Breaking API changes are not automatically detected. Agent tool bindings could break silently.
- **Compensating Controls**:
  - Add OpenAPI spec generation and diff as a CI step
  - Add integration tests that validate API response shapes against expected contracts
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add contract testing (Pact or OpenAPI diff) to the Azure Pipelines build to catch breaking changes before release.
- **Evidence**: `azure-pipelines.yml`, `src/NzbDrone.Integration.Test/`

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The application has a self-update mechanism (`NzbDrone.Update` project) that backs up the current installation before applying updates, enabling rollback to the previous version. However, this is a file-system-level backup/restore — not a deployment platform rollback. There is no blue/green deployment, no canary, no traffic shifting, and no automated rollback triggers.
- **Gap**: Rollback is manual and file-system-based. No deployment platform with automated rollback capability. No health-check-driven automatic rollback.
- **Compensating Controls**:
  - Maintain version-pinned deployments and manual rollback procedures
  - Use container orchestration (Docker/Kubernetes) with automated rollback on health check failure
- **Remediation Timeline**: 90–180 days
- **Recommendation**: Containerize the application and deploy via orchestration that supports automated rollback (Kubernetes rollout undo, ECS rolling update with circuit breaker).
- **Evidence**: `src/NzbDrone.Update/`, `azure-pipelines.yml`

#### ENG-Q5: Encryption at Rest — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The application stores data in SQLite (file-based) or PostgreSQL. No encryption at rest is configured at the application level. SQLite databases are plain files with no encryption. PostgreSQL encryption would depend on the hosting environment. No KMS integration, no application-level field encryption.
- **Gap**: No encryption at rest for the local SQLite database. Credentials stored in the database (indexer passwords, API keys) are accessible to anyone with filesystem access.
- **Compensating Controls**:
  - Deploy on encrypted volumes (EBS encryption, encrypted filesystems)
  - Use PostgreSQL with TDE or on encrypted storage
- **Remediation Timeline**: 30–60 days
- **Recommendation**: For cloud deployments, ensure the underlying storage is encrypted (EBS, encrypted RDS). For self-hosted, consider SQLCipher for SQLite encryption or migrating to PostgreSQL on encrypted storage.
- **Evidence**: `src/NzbDrone.Core/Datastore/` (SQLite/PostgreSQL database access)

#### DATA-Q3: Selective Query Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The API supports page-based offset pagination via `PagingSpec<T>` with `page`, `pageSize`, `sortKey`, and `sortDirection` parameters. Some endpoints support filter parameters. However, there is no cursor-based pagination (offset pagination degrades at scale), no field selection (GraphQL-style), and result size limits are not enforced by default.
- **Gap**: Offset-only pagination degrades at scale. No cursor-based pagination. No field selection to limit payload size.
- **Compensating Controls**:
  - Set reasonable `pageSize` defaults and maximums in agent tool definitions
  - Agent-side filtering of response fields to manage context window size
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add maximum page size enforcement and consider cursor-based pagination for large collections. Document pagination parameters in the OpenAPI spec.
- **Evidence**: `src/NzbDrone.Core/Datastore/PagingSpec.cs`

---

## INFOs — Architecture and Design Inputs

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No idempotency patterns exist in the codebase. Write endpoints (POST, PUT, DELETE) do not support idempotency keys. POST requests will create duplicate resources on retry.
- **Implication**: If agent scope expands to write-enabled, this becomes a BLOCKER. Plan idempotency key support before enabling write operations for agents.
- **Recommendation**: When planning write-enabled agent access, implement idempotency keys for POST endpoints (at minimum for resource creation operations).
- **Evidence**: `src/Prowlarr.Http/REST/RestController.cs`

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: All API responses are JSON (`application/json`). The application uses `System.Text.Json` for serialization with consistent naming conventions. Binary content (torrent files, NZB files) is served via separate download endpoints with appropriate content types.
- **Implication**: JSON format is ideal for agent consumption. No additional parsing logic needed.
- **Recommendation**: No action needed.
- **Evidence**: `src/Prowlarr.Http/`, `src/Prowlarr.Api.V1/openapi.json`

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limit headers are returned by the API (`X-RateLimit-Remaining`, `Retry-After`). No rate limiting documentation exists. The application has no server-side rate limiting (see STATE-Q5).
- **Implication**: Agents cannot self-throttle based on rate limit feedback. Agent tool definitions must include conservative polling intervals.
- **Recommendation**: When rate limiting is implemented (STATE-Q5), include standard rate limit headers in responses.
- **Evidence**: `src/NzbDrone.Host/Startup.cs`

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO (system has write operations but agent scope is read-only)
- **Finding**: No compensation or rollback patterns exist for multi-step operations. The application uses simple CRUD operations without saga patterns or compensating transactions. The only backup/restore is the self-update mechanism (filesystem-level).
- **Implication**: If agent scope expands to write-enabled, this becomes a BLOCKER. Multi-step agent workflows that fail mid-sequence will leave partial state.
- **Recommendation**: When planning write-enabled agent access, implement compensation logic for multi-step operations (e.g., adding an indexer + configuring sync targets).
- **Evidence**: `src/NzbDrone.Core/`

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No optimistic locking or concurrency controls exist. The database uses last-write-wins semantics. No ETag headers, no version fields in entities, no `If-Match` header support. SQLite's file-level locking provides basic serialization but is not a concurrency control mechanism for application-level conflicts.
- **Implication**: If multiple write-enabled agents operate simultaneously, data races will occur. Plan concurrency controls before expanding to write-enabled scope.
- **Recommendation**: Add version fields to entities and ETag support for PUT operations before enabling concurrent write access.
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs`

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits exist. No per-agent spend limits, no maximum records-per-operation caps, no bulk operation safeguards. The API does not restrict the number of operations per session.
- **Implication**: When write-enabled agents are introduced, there is no limit on the blast radius of an agent error.
- **Recommendation**: Plan transaction limit enforcement before expanding to write-enabled agent scope.
- **Evidence**: `src/Prowlarr.Api.V1/`

### AUTH-Q5: Credential Management

- **Severity**: INFO
- **Finding**: Credentials are stored in XML configuration files (`config.xml`) and the SQLite database. The API key is generated at startup and stored in the config file. Indexer credentials (usernames, passwords, API keys for external services) are stored in the database. No external secrets management system is used (no AWS Secrets Manager, no HashiCorp Vault, no Azure Key Vault).
- **Implication**: Credential compromise requires filesystem access. For cloud deployments, consider migrating sensitive configuration to a secrets manager.
- **Recommendation**: For production cloud deployments, integrate with a secrets management system for the master API key and database credentials.
- **Evidence**: `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`

### DATA-Q2: Data Residency and Sovereignty ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO (read-only scope, lower risk profile)
- **Finding**: No data residency requirements are documented or enforced. The application stores data locally (SQLite file or user-configured PostgreSQL). Data residency depends entirely on where the application is deployed. No cross-region replication, no GDPR-specific controls.
- **Implication**: For deployments handling EU user data, ensure the deployment region complies with GDPR. Agent interactions should not transmit indexer credentials to LLM endpoints in other jurisdictions.
- **Recommendation**: Document data residency requirements for production deployments. Ensure agent tool definitions specify which response fields are safe to send to LLM providers.
- **Evidence**: `src/NzbDrone.Core/Datastore/`

### HITL-Q3: Sandbox/Staging Environment

- **Severity**: INFO
- **Finding**: No dedicated sandbox or staging environment is defined in the repository. The application supports a development mode via environment configuration. Docker-compose is not provided. The `.devcontainer/devcontainer.json` provides a development container but not a staging equivalent.
- **Implication**: Agent testing must be done against a local development instance. No production-equivalent staging with realistic data shapes exists.
- **Recommendation**: Create a Docker Compose environment with seed data for agent integration testing.
- **Evidence**: `.devcontainer/devcontainer.json`, `azure-pipelines.yml`

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality metrics, completeness scores, or freshness SLAs exist. The health check system monitors indexer connectivity status (available/unavailable/disabled) but does not track data quality dimensions.
- **Implication**: Agents consuming indexer data have no signal about data freshness or completeness.
- **Recommendation**: Consider adding freshness metadata to API responses (e.g., `last_sync_time` for indexer data).
- **Evidence**: `src/NzbDrone.Core/HealthCheck/`

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: PASS (no finding)
- **Finding**: Prowlarr exposes a well-documented REST API at `/api/v1/` with 31 controllers covering all application functionality. An OpenAPI 3.0.4 specification is committed at `src/Prowlarr.Api.V1/openapi.json`. No direct database access or file-based exchange is required for integration.
- **Gap**: None
- **Recommendation**: None
- **Evidence**: `src/Prowlarr.Api.V1/openapi.json`, `src/Prowlarr.Api.V1/` (31 controller files)

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: OpenAPI 3.0.4 spec exists and is committed. Generated via Swashbuckle. No CI validation of spec-code synchronization.
- **Gap**: No automated spec drift detection in CI.
- **Recommendation**: Add OpenAPI diff validation to CI.
- **Evidence**: `src/Prowlarr.Api.V1/openapi.json`

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: Global error pipeline maps exceptions to HTTP codes with structured JSON bodies. Lacks `retryable` indicator and machine-readable error codes.
- **Gap**: No retryable/terminal classification. No standardized error codes.
- **Recommendation**: Add error code and retryable boolean to error responses.
- **Evidence**: `src/Prowlarr.Http/ErrorManagement/ProwlarrErrorPipeline.cs`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No idempotency support. Write endpoints lack idempotency keys.
- **Gap**: POST requests create duplicates on retry.
- **Recommendation**: Plan idempotency key support for write-enabled scope expansion.
- **Evidence**: `src/Prowlarr.Http/REST/RestController.cs`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: All API responses are JSON. Binary content served via separate endpoints.
- **Gap**: None
- **Recommendation**: No action needed.
- **Evidence**: `src/Prowlarr.Api.V1/openapi.json`

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
- **Finding**: No rate limit headers returned. No rate limiting documentation.
- **Gap**: Agents cannot self-throttle.
- **Recommendation**: Include rate limit headers when rate limiting is implemented.
- **Evidence**: `src/NzbDrone.Host/Startup.cs`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: Single shared API key for all consumers. No per-agent identity or principal attribution.
- **Gap**: Cannot distinguish which agent made a call. No per-agent credentials.
- **Recommendation**: Implement multiple API key support with principal labels and attribution in audit logs.
- **Evidence**: `src/Prowlarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: Binary authentication — valid API key grants full access to all operations.
- **Gap**: No least-privilege model. Cannot scope down agent access.
- **Recommendation**: Implement RBAC with at least read-only and admin roles.
- **Evidence**: `src/Prowlarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization. Authenticated callers can perform any HTTP method on any resource.
- **Gap**: Cannot restrict agent to read operations only at application level.
- **Recommendation**: Add authorization policy distinguishing read from write operations.
- **Evidence**: `src/NzbDrone.Host/Startup.cs`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Archetype calibration — stateful-crud evaluates normally, but this is extended for non-orchestrator archetypes without downstream service calls.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: Credentials stored in XML config files and SQLite database. No external secrets management.
- **Gap**: No secrets manager integration.
- **Recommendation**: Integrate with secrets management for cloud deployments.
- **Evidence**: `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Auth events logged locally. No immutable audit trail for API operations.
- **Gap**: No tamper-evident audit logs. No principal attribution in API operation logs.
- **Recommendation**: Add audit middleware and ship to immutable log store.
- **Evidence**: `src/Prowlarr.Http/Authentication/AuthenticationService.cs`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: Single API key cannot be selectively revoked per agent.
- **Gap**: All-or-nothing key revocation.
- **Recommendation**: Implement multi-key support with per-key disable capability.
- **Evidence**: `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No compensation or rollback for multi-step operations.
- **Gap**: Partial state on mid-sequence failure.
- **Recommendation**: Plan compensation logic before write-enabled scope expansion.
- **Evidence**: `src/NzbDrone.Core/`

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
- **Finding**: No optimistic locking. Last-write-wins semantics.
- **Gap**: Data races possible with concurrent write access.
- **Recommendation**: Add version fields and ETag support before write-enabled scope.
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has external dependencies (calls other services or external APIs)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No server-side rate limiting on API endpoints. Only outbound rate limiting to external indexers.
- **Gap**: No protection against agent traffic overwhelming the application.
- **Recommendation**: Add ASP.NET Core rate limiting middleware.
- **Evidence**: `src/NzbDrone.Common/TPL/RateLimitService.cs`, `src/NzbDrone.Host/Startup.cs`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits.
- **Gap**: No blast radius constraints for agent operations.
- **Recommendation**: Plan transaction limits before write-enabled scope.
- **Evidence**: `src/Prowlarr.Api.V1/`

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
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: INFO
- **Finding**: No dedicated staging environment. Dev container available for development.
- **Gap**: No production-equivalent testing environment for agents.
- **Recommendation**: Create Docker Compose environment with seed data for agent testing.
- **Evidence**: `.devcontainer/devcontainer.json`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — B1 evaluated as RISK-SAFETY (sensitive fields exposed in API responses)
- **Finding**: API exposes plaintext secrets (API key, proxy password, SSL cert password) in HostConfigResource.
- **Gap**: No field-level filtering for sensitive data in API responses.
- **Recommendation**: Create separate DTOs excluding credentials. Add `[JsonIgnore]` to sensitive fields.
- **Evidence**: `src/Prowlarr.Api.V1/Config/HostConfigResource.cs`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No data residency controls. Data stored locally, residency depends on deployment.
- **Gap**: No documented residency requirements.
- **Recommendation**: Document residency requirements for production deployments.
- **Evidence**: `src/NzbDrone.Core/Datastore/`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK-QUALITY
- **Finding**: Offset pagination with page/pageSize/sort. No cursor-based pagination or field selection.
- **Gap**: Offset pagination degrades at scale. No field selection.
- **Recommendation**: Add max page size enforcement and consider cursor-based pagination.
- **Evidence**: `src/NzbDrone.Core/Datastore/PagingSpec.cs`

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
- **Finding**: Comprehensive 40+ regex pattern redaction applied to all log outputs. Reactive pattern-based approach rather than proactive allowlisting.
- **Gap**: Novel credential formats may not be captured. Reactive vs proactive model.
- **Recommendation**: Migrate to allowlist-based logging for sensitive contexts.
- **Evidence**: `src/NzbDrone.Common/Instrumentation/CleanseLogMessage.cs`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics or freshness SLAs.
- **Gap**: No data quality signals for agent consumers.
- **Recommendation**: Add freshness metadata to API responses.
- **Evidence**: `src/NzbDrone.Core/HealthCheck/`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: API versioned at URL level (/api/v1/). OpenAPI spec committed. No breaking change detection or contract testing in CI.
- **Gap**: No automated breaking change detection. Agent tools could break silently.
- **Recommendation**: Add OpenAPI diff tooling and contract tests to CI.
- **Evidence**: `src/Prowlarr.Api.V1/openapi.json`, `azure-pipelines.yml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Field names are human-readable and semantically meaningful (e.g., `indexerName`, `enableRss`, `baseUrl`, `configContract`). No legacy abbreviations or coded fields requiring data dictionaries.
- **Implication**: Agent LLM reasoning can work directly with field names without translation.
- **Recommendation**: No action needed.
- **Evidence**: `src/Prowlarr.Api.V1/openapi.json`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal data catalog or metadata layer. The OpenAPI spec serves as the primary API documentation. No Glue Data Catalog, DataHub, or equivalent.
- **Implication**: Agent tool builders must rely on OpenAPI spec and code inspection for understanding data semantics.
- **Recommendation**: Enhance OpenAPI spec descriptions for agent tool generation.
- **Evidence**: `src/Prowlarr.Api.V1/openapi.json`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: No distributed tracing. NLog with pipe-delimited format by default. Optional CLEF JSON. No correlation IDs.
- **Gap**: Cannot trace agent-initiated requests. No structured logging by default.
- **Recommendation**: Add OpenTelemetry and correlation ID middleware. Enable structured JSON logging.
- **Evidence**: `src/NzbDrone.Common/Instrumentation/NzbDroneLogger.cs`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: No alerting configured for API error rates or latency.
- **Gap**: No automated detection of API degradation from agent traffic.
- **Recommendation**: Add metrics export and alert thresholds.
- **Evidence**: `src/Prowlarr.Api.V1/Health/HealthController.cs`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Always evaluated as INFO
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance
- **Severity**: RISK-QUALITY
- **Finding**: No IaC in repository. Application distributed as self-contained archives.
- **Gap**: No IaC governance for deployment infrastructure.
- **Recommendation**: Create IaC for deployment infrastructure externally.
- **Evidence**: Repository root (no IaC files)

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive CI/CD pipeline. No API contract testing or breaking change detection.
- **Gap**: Breaking API changes not caught in CI.
- **Recommendation**: Add contract testing to CI pipeline.
- **Evidence**: `azure-pipelines.yml`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: File-system-level backup/restore for self-updates. No platform-level rollback.
- **Gap**: Manual rollback only. No automated health-check-driven rollback.
- **Recommendation**: Containerize and deploy with orchestration supporting automated rollback.
- **Evidence**: `src/NzbDrone.Update/`, `azure-pipelines.yml`

#### ENG-Q4: API Test Coverage
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Always evaluated (but INFO for stateless-utility)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### ENG-Q5: Encryption at Rest
- **Severity**: RISK-QUALITY
- **Finding**: SQLite plain files. No application-level encryption. Credentials accessible with filesystem access.
- **Gap**: No encryption at rest for local data.
- **Recommendation**: Deploy on encrypted volumes or use SQLCipher.
- **Evidence**: `src/NzbDrone.Core/Datastore/`

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `src/Prowlarr.Http/Authentication/ApiKeyAuthenticationHandler.cs` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q7 |
| `src/Prowlarr.Http/Authentication/AuthenticationService.cs` | AUTH-Q6 |
| `src/Prowlarr.Http/Authentication/UiAuthorizationHandler.cs` | AUTH-Q3 |
| `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` | AUTH-Q1, AUTH-Q5, AUTH-Q7, DATA-Q1 |
| `src/NzbDrone.Host/Startup.cs` | AUTH-Q2, AUTH-Q3, STATE-Q5, API-Q8 |
| `src/Prowlarr.Http/ErrorManagement/ProwlarrErrorPipeline.cs` | API-Q3 |
| `src/Prowlarr.Http/REST/RestController.cs` | API-Q4 |
| `src/Prowlarr.Api.V1/Config/HostConfigResource.cs` | DATA-Q1 |
| `src/NzbDrone.Common/Instrumentation/NzbDroneLogger.cs` | AUTH-Q6, OBS-Q1 |
| `src/NzbDrone.Common/Instrumentation/CleanseLogMessage.cs` | DATA-Q6 |
| `src/NzbDrone.Common/TPL/RateLimitService.cs` | STATE-Q5 |
| `src/NzbDrone.Core/Datastore/BasicRepository.cs` | STATE-Q3 |
| `src/NzbDrone.Core/Datastore/PagingSpec.cs` | DATA-Q3 |
| `src/Prowlarr.Api.V1/Health/HealthController.cs` | OBS-Q2 |
| `src/NzbDrone.Core/HealthCheck/HealthCheckService.cs` | OBS-Q2, DATA-Q7 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `src/Prowlarr.Api.V1/openapi.json` | API-Q1, API-Q2, API-Q5, DISC-Q1, DISC-Q2, DISC-Q3 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `azure-pipelines.yml` | ENG-Q2, ENG-Q3, DISC-Q1 |
| `.github/workflows/ci.yml` | ENG-Q2 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `.devcontainer/devcontainer.json` | HITL-Q3 |
