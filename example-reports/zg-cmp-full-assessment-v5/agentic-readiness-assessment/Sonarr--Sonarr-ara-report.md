# Agentic Readiness Assessment Report

**Target**: Sonarr (TV-series PVR for usenet and BitTorrent users)
**Date**: 2025-07-14
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: monorepo (single-service: treated as application — all 43 questions apply)
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: csharp, media, desktop
**Context**: TV-series PVR for usenet and BitTorrent users (*arr suite).

**Archetype Justification**: Sonarr has SQLite/PostgreSQL database connections (NzbDrone.Core/Datastore), exposes CRUD REST APIs for Series, Episodes, EpisodeFiles, and Commands (Sonarr.Api.V3, Sonarr.Api.V5), and manages user-specific configuration data. This matches the stateful-crud archetype.

**Surface flags**:
- has_persistent_data_store: true (SQLite/PostgreSQL — NzbDrone.Core/Datastore)
- has_http_rpc_surface: true (ASP.NET Core REST API — Sonarr.Api.V3, Sonarr.Api.V5)
- has_auth_surface: true (API key auth, Forms auth — Sonarr.Http/Authentication)
- has_write_operations: true (POST/PUT/DELETE endpoints for Series, Episodes, Commands)
- has_logging_of_user_data: true (LoggingMiddleware logs request paths including IP addresses)

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 2 | **RISK-SAFETY**: 9 | **RISK-QUALITY**: 13 | **INFOs**: 15

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days. The two BLOCKERs (AUTH-Q1: machine identity without per-agent attribution, DATA-Q1: unclassified sensitive credentials in database) must be resolved before any agent integration — including read-only pilots. Once BLOCKERs are resolved, the 9 RISK-SAFETY findings will require compensating controls for a supervised pilot.

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 2 |
| RISK-SAFETY | 9 |
| RISK-QUALITY | 13 |
| INFO | 15 |
| N/A | 0 |
| Not Evaluated (extended) | 4 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 15
**Extended Questions Not Triggered**: 4
**Questions N/A (repo_type: monorepo)**: 0
**Service Archetype**: stateful-crud (auto-detected)

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: Sonarr supports API key authentication via `ApiKeyAuthenticationHandler.cs` using the `X-Api-Key` header or `apikey` query parameter. However, a single shared API key is used for all API consumers. When authenticated, the only claim set is `new Claim("ApiKey", "true")` — there is no per-agent principal attribution. All API key consumers appear as the same identity. No `user_id`, `agent_id`, or distinguishing claim is attached to API key authentication.
- **Gap**: No mechanism exists to distinguish which agent (or consumer) made a given API call. All API key holders share the same identity claim. Audit and forensics cannot attribute actions to a specific agent instance.
- **Remediation**:
  - **Immediate**: Implement support for multiple named API keys, each with a unique principal identifier claim (e.g., `agent_name` or `client_id`). Modify `ApiKeyAuthenticationHandler` to look up the API key against a table of registered keys and attach the corresponding identity claims.
  - **Target State**: Each agent identity has its own API key with distinguishable claims in the authentication ticket. Audit logs can attribute every API call to a specific agent instance.
  - **Estimated Effort**: Medium (2–4 weeks)
  - **Dependencies**: AUTH-Q6 (audit logging) — attribution is meaningless without logs that record it.
- **Evidence**: `src/Sonarr.Http/Authentication/ApiKeyAuthenticationHandler.cs` (lines 59–67: single claim `ApiKey: true`), `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (single `ApiKey` property)

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: **Stage A: Yes** — Sonarr stores sensitive data in its database. Download client credentials (passwords, API keys), indexer API keys, and notification webhook URLs are stored as provider settings via `ProviderDefinition` / `ProviderSettingConverter`. PostgreSQL connection passwords are stored in the XML config file. **Stage B:** No field-level data classification exists. No data tagging in the database schema. No encryption at the field level for credentials stored in provider settings. Download client passwords and indexer API keys are stored in the `Settings` JSON column without field-level encryption or classification controls.
- **Gap**: Sensitive credentials stored in the database are not classified, tagged, or protected with field-level controls. An agent with read access to the API could potentially retrieve provider settings that include embedded credentials.
- **Remediation**:
  - **Immediate**: Classify the `Settings` column in provider-related tables as containing credentials. Implement API-level response filtering to redact credential fields (passwords, API keys) from API responses unless explicitly requested by an elevated identity.
  - **Target State**: All fields containing credentials are classified as `sensitive/credential`, redacted from API responses by default, and optionally encrypted at the field level in the database.
  - **Estimated Effort**: Medium (3–6 weeks)
  - **Dependencies**: AUTH-Q1 (per-agent identity) — field-level access control requires distinguishable identities.
- **Evidence**: `src/NzbDrone.Core/ThingiProvider/ProviderDefinition.cs`, `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (PostgresPassword, ApiKey properties), `src/NzbDrone.Core/Datastore/` (no field-level encryption or classification)

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Sonarr uses a single API key that grants full access to all API endpoints. There are no scoped permissions, role definitions, or resource-level access controls for API key consumers. No IAM policies exist (desktop application, no cloud infrastructure). The API key either grants full access or no access.
- **Gap**: No mechanism to grant an agent read-only access to specific resources (e.g., read Series but not modify Download Clients). All API key holders have identical, unlimited access.
- **Compensating Controls**:
  - Deploy a reverse proxy (e.g., nginx, API gateway) in front of Sonarr that filters HTTP methods and paths per API key
  - Use network segmentation to restrict agent access to specific Sonarr endpoints
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement role-based API key scoping — define permission levels (read-only, read-write, admin) and associate each API key with a permission set.
- **Evidence**: `src/Sonarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/NzbDrone.Host/Startup.cs` (FallbackPolicy requires authenticated user but no permission checks)

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization exists for API key consumers. Once authenticated with a valid API key, any HTTP method (GET, POST, PUT, DELETE) is permitted on any endpoint. No middleware checks `canRead`, `canWrite`, or `canDelete` for API key principals.
- **Gap**: An agent intended for read-only access could execute DELETE or POST operations if it receives or generates incorrect tool calls.
- **Compensating Controls**:
  - Deploy a reverse proxy that enforces HTTP method allowlisting (allow only GET, HEAD for read-only agents)
  - Implement an ASP.NET Core authorization policy that checks claims for permitted HTTP methods
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add authorization policies per HTTP method. Leverage ASP.NET Core's policy-based authorization to require specific claims (e.g., `write:series`) for mutating endpoints.
- **Evidence**: `src/Sonarr.Http/REST/RestController.cs` (no authorization attribute checks per method), `src/NzbDrone.Host/Startup.cs` (FallbackPolicy only requires authentication)

#### AUTH-Q6: Immutable Audit Logging ⚡

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Authentication events are logged via `AuthenticationService.cs` to NLog (`Auth` logger) with IP address and username. API requests are logged via `LoggingMiddleware.cs` with request sequence ID, HTTP method, path, and origin IP. However, logs are written to local files via NLog's `CleansingFileTarget` — they are mutable, not tamper-evident, and can be deleted or modified by anyone with filesystem access.
- **Gap**: No immutable log storage. No CloudTrail or equivalent. Logs are local files subject to tampering. No log integrity verification.
- **Compensating Controls**:
  - Forward logs to an external immutable log aggregation service (e.g., syslog to a remote server — Sonarr has syslog support via `SyslogServer`/`SyslogPort` config)
  - Enable syslog forwarding to an append-only log store
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure Sonarr's built-in syslog forwarding to send auth and API logs to an immutable external log store. Add agent identity fields to log entries once AUTH-Q1 is resolved.
- **Evidence**: `src/Sonarr.Http/Authentication/AuthenticationService.cs`, `src/Sonarr.Http/Middleware/LoggingMiddleware.cs`, `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (SyslogServer, SyslogPort properties)

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Sonarr has a single shared API key. The only mechanism to revoke access is `ResetApiKeyCommand`, which regenerates the entire API key — disrupting all consumers simultaneously. There is no way to suspend an individual agent identity without affecting all other API consumers.
- **Gap**: No per-agent identity suspension. Revoking a misbehaving agent requires regenerating the API key for all consumers.
- **Compensating Controls**:
  - Use a reverse proxy with per-agent API key mapping; revoke at the proxy layer
  - Implement IP-based blocking for compromised agent instances
- **Remediation Timeline**: 60–90 days (depends on AUTH-Q1 multi-key implementation)
- **Recommendation**: After implementing multiple named API keys (AUTH-Q1), add per-key enable/disable functionality without affecting other keys.
- **Evidence**: `src/NzbDrone.Core/Configuration/ResetApiKeyCommand.cs`, `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (single ApiKey property)

#### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No saga pattern, compensating transactions, or explicit rollback mechanisms found. The `CommandExecutor.cs` executes commands sequentially and catches failures, but failed commands are simply marked as failed — no compensation or undo logic is triggered for partially completed multi-step operations.
- **Gap**: If a multi-step operation (e.g., series import with metadata fetch + file rename + notification) fails mid-sequence, the system is left in a partial state with no automatic rollback.
- **Compensating Controls**:
  - For read-only agent scope, this risk is minimized since agents will not initiate write workflows
  - Monitor command status via `/api/v3/command` to detect failed operations
- **Remediation Timeline**: 90–180 days
- **Recommendation**: Implement compensation patterns for critical multi-step write workflows. Add rollback handlers to `CommandExecutor` for commands that modify state.
- **Evidence**: `src/NzbDrone.Core/Messaging/Commands/CommandExecutor.cs` (catch block marks command as Failed but no compensation)

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Sonarr calls multiple external services: indexers (Newznab, Torznab), download clients (SABnzbd, NZBGet, qBittorrent, Deluge, Transmission), and metadata providers (TheTVDB, TMDB). The `HttpClient.cs` has basic retry logic for outbound HTTP requests and throws `TooManyRequestsException` on 429 status codes. Polly retry strategy is used in `BasicRepository.cs` for SQLite busy retries. However, no circuit breaker pattern is implemented — there is no mechanism to stop calling a failing external service after repeated failures.
- **Gap**: No circuit breaker protection for external dependency calls. A failing indexer or download client will be repeatedly called, potentially cascading failures back to agent-initiated requests.
- **Compensating Controls**:
  - Sonarr's `RateLimitService.cs` provides per-host rate limiting for outbound calls, partially mitigating thundering herd scenarios
  - Indexer and download client status tracking exists (`IndexerStatus`, `DownloadClientStatus`) which can temporarily disable failing providers
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement Polly circuit breaker policies on the `HttpClient` for external service calls. Use existing status tracking to automatically open circuits when providers fail repeatedly.
- **Evidence**: `src/NzbDrone.Common/Http/HttpClient.cs` (no circuit breaker), `src/NzbDrone.Common/TPL/RateLimitService.cs` (rate limiting only), `src/NzbDrone.Core/Datastore/BasicRepository.cs` (Polly retry for SQLite only)

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No API-layer rate limiting exists on incoming requests. The application listens directly on port 8989 with no API gateway, WAF, or rate limiting middleware. The `RateLimitService.cs` applies rate limiting only to Sonarr's outbound HTTP requests (to indexers and download clients), not to incoming API requests from agents.
- **Gap**: A runaway agent loop or misconfigured agent could send unlimited requests to Sonarr's API at machine speed, potentially overwhelming the application.
- **Compensating Controls**:
  - Deploy a reverse proxy (nginx, Caddy) with rate limiting in front of Sonarr
  - Use iptables/nftables rate limiting at the network level
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add ASP.NET Core rate limiting middleware (`Microsoft.AspNetCore.RateLimiting`) to the request pipeline in `Startup.cs`. Configure per-IP and per-API-key limits.
- **Evidence**: `src/NzbDrone.Host/Startup.cs` (no rate limiting middleware), `src/NzbDrone.Common/TPL/RateLimitService.cs` (outbound only)

#### DATA-Q2: Data Residency and Sovereignty ⚡

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Sonarr is a desktop/server application where data resides on the user's local machine or Docker host. The database (SQLite or PostgreSQL) stores TV series metadata, episode information, and user configuration. No cloud region configuration or data residency controls exist because the application is self-hosted. However, if an agent reads data from Sonarr and sends it to an LLM provider, the data (which may include file paths, local network information, and download client credentials) could cross jurisdictional boundaries.
- **Gap**: No explicit data residency controls or data boundary enforcement. While the self-hosted nature means data physically stays local, there are no controls preventing an agent from exfiltrating data to external services.
- **Compensating Controls**:
  - Configure the agent orchestration layer to ensure LLM calls are made to same-region endpoints
  - Implement response filtering at the agent layer to strip local paths and credentials before sending to LLM
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document data residency characteristics. Implement API response sanitization to strip file paths, IP addresses, and credentials before data leaves the local context.
- **Evidence**: `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (PostgresHost, local file storage), `src/NzbDrone.Core/Datastore/` (SQLite local file database)

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: `CleanseLogMessage.cs` implements extensive log scrubbing with 20+ regex rules that redact API keys, passwords, tokens, tracker announce keys, and partially mask non-local IP addresses. This is applied via NLog's `CleansingConsoleTarget` and `CleansingFileTarget`. However: (1) `LoggingMiddleware.cs` logs request paths and full query strings before cleansing is applied to the log message, (2) IP addresses of local network clients are NOT masked, (3) no PII masking exists for entity-level data (series titles containing personal information in file paths).
- **Gap**: PII redaction coverage is partial. Log cleansing focuses on credentials and external IPs but does not address local IPs, file system paths that may contain usernames, or entity data that could contain personal information.
- **Compensating Controls**:
  - Restrict log file access to authorized administrators only
  - Configure log rotation with short retention periods
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Extend `CleanseLogMessage` to mask local IP addresses in API request logs. Add path-cleansing rules that redact OS username components from file paths (the regex for `C:\Users\` and `/home/` already exists but only in log messages, not in all log contexts).
- **Evidence**: `src/NzbDrone.Common/Instrumentation/CleanseLogMessage.cs` (20+ cleansing rules), `src/Sonarr.Http/Middleware/LoggingMiddleware.cs` (logs IP via GetRemoteIP)

### RISK-QUALITY — Address as Capacity Allows

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: `SonarrErrorPipeline.cs` returns structured JSON error responses via `ErrorModel` with `Message`, `Description`, and `Content` fields. The pipeline distinguishes `ValidationException` (400), `ModelNotFoundException` (404), `ModelConflictException` (409), `SQLiteException` constraint failures (409), and general errors (500). This provides good error differentiation.
- **Gap**: No explicit `retryable` flag or error category in error responses. An agent cannot programmatically determine whether a 500 error is transient (retry) or permanent (abort) without inspecting the message text.
- **Compensating Controls**:
  - Agent tool definitions can include status-code-based retry logic (retry on 429, 503; abort on 400, 404, 409)
  - Agents can use the `Description` field for additional context
- **Remediation Timeline**: 30 days
- **Recommendation**: Add a `retryable` boolean and `errorCode` string to `ErrorModel`. Map exceptions to error categories (e.g., `RATE_LIMITED`, `CONFLICT`, `NOT_FOUND`, `INTERNAL`).
- **Evidence**: `src/Sonarr.Http/ErrorManagement/SonarrErrorPipeline.cs`, `src/Sonarr.Http/ErrorManagement/ErrorModel.cs`

#### AUTH-Q4: Identity Propagation and Delegation — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No identity propagation mechanism exists. Sonarr uses a single shared API key with no JWT/OAuth token exchange, no on-behalf-of flows, and no distinction between an agent acting under its own identity vs. acting on behalf of a human user. In the desktop application context, this is expected — Sonarr is typically accessed by a single user or household.
- **Gap**: Cannot distinguish agent-as-self from agent-on-behalf-of-user. All API consumers are treated identically.
- **Compensating Controls**:
  - Document the agent's operating context (which user's Sonarr instance it accesses)
  - Implement at the agent orchestration layer rather than in Sonarr
- **Remediation Timeline**: 90–180 days (low priority for desktop application)
- **Recommendation**: If multi-user agent access is needed in the future, implement JWT-based authentication with user context claims alongside the API key mechanism.
- **Evidence**: `src/Sonarr.Http/Authentication/ApiKeyAuthenticationHandler.cs` (no user context propagation), `src/Sonarr.Http/Authentication/AuthenticationService.cs` (Forms auth is separate from API key auth)

#### AUTH-Q5: Credential Management — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The API key is stored in a local XML configuration file (`config.xml`) managed by `ConfigFileProvider.cs`. PostgreSQL credentials (host, user, password) are stored in the same config file or passed via environment variables/command-line options. No secrets manager integration (no AWS Secrets Manager, no HashiCorp Vault). Download client and indexer credentials are stored in the SQLite/PostgreSQL database in the `Settings` JSON column.
- **Gap**: Credentials stored in plaintext configuration files and database columns. No rotation mechanism for stored credentials (except `ResetApiKeyCommand` for the API key). No encryption at rest for the config file.
- **Compensating Controls**:
  - Use filesystem permissions to restrict access to the config file
  - Use environment variables for PostgreSQL credentials (supported via `PostgresOptions`)
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement encrypted storage for the `Settings` column containing provider credentials. Support external secrets providers for database and API credentials.
- **Evidence**: `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (XML config, plaintext storage), `src/NzbDrone.Core/Configuration/ResetApiKeyCommand.cs`

#### DATA-Q5: Temporal Metadata and Freshness — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Database models include relevant timestamp fields: `Episode.AirDateUtc`, `Series.Added`, `Series.LastAired`, `EpisodeFile.DateAdded`. Timestamps are stored in UTC. However, API responses do not include `Cache-Control`, `X-Data-Age`, or `last_refreshed` headers. No freshness signaling mechanism tells agents whether data is current or stale.
- **Gap**: Agents cannot determine data freshness from API response headers. Metadata sourced from external providers (TheTVDB, TMDB) may be cached without indication of staleness.
- **Compensating Controls**:
  - Agents can use entity-level timestamp fields (e.g., `lastInfoSync` on Series) to assess freshness
  - Trigger a metadata refresh command before reading if freshness is critical
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `Last-Modified` and `Cache-Control` headers to API responses. Include a `lastRefreshed` field in series/episode API responses.
- **Evidence**: `src/NzbDrone.Core/Tv/Series.cs`, `src/NzbDrone.Core/Tv/Episode.cs`, `src/Sonarr.Http/Middleware/CacheHeaderMiddleware.cs`

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: APIs are versioned with `/api/v3/` and `/api/v5/` URL patterns. OpenAPI specifications are committed to the repository. Database schema is versioned through 230+ migration files in `NzbDrone.Core/Datastore/Migration/`. Deprecated endpoints emit a `Deprecation: true` response header via `RestController.cs`.
- **Gap**: No breaking-change detection in CI. No Pact consumer-driven contract tests. No OpenAPI diff tools in the build pipeline. OpenAPI specs are committed but not validated against the implementation during builds.
- **Compensating Controls**:
  - The `api_docs.yml` GitHub Actions workflow generates API docs, providing some spec maintenance
  - Version-separated API paths (`v3`, `v5`) reduce silent breakage risk
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenAPI diff checks (e.g., `oasdiff`) to the CI pipeline to detect breaking changes between builds. Validate that generated OpenAPI specs match committed specs.
- **Evidence**: `src/Sonarr.Api.V3/openapi.json`, `src/Sonarr.Api.V5/openapi.json`, `.github/workflows/api_docs.yml`, `src/NzbDrone.Core/Datastore/Migration/`

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Docker test containers exist in `docker/tests/` for Mono compatibility testing. A build Dockerfile exists at `distribution/docker-build/Dockerfile`. Development configuration is available for local debugging. However, no formal staging or sandbox environment with production-equivalent data shape exists for agent testing.
- **Gap**: No dedicated staging environment where agents can be tested against realistic data without risk to a user's live Sonarr instance.
- **Compensating Controls**:
  - Sonarr can be run as a separate Docker instance with test data for agent development
  - Integration tests in the codebase (`NzbDrone.Integration.Test`) provide a template for agent test setup
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a Docker Compose configuration with seed data for agent testing. Include sample series, episodes, and mock download client/indexer configurations.
- **Evidence**: `docker/tests/`, `distribution/docker-build/Dockerfile`, `src/NzbDrone.Integration.Test/`

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No distributed tracing (no OpenTelemetry, no X-Ray). NLog provides logging with `CleansingConsoleLogLayout` and CLEF-format support via `CleansingClefLogLayout`. `LoggingMiddleware.cs` assigns `ApiRequestSequenceID` for request correlation and logs request duration. Sentry integration exists for error tracking via `SentryTarget`. However, no `traceparent` header propagation, no JSON-structured logging by default, and no correlation ID in response headers.
- **Gap**: Cannot trace agent-initiated requests through the system. No distributed trace context propagation. Request sequence IDs are internal only (not returned to callers).
- **Compensating Controls**:
  - The `ApiRequestSequenceID` provides basic request correlation within Sonarr's logs
  - Sentry captures errors with stack traces for debugging
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add OpenTelemetry instrumentation to the ASP.NET Core pipeline. Return a `X-Request-Id` header to callers for correlation. Enable CLEF (JSON) log format by default.
- **Evidence**: `src/Sonarr.Http/Middleware/LoggingMiddleware.cs` (ApiRequestSequenceID), `src/NzbDrone.Core/Instrumentation/ReconfigureLogging.cs` (Sentry)

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Sonarr has an internal `HealthCheckService` that monitors application health (disk space, indexer status, download client connectivity, etc.) and surfaces results via the API and UI. However, no external alerting thresholds are configured — no CloudWatch alarms, no PagerDuty/OpsGenie integration, no SLO-based alerting.
- **Gap**: No proactive alerting when error rates or latency increase on API endpoints agents consume. Health issues are detected only when a user or agent polls the health endpoint.
- **Compensating Controls**:
  - Agents can poll `/api/v3/health` to check system status before operations
  - Webhook notifications can forward health events to external monitoring
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure Sonarr's webhook notifications to send health alerts to an external monitoring system. Implement external endpoint monitoring (e.g., uptime check on `/api/v3/system/status`).
- **Evidence**: `src/NzbDrone.Core/HealthCheck/HealthCheckService.cs`, `src/NzbDrone.Core/Notifications/Webhook/`

#### ENG-Q1: Infrastructure Governance — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No Infrastructure as Code found in the repository. No Terraform, CloudFormation, CDK, Helm, or Kustomize definitions. Sonarr is a desktop/server application distributed via Docker images, Debian packages, Windows installers, and macOS bundles. Infrastructure is the user's local machine or Docker host.
- **Gap**: No IaC governance for the agent-facing integration surface. The API surface (port, authentication, network exposure) is configured by end users without code-reviewed, version-controlled infrastructure definitions.
- **Compensating Controls**:
  - Sonarr's Docker image provides a consistent, reproducible deployment
  - Configuration is well-documented for self-hosted setups
- **Remediation Timeline**: 90+ days (low priority for self-hosted application)
- **Recommendation**: Provide reference IaC templates (Docker Compose, Helm chart) for production-grade Sonarr deployments with security best practices (reverse proxy, rate limiting, separate database).
- **Evidence**: `distribution/docker-build/Dockerfile`, absence of IaC files in repository root

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive CI/CD via GitHub Actions (`build_v5.yml`): multi-platform builds (Linux, macOS, Windows, FreeBSD), unit tests, PostgreSQL integration tests, frontend linting, and integration tests. OpenAPI specs are generated via `api_docs.yml` workflow. However, no API contract testing (no Pact, no consumer-driven contracts, no OpenAPI diff validation in CI).
- **Gap**: API changes are not automatically validated against agent tool definitions. Breaking changes to API responses could silently break agent integrations.
- **Compensating Controls**:
  - OpenAPI specs are committed to the repository and can be manually diffed
  - Integration tests provide some coverage of API behavior
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenAPI diff validation to the CI pipeline. Compare generated OpenAPI spec against the committed version to detect breaking changes.
- **Evidence**: `.github/workflows/build_v5.yml`, `.github/workflows/api_docs.yml`

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Sonarr has a built-in self-update mechanism (`NzbDrone.Core/Update/`) that downloads and applies updates. No blue/green deployment, no canary releases, no automated rollback. Rollback requires manual reinstallation of a previous version. Docker deployments can roll back by using a previous image tag.
- **Gap**: No automated rollback within 15–30 minutes. Manual intervention required to restore a previous version.
- **Compensating Controls**:
  - Docker deployments can use image tag pinning and quick rollback via `docker pull` of previous tag
  - Database migrations include down-migration support in some cases
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Document rollback procedures for both Docker and native installations. For Docker deployments, provide a rollback script that restores the previous image tag and database backup.
- **Evidence**: `src/NzbDrone.Core/Update/`, `distribution/docker-build/Dockerfile`

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Extensive test suites exist: NUnit-based unit tests across `NzbDrone.Core.Test`, `NzbDrone.Common.Test`, `NzbDrone.Host.Test`, and integration tests in `NzbDrone.Integration.Test`. CI runs tests on Linux, macOS, Windows, and PostgreSQL. However, no explicit API contract tests (no Postman/Newman collections, no REST Assured, no Pact tests targeting the API surface specifically).
- **Gap**: While integration tests exercise API endpoints, there are no dedicated API contract tests validating input handling, output format consistency, error responses, and edge cases specifically from an agent consumer perspective.
- **Compensating Controls**:
  - Integration tests provide indirect API coverage
  - OpenAPI specs serve as de facto contract documentation
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add dedicated API contract test suites targeting the agent-facing endpoints. Include tests for pagination behavior, error response format, and authentication edge cases.
- **Evidence**: `.github/workflows/build_v5.yml` (test matrix), `src/NzbDrone.Integration.Test/`, `src/NzbDrone.Core.Test/`

#### ENG-Q5: Encryption at Rest — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: SQLite database is stored as a plain file on the user's filesystem with no encryption. PostgreSQL connections may or may not use SSL (configurable via connection string). No KMS integration, no column-level encryption, no transparent data encryption configuration in the codebase.
- **Gap**: Data at rest (including stored credentials in provider settings) is unencrypted. Physical access to the database file grants full access to all stored data.
- **Compensating Controls**:
  - Filesystem-level encryption (LUKS, BitLocker, FileVault) provides transparent encryption
  - PostgreSQL deployments can use TDE or encrypted storage volumes
- **Remediation Timeline**: 90+ days
- **Recommendation**: For SQLite, evaluate SQLCipher for transparent database encryption. For PostgreSQL, document TDE configuration requirements. Implement column-level encryption for the provider settings containing credentials.
- **Evidence**: `src/NzbDrone.Core/Datastore/` (no encryption configuration), `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (plaintext config)

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO
- **Finding**: Sonarr exposes a well-documented REST API via ASP.NET Core controllers across two API versions: `Sonarr.Api.V3` (endpoints under `/api/v3/`) and `Sonarr.Api.V5` (endpoints under `/api/v5/`). Endpoints cover Series, Episodes, EpisodeFiles, Commands, Calendar, Queue, History, Wanted, Profiles, and system management. No direct database access or UI automation is required.
- **Implication**: The API surface is well-suited for agent tool generation. Agents can be built against versioned, stable REST endpoints.
- **Recommendation**: No action required. Continue maintaining the versioned API surface.
- **Evidence**: `src/Sonarr.Api.V3/`, `src/Sonarr.Api.V5/`, `src/NzbDrone.Host/Startup.cs`

### API-Q2: Machine-Readable API Specification

- **Severity**: INFO
- **Finding**: OpenAPI 3.0.1 specification exists at `src/Sonarr.Api.V3/openapi.json` (290KB) and OpenAPI 3.0.4 specification at `src/Sonarr.Api.V5/openapi.json` (255KB). Specs are auto-generated via Swashbuckle/SwaggerGen configured in `Startup.cs`. API security schemes (X-Api-Key header, apikey query parameter) are documented in the specs.
- **Implication**: Agent tool definitions can be auto-generated from the OpenAPI specs. This significantly reduces integration effort.
- **Recommendation**: Ensure specs are regenerated and committed with each release. Consider publishing specs to an API catalog.
- **Evidence**: `src/Sonarr.Api.V3/openapi.json`, `src/Sonarr.Api.V5/openapi.json`, `src/NzbDrone.Host/Startup.cs` (SwaggerGen config)

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No idempotency key middleware found. Write endpoints (POST for series, commands, etc.) do not accept idempotency keys. PUT operations are naturally idempotent (update by ID). POST operations are not idempotent — duplicate POSTs could create duplicate resources.
- **Implication**: If agent scope expands to write-enabled in the future, idempotency keys will be needed on POST endpoints to prevent duplicate operations from LLM non-determinism or retries.
- **Recommendation**: Plan for idempotency key support on POST endpoints if write-enabled agent access is planned.
- **Evidence**: `src/Sonarr.Http/REST/RestController.cs` (no idempotency middleware)

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: All API responses are structured JSON via `System.Text.Json` serialization configured in `Startup.cs` (`STJson.ApplySerializerSettings`). Response content type is `application/json`. No XML, binary, or protobuf formats are used for the REST API.
- **Implication**: JSON responses are directly consumable by LLM-based agents without format conversion.
- **Recommendation**: No action required.
- **Evidence**: `src/NzbDrone.Host/Startup.cs` (AddJsonOptions), `src/NzbDrone.Common/Serializer/STJson.cs`

### API-Q6: Asynchronous Operation Support

- **Severity**: INFO
- **Finding**: Sonarr's Command system provides a robust async operation pattern. Commands are submitted via POST to `/api/v3/command` and their status can be polled via GET. `CommandExecutor.cs` processes commands in a background thread pool (3 threads). Commands have lifecycle states (Queued, Started, Completed, Failed). The `CommandQueueManager` manages the command queue.
- **Implication**: Long-running operations (series refresh, episode search, download import) are well-suited for agent async patterns — submit command, poll for completion.
- **Recommendation**: No action required. Document the command lifecycle for agent developers.
- **Evidence**: `src/NzbDrone.Core/Messaging/Commands/CommandExecutor.cs`, `src/NzbDrone.Core/Messaging/Commands/CommandQueueManager.cs`

### API-Q7: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: Sonarr emits real-time events via SignalR hub at `/signalr/messages` for model changes (created, updated, deleted) through `RestControllerWithSignalR`. Additionally, a comprehensive webhook notification system exists in `NzbDrone.Core/Notifications/Webhook/` supporting events: Grab, Download, ImportComplete, Rename, EpisodeFileDelete, SeriesAdd, SeriesDelete, Health, HealthRestored, ApplicationUpdate, ManualInteractionRequired.
- **Implication**: Agents can subscribe to Sonarr events via webhooks for proactive automation (e.g., trigger quality upgrade check when new episode is available). SignalR provides real-time UI updates but may also be consumable by agents.
- **Recommendation**: Document webhook event schemas for agent consumption. Consider exposing SignalR events as a supported integration surface.
- **Evidence**: `src/Sonarr.Http/REST/RestControllerWithSignalR.cs`, `src/NzbDrone.Core/Notifications/Webhook/`

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limit headers (`X-RateLimit-Remaining`, `Retry-After`) are returned in API responses. No API Gateway throttle settings or WAF rate rules exist. No rate limit documentation found.
- **Implication**: Agents cannot self-throttle based on API response headers. They must rely on external rate limiting or hardcoded throttle intervals.
- **Recommendation**: Add rate limit response headers when rate limiting middleware is implemented (per STATE-Q5 recommendation).
- **Evidence**: `src/NzbDrone.Host/Startup.cs` (no rate limit middleware or headers)

### STATE-Q2: Queryable Current State

- **Severity**: INFO
- **Finding**: All major entities expose queryable current state via GET endpoints: Series (`/api/v3/series`), Episodes (`/api/v3/episode`), EpisodeFiles (`/api/v3/episodefile`), Commands (`/api/v3/command`), Queue (`/api/v3/queue`), Calendar, History, and Wanted. Entities include status fields (e.g., Series has `status`, Commands have `status`).
- **Implication**: Agents can inspect current system state before making decisions. The read-before-write pattern is fully supported.
- **Recommendation**: No action required.
- **Evidence**: `src/Sonarr.Api.V3/`, `src/NzbDrone.Core/Datastore/BasicRepository.cs` (GetPaged, Find, Get methods)

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits per agent identity. No maximum records modified per run, no spend caps, no bulk operation limits. Desktop application design does not include multi-tenant resource controls.
- **Implication**: If agent scope expands to write-enabled, transaction limits will be critical to prevent catastrophic bulk modifications.
- **Recommendation**: Plan transaction limit support if write-enabled agent access is anticipated.
- **Evidence**: No transaction limit configuration found in codebase

### DATA-Q3: Selective Query Support

- **Severity**: INFO
- **Finding**: Pagination is fully implemented via `PagingResource.cs` and `PagingSpec.cs`. API endpoints support `Page`, `PageSize`, `SortKey`, and `SortDirection` parameters. Default page size is 10. Filtering is supported per endpoint via filter expressions. Sort key validation exists (allowedSortKeys).
- **Implication**: Agents can retrieve bounded result sets efficiently. No risk of unbounded query results overwhelming LLM context windows.
- **Recommendation**: No action required.
- **Evidence**: `src/Sonarr.Http/PagingResource.cs`, `src/NzbDrone.Core/Datastore/PagingSpec.cs`, `src/NzbDrone.Core/Datastore/BasicRepository.cs` (GetPaged)

### DATA-Q4: System of Record Designations

- **Severity**: INFO
- **Finding**: Sonarr is the authoritative system of record for its own managed data: series/episode metadata (sourced from TheTVDB/TMDB but locally stored and managed), episode file tracking, quality profiles, and download queue state. External metadata is periodically synced but Sonarr maintains its own copy.
- **Implication**: Agents querying Sonarr get authoritative data for the managed media library. No cross-system reconciliation needed for Sonarr-owned entities.
- **Recommendation**: No action required.
- **Evidence**: `src/NzbDrone.Core/Tv/Series.cs`, `src/NzbDrone.Core/Tv/Episode.cs`

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality dashboards, profiling reports, or completeness metrics exist. No null rate monitoring or duplicate detection logic exposed via API. The HealthCheck system monitors operational health (connectivity, disk space) but not data quality.
- **Implication**: Agents cannot assess data quality before reasoning. May need to implement quality checks in the agent layer.
- **Recommendation**: Consider exposing data completeness metrics (e.g., percentage of series with complete metadata, episodes with files) via the API.
- **Evidence**: `src/NzbDrone.Core/HealthCheck/` (operational health only)

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Field names are human-readable and semantically meaningful throughout the codebase and API: `Title`, `SeasonNumber`, `EpisodeNumber`, `AirDateUtc`, `QualityProfile`, `SeriesType`, `EpisodeFile`, `DownloadClient`, etc. No legacy codes or cryptic abbreviations found in the API surface.
- **Implication**: Agent tool definitions will have self-documenting parameter and response field names, improving LLM reasoning quality.
- **Recommendation**: No action required. Maintain current naming conventions.
- **Evidence**: `src/Sonarr.Api.V3/openapi.json`, `src/NzbDrone.Core/Tv/Series.cs`, `src/NzbDrone.Core/Tv/Episode.cs`

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No formal data catalog or metadata layer exists. The OpenAPI specifications serve as the primary documentation of what data Sonarr exposes. No AWS Glue Data Catalog, Collibra, or DataHub integration.
- **Implication**: Agent tool authors must rely on OpenAPI specs and source code to understand available data. No semantic search across Sonarr's data model.
- **Recommendation**: Consider publishing a data dictionary as part of the API documentation that describes entity relationships and data semantics.
- **Evidence**: `src/Sonarr.Api.V3/openapi.json`, `src/Sonarr.Api.V5/openapi.json`

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No custom business outcome metrics are published. No CloudWatch metrics, no Prometheus exporters, no custom dashboards tracking resolution rates, episode acquisition success, or quality upgrade rates. Sentry integration captures error events only.
- **Implication**: When agents interact with Sonarr, there are no business-level metrics to measure whether agent actions produce good outcomes (e.g., successful series additions, quality upgrades triggered).
- **Recommendation**: Implement custom metrics for key business outcomes: series addition success rate, episode search hit rate, download completion rate, quality upgrade frequency.
- **Evidence**: `src/NzbDrone.Core/Instrumentation/` (Sentry only)

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO (no gap — criteria met)
- **Finding**: Sonarr exposes a documented REST API via ASP.NET Core controllers (Sonarr.Api.V3, Sonarr.Api.V5) with versioned endpoints. No direct database access, file-based exchange, or UI automation required.
- **Gap**: None
- **Recommendation**: Continue maintaining the versioned REST API surface.
- **Evidence**: `src/Sonarr.Api.V3/`, `src/Sonarr.Api.V5/`, `src/NzbDrone.Host/Startup.cs`

#### API-Q2: Machine-Readable API Specification
- **Severity**: INFO (no gap — criteria met)
- **Finding**: OpenAPI 3.0.1 spec at `src/Sonarr.Api.V3/openapi.json` and OpenAPI 3.0.4 spec at `src/Sonarr.Api.V5/openapi.json`. Auto-generated via SwaggerGen in Startup.cs.
- **Gap**: None
- **Recommendation**: Ensure specs are validated against implementation in CI.
- **Evidence**: `src/Sonarr.Api.V3/openapi.json`, `src/Sonarr.Api.V5/openapi.json`

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: `SonarrErrorPipeline.cs` returns structured JSON ErrorModel with Message, Description, Content. Distinguishes 400/404/409/500. No explicit retryable flag.
- **Gap**: No retryable boolean or error category in error responses.
- **Recommendation**: Add `retryable` and `errorCode` fields to ErrorModel.
- **Evidence**: `src/Sonarr.Http/ErrorManagement/SonarrErrorPipeline.cs`, `src/Sonarr.Http/ErrorManagement/ErrorModel.cs`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No idempotency key middleware. Write endpoints lack idempotency keys. PUT is naturally idempotent; POST is not.
- **Gap**: No idempotency support on POST endpoints (informational for read-only scope).
- **Recommendation**: Plan idempotency key support for future write-enabled scope.
- **Evidence**: `src/Sonarr.Http/REST/RestController.cs`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: All API responses are structured JSON via System.Text.Json. Content-type: application/json.
- **Gap**: None
- **Recommendation**: No action required.
- **Evidence**: `src/NzbDrone.Host/Startup.cs`

#### API-Q6: Asynchronous Operation Support
- **Severity**: INFO (extended — triggered: long-running operations exist)
- **Finding**: Command system supports async patterns — submit via POST `/api/v3/command`, poll via GET. CommandExecutor processes in background thread pool. Commands have Queued/Started/Completed/Failed lifecycle.
- **Gap**: None — async pattern is implemented.
- **Recommendation**: Document command lifecycle for agent developers.
- **Evidence**: `src/NzbDrone.Core/Messaging/Commands/CommandExecutor.cs`

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO (extended — triggered: stateful-crud with state changes)
- **Finding**: SignalR hub at `/signalr/messages` broadcasts model change events. Comprehensive webhook notification system supports 11 event types (Grab, Download, Rename, etc.).
- **Gap**: None — event emission is well-implemented.
- **Recommendation**: Document webhook event schemas for agent consumption.
- **Evidence**: `src/Sonarr.Http/REST/RestControllerWithSignalR.cs`, `src/NzbDrone.Core/Notifications/Webhook/`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit headers (X-RateLimit-Remaining, Retry-After) in API responses. No rate limit documentation.
- **Gap**: Agents cannot self-throttle based on response headers.
- **Recommendation**: Add rate limit headers when rate limiting is implemented.
- **Evidence**: `src/NzbDrone.Host/Startup.cs`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: Single shared API key via X-Api-Key header or apikey query parameter. All consumers share identity claim `ApiKey: true`. No per-agent principal attribution.
- **Gap**: No mechanism to distinguish which agent made an API call. All API key holders are the same identity.
- **Recommendation**: Implement multiple named API keys with unique principal claims.
- **Evidence**: `src/Sonarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: Single API key grants full access to all endpoints. No scoped permissions, roles, or resource-level access controls.
- **Gap**: Cannot grant agent read-only access to specific resources.
- **Recommendation**: Implement role-based API key scoping with permission levels.
- **Evidence**: `src/Sonarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/NzbDrone.Host/Startup.cs`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization for API key consumers. Any HTTP method permitted on any endpoint once authenticated.
- **Gap**: Agent intended for read-only could execute DELETE/POST operations.
- **Recommendation**: Add authorization policies per HTTP method using ASP.NET Core policy-based auth.
- **Evidence**: `src/Sonarr.Http/REST/RestController.cs`, `src/NzbDrone.Host/Startup.cs`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: RISK-QUALITY
- **Finding**: No identity propagation. Single shared API key, no JWT/OAuth token exchange, no on-behalf-of flows. Desktop application context where single-user access is typical.
- **Gap**: Cannot distinguish agent-as-self from agent-on-behalf-of-user.
- **Recommendation**: Implement JWT-based auth with user context claims if multi-user agent access is needed.
- **Evidence**: `src/Sonarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/Sonarr.Http/Authentication/AuthenticationService.cs`

#### AUTH-Q5: Credential Management
- **Severity**: RISK-QUALITY
- **Finding**: API key stored in local XML config file. PostgreSQL credentials in config or environment variables. Provider credentials (download clients, indexers) stored in database Settings JSON column. No secrets manager integration.
- **Gap**: Credentials stored in plaintext. No rotation mechanism except manual API key reset.
- **Recommendation**: Implement encrypted storage for provider credentials. Support external secrets providers.
- **Evidence**: `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`, `src/NzbDrone.Core/Configuration/ResetApiKeyCommand.cs`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Auth events logged via NLog Auth logger. API requests logged via LoggingMiddleware with sequence ID, method, path, IP. Logs written to mutable local files. Syslog forwarding supported but not configured by default.
- **Gap**: No immutable log storage. Logs are mutable local files subject to tampering.
- **Recommendation**: Configure syslog forwarding to an immutable external log store.
- **Evidence**: `src/Sonarr.Http/Authentication/AuthenticationService.cs`, `src/Sonarr.Http/Middleware/LoggingMiddleware.cs`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: Single shared API key. Only revocation mechanism is ResetApiKeyCommand which regenerates the entire key, disrupting all consumers.
- **Gap**: No per-agent identity suspension.
- **Recommendation**: Implement per-key enable/disable after multi-key support (AUTH-Q1).
- **Evidence**: `src/NzbDrone.Core/Configuration/ResetApiKeyCommand.cs`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No saga pattern or compensating transactions. CommandExecutor catches failures and marks commands as Failed but no rollback logic for partially completed operations.
- **Gap**: Multi-step operations that fail mid-sequence leave the system in partial state.
- **Recommendation**: Implement compensation patterns for critical write workflows.
- **Evidence**: `src/NzbDrone.Core/Messaging/Commands/CommandExecutor.cs`

#### STATE-Q2: Queryable Current State
- **Severity**: INFO (extended — triggered: stateful-crud)
- **Finding**: All major entities are queryable via GET endpoints. Series, Episodes, EpisodeFiles, Commands, Queue, Calendar, History, Wanted all expose current state.
- **Gap**: None — queryable state is well-implemented.
- **Recommendation**: No action required.
- **Evidence**: `src/Sonarr.Api.V3/`, `src/NzbDrone.Core/Datastore/BasicRepository.cs`

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled AND service has persistent state
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY (extended — triggered: external dependencies)
- **Finding**: Sonarr calls 3+ external services (indexers, download clients, metadata providers). No circuit breaker patterns found. Polly is used only for SQLite busy retries in BasicRepository, not for external HTTP calls.
- **Gap**: No circuit breaker protection for external dependency calls.
- **Recommendation**: Implement Polly circuit breaker policies on HttpClient for external calls.
- **Evidence**: `src/NzbDrone.Common/Http/HttpClient.cs`, `src/NzbDrone.Core/Datastore/BasicRepository.cs`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No API-layer rate limiting on incoming requests. RateLimitService applies only to outbound requests. No API gateway or WAF.
- **Gap**: Runaway agent loop could overwhelm the application.
- **Recommendation**: Add ASP.NET Core rate limiting middleware to Startup.cs.
- **Evidence**: `src/NzbDrone.Host/Startup.cs`, `src/NzbDrone.Common/TPL/RateLimitService.cs`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits per agent identity.
- **Gap**: No transaction limits (informational for read-only scope).
- **Recommendation**: Plan transaction limits for future write-enabled scope.
- **Evidence**: No transaction limit configuration found

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path (P2 priority — not triggered)
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
- **Severity**: RISK-QUALITY
- **Finding**: Docker test containers in `docker/tests/` for compatibility testing. Build Dockerfile at `distribution/docker-build/Dockerfile`. No formal staging/sandbox environment with production-equivalent data shape.
- **Gap**: No dedicated staging environment for agent testing.
- **Recommendation**: Create Docker Compose configuration with seed data for agent testing.
- **Evidence**: `docker/tests/`, `distribution/docker-build/Dockerfile`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: Stage A: Yes — stores download client credentials, indexer API keys, webhook URLs in database. Stage B: No field-level classification, no data tagging, no field-level encryption.
- **Gap**: Sensitive credentials stored without classification or field-level access controls.
- **Recommendation**: Classify credential fields, implement API response filtering to redact credentials by default.
- **Evidence**: `src/NzbDrone.Core/ThingiProvider/ProviderDefinition.cs`, `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Self-hosted desktop/server app. Data resides locally. No cloud region config or data residency controls. Risk is that an agent could send local data (file paths, credentials) to an external LLM.
- **Gap**: No data boundary enforcement preventing agent exfiltration of local data.
- **Recommendation**: Document data residency characteristics. Implement API response sanitization for agent consumption.
- **Evidence**: `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`, `src/NzbDrone.Core/Datastore/`

#### DATA-Q3: Selective Query Support
- **Severity**: INFO (extended — triggered: list/query endpoints)
- **Finding**: Pagination fully implemented via PagingResource.cs. Supports Page, PageSize, SortKey, SortDirection. Default page size 10. Filtering per endpoint.
- **Gap**: None — pagination is well-implemented.
- **Recommendation**: No action required.
- **Evidence**: `src/Sonarr.Http/PagingResource.cs`, `src/NzbDrone.Core/Datastore/PagingSpec.cs`

#### DATA-Q4: System of Record Designations
- **Severity**: INFO (extended — triggered: stateful-crud)
- **Finding**: Sonarr is the authoritative system of record for its managed media library data. External metadata synced from TheTVDB/TMDB is locally stored and managed.
- **Gap**: None — system of record is clear.
- **Recommendation**: No action required.
- **Evidence**: `src/NzbDrone.Core/Tv/Series.cs`, `src/NzbDrone.Core/Tv/Episode.cs`

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK-QUALITY (extended — triggered: stateful-crud)
- **Finding**: Timestamp fields exist (AirDateUtc, Added, LastAired, DateAdded) in UTC. No Cache-Control or X-Data-Age headers in responses. No freshness signaling.
- **Gap**: Agents cannot determine data freshness from response headers.
- **Recommendation**: Add Last-Modified and Cache-Control headers. Include lastRefreshed fields.
- **Evidence**: `src/NzbDrone.Core/Tv/Series.cs`, `src/NzbDrone.Core/Tv/Episode.cs`

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: CleanseLogMessage.cs implements 20+ regex rules scrubbing API keys, passwords, tokens, tracker keys, and partially masking non-local IPs. LoggingMiddleware logs request paths with IP addresses. Local IPs are not masked.
- **Gap**: Partial PII redaction coverage. Local IPs and file paths with usernames not fully addressed.
- **Recommendation**: Extend CleanseLogMessage to mask local IPs. Ensure file path cleansing applies in all log contexts.
- **Evidence**: `src/NzbDrone.Common/Instrumentation/CleanseLogMessage.cs`, `src/Sonarr.Http/Middleware/LoggingMiddleware.cs`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO (extended — always evaluated)
- **Finding**: No data quality dashboards, profiling, or completeness metrics. HealthCheck monitors operational health only.
- **Gap**: No data quality visibility.
- **Recommendation**: Consider exposing data completeness metrics via the API.
- **Evidence**: `src/NzbDrone.Core/HealthCheck/`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: APIs versioned with /api/v3/ and /api/v5/ URL patterns. OpenAPI specs committed. 230+ database migration files. Deprecated endpoint headers. No breaking-change detection in CI.
- **Gap**: No automated breaking-change detection. No Pact or OpenAPI diff in pipeline.
- **Recommendation**: Add OpenAPI diff checks (oasdiff) to CI pipeline.
- **Evidence**: `src/Sonarr.Api.V3/openapi.json`, `src/Sonarr.Api.V5/openapi.json`, `.github/workflows/api_docs.yml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO (extended — always evaluated)
- **Finding**: Field names are human-readable and semantic: Title, SeasonNumber, EpisodeNumber, AirDateUtc, QualityProfile, SeriesType. No legacy codes.
- **Gap**: None.
- **Recommendation**: Maintain current naming conventions.
- **Evidence**: `src/Sonarr.Api.V3/openapi.json`, `src/NzbDrone.Core/Tv/Series.cs`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO (extended — always evaluated)
- **Finding**: No formal data catalog. OpenAPI specs serve as primary documentation.
- **Gap**: No semantic metadata layer.
- **Recommendation**: Consider publishing a data dictionary with entity relationship documentation.
- **Evidence**: `src/Sonarr.Api.V3/openapi.json`, `src/Sonarr.Api.V5/openapi.json`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: No distributed tracing (no OpenTelemetry, no X-Ray). NLog with CleansingConsoleLogLayout and CLEF support. LoggingMiddleware assigns ApiRequestSequenceID. Sentry for errors. No traceparent propagation or JSON logging by default.
- **Gap**: Cannot trace agent-initiated requests. No distributed trace context. Internal-only request sequence IDs.
- **Recommendation**: Add OpenTelemetry instrumentation. Return X-Request-Id header. Enable CLEF format.
- **Evidence**: `src/Sonarr.Http/Middleware/LoggingMiddleware.cs`, `src/NzbDrone.Core/Instrumentation/ReconfigureLogging.cs`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: Internal HealthCheckService monitors app health. No external alerting thresholds (no CloudWatch, no PagerDuty). Desktop app monitors own health internally.
- **Gap**: No proactive alerting for API degradation.
- **Recommendation**: Configure webhook notifications to forward health alerts to external monitoring.
- **Evidence**: `src/NzbDrone.Core/HealthCheck/HealthCheckService.cs`, `src/NzbDrone.Core/Notifications/Webhook/`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO (extended — always evaluated)
- **Finding**: No custom business metrics. No CloudWatch, no Prometheus. Sentry for error tracking only.
- **Gap**: No business-level visibility for agent interactions.
- **Recommendation**: Implement custom metrics for key outcomes (series addition rate, download completion rate).
- **Evidence**: `src/NzbDrone.Core/Instrumentation/`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK-QUALITY
- **Finding**: No IaC found. Desktop/server app distributed via Docker, Debian packages, Windows installers. Infrastructure is the user's machine.
- **Gap**: No IaC governance for API surface configuration.
- **Recommendation**: Provide reference IaC templates (Docker Compose, Helm) with security best practices.
- **Evidence**: `distribution/docker-build/Dockerfile`, absence of IaC files

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive CI via GitHub Actions: multi-platform builds, unit/integration/Postgres tests, frontend linting. No API contract testing (no Pact, no OpenAPI diff in CI).
- **Gap**: API changes not validated against agent tool definitions.
- **Recommendation**: Add OpenAPI diff validation to CI pipeline.
- **Evidence**: `.github/workflows/build_v5.yml`, `.github/workflows/api_docs.yml`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: Built-in self-update mechanism. No blue/green or canary. Rollback requires manual reinstallation. Docker rollback via previous image tag.
- **Gap**: No automated rollback within 15–30 minutes.
- **Recommendation**: Document rollback procedures. Provide Docker rollback scripts.
- **Evidence**: `src/NzbDrone.Core/Update/`, `distribution/docker-build/Dockerfile`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY (extended — always evaluated)
- **Finding**: Extensive NUnit test suites (unit + integration). CI runs on 3 OSes + PostgreSQL. No dedicated API contract tests targeting agent-facing endpoints.
- **Gap**: No dedicated API contract tests from agent consumer perspective.
- **Recommendation**: Add API contract test suites for agent-facing endpoints.
- **Evidence**: `.github/workflows/build_v5.yml`, `src/NzbDrone.Integration.Test/`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: RISK-QUALITY (extended — triggered: persistent data stores)
- **Finding**: SQLite stored as plain file. No KMS, no column-level encryption, no TDE configuration.
- **Gap**: Data at rest unencrypted including stored credentials.
- **Recommendation**: Evaluate SQLCipher for SQLite encryption. Document PostgreSQL TDE configuration.
- **Evidence**: `src/NzbDrone.Core/Datastore/`, `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `src/Sonarr.Http/Authentication/ApiKeyAuthenticationHandler.cs` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4 |
| `src/Sonarr.Http/Authentication/AuthenticationService.cs` | AUTH-Q4, AUTH-Q6 |
| `src/Sonarr.Http/ErrorManagement/SonarrErrorPipeline.cs` | API-Q3 |
| `src/Sonarr.Http/ErrorManagement/ErrorModel.cs` | API-Q3 |
| `src/Sonarr.Http/REST/RestController.cs` | AUTH-Q3, API-Q4, DISC-Q1 |
| `src/Sonarr.Http/REST/RestControllerWithSignalR.cs` | API-Q7 |
| `src/Sonarr.Http/PagingResource.cs` | DATA-Q3 |
| `src/Sonarr.Http/Middleware/LoggingMiddleware.cs` | AUTH-Q6, DATA-Q6, OBS-Q1 |
| `src/NzbDrone.Host/Startup.cs` | API-Q1, API-Q2, API-Q5, AUTH-Q2, AUTH-Q3, STATE-Q5, API-Q8 |
| `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` | AUTH-Q1, AUTH-Q5, AUTH-Q6, DATA-Q1, DATA-Q2, ENG-Q5 |
| `src/NzbDrone.Core/Configuration/ResetApiKeyCommand.cs` | AUTH-Q5, AUTH-Q7 |
| `src/NzbDrone.Core/Messaging/Commands/CommandExecutor.cs` | STATE-Q1, API-Q6 |
| `src/NzbDrone.Core/Messaging/Commands/CommandQueueManager.cs` | API-Q6 |
| `src/NzbDrone.Core/Datastore/BasicRepository.cs` | STATE-Q2, STATE-Q4, DATA-Q3 |
| `src/NzbDrone.Core/Datastore/PagingSpec.cs` | DATA-Q3 |
| `src/NzbDrone.Common/Http/HttpClient.cs` | STATE-Q4 |
| `src/NzbDrone.Common/TPL/RateLimitService.cs` | STATE-Q4, STATE-Q5 |
| `src/NzbDrone.Common/Instrumentation/CleanseLogMessage.cs` | DATA-Q6 |
| `src/NzbDrone.Core/Tv/Series.cs` | DATA-Q4, DATA-Q5, DISC-Q2 |
| `src/NzbDrone.Core/Tv/Episode.cs` | DATA-Q4, DATA-Q5, DISC-Q2 |
| `src/NzbDrone.Core/ThingiProvider/ProviderDefinition.cs` | DATA-Q1 |
| `src/NzbDrone.Core/HealthCheck/HealthCheckService.cs` | OBS-Q2 |
| `src/NzbDrone.Core/Instrumentation/ReconfigureLogging.cs` | OBS-Q1 |
| `src/NzbDrone.Core/Update/` | ENG-Q3 |
| `src/NzbDrone.Core/Notifications/Webhook/` | API-Q7, OBS-Q2 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `src/Sonarr.Api.V3/openapi.json` | API-Q2, DISC-Q1, DISC-Q2, DISC-Q3 |
| `src/Sonarr.Api.V5/openapi.json` | API-Q2, DISC-Q1, DISC-Q3 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/build_v5.yml` | ENG-Q2, ENG-Q4 |
| `.github/workflows/api_docs.yml` | DISC-Q1, ENG-Q2 |
| `.github/workflows/deploy.yml` | ENG-Q2 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `distribution/docker-build/Dockerfile` | ENG-Q1, ENG-Q3, HITL-Q3 |
| `docker/tests/` | HITL-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `src/Sonarr.sln` | Step 1 (Discovery) |
| `src/Directory.Build.props` | Step 1 (Discovery) |
| `package.json` | Step 1 (Discovery) |
| `global.json` | Step 1 (Discovery) |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `src/NuGet.Config` | Step 1 (Discovery) |
| `.editorconfig` | Step 1 (Discovery) |

### Database Migrations
| File | Questions Referenced |
|------|---------------------|
| `src/NzbDrone.Core/Datastore/Migration/` (230+ files) | DISC-Q1 |
