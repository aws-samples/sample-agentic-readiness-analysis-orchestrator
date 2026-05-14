# Agentic Readiness Analysis Report

**Target**: graylog2-server (monorepo primary service)
**Date**: 2026-04-30
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**Repository Type**: monorepo
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: java, observability, logging
**Context**: Graylog centralized log-management server.

**Archetype Justification**: graylog2-server has persistent state (MongoDB + OpenSearch), exposes CRUD endpoints for streams, dashboards, users, inputs, and alerts, manages entity lifecycles with user-specific data — classic stateful-crud pattern.

**Surface flags**:
- has_persistent_data_store: true
- has_http_rpc_surface: true
- has_auth_surface: true
- has_write_operations: true
- has_logging_of_user_data: true

---

## Readiness Profile: Pilot-Ready (Safety Concerns)

**BLOCKERs**: 0 | **RISK-SAFETY**: 6 | **RISK-QUALITY**: 12 | **INFOs**: 21

With DATA-Q1 reclassified from BLOCKER to INFO under the new tiered model (see INFOs below), Graylog has no remaining BLOCKERs. Proceed with a supervised pilot; prioritize RISK-SAFETY remediation (especially AUTH-Q6 audit immutability) before expanding scope.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 0 |
| RISK-SAFETY | 6 |
| RISK-QUALITY | 12 |
| INFO | 21 |
| N/A | 0 |
| Not Evaluated (extended) | 4 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 15
**Extended Questions Not Triggered**: 4
**Questions N/A (repo_type: monorepo)**: 0
**Service Archetype**: stateful-crud (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

_None. DATA-Q1 was previously BLOCKER under the binary "formal classification absent" rule; under the tiered model it resolves to INFO (see INFOs section) because Graylog excludes password from user responses via explicit `readableFields`, wraps LDAP and webhook secrets in `EncryptedValue` (serialized as `{"is_set": true}` without plaintext), and enforces granular GRN-based RBAC. Log-content redaction for ingested PII is a source-system responsibility, not a Graylog code defect._

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q6: Immutable Audit Logging — RISK-SAFETY ⚡

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Graylog has a comprehensive audit event system. `AuditEventSender` interface supports success/failure logging with `AuditActor` attribution (URN-based: `urn:graylog:user:<username>` or `urn:graylog:node:<nodeId>`). MCP-specific audit events are defined: `MCP_PROTOCOL_INITIALIZE`, `MCP_TOOL_LIST`, `MCP_TOOL_CALL`, `MCP_RESOURCE_LIST`, `MCP_RESOURCE_READ`, `MCP_PROMPT_LIST`, `MCP_PROMPT_GET`. The `McpService` logs every tool call with the authenticated user's identity via `AuditActor.user(permissionHelper.getCurrentUser().getName())`. However, audit events are stored in MongoDB, which does not provide immutable or tamper-evident storage by default. No CloudTrail, S3 Object Lock, or WORM storage configuration was found.
- **Gap**: Audit logs are stored in MongoDB without immutability guarantees. No tamper-evident storage configuration. An operator with MongoDB admin access could modify or delete audit records.
- **Compensating Controls**:
  - Forward audit events to a separate, immutable log sink (e.g., Graylog's own log ingestion pipeline with write-once index retention)
  - Enable MongoDB audit logging with write to a read-only external store
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure audit event forwarding to an immutable storage backend (S3 with Object Lock, or a dedicated Graylog stream with write-once retention policy) for all MCP-related audit events.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/audit/AuditEventSender.java`, `graylog2-server/src/main/java/org/graylog2/audit/AuditEventTypes.java`, `graylog2-server/src/main/java/org/graylog2/audit/AuditActor.java`, `graylog2-server/src/main/java/org/graylog/mcp/server/McpService.java`

#### STATE-Q1: Compensation and Rollback — RISK-SAFETY ⚡

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No formal compensation, saga, or rollback patterns were found in the codebase. `MongoDBUpsertRetryer` provides retry logic for concurrent upserts but is deprecated and does not constitute a compensation mechanism. MongoDB operations are generally non-transactional at the multi-collection level. There are no explicit undo endpoints, compensating transactions, or Step Functions-style rollback states. The system relies on individual MongoDB document atomicity rather than multi-step transaction coordination.
- **Gap**: No compensation or rollback mechanism for multi-step operations. If a multi-step write sequence fails mid-execution, partial state persists.
- **Compensating Controls**:
  - For read-only agent scope, this risk is significantly reduced since agents do not execute write workflows
  - If scope expands to write-enabled, implement saga patterns for critical multi-step operations (e.g., stream creation with rule configuration)
- **Remediation Timeline**: 60–90 days (if scope expands to write-enabled)
- **Recommendation**: Document which operations are multi-step and assess compensation needs. For read-only scope, this is lower priority but should be addressed before expanding to write-enabled.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/database/MongoDBUpsertRetryer.java` (deprecated)

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Graylog calls OpenSearch/Elasticsearch for all search and indexing operations. The `graylog-storage-opensearch2` and `graylog-storage-opensearch3` modules handle these interactions. No circuit breaker patterns (Resilience4j, Hystrix, or custom implementations) were found. The `ChunkedBulkIndexer` in `graylog2-server/src/main/java/org/graylog2/indexer/messages/` has some retry logic for indexing but no circuit breaker to prevent cascading failures. When an agent-initiated search request via the MCP `SearchMessagesTool` triggers an OpenSearch call, a failing OpenSearch cluster could cascade through to the agent without protection.
- **Gap**: No circuit breakers protecting OpenSearch dependency calls. Agent-initiated requests could cascade failures from a degraded OpenSearch cluster back through the MCP endpoint.
- **Compensating Controls**:
  - Deploy an API gateway or reverse proxy with circuit breaker configuration in front of the Graylog REST API
  - Configure OpenSearch client-level timeout settings aggressively
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement circuit breaker patterns on OpenSearch client calls, at minimum for the search path that the MCP `SearchMessagesTool` uses. Consider Resilience4j integration.
- **Evidence**: `graylog-storage-opensearch2/`, `graylog-storage-opensearch3/`, `graylog2-server/src/main/java/org/graylog2/indexer/messages/ChunkedBulkIndexer.java`

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: A `TooManyRequestsStatus` class exists in `graylog2-server/src/main/java/org/graylog2/rest/TooManyRequestsStatus.java`, defining HTTP 429 response status. However, no systematic rate limiting middleware, API gateway throttling configuration, or per-endpoint rate limit enforcement was found in the codebase. The MCP endpoint at `/api/mcp` has no rate limiting. The REST API has no `express-rate-limit` equivalent or WAF rate rules. No `X-RateLimit-Remaining` or `Retry-After` headers are returned. A runaway agent loop could issue unlimited requests to the search endpoint at machine speed.
- **Gap**: No API-layer rate limiting enforcement. The `TooManyRequestsStatus` class defines the status code but is not systematically applied. The MCP endpoint has no rate limiting.
- **Compensating Controls**:
  - Deploy a reverse proxy (nginx, HAProxy) or API gateway with rate limiting in front of the Graylog API
  - Configure per-IP or per-token request limits at the network layer
- **Remediation Timeline**: 30 days
- **Recommendation**: Implement rate limiting middleware for the REST API and MCP endpoint. At minimum, add per-access-token rate limits for the `/api/mcp` endpoint. Return `X-RateLimit-Remaining` and `Retry-After` headers.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/rest/TooManyRequestsStatus.java`, `graylog2-server/src/main/java/org/graylog/mcp/server/McpRestResource.java`

#### DATA-Q2: Data Residency and Sovereignty — RISK-SAFETY ⚡

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Graylog stores log data in OpenSearch indices and metadata in MongoDB. The `docker-compose.yml` in `data-node/migration/` shows MongoDB and OpenSearch configured without region constraints. No data residency controls, GDPR/LGPD compliance configurations, or cross-region replication restrictions were found in the codebase. As a self-hosted product, data residency is an operator responsibility, but no tooling or configuration hooks exist to enforce residency constraints that an agent would respect when retrieving log data.
- **Gap**: No data residency or sovereignty controls in the codebase. If an agent sends log data containing EU citizen PII to an LLM endpoint in a different jurisdiction, the operator has no application-level controls to prevent it.
- **Compensating Controls**:
  - Deploy Graylog in a single region with network-level egress controls
  - Configure the agent orchestration layer to enforce data residency rules before sending data to LLM endpoints
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add data residency metadata to streams or index sets, allowing operators to tag data with jurisdiction constraints. Expose this metadata via the MCP tools so agents can respect residency boundaries.
- **Evidence**: `data-node/migration/docker-compose.yml`, absence of residency configuration in codebase

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Graylog's application logs use `log4j2.xml` with `PatternLayout` (`%d %-5p: %c - %m%n`). No PII masking, scrubbing, or redaction middleware was found in the logging configuration. The audit event system logs usernames in `AuditActor` URNs (`urn:graylog:user:<username>`). The MCP `PermissionHelper` logs user principals in permission denial messages: `"Not authorized. User <{}> is missing permission <{}>"`. The `AccessTokenAuthenticator` logs user names: `"Found user {} for access token."`. No Amazon Macie integration, log scrubbing library, or PII regex filters were found. While Graylog is a log platform that ingests external logs (which may contain PII), its own application-level logging also includes user identifiers without redaction.
- **Gap**: No PII redaction in Graylog's own application logs. Usernames, user IDs, and permission details are logged in cleartext. No masking library or log filter configuration.
- **Compensating Controls**:
  - Configure log4j2 with a custom layout or filter that masks user identifiers
  - Route Graylog's own application logs through a Graylog pipeline with PII redaction rules
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement a log4j2 PatternLayout replacement or RewritePolicy that masks PII patterns (usernames, email addresses) in application log output. Add a PII redaction pipeline rule for Graylog's own ingested logs.
- **Evidence**: `graylog2-server/src/main/resources/log4j2.xml`, `graylog2-server/src/main/java/org/graylog2/audit/AuditActor.java`, `graylog2-server/src/main/java/org/graylog/mcp/tools/PermissionHelper.java`, `graylog2-server/src/main/java/org/graylog2/security/realm/AccessTokenAuthenticator.java`

### RISK-QUALITY — Address as Capacity Allows

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Multiple `ExceptionMapper` implementations exist: `ElasticsearchExceptionMapper` returns `SearchError` with message and error details, `ValidationExceptionMapper` returns `ValidationApiError` with validation errors, `QueryParsingExceptionMapper` and `NotFoundExceptionMapper` return structured responses. The MCP endpoint returns JSON-RPC errors with error codes (`McpSchema.ErrorCodes.INVALID_PARAMS`, `INTERNAL_ERROR`, `RESOURCE_NOT_FOUND`, `METHOD_NOT_FOUND`). However, the REST API error responses lack a consistent, unified error format with a retryable/non-retryable classification. Different exception mappers return different structures. No `retryable` boolean or error category is consistently present across all error responses.
- **Gap**: Error responses lack a unified format with consistent error codes and retryable/non-retryable classification across all REST endpoints. MCP errors are well-structured via JSON-RPC but REST API errors are inconsistent.
- **Compensating Controls**:
  - Agents can use HTTP status codes (429, 503 → retryable; 400, 403, 404 → non-retryable) as a heuristic
  - MCP JSON-RPC error codes provide structured error information for MCP-based agents
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Introduce a unified error response envelope for REST API errors containing `error_code`, `message`, `retryable` boolean, and `details` fields. Standardize across all ExceptionMappers.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/rest/ElasticsearchExceptionMapper.java`, `graylog2-server/src/main/java/org/graylog2/rest/ValidationExceptionMapper.java`, `graylog2-server/src/main/java/org/graylog/mcp/server/McpRestResource.java`

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: OpenAPI spec is auto-generated from Swagger annotations and served at `/api/openapi` and `/api/openapi.yaml` via `OpenApiResource.java`. The web interface has a `generate:apidefs` script in `package.json` that generates API definitions from the server's Swagger output. The API is served under the `/api/` prefix. However, no explicit API versioning (`/v1/`, `/v2/`, `Accept-Version` headers) was found. No breaking change detection tools (OpenAPI diff, `buf breaking`, Pact) are configured in CI. The `build.yml` GitHub Actions workflow runs backend and frontend tests but no API contract tests.
- **Gap**: No explicit API version scheme. No breaking change detection in CI. Agent tool bindings could break silently when API schemas change during Graylog upgrades.
- **Compensating Controls**:
  - Pin agent tool definitions to a specific Graylog release version
  - Manually diff OpenAPI specs between releases before upgrading
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenAPI spec diff checking to the CI pipeline (e.g., `oasdiff` or `openapi-diff`) to detect breaking changes before merging. Implement explicit API versioning for the MCP endpoint.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/shared/rest/documentation/openapi/OpenApiResource.java`, `graylog2-web-interface/package.json` (`generate:apidefs` script), `.github/workflows/build.yml`

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: OpenTelemetry tracing is integrated via `TracingModule` and `TracerProvider`, which uses `GlobalOpenTelemetry.get().getTracer("org.graylog")` — relying on the OpenTelemetry javaagent for implementation. Custom semantic attributes are defined in `GraylogSemanticAttributes` for lookup tables, periodicals, system jobs, and scheduler jobs. Proto files for OpenTelemetry collector (metrics, traces, logs) exist in `graylog2-server/src/main/proto/opentelemetry/`. However, application logging via `log4j2.xml` uses `PatternLayout` (human-readable format), not structured JSON logging. No `correlation_id` or `request_id` fields are consistently propagated through log entries. Tracing is present but logging is not structured for machine consumption.
- **Gap**: Application logs are not structured (JSON). No consistent correlation ID propagation in log entries. Tracing exists (OpenTelemetry) but structured logging does not complement it for end-to-end request reconstruction.
- **Compensating Controls**:
  - Use OpenTelemetry trace IDs for request correlation (when javaagent is deployed)
  - Configure a JSON-format log appender alongside the PatternLayout appender
- **Remediation Timeline**: 30 days
- **Recommendation**: Add a JSON-format log4j2 appender (e.g., `JsonLayout` or `JsonTemplateLayout`) with trace ID and correlation ID fields. This enables machine-parseable logs for debugging agent-initiated requests.
- **Evidence**: `graylog2-server/src/main/java/org/graylog/tracing/TracingModule.java`, `graylog2-server/src/main/java/org/graylog/tracing/TracerProvider.java`, `graylog2-server/src/main/java/org/graylog/tracing/GraylogSemanticAttributes.java`, `graylog2-server/src/main/resources/log4j2.xml`

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Graylog exposes extensive Prometheus metrics via a 1384-line mapping configuration in `prometheus-exporter.yml`, covering stream incoming messages, indexer metrics, journal metrics, pipeline processing metrics, and JVM metrics. Graylog IS an alerting platform with event definitions and notification system. However, no self-monitoring alerts (alerting on Graylog's own API error rates, latency, or MCP endpoint health) were found configured in the repository. Prometheus metrics are exported but no CloudWatch alarms, PagerDuty integration, or anomaly detection configuration exists for the APIs agents will consume.
- **Gap**: Prometheus metrics are exposed but no alerting thresholds are configured for the API surface. No self-monitoring alerts for MCP endpoint error rates or latency.
- **Compensating Controls**:
  - Configure external Prometheus alerting rules for Graylog's own metrics endpoint
  - Use Graylog's own alerting system to monitor its application logs for error patterns
- **Remediation Timeline**: 30 days
- **Recommendation**: Define Prometheus alerting rules for MCP endpoint error rates, search latency, and API 5xx rates. Configure Graylog event definitions to self-monitor its own performance.
- **Evidence**: `graylog2-server/src/main/resources/prometheus-exporter.yml`

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: A `docker-compose.yml` in `data-node/migration/` provides a local development environment with MongoDB, OpenSearch nodes, DataNode instances, and a Graylog server. This is suitable for development and migration testing. The CI pipeline in `.github/workflows/build.yml` runs full-backend-tests against OpenSearch and MongoDB containers. However, no production-equivalent staging environment configuration, synthetic data generators, or seed data scripts were found. The docker-compose setup uses development images and is not designed for production-equivalent testing.
- **Gap**: No production-equivalent staging or sandbox environment configuration. The docker-compose setup is for development/migration, not for testing agent behavior against realistic data volumes and configurations.
- **Compensating Controls**:
  - Use the docker-compose development environment as a lightweight sandbox for initial agent testing
  - Create a staging Graylog instance with anonymized production data for pre-deployment agent validation
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a docker-compose-based staging environment with production-equivalent configuration and seed data scripts that populate realistic log data for agent testing.
- **Evidence**: `data-node/migration/docker-compose.yml`, `.github/workflows/build.yml`

#### ENG-Q1: Infrastructure Governance — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No Infrastructure as Code (Terraform, CloudFormation, CDK, Helm, Kustomize) was found in the repository. Graylog is a self-hosted open-source product — infrastructure provisioning is the responsibility of operators who deploy it. The `docker-compose.yml` in `data-node/migration/` is for development/migration, not production infrastructure. The `config/` directory contains only code quality tools (`pmd-rules.xml`, `spotbugs-exclude.xml`, `settings.xml`). No API gateway, IAM role, or network configuration definitions exist.
- **Gap**: No IaC defining the agent-facing infrastructure surface (API gateway, IAM roles, network policies). Infrastructure governance is delegated to operators.
- **Compensating Controls**:
  - This is expected for a self-hosted product — operators must provide IaC for their deployment
  - Publish reference IaC modules (Terraform, Helm) that embed security best practices for agent-facing deployments
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Provide reference Helm charts or Terraform modules with secure-by-default configurations for agent-facing Graylog deployments, including API gateway with rate limiting, TLS, and IAM policies.
- **Evidence**: Absence of IaC files in repository root. `config/pmd-rules.xml`, `config/spotbugs-exclude.xml`, `data-node/migration/docker-compose.yml`

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: GitHub Actions CI pipeline in `.github/workflows/build.yml` includes: build-artifacts, frontend-tests, backend-tests, and full-backend-tests. Backend tests run with Maven (`-DexcludedGroups=full-backend-test`). Full-backend-tests run against OpenSearch and MongoDB containers. MCP-specific tests exist (`McpRestResourceTest.java`, `McpServiceTest.java`). However, no API contract testing (Pact, OpenAPI spec validation in CI, schema comparison) was found. The CI does not detect API-breaking changes before production.
- **Gap**: No API contract testing in CI. No OpenAPI spec validation or breaking change detection. Changes to the REST API or MCP tool schemas are not caught before they affect agents.
- **Compensating Controls**:
  - The auto-generated OpenAPI spec from annotations ensures spec-code consistency
  - MCP unit tests provide some coverage for tool call contracts
- **Remediation Timeline**: 30 days
- **Recommendation**: Add OpenAPI spec snapshot comparison to the CI pipeline. Generate the OpenAPI spec during builds and compare against a committed baseline to detect breaking changes.
- **Evidence**: `.github/workflows/build.yml`, `graylog2-server/src/test/java/org/graylog/mcp/server/McpRestResourceTest.java`, `graylog2-server/src/test/java/org/graylog/mcp/server/McpServiceTest.java`

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No blue/green deployment, canary deployment, or rollback configuration was found in the repository. The CI pipeline builds Maven artifacts and runs tests but does not define deployment or rollback procedures. This is expected for a self-hosted product — deployment and rollback are operator responsibilities. No feature flag framework was found. Version management is via Maven (`7.1.0-SNAPSHOT`).
- **Gap**: No rollback capability defined in the repository. Operators must implement their own rollback procedures.
- **Compensating Controls**:
  - Operators can implement rollback via container image version pinning and database backup/restore
  - Maven version numbering allows operators to roll back to previous releases
- **Remediation Timeline**: 60 days
- **Recommendation**: Document rollback procedures for Graylog upgrades. Provide migration scripts with rollback support for database schema changes.
- **Evidence**: `.github/workflows/build.yml`, `pom.xml`

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The `full-backend-tests` module runs integration tests against real OpenSearch and MongoDB instances. MCP-specific unit tests exist (`McpRestResourceTest.java`, `McpServiceTest.java`). Frontend tests use Jest. Backend tests use JUnit. However, no dedicated API test suites (Postman/Newman collections, REST Assured API tests, or Pact contract tests) were found. Test coverage for the agent-facing MCP endpoint's input handling, error responses, and edge cases (malformed JSON-RPC, invalid tool names, permission boundaries) is limited to the two MCP test files.
- **Gap**: Limited API test coverage for the MCP endpoint specifically. No contract tests or comprehensive API test suites for the REST API endpoints agents will consume.
- **Compensating Controls**:
  - Existing MCP unit tests cover basic tool call and error scenarios
  - Full-backend-tests provide integration coverage for the underlying services
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Expand MCP endpoint test coverage to include: permission boundary tests, rate limit behavior, concurrent request handling, malformed input handling, and all tool call variations.
- **Evidence**: `graylog2-server/src/test/java/org/graylog/mcp/server/McpRestResourceTest.java`, `graylog2-server/src/test/java/org/graylog/mcp/server/McpServiceTest.java`, `full-backend-tests/`

#### ENG-Q5: Encryption at Rest — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: `EncryptedValueService` provides AES encryption for sensitive configuration values using a `password_secret` key (minimum 16 characters, injected from configuration). `AccessTokenCipher` encrypts access tokens at rest in MongoDB using AES-SIV. However, no database-level encryption at rest configuration was found for MongoDB or OpenSearch. The `docker-compose.yml` does not configure MongoDB or OpenSearch with encryption at rest. Log data stored in OpenSearch indices is not encrypted at the storage layer by default.
- **Gap**: Application-level encryption exists for sensitive fields (access tokens, encrypted values) but no database-level encryption at rest for MongoDB or OpenSearch. Log data in OpenSearch indices is stored unencrypted at the storage layer.
- **Compensating Controls**:
  - Operators can enable MongoDB encryption at rest and OpenSearch encryption at rest at the infrastructure level
  - Access tokens are already encrypted via EncryptedValueService/AccessTokenCipher
- **Remediation Timeline**: 30 days (operator configuration)
- **Recommendation**: Document encryption at rest requirements for operators. Provide configuration guidance for enabling MongoDB and OpenSearch encryption at rest. Consider adding encryption at rest to the reference docker-compose configuration.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/security/encryption/EncryptedValueService.java`, `graylog2-server/src/main/java/org/graylog2/security/AccessTokenServiceImpl.java`, `data-node/migration/docker-compose.yml`

#### DATA-Q4: System of Record Designations — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Graylog is the de facto system of record for ingested log data, stream configurations, user accounts, dashboards, and alert definitions. MongoDB stores metadata and configuration; OpenSearch stores indexed log messages. However, no formal system-of-record designations, master data management processes, or conflict resolution logic were found documented in the codebase. For multi-node deployments, MongoDB is the authoritative source for configuration and OpenSearch for log data, but this is implicit rather than documented.
- **Gap**: No formal system-of-record documentation. Implicit data ownership without explicit golden record designations.
- **Compensating Controls**:
  - Graylog's architecture inherently designates MongoDB for config and OpenSearch for logs — agents can rely on this convention
- **Remediation Timeline**: 30 days
- **Recommendation**: Document system-of-record designations for all data domains. Clarify which MCP tools return authoritative data vs. cached/derived data.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/database/`, `graylog-storage-opensearch2/`, `graylog-storage-opensearch3/`

#### DATA-Q5: Temporal Metadata and Freshness — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Log messages inherently have timestamps. `AccessTokenImpl` includes `CREATED_AT`, `EXPIRES_AT`, and `LAST_ACCESS` fields. `GrantDTO` includes `createdAt` and `updatedAt` fields set with `ZonedDateTime.now(ZoneOffset.UTC)`. The `SearchMessagesTool` returns results with `effectiveTimerange` metadata. However, no `Cache-Control` headers, `X-Data-Age` headers, or `consistency_level` indicators were found on REST API responses. Agents cannot programmatically determine whether data returned is current, cached, or eventually consistent.
- **Gap**: Entity timestamps exist but API responses do not signal data freshness. No `Cache-Control`, `X-Data-Age`, or consistency level indicators on REST or MCP responses.
- **Compensating Controls**:
  - The `SearchMessagesTool` returns effective timerange metadata, which provides temporal context for search results
  - Entity timestamps (created_at, updated_at) are available in response payloads
- **Remediation Timeline**: 30 days
- **Recommendation**: Add `Cache-Control` or custom freshness headers to REST API responses. Include `data_freshness` or `consistency_level` metadata in MCP tool responses.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/security/AccessTokenServiceImpl.java`, `graylog2-server/src/main/java/org/graylog/security/DBGrantService.java`, `graylog2-server/src/main/java/org/graylog/mcp/tools/SearchMessagesTool.java`

---

## INFOs — Architecture and Design Inputs

### DATA-Q1: Sensitive Data Classification ⚡ (Tiered) — Demoted from BLOCKER

- **Severity**: INFO
- **Stage A**: Yes — user accounts (hashed passwords in MongoDB), LDAP bind passwords, webhook/notification secrets, access tokens, and ingested log content.
- **B1 — API response scoping: CLEAR.** `UserImpl.java:78-82` `@DbEntity.readableFields` excludes the password field; `UserSummary` response never contains password hashes. `EncryptedValue` wrapper (`EncryptedValue.java:50-60`) serializes as `{"is_set": true}` for LDAP bind passwords and notification secrets — plaintext never leaves the server. Ingested log content is returned verbatim but stream-level permissions still gate access.
- **B2 — Access control differentiation: CLEAR.** GRN-based RBAC with fine permissions (`USERS_READ/EDIT`, `EVENT_NOTIFICATIONS_READ/EDIT/DELETE`, `STREAMS_READ`, etc.). `isPermitted(permission, GRN)` checks enforced in resource handlers; `executionGuard.checkUserIsPermittedToSeeStreams()` in `MessagesResource`.
- **B3 — Formal classification metadata: INFO.** `EncryptedValue` and `@DbEntity.readableFields` are classification-by-type primitives for secret/field exposure; no PII classification on ingested log fields.
- **Overall**: Only B3 fires → **DATA-Q1 = INFO**. Graylog's secret handling and RBAC are robust; log-field PII is source-system–classified.
- **Recommendation (aspirational)**: Add optional log-field PII classification index and MCP tool redaction layer; document that ingested log content is source-system–classified.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/users/UserImpl.java` (readableFields), `UserSummary.java`, `EncryptedValue.java`, `EncryptedValueService.java`, `RestPermissions.java`, `MessagesResource.java`.

### API-Q1: Documented API Interface
- **Severity**: INFO (BLOCKER question — no gap found)
- **Finding**: Graylog exposes an extensive documented REST API via JAX-RS `@Path` annotations with Swagger/OpenAPI annotations (`io.swagger.v3.oas.annotations`). The OpenAPI spec is auto-generated and served at `/api/openapi` and `/api/openapi.yaml`. An explicit OpenAPI 3.1 spec exists at `api-specs/stream-output-filters.yml`. The MCP endpoint at `/api/mcp` provides a JSON-RPC interface for agent tool calls, fully documented with `@Operation` annotations.
- **Implication**: Agents can bind to the REST API via OpenAPI and to the MCP endpoint via the Model Context Protocol. Both surfaces are well-documented and stable.
- **Recommendation**: Continue maintaining OpenAPI annotations. Consider auto-generating MCP tool definitions from the OpenAPI spec.
- **Evidence**: `graylog2-server/src/main/java/org/graylog/mcp/server/McpRestResource.java`, `graylog2-server/src/main/java/org/graylog2/shared/rest/documentation/openapi/OpenApiResource.java`, `api-specs/stream-output-filters.yml`

### API-Q2: Machine-Readable API Specification
- **Severity**: INFO (RISK-QUALITY question — no gap found)
- **Finding**: OpenAPI spec is auto-generated from code annotations via `OpenApiResource.java` and served in JSON and YAML formats. This is kept in sync with the implementation since it is annotation-driven. The web interface generates API definitions via the `generate:apidefs` script.
- **Implication**: Agent tool definitions can be generated from the machine-readable OpenAPI spec, reducing manual tool authoring.
- **Recommendation**: Ensure the auto-generated spec includes all MCP-relevant endpoints.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/shared/rest/documentation/openapi/OpenApiResource.java`, `graylog2-web-interface/package.json`

### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No idempotency key support was found on write endpoints. The `LookupDataAdapterRefreshService` is the only file mentioning idempotency. Read-only agents do not execute write operations.
- **Implication**: If agent scope expands to write-enabled, idempotency must be addressed before deployment.
- **Recommendation**: Implement idempotency keys for critical write endpoints before expanding to write-enabled agent scope.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/lookup/LookupDataAdapterRefreshService.java`

### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: All REST API endpoints produce JSON (`@Produces(MediaType.APPLICATION_JSON)`). The MCP endpoint returns JSON-RPC responses. No XML or binary formats are used for API responses.
- **Implication**: JSON responses are directly consumable by LLM-based agents without format conversion.
- **Recommendation**: No action needed.
- **Evidence**: `graylog2-server/src/main/java/org/graylog/mcp/server/McpRestResource.java`

### API-Q6: Asynchronous Operation Support
- **Severity**: INFO (RISK-QUALITY question — no gap found)
- **Finding**: Graylog has a comprehensive system jobs framework for long-running operations (index rotation, range rebuilds, migrations). Background jobs are managed internally. The `SearchMessagesTool` is synchronous but scoped by `rangeSeconds` and `limit` parameters to bound execution time.
- **Implication**: Agents should be aware that search operations over large time ranges may be slow. System jobs operate asynchronously in the background.
- **Recommendation**: Document expected response times for MCP tools. Consider adding timeout hints to tool descriptions.
- **Evidence**: `graylog2-server/src/main/java/org/graylog/mcp/tools/SearchMessagesTool.java`

### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: Graylog has a comprehensive audit event system with 100+ event types covering all entity lifecycle changes (stream create/delete/update, user changes, input changes, etc.). MCP-specific events track protocol initialization, tool calls, and resource access. The event notification system supports webhook, email, and HTTP notifications.
- **Implication**: Future event-driven agents could subscribe to Graylog event notifications for proactive behavior.
- **Recommendation**: Expose MCP-specific audit events via the notification system for agent observability.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/audit/AuditEventTypes.java`

### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: `TooManyRequestsStatus` class defines HTTP 429 status. No rate limit headers (`X-RateLimit-Remaining`, `Retry-After`) are returned. No rate limit documentation was found.
- **Implication**: Agents cannot self-throttle based on rate limit signals. This compounds the STATE-Q5 rate limiting gap.
- **Recommendation**: When rate limiting is implemented (STATE-Q5), ensure rate limit headers are returned in all responses.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/rest/TooManyRequestsStatus.java`

### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO (BLOCKER question — no gap found)
- **Finding**: Graylog supports multiple authentication mechanisms suitable for machine identity: Access Token authentication (`AccessTokenAuthenticator`), Bearer Token (`BearerTokenRealm`), HTTP Header authentication (`HTTPHeaderAuthenticationRealm`), and session-based authentication. Access tokens can be created per-user with expiration dates. `AuditActor` includes `urn:graylog:user:<username>` for audit attribution. The MCP endpoint requires `MCP_SERVER_ACCESS` permission and authenticates via `@RequiresAuthentication`.
- **Implication**: Agents can authenticate using access tokens with full audit attribution. A dedicated "MCP Server Access" built-in role exists for granting MCP access.
- **Recommendation**: Create dedicated service accounts for each agent instance rather than sharing access tokens.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/security/realm/AccessTokenAuthenticator.java`, `graylog2-server/src/main/java/org/graylog2/shared/security/RestPermissions.java`

### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: INFO (RISK-SAFETY question — no gap found)
- **Finding**: Graylog implements fine-grained permissions via the `RestPermissions` system with `action:resource:instance` pattern (e.g., `streams:read`, `streams:edit`, `dashboards:create`). Grant-based authorization (`DBGrantService`, `GrantDTO`) supports per-entity capability grants (VIEW, MANAGE, OWN). The MCP `PermissionHelper` enforces permission checks at the tool level with `isPermitted(permission, instanceId)`.
- **Implication**: Agent identities can be scoped to read-only access on specific resources. The permission system is fine-grained enough for least-privilege agent deployments.
- **Recommendation**: Define a minimal permission set for MCP agent identities (e.g., read-only streams + search only).
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/shared/security/RestPermissions.java`, `graylog2-server/src/main/java/org/graylog/security/DBGrantService.java`, `graylog2-server/src/main/java/org/graylog/mcp/tools/PermissionHelper.java`

### AUTH-Q3: Action-Level Authorization
- **Severity**: INFO (RISK-SAFETY question — no gap found)
- **Finding**: Action-level authorization is enforced via `@RequiresPermissions` annotations on REST endpoints and explicit `permissionHelper.checkPermission(permission, instanceId)` calls in MCP tools. Different actions (read, edit, create, delete) have distinct permissions. The MCP `SearchMessagesTool` delegates to the query engine which performs its own permission checks.
- **Implication**: An agent can be granted read access without write access at the action level. MCP tools inherit the calling user's permission boundary.
- **Recommendation**: No action needed — the action-level authorization is comprehensive.
- **Evidence**: `graylog2-server/src/main/java/org/graylog/mcp/server/McpRestResource.java`, `graylog2-server/src/main/java/org/graylog/mcp/tools/PermissionHelper.java`

### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: The MCP endpoint extracts the current user via `getCurrentUser()` and propagates identity through `PermissionHelper` for all tool calls. `SearchUser` context is passed to the search engine. `SecurityContext` provides the authenticated principal. The system tracks which user initiated which action.
- **Implication**: Agent identity is propagated through the request pipeline. The MCP endpoint distinguishes between the agent's service identity and the calling user's permissions.
- **Recommendation**: Consider adding explicit agent-vs-human identity distinction in audit logs.
- **Evidence**: `graylog2-server/src/main/java/org/graylog/mcp/server/McpRestResource.java`, `graylog2-server/src/main/java/org/graylog/mcp/tools/PermissionHelper.java`

### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: `EncryptedValueService` provides AES encryption for sensitive configuration values using a `password_secret` key injected from configuration (minimum 16 characters). `AccessTokenCipher` encrypts access tokens at rest. The `docker-compose.yml` uses environment variable placeholders for secrets (`GRAYLOG_PASSWORD_SECRET`, `GRAYLOG_ROOT_PASSWORD_SHA2`). No hardcoded credentials were found in source code. The `password_secret` is configuration-injected, not hardcoded.
- **Implication**: Credential management follows security best practices for a self-hosted product. Operators must manage the `password_secret` securely.
- **Recommendation**: Document the requirement to use a secrets manager for `password_secret` in production deployments.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/security/encryption/EncryptedValueService.java`, `data-node/migration/docker-compose.yml`

### AUTH-Q7: Agent Identity Suspension
- **Severity**: INFO (RISK-SAFETY question — no gap found)
- **Finding**: Access tokens can be deleted/revoked (`USER_ACCESS_TOKEN_DELETE` audit event, `AccessTokenServiceImpl.deleteById()`, `deleteAllForUser()`). User accounts can be disabled via `AccountStatus.DISABLED` — the `AccessTokenAuthenticator` checks account status and rejects disabled accounts. `UserSessionTerminationService` terminates all active sessions for disabled/deleted users.
- **Implication**: If an agent identity (access token) is compromised, it can be immediately revoked. If the agent's user account is disabled, all sessions and access tokens become invalid.
- **Recommendation**: No action needed — identity suspension mechanisms are comprehensive.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/security/AccessTokenServiceImpl.java`, `graylog2-server/src/main/java/org/graylog2/security/realm/AccessTokenAuthenticator.java`, `graylog2-server/src/main/java/org/graylog2/security/UserSessionTerminationService.java`

### STATE-Q2: Queryable Current State
- **Severity**: INFO (RISK-QUALITY extended — no gap found)
- **Finding**: Graylog exposes GET endpoints for all managed entities (streams, inputs, dashboards, users, index sets, etc.). `PaginationParameters` provides `query`, `page`, `per_page`, `sort`, `order` parameters. MCP tools (`ListStreamsTool`, `ListInputsTool`, `ListFieldsTool`, `ListIndicesTool`, `ListIndexSetsTool`, `SystemInfoTool`) provide queryable state access.
- **Implication**: Agents can inspect current system state before taking action via MCP tools or REST API.
- **Recommendation**: No action needed.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/rest/PaginationParameters.java`, `graylog2-server/src/main/java/org/graylog/mcp/tools/`

### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits per agent identity were found. Read-only agents do not modify records, trigger spend, or delete data.
- **Implication**: If scope expands to write-enabled, transaction limits must be implemented.
- **Recommendation**: Plan transaction limit infrastructure before expanding to write-enabled scope.
- **Evidence**: No evidence found — absence is itself a finding.

### DATA-Q3: Selective Query Support
- **Severity**: INFO (RISK-QUALITY extended — no gap found)
- **Finding**: Strong pagination support exists. `PaginationParameters` provides `query`, `page`, `per_page`, `sort`, `order`. The MCP `SearchMessagesTool` has `limit` (default 50), `offset`, `fields` selection, `streams` scoping, and `rangeSeconds` parameters. The OpenAPI spec in `api-specs/stream-output-filters.yml` defines pagination parameters.
- **Implication**: Agents can retrieve bounded, filtered result sets. The default limit of 50 messages prevents unbounded queries.
- **Recommendation**: No action needed — pagination and filtering are well-implemented.
- **Evidence**: `graylog2-server/src/main/java/org/graylog/mcp/tools/SearchMessagesTool.java`, `graylog2-server/src/main/java/org/graylog2/rest/PaginationParameters.java`, `api-specs/stream-output-filters.yml`

### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality scores, completeness metrics, or data profiling reports were found. Graylog provides metrics for incoming message rates (`stream_incoming_messages`) and indexer health, but no data quality indicators for the log data itself.
- **Implication**: Agents cannot assess log data completeness before reasoning. This is typical for log management platforms.
- **Recommendation**: Consider exposing message completeness metrics (e.g., messages with missing fields) via the MCP tools.
- **Evidence**: `graylog2-server/src/main/resources/prometheus-exporter.yml`

### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: REST API response models and database entity field names use semantically meaningful names: `stream_id`, `destination_type`, `created_at`, `updated_at`, `expires_at`, `last_access`, `username`. MCP tool parameters use clear names: `query`, `streams`, `stream_categories`, `range_seconds`, `limit`, `offset`. No legacy abbreviations or cryptic codes were found.
- **Implication**: Agent LLMs can interpret field names without a data dictionary.
- **Recommendation**: No action needed.
- **Evidence**: `graylog2-server/src/main/java/org/graylog/mcp/tools/SearchMessagesTool.java`, `api-specs/stream-output-filters.yml`

### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal data catalog or metadata layer was found (no Glue Data Catalog, Collibra, or DataHub integration). The OpenAPI spec serves as an API catalog. Field type profiles in the indexer provide schema metadata for indexed log fields.
- **Implication**: Agent tool builders must rely on the OpenAPI spec and MCP tool descriptions for data discovery.
- **Recommendation**: Consider exposing field metadata (types, cardinality) via MCP tools for agent-assisted data exploration.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/shared/rest/documentation/openapi/OpenApiResource.java`

### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: Prometheus metrics include business-relevant metrics: `stream_incoming_messages` (per stream), indexer throughput, journal utilization, pipeline processing metrics, and forwarder metrics (1384-line mapping in `prometheus-exporter.yml`). These are infrastructure/operational metrics rather than business outcome metrics (resolution rates, agent success rates).
- **Implication**: Agent behavior metrics are not currently tracked. When agents are deployed, custom metrics for agent-initiated search success rates, result relevance, and response times should be added.
- **Recommendation**: Add Prometheus metrics for MCP endpoint usage: tool call counts, success/failure rates, response times per tool.
- **Evidence**: `graylog2-server/src/main/resources/prometheus-exporter.yml`

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO (no gap — BLOCKER criterion satisfied)
- **Finding**: Graylog exposes a well-documented REST API via JAX-RS annotations with Swagger/OpenAPI annotations. Auto-generated OpenAPI spec at `/api/openapi`. MCP endpoint at `/api/mcp` provides JSON-RPC for agents.
- **Gap**: None
- **Recommendation**: Continue maintaining OpenAPI annotations.
- **Evidence**: `graylog2-server/src/main/java/org/graylog/mcp/server/McpRestResource.java`, `graylog2-server/src/main/java/org/graylog2/shared/rest/documentation/openapi/OpenApiResource.java`, `api-specs/stream-output-filters.yml`

#### API-Q2: Machine-Readable API Specification
- **Severity**: INFO (no gap — RISK-QUALITY criterion satisfied)
- **Finding**: OpenAPI auto-generated from annotations, served at `/api/openapi` and `/api/openapi.yaml`. Kept in sync with implementation.
- **Gap**: None
- **Recommendation**: Ensure MCP-relevant endpoints are fully annotated.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/shared/rest/documentation/openapi/OpenApiResource.java`

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: Multiple ExceptionMappers exist. MCP returns JSON-RPC errors with error codes. REST API error formats are inconsistent across mappers. No retryable/non-retryable classification.
- **Gap**: No unified error format with retryable indicators across REST endpoints.
- **Recommendation**: Standardize REST error envelope with error_code, message, retryable, details.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/rest/ElasticsearchExceptionMapper.java`, `graylog2-server/src/main/java/org/graylog2/rest/ValidationExceptionMapper.java`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No idempotency key support on write endpoints. Read-only agents do not execute writes.
- **Gap**: No idempotency keys (INFO for read-only scope).
- **Recommendation**: Address before expanding to write-enabled scope.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/lookup/LookupDataAdapterRefreshService.java`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: All API responses are JSON. MCP returns JSON-RPC.
- **Gap**: None
- **Recommendation**: No action needed.
- **Evidence**: `graylog2-server/src/main/java/org/graylog/mcp/server/McpRestResource.java`

#### API-Q6: Asynchronous Operation Support
- **Severity**: INFO (no gap — extended triggered, async patterns exist)
- **Finding**: System jobs framework handles long-running operations. SearchMessagesTool is synchronous but bounded.
- **Gap**: None — async patterns exist for long-running operations.
- **Recommendation**: Document timeout expectations for MCP tools.
- **Evidence**: `graylog2-server/src/main/java/org/graylog/mcp/tools/SearchMessagesTool.java`

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: 100+ audit event types covering all entity lifecycle changes. MCP-specific events. Notification system supports webhooks.
- **Gap**: None
- **Recommendation**: Expose MCP audit events via notification system.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/audit/AuditEventTypes.java`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: TooManyRequestsStatus defines 429 status. No rate limit headers or documentation.
- **Gap**: No rate limit headers returned.
- **Recommendation**: Implement rate limit headers when rate limiting is added (STATE-Q5).
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/rest/TooManyRequestsStatus.java`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO (no gap — BLOCKER criterion satisfied)
- **Finding**: Access Token, Bearer Token, HTTP Header, and session authentication. AuditActor provides URN-based attribution. MCP requires MCP_SERVER_ACCESS permission. Built-in "MCP Server Access" role.
- **Gap**: None
- **Recommendation**: Create dedicated service accounts per agent instance.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/security/realm/AccessTokenAuthenticator.java`, `graylog2-server/src/main/java/org/graylog2/shared/security/RestPermissions.java`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: INFO (no gap — RISK-SAFETY criterion satisfied)
- **Finding**: Fine-grained `action:resource:instance` permissions. Grant-based authorization with VIEW/MANAGE/OWN capabilities. MCP PermissionHelper enforces per-tool permission checks.
- **Gap**: None
- **Recommendation**: Define minimal agent permission set.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/shared/security/RestPermissions.java`, `graylog2-server/src/main/java/org/graylog/security/DBGrantService.java`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: INFO (no gap — RISK-SAFETY criterion satisfied)
- **Finding**: @RequiresPermissions on endpoints. PermissionHelper.checkPermission() in MCP tools. Distinct read/edit/create/delete permissions.
- **Gap**: None
- **Recommendation**: No action needed.
- **Evidence**: `graylog2-server/src/main/java/org/graylog/mcp/tools/PermissionHelper.java`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: SecurityContext, SearchUser, and PermissionHelper propagate identity through MCP tool calls. getCurrentUser() tracks initiating user.
- **Gap**: No explicit agent-vs-human identity distinction.
- **Recommendation**: Add agent identity type flag to audit context.
- **Evidence**: `graylog2-server/src/main/java/org/graylog/mcp/server/McpRestResource.java`

#### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: EncryptedValueService with AES encryption. AccessTokenCipher for token encryption. password_secret from configuration. No hardcoded secrets.
- **Gap**: None — credentials are managed securely.
- **Recommendation**: Document secrets manager requirement for operators.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/security/encryption/EncryptedValueService.java`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Comprehensive audit logging with MCP-specific events and user attribution. Stored in MongoDB without immutability guarantees.
- **Gap**: Audit logs not immutable/tamper-evident.
- **Recommendation**: Forward audit events to immutable storage.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/audit/AuditEventSender.java`, `graylog2-server/src/main/java/org/graylog2/audit/AuditEventTypes.java`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: INFO (no gap — RISK-SAFETY criterion satisfied)
- **Finding**: Token revocation, account disable, session termination. AccountStatus check in AccessTokenAuthenticator.
- **Gap**: None
- **Recommendation**: No action needed.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/security/AccessTokenServiceImpl.java`, `graylog2-server/src/main/java/org/graylog2/security/UserSessionTerminationService.java`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No saga, compensation, or rollback patterns. MongoDBUpsertRetryer deprecated. Individual document atomicity only.
- **Gap**: No multi-step compensation mechanism.
- **Recommendation**: Document multi-step operations and implement compensation if write scope expands.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/database/MongoDBUpsertRetryer.java`

#### STATE-Q2: Queryable Current State
- **Severity**: INFO (no gap — extended triggered, queryable state exists)
- **Finding**: GET endpoints for all entities. PaginationParameters. MCP tools for listing streams, inputs, fields, indices, index sets.
- **Gap**: None
- **Recommendation**: No action needed.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/rest/PaginationParameters.java`, `graylog2-server/src/main/java/org/graylog/mcp/tools/`

#### STATE-Q3: Concurrency Controls
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled AND service has persistent state
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: No circuit breakers on OpenSearch dependency calls. Retry logic in ChunkedBulkIndexer but no circuit breaker pattern.
- **Gap**: No circuit breakers protecting external dependency calls.
- **Recommendation**: Implement Resilience4j circuit breakers on OpenSearch client calls.
- **Evidence**: `graylog-storage-opensearch2/`, `graylog-storage-opensearch3/`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: TooManyRequestsStatus exists but no systematic rate limiting. MCP endpoint has no rate limits.
- **Gap**: No API-layer rate limiting enforcement.
- **Recommendation**: Implement per-token rate limiting for MCP and REST APIs.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/rest/TooManyRequestsStatus.java`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No transaction limits. Read-only agents do not modify data.
- **Gap**: No transaction limits (INFO for read-only).
- **Recommendation**: Implement before expanding to write-enabled scope.
- **Evidence**: No evidence found — absence is itself a finding.

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q2: Configurable Approval Gates
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: docker-compose for local dev/migration. CI runs full-backend-tests against containers. No production-equivalent staging.
- **Gap**: No production-equivalent staging environment for agent testing.
- **Recommendation**: Create staging environment with seed data for agent validation.
- **Evidence**: `data-node/migration/docker-compose.yml`, `.github/workflows/build.yml`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
#### DATA-Q1: Sensitive Data Classification ⚡ (Tiered)
- **Severity**: INFO
- **Stage A**: Yes — Graylog stores user accounts (hashed password in MongoDB), LDAP bind passwords, webhook/notification secrets, access tokens, and ingested log content (which may include PII from source systems).
- **B1 — API response scoping: CLEAR.** `UserImpl.java:78-82` `@DbEntity` annotation marks `readableFields` excluding the password field; `UserSummary` response model contains no password hash. LDAP `AuthServiceBackend.systemUserPassword()` uses `EncryptedValue` wrapper whose serializer returns `{"is_set": true}` without the encrypted value or salt (`EncryptedValue.java:50-60`). Notification/webhook secrets follow the same `EncryptedValue` pattern. Ingested log-message content is returned verbatim (source-system responsibility), but stream-level permissions still gate access.
- **B2 — Access control differentiation: CLEAR.** Granular GRN-based RBAC in `RestPermissions.java` with fine permission families (`USERS_READ/EDIT`, `EVENT_NOTIFICATIONS_READ/EDIT/DELETE`, `STREAMS_READ`, `DATANODE_READ`, etc.). `UsersResource.getbyId()` checks `isPermitted(USERS_EDIT, username)`. Stream-level access enforced via `executionGuard.checkUserIsPermittedToSeeStreams()` in `MessagesResource`.
- **B3 — Formal classification metadata: INFO.** `EncryptedValue` wrapper IS a classification-by-type primitive for secret fields; `@DbEntity.readableFields` is a declarative field exposure list. No PII classification on log fields.
- **Overall**: Only B3 fires for log-field PII classification → **DATA-Q1 = INFO**. Graylog properly excludes secrets from API responses and enforces RBAC.
- **Recommendation (aspirational)**: Add an optional log-field classification index and MCP tool redaction layer; document that ingested log content is source-system-classified.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/users/UserImpl.java` (readableFields), `UserSummary.java`, `EncryptedValue.java`, `EncryptedValueService.java`, `RestPermissions.java`, `MessagesResource.java`, `AuthorizationInterceptor` pattern via Shiro.

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No data residency controls. Log data stored without region constraints.
- **Gap**: No data residency enforcement.
- **Recommendation**: Add residency metadata to streams/index sets.
- **Evidence**: `data-node/migration/docker-compose.yml`

#### DATA-Q3: Selective Query Support
- **Severity**: INFO (no gap — extended triggered, pagination exists)
- **Finding**: PaginationParameters. SearchMessagesTool with limit/offset/fields/streams. Default limit 50.
- **Gap**: None
- **Recommendation**: No action needed.
- **Evidence**: `graylog2-server/src/main/java/org/graylog/mcp/tools/SearchMessagesTool.java`, `graylog2-server/src/main/java/org/graylog2/rest/PaginationParameters.java`

#### DATA-Q4: System of Record Designations
- **Severity**: RISK-QUALITY
- **Finding**: Graylog is de facto SoR for log data. MongoDB for config, OpenSearch for logs. No formal documentation.
- **Gap**: No formal SoR designations.
- **Recommendation**: Document data ownership designations.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/database/`

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK-QUALITY
- **Finding**: Entity timestamps exist (created_at, updated_at, expires_at). SearchMessagesTool returns effectiveTimerange. No Cache-Control or freshness headers.
- **Gap**: No freshness signaling in API responses.
- **Recommendation**: Add Cache-Control or custom freshness headers.
- **Evidence**: `graylog2-server/src/main/java/org/graylog/mcp/tools/SearchMessagesTool.java`

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: log4j2.xml uses PatternLayout without masking. Usernames logged in cleartext in audit events and permission checks.
- **Gap**: No PII redaction in application logs.
- **Recommendation**: Implement log masking via log4j2 RewritePolicy.
- **Evidence**: `graylog2-server/src/main/resources/log4j2.xml`, `graylog2-server/src/main/java/org/graylog2/audit/AuditActor.java`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics. Stream incoming message rates tracked but no completeness indicators.
- **Gap**: No data quality scores.
- **Recommendation**: Expose completeness metrics via MCP tools.
- **Evidence**: `graylog2-server/src/main/resources/prometheus-exporter.yml`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: OpenAPI auto-generated. No explicit API versioning. No breaking change detection in CI.
- **Gap**: No API versioning or breaking change detection.
- **Recommendation**: Add OpenAPI diff checking to CI.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/shared/rest/documentation/openapi/OpenApiResource.java`, `.github/workflows/build.yml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Semantically clear field names throughout. No legacy abbreviations.
- **Gap**: None
- **Recommendation**: No action needed.
- **Evidence**: `graylog2-server/src/main/java/org/graylog/mcp/tools/SearchMessagesTool.java`, `api-specs/stream-output-filters.yml`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal data catalog. OpenAPI spec serves as API catalog. Field type profiles provide indexer metadata.
- **Gap**: No data catalog.
- **Recommendation**: Expose field metadata via MCP tools.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/shared/rest/documentation/openapi/OpenApiResource.java`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: OpenTelemetry tracing via TracingModule/TracerProvider. GraylogSemanticAttributes. Logs use PatternLayout (not JSON). No correlation IDs.
- **Gap**: Logs not structured. No correlation ID propagation.
- **Recommendation**: Add JSON log appender with trace ID fields.
- **Evidence**: `graylog2-server/src/main/java/org/graylog/tracing/TracingModule.java`, `graylog2-server/src/main/resources/log4j2.xml`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: Prometheus metrics exported (1384 mappings). No self-monitoring alerting configured for APIs.
- **Gap**: No alerting thresholds for API surface.
- **Recommendation**: Define Prometheus alerting rules for MCP and REST API metrics.
- **Evidence**: `graylog2-server/src/main/resources/prometheus-exporter.yml`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: Infrastructure/operational Prometheus metrics. No agent-specific business outcome metrics.
- **Gap**: No agent behavior metrics.
- **Recommendation**: Add MCP tool call metrics to Prometheus exporter.
- **Evidence**: `graylog2-server/src/main/resources/prometheus-exporter.yml`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance
- **Severity**: RISK-QUALITY
- **Finding**: No IaC in repository. Self-hosted product — operators provide infrastructure.
- **Gap**: No IaC for agent-facing surface.
- **Recommendation**: Publish reference IaC modules with security defaults.
- **Evidence**: Absence of IaC files in repository.

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: GitHub Actions CI with build, frontend, backend, full-backend tests. MCP tests exist. No API contract testing.
- **Gap**: No breaking change detection in CI.
- **Recommendation**: Add OpenAPI spec comparison to CI pipeline.
- **Evidence**: `.github/workflows/build.yml`, `graylog2-server/src/test/java/org/graylog/mcp/server/McpServiceTest.java`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: No deployment rollback configuration. Self-hosted product — operator responsibility.
- **Gap**: No rollback capability in repository.
- **Recommendation**: Document rollback procedures.
- **Evidence**: `.github/workflows/build.yml`, `pom.xml`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: MCP unit tests exist (McpRestResourceTest, McpServiceTest). Full-backend-tests module. No contract tests or comprehensive API test suites.
- **Gap**: Limited MCP endpoint test coverage.
- **Recommendation**: Expand MCP test coverage for edge cases and permission boundaries.
- **Evidence**: `graylog2-server/src/test/java/org/graylog/mcp/server/McpRestResourceTest.java`, `graylog2-server/src/test/java/org/graylog/mcp/server/McpServiceTest.java`

#### ENG-Q5: Encryption at Rest
- **Severity**: RISK-QUALITY
- **Finding**: EncryptedValueService and AccessTokenCipher for application-level encryption. No database-level encryption at rest.
- **Gap**: No database-level encryption at rest for MongoDB/OpenSearch.
- **Recommendation**: Document encryption at rest requirements for operators.
- **Evidence**: `graylog2-server/src/main/java/org/graylog2/security/encryption/EncryptedValueService.java`, `data-node/migration/docker-compose.yml`

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `graylog2-server/src/main/java/org/graylog/mcp/server/McpRestResource.java` | API-Q1, API-Q3, API-Q5, AUTH-Q1, AUTH-Q3, AUTH-Q4, STATE-Q5 |
| `graylog2-server/src/main/java/org/graylog/mcp/server/McpService.java` | AUTH-Q6 |
| `graylog2-server/src/main/java/org/graylog/mcp/tools/PermissionHelper.java` | AUTH-Q2, AUTH-Q3, AUTH-Q4, DATA-Q6 |
| `graylog2-server/src/main/java/org/graylog/mcp/tools/SearchMessagesTool.java` | DATA-Q1, DATA-Q3, DATA-Q5, API-Q6 |
| `graylog2-server/src/main/java/org/graylog2/shared/security/RestPermissions.java` | AUTH-Q1, AUTH-Q2 |
| `graylog2-server/src/main/java/org/graylog/security/DBGrantService.java` | AUTH-Q2, DATA-Q5 |
| `graylog2-server/src/main/java/org/graylog/security/Capability.java` | AUTH-Q2 |
| `graylog2-server/src/main/java/org/graylog2/audit/AuditEventSender.java` | AUTH-Q6 |
| `graylog2-server/src/main/java/org/graylog2/audit/AuditEventTypes.java` | AUTH-Q6, API-Q7 |
| `graylog2-server/src/main/java/org/graylog2/audit/AuditActor.java` | AUTH-Q6, DATA-Q6 |
| `graylog2-server/src/main/java/org/graylog2/security/AccessTokenServiceImpl.java` | AUTH-Q7, DATA-Q1, DATA-Q5, ENG-Q5 |
| `graylog2-server/src/main/java/org/graylog2/security/realm/AccessTokenAuthenticator.java` | AUTH-Q1, AUTH-Q7, DATA-Q6 |
| `graylog2-server/src/main/java/org/graylog2/security/UserSessionTerminationService.java` | AUTH-Q7 |
| `graylog2-server/src/main/java/org/graylog2/security/encryption/EncryptedValueService.java` | AUTH-Q5, DATA-Q1, ENG-Q5 |
| `graylog2-server/src/main/java/org/graylog2/database/MongoDBUpsertRetryer.java` | STATE-Q1 |
| `graylog2-server/src/main/java/org/graylog2/rest/PaginationParameters.java` | STATE-Q2, DATA-Q3 |
| `graylog2-server/src/main/java/org/graylog2/rest/TooManyRequestsStatus.java` | STATE-Q5, API-Q8 |
| `graylog2-server/src/main/java/org/graylog2/rest/ElasticsearchExceptionMapper.java` | API-Q3 |
| `graylog2-server/src/main/java/org/graylog2/rest/ValidationExceptionMapper.java` | API-Q3 |
| `graylog2-server/src/main/java/org/graylog/tracing/TracingModule.java` | OBS-Q1 |
| `graylog2-server/src/main/java/org/graylog/tracing/TracerProvider.java` | OBS-Q1 |
| `graylog2-server/src/main/java/org/graylog/tracing/GraylogSemanticAttributes.java` | OBS-Q1 |
| `graylog2-server/src/main/java/org/graylog2/shared/rest/documentation/openapi/OpenApiResource.java` | API-Q2, DISC-Q1, DISC-Q3 |
| `graylog2-server/src/main/java/org/graylog2/lookup/LookupDataAdapterRefreshService.java` | API-Q4 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `api-specs/stream-output-filters.yml` | API-Q1, DATA-Q3, DISC-Q2 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/build.yml` | ENG-Q2, ENG-Q3, ENG-Q4, HITL-Q3, DISC-Q1 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `data-node/migration/docker-compose.yml` | AUTH-Q5, DATA-Q2, HITL-Q3, ENG-Q5 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `pom.xml` | ENG-Q3 |
| `graylog2-web-interface/package.json` | API-Q2, DISC-Q1 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `graylog2-server/src/main/resources/log4j2.xml` | OBS-Q1, DATA-Q6 |
| `graylog2-server/src/main/resources/prometheus-exporter.yml` | OBS-Q2, OBS-Q3, DATA-Q7 |

### Test Files
| File | Questions Referenced |
|------|---------------------|
| `graylog2-server/src/test/java/org/graylog/mcp/server/McpRestResourceTest.java` | ENG-Q2, ENG-Q4 |
| `graylog2-server/src/test/java/org/graylog/mcp/server/McpServiceTest.java` | ENG-Q2, ENG-Q4 |

### Storage Modules
| File | Questions Referenced |
|------|---------------------|
| `graylog-storage-opensearch2/` | STATE-Q4, DATA-Q4 |
| `graylog-storage-opensearch3/` | STATE-Q4, DATA-Q4 |
