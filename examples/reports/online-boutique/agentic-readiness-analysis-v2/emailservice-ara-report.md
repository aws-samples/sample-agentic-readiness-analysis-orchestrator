# Agentic Readiness Analysis Report

**Target**: services/microservices-demo/src/emailservice
**Date**: 2026-04-16
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**Repository Type**: application
**Service Archetype**: event-processor (user-provided)
**Archetype Justification**: Sends order confirmation emails as a side-effect of checkout. No persistent state. Single gRPC RPC (SendOrderConfirmation) called by checkoutservice. Functions as a notification sender.
**Agent Scope**: read-only
**Priority**: P2
**Tags**: python, grpc, notifications
**Context**: Python gRPC service sending order confirmation emails.

---

## Readiness Profile: Pilot-Ready

**BLOCKERs**: 0 | **RISKs**: 7 | **INFOs**: 24

Supervised pilot with: (1) human approval gates on irreversible actions, (2) agent limited to low-blast-radius operations, (3) compensating controls for each open RISK, (4) remediation timeline before expanding scope.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 0 |
| RISK | 7 |
| INFO | 24 |
| N/A | 0 |
| Not Evaluated (extended) | 12 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 7
**Extended Questions Not Triggered**: 12
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: event-processor (user-provided)

---

## BLOCKERs — Must Resolve Before Agent Deployment

No BLOCKERs identified.

---

## RISKs — Proceed with Compensating Controls

### API-Q3: Structured Error Responses
- **Severity**: RISK
- **Finding**: `SendOrderConfirmation` in `email_server.py` uses `context.set_code(grpc.StatusCode.INTERNAL)` and `context.set_details(...)` for both error paths: template rendering failure and email sending failure. No structured error body, no retryable boolean, no error code taxonomy. An agent cannot distinguish a transient email provider failure from a permanent template error.
- **Gap**: No structured error model. Both error types return INTERNAL status.
- **Compensating Controls**:
  - Template errors are deterministic (terminal); email send errors are transient (retry)
  - Wrap agent tool calls with client-side error classification
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Use distinct gRPC status codes: `INTERNAL` for template errors (terminal), `UNAVAILABLE` for email send failures (retryable). Add gRPC rich error details.
- **Evidence**: `src/emailservice/email_server.py` (SendOrderConfirmation error handling)

### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicy defines per-path rules for `SendOrderConfirmation`. The Python gRPC server in `email_server.py` uses `grpc.server(futures.ThreadPoolExecutor(...))` with no interceptor for authorization. All calls reaching the application are accepted without application-layer checks.
- **Gap**: No application-layer authorization. Mesh bypass exposes the RPC.
- **Compensating Controls**:
  - Istio sidecar injection ensures mesh-level enforcement
  - Network policies restrict ingress to checkoutservice only
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement a gRPC server interceptor for authorization as defense in depth.
- **Evidence**: `src/emailservice/email_server.py`, `helm-chart/templates/emailservice.yaml`

### AUTH-Q5: Credential Management
- **Severity**: RISK
- **Finding**: The `EmailService` class (non-dummy) references `project_id`, `region`, `sender_id`, `from_address` variables for the cloud mail client, but these are undefined — the class raises `Exception('cloud mail client not implemented')`. The `DummyEmailService` (active) uses no credentials. No Secrets Manager or Vault integration.
- **Gap**: No credential management framework for when real email client is implemented.
- **Compensating Controls**:
  - Dummy mode eliminates current credential concerns
  - K8s ServiceAccount provides pod identity
- **Remediation Timeline**: When real email client is implemented
- **Recommendation**: Use K8s Secrets with external secrets operator or AWS Secrets Manager when implementing the real email client.
- **Evidence**: `src/emailservice/email_server.py` (EmailService class, DummyEmailService class)

### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK
- **Archetype-Calibrated**: event-processor handling PII (email addresses) — evaluated as RISK
- **Finding**: Python JSON logger (`getJSONLogger`) outputs operational messages. `DummyEmailService.SendOrderConfirmation` logs `request.email` — the email address (PII) is logged directly in plaintext. No principal attribution. Logs are ephemeral container stdout. OpenTelemetry tracing is configured with `GrpcInstrumentorServer` and OTLP exporter but is not audit-grade.
- **Gap**: PII (email address) logged without redaction. No immutable audit trail. No principal attribution.
- **Compensating Controls**:
  - OTel tracing provides request-level correlation
  - Forward container stdout to immutable log aggregation
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Redact email addresses in logs (mask to `u***@domain.com`). Add caller identity from Istio mTLS. Forward to immutable store.
- **Evidence**: `src/emailservice/email_server.py` (DummyEmailService log with request.email), `src/emailservice/logger.py`

### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK
- **Finding**: `DummyEmailService.SendOrderConfirmation` logs the raw email address: `logger.info('A request to send order confirmation email to {} has been received.'.format(request.email))`. The `request.email` field is classified as PII in the proto. No PII redaction framework. Email addresses are logged in plaintext to container stdout.
- **Gap**: PII (email address) logged without redaction. Direct violation of PII handling best practices.
- **Compensating Controls**:
  - Restrict log access to authorized personnel
  - Implement log masking at the aggregation layer
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Mask email addresses in logs: `u***@domain.com`. Implement structured logging with PII field-level masking.
- **Evidence**: `src/emailservice/email_server.py` (DummyEmailService.SendOrderConfirmation)

### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK
- **Finding**: CI exists (Cloud Build + GitHub Actions). Proto versioned (`hipstershop.v1`). `buf.yaml` configured with STANDARD lint and FILE-level breaking change detection. However, `buf breaking` is not wired into CI. No emailservice-specific tests found. No contract tests.
- **Gap**: `buf breaking` not in CI. Zero test coverage for emailservice.
- **Compensating Controls**:
  - Proto versioning provides implicit contract stability
  - DummyEmailService has trivial logic (log and return Empty)
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `buf breaking` to CI. Add unit tests for SendOrderConfirmation template rendering and error handling.
- **Evidence**: `cloudbuild.yaml`, `.github/workflows/ci-pr.yaml`, `protos/buf.yaml`

### ENG-Q4: API Test Coverage
- **Severity**: RISK
- **Finding**: No emailservice-specific tests found. No test files in the emailservice directory. DummyEmailService has trivial logic but the real EmailService class has template rendering and email sending logic that is untested. CI smoke test via loadgenerator exercises the RPC indirectly through checkoutservice.
- **Gap**: Zero test coverage. Template rendering errors and email sending failures are untested.
- **Compensating Controls**:
  - DummyEmailService has trivial logic (log and return Empty)
  - Loadgenerator exercises the RPC indirectly
- **Remediation Timeline**: 30 days
- **Recommendation**: Add unit tests for Jinja2 template rendering, error handling paths, and gRPC response codes.
- **Evidence**: `src/emailservice/email_server.py`, `.github/workflows/ci-pr.yaml`

---

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: gRPC interface in `protos/demo.proto` with `EmailService` defining a single `SendOrderConfirmation` RPC. Proto uses versioned package `hipstershop.v1`. Data classification: "PII (email addresses are personally identifiable)". System of record: "emailservice is a notification sender (no persistent state)".
- **Implication**: gRPC interface is well-documented. Single-RPC surface is simple for agent integration.
- **Recommendation**: No remediation needed.
- **Evidence**: `protos/demo.proto`, `src/emailservice/email_server.py`

### API-Q2: Machine-Readable API Specification
- **Severity**: INFO
- **Finding**: `protos/demo.proto` is machine-readable. Strongly typed with PII classification comments and versioned package. `buf.yaml` provides linting and breaking change detection.
- **Implication**: Agent tool definitions can be auto-generated from proto.
- **Recommendation**: Consider enabling gRPC server reflection for runtime discovery.
- **Evidence**: `protos/demo.proto`, `protos/buf.yaml`

### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: `SendOrderConfirmation` is a fire-and-forget notification. Calling it multiple times with the same order sends duplicate emails — it is not idempotent. However, with read-only agent scope, the agent is not expected to call this RPC directly.
- **Implication**: Duplicate email risk exists but is mitigated by read-only scope and single-caller restriction (checkoutservice only).
- **Recommendation**: Add deduplication by order_id before expanding agent scope.
- **Evidence**: `src/emailservice/email_server.py`

### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: Returns `Empty` message (no response body). The RPC is a command (send email) not a query. Success is indicated by gRPC OK status. Error details provided via `context.set_details()`.
- **Implication**: Empty response is appropriate for fire-and-forget notification. Agent receives success/failure signal via gRPC status.
- **Recommendation**: No action needed.
- **Evidence**: `protos/demo.proto`

### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: EnvoyFilter rate-limit now covers emailservice in addition to frontend. No rate limit headers returned in gRPC metadata. Internal ClusterIP service.
- **Implication**: Agents cannot self-throttle based on server-provided signals.
- **Recommendation**: Add rate limit metadata to gRPC responses when rate limiting is applied.
- **Evidence**: `istio-manifests/rate-limit.yaml`, `helm-chart/templates/emailservice.yaml`

### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: Istio AuthorizationPolicy enabled with mTLS. Callers restricted to `checkoutservice` principal only. Sidecars and network policies enabled. Single-caller restriction is the tightest in the portfolio. Python gRPC server uses `add_insecure_port` — Istio sidecar handles mTLS (standard pattern).
- **Implication**: Machine identity authenticated at mesh layer. Single-caller restriction provides strong access control.
- **Recommendation**: No action needed. Single-caller AuthorizationPolicy is well-scoped.
- **Evidence**: `helm-chart/values.yaml`, `helm-chart/templates/emailservice.yaml`, `src/emailservice/email_server.py`

### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: INFO
- **Archetype-Calibrated**: event-processor with single caller — downgraded to INFO
- **Finding**: Istio AuthorizationPolicy restricts callers to `checkoutservice` service account principal on `/hipstershop.EmailService/SendOrderConfirmation`. Single caller, single RPC — maximally scoped. No agent-specific service accounts defined, but the existing restriction is the tightest possible for this archetype.
- **Implication**: Permissions are already least-privilege for the current access pattern.
- **Recommendation**: Create agent-specific K8s ServiceAccounts if agent needs direct access in the future.
- **Evidence**: `helm-chart/templates/emailservice.yaml`, `helm-chart/values.yaml`

### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Archetype-Calibrated**: event-processor — downgraded to INFO
- **Finding**: No JWT parsing, no token exchange. `SendOrderConfirmationRequest` contains `email` (PII) and `OrderResult` but no caller identity context. Istio mTLS provides implicit caller identity. Single caller (checkoutservice) makes identity propagation less critical.
- **Implication**: For an event-processor with a single caller, identity propagation has lower priority.
- **Recommendation**: Add caller identity to audit logs when audit logging is implemented (see AUTH-Q6).
- **Evidence**: `src/emailservice/email_server.py`, `protos/demo.proto`

### AUTH-Q7: Agent Identity Suspension
- **Severity**: INFO
- **Finding**: Istio AuthorizationPolicy and NetworkPolicy provide suspension mechanisms. Single-caller restriction means suspension is straightforward — remove checkoutservice from the policy. No automated mechanism.
- **Implication**: Manual suspension is feasible via policy update.
- **Recommendation**: Implement automated suspension if agent direct access is added.
- **Evidence**: `helm-chart/templates/emailservice.yaml`, `helm-chart/values.yaml`

### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Email sending is a fire-and-forget side-effect. Once sent, an email cannot be "unsent". DummyEmailService only logs — no actual email is sent. No compensation mechanism exists or is feasible for sent emails.
- **Implication**: Email is inherently non-compensable. DummyEmailService has no side-effects to compensate.
- **Recommendation**: Implement email queuing with delay (e.g., 5-minute send delay) to allow cancellation before actual delivery.
- **Evidence**: `src/emailservice/email_server.py`

### STATE-Q5: Rate Limiting and Throttling
- **Severity**: INFO
- **Finding**: EnvoyFilter rate limiting now includes emailservice (previously only frontend). HPA configured (1–3 replicas at 70% CPU). gRPC server uses `ThreadPoolExecutor(max_workers=10)` providing implicit concurrency limiting. Rate limiting at the mesh layer addresses the primary concern.
- **Implication**: Rate limiting is in place at the mesh layer. Per-recipient limiting is a future enhancement.
- **Recommendation**: Consider per-recipient rate limiting to prevent email flooding when real email client is implemented.
- **Evidence**: `istio-manifests/rate-limit.yaml`, `kubernetes-manifests/hpa.yaml`, `src/emailservice/email_server.py`

### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: DummyEmailService only logs — no actual emails sent. Real EmailService would send actual emails. EnvoyFilter rate limiting now provides mesh-level blast radius control. ThreadPoolExecutor(max_workers=10) provides implicit concurrency cap.
- **Implication**: Blast radius is minimal in dummy mode. Rate limiting provides protection when real email sending is enabled.
- **Recommendation**: Implement per-recipient rate limiting before enabling real email sending.
- **Evidence**: `src/emailservice/email_server.py`, `istio-manifests/rate-limit.yaml`

### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO
- **Finding**: PII classification is comprehensive. Proto classifies: "Data Classification: PII (email addresses are personally identifiable)", `email` field: "Classification: PII", `shipping_address` in OrderResult: "Classification: PII". `DATA_CLASSIFICATION.md` classifies emailservice as PII with sensitive fields `email`, `Address.*`.
- **Implication**: PII classification is documented and consistent across proto and DATA_CLASSIFICATION.md.
- **Recommendation**: Maintain classification documentation as schema evolves.
- **Evidence**: `protos/demo.proto`, `DATA_CLASSIFICATION.md`

### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: PII (email, address) processed in-memory only. DummyEmailService does not persist or transmit data externally. No cross-region transfer. When real email client is implemented, email content (containing PII) will be transmitted to the mail provider.
- **Implication**: No residency concerns in dummy mode.
- **Recommendation**: Assess mail provider data residency before implementing real email client.
- **Evidence**: `DATA_CLASSIFICATION.md`, `protos/demo.proto`, `src/emailservice/email_server.py`

### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: Email content generated from Jinja2 template (`confirmation.html`). Template rendering uses order data from the request. No input validation on email address format. DummyEmailService does not validate inputs.
- **Implication**: Invalid email addresses will not be caught before send attempt.
- **Recommendation**: Add email address format validation before sending.
- **Evidence**: `src/emailservice/email_server.py`, `src/emailservice/templates/confirmation.html`

### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: INFO
- **Finding**: Proto versioned `hipstershop.v1`. `buf.yaml` configured with STANDARD lint and FILE-level breaking change detection. `buf breaking` not yet wired into CI but tooling is in place.
- **Implication**: Schema versioning infrastructure is solid. CI integration is the remaining gap (tracked in ENG-Q2).
- **Recommendation**: Add `buf breaking` to CI pipeline.
- **Evidence**: `protos/demo.proto`, `protos/buf.yaml`

### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Clear semantic names: `email`, `order_id`, `shipping_tracking_id`, `shipping_cost`, `shipping_address`, `items`. Detailed proto comments with data classification annotations.
- **Implication**: Field names are self-documenting for agent tool generation.
- **Recommendation**: No action needed.
- **Evidence**: `protos/demo.proto`

### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal catalog. Proto with PII classification. DATA_CLASSIFICATION.md provides taxonomy. Proto declares "no persistent state" — clear system of record designation.
- **Implication**: Informal catalog exists via proto annotations and DATA_CLASSIFICATION.md.
- **Recommendation**: Register in organization API catalog.
- **Evidence**: `protos/demo.proto`, `DATA_CLASSIFICATION.md`

### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: INFO
- **Finding**: OpenTelemetry tracing configured with `GrpcInstrumentorServer` and `OTLPSpanExporter` to the OTel Collector. `ENABLE_TRACING=1` env var enables tracing. `COLLECTOR_SERVICE_ADDR` configured in Helm. Python JSON logger (`getJSONLogger`) provides structured logging. OTel instrumentation is functional (not a TODO stub).
- **Implication**: Distributed tracing is operational. Structured logging with JSON format. Positive finding.
- **Recommendation**: Add trace_id to log entries for log-to-trace correlation.
- **Evidence**: `src/emailservice/email_server.py`, `helm-chart/templates/emailservice.yaml`, `src/emailservice/requirements.in`

### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: INFO
- **Finding**: Prometheus alerting rules in `monitoring-alerts.yaml` cover all gRPC services including emailservice. Health probes (liveness + readiness) via gRPC. HPA configured (1–3 replicas at 70% CPU).
- **Implication**: Alerting infrastructure is comprehensive.
- **Recommendation**: Tune thresholds for email service patterns (email sending may have higher latency).
- **Evidence**: `kubernetes-manifests/monitoring-alerts.yaml`, `helm-chart/templates/emailservice.yaml`, `kubernetes-manifests/hpa.yaml`

### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics. Operational logging only. No email delivery success rate, bounce rate, or send latency metrics.
- **Implication**: Cannot measure email delivery effectiveness.
- **Recommendation**: Publish email send success/failure rates and delivery latency when real email client is implemented.
- **Evidence**: `src/emailservice/email_server.py`

### HITL-Q3: Sandbox/Staging Environment
- **Severity**: INFO
- **Finding**: Skaffold local dev. Cloud Build staging. CI per-PR namespaces. DummyEmailService provides safe testing (no actual emails sent).
- **Implication**: DummyEmailService is effectively a sandbox. No dedicated agent testing environment.
- **Recommendation**: Create persistent staging namespace for agent integration testing.
- **Evidence**: `cloudbuild.yaml`, `src/emailservice/Dockerfile`, `.github/workflows/ci-pr.yaml`

### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: INFO
- **Finding**: Comprehensive IaC via Helm. All security policies enabled (AuthorizationPolicies, NetworkPolicies, Sidecars). CODEOWNERS enforces review. No drift detection.
- **Implication**: IaC governance is strong. Drift detection is the remaining gap.
- **Recommendation**: Implement GitOps with Flux or ArgoCD for drift detection.
- **Evidence**: `helm-chart/templates/emailservice.yaml`, `helm-chart/values.yaml`, `.github/CODEOWNERS`

### ENG-Q3: Rollback Capability
- **Severity**: INFO
- **Finding**: K8s Deployment rollout with `kubectl rollout undo`. gRPC health probes for liveness and readiness. Monitoring alerts for error detection. Manual rollback process.
- **Implication**: Rollback is available but manual.
- **Recommendation**: Configure Flagger or Argo Rollouts for automated canary rollback.
- **Evidence**: `cloudbuild.yaml`, `helm-chart/templates/emailservice.yaml`

---

## Not Evaluated (Extended) — Questions Not Triggered

### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Trigger**: Service has operations >30s OR long-running workflows
- **Reason**: emailservice processes requests synchronously in sub-second time. No long-running workflows.

### API-Q7: Event Emission for State Changes
- **Severity**: Not Evaluated (extended)
- **Trigger**: Service has state changes (stateful-crud, orchestrator)
- **Reason**: event-processor archetype — consumes events, does not own state changes.

### STATE-Q2: Queryable Current State
- **Severity**: Not Evaluated (extended)
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator)
- **Reason**: event-processor — no persistent state.

### STATE-Q3: Concurrency Controls ⚡
- **Severity**: Not Evaluated (extended)
- **Trigger**: agent_scope is write-enabled AND service has persistent state
- **Reason**: agent_scope is read-only.

### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Trigger**: Service is P0 priority OR is on the critical path
- **Reason**: Service is P2 priority, not on critical path.

### HITL-Q1: Draft/Pending State ⚡
- **Severity**: Not Evaluated (extended)
- **Trigger**: agent_scope is write-enabled
- **Reason**: agent_scope is read-only.

### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: Not Evaluated (extended)
- **Trigger**: agent_scope is write-enabled
- **Reason**: agent_scope is read-only.

### DATA-Q3: Selective Query Support
- **Severity**: Not Evaluated (extended)
- **Trigger**: Service has list/query endpoints with potentially unbounded results
- **Reason**: Single fire-and-forget RPC, no list/query endpoints.

### DATA-Q4: System of Record Designations
- **Severity**: Not Evaluated (extended)
- **Trigger**: Service has persistent state (stateful-crud, data-gateway)
- **Reason**: event-processor — no persistent state. Proto explicitly states "no persistent state".

### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: Not Evaluated (extended)
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator)
- **Reason**: event-processor — no persistent state.

### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: Not Evaluated (extended)
- **Trigger**: Service has persistent data stores
- **Reason**: event-processor — no persistent data stores.

### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: Not Evaluated (extended)
- **Trigger**: Service has external dependencies (calls other services or external APIs)
- **Reason**: DummyEmailService has no external dependencies. Real EmailService would call external mail provider.

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: gRPC interface in `protos/demo.proto` with `EmailService` defining `SendOrderConfirmation` RPC. Versioned package `hipstershop.v1`. PII classification. System of record: notification sender (no persistent state). Positive finding.
- **Gap**: None — BLOCKER criteria satisfied.
- **Recommendation**: No remediation needed.
- **Evidence**: `protos/demo.proto`, `src/emailservice/email_server.py`

#### API-Q2: Machine-Readable API Specification
- **Severity**: INFO
- **Finding**: `protos/demo.proto` is machine-readable. Strongly typed with PII classification and versioned package. `buf.yaml` provides linting and breaking change detection.
- **Gap**: None.
- **Recommendation**: Consider enabling gRPC server reflection.
- **Evidence**: `protos/demo.proto`, `protos/buf.yaml`

#### API-Q3: Structured Error Responses
- **Severity**: RISK
- **Finding**: Two error paths both return `INTERNAL` with human-readable detail strings. No structured error body. No retryable boolean.
- **Gap**: Cannot distinguish transient from terminal errors.
- **Recommendation**: Use distinct gRPC status codes for template errors vs email send failures.
- **Evidence**: `src/emailservice/email_server.py`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: SendOrderConfirmation is not idempotent (duplicate calls send duplicate emails). Read-only scope mitigates.
- **Gap**: No deduplication. Acceptable for read-only scope.
- **Recommendation**: Add deduplication by order_id before expanding scope.
- **Evidence**: `src/emailservice/email_server.py`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: Returns `Empty` message. Fire-and-forget notification. Success/failure via gRPC status.
- **Gap**: None — appropriate for notification service.
- **Recommendation**: No action needed.
- **Evidence**: `protos/demo.proto`

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered.
- **Trigger**: Service has operations >30s OR long-running workflows
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered. Archetype: `event-processor` — consumes events, does not own state changes.
- **Trigger**: Service has state changes (stateful-crud, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: EnvoyFilter rate limiting now covers emailservice. No rate limit headers in gRPC metadata. Internal ClusterIP service.
- **Gap**: Agents cannot self-throttle.
- **Recommendation**: Add rate limit metadata to gRPC responses.
- **Evidence**: `istio-manifests/rate-limit.yaml`, `helm-chart/templates/emailservice.yaml`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: Istio AuthorizationPolicy with mTLS. Single caller: checkoutservice. Sidecars and network policies enabled. Tightest access control in portfolio.
- **Gap**: None — mesh-level mTLS with single-caller restriction.
- **Recommendation**: No action needed.
- **Evidence**: `helm-chart/values.yaml`, `helm-chart/templates/emailservice.yaml`, `src/emailservice/email_server.py`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: INFO
- **Archetype-Calibrated**: event-processor with single caller — downgraded to INFO
- **Finding**: AuthorizationPolicy restricts to checkoutservice on single RPC. Maximally scoped for this archetype.
- **Gap**: No agent-specific service accounts. Lower priority given single-caller restriction.
- **Recommendation**: Create agent-specific service accounts if direct access needed.
- **Evidence**: `helm-chart/templates/emailservice.yaml`, `helm-chart/values.yaml`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK
- **Finding**: Istio per-path rules defined. No application-layer authorization in Python gRPC server.
- **Gap**: No application-layer authorization.
- **Recommendation**: Implement gRPC server interceptor for authorization.
- **Evidence**: `src/emailservice/email_server.py`, `helm-chart/templates/emailservice.yaml`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Archetype-Calibrated**: event-processor — downgraded to INFO
- **Finding**: No identity propagation. Single caller (checkoutservice). Istio mTLS provides mesh-level identity.
- **Gap**: No application-level identity propagation. Lower priority for single-caller event-processor.
- **Recommendation**: Add caller identity to audit logs.
- **Evidence**: `src/emailservice/email_server.py`, `protos/demo.proto`

#### AUTH-Q5: Credential Management
- **Severity**: RISK
- **Finding**: DummyEmailService uses no credentials. Real EmailService references undefined variables. No Secrets Manager or Vault.
- **Gap**: No credential management framework for when real email client is implemented.
- **Recommendation**: Use K8s external secrets operator when implementing real email client.
- **Evidence**: `src/emailservice/email_server.py`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK
- **Finding**: PII (email address) logged in plaintext. No principal attribution. OTel tracing configured but not audit-grade. Logs are ephemeral stdout.
- **Gap**: PII logged without redaction. No immutable audit trail.
- **Recommendation**: Redact email addresses in logs. Add caller identity. Forward to immutable store.
- **Evidence**: `src/emailservice/email_server.py`, `src/emailservice/logger.py`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: INFO
- **Finding**: AuthorizationPolicy and NetworkPolicy provide suspension. Single-caller restriction makes suspension straightforward.
- **Gap**: No automated suspension.
- **Recommendation**: Implement automated suspension if agent direct access is added.
- **Evidence**: `helm-chart/templates/emailservice.yaml`, `helm-chart/values.yaml`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Email is fire-and-forget. DummyEmailService only logs. No compensation feasible for sent emails.
- **Gap**: Email is inherently non-compensable.
- **Recommendation**: Implement email queuing with delay for cancellation window.
- **Evidence**: `src/emailservice/email_server.py`

#### STATE-Q2: Queryable Current State
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered. Archetype: `event-processor` — no persistent state.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered. agent_scope is "read-only".
- **Trigger**: agent_scope is write-enabled AND service has persistent state
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered. DummyEmailService has no external dependencies.
- **Trigger**: Service has external dependencies (calls other services or external APIs)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: INFO
- **Finding**: EnvoyFilter rate limiting now includes emailservice. HPA (1–3 replicas). ThreadPoolExecutor(max_workers=10) provides concurrency cap.
- **Gap**: No per-recipient rate limiting.
- **Recommendation**: Add per-recipient rate limiting when real email client is implemented.
- **Evidence**: `istio-manifests/rate-limit.yaml`, `kubernetes-manifests/hpa.yaml`, `src/emailservice/email_server.py`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: DummyEmailService only logs. EnvoyFilter rate limiting provides mesh-level blast radius control. Minimal blast radius in dummy mode.
- **Gap**: None in dummy mode.
- **Recommendation**: Implement per-recipient rate limiting before enabling real email.
- **Evidence**: `src/emailservice/email_server.py`, `istio-manifests/rate-limit.yaml`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered. Service is P2 priority.
- **Trigger**: Service is P0 priority OR is on the critical path
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered. agent_scope is "read-only".
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered. agent_scope is "read-only".
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: INFO
- **Finding**: Skaffold local dev. Cloud Build staging. DummyEmailService provides safe testing. No persistent agent testing environment.
- **Gap**: No dedicated agent testing environment. DummyEmailService is effectively a sandbox.
- **Recommendation**: Create persistent staging namespace.
- **Evidence**: `cloudbuild.yaml`, `src/emailservice/Dockerfile`, `.github/workflows/ci-pr.yaml`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO
- **Finding**: PII classification documented: email addresses, shipping addresses. Proto and DATA_CLASSIFICATION.md both classify emailservice as PII.
- **Gap**: None — PII classification is comprehensive.
- **Recommendation**: Maintain classification documentation.
- **Evidence**: `protos/demo.proto`, `DATA_CLASSIFICATION.md`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: PII processed in-memory only in dummy mode. No external transmission. Real email client will transmit PII to mail provider.
- **Gap**: No residency analysis for mail provider.
- **Recommendation**: Assess mail provider data residency before implementing real client.
- **Evidence**: `DATA_CLASSIFICATION.md`, `protos/demo.proto`, `src/emailservice/email_server.py`

#### DATA-Q3: Selective Query Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered. Single fire-and-forget RPC, no list/query endpoints.
- **Trigger**: Service has list/query endpoints with potentially unbounded results
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q4: System of Record Designations
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered. Archetype: `event-processor` — no persistent state.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered. Archetype: `event-processor` — no persistent state.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK
- **Finding**: Email address logged in plaintext via `logger.info('...{}'.format(request.email))`. Direct PII leakage.
- **Gap**: PII logged without redaction.
- **Recommendation**: Mask email addresses: `u***@domain.com`.
- **Evidence**: `src/emailservice/email_server.py`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: Email content from Jinja2 template. No email address format validation. DummyEmailService does not validate inputs.
- **Gap**: No input validation.
- **Recommendation**: Add email address format validation.
- **Evidence**: `src/emailservice/email_server.py`, `src/emailservice/templates/confirmation.html`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: INFO
- **Finding**: Proto versioned `hipstershop.v1`. `buf.yaml` configured. `buf breaking` not in CI.
- **Gap**: `buf breaking` not in CI.
- **Recommendation**: Add `buf breaking` to CI.
- **Evidence**: `protos/demo.proto`, `protos/buf.yaml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Clear names: `email`, `order_id`, `shipping_tracking_id`, `shipping_cost`, `shipping_address`, `items`. Detailed proto comments.
- **Gap**: None.
- **Recommendation**: No action needed.
- **Evidence**: `protos/demo.proto`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal catalog. Proto with PII classification. DATA_CLASSIFICATION.md. Proto declares "no persistent state".
- **Gap**: No formal catalog.
- **Recommendation**: Register in organization API catalog.
- **Evidence**: `protos/demo.proto`, `DATA_CLASSIFICATION.md`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: INFO
- **Finding**: OTel tracing configured with GrpcInstrumentorServer and OTLPSpanExporter. ENABLE_TRACING and COLLECTOR_SERVICE_ADDR configured in Helm. Python JSON logger. Tracing is functional.
- **Gap**: No trace_id in log entries.
- **Recommendation**: Add trace_id to log entries for correlation.
- **Evidence**: `src/emailservice/email_server.py`, `helm-chart/templates/emailservice.yaml`, `src/emailservice/requirements.in`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: INFO
- **Finding**: Prometheus alerting rules cover all gRPC services. Health probes. HPA (1–3 replicas).
- **Gap**: None — alerting is comprehensive.
- **Recommendation**: Tune thresholds for email service latency patterns.
- **Evidence**: `kubernetes-manifests/monitoring-alerts.yaml`, `helm-chart/templates/emailservice.yaml`, `kubernetes-manifests/hpa.yaml`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics. No email delivery success/failure rates.
- **Gap**: No business outcome monitoring.
- **Recommendation**: Publish email send success/failure rates when real client is implemented.
- **Evidence**: `src/emailservice/email_server.py`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: INFO
- **Finding**: Comprehensive IaC via Helm. All security policies enabled. CODEOWNERS. No drift detection.
- **Gap**: Drift detection missing.
- **Recommendation**: Implement GitOps.
- **Evidence**: `helm-chart/templates/emailservice.yaml`, `helm-chart/values.yaml`, `.github/CODEOWNERS`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK
- **Finding**: CI exists. Proto versioned. `buf.yaml` configured. `buf breaking` not in CI. No emailservice tests.
- **Gap**: `buf breaking` not in CI. Zero test coverage.
- **Recommendation**: Add `buf breaking` to CI. Add unit tests.
- **Evidence**: `cloudbuild.yaml`, `.github/workflows/ci-pr.yaml`, `protos/buf.yaml`

#### ENG-Q3: Rollback Capability
- **Severity**: INFO
- **Finding**: K8s Deployment rollout. Manual rollback. Health probes. Monitoring alerts.
- **Gap**: No automated rollback.
- **Recommendation**: Configure Flagger or Argo Rollouts.
- **Evidence**: `cloudbuild.yaml`, `helm-chart/templates/emailservice.yaml`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK
- **Finding**: No emailservice tests. DummyEmailService has trivial logic. Real EmailService has untested template rendering.
- **Gap**: Zero test coverage.
- **Recommendation**: Add unit tests for template rendering and error handling.
- **Evidence**: `src/emailservice/email_server.py`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered. Archetype: `event-processor` — no persistent data stores.
- **Trigger**: Service has persistent data stores
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

---

## Evidence Index

### Infrastructure as Code
| File | Questions Referenced |
|------|---------------------|
| `helm-chart/templates/emailservice.yaml` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q7, API-Q8, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q3, STATE-Q5 |
| `helm-chart/values.yaml` | AUTH-Q1, AUTH-Q2, AUTH-Q4, AUTH-Q7, ENG-Q1 |
| `kubernetes-manifests/hpa.yaml` | STATE-Q5, OBS-Q2 |
| `kubernetes-manifests/monitoring-alerts.yaml` | OBS-Q2 |
| `istio-manifests/rate-limit.yaml` | STATE-Q5, STATE-Q6, API-Q8 |

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `src/emailservice/email_server.py` | API-Q1, API-Q3, API-Q4, AUTH-Q1, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q6, STATE-Q1, STATE-Q5, STATE-Q6, DATA-Q1, DATA-Q2, DATA-Q6, DATA-Q7, OBS-Q1, OBS-Q3, ENG-Q4, HITL-Q3 |
| `src/emailservice/logger.py` | AUTH-Q6 |
| `src/emailservice/templates/confirmation.html` | DATA-Q7 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `protos/demo.proto` | API-Q1, API-Q2, API-Q4, API-Q5, AUTH-Q4, DATA-Q1, DATA-Q2, DISC-Q1, DISC-Q2, DISC-Q3, ENG-Q2 |
| `protos/buf.yaml` | API-Q2, DISC-Q1, ENG-Q2 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `cloudbuild.yaml` | HITL-Q3, ENG-Q1, ENG-Q2, ENG-Q3 |
| `.github/workflows/ci-pr.yaml` | HITL-Q3, ENG-Q2, ENG-Q4 |
| `.github/CODEOWNERS` | ENG-Q1 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `src/emailservice/Dockerfile` | HITL-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `src/emailservice/requirements.in` | OBS-Q1 |
| `src/emailservice/requirements.txt` | OBS-Q1 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `DATA_CLASSIFICATION.md` | DATA-Q1, DATA-Q2, DISC-Q3 |
