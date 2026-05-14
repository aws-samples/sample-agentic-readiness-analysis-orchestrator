# Agentic Readiness Analysis Report

**Target**: services/microservices-demo/src/checkoutservice
**Date**: 2026-04-16
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**Repository Type**: application
**Service Archetype**: orchestrator (user-provided)
**Agent Scope**: read-only
**Priority**: P0
**Tags**: go, grpc, orchestrator, critical-path
**Context**: Go gRPC service orchestrating the checkout workflow.

---

## Readiness Profile: Pilot-Ready

**BLOCKERs**: 0 | **RISKs**: 17 | **INFOs**: 20

Supervised pilot with: (1) human approval gates on irreversible actions, (2) agent limited to low-blast-radius operations, (3) compensating controls for each open RISK, (4) remediation timeline before expanding scope.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 0 |
| RISK | 17 |
| INFO | 20 |
| N/A | 0 |
| Not Evaluated (extended) | 6 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 13
**Extended Questions Not Triggered**: 6
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: orchestrator (user-provided)

---

## BLOCKERs — Must Resolve Before Agent Deployment

No BLOCKERs identified.

---

## RISKs — Proceed with Compensating Controls

### API-Q3: Structured Error Responses
- **Severity**: RISK
- **Finding**: `PlaceOrder` uses `status.Errorf(codes.Internal, err.Error())` for most errors — wrapping internal error strings into gRPC status codes. Some differentiation exists: `codes.Unavailable` for shipping errors, `codes.Internal` for payment and cart failures. However, error messages expose internal implementation details (e.g., `"failed to charge card: %+v"`) and no structured error metadata (retryable boolean, error category) is returned.
- **Gap**: Agents cannot distinguish retriable from terminal errors beyond gRPC status codes. Internal error details leak in messages. No structured error body with retryable indicators.
- **Compensating Controls**:
  - Wrap agent tool calls with client-side error classification based on gRPC status codes
  - Implement retry with exponential backoff for UNAVAILABLE status codes; treat INTERNAL as non-retriable
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Refactor error handling to use specific gRPC status codes (e.g., `INVALID_ARGUMENT` for bad input, `FAILED_PRECONDITION` for empty cart, `UNAVAILABLE` for downstream failures). Add structured error details using `google.rpc.Status` with retryable metadata. Sanitize internal error messages.
- **Evidence**: `src/checkoutservice/main.go` (PlaceOrder, chargeCard, shipOrder, prepareOrderItemsAndShippingQuoteFromCart)

### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicy restricts callers to `frontend` service account only, with access limited to `/hipstershop.CheckoutService/PlaceOrder` on port 5050. This is well-scoped for the single RPC. However, no agent-specific service accounts are defined. Any agent would need to call through the frontend or have a new AuthorizationPolicy entry.
- **Gap**: No agent-specific service accounts with tailored permissions. Only `frontend` is authorized.
- **Compensating Controls**:
  - Istio AuthorizationPolicy restricts callers to known service accounts (defense in depth)
  - NetworkPolicy further restricts ingress to frontend pods only
  - Define agent-specific K8s ServiceAccounts and add them to the AuthorizationPolicy
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create agent-specific service accounts with per-RPC AuthorizationPolicy rules. For read-only agents, consider adding a read-only query RPC (e.g., `GetOrderStatus`) and scoping agent access to that RPC only.
- **Evidence**: `helm-chart/templates/checkoutservice.yaml` (AuthorizationPolicy section), `helm-chart/values.yaml` (`authorizationPolicies.create: true`)

### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicy defines per-path rules restricting access to `/hipstershop.CheckoutService/PlaceOrder` from `frontend` only. However, the application code itself has no action-level authorization — the gRPC server accepts all calls that reach it. Authorization is entirely at the mesh layer.
- **Gap**: No application-layer action-level authorization. If the mesh is bypassed, all RPCs are accessible to any caller.
- **Compensating Controls**:
  - Istio sidecar injection (`sidecars.create: true`) ensures mesh-level enforcement
  - Network policies (`networkPolicies.create: true`) provide additional defense in depth
  - Sidecar egress is scoped to only the 6 downstream services + OTel collector
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement a gRPC server interceptor for action-level authorization as defense in depth beyond the mesh layer. Extract Istio peer identity from request headers for application-level validation.
- **Evidence**: `src/checkoutservice/main.go`, `helm-chart/templates/checkoutservice.yaml`, `helm-chart/values.yaml`

### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: No audit logging exists. Logrus logs operational messages only (order placement, payment success, email confirmation). Logs include `user_id` and `email` in plain text — PII leakage concern. No principal attribution (which service account called PlaceOrder). Logs are ephemeral container stdout with no immutable storage configuration. OpenTelemetry tracing is enabled (`ENABLE_TRACING=1`), providing request-level trace context but not audit-grade principal attribution.
- **Gap**: No immutable audit trail. Cannot determine which caller (agent or human) initiated a checkout. PII (email, user_id) logged without redaction.
- **Compensating Controls**:
  - Configure K8s log forwarding to immutable store (e.g., CloudWatch Logs with retention policy, S3 with Object Lock)
  - OpenTelemetry traces provide request correlation as a partial audit signal
  - Istio access logs capture caller identity at the mesh layer
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add structured audit logging with caller identity (extracted from Istio mTLS peer identity). Forward to immutable store. Redact PII from operational logs (see DATA-Q6).
- **Evidence**: `src/checkoutservice/main.go` (logrus with no audit fields), `helm-chart/values.yaml` (`tracing: true`)

### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicy provides a mechanism to deny specific service accounts by updating the policy. NetworkPolicies are enabled. However, there is no automated suspension mechanism — policy changes require Helm value updates or manual kubectl edits. No API key revocation, no service account disable endpoint.
- **Gap**: No automated or rapid suspension mechanism. Isolating a misbehaving agent requires manual AuthorizationPolicy or NetworkPolicy changes.
- **Compensating Controls**:
  - Istio AuthorizationPolicy can be updated to deny specific service accounts (manual process)
  - K8s NetworkPolicy can block specific pods as emergency measure
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement automated suspension via AuthorizationPolicy updates triggered by anomaly detection. Consider an operator or webhook that can instantly deny a service account.
- **Evidence**: `helm-chart/templates/checkoutservice.yaml`, `helm-chart/values.yaml` (`authorizationPolicies.create: true`, `networkPolicies.create: true`)

### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: `PlaceOrder` executes a multi-step workflow: (1) get cart, (2) get product details + convert currency, (3) get shipping quote + convert currency, (4) charge card, (5) ship order, (6) empty cart, (7) send email. If step 5 (shipping) fails after step 4 (payment) succeeds, the card is charged but no shipment occurs. No saga pattern, no compensating transactions, no explicit undo endpoints. Email failure is swallowed with a warning log.
- **Gap**: No compensation for partial failures in the checkout workflow. Payment charge is not reversed if shipping fails. Cart is emptied even if email confirmation fails.
- **Compensating Controls**:
  - Read-only agent scope means agents do not directly trigger PlaceOrder
  - Document the partial failure risk for agent integration teams
  - Implement manual refund process for payment-without-shipment scenarios
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement saga pattern with compensating transactions: if `shipOrder` fails after `chargeCard` succeeds, issue a refund via `paymentservice`. If `emptyCart` fails, retry asynchronously. Consider Step Functions or a workflow engine for orchestration.
- **Evidence**: `src/checkoutservice/main.go` (PlaceOrder function — sequential steps with no compensation)

### STATE-Q2: Queryable Current State
- **Severity**: RISK
- **Finding**: CheckoutService exposes only `PlaceOrder` — a write-only RPC. No query endpoints for order status, checkout state, or order history. The service is stateless (no database) and delegates state to downstream services (cart, payment, shipping). An agent cannot inspect the current state of a checkout before or after placing an order.
- **Gap**: No read endpoints. Agents cannot query order status or verify checkout state.
- **Compensating Controls**:
  - Cart state is queryable via `cartservice.GetCart`
  - Order results are returned in the `PlaceOrderResponse`
  - Agent can query downstream services individually for state
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a `GetOrderStatus` or `PreviewOrder` RPC that returns the current cart contents, shipping quote, and total without executing the checkout. This enables agents to verify state before committing.
- **Evidence**: `protos/demo.proto` (CheckoutService has only PlaceOrder), `src/checkoutservice/main.go`

### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK
- **Finding**: CheckoutService calls 6 downstream services (cart, product catalog, currency, shipping, payment, email) with no circuit breakers, no retry logic, and no timeout configurations on gRPC client calls. `mustConnGRPC` uses a 3-second connection timeout but no per-call deadlines. `convertCurrency` uses `context.TODO()` instead of propagating the parent context — losing timeout and cancellation propagation. Istio sidecar provides mesh-level retry and timeout capabilities but no explicit configuration is present.
- **Gap**: No application-level circuit breakers or resilience patterns. A downstream service failure cascades directly to the caller. `context.TODO()` in `convertCurrency` is a bug — it bypasses context propagation.
- **Compensating Controls**:
  - Istio sidecar can be configured with retry policies and timeouts at the mesh layer
  - K8s liveness/readiness probes restart unhealthy pods
  - HPA auto-scales based on CPU utilization
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add per-call context deadlines. Fix `context.TODO()` to use the parent context. Implement circuit breakers (e.g., `sony/gobreaker` or Istio DestinationRule outlier detection). Configure Istio retry policies for idempotent downstream calls.
- **Evidence**: `src/checkoutservice/main.go` (mustConnGRPC, convertCurrency with context.TODO()), `helm-chart/templates/checkoutservice.yaml` (Sidecar egress)

### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: RISK
- **Finding**: HPA is configured with minReplicas=1, maxReplicas=5, targeting 70% CPU utilization. Resource limits are conservative (100m CPU request, 200m limit; 64Mi memory request, 128Mi limit). Monitoring alerts are configured for error rates and latency. However, no load testing results exist for agent traffic patterns. The service calls 6 downstream services — agent-induced fan-out could overwhelm downstream services even if checkoutservice itself scales.
- **Gap**: No load testing for agent traffic patterns. Conservative resource limits may be insufficient for burst traffic. Fan-out to 6 downstream services amplifies agent traffic 6x.
- **Compensating Controls**:
  - HPA provides auto-scaling based on CPU
  - Monitoring alerts detect degradation
  - Rate-limit EnvoyFilter on frontend limits inbound request rate
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Conduct load testing with agent-like traffic patterns (burst, retry, fan-out). Increase maxReplicas based on results. Ensure downstream services also have HPAs configured (they do). Consider dedicated agent traffic isolation.
- **Evidence**: `kubernetes-manifests/hpa.yaml` (checkoutservice HPA), `kubernetes-manifests/monitoring-alerts.yaml`, `helm-chart/values.yaml` (resource limits)

### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK
- **Finding**: Proto defines `created_at` and `updated_at` timestamps on `Cart`, `Product`, and `OrderResult` messages using `google.protobuf.Timestamp`. However, `PlaceOrderResponse` returns an `OrderResult` with `created_at` but no `updated_at`. No `Cache-Control` or freshness headers. No consistency level indicators. Cart data freshness depends on Redis TTL in cartservice. Product prices may be stale if catalog is updated between cart addition and checkout.
- **Gap**: No freshness signaling for data returned to agents. No consistency level indicators. Price staleness risk between cart and checkout.
- **Compensating Controls**:
  - `google.protobuf.Timestamp` fields provide temporal metadata on key entities
  - Real-time gRPC calls to downstream services ensure data is current at call time
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `Cache-Control` equivalent metadata to gRPC responses. Document consistency guarantees for the checkout workflow (e.g., prices are fetched at checkout time, not cart time).
- **Evidence**: `protos/demo.proto` (Timestamp fields on Cart, Product, OrderResult), `src/checkoutservice/main.go`

### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK
- **Finding**: `PlaceOrder` logs `user_id` and `email` in plain text: `log.Infof("[PlaceOrder] user_id=%q user_currency=%q", req.UserId, req.UserCurrency)` and `log.Infof("order confirmation email sent to %q", req.Email)`. Credit card data is not logged. Address data is not logged. But PII (user_id, email) appears in operational logs without redaction.
- **Gap**: PII (user_id, email) logged without redaction. No log scrubbing middleware.
- **Compensating Controls**:
  - Credit card data (PCI) is not logged — positive finding
  - Address data is not logged — positive finding
  - Configure log aggregation with PII masking at the collection layer
- **Remediation Timeline**: 30 days
- **Recommendation**: Redact or hash `user_id` and `email` in log output. Use structured logging fields with a PII-aware formatter. Consider a logrus hook that masks PII fields.
- **Evidence**: `src/checkoutservice/main.go` (PlaceOrder log statements)

### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK
- **Finding**: Skaffold provides local development. CI deploys per-PR to ephemeral namespaces on `prs-gke-cluster`. No persistent agent testing environment with production-equivalent data shape. Smoke tests via loadgenerator validate basic functionality.
- **Gap**: No dedicated agent testing environment. Ephemeral PR namespaces are destroyed after CI.
- **Compensating Controls**:
  - Use Skaffold for local instance with Docker build for isolated testing
  - Leverage per-PR ephemeral namespaces for integration testing
- **Remediation Timeline**: 30 days
- **Recommendation**: Create persistent staging namespace for agent integration testing with production-equivalent configuration and synthetic data.
- **Evidence**: `skaffold.yaml`, `src/checkoutservice/Dockerfile`, `.github/workflows/ci-pr.yaml`

### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK
- **Finding**: CI exists (Cloud Build + Skaffold + GitHub Actions). Go unit tests run for `shippingservice`, `productcatalogservice`, and `frontend/validator` — but not for `checkoutservice`. Proto uses versioned package (`hipstershop.v1`) and `buf.yaml` exists with `breaking: FILE` rule configured. However, `buf breaking` is not executed in CI — the rule is defined but not enforced. No checkoutservice-specific contract tests.
- **Gap**: No automated breaking change detection in CI pipeline despite `buf.yaml` having the rule defined. No checkoutservice-specific API contract tests. Checkoutservice excluded from Go unit test CI step.
- **Compensating Controls**:
  - Protobuf wire compatibility provides implicit backward compatibility for additive changes
  - `buf.yaml` with `breaking: FILE` rule is ready to be added to CI
  - Smoke test via loadgenerator exercises the checkout flow end-to-end
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `buf breaking` to CI pipeline. Add checkoutservice to the Go unit test CI step. Add contract tests validating `PlaceOrderRequest`/`PlaceOrderResponse` schemas.
- **Evidence**: `cloudbuild.yaml`, `.github/workflows/ci-pr.yaml`, `protos/buf.yaml`, `protos/demo.proto`

---

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: Well-documented gRPC interface in `protos/demo.proto` with `CheckoutService` defining `PlaceOrder` RPC. Proto uses versioned package `hipstershop.v1` with data classification comments (PCI + PII). Implemented in `main.go`. Positive finding.
- **Implication**: gRPC interface can be used directly as agent tool binding. Proto enables auto-generated client code. Data classification comments inform agent access policies.
- **Recommendation**: No remediation needed.
- **Evidence**: `protos/demo.proto`, `src/checkoutservice/main.go`

### API-Q2: Machine-Readable API Specification
- **Severity**: INFO
- **Finding**: `protos/demo.proto` is a machine-readable spec with versioned package `hipstershop.v1`, data classification comments, and `buf.yaml` for linting. Protobuf is strongly typed with field numbers and timestamps. Spec is current with implementation. Positive finding.
- **Implication**: Agent tool definitions can be auto-generated from proto. `buf` tooling enables schema governance. Shared proto across services is a minor concern for independent evolution.
- **Recommendation**: Consider enabling gRPC server reflection for runtime schema discovery. Evaluate splitting the monolithic proto into per-service proto files.
- **Evidence**: `protos/demo.proto`, `protos/buf.yaml`

### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: `PlaceOrder` is not idempotent — each call generates a new `uuid`, charges the card, ships the order, and empties the cart. No idempotency key support. Duplicate calls create duplicate orders and charges.
- **Implication**: For read-only agent scope, idempotency is informational only. Critical concern if agent scope expands to write-enabled.
- **Recommendation**: Implement idempotency key support in `PlaceOrder` before enabling write-enabled agent scope.
- **Evidence**: `src/checkoutservice/main.go` (PlaceOrder generates new UUID per call)

### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: Istio AuthorizationPolicy is enabled (`authorizationPolicies.create: true`), providing mTLS-based identity verification. Callers restricted to `frontend` service account with per-path rules for `/hipstershop.CheckoutService/PlaceOrder`. Istio sidecars enabled (`sidecars.create: true`). The gRPC server uses `insecure.NewCredentials()` at the application layer, but Istio sidecar terminates mTLS before traffic reaches the application — standard Istio pattern.
- **Implication**: Machine identity is authenticated at the mesh layer via mTLS with per-service principal attribution. This satisfies the core requirement for agent identity verification.
- **Recommendation**: For defense in depth, consider implementing a gRPC interceptor that extracts the Istio peer identity from request headers for application-level audit logging.
- **Evidence**: `helm-chart/values.yaml` (`authorizationPolicies.create: true`, `sidecars.create: true`), `helm-chart/templates/checkoutservice.yaml` (AuthorizationPolicy), `src/checkoutservice/main.go`

### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: No secrets or credentials are used by the service — all downstream service addresses are passed via environment variables (non-secret). gRPC connections use `insecure.NewCredentials()` at the application layer (Istio mTLS handles transport security). Google Cloud Profiler uses Workload Identity. Credential-free architecture by design.
- **Implication**: No credential management concerns. Workload Identity and Istio mTLS eliminate the need for application-managed credentials. Positive finding.
- **Recommendation**: Maintain credential-free architecture. If credentials are introduced, adopt K8s external secrets operator or AWS Secrets Manager.
- **Evidence**: `src/checkoutservice/main.go`, `helm-chart/templates/checkoutservice.yaml` (env vars), `go.mod`

### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: RISK
- **Finding**: No JWT parsing, no token exchange, no user context headers. `user_id` is passed as a plain string field in `PlaceOrderRequest` — not authenticated or validated against the caller's identity. No distinction between agent-as-self vs agent-on-behalf-of-user. Istio mTLS provides implicit caller identity at the mesh layer but not user-level identity.
- **Gap**: No identity propagation through the 6 downstream service calls. `user_id` is trusted without validation. An agent could place orders for any user_id.
- **Compensating Controls**:
  - Istio mTLS provides caller service identity at the mesh layer
  - AuthorizationPolicy restricts callers to `frontend` only
  - Read-only agent scope means agents do not directly call PlaceOrder
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement JWT-based identity propagation. Validate `user_id` against the authenticated caller's identity. Distinguish agent-as-self vs agent-on-behalf-of-user in downstream calls.
- **Evidence**: `src/checkoutservice/main.go` (PlaceOrder accepts user_id without validation), `protos/demo.proto`, `helm-chart/values.yaml`

### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits. `PlaceOrder` has no per-user or per-session limits on order value, item count, or frequency. A write-enabled agent could place unlimited orders at machine speed.
- **Implication**: Transaction limits not applicable for read-only scope. Critical concern if agent scope expands to write-enabled.
- **Recommendation**: Implement per-user order frequency limits and maximum order value caps before enabling write-enabled agent scope.
- **Evidence**: `src/checkoutservice/main.go`

### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO
- **Finding**: Comprehensive data classification exists. Proto includes field-level classification comments: `PlaceOrderRequest` is PCI+PII (contains `CreditCardInfo` [PCI], `Address` [PII], `email` [PII]). `DATA_CLASSIFICATION.md` documents service-level classifications and agent access policies. CheckoutService is classified as PCI+PII with sensitive fields `CreditCardInfo.*`, `email`, `Address.*`.
- **Implication**: Data classification is well-documented at both the proto field level and the service level. Agent access policies are defined in `DATA_CLASSIFICATION.md`. Positive finding.
- **Recommendation**: No remediation needed. Maintain classification as proto evolves.
- **Evidence**: `protos/demo.proto` (field-level classification comments), `DATA_CLASSIFICATION.md`

### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: CheckoutService handles PCI (credit card) and PII (email, address) data. No explicit data residency requirements or documentation. No data residency configuration in IaC. PCI data transits through the service but is not stored. PII (email, address) is passed to downstream services.
- **Gap**: No formal data residency documentation for PCI/PII data. No analysis of whether agent-initiated requests could transmit PCI/PII data to LLM providers in different jurisdictions.
- **Compensating Controls**:
  - PCI data is not stored by checkoutservice (pass-through to paymentservice)
  - `DATA_CLASSIFICATION.md` documents that no agent may access PCI fields without PCI-DSS compliance verification
  - Istio mTLS ensures data stays within the mesh
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document data residency posture formally. Ensure agent orchestration layer does not transmit PCI/PII data to LLM providers. Implement data residency controls if deploying to multi-region.
- **Evidence**: `DATA_CLASSIFICATION.md`, `protos/demo.proto`, `src/checkoutservice/main.go`

### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: INFO
- **Finding**: Proto uses versioned package `hipstershop.v1`. `buf.yaml` exists with `breaking: FILE` rule for breaking change detection and `STANDARD` lint rules. Proto defines typed schemas with data classification comments and timestamps. Breaking change detection tooling is in place but not yet enforced in CI.
- **Implication**: Schema versioning is established. Proto versioning enables safe evolution. `buf` tooling provides a path to automated breaking change detection. The `breaking: FILE` rule will catch field removals, type changes, and reserved number violations.
- **Recommendation**: Add `buf breaking` to CI pipeline to complete the contract testing story (tracked under ENG-Q2).
- **Evidence**: `protos/demo.proto` (`hipstershop.v1`), `protos/buf.yaml`

### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: INFO
- **Finding**: OpenTelemetry SDK with gRPC instrumentation is enabled. `otelgrpc.NewServerHandler()` and `otelgrpc.NewClientHandler()` instrument both server and client calls. OTel trace exporter sends to the OpenTelemetry Collector (`COLLECTOR_SERVICE_ADDR`). Trace context is propagated via `propagation.TraceContext{}` and `propagation.Baggage{}`. Logrus provides structured JSON logging with timestamp, severity, and message fields.
- **Implication**: Distributed tracing is operational across all 6 downstream service calls. Trace context enables end-to-end request correlation. Structured JSON logging supports log aggregation. The remaining gap (no trace_id in logrus entries) is minor — OpenTelemetry trace IDs serve the same purpose.
- **Recommendation**: Add trace_id to logrus log entries for log-to-trace correlation. Consider using `otellogrus` bridge.
- **Evidence**: `src/checkoutservice/main.go` (OTel setup, otelgrpc handlers), `helm-chart/values.yaml` (`tracing: true`, `opentelemetryCollector.create: true`), `go.mod`

### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: INFO
- **Finding**: PrometheusRule monitoring alerts are configured for gRPC error rates (>1% warning, >5% critical), P95 latency (>500ms), and service availability. HPA is configured for auto-scaling. K8s health probes (liveness + readiness) provide pod availability monitoring.
- **Implication**: Alerting infrastructure is in place. Service degradation will be detected before agents cascade failures. The 6-service fan-out means checkoutservice latency alerts will catch downstream degradation.
- **Recommendation**: Tune alert thresholds based on agent traffic patterns during pilot. Consider per-downstream-service latency alerts.
- **Evidence**: `kubernetes-manifests/monitoring-alerts.yaml`, `kubernetes-manifests/hpa.yaml`, `kubernetes-manifests/checkoutservice.yaml`

### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: INFO
- **Finding**: Comprehensive IaC: K8s manifests, Kustomize, Helm, Terraform. CODEOWNERS enforces peer review. GitHub Actions CI on PRs. AuthorizationPolicies, NetworkPolicies, Sidecars, and HPAs are all defined in IaC and enabled. Rate-limit EnvoyFilter defined in `istio-manifests/rate-limit.yaml`. No drift detection configured.
- **Implication**: Infrastructure governance is strong — IaC coverage is comprehensive and peer review is enforced. The drift detection gap is minor for a K8s-native deployment where Helm/Kustomize reconciliation provides implicit drift correction on deploy.
- **Recommendation**: Implement drift detection or GitOps (ArgoCD/Flux) for continuous reconciliation.
- **Evidence**: `kubernetes-manifests/checkoutservice.yaml`, `.github/terraform/main.tf`, `.github/CODEOWNERS`, `.github/workflows/ci-pr.yaml`, `helm-chart/values.yaml`, `istio-manifests/rate-limit.yaml`

### ENG-Q3: Rollback Capability
- **Severity**: RISK
- **Finding**: K8s Deployment with rollout history. Skaffold deployment. No automated rollback triggers. Manual rollback via `kubectl rollout undo` only. No canary deployment, no Flagger, no Argo Rollouts. Monitoring alerts can trigger manual rollback faster.
- **Gap**: No automated rollback on service degradation. Manual rollback only.
- **Compensating Controls**:
  - K8s rollout history enables manual rollback within minutes
  - Liveness/readiness probes prevent traffic to unhealthy pods
  - Monitoring alerts detect degradation and can trigger manual rollback
  - HPA provides auto-scaling during degradation
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure automated rollback triggers using Flagger or Argo Rollouts with canary analysis. As a P0 critical-path service, automated rollback is especially important.
- **Evidence**: `skaffold.yaml`, `kubernetes-manifests/checkoutservice.yaml`, `kubernetes-manifests/monitoring-alerts.yaml`

### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: gRPC Protocol Buffers — strongly-typed binary format with explicit types, field numbers, data classification comments, and timestamps.
- **Implication**: Protobuf is more structured than JSON. Excellent for agent integration with auto-generated client code.
- **Recommendation**: No action needed.
- **Evidence**: `protos/demo.proto`

### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: No event emission. `PlaceOrder` returns the `OrderResult` synchronously but does not emit events to a message bus. No SNS/EventBridge/Kafka integration. No webhook callbacks. State changes (order placed, payment charged, order shipped) are not published as events.
- **Implication**: Agents cannot subscribe to checkout events for reactive workflows. All interaction is request/response.
- **Recommendation**: Emit order lifecycle events (order.placed, payment.charged, order.shipped) to a message bus for event-driven agent patterns.
- **Evidence**: `src/checkoutservice/main.go` (PlaceOrder — no event publishing)

### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: Rate-limit EnvoyFilter is configured on the frontend with `x-rate-limit-limit` and `x-rate-limit-remaining` response headers. Token bucket: 100 requests per 60 seconds. However, this applies to the frontend workload, not directly to checkoutservice. No rate limit headers on checkoutservice gRPC responses.
- **Implication**: Agents calling through the frontend will receive rate limit headers. Direct gRPC callers to checkoutservice will not.
- **Recommendation**: Add rate limit headers to checkoutservice gRPC responses via EnvoyFilter or gRPC trailing metadata.
- **Evidence**: `istio-manifests/rate-limit.yaml`, `src/checkoutservice/main.go`

### STATE-Q5: Rate Limiting and Throttling
- **Severity**: INFO
- **Finding**: Rate-limit EnvoyFilter is configured on the frontend (`istio-manifests/rate-limit.yaml`) with a token bucket of 100 requests per 60 seconds. This protects the checkout flow from the frontend entry point. No application-level rate limiting in checkoutservice itself. K8s resource limits cap CPU/memory. HPA provides auto-scaling.
- **Implication**: Rate limiting exists at the frontend entry point, which is the primary ingress path for checkout requests. Direct service-to-service calls bypass this limit.
- **Recommendation**: Consider adding a checkoutservice-specific rate limit via EnvoyFilter or gRPC interceptor for defense in depth.
- **Evidence**: `istio-manifests/rate-limit.yaml`, `src/checkoutservice/main.go`, `kubernetes-manifests/checkoutservice.yaml`

### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics. CheckoutService is stateless — data quality depends on downstream services (cart, product catalog, currency, payment, shipping). No validation of cart item quantities, product availability, or currency code validity before processing.
- **Implication**: Data quality is delegated to downstream services. No pre-validation means invalid data propagates through the checkout workflow.
- **Recommendation**: Add input validation for `PlaceOrderRequest` fields (e.g., non-empty cart, valid currency code, valid address fields) before calling downstream services.
- **Evidence**: `src/checkoutservice/main.go`, `protos/demo.proto`

### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Clear semantic names: `user_id`, `user_currency`, `credit_card`, `email`, `address`, `street_address`, `city`, `state`, `country`, `zip_code`, `order_id`, `shipping_tracking_id`. Detailed comments with data classification. No abbreviations or legacy codes.
- **Implication**: LLMs can interpret fields directly. No translation needed. Data classification comments enhance semantic understanding.
- **Recommendation**: No action needed.
- **Evidence**: `protos/demo.proto`

### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal catalog. Proto file serves as informal documentation with data classification comments. `DATA_CLASSIFICATION.md` provides service-level data ownership and classification taxonomy. Agent access policies documented.
- **Implication**: `DATA_CLASSIFICATION.md` serves as a lightweight data catalog. Sufficient for the current service scope.
- **Recommendation**: Register in organization API catalog if part of larger data mesh.
- **Evidence**: `protos/demo.proto`, `DATA_CLASSIFICATION.md`

### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics. Operational logging captures order placement success/failure and payment transaction IDs. OpenTelemetry metrics provide infrastructure-level visibility. No metrics for checkout conversion rate, average order value, or payment failure rate.
- **Implication**: No business outcome monitoring. For a P0 critical-path service, business metrics are important for measuring agent impact on checkout success rates.
- **Recommendation**: Publish metrics for checkout success rate, average order value, payment failure rate, and end-to-end checkout latency.
- **Evidence**: `src/checkoutservice/main.go`

### ENG-Q4: API Test Coverage
- **Severity**: INFO
- **Finding**: `money/money_test.go` provides unit tests for the money arithmetic package (IsValid, IsZero, IsPositive, Sum, Multiply). No tests for `PlaceOrder` RPC or any of the downstream service call functions. CI skips checkoutservice in the Go unit test step. Smoke test via loadgenerator exercises the checkout flow end-to-end.
- **Implication**: Money arithmetic is tested. Core checkout orchestration logic is untested. For a P0 orchestrator service, this is a significant gap — but the loadgenerator smoke test provides basic end-to-end coverage.
- **Recommendation**: Add unit tests for `PlaceOrder` with mocked downstream services. Add integration tests. Include checkoutservice in CI Go test step.
- **Evidence**: `src/checkoutservice/money/money_test.go`, `.github/workflows/ci-pr.yaml`, `src/checkoutservice/main.go`

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: Well-documented gRPC interface in `protos/demo.proto` with `CheckoutService` defining `PlaceOrder` RPC. Proto uses versioned package `hipstershop.v1` with data classification comments (PCI + PII). Implemented in `main.go`. Positive finding.
- **Gap**: None — BLOCKER criteria satisfied.
- **Recommendation**: No remediation needed.
- **Evidence**: `protos/demo.proto`, `src/checkoutservice/main.go`

#### API-Q2: Machine-Readable API Specification
- **Severity**: INFO
- **Finding**: `protos/demo.proto` is a machine-readable spec with versioned package `hipstershop.v1`, data classification comments, and `buf.yaml` for linting. Protobuf is strongly typed with field numbers and timestamps. Spec is current with implementation. Positive finding.
- **Gap**: Shared proto across all services — changes to any service affect the same file. No gRPC server reflection.
- **Recommendation**: Consider enabling gRPC server reflection for runtime schema discovery. Evaluate splitting the monolithic proto into per-service proto files for independent evolution.
- **Evidence**: `protos/demo.proto`, `protos/buf.yaml`

#### API-Q3: Structured Error Responses
- **Severity**: RISK
- **Finding**: `PlaceOrder` uses `status.Errorf(codes.Internal, err.Error())` for most errors. Some differentiation: `codes.Unavailable` for shipping. Error messages expose internal details. No structured error metadata.
- **Gap**: Agents cannot distinguish retriable from terminal errors. Internal error details leak.
- **Recommendation**: Use specific gRPC status codes. Add structured error details using `google.rpc.Status`. Sanitize error messages.
- **Evidence**: `src/checkoutservice/main.go` (PlaceOrder, chargeCard, shipOrder)

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: `PlaceOrder` is not idempotent — each call generates a new UUID, charges the card, ships the order, and empties the cart. No idempotency key support.
- **Gap**: Duplicate calls create duplicate orders and charges. Critical if agent scope expands to write-enabled.
- **Recommendation**: Implement idempotency key support before enabling write-enabled agent scope.
- **Evidence**: `src/checkoutservice/main.go` (PlaceOrder generates new UUID per call)

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: gRPC Protocol Buffers — strongly-typed binary format with explicit types, field numbers, data classification comments, and timestamps.
- **Gap**: None.
- **Recommendation**: No action needed.
- **Evidence**: `protos/demo.proto`

#### API-Q6: Asynchronous Operation Support
- **Severity**: RISK
- **Finding**: `PlaceOrder` is a synchronous RPC that orchestrates 6 downstream service calls sequentially. No async patterns, no job submission, no polling endpoint, no webhook callback. The entire checkout workflow executes in a single request/response cycle. For a complex orchestration with payment charging and shipping, this could exceed agent timeout limits under load.
- **Trigger**: Service has operations >30s OR long-running workflows — triggered (orchestrator calling 6 services sequentially)
- **Gap**: No async operation support. Long checkout workflows may timeout under load.
- **Recommendation**: Consider implementing an async checkout pattern: submit order → return order ID → poll for status. This decouples the agent from the multi-step workflow execution.
- **Evidence**: `src/checkoutservice/main.go` (PlaceOrder — sequential calls to 6 services)

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: No event emission. `PlaceOrder` returns `OrderResult` synchronously. No SNS/EventBridge/Kafka integration. No webhook callbacks. State changes not published as events.
- **Trigger**: Service has state changes (orchestrator) — triggered
- **Gap**: Agents cannot subscribe to checkout events for reactive workflows.
- **Recommendation**: Emit order lifecycle events to a message bus for event-driven agent patterns.
- **Evidence**: `src/checkoutservice/main.go`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: Rate-limit EnvoyFilter on frontend returns `x-rate-limit-limit` and `x-rate-limit-remaining` headers. Token bucket: 100 req/60s. No rate limit headers on checkoutservice gRPC responses directly.
- **Gap**: Direct gRPC callers to checkoutservice do not receive rate limit headers.
- **Recommendation**: Add rate limit headers to checkoutservice gRPC responses.
- **Evidence**: `istio-manifests/rate-limit.yaml`, `src/checkoutservice/main.go`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: Istio AuthorizationPolicy enabled with mTLS-based identity verification. Callers restricted to `frontend` service account with per-path rules for `/hipstershop.CheckoutService/PlaceOrder`. Sidecars enabled. Application uses `insecure.NewCredentials()` — standard Istio pattern where sidecar terminates mTLS.
- **Gap**: None — mesh-level mTLS with per-service AuthorizationPolicy satisfies machine identity authentication.
- **Recommendation**: For defense in depth, extract Istio peer identity from request headers for application-level audit logging.
- **Evidence**: `helm-chart/values.yaml`, `helm-chart/templates/checkoutservice.yaml`, `src/checkoutservice/main.go`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicy restricts callers to `frontend` only with per-path rules. No agent-specific service accounts.
- **Gap**: No agent-specific service accounts with tailored permissions.
- **Recommendation**: Create agent-specific service accounts with per-RPC AuthorizationPolicy rules.
- **Evidence**: `helm-chart/templates/checkoutservice.yaml`, `helm-chart/values.yaml`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicy defines per-path rules. No application-layer action-level authorization.
- **Gap**: No application-layer authorization. Mesh bypass exposes all RPCs.
- **Recommendation**: Implement gRPC server interceptor for action-level authorization.
- **Evidence**: `src/checkoutservice/main.go`, `helm-chart/templates/checkoutservice.yaml`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: RISK
- **Finding**: No JWT parsing, token exchange, or user context headers. `user_id` passed as plain string without validation. No distinction between agent-as-self vs agent-on-behalf-of-user. Istio mTLS provides caller service identity only.
- **Gap**: No identity propagation through 6 downstream calls. `user_id` trusted without validation.
- **Recommendation**: Implement JWT-based identity propagation. Validate `user_id` against authenticated caller identity.
- **Evidence**: `src/checkoutservice/main.go`, `protos/demo.proto`, `helm-chart/values.yaml`

#### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: No secrets or credentials used. Service addresses via env vars. `insecure.NewCredentials()` with Istio mTLS. Workload Identity for GCP. Credential-free architecture by design.
- **Gap**: None — no credentials to manage. Positive finding.
- **Recommendation**: Maintain credential-free architecture. Adopt external secrets operator if credentials needed.
- **Evidence**: `src/checkoutservice/main.go`, `helm-chart/templates/checkoutservice.yaml`, `go.mod`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: No audit logging. Logrus operational messages only. PII (user_id, email) logged in plain text. No principal attribution. OpenTelemetry tracing enabled but not audit-grade.
- **Gap**: No immutable audit trail. Cannot attribute actions to specific agent identities. PII leakage in logs.
- **Recommendation**: Add structured audit logging with caller identity. Forward to immutable store. Redact PII.
- **Evidence**: `src/checkoutservice/main.go`, `helm-chart/values.yaml`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicy and NetworkPolicies provide manual suspension mechanisms. No automated suspension.
- **Gap**: No automated or rapid suspension mechanism.
- **Recommendation**: Implement automated suspension via AuthorizationPolicy updates triggered by anomaly detection.
- **Evidence**: `helm-chart/templates/checkoutservice.yaml`, `helm-chart/values.yaml`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: Multi-step workflow with no compensation. Payment charge not reversed if shipping fails. Cart emptied regardless of email failure.
- **Gap**: No compensation for partial failures in checkout workflow.
- **Recommendation**: Implement saga pattern with compensating transactions.
- **Evidence**: `src/checkoutservice/main.go` (PlaceOrder — sequential steps)

#### STATE-Q2: Queryable Current State
- **Severity**: RISK
- **Finding**: Only `PlaceOrder` RPC — write-only. No query endpoints for order status or checkout state. Stateless service delegates state to downstream services.
- **Trigger**: Service has persistent state (orchestrator) — triggered
- **Gap**: No read endpoints. Agents cannot query order status.
- **Recommendation**: Add `GetOrderStatus` or `PreviewOrder` RPC.
- **Evidence**: `protos/demo.proto`, `src/checkoutservice/main.go`

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `orchestrator`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled AND service has persistent state
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK
- **Finding**: Calls 6 downstream services with no circuit breakers, no retry logic, no per-call deadlines. `convertCurrency` uses `context.TODO()` — bypasses context propagation. Istio sidecar provides mesh-level capabilities but no explicit configuration.
- **Trigger**: Service has external dependencies — triggered (6 downstream services)
- **Gap**: No application-level circuit breakers. Downstream failures cascade directly. `context.TODO()` bug.
- **Recommendation**: Add per-call context deadlines. Fix `context.TODO()`. Implement circuit breakers. Configure Istio retry policies.
- **Evidence**: `src/checkoutservice/main.go` (mustConnGRPC, convertCurrency)

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: INFO
- **Finding**: Rate-limit EnvoyFilter on frontend (100 req/60s token bucket). No application-level rate limiting in checkoutservice. K8s resource limits and HPA provide scaling.
- **Gap**: Direct service-to-service calls bypass frontend rate limit. Minor gap given AuthorizationPolicy restricts callers to frontend.
- **Recommendation**: Consider checkoutservice-specific rate limit for defense in depth.
- **Evidence**: `istio-manifests/rate-limit.yaml`, `src/checkoutservice/main.go`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits. No per-user or per-session limits on order value, item count, or frequency.
- **Gap**: None for read-only scope. Critical if write-enabled.
- **Recommendation**: Implement transaction limits before enabling write-enabled agent scope.
- **Evidence**: `src/checkoutservice/main.go`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: RISK
- **Finding**: HPA configured (1–5 replicas, 70% CPU target). Conservative resource limits. Monitoring alerts configured. No load testing for agent traffic. 6-service fan-out amplifies traffic.
- **Trigger**: Service is P0 priority — triggered
- **Gap**: No load testing for agent traffic patterns. Fan-out amplification risk.
- **Recommendation**: Conduct load testing with agent-like traffic patterns. Increase maxReplicas based on results.
- **Evidence**: `kubernetes-manifests/hpa.yaml`, `kubernetes-manifests/monitoring-alerts.yaml`

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `orchestrator`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `orchestrator`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK
- **Finding**: Skaffold local dev. CI per-PR ephemeral namespaces. No persistent agent testing environment.
- **Gap**: No dedicated agent testing environment.
- **Recommendation**: Create persistent staging namespace for agent integration testing.
- **Evidence**: `skaffold.yaml`, `src/checkoutservice/Dockerfile`, `.github/workflows/ci-pr.yaml`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO
- **Finding**: Comprehensive classification. Proto field-level comments: `PlaceOrderRequest` is PCI+PII. `DATA_CLASSIFICATION.md` documents service-level classifications and agent access policies. Positive finding.
- **Gap**: None — classification is thorough.
- **Recommendation**: Maintain classification as proto evolves.
- **Evidence**: `protos/demo.proto`, `DATA_CLASSIFICATION.md`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: Handles PCI and PII data. No explicit residency documentation. PCI data is pass-through (not stored).
- **Gap**: No formal data residency documentation for PCI/PII data.
- **Recommendation**: Document data residency posture. Ensure agent orchestration does not transmit PCI/PII to LLM providers.
- **Evidence**: `DATA_CLASSIFICATION.md`, `protos/demo.proto`

#### DATA-Q3: Selective Query Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `orchestrator`, agent_scope: `read-only`.
- **Trigger**: Service has list/query endpoints with potentially unbounded results
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q4: System of Record Designations
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `orchestrator`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK
- **Finding**: Proto defines `created_at`/`updated_at` timestamps using `google.protobuf.Timestamp`. No freshness headers. No consistency level indicators. Price staleness risk between cart and checkout.
- **Trigger**: Service has persistent state (orchestrator) — triggered
- **Gap**: No freshness signaling. No consistency indicators.
- **Recommendation**: Add freshness metadata to gRPC responses. Document consistency guarantees.
- **Evidence**: `protos/demo.proto`, `src/checkoutservice/main.go`

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK
- **Finding**: `user_id` and `email` logged in plain text. Credit card and address data not logged (positive). No log scrubbing middleware.
- **Gap**: PII (user_id, email) logged without redaction.
- **Recommendation**: Redact or hash PII in log output. Use PII-aware logrus hook.
- **Evidence**: `src/checkoutservice/main.go` (PlaceOrder log statements)

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics. Stateless service — quality depends on downstream services. No input validation before processing.
- **Gap**: No pre-validation of PlaceOrderRequest fields.
- **Recommendation**: Add input validation for cart, currency code, and address fields.
- **Evidence**: `src/checkoutservice/main.go`, `protos/demo.proto`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: INFO
- **Finding**: Proto uses `hipstershop.v1`. `buf.yaml` with `breaking: FILE` rule. Data classification comments. Breaking change detection not yet in CI.
- **Gap**: `buf breaking` not enforced in CI (tracked under ENG-Q2).
- **Recommendation**: Add `buf breaking` to CI pipeline.
- **Evidence**: `protos/demo.proto`, `protos/buf.yaml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Clear semantic names with data classification comments. No abbreviations or legacy codes.
- **Gap**: None.
- **Recommendation**: No action needed.
- **Evidence**: `protos/demo.proto`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal catalog. Proto and `DATA_CLASSIFICATION.md` serve as lightweight documentation with classification taxonomy and agent access policies.
- **Gap**: No formal catalog. Sufficient for current scope.
- **Recommendation**: Register in organization API catalog if part of larger data mesh.
- **Evidence**: `protos/demo.proto`, `DATA_CLASSIFICATION.md`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: INFO
- **Finding**: OpenTelemetry SDK with gRPC instrumentation on both server and client handlers. OTel Collector deployed. Trace context propagated. Logrus structured JSON logging. No trace_id in log entries (minor).
- **Gap**: No trace_id in logrus entries (minor — OTel trace IDs serve same purpose).
- **Recommendation**: Add trace_id to logrus entries via `otellogrus` bridge.
- **Evidence**: `src/checkoutservice/main.go`, `helm-chart/values.yaml`, `go.mod`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: INFO
- **Finding**: PrometheusRule alerts for gRPC error rates, P95 latency, and service availability. HPA configured. Health probes active.
- **Gap**: None — alerting infrastructure is in place.
- **Recommendation**: Tune thresholds for agent traffic patterns. Add per-downstream-service latency alerts.
- **Evidence**: `kubernetes-manifests/monitoring-alerts.yaml`, `kubernetes-manifests/hpa.yaml`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics. Operational logging captures order success/failure and transaction IDs. No checkout conversion rate or payment failure rate metrics.
- **Gap**: No business outcome monitoring for a P0 critical-path service.
- **Recommendation**: Publish checkout success rate, average order value, and payment failure rate metrics.
- **Evidence**: `src/checkoutservice/main.go`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: INFO
- **Finding**: Comprehensive IaC: K8s manifests, Kustomize, Helm, Terraform. CODEOWNERS enforces peer review. CI on PRs. AuthorizationPolicies, NetworkPolicies, Sidecars, HPAs, EnvoyFilter all in IaC. No drift detection.
- **Gap**: Drift detection missing (minor for K8s-native with Helm reconciliation).
- **Recommendation**: Implement drift detection or GitOps (ArgoCD/Flux).
- **Evidence**: `kubernetes-manifests/checkoutservice.yaml`, `.github/terraform/main.tf`, `.github/CODEOWNERS`, `.github/workflows/ci-pr.yaml`, `helm-chart/values.yaml`, `istio-manifests/rate-limit.yaml`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK
- **Finding**: CI exists. Proto versioned. `buf.yaml` with `breaking: FILE` rule. No `buf breaking` in CI. Checkoutservice excluded from Go unit tests. No contract tests.
- **Gap**: No automated breaking change detection. Checkoutservice excluded from CI tests.
- **Recommendation**: Add `buf breaking` to CI. Include checkoutservice in Go test step. Add contract tests.
- **Evidence**: `cloudbuild.yaml`, `.github/workflows/ci-pr.yaml`, `protos/buf.yaml`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK
- **Finding**: K8s rollout history. Skaffold deployment. Manual rollback only. No canary or automated rollback. Monitoring alerts can trigger manual rollback.
- **Gap**: No automated rollback. Critical for P0 service.
- **Recommendation**: Configure automated rollback with Flagger or Argo Rollouts.
- **Evidence**: `skaffold.yaml`, `kubernetes-manifests/checkoutservice.yaml`, `kubernetes-manifests/monitoring-alerts.yaml`

#### ENG-Q4: API Test Coverage
- **Severity**: INFO
- **Finding**: `money/money_test.go` tests money arithmetic. No PlaceOrder tests. CI skips checkoutservice. Loadgenerator smoke test provides basic end-to-end coverage.
- **Gap**: Core orchestration logic untested. Money package tested.
- **Recommendation**: Add unit tests for PlaceOrder with mocked downstream services. Include in CI.
- **Evidence**: `src/checkoutservice/money/money_test.go`, `.github/workflows/ci-pr.yaml`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `orchestrator`, agent_scope: `read-only`.
- **Trigger**: Service has persistent data stores
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

---

## Evidence Index

### Infrastructure as Code
| File | Questions Referenced |
|------|---------------------|
| `.github/terraform/main.tf` | ENG-Q1 |
| `kubernetes-manifests/checkoutservice.yaml` | AUTH-Q1, AUTH-Q2, STATE-Q5, OBS-Q2, API-Q8, ENG-Q1, ENG-Q3 |
| `kubernetes-manifests/hpa.yaml` | STATE-Q7, OBS-Q2 |
| `kubernetes-manifests/monitoring-alerts.yaml` | OBS-Q2, STATE-Q7, ENG-Q3 |
| `helm-chart/templates/checkoutservice.yaml` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q7, ENG-Q1 |
| `helm-chart/values.yaml` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q6, AUTH-Q7, OBS-Q1, OBS-Q2, ENG-Q1, STATE-Q5 |
| `istio-manifests/rate-limit.yaml` | STATE-Q5, API-Q8, ENG-Q1 |

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `src/checkoutservice/main.go` | API-Q1, API-Q2, API-Q3, API-Q4, API-Q5, API-Q6, API-Q7, API-Q8, AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q2, STATE-Q4, STATE-Q5, STATE-Q6, STATE-Q7, DATA-Q2, DATA-Q5, DATA-Q6, DATA-Q7, OBS-Q1, OBS-Q3, ENG-Q4 |
| `src/checkoutservice/money/money_test.go` | ENG-Q4 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `protos/demo.proto` | API-Q1, API-Q2, API-Q4, API-Q5, API-Q7, AUTH-Q4, STATE-Q2, DATA-Q1, DATA-Q2, DATA-Q5, DATA-Q7, DISC-Q1, DISC-Q2, DISC-Q3, ENG-Q2 |
| `protos/buf.yaml` | API-Q2, DISC-Q1, ENG-Q2 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `cloudbuild.yaml` | ENG-Q2 |
| `skaffold.yaml` | HITL-Q3, ENG-Q1, ENG-Q3 |
| `.github/workflows/ci-pr.yaml` | HITL-Q3, ENG-Q1, ENG-Q2, ENG-Q4 |
| `.github/CODEOWNERS` | ENG-Q1 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `src/checkoutservice/Dockerfile` | HITL-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `src/checkoutservice/go.mod` | AUTH-Q5, OBS-Q1 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `DATA_CLASSIFICATION.md` | DATA-Q1, DATA-Q2, DISC-Q3 |
