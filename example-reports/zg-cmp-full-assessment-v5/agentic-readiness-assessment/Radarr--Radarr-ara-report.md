# Agentic Readiness Assessment Report

**Target**: Radarr (https://github.com/Radarr/Radarr)
**Date**: 2026-04-30
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**TD Version**: 3g1ipe93e5d2wb6n5d4yqaf9
**Repository Type**: monorepo (assessed as single application — see note below)
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: csharp, media, desktop
**Context**: Movie collection manager (*arr suite).

**Archetype Justification**: Radarr owns persistent state (SQLite/PostgreSQL database), exposes full CRUD operations on business entities (movies, profiles, download clients, indexers), and manages entity lifecycle (monitored/unmonitored, download status tracking). While it has orchestrator characteristics (calls TMDb, indexers, download clients), the primary pattern is CRUD management of a movie collection.

> **Note**: The repository is declared as `monorepo`, but examination reveals it is a single application (Radarr) with a backend (.NET 8 C# solution with ~25 projects in `src/`) and a frontend (React/TypeScript in `frontend/`). All 43 questions are assessed against the single Radarr application service.

- **Surface flags**:
  - has_persistent_data_store: true
  - has_http_rpc_surface: true
  - has_auth_surface: true
  - has_write_operations: true
  - has_logging_of_user_data: true

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 2 | **RISK-SAFETY**: 9 | **RISK-QUALITY**: 13 | **INFOs**: 18

> Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 2 |
| RISK-SAFETY | 9 |
| RISK-QUALITY | 13 |
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
- **Finding**: Radarr uses a single shared API key for all API consumers. The key is set via `X-Api-Key` header or `apikey` query parameter (`ApiKeyAuthenticationHandler.cs`). All consumers — human users, third-party tools, and potential agents — share the same key. The authenticated principal is a single claim `("ApiKey", "true")` with no identity differentiation. There is no per-agent principal attribution: audit logs cannot distinguish which agent made a specific API call.
- **Gap**: No machine identity model that distinguishes individual agents. Single API key grants identical access to all consumers. No principal attribution beyond "has valid API key."
- **Remediation**:
  - **Immediate**: Implement support for multiple API keys, each with a unique identifier (e.g., `key_name` or `agent_id`) that is logged with every request. This can be done by extending the `ApiKeyAuthenticationHandler` to support a key registry.
  - **Target State**: Each agent has a unique API key with a named principal. Audit logs include the agent identifier for every API call.
  - **Estimated Effort**: Medium (2–4 weeks of development)
  - **Dependencies**: Interacts with AUTH-Q6 (audit logging) — principal attribution is only useful if the principal is logged.
- **Evidence**: `src/Radarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (single `ApiKey` property), `src/NzbDrone.Host/Startup.cs` (auth configuration)

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: **Stage A**: The system stores sensitive data. Download client configurations include API keys, passwords, and credentials for indexers (Newznab, Torznab, HDBits, PassThePopcorn, etc.) and download clients, stored in the SQLite/PostgreSQL database. User authentication credentials (username/password hashes) are stored for forms-based auth. **Stage B**: No data classification tags exist at the field level. No field-level encryption is applied to stored credentials. Download client and indexer passwords are stored in the database without classification or access control differentiation. While the `ClientSchema` module includes a `PrivacyLevel` enum in `Field.cs` (indicating some awareness of sensitive fields in the UI), this does not constitute data classification with access controls preventing an agent from retrieving credentials via the API.
- **Gap**: Sensitive credentials (download client API keys, indexer passwords) are stored without field-level classification, encryption, or access controls. An agent with the API key can retrieve all download client and indexer configurations including their credentials via `GET /api/v3/downloadclient` and `GET /api/v3/indexer`.
- **Remediation**:
  - **Immediate**: Implement field-level redaction on credential fields in API responses. When a GET request retrieves download client or indexer configurations, mask credential fields (return `"********"` instead of actual passwords/API keys). The `PrivacyLevel` enum already identifies sensitive fields — use it as the classification source.
  - **Target State**: Sensitive fields are classified, redacted in API responses by default, and accessible only through a separate privileged endpoint or with an elevated scope.
  - **Estimated Effort**: Medium (2–3 weeks)
  - **Dependencies**: None
- **Evidence**: `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (credentials stored in config), `src/Radarr.Http/ClientSchema/` (PrivacyLevel enum), `src/Radarr.Api.V3/DownloadClient/`, `src/Radarr.Api.V3/Indexers/`, `src/Radarr.Api.V3/openapi.json`

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The single API key grants unrestricted access to all API endpoints — read and write across all resources (movies, download clients, indexers, system configuration). No role-based access control, no resource-level scoping, no IAM policies. Any valid API key holder has full administrative access.
- **Gap**: No mechanism to grant an agent read-only access to specific resources without inheriting broader write privileges.
- **Compensating Controls**:
  - Deploy a reverse proxy (e.g., nginx, Caddy) in front of Radarr that restricts the agent to GET-only methods on specific endpoints.
  - Use an API gateway layer that enforces read-only access policies per API key.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement a role/scope system where API keys can be assigned specific permissions (e.g., `read:movies`, `write:movies`, `admin`).
- **Evidence**: `src/Radarr.Http/Authentication/ApiKeyAuthenticationHandler.cs` (single key, no scoping), `src/NzbDrone.Host/Startup.cs` (fallback auth policy applies uniformly)

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization exists. The API key authentication grants blanket access to all HTTP methods (GET, POST, PUT, DELETE) on all endpoints. No `canRead`, `canWrite`, `canDelete` permission checks in middleware or controllers. An agent authenticated with the API key can delete movies, modify configurations, and trigger system commands.
- **Gap**: Cannot restrict an agent to read-only actions on a per-resource basis. All authenticated requests have full CRUD access.
- **Compensating Controls**:
  - Use a reverse proxy to enforce method-level restrictions (allow only GET requests for agent traffic).
  - Implement a read-only API key scope as an interim measure.
- **Remediation Timeline**: 60–90 days (can be addressed together with AUTH-Q2)
- **Recommendation**: Add action-level permission checks to the `RestController` base class, enforcing per-method authorization based on the API key's assigned scope.
- **Evidence**: `src/Radarr.Http/REST/RestController.cs` (no permission checks), `src/Radarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`

#### AUTH-Q6: Immutable Audit Logging ⚡

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Authentication events are logged via NLog (`AuthenticationService.cs` logs IP addresses and usernames for login/logout/failure). The `LoggingMiddleware` logs HTTP request method, path, status code, and duration. However, logs are stored as local files with no immutability, no tamper-evidence, and no centralized log aggregation. The `DatabaseTarget` writes logs to a local SQLite `radarr-log` database, but this is not immutable. No CloudTrail equivalent.
- **Gap**: Logs are mutable local files. No immutable audit trail. No tamper-evident storage. Agent actions cannot be forensically verified.
- **Compensating Controls**:
  - Forward NLog output to a centralized, append-only log service (e.g., syslog server with immutable storage). Radarr already supports syslog via `SyslogServer`/`SyslogPort` configuration.
  - Enable the existing syslog integration and point it to an immutable log collector.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure syslog forwarding to an immutable log store. Enhance log entries to include the authenticated principal identifier (requires AUTH-Q1 remediation first).
- **Evidence**: `src/Radarr.Http/Authentication/AuthenticationService.cs`, `src/Radarr.Http/Middleware/LoggingMiddleware.cs`, `src/NzbDrone.Core/Instrumentation/DatabaseTarget.cs`, `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (SyslogServer, SyslogPort properties)

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: With a single shared API key, the only way to revoke an agent's access is to reset the API key via `ResetApiKeyCommand`, which invalidates ALL API consumers simultaneously. There is no mechanism to suspend an individual agent identity without affecting other integrations (e.g., mobile apps, other automation tools, web UI).
- **Gap**: Cannot isolate and revoke a single agent's access. Revoking the API key is an all-or-nothing operation.
- **Compensating Controls**:
  - Deploy a reverse proxy that issues separate tokens to each agent, allowing individual revocation at the proxy layer while using a single upstream Radarr API key.
  - Implement the multi-key support from AUTH-Q1 remediation, which inherently enables per-key revocation.
- **Remediation Timeline**: 60–90 days (addressed by AUTH-Q1 remediation)
- **Recommendation**: Implement multiple API keys with individual revocation capability.
- **Evidence**: `src/NzbDrone.Core/Configuration/ResetApiKeyCommand.cs`, `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (single ApiKey property)

#### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No saga patterns, no explicit rollback endpoints, no compensating transaction logic. `BasicRepository.cs` uses database transactions for `InsertMany` operations (wraps in `IsolationLevel.ReadCommitted`), but there are no application-level compensation mechanisms for multi-step workflows. The Command system (`CommandController.cs`) queues commands but has no rollback or undo capability.
- **Gap**: No compensation logic for multi-step operations. If a future write-enabled agent scope is adopted, partial failures in multi-step workflows would leave the system in an inconsistent state.
- **Compensating Controls**:
  - Keep agent scope read-only (current state) to avoid write-path risks.
  - For any future write operations, implement explicit undo endpoints for critical operations.
- **Remediation Timeline**: 90–180 days (if write-enabled scope is planned)
- **Recommendation**: For current read-only scope, this is acceptable with monitoring. If write-enabled scope is planned, implement compensating actions for movie add/delete and configuration changes.
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs` (InsertMany transaction), `src/Radarr.Api.V3/Commands/CommandController.cs` (no undo/rollback)

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Radarr has a **partial** resilience implementation. The `ProviderStatusServiceBase` implements an escalation backoff pattern that temporarily disables failing providers (indexers, download clients, notifications) after repeated failures — functionally similar to a circuit breaker. `BasicRepository.cs` uses Polly retry with exponential backoff for SQLite busy errors. `HttpIndexerBase.cs` catches `TooManyRequestsException` and `RequestLimitReachedException` with backoff periods. However, there are no formal circuit breaker patterns (no Resilience4j, no Polly `CircuitBreaker` policy), no timeout configurations on outbound HTTP clients, and the backoff mechanism is provider-specific rather than a general resilience pattern.
- **Gap**: No formal circuit breaker on outbound HTTP calls to TMDb, indexers, or download clients. Provider backoff mechanism exists but is not a full circuit breaker (no open/half-open/closed states). Missing timeout configurations on HTTP clients.
- **Compensating Controls**:
  - The existing `ProviderStatusServiceBase` backoff mechanism provides partial protection — failing providers are automatically disabled with escalating backoff periods.
  - Monitor provider status via `/api/v3/health` endpoint which reports disabled providers.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add Polly `CircuitBreaker` policies to the `IHttpClient` used for outbound calls. Configure explicit timeout policies on all HTTP client instances.
- **Evidence**: `src/NzbDrone.Core/ThingiProvider/Status/ProviderStatusServiceBase.cs` (escalation backoff), `src/NzbDrone.Core/Datastore/BasicRepository.cs` (Polly retry), `src/NzbDrone.Core/Indexers/HttpIndexerBase.cs` (exception handling with backoff)

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No API rate limiting middleware exists. No `express-rate-limit` equivalent, no API Gateway, no WAF rate rules. The application runs as a self-hosted Kestrel server with no throttling on API endpoints. An automated agent calling endpoints at machine speed could overwhelm the SQLite database or exhaust system resources.
- **Gap**: No rate limiting on API endpoints. A runaway agent loop could DDoS the self-hosted instance.
- **Compensating Controls**:
  - Deploy a reverse proxy (nginx, Caddy) with rate limiting configuration in front of Radarr.
  - Use ASP.NET Core's built-in rate limiting middleware (`Microsoft.AspNetCore.RateLimiting`) — available in .NET 8.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add ASP.NET Core rate limiting middleware to `Startup.cs` with configurable limits per client. This is a low-effort, high-impact improvement.
- **Evidence**: `src/NzbDrone.Host/Startup.cs` (no rate limiting middleware configured), `src/Radarr.Http/Middleware/` (no rate limiting middleware present)

#### DATA-Q2: Data Residency and Sovereignty ⚡

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Radarr is a self-hosted application — data resides wherever the user installs it (local machine, NAS, Docker container). There are no cross-region replication settings, no cloud deployment, and no centralized data storage. Data residency is entirely user-controlled. However, if an agent reads data from Radarr and transmits it to an LLM provider in a different jurisdiction, stored credentials (indexer API keys, download client passwords) could cross compliance boundaries.
- **Gap**: No data residency controls in the application itself. The risk depends on how the agent is deployed and which LLM provider processes the data. No documentation of data residency implications.
- **Compensating Controls**:
  - Ensure the agent architecture does not transmit credential fields to LLM providers (requires DATA-Q1 field-level redaction first).
  - Document data residency implications for agent deployments in the operational runbook.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement field-level redaction (DATA-Q1) to prevent credentials from being transmitted to LLM providers. Document that Radarr data is local and agent deployments must ensure data does not leave the user's jurisdiction without consent.
- **Evidence**: `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (local config/data storage), `src/NzbDrone.Core/Datastore/` (local SQLite/PostgreSQL)

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: `AuthenticationService.cs` logs IP addresses and usernames in plain text: `"Auth-Failure ip {0} username '{1}'"`, `"Auth-Success ip {0} username '{1}'"`, `"Auth-Unauthorized ip {0} url '{1}'"`. `LoggingMiddleware.cs` logs remote IP and User-Agent headers. No PII scrubbing middleware, no log masking libraries, no regex-based PII filters in the logging pipeline.
- **Gap**: IP addresses and usernames are logged in plain text. No PII redaction in logging pipeline.
- **Compensating Controls**:
  - Configure NLog to use a custom layout renderer that masks IP addresses and usernames.
  - Forward logs to a centralized system with PII redaction capabilities.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add a PII masking NLog layout renderer or log filter that redacts IP addresses and usernames from log output. This is a low-effort change in the NLog configuration.
- **Evidence**: `src/Radarr.Http/Authentication/AuthenticationService.cs` (lines with IP/username logging), `src/Radarr.Http/Middleware/LoggingMiddleware.cs` (IP and User-Agent logging)

### RISK-QUALITY — Address as Capacity Allows

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: `RadarrErrorPipeline.cs` handles exceptions with structured JSON error responses via `ErrorModel` (with `Message`, `Description`, `Content` fields). It differentiates exception types: `ApiException` (custom status codes), `ValidationException` (400 with validation errors), `ModelNotFoundException` (404), `ModelConflictException` (409), `SQLiteException` (409 for constraint failures). HTTP status codes are used correctly. However, the error model lacks a `retryable` boolean or error category field that would allow an agent to programmatically distinguish retriable from terminal errors.
- **Gap**: No `retryable` or `errorCategory` field in error responses. An agent cannot programmatically distinguish a retriable 503 from a terminal 400 without parsing the HTTP status code.
- **Compensating Controls**:
  - Agents can use HTTP status code ranges (4xx = terminal, 5xx = retriable) as a heuristic.
  - Document error response semantics in the OpenAPI spec.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add a `retryable` boolean and `errorCode` string field to the `ErrorModel` class.
- **Evidence**: `src/Radarr.Http/ErrorManagement/RadarrErrorPipeline.cs`, `src/Radarr.Http/ErrorManagement/ErrorModel.cs`

#### AUTH-Q4: Identity Propagation and Delegation — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No identity propagation mechanisms. No JWT parsing middleware, no OAuth2 on-behalf-of flows, no token exchange patterns. The single API key model does not carry caller identity context. When Radarr calls external services (TMDb, indexers, download clients), it uses its own configured credentials — there is no concept of "acting on behalf of" a specific user or agent.
- **Gap**: Cannot distinguish between an agent acting under its own identity vs. acting on behalf of a specific user.
- **Compensating Controls**:
  - For a self-hosted single-user application, identity propagation is less critical — the single user is the implicit subject.
  - Log the User-Agent header (already captured in `LoggingMiddleware`) to differentiate agent traffic from human traffic.
- **Remediation Timeline**: 90+ days (requires architectural changes)
- **Recommendation**: For a self-hosted single-user app, this is lower priority. If multi-user support is added, implement identity propagation.
- **Evidence**: `src/Radarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/Radarr.Http/Middleware/LoggingMiddleware.cs`

#### AUTH-Q5: Credential Management — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The API key is stored in a local XML configuration file (`config.xml`) managed by `ConfigFileProvider.cs`. No secrets manager integration (no AWS Secrets Manager, no HashiCorp Vault). No key rotation mechanism beyond `ResetApiKeyCommand` which generates a new GUID. Download client and indexer credentials are stored in the SQLite/PostgreSQL database without encryption. This is consistent with a self-hosted application model where credentials are on the user's local machine.
- **Gap**: No secrets manager, no automated rotation. Credentials stored in plain text in config file and database.
- **Compensating Controls**:
  - The self-hosted model means credentials are on the user's machine, reducing exposure compared to cloud deployments.
  - Restrict file permissions on the config file and database.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement optional database-level encryption for stored credentials. Document security best practices for file permissions.
- **Evidence**: `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (API key in XML config), `src/NzbDrone.Core/Configuration/ResetApiKeyCommand.cs`

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The CI/CD pipeline (`azure-pipelines.yml`) includes comprehensive testing: unit tests, integration tests, automation tests across Windows, Mac, Linux, FreeBSD, Alpine/musl. Docker-based test environments for PostgreSQL. SonarCloud analysis configured. However, there is no developer- or agent-facing sandbox environment with production-equivalent data shape for testing agent interactions.
- **Gap**: No sandbox/staging environment for agent testing. Agents must be tested against the user's live Radarr instance.
- **Compensating Controls**:
  - Users can run a separate Radarr instance for testing (the application supports running multiple instances with different data directories).
  - Docker images (community-maintained, e.g., `linuxserver/radarr`) enable quick sandbox creation.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Provide documentation and/or a Docker Compose file for setting up a sandbox Radarr instance with seed data for agent testing.
- **Evidence**: `azure-pipelines.yml` (test stages), `.github/workflows/ci.yml`

#### DATA-Q5: Temporal Metadata and Freshness — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Movies have an `Added` timestamp (`Movie.cs`). `MovieMetadata` includes `InCinemas`, `PhysicalRelease`, `DigitalRelease` dates. History records have dates. `MovieFile` has `DateAdded`. However, no `Cache-Control` headers, no `X-Data-Age` headers, no `last_refreshed` metadata, and no consistency level signaling in API responses. An agent cannot determine if the data returned is current or stale.
- **Gap**: No freshness signaling in API responses. Timestamps exist in data models but no mechanism to communicate data staleness to consumers.
- **Compensating Controls**:
  - Agents can use the `Added` and history date fields to assess data age.
  - The `/api/v3/command` endpoint can trigger a movie refresh to ensure data is current before reading.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add `Last-Modified` and `Cache-Control` headers to API responses. Include a `lastRefreshed` field in movie resources.
- **Evidence**: `src/NzbDrone.Core/Movies/Movie.cs` (Added field), `src/Radarr.Api.V3/openapi.json`

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: API is versioned at `/api/v3/`. OpenAPI spec is auto-generated via Swashbuckle and committed via CI pipeline (`Api_Docs` job in `azure-pipelines.yml`). Deprecated endpoints are marked with `[Obsolete]` attribute and return `Deprecation: true` header (`RestController.cs`). However, no breaking change detection tools in CI (no `buf breaking`, no OpenAPI diff, no Pact consumer-driven contract tests).
- **Gap**: No automated breaking change detection. API changes could silently break agent tool bindings.
- **Compensating Controls**:
  - The auto-generated OpenAPI spec in CI provides a snapshot for manual diff comparison.
  - The `[Obsolete]` attribute and deprecation header provide some signal to consumers.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add an OpenAPI diff step to the CI pipeline that flags breaking changes (e.g., `oasdiff` or `openapi-diff`).
- **Evidence**: `azure-pipelines.yml` (Api_Docs job), `src/Radarr.Http/REST/RestController.cs` (deprecation handling), `src/Radarr.Api.V3/openapi.json`

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: NLog is used for structured logging. `LoggingMiddleware.cs` assigns a sequential `ApiRequestSequenceID` per request and logs method, path, status code, and duration. Sentry integration exists for error tracking (source map uploads in `azure-pipelines.yml`, `@sentry/browser` in `package.json`, `ReconfigureSentry.cs`). However, no distributed tracing (no OpenTelemetry, no X-Ray, no `traceparent` header propagation). Logs are structured but use NLog's format rather than JSON. No correlation ID that spans across Radarr's calls to external services.
- **Gap**: No distributed tracing. `ApiRequestSequenceID` is local to the Radarr instance and does not propagate to external service calls. Cannot trace an agent-initiated request through Radarr to TMDb/indexer/download client calls.
- **Compensating Controls**:
  - The `ApiRequestSequenceID` provides per-request correlation within Radarr logs.
  - Sentry captures unhandled exceptions with stack traces.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenTelemetry instrumentation to the ASP.NET Core pipeline. .NET 8 has built-in OpenTelemetry support.
- **Evidence**: `src/Radarr.Http/Middleware/LoggingMiddleware.cs`, `src/NzbDrone.Core/Instrumentation/ReconfigureSentry.cs`, `package.json` (@sentry/browser)

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No alerting thresholds configured for error rates or latency. No CloudWatch alarms, no PagerDuty/OpsGenie integration. Radarr has a `/api/v3/health` endpoint that reports system health issues (disk space, indexer availability, download client status) but no SLA-based alerting. Notifications can be configured for download events but not for API health metrics.
- **Gap**: No automated alerting on API error rates or latency. Users must manually monitor the health endpoint.
- **Compensating Controls**:
  - External monitoring tools (UptimeRobot, Healthchecks.io) can poll the `/api/v3/health` endpoint.
  - The notification system can be extended to alert on health check failures.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Expose Prometheus-compatible metrics endpoint for error rates and latency. Enable integration with external monitoring.
- **Evidence**: `src/NzbDrone.Core/HealthCheck/`, `src/Radarr.Api.V3/Health/`

#### ENG-Q1: Infrastructure Governance — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No IaC files in the repository. No Terraform, CloudFormation, CDK, Helm, or Kustomize definitions. This is consistent with Radarr's nature as a self-hosted application — the infrastructure is user-managed (installed on personal machines, NAS devices, or Docker containers with community-maintained images).
- **Gap**: No IaC for the deployment infrastructure. Infrastructure configuration is manual and user-specific.
- **Compensating Controls**:
  - Community-maintained Docker images (e.g., `linuxserver/radarr`) provide standardized deployment.
  - The application is self-contained with minimal infrastructure requirements.
- **Remediation Timeline**: N/A (by design for self-hosted applications)
- **Recommendation**: For agent deployments, provide an official Docker Compose template that includes a reverse proxy with rate limiting and auth proxy.
- **Evidence**: Root directory (no IaC files), `distribution/` directory (packaging scripts only)

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive CI/CD via Azure Pipelines with: backend build (Windows, Mac, Linux), frontend build, unit tests, integration tests (`NzbDrone.Integration.Test`), automation tests (`NzbDrone.Automation.Test`), SonarCloud analysis, coverage reports. OpenAPI spec auto-generated and committed. However, no explicit API contract tests — no Pact, no OpenAPI diff validation, no breaking change detection in the pipeline.
- **Gap**: No automated API contract testing to catch breaking changes before they reach production.
- **Compensating Controls**:
  - Integration tests provide some coverage of API behavior.
  - Auto-generated OpenAPI spec provides a baseline for manual comparison.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenAPI spec diff step to CI pipeline. Consider adding Pact or similar consumer-driven contract tests.
- **Evidence**: `azure-pipelines.yml` (multi-stage pipeline), `.github/workflows/ci.yml`, `src/NzbDrone.Integration.Test/`, `src/NzbDrone.Automation.Test/`

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Radarr includes a self-update mechanism (`NzbDrone.Update` project). Users can manually roll back by reinstalling a previous version. The application backs up the database before updates. However, there is no automated rollback capability — no blue/green deployment, no canary, no feature flags, no CodeDeploy integration.
- **Gap**: No automated rollback. Rollback requires manual intervention (reinstall previous version).
- **Compensating Controls**:
  - Database backups before updates provide data recovery capability.
  - Docker-based deployments can roll back by changing the container image tag.
- **Remediation Timeline**: N/A (acceptable for self-hosted application model)
- **Recommendation**: Document rollback procedures for agent-integrated deployments. For Docker deployments, pin to specific version tags.
- **Evidence**: `src/NzbDrone.Update/` (update mechanism), `azure-pipelines.yml` (release packaging)

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Integration tests exist (`NzbDrone.Integration.Test`) that test API endpoints. Automation tests (`NzbDrone.Automation.Test`) test UI-driven workflows. Unit tests cover core business logic. SonarCloud analysis with coverage reports is configured. Tests run across Windows, Mac, Linux, FreeBSD, Alpine/musl, and with PostgreSQL 14/15. However, no explicit API contract tests are visible, and coverage of individual API endpoints for input validation, error responses, and edge cases is not measurable from the pipeline configuration alone.
- **Gap**: No explicit API contract test coverage metrics. Cannot verify comprehensive coverage of all endpoints agents would consume.
- **Compensating Controls**:
  - Existing integration and automation tests provide baseline API coverage.
  - SonarCloud tracks overall code coverage.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add API-specific test coverage metrics. Ensure all endpoints used by agents have dedicated integration tests.
- **Evidence**: `azure-pipelines.yml` (test stages), `src/NzbDrone.Integration.Test/`, `src/NzbDrone.Automation.Test/`

#### ENG-Q5: Encryption at Rest — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: SQLite database is stored as a local file with no encryption at rest. PostgreSQL support is available but encryption depends on the user's deployment configuration. No KMS integration, no transparent data encryption in the application layer. Credentials for indexers and download clients are stored in plaintext in the database.
- **Gap**: No encryption at rest for the SQLite database. Stored credentials are unencrypted on disk.
- **Compensating Controls**:
  - File system-level encryption (BitLocker, LUKS, FileVault) can provide encryption at rest.
  - PostgreSQL deployments can enable TDE independently.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement SQLCipher for encrypted SQLite databases, or at minimum encrypt credential fields before storing them in the database.
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs` (SQLite), `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (PostgreSQL config)

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO
- **Finding**: Radarr exposes a well-documented REST API at `/api/v3/*` via ASP.NET Core controllers. An OpenAPI 3.0.4 specification is maintained at `src/Radarr.Api.V3/openapi.json` (12,843 lines, 302 KB), auto-generated via Swashbuckle. The API covers movies, history, queue, commands, download clients, indexers, quality profiles, system configuration, and more. No direct database access or file-based exchange patterns are required.
- **Implication**: The API surface is well-suited for agent tool binding. The OpenAPI spec can be used to auto-generate agent tool definitions.
- **Recommendation**: No action needed. This is a strength.
- **Evidence**: `src/Radarr.Api.V3/openapi.json`, `src/NzbDrone.Host/Startup.cs` (Swagger config), `src/Radarr.Api.V3/` (controller directory)

### API-Q2: Machine-Readable API Specification

- **Severity**: INFO
- **Finding**: OpenAPI 3.0.4 specification exists at `src/Radarr.Api.V3/openapi.json`, auto-generated via Swashbuckle/Swagger in `Startup.cs`. The `Api_Docs` job in `azure-pipelines.yml` auto-generates the spec, commits changes, and creates a PR for review. The spec is kept current with the implementation via CI automation.
- **Implication**: Agent frameworks can consume the OpenAPI spec directly for tool generation. The auto-generation ensures the spec stays in sync with code.
- **Recommendation**: No action needed. This is a strength.
- **Evidence**: `src/Radarr.Api.V3/openapi.json`, `azure-pipelines.yml` (Api_Docs job), `src/NzbDrone.Host/Startup.cs`

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No idempotency key support in write endpoints. POST endpoints create new resources without idempotency checks. `RestController.cs` does not implement idempotency middleware. Write endpoints rely on database constraints (unique keys) for some degree of duplicate prevention, but no explicit idempotency key header or parameter is supported.
- **Implication**: For read-only agent scope, this is informational. If write-enabled scope is adopted, idempotency would need to be implemented to prevent duplicate resource creation from agent retries.
- **Recommendation**: If write-enabled scope is planned, implement idempotency key support (e.g., `X-Idempotency-Key` header) for POST endpoints.
- **Evidence**: `src/Radarr.Http/REST/RestController.cs`, `src/Radarr.Api.V3/Movies/`

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: All API responses use JSON format via `System.Text.Json` serialization (`STJson.ApplySerializerSettings` in `Startup.cs`). Content-Type is `application/json`. The `VersionMiddleware` adds `X-Application-Version` header to API responses. No XML, binary, or protobuf responses.
- **Implication**: JSON is the optimal format for LLM-based agent consumption. No additional parsing adapters are needed.
- **Recommendation**: No action needed.
- **Evidence**: `src/NzbDrone.Host/Startup.cs` (JSON serializer config), `src/Radarr.Http/Middleware/VersionMiddleware.cs`

### API-Q6: Asynchronous Operation Support

- **Severity**: INFO
- **Finding**: The Command system (`/api/v3/command`) supports asynchronous operations. Commands are queued via `POST /api/v3/command`, assigned an ID, and can be polled for status via `GET /api/v3/command/{id}`. SignalR provides real-time status updates. Commands include movie refresh, indexer search, RSS sync, and manual import — operations that can take >30 seconds. The `CommandController` broadcasts status updates via SignalR (`CommandUpdatedEvent`).
- **Implication**: Agents can use the command system for long-running operations with polling or SignalR subscription for completion notification.
- **Recommendation**: No action needed. The async pattern is well-implemented.
- **Evidence**: `src/Radarr.Api.V3/Commands/CommandController.cs`, `src/NzbDrone.Host/Startup.cs` (SignalR hub)

### API-Q7: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: SignalR hub at `/signalr/messages` broadcasts real-time state change notifications. `RestControllerWithSignalR` automatically broadcasts model events (Created, Updated, Deleted, Sync) for all resources that extend this base class. Notifications are structured as `ResourceChangeMessage` with the action type and resource body.
- **Implication**: Agents can subscribe to the SignalR hub for real-time event-driven patterns rather than polling. This enables proactive agent behavior.
- **Recommendation**: Document the SignalR message format for agent developers.
- **Evidence**: `src/Radarr.Http/REST/RestControllerWithSignalR.cs`, `src/NzbDrone.Host/Startup.cs` (MapHub)

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limit headers (`X-RateLimit-Remaining`, `Retry-After`) are returned in API responses. No rate limit documentation exists in the OpenAPI spec. The indexer subsystem respects rate limits from external services (`TooManyRequestsException`, `RequestLimitReachedException` handling in `HttpIndexerBase.cs`), but the Radarr API itself does not communicate rate limits to its consumers.
- **Implication**: Agents have no programmatic way to determine rate limits. Without rate limit awareness, agents may inadvertently overwhelm the instance. This interacts with STATE-Q5 (no rate limiting).
- **Recommendation**: If rate limiting is added (STATE-Q5), include `X-RateLimit-Remaining` and `Retry-After` headers in responses.
- **Evidence**: `src/Radarr.Http/Middleware/` (no rate limit headers), `src/NzbDrone.Core/Indexers/HttpIndexerBase.cs` (external rate limit handling)

### STATE-Q2: Queryable Current State

- **Severity**: INFO
- **Finding**: State is fully queryable via GET endpoints for all resources: movies (`/api/v3/movie`), queue (`/api/v3/queue`), history (`/api/v3/history`), download clients, indexers, quality profiles, system status, health checks, and more. The OpenAPI spec documents all GET endpoints. Agents can inspect current state before taking action.
- **Implication**: Agents have comprehensive read access to the application's current state. This is a strength for read-only agent scope.
- **Recommendation**: No action needed.
- **Evidence**: `src/Radarr.Api.V3/openapi.json`, `src/Radarr.Api.V3/` (all controller directories)

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No optimistic locking (no version fields, no ETags, no `If-Match` headers). `BasicRepository.cs` uses Polly retry with exponential backoff for SQLite busy errors (database-level locking), but no application-level concurrency controls. No conflict resolution logic for concurrent writes.
- **Implication**: For read-only agent scope, this is informational. If write-enabled scope is adopted, concurrent agent writes could cause data integrity issues.
- **Recommendation**: If write-enabled scope is planned, implement optimistic locking (version fields + `If-Match` header support).
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs` (Polly retry, no version fields)

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits per agent identity. No `max_records_per_operation` or `max_spend_per_session` controls. All API consumers have identical unlimited access.
- **Implication**: For read-only agent scope, blast radius is limited to data access volume (no destructive operations). If write-enabled scope is adopted, transaction limits would be critical.
- **Recommendation**: If write-enabled scope is planned, implement per-key transaction limits.
- **Evidence**: `src/Radarr.Http/REST/RestController.cs`, `src/NzbDrone.Host/Startup.cs`

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No draft/pending state for movie entities. Movies are either monitored or unmonitored. The Command system has operational states (queued/started/completed/failed) but these are execution states, not approval workflows. No two-step commit patterns exist.
- **Implication**: For read-only scope, this is informational. For write-enabled scope, draft states would be valuable for human review of agent-proposed changes.
- **Recommendation**: If write-enabled scope is planned, consider adding a "proposed" status for agent-initiated movie additions.
- **Evidence**: `src/NzbDrone.Core/Movies/Movie.cs`, `src/Radarr.Api.V3/Commands/CommandController.cs`

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No approval workflow endpoints. No configurable operation-level approval flags. No Step Functions with human approval tasks. All API operations execute immediately upon request.
- **Implication**: For read-only scope, this is informational. For write-enabled scope, approval gates would be valuable for high-risk operations (e.g., bulk movie deletion).
- **Recommendation**: If write-enabled scope is planned, implement configurable approval requirements per operation type.
- **Evidence**: `src/Radarr.Api.V3/` (no approval endpoints)

### DATA-Q3: Selective Query Support

- **Severity**: INFO
- **Finding**: Pagination is implemented via `PagingResource.cs` and `PagingSpec.cs`. Endpoints supporting pagination include history, queue, blocklist, wanted/missing, and logs. Parameters: `page`, `pageSize`, `sortKey`, `sortDirection`. Default page size is 10. Filter expressions are supported. The `BasicRepository.GetPaged` method enforces pagination with `LIMIT` and `OFFSET`.
- **Implication**: Agents can retrieve bounded result sets, preventing context window exhaustion. This is a strength.
- **Recommendation**: Ensure all list endpoints support pagination. Consider adding cursor-based pagination for large datasets.
- **Evidence**: `src/Radarr.Http/PagingResource.cs`, `src/NzbDrone.Core/Datastore/PagingSpec.cs`, `src/NzbDrone.Core/Datastore/BasicRepository.cs` (GetPaged)

### DATA-Q4: System of Record Designations

- **Severity**: INFO
- **Finding**: Clear system-of-record designations exist. Radarr is the system of record for movie collection management (monitored movies, quality profiles, download preferences). TMDb (The Movie Database) is the authoritative source for movie metadata (titles, release dates, ratings, posters). The `MetadataSource` module manages synchronization with TMDb. Download clients and indexers are external systems with their own state.
- **Implication**: Agents can rely on Radarr as the single source of truth for collection state and TMDb for metadata. No conflicting data sources for the same entities.
- **Recommendation**: No action needed. Document the system-of-record designations for agent developers.
- **Evidence**: `src/NzbDrone.Core/MetadataSource/`, `src/NzbDrone.Core/Movies/RefreshMovieService.cs`

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality scores, no completeness metrics, no data profiling dashboards. No null rate monitoring or duplicate detection logic. The `/api/v3/health` endpoint reports system-level issues but not data quality issues.
- **Implication**: Agents cannot assess data quality before reasoning. Movie metadata completeness depends on TMDb data quality.
- **Recommendation**: Consider adding data quality indicators (e.g., metadata completeness percentage per movie) to API responses.
- **Evidence**: `src/NzbDrone.Core/HealthCheck/`, `src/Radarr.Api.V3/Health/`

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Field names are human-readable and semantically meaningful: `movieId`, `sourceTitle`, `qualityProfileId`, `rootFolderPath`, `monitored`, `minimumAvailability`, `added`, `movieFileId`, `tmdbId`, `imdbId`. No legacy abbreviations. CamelCase naming convention consistently applied across all API resources.
- **Implication**: LLM-based agents can reason about data fields without a data dictionary. Field names are self-documenting.
- **Recommendation**: No action needed. This is a strength.
- **Evidence**: `src/Radarr.Api.V3/openapi.json`, `src/NzbDrone.Core/Movies/Movie.cs`

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No formal data catalog (no AWS Glue Data Catalog, no Collibra, no DataHub). API documentation is available via the auto-generated OpenAPI/Swagger spec. The Radarr wiki (external) provides user-facing documentation. Database schema is implicit in the C# model classes.
- **Implication**: Agent tool developers must rely on the OpenAPI spec for understanding data structures. No additional semantic metadata layer exists.
- **Recommendation**: Consider publishing the OpenAPI spec as a discoverable resource (already available at `/docs/v3/openapi.json` in debug mode).
- **Evidence**: `src/Radarr.Api.V3/openapi.json`, `src/NzbDrone.Host/Startup.cs` (Swagger route)

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No custom business metrics published. No equivalent of `cloudwatch.put_metric_data`. The health check system reports system issues (disk space, indexer health, download client status) but not business outcomes (e.g., movies downloaded per week, search success rate, queue throughput).
- **Implication**: Cannot measure whether agent interactions produce good business outcomes. Metrics must be derived from API data externally.
- **Recommendation**: Consider exposing aggregate statistics via the API (e.g., movies added this month, download success rate).
- **Evidence**: `src/NzbDrone.Core/HealthCheck/`, `src/Radarr.Api.V3/Health/`

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO (passes — no gap)
- **Finding**: Well-documented REST API at `/api/v3/*` with OpenAPI 3.0.4 specification auto-generated via Swashbuckle. 40+ API controllers covering all application resources.
- **Gap**: None
- **Recommendation**: No action needed
- **Evidence**: `src/Radarr.Api.V3/openapi.json`, `src/NzbDrone.Host/Startup.cs`

#### API-Q2: Machine-Readable API Specification
- **Severity**: INFO (passes — no gap)
- **Finding**: OpenAPI 3.0.4 spec at `src/Radarr.Api.V3/openapi.json`, auto-generated and auto-committed via CI pipeline.
- **Gap**: None
- **Recommendation**: No action needed
- **Evidence**: `src/Radarr.Api.V3/openapi.json`, `azure-pipelines.yml`

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: `ErrorModel` provides structured JSON errors with `Message`, `Description`, `Content`. Exception types mapped to HTTP status codes. Missing `retryable` indicator.
- **Gap**: No `retryable` boolean or error category for agent consumption
- **Recommendation**: Add `retryable` and `errorCode` fields to `ErrorModel`
- **Evidence**: `src/Radarr.Http/ErrorManagement/RadarrErrorPipeline.cs`, `src/Radarr.Http/ErrorManagement/ErrorModel.cs`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No idempotency key support. Database constraints provide some duplicate prevention.
- **Gap**: No explicit idempotency mechanism for write endpoints
- **Recommendation**: Implement idempotency keys if write-enabled scope is planned
- **Evidence**: `src/Radarr.Http/REST/RestController.cs`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: All responses in JSON via System.Text.Json. `application/json` content type.
- **Gap**: None
- **Recommendation**: No action needed
- **Evidence**: `src/NzbDrone.Host/Startup.cs`

#### API-Q6: Asynchronous Operation Support
- **Severity**: INFO (passes — extended question, triggered for operations >30s)
- **Finding**: Command system supports async via `/api/v3/command` with polling and SignalR notifications.
- **Gap**: None
- **Recommendation**: No action needed
- **Evidence**: `src/Radarr.Api.V3/Commands/CommandController.cs`

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO (extended, triggered for stateful-crud)
- **Finding**: SignalR hub at `/signalr/messages` broadcasts real-time CRUD events.
- **Gap**: None — event emission is well-implemented
- **Recommendation**: Document SignalR message format for agent developers
- **Evidence**: `src/Radarr.Http/REST/RestControllerWithSignalR.cs`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit headers or documentation. External rate limits handled in indexer subsystem.
- **Gap**: No rate limit communication to API consumers
- **Recommendation**: Add rate limit headers when rate limiting is implemented
- **Evidence**: `src/Radarr.Http/Middleware/`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: Single shared API key. No per-agent principal attribution.
- **Gap**: Cannot distinguish individual agent identities
- **Recommendation**: Implement multi-key support with named principals
- **Evidence**: `src/Radarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: Single API key grants full access to all endpoints, read and write.
- **Gap**: No scoped permissions mechanism
- **Recommendation**: Implement role/scope system for API keys
- **Evidence**: `src/Radarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization. All authenticated requests have full CRUD access.
- **Gap**: Cannot restrict agent to read-only actions per resource
- **Recommendation**: Add method-level permission checks to RestController
- **Evidence**: `src/Radarr.Http/REST/RestController.cs`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: RISK-QUALITY
- **Finding**: No identity propagation. Single API key model carries no caller context.
- **Gap**: Cannot distinguish agent-as-self vs agent-on-behalf-of-user
- **Recommendation**: Lower priority for single-user self-hosted app
- **Evidence**: `src/Radarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`

#### AUTH-Q5: Credential Management
- **Severity**: RISK-QUALITY
- **Finding**: API key in local XML config file. No secrets manager. No automated rotation.
- **Gap**: No secrets management, no rotation mechanism
- **Recommendation**: Implement optional credential encryption
- **Evidence**: `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Auth events logged via NLog. Logs are local mutable files. No immutable storage.
- **Gap**: No immutable audit trail
- **Recommendation**: Configure syslog forwarding to immutable store
- **Evidence**: `src/Radarr.Http/Authentication/AuthenticationService.cs`, `src/Radarr.Http/Middleware/LoggingMiddleware.cs`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: Single API key — revocation is all-or-nothing via `ResetApiKeyCommand`.
- **Gap**: Cannot suspend individual agent identities
- **Recommendation**: Implement multi-key support with per-key revocation
- **Evidence**: `src/NzbDrone.Core/Configuration/ResetApiKeyCommand.cs`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No saga patterns or rollback endpoints. Database transactions for InsertMany only.
- **Gap**: No application-level compensation for multi-step workflows
- **Recommendation**: Acceptable for read-only scope; implement if write-enabled is planned
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs`

#### STATE-Q2: Queryable Current State
- **Severity**: INFO (passes — extended, triggered for stateful-crud)
- **Finding**: All resources queryable via GET endpoints. Comprehensive read access.
- **Gap**: None
- **Recommendation**: No action needed
- **Evidence**: `src/Radarr.Api.V3/openapi.json`

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No optimistic locking. Polly retry for SQLite busy errors.
- **Gap**: No application-level concurrency controls
- **Recommendation**: Implement optimistic locking if write-enabled is planned
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY (extended, triggered — has external dependencies)
- **Finding**: Partial resilience via `ProviderStatusServiceBase` escalation backoff. Polly retry for SQLite. No formal circuit breaker pattern.
- **Gap**: No formal circuit breaker on outbound HTTP calls
- **Recommendation**: Add Polly CircuitBreaker policies
- **Evidence**: `src/NzbDrone.Core/ThingiProvider/Status/ProviderStatusServiceBase.cs`, `src/NzbDrone.Core/Indexers/HttpIndexerBase.cs`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No API rate limiting. Self-hosted Kestrel server with no throttling.
- **Gap**: No rate limiting on API endpoints
- **Recommendation**: Add ASP.NET Core rate limiting middleware
- **Evidence**: `src/NzbDrone.Host/Startup.cs`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No transaction limits per agent identity.
- **Gap**: No configurable blast radius controls
- **Recommendation**: Implement if write-enabled scope is planned
- **Evidence**: `src/Radarr.Http/REST/RestController.cs`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path. Priority is P2.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No draft/pending state. Movies are monitored/unmonitored. Command system has operational states.
- **Gap**: No draft states for human review of agent proposals
- **Recommendation**: Consider adding draft states if write-enabled scope is planned
- **Evidence**: `src/NzbDrone.Core/Movies/Movie.cs`

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No approval workflows. All operations execute immediately.
- **Gap**: No configurable approval gates
- **Recommendation**: Consider implementing if write-enabled scope is planned
- **Evidence**: `src/Radarr.Api.V3/`

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive CI/CD testing but no developer/agent-facing sandbox.
- **Gap**: No sandbox environment for agent testing
- **Recommendation**: Provide Docker Compose template for sandbox setup
- **Evidence**: `azure-pipelines.yml`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: Stores download client/indexer credentials without classification or field-level encryption.
- **Gap**: No data classification or access controls on sensitive fields
- **Recommendation**: Implement field-level redaction using existing PrivacyLevel enum
- **Evidence**: `src/Radarr.Http/ClientSchema/`, `src/Radarr.Api.V3/DownloadClient/`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Self-hosted, user-controlled data residency. Risk if agent transmits credentials to LLM.
- **Gap**: No data residency controls in application
- **Recommendation**: Implement field-level redaction to prevent credential transmission
- **Evidence**: `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`

#### DATA-Q3: Selective Query Support
- **Severity**: INFO (passes — extended, triggered for stateful-crud)
- **Finding**: Pagination implemented with page, pageSize, sortKey, sortDirection, filters.
- **Gap**: None
- **Recommendation**: Consider cursor-based pagination for large datasets
- **Evidence**: `src/Radarr.Http/PagingResource.cs`, `src/NzbDrone.Core/Datastore/PagingSpec.cs`

#### DATA-Q4: System of Record Designations
- **Severity**: INFO (passes — extended, triggered for stateful-crud)
- **Finding**: Clear SoR: Radarr for collection state, TMDb for metadata.
- **Gap**: None
- **Recommendation**: Document for agent developers
- **Evidence**: `src/NzbDrone.Core/MetadataSource/`

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK-QUALITY (extended, triggered for stateful-crud)
- **Finding**: Timestamps exist (Added, InCinemas, etc.) but no freshness signaling headers.
- **Gap**: No Cache-Control, X-Data-Age, or lastRefreshed in API responses
- **Recommendation**: Add Last-Modified and Cache-Control headers
- **Evidence**: `src/NzbDrone.Core/Movies/Movie.cs`

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: IP addresses and usernames logged in plain text. No PII scrubbing.
- **Gap**: No PII redaction in logging pipeline
- **Recommendation**: Add PII masking NLog filter
- **Evidence**: `src/Radarr.Http/Authentication/AuthenticationService.cs`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics. Health checks report system issues, not data quality.
- **Gap**: No data quality indicators
- **Recommendation**: Consider adding metadata completeness indicators
- **Evidence**: `src/NzbDrone.Core/HealthCheck/`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: Versioned API (/api/v3/), auto-generated OpenAPI spec, deprecation headers. No breaking change detection in CI.
- **Gap**: No automated breaking change detection
- **Recommendation**: Add OpenAPI diff to CI pipeline
- **Evidence**: `azure-pipelines.yml`, `src/Radarr.Http/REST/RestController.cs`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Human-readable camelCase field names. No legacy abbreviations.
- **Gap**: None
- **Recommendation**: No action needed
- **Evidence**: `src/Radarr.Api.V3/openapi.json`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal data catalog. OpenAPI spec serves as API documentation.
- **Gap**: No semantic metadata layer
- **Recommendation**: Publish OpenAPI spec as discoverable resource
- **Evidence**: `src/Radarr.Api.V3/openapi.json`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: NLog logging with request sequence IDs. Sentry for error tracking. No distributed tracing.
- **Gap**: No OpenTelemetry or distributed trace propagation
- **Recommendation**: Add OpenTelemetry instrumentation (.NET 8 built-in support)
- **Evidence**: `src/Radarr.Http/Middleware/LoggingMiddleware.cs`, `src/NzbDrone.Core/Instrumentation/ReconfigureSentry.cs`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: Health check endpoint exists. No automated alerting thresholds.
- **Gap**: No alerting on API error rates or latency
- **Recommendation**: Expose Prometheus metrics endpoint
- **Evidence**: `src/NzbDrone.Core/HealthCheck/`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics. Health checks cover system issues only.
- **Gap**: No business outcome measurement
- **Recommendation**: Expose aggregate statistics via API
- **Evidence**: `src/NzbDrone.Core/HealthCheck/`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance
- **Severity**: RISK-QUALITY
- **Finding**: No IaC files. Self-hosted application with user-managed infrastructure.
- **Gap**: No IaC for deployment infrastructure
- **Recommendation**: Provide official Docker Compose template
- **Evidence**: Root directory (no IaC files)

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive CI/CD with multi-platform testing. No API contract tests.
- **Gap**: No automated API contract testing
- **Recommendation**: Add OpenAPI diff and contract tests to CI
- **Evidence**: `azure-pipelines.yml`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: Self-update mechanism with database backups. No automated rollback.
- **Gap**: No automated rollback capability
- **Recommendation**: Document rollback procedures; pin Docker tags
- **Evidence**: `src/NzbDrone.Update/`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: Integration and automation tests exist. SonarCloud analysis. No explicit API contract coverage metrics.
- **Gap**: No API-specific coverage metrics
- **Recommendation**: Add API test coverage metrics
- **Evidence**: `azure-pipelines.yml`, `src/NzbDrone.Integration.Test/`

#### ENG-Q5: Encryption at Rest
- **Severity**: RISK-QUALITY (extended, triggered — has persistent data stores)
- **Finding**: SQLite database unencrypted on disk. PostgreSQL encryption depends on deployment.
- **Gap**: No encryption at rest in application layer
- **Recommendation**: Implement SQLCipher or credential field encryption
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs`

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `src/Radarr.Http/Authentication/ApiKeyAuthenticationHandler.cs` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4, API-Q4 |
| `src/Radarr.Http/Authentication/AuthenticationService.cs` | AUTH-Q6, DATA-Q6 |
| `src/Radarr.Http/Authentication/AuthenticationBuilderExtensions.cs` | AUTH-Q1 |
| `src/Radarr.Http/REST/RestController.cs` | API-Q3, API-Q4, AUTH-Q3, DISC-Q1, STATE-Q6 |
| `src/Radarr.Http/REST/RestControllerWithSignalR.cs` | API-Q7 |
| `src/Radarr.Http/ErrorManagement/RadarrErrorPipeline.cs` | API-Q3 |
| `src/Radarr.Http/ErrorManagement/ErrorModel.cs` | API-Q3 |
| `src/Radarr.Http/PagingResource.cs` | DATA-Q3 |
| `src/Radarr.Http/Middleware/LoggingMiddleware.cs` | AUTH-Q6, DATA-Q6, OBS-Q1 |
| `src/Radarr.Http/Middleware/VersionMiddleware.cs` | API-Q5 |
| `src/NzbDrone.Host/Startup.cs` | API-Q1, API-Q2, API-Q5, API-Q6, AUTH-Q1, STATE-Q5 |
| `src/NzbDrone.Core/Datastore/BasicRepository.cs` | STATE-Q1, STATE-Q3, STATE-Q4, ENG-Q5 |
| `src/NzbDrone.Core/Datastore/PagingSpec.cs` | DATA-Q3 |
| `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` | AUTH-Q1, AUTH-Q5, AUTH-Q6, DATA-Q2 |
| `src/NzbDrone.Core/Configuration/ResetApiKeyCommand.cs` | AUTH-Q5, AUTH-Q7 |
| `src/NzbDrone.Core/Movies/Movie.cs` | DATA-Q5, HITL-Q1, DISC-Q2 |
| `src/NzbDrone.Core/ThingiProvider/Status/ProviderStatusServiceBase.cs` | STATE-Q4 |
| `src/NzbDrone.Core/Indexers/HttpIndexerBase.cs` | STATE-Q4, API-Q8 |
| `src/NzbDrone.Core/Instrumentation/ReconfigureSentry.cs` | OBS-Q1 |
| `src/NzbDrone.Core/Instrumentation/DatabaseTarget.cs` | AUTH-Q6 |
| `src/Radarr.Api.V3/Commands/CommandController.cs` | API-Q6, STATE-Q1 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `src/Radarr.Api.V3/openapi.json` | API-Q1, API-Q2, DATA-Q1, DATA-Q5, DISC-Q1, DISC-Q2, DISC-Q3, STATE-Q2 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `azure-pipelines.yml` | API-Q2, DISC-Q1, ENG-Q2, ENG-Q3, ENG-Q4, HITL-Q3, OBS-Q1 |
| `.github/workflows/ci.yml` | ENG-Q2, HITL-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `package.json` | OBS-Q1 (Sentry dependency) |
| `global.json` | Step 1 (SDK version) |
| `src/Directory.Build.props` | Step 1 (build configuration) |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `src/NuGet.config` | Step 1 (package sources) |
