# Agentic Readiness Assessment Report

**Target**: graylog2-server (monorepo primary service)
**Date**: 2025-07-14
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: monorepo
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: java, observability, logging
**Context**: Graylog centralized log-management server.

**Archetype Justification**: graylog2-server has MongoDB persistent state (MongoConnection, MongoCollections, 60+ collections), CRUD operations on streams, dashboards, users, inputs, alerts, and index sets via hundreds of JAX-RS REST resources, and directly manages business entity lifecycles. Classified as stateful-crud rather than orchestrator because the primary value is state ownership and CRUD, not service coordination.

---

## Readiness Profile: Pilot-Ready (Safety Concerns)

**BLOCKERs**: 0 | **RISK-SAFETY**: 7 | **RISK-QUALITY**: 19 | **INFOs**: 12

Supervised pilot with elevated safety oversight: (1) all Pilot-Ready controls apply, (2) prioritize RISK-SAFETY remediation before expanding agent scope, (3) dedicated safety review cadence, (4) agent restricted to lowest-blast-radius read-only operations until RISK-SAFETY count drops below 3.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 2 |
| RISK-SAFETY | 9 |
| RISK-QUALITY | 19 |
| INFO | 12 |
| N/A | 0 |
| Not Evaluated (extended) | 1 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 18
**Extended Questions Not Triggered**: 1
**Questions N/A (repo_type: monorepo)**: 0
**Service Archetype**: stateful-crud (auto-detected)

*Note: Of the 2 BLOCKER-severity questions (API-Q1, AUTH-Q1), no gaps were identified — controls are adequate. Of the 9 RISK-SAFETY-severity questions, 2 (AUTH-Q3, AUTH-Q7) had no gaps identified. The readiness profile is determined by gap counts only: 0 BLOCKER gaps, 7 RISK-SAFETY gaps.*

---

## BLOCKERs — Must Resolve Before Agent Deployment

No BLOCKERs identified.

---

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### STATE-Q1: Compensation and Rollback — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No formal saga pattern, compensation logic, or explicit undo endpoints found. Content pack installation (`ContentPackService`) and system jobs (`LegacySystemJobManager`) execute multi-step operations without rollback capability. Stream configuration changes are atomic per-resource but multi-resource workflows (e.g., content pack install creating streams + inputs + dashboards) have no compensating transaction mechanism.
- **Gap**: Agent-initiated multi-step read-then-act workflows could leave the system in an inconsistent state if a downstream step fails (e.g., reading configuration from multiple endpoints and acting on partial data). For read-only agents this is lower risk but still relevant for system maturity.
- **Compensating Controls**:
  - Scope agent to single-resource reads (no multi-step workflows)
  - Use content packs for atomic configuration snapshots
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement content pack versioning with rollback capability for multi-resource operations.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/system/jobs/LegacySystemJobManager.java`, `graylog2-server/src/main/java/org/graylog2/contentpacks/`

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Limited resilience patterns found. `ChunkedBulkIndexer` implements retry with backoff for Elasticsearch bulk indexing (splits batch on 413 errors, exponential backoff). `MongoDBUpsertRetryer` provides retry for MongoDB upsert conflicts (deprecated, 3 attempts). However, no formal circuit breaker framework (e.g., Resilience4j) is used. HTTP client timeouts are configurable in `graylog.conf` (`elasticsearch_connect_timeout`, `elasticsearch_socket_timeout`, `http_connect_timeout`, `http_read_timeout`).
- **Gap**: No circuit breakers on calls to OpenSearch/data-node. A cascading failure from OpenSearch downtime could propagate to the REST API layer that agents consume. Configurable timeouts exist but are not paired with circuit breaker state management.
- **Compensating Controls**:
  - Deploy a reverse proxy (e.g., nginx, HAProxy) with circuit breaker capability in front of Graylog
  - Monitor OpenSearch health independently and pause agent operations during outages
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add Resilience4j circuit breakers to OpenSearch and data-node HTTP client calls.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/indexer/messages/ChunkedBulkIndexer.java`, `graylog2-server/src/main/java/org/graylog2/database/MongoDBUpsertRetryer.java`, `misc/graylog.conf`

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: A `TooManyRequestsStatus` class (HTTP 429) exists, indicating rate limiting was considered architecturally, but no application-level rate limiting middleware is implemented. No `express-rate-limit` equivalent, no API Gateway throttling, and no per-endpoint rate limits in the JAX-RS resource layer. The `lb_throttle_threshold_percentage` config parameter in `graylog.conf` controls load balancer health signaling based on journal usage but does not enforce API-level rate limits.
- **Gap**: A runaway agent loop calling the Graylog REST API at machine speed has no throttling protection. This could overwhelm the Graylog server and degrade service for all users.
- **Compensating Controls**:
  - Deploy Graylog behind a reverse proxy with rate limiting (nginx `limit_req_zone`, HAProxy rate limiting)
  - Configure agent-side rate limiting in the orchestration layer
- **Remediation Timeline**: 30 days
- **Recommendation**: Implement a JAX-RS request filter with per-token rate limiting using Guava `RateLimiter` or a dedicated middleware. Alternatively, deploy an API gateway in front of Graylog.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/rest/TooManyRequestsStatus.java`, `misc/graylog.conf`

#### AUTH-Q6: Immutable Audit Logging — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Graylog has a comprehensive audit logging system: `AuditEventSender` dispatches events, `AuditActor` attributes actions to users (`urn:graylog:user:<username>`) or system nodes (`urn:graylog:node:<nodeId>`), and `AuditEventTypes` defines 150+ event types including MCP-specific events (`MCP_TOOL_CALL`, `MCP_RESOURCE_READ`, `MCP_PROTOCOL_INITIALIZE`). The `@AuditEvent` and `@NoAuditEvent` annotations enforce audit coverage on REST resources. However, audit logs are stored in MongoDB and internal Graylog log streams — there is no immutable storage configuration (no S3 Object Lock, no WORM storage, no separate immutable audit destination).
- **Gap**: Audit logs can be modified or deleted by MongoDB administrators. For a read-only agent, this is a lower risk but still represents a gap in forensic capability. Agent actions through the MCP endpoint ARE audited (MCP_TOOL_CALL, MCP_RESOURCE_READ events with actor attribution).
- **Compensating Controls**:
  - Forward Graylog audit events to a separate, immutable log destination (e.g., S3 with Object Lock, CloudWatch Logs with retention policy)
  - Enable MongoDB auditing at the database level
- **Remediation Timeline**: 30 days
- **Recommendation**: Configure a dedicated Graylog output to forward audit events to an immutable storage backend. Enable MongoDB audit logging with write-once storage.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/audit/AuditEventSender.java`, `graylog2-server/src/main/java/org/graylog2/audit/AuditActor.java`, `graylog2-server/src/main/java/org/graylog2/audit/AuditEventTypes.java`

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The `log4j2.xml` configuration uses a `PatternLayout` with standard patterns (`%d %-5p: %c - %m%n`) and no PII scrubbing filters. No log masking libraries or regex-based PII redaction patterns are configured. The internal `Memory` appender buffers logs in memory for REST API access, also without PII filtering. Graylog processes and indexes log messages that may contain customer PII, usernames, IP addresses, and session tokens. The `AccessTokenImpl` uses `EncryptedValue` to protect tokens in database storage, and the `EncryptedValueSerializer` prevents encrypted values from appearing in API responses, but this does not extend to application logs.
- **Gap**: If an agent queries Graylog's search API and retrieves log messages containing PII, or if Graylog's own application logs contain PII from user operations, this data could leak into LLM prompt/response pairs without redaction.
- **Compensating Controls**:
  - Configure agent-side PII redaction before sending data to LLMs
  - Use Graylog's pipeline processing rules to redact PII in stored log messages
  - Add custom log4j2 pattern converter for PII masking in application logs
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement a custom log4j2 `PatternConverter` or `RewritePolicy` to mask PII patterns (emails, IPs, tokens) in application logs. Create Graylog pipeline rules for PII redaction in indexed messages.
- **Evidence**: `graylog2-server/src/main/resources/log4j2.xml`, `graylog2-server/src/main/java/org/graylog2/security/encryption/EncryptedValueSerializer.java`

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Graylog has a comprehensive RBAC system with 100+ fine-grained permission constants in `RestPermissions.java` (e.g., `streams:read`, `inputs:create`, `users:edit`, `mcp_server:access`). Entity-level grants via `DBGrantService` support Viewer/Manager/Owner capabilities per resource. Built-in roles include scoped roles like "Dashboard Creator", "MCP Server Access", and "API Browser Reader". The system supports creating an agent identity with read-only permissions to specific streams, dashboards, or search operations.
- **Gap**: The root admin account (`root_username` in `graylog.conf`) has implicit `*:*` wildcard permissions. If an agent is configured with admin credentials, it inherits all permissions with no restriction. The system supports scoped permissions but does not enforce least privilege by default — it requires deliberate configuration.
- **Compensating Controls**:
  - Create a dedicated agent user with only `mcp_server:access`, `streams:read`, `messages:read`, `searches:*` permissions
  - Use entity-level grants to restrict access to specific streams
- **Remediation Timeline**: 7 days (configuration task)
- **Recommendation**: Create a dedicated "Agent Reader" built-in role with minimal read-only permissions. Document agent identity setup in deployment guides.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/shared/security/RestPermissions.java`, `graylog2-server/src/main/java/org/graylog/security/DBGrantService.java`

#### DATA-Q2: Data Residency and Sovereignty — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Graylog is a self-hosted application. Data residency is entirely determined by the operator's deployment choices. No region-specific storage configurations, GDPR-specific controls, or cross-region replication settings exist in the codebase.
- **Gap**: No code-level data residency controls. If an agent sends Graylog data to an LLM endpoint in a different jurisdiction, compliance depends entirely on the operator's deployment architecture.
- **Compensating Controls**:
  - Deploy LLM endpoints in the same region as Graylog
  - Configure agent-side data filtering to exclude regulated data from LLM prompts
- **Remediation Timeline**: N/A (deployment-dependent, operator responsibility)
- **Recommendation**: Document data residency considerations for agent deployments. Add deployment guide section on configuring agents with region-aware LLM endpoints.
- **Evidence**: `misc/graylog.conf` (mongodb_uri, elasticsearch_hosts)

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Graylog uses Swagger v3 / OpenAPI annotations (`@Operation`, `@Tag`, `@Parameter`, `@ApiResponse`) throughout all JAX-RS REST resources. A build-time tool (`GenerateApiDefinition.java`) auto-generates an OpenAPI specification at compile time (output to `target/swagger`). A standalone OpenAPI 3.1.0 spec exists at `api-specs/stream-output-filters.yml`. The MCP endpoint at `/mcp` is also Swagger-annotated.
- **Gap**: The auto-generated OpenAPI spec is a build artifact (not committed to source). The only committed spec covers a single feature (stream destination filters). An agent tool builder cannot access the full API spec without building the project. The auto-generated spec's currency depends on annotation completeness.
- **Compensating Controls**:
  - Build the project to generate the full OpenAPI spec (`./mvnw package`)
  - Use the runtime Swagger UI at `/api/api-browser` for interactive exploration
- **Remediation Timeline**: 14 days
- **Recommendation**: Commit the auto-generated OpenAPI spec to the repository (e.g., `api-specs/graylog-server-openapi.json`) and update it in CI on API changes.
- **Evidence**: `api-specs/stream-output-filters.yml`, `graylog2-server/src/main/java/org/graylog/mcp/server/McpRestResource.java` (Swagger annotations)

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Graylog has a structured error handling system with multiple exception mappers: `ValidationExceptionMapper` returns 400 with `ValidationApiError` (message + validation errors map), `ElasticsearchExceptionMapper` returns 500 with `SearchError` (message + error details), `QueryParsingExceptionMapper`, `JsonProcessingExceptionMapper`, `BadRequestExceptionMapper`, and `WebApplicationExceptionMapper`. The MCP endpoint returns JSON-RPC error responses with error codes (`McpSchema.ErrorCodes.INVALID_PARAMS`, `INTERNAL_ERROR`).
- **Gap**: Error responses vary by exception type — there is no single unified error envelope with a consistent `error_code`, `message`, `retryable` structure across all endpoints. Some errors return HTML via `GraylogErrorPageGenerator`. An agent cannot reliably parse all error responses with a single schema.
- **Compensating Controls**:
  - Use the MCP endpoint (`/mcp`) which has consistent JSON-RPC error format
  - Build agent error parsing to handle both JSON and non-JSON responses
- **Remediation Timeline**: 30 days
- **Recommendation**: Standardize all REST API error responses into a single JSON envelope: `{type, message, error_code, retryable}`. Deprecate HTML error responses.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/rest/ValidationExceptionMapper.java`, `graylog2-server/src/main/java/org/graylog2/rest/ElasticsearchExceptionMapper.java`, `graylog2-server/src/main/java/org/graylog2/rest/GraylogErrorPageGenerator.java`

#### AUTH-Q4: Identity Propagation and Delegation — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Graylog supports identity propagation via: (1) `AccessTokenAuthenticator` for API token authentication with user attribution, (2) `BearerTokenRealm` for bearer tokens, (3) `HTTPHeaderAuthenticationRealm` for header-based auth (e.g., reverse proxy SSO), (4) JWT tokens for graylog-server ↔ data-node communication (`IndexerJwtAuthTokenProvider`). The MCP endpoint uses `SearchUser` context for user-scoped searches and `PermissionHelper` for permission enforcement. `AuditActor` distinguishes user actions (`urn:graylog:user:`) from system actions (`urn:graylog:node:`).
- **Archetype calibration**: For stateful-crud, evaluated at RISK-QUALITY (default severity for this archetype). Identity propagation is well-implemented — controls are adequate.
- **Gap**: Minimal — the system supports identity propagation with user attribution throughout the request lifecycle. No explicit on-behalf-of token exchange flow, but the access token model correctly attributes agent actions to a specific user identity.
- **Compensating Controls**:
  - Create a dedicated agent user with an access token — identity flows through to audit logs, search permissions, and data access controls
  - Use `HTTPHeaderAuthenticationRealm` for reverse proxy SSO delegation if needed
- **Remediation Timeline**: No immediate remediation required — controls are adequate
- **Recommendation**: When setting up an agent identity, create a dedicated user (not admin) with an access token. The system correctly propagates this identity to all downstream operations. Consider adding explicit on-behalf-of token exchange for delegated agent scenarios.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/security/realm/AccessTokenAuthenticator.java`, `graylog2-server/src/main/java/org/graylog/mcp/tools/PermissionHelper.java`

#### AUTH-Q5: Credential Management — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Graylog uses `EncryptedValue`/`EncryptedValueService` with AES-SIV encryption for storing secrets in MongoDB. Access tokens are encrypted via `AccessTokenCipher` using AES-SIV derived from the `password_secret` configuration parameter. The `EncryptedValueSerializer` prevents encrypted values from appearing in API responses (shows `{is_set: true}` instead). JWT tokens for data-node communication use `IndexerJwtAuthTokenProvider`. The `password_secret` must be configured in `graylog.conf` and is used as the master encryption key.
- **Gap**: `password_secret` is stored in a flat configuration file (`graylog.conf`), not in a secrets management system. No rotation mechanism for access tokens or `password_secret` is built in. No integration with AWS Secrets Manager, HashiCorp Vault, or similar. The `graylog.conf` comments warn that changing `password_secret` invalidates all sessions and encrypted values.
- **Compensating Controls**:
  - Use environment variables for `password_secret` instead of the config file
  - Restrict file system access to `graylog.conf`
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add Secrets Manager integration for `password_secret` and access token rotation. Support programmatic secret rotation without service restart.
- **Evidence**: `misc/graylog.conf`, `graylog2-server/src/main/java/org/graylog2/security/encryption/EncryptedValue.java`, `graylog2-server/src/main/java/org/graylog2/security/AccessTokenCipher.java`

#### DATA-Q1: Sensitive Data Classification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Graylog implements field-level protection through multiple mechanisms: (1) `EncryptedValue`/`EncryptedValueService` encrypts sensitive fields (access tokens, secrets) at rest with AES-SIV, (2) `DbEntity` annotation with `readableFields` array controls which fields are exposed through the API catalog (e.g., `AccessTokenImpl` restricts readable fields), (3) `EncryptedValueSerializer` prevents encrypted values from appearing in HTTP responses, (4) RBAC via `@RequiresPermissions` prevents unauthorized resource access. The MCP tools (`PermissionHelper`) enforce permission checks before returning data.
- **Gap**: There is no formal data classification taxonomy (e.g., "PII", "PHI", "Confidential") applied systematically across all entity types. Protection is implemented ad-hoc per entity rather than through a unified classification framework. Log messages indexed in OpenSearch may contain unclassified sensitive data from source systems.
- **Compensating Controls**:
  - Use Graylog pipeline rules to classify and tag log messages containing PII
  - Restrict agent access to specific streams with known data sensitivity levels
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement a data classification annotation system that tags MongoDB fields and OpenSearch index fields by sensitivity level. Integrate with the DbEntity catalog.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/security/encryption/EncryptedValue.java`, `graylog2-server/src/main/java/org/graylog2/database/dbcatalog/DbEntityCatalogEntry.java`, `graylog2-server/src/main/java/org/graylog2/security/AccessTokenImpl.java`

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Graylog's REST API uses a `/api/` URL prefix. The OpenAPI spec in `api-specs/stream-output-filters.yml` is versioned (1.0.0). Database migrations are versioned with 283 migration files (`V*.java` pattern). Dependabot monitors Maven and npm dependencies for updates. The CI build (`build.yml`) runs backend tests and full integration tests.
- **Gap**: No explicit API versioning strategy (no `/v1/`, `/v2/` prefixes). No breaking change detection tools (no `buf breaking`, no OpenAPI diff in CI). No consumer-driven contract tests (Pact). API changes could break agent tool bindings without detection.
- **Compensating Controls**:
  - Pin agent tool definitions to specific Graylog server versions
  - Monitor Graylog release notes for API breaking changes
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenAPI spec diff checking to CI (e.g., `oasdiff`) to detect breaking changes before merge.
- **Evidence**: `api-specs/stream-output-filters.yml`, `.github/workflows/build.yml`, `.github/dependabot.yml`

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Graylog has OpenTelemetry integration: `TracingModule` binds an `io.opentelemetry.api.trace.Tracer`, `TracerProvider` uses `GlobalOpenTelemetry.get().getTracer("org.graylog")`, and `GraylogSemanticAttributes` defines custom trace attributes for lookup tables, system jobs, scheduler jobs, and periodicals. When the OpenTelemetry Java agent is attached, full distributed tracing is available. However, logging uses standard log4j2 with `PatternLayout` (`%d %-5p: %c - %m%n`) — not structured JSON. No `request_id` or `correlation_id` field injection is visible in the log configuration.
- **Gap**: Logs are not structured (plain text, not JSON). No correlation ID linking REST API requests to log entries. Tracing requires the OpenTelemetry Java agent to be attached externally — it is not enabled by default.
- **Compensating Controls**:
  - Attach the OpenTelemetry Java agent at deployment time
  - Configure log4j2 with `JsonLayout` for structured logging
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add a `JsonLayout` option to log4j2.xml. Inject `X-Request-Id` or trace ID into MDC for correlation. Enable OpenTelemetry by default with configurable export.
- **Evidence**: `graylog2-server/src/main/java/org/graylog/tracing/TracingModule.java`, `graylog2-server/src/main/java/org/graylog/tracing/TracerProvider.java`, `graylog2-server/src/main/resources/log4j2.xml`

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Graylog has a comprehensive Prometheus exporter with 1384 lines of metric mappings (`prometheus-exporter.yml`) covering stream processing, indexing, journal, JVM, HTTP, and search metrics. Dropwizard Metrics integration with `@Timed` annotations on REST resources provides per-endpoint latency and throughput data. Graylog IS itself an alerting platform — it can alert on its own metrics when they are ingested as log data.
- **Gap**: No pre-configured alerting thresholds on Graylog's own API error rates or latency degradation. The Prometheus exporter must be enabled (`prometheus_exporter_enabled = false` by default) and connected to an external alerting system. No built-in self-monitoring alerting for the REST API surface agents consume.
- **Compensating Controls**:
  - Enable the Prometheus exporter and connect to Grafana/Alertmanager
  - Use Graylog itself to monitor its own API health via GELF input
- **Remediation Timeline**: 14 days
- **Recommendation**: Enable Prometheus exporter by default. Ship pre-built Grafana dashboards with alerting rules for API error rate, latency P99, and agent-specific traffic patterns.
- **Evidence**: `graylog2-server/src/main/resources/prometheus-exporter.yml`, `misc/graylog.conf`

#### ENG-Q1: Infrastructure Governance — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No Infrastructure-as-Code (Terraform, CloudFormation, CDK, Helm, Kustomize) found in the repository. Graylog is a self-hosted application distributed as tarballs, DEB/RPM packages, and container images. Deployment infrastructure is the operator's responsibility. A `docker-compose.yml` exists at `data-node/migration/docker-compose.yml` for migration testing only.
- **Gap**: As a self-hosted product, the integration surface (API gateway, IAM roles, network config) is entirely operator-managed. No reference IaC, no drift detection, no deployment automation in the repo. This is inherent to the product model, not a deficiency in the codebase.
- **Compensating Controls**:
  - Operators should maintain IaC for their Graylog deployment (Terraform, Ansible, etc.)
  - Use the official Docker images with Kubernetes Helm charts (maintained separately)
- **Remediation Timeline**: N/A (operator responsibility)
- **Recommendation**: Publish reference Terraform modules or Helm charts for common deployment patterns. Include agent-facing security configurations (dedicated user, rate limiting proxy, audit forwarding).
- **Evidence**: No IaC files found. `data-node/migration/docker-compose.yml` (migration testing only)

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: GitHub Actions CI (`build.yml`) runs: (1) build artifacts (compile + javadoc), (2) frontend tests, (3) backend tests (`verify -DexcludedGroups=full-backend-test`), (4) full backend integration tests with matrix strategy (OpenSearch 2.19.3/MongoDB 8.0 + DataNode/MongoDB 7.0). Dependabot monitors Maven and npm dependencies daily. 1193 Java test files in `graylog2-server/src/test/` and 62 full backend integration tests.
- **Gap**: No API contract testing (no Pact, no OpenAPI validation in CI, no schema diff checks). No explicit test that the auto-generated OpenAPI spec matches actual API behavior. API changes that break agent tool bindings would not be detected by the current CI pipeline.
- **Compensating Controls**:
  - Full backend integration tests cover API behavior implicitly
  - Agent tool definitions can be version-pinned to tested Graylog versions
- **Remediation Timeline**: 30 days
- **Recommendation**: Add OpenAPI spec generation + diff check as a CI step. Generate the spec in CI and compare against the committed spec to detect breaking changes.
- **Evidence**: `.github/workflows/build.yml`, `.github/dependabot.yml`

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No deployment rollback mechanisms found in the repository. No blue/green deployment config, no CodeDeploy rollback, no Helm rollback, no feature flags infrastructure. Database migrations (283 `V*.java` files) are forward-only with no reverse migration support. The CI pipeline builds and tests but does not deploy.
- **Gap**: As a self-hosted product, rollback capability depends on the operator's deployment infrastructure. A broken Graylog upgrade that changes API behavior would require the operator to restore from backup or reinstall the previous version. No built-in rollback automation.
- **Compensating Controls**:
  - Operators should implement blue/green deployment with their infrastructure
  - Database snapshots before upgrades
  - Containerized deployments allow image tag rollback
- **Remediation Timeline**: N/A (operator responsibility)
- **Recommendation**: Document recommended rollback procedures. Provide migration rollback scripts for critical schema changes.
- **Evidence**: `.github/workflows/build.yml`, `graylog2-server/src/main/java/org/graylog2/migrations/`

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: A `docker-compose.yml` at `data-node/migration/docker-compose.yml` provides a multi-node cluster (3 OpenSearch nodes, 3 DataNode instances, MongoDB, Graylog) for migration testing. The `full-backend-tests` module uses Testcontainers for integration testing with real OpenSearch and MongoDB instances. No dedicated sandbox or staging environment configuration.
- **Gap**: No production-equivalent staging environment with seed data. The docker-compose is for migration testing, not for agent behavior testing. No synthetic data generators for safe agent experimentation.
- **Compensating Controls**:
  - Use docker-compose to stand up a local Graylog instance for agent testing
  - Configure a separate Graylog instance with non-production data for pilots
- **Remediation Timeline**: 14 days
- **Recommendation**: Publish a docker-compose.yml specifically for agent testing with seed data (sample streams, dashboards, log messages) and a pre-configured agent user.
- **Evidence**: `data-node/migration/docker-compose.yml`, `full-backend-tests/`

#### STATE-Q2: Queryable Current State — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Graylog exposes GET endpoints for all CRUD resources (streams, inputs, dashboards, users, index sets, roles, alerts). The REST API follows consistent patterns: `GET /api/streams` (list), `GET /api/streams/{id}` (detail). System status is queryable via `/api/system/cluster/nodes`, `/api/system/jobs`, `/api/system/indexer/cluster/health`. The MCP tools (`ListStreamsTool`, `ListInputsTool`, `ListIndicesTool`, `ReadResourceTool`) expose queryable state for agent consumption.
- **Gap**: No unified "state machine" status API. Resource states are queryable per-resource but there is no aggregate status endpoint showing the system's overall state for agent decision-making.
- **Compensating Controls**:
  - Use the MCP tools for unified resource querying
  - Combine multiple GET endpoints for comprehensive state inspection
- **Remediation Timeline**: 30 days
- **Recommendation**: Add an aggregate system status endpoint summarizing key resource states for agent consumption.
- **Evidence**: `graylog2-server/src/main/java/org/graylog/mcp/tools/`, `graylog2-server/src/main/java/org/graylog2/rest/resources/`

#### API-Q6: Asynchronous Operation Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Graylog has system jobs (`LegacySystemJobManager`) for long-running operations: index rotation, index range recalculation, content pack installation. Jobs are submitted via `POST /api/system/jobs` and their status is queryable via `GET /api/system/jobs`. The job scheduler (`job_scheduler_system_worker_threads = 5`) manages concurrency. Index optimization has a configurable timeout (`elasticsearch_index_optimization_timeout = 1h`).
- **Gap**: The system jobs API provides basic polling patterns but lacks webhook callbacks or push notifications on job completion. Agent must poll for job status.
- **Compensating Controls**:
  - Implement agent-side polling with exponential backoff for long-running operations
  - Use Graylog notifications/alerts to signal job completion
- **Remediation Timeline**: 30 days
- **Recommendation**: Add webhook callback support for system job completion. Include estimated completion time in job status responses.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/system/jobs/LegacySystemJobManager.java`, `misc/graylog.conf`

#### DATA-Q3: Selective Query Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Graylog implements comprehensive pagination and filtering: `PaginatedList` provides paginated results with total count, `PaginationParameters` supports `page`, `per_page`, `sort`, `order`, and `query` parameters. The `api-specs/stream-output-filters.yml` demonstrates standard pagination with configurable page size (default: 20). Search API supports field selection, time range filtering, and Graylog query language for precise result filtering. The MCP `SearchMessagesTool` and `AggregateMessagesTool` support filtered queries.
- **Gap**: Minimal — pagination and filtering are well-implemented. Some list endpoints may return unbounded results if `per_page` is set too high. No enforced maximum page size in all endpoints.
- **Compensating Controls**:
  - Configure agent to use reasonable page sizes (e.g., per_page=50)
  - Use search query filtering to narrow result sets
- **Remediation Timeline**: 14 days
- **Recommendation**: Enforce maximum page size (e.g., 500) across all paginated endpoints to prevent context window overflow.
- **Evidence**: `api-specs/stream-output-filters.yml`, `graylog2-server/src/main/java/org/graylog2/rest/PaginationParameters.java`

#### DATA-Q4: System of Record Designations — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Graylog is the authoritative system of record for its own configuration data (streams, inputs, dashboards, users, roles, index sets, alerts). These are stored in MongoDB with clear ownership. For log data, Graylog indexes messages in OpenSearch but the original log sources are external systems — Graylog is a secondary copy, not the system of record for the original log events.
- **Gap**: No formal system-of-record documentation. No explicit designation of which data Graylog owns vs. caches. An agent querying log data should understand it is reading indexed copies, not authoritative records.
- **Compensating Controls**:
  - Document data ownership in agent tool descriptions
  - Clarify in MCP resource descriptions which data is authoritative vs. cached
- **Remediation Timeline**: 14 days
- **Recommendation**: Add system-of-record annotations to API documentation and MCP resource descriptions.
- **Evidence**: `graylog2-server/src/main/java/org/graylog/mcp/resources/`

#### DATA-Q5: Temporal Metadata and Freshness — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Graylog entities include temporal metadata: `AccessTokenImpl` has `CREATED_AT`, `LAST_ACCESS`, `EXPIRES_AT` fields. Log messages have `timestamp` fields with timezone information. The search API returns message timestamps. Index sets have rotation timestamps. Database migration files are timestamped (`V20251030000000_...`). UTC is used for internal timestamps (Joda-Time `DateTimeZone.UTC`).
- **Gap**: No `Cache-Control` or `X-Data-Age` headers on API responses. No `consistency_level` field indicating whether search results are from primary or replica. OpenSearch eventually-consistent reads are not signaled to the API consumer.
- **Compensating Controls**:
  - Use the `timestamp` field in search results for freshness reasoning
  - Implement agent-side staleness checks based on message timestamps
- **Remediation Timeline**: 30 days
- **Recommendation**: Add `X-Data-Freshness` or `Cache-Control` headers to search API responses indicating data age and consistency level.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/security/AccessTokenImpl.java`

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The repository contains 1193 Java test files in `graylog2-server/src/test/` and 62 full-backend integration tests. The CI pipeline (`build.yml`) runs backend tests and full integration tests with real OpenSearch and MongoDB instances via Testcontainers. The build uses `-Pedantic` flag for strict compilation. SpotBugs is included (though sometimes skipped in CI for speed). Full-backend tests matrix tests against multiple OpenSearch versions and MongoDB versions.
- **Gap**: No dedicated API contract tests. No explicit REST resource test coverage metrics. No Postman/Newman collections or REST Assured test suites specifically validating the agent-facing API surface. The existing tests are primarily unit tests and integration tests, not API contract tests.
- **Compensating Controls**:
  - Full backend integration tests implicitly validate API behavior
  - MCP endpoint behavior is validated through the test infrastructure
- **Remediation Timeline**: 30 days
- **Recommendation**: Add dedicated API contract test suite for the MCP endpoint and key REST resources agents will consume. Measure API endpoint test coverage.
- **Evidence**: `.github/workflows/build.yml`, `full-backend-tests/`

#### ENG-Q5: Encryption at Rest — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Graylog encrypts sensitive fields at rest using `EncryptedValue`/`EncryptedValueService` with AES-SIV encryption derived from `password_secret`. Access tokens are encrypted in MongoDB via `AccessTokenCipher`. JWT tokens for data-node communication are cryptographically signed. Password hashing uses PBKDF2, BCrypt, or SHA-256.
- **Gap**: Encryption at rest is field-level (specific sensitive fields only), not database-level or disk-level. MongoDB and OpenSearch storage is not encrypted at rest by default — this depends on operator deployment configuration. Log messages stored in OpenSearch indices are not encrypted beyond what the storage layer provides.
- **Compensating Controls**:
  - Enable MongoDB encryption at rest (WiredTiger encryption)
  - Enable OpenSearch node-level encryption at rest
  - Use encrypted EBS volumes for all data storage
- **Remediation Timeline**: 14 days (operator configuration)
- **Recommendation**: Document encryption-at-rest deployment requirements. Add deployment checklist for MongoDB and OpenSearch encryption configuration.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/security/encryption/EncryptedValue.java`, `graylog2-server/src/main/java/org/graylog2/security/AccessTokenCipher.java`

---

## INFOs — Architecture and Design Inputs

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Write endpoints (POST/PUT/DELETE) do not implement idempotency keys. `AccessTokenServiceImpl.create()` uses a retry loop (10 attempts) to generate unique tokens with `SecureRandom` and catches `MongoException` duplicate key errors. MongoDB unique indexes on `AccessTokenImpl.TOKEN` provide de-duplication at the database level but not at the API level.
- **Implication**: If agent scope expands to write-enabled, idempotency keys must be added to write endpoints to prevent duplicate operations from LLM non-determinism.
- **Recommendation**: Plan idempotency key support in POST endpoints before enabling write agent scope.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/security/AccessTokenServiceImpl.java`

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: All REST API responses use `MediaType.APPLICATION_JSON` (JSON). The MCP endpoint (`/mcp`) uses JSON-RPC 2.0 over JSON. No XML or binary response formats found in the REST API layer. Protobuf is used internally for journal messages (`JournalMessages.java`) but not exposed through the API.
- **Implication**: JSON is the ideal format for agent consumption. LLMs can parse Graylog API responses directly with no format transformation needed.
- **Recommendation**: No action needed. Maintain JSON-only API surface.
- **Evidence**: `graylog2-server/src/main/java/org/graylog/mcp/server/McpRestResource.java`

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: The `TooManyRequestsStatus` class defines HTTP 429 response status but no `X-RateLimit-Remaining` or `Retry-After` headers are returned by any endpoint. Rate limits are not documented in the API spec or configuration reference.
- **Implication**: Agents cannot self-throttle based on rate limit headers. Agent-side rate limiting must be configured manually.
- **Recommendation**: Document recommended API call rates. Add `X-RateLimit-Remaining` and `Retry-After` headers when rate limiting is implemented.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/rest/TooManyRequestsStatus.java`

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: `MongoDBUpsertRetryer` (deprecated) retries upserts on duplicate key errors. MongoDB's native server-side retries handle upsert conflicts in MongoDB ≥ 4.2. The `EtagService` in the Sidecar plugin implements ETag-based conditional requests. No optimistic locking (version fields) found in core entity models.
- **Implication**: Read-only agents are not affected. If write scope is enabled, optimistic locking should be added to prevent concurrent modification races.
- **Recommendation**: Add version fields to core entities (streams, inputs, dashboards) before enabling write agent scope.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/database/MongoDBUpsertRetryer.java`, `graylog2-server/src/main/java/org/graylog/plugins/sidecar/services/EtagService.java`

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits found (no max records per operation, no spend limits, no per-agent operation caps). The `output_batch_size` (500 messages) and `elasticsearch_max_total_connections` (200) provide system-level limits but not per-agent limits.
- **Implication**: Read-only agents cannot modify data, so transaction limits are not immediately relevant. For future write-enabled scope, per-agent limits should be implemented.
- **Recommendation**: Plan per-agent-identity operation limits before enabling write scope.
- **Evidence**: `misc/graylog.conf`

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Content packs support install/uninstall workflows. Streams have start/stop states. Event definitions have status fields. However, no general "draft" or "pending" state exists across entity types.
- **Implication**: Read-only agents do not create state changes. For future write-enabled scope, draft states would enable human-in-the-loop approval for agent-proposed changes.
- **Recommendation**: Consider adding a "draft" status to streams, dashboards, and event definitions for future agent write operations.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/rest/resources/streams/StreamResource.java`

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable approval gates found. Content pack installation is immediate. Stream creation is immediate. No two-step commit patterns or explicit confirmation steps in the REST API.
- **Implication**: Read-only agents do not execute write operations. For future write scope, approval gates would be valuable for high-risk operations.
- **Recommendation**: Plan configurable approval workflows for destructive operations (delete stream, change input configuration) before enabling write agent scope.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/rest/resources/`

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Graylog uses clear, semantically meaningful field names in API responses and database schemas. Java naming conventions map to readable JSON: `stream_id`, `destination_type`, `created_at`, `last_access`, `expires_at`, `event_definitions`, `index_sets`. The `DbEntityCatalogEntry` records include `titleField` for human-readable entity identification. No legacy abbreviations or cryptic codes found.
- **Implication**: Agents using LLM-based reasoning can interpret Graylog field names without a data dictionary. The field naming is clear and self-documenting.
- **Recommendation**: No action needed. Maintain clear naming conventions.
- **Evidence**: `api-specs/stream-output-filters.yml`, `graylog2-server/src/main/java/org/graylog2/database/dbcatalog/DbEntityCatalogEntry.java`

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: Graylog has an internal `DbEntitiesCatalog` system that registers MongoDB entity classes with their collection names, title fields, read permissions, and readable fields using `@DbEntity` annotations and `DbEntitiesCatalogProvider`. The MCP server exposes resource providers (`StreamResourceProvider`, `DashboardResourceProvider`, `EventDefinitionResourceProvider`) that describe available resources with their schemas. The Prometheus exporter mapping file serves as a metrics catalog.
- **Implication**: The `DbEntitiesCatalog` provides a form of internal metadata layer that could accelerate agent tool definition. The MCP resource providers already expose Graylog entities as agent-consumable resources.
- **Recommendation**: Extend the MCP resource providers to cover all entity types. Document the DbEntitiesCatalog for external consumers.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/database/dbcatalog/DbEntitiesCatalog.java`, `graylog2-server/src/main/java/org/graylog/mcp/resources/`

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No formal data quality score, completeness metric, or data profiling found. Graylog monitors processing throughput (`stream_incoming_messages` Prometheus metric), index health, and journal status. Input processing has fault counting (`output_fault_count_threshold`, `output_fault_penalty_seconds`). No data freshness SLAs or null rate monitoring.
- **Implication**: Agents cannot reason about data quality or completeness. Planning input for future data quality observability.
- **Recommendation**: Add data quality metrics to the Prometheus exporter: message completeness rates, field extraction success rates, index lag metrics.
- **Evidence**: `graylog2-server/src/main/resources/prometheus-exporter.yml`, `misc/graylog.conf`

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: BLOCKER (no gap identified — controls adequate)
- **Finding**: Graylog exposes a comprehensive REST API via JAX-RS with Swagger v3 annotations (`@Operation`, `@Tag`, `@Parameter`, `@ApiResponse`) across hundreds of resources under `graylog2-server/src/main/java/org/graylog2/rest/resources/`. The MCP endpoint at `/mcp` provides a dedicated Model Context Protocol interface for agent integration. All endpoints produce and consume `MediaType.APPLICATION_JSON`. No direct database access, file-based exchange, or UI automation required for integration.
- **Gap**: None — a well-documented REST API with MCP integration exists.
- **Recommendation**: No remediation needed. The REST API and MCP endpoint provide a strong integration surface for agents.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/rest/resources/` (60+ resource classes), `graylog2-server/src/main/java/org/graylog/mcp/server/McpRestResource.java`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section above.
- **Gap**: Auto-generated OpenAPI spec not committed to repository.
- **Recommendation**: Commit the auto-generated OpenAPI spec to the repository.
- **Evidence**: `api-specs/stream-output-filters.yml`

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section above.
- **Gap**: No unified error envelope across all endpoints.
- **Recommendation**: Standardize REST API error responses.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/rest/ValidationExceptionMapper.java`, `graylog2-server/src/main/java/org/graylog2/rest/ElasticsearchExceptionMapper.java`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: See INFOs section above.
- **Gap**: No idempotency key support in write endpoints.
- **Recommendation**: Plan idempotency before write scope.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/security/AccessTokenServiceImpl.java`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: See INFOs section above.
- **Gap**: None.
- **Recommendation**: Maintain JSON-only API surface.
- **Evidence**: `graylog2-server/src/main/java/org/graylog/mcp/server/McpRestResource.java`

#### API-Q6: Asynchronous Operation Support
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section. System jobs with polling pattern exists but no webhook callbacks.
- **Gap**: No push notifications on job completion.
- **Recommendation**: Add webhook callback support for system job completion.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/system/jobs/LegacySystemJobManager.java`

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: Graylog uses an internal EventBus (Google Guava) for state change propagation within the server. `@Subscribe` annotations handle events like `UserChangedEvent`. Notification system sends alerts on stream rule matches, system events. No external webhook emission for configuration state changes (stream created/updated/deleted).
- **Implication**: Agents cannot subscribe to configuration change events. Must poll for state changes.
- **Recommendation**: Add webhook notification support for configuration entity state changes.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/security/UserSessionTerminationService.java` (EventBus usage)

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: See INFOs section above.
- **Gap**: No rate limit headers returned.
- **Recommendation**: Document recommended API call rates.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/rest/TooManyRequestsStatus.java`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER (no gap identified — controls adequate)
- **Finding**: Graylog supports machine identity authentication via `AccessTokenAuthenticator`: API access tokens are created per-user, stored in MongoDB with AES-SIV encryption, and authenticated via HTTP Basic Auth (token as username, "token" as password). Each token is attributed to a specific user (`AccessTokenImpl.USERNAME`), and the `AuditActor.user()` method records the authenticated user in audit logs. The MCP endpoint requires `@RequiresAuthentication` and `@RequiresPermissions(RestPermissions.MCP_SERVER_ACCESS)`. Additional auth mechanisms include `BearerTokenRealm`, `HTTPHeaderAuthenticationRealm`, and `SessionAuthenticator`.
- **Gap**: None — machine identity with principal attribution exists.
- **Recommendation**: Create a dedicated Graylog user for agent access. Generate an access token for that user with minimal permissions.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/security/realm/AccessTokenAuthenticator.java`, `graylog2-server/src/main/java/org/graylog2/security/AccessTokenServiceImpl.java`, `graylog2-server/src/main/java/org/graylog2/audit/AuditActor.java`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: See RISKs section above.
- **Gap**: Admin wildcard permissions; no enforced least privilege by default.
- **Recommendation**: Create dedicated "Agent Reader" role.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/shared/security/RestPermissions.java`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY (no gap identified — controls adequate)
- **Finding**: Graylog enforces action-level authorization via `@RequiresPermissions` annotations on every REST resource with specific `domain:action` patterns (e.g., `streams:read`, `streams:edit`, `streams:create`, `streams:changestate`). The `CaseSensitiveWildcardPermission` class parses permission strings. Entity-level grants via `DBGrantService` support Viewer (read), Manager (read+write), and Owner (read+write+delete) capabilities per resource instance. The MCP endpoint requires `mcp_server:access` permission specifically.
- **Gap**: Minimal — the system supports fine-grained action-level authorization. An agent with `streams:read` cannot delete streams.
- **Recommendation**: No immediate action needed. The authorization model is well-suited for agent scope restriction.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/shared/security/RestPermissions.java`, `graylog2-server/src/main/java/org/graylog/security/DBGrantService.java`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: RISK-QUALITY
- **Archetype calibration**: For stateful-crud, evaluated at RISK-QUALITY (default severity for this archetype). Identity propagation is well-implemented — controls are adequate.
- **Finding**: See RISKs section above. Graylog supports identity propagation via access tokens, bearer tokens, header-based auth, and JWT tokens with user attribution throughout the request lifecycle.
- **Gap**: Minimal — no explicit on-behalf-of token exchange flow, but access token model correctly attributes agent actions.
- **Recommendation**: Create dedicated agent user with access token. Consider adding on-behalf-of token exchange for delegated agent scenarios.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/security/realm/AccessTokenAuthenticator.java`, `graylog2-server/src/main/java/org/graylog/mcp/tools/PermissionHelper.java`

#### AUTH-Q5: Credential Management
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section above.
- **Gap**: `password_secret` in flat config file; no secrets manager integration.
- **Recommendation**: Add Secrets Manager integration.
- **Evidence**: `misc/graylog.conf`, `graylog2-server/src/main/java/org/graylog2/security/encryption/EncryptedValue.java`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: See RISKs section above.
- **Gap**: Audit logs not stored in immutable storage.
- **Recommendation**: Forward audit events to immutable storage backend.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/audit/AuditEventTypes.java`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY (no gap identified — controls adequate)
- **Finding**: Agent identities can be suspended immediately through multiple mechanisms: (1) `AccessTokenService.deleteAllForUser(username)` revokes all access tokens for a user, (2) `User.AccountStatus.ENABLED` check in `AccessTokenAuthenticator.doGetAuthenticationInfo()` blocks authentication for disabled accounts, (3) `UserSessionTerminationService` terminates all sessions for a user on account status change (listens for `UserChangedEvent`), (4) Individual tokens can be deleted via `AccessTokenServiceImpl.deleteById()`.
- **Gap**: Minimal — the system supports immediate identity suspension without affecting other users.
- **Recommendation**: Document the agent identity suspension procedure. Create a runbook for emergency agent revocation.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/security/realm/AccessTokenAuthenticator.java`, `graylog2-server/src/main/java/org/graylog2/security/UserSessionTerminationService.java`, `graylog2-server/src/main/java/org/graylog2/security/AccessTokenServiceImpl.java`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: See RISKs section above.
- **Gap**: No formal compensation/rollback patterns.
- **Recommendation**: Implement content pack versioning with rollback.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/system/jobs/LegacySystemJobManager.java`

#### STATE-Q2: Queryable Current State
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section. GET endpoints for all resources; MCP tools expose queryable state.
- **Gap**: No aggregate system status endpoint.
- **Recommendation**: Add aggregate status endpoint.
- **Evidence**: `graylog2-server/src/main/java/org/graylog/mcp/tools/`

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: See INFOs section above.
- **Gap**: No optimistic locking in core entities.
- **Recommendation**: Add version fields before write scope.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/database/MongoDBUpsertRetryer.java`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: See RISKs section above.
- **Gap**: No formal circuit breakers.
- **Recommendation**: Add Resilience4j circuit breakers.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/indexer/messages/ChunkedBulkIndexer.java`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: See RISKs section above.
- **Gap**: No rate limiting enforcement.
- **Recommendation**: Implement per-token rate limiting.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/rest/TooManyRequestsStatus.java`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: See INFOs section above.
- **Gap**: No per-agent operation limits.
- **Recommendation**: Plan per-agent limits before write scope.
- **Evidence**: `misc/graylog.conf`

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
- **Finding**: See INFOs section above.
- **Gap**: No general draft/pending state.
- **Recommendation**: Consider draft states for future write scope.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/rest/resources/streams/StreamResource.java`

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: See INFOs section above.
- **Gap**: No approval gates.
- **Recommendation**: Plan approval workflows for write scope.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/rest/resources/`

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section above.
- **Gap**: No production-equivalent staging environment.
- **Recommendation**: Publish agent-testing docker-compose with seed data.
- **Evidence**: `data-node/migration/docker-compose.yml`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section above.
- **Gap**: No formal data classification taxonomy.
- **Recommendation**: Implement data classification annotation system.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/security/encryption/EncryptedValue.java`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: See RISKs section above.
- **Gap**: No code-level data residency controls.
- **Recommendation**: Document data residency considerations for agent deployments.
- **Evidence**: `misc/graylog.conf`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section. Comprehensive pagination/filtering via PaginatedList and PaginationParameters.
- **Gap**: No enforced maximum page size in all endpoints.
- **Recommendation**: Enforce maximum page size across all endpoints.
- **Evidence**: `api-specs/stream-output-filters.yml`

#### DATA-Q4: System of Record Designations
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section. Graylog owns config data; log data is indexed copy.
- **Gap**: No formal system-of-record documentation.
- **Recommendation**: Add system-of-record annotations to API docs.
- **Evidence**: `graylog2-server/src/main/java/org/graylog/mcp/resources/`

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section. Temporal fields exist on entities. UTC timestamps.
- **Gap**: No Cache-Control/freshness headers on API responses.
- **Recommendation**: Add freshness headers to search API responses.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/security/AccessTokenImpl.java`

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: See RISKs section above.
- **Gap**: No PII scrubbing in log configuration.
- **Recommendation**: Implement custom log4j2 PII masking.
- **Evidence**: `graylog2-server/src/main/resources/log4j2.xml`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: See INFOs section above.
- **Gap**: No formal data quality metrics.
- **Recommendation**: Add data quality metrics to Prometheus exporter.
- **Evidence**: `graylog2-server/src/main/resources/prometheus-exporter.yml`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section above.
- **Gap**: No API versioning or breaking change detection in CI.
- **Recommendation**: Add OpenAPI diff checking to CI.
- **Evidence**: `.github/workflows/build.yml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: See INFOs section above.
- **Gap**: None.
- **Recommendation**: Maintain clear naming conventions.
- **Evidence**: `api-specs/stream-output-filters.yml`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: See INFOs section above.
- **Gap**: Internal catalog not externally documented.
- **Recommendation**: Extend MCP resource providers.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/database/dbcatalog/DbEntitiesCatalog.java`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section above.
- **Gap**: Logs not structured; tracing requires external agent.
- **Recommendation**: Add JsonLayout and enable OpenTelemetry by default.
- **Evidence**: `graylog2-server/src/main/java/org/graylog/tracing/TracingModule.java`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section above.
- **Gap**: No pre-configured alerting thresholds.
- **Recommendation**: Enable Prometheus exporter by default with alerting rules.
- **Evidence**: `graylog2-server/src/main/resources/prometheus-exporter.yml`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: Dropwizard Metrics integration with `@Timed` annotations on REST resources provides per-endpoint latency and throughput. Prometheus exporter maps 1384 metric patterns including stream-level incoming messages, journal throughput, indexing rates, and processing times. Custom metrics for business outcomes (e.g., alert resolution rates, search success rates) are not exposed.
- **Implication**: Infrastructure metrics are comprehensive. Business outcome metrics for agent interactions would need to be added as custom metrics.
- **Recommendation**: Add custom Prometheus metrics for agent-relevant business outcomes: search success rate, MCP tool call rates, agent session durations.
- **Evidence**: `graylog2-server/src/main/resources/prometheus-exporter.yml`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section above.
- **Gap**: No IaC in repository (self-hosted product).
- **Recommendation**: Publish reference IaC modules.
- **Evidence**: No IaC files found

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section above.
- **Gap**: No API contract testing in CI.
- **Recommendation**: Add OpenAPI spec diff checking.
- **Evidence**: `.github/workflows/build.yml`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section above.
- **Gap**: No rollback automation (self-hosted product).
- **Recommendation**: Document rollback procedures.
- **Evidence**: `.github/workflows/build.yml`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section. 1193 test files + 62 full-backend integration tests.
- **Gap**: No dedicated API contract tests.
- **Recommendation**: Add API contract test suite for MCP and key REST resources.
- **Evidence**: `.github/workflows/build.yml`, `full-backend-tests/`

#### ENG-Q5: Encryption at Rest
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section. Field-level encryption via EncryptedValue/AES-SIV.
- **Gap**: Database-level encryption is operator-dependent.
- **Recommendation**: Document encryption-at-rest deployment requirements.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/security/encryption/EncryptedValue.java`

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `graylog2-server/src/main/java/org/graylog/mcp/server/McpRestResource.java` | API-Q1, API-Q2, API-Q5, AUTH-Q1 |
| `graylog2-server/src/main/java/org/graylog/mcp/tools/PermissionHelper.java` | AUTH-Q4 |
| `graylog2-server/src/main/java/org/graylog2/rest/resources/` (60+ classes) | API-Q1, API-Q3 |
| `graylog2-server/src/main/java/org/graylog2/rest/ValidationExceptionMapper.java` | API-Q3 |
| `graylog2-server/src/main/java/org/graylog2/rest/ElasticsearchExceptionMapper.java` | API-Q3 |
| `graylog2-server/src/main/java/org/graylog2/rest/GraylogErrorPageGenerator.java` | API-Q3 |
| `graylog2-server/src/main/java/org/graylog2/rest/TooManyRequestsStatus.java` | API-Q8, STATE-Q5 |
| `graylog2-server/src/main/java/org/graylog2/shared/security/RestPermissions.java` | AUTH-Q2, AUTH-Q3 |
| `graylog2-server/src/main/java/org/graylog/security/DBGrantService.java` | AUTH-Q2, AUTH-Q3 |
| `graylog2-server/src/main/java/org/graylog2/security/realm/AccessTokenAuthenticator.java` | AUTH-Q1, AUTH-Q4, AUTH-Q7 |
| `graylog2-server/src/main/java/org/graylog2/security/AccessTokenServiceImpl.java` | AUTH-Q1, AUTH-Q7, API-Q4 |
| `graylog2-server/src/main/java/org/graylog2/security/encryption/EncryptedValue.java` | AUTH-Q5, DATA-Q1 |
| `graylog2-server/src/main/java/org/graylog2/security/UserSessionTerminationService.java` | AUTH-Q7 |
| `graylog2-server/src/main/java/org/graylog2/audit/AuditActor.java` | AUTH-Q1, AUTH-Q6 |
| `graylog2-server/src/main/java/org/graylog2/audit/AuditEventTypes.java` | AUTH-Q6 |
| `graylog2-server/src/main/java/org/graylog2/audit/AuditEventSender.java` | AUTH-Q6 |
| `graylog2-server/src/main/java/org/graylog2/indexer/messages/ChunkedBulkIndexer.java` | STATE-Q4 |
| `graylog2-server/src/main/java/org/graylog2/database/MongoDBUpsertRetryer.java` | STATE-Q3, STATE-Q4 |
| `graylog2-server/src/main/java/org/graylog2/system/jobs/LegacySystemJobManager.java` | STATE-Q1 |
| `graylog2-server/src/main/java/org/graylog/tracing/TracingModule.java` | OBS-Q1 |
| `graylog2-server/src/main/java/org/graylog/tracing/TracerProvider.java` | OBS-Q1 |
| `graylog2-server/src/main/java/org/graylog/tracing/GraylogSemanticAttributes.java` | OBS-Q1 |
| `graylog2-server/src/main/java/org/graylog2/database/dbcatalog/DbEntitiesCatalog.java` | DISC-Q3, DATA-Q1 |
| `graylog2-server/src/main/java/org/graylog2/database/dbcatalog/DbEntityCatalogEntry.java` | DISC-Q3, DATA-Q1 |
| `graylog2-server/src/main/java/org/graylog/plugins/sidecar/services/EtagService.java` | STATE-Q3 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `api-specs/stream-output-filters.yml` | API-Q2, DISC-Q1, DISC-Q2 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/build.yml` | ENG-Q2, ENG-Q3, DISC-Q1 |
| `.github/dependabot.yml` | ENG-Q2 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `data-node/migration/docker-compose.yml` | HITL-Q3 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `misc/graylog.conf` | AUTH-Q5, STATE-Q4, STATE-Q5, STATE-Q6, DATA-Q2, OBS-Q2 |
| `misc/datanode.conf` | AUTH-Q5, DATA-Q2 |
| `misc/security.properties` | AUTH-Q5 |
| `graylog2-server/src/main/resources/log4j2.xml` | OBS-Q1, DATA-Q6 |
| `graylog2-server/src/main/resources/prometheus-exporter.yml` | OBS-Q2, DATA-Q7 |

### Security Documentation
| File | Questions Referenced |
|------|---------------------|
| `SECURITY.md` | AUTH-Q5 |
