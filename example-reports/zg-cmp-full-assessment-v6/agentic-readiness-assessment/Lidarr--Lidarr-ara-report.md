# Agentic Readiness Assessment Report

**Target**: Lidarr--Lidarr
**Date**: 2025-05-08
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: csharp, media, desktop
**Context**: Music collection manager (*arr suite).

**Archetype Justification**: The application owns persistent state (SQLite/PostgreSQL databases) and exposes full CRUD operations (create/update/delete artists, albums, tracks, queue items) via 75+ REST API controllers with entity lifecycle management.

**Surface flags**:
  - has_persistent_data_store: true
  - has_http_rpc_surface: true
  - has_auth_surface: true
  - has_write_operations: true
  - has_logging_of_user_data: true

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 1 | **RISK-SAFETY**: 7 | **RISK-QUALITY**: 11 | **INFOs**: 13

This repo has 1 BLOCKER finding (resolving to Remediation Required). The single BLOCKER (AUTH-Q1: Machine Identity Authentication) must be resolved before any agent deployment — including pilots.

**V6 Classification Rationale**: This repo has 1 High finding (AUTH-Q1 BLOCKER), 18 Medium findings (7 safety-impact, 11 quality-only), and 13 Low findings. 1 High → "Remediation Required" per V6 rule "1-2 High → Remediation Required." The V5 Readiness Profile also resolves to "Remediation Required" (1 BLOCKER present). V6 and V5 classifications are aligned.

**Deployment Gate**: Resolve all blockers before any agent deployment — including pilots.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 1 |
| RISK-SAFETY | 7 |
| RISK-QUALITY | 11 |
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
- **Finding**: Lidarr uses a single, static API key for all API access. The API key is a GUID stored in plaintext XML configuration (`config.xml`). All authenticated requests share the same identity — there is no mechanism to distinguish between different callers (agents, users, integrations). The `ApiKeyAuthenticationHandler.cs` validates a single shared key from header `X-Api-Key`, query param `apikey`, or `Authorization: Bearer` token. Authentication succeeds as `"API"` principal with no further identity attribution.
- **Gap**: No support for individual machine identity (client credentials OAuth, mTLS, or per-agent API keys). All API consumers share a single identity. No principal attribution in audit logs — every request authenticates as the same `"API"` claim.
- **Remediation**:
  - **Immediate**: Introduce per-agent API key generation with unique principal identifiers. Add a `ClientId` field to the authentication ticket that can be used in audit logging.
  - **Target State**: Each agent identity has a unique credential (API key or OAuth client credential) that is attributed in all audit/history records. Agent identities can be individually revoked.
  - **Estimated Effort**: High
  - **Dependencies**: AUTH-Q6 (audit logging), AUTH-Q7 (identity suspension)
- **Evidence**: `src/Lidarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`

---

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The authorization model is binary — either you have the API key (full access to all endpoints) or you don't. There are no IAM policies, role definitions, or scope-based permissions. The single API key grants unrestricted access to every endpoint including destructive operations (delete artists, delete queue items, reset API key).
- **Gap**: No mechanism to grant an agent read-only access to specific resources. Every authenticated caller has identical full-admin privileges.
- **Compensating Controls**:
  - Deploy an API gateway or reverse proxy in front of Lidarr that restricts agent access to specific HTTP methods and URL paths
  - Use a read-only database replica for agent queries (requires custom adapter)
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement role-based access control with at minimum a "read-only" role that excludes POST/PUT/DELETE operations. Support scoped API keys per consumer.
- **Evidence**: `src/Lidarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/NzbDrone.Host/Startup.cs` (single fallback policy)

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization exists. Once authenticated via API key, all 75+ endpoints (read, create, update, delete) are accessible with no additional permission checks. The `UiAuthorizationHandler` only distinguishes authenticated vs. anonymous users, not read vs. write permissions.
- **Gap**: Cannot enforce that an agent may read albums but not delete them within the same resource type.
- **Compensating Controls**:
  - External reverse proxy with path + method-based ACLs
  - Network segmentation restricting agent access to specific endpoints
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Introduce action-level authorization attributes on controllers (e.g., `[RequirePermission("albums:read")]` vs `[RequirePermission("albums:delete")]`).
- **Evidence**: `src/Lidarr.Http/Authentication/UiAuthorizationHandler.cs`, `src/Lidarr.Http/REST/RestController.cs`

#### AUTH-Q6: Immutable Audit Logging — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Lidarr logs authentication events via NLog "Auth" logger and records entity history (grabbed, imported, failed events) in the database via `EntityHistoryRepository`. However: (1) logs are stored on the local filesystem with no immutability guarantees, (2) the authenticated principal is not recorded — all API requests authenticate as generic "API" identity, (3) history records track system events (downloads, imports) but not who initiated them.
- **Gap**: No immutable, tamper-evident audit trail. No per-caller attribution in logs or history. Local log files can be modified or deleted by any user with filesystem access.
- **Compensating Controls**:
  - Forward Lidarr logs to a centralized, append-only log aggregation service (e.g., CloudWatch Logs, ELK with immutable indices)
  - Implement log shipping with integrity verification
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add caller identity (agent/user principal) to all EntityHistory records and API request logs. Ship logs to an immutable store.
- **Evidence**: `src/NzbDrone.Core/History/EntityHistoryRepository.cs`, `src/Lidarr.Http/Middleware/LoggingMiddleware.cs`, `src/Lidarr.Http/Authentication/AuthenticationService.cs`

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: There is no mechanism to suspend an individual agent identity. The single shared API key cannot be selectively revoked — the only option is to reset the entire API key (via `ResetApiKeyCommand`), which disconnects ALL consumers simultaneously.
- **Gap**: Cannot isolate a misbehaving agent without disrupting all API consumers (UI, other integrations, other agents).
- **Compensating Controls**:
  - Revoke agent access at an external proxy/gateway layer if one is deployed in front of Lidarr
  - IP-based blocking at the network level
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Support multiple API keys with individual revocation. Each agent should have its own key that can be disabled independently.
- **Evidence**: `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` (single ApiKey, `ResetApiKeyCommand`)

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No inbound rate limiting exists on any API endpoint. The `RateLimitService` in the codebase only throttles *outbound* HTTP requests to external services (indexers, download clients). There is no API Gateway, WAF, or application-level middleware to rate-limit incoming requests.
- **Gap**: A runaway agent loop can overwhelm the application at machine speed with no protection. No usage plans, no throttle configuration, no per-consumer rate limits.
- **Compensating Controls**:
  - Deploy a reverse proxy (nginx, HAProxy) with rate limiting in front of Lidarr
  - Use OS-level iptables/nftables rate limiting for the Lidarr port
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add rate limiting middleware (e.g., `AspNetCoreRateLimit` NuGet package) with per-key throttling. Consider configurable limits per consumer.
- **Evidence**: `src/NzbDrone.Common/TPL/RateLimitService.cs` (outbound only), `src/NzbDrone.Host/Startup.cs` (no rate limiting middleware)

#### DATA-Q2: Data Residency and Sovereignty — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Lidarr stores user data locally (SQLite database on the host filesystem or in a PostgreSQL database). The application itself has no data residency enforcement — data location depends entirely on where the operator deploys it. If an agent reads user library data (artists, albums, listening preferences) and transmits it to an LLM endpoint in another region, there are no controls preventing cross-boundary data flow.
- **Gap**: No data residency configuration, no region enforcement, no data classification that would identify user library metadata as subject to residency constraints.
- **Compensating Controls**:
  - Architect the agent to use Amazon Bedrock in the same region as the Lidarr deployment
  - Restrict agent-LLM communication to in-region endpoints via network policy
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document the data residency characteristics of Lidarr deployments. If operating in regulated jurisdictions, ensure the agent architecture keeps data in-region.
- **Evidence**: `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs`, `src/NzbDrone.Core/Datastore/DbFactory.cs`

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The `LoggingMiddleware` logs request URLs at Trace level and API request details at Debug level. The `LidarrErrorPipeline` includes full exception stack traces (including `exception.ToString()`) in HTTP error responses. The `HostConfigResource` endpoint returns sensitive credentials (API key, SSL cert password, proxy password) in JSON responses. No PII scrubbing middleware or log filtering exists.
- **Gap**: No log scrubbing for sensitive data. Stack traces in error responses may expose internal paths and data. If user metadata (artist names, library paths) is logged, there is no redaction mechanism.
- **Compensating Controls**:
  - Configure NLog logging level to Warning in production (suppresses Trace/Debug request logs)
  - Deploy a log scrubbing pipeline between Lidarr and log aggregation
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add PII redaction to logging middleware. Remove stack traces from production error responses. Filter sensitive fields from `HostConfigResource` responses.
- **Evidence**: `src/Lidarr.Http/Middleware/LoggingMiddleware.cs`, `src/Lidarr.Http/ErrorManagement/LidarrErrorPipeline.cs`, `src/Lidarr.Api.V1/Config/HostConfigResource.cs`

### RISK-QUALITY — Address as Capacity Allows

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The `LidarrErrorPipeline` returns structured error bodies with `Message` and `Description` fields. HTTP status codes are mapped correctly (400 for validation, 404 for not found, 409 for conflicts, 500 for server errors). FluentValidation errors return structured field-level error arrays. However, there is no machine-readable error code, no `retryable` field, and no error categorization beyond HTTP status codes.
- **Gap**: No machine-readable error codes beyond HTTP status. An agent cannot programmatically distinguish "database locked, retry" from "invalid input, do not retry" without parsing error message text.
- **Compensating Controls**:
  - Agents can use HTTP status code ranges as heuristics (4xx = terminal, 5xx = retriable)
  - Build error classification into the agent tool wrapper based on known Lidarr error patterns
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add an `errorCode` field (machine-readable enum) and a `retryable` boolean to the error response model.
- **Evidence**: `src/Lidarr.Http/ErrorManagement/LidarrErrorPipeline.cs`

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The API is versioned via URL path (`/api/v1/`). An auto-generated OpenAPI 3.0.4 specification exists (`openapi.json`, 13,101 lines). Database schema is versioned via FluentMigrator (80 migration files). However, there is no breaking change detection in CI, no consumer-driven contract testing, and no changelog or deprecation notice process for API changes.
- **Gap**: No automated breaking change detection. API consumers (including agents) can be broken silently by a new release. No Pact or OpenAPI diff tooling in the CI pipeline.
- **Compensating Controls**:
  - Pin agent tool definitions to a specific Lidarr version and test against it before upgrading
  - Use the OpenAPI spec as a baseline and diff manually before upgrades
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenAPI spec diff to the Azure Pipelines CI. Fail the build on breaking changes unless explicitly approved.
- **Evidence**: `src/Lidarr.Api.V1/openapi.json`, `src/NzbDrone.Core/Datastore/Migration/` (80 migration files), `azure-pipelines.yml`

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Lidarr uses NLog with file logging, Sentry integration, and optional CLEF (structured JSON) output. The `LoggingMiddleware` logs HTTP requests with request paths but does not propagate or generate trace IDs. There is no OpenTelemetry, X-Ray, or `traceparent` header support. No correlation IDs link related log entries for a single request across components.
- **Gap**: No distributed tracing. No correlation IDs for request-scoped log aggregation. Cannot reconstruct the full lifecycle of an agent-initiated request across the application's internal components.
- **Compensating Controls**:
  - Use NLog's CLEF output with timestamps for rough correlation
  - Add request correlation middleware as a lightweight alternative to full distributed tracing
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add OpenTelemetry instrumentation (ASP.NET Core has built-in support). Propagate `traceparent` headers and include trace IDs in structured logs.
- **Evidence**: `src/NzbDrone.Common/Instrumentation/NzbDroneLogger.cs`, `src/Lidarr.Http/Middleware/LoggingMiddleware.cs`

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No alerting configuration exists in the codebase. Sentry is integrated for error capture, but there are no configured thresholds, CloudWatch alarms, PagerDuty/OpsGenie integrations, or SLO-based alerting for API error rates or latency.
- **Gap**: No proactive alerting when the API degrades. Agent failures due to Lidarr API degradation will not be detected until users report problems.
- **Compensating Controls**:
  - Configure Sentry alert rules for error rate spikes
  - Monitor Lidarr's built-in health check endpoint from an external monitoring service
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure alerting on API error rates and response latency using Sentry or an external monitoring solution.
- **Evidence**: `src/NzbDrone.Common/Instrumentation/NzbDroneLogger.cs` (Sentry integration), absence of alerting configuration

#### ENG-Q1: Infrastructure Governance — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No infrastructure-as-code exists in this repository. Lidarr is deployed as platform-specific installers (Debian packages, macOS app bundles, Windows installers). There is no Terraform, CloudFormation, or CDK defining the infrastructure that would expose Lidarr to agents. No drift detection, no infrastructure peer review process.
- **Gap**: No IaC defining the agent-facing integration surface. Infrastructure configuration is manual and not subject to code review or drift detection.
- **Compensating Controls**:
  - Create IaC separately for the deployment environment (e.g., Terraform for the VM/container hosting Lidarr)
  - Document the deployment topology and access controls
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Define the Lidarr deployment infrastructure as code (container orchestration, networking, access controls) in a separate IaC repository if Lidarr will be exposed to agents in a managed environment.
- **Evidence**: `distribution/debian/install.sh`, `distribution/debian/lidarr.service`, absence of IaC files

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: A comprehensive Azure Pipelines CI/CD pipeline exists with unit testing, integration testing, and automation testing stages. The pipeline builds for 12+ platform combinations and includes SonarCloud analysis. However, there is no API contract testing (no Pact, no OpenAPI validation in CI, no breaking change detection).
- **Gap**: API changes are not validated against consumer contracts. An agent tool binding could break silently when Lidarr is updated.
- **Compensating Controls**:
  - Run OpenAPI spec diff as a manual check before upgrades
  - Integration tests partially cover API behavior but do not test against external consumer contracts
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenAPI spec validation and diff to the CI pipeline. Consider adding consumer-driven contract tests for known agent tool bindings.
- **Evidence**: `azure-pipelines.yml`, `src/NzbDrone.Integration.Test/`

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Lidarr has a built-in self-update mechanism (`NzbDrone.Update` project) but no automated rollback capability. The Azure Pipelines CI produces artifacts for multiple platforms but there is no blue/green deployment, canary release, or automated rollback trigger. Rolling back requires manually re-installing a previous version.
- **Gap**: No automated deployment rollback. If an update breaks agent-facing APIs, recovery requires manual intervention.
- **Compensating Controls**:
  - Maintain a backup of the previous version binary alongside the current installation
  - Use container-based deployment with image version pinning for instant rollback
- **Remediation Timeline**: 30–60 days
- **Recommendation**: If deploying in a containerized environment, use image tags and orchestrator rollback (Kubernetes, ECS). For bare-metal, implement a rollback script that restores the previous version.
- **Evidence**: `src/NzbDrone.Update/`, `azure-pipelines.yml`

#### ENG-Q5: Encryption at Rest — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: SQLite databases are stored as unencrypted files on the local filesystem. PostgreSQL connections in `ConnectionStringFactory` do not enforce TLS/SSL. No encryption-at-rest configuration exists anywhere in the codebase — no KMS references, no encrypted storage configuration, no disk encryption settings.
- **Gap**: Data at rest is unencrypted. User library metadata, API keys, and credentials stored in the database and config files are accessible to anyone with filesystem access.
- **Compensating Controls**:
  - Use OS-level full-disk encryption (LUKS, BitLocker, FileVault) on the host
  - Deploy on encrypted EBS volumes if running on AWS
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Enable encrypted storage at the infrastructure layer. For PostgreSQL, enforce TLS connections. Consider SQLCipher for SQLite encryption.
- **Evidence**: `src/NzbDrone.Core/Datastore/DbFactory.cs`, `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs`

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Integration tests exist in `src/NzbDrone.Integration.Test/ApiTests/` covering major API resources (Artist, Album, Track, DownloadClient, Indexer, Notification, Release, Command, Calendar, History, Blocklist, RootFolder, etc.) with typed REST clients. Azure Pipelines CI runs tests in a dedicated `Unit_Test` stage. However, there is no consumer-driven contract testing, no OpenAPI schema validation in CI, and no automated breaking-change detection.
- **Gap**: No API contract testing or breaking-change detection in CI. Tests validate functional behavior but do not guard against schema drift that would break agent tool bindings.
- **Compensating Controls**:
  - Existing integration tests catch functional regressions in API behavior
  - Manual review of API response changes during PR review
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenAPI spec diff validation to the CI pipeline. Consider consumer-driven contract tests (Pact) for agent-facing endpoints.
- **Evidence**: `src/NzbDrone.Integration.Test/ApiTests/`, `azure-pipelines.yml`

#### AUTH-Q5: Credential Management — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: All credentials are stored as plaintext in an XML configuration file (`config.xml`). This includes the API key (GUID), PostgreSQL password, and SSL certificate password. The `ConfigFileProvider` reads these values directly from XML elements with no encryption. Environment variable overrides are supported via IOptions pattern but credentials are not rotated automatically.
- **Gap**: No secrets management system (no Vault, no AWS Secrets Manager). Credentials are stored in plaintext on disk. No rotation mechanism.
- **Compensating Controls**:
  - Restrict filesystem permissions on `config.xml` to the Lidarr service account only
  - Use environment variables sourced from a secrets manager in containerized deployments
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Support external secrets providers for credential injection. Remove plaintext credential storage from `config.xml`.
- **Evidence**: `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`

---

## INFOs — Architecture and Design Inputs

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No idempotency patterns found in the codebase. Write endpoints (POST, PUT, DELETE) do not support idempotency keys. No unique constraint enforcement on business keys for create operations beyond database-level constraints.
- **Implication**: If agent scope is expanded to write-enabled in the future, non-idempotent writes will be a BLOCKER. Agent retries could create duplicate records.
- **Recommendation**: Implement idempotency key support on write endpoints before expanding agent scope to write-enabled.
- **Evidence**: Absence of idempotency patterns across all controllers in `src/Lidarr.Api.V1/`

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: All API responses use JSON serialization (Newtonsoft.Json and System.Text.Json). Content-Type is `application/json`. Responses are well-structured with typed resource models. SignalR uses JSON hub protocol for real-time updates.
- **Implication**: JSON format is ideal for agent consumption — no parsing complexity. Agents can consume Lidarr API responses directly.
- **Recommendation**: No action needed. JSON is the preferred format for agent tool responses.
- **Evidence**: `src/Lidarr.Http/REST/RestController.cs`, `src/NzbDrone.Host/Startup.cs` (AddNewtonsoftJson)

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limit headers (`X-RateLimit-Remaining`, `Retry-After`) are returned in API responses. No rate limit documentation exists. The only response header added is `X-Application-Version` (via `VersionMiddleware`).
- **Implication**: Agents cannot self-throttle based on server-side rate limit signals. If rate limiting is added (per STATE-Q5 recommendation), headers should be included.
- **Recommendation**: When rate limiting is implemented, include standard rate limit headers in responses.
- **Evidence**: `src/Lidarr.Http/Middleware/VersionMiddleware.cs`

### API-Q7: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: The system has comprehensive event emission capabilities. SignalR hubs broadcast real-time state changes (Created/Updated/Deleted/Sync) to all connected clients. A webhook subsystem supports HTTP callbacks for 12+ event types (Grab, ReleaseImport, DownloadFailure, ArtistAdd, ArtistDelete, AlbumDelete, HealthIssue, etc.). An internal EventAggregator provides in-process pub/sub. Multiple notification providers (Discord, Email, Emby, Kodi) can react to state changes.
- **Implication**: Agents can subscribe to state changes via SignalR or webhooks without polling. This is a strong foundation for event-driven agent patterns.
- **Recommendation**: Document webhook payload schemas for agent tool binding. Consider adding an event replay/history endpoint for agents to catch up on missed events.
- **Evidence**: `src/NzbDrone.SignalR/MessageHub.cs`, `src/Lidarr.Http/REST/RestControllerWithSignalR.cs`, `src/NzbDrone.Core/Notifications/Webhook/Webhook.cs`

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO (agent_scope read-only + stateful-crud archetype, but read-only scope means no write workflows)
- **Finding**: No compensation or saga patterns exist. Multi-step operations (e.g., adding an artist triggers metadata fetch, album creation, monitoring setup) have no rollback mechanism if a step fails mid-sequence. Database transactions are used for batch inserts but not for cross-service workflow compensation.
- **Implication**: If agent scope is expanded to write-enabled, partial failures in multi-step operations will leave data in inconsistent states.
- **Recommendation**: Implement compensation logic for multi-step write operations before expanding to write-enabled agent scope.
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs` (InsertMany with transactions), absence of saga/compensation patterns

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Concurrency is managed at the database level only. SQLite provides file-level locking with Polly retry (3 attempts, exponential backoff) for busy errors. No application-level optimistic locking (no version fields, no ETags, no `If-Match` headers). No `SELECT FOR UPDATE` patterns.
- **Implication**: If multiple write-enabled agents operate concurrently, race conditions could occur (e.g., two agents updating the same album simultaneously with no conflict detection).
- **Recommendation**: Add optimistic locking (version fields) to entities that agents may modify concurrently.
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs` (Polly retry for SQLite Busy)

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits exist. Bulk operations (e.g., `QueueController.RemoveMany`, `AlbumController` bulk operations) have no per-session limits on records modified.
- **Implication**: If agent scope is expanded to write-enabled, an agent error could delete or modify an unbounded number of records in a single request.
- **Recommendation**: Add configurable limits on bulk operations before enabling write-scope agents.
- **Evidence**: `src/Lidarr.Api.V1/Queue/QueueController.cs` (RemoveMany with no limit)

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No draft/pending state concept exists for most entities. Artists and albums are either fully added or not present. The download queue has status tracking (queued, downloading, imported) but this is system-driven, not approval-driven.
- **Implication**: If agent scope expands to write-enabled for high-stakes operations, there is no mechanism for human approval before commit.
- **Recommendation**: Consider adding a "proposed" state for agent-initiated additions if write scope is enabled.
- **Evidence**: `src/Lidarr.Api.V1/Albums/AlbumController.cs`, `src/NzbDrone.Core/Music/`

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No approval gate mechanism exists. All API operations execute immediately upon request — there is no configurable "require approval" flag for specific operation types.
- **Implication**: High-risk write operations (delete artist, bulk queue removal) cannot be gated behind human approval.
- **Recommendation**: Not needed for read-only agent scope. If write scope is planned, add configurable approval workflows.
- **Evidence**: Absence of approval patterns across all controllers

### DATA-Q1: Sensitive Data Classification

- **Severity**: INFO
- **Finding**: Stage A assessment: Lidarr stores user-specific data (music library metadata, artist preferences, download history, user credentials) in its database. However, the data is primarily media collection metadata — not regulated PII/PHI/financial data. User credentials (username/password hash) exist but are limited to the Lidarr instance's own authentication. The `HostConfigResource` does expose API keys and proxy passwords in responses, but this is an authenticated admin-only endpoint. B1: The API key and credentials ARE returned in the HostConfig endpoint response but it requires existing API key auth to access. B3: No formal classification metadata exists.
- **Implication**: For a read-only agent, the primary risk is the agent inadvertently reading the HostConfig endpoint and exposing the API key or credentials. Data is media metadata, not regulated data.
- **Recommendation**: Exclude `ApiKey`, `SslCertPassword`, and `ProxyPassword` fields from API responses (or return masked values). Create a separate privileged endpoint for credential management.
- **Evidence**: `src/Lidarr.Api.V1/Config/HostConfigResource.cs`, `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: INFO
- **Finding**: No identity propagation exists. All API requests authenticate via a single shared API key — there is no concept of "agent acting on behalf of user" vs "agent acting as itself." No JWT parsing, no OAuth2 on-behalf-of flows, no user context headers.
- **Implication**: Cannot distinguish agent-as-self from agent-on-behalf-of-user. All operations appear as the same identity in logs and history.
- **Recommendation**: Archetype is stateful-crud which normally evaluates this as RISK, but calibrated to INFO per archetype calibration rules (self-hosted application with single-user context — identity propagation has minimal security impact in a personal media manager).
- **Evidence**: `src/Lidarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No formal data quality scoring or completeness metrics exist. The application relies on external metadata providers (MusicBrainz, Spotify) as sources of truth. No data profiling, no null rate monitoring, no quality dashboards.
- **Implication**: Agents reasoning over Lidarr data cannot assess data completeness without checking individual fields.
- **Recommendation**: Consider adding metadata completeness indicators to artist/album resources.
- **Evidence**: Absence of data quality tooling or metrics

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No custom business metrics are published. The application tracks internal state (download counts, import counts, health checks) but does not emit metrics to an external observability platform. Health checks are exposed via the `/api/v1/health` endpoint.
- **Implication**: No visibility into agent-initiated operation outcomes at a business level. Cannot measure whether agent interactions produce good results.
- **Recommendation**: If deploying agents against Lidarr, instrument business outcome metrics (e.g., successful imports per agent session, artist additions per period).
- **Evidence**: Absence of metrics publication, `src/Lidarr.Api.V1/Health/HealthController.cs`

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: PASS (no finding)
- **Finding**: Lidarr exposes a comprehensive REST API with 75+ controllers under `/api/v1/`. A machine-readable OpenAPI 3.0.4 specification (13,101 lines) is auto-generated via Swashbuckle. All interactions happen via HTTP REST — no direct database access or file-based exchange required.
- **Gap**: None — the API surface is well-documented and accessible.
- **Recommendation**: None needed.
- **Evidence**: `src/Lidarr.Api.V1/openapi.json`, `src/Lidarr.Api.V1/` (75+ controller files)

#### API-Q2: Machine-Readable API Specification
- **Severity**: PASS (no finding)
- **Finding**: A comprehensive OpenAPI 3.0.4 specification exists at `src/Lidarr.Api.V1/openapi.json`. It is auto-generated from code annotations via Swashbuckle (NSwag/Swashbuckle 9.0.6), ensuring it stays current with the implementation. The spec covers all endpoints, request/response schemas, and authentication requirements.
- **Gap**: None — machine-readable spec exists and is auto-generated.
- **Recommendation**: None needed.
- **Evidence**: `src/Lidarr.Api.V1/openapi.json`

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section above.
- **Gap**: No machine-readable error codes or retryable indicators.
- **Recommendation**: Add `errorCode` and `retryable` fields to error response model.
- **Evidence**: `src/Lidarr.Http/ErrorManagement/LidarrErrorPipeline.cs`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No idempotency support. Write endpoints have no idempotency keys or deduplication logic.
- **Gap**: Non-idempotent writes would be a BLOCKER under write-enabled scope.
- **Recommendation**: Implement idempotency keys before expanding to write scope.
- **Evidence**: Absence of idempotency patterns in `src/Lidarr.Api.V1/`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: All responses are JSON. Well-typed resource models throughout.
- **Gap**: None.
- **Recommendation**: None needed.
- **Evidence**: `src/Lidarr.Http/REST/RestController.cs`

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has operations >30s OR long-running workflows
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: The system has comprehensive event emission capabilities. SignalR hubs broadcast real-time state changes (Created/Updated/Deleted/Sync) to all connected clients via `RestControllerWithSignalR<TResource, TModel>`. A webhook subsystem (`src/NzbDrone.Core/Notifications/Webhook/`) supports HTTP callbacks for 12+ event types (Grab, ReleaseImport, DownloadFailure, ArtistAdd, ArtistDelete, AlbumDelete, HealthIssue, etc.). An internal EventAggregator provides in-process pub/sub for domain events. Multiple notification providers (Discord, Email, Emby, Kodi) can react to state changes.
- **Implication**: Agents can subscribe to state changes via SignalR or webhooks without polling. This is a strong foundation for event-driven agent patterns.
- **Recommendation**: Document webhook payload schemas for agent tool binding. Consider adding an event replay/history endpoint.
- **Evidence**: `src/NzbDrone.SignalR/MessageHub.cs`, `src/Lidarr.Http/REST/RestControllerWithSignalR.cs`, `src/NzbDrone.Core/Notifications/Webhook/Webhook.cs`, `src/NzbDrone.Core/Notifications/Webhook/WebhookEventType.cs`, `src/NzbDrone.Core/Messaging/Events/EventAggregator.cs`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit headers or documentation. Only `X-Application-Version` header is added.
- **Gap**: Agents cannot self-throttle based on server signals.
- **Recommendation**: Include rate limit headers when rate limiting is implemented.
- **Evidence**: `src/Lidarr.Http/Middleware/VersionMiddleware.cs`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: Single shared API key with no per-caller identity attribution. See BLOCKERs section.
- **Gap**: No machine identity differentiation.
- **Recommendation**: Implement per-agent API keys with unique principal attribution.
- **Evidence**: `src/Lidarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: Binary authentication model — full access or no access. See RISKs section.
- **Gap**: No scoped permissions.
- **Recommendation**: Implement RBAC with read-only roles.
- **Evidence**: `src/Lidarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`, `src/NzbDrone.Host/Startup.cs`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization. See RISKs section.
- **Gap**: Cannot restrict read vs. write within resource types.
- **Recommendation**: Add action-level permission attributes.
- **Evidence**: `src/Lidarr.Http/Authentication/UiAuthorizationHandler.cs`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: No identity propagation — single shared key. Archetype-calibrated to INFO for stateful-crud in a single-user/self-hosted context.
- **Gap**: Cannot distinguish agent-as-self from agent-on-behalf-of-user.
- **Recommendation**: Consider if multi-user access is planned.
- **Evidence**: `src/Lidarr.Http/Authentication/ApiKeyAuthenticationHandler.cs`

#### AUTH-Q5: Credential Management
- **Severity**: RISK-QUALITY
- **Finding**: Plaintext credentials in XML config file. See RISKs section.
- **Gap**: No secrets management system, no rotation.
- **Recommendation**: Support external secrets providers.
- **Evidence**: `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Local filesystem logs with no immutability. No per-caller attribution. See RISKs section.
- **Gap**: No immutable audit trail.
- **Recommendation**: Ship logs to immutable store. Add caller identity to records.
- **Evidence**: `src/NzbDrone.Core/History/EntityHistoryRepository.cs`, `src/Lidarr.Http/Middleware/LoggingMiddleware.cs`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: Cannot suspend individual agent identities. See RISKs section.
- **Gap**: Only option is resetting the shared API key (affects all consumers).
- **Recommendation**: Support multiple independently-revocable API keys.
- **Evidence**: `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No compensation or saga patterns. Multi-step operations have no rollback.
- **Gap**: Partial failure states possible if write scope is enabled.
- **Recommendation**: Implement compensation before expanding to write scope.
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs`

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
- **Finding**: Database-level locking only (SQLite file lock + Polly retry). No application-level optimistic locking.
- **Gap**: No version fields or ETags for concurrent write protection.
- **Recommendation**: Add optimistic locking before enabling write-scope agents.
- **Evidence**: `src/NzbDrone.Core/Datastore/BasicRepository.cs`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has external dependencies (calls other services or external APIs)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No inbound rate limiting. See RISKs section.
- **Gap**: No protection against agent traffic storms.
- **Recommendation**: Add rate limiting middleware.
- **Evidence**: `src/NzbDrone.Common/TPL/RateLimitService.cs` (outbound only)

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits on bulk operations.
- **Gap**: Unbounded bulk operations possible under write scope.
- **Recommendation**: Add limits before enabling write-scope agents.
- **Evidence**: `src/Lidarr.Api.V1/Queue/QueueController.cs`

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
- **Finding**: No draft/pending state concept for agent-proposed changes.
- **Gap**: No mechanism for human approval before commit.
- **Recommendation**: Not needed for read-only scope.
- **Evidence**: `src/Lidarr.Api.V1/Albums/AlbumController.cs`

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No approval gate mechanism.
- **Gap**: Operations execute immediately upon request.
- **Recommendation**: Not needed for read-only scope.
- **Evidence**: Absence of approval patterns

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: A devcontainer configuration exists (`.devcontainer/devcontainer.json`) providing a development environment with .NET 8 and Node.js 20. The CI pipeline uses ephemeral environments for testing. However, there is no documented staging environment with production-equivalent data shape for agent testing.
- **Gap**: No staging environment with production-like data for agent behavior validation.
- **Recommendation**: Create a Docker-based staging setup with seed data that mirrors production data shape for agent testing.
- **Evidence**: `.devcontainer/devcontainer.json`, `azure-pipelines.yml` (test stages)

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification ⚡
- **Severity**: INFO
- **Finding**: Stage A: Lidarr stores user-specific media metadata (not regulated PII/PHI/financial). Credentials exist but are limited scope. Overall assessed as INFO for read-only agent scope against media metadata. See INFOs section for details.
- **Gap**: HostConfig endpoint returns sensitive credentials unmasked.
- **Recommendation**: Mask credentials in API responses.
- **Evidence**: `src/Lidarr.Api.V1/Config/HostConfigResource.cs`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No residency controls. Data location depends on deployment. See RISKs section.
- **Gap**: No data residency enforcement.
- **Recommendation**: Document residency characteristics. Keep agent-LLM communication in-region.
- **Evidence**: `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs`

#### DATA-Q3: Selective Query Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has list/query endpoints with potentially unbounded results
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

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
- **Finding**: No PII scrubbing in logs. Stack traces in error responses. See RISKs section.
- **Gap**: No log redaction mechanism.
- **Recommendation**: Add PII redaction middleware.
- **Evidence**: `src/Lidarr.Http/Middleware/LoggingMiddleware.cs`, `src/Lidarr.Http/ErrorManagement/LidarrErrorPipeline.cs`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics. Relies on external metadata providers.
- **Gap**: No completeness or freshness indicators.
- **Recommendation**: Consider adding metadata completeness indicators.
- **Evidence**: Absence of data quality tooling

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: API versioned via URL path. OpenAPI spec auto-generated. No breaking change detection in CI. See RISKs section.
- **Gap**: No automated breaking change detection.
- **Recommendation**: Add OpenAPI diff to CI.
- **Evidence**: `src/Lidarr.Api.V1/openapi.json`, `azure-pipelines.yml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Field names throughout the codebase are human-readable and semantically clear: `ArtistName`, `AlbumTitle`, `TrackNumber`, `QualityProfile`, `MonitoredItems`. No legacy abbreviations or codes requiring a data dictionary.
- **Implication**: Agent LLM reasoning can interpret field names directly without mapping.
- **Recommendation**: None needed. Naming conventions are already agent-friendly.
- **Evidence**: `src/Lidarr.Api.V1/` resource files, `src/Lidarr.Api.V1/openapi.json`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal data catalog exists. The OpenAPI specification serves as the primary schema documentation. Database schema is documented implicitly through FluentMigrator migration files (80 migrations).
- **Implication**: Agent tool builders must derive data semantics from the OpenAPI spec and resource model documentation.
- **Recommendation**: The OpenAPI spec is sufficient for agent tool generation. No additional catalog needed for this use case.
- **Evidence**: `src/Lidarr.Api.V1/openapi.json`, `src/NzbDrone.Core/Datastore/Migration/`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: NLog with file output and optional CLEF structured JSON. No distributed tracing. No correlation IDs. See RISKs section.
- **Gap**: Cannot trace agent-initiated requests through the system.
- **Recommendation**: Add OpenTelemetry instrumentation.
- **Evidence**: `src/NzbDrone.Common/Instrumentation/NzbDroneLogger.cs`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: No alerting configured. Sentry captures errors but no threshold alerts. See RISKs section.
- **Gap**: No proactive degradation detection.
- **Recommendation**: Configure alerting via Sentry or external monitoring.
- **Evidence**: Absence of alerting configuration

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics published externally. Internal health checks only.
- **Implication**: No visibility into agent interaction outcomes.
- **Recommendation**: Instrument business metrics if deploying agents.
- **Evidence**: Absence of metrics publication

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance
- **Severity**: RISK-QUALITY
- **Finding**: No IaC. Self-hosted application with manual deployment. See RISKs section.
- **Gap**: No codified infrastructure for the agent-facing surface.
- **Recommendation**: Create IaC for the deployment environment.
- **Evidence**: `distribution/` (installers only)

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive CI/CD pipeline but no API contract testing. See RISKs section.
- **Gap**: API changes not validated against consumer contracts.
- **Recommendation**: Add OpenAPI validation and diff to CI.
- **Evidence**: `azure-pipelines.yml`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: No automated rollback. Manual re-installation required. See RISKs section.
- **Gap**: No fast automated rollback.
- **Recommendation**: Use container-based deployment with version pinning.
- **Evidence**: `src/NzbDrone.Update/`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: Integration tests exist in `src/NzbDrone.Integration.Test/ApiTests/` covering major API resources (Artist, Album, Track, DownloadClient, Indexer, Notification, Release, Command, Calendar, History, Blocklist, RootFolder, etc.) with typed REST clients. Azure Pipelines CI (`azure-pipelines.yml`) builds and publishes test packages across platforms with a dedicated `Unit_Test` stage. However, there is no consumer-driven contract testing (Pact), no OpenAPI schema validation in CI, and no automated breaking-change detection for API responses.
- **Gap**: No API contract testing or schema-breaking-change detection in CI. Tests validate functional behavior but do not guard against schema drift that would break agent tool bindings.
- **Recommendation**: Add OpenAPI spec diff validation to the CI pipeline. Consider consumer-driven contract tests (Pact) for agent-facing endpoints.
- **Evidence**: `src/NzbDrone.Integration.Test/ApiTests/`, `src/NzbDrone.Integration.Test/Client/ClientBase.cs`, `azure-pipelines.yml`

#### ENG-Q5: Encryption at Rest
- **Severity**: RISK-QUALITY
- **Finding**: No encryption at rest. Unencrypted SQLite files. No TLS enforcement on PostgreSQL. See RISKs section.
- **Gap**: Data at rest unencrypted.
- **Recommendation**: Use OS-level disk encryption. Enforce TLS for PostgreSQL.
- **Evidence**: `src/NzbDrone.Core/Datastore/DbFactory.cs`

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `src/Lidarr.Http/Authentication/ApiKeyAuthenticationHandler.cs` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4 |
| `src/Lidarr.Http/Authentication/AuthenticationService.cs` | AUTH-Q6 |
| `src/Lidarr.Http/Authentication/UiAuthorizationHandler.cs` | AUTH-Q3 |
| `src/Lidarr.Http/REST/RestController.cs` | API-Q3, API-Q5 |
| `src/Lidarr.Http/Middleware/LoggingMiddleware.cs` | AUTH-Q6, DATA-Q6, OBS-Q1 |
| `src/Lidarr.Http/Middleware/VersionMiddleware.cs` | API-Q8 |
| `src/Lidarr.Http/ErrorManagement/LidarrErrorPipeline.cs` | API-Q3, DATA-Q6 |
| `src/NzbDrone.Host/Startup.cs` | AUTH-Q2, STATE-Q5 |
| `src/NzbDrone.Core/Datastore/BasicRepository.cs` | STATE-Q1, STATE-Q3 |
| `src/NzbDrone.Core/Datastore/DbFactory.cs` | DATA-Q2, ENG-Q5 |
| `src/NzbDrone.Core/Datastore/ConnectionStringFactory.cs` | DATA-Q2, ENG-Q5 |
| `src/NzbDrone.Core/Configuration/ConfigFileProvider.cs` | AUTH-Q1, AUTH-Q5, AUTH-Q7 |
| `src/NzbDrone.Core/History/EntityHistoryRepository.cs` | AUTH-Q6 |
| `src/NzbDrone.Common/TPL/RateLimitService.cs` | STATE-Q5 |
| `src/NzbDrone.Common/Instrumentation/NzbDroneLogger.cs` | OBS-Q1, OBS-Q2 |
| `src/Lidarr.Api.V1/Config/HostConfigResource.cs` | DATA-Q1, DATA-Q6 |
| `src/Lidarr.Api.V1/Queue/QueueController.cs` | STATE-Q6 |
| `src/Lidarr.Api.V1/Albums/AlbumController.cs` | HITL-Q1 |
| `src/NzbDrone.SignalR/MessageHub.cs` | API-Q7 |
| `src/Lidarr.Http/REST/RestControllerWithSignalR.cs` | API-Q7 |
| `src/NzbDrone.Core/Notifications/Webhook/Webhook.cs` | API-Q7 |
| `src/NzbDrone.Core/Notifications/Webhook/WebhookEventType.cs` | API-Q7 |
| `src/NzbDrone.Core/Messaging/Events/EventAggregator.cs` | API-Q7 |
| `src/NzbDrone.Integration.Test/ApiTests/` | ENG-Q4 |
| `src/NzbDrone.Integration.Test/Client/ClientBase.cs` | ENG-Q4 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `src/Lidarr.Api.V1/openapi.json` | API-Q1, API-Q2, DISC-Q1, DISC-Q2, DISC-Q3 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `azure-pipelines.yml` | ENG-Q2, ENG-Q3, ENG-Q4, DISC-Q1, HITL-Q3 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `.devcontainer/devcontainer.json` | HITL-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `src/NzbDrone.Core/Datastore/Migration/` (80 files) | DISC-Q1 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `distribution/debian/install.sh` | ENG-Q1 |
| `distribution/debian/lidarr.service` | ENG-Q1 |
