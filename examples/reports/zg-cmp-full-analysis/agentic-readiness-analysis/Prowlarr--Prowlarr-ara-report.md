# Agentic Readiness Analysis Report

**Target**: Prowlarr (.)
**Date**: 2026-04-29
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**Repository Type**: monorepo
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: csharp, media, desktop
**Context**: Indexer manager/proxy for the *arr suite.

**Archetype Justification**: Prowlarr manages persistent state in SQLite/PostgreSQL (indexers, applications, history, users, config) and exposes full CRUD endpoints via ASP.NET Core REST controllers. It owns entity lifecycle management for indexers and applications, qualifying it as stateful-crud.

---

## Table of Contents

1. Readiness Profile
2. Summary
3. BLOCKERs — Must Resolve Before Agent Deployment
4. RISKs
   - RISK-SAFETY — Must Address for Agent Safety
   - RISK-QUALITY — Address as Capacity Allows
5. INFOs — Architecture and Design Inputs
6. Detailed Findings
   - 01 — API Surface and Interface Design (API-Q1 through API-Q8)
   - 02 — Authentication, Authorization, and Identity (AUTH-Q1 through AUTH-Q7)
   - 03 — State Management and Transactional Integrity (STATE-Q1 through STATE-Q7)
   - 04 — Human-in-the-Loop and Approval Workflows (HITL-Q1 through HITL-Q3)
   - 05 — Data Accessibility and Quality (DATA-Q1 through DATA-Q7)
   - 06 — Discoverability and Semantic Readiness (DISC-Q1 through DISC-Q3)
   - 07 — Observability of Target Systems (OBS-Q1 through OBS-Q3)
   - 08 — Engineering and Deployment Maturity (ENG-Q1 through ENG-Q5)
7. Evidence Index

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 2 | **RISK-SAFETY**: 9 | **RISK-QUALITY**: 18 | **INFOs**: 13

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days. The two BLOCKERs (AUTH-Q1: Machine Identity Authentication, DATA-Q1: Sensitive Data Classification) must be resolved before any agent integration — even read-only pilots. Once BLOCKERs are resolved, the 9 RISK-SAFETY findings will place Prowlarr at "Pilot-Ready (Safety Concerns)" requiring supervised pilot with elevated safety oversight and prioritized safety remediation.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 2 |
| RISK-SAFETY | 9 |
| RISK-QUALITY | 18 |
| INFO | 13 |
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
- **Finding**: Prowlarr uses a single shared API key for all API authentication (`ApiKeyAuthenticationHandler.cs`). The key is configured per-instance in the XML config file and validated via `X-Api-Key` header, `apikey` query parameter, or `Authorization: Bearer` header. On successful authentication, the only claim set is `ApiKey=true` — there is no principal attribution. All API key holders receive identical, undifferentiated access. There is no support for multiple API keys, service accounts, or machine identity with distinct principals.
- **Gap**: No per-agent identity support. Cannot distinguish which agent made a call. A single compromised API key exposes the entire API surface with no attribution trail.
- **Remediation**:
  - **Immediate**: Implement multi-key support where each API key maps to a named principal (e.g., `agent-read-only`, `sonarr-sync`). Store keys in a key table with principal name and creation timestamp. Include the principal name in all log entries.
  - **Target State**: Each agent identity has its own API key with principal attribution. Audit logs record which specific agent identity performed each action.
  - **Estimated Effort**: Medium (2–4 weeks for multi-key support and audit attribution)
  - **Dependencies**: AUTH-Q6 (audit logging) benefits from principal attribution.
- **Evidence**: `src/Prowlarr.Http/Authentication/ApiKeyAuthenticationHandler.cs` (lines 55–63: single claim `ApiKey=true`), `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (ApiKey property, single key per instance)

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: Prowlarr stores sensitive data without field-level classification or tagging. The database contains: (1) indexer credentials — API keys, passwords, cookies stored as JSON in the `Settings` column of the `Indexers` table; (2) application credentials — API keys and URLs for Sonarr/Radarr/Lidarr in the `Settings` column of the `Applications` table; (3) user credentials — passwords and salts in the `Users` table; (4) download client credentials in `DownloadClients` settings. The `ProtectionService` provides AES encryption for download link protection but does not encrypt stored credentials at the field level.
- **Gap**: No data classification scheme exists. Sensitive credentials (indexer API keys, *arr application API keys, user passwords) are stored in a JSON blob in the `Settings` column without field-level encryption, classification tags, or access controls distinguishing sensitive from non-sensitive fields. An agent with API access can retrieve indexer configurations containing plaintext API keys for third-party services.
- **Remediation**:
  - **Immediate**: Classify fields containing credentials as sensitive. Implement field-level encryption for the `Settings` column using `ProtectionService` (which already provides AES encryption). Redact sensitive fields from API GET responses unless explicitly requested with elevated authorization.
  - **Target State**: All credential fields are encrypted at rest and redacted from API responses. A data classification schema identifies PII, credentials, and configuration data.
  - **Estimated Effort**: Medium (3–6 weeks for field-level encryption and API response filtering)
  - **Dependencies**: AUTH-Q2 (scoped permissions) needed to control which identities can access sensitive fields.
- **Evidence**: `src/NzbDrone.Core/Datastore/Migration/001_initial_setup.cs` (Settings columns on Indexers, Applications, Notifications tables), `src/NzbDrone.Core/Security/ProtectionService.cs` (AES encryption exists but only used for download links), `src/Prowlarr.Api.V1/Indexers/` (API exposes indexer settings including credentials)

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The API key grants full, undifferentiated access to all API endpoints. There is no role-based or scope-based permission model. The `FallbackPolicy` in `Startup.cs` requires authentication via the `"API"` scheme but does not differentiate between read and write permissions. All authenticated requests have identical privileges. There is no mechanism to issue a read-only API key.
- **Gap**: Cannot scope an agent to read-only access. An agent authenticated with the API key can call write endpoints (POST/PUT/DELETE) even if only read access is intended.
- **Compensating Controls**:
  - Implement an API gateway or reverse proxy in front of Prowlarr that restricts agent traffic to GET methods only.
  - Use network-level controls to limit the agent's access to specific endpoints.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Introduce role-based API keys (e.g., `read-only`, `read-write`, `admin`) with method-level enforcement in the authorization pipeline.
- **Evidence**: `src/NzbDrone.Host/Startup.cs` (FallbackPolicy, lines 136–140), `src/Prowlarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization exists. The authorization pipeline uses a single `FallbackPolicy` that requires authentication but does not distinguish between read, write, or delete actions on the same resource type. The `UiAuthorizationHandler` provides a local-address bypass for UI access but no action-level differentiation for API consumers.
- **Gap**: Cannot prevent an agent from deleting indexers when only read access is intended. All authenticated API consumers have identical action-level permissions.
- **Compensating Controls**:
  - Deploy an API gateway that filters allowed HTTP methods per agent identity.
  - Implement a middleware that checks HTTP method against a per-key permission map before routing to controllers.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add action-level authorization attributes to controllers (e.g., `[Authorize(Policy = "ReadOnly")]` on GET endpoints, `[Authorize(Policy = "ReadWrite")]` on POST/PUT/DELETE).
- **Evidence**: `src/NzbDrone.Host/Startup.cs` (FallbackPolicy), `src/Prowlarr.Http/Authentication/UiAuthorizationHandler.cs`

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: `AuthenticationService.cs` logs login success, failure, logout, and unauthorized events via NLog to the `Auth` logger, including IP address and username. However: (1) logs are written to local files and optionally to SQLite/PostgreSQL — neither is immutable or tamper-evident; (2) API key authentication does not log per-request actions — only initial auth events; (3) no CloudTrail, WORM storage, or log integrity verification exists; (4) the `LoggingMiddleware` logs HTTP request/response pairs at Trace level but without principal attribution.
- **Gap**: No immutable audit trail. Logs are mutable local files. API key-authenticated requests are not individually attributed to a principal. An agent's actions cannot be forensically reconstructed.
- **Compensating Controls**:
  - Forward NLog output to an external immutable log store (e.g., CloudWatch Logs with retention lock, S3 with object lock).
  - Add request-level audit logging that records the authenticated principal, HTTP method, path, and timestamp for every API call.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add structured audit logging middleware that logs every API request with principal identity. Configure log forwarding to an immutable store.
- **Evidence**: `src/Prowlarr.Http/Authentication/AuthenticationService.cs` (auth logging), `src/Prowlarr.Http/Middleware/LoggingMiddleware.cs` (HTTP logging without principal attribution), `src/NzbDrone.Core/Instrumentation/DatabaseTarget.cs` (log storage in SQLite/PostgreSQL)

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: There is a single API key per Prowlarr instance. The only way to revoke access is to regenerate the API key via `ResetApiKeyCommand`, which invalidates the key for all consumers simultaneously. There is no mechanism to suspend a specific agent identity without disrupting all other API consumers (including *arr application integrations that rely on the same API key).
- **Gap**: Cannot isolate a misbehaving agent without disrupting the entire integration ecosystem. Revoking the API key breaks Sonarr, Radarr, Lidarr, and all other consumers simultaneously.
- **Compensating Controls**:
  - Use a reverse proxy that maintains per-agent tokens and maps them to the shared Prowlarr API key. Revoke at the proxy layer.
  - Implement network-level blocking for specific agent IPs.
- **Remediation Timeline**: 30–60 days (dependent on AUTH-Q1 multi-key support)
- **Recommendation**: Implement multi-key support (AUTH-Q1) with individual key revocation capability.
- **Evidence**: `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (single ApiKey, `ResetApiKeyCommand`)

#### STATE-Q1: Compensation and Rollback ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The `ApplicationService.SyncIndexers` method performs multi-step operations across Prowlarr and external *arr applications (add, update, remove indexers). Failures in individual steps are caught per-application with try/catch in `ExecuteAction`, recording status via `ApplicationStatusService` (escalation levels, failure tracking). However, there is no saga pattern, compensation logic, or rollback mechanism. If step 3 of a 5-application sync fails, the first 2 applications have already been modified with no undo capability.
- **Gap**: No compensation or rollback for multi-step operations. Partial failures during application sync leave systems in inconsistent states.
- **Compensating Controls**:
  - Application sync can be re-run (`ApplicationIndexerSyncCommand`) to reconcile state, functioning as an eventual-consistency mechanism.
  - The `forceSync` parameter allows full re-synchronization as a manual recovery step.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement compensation logic in `ApplicationService` that tracks sync operations and can undo partial changes on failure.
- **Evidence**: `src/NzbDrone.Core/Applications/ApplicationService.cs` (SyncIndexers, ExecuteAction methods), `src/NzbDrone.Core/Applications/ApplicationStatusService.cs`

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Prowlarr implements retry logic at the database layer (`BasicRepository` uses Polly `RetryStrategy` with exponential backoff for SQLite busy errors). The `ApplicationStatusService` implements an escalation pattern that disables failing integrations after repeated failures. The HTTP client (`HttpClient.cs`) handles `TooManyRequestsException` (429) and uses `RateLimitService` for outbound request rate limiting. However: (1) no formal circuit breaker pattern exists — the `ApplicationStatus` escalation is not a circuit breaker (it does not trip open and half-open); (2) no timeout configuration on the HTTP client for downstream calls beyond the default .NET timeout; (3) no bulkhead isolation between indexer calls and application sync calls.
- **Gap**: No circuit breaker implementation. Cascading failures from downstream indexers or *arr applications are mitigated by status escalation but not by circuit breaker patterns that prevent thundering herd on recovery.
- **Compensating Controls**:
  - The `ApplicationStatusService` escalation pattern provides degraded-mode behavior (disabling failing integrations).
  - The `RateLimitService` provides host-level outbound rate limiting.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add Polly circuit breaker policies to the HTTP client for downstream service calls. Implement bulkhead isolation for independent downstream service categories.
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs` (RetryStrategy), `src/NzbDrone.Common/Http/HttpClient.cs` (TooManyRequestsException handling), `src/NzbDrone.Common/TPL/RateLimitService.cs`, `src/NzbDrone.Core/Applications/ApplicationStatusService.cs`

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Prowlarr has no API-layer rate limiting for inbound requests. The `Startup.cs` middleware pipeline does not include any rate limiting middleware. The `RateLimitService` exists but is used exclusively for outbound HTTP requests to indexers (per-host rate limiting), not for inbound API traffic. There is no API Gateway, WAF, or application-level throttling configuration.
- **Gap**: No inbound API rate limiting. A runaway agent loop can send unlimited requests per second to the Prowlarr API, potentially overwhelming the application (especially with search operations that fan out to multiple indexers).
- **Compensating Controls**:
  - Deploy a reverse proxy (nginx, HAProxy) in front of Prowlarr with rate limiting configuration.
  - Use ASP.NET Core's built-in rate limiting middleware (`Microsoft.AspNetCore.RateLimiting`).
- **Remediation Timeline**: 7–14 days (quick win with ASP.NET Core rate limiting middleware)
- **Recommendation**: Add `Microsoft.AspNetCore.RateLimiting` middleware to `Startup.cs` with configurable per-client rate limits. This is a low-effort, high-impact change.
- **Evidence**: `src/NzbDrone.Host/Startup.cs` (no rate limiting middleware), `src/NzbDrone.Common/TPL/RateLimitService.cs` (outbound only), `src/Prowlarr.Http/Middleware/` (no rate limiting middleware)

#### DATA-Q2: Data Residency and Sovereignty ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Prowlarr is a self-hosted desktop/server application. Data is stored locally in SQLite files or in a user-configured PostgreSQL instance. All data resides on the user's infrastructure by default. There are no cross-region replication settings or cloud-managed data stores. However, if an agent reads Prowlarr data and sends it to an LLM endpoint in another jurisdiction, the data (which may include usernames, IP addresses, and third-party service credentials) could cross compliance boundaries.
- **Gap**: No data residency controls exist within the application. The application does not enforce or document data residency requirements. If integrated with an LLM-based agent, the data flow to the LLM provider's region is not controlled by the application.
- **Compensating Controls**:
  - Self-hosted nature means data residency is controlled by the operator's infrastructure choices.
  - Agent architecture should enforce data residency at the agent layer (e.g., use a regional LLM endpoint).
- **Remediation Timeline**: 30–60 days (documentation and agent-architecture-level controls)
- **Recommendation**: Document the data types stored by Prowlarr and their sensitivity classifications. Provide guidance for agent integrators on data residency requirements.
- **Evidence**: `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` (local SQLite or user-configured PostgreSQL)

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Prowlarr implements `CleanseLogMessage` which uses 30+ regex rules to scrub API keys, tokens, passwords, tracker announce keys, and other credentials from log messages. Remote IP addresses are partially redacted for non-local addresses (middle octets replaced). However: (1) `AuthenticationService.cs` logs usernames and IP addresses in auth events at Info/Warn/Debug levels without redaction; (2) the `LoggingMiddleware` logs full request paths including query parameters (which may contain sensitive data) at Trace level; (3) the `DatabaseTarget` stores cleansed log messages in SQLite/PostgreSQL but the auth-specific logs go through a separate logger that may not have the same cleansing applied.
- **Gap**: Usernames and IP addresses are logged in plaintext in auth events. The `CleanseLogMessage` regex rules are comprehensive for credential scrubbing but do not cover username or IP address fields in structured auth log entries (which bypass the general cleansing pipeline).
- **Compensating Controls**:
  - The `CleanseLogMessage` rules cover most credential patterns effectively.
  - The `CleanseRemoteIPRegex` partially redacts non-local IP addresses.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Apply `CleanseLogMessage` to auth logger output. Redact usernames in log entries (or hash them). Ensure all log pipelines flow through the cleansing middleware.
- **Evidence**: `src/NzbDrone.Common/Instrumentation/CleanseLogMessage.cs` (credential scrubbing rules), `src/Prowlarr.Http/Authentication/AuthenticationService.cs` (plaintext username/IP logging), `src/Prowlarr.Http/Middleware/LoggingMiddleware.cs` (request path logging)

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: An OpenAPI 3.0.4 specification exists at `src/Prowlarr.Api.V1/openapi.json` (auto-generated via Swashbuckle). The CI pipeline includes an `Api_Docs` job that regenerates the spec on the `develop` branch and auto-creates a PR if changes are detected. The spec documents security schemes (X-Api-Key header and apikey query parameter).
- **Gap**: The spec is auto-generated only on the `develop` branch (not on PRs), meaning the spec may drift during feature development until merged.
- **Compensating Controls**:
  - The Api_Docs CI job provides automated spec regeneration.
  - The spec is committed to the repository, providing version control history.
- **Remediation Timeline**: 7–14 days
- **Recommendation**: Add OpenAPI spec validation to PR checks to detect drift before merge.
- **Evidence**: `src/Prowlarr.Api.V1/openapi.json`, `azure-pipelines.yml` (Api_Docs job), `src/NzbDrone.Host/Startup.cs` (SwaggerGen configuration)

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: `ProwlarrErrorPipeline.cs` handles exceptions and returns JSON error responses via `ErrorModel` which contains `Message`, `Description`, and `Content` fields. Different exception types map to appropriate HTTP status codes (400 for validation, 404 for not found, 409 for conflicts, 500 for internal errors). `ValidationException` returns FluentValidation error objects directly.
- **Gap**: No `retryable` boolean or error category field. No machine-readable error code (only HTTP status code and freeform message). Agents cannot programmatically distinguish retriable from terminal errors without parsing message text.
- **Compensating Controls**:
  - HTTP status codes provide basic error categorization (429, 503 = retriable; 400, 404, 409 = terminal).
  - The `ErrorModel.Content` field can carry additional context when populated.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add an `errorCode` enum and `retryable` boolean to `ErrorModel`. Define a standard error code catalog.
- **Evidence**: `src/Prowlarr.Http/ErrorManagement/ProwlarrErrorPipeline.cs`, `src/Prowlarr.Http/ErrorManagement/ErrorModel.cs`

#### API-Q6: Asynchronous Operation Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Prowlarr supports an asynchronous command system via `CommandController`. Commands are submitted via `POST /api/v1/command`, queued by `CommandQueueManager`, and their status can be polled via `GET /api/v1/command`. The `SearchController` search operation is synchronous and may take >30s when querying multiple indexers. SignalR provides real-time command status updates.
- **Gap**: Search operations (potentially long-running) are synchronous with no job submission/polling pattern. Only the command system supports async patterns.
- **Compensating Controls**:
  - The command system provides async patterns for operations like `ApplicationIndexerSyncCommand`.
  - SignalR provides push notifications for command status changes.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Consider wrapping search operations in the command system to support async execution with polling.
- **Evidence**: `src/Prowlarr.Api.V1/Commands/CommandController.cs`, `src/Prowlarr.Api.V1/Search/SearchController.cs`

#### AUTH-Q4: Identity Propagation and Delegation — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Prowlarr does not implement identity propagation. When making downstream calls to *arr applications (Sonarr, Radarr, etc.), Prowlarr authenticates using the target application's API key stored in `ApplicationDefinition.Settings`. There is no concept of "acting on behalf of" a specific user or agent — all downstream calls are made under Prowlarr's own service identity. No JWT, OAuth token exchange, or on-behalf-of flows exist.
- **Gap**: Cannot distinguish whether a downstream action was triggered by a human via the UI or an agent via the API. All downstream calls use the same service identity regardless of the original caller.
- **Compensating Controls**:
  - For a read-only agent scope, identity propagation is less critical since no state changes are being made downstream on behalf of the agent.
  - Audit logging improvements (AUTH-Q6) can track the original caller context.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add caller context headers to downstream HTTP requests so *arr applications can log the originating principal.
- **Evidence**: `src/NzbDrone.Core/Applications/ApplicationService.cs`, `src/NzbDrone.Core/Applications/Sonarr/`, `src/NzbDrone.Common/Http/HttpClient.cs`

#### AUTH-Q5: Credential Management — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The API key is stored in a local XML config file (`config.xml`) read by `ConfigFileProvider`. Indexer and application credentials are stored in the SQLite/PostgreSQL database in the `Settings` JSON column. No secrets management system (Vault, AWS Secrets Manager) is used. No credential rotation mechanism exists beyond manual `ResetApiKeyCommand` for the API key. PostgreSQL connection credentials are passed via environment variables or config file.
- **Gap**: Credentials stored in plaintext in config files and database. No rotation mechanism. No secrets manager integration.
- **Compensating Controls**:
  - Self-hosted nature means the operator controls file system permissions on the config file and database.
  - The `ProtectionService` provides AES encryption capability that could be extended to credential storage.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Encrypt sensitive fields in the database using `ProtectionService`. Support environment variable-based API key configuration for containerized deployments. Implement automatic API key rotation.
- **Evidence**: `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (XML config file storage), `src/NzbDrone.Core/Security/ProtectionService.cs` (AES encryption available)

#### STATE-Q2: Queryable Current State — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Prowlarr exposes comprehensive GET endpoints for current state: indexers (`GET /api/v1/indexer`), applications (`GET /api/v1/applications`), history (`GET /api/v1/history` with pagination), indexer status (`GET /api/v1/indexerstatus`), application status, system status, health checks, and commands. `BasicRepository.GetPaged` provides pagination with `Page`, `PageSize`, `SortKey`, and `SortDirection`. State is readily queryable before taking action.
- **Gap**: Minimal. State is queryable and paginated. No freshness indicators on GET responses (see DATA-Q5).
- **Compensating Controls**:
  - Comprehensive REST endpoints for all entity types.
- **Remediation Timeline**: N/A (satisfied with minor gap noted in DATA-Q5)
- **Recommendation**: Add `Last-Modified` or `ETag` headers to GET responses for cache validation.
- **Evidence**: `src/Prowlarr.Api.V1/Indexers/`, `src/Prowlarr.Api.V1/History/HistoryController.cs`, `src/NzbDrone.Core/Datastore/BasicRepository.cs` (GetPaged)

#### DATA-Q3: Selective Query Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Prowlarr supports pagination via `PagingSpec<TModel>` with `Page`, `PageSize`, `SortKey`, `SortDirection`, and `FilterExpressions`. The `HistoryController` supports filtering by `eventType`, `successful`, `downloadId`, and `indexerIds`. The search API supports `limit`, `offset`, `query`, `type`, `categories`, and `indexerIds` parameters. `PagingRequestResource` defaults to `Page=1, PageSize=10`.
- **Gap**: No maximum page size enforcement — a client can request `PageSize=999999` to retrieve unbounded result sets. GraphQL-style field selection is not available.
- **Compensating Controls**:
  - Default page size of 10 provides reasonable defaults.
  - Filter parameters reduce result set size.
- **Remediation Timeline**: 7–14 days
- **Recommendation**: Enforce a maximum `PageSize` (e.g., 100) in `PagingResource` validation.
- **Evidence**: `src/Prowlarr.Http/PagingResource.cs`, `src/NzbDrone.Core/Datastore/PagingSpec.cs`, `src/Prowlarr.Api.V1/History/HistoryController.cs`

#### DATA-Q4: System of Record Designations — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Prowlarr is the system of record for indexer definitions, application mappings (`AppIndexerMap`), and search history within its own scope. However, the *arr applications (Sonarr, Radarr, etc.) maintain their own copies of indexer configurations via the sync mechanism. There is no documented system-of-record designation or master data management process.
- **Gap**: No formal system-of-record documentation. When indexer configurations exist in both Prowlarr and Sonarr, there is no documented resolution process for conflicts (Prowlarr pushes to *arr apps, but conflicts are handled ad-hoc).
- **Compensating Controls**:
  - The `ApplicationService.SyncIndexers` method provides unidirectional sync (Prowlarr → *arr apps) as the de facto system-of-record pattern.
- **Remediation Timeline**: 14–30 days (documentation)
- **Recommendation**: Document Prowlarr as the system of record for indexer configurations. Document the sync flow and conflict resolution behavior.
- **Evidence**: `src/NzbDrone.Core/Applications/ApplicationService.cs` (SyncIndexers), `src/NzbDrone.Core/Applications/AppIndexerMapService.cs`

#### DATA-Q5: Temporal Metadata and Freshness — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Some temporal metadata exists: `History` table has `Date` column (DateTime), `Indexers` table has `Added` column (DateTime), `Commands` table has `QueuedAt`/`StartedAt`/`EndedAt` columns. SQLite is configured with `DateTimeKind.Utc`. PostgreSQL migration 036 updates timestamp columns to with-timezone. However: (1) no `updated_at` field on most entities (indexers, applications); (2) no `Cache-Control` or `Last-Modified` headers on API responses; (3) no freshness signaling (stale/cached/eventual consistency indicators).
- **Gap**: Limited temporal metadata. No `updated_at` timestamps on core entities. No HTTP cache headers or data freshness signaling in API responses.
- **Compensating Controls**:
  - History entries are timestamped with UTC dates.
  - The `IfModifiedMiddleware` exists but is used for static frontend assets, not API responses.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add `updated_at` columns to core entity tables. Add `Last-Modified` headers to API GET responses.
- **Evidence**: `src/NzbDrone.Core/Datastore/Migration/001_initial_setup.cs` (Date, Added columns), `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` (DateTimeKind.Utc), `src/Prowlarr.Http/Middleware/IfModifiedMiddleware.cs`

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The API is versioned at `/api/v1/` (via `VersionedApiControllerAttribute`). The OpenAPI spec is committed to the repository and auto-generated in CI. Database schema is versioned via FluentMigrator (43 migrations from 000 to 043). However: (1) no breaking change detection tools (e.g., OpenAPI diff, `buf breaking`) in CI; (2) no consumer-driven contract tests (Pact); (3) no deprecation notices or changelog for API changes.
- **Gap**: No automated breaking change detection in CI. API changes could break agent tool bindings without detection.
- **Compensating Controls**:
  - URL-based API versioning (`/api/v1/`) provides a versioning mechanism.
  - OpenAPI spec generation in CI provides a diff-able artifact.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add OpenAPI diff comparison in PR checks to detect breaking changes. Add a deprecation notice mechanism to API responses.
- **Evidence**: `src/Prowlarr.Http/VersionedApiControllerAttribute.cs`, `src/Prowlarr.Api.V1/openapi.json`, `azure-pipelines.yml` (Api_Docs job), `src/NzbDrone.Core/Datastore/Migration/`

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Prowlarr uses NLog for logging throughout. The `LoggingMiddleware` assigns a sequential `ApiRequestSequenceID` per request and logs timing. Logs can be output in CLEF (Compact Log Event Format) JSON via `CleansingClefLogLayout`. The `DatabaseTarget` stores logs in SQLite/PostgreSQL. Sentry integration exists for error tracking. However: (1) no distributed tracing (no OpenTelemetry, no X-Ray, no `traceparent` header propagation); (2) no `correlation_id` or `request_id` field in structured logs (only a sequential integer `ApiRequestSequenceID`); (3) CLEF format is available but not the default (default is console text format).
- **Gap**: No distributed tracing. No correlation ID propagation for multi-service debugging. The sequential request ID is local to one instance and not suitable for cross-service tracing.
- **Compensating Controls**:
  - CLEF JSON log format is available via configuration.
  - Sentry provides error tracking with stack traces.
  - Per-request timing is logged.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenTelemetry instrumentation to the ASP.NET Core pipeline. Propagate `traceparent` headers. Add a `correlation_id` field to structured log entries.
- **Evidence**: `src/Prowlarr.Http/Middleware/LoggingMiddleware.cs` (ApiRequestSequenceID), `src/NzbDrone.Common/Instrumentation/CleansingClefLogLayout.cs`, `src/NzbDrone.Core/Instrumentation/DatabaseTarget.cs`, `src/NzbDrone.Common/Instrumentation/Sentry/SentryTarget.cs`

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Prowlarr has a comprehensive `HealthCheckService` that runs periodic health checks (checks in `src/NzbDrone.Core/HealthCheck/Checks/`). Health check results are published via events (`HealthCheckCompleteEvent`, `HealthCheckFailedEvent`, `HealthCheckRestoredEvent`) and surfaced via the API (`GET /api/v1/health`). Notifications can be triggered on health issues via the notification system. However: (1) no external alerting integration (PagerDuty, OpsGenie) out of the box; (2) no error rate or latency threshold-based alerting; (3) health checks are internal application health, not API-level SLO monitoring.
- **Gap**: No API-level error rate or latency alerting. Health checks cover internal health (indexer connectivity, database, disk space) but not API performance metrics.
- **Compensating Controls**:
  - The health check system provides internal monitoring.
  - Notification integrations (email, Webhook, Discord, Slack, Telegram, etc.) can deliver health check alerts.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add API-level metrics (error rate, latency percentiles) and integrate with an external monitoring system.
- **Evidence**: `src/NzbDrone.Core/HealthCheck/HealthCheckService.cs`, `src/NzbDrone.Core/HealthCheck/Checks/`, `src/NzbDrone.Core/Notifications/`

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No dedicated sandbox or staging environment configuration exists. The CI pipeline tests against SQLite and PostgreSQL (versions 14, 15) in Docker containers during integration tests. The application can be run locally with a separate data directory. However: (1) no Docker Compose file for easy local testing; (2) no seed data scripts; (3) no synthetic data generators; (4) no environment-specific configuration for staging.
- **Gap**: No out-of-the-box sandbox environment. Testing agent behavior requires manually setting up a Prowlarr instance.
- **Compensating Controls**:
  - Integration tests run against real Prowlarr instances in CI.
  - The application can be run with a custom `--data` directory for isolation.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Create a Docker Compose file for local development/testing. Add seed data scripts for common test scenarios.
- **Evidence**: `azure-pipelines.yml` (integration test stages with PostgreSQL Docker containers), `src/NzbDrone.Integration.Test/`

#### ENG-Q1: Infrastructure Governance — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No infrastructure-as-code exists. Prowlarr is a self-hosted desktop/server application — there are no Terraform, CloudFormation, CDK, Helm, or Kustomize files. Infrastructure is managed by the end-user deploying the application. The CI pipeline (`azure-pipelines.yml`) defines the build/test infrastructure but not the deployment infrastructure.
- **Gap**: No IaC for the agent-facing integration surface. When deployed behind a reverse proxy or API gateway (recommended for agent integration), that infrastructure should be codified.
- **Compensating Controls**:
  - Self-hosted nature means infrastructure governance is the operator's responsibility.
  - Community Docker images exist (maintained externally by hotio/linuxserver) though not in this repository.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: If deploying Prowlarr as an agent integration target, create IaC for the deployment infrastructure (reverse proxy, rate limiting, monitoring). Consider adding a reference Dockerfile and Helm chart to the repository.
- **Evidence**: No IaC files found in repository. `distribution/` contains only Windows/macOS installer resources.

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive CI pipeline in Azure DevOps (`azure-pipelines.yml`): unit tests (multi-platform: Windows, Mac, Linux, FreeBSD, Alpine), integration tests (multi-platform with SQLite and PostgreSQL), automation tests, SonarCloud analysis, and OpenAPI spec generation (`Api_Docs` job). The `Api_Docs` job regenerates `openapi.json` and auto-creates PRs for spec changes. However: (1) no consumer-driven contract testing (Pact); (2) no OpenAPI diff/breaking change detection; (3) the `Api_Docs` job only runs on `develop` branch, not on PRs.
- **Gap**: No API contract testing in the CI pipeline. Breaking API changes are not detected before merge.
- **Compensating Controls**:
  - Comprehensive test suite (unit, integration, automation) reduces the risk of unintended API changes.
  - OpenAPI spec auto-generation catches spec drift on the develop branch.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add OpenAPI spec comparison (e.g., `oasdiff`) to PR checks. Add contract tests for critical API endpoints.
- **Evidence**: `azure-pipelines.yml` (Unit_Test, Integration, Automation, Analyze stages, Api_Docs job)

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Prowlarr has a built-in update mechanism (`src/NzbDrone.Update/`) that downloads and installs new versions. The `UpdateMechanism` supports `BuiltIn`, `Script`, and `External` modes. Database migrations are forward-only (FluentMigrator). There is no rollback mechanism for database schema changes. No blue/green deployment, canary, or traffic shifting capabilities exist.
- **Gap**: No automated rollback. Database migrations are irreversible. Rolling back to a previous version requires manual database backup restoration.
- **Compensating Controls**:
  - Database backups can be created before updates via the backup functionality (`src/NzbDrone.Core/Backup/`).
  - The update mechanism creates a backup before applying updates.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add forward-compatible migration strategies. Document rollback procedures. For agent-facing deployments, implement blue/green or canary patterns at the infrastructure layer.
- **Evidence**: `src/NzbDrone.Update/`, `src/NzbDrone.Core/Datastore/Migration/` (43 forward-only migrations), `src/NzbDrone.Core/Backup/`

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Multiple test projects exist: `NzbDrone.Core.Test`, `Prowlarr.Api.V1.Test`, `NzbDrone.Host.Test`, `NzbDrone.Integration.Test`, `NzbDrone.Automation.Test`, `NzbDrone.Common.Test`, `NzbDrone.Libraries.Test`, `Prowlarr.Benchmark.Test`. SonarCloud analysis with Cobertura coverage reports is configured in CI. Integration tests run the full application and test API endpoints.
- **Gap**: No dedicated API contract test suite. Coverage metrics are not published as part of the PR review process (SonarCloud gates are available but coverage thresholds are not documented).
- **Compensating Controls**:
  - Integration tests provide end-to-end API testing.
  - SonarCloud provides continuous code quality and coverage analysis.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add explicit API contract tests for agent-facing endpoints. Publish coverage reports as PR comments.
- **Evidence**: `src/Prowlarr.Api.V1.Test/`, `src/NzbDrone.Integration.Test/`, `azure-pipelines.yml` (SonarCloud, Cobertura)

#### ENG-Q5: Encryption at Rest — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: SQLite database files are stored on the local filesystem without encryption. PostgreSQL encryption at rest depends on the operator's PostgreSQL configuration. The application does not configure or enforce encryption at the database level. The `ProtectionService` provides application-level AES encryption but is only used for download link protection, not for database encryption.
- **Gap**: No encryption at rest for the SQLite database containing sensitive credentials (indexer API keys, application API keys, user passwords). Data is protected only by filesystem permissions.
- **Compensating Controls**:
  - Operators can use full-disk encryption (LUKS, BitLocker, FileVault) to encrypt the filesystem.
  - PostgreSQL deployments can enable TDE (Transparent Data Encryption).
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement SQLite encryption (e.g., SQLCipher) or extend `ProtectionService` to encrypt sensitive columns. Document the requirement for disk-level encryption in deployment guides.
- **Evidence**: `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` (no encryption in SQLite connection string), `src/NzbDrone.Core/Security/ProtectionService.cs` (AES available but unused for DB)

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO (Satisfied — no gap)
- **Finding**: Prowlarr exposes a fully documented REST API via ASP.NET Core controllers in the `Prowlarr.Api.V1` assembly at `/api/v1/`. An OpenAPI 3.0.4 specification exists at `src/Prowlarr.Api.V1/openapi.json`. Endpoints cover indexers, applications, search, history, commands, system, health, tags, notifications, download clients, and configuration. No direct database access or UI automation is required for integration.
- **Implication**: Agent tools can be generated directly from the OpenAPI specification. The REST API is the primary integration surface.
- **Recommendation**: No action needed. The API surface is well-documented and suitable for agent tool generation.
- **Evidence**: `src/Prowlarr.Api.V1/openapi.json`, `src/Prowlarr.Api.V1/` (controller directory), `src/NzbDrone.Host/Startup.cs` (SwaggerGen configuration)

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Write endpoints (POST, PUT, DELETE) do not implement idempotency keys. The `RestController.cs` does not include idempotency middleware or decorators. POST operations rely on database auto-increment IDs. No `Idempotency-Key` header support exists. However, the `BasicRepository.Insert` throws `InvalidOperationException` if a model already has an ID, providing some protection against duplicate inserts.
- **Implication**: If agent scope is expanded to write-enabled in the future, idempotency support will be required (escalates to BLOCKER).
- **Recommendation**: Plan for idempotency key support in write endpoints before enabling write-access agents.
- **Evidence**: `src/Prowlarr.Http/REST/RestController.cs`, `src/NzbDrone.Core/Datastore/BasicRepository.cs` (Insert method)

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: All API responses are JSON, serialized via `System.Text.Json` (configured in `Startup.cs` with `STJson.ApplySerializerSettings`). Controllers are annotated with `[Produces("application/json")]`. Property naming follows camelCase convention. The Torznab feed endpoint provides XML for compatibility with *arr applications.
- **Implication**: JSON responses are directly consumable by LLM-based agents. The Torznab XML endpoint would require parsing if consumed by an agent.
- **Recommendation**: No action needed for the primary REST API. Agent tools should target the `/api/v1/` JSON endpoints.
- **Evidence**: `src/NzbDrone.Host/Startup.cs` (STJson.ApplySerializerSettings), `src/Prowlarr.Api.V1/` (Produces attributes)

### API-Q7: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: Prowlarr uses SignalR (`MessageHub` at `/signalr/messages`) to broadcast real-time events. The `BroadcastResourceChange` pattern in `RestControllerWithSignalR` emits events for model created, updated, deleted, and sync operations. Command status updates are debounced and broadcast via SignalR. The `BasicRepository` publishes `ModelEvent<TModel>` via `IEventAggregator` for internal event handling.
- **Implication**: SignalR provides a real-time event stream that agents could subscribe to for reactive behavior (e.g., respond to indexer status changes). This is valuable for proactive agent patterns.
- **Recommendation**: Document the SignalR event schema for agent integrators. Consider adding webhook support as an alternative to SignalR for server-to-server integrations.
- **Evidence**: `src/NzbDrone.SignalR/MessageHub.cs`, `src/Prowlarr.Api.V1/Commands/CommandController.cs` (BroadcastResourceChange)

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limit headers (`X-RateLimit-Remaining`, `Retry-After`) are returned in API responses. No rate limiting documentation exists. The application does not include API Gateway throttle settings or WAF rate rules. The only rate limiting is the outbound `RateLimitService` for indexer queries.
- **Implication**: Agents have no visibility into their consumption rate. Without rate limit headers, agents cannot self-throttle and will need to implement their own backoff logic based on error responses (429 or connection failures).
- **Recommendation**: When implementing inbound rate limiting (STATE-Q5), include `X-RateLimit-Remaining` and `Retry-After` headers in responses.
- **Evidence**: `src/NzbDrone.Host/Startup.cs` (no rate limiting middleware), `src/Prowlarr.Http/Middleware/` (no rate limit headers)

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: SQLite is configured with WAL (Write-Ahead Logging) journal mode and `BusyTimeout=1000ms`. The `BasicRepository` includes a Polly `RetryStrategy` with exponential backoff for SQLite busy errors. However, no application-level optimistic locking exists (no version fields, ETags, or `If-Match` headers on entities). PostgreSQL uses `ReadCommitted` isolation level for batch inserts.
- **Implication**: For read-only agents, concurrency is not a concern. If scope is expanded to write-enabled, optimistic locking must be added to prevent race conditions between concurrent agent instances.
- **Recommendation**: Plan for optimistic locking (version fields or ETags) on core entities before enabling write-access agents.
- **Evidence**: `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` (WAL mode, BusyTimeout), `src/NzbDrone.Core/Datastore/BasicRepository.cs` (RetryStrategy)

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits exist (e.g., maximum records per operation, maximum spend per hour). Bulk operations like `InsertMany`, `UpdateMany`, and `DeleteMany` in `BasicRepository` have no upper bounds. The search API does not limit the number of concurrent indexer queries.
- **Implication**: For read-only agents, blast radius is limited to data retrieval volume. If scope is expanded to write-enabled, transaction limits are critical to prevent catastrophic bulk operations.
- **Recommendation**: Implement configurable operation limits before enabling write-access agents.
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs` (InsertMany, UpdateMany, DeleteMany without limits)

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No draft or pending state mechanism exists for most entities. Indexers, applications, and notifications are created in an active state immediately upon POST. The `Commands` table has status fields (`Status`, `QueuedAt`, `StartedAt`, `EndedAt`) that provide a pending-state pattern for commands. The `IndexerStatus` entity tracks failure states but not draft states.
- **Implication**: For read-only agents, draft states are not needed. For future write-enabled agents, a draft/review workflow would be valuable for high-risk operations like indexer creation or application configuration changes.
- **Recommendation**: Consider adding draft states for entity creation when planning write-enabled agent integration.
- **Evidence**: `src/NzbDrone.Core/Datastore/Migration/001_initial_setup.cs` (no draft/status columns on Indexers, Applications)

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No approval gate mechanism exists. All API operations execute immediately upon request. There is no workflow engine, approval endpoint, or configurable operation-level flags requiring human confirmation.
- **Implication**: For read-only agents, approval gates are not needed. For future write-enabled agents, approval gates would provide defense-in-depth for destructive operations.
- **Recommendation**: Consider implementing approval workflows for high-risk operations when planning write-enabled agent integration.
- **Evidence**: `src/Prowlarr.Http/REST/RestController.cs`, `src/Prowlarr.Api.V1/`

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No formal data quality metrics, completeness scores, or data profiling reports exist. The `HealthCheckService` provides application health monitoring but not data quality monitoring. The `IndexerStats` module tracks indexer query statistics but not data quality metrics.
- **Implication**: Agents cannot assess data reliability before acting on it. Data quality issues (stale indexer entries, orphaned mappings) would need to be detected by the agent itself.
- **Recommendation**: Consider adding data quality metrics (e.g., indexer availability rates, stale entry counts) to the health check or statistics API.
- **Evidence**: `src/NzbDrone.Core/HealthCheck/`, `src/NzbDrone.Core/IndexerStats/`

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Field names in the API and database are human-readable and semantically meaningful. Examples: `IndexerId`, `SyncLevel`, `EnableRss`, `EnableAutomaticSearch`, `Priority`, `EventType`, `DownloadId`, `PageSize`, `SortDirection`. The camelCase convention is consistently applied in API responses. No legacy abbreviations or opaque codes requiring a data dictionary were found.
- **Implication**: Agent LLM reasoning can effectively interpret field names without a data dictionary. Tool definitions generated from the OpenAPI spec will be self-describing.
- **Recommendation**: No action needed. Field naming is already suitable for agent consumption.
- **Evidence**: `src/Prowlarr.Api.V1/openapi.json`, `src/NzbDrone.Core/Datastore/Migration/001_initial_setup.cs`

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No formal data catalog or metadata layer exists. The OpenAPI spec serves as the de facto API schema documentation. The database schema is defined in FluentMigrator migration files. No AWS Glue Data Catalog, Collibra, Alation, or DataHub integration exists.
- **Implication**: Agent tool builders must rely on the OpenAPI spec and source code to understand data semantics. No automated data discovery is available.
- **Recommendation**: The OpenAPI spec is sufficient for agent tool generation. Consider adding API description annotations (`<summary>` XML comments) to controllers for richer spec documentation.
- **Evidence**: `src/Prowlarr.Api.V1/openapi.json`, `src/NzbDrone.Core/Datastore/Migration/`

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: Sentry integration exists for error tracking and release management (source maps uploaded in CI). The `IndexerStats` module tracks search statistics. Health checks monitor internal application health. However, no custom business outcome metrics are published (e.g., search success rates, indexer response times, sync completion rates). No metrics collection system (Prometheus, CloudWatch custom metrics) is configured.
- **Implication**: When agents consume the Prowlarr API, there will be no visibility into whether agent interactions produce good business outcomes (e.g., successful search rates, timely sync completions).
- **Recommendation**: Add Prometheus metrics endpoint or custom metric publishing for key business outcomes (search success rate, sync latency, indexer availability).
- **Evidence**: `azure-pipelines.yml` (Sentry source map upload), `src/NzbDrone.Core/IndexerStats/`, `src/NzbDrone.Common/Instrumentation/Sentry/SentryTarget.cs`

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO (Satisfied — control present)
- **Finding**: Prowlarr exposes a documented REST API at `/api/v1/` via ASP.NET Core controllers. OpenAPI 3.0.4 spec at `src/Prowlarr.Api.V1/openapi.json`. No direct DB access required.
- **Gap**: None. API surface is well-documented.
- **Recommendation**: No action needed.
- **Evidence**: `src/Prowlarr.Api.V1/openapi.json`, `src/NzbDrone.Host/Startup.cs`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: OpenAPI 3.0.4 spec exists, auto-generated via Swashbuckle, with CI auto-regeneration on develop branch.
- **Gap**: Spec regeneration only runs on develop branch, not on PRs.
- **Recommendation**: Add OpenAPI spec validation to PR checks.
- **Evidence**: `src/Prowlarr.Api.V1/openapi.json`, `azure-pipelines.yml`

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: JSON error responses with Message/Description/Content fields. Appropriate HTTP status codes per exception type.
- **Gap**: No machine-readable error code or retryable boolean.
- **Recommendation**: Add errorCode enum and retryable boolean to ErrorModel.
- **Evidence**: `src/Prowlarr.Http/ErrorManagement/ProwlarrErrorPipeline.cs`, `src/Prowlarr.Http/ErrorManagement/ErrorModel.cs`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No idempotency key support on write endpoints. POST relies on auto-increment IDs.
- **Gap**: Write endpoints are not idempotent (INFO for read-only scope).
- **Recommendation**: Plan for idempotency keys before enabling write-access agents.
- **Evidence**: `src/Prowlarr.Http/REST/RestController.cs`, `src/NzbDrone.Core/Datastore/BasicRepository.cs`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: All API responses are JSON via System.Text.Json with camelCase convention. Torznab feed provides XML for *arr compatibility.
- **Gap**: N/A
- **Recommendation**: Agent tools should target `/api/v1/` JSON endpoints.
- **Evidence**: `src/NzbDrone.Host/Startup.cs`

#### API-Q6: Asynchronous Operation Support
- **Severity**: RISK-QUALITY
- **Finding**: Command system supports async pattern (POST/GET/poll). Search operations are synchronous and may take >30s.
- **Gap**: Long-running search operations lack async support.
- **Recommendation**: Wrap search operations in the command system for async execution.
- **Evidence**: `src/Prowlarr.Api.V1/Commands/CommandController.cs`, `src/Prowlarr.Api.V1/Search/SearchController.cs`

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: SignalR hub at `/signalr/messages` broadcasts state changes in real-time. Internal event aggregator supports model events.
- **Gap**: N/A
- **Recommendation**: Document SignalR event schema. Consider webhook support.
- **Evidence**: `src/NzbDrone.SignalR/MessageHub.cs`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit headers in API responses. No rate limiting documentation.
- **Gap**: Agents cannot self-throttle.
- **Recommendation**: Include rate limit headers when implementing STATE-Q5.
- **Evidence**: `src/NzbDrone.Host/Startup.cs`, `src/Prowlarr.Http/Middleware/`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: Single shared API key per instance. No per-agent identity. Claim is only `ApiKey=true`.
- **Gap**: No principal attribution. Cannot distinguish agent identities.
- **Recommendation**: Implement multi-key support with named principals.
- **Evidence**: `src/Prowlarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: API key grants full access. No role-based permission model. FallbackPolicy requires authentication only.
- **Gap**: Cannot scope agent to read-only.
- **Recommendation**: Introduce role-based API keys with method-level enforcement.
- **Evidence**: `src/NzbDrone.Host/Startup.cs`, `src/Prowlarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization. All authenticated consumers have identical privileges.
- **Gap**: Cannot enforce read-only access per agent.
- **Recommendation**: Add action-level authorization attributes to controllers.
- **Evidence**: `src/NzbDrone.Host/Startup.cs`, `src/Prowlarr.Http/Authentication/UiAuthorizationHandler.cs`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: RISK-QUALITY
- **Finding**: No identity propagation to downstream *arr applications. All downstream calls use Prowlarr's service identity.
- **Gap**: Cannot distinguish originating caller in downstream systems.
- **Recommendation**: Add caller context headers to downstream requests.
- **Evidence**: `src/NzbDrone.Core/Applications/ApplicationService.cs`, `src/NzbDrone.Common/Http/HttpClient.cs`

#### AUTH-Q5: Credential Management
- **Severity**: RISK-QUALITY
- **Finding**: API key in XML config file. Credentials in database Settings column. No secrets manager. No rotation mechanism.
- **Gap**: Plaintext credential storage. No rotation.
- **Recommendation**: Encrypt sensitive database fields. Support env-var API key configuration.
- **Evidence**: `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`, `src/NzbDrone.Core/Security/ProtectionService.cs`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Auth events logged via NLog. Logs are mutable local files/database. No per-request audit with principal attribution.
- **Gap**: No immutable audit trail. No per-request agent attribution.
- **Recommendation**: Add structured audit logging middleware. Forward to immutable store.
- **Evidence**: `src/Prowlarr.Http/Authentication/AuthenticationService.cs`, `src/Prowlarr.Http/Middleware/LoggingMiddleware.cs`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: Single API key. Regeneration invalidates all consumers. No individual revocation.
- **Gap**: Cannot suspend individual agent without disrupting all integrations.
- **Recommendation**: Implement multi-key support with individual revocation.
- **Evidence**: `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Multi-step application sync with per-step error handling but no rollback or compensation.
- **Gap**: Partial failures leave inconsistent state.
- **Recommendation**: Implement compensation logic in ApplicationService.
- **Evidence**: `src/NzbDrone.Core/Applications/ApplicationService.cs`

#### STATE-Q2: Queryable Current State
- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive GET endpoints with pagination. State is readily queryable.
- **Gap**: No freshness indicators on responses.
- **Recommendation**: Add Last-Modified/ETag headers.
- **Evidence**: `src/Prowlarr.Api.V1/`, `src/NzbDrone.Core/Datastore/BasicRepository.cs`

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: SQLite WAL mode with BusyTimeout. Polly retry on busy. No optimistic locking.
- **Gap**: No application-level concurrency controls (INFO for read-only).
- **Recommendation**: Plan for optimistic locking before write-enabled scope.
- **Evidence**: `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs`, `src/NzbDrone.Core/Datastore/BasicRepository.cs`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: Polly retry at DB layer. ApplicationStatus escalation. No formal circuit breaker pattern.
- **Gap**: No circuit breaker. Cascading failure risk.
- **Recommendation**: Add Polly circuit breaker policies to HTTP client.
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs`, `src/NzbDrone.Common/Http/HttpClient.cs`, `src/NzbDrone.Common/TPL/RateLimitService.cs`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No inbound API rate limiting. RateLimitService is outbound only.
- **Gap**: Agent traffic can overwhelm the API.
- **Recommendation**: Add ASP.NET Core rate limiting middleware.
- **Evidence**: `src/NzbDrone.Host/Startup.cs`, `src/NzbDrone.Common/TPL/RateLimitService.cs`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits. Bulk operations have no bounds.
- **Gap**: No transaction limits (INFO for read-only).
- **Recommendation**: Implement operation limits before write-enabled scope.
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path. (Priority is P2.)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No draft state mechanism. Entities created in active state. Commands have status fields.
- **Gap**: No draft/pending state (INFO for read-only).
- **Recommendation**: Consider draft states for write-enabled agent scope.
- **Evidence**: `src/NzbDrone.Core/Datastore/Migration/001_initial_setup.cs`

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No approval gate mechanism. Operations execute immediately.
- **Gap**: No approval workflows (INFO for read-only).
- **Recommendation**: Consider approval workflows for write-enabled scope.
- **Evidence**: `src/Prowlarr.Http/REST/RestController.cs`

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: No sandbox configuration. CI uses Docker containers for testing. No Docker Compose for local dev.
- **Gap**: No out-of-the-box sandbox environment.
- **Recommendation**: Create Docker Compose file and seed data scripts.
- **Evidence**: `azure-pipelines.yml`, `src/NzbDrone.Integration.Test/`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: Sensitive credentials stored unclassified in database Settings columns. No field-level encryption or classification.
- **Gap**: No data classification. Credentials exposed via API.
- **Recommendation**: Classify sensitive fields. Implement field-level encryption.
- **Evidence**: `src/NzbDrone.Core/Datastore/Migration/001_initial_setup.cs`, `src/NzbDrone.Core/Security/ProtectionService.cs`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Self-hosted app. Data on user infrastructure. No residency controls.
- **Gap**: No data residency documentation or controls for agent data flows.
- **Recommendation**: Document data types and residency requirements for agent integrators.
- **Evidence**: `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK-QUALITY
- **Finding**: Pagination, sorting, filtering supported. Default page size 10.
- **Gap**: No maximum page size enforcement.
- **Recommendation**: Enforce maximum PageSize.
- **Evidence**: `src/Prowlarr.Http/PagingResource.cs`, `src/NzbDrone.Core/Datastore/PagingSpec.cs`

#### DATA-Q4: System of Record Designations
- **Severity**: RISK-QUALITY
- **Finding**: Prowlarr is de facto SoR for indexer configs. Unidirectional sync to *arr apps.
- **Gap**: No formal SoR documentation.
- **Recommendation**: Document Prowlarr as system of record for indexer configurations.
- **Evidence**: `src/NzbDrone.Core/Applications/ApplicationService.cs`

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK-QUALITY
- **Finding**: Some timestamps (Date, Added, QueuedAt). UTC storage. No updated_at. No cache headers.
- **Gap**: Limited temporal metadata. No freshness signaling.
- **Recommendation**: Add updated_at columns and Last-Modified headers.
- **Evidence**: `src/NzbDrone.Core/Datastore/Migration/001_initial_setup.cs`, `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs`

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: Comprehensive credential scrubbing via CleanseLogMessage (30+ regex rules). IP partial redaction. Auth logger logs usernames/IPs in plaintext.
- **Gap**: Usernames and IPs logged in plaintext in auth events.
- **Recommendation**: Apply CleanseLogMessage to auth logger. Redact/hash usernames.
- **Evidence**: `src/NzbDrone.Common/Instrumentation/CleanseLogMessage.cs`, `src/Prowlarr.Http/Authentication/AuthenticationService.cs`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics. Health checks cover app health, not data quality.
- **Gap**: N/A (INFO)
- **Recommendation**: Consider data quality metrics for indexer availability and stale entries.
- **Evidence**: `src/NzbDrone.Core/HealthCheck/`, `src/NzbDrone.Core/IndexerStats/`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: API versioned at /api/v1/. OpenAPI spec in repo. DB schema via FluentMigrator. No breaking change detection.
- **Gap**: No automated breaking change detection in CI.
- **Recommendation**: Add OpenAPI diff to PR checks.
- **Evidence**: `src/Prowlarr.Http/VersionedApiControllerAttribute.cs`, `src/Prowlarr.Api.V1/openapi.json`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Human-readable, semantically meaningful field names. Consistent camelCase convention.
- **Gap**: N/A
- **Recommendation**: No action needed.
- **Evidence**: `src/Prowlarr.Api.V1/openapi.json`, `src/NzbDrone.Core/Datastore/Migration/001_initial_setup.cs`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal data catalog. OpenAPI spec serves as de facto documentation.
- **Gap**: N/A
- **Recommendation**: Add XML comment annotations to controllers for richer spec documentation.
- **Evidence**: `src/Prowlarr.Api.V1/openapi.json`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: NLog with sequential request ID. CLEF JSON format available. Sentry integration. No distributed tracing.
- **Gap**: No distributed tracing. No correlation ID.
- **Recommendation**: Add OpenTelemetry instrumentation.
- **Evidence**: `src/Prowlarr.Http/Middleware/LoggingMiddleware.cs`, `src/NzbDrone.Common/Instrumentation/`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: HealthCheckService with periodic checks. Notification integrations. No API-level SLO alerting.
- **Gap**: No error rate/latency alerting on APIs.
- **Recommendation**: Add API metrics and external monitoring integration.
- **Evidence**: `src/NzbDrone.Core/HealthCheck/`, `src/NzbDrone.Core/Notifications/`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: Sentry for error tracking. IndexerStats for search statistics. No custom business metrics.
- **Gap**: N/A (INFO)
- **Recommendation**: Add Prometheus metrics for business outcomes.
- **Evidence**: `azure-pipelines.yml`, `src/NzbDrone.Core/IndexerStats/`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance
- **Severity**: RISK-QUALITY
- **Finding**: No IaC. Self-hosted desktop application. Infrastructure is operator-managed.
- **Gap**: No IaC for agent-facing integration surface.
- **Recommendation**: Create IaC for deployment infrastructure (reverse proxy, monitoring).
- **Evidence**: No IaC files found. `distribution/`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive CI (unit, integration, automation, SonarCloud). Api_Docs job. No contract testing.
- **Gap**: No API contract testing or breaking change detection in CI.
- **Recommendation**: Add OpenAPI diff and contract tests to PR checks.
- **Evidence**: `azure-pipelines.yml`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: Built-in update mechanism. Forward-only DB migrations. Backup before update.
- **Gap**: No automated rollback. Irreversible migrations.
- **Recommendation**: Document rollback procedures. Forward-compatible migrations.
- **Evidence**: `src/NzbDrone.Update/`, `src/NzbDrone.Core/Datastore/Migration/`, `src/NzbDrone.Core/Backup/`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: Multiple test projects. SonarCloud analysis. Integration tests against live app. No dedicated contract tests.
- **Gap**: No API contract test suite. Coverage thresholds not documented.
- **Recommendation**: Add API contract tests for agent-facing endpoints.
- **Evidence**: `src/Prowlarr.Api.V1.Test/`, `src/NzbDrone.Integration.Test/`, `azure-pipelines.yml`

#### ENG-Q5: Encryption at Rest
- **Severity**: RISK-QUALITY
- **Finding**: SQLite unencrypted on filesystem. PostgreSQL encryption depends on operator config. ProtectionService AES exists but unused for DB.
- **Gap**: No encryption at rest for SQLite database containing credentials.
- **Recommendation**: Implement SQLite encryption (SQLCipher) or extend ProtectionService.
- **Evidence**: `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs`, `src/NzbDrone.Core/Security/ProtectionService.cs`

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `src/Prowlarr.Http/Authentication/ApiKeyAuthenticationHandler.cs` | AUTH-Q1, AUTH-Q2 |
| `src/Prowlarr.Http/Authentication/AuthenticationService.cs` | AUTH-Q6, DATA-Q6 |
| `src/Prowlarr.Http/Authentication/UiAuthorizationHandler.cs` | AUTH-Q3 |
| `src/NzbDrone.Host/Startup.cs` | API-Q1, API-Q2, API-Q5, AUTH-Q2, AUTH-Q3, STATE-Q5, API-Q8 |
| `src/Prowlarr.Http/ErrorManagement/ProwlarrErrorPipeline.cs` | API-Q3 |
| `src/Prowlarr.Http/ErrorManagement/ErrorModel.cs` | API-Q3 |
| `src/Prowlarr.Http/REST/RestController.cs` | API-Q4, HITL-Q2 |
| `src/Prowlarr.Http/Middleware/LoggingMiddleware.cs` | AUTH-Q6, OBS-Q1, DATA-Q6 |
| `src/Prowlarr.Http/Middleware/IfModifiedMiddleware.cs` | DATA-Q5 |
| `src/Prowlarr.Http/PagingResource.cs` | DATA-Q3, STATE-Q2 |
| `src/NzbDrone.Core/Datastore/BasicRepository.cs` | API-Q4, STATE-Q2, STATE-Q3, STATE-Q4, STATE-Q6 |
| `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` | STATE-Q3, DATA-Q2, DATA-Q5, ENG-Q5 |
| `src/NzbDrone.Core/Datastore/PagingSpec.cs` | DATA-Q3 |
| `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` | AUTH-Q1, AUTH-Q5, AUTH-Q7 |
| `src/NzbDrone.Core/Applications/ApplicationService.cs` | STATE-Q1, STATE-Q4, AUTH-Q4, DATA-Q4 |
| `src/NzbDrone.Core/Applications/ApplicationStatusService.cs` | STATE-Q1, STATE-Q4 |
| `src/NzbDrone.Core/Security/ProtectionService.cs` | DATA-Q1, AUTH-Q5, ENG-Q5 |
| `src/NzbDrone.Common/Http/HttpClient.cs` | STATE-Q4, AUTH-Q4 |
| `src/NzbDrone.Common/TPL/RateLimitService.cs` | STATE-Q4, STATE-Q5 |
| `src/NzbDrone.Common/Instrumentation/CleanseLogMessage.cs` | DATA-Q6 |
| `src/NzbDrone.Core/Instrumentation/DatabaseTarget.cs` | AUTH-Q6, OBS-Q1 |
| `src/NzbDrone.Common/Instrumentation/CleansingClefLogLayout.cs` | OBS-Q1 |
| `src/NzbDrone.Common/Instrumentation/Sentry/SentryTarget.cs` | OBS-Q1, OBS-Q3 |
| `src/NzbDrone.SignalR/MessageHub.cs` | API-Q7 |
| `src/Prowlarr.Api.V1/Commands/CommandController.cs` | API-Q6, API-Q7 |
| `src/Prowlarr.Api.V1/Search/SearchController.cs` | API-Q6 |
| `src/Prowlarr.Api.V1/History/HistoryController.cs` | DATA-Q3, STATE-Q2 |
| `src/Prowlarr.Http/VersionedApiControllerAttribute.cs` | DISC-Q1 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `src/Prowlarr.Api.V1/openapi.json` | API-Q1, API-Q2, DISC-Q1, DISC-Q2, DISC-Q3 |
| `schemas/torznab.xsd` | API-Q5 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `azure-pipelines.yml` | API-Q2, ENG-Q2, ENG-Q3, ENG-Q4, HITL-Q3, OBS-Q3 |
| `.github/workflows/ci.yml` | ENG-Q2 |
| `.github/dependabot.yml` | ENG-Q2 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `package.json` | Discovery |
| `yarn.lock` | Discovery |
| `src/Prowlarr.sln` | Discovery |
| `global.json` | Discovery |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `.editorconfig` | Discovery |
| `src/omnisharp.json` | Discovery |
| `tsconfig.json` | Discovery |

### Database Migrations
| File | Questions Referenced |
|------|---------------------|
| `src/NzbDrone.Core/Datastore/Migration/001_initial_setup.cs` | DATA-Q1, DATA-Q5, HITL-Q1, DISC-Q2 |
| `src/NzbDrone.Core/Datastore/Migration/036_postgres_update_timestamp_columns_to_with_timezone.cs` | DATA-Q5 |

### Test Projects
| Directory | Questions Referenced |
|-----------|---------------------|
| `src/Prowlarr.Api.V1.Test/` | ENG-Q4 |
| `src/NzbDrone.Integration.Test/` | ENG-Q4, HITL-Q3 |
| `src/NzbDrone.Core.Test/` | ENG-Q4 |
| `src/NzbDrone.Automation.Test/` | ENG-Q4 |

### Notable Absences
| Absent Artifact | Questions Affected |
|-----------------|-------------------|
| No Dockerfile | HITL-Q3, ENG-Q1 |
| No Docker Compose | HITL-Q3 |
| No IaC files (Terraform, CloudFormation, CDK, Helm) | ENG-Q1 |
| No OpenTelemetry configuration | OBS-Q1 |
| No rate limiting middleware | STATE-Q5, API-Q8 |
| No circuit breaker configuration | STATE-Q4 |
| No idempotency key middleware | API-Q4 |
| No secrets manager integration | AUTH-Q5 |
