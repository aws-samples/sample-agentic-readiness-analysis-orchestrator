# Agentic Readiness Analysis Report

**Target**: services/microservices-demo/src/currencyservice
**Date**: 2026-04-16
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**Repository Type**: application
**Service Archetype**: stateless-utility (user-provided)
**Agent Scope**: read-only
**Priority**: P1
**Tags**: cpp, grpc, utility
**Context**: C++ gRPC service converting between currencies. (Note: actual implementation is Node.js/gRPC, not C++.)

---

## Readiness Profile: Pilot-Ready

**BLOCKERs**: 0 | **RISKs**: 12 | **INFOs**: 19

Supervised pilot with: (1) human approval gates on irreversible actions, (2) agent limited to low-blast-radius operations, (3) compensating controls for each open RISK, (4) remediation timeline before expanding scope.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 0 |
| RISK | 12 |
| INFO | 19 |
| N/A | 0 |
| Not Evaluated (extended) | 12 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 7
**Extended Questions Not Triggered**: 12
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: stateless-utility (user-provided)

---

## BLOCKERs — Must Resolve Before Agent Deployment

No BLOCKERs identified.

---

## RISKs — Proceed with Compensating Controls

### API-Q3: Structured Error Responses
- **Severity**: RISK
- **Finding**: The `convert` function in `server.js` calls `callback(err.message)` on error — a plain string without structured error codes or retryable indicators. gRPC status codes are not set explicitly. The `getSupportedCurrencies` function has no error handling at all.
- **Gap**: Agents cannot distinguish retriable from terminal errors. No structured error metadata in gRPC responses.
- **Compensating Controls**:
  - Wrap agent tool calls with client-side error classification based on gRPC status codes
  - Implement retry with exponential backoff for UNKNOWN/UNAVAILABLE status codes
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Refactor error handling to use explicit gRPC status codes (e.g., `grpc.status.INVALID_ARGUMENT` for bad currency codes, `grpc.status.NOT_FOUND` for unsupported currencies). Return structured error metadata.
- **Evidence**: `server.js` (convert function catch block)

### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicy is now enabled (`authorizationPolicies.create: true` in `helm-chart/values.yaml`), restricting callers to `frontend` and `checkoutservice` service accounts. However, both allowed callers have unrestricted access to both RPCs (`GetSupportedCurrencies` and `Convert`). No agent-specific service accounts are defined. No IAM policies or application-level RBAC.
- **Gap**: No per-RPC scoping for different callers. No agent-specific service accounts with tailored permissions.
- **Compensating Controls**:
  - Istio AuthorizationPolicy restricts callers to known service accounts (defense in depth)
  - Define agent-specific K8s ServiceAccounts and add them to the AuthorizationPolicy with per-path rules
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create agent-specific service accounts with per-RPC AuthorizationPolicy rules (e.g., agent can call `Convert` but not `GetSupportedCurrencies`, or vice versa).
- **Evidence**: `helm-chart/templates/currencyservice.yaml` (AuthorizationPolicy section), `helm-chart/values.yaml` (`authorizationPolicies.create: true`)

### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicy is enabled and defines per-path rules for the two RPCs. However, the application code itself has no action-level authorization — the gRPC server accepts all calls that reach it. Authorization is entirely at the mesh layer.
- **Gap**: No application-layer action-level authorization. If the mesh is bypassed, all RPCs are accessible to any caller.
- **Compensating Controls**:
  - Istio sidecar injection (`sidecars.create: true`) ensures mesh-level enforcement
  - Network policies (`networkPolicies.create: true`) provide additional defense in depth
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement a gRPC server interceptor for action-level authorization as defense in depth beyond the mesh layer.
- **Evidence**: `server.js`, `helm-chart/templates/currencyservice.yaml`, `helm-chart/values.yaml`

### AUTH-Q5: Credential Management
- **Severity**: RISK
- **Finding**: No secrets or credentials are used by the service itself — static JSON data, no database connections. Google Cloud Profiler uses Workload Identity (no hardcoded credentials). No secrets in environment variables or configuration files. No Secrets Manager or Vault integration.
- **Gap**: No formal credential management system. While the service currently has no credentials to manage, there is no framework for credential lifecycle management if credentials are introduced.
- **Compensating Controls**:
  - Credential-free architecture eliminates current secret rotation concerns
  - Workload Identity for GCP libraries avoids hardcoded credentials
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Maintain credential-free architecture. If credentials are introduced, use K8s Secrets with external secrets operator or AWS Secrets Manager.
- **Evidence**: `server.js`, `data/currency_conversion.json`, `package.json`

### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: No audit logging exists. Pino logs operational messages only (startup, conversion success/failure). No principal attribution in any log output. Logs are ephemeral container stdout with no immutable storage configuration. No CloudTrail or equivalent. OpenTelemetry tracing is now enabled (`tracing: true` in values.yaml), which provides request-level trace context but not audit-grade principal attribution.
- **Gap**: No immutable audit trail. Cannot determine who called the service or attribute actions to specific agent identities.
- **Compensating Controls**:
  - Configure K8s log forwarding to immutable store (e.g., CloudWatch Logs with retention policy, S3 with Object Lock)
  - OpenTelemetry traces provide request correlation as a partial audit signal
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add structured audit logging with caller identity (extracted from Istio mTLS peer identity). Forward to immutable store. Depends on AUTH-Q1 for principal attribution.
- **Evidence**: `server.js` (Pino logger with no audit fields), `helm-chart/values.yaml` (`tracing: true`)

### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicy is now enabled, providing a mechanism to deny specific service accounts by updating the policy. However, there is no automated suspension mechanism — policy changes require Helm value updates or manual kubectl edits. No API key revocation, no service account disable endpoint.
- **Gap**: No automated or rapid suspension mechanism. Isolating a misbehaving agent requires manual AuthorizationPolicy or NetworkPolicy changes.
- **Compensating Controls**:
  - Istio AuthorizationPolicy can be updated to deny specific service accounts (manual process)
  - K8s NetworkPolicy (now enabled) can block specific pods as emergency measure
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement automated suspension via AuthorizationPolicy updates triggered by anomaly detection. Consider an operator or webhook that can instantly deny a service account.
- **Evidence**: `helm-chart/templates/currencyservice.yaml`, `helm-chart/values.yaml` (`authorizationPolicies.create: true`, `networkPolicies.create: true`)

### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: Service is stateless — reads static JSON and performs arithmetic. No multi-step write operations. No state mutations to compensate.
- **Gap**: No compensation mechanisms exist, though no state mutations require compensation. The RISK rating reflects the absence of the mechanism, not an active threat.
- **Compensating Controls**:
  - Stateless nature means compensation is not operationally needed
  - Document stateless architecture for agent integration teams
- **Remediation Timeline**: No immediate action; revisit if write operations added
- **Recommendation**: Maintain stateless architecture documentation. Implement compensation if write operations are added.
- **Evidence**: `server.js`, `data/currency_conversion.json`

### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK
- **Finding**: No application-level rate limiting. K8s resource limits cap CPU/memory but not request rates. ClusterIP service with no API Gateway. Istio sidecar is enabled but no Envoy rate limiting configuration is present.
- **Gap**: Runaway agent loop could overwhelm the service. No per-caller rate limiting.
- **Compensating Controls**:
  - Implement rate limiting at Istio/Envoy level using EnvoyFilter or Istio rate limiting service
  - Configure agent-side request rate caps in the agent orchestration layer
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add gRPC interceptor for rate limiting or configure Istio/Envoy rate limiting per source service account.
- **Evidence**: `server.js`, `kubernetes-manifests/currencyservice.yaml`, `helm-chart/values.yaml` (`sidecars.create: true`)

### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK
- **Finding**: Skaffold provides local development. CI deploys per-PR to ephemeral namespaces on `prs-gke-cluster`. No persistent agent testing environment with production-equivalent data shape.
- **Gap**: No dedicated agent testing environment.
- **Compensating Controls**:
  - Use Skaffold for local instance with Docker build for isolated testing
  - Leverage per-PR ephemeral namespaces for integration testing
- **Remediation Timeline**: 30 days
- **Recommendation**: Create persistent staging namespace for agent integration testing with production-equivalent configuration.
- **Evidence**: `skaffold.yaml`, `Dockerfile`, `.github/workflows/ci-pr.yaml`

### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: Static, publicly available ECB exchange rates. No regulated data. No explicit residency requirements or documentation. No data residency configuration in IaC or application code.
- **Gap**: No formal data residency documentation. Public ECB rates have no residency restrictions, but no formal analysis exists.
- **Compensating Controls**:
  - Document that current data (ECB public rates) has no residency restrictions
  - Implement residency controls proactively if user-specific or regulated data is added
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document data residency posture formally. Implement residency-aware controls if the service scope expands to include regulated or user-specific data.
- **Evidence**: `data/currency_conversion.json`, `server.js`

### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK
- **Finding**: CI exists (Cloud Build + Skaffold + GitHub Actions). Smoke test via loadgenerator. Proto now uses versioned package (`hipstershop.v1`) and `buf.yaml` exists for proto linting. However, no `buf breaking` is configured in CI for breaking change detection. No currencyservice-specific contract tests.
- **Gap**: No automated breaking change detection in CI pipeline. No service-specific API contract tests.
- **Compensating Controls**:
  - Protobuf wire compatibility provides implicit backward compatibility for additive changes
  - `buf.yaml` enables linting but breaking change detection requires `buf breaking` in CI
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `buf breaking` to CI pipeline. Add CurrencyService-specific contract tests validating input/output schemas.
- **Evidence**: `cloudbuild.yaml`, `skaffold.yaml`, `.github/workflows/ci-pr.yaml`, `buf.yaml`, `proto/demo.proto`

### ENG-Q3: Rollback Capability
- **Severity**: RISK
- **Finding**: K8s Deployment with rollout history. Skaffold deployment. No automated rollback triggers. Manual rollback via `kubectl rollout undo` only. No canary deployment, no Flagger, no Argo Rollouts.
- **Gap**: No automated rollback on service degradation. Manual rollback only.
- **Compensating Controls**:
  - K8s rollout history enables manual rollback within minutes
  - Liveness/readiness probes prevent traffic to unhealthy pods
  - Monitoring alerts (now configured) can trigger manual rollback faster
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure automated rollback triggers using Flagger or Argo Rollouts with canary analysis.
- **Evidence**: `skaffold.yaml`, `kubernetes-manifests/currencyservice.yaml`

---

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: Well-documented gRPC interface in `proto/demo.proto` with `CurrencyService` defining `GetSupportedCurrencies` and `Convert` RPCs. Proto now uses versioned package `hipstershop.v1`. Implemented in `server.js`. Positive finding.
- **Implication**: gRPC interface can be used directly as agent tool binding. Proto enables auto-generated client code.
- **Recommendation**: No remediation needed.
- **Evidence**: `proto/demo.proto`, `server.js`

### API-Q2: Machine-Readable API Specification
- **Severity**: INFO
- **Finding**: `proto/demo.proto` is a machine-readable spec. Protobuf is strongly typed with field numbers, data classification comments, and timestamps. `buf.yaml` provides proto linting. Spec is current with implementation. Positive finding.
- **Implication**: Agent tool definitions can be auto-generated from proto. `buf` tooling enables schema governance.
- **Recommendation**: Consider enabling gRPC server reflection for runtime schema discovery.
- **Evidence**: `proto/demo.proto`, `buf.yaml`, `server.js`

### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Both RPCs are read-only, stateless, and inherently idempotent with no write side effects. Same input always produces same output (deterministic arithmetic on static data).
- **Implication**: No idempotency concerns for read-only scope.
- **Recommendation**: No action needed.
- **Evidence**: `server.js`, `data/currency_conversion.json`

### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: Istio AuthorizationPolicy is now enabled (`authorizationPolicies.create: true` in `helm-chart/values.yaml`), providing service-mesh-level identity verification using mTLS between pods. Callers are restricted to `frontend` and `checkoutservice` service accounts. Istio sidecars are enabled (`sidecars.create: true`), ensuring mTLS is enforced. The gRPC server in `server.js` still uses `grpc.ServerCredentials.createInsecure()` at the application layer, but the Istio sidecar terminates mTLS before traffic reaches the application — this is the standard Istio pattern.
- **Implication**: Machine identity is authenticated at the mesh layer via mTLS with per-service principal attribution. This satisfies the core requirement for agent identity verification. Application-layer auth is defense-in-depth, not a prerequisite.
- **Recommendation**: For defense in depth, consider implementing a gRPC interceptor that extracts the Istio peer identity from request headers for application-level logging.
- **Evidence**: `helm-chart/values.yaml` (`authorizationPolicies.create: true`, `sidecars.create: true`), `helm-chart/templates/currencyservice.yaml` (AuthorizationPolicy section), `server.js` (`grpc.ServerCredentials.createInsecure()`)

### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Archetype-Calibrated**: stateless-utility — downgraded to INFO
- **Finding**: No JWT parsing, no token exchange, no user context headers. No identity context in gRPC calls. However, Istio mTLS provides implicit caller identity at the mesh layer.
- **Implication**: For a stateless-utility returning public reference data, identity propagation has minimal security impact — responses are not user-specific and data is public ECB rates. Istio provides caller identity at the mesh layer.
- **Recommendation**: No immediate action. Implement identity propagation if the service evolves to handle user-specific data.
- **Evidence**: `server.js`, `helm-chart/values.yaml`

### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No writes, deletes, or modifications. Minimal blast radius. Read-only operations on public data.
- **Implication**: Transaction limits not applicable for read-only operations on public data.
- **Recommendation**: Implement if write operations are added.
- **Evidence**: `server.js`

### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO
- **Finding**: Handles public ECB exchange rates and monetary amounts only. No PII, PHI, or financial account data. Proto now includes data classification comments. Public data with no sensitivity classification required.
- **Implication**: No data classification controls needed. No PII exposure risk. Positive finding.
- **Recommendation**: Implement classification if user-specific financial data is added.
- **Evidence**: `data/currency_conversion.json`, `proto/demo.proto` (data classification comments)

### DATA-Q6: PII Redaction in Logs
- **Severity**: INFO
- **Finding**: Logs contain operational messages only (startup, conversion success/failure). No request details logged. No PII in data model. No PII leakage risk.
- **Implication**: No PII redaction needed. Positive finding.
- **Recommendation**: No action needed.
- **Evidence**: `server.js`

### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: INFO
- **Finding**: Proto now uses versioned package `hipstershop.v1`. `buf.yaml` exists for proto linting. Proto defines typed schemas with data classification comments and timestamps. Breaking change detection (`buf breaking`) not yet in CI but tooling is in place.
- **Implication**: Schema versioning is established. Proto versioning enables safe evolution. `buf` tooling provides a path to automated breaking change detection.
- **Recommendation**: Add `buf breaking` to CI pipeline to complete the contract testing story (tracked under ENG-Q2).
- **Evidence**: `proto/demo.proto` (`hipstershop.v1`), `buf.yaml`

### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: INFO
- **Finding**: OpenTelemetry SDK with gRPC instrumentation is now enabled by default (`tracing: true` in `helm-chart/values.yaml`). OpenTelemetry Collector is deployed (`opentelemetryCollector.create: true`). Pino provides structured JSON logging. Metrics are enabled (`metrics: true`). No correlation_id/request_id in application logs, but trace context is propagated via OpenTelemetry.
- **Implication**: Distributed tracing is operational. Trace context enables end-to-end request correlation across services. Structured JSON logging supports log aggregation. The remaining gap (no request_id in Pino logs) is minor — OpenTelemetry trace IDs serve the same purpose.
- **Recommendation**: Add trace_id to Pino log entries for log-to-trace correlation. This is a minor enhancement, not a gap.
- **Evidence**: `server.js` (OpenTelemetry setup), `helm-chart/values.yaml` (`tracing: true`, `opentelemetryCollector.create: true`, `metrics: true`), `package.json`

### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: INFO
- **Finding**: Monitoring alerts have been added for error rates and latency. Metrics collection is enabled (`metrics: true`). K8s health probes provide pod availability. HPA is configured for auto-scaling based on metrics.
- **Implication**: Alerting infrastructure is in place. Service degradation will be detected before agents cascade failures.
- **Recommendation**: Tune alert thresholds based on agent traffic patterns during pilot.
- **Evidence**: `kubernetes-manifests/currencyservice.yaml`, `helm-chart/values.yaml` (`metrics: true`)

### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: INFO
- **Finding**: IaC exists across multiple layers: K8s manifests, Kustomize, Helm, Terraform. CODEOWNERS enforces peer review. GitHub Actions CI on PRs. AuthorizationPolicies, NetworkPolicies, and Sidecars are all defined in IaC and enabled. No drift detection configured.
- **Implication**: Infrastructure governance is strong — IaC coverage is comprehensive and peer review is enforced. The drift detection gap is minor for a K8s-native deployment where Helm/Kustomize reconciliation provides implicit drift correction on deploy.
- **Recommendation**: Implement drift detection for completeness. Consider ArgoCD or Flux for GitOps-based continuous reconciliation.
- **Evidence**: `kubernetes-manifests/currencyservice.yaml`, `terraform/main.tf`, `.github/CODEOWNERS`, `.github/workflows/ci-pr.yaml`, `helm-chart/values.yaml`

### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: gRPC Protocol Buffers — strongly-typed binary format with explicit types, field numbers, and data classification comments.
- **Implication**: Protobuf is more structured than JSON. Excellent for agent integration with auto-generated client code.
- **Recommendation**: No action needed.
- **Evidence**: `proto/demo.proto`

### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit headers. Internal ClusterIP service. K8s resource limits provide implicit capping.
- **Implication**: Agents cannot self-throttle based on server-side rate limit signals.
- **Recommendation**: Add gRPC trailing metadata with rate limit status when rate limiting is implemented.
- **Evidence**: `server.js`, `kubernetes-manifests/currencyservice.yaml`

### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No quality metrics. 34 static currency entries. No validation of rate ranges. Quality fixed at build time.
- **Implication**: Quality is static and deterministic. No runtime degradation risk.
- **Recommendation**: Add validation that rates are positive and within expected ranges.
- **Evidence**: `data/currency_conversion.json`

### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Clear semantic names: `currency_code`, `units`, `nanos`, `to_code`. Detailed comments. No abbreviations.
- **Implication**: LLMs can interpret fields directly. No translation needed.
- **Recommendation**: No action needed.
- **Evidence**: `proto/demo.proto`

### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal catalog. Proto file serves as informal documentation with data classification comments. Self-describing JSON data.
- **Implication**: Sufficient for single-purpose utility service.
- **Recommendation**: Register in organization API catalog if part of larger data mesh.
- **Evidence**: `proto/demo.proto`, `data/currency_conversion.json`

### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics. Operational logging and OpenTelemetry metrics provide infrastructure-level visibility.
- **Implication**: No business outcome monitoring. Operational metrics may suffice initially for a utility service.
- **Recommendation**: Publish metrics for conversion volume by currency pair if business analytics are needed.
- **Evidence**: `server.js`

### ENG-Q4: API Test Coverage
- **Severity**: INFO
- **Finding**: Test script is stub. Zero test files. CI skips currencyservice. Simple service logic reduces untested-code risk.
- **Implication**: For a stateless-utility with simple arithmetic logic, the risk of zero test coverage is lower than for stateful services. Still recommended for regression safety.
- **Recommendation**: Add unit tests for `convert` function and `_carry` helper. Add gRPC integration tests.
- **Evidence**: `package.json`, `server.js`, `.github/workflows/ci-pr.yaml`

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: Well-documented gRPC interface in `proto/demo.proto` with `CurrencyService` defining `GetSupportedCurrencies` and `Convert` RPCs. Proto uses versioned package `hipstershop.v1`. Implemented in `server.js`. Positive finding.
- **Gap**: None — BLOCKER criteria satisfied.
- **Recommendation**: No remediation needed.
- **Evidence**: `proto/demo.proto`, `server.js`

#### API-Q2: Machine-Readable API Specification
- **Severity**: INFO
- **Finding**: `proto/demo.proto` is a machine-readable spec. Protobuf is strongly typed with field numbers, data classification comments, and timestamps. `buf.yaml` provides proto linting. Current with implementation. Positive finding.
- **Gap**: None.
- **Recommendation**: Consider enabling gRPC server reflection for runtime schema discovery.
- **Evidence**: `proto/demo.proto`, `buf.yaml`, `server.js`

#### API-Q3: Structured Error Responses
- **Severity**: RISK
- **Finding**: `convert` calls `callback(err.message)` — plain string. No gRPC status codes set explicitly. No structured error metadata.
- **Gap**: Agents cannot distinguish retriable from terminal errors.
- **Recommendation**: Use explicit gRPC status codes and structured error metadata.
- **Evidence**: `server.js` (convert function catch block)

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Both RPCs are read-only, stateless, inherently idempotent. Same input always produces same output.
- **Gap**: N/A — no write operations.
- **Recommendation**: No action needed.
- **Evidence**: `server.js`, `data/currency_conversion.json`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: gRPC Protocol Buffers — strongly-typed binary format with explicit types, field numbers, and documentation. Data classification comments in proto.
- **Gap**: None.
- **Recommendation**: No action needed.
- **Evidence**: `proto/demo.proto`

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has operations >30s OR long-running workflows
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has state changes (stateful-crud, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit headers. Internal ClusterIP service. K8s resource limits provide implicit capping. No `X-RateLimit-Remaining` or `Retry-After` headers in gRPC responses.
- **Gap**: Agents cannot self-throttle based on server-side rate limit signals.
- **Recommendation**: Add gRPC trailing metadata with rate limit status when rate limiting is implemented (see STATE-Q5).
- **Evidence**: `server.js`, `kubernetes-manifests/currencyservice.yaml`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: Istio AuthorizationPolicy is enabled (`authorizationPolicies.create: true`), providing mTLS-based identity verification. Callers restricted to `frontend` and `checkoutservice` service accounts. Istio sidecars enabled (`sidecars.create: true`). The gRPC server uses `grpc.ServerCredentials.createInsecure()` at the application layer, but Istio sidecar terminates mTLS before traffic reaches the application — standard Istio pattern.
- **Gap**: None — mesh-level mTLS with per-service AuthorizationPolicy satisfies machine identity authentication. Application-layer auth is defense-in-depth.
- **Recommendation**: For defense in depth, consider extracting Istio peer identity from request headers for application-level audit logging.
- **Evidence**: `helm-chart/values.yaml` (`authorizationPolicies.create: true`, `sidecars.create: true`), `helm-chart/templates/currencyservice.yaml`, `server.js`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicy restricts callers to `frontend` and `checkoutservice`. Both have access to both RPCs. No agent-specific service accounts.
- **Gap**: No per-RPC scoping for different callers. No agent-specific permissions.
- **Recommendation**: Create agent-specific service accounts with per-RPC AuthorizationPolicy rules.
- **Evidence**: `helm-chart/templates/currencyservice.yaml`, `helm-chart/values.yaml`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicy defines per-path rules. No application-layer action-level authorization.
- **Gap**: No application-layer authorization. Mesh bypass exposes all RPCs.
- **Recommendation**: Implement gRPC server interceptor for action-level authorization as defense in depth.
- **Evidence**: `server.js`, `helm-chart/templates/currencyservice.yaml`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Archetype-Calibrated**: stateless-utility — downgraded to INFO
- **Finding**: No JWT parsing, token exchange, or user context headers. Istio mTLS provides implicit caller identity at mesh layer.
- **Gap**: No application-level identity propagation. Minimal impact for stateless-utility returning public data.
- **Recommendation**: No immediate action. Implement if service evolves to handle user-specific data.
- **Evidence**: `server.js`, `helm-chart/values.yaml`

#### AUTH-Q5: Credential Management
- **Severity**: RISK
- **Finding**: No secrets or credentials used. Static JSON data. Workload Identity for GCP libraries. No Secrets Manager or Vault integration.
- **Gap**: No credential management framework if credentials are introduced.
- **Recommendation**: Maintain credential-free architecture. Adopt K8s external secrets operator if credentials are needed.
- **Evidence**: `server.js`, `data/currency_conversion.json`, `package.json`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: No audit logging. Pino operational messages only. No principal attribution. OpenTelemetry tracing enabled but provides request correlation, not audit-grade attribution. Logs are ephemeral container stdout.
- **Gap**: No immutable audit trail. Cannot attribute actions to specific agent identities.
- **Recommendation**: Add structured audit logging with caller identity. Forward to immutable store.
- **Evidence**: `server.js`, `helm-chart/values.yaml` (`tracing: true`)

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicy provides a mechanism to deny specific service accounts. NetworkPolicies enabled. No automated suspension — requires manual policy changes.
- **Gap**: No automated or rapid suspension mechanism.
- **Recommendation**: Implement automated suspension via AuthorizationPolicy updates triggered by anomaly detection.
- **Evidence**: `helm-chart/templates/currencyservice.yaml`, `helm-chart/values.yaml`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: Stateless service. No write operations, no transactions, no state mutations to compensate.
- **Gap**: No compensation mechanisms — but no state mutations exist.
- **Recommendation**: Maintain stateless architecture. Implement compensation if write operations added.
- **Evidence**: `server.js`, `data/currency_conversion.json`

#### STATE-Q2: Queryable Current State
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled AND service has persistent state
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has external dependencies (calls other services or external APIs)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK
- **Finding**: No application-level rate limiting. K8s resource limits only. No API Gateway. Istio sidecar enabled but no Envoy rate limiting configured.
- **Gap**: Runaway agent loop risk. No per-caller rate limiting.
- **Recommendation**: Configure Istio/Envoy rate limiting or add gRPC rate limiting interceptor.
- **Evidence**: `server.js`, `kubernetes-manifests/currencyservice.yaml`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No writes, deletes, or modifications. Minimal blast radius. Read-only operations on public data.
- **Gap**: None for read-only scope.
- **Recommendation**: Implement if write operations added.
- **Evidence**: `server.js`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK
- **Finding**: Skaffold local dev. CI per-PR ephemeral namespaces. No persistent agent testing environment.
- **Gap**: No dedicated agent testing environment.
- **Recommendation**: Create persistent staging namespace for agent integration testing.
- **Evidence**: `skaffold.yaml`, `Dockerfile`, `.github/workflows/ci-pr.yaml`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO
- **Finding**: Public ECB exchange rates and monetary amounts only. No PII/PHI/financial account data. Proto includes data classification comments. Public data.
- **Gap**: None — public data with no sensitivity classification required.
- **Recommendation**: Implement classification if user-specific financial data added.
- **Evidence**: `data/currency_conversion.json`, `proto/demo.proto`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: Static, publicly available ECB exchange rates. No regulated data. No explicit residency requirements or documentation.
- **Gap**: No formal data residency documentation. Public ECB rates have no residency restrictions, but no formal analysis exists.
- **Recommendation**: Document data residency posture formally. Implement controls if regulated data is added.
- **Evidence**: `data/currency_conversion.json`, `server.js`

#### DATA-Q3: Selective Query Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has list/query endpoints with potentially unbounded results
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q4: System of Record Designations
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q6: PII Redaction in Logs
- **Severity**: INFO
- **Finding**: Logs contain operational messages only. No request details logged. No PII in data model. No PII leakage risk.
- **Gap**: None.
- **Recommendation**: No action needed.
- **Evidence**: `server.js`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No quality metrics. 34 static currency entries. No validation of rate ranges. Quality fixed at build time with no runtime degradation.
- **Gap**: No quality monitoring, but static data has fixed quality characteristics.
- **Recommendation**: Add validation that rates are positive and within expected ranges.
- **Evidence**: `data/currency_conversion.json`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: INFO
- **Finding**: Proto uses versioned package `hipstershop.v1`. `buf.yaml` exists for proto linting. Typed schemas with data classification comments. Breaking change detection not yet in CI.
- **Gap**: `buf breaking` not in CI (tracked under ENG-Q2).
- **Recommendation**: Add `buf breaking` to CI pipeline.
- **Evidence**: `proto/demo.proto`, `buf.yaml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Clear semantic names: `currency_code`, `units`, `nanos`, `to_code`. Detailed comments. No abbreviations. Data classification comments in proto.
- **Gap**: None.
- **Recommendation**: No action needed.
- **Evidence**: `proto/demo.proto`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal catalog. Proto file serves as informal documentation with data classification comments. Self-describing JSON data with ECB source attribution.
- **Gap**: No formal catalog. Sufficient for single-purpose utility service.
- **Recommendation**: Register in organization API catalog if part of larger data mesh.
- **Evidence**: `proto/demo.proto`, `data/currency_conversion.json`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: INFO
- **Finding**: OpenTelemetry SDK with gRPC instrumentation enabled (`tracing: true`). OpenTelemetry Collector deployed (`opentelemetryCollector.create: true`). Metrics enabled (`metrics: true`). Pino structured JSON logging. Trace context propagated via OpenTelemetry.
- **Gap**: No trace_id in Pino log entries (minor — OpenTelemetry trace IDs serve the same purpose).
- **Recommendation**: Add trace_id to Pino log entries for log-to-trace correlation.
- **Evidence**: `server.js`, `helm-chart/values.yaml`, `package.json`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: INFO
- **Finding**: Monitoring alerts configured for error rates and latency. Metrics collection enabled. K8s health probes provide pod availability. HPA configured for auto-scaling.
- **Gap**: None — alerting infrastructure is in place.
- **Recommendation**: Tune alert thresholds based on agent traffic patterns during pilot.
- **Evidence**: `kubernetes-manifests/currencyservice.yaml`, `helm-chart/values.yaml`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics. Operational logging and OpenTelemetry metrics provide infrastructure-level visibility. No conversion volume metrics by currency pair.
- **Gap**: No business outcome monitoring. Operational metrics may suffice initially for a utility service.
- **Recommendation**: Publish metrics for conversion volume by currency pair if business analytics are needed.
- **Evidence**: `server.js`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: INFO
- **Finding**: Comprehensive IaC: K8s manifests, Kustomize, Helm, Terraform. CODEOWNERS enforces peer review. GitHub Actions CI on PRs. AuthorizationPolicies, NetworkPolicies, Sidecars all defined in IaC and enabled. No drift detection.
- **Gap**: Drift detection missing (minor for K8s-native deployment with Helm reconciliation).
- **Recommendation**: Implement drift detection or GitOps (ArgoCD/Flux) for continuous reconciliation.
- **Evidence**: `kubernetes-manifests/currencyservice.yaml`, `terraform/main.tf`, `.github/CODEOWNERS`, `.github/workflows/ci-pr.yaml`, `helm-chart/values.yaml`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK
- **Finding**: CI exists. Proto versioned (`hipstershop.v1`). `buf.yaml` for linting. No `buf breaking` in CI. No service-specific contract tests.
- **Gap**: No automated breaking change detection in CI.
- **Recommendation**: Add `buf breaking` to CI. Add CurrencyService contract tests.
- **Evidence**: `cloudbuild.yaml`, `.github/workflows/ci-pr.yaml`, `buf.yaml`, `proto/demo.proto`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK
- **Finding**: K8s rollout history. Skaffold deployment. Manual rollback only. No canary or automated rollback.
- **Gap**: No automated rollback on service degradation.
- **Recommendation**: Configure automated rollback triggers (Flagger, Argo Rollouts).
- **Evidence**: `skaffold.yaml`, `kubernetes-manifests/currencyservice.yaml`

#### ENG-Q4: API Test Coverage
- **Severity**: INFO
- **Finding**: Test script is stub: `echo "Error: no test specified" && exit 1`. Zero test files. CI skips currencyservice. Only coverage is loadgenerator smoke test. Simple service logic (arithmetic on static data) reduces untested-code risk.
- **Gap**: Zero test coverage. For a stateless-utility, the risk is lower than for stateful services, but tests are still recommended.
- **Recommendation**: Add unit tests for `convert` function and `_carry` helper. Add gRPC integration tests. Include in CI.
- **Evidence**: `package.json`, `server.js`, `.github/workflows/ci-pr.yaml`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent data stores
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

---

## Evidence Index

### Infrastructure as Code
| File | Questions Referenced |
|------|---------------------|
| `terraform/main.tf` | AUTH-Q6, ENG-Q1 |
| `kubernetes-manifests/currencyservice.yaml` | AUTH-Q1, AUTH-Q2, STATE-Q5, OBS-Q2, API-Q8, ENG-Q1, ENG-Q3 |
| `kustomize/base/currencyservice.yaml` | ENG-Q1 |
| `helm-chart/templates/currencyservice.yaml` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q7, ENG-Q1 |
| `helm-chart/values.yaml` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q6, AUTH-Q7, OBS-Q1, OBS-Q2, ENG-Q1, STATE-Q5 |

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `src/currencyservice/server.js` | API-Q1, API-Q2, API-Q3, API-Q4, API-Q8, AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q5, STATE-Q6, DATA-Q1, DATA-Q2, DATA-Q6, OBS-Q1, OBS-Q3, ENG-Q4 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `src/currencyservice/proto/demo.proto` | API-Q1, API-Q2, API-Q4, API-Q5, DATA-Q1, DISC-Q1, DISC-Q2, ENG-Q2 |
| `buf.yaml` | API-Q2, DISC-Q1, ENG-Q2 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `cloudbuild.yaml` | ENG-Q2 |
| `skaffold.yaml` | HITL-Q3, ENG-Q1, ENG-Q2, ENG-Q3 |
| `.github/workflows/ci-pr.yaml` | HITL-Q3, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4 |
| `.github/CODEOWNERS` | ENG-Q1 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `src/currencyservice/Dockerfile` | HITL-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `src/currencyservice/package.json` | AUTH-Q5, OBS-Q1, ENG-Q4 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `src/currencyservice/data/currency_conversion.json` | API-Q4, STATE-Q1, DATA-Q1, DATA-Q2, DATA-Q7, DISC-Q3 |
