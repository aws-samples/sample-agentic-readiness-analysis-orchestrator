# Agentic Readiness Assessment Report

**Target**: Graylog2--graylog2-server
**Date**: 2025-05-08
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: java, observability, logging
**Context**: Graylog centralized log-management server.

**Archetype Justification**: Graylog owns persistent state in MongoDB (users, streams, dashboards, event definitions, content packs) and exposes full CRUD operations via 187+ JAX-RS REST endpoints across 14 resource groups. The system also manages OpenSearch/Elasticsearch indexes with lifecycle operations.

**Surface flags**:
- has_persistent_data_store: true
- has_http_rpc_surface: true
- has_auth_surface: true
- has_write_operations: true
- has_logging_of_user_data: true

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 1 | **RISK-SAFETY**: 5 | **RISK-QUALITY**: 9 | **INFOs**: 17

This repo has 1 BLOCKER, which places it in the "Remediation Required" tier. Resolve the blocker before any agent deployment — including pilots.

**Classification Rationale**: AUTH-Q6 resolves to BLOCKER because the open-source edition ships with `NullAuditEventSender` which discards all audit events — while machine identity via access tokens exists, the inability to immutably log agent actions in the OSS deployment creates an unresolvable attribution gap. With 1 High finding and 5 safety-impact Medium findings, the V6 rule "1-2 High → Remediation Required" applies.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 1 |
| RISK-SAFETY | 5 |
| RISK-QUALITY | 9 |
| INFO | 17 |
| Pass | 2 |
| N/A | 0 |
| Not Evaluated (extended) | 9 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 10
**Extended Questions Not Triggered**: 9
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: stateful-crud (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q6: Immutable Audit Logging ⚡

- **Severity**: BLOCKER (conditional resolved to RISK-SAFETY for read-only scope — however, this is elevated to BLOCKER because the open-source edition has NO audit logging at all, not even mutable logging)
- **Finding**: The open-source edition ships with `NullAuditEventSender` — a no-op implementation that silently discards all audit events. While the audit framework defines 100+ event types and integrates with REST endpoints via `@AuditEvent` annotations, no audit events are actually persisted. The comprehensive framework exists but is entirely non-functional in OSS.
- **Gap**: No audit trail whatsoever for any operation — read or write — in the open-source deployment. Agent-initiated requests cannot be attributed or forensically traced.
- **Remediation**:
  - **Immediate**: Implement a `MongoAuditEventSender` that persists audit events to a dedicated MongoDB collection. The framework already defines all event types and integrations — only the persistence layer is missing.
  - **Target State**: All API operations log the authenticated principal, action, resource, and timestamp to an append-only audit collection with TTL-based retention.
  - **Estimated Effort**: Medium
  - **Dependencies**: None — the audit framework is fully wired; only the sender implementation needs replacing.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/audit/NullAuditEventSender.java`, `graylog2-server/src/main/java/org/graylog2/audit/AuditEventSender.java`, `graylog2-server/src/main/java/org/graylog2/audit/AuditEventTypes.java`

---

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Graylog implements a fine-grained permission model with 100+ permissions in `domain:action` format (e.g., `users:create`, `streams:read`) and supports per-instance scoping (e.g., `streams:read:stream-id`). Built-in roles (Reader, Admin) and GRN-based capability mapping (view/manage/own) provide resource-level access control. However, there is no dedicated "agent" role template with minimal permissions pre-configured.
- **Gap**: While the permission system is granular, there is no documented guidance or pre-built role for agent identities with least-privilege defaults. An admin creating an agent token must manually determine the minimal permission set.
- **Compensating Controls**:
  - Create a custom "Agent Reader" role with explicit minimal permissions (e.g., `searches:read`, `streams:read`, `messages:read`) and document it as the standard agent role.
  - Use the GRN-based capability system to grant `view` capability only on specific resources the agent needs.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Define and document a least-privilege agent role template that restricts agent tokens to only the API operations required for the intended use case.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/shared/security/RestPermissions.java`, `graylog2-server/src/main/java/org/graylog2/shared/security/Permissions.java`

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The permission model supports action-level granularity (`streams:read` vs `streams:edit` vs `streams:delete`). Jersey resource methods enforce permissions via Shiro's `@RequiresPermissions` annotations and programmatic `isPermitted()` checks. GRN capabilities (view/manage/own) provide an additional layer. However, the coarse admin role bypasses all action-level checks — admin tokens have unrestricted access.
- **Gap**: No mechanism to restrict an admin-created agent token to read-only operations if the creating user is an admin. The permission model works for scoped roles but the admin bypass is a blast-radius risk for agent tokens created by administrators.
- **Compensating Controls**:
  - Always create agent tokens under a non-admin user account with explicitly scoped roles.
  - Use the Reader role as the base for agent identities, adding only specific additional permissions as needed.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Enforce that agent tokens cannot inherit admin privileges regardless of the creating user's role. Add a token-level permission restriction that caps token privileges below admin level.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/rest/resources/users/UsersResource.java`, `graylog2-server/src/main/java/org/graylog2/shared/security/RestPermissions.java`

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: `UserSessionTerminationService` supports both global session termination (revision bump forcing re-auth) and per-user termination via EventBus when accounts are disabled/deleted. Access tokens can be individually deleted. However, there is no API endpoint to immediately revoke a specific access token by token value without knowing which user owns it, and token revocation does not propagate instantly to in-flight requests using cached sessions.
- **Gap**: No single "kill switch" API to suspend a specific agent identity by token identifier. Suspension requires identifying the user, then deleting the token, then terminating sessions — a multi-step process with potential delay.
- **Compensating Controls**:
  - Disable the user account associated with the agent token — triggers automatic session termination across the cluster.
  - Use short-lived tokens with TTL to limit exposure window.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement a token revocation endpoint that accepts a token identifier and immediately invalidates it across all cluster nodes without requiring user identification first.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/security/UserSessionTerminationService.java`, `graylog2-server/src/main/java/org/graylog2/security/AccessTokenServiceImpl.java`

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No API-layer rate limiting exists in the application. No rate limiting middleware, throttling configuration, 429 response handling, or rate limit headers (`X-RateLimit-Remaining`, `Retry-After`) were found. The only rate-related code is `RateLimitedLog` which throttles log output, not API requests.
- **Gap**: A runaway agent loop or misconfigured agent could make thousands of API calls per second with no throttling. The system has no defense against agent-induced traffic storms at the application layer.
- **Compensating Controls**:
  - Deploy Graylog behind a reverse proxy (nginx, HAProxy) or API gateway with rate limiting configured per client/token.
  - Use network-level controls (firewall rules, WAF) to throttle agent IP ranges.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement per-token rate limiting at the Jersey filter level, with configurable limits per permission role. Return 429 with `Retry-After` header when limits are exceeded.
- **Evidence**: No rate limiting code found in `graylog2-server/src/main/java/org/graylog2/rest/` or Jersey filter configurations.

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Logging uses Log4j2 with plain-text `PatternLayout` (`%d %-5p: %c - %m%n`). No structured JSON logging is configured. No PII scrubbing, masking, or redaction filters exist in the logging pipeline. User identifiers (usernames, email addresses) may be logged in authentication events and error messages without any redaction.
- **Gap**: No mechanism to prevent PII from appearing in application logs. Agent-initiated requests that trigger error paths may log request details including user-related fields.
- **Compensating Controls**:
  - Configure log rotation with strict access controls and short retention periods.
  - Deploy a log aggregation pipeline with PII scrubbing (e.g., AWS CloudWatch with data protection policies) between Graylog server logs and long-term storage.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add a Log4j2 `RewritePolicy` or custom `LogEvent` filter that redacts known PII patterns (email, IP addresses) before log output. Consider switching to `JsonTemplateLayout` for structured logging.
- **Evidence**: `graylog2-server/src/main/resources/log4j2.xml`

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: One hand-authored OpenAPI 3.1.0 spec exists (`api-specs/stream-output-filters.yml`) covering only stream destination filter endpoints. The build system can generate a comprehensive OpenAPI spec from code annotations (Maven `generate-openapi` profile), but the generated spec is a build artifact (`target/openapi.yaml`) not committed to the repository.
- **Gap**: No complete, version-controlled API specification exists. The 187+ REST endpoints are documented only via JAX-RS annotations and Swagger/OpenAPI annotations in code, requiring a build to produce a usable spec.
- **Compensating Controls**:
  - Run the Maven `generate-openapi` profile to produce the full spec and commit it to the repository.
  - Use the build-generated spec as the source of truth for agent tool definition generation.
- **Remediation Timeline**: 30 days
- **Recommendation**: Add a CI step that generates and commits the OpenAPI spec on each release, ensuring a version-controlled machine-readable API definition is always available.
- **Evidence**: `api-specs/stream-output-filters.yml`, `graylog2-server/pom.xml` (generate-openapi profile)

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The API has a well-defined error response hierarchy based on the `GenericError` interface with JSON type discrimination. 14 `ExceptionMapper` classes provide consistent mapping from exceptions to HTTP status codes (NotFoundException → 404, ValidationException → 400, etc.). `ApiError` provides `{"type": "ApiError", "message": "..."}`. `ValidationApiError` includes field-level error details. However, no `retryable` field, error code enumeration, or machine-readable error category is included in error responses.
- **Gap**: Error responses lack a `retryable` flag or error code that agents can use to distinguish transient failures from permanent errors. Agents must infer retry behavior from HTTP status codes alone.
- **Compensating Controls**:
  - Document which HTTP status codes are retriable (503, 429) vs terminal (400, 403, 404) in agent tool definitions.
  - Agent orchestration layer can maintain a status-code-to-retry mapping.
- **Remediation Timeline**: 60 days
- **Recommendation**: Add a `code` field (string enum) and `retryable` boolean to the `GenericError` interface to give agents machine-readable error classification.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/rest/GenericError.java`, `graylog2-server/src/main/java/org/graylog2/rest/models/system/responses/` (ExceptionMapper classes)

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: OpenTelemetry integration exists via `TracerProvider` (uses `GlobalOpenTelemetry.get().getTracer("org.graylog")`) with 11 custom semantic attributes covering system operations. The implementation relies on an external Java agent for trace export (falling back to no-op if absent). However, logging is plain-text only (no JSON/structured format), no `correlation_id` or `trace_id` fields are injected into log entries, and trace context propagation through HTTP headers is not evident in the REST layer.
- **Gap**: Tracing exists but is optional (requires external agent). Logs are unstructured and not correlated with traces. An agent-initiated request cannot be easily traced end-to-end through log analysis.
- **Compensating Controls**:
  - Deploy with the OpenTelemetry Java agent to enable trace export.
  - Correlate traces via the OTel agent's automatic trace-id log injection (requires switching to a layout that supports MDC fields).
- **Remediation Timeline**: 60 days
- **Recommendation**: Enable OTel auto-instrumentation for JAX-RS endpoints and switch Log4j2 to `JsonTemplateLayout` with trace context fields (`trace_id`, `span_id`) injected from MDC.
- **Evidence**: `graylog2-server/src/main/java/org/graylog/tracing/TracerProvider.java`, `graylog2-server/src/main/resources/log4j2.xml`

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Prometheus metrics are extensively configured with 100+ metric mappings (`prometheus-exporter.yml`) covering streams, inputs, buffers, journal, search/indexing, pipelines, event processing, and traffic. The `@Timed` annotation on REST endpoints generates latency metrics. However, no alerting configuration (Prometheus alerting rules, PagerDuty/OpsGenie integration, or CloudWatch alarms) is defined in the repository.
- **Gap**: Metrics are collected but no alerting thresholds or anomaly detection are configured within the application or its deployment artifacts. Alerting must be configured externally.
- **Compensating Controls**:
  - Configure Prometheus Alertmanager rules externally to alert on p99 latency and error rate thresholds on the Graylog API endpoints.
  - Use Graylog's own alerting system to monitor its own metrics (self-monitoring).
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a `prometheus-alerts.yml` reference configuration with recommended alerting thresholds for API latency, error rates, and throughput anomalies.
- **Evidence**: `graylog2-server/src/main/resources/prometheus-exporter.yml`

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The API does not use URL-based versioning (`/v1/`, `/v2/`), `Accept-Version` headers, or a schema registry. No consumer-driven contract tests (Pact) or breaking change detection tools are present in CI. The `UPGRADING.md` file documents breaking changes between major versions, but there is no automated mechanism to detect or prevent breaking changes in the API surface.
- **Gap**: Agent tool bindings could break silently when the API changes between versions. No automated contract testing or schema comparison exists in the CI pipeline.
- **Compensating Controls**:
  - Pin agent tool definitions to a specific Graylog version and re-validate on upgrade using the generated OpenAPI spec diff.
  - Use `UPGRADING.md` as a manual contract change log for major version transitions.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add OpenAPI spec comparison (e.g., `oasdiff`) to the CI pipeline to detect and flag breaking changes before merge.
- **Evidence**: `UPGRADING.md`, `.github/workflows/build.yml` (no contract testing steps)

#### ENG-Q1: Infrastructure Governance — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No Infrastructure as Code exists in this repository. No Terraform, CloudFormation, CDK, Helm charts, or Kubernetes manifests are present. Deployment infrastructure is managed externally. The repository contains only the application code, build configuration, and test Docker Compose files for development.
- **Gap**: The infrastructure that would expose Graylog APIs to agents (API gateways, load balancers, network policies, IAM roles) is not defined or governed in this repository. Infrastructure changes cannot be reviewed in the context of the application code.
- **Compensating Controls**:
  - Ensure the external infrastructure repository containing Graylog deployment artifacts has IaC governance (peer review, drift detection).
  - Document the expected deployment topology for agent access.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add a reference Helm chart or Docker Compose deployment configuration to the repository that documents the expected production topology, including API gateway and rate limiting configuration.
- **Evidence**: No IaC files found in the repository. Docker Compose files exist only in `data-node/migration/` for testing.

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: GitHub Actions CI runs Maven verify with unit tests, integration tests (Testcontainers), and SpotBugs analysis across 4 parallel jobs. Frontend tests run Jest. However, no API contract testing (Pact, OpenAPI diff, schema validation) is present in the pipeline. No step validates that API changes are backward-compatible.
- **Gap**: The CI pipeline does not detect API-breaking changes. An endpoint signature change could be merged without alerting downstream consumers (including agent tool definitions).
- **Compensating Controls**:
  - Generate and diff OpenAPI specs as part of the PR review process (manual).
  - Integration tests against API endpoints provide some regression detection but not formal contract validation.
- **Remediation Timeline**: 60 days
- **Recommendation**: Add a CI step that generates the OpenAPI spec and compares it against the committed baseline, failing the build on backward-incompatible changes.
- **Evidence**: `.github/workflows/build.yml`

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Database migrations are forward-only (75 migrations with `upgrade()` method, no `downgrade()`). Content pack operations support rollback (`ContentPackService.rollback()` deletes created entities on failure). However, no deployment rollback mechanisms (blue/green, canary, feature flags for API versions, CodeDeploy rollback triggers) are defined in the repository.
- **Gap**: A broken release that changes API behavior cannot be quickly rolled back at the deployment level from within this repository. MongoDB's schema-less nature reduces migration risk, but application logic changes are not reversible.
- **Compensating Controls**:
  - External deployment infrastructure should provide rollback capability (container image versioning, load balancer traffic shifting).
  - Keep previous version's container image tagged for quick revert.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document the rollback procedure and ensure the external deployment system supports one-click rollback to the previous Graylog version.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/migrations/` (forward-only), `graylog2-server/src/main/java/org/graylog2/contentpacks/ContentPackService.java`

---

## INFOs — Architecture and Design Inputs

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No idempotency key support exists in write endpoints. POST operations (e.g., creating streams, users, dashboards) do not support idempotency keys or duplicate request detection.
- **Implication**: If the agent scope expands to write-enabled, non-idempotent write endpoints will create duplicate records on retry. This becomes a BLOCKER under write-enabled scope.
- **Recommendation**: Implement idempotency key support (via `Idempotency-Key` header) on critical write endpoints before expanding agent scope to write-enabled.
- **Evidence**: No idempotency patterns found in `graylog2-server/src/main/java/org/graylog2/rest/`

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: All API responses use structured JSON (Jackson serialization). Content-Type is `application/json`. DTOs are well-defined with AutoValue/Jackson annotations. Pagination responses wrap entities in a standard structure with metadata.
- **Implication**: JSON responses are well-suited for LLM consumption and agent tool output parsing.
- **Recommendation**: No action needed — JSON is the optimal format for agent consumption.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/rest/models/` (DTO layer)

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limit documentation exists and no rate limit headers (`X-RateLimit-Remaining`, `Retry-After`) are returned in API responses. The application does not enforce or communicate rate limits.
- **Implication**: Agents cannot self-throttle based on rate limit signals. Agent orchestration must implement external rate limiting awareness.
- **Recommendation**: When rate limiting is implemented (see STATE-Q5), include standard rate limit headers in all API responses.
- **Evidence**: No rate limit headers found in response construction code.

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Content pack operations support rollback on failure. Individual entity handlers (EventDefinitionHandler, NotificationResourceHandler) implement compensation logic. However, no general-purpose saga pattern or multi-step transaction compensation framework exists for arbitrary API operations.
- **Implication**: Under write-enabled scope, this becomes a BLOCKER — multi-step agent workflows (e.g., create stream + create pipeline + connect them) cannot be atomically rolled back if a later step fails.
- **Recommendation**: Before expanding to write-enabled scope, implement compensation endpoints or saga coordination for critical multi-step workflows.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/contentpacks/ContentPackService.java`

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: MongoDB atomic operations (`findAndModify`, conditional updates) are used in some areas. `MongoCollection.getOrCreate()` provides atomic upsert. No application-level optimistic locking (ETags, version fields) is implemented on REST endpoints. DynamoDB conditional writes are not applicable (MongoDB backend).
- **Implication**: Under write-enabled scope, concurrent agent writes could cause race conditions on entities without version-field protection.
- **Recommendation**: Add `version` fields and `If-Match` ETag support on write endpoints before enabling write scope for agents.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/database/MongoCollections.java`

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits exist per agent identity. No maximum records per operation, maximum spend per hour, or similar blast-radius controls are implemented.
- **Implication**: Under write-enabled scope, an agent could perform unbounded bulk operations (e.g., delete all streams, modify all pipelines) with no safety limit.
- **Recommendation**: Implement per-token operation limits before expanding to write-enabled scope.
- **Evidence**: No transaction limit configuration found in the codebase.

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No draft/pending state exists for most entity types. Content packs have a versioning/installation model that provides review before activation, but standard entities (streams, dashboards, pipelines) are immediately active on creation.
- **Implication**: Under write-enabled scope, agents would immediately commit changes without human review opportunity.
- **Recommendation**: Consider a draft state for agent-created entities before expanding to write-enabled scope.
- **Evidence**: No draft status fields found in entity models.

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable approval gates exist for high-risk operations. All authorized API operations execute immediately.
- **Implication**: Under write-enabled scope, destructive operations (delete stream, modify pipeline) have no human-in-the-loop safety net at the application layer.
- **Recommendation**: Add operation-level approval requirements (configurable per operation type) before enabling write scope.
- **Evidence**: No approval workflow patterns found in REST resources.

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: INFO
- **Finding**: Graylog's access token system authenticates the token bearer as the owning user — the token acts as a static credential for a specific user identity. There is no OAuth2 on-behalf-of flow or token exchange pattern. The system cannot distinguish "agent acting as itself" vs "agent acting on behalf of user X" at the protocol level.
- **Implication**: Agent tool calls will appear as the user who owns the token. Multi-tenant agent scenarios (agent serving multiple users) would require separate tokens per user.
- **Recommendation**: For read-only agent use cases, a dedicated agent user account with a scoped token is sufficient. On-behalf-of flows are not required for the current scope.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/security/realm/AccessTokenAuthenticator.java`

### AUTH-Q5: Credential Management

- **Severity**: INFO
- **Finding**: Access tokens are encrypted at rest using AES-SIV (RFC 5297) in MongoDB. General secrets use AES-CBC encryption via `EncryptedValueService`. The master encryption key (`password_secret`) is stored in the `graylog.conf` configuration file. No HSM or external key management system (Vault, AWS KMS) integration exists. SMTP credentials are stored in plaintext in configuration.
- **Implication**: The master key in a config file is acceptable for self-hosted deployments with OS-level access controls. For cloud deployments where agents access Graylog, external secret management would strengthen the security posture.
- **Recommendation**: Consider Vault or AWS Secrets Manager integration for the `password_secret` and other sensitive configuration values in production deployments.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/security/AccessTokenCipher.java`, `graylog2-server/src/main/java/org/graylog2/security/encryption/EncryptedValueService.java`, `misc/graylog.conf`

### DATA-Q2: Data Residency and Sovereignty ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY, but further calibrated: no data residency requirements are documented or configured in the codebase, and the system is self-hosted (data stays where deployed). Evaluated as INFO because the deployment model is operator-controlled — the operator decides where to host Graylog and its MongoDB/OpenSearch data stores.
- **Finding**: No GDPR, data residency, or data sovereignty configuration exists in the codebase. No region-specific data routing. The system is self-hosted, meaning data residency is determined by the operator's deployment location, not by application configuration.
- **Implication**: For agent integration, the operator must ensure that any LLM endpoint the agent sends data to respects the same jurisdictional boundaries as the Graylog deployment. This is a deployment-time concern, not an application-level gap.
- **Recommendation**: Document data residency requirements in the deployment guide for organizations using Graylog with AI agents.
- **Evidence**: No GDPR/residency configuration found in the codebase.

### API-Q7: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: Graylog has robust event emission capabilities: internal EventBus for state changes, outbound HTTP notifications (`HTTPEventNotificationV2`), Slack/Teams webhooks, and configurable event definitions that trigger notifications on log-based conditions. URL allowlisting provides security controls on outbound webhooks.
- **Implication**: Agents can subscribe to Graylog events via HTTP webhooks, enabling reactive agent patterns without polling. The event system is mature and production-ready.
- **Recommendation**: Document webhook payload schemas for agent consumption. Consider adding a standardized event schema for agent-relevant state changes.
- **Evidence**: `graylog2-server/src/main/java/org/graylog/events/notifications/types/HTTPEventNotificationV2.java`

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No formal data quality scoring, completeness metrics, or data profiling exists. The system processes incoming log data without quality assessment. Indexer failure handling exists (failure indexer, dead letter patterns) for processing failures.
- **Implication**: Agents querying Graylog cannot assess data completeness or freshness at a metadata level. They must trust that indexed data represents the full picture.
- **Recommendation**: Consider adding data freshness indicators to search responses (latest indexed timestamp, index lag metrics).
- **Evidence**: `graylog2-server/src/main/java/org/graylog/failure/`

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: Prometheus metrics cover infrastructure and processing metrics (message throughput, buffer utilization, indexing rates, search latency). Custom business-outcome metrics (e.g., alert quality, time-to-detection, resolution rates) are not emitted by the application itself — these are emergent properties of how the system is used.
- **Implication**: When agents interact with Graylog, measuring whether agent queries produce good outcomes (accurate results, useful insights) requires external metric definition.
- **Recommendation**: Define agent-specific success metrics externally (e.g., percentage of agent queries returning non-empty results, average relevance score).
- **Evidence**: `graylog2-server/src/main/resources/prometheus-exporter.yml`

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: PASS (no finding)
- **Finding**: Graylog exposes a comprehensive REST API via 187+ JAX-RS resource classes across 14 resource groups (cluster, streams, system, tools, users, etc.). Endpoints use standard annotations (`@Path`, `@GET/@POST/@PUT/@DELETE`, `@Produces("application/json")`). An MCP (Model Context Protocol) server endpoint is also available at `/mcp` exposing 12 tools and 3 resource types for direct agent integration.
- **Gap**: None — a well-documented API interface exists.
- **Recommendation**: The existing API surface is suitable for agent tool binding. The MCP endpoint provides a direct agent integration path.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/rest/resources/`, `graylog2-server/src/main/java/org/graylog/mcp/server/McpRestResource.java`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: One hand-authored OpenAPI 3.1.0 spec exists covering stream destination filters only. A build-time OpenAPI generation capability exists but the output is not committed.
- **Gap**: No complete, version-controlled machine-readable API specification.
- **Recommendation**: Commit the build-generated OpenAPI spec to the repository and keep it updated in CI.
- **Evidence**: `api-specs/stream-output-filters.yml`, `graylog2-server/pom.xml`

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: Well-structured error hierarchy with `GenericError` interface, JSON type discrimination, and 14 ExceptionMapper classes. Missing `retryable` flag and error code enumeration.
- **Gap**: No machine-readable retry/error classification in response bodies.
- **Recommendation**: Add `code` enum and `retryable` boolean to error responses.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/rest/GenericError.java`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No idempotency key support exists in write endpoints.
- **Gap**: Non-idempotent write operations (becomes BLOCKER under write-enabled scope).
- **Recommendation**: Implement idempotency keys before expanding agent scope.
- **Evidence**: No idempotency patterns found in REST resources.

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: All API responses use structured JSON with well-defined DTOs.
- **Gap**: None.
- **Recommendation**: No action needed.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/rest/models/`

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has operations >30s OR long-running workflows
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: Robust event emission via internal EventBus, outbound HTTP webhooks, Slack/Teams notifications, and configurable event definitions.
- **Gap**: None — event emission capability is mature.
- **Recommendation**: Document webhook payload schemas for agent consumption.
- **Evidence**: `graylog2-server/src/main/java/org/graylog/events/notifications/types/HTTPEventNotificationV2.java`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit documentation or headers exist.
- **Gap**: Agents cannot self-throttle based on rate limit signals.
- **Recommendation**: Add rate limit headers when rate limiting is implemented.
- **Evidence**: No rate limit headers found.

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: PASS (no finding)
- **Finding**: Graylog supports machine identity authentication via access tokens (256-bit random values, base-32 encoded, encrypted at rest with AES-SIV). Tokens are associated with specific user accounts and support configurable TTL with expiration. The `AccessTokenAuthenticator` Shiro realm validates tokens and attributes requests to the owning user. The MCP endpoint requires `@RequiresAuthentication` and specific `mcp_server:access` permission.
- **Gap**: None — machine identity authentication with principal attribution exists and functions correctly.
- **Recommendation**: Create dedicated user accounts for agent identities rather than reusing human user tokens.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/security/realm/AccessTokenAuthenticator.java`, `graylog2-server/src/main/java/org/graylog2/security/AccessTokenServiceImpl.java`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: 100+ fine-grained permissions with per-instance scoping. No pre-built agent role template.
- **Gap**: No documented least-privilege agent role.
- **Recommendation**: Define agent role templates.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/shared/security/RestPermissions.java`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: Action-level granularity exists (`read` vs `edit` vs `delete`) but admin bypass circumvents all checks.
- **Gap**: Admin tokens bypass action-level enforcement.
- **Recommendation**: Enforce token-level permission caps below admin.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/shared/security/RestPermissions.java`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: Token authentication maps to owning user. No on-behalf-of flow.
- **Gap**: Cannot distinguish agent-as-self vs agent-on-behalf-of-user.
- **Recommendation**: Dedicated agent user account with scoped token is sufficient for read-only scope.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/security/realm/AccessTokenAuthenticator.java`

#### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: Tokens encrypted at rest (AES-SIV). Master key in config file. No HSM/KMS integration.
- **Gap**: No external key management integration.
- **Recommendation**: Consider Vault/KMS for production deployments.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/security/AccessTokenCipher.java`, `misc/graylog.conf`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: BLOCKER
- **Conditional**: agent_scope is "read-only" — base severity is RISK-SAFETY. However, the open-source edition has NO audit logging at all (NullAuditEventSender discards all events), which escalates this to BLOCKER regardless of scope — you cannot attribute ANY operation to ANY principal.
- **Finding**: `NullAuditEventSender` discards all audit events. No audit trail exists in the OSS edition.
- **Gap**: Complete absence of audit logging in any form.
- **Recommendation**: Implement a persistent audit event sender.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/audit/NullAuditEventSender.java`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: Session termination and token deletion exist but require multi-step process.
- **Gap**: No single-operation token revocation API.
- **Recommendation**: Implement direct token revocation endpoint.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/security/UserSessionTerminationService.java`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Content pack rollback exists. No general saga pattern.
- **Gap**: No general multi-step compensation framework.
- **Recommendation**: Implement before expanding to write-enabled scope.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/contentpacks/ContentPackService.java`

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
- **Finding**: MongoDB atomic operations used. No application-level optimistic locking on REST.
- **Gap**: No ETag/version field support on endpoints.
- **Recommendation**: Add version fields before enabling write scope.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/database/MongoCollections.java`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has external dependencies (calls other services or external APIs)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No API-layer rate limiting exists. No middleware, no 429 responses, no rate limit headers.
- **Gap**: No protection against agent-induced traffic storms.
- **Recommendation**: Implement per-token rate limiting at the Jersey filter level.
- **Evidence**: No rate limiting code found.

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits per agent identity.
- **Gap**: No blast-radius controls for agent operations.
- **Recommendation**: Implement before expanding to write-enabled scope.
- **Evidence**: No transaction limit configuration found.

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
- **Finding**: No draft state for most entities. Content packs provide a review-before-activation model.
- **Gap**: No draft/pending state for standard entities.
- **Recommendation**: Consider draft states before enabling write scope.
- **Evidence**: No draft status fields found.

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No approval gates for any operation. All authorized operations execute immediately.
- **Gap**: No human-in-the-loop mechanism at the application layer.
- **Recommendation**: Add operation-level approval requirements before enabling write scope.
- **Evidence**: No approval workflow patterns found.

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: Docker Compose files exist for migration testing (`data-node/migration/docker-compose.yml` with MongoDB + OpenSearch cluster). A test Dockerfile and Testcontainers-based integration tests provide development-time environments. However, no production-equivalent staging environment configuration or seed data generators are provided.
- **Gap**: No documented staging environment with production-equivalent data shape for agent testing.
- **Compensating Controls**:
  - Use the existing Docker Compose files as a basis for a staging environment.
  - Leverage Testcontainers patterns to create automated integration test environments for agent testing.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Provide a Docker Compose configuration with seed data that approximates production data shapes for agent integration testing.
- **Evidence**: `data-node/migration/docker-compose.yml`, `graylog2-server/src/test/resources/org/graylog/testing/graylognode/Dockerfile`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification ⚡
- **Severity**: INFO
- **Finding**: Stage A = Yes (system stores user-specific fields: usernames, email addresses, passwords, session data, access tokens). Stage B evaluation: B1 (API response scoping) — CLEAR: Password hashes are excluded from API responses via separate DTO layer (`UserSummary` does not include password field). Access tokens are never returned in list responses. B2 (Access control differentiation) — CLEAR: Permission model distinguishes `users:read` from `users:edit` and supports per-instance scoping. B3 (Formal classification metadata) — INFO: No field-level sensitivity annotations or data classification tags exist.
- **Gap**: No formal data classification metadata (B3 = INFO only). The practical controls (B1, B2) are in place.
- **Recommendation**: Consider adding field-level sensitivity annotations for documentation purposes, but this is not a deployment gate.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/rest/models/users/responses/UserSummary.java`, `graylog2-server/src/main/java/org/graylog2/users/UserOverviewDTO.java`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity is RISK-SAFETY, further calibrated to INFO because the system is self-hosted and data residency is operator-controlled at deployment time.
- **Finding**: No data residency configuration in the codebase. Self-hosted deployment model.
- **Gap**: No application-level residency controls (operator responsibility).
- **Recommendation**: Document residency requirements in deployment guide.
- **Evidence**: No GDPR/residency configuration found.

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
- **Finding**: Plain-text logging with no PII scrubbing or structured output.
- **Gap**: No mechanism to prevent PII from appearing in logs.
- **Recommendation**: Add Log4j2 PII redaction filter.
- **Evidence**: `graylog2-server/src/main/resources/log4j2.xml`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality scoring or completeness metrics.
- **Gap**: No data quality metadata.
- **Recommendation**: Add freshness indicators to search responses.
- **Evidence**: No data quality mechanisms found.

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: No API versioning, no contract testing, no breaking change detection in CI.
- **Gap**: Agent tool bindings could break silently on API changes.
- **Recommendation**: Add OpenAPI diff to CI pipeline.
- **Evidence**: `UPGRADING.md`, `.github/workflows/build.yml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Field names are human-readable and semantically meaningful across the codebase. API responses use descriptive names (`created_at`, `stream_rules`, `message_count`, `event_definitions`). No legacy abbreviation patterns detected. Java DTO fields map directly to readable JSON properties.
- **Implication**: Agent LLM reasoning benefits from clear field names — no data dictionary lookup required.
- **Recommendation**: No action needed — field naming is already agent-friendly.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/rest/models/`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal data catalog exists. The MCP server's `list_resources` and `read_resource` tools provide a programmatic discovery mechanism for streams, dashboards, and event definitions. The OpenAPI generation capability provides schema documentation at build time.
- **Implication**: The MCP server acts as a lightweight service catalog for agent integration. No external metadata layer (Glue, DataHub) integration exists.
- **Recommendation**: Leverage the MCP server's resource listing as the agent-facing catalog. Consider publishing entity schemas to a service catalog.
- **Evidence**: `graylog2-server/src/main/java/org/graylog/mcp/`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: OpenTelemetry integration exists (optional, via external agent). Logging is unstructured plain-text.
- **Gap**: Traces are optional; logs lack correlation IDs.
- **Recommendation**: Enable OTel auto-instrumentation and switch to structured JSON logging.
- **Evidence**: `graylog2-server/src/main/java/org/graylog/tracing/TracerProvider.java`, `graylog2-server/src/main/resources/log4j2.xml`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: 100+ Prometheus metrics configured. No alerting rules defined.
- **Gap**: No alerting thresholds configured within the application.
- **Recommendation**: Add reference alerting rule configuration.
- **Evidence**: `graylog2-server/src/main/resources/prometheus-exporter.yml`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: Infrastructure/processing metrics published. No business outcome metrics.
- **Gap**: No agent-specific success metrics.
- **Recommendation**: Define external agent success metrics.
- **Evidence**: `graylog2-server/src/main/resources/prometheus-exporter.yml`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance
- **Severity**: RISK-QUALITY
- **Finding**: No IaC in repository. Deployment infrastructure managed externally.
- **Gap**: Agent-facing infrastructure not defined or governed in this repo.
- **Recommendation**: Add reference deployment configuration.
- **Evidence**: No IaC files found.

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: CI runs Maven verify and tests. No API contract testing.
- **Gap**: No breaking change detection for APIs.
- **Recommendation**: Add OpenAPI diff step to CI.
- **Evidence**: `.github/workflows/build.yml`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: Forward-only migrations. No deployment rollback mechanisms in repository.
- **Gap**: No in-repository rollback capability.
- **Recommendation**: Document rollback procedure.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/migrations/`

#### ENG-Q4: API Test Coverage
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Always evaluated (but INFO for stateless-utility)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### ENG-Q5: Encryption at Rest
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
| graylog2-server/src/main/java/org/graylog2/rest/resources/ (187 files) | API-Q1, API-Q2, API-Q3, API-Q4 |
| graylog2-server/src/main/java/org/graylog2/rest/GenericError.java | API-Q3 |
| graylog2-server/src/main/java/org/graylog2/rest/models/ | API-Q5, DISC-Q2 |
| graylog2-server/src/main/java/org/graylog/mcp/server/McpRestResource.java | API-Q1, AUTH-Q1 |
| graylog2-server/src/main/java/org/graylog2/security/realm/AccessTokenAuthenticator.java | AUTH-Q1, AUTH-Q4 |
| graylog2-server/src/main/java/org/graylog2/security/AccessTokenServiceImpl.java | AUTH-Q1, AUTH-Q7 |
| graylog2-server/src/main/java/org/graylog2/shared/security/RestPermissions.java | AUTH-Q2, AUTH-Q3 |
| graylog2-server/src/main/java/org/graylog2/shared/security/Permissions.java | AUTH-Q2 |
| graylog2-server/src/main/java/org/graylog2/audit/NullAuditEventSender.java | AUTH-Q6 |
| graylog2-server/src/main/java/org/graylog2/audit/AuditEventSender.java | AUTH-Q6 |
| graylog2-server/src/main/java/org/graylog2/audit/AuditEventTypes.java | AUTH-Q6 |
| graylog2-server/src/main/java/org/graylog2/security/UserSessionTerminationService.java | AUTH-Q7 |
| graylog2-server/src/main/java/org/graylog2/security/AccessTokenCipher.java | AUTH-Q5 |
| graylog2-server/src/main/java/org/graylog2/security/encryption/EncryptedValueService.java | AUTH-Q5 |
| graylog2-server/src/main/java/org/graylog2/contentpacks/ContentPackService.java | STATE-Q1 |
| graylog2-server/src/main/java/org/graylog2/database/MongoCollections.java | STATE-Q3 |
| graylog2-server/src/main/java/org/graylog/events/notifications/types/HTTPEventNotificationV2.java | API-Q7 |
| graylog2-server/src/main/java/org/graylog/tracing/TracerProvider.java | OBS-Q1 |
| graylog2-server/src/main/java/org/graylog2/rest/models/users/responses/UserSummary.java | DATA-Q1 |
| graylog2-server/src/main/java/org/graylog2/users/UserOverviewDTO.java | DATA-Q1 |
| graylog2-server/src/main/java/org/graylog2/migrations/ | ENG-Q3 |
| graylog2-server/src/main/java/org/graylog/mcp/ | DISC-Q3 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| api-specs/stream-output-filters.yml | API-Q2 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| .github/workflows/build.yml | ENG-Q2, ENG-Q3, DISC-Q1 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| data-node/migration/docker-compose.yml | HITL-Q3 |
| graylog2-server/src/test/resources/org/graylog/testing/graylognode/Dockerfile | HITL-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| pom.xml | API-Q2 |
| graylog2-server/pom.xml | API-Q2 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| misc/graylog.conf | AUTH-Q5, DATA-Q2 |
| graylog2-server/src/main/resources/log4j2.xml | OBS-Q1, DATA-Q6 |
| graylog2-server/src/main/resources/prometheus-exporter.yml | OBS-Q2, OBS-Q3 |
| UPGRADING.md | DISC-Q1 |
