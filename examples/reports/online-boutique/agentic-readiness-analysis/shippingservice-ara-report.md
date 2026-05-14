# Agentic Readiness Analysis Report

**Target**: services/microservices-demo/src/shippingservice
**Date**: 2026-04-16
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**Repository Type**: application
**Service Archetype**: stateful-crud (user-provided)
**Agent Scope**: read-only
**Priority**: P1
**Tags**: go, grpc, shipping
**Context**: Go gRPC service providing shipping cost estimates and tracking.

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 2 | **RISKs**: 17 | **INFOs**: 13

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days. The two blockers (AUTH-Q1: no machine identity authentication; DATA-Q1: PII data — shipping addresses) must be resolved before any agent can safely call this service. The 17 RISKs are manageable with compensating controls once blockers are cleared.

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
**Service Archetype**: stateful-crud (user-provided)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: The gRPC server is created via `grpc.NewServer()` in `main.go` (line 89) with no authentication interceptor, no TLS configuration, and no credential verification. The server accepts all incoming connections on port 50051. Istio AuthorizationPolicies are disabled (`authorizationPolicies.create: false` in `helm-chart/values.yaml`), so there is no mesh-level caller identity enforcement. NetworkPolicies are also disabled (`networkPolicies.create: false`). gRPC server reflection is enabled (`reflection.Register(srv)` at line 96) which exposes the full service schema to any caller. No OAuth2, no API key, no mTLS at the application layer.
- **Gap**: No machine identity authentication at any layer. Any network-reachable client can call `GetQuote` and `ShipOrder` without presenting credentials. gRPC reflection exposes the full API surface to unauthenticated callers.
- **Remediation**:
  - **Immediate**: Enable Istio AuthorizationPolicies (`authorizationPolicies.create: true`) to enforce mTLS-based caller identity at the mesh layer.
  - **Target State**: Mesh-level mTLS with per-caller AuthorizationPolicy rules. Agent-specific K8s ServiceAccounts. Application-layer gRPC `UnaryInterceptor` for defense-in-depth.
  - **Estimated Effort**: Low (Helm value change), Medium (application-layer interceptor)
  - **Dependencies**: AUTH-Q2, AUTH-Q6
- **Evidence**: `main.go` (line 89, `grpc.NewServer()` with no auth; line 96, `reflection.Register(srv)`), `helm-chart/values.yaml` (`authorizationPolicies.create: false`, `networkPolicies.create: false`)

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: The shipping service processes PII — physical shipping addresses. The `ShipOrderRequest` and `GetQuoteRequest` proto messages contain an `Address` message with `street_address`, `city`, `state`, `country`, and `zip_code`. The `ShipOrder` handler in `main.go` (line 131) constructs a `baseAddress` string from `street_address`, `city`, and `state` and uses it as a salt for tracking ID generation. Address data is PII under GDPR and CCPA. No formal data classification exists — no `DATA_CLASSIFICATION.md` in the service directory. The repo-level `DATA_CLASSIFICATION.md` exists but does not provide per-service PII classification.
- **Gap**: PII (physical addresses) processed without formal data classification. Address data used as input to tracking ID generation (leaked into tracking ID entropy). No PII handling controls.
- **Remediation**:
  - **Immediate**: Create a `DATA_CLASSIFICATION.md` documenting that the shipping service processes PII (physical addresses). Classify `Address` fields as CONFIDENTIAL/PII.
  - **Target State**: PII-aware logging (redact addresses from logs). Address data handling compliant with GDPR/CCPA requirements.
  - **Estimated Effort**: Low (classification document), Medium (PII handling controls)
  - **Dependencies**: AUTH-Q1 (identity required before PII access controls)
- **Evidence**: `proto/demo.proto` (Address message with `street_address`, `city`, `state`, `country`, `zip_code`), `main.go` (line 131, `baseAddress` from address fields), `tracker.go` (CreateTrackingId uses address as salt)

---

## RISKs — Proceed with Compensating Controls

### API-Q2: Machine-Readable API Specification

- **Severity**: RISK
- **Finding**: The service API is defined in `genproto/demo.pb.go` generated from the shared `demo.proto`. The `ShippingService` has two RPCs: `GetQuote` and `ShipOrder`. Protobuf is machine-readable. gRPC server reflection IS enabled (`reflection.Register(srv)` in `main.go`), which is a positive — agents can discover the API at runtime. However, the proto file is monolithic (all 10 services) and not published as a standalone spec.
- **Gap**: No standalone machine-readable spec. Proto is shared across all services. Reflection is enabled but unauthenticated.
- **Compensating Controls**:
  - gRPC server reflection enables runtime API discovery
  - The proto file can generate client stubs for agent tool definitions
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Secure gRPC reflection behind authentication. Extract shipping service proto into standalone file.
- **Evidence**: `main.go` (line 96, `reflection.Register(srv)`), `genproto/demo.pb.go` (generated from demo.proto)

### API-Q3: Structured Error Responses

- **Severity**: RISK
- **Finding**: The `GetQuote` and `ShipOrder` handlers return `nil` errors on success. Error handling is minimal — no explicit error returns in the current implementation. The gRPC framework provides standard status codes, but no rich error model is implemented. No `google.golang.org/genproto/googleapis/rpc/errdetails` usage. No retryable boolean, no error code taxonomy.
- **Gap**: No rich error model. Agents cannot distinguish retriable from terminal errors.
- **Compensating Controls**:
  - gRPC status codes provide basic error classification
  - Wrap agent tool calls with client-side error classification
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement gRPC rich error model using `errdetails` package. Add error codes and retryable flags.
- **Evidence**: `main.go` (GetQuote and ShipOrder handlers — minimal error handling)

### AUTH-Q2: Scoped Permissions (Least Privilege)

- **Severity**: RISK
- **Finding**: AuthorizationPolicies disabled. The Helm template defines a policy restricting callers to `frontend` and `checkoutservice` service accounts on `/hipstershop.ShippingService/GetQuote` and `/hipstershop.ShippingService/ShipOrder`, but not deployed. No agent-specific service accounts.
- **Gap**: No caller restriction. No agent-specific permission scoping.
- **Compensating Controls**:
  - Enable AuthorizationPolicies to activate existing Helm template
  - Define agent-specific K8s ServiceAccounts
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Enable `authorizationPolicies.create: true`. Create agent-specific service accounts with per-RPC rules.
- **Evidence**: `helm-chart/values.yaml` (`authorizationPolicies.create: false`), `helm-chart/templates/shippingservice.yaml`

### AUTH-Q3: Action-Level Authorization

- **Severity**: RISK
- **Finding**: No application-layer authorization. The gRPC server accepts all calls. AuthorizationPolicy with per-path rules exists in Helm template but disabled. Both `GetQuote` (read) and `ShipOrder` (write) are equally accessible.
- **Gap**: No action-level authorization. Read and write RPCs have identical access controls (none).
- **Compensating Controls**:
  - Enable AuthorizationPolicies for mesh-level per-path enforcement
  - The service exposes only two RPCs, limiting the action surface
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Enable AuthorizationPolicies. Consider separate authorization rules for `GetQuote` (read) vs `ShipOrder` (write).
- **Evidence**: `main.go` (no auth interceptor), `helm-chart/values.yaml` (`authorizationPolicies.create: false`)

### AUTH-Q5: Credential Management

- **Severity**: RISK
- **Finding**: No secrets or credentials used. Only environment variable is `PORT`. No database connections, no external API calls. Shipping cost is calculated in-memory (`quote.go`), tracking IDs are generated algorithmically (`tracker.go`). No Secrets Manager or Vault.
- **Gap**: No credential management framework. Credential-free architecture is appropriate for current scope.
- **Compensating Controls**:
  - Credential-free architecture eliminates secret rotation concerns
  - K8s ServiceAccount with Istio mTLS (when enabled) avoids hardcoded credentials
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Maintain credential-free architecture. Use K8s Secrets with external secrets operator if credentials are introduced.
- **Evidence**: `main.go` (line 79, `os.LookupEnv("PORT")`), `Dockerfile` (no secrets)

### AUTH-Q6: Immutable Audit Logging ⚡

- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: Logging uses `logrus` with JSON formatter (`JSONFormatter` with `timestamp`, `severity`, `message` fields). Logs include request start/complete messages for `GetQuote` and `ShipOrder` but no request details, no caller identity, no principal attribution. Logs are ephemeral container stdout. No immutable storage. Tracing is disabled (`initTracing()` is a TODO stub at line 148).
- **Gap**: No immutable audit trail. No principal attribution. No immutable log storage. Tracing is a stub.
- **Compensating Controls**:
  - JSON structured logging provides basic log analysis
  - Enable Istio access logging for mesh-level request attribution
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add caller identity to structured logs. Forward to immutable store. Implement OpenTelemetry tracing (replace TODO stub).
- **Evidence**: `main.go` (lines 42–52, logrus JSON formatter; lines 147–148, initTracing TODO stub)

### AUTH-Q7: Agent Identity Suspension

- **Severity**: RISK
- **Finding**: No agent identity suspension mechanism. AuthorizationPolicies disabled. No kill switch for individual agent instances.
- **Gap**: No mechanism to immediately suspend a misbehaving agent.
- **Compensating Controls**:
  - When AuthorizationPolicies are enabled, removing an agent's principal blocks access
  - K8s NetworkPolicy can block specific pod selectors
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement agent-specific ServiceAccounts with AuthorizationPolicy-based suspension.
- **Evidence**: `helm-chart/values.yaml` (`authorizationPolicies.create: false`), `helm-chart/templates/shippingservice.yaml`

### STATE-Q2: Queryable Current State

- **Severity**: RISK
- **Finding**: The shipping service is stateless — it does not persist shipping records, tracking IDs, or quote history. `GetQuote` calculates a cost based on item count (always $8.99 for non-empty carts). `ShipOrder` generates a tracking ID algorithmically but does not store it. There is no way to query previous quotes or track shipment status.
- **Gap**: No queryable state. Agents cannot verify previous quotes or track shipments.
- **Compensating Controls**:
  - The calling service (checkoutservice) may store tracking IDs in order records
  - Implement a shipment tracking query endpoint
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement a `GetShipmentStatus` RPC for tracking ID lookup. Consider persisting quote and shipment records.
- **Evidence**: `main.go` (GetQuote and ShipOrder — no persistence), `quote.go` (in-memory calculation), `tracker.go` (algorithmic ID generation)

### STATE-Q4: Circuit Breakers and Resilience

- **Severity**: RISK
- **Finding**: The shipping service has no external dependencies and no resilience patterns. No circuit breakers, no retry logic, no timeout configuration. The gRPC server has no graceful shutdown handling. All operations are in-memory calculations.
- **Gap**: No resilience patterns. While currently no external dependencies, the lack of resilience infrastructure means adding external shipping APIs would require significant rework.
- **Compensating Controls**:
  - In-memory operations have no external failure modes
  - K8s health probes provide basic availability detection
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add graceful shutdown handling. Implement circuit breaker pattern for future external API integration.
- **Evidence**: `main.go` (no circuit breaker, no graceful shutdown), `quote.go` (in-memory), `tracker.go` (in-memory)

### DATA-Q3: Selective Query Support

- **Severity**: RISK
- **Finding**: `GetQuote` accepts a single request with items array and returns a single cost. `ShipOrder` accepts a single order and returns a tracking ID. No list/query endpoints, no pagination, no filtering. An agent could call `ShipOrder` at machine speed to generate many shipments without any batch controls.
- **Gap**: No selective query. No batch limits on shipment creation.
- **Compensating Controls**:
  - Rate limiting at mesh or API gateway layer can bound requests
  - Simulated shipping limits real-world impact
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement per-caller rate limiting on `ShipOrder` RPC.
- **Evidence**: `proto/demo.proto` (GetQuote, ShipOrder — single request/response)

### DATA-Q4: System of Record Designations

- **Severity**: RISK
- **Finding**: The shipping service does not persist data. Tracking IDs are generated algorithmically but not stored. Quote calculations are ephemeral. The service cannot serve as a system of record for shipping records.
- **Gap**: No system of record for shipping data. Tracking IDs not persisted.
- **Compensating Controls**:
  - Checkoutservice may record tracking IDs in order records
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement persistent shipment records with tracking ID as primary key.
- **Evidence**: `tracker.go` (generates tracking ID, doesn't persist), `main.go` (no database)

### DATA-Q5: Temporal Metadata and Freshness

- **Severity**: RISK
- **Finding**: `GetQuoteResponse` contains only `cost_usd`. `ShipOrderResponse` contains only `tracking_id`. No timestamps, no `created_at`, no `shipped_at` metadata. Agents cannot determine when a quote was generated or when a shipment was created.
- **Gap**: No temporal metadata on responses.
- **Compensating Controls**:
  - Calling service can record timestamps at invocation time
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `quoted_at` to GetQuoteResponse and `shipped_at` to ShipOrderResponse.
- **Evidence**: `proto/demo.proto` (GetQuoteResponse, ShipOrderResponse — no timestamps)

### OBS-Q1: Distributed Tracing and Structured Logging

- **Severity**: RISK
- **Finding**: Tracing is disabled. `initTracing()` in `main.go` (line 148) is a TODO stub. `initStats()` (line 145) is also a TODO stub. Logging uses `logrus` with JSON formatter — structured logs with `timestamp`, `severity`, `message` fields. Logs lack trace correlation IDs. The `go.mod` includes `go.opentelemetry.io/otel` as indirect dependencies but no direct instrumentation.
- **Gap**: No distributed tracing. Structured logs lack trace correlation. Agent-initiated requests cannot be traced.
- **Compensating Controls**:
  - Logrus JSON structured logging provides basic log analysis
  - Istio sidecar can provide mesh-level trace context
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement OpenTelemetry Go SDK instrumentation. Replace `initTracing()` TODO with actual implementation. Add trace context to logrus fields.
- **Evidence**: `main.go` (lines 145–148, initStats and initTracing TODO stubs), `go.mod` (OpenTelemetry indirect deps)

### OBS-Q2: Alerting on Error Rates and Latency

- **Severity**: RISK
- **Finding**: No alerting configuration. gRPC health probes (readiness and liveness on port 50051) exist but no error rate or latency alerting. No custom metrics. `initStats()` is a TODO stub.
- **Gap**: No alerting on error rates or latency.
- **Compensating Controls**:
  - gRPC health probes provide basic availability detection
  - Istio sidecar metrics can feed Prometheus alerting
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure Prometheus alerting rules for gRPC error rates and p99 latency.
- **Evidence**: `main.go` (line 145, initStats TODO), `helm-chart/templates/shippingservice.yaml` (health probes only)

### DISC-Q1: Schema Versioning and API Contracts

- **Severity**: RISK
- **Finding**: Proto uses `package hipstershop` with no version suffix. No `buf.yaml`. No breaking change detection. No contract tests. CI has no proto compatibility checks.
- **Gap**: No proto versioning. No breaking change detection.
- **Compensating Controls**:
  - Proto file in source control provides change history via git
  - Pin agent tool definitions to current schema
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add version suffix (`hipstershop.v1`). Integrate `buf breaking` into CI.
- **Evidence**: `genproto/demo.pb.go` (generated from `package hipstershop`), no `buf.yaml`

### ENG-Q1: Infrastructure Governance for Agent-Facing Surface

- **Severity**: RISK
- **Finding**: Helm charts and Terraform with PR-based review. No drift detection.
- **Gap**: No drift detection.
- **Compensating Controls**:
  - Helm charts provide declarative infrastructure
  - GitHub PR workflow enforces peer review
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement GitOps with ArgoCD or Flux.
- **Evidence**: `helm-chart/templates/shippingservice.yaml`, `helm-chart/values.yaml`

### ENG-Q2: CI/CD with API Contract Testing

- **Severity**: RISK
- **Finding**: CI/CD exists via GitHub Actions and Cloud Build. The shipping service has unit tests (`shippingservice_test.go`) covering `GetQuote`, `ShipOrder`, tracking ID generation, and quote calculation. However, no API contract tests (Pact), no proto compatibility checks, no gRPC integration tests against a running server.
- **Gap**: Unit tests exist but no API contract testing. No proto breaking change detection.
- **Compensating Controls**:
  - Unit tests validate core business logic
  - Staging deployment provides pre-production validation
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add gRPC integration tests. Integrate `buf breaking` for proto compatibility.
- **Evidence**: `shippingservice_test.go` (unit tests for GetQuote, ShipOrder, tracking ID), `.github/workflows/ci-pr.yaml`

### ENG-Q4: API Test Coverage

- **Severity**: RISK
- **Finding**: Unit tests exist in `shippingservice_test.go` covering `GetQuote` (basic and empty cart), `ShipOrder` (basic), tracking ID format and uniqueness, quote creation, and random number generation. Good coverage of business logic. However, no gRPC integration tests, no error path testing, no load testing. Tests run via `go test` in CI.
- **Gap**: Unit tests cover happy paths but no error paths, no integration tests, no contract tests.
- **Compensating Controls**:
  - Existing unit tests validate core business logic
  - Smoke tests via load generator provide end-to-end validation
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add error path tests. Add gRPC integration tests against a running server.
- **Evidence**: `shippingservice_test.go` (TestGetQuote, TestShipOrder, TestTrackingIdFormat, TestTrackingIdUniqueness, etc.)

### ENG-Q5: Encryption at Rest for Agent-Accessible Data

- **Severity**: RISK
- **Finding**: The shipping service does not persist data. Address data and tracking IDs exist only in-memory during request processing. However, log output may contain address data (currently logs only start/complete messages, not request details). No persistent data store to encrypt.
- **Gap**: No persistent data store. Address data in-memory only. Log storage encryption depends on K8s node configuration.
- **Compensating Controls**:
  - In-memory-only processing means PII is not persisted by the application
  - Current logging does not include address details
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Ensure address data is not logged. If shipment records are persisted (per STATE-Q2), ensure encryption at rest.
- **Evidence**: `main.go` (logs only start/complete messages), `tracker.go` (in-memory), `quote.go` (in-memory)

---

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO
- **Finding**: The service exposes a gRPC API with two RPCs: `GetQuote(GetQuoteRequest) returns (GetQuoteResponse)` and `ShipOrder(ShipOrderRequest) returns (ShipOrderResponse)`. Well-defined, typed interface using Protocol Buffers. gRPC server reflection is enabled for runtime discovery.
- **Implication**: The gRPC interface is agent-consumable with runtime discovery via reflection.
- **Recommendation**: No action required.
- **Evidence**: `genproto/demo.pb.go`, `main.go` (line 96, `reflection.Register(srv)`)

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: `GetQuote` is read-only and deterministic (same item count → same cost). `ShipOrder` is a write operation that generates a random tracking ID — not idempotent. Repeated calls with the same address/items produce different tracking IDs. No idempotency key in request schema.
- **Implication**: ShipOrder is non-idempotent. If scope changes to write-enabled, this needs attention.
- **Recommendation**: No action for read-only scope. Add idempotency key to ShipOrderRequest if write-enabled.
- **Evidence**: `main.go` (ShipOrder generates random tracking ID), `tracker.go` (random components in ID)

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: Responses are Protocol Buffers over gRPC. `GetQuoteResponse` contains `cost_usd` (Money message). `ShipOrderResponse` contains `tracking_id` (string). Strongly typed.
- **Implication**: Protobuf is efficient for machine consumption.
- **Recommendation**: Consider gRPC-JSON transcoding if agents require JSON.
- **Evidence**: `genproto/demo.pb.go` (GetQuoteResponse, ShipOrderResponse)

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limiting configured. No rate limit documentation.
- **Implication**: Agents have no rate limit feedback.
- **Recommendation**: Document throughput capacity. Consider gRPC rate limiting.
- **Evidence**: `main.go` (no rate limiting), `helm-chart/templates/shippingservice.yaml`

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: INFO
- **Finding**: No identity propagation. `GetQuoteRequest` and `ShipOrderRequest` contain `Address` and `CartItem` data but no user identity. The service does not know who is requesting the quote or shipment.
- **Implication**: No caller identity propagation. Limited audit capability for PII-processing service.
- **Recommendation**: Add caller identity context when AUTH-Q1 is resolved.
- **Evidence**: `genproto/demo.pb.go` (no user identity in requests), `main.go`

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: `ShipOrder` is a write operation with no compensation. No `CancelShipment` RPC. Once a tracking ID is generated, it cannot be voided. `GetQuote` is read-only.
- **Implication**: No compensation for write operations. Mitigated by read-only scope.
- **Recommendation**: No action for read-only scope. Implement CancelShipment if write-enabled.
- **Evidence**: `main.go` (ShipOrder — no compensation), `genproto/demo.pb.go` (no cancel RPC)

### STATE-Q5: Rate Limiting and Throttling

- **Severity**: INFO
- **Finding**: No rate limiting. Resource limits (CPU: 200m, memory: 128Mi) provide coarse ceiling. In-memory operations with no external dependencies limit blast radius.
- **Implication**: Runaway agent loop limited to pod resource exhaustion.
- **Recommendation**: Consider gRPC rate limiting via interceptor.
- **Evidence**: `helm-chart/templates/shippingservice.yaml` (resource limits), `helm-chart/values.yaml`

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: `ShipOrder` generates tracking IDs with no limits. `GetQuote` is read-only. Read-only scope mitigates.
- **Gap**: N/A for read-only scope.
- **Recommendation**: No action for current scope.
- **Evidence**: `main.go` (ShipOrder), `tracker.go`

### HITL-Q3: Sandbox/Staging Environment

- **Severity**: INFO
- **Finding**: CI pipeline deploys to staging GKE cluster with per-PR namespaces. Full stack via Skaffold with smoke tests.
- **Gap**: No dedicated agent testing documentation.
- **Recommendation**: Document staging environment for agent testing.
- **Evidence**: `.github/workflows/ci-pr.yaml`, `cloudbuild.yaml`

### DATA-Q2: Data Residency and Sovereignty ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Address data exists only in-memory during request processing. Not persisted. Processing region determined by GKE cluster. GDPR/CCPA may apply to address processing.
- **Gap**: No formal data residency documentation for PII processing.
- **Recommendation**: Document processing region for GDPR/CCPA compliance.
- **Evidence**: `main.go` (in-memory processing), `helm-chart/values.yaml`

### DATA-Q6: PII Redaction in Logs

- **Severity**: INFO
- **Finding**: Current logging does not include address details. Logs contain only `[GetQuote] received request` / `completed request` and `[ShipOrder] received request` / `completed request` messages. No PII in log output.
- **Gap**: None — address data is not currently logged.
- **Recommendation**: Maintain current practice of not logging address details.
- **Evidence**: `main.go` (lines 113–114, 128–129, log messages without request details)

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: `GetQuote` calculates cost based on item count — deterministic and complete. `ShipOrder` generates tracking IDs algorithmically. No external data source that could degrade. Input validation is minimal (no address validation).
- **Gap**: No address validation. Invalid addresses are accepted without error.
- **Recommendation**: Consider adding address validation for data quality.
- **Evidence**: `quote.go` (deterministic calculation), `tracker.go` (algorithmic generation), `main.go` (no input validation)

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Proto field names are human-readable: `street_address`, `city`, `state`, `country`, `zip_code`, `tracking_id`, `cost_usd`, `product_id`, `quantity`. No legacy abbreviations.
- **Gap**: None — naming is clear and semantic.
- **Recommendation**: No action required.
- **Evidence**: `genproto/demo.pb.go` (Address, GetQuoteRequest, ShipOrderRequest field names)

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No formal data catalog. Proto file serves as de facto schema documentation.
- **Gap**: No formal metadata layer.
- **Recommendation**: No action required for current scope.
- **Evidence**: `genproto/demo.pb.go`

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No custom business metrics. `initStats()` is a TODO stub. No shipping cost distribution, no shipment volume metrics, no quote-to-shipment conversion tracking.
- **Gap**: No business outcome measurement.
- **Recommendation**: Implement shipping volume and cost metrics.
- **Evidence**: `main.go` (line 145, initStats TODO stub)

### ENG-Q3: Rollback Capability

- **Severity**: INFO
- **Finding**: Helm rollback available. K8s rolling update. No canary or automated rollback. Distroless container image provides minimal attack surface.
- **Gap**: No automated rollback triggers.
- **Recommendation**: Consider Flagger or Argo Rollouts.
- **Evidence**: `helm-chart/Chart.yaml`, `helm-chart/templates/shippingservice.yaml`, `Dockerfile` (distroless base)

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: gRPC API with `GetQuote` and `ShipOrder` RPCs. Well-defined proto interface. gRPC reflection enabled.
- **Gap**: Monolithic proto file shared across all services.
- **Recommendation**: Extract shipping service proto into standalone file.
- **Evidence**: `genproto/demo.pb.go`, `main.go` (reflection.Register)

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK
- **Finding**: Proto IDL is machine-readable. gRPC reflection enabled. Monolithic proto shared across services.
- **Gap**: No standalone spec. Reflection is unauthenticated.
- **Recommendation**: Secure reflection. Extract standalone proto.
- **Evidence**: `main.go` (reflection.Register), `genproto/demo.pb.go`

#### API-Q3: Structured Error Responses
- **Severity**: RISK
- **Finding**: Minimal error handling. No rich error model. No `errdetails` usage.
- **Gap**: No rich error model beyond gRPC status codes.
- **Recommendation**: Implement gRPC rich error model with errdetails.
- **Evidence**: `main.go` (GetQuote, ShipOrder handlers)

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: GetQuote is deterministic. ShipOrder generates random tracking IDs — not idempotent.
- **Gap**: ShipOrder is non-idempotent. Mitigated by read-only scope.
- **Recommendation**: No action for read-only scope.
- **Evidence**: `main.go` (ShipOrder), `tracker.go` (random ID generation)

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: Protocol Buffers over gRPC. Strongly typed responses.
- **Gap**: Binary protobuf may need transcoding for LLM agents.
- **Recommendation**: Consider gRPC-JSON transcoding.
- **Evidence**: `genproto/demo.pb.go`

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered.
- **Trigger**: Service has operations >30s OR long-running workflows
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered.
- **Trigger**: Service has state changes (stateful-crud, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limiting. No documentation.
- **Gap**: No rate limit feedback.
- **Recommendation**: Document throughput capacity.
- **Evidence**: `main.go`, `helm-chart/templates/shippingservice.yaml`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: `grpc.NewServer()` with no auth. AuthorizationPolicies disabled. Reflection enabled without auth.
- **Gap**: No machine identity authentication.
- **Recommendation**: Enable Istio AuthorizationPolicies. Add gRPC interceptor.
- **Evidence**: `main.go` (line 89, grpc.NewServer(); line 96, reflection.Register), `helm-chart/values.yaml`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK
- **Finding**: AuthorizationPolicies disabled. Helm template restricts to frontend and checkoutservice but not deployed.
- **Gap**: No caller restriction.
- **Recommendation**: Enable AuthorizationPolicies. Create agent-specific service accounts.
- **Evidence**: `helm-chart/values.yaml`, `helm-chart/templates/shippingservice.yaml`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK
- **Finding**: No authorization. Both GetQuote (read) and ShipOrder (write) equally accessible.
- **Gap**: No action-level authorization.
- **Recommendation**: Enable AuthorizationPolicies. Separate rules for read vs write RPCs.
- **Evidence**: `main.go`, `helm-chart/values.yaml`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: No identity propagation. Requests contain address and items but no user identity.
- **Gap**: No identity propagation.
- **Recommendation**: Add caller identity context.
- **Evidence**: `genproto/demo.pb.go` (no user identity in requests)

#### AUTH-Q5: Credential Management
- **Severity**: RISK
- **Finding**: No secrets used. Only PORT env var. Credential-free architecture.
- **Gap**: No credential management framework.
- **Recommendation**: Maintain credential-free architecture.
- **Evidence**: `main.go` (PORT only), `Dockerfile`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: Logrus JSON logging. No principal attribution. No immutable storage. Tracing is TODO stub.
- **Gap**: No immutable audit trail.
- **Recommendation**: Add principal attribution. Forward to immutable store. Implement tracing.
- **Evidence**: `main.go` (logrus formatter, initTracing TODO)

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK
- **Finding**: No suspension mechanism. AuthorizationPolicies disabled.
- **Gap**: No mechanism to suspend misbehaving agent.
- **Recommendation**: Implement agent-specific ServiceAccounts with AuthorizationPolicy suspension.
- **Evidence**: `helm-chart/values.yaml`, `helm-chart/templates/shippingservice.yaml`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: ShipOrder has no compensation. No CancelShipment RPC. Read-only scope mitigates.
- **Gap**: No compensation for writes.
- **Recommendation**: No action for read-only scope.
- **Evidence**: `main.go` (ShipOrder), `genproto/demo.pb.go`

#### STATE-Q2: Queryable Current State
- **Severity**: RISK
- **Finding**: No persistent state. Tracking IDs and quotes not stored. No query capability.
- **Gap**: No queryable state.
- **Recommendation**: Implement GetShipmentStatus RPC.
- **Evidence**: `main.go` (no persistence), `tracker.go`, `quote.go`

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered. agent_scope is read-only.
- **Trigger**: agent_scope is write-enabled AND service has persistent state
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK
- **Finding**: No resilience patterns. No external dependencies. No graceful shutdown.
- **Gap**: No resilience infrastructure.
- **Recommendation**: Add graceful shutdown. Implement circuit breaker for future external APIs.
- **Evidence**: `main.go` (no circuit breaker, no graceful shutdown)

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: INFO
- **Finding**: No rate limiting. Resource limits provide coarse ceiling. In-memory operations limit blast radius.
- **Gap**: No request-level throttling.
- **Recommendation**: Consider gRPC rate limiting.
- **Evidence**: `helm-chart/templates/shippingservice.yaml`, `helm-chart/values.yaml`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No transaction limits. Read-only scope mitigates.
- **Gap**: N/A for read-only scope.
- **Recommendation**: No action for current scope.
- **Evidence**: `main.go`, `tracker.go`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered. Service is P1 priority, not P0.
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
- **Finding**: Staging GKE cluster with per-PR namespaces. Full stack via Skaffold.
- **Gap**: No dedicated agent testing documentation.
- **Recommendation**: Document staging environment for agent testing.
- **Evidence**: `.github/workflows/ci-pr.yaml`, `cloudbuild.yaml`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: PII — physical addresses (street_address, city, state, country, zip_code). Address used as salt for tracking ID generation. No formal classification.
- **Gap**: PII processed without classification controls.
- **Recommendation**: Create DATA_CLASSIFICATION.md. Classify Address as CONFIDENTIAL/PII.
- **Evidence**: `genproto/demo.pb.go` (Address message), `main.go` (line 131, baseAddress), `tracker.go`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Address data in-memory only. Not persisted. GDPR/CCPA may apply.
- **Gap**: No data residency documentation.
- **Recommendation**: Document processing region.
- **Evidence**: `main.go` (in-memory), `helm-chart/values.yaml`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK
- **Finding**: Single request/response RPCs. No list/query. No batch limits.
- **Gap**: No selective query. No batch limits.
- **Recommendation**: Implement per-caller rate limiting.
- **Evidence**: `genproto/demo.pb.go` (GetQuote, ShipOrder)

#### DATA-Q4: System of Record Designations
- **Severity**: RISK
- **Finding**: No persistent data. Not a system of record. Tracking IDs not stored.
- **Gap**: No system of record for shipping data.
- **Recommendation**: Implement persistent shipment records.
- **Evidence**: `tracker.go` (generates, doesn't persist), `main.go` (no database)

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK
- **Finding**: No timestamps in responses. No created_at, no shipped_at.
- **Gap**: No temporal metadata.
- **Recommendation**: Add timestamps to responses.
- **Evidence**: `genproto/demo.pb.go` (no timestamps in responses)

#### DATA-Q6: PII Redaction in Logs
- **Severity**: INFO
- **Finding**: Address data not logged. Logs contain only start/complete messages.
- **Gap**: None.
- **Recommendation**: Maintain current practice.
- **Evidence**: `main.go` (lines 113–114, 128–129)

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: Deterministic calculations. No external data source. Minimal input validation.
- **Gap**: No address validation.
- **Recommendation**: Consider address validation.
- **Evidence**: `quote.go`, `tracker.go`, `main.go`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK
- **Finding**: `package hipstershop` — no version suffix. No buf.yaml. No breaking change detection.
- **Gap**: No proto versioning.
- **Recommendation**: Add version suffix. Integrate buf breaking.
- **Evidence**: `genproto/demo.pb.go`, no `buf.yaml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Human-readable field names: street_address, city, tracking_id, cost_usd.
- **Gap**: None.
- **Recommendation**: No action required.
- **Evidence**: `genproto/demo.pb.go`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal data catalog. Proto file as schema documentation.
- **Gap**: No formal metadata layer.
- **Recommendation**: No action required.
- **Evidence**: `genproto/demo.pb.go`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK
- **Finding**: Tracing disabled (TODO stub). Logrus JSON structured logging. No trace correlation.
- **Gap**: No distributed tracing. No trace correlation in logs.
- **Recommendation**: Implement OpenTelemetry Go SDK. Replace TODO stub.
- **Evidence**: `main.go` (initTracing TODO, logrus formatter)

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK
- **Finding**: No alerting. Health probes only. initStats is TODO stub.
- **Gap**: No alerting.
- **Recommendation**: Configure Prometheus alerting rules.
- **Evidence**: `main.go` (initStats TODO), `helm-chart/templates/shippingservice.yaml`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom metrics. initStats TODO stub.
- **Gap**: No business outcome measurement.
- **Recommendation**: Implement shipping volume and cost metrics.
- **Evidence**: `main.go` (initStats TODO)

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK
- **Finding**: Helm charts and Terraform with PR review. No drift detection.
- **Gap**: No drift detection.
- **Recommendation**: Implement GitOps.
- **Evidence**: `helm-chart/templates/shippingservice.yaml`, `helm-chart/values.yaml`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK
- **Finding**: Unit tests exist (shippingservice_test.go). No API contract tests. No proto compatibility checks.
- **Gap**: No contract testing. No proto breaking change detection.
- **Recommendation**: Add gRPC integration tests. Integrate buf breaking.
- **Evidence**: `shippingservice_test.go`, `.github/workflows/ci-pr.yaml`

#### ENG-Q3: Rollback Capability
- **Severity**: INFO
- **Finding**: Helm rollback available. K8s rolling update. No automated rollback.
- **Gap**: No automated rollback triggers.
- **Recommendation**: Consider Flagger or Argo Rollouts.
- **Evidence**: `helm-chart/Chart.yaml`, `helm-chart/templates/shippingservice.yaml`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK
- **Finding**: Unit tests cover GetQuote, ShipOrder, tracking ID, quote calculation. No error path tests, no integration tests.
- **Gap**: Happy path coverage only. No integration tests.
- **Recommendation**: Add error path and integration tests.
- **Evidence**: `shippingservice_test.go`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: RISK
- **Finding**: No persistent data. Address data in-memory only. Log storage encryption depends on K8s node config.
- **Gap**: No persistent data to encrypt. Log encryption depends on infrastructure.
- **Recommendation**: Ensure address data not logged. Enable node-level encryption.
- **Evidence**: `main.go` (no persistence), `tracker.go`, `quote.go`

---

## Evidence Index

### Infrastructure as Code
| File | Questions Referenced |
|------|---------------------|
| `helm-chart/templates/shippingservice.yaml` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q7, OBS-Q2, ENG-Q1, ENG-Q3, API-Q8, STATE-Q5 |
| `helm-chart/values.yaml` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q5, AUTH-Q6, AUTH-Q7, OBS-Q1, STATE-Q5, ENG-Q1 |
| `helm-chart/Chart.yaml` | ENG-Q3 |

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `main.go` | API-Q1, API-Q2, API-Q3, API-Q4, AUTH-Q1, AUTH-Q3, AUTH-Q5, AUTH-Q6, STATE-Q1, STATE-Q2, STATE-Q4, DATA-Q1, DATA-Q6, OBS-Q1, OBS-Q2, OBS-Q3, ENG-Q4 |
| `quote.go` | STATE-Q2, DATA-Q7 |
| `tracker.go` | API-Q4, STATE-Q2, DATA-Q1, DATA-Q4 |
| `shippingservice_test.go` | ENG-Q2, ENG-Q4 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `genproto/demo.pb.go` | API-Q1, API-Q2, API-Q4, API-Q5, AUTH-Q4, DATA-Q1, DATA-Q2, DATA-Q3, DATA-Q5, DISC-Q1, DISC-Q2, DISC-Q3, STATE-Q1 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/ci-pr.yaml` | HITL-Q3, DISC-Q1, ENG-Q2, ENG-Q4 |
| `cloudbuild.yaml` | ENG-Q2, ENG-Q3, HITL-Q3 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `Dockerfile` | AUTH-Q5, ENG-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `go.mod` | API-Q2, OBS-Q1 |