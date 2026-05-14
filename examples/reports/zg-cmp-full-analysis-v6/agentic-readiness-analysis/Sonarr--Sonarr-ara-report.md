# Agentic Readiness Analysis Report

**Target**: Sonarr--Sonarr
**Date**: 2025-05-08
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**Repository Type**: application
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: csharp, media, desktop
**Context**: TV-series PVR for usenet and BitTorrent users (*arr suite).

**Archetype Justification**: The application owns persistent state in SQLite/PostgreSQL databases, exposes CRUD operations on business entities (Series, Episodes, EpisodeFiles, DownloadClients), manages entity lifecycles with status fields, and handles user-specific configuration data.

**Surface flags**:
- has_persistent_data_store: true
- has_http_rpc_surface: true
- has_auth_surface: true
- has_write_operations: true
- has_logging_of_user_data: true

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 1 | **RISK-SAFETY**: 8 | **RISK-QUALITY**: 13 | **INFOs**: 16

Resolve all blockers before any agent deployment — including pilots.

**Classification Rationale**: This repo has 1 High finding (BLOCKER: AUTH-Q1 — no machine identity authentication), 21 Medium findings (8 safety-impact RISK-SAFETY + 13 RISK-QUALITY), and 16 Low findings (INFO). The matched rule is "1–2 High → Remediation Required." The V6 unified tier aligns with the V5 readiness profile: 1 BLOCKER with any RISK-SAFETY count → Remediation Required.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 1 |
| RISK-SAFETY | 8 |
| RISK-QUALITY | 13 |
| INFO | 16 |
| N/A | 0 |
| Not Evaluated (extended) | 4 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 15
**Extended Questions Not Triggered**: 4
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: stateful-crud (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: The application uses a single shared API key for all programmatic access. There is no support for service accounts, client credentials OAuth 2.0, mTLS, or any mechanism that attributes requests to distinct machine identities. The API key is a single `Guid.NewGuid()` value stored in plaintext in `config.xml`, shared across all consumers. The `ApiKeyAuthenticationHandler` validates requests against this single key — no principal attribution is possible.
- **Gap**: No machine identity authentication. Cannot distinguish which agent or service made a call. Cannot attribute API calls to individual agent identities in audit logs.
- **Remediation**:
  - **Immediate**: Implement support for multiple API keys with distinct identity labels, or add OAuth 2.0 client credentials flow via an API gateway in front of Sonarr.
  - **Target State**: Each agent identity has its own credential (API key or OAuth client) with principal attribution recorded in logs.
  - **Estimated Effort**: Medium
  - **Dependencies**: AUTH-Q6 (audit logging) depends on resolving this — you cannot log "which agent" without distinct identities.
- **Evidence**: `src/Sonarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`

---

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The authorization model is binary — a valid API key grants full access to all endpoints and all operations. There is no role-based access, no scoped permissions, and no ability to restrict an agent to read-only access on specific resources. The `FallbackPolicy` in `Startup.cs` requires authentication but does not differentiate access levels.
- **Gap**: No scoped permissions. An agent with the API key can read, write, and delete any resource.
- **Compensating Controls**:
  - Deploy an API gateway in front of Sonarr that restricts agent traffic to specific HTTP methods and paths (e.g., allow only GET requests).
  - Use network-level controls to limit agent access to a read-only reverse proxy endpoint.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement RBAC or introduce scoped API key permissions that differentiate read vs write access per resource type.
- **Evidence**: `src/Sonarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/NzbDrone.Host/Startup.cs`

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization exists. Any authenticated principal can perform any operation. Controllers use `[AllowAnonymous]` only for `/ping` and `/login`.
- **Gap**: Cannot restrict an agent to "read records but not delete them" within the same resource type.
- **Compensating Controls**:
  - API gateway with method-level routing rules (allow GET, block DELETE/PUT/POST for agent traffic).
  - Application-level middleware that inspects a custom header identifying agent requests and restricts HTTP methods.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add action-level authorization attributes or implement an ABAC/fine-grained RBAC model.
- **Evidence**: `src/NzbDrone.Host/Startup.cs`, `src/Sonarr.Http/REST/RestController.cs`

#### AUTH-Q6: Immutable Audit Logging — RISK-SAFETY ⚡

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The application logs HTTP requests (method, URL, status code, duration, source IP) but does NOT log the authenticated principal identity. No immutable audit trail — logs are written to local files and a local database table with no tamper protection.
- **Gap**: No authenticated principal attribution in logs. No immutable log storage.
- **Compensating Controls**:
  - Forward logs to an append-only external system (e.g., CloudWatch Logs with retention lock).
  - Add middleware to inject authenticated principal identity into structured log entries.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Enhance `LoggingMiddleware` to log the authenticated principal for every request. Configure immutable log storage.
- **Evidence**: `src/Sonarr.Http/Middleware/LoggingMiddleware.cs`, `src/NzbDrone.Core/Instrumentation/DatabaseTarget.cs`

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The application supports only a single API key. There is no mechanism to suspend an individual agent identity without affecting all API consumers. The only option is `ResetApiKeyCommand` which invalidates ALL clients.
- **Gap**: Cannot isolate and suspend a misbehaving agent without disrupting all consumers.
- **Compensating Controls**:
  - Use an API gateway with per-client API keys that can be individually revoked.
  - Implement IP-based allowlisting.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement multi-key support with per-key lifecycle management.
- **Evidence**: `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Polly retry only (SQLite busy errors and HTTP 5xx). NO circuit breaker patterns. External dependency calls (indexers, download clients, metadata providers) have no circuit breaker protection.
- **Gap**: No circuit breaker pattern. Agent-initiated requests could cascade into system-wide failures.
- **Compensating Controls**:
  - Add Polly `CircuitBreaker` policies on external HTTP client calls.
  - Deploy an API gateway with circuit breaker capabilities.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add Polly circuit breaker policies to all external HTTP client calls.
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs`, `src/NzbDrone.Core/Download/DownloadClientBase.cs`

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: NO inbound API rate limiting. The `RateLimitService` only throttles OUTBOUND requests to external services. The API surface accepts unlimited inbound requests.
- **Gap**: No inbound API-layer rate limiting.
- **Compensating Controls**:
  - Deploy an API gateway or reverse proxy with rate limiting rules.
  - Add ASP.NET Core rate limiting middleware.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add inbound rate limiting middleware or configure rate limits at the gateway layer.
- **Evidence**: `src/NzbDrone.Core/Http/RateLimitService.cs`, `src/NzbDrone.Host/Startup.cs`

#### DATA-Q1: Sensitive Data Classification — RISK-SAFETY ⚡

- **Severity**: RISK-SAFETY
- **Conditional**: Stage A = Yes. agent_scope is "read-only" — B1 resolves to RISK-SAFETY.
- **Finding**: The `HostConfigResource` API endpoint (`GET /api/v3/config/host`) returns the API key in plaintext, hashed password, proxy password, proxy username, and SSL cert password without any `[JsonIgnore]` filtering. No access control differentiation between sensitive and non-sensitive data (B2). No formal classification metadata (B3).
- **Gap**: Sensitive credentials exposed in general API responses. No access differentiation.
- **Compensating Controls**:
  - Add `[JsonIgnore]` to sensitive fields in `HostConfigResource`.
  - Create separate admin-only endpoint for credential access with higher privilege requirements.
- **Remediation Timeline**: 30 days
- **Recommendation**: Add `[JsonIgnore]` to ApiKey, Password, SslCertPassword, ProxyPassword fields. Separate credential endpoints from general config endpoints.
- **Evidence**: `src/Sonarr.Api.V3/Config/HostConfigResource.cs`, `src/Sonarr.Api.V3/Config/HostConfigController.cs`

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: `CleanseLogMessage` scrubs API keys and passwords via regex patterns. However, it does not redact broader PII: IP addresses logged in request middleware, file paths containing usernames, user-submitted content. Sentry captures stack traces with potentially sensitive context.
- **Gap**: Log sanitization focuses on credentials but does not cover broader PII.
- **Compensating Controls**:
  - Extend `CleanseLogMessage` patterns to cover IP addresses and file paths.
  - Configure log forwarding to strip PII before external storage.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Audit all log output for PII leakage. Extend sanitization patterns.
- **Evidence**: `src/NzbDrone.Core/Instrumentation/CleansingExtensions.cs`, `src/Sonarr.Http/Middleware/LoggingMiddleware.cs`

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: OpenAPI 3.0.1 specifications exist for V3 (12,497 lines) and V5 (10,982 lines), auto-generated via Swashbuckle and maintained in CI (`api_docs.yml`).
- **Gap**: No contract testing validates spec accuracy against actual API behavior.
- **Compensating Controls**:
  - Use existing OpenAPI specs directly for agent tool generation.
  - Add OpenAPI diff detection in CI.
- **Remediation Timeline**: 30 days
- **Recommendation**: Add OpenAPI spec diffing to CI to detect breaking changes before merge.
- **Evidence**: `src/Sonarr.Api.V3/openapi.json`, `src/Sonarr.Api.V5/openapi.json`, `.github/workflows/api_docs.yml`

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Centralized error pipeline (`SonarrErrorPipeline`) maps exceptions to HTTP status codes with structured bodies (`message`, `description`, `content`). FluentValidation errors return 400 with field-level arrays. However, no `retryable` boolean or error category field exists.
- **Gap**: Agent cannot programmatically distinguish retriable from terminal errors without parsing messages.
- **Compensating Controls**:
  - Document retriable status codes in agent tool definitions.
  - Add retryable field to error format.
- **Remediation Timeline**: 30 days
- **Recommendation**: Add `retryable` boolean or error category field.
- **Evidence**: `src/Sonarr.Http/ErrorManagement/SonarrErrorPipeline.cs`

#### AUTH-Q5: Credential Management — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Credentials are stored in plaintext in `config.xml` (API key, PostgreSQL password). Environment variable overrides supported. No integration with secrets management systems (Secrets Manager, Vault). The `HostConfigResource` API returns all credentials to authenticated users.
- **Gap**: No secrets management integration. Credentials in plaintext config files.
- **Compensating Controls**:
  - Use environment variables for credential injection in containerized deployments.
  - Integrate with a secrets management system for credential storage and rotation.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Remove sensitive fields from API responses. Integrate with secrets management for credential rotation.
- **Evidence**: `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`, `src/Sonarr.Api.V3/Config/HostConfigResource.cs`

#### DATA-Q3: Selective Query Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Pagination support exists via `PagingResource` (page, pageSize, sortKey, sortDirection) used by log endpoints and import list exclusions. However, most entity list endpoints (series, episodes, episode files) return ALL results without pagination. No maximum page size validation exists — clients can request unbounded result sets.
- **Gap**: Most list endpoints return unbounded results. Agents retrieving full series/episode lists get everything regardless of need.
- **Compensating Controls**:
  - Agent tool definitions can use explicit filtering parameters available on some endpoints.
  - Limit agent queries to specific entity IDs rather than full lists.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add pagination to all list endpoints. Implement maximum page size validation.
- **Evidence**: `src/Sonarr.Http/PagingResource.cs`, `src/Sonarr.Api.V3/Series/SeriesController.cs`

#### DATA-Q4: System of Record Designations — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Sonarr is the system of record for series monitoring state, quality preferences, and download history within its domain. However, it defers to external sources for metadata (TVDB/TMDb for series/episode info) and has no formal master data management process. No documentation designates which data is authoritative vs derived.
- **Gap**: No formal system-of-record designations. No documented data ownership boundaries.
- **Compensating Controls**:
  - Document which entities are owned by Sonarr vs external sources in agent tool descriptions.
  - Treat Sonarr as authoritative for monitoring state and download history; treat metadata as derived.
- **Remediation Timeline**: 30 days
- **Recommendation**: Document data ownership in API documentation or README.
- **Evidence**: `src/NzbDrone.Core/MetadataSource/`, `src/NzbDrone.Core/Tv/`

#### DATA-Q5: Temporal Metadata and Freshness — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Entities include `added` and `lastInfoSync` timestamp fields. Series have `lastSearchTime`. Database records use UTC timestamps. However, there are no `Cache-Control` or freshness headers in API responses. Agents cannot distinguish whether data is current vs cached. No `X-Data-Age` or consistency-level signaling.
- **Gap**: No freshness signaling in API responses. Agents cannot determine if data is current or stale.
- **Compensating Controls**:
  - Use `lastInfoSync` field values to infer freshness client-side.
  - Add Cache-Control headers to API responses.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add Cache-Control or X-Data-Age headers to API responses.
- **Evidence**: `src/NzbDrone.Core/Tv/Series.cs`, `src/Sonarr.Api.V3/Series/SeriesResource.cs`

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: API versioned (V3, V5 paths coexist). OpenAPI specs maintained per version. 233 FluentMigrator database migrations. No breaking change detection in CI (no `oasdiff`, no Pact).
- **Gap**: No automated breaking change detection. Agent tool bindings could break silently.
- **Compensating Controls**:
  - Pin agent tools to specific API version.
  - Add OpenAPI diff tooling to CI.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenAPI spec comparison to CI that fails on breaking changes.
- **Evidence**: `src/Sonarr.Api.V3/openapi.json`, `.github/workflows/api_docs.yml`

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: NLog with CLEF structured JSON available. `LoggingMiddleware` assigns sequential request IDs. No distributed tracing (no OpenTelemetry, no X-Ray, no traceparent propagation). Request IDs are process-local integers that reset on restart.
- **Gap**: No distributed tracing. No globally unique correlation IDs.
- **Compensating Controls**:
  - Add OpenTelemetry SDK with ASP.NET Core instrumentation.
  - Replace sequential IDs with GUID-based correlation IDs.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenTelemetry instrumentation with trace ID propagation.
- **Evidence**: `src/Sonarr.Http/Middleware/LoggingMiddleware.cs`

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Internal health checks (~20+) with notification routing to 25+ channels. No infrastructure-level alerting on API error rates or latency. No CloudWatch alarms, Prometheus rules, or SLO monitoring.
- **Gap**: No error rate or latency alerting on the API surface.
- **Compensating Controls**:
  - Deploy monitoring with alerting on 5xx rate and P99 latency.
  - Use health check webhook notifications as partial signal.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add metrics collection and alerting thresholds.
- **Evidence**: `src/NzbDrone.Core/HealthCheck/`, `src/NzbDrone.Core/Notifications/`

#### ENG-Q1: Infrastructure Governance — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No IaC in repository. Self-hosted application distributed as platform-specific packages.
- **Gap**: No IaC defining how the API surface is exposed for agent consumption.
- **Compensating Controls**:
  - Create IaC for agent-facing deployment when applicable.
  - Use container orchestration with version-controlled manifests.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Define hosting infrastructure as code for agent integration scenarios.
- **Evidence**: No IaC files found. Distribution is via platform-specific packages.

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive CI pipeline (multi-OS unit tests, integration tests, PostgreSQL compatibility) but no API contract tests or breaking change detection.
- **Gap**: No API contract testing in CI.
- **Compensating Controls**:
  - Add OpenAPI diff tooling to CI.
  - Pin agent tools to specific API version with manual review on spec changes.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add contract testing or OpenAPI schema diffing to CI.
- **Evidence**: `.github/workflows/build_v5.yml`, `.github/workflows/api_docs.yml`

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Self-hosted release model. No blue/green, no canary, no automated rollback. Users manually downgrade.
- **Gap**: No automated rollback capability.
- **Compensating Controls**:
  - Use container-based deployment with orchestration rollback.
  - Pin agent deployments to tested versions.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Use container-based deployment with rollback for agent integration.
- **Evidence**: `.github/workflows/deploy.yml`

#### ENG-Q5: Encryption at Rest — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: SQLite database is unencrypted by default. Credentials in plaintext `config.xml`. No KMS integration.
- **Gap**: No encryption at rest for database or configuration.
- **Compensating Controls**:
  - Deploy on infrastructure with volume-level encryption.
  - Use PostgreSQL on encrypted RDS.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Use encrypted volumes at infrastructure layer.
- **Evidence**: `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs`, `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`

---

## INFOs — Architecture and Design Inputs

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No idempotency patterns. No idempotency keys, no deduplication tokens. Write endpoints rely solely on database unique constraints for conflict detection (409 on violation).
- **Implication**: If agent_scope expands to write-enabled, this becomes a BLOCKER.
- **Recommendation**: Implement idempotency keys before enabling write-enabled scope.
- **Evidence**: `src/Sonarr.Http/REST/RestController.cs`

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: All API responses use structured JSON via `System.Text.Json`. Content-Type `application/json`. SignalR uses JSON protocol.
- **Implication**: JSON is well-suited for agent consumption.
- **Recommendation**: No action needed.
- **Evidence**: `src/Sonarr.Api.V3/openapi.json`

### API-Q6: Asynchronous Operation Support

- **Severity**: INFO
- **Finding**: The Command system provides async operation support. Clients POST to `/api/v3/command` to submit operations (RSS sync, series search, rename). Command status is queryable via GET. SignalR broadcasts progress updates. This is a functional async pattern for long-running operations.
- **Implication**: Agents can submit long-running operations and poll for completion. The pattern is usable but not REST-standard (no Location header, no standard polling contract).
- **Recommendation**: Document the command polling pattern in agent tool definitions.
- **Evidence**: `src/Sonarr.Api.V3/Commands/CommandController.cs`, `src/NzbDrone.Core/Messaging/Commands/CommandQueueManager.cs`

### API-Q7: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: SignalR broadcasts model events on state changes (series added/updated/deleted, episodes grabbed/imported). The notification system supports webhooks with configurable triggers (OnGrab, OnDownload, OnSeriesAdd, OnSeriesDelete, OnHealthIssue, OnHealthRestored). This provides event emission for state changes.
- **Implication**: Agents can subscribe to state changes via webhook notifications or SignalR. The webhook system is production-ready for event-driven agent patterns.
- **Recommendation**: No immediate action. Document webhook configuration for agent event subscriptions.
- **Evidence**: `src/NzbDrone.Core/Notifications/Webhook/`, `src/NzbDrone.SignalR/`

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limit headers (`X-RateLimit-Remaining`, `Retry-After`) in responses. No documented limits in OpenAPI spec.
- **Implication**: Agents have no signal for self-throttling.
- **Recommendation**: Include rate limit headers when inbound limiting is implemented.
- **Evidence**: `src/NzbDrone.Core/Http/RateLimitService.cs`

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: INFO
- **Finding**: No identity propagation or delegation. Single-user application with no concept of acting on behalf of another user. The API key identifies "the Sonarr instance" not a specific user or agent.
- **Implication**: Identity propagation is less critical for this self-hosted single-user application.
- **Recommendation**: No immediate action for read-only scope.
- **Evidence**: `src/Sonarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No compensation or rollback patterns. The Command system executes operations as single units. Database operations use individual transactions per repository call but no saga pattern exists.
- **Implication**: If agent_scope expands to write-enabled, this becomes a BLOCKER.
- **Recommendation**: Implement compensation logic before enabling write-enabled scope.
- **Evidence**: `src/NzbDrone.Core/Messaging/Commands/`

### STATE-Q2: Queryable Current State

- **Severity**: INFO
- **Finding**: Rich GET endpoints expose current state for all resources: `GET /api/v3/series` returns all series with status, monitoring state, quality, and statistics. `GET /api/v3/episode` returns episodes with file status. `GET /api/v3/queue` returns current download queue. `GET /api/v3/command` returns command execution status. The API surface fully supports read-before-act patterns.
- **Implication**: Agents can inspect current state before deciding next steps. Well-suited for agentic workflows.
- **Recommendation**: No action needed — current state is fully queryable.
- **Evidence**: `src/Sonarr.Api.V3/Series/SeriesController.cs`, `src/Sonarr.Api.V3/Episodes/EpisodeController.cs`

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits. Bulk operations have no upper bounds.
- **Implication**: If agent_scope expands to write-enabled, an agent error could trigger unbounded operations.
- **Recommendation**: Implement before enabling write-enabled scope.
- **Evidence**: `src/Sonarr.Api.V3/Series/SeriesController.cs`

### DATA-Q2: Data Residency and Sovereignty ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — self-hosted with local data storage.
- **Finding**: Self-hosted application — all data resides on the user's local machine. No cloud-managed data stores, no cross-region replication.
- **Implication**: Data residency is controlled by the deployment operator. Ensure agent architecture doesn't forward local data to non-compliant regions.
- **Recommendation**: Document data flow constraints for agent architecture design.
- **Evidence**: `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs`

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No formal data quality metrics. Health checks detect missing metadata from external providers. Refresh scheduling keeps metadata current.
- **Implication**: Agent decisions requiring metadata completeness must infer quality from field presence.
- **Recommendation**: No immediate action needed.
- **Evidence**: `src/NzbDrone.Core/HealthCheck/`

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Field names are human-readable and semantically meaningful: `SeriesResource.title`, `EpisodeResource.seasonNumber`, `EpisodeFileResource.relativePath`. No legacy abbreviation codes.
- **Implication**: Agent tool definitions can use field names directly. LLM reasoning benefits from clear semantics.
- **Recommendation**: No action needed.
- **Evidence**: `src/Sonarr.Api.V3/Series/SeriesResource.cs`

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No formal data catalog. OpenAPI specs serve as de facto API documentation. Database schema implicitly defined by FluentMigrator migrations.
- **Implication**: Agent tool authors must consult OpenAPI specs for data semantics.
- **Recommendation**: Enrich OpenAPI schema descriptions and examples.
- **Evidence**: `src/Sonarr.Api.V3/openapi.json`

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No custom business outcome metrics published. The application tracks internal statistics (series counts, episode counts, disk usage) but does not emit metrics to external monitoring systems.
- **Implication**: When agents consume this system, business metrics (e.g., successful imports, queue throughput) would be the primary signal for agent effectiveness. Currently no pipeline for this.
- **Recommendation**: Consider adding metrics export for key business events if agent integration proceeds.
- **Evidence**: `src/NzbDrone.Core/Tv/`, `src/NzbDrone.Core/Download/`

### ENG-Q4: API Test Coverage

- **Severity**: INFO
- **Finding**: The application has comprehensive test coverage: 12 test projects covering unit tests, integration tests (with full HTTP client testing against running instances), and automation tests. The integration test suite (`NzbDrone.Integration.Test`) makes real HTTP requests against API endpoints. CI runs tests on 3 operating systems with PostgreSQL compatibility testing.
- **Implication**: Existing test infrastructure provides good coverage of API behavior. Tests validate input handling, output format, and error responses.
- **Recommendation**: Consider adding explicit contract tests that validate OpenAPI spec accuracy.
- **Evidence**: `src/NzbDrone.Integration.Test/`, `.github/workflows/build_v5.yml`

### HITL-Q3: Sandbox/Staging Environment

- **Severity**: INFO
- **Finding**: Docker-based development containers exist (`.devcontainer/`). CI pipeline runs integration tests with full application instances. The self-hosted nature means each installation is its own isolated environment. Docker test configurations exist for validation.
- **Implication**: Creating a sandbox is straightforward — spin up a Docker container with seed data. No separate staging infrastructure needed for a self-hosted app.
- **Recommendation**: Create a Docker Compose-based sandbox with seed data for agent development.
- **Evidence**: `.devcontainer/devcontainer.json`, `docker/tests/`, `.github/workflows/build_v5.yml`

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: PASS
- **Finding**: The application exposes a well-documented REST API with two versioned surfaces (V3 and V5). Controllers organized by resource type with clear routing. OpenAPI specifications document all endpoints.
- **Gap**: None.
- **Recommendation**: N/A.
- **Evidence**: `src/Sonarr.Api.V3/`, `src/Sonarr.Api.V5/`, `src/Sonarr.Api.V3/openapi.json`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: OpenAPI 3.0.1 specs exist, auto-generated via Swashbuckle, maintained in CI.
- **Gap**: No contract testing validates spec accuracy.
- **Recommendation**: Add OpenAPI diff and contract validation to CI.
- **Evidence**: `src/Sonarr.Api.V3/openapi.json`, `src/Sonarr.Api.V5/openapi.json`

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: Centralized error pipeline with structured bodies. No retryable indicator.
- **Gap**: No retryable flag or error category.
- **Recommendation**: Add retryable field.
- **Evidence**: `src/Sonarr.Http/ErrorManagement/SonarrErrorPipeline.cs`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No idempotency patterns. Relies on database constraints.
- **Gap**: No idempotency keys on write endpoints.
- **Recommendation**: Implement before enabling write-enabled scope.
- **Evidence**: `src/Sonarr.Http/REST/RestController.cs`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: All responses structured JSON. Content-Type `application/json`.
- **Gap**: None.
- **Recommendation**: No action needed.
- **Evidence**: `src/Sonarr.Api.V3/openapi.json`

#### API-Q6: Asynchronous Operation Support
- **Severity**: INFO
- **Finding**: Command system provides async operation support. POST to submit, GET to poll status. SignalR broadcasts progress. Functional async pattern exists.
- **Gap**: Not REST-standard (no Location header, no standard polling contract).
- **Recommendation**: Document command polling pattern in agent tool definitions.
- **Evidence**: `src/Sonarr.Api.V3/Commands/CommandController.cs`

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: SignalR broadcasts model events. Webhook notification system supports configurable triggers (OnGrab, OnDownload, OnSeriesAdd, OnSeriesDelete, OnHealthIssue, OnHealthRestored).
- **Gap**: None — event emission exists via webhooks and SignalR.
- **Recommendation**: Document webhook configuration for agent event subscriptions.
- **Evidence**: `src/NzbDrone.Core/Notifications/Webhook/`, `src/NzbDrone.SignalR/`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit headers or documentation in API.
- **Gap**: No programmatic rate limit signaling.
- **Recommendation**: Include rate limit headers when inbound limiting is implemented.
- **Evidence**: `src/NzbDrone.Core/Http/RateLimitService.cs`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: Single shared API key. No principal attribution. No machine identity support.
- **Gap**: Cannot distinguish agent identities.
- **Recommendation**: Implement multi-key or OAuth client credentials.
- **Evidence**: `src/Sonarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: Binary access — valid key grants full access.
- **Gap**: No scoped permissions.
- **Recommendation**: Implement RBAC or scoped keys.
- **Evidence**: `src/Sonarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/NzbDrone.Host/Startup.cs`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization.
- **Gap**: Cannot restrict read vs write per resource type.
- **Recommendation**: Add action-level authorization.
- **Evidence**: `src/NzbDrone.Host/Startup.cs`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: No identity propagation. Single-user self-hosted app.
- **Gap**: No delegation mechanism.
- **Recommendation**: No immediate action for this deployment model.
- **Evidence**: `src/Sonarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`

#### AUTH-Q5: Credential Management
- **Severity**: RISK-QUALITY
- **Finding**: Credentials in plaintext config.xml. Environment variable overrides supported. No secrets management integration.
- **Gap**: No secrets management. Credentials exposed via API.
- **Recommendation**: Integrate secrets management. Remove credentials from API responses.
- **Evidence**: `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`, `src/Sonarr.Api.V3/Config/HostConfigResource.cs`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No principal attribution in logs. No immutable storage.
- **Gap**: Cannot attribute actions to identities.
- **Recommendation**: Add principal attribution. Configure immutable log storage.
- **Evidence**: `src/Sonarr.Http/Middleware/LoggingMiddleware.cs`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: Single API key. Cannot suspend individual identity.
- **Gap**: No per-identity suspension.
- **Recommendation**: Implement multi-key with lifecycle management.
- **Evidence**: `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No compensation or rollback patterns. Fire-and-forget operations.
- **Gap**: No rollback for multi-step operations.
- **Recommendation**: Implement before enabling write-enabled scope.
- **Evidence**: `src/NzbDrone.Core/Messaging/Commands/`

#### STATE-Q2: Queryable Current State
- **Severity**: INFO
- **Finding**: Rich GET endpoints for all resources. Series, episodes, queue, commands all queryable. Fully supports read-before-act patterns.
- **Gap**: None — state is fully queryable.
- **Recommendation**: No action needed.
- **Evidence**: `src/Sonarr.Api.V3/Series/SeriesController.cs`, `src/Sonarr.Api.V3/Episodes/EpisodeController.cs`

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled AND service has persistent state
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: Polly retry only. No circuit breaker.
- **Gap**: No circuit breaker for external dependencies.
- **Recommendation**: Add Polly circuit breaker policies.
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs`, `src/NzbDrone.Core/Download/DownloadClientBase.cs`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No inbound rate limiting. Outbound only.
- **Gap**: No inbound API protection.
- **Recommendation**: Add inbound rate limiting.
- **Evidence**: `src/NzbDrone.Core/Http/RateLimitService.cs`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No transaction limits. No operation caps.
- **Gap**: No blast radius controls.
- **Recommendation**: Implement before enabling write-enabled scope.
- **Evidence**: `src/Sonarr.Api.V3/Series/SeriesController.cs`

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
- **Finding**: Docker-based development containers exist. CI runs full integration tests. Self-hosted nature means each installation is isolated. Docker test configs available.
- **Gap**: No formal sandbox with production-equivalent data shape documented for agent testing.
- **Recommendation**: Create Docker Compose-based sandbox with seed data.
- **Evidence**: `.devcontainer/devcontainer.json`, `docker/tests/`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — B1 resolves to RISK-SAFETY
- **Finding**: HostConfigResource API returns API key, hashed password, proxy credentials, SSL cert password without filtering.
- **Gap**: Sensitive credentials exposed in general API responses.
- **Recommendation**: Add [JsonIgnore] to sensitive fields. Separate credential endpoints.
- **Evidence**: `src/Sonarr.Api.V3/Config/HostConfigResource.cs`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — self-hosted local storage
- **Finding**: Self-hosted. All data local. No cross-region issues.
- **Gap**: None for self-hosted model.
- **Recommendation**: Document data flow constraints for agent architecture.
- **Evidence**: `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK-QUALITY
- **Finding**: Pagination exists on some endpoints (logs, exclusions). Most entity list endpoints return all results without pagination. No max page size validation.
- **Gap**: Most list endpoints return unbounded results.
- **Recommendation**: Add pagination to all list endpoints.
- **Evidence**: `src/Sonarr.Http/PagingResource.cs`, `src/Sonarr.Api.V3/Series/SeriesController.cs`

#### DATA-Q4: System of Record Designations
- **Severity**: RISK-QUALITY
- **Finding**: Sonarr is SoR for monitoring state and download history. Defers to TVDB/TMDb for metadata. No formal documentation of data ownership.
- **Gap**: No documented data ownership boundaries.
- **Recommendation**: Document data ownership in API docs.
- **Evidence**: `src/NzbDrone.Core/MetadataSource/`, `src/NzbDrone.Core/Tv/`

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK-QUALITY
- **Finding**: Entities include timestamps (`added`, `lastInfoSync`). UTC storage. No freshness headers in API responses.
- **Gap**: No freshness signaling in responses.
- **Recommendation**: Add Cache-Control or X-Data-Age headers.
- **Evidence**: `src/NzbDrone.Core/Tv/Series.cs`

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: CleanseLogMessage covers credentials. Does not cover broader PII.
- **Gap**: Incomplete PII redaction.
- **Recommendation**: Extend sanitization patterns.
- **Evidence**: `src/NzbDrone.Core/Instrumentation/CleansingExtensions.cs`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No formal quality metrics. Health checks detect missing metadata.
- **Gap**: No data quality scoring.
- **Recommendation**: No immediate action.
- **Evidence**: `src/NzbDrone.Core/HealthCheck/`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: API versioned. OpenAPI maintained. No breaking change detection.
- **Gap**: No automated breaking change detection.
- **Recommendation**: Add OpenAPI diff to CI.
- **Evidence**: `src/Sonarr.Api.V3/openapi.json`, `.github/workflows/api_docs.yml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Field names are clear and human-readable throughout.
- **Gap**: None.
- **Recommendation**: No action needed.
- **Evidence**: `src/Sonarr.Api.V3/Series/SeriesResource.cs`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal data catalog. OpenAPI specs serve as API documentation.
- **Gap**: No programmatic metadata discovery.
- **Recommendation**: Enrich OpenAPI schema descriptions.
- **Evidence**: `src/Sonarr.Api.V3/openapi.json`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: NLog with CLEF JSON. No distributed tracing. Process-local request IDs.
- **Gap**: No distributed tracing or unique correlation IDs.
- **Recommendation**: Add OpenTelemetry.
- **Evidence**: `src/Sonarr.Http/Middleware/LoggingMiddleware.cs`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: Internal health checks only. No infrastructure alerting.
- **Gap**: No API error rate/latency alerting.
- **Recommendation**: Add metrics and alerting.
- **Evidence**: `src/NzbDrone.Core/HealthCheck/`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No business outcome metrics exported. Internal statistics tracked.
- **Gap**: No external metrics pipeline.
- **Recommendation**: Add metrics export for key business events if agent integration proceeds.
- **Evidence**: `src/NzbDrone.Core/Tv/`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance
- **Severity**: RISK-QUALITY
- **Finding**: No IaC. Self-hosted packages.
- **Gap**: No IaC for agent-facing infrastructure.
- **Recommendation**: Create IaC for agent deployment scenarios.
- **Evidence**: No IaC files found.

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive CI but no contract testing.
- **Gap**: No API contract testing.
- **Recommendation**: Add OpenAPI diff or Pact.
- **Evidence**: `.github/workflows/build_v5.yml`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: No automated rollback. Manual downgrade only.
- **Gap**: No automated rollback.
- **Recommendation**: Use container-based deployment with rollback.
- **Evidence**: `.github/workflows/deploy.yml`

#### ENG-Q4: API Test Coverage
- **Severity**: INFO
- **Finding**: 12 test projects. Integration tests make real HTTP requests against API. CI runs on 3 OSes with PostgreSQL compatibility. Comprehensive test coverage exists.
- **Gap**: Tests are functional but not explicitly contract-oriented (covered by ENG-Q2).
- **Recommendation**: Consider adding explicit OpenAPI contract tests.
- **Evidence**: `src/NzbDrone.Integration.Test/`, `.github/workflows/build_v5.yml`

#### ENG-Q5: Encryption at Rest
- **Severity**: RISK-QUALITY
- **Finding**: SQLite unencrypted. Config in plaintext. No KMS.
- **Gap**: No encryption at rest.
- **Recommendation**: Use encrypted volumes at infrastructure layer.
- **Evidence**: `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs`

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| src/Sonarr.Http/Authentication/ApiKeyAuthenticationHandler.cs | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4 |
| src/Sonarr.Http/REST/RestController.cs | AUTH-Q3, API-Q3, API-Q4 |
| src/Sonarr.Http/ErrorManagement/SonarrErrorPipeline.cs | API-Q3 |
| src/Sonarr.Http/Middleware/LoggingMiddleware.cs | AUTH-Q6, DATA-Q6, OBS-Q1 |
| src/Sonarr.Http/PagingResource.cs | DATA-Q3 |
| src/NzbDrone.Host/Startup.cs | AUTH-Q2, AUTH-Q3, STATE-Q5 |
| src/NzbDrone.Core/Configuration/ConfigFileProvider.cs | AUTH-Q1, AUTH-Q5, AUTH-Q7, ENG-Q5 |
| src/NzbDrone.Core/Datastore/BasicRepository.cs | STATE-Q1, STATE-Q4 |
| src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs | DATA-Q2, ENG-Q5 |
| src/NzbDrone.Core/Download/DownloadClientBase.cs | STATE-Q4 |
| src/NzbDrone.Core/Http/RateLimitService.cs | STATE-Q5, API-Q8 |
| src/NzbDrone.Core/Instrumentation/CleansingExtensions.cs | DATA-Q6 |
| src/NzbDrone.Core/Instrumentation/DatabaseTarget.cs | AUTH-Q6 |
| src/NzbDrone.Core/Messaging/Commands/CommandQueueManager.cs | API-Q6, STATE-Q1 |
| src/NzbDrone.Core/Tv/Series.cs | DATA-Q5, STATE-Q2 |
| src/NzbDrone.Core/HealthCheck/ | OBS-Q2, DATA-Q7 |
| src/NzbDrone.Core/Notifications/Webhook/ | API-Q7 |
| src/NzbDrone.Core/MetadataSource/ | DATA-Q4 |
| src/NzbDrone.SignalR/ | API-Q7 |
| src/Sonarr.Api.V3/Config/HostConfigResource.cs | AUTH-Q5, DATA-Q1 |
| src/Sonarr.Api.V3/Config/HostConfigController.cs | DATA-Q1 |
| src/Sonarr.Api.V3/Series/SeriesResource.cs | DISC-Q2, DATA-Q5 |
| src/Sonarr.Api.V3/Series/SeriesController.cs | STATE-Q2, STATE-Q6, DATA-Q3 |
| src/Sonarr.Api.V3/Episodes/EpisodeController.cs | STATE-Q2 |
| src/Sonarr.Api.V3/Commands/CommandController.cs | API-Q6 |
| src/NzbDrone.Integration.Test/ | ENG-Q4 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| src/Sonarr.Api.V3/openapi.json | API-Q1, API-Q2, API-Q5, API-Q8, DISC-Q1, DISC-Q3 |
| src/Sonarr.Api.V5/openapi.json | API-Q2, DISC-Q1, DISC-Q3 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| .github/workflows/build_v5.yml | ENG-Q2, ENG-Q4, HITL-Q3 |
| .github/workflows/deploy.yml | ENG-Q3 |
| .github/workflows/api_docs.yml | API-Q2, DISC-Q1, ENG-Q2 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| .devcontainer/devcontainer.json | HITL-Q3 |
| docker/tests/ | HITL-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| src/NzbDrone.Core/Sonarr.Core.csproj | STATE-Q4 |
| src/NzbDrone.Host/Sonarr.Host.csproj | AUTH-Q1 |
