# Agentic Readiness Assessment Report

**Target**: Sonarr (https://github.com/Sonarr/Sonarr)
**Date**: 2026-04-29
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: monorepo
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: csharp, media, desktop
**Context**: TV-series PVR for usenet and BitTorrent users (*arr suite).
**Archetype Justification**: Sonarr has persistent state (SQLite/PostgreSQL database), CRUD operations on series/episodes/downloads, write endpoints alongside read endpoints, and user-specific data — classifying it as stateful-crud.

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 2 | **RISK-SAFETY**: 9 | **RISK-QUALITY**: 16 | **INFOs**: 15

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days.

> **Note**: Sonarr is a self-hosted desktop/server application, not a cloud-native service. Many findings (no IaC, no secrets management, no distributed tracing) reflect its architecture as a locally-deployed media management application. Remediation recommendations account for this context and focus on what is pragmatically achievable within the application's deployment model.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 2 |
| RISK-SAFETY | 9 |
| RISK-QUALITY | 16 |
| INFO | 15 |
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
- **Finding**: Sonarr supports API key authentication via `X-Api-Key` header or `apikey` query parameter, implemented in `ApiKeyAuthenticationHandler.cs`. However, there is only a **single shared API key** for all API consumers. All authenticated requests receive the same identity claim (`ApiKey=true`) with no per-principal attribution. There is no mechanism to distinguish which agent (or human) made a specific API call. The API key is a GUID auto-generated in `ConfigFileProvider.cs` and stored in `config.xml`.
- **Gap**: No per-agent identity. No principal attribution in audit logs. A single shared API key means all consumers — human UI, third-party tools, and any future agents — share one identity. This makes audit attribution impossible and violates the requirement that agents be individually identifiable.
- **Remediation**:
  - **Immediate**: Implement a secondary API key registry that maps multiple API keys to named principals (e.g., `agent-sonarr-reader`, `third-party-tool-1`). Each key should carry a principal claim that appears in log entries. This can be done as a lightweight extension to the existing `ApiKeyAuthenticationHandler`.
  - **Target State**: Each agent identity has its own API key with a distinguishable principal name that appears in all request logs. Revocation of one key does not affect others.
  - **Estimated Effort**: Medium (2–4 weeks for multi-key support with principal attribution)
  - **Dependencies**: AUTH-Q7 (identity suspension) is resolved simultaneously if multi-key support is implemented.
- **Evidence**: `src/Sonarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/Sonarr.Http/Authentication/AuthenticationBuilderExtensions.cs`, `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: Sonarr stores sensitive data including: user credentials (Forms auth passwords in the Users table), the master API key, download client credentials (usernames, passwords, API keys for SABnzbd, NZBGet, qBittorrent, etc.), indexer API keys, and notification service tokens (Discord webhooks, Telegram bot tokens, Plex tokens). None of this data has field-level classification tags. There is no data classification framework, no tagging system, and no Macie or equivalent integration. The `CleanseLogMessage.cs` class redacts secrets from logs using regex patterns, which provides some protection but is not a substitute for systematic data classification.
- **Gap**: No field-level data classification. No controls preventing an agent from retrieving sensitive credentials through the API (e.g., download client configurations include credentials in API responses). Without classification, there is no mechanism to restrict agent access to sensitive fields.
- **Remediation**:
  - **Immediate**: Audit all API response models that may expose credentials. Implement response-level redaction for sensitive fields (passwords, API keys, tokens) in API responses intended for agent consumption. At minimum, ensure the existing `CleanseLogMessage` patterns cover all credential types stored in the database.
  - **Target State**: Sensitive fields are classified at the model level (e.g., `[SensitiveData]` attribute), and API serialization automatically redacts or excludes classified fields for agent-scoped API keys.
  - **Estimated Effort**: Medium (3–6 weeks for field classification and response filtering)
  - **Dependencies**: AUTH-Q1 (multi-key identity) is needed first so agent-scoped keys can have different field visibility than admin keys.
- **Evidence**: `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (PostgresPassword, ApiKey in plaintext), `src/NzbDrone.Common/Instrumentation/CleanseLogMessage.cs` (log redaction rules), `src/NzbDrone.Core/Download/DownloadClientDefinition.cs`, `src/NzbDrone.Core/Indexers/`

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Sonarr has no permission scoping mechanism. The single API key grants full access to all API endpoints — read and write. There is no role-based access control, no IAM policies, and no API gateway resource policies. All authenticated consumers (API key or Forms auth) receive identical, unrestricted access to the entire API surface.
- **Gap**: No mechanism to grant an agent read-only access to specific resources (e.g., series and episodes) without also granting write access to settings, download clients, and system configuration.
- **Compensating Controls**:
  - Deploy a reverse proxy (e.g., nginx, Caddy) in front of Sonarr that restricts agent-scoped API keys to GET methods only on specific endpoint paths.
  - Use an API gateway layer that enforces method-level restrictions per API key before requests reach Sonarr.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement role-based API key scoping — at minimum, distinguish between "read-only" and "admin" API key tiers. This can be achieved by extending `ApiKeyAuthenticationHandler` to carry role claims and adding `[Authorize(Roles = "Admin")]` attributes on write endpoints.
- **Evidence**: `src/Sonarr.Http/Authentication/ApiKeyAuthenticationHandler.cs` (single claim: `ApiKey=true`), `src/NzbDrone.Host/Startup.cs` (FallbackPolicy requires authenticated but no role differentiation)

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization exists. Once authenticated via API key or Forms authentication, all endpoints are accessible with all HTTP methods. There are no `canRead`/`canWrite`/`canDelete` checks in any controller or middleware. The `UiAuthorizationHandler` handles only local-address bypass for UI auth — it does not implement action-level controls.
- **Gap**: An agent authenticated with read-only intent can execute DELETE, POST, and PUT operations because no action-level checks exist.
- **Compensating Controls**:
  - Proxy-level enforcement of HTTP method restrictions (allow only GET/HEAD for agent API keys).
  - Agent orchestration layer restricts which tool definitions expose write operations.
- **Remediation Timeline**: 60–90 days (aligned with AUTH-Q2 role-based scoping)
- **Recommendation**: Add action-level authorization attributes to controllers. RestController already distinguishes `[RestGetById]`, `[RestPostById]`, `[RestPutById]`, `[RestDeleteById]` — add role-based authorization requirements on write attributes.
- **Evidence**: `src/Sonarr.Http/REST/RestController.cs`, `src/Sonarr.Http/Authentication/UiAuthorizationHandler.cs`, `src/Sonarr.Api.V3/Series/SeriesController.cs`

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Sonarr logs authentication events via `AuthenticationService.cs` (success, failure, unauthorized, logout) with IP address and username. Request logging in `LoggingMiddleware.cs` records method, path, status code, and duration with request sequence IDs. Logs are stored in the SQLite/PostgreSQL log database via `DatabaseTarget.cs` and in file system via NLog `CleansingFileTarget`. However, logs are **not immutable** — the log database can be modified, and log files can be deleted or edited. There is no tamper-evident logging (no CloudTrail, no S3 object lock, no log integrity verification).
- **Gap**: Log database entries can be modified or deleted. File-based logs have no integrity protection. No mechanism to prove logs have not been tampered with after the fact.
- **Compensating Controls**:
  - Forward logs to an external immutable log aggregator (e.g., syslog to a remote server with write-only access). Sonarr already supports syslog output via `ReconfigureLogging.cs`.
  - Enable Sonarr's syslog integration to stream logs to a tamper-evident log service.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure syslog forwarding to an external immutable log store. Sonarr's `ReconfigureLogging.cs` already implements syslog via NLog.Targets.Syslog — this is a configuration change, not a code change.
- **Evidence**: `src/Sonarr.Http/Authentication/AuthenticationService.cs`, `src/Sonarr.Http/Middleware/LoggingMiddleware.cs`, `src/NzbDrone.Core/Instrumentation/DatabaseTarget.cs`, `src/NzbDrone.Core/Instrumentation/ReconfigureLogging.cs`

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: There is only one API key shared across all consumers. `ResetApiKeyCommand` regenerates the API key, which invalidates **all** API consumers simultaneously — not just one agent. There is no per-agent identity to suspend individually.
- **Gap**: Cannot isolate a misbehaving agent without disrupting all other API consumers (including the web UI, other tools, and other agents).
- **Compensating Controls**:
  - If a proxy-based multi-key approach is used (see AUTH-Q1 remediation), the proxy can revoke individual keys without affecting Sonarr's master key.
  - Implement network-level blocking of specific agent IPs as an emergency stop.
- **Remediation Timeline**: 60–90 days (resolved simultaneously with AUTH-Q1 multi-key support)
- **Recommendation**: Implement multi-key support as described in AUTH-Q1. Each key can then be independently disabled.
- **Evidence**: `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (`Execute(ResetApiKeyCommand)` regenerates single key), `src/Sonarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`

#### STATE-Q1: Compensation and Rollback ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No compensation or rollback mechanisms exist. `BasicRepository.cs` performs direct INSERT, UPDATE, and DELETE operations. The command system (`CommandController.cs`, `IManageCommandQueue`) supports command queuing and cancellation but not rollback of completed commands. There are no saga patterns, no two-phase commit, no undo endpoints. Database operations use simple transactions via `BeginTransaction(IsolationLevel.ReadCommitted)` for batch inserts only — not for multi-step workflow rollback.
- **Gap**: If a multi-step operation (e.g., add series → scan library → configure quality profile) fails partway through, there is no mechanism to undo completed steps.
- **Compensating Controls**:
  - For read-only agents, this risk is mitigated by scope — read operations have no state to roll back.
  - For future write-enabled agents, implement compensating delete/update operations as explicit API calls in the agent orchestration layer.
- **Remediation Timeline**: 90–180 days
- **Recommendation**: For the current read-only scope, no immediate action required. Document the compensating actions for each write operation to prepare for future write-enabled agent integration.
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs`, `src/Sonarr.Api.V3/Commands/CommandController.cs`

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Sonarr calls multiple external services: indexers (Newznab, Torznab providers), download clients (SABnzbd, NZBGet, qBittorrent, Deluge, Transmission), metadata sources (TheTVDB, TMDB), and notification services (Discord, Telegram, Plex, Emby). The HTTP client in `NzbDrone.Common/Http/HttpClient.cs` has basic timeout and redirect handling but **no circuit breaker pattern**. The `BasicRepository` uses Polly `RetryStrategy` for SQLite busy errors (retry 3 times with exponential backoff and jitter), but this is database-level, not external-service-level. `IRateLimitService` is used for outbound rate limiting to respect external provider limits, but this is not a circuit breaker — it does not trip on failure patterns.
- **Gap**: If an external indexer or download client goes down, Sonarr will continue sending requests, potentially cascading the failure. An agent calling Sonarr endpoints that depend on failing external services will experience degraded responses without clear failure signaling.
- **Compensating Controls**:
  - The existing `DownloadClientStatusService` and `IndexerStatusService` track provider health and temporarily disable failing providers — this is a partial circuit-breaker equivalent at the application logic level.
  - Monitor agent-facing endpoints and implement timeout limits in the agent orchestration layer.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add Polly circuit breaker policies to the `HttpClient` for external service calls, particularly for indexer and download client communications.
- **Evidence**: `src/NzbDrone.Common/Http/HttpClient.cs`, `src/NzbDrone.Core/Datastore/BasicRepository.cs` (Polly retry for SQLite only)

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No rate limiting middleware exists in the Sonarr HTTP pipeline. The `Startup.cs` middleware pipeline includes logging, caching, buffering, authentication, and authorization but no rate limiting. There is no API gateway in front of the self-hosted Kestrel server. The `IRateLimitService` in `HttpClient.cs` applies to **outbound** requests to external providers (to respect their rate limits), not to **inbound** API requests.
- **Gap**: An agent calling Sonarr's API at machine speed could overwhelm the self-hosted application, starving the web UI and other consumers. No mechanism to throttle individual consumers.
- **Compensating Controls**:
  - Deploy a reverse proxy (nginx, Caddy) with rate limiting rules in front of Sonarr.
  - Implement rate limiting in the agent orchestration layer (throttle tool calls to Sonarr).
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add ASP.NET Core rate limiting middleware (`Microsoft.AspNetCore.RateLimiting`) to the pipeline. Configure per-API-key limits (when multi-key is available) or per-IP limits as a starting point.
- **Evidence**: `src/NzbDrone.Host/Startup.cs` (middleware pipeline has no rate limiter), `src/NzbDrone.Common/Http/HttpClient.cs` (`IRateLimitService` is outbound-only)

#### DATA-Q2: Data Residency and Sovereignty ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Sonarr is a self-hosted desktop/server application. Data is stored locally in SQLite databases or optionally in a user-configured PostgreSQL instance. There are no data residency controls in the application itself — data location is determined entirely by where the user installs Sonarr. No GDPR, LGPD, or data sovereignty references exist in the codebase or documentation.
- **Gap**: If an agent reads data from a locally-hosted Sonarr instance and transmits it to an LLM provider in a different jurisdiction, the user's locally-stored data (which may include IP addresses, usernames, file paths revealing personal information) could cross compliance boundaries.
- **Compensating Controls**:
  - Ensure the LLM provider endpoint is in the same jurisdiction as the Sonarr instance.
  - Implement data filtering in the agent layer to strip any personally identifiable fields before sending to LLM.
- **Remediation Timeline**: 30–60 days (agent architecture decision, not Sonarr code change)
- **Recommendation**: Document data residency considerations in the agent deployment guide. Use Amazon Bedrock with in-region endpoints to keep data within the user's jurisdiction.
- **Evidence**: `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (PostgreSQL connection configured locally), `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs`

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Sonarr implements `CleanseLogMessage.cs` which redacts API keys, tokens, passwords, usernames, tracker announce keys, webhook URLs, and home directory paths from log messages using extensive regex patterns. This is applied via `CleansingFileTarget`, `CleansingConsoleLogLayout`, `CleansingClefLogLayout`, and in the `DatabaseTarget.cs` for log database entries. Sentry event cleansing also applies these rules. However, the redaction is **secret-focused, not PII-focused** — it targets credentials and authentication tokens but does not redact email addresses, IP addresses of users (only partially — successful auth logs expose remote IPs), file paths containing media content names, or series/episode titles that could reveal viewing habits.
- **Gap**: Agent-initiated log entries may contain user viewing habits (series names, episode tracking), file system paths revealing personal information, and IP addresses. These are not systematically redacted.
- **Compensating Controls**:
  - `CleanseRemoteIPRegex` partially masks non-local IP addresses (e.g., `192.*.*.168`), but this only applies to auth-related log lines.
  - Limit agent log verbosity to minimize PII exposure in log entries.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Extend `CleanseLogMessage` with additional PII patterns (email regex, full IP masking in all log contexts). For agent-specific logging, consider a dedicated log target with stricter redaction rules.
- **Evidence**: `src/NzbDrone.Common/Instrumentation/CleanseLogMessage.cs`, `src/NzbDrone.Core/Instrumentation/DatabaseTarget.cs`, `src/NzbDrone.Common/Instrumentation/CleansingFileTarget.cs`

### RISK-QUALITY — Address as Capacity Allows

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Sonarr implements structured error responses via `ErrorModel` (properties: `Message`, `Description`, `Content`) and `SonarrErrorPipeline`. The pipeline distinguishes between `ApiException` (custom status codes), `ValidationException` (400 with FluentValidation error details), `NzbDroneClientException`, `ModelNotFoundException` (404), `ModelConflictException` (409), and `SQLiteException` (constraint failures → 409). All error responses are JSON. However, there is **no `retryable` boolean or error code taxonomy** — agents cannot programmatically distinguish retriable errors (e.g., SQLite busy) from terminal errors (e.g., validation failure) without parsing the message string.
- **Gap**: No machine-readable retryability indicator. No error code enumeration beyond HTTP status codes.
- **Compensating Controls**:
  - Agent tool definitions can map HTTP status codes to retry behavior (e.g., 409 → retry, 400 → terminal, 500 → retry with backoff).
  - The existing `TooManyRequestsException` (429) is properly thrown by the HTTP client for outbound requests — extend this pattern to inbound responses.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add an `errorCode` field and `retryable` boolean to `ErrorModel`. Define a simple taxonomy: `VALIDATION_ERROR`, `NOT_FOUND`, `CONFLICT`, `INTERNAL_ERROR`, `RATE_LIMITED`.
- **Evidence**: `src/Sonarr.Http/ErrorManagement/ErrorModel.cs`, `src/Sonarr.Http/ErrorManagement/SonarrErrorPipeline.cs`

#### AUTH-Q4: Identity Propagation and Delegation — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Sonarr is a self-hosted, predominantly single-user application. There is no identity propagation through service calls, no JWT parsing middleware, no OAuth2 on-behalf-of flows, and no token exchange patterns. Authentication is binary: either the API key matches (full access) or Forms auth succeeds (full access). There is no concept of an agent acting on behalf of a specific user vs. acting under its own identity.
- **Gap**: Cannot distinguish agent-as-self from agent-on-behalf-of-user. No delegation model.
- **Compensating Controls**:
  - For a single-user self-hosted application, identity propagation is less critical — the agent and the user are in the same trust boundary.
  - Add a custom `X-On-Behalf-Of` header that agents include, logged by LoggingMiddleware for attribution.
- **Remediation Timeline**: 90–120 days
- **Recommendation**: Low priority for single-user deployments. If multi-user support is added, implement JWT-based auth with user context propagation.
- **Evidence**: `src/Sonarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/NzbDrone.Host/Startup.cs`

#### AUTH-Q5: Credential Management — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Credentials are stored in plaintext in `config.xml` (API key, PostgreSQL password, SSL cert password) and managed via `ConfigFileProvider.cs`. The API key is an auto-generated GUID. Download client and indexer credentials are stored in the SQLite/PostgreSQL database. There is no secrets management integration — no Vault, no AWS Secrets Manager, no encrypted credential store. Environment variables can override config file values via `IOptions<PostgresOptions>` and `IOptions<AuthOptions>`, which is marginally better than config files.
- **Gap**: Credentials stored in plaintext files. No rotation mechanism (except manual API key reset). No encrypted credential storage.
- **Compensating Controls**:
  - Use environment variables instead of config.xml for sensitive values (already supported).
  - Restrict file system permissions on `config.xml` to the Sonarr process user only.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: For self-hosted deployments, document best practices for credential management (environment variables, file permissions). For container deployments, use Docker secrets or Kubernetes secrets to inject credentials.
- **Evidence**: `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (plaintext config), `src/NzbDrone.Common/Options/PostgresOptions.cs`

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Sonarr maintains versioned APIs at `/api/v3/` and `/api/v5/` using `VersionedApiControllerAttribute`. OpenAPI specs are maintained at `src/Sonarr.Api.V3/openapi.json` and `src/Sonarr.Api.V5/openapi.json`, auto-generated via Swashbuckle/SwaggerGen. A dedicated CI workflow (`api_docs.yml`) auto-generates and commits updated OpenAPI specs on changes to API controllers. The `RestController` adds `Deprecation: true` headers for deprecated endpoints. However, there is **no breaking change detection in CI** — no OpenAPI diff tooling, no Pact consumer-driven contract tests, no `buf breaking` equivalent.
- **Gap**: API changes can be introduced without automated detection of breaking changes. Agent tool bindings could break silently.
- **Compensating Controls**:
  - The auto-generated OpenAPI specs in CI provide a diffable artifact — breaking changes would appear in PR diffs of `openapi.json`.
  - Manual review of `openapi.json` changes in PRs catches some breaking changes.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add an OpenAPI diff step to the CI pipeline (e.g., `oasdiff` or `openapi-diff`) that fails the build on breaking changes. This is a lightweight CI addition.
- **Evidence**: `src/Sonarr.Http/VersionedApiControllerAttribute.cs`, `.github/workflows/api_docs.yml`, `src/Sonarr.Api.V3/openapi.json`, `src/Sonarr.Api.V5/openapi.json`

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Sonarr uses NLog for logging. `LoggingMiddleware.cs` assigns sequential request IDs (`ApiRequestSequenceID`) and logs request start/end with method, path, status code, and duration. Logs are stored in SQLite/PostgreSQL via `DatabaseTarget.cs` and in file system via `CleansingFileTarget`. MiniProfiler is integrated for debug builds. However, there is **no distributed tracing** — no OpenTelemetry, no X-Ray instrumentation, no `traceparent` header propagation. Logs are not structured JSON by default (NLog layout-based formatting). The `CleansingClefLogLayout` suggests CLEF (Compact Log Event Format) support for structured logging, but it is not the default.
- **Gap**: No trace ID propagation for cross-service debugging. No structured JSON logging by default. Request sequence IDs are local to the Sonarr instance, not propagated to external service calls.
- **Compensating Controls**:
  - The request sequence ID provides local request correlation within Sonarr.
  - MiniProfiler provides performance profiling for debug builds.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add OpenTelemetry SDK integration for distributed tracing. ASP.NET Core has built-in support via `AddOpenTelemetry()`. Enable CLEF structured logging as the default format for machine consumption.
- **Evidence**: `src/Sonarr.Http/Middleware/LoggingMiddleware.cs`, `src/NzbDrone.Core/Instrumentation/DatabaseTarget.cs`, `src/NzbDrone.Common/Instrumentation/CleansingClefLogLayout.cs`

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Sonarr has Sentry integration for error tracking (`ReconfigureSentry.cs`, `SentryTarget`), which captures exceptions in production builds and sends them to Sentry.io. The build pipeline sends Discord notifications on build success/failure. However, there are **no alerting thresholds** on API error rates or latency. No CloudWatch alarms, no PagerDuty/OpsGenie integration, no SLO-based alerting. The HealthCheck system (`src/NzbDrone.Core/HealthCheck/`) monitors internal health (disk space, download clients, indexers) but does not expose alerting for API performance metrics.
- **Gap**: No automated alerting when API error rates spike or latency degrades. Agents will experience degradation without notification to operators.
- **Compensating Controls**:
  - Sentry captures errors and can be configured with alerting rules for error rate thresholds.
  - Deploy an external monitoring tool (e.g., Uptime Kuma) to monitor Sonarr's health endpoint.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure Sentry alerting rules for error rate spikes. Add a `/api/health` endpoint that reports API latency percentiles for external monitoring.
- **Evidence**: `src/NzbDrone.Core/Instrumentation/ReconfigureSentry.cs`, `src/NzbDrone.Core/HealthCheck/`, `.github/workflows/build_v5.yml` (Discord notifications)

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No dedicated sandbox or staging environment exists. The `docker/tests/` directory contains legacy Mono build test configurations, not API testing environments. The CI pipeline (`build_v5.yml`) runs unit tests and integration tests (`NzbDrone.Integration.Test`) across multiple platforms (Linux, macOS, Windows) and PostgreSQL versions (16, 17, 18), which provides strong test coverage. However, there is no staging environment with production-equivalent data shape for agent testing. The application can be run locally for development, but no seed data scripts or synthetic data generators exist for creating realistic test environments.
- **Gap**: No staging environment for agent testing. First agent integration testing would need to occur against a development instance with manually configured data.
- **Compensating Controls**:
  - Sonarr can be easily installed as a second instance on a different port for testing purposes.
  - Docker deployment enables quick spin-up of isolated test instances.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a Docker Compose configuration for a test environment with seed data (sample series, episodes, quality profiles) that agents can test against without risk to a production instance.
- **Evidence**: `docker/tests/`, `.github/workflows/build_v5.yml`, `src/NzbDrone.Integration.Test/`

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No Infrastructure as Code exists. Sonarr is a self-hosted desktop/server application distributed as platform-specific binaries (Windows installer, Linux tar.gz, macOS app, Docker images). The `distribution/docker-build/Dockerfile` is a legacy Mono build container, not a deployment IaC definition. There are no Terraform modules, CloudFormation templates, CDK stacks, Helm charts, or Kustomize configurations. Infrastructure (API gateway, IAM, secrets, networking) is not defined as code because the application runs directly on user hardware.
- **Gap**: No IaC for the agent-facing surface. Infrastructure configuration (port binding, SSL, authentication settings) is managed through `config.xml` — not version-controlled or peer-reviewed.
- **Compensating Controls**:
  - Configuration changes through the web UI are logged.
  - For Docker deployments, environment variables and docker-compose files can serve as lightweight IaC.
- **Remediation Timeline**: 60–90 days (if cloud deployment is planned)
- **Recommendation**: For agent integration, create a reference Docker Compose or Helm chart that defines the recommended deployment topology (Sonarr + reverse proxy with rate limiting + log aggregation). This serves as lightweight IaC for the agent-facing surface.
- **Evidence**: `distribution/docker-build/Dockerfile` (legacy build container only), `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (XML config)

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Sonarr has a comprehensive CI/CD pipeline via GitHub Actions (`build_v5.yml`). The pipeline includes: multi-platform builds (10 runtime targets), unit tests on Linux/macOS/Windows, PostgreSQL compatibility tests (versions 16, 17, 18), integration tests with binary artifacts, frontend linting and builds, and automated deployment with release creation. The `api_docs.yml` workflow auto-generates OpenAPI specs on API changes. However, there are **no API contract tests** — no Pact tests, no OpenAPI validation against actual responses, no schema comparison in CI.
- **Gap**: API changes are not validated against consumer expectations. No breaking change detection for agent tool bindings.
- **Compensating Controls**:
  - The integration test suite (`NzbDrone.Integration.Test`) tests API endpoints functionally, which provides indirect contract validation.
  - Auto-generated OpenAPI specs create a diffable artifact for manual review.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add an OpenAPI diff step to the CI pipeline and consider consumer-driven contract tests for critical agent-consumed endpoints.
- **Evidence**: `.github/workflows/build_v5.yml`, `.github/workflows/api_docs.yml`, `src/NzbDrone.Integration.Test/ApiTests/`

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Sonarr distributes versioned releases via GitHub Releases with SHA256 checksums. The update mechanism is built into the application (`src/NzbDrone.Update/`) and supports automatic updates. The `deploy.yml` workflow creates GitHub releases with tagged versions. However, there is **no automated rollback** — reverting to a previous version requires manual download and reinstallation. Database migrations may not be reversible. There are no blue/green deployments, no canary releases, no feature flags, and no traffic shifting.
- **Gap**: If a new version breaks agent-facing APIs, rollback is manual and may involve database compatibility issues.
- **Compensating Controls**:
  - Users can manually download and install a previous version from GitHub Releases.
  - The `Backup` system (`src/NzbDrone.Core/Backup/`) creates database backups before updates.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Document the rollback procedure (backup database, download previous release, restore). Consider adding reversible migrations and a rollback command to the update system.
- **Evidence**: `.github/workflows/deploy.yml`, `src/NzbDrone.Update/`, `src/NzbDrone.Core/Backup/`

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Sonarr has integration tests in `NzbDrone.Integration.Test/ApiTests/` covering: Series, Episodes, EpisodeFiles, History, Commands, Calendar, Blocklist, DownloadClient, Indexer, Notification, Queue, Release, RootFolder, DiskSpace, and Wanted endpoints. Unit tests exist in `NzbDrone.Core.Test/` for core business logic. The CI pipeline runs these tests across multiple platforms and PostgreSQL versions. However, tests focus on happy-path functionality — **no dedicated error response format validation, no edge case testing for agent consumption patterns** (e.g., pagination boundary conditions, invalid sort keys, malformed queries).
- **Gap**: Test coverage exists but does not validate agent-specific consumption patterns (structured error format, pagination edge cases, concurrent access scenarios).
- **Compensating Controls**:
  - The existing integration test suite provides a foundation for adding agent-specific test cases.
  - Multi-platform and multi-database testing ensures API behavior consistency.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add API contract test cases specifically for agent consumption: validate error response format, pagination boundaries (page 0, page beyond total), and response content types.
- **Evidence**: `src/NzbDrone.Integration.Test/ApiTests/`, `.github/workflows/build_v5.yml`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Sonarr stores persistent data in SQLite databases (default) or PostgreSQL (optional). SQLite databases are stored as unencrypted files on the local filesystem. The database contains sensitive credentials (download client passwords, indexer API keys, notification tokens, user passwords). There is **no encryption at rest** — no KMS integration, no SQLite encryption extensions, no transparent data encryption. PostgreSQL connections can use SSL, but the database files themselves have no encryption configuration in the Sonarr codebase.
- **Gap**: Database files containing credentials and user data are stored unencrypted. Physical access to the storage medium exposes all data.
- **Compensating Controls**:
  - Host-level full-disk encryption (BitLocker, LUKS, FileVault) protects data at rest at the OS level.
  - For PostgreSQL deployments, TDE can be configured at the database level independently of Sonarr.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Document full-disk encryption as a deployment requirement for agent-integrated instances. For high-security deployments, consider SQLCipher for encrypted SQLite databases.
- **Evidence**: `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs`, `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`

#### API-Q6: Asynchronous Operation Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Sonarr has long-running operations that exceed 30 seconds. The Command system provides async patterns with SignalR real-time updates. However, no timeout documentation or `Retry-After` headers on polling endpoints.
- **Gap**: No documented timeout values. No retry guidance in API responses.
- **Compensating Controls**:
  - SignalR provides real-time completion notifications, eliminating the need for polling in many cases.
  - Agent orchestration can implement exponential backoff polling for command status.
- **Remediation Timeline**: 30 days
- **Recommendation**: Document expected completion times for common commands. Add `Retry-After` header to command status responses.
- **Evidence**: `src/Sonarr.Api.V3/Commands/CommandController.cs`, `src/NzbDrone.Core/Messaging/Commands/`

#### DATA-Q3: Selective Query Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Pagination supported via `PagingResource<T>` with `page`, `pageSize`, `sortKey`, `sortDirection`. Default page size is 10. Sort key validation prevents injection. Filter expressions supported. However, no field-level selection (GraphQL-style) and offset-based only (no cursor-based pagination).
- **Gap**: Offset-based pagination may have consistency issues with concurrent modifications. No field-level selection.
- **Compensating Controls**:
  - Agent can request small page sizes to limit context window consumption.
  - Sort by ID to minimize offset drift issues.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Consider cursor-based pagination for large result sets.
- **Evidence**: `src/Sonarr.Http/PagingResource.cs`, `src/NzbDrone.Core/Datastore/BasicRepository.cs`

#### DATA-Q4: System of Record Designations — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Sonarr is authoritative for monitoring configuration, quality profiles, and root folders. External metadata (TheTVDB/TMDB) is cached, not authoritative. No formal system-of-record documentation.
- **Gap**: Agent may not know which fields are authoritative vs. cached.
- **Compensating Controls**:
  - Agent tool descriptions can document authoritative vs. cached fields.
  - `LastInfoSync` field indicates metadata freshness.
- **Remediation Timeline**: 30 days
- **Recommendation**: Document system-of-record designations in API documentation.
- **Evidence**: `src/NzbDrone.Core/Tv/RefreshSeriesService.cs`, `src/NzbDrone.Core/MetadataSource/`

#### DATA-Q5: Temporal Metadata and Freshness — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Entities include temporal fields (`Added`, `LastInfoSync`, `AirDateUtc`, `FirstAired`, `LastAired`). UTC storage used. History entries have timestamps. However, no `Cache-Control`, `X-Data-Age`, or `Last-Modified` headers in API responses. No staleness indicator.
- **Gap**: No data freshness signal in API responses.
- **Compensating Controls**:
  - `LastInfoSync` field in series responses indicates when metadata was last refreshed.
  - History API provides event timestamps for data change tracking.
- **Remediation Timeline**: 30 days
- **Recommendation**: Add `Last-Modified` headers to series and episode endpoints based on `LastInfoSync`.
- **Evidence**: `src/NzbDrone.Core/Tv/Series.cs`, `src/NzbDrone.Core/Tv/Episode.cs`

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO
- **Finding**: Sonarr exposes a well-documented REST API via ASP.NET Core controllers in `Sonarr.Api.V3` and `Sonarr.Api.V5`. The API is accessible at `/api/v3/` and `/api/v5/` with versioning via `VersionedApiControllerAttribute`. Controllers inherit from `RestController<TResource>` providing standardized CRUD patterns. The API uses API key authentication via `X-Api-Key` header. The OpenAPI specs document all endpoints with request/response schemas. There is no requirement for direct database access, file-based exchange, or UI automation. The control exists and no gap was found — the API is well-documented and suitable for agent integration.
- **Implication**: The documented REST API provides a solid foundation for agent tool binding. No integration barriers exist at the interface level.
- **Recommendation**: No action required. Maintain current API documentation practices.
- **Evidence**: `src/Sonarr.Http/REST/RestController.cs`, `src/Sonarr.Api.V3/`, `src/Sonarr.Api.V5/`, `src/NzbDrone.Host/Startup.cs`

### API-Q2: Machine-Readable API Specification

- **Severity**: INFO
- **Finding**: OpenAPI 3.0 specifications exist at `src/Sonarr.Api.V3/openapi.json` and `src/Sonarr.Api.V5/openapi.json`. These are auto-generated from Swashbuckle/SwaggerGen configured in `Startup.cs` with full schema definitions, security schemes (X-Api-Key header and apikey query parameter), and server configuration. The `api_docs.yml` CI workflow auto-generates and commits updated OpenAPI specs on API changes, keeping specs current with the implementation. The control exists and no gap was found — machine-readable specs are present and CI-maintained.
- **Implication**: Agent tool definitions can be auto-generated from the OpenAPI specs. No manual tool authoring needed.
- **Recommendation**: No action required. Maintain CI-driven OpenAPI spec generation.
- **Evidence**: `src/Sonarr.Api.V3/openapi.json`, `src/Sonarr.Api.V5/openapi.json`, `.github/workflows/api_docs.yml`, `src/NzbDrone.Host/Startup.cs`

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Write API endpoints (POST, PUT, DELETE on series, episodes, commands, etc.) do not implement idempotency keys. POST operations create new resources without duplicate detection beyond database-level unique constraints. The command system (`CommandController`) does not deduplicate identical command submissions.
- **Implication**: If agent scope is expanded to write-enabled, idempotency will become a BLOCKER. Agent retries could create duplicate series entries, trigger duplicate downloads, or submit redundant commands.
- **Recommendation**: Plan for idempotency key support on write endpoints before expanding agent scope to write-enabled.
- **Evidence**: `src/Sonarr.Api.V3/Series/SeriesController.cs`, `src/Sonarr.Api.V3/Commands/CommandController.cs`

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: All API responses are JSON, serialized via `System.Text.Json` with custom settings configured in `STJson.ApplySerializerSettings()`. The `[Produces("application/json")]` attribute is applied to controller methods. Swagger/OpenAPI specs document the response schemas. No XML, binary, or protobuf formats are used for API responses.
- **Implication**: JSON is ideal for LLM consumption. Agent tool definitions can be generated directly from the OpenAPI specs. No format transformation is needed.
- **Recommendation**: No action required. JSON is the optimal format for agent integration.
- **Evidence**: `src/NzbDrone.Host/Startup.cs` (JsonOptions configuration), `src/Sonarr.Http/REST/RestController.cs` (`[Produces("application/json")]`)

### API-Q7: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: Sonarr emits real-time state change events via a SignalR hub at `/signalr/messages`. The `RestControllerWithSignalR` base class broadcasts `ModelEvent<TModel>` events (Created, Updated, Deleted, Sync) for all managed entities. The `BroadcastResourceChange` method sends events with resource name, action, body (the changed resource), and API version. Multiple event handlers (`IHandle<T>`) respond to domain events (EpisodeImported, SeriesUpdated, CommandUpdated, etc.) and broadcast them to connected SignalR clients.
- **Implication**: SignalR provides a foundation for event-driven agent patterns. Agents can subscribe to real-time notifications instead of polling. This enables proactive agents that respond to series updates, episode imports, and download completions.
- **Recommendation**: Document the SignalR event schema for agent tool authors. Consider adding webhook support as an alternative to SignalR for agents that cannot maintain persistent connections.
- **Evidence**: `src/Sonarr.Http/REST/RestControllerWithSignalR.cs`, `src/NzbDrone.SignalR/`, `src/NzbDrone.Host/Startup.cs` (`MapHub<MessageHub>("/signalr/messages")`)

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limiting is implemented, so there are no rate limit headers (`X-RateLimit-Remaining`, `Retry-After`) in API responses. No rate limit documentation exists. The outbound `IRateLimitService` is for external provider rate limiting, not inbound API rate limiting.
- **Implication**: Agents cannot self-throttle based on server capacity signals. Agent orchestration must implement its own rate limiting logic without server-side guidance.
- **Recommendation**: When rate limiting is implemented (see STATE-Q5), include standard rate limit headers in API responses.
- **Evidence**: `src/NzbDrone.Host/Startup.cs` (no rate limit middleware), `src/NzbDrone.Common/Http/HttpClient.cs`

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No explicit concurrency controls exist for write operations. There are no version fields, no ETags, no `If-Match` headers, and no optimistic locking. SQLite provides implicit write serialization through its locking mechanism. The `BasicRepository` includes a Polly retry strategy for SQLite busy errors (`SQLiteErrorCode.Busy`), handling concurrent write contention at the database level. PostgreSQL uses `ReadCommitted` isolation level for batch operations.
- **Implication**: For read-only agents, this has no impact. If agent scope expands to write-enabled, concurrent writes from multiple agents could produce last-write-wins conflicts without optimistic locking.
- **Recommendation**: No action for read-only scope. Plan optimistic locking (ETag/version field support) before enabling write operations.
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs` (Polly retry for SQLite busy)

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits exist. There are no per-identity limits on records modified, actions per hour, or operation scope. Bulk operations (e.g., `UpdateMany`, `DeleteMany` in `BasicRepository`) have no configurable caps.
- **Implication**: For read-only agents, blast radius is limited to query load. If expanded to write-enabled, an agent could delete all series or modify all quality profiles in a single API call sequence.
- **Recommendation**: No action for read-only scope. Implement transaction limits before enabling write operations.
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs`

### STATE-Q2: Queryable Current State

- **Severity**: INFO
- **Finding**: State is fully queryable via REST API. GET endpoints exist for all major entities: series (`/api/v3/series`), episodes (`/api/v3/episode`), episode files (`/api/v3/episodefile`), history (`/api/v3/history`), queue (`/api/v3/queue`), calendar (`/api/v3/calendar`), health (`/api/v3/health`), and system status (`/api/v3/system/status`). All state-bearing entities are accessible through standardized REST patterns.
- **Implication**: Agents can inspect current state before deciding next steps. No external state tracking required.
- **Recommendation**: No action required. State queryability is comprehensive.
- **Evidence**: `src/Sonarr.Api.V3/Series/SeriesController.cs`, `src/Sonarr.Api.V3/Episodes/`, `src/Sonarr.Api.V3/Queue/`

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Sonarr has no concept of a draft or pending state for most entities. Series are either added or not. Episodes are either monitored or unmonitored. The command system has a queued/started/completed/failed lifecycle, but this is execution state, not a draft-before-commit pattern. The `SeasonPass` controller allows bulk monitoring changes but with immediate effect.
- **Implication**: Read-only agents do not need draft states. If write-enabled, agents would commit changes immediately without a review step.
- **Recommendation**: No action for read-only scope.
- **Evidence**: `src/Sonarr.Api.V3/Series/SeriesController.cs`, `src/Sonarr.Api.V3/Commands/CommandController.cs`

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable approval gates exist. All API operations execute immediately upon request. There are no approval workflow endpoints, no human-in-the-loop confirmation steps, and no configurable operation-level flags requiring manual approval.
- **Implication**: Read-only agents are not affected. Write-enabled agents would bypass any human oversight.
- **Recommendation**: No action for read-only scope.
- **Evidence**: `src/Sonarr.Api.V3/`, `src/NzbDrone.Host/Startup.cs`

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: API response field names are semantically meaningful and human-readable. Examples from the Series model: `title`, `seasonNumber`, `episodeNumber`, `airDate`, `airDateUtc`, `overview`, `monitored`, `qualityProfileId`, `seriesType`, `path`, `firstAired`, `lastAired`, `added`. No legacy abbreviations or cryptic codes are used. Field names follow camelCase convention (configured in `Startup.cs` via `DescribeAllParametersInCamelCase()`). The REST resource models in `Sonarr.Api.V3` use clear, self-documenting property names.
- **Implication**: LLM-based agents can reason about field semantics without requiring a data dictionary. Tool definitions generated from the OpenAPI spec will have interpretable parameter names.
- **Recommendation**: No action required. Maintain current naming conventions.
- **Evidence**: `src/NzbDrone.Core/Tv/Series.cs`, `src/NzbDrone.Core/Tv/Episode.cs`, `src/Sonarr.Api.V3/openapi.json`

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No formal data catalog or metadata layer exists. There is no AWS Glue Data Catalog, Collibra, Alation, DataHub, or equivalent. The OpenAPI specs (`openapi.json`) serve as the closest equivalent to a data catalog — they describe available endpoints, request/response schemas, and data types. Database migration files in `src/NzbDrone.Core/Datastore/Migration/` document the schema evolution.
- **Implication**: Agent tool authors must rely on the OpenAPI specs and API documentation to understand what data Sonarr holds. No semantic metadata layer exists for automated discovery.
- **Recommendation**: The existing OpenAPI specs are sufficient for agent tool generation. Consider adding model-level descriptions to Swagger annotations for richer metadata.
- **Evidence**: `src/Sonarr.Api.V3/openapi.json`, `src/Sonarr.Api.V5/openapi.json`, `src/NzbDrone.Core/Datastore/Migration/`

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No formal data quality scores, completeness metrics, or data profiling exist. Sonarr relies on external metadata sources (TheTVDB, TMDB) for series/episode data, which may have gaps. The application does not track null rates, duplicate detection, or data freshness SLAs. HealthChecks flag configuration issues but not data quality issues.
- **Implication**: Agents reasoning about series completeness or episode availability may encounter missing data without a quality signal. The History API can be queried for freshness but there is no explicit data quality metric.
- **Recommendation**: Low priority. Consider exposing a data completeness indicator (e.g., "episodes with files / total episodes") as a metric for agent decision-making.
- **Evidence**: `src/NzbDrone.Core/HealthCheck/`, `src/NzbDrone.Core/History/`

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: Sonarr tracks internal health checks (`src/NzbDrone.Core/HealthCheck/`) for operational status (disk space, download client connectivity, indexer availability). Sentry captures exceptions for production error tracking. However, there are **no custom business outcome metrics** — no tracking of series completion rates, download success rates, episode import rates, or search hit rates as publishable metrics. Logging captures these events textually but not as structured metrics.
- **Implication**: No quantitative metrics for measuring whether agent interactions produce good business outcomes.
- **Recommendation**: Expose key business metrics via a `/api/metrics` endpoint or integrate with OpenTelemetry metrics for structured metric collection.
- **Evidence**: `src/NzbDrone.Core/HealthCheck/`, `src/NzbDrone.Core/History/`, `src/NzbDrone.Core/Instrumentation/ReconfigureSentry.cs`

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: Sonarr exposes a well-documented REST API via ASP.NET Core controllers in `Sonarr.Api.V3` and `Sonarr.Api.V5`. The API is accessible at `/api/v3/` and `/api/v5/` with versioning via `VersionedApiControllerAttribute`. Controllers inherit from `RestController<TResource>` providing standardized CRUD patterns. The API uses API key authentication via `X-Api-Key` header. The OpenAPI specs document all endpoints with request/response schemas. There is no requirement for direct database access, file-based exchange, or UI automation. The control exists and no gap was found — the API is well-documented and suitable for agent integration.
- **Gap**: None — documented REST API exists and is suitable for agent tool binding.
- **Recommendation**: No action required. Maintain current API documentation practices.
- **Evidence**: `src/Sonarr.Http/REST/RestController.cs`, `src/Sonarr.Api.V3/`, `src/Sonarr.Api.V5/`, `src/NzbDrone.Host/Startup.cs`

#### API-Q2: Machine-Readable API Specification
- **Severity**: INFO
- **Finding**: OpenAPI 3.0 specifications exist at `src/Sonarr.Api.V3/openapi.json` and `src/Sonarr.Api.V5/openapi.json`. These are auto-generated from Swashbuckle/SwaggerGen configured in `Startup.cs` with full schema definitions, security schemes (X-Api-Key header and apikey query parameter), and server configuration. The `api_docs.yml` CI workflow auto-generates and commits updated OpenAPI specs on API changes, keeping specs current with the implementation. The control exists and no gap was found — machine-readable specs are present and CI-maintained.
- **Gap**: None — machine-readable specs exist and are kept current via CI automation.
- **Recommendation**: No action required. Maintain CI-driven OpenAPI spec generation.
- **Evidence**: `src/Sonarr.Api.V3/openapi.json`, `src/Sonarr.Api.V5/openapi.json`, `.github/workflows/api_docs.yml`, `src/NzbDrone.Host/Startup.cs`

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: Structured error responses via `ErrorModel` (Message, Description, Content) with type-specific handling in `SonarrErrorPipeline`. No retryable indicator or error code taxonomy.
- **Gap**: No machine-readable retryability. No error code enumeration.
- **Recommendation**: Add `errorCode` and `retryable` fields to `ErrorModel`.
- **Evidence**: `src/Sonarr.Http/ErrorManagement/ErrorModel.cs`, `src/Sonarr.Http/ErrorManagement/SonarrErrorPipeline.cs`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No idempotency key support on write endpoints. POST creates without duplicate detection. Command system does not deduplicate.
- **Gap**: Write endpoints are not idempotent.
- **Recommendation**: Plan idempotency support before expanding to write-enabled scope.
- **Evidence**: `src/Sonarr.Api.V3/Series/SeriesController.cs`, `src/Sonarr.Api.V3/Commands/CommandController.cs`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: JSON responses via System.Text.Json. All controllers produce `application/json`.
- **Gap**: N/A
- **Recommendation**: No action required.
- **Evidence**: `src/NzbDrone.Host/Startup.cs`, `src/Sonarr.Http/REST/RestController.cs`

#### API-Q6: Asynchronous Operation Support
- **Severity**: RISK-QUALITY
- **Finding**: Sonarr has long-running operations (library scans, download processing, series refresh) that exceed 30 seconds. The Command system (`CommandController`) provides an async pattern: commands are submitted via POST to `/api/v3/command`, return a command ID, and can be polled via GET. SignalR broadcasts command status updates (queued, started, completed, failed) in real-time. This constitutes a proper async pattern for long-running tasks.
- **Gap**: While the pattern exists, there are no explicit timeout values documented in the API spec, and the polling endpoint does not include `Retry-After` headers.
- **Recommendation**: Document expected completion times for common commands. Add `Retry-After` header to command status responses.
- **Evidence**: `src/Sonarr.Api.V3/Commands/CommandController.cs`, `src/NzbDrone.Core/Messaging/Commands/`

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: SignalR hub at `/signalr/messages` provides real-time state change notifications for all managed entities.
- **Gap**: No webhook alternative for agents without persistent connections.
- **Recommendation**: Document SignalR event schema. Consider webhook support.
- **Evidence**: `src/Sonarr.Http/REST/RestControllerWithSignalR.cs`, `src/NzbDrone.SignalR/`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limiting implemented. No rate limit headers in responses.
- **Gap**: No server-side rate limit signals for agent self-throttling.
- **Recommendation**: Include rate limit headers when rate limiting is implemented.
- **Evidence**: `src/NzbDrone.Host/Startup.cs`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: Single shared API key via `X-Api-Key` header. No per-principal attribution. All API key users get identical claim (`ApiKey=true`).
- **Gap**: No per-agent identity. No audit attribution for individual consumers.
- **Recommendation**: Implement multi-key registry with named principals.
- **Evidence**: `src/Sonarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: No permission scoping. API key grants full access to all endpoints. No RBAC.
- **Gap**: Cannot grant read-only access without also granting write access.
- **Recommendation**: Implement role-based API key scoping (read-only vs admin tiers).
- **Evidence**: `src/Sonarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/NzbDrone.Host/Startup.cs`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization. All authenticated users have full read/write/delete access.
- **Gap**: Agent with read-only intent can execute write operations.
- **Recommendation**: Add role-based authorization attributes to controller write methods.
- **Evidence**: `src/Sonarr.Http/REST/RestController.cs`, `src/Sonarr.Api.V3/Series/SeriesController.cs`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: RISK-QUALITY
- **Finding**: No identity propagation. Single-user desktop/server application. No JWT, no token exchange, no on-behalf-of flows.
- **Gap**: Cannot distinguish agent-as-self from agent-on-behalf-of-user.
- **Recommendation**: Low priority for single-user deployments.
- **Evidence**: `src/Sonarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`

#### AUTH-Q5: Credential Management
- **Severity**: RISK-QUALITY
- **Finding**: Credentials in plaintext `config.xml`. API key is auto-generated GUID. No secrets management. Environment variable overrides available for PostgreSQL credentials.
- **Gap**: No encrypted credential storage. No rotation mechanism.
- **Recommendation**: Document environment variable best practices. Use Docker secrets for container deployments.
- **Evidence**: `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Auth events logged. Request logging with sequence IDs. Logs stored in database and files. Not immutable — no tamper evidence.
- **Gap**: Logs can be modified or deleted. No integrity verification.
- **Recommendation**: Configure syslog forwarding to external immutable store (already supported via NLog.Targets.Syslog).
- **Evidence**: `src/Sonarr.Http/Authentication/AuthenticationService.cs`, `src/Sonarr.Http/Middleware/LoggingMiddleware.cs`, `src/NzbDrone.Core/Instrumentation/DatabaseTarget.cs`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: Single shared API key. `ResetApiKeyCommand` invalidates all consumers. No per-agent identity suspension.
- **Gap**: Cannot isolate misbehaving agent without disrupting all consumers.
- **Recommendation**: Implement multi-key support (resolves with AUTH-Q1).
- **Evidence**: `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`, `src/Sonarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No compensation or rollback mechanisms. Direct INSERT/UPDATE/DELETE via `BasicRepository`. No saga pattern, no undo endpoints.
- **Gap**: Multi-step operations cannot be undone if they fail partway through.
- **Recommendation**: Document compensating actions for write operations. No immediate action for read-only scope.
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs`, `src/Sonarr.Api.V3/Commands/CommandController.cs`

#### STATE-Q2: Queryable Current State
- **Severity**: INFO
- **Finding**: State is fully queryable via REST API. GET endpoints exist for all major entities: series (`/api/v3/series`), episodes (`/api/v3/episode`), episode files (`/api/v3/episodefile`), history (`/api/v3/history`), queue (`/api/v3/queue`), calendar (`/api/v3/calendar`), health (`/api/v3/health`), and system status (`/api/v3/system/status`). All state-bearing entities are accessible through standardized REST patterns.
- **Gap**: Minor — some operational state (internal command queue, in-progress downloads) is queryable but may have eventual consistency delays.
- **Recommendation**: No action required. State queryability is comprehensive.
- **Evidence**: `src/Sonarr.Api.V3/Series/SeriesController.cs`, `src/Sonarr.Api.V3/Episodes/`, `src/Sonarr.Api.V3/Queue/`

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No explicit optimistic locking. SQLite serializes writes implicitly. Polly retry for SQLite busy errors.
- **Gap**: No version fields, ETags, or If-Match headers.
- **Recommendation**: Plan optimistic locking before enabling write operations.
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: No circuit breaker patterns for external service calls. Polly retry exists only for SQLite busy errors. Outbound rate limiting exists but no circuit breaking.
- **Gap**: Failing external services can cascade to agent-facing endpoints.
- **Recommendation**: Add Polly circuit breaker policies to `HttpClient` for external calls.
- **Evidence**: `src/NzbDrone.Common/Http/HttpClient.cs`, `src/NzbDrone.Core/Datastore/BasicRepository.cs`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No inbound rate limiting middleware. Self-hosted Kestrel with no API gateway. `IRateLimitService` is outbound-only.
- **Gap**: No protection against agent traffic storms overwhelming the application.
- **Recommendation**: Add ASP.NET Core rate limiting middleware.
- **Evidence**: `src/NzbDrone.Host/Startup.cs`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits. No per-identity caps on operations.
- **Gap**: No blast radius controls for write operations.
- **Recommendation**: No action for read-only scope.
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path. Sonarr is P2 priority and not on the critical path.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No draft or pending state concept. Entities are created or modified immediately. Command system has execution state (queued/started/completed) but not a draft-before-commit pattern.
- **Gap**: No review step before committing changes.
- **Recommendation**: No action for read-only scope.
- **Evidence**: `src/Sonarr.Api.V3/Series/SeriesController.cs`

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable approval gates. All operations execute immediately upon request.
- **Gap**: No human-in-the-loop confirmation for any operation.
- **Recommendation**: No action for read-only scope.
- **Evidence**: `src/Sonarr.Api.V3/`, `src/NzbDrone.Host/Startup.cs`

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: No dedicated staging environment. Docker test configs exist for build testing only. CI runs comprehensive tests but no production-equivalent test environment for agent testing.
- **Gap**: No staging environment with realistic data for agent testing.
- **Recommendation**: Create Docker Compose test environment with seed data.
- **Evidence**: `docker/tests/`, `.github/workflows/build_v5.yml`, `src/NzbDrone.Integration.Test/`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: Sensitive data (credentials, API keys, tokens) stored without field-level classification. No tagging system. `CleanseLogMessage` provides log-level redaction but not API-level data classification.
- **Gap**: No controls preventing agent from retrieving sensitive fields through the API.
- **Recommendation**: Implement field-level classification attributes and response-level redaction for agent API keys.
- **Evidence**: `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`, `src/NzbDrone.Common/Instrumentation/CleanseLogMessage.cs`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Self-hosted application. Data stored locally (SQLite or PostgreSQL). No data residency controls in the application. Data location determined by user installation.
- **Gap**: Agent transmitting data to LLM in different jurisdiction could cross compliance boundaries.
- **Recommendation**: Document data residency considerations. Use in-region LLM endpoints.
- **Evidence**: `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`, `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK-QUALITY
- **Finding**: Pagination is supported via `PagingResource<T>` with `page`, `pageSize`, `sortKey`, and `sortDirection` parameters. The `PagingSpec<TModel>` class in `BasicRepository.cs` implements server-side pagination with SQL LIMIT/OFFSET. Sort key validation ensures only allowed keys are used. Default page size is 10 records. Filter expressions are supported for query refinement. Multiple list endpoints (history, queue, wanted, blocklist) use this pagination framework.
- **Gap**: No field-level selection (GraphQL-style). No cursor-based pagination (offset-based only, which can have consistency issues with concurrent modifications).
- **Recommendation**: Consider cursor-based pagination for large result sets where offset-based pagination may skip or duplicate records during concurrent writes.
- **Evidence**: `src/Sonarr.Http/PagingResource.cs`, `src/NzbDrone.Core/Datastore/BasicRepository.cs` (`GetPagedRecords`), `src/NzbDrone.Core/Datastore/PagingSpec.cs`

#### DATA-Q4: System of Record Designations
- **Severity**: RISK-QUALITY
- **Finding**: Sonarr is the authoritative system of record for: series monitoring configuration, quality profile assignments, download client mappings, and root folder configurations. It is NOT the system of record for: series/episode metadata (sourced from TheTVDB/TMDB), download status (sourced from download clients), or media file existence (sourced from file system scans). There is no formal master data management or golden record designation. Metadata refresh commands re-sync from authoritative sources.
- **Gap**: No documented system-of-record designations. An agent may not know which fields are authoritative vs. cached from external sources.
- **Recommendation**: Document which entities/fields are authoritative in Sonarr vs. cached from external sources. Add a `sourceOfTruth` field to API documentation.
- **Evidence**: `src/NzbDrone.Core/Tv/RefreshSeriesService.cs`, `src/NzbDrone.Core/MetadataSource/`

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK-QUALITY
- **Finding**: Sonarr entities include temporal fields: `Series.Added` (UTC DateTime), `Series.LastInfoSync` (DateTime), `Episode.AirDateUtc` (UTC DateTime), `Series.FirstAired`, `Series.LastAired`. History entries have timestamps. The `LastInfoSync` field indicates when series metadata was last refreshed from external sources. However, there is no `Cache-Control` or `X-Data-Age` header in API responses, and no explicit staleness indicator. All timestamps use UTC storage. No `consistency_level` field exists.
- **Gap**: No data freshness signal in API responses. An agent cannot determine if the series metadata it receives is current or potentially stale from the last sync.
- **Recommendation**: Add `Last-Modified` or `X-Data-Age` headers to series and episode endpoints based on `LastInfoSync`. This is a lightweight API enhancement.
- **Evidence**: `src/NzbDrone.Core/Tv/Series.cs` (`LastInfoSync`, `Added`), `src/NzbDrone.Core/Tv/Episode.cs` (`AirDateUtc`)

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: `CleanseLogMessage` redacts secrets (API keys, passwords, tokens, webhook URLs, home directory paths). Applied across all log targets. Partial IP masking for non-local addresses in auth logs. Not PII-comprehensive — viewing habits, media paths, email addresses not systematically redacted.
- **Gap**: Agent-initiated logs may expose viewing habits and file paths.
- **Recommendation**: Extend `CleanseLogMessage` with PII patterns.
- **Evidence**: `src/NzbDrone.Common/Instrumentation/CleanseLogMessage.cs`, `src/NzbDrone.Core/Instrumentation/DatabaseTarget.cs`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality scores or completeness metrics. External metadata may have gaps. HealthChecks flag configuration issues, not data quality.
- **Gap**: No data quality signal for agent decision-making.
- **Recommendation**: Consider exposing data completeness indicators.
- **Evidence**: `src/NzbDrone.Core/HealthCheck/`, `src/NzbDrone.Core/History/`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: Versioned APIs at `/api/v3/` and `/api/v5/`. Auto-generated OpenAPI specs with CI workflow for updates. Deprecation headers on deprecated endpoints. No breaking change detection in CI.
- **Gap**: No automated breaking change detection for agent tool bindings.
- **Recommendation**: Add OpenAPI diff tooling to CI.
- **Evidence**: `src/Sonarr.Http/VersionedApiControllerAttribute.cs`, `.github/workflows/api_docs.yml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Field names are human-readable and semantically clear (e.g., `title`, `seasonNumber`, `episodeNumber`, `airDate`). No legacy abbreviations.
- **Gap**: N/A
- **Recommendation**: Maintain current conventions.
- **Evidence**: `src/NzbDrone.Core/Tv/Series.cs`, `src/NzbDrone.Core/Tv/Episode.cs`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal data catalog. OpenAPI specs serve as the closest equivalent. Database migrations document schema evolution.
- **Gap**: No semantic metadata layer for automated discovery.
- **Recommendation**: OpenAPI specs are sufficient. Consider adding model-level Swagger descriptions.
- **Evidence**: `src/Sonarr.Api.V3/openapi.json`, `src/Sonarr.Api.V5/openapi.json`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: NLog-based logging with request sequence IDs. No distributed tracing (no OpenTelemetry, no X-Ray). MiniProfiler for debug builds. CLEF layout available but not default.
- **Gap**: No trace ID propagation. No structured JSON logging by default.
- **Recommendation**: Add OpenTelemetry integration. Enable CLEF structured logging.
- **Evidence**: `src/Sonarr.Http/Middleware/LoggingMiddleware.cs`, `src/NzbDrone.Core/Instrumentation/DatabaseTarget.cs`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: Sentry for error tracking. Discord for build notifications. HealthCheck system for operational health. No alerting thresholds on API performance.
- **Gap**: No automated alerting for API degradation.
- **Recommendation**: Configure Sentry alerting rules. Add health endpoint with latency metrics.
- **Evidence**: `src/NzbDrone.Core/Instrumentation/ReconfigureSentry.cs`, `src/NzbDrone.Core/HealthCheck/`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics published as structured data. History system records events textually. HealthChecks cover operational health only.
- **Gap**: No quantitative business metrics for measuring agent interaction outcomes.
- **Recommendation**: Expose key metrics via API endpoint or OpenTelemetry.
- **Evidence**: `src/NzbDrone.Core/HealthCheck/`, `src/NzbDrone.Core/History/`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK-QUALITY
- **Finding**: No IaC. Self-hosted application distributed as platform-specific binaries. Legacy Dockerfile for build only. Configuration via XML config file.
- **Gap**: No version-controlled, peer-reviewed infrastructure definition.
- **Recommendation**: Create reference Docker Compose or Helm chart for agent-ready deployment topology.
- **Evidence**: `distribution/docker-build/Dockerfile`, `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive CI/CD via GitHub Actions. Multi-platform builds, unit tests, integration tests, PostgreSQL tests, automated deployment. Auto-generated OpenAPI specs. No API contract tests (no Pact, no OpenAPI diff).
- **Gap**: No breaking change detection for agent tool bindings.
- **Recommendation**: Add OpenAPI diff step to CI. Consider Pact tests for agent endpoints.
- **Evidence**: `.github/workflows/build_v5.yml`, `.github/workflows/api_docs.yml`, `src/NzbDrone.Integration.Test/ApiTests/`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: Versioned releases via GitHub. Built-in update mechanism. No automated rollback. Manual version revert possible. Database backups before updates.
- **Gap**: Rollback is manual and may involve database compatibility issues.
- **Recommendation**: Document rollback procedure. Consider reversible migrations.
- **Evidence**: `.github/workflows/deploy.yml`, `src/NzbDrone.Update/`, `src/NzbDrone.Core/Backup/`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: Integration tests covering 15+ API endpoint categories. Unit tests for core logic. Multi-platform and multi-database CI testing. Happy-path focused — no agent-specific consumption pattern tests.
- **Gap**: No error format validation or pagination edge case tests.
- **Recommendation**: Add agent-specific API contract tests.
- **Evidence**: `src/NzbDrone.Integration.Test/ApiTests/`, `.github/workflows/build_v5.yml`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: RISK-QUALITY
- **Finding**: SQLite databases stored unencrypted. PostgreSQL encryption not configured at Sonarr level. Database contains sensitive credentials.
- **Gap**: No application-level encryption at rest.
- **Recommendation**: Document full-disk encryption as deployment requirement. Consider SQLCipher for high-security deployments.
- **Evidence**: `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs`, `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `src/Sonarr.Http/Authentication/ApiKeyAuthenticationHandler.cs` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q7 |
| `src/Sonarr.Http/Authentication/AuthenticationBuilderExtensions.cs` | AUTH-Q1 |
| `src/Sonarr.Http/Authentication/AuthenticationService.cs` | AUTH-Q6 |
| `src/Sonarr.Http/Authentication/UiAuthorizationHandler.cs` | AUTH-Q3 |
| `src/Sonarr.Http/ErrorManagement/ErrorModel.cs` | API-Q3 |
| `src/Sonarr.Http/ErrorManagement/SonarrErrorPipeline.cs` | API-Q3 |
| `src/Sonarr.Http/REST/RestController.cs` | API-Q1, API-Q3, API-Q5 |
| `src/Sonarr.Http/REST/RestControllerWithSignalR.cs` | API-Q7 |
| `src/Sonarr.Http/PagingResource.cs` | DATA-Q3 |
| `src/Sonarr.Http/Middleware/LoggingMiddleware.cs` | AUTH-Q6, OBS-Q1 |
| `src/Sonarr.Http/VersionedApiControllerAttribute.cs` | DISC-Q1 |
| `src/NzbDrone.Host/Startup.cs` | API-Q1, API-Q2, API-Q5, API-Q8, AUTH-Q2, STATE-Q5 |
| `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` | AUTH-Q1, AUTH-Q5, AUTH-Q7, DATA-Q1, DATA-Q2, ENG-Q1, ENG-Q5 |
| `src/NzbDrone.Core/Datastore/BasicRepository.cs` | STATE-Q1, STATE-Q2, STATE-Q3, STATE-Q4, STATE-Q6, DATA-Q3 |
| `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` | DATA-Q2, ENG-Q5 |
| `src/NzbDrone.Core/Instrumentation/DatabaseTarget.cs` | AUTH-Q6, DATA-Q6, OBS-Q1 |
| `src/NzbDrone.Core/Instrumentation/ReconfigureLogging.cs` | AUTH-Q6 |
| `src/NzbDrone.Core/Instrumentation/ReconfigureSentry.cs` | OBS-Q2, OBS-Q3 |
| `src/NzbDrone.Common/Http/HttpClient.cs` | STATE-Q4, STATE-Q5, API-Q8 |
| `src/NzbDrone.Common/Instrumentation/CleanseLogMessage.cs` | DATA-Q1, DATA-Q6 |
| `src/NzbDrone.Common/Instrumentation/CleansingFileTarget.cs` | DATA-Q6 |
| `src/NzbDrone.Common/Instrumentation/CleansingClefLogLayout.cs` | OBS-Q1 |
| `src/NzbDrone.Core/Tv/Series.cs` | DATA-Q5, DISC-Q2 |
| `src/NzbDrone.Core/Tv/Episode.cs` | DATA-Q5, DISC-Q2 |
| `src/NzbDrone.Core/HealthCheck/` | OBS-Q2, OBS-Q3, DATA-Q7 |
| `src/NzbDrone.Core/History/` | OBS-Q3, DATA-Q7 |
| `src/NzbDrone.Core/Backup/` | ENG-Q3 |
| `src/NzbDrone.Core/MetadataSource/` | DATA-Q4 |
| `src/NzbDrone.Core/Tv/RefreshSeriesService.cs` | DATA-Q4 |
| `src/NzbDrone.Update/` | ENG-Q3 |
| `src/NzbDrone.SignalR/` | API-Q7 |
| `src/Sonarr.Api.V3/Series/SeriesController.cs` | API-Q1, API-Q4, AUTH-Q3, STATE-Q2, HITL-Q1 |
| `src/Sonarr.Api.V3/Commands/CommandController.cs` | API-Q4, API-Q6, STATE-Q1 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `src/Sonarr.Api.V3/openapi.json` | API-Q2, DISC-Q1, DISC-Q2, DISC-Q3 |
| `src/Sonarr.Api.V5/openapi.json` | API-Q2, DISC-Q1, DISC-Q3 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/build_v5.yml` | ENG-Q2, ENG-Q4, HITL-Q3, OBS-Q2 |
| `.github/workflows/deploy.yml` | ENG-Q3 |
| `.github/workflows/api_docs.yml` | API-Q2, DISC-Q1, ENG-Q2 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `distribution/docker-build/Dockerfile` | ENG-Q1 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `global.json` | (Discovery — .NET SDK 10.0.201) |
| `package.json` | (Discovery — frontend dependencies) |
| `src/Directory.Build.props` | (Discovery — build configuration, Sentry integration) |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `SECURITY.md` | (Discovery — security policy) |

### Test Files
| File | Questions Referenced |
|------|---------------------|
| `src/NzbDrone.Integration.Test/ApiTests/` | ENG-Q2, ENG-Q4, HITL-Q3 |
| `docker/tests/` | HITL-Q3 |
