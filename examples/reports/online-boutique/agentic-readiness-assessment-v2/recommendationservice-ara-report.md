# Agentic Readiness Assessment Report

**Target**: services/microservices-demo/src/recommendationservice
**Date**: 2026-04-16
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Service Archetype**: data-gateway (user-provided)
**Archetype Justification**: Reads product catalog via gRPC call to productcatalogservice, filters products based on cart contents, and returns filtered recommendations. Minimal business logic (random sampling). Read-heavy data access layer over the product catalog.
**Agent Scope**: read-only
**Priority**: P1
**Tags**: python, grpc, ml, recommendations
**Context**: Python gRPC service providing product recommendations based on cart contents.

---

## Readiness Profile: Pilot-Ready

**BLOCKERs**: 0 | **RISKs**: 11 | **INFOs**: 25

Supervised pilot with: (1) human approval gates on irreversible actions, (2) agent limited to low-blast-radius operations, (3) compensating controls for each open RISK, (4) remediation timeline before expanding scope.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 0 |
| RISK | 11 |
| INFO | 25 |
| N/A | 0 |
| Not Evaluated (extended) | 7 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 12
**Extended Questions Not Triggered**: 7
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: data-gateway (user-provided)

---

## BLOCKERs — Must Resolve Before Agent Deployment

No BLOCKERs identified.

---

## RISKs — Proceed with Compensating Controls

### API-Q3: Structured Error Responses
- **Severity**: RISK
- **Finding**: `ListRecommendations` in `recommendation_server.py` has no explicit error handling. If `product_catalog_stub.ListProducts` fails, the gRPC framework propagates the upstream error directly. No try/except block, no structured error response, no retryable boolean. An agent receiving an error cannot determine whether the failure is in recommendationservice or productcatalogservice.
- **Gap**: No error handling. Upstream errors propagated without classification or enrichment.
- **Compensating Controls**:
  - Wrap agent tool calls with client-side error classification
  - Add try/except with structured error responses
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add try/except around `product_catalog_stub.ListProducts` call. Return `UNAVAILABLE` for upstream failures (retryable) and `INTERNAL` for local failures (terminal).
- **Evidence**: `src/recommendationservice/recommendation_server.py` (ListRecommendations method)

### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicy restricts callers to `frontend` service account principal on `/hipstershop.RecommendationService/ListRecommendations`. Single caller, single RPC. No agent-specific service accounts. No per-caller differentiation.
- **Gap**: No agent-specific service accounts.
- **Compensating Controls**:
  - AuthorizationPolicy restricts to single caller (frontend)
  - Define agent-specific K8s ServiceAccounts with per-RPC rules
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create agent-specific service accounts if agent needs direct access to recommendations.
- **Evidence**: `helm-chart/templates/recommendationservice.yaml` (AuthorizationPolicy), `helm-chart/values.yaml`

### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicy defines per-path rules. Python gRPC server uses `grpc.server(futures.ThreadPoolExecutor(...))` with no interceptor for authorization. All calls reaching the application are accepted.
- **Gap**: No application-layer authorization.
- **Compensating Controls**:
  - Istio sidecar injection ensures mesh-level enforcement
  - Network policies restrict ingress to frontend only
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement gRPC server interceptor for authorization as defense in depth.
- **Evidence**: `src/recommendationservice/recommendation_server.py`, `helm-chart/templates/recommendationservice.yaml`

### AUTH-Q5: Credential Management
- **Severity**: RISK
- **Finding**: No secrets or credentials used directly. Connection to productcatalogservice uses `grpc.insecure_channel(catalog_addr)` — Istio sidecar handles mTLS. `PRODUCT_CATALOG_SERVICE_ADDR` is a service address, not a credential. No Secrets Manager or Vault integration.
- **Gap**: No credential management framework. `grpc.insecure_channel` relies entirely on Istio for transport security.
- **Compensating Controls**:
  - Istio mTLS encrypts inter-service communication
  - K8s ServiceAccount provides pod identity
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Maintain Istio-based transport security. Adopt external secrets operator if credentials are introduced.
- **Evidence**: `src/recommendationservice/recommendation_server.py` (`grpc.insecure_channel`), `helm-chart/templates/recommendationservice.yaml`

### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK
- **Archetype-Calibrated**: data-gateway with PII-CANDIDATE user_id — evaluated as RISK
- **Finding**: Python JSON logger outputs operational messages. `ListRecommendations` logs product IDs returned: `logger.info("[Recv ListRecommendations] product_ids={}".format(prod_list))`. No principal attribution. No user_id logging (the `request.user_id` field is not logged). Logs are ephemeral container stdout. OTel tracing configured with both `GrpcInstrumentorClient` and `GrpcInstrumentorServer`.
- **Gap**: No immutable audit trail. No principal attribution. user_id (PII-CANDIDATE) not tracked in logs.
- **Compensating Controls**:
  - OTel tracing provides request-level correlation for both client and server calls
  - Forward container stdout to immutable log aggregation
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add structured audit logging with caller identity and user_id for recommendation access attribution. Forward to immutable store.
- **Evidence**: `src/recommendationservice/recommendation_server.py` (logger.info with prod_list), `src/recommendationservice/logger.py`

### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK
- **Finding**: `ListRecommendations` calls `product_catalog_stub.ListProducts(demo_pb2.Empty())` synchronously with no timeout, no retry, no circuit breaker. If productcatalogservice is slow or unavailable, recommendationservice blocks indefinitely. No `grpc.channel_ready_future` timeout. No deadline propagation from the incoming request context.
- **Gap**: No circuit breaker, no timeout, no retry logic for the productcatalogservice dependency. Single point of failure.
- **Compensating Controls**:
  - Istio provides mesh-level retry and timeout policies
  - Add gRPC deadline to the outbound call
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add gRPC deadline to `ListProducts` call: `product_catalog_stub.ListProducts(demo_pb2.Empty(), timeout=5)`. Implement circuit breaker pattern or use Istio DestinationRule with outlier detection.
- **Evidence**: `src/recommendationservice/recommendation_server.py` (product_catalog_stub.ListProducts call with no timeout)

### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK
- **Finding**: EnvoyFilter rate limiting targets frontend only. No rate limiting on recommendationservice. No application-level rate limiting. HPA provides auto-scaling (1–5 replicas at 70% CPU). ThreadPoolExecutor(max_workers=10) provides implicit concurrency cap. Each recommendation request triggers a full product catalog fetch — amplification risk.
- **Gap**: No rate limiting. Each request amplifies to a full catalog fetch from productcatalogservice.
- **Compensating Controls**:
  - ThreadPoolExecutor limits concurrent processing
  - HPA provides elastic capacity
  - Extend EnvoyFilter to include recommendationservice
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add EnvoyFilter targeting recommendationservice. Consider caching product catalog to reduce amplification.
- **Evidence**: `istio-manifests/rate-limit.yaml`, `kubernetes-manifests/hpa.yaml`, `src/recommendationservice/recommendation_server.py`

### DATA-Q3: Selective Query Support
- **Severity**: RISK
- **Finding**: `ListRecommendations` fetches the entire product catalog via `product_catalog_stub.ListProducts(demo_pb2.Empty())` on every request, then filters client-side. No pagination, no server-side filtering, no limit parameter. Returns up to `max_responses = 5` recommendations but fetches all products to do so.
- **Gap**: No selective query. Full catalog fetch on every request. Unbounded upstream query amplification.
- **Compensating Controls**:
  - `max_responses = 5` caps the response size
  - Cache product catalog locally to reduce upstream calls
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Cache the product catalog with TTL. Add pagination support to ListRecommendations if the catalog grows large.
- **Evidence**: `src/recommendationservice/recommendation_server.py` (ListProducts call, max_responses=5)

### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK
- **Finding**: Recommendations are computed from a real-time product catalog fetch — always fresh but with no freshness indicator in the response. `ListRecommendationsResponse` contains only `product_ids` — no timestamp, no cache age, no freshness signal. If caching is added (see DATA-Q3), staleness becomes a concern.
- **Gap**: No freshness metadata in responses. Agent cannot determine recommendation age.
- **Compensating Controls**:
  - Real-time computation ensures freshness (no caching currently)
  - Add `computed_at` timestamp to response
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `computed_at` timestamp to `ListRecommendationsResponse`. Critical if caching is implemented.
- **Evidence**: `protos/demo.proto` (ListRecommendationsResponse), `src/recommendationservice/recommendation_server.py`

### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK
- **Finding**: CI exists (Cloud Build + GitHub Actions). Proto versioned (`hipstershop.v1`). `buf.yaml` configured. `buf breaking` not in CI. No recommendationservice-specific tests found. No contract tests.
- **Gap**: `buf breaking` not in CI. Zero test coverage.
- **Compensating Controls**:
  - Proto versioning provides implicit contract stability
  - Simple logic (filter + random sample) reduces untested-code risk
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `buf breaking` to CI. Add unit tests for recommendation filtering and sampling logic.
- **Evidence**: `cloudbuild.yaml`, `.github/workflows/ci-pr.yaml`, `protos/buf.yaml`

### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: RISK
- **Finding**: No persistent data store. Product catalog fetched in real-time from productcatalogservice. Recommendation results computed in-memory. If local caching is added (see DATA-Q3), cached product data and user_id associations would need encryption at rest.
- **Gap**: No encryption at rest framework. Not currently needed but required if caching is added.
- **Compensating Controls**:
  - No persistent data eliminates current encryption-at-rest risk
  - Istio mTLS encrypts data in transit
- **Remediation Timeline**: When caching is implemented
- **Recommendation**: Ensure encryption at rest if local product catalog cache is added.
- **Evidence**: `src/recommendationservice/recommendation_server.py`, `helm-chart/values.yaml`

---

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: gRPC interface in `protos/demo.proto` with `RecommendationService` defining a single `ListRecommendations` RPC. Proto uses versioned package `hipstershop.v1`. No explicit data classification comment on RecommendationService section (unlike other services), but `ListRecommendationsRequest.user_id` is a PII-CANDIDATE field. Implemented in `recommendation_server.py` with `RecommendationService` class.
- **Implication**: gRPC interface is documented. Single-RPC surface is simple for agent integration.
- **Recommendation**: Add data classification comment to RecommendationService section in proto (e.g., "Data Classification: INTERNAL / PII-CANDIDATE").
- **Evidence**: `protos/demo.proto`, `src/recommendationservice/recommendation_server.py`

### API-Q2: Machine-Readable API Specification
- **Severity**: INFO
- **Finding**: `protos/demo.proto` is machine-readable. Strongly typed with versioned package. `buf.yaml` provides linting and breaking change detection. Positive finding.
- **Implication**: Agent tool definitions can be auto-generated from proto.
- **Recommendation**: Consider enabling gRPC server reflection for runtime discovery.
- **Evidence**: `protos/demo.proto`, `protos/buf.yaml`

### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: `ListRecommendations` is read-only. It fetches the product catalog, filters, and returns random samples. No write side effects. Non-deterministic (random sampling) but no state mutations.
- **Implication**: Read-only operation. No idempotency concerns.
- **Recommendation**: No action needed.
- **Evidence**: `src/recommendationservice/recommendation_server.py`

### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: gRPC Protocol Buffers. `ListRecommendationsResponse` contains `repeated string product_ids`. Simple, well-typed response. Product IDs are opaque identifiers that can be resolved via productcatalogservice.
- **Implication**: Simple response format. Agent can use product_ids directly for downstream lookups.
- **Recommendation**: No action needed.
- **Evidence**: `protos/demo.proto`

### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit headers. EnvoyFilter rate limit headers only on frontend. Internal ClusterIP service.
- **Implication**: Agents cannot self-throttle.
- **Recommendation**: Extend EnvoyFilter rate limit headers when rate limiting is applied.
- **Evidence**: `istio-manifests/rate-limit.yaml`, `helm-chart/templates/recommendationservice.yaml`

### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: Istio AuthorizationPolicy enabled with mTLS. Callers restricted to `frontend` principal. Sidecars and network policies enabled. Python gRPC server uses `add_insecure_port` — Istio sidecar handles mTLS. Sidecar egress configured to allow productcatalogservice and OTel Collector.
- **Implication**: Machine identity authenticated at mesh layer. Egress scoped to required dependencies.
- **Recommendation**: No action needed.
- **Evidence**: `helm-chart/values.yaml`, `helm-chart/templates/recommendationservice.yaml`, `src/recommendationservice/recommendation_server.py`

### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Archetype-Calibrated**: data-gateway — downgraded to INFO
- **Finding**: No JWT parsing, no token exchange. `ListRecommendationsRequest` contains `user_id` (PII-CANDIDATE) and `product_ids` but no caller identity context. The `user_id` is used for filtering (exclude products already in cart) but not logged or propagated to the productcatalogservice call. Istio mTLS provides mesh-level caller identity.
- **Implication**: user_id is used for filtering only, not for authorization decisions. Identity propagation has lower priority for a read-only data-gateway.
- **Recommendation**: Propagate user_id context to audit logs when audit logging is implemented.
- **Evidence**: `src/recommendationservice/recommendation_server.py`, `protos/demo.proto`

### AUTH-Q7: Agent Identity Suspension
- **Severity**: INFO
- **Finding**: Istio AuthorizationPolicy and NetworkPolicy provide suspension mechanisms. Single-caller restriction (frontend) makes suspension straightforward.
- **Gap**: No automated suspension.
- **Recommendation**: Implement automated suspension if agent direct access is added.
- **Evidence**: `helm-chart/templates/recommendationservice.yaml`, `helm-chart/values.yaml`

### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Read-only service. No state mutations. No write operations. No compensation needed.
- **Implication**: No compensation concerns.
- **Recommendation**: No action needed.
- **Evidence**: `src/recommendationservice/recommendation_server.py`

### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Read-only operations. No writes, deletes, or modifications. Each request fetches the full product catalog (amplification) but has no destructive side effects.
- **Implication**: Blast radius is limited to resource consumption (CPU, memory, upstream load). No data mutation risk.
- **Recommendation**: Address amplification via caching (see DATA-Q3).
- **Evidence**: `src/recommendationservice/recommendation_server.py`

### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO
- **Finding**: Handles PII-CANDIDATE data — `user_id` in `ListRecommendationsRequest`. `DATA_CLASSIFICATION.md` classifies recommendationservice as "INTERNAL / PII-CANDIDATE" with sensitive field `user_id`. Product IDs are PUBLIC data. No explicit data classification comment on RecommendationService section in proto, but `user_id` classification is inherited from the field-level annotation pattern.
- **Implication**: PII-CANDIDATE classification documented. user_id handling requires awareness but not full PII controls.
- **Recommendation**: Add explicit data classification comment to RecommendationService section in proto.
- **Evidence**: `protos/demo.proto`, `DATA_CLASSIFICATION.md`

### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: user_id (PII-CANDIDATE) processed in-memory only. Product data is PUBLIC. No persistent storage. No cross-region transfer.
- **Implication**: Minimal residency concerns. user_id is transient.
- **Recommendation**: Assess residency if user_id is sent to external ML services for personalization.
- **Evidence**: `DATA_CLASSIFICATION.md`, `protos/demo.proto`, `src/recommendationservice/recommendation_server.py`

### DATA-Q4: System of Record Designations
- **Severity**: INFO
- **Finding**: Recommendationservice is not a system of record — it reads from productcatalogservice (the system of record for product data) and computes recommendations on-the-fly. No persistent state. `DATA_CLASSIFICATION.md` lists it as system of record for "Product recommendations" but this is computed, not stored.
- **Implication**: Clear dependency on productcatalogservice as upstream system of record. Recommendations are derived, not authoritative.
- **Recommendation**: Document that productcatalogservice is the authoritative source. Recommendations are ephemeral computations.
- **Evidence**: `protos/demo.proto`, `DATA_CLASSIFICATION.md`, `src/recommendationservice/recommendation_server.py`

### DATA-Q6: PII Redaction in Logs
- **Severity**: INFO
- **Finding**: Logs contain product IDs only: `logger.info("[Recv ListRecommendations] product_ids={}".format(prod_list))`. The `request.user_id` (PII-CANDIDATE) is not logged. Product IDs are PUBLIC data. No PII leakage in current log statements.
- **Implication**: No PII in logs. Positive finding.
- **Recommendation**: Ensure user_id is not added to logs without redaction if logging is expanded.
- **Evidence**: `src/recommendationservice/recommendation_server.py`

### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: Recommendations depend on product catalog quality (owned by productcatalogservice). Random sampling provides diversity but no relevance scoring. `max_responses = 5` caps output. No quality metrics.
- **Gap**: No recommendation quality monitoring.
- **Recommendation**: Add quality metrics if ML-based recommendations are implemented.
- **Evidence**: `src/recommendationservice/recommendation_server.py`

### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: INFO
- **Finding**: Proto versioned `hipstershop.v1`. `buf.yaml` with STANDARD lint and FILE-level breaking change detection. `buf breaking` not in CI.
- **Gap**: `buf breaking` not in CI.
- **Recommendation**: Add `buf breaking` to CI pipeline.
- **Evidence**: `protos/demo.proto`, `protos/buf.yaml`

### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Clear semantic names: `user_id`, `product_ids`. Simple, unambiguous. Proto comments minimal but field names are self-documenting.
- **Gap**: None.
- **Recommendation**: No action needed.
- **Evidence**: `protos/demo.proto`

### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal catalog. Proto with field-level annotations. DATA_CLASSIFICATION.md provides taxonomy. Dependency on productcatalogservice documented in Helm (PRODUCT_CATALOG_SERVICE_ADDR env var).
- **Gap**: No formal catalog.
- **Recommendation**: Register in organization API catalog.
- **Evidence**: `protos/demo.proto`, `DATA_CLASSIFICATION.md`, `helm-chart/templates/recommendationservice.yaml`

### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: INFO
- **Finding**: OpenTelemetry tracing configured with both `GrpcInstrumentorClient` (for outbound calls to productcatalogservice) and `GrpcInstrumentorServer` (for inbound calls). `OTLPSpanExporter` configured with `COLLECTOR_SERVICE_ADDR`. Python JSON logger. Tracing is functional — both client and server instrumentation provides end-to-end trace context across the recommendation → product catalog call chain.
- **Implication**: Distributed tracing is operational with both client and server instrumentation. Best tracing setup among Python services. Positive finding.
- **Recommendation**: Add trace_id to log entries for log-to-trace correlation.
- **Evidence**: `src/recommendationservice/recommendation_server.py` (GrpcInstrumentorClient + GrpcInstrumentorServer), `helm-chart/templates/recommendationservice.yaml`, `src/recommendationservice/requirements.in`

### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: INFO
- **Finding**: Prometheus alerting rules cover all gRPC services. Health probes (liveness + readiness) via gRPC. HPA configured (1–5 replicas).
- **Implication**: Alerting infrastructure is comprehensive.
- **Recommendation**: Add recommendation-specific alerts for upstream dependency failures (productcatalogservice unavailable).
- **Evidence**: `kubernetes-manifests/monitoring-alerts.yaml`, `helm-chart/templates/recommendationservice.yaml`, `kubernetes-manifests/hpa.yaml`

### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics. Logs product IDs returned but no recommendation quality metrics (click-through rate, conversion rate, diversity score).
- **Gap**: No business outcome monitoring.
- **Recommendation**: Publish recommendation quality metrics: CTR, diversity, coverage.
- **Evidence**: `src/recommendationservice/recommendation_server.py`

### HITL-Q3: Sandbox/Staging Environment
- **Severity**: INFO
- **Finding**: Skaffold local dev. Cloud Build staging. CI per-PR namespaces. No persistent agent testing environment.
- **Gap**: No dedicated agent testing environment.
- **Recommendation**: Create persistent staging namespace for agent integration testing.
- **Evidence**: `cloudbuild.yaml`, `src/recommendationservice/Dockerfile`, `.github/workflows/ci-pr.yaml`

### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: INFO
- **Finding**: Comprehensive IaC via Helm. All security policies enabled. CODEOWNERS enforces review. No drift detection.
- **Gap**: Drift detection missing.
- **Recommendation**: Implement GitOps.
- **Evidence**: `helm-chart/templates/recommendationservice.yaml`, `helm-chart/values.yaml`, `.github/CODEOWNERS`

### ENG-Q3: Rollback Capability
- **Severity**: INFO
- **Finding**: K8s Deployment rollout. Manual rollback. gRPC health probes. Monitoring alerts.
- **Gap**: No automated rollback.
- **Recommendation**: Configure Flagger or Argo Rollouts.
- **Evidence**: `cloudbuild.yaml`, `helm-chart/templates/recommendationservice.yaml`

### ENG-Q4: API Test Coverage
- **Severity**: INFO
- **Archetype-Calibrated**: data-gateway with simple logic — evaluated as INFO (downgraded from RISK)
- **Finding**: No recommendationservice-specific tests. `client.py` exists as a manual test client but not automated. Simple logic: fetch catalog, filter by cart contents, random sample up to 5. CI smoke test via loadgenerator exercises the RPC indirectly.
- **Gap**: Zero test coverage. Simple logic reduces risk.
- **Recommendation**: Add unit tests for filtering logic and edge cases (empty catalog, all products in cart).
- **Evidence**: `src/recommendationservice/recommendation_server.py`, `src/recommendationservice/client.py`

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: gRPC interface in `protos/demo.proto` with `RecommendationService` defining `ListRecommendations` RPC. Versioned package `hipstershop.v1`. No explicit data classification comment on section. Implemented in `recommendation_server.py`.
- **Gap**: None — BLOCKER criteria satisfied. Missing data classification comment on service section (minor).
- **Recommendation**: Add data classification comment to RecommendationService section.
- **Evidence**: `protos/demo.proto`, `src/recommendationservice/recommendation_server.py`

#### API-Q2: Machine-Readable API Specification
- **Severity**: INFO
- **Finding**: `protos/demo.proto` is machine-readable. Strongly typed with versioned package. `buf.yaml` provides linting and breaking change detection.
- **Gap**: None.
- **Recommendation**: Consider enabling gRPC server reflection.
- **Evidence**: `protos/demo.proto`, `protos/buf.yaml`

#### API-Q3: Structured Error Responses
- **Severity**: RISK
- **Finding**: No error handling in ListRecommendations. Upstream errors from productcatalogservice propagated without classification.
- **Gap**: No structured error responses. No error classification.
- **Recommendation**: Add try/except with distinct status codes for upstream vs local failures.
- **Evidence**: `src/recommendationservice/recommendation_server.py`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Read-only operation. No write side effects. Non-deterministic (random sampling) but no state mutations.
- **Gap**: N/A — no write operations.
- **Recommendation**: No action needed.
- **Evidence**: `src/recommendationservice/recommendation_server.py`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: gRPC Protocol Buffers. `ListRecommendationsResponse` with `repeated string product_ids`. Simple, well-typed.
- **Gap**: None.
- **Recommendation**: No action needed.
- **Evidence**: `protos/demo.proto`

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `data-gateway`, agent_scope: `read-only`.
- **Trigger**: Service has operations >30s OR long-running workflows
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `data-gateway`, agent_scope: `read-only`.
- **Trigger**: Service has state changes (stateful-crud, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit headers. EnvoyFilter rate limit headers only on frontend.
- **Gap**: Agents cannot self-throttle.
- **Recommendation**: Extend EnvoyFilter when rate limiting is applied.
- **Evidence**: `istio-manifests/rate-limit.yaml`, `helm-chart/templates/recommendationservice.yaml`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: Istio AuthorizationPolicy with mTLS. Single caller: frontend. Sidecars and network policies enabled. Sidecar egress scoped to productcatalogservice and OTel Collector.
- **Gap**: None — mesh-level mTLS with scoped egress.
- **Recommendation**: No action needed.
- **Evidence**: `helm-chart/values.yaml`, `helm-chart/templates/recommendationservice.yaml`, `src/recommendationservice/recommendation_server.py`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK
- **Finding**: AuthorizationPolicy restricts to frontend on single RPC. No agent-specific service accounts.
- **Gap**: No agent-specific permissions.
- **Recommendation**: Create agent-specific service accounts if direct access needed.
- **Evidence**: `helm-chart/templates/recommendationservice.yaml`, `helm-chart/values.yaml`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK
- **Finding**: Istio per-path rules defined. No application-layer authorization.
- **Gap**: No application-layer authorization.
- **Recommendation**: Implement gRPC server interceptor.
- **Evidence**: `src/recommendationservice/recommendation_server.py`, `helm-chart/templates/recommendationservice.yaml`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Archetype-Calibrated**: data-gateway — downgraded to INFO
- **Finding**: No identity propagation. user_id used for filtering only. Istio mTLS provides mesh-level identity.
- **Gap**: No application-level identity propagation. Lower priority for read-only data-gateway.
- **Recommendation**: Propagate user_id to audit logs.
- **Evidence**: `src/recommendationservice/recommendation_server.py`, `protos/demo.proto`

#### AUTH-Q5: Credential Management
- **Severity**: RISK
- **Finding**: No credentials. `grpc.insecure_channel` for productcatalogservice (Istio handles mTLS). No Secrets Manager.
- **Gap**: No credential management framework.
- **Recommendation**: Maintain Istio-based security. Adopt external secrets operator if needed.
- **Evidence**: `src/recommendationservice/recommendation_server.py`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK
- **Finding**: Logs product IDs only. No principal attribution. user_id not logged. OTel tracing with client+server instrumentation. Logs are ephemeral stdout.
- **Gap**: No immutable audit trail. No principal attribution.
- **Recommendation**: Add structured audit logging with caller identity and user_id.
- **Evidence**: `src/recommendationservice/recommendation_server.py`, `src/recommendationservice/logger.py`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: INFO
- **Finding**: AuthorizationPolicy and NetworkPolicy provide suspension. Single-caller restriction.
- **Gap**: No automated suspension.
- **Recommendation**: Implement automated suspension if agent direct access is added.
- **Evidence**: `helm-chart/templates/recommendationservice.yaml`, `helm-chart/values.yaml`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Read-only service. No state mutations. No compensation needed.
- **Gap**: None.
- **Recommendation**: No action needed.
- **Evidence**: `src/recommendationservice/recommendation_server.py`

#### STATE-Q2: Queryable Current State
- **Severity**: INFO
- **Finding**: data-gateway archetype triggers this extended question. Recommendationservice has no persistent state — recommendations are computed on-the-fly from productcatalogservice. The `ListRecommendations` RPC itself serves as the queryable interface, returning current recommendations based on real-time catalog data.
- **Gap**: No stored state to query. Computed results are ephemeral.
- **Recommendation**: No action needed — real-time computation provides current state by design.
- **Evidence**: `src/recommendationservice/recommendation_server.py`, `protos/demo.proto`

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `data-gateway`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled AND service has persistent state
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK
- **Finding**: Synchronous call to productcatalogservice with no timeout, retry, or circuit breaker. Blocks indefinitely if upstream is slow.
- **Gap**: No resilience patterns for upstream dependency.
- **Recommendation**: Add gRPC deadline. Implement circuit breaker or Istio outlier detection.
- **Evidence**: `src/recommendationservice/recommendation_server.py`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK
- **Finding**: No rate limiting. Each request triggers full catalog fetch (amplification). HPA (1–5 replicas). ThreadPoolExecutor(max_workers=10).
- **Gap**: No rate limiting. Request amplification risk.
- **Recommendation**: Add EnvoyFilter. Cache product catalog.
- **Evidence**: `istio-manifests/rate-limit.yaml`, `kubernetes-manifests/hpa.yaml`, `src/recommendationservice/recommendation_server.py`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Read-only. No destructive side effects. Amplification risk (full catalog fetch) but no data mutation.
- **Gap**: None for data safety. Amplification is a resource concern.
- **Recommendation**: Address amplification via caching.
- **Evidence**: `src/recommendationservice/recommendation_server.py`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `data-gateway`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `data-gateway`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `data-gateway`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: INFO
- **Finding**: Skaffold local dev. Cloud Build staging. CI per-PR namespaces. `client.py` provides manual testing.
- **Gap**: No dedicated agent testing environment.
- **Recommendation**: Create persistent staging namespace.
- **Evidence**: `cloudbuild.yaml`, `src/recommendationservice/Dockerfile`, `.github/workflows/ci-pr.yaml`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO
- **Finding**: PII-CANDIDATE (user_id) classified in DATA_CLASSIFICATION.md. Product IDs are PUBLIC. No explicit proto section comment.
- **Gap**: Missing proto section data classification comment.
- **Recommendation**: Add data classification comment to RecommendationService section in proto.
- **Evidence**: `protos/demo.proto`, `DATA_CLASSIFICATION.md`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: user_id processed in-memory only. Product data is PUBLIC. No persistent storage. No cross-region transfer.
- **Gap**: Minimal residency concerns.
- **Recommendation**: Assess residency if user_id sent to external ML services.
- **Evidence**: `DATA_CLASSIFICATION.md`, `protos/demo.proto`, `src/recommendationservice/recommendation_server.py`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK
- **Finding**: Full catalog fetch on every request. No pagination, no server-side filtering. max_responses=5 caps output but not input.
- **Gap**: Unbounded upstream query amplification.
- **Recommendation**: Cache product catalog. Add pagination if catalog grows.
- **Evidence**: `src/recommendationservice/recommendation_server.py`

#### DATA-Q4: System of Record Designations
- **Severity**: INFO
- **Finding**: Not a system of record. Reads from productcatalogservice. Recommendations are computed, not stored.
- **Gap**: None — clear dependency documentation.
- **Recommendation**: Document productcatalogservice as authoritative source.
- **Evidence**: `protos/demo.proto`, `DATA_CLASSIFICATION.md`, `src/recommendationservice/recommendation_server.py`

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK
- **Finding**: No freshness metadata in responses. Real-time computation ensures freshness currently. Staleness risk if caching is added.
- **Gap**: No freshness signal in response.
- **Recommendation**: Add computed_at timestamp. Critical if caching is implemented.
- **Evidence**: `protos/demo.proto`, `src/recommendationservice/recommendation_server.py`

#### DATA-Q6: PII Redaction in Logs
- **Severity**: INFO
- **Finding**: Logs product IDs only (PUBLIC). user_id not logged. No PII leakage.
- **Gap**: None.
- **Recommendation**: Ensure user_id not added to logs without redaction.
- **Evidence**: `src/recommendationservice/recommendation_server.py`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: Random sampling. No relevance scoring. max_responses=5. Quality depends on upstream catalog.
- **Gap**: No quality monitoring.
- **Recommendation**: Add quality metrics if ML recommendations are implemented.
- **Evidence**: `src/recommendationservice/recommendation_server.py`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: INFO
- **Finding**: Proto versioned `hipstershop.v1`. `buf.yaml` configured. `buf breaking` not in CI.
- **Gap**: `buf breaking` not in CI.
- **Recommendation**: Add `buf breaking` to CI.
- **Evidence**: `protos/demo.proto`, `protos/buf.yaml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Clear names: `user_id`, `product_ids`. Simple and self-documenting.
- **Gap**: None.
- **Recommendation**: No action needed.
- **Evidence**: `protos/demo.proto`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal catalog. Proto with field annotations. DATA_CLASSIFICATION.md. Dependency on productcatalogservice documented in Helm.
- **Gap**: No formal catalog.
- **Recommendation**: Register in organization API catalog.
- **Evidence**: `protos/demo.proto`, `DATA_CLASSIFICATION.md`, `helm-chart/templates/recommendationservice.yaml`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: INFO
- **Finding**: OTel tracing with both GrpcInstrumentorClient and GrpcInstrumentorServer. End-to-end trace context across recommendation → product catalog chain. Python JSON logger. Best tracing setup among Python services.
- **Gap**: No trace_id in log entries.
- **Recommendation**: Add trace_id to log entries.
- **Evidence**: `src/recommendationservice/recommendation_server.py`, `helm-chart/templates/recommendationservice.yaml`, `src/recommendationservice/requirements.in`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: INFO
- **Finding**: Prometheus alerting rules cover all gRPC services. Health probes. HPA (1–5 replicas).
- **Gap**: None — alerting is comprehensive.
- **Recommendation**: Add alerts for upstream dependency failures.
- **Evidence**: `kubernetes-manifests/monitoring-alerts.yaml`, `helm-chart/templates/recommendationservice.yaml`, `kubernetes-manifests/hpa.yaml`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics. Logs product IDs returned. No recommendation quality metrics.
- **Gap**: No business outcome monitoring.
- **Recommendation**: Publish recommendation quality metrics: CTR, diversity, coverage.
- **Evidence**: `src/recommendationservice/recommendation_server.py`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: INFO
- **Finding**: Comprehensive IaC via Helm. All security policies enabled. CODEOWNERS. No drift detection.
- **Gap**: Drift detection missing.
- **Recommendation**: Implement GitOps.
- **Evidence**: `helm-chart/templates/recommendationservice.yaml`, `helm-chart/values.yaml`, `.github/CODEOWNERS`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK
- **Finding**: CI exists. Proto versioned. `buf.yaml` configured. `buf breaking` not in CI. No tests.
- **Gap**: `buf breaking` not in CI. Zero test coverage.
- **Recommendation**: Add `buf breaking` to CI. Add unit tests.
- **Evidence**: `cloudbuild.yaml`, `.github/workflows/ci-pr.yaml`, `protos/buf.yaml`

#### ENG-Q3: Rollback Capability
- **Severity**: INFO
- **Finding**: K8s Deployment rollout. Manual rollback. Health probes. Monitoring alerts.
- **Gap**: No automated rollback.
- **Recommendation**: Configure Flagger or Argo Rollouts.
- **Evidence**: `cloudbuild.yaml`, `helm-chart/templates/recommendationservice.yaml`

#### ENG-Q4: API Test Coverage
- **Severity**: INFO
- **Archetype-Calibrated**: data-gateway with simple logic — evaluated as INFO
- **Finding**: No automated tests. `client.py` for manual testing. Simple logic (filter + random sample). CI smoke test via loadgenerator.
- **Gap**: Zero test coverage. Simple logic reduces risk.
- **Recommendation**: Add unit tests for filtering and edge cases.
- **Evidence**: `src/recommendationservice/recommendation_server.py`, `src/recommendationservice/client.py`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: RISK
- **Finding**: No persistent store. Data computed in-memory. Required if caching is added.
- **Gap**: No encryption at rest framework (not currently needed).
- **Recommendation**: Ensure encryption at rest if local cache is added.
- **Evidence**: `src/recommendationservice/recommendation_server.py`, `helm-chart/values.yaml`

---

## Evidence Index

### Infrastructure as Code
| File | Questions Referenced |
|------|---------------------|
| `helm-chart/templates/recommendationservice.yaml` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q7, API-Q8, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q3, STATE-Q5, DISC-Q3 |
| `helm-chart/values.yaml` | AUTH-Q1, AUTH-Q2, AUTH-Q7, ENG-Q1, ENG-Q5 |
| `kubernetes-manifests/hpa.yaml` | STATE-Q5, OBS-Q2 |
| `kubernetes-manifests/monitoring-alerts.yaml` | OBS-Q2 |
| `istio-manifests/rate-limit.yaml` | STATE-Q5, API-Q8 |

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `src/recommendationservice/recommendation_server.py` | API-Q1, API-Q3, API-Q4, AUTH-Q1, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q6, STATE-Q1, STATE-Q2, STATE-Q4, STATE-Q5, STATE-Q6, DATA-Q2, DATA-Q3, DATA-Q5, DATA-Q6, DATA-Q7, OBS-Q1, OBS-Q3, ENG-Q4, ENG-Q5 |
| `src/recommendationservice/logger.py` | AUTH-Q6 |
| `src/recommendationservice/client.py` | ENG-Q4 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `protos/demo.proto` | API-Q1, API-Q2, API-Q5, AUTH-Q4, DATA-Q1, DATA-Q2, DATA-Q4, DATA-Q5, DISC-Q1, DISC-Q2, DISC-Q3, STATE-Q2 |
| `protos/buf.yaml` | API-Q2, DISC-Q1, ENG-Q2 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `cloudbuild.yaml` | HITL-Q3, ENG-Q2, ENG-Q3 |
| `.github/workflows/ci-pr.yaml` | HITL-Q3, ENG-Q2 |
| `.github/CODEOWNERS` | ENG-Q1 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `src/recommendationservice/Dockerfile` | HITL-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `src/recommendationservice/requirements.in` | OBS-Q1 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `DATA_CLASSIFICATION.md` | DATA-Q1, DATA-Q2, DATA-Q4, DISC-Q3 |
