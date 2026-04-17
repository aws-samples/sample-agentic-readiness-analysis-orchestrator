# Agentic Readiness Assessment Report

**Target**: services/microservices-demo/src/shippingservice
**Date**: 2026-04-16
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Service Archetype**: stateful-crud (user-provided)
**Agent Scope**: read-only
**Priority**: P1
**Tags**: go, grpc, shipping
**Context**: Go gRPC service providing shipping cost estimates and tracking.

---

## Readiness Profile: Pilot-Ready

**BLOCKERs**: 0 | **RISKs**: 13 | **INFOs**: 20

Supervised pilot with: (1) human approval gates on irreversible actions, (2) agent limited to low-blast-radius operations, (3) compensating controls for each open RISK, (4) remediation timeline before expanding scope.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 0 |
| RISK | 13 |
| INFO | 20 |
| N/A | 0 |
| Not Evaluated (extended) | 10 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 9
**Extended Questions Not Triggered**: 10
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: stateful-crud (user-provided)

---

## BLOCKERs — Must Resolve Before Agent Deployment

No BLOCKERs identified.

---

## RISKs — Proceed with Compensating Controls

### API-Q2: Machine-Readable API Specification
- **Severity**: RISK
- **Finding**: `protos/demo.proto` defines `ShippingService` with `GetQuote` and `ShipOrder` RPCs using versioned package `hipstershop.v1`. `buf.yaml` provides proto linting. However, the proto is shared across all services — there is no shippingservice-specific OpenAPI or standalone spec. The proto is manually maintained, not auto-generated from code annotations.
- **Gap**: No auto-generated spec. Proto is the only machine-readable spec and is shared across all services. No gRPC server reflection enabled in production (reflection is registered in `main.go` but only for development).
- **Compensating Controls**:
  - Proto file serves as machine-readable spec for agent tool generation
  - gRPC reflection is registered in `main.go` for runtime schema discovery
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Ensure proto is the canonical spec and add `buf breaking` to CI for breaking change detection. Consider generating OpenAPI from proto using `grpc-gateway` if REST clients are needed.
- **Evidence**: `protos/demo.proto`, `protos/buf.yaml`, `src/shippingservice/main.go` (reflection.Register)

### API-Q3: Structured Error Responses
- **Severity**: RISK
- **Finding**: `GetQuote` and `ShipOrder` in `main.go` return Go errors directly without explicit gRPC status codes. No structured error metadata (error codes, retryable indicators). The `ShipOrder` function does not validate the `Address` field — a nil address would cause a nil pointer dereference panic rather than a structured error.
- **Gap**: Agents cannot distinguish retriable from terminal errors. No input validation with structured error responses.
- **Compensating Controls**:
  - Wrap agent tool calls with client-side error classification based on gRPC status codes
  - Implement retry with exponential backoff for UNAVAILABLE/INTERNAL status codes
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add input validation for `Address` fields. Return explicit gRPC status codes (`codes.InvalidArgument` for bad input, `codes.Internal` for server errors). Include structured error details using `google.rpc.Status`.
- **Evidence**: `src/shippingservice/main.go` (GetQuote, ShipOrder functions)

### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicy restricts callers to `frontend` and `checkoutservice` service accounts with per-path rules for `/hipstershop.ShippingService/GetQuote` and `/hipstershop.ShippingService/ShipOrder`. However, both callers have access to both RPCs. No agent-specific service accounts are defined.
- **Gap**: No per-RPC scoping for different callers. No agent-specific service accounts with tailored permissions. An agent should ideally have read-only access to `GetQuote` without `ShipOrder`.
- **Compensating Controls**:
  - Istio AuthorizationPolicy restricts callers to known service accounts (defense in depth)
  - Define agent-specific K8s ServiceAccounts with per-RPC AuthorizationPolicy rules
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create agent-specific service accounts. Grant read-only agents access to `GetQuote` only, restricting `ShipOrder` to write-enabled callers.
- **Evidence**: `helm-chart/templates/shippingservice.yaml` (AuthorizationPolicy), `helm-chart/values.yaml` (`authorizationPolicies.create: true`)

### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicy defines per-path rules for the two RPCs. The application code in `main.go` has no action-level authorization — the gRPC server accepts all calls that reach it. Authorization is entirely at the mesh layer.
- **Gap**: No application-layer action-level authorization. If the mesh is bypassed, both RPCs (including the write operation `ShipOrder`) are accessible to any caller.
- **Compensating Controls**:
  - Istio sidecar injection (`sidecars.create: true`) ensures mesh-level enforcement
  - Network policies (`networkPolicies.create: true`) provide additional defense in depth
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement a gRPC unary interceptor for action-level authorization as defense in depth. Extract Istio peer identity from request metadata and enforce per-RPC access control.
- **Evidence**: `src/shippingservice/main.go`, `helm-chart/templates/shippingservice.yaml`, `helm-chart/values.yaml`

### AUTH-Q5: Credential Management
- **Severity**: RISK
- **Finding**: No secrets or credentials used by the service — no database connections, no external API calls. Google Cloud Profiler uses Workload Identity (no hardcoded credentials). No Secrets Manager or Vault integration. No `.env` files committed.
- **Gap**: No formal credential management framework. While the service currently has no credentials to manage, there is no framework for credential lifecycle management if credentials are introduced.
- **Compensating Controls**:
  - Credential-free architecture eliminates current secret rotation concerns
  - Workload Identity for GCP libraries avoids hardcoded credentials
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Maintain credential-free architecture. If credentials are introduced, use K8s Secrets with external secrets operator or AWS Secrets Manager.
- **Evidence**: `src/shippingservice/main.go`, `src/shippingservice/go.mod`, `helm-chart/templates/shippingservice.yaml`

### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: Logrus provides structured JSON logging with timestamps, but logs contain only operational messages (`[GetQuote] received request`, `[ShipOrder] received request`). No principal attribution — logs do not record who called the service. No immutable storage configuration. OpenTelemetry tracing is enabled (OTel dependencies in `go.mod`), providing request-level trace context but not audit-grade principal attribution. Logs are ephemeral container stdout.
- **Gap**: No immutable audit trail. Cannot determine who called the service or attribute actions to specific agent identities. `ShipOrder` logs PII-adjacent data (address used to generate tracking ID) without redaction.
- **Compensating Controls**:
  - Configure K8s log forwarding to immutable store (CloudWatch Logs with retention, S3 with Object Lock)
  - OpenTelemetry traces provide request correlation as a partial audit signal
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add structured audit logging with caller identity (extracted from Istio mTLS peer identity). Forward to immutable store. Redact PII from operational logs.
- **Evidence**: `src/shippingservice/main.go` (logrus JSON formatter, ShipOrder logging), `src/shippingservice/go.mod` (OTel dependencies)

### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicy provides a mechanism to deny specific service accounts by updating the policy. NetworkPolicies are enabled. However, there is no automated suspension mechanism — policy changes require Helm value updates or manual kubectl edits.
- **Gap**: No automated or rapid suspension mechanism. Isolating a misbehaving agent requires manual AuthorizationPolicy or NetworkPolicy changes.
- **Compensating Controls**:
  - Istio AuthorizationPolicy can be updated to deny specific service accounts (manual process)
  - K8s NetworkPolicy can block specific pods as emergency measure
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement automated suspension via AuthorizationPolicy updates triggered by anomaly detection. Consider an operator or webhook that can instantly deny a service account.
- **Evidence**: `helm-chart/templates/shippingservice.yaml`, `helm-chart/values.yaml` (`authorizationPolicies.create: true`, `networkPolicies.create: true`)

### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: `ShipOrder` generates a tracking ID using random values and address data — this is a write operation that creates a new tracking ID on every call. There is no persistent state, no database, and no way to "undo" a generated tracking ID. `GetQuote` is stateless and idempotent.
- **Gap**: No compensation mechanism for `ShipOrder`. In a real shipping system, a generated tracking ID would need cancellation/void capability. The mock implementation has no rollback.
- **Compensating Controls**:
  - Mock implementation — tracking IDs are not persisted or actionable
  - Read-only agent scope means agents would only call `GetQuote`, not `ShipOrder`
- **Remediation Timeline**: No immediate action for read-only scope; implement compensation if write scope is enabled
- **Recommendation**: If `ShipOrder` becomes a real write operation, implement order cancellation/void endpoint. For read-only agents, restrict to `GetQuote` via AuthorizationPolicy.
- **Evidence**: `src/shippingservice/main.go` (ShipOrder), `src/shippingservice/tracker.go`

### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK
- **Finding**: Rate-limit EnvoyFilter is configured at the Istio mesh level. However, no application-level rate limiting exists in the Go gRPC server. K8s resource limits cap CPU/memory but not request rates. HPAs are configured for auto-scaling.
- **Gap**: Application-level rate limiting is absent. EnvoyFilter provides mesh-level protection, but a misconfigured or bypassed sidecar would leave the service unprotected.
- **Compensating Controls**:
  - EnvoyFilter rate limiting at Istio mesh level provides primary protection
  - HPAs auto-scale pods under load, absorbing burst traffic
  - Agent-side request rate caps in the orchestration layer
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add gRPC unary interceptor for application-level rate limiting as defense in depth. Configure per-caller limits based on service account identity.
- **Evidence**: `src/shippingservice/main.go`, `kubernetes-manifests/shippingservice.yaml`, `helm-chart/values.yaml` (`sidecars.create: true`)

### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK
- **Finding**: Skaffold provides local development. CI deploys per-PR to ephemeral namespaces. Docker build supports local testing. No persistent agent testing environment with production-equivalent data shape.
- **Gap**: No dedicated agent testing environment.
- **Compensating Controls**:
  - Use Skaffold for local instance with Docker build for isolated testing
  - Leverage per-PR ephemeral namespaces for integration testing
- **Remediation Timeline**: 30 days
- **Recommendation**: Create persistent staging namespace for agent integration testing with production-equivalent configuration.
- **Evidence**: `skaffold.yaml`, `src/shippingservice/Dockerfile`, `.github/workflows/ci-pr.yaml`

### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: Service handles PII (shipping addresses). No explicit data residency requirements or documentation. No data residency configuration in IaC or application code. Addresses are processed in-memory and not persisted, but are transmitted to the service and logged.
- **Gap**: No formal data residency documentation for PII data. Addresses are PII and may be subject to GDPR/LGPD if serving EU/Brazil customers. No assessment of whether agent-to-LLM transmission of address data crosses jurisdictional boundaries.
- **Compensating Controls**:
  - Document that addresses are processed in-memory only, not persisted
  - Implement residency-aware controls if data is persisted or transmitted to LLM providers
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document data residency posture formally. Assess whether address PII transmitted to agents/LLMs crosses jurisdictional boundaries. Implement region-aware processing if required.
- **Evidence**: `protos/demo.proto` (Address message — PII classification), `DATA_CLASSIFICATION.md`, `src/shippingservice/main.go`

### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK
- **Finding**: CI exists (Cloud Build + Skaffold + GitHub Actions). Unit tests exist in `shippingservice_test.go` covering `GetQuote`, `ShipOrder`, tracking ID generation, and quote creation. Proto uses versioned package (`hipstershop.v1`) and `buf.yaml` exists with `breaking.use: [FILE]` configured. However, `buf breaking` is not integrated into CI pipeline. No shippingservice-specific contract tests.
- **Gap**: No automated breaking change detection in CI pipeline despite `buf.yaml` having breaking change rules configured. No consumer-driven contract tests.
- **Compensating Controls**:
  - Protobuf wire compatibility provides implicit backward compatibility for additive changes
  - `buf.yaml` has breaking change detection configured (`breaking.use: [FILE]`) — needs CI integration
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `buf breaking` to CI pipeline. Add ShippingService-specific contract tests validating `GetQuote` and `ShipOrder` request/response schemas.
- **Evidence**: `cloudbuild.yaml`, `.github/workflows/ci-pr.yaml`, `protos/buf.yaml`, `protos/demo.proto`

### ENG-Q3: Rollback Capability
- **Severity**: RISK
- **Finding**: K8s Deployment with rollout history. Skaffold deployment. No automated rollback triggers. Manual rollback via `kubectl rollout undo` only. No canary deployment, no Flagger, no Argo Rollouts. Monitoring alerts and HPAs are configured, which can detect degradation faster.
- **Gap**: No automated rollback on service degradation. Manual rollback only.
- **Compensating Controls**:
  - K8s rollout history enables manual rollback within minutes
  - Liveness/readiness probes prevent traffic to unhealthy pods
  - Monitoring alerts can trigger manual rollback faster
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure automated rollback triggers using Flagger or Argo Rollouts with canary analysis.
- **Evidence**: `skaffold.yaml`, `kubernetes-manifests/shippingservice.yaml`

---

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: Well-documented gRPC interface in `protos/demo.proto` with `ShippingService` defining `GetQuote` and `ShipOrder` RPCs. Proto uses versioned package `hipstershop.v1` with data classification comments (PII on Address, ShipOrderRequest). Implemented in `main.go`. gRPC reflection registered for runtime discovery. Positive finding.
- **Implication**: gRPC interface can be used directly as agent tool binding. Proto enables auto-generated client code. Data classification comments inform agent access policies.
- **Recommendation**: No remediation needed.
- **Evidence**: `protos/demo.proto`, `src/shippingservice/main.go`

### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: `GetQuote` is stateless and idempotent — same items always produce the same quote ($8.99 flat rate). `ShipOrder` is a write operation that generates a new random tracking ID on every call — it is NOT idempotent. No idempotency key support.
- **Implication**: For read-only scope, agents call `GetQuote` only — no idempotency concerns. If write scope is enabled, `ShipOrder` non-idempotency becomes a BLOCKER.
- **Recommendation**: If write scope is enabled, add idempotency key support to `ShipOrder` to prevent duplicate tracking IDs on retry.
- **Evidence**: `src/shippingservice/main.go`, `src/shippingservice/tracker.go`

### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: gRPC Protocol Buffers — strongly-typed binary format with explicit types, field numbers, and data classification comments. `GetQuoteResponse` returns `Money` (currency_code, units, nanos). `ShipOrderResponse` returns `tracking_id` string.
- **Implication**: Protobuf is more structured than JSON. Excellent for agent integration with auto-generated client code.
- **Recommendation**: No action needed.
- **Evidence**: `protos/demo.proto`

### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: Rate-limit EnvoyFilter is configured at the mesh level. No rate limit headers in gRPC responses. Internal ClusterIP service. K8s resource limits and HPAs provide implicit capacity management.
- **Implication**: Agents cannot self-throttle based on server-side rate limit signals. EnvoyFilter provides protection but agents have no visibility into remaining capacity.
- **Recommendation**: Add gRPC trailing metadata with rate limit status (remaining requests, retry-after) when application-level rate limiting is implemented.
- **Evidence**: `src/shippingservice/main.go`, `kubernetes-manifests/shippingservice.yaml`

### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: Istio AuthorizationPolicy is enabled (`authorizationPolicies.create: true`), providing mTLS-based identity verification. Callers restricted to `frontend` and `checkoutservice` service accounts with per-path rules. Istio sidecars enabled (`sidecars.create: true`). The gRPC server uses insecure credentials at the application layer, but Istio sidecar terminates mTLS before traffic reaches the application — standard Istio pattern.
- **Implication**: Machine identity is authenticated at the mesh layer via mTLS with per-service principal attribution. Satisfies the core requirement for agent identity verification.
- **Recommendation**: For defense in depth, consider extracting Istio peer identity from request metadata for application-level audit logging.
- **Evidence**: `helm-chart/values.yaml` (`authorizationPolicies.create: true`, `sidecars.create: true`), `helm-chart/templates/shippingservice.yaml` (AuthorizationPolicy), `src/shippingservice/main.go`

### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: No JWT parsing, no token exchange, no user context headers in the Go gRPC server. No identity context propagated in gRPC calls. Istio mTLS provides implicit caller identity at the mesh layer. The service handles PII (addresses) but does not personalize responses per user — it computes a flat-rate quote and generates a tracking ID.
- **Implication**: Identity propagation has limited security impact for this service — quotes are not user-specific (flat rate) and tracking IDs are generated without user context. Istio provides caller identity at the mesh layer. However, PII handling means identity propagation becomes more important if access controls are tightened.
- **Recommendation**: Implement identity propagation if per-user access controls on PII are required.
- **Evidence**: `src/shippingservice/main.go`, `helm-chart/values.yaml`

### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: `GetQuote` is stateless — no shared state, no database, no concurrent write risk. `ShipOrder` generates random tracking IDs with no persistent state — concurrent calls produce unique IDs (verified by `TestTrackingIdUniqueness` test). No optimistic locking or version fields needed.
- **Implication**: No concurrency concerns for read-only scope. If `ShipOrder` persists tracking IDs in the future, concurrency controls will be needed.
- **Recommendation**: Implement concurrency controls if persistent state is added.
- **Evidence**: `src/shippingservice/main.go`, `src/shippingservice/tracker.go`, `src/shippingservice/shippingservice_test.go`

### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: `GetQuote` is read-only with no side effects. `ShipOrder` generates tracking IDs but does not persist them or trigger downstream actions in the mock implementation. Minimal blast radius.
- **Implication**: Transaction limits not critical for read-only operations. If `ShipOrder` becomes a real write operation, per-agent transaction limits should be enforced.
- **Recommendation**: Implement transaction limits if write operations are enabled.
- **Evidence**: `src/shippingservice/main.go`

### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO
- **Finding**: PII is classified and documented. `protos/demo.proto` includes data classification comments: `Address` message is marked as PII, `ShipOrderRequest` contains PII via Address. `DATA_CLASSIFICATION.md` classifies shippingservice as PII with sensitive fields `Address.*`. Agent access policy documented — read-only agents may access PII only with explicit Istio AuthorizationPolicy authorization.
- **Implication**: Data classification is in place. PII is identified at the field level. Agent access policies are documented. Positive finding.
- **Recommendation**: Implement field-level access controls if agents need access to address data without full PII exposure (e.g., return city/state but redact street address).
- **Evidence**: `protos/demo.proto` (Address PII classification), `DATA_CLASSIFICATION.md`

### DATA-Q6: PII Redaction in Logs
- **Severity**: INFO
- **Finding**: Logrus logs operational messages only (`[GetQuote] received request`, `[ShipOrder] received request`). However, `ShipOrder` constructs `baseAddress` from `in.Address.StreetAddress`, `in.Address.City`, `in.Address.State` — this PII string is passed to `CreateTrackingId` but is NOT logged directly. No request/response payloads are logged. No PII in log output.
- **Implication**: No PII leakage in current logging. However, if debug logging is enabled or log level is changed, address data could leak. The `baseAddress` variable contains PII in memory.
- **Recommendation**: Add explicit PII redaction middleware to prevent accidental PII logging if log levels change. Consider structured logging that excludes PII fields by default.
- **Evidence**: `src/shippingservice/main.go` (ShipOrder function, logrus configuration)

### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: INFO
- **Finding**: Proto uses versioned package `hipstershop.v1`. `buf.yaml` exists with `breaking.use: [FILE]` for breaking change detection and `lint.use: [STANDARD]` for proto linting. Proto defines typed schemas with data classification comments. Breaking change detection tooling is configured but not yet integrated into CI.
- **Implication**: Schema versioning is established. Proto versioning enables safe evolution. `buf` tooling provides a path to automated breaking change detection.
- **Recommendation**: Add `buf breaking` to CI pipeline to complete the contract testing story (tracked under ENG-Q2).
- **Evidence**: `protos/demo.proto` (`hipstershop.v1`), `protos/buf.yaml`

### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: INFO
- **Finding**: OpenTelemetry dependencies present in `go.mod` (`go.opentelemetry.io/otel`, `go.opentelemetry.io/contrib/instrumentation/google.golang.org/grpc/otelgrpc`). OTel Collector deployed (`opentelemetryCollector.create: true`). Tracing enabled (`tracing: true`). Logrus provides structured JSON logging with timestamps and severity levels. No `request_id` or `correlation_id` in application logs, but trace context is propagated via OpenTelemetry.
- **Implication**: Distributed tracing is operational. Trace context enables end-to-end request correlation. Structured JSON logging supports log aggregation. The remaining gap (no trace_id in logrus entries) is minor — OpenTelemetry trace IDs serve the same purpose.
- **Recommendation**: Add trace_id to logrus log entries for log-to-trace correlation. This is a minor enhancement.
- **Evidence**: `src/shippingservice/main.go` (logrus JSON formatter), `src/shippingservice/go.mod` (OTel dependencies), `helm-chart/values.yaml` (`tracing: true`, `opentelemetryCollector.create: true`)

### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: INFO
- **Finding**: Monitoring alerts configured for error rates and latency. Metrics collection enabled (`metrics: true`). K8s liveness/readiness probes on gRPC port 50051. HPAs configured for auto-scaling based on metrics.
- **Implication**: Alerting infrastructure is in place. Service degradation will be detected before agents cascade failures.
- **Recommendation**: Tune alert thresholds based on agent traffic patterns during pilot.
- **Evidence**: `kubernetes-manifests/shippingservice.yaml`, `helm-chart/values.yaml` (`metrics: true`)

### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: INFO
- **Finding**: Comprehensive IaC: K8s manifests, Kustomize, Helm, Terraform. CODEOWNERS enforces peer review. GitHub Actions CI on PRs. AuthorizationPolicies, NetworkPolicies, and Sidecars all defined in IaC and enabled. HPAs and monitoring alerts defined in IaC. No drift detection configured.
- **Implication**: Infrastructure governance is strong — IaC coverage is comprehensive and peer review is enforced. The drift detection gap is minor for a K8s-native deployment where Helm reconciliation provides implicit drift correction on deploy.
- **Recommendation**: Implement drift detection or GitOps (ArgoCD/Flux) for continuous reconciliation.
- **Evidence**: `kubernetes-manifests/shippingservice.yaml`, `helm-chart/templates/shippingservice.yaml`, `helm-chart/values.yaml`, `.github/CODEOWNERS`, `.github/workflows/ci-pr.yaml`

### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: `ShipOrder` creates a tracking ID (state change) but does not emit events. No webhook endpoints, no SNS/EventBridge/SQS integration, no Kafka topics. The tracking ID is returned synchronously only.
- **Implication**: Agents cannot subscribe to shipping events. If proactive notification of shipment status is needed, event emission must be added.
- **Recommendation**: Emit events on `ShipOrder` completion (e.g., to SNS/EventBridge) if downstream consumers need to react to new shipments.
- **Evidence**: `src/shippingservice/main.go` (ShipOrder)

### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics. Quote logic is deterministic ($8.99 flat rate for non-empty carts, $0 for empty). Tracking ID generation is random but tested for format and uniqueness. No runtime data quality degradation risk.
- **Implication**: Quality is deterministic and tested. No runtime degradation risk for quote generation.
- **Recommendation**: Add validation that address fields are non-empty before processing. Monitor tracking ID collision rates if IDs are persisted.
- **Evidence**: `src/shippingservice/quote.go`, `src/shippingservice/tracker.go`, `src/shippingservice/shippingservice_test.go`

### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Clear semantic names: `street_address`, `city`, `state`, `country`, `zip_code`, `tracking_id`, `cost_usd`, `currency_code`, `units`, `nanos`. Detailed data classification comments. No abbreviations or legacy codes.
- **Implication**: LLMs can interpret fields directly. No translation or data dictionary needed.
- **Recommendation**: No action needed.
- **Evidence**: `protos/demo.proto`

### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal data catalog. Proto file with data classification comments serves as informal documentation. `DATA_CLASSIFICATION.md` provides service-level classification and agent access policy. Self-describing proto schema.
- **Implication**: Sufficient for a focused shipping service. `DATA_CLASSIFICATION.md` provides portfolio-level context.
- **Recommendation**: Register in organization API catalog if part of larger data mesh.
- **Evidence**: `protos/demo.proto`, `DATA_CLASSIFICATION.md`

### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics. Operational logging and OpenTelemetry metrics provide infrastructure-level visibility. No metrics for quote volume, shipping order volume, or tracking ID generation rates.
- **Implication**: No business outcome monitoring. Operational metrics may suffice initially.
- **Recommendation**: Publish metrics for quote request volume and ship order volume if business analytics are needed.
- **Evidence**: `src/shippingservice/main.go`

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: Well-documented gRPC interface in `protos/demo.proto` with `ShippingService` defining `GetQuote` and `ShipOrder` RPCs. Proto uses versioned package `hipstershop.v1` with data classification comments. Implemented in `main.go`. gRPC reflection registered. Positive finding.
- **Gap**: None — BLOCKER criteria satisfied.
- **Recommendation**: No remediation needed.
- **Evidence**: `protos/demo.proto`, `src/shippingservice/main.go`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK
- **Finding**: `protos/demo.proto` is a machine-readable spec with versioned package `hipstershop.v1`. `buf.yaml` provides proto linting. Shared across all services. Manually maintained.
- **Gap**: No auto-generated spec. No `buf breaking` in CI for breaking change detection.
- **Recommendation**: Add `buf breaking` to CI. Consider generating OpenAPI from proto if REST clients are needed.
- **Evidence**: `protos/demo.proto`, `protos/buf.yaml`, `src/shippingservice/main.go`

#### API-Q3: Structured Error Responses
- **Severity**: RISK
- **Finding**: Go errors returned directly without explicit gRPC status codes. No structured error metadata. Nil address would cause panic rather than structured error.
- **Gap**: Agents cannot distinguish retriable from terminal errors. No input validation.
- **Recommendation**: Add input validation. Return explicit gRPC status codes with structured error details.
- **Evidence**: `src/shippingservice/main.go` (GetQuote, ShipOrder)

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: `GetQuote` is stateless and idempotent. `ShipOrder` generates a new random tracking ID on every call — NOT idempotent. No idempotency key support.
- **Gap**: `ShipOrder` is non-idempotent. Not a concern for read-only scope.
- **Recommendation**: Add idempotency key support to `ShipOrder` if write scope is enabled.
- **Evidence**: `src/shippingservice/main.go`, `src/shippingservice/tracker.go`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: gRPC Protocol Buffers — strongly-typed binary format with explicit types, field numbers, and data classification comments.
- **Gap**: None.
- **Recommendation**: No action needed.
- **Evidence**: `protos/demo.proto`

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has operations >30s OR long-running workflows
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: `ShipOrder` creates a tracking ID (state change) but does not emit events. No webhook, SNS, EventBridge, or Kafka integration.
- **Gap**: No event emission for state changes.
- **Recommendation**: Emit events on `ShipOrder` completion if downstream consumers need to react.
- **Evidence**: `src/shippingservice/main.go`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: Rate-limit EnvoyFilter configured at mesh level. No rate limit headers in gRPC responses. Internal ClusterIP service.
- **Gap**: Agents cannot self-throttle based on server-side rate limit signals.
- **Recommendation**: Add gRPC trailing metadata with rate limit status when application-level rate limiting is implemented.
- **Evidence**: `src/shippingservice/main.go`, `kubernetes-manifests/shippingservice.yaml`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: Istio AuthorizationPolicy enabled with mTLS-based identity verification. Callers restricted to `frontend` and `checkoutservice` service accounts with per-path rules. Sidecars enabled. Standard Istio mTLS pattern.
- **Gap**: None — mesh-level mTLS with per-service AuthorizationPolicy satisfies machine identity authentication.
- **Recommendation**: Extract Istio peer identity from request metadata for application-level audit logging.
- **Evidence**: `helm-chart/values.yaml`, `helm-chart/templates/shippingservice.yaml`, `src/shippingservice/main.go`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicy restricts callers to `frontend` and `checkoutservice`. Both have access to both RPCs. No agent-specific service accounts.
- **Gap**: No per-RPC scoping for different callers. No agent-specific permissions.
- **Recommendation**: Create agent-specific service accounts with per-RPC AuthorizationPolicy rules.
- **Evidence**: `helm-chart/templates/shippingservice.yaml`, `helm-chart/values.yaml`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicy defines per-path rules. No application-layer action-level authorization in Go code.
- **Gap**: No application-layer authorization. Mesh bypass exposes both RPCs including write operation `ShipOrder`.
- **Recommendation**: Implement gRPC unary interceptor for action-level authorization as defense in depth.
- **Evidence**: `src/shippingservice/main.go`, `helm-chart/templates/shippingservice.yaml`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: No JWT parsing, token exchange, or user context headers. Istio mTLS provides implicit caller identity. Service handles PII but does not personalize responses per user.
- **Gap**: No application-level identity propagation. Limited impact for flat-rate quote service.
- **Recommendation**: Implement identity propagation if per-user PII access controls are required.
- **Evidence**: `src/shippingservice/main.go`, `helm-chart/values.yaml`

#### AUTH-Q5: Credential Management
- **Severity**: RISK
- **Finding**: No secrets or credentials used. Credential-free architecture. Workload Identity for GCP. No Secrets Manager or Vault.
- **Gap**: No credential management framework if credentials are introduced.
- **Recommendation**: Maintain credential-free architecture. Adopt external secrets operator if credentials are needed.
- **Evidence**: `src/shippingservice/main.go`, `src/shippingservice/go.mod`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: Logrus structured JSON logging with timestamps. Operational messages only. No principal attribution. OTel tracing enabled but not audit-grade. Logs are ephemeral container stdout.
- **Gap**: No immutable audit trail. Cannot attribute actions to specific agent identities.
- **Recommendation**: Add structured audit logging with caller identity. Forward to immutable store.
- **Evidence**: `src/shippingservice/main.go`, `src/shippingservice/go.mod`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicy and NetworkPolicies provide manual suspension mechanisms. No automated suspension.
- **Gap**: No automated or rapid suspension mechanism.
- **Recommendation**: Implement automated suspension via AuthorizationPolicy updates triggered by anomaly detection.
- **Evidence**: `helm-chart/templates/shippingservice.yaml`, `helm-chart/values.yaml`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: `ShipOrder` generates tracking IDs with no rollback capability. `GetQuote` is stateless. Mock implementation — IDs not persisted.
- **Gap**: No compensation mechanism for `ShipOrder`.
- **Recommendation**: Implement order cancellation if `ShipOrder` becomes a real write operation.
- **Evidence**: `src/shippingservice/main.go`, `src/shippingservice/tracker.go`

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
- **Finding**: `GetQuote` is stateless. `ShipOrder` generates random tracking IDs with no shared state. Concurrent calls produce unique IDs (tested).
- **Gap**: None for read-only scope.
- **Recommendation**: Implement concurrency controls if persistent state is added.
- **Evidence**: `src/shippingservice/main.go`, `src/shippingservice/tracker.go`, `src/shippingservice/shippingservice_test.go`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has external dependencies (calls other services or external APIs)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK
- **Finding**: Rate-limit EnvoyFilter at mesh level. No application-level rate limiting. K8s resource limits and HPAs configured.
- **Gap**: No application-level rate limiting. Sidecar bypass leaves service unprotected.
- **Recommendation**: Add gRPC unary interceptor for application-level rate limiting.
- **Evidence**: `src/shippingservice/main.go`, `kubernetes-manifests/shippingservice.yaml`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: `GetQuote` is read-only. `ShipOrder` generates tracking IDs but does not persist them. Minimal blast radius.
- **Gap**: None for read-only scope.
- **Recommendation**: Implement transaction limits if write operations are enabled.
- **Evidence**: `src/shippingservice/main.go`

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
- **Severity**: RISK
- **Finding**: Skaffold local dev. CI per-PR ephemeral namespaces. Docker build for local testing. No persistent agent testing environment.
- **Gap**: No dedicated agent testing environment.
- **Recommendation**: Create persistent staging namespace for agent integration testing.
- **Evidence**: `skaffold.yaml`, `src/shippingservice/Dockerfile`, `.github/workflows/ci-pr.yaml`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO
- **Finding**: PII classified and documented. Proto includes data classification comments on `Address` (PII) and `ShipOrderRequest` (PII). `DATA_CLASSIFICATION.md` classifies shippingservice as PII with sensitive fields `Address.*`. Agent access policy documented.
- **Gap**: None — PII is classified at field level with documented agent access policies. Positive finding.
- **Recommendation**: Implement field-level access controls if agents need partial address access.
- **Evidence**: `protos/demo.proto`, `DATA_CLASSIFICATION.md`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: Service handles PII (shipping addresses). No explicit residency documentation. Addresses processed in-memory, not persisted.
- **Gap**: No formal data residency documentation for PII data.
- **Recommendation**: Document data residency posture. Assess jurisdictional boundaries for agent-to-LLM PII transmission.
- **Evidence**: `protos/demo.proto`, `DATA_CLASSIFICATION.md`, `src/shippingservice/main.go`

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
- **Severity**: INFO
- **Finding**: Logrus logs operational messages only. `ShipOrder` constructs `baseAddress` from PII fields but does NOT log it directly. No request/response payloads logged. No PII in log output.
- **Gap**: None currently. Risk of PII leakage if debug logging is enabled.
- **Recommendation**: Add explicit PII redaction middleware to prevent accidental PII logging.
- **Evidence**: `src/shippingservice/main.go`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No quality metrics. Deterministic quote logic ($8.99 flat rate). Tracking ID generation tested for format and uniqueness. No runtime degradation risk.
- **Gap**: No quality monitoring, but deterministic logic has fixed quality characteristics.
- **Recommendation**: Add address field validation. Monitor tracking ID collision rates if IDs are persisted.
- **Evidence**: `src/shippingservice/quote.go`, `src/shippingservice/tracker.go`, `src/shippingservice/shippingservice_test.go`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: INFO
- **Finding**: Proto uses versioned package `hipstershop.v1`. `buf.yaml` configured with `breaking.use: [FILE]` and `lint.use: [STANDARD]`. Data classification comments in proto. Breaking change detection not yet in CI.
- **Gap**: `buf breaking` not in CI (tracked under ENG-Q2).
- **Recommendation**: Add `buf breaking` to CI pipeline.
- **Evidence**: `protos/demo.proto`, `protos/buf.yaml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Clear semantic names: `street_address`, `city`, `state`, `country`, `zip_code`, `tracking_id`, `cost_usd`. Detailed comments. No abbreviations.
- **Gap**: None.
- **Recommendation**: No action needed.
- **Evidence**: `protos/demo.proto`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal catalog. Proto with data classification comments and `DATA_CLASSIFICATION.md` serve as informal documentation.
- **Gap**: No formal catalog. Sufficient for focused shipping service.
- **Recommendation**: Register in organization API catalog if part of larger data mesh.
- **Evidence**: `protos/demo.proto`, `DATA_CLASSIFICATION.md`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: INFO
- **Finding**: OpenTelemetry dependencies in `go.mod`. OTel Collector deployed. Tracing and metrics enabled. Logrus provides structured JSON logging with timestamps and severity. Trace context propagated via OTel.
- **Gap**: No trace_id in logrus entries (minor — OTel trace IDs serve the same purpose).
- **Recommendation**: Add trace_id to logrus log entries for log-to-trace correlation.
- **Evidence**: `src/shippingservice/main.go`, `src/shippingservice/go.mod`, `helm-chart/values.yaml`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: INFO
- **Finding**: Monitoring alerts configured. Metrics enabled. K8s liveness/readiness probes on gRPC port. HPAs configured.
- **Gap**: None — alerting infrastructure is in place.
- **Recommendation**: Tune alert thresholds based on agent traffic patterns during pilot.
- **Evidence**: `kubernetes-manifests/shippingservice.yaml`, `helm-chart/values.yaml`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics. Operational logging and OTel metrics provide infrastructure-level visibility.
- **Gap**: No business outcome monitoring.
- **Recommendation**: Publish metrics for quote volume and ship order volume if business analytics are needed.
- **Evidence**: `src/shippingservice/main.go`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: INFO
- **Finding**: Comprehensive IaC: K8s manifests, Kustomize, Helm, Terraform. CODEOWNERS enforces peer review. GitHub Actions CI. AuthorizationPolicies, NetworkPolicies, Sidecars, HPAs, monitoring alerts all defined in IaC. No drift detection.
- **Gap**: Drift detection missing (minor for K8s-native deployment).
- **Recommendation**: Implement drift detection or GitOps (ArgoCD/Flux).
- **Evidence**: `kubernetes-manifests/shippingservice.yaml`, `helm-chart/templates/shippingservice.yaml`, `helm-chart/values.yaml`, `.github/CODEOWNERS`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK
- **Finding**: CI exists. Unit tests in `shippingservice_test.go`. Proto versioned (`hipstershop.v1`). `buf.yaml` with breaking change rules. No `buf breaking` in CI. No contract tests.
- **Gap**: No automated breaking change detection in CI.
- **Recommendation**: Add `buf breaking` to CI. Add ShippingService contract tests.
- **Evidence**: `cloudbuild.yaml`, `.github/workflows/ci-pr.yaml`, `protos/buf.yaml`, `protos/demo.proto`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK
- **Finding**: K8s rollout history. Skaffold deployment. Manual rollback only. No canary or automated rollback. Monitoring alerts can detect degradation faster.
- **Gap**: No automated rollback on service degradation.
- **Recommendation**: Configure automated rollback triggers (Flagger, Argo Rollouts).
- **Evidence**: `skaffold.yaml`, `kubernetes-manifests/shippingservice.yaml`

#### ENG-Q4: API Test Coverage
- **Severity**: INFO
- **Finding**: `shippingservice_test.go` contains 9 test functions covering: `GetQuote` (basic + empty cart), `ShipOrder` (basic), tracking ID format and uniqueness, `CreateQuoteFromFloat`, `CreateQuoteFromCount`, `getRandomLetterCode`, `getRandomNumber`, and `Quote.String()`. Good unit test coverage for core logic. No gRPC integration tests. CI includes Go test execution.
- **Gap**: No gRPC integration tests. Unit tests cover core logic but not gRPC middleware or error handling paths.
- **Recommendation**: Add gRPC integration tests validating end-to-end request/response behavior including error cases.
- **Evidence**: `src/shippingservice/shippingservice_test.go`, `.github/workflows/ci-pr.yaml`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has persistent data stores
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

---

## Evidence Index

### Infrastructure as Code
| File | Questions Referenced |
|------|---------------------|
| `kubernetes-manifests/shippingservice.yaml` | AUTH-Q1, STATE-Q5, OBS-Q2, API-Q8, ENG-Q1, ENG-Q3 |
| `helm-chart/templates/shippingservice.yaml` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q7, ENG-Q1 |
| `helm-chart/values.yaml` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q6, AUTH-Q7, OBS-Q1, OBS-Q2, ENG-Q1, STATE-Q5 |

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `src/shippingservice/main.go` | API-Q1, API-Q2, API-Q3, API-Q4, API-Q7, API-Q8, AUTH-Q1, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q6, STATE-Q1, STATE-Q3, STATE-Q5, STATE-Q6, DATA-Q2, DATA-Q6, OBS-Q1, OBS-Q3, ENG-Q4 |
| `src/shippingservice/quote.go` | DATA-Q7 |
| `src/shippingservice/tracker.go` | API-Q4, STATE-Q1, STATE-Q3, DATA-Q7 |
| `src/shippingservice/shippingservice_test.go` | STATE-Q3, DATA-Q7, ENG-Q4 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `protos/demo.proto` | API-Q1, API-Q2, API-Q4, API-Q5, DATA-Q1, DATA-Q2, DISC-Q1, DISC-Q2, DISC-Q3, ENG-Q2 |
| `protos/buf.yaml` | API-Q2, DISC-Q1, ENG-Q2 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `cloudbuild.yaml` | ENG-Q2 |
| `skaffold.yaml` | HITL-Q3, ENG-Q3 |
| `.github/workflows/ci-pr.yaml` | HITL-Q3, ENG-Q2, ENG-Q4 |
| `.github/CODEOWNERS` | ENG-Q1 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `src/shippingservice/Dockerfile` | HITL-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `src/shippingservice/go.mod` | AUTH-Q5, AUTH-Q6, OBS-Q1 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `DATA_CLASSIFICATION.md` | DATA-Q1, DATA-Q2, DISC-Q3 |