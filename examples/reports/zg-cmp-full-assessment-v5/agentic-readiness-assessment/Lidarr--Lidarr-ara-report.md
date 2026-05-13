# Agentic Readiness Assessment Report

**Target**: Lidarr (.)
**Date**: 2026-04-30
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: monorepo
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: csharp, media, desktop
**Context**: Music collection manager (*arr suite).

**Archetype Justification**: Lidarr owns a SQLite/PostgreSQL database with 80+ migrations, exposes full CRUD REST API endpoints, and orchestrates workflows across metadata providers, indexers, download clients, and notification services. Classified as stateful-crud (most conservative) because it owns persistent state AND performs CRUD operations despite significant orchestrator traits.

**Surface flags**:
- has_persistent_data_store: true
- has_http_rpc_surface: true
- has_auth_surface: true
- has_write_operations: true
- has_logging_of_user_data: true

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 2 | **RISK-SAFETY**: 8 | **RISK-QUALITY**: 14 | **INFOs**: 18

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days.

---

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
**Extended Questions Not Triggered**: 1
**Questions N/A (repo_type: monorepo)**: 0
**Service Archetype**: stateful-crud (auto-detected)

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: Lidarr uses a single shared API key for all API authentication (`ApiKeyAuthenticationHandler.cs`). The key is generated as a GUID stored in `config.xml` and shared across all consumers. Authentication creates a `ClaimsPrincipal` with only a generic `("ApiKey", "true")` claim — no principal identity, no agent ID, no caller attribution. All authenticated callers are indistinguishable in logs and audit trails.
- **Gap**: No machine identity model exists. There is no way to issue distinct API keys per agent instance, no principal attribution in the authentication ticket, and no audit log field that distinguishes which agent (or which caller) made a specific request. The `LoggingMiddleware.cs` logs IP address and User-Agent but not the authenticated identity.
- **Remediation**:
  - **Immediate**: Implement a multi-key API authentication model where each agent instance receives a unique API key mapped to a named principal. Extend the `ClaimsPrincipal` to include an identity claim (e.g., `agent_id`, `caller_name`) propagated into logs.
  - **Target State**: Each agent has a unique API key that resolves to a named identity visible in all request logs and audit trails.
  - **Estimated Effort**: Medium
  - **Dependencies**: AUTH-Q6 (audit logging) depends on this — identity must exist before it can be logged.
- **Evidence**: `src/Lidarr.Http/Authentication/ApiKeyAuthenticationHandler.cs` (lines 51-59: single `_apiKey` comparison, generic claim), `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (ApiKey property: single GUID), `src/Lidarr.Http/Middleware/LoggingMiddleware.cs` (logs IP and User-Agent only)

### DATA-Q1: Sensitive Data Classification ⚡ (Tiered)

- **Severity**: BLOCKER
- **Stage A**: Yes — Lidarr stores the master application API key, admin Forms-auth password, SSL/proxy passwords, and per-provider third-party credentials (indexer API keys, SABnzbd/qBittorrent/Transmission passwords, notification service tokens).
- **B1 — API response scoping: BLOCKER.** The framework's masking protection applies unevenly:
  - **Provider settings path: CLEAR.** `src/Lidarr.Http/ClientSchema/SchemaBuilder.cs:38-44` replaces any `PrivacyLevel.ApiKey`/`PrivacyLevel.Password` field with `"********"` (`PRIVATE_VALUE`) before serialization. Provider settings (Newznab `ApiKey`, SABnzbd `ApiKey`/`Password`/`Username`, etc.) are all decorated with `Privacy = PrivacyLevel.ApiKey|Password`, so `GET /api/v1/indexer/{id}` and `GET /api/v1/downloadclient/{id}` return masked credentials. CLEAR.
  - **HostConfigResource path: BLOCKER.** `src/Lidarr.Api.V1/Config/HostConfigResource.cs` is a plain POCO with public `string ApiKey`, `string Password`, `string PasswordConfirmation`, `string SslCertPassword`, `string ProxyPassword` — none decorated with `FieldDefinition`/`Privacy`. `HostConfigController.GetHostConfig()` reads `_configFileProvider.ToResource(_configService)` which copies these values directly. `GET /api/v1/config/host` returns the master API key, admin password, SSL cert password, and proxy password **unmasked in plaintext**.
- **B2 — Access control differentiation: RISK-SAFETY.** Single global API key (`src/Lidarr.Http/Authentication/ApiKeyAuthenticationHandler.cs:35-50`). No multi-user RBAC; no read-only/admin scopes.
- **B3 — Formal classification metadata: PARTIAL (contributes no finding).** `PrivacyLevel` enum (`FieldDefinitionAttribute.cs:95-101`) is formal classification, applied consistently to provider settings but **not** to `HostConfigResource`.
- **Overall (read-only scope)**: B1 fires as BLOCKER — a read-only agent calling `GET /api/v1/config/host` exfiltrates the master API key (enabling impersonation) plus stored admin/SSL/proxy passwords. Credential-exfiltration BLOCKER. → **DATA-Q1 = BLOCKER**.
- **Gap**: `HostConfigResource` bypasses the `SchemaBuilder`/`PrivacyLevel` masking that correctly protects provider settings.
- **Remediation**:
  - **Immediate**: Mask `ApiKey`, `Password`, `PasswordConfirmation`, `SslCertPassword`, `ProxyPassword` in `HostConfigResourceMapper.ToResource()`; or extend `SchemaBuilder` masking to non-provider resources via a `[Sensitive]` attribute.
  - **Estimated Effort**: Low (the masking primitive exists; this is a coverage fix).
- **Evidence**: `src/Lidarr.Api.V1/Config/HostConfigResource.cs` (unmasked credential properties), `src/Lidarr.Api.V1/Config/HostConfigController.cs` (returns resource without redaction), `src/Lidarr.Http/ClientSchema/SchemaBuilder.cs:38-44` (working masking pattern), `src/NzbDrone.Core/Annotations/FieldDefinitionAttribute.cs:95-101` (PrivacyLevel enum), `src/NzbDrone.Core/Indexers/Newznab/NewznabSettings.cs:62`, `src/NzbDrone.Core/Download/Clients/Sabnzbd/SabnzbdSettings.cs:54-62` (masked provider-side), `src/Lidarr.Http/Authentication/ApiKeyAuthenticationHandler.cs:35-50` (single global API key).

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The API key authentication model in `ApiKeyAuthenticationHandler.cs` is all-or-nothing. A valid API key grants full access to every endpoint — read and write, across all resource types (artists, albums, queue, system settings, commands). There are no role definitions, permission scopes, or access levels. The `ClaimsPrincipal` contains only `("ApiKey", "true")` with no scope or permission claims.
- **Gap**: No scoped permissions model exists. An agent intended for read-only music library queries would have identical privileges to one performing write operations on system settings.
- **Compensating Controls**:
  - Deploy a reverse proxy (e.g., nginx, Caddy) in front of Lidarr that restricts allowed HTTP methods (GET only) and URL paths per API key
  - Implement agent-side constraints in the orchestration layer to limit which endpoints the agent tool definitions expose
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement a role-based API key system with at minimum read-only and full-access tiers. Add scope claims to the authentication ticket.
- **Evidence**: `src/Lidarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/NzbDrone.Host/Startup.cs` (FallbackPolicy requires authenticated user but no role/scope check)

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization exists beyond the binary authenticated/unauthenticated check. All REST controllers inherit from `RestController<TResource>` which performs validation on input but no permission checks per action. The `V1ApiControllerAttribute` applies CORS policy but not authorization scoping. An authenticated caller can perform any CRUD operation on any resource.
- **Gap**: No RBAC, ABAC, or method-level authorization. An agent cannot be restricted to read-only operations on specific resource types at the application layer.
- **Compensating Controls**:
  - Implement a reverse proxy that filters by HTTP method (block POST/PUT/DELETE for read-only agents)
  - Use agent tool definitions that only expose GET endpoints
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add authorization attributes to controllers (e.g., `[Authorize(Policy = "ReadOnly")]` on GET methods, `[Authorize(Policy = "WriteAccess")]` on POST/PUT/DELETE).
- **Evidence**: `src/Lidarr.Http/REST/RestController.cs` (no authorization checks), `src/Lidarr.Api.V1/Artist/ArtistController.cs` (no `[Authorize]` attributes on action methods), `src/NzbDrone.Host/Startup.cs` (FallbackPolicy: RequireAuthenticatedUser only)

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: `LoggingMiddleware.cs` logs request method, path, IP address, User-Agent, response status code, and duration. However, it does not log the authenticated principal identity (because the authentication model produces no distinguishable principal — see AUTH-Q1). The `DatabaseTarget.cs` writes logs to SQLite/PostgreSQL with Message, Time, Logger, Exception, and Level — no principal field. The `AuthenticationService.cs` logs auth success/failure events with IP and username for forms auth, but not for API key auth. Log storage is not immutable — SQLite files and PostgreSQL tables can be modified by anyone with filesystem or database access.
- **Gap**: (1) No authenticated principal is logged per request (logs record IP/User-Agent but not who authenticated). (2) Log storage is mutable — no write-once, tamper-evident storage (no CloudTrail, no S3 Object Lock, no immutable log configuration). (3) The Auth logger captures forms authentication events but API key authentication produces no identity-attributed log entries.
- **Compensating Controls**:
  - Forward application logs to an external immutable log aggregator (e.g., Loki, Elasticsearch with append-only indices)
  - Add User-Agent-based agent identification as a proxy for principal attribution until AUTH-Q1 is resolved
- **Remediation Timeline**: 30–60 days (after AUTH-Q1 provides principal identity)
- **Recommendation**: Add authenticated principal to LoggingMiddleware output. Configure log forwarding to immutable storage.
- **Evidence**: `src/Lidarr.Http/Middleware/LoggingMiddleware.cs` (no principal in log entries), `src/NzbDrone.Core/Instrumentation/DatabaseTarget.cs` (INSERT schema: Message, Time, Logger, Exception, ExceptionType, Level — no principal), `src/Lidarr.Http/Authentication/AuthenticationService.cs` (Auth logger for forms auth only)

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: `ResetApiKeyCommand` in `ConfigFileProvider.cs` regenerates the single global API key (`SetValue("ApiKey", GenerateApiKey())`). This is an all-or-nothing mechanism — resetting the key invalidates ALL consumers simultaneously, not just a specific agent. There is no mechanism to issue, track, or selectively revoke individual agent API keys.
- **Gap**: Cannot suspend a single agent identity without disrupting all other API consumers. The single shared API key model means any suspension is a global lockout.
- **Compensating Controls**:
  - Use a reverse proxy with per-agent API keys that can be individually revoked at the proxy layer
  - Implement agent-specific rate limiting or IP-based blocking at the network layer
- **Remediation Timeline**: 60–90 days (depends on AUTH-Q1 multi-key implementation)
- **Recommendation**: Implement a multi-key system with individual key revocation capability. This is a prerequisite from AUTH-Q1.
- **Evidence**: `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (Execute method for ResetApiKeyCommand: `SetValue("ApiKey", GenerateApiKey())` — single global key)

#### STATE-Q1: Compensation and Rollback ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Lidarr's command execution framework (`CommandQueueManager`, `CommandExecutor`) processes operations as queued commands but provides no compensation or rollback mechanism for multi-step workflows. Operations like "add artist → search for releases → download → import" are sequential but not transactional — a failure at step 3 leaves steps 1-2 committed with no automatic undo. The `BackupService.cs` provides database backup/restore but this is a manual disaster recovery tool, not an operational rollback mechanism.
- **Gap**: No saga pattern, compensating transactions, or undo endpoints. Multi-step operations can leave the system in partial states on failure.
- **Compensating Controls**:
  - For read-only agent scope, this is informational — read operations do not create partial state
  - If scope expands to write-enabled, implement command-level undo via the existing event system
- **Remediation Timeline**: 90–180 days
- **Recommendation**: Implement compensation handlers for critical multi-step command workflows. The existing event aggregator pattern could be extended to support rollback events.
- **Evidence**: `src/Lidarr.Api.V1/Commands/CommandController.cs` (fire-and-forget command execution), `src/NzbDrone.Core/Backup/BackupService.cs` (manual backup only), `src/NzbDrone.Core/Datastore/BasicRepository.cs` (transaction support exists for InsertMany but not cross-entity compensation)

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Lidarr has partial resilience patterns: (1) `BasicRepository.cs` uses Polly `RetryStrategyOptions` with exponential backoff for SQLite busy errors (3 retries, 100ms base delay with jitter). (2) `ProviderStatusServiceBase.cs` implements an escalation-based backoff pattern that temporarily disables failing providers (indexers, download clients, notifications) with configurable escalation levels — this is a circuit-breaker-like pattern. (3) `HttpClient.cs` integrates with `RateLimitService.cs` for outbound request rate limiting. However: (a) No formal circuit breaker library pattern (e.g., Polly CircuitBreaker policy) on HTTP calls. (b) No timeout configuration visible on outbound HTTP clients beyond the default. (c) The `ProviderStatusServiceBase` escalation is provider-scoped, not request-scoped — a cascade failure through a provider may still affect the calling service before the provider is disabled.
- **Gap**: Resilience is partial. The provider status backoff is a reasonable compensating pattern but is not a true circuit breaker. HTTP client calls to external services (MusicBrainz, indexers, download clients) lack explicit circuit breaker policies that would prevent cascading failures from overwhelming the application.
- **Compensating Controls**:
  - The existing `ProviderStatusServiceBase` escalation pattern provides baseline protection against persistent provider failures
  - Agent callers should implement their own circuit breakers when calling Lidarr APIs
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add Polly `CircuitBreakerPolicy` to outbound HTTP client calls. The infrastructure (Polly dependency, `HttpClient.cs` interceptor pattern) already exists to support this.
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs` (Polly retry for SQLite), `src/NzbDrone.Core/ThingiProvider/Status/ProviderStatusServiceBase.cs` (escalation backoff), `src/NzbDrone.Common/Http/HttpClient.cs` (rate limiting but no circuit breaker), `src/NzbDrone.Common/TPL/RateLimitService.cs`

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No API-layer rate limiting exists on inbound requests to Lidarr's REST API. The `Startup.cs` middleware pipeline includes logging, authentication, authorization, response compression, caching, and buffering — but no rate limiting middleware. The `RateLimitService.cs` is used only for outbound HTTP requests (to indexers, download clients) — not for inbound API traffic. CORS is configured to `AllowAnyOrigin().AllowAnyMethod().AllowAnyHeader()` with no rate restrictions.
- **Gap**: No protection against a runaway agent loop making requests at machine speed. An agent bug could overwhelm the embedded SQLite database or exhaust application resources.
- **Compensating Controls**:
  - Deploy a reverse proxy with rate limiting in front of Lidarr (nginx `limit_req_zone`, Caddy `rate_limit`)
  - Configure agent-side rate limiting in the orchestration layer
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add ASP.NET Core rate limiting middleware (available in .NET 7+; Lidarr targets .NET 8) via `AddRateLimiter()` in `Startup.cs`. Configure per-IP or per-API-key limits.
- **Evidence**: `src/NzbDrone.Host/Startup.cs` (no rate limiting middleware in pipeline), `src/NzbDrone.Common/TPL/RateLimitService.cs` (outbound only), `src/NzbDrone.Host/Startup.cs` (CORS: AllowAnyOrigin, AllowAnyMethod)

#### DATA-Q2: Data Residency and Sovereignty ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Lidarr is a self-hosted desktop/server application where data residency is determined entirely by where the user installs it. The database (SQLite file or PostgreSQL server) resides on the user's infrastructure. No data residency controls, region configuration, or sovereignty enforcement exist in the application itself. If an agent reads data from a Lidarr instance and transmits it to an LLM endpoint in a different jurisdiction, the application has no mechanism to prevent or flag this.
- **Gap**: No data residency awareness or controls. The application does not classify data by jurisdiction, does not restrict cross-region transmission, and does not provide metadata about the legal jurisdiction of the data it holds.
- **Compensating Controls**:
  - Document data residency requirements in agent deployment configuration (external to Lidarr)
  - Use region-local LLM endpoints (e.g., Amazon Bedrock in the same region as the Lidarr instance)
- **Remediation Timeline**: 30–60 days (documentation); 90+ days (application-level controls)
- **Recommendation**: For a self-hosted music collection manager at P2 priority, data residency risk is lower than for cloud SaaS applications. Document residency considerations in the agent integration guide.
- **Evidence**: `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` (local SQLite path or user-configured PostgreSQL), `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (no region or residency configuration)

### RISK-QUALITY — Address as Capacity Allows

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: `ErrorModel.cs` defines a JSON error response with `Message`, `Description`, and `Content` fields. `LidarrErrorPipeline.cs` maps exception types to HTTP status codes (400 for validation, 404 for not found, 409 for conflicts, 500 for internal errors). Validation errors from FluentValidation are serialized directly. However, there is no machine-readable error code (only human-readable messages), no `retryable` boolean or error category, and no consistent error type taxonomy.
- **Gap**: No structured error code or retryable indicator. An agent receiving a 500 error cannot distinguish a transient database lock from a permanent logic error without parsing the message string.
- **Compensating Controls**:
  - Agent-side heuristic: treat 429 and 503 as retryable, 4xx as terminal
  - Parse error messages for known patterns (e.g., "constraint failed" = conflict)
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add an `ErrorCode` enum and `IsRetryable` boolean to `ErrorModel`. Map known exception types to stable error codes.
- **Evidence**: `src/Lidarr.Http/ErrorManagement/ErrorModel.cs`, `src/Lidarr.Http/ErrorManagement/LidarrErrorPipeline.cs`

#### API-Q6: Asynchronous Operation Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Lidarr has a command queue system (`CommandController.cs`) where long-running operations (metadata refresh, search, download) are submitted as commands via `POST /api/v1/command` and return immediately with a command ID. Command status can be queried via `GET /api/v1/command/{id}`. Real-time updates are pushed via SignalR (`MessageHub.cs`). However, there is no standard polling endpoint with completion status — the command status endpoint exists but does not follow a standard async pattern (e.g., `202 Accepted` with `Location` header pointing to status endpoint).
- **Gap**: Async pattern exists functionally but does not follow REST best practices for async operations. The `POST /api/v1/command` returns `201 Created` rather than `202 Accepted` with a `Location` header for status polling.
- **Compensating Controls**:
  - Agent can poll `GET /api/v1/command/{id}` after submission
  - Agent can subscribe to SignalR for real-time command status updates
- **Remediation Timeline**: 30 days
- **Recommendation**: Return `202 Accepted` with `Location: /api/v1/command/{id}` header for command submissions. Add `Retry-After` header.
- **Evidence**: `src/Lidarr.Api.V1/Commands/CommandController.cs` (StartCommand returns Created), `src/NzbDrone.SignalR/MessageHub.cs`

#### AUTH-Q4: Identity Propagation and Delegation — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Lidarr makes outbound calls to indexers, download clients, metadata providers, and notification services using service-specific credentials (API keys, passwords) stored in the database — not propagated caller identity. There is no JWT/OAuth token exchange, no on-behalf-of flows, and no mechanism to distinguish whether an outbound call was initiated by a human user or an agent. The application uses its own stored credentials for all external service calls regardless of who triggered the operation.
- **Gap**: No identity propagation through service calls. All outbound calls use Lidarr's own stored credentials with no caller context.
- **Compensating Controls**:
  - For a self-hosted music manager, identity propagation to external services is less critical than for a multi-tenant SaaS application
  - Log the initiating caller context in command execution for forensic purposes
- **Remediation Timeline**: 90+ days
- **Recommendation**: Low priority for a P2 self-hosted application. Consider adding caller context to command execution metadata if agent scope expands to write-enabled.
- **Evidence**: `src/NzbDrone.Common/Http/HttpClient.cs` (outbound calls use request-level credentials, no propagated identity)

#### AUTH-Q5: Credential Management — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Credentials are stored in XML configuration file (`config.xml` managed by `ConfigFileProvider.cs`) and in the SQLite/PostgreSQL database (indexer, download client, and notification settings). No secrets management system integration (no AWS Secrets Manager, no HashiCorp Vault). The API key is a plaintext GUID in the config file. PostgreSQL password is stored in the config file or passed via environment variables (`Lidarr__Postgres__Password`). Environment variable support exists for PostgreSQL credentials but not for other secrets.
- **Gap**: No centralized secrets management. Credentials are stored in plaintext in config files and database. No rotation mechanism for stored third-party credentials.
- **Compensating Controls**:
  - Restrict filesystem permissions on `config.xml` and SQLite database file
  - Use environment variables for PostgreSQL credentials (already supported)
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement configuration provider that supports secrets manager integration for at minimum the API key and database password.
- **Evidence**: `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (XML config with ApiKey, PostgresPassword), `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` (plaintext connection strings)

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No sandbox or staging environment configuration exists in the repository. The CI/CD pipeline (`azure-pipelines.yml`) runs integration tests using temporary instances but does not maintain a persistent staging environment with production-equivalent data. The application supports separate database configuration for testing via environment variables, and `DbFactory.cs` handles database creation/migration, but there is no seed data or synthetic data generation for agent testing.
- **Gap**: No pre-configured sandbox environment for agent testing. Agents would need to be tested against a separate Lidarr instance manually configured by the operator.
- **Compensating Controls**:
  - Lidarr is easily deployed as a separate instance (self-hosted) — create a dedicated test instance for agent development
  - Use the existing integration test framework to create automated agent test scenarios
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a Docker Compose configuration for a sandbox Lidarr instance with seed data (sample artists, albums) for agent testing.
- **Evidence**: `azure-pipelines.yml` (integration tests use temporary instances), `src/NzbDrone.Core/Datastore/DbFactory.cs` (database creation but no seed data)

#### DATA-Q4: System of Record Designations — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Lidarr uses MusicBrainz (via SkyHook proxy) as the authoritative source for music metadata (artist names, album titles, release dates, track listings). The local database is the system of record for user configuration (quality profiles, root folders, monitored status) and download/import state. However, these designations are implicit in the code — not documented or exposed through API metadata.
- **Gap**: No explicit system-of-record designations documented. An agent cannot determine whether a field value is authoritative (from MusicBrainz) or user-configured (local) without understanding the application's architecture.
- **Compensating Controls**:
  - Document SoR designations in agent tool descriptions
  - Use metadata refresh commands to ensure local data is synchronized with MusicBrainz
- **Remediation Timeline**: 30 days (documentation)
- **Recommendation**: Add SoR metadata to API documentation or response headers indicating data provenance.
- **Evidence**: `src/Lidarr.Api.V1/openapi.json` (no provenance metadata), `src/NzbDrone.Core/Datastore/Migration/` (80+ migrations defining local schema)

#### DATA-Q5: Temporal Metadata and Freshness — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: `ModelBase.cs` defines only an `Id` field — no `CreatedAt`, `UpdatedAt`, or `LastModified` timestamps on the base entity. Some domain entities include temporal fields: albums have `ReleaseDate`, history records have timestamp fields, and the queue has status timestamps. However, there is no universal `updated_at` field across all entities, no `Cache-Control` or data-freshness headers in API responses, and no signal for whether data is current or cached.
- **Gap**: Inconsistent temporal metadata. No universal entity timestamps. No API-level data freshness indicators. An agent cannot determine when a record was last updated without domain-specific knowledge.
- **Compensating Controls**:
  - Use the History API (`/api/v1/history`) to check recent activity timestamps
  - Trigger metadata refresh commands before querying to ensure freshness
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add `CreatedAt` and `UpdatedAt` timestamps to `ModelBase`. Include `Last-Modified` headers in API responses.
- **Evidence**: `src/NzbDrone.Core/Datastore/ModelBase.cs` (Id field only), `src/NzbDrone.Core/Datastore/Migration/` (no universal timestamp migration)

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: API is versioned at the URL level (`/api/v1/`) via `VersionedApiControllerAttribute.cs`. OpenAPI 3.0.4 specification is auto-generated and committed (`openapi.json`). Database schema is versioned through 80+ numbered migrations. However: (1) No breaking change detection in CI — the pipeline generates and commits the OpenAPI spec but does not diff it for breaking changes. (2) No consumer-driven contract tests (Pact). (3) No deprecation notices or changelog for API changes.
- **Gap**: Schema versioning exists but breaking change detection is absent. API spec updates are committed automatically but not validated for backward compatibility. Agent tool bindings could break silently on API changes.
- **Compensating Controls**:
  - Pin agent tool definitions to known-good API schema versions
  - Monitor openapi.json changes in version control for breaking changes
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenAPI diff checking to the CI pipeline (e.g., `oasdiff` or `openapi-diff`) to detect breaking changes before merge.
- **Evidence**: `src/Lidarr.Http/VersionedApiControllerAttribute.cs` (/api/v1/), `src/Lidarr.Api.V1/openapi.json` (auto-generated), `azure-pipelines.yml` (Api_Docs job commits spec but no diff), `src/NzbDrone.Core/Datastore/Migration/` (numbered migrations)

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Lidarr uses NLog with multiple targets: file (text format with `FileLogLayout`), database (`DatabaseTarget.cs` writing to Logs table), Sentry (error reporting), and optional console (with CLEF structured format option). `LoggingMiddleware.cs` assigns an incrementing `ApiRequestSequenceID` per request — this provides request correlation within a single instance but is not a distributed trace ID. No OpenTelemetry, X-Ray, or W3C `traceparent` header propagation. Default log format is pipe-delimited text (`date|level|logger|message`), not structured JSON. CLEF format is available for console output only (`ConsoleLogFormat.Clef`).
- **Gap**: (1) No distributed tracing — request IDs are instance-local integers, not propagated across service boundaries. (2) Default logging is unstructured text, not JSON. (3) No trace context propagation for outbound HTTP calls.
- **Compensating Controls**:
  - Use CLEF console log format for structured output: set `LIDARR__LOG__CONSOLEFORMAT=Clef`
  - Correlate requests using the sequence ID in LoggingMiddleware for single-instance debugging
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add OpenTelemetry SDK and configure trace context propagation. Switch default log format to structured JSON.
- **Evidence**: `src/NzbDrone.Common/Instrumentation/NzbDroneLogger.cs` (FileLogLayout: pipe-delimited text, CLEF option for console), `src/Lidarr.Http/Middleware/LoggingMiddleware.cs` (integer sequence ID), `src/NzbDrone.Core/Instrumentation/DatabaseTarget.cs` (no trace ID in schema)

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Lidarr has a comprehensive `HealthCheckService.cs` with 20+ health checks (indexer connectivity, download client health, disk space, update availability, etc.) that run on startup, on schedule, and on relevant events. Health check failures trigger notifications (Discord, Telegram, Email, etc. via the notification framework). However, these are application-level self-checks — not infrastructure-level alerting on error rates, latency percentiles, or SLO-based thresholds. No CloudWatch, Prometheus, or Grafana integration. No alerting on API response time degradation.
- **Gap**: Health checks exist for application component health but not for API performance metrics. No alerting thresholds on error rates or latency for the APIs that agents would consume.
- **Compensating Controls**:
  - Health check results are available via `/api/v1/health` — agents can monitor this
  - Deploy external monitoring (e.g., Uptime Kuma, Prometheus blackbox exporter) against Lidarr API endpoints
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Expose Prometheus metrics endpoint with request count, error rate, and latency histograms. The ASP.NET Core metrics middleware can provide this with minimal effort.
- **Evidence**: `src/NzbDrone.Core/HealthCheck/HealthCheckService.cs` (application health checks), `src/NzbDrone.Core/Notifications/` (notification framework for health alerts)

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: `azure-pipelines.yml` defines a comprehensive multi-stage pipeline: Setup → Build Backend (Linux/Mac/Windows) → Build Frontend → Packages → Installer → Unit Tests (native + Docker + Postgres) → Integration Tests (native + Docker + FreeBSD + Postgres) → Automation Tests → Analyze (SonarCloud, Lint, API Docs). The Api_Docs job auto-generates the OpenAPI spec and commits changes. However: (1) No consumer-driven contract tests (Pact). (2) No OpenAPI diff/breaking change detection. (3) Integration tests validate API behavior but do not explicitly test contract stability.
- **Gap**: Comprehensive CI/CD exists but lacks explicit API contract testing. Breaking API changes are not automatically detected before merge.
- **Compensating Controls**:
  - The openapi.json auto-generation and commit process provides a de facto contract snapshot
  - Integration tests in `NzbDrone.Integration.Test/ApiTests/` cover core API behavior
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add an `oasdiff` or `openapi-diff` step to the PR pipeline that compares the generated openapi.json against the base branch and fails on breaking changes.
- **Evidence**: `azure-pipelines.yml` (Api_Docs job, Unit_Test stage, Integration stage), `src/NzbDrone.Integration.Test/ApiTests/` (15+ API test fixtures)

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Lidarr has a built-in auto-update mechanism (`InstallUpdateService.cs`, `UpdateEngine/`) that downloads and applies updates. `BackupService.cs` creates database backups before updates. However, there is no automated rollback mechanism — if an update breaks agent-facing APIs, rollback requires manual intervention (restore from backup, reinstall previous version). No blue/green, canary, or traffic-shifting deployment patterns (expected for a self-hosted desktop application).
- **Gap**: No automated rollback capability. Recovery from a breaking update requires manual backup restoration and version downgrade.
- **Compensating Controls**:
  - BackupService creates automatic backups (configurable retention) that can be restored manually
  - Pin to a known-good version by disabling auto-updates (`UpdateAutomatically = false` in config)
- **Remediation Timeline**: 60–90 days
- **Recommendation**: For a self-hosted application, the primary mitigation is version pinning. Document a rollback procedure for agent operators. Consider adding a "previous version" rollback command.
- **Evidence**: `src/NzbDrone.Core/Update/InstallUpdateService.cs`, `src/NzbDrone.Core/Backup/BackupService.cs` (backup before update), `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (UpdateAutomatically setting)

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The repository has multiple test projects: `NzbDrone.Core.Test` (unit tests), `NzbDrone.Integration.Test` (integration tests with 15+ API test fixtures covering Artist, Album, Blocklist, Calendar, Command, DownloadClient, History, Indexer, etc.), `NzbDrone.Automation.Test` (UI automation), and `NzbDrone.Api.Test` (API schema tests). The CI pipeline runs unit, integration, and automation tests across multiple platforms (Windows, Linux, Mac, FreeBSD) and database backends (SQLite, PostgreSQL 14, PostgreSQL 15). However: (1) No explicit contract tests for API schema stability. (2) Test coverage metrics from SonarCloud show API layer (`Lidarr.Api.V1`) is excluded from coverage analysis (`sonar.coverage.exclusions=**/Lidarr.Api.V1/**/*`).
- **Gap**: API integration tests exist but API test coverage is explicitly excluded from metrics. No contract tests validate that API responses match the OpenAPI specification.
- **Compensating Controls**:
  - Existing integration tests provide functional API validation across platforms
  - SonarCloud analysis covers core business logic
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Remove the API layer coverage exclusion from SonarCloud. Add contract tests that validate API responses against the OpenAPI spec.
- **Evidence**: `src/NzbDrone.Integration.Test/ApiTests/` (15+ fixtures), `azure-pipelines.yml` (SonarCloud: `sonar.coverage.exclusions=**/Lidarr.Api.V1/**/*`), `src/NzbDrone.Api.Test/` (schema tests)

#### ENG-Q5: Encryption at Rest — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: SQLite databases are stored as plaintext files on disk. `ConnectionStringFactory.cs` configures SQLite with WAL journal mode and connection pooling but no encryption (no SQLCipher, no SEE). PostgreSQL connections use plaintext connection strings without SSL/TLS enforcement (`NpgsqlConnectionStringBuilder` with no `SslMode` configuration). Stored credentials (indexer API keys, download client passwords, notification tokens) in the database `Settings` column are unencrypted JSON.
- **Gap**: No encryption at rest for the database files or sensitive fields within the database. A compromised filesystem exposes all stored credentials.
- **Compensating Controls**:
  - Rely on OS-level full-disk encryption (BitLocker, LUKS, FileVault) for the host machine
  - Restrict filesystem permissions on the Lidarr data directory
- **Remediation Timeline**: 90+ days
- **Recommendation**: Evaluate SQLCipher for SQLite encryption at rest. For PostgreSQL, configure SSL mode. Implement field-level encryption for credential storage.
- **Evidence**: `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` (no encryption config for SQLite or PostgreSQL), `src/NzbDrone.Core/Datastore/DbFactory.cs` (no encryption initialization)

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO (passes — no BLOCKER)
- **Finding**: Lidarr exposes a comprehensive REST API at `/api/v1/` with 40+ resource endpoints covering artists, albums, tracks, queue, history, commands, health, system, and more. An OpenAPI 3.0.4 specification (308KB, 13,102 lines) is auto-generated from Swagger annotations in `Startup.cs` and committed at `src/Lidarr.Api.V1/openapi.json`. Integration does not require direct database access — all operations are available through the documented API.
- **Implication**: The API surface is well-documented and agent-consumable. Tool definitions can be auto-generated from the OpenAPI spec.
- **Recommendation**: Use the OpenAPI spec as the basis for agent tool generation.
- **Evidence**: `src/Lidarr.Api.V1/openapi.json`, `src/NzbDrone.Host/Startup.cs` (SwaggerGen configuration), `src/Lidarr.Api.V1/` (40+ controller/resource directories)

### API-Q2: Machine-Readable API Specification

- **Severity**: INFO (passes — no RISK-QUALITY gap)
- **Finding**: OpenAPI 3.0.4 specification at `src/Lidarr.Api.V1/openapi.json` is auto-generated from code annotations via Swashbuckle/Swagger in `Startup.cs`. The spec is updated via the `Api_Docs` job in the CI pipeline and committed to the repository. It includes security definitions for X-Api-Key authentication, server configuration, and full schema definitions.
- **Implication**: Machine-readable API spec exists and is current. Agent tool generation can use this directly.
- **Recommendation**: Ensure the openapi.json stays synchronized with code changes (the CI pipeline handles this).
- **Evidence**: `src/Lidarr.Api.V1/openapi.json`, `azure-pipelines.yml` (Api_Docs job)

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Write endpoints (POST/PUT/DELETE for artists, albums, commands, etc.) do not implement idempotency keys. POST endpoints create new records without duplicate detection. The command system (`CommandController.cs`) allows duplicate command submissions. However, since agent_scope is read-only, idempotency of write operations is informational only.
- **Implication**: If agent scope expands to write-enabled, idempotency will become a BLOCKER. Plan for idempotency key support in write endpoints.
- **Recommendation**: Add idempotency key header support (e.g., `X-Idempotency-Key`) to write endpoints proactively.
- **Evidence**: `src/Lidarr.Api.V1/Artist/ArtistController.cs` (AddArtist: no idempotency check), `src/Lidarr.Api.V1/Commands/CommandController.cs` (StartCommand: no duplicate prevention)

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: All API responses are JSON, serialized via `System.Text.Json` with custom settings applied in `Startup.cs` (`STJson.ApplySerializerSettings`). Response content type is `application/json`. No XML, binary, or protobuf formats are used. Naming convention is camelCase.
- **Implication**: JSON responses are directly consumable by LLM-based agents without additional parsing.
- **Recommendation**: No action needed.
- **Evidence**: `src/NzbDrone.Host/Startup.cs` (AddJsonOptions with STJson settings), `src/Lidarr.Api.V1/Artist/ArtistController.cs` ([Produces("application/json")])

### API-Q7: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: Lidarr has comprehensive event emission: (1) SignalR hub (`MessageHub.cs`) broadcasts real-time state changes to connected clients. (2) Webhook notification system (`src/NzbDrone.Core/Notifications/Webhook/`) supports HTTP callbacks for events (grab, import, rename, delete, health status changes). (3) The notification framework supports 20+ channels (Discord, Telegram, Slack, Email, Plex, etc.) for event notifications. All state-changing operations publish events via the `IEventAggregator`.
- **Implication**: Rich event emission exists for building reactive agent patterns. SignalR provides real-time updates; webhooks provide async notifications.
- **Recommendation**: Use SignalR for real-time agent state monitoring. Configure webhooks for event-driven agent workflows.
- **Evidence**: `src/NzbDrone.SignalR/MessageHub.cs`, `src/NzbDrone.Core/Notifications/Webhook/` (15+ webhook payload types), `src/Lidarr.Api.V1/Artist/ArtistController.cs` (BroadcastResourceChange on all state changes)

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limit headers (`X-RateLimit-Remaining`, `Retry-After`) are returned in API responses. No rate limit documentation exists in the OpenAPI spec. The application does not enforce or communicate rate limits to API consumers.
- **Implication**: Agents cannot self-throttle based on rate limit signals from the API. Agent orchestration must implement rate limiting externally.
- **Recommendation**: Add rate limit headers to API responses when rate limiting is implemented (see STATE-Q5).
- **Evidence**: `src/NzbDrone.Host/Startup.cs` (no rate limit headers middleware), `src/Lidarr.Api.V1/openapi.json` (no rate limit documentation)

### STATE-Q2: Queryable Current State

- **Severity**: INFO (passes — no RISK gap)
- **Finding**: All major entities expose GET endpoints for querying current state: `/api/v1/artist` (with optional mbId filter), `/api/v1/album` (with artistId and albumIds filters), `/api/v1/queue` (with paging), `/api/v1/history` (with paging and filters), `/api/v1/command` (list all commands with status), `/api/v1/health` (system health), `/api/v1/system/status` (system info). State is fully queryable before taking action.
- **Implication**: Agents can fully inspect system state before deciding on actions. Read-before-act patterns are well supported.
- **Recommendation**: No action needed.
- **Evidence**: `src/Lidarr.Api.V1/Artist/ArtistController.cs` (AllArtists GET), `src/Lidarr.Api.V1/Commands/CommandController.cs` (GetStartedCommands GET), `src/Lidarr.Http/PagingResource.cs` (pagination support)

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No optimistic locking (version fields, ETags, `If-Match` headers) on write endpoints. `BasicRepository.cs` uses simple `WHERE Id = @Id` updates without version checks. SQLite WAL mode provides database-level concurrency. Polly retry strategy handles SQLite busy errors. No explicit concurrency controls for preventing concurrent write conflicts.
- **Implication**: If agent scope expands to write-enabled with multiple concurrent agents, race conditions on updates are possible. Plan for optimistic locking on critical entities.
- **Recommendation**: Add version fields to entities and ETag support on write endpoints before expanding to write-enabled agent scope.
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs` (no version field, Polly retry for busy), `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` (WAL mode)

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits (max records per operation, max spend, max deletes). Bulk operations in BasicRepository process unlimited items. No per-agent operation quotas.
- **Implication**: If agent scope expands to write-enabled, there is no blast radius containment. An agent could execute unlimited write operations.
- **Recommendation**: Implement configurable per-agent operation limits before enabling write scope.
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs` (InsertMany/UpdateMany/DeleteMany: no limits)

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Lidarr has implicit pending states: (1) Commands have status lifecycle (Queued → Started → Completed/Failed). (2) PendingReleaseService manages releases awaiting download delay. (3) Queue items have status (Downloading, Paused, Completed). However, these are operational states, not human-approval draft states.
- **Implication**: The command queue provides a natural integration point for draft/approval patterns if needed in the future.
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: `src/Lidarr.Api.V1/Commands/CommandController.cs`, `src/NzbDrone.Core/Download/Pending/PendingReleaseService.cs`

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable approval gates exist. Operations execute immediately upon API call. The command queue processes commands without human approval steps.
- **Implication**: If agent scope expands to write-enabled, approval gates should be considered for high-risk operations (e.g., delete artist, bulk imports).
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: `src/Lidarr.Api.V1/Commands/CommandController.cs` (immediate command execution)

### DATA-Q3: Selective Query Support

- **Severity**: INFO (passes — no RISK-QUALITY gap)
- **Finding**: `PagingResource.cs` implements pagination with `Page` (default 1), `PageSize` (default 10), `SortKey`, and `SortDirection`. Controllers like `HistoryController`, `QueueController`, and `WantedController` use paged queries. Additional filtering is available via query parameters (e.g., `artistId`, `albumIds`). `BasicRepository.GetPaged()` implements `LIMIT/OFFSET` pagination with filter expressions.
- **Implication**: Agents can retrieve bounded result sets with pagination and filtering. LLM context window overflow is manageable.
- **Recommendation**: No action needed. Pagination and filtering are well-implemented.
- **Evidence**: `src/Lidarr.Http/PagingResource.cs`, `src/NzbDrone.Core/Datastore/BasicRepository.cs` (GetPaged with LIMIT/OFFSET)

### DATA-Q6: PII Redaction in Logs

- **Severity**: INFO (passes — RISK-SAFETY but no gap)
- **Finding**: `CleanseLogMessage.cs` implements comprehensive log scrubbing with 25+ regex patterns that redact: API keys and tokens (query parameters and JSON), passwords (URL parameters and JSON values), tracker announce keys, file paths with usernames (Windows and Unix), NzbGet/Sabnzbd/uTorrent/Deluge credentials, Discord webhook URLs, Telegram bot tokens, and remote IP addresses (partial redaction). The `CleansingConsoleLogLayout` and `CleansingFileTarget` apply cleansing to all console and file log output. `DatabaseTarget.cs` calls `CleanseLogMessage.Cleanse()` on both message and exception before database storage. Sentry integration sends sanitized events.
- **Implication**: Log scrubbing is thorough and applied consistently across all log targets. This is a strong implementation for a self-hosted application.
- **Recommendation**: No immediate action. Periodically review cleansing rules as new integrations are added.
- **Evidence**: `src/NzbDrone.Common/Instrumentation/CleanseLogMessage.cs` (25+ regex rules), `src/NzbDrone.Core/Instrumentation/DatabaseTarget.cs` (Cleanse calls), `src/NzbDrone.Common/Instrumentation/NzbDroneLogger.cs` (CleansingConsoleLogLayout, CleansingFileTarget)

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No formal data quality metrics, completeness monitoring, or data profiling. The health check system monitors component connectivity (indexers, download clients) but not data quality. MusicBrainz metadata quality is inherited from the upstream source without local quality scoring.
- **Implication**: Agents reasoning on incomplete music metadata (missing albums, incorrect track counts) would have no signal for data quality.
- **Recommendation**: Consider exposing artist/album completeness metrics via the statistics endpoints already in use.
- **Evidence**: `src/NzbDrone.Core/HealthCheck/HealthCheckService.cs` (component health only), `src/NzbDrone.Core/ArtistStats/` (statistics service exists but no quality metrics)

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Field names in API resources and database models are human-readable and semantically meaningful: `ArtistName`, `AlbumTitle`, `ReleaseDate`, `TrackTitle`, `QualityProfileId`, `MetadataProfileId`, `Monitored`, `Path`, `Statistics`, `ForeignArtistId`. No legacy abbreviations or codes requiring a data dictionary.
- **Implication**: LLM-based agents can reason about field names without a lookup table. Tool descriptions can use field names directly.
- **Recommendation**: No action needed. Naming conventions are clear and consistent.
- **Evidence**: `src/Lidarr.Api.V1/Artist/ArtistController.cs`, `src/Lidarr.Api.V1/openapi.json` (schema definitions)

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: The OpenAPI specification serves as the primary API catalog. No formal data catalog (Glue, Collibra, DataHub) exists. Database schema is documented implicitly through the migration files and `TableMapping.cs` but not through an external metadata layer.
- **Implication**: Agent tool builders must rely on the OpenAPI spec and code inspection for understanding data semantics. No self-service discovery mechanism.
- **Recommendation**: The OpenAPI spec is sufficient for agent tool generation. Consider adding field-level descriptions to the OpenAPI spec for improved agent understanding.
- **Evidence**: `src/Lidarr.Api.V1/openapi.json`, `src/NzbDrone.Core/Datastore/Migration/` (80+ migrations)

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No custom business outcome metrics are published. The application tracks internal statistics (ArtistStatistics: album counts, track counts, size on disk) but does not publish metrics to external monitoring systems. No Prometheus, CloudWatch, or StatsD integration. The Sentry integration captures errors but not business KPIs.
- **Implication**: When agents interact with Lidarr, there is no metric pipeline to measure whether agent actions produce good business outcomes (e.g., successful imports per agent session, failed searches, queue efficiency).
- **Recommendation**: Expose internal statistics as Prometheus metrics. Track agent-initiated operations as a separate metric dimension.
- **Evidence**: `src/NzbDrone.Core/ArtistStats/` (internal statistics), `src/NzbDrone.Common/Instrumentation/NzbDroneLogger.cs` (Sentry for errors only)

### ENG-Q1: Infrastructure Governance

- **Severity**: INFO
- **Finding**: Lidarr is a self-hosted desktop/server application distributed as standalone packages (ZIP, TAR, DMG, installers). No cloud infrastructure is defined — no Terraform, CloudFormation, CDK, Helm, or Kubernetes manifests exist in the repository. The application is deployed by end users on their own infrastructure. PR-based code review is enforced via GitHub (`.github/PULL_REQUEST_TEMPLATE.md` exists). The Azure Pipelines CI/CD validates all code changes.
- **Implication**: IaC governance is not applicable for this deployment model. Agent operators who deploy Lidarr in cloud environments (Docker, Kubernetes) should manage their own IaC. The application itself does not dictate infrastructure.
- **Recommendation**: For agent integration, create IaC templates (Terraform/CDK modules, Helm charts) that deploy Lidarr with appropriate network policies, rate limiting, and monitoring — this would be agent-operator infrastructure, not application infrastructure.
- **Evidence**: Repository root (no IaC files), `azure-pipelines.yml` (CI/CD exists), `.github/PULL_REQUEST_TEMPLATE.md` (PR review process)

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: BLOCKER (resolved: passes — no gap)
- **Finding**: Lidarr exposes a comprehensive REST API at `/api/v1/` with 40+ resource endpoints. OpenAPI 3.0.4 spec at `openapi.json`. No direct DB access required.
- **Gap**: None — API surface is well-documented.
- **Recommendation**: Use OpenAPI spec for agent tool generation.
- **Evidence**: `src/Lidarr.Api.V1/openapi.json`, `src/NzbDrone.Host/Startup.cs`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY (resolved: passes — no gap)
- **Finding**: OpenAPI 3.0.4 spec auto-generated via Swashbuckle, committed in repo, updated via CI.
- **Gap**: None — machine-readable spec exists and is current.
- **Recommendation**: Maintain CI-driven spec generation.
- **Evidence**: `src/Lidarr.Api.V1/openapi.json`, `azure-pipelines.yml`

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: ErrorModel has Message/Description/Content. HTTP status codes mapped by exception type. No error codes or retryable indicator.
- **Gap**: No machine-readable error code or retryable boolean.
- **Recommendation**: Add ErrorCode enum and IsRetryable to ErrorModel.
- **Evidence**: `src/Lidarr.Http/ErrorManagement/ErrorModel.cs`, `src/Lidarr.Http/ErrorManagement/LidarrErrorPipeline.cs`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No idempotency keys on write endpoints. Not relevant for read-only agent scope.
- **Gap**: Write endpoints lack idempotency (informational for read-only scope).
- **Recommendation**: Plan idempotency key support before write-enabled scope expansion.
- **Evidence**: `src/Lidarr.Api.V1/Artist/ArtistController.cs`, `src/Lidarr.Api.V1/Commands/CommandController.cs`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: All responses are JSON via System.Text.Json. camelCase convention.
- **Gap**: None.
- **Recommendation**: No action needed.
- **Evidence**: `src/NzbDrone.Host/Startup.cs`

#### API-Q6: Asynchronous Operation Support
- **Severity**: RISK-QUALITY
- **Finding**: Command queue with status polling and SignalR exist but don't follow REST async best practices (202 Accepted + Location header).
- **Gap**: Non-standard async pattern.
- **Recommendation**: Return 202 Accepted with Location header for command submissions.
- **Evidence**: `src/Lidarr.Api.V1/Commands/CommandController.cs`, `src/NzbDrone.SignalR/MessageHub.cs`

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: SignalR real-time events, Webhook notifications, 20+ notification channels. Comprehensive event emission.
- **Gap**: None — event emission is well-implemented.
- **Recommendation**: Use SignalR and webhooks for reactive agent patterns.
- **Evidence**: `src/NzbDrone.SignalR/MessageHub.cs`, `src/NzbDrone.Core/Notifications/Webhook/`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit headers or documentation in API responses.
- **Gap**: Agents cannot self-throttle based on server signals.
- **Recommendation**: Add rate limit headers when rate limiting is implemented.
- **Evidence**: `src/NzbDrone.Host/Startup.cs`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: Single shared API key with generic claim. No per-agent identity or principal attribution.
- **Gap**: No machine identity model. All callers indistinguishable.
- **Recommendation**: Implement multi-key API authentication with named principals.
- **Evidence**: `src/Lidarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: All-or-nothing API key. No role definitions or permission scopes.
- **Gap**: No scoped permissions model.
- **Recommendation**: Implement role-based API key tiers.
- **Evidence**: `src/Lidarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/NzbDrone.Host/Startup.cs`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: No RBAC, ABAC, or method-level authorization. Binary auth check only.
- **Gap**: No action-level access control.
- **Recommendation**: Add authorization attributes to controller actions.
- **Evidence**: `src/Lidarr.Http/REST/RestController.cs`, `src/Lidarr.Api.V1/Artist/ArtistController.cs`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: RISK-QUALITY
- **Finding**: Outbound calls use stored service credentials, no caller identity propagation.
- **Gap**: No identity propagation or on-behalf-of flows.
- **Recommendation**: Low priority for P2 self-hosted app.
- **Evidence**: `src/NzbDrone.Common/Http/HttpClient.cs`

#### AUTH-Q5: Credential Management
- **Severity**: RISK-QUALITY
- **Finding**: Credentials in XML config and database. No secrets manager. Environment variable support for PostgreSQL only.
- **Gap**: No centralized secrets management.
- **Recommendation**: Implement secrets manager integration.
- **Evidence**: `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`, `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Logs request metadata but not authenticated principal. No immutable log storage.
- **Gap**: No principal attribution in logs. Mutable log storage.
- **Recommendation**: Add principal to log entries. Forward to immutable storage.
- **Evidence**: `src/Lidarr.Http/Middleware/LoggingMiddleware.cs`, `src/NzbDrone.Core/Instrumentation/DatabaseTarget.cs`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: ResetApiKeyCommand regenerates single global key. Cannot suspend individual agents.
- **Gap**: No per-agent identity suspension.
- **Recommendation**: Implement multi-key system with individual revocation.
- **Evidence**: `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Command queue without compensation. Multi-step operations not transactional.
- **Gap**: No saga pattern or undo endpoints.
- **Recommendation**: Implement compensation handlers for critical workflows.
- **Evidence**: `src/Lidarr.Api.V1/Commands/CommandController.cs`, `src/NzbDrone.Core/Backup/BackupService.cs`

#### STATE-Q2: Queryable Current State
- **Severity**: RISK-QUALITY (resolved: passes — no gap)
- **Finding**: Comprehensive GET endpoints for all major entities with filtering and pagination.
- **Gap**: None — state is fully queryable.
- **Recommendation**: No action needed.
- **Evidence**: `src/Lidarr.Api.V1/Artist/ArtistController.cs`, `src/Lidarr.Http/PagingResource.cs`

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No optimistic locking. SQLite WAL provides base concurrency.
- **Gap**: No version fields or ETags (informational for read-only scope).
- **Recommendation**: Add optimistic locking before write-enabled scope.
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: Partial resilience: Polly retry for SQLite, ProviderStatusServiceBase escalation backoff, outbound rate limiting. No formal circuit breakers on HTTP calls.
- **Gap**: Incomplete circuit breaker pattern on external service calls.
- **Recommendation**: Add Polly CircuitBreakerPolicy to outbound HTTP calls.
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs`, `src/NzbDrone.Core/ThingiProvider/Status/ProviderStatusServiceBase.cs`, `src/NzbDrone.Common/Http/HttpClient.cs`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No inbound API rate limiting. RateLimitService is outbound only.
- **Gap**: No protection against runaway agent loops.
- **Recommendation**: Add ASP.NET Core rate limiting middleware.
- **Evidence**: `src/NzbDrone.Host/Startup.cs`, `src/NzbDrone.Common/TPL/RateLimitService.cs`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits or per-agent quotas.
- **Gap**: No blast radius containment (informational for read-only scope).
- **Recommendation**: Implement limits before write-enabled scope.
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path. (Priority is P2, not on critical path.)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Command queue has status lifecycle. PendingReleaseService manages release delays. Not approval-based drafts.
- **Gap**: No human-approval draft states (informational for read-only scope).
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: `src/Lidarr.Api.V1/Commands/CommandController.cs`

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No approval gates. Operations execute immediately.
- **Gap**: No configurable approval workflow (informational for read-only scope).
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: `src/Lidarr.Api.V1/Commands/CommandController.cs`

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: No sandbox or staging environment. CI uses temporary instances for testing.
- **Gap**: No pre-configured agent testing environment.
- **Recommendation**: Create Docker Compose sandbox with seed data.
- **Evidence**: `azure-pipelines.yml`, `src/NzbDrone.Core/Datastore/DbFactory.cs`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification ⚡ (Tiered)
- **Severity**: BLOCKER
- **Finding**: B1 BLOCKER for `HostConfigResource` — `GET /api/v1/config/host` returns master `ApiKey`, admin `Password`, `SslCertPassword`, `ProxyPassword` unmasked. Provider settings (indexer/download client/notification) ARE properly masked via `PrivacyLevel` + `SchemaBuilder`. B2 RISK-SAFETY (single global API key). B3 partial. See BLOCKERs section above.
- **Gap**: Coverage gap in the `HostConfigResource` path; the masking primitive exists and works for provider settings.
- **Recommendation**: Mask credential fields in `HostConfigResourceMapper.ToResource()`.
- **Evidence**: `src/Lidarr.Api.V1/Config/HostConfigResource.cs`, `src/Lidarr.Api.V1/Config/HostConfigController.cs`, `src/Lidarr.Http/ClientSchema/SchemaBuilder.cs:38-44`.

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Self-hosted app. No residency controls or region awareness.
- **Gap**: No data residency enforcement.
- **Recommendation**: Document residency considerations for agent integration.
- **Evidence**: `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs`, `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK-QUALITY (resolved: passes — no gap)
- **Finding**: PagingResource with Page, PageSize, SortKey, SortDirection. Query filters on controllers.
- **Gap**: None — pagination and filtering are well-implemented.
- **Recommendation**: No action needed.
- **Evidence**: `src/Lidarr.Http/PagingResource.cs`, `src/NzbDrone.Core/Datastore/BasicRepository.cs`

#### DATA-Q4: System of Record Designations
- **Severity**: RISK-QUALITY
- **Finding**: MusicBrainz for metadata, local DB for user config. Implicit, not documented.
- **Gap**: No explicit SoR designations in API or docs.
- **Recommendation**: Document SoR in agent tool descriptions.
- **Evidence**: `src/Lidarr.Api.V1/openapi.json`

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK-QUALITY
- **Finding**: ModelBase has Id only, no universal timestamps. Some entities have dates. No freshness headers.
- **Gap**: Inconsistent temporal metadata. No data freshness signaling.
- **Recommendation**: Add CreatedAt/UpdatedAt to ModelBase. Add Last-Modified headers.
- **Evidence**: `src/NzbDrone.Core/Datastore/ModelBase.cs`

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY (resolved: passes — no gap)
- **Finding**: CleanseLogMessage.cs has 25+ regex rules for comprehensive log scrubbing. Applied to all log targets.
- **Gap**: None — log scrubbing is thorough and consistent.
- **Recommendation**: Periodically review cleansing rules.
- **Evidence**: `src/NzbDrone.Common/Instrumentation/CleanseLogMessage.cs`, `src/NzbDrone.Core/Instrumentation/DatabaseTarget.cs`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No formal data quality metrics or completeness monitoring.
- **Gap**: No data quality signals for agents.
- **Recommendation**: Expose completeness metrics via statistics endpoints.
- **Evidence**: `src/NzbDrone.Core/HealthCheck/HealthCheckService.cs`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: /api/v1/ URL versioning, OpenAPI spec auto-generated, 80+ migrations. No breaking change detection in CI.
- **Gap**: No automated breaking change detection for API contracts.
- **Recommendation**: Add OpenAPI diff step to CI pipeline.
- **Evidence**: `src/Lidarr.Http/VersionedApiControllerAttribute.cs`, `src/Lidarr.Api.V1/openapi.json`, `azure-pipelines.yml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Clear, human-readable field names (ArtistName, AlbumTitle, etc.). No legacy abbreviations.
- **Gap**: None.
- **Recommendation**: No action needed.
- **Evidence**: `src/Lidarr.Api.V1/openapi.json`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: OpenAPI spec as primary catalog. No formal data catalog.
- **Gap**: No self-service data discovery.
- **Recommendation**: Add field-level descriptions to OpenAPI spec.
- **Evidence**: `src/Lidarr.Api.V1/openapi.json`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: NLog with text format, instance-local sequence IDs, Sentry integration. No OpenTelemetry. CLEF format optional for console.
- **Gap**: No distributed tracing. Default logs are unstructured text.
- **Recommendation**: Add OpenTelemetry SDK and structured JSON logging.
- **Evidence**: `src/NzbDrone.Common/Instrumentation/NzbDroneLogger.cs`, `src/Lidarr.Http/Middleware/LoggingMiddleware.cs`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: HealthCheckService with 20+ checks and notification integration. No API performance metrics or alerting.
- **Gap**: No alerting on API error rates or latency.
- **Recommendation**: Expose Prometheus metrics endpoint.
- **Evidence**: `src/NzbDrone.Core/HealthCheck/HealthCheckService.cs`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: Internal statistics exist (ArtistStatistics) but not published to external monitoring. No Prometheus/CloudWatch.
- **Gap**: No business metric pipeline.
- **Recommendation**: Expose internal statistics as Prometheus metrics.
- **Evidence**: `src/NzbDrone.Core/ArtistStats/`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: INFO (self-hosted app — no cloud IaC applicable)
- **Finding**: Self-hosted desktop/server app. No cloud IaC in repo. PR review and CI/CD exist for code changes.
- **Gap**: No IaC (expected for self-hosted deployment model).
- **Recommendation**: Agent operators should create their own IaC for deploying Lidarr.
- **Evidence**: Repository root (no IaC), `azure-pipelines.yml`, `.github/PULL_REQUEST_TEMPLATE.md`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive Azure Pipelines CI/CD. No API contract tests or breaking change detection.
- **Gap**: No automated API contract validation.
- **Recommendation**: Add OpenAPI diff step to pipeline.
- **Evidence**: `azure-pipelines.yml`, `src/NzbDrone.Integration.Test/ApiTests/`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: Auto-update with pre-update backups. No automated rollback. Manual restore required.
- **Gap**: No automated rollback mechanism.
- **Recommendation**: Version pinning and documented rollback procedure.
- **Evidence**: `src/NzbDrone.Core/Update/InstallUpdateService.cs`, `src/NzbDrone.Core/Backup/BackupService.cs`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: Integration tests cover 15+ API endpoints across platforms. API layer excluded from SonarCloud coverage.
- **Gap**: API coverage excluded from metrics. No contract tests.
- **Recommendation**: Include API layer in coverage. Add contract tests.
- **Evidence**: `src/NzbDrone.Integration.Test/ApiTests/`, `azure-pipelines.yml`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: RISK-QUALITY
- **Finding**: SQLite files unencrypted. PostgreSQL connections without SSL enforcement. Credentials stored as plaintext JSON.
- **Gap**: No encryption at rest for database or sensitive fields.
- **Recommendation**: Evaluate SQLCipher for SQLite. Configure PostgreSQL SSL. Implement field-level encryption.
- **Evidence**: `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs`, `src/NzbDrone.Core/Datastore/DbFactory.cs`

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `src/Lidarr.Http/Authentication/ApiKeyAuthenticationHandler.cs` | AUTH-Q1, AUTH-Q2, AUTH-Q3 |
| `src/Lidarr.Http/Authentication/AuthenticationBuilderExtensions.cs` | AUTH-Q1 |
| `src/Lidarr.Http/Authentication/AuthenticationService.cs` | AUTH-Q6 |
| `src/Lidarr.Http/ErrorManagement/ErrorModel.cs` | API-Q3 |
| `src/Lidarr.Http/ErrorManagement/LidarrErrorPipeline.cs` | API-Q3 |
| `src/Lidarr.Http/REST/RestController.cs` | AUTH-Q3 |
| `src/Lidarr.Http/PagingResource.cs` | DATA-Q3, STATE-Q2 |
| `src/Lidarr.Http/Middleware/LoggingMiddleware.cs` | AUTH-Q1, AUTH-Q6, OBS-Q1 |
| `src/Lidarr.Http/VersionedApiControllerAttribute.cs` | DISC-Q1 |
| `src/NzbDrone.Host/Startup.cs` | API-Q1, API-Q2, API-Q5, AUTH-Q2, AUTH-Q3, STATE-Q5, API-Q8 |
| `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` | AUTH-Q1, AUTH-Q5, AUTH-Q7, DATA-Q1, DATA-Q2 |
| `src/NzbDrone.Core/Datastore/BasicRepository.cs` | STATE-Q1, STATE-Q3, STATE-Q4, STATE-Q6, DATA-Q3 |
| `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` | AUTH-Q5, DATA-Q1, DATA-Q2, ENG-Q5, STATE-Q3 |
| `src/NzbDrone.Core/Datastore/DbFactory.cs` | HITL-Q3, ENG-Q5 |
| `src/NzbDrone.Core/Datastore/ModelBase.cs` | DATA-Q5 |
| `src/NzbDrone.Core/Instrumentation/DatabaseTarget.cs` | AUTH-Q6, OBS-Q1, DATA-Q6 |
| `src/NzbDrone.Core/ThingiProvider/Status/ProviderStatusServiceBase.cs` | STATE-Q4 |
| `src/NzbDrone.Core/HealthCheck/HealthCheckService.cs` | OBS-Q2, DATA-Q7 |
| `src/NzbDrone.Core/Backup/BackupService.cs` | STATE-Q1, ENG-Q3 |
| `src/NzbDrone.Core/Update/InstallUpdateService.cs` | ENG-Q3 |
| `src/NzbDrone.Common/Http/HttpClient.cs` | STATE-Q4, AUTH-Q4 |
| `src/NzbDrone.Common/TPL/RateLimitService.cs` | STATE-Q4, STATE-Q5 |
| `src/NzbDrone.Common/Instrumentation/CleanseLogMessage.cs` | DATA-Q6 |
| `src/NzbDrone.Common/Instrumentation/NzbDroneLogger.cs` | OBS-Q1, DATA-Q6, OBS-Q3 |
| `src/NzbDrone.SignalR/MessageHub.cs` | API-Q6, API-Q7 |
| `src/Lidarr.Api.V1/Artist/ArtistController.cs` | API-Q1, API-Q4, AUTH-Q3, API-Q7, DISC-Q2 |
| `src/Lidarr.Api.V1/Commands/CommandController.cs` | API-Q4, API-Q6, STATE-Q1, HITL-Q1, HITL-Q2 |
| `src/NzbDrone.Core/Download/Pending/PendingReleaseService.cs` | HITL-Q1 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `src/Lidarr.Api.V1/openapi.json` | API-Q1, API-Q2, DATA-Q1, DATA-Q4, DISC-Q1, DISC-Q2, DISC-Q3, API-Q8 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `azure-pipelines.yml` | API-Q2, DISC-Q1, ENG-Q1, ENG-Q2, ENG-Q4, HITL-Q3 |
| `.github/PULL_REQUEST_TEMPLATE.md` | ENG-Q1 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `package.json` | Discovery (frontend dependencies) |
| `global.json` | Discovery (.NET 8.0.405 target) |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` | AUTH-Q1, AUTH-Q5, AUTH-Q7, DATA-Q1, DATA-Q2, ENG-Q3 |

### Notification / Webhook Sources
| File | Questions Referenced |
|------|---------------------|
| `src/NzbDrone.Core/Notifications/Webhook/` | API-Q7 |
| `src/NzbDrone.Core/Notifications/` | OBS-Q2 |

### Test Projects
| File | Questions Referenced |
|------|---------------------|
| `src/NzbDrone.Integration.Test/ApiTests/` | ENG-Q2, ENG-Q4 |
| `src/NzbDrone.Api.Test/` | ENG-Q4 |

### Database Migrations
| File | Questions Referenced |
|------|---------------------|
| `src/NzbDrone.Core/Datastore/Migration/` | DISC-Q1, DATA-Q5, DISC-Q3 |
