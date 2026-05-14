# Agentic Readiness Analysis Report

**Target**: openzipkin/zipkin (monorepo)
**Date**: 2026-04-29
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**Repository Type**: monorepo
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: java, observability, tracing
**Context**: Distributed tracing system.

**Archetype Justification**: Zipkin server ingests trace spans via HTTP, gRPC, and message queue collectors (write path), stores them in configurable persistent backends (Cassandra, Elasticsearch, MySQL, in-memory), and exposes a comprehensive query API for traces, services, and dependencies (read path). It has both significant write and read paths with persistent state, classifying it as stateful-crud.

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 2 | **RISK-SAFETY**: 9 | **RISK-QUALITY**: 15 | **INFOs**: 15

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days.

Two BLOCKERs were identified:
1. **AUTH-Q1**: No machine identity authentication — the Zipkin server accepts all requests without authentication.
2. **DATA-Q1**: No sensitive data classification — trace data may contain sensitive information (HTTP URLs, user IDs, query parameters) with no field-level classification or access controls.

These must be resolved before any agent (including read-only agents) can safely integrate with this system.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 2 |
| RISK-SAFETY | 9 |
| RISK-QUALITY | 15 |
| INFO | 15 |
| N/A | 0 |
| Not Evaluated (extended) | 2 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 17
**Extended Questions Not Triggered**: 2
**Questions N/A (repo_type: monorepo)**: 0
**Service Archetype**: stateful-crud (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: Zipkin server has NO authentication mechanism built in. No OAuth2 client credentials flow, no API key validation, no mTLS configuration, no service account definitions, no Cognito integration, no API Gateway authorizers. The server accepts all incoming HTTP, gRPC, and collector requests without any identity verification. TLS/SSL is supported via `armeria.ssl.*` but this provides transport encryption, not caller authentication. The CORS configuration in `ZipkinHttpConfiguration.java` allows all origins (`*`) by default.
- **Gap**: No machine identity authentication of any kind. An agent calling Zipkin cannot be attributed as a distinct principal. All callers are anonymous.
- **Remediation**:
  - **Immediate**: Deploy an API Gateway or reverse proxy (e.g., AWS API Gateway, Envoy, or Nginx) in front of Zipkin that enforces API key or OAuth2 client credentials authentication. Map each agent to a distinct API key for attribution.
  - **Target State**: Every API request to Zipkin is authenticated with a principal identity (API key, OAuth2 client credential, or mTLS certificate) that is logged in an immutable audit trail.
  - **Estimated Effort**: Medium (30–60 days including proxy setup, key provisioning, and testing)
  - **Dependencies**: Resolving AUTH-Q6 (audit logging) depends on this — you cannot log authenticated principals if there are none.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpConfiguration.java`, `zipkin-server/src/main/resources/zipkin-server-shared.yml`, `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpCollector.java`

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: Trace data stored and served by Zipkin may contain sensitive information embedded in span tags (e.g., `http.url` with query parameters, user IDs, database query strings, IP addresses). The Span model (`zipkin2/Span.java`) accepts arbitrary key-value tags with no classification. The `AUTOCOMPLETE_KEYS` configuration whitelists certain tag keys for UI autocomplete but does not function as a data classification mechanism. No field-level encryption exists. No data classification tags on storage resources. No PII detection tools (e.g., AWS Macie) integrated. No data classification policies documented in the repository.
- **Gap**: Sensitive data in trace spans is not classified, tagged, or access-controlled at the field level. An agent with read access to the query API could retrieve spans containing PII or sensitive business data without restriction.
- **Remediation**:
  - **Immediate**: Audit span tags across production traces to identify fields containing PII (e.g., `http.url`, `db.statement`, `user.id`). Implement tag-level redaction or filtering in Zipkin's storage layer or via an ingestion pipeline before data reaches storage.
  - **Target State**: Sensitive fields in trace data are classified and tagged. Access controls prevent agents from retrieving classified fields without explicit authorization. A data classification policy is documented and enforced.
  - **Estimated Effort**: High (60–120 days including data audit, classification schema, and enforcement implementation)
  - **Dependencies**: This should be resolved alongside DATA-Q6 (PII in logs) as both address data sensitivity.
- **Evidence**: `zipkin/src/main/java/zipkin2/Span.java`, `zipkin-server/src/main/resources/zipkin-server-shared.yml`, `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java`

---

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No authorization model exists in the Zipkin codebase. Since there is no authentication (AUTH-Q1), there are no IAM policies, no role-per-service configuration, and no API Gateway resource policies. All endpoints are accessible to all callers with identical (full) privileges. There is no mechanism to grant an agent read-only access to specific resources.
- **Gap**: No scoped permissions. An agent cannot be restricted to specific operations or resource types.
- **Compensating Controls**:
  - Deploy an API Gateway in front of Zipkin with route-level policies that restrict agent identities to GET-only methods on specific paths (e.g., `/api/v2/trace/*`, `/api/v2/services`).
  - Use network segmentation to limit which services/agents can reach Zipkin's collector vs. query endpoints.
- **Remediation Timeline**: 30–60 days (concurrent with AUTH-Q1 remediation)
- **Recommendation**: Implement API Gateway with method-level authorization when resolving AUTH-Q1. Define separate API keys for read-only agents vs. instrumentation clients.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpConfiguration.java`, `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java`

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization (ABAC or fine-grained RBAC) exists. No permission matrices, no middleware checks (`canRead`, `canWrite`, `canDelete`), no API Gateway method-level authorization. All API endpoints — including write endpoints (`POST /api/v1/spans`, `POST /api/v2/spans`) and query endpoints (`GET /api/v2/traces`) — are equally accessible.
- **Gap**: Cannot enforce action-level authorization. An agent cannot be restricted to read but not write, even within the same resource type.
- **Compensating Controls**:
  - API Gateway method-level restrictions: allow agent API keys only on GET methods, block POST/PUT/DELETE.
  - Network-level separation: route read-only agent traffic through a proxy that only forwards to the query API, not collector endpoints.
- **Remediation Timeline**: 30–60 days (concurrent with AUTH-Q1/Q2 remediation)
- **Recommendation**: When implementing the API Gateway for AUTH-Q1, configure method-level restrictions per API key. Ensure read-only agent keys cannot call POST endpoints.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpConfiguration.java`, `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpCollector.java`

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No immutable audit logging exists. Application logs use console output via SLF4J/Log4j2 with the pattern `%clr{%5p} %clr{[%X{traceId}/%X{spanId}]}{yellow}`. These logs are not structured, not immutable, and not tamper-evident. No CloudTrail configuration, no S3 bucket with object lock, no CloudWatch log retention policies. Since there is no authentication, logs do not record which principal performed an action.
- **Gap**: No audit trail for API requests. Cannot determine what actions an agent performed or when.
- **Compensating Controls**:
  - Route traffic through an API Gateway with access logging enabled to an immutable log destination (S3 with Object Lock or CloudWatch Logs with retention policy).
  - Enable Zipkin's self-tracing (`SELF_TRACING_ENABLED=true`) to capture request-level traces, though these are not immutable.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Deploy API Gateway access logs to an immutable destination. Log the authenticated principal (once AUTH-Q1 is resolved), request path, method, timestamp, and response code.
- **Evidence**: `zipkin-server/src/main/resources/zipkin-server-shared.yml` (logging.pattern.level), no CloudTrail or immutable log configuration found

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Since there is no authentication mechanism (AUTH-Q1), there are no identities to suspend. No API key revocation endpoints, no IAM role deactivation, no service account disable mechanisms, no Cognito user pool user disable. If an agent behaves anomalously, the only recourse is network-level blocking (firewall rules).
- **Gap**: Cannot suspend an individual agent identity without affecting all traffic.
- **Compensating Controls**:
  - If an API Gateway is deployed (per AUTH-Q1 remediation), agent API keys can be revoked immediately.
  - Network-level IP blocking as a last resort.
- **Remediation Timeline**: 30–60 days (resolved as part of AUTH-Q1 remediation)
- **Recommendation**: When implementing API keys via API Gateway, ensure key revocation is operationally simple (single API call or console action).
- **Evidence**: No authentication-related code found in the repository

#### STATE-Q1: Compensation and Rollback ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No saga pattern, no two-phase commit, no explicit undo endpoints, and no compensating transaction logic exists. Span ingestion is append-only — once a span is written to storage (Cassandra, Elasticsearch, MySQL), there is no rollback mechanism. The `InMemoryStorage` evicts oldest traces when `MEM_MAX_SPANS` is exceeded, but this is not a rollback capability. Step Functions are not used.
- **Gap**: No compensation or rollback for multi-step operations. If a batch span ingestion partially fails, the system is left in a partial state.
- **Compensating Controls**:
  - For read-only agents, this is lower risk since agents will not initiate write operations.
  - If agents are later expanded to write scope, consider implementing idempotent span ingestion with deduplication at the storage layer.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Document the append-only nature of span ingestion. If write-enabled agents are planned, implement explicit deduplication and compensation patterns.
- **Evidence**: `zipkin/src/main/java/zipkin2/storage/InMemoryStorage.java`, `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpCollector.java`

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Limited resilience patterns exist. The `ThrottledStorageComponent` uses Netflix concurrency-limits (`Gradient2Limit`) to limit concurrent writes to storage, with configurable `STORAGE_THROTTLE_MIN_CONCURRENCY`, `STORAGE_THROTTLE_MAX_CONCURRENCY`, and `STORAGE_THROTTLE_MAX_QUEUE_SIZE`. Timeout configurations exist: `ES_TIMEOUT=10000ms`, `QUERY_TIMEOUT=11s`, `RABBIT_CONNECTION_TIMEOUT=60000`. However, no circuit breaker annotations (`@CircuitBreaker`), no Resilience4j integration, and no exponential backoff on downstream calls. The storage throttle is experimental and not recommended for production per the README.
- **Gap**: No circuit breaker pattern on calls to storage backends. A storage backend failure (Cassandra, Elasticsearch) could cascade to the agent through the query API with no circuit-breaking protection.
- **Compensating Controls**:
  - Enable `STORAGE_THROTTLE_ENABLED=true` with conservative concurrency limits to prevent storage overload.
  - Deploy a service mesh (e.g., Istio, App Mesh) with circuit breaker policies on traffic to Zipkin.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Evaluate adding Resilience4j circuit breakers on storage backend calls, particularly for the query path that agents will consume.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/throttle/ThrottledStorageComponent.java`, `zipkin-server/src/main/resources/zipkin-server-shared.yml`

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No API-side rate limiting exists. The `ThrottledStorageComponent` limits concurrent writes to storage (internal throttling) but does not limit incoming HTTP/gRPC request rates. No API Gateway throttling, no WAF rate rules, no application-level rate limiting middleware (e.g., `express-rate-limit` equivalent). The Armeria server has a request timeout of 11 seconds but no per-client rate limits. The CORS configuration permits all origins. A runaway agent loop could overwhelm the query API at machine speed.
- **Gap**: No rate limiting on the API surface. Agent traffic is unlimited.
- **Compensating Controls**:
  - Deploy an API Gateway or WAF with rate limiting per API key/client IP.
  - Configure the Armeria server's request timeout as a soft protection (`QUERY_TIMEOUT=11s`).
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Deploy an API Gateway with usage plans and per-key throttle settings. Configure separate rate limits for agent identities.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpConfiguration.java`, `zipkin-server/src/main/resources/zipkin-server-shared.yml`

#### DATA-Q2: Data Residency and Sovereignty ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No data residency requirements are documented in the codebase. Storage backends are configured entirely by the operator via environment variables (`CASSANDRA_CONTACT_POINTS`, `ES_HOSTS`, `MYSQL_HOST`). No cross-region replication settings managed by the application. No GDPR, LGPD, or other data sovereignty references in code. Data sovereignty is an operator responsibility, not enforced by the application.
- **Gap**: The application provides no data residency enforcement. If an agent transmits trace data (which may contain PII — see DATA-Q1) to an LLM provider in a different region, there are no application-level controls to prevent it.
- **Compensating Controls**:
  - Document the deployment region and ensure LLM endpoints used by agents are in the same region.
  - Apply network-level controls (VPC endpoints, PrivateLink) to ensure trace data does not leave the deployment region.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document data residency requirements for trace data. Ensure the agent architecture constrains LLM calls to the same region as Zipkin's storage.
- **Evidence**: `zipkin-server/src/main/resources/zipkin-server-shared.yml` (storage configuration section)

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No PII redaction exists in logging. No log scrubbing middleware, no PII masking libraries, no regex patterns for PII in logging utilities, no Amazon Macie integration. Application logs may include span data in debug mode (`--logging.level.zipkin2=DEBUG`). The logging pattern `%clr{%5p} %clr{[%X{traceId}/%X{spanId}]}{yellow}` includes trace context but no PII filtering. Error responses via `BodyIsExceptionMessage.java` return raw exception messages as `text/plain`, which could include sensitive data from span parsing.
- **Gap**: PII in trace data could leak into application logs, error responses, and observability data.
- **Compensating Controls**:
  - Run Zipkin at INFO log level (default) and avoid DEBUG in production.
  - Deploy a log aggregation pipeline with PII redaction (e.g., CloudWatch log filters, Datadog PII scanner).
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement log scrubbing for known PII patterns. Review error response handling in `BodyIsExceptionMessage.java` to ensure exception messages do not expose sensitive span data.
- **Evidence**: `zipkin-server/src/main/resources/zipkin-server-shared.yml` (logging section), `zipkin-server/src/main/java/zipkin2/server/internal/BodyIsExceptionMessage.java`

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, GraphQL schema, or equivalent machine-readable specification exists in the repository. The README references an external API specification at `https://zipkin.io/zipkin-api/zipkin-api.yaml`, but this file is not maintained within the repo. No auto-generated specs from code annotations. The API is documented in prose in `zipkin-server/README.md` and through endpoint annotations in `ZipkinQueryApiV2.java`.
- **Gap**: No in-repo machine-readable API spec. Agent tool generation requires manual authoring or reliance on an external, potentially out-of-sync spec.
- **Compensating Controls**:
  - Use the externally hosted `zipkin-api.yaml` for tool generation, with manual validation against the running server.
  - Generate an OpenAPI spec from the Armeria annotated service definitions.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add the OpenAPI spec to the repository and integrate spec validation into CI.
- **Evidence**: `zipkin-server/README.md`, `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java`

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Error responses are returned as `text/plain` with HTTP status codes (400, 404, 500) and raw exception messages. The `BodyIsExceptionMessage.java` handler returns `cause.getMessage()` as plain text for `IllegalArgumentException` (400) and other exceptions (500). No structured JSON error body with error code, error message, or retryable boolean. For example, a `GET /api/v2/trace/{traceId}` for a non-existent trace returns `404` with plain text `"{traceId} not found"`.
- **Gap**: Agents cannot programmatically distinguish retriable errors from terminal errors. No machine-parseable error classification.
- **Compensating Controls**:
  - Build error parsing logic in the agent tool layer to map known HTTP status codes to retry/terminal decisions.
  - Wrap Zipkin API calls with an MCP server that translates plain-text errors into structured responses.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement a structured error response format (JSON with `error_code`, `message`, `retryable` fields) in `BodyIsExceptionMessage.java`.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/BodyIsExceptionMessage.java`, `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java`

#### STATE-Q2: Queryable Current State — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Zipkin exposes comprehensive query endpoints for current state. `/api/v2/trace/{traceId}` retrieves individual traces. `/api/v2/traces` supports filtered queries with `serviceName`, `remoteServiceName`, `spanName`, `annotationQuery`, `minDuration`, `maxDuration`, `endTs`, `lookback`, and `limit` parameters. `/api/v2/services` and `/api/v2/spans` provide metadata. `/api/v2/traceMany` supports batch trace retrieval. The query surface is well-designed for agent consumption.
- **Gap**: Minimal — the query surface is comprehensive. However, there are no ETags or version fields on responses to enable conditional requests.
- **Compensating Controls**: Not needed — state is queryable.
- **Remediation Timeline**: N/A (substantially satisfied)
- **Recommendation**: Consider adding `ETag` or `Last-Modified` headers to trace query responses to enable conditional requests and reduce unnecessary data transfer.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java`

#### DATA-Q3: Selective Query Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The `/api/v2/traces` endpoint supports pagination via the `limit` parameter (default 10), filtering by `serviceName`, `remoteServiceName`, `spanName`, `annotationQuery`, `minDuration`, `maxDuration`, and time-windowing via `endTs` and `lookback`. The `QUERY_LOOKBACK` default of 24 hours limits the time window. However, `/api/v2/services` and `/api/v2/spans` return full lists without pagination. `/api/v2/autocompleteValues` also returns unbounded lists.
- **Gap**: Metadata endpoints (`/services`, `/spans`, `/autocompleteValues`) lack pagination. In environments with many services, these could return large result sets.
- **Compensating Controls**:
  - Set `QUERY_LOOKBACK` to a reasonable window to limit result sizes implicitly.
  - Cache service/span name lists in the agent tool layer.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add pagination support to `/api/v2/services` and `/api/v2/spans` endpoints. Consider a `limit` parameter for autocomplete endpoints.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java`

#### DATA-Q4: System of Record Designations — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Zipkin IS the system of record for distributed trace data. The storage backend (Cassandra, Elasticsearch, MySQL, or in-memory) is the authoritative store. The system architecture is clear: instrumented applications report spans to Zipkin, and Zipkin is the single source of truth for trace data. No master data management or conflict resolution is needed as Zipkin owns its data domain.
- **Gap**: Minimal — the system of record designation is clear by architecture. However, it is not formally documented.
- **Compensating Controls**: Not needed — the architecture self-documents this.
- **Remediation Timeline**: N/A (substantially satisfied)
- **Recommendation**: Document Zipkin as the system of record for trace data in the deployment documentation.
- **Evidence**: `zipkin/src/main/java/zipkin2/storage/StorageComponent.java`, `zipkin-server/README.md`

#### DATA-Q5: Temporal Metadata and Freshness — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Spans include `timestamp` (epoch microseconds) and `duration` (microseconds) fields with high precision. These serve as creation timestamps. The `Cache-Control: max-age={namesMaxAge}` header is set on service/span name responses (default 300s). However, trace query responses have no `Cache-Control`, no `X-Data-Age`, and no `consistency_level` field. Storage backends may have eventual consistency (Cassandra, Elasticsearch) but this is not signaled to API consumers. No timezone normalization is needed as timestamps are epoch-based.
- **Gap**: No freshness signaling on trace query responses. An agent cannot determine if data is cached, stale, or eventually consistent.
- **Compensating Controls**:
  - Document the eventual consistency characteristics of each storage backend.
  - Agents should account for ingestion delay (typically seconds) when reasoning about trace data.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `Cache-Control` or `X-Data-Freshness` headers to trace query responses. Document consistency guarantees per storage backend.
- **Evidence**: `zipkin/src/main/java/zipkin2/Span.java` (timestamp, duration fields), `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java` (maybeCacheNames)

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The API uses URL-based versioning (`/api/v1/`, `/api/v2/`). The Java codec layer supports multiple formats: `SpanBytesDecoder.JSON_V1`, `JSON_V2`, `THRIFT`, `PROTO3`. Proto definitions are managed externally via `zipkin-proto3` (version `1.0.0`). However, no breaking change detection tools exist in CI — no `buf breaking`, no OpenAPI diff, no Pact consumer-driven contract tests. No changelog for API changes. No schema registry.
- **Gap**: API versioning exists but no automated breaking change detection in CI. Agent tool bindings could break silently on API changes.
- **Compensating Controls**:
  - Pin agent tool definitions to a specific API version (`/api/v2/`).
  - Manually validate agent tool behavior after Zipkin upgrades.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenAPI spec validation to the CI pipeline to detect breaking changes. Consider adding consumer-driven contract tests (Pact).
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java`, `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpCollector.java`, `pom.xml` (zipkin-proto3.version)

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Zipkin IS a distributed tracing system and supports self-tracing (`SELF_TRACING_ENABLED`). Brave tracing integration is built-in. The logging pattern includes trace context: `%clr{%5p} %clr{[%X{traceId}/%X{spanId}]}{yellow}`. Correlation IDs are present. However, logs are not structured JSON by default — they use a pattern-based text format via SLF4J/Log4j2. Log output goes to console.
- **Gap**: Logs are not structured JSON. While trace context is present, text-format logs are harder to parse and correlate programmatically.
- **Compensating Controls**:
  - Deploy a log aggregation pipeline that parses the text log format.
  - Enable self-tracing for detailed request-level tracing.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure structured JSON logging output. This can be done via Log4j2 JSON layout configuration.
- **Evidence**: `zipkin-server/src/main/resources/zipkin-server-shared.yml` (logging.pattern.level), `zipkin-server/src/main/java/zipkin2/server/internal/brave/ZipkinSelfTracingConfiguration.java`

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive metrics are exposed via Prometheus endpoint (`/prometheus`) and Micrometer integration. The `http.server.requests` timer tracks response time histograms with `method`, `uri`, and `status` tags. JVM metrics (memory, GC, threads, classloader, processor) are published. Collector metrics track messages, bytes, spans, and drops per transport. However, no alerting thresholds are configured in the codebase — no CloudWatch alarms, no PagerDuty/OpsGenie integration, no anomaly detection. Alerting is entirely an operator responsibility via Prometheus/Grafana.
- **Gap**: Metrics are available but no alerting is configured. Target system degradation would not trigger automatic alerts.
- **Compensating Controls**:
  - Configure Prometheus alerting rules for Zipkin query latency and error rates.
  - Set up Grafana dashboards with alert thresholds for agent-consumed endpoints.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create Prometheus alerting rules for `http.server.requests` error rate and latency percentiles on `/api/v2/*` endpoints.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/prometheus/ZipkinPrometheusMetricsConfiguration.java`, `zipkin-server/src/main/java/zipkin2/server/internal/MicrometerCollectorMetrics.java`

#### ENG-Q1: Infrastructure Governance — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No IaC files exist in the repository. No Terraform, CloudFormation, CDK, Helm charts, or Kustomize configurations. The Dockerfile and docker-compose files define container packaging but not cloud infrastructure (API gateways, IAM, secrets, networking). No drift detection. Infrastructure provisioning is entirely the operator's responsibility. The Helm chart reference in README.md points to an external repo (`zipkin-helm`).
- **Gap**: The integration surface (API gateway, IAM roles, secrets, networking) is not defined as code within this repository. No peer review or drift detection for infrastructure changes.
- **Compensating Controls**:
  - Maintain IaC for Zipkin deployment infrastructure in a separate infrastructure repository.
  - Use the external `zipkin-helm` chart with version-pinned values.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Create IaC (Terraform or CDK) for the Zipkin deployment infrastructure, including API Gateway, IAM roles, and network configuration. Store in this repo or a linked infrastructure repo.
- **Evidence**: No IaC files found. `docker/Dockerfile`, `docker/examples/*.yml` (container-only definitions)

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive CI/CD exists via GitHub Actions: `test.yml` (unit tests on JDK 21 and 25), `test_docker` (integration tests per storage/collector module), `deploy.yml` (Maven deploy + Docker push), `security.yml` (Trivy vulnerability scanner), `lint.yml` (YAML/markdown linting), `create_release.yml` (Maven release). However, no API contract tests exist in CI — no Pact consumer-driven contract tests, no OpenAPI spec validation in build, no schema comparison tools, no breaking change detection.
- **Gap**: CI/CD is mature for functional testing but lacks API contract testing. Agent-breaking API changes would not be caught before production.
- **Compensating Controls**:
  - Manually validate agent tool behavior after each Zipkin release.
  - Pin agent tool integrations to specific Zipkin versions.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenAPI spec validation to the CI pipeline. Consider adding Pact consumer-driven contract tests for agent-facing endpoints.
- **Evidence**: `.github/workflows/test.yml`, `.github/workflows/deploy.yml`, `.github/workflows/security.yml`

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No automated rollback mechanism exists. No blue/green deployment, no CodeDeploy rollback triggers, no Helm rollback configuration, no feature flags, no canary deployment with automatic rollback. Docker images are versioned by tag. The Maven release plugin (`create_release.yml`) handles versioning. Rollback would require manually deploying a previous Docker image version (`docker run openzipkin/zipkin:<previous-version>`).
- **Gap**: No automated rollback capability. Recovery from a bad deployment depends on manual intervention.
- **Compensating Controls**:
  - Maintain a list of known-good Docker image versions.
  - Use container orchestration (ECS, Kubernetes) with rolling update and manual rollback commands.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement automated rollback capability in the deployment pipeline. If using Kubernetes/ECS, configure health check-based rollback triggers.
- **Evidence**: `.github/workflows/deploy.yml`, `.github/workflows/create_release.yml`, `docker/Dockerfile`

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive integration test suite exists: `ITZipkinServer.java`, `ITZipkinGrpcCollector.java`, `ITZipkinServerCORS.java`, `ITZipkinServerTimeout.java`, `ITZipkinServerAutocomplete.java`, `ITZipkinServerQueryDisabled.java`, `ITZipkinServerHttpCollectorDisabled.java`, `ITZipkinServerSsl.java`. Per-storage integration tests run in Docker (`test_docker` CI job). Tests validate input handling, output format, and error scenarios. However, no explicit API contract tests (Postman/Newman, Pact) — tests are integration-style, not contract-style.
- **Gap**: Tests are functional, not contract-oriented. Changes to response format or behavior may not be caught unless they break existing assertions.
- **Compensating Controls**:
  - Existing integration tests provide reasonable coverage of API behavior.
  - Manual validation of agent tool behavior after Zipkin upgrades.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add API contract tests that explicitly validate response schemas, error formats, and field names for agent-consumed endpoints.
- **Evidence**: `zipkin-server/src/test/java/zipkin2/server/internal/ITZipkinServer.java`, `.github/workflows/test.yml`

#### ENG-Q5: Encryption at Rest — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No encryption-at-rest configuration exists in the codebase. SSL/TLS transport encryption is supported for Cassandra (`CASSANDRA_USE_SSL`), Elasticsearch (`ES_SSL_NO_VERIFY`, JSSE keystore/truststore), and MySQL (`MYSQL_USE_SSL`). However, these are transport encryption (in-transit), not encryption at rest. No KMS key configuration, no `kms_key_id` settings. Encryption at rest depends entirely on the storage backend's operator configuration.
- **Gap**: No application-level enforcement of encryption at rest. Trace data (which may contain PII — see DATA-Q1) could be stored unencrypted.
- **Compensating Controls**:
  - Configure encryption at rest at the storage backend level (e.g., Elasticsearch encryption at rest, Cassandra transparent data encryption, RDS encryption).
  - Document encryption-at-rest requirements in deployment documentation.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document encryption-at-rest requirements and provide configuration guidance for each supported storage backend. Consider adding validation checks at startup.
- **Evidence**: `zipkin-server/src/main/resources/zipkin-server-shared.yml` (SSL sections for cassandra3, elasticsearch, mysql)

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Docker-compose examples exist for local testing with multiple storage backends: `docker-compose.yml` (in-memory), `docker-compose-elasticsearch.yml`, `docker-compose-cassandra.yml`, `docker-compose-mysql.yml`, `docker-compose-kafka.yml`, `docker-compose-rabbitmq.yml`, `docker-compose-activemq.yml`, `docker-compose-pulsar.yml`. Docker-based test images exist under `docker/test-images/` for integration testing. These provide production-equivalent topology. However, no seed data scripts or synthetic trace generators exist for agent testing specifically.
- **Gap**: Local testing infrastructure exists but no pre-built sandbox with realistic trace data for agent testing.
- **Compensating Controls**:
  - Use docker-compose to spin up a local Zipkin instance and generate test traces using Zipkin's client libraries.
  - Deploy a staging Zipkin instance with production-equivalent data shape.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create seed data scripts that generate realistic trace data for agent testing scenarios.
- **Evidence**: `docker/examples/docker-compose.yml`, `docker/examples/docker-compose-elasticsearch.yml`, `docker/test-images/`

---

## INFOs — Architecture and Design Inputs

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Span ingestion (`POST /api/v2/spans`) is naturally quasi-idempotent — duplicate spans with the same trace ID and span ID are deduplicated by the `InMemoryStorage` (uses `LinkedHashSet`). No explicit idempotency key support exists. No idempotency middleware or decorators.
- **Implication**: Read-only agents do not execute write operations. If scope expands to write-enabled, idempotency should be evaluated as a BLOCKER.
- **Recommendation**: If expanding to write-enabled agents, implement explicit idempotency keys on write endpoints.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpCollector.java`, `zipkin/src/main/java/zipkin2/storage/InMemoryStorage.java`

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: All query API endpoints return JSON responses (`MediaType.JSON`). Collector endpoints accept JSON (v1, v2), Protobuf (proto3), and Thrift formats. Response serialization uses `SpanBytesEncoder.JSON_V2` for trace data and `DependencyLinkBytesEncoder.JSON_V1` for dependency links. Content-Type headers are properly set.
- **Implication**: JSON responses are well-suited for LLM consumption. Agent tools can parse responses directly.
- **Recommendation**: No action needed. JSON is the ideal format for agent integration.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java`

### API-Q7: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: Zipkin does not emit events or webhooks for state changes. Spans are ingested and stored, but no notification mechanism exists for downstream consumers when new traces arrive or when trace state changes. The collectors (Kafka, RabbitMQ, etc.) consume events but the server does not produce events for external consumption.
- **Implication**: Agents must poll the query API for new traces rather than reacting to events. This is acceptable for most current use cases but limits proactive agent workflows.
- **Recommendation**: Consider adding event emission (SNS, EventBridge, or webhooks) for new trace ingestion events if proactive agent workflows are planned.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java`, `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpCollector.java`

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limit headers (`X-RateLimit-Remaining`, `Retry-After`) are returned in API responses. The storage throttle (`ThrottledStorageComponent`) limits write concurrency but does not expose this to clients via headers. The query timeout (`QUERY_TIMEOUT=11s`) is documented in the README. No API Gateway throttle settings exist in the repository.
- **Implication**: Agents cannot self-throttle based on rate limit headers. They must be configured with conservative polling intervals.
- **Recommendation**: If an API Gateway is deployed (per AUTH-Q1 remediation), configure rate limit response headers.
- **Evidence**: `zipkin-server/src/main/resources/zipkin-server-shared.yml`, `zipkin-server/README.md`

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: INFO
- **Finding**: No identity propagation exists. No JWT parsing middleware, no OAuth2 on-behalf-of flows, no token exchange patterns, no user context headers (`X-User-Id`). Since there is no authentication (AUTH-Q1), identity propagation is moot. Archetype calibration: stateful-crud, standard severity applies; however, this remains INFO because the primary data Zipkin serves (traces) is operational, not user-specific.
- **Implication**: When authentication is added (AUTH-Q1 remediation), identity propagation should be considered to distinguish agent-as-self vs. agent-on-behalf-of-user.
- **Recommendation**: Plan identity propagation as part of the AUTH-Q1 remediation. Ensure the API Gateway passes through identity context to Zipkin.
- **Evidence**: No identity-related code found

### AUTH-Q5: Credential Management

- **Severity**: INFO
- **Finding**: Storage backend credentials are managed via environment variables: `CASSANDRA_USERNAME`/`CASSANDRA_PASSWORD`, `ES_USERNAME`/`ES_PASSWORD`, `MYSQL_USER`/`MYSQL_PASS`, `ACTIVEMQ_USERNAME`/`ACTIVEMQ_PASSWORD`, `RABBIT_USER`/`RABBIT_PASSWORD`. The `ES_CREDENTIALS_FILE` supports file-based credentials with a configurable rotation interval (`ES_CREDENTIALS_REFRESH_INTERVAL`, default 5s). Docker-compose examples use default credentials (e.g., `RABBIT_PASSWORD=guest`). No AWS Secrets Manager or HashiCorp Vault integration.
- **Implication**: Credentials are managed via environment variables, which is acceptable for containerized deployments but lacks rotation and central management. The `ES_CREDENTIALS_FILE` with rotation is a positive pattern.
- **Recommendation**: Use a secrets management system (AWS Secrets Manager, Vault) for production credentials. Avoid committing credentials in docker-compose examples.
- **Evidence**: `zipkin-server/src/main/resources/zipkin-server-shared.yml`, `docker/examples/docker-compose-rabbitmq.yml`

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No optimistic locking, no ETags, no version fields on API responses. `InMemoryStorage` uses Java `synchronized` methods for thread safety. Cassandra provides eventual consistency; Elasticsearch provides optimistic concurrency control internally. No application-level concurrency controls are exposed to API consumers.
- **Implication**: Read-only agents do not perform writes, so concurrency controls are not a concern for the current scope.
- **Recommendation**: If expanding to write-enabled agents, evaluate adding ETags or version fields to enable optimistic concurrency control on write operations.
- **Evidence**: `zipkin/src/main/java/zipkin2/storage/InMemoryStorage.java`

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits exist. `COLLECTOR_SAMPLE_RATE` controls sampling for all clients globally, not per-agent. `MEM_MAX_SPANS=500000` is a global storage limit. No per-session or per-agent limits.
- **Implication**: Read-only agents cannot modify records, so transaction limits are not a concern for the current scope.
- **Recommendation**: If expanding to write-enabled agents, implement per-agent transaction limits.
- **Evidence**: `zipkin-server/src/main/resources/zipkin-server-shared.yml`

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No draft or pending state concept exists. Span ingestion is immediate and final — there is no concept of a pending span that requires approval. The system is designed for high-throughput telemetry ingestion where immediate processing is essential.
- **Implication**: Read-only agents do not make state changes. Draft states are not relevant for the current scope.
- **Recommendation**: If write-enabled agent operations are planned (e.g., archiving traces, modifying tags), consider implementing a draft/approval workflow.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpCollector.java`

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No approval workflow endpoints, no two-step commit patterns, no configurable operation-level flags, no Step Functions with human approval tasks. The system processes all requests immediately.
- **Implication**: Read-only agents do not execute write operations. Approval gates are not relevant for the current scope.
- **Recommendation**: If high-risk write operations are planned for agents, implement configurable approval gates.
- **Evidence**: `zipkin-server/src/main/resources/zipkin-server-shared.yml`

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Field names are human-readable and semantically meaningful: `traceId`, `spanId`, `parentId`, `name` (operation name), `serviceName`, `timestamp`, `duration`, `tags`, `annotations`, `localEndpoint`, `remoteEndpoint`, `kind`. No legacy abbreviations or cryptic codes. The data model is well-documented through the `Span.java`, `Endpoint.java`, `Annotation.java`, and `DependencyLink.java` classes.
- **Implication**: Agent tools can use field names directly without a data dictionary. LLM-based reasoning benefits from clear semantics.
- **Recommendation**: No action needed. Field naming is excellent.
- **Evidence**: `zipkin/src/main/java/zipkin2/Span.java`, `zipkin/src/main/java/zipkin2/Endpoint.java`, `zipkin/src/main/java/zipkin2/Annotation.java`

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No formal data catalog exists (no AWS Glue Data Catalog, no Collibra, no Alation, no DataHub). The `/api/v2/services`, `/api/v2/spans`, and `/api/v2/autocompleteKeys` endpoints serve as informal metadata discovery. The data schema is implicitly documented through the source code data models.
- **Implication**: Agents (or tool builders) must discover the data schema through the API or source code. No centralized catalog accelerates tool definition.
- **Recommendation**: Consider documenting the data model in a machine-readable format (JSON Schema) and exposing it via an API endpoint.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java`

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: Collector metrics track operationally relevant events: `zipkin_collector.messages`, `zipkin_collector.spans`, `zipkin_collector.spans_dropped`, `zipkin_collector.bytes`, `zipkin_collector.messages_dropped` — all broken down by transport (http, grpc, kafka, rabbitmq, etc.). The `http.server.requests` timer provides request-level metrics. However, no higher-level business outcome metrics exist (e.g., trace completeness rate, query satisfaction, resolution time for troubleshooting workflows).
- **Implication**: When agents consume Zipkin, operational metrics will show request volume and errors but not whether agent interactions produce good outcomes.
- **Recommendation**: Define and publish custom metrics for agent-relevant business outcomes (e.g., queries that returned useful results, trace completeness percentage).
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/MicrometerCollectorMetrics.java`, `zipkin-server/src/main/java/zipkin2/server/internal/prometheus/ZipkinPrometheusMetricsConfiguration.java`

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No formal data quality dashboards, profiling reports, or null rate monitoring exist. `MEM_MAX_SPANS=500000` imposes a storage limit. `COLLECTOR_SAMPLE_RATE` controls sampling. Collector metrics (`zipkin_collector.spans_dropped`) provide visibility into data loss. The `SEARCH_ENABLED` flag can disable indexing. However, no data quality scores, completeness metrics, or freshness SLAs are defined.
- **Implication**: Agents acting on trace data cannot assess data quality or completeness. Decisions based on incomplete traces could be incorrect.
- **Recommendation**: Monitor `zipkin_collector.spans_dropped` rate as a proxy for data quality. Document expected data completeness per storage backend.
- **Evidence**: `zipkin-server/src/main/resources/zipkin-server-shared.yml`, `zipkin-server/src/main/java/zipkin2/server/internal/MicrometerCollectorMetrics.java`

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO (Satisfied — no gap identified)
- **Finding**: Zipkin exposes a well-documented REST API at `/api/v2/*` via `ZipkinQueryApiV2.java` (GET endpoints for traces, services, spans, dependencies, autocomplete). Write endpoints at `POST /api/v1/spans` and `POST /api/v2/spans` via `ZipkinHttpCollector.java`. gRPC endpoint at `zipkin.proto3.SpanService/Report` via `ZipkinGrpcCollector.java`. Health at `/health`, metrics at `/metrics` and `/prometheus`. Comprehensive documentation in `zipkin-server/README.md` with external API docs at `https://zipkin.io/zipkin-api/`.
- **Gap**: None — documented REST, gRPC, and messaging interfaces exist.
- **Recommendation**: No action needed. Consider bringing the external OpenAPI spec into the repository (see API-Q2).
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java`, `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpCollector.java`, `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinGrpcCollector.java`, `zipkin-server/README.md`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, GraphQL schema, or equivalent machine-readable specification exists in the repository. External reference at `https://zipkin.io/zipkin-api/zipkin-api.yaml` is not maintained in-repo.
- **Gap**: No in-repo machine-readable API specification.
- **Recommendation**: Add the OpenAPI spec to the repository and integrate validation into CI.
- **Evidence**: No spec files found. External reference in `zipkin-server/README.md`.

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: Error responses returned as `text/plain` via `BodyIsExceptionMessage.java`. HTTP status codes (400, 404, 500) with raw exception messages. No structured JSON error body.
- **Gap**: No machine-parseable error classification (error code, retryable flag).
- **Recommendation**: Implement structured JSON error responses.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/BodyIsExceptionMessage.java`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Span ingestion is quasi-idempotent via deduplication. No explicit idempotency key support.
- **Gap**: No explicit idempotency mechanism.
- **Recommendation**: Evaluate if scope expands to write-enabled.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpCollector.java`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: JSON responses on all query endpoints. Protobuf/Thrift on collector endpoints. Well-structured.
- **Gap**: None.
- **Recommendation**: No action needed.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java`

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has operations >30s OR long-running workflows. Zipkin query operations have an 11s default timeout. No long-running async operations exposed.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: Zipkin does not emit events or webhooks for state changes. Collectors consume events but the server does not produce them for external consumption.
- **Gap**: No event emission mechanism.
- **Recommendation**: Consider adding event emission for proactive agent workflows.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit headers in responses. Storage throttle exists but not exposed to clients. Query timeout (11s) documented.
- **Gap**: No rate limit headers.
- **Recommendation**: Configure rate limit headers if API Gateway is deployed.
- **Evidence**: `zipkin-server/src/main/resources/zipkin-server-shared.yml`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: No authentication mechanism. Server accepts all requests without identity verification. TLS supported but is transport encryption, not authentication.
- **Gap**: No machine identity authentication.
- **Recommendation**: Deploy API Gateway with API key or OAuth2 authentication.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpConfiguration.java`, `zipkin-server/src/main/resources/zipkin-server-shared.yml`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: No authorization model. All endpoints accessible to all callers.
- **Gap**: No scoped permissions.
- **Recommendation**: Implement API Gateway with route-level policies.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpConfiguration.java`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: No ABAC, RBAC, or action-level checks. All endpoints equally accessible.
- **Gap**: No action-level authorization.
- **Recommendation**: Configure method-level restrictions per API key at the API Gateway.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpConfiguration.java`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: No identity propagation. No JWT, OAuth2, or user context headers.
- **Gap**: No identity propagation.
- **Recommendation**: Plan identity propagation as part of AUTH-Q1 remediation.
- **Evidence**: No identity-related code found

#### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: Credentials via environment variables. `ES_CREDENTIALS_FILE` supports file-based rotation. No secrets manager integration.
- **Gap**: No centralized secrets management.
- **Recommendation**: Use AWS Secrets Manager or Vault for production.
- **Evidence**: `zipkin-server/src/main/resources/zipkin-server-shared.yml`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No immutable audit logging. Console logs via SLF4J/Log4j2, not immutable or tamper-evident. No CloudTrail.
- **Gap**: No audit trail for API requests.
- **Recommendation**: Deploy API Gateway with access logging to immutable storage.
- **Evidence**: `zipkin-server/src/main/resources/zipkin-server-shared.yml`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: No authentication means no identities to suspend. No revocation mechanisms.
- **Gap**: Cannot suspend individual agent identities.
- **Recommendation**: API key revocation will be available once AUTH-Q1 is resolved.
- **Evidence**: No authentication code found

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No compensation or rollback. Span ingestion is append-only.
- **Gap**: No rollback capability.
- **Recommendation**: Document append-only nature. Implement compensation if write scope expands.
- **Evidence**: `zipkin/src/main/java/zipkin2/storage/InMemoryStorage.java`

#### STATE-Q2: Queryable Current State
- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive query API: `/api/v2/trace/{traceId}`, `/api/v2/traces` with filters, `/api/v2/services`, `/api/v2/spans`. State is fully queryable.
- **Gap**: No ETags or version fields for conditional requests.
- **Recommendation**: Add ETags to trace query responses.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java`

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: `InMemoryStorage` uses synchronized methods. No application-level concurrency controls exposed to API consumers.
- **Gap**: No optimistic locking or ETags.
- **Recommendation**: Evaluate if write scope expands.
- **Evidence**: `zipkin/src/main/java/zipkin2/storage/InMemoryStorage.java`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: Limited resilience. Netflix concurrency-limits in `ThrottledStorageComponent`. Timeouts configured. No circuit breaker pattern.
- **Gap**: No circuit breakers on storage backend calls.
- **Recommendation**: Add Resilience4j circuit breakers or deploy a service mesh.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/throttle/ThrottledStorageComponent.java`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: Storage-side throttling only. No API-side rate limiting, no WAF rules, no per-client limits.
- **Gap**: No API-side rate limiting.
- **Recommendation**: Deploy API Gateway with per-key rate limits.
- **Evidence**: `zipkin-server/src/main/resources/zipkin-server-shared.yml`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No per-agent transaction limits. Global limits only (`COLLECTOR_SAMPLE_RATE`, `MEM_MAX_SPANS`).
- **Gap**: No per-agent limits.
- **Recommendation**: Evaluate if write scope expands.
- **Evidence**: `zipkin-server/src/main/resources/zipkin-server-shared.yml`

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
- **Finding**: No draft/pending state. Span ingestion is immediate and final.
- **Gap**: No draft state concept.
- **Recommendation**: Consider if write scope expands.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpCollector.java`

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No approval workflows. System processes all requests immediately.
- **Gap**: No approval gates.
- **Recommendation**: Consider if write scope expands.
- **Evidence**: `zipkin-server/src/main/resources/zipkin-server-shared.yml`

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: Docker-compose examples for local testing with multiple storage backends. Docker test images for integration testing. No seed data scripts for agent testing.
- **Gap**: No pre-built sandbox with realistic trace data for agent testing.
- **Recommendation**: Create seed data scripts for agent testing scenarios.
- **Evidence**: `docker/examples/docker-compose.yml`, `docker/test-images/`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: No data classification. Span tags may contain PII. No field-level encryption. No PII detection tools.
- **Gap**: Sensitive data not classified or access-controlled.
- **Recommendation**: Audit span tags for PII. Implement field-level classification and redaction.
- **Evidence**: `zipkin/src/main/java/zipkin2/Span.java`, `zipkin-server/src/main/resources/zipkin-server-shared.yml`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No data residency enforcement in the application. Storage configured by operator via environment variables.
- **Gap**: No application-level data residency controls.
- **Recommendation**: Document residency requirements. Ensure agent LLM calls stay in-region.
- **Evidence**: `zipkin-server/src/main/resources/zipkin-server-shared.yml`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK-QUALITY
- **Finding**: `/api/v2/traces` supports pagination and filtering. Metadata endpoints lack pagination.
- **Gap**: Unbounded results on `/services`, `/spans`, `/autocompleteValues`.
- **Recommendation**: Add pagination to metadata endpoints.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java`

#### DATA-Q4: System of Record Designations
- **Severity**: RISK-QUALITY
- **Finding**: Zipkin IS the system of record for trace data. Clear architecture.
- **Gap**: Not formally documented.
- **Recommendation**: Document Zipkin as system of record in deployment docs.
- **Evidence**: `zipkin/src/main/java/zipkin2/storage/StorageComponent.java`

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK-QUALITY
- **Finding**: Spans have microsecond-precision timestamps. `Cache-Control` on name responses. No freshness signaling on trace queries.
- **Gap**: No freshness headers on trace responses.
- **Recommendation**: Add freshness headers to trace query responses.
- **Evidence**: `zipkin/src/main/java/zipkin2/Span.java`, `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java`

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: No log scrubbing or PII masking. Error responses may expose sensitive span data.
- **Gap**: PII in traces could leak into logs and error responses.
- **Recommendation**: Implement log scrubbing. Review error response handling.
- **Evidence**: `zipkin-server/src/main/resources/zipkin-server-shared.yml`, `zipkin-server/src/main/java/zipkin2/server/internal/BodyIsExceptionMessage.java`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: Collector metrics provide some visibility. No formal data quality dashboards or SLAs.
- **Gap**: No data quality scores or completeness metrics.
- **Recommendation**: Monitor `spans_dropped` rate. Document expected completeness.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/MicrometerCollectorMetrics.java`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: URL versioning (`/api/v1/`, `/api/v2/`). Multiple codec formats supported. No automated breaking change detection in CI.
- **Gap**: No automated breaking change detection.
- **Recommendation**: Add OpenAPI validation and contract tests to CI.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java`, `pom.xml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Excellent field naming: `traceId`, `spanId`, `parentId`, `name`, `serviceName`, `timestamp`, `duration`, `tags`. No legacy abbreviations.
- **Gap**: None.
- **Recommendation**: No action needed.
- **Evidence**: `zipkin/src/main/java/zipkin2/Span.java`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal data catalog. Informal metadata via `/api/v2/services`, `/api/v2/spans`, `/api/v2/autocompleteKeys`.
- **Gap**: No centralized data catalog.
- **Recommendation**: Consider machine-readable schema documentation.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: Self-tracing supported. Brave integration built-in. Trace context in logs. Logs are text-format, not structured JSON.
- **Gap**: Logs not structured JSON by default.
- **Recommendation**: Configure structured JSON logging.
- **Evidence**: `zipkin-server/src/main/resources/zipkin-server-shared.yml`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive Prometheus metrics. No alerting thresholds configured. Alerting is operator responsibility.
- **Gap**: No alerting configured.
- **Recommendation**: Create Prometheus alerting rules for agent-consumed endpoints.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/prometheus/ZipkinPrometheusMetricsConfiguration.java`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: Collector metrics (messages, spans, drops per transport). No higher-level business outcome metrics.
- **Gap**: Metrics are operational, not business-outcome oriented.
- **Recommendation**: Define custom metrics for agent-relevant outcomes.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/MicrometerCollectorMetrics.java`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance
- **Severity**: RISK-QUALITY
- **Finding**: No IaC in the repository. Docker definitions only. Infrastructure provisioning is operator responsibility.
- **Gap**: Integration surface not defined as code.
- **Recommendation**: Create IaC for deployment infrastructure.
- **Evidence**: No IaC files found. `docker/Dockerfile`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive CI/CD (GitHub Actions). No API contract tests. Tests are functional, not contract-oriented.
- **Gap**: No API contract testing in CI.
- **Recommendation**: Add OpenAPI validation and Pact tests to CI.
- **Evidence**: `.github/workflows/test.yml`, `.github/workflows/deploy.yml`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: No automated rollback. Docker images versioned. Manual rollback via previous image version.
- **Gap**: No automated rollback mechanism.
- **Recommendation**: Implement automated rollback in deployment pipeline.
- **Evidence**: `.github/workflows/deploy.yml`, `docker/Dockerfile`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive integration test suite (74 test files). Tests cover API input handling, output format, errors. Run in CI. However, tests are integration-style not contract-style.
- **Gap**: Tests are functional, not contract-oriented.
- **Recommendation**: Add explicit API contract tests for agent-consumed endpoints.
- **Evidence**: `zipkin-server/src/test/java/zipkin2/server/internal/ITZipkinServer.java`, `.github/workflows/test.yml`

#### ENG-Q5: Encryption at Rest
- **Severity**: RISK-QUALITY
- **Finding**: Transport encryption supported (SSL/TLS for Cassandra, Elasticsearch, MySQL). No encryption-at-rest configuration in the application. Operator responsibility.
- **Gap**: No application-level encryption at rest enforcement.
- **Recommendation**: Document encryption-at-rest requirements per storage backend.
- **Evidence**: `zipkin-server/src/main/resources/zipkin-server-shared.yml`

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java` | API-Q1, API-Q2, API-Q3, API-Q5, API-Q7, AUTH-Q2, STATE-Q2, DATA-Q1, DATA-Q3, DATA-Q5, DISC-Q1, DISC-Q3 |
| `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpCollector.java` | API-Q1, API-Q4, API-Q7, AUTH-Q1, AUTH-Q3, STATE-Q1, HITL-Q1 |
| `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinGrpcCollector.java` | API-Q1 |
| `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpConfiguration.java` | AUTH-Q1, AUTH-Q2, AUTH-Q3, STATE-Q5 |
| `zipkin-server/src/main/java/zipkin2/server/internal/BodyIsExceptionMessage.java` | API-Q3, DATA-Q6 |
| `zipkin-server/src/main/java/zipkin2/server/internal/throttle/ThrottledStorageComponent.java` | STATE-Q4 |
| `zipkin-server/src/main/java/zipkin2/server/internal/MicrometerCollectorMetrics.java` | OBS-Q2, OBS-Q3, DATA-Q7 |
| `zipkin-server/src/main/java/zipkin2/server/internal/prometheus/ZipkinPrometheusMetricsConfiguration.java` | OBS-Q2, OBS-Q3 |
| `zipkin-server/src/main/java/zipkin2/server/internal/brave/ZipkinSelfTracingConfiguration.java` | OBS-Q1 |
| `zipkin/src/main/java/zipkin2/Span.java` | DATA-Q1, DATA-Q5, DISC-Q2 |
| `zipkin/src/main/java/zipkin2/Endpoint.java` | DISC-Q2 |
| `zipkin/src/main/java/zipkin2/Annotation.java` | DISC-Q2 |
| `zipkin/src/main/java/zipkin2/storage/InMemoryStorage.java` | API-Q4, STATE-Q1, STATE-Q3 |
| `zipkin/src/main/java/zipkin2/storage/StorageComponent.java` | DATA-Q4 |
| `zipkin-server/src/test/java/zipkin2/server/internal/ITZipkinServer.java` | ENG-Q4 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `zipkin-server/src/main/resources/zipkin-server-shared.yml` | AUTH-Q1, AUTH-Q5, AUTH-Q6, STATE-Q4, STATE-Q5, STATE-Q6, DATA-Q1, DATA-Q2, OBS-Q1, ENG-Q5, API-Q8, HITL-Q2 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/test.yml` | ENG-Q2, ENG-Q4 |
| `.github/workflows/deploy.yml` | ENG-Q2, ENG-Q3 |
| `.github/workflows/security.yml` | ENG-Q2 |
| `.github/workflows/create_release.yml` | ENG-Q3 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `docker/Dockerfile` | ENG-Q1, ENG-Q3 |
| `docker/examples/docker-compose.yml` | HITL-Q3 |
| `docker/examples/docker-compose-elasticsearch.yml` | HITL-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `pom.xml` | DISC-Q1 (zipkin-proto3 version) |
| `zipkin-lens/package.json` | Discovery scan |

### Documentation
| File | Questions Referenced |
|------|---------------------|
| `zipkin-server/README.md` | API-Q1, API-Q2, API-Q8, DATA-Q4 |
| `README.md` | Discovery scan |
