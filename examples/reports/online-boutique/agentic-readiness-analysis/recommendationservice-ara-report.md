# Agentic Readiness Analysis Report

**Target**: services/microservices-demo/src/recommendationservice
**Date**: 2026-04-16
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**Repository Type**: application
**Service Archetype**: data-gateway (user-provided)
**Agent Scope**: read-only
**Priority**: P1
**Tags**: python, grpc, ml, recommendations
**Context**: Python gRPC service providing product recommendations based on cart contents.

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 2 | **RISKs**: 17 | **INFOs**: 13

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days. The two blockers (AUTH-Q1: no machine identity authentication; DATA-Q1: user_id is PII-candidate) must be resolved before any agent can safely call this service. The 17 RISKs are manageable with compensating controls once blockers are cleared.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 2 |
| RISK | 17 |
| INFO | 13 |
| N/A | 0 |
| Not Evaluated (extended) | 11 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 8
**Extended Questions Not Triggered**: 11
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: data-gateway (user-provided)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: The gRPC server is created via `grpc.server(futures.ThreadPoolExecutor(max_workers=10))` in `recommendation_server.py` (line 117) with `server.add_insecure_port('[::]:'+port)` (line 123). No authentication interceptor, no TLS, no credential verification. Istio AuthorizationPolicies are disabled (`authorizationPolicies.create: false`). NetworkPolicies disabled. Any network-reachable client can call `ListRecommendations` without credentials.
- **Gap**: No machine identity authentication at any layer. Agents cannot be identified or attributed.
- **Remediation**:
  - **Immediate**: Enable Istio AuthorizationPolicies (`authorizationPolicies.create: true`) for mTLS-based caller identity.
  - **Target State**: Mesh-level mTLS with per-caller AuthorizationPolicy rules. Agent-specific K8s ServiceAccounts. Application-layer gRPC interceptor for defense-in-depth.
  - **Estimated Effort**: Low (Helm value change), Medium (application-layer interceptor)
  - **Dependencies**: AUTH-Q2, AUTH-Q6
- **Evidence**: `recommendation_server.py` (line 117, `grpc.server()`; line 123, `add_insecure_port`), `helm-chart/values.yaml` (`authorizationPolicies.create: false`)

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: The `ListRecommendationsRequest` proto message contains `user_id` (string) and `product_ids` (repeated string). The `user_id` field is a PII-candidate — it identifies a specific user and their browsing/cart behavior. Combined with `product_ids`, it reveals user shopping preferences. The `client.py` test client sends `user_id="test"` and `product_ids=["test"]`. No formal data classification exists. The recommendation service calls `productcatalog` to get the full product list and filters based on user's current cart — this creates a user behavior profile.
- **Gap**: PII-candidate data (`user_id`) processed without formal classification. User behavior profiling (cart contents → recommendations) without privacy controls. No `DATA_CLASSIFICATION.md` in service directory.
- **Remediation**:
  - **Immediate**: Create `DATA_CLASSIFICATION.md` documenting that the service processes PII-candidate data (`user_id`) and user behavior data (product preferences). Classify `user_id` as CONFIDENTIAL/PII.
  - **Target State**: Privacy-aware recommendation logic. User consent verification. Data minimization (hash user_id if full identity not needed).
  - **Estimated Effort**: Low (classification), Medium (privacy controls)
- **Evidence**: `recommendation_server.py` (line 73, `request.product_ids`; line 80, logs product_ids), `client.py` (line 37, `user_id="test"`), `proto/demo.proto` (ListRecommendationsRequest with `user_id`)

---

## RISKs — Proceed with Compensating Controls

### API-Q2: Machine-Readable API Specification

- **Severity**: RISK
- **Finding**: The service API is defined via generated protobuf stubs (`demo_pb2.py`, `demo_pb2_grpc.py`). The `RecommendationService` has a single RPC: `ListRecommendations`. Protobuf is machine-readable. No gRPC server reflection enabled. No OpenAPI or standalone spec.
- **Gap**: No standalone spec. No gRPC reflection for runtime discovery.
- **Compensating Controls**:
  - Proto stubs can generate client code for agent tool definitions
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Enable gRPC server reflection. Extract recommendation service proto into standalone file.
- **Evidence**: `demo_pb2_grpc.py` (generated stubs), `recommendation_server.py` (no reflection)

### API-Q3: Structured Error Responses

- **Severity**: RISK
- **Finding**: The `ListRecommendations` method has no explicit error handling. If `product_catalog_stub.ListProducts()` fails, the exception propagates unhandled to the gRPC framework which maps it to `UNKNOWN` status. No try/except blocks in the recommendation logic. No structured error responses, no retryable flags, no error code taxonomy.
- **Gap**: No error handling. Exceptions propagate as UNKNOWN gRPC status. Agents cannot distinguish between service errors and upstream (productcatalog) failures.
- **Compensating Controls**:
  - Wrap agent tool calls with client-side error classification
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add try/except blocks around `product_catalog_stub.ListProducts()`. Map exceptions to appropriate gRPC status codes (UNAVAILABLE for upstream failures, INTERNAL for logic errors).
- **Evidence**: `recommendation_server.py` (lines 70–82, ListRecommendations — no error handling)

### AUTH-Q2: Scoped Permissions (Least Privilege)

- **Severity**: RISK
- **Finding**: AuthorizationPolicies disabled. Helm template restricts callers to `frontend` service account on `/hipstershop.RecommendationService/ListRecommendations`, but not deployed.
- **Gap**: No caller restriction. No agent-specific permission scoping.
- **Compensating Controls**:
  - Enable AuthorizationPolicies to activate existing Helm template
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Enable `authorizationPolicies.create: true`. Create agent-specific service accounts.
- **Evidence**: `helm-chart/values.yaml`, `helm-chart/templates/recommendationservice.yaml`

### AUTH-Q3: Action-Level Authorization

- **Severity**: RISK
- **Finding**: No application-layer authorization. AuthorizationPolicy with per-path rules exists but disabled. Single RPC (`ListRecommendations`) is accessible to any caller.
- **Gap**: No action-level authorization.
- **Recommendation**: Enable AuthorizationPolicies. Implement gRPC interceptor for defense in depth.
- **Evidence**: `recommendation_server.py` (no auth), `helm-chart/values.yaml`

### AUTH-Q5: Credential Management

- **Severity**: RISK
- **Finding**: The service connects to `productcatalogservice` via `grpc.insecure_channel(catalog_addr)` (line 115). The `PRODUCT_CATALOG_SERVICE_ADDR` is read from environment variables. No secrets, no API keys, no Secrets Manager. The gRPC channel is insecure (no TLS).
- **Gap**: No credential management. Insecure gRPC channel to upstream service. No TLS on inter-service communication.
- **Compensating Controls**:
  - Istio mTLS (when enabled) provides transport encryption at the mesh layer
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Rely on Istio mTLS for inter-service encryption. If credentials are introduced, use K8s Secrets with external secrets operator.
- **Evidence**: `recommendation_server.py` (line 115, `grpc.insecure_channel(catalog_addr)`)

### AUTH-Q6: Immutable Audit Logging ⚡

- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: Logging uses `python-json-logger` via custom `logger.py` with JSON format including `timestamp`, `severity`, `name`, `message`. The `ListRecommendations` handler logs recommended product IDs. No principal attribution. Logs are ephemeral container stdout. No immutable storage. Tracing setup exists but is gated by `ENABLE_TRACING` env var (disabled in analysis context).
- **Gap**: No immutable audit trail. No principal attribution. No immutable log storage.
- **Compensating Controls**:
  - JSON structured logging provides basic analysis capability
  - OpenTelemetry instrumentation is integrated (gRPC client and server instrumentors)
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add caller identity to logs. Forward to immutable store. Enable tracing.
- **Evidence**: `recommendation_server.py` (line 80, logs product_ids), `logger.py` (JSON formatter)

### AUTH-Q7: Agent Identity Suspension

- **Severity**: RISK
- **Finding**: No agent identity suspension mechanism. AuthorizationPolicies disabled.
- **Gap**: No mechanism to suspend misbehaving agent.
- **Recommendation**: Implement agent-specific ServiceAccounts with AuthorizationPolicy-based suspension.
- **Evidence**: `helm-chart/values.yaml`, `helm-chart/templates/recommendationservice.yaml`

### STATE-Q2: Queryable Current State

- **Severity**: RISK
- **Finding**: The recommendation service is stateless — it fetches the full product catalog from `productcatalogservice` on every request, filters out products already in the user's cart, and returns a random sample. No recommendation history is stored. No way to query what was previously recommended to a user.
- **Gap**: No queryable state. No recommendation history. Agents cannot verify previous recommendations.
- **Recommendation**: Consider caching recommendations per user session for consistency.
- **Evidence**: `recommendation_server.py` (lines 70–82, fetches catalog on every call)

### STATE-Q4: Circuit Breakers and Resilience

- **Severity**: RISK
- **Finding**: The service calls `product_catalog_stub.ListProducts()` on every request with no circuit breaker, no retry logic, no timeout configuration, and no fallback. If productcatalogservice is down, every recommendation request fails. The gRPC channel is created once at startup with no reconnection logic. No graceful degradation.
- **Gap**: No resilience patterns for the productcatalog dependency. Single point of failure.
- **Compensating Controls**:
  - K8s health probes detect pod-level failures
  - Istio sidecar can provide retry and timeout policies
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add circuit breaker for productcatalog calls. Implement timeout on `ListProducts()`. Add fallback (e.g., return empty recommendations on upstream failure).
- **Evidence**: `recommendation_server.py` (line 73, `product_catalog_stub.ListProducts()` — no resilience)

### DATA-Q3: Selective Query Support

- **Severity**: RISK
- **Finding**: `ListRecommendations` returns up to 5 product IDs (hardcoded `max_responses = 5`). The service fetches the ENTIRE product catalog on every request (`product_catalog_stub.ListProducts(demo_pb2.Empty())`), filters, and samples. No pagination, no filtering parameters beyond `product_ids` exclusion. The full catalog fetch is inefficient and unbounded.
- **Gap**: Full catalog fetch on every request. No pagination. Hardcoded response limit.
- **Compensating Controls**:
  - Hardcoded max_responses=5 limits response size
  - Product catalog is small in the demo (9 products)
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `max_results` parameter to `ListRecommendationsRequest`. Implement catalog caching to avoid full fetch per request.
- **Evidence**: `recommendation_server.py` (line 71, `max_responses = 5`; line 73, full catalog fetch)

### DATA-Q4: System of Record Designations

- **Severity**: RISK
- **Finding**: The recommendation service is not a system of record. It generates recommendations dynamically from the product catalog. No recommendation history, no user preference storage, no model state.
- **Gap**: No system of record designation. Recommendations are ephemeral.
- **Recommendation**: If recommendation quality tracking is needed, implement recommendation logging with user_id correlation.
- **Evidence**: `recommendation_server.py` (dynamic generation, no persistence)

### DATA-Q5: Temporal Metadata and Freshness

- **Severity**: RISK
- **Finding**: `ListRecommendationsResponse` contains only `product_ids` (repeated string). No timestamp, no `generated_at`, no catalog freshness indicator. Agents cannot determine when recommendations were generated or whether the underlying catalog has changed.
- **Gap**: No temporal metadata. No freshness signaling.
- **Recommendation**: Add `generated_at` timestamp and `catalog_version` to response.
- **Evidence**: `demo_pb2.py` (ListRecommendationsResponse — product_ids only)

### OBS-Q1: Distributed Tracing and Structured Logging

- **Severity**: RISK
- **Finding**: OpenTelemetry instrumentation is integrated — `GrpcInstrumentorClient` and `GrpcInstrumentorServer` are initialized, and OTLP exporter is configured when `ENABLE_TRACING == "1"`. However, tracing is disabled in the analysis context. JSON structured logging via `python-json-logger`. Logs lack trace correlation IDs when tracing is disabled.
- **Gap**: Tracing disabled. Logs lack trace correlation. OpenTelemetry is integrated but inactive.
- **Compensating Controls**:
  - OpenTelemetry SDK is already integrated — enabling requires only env var change
  - JSON structured logging provides basic analysis
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Enable tracing (`ENABLE_TRACING: "1"`). The OpenTelemetry integration is already implemented.
- **Evidence**: `recommendation_server.py` (lines 100–112, OpenTelemetry setup), `logger.py` (JSON formatter)

### OBS-Q2: Alerting on Error Rates and Latency

- **Severity**: RISK
- **Finding**: No alerting configuration. gRPC health probes (readiness and liveness on port 8080) exist but no error rate or latency alerting. No custom metrics.
- **Gap**: No alerting on error rates or latency.
- **Recommendation**: Configure Prometheus alerting rules for ListRecommendations error rates and p99 latency.
- **Evidence**: `helm-chart/templates/recommendationservice.yaml` (health probes only)

### DISC-Q1: Schema Versioning and API Contracts

- **Severity**: RISK
- **Finding**: Proto uses `package hipstershop` with no version suffix. No `buf.yaml`. No breaking change detection. No contract tests.
- **Gap**: No proto versioning. No breaking change detection.
- **Recommendation**: Add version suffix. Integrate `buf breaking` into CI.
- **Evidence**: `demo_pb2.py` (generated from `package hipstershop`), no `buf.yaml`

### ENG-Q1: Infrastructure Governance for Agent-Facing Surface

- **Severity**: RISK
- **Finding**: Helm charts and Terraform with PR-based review. No drift detection.
- **Gap**: No drift detection.
- **Recommendation**: Implement GitOps with ArgoCD or Flux.
- **Evidence**: `helm-chart/templates/recommendationservice.yaml`, `helm-chart/values.yaml`

### ENG-Q2: CI/CD with API Contract Testing

- **Severity**: RISK
- **Finding**: CI/CD exists via GitHub Actions and Cloud Build. The recommendation service has no test files. No unit tests, no integration tests, no contract tests. No proto compatibility checks.
- **Gap**: No tests at all. No API contract testing.
- **Recommendation**: Add unit tests for recommendation logic. Add gRPC integration tests. Integrate `buf breaking`.
- **Evidence**: `src/recommendationservice/` (no test files), `.github/workflows/ci-pr.yaml`

### ENG-Q4: API Test Coverage

- **Severity**: RISK
- **Finding**: No automated tests. No test files in the service directory. The `client.py` is a manual test client, not an automated test. CI does not run any recommendation service tests.
- **Gap**: Zero test coverage.
- **Recommendation**: Add unit tests for recommendation filtering and sampling logic. Add gRPC integration tests.
- **Evidence**: `src/recommendationservice/` (no test files), `client.py` (manual test client)

### ENG-Q5: Encryption at Rest for Agent-Accessible Data

- **Severity**: RISK
- **Finding**: No persistent data. Recommendations generated dynamically from product catalog. User_id and product_ids exist only in-memory during request processing. Log output includes product_ids but not user_id in the current implementation.
- **Gap**: No persistent data to encrypt. Log storage encryption depends on K8s node config.
- **Recommendation**: Ensure user_id is not logged. Enable node-level disk encryption.
- **Evidence**: `recommendation_server.py` (line 80, logs product_ids), `logger.py`

---

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO
- **Finding**: gRPC API with single RPC: `ListRecommendations(ListRecommendationsRequest) returns (ListRecommendationsResponse)`. Well-defined proto interface.
- **Implication**: Agent-consumable gRPC interface.
- **Recommendation**: No action required.
- **Evidence**: `demo_pb2_grpc.py` (RecommendationService), `recommendation_server.py`

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: `ListRecommendations` is a read-only RPC. However, it uses `random.sample()` to select recommendations, so repeated calls with the same input may return different results. Not idempotent in the strict sense, but read-only.
- **Implication**: Non-deterministic read. Agents may get different recommendations on retry.
- **Recommendation**: No action required. Document non-deterministic behavior for agent consumers.
- **Evidence**: `recommendation_server.py` (line 77, `random.sample()`)

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: Responses are Protocol Buffers over gRPC. `ListRecommendationsResponse` contains `product_ids` (repeated string). Strongly typed.
- **Implication**: Protobuf is efficient for machine consumption.
- **Recommendation**: Consider gRPC-JSON transcoding if agents require JSON.
- **Evidence**: `demo_pb2.py` (ListRecommendationsResponse)

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limiting. No documentation. Each request triggers a full product catalog fetch from productcatalogservice.
- **Implication**: Agents calling at machine speed will generate proportional load on productcatalogservice.
- **Recommendation**: Implement rate limiting. Cache product catalog to reduce upstream load.
- **Evidence**: `recommendation_server.py` (full catalog fetch per request)

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: INFO
- **Finding**: `ListRecommendationsRequest` contains `user_id` but the service does not validate or propagate this identity. The `user_id` is used only to correlate with cart contents (via `product_ids`). No JWT, no token exchange, no identity verification.
- **Implication**: `user_id` is accepted without verification. An agent could request recommendations for any user.
- **Recommendation**: Validate `user_id` against caller identity when AUTH-Q1 is resolved.
- **Evidence**: `recommendation_server.py` (line 73, uses request.product_ids but not user_id for logic)

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Read-only service. No write operations. No state mutations. Compensation not applicable.
- **Gap**: N/A — read-only.
- **Recommendation**: No action required.
- **Evidence**: `recommendation_server.py` (read-only ListRecommendations)

### STATE-Q5: Rate Limiting and Throttling

- **Severity**: INFO
- **Finding**: No rate limiting. Resource limits (CPU: 200m, memory: 450Mi). ThreadPoolExecutor with max_workers=10 provides a concurrency ceiling.
- **Implication**: ThreadPoolExecutor limits concurrent requests to 10. Beyond that, requests queue.
- **Recommendation**: Consider explicit rate limiting beyond thread pool ceiling.
- **Evidence**: `recommendation_server.py` (line 117, max_workers=10), `helm-chart/values.yaml`

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Read-only service. No state mutations. Blast radius limited to upstream load on productcatalogservice.
- **Gap**: N/A for read-only scope.
- **Recommendation**: No action for current scope.
- **Evidence**: `recommendation_server.py`

### HITL-Q3: Sandbox/Staging Environment

- **Severity**: INFO
- **Finding**: Staging GKE cluster with per-PR namespaces. Full stack via Skaffold.
- **Gap**: No dedicated agent testing documentation.
- **Recommendation**: Document staging environment for agent testing.
- **Evidence**: `.github/workflows/ci-pr.yaml`, `cloudbuild.yaml`

### DATA-Q2: Data Residency and Sovereignty ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: User_id and product_ids in-memory only. Not persisted. Processing region determined by GKE cluster.
- **Gap**: No data residency documentation.
- **Recommendation**: Document processing region for GDPR compliance (user_id is PII-candidate).
- **Evidence**: `recommendation_server.py` (in-memory), `helm-chart/values.yaml`

### DATA-Q6: PII Redaction in Logs

- **Severity**: INFO
- **Finding**: Logs include recommended product_ids but not user_id. Product IDs are not PII. Current logging does not expose user identity.
- **Gap**: None — user_id not logged.
- **Recommendation**: Maintain current practice. Ensure user_id is never added to logs.
- **Evidence**: `recommendation_server.py` (line 80, logs product_ids only)

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: Recommendations depend on product catalog quality. The service fetches the full catalog and randomly samples. No quality scoring, no relevance ranking, no freshness checking of catalog data.
- **Implication**: Recommendation quality is random — no ML model, no collaborative filtering.
- **Recommendation**: Document that recommendations are random samples, not ML-driven.
- **Evidence**: `recommendation_server.py` (random.sample for selection)

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Proto field names are human-readable: `user_id`, `product_ids`. No legacy abbreviations.
- **Gap**: None.
- **Recommendation**: No action required.
- **Evidence**: `demo_pb2.py` (ListRecommendationsRequest, ListRecommendationsResponse)

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No formal data catalog. Proto file as schema documentation.
- **Gap**: No formal metadata layer.
- **Recommendation**: No action required.
- **Evidence**: `demo_pb2.py`

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No custom metrics. No recommendation click-through tracking, no relevance scoring, no A/B testing metrics.
- **Gap**: No business outcome measurement for recommendations.
- **Recommendation**: Implement recommendation click-through and conversion metrics.
- **Evidence**: `recommendation_server.py` (no metrics)

### ENG-Q3: Rollback Capability

- **Severity**: INFO
- **Finding**: Helm rollback available. K8s rolling update. No automated rollback.
- **Gap**: No automated rollback triggers.
- **Recommendation**: Consider Flagger or Argo Rollouts.
- **Evidence**: `helm-chart/Chart.yaml`, `helm-chart/templates/recommendationservice.yaml`

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: gRPC API with `ListRecommendations` RPC. Well-defined proto interface.
- **Gap**: Monolithic proto shared across all services.
- **Recommendation**: Extract recommendation service proto into standalone file.
- **Evidence**: `demo_pb2_grpc.py`, `recommendation_server.py`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK
- **Finding**: Proto IDL is machine-readable. No gRPC reflection. Monolithic proto.
- **Gap**: No standalone spec. No runtime discovery.
- **Recommendation**: Enable gRPC reflection. Extract standalone proto.
- **Evidence**: `demo_pb2_grpc.py`, `recommendation_server.py` (no reflection)

#### API-Q3: Structured Error Responses
- **Severity**: RISK
- **Finding**: No error handling in ListRecommendations. Exceptions propagate as UNKNOWN status.
- **Gap**: No rich error model. No error handling.
- **Recommendation**: Add try/except. Map to gRPC status codes.
- **Evidence**: `recommendation_server.py` (lines 70–82)

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Read-only RPC. Non-deterministic due to random.sample().
- **Gap**: Non-deterministic reads. Not a write concern.
- **Recommendation**: Document non-deterministic behavior.
- **Evidence**: `recommendation_server.py` (line 77, random.sample)

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: Protocol Buffers over gRPC. Strongly typed.
- **Gap**: Binary protobuf may need transcoding.
- **Recommendation**: Consider gRPC-JSON transcoding.
- **Evidence**: `demo_pb2.py`

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered.
- **Trigger**: Service has operations >30s OR long-running workflows
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered. data-gateway archetype — read-only, no state changes.
- **Trigger**: Service has state changes (stateful-crud, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limiting. Each request triggers full catalog fetch.
- **Gap**: No rate limit feedback. Amplified upstream load.
- **Recommendation**: Implement rate limiting. Cache catalog.
- **Evidence**: `recommendation_server.py`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: `grpc.server()` with `add_insecure_port`. AuthorizationPolicies disabled. No auth.
- **Gap**: No machine identity authentication.
- **Recommendation**: Enable Istio AuthorizationPolicies. Add gRPC interceptor.
- **Evidence**: `recommendation_server.py` (lines 117, 123), `helm-chart/values.yaml`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK
- **Finding**: AuthorizationPolicies disabled. Helm template restricts to frontend but not deployed.
- **Gap**: No caller restriction.
- **Recommendation**: Enable AuthorizationPolicies. Create agent-specific service accounts.
- **Evidence**: `helm-chart/values.yaml`, `helm-chart/templates/recommendationservice.yaml`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK
- **Finding**: No authorization. Single RPC accessible to any caller.
- **Gap**: No action-level authorization.
- **Recommendation**: Enable AuthorizationPolicies.
- **Evidence**: `recommendation_server.py`, `helm-chart/values.yaml`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: user_id in request but not validated or propagated. No JWT, no token exchange.
- **Gap**: user_id accepted without verification.
- **Recommendation**: Validate user_id against caller identity.
- **Evidence**: `recommendation_server.py` (line 73)

#### AUTH-Q5: Credential Management
- **Severity**: RISK
- **Finding**: Insecure gRPC channel to productcatalogservice. No secrets. No TLS.
- **Gap**: No credential management. Insecure inter-service communication.
- **Recommendation**: Rely on Istio mTLS. Use external secrets operator if needed.
- **Evidence**: `recommendation_server.py` (line 115, `grpc.insecure_channel`)

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: JSON structured logging. No principal attribution. No immutable storage. Tracing gated by env var.
- **Gap**: No immutable audit trail.
- **Recommendation**: Add principal attribution. Forward to immutable store. Enable tracing.
- **Evidence**: `recommendation_server.py` (line 80), `logger.py`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK
- **Finding**: No suspension mechanism. AuthorizationPolicies disabled.
- **Gap**: No mechanism to suspend agent.
- **Recommendation**: Implement agent-specific ServiceAccounts.
- **Evidence**: `helm-chart/values.yaml`, `helm-chart/templates/recommendationservice.yaml`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Read-only. No write operations. Compensation not applicable.
- **Gap**: N/A.
- **Recommendation**: No action required.
- **Evidence**: `recommendation_server.py`

#### STATE-Q2: Queryable Current State
- **Severity**: RISK
- **Finding**: Stateless. No recommendation history. Full catalog fetched per request.
- **Gap**: No queryable state.
- **Recommendation**: Consider caching recommendations per session.
- **Evidence**: `recommendation_server.py` (lines 70–82)

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered. agent_scope is read-only.
- **Trigger**: agent_scope is write-enabled AND service has persistent state
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK
- **Finding**: No circuit breaker for productcatalog dependency. No retry, no timeout, no fallback.
- **Gap**: Single point of failure on productcatalog.
- **Recommendation**: Add circuit breaker. Implement timeout and fallback.
- **Evidence**: `recommendation_server.py` (line 73, no resilience)

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: INFO
- **Finding**: No rate limiting. ThreadPoolExecutor max_workers=10 provides concurrency ceiling.
- **Gap**: No explicit rate limiting.
- **Recommendation**: Consider explicit rate limiting.
- **Evidence**: `recommendation_server.py` (line 117, max_workers=10)

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Read-only. Blast radius limited to upstream load.
- **Gap**: N/A for read-only.
- **Recommendation**: No action.
- **Evidence**: `recommendation_server.py`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered. Service is P1, not P0.
- **Trigger**: Service is P0 priority OR is on the critical path
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered. agent_scope is read-only.
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered. agent_scope is read-only.
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: INFO
- **Finding**: Staging GKE cluster with per-PR namespaces.
- **Gap**: No agent testing documentation.
- **Recommendation**: Document staging environment.
- **Evidence**: `.github/workflows/ci-pr.yaml`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: user_id is PII-candidate. Combined with product_ids reveals user behavior. No classification.
- **Gap**: PII-candidate data without classification.
- **Recommendation**: Create DATA_CLASSIFICATION.md. Classify user_id as CONFIDENTIAL/PII.
- **Evidence**: `recommendation_server.py`, `demo_pb2.py` (ListRecommendationsRequest)

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: In-memory only. Not persisted.
- **Gap**: No data residency documentation.
- **Recommendation**: Document processing region.
- **Evidence**: `recommendation_server.py`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK
- **Finding**: Full catalog fetch per request. Hardcoded max_responses=5. No pagination.
- **Gap**: Unbounded upstream fetch. No pagination.
- **Recommendation**: Add max_results parameter. Cache catalog.
- **Evidence**: `recommendation_server.py` (lines 71, 73)

#### DATA-Q4: System of Record Designations
- **Severity**: RISK
- **Finding**: Not a system of record. Dynamic generation. No persistence.
- **Gap**: No system of record.
- **Recommendation**: Implement recommendation logging if tracking needed.
- **Evidence**: `recommendation_server.py`

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK
- **Finding**: Response contains only product_ids. No timestamps. No freshness indicator.
- **Gap**: No temporal metadata.
- **Recommendation**: Add generated_at timestamp.
- **Evidence**: `demo_pb2.py` (ListRecommendationsResponse)

#### DATA-Q6: PII Redaction in Logs
- **Severity**: INFO
- **Finding**: Logs product_ids only. user_id not logged.
- **Gap**: None.
- **Recommendation**: Maintain current practice.
- **Evidence**: `recommendation_server.py` (line 80)

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: Random sampling. No quality scoring. Depends on catalog quality.
- **Gap**: No quality assurance beyond catalog availability.
- **Recommendation**: Document random sampling behavior.
- **Evidence**: `recommendation_server.py` (random.sample)

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK
- **Finding**: `package hipstershop` — no version. No buf.yaml. No breaking change detection.
- **Gap**: No proto versioning.
- **Recommendation**: Add version suffix. Integrate buf breaking.
- **Evidence**: `demo_pb2.py`, no `buf.yaml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Human-readable: user_id, product_ids.
- **Gap**: None.
- **Recommendation**: No action required.
- **Evidence**: `demo_pb2.py`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal data catalog. Proto as schema documentation.
- **Gap**: No formal metadata layer.
- **Recommendation**: No action required.
- **Evidence**: `demo_pb2.py`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK
- **Finding**: OpenTelemetry integrated but disabled. JSON structured logging. No trace correlation.
- **Gap**: Tracing disabled. No trace correlation.
- **Recommendation**: Enable tracing. OpenTelemetry already integrated.
- **Evidence**: `recommendation_server.py` (lines 100–112), `logger.py`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK
- **Finding**: No alerting. Health probes only.
- **Gap**: No alerting.
- **Recommendation**: Configure Prometheus alerting.
- **Evidence**: `helm-chart/templates/recommendationservice.yaml`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom metrics. No recommendation quality tracking.
- **Gap**: No business outcome measurement.
- **Recommendation**: Implement click-through and conversion metrics.
- **Evidence**: `recommendation_server.py`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK
- **Finding**: Helm charts and Terraform with PR review. No drift detection.
- **Gap**: No drift detection.
- **Recommendation**: Implement GitOps.
- **Evidence**: `helm-chart/templates/recommendationservice.yaml`, `helm-chart/values.yaml`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK
- **Finding**: No tests. No contract tests. No proto checks.
- **Gap**: Zero test coverage.
- **Recommendation**: Add unit and integration tests.
- **Evidence**: `src/recommendationservice/` (no test files)

#### ENG-Q3: Rollback Capability
- **Severity**: INFO
- **Finding**: Helm rollback available. No automated rollback.
- **Gap**: No automated rollback.
- **Recommendation**: Consider Flagger or Argo Rollouts.
- **Evidence**: `helm-chart/Chart.yaml`, `helm-chart/templates/recommendationservice.yaml`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK
- **Finding**: No automated tests. client.py is manual test client only.
- **Gap**: Zero test coverage.
- **Recommendation**: Add unit tests for recommendation logic.
- **Evidence**: `src/recommendationservice/` (no test files), `client.py` (manual)

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: RISK
- **Finding**: No persistent data. In-memory only. Log encryption depends on K8s node config.
- **Gap**: No persistent data to encrypt.
- **Recommendation**: Ensure user_id not logged. Enable node-level encryption.
- **Evidence**: `recommendation_server.py` (line 80), `logger.py`

---

## Evidence Index

### Infrastructure as Code
| File | Questions Referenced |
|------|---------------------|
| `helm-chart/templates/recommendationservice.yaml` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q7, OBS-Q2, ENG-Q1, ENG-Q3, STATE-Q5 |
| `helm-chart/values.yaml` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q5, AUTH-Q6, AUTH-Q7, OBS-Q1, STATE-Q5, ENG-Q1 |

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `recommendation_server.py` | API-Q1, API-Q2, API-Q3, API-Q4, AUTH-Q1, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q6, STATE-Q1, STATE-Q2, STATE-Q4, STATE-Q5, DATA-Q1, DATA-Q3, DATA-Q6, OBS-Q1, OBS-Q3, ENG-Q4, ENG-Q5 |
| `logger.py` | AUTH-Q6, OBS-Q1, DATA-Q6 |
| `client.py` | DATA-Q1, ENG-Q4 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `demo_pb2.py` / `demo_pb2_grpc.py` | API-Q1, API-Q2, API-Q4, API-Q5, AUTH-Q4, DATA-Q1, DATA-Q2, DATA-Q5, DISC-Q1, DISC-Q2, DISC-Q3 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/ci-pr.yaml` | HITL-Q3, DISC-Q1, ENG-Q2, ENG-Q4 |
| `cloudbuild.yaml` | ENG-Q2, ENG-Q3 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `Dockerfile` | AUTH-Q5 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `requirements.txt` | API-Q2, OBS-Q1 |