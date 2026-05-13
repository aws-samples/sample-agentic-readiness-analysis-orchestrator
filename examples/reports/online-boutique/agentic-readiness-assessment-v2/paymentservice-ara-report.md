# Agentic Readiness Assessment Report

**Target**: services/microservices-demo/src/paymentservice
**Date**: 2026-04-16
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Service Archetype**: stateful-crud (user-provided)
**Agent Scope**: read-only
**Priority**: P0
**Tags**: nodejs, grpc, payment
**Context**: Node.js gRPC service handling payment processing (simulated).

---

## Readiness Profile: Pilot-Ready

**BLOCKERs**: 0 | **RISKs**: 14 | **INFOs**: 25

Supervised pilot with: (1) human approval gates on irreversible actions, (2) agent limited to low-blast-radius operations, (3) compensating controls for each open RISK, (4) remediation timeline before expanding scope.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 0 |
| RISK | 14 |
| INFO | 25 |
| N/A | 0 |
| Not Evaluated (extended) | 4 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 15
**Extended Questions Not Triggered**: 4
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: stateful-crud (user-provided)

---

## BLOCKERs — Must Resolve Before Agent Deployment

No BLOCKERs identified.

---

## RISKs — Proceed with Compensating Controls

### API-Q2: Machine-Readable API Specification
- **Severity**: RISK
- **Finding**: `protos/demo.proto` is machine-readable with strongly typed fields, versioned package (`hipstershop.v1`), and PCI data classification comments on `CreditCardInfo`. `protos/buf.yaml` provides STANDARD lint rules and FILE-level breaking change detection. However, gRPC server reflection is not enabled in `server.js` — the server uses `grpc.Server()` with no reflection service registered.
- **Gap**: No gRPC server reflection for runtime schema discovery. Agents must use the proto file directly.
- **Compensating Controls**:
  - Proto file serves as the authoritative machine-readable spec with `buf` tooling for governance
  - Agent tool definitions can be auto-generated from proto at build time
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Enable gRPC server reflection by adding `@grpc/reflection` package and registering the reflection service on the gRPC server.
- **Evidence**: `protos/demo.proto`, `protos/buf.yaml`, `src/paymentservice/server.js`

### API-Q3: Structured Error Responses
- **Severity**: RISK
- **Finding**: `charge.js` throws typed error classes (`InvalidCreditCard`, `UnacceptedCreditCard`, `ExpiredCreditCard`) extending `CreditCardError` with a `code: 400` property. `server.js` catches errors and forwards via `callback(err)`. gRPC maps these to status codes, but there is no gRPC rich error model — no `google.rpc.ErrorInfo`, no retryable boolean, no structured error body beyond the status code and message string.
- **Gap**: No rich error model. Agents cannot distinguish retriable from terminal errors programmatically.
- **Compensating Controls**:
  - Wrap agent tool calls with client-side error classification (INVALID_ARGUMENT → terminal, UNAVAILABLE → retry)
  - `CreditCardError.code = 400` provides a signal but is not propagated as gRPC metadata
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Map `CreditCardError` subclasses to gRPC rich error model using `@grpc/grpc-js` status metadata. Include error code, retryable flag, and human-readable message.
- **Evidence**: `src/paymentservice/charge.js`, `src/paymentservice/server.js`

### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicy restricts callers to the `checkoutservice` service account on `/hipstershop.PaymentService/Charge` path, port 50051. NetworkPolicy restricts ingress to `checkoutservice` pods only. However, no agent-specific service accounts are defined — all authorized callers have identical access.
- **Gap**: No agent-specific service accounts with tailored permissions. No per-caller differentiation.
- **Compensating Controls**:
  - Istio AuthorizationPolicy restricts callers to `checkoutservice` only (defense in depth)
  - NetworkPolicy provides additional network-level isolation
  - Define agent-specific K8s ServiceAccounts and add them to the AuthorizationPolicy
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create agent-specific service accounts with per-RPC AuthorizationPolicy rules. For a PCI service, agent access should be tightly scoped and separately auditable.
- **Evidence**: `helm-chart/templates/paymentservice.yaml`, `helm-chart/values.yaml`

### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicy defines per-path rules (`/hipstershop.PaymentService/Charge`, method POST, port 50051). However, the application code has no action-level authorization — `server.js` uses `grpc.Server()` with `grpc.ServerCredentials.createInsecure()` and no interceptor or middleware for authorization. Authorization is entirely at the mesh layer.
- **Gap**: No application-layer action-level authorization. If the mesh is bypassed or misconfigured, the Charge RPC is open to any caller. Critical for a PCI-handling service.
- **Compensating Controls**:
  - Istio sidecar injection (`sidecars.create: true`) ensures mesh-level enforcement
  - NetworkPolicy restricts ingress to checkoutservice only
  - `createInsecure()` is standard for Istio-proxied services (mTLS terminates at sidecar)
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement a gRPC interceptor for action-level authorization as defense in depth. For a PCI service, application-layer auth is strongly recommended beyond mesh-only enforcement.
- **Evidence**: `src/paymentservice/server.js`, `helm-chart/templates/paymentservice.yaml`

### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: RISK
- **Finding**: No JWT parsing, no token exchange, no user context headers. The `ChargeRequest` message contains `amount` and `credit_card` — no user identity field. Istio mTLS provides implicit caller identity at the mesh layer (checkoutservice principal), but the paymentservice cannot distinguish whether a charge was initiated by a human checkout flow or an agent-initiated flow.
- **Gap**: No identity propagation. For a PCI service processing payments, the inability to attribute charges to specific users or distinguish agent-initiated vs human-initiated payments is a compliance concern.
- **Compensating Controls**:
  - Istio mTLS provides caller service identity (checkoutservice)
  - Audit attribution can be added at the orchestration layer (checkoutservice logs user context)
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add user identity propagation via gRPC metadata headers. Log the originating user/agent identity alongside each charge for PCI audit trail requirements.
- **Evidence**: `src/paymentservice/server.js`, `protos/demo.proto` (ChargeRequest), `helm-chart/values.yaml`

### AUTH-Q5: Credential Management
- **Severity**: RISK
- **Finding**: No secrets or credentials used — payment processing is simulated (fake transaction IDs via `uuid.v4()`). No database connections, no external payment gateway API keys. No Secrets Manager or Vault integration. The `@google-cloud/profiler` uses ambient GCP credentials via workload identity.
- **Gap**: No credential management framework. A real payment processor would require API keys to a payment gateway. No framework exists for credential lifecycle management.
- **Compensating Controls**:
  - Simulated architecture eliminates current secret rotation concerns
  - K8s ServiceAccount provides pod identity without explicit credential management
- **Remediation Timeline**: 30–60 days
- **Recommendation**: When integrating a real payment gateway, use K8s external secrets operator or AWS Secrets Manager for API key management with automatic rotation.
- **Evidence**: `src/paymentservice/charge.js`, `src/paymentservice/package.json`, `src/paymentservice/index.js`

### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicy provides a mechanism to deny specific service accounts by updating the policy. NetworkPolicy provides additional isolation. However, there is no automated suspension mechanism — policy changes require Helm value updates or manual kubectl edits. No API key revocation, no service account disable endpoint.
- **Gap**: No automated or rapid suspension mechanism. Manual AuthorizationPolicy updates are the only path. For a P0 PCI service, rapid suspension capability is important.
- **Compensating Controls**:
  - AuthorizationPolicy can be updated via kubectl to immediately block a specific principal
  - NetworkPolicy provides a second isolation layer
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement automated suspension via AuthorizationPolicy updates triggered by anomaly detection. For a P0 PCI service, consider a kill-switch mechanism that can revoke agent access within minutes.
- **Evidence**: `helm-chart/templates/paymentservice.yaml`, `helm-chart/values.yaml`

### STATE-Q2: Queryable Current State
- **Severity**: RISK
- **Finding**: The paymentservice exposes only a single `Charge` RPC — a write operation that returns a `transaction_id`. There is no query endpoint to look up transaction status, verify whether a charge was already processed, or retrieve transaction history. The service is stateless (generates UUIDs and discards them). An agent cannot inspect current state before taking action.
- **Gap**: No queryable state. No transaction lookup or status endpoint. An agent cannot verify whether a previous charge succeeded before retrying.
- **Compensating Controls**:
  - Simulated payment processor — no real charges are made, so state query is less critical
  - Idempotency at the orchestration layer (checkoutservice) can compensate
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add a `GetTransaction` RPC or transaction status endpoint. For a real payment processor, this is essential for agent retry safety and reconciliation.
- **Evidence**: `protos/demo.proto` (PaymentService — only Charge RPC), `src/paymentservice/server.js`

### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK
- **Finding**: An EnvoyFilter rate limiting configuration exists in `istio-manifests/rate-limit.yaml`, but it targets only the `frontend` workload (`workloadSelector.labels.app: frontend`). The paymentservice has no rate limiting — no application-level middleware, no Envoy rate limiting on the paymentservice sidecar. HPA in `kubernetes-manifests/hpa.yaml` provides auto-scaling (1–5 replicas at 70% CPU) but does not prevent request flooding.
- **Gap**: Rate limiting exists but only protects frontend. A runaway agent loop could flood the paymentservice with charge requests. No per-caller rate limiting on a P0 PCI service.
- **Compensating Controls**:
  - Extend the existing EnvoyFilter pattern to include paymentservice workload selector
  - Configure agent-side request rate caps in the agent orchestration layer
  - HPA provides elastic capacity as partial mitigation
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Create an EnvoyFilter targeting the paymentservice workload with conservative rate limits. Configure per-source-principal rate limits. PCI service should have tighter limits than general services.
- **Evidence**: `istio-manifests/rate-limit.yaml`, `kubernetes-manifests/hpa.yaml`, `helm-chart/values.yaml`

### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: RISK
- **Finding**: HPA configured for paymentservice (1–5 replicas at 70% CPU utilization). K8s resource limits set (100m–200m CPU, 128Mi–256Mi memory). No load test results or capacity planning documentation found. No circuit breakers isolating agent traffic from checkout traffic. As a P0 service on the critical payment path, agent-induced load could starve the checkout flow.
- **Gap**: No load testing evidence. No traffic isolation between agent and human-initiated requests. HPA provides scaling but no capacity planning for agent traffic patterns.
- **Compensating Controls**:
  - HPA auto-scaling provides elastic capacity
  - Rate limiting (when applied — see STATE-Q5) will cap agent traffic
  - Istio sidecar provides traffic management capabilities
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Conduct load testing with simulated agent traffic patterns. Consider separate traffic lanes (Istio VirtualService routing) for agent vs human-initiated payment requests.
- **Evidence**: `kubernetes-manifests/hpa.yaml`, `helm-chart/templates/paymentservice.yaml`, `helm-chart/values.yaml`

### DATA-Q4: System of Record Designations
- **Severity**: RISK
- **Finding**: `DATA_CLASSIFICATION.md` designates paymentservice as the system of record for "Payment transactions" with PCI classification. Proto comment states "System of Record: paymentservice owns payment transactions". However, the service is stateless — `charge.js` generates a UUID and returns it without persisting. The system-of-record designation is documented but not implemented.
- **Gap**: Documented as system of record for payment transactions, but no persistent storage exists. Transaction IDs are generated and discarded.
- **Compensating Controls**:
  - Simulated payment processor — no real transactions to reconcile
  - Checkoutservice (orchestrator) may log transaction IDs as part of order records
- **Remediation Timeline**: 60–90 days
- **Recommendation**: For a real payment processor, implement persistent transaction storage with the paymentservice as the authoritative source. Add transaction lookup capability (see STATE-Q2).
- **Evidence**: `DATA_CLASSIFICATION.md`, `protos/demo.proto`, `src/paymentservice/charge.js`

### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK
- **Finding**: `ChargeResponse` contains only `transaction_id` — no `created_at`, `processed_at`, or timestamp fields. The proto defines `google.protobuf.Timestamp` imports (used by other services like Cart and Product) but PaymentService messages do not use them. No `Cache-Control` or freshness headers.
- **Gap**: No temporal metadata on payment transactions. An agent cannot determine when a charge was processed or verify transaction freshness.
- **Compensating Controls**:
  - Simulated processor — temporal accuracy is less critical for fake transactions
  - Agent orchestration layer can timestamp charge requests/responses externally
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `processed_at` timestamp to `ChargeResponse`. Use `google.protobuf.Timestamp` (already imported in proto).
- **Evidence**: `protos/demo.proto`, `src/paymentservice/charge.js`

### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK
- **Finding**: CI exists (Cloud Build + Skaffold + GitHub Actions). Proto versioned (`hipstershop.v1`). `protos/buf.yaml` with STANDARD lint and FILE-level breaking change detection configured. However, `buf breaking` is not integrated into CI pipeline. No paymentservice-specific contract tests. No consumer-driven contract testing (Pact). Protobuf wire compatibility provides implicit backward compatibility for additive changes only.
- **Gap**: `buf breaking` not in CI. No contract tests for the Charge RPC. Breaking changes to PCI-handling proto messages could silently break agent tool bindings.
- **Compensating Controls**:
  - `buf.yaml` configuration exists — CI integration is a configuration step, not a new tool adoption
  - Protobuf backward compatibility rules prevent most accidental breaks
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add `buf breaking` to CI pipeline. Add PaymentService-specific contract tests validating Charge request/response schema.
- **Evidence**: `cloudbuild.yaml`, `.github/workflows/ci-pr.yaml`, `protos/buf.yaml`, `protos/demo.proto`

### ENG-Q3: Rollback Capability
- **Severity**: RISK
- **Finding**: K8s Deployment with rollout history. Skaffold deployment. Manual rollback via `kubectl rollout undo`. No automated rollback triggers. No canary deployment. Liveness/readiness probes (gRPC health check on port 50051) prevent traffic to unhealthy pods. Monitoring alerts can trigger manual rollback. For a P0 PCI service, automated rollback is important.
- **Gap**: No automated rollback on service degradation. Manual rollback only. P0 payment service requires faster recovery.
- **Compensating Controls**:
  - gRPC health probes prevent traffic to unhealthy pods
  - Monitoring alerts (see OBS-Q2) enable faster manual response
  - HPA provides capacity buffer during degraded deployments
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure automated rollback using Flagger or Argo Rollouts with canary analysis. For a P0 PCI service, target rollback within 5 minutes of degradation detection.
- **Evidence**: `cloudbuild.yaml`, `helm-chart/templates/paymentservice.yaml`

---

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: Well-documented gRPC interface in `protos/demo.proto` with `PaymentService` defining a single `Charge` RPC. Proto uses versioned package `hipstershop.v1`. Data classification comment marks PaymentService as PCI with field-level annotations on `CreditCardInfo`. Implemented in `server.js` with `ChargeServiceHandler` binding to `hipsterShopPackage.PaymentService.service`. Health check service also registered.
- **Implication**: gRPC interface can be used directly as agent tool binding. Proto enables auto-generated client code. PCI classification comments inform agent access policy.
- **Recommendation**: No remediation needed.
- **Evidence**: `protos/demo.proto`, `src/paymentservice/server.js`

### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The `Charge` RPC is a write operation — it processes a payment and returns a `transaction_id`. No idempotency key support. Each call generates a new UUID via `uuidv4()`. In a write-enabled scope, duplicate charges would occur on retry. Payment is simulated (no real charges).
- **Implication**: No idempotency concerns for read-only scope. Critical gap if agent scope expands to write-enabled — duplicate charges are a PCI compliance and financial risk.
- **Recommendation**: Implement idempotency key support in `ChargeRequest` before enabling write-enabled agent scope.
- **Evidence**: `src/paymentservice/charge.js`, `protos/demo.proto`

### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: gRPC Protocol Buffers — strongly-typed binary format. `ChargeResponse` contains a single `transaction_id` (string) field. `ChargeRequest` contains `Money` (structured amount) and `CreditCardInfo` (PCI-annotated fields). Protobuf provides explicit types and field numbers.
- **Implication**: Protobuf is highly structured. Minimal response payload (single field) is easy for agents to parse. PCI field annotations inform data handling requirements.
- **Recommendation**: No action needed.
- **Evidence**: `protos/demo.proto`

### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: No event emission. The `Charge` RPC is fire-and-forget — returns a `transaction_id` with no webhook, no SNS/EventBridge integration, no Kafka topic. State changes (successful charges) are not published as events.
- **Implication**: Agents cannot subscribe to payment completion events. Polling is the only option for payment status verification (and no polling endpoint exists — see STATE-Q2).
- **Recommendation**: Publish charge completion events to an event bus (SNS/EventBridge) for downstream consumers and agent-reactive patterns.
- **Evidence**: `src/paymentservice/server.js`, `src/paymentservice/charge.js`

### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit headers on paymentservice responses. The EnvoyFilter in `istio-manifests/rate-limit.yaml` adds `x-rate-limit-limit` and `x-rate-limit-remaining` headers but only for the frontend workload. Internal ClusterIP service with no API Gateway.
- **Implication**: Agents calling paymentservice cannot self-throttle based on server-side rate limit signals.
- **Recommendation**: When rate limiting is extended to paymentservice (see STATE-Q5), configure the EnvoyFilter to include rate limit response headers.
- **Evidence**: `istio-manifests/rate-limit.yaml`, `helm-chart/templates/paymentservice.yaml`

### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: Istio AuthorizationPolicy is enabled (`authorizationPolicies.create: true`), providing mTLS-based identity verification. Callers restricted to `checkoutservice` service account principal. Istio sidecars enabled (`sidecars.create: true`). NetworkPolicies enabled (`networkPolicies.create: true`), restricting ingress to checkoutservice pods on port 50051. The gRPC server uses `grpc.ServerCredentials.createInsecure()` — standard for Istio-proxied services where mTLS terminates at the sidecar.
- **Implication**: Machine identity is authenticated at the mesh layer via mTLS with per-service principal attribution. Satisfies core requirement for agent identity verification. PCI service has tighter caller restrictions (checkoutservice only).
- **Recommendation**: For defense in depth on a PCI service, implement a gRPC interceptor that extracts Istio peer identity from request headers for application-level audit logging.
- **Evidence**: `helm-chart/values.yaml`, `helm-chart/templates/paymentservice.yaml`, `src/paymentservice/server.js`

### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No audit logging at the application layer. Pino logger outputs operational messages (startup, transaction processed with last-4 digits and amount). No principal attribution in logs. Logs are ephemeral container stdout. OpenTelemetry tracing is enabled (`ENABLE_TRACING=1`) with OTel Collector deployed — provides request-level trace context but not audit-grade attribution. `charge.js` logs partial PCI data (card type, last 4 digits).
- **Implication**: For a read-only agent, audit risk is moderate. However, this is a PCI service — audit logging with principal attribution becomes critical if agent scope expands to write-enabled.
- **Recommendation**: Add structured audit logging with caller identity (from Istio mTLS peer identity). Review PCI-DSS requirements for log content.
- **Evidence**: `src/paymentservice/charge.js`, `src/paymentservice/logger.js`, `helm-chart/values.yaml`

### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The `Charge` RPC is a single-step operation — validate card, generate UUID, return. No multi-step workflow. No persistent state to roll back. No saga pattern. The simulated payment has no real side effects to compensate.
- **Implication**: No compensation concerns for simulated payments. Critical gap if integrated with a real payment gateway — failed partial charges need compensation.
- **Recommendation**: Implement refund/void RPCs as compensation mechanisms before integrating with a real payment gateway.
- **Evidence**: `src/paymentservice/charge.js`, `src/paymentservice/server.js`

### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: INFO
- **Finding**: Paymentservice has no outbound service calls — it receives `ChargeRequest`, validates the card locally using `simple-card-validator`, generates a UUID, and returns. No HTTP clients, no gRPC stubs to other services, no external API calls. The Istio Sidecar egress is limited to `istio-system` and the OTel collector only.
- **Implication**: No external dependencies requiring circuit breakers. Positive finding — minimal failure surface.
- **Recommendation**: Implement circuit breakers when integrating with a real payment gateway (external dependency).
- **Evidence**: `src/paymentservice/charge.js`, `helm-chart/templates/paymentservice.yaml`

### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No transaction limits. Each `Charge` call processes independently with no per-caller caps, no maximum charge amount, no daily transaction limits. The simulated processor accepts any amount.
- **Implication**: For read-only scope, blast radius is minimal. For write-enabled scope, absence of transaction limits on a payment service is a critical financial risk.
- **Recommendation**: Implement configurable transaction limits (max charge amount, max charges per hour per caller) before enabling write-enabled agent scope.
- **Evidence**: `src/paymentservice/charge.js`, `src/paymentservice/server.js`

### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO
- **Finding**: PCI data is classified at the field level. Proto includes "Data Classification: PCI (credit card data subject to PCI-DSS)" and "Classification: PCI — All fields are PCI-DSS regulated" on `CreditCardInfo`. Individual fields annotated: `credit_card_number` as "PCI: Primary Account Number (PAN)", `credit_card_cvv` as "PCI: Card Verification Value". `DATA_CLASSIFICATION.md` classifies paymentservice as PCI with sensitive fields `CreditCardInfo.*`. Agent access policy states: "No agent may access PCI fields without PCI-DSS compliance verification."
- **Implication**: PCI data is comprehensively classified in both proto and documentation. Agent access policy explicitly restricts PCI field access. Positive finding.
- **Recommendation**: Maintain classification documentation. Enforce PCI access policy at the AuthorizationPolicy level.
- **Evidence**: `protos/demo.proto`, `DATA_CLASSIFICATION.md`

### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: PCI data (credit card numbers, CVV) is subject to PCI-DSS requirements. The simulated processor does not persist card data — it validates and discards. No cross-region replication. `DATA_CLASSIFICATION.md` agent access policy prohibits agent access to PCI fields without PCI-DSS compliance verification.
- **Implication**: For read-only scope, data residency risk is moderate — an agent reading charge responses only sees `transaction_id` (non-PCI). The risk is in the request path where `CreditCardInfo` is transmitted.
- **Recommendation**: Ensure agent orchestration layer never passes `CreditCardInfo` fields to LLM context. Implement PCI field filtering at the agent tool definition level.
- **Evidence**: `DATA_CLASSIFICATION.md`, `protos/demo.proto`, `src/paymentservice/charge.js`

### DATA-Q3: Selective Query Support
- **Severity**: INFO
- **Finding**: The `Charge` RPC is a single-operation endpoint, not a list/query endpoint. No pagination, filtering, or sorting needed — each call processes one charge and returns one `transaction_id`. No unbounded result sets.
- **Implication**: No selective query concerns. Single-operation design is inherently bounded.
- **Recommendation**: If transaction history query is added (see STATE-Q2), implement pagination and filtering from the start.
- **Evidence**: `protos/demo.proto`

### DATA-Q6: PII Redaction in Logs
- **Severity**: INFO
- **Finding**: `charge.js` logs `Transaction processed: {cardType} ending {last4} Amount: {currency}{units}.{nanos}`. This includes partial card data (card type and last 4 digits) which is permitted under PCI-DSS (last 4 digits are not considered sensitive). `server.js` logs the full `ChargeRequest` via `JSON.stringify(call.request)` — this includes the full credit card number, CVV, and expiration in the log output. This is a PCI-DSS violation (Requirement 3.4 — render PAN unreadable).
- **Implication**: Full PCI data (PAN, CVV) is logged via `JSON.stringify(call.request)` in `server.js`. This is a PCI-DSS compliance issue regardless of agent scope.
- **Recommendation**: Remove or redact `JSON.stringify(call.request)` in `server.js` `ChargeServiceHandler`. Implement a PCI-aware log scrubber that masks card numbers and CVV before logging.
- **Evidence**: `src/paymentservice/server.js`, `src/paymentservice/charge.js`

### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: Card validation uses `simple-card-validator` library for card type detection and validity checking. Expiration date validation compares against current date. Amount validation is implicit (protobuf typing). No quality monitoring for transaction success rates or validation failure rates.
- **Implication**: Card validation provides input quality gates. No runtime quality degradation risk for simulated processor. Quality metrics become important with a real payment gateway.
- **Recommendation**: Publish metrics for card validation failure rates and transaction success rates when integrating with a real payment gateway.
- **Evidence**: `src/paymentservice/charge.js`, `src/paymentservice/package.json`

### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: INFO
- **Finding**: Proto uses versioned package `hipstershop.v1`. `protos/buf.yaml` with STANDARD lint rules and FILE-level breaking change detection. PCI field annotations provide data classification context within the schema. `buf breaking` configured but not yet in CI (tracked under ENG-Q2).
- **Implication**: Schema versioning is established. Proto versioning enables safe evolution. `buf` tooling provides a path to automated breaking change detection.
- **Recommendation**: Add `buf breaking` to CI pipeline (tracked under ENG-Q2).
- **Evidence**: `protos/demo.proto`, `protos/buf.yaml`

### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Clear semantic names: `credit_card_number`, `credit_card_cvv`, `credit_card_expiration_year`, `credit_card_expiration_month`, `transaction_id`, `currency_code`, `units`, `nanos`. PCI classification comments provide additional semantic context. No abbreviations or legacy codes.
- **Implication**: LLMs can interpret fields directly. PCI annotations provide data handling context. No translation or data dictionary needed.
- **Recommendation**: No action needed.
- **Evidence**: `protos/demo.proto`

### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal data catalog. Proto file with PCI data classification comments. `DATA_CLASSIFICATION.md` provides service-level data ownership, classification taxonomy, and agent access policy. Self-describing proto with semantic field names and PCI annotations.
- **Implication**: `DATA_CLASSIFICATION.md` provides portfolio-level data governance context with explicit PCI handling rules. Sufficient for agent tool definition.
- **Recommendation**: Register in organization API catalog. Ensure PCI classification is propagated to any service registry or API gateway catalog.
- **Evidence**: `protos/demo.proto`, `DATA_CLASSIFICATION.md`

### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: INFO
- **Finding**: OpenTelemetry tracing is enabled via `ENABLE_TRACING=1` environment variable. `index.js` initializes the OpenTelemetry Node SDK with `OTLPTraceExporter` pointing to the OTel Collector (`COLLECTOR_SERVICE_ADDR`), `GrpcInstrumentation` for automatic gRPC span creation, and service name `paymentservice`. OTel Collector is deployed (`opentelemetryCollector.create: true`). Metrics enabled (`metrics: true`). Pino logger provides structured JSON logging with severity levels. No trace_id correlation in Pino log entries.
- **Implication**: Distributed tracing is operational with automatic gRPC instrumentation. Trace context enables end-to-end request correlation. Structured JSON logs via Pino. The gap (no trace_id in log entries) is minor.
- **Recommendation**: Add trace_id to Pino log context for log-to-trace correlation. Use `@opentelemetry/instrumentation-pino` for automatic injection.
- **Evidence**: `src/paymentservice/index.js`, `src/paymentservice/logger.js`, `helm-chart/values.yaml`, `src/paymentservice/package.json`

### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: INFO
- **Finding**: Prometheus alerting rules in `kubernetes-manifests/monitoring-alerts.yaml`: `HighGrpcErrorRate` (1%, 5m), `CriticalGrpcErrorRate` (5%, 2m), `HighP95Latency` (500ms, 5m), `ServiceDown`. Alerts apply to all gRPC services including paymentservice. Metrics enabled (`metrics: true`). K8s health probes (gRPC liveness + readiness on port 50051). HPA configured (1–5 replicas).
- **Implication**: Alerting infrastructure is comprehensive. Payment service degradation will be detected before agents cascade failures. Both error rate and latency thresholds configured with appropriate severity levels.
- **Recommendation**: Consider tighter alert thresholds for the P0 payment service (e.g., 0.5% error rate warning, 200ms P95 latency) given its critical-path position.
- **Evidence**: `kubernetes-manifests/monitoring-alerts.yaml`, `helm-chart/values.yaml`, `helm-chart/templates/paymentservice.yaml`, `kubernetes-manifests/hpa.yaml`

### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics. Operational logging and OpenTelemetry metrics provide infrastructure-level visibility. No payment success rate, decline rate, or average transaction value metrics.
- **Implication**: No business outcome monitoring. For a P0 payment service, business metrics (charge success rate, decline rate by card type, average transaction value) are important for measuring agent interaction quality.
- **Recommendation**: Publish custom metrics for charge success/failure rates, decline reasons, and transaction values.
- **Evidence**: `src/paymentservice/charge.js`, `src/paymentservice/server.js`

### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: INFO
- **Finding**: Comprehensive IaC: Helm chart defines Deployment, Service, ServiceAccount, NetworkPolicy, Sidecar, and AuthorizationPolicy for paymentservice. All security policies enabled (`authorizationPolicies.create: true`, `networkPolicies.create: true`, `sidecars.create: true`). Security context enforced (non-root, read-only root filesystem, dropped capabilities). CODEOWNERS enforces peer review. GitHub Actions CI. No drift detection.
- **Implication**: Infrastructure governance is strong. All security controls are IaC-defined and enabled. The drift detection gap is minor for K8s-native deployment with Helm reconciliation.
- **Recommendation**: Implement drift detection or GitOps (ArgoCD/Flux). For a P0 PCI service, drift detection is more important than for non-critical services.
- **Evidence**: `helm-chart/templates/paymentservice.yaml`, `helm-chart/values.yaml`, `.github/CODEOWNERS`, `.github/workflows/ci-pr.yaml`

### ENG-Q4: API Test Coverage
- **Severity**: INFO
- **Finding**: No paymentservice-specific tests. `package.json` scripts section has `"test": "echo \"Error: no test specified\" && exit 1"`. No test dependencies (no mocha, jest, or tap). CI smoke test via loadgenerator exercises the `Charge` RPC indirectly through the checkout flow. Card validation logic in `charge.js` is untested.
- **Implication**: Zero test coverage on a PCI service. Card validation edge cases (expired cards, unsupported card types, invalid numbers) are untested.
- **Recommendation**: Add unit tests for `charge.js` (valid/invalid cards, expired cards, unsupported types, edge cases). Add gRPC integration tests for the `Charge` RPC. Include in CI.
- **Evidence**: `src/paymentservice/package.json`, `src/paymentservice/charge.js`

### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: INFO
- **Finding**: The paymentservice has no persistent data store — transaction IDs are generated in-memory via `uuidv4()` and returned without persistence. No database, no cache, no file storage. Credit card data is validated and discarded within the request lifecycle. No data at rest to encrypt.
- **Implication**: No persistent data store exists. Encryption at rest becomes relevant when persistent transaction storage is added (see DATA-Q4).
- **Recommendation**: Implement encryption at rest (KMS) when adding persistent transaction storage. PCI-DSS Requirement 3.4 mandates rendering PAN unreadable anywhere it is stored.
- **Evidence**: `src/paymentservice/charge.js`, `src/paymentservice/server.js`

### HITL-Q3: Sandbox/Staging Environment
- **Severity**: INFO
- **Finding**: Skaffold local dev. Cloud Build deploys to GKE staging. CI per-PR ephemeral namespaces. No persistent agent-specific testing environment. Docker-based local development via Skaffold + minikube.
- **Implication**: For a read-only agent on a simulated payment processor, existing CI infrastructure provides adequate testing. A persistent staging environment becomes critical before write-enabled agent scope on a real payment gateway.
- **Recommendation**: Create persistent staging namespace with simulated payment gateway for agent integration testing before expanding scope.
- **Evidence**: `cloudbuild.yaml`, `src/paymentservice/Dockerfile`, `.github/workflows/ci-pr.yaml`

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: Well-documented gRPC interface in `protos/demo.proto` with `PaymentService` defining a single `Charge` RPC. Proto uses versioned package `hipstershop.v1`. PCI data classification comments on `CreditCardInfo` and `PaymentService`. Implemented in `server.js` with `ChargeServiceHandler`.
- **Gap**: None — BLOCKER criteria satisfied.
- **Recommendation**: No remediation needed.
- **Evidence**: `protos/demo.proto`, `src/paymentservice/server.js`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK
- **Finding**: `protos/demo.proto` is machine-readable with `buf.yaml` governance. No gRPC server reflection enabled.
- **Gap**: No runtime schema discovery via gRPC reflection.
- **Recommendation**: Enable gRPC server reflection via `@grpc/reflection`.
- **Evidence**: `protos/demo.proto`, `protos/buf.yaml`, `src/paymentservice/server.js`

#### API-Q3: Structured Error Responses
- **Severity**: RISK
- **Finding**: Typed error classes (`InvalidCreditCard`, `UnacceptedCreditCard`, `ExpiredCreditCard`) exist but are not mapped to gRPC rich error model. No retryable boolean, no structured error body.
- **Gap**: Agents cannot distinguish retriable from terminal errors programmatically.
- **Recommendation**: Map error classes to gRPC rich error model with metadata.
- **Evidence**: `src/paymentservice/charge.js`, `src/paymentservice/server.js`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: `Charge` RPC generates new UUID per call via `uuidv4()`. No idempotency key. Simulated payment — no real financial side effects.
- **Gap**: No idempotency. Critical if scope expands to write-enabled.
- **Recommendation**: Implement idempotency key in `ChargeRequest` before write-enabled scope.
- **Evidence**: `src/paymentservice/charge.js`, `protos/demo.proto`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: gRPC Protocol Buffers. `ChargeResponse` contains single `transaction_id` string. Strongly typed with field numbers.
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
- **Finding**: No event emission for charge completion. Fire-and-forget pattern. No webhook, SNS, EventBridge, or Kafka integration.
- **Gap**: Agents cannot subscribe to payment events.
- **Recommendation**: Publish charge completion events to an event bus.
- **Evidence**: `src/paymentservice/server.js`, `src/paymentservice/charge.js`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit headers on paymentservice. EnvoyFilter targets frontend only.
- **Gap**: Agents cannot self-throttle based on server-side signals.
- **Recommendation**: Extend EnvoyFilter rate limit headers to paymentservice.
- **Evidence**: `istio-manifests/rate-limit.yaml`, `helm-chart/templates/paymentservice.yaml`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: Istio mTLS via AuthorizationPolicy restricts callers to `checkoutservice` principal. Sidecars and NetworkPolicies enabled. `createInsecure()` is standard for Istio-proxied services.
- **Gap**: None — mesh-level mTLS with per-service AuthorizationPolicy satisfies machine identity authentication.
- **Recommendation**: Implement gRPC interceptor for application-level audit logging of peer identity.
- **Evidence**: `helm-chart/values.yaml`, `helm-chart/templates/paymentservice.yaml`, `src/paymentservice/server.js`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK
- **Finding**: AuthorizationPolicy restricts to `checkoutservice` on `/hipstershop.PaymentService/Charge`. No agent-specific service accounts.
- **Gap**: No agent-specific service accounts with tailored permissions.
- **Recommendation**: Create agent-specific service accounts with per-RPC AuthorizationPolicy rules.
- **Evidence**: `helm-chart/templates/paymentservice.yaml`, `helm-chart/values.yaml`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicy defines per-path rules. No application-layer authorization — gRPC server accepts all calls that reach it.
- **Gap**: No application-layer authorization. Mesh bypass exposes Charge RPC.
- **Recommendation**: Implement gRPC interceptor for action-level authorization. Critical for PCI service.
- **Evidence**: `src/paymentservice/server.js`, `helm-chart/templates/paymentservice.yaml`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: RISK
- **Finding**: No JWT parsing, token exchange, or user context headers. `ChargeRequest` has no user identity field. Cannot distinguish agent-initiated vs human-initiated charges.
- **Gap**: No identity propagation. PCI compliance concern for payment attribution.
- **Recommendation**: Add user identity propagation via gRPC metadata headers.
- **Evidence**: `src/paymentservice/server.js`, `protos/demo.proto`, `helm-chart/values.yaml`

#### AUTH-Q5: Credential Management
- **Severity**: RISK
- **Finding**: No credentials used — simulated payment processor. No Secrets Manager or Vault integration.
- **Gap**: No credential management framework for future payment gateway integration.
- **Recommendation**: Adopt K8s external secrets operator or AWS Secrets Manager when integrating real payment gateway.
- **Evidence**: `src/paymentservice/charge.js`, `src/paymentservice/package.json`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No audit logging. Pino operational logs only. No principal attribution. OTel tracing enabled but not audit-grade. `server.js` logs full `ChargeRequest` including PCI data via `JSON.stringify`.
- **Gap**: No immutable audit trail. PCI data in logs is a compliance concern.
- **Recommendation**: Add structured audit logging with caller identity. Remove PCI data from log output.
- **Evidence**: `src/paymentservice/server.js`, `src/paymentservice/charge.js`, `helm-chart/values.yaml`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK
- **Finding**: AuthorizationPolicy and NetworkPolicy provide manual suspension mechanisms. No automated suspension.
- **Gap**: No automated or rapid suspension. Manual policy changes required.
- **Recommendation**: Implement automated suspension via AuthorizationPolicy updates triggered by anomaly detection.
- **Evidence**: `helm-chart/templates/paymentservice.yaml`, `helm-chart/values.yaml`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Single-step operation. No persistent state. Simulated payment with no real side effects. No refund/void RPCs.
- **Gap**: No compensation mechanisms. Critical gap for real payment gateway integration.
- **Recommendation**: Implement refund/void RPCs before integrating with real payment gateway.
- **Evidence**: `src/paymentservice/charge.js`, `src/paymentservice/server.js`

#### STATE-Q2: Queryable Current State
- **Severity**: RISK
- **Finding**: Only `Charge` RPC exists — no query endpoint. No transaction lookup or status verification. Service is stateless (UUIDs generated and discarded).
- **Gap**: No queryable state. Agent cannot verify previous charge status.
- **Recommendation**: Add `GetTransaction` RPC or transaction status endpoint.
- **Evidence**: `protos/demo.proto`, `src/paymentservice/server.js`

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled AND service has persistent state
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: INFO
- **Finding**: Paymentservice has no outbound service calls — validates card locally, generates UUID, returns. No external dependencies. Istio Sidecar egress limited to `istio-system` and OTel collector.
- **Gap**: No external dependencies requiring circuit breakers. Positive finding.
- **Recommendation**: Implement circuit breakers when integrating with a real payment gateway.
- **Evidence**: `src/paymentservice/charge.js`, `helm-chart/templates/paymentservice.yaml`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK
- **Finding**: EnvoyFilter rate limiting targets frontend only. No rate limiting on paymentservice. HPA provides scaling (1–5 replicas) but not request capping.
- **Gap**: No rate limiting on P0 PCI service. Runaway agent loop risk.
- **Recommendation**: Create EnvoyFilter targeting paymentservice with conservative rate limits.
- **Evidence**: `istio-manifests/rate-limit.yaml`, `kubernetes-manifests/hpa.yaml`, `helm-chart/values.yaml`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No transaction limits. No per-caller caps. Simulated processor accepts any amount.
- **Gap**: None for read-only scope. Critical for write-enabled scope.
- **Recommendation**: Implement transaction limits before write-enabled agent scope.
- **Evidence**: `src/paymentservice/charge.js`, `src/paymentservice/server.js`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: RISK
- **Finding**: HPA configured (1–5 replicas, 70% CPU). Resource limits set. No load test results. No traffic isolation between agent and checkout traffic.
- **Gap**: No capacity planning for agent traffic on P0 service.
- **Recommendation**: Conduct load testing. Consider separate traffic lanes for agent vs human requests.
- **Evidence**: `kubernetes-manifests/hpa.yaml`, `helm-chart/templates/paymentservice.yaml`, `helm-chart/values.yaml`

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
- **Severity**: INFO
- **Finding**: Skaffold local dev. Cloud Build deploys to GKE staging. CI per-PR ephemeral namespaces. No persistent agent-specific testing environment.
- **Gap**: No dedicated agent testing environment. Acceptable for read-only pilot on simulated processor.
- **Recommendation**: Create persistent staging namespace with simulated payment gateway for agent testing.
- **Evidence**: `cloudbuild.yaml`, `src/paymentservice/Dockerfile`, `.github/workflows/ci-pr.yaml`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO
- **Finding**: PCI data classified at field level in proto and `DATA_CLASSIFICATION.md`. `CreditCardInfo` fields annotated as PCI-DSS regulated. Agent access policy explicitly restricts PCI field access.
- **Gap**: None — comprehensive PCI classification. Positive finding.
- **Recommendation**: Maintain classification. Enforce PCI access policy at AuthorizationPolicy level.
- **Evidence**: `protos/demo.proto`, `DATA_CLASSIFICATION.md`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: PCI data subject to PCI-DSS. Simulated processor does not persist card data. Agent access policy prohibits PCI field access without compliance verification.
- **Gap**: PCI data must not be transmitted to LLM providers. Risk is in request path (CreditCardInfo).
- **Recommendation**: Ensure agent orchestration never passes CreditCardInfo to LLM context.
- **Evidence**: `DATA_CLASSIFICATION.md`, `protos/demo.proto`, `src/paymentservice/charge.js`

#### DATA-Q3: Selective Query Support
- **Severity**: INFO
- **Finding**: Single-operation endpoint (`Charge`). No list/query endpoints. No unbounded result sets.
- **Gap**: None — single-operation design is inherently bounded.
- **Recommendation**: Implement pagination if transaction history query is added.
- **Evidence**: `protos/demo.proto`

#### DATA-Q4: System of Record Designations
- **Severity**: RISK
- **Finding**: Documented as system of record for payment transactions in `DATA_CLASSIFICATION.md` and proto. However, no persistent storage — transaction IDs generated and discarded.
- **Gap**: System-of-record designation documented but not implemented. No persistent transaction store.
- **Recommendation**: Implement persistent transaction storage for real payment processor.
- **Evidence**: `DATA_CLASSIFICATION.md`, `protos/demo.proto`, `src/paymentservice/charge.js`

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK
- **Finding**: `ChargeResponse` has no timestamps. `google.protobuf.Timestamp` imported but not used by PaymentService messages.
- **Gap**: No temporal metadata on transactions.
- **Recommendation**: Add `processed_at` timestamp to `ChargeResponse`.
- **Evidence**: `protos/demo.proto`, `src/paymentservice/charge.js`

#### DATA-Q6: PII Redaction in Logs
- **Severity**: INFO
- **Finding**: `server.js` logs full `ChargeRequest` via `JSON.stringify(call.request)` including PAN and CVV. `charge.js` logs last-4 digits only (PCI-compliant). Full PCI data in `server.js` logs is a PCI-DSS violation.
- **Gap**: PCI data (PAN, CVV) logged in plaintext via `JSON.stringify`.
- **Recommendation**: Remove or redact `JSON.stringify(call.request)` in `ChargeServiceHandler`. Implement PCI-aware log scrubber.
- **Evidence**: `src/paymentservice/server.js`, `src/paymentservice/charge.js`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: Card validation via `simple-card-validator`. Expiration date validation. No quality metrics for transaction success/failure rates.
- **Gap**: No quality monitoring. Input validation provides quality gates.
- **Recommendation**: Publish validation failure rate metrics when integrating real payment gateway.
- **Evidence**: `src/paymentservice/charge.js`, `src/paymentservice/package.json`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: INFO
- **Finding**: Proto versioned (`hipstershop.v1`). `buf.yaml` with STANDARD lint and FILE-level breaking change detection. PCI annotations in schema. `buf breaking` not in CI.
- **Gap**: `buf breaking` not in CI (tracked under ENG-Q2).
- **Recommendation**: Add `buf breaking` to CI pipeline.
- **Evidence**: `protos/demo.proto`, `protos/buf.yaml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Clear names: `credit_card_number`, `credit_card_cvv`, `transaction_id`, `currency_code`. PCI annotations provide additional context. No abbreviations.
- **Gap**: None.
- **Recommendation**: No action needed.
- **Evidence**: `protos/demo.proto`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal catalog. Proto with PCI annotations. `DATA_CLASSIFICATION.md` provides taxonomy and agent access policy.
- **Gap**: No formal catalog. Sufficient with `DATA_CLASSIFICATION.md`.
- **Recommendation**: Register in organization API catalog with PCI classification propagated.
- **Evidence**: `protos/demo.proto`, `DATA_CLASSIFICATION.md`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: INFO
- **Finding**: OTel Node SDK with `GrpcInstrumentation`, `OTLPTraceExporter` to collector. Pino structured JSON logging. Metrics enabled. No trace_id in Pino log entries.
- **Gap**: No trace_id in log entries (minor).
- **Recommendation**: Add `@opentelemetry/instrumentation-pino` for automatic trace_id injection.
- **Evidence**: `src/paymentservice/index.js`, `src/paymentservice/logger.js`, `helm-chart/values.yaml`, `src/paymentservice/package.json`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: INFO
- **Finding**: Prometheus alerting rules: `HighGrpcErrorRate` (1%, 5m), `CriticalGrpcErrorRate` (5%, 2m), `HighP95Latency` (500ms, 5m), `ServiceDown`. Applies to all gRPC services. Health probes configured. HPA active.
- **Gap**: None — comprehensive alerting. Consider tighter thresholds for P0 service.
- **Recommendation**: Tighten alert thresholds for P0 payment service.
- **Evidence**: `kubernetes-manifests/monitoring-alerts.yaml`, `helm-chart/values.yaml`, `helm-chart/templates/paymentservice.yaml`, `kubernetes-manifests/hpa.yaml`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics. No charge success rate, decline rate, or transaction value metrics.
- **Gap**: No business outcome monitoring for P0 payment service.
- **Recommendation**: Publish charge success/failure rates, decline reasons, and transaction value metrics.
- **Evidence**: `src/paymentservice/charge.js`, `src/paymentservice/server.js`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: INFO
- **Finding**: Comprehensive Helm IaC: Deployment, Service, ServiceAccount, NetworkPolicy, Sidecar, AuthorizationPolicy. All security policies enabled. Hardened security context. CODEOWNERS. GitHub Actions CI. No drift detection.
- **Gap**: No drift detection (minor for K8s-native with Helm).
- **Recommendation**: Implement drift detection or GitOps. Higher priority for P0 PCI service.
- **Evidence**: `helm-chart/templates/paymentservice.yaml`, `helm-chart/values.yaml`, `.github/CODEOWNERS`, `.github/workflows/ci-pr.yaml`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK
- **Finding**: CI exists. Proto versioned. `buf.yaml` configured. `buf breaking` not in CI. No paymentservice-specific contract tests.
- **Gap**: No breaking change detection in CI for PCI-handling proto messages.
- **Recommendation**: Add `buf breaking` to CI. Add PaymentService contract tests.
- **Evidence**: `cloudbuild.yaml`, `.github/workflows/ci-pr.yaml`, `protos/buf.yaml`, `protos/demo.proto`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK
- **Finding**: K8s Deployment rollout. Manual rollback only. No canary. gRPC health probes. Monitoring alerts enable faster manual response.
- **Gap**: No automated rollback for P0 PCI service.
- **Recommendation**: Configure automated rollback with Flagger or Argo Rollouts.
- **Evidence**: `cloudbuild.yaml`, `helm-chart/templates/paymentservice.yaml`

#### ENG-Q4: API Test Coverage
- **Severity**: INFO
- **Finding**: Zero test coverage. `package.json` has no test script. No test dependencies. Card validation logic untested.
- **Gap**: No tests on PCI service. Higher risk than non-PCI services.
- **Recommendation**: Add unit tests for `charge.js` and gRPC integration tests for `Charge` RPC.
- **Evidence**: `src/paymentservice/package.json`, `src/paymentservice/charge.js`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: INFO
- **Finding**: No persistent data store — transaction IDs generated in-memory and returned without persistence. No database, no cache, no file storage. Credit card data validated and discarded within request lifecycle.
- **Gap**: None — no persistent data store exists. Relevant when persistent storage is added (see DATA-Q4).
- **Recommendation**: Implement encryption at rest (KMS) when adding persistent transaction storage. PCI-DSS Requirement 3.4 mandates rendering PAN unreadable anywhere it is stored.
- **Evidence**: `src/paymentservice/charge.js`, `src/paymentservice/server.js`

---

## Evidence Index

### Infrastructure as Code
| File | Questions Referenced |
|------|---------------------|
| `helm-chart/templates/paymentservice.yaml` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q7, API-Q8, STATE-Q4, STATE-Q5, STATE-Q7, ENG-Q1, ENG-Q3 |
| `helm-chart/values.yaml` | AUTH-Q1, AUTH-Q2, AUTH-Q4, AUTH-Q6, AUTH-Q7, OBS-Q1, OBS-Q2, ENG-Q1, STATE-Q5, STATE-Q7 |
| `kubernetes-manifests/hpa.yaml` | STATE-Q5, STATE-Q7, OBS-Q2 |
| `kubernetes-manifests/monitoring-alerts.yaml` | OBS-Q2 |
| `istio-manifests/rate-limit.yaml` | STATE-Q5, API-Q8 |

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `src/paymentservice/server.js` | API-Q1, API-Q2, API-Q3, API-Q7, AUTH-Q1, AUTH-Q3, AUTH-Q4, AUTH-Q6, STATE-Q1, STATE-Q2, STATE-Q6, DATA-Q6, OBS-Q3, ENG-Q5 |
| `src/paymentservice/charge.js` | API-Q3, API-Q4, API-Q7, AUTH-Q5, AUTH-Q6, STATE-Q1, STATE-Q4, STATE-Q6, DATA-Q1, DATA-Q2, DATA-Q4, DATA-Q5, DATA-Q6, DATA-Q7, OBS-Q3, ENG-Q4, ENG-Q5 |
| `src/paymentservice/index.js` | AUTH-Q5, OBS-Q1 |
| `src/paymentservice/logger.js` | AUTH-Q6, OBS-Q1 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `protos/demo.proto` | API-Q1, API-Q2, API-Q4, API-Q5, API-Q7, AUTH-Q4, DATA-Q1, DATA-Q2, DATA-Q3, DATA-Q4, DATA-Q5, DISC-Q1, DISC-Q2, DISC-Q3, ENG-Q2, STATE-Q2 |
| `protos/buf.yaml` | API-Q2, DISC-Q1, ENG-Q2 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `cloudbuild.yaml` | HITL-Q3, ENG-Q2, ENG-Q3 |
| `.github/workflows/ci-pr.yaml` | HITL-Q3, ENG-Q1, ENG-Q2, ENG-Q4 |
| `.github/CODEOWNERS` | ENG-Q1 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `src/paymentservice/Dockerfile` | HITL-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `src/paymentservice/package.json` | AUTH-Q5, OBS-Q1, DATA-Q7, ENG-Q4 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `DATA_CLASSIFICATION.md` | DATA-Q1, DATA-Q2, DATA-Q4, DISC-Q3 |
