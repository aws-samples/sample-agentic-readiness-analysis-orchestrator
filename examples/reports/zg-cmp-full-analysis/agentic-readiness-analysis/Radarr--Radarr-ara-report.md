# Agentic Readiness Analysis Report

**Target**: Radarr (https://github.com/Radarr/Radarr)
**Date**: 2026-04-29
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**Repository Type**: monorepo
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: csharp, media, desktop
**Context**: Movie collection manager (*arr suite).

**Archetype Justification**: Radarr has persistent state via SQLite/PostgreSQL databases with CRUD operations on movies, collections, download clients, and indexers. It manages entity lifecycles (add, update, delete movies) with user-specific configurations, mapping directly to the stateful-crud archetype.

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 2 | **RISK-SAFETY**: 8 | **RISK-QUALITY**: 18 | **INFOs**: 14

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 2 |
| RISK-SAFETY | 8 |
| RISK-QUALITY | 18 |
| INFO | 14 |
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
- **Finding**: Radarr supports API key authentication via a single shared key passed as `X-Api-Key` header or `apikey` query parameter (`ApiKeyAuthenticationHandler.cs`). However, the API key is a single global secret — all consumers share the same key. The authenticated identity is a generic `ClaimsIdentity` with a single claim `("ApiKey", "true")` — no agent identity, no consumer ID, no principal name. Audit logs cannot distinguish which agent or consumer performed an action.
- **Gap**: No machine identity authentication with per-principal attribution. A single shared API key provides no way to identify which agent made a call, making forensics and audit impossible.
- **Remediation**:
  - **Immediate**: Implement support for multiple API keys, each associated with a named principal (e.g., `agent-movie-scanner`, `automation-client-1`). Include the principal name in the `ClaimsIdentity` so it appears in request logs.
  - **Target State**: Each agent consumer has a unique API key with a named identity. Audit logs include the authenticated principal for every request.
  - **Estimated Effort**: Medium
  - **Dependencies**: AUTH-Q6 (audit logging) — attribution is meaningless without immutable logs.
- **Evidence**: `src/Radarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: Radarr stores user credentials (`User.cs` with `Username`, `Password`, `Salt` fields), API keys (in XML config files), download client credentials, indexer API keys, and notification service tokens (Discord webhooks, Telegram bot tokens, Plex tokens). None of this sensitive data is classified or tagged at the field level. There are no field-level access controls — any authenticated consumer with the single API key has full read access to all data including credentials stored in download client and indexer configurations. The `CleanseLogMessage.cs` scrubs secrets from logs, indicating awareness of sensitive data, but no formal classification system exists.
- **Gap**: No sensitive data classification at the field level. No controls preventing an agent from retrieving stored credentials, API keys, or tokens through the API. An agent with read access could expose indexer API keys, download client passwords, and notification tokens.
- **Remediation**:
  - **Immediate**: Audit all API responses that return provider configurations (download clients, indexers, notifications) and redact credential fields from GET responses. Implement a `[SensitiveField]` attribute for data models.
  - **Target State**: All sensitive fields are classified, tagged, and redacted from API responses. Agent-accessible endpoints never return raw credentials.
  - **Estimated Effort**: Medium
  - **Dependencies**: AUTH-Q2 (scoped permissions) — classification enables permission-based access control for sensitive data.
- **Evidence**: `src/NzbDrone.Core/Authentication/User.cs`, `src/NzbDrone.Common/Instrumentation/CleanseLogMessage.cs`, `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Radarr uses a single global API key that grants full access to all endpoints. There is no role-based access control, no resource-based scoping, and no distinction between read and write access. The `FallbackPolicy` in `Startup.cs` requires authentication but applies no further authorization.
- **Gap**: No scoped permissions. Any authenticated consumer has full administrative access to the entire API surface including destructive operations.
- **Compensating Controls**:
  - Deploy a reverse proxy (nginx, Caddy) that restricts the agent's requests to GET methods and specific URL paths.
  - Use a separate Radarr instance for agent access with restricted filesystem permissions.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement role-based API key support — at minimum distinguish "read-only" and "admin" roles.
- **Evidence**: `src/Radarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/NzbDrone.Host/Startup.cs`

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization exists. The API key grants identical access to all HTTP methods (GET, POST, PUT, DELETE) across all controllers. There is no middleware or policy that distinguishes read from write operations at the authorization level.
- **Gap**: No ability to allow an agent to read records but not delete them. All actions are permitted equally.
- **Compensating Controls**:
  - Restrict agent access at the reverse proxy level to specific HTTP methods and paths.
  - Wrap agent tool definitions to only expose read-only endpoints.
- **Remediation Timeline**: 60–90 days (can be combined with AUTH-Q2 remediation)
- **Recommendation**: Introduce authorization policies per controller action — annotate controllers with required permission levels.
- **Evidence**: `src/Radarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/NzbDrone.Host/Startup.cs`, `src/Radarr.Api.V3/Movies/MovieController.cs`

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Radarr has an `Auth` logger in `AuthenticationService.cs` that logs authentication events with IP addresses. `LoggingMiddleware.cs` logs all HTTP requests with sequence ID, method, path, status code, and duration. However: (1) logs are stored in local NLog files and optionally SQLite/PostgreSQL — neither is immutable or tamper-evident; (2) the authenticated principal is not included in request logs; (3) no CloudTrail equivalent, no object-lock, no write-once storage.
- **Gap**: Audit logs exist but are not immutable, not tamper-evident, and do not record the authenticated principal per request.
- **Compensating Controls**:
  - Forward logs to an external, append-only log aggregator (Loki, Elasticsearch with write-only policies).
  - Enable syslog forwarding (already supported: `SyslogServer` config) to a remote syslog server.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add authenticated principal to request log format. Configure log forwarding to immutable storage.
- **Evidence**: `src/Radarr.Http/Authentication/AuthenticationService.cs`, `src/Radarr.Http/Middleware/LoggingMiddleware.cs`

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Radarr supports only a single global API key. There is no mechanism to suspend or revoke an individual agent's access without changing the API key for all consumers. `ResetApiKeyCommand` regenerates the key but affects all integrations simultaneously.
- **Gap**: Cannot isolate or revoke a single agent's access without disrupting all API consumers.
- **Compensating Controls**:
  - Use a reverse proxy with per-consumer API key management.
  - Implement IP-based allowlisting for agent access.
- **Remediation Timeline**: 60–90 days (aligned with AUTH-Q1 multi-key support)
- **Recommendation**: Implement multi-key support with per-key enable/disable capability.
- **Evidence**: `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Radarr has no API-level rate limiting or throttling. No API Gateway, no rate limiting middleware, no WAF. The application runs as a self-hosted Kestrel server with no request throttling. The outbound HTTP client handles upstream 429 responses, but the inbound API surface has no protection.
- **Gap**: No rate limiting on the API layer. A runaway agent loop could overwhelm the application at machine speed.
- **Compensating Controls**:
  - Deploy a reverse proxy with rate limiting rules in front of Radarr.
  - Configure agent-side rate limiting (e.g., max 10 requests/second).
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add ASP.NET Core rate limiting middleware (`Microsoft.AspNetCore.RateLimiting`) or deploy behind a rate-limiting reverse proxy.
- **Evidence**: `src/NzbDrone.Host/Startup.cs`, `src/NzbDrone.Common/Http/TooManyRequestsException.cs`

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Radarr calls multiple external services (indexers, download clients, TMDb, notification services). Polly is used for database retry only. No circuit breaker pattern on outbound HTTP calls. `TooManyRequestsException` handler provides partial resilience for indexers.
- **Gap**: No circuit breakers on external HTTP calls. Failing external dependencies could cascade and degrade API responsiveness.
- **Compensating Controls**:
  - Configure HTTP client timeouts to prevent indefinite hangs.
  - Monitor external service health independently.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add Polly circuit breaker policies to outbound HTTP clients. Configure timeouts on all external calls.
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs`, `src/NzbDrone.Common/Http/HttpClient.cs`

#### DATA-Q2: Data Residency and Sovereignty ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Self-hosted application with local data storage. No data residency controls to prevent agent transmission of data to external LLM providers. Movie metadata is non-regulated but credentials and API keys are stored locally.
- **Gap**: No data classification to indicate which fields are safe for external transmission.
- **Compensating Controls**:
  - Document data sensitivity levels for agent developers.
  - Configure agent to exclude credential-containing endpoints from LLM context.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Classify data fields by sensitivity. Document safe-for-LLM-transmission vs. restricted fields.
- **Evidence**: `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs`

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Comprehensive log scrubbing via `CleanseLogMessage.cs` (25+ regex rules). However, API error responses leak exception stack traces via `ErrorModel.Description` which may contain file paths, connection strings, or internal details.
- **Gap**: API error responses may expose sensitive information through stack traces.
- **Compensating Controls**:
  - Configure agent to not forward error response `Description` fields to LLM context.
  - Filter error responses at the reverse proxy level.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Remove or redact `Description` from production error responses. Return stack traces only in debug mode.
- **Evidence**: `src/NzbDrone.Common/Instrumentation/CleanseLogMessage.cs`, `src/Radarr.Http/ErrorManagement/ErrorModel.cs`

### RISK-QUALITY — Address as Capacity Allows

#### AUTH-Q4: Identity Propagation and Delegation — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No identity propagation. Single API key, no JWT, no OAuth2, no on-behalf-of flows. The application does not distinguish between callers or propagate caller identity to downstream services. For a self-hosted desktop application, this is less critical, but in shared or multi-agent deployments, all agent actions are attributed to the single Radarr instance with no way to trace which agent initiated a request chain.
- **Gap**: No identity propagation through service calls. Cannot distinguish between an agent acting under its own identity vs. on behalf of a user.
- **Compensating Controls**:
  - Use a reverse proxy that injects caller identity headers before forwarding to Radarr.
  - Implement agent-side logging of all requests made to Radarr with agent identity context.
- **Remediation Timeline**: 60–90 days (aligned with AUTH-Q1 multi-key support)
- **Recommendation**: For multi-user deployments, add user context to API key authentication. Implement JWT or token-based identity propagation.
- **Evidence**: `src/Radarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`

#### AUTH-Q5: Credential Management — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: API key stored in XML config file on local filesystem (`config.xml`). User passwords hashed with PBKDF2 with per-user salts. `CleanseLogMessage.cs` scrubs secrets from logs using comprehensive regex patterns. No external secrets management — no Secrets Manager, no Vault, no KMS. No credential rotation mechanism. The API key persists indefinitely unless manually regenerated via `ResetApiKeyCommand`.
- **Gap**: Credentials stored in plaintext XML config file with no external secrets management and no rotation capability. A prompt injection attack or agent bug could potentially read the config file path and expose the API key.
- **Compensating Controls**:
  - Restrict filesystem permissions on `config.xml` to the Radarr service account only.
  - For containerized deployments, inject credentials via environment variables or mounted secrets.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Support environment variable injection for credentials in all deployment modes. Implement API key rotation with configurable expiry.
- **Evidence**: `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`, `src/NzbDrone.Core/Authentication/User.cs`, `src/NzbDrone.Common/Instrumentation/CleanseLogMessage.cs`

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: An OpenAPI 3.0.4 specification exists at `src/Radarr.Api.V3/openapi.json` (302 KB, 12,843 lines), auto-generated from Swashbuckle/Swagger annotations. The CI includes an `Api_Docs` job that regenerates the spec and creates a PR. The spec is comprehensive and current.
- **Gap**: The spec is only served at runtime in debug mode (`if (BuildInfo.IsDebug)`). Production instances do not expose it.
- **Compensating Controls**:
  - Use the repository-hosted `openapi.json` for agent tool generation.
  - Enable Swagger endpoint in production behind API key authentication.
- **Remediation Timeline**: 7–14 days
- **Recommendation**: Consider serving the OpenAPI spec in production behind authentication or document the repository location as canonical.
- **Evidence**: `src/Radarr.Api.V3/openapi.json`, `src/NzbDrone.Host/Startup.cs`

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Radarr returns structured JSON errors via `ErrorModel` with `Message`, `Description`, and `Content` fields. `RadarrErrorPipeline.cs` maps exceptions to HTTP status codes (400, 404, 409, 500). Validation errors return FluentValidation error lists. However, there is no `retryable` boolean, no error code field, and no machine-parseable error category.
- **Gap**: Error responses lack a `retryable` flag and error code — agents must infer retry behavior from HTTP status codes alone.
- **Compensating Controls**:
  - Implement agent-side error classification based on HTTP status codes.
  - Wrap agent tool error handling to classify Radarr error patterns.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add an `errorCode` field and a `retryable` boolean to the `ErrorModel` class.
- **Evidence**: `src/Radarr.Http/ErrorManagement/ErrorModel.cs`, `src/Radarr.Http/ErrorManagement/RadarrErrorPipeline.cs`

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: API is versioned at `/api/v3/`. OpenAPI spec versioned as "3.0.0". Database has 242 versioned migrations. However, no breaking change detection in CI — no OpenAPI diff tool, no consumer-driven contract tests.
- **Gap**: API versioning exists but no automated breaking change detection. Agent tool schemas could break silently.
- **Compensating Controls**:
  - Monitor `openapi.json` diff in PRs manually.
  - Pin agent tool definitions to a specific API version.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add an OpenAPI diff tool (e.g., `oasdiff`) to CI that fails on backward-incompatible changes.
- **Evidence**: `src/Radarr.Api.V3/openapi.json`, `azure-pipelines.yml`, `src/Radarr.Http/VersionedApiControllerAttribute.cs`

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: NLog logging with `LoggingMiddleware` assigns sequential request IDs and tracks duration. Sentry for error reporting. However: (1) no structured JSON logs by default; (2) no distributed tracing (no OpenTelemetry, no X-Ray); (3) request ID is a local incrementing integer, not a globally unique correlation ID.
- **Gap**: No distributed tracing. No globally unique correlation IDs. Logs are not structured JSON by default.
- **Compensating Controls**:
  - Enable NLog JSON layout for structured output.
  - Add a correlation ID middleware generating UUIDs per request.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenTelemetry instrumentation. Replace sequential request ID with UUID. Configure NLog JSON layout.
- **Evidence**: `src/Radarr.Http/Middleware/LoggingMiddleware.cs`, `src/NzbDrone.Core/Instrumentation/ReconfigureSentry.cs`

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Sentry for error reporting. Internal health check system. No alerting thresholds on API error rates or latency — no CloudWatch alarms, no PagerDuty, no SLO-based alerting.
- **Gap**: No alerting on API error rates, latency, or availability.
- **Compensating Controls**:
  - Configure Sentry alert rules for error rate thresholds.
  - Deploy an external uptime monitor.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Configure Sentry alert rules. Consider Prometheus metrics with Grafana alerting.
- **Evidence**: `src/NzbDrone.Core/Instrumentation/ReconfigureSentry.cs`, `azure-pipelines.yml`

#### ENG-Q1: Infrastructure Governance — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Radarr is a self-hosted application distributed as platform-specific binaries. No IaC (no Terraform, CloudFormation, CDK, Helm). `distribution/` contains only Windows/macOS installer configs. Infrastructure configuration is manual.
- **Gap**: No IaC. No peer review of infrastructure changes, no drift detection.
- **Compensating Controls**:
  - Create IaC (Docker Compose, Helm) for standardized agent integration deployments.
  - Document required configuration for agent-ready deployments.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Publish an official Docker image with Helm chart or Docker Compose for standardized deployments.
- **Evidence**: `distribution/` (Windows/macOS installers only), absence of IaC files

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive CI/CD via Azure Pipelines and GitHub Actions. Multi-platform builds, unit tests (SQLite and Postgres), integration tests, automation tests, SonarCloud analysis, Sentry source maps, and OpenAPI spec regeneration. However, no API contract testing (no Pact, no OpenAPI diff).
- **Gap**: No automated API contract or breaking change detection in CI.
- **Compensating Controls**:
  - Manually review `openapi.json` changes.
  - Add OpenAPI diff step to pipeline.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add `oasdiff` or `spectral` to CI for automated breaking change detection.
- **Evidence**: `azure-pipelines.yml`, `.github/workflows/ci.yml`

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Built-in update mechanism (`NzbDrone.Update/`). No blue/green, no canary, no automated rollback. Application is self-hosted and updated in-place. Database migrations are forward-only (FluentMigrator with no down migrations).
- **Gap**: No automated rollback capability. Rolling back requires manual intervention and possible database restoration.
- **Compensating Controls**:
  - Maintain database backups before updates (built-in backup system in `NzbDrone.Core/Backup/`).
  - Pin Radarr version for agent deployments and test updates before applying.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement database migration rollback. For containerized deployments, use tagged images with rollback.
- **Evidence**: `src/NzbDrone.Update/`, `src/NzbDrone.Core/Datastore/Migration/`, `src/NzbDrone.Core/Backup/`

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Integration tests in `src/NzbDrone.Integration.Test/ApiTests/` cover core endpoints (MovieFixture, MovieFileFixture, HistoryFixture, CommandFixture, etc.). Unit tests in `src/NzbDrone.Core.Test/`. SonarCloud integrated. Tests focus on functional correctness — no contract tests validating schema shapes or error format consistency.
- **Gap**: API tests exist but do not cover contract validation or agent-specific consumption patterns.
- **Compensating Controls**:
  - Existing integration tests provide reasonable stability confidence.
  - Add snapshot testing for API response shapes.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add API contract snapshot tests validating response schemas against the OpenAPI spec.
- **Evidence**: `src/NzbDrone.Integration.Test/ApiTests/`, `azure-pipelines.yml`

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No sandbox or staging environment provided. CI uses Docker containers for testing (Postgres, Alpine musl) but these are ephemeral. No published Docker Compose for local testing, no seed data scripts.
- **Gap**: No sandbox or staging environment for testing agent behavior against realistic data.
- **Compensating Controls**:
  - Create a local Docker Compose setup with test instance and seed data.
  - Use a dedicated Radarr instance with non-production data for agent testing.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Publish Docker Compose configuration with seed data for agent development and testing.
- **Evidence**: `azure-pipelines.yml`, absence of `docker-compose.yml`, absence of seed data scripts

#### API-Q6: Asynchronous Operation Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Radarr has a Command system for long-running operations with queue-based processing. The API exposes `/api/v3/command` for submitting and querying command status. However, no standard async API pattern (RFC 7240, Location header) and no webhook callbacks.
- **Gap**: Custom async pattern, not standards-based.
- **Compensating Controls**:
  - Document the Command polling pattern for agent integration.
  - Implement agent-side polling logic for command completion.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document the Command API pattern. Add `Retry-After` headers to pending status responses.
- **Evidence**: `src/Radarr.Api.V3/Commands/`

#### STATE-Q2: Queryable Current State — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: All controllers expose GET endpoints for resource state. However, the main movie collection endpoint returns unbounded results. No general-purpose query filtering.
- **Gap**: Some endpoints return unbounded results. Limited query filtering.
- **Compensating Controls**:
  - Use endpoint-specific filters (e.g., `tmdbId` parameter).
  - Implement agent-side result set management.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add pagination to collection endpoints. Add query parameter filtering.
- **Evidence**: `src/Radarr.Api.V3/Movies/MovieController.cs`

#### DATA-Q3: Selective Query Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: `PagingResource` provides pagination for some endpoints. Primary movie endpoint returns all movies without pagination. Filtering limited to endpoint-specific parameters.
- **Gap**: Primary collection endpoint lacks pagination. Unbounded responses for large libraries.
- **Compensating Controls**:
  - Use `tmdbId` filter for single-movie queries.
  - Implement agent-side chunking for large collections.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add pagination to `/api/v3/movie`. Add general query filtering.
- **Evidence**: `src/Radarr.Http/PagingResource.cs`, `src/Radarr.Api.V3/Movies/MovieController.cs`

#### DATA-Q4: System of Record Designations — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Radarr is de facto system of record for movie collection management. TMDb is upstream metadata authority. No formal documentation of these designations.
- **Gap**: No system-of-record documentation. No conflict resolution across *arr suite apps.
- **Compensating Controls**:
  - Document Radarr as authoritative for collection state, TMDb for metadata.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Formalize system-of-record documentation.
- **Evidence**: `src/NzbDrone.Core/Movies/Movie.cs`

#### DATA-Q5: Temporal Metadata and Freshness — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: `Added` and `LastSearchTime` timestamps exist. No `updated_at` on records. No freshness headers. Agents cannot determine metadata freshness from TMDb.
- **Gap**: No `updated_at` timestamps. No data freshness signaling.
- **Compensating Controls**:
  - Use `Added` and `LastSearchTime` as approximate freshness indicators.
  - Trigger metadata refresh before critical agent queries.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `updated_at` to models. Include `Last-Modified` headers.
- **Evidence**: `src/NzbDrone.Core/Movies/Movie.cs`

#### ENG-Q5: Encryption at Rest — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: SQLite databases stored as plain files. No application-level encryption. PostgreSQL encryption depends on server configuration. Host OS filesystem encryption is outside application control.
- **Gap**: No application-level encryption at rest.
- **Compensating Controls**:
  - Enable host-level filesystem encryption (BitLocker, LUKS, FileVault).
  - For PostgreSQL, enable TDE.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document host-level encryption requirement. Consider SQLCipher for SQLite.
- **Evidence**: `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs`

## INFOs — Architecture and Design Inputs

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Write endpoints do not implement idempotency keys. POST creates a new resource on each call. PUT updates are naturally idempotent by ID. DELETE operations are naturally idempotent. No idempotency middleware exists.
- **Implication**: If agent scope expands to write-enabled, idempotency keys must be added to POST endpoints to prevent duplicate resource creation from retries.
- **Recommendation**: Plan idempotency key support for POST endpoints before enabling write operations.
- **Evidence**: `src/Radarr.Api.V3/Movies/MovieController.cs`

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: All API responses are JSON, serialized via `System.Text.Json` with custom settings (`STJson`). Content type is `application/json`. The OpenAPI spec documents all response schemas.
- **Implication**: JSON responses are ideal for agent consumption. No conversion layer needed.
- **Recommendation**: No action required.
- **Evidence**: `src/NzbDrone.Host/Startup.cs`, `src/Radarr.Api.V3/Movies/MovieController.cs`

### API-Q7: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: Radarr emits real-time events via SignalR WebSocket hub at `/signalr/messages`. `RestControllerWithSignalR` broadcasts `ResourceChangeMessage` events for create, update, and delete actions. `MovieController` handles MovieUpdated, MovieEdited, MoviesDeleted, MovieRenamed, and MediaCoversUpdated events.
- **Implication**: SignalR events enable reactive agent patterns without polling. This is a strength for agentic integration.
- **Recommendation**: Document SignalR event schema for agent developers. Consider REST-based webhook alternative.
- **Evidence**: `src/NzbDrone.SignalR/MessageHub.cs`, `src/Radarr.Http/REST/RestControllerWithSignalR.cs`

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limits documented. No rate limit headers returned. Outbound HTTP client handles 429 responses from upstream services, but inbound API does not implement or document rate limits.
- **Implication**: Agents have no visibility into acceptable request rates and cannot self-throttle.
- **Recommendation**: When rate limiting is implemented (STATE-Q5), include `X-RateLimit-Remaining` and `Retry-After` headers.
- **Evidence**: `src/NzbDrone.Host/Startup.cs`, `src/NzbDrone.Common/Http/TooManyRequestsException.cs`

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Database transactions for multi-record operations (`InsertMany` uses `BeginTransaction` with `IsolationLevel.ReadCommitted`). Polly retry for SQLite busy errors with exponential backoff. No saga patterns, no explicit undo endpoints, no compensating transactions for multi-step workflows.
- **Implication**: If scope expands to write-enabled, absence of compensation/rollback becomes a BLOCKER.
- **Recommendation**: Plan compensation logic for multi-step workflows before expanding to write-enabled scope.
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs`

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: SQLite with WAL mode for concurrent read access. Polly retry for `SQLiteErrorCode.Busy` with exponential backoff. Database constraints enforce uniqueness. No optimistic locking (no version fields, no ETags). Concurrent writes serialized by SQLite write lock.
- **Implication**: Read-only agents unaffected. For write-enabled scope, implement ETag-based optimistic locking.
- **Recommendation**: No immediate action. For write scope, add optimistic locking.
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs`, `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs`

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits. No per-agent operation limits. Read operations bounded by pagination.
- **Implication**: If scope expands to write-enabled, implement per-agent transaction limits.
- **Recommendation**: Plan configurable per-agent limits before enabling write operations.
- **Evidence**: `src/Radarr.Api.V3/Movies/MovieController.cs`, `src/Radarr.Http/PagingResource.cs`

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Status-based state management for movies (TBA, Announced, InCinemas, Released) and `Monitored` flag. Downloads go through queue with pending/processing states. No explicit draft/pending state for CRUD operations.
- **Implication**: For write-enabled scope, draft states would allow agents to propose additions for human review.
- **Recommendation**: No immediate action. Consider "pending review" status for write-enabled scope.
- **Evidence**: `src/NzbDrone.Core/Movies/Movie.cs`

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable approval gates. Operations execute immediately upon API call. No two-step confirmation, no operation-level flags.
- **Implication**: For write-enabled scope, implement approval gates for destructive operations.
- **Recommendation**: No immediate action.
- **Evidence**: `src/Radarr.Api.V3/Movies/MovieController.cs`

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No formal data quality scoring or completeness metrics. Radarr relies on TMDb as upstream metadata source. No data profiling, no null rate monitoring, no freshness SLAs.
- **Implication**: Agents may encounter incomplete metadata records. Tool descriptions should note metadata completeness varies.
- **Recommendation**: Consider adding metadata completeness indicators to API responses.
- **Evidence**: `src/NzbDrone.Core/Movies/Movie.cs`

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Field names are human-readable and semantic: `title`, `year`, `tmdbId`, `imdbId`, `monitored`, `qualityProfileId`, `minimumAvailability`, `sizeOnDisk`, `hasFile`. CamelCase consistently used. No legacy abbreviations.
- **Implication**: Agent LLM reasoning benefits from clear field names. This is a strength.
- **Recommendation**: No action required.
- **Evidence**: `src/Radarr.Api.V3/openapi.json`, `src/NzbDrone.Core/Movies/Movie.cs`

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No formal data catalog. OpenAPI spec serves as de facto metadata layer. Database schemas defined through C# models and FluentMigrator migrations. No Glue Data Catalog, no DataHub.
- **Implication**: Agent developers must reference OpenAPI spec and source code for data semantics.
- **Recommendation**: Consider publishing a data dictionary alongside the OpenAPI spec.
- **Evidence**: `src/Radarr.Api.V3/openapi.json`, `src/NzbDrone.Core/Datastore/Migration/`

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No custom business outcome metrics published. No `put_metric_data` for business events, no custom dashboards tracking movie acquisition rates, download success rates, or quality upgrade rates. The internal health check system monitors operational health but not business outcomes.
- **Implication**: When agents consume the system, business metrics become the signal for whether agent interactions produce good outcomes. Without them, agent effectiveness is unmeasured.
- **Recommendation**: Consider adding metrics for movie acquisition success rate, download completion rate, and quality upgrade rate.
- **Evidence**: `src/NzbDrone.Core/HealthCheck/`

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: Radarr exposes a fully documented REST API at `/api/v3/` with controllers for movies, collections, download clients, indexers, history, queue, commands, and system configuration. The API is defined in `Radarr.Api.V3` with ASP.NET Core controllers extending `RestController<T>` and `RestControllerWithSignalR<T, M>`. No direct database access or file-based exchange patterns required for integration. An OpenAPI 3.0.4 specification is maintained at `src/Radarr.Api.V3/openapi.json`.
- **Gap**: None — the API surface is well-documented and comprehensive. The documented REST interface is the integration surface for agent tools.
- **Recommendation**: No action required. The REST API is the integration surface for agent tools.
- **Evidence**: `src/Radarr.Api.V3/` (all controllers), `src/Radarr.Api.V3/openapi.json`, `src/NzbDrone.Host/Startup.cs`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: OpenAPI 3.0.4 specification at `src/Radarr.Api.V3/openapi.json` (302 KB). Auto-generated from Swashbuckle annotations. CI includes `Api_Docs` job that regenerates and creates PRs. Spec only served in debug mode at runtime.
- **Gap**: Production instances do not serve the spec at runtime.
- **Recommendation**: Serve OpenAPI spec in production behind authentication or document repo location.
- **Evidence**: `src/Radarr.Api.V3/openapi.json`, `src/NzbDrone.Host/Startup.cs`

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: Structured JSON errors via `ErrorModel` with `Message`, `Description`, `Content`. Exception-to-status-code mapping in `RadarrErrorPipeline.cs`. No `retryable` boolean or error code field.
- **Gap**: No machine-parseable error code or retryable indicator.
- **Recommendation**: Add `errorCode` and `retryable` fields to `ErrorModel`.
- **Evidence**: `src/Radarr.Http/ErrorManagement/ErrorModel.cs`, `src/Radarr.Http/ErrorManagement/RadarrErrorPipeline.cs`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No idempotency keys on write endpoints. POST creates new resources without idempotency protection. PUT and DELETE are naturally idempotent.
- **Gap**: POST endpoints lack idempotency keys.
- **Recommendation**: Plan idempotency key support before enabling write scope.
- **Evidence**: `src/Radarr.Api.V3/Movies/MovieController.cs`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: JSON responses via `System.Text.Json`. Content type `application/json`. All schemas documented in OpenAPI spec.
- **Gap**: None.
- **Recommendation**: No action required.
- **Evidence**: `src/NzbDrone.Host/Startup.cs`

#### API-Q6: Asynchronous Operation Support
- **Severity**: RISK-QUALITY
- **Finding**: Radarr has a Command system (`NzbDrone.Core/Messaging/Commands/`) for long-running operations (movie search, download, rename, refresh metadata). Commands are queued and processed asynchronously via `ManageCommandQueue`. The API exposes `/api/v3/command` for submitting commands and querying status. However, there is no standard async pattern (no polling endpoint with job ID in Location header, no webhook callback on completion). The Command endpoint returns the command ID and status can be polled via GET, but this is a custom pattern rather than a standards-based async API pattern.
- **Gap**: Long-running operations use a custom Command queue pattern. No standard async API pattern (RFC 7240, Location header with job URL). No webhook callback on completion.
- **Recommendation**: Document the Command polling pattern for agent developers. Consider adding a `Retry-After` header to pending command status responses.
- **Evidence**: `src/Radarr.Api.V3/Commands/`, `src/NzbDrone.Core/Messaging/Commands/`

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: SignalR WebSocket hub at `/signalr/messages` broadcasts real-time events for model create/update/delete. Comprehensive event coverage across controllers.
- **Gap**: None — strong event emission capability.
- **Recommendation**: Document SignalR event schema for agent developers.
- **Evidence**: `src/NzbDrone.SignalR/MessageHub.cs`, `src/Radarr.Http/REST/RestControllerWithSignalR.cs`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limits documented or implemented. No rate limit headers in responses.
- **Gap**: No rate limit documentation or headers.
- **Recommendation**: Implement rate limit headers when rate limiting is added.
- **Evidence**: `src/NzbDrone.Host/Startup.cs`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: Single shared API key via `X-Api-Key` header or `apikey` query parameter. No per-principal attribution. Generic `ClaimsIdentity` with only `("ApiKey", "true")` claim.
- **Gap**: No machine identity with per-principal attribution.
- **Recommendation**: Implement multiple named API keys.
- **Evidence**: `src/Radarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: Single API key grants full access to all endpoints. No RBAC, no resource scoping, no read/write distinction.
- **Gap**: No scoped permissions.
- **Recommendation**: Implement role-based API key support.
- **Evidence**: `src/Radarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/NzbDrone.Host/Startup.cs`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization. API key grants identical access to all HTTP methods across all controllers.
- **Gap**: No ability to restrict actions per consumer.
- **Recommendation**: Introduce authorization policies per controller action.
- **Evidence**: `src/Radarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/Radarr.Api.V3/Movies/MovieController.cs`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: RISK-QUALITY
- **Finding**: No identity propagation. Single API key, no JWT, no OAuth2, no on-behalf-of flows. Self-hosted single-user application model. The application does not distinguish between callers or propagate caller identity to downstream services.
- **Gap**: No identity propagation through service calls. Cannot distinguish between an agent acting under its own identity vs. on behalf of a user.
- **Recommendation**: For multi-user deployments, add user context to API key authentication. Implement JWT or token-based identity propagation.
- **Evidence**: `src/Radarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`

#### AUTH-Q5: Credential Management
- **Severity**: RISK-QUALITY
- **Finding**: API key stored in XML config file on local filesystem (`config.xml`). Passwords hashed with PBKDF2 + salt. `CleanseLogMessage.cs` scrubs secrets from logs. No external secrets manager — no Secrets Manager, no Vault, no KMS. No credential rotation mechanism.
- **Gap**: Credentials stored in plaintext XML config file with no external secrets management and no rotation capability.
- **Recommendation**: Support environment variable injection for credentials in all deployment modes. Implement API key rotation with configurable expiry.
- **Evidence**: `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`, `src/NzbDrone.Common/Instrumentation/CleanseLogMessage.cs`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Auth logger and LoggingMiddleware exist. Logs stored locally in NLog files and SQLite/PostgreSQL. Not immutable, not tamper-evident. No principal in request logs.
- **Gap**: Logs not immutable. No principal attribution in request logs.
- **Recommendation**: Add principal to logs. Forward to immutable storage.
- **Evidence**: `src/Radarr.Http/Authentication/AuthenticationService.cs`, `src/Radarr.Http/Middleware/LoggingMiddleware.cs`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: Single global API key. No per-consumer revocation. `ResetApiKeyCommand` affects all consumers.
- **Gap**: Cannot suspend individual agent identities.
- **Recommendation**: Implement multi-key support with per-key disable.
- **Evidence**: `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Database transactions for multi-record operations. Polly retry for SQLite busy errors. No saga patterns, no undo endpoints.
- **Gap**: No compensation for multi-step operations.
- **Recommendation**: Plan compensation logic before expanding to write scope.
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs`

#### STATE-Q2: Queryable Current State
- **Severity**: RISK-QUALITY
- **Finding**: All controllers expose GET endpoints for querying resource state. `MovieController.AllMovie()` returns all movies. Individual resources are queryable by ID via `GetResourceByIdWithErrorHandler()`. Queue, history, calendar, and system status all have GET endpoints. However, some endpoints (like `AllMovie`) return the entire collection without filtering, which can be costly for large libraries. The API lacks a general-purpose query language for complex state queries.
- **Gap**: State is queryable but some endpoints return unbounded result sets. No general-purpose query filtering beyond endpoint-specific parameters.
- **Recommendation**: Add query parameter filtering to collection endpoints. Consider GraphQL or OData-style filtering.
- **Evidence**: `src/Radarr.Api.V3/Movies/MovieController.cs`, `src/Radarr.Http/REST/RestController.cs`

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: SQLite WAL mode. Polly retry for busy errors. Database constraints. No optimistic locking.
- **Gap**: No optimistic locking for write operations.
- **Recommendation**: For write scope, add ETag-based optimistic locking.
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: Radarr calls multiple external services: indexers (Newznab, Torznab), download clients (SABnzbd, NZBGet, qBittorrent, Transmission), metadata providers (TMDb), and notification services (Discord, Telegram, Plex). Polly is used for database retry logic (SQLite busy errors with exponential backoff in `BasicRepository.cs`), but no circuit breaker pattern is applied to outbound HTTP calls. The `TooManyRequestsException` handler records indexer failures and enforces backoff periods, which is a partial resilience pattern. However, there is no formal circuit breaker, no bulkhead isolation, and no timeout configuration on HTTP client calls to external services.
- **Gap**: No circuit breakers on external HTTP calls. A failing external dependency (e.g., TMDb timeout) could cascade and degrade the entire application's responsiveness for agent requests.
- **Recommendation**: Add Polly circuit breaker policies to the HTTP client for external service calls. Configure timeouts on all outbound HTTP requests.
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs` (Polly retry), `src/NzbDrone.Common/Http/HttpClient.cs`, `src/NzbDrone.Common/Http/TooManyRequestsException.cs`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No API-level rate limiting. Self-hosted Kestrel with no throttling. Outbound 429 handling exists but inbound has no protection.
- **Gap**: No rate limiting on inbound API.
- **Recommendation**: Add ASP.NET Core rate limiting middleware or reverse proxy.
- **Evidence**: `src/NzbDrone.Host/Startup.cs`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits. No per-agent operation limits.
- **Gap**: No transaction limits.
- **Recommendation**: Plan per-agent limits before enabling write scope.
- **Evidence**: `src/Radarr.Api.V3/Movies/MovieController.cs`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path. This service is P2 priority.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Status-based movie management (TBA, Announced, InCinemas, Released). Download queue with pending states. No draft state for CRUD operations.
- **Gap**: No draft/pending state for resource creation.
- **Recommendation**: Consider "pending review" status for write-enabled scope.
- **Evidence**: `src/NzbDrone.Core/Movies/Movie.cs`

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No approval gates. Operations execute immediately.
- **Gap**: No configurable approval requirements.
- **Recommendation**: Implement for write-enabled scope.
- **Evidence**: `src/Radarr.Api.V3/Movies/MovieController.cs`

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: No sandbox/staging environment. CI uses ephemeral containers. No Docker Compose for local testing, no seed data.
- **Gap**: No reusable staging environment for agent testing.
- **Recommendation**: Publish Docker Compose with seed data.
- **Evidence**: `azure-pipelines.yml`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: User credentials, API keys, download client passwords, indexer tokens, notification tokens stored without field-level classification or access controls. Any API consumer can access all data.
- **Gap**: No sensitive data classification. No field-level access controls.
- **Recommendation**: Classify and redact sensitive fields from API responses.
- **Evidence**: `src/NzbDrone.Core/Authentication/User.cs`, `src/NzbDrone.Common/Instrumentation/CleanseLogMessage.cs`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Radarr is a self-hosted application. Data resides on the user's own infrastructure (local SQLite or user-managed PostgreSQL). The application stores movie metadata (non-regulated, sourced from TMDb), user credentials (local-only), and configuration data. There are no cloud data residency concerns inherent to the application. However, if an agent transmits movie collection data or user configuration to an LLM endpoint, the data residency characteristics depend entirely on where the agent sends data — the application has no controls to prevent data transmission to external services.
- **Gap**: No data residency controls within the application. While the data is locally stored, there are no mechanisms to restrict what data an agent can transmit to external LLM providers. No data classification tags to indicate which fields can safely leave the local environment.
- **Recommendation**: Classify data fields by sensitivity level. Document which data types are safe for LLM transmission (movie metadata) vs. restricted (credentials, API keys).
- **Evidence**: `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs`, `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK-QUALITY
- **Finding**: Radarr provides `PagingResource` with `Page`, `PageSize`, `SortKey`, `SortDirection` and `TotalRecords` for paginated endpoints (history, blocklist, wanted/missing). However, the primary movie endpoint (`/api/v3/movie`) returns all movies in a single unbounded response with no pagination support — a collection of 10,000+ movies would be returned in one response. Other collection endpoints (queue, history) support pagination via `PagingSpec`. Filtering is limited to endpoint-specific query parameters (e.g., `tmdbId` for movies).
- **Gap**: Primary movie collection endpoint lacks pagination. Large collections produce unbounded responses that would exceed LLM context windows.
- **Recommendation**: Add pagination support to the `/api/v3/movie` endpoint. Add general query filtering parameters.
- **Evidence**: `src/Radarr.Http/PagingResource.cs`, `src/Radarr.Api.V3/Movies/MovieController.cs`

#### DATA-Q4: System of Record Designations
- **Severity**: RISK-QUALITY
- **Finding**: Radarr is the system of record for the user's movie collection management — it tracks which movies are monitored, their quality profiles, root folder paths, and download status. Movie metadata is sourced from TMDb (read-only upstream) with local overrides. There are no formal system-of-record designations or documentation. If an agent queries multiple *arr suite applications (Radarr, Sonarr, Lidarr), there is no master data management process for shared entities like download clients or indexer configurations.
- **Gap**: No formal system-of-record documentation. No conflict resolution for shared configuration across *arr suite applications.
- **Recommendation**: Document Radarr as the system of record for movie collection management. Document TMDb as the upstream metadata authority.
- **Evidence**: `src/NzbDrone.Core/Movies/Movie.cs`, `src/NzbDrone.Core/MetadataSource/`

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK-QUALITY
- **Finding**: Movie entities include `Added` (DateTime when the movie was added to Radarr), and the MovieMetadata includes `InCinemas`, `PhysicalRelease`, `DigitalRelease` dates. However, there is no `updated_at` timestamp on movie records, no `last_refreshed` timestamp for metadata from TMDb, and no `Cache-Control` or `X-Data-Age` headers in API responses. The `LastSearchTime` field tracks when the last search was performed for a movie. There is no mechanism for the API to signal whether returned data is current, stale, or cached.
- **Gap**: No `updated_at` timestamps on records. No data freshness headers in API responses. Agents cannot determine when metadata was last refreshed from TMDb.
- **Recommendation**: Add `updated_at` timestamps to data models. Include `Last-Modified` and `Cache-Control` headers in API responses.
- **Evidence**: `src/NzbDrone.Core/Movies/Movie.cs` (`Added`, `LastSearchTime` fields)

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: `CleanseLogMessage.cs` implements comprehensive secret scrubbing with 25+ regex rules covering: API keys, passwords, tokens, tracker announce keys, Discord webhooks, Telegram bot tokens, Plex tokens, NzbGet/Sabnzbd credentials, uTorrent/Deluge credentials, and BroadcastheNet tokens. Remote IP addresses are partially masked (e.g., `10.*.*.1`). User home directory paths are scrubbed from logs. However, this scrubbing operates on log messages only — PII in API error responses (`ErrorModel.Description` includes full exception stack traces) may contain sensitive data like file paths or connection strings.
- **Gap**: Log scrubbing is thorough for secrets, but API error responses may leak sensitive information through exception stack traces in the `Description` field. The `ErrorModel` sends full exception `ToString()` output to API clients.
- **Recommendation**: Redact or remove the `Description` field from production API error responses. Return stack traces only in debug mode.
- **Evidence**: `src/NzbDrone.Common/Instrumentation/CleanseLogMessage.cs`, `src/Radarr.Http/ErrorManagement/RadarrErrorPipeline.cs`, `src/Radarr.Http/ErrorManagement/ErrorModel.cs`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No formal data quality metrics. TMDb as upstream source. No data profiling or completeness monitoring.
- **Gap**: No data quality indicators.
- **Recommendation**: Add metadata completeness indicators.
- **Evidence**: `src/NzbDrone.Core/Movies/Movie.cs`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: API versioned at `/api/v3/`. OpenAPI spec versioned. 242 database migrations. No automated breaking change detection in CI.
- **Gap**: No automated breaking change detection.
- **Recommendation**: Add OpenAPI diff tool to CI.
- **Evidence**: `src/Radarr.Api.V3/openapi.json`, `azure-pipelines.yml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Human-readable, semantic field names. CamelCase consistent. No legacy abbreviations.
- **Gap**: None.
- **Recommendation**: No action required.
- **Evidence**: `src/Radarr.Api.V3/openapi.json`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal data catalog. OpenAPI spec as de facto metadata. Schemas in C# models and migrations.
- **Gap**: No dedicated data dictionary.
- **Recommendation**: Publish data dictionary alongside OpenAPI spec.
- **Evidence**: `src/Radarr.Api.V3/openapi.json`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: NLog with sequential request IDs. Sentry integration. No distributed tracing, no structured JSON logs by default, no globally unique correlation IDs.
- **Gap**: No distributed tracing. No structured JSON logs.
- **Recommendation**: Add OpenTelemetry. Configure JSON log layout.
- **Evidence**: `src/Radarr.Http/Middleware/LoggingMiddleware.cs`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: Sentry for error reporting. Internal health checks. No alerting thresholds on API metrics.
- **Gap**: No API alerting.
- **Recommendation**: Configure Sentry alerts. Add Prometheus metrics.
- **Evidence**: `src/NzbDrone.Core/Instrumentation/ReconfigureSentry.cs`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics. Health check system for operational health only.
- **Gap**: No business outcome metrics.
- **Recommendation**: Add movie acquisition and download success metrics.
- **Evidence**: `src/NzbDrone.Core/HealthCheck/`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance
- **Severity**: RISK-QUALITY
- **Finding**: Self-hosted application. No IaC. Distribution as platform binaries. Manual infrastructure configuration.
- **Gap**: No IaC, no peer review, no drift detection.
- **Recommendation**: Publish official Docker/Helm configuration.
- **Evidence**: `distribution/`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: Azure Pipelines + GitHub Actions. Multi-platform builds, extensive testing, SonarCloud, OpenAPI regeneration. No API contract testing.
- **Gap**: No automated API contract testing.
- **Recommendation**: Add `oasdiff` to CI.
- **Evidence**: `azure-pipelines.yml`, `.github/workflows/ci.yml`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: In-place updates. Forward-only migrations. Built-in backup system. No automated rollback.
- **Gap**: No automated rollback.
- **Recommendation**: Implement migration rollback. Use tagged container images.
- **Evidence**: `src/NzbDrone.Update/`, `src/NzbDrone.Core/Datastore/Migration/`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: Integration tests for core API endpoints. Unit tests. SonarCloud. No contract tests or schema validation.
- **Gap**: No contract validation tests.
- **Recommendation**: Add contract snapshot tests.
- **Evidence**: `src/NzbDrone.Integration.Test/ApiTests/`

#### ENG-Q5: Encryption at Rest
- **Severity**: RISK-QUALITY
- **Finding**: Radarr uses SQLite (file-based, no built-in encryption at rest) and optionally PostgreSQL. SQLite databases are stored as plain files on the local filesystem. No KMS, no encryption configuration in the codebase. The SQLite connection string in `ConnectionStringFactory.cs` does not specify encryption. PostgreSQL encryption at rest depends on the PostgreSQL server configuration (managed by the user, not by Radarr). For self-hosted applications, encryption at rest depends on the host OS filesystem encryption (BitLocker, LUKS, FileVault), which is outside Radarr's control.
- **Gap**: No application-level encryption at rest. SQLite databases containing API keys, credentials, and user data are stored as plain files. Encryption depends entirely on host OS configuration.
- **Recommendation**: Document the recommendation for host-level filesystem encryption. For SQLite, consider SQLCipher for application-level encryption. For PostgreSQL, document the requirement for TDE or filesystem encryption.
- **Evidence**: `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs`, `src/NzbDrone.Core/Datastore/DbFactory.cs`

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `src/Radarr.Http/Authentication/ApiKeyAuthenticationHandler.cs` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4 |
| `src/Radarr.Http/Authentication/AuthenticationService.cs` | AUTH-Q6 |
| `src/Radarr.Http/ErrorManagement/ErrorModel.cs` | API-Q3 |
| `src/Radarr.Http/ErrorManagement/RadarrErrorPipeline.cs` | API-Q3 |
| `src/Radarr.Http/REST/RestController.cs` | API-Q1 |
| `src/Radarr.Http/REST/RestControllerWithSignalR.cs` | API-Q7 |
| `src/Radarr.Http/Middleware/LoggingMiddleware.cs` | AUTH-Q6, OBS-Q1 |
| `src/Radarr.Http/PagingResource.cs` | STATE-Q6, DATA-Q3 |
| `src/Radarr.Http/VersionedApiControllerAttribute.cs` | DISC-Q1 |
| `src/Radarr.Api.V3/Movies/MovieController.cs` | API-Q1, API-Q4, AUTH-Q3, STATE-Q6, HITL-Q1, HITL-Q2 |
| `src/NzbDrone.Core/Datastore/BasicRepository.cs` | STATE-Q1, STATE-Q3 |
| `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` | STATE-Q3, ENG-Q5 |
| `src/NzbDrone.Core/Datastore/DbFactory.cs` | ENG-Q5 |
| `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` | AUTH-Q1, AUTH-Q5, AUTH-Q7, DATA-Q1 |
| `src/NzbDrone.Core/Authentication/User.cs` | AUTH-Q5, DATA-Q1 |
| `src/NzbDrone.Core/Movies/Movie.cs` | HITL-Q1, DATA-Q7, DISC-Q2 |
| `src/NzbDrone.Core/Instrumentation/ReconfigureSentry.cs` | OBS-Q1, OBS-Q2 |
| `src/NzbDrone.Common/Instrumentation/CleanseLogMessage.cs` | AUTH-Q5, DATA-Q1, DATA-Q6 |
| `src/NzbDrone.Common/Http/TooManyRequestsException.cs` | STATE-Q5, API-Q8 |
| `src/NzbDrone.SignalR/MessageHub.cs` | API-Q7 |
| `src/NzbDrone.Host/Startup.cs` | API-Q1, API-Q2, API-Q5, API-Q8, AUTH-Q2, STATE-Q5 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `src/Radarr.Api.V3/openapi.json` | API-Q1, API-Q2, DISC-Q1, DISC-Q2, DISC-Q3 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `azure-pipelines.yml` | ENG-Q2, ENG-Q3, ENG-Q4, OBS-Q2, DISC-Q1, HITL-Q3 |
| `.github/workflows/ci.yml` | ENG-Q2 |
| `.github/dependabot.yml` | ENG-Q2 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `src/NzbDrone.Core/Radarr.Core.csproj` | STATE-Q4 (Polly reference) |
| `package.json` | API-Q7 (@microsoft/signalr), OBS-Q1 (@sentry/browser) |
| `global.json` | ENG-Q2 (.NET SDK version) |

### Distribution / Deployment
| File | Questions Referenced |
|------|---------------------|
| `distribution/` | ENG-Q1 |
| `src/NzbDrone.Update/` | ENG-Q3 |
| `src/NzbDrone.Core/Backup/` | ENG-Q3 |

### Test Files
| File | Questions Referenced |
|------|---------------------|
| `src/NzbDrone.Integration.Test/ApiTests/` | ENG-Q4 |
| `src/NzbDrone.Core.Test/` | ENG-Q4 |

### Database Migrations
| File | Questions Referenced |
|------|---------------------|
| `src/NzbDrone.Core/Datastore/Migration/` (242 files) | DISC-Q1, ENG-Q3 |

### Health Checks
| File | Questions Referenced |
|------|---------------------|
| `src/NzbDrone.Core/HealthCheck/` | OBS-Q2, OBS-Q3 |
