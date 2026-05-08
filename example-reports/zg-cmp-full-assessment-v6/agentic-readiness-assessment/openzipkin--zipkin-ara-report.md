# Agentic Readiness Assessment Report

**Target**: /Users/lucasdu/Documents/AWS-MAC/2026-projects/sample-agentic-readiness-assessment/services/openzipkin--zipkin
**Date**: 2026-05-08
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: java, observability, tracing
**Context**: Distributed tracing system.

**Archetype Justification**: Zipkin has persistent data stores (Cassandra, Elasticsearch, MySQL), exposes both read (query API) and write (span ingestion) endpoints, and manages trace data entity lifecycle — fitting the stateful-crud pattern.

**Surface flags**:
- has_persistent_data_store: true
- has_http_rpc_surface: true
- has_auth_surface: false
- has_write_operations: true
- has_logging_of_user_data: false

---

## Readiness Profile: Pilot-Ready (Safety Concerns)

**BLOCKERs**: 1 | **RISK-SAFETY**: 5 | **RISK-QUALITY**: 9 | **INFOs**: 9

This repo has 1 BLOCKER (High) finding and 5 RISK-SAFETY (Medium, safety-impact) findings. The matched rule is "1-2 High → Remediation Required." Resolve the BLOCKER before any agent deployment — including pilots. The V6 classification maps to "Remediation Required" based on the 1 High finding, regardless of the RISK-SAFETY count.

Resolve all blockers before any agent deployment — including pilots.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 1 |
| RISK-SAFETY | 5 |
| RISK-QUALITY | 9 |
| INFO | 9 |
| N/A | 0 |
| Not Evaluated (extended) | 19 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 0
**Extended Questions Not Triggered**: 19
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: stateful-crud (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: The Zipkin server has no authentication mechanism. No OAuth2, API key, mTLS, or any identity-based access control is implemented. The application is designed to be accessed without authentication, relying entirely on network-level security (reverse proxy, service mesh) for access control.
- **Gap**: No machine identity authentication exists. An agent calling this system cannot be identified, attributed, or distinguished from any other caller. There is no mechanism for principal attribution in any logs.
- **Remediation**:
  - **Immediate**: Deploy an API Gateway or reverse proxy (e.g., AWS API Gateway, Envoy, Istio) in front of Zipkin that enforces API key or OAuth2 client credentials authentication and passes caller identity headers.
  - **Target State**: Every API request is authenticated with a machine identity principal. The authenticated principal is logged in access logs for attribution.
  - **Estimated Effort**: Medium
  - **Dependencies**: AUTH-Q6 (audit logging) depends on this — you cannot log authenticated principals without an authentication mechanism.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java` (no auth annotations), `zipkin-server/src/main/resources/zipkin-server-shared.yml` (no auth config)

---

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No authorization model exists within Zipkin. All API endpoints are accessible to any caller without permission checks. There are no IAM policies, role definitions, or scope-based access controls.
- **Gap**: Without scoped permissions, an agent identity cannot be restricted to read-only access on specific resources. Any caller can both query traces and submit spans.
- **Compensating Controls**:
  - Deploy an API Gateway with method-level authorization (e.g., allow GET /api/v2/* but deny POST /api/v2/spans for read-only agents)
  - Use network segmentation to expose only query endpoints to agent callers
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement API Gateway resource policies that separate read (GET) and write (POST) operations with different authorization levels.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java`, `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpCollector.java` (no auth checks)

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization exists. The server does not distinguish between read and write operations from an access control perspective. Any network-reachable client can execute any operation.
- **Gap**: Cannot enforce action-level policies such as "agent can read traces but cannot submit spans" at the application layer.
- **Compensating Controls**:
  - API Gateway method-level policies (GET vs POST)
  - Service mesh authorization policies (Istio AuthorizationPolicy)
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement authorization at the platform layer (API Gateway or service mesh) with per-method policies.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java`, `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpCollector.java`

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No identity management exists within Zipkin. There is no mechanism to suspend, revoke, or disable any caller's access because there is no identity system.
- **Gap**: Cannot isolate a misbehaving agent without network-level blocking (firewall rules, security groups).
- **Compensating Controls**:
  - API Gateway API key revocation (if API keys are enforced at the gateway layer)
  - Network-level IP blocking via security groups or WAF rules
- **Remediation Timeline**: 30–60 days
- **Recommendation**: When API Gateway authentication is added (AUTH-Q1), ensure API keys can be individually revoked without affecting other agent identities.
- **Evidence**: `zipkin-server/src/main/resources/zipkin-server-shared.yml` (no identity config)

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The application implements storage-level throttling via `ThrottledStorageComponent` using Netflix concurrency-limits for adaptive write-path rate limiting. However, this only throttles storage writes (span ingestion). There is no rate limiting on the query API layer — a runaway agent loop querying `/api/v2/traces` repeatedly would not be throttled.
- **Gap**: No API-layer rate limiting exists for read operations. Query endpoints are unprotected from traffic storms.
- **Compensating Controls**:
  - Deploy AWS API Gateway or WAF with rate limiting rules on query endpoints
  - Configure Armeria server-level request rate limiting
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add API Gateway throttling configuration (e.g., `aws_api_gateway_usage_plan`) or WAF rate rules protecting query endpoints from excessive agent traffic.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/throttle/ThrottledStorageComponent.java` (write-only throttle), `zipkin-server/src/main/resources/zipkin-server-shared.yml` (`storage.throttle` section)

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Zipkin stores and returns trace data which includes service names, span names, endpoint metadata, and user-defined annotations/tags. While the core trace data model does not inherently store PII, user-defined tags (annotation values, span tags) can contain arbitrary data including PII if instrumented applications pass it. The logging configuration (`simplelogger.properties`, `zipkin-server-shared.yml`) shows structured logging with traceId/spanId context but no PII scrubbing or redaction middleware.
- **Gap**: No log scrubbing or PII masking is configured. If upstream services annotate spans with PII (e.g., user email in a tag), Zipkin stores and returns it without redaction.
- **Compensating Controls**:
  - Enforce instrumentation guidelines upstream to prevent PII from being included in span tags
  - Deploy log filtering at the centralized logging layer (CloudWatch Logs filters, Datadog pipelines)
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement tag-level filtering on span ingestion to drop or mask known PII patterns before storage. Add log redaction middleware for structured logging output.
- **Evidence**: `zipkin-server/src/main/resources/zipkin-server-shared.yml` (logging section), `zipkin-server/src/main/resources/simplelogger.properties`

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, Swagger, AsyncAPI, or other machine-readable API specification file exists in the repository. The API is defined solely through Java annotations in Armeria framework code (`@Get`, `@Post`).
- **Gap**: Agent tool generation requires manual authoring of tool definitions rather than automatic generation from a spec. Tool definitions will drift from implementation over time.
- **Compensating Controls**:
  - Generate OpenAPI spec from Armeria annotations using a code-analysis tool
  - Manually maintain an OpenAPI spec as a documentation artifact
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Generate an OpenAPI 3.0 specification from the existing API routes. Armeria supports OpenAPI plugin generation, or the spec can be authored from the existing route definitions in `ZipkinQueryApiV2.java` and `ZipkinHttpCollector.java`.
- **Evidence**: No `openapi.yaml`, `swagger.yaml`, or `swagger.json` files found in repository

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Error responses use plain text bodies with HTTP status codes. The `BodyIsExceptionMessage` exception handler returns `BAD_REQUEST` (400) for `IllegalArgumentException` and `INTERNAL_SERVER_ERROR` (500) for other exceptions, with the exception message as a plain text body. There is no structured error format (no error codes, no retryable indicators).
- **Gap**: Agents cannot programmatically distinguish between error types or determine retryability without parsing plain text messages. No structured error codes or retry guidance in responses.
- **Compensating Controls**:
  - Agent tool definitions can map known HTTP status codes to retry behavior (4xx = terminal, 5xx = retriable)
  - Wrap Zipkin API in an intermediary that adds structured error envelopes
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement a structured JSON error response format with fields: `error_code`, `message`, and `retryable` boolean. Update `BodyIsExceptionMessage` to return JSON instead of plain text.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/BodyIsExceptionMessage.java`

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Zipkin has self-tracing capability via Brave integration (`TracingStorageComponent`), which instruments internal storage operations. The logging pattern includes `traceId` and `spanId` in the log format (`%clr{%5p} %clr{[%X{traceId}/%X{spanId}]}{yellow}`). However, this is self-tracing of Zipkin's own operations — it does not trace inbound API requests from agents in a way that correlates with external distributed tracing systems. Logs use SLF4J with the standard pattern but are not structured JSON.
- **Gap**: Logs are not structured JSON format. While traceId/spanId are included in log patterns, there is no request-level correlation ID for inbound API calls. Self-tracing is available but not enabled by default.
- **Compensating Controls**:
  - Enable self-tracing (`SELF_TRACING_ENABLED=true`) to trace internal operations
  - Deploy a structured logging sidecar or log pipeline that converts output to JSON
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Enable structured JSON logging (e.g., via Logback JSON encoder) and ensure inbound API requests generate correlation IDs that appear in both response headers and logs.
- **Evidence**: `zipkin-server/src/main/resources/zipkin-server-shared.yml` (logging pattern, self-tracing config), `zipkin-server/src/main/java/zipkin2/server/internal/brave/TracingStorageComponent.java`

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Zipkin exposes Prometheus metrics via Micrometer (`ZipkinPrometheusMetricsConfiguration`) including HTTP request duration metrics (`http.server.requests`). A sample `prometheus.yml` exists in `docker/examples/prometheus/`. However, no alerting rules, CloudWatch alarms, or alerting configuration is defined in the repository.
- **Gap**: Metrics are emitted but no alerting thresholds are configured. Degradation of query API performance or elevated error rates would not trigger alerts.
- **Compensating Controls**:
  - Configure Prometheus alerting rules externally based on the exposed metrics
  - Deploy CloudWatch alarms if running on AWS
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Define alerting rules for query API latency p99 and error rate thresholds. If using Prometheus, add alerting rules; if on AWS, configure CloudWatch alarms on key metrics.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/prometheus/ZipkinPrometheusMetricsConfiguration.java`, `docker/examples/prometheus/prometheus.yml`

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The API uses versioned URL paths (`/api/v2/`), indicating awareness of API versioning. However, there is no formal schema versioning, no breaking change detection in CI, no consumer-driven contract tests, and no changelog documenting API changes. The proto definition uses an external dependency (`zipkin-proto3.version=1.0.0`).
- **Gap**: No breaking change detection mechanism in the CI pipeline. API changes could break agent tool bindings without advance notice. No contract testing (e.g., Pact) is present.
- **Compensating Controls**:
  - Pin agent tool definitions to specific API version paths (/api/v2/)
  - Monitor API response schema changes via integration tests
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add OpenAPI spec diffing to CI pipeline (e.g., `oasdiff`) to detect breaking changes. Consider consumer-driven contract tests for agent tool consumers.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java` (v2 API paths), `pom.xml` (`zipkin-proto3.version`)

#### ENG-Q1: Infrastructure Governance — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No Infrastructure as Code files exist in this repository. No Terraform, CloudFormation, CDK, Helm charts, or Kustomize configurations are present. The infrastructure exposing Zipkin to agents is not defined in this codebase.
- **Gap**: The agent-facing integration surface (API gateway, IAM roles, networking) is not governed as code in this repository. Infrastructure may be managed elsewhere or manually.
- **Compensating Controls**:
  - IaC may be maintained in a separate infrastructure repository
  - Docker Compose files provide deployment topology documentation for development/testing
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Create IaC definitions for the Zipkin deployment surface including API gateway, networking, and access controls. If maintained separately, link the infrastructure repo from documentation.
- **Evidence**: No `.tf`, `.cfn.yaml`, `cdk.json`, `Chart.yaml`, or `kustomization.yaml` files found

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The repository has a comprehensive CI/CD pipeline via GitHub Actions (8 workflows) including test, deploy, docker_push, create_release, security scanning (Trivy), and linting. Tests run across JDK 21 and 25 with Docker-based integration tests. However, there are no API contract tests, no OpenAPI validation in CI, and no breaking change detection.
- **Gap**: CI pipeline tests functional correctness but does not validate API contracts. Breaking API changes would not be caught before deployment.
- **Compensating Controls**:
  - Integration tests (`ITZipkinServer`, `ITZipkinServerCORS`, etc.) validate API behavior indirectly
  - Multi-JDK testing ensures compatibility
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add API contract testing to the CI pipeline — either consumer-driven contract tests (Pact) or OpenAPI spec validation. The existing integration tests partially cover this but are not contract-focused.
- **Evidence**: `.github/workflows/test.yml`, `.github/workflows/deploy.yml`, `.github/workflows/security.yml`

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The repository publishes Docker images to Docker Hub and GHCR via CI/CD. The deployment workflow uses Maven release plugin for versioning. Docker images are versioned, enabling rollback by pulling a previous image version. However, no explicit rollback mechanism (blue/green, canary, CodeDeploy) is defined in the repository.
- **Gap**: Rollback relies on external deployment tooling pulling a previous Docker image version. No automated rollback triggers or deployment strategies are defined in the repository.
- **Compensating Controls**:
  - Docker image versioning enables manual rollback to previous versions
  - External orchestration (Kubernetes, ECS) may provide automated rollback
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Define deployment strategy with automated rollback triggers in the deployment environment (e.g., ECS circuit breaker, Kubernetes rollback, CodeDeploy automatic rollback on error threshold).
- **Evidence**: `.github/workflows/deploy.yml`, `.github/workflows/docker_push.yml`, `docker/Dockerfile`

---

## INFOs — Architecture and Design Inputs

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Write endpoints (POST /api/v2/spans) do not implement idempotency keys. Span ingestion is append-only — submitting the same span data twice creates duplicate entries. However, with agent_scope=read-only, agents will not execute write operations.
- **Implication**: If agent scope is later expanded to write-enabled, idempotency for span submission must be addressed. The current append-only design means duplicates degrade query quality but do not corrupt state.
- **Recommendation**: If write-enabled scope is planned, implement deduplication based on traceId+spanId+timestamp as a natural idempotency key.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpCollector.java`

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: All API responses use JSON format. The query API returns JSON-encoded spans (`SpanBytesEncoder.JSON_V2`) and dependency links (`DependencyLinkBytesEncoder.JSON_V1`). The collector also accepts Protobuf and Thrift for span ingestion. Content-Type is `application/json`.
- **Implication**: JSON responses are directly consumable by LLM-based agents. No binary format parsing is required for the query API.
- **Recommendation**: No action needed — JSON is the optimal format for agent consumption.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java` (MediaType.JSON)

### AUTH-Q5: Credential Management

- **Severity**: INFO
- **Finding**: Credentials for backend storage connections (Cassandra, Elasticsearch, MySQL, RabbitMQ, ActiveMQ) are managed through environment variables referenced in YAML configuration. No secrets management system (AWS Secrets Manager, Vault) is integrated. Credentials are not hardcoded in source code — they are parameterized via `${ENV_VAR}` references. The CI/CD pipeline uses GitHub Actions secrets for deployment credentials.
- **Implication**: Environment variable-based credential management is standard for containerized deployments. For production agent integration, consider adding secrets rotation capability.
- **Recommendation**: When deploying to AWS, use AWS Secrets Manager or Parameter Store for storage credentials with automatic rotation.
- **Evidence**: `zipkin-server/src/main/resources/zipkin-server-shared.yml` (CASSANDRA_PASSWORD, ES_PASSWORD, MYSQL_PASS, RABBIT_PASSWORD environment variable references)

### AUTH-Q6: Immutable Audit Logging ⚡

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No audit logging configuration exists within the application. There are no CloudTrail configurations, no immutable log storage, and no per-request principal logging. The logging configuration captures operational logs (traceId/spanId in log pattern) but does not log authenticated principals because no authentication exists.
- **Gap**: No audit trail identifies which caller performed which operation. Without authentication (AUTH-Q1), audit logging of principals is structurally impossible.
- **Recommendation**: After implementing authentication (AUTH-Q1), add per-request audit logging that captures the authenticated principal, action, and timestamp in an immutable store.
- **Evidence**: `zipkin-server/src/main/resources/zipkin-server-shared.yml` (logging section)

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The storage layer uses database-specific concurrency controls (Cassandra write consistency, Elasticsearch optimistic concurrency, MySQL connection pooling via HikariCP). The `ThrottledStorageComponent` provides concurrency limiting for writes. However, these are internal controls, not exposed as API-level ETags or version fields.
- **Implication**: Read-only agents do not require write-level concurrency controls. If scope expands to write-enabled, evaluate whether span ingestion (append-only) needs optimistic locking (likely not — traces are immutable once written).
- **Recommendation**: No action needed for read-only scope. Trace data is append-only by design, reducing concurrency risk.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/throttle/ThrottledStorageComponent.java`

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable per-agent transaction limits exist. The throttle component limits concurrent storage writes but does not provide per-identity rate limiting or blast radius constraints.
- **Implication**: For read-only agents, blast radius is limited to query load (which API-level rate limiting addresses). If write-enabled scope is added, per-agent limits on span ingestion volume would be important.
- **Recommendation**: No action needed for read-only scope. Monitor query volume per agent identity when platform-level auth is added.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/throttle/ThrottledStorageComponent.java`

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: INFO
- **Finding**: No identity propagation mechanism exists because no authentication exists. The system does not support JWT parsing, token exchange, or on-behalf-of flows. The Elasticsearch storage has `BasicAuthInterceptor` for backend storage authentication, but this is internal storage access — not client-facing identity propagation.
- **Implication**: Agent-to-Zipkin calls cannot carry propagated user identity. For a tracing system, this is lower priority — agents typically query traces using service-level identity rather than user-delegated access.
- **Recommendation**: When implementing AUTH-Q1, consider whether agents need to propagate end-user identity or operate under their own service identity (more likely for a tracing system).
- **Evidence**: `zipkin-server/src/main/resources/zipkin-server-shared.yml` (elasticsearch basic auth config is storage-internal)

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limit headers (X-RateLimit-Remaining, Retry-After) are returned by the API. The storage throttle component returns `RejectedExecutionException` when over capacity, which surfaces as a 500 error to clients, but no rate limit signaling exists for query endpoints.
- **Implication**: Agents cannot self-throttle based on server feedback. They would need to implement their own backoff based on error responses.
- **Recommendation**: Add rate limit response headers when platform-level rate limiting is implemented. Return `Retry-After` header on throttled requests.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java`, `zipkin-server/src/main/java/zipkin2/server/internal/throttle/ThrottledStorageComponent.java`

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: Zipkin publishes HTTP request metrics via Micrometer/Prometheus (`http.server.requests` with URI, status, method tags). JVM metrics (GC, memory, threads, classloader) are also exposed. The throttle component publishes concurrency metrics. These are infrastructure/operational metrics, not business outcome metrics.
- **Implication**: For a tracing system, "business outcomes" are operational metrics (traces stored, query latency, storage capacity). These are partially covered by the existing metrics. Agent-specific metrics (queries per agent, agent error rates) are not tracked.
- **Recommendation**: When agent identity is added, publish per-agent-identity metrics (queries/min, error rate, data volume consumed).
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/prometheus/ZipkinPrometheusMetricsConfiguration.java`

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: PASS (no finding)
- **Finding**: Zipkin exposes a well-defined REST API at `/api/v2/` with clear endpoint structure. Query endpoints (GET) serve trace retrieval, service listing, and dependency analysis. Collector endpoints (POST) accept span ingestion in JSON and Protobuf formats. A gRPC collector is also available. This is a proper programmatic API — no direct database access, file-based exchange, or UI automation is required.
- **Gap**: N/A — API interface exists
- **Recommendation**: N/A
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java`, `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpCollector.java`, `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinGrpcCollector.java`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, Swagger, AsyncAPI, or machine-readable API specification exists. API is defined only in Armeria Java annotations.
- **Gap**: Agent tool definitions must be manually authored and will drift from implementation.
- **Recommendation**: Generate OpenAPI 3.0 specification from existing API routes.
- **Evidence**: No spec files found; API defined in `ZipkinQueryApiV2.java` and `ZipkinHttpCollector.java`

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: Error responses are plain text with HTTP status codes. `BodyIsExceptionMessage` returns 400 for `IllegalArgumentException` and 500 for other errors with the exception message as body.
- **Gap**: No structured error codes, no retryable indicator, no machine-parseable error format.
- **Recommendation**: Implement structured JSON error responses with error_code, message, and retryable fields.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/BodyIsExceptionMessage.java`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Span ingestion (POST /api/v2/spans) is not idempotent — duplicate submissions create duplicate data. No idempotency key support.
- **Gap**: Not applicable for read-only agent scope.
- **Recommendation**: If write scope is added, implement deduplication on traceId+spanId.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpCollector.java`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: All query responses are JSON (`MediaType.JSON`). Collector accepts JSON, Protobuf, and Thrift.
- **Implication**: JSON is optimal for LLM/agent consumption.
- **Recommendation**: No action needed.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java`

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
- **Finding**: No rate limit headers returned. Storage throttle returns 500 on overload without Retry-After signaling.
- **Implication**: Agents cannot self-throttle based on server feedback.
- **Recommendation**: Add rate limit headers when platform-level rate limiting is implemented.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: No authentication mechanism exists. The Zipkin server accepts all requests without identity verification.
- **Gap**: Agent callers cannot be identified or attributed.
- **Recommendation**: Deploy API Gateway with OAuth2 client credentials or API key authentication.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java`, `zipkin-server/src/main/resources/zipkin-server-shared.yml`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: No authorization model. All endpoints accessible to all callers.
- **Gap**: Cannot restrict agent to specific operations or resources.
- **Recommendation**: Implement API Gateway resource policies separating read/write access.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization. Read and write operations are equally accessible.
- **Gap**: Cannot enforce "read but not write" at the application layer.
- **Recommendation**: Implement platform-layer authorization policies per HTTP method.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java`, `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpCollector.java`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: No identity propagation mechanism. No JWT/OAuth/mTLS. Archetype calibration: for a tracing system acting as a data-gateway for observability data, identity propagation has lower priority.
- **Gap**: Agent calls cannot carry propagated identity. Low impact for tracing system use case.
- **Recommendation**: Evaluate whether service-level identity (AUTH-Q1) is sufficient for agent use cases.
- **Evidence**: `zipkin-server/src/main/resources/zipkin-server-shared.yml`

#### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: Credentials managed via environment variables. No secrets management system integrated. No hardcoded credentials in source. CI uses GitHub Actions secrets.
- **Implication**: Standard for containerized deployments. Production should use secrets manager with rotation.
- **Recommendation**: Use AWS Secrets Manager for production storage credentials.
- **Evidence**: `zipkin-server/src/main/resources/zipkin-server-shared.yml`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No audit logging. No CloudTrail, no immutable log storage, no per-request principal logging. Without authentication, principal logging is structurally impossible.
- **Gap**: No audit trail for any operations.
- **Recommendation**: Implement audit logging after AUTH-Q1 is resolved.
- **Evidence**: `zipkin-server/src/main/resources/zipkin-server-shared.yml`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: No identity system — cannot suspend individual agent access.
- **Gap**: Cannot isolate misbehaving agents without network-level blocking.
- **Recommendation**: Implement revocable API keys at the gateway layer.
- **Evidence**: `zipkin-server/src/main/resources/zipkin-server-shared.yml`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY, then further calibrated: Zipkin trace storage is append-only. There are no multi-step write workflows that would need compensation. Span ingestion is a single atomic operation. Recording as INFO based on the append-only nature of the write path.
- **Finding**: Trace data is append-only and immutable. There are no multi-step write workflows requiring compensation. Spans are ingested atomically — there is no partial state scenario from a single ingestion call.
- **Gap**: No compensation mechanism, but none is needed for append-only trace storage.
- **Recommendation**: No action needed — trace data model is inherently safe from partial-write scenarios.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpCollector.java`

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
- **Finding**: Storage-level concurrency via ThrottledStorageComponent (Netflix concurrency-limits). Database-specific controls (Cassandra consistency, HikariCP pooling). No API-level ETags.
- **Gap**: Not applicable for read-only scope.
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/throttle/ThrottledStorageComponent.java`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has external dependencies (calls other services or external APIs)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: Write-path throttling exists via ThrottledStorageComponent. No API-layer rate limiting on query endpoints.
- **Gap**: Query endpoints unprotected from agent traffic storms.
- **Recommendation**: Add API Gateway throttling or WAF rate rules for query endpoints.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/throttle/ThrottledStorageComponent.java`, `zipkin-server/src/main/resources/zipkin-server-shared.yml`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No per-agent transaction limits. Throttle provides global concurrency limits only.
- **Gap**: Not applicable for read-only scope.
- **Recommendation**: Monitor query volume per agent when identity is added.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/throttle/ThrottledStorageComponent.java`

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
- **Severity**: PASS (no finding)
- **Finding**: Extensive Docker Compose configurations provide production-equivalent local environments. 14 docker-compose files cover various storage backends (Cassandra, Elasticsearch, MySQL) and collector configurations (Kafka, RabbitMQ, Pulsar, ActiveMQ). These enable realistic testing environments with full storage and collector stacks.
- **Gap**: N/A — sandbox/testing environments are well-supported via Docker Compose
- **Recommendation**: N/A
- **Evidence**: `docker/examples/docker-compose.yml`, `docker/examples/docker-compose-cassandra.yml`, `docker/examples/docker-compose-elasticsearch.yml`, `docker/examples/docker-compose-mysql.yml`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification ⚡
- **Severity**: INFO
- **Conditional**: Stage A evaluation — Zipkin stores distributed trace data: service names, span names, endpoint IPs/ports, trace IDs, span IDs, durations, timestamps, and user-defined annotations/tags. The core data model does not inherently contain PII (no user emails, passwords, or financial data). However, user-defined span tags could contain arbitrary data. The data is operational/observability data, not user account or transactional data. Stage A = borderline — classifying as INFO because the system's primary data model is non-sensitive operational telemetry.
- **Finding**: Trace data (service names, operation names, timing data, endpoint metadata) is operational observability data. User-defined tags could theoretically contain PII if instrumented services annotate spans with such data, but this is not inherent to Zipkin's data model.
- **Gap**: No formal data classification. No tag-level filtering to prevent PII from entering the trace store via user-defined annotations.
- **Recommendation**: Document that trace data is classified as "internal/operational." Implement tag filtering rules to reject or mask known PII patterns during span ingestion.
- **Evidence**: `zipkin/src/main/java/zipkin2/Span.java` (data model), `zipkin-server/src/main/resources/zipkin-server-shared.yml`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — surface-flag calibration: trace data is operational telemetry (service names, timing, topology). While stored persistently, it does not contain regulated PII/PHI/financial data subject to GDPR data residency rules. Recording as INFO.
- **Finding**: Trace data is stored in the configured backend (Cassandra, Elasticsearch, or MySQL). No data residency configuration exists because the data is operational telemetry without regulatory residency requirements.
- **Gap**: No explicit data residency enforcement, but trace data is not subject to typical residency regulations (GDPR personal data, HIPAA PHI).
- **Recommendation**: If traces contain sensitive data from regulated services, evaluate whether trace storage must be region-restricted.
- **Evidence**: `zipkin-server/src/main/resources/zipkin-server-shared.yml` (storage configuration)

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
- **Finding**: No PII scrubbing in logs. User-defined span tags could contain PII. Logging does not filter sensitive content.
- **Gap**: No log redaction middleware for PII that may arrive via span annotations.
- **Recommendation**: Implement tag-level filtering on ingestion and log redaction for known PII patterns.
- **Evidence**: `zipkin-server/src/main/resources/zipkin-server-shared.yml` (logging config)

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
- **Finding**: API uses versioned URL paths (/api/v2/). No formal schema versioning or breaking change detection in CI.
- **Gap**: No breaking change detection mechanism.
- **Recommendation**: Add OpenAPI spec diffing to CI pipeline.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java`, `pom.xml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Always evaluated as INFO
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Always evaluated as INFO
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: Self-tracing available via Brave. Logging includes traceId/spanId in pattern. Logs are not structured JSON. No correlation IDs for inbound requests.
- **Gap**: Non-JSON logs, no request correlation IDs.
- **Recommendation**: Enable structured JSON logging and request correlation IDs.
- **Evidence**: `zipkin-server/src/main/resources/zipkin-server-shared.yml`, `zipkin-server/src/main/java/zipkin2/server/internal/brave/TracingStorageComponent.java`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: Prometheus metrics exposed. No alerting rules configured.
- **Gap**: No alerting thresholds for agent-consumed APIs.
- **Recommendation**: Define Prometheus alerting rules or CloudWatch alarms for API latency and error rates.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/prometheus/ZipkinPrometheusMetricsConfiguration.java`, `docker/examples/prometheus/prometheus.yml`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Always evaluated as INFO
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance
- **Severity**: RISK-QUALITY
- **Finding**: No IaC in this repository. Infrastructure presumably managed elsewhere or manually.
- **Gap**: Agent-facing infrastructure not governed as code in this repo.
- **Recommendation**: Create IaC definitions for the Zipkin deployment surface.
- **Evidence**: No IaC files found

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive CI/CD (8 GitHub Actions workflows, multi-JDK testing, Docker integration tests, Trivy security scanning). No API contract testing.
- **Gap**: Breaking API changes not caught before deployment.
- **Recommendation**: Add API contract testing to CI pipeline.
- **Evidence**: `.github/workflows/test.yml`, `.github/workflows/deploy.yml`, `.github/workflows/security.yml`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: Docker image versioning enables rollback. No automated rollback mechanism defined.
- **Gap**: Rollback relies on external deployment tooling.
- **Recommendation**: Define deployment strategy with automated rollback triggers.
- **Evidence**: `.github/workflows/deploy.yml`, `.github/workflows/docker_push.yml`, `docker/Dockerfile`

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
| zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java | API-Q1, API-Q2, API-Q3, API-Q5, API-Q8, AUTH-Q1, AUTH-Q2, AUTH-Q3, DISC-Q1, STATE-Q5 |
| zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpCollector.java | API-Q1, API-Q2, API-Q4, AUTH-Q3, STATE-Q1 |
| zipkin-server/src/main/java/zipkin2/server/internal/BodyIsExceptionMessage.java | API-Q3 |
| zipkin-server/src/main/java/zipkin2/server/internal/throttle/ThrottledStorageComponent.java | STATE-Q3, STATE-Q5, STATE-Q6, API-Q8 |
| zipkin-server/src/main/java/zipkin2/server/internal/brave/TracingStorageComponent.java | OBS-Q1 |
| zipkin-server/src/main/java/zipkin2/server/internal/prometheus/ZipkinPrometheusMetricsConfiguration.java | OBS-Q2, OBS-Q3 |
| zipkin-server/src/main/java/zipkin2/server/internal/ZipkinGrpcCollector.java | API-Q1 |
| zipkin/src/main/java/zipkin2/Span.java | DATA-Q1 |
| zipkin/src/main/java/zipkin2/storage/StorageComponent.java | STATE-Q3 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| .github/workflows/test.yml | ENG-Q2, ENG-Q4 |
| .github/workflows/deploy.yml | ENG-Q2, ENG-Q3 |
| .github/workflows/docker_push.yml | ENG-Q3 |
| .github/workflows/security.yml | ENG-Q2 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| docker/Dockerfile | ENG-Q3 |
| docker/examples/docker-compose.yml | HITL-Q3 |
| docker/examples/docker-compose-cassandra.yml | HITL-Q3 |
| docker/examples/docker-compose-elasticsearch.yml | HITL-Q3 |
| docker/examples/docker-compose-mysql.yml | HITL-Q3 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| zipkin-server/src/main/resources/zipkin-server-shared.yml | AUTH-Q1, AUTH-Q4, AUTH-Q5, AUTH-Q6, AUTH-Q7, STATE-Q5, DATA-Q1, DATA-Q2, DATA-Q6, OBS-Q1 |
| docker/examples/prometheus/prometheus.yml | OBS-Q2 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| pom.xml | DISC-Q1 |
