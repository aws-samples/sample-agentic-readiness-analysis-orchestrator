# Agentic Readiness Assessment Report

**Target**: openzipkin/zipkin (monorepo — primary service: zipkin-server)
**Date**: 2026-04-30
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**TD Version**: N/A (version not resolved at assessment time)
**Repository Type**: monorepo
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: java, observability, tracing
**Context**: Distributed tracing system.

**Archetype Justification**: Zipkin server owns persistent trace data across multiple configurable storage backends (InMemory, Cassandra, Elasticsearch, MySQL), exposes CRUD-like operations (POST spans for ingestion, GET traces/services/dependencies for querying), and manages the lifecycle of trace data including TTL-based purging.

**Surface flags**:
- has_persistent_data_store: true
- has_http_rpc_surface: true
- has_auth_surface: false
- has_write_operations: true
- has_logging_of_user_data: false

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 1 | **RISK-SAFETY**: 7 | **RISK-QUALITY**: 14 | **INFOs**: 16

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 1 |
| RISK-SAFETY | 7 |
| RISK-QUALITY | 14 |
| INFO | 16 |
| N/A | 0 |
| Not Evaluated (extended) | 5 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 14
**Extended Questions Not Triggered**: 5
**Questions N/A (repo_type: monorepo)**: 0
**Service Archetype**: stateful-crud (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: Zipkin server exposes all API endpoints (REST and gRPC) without any authentication mechanism. No OAuth2, API key validation, mTLS, JWT middleware, service account definitions, API Gateway authorizers, or Cognito integration exists in the codebase. All endpoints at `/api/v1/*`, `/api/v2/*`, `/health`, `/info`, `/prometheus`, and the gRPC `zipkin.proto3.SpanService/Report` are completely open and unauthenticated. The only access control is CORS configuration via `zipkin.query.allowed-origins` (default `*`), which is a browser-side policy, not server-side authentication.
- **Gap**: No machine identity authentication exists. Any client can call any endpoint without identification. There is no way to attribute API calls to a specific agent principal for audit or forensics.
- **Remediation**:
  - **Immediate**: Deploy Zipkin behind an API Gateway (AWS API Gateway, Kong, or Envoy) with API key or OAuth2 client credentials authentication. This provides machine identity without modifying Zipkin source code.
  - **Target State**: All agent-facing API endpoints require authenticated machine identity with principal attribution in audit logs. Each agent has a unique identity (API key or OAuth2 client ID) traceable in logs.
  - **Estimated Effort**: Medium (2–4 weeks for API Gateway setup with auth; Zipkin itself requires no code changes)
  - **Dependencies**: AUTH-Q6 (audit logging) depends on having machine identity first — you cannot log "who" without identity.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpConfiguration.java` (no auth middleware), `zipkin-server/src/main/resources/zipkin-server-shared.yml` (no auth configuration), `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java` (no auth decorators on endpoints)

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No authorization model exists in Zipkin server. There are no IAM policies, role definitions, permission scoping, or access control lists. All API consumers have identical, unlimited access to all endpoints — both read (query API) and write (span ingestion). No IaC files exist in the repository defining IAM roles or API Gateway resource policies.
- **Gap**: Cannot scope an agent identity to read-only access on specific resources. All callers have full access to all endpoints including write operations.
- **Compensating Controls**:
  - Deploy behind an API Gateway with route-level authorization — allow agent identity access only to `GET /api/v2/*` endpoints, blocking `POST /api/v1/spans`, `POST /api/v2/spans`, and gRPC ingestion.
  - Use network-level controls (security groups, VPC policies) to restrict which services can reach the Zipkin write endpoints.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement API Gateway with method-level authorization policies. Define separate API keys for read-only agent access vs. write-enabled collector access.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpConfiguration.java`, `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java` (no permission checks)

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization exists. There is no ABAC, fine-grained RBAC, permission matrices, or action-level middleware (`canRead`, `canWrite`, `canDelete`). All endpoints are equally accessible to all callers.
- **Gap**: Cannot enforce action-level authorization — an agent with any access has full access to all operations including span ingestion (write) and trace querying (read).
- **Compensating Controls**:
  - API Gateway method-level authorization (allow GET, block POST for read-only agents)
  - Service mesh policies (Istio AuthorizationPolicy) restricting HTTP methods per caller identity
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement API Gateway or service mesh policies that enforce action-level access control per agent identity.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpConfiguration.java` (no auth decorators), `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java` (no permission checks on GET handlers)

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No immutable audit logging configuration exists. No CloudTrail, no S3 bucket with object lock for logs, no CloudWatch log retention policies with immutable storage. Zipkin uses Log4j2 with a pattern that includes `traceId/spanId` correlation but does not log authenticated principals (because there is no authentication). The logging pattern `%clr{%5p} %clr{[%X{traceId}/%X{spanId}]}{yellow}` captures trace context but not caller identity.
- **Gap**: No audit trail exists for API operations. Cannot determine which agent or client made which API call. Even debug-level logging in `ZipkinHttpCollector.maybeLog()` only captures `clientAddress` and `userAgent`, not authenticated principal.
- **Compensating Controls**:
  - Deploy behind an API Gateway that logs all requests with caller identity to CloudWatch Logs with retention policies
  - Enable access logging at the load balancer/reverse proxy level
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure API Gateway access logging with caller identity attribution. Store logs in S3 with object lock for immutability.
- **Evidence**: `zipkin-server/src/main/resources/zipkin-server-shared.yml` (logging configuration — no audit trail), `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpCollector.java` (debug logging only captures clientAddress/userAgent)

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No mechanism exists to suspend or revoke individual agent identities. There are no API key revocation endpoints, no IAM role deactivation procedures, no service account disable mechanisms, and no Cognito user pool integration. Since there is no authentication at all, the concept of suspending an individual identity does not apply at the application layer.
- **Gap**: Cannot isolate or disable a misbehaving agent without taking down the entire service or blocking at the network level.
- **Compensating Controls**:
  - API Gateway API key deletion/disabling provides immediate revocation per agent identity
  - Network-level IP blocking via security groups or WAF rules
- **Remediation Timeline**: 30–60 days (tied to AUTH-Q1 remediation — identity must exist before it can be suspended)
- **Recommendation**: Implement API key-based identity at API Gateway. Each agent gets a unique API key that can be individually revoked.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpConfiguration.java` (no identity management), `zipkin-server/src/main/resources/zipkin-server-shared.yml` (no auth/identity configuration)

#### STATE-Q1: Compensation and Rollback ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No compensation or rollback mechanisms exist for multi-step operations. No saga patterns, two-phase commits, explicit undo endpoints, or compensating transactions are found. Zipkin's data model is append-only — spans are ingested and stored but not updated or deleted through the API. There is no `DELETE` endpoint for traces. The closest to state management is `MEM_MAX_SPANS` which purges oldest traces when the limit is exceeded, but this is automated TTL, not compensating logic.
- **Gap**: No ability to undo or compensate for failed multi-step operations. However, given the append-only nature of trace data and the read-only agent scope, the risk is mitigated by the data model itself.
- **Compensating Controls**:
  - The append-only data model inherently limits the blast radius — spans cannot be modified or deleted via API
  - TTL-based data expiration in storage backends (Elasticsearch index lifecycle, Cassandra TTL) provides eventual cleanup
- **Remediation Timeline**: 60–90 days (low priority given append-only model and read-only scope)
- **Recommendation**: Document the append-only data model as a compensating control. For write-enabled scope expansion, implement span deletion endpoints with approval gates.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java` (read-only endpoints), `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpCollector.java` (write-only, no compensation)

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No API-layer rate limiting exists. The `ThrottledStorageComponent` provides adaptive concurrency limiting for storage writes using Netflix `concurrency-limits-core` (Gradient2Limit algorithm), but this only throttles storage write operations — not incoming API requests. The Armeria server has a request timeout of 11 seconds (`sb.requestTimeout(Duration.ofSeconds(11))`) but no per-client rate limiting. No API Gateway throttle settings, WAF rate rules, or application-level rate limiting middleware (`express-rate-limit` equivalent) are configured. The storage throttle is configurable via `STORAGE_THROTTLE_ENABLED`, `STORAGE_THROTTLE_MIN_CONCURRENCY`, `STORAGE_THROTTLE_MAX_CONCURRENCY`, and `STORAGE_THROTTLE_MAX_QUEUE_SIZE`, but these only protect the storage backend, not the API surface itself.
- **Gap**: A runaway agent loop could overwhelm the query API at machine speed. No per-client or per-endpoint rate limiting exists at the HTTP layer.
- **Compensating Controls**:
  - Deploy behind AWS API Gateway with usage plans and throttle settings per API key
  - Add WAF rate rules to limit request rates per source IP
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Deploy API Gateway with usage plans defining request-per-second and burst limits per agent API key. This is achievable without Zipkin code changes.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/throttle/ThrottledStorageComponent.java` (storage throttle only), `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpConfiguration.java` (no rate limiting middleware), `zipkin-server/src/main/resources/zipkin-server-shared.yml` (storage.throttle configuration only)

#### DATA-Q2: Data Residency and Sovereignty ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Zipkin stores trace data in configurable storage backends (InMemory, Cassandra, Elasticsearch, MySQL). No region-specific configurations or data residency controls exist in the codebase. Storage location is determined by the deployment configuration (where the storage backend is deployed), not by the application itself. No cross-region replication settings or data sovereignty policies are defined.
- **Gap**: No explicit data residency controls in the application. An agent could potentially transmit trace data (which may include service endpoint IPs and user-defined tags) to an LLM provider in a different region.
- **Compensating Controls**:
  - Trace data is primarily operational metadata (service names, durations, IPs), not regulated PII — residency risk is lower than for user-facing data
  - Data residency controls should be applied at the deployment/infrastructure layer (IaC defining storage region)
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Define data residency requirements in deployment IaC. Ensure LLM endpoints are co-located with the Zipkin deployment region. Document which trace data fields are safe to transmit to external services.
- **Evidence**: `zipkin-server/src/main/resources/zipkin-server-shared.yml` (storage backend configurations with no region constraints)

### RISK-QUALITY — Address as Capacity Allows

#### AUTH-Q4: Identity Propagation and Delegation — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No identity propagation exists. No JWT parsing middleware, OAuth2 on-behalf-of flows, token exchange patterns, or user context headers are found. Since there is no authentication (AUTH-Q1), there is no identity to propagate. The system does not distinguish between agent-as-self and agent-on-behalf-of-user.
- **Gap**: No identity propagation mechanism exists. Cannot distinguish between an agent acting under its own service identity vs. acting on behalf of a specific human user. The system cannot carry propagated identity through service calls.
- **Compensating Controls**:
  - Address after AUTH-Q1 (machine identity) is resolved — identity must exist before it can be propagated
  - For a tracing system serving operational data, identity propagation has lower impact than in user-facing services
- **Remediation Timeline**: 60–90 days (dependent on AUTH-Q1 resolution)
- **Recommendation**: After AUTH-Q1 is resolved, implement JWT or OAuth2 token exchange to support on-behalf-of flows for agent-delegated access.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpConfiguration.java` (no identity middleware)

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, GraphQL schema, or Smithy specification files exist within the repository. The README references an external API specification at `https://zipkin.io/zipkin-api/` and mentions `zipkin-api.yaml` hosted in a separate `openzipkin/zipkin-api` repository. The gRPC service is defined via `zipkin-proto3` (referenced as a test dependency in `zipkin-server/pom.xml`). While the API is well-documented in the README with endpoint descriptions, parameters, and examples, there is no in-repo machine-readable spec that can be used for automated tool generation.
- **Gap**: Agent frameworks cannot auto-generate tool definitions from an in-repo spec. Manual tool authoring is required, referencing the external `zipkin-api.yaml`.
- **Compensating Controls**:
  - Reference the external `https://zipkin.io/zipkin-api/zipkin-api.yaml` for tool generation
  - Generate OpenAPI spec from Armeria server annotations using Armeria's built-in documentation service
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add the `zipkin-api.yaml` OpenAPI spec as a submodule or copy into the repository. Alternatively, enable Armeria's `DocService` to auto-generate API documentation.
- **Evidence**: `README.md` (references external zipkin-api), `zipkin-server/README.md` (endpoint documentation), `zipkin-server/pom.xml` (zipkin-proto3 test dependency)

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Error responses are returned as plain text (`text/plain`), not structured JSON. The `BodyIsExceptionMessage` exception handler returns HTTP status codes (400 BAD_REQUEST for `IllegalArgumentException`, 500 INTERNAL_SERVER_ERROR for others) with the exception message as the response body in plain text. For example: `HttpResponse.of(BAD_REQUEST, ANY_TEXT_TYPE, message)`. There is no structured error format with error codes, error categories, or retryable indicators. The query API returns `NOT_FOUND` with `"<traceId> not found"` for missing traces.
- **Gap**: Agents cannot distinguish retriable errors from terminal errors programmatically. A 500 with a plain-text message forces agents to parse free-text strings to determine next actions.
- **Compensating Controls**:
  - Build error parsing logic into the agent tool wrapper that maps known error text patterns to structured categories
  - Use HTTP status codes as primary signal (4xx = terminal, 5xx = retriable with backoff)
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement a structured JSON error format: `{"error": {"code": "TRACE_NOT_FOUND", "message": "...", "retryable": false}}`. Modify `BodyIsExceptionMessage` to return JSON error bodies.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/BodyIsExceptionMessage.java` (plain text error responses), `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java` (plain text NOT_FOUND responses)

#### AUTH-Q5: Credential Management — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Storage backend credentials are managed through environment variables: `CASSANDRA_PASSWORD`, `ES_PASSWORD`, `MYSQL_PASS`, `RABBIT_PASSWORD`, `ACTIVEMQ_PASSWORD`. No integration with AWS Secrets Manager, HashiCorp Vault, or any secrets management system is found. Elasticsearch supports file-based credential rotation via `ES_CREDENTIALS_FILE` with configurable refresh interval (`ES_CREDENTIALS_REFRESH_INTERVAL`), which is the most mature credential management pattern in the codebase. No hardcoded credentials are found in source code — all are environment variable-based. The `.settings.xml` references GPG passphrase and Sonatype credentials via environment variables in CI/CD.
- **Gap**: No centralized secrets management with automated rotation. Environment variables are the primary credential delivery mechanism, which is adequate for containerized deployments but lacks rotation automation and audit trails.
- **Compensating Controls**:
  - Use container orchestration secrets (Kubernetes Secrets, ECS Secrets) to inject credentials
  - ES_CREDENTIALS_FILE already supports periodic credential refresh — extend this pattern to other backends
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Integrate with AWS Secrets Manager for all storage backend credentials. Use Kubernetes external-secrets-operator or ECS secrets integration to bridge Secrets Manager to environment variables.
- **Evidence**: `zipkin-server/src/main/resources/zipkin-server-shared.yml` (all credential configs via env vars), `zipkin-server/src/main/java/zipkin2/server/internal/elasticsearch/BasicCredentials.java` (ES credential handling)

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Zipkin supports API versioning via URL paths (`/api/v1/` and `/api/v2/`). The data model has v1 and v2 formats with codec support for both (SpanBytesDecoder.JSON_V1, JSON_V2, THRIFT, PROTO3). The external `zipkin-api` repository maintains the API specification. However, no breaking change detection tools (OpenAPI diff, `buf breaking`, Pact consumer-driven contract tests) are found in the CI pipeline. The `test.yml` workflow runs unit and integration tests but does not include explicit API contract validation or schema comparison steps.
- **Gap**: No automated breaking change detection in CI. API changes could break agent tool bindings without pre-deployment warning.
- **Compensating Controls**:
  - The external `zipkin-api` repo serves as a schema registry
  - Integration tests in `ITZipkinServer.java` cover core API behavior, providing implicit contract testing
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenAPI diff checks in CI comparing the current API spec against the previous version. Alternatively, add Pact consumer-driven contract tests for agent tool bindings.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java` (/api/v2/ endpoints), `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpCollector.java` (/api/v1/ and /api/v2/ write endpoints), `.github/workflows/test.yml` (no contract testing step)

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Zipkin supports self-tracing via Brave when `SELF_TRACING_ENABLED=true`. The logging pattern includes trace context: `%clr{%5p} %clr{[%X{traceId}/%X{spanId}]}{yellow}`. MDCScopeDecorator is configured to put trace IDs into SLF4J MDC context. However, self-tracing is disabled by default. Logging uses Log4j2 but the log format is not structured JSON — it uses a human-readable pattern format. No `correlation_id` or `request_id` field is injected into logs beyond the Brave-provided traceId/spanId.
- **Gap**: Logs are not structured JSON by default. Self-tracing is disabled by default. Without structured logging, automated log analysis for agent-initiated requests requires custom parsing.
- **Compensating Controls**:
  - Enable self-tracing (`SELF_TRACING_ENABLED=true`) for agent-facing deployments
  - Configure Log4j2 with JSON layout for structured log output
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Enable self-tracing and configure Log4j2 JSON layout. Add a `request_id` or `correlation_id` to all API responses and logs.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/brave/ZipkinSelfTracingConfiguration.java` (self-tracing config), `zipkin-server/src/main/resources/zipkin-server-shared.yml` (log pattern with traceId/spanId, self-tracing disabled by default)

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Prometheus metrics are exposed at `/prometheus` and `/actuator/prometheus` via Micrometer integration. HTTP request duration histograms (`http.server.requests`) are recorded with method, URI, and status tags. Collector metrics (messages, bytes, spans, spans_dropped) are exported per transport. JVM metrics (memory, GC, threads, classloader, CPU) are exported. Docker Compose examples include Prometheus and Grafana setup. However, no alerting thresholds, CloudWatch alarms, PagerDuty/OpsGenie integration, or SLO-based alerting configuration exists in the repository.
- **Gap**: Metrics are collected and exported but no alerting rules are defined. Degradation of the Zipkin API would not trigger automated alerts.
- **Compensating Controls**:
  - The Prometheus + Grafana docker-compose example provides a foundation for adding alert rules
  - Prometheus AlertManager can be configured externally without Zipkin code changes
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add Prometheus AlertManager rules for error rate (5xx > 1%), latency (p99 > 5s), and spans_dropped rate. Configure PagerDuty/OpsGenie integration.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/prometheus/ZipkinPrometheusMetricsConfiguration.java` (metrics collection), `docker/examples/docker-compose-prometheus.yml` (Prometheus setup), `zipkin-server/src/main/java/zipkin2/server/internal/MicrometerCollectorMetrics.java` (collector metrics)

#### ENG-Q1: Infrastructure Governance — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No Infrastructure-as-Code files exist in the repository. There are no Terraform, CloudFormation, CDK, Helm charts, or Kustomize definitions for API gateways, IAM roles, secrets, or networking. The deployment infrastructure consists only of a `docker/Dockerfile` (multi-stage build) and `docker/examples/` docker-compose files (learning/development use only, not production). The CI/CD pipeline (`deploy.yml`) pushes artifacts to Maven Central and Docker Hub but does not provision infrastructure. GitHub PRs are required for code changes (change review is present).
- **Gap**: (1) Integration surface (API gateway, IAM, networking) is not defined as IaC — does not exist. (2) Change review exists for code via GitHub PRs. (3) No drift detection.
- **Compensating Controls**:
  - Define IaC in a separate infrastructure repository for the Zipkin deployment
  - Helm charts are available via `helm repo add zipkin https://zipkin.io/zipkin-helm` (external repo)
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Create IaC (Terraform or CDK) defining the API Gateway, IAM roles, security groups, and observability infrastructure for the Zipkin deployment. Reference the external `zipkin-helm` charts for Kubernetes deployments.
- **Evidence**: Repository root (no `.tf`, `.cfn.yaml`, `cdk.json`, `Chart.yaml`, or `kustomization.yaml` files), `docker/Dockerfile`, `.github/workflows/deploy.yml`

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive CI/CD exists via GitHub Actions. `test.yml` runs unit tests on JDK 21 and 25, with Docker-based integration tests for all collector and storage modules (activemq, kafka, rabbitmq, pulsar, cassandra, elasticsearch, mysql, zipkin-server). `security.yml` runs Trivy vulnerability and secret scanning. `deploy.yml` deploys to Maven Central and Docker Hub. However, no API contract testing (Pact, OpenAPI validation, schema comparison) exists in the pipeline. Integration tests in `ITZipkinServer.java` test API behavior but do not explicitly validate API contracts against a spec.
- **Gap**: No explicit API contract testing or breaking change detection in CI. API changes are caught by integration tests but not by spec-based validation.
- **Compensating Controls**:
  - Integration tests (`ITZipkinServer.java`, `ITZipkinGrpcCollector.java`, `ITZipkinServerCORS.java`, etc.) provide implicit API contract coverage
  - Trivy security scanning catches vulnerability-related breaking changes
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenAPI spec validation step to `test.yml` that compares the current API behavior against the external `zipkin-api.yaml` specification.
- **Evidence**: `.github/workflows/test.yml` (comprehensive test matrix), `.github/workflows/security.yml` (Trivy scanning), `zipkin-server/src/test/java/zipkin2/server/internal/ITZipkinServer.java` (integration tests)

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Deployment is Docker-based. `deploy.yml` pushes tagged images to Docker Hub (`openzipkin/zipkin`) and GitHub Container Registry (`ghcr.io/openzipkin/zipkin`). Docker image versioning allows manual rollback by deploying a previous tag. No blue/green deployment configuration, CodeDeploy rollback triggers, Helm rollback, canary deployment, or automated rollback mechanisms exist in the repository.
- **Gap**: Rollback is manual — requires deploying a previous Docker image tag. No automated rollback triggers or canary deployment patterns.
- **Compensating Controls**:
  - Docker image tags provide version pinning for manual rollback
  - Kubernetes Deployment rollback (`kubectl rollout undo`) if deployed on K8s
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement canary deployment with automated rollback triggers based on error rate metrics. Define Helm rollback procedures for Kubernetes deployments.
- **Evidence**: `.github/workflows/deploy.yml` (push to Docker Hub/GHCR), `docker/Dockerfile` (multi-stage build with version tags)

#### DATA-Q4: System of Record Designations — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Zipkin is the de facto system of record for distributed traces — it is the canonical store for span data ingested from instrumented services. However, there is no formal system-of-record designation documented, no master data management process, and no conflict resolution logic for scenarios where trace data might be ingested from multiple collectors or storage backends. The system stores whatever spans it receives without deduplication or golden-record resolution.
- **Gap**: No formal system-of-record designation or master data management process. Agents reasoning across multiple systems may not know that Zipkin is the authoritative source for trace data.
- **Compensating Controls**:
  - Zipkin is inherently the single authoritative source for traces it stores — there is no competing system for the same data
  - The append-only data model reduces conflict scenarios
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document Zipkin as the system of record for distributed trace data. Add metadata to the API responses or documentation indicating data authority and ownership.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java` (query API), `zipkin-server/src/main/resources/zipkin-server-shared.yml` (storage configuration)

#### DATA-Q5: Temporal Metadata and Freshness — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Span data includes precise temporal metadata: `timestamp` (epoch microseconds of span start) and `duration` (microseconds of critical path). These are set directly by instrumentation. However, the query API does not signal data freshness — no `Cache-Control`, `X-Data-Age`, `last_refreshed`, or `consistency_level` headers are returned on trace query responses. The names endpoints (`/api/v2/services`, `/api/v2/spans`) return `Cache-Control: max-age=300, must-revalidate` when service count exceeds 3, but trace data endpoints return no freshness signals. Agents cannot determine whether trace data is current, stale, cached, or eventually consistent.
- **Gap**: No data freshness signaling on trace query endpoints. While individual spans have precise timestamps, the system cannot tell an agent whether the traces returned are from a strongly consistent read or an eventually consistent one (which varies by storage backend — InMemory is consistent, Elasticsearch may have indexing delays, Cassandra has tunable consistency).
- **Compensating Controls**:
  - Span-level `timestamp` and `duration` fields provide temporal anchoring for individual spans
  - The `lookback` and `endTs` query parameters allow time-bounded queries
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `X-Data-Freshness` or `Cache-Control` headers to trace query endpoints. Document the consistency model per storage backend so agents can reason about data reliability.
- **Evidence**: `zipkin/src/main/java/zipkin2/Span.java` (`timestamp` and `duration` fields), `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java` (no freshness headers on trace endpoints, Cache-Control only on names endpoints)

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No encryption-at-rest configuration exists within the Zipkin codebase. No KMS key references, no `kms_key_id` settings on storage resources, and no customer-managed encryption keys are configured. Encryption at rest is delegated entirely to the storage backend: Cassandra supports `use-ssl` for transport encryption but not application-level encryption at rest; Elasticsearch supports `ssl.no-verify` for transport but not application-level encryption at rest; MySQL supports `use-ssl` for transport. No IaC files exist to verify encryption settings on the underlying data stores (S3, EBS, RDS, DynamoDB, etc.).
- **Gap**: No encryption-at-rest controls in the application or IaC. Encryption at rest must be configured at the storage backend deployment layer, which is not defined in this repository.
- **Compensating Controls**:
  - Most cloud-managed storage services (RDS, Elasticsearch Service, Amazon Keyspaces) enable encryption at rest by default
  - Encryption at rest should be configured in the deployment IaC (separate from this repository)
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Define encryption-at-rest requirements in the deployment IaC. Ensure all storage backends (Elasticsearch, Cassandra, MySQL) use encrypted volumes and KMS-managed keys.
- **Evidence**: `zipkin-server/src/main/resources/zipkin-server-shared.yml` (storage configurations with SSL transport options but no encryption-at-rest settings), repository root (no IaC files defining storage encryption)

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Docker Compose examples in `docker/examples/` provide local testing environments for various storage backends (in-memory, Cassandra, Elasticsearch, MySQL) and collectors (Kafka, RabbitMQ, ActiveMQ, Pulsar). The default `docker-compose.yml` runs Zipkin Slim with in-memory storage. InMemoryStorage provides zero-dependency test mode with configurable `MEM_MAX_SPANS`. The Dockerfile includes HEALTHCHECK. However, these are explicitly noted as "meant for learning Zipkin, not production deployments" and do not represent a production-equivalent staging environment.
- **Gap**: No production-equivalent staging environment with realistic data shape. Docker Compose examples are for learning/development only. No seed data scripts or synthetic data generators.
- **Compensating Controls**:
  - Docker Compose examples provide a functional local testing environment
  - InMemoryStorage mode enables rapid agent testing without external dependencies
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Create a staging environment with production-equivalent storage configuration and synthetic trace data. Add seed data scripts that generate representative trace volumes.
- **Evidence**: `docker/examples/docker-compose.yml` ("meant for learning, not production"), `docker/examples/` (15 docker-compose configurations)

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO
- **Finding**: Zipkin exposes a well-documented REST API at `/api/v2/*` and `/api/v1/*` via Armeria HTTP server on port 9411, plus a gRPC endpoint at `zipkin.proto3.SpanService/Report`. The API is documented in `zipkin-server/README.md` with endpoint descriptions, parameters, environment variable configuration, and examples. External documentation at `https://zipkin.io/zipkin-api/` provides comprehensive API reference. No gap — a documented API interface exists.
- **Implication**: Agents can bind to stable, well-documented REST endpoints. The `/api/v2/` surface is suitable for tool definition.
- **Recommendation**: No remediation needed. Consider adding the external API spec into the repository for self-contained documentation.
- **Evidence**: `zipkin-server/README.md`, `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java`, `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpCollector.java`

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The POST `/api/v2/spans` and `/api/v1/spans` endpoints accept span data for ingestion. Spans have natural idempotency via their composite key (traceId + spanId) — submitting the same span twice does not create duplicates in most storage backends. No explicit idempotency key support or middleware exists, but the data model provides implicit idempotency.
- **Implication**: For read-only agent scope, idempotency of write operations is informational only. If scope expands to write-enabled, the natural idempotency of trace spans mitigates risk.
- **Recommendation**: Document the implicit idempotency of span ingestion. If write-enabled agents are planned, validate idempotency behavior across all storage backends.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpCollector.java`, `zipkin/src/main/java/zipkin2/Span.java` (traceId + spanId uniqueness)

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: API responses use structured JSON via `SpanBytesEncoder.JSON_V2` and Jackson serialization. The gRPC endpoint uses Protocol Buffers (proto3). Content-Type headers are set to `application/json`. Cache-Control headers are returned for name-based endpoints when conditions are met. Response format is well-structured and machine-readable.
- **Implication**: JSON responses are ideal for LLM consumption. No additional parsing logic needed for agent tools.
- **Recommendation**: No action needed.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java` (JSON responses)

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limit documentation or headers exist. No `X-RateLimit-Remaining`, `Retry-After`, or similar headers are returned. No API Gateway usage plans or WAF rate rules are configured. The storage throttle rejects requests with `RejectedExecutionException` when capacity is exceeded, but this is returned as a 500 error, not rate-limit headers.
- **Implication**: Agents cannot self-throttle based on rate limit signals. Without rate limit headers, agents will only learn about capacity issues through errors.
- **Recommendation**: If deploying behind API Gateway, ensure rate limit headers are passed through to clients. Add documentation of rate limits to the API reference.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpConfiguration.java` (no rate limit headers), `zipkin-server/src/main/java/zipkin2/server/internal/throttle/ThrottledStorageComponent.java` (storage throttle, no HTTP headers)

### API-Q7: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: Zipkin does not emit events, webhooks, or notifications for state changes (new spans ingested, new services discovered, trace completion). No SNS, EventBridge, SQS, Kafka producer, or webhook endpoint exists for outbound state change notifications. While Zipkin consumes from Kafka/RabbitMQ/ActiveMQ/Pulsar as collectors (inbound span ingestion), it does not produce events to notify downstream consumers of meaningful state changes. The only reactive mechanism is polling the query API.
- **Implication**: Agents cannot react proactively to new trace data or service discovery changes. All agent interactions must be request-driven (polling). This is acceptable for initial read-only deployments but becomes a limitation for event-driven agent patterns.
- **Recommendation**: Consider adding an event emission layer (SNS, EventBridge, or Kafka producer) for key state changes: new service registered, trace exceeding duration threshold, error rate spike detected. This enables proactive agent patterns.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpCollector.java` (ingestion only, no outbound events), `zipkin-server/src/main/resources/zipkin-server-shared.yml` (collector configs are inbound only)

### STATE-Q2: Queryable Current State

- **Severity**: INFO
- **Finding**: Zipkin exposes comprehensive queryable state through its REST API. The query API provides: `GET /api/v2/traces` (search traces with filters: serviceName, spanName, minDuration, maxDuration, endTs, lookback, limit), `GET /api/v2/trace/{traceId}` (retrieve specific trace), `GET /api/v2/traceMany` (retrieve multiple traces), `GET /api/v2/services` (list all service names), `GET /api/v2/spans` (list span names for a service), `GET /api/v2/remoteServices` (list remote services), `GET /api/v2/dependencies` (service dependency graph), `GET /api/v2/autocompleteKeys` and `GET /api/v2/autocompleteValues` (tag autocompletion). Agents can inspect the full current state before taking any action.
- **Implication**: Agents have full read access to Zipkin's current state. No gap exists — queryable state is a strength of this system.
- **Recommendation**: No action needed.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java` (comprehensive query API with filtering, sorting, and limit parameters)

### DATA-Q3: Selective Query Support

- **Severity**: INFO
- **Finding**: The Zipkin query API supports comprehensive selective query capabilities. The `/api/v2/traces` endpoint accepts: `serviceName` (filter by service), `remoteServiceName` (filter by remote service), `spanName` (filter by operation), `annotationQuery` (filter by annotations/tags), `minDuration` and `maxDuration` (duration range filters), `endTs` and `lookback` (time window), and `limit` (default 10, controls result set size). The `QueryRequest` builder validates these parameters. Result sets are bounded by the `limit` parameter. Field selection is not supported (full span objects are returned), but the combination of filters effectively limits result sizes to what an agent needs.
- **Implication**: Agents can query precisely the data they need without retrieving unbounded result sets. The default limit of 10 provides natural bounds. No gap exists.
- **Recommendation**: No action needed. Consider adding cursor-based pagination for large result sets if agent use cases require iterating beyond the limit.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java` (getTraces method with filtering parameters, limit defaults to 10)

### ENG-Q4: API Test Coverage

- **Severity**: INFO
- **Finding**: Comprehensive automated tests exist for the APIs agents will consume. Integration test classes include: `ITZipkinServer.java` (core API endpoint tests for traces, services, spans, dependencies), `ITZipkinGrpcCollector.java` (gRPC endpoint tests), `ITZipkinServerCORS.java` (CORS policy tests), `ITZipkinServerTimeout.java` (timeout behavior), `ITZipkinServerQueryDisabled.java` (disabled query endpoint behavior), `ITZipkinServerHttpCollectorDisabled.java` (disabled collector behavior), `ITZipkinServerAutocomplete.java` (autocomplete API tests), `ITZipkinServerSsl.java` (SSL configuration tests), `ITZipkinHealth.java` and `ITZipkinHealthDown.java` (health endpoint tests), `ITZipkinMetrics.java` and `ITZipkinMetricsDirty.java` (metrics endpoint tests). These run in CI via the `test.yml` GitHub Actions workflow on JDK 21 and 25. Tests cover input handling, output format, error responses, and edge cases.
- **Implication**: API behavior changes are caught by comprehensive integration tests before deployment. Agent tool bindings are protected by existing test coverage.
- **Recommendation**: No immediate action needed. Consider adding explicit API contract tests (Pact or OpenAPI-based) to complement the existing integration tests.
- **Evidence**: `zipkin-server/src/test/java/zipkin2/server/internal/ITZipkinServer.java`, `zipkin-server/src/test/java/zipkin2/server/internal/ITZipkinGrpcCollector.java`, `zipkin-server/src/test/java/zipkin2/server/internal/ITZipkinServerCORS.java`, `.github/workflows/test.yml` (CI pipeline running tests)

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No optimistic locking, pessimistic locking, ETags, or version fields exist. Zipkin's data model is append-only — spans are written once and never updated. The storage throttle uses adaptive concurrency limiting (Netflix Gradient2Limit) to control concurrent writes to storage, but this is not concurrency control in the traditional sense.
- **Implication**: For read-only agents, concurrency controls are not needed. The append-only data model eliminates write-write conflicts.
- **Recommendation**: No action needed for read-only scope. If write-enabled scope is planned, the append-only model inherently avoids most concurrency issues.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/throttle/ThrottledStorageComponent.java`

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits exist for agent-initiated actions. No `max_records_per_query`, `max_spend_per_hour`, or similar limits are configurable per agent identity. Query results are limited by the `limit` parameter (default 10) in the trace search endpoint.
- **Implication**: For read-only agents, transaction limits are informational. The default query `limit=10` provides natural bounds on result sets.
- **Recommendation**: No action needed for read-only scope. If write-enabled scope is planned, consider adding per-agent-identity write limits.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java` (limit parameter defaults to 10)

### DATA-Q1: Sensitive Data Classification

- **Severity**: INFO
- **Finding**: Stage A evaluation — Zipkin stores trace data containing service names, operation names, durations, endpoint IPs, and user-defined tags. Tags MAY contain sensitive data if instrumented applications explicitly add PII as span tags (e.g., `user_id`, `email`). However, the system itself does not classify, restrict, or filter what goes into tags — it is a pass-through for trace data. The core data model (Span.java) includes traceId, spanId, parentId, name, kind, timestamp, duration, localEndpoint, remoteEndpoint, annotations, and tags. Endpoint IPs are operational metadata, not PII. The system's purpose is operational observability, not user data processing.
- **Implication**: Zipkin is primarily an operational observability tool. Sensitive data classification should be enforced at the instrumentation layer (the applications sending traces to Zipkin), not at the Zipkin server itself. Agent access to trace data is low-risk for PII exposure.
- **Recommendation**: Document that PII should not be included in span tags. Consider adding tag-level filtering/redaction for sensitive keys.
- **Evidence**: `zipkin/src/main/java/zipkin2/Span.java` (data model), `zipkin-server/src/main/resources/zipkin-server-shared.yml` (autocomplete-keys configuration)

### DATA-Q6: PII Redaction in Logs

- **Severity**: INFO
- **Finding**: has_logging_of_user_data is false. Zipkin logs operational metrics and trace context (traceId/spanId) but does not log user PII. Debug-level logging in `ZipkinHttpCollector.maybeLog()` captures `clientAddress` and `userAgent` — these are network metadata, not user PII. No request body logging exists in production. The trace data itself (service names, operation names, tags) is operational data, not PII, unless explicitly tagged by instrumented applications.
- **Implication**: PII-in-logs risk is minimal for a tracing system. The primary risk vector is user-defined span tags, which are not logged by the server but stored in the database.
- **Recommendation**: No immediate action needed. If agents will read traces that may contain PII in tags, implement field-level filtering in the agent tool.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpCollector.java` (debug logging only), `zipkin-server/src/main/resources/zipkin-server-shared.yml` (logging configuration)

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality scores, completeness metrics, or data profiling exist. Collector metrics track message counts, byte counts, span counts, and dropped spans/messages per transport — but these are throughput metrics, not data quality metrics. No null rate monitoring, duplicate detection, or data freshness SLAs exist.
- **Implication**: Agent decisions based on trace data cannot be validated against data quality signals. Incomplete traces (missing spans) are a known limitation of distributed tracing.
- **Recommendation**: Consider adding data quality metrics (e.g., percentage of traces with missing spans, tag completeness rate) to the Prometheus endpoint.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/MicrometerCollectorMetrics.java` (throughput metrics only)

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Zipkin uses clear, semantically meaningful field names throughout the data model and API. Examples: `traceId`, `spanId`, `parentId`, `operationName`, `serviceName`, `localEndpoint`, `remoteEndpoint`, `tags`, `annotations`, `timestamp`, `duration`, `kind` (CLIENT, SERVER, PRODUCER, CONSUMER). No legacy abbreviations or codes requiring a data dictionary. The `Endpoint` object uses `serviceName`, `ipv4`, `ipv6`, `port`. API query parameters are equally clear: `serviceName`, `spanName`, `minDuration`, `maxDuration`, `endTs`, `lookback`, `limit`.
- **Implication**: LLM-based agent reasoning can interpret field names directly without a translation layer.
- **Recommendation**: No action needed. Field naming is exemplary.
- **Evidence**: `zipkin/src/main/java/zipkin2/Span.java`, `zipkin/src/main/java/zipkin2/Endpoint.java`, `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java`

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No formal data catalog or metadata layer exists (no AWS Glue Data Catalog, Collibra, Alation, or DataHub integration). However, the Zipkin data model is self-documenting through well-named Java classes (`Span.java`, `Endpoint.java`, `DependencyLink.java`) and the external API specification at `zipkin.io/zipkin-api/`. The README provides comprehensive documentation of the data model and query capabilities.
- **Implication**: Accelerates tool definition when building agent tools — the data model is well-documented even without a formal catalog.
- **Recommendation**: Consider publishing data model documentation to an internal API catalog or developer portal.
- **Evidence**: `README.md`, `zipkin-server/README.md`, `zipkin/src/main/java/zipkin2/Span.java`

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: Collector metrics (messages, bytes, spans, spans_dropped per transport) and HTTP request duration histograms are exported via Micrometer/Prometheus. JVM metrics (memory, GC, threads) are exported. These are operational and infrastructure metrics, not business outcome metrics. No custom metrics for trace query resolution rates, user satisfaction, or trace completeness are published.
- **Implication**: When agents consume the Zipkin API, there is no metric tracking whether the traces returned to agents are useful (e.g., trace completeness, query result quality).
- **Recommendation**: Consider adding business outcome metrics such as trace completeness rate, average spans per trace, and query latency percentiles per service.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/MicrometerCollectorMetrics.java`, `zipkin-server/src/main/java/zipkin2/server/internal/prometheus/ZipkinPrometheusMetricsConfiguration.java`

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: Zipkin exposes documented REST endpoints (`/api/v2/traces`, `/api/v2/trace/{traceId}`, `/api/v2/services`, `/api/v2/spans`, `/api/v2/dependencies`, `/api/v2/remoteServices`, `/api/v2/autocompleteKeys`, `/api/v2/autocompleteValues`, `/api/v2/traceMany`) and gRPC (`zipkin.proto3.SpanService/Report`). Write endpoints include `POST /api/v2/spans` and `POST /api/v1/spans`. The API is documented externally at `https://zipkin.io/zipkin-api/` and in `zipkin-server/README.md`. No gap — a documented API interface exists.
- **Gap**: None — documented API interface exists.
- **Recommendation**: No remediation needed. Consider adding the external API spec into the repository for self-contained documentation.
- **Evidence**: `zipkin-server/README.md`, `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java`, `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpCollector.java`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI/Swagger/AsyncAPI/GraphQL spec files found in the repository. External `zipkin-api.yaml` at `https://zipkin.io/zipkin-api/`. gRPC proto at `zipkin-proto3`.
- **Gap**: No in-repo machine-readable spec for automated tool generation.
- **Recommendation**: Add `zipkin-api.yaml` to the repository or enable Armeria DocService.
- **Evidence**: `README.md`, `zipkin-server/pom.xml`

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: Error responses are plain text (`text/plain`). `BodyIsExceptionMessage` returns HTTP status codes with exception message as body. No structured JSON error codes, no retryable boolean.
- **Gap**: Agents cannot programmatically distinguish retriable from terminal errors.
- **Recommendation**: Implement structured JSON error format.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/BodyIsExceptionMessage.java`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Spans have natural idempotency via traceId+spanId composite key. No explicit idempotency key support.
- **Gap**: N/A for read-only scope.
- **Recommendation**: Document implicit idempotency.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpCollector.java`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: JSON responses via `SpanBytesEncoder.JSON_V2`. gRPC uses Proto3. Content-Type: application/json.
- **Gap**: None.
- **Recommendation**: No action needed.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java`

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has operations >30s OR long-running workflows. Zipkin query timeout is 11s; no long-running workflows detected.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: Zipkin does not emit events, webhooks, or notifications for state changes. No SNS, EventBridge, SQS, Kafka producer, or webhook endpoint exists for outbound state change notifications. While Zipkin consumes from Kafka/RabbitMQ/ActiveMQ/Pulsar as collectors (inbound span ingestion), it does not produce events to notify downstream consumers of meaningful state changes.
- **Gap**: No event emission mechanism exists for state changes. Agents must poll the query API to detect new data.
- **Recommendation**: Consider adding an event emission layer for key state changes (new service registered, trace exceeding duration threshold). This enables proactive agent patterns.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpCollector.java` (ingestion only, no outbound events), `zipkin-server/src/main/resources/zipkin-server-shared.yml` (collector configs are inbound only)

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit documentation or headers. No X-RateLimit-Remaining or Retry-After headers.
- **Gap**: Agents cannot self-throttle.
- **Recommendation**: Add rate limit headers via API Gateway.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpConfiguration.java`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: No authentication mechanism exists. All endpoints are open/unauthenticated. No OAuth2, API key, mTLS, JWT, or Cognito integration.
- **Gap**: No machine identity — cannot attribute API calls to agent principals.
- **Recommendation**: Deploy behind API Gateway with OAuth2 or API key authentication.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpConfiguration.java`, `zipkin-server/src/main/resources/zipkin-server-shared.yml`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: No authorization model. All callers have unlimited access.
- **Gap**: Cannot scope agent to read-only access.
- **Recommendation**: API Gateway with route-level authorization.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpConfiguration.java`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: No ABAC/RBAC. No action-level checks.
- **Gap**: Cannot enforce read vs. write per agent.
- **Recommendation**: API Gateway method-level authorization.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: RISK-QUALITY
- **Finding**: No identity propagation exists. No JWT parsing middleware, OAuth2 on-behalf-of flows, token exchange patterns, or user context headers are found. Since there is no authentication (AUTH-Q1), there is no identity to propagate. The system does not distinguish between agent-as-self and agent-on-behalf-of-user. Archetype calibration to INFO applies only to `stateless-utility` and `data-gateway` archetypes; `stateful-crud` retains the base RISK severity.
- **Gap**: No identity propagation mechanism. Cannot distinguish agent-as-self vs. agent-on-behalf-of-user.
- **Recommendation**: Address after AUTH-Q1 is resolved. Implement JWT or OAuth2 token exchange to support on-behalf-of flows.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpConfiguration.java` (no identity middleware)

#### AUTH-Q5: Credential Management
- **Severity**: RISK-QUALITY
- **Finding**: Credentials managed via environment variables. ES_CREDENTIALS_FILE supports file-based rotation. No Secrets Manager or Vault integration. No hardcoded credentials in source.
- **Gap**: No centralized secrets management with automated rotation.
- **Recommendation**: Integrate with AWS Secrets Manager.
- **Evidence**: `zipkin-server/src/main/resources/zipkin-server-shared.yml`, `zipkin-server/src/main/java/zipkin2/server/internal/elasticsearch/BasicCredentials.java`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No immutable audit logging. No CloudTrail. Log4j2 pattern includes traceId/spanId but not caller identity.
- **Gap**: No audit trail for API operations.
- **Recommendation**: API Gateway access logging with caller identity to CloudWatch Logs.
- **Evidence**: `zipkin-server/src/main/resources/zipkin-server-shared.yml`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: No identity suspension mechanism. No API key revocation. No IAM role management.
- **Gap**: Cannot isolate misbehaving agents.
- **Recommendation**: Implement API key-based identity with revocation at API Gateway.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpConfiguration.java`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No compensation/rollback. Append-only data model.
- **Gap**: No undo capability. Mitigated by append-only model.
- **Recommendation**: Document append-only model as compensating control.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpCollector.java`

#### STATE-Q2: Queryable Current State
- **Severity**: INFO
- **Finding**: Zipkin exposes comprehensive queryable state through its REST API: `GET /api/v2/traces` (search with filters), `GET /api/v2/trace/{traceId}` (retrieve specific trace), `GET /api/v2/traceMany` (batch retrieval), `GET /api/v2/services`, `GET /api/v2/spans`, `GET /api/v2/remoteServices`, `GET /api/v2/dependencies`, `GET /api/v2/autocompleteKeys`, `GET /api/v2/autocompleteValues`. Agents can inspect the full current state before taking any action. No gap exists.
- **Gap**: None — comprehensive queryable state exists.
- **Recommendation**: No action needed.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java` (comprehensive query API)

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No optimistic/pessimistic locking. Append-only data model eliminates write conflicts.
- **Gap**: N/A for read-only scope.
- **Recommendation**: No action needed.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/throttle/ThrottledStorageComponent.java`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has external dependencies (calls other services or external APIs). Zipkin-server calls storage backends but these are internal dependencies, not external service APIs. The ThrottledStorageComponent provides adaptive concurrency limiting.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No API-layer rate limiting. Storage throttle only protects backend writes. No per-client rate limiting.
- **Gap**: Runaway agent loops could overwhelm the query API.
- **Recommendation**: Deploy API Gateway with usage plans.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/throttle/ThrottledStorageComponent.java`, `zipkin-server/src/main/resources/zipkin-server-shared.yml`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No per-agent transaction limits. Query limit defaults to 10.
- **Gap**: N/A for read-only scope.
- **Recommendation**: No action needed.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path. Priority is P2; not on critical path.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled. Agent scope is read-only — not triggered.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled. Agent scope is read-only — not triggered.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: Docker Compose examples for learning/development. InMemoryStorage for zero-dependency testing. Not production-equivalent.
- **Gap**: No production-equivalent staging with realistic data.
- **Recommendation**: Create staging environment with synthetic trace data.
- **Evidence**: `docker/examples/docker-compose.yml`, `docker/examples/`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO
- **Finding**: Stage A = No. Zipkin stores operational trace data (service names, operation names, durations, IPs). Tags MAY contain PII if instrumented apps add it, but the system is not a data-handling target by design. Trace data is operational observability data, not user data.
- **Gap**: None — not a data-handling target for PII/PHI/financial data.
- **Recommendation**: Document that PII should not be included in span tags.
- **Evidence**: `zipkin/src/main/java/zipkin2/Span.java`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Zipkin stores trace data in configurable storage backends. No region-specific configurations or data residency controls exist in the codebase. Storage location is determined by the deployment configuration (where Cassandra/Elasticsearch/MySQL is deployed), not by the application itself.
- **Gap**: No explicit data residency controls. An agent could potentially transmit trace data (which may include service endpoint IPs) to an LLM provider in a different region.
- **Compensating Controls**: Trace data is operational metadata (service names, durations), not regulated PII. Residency controls should be applied at the deployment layer.
- **Recommendation**: Define data residency requirements in the deployment IaC. Ensure LLM endpoints are in the same region as the Zipkin deployment.
- **Evidence**: `zipkin-server/src/main/resources/zipkin-server-shared.yml` (storage backend configurations)

#### DATA-Q3: Selective Query Support
- **Severity**: INFO
- **Finding**: The Zipkin query API supports comprehensive selective query capabilities. The `/api/v2/traces` endpoint accepts: `serviceName`, `remoteServiceName`, `spanName`, `annotationQuery`, `minDuration`, `maxDuration`, `endTs`, `lookback`, and `limit` (default 10). The `QueryRequest` builder validates these parameters. Result sets are bounded by the `limit` parameter. No gap exists.
- **Gap**: None — comprehensive filtering, time-windowing, and result-size limiting exist.
- **Recommendation**: No action needed. Consider adding cursor-based pagination for large result sets.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java` (getTraces method with filtering, limit defaults to 10)

#### DATA-Q4: System of Record Designations
- **Severity**: RISK-QUALITY
- **Finding**: Zipkin is the de facto system of record for distributed traces — it is the canonical store for span data ingested from instrumented services. However, there is no formal system-of-record designation documented, no master data management process, and no conflict resolution logic. The system stores whatever spans it receives without deduplication or golden-record resolution.
- **Gap**: No formal system-of-record designation or master data management process documented.
- **Recommendation**: Document Zipkin as the system of record for distributed trace data. Add metadata to API responses or documentation indicating data authority.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java` (query API), `zipkin-server/src/main/resources/zipkin-server-shared.yml` (storage configuration)

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK-QUALITY
- **Finding**: Span data includes precise temporal metadata: `timestamp` (epoch microseconds of span start) and `duration` (microseconds of critical path), set directly by instrumentation. However, the trace query API does not signal data freshness — no `Cache-Control`, `X-Data-Age`, `last_refreshed`, or `consistency_level` headers on trace endpoints. Names endpoints return `Cache-Control: max-age=300` when service count exceeds 3. Agents cannot determine whether trace data is from a strongly consistent read or an eventually consistent one (varies by storage backend).
- **Gap**: No data freshness signaling on trace query endpoints. Consistency model varies by storage backend but is not communicated to API consumers.
- **Recommendation**: Add `X-Data-Freshness` or `Cache-Control` headers to trace query endpoints. Document the consistency model per storage backend.
- **Evidence**: `zipkin/src/main/java/zipkin2/Span.java` (`timestamp` and `duration` fields), `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java` (no freshness headers on trace endpoints)

#### DATA-Q6: PII Redaction in Logs
- **Severity**: INFO
- **Finding**: has_logging_of_user_data is false. No PII in logs. Debug logging captures clientAddress/userAgent only.
- **Gap**: None — PII-in-logs risk not applicable for this system.
- **Recommendation**: No action needed.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpCollector.java`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality scores or completeness metrics. Collector metrics track throughput only.
- **Gap**: No data quality signals for agent reasoning.
- **Recommendation**: Consider adding trace completeness metrics.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/MicrometerCollectorMetrics.java`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: API versioning via URL paths (/api/v1/, /api/v2/). v1 and v2 codecs. External zipkin-api repo. No breaking change detection in CI.
- **Gap**: No automated breaking change detection.
- **Recommendation**: Add OpenAPI diff checks in CI.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java`, `.github/workflows/test.yml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Clear, semantic field names: traceId, spanId, parentId, serviceName, localEndpoint, remoteEndpoint, tags, annotations, timestamp, duration. No legacy abbreviations.
- **Gap**: None.
- **Recommendation**: No action needed.
- **Evidence**: `zipkin/src/main/java/zipkin2/Span.java`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal data catalog. Data model self-documented via Java classes and external API spec.
- **Gap**: No formal catalog.
- **Recommendation**: Publish data model to internal API catalog.
- **Evidence**: `README.md`, `zipkin/src/main/java/zipkin2/Span.java`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: Self-tracing via Brave (disabled by default). Log pattern includes traceId/spanId. Not structured JSON. Log4j2 with human-readable format.
- **Gap**: Logs not structured JSON. Self-tracing disabled by default.
- **Recommendation**: Enable self-tracing. Configure JSON log layout.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/brave/ZipkinSelfTracingConfiguration.java`, `zipkin-server/src/main/resources/zipkin-server-shared.yml`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: Prometheus metrics exposed. HTTP duration histograms. Collector metrics. No alerting thresholds or AlertManager configuration.
- **Gap**: No alerting rules defined.
- **Recommendation**: Add Prometheus AlertManager rules.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/prometheus/ZipkinPrometheusMetricsConfiguration.java`, `docker/examples/docker-compose-prometheus.yml`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: Operational metrics only (collector throughput, JVM, HTTP durations). No business outcome metrics.
- **Gap**: No business outcome signals.
- **Recommendation**: Add trace completeness and query quality metrics.
- **Evidence**: `zipkin-server/src/main/java/zipkin2/server/internal/MicrometerCollectorMetrics.java`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance
- **Severity**: RISK-QUALITY
- **Finding**: No IaC in repository. Dockerfile and docker-compose only. GitHub PRs for change review. No drift detection.
- **Gap**: No IaC for integration surface.
- **Recommendation**: Create IaC for deployment infrastructure.
- **Evidence**: Repository root (no IaC files), `docker/Dockerfile`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive CI/CD via GitHub Actions. Unit tests, Docker integration tests, Trivy security scanning. No API contract testing.
- **Gap**: No spec-based API contract validation.
- **Recommendation**: Add OpenAPI spec validation to CI pipeline.
- **Evidence**: `.github/workflows/test.yml`, `.github/workflows/security.yml`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: Docker image versioning allows manual rollback. No automated rollback, blue/green, or canary patterns.
- **Gap**: Rollback is manual.
- **Recommendation**: Implement canary deployment with automated rollback.
- **Evidence**: `.github/workflows/deploy.yml`, `docker/Dockerfile`

#### ENG-Q4: API Test Coverage
- **Severity**: INFO
- **Finding**: Comprehensive automated tests exist for the APIs agents will consume. Integration test classes include: `ITZipkinServer.java` (core API endpoint tests), `ITZipkinGrpcCollector.java` (gRPC), `ITZipkinServerCORS.java` (CORS), `ITZipkinServerTimeout.java` (timeout), `ITZipkinServerQueryDisabled.java`, `ITZipkinServerHttpCollectorDisabled.java`, `ITZipkinServerAutocomplete.java`, `ITZipkinServerSsl.java`, `ITZipkinHealth.java`, `ITZipkinHealthDown.java`, `ITZipkinMetrics.java`, `ITZipkinMetricsDirty.java`. These run in CI via `test.yml` on JDK 21 and 25. Tests cover input handling, output format, error responses, and edge cases. No gap exists.
- **Gap**: None — comprehensive API test coverage exists and runs in CI.
- **Recommendation**: No immediate action needed. Consider adding explicit API contract tests (Pact or OpenAPI-based) to complement integration tests.
- **Evidence**: `zipkin-server/src/test/java/zipkin2/server/internal/ITZipkinServer.java`, `zipkin-server/src/test/java/zipkin2/server/internal/ITZipkinGrpcCollector.java`, `.github/workflows/test.yml`

#### ENG-Q5: Encryption at Rest
- **Severity**: RISK-QUALITY
- **Finding**: No encryption-at-rest configuration exists within the Zipkin codebase. No KMS key references, no `kms_key_id` settings on storage resources, and no customer-managed encryption keys are configured. Storage backends support SSL for transport encryption (Cassandra `use-ssl`, Elasticsearch `ssl.no-verify`, MySQL `use-ssl`) but not application-level encryption at rest. No IaC files exist to verify encryption settings on the underlying data stores.
- **Gap**: No encryption-at-rest controls in the application or IaC. Encryption at rest must be configured at the storage backend deployment layer.
- **Recommendation**: Define encryption-at-rest requirements in the deployment IaC. Ensure all storage backends use encrypted volumes and KMS-managed keys.
- **Evidence**: `zipkin-server/src/main/resources/zipkin-server-shared.yml` (storage configs with SSL transport only, no encryption-at-rest), repository root (no IaC files)

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java` | API-Q1, API-Q2, API-Q3, API-Q5, AUTH-Q2, AUTH-Q3, DISC-Q1, STATE-Q6 |
| `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpCollector.java` | API-Q1, API-Q4, AUTH-Q6, STATE-Q1, DATA-Q6 |
| `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinGrpcCollector.java` | API-Q1 |
| `zipkin-server/src/main/java/zipkin2/server/internal/BodyIsExceptionMessage.java` | API-Q3 |
| `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinHttpConfiguration.java` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q7, API-Q8, STATE-Q5 |
| `zipkin-server/src/main/java/zipkin2/server/internal/ZipkinConfiguration.java` | AUTH-Q1 |
| `zipkin-server/src/main/java/zipkin2/server/internal/throttle/ThrottledStorageComponent.java` | STATE-Q3, STATE-Q5 |
| `zipkin-server/src/main/java/zipkin2/server/internal/brave/ZipkinSelfTracingConfiguration.java` | OBS-Q1 |
| `zipkin-server/src/main/java/zipkin2/server/internal/prometheus/ZipkinPrometheusMetricsConfiguration.java` | OBS-Q2, OBS-Q3 |
| `zipkin-server/src/main/java/zipkin2/server/internal/MicrometerCollectorMetrics.java` | OBS-Q2, OBS-Q3, DATA-Q7 |
| `zipkin-server/src/main/java/zipkin2/server/internal/health/ZipkinHealthController.java` | API-Q1 |
| `zipkin-server/src/main/java/zipkin2/server/internal/elasticsearch/BasicCredentials.java` | AUTH-Q5 |
| `zipkin/src/main/java/zipkin2/Span.java` | API-Q4, DATA-Q1, DISC-Q2, DISC-Q3 |
| `zipkin/src/main/java/zipkin2/Endpoint.java` | DISC-Q2 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/test.yml` | ENG-Q2, DISC-Q1 |
| `.github/workflows/deploy.yml` | ENG-Q3 |
| `.github/workflows/security.yml` | ENG-Q2 |
| `.github/workflows/docker_push.yml` | ENG-Q3 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `docker/Dockerfile` | ENG-Q1, ENG-Q3 |
| `docker/examples/docker-compose.yml` | HITL-Q3 |
| `docker/examples/docker-compose-prometheus.yml` | OBS-Q2 |
| `docker/examples/` (15 compose files) | HITL-Q3 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `zipkin-server/src/main/resources/zipkin-server-shared.yml` | AUTH-Q1, AUTH-Q5, AUTH-Q6, AUTH-Q7, STATE-Q5, OBS-Q1, DATA-Q2, DATA-Q6 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `pom.xml` | API-Q2, ENG-Q2 |
| `zipkin-server/pom.xml` | API-Q2 |
| `zipkin-lens/package.json` | Step 1 (context) |

### Documentation
| File | Questions Referenced |
|------|---------------------|
| `README.md` | API-Q1, API-Q2, DISC-Q3 |
| `zipkin-server/README.md` | API-Q1, API-Q2, AUTH-Q5 |

### Test Files (Referenced but not modified)
| File | Questions Referenced |
|------|---------------------|
| `zipkin-server/src/test/java/zipkin2/server/internal/ITZipkinServer.java` | ENG-Q2, ENG-Q4 |
| `zipkin-server/src/test/java/zipkin2/server/internal/ITZipkinGrpcCollector.java` | ENG-Q4 |
| `zipkin-server/src/test/java/zipkin2/server/internal/ITZipkinServerCORS.java` | ENG-Q4 |
| `zipkin-server/src/test/java/zipkin2/server/internal/ITZipkinServerTimeout.java` | ENG-Q4 |
| `zipkin-server/src/test/java/zipkin2/server/internal/ITZipkinServerSsl.java` | ENG-Q4 |
