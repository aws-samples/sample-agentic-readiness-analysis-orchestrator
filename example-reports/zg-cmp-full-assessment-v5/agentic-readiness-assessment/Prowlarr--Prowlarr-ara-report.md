# Agentic Readiness Assessment Report

**Target**: Prowlarr (Indexer manager/proxy for the *arr suite)
**Date**: 2026-04-30
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**TD Version**: 3g1ipe93e5d2wb6n
**Repository Type**: monorepo (single application assessed as unified service)
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: csharp, media, desktop
**Context**: Indexer manager/proxy for the *arr suite.

**Archetype Justification**: Prowlarr has persistent state (SQLite/PostgreSQL via Dapper ORM), exposes full CRUD endpoints for indexers, applications, notifications, and download clients, and manages entity lifecycle with user-specific data. Although it proxies requests to external indexer APIs, its primary pattern is CRUD management of indexer configurations.

**Surface flags**:
- has_persistent_data_store: true
- has_http_rpc_surface: true
- has_auth_surface: true
- has_write_operations: true
- has_logging_of_user_data: true

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 2 | **RISK-SAFETY**: 9 | **RISK-QUALITY**: 14 | **INFOs**: 17

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 2 |
| RISK-SAFETY | 9 |
| RISK-QUALITY | 14 |
| INFO | 17 |
| N/A | 0 |
| Not Evaluated (extended) | 1 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 8
**Extended Questions Not Triggered**: 1 (STATE-Q7)
**Questions N/A (repo_type: monorepo)**: 0
**Service Archetype**: stateful-crud (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: Prowlarr supports API key authentication via `ApiKeyAuthenticationHandler` (`X-Api-Key` header or `apikey` query parameter). However, the entire application shares a **single API key** generated at first launch and stored in `config.xml`. All API consumers — human users, connected *arr applications (Sonarr, Radarr), and any agent — authenticate with the same key. The `ClaimsPrincipal` created on successful auth contains only a generic `ApiKey=true` claim with no agent-specific identity. There is no principal attribution — audit logs cannot distinguish which caller made a request.
- **Gap**: No per-agent identity mechanism. No principal attribution in authenticated sessions. A single shared key means all consumers are indistinguishable. Cannot attribute API calls to a specific agent instance.
- **Remediation**:
  - **Immediate**: Implement support for multiple API keys, each with a unique identifier (e.g., `agent-name` or `client-id` claim). Modify `ApiKeyAuthenticationHandler` to look up the provided key in a registry of named keys and inject the key name into the `ClaimsPrincipal`.
  - **Target State**: Each agent has a dedicated API key with a human-readable name, and the authenticated principal name appears in every log entry for that request.
  - **Estimated Effort**: Medium (2–4 weeks)
  - **Dependencies**: AUTH-Q6 (immutable audit logging depends on having a distinguishable principal)
- **Evidence**: `src/Prowlarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (ApiKey property)

---

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: Prowlarr stores sensitive data across multiple categories:
  - **User credentials**: `Users` table stores `Username`, `Password` (hashed), `Salt`, and `Iterations` (`src/NzbDrone.Core/Authentication/User.cs`).
  - **Indexer credentials**: Indexer definitions store API keys, cookies, usernames, and passwords in a JSON `Settings` column (visible in `src/NzbDrone.Core/Indexers/IndexerDefinition.cs` and exposed via `src/Prowlarr.Api.V1/Indexers/IndexerResource.cs`).
  - **Download client credentials**: Download client settings similarly contain authentication tokens and connection strings.
  - **Application sync credentials**: Connected *arr application settings contain API keys for remote systems.
  
  Stage A = **Yes** — the system stores user credentials, third-party API keys, and authentication secrets.
  
  Stage B: No field-level data classification, no tagging, no access controls differentiating which API consumers can read credential fields. The OpenAPI spec exposes indexer settings (including credential fields) to any authenticated caller. No data masking or field-level encryption.
- **Gap**: Sensitive fields (passwords, API keys, tokens) are not classified at the schema level, not tagged, and not protected by field-level access controls. An agent with the shared API key can read indexer credentials.
- **Remediation**:
  - **Immediate**: Add a `SensitiveResourceAttribute` or equivalent to credential fields in API resources. Modify resource mappers to redact sensitive fields (replace with `"(redacted)"`) in API responses for read operations. Prowlarr already has a `FieldDefinition.Privacy` property in the client schema (`src/Prowlarr.Http/ClientSchema/`) — extend this to enforce server-side redaction.
  - **Target State**: Credential fields are classified as sensitive at the schema level and are never returned in API GET responses. Write operations accept credentials but never echo them back.
  - **Estimated Effort**: Medium (2–4 weeks)
  - **Dependencies**: AUTH-Q2 (scoped permissions would allow some agents to access unredacted data if needed)
- **Evidence**: `src/NzbDrone.Core/Authentication/User.cs`, `src/NzbDrone.Core/Indexers/IndexerDefinition.cs`, `src/Prowlarr.Api.V1/Indexers/IndexerResource.cs`, `src/Prowlarr.Http/ClientSchema/`

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Prowlarr has a single authentication tier: API key grants full access to all endpoints. There is no RBAC, no role differentiation, and no ability to create a read-only API key. The `ApiKeyAuthenticationHandler` performs a simple string comparison — if the key matches, the caller gets a `ClaimsPrincipal` with `ApiKey=true` and full access to every controller action.
- **Gap**: Cannot scope an agent to read-only access on specific resources (e.g., search-only without indexer management). All API key holders have identical, unrestricted access.
- **Compensating Controls**:
  - Deploy a reverse proxy (e.g., nginx, Caddy) in front of Prowlarr that restricts the agent to specific HTTP methods (GET only) and URL paths.
  - Use network-level controls to limit agent access to specific API endpoints.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Introduce role-based API key scoping — at minimum, support `read-only` and `full-access` key types. Consider per-resource permissions (indexer-read, search, config-read).
- **Evidence**: `src/Prowlarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/NzbDrone.Host/Startup.cs` (FallbackPolicy)

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization exists. The ASP.NET Core authorization pipeline uses a single `FallbackPolicy` that requires authentication but does not differentiate between GET, POST, PUT, and DELETE. An authenticated caller can read records AND delete them within the same resource type.
- **Gap**: No ABAC, no fine-grained RBAC, no action-level checks in middleware. An agent authenticated with the shared API key can perform any operation on any resource.
- **Compensating Controls**:
  - Reverse proxy enforcing HTTP method restrictions (allow GET only for agent traffic).
  - Agent orchestration layer that only exposes read-only tool definitions.
- **Remediation Timeline**: 60–90 days (can be combined with AUTH-Q2 remediation)
- **Recommendation**: Implement action-level authorization policies in ASP.NET Core using custom `IAuthorizationRequirement` handlers that check the caller's key type against the HTTP method.
- **Evidence**: `src/NzbDrone.Host/Startup.cs` (FallbackPolicy configuration), `src/Prowlarr.Http/Authentication/UiAuthorizationHandler.cs`

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Prowlarr has multiple logging layers: (1) `AuthenticationService` logs login/logout/unauthorized events with IP and username via NLog (`Auth` logger). (2) `LoggingMiddleware` logs every request with sequence ID, HTTP method, path, status code, duration, and origin IP+User-Agent. (3) `DatabaseTarget` writes logs to a `Logs` table in SQLite/PostgreSQL. However, logs are **not immutable** — the SQLite log database is a regular file with no write protection, and the `CleanLogCommand` and `DeleteLogFilesService` can purge logs. There is no CloudTrail, no S3 object lock, no tamper-evident storage.
- **Gap**: Logs exist but are mutable and purgeable. No immutable audit trail. No tamper-evident log storage. The `CleanseLogMessage` class scrubs secrets but cannot guarantee completeness.
- **Compensating Controls**:
  - Forward logs to an external immutable log store (e.g., CloudWatch Logs with retention policy, S3 with object lock, Loki) via syslog integration (Prowlarr supports syslog: `SyslogServer`/`SyslogPort` config).
  - Disable log purge commands for the production instance.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure syslog forwarding to an immutable external log store. Prowlarr already supports syslog configuration — enable it and point it to a centralized logging service.
- **Evidence**: `src/Prowlarr.Http/Authentication/AuthenticationService.cs`, `src/Prowlarr.Http/Middleware/LoggingMiddleware.cs`, `src/NzbDrone.Core/Instrumentation/DatabaseTarget.cs`, `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (SyslogServer, SyslogPort)

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: There is only one API key for the entire application. The only way to revoke access is to reset the API key via `ResetApiKeyCommand`, which invalidates **all** API consumers simultaneously — including connected *arr applications (Sonarr, Radarr, Lidarr) that use the same key for sync.
- **Gap**: Cannot suspend a single agent's access without disrupting all other consumers. No individual key revocation.
- **Compensating Controls**:
  - Reverse proxy with per-client allow/deny rules that can block a specific agent's traffic without touching the Prowlarr API key.
  - API gateway with per-client API key mapping that can revoke individual keys while maintaining a single upstream key.
- **Remediation Timeline**: 60–90 days (depends on AUTH-Q1 multi-key implementation)
- **Recommendation**: Implement multi-key support (AUTH-Q1) first, then add per-key enable/disable functionality.
- **Evidence**: `src/NzbDrone.Core/Configuration/ResetApiKeyCommand.cs`, `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`

#### STATE-Q1: Compensation and Rollback ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No saga pattern, no compensating transactions, and no explicit rollback logic for multi-step operations. Database operations use Dapper with `IDbTransaction` for batch inserts (`InsertMany`) but no application-level compensation for business workflows. Database migrations use FluentMigrator with forward-only migrations (no down-migration scripts found). The command queue (`CommandController`) processes commands sequentially but has no undo/compensate mechanism.
- **Gap**: If a multi-step workflow (e.g., bulk indexer update + application sync) fails partway through, there is no automatic rollback to a consistent state.
- **Compensating Controls**:
  - Limit agent scope to read-only operations (already the case with `agent_scope=read-only`).
  - For any future write-enabled agent, implement operation-level undo endpoints.
- **Remediation Timeline**: 90–180 days (significant architectural work)
- **Recommendation**: For immediate needs, the read-only agent scope avoids the worst risks. For future write-enabled scope, implement compensating actions for critical workflows.
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs` (InsertMany with transaction), `src/NzbDrone.Core/Datastore/Migration/`

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Prowlarr has Polly retry logic for SQLite busy errors (`RetryStrategy` in `BasicRepository` with exponential backoff, 3 retries). However, for external HTTP calls to indexer APIs — which are the primary runtime dependency — there are no circuit breaker patterns. `HttpIndexerBase` and `IndexerHttpClient` make HTTP calls to external indexer services without circuit breaker, timeout configuration, or bulkhead isolation. The `IndexerLimitService` tracks query/grab counts per indexer and refuses requests when limits are exceeded, providing partial protection.
- **Gap**: No circuit breaker for external indexer HTTP calls. A failing external indexer can cause cascading timeouts. `IndexerLimitService` provides rate limiting per indexer but not circuit breaking.
- **Compensating Controls**:
  - `IndexerLimitService` provides partial protection by stopping requests to indexers that exceed configured limits.
  - Monitor indexer status via `IndexerStatusService` which tracks indexer health.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add Polly circuit breaker policies to `IndexerHttpClient` for external HTTP calls. Configure timeout, retry, and circuit breaker policies per indexer.
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs` (Polly retry), `src/NzbDrone.Core/Indexers/IndexerLimitService.cs`, `src/NzbDrone.Core/Indexers/IndexerHttpClient.cs`

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No rate limiting middleware is configured in the ASP.NET Core pipeline (`Startup.cs`). No API Gateway throttling. No WAF rate rules. The application has no protection against a runaway agent sending requests at machine speed. The CORS policy allows any origin with any method. The only rate-related control is `IndexerLimitService` which limits queries/grabs per indexer based on configured thresholds — but this protects external indexers, not the Prowlarr API itself.
- **Gap**: No API-level rate limiting. An agent bug could DDoS the Prowlarr instance at machine speed.
- **Compensating Controls**:
  - Deploy a reverse proxy (nginx, Caddy, HAProxy) with rate limiting rules in front of Prowlarr.
  - Use ASP.NET Core's built-in rate limiting middleware (`Microsoft.AspNetCore.RateLimiting`) — available in .NET 8.
- **Remediation Timeline**: 7–14 days (quick win using built-in .NET 8 rate limiting)
- **Recommendation**: Add `Microsoft.AspNetCore.RateLimiting` middleware to `Startup.cs` with per-client rate limits. This is a low-effort, high-impact fix available natively in .NET 8.
- **Evidence**: `src/NzbDrone.Host/Startup.cs` (no rate limiting middleware), `src/NzbDrone.Core/Indexers/IndexerLimitService.cs`

#### DATA-Q2: Data Residency and Sovereignty ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No data residency configuration found. By default, Prowlarr uses local SQLite databases stored on the host filesystem. When configured with PostgreSQL, connection details are provided via environment variables (`Prowlarr__Postgres__Host`, etc.) with no region or jurisdiction constraints. There are no data sovereignty policies, no GDPR/LGPD compliance references, and no cross-region replication controls. The application stores indexer credentials and search history that could be subject to data protection regulations depending on the deployment context.
- **Gap**: No data residency controls. If an agent forwards data to an LLM in a different jurisdiction, there are no technical controls to prevent it.
- **Compensating Controls**:
  - Document the deployment region and ensure the agent's LLM endpoint is in the same jurisdiction.
  - For self-hosted deployments, the data stays local by default (SQLite on local disk).
- **Remediation Timeline**: 30–60 days (primarily documentation and policy)
- **Recommendation**: Document data residency requirements. For cloud-hosted PostgreSQL deployments, configure region-locked database instances and document the residency constraints.
- **Evidence**: `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs`, `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (PostgresHost, PostgresPort)

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Prowlarr has a sophisticated `CleanseLogMessage` class that scrubs API keys, tokens, passwords, tracker announce keys, and other secrets from log messages using 30+ regex patterns. It also partially redacts remote IP addresses (obfuscating middle octets for non-local IPs). However: (1) `AuthenticationService` logs IP addresses and usernames for auth events (`Auth-Success ip {0} username '{1}'`, `Auth-Failure ip {0} username '{1}'`). (2) `LoggingMiddleware` logs origin IP and User-Agent for every request. (3) The `CleanseRemoteIPRegex` only redacts IPs in specific patterns (`Auth-Success`/`Auth-Logout` patterns) — other IP logging (e.g., in `LoggingMiddleware`) is not redacted.
- **Gap**: Usernames and IP addresses appear in logs. While API keys and passwords are scrubbed, user identifiers (IP, username) are not consistently redacted. IP addresses are partially redacted only in auth-related log lines.
- **Compensating Controls**:
  - Forward logs to a system with field-level access controls that restricts who can view IP/username fields.
  - Extend `CleanseLogMessage` to optionally redact username and IP fields.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Extend `CleanseLogMessage` to cover username redaction. Apply IP redaction consistently across all log sources, not just auth events.
- **Evidence**: `src/NzbDrone.Common/Instrumentation/CleanseLogMessage.cs`, `src/Prowlarr.Http/Authentication/AuthenticationService.cs`, `src/Prowlarr.Http/Middleware/LoggingMiddleware.cs`

---

### RISK-QUALITY — Address as Capacity Allows

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Prowlarr has a structured error pipeline (`ProwlarrErrorPipeline`) that returns JSON error responses with `Message`, `Description`, and `Content` fields via `ErrorModel`. Different exception types map to appropriate HTTP status codes (400 for validation, 404 for not found, 409 for conflict, 500 for unhandled). `ValidationException` returns detailed field-level errors. However, there is no `retryable` boolean or error classification that distinguishes retriable errors from terminal errors.
- **Gap**: No machine-readable retryability indicator in error responses. An agent receiving a 500 cannot distinguish a transient failure (retry) from a persistent bug (do not retry).
- **Compensating Controls**:
  - Agent orchestration layer can implement retry logic based on HTTP status codes (retry 500/503, do not retry 400/404/409).
- **Remediation Timeline**: 7–14 days
- **Recommendation**: Add a `retryable` boolean or `errorCategory` enum (transient/permanent/rate-limited) to `ErrorModel`.
- **Evidence**: `src/Prowlarr.Http/ErrorManagement/ProwlarrErrorPipeline.cs`, `src/Prowlarr.Http/ErrorManagement/ErrorModel.cs`

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No separate staging or sandbox environment configuration found. The application has no environment-specific configuration profiles, no Docker Compose for local testing, no seed data scripts, and no synthetic data generators. As a desktop/self-hosted application, testing typically happens against a live instance.
- **Gap**: No staging environment to test agent behavior before production. First-time agent testing would be against a live Prowlarr instance with real indexer configurations.
- **Compensating Controls**:
  - Stand up a separate Prowlarr instance with test indexer configurations for agent testing.
  - Use a Docker container (community-maintained) as an isolated test environment.
- **Remediation Timeline**: 7–14 days
- **Recommendation**: Create a docker-compose development environment with seed data for agent testing.
- **Evidence**: No staging configuration files found in repository.

#### DATA-Q4: System of Record Designations — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No system-of-record designations found. Prowlarr manages indexer configurations, but there are no formal SoR declarations for entities like indexers, applications, or download clients. When connected *arr applications sync indexer settings, there is no documented master-data ownership model.
- **Gap**: No SoR designations. Agents reasoning across Prowlarr and connected *arr apps could encounter conflicting indexer configurations.
- **Compensating Controls**:
  - Document Prowlarr as the SoR for indexer configurations and connected *arr apps as consumers.
- **Remediation Timeline**: 14–30 days (documentation)
- **Recommendation**: Document entity ownership model: Prowlarr owns indexer definitions; *arr apps own their sync settings.
- **Evidence**: No SoR documentation found.

#### DATA-Q5: Temporal Metadata and Freshness — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The `History` model includes a `Date` field. Database timestamps use UTC via `DapperUtcConverter`. `ScheduledTasks` track `LastExecution` and `LastStartTime`. However, there are no freshness indicators in API responses — no `Cache-Control` headers, no `X-Data-Age` headers, no `last_refreshed` fields, and no `consistency_level` signaling. API responses do not indicate whether data is current, cached, or stale.
- **Gap**: No API-level freshness signaling. An agent cannot determine if indexer status data is current or stale.
- **Compensating Controls**:
  - Agent can check `History` endpoint timestamps to infer data freshness.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add `Last-Modified` or custom `X-Data-Age` response headers to entity endpoints. Include `lastUpdated` fields in resource representations.
- **Evidence**: `src/NzbDrone.Core/History/History.cs` (Date field), `src/NzbDrone.Core/Datastore/Converters/`

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The API is versioned at `/api/v1/` via `VersionedApiControllerAttribute`. The OpenAPI spec (`openapi.json`) is auto-generated from code annotations via Swashbuckle and is committed to the repository. Database schema is versioned via FluentMigrator migrations (001 through 043). However, there is no breaking change detection in CI — no `buf breaking`, no OpenAPI diff tools, no consumer-driven contract tests (Pact). The Azure Pipelines `Api_Docs` job regenerates `openapi.json` and auto-commits it, but does not validate backward compatibility.
- **Gap**: No automated breaking change detection in CI pipeline. API schema changes could silently break agent tool bindings.
- **Compensating Controls**:
  - Pin agent tool definitions to specific OpenAPI spec versions and manually validate on updates.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add an OpenAPI diff step to the CI pipeline that fails on breaking changes (e.g., `oasdiff` or `optic`).
- **Evidence**: `src/Prowlarr.Api.V1/openapi.json`, `src/Prowlarr.Http/VersionedApiControllerAttribute.cs`, `azure-pipelines.yml` (Api_Docs job), `src/NzbDrone.Core/Datastore/Migration/`

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Prowlarr uses NLog for logging with multiple targets: console, file, database (`DatabaseTarget`), and optional syslog. `LoggingMiddleware` assigns a sequential `ApiRequestSequenceID` to each request and logs method, path, status code, and duration — providing request correlation within a single instance. However, there is no distributed tracing (no OpenTelemetry, no X-Ray, no `traceparent` header propagation). Logs are structured to the NLog layout but not in JSON format by default (configurable via `ConsoleLogFormat`). The sequence ID is an incrementing integer, not a trace ID that propagates across services.
- **Gap**: No distributed tracing. No trace ID propagation. Request sequence IDs are instance-local and non-propagatable. Logs are not JSON-structured by default.
- **Compensating Controls**:
  - The `ApiRequestSequenceID` provides basic per-instance correlation.
  - Configure `ConsoleLogFormat` to structured/JSON output.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenTelemetry instrumentation to the ASP.NET Core pipeline. This is well-supported in .NET 8 via `Microsoft.Extensions.Telemetry`.
- **Evidence**: `src/Prowlarr.Http/Middleware/LoggingMiddleware.cs`, `src/NzbDrone.Core/Instrumentation/DatabaseTarget.cs`, `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (ConsoleLogFormat)

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No alerting configuration found. Sentry integration exists for error reporting (`ReconfigureSentry.cs`, Sentry source map uploads in Azure Pipelines), but there are no alerting thresholds for error rates or latency. No CloudWatch alarms, no PagerDuty/OpsGenie integration, no anomaly detection. Health checks exist (`src/NzbDrone.Core/HealthCheck/`) but these are internal status checks, not external alerting.
- **Gap**: No external alerting for API error rates or latency degradation. Sentry captures errors but does not alert on rate-based thresholds.
- **Compensating Controls**:
  - Configure Sentry alert rules for error rate spikes.
  - Use external monitoring (Uptime Kuma, Grafana) against the Prowlarr health endpoint.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Configure Sentry alert rules for error rate thresholds. Add health check endpoint monitoring via external tools.
- **Evidence**: `src/NzbDrone.Core/Instrumentation/ReconfigureSentry.cs`, `azure-pipelines.yml` (Sentry integration), `src/NzbDrone.Core/HealthCheck/`

#### ENG-Q1: Infrastructure Governance — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No Infrastructure as Code found in the repository. Prowlarr is a self-hosted desktop/server application distributed as binary packages (zip, tar.gz, installers) via Azure Pipelines. There are no Terraform, CloudFormation, CDK, Helm, or Kustomize files. The `distribution/` directory contains only Windows installer scripts (InnoSetup). Deployment is end-user managed with no standardized IaC.
- **Gap**: No IaC for the agent-facing surface. Deployment configuration is manual and user-specific.
- **Compensating Controls**:
  - Community-maintained Docker images and Helm charts exist outside this repository.
  - Document recommended deployment configuration for agent integration.
- **Remediation Timeline**: 30–60 days (if providing official container/IaC support)
- **Recommendation**: Provide an official Dockerfile and docker-compose.yml for standardized deployment. Consider publishing a Helm chart for Kubernetes deployments.
- **Evidence**: `distribution/` directory (Windows installer only), no IaC files found.

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive CI/CD exists via Azure Pipelines: multi-platform builds (Linux, Mac, Windows), unit tests, integration tests (with SQLite and PostgreSQL 14/15), automation tests, code coverage via SonarCloud, and frontend linting. However, no API contract testing exists — no Pact, no OpenAPI validation in CI, no schema comparison tools. The `Api_Docs` job regenerates the OpenAPI spec but does not validate backward compatibility. Integration tests in `NzbDrone.Integration.Test/ApiTests/` test API endpoints functionally but do not perform contract-level validation.
- **Gap**: No API contract testing in CI. Breaking API changes are not caught before deployment.
- **Compensating Controls**:
  - Existing integration tests provide functional API coverage.
  - Manual OpenAPI spec review on PRs.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add an OpenAPI diff step to the CI pipeline that compares the generated spec against the committed version and fails on breaking changes.
- **Evidence**: `azure-pipelines.yml`, `src/NzbDrone.Integration.Test/ApiTests/`, `src/Prowlarr.Api.V1/openapi.json`

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Prowlarr is distributed as self-contained binary packages. The `NzbDrone.Update` project handles application updates with an auto-update mechanism, but there is no built-in rollback capability. Database migrations are forward-only (FluentMigrator, no down-migration scripts). Users must manually restore from backup to revert. There is no blue/green deployment, no canary deployment, no CodeDeploy integration.
- **Gap**: No automated rollback. Database migrations are not reversible. Recovery requires manual backup restoration.
- **Compensating Controls**:
  - Prowlarr creates automatic backups (`src/NzbDrone.Core/Backup/`) that can be restored manually.
  - Pin agent tool definitions to specific API versions to reduce sensitivity to updates.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement down-migration scripts for critical schema changes. For containerized deployments, use image version pinning with rollback capability.
- **Evidence**: `src/NzbDrone.Update/`, `src/NzbDrone.Core/Datastore/Migration/`, `src/NzbDrone.Core/Backup/`

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Integration tests exist in `NzbDrone.Integration.Test/ApiTests/` covering commands, file system, history, indexers, notifications, and releases. The `Prowlarr.Api.V1.Test` project provides unit-level API tests. SonarCloud code coverage analysis runs in CI. However, there are no dedicated API contract tests, no Postman/Newman collections, and no systematic validation of input handling, error responses, and edge cases for all API endpoints.
- **Gap**: API test coverage exists but is not comprehensive for contract validation. No systematic coverage of error responses and edge cases across all endpoints.
- **Compensating Controls**:
  - Existing integration and automation tests provide baseline coverage.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add API contract test suites (Postman/Newman or REST-assured equivalent) that validate all endpoint input/output contracts.
- **Evidence**: `src/NzbDrone.Integration.Test/ApiTests/`, `src/Prowlarr.Api.V1.Test/`, `azure-pipelines.yml` (test stages)

#### ENG-Q5: Encryption at Rest — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: SQLite databases are stored as plain files on the local filesystem with no encryption. PostgreSQL connections do not enforce SSL/TLS (no `SslMode` parameter in `NpgsqlConnectionStringBuilder`). No KMS integration, no customer-managed encryption keys, no `aws_kms_key` references. The `Users` table stores password hashes (not plaintext), but indexer API keys and download client credentials in `Settings` JSON columns are stored unencrypted.
- **Gap**: Data at rest is not encrypted. Sensitive credentials in the database (indexer API keys, download client tokens) are stored in plaintext JSON.
- **Compensating Controls**:
  - Use full-disk encryption (LUKS, BitLocker, FileVault) on the host where Prowlarr runs.
  - For PostgreSQL, configure TDE or use an encrypted RDS instance.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Encrypt sensitive fields in the `Settings` JSON column using application-level encryption. For PostgreSQL, enforce SSL connections.
- **Evidence**: `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` (no SSL parameters), `src/NzbDrone.Core/Authentication/User.cs` (hashed passwords), `src/NzbDrone.Core/Indexers/IndexerDefinition.cs` (plaintext Settings)

#### AUTH-Q4: Identity Propagation and Delegation — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No identity propagation mechanisms exist. No JWT parsing, no OAuth2 on-behalf-of flows, no token exchange patterns. Prowlarr is a single-user/single-instance desktop-style application — it does not distinguish between an agent acting under its own identity vs. acting on behalf of a user. All API consumers are treated identically via the shared API key.
- **Gap**: No identity propagation. No user context headers. No separate auth flows for service-to-service vs. user-delegated calls.
- **Compensating Controls**:
  - For read-only agent scope, identity propagation is less critical as no data modification occurs.
  - Agent orchestration layer can maintain its own identity context.
- **Remediation Timeline**: 90+ days (requires fundamental auth architecture changes)
- **Recommendation**: For the current read-only scope, this is acceptable. For future multi-tenant or delegated access, implement JWT/OAuth2 support.
- **Evidence**: `src/Prowlarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/Prowlarr.Http/Authentication/AuthenticationBuilderExtensions.cs`

#### AUTH-Q5: Credential Management — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The Prowlarr API key is stored in `config.xml` on the local filesystem — a plain XML file. PostgreSQL credentials are read from environment variables (`Prowlarr__Postgres__Password`). No secrets management system (AWS Secrets Manager, HashiCorp Vault) is used. No credential rotation mechanism exists (the API key is generated once at startup and persists until manually reset). `CleanseLogMessage` scrubs credentials from log output, providing some protection against log leakage.
- **Gap**: Credentials stored in plaintext XML and environment variables. No secrets manager. No automatic rotation. No integration with external credential stores.
- **Compensating Controls**:
  - `CleanseLogMessage` scrubs credentials from log output.
  - File system permissions can restrict access to `config.xml`.
  - Environment variables are standard for container deployments.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: For containerized deployments, consider supporting mounted secret files or external secret store references. Document best practices for securing `config.xml`.
- **Evidence**: `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (ApiKey, PostgresPassword), `src/NzbDrone.Common/Instrumentation/CleanseLogMessage.cs`

---

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO
- **Finding**: Prowlarr exposes a well-documented REST API via ASP.NET Core controllers in `Prowlarr.Api.V1/`. The API is versioned at `/api/v1/` and includes controllers for indexers, search, applications, commands, history, notifications, download clients, tags, health, system, and configuration. No direct database access patterns, no file-based exchange, no UI automation. The API is the primary integration surface.
- **Implication**: The API is suitable for agent tool binding. No integration workarounds needed.
- **Recommendation**: No action required.
- **Evidence**: `src/Prowlarr.Api.V1/` (all controllers), `src/Prowlarr.Api.V1/openapi.json`

### API-Q2: Machine-Readable API Specification

- **Severity**: INFO
- **Finding**: An OpenAPI 3.0.4 specification exists at `src/Prowlarr.Api.V1/openapi.json` (141.95 KB, 6356 lines). It is auto-generated from code annotations via Swashbuckle (`AddSwaggerGen` in `Startup.cs`) and committed to the repository. The spec includes security definitions for API key auth (header and query parameter), server variable templates, and comprehensive endpoint/schema definitions.
- **Implication**: Agent tool definitions can be auto-generated from this spec. No manual tool authoring needed.
- **Recommendation**: Ensure the spec is regenerated and committed on every API change (already done via the `Api_Docs` CI job).
- **Evidence**: `src/Prowlarr.Api.V1/openapi.json`, `src/NzbDrone.Host/Startup.cs` (Swashbuckle config)

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Write endpoints (POST for create, PUT for update, DELETE for remove) do not implement idempotency keys. The `RestController` does not enforce idempotency middleware. However, with `agent_scope=read-only`, idempotency of write operations is informational only.
- **Implication**: If agent scope expands to write-enabled, idempotency must be addressed.
- **Recommendation**: No immediate action for read-only scope. Plan for idempotency key support if write scope is planned.
- **Evidence**: `src/Prowlarr.Http/REST/RestController.cs`

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: All API responses are JSON, serialized via `System.Text.Json` with custom settings (`STJson.ApplySerializerSettings`). The `Produces("application/json")` attribute is used on controller actions. No XML, binary, or protobuf formats.
- **Implication**: JSON is ideal for LLM consumption. No format conversion needed.
- **Recommendation**: No action required.
- **Evidence**: `src/NzbDrone.Host/Startup.cs` (AddJsonOptions), `src/Prowlarr.Api.V1/Search/SearchController.cs`

### API-Q6: Asynchronous Operation Support

- **Severity**: INFO
- **Finding**: Prowlarr implements an asynchronous command queue pattern via `CommandController`. Commands are submitted via POST, return immediately with a `CommandResource` (including status tracking), and can be polled via GET. Commands support `Queued`, `Started`, and `Ended` timestamps with `Duration` tracking. SignalR broadcasts real-time status updates for commands. Indexer searches are inherently async (external HTTP calls to indexer APIs).
- **Implication**: Long-running operations (indexer searches, bulk operations) have a proper async pattern. Agents can submit commands and poll for completion or receive SignalR updates.
- **Recommendation**: Document the command queue pattern for agent tool definitions.
- **Evidence**: `src/Prowlarr.Api.V1/Commands/CommandController.cs`, `src/Prowlarr.Api.V1/Commands/CommandResource.cs`

### API-Q7: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: Prowlarr emits real-time events via SignalR (`/signalr/messages` hub). `RestControllerWithSignalR` broadcasts `ModelEvent` changes (Created, Updated, Deleted, Sync) for all entity types. The `BroadcastResourceChange` method sends structured `SignalRMessage` objects with resource name, body, and action type. This enables reactive agent patterns.
- **Implication**: Agents can subscribe to SignalR for real-time state change notifications instead of polling.
- **Recommendation**: Document the SignalR event schema for agent consumption.
- **Evidence**: `src/Prowlarr.Http/REST/RestControllerWithSignalR.cs`, `src/NzbDrone.SignalR/`

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limit headers (`X-RateLimit-Remaining`, `Retry-After`) are returned in API responses. No rate limit documentation exists. The `IndexerLimitService` tracks per-indexer query/grab limits but this information is not exposed via API headers to the caller.
- **Implication**: Agents cannot self-throttle based on API-communicated limits. Must rely on external rate limiting.
- **Recommendation**: Expose rate limit information via standard headers if rate limiting middleware is added (STATE-Q5).
- **Evidence**: `src/NzbDrone.Host/Startup.cs`, `src/NzbDrone.Core/Indexers/IndexerLimitService.cs`

### STATE-Q2: Queryable Current State

- **Severity**: INFO
- **Finding**: All entity types have GET endpoints returning current state. `RestController` requires `GetResourceById(int id)` implementation. List endpoints return all resources. History endpoint provides paginated query results with filters and sorting. Indexer status is queryable via `IndexerStatusController`. System status is available at `/api/v1/system/status`.
- **Implication**: Agents can read current state before deciding next steps. No external state synchronization needed.
- **Recommendation**: No action required.
- **Evidence**: `src/Prowlarr.Http/REST/RestController.cs`, `src/Prowlarr.Api.V1/Indexers/IndexerStatusController.cs`

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No optimistic locking (version fields, ETags, `If-Match` headers) found. SQLite uses WAL mode with `BusyTimeout=1000ms` and Polly retry for busy errors. No `SELECT FOR UPDATE` patterns. No DynamoDB conditional writes (not applicable — uses SQLite/PostgreSQL). For read-only agent scope, concurrency controls for write operations are not needed.
- **Implication**: If agent scope expands to write-enabled, concurrent write safety must be addressed.
- **Recommendation**: No immediate action for read-only scope.
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs`, `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs`

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits found. No `max_records_per_operation`, no `max_spend_per_session`, no per-agent operational limits. For read-only agent scope, transaction limits for write operations are informational only.
- **Implication**: If agent scope expands to write-enabled, blast radius controls must be added.
- **Recommendation**: No immediate action for read-only scope.
- **Evidence**: No transaction limit configuration found.

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No draft/pending state pattern found. Entities go from creation directly to active state. No approval workflows. No two-step commit patterns.
- **Implication**: Not needed for read-only scope. Relevant for future write-enabled scope.
- **Recommendation**: No immediate action.
- **Evidence**: No draft state patterns found in source code.

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable approval gates found. No approval API endpoints. No `waitForTaskToken` patterns.
- **Implication**: Not needed for read-only scope.
- **Recommendation**: No immediate action.
- **Evidence**: No approval workflow code found.

### DATA-Q3: Selective Query Support

- **Severity**: INFO
- **Finding**: Prowlarr implements comprehensive pagination via `PagingResource` with `Page`, `PageSize`, `SortKey`, and `SortDirection` parameters. The `SearchController` supports `Limit` and `Offset` parameters. `PagingSpec` enforces page-based queries with configurable sort keys validated against an allowlist. Default page size is 10.
- **Implication**: Agents can retrieve bounded result sets. No risk of exhausting LLM context windows with unbounded queries.
- **Recommendation**: No action required.
- **Evidence**: `src/Prowlarr.Http/PagingResource.cs`, `src/NzbDrone.Core/Datastore/PagingSpec.cs`, `src/Prowlarr.Api.V1/Search/SearchController.cs`

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality metrics, no data profiling, no null rate monitoring, no duplicate detection, no data freshness SLAs.
- **Implication**: Agent must treat all data as best-effort. Plan for data quality monitoring as agent adoption grows.
- **Recommendation**: Consider adding data quality health checks (e.g., orphaned indexer references, stale status records).
- **Evidence**: No data quality tooling found.

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: API resource field names are generally descriptive and camelCase (`indexerId`, `downloadUrl`, `magnetUrl`, `publishDate`, `seeders`, `leechers`). Some legacy naming from the NzbDrone codebase persists in internal code (e.g., `NzbDrone.Core` namespace), but API-facing resources use clean, descriptive names. The OpenAPI spec provides schema definitions with clear type information.
- **Implication**: Field names are LLM-interpretable without a data dictionary.
- **Recommendation**: No action required.
- **Evidence**: `src/Prowlarr.Api.V1/openapi.json`, `src/Prowlarr.Api.V1/Search/ReleaseResource.cs`

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No data catalog, no metadata layer, no Glue Data Catalog, no schema documentation beyond the OpenAPI spec itself.
- **Implication**: The OpenAPI spec serves as the primary metadata source for agent tool definitions.
- **Recommendation**: Consider documenting entity relationships and data semantics in a developer guide.
- **Evidence**: No data catalog found.

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No custom business metrics published. No `PutMetricData` equivalents. The `IndexerStats` endpoint provides query/grab counts per indexer, which could serve as proxy business metrics, but these are not published as telemetry.
- **Implication**: No business-outcome visibility for agent interactions. Monitoring is limited to infrastructure metrics.
- **Recommendation**: Consider publishing indexer query success rates and search latency as custom metrics.
- **Evidence**: `src/Prowlarr.Api.V1/Indexers/IndexerStatsController.cs`

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: Prowlarr exposes a documented REST API via ASP.NET Core controllers in `Prowlarr.Api.V1/` with versioned endpoints at `/api/v1/`. Controllers cover indexers, search, applications, commands, history, notifications, download clients, tags, health, system, and configuration. OpenAPI spec auto-generated via Swashbuckle.
- **Gap**: None — documented API exists.
- **Recommendation**: No action required.
- **Evidence**: `src/Prowlarr.Api.V1/`, `src/Prowlarr.Api.V1/openapi.json`

#### API-Q2: Machine-Readable API Specification
- **Severity**: INFO
- **Finding**: OpenAPI 3.0.4 specification at `src/Prowlarr.Api.V1/openapi.json` (141.95 KB). Auto-generated from code via Swashbuckle and committed to repository. CI pipeline regenerates and auto-commits updates.
- **Gap**: None — machine-readable spec exists and is kept current.
- **Recommendation**: No action required.
- **Evidence**: `src/Prowlarr.Api.V1/openapi.json`, `azure-pipelines.yml` (Api_Docs job)

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: `ProwlarrErrorPipeline` returns JSON error responses with `Message`, `Description`, `Content` fields. HTTP status codes mapped per exception type (400/404/409/500). Missing retryable indicator.
- **Gap**: No machine-readable retryability classification in error responses.
- **Recommendation**: Add `retryable` boolean to `ErrorModel`.
- **Evidence**: `src/Prowlarr.Http/ErrorManagement/ProwlarrErrorPipeline.cs`, `src/Prowlarr.Http/ErrorManagement/ErrorModel.cs`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No idempotency key support on write endpoints. Not relevant for read-only agent scope.
- **Gap**: No idempotency keys (informational for read-only scope).
- **Recommendation**: Plan for idempotency if write scope is planned.
- **Evidence**: `src/Prowlarr.Http/REST/RestController.cs`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: All responses JSON via `System.Text.Json`. `Produces("application/json")` on controllers.
- **Gap**: None.
- **Recommendation**: No action required.
- **Evidence**: `src/NzbDrone.Host/Startup.cs`

#### API-Q6: Asynchronous Operation Support
- **Severity**: INFO
- **Finding**: Command queue pattern with status tracking. Commands submitted via POST, polled via GET, real-time updates via SignalR. Supports `Queued`/`Started`/`Ended` lifecycle.
- **Gap**: None — async pattern exists.
- **Recommendation**: Document command queue for agent tool definitions.
- **Evidence**: `src/Prowlarr.Api.V1/Commands/CommandController.cs`

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: SignalR hub at `/signalr/messages` broadcasts Created/Updated/Deleted/Sync events for all entity types via `RestControllerWithSignalR`.
- **Gap**: None — event emission exists.
- **Recommendation**: Document SignalR event schema for agents.
- **Evidence**: `src/Prowlarr.Http/REST/RestControllerWithSignalR.cs`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No `X-RateLimit-Remaining` or `Retry-After` headers. Per-indexer limits tracked by `IndexerLimitService` but not exposed via API headers.
- **Gap**: No rate limit headers in responses.
- **Recommendation**: Add rate limit headers if middleware is added.
- **Evidence**: `src/NzbDrone.Host/Startup.cs`, `src/NzbDrone.Core/Indexers/IndexerLimitService.cs`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: Single shared API key via `X-Api-Key` header or `apikey` query parameter. No per-agent attribution. `ClaimsPrincipal` contains only generic `ApiKey=true` claim.
- **Gap**: No per-agent identity. Cannot attribute API calls to specific agent instances.
- **Recommendation**: Implement multiple named API keys with principal attribution.
- **Evidence**: `src/Prowlarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: Single authentication tier — API key grants unrestricted access to all endpoints. No RBAC.
- **Gap**: Cannot scope agent to read-only access.
- **Recommendation**: Introduce role-based API key scoping.
- **Evidence**: `src/Prowlarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization. `FallbackPolicy` requires authentication only, not specific method permissions.
- **Gap**: No ABAC, no method-level authorization.
- **Recommendation**: Implement authorization policies per HTTP method.
- **Evidence**: `src/NzbDrone.Host/Startup.cs`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: RISK-QUALITY
- **Finding**: No JWT, no OAuth2, no on-behalf-of flows. Single-user desktop app pattern.
- **Gap**: No identity propagation through service calls.
- **Recommendation**: Accept for read-only scope; plan JWT/OAuth2 for future multi-tenant access.
- **Evidence**: `src/Prowlarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`

#### AUTH-Q5: Credential Management
- **Severity**: RISK-QUALITY
- **Finding**: API key in `config.xml`. PostgreSQL credentials in environment variables. No secrets manager. No rotation.
- **Gap**: Plaintext credential storage. No rotation mechanism.
- **Recommendation**: Support external secret store references for containerized deployments.
- **Evidence**: `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Auth events logged with IP and username. Database log target writes to SQLite/PostgreSQL. Logs are mutable and purgeable. Syslog forwarding supported but not configured by default.
- **Gap**: No immutable audit trail. Logs can be purged.
- **Recommendation**: Enable syslog forwarding to an immutable external store.
- **Evidence**: `src/Prowlarr.Http/Authentication/AuthenticationService.cs`, `src/NzbDrone.Core/Instrumentation/DatabaseTarget.cs`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: Single shared API key. Only revocation mechanism (`ResetApiKeyCommand`) invalidates all consumers.
- **Gap**: Cannot suspend individual agent access.
- **Recommendation**: Implement multi-key support with per-key disable functionality.
- **Evidence**: `src/NzbDrone.Core/Configuration/ResetApiKeyCommand.cs`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No saga pattern, no compensating transactions. Forward-only database migrations. `InsertMany` uses transactions but no application-level rollback.
- **Gap**: No multi-step rollback capability.
- **Recommendation**: Read-only scope mitigates. Plan compensation for write scope.
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs`

#### STATE-Q2: Queryable Current State
- **Severity**: INFO
- **Finding**: GET endpoints for all entity types. History with pagination. System status endpoint.
- **Gap**: None.
- **Recommendation**: No action required.
- **Evidence**: `src/Prowlarr.Http/REST/RestController.cs`

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No optimistic locking. SQLite WAL mode with Polly retry. Informational for read-only scope.
- **Gap**: No concurrency controls (informational).
- **Recommendation**: No immediate action.
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: Polly retry for SQLite busy errors. No circuit breakers for external indexer HTTP calls. `IndexerLimitService` provides query/grab limits per indexer.
- **Gap**: No circuit breaker for external HTTP dependencies.
- **Recommendation**: Add Polly circuit breaker to `IndexerHttpClient`.
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs`, `src/NzbDrone.Core/Indexers/IndexerLimitService.cs`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No API-level rate limiting middleware. CORS allows any origin with any method.
- **Gap**: No rate limiting on the Prowlarr API itself.
- **Recommendation**: Add .NET 8 `Microsoft.AspNetCore.RateLimiting` middleware.
- **Evidence**: `src/NzbDrone.Host/Startup.cs`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits. Informational for read-only scope.
- **Gap**: No transaction limits (informational).
- **Recommendation**: No immediate action.
- **Evidence**: N/A

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path. This service is P2 priority and not on critical path.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No draft/pending state pattern. Entities are immediately active on creation.
- **Gap**: No draft states (informational for read-only).
- **Recommendation**: No immediate action.
- **Evidence**: No draft patterns found.

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No approval workflows or configurable gates.
- **Gap**: No approval gates (informational for read-only).
- **Recommendation**: No immediate action.
- **Evidence**: No approval workflow code found.

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: No staging environment configuration. No Docker Compose for local testing. No seed data scripts.
- **Gap**: No safe environment for agent testing.
- **Recommendation**: Create docker-compose environment with seed data.
- **Evidence**: No staging configuration found.

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: Stores user credentials (hashed passwords, salts), indexer API keys/cookies, download client credentials, application sync API keys. No field-level classification or access controls.
- **Gap**: Sensitive data not classified, tagged, or protected at the field level.
- **Recommendation**: Implement field-level redaction for credential fields in API responses.
- **Evidence**: `src/NzbDrone.Core/Authentication/User.cs`, `src/NzbDrone.Core/Indexers/IndexerDefinition.cs`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No data residency configuration. Local SQLite by default. PostgreSQL via environment variables with no region constraints.
- **Gap**: No data residency controls.
- **Recommendation**: Document residency requirements and deployment constraints.
- **Evidence**: `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs`

#### DATA-Q3: Selective Query Support
- **Severity**: INFO
- **Finding**: Pagination via `PagingResource` with page/pageSize/sortKey/sortDirection. Search supports limit/offset.
- **Gap**: None — bounded queries supported.
- **Recommendation**: No action required.
- **Evidence**: `src/Prowlarr.Http/PagingResource.cs`

#### DATA-Q4: System of Record Designations
- **Severity**: RISK-QUALITY
- **Finding**: No SoR designations. No master data management documentation.
- **Gap**: No formal entity ownership model.
- **Recommendation**: Document Prowlarr as SoR for indexer configurations.
- **Evidence**: No SoR documentation found.

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK-QUALITY
- **Finding**: History has `Date` field. UTC conversion via DapperUtcConverter. No API-level freshness headers.
- **Gap**: No freshness signaling in API responses.
- **Recommendation**: Add `Last-Modified` or `X-Data-Age` headers.
- **Evidence**: `src/NzbDrone.Core/History/History.cs`

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: `CleanseLogMessage` scrubs secrets (30+ patterns). IP partially redacted for remote addresses. Auth logger logs IP and username.
- **Gap**: Usernames and IPs not consistently redacted across all log sources.
- **Recommendation**: Extend `CleanseLogMessage` for username and consistent IP redaction.
- **Evidence**: `src/NzbDrone.Common/Instrumentation/CleanseLogMessage.cs`, `src/Prowlarr.Http/Authentication/AuthenticationService.cs`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics or profiling.
- **Gap**: None (INFO-level).
- **Recommendation**: Consider data quality health checks.
- **Evidence**: No data quality tooling found.

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: API versioned at `/api/v1/`. OpenAPI spec auto-generated. Database migrations versioned (001–043). No breaking change detection in CI.
- **Gap**: No automated breaking change detection.
- **Recommendation**: Add OpenAPI diff step to CI pipeline.
- **Evidence**: `src/Prowlarr.Api.V1/openapi.json`, `azure-pipelines.yml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: API fields are descriptive camelCase. Legacy NzbDrone naming in internal code only.
- **Gap**: None.
- **Recommendation**: No action required.
- **Evidence**: `src/Prowlarr.Api.V1/openapi.json`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No data catalog. OpenAPI spec is the primary metadata source.
- **Gap**: None (INFO-level).
- **Recommendation**: Consider entity relationship documentation.
- **Evidence**: No data catalog found.

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: NLog logging with per-request sequence IDs. No OpenTelemetry, no trace ID propagation, no JSON-structured logs by default.
- **Gap**: No distributed tracing. No propagatable trace IDs.
- **Recommendation**: Add OpenTelemetry instrumentation.
- **Evidence**: `src/Prowlarr.Http/Middleware/LoggingMiddleware.cs`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: Sentry integration for error reporting. No alerting thresholds. No external monitoring.
- **Gap**: No alerting for API error rates or latency.
- **Recommendation**: Configure Sentry alert rules and external monitoring.
- **Evidence**: `src/NzbDrone.Core/Instrumentation/ReconfigureSentry.cs`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics. `IndexerStats` endpoint provides proxy metrics.
- **Gap**: None (INFO-level).
- **Recommendation**: Consider publishing indexer success rates as metrics.
- **Evidence**: `src/Prowlarr.Api.V1/Indexers/IndexerStatsController.cs`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance
- **Severity**: RISK-QUALITY
- **Finding**: No IaC in repository. Desktop app distributed as binary packages. No Terraform/CloudFormation/CDK/Helm.
- **Gap**: No IaC for agent-facing surface.
- **Recommendation**: Provide official Dockerfile and docker-compose.yml.
- **Evidence**: `distribution/` (Windows installer only)

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: Azure Pipelines with multi-platform builds, unit/integration/automation tests, SonarCloud. No API contract testing (no Pact, no OpenAPI diff).
- **Gap**: No API contract testing in CI.
- **Recommendation**: Add OpenAPI diff step to CI.
- **Evidence**: `azure-pipelines.yml`, `src/NzbDrone.Integration.Test/ApiTests/`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: Binary distribution with auto-updater. Forward-only database migrations. Manual backup restoration for rollback.
- **Gap**: No automated rollback capability.
- **Recommendation**: Implement down-migration scripts. Use image version pinning for containers.
- **Evidence**: `src/NzbDrone.Update/`, `src/NzbDrone.Core/Backup/`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: Integration tests in `ApiTests/` covering major endpoints. `Prowlarr.Api.V1.Test` for unit tests. SonarCloud coverage. No dedicated contract tests.
- **Gap**: No systematic contract validation across all endpoints.
- **Recommendation**: Add contract test suites for all agent-facing endpoints.
- **Evidence**: `src/NzbDrone.Integration.Test/ApiTests/`, `src/Prowlarr.Api.V1.Test/`

#### ENG-Q5: Encryption at Rest
- **Severity**: RISK-QUALITY
- **Finding**: SQLite files unencrypted. PostgreSQL connections without SSL enforcement. Passwords hashed but indexer API keys stored as plaintext JSON.
- **Gap**: No encryption at rest for sensitive data.
- **Recommendation**: Encrypt sensitive Settings fields. Enforce PostgreSQL SSL.
- **Evidence**: `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs`

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `src/Prowlarr.Http/Authentication/ApiKeyAuthenticationHandler.cs` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4 |
| `src/Prowlarr.Http/Authentication/AuthenticationService.cs` | AUTH-Q6, DATA-Q6 |
| `src/Prowlarr.Http/Authentication/AuthenticationBuilderExtensions.cs` | AUTH-Q4 |
| `src/Prowlarr.Http/Authentication/UiAuthorizationHandler.cs` | AUTH-Q3 |
| `src/Prowlarr.Http/ErrorManagement/ProwlarrErrorPipeline.cs` | API-Q3 |
| `src/Prowlarr.Http/ErrorManagement/ErrorModel.cs` | API-Q3 |
| `src/Prowlarr.Http/REST/RestController.cs` | API-Q4, STATE-Q2 |
| `src/Prowlarr.Http/REST/RestControllerWithSignalR.cs` | API-Q7 |
| `src/Prowlarr.Http/PagingResource.cs` | DATA-Q3 |
| `src/Prowlarr.Http/Middleware/LoggingMiddleware.cs` | AUTH-Q6, OBS-Q1, DATA-Q6 |
| `src/Prowlarr.Http/VersionedApiControllerAttribute.cs` | DISC-Q1 |
| `src/NzbDrone.Host/Startup.cs` | API-Q2, API-Q5, AUTH-Q3, STATE-Q5, API-Q8 |
| `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` | AUTH-Q1, AUTH-Q5, AUTH-Q6, AUTH-Q7, DATA-Q2, OBS-Q1 |
| `src/NzbDrone.Core/Configuration/ResetApiKeyCommand.cs` | AUTH-Q7 |
| `src/NzbDrone.Core/Authentication/User.cs` | DATA-Q1 |
| `src/NzbDrone.Core/Datastore/BasicRepository.cs` | STATE-Q1, STATE-Q3, STATE-Q4 |
| `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` | DATA-Q2, STATE-Q3, ENG-Q5 |
| `src/NzbDrone.Core/Datastore/PagingSpec.cs` | DATA-Q3 |
| `src/NzbDrone.Core/Indexers/IndexerLimitService.cs` | STATE-Q4, STATE-Q5, API-Q8 |
| `src/NzbDrone.Core/Indexers/IndexerHttpClient.cs` | STATE-Q4 |
| `src/NzbDrone.Core/Indexers/IndexerDefinition.cs` | DATA-Q1, ENG-Q5 |
| `src/NzbDrone.Core/Instrumentation/DatabaseTarget.cs` | AUTH-Q6 |
| `src/NzbDrone.Core/Instrumentation/ReconfigureSentry.cs` | OBS-Q2 |
| `src/NzbDrone.Core/History/History.cs` | DATA-Q5 |
| `src/NzbDrone.Core/HealthCheck/` | OBS-Q2 |
| `src/NzbDrone.Core/Backup/` | ENG-Q3 |
| `src/NzbDrone.Common/Instrumentation/CleanseLogMessage.cs` | AUTH-Q5, DATA-Q6 |
| `src/NzbDrone.Update/` | ENG-Q3 |
| `src/Prowlarr.Api.V1/Commands/CommandController.cs` | API-Q6 |
| `src/Prowlarr.Api.V1/Commands/CommandResource.cs` | API-Q6 |
| `src/Prowlarr.Api.V1/Search/SearchController.cs` | API-Q5, DATA-Q3 |
| `src/Prowlarr.Api.V1/Indexers/IndexerController.cs` | DATA-Q1 |
| `src/Prowlarr.Api.V1/Indexers/IndexerResource.cs` | DATA-Q1 |
| `src/Prowlarr.Api.V1/Indexers/IndexerStatsController.cs` | OBS-Q3 |
| `src/Prowlarr.Api.V1/Indexers/IndexerStatusController.cs` | STATE-Q2 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `src/Prowlarr.Api.V1/openapi.json` | API-Q1, API-Q2, DISC-Q1, DISC-Q2, ENG-Q2 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `azure-pipelines.yml` | ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4, OBS-Q2, DISC-Q1 |
| `.github/workflows/ci.yml` | ENG-Q2 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `package.json` | API-Q7 (SignalR client dependency) |
| `global.json` | (SDK version reference) |
| `src/Prowlarr.Api.V1/Prowlarr.Api.V1.csproj` | (project dependencies) |
| `src/NzbDrone.Core/Prowlarr.Core.csproj` | (project dependencies) |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `src/NuGet.config` | (build configuration) |

### Database Migrations
| File | Questions Referenced |
|------|---------------------|
| `src/NzbDrone.Core/Datastore/Migration/` (001–043) | STATE-Q1, DISC-Q1, ENG-Q3 |

### Test Files
| File | Questions Referenced |
|------|---------------------|
| `src/NzbDrone.Integration.Test/ApiTests/` | ENG-Q2, ENG-Q4 |
| `src/Prowlarr.Api.V1.Test/` | ENG-Q4 |

### Distribution
| File | Questions Referenced |
|------|---------------------|
| `distribution/` | ENG-Q1 |
