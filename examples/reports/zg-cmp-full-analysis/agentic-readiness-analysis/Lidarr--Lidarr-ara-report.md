# Agentic Readiness Analysis Report

**Target**: Lidarr (Music collection manager, *arr suite)
**Date**: 2025-07-17
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**Repository Type**: monorepo
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: csharp, media, desktop
**Context**: Music collection manager (*arr suite). Self-hosted media management application built with ASP.NET Core (.NET 8) and a React frontend. Manages music artists, albums, tracks, and associated files using SQLite/PostgreSQL. Exposes a REST API (v1) with OpenAPI specification and real-time updates via SignalR.

**Archetype Justification**: Lidarr uses SQLite/PostgreSQL databases (persistent state), exposes full CRUD endpoints for Artists, Albums, Tracks, and TrackFiles, and manages entity lifecycles with status fields. It is not an orchestrator (does not coordinate 3+ downstream services in request path), not event-driven-only (has a synchronous REST API), and not a data-gateway (has substantial business logic beyond querying).

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 2 | **RISK-SAFETY**: 8 | **RISK-QUALITY**: 14 | **INFOs**: 18

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days. The two BLOCKERs (AUTH-Q1: Machine Identity Authentication and DATA-Q1: Sensitive Data Classification) must be resolved before any agent integration. Once BLOCKERs are cleared, the 8 RISK-SAFETY findings will place this system at **Pilot-Ready (Safety Concerns)**, requiring supervised pilot with elevated safety oversight.

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 2 |
| RISK-SAFETY | 8 |
| RISK-QUALITY | 14 |
| INFO | 18 |
| N/A | 0 |
| Not Evaluated (extended) | 1 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 18
**Extended Questions Not Triggered**: 1 (STATE-Q7)
**Questions N/A (repo_type: monorepo)**: 0
**Service Archetype**: stateful-crud (auto-detected)

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: Lidarr supports API key authentication via `ApiKeyAuthenticationHandler.cs`. The API key is passed as `X-Api-Key` header, `apikey` query parameter, or `Authorization: Bearer` header. However, Lidarr uses a **single shared API key** for all consumers. The authenticated principal is recorded only as a generic claim `ApiKey=true` with no identity attribution. There is no mechanism to distinguish which agent or consumer made a request — all API key holders share the same identity.
- **Gap**: No per-agent identity. No principal attribution in audit logs. A single API key is shared across all consumers. The `ClaimsIdentity` created in `ApiKeyAuthenticationHandler.cs` contains only `new Claim("ApiKey", "true")` — no consumer-specific identifier.
- **Remediation**:
  - **Immediate**: Implement a multi-key authentication scheme that maps distinct API keys to named principals (e.g., `agent-lidarr-reader`, `frontend-ui`). Each key should generate a `ClaimsIdentity` with the principal name included.
  - **Target State**: Each agent or integration has its own API key with a named identity. Audit logs record the specific principal for every request.
  - **Estimated Effort**: Medium (2–4 weeks)
  - **Dependencies**: AUTH-Q6 (audit logging must record the new principal field)
- **Evidence**: `src/Lidarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (ApiKey property), `src/Lidarr.Http/Authentication/AuthenticationBuilderExtensions.cs`

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: Lidarr stores sensitive data including user credentials (username, hashed password, salt in `Users` table via `UserRepository.cs`), API keys (in XML config file via `ConfigFileProvider.cs`), and download client credentials (stored in provider settings in the database). There is no data classification system — no field-level tags, no sensitivity labels, no access controls distinguishing sensitive fields from non-sensitive ones. The `UserService.cs` stores PBKDF2-hashed passwords with salts, but no field-level encryption or classification metadata exists.
- **Gap**: No data classification tags on any data store. No field-level access controls preventing an agent from reading user credential hashes, API keys, or download client passwords. No PII detection or data classification tooling configured.
- **Remediation**:
  - **Immediate**: Create a data classification inventory documenting all sensitive fields (Users table credentials, API keys, download client credentials, indexer credentials). Implement field-level filtering in API responses to exclude sensitive fields from agent-accessible endpoints.
  - **Target State**: All sensitive data fields are classified and tagged. API responses to agent identities exclude or redact credential fields. Field-level access controls enforced.
  - **Estimated Effort**: Medium (3–6 weeks)
  - **Dependencies**: AUTH-Q1 (need per-agent identity before field-level access controls can be scoped per consumer)
- **Evidence**: `src/NzbDrone.Core/Authentication/UserService.cs`, `src/NzbDrone.Core/Authentication/UserRepository.cs`, `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (ApiKey, PostgresPassword properties)

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Lidarr uses a single API key that grants full access to all endpoints. There is no role-based access control, no permission scoping, and no mechanism to grant an agent read-only access to specific resources. The `ApiKeyAuthenticationHandler.cs` validates the key and creates a principal with a single claim `ApiKey=true`. The fallback authorization policy in `Startup.cs` requires authentication but does not check specific permissions.
- **Gap**: No scoped permissions. A single API key grants unrestricted access to all 100+ API endpoints including destructive operations (DELETE artists, purge queue, reset API key).
- **Compensating Controls**:
  - Deploy a reverse proxy (e.g., nginx, Caddy) in front of Lidarr that restricts the agent to GET-only methods on specific URL paths.
  - Use network-level controls to limit agent access to specific endpoints.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement role-based API key scoping — at minimum, a read-only role that restricts access to GET endpoints only.
- **Evidence**: `src/Lidarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/NzbDrone.Host/Startup.cs` (FallbackPolicy)

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Lidarr has no action-level authorization. Once authenticated via API key, a consumer can perform any operation — read, create, update, or delete — on any resource type. There are no ABAC policies, no fine-grained RBAC, and no per-action permission checks in middleware or controllers. The `RestController.cs` validates input but does not check authorization per action.
- **Gap**: No action-level authorization. An agent authenticated via API key can delete artists, modify albums, cancel downloads, and reset the API key — all with the same credential.
- **Compensating Controls**:
  - Use a reverse proxy to enforce method-level restrictions (allow GET, deny POST/PUT/DELETE).
  - Wrap Lidarr API access in a custom gateway that enforces action-level policies.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement action-level authorization policies per API key role (e.g., `canRead`, `canWrite`, `canDelete`).
- **Evidence**: `src/Lidarr.Http/REST/RestController.cs`, `src/Lidarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`

#### AUTH-Q6: Immutable Audit Logging — RISK-SAFETY ⚡

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: `AuthenticationService.cs` logs authentication events (success, failure, unauthorized, logout) via NLog to the `Auth` logger, including IP address and username. The `LoggingMiddleware.cs` logs HTTP requests with method, path, status code, and duration. However, these logs are written to local files via NLog and optionally to a SQLite/PostgreSQL log database via `DatabaseTarget.cs`. There is no immutable or tamper-evident log storage — log files can be modified or deleted by anyone with filesystem access.
- **Gap**: Logs are not immutable. No tamper-evident storage. No CloudTrail equivalent. Log database records can be deleted (the `LogRepository` inherits from `BasicRepository` which includes `Delete` and `Purge` methods).
- **Compensating Controls**:
  - Forward NLog output to an external SIEM or immutable log store (e.g., syslog to a remote server — Lidarr supports syslog via `SyslogServer` config).
  - Enable the syslog configuration to ship logs to a centralized, append-only log aggregator.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure syslog forwarding to an immutable log store. Add the authenticated principal identity (once AUTH-Q1 is resolved) to all API request log entries.
- **Evidence**: `src/Lidarr.Http/Authentication/AuthenticationService.cs`, `src/Lidarr.Http/Middleware/LoggingMiddleware.cs`, `src/NzbDrone.Core/Instrumentation/DatabaseTarget.cs`, `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (SyslogServer property)

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Lidarr has a `ResetApiKeyCommand` that regenerates the API key (`ConfigFileProvider.Execute(ResetApiKeyCommand)`). However, since there is only one API key, resetting it disconnects ALL consumers — including the web UI and any other integrations. There is no mechanism to suspend a single agent identity without affecting other consumers.
- **Gap**: Cannot suspend an individual agent identity. The only revocation mechanism (API key reset) is a nuclear option that disconnects all consumers.
- **Compensating Controls**:
  - Use a reverse proxy with per-consumer API keys that can be individually revoked at the proxy layer.
  - Implement an API gateway that maps multiple external keys to the single Lidarr key, enabling per-consumer revocation.
- **Remediation Timeline**: 60–90 days (depends on AUTH-Q1 multi-key implementation)
- **Recommendation**: Implement multi-key support so individual keys can be disabled without affecting other consumers.
- **Evidence**: `src/NzbDrone.Core/Configuration/ResetApiKeyCommand.cs`, `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (Execute method)

#### STATE-Q1: Compensation and Rollback — RISK-SAFETY ⚡

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: `BasicRepository.cs` uses database transactions for `InsertMany` operations (`conn.BeginTransaction(IsolationLevel.ReadCommitted)`). However, there are no saga patterns, no compensation logic, and no explicit undo endpoints. Multi-step operations like adding an artist (which creates the artist record, scans for existing files, triggers metadata refresh, and initiates indexer search) have no rollback if an intermediate step fails. The `CommandController` allows canceling queued commands but not reversing completed ones.
- **Gap**: No compensation or rollback for multi-step operations. No undo endpoints. Transaction support limited to single-repository batch operations.
- **Compensating Controls**:
  - For a read-only agent scope, this is less critical since the agent will not initiate write operations. The risk applies to future write-enabled scope expansion.
  - Monitor command completion status via the Command API to detect failed multi-step operations.
- **Remediation Timeline**: 90–180 days
- **Recommendation**: Implement compensating actions for critical multi-step workflows (e.g., artist deletion with file cleanup). Add explicit undo/rollback endpoints for reversible operations.
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs` (InsertMany transaction), `src/Lidarr.Api.V1/Commands/CommandController.cs`

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Lidarr uses Polly `ResiliencePipeline` with retry strategy in `BasicRepository.cs` for SQLite busy errors (3 retries with exponential backoff and jitter). However, Lidarr makes HTTP calls to external services (indexers like Newznab/Torznab, download clients like SABnzbd/Transmission, metadata sources, notification services) and there are no circuit breakers configured for these external dependency calls. The `HttpIndexerBase`, download client base classes, and notification services make HTTP calls without circuit breaker protection.
- **Gap**: No circuit breakers for external HTTP calls to indexers, download clients, or notification services. Only SQLite busy retry logic exists. A failing external service could cause cascading timeouts.
- **Compensating Controls**:
  - Lidarr has status tracking for indexers (`IndexerStatusService`) and download clients (`DownloadClientStatusService`) that mark providers as unavailable after failures — this is a basic form of circuit breaking at the application level.
  - External service failures primarily affect background tasks, not the REST API surface agents would consume.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add Polly circuit breaker policies to HTTP client calls for indexers, download clients, and metadata sources.
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs` (RetryStrategy), `src/NzbDrone.Core/Indexers/HttpIndexerBase.cs`, `src/NzbDrone.Core/Download/DownloadClientBase.cs`

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No rate limiting middleware is configured in `Startup.cs`. The ASP.NET Core pipeline includes authentication, authorization, response compression, and custom middleware (logging, caching, versioning) but no rate limiting. There is no API Gateway, WAF, or application-level throttling. The CORS policy allows any origin with any method (`AllowAnyOrigin().AllowAnyMethod().AllowAnyHeader()`), which combined with no rate limits means an agent loop could overwhelm the application.
- **Gap**: No rate limiting at any layer — no middleware, no API Gateway, no WAF. An agent making rapid API calls could exhaust SQLite connections and degrade the application.
- **Compensating Controls**:
  - Deploy a reverse proxy with rate limiting in front of Lidarr (e.g., nginx `limit_req_zone`).
  - Configure agent-side rate limiting in the agent orchestration layer.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add ASP.NET Core rate limiting middleware (`Microsoft.AspNetCore.RateLimiting`, available in .NET 7+). Define per-client rate limits using the API key as the partition key.
- **Evidence**: `src/NzbDrone.Host/Startup.cs` (no rate limiting middleware in pipeline)

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: `AuthenticationService.cs` logs IP addresses and usernames in plain text: `Auth-Failure ip {0} username '{1}'`, `Auth-Success ip {0} username '{1}'`, `Auth-Unauthorized ip {0} url '{1}'`. `LoggingMiddleware.cs` logs the remote IP and User-Agent header for every request. The `CleanseLogMessage` class exists in the codebase (referenced in `DatabaseTarget.cs`), but it is not applied to auth logs or HTTP request logs. There is no PII masking, no log scrubbing middleware, and no filtering of sensitive data from log output.
- **Gap**: IP addresses and usernames logged in plain text. No PII redaction in auth logs or HTTP request logs. `CleanseLogMessage` exists but is not consistently applied across all log paths.
- **Compensating Controls**:
  - Configure NLog rules to filter or mask sensitive fields before writing to log targets.
  - Use syslog forwarding to a centralized system that applies PII redaction.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Apply `CleanseLogMessage` consistently to all log paths. Mask IP addresses in auth logs (e.g., `192.168.x.x`). Exclude usernames from INFO-level logs.
- **Evidence**: `src/Lidarr.Http/Authentication/AuthenticationService.cs` (LogFailure, LogSuccess, LogUnauthorized), `src/Lidarr.Http/Middleware/LoggingMiddleware.cs` (GetOrigin)

### RISK-QUALITY — Address as Capacity Allows

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: `LidarrErrorPipeline.cs` returns `ErrorModel` with `Message`, `Description`, and `Content` fields as JSON. The pipeline differentiates error types: `ApiException`, `ValidationException`, `NzbDroneClientException`, `ModelNotFoundException`, `ModelConflictException`, and `SQLiteException` — each mapped to appropriate HTTP status codes (400, 404, 409, 500). `ValidationException` returns `FluentValidation` error objects directly.
- **Gap**: No structured error codes (only HTTP status codes). No `retryable` field or error category to help agents distinguish retriable from terminal errors. No consistent error code enumeration across error types. Error `Description` includes full stack trace, which is verbose and not agent-friendly.
- **Compensating Controls**:
  - Agent can use HTTP status codes for basic classification (4xx = terminal, 5xx = retriable).
  - Wrap Lidarr API calls in an agent-side error classifier that maps status codes to retry decisions.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a structured `errorCode` field and `retryable` boolean to `ErrorModel`. Define an error code enumeration (e.g., `VALIDATION_ERROR`, `NOT_FOUND`, `CONFLICT`, `DATABASE_BUSY`, `INTERNAL_ERROR`).
- **Evidence**: `src/Lidarr.Http/ErrorManagement/LidarrErrorPipeline.cs`, `src/Lidarr.Http/ErrorManagement/ErrorModel.cs`

#### API-Q6: Asynchronous Operation Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Lidarr has a `CommandController` that supports asynchronous operations: `POST /api/v1/command` starts a command and returns `201 Created` with the command ID. `GET /api/v1/command` lists all commands with their status (`Queued`, `Started`, `Completed`, `Failed`). Individual commands can be retrieved by ID via `GET /api/v1/command/{id}`. SignalR provides real-time updates for command status changes via `CommandUpdatedEvent`. However, there is no explicit polling endpoint with `Retry-After` headers, and command results are not structured for agent consumption (no estimated completion time, no progress percentage in the API response).
- **Gap**: Async command pattern exists but lacks agent-friendly metadata (estimated completion time, progress percentage, `Retry-After` headers). Agents must poll or subscribe to SignalR for status updates.
- **Compensating Controls**:
  - Agent can poll `GET /api/v1/command/{id}` at regular intervals to check command status.
  - Agent can subscribe to SignalR for real-time command updates.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `Retry-After` headers to in-progress command responses. Add `progress` and `estimatedCompletionTime` fields to `CommandResource`.
- **Evidence**: `src/Lidarr.Api.V1/Commands/CommandController.cs`, `src/Lidarr.Api.V1/Commands/CommandResource.cs`

#### AUTH-Q5: Credential Management — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The API key is generated as a GUID (`Guid.NewGuid().ToString().Replace("-", "")`) in `ConfigFileProvider.cs` and stored in an XML configuration file on the local filesystem. PostgreSQL credentials (host, user, password) are stored in the same XML config file or passed via environment variables. There is no integration with any secrets management system (no AWS Secrets Manager, no HashiCorp Vault, no Azure Key Vault). The API key can be reset via `ResetApiKeyCommand` but there is no automatic rotation.
- **Gap**: Credentials stored in plain-text XML config file. No secrets management integration. No automatic credential rotation. PostgreSQL password in config file or environment variable.
- **Compensating Controls**:
  - Use environment variables for PostgreSQL credentials instead of the config file (Lidarr supports `Lidarr__Postgres__*` env vars).
  - Restrict filesystem permissions on the Lidarr config directory.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Integrate with a secrets manager for production deployments. Implement API key rotation schedule.
- **Evidence**: `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (ApiKey property, GenerateApiKey method, PostgresPassword property)

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No Docker Compose file exists for local testing. No sandbox or staging environment configuration found. The `build.sh` script supports local development builds. The `azure-pipelines.yml` CI pipeline runs unit, integration, and automation tests across multiple platforms (Windows, Mac, Linux, FreeBSD) with both SQLite and PostgreSQL databases — but these are CI environments, not persistent staging environments agents can test against.
- **Gap**: No sandbox or staging environment with production-equivalent data for agent testing. No seed data scripts. No synthetic data generators.
- **Compensating Controls**:
  - Deploy a separate Lidarr instance with a test music library for agent development and testing.
  - Use the integration test infrastructure as a template for creating a staging environment.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a Docker Compose configuration for local agent testing with seed data. Publish a test database with sample artist/album/track data.
- **Evidence**: `azure-pipelines.yml` (CI test stages), `build.sh`

#### DATA-Q5: Temporal Metadata and Freshness — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Lidarr stores timestamps in UTC via `DapperUtcConverter` which ensures `DateTime.SpecifyKind(value, DateTimeKind.Utc)` on read and `value.ToUniversalTime()` on write. The SQLite connection is configured with `DateTimeKind = DateTimeKind.Utc`. Database models include temporal fields like `DateAdded` on albums and `DateAdded`/`Modified` on track files. PostgreSQL migration `061_postgres_update_timestamp_columns_to_with_timezone.cs` ensures timestamp columns use timezone-aware types.
- **Gap**: No freshness signaling in API responses — no `Cache-Control` headers, no `X-Data-Age` header, no `last_refreshed` field. Agents cannot determine if data returned is current or stale. No `consistency_level` indicator.
- **Compensating Controls**:
  - Agent can check `DateAdded`/`Modified` fields on entities to assess data age.
  - Agent can use the `LastInfoSync` field on artist metadata to determine when data was last refreshed from external sources.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `Cache-Control` and `Last-Modified` headers to GET responses. Include a `lastRefreshed` field in API responses for entities synced from external metadata sources.
- **Evidence**: `src/NzbDrone.Core/Datastore/Converters/UtcConverter.cs`, `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` (DateTimeKind.Utc)

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The API is versioned as v1 (`/api/v1/`) via `VersionedApiControllerAttribute`. The OpenAPI specification is versioned (`"version": "1.0.0"`). Database schemas are managed via FluentMigrator with 80+ numbered migrations (`000_database_engine_version_check.cs` through `080_update_redacted_baseurl.cs`). The CI pipeline includes an `Api_Docs` job that auto-generates and commits updated `openapi.json`. However, there is no breaking change detection in CI — no `buf breaking`, no OpenAPI diff tool, no consumer-driven contract tests.
- **Gap**: No breaking change detection for the API schema. No consumer-driven contract testing (no Pact tests). Changes to the OpenAPI spec are committed automatically but not validated against previous versions. An agent's tool bindings could break silently after an API update.
- **Compensating Controls**:
  - The API versioning (v1) provides a stable URL namespace.
  - The automated OpenAPI generation ensures the spec stays in sync with the codebase.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenAPI diff validation to the CI pipeline (e.g., `openapi-diff` or `oasdiff`) to detect breaking changes before merge. Consider consumer-driven contract tests for agent tool definitions.
- **Evidence**: `src/Lidarr.Api.V1/openapi.json`, `azure-pipelines.yml` (Api_Docs job), `src/NzbDrone.Core/Datastore/Migration/`

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Lidarr uses NLog for logging. `LoggingMiddleware.cs` assigns a sequential `ApiRequestSequenceID` to each request and logs it with method, path, status code, and duration. The `DatabaseTarget.cs` writes logs to a dedicated log database (SQLite or PostgreSQL) with Message, Time, Logger, Exception, ExceptionType, and Level fields. However, there is no distributed tracing (no OpenTelemetry, no X-Ray), no `traceparent` header propagation, and logs are not structured JSON — they use NLog text formatting.
- **Gap**: No distributed tracing. No trace ID propagation. Logs are not structured JSON format. The `ApiRequestSequenceID` is a local counter, not a globally unique correlation ID. Cannot trace a request across the Lidarr process boundary.
- **Compensating Controls**:
  - The `ApiRequestSequenceID` provides basic request correlation within the Lidarr process.
  - NLog can be configured with a JSON layout for structured logging without code changes.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add OpenTelemetry instrumentation for ASP.NET Core. Configure NLog with JSON layout. Propagate `traceparent` headers and include trace IDs in API responses.
- **Evidence**: `src/Lidarr.Http/Middleware/LoggingMiddleware.cs`, `src/NzbDrone.Core/Instrumentation/DatabaseTarget.cs`

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Lidarr integrates with Sentry for error tracking — `ReconfigureSentry.cs` configures the Sentry SDK with database version, migration info, and branch. The `azure-pipelines.yml` uploads source maps to Sentry and creates releases with deployment environment tags. Sentry provides error alerting capabilities. However, there are no explicit alerting thresholds configured for error rates or latency. No health check endpoints with latency monitoring. The `HealthCheckController` exists but tracks application-level health, not API performance.
- **Gap**: No explicit alerting thresholds for API error rates or latency. Sentry captures errors but does not alert on degradation patterns. No SLO-based alerting.
- **Compensating Controls**:
  - Sentry provides basic error alerting out of the box.
  - Configure Sentry alert rules for error rate thresholds on agent-consumed endpoints.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure Sentry alert rules for error rate and latency thresholds on the `/api/v1/` endpoints. Add health check endpoints with latency metrics.
- **Evidence**: `src/NzbDrone.Core/Instrumentation/ReconfigureSentry.cs`, `azure-pipelines.yml` (Sentry source map upload)

#### ENG-Q1: Infrastructure Governance — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No Infrastructure as Code (IaC) found in the repository. No Terraform, CloudFormation, CDK, Helm charts, or Kustomize configurations. Lidarr is a self-hosted desktop/server application distributed as platform-specific packages (Windows installer, macOS app, Linux tarballs). Infrastructure is managed by end users on their own systems.
- **Gap**: No IaC governance because there is no cloud infrastructure to govern. The application is self-hosted. API gateway, IAM roles, secrets management, and network configuration are the responsibility of the user's deployment environment.
- **Compensating Controls**:
  - For users deploying Lidarr in container environments, the community Docker images (maintained separately) provide infrastructure definitions.
  - Document recommended infrastructure configurations for agent integration (reverse proxy setup, network policies).
- **Remediation Timeline**: 60–90 days (depends on target deployment model)
- **Recommendation**: Provide reference infrastructure configurations (Docker Compose, Helm chart) for production deployments with agent integration. Include reverse proxy, rate limiting, and TLS configuration.
- **Evidence**: No IaC files found. `distribution/` directory contains only platform-specific packaging (debian, osx, windows).

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Lidarr has a comprehensive CI/CD pipeline via `azure-pipelines.yml` with multiple stages: Build Backend (multi-platform), Build Frontend, Unit Tests (SQLite and PostgreSQL on multiple OSes), Integration Tests (native + Docker + PostgreSQL), Automation Tests (UI tests), and Analyze (SonarCloud for both backend and frontend, linting). The pipeline auto-generates `openapi.json` and creates PRs for API doc updates. However, there are no API contract tests (no Pact, no OpenAPI validation, no schema comparison).
- **Gap**: No API contract testing in CI. No breaking change detection for the OpenAPI spec. The API docs job generates and commits the spec but does not validate it against the previous version.
- **Compensating Controls**:
  - Integration tests cover API behavior implicitly.
  - SonarCloud analysis catches code quality issues.
  - The automated openapi.json generation ensures the spec reflects the current codebase.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add an OpenAPI diff step to the CI pipeline that fails on breaking changes. Add contract tests for critical agent-consumed endpoints.
- **Evidence**: `azure-pipelines.yml` (all stages), `.github/workflows/ci.yml`

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Lidarr is distributed as self-contained packages (Windows installers, macOS apps, Linux tarballs). The `NzbDrone.Update` project handles automatic updates with a built-in updater. However, there is no automated rollback mechanism — if an update breaks agent-facing APIs, users must manually restore from backup. The database migration system (FluentMigrator) does not support reverse migrations. The `DatabaseRestorationService` exists but requires manual backup restore.
- **Gap**: No automated rollback for broken deployments. Database migrations are forward-only. No blue/green, canary, or feature-flag deployment patterns.
- **Compensating Controls**:
  - Lidarr creates automatic database backups before updates.
  - Users can manually restore from backup and reinstall the previous version.
- **Remediation Timeline**: 90–180 days
- **Recommendation**: Implement reversible database migrations. Add a rollback command that restores the previous version from the backup created during update. Consider feature flags for API-breaking changes.
- **Evidence**: `src/NzbDrone.Update/`, `src/NzbDrone.Core/Datastore/DatabaseRestorationService.cs`, `src/NzbDrone.Core/Datastore/Migration/`

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Lidarr has extensive test projects: `NzbDrone.Core.Test`, `NzbDrone.Host.Test`, `NzbDrone.Api.Test`, `NzbDrone.Integration.Test`, `NzbDrone.Automation.Test`, `NzbDrone.Common.Test`, `NzbDrone.Libraries.Test`, `NzbDrone.Mono.Test`, `NzbDrone.Windows.Test`, and `NzbDrone.Update.Test`. The CI pipeline runs unit tests on multiple platforms (Windows, Mac, Linux, FreeBSD, Alpine) with both SQLite and PostgreSQL. SonarCloud analysis with code coverage reporting is configured. Integration tests run against the actual packaged application.
- **Gap**: While test coverage is substantial, there are no dedicated API contract tests validating input handling, output format, and error responses for specific agent consumption scenarios. Integration tests cover API behavior implicitly but not systematically for all endpoints.
- **Compensating Controls**:
  - Integration tests provide broad API coverage.
  - SonarCloud tracks coverage metrics.
  - Automation tests validate end-to-end UI + API flows.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add dedicated API test suites for agent-consumed endpoints, validating response schemas, error formats, and pagination behavior.
- **Evidence**: `src/NzbDrone.Api.Test/`, `src/NzbDrone.Integration.Test/`, `src/NzbDrone.Automation.Test/`, `azure-pipelines.yml` (Unit_Test, Integration, Automation stages)

#### ENG-Q5: Encryption at Rest — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Lidarr uses SQLite (file-based) or PostgreSQL for data storage. The SQLite database file is stored on the local filesystem with no encryption. The SQLite connection string in `ConnectionStringFactory.cs` does not include encryption parameters. PostgreSQL connections use standard `NpgsqlConnectionStringBuilder` without SSL/TLS enforcement or encryption-at-rest configuration. User credential hashes, API keys, and download client credentials are stored without database-level encryption.
- **Gap**: No encryption at rest for SQLite databases. No explicit encryption configuration for PostgreSQL. Sensitive data (credential hashes, API keys) stored in unencrypted database files.
- **Compensating Controls**:
  - Rely on filesystem-level encryption (e.g., LUKS, BitLocker, FileVault) on the host system.
  - PostgreSQL deployments can use encrypted storage at the database server level.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Support SQLite encryption (SEE or SQLCipher). Document recommended filesystem encryption for self-hosted deployments. For PostgreSQL, enforce SSL connections and document encryption-at-rest requirements.
- **Evidence**: `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` (SQLite and PostgreSQL connection strings)

#### AUTH-Q4: Identity Propagation and Delegation — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Lidarr is a self-hosted, single-application system — not a multi-service architecture. There are no downstream service calls that require identity propagation. The application does call external services (indexers, download clients, metadata sources) but authenticates to those services with their own credentials, not with the caller's identity. There is no JWT, no OAuth token exchange, no on-behalf-of flows.
- **Gap**: No identity propagation mechanism exists. While the self-hosted architecture minimizes the practical impact, the `stateful-crud` archetype requires evaluation at RISK-QUALITY severity. If Lidarr is integrated into a multi-service agent orchestration, the absence of identity propagation means the agent architecture layer must handle identity context entirely.
- **Compensating Controls**:
  - Agent architecture layer can manage identity context externally, passing user context via custom headers if needed.
  - The single-application deployment model limits the blast radius of missing identity propagation.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: If agent integration requires user-delegated operations, implement a lightweight identity context mechanism (e.g., accept `X-On-Behalf-Of` header with user principal and validate against an allowlist).
- **Evidence**: `src/Lidarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/NzbDrone.Core/Indexers/HttpIndexerBase.cs`

---

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO (Pass)
- **Finding**: Lidarr exposes a fully documented REST API via ASP.NET Core controllers in `src/Lidarr.Api.V1/`. The API surface includes 40+ controller directories covering Artists, Albums, Tracks, TrackFiles, Commands, Queue, History, Search, Indexers, DownloadClients, Notifications, and more. An OpenAPI 3.0.4 specification is maintained at `src/Lidarr.Api.V1/openapi.json` (13,102 lines, 308 KB). The API is served at `/api/v1/` with JSON request/response formats.
- **Implication**: The REST API provides a comprehensive integration surface for agent tools. No direct database access or UI automation required.
- **Recommendation**: No action required. The API surface is well-defined and documented.
- **Evidence**: `src/Lidarr.Api.V1/` (all controller directories), `src/Lidarr.Api.V1/openapi.json`

### API-Q2: Machine-Readable API Specification

- **Severity**: INFO (Pass)
- **Finding**: An OpenAPI 3.0.4 specification exists at `src/Lidarr.Api.V1/openapi.json`, auto-generated by Swashbuckle (configured in `Startup.cs` via `services.AddSwaggerGen()`). The CI pipeline's `Api_Docs` job regenerates the spec and auto-creates PRs for changes. The spec includes security definitions for API key authentication (header and query parameter).
- **Implication**: Agent tool definitions can be auto-generated from the OpenAPI spec. The spec is kept current via CI automation.
- **Recommendation**: No action required. Consider publishing the spec to an API catalog for easier discovery.
- **Evidence**: `src/Lidarr.Api.V1/openapi.json`, `src/NzbDrone.Host/Startup.cs` (AddSwaggerGen), `azure-pipelines.yml` (Api_Docs job)

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Write endpoints (POST, PUT, DELETE) do not implement idempotency keys. POST endpoints create new resources without checking for duplicates (e.g., `ArtistController.AddArtist` creates via `_addArtistService.AddArtist`). PUT endpoints update by ID (naturally idempotent for the same payload). DELETE endpoints delete by ID (naturally idempotent). No `Idempotency-Key` header support found.
- **Implication**: For read-only agent scope, idempotency is not a concern. If agent scope expands to write-enabled, POST endpoints will need idempotency key support to prevent duplicate resource creation on retry.
- **Recommendation**: Plan for idempotency key middleware if agent scope is upgraded to write-enabled.
- **Evidence**: `src/Lidarr.Api.V1/Artist/ArtistController.cs` (AddArtist), `src/Lidarr.Http/REST/RestController.cs`

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: All API responses are JSON, serialized via `STJson` (System.Text.Json). Configured in `Startup.cs` via `AddJsonOptions(options => STJson.ApplySerializerSettings(options.JsonSerializerOptions))`. Response content type is `application/json` as declared in controller attributes (`[Produces("application/json")]`).
- **Implication**: JSON format is ideal for LLM consumption. No binary or complex XML parsing required for agent tools.
- **Recommendation**: No action required.
- **Evidence**: `src/NzbDrone.Host/Startup.cs` (AddJsonOptions), `src/Lidarr.Api.V1/Artist/ArtistController.cs` (`[Produces("application/json")]`)

### API-Q7: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: Lidarr emits real-time events via SignalR WebSocket hub at `/signalr/messages`. The `RestControllerWithSignalR` base class broadcasts `ModelAction` events (Created, Updated, Deleted, Sync) for all CRUD operations. Controllers like `ArtistController` handle domain events (`AlbumImportedEvent`, `ArtistAddedEvent`, etc.) and broadcast corresponding SignalR messages. The `CommandController` broadcasts command status updates via SignalR with debouncing.
- **Implication**: Agents can subscribe to SignalR for real-time state change notifications without polling. This enables proactive agent patterns (e.g., triggering actions when new albums are added).
- **Recommendation**: Document the SignalR message schema for agent consumers. Consider adding webhook support as an alternative to WebSocket subscription.
- **Evidence**: `src/NzbDrone.SignalR/MessageHub.cs`, `src/Lidarr.Http/REST/RestControllerWithSignalR.cs`, `src/Lidarr.Api.V1/Artist/ArtistController.cs` (Handle methods)

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limit documentation found. No rate limit headers (`X-RateLimit-Remaining`, `Retry-After`) are returned in API responses. No API Gateway throttle settings or WAF rate rules configured. The self-hosted nature of Lidarr means rate limits are deployment-specific.
- **Implication**: Agents have no visibility into rate limits. Without rate limit awareness, agents cannot self-throttle. This must be configured at the deployment layer (reverse proxy).
- **Recommendation**: Add rate limit headers to API responses once rate limiting is implemented (see STATE-Q5).
- **Evidence**: `src/NzbDrone.Host/Startup.cs` (no rate limit middleware)

### STATE-Q2: Queryable Current State

- **Severity**: INFO (Pass)
- **Finding**: All major entities expose GET endpoints for querying current state. `GET /api/v1/artist` returns all artists with statistics. `GET /api/v1/album` returns albums with filter support. `GET /api/v1/trackfile` returns track files. `GET /api/v1/queue` returns the current download queue. `GET /api/v1/command` returns active commands with status. `GET /api/v1/health` returns health check results. The OpenAPI spec documents 100+ GET endpoints across all resource types.
- **Implication**: Agents can inspect current state before taking action. The comprehensive GET API surface supports read-before-write patterns.
- **Recommendation**: No action required.
- **Evidence**: `src/Lidarr.Api.V1/openapi.json`, `src/Lidarr.Api.V1/Artist/ArtistController.cs` (AllArtists), `src/Lidarr.Api.V1/Commands/CommandController.cs` (GetStartedCommands)

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No optimistic locking (no version fields, no ETags, no `If-Match` headers). No pessimistic locking except implicit SQLite file-level locking. The `BasicRepository` uses Polly retry for SQLite busy errors, which handles concurrent access at the database level. The `ModelConflictException` exists for conflict detection but is only used for unique constraint violations.
- **Implication**: For read-only agent scope, concurrency controls are not a concern. If scope expands to write-enabled, optimistic locking should be implemented to prevent data races between concurrent agent instances.
- **Recommendation**: Plan for optimistic locking (version fields + ETags) if agent scope is upgraded to write-enabled.
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs`, `src/NzbDrone.Core/Datastore/ModelConflictException.cs`

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits. No per-agent action limits. No maximum records per operation. The `ArtistEditorController` supports bulk operations on artists and the `AlbumStudio` controller supports bulk album operations without quantity limits.
- **Implication**: For read-only agent scope, transaction limits are not a concern. If scope expands to write-enabled, per-agent transaction limits should be implemented to prevent bulk destructive operations.
- **Recommendation**: Plan for configurable per-agent transaction limits if scope is upgraded to write-enabled.
- **Evidence**: `src/Lidarr.Api.V1/Artist/ArtistEditorController.cs`, `src/Lidarr.Api.V1/AlbumStudio/`

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The Command system has statuses: `Queued`, `Started`, `Completed`, `Failed`, `Cancelled`. Commands are queued before execution, providing a natural "pending" state. However, there is no general-purpose "draft" state for CRUD operations — creating an artist immediately commits it to the database.
- **Implication**: For read-only scope, draft states are not relevant. The command queue provides some pending-state behavior for background operations.
- **Recommendation**: If expanding to write-enabled scope, consider adding a draft/pending state for entity creation that requires human confirmation.
- **Evidence**: `src/Lidarr.Api.V1/Commands/CommandController.cs`, `src/Lidarr.Api.V1/Commands/CommandResource.cs`

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No approval workflow exists. No operation requires human confirmation before execution. All API operations are executed immediately upon authenticated request.
- **Implication**: For read-only scope, approval gates are not relevant. If expanding to write-enabled scope, consider adding configurable approval gates for high-risk operations (e.g., bulk delete, API key reset).
- **Recommendation**: Plan for approval gates if scope is upgraded to write-enabled.
- **Evidence**: No approval workflow code found in the codebase.

### DATA-Q2: Data Residency and Sovereignty ⚡

- **Severity**: INFO (Pass)
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY, but no gap found
- **Finding**: Lidarr is a self-hosted application. All data (music library metadata, user credentials, download history) is stored locally on the user's filesystem (SQLite) or a user-configured PostgreSQL instance. No data is transmitted to cloud services by the application itself. The only external data flows are: (1) metadata queries to MusicBrainz/LidarrAPI for artist/album information, (2) indexer queries for release searches, and (3) download client interactions. None of these involve sending user-owned data to third parties.
- **Implication**: Data residency is fully under user control. An agent consuming Lidarr's API should be configured to not transmit Lidarr data to LLM providers in different jurisdictions if residency requirements apply.
- **Recommendation**: Document the data flow architecture for agent integrators. Note that agent orchestration layers must handle residency constraints for data extracted from Lidarr.
- **Evidence**: `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` (local SQLite paths), `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (PostgresHost property)

### DATA-Q3: Selective Query Support

- **Severity**: INFO (Pass)
- **Finding**: Lidarr implements pagination via `PagingSpec` with `Page`, `PageSize`, `SortKey`, `SortDirection`, and `FilterExpressions`. The `PagingResource` API model supports `page` (default 1), `pageSize` (default 10), and sorting parameters. The `BasicRepository.GetPaged` method applies LIMIT/OFFSET with sorting. Various API endpoints support query parameters for filtering (e.g., `artistId` on albums, `albumIds` on tracks). The `Wanted/Missing` and `Wanted/Cutoff` endpoints use paginated responses.
- **Implication**: Agents can query with filters, pagination, and sorting. The default page size of 10 prevents unbounded result sets.
- **Recommendation**: Consider adding a configurable maximum `pageSize` to prevent agents from requesting very large result sets.
- **Evidence**: `src/NzbDrone.Core/Datastore/PagingSpec.cs`, `src/Lidarr.Http/PagingResource.cs`, `src/NzbDrone.Core/Datastore/BasicRepository.cs` (GetPaged)

### DATA-Q4: System of Record Designations

- **Severity**: INFO (Pass)
- **Finding**: Lidarr is the authoritative system of record for the user's music library state — which artists are monitored, which albums are wanted, which track files exist on disk, download history, and quality/metadata profiles. Artist and album metadata is sourced from MusicBrainz via LidarrAPI but the local copy is the operational truth for the Lidarr instance.
- **Implication**: Agent should treat Lidarr as the authoritative source for music library state. Metadata freshness depends on the last metadata refresh command execution.
- **Recommendation**: No action required. Document the metadata refresh cadence for agent consumers.
- **Evidence**: `src/NzbDrone.Core/Music/` (domain models), `src/NzbDrone.Core/MetadataSource/`

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality scores, completeness metrics, or data profiling found. The `HealthCheck` system monitors application health (indexer connectivity, download client status, root folder accessibility) but does not assess data quality. No null rate monitoring, duplicate detection, or data freshness SLAs.
- **Implication**: Agent has no visibility into data quality. Missing metadata (e.g., albums without cover art, artists without biography) may affect agent reasoning quality.
- **Recommendation**: Consider adding data quality health checks (e.g., percentage of artists with complete metadata, albums with covers).
- **Evidence**: `src/NzbDrone.Core/HealthCheck/` (application health, not data quality)

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO (Pass)
- **Finding**: Field names are semantically meaningful using C# PascalCase conventions, serialized to camelCase JSON via STJson. Examples: `artistName`, `albumTitle`, `trackTitle`, `qualityProfileId`, `metadataProfileId`, `rootFolderPath`, `dateAdded`, `foreignArtistId`. No legacy abbreviations or opaque codes. The OpenAPI spec documents all fields with types.
- **Implication**: Agent LLM reasoning benefits from human-readable field names. No data dictionary needed.
- **Recommendation**: No action required.
- **Evidence**: `src/Lidarr.Api.V1/openapi.json`, `src/Lidarr.Api.V1/Artist/ArtistResource.cs`

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No formal data catalog or metadata layer exists. The OpenAPI spec serves as the primary API documentation. No AWS Glue Data Catalog, no DataHub, no Collibra. The database schema is defined implicitly through C# model classes and FluentMigrator migrations.
- **Implication**: Agent tool builders must rely on the OpenAPI spec and source code inspection to understand data semantics. Consider generating a data dictionary from the database schema.
- **Recommendation**: Generate and publish a data dictionary from the FluentMigrator migrations and model classes.
- **Evidence**: `src/Lidarr.Api.V1/openapi.json`, `src/NzbDrone.Core/Datastore/Migration/`

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No custom business outcome metrics published. No `cloudwatch.put_metric_data` or equivalent. Sentry captures errors and exceptions but not business KPIs. No dashboards tracking music library growth, download success rates, or import completion rates.
- **Implication**: When agents consume Lidarr, there are no business-level metrics to measure whether agent interactions produce good outcomes (e.g., successful library growth, quality upgrade rates).
- **Recommendation**: Add custom metrics for key business outcomes: successful imports per day, queue completion rate, metadata refresh success rate.
- **Evidence**: `src/NzbDrone.Core/Instrumentation/` (logging only, no metrics)

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO (Pass)
- **Finding**: Lidarr exposes a fully documented REST API via ASP.NET Core controllers in `src/Lidarr.Api.V1/` with an OpenAPI 3.0.4 specification at `src/Lidarr.Api.V1/openapi.json`. No direct database access or UI automation required.
- **Gap**: None — API interface exists and is documented.
- **Recommendation**: No action required.
- **Evidence**: `src/Lidarr.Api.V1/`, `src/Lidarr.Api.V1/openapi.json`

#### API-Q2: Machine-Readable API Specification
- **Severity**: INFO (Pass)
- **Finding**: OpenAPI 3.0.4 spec auto-generated by Swashbuckle, kept current via CI automation.
- **Gap**: None — machine-readable spec exists and is current.
- **Recommendation**: No action required.
- **Evidence**: `src/Lidarr.Api.V1/openapi.json`, `src/NzbDrone.Host/Startup.cs`

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: `ErrorModel` returns `Message`, `Description`, `Content` as JSON with appropriate HTTP status codes per error type. No structured error codes or retryable indicators.
- **Gap**: No error codes, no `retryable` field, stack traces in `Description`.
- **Recommendation**: Add `errorCode` and `retryable` to `ErrorModel`.
- **Evidence**: `src/Lidarr.Http/ErrorManagement/LidarrErrorPipeline.cs`, `src/Lidarr.Http/ErrorManagement/ErrorModel.cs`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No idempotency key support on POST endpoints. PUT/DELETE are naturally idempotent by ID.
- **Gap**: No `Idempotency-Key` header support. Relevant for future write-enabled scope.
- **Recommendation**: Plan for idempotency key middleware if scope is upgraded.
- **Evidence**: `src/Lidarr.Api.V1/Artist/ArtistController.cs`, `src/Lidarr.Http/REST/RestController.cs`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: All responses are JSON via STJson (System.Text.Json).
- **Gap**: N/A
- **Recommendation**: No action required.
- **Evidence**: `src/NzbDrone.Host/Startup.cs`

#### API-Q6: Asynchronous Operation Support
- **Severity**: RISK-QUALITY
- **Finding**: Command system supports async pattern (POST to start, GET to poll, SignalR for real-time). Lacks `Retry-After` headers and progress metadata.
- **Gap**: No `Retry-After` headers, no progress percentage, no estimated completion time.
- **Recommendation**: Add agent-friendly metadata to command responses.
- **Evidence**: `src/Lidarr.Api.V1/Commands/CommandController.cs`

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: SignalR hub at `/signalr/messages` broadcasts CRUD events for all entities.
- **Gap**: N/A — event emission exists.
- **Recommendation**: Document SignalR message schema for agent consumers.
- **Evidence**: `src/NzbDrone.SignalR/MessageHub.cs`, `src/Lidarr.Http/REST/RestControllerWithSignalR.cs`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit documentation or headers. Self-hosted — limits are deployment-specific.
- **Gap**: No rate limit headers returned.
- **Recommendation**: Add rate limit headers once rate limiting is implemented.
- **Evidence**: `src/NzbDrone.Host/Startup.cs`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: Single shared API key with no principal attribution. Claim is `ApiKey=true` only.
- **Gap**: No per-agent identity. Cannot distinguish consumers in audit logs.
- **Recommendation**: Implement multi-key auth with named principals.
- **Evidence**: `src/Lidarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: Single API key grants unrestricted access to all endpoints.
- **Gap**: No scoped permissions. No read-only role.
- **Recommendation**: Implement role-based API key scoping.
- **Evidence**: `src/Lidarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/NzbDrone.Host/Startup.cs`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization. Any authenticated consumer can perform any operation.
- **Gap**: No ABAC/RBAC per action.
- **Recommendation**: Implement per-action authorization policies.
- **Evidence**: `src/Lidarr.Http/REST/RestController.cs`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: RISK-QUALITY
- **Finding**: Self-hosted single-app architecture. No multi-service identity propagation needed. However, per stateful-crud archetype rules, evaluated at base RISK-QUALITY severity.
- **Gap**: No identity propagation mechanism exists. While the self-hosted architecture minimizes practical impact, the absence means the agent architecture layer must handle identity context if user-delegated operations are needed.
- **Recommendation**: If agent integration requires user-delegated operations, implement a lightweight identity context mechanism (e.g., `X-On-Behalf-Of` header).
- **Evidence**: `src/Lidarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`

#### AUTH-Q5: Credential Management
- **Severity**: RISK-QUALITY
- **Finding**: API key stored in plain-text XML config file. No secrets management integration.
- **Gap**: No secrets manager. No automatic rotation.
- **Recommendation**: Integrate with secrets manager for production deployments.
- **Evidence**: `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Auth logger and HTTP request logging exist but logs are not immutable. Log database supports deletion.
- **Gap**: No immutable log storage. No tamper-evident logging.
- **Recommendation**: Configure syslog forwarding to immutable log store.
- **Evidence**: `src/Lidarr.Http/Authentication/AuthenticationService.cs`, `src/NzbDrone.Core/Instrumentation/DatabaseTarget.cs`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: Only `ResetApiKeyCommand` exists — nuclear option that disconnects all consumers.
- **Gap**: Cannot suspend individual agent identities.
- **Recommendation**: Implement multi-key support with per-key suspension.
- **Evidence**: `src/NzbDrone.Core/Configuration/ResetApiKeyCommand.cs`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Database transactions for InsertMany only. No saga patterns, no compensation logic, no undo endpoints.
- **Gap**: No rollback for multi-step operations.
- **Recommendation**: Implement compensating actions for critical workflows.
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs`

#### STATE-Q2: Queryable Current State
- **Severity**: INFO (Pass)
- **Finding**: Comprehensive GET endpoints for all entities. 100+ GET endpoints documented in OpenAPI spec.
- **Gap**: None — current state is queryable.
- **Recommendation**: No action required.
- **Evidence**: `src/Lidarr.Api.V1/openapi.json`

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No optimistic locking, no ETags. Polly retry for SQLite busy errors handles basic concurrency.
- **Gap**: No optimistic locking (relevant for write-enabled scope).
- **Recommendation**: Plan for optimistic locking if scope is upgraded.
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: Polly retry for SQLite busy errors. No circuit breakers for external HTTP calls to indexers, download clients, notification services.
- **Gap**: No circuit breakers for external dependency calls.
- **Recommendation**: Add Polly circuit breaker policies to HTTP clients.
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs`, `src/NzbDrone.Core/Indexers/`, `src/NzbDrone.Core/Download/`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No rate limiting at any layer. Open CORS policy with `AllowAnyOrigin().AllowAnyMethod()`.
- **Gap**: No rate limiting middleware, no API Gateway, no WAF.
- **Recommendation**: Add ASP.NET Core rate limiting middleware.
- **Evidence**: `src/NzbDrone.Host/Startup.cs`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits. Bulk operations without quantity limits.
- **Gap**: No per-agent action limits (relevant for write-enabled scope).
- **Recommendation**: Plan for per-agent transaction limits if scope is upgraded.
- **Evidence**: `src/Lidarr.Api.V1/Artist/ArtistEditorController.cs`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path. This service is P2 priority and not on a critical path.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Command system has Queued/Started/Completed/Failed statuses. No general-purpose draft state for CRUD operations.
- **Gap**: No draft state for entity creation (relevant for write-enabled scope).
- **Recommendation**: Plan for draft states if scope is upgraded.
- **Evidence**: `src/Lidarr.Api.V1/Commands/CommandController.cs`

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No approval workflow exists. All operations execute immediately.
- **Gap**: No approval gates (relevant for write-enabled scope).
- **Recommendation**: Plan for approval gates if scope is upgraded.
- **Evidence**: No approval workflow code found.

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: No Docker Compose, no sandbox environment, no seed data scripts. CI pipeline runs tests but not persistent staging.
- **Gap**: No sandbox environment for agent testing.
- **Recommendation**: Create Docker Compose config with seed data for agent testing.
- **Evidence**: `azure-pipelines.yml`, `build.sh`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: User credentials, API keys, and service credentials stored without classification or field-level access controls.
- **Gap**: No data classification. No field-level access controls.
- **Recommendation**: Create data classification inventory; implement field-level filtering.
- **Evidence**: `src/NzbDrone.Core/Authentication/UserService.cs`, `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO (Pass)
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY, but no gap found
- **Finding**: Self-hosted application. All data stored locally. No data transmitted to cloud services.
- **Gap**: None — data residency under user control.
- **Recommendation**: Document data flow architecture for agent integrators.
- **Evidence**: `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs`

#### DATA-Q3: Selective Query Support
- **Severity**: INFO (Pass)
- **Finding**: Pagination via PagingSpec (Page, PageSize, SortKey, SortDirection, FilterExpressions). Default pageSize=10.
- **Gap**: No maximum pageSize enforcement.
- **Recommendation**: Add configurable maximum pageSize.
- **Evidence**: `src/NzbDrone.Core/Datastore/PagingSpec.cs`, `src/Lidarr.Http/PagingResource.cs`

#### DATA-Q4: System of Record Designations
- **Severity**: INFO (Pass)
- **Finding**: Lidarr is authoritative for music library state. Metadata sourced from MusicBrainz but local copy is operational truth.
- **Gap**: None.
- **Recommendation**: Document metadata refresh cadence.
- **Evidence**: `src/NzbDrone.Core/Music/`, `src/NzbDrone.Core/MetadataSource/`

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK-QUALITY
- **Finding**: UTC timestamps via DapperUtcConverter. DateAdded/Modified fields on entities. No freshness signaling headers.
- **Gap**: No Cache-Control, X-Data-Age, or last_refreshed headers.
- **Recommendation**: Add freshness headers to GET responses.
- **Evidence**: `src/NzbDrone.Core/Datastore/Converters/UtcConverter.cs`

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: IP addresses and usernames logged in plain text in auth and HTTP request logs.
- **Gap**: No PII redaction. CleanseLogMessage exists but inconsistently applied.
- **Recommendation**: Apply CleanseLogMessage consistently; mask IPs in auth logs.
- **Evidence**: `src/Lidarr.Http/Authentication/AuthenticationService.cs`, `src/Lidarr.Http/Middleware/LoggingMiddleware.cs`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics. HealthCheck monitors app health, not data quality.
- **Gap**: No data quality monitoring.
- **Recommendation**: Add data quality health checks.
- **Evidence**: `src/NzbDrone.Core/HealthCheck/`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: API versioned as v1. OpenAPI spec versioned. 80+ database migrations via FluentMigrator. CI auto-generates openapi.json. No breaking change detection.
- **Gap**: No breaking change detection in CI. No consumer-driven contract tests.
- **Recommendation**: Add OpenAPI diff validation to CI pipeline.
- **Evidence**: `src/Lidarr.Api.V1/openapi.json`, `azure-pipelines.yml`, `src/NzbDrone.Core/Datastore/Migration/`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO (Pass)
- **Finding**: PascalCase C# serialized to camelCase JSON. Human-readable names (artistName, albumTitle, etc.). No legacy abbreviations.
- **Gap**: None.
- **Recommendation**: No action required.
- **Evidence**: `src/Lidarr.Api.V1/openapi.json`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal data catalog. OpenAPI spec serves as primary documentation.
- **Gap**: No metadata layer beyond OpenAPI spec.
- **Recommendation**: Generate data dictionary from model classes.
- **Evidence**: `src/Lidarr.Api.V1/openapi.json`, `src/NzbDrone.Core/Datastore/Migration/`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: NLog logging with ApiRequestSequenceID for request correlation. Log database with structured fields. No OpenTelemetry, no distributed tracing, no JSON structured logs.
- **Gap**: No distributed tracing. No trace ID propagation. Logs not structured JSON.
- **Recommendation**: Add OpenTelemetry instrumentation; configure NLog JSON layout.
- **Evidence**: `src/Lidarr.Http/Middleware/LoggingMiddleware.cs`, `src/NzbDrone.Core/Instrumentation/DatabaseTarget.cs`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: Sentry integration for error tracking with release management. No explicit alerting thresholds for error rates or latency.
- **Gap**: No alerting thresholds. No SLO-based alerting.
- **Recommendation**: Configure Sentry alert rules for API error rates and latency.
- **Evidence**: `src/NzbDrone.Core/Instrumentation/ReconfigureSentry.cs`, `azure-pipelines.yml`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business outcome metrics. Sentry captures errors only.
- **Gap**: No business KPI tracking.
- **Recommendation**: Add metrics for library growth, download success rates, import completion rates.
- **Evidence**: `src/NzbDrone.Core/Instrumentation/`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK-QUALITY
- **Finding**: No IaC found. Self-hosted desktop/server application. Infrastructure managed by end users.
- **Gap**: No IaC governance. No cloud infrastructure to govern.
- **Recommendation**: Provide reference infrastructure configs (Docker Compose, Helm) for production deployments.
- **Evidence**: No IaC files found. `distribution/` (platform packaging only).

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive CI/CD via Azure Pipelines with multi-platform builds, tests, and SonarCloud analysis. Auto-generated openapi.json. No API contract tests.
- **Gap**: No API contract testing. No breaking change detection.
- **Recommendation**: Add OpenAPI diff step to CI. Add contract tests for agent endpoints.
- **Evidence**: `azure-pipelines.yml`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: Self-contained package distribution. Built-in updater. No automated rollback. Forward-only database migrations.
- **Gap**: No automated rollback. No blue/green or canary deployments.
- **Recommendation**: Implement reversible migrations. Add rollback command.
- **Evidence**: `src/NzbDrone.Update/`, `src/NzbDrone.Core/Datastore/DatabaseRestorationService.cs`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: 10 test projects. Multi-platform CI with unit, integration, and automation tests. SonarCloud coverage. No dedicated API contract tests.
- **Gap**: No systematic API contract testing for agent consumption.
- **Recommendation**: Add dedicated API test suites for agent-consumed endpoints.
- **Evidence**: `src/NzbDrone.Api.Test/`, `src/NzbDrone.Integration.Test/`, `azure-pipelines.yml`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: RISK-QUALITY
- **Finding**: SQLite file-based storage without encryption. PostgreSQL without explicit encryption-at-rest config.
- **Gap**: No database-level encryption at rest.
- **Recommendation**: Support SQLite encryption (SQLCipher). Document filesystem encryption requirements.
- **Evidence**: `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs`

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `src/Lidarr.Http/Authentication/ApiKeyAuthenticationHandler.cs` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4 |
| `src/Lidarr.Http/Authentication/AuthenticationService.cs` | AUTH-Q6, DATA-Q6 |
| `src/Lidarr.Http/Authentication/AuthenticationBuilderExtensions.cs` | AUTH-Q1 |
| `src/Lidarr.Http/Authentication/NoAuthenticationHandler.cs` | AUTH-Q4 |
| `src/Lidarr.Http/ErrorManagement/LidarrErrorPipeline.cs` | API-Q3 |
| `src/Lidarr.Http/ErrorManagement/ErrorModel.cs` | API-Q3 |
| `src/Lidarr.Http/Middleware/LoggingMiddleware.cs` | AUTH-Q6, DATA-Q6, OBS-Q1 |
| `src/Lidarr.Http/REST/RestController.cs` | AUTH-Q3, API-Q4 |
| `src/Lidarr.Http/REST/RestControllerWithSignalR.cs` | API-Q7 |
| `src/Lidarr.Http/PagingResource.cs` | DATA-Q3 |
| `src/NzbDrone.Host/Startup.cs` | API-Q2, API-Q5, API-Q8, AUTH-Q2, STATE-Q5 |
| `src/NzbDrone.Core/Authentication/UserService.cs` | DATA-Q1 |
| `src/NzbDrone.Core/Authentication/UserRepository.cs` | DATA-Q1 |
| `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` | AUTH-Q1, AUTH-Q5, AUTH-Q6, AUTH-Q7, DATA-Q1, DATA-Q2 |
| `src/NzbDrone.Core/Configuration/ResetApiKeyCommand.cs` | AUTH-Q7 |
| `src/NzbDrone.Core/Datastore/BasicRepository.cs` | STATE-Q1, STATE-Q3, STATE-Q4, DATA-Q3 |
| `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` | DATA-Q2, DATA-Q5, ENG-Q5 |
| `src/NzbDrone.Core/Datastore/DbFactory.cs` | Archetype detection |
| `src/NzbDrone.Core/Datastore/PagingSpec.cs` | DATA-Q3 |
| `src/NzbDrone.Core/Datastore/Converters/UtcConverter.cs` | DATA-Q5 |
| `src/NzbDrone.Core/Datastore/DatabaseRestorationService.cs` | ENG-Q3 |
| `src/NzbDrone.Core/Datastore/ModelConflictException.cs` | STATE-Q3 |
| `src/NzbDrone.Core/Instrumentation/DatabaseTarget.cs` | AUTH-Q6, OBS-Q1 |
| `src/NzbDrone.Core/Instrumentation/ReconfigureSentry.cs` | OBS-Q2 |
| `src/NzbDrone.SignalR/MessageHub.cs` | API-Q7 |
| `src/Lidarr.Api.V1/Artist/ArtistController.cs` | API-Q4, API-Q5, API-Q7 |
| `src/Lidarr.Api.V1/Artist/ArtistEditorController.cs` | STATE-Q6 |
| `src/Lidarr.Api.V1/Commands/CommandController.cs` | API-Q6, STATE-Q1, HITL-Q1 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `src/Lidarr.Api.V1/openapi.json` | API-Q1, API-Q2, DISC-Q1, DISC-Q2, STATE-Q2 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `azure-pipelines.yml` | API-Q2, OBS-Q2, ENG-Q2, ENG-Q4, HITL-Q3, DISC-Q1 |
| `.github/workflows/ci.yml` | ENG-Q2 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `package.json` | Archetype detection (frontend stack) |
| `global.json` | Archetype detection (.NET SDK version) |
| `src/Directory.Build.props` | Archetype detection (project structure) |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `build.sh` | HITL-Q3 |

### Notable Absences
| Absent Artifact | Questions Affected |
|----------------|-------------------|
| No Dockerfile or docker-compose.yml | HITL-Q3, ENG-Q1 |
| No Terraform/CloudFormation/CDK files | ENG-Q1 |
| No rate limiting middleware | STATE-Q5, API-Q8 |
| No OpenTelemetry instrumentation | OBS-Q1 |
| No API contract tests (Pact, OpenAPI diff) | ENG-Q2, DISC-Q1 |
| No secrets management integration | AUTH-Q5 |
| No data classification tags | DATA-Q1 |
| No PII redaction middleware | DATA-Q6 |
