# Agentic Readiness Assessment Report

**Target**: /Users/lucasdu/Documents/AWS-MAC/2026-projects/sample-agentic-readiness-assessment/services/Radarr--Radarr
**Date**: 2025-05-08
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: csharp, media, desktop
**Context**: Movie collection manager (*arr suite).

**Archetype Justification**: Radarr owns persistent state (SQLite/PostgreSQL databases for movies, collections, downloads, users) and exposes full CRUD operations via 164 REST API endpoints. It manages entity lifecycles (movies: added → monitored → downloaded → imported) with create/update/delete endpoints.

**Surface flags**:
- has_persistent_data_store: true
- has_http_rpc_surface: true
- has_auth_surface: true
- has_write_operations: true
- has_logging_of_user_data: true

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 1 | **RISK-SAFETY**: 7 | **RISK-QUALITY**: 10 | **INFOs**: 13

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days.

**Classification Rationale**: This repo has 1 High finding (AUTH-Q1: no machine identity), 17 Medium findings (7 safety-impact, 10 quality), and 13 Low findings. The matched rule is "1-2 High → Remediation Required." The V6 unified classification maps directly from V5: the single unconditional BLOCKER drives Remediation Required status regardless of Medium/Low counts.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 1 |
| RISK-SAFETY | 7 |
| RISK-QUALITY | 10 |
| INFO | 13 |
| N/A | 0 |
| Not Evaluated (extended) | 11 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 8
**Extended Questions Not Triggered**: 11
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: stateful-crud (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: Radarr uses a single shared API key for all API authentication. The key is generated from `Guid.NewGuid()` and stored in an XML config file. All clients — human UI, scripts, and any potential agents — share the same key. There is no principal attribution: the system cannot distinguish which client made a specific API call. No JWT, OAuth client-credentials, mTLS, or service-account support exists.
- **Gap**: No machine identity authentication with principal attribution. A single shared API key provides authentication but not identity — audit logs cannot attribute actions to specific agents vs. humans vs. scripts.
- **Remediation**:
  - **Immediate**: Implement per-client API key issuance with a `client_id` or `principal` field stored alongside each key. Add the principal to request context so downstream logging can attribute actions.
  - **Target State**: Each agent instance has a unique API key (or OAuth client credential) with the principal identity recorded in all audit-relevant logs. The system can distinguish "Agent-MovieImporter" from "Agent-SearchTrigger" from "Human-Admin."
  - **Estimated Effort**: Medium
  - **Dependencies**: AUTH-Q6 (audit logging) depends on this — cannot log "who" until identity is established.
- **Evidence**: `src/Radarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (GenerateApiKey method), `src/Radarr.Http/Authentication/AuthenticationBuilderExtensions.cs`

---

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No permission scoping exists. The single API key grants full access to all 164 API endpoints — read, write, delete, system restart, backup restore. There is no mechanism to issue a restricted key that grants, for example, read-only access to movies but no delete capability.
- **Gap**: No least-privilege enforcement. An agent intended for read-only movie queries has the same access as one intended for system administration.
- **Compensating Controls**:
  - Deploy an API gateway or reverse proxy in front of Radarr that restricts which endpoints a specific agent key can reach.
  - Scope agent usage to read-only operations via orchestration-layer policy (agent tool definitions exclude write endpoints).
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Introduce role-based API keys (e.g., `read-only`, `media-management`, `admin`) that map to allowed endpoint sets. ASP.NET Core authorization policies can enforce this per-controller.
- **Evidence**: `src/NzbDrone.Host/Startup.cs` (FallbackPolicy requires auth but no role checks), `src/Radarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization exists. Once authenticated with the API key, any HTTP method (GET, POST, PUT, DELETE) is permitted on any endpoint. There are no per-action checks (e.g., `canRead` vs. `canDelete`) in middleware or controller logic.
- **Gap**: Cannot restrict an agent to "read movies" while denying "delete movies" within the same resource type.
- **Compensating Controls**:
  - Limit agent tool definitions at the orchestration layer to exclude destructive operations (DELETE, system/shutdown, system/restart).
  - Deploy a reverse proxy with method-level filtering per client identity.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add authorization policies per HTTP method/endpoint group. ASP.NET Core supports `[Authorize(Policy = "WriteMovies")]` on controller actions.
- **Evidence**: `src/Radarr.Api.V3/Movies/MovieController.cs` (no authorization attributes beyond global auth), `src/NzbDrone.Host/Startup.cs`

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: There is no mechanism to suspend or revoke individual agent identities. Since all clients share a single API key, revoking the key disables ALL API access — there is no way to isolate a misbehaving agent without taking down all integrations.
- **Gap**: Cannot suspend one agent's access without disrupting all other API consumers.
- **Compensating Controls**:
  - Deploy an API gateway with per-client keys that can be individually revoked.
  - Use network-level controls (IP allowlisting) to isolate agent access.
- **Remediation Timeline**: 30–60 days (depends on AUTH-Q1 remediation)
- **Recommendation**: Once per-client API keys are implemented (AUTH-Q1), add a key status field (active/suspended) and check it during authentication. Provide an admin endpoint to toggle key status.
- **Evidence**: `src/Radarr.Http/Authentication/ApiKeyAuthenticationHandler.cs` (compares against single key, no revocation mechanism), `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No inbound API rate limiting exists. The application has outbound rate limiting (2-second delays per indexer host for external requests) but no middleware or configuration to throttle incoming API requests. A runaway agent loop could submit unlimited requests per second to the API.
- **Gap**: No protection against agent traffic storms overwhelming the application. The single-instance SQLite database is particularly vulnerable to concurrent write pressure.
- **Compensating Controls**:
  - Deploy Radarr behind a reverse proxy (nginx, Caddy, Traefik) with rate limiting configured per client.
  - Implement agent-side rate limiting in the tool orchestration layer.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add ASP.NET Core rate limiting middleware (`Microsoft.AspNetCore.RateLimiting`) with per-client sliding window policies. Consider tighter limits on write endpoints than read endpoints.
- **Evidence**: `src/NzbDrone.Common/TPL/RateLimitService.cs` (outbound only), `src/NzbDrone.Common/Http/HttpClient.cs` (applies to outbound HTTP), `src/NzbDrone.Host/Startup.cs` (no rate limiting middleware registered)

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Radarr has comprehensive log cleansing for secrets (API keys, passwords, tokens, webhook URLs) via 20+ regex patterns in `CleanseLogMessage.cs`. However, the HTTP logging middleware logs full request paths including query parameters that could contain user-identifiable information. OS usernames in file paths are partially masked. IP addresses are partially masked for non-local addresses. The system logs movie titles and file paths which could be considered behavioral data.
- **Gap**: While secrets are well-scrubbed, request/response body logging at trace level could capture user-submitted data. The log cleansing is regex-based and may miss new patterns of sensitive data introduced through provider plugins.
- **Compensating Controls**:
  - Keep log level at Info (default) in production — trace-level body logging is disabled by default.
  - Restrict log file access to the Radarr admin user only.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Audit logging middleware for any user-submitted content logged at non-trace levels. Consider adding a structured log field allowlist rather than relying solely on regex-based scrubbing.
- **Evidence**: `src/NzbDrone.Common/Instrumentation/CleanseLogMessage.cs`, `src/NzbDrone.Common/Instrumentation/CleansingFileTarget.cs`, `src/Radarr.Http/Middleware/LoggingMiddleware.cs`

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: An OpenAPI 3.0.4 specification exists at `src/Radarr.Api.V3/openapi.json` with 164 documented endpoints. The spec is auto-generated via Swashbuckle from code annotations, which keeps it current with the implementation. Security schemes (X-Api-Key header and apikey query param) are documented.
- **Gap**: The spec exists and is auto-generated — this is a PASS for machine-readable spec presence. However, many response schemas lack detailed descriptions and example values that would improve agent tool generation quality.
- **Compensating Controls**:
  - Use the existing OpenAPI spec directly for agent tool generation.
  - Supplement with manual descriptions for high-priority endpoints.
- **Remediation Timeline**: 30 days (enrichment, not creation)
- **Recommendation**: Enrich the OpenAPI spec with response examples and field descriptions for key endpoints (movies, queue, system). Add `x-agent-tool-name` extensions for endpoints suited to agent consumption.
- **Evidence**: `src/Radarr.Api.V3/openapi.json`

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The application has a global exception handler (`RadarrErrorPipeline`) that returns structured JSON error bodies with `ErrorModel` containing `Message`, `Description`, and `Content` fields. Exception types are mapped to appropriate HTTP status codes (404, 409, 400, 500). FluentValidation errors return detailed field-level validation messages.
- **Gap**: No `retryable` flag or error category field. The error model lacks a machine-readable error code (only human-readable message). An agent cannot distinguish "retry this in 5 seconds" from "fix your input" without parsing message text.
- **Compensating Controls**:
  - Agents can use HTTP status codes as a proxy: 4xx = terminal, 5xx/timeout = retriable.
  - Build a status-code-to-behavior mapping in the agent tool layer.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add an `errorCode` enum field and `retryable` boolean to `ErrorModel`. Map existing exception types to stable error codes (e.g., `VALIDATION_FAILED`, `RESOURCE_NOT_FOUND`, `CONFLICT`, `INTERNAL_ERROR`).
- **Evidence**: `src/Radarr.Http/ErrorManagement/RadarrErrorPipeline.cs`, `src/Radarr.Http/ErrorManagement/ErrorModel.cs`

#### DATA-Q3: Selective Query Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Pagination is available on some endpoints (blocklist, queue, history, exclusions) via `PagingResource<T>` with `page`, `pageSize`, `sortKey`, `sortDirection`, and `totalRecords`. However, the primary movie endpoint (`GET /api/v3/movie`) returns ALL movies in a single response with no pagination. Filter support exists via query parameters on some endpoints (movieIds, protocol, status).
- **Gap**: The primary entity endpoint (movies) has no pagination, which means an agent querying a library of thousands of movies receives an unbounded result set. No field selection (sparse fieldsets) is available on any endpoint.
- **Compensating Controls**:
  - Agents can use the filter parameters (tmdbId, excludeLocalCovers) to narrow results.
  - For collections with many movies, use the paginated history/queue endpoints instead.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add pagination to `GET /api/v3/movie` (breaking change — requires API version bump or opt-in via query param). Add sparse fieldset support (`?fields=id,title,status`) to reduce payload size for agent consumption.
- **Evidence**: `src/Radarr.Api.V3/Movies/MovieController.cs` (no pagination), `src/Radarr.Api.V3/Queue/QueueController.cs` (paginated), `src/Radarr.Api.V3/Blocklist/BlocklistController.cs` (paginated)

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The API is versioned at the URL level (`/api/v3/`) and the OpenAPI spec declares version `3.0.0`. However, there is no breaking-change detection in CI, no consumer-driven contract testing (Pact), and no schema comparison tooling. The CI pipeline (Azure Pipelines and GitHub Actions) runs unit and integration tests but does not validate API contract stability between builds.
- **Gap**: No automated breaking-change detection. An API response field removal or type change would not be caught until downstream consumers (including agents) fail. No deprecation notices or changelog for API changes.
- **Compensating Controls**:
  - Pin agent tool schemas to a specific Radarr version and validate compatibility on upgrade.
  - Use the auto-generated OpenAPI spec diff between releases to detect breaking changes manually.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenAPI spec diff (e.g., `oasdiff`) as a CI step that fails on breaking changes. Publish a CHANGELOG for API modifications.
- **Evidence**: `src/Radarr.Api.V3/openapi.json`, `azure-pipelines.yml`, `.github/workflows/ci.yml`

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Radarr has structured logging via NLog with consistent format (`date|level|logger|message`) and supports CLEF (Compact Log Event Format) for console output. The HTTP logging middleware assigns sequence IDs to requests. However, there is no distributed tracing (no OpenTelemetry, no X-Ray, no `traceparent` header propagation). Logs are not JSON-structured by default (plain text format with pipe delimiters).
- **Gap**: No distributed tracing capability. No correlation IDs linking log entries across request lifecycle. The sequence ID in HTTP middleware is request-scoped but not propagated to downstream service calls or database queries.
- **Compensating Controls**:
  - Use the HTTP middleware sequence ID and timestamp to correlate request logs manually.
  - External reverse proxy can inject trace IDs into requests.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add OpenTelemetry SDK with ASP.NET Core instrumentation. Switch default log format to JSON with a `traceId` field. Propagate correlation IDs through the request pipeline.
- **Evidence**: `src/NzbDrone.Common/Instrumentation/NzbDroneLogger.cs`, `src/Radarr.Http/Middleware/LoggingMiddleware.cs`

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Radarr integrates with Sentry for error reporting (unhandled exceptions are sent to Sentry with filtered exception types). There is a built-in health check system (`/api/v3/health`) that monitors internal component health. However, there are no alerting thresholds configured for API error rates or latency — no CloudWatch alarms, no PagerDuty integration, no SLO-based alerting. This is expected for a self-hosted desktop application.
- **Gap**: No automated alerting on API degradation. If agent-initiated requests start failing at elevated rates, there is no mechanism to detect and alert operators.
- **Compensating Controls**:
  - Sentry captures unhandled exceptions and can be configured with alert rules.
  - Deploy external monitoring (e.g., Uptime Kuma, Healthchecks.io) against the `/ping` endpoint.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Expose Prometheus metrics endpoint for request rate, error rate, and latency. Configure alerting via Grafana or Sentry performance monitoring.
- **Evidence**: `src/NzbDrone.Common/Instrumentation/Sentry/SentryTarget.cs`, `src/Radarr.Api.V3/Health/HealthController.cs`

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No Infrastructure as Code exists in this repository. Radarr is a self-hosted application — users deploy it on their own infrastructure (bare metal, Docker, NAS devices). There are no Terraform, CloudFormation, CDK, or Helm definitions. The application manages its own configuration via XML files and environment variables.
- **Gap**: No IaC-defined integration surface. Users deploying Radarr as an agent-accessible service must define their own API gateway, IAM roles, and network policies outside of this repository. No drift detection or peer-reviewed infrastructure changes are possible within the application itself.
- **Compensating Controls**:
  - Provide reference IaC templates (Terraform/CDK) for deploying Radarr behind an API gateway with proper auth and rate limiting.
  - Document recommended deployment architecture for agent-accessible instances.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Create a `deploy/` directory with reference IaC for common deployment patterns (Docker Compose with reverse proxy, Kubernetes Helm chart with Ingress and rate limiting).
- **Evidence**: No IaC files found in repository. Deployment relies on community-maintained Docker images and platform-specific packages.

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: A comprehensive CI/CD pipeline exists via Azure Pipelines (10-stage, multi-platform) and GitHub Actions. The pipeline includes unit tests, integration tests, automation tests (UI), and SonarCloud analysis. However, there is no API contract testing — no Pact tests, no OpenAPI spec validation against implementation in the build, no breaking-change detection.
- **Gap**: API changes are not validated against a contract in CI. A breaking change (removed field, changed type) would pass all existing tests and only be detected by consumers after release.
- **Compensating Controls**:
  - The OpenAPI spec is auto-generated from code annotations (Swashbuckle), which means the spec always reflects the current code state — but there's no comparison to the previous version.
  - Integration tests exercise API endpoints, providing partial contract coverage.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add an OpenAPI spec diff step in CI that compares the generated spec against the last released version and fails on breaking changes. Consider adding consumer-driven contract tests (Pact) for key endpoints.
- **Evidence**: `azure-pipelines.yml`, `.github/workflows/ci.yml`, `src/Radarr.Api.V3/openapi.json`

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The application includes a self-updater component (`NzbDrone.Update` project) that can update the running instance. The CI/CD pipeline produces versioned packages for multiple platforms. However, there is no automated rollback mechanism — updates are one-way. There are no blue/green deployments, canary releases, or feature flags in the deployment process. Database migrations (FluentMigrator) are forward-only with no down-migration support observed.
- **Gap**: No fast rollback if a new release breaks agent-facing APIs. Users must manually reinstall a previous version and restore database backups. Database schema changes cannot be rolled back automatically.
- **Compensating Controls**:
  - Radarr's built-in backup system creates database backups before updates.
  - Pin agent deployments to a tested Radarr version and delay upgrades until validated.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add down-migration support in FluentMigrator. Document a rollback procedure. Consider implementing a feature-flag system for new API changes.
- **Evidence**: `src/NzbDrone.Update/`, `src/NzbDrone.Core/Datastore/Migration/`, `azure-pipelines.yml` (Packages stage)

---

## INFOs — Architecture and Design Inputs

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No idempotency key support exists on any write endpoint. No ETags, If-Match headers, or conditional writes. The only deduplication mechanism is command-queue equality comparison that prevents re-queuing the same command. POST endpoints (e.g., POST /api/v3/movie) will create duplicates if called multiple times with the same payload.
- **Implication**: If agent scope expands to write-enabled, idempotency will become a BLOCKER. Duplicate movie additions, repeated queue grabs, and double-submitted commands would occur on retries.
- **Recommendation**: Plan idempotency key support for write endpoints before expanding agent scope to write-enabled.
- **Evidence**: `src/Radarr.Api.V3/Movies/MovieController.cs`, `src/NzbDrone.Core/Messaging/Commands/CommandQueueManager.cs`

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: All API responses are JSON (Content-Type: application/json). The application uses System.Text.Json for serialization with consistent naming conventions (camelCase). SignalR messages are also JSON-encoded. No XML, binary, or protobuf formats.
- **Implication**: JSON is ideal for LLM consumption. Agent tools can parse responses directly without format conversion.
- **Recommendation**: No action required — JSON is the preferred format for agent integration.
- **Evidence**: `src/Radarr.Api.V3/openapi.json`, `src/NzbDrone.Host/Startup.cs` (JSON serialization config)

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limit headers (X-RateLimit-Remaining, Retry-After) are returned in API responses. No rate limits are documented in the OpenAPI spec. The application has no inbound rate limiting, so there are no limits to document.
- **Implication**: Agents have no self-throttling signal from the API. Once rate limiting is implemented (STATE-Q5), rate limit headers should be added so agents can self-regulate.
- **Recommendation**: When inbound rate limiting is implemented, include standard rate limit headers in responses.
- **Evidence**: `src/Radarr.Api.V3/openapi.json` (no rate limit documentation)

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No compensation or saga patterns exist. The command queue system processes commands sequentially but has no rollback logic — a failed command is simply marked "Failed" with the exception recorded. Multi-step operations (e.g., import movie file → rename → update metadata) have no compensation if a middle step fails.
- **Implication**: If agent scope expands to write-enabled, this becomes a BLOCKER. Agent-initiated multi-step workflows (add movie → configure quality → trigger search) cannot be atomically rolled back.
- **Recommendation**: Plan saga/compensation patterns for multi-step write workflows before expanding agent scope.
- **Evidence**: `src/NzbDrone.Core/Messaging/Commands/CommandQueueManager.cs`, `src/NzbDrone.Core/Download/CompletedDownloadService.cs`

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No optimistic locking (version fields, ETags) exists on any entity. The `ModelBase` class has only an `int Id` field. No `RowVersion`, `ConcurrencyToken`, or `UpdatedAt` timestamps. Transactions are used only for bulk inserts. SQLite WAL mode provides some concurrency support for reads, with Polly retry on Busy errors.
- **Implication**: Multiple concurrent write agents could overwrite each other's changes silently. Relevant for future write-enabled scope expansion.
- **Recommendation**: Add version fields to key entities (Movie, MovieFile, Collection) before enabling concurrent write agents.
- **Evidence**: `src/NzbDrone.Core/Datastore/ModelBase.cs`, `src/NzbDrone.Core/Datastore/BasicRepository.cs`

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits exist. The bulk endpoints (e.g., `PUT /api/v3/movie/editor`, `DELETE /api/v3/blocklist/bulk`) accept unbounded arrays. There is no per-session or per-identity limit on how many records can be modified in a single call or time window.
- **Implication**: A write-enabled agent could bulk-delete entire movie collections or bulk-modify all monitored states in a single request.
- **Recommendation**: Add configurable limits on bulk operation size before expanding agent scope to write-enabled.
- **Evidence**: `src/Radarr.Api.V3/Movies/MovieEditorController.cs`, `src/Radarr.Api.V3/Blocklist/BlocklistController.cs`

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Limited draft-state support. The command queue has a lifecycle (Queued → Started → Completed/Failed) which provides a form of pending state for background operations. Movies can be added as "unmonitored" (not actively searched) which acts as a soft draft. However, there is no general-purpose "draft" or "pending human approval" state for API writes.
- **Implication**: A write-enabled agent could not propose changes for human review before execution.
- **Recommendation**: Consider adding a "proposed" status for movie additions that require human confirmation before triggering searches.
- **Evidence**: `src/NzbDrone.Core/Messaging/Commands/CommandModel.cs`, `src/NzbDrone.Core/Movies/Movie.cs` (Monitored field)

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable approval gates exist. All API operations execute immediately upon request. There is no mechanism to configure specific operations (e.g., "delete movie", "system restart") to require a secondary approval step.
- **Implication**: Write-enabled agents would execute all operations immediately with no human-in-the-loop safety net.
- **Recommendation**: Consider implementing operation-level approval workflows (e.g., destructive operations require confirmation via a separate "confirm" endpoint) before expanding agent scope.
- **Evidence**: `src/Radarr.Api.V3/Movies/MovieController.cs` (DELETE executes immediately), `src/Radarr.Api.V3/System/SystemController.cs` (shutdown/restart execute immediately)

### AUTH-Q5: Credential Management

- **Severity**: INFO
- **Finding**: Credentials are stored in an XML configuration file on the local filesystem. The API key is a GUID stored in config.xml. PostgreSQL credentials can be provided via environment variables or config XML. No secrets management system (Vault, AWS Secrets Manager) is integrated. Password hashing uses PBKDF2-HMACSHA512 with 10000 iterations and 128-bit salt — adequate for a self-hosted application.
- **Implication**: For cloud-deployed agent-accessible instances, credentials should be migrated to a secrets management service. The current approach is acceptable for self-hosted desktop use but insufficient for multi-tenant or cloud deployments.
- **Recommendation**: For agent-accessible deployments, integrate with a secrets manager for API key and database credential storage. Add key rotation support.
- **Evidence**: `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`, `src/NzbDrone.Core/Authentication/UserService.cs`

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: PASS (no finding)
- **Finding**: Radarr exposes a well-documented REST API with 164 endpoints under `/api/v3/`. An OpenAPI 3.0.4 specification is auto-generated via Swashbuckle and stored at `src/Radarr.Api.V3/openapi.json`. The API is the primary integration surface — no direct database access or file-based exchange is required. All operations are available via HTTP REST calls.
- **Gap**: None — the API surface is well-defined and documented.
- **Recommendation**: None required.
- **Evidence**: `src/Radarr.Api.V3/openapi.json`, 70+ controller files in `src/Radarr.Api.V3/`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: OpenAPI 3.0.4 specification exists, auto-generated from code annotations. Kept current with implementation via Swashbuckle. However, response schemas lack detailed descriptions and examples.
- **Gap**: Spec exists but could be enriched with descriptions and examples for agent tool generation quality.
- **Recommendation**: Enrich OpenAPI spec with response examples and field descriptions.
- **Evidence**: `src/Radarr.Api.V3/openapi.json`

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: Structured JSON error bodies (ErrorModel with Message, Description, Content). Exception types mapped to HTTP status codes. No machine-readable error code enum or retryable flag.
- **Gap**: Missing error code and retryable indicator for agent consumption.
- **Recommendation**: Add errorCode enum and retryable boolean to ErrorModel.
- **Evidence**: `src/Radarr.Http/ErrorManagement/RadarrErrorPipeline.cs`, `src/Radarr.Http/ErrorManagement/ErrorModel.cs`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No idempotency keys, ETags, or conditional writes on any endpoint. Command deduplication provides partial protection for background operations only.
- **Gap**: Write endpoints are not idempotent.
- **Recommendation**: Plan idempotency key support before write-enabled agent scope.
- **Evidence**: `src/Radarr.Api.V3/Movies/MovieController.cs`, `src/NzbDrone.Core/Messaging/Commands/CommandQueueManager.cs`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: All responses are JSON (System.Text.Json, camelCase). Ideal for LLM consumption.
- **Gap**: None.
- **Recommendation**: No action required.
- **Evidence**: `src/Radarr.Api.V3/openapi.json`

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
- **Finding**: No rate limit headers returned. No inbound rate limiting exists to document.
- **Gap**: No rate limit signaling to agents.
- **Recommendation**: Add rate limit headers when inbound rate limiting is implemented.
- **Evidence**: `src/Radarr.Api.V3/openapi.json`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: Single shared API key with no principal attribution. Cannot distinguish which client made a specific call. No JWT, OAuth client-credentials, mTLS, or service-account support.
- **Gap**: No machine identity authentication with principal attribution.
- **Recommendation**: Implement per-client API key issuance with principal field.
- **Evidence**: `src/Radarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: Single API key grants full access to all 164 endpoints. No role-based access, no permission scoping.
- **Gap**: No least-privilege enforcement.
- **Recommendation**: Introduce role-based API keys mapping to allowed endpoint sets.
- **Evidence**: `src/NzbDrone.Host/Startup.cs`, `src/Radarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: No per-action authorization checks. Any authenticated client can perform any HTTP method on any endpoint.
- **Gap**: Cannot restrict agents to specific actions within a resource type.
- **Recommendation**: Add per-method authorization policies on controllers.
- **Evidence**: `src/Radarr.Api.V3/Movies/MovieController.cs`, `src/NzbDrone.Host/Startup.cs`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Archetype-calibrated to INFO for stateful-crud with single-user model
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: Credentials stored in local XML config file. No secrets management integration. Acceptable for self-hosted desktop app, insufficient for cloud agent-accessible deployment.
- **Gap**: No secrets manager integration.
- **Recommendation**: Integrate with secrets manager for cloud deployments.
- **Evidence**: `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`, `src/NzbDrone.Core/Authentication/UserService.cs`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No immutable audit logging. Rotating text log files are mutable. No principal attribution in logs. No CloudTrail or append-only storage.
- **Gap**: Cannot attribute actions to callers. Logs are not immutable.
- **Recommendation**: Add principal identity to HTTP logging. Forward to immutable external store.
- **Evidence**: `src/Radarr.Http/Middleware/LoggingMiddleware.cs`, `src/NzbDrone.Common/Instrumentation/NzbDroneLogger.cs`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: No mechanism to suspend individual agent identities. Revoking the single shared API key disables all access.
- **Gap**: Cannot isolate misbehaving agents without full API lockout.
- **Recommendation**: Implement per-client keys with active/suspended status.
- **Evidence**: `src/Radarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No compensation or saga patterns. Failed commands are marked "Failed" with no rollback. Multi-step operations have no atomic compensation.
- **Gap**: No rollback capability for multi-step write operations.
- **Recommendation**: Plan saga/compensation patterns before write-enabled scope expansion.
- **Evidence**: `src/NzbDrone.Core/Messaging/Commands/CommandQueueManager.cs`

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
- **Finding**: No optimistic locking (version fields, ETags). ModelBase has only int Id. SQLite WAL with Polly retry on Busy.
- **Gap**: No concurrency controls for writes.
- **Recommendation**: Add version fields before enabling concurrent write agents.
- **Evidence**: `src/NzbDrone.Core/Datastore/ModelBase.cs`, `src/NzbDrone.Core/Datastore/BasicRepository.cs`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has external dependencies (calls other services or external APIs)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No inbound API rate limiting. Only outbound rate limiting for external service calls. No protection against agent traffic storms.
- **Gap**: No API-layer throttling to prevent agent overload.
- **Recommendation**: Add ASP.NET Core rate limiting middleware with per-client policies.
- **Evidence**: `src/NzbDrone.Common/TPL/RateLimitService.cs`, `src/NzbDrone.Host/Startup.cs`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No transaction limits. Bulk endpoints accept unbounded arrays.
- **Gap**: No configurable limits on bulk operations.
- **Recommendation**: Add bulk operation size limits before write-enabled scope.
- **Evidence**: `src/Radarr.Api.V3/Movies/MovieEditorController.cs`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Limited draft-state. Command queue lifecycle (Queued→Started→Completed) and unmonitored movie status provide partial pending semantics.
- **Gap**: No general-purpose draft/approval state for writes.
- **Recommendation**: Add "proposed" status for movie additions requiring human confirmation.
- **Evidence**: `src/NzbDrone.Core/Messaging/Commands/CommandModel.cs`, `src/NzbDrone.Core/Movies/Movie.cs`

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No approval gates. All operations execute immediately. No mechanism to require secondary confirmation.
- **Gap**: No operation-level approval workflows.
- **Recommendation**: Implement confirmation endpoints for destructive operations before write-enabled scope.
- **Evidence**: `src/Radarr.Api.V3/Movies/MovieController.cs`, `src/Radarr.Api.V3/System/SystemController.cs`

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: A `.devcontainer` configuration exists for development. Docker Compose is not present for local testing. The CI pipeline tests against multiple databases (SQLite and PostgreSQL 14/15) which provides some staging capability. However, there is no production-equivalent sandbox environment with seed data for agent testing.
- **Gap**: No sandbox environment with production-equivalent data shape for agent testing.
- **Recommendation**: Create a Docker Compose environment with seed data for agent integration testing.
- **Evidence**: `.devcontainer/devcontainer.json`, `azure-pipelines.yml` (test stages)

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — B1 fires as RISK-SAFETY
- **Finding**: **Stage A = Yes**: The system stores user credentials (password hash, salt, iterations), API keys, download client credentials, proxy passwords, and SSL certificate passwords. **Stage B - B1**: The `HostConfigResource` endpoint (`GET /api/v3/config/host`) returns the API key, password hash, SSL cert password, proxy credentials, and PostgreSQL credentials in its API response. Provider settings (download clients, indexers) include fields annotated with `PrivacyLevel.Password` that are still serialized in API responses. **B2**: No access control differentiation — single API key grants access to all data including credentials. **B3**: No formal classification metadata.
- **Gap**: Agent-facing API responses include sensitive credentials. The HostConfig endpoint is particularly dangerous — it returns the system API key and password hash to any authenticated caller.
- **Recommendation**: Add `[JsonIgnore]` to sensitive fields in HostConfigResource (ApiKey, Password, SslCertPassword, ProxyPassword, PostgresPassword). Create separate endpoints for credential management that are excluded from agent-facing tool definitions. Implement field-level filtering based on caller role.
- **Evidence**: `src/Radarr.Api.V3/Config/HostConfigResource.cs`, `src/Radarr.Api.V3/Config/HostConfigController.cs`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY; however, archetype calibration applies.
- **Finding**: Radarr is a self-hosted application. Data resides on the user's own infrastructure — the user controls data residency entirely. The application stores movie metadata (public TMDB/IMDB data), user credentials, and file system paths. No regulated data (GDPR-protected PII beyond the single admin user, HIPAA, PCI) is stored. The "user" is the self-hosting individual administering their own system.
- **Gap**: For cloud-hosted or multi-user deployments, data residency would need explicit configuration. For the default self-hosted single-user scenario, residency is inherently controlled by the user.
- **Recommendation**: If deploying as a cloud-hosted agent-accessible service, document data residency controls and ensure the LLM endpoint is in the same jurisdiction as the data.
- **Evidence**: `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs`, `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK-QUALITY
- **Finding**: Pagination on some endpoints (blocklist, queue, history) but not on the primary movie endpoint. Filter parameters available on select endpoints.
- **Gap**: Primary entity endpoint (movies) has no pagination — unbounded result sets.
- **Recommendation**: Add pagination to GET /api/v3/movie. Add sparse fieldset support.
- **Evidence**: `src/Radarr.Api.V3/Movies/MovieController.cs`, `src/Radarr.Api.V3/Queue/QueueController.cs`

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
- **Finding**: Comprehensive log cleansing (20+ regex patterns) for secrets. OS usernames partially masked. IP addresses partially masked. However, trace-level logging can capture request/response bodies with user data. Regex-based approach may miss new sensitive patterns.
- **Gap**: Potential for PII leakage at trace log levels. Regex scrubbing is not guaranteed complete.
- **Recommendation**: Audit trace-level logging for user content. Consider structured log field allowlist.
- **Evidence**: `src/NzbDrone.Common/Instrumentation/CleanseLogMessage.cs`, `src/Radarr.Http/Middleware/LoggingMiddleware.cs`

#### DATA-Q7: Data Quality Awareness
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Always evaluated as INFO
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: API versioned at URL level (/api/v3/). OpenAPI spec version 3.0.0. No breaking-change detection in CI. No consumer-driven contract tests.
- **Gap**: No automated breaking-change detection. No deprecation notices.
- **Recommendation**: Add OpenAPI spec diff as CI step. Publish API CHANGELOG.
- **Evidence**: `src/Radarr.Api.V3/openapi.json`, `azure-pipelines.yml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Field names are human-readable and semantically meaningful. API uses clear camelCase naming: `movieId`, `qualityProfileId`, `minimumAvailability`, `sizeOnDisk`, `hasFile`, `isAvailable`. Database columns use clear PascalCase. No legacy abbreviations or cryptic codes requiring a data dictionary.
- **Implication**: Agent LLMs can reason about field meanings directly from names without requiring a lookup table.
- **Recommendation**: No action required — naming conventions are agent-friendly.
- **Evidence**: `src/Radarr.Api.V3/Movies/MovieResource.cs`, `src/Radarr.Api.V3/openapi.json`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal data catalog or metadata layer. The OpenAPI spec serves as the de facto API catalog. Database schema is defined via FluentMigrator migrations. No Glue Data Catalog, Collibra, or equivalent metadata repository.
- **Implication**: Agent tool builders must rely on the OpenAPI spec and source code for understanding data semantics. The self-documenting API with meaningful field names partially compensates.
- **Recommendation**: Consider documenting entity relationships and data flow in a lightweight format (Markdown or Mermaid diagrams) for agent tool builders.
- **Evidence**: `src/Radarr.Api.V3/openapi.json`, `src/NzbDrone.Core/Datastore/Migration/`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: NLog-based logging with consistent format. CLEF support for console. HTTP middleware sequence IDs. No distributed tracing (no OpenTelemetry, X-Ray, traceparent). Not JSON-structured by default.
- **Gap**: No distributed tracing. No correlation IDs across request lifecycle.
- **Recommendation**: Add OpenTelemetry SDK. Switch to JSON log format with traceId field.
- **Evidence**: `src/NzbDrone.Common/Instrumentation/NzbDroneLogger.cs`, `src/Radarr.Http/Middleware/LoggingMiddleware.cs`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: Sentry for error reporting. Built-in health check system. No error rate or latency alerting thresholds. Expected for self-hosted desktop application.
- **Gap**: No automated alerting on API degradation.
- **Recommendation**: Expose Prometheus metrics endpoint. Configure alerting for agent-accessible deployments.
- **Evidence**: `src/NzbDrone.Common/Instrumentation/Sentry/SentryTarget.cs`, `src/Radarr.Api.V3/Health/HealthController.cs`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics published externally. Internal health checks monitor component health (disk space, download client connectivity, indexer status). No CloudWatch/Prometheus metrics for business outcomes (movies imported per day, search success rate, download completion rate).
- **Implication**: Cannot measure whether agent-initiated operations produce desired outcomes without building external monitoring.
- **Recommendation**: Expose key business metrics (movies added, downloads completed, import success rate) via a metrics endpoint for agent behavior validation.
- **Evidence**: `src/Radarr.Api.V3/Health/HealthController.cs`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK-QUALITY
- **Finding**: No IaC in repository. Self-hosted application relying on user-managed infrastructure. No Terraform, CloudFormation, CDK, or Helm charts.
- **Gap**: No IaC-defined integration surface for agent-accessible deployments.
- **Recommendation**: Create reference IaC templates for agent-accessible deployment patterns.
- **Evidence**: No IaC files found in repository.

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive CI/CD (Azure Pipelines 10-stage + GitHub Actions). Unit, integration, and automation tests. No API contract testing, no OpenAPI spec validation against implementation, no breaking-change detection.
- **Gap**: No API contract testing in CI.
- **Recommendation**: Add OpenAPI spec diff step. Consider Pact tests for key endpoints.
- **Evidence**: `azure-pipelines.yml`, `.github/workflows/ci.yml`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: Self-updater exists. Versioned packages produced by CI. No automated rollback. Forward-only database migrations. Manual rollback requires reinstallation.
- **Gap**: No fast automated rollback capability.
- **Recommendation**: Add down-migration support. Document rollback procedures. Consider feature flags.
- **Evidence**: `src/NzbDrone.Update/`, `src/NzbDrone.Core/Datastore/Migration/`

#### ENG-Q4: API Test Coverage
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Always evaluated (but INFO for stateless-utility)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has persistent data stores
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| src/Radarr.Http/Authentication/ApiKeyAuthenticationHandler.cs | AUTH-Q1, AUTH-Q2, AUTH-Q7 |
| src/Radarr.Http/Authentication/AuthenticationBuilderExtensions.cs | AUTH-Q1 |
| src/NzbDrone.Core/Configuration/ConfigFileProvider.cs | AUTH-Q1, AUTH-Q5, AUTH-Q7, DATA-Q2 |
| src/NzbDrone.Host/Startup.cs | AUTH-Q2, AUTH-Q3, API-Q5, STATE-Q5 |
| src/Radarr.Api.V3/Movies/MovieController.cs | API-Q4, AUTH-Q3, DATA-Q3, HITL-Q2 |
| src/Radarr.Api.V3/Queue/QueueController.cs | DATA-Q3 |
| src/Radarr.Api.V3/Blocklist/BlocklistController.cs | DATA-Q3, STATE-Q6 |
| src/Radarr.Api.V3/Movies/MovieEditorController.cs | STATE-Q6 |
| src/Radarr.Http/ErrorManagement/RadarrErrorPipeline.cs | API-Q3 |
| src/Radarr.Http/ErrorManagement/ErrorModel.cs | API-Q3 |
| src/Radarr.Http/Middleware/LoggingMiddleware.cs | AUTH-Q6, DATA-Q6, OBS-Q1 |
| src/NzbDrone.Common/Instrumentation/NzbDroneLogger.cs | AUTH-Q6, OBS-Q1 |
| src/NzbDrone.Common/Instrumentation/CleanseLogMessage.cs | DATA-Q6 |
| src/NzbDrone.Common/Instrumentation/CleansingFileTarget.cs | DATA-Q6 |
| src/NzbDrone.Common/TPL/RateLimitService.cs | STATE-Q5 |
| src/NzbDrone.Core/Datastore/ModelBase.cs | STATE-Q3 |
| src/NzbDrone.Core/Datastore/BasicRepository.cs | STATE-Q3 |
| src/NzbDrone.Core/Messaging/Commands/CommandQueueManager.cs | API-Q4, STATE-Q1 |
| src/NzbDrone.Core/Messaging/Commands/CommandModel.cs | HITL-Q1 |
| src/NzbDrone.Core/Movies/Movie.cs | HITL-Q1 |
| src/NzbDrone.Core/Authentication/UserService.cs | AUTH-Q5 |
| src/Radarr.Api.V3/Config/HostConfigResource.cs | DATA-Q1 |
| src/Radarr.Api.V3/Config/HostConfigController.cs | DATA-Q1 |
| src/Radarr.Api.V3/System/SystemController.cs | HITL-Q2 |
| src/Radarr.Api.V3/Movies/MovieResource.cs | DISC-Q2 |
| src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs | DATA-Q2 |
| src/NzbDrone.Common/Instrumentation/Sentry/SentryTarget.cs | OBS-Q2 |
| src/Radarr.Api.V3/Health/HealthController.cs | OBS-Q2, OBS-Q3 |
| src/NzbDrone.Core/Download/CompletedDownloadService.cs | STATE-Q1 |
| src/NzbDrone.Update/ | ENG-Q3 |
| src/NzbDrone.Core/Datastore/Migration/ | ENG-Q3, DISC-Q3 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| src/Radarr.Api.V3/openapi.json | API-Q1, API-Q2, API-Q5, API-Q8, DISC-Q1, DISC-Q2, DISC-Q3, ENG-Q2 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| azure-pipelines.yml | DISC-Q1, ENG-Q2, ENG-Q3, HITL-Q3 |
| .github/workflows/ci.yml | DISC-Q1, ENG-Q2 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| .devcontainer/devcontainer.json | HITL-Q3 |
