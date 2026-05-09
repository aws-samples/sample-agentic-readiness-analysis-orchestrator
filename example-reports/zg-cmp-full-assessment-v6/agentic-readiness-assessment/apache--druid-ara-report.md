# Agentic Readiness Assessment Report

**Target**: . (apache--druid)
**Date**: 2025-05-07
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: monorepo
**Service Archetype**: data-gateway (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: java, analytics, database
**Context**: Apache Druid: high-performance real-time analytics database.

**Archetype Justification**: Apache Druid is a read-heavy analytics database. Its primary surface is a query engine accepting SQL and native JSON queries, returning analytics results. While it has CRUD operations for datasource management and ingestion tasks, the dominant traffic pattern is query execution (>90% reads), fitting the data-gateway archetype.

**Surface flags**:
- has_persistent_data_store: true
- has_http_rpc_surface: true
- has_auth_surface: true
- has_write_operations: true
- has_logging_of_user_data: true

---

## Readiness Profile: Pilot-Ready (Safety Concerns)

**BLOCKERs**: 1 | **RISK-SAFETY**: 5 | **RISK-QUALITY**: 9 | **INFOs**: 14

**Classification Rationale**: This repo has 1 High finding (AUTH-Q1 BLOCKER), 14 Medium findings (5 safety-impact, 9 quality-impact), and 14 Low findings. The matched rule is "1-2 High → Remediation Required." V5 Readiness Profile aligns: 1 BLOCKER forces Remediation Required regardless of RISK-SAFETY count.

Resolve all blockers before any agent deployment — including pilots. The critical gap is machine identity authentication support for agent principals.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 1 |
| RISK-SAFETY | 5 |
| RISK-QUALITY | 9 |
| INFO | 14 |
| N/A | 0 |
| Not Evaluated (extended) | 14 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 5
**Extended Questions Not Triggered**: 14
**Questions N/A (repo_type: monorepo)**: 0
**Service Archetype**: data-gateway (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: Druid's authentication framework is pluggable (Authenticator interface chain) and supports HTTP Basic, Kerberos, LDAP, and PAC4J/OIDC. However, there is no native support for service account or machine identity authentication with principal attribution for autonomous agents. The BasicHTTPAuthenticator is credential-based (username/password), not designed for machine-to-machine OAuth2 client credentials flows. The PAC4J extension supports OIDC but targets human interactive login (browser-based SSO), not client_credentials grant.
- **Gap**: No OAuth2 client credentials flow, no API key with principal attribution, no mTLS-based service account mechanism designed for agent identities. Existing auth mechanisms target human users or inter-node communication (internal system credentials via Escalator pattern). An agent would need to use a shared username/password credential with no differentiation between agent instances.
- **Remediation**:
  - **Immediate**: Implement an Authenticator extension supporting OAuth2 client_credentials or API key-based machine identity with per-agent principal attribution in audit logs. Alternatively, deploy an API Gateway (e.g., AWS API Gateway, Kong) in front of Druid that handles machine identity and passes authenticated principal headers.
  - **Target State**: Agent identities are individually authenticated, attributed in audit logs, and distinguishable from human users.
  - **Estimated Effort**: Medium
  - **Dependencies**: AUTH-Q6 (audit logging immutability depends on knowing the agent principal)
- **Evidence**: `server/src/main/java/org/apache/druid/server/security/Authenticator.java`, `extensions-core/druid-basic-security/`, `extensions-core/druid-pac4j/`

---

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Druid's authorization model supports resource-level and action-level scoping. The `Authorizer` interface evaluates `(AuthenticationResult, Resource, Action)` where Resource has types (DATASOURCE, VIEW, CONFIG, STATE, SYSTEM_TABLE, QUERY_CONTEXT, EXTERNAL) and Action can be READ or WRITE. The BasicHTTPAuthorizer extension supports per-user role assignments with resource-regex patterns.
- **Gap**: While the authorization model exists, it operates at a coarse granularity — permissions are scoped to resource types and regex patterns over resource names, not to individual API endpoints or specific operations within a resource. There is no built-in concept of "agent identity with restricted scope" vs "admin identity." An agent granted READ on datasources gets READ on all matching datasources.
- **Compensating Controls**:
  - Deploy an API Gateway with fine-grained route-level policies restricting agent access to specific endpoints
  - Create dedicated Druid users with narrow resource-regex patterns limiting to specific datasources
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create dedicated authorization roles for agent identities with minimal resource-regex patterns. Consider extending the Authorizer to support endpoint-level scoping.
- **Evidence**: `server/src/main/java/org/apache/druid/server/security/Authorizer.java`, `server/src/main/java/org/apache/druid/server/security/ResourceType.java`, `server/src/main/java/org/apache/druid/server/security/Resource.java`

#### AUTH-Q6: Immutable Audit Logging — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Druid has an AuditManager framework with two implementations (SQLAuditManager, LoggingAuditManager). The SQLAuditManager records audit entries in a metadata store. However, audit logs are NOT immutable — the `removeAuditLogsOlderThan()` method allows deletion, and there is no cryptographic hash chaining or tamper-evidence mechanism. Any database administrator with metadata store access can modify or delete audit entries without detection.
- **Gap**: Audit logs are append-only with scheduled pruning (KillAuditLog duty) but lack tamper-evidence. No CloudTrail integration, no object-lock storage, no hash chains.
- **Compensating Controls**:
  - Stream audit events to an immutable external store (S3 with object lock, CloudWatch Logs with retention lock)
  - Deploy a LoggingAuditManager that writes to a tamper-evident log aggregation system
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement an AuditManager extension that writes to an immutable store (e.g., S3 with Object Lock enabled) or integrate with AWS CloudTrail for agent-initiated operations via an API Gateway proxy.
- **Evidence**: `processing/src/main/java/org/apache/druid/audit/AuditManager.java`, `server/src/main/java/org/apache/druid/server/audit/SQLAuditManager.java`

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The BasicHTTPAuthorizer supports disabling individual users, and the Druid coordinator exposes APIs for managing basic-security users. However, there is no dedicated mechanism for immediate agent identity suspension with automatic propagation. User disablement requires a coordinator API call and depends on the authentication cache refresh interval.
- **Gap**: No immediate, propagated suspension mechanism for agent identities. Cache-based authentication means there is a window (configurable but non-zero) between disabling a user and that user being locked out of all Druid nodes.
- **Compensating Controls**:
  - Set BasicHTTPAuthenticator cache duration to minimum value for near-immediate propagation
  - Deploy an API Gateway with API key revocation capability for instant agent lockout
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Deploy an API Gateway layer that provides instant API key revocation for agent identities, independent of Druid's internal auth cache refresh.
- **Evidence**: `extensions-core/druid-basic-security/`, `server/src/main/java/org/apache/druid/server/security/`

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Druid has no HTTP-level rate limiting for its REST APIs. The only traffic management is internal query scheduling via `QueryScheduler` using resilience4j bulkheads for query lane isolation (ManualQueryLaningStrategy). This controls concurrent query execution but does not rate-limit API requests at the HTTP layer. There is no API Gateway, WAF, or application-level rate-limiting middleware.
- **Gap**: No request-level rate limiting. An agent (or any client) can send unlimited requests to any Druid endpoint. The QueryScheduler provides back-pressure on query execution only, not on the API surface as a whole.
- **Compensating Controls**:
  - Deploy an API Gateway (AWS API Gateway, Kong, Envoy) with throttling policies in front of Druid
  - Configure query lane isolation to limit agent queries to a dedicated lane with bounded concurrency
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Deploy an API Gateway with usage plans and throttling in front of all Druid API endpoints. Configure per-agent rate limits to prevent runaway agent loops.
- **Evidence**: `server/src/main/java/org/apache/druid/server/QueryScheduler.java`, `server/src/main/java/org/apache/druid/server/scheduling/ManualQueryLaningStrategy.java`, root `pom.xml` (resilience4j-bulkhead)

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Druid uses Log4j2 for logging and emits query text, user identity, and request context in logs. There is no PII scrubbing middleware, no log masking utilities, and no field-level redaction in the logging pipeline. Query text logged by the RequestLogger may contain user-submitted data. The AuditManager stores the full payload of configuration changes as JSON without redaction.
- **Gap**: No PII redaction in logs. User-submitted query text, identifiers, and configuration payloads are logged verbatim. No integration with Macie, Presidio, or custom log scrubbing.
- **Compensating Controls**:
  - Configure Log4j2 pattern layouts to exclude sensitive fields
  - Deploy a log aggregation layer (CloudWatch, Elasticsearch) with field-level masking
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement a custom Log4j2 filter or appender that redacts PII patterns from log output. For query logs, redact literal values from SQL/native query text before logging.
- **Evidence**: `extensions-core/s3-extensions/src/test/resources/log4j2.xml`, `server/src/main/java/org/apache/druid/server/audit/SQLAuditManager.java`

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Druid has no OpenAPI, Swagger, or machine-readable API specification. The REST API is defined entirely through JAX-RS annotations in Java source code across 30+ Resource classes. There are .proto files for the gRPC contrib extension, but these cover only the query surface for gRPC clients, not the full management API.
- **Gap**: No machine-readable spec for the majority of Druid's REST API surface. Agent tool generation requires manual inspection of Java source code.
- **Compensating Controls**:
  - Use JAX-RS annotation scanning tools (e.g., swagger-jaxrs2) to auto-generate OpenAPI specs
  - Maintain a manually curated tool definition for the subset of APIs agents will use
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Integrate swagger-jaxrs2 or a similar annotation scanner to auto-generate OpenAPI specs from existing JAX-RS annotations. This could be a build step producing a versioned spec artifact.
- **Evidence**: `server/src/main/java/org/apache/druid/server/http/DataSourcesResource.java`, `extensions-contrib/grpc-query/src/main/proto/query.proto`

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Druid has a sophisticated `DruidException` framework with persona targeting (USER/OPERATOR/DEVELOPER), HTTP status code categories (400, 401, 403, 404, 409, 429, 500), error codes, and sanitization strategies. JAX-RS exception mappers translate exceptions to structured JSON responses. Error responses include `error`, `errorMessage`, and `errorCode` fields.
- **Gap**: While DruidException provides structured errors internally, the error response contract is not standardized across all endpoints. Some older endpoints return plain text errors. There is no explicit `retryable` field in error responses — agents must infer retryability from HTTP status codes.
- **Compensating Controls**:
  - Document which HTTP status codes are retriable (429, 503) in agent tool definitions
  - Build agent-side logic to interpret DruidException error codes
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a `retryable` boolean field to the standard error response envelope. Standardize all endpoint error responses through the DruidException framework.
- **Evidence**: `processing/src/main/java/org/apache/druid/error/DruidException.java`, `server/src/main/java/org/apache/druid/server/` (exception mapper files)

#### DATA-Q3: Selective Query Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Druid's native query API supports LIMIT/OFFSET, filters, and time-based constraints. SQL queries support standard LIMIT/OFFSET. However, the management REST APIs (datasources, tasks, segments) have inconsistent pagination support — many list endpoints return unbounded result sets. The `/druid/coordinator/v1/datasources` endpoint returns all datasources without pagination.
- **Gap**: Management APIs lack consistent pagination, filtering, and result-size limits. Query APIs are well-bounded by LIMIT but management APIs could return arbitrarily large lists for clusters with many datasources, segments, or tasks.
- **Compensating Controls**:
  - Agent tool definitions can enforce client-side pagination or result-size limits
  - Use SQL LIMIT clauses for data queries; restrict management API calls to specific resources
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add pagination parameters (limit, offset/cursor) to management REST API endpoints that return collections (datasources, segments, tasks, supervisors).
- **Evidence**: `server/src/main/java/org/apache/druid/server/http/DataSourcesResource.java`, `processing/src/main/java/org/apache/druid/query/spec/`

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Druid uses path-based API versioning (`/druid/{service}/v1/...`, `/druid/v2/` for native queries). Database schema migrations exist as SQL upgrade scripts. However, there is no breaking change detection in CI, no consumer-driven contract testing (Pact), no OpenAPI diff tooling, and no formal deprecation mechanism for API changes.
- **Gap**: No automated breaking change detection. API changes are reviewed via PR process but have no automated validation that agent-facing contracts remain stable. No changelog or deprecation notices for API changes.
- **Compensating Controls**:
  - Pin agent tool definitions to specific Druid versions
  - Monitor Druid release notes for breaking API changes manually
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Integrate OpenAPI diff tooling (once specs are generated per API-Q2) into CI to detect breaking changes. Establish a deprecation policy for API endpoints.
- **Evidence**: `server/src/main/java/org/apache/druid/server/http/DataSourcesResource.java` (path `/druid/coordinator/v1/datasources`), `.github/workflows/static-checks.yml`

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Druid has a contrib OpenTelemetry emitter extension that converts `query/time` metrics to OTel spans with W3C trace context propagation. However, this is not deeply integrated — it covers only query metrics, not full request tracing across services. Logging uses Log4j2 with text-based formats by default. Queries have `queryId` fields for correlation but there is no request-level correlation ID propagated across HTTP requests to all services.
- **Gap**: No native distributed tracing across Druid service nodes (Broker → Historical → Deep Storage). OpenTelemetry integration is shallow (metrics only, contrib extension). No structured JSON logging by default. Query IDs exist but are not propagated as trace context to downstream services.
- **Compensating Controls**:
  - Deploy the OpenTelemetry contrib extension and configure Log4j2 JSON layout
  - Use query IDs for manual request correlation in log aggregation
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Promote OpenTelemetry from contrib to core. Implement full request tracing (not just query metrics) with trace ID propagation in inter-service HTTP calls. Configure structured JSON logging by default.
- **Evidence**: `extensions-contrib/opentelemetry-emitter/`, `server/src/main/java/org/apache/druid/server/QueryScheduler.java`, `processing/src/main/java/org/apache/druid/query/QueryResourceId.java`

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Druid emits metrics via its ServiceEmitter framework (supports Graphite, StatsD, Kafka, Prometheus, CloudWatch via extensions). The metrics include query time, error counts, and latency. However, alerting configuration is not defined within the repository — no CloudWatch alarms, no PagerDuty/OpsGenie integration, no SLO definitions.
- **Gap**: No alerting thresholds defined in the codebase. Metric emission exists but alert configuration is left to operators. No pre-built alerting templates for agent-relevant error rates.
- **Compensating Controls**:
  - Configure alerting in the deployment platform (CloudWatch, Prometheus Alertmanager) using Druid's emitted metrics
  - Define SLO-based alerts externally
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Provide reference alerting configurations (CloudWatch alarm templates or Prometheus recording rules) for key agent-facing metrics: query error rate, query latency P99, API 5xx rate.
- **Evidence**: `extensions-contrib/opentelemetry-emitter/`, root `pom.xml` (emitter dependencies)

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The repository contains no Infrastructure-as-Code (IaC) for deploying Druid or its supporting infrastructure. No Terraform, CloudFormation, CDK, Helm charts, or Kustomize manifests exist. The only deployment artifact is a Docker Compose file for local development and a Dockerfile for building the container image.
- **Gap**: No IaC defining the agent-facing integration surface (API gateways, IAM roles, network policies). Deployment is left entirely to operators. No drift detection, no peer-reviewed IaC changes.
- **Compensating Controls**:
  - Operators deploy Druid using their own IaC (many community Helm charts and Terraform modules exist externally)
  - The Docker image provides a reproducible runtime base
- **Remediation Timeline**: 90+ days
- **Recommendation**: Provide reference IaC (Helm chart or Terraform module) for deploying Druid with security best practices — including API Gateway, IAM roles, and network policies for agent access.
- **Evidence**: `distribution/docker/Dockerfile`, `distribution/docker/docker-compose.yml`

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Druid has comprehensive CI/CD with 13 GitHub Actions workflows covering unit tests, integration tests, static analysis, CodeQL security scanning, and Docker builds. However, there is no API contract testing — no Pact, no OpenAPI validation, no schema comparison tooling in CI.
- **Gap**: No automated detection of API-breaking changes in the CI pipeline. API changes are reviewed through human PR review only.
- **Compensating Controls**:
  - Rely on the extensive integration test suite to catch behavioral regressions
  - Monitor release notes for API changes
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Once OpenAPI specs are generated (API-Q2), integrate an OpenAPI diff tool into CI to flag breaking changes on PRs that modify Resource classes.
- **Evidence**: `.github/workflows/ci.yml`, `.github/workflows/static-checks.yml`, `.github/workflows/unit-and-integration-tests-unified.yml`

---

## INFOs — Architecture and Design Inputs

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Druid has internal idempotency at the operation level (segment allocation, task execution) but no HTTP-level idempotency keys for write endpoints. POST endpoints for task submission, datasource operations, and configuration changes do not accept idempotency keys.
- **Implication**: If agent scope expands to write-enabled, this becomes a BLOCKER. Plan for idempotency key support on write endpoints.
- **Recommendation**: When expanding to write-enabled scope, add idempotency key headers to task submission and configuration change endpoints.
- **Evidence**: `server/src/main/java/org/apache/druid/server/http/DataSourcesResource.java`

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: All Druid API responses use structured JSON. Native queries accept and return JSON. SQL queries accept JSON and return JSON arrays. Management APIs return JSON objects. Content-Type is consistently `application/json`.
- **Implication**: JSON responses are directly consumable by LLM-based agents without format conversion.
- **Recommendation**: No action needed. This is a strength.
- **Evidence**: `server/src/main/java/org/apache/druid/server/http/DataSourcesResource.java`

### API-Q7: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: Druid does not natively emit events or webhooks for state changes. It has an internal event emission system (ServiceEmitter) for metrics and alerts, but no external event notification for business state changes (datasource created, ingestion completed, segment loaded).
- **Implication**: Agents cannot subscribe to state change notifications. They must poll for status updates.
- **Recommendation**: Consider adding webhook or EventBridge integration for key state transitions (task completion, datasource availability changes).
- **Evidence**: `server/src/main/java/org/apache/druid/server/metrics/`

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: Druid does not return rate limit headers (X-RateLimit-Remaining, Retry-After) in API responses. No rate limit documentation exists in the API surface because no rate limiting is implemented.
- **Implication**: Agents have no signal for self-throttling. They will discover limits only through 503 errors when the server is overloaded.
- **Recommendation**: When rate limiting is added (STATE-Q5), include standard rate limit headers in responses.
- **Evidence**: `server/src/main/java/org/apache/druid/server/http/`

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: INFO
- **Archetype calibration**: data-gateway — downgraded to INFO
- **Finding**: Druid propagates authentication results internally via `AuthenticationResult` objects through the request lifecycle. The Escalator pattern allows internal service-to-service calls with elevated privileges. However, there is no OAuth2 token exchange or on-behalf-of flow — all requests are authenticated independently at the service boundary.
- **Implication**: In a data-gateway context with read-heavy analytics queries, identity propagation is less critical since the primary concern is data access authorization, not delegation. If multi-tenant agent scenarios arise, identity propagation will need enhancement.
- **Recommendation**: No immediate action for data-gateway use case. Revisit if agents need to operate on behalf of specific tenants.
- **Evidence**: `server/src/main/java/org/apache/druid/server/security/AuthenticationResult.java`, `server/src/main/java/org/apache/druid/server/security/Escalator.java`

### AUTH-Q5: Credential Management

- **Severity**: INFO
- **Finding**: Druid supports credential management via `PasswordProvider` (deprecated) and `DynamicConfigProvider` interfaces. Default implementations use plaintext configuration or environment variables. AWS RDS Token provider exists. There is no native integration with AWS Secrets Manager, HashiCorp Vault, or KMS for credential rotation. The docker-compose file contains a hardcoded development password ("FoolishPassword") but this is clearly a local development artifact.
- **Implication**: Credentials for Druid metadata stores and deep storage are managed through environment variables or configuration files. Rotation requires service restart. This is adequate for development but needs enhancement for production agent deployment.
- **Recommendation**: Implement a DynamicConfigProvider extension for AWS Secrets Manager or Vault integration with automatic rotation support.
- **Evidence**: `distribution/docker/docker-compose.yml`, `server/src/main/java/org/apache/druid/metadata/`

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY; however, archetype calibration applies.
- **Scope-Calibrated**: agent_scope is "read-only" AND data-gateway archetype — evaluated as INFO
- **Finding**: Druid has no explicit compensation or rollback mechanisms for multi-step operations. Ingestion tasks are atomic (succeed or fail entirely), but multi-step workflows (e.g., configure compaction → submit task → verify) have no built-in rollback.
- **Implication**: For read-only agent scope with a data-gateway pattern, compensation is not immediately needed — queries are stateless. If scope expands to write-enabled operations (task submission, configuration changes), this becomes critical.
- **Recommendation**: No action for read-only scope. Plan compensation logic if expanding to write-enabled.
- **Evidence**: `indexing-service/src/main/java/org/apache/druid/indexing/`

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Druid uses optimistic concurrency for metadata operations (version checks on segments, conditional writes). The coordinator uses versioned segment metadata. However, the REST API does not expose ETag or If-Match headers for write operations.
- **Implication**: For read-only agents, concurrency controls are not immediately relevant. If scope expands, ETags on configuration endpoints would prevent concurrent write conflicts.
- **Recommendation**: No action for read-only scope.
- **Evidence**: `server/src/main/java/org/apache/druid/server/http/`

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Druid has no configurable transaction limits per identity. Query resource limits exist (maxSubqueryRows, maxScatterGatherBytes, query timeout) but these are system-wide, not per-agent.
- **Implication**: Read-only agents are bounded by query timeouts and resource limits. For future write-enabled scope, per-agent blast radius controls would be needed.
- **Recommendation**: No action for read-only scope.
- **Evidence**: `server/src/main/java/org/apache/druid/server/QueryScheduler.java`

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Druid has pending segment allocation for ingestion tasks, but no user-facing draft/pending state for API operations. Configuration changes and task submissions are immediately effective.
- **Implication**: Read-only agents do not modify state, so draft/pending is not relevant. If expanding to write scope, consider adding approval gates for configuration changes.
- **Recommendation**: No action for read-only scope.
- **Evidence**: `server/src/main/java/org/apache/druid/metadata/PendingSegmentRecord.java`

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No approval gate mechanism exists in Druid. All operations are executed immediately upon request.
- **Implication**: Not relevant for read-only agents. Would become important if agents perform configuration changes or task management.
- **Recommendation**: No action for read-only scope.
- **Evidence**: No evidence found — absence is itself a finding.

### DATA-Q5: Temporal Metadata and Freshness

- **Severity**: INFO
- **Archetype calibration**: data-gateway — downgraded to INFO
- **Finding**: Druid is inherently time-series oriented. All data has `__time` column as a first-class dimension. Segments have interval metadata (start/end time). Queries can filter by time range. However, API responses do not include freshness headers (Cache-Control, X-Data-Age) or consistency level signals.
- **Implication**: Druid's time-series nature means temporal metadata is rich within data. However, agents querying the API cannot easily determine whether results reflect real-time ingestion or stale segment data without checking ingestion lag.
- **Recommendation**: Consider adding response headers indicating data freshness (e.g., latest ingestion timestamp for queried datasource).
- **Evidence**: `processing/src/main/java/org/apache/druid/query/`

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No formal data quality scoring or completeness metrics exist within the Druid codebase. Druid trusts incoming data as-is. There is no null-rate monitoring, duplicate detection, or data profiling built into the system.
- **Implication**: Agents querying Druid have no signal about data quality or completeness of the underlying datasets.
- **Recommendation**: Consider exposing metadata about ingestion completeness and segment coverage via an API.
- **Evidence**: No evidence found — absence is itself a finding.

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: PASS (no finding)
- **Finding**: Druid exposes a fully documented REST API via JAX-RS annotations. The API surface includes management endpoints (`/druid/coordinator/v1/`, `/druid/overlord/v1/`), query endpoints (`/druid/v2/`, `/druid/v2/sql/`), and router endpoints (`/druid/router/v1/`). Documentation exists at docs.apache.org/druid. Integration does NOT require direct database access or UI automation.
- **Gap**: None — API interface exists and is documented.
- **Recommendation**: No action needed.
- **Evidence**: `server/src/main/java/org/apache/druid/server/http/DataSourcesResource.java`, `server/src/main/java/org/apache/druid/server/http/CoordinatorResource.java`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, Swagger, or machine-readable API specification exists. APIs are defined through JAX-RS annotations only. A gRPC .proto exists for the query surface in a contrib extension.
- **Gap**: No machine-readable spec for the full REST API. Agent tool generation requires manual work.
- **Recommendation**: Integrate swagger-jaxrs2 to auto-generate OpenAPI specs from existing annotations.
- **Evidence**: `server/src/main/java/org/apache/druid/server/http/DataSourcesResource.java`, `extensions-contrib/grpc-query/src/main/proto/query.proto`

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: DruidException provides structured errors with error codes and HTTP status categories. However, not all endpoints use it consistently, and no `retryable` field exists.
- **Gap**: Inconsistent error format across endpoints. No explicit retryability signal.
- **Recommendation**: Standardize all error responses through DruidException. Add `retryable` boolean.
- **Evidence**: `processing/src/main/java/org/apache/druid/error/DruidException.java`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No HTTP-level idempotency keys. Internal operations have idempotency (segment allocation) but write endpoints do not support idempotency headers.
- **Gap**: No idempotency key support on write endpoints.
- **Recommendation**: Plan idempotency if expanding to write-enabled scope.
- **Evidence**: `server/src/main/java/org/apache/druid/server/http/DataSourcesResource.java`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: All responses are structured JSON. Content-Type is consistently application/json.
- **Gap**: None.
- **Recommendation**: No action needed.
- **Evidence**: `server/src/main/java/org/apache/druid/server/http/DataSourcesResource.java`

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `data-gateway`, agent_scope: `read-only`.
- **Trigger**: Service has operations >30s OR long-running workflows
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: No external event emission or webhooks for state changes. Internal metrics only.
- **Gap**: No event-driven notification for agents.
- **Recommendation**: Consider webhook/EventBridge integration for key state transitions.
- **Evidence**: `server/src/main/java/org/apache/druid/server/metrics/`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit headers or documentation. No rate limiting implemented.
- **Gap**: No self-throttling signal for agents.
- **Recommendation**: Add rate limit headers when rate limiting is implemented.
- **Evidence**: `server/src/main/java/org/apache/druid/server/http/`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: No native OAuth2 client credentials, API key with principal attribution, or mTLS for machine identity. Existing auth targets human users or inter-node communication.
- **Gap**: No machine identity mechanism for agent principals.
- **Recommendation**: Implement OAuth2 client_credentials support or deploy an API Gateway for machine identity.
- **Evidence**: `server/src/main/java/org/apache/druid/server/security/Authenticator.java`, `extensions-core/druid-basic-security/`, `extensions-core/druid-pac4j/`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: Authorization model supports resource-type + regex scoping with READ/WRITE actions. Coarse granularity — no endpoint-level scoping.
- **Gap**: No fine-grained endpoint-level permission scoping for agent identities.
- **Recommendation**: Create dedicated roles with narrow resource-regex patterns for agent identities.
- **Evidence**: `server/src/main/java/org/apache/druid/server/security/Authorizer.java`, `server/src/main/java/org/apache/druid/server/security/ResourceType.java`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: PASS (no finding)
- **Finding**: Druid's authorization explicitly supports action-level checks. The `Authorizer.authorize()` method takes `(AuthenticationResult, Resource, Action)` where Action can be READ or WRITE. Resource filters on endpoints enforce specific action requirements. An agent granted READ cannot perform WRITE operations on the same resource.
- **Gap**: None — action-level authorization is supported.
- **Recommendation**: No action needed.
- **Evidence**: `server/src/main/java/org/apache/druid/server/security/Authorizer.java`, `server/src/main/java/org/apache/druid/server/http/security/DatasourceResourceFilter.java`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: Internal identity propagation via AuthenticationResult. No OAuth2 token exchange or on-behalf-of flows. Archetype calibration (data-gateway) applies — downgraded to INFO.
- **Gap**: No identity delegation for multi-tenant agent scenarios.
- **Recommendation**: Revisit if multi-tenant agent scenarios arise.
- **Evidence**: `server/src/main/java/org/apache/druid/server/security/AuthenticationResult.java`

#### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: Extensible via DynamicConfigProvider. Default is environment variables or plaintext config. No native Vault/Secrets Manager integration. AWS RDS Token provider exists for RDS connections.
- **Gap**: No integrated secrets management with rotation.
- **Recommendation**: Implement DynamicConfigProvider for AWS Secrets Manager.
- **Evidence**: `distribution/docker/docker-compose.yml`, `server/src/main/java/org/apache/druid/metadata/`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Audit logs exist (AuditManager) but are not immutable. `removeAuditLogsOlderThan()` allows deletion. No hash chaining or tamper evidence.
- **Gap**: Audit logs are not tamper-evident. Database admins can modify them.
- **Recommendation**: Stream audit events to immutable external store (S3 with Object Lock).
- **Evidence**: `processing/src/main/java/org/apache/druid/audit/AuditManager.java`, `server/src/main/java/org/apache/druid/server/audit/SQLAuditManager.java`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: User disablement available via coordinator API but depends on auth cache refresh interval. Not immediate propagation.
- **Gap**: No instant agent identity lockout across all nodes.
- **Recommendation**: Deploy API Gateway with instant API key revocation.
- **Evidence**: `extensions-core/druid-basic-security/`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO (data-gateway archetype calibration)
- **Finding**: No explicit compensation or rollback for multi-step operations. Ingestion tasks are atomic individually.
- **Gap**: No multi-step rollback.
- **Recommendation**: No action for read-only scope.
- **Evidence**: `indexing-service/src/main/java/org/apache/druid/indexing/`

#### STATE-Q2: Queryable Current State
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `data-gateway`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Internal optimistic concurrency exists. No ETags on REST API.
- **Gap**: No API-level concurrency controls exposed.
- **Recommendation**: No action for read-only scope.
- **Evidence**: `server/src/main/java/org/apache/druid/server/http/`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `data-gateway`, agent_scope: `read-only`.
- **Trigger**: Service has external dependencies (calls other services or external APIs)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No HTTP-level rate limiting. Only internal query scheduling with resilience4j bulkheads.
- **Gap**: Unlimited API requests possible from any client.
- **Recommendation**: Deploy API Gateway with throttling policies.
- **Evidence**: `server/src/main/java/org/apache/druid/server/QueryScheduler.java`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: System-wide query limits exist but no per-agent transaction limits.
- **Gap**: No per-identity blast radius controls.
- **Recommendation**: No action for read-only scope.
- **Evidence**: `server/src/main/java/org/apache/druid/server/QueryScheduler.java`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `data-gateway`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No user-facing draft/pending state. Operations execute immediately.
- **Gap**: No draft state for agent-proposed changes.
- **Recommendation**: No action for read-only scope.
- **Evidence**: `server/src/main/java/org/apache/druid/metadata/PendingSegmentRecord.java`

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No approval gate mechanism exists.
- **Gap**: No human-in-the-loop gates.
- **Recommendation**: No action for read-only scope.
- **Evidence**: No evidence found — absence is itself a finding.

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: A Docker Compose file provides a local development environment with all Druid services. However, there is no dedicated staging environment configuration with production-equivalent data shape, no seed data scripts, and no synthetic data generators in the repository.
- **Gap**: Docker Compose is for development only, not a staging environment with realistic data volumes.
- **Recommendation**: Provide reference configurations for a staging environment with synthetic data generation scripts.
- **Evidence**: `distribution/docker/docker-compose.yml`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO
- **Finding**: Stage A evaluation: Druid is a data-gateway for analytics data. It stores whatever data users ingest — which MAY include PII depending on the use case. However, Druid itself does not define the data schema or own PII classification — it is a storage/query engine. The data sensitivity depends entirely on what users ingest. Druid does not have API response field-level filtering (it returns whatever columns are queried). However, for data-gateway archetype with read-only scope, the severity is calibrated to INFO because: (1) Druid's authorization scopes to datasource level (resource-regex), so agents can be restricted to non-sensitive datasources; (2) data classification is a deployment-time concern — Druid provides the mechanism (resource authorization) but the data owner decides what is sensitive.
- **Gap**: No field-level access control in query responses. All columns of a datasource are accessible if READ permission is granted.
- **Recommendation**: For deployments with sensitive data, restrict agent identities to non-sensitive datasources via resource authorization. Consider column-level security if sensitive and non-sensitive data coexist in the same datasource.
- **Evidence**: `server/src/main/java/org/apache/druid/server/security/Authorizer.java`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Druid stores data in configurable deep storage (S3, HDFS, Azure, GCS) and local segment cache. There is no built-in data residency enforcement — data location depends entirely on deployment configuration. If Druid holds regulated data (GDPR, HIPAA), an agent querying and transmitting results to an LLM in another region could violate residency requirements.
- **Gap**: No data residency enforcement or awareness at the application layer. No region-tagging of data. Druid is unaware of regulatory boundaries.
- **Recommendation**: Document data residency requirements per datasource. Enforce at the deployment layer (deploy Druid and LLM endpoints in the same region). Consider adding datasource-level metadata tags for regulatory classification.
- **Evidence**: `extensions-core/s3-extensions/`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK-QUALITY
- **Finding**: Query APIs support LIMIT/OFFSET and time-range filtering. Management APIs lack consistent pagination.
- **Gap**: Management API endpoints return unbounded collections.
- **Recommendation**: Add pagination to management endpoints.
- **Evidence**: `server/src/main/java/org/apache/druid/server/http/DataSourcesResource.java`

#### DATA-Q4: System of Record Designations
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `data-gateway`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: INFO
- **Finding**: Rich temporal metadata in data (time-series first-class). No freshness headers in API responses.
- **Gap**: No freshness signal in API responses.
- **Recommendation**: Add response headers for data freshness.
- **Evidence**: `processing/src/main/java/org/apache/druid/query/`

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: No PII scrubbing in logging. Query text and configuration payloads logged verbatim.
- **Gap**: No log-level PII redaction.
- **Recommendation**: Implement Log4j2 PII filtering.
- **Evidence**: `server/src/main/java/org/apache/druid/server/audit/SQLAuditManager.java`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics or scoring within Druid.
- **Gap**: No data quality signals for agents.
- **Recommendation**: Consider exposing ingestion completeness metadata.
- **Evidence**: No evidence found — absence is itself a finding.

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: Path-based versioning exists (/v1/, /v2/). No automated breaking change detection in CI. No contract testing.
- **Gap**: No automated API contract stability validation.
- **Recommendation**: Integrate OpenAPI diff tooling into CI.
- **Evidence**: `server/src/main/java/org/apache/druid/server/http/DataSourcesResource.java`, `.github/workflows/static-checks.yml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Druid uses semantically meaningful field names throughout its API (e.g., `dataSource`, `intervals`, `dimensions`, `aggregations`, `granularity`, `queryType`). Query response field names match the schema defined by the user at ingestion time. No legacy codes requiring translation.
- **Implication**: Agent tool definitions can use Druid field names directly without a data dictionary.
- **Recommendation**: No action needed. This is a strength.
- **Evidence**: `processing/src/main/java/org/apache/druid/query/`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: Druid provides system tables (`INFORMATION_SCHEMA`) queryable via SQL that describe available datasources, columns, and their types. The `/druid/coordinator/v1/metadata/datasources` endpoint provides schema metadata. No external data catalog integration (Glue, Collibra).
- **Implication**: Agents can discover available data through SQL system tables and metadata APIs, which is adequate for tool binding.
- **Recommendation**: Consider registering Druid datasources in a centralized data catalog for cross-system discoverability.
- **Evidence**: `sql/src/main/java/org/apache/druid/sql/calcite/`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: Contrib OpenTelemetry emitter (shallow — metrics only). No native distributed tracing. Text-based logging default. Query IDs exist but no request-level correlation across services.
- **Gap**: No full distributed tracing. No structured JSON logging by default. No request-level trace propagation.
- **Recommendation**: Promote OpenTelemetry to core. Implement structured JSON logging.
- **Evidence**: `extensions-contrib/opentelemetry-emitter/`, `processing/src/main/java/org/apache/druid/query/QueryResourceId.java`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: Metric emission framework exists. No alerting configuration in the repository.
- **Gap**: No pre-defined alerting thresholds.
- **Recommendation**: Provide reference alerting configurations.
- **Evidence**: `extensions-contrib/opentelemetry-emitter/`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: Druid emits query metrics (query/time, query/bytes, query/node/time) via ServiceEmitter. These are operational metrics, not business outcome metrics. Business metrics would depend on the use case (e.g., query success rate for agent-submitted queries).
- **Implication**: Agent effectiveness monitoring would need custom metrics on top of existing infrastructure.
- **Recommendation**: Define agent-specific business metrics (agent query success rate, result quality).
- **Evidence**: `processing/src/main/java/org/apache/druid/query/DefaultQueryMetrics.java`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK-QUALITY
- **Finding**: No IaC in the repository. Docker Compose for local dev only. No Terraform, CloudFormation, Helm, or CDK.
- **Gap**: No IaC for production deployment. No drift detection.
- **Recommendation**: Provide reference IaC for production deployment with security best practices.
- **Evidence**: `distribution/docker/Dockerfile`, `distribution/docker/docker-compose.yml`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive CI/CD (13 workflows). No API contract testing (no Pact, no OpenAPI validation).
- **Gap**: No automated API-breaking change detection.
- **Recommendation**: Integrate OpenAPI diff tool into CI after generating specs.
- **Evidence**: `.github/workflows/ci.yml`, `.github/workflows/static-checks.yml`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: No rollback configuration in the repository. No blue-green, canary, or deployment strategy defined. Rollback is entirely an operator responsibility.
- **Gap**: No rollback mechanism defined in the codebase.
- **Recommendation**: Provide reference deployment configurations with rollback capabilities.
- **Evidence**: `.github/workflows/`

#### ENG-Q4: API Test Coverage
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `data-gateway`, agent_scope: `read-only`.
- **Trigger**: Always evaluated (but INFO for stateless-utility)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `data-gateway`, agent_scope: `read-only`.
- **Trigger**: Service has persistent data stores
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `server/src/main/java/org/apache/druid/server/security/Authenticator.java` | AUTH-Q1 |
| `server/src/main/java/org/apache/druid/server/security/Authorizer.java` | AUTH-Q2, AUTH-Q3, DATA-Q1 |
| `server/src/main/java/org/apache/druid/server/security/AuthenticationResult.java` | AUTH-Q4 |
| `server/src/main/java/org/apache/druid/server/security/Escalator.java` | AUTH-Q4 |
| `server/src/main/java/org/apache/druid/server/security/ResourceType.java` | AUTH-Q2 |
| `server/src/main/java/org/apache/druid/server/security/Resource.java` | AUTH-Q2 |
| `server/src/main/java/org/apache/druid/server/http/DataSourcesResource.java` | API-Q1, API-Q2, API-Q3, API-Q4, API-Q5, DATA-Q3, DISC-Q1 |
| `server/src/main/java/org/apache/druid/server/http/CoordinatorResource.java` | API-Q1 |
| `server/src/main/java/org/apache/druid/server/http/security/DatasourceResourceFilter.java` | AUTH-Q3 |
| `server/src/main/java/org/apache/druid/server/QueryScheduler.java` | STATE-Q5, STATE-Q6, OBS-Q1 |
| `server/src/main/java/org/apache/druid/server/scheduling/ManualQueryLaningStrategy.java` | STATE-Q5 |
| `server/src/main/java/org/apache/druid/server/audit/SQLAuditManager.java` | AUTH-Q6, DATA-Q6 |
| `server/src/main/java/org/apache/druid/metadata/PendingSegmentRecord.java` | HITL-Q1 |
| `processing/src/main/java/org/apache/druid/audit/AuditManager.java` | AUTH-Q6 |
| `processing/src/main/java/org/apache/druid/error/DruidException.java` | API-Q3 |
| `processing/src/main/java/org/apache/druid/query/QueryResourceId.java` | OBS-Q1 |
| `processing/src/main/java/org/apache/druid/query/DefaultQueryMetrics.java` | OBS-Q3 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `extensions-contrib/grpc-query/src/main/proto/query.proto` | API-Q2 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/ci.yml` | ENG-Q2 |
| `.github/workflows/static-checks.yml` | ENG-Q2, DISC-Q1 |
| `.github/workflows/unit-and-integration-tests-unified.yml` | ENG-Q2 |
| `.github/workflows/codeql.yml` | ENG-Q2 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `distribution/docker/Dockerfile` | ENG-Q1 |
| `distribution/docker/docker-compose.yml` | ENG-Q1, AUTH-Q5, HITL-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `pom.xml` (root) | STATE-Q5 |
| `server/pom.xml` | STATE-Q5 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `extensions-core/s3-extensions/src/test/resources/log4j2.xml` | DATA-Q6 |
