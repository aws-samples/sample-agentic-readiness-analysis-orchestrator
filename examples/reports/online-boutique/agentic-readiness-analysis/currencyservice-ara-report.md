# Agentic Readiness Analysis Report

**Target**: services/microservices-demo/src/currencyservice
**Date**: 2025-07-14
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**Repository Type**: application
**Service Archetype**: stateless-utility (user-provided)
**Agent Scope**: read-only
**Priority**: P1
**Tags**: cpp, grpc, utility
**Context**: C++ gRPC service converting between currencies. (Note: actual implementation is Node.js/gRPC.)

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 1 | **RISKs**: 16 | **INFOs**: 14

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days. The single BLOCKER (AUTH-Q1: Machine Identity Authentication) must be resolved before any agent can safely call this service. The gRPC server binds with insecure credentials and all mesh-layer identity controls (AuthorizationPolicies, Sidecars, NetworkPolicies) are disabled in the Helm values. Any pod in the cluster can call any RPC without authentication or attribution.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 1 |
| RISK | 16 |
| INFO | 14 |
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

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: The gRPC server in `server.js` binds with `grpc.ServerCredentials.createInsecure()` — no TLS, no mTLS, no authentication of any kind at the application layer. The Helm chart (`helm-chart/templates/currencyservice.yaml`) defines an Istio AuthorizationPolicy and Sidecar resource, but both are gated behind values flags. In `helm-chart/values.yaml`, `authorizationPolicies.create: false`, `sidecars.create: false`, and `networkPolicies.create: false` — all three mesh-layer identity controls are disabled by default. With sidecars disabled, there is no mTLS between pods. With AuthorizationPolicies disabled, there is no caller restriction. Any pod in the namespace can call any RPC on port 7000 without authentication. No OAuth2 client credentials flow, no API key authentication, no service account attribution in audit logs.
- **Gap**: Zero authentication at both application and mesh layers. No machine identity verification. No principal attribution for any call. An agent calling this service cannot be identified, and a malicious caller cannot be distinguished from a legitimate one.
- **Remediation**:
  - **Immediate**: Enable Istio sidecar injection (`sidecars.create: true`) and AuthorizationPolicies (`authorizationPolicies.create: true`) in `helm-chart/values.yaml`. This activates mTLS between pods and restricts callers to `frontend` and `checkoutservice` service accounts as defined in the Helm template. Add agent-specific K8s ServiceAccounts to the AuthorizationPolicy.
  - **Target State**: Mesh-level mTLS with per-service principal attribution. AuthorizationPolicy restricts callers to explicitly allowed service accounts. Agent identities are distinct ServiceAccounts with per-RPC path rules. Application-layer gRPC interceptor extracts Istio peer identity for audit logging.
  - **Estimated Effort**: Medium
  - **Dependencies**: None — this is the foundational blocker. AUTH-Q2, AUTH-Q3, AUTH-Q6, and AUTH-Q7 all depend on identity being established first.
- **Evidence**: `server.js` (`grpc.ServerCredentials.createInsecure()`), `helm-chart/values.yaml` (`authorizationPolicies.create: false`, `sidecars.create: false`, `networkPolicies.create: false`), `helm-chart/templates/currencyservice.yaml` (AuthorizationPolicy and Sidecar sections gated by values flags)

---

## RISKs — Proceed with Compensating Controls

### API-Q3: Structured Error Responses
- **Severity**: RISK
- **Finding**: The `convert` function in `server.js` catches errors and calls `callback(err.message)` — a plain string with no structured error codes, no gRPC status code mapping, and no retryable indicator. The `getSupportedCurrencies` function has no error handling at all. Neither RPC sets explicit gRPC status codes (e.g., `INVALID_ARGUMENT`, `NOT_FOUND`).
- **Gap**: Agents cannot distinguish retriable errors (e.g., transient server failure) from terminal errors (e.g., unsupported currency code). No structured error metadata in gRPC responses.
- **Compensating Controls**:
  - Wrap agent tool calls with client-side error classification based on gRPC status codes
  - Implement retry with exponential backoff for UNKNOWN/UNAVAILABLE status codes at the agent layer
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Refactor error handling to use explicit gRPC status codes (`grpc.status.INVALID_ARGUMENT` for bad currency codes, `grpc.status.NOT_FOUND` for unsupported currencies). Return structured error metadata via gRPC trailing metadata.
- **Evidence**: `server.js` (convert function catch block, getSupportedCurrencies with no error handling)

### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK
- **Finding**: AuthorizationPolicies are disabled (`authorizationPolicies.create: false` in `helm-chart/values.yaml`). The Helm template defines per-path rules restricting callers to `frontend` and `checkoutservice` service accounts, but this configuration is not active. With policies disabled, any pod in the namespace can call both RPCs. No IAM policies, no application-level RBAC, no agent-specific service accounts.
- **Gap**: No permission scoping at any layer. All callers have unrestricted access to all RPCs.
- **Compensating Controls**:
  - Enable AuthorizationPolicies as part of AUTH-Q1 remediation to activate caller restrictions
  - Define agent-specific K8s ServiceAccounts with per-RPC AuthorizationPolicy rules
- **Remediation Timeline**: 30–60 days (concurrent with AUTH-Q1)
- **Recommendation**: Enable AuthorizationPolicies and create agent-specific service accounts with per-RPC path rules (e.g., agent can call `Convert` but not `GetSupportedCurrencies`, or vice versa).
- **Evidence**: `helm-chart/values.yaml` (`authorizationPolicies.create: false`), `helm-chart/templates/currencyservice.yaml` (AuthorizationPolicy section — defined but inactive)

### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK
- **Finding**: The gRPC server in `server.js` accepts all calls that reach it — no authorization checks, no interceptors, no middleware. The Helm template defines per-path AuthorizationPolicy rules for `/hipstershop.CurrencyService/Convert` and `/hipstershop.CurrencyService/GetSupportedCurrencies`, but these are disabled (`authorizationPolicies.create: false`). No application-layer action-level authorization exists.
- **Gap**: No action-level authorization at any layer. If AuthorizationPolicies are enabled (AUTH-Q1), mesh-level per-path rules activate, but application-layer authorization remains absent.
- **Compensating Controls**:
  - Enabling AuthorizationPolicies (AUTH-Q1) provides mesh-level per-path authorization
  - Implement a gRPC server interceptor for defense-in-depth application-layer authorization
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Enable AuthorizationPolicies first (AUTH-Q1). Then implement a gRPC server interceptor that validates caller identity and authorized actions as defense in depth beyond the mesh layer.
- **Evidence**: `server.js` (no authorization logic), `helm-chart/templates/currencyservice.yaml` (per-path rules defined but inactive), `helm-chart/values.yaml`

### AUTH-Q5: Credential Management
- **Severity**: RISK
- **Finding**: No secrets or credentials are used by the service — it reads static JSON data with no database connections. Google Cloud Profiler uses implicit Workload Identity (no hardcoded credentials). No Secrets Manager, Vault, or external secrets operator integration. No `.env` files committed. No hardcoded passwords or API keys in source code. However, no credential management framework exists for future agent API keys or service credentials.
- **Gap**: No formal credential management system. While the service currently has no credentials to manage, there is no framework for credential lifecycle management if credentials are introduced.
- **Compensating Controls**:
  - Credential-free architecture eliminates current secret rotation concerns
  - Workload Identity for GCP libraries avoids hardcoded credentials
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Maintain credential-free architecture. If credentials are introduced (e.g., agent API keys), use K8s Secrets with an external secrets operator or AWS Secrets Manager with rotation.
- **Evidence**: `server.js`, `data/currency_conversion.json`, `package.json`

### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: No audit logging exists. Pino logs operational messages only (startup, conversion success/failure) with no principal attribution. Logs are ephemeral container stdout with no immutable storage configuration. No CloudTrail or equivalent. OpenTelemetry tracing is disabled by default (`opentelemetryCollector.create: false`, `tracing: false` in `helm-chart/values.yaml`). The tracing code in `server.js` is gated behind `ENABLE_TRACING == "1"` which is not set when `googleCloudOperations.tracing` is false.
- **Gap**: No immutable audit trail. No principal attribution in any log output. No tracing. Cannot determine who called the service or attribute actions to specific agent identities.
- **Compensating Controls**:
  - Configure K8s log forwarding to immutable store (e.g., CloudWatch Logs with retention policy, S3 with Object Lock)
  - Enable OpenTelemetry tracing to provide request-level trace context as a partial audit signal
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Enable tracing (`opentelemetryCollector.create: true`, `tracing: true`). Add structured audit logging with caller identity (extracted from Istio mTLS peer identity once AUTH-Q1 is resolved). Forward to immutable store.
- **Evidence**: `server.js` (Pino logger with no audit fields, tracing gated behind env var), `helm-chart/values.yaml` (`opentelemetryCollector.create: false`, `tracing: false`)

### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK
- **Finding**: AuthorizationPolicies are disabled, so there is no mechanism to deny specific service accounts. NetworkPolicies are also disabled. No API key revocation, no service account disable endpoint, no automated suspension mechanism. Even if policies were enabled, changes would require Helm value updates or manual kubectl edits — no automated or rapid suspension path exists.
- **Gap**: No suspension mechanism at any layer. Cannot isolate a misbehaving agent without manual intervention and redeployment.
- **Compensating Controls**:
  - Enable AuthorizationPolicies and NetworkPolicies (AUTH-Q1) to create a foundation for identity-based blocking
  - Manual kubectl patch of AuthorizationPolicy or NetworkPolicy as emergency measure
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Enable AuthorizationPolicies and NetworkPolicies first (AUTH-Q1). Then implement automated suspension via AuthorizationPolicy updates triggered by anomaly detection. Consider an operator or webhook that can instantly deny a service account.
- **Evidence**: `helm-chart/values.yaml` (`authorizationPolicies.create: false`, `networkPolicies.create: false`), `helm-chart/templates/currencyservice.yaml`

### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: Service is stateless — reads static JSON and performs arithmetic. No multi-step write operations. No state mutations to compensate. No saga pattern, no undo endpoints, no Step Functions.
- **Gap**: No compensation mechanisms exist, though no state mutations require compensation. The RISK rating reflects the absence of the mechanism, not an active threat.
- **Compensating Controls**:
  - Stateless nature means compensation is not operationally needed
  - Document stateless architecture for agent integration teams
- **Remediation Timeline**: No immediate action; revisit if write operations are added
- **Recommendation**: Maintain stateless architecture documentation. Implement compensation if write operations are added.
- **Evidence**: `server.js`, `data/currency_conversion.json`

### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK
- **Finding**: No application-level rate limiting. No gRPC interceptor for request throttling. K8s resource limits cap CPU (200m) and memory (256Mi) but not request rates. ClusterIP service with no API Gateway. Istio sidecar is disabled (`sidecars.create: false`), so no Envoy-level rate limiting is possible. No WAF rules.
- **Gap**: Runaway agent loop could overwhelm the service at machine speed. No per-caller rate limiting at any layer.
- **Compensating Controls**:
  - Enable Istio sidecars and configure Envoy rate limiting per source service account
  - Configure agent-side request rate caps in the agent orchestration layer
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Enable Istio sidecars (AUTH-Q1). Add gRPC interceptor for application-level rate limiting or configure Istio/Envoy rate limiting per source service account.
- **Evidence**: `server.js` (no rate limiting), `helm-chart/values.yaml` (`sidecars.create: false`), `helm-chart/templates/currencyservice.yaml` (resource limits only)

### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK
- **Finding**: Skaffold provides local development via Docker build. CI deploys per-PR to ephemeral namespaces on `prs-gke-cluster` (`.github/workflows/ci-pr.yaml`). Smoke tests run via loadgenerator. No persistent agent testing environment with production-equivalent data shape.
- **Gap**: No dedicated agent testing environment. Ephemeral PR namespaces are transient and not designed for agent integration testing.
- **Compensating Controls**:
  - Use Skaffold for local instance with Docker build for isolated testing
  - Leverage per-PR ephemeral namespaces for integration testing
- **Remediation Timeline**: 30 days
- **Recommendation**: Create a persistent staging namespace for agent integration testing with production-equivalent configuration.
- **Evidence**: `.github/workflows/ci-pr.yaml` (ephemeral PR deployment), `Dockerfile`, `cloudbuild.yaml`

### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: Static, publicly available ECB exchange rates embedded in `data/currency_conversion.json`. No regulated data (no PII, PHI, or financial account data). No explicit residency requirements or documentation. No `DATA_CLASSIFICATION.md` in the currencyservice directory. The parent repo has a `DATA_CLASSIFICATION.md` at the root but it does not cover per-service residency posture.
- **Gap**: No formal data residency documentation for this service. Public ECB rates have no residency restrictions, but no formal analysis exists.
- **Compensating Controls**:
  - Document that current data (ECB public rates) has no residency restrictions
  - Implement residency controls proactively if user-specific or regulated data is added
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document data residency posture formally in a service-level `DATA_CLASSIFICATION.md`. Implement residency-aware controls if the service scope expands to include regulated or user-specific data.
- **Evidence**: `data/currency_conversion.json`, `server.js`

### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK
- **Finding**: CI exists via Cloud Build (`cloudbuild.yaml`) and GitHub Actions (`.github/workflows/ci-pr.yaml`). Smoke tests run via loadgenerator in ephemeral PR namespaces. However, the proto uses unversioned `package hipstershop` (no version suffix). No `buf.yaml` exists for proto linting or breaking change detection. No `buf breaking` in CI. No currencyservice-specific unit tests — `package.json` has `"test": "echo \"Error: no test specified\" && exit 1"`. CI PR workflow runs Go and C# tests only; Node.js currencyservice is not tested.
- **Gap**: No automated breaking change detection for proto schemas. No service-specific contract tests. No proto linting. Unversioned proto package means no formal versioning contract.
- **Compensating Controls**:
  - Protobuf wire compatibility provides implicit backward compatibility for additive changes
  - Loadgenerator smoke tests catch gross integration failures
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `buf.yaml` for proto linting. Add `buf breaking` to CI pipeline for breaking change detection. Add CurrencyService-specific contract tests. Version the proto package (e.g., `hipstershop.v1`).
- **Evidence**: `proto/demo.proto` (`package hipstershop` — no version), `package.json` (stub test script), `.github/workflows/ci-pr.yaml` (no Node.js tests), `cloudbuild.yaml`

### ENG-Q3: Rollback Capability
- **Severity**: RISK
- **Finding**: K8s Deployment with rollout history. Skaffold deployment via Cloud Build. No automated rollback triggers. Manual rollback via `kubectl rollout undo` only. No canary deployment, no Flagger, no Argo Rollouts. No feature flags.
- **Gap**: No automated rollback on service degradation. Manual rollback only. No canary analysis.
- **Compensating Controls**:
  - K8s rollout history enables manual rollback within minutes
  - Liveness/readiness gRPC probes prevent traffic to unhealthy pods
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure automated rollback triggers using Flagger or Argo Rollouts with canary analysis. Add health-based rollback triggers.
- **Evidence**: `helm-chart/templates/currencyservice.yaml` (Deployment with probes), `cloudbuild.yaml` (Skaffold deploy)

### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK
- **Finding**: OpenTelemetry SDK is present in `package.json` and `server.js` with gRPC instrumentation registered unconditionally. However, trace export is gated behind `ENABLE_TRACING == "1"`, and the Helm values have `opentelemetryCollector.create: false` and `tracing: false` — so the `ENABLE_TRACING` and `COLLECTOR_SERVICE_ADDR` environment variables are not set. Tracing is effectively disabled. Pino provides structured JSON logging with `severity` field, but no `correlation_id`, `request_id`, or `trace_id` in log entries.
- **Gap**: Tracing disabled by default. No trace context in logs. Agent-initiated requests cannot be traced end-to-end across services.
- **Compensating Controls**:
  - Enable tracing by setting `opentelemetryCollector.create: true` and `tracing: true` in values.yaml
  - gRPC instrumentation is already registered — enabling the collector activates trace propagation
- **Remediation Timeline**: 30 days
- **Recommendation**: Enable OpenTelemetry tracing in Helm values. Add trace_id to Pino log entries for log-to-trace correlation.
- **Evidence**: `server.js` (OpenTelemetry setup gated behind env var), `helm-chart/values.yaml` (`opentelemetryCollector.create: false`, `tracing: false`), `package.json` (OpenTelemetry dependencies present)

### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK
- **Finding**: No alerting configured. No CloudWatch alarms, no Prometheus alerting rules, no PagerDuty/OpsGenie integration. Metrics collection is disabled (`metrics: false` in `helm-chart/values.yaml`). K8s liveness/readiness gRPC probes provide pod availability detection only. No HPA configured — fixed replica count with no auto-scaling based on metrics. No monitoring alerts of any kind.
- **Gap**: No alerting on error rates or latency. Service degradation will not be detected until agents start failing.
- **Compensating Controls**:
  - K8s liveness/readiness probes restart unhealthy pods automatically
  - Agent-side timeout and retry logic provides client-side detection
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Enable metrics collection (`metrics: true`). Configure alerting on gRPC error rates and p99 latency. Add HPA for auto-scaling based on CPU/request metrics.
- **Evidence**: `helm-chart/values.yaml` (`metrics: false`), `helm-chart/templates/currencyservice.yaml` (probes only, no HPA)

### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK
- **Finding**: Proto uses unversioned `package hipstershop` — no version suffix (e.g., `hipstershop.v1`). No `buf.yaml` for proto linting or governance. No breaking change detection tools in CI. No changelog or deprecation notices. The proto file is a shared monolith defining all services in a single file — a breaking change to any service's messages affects all consumers.
- **Gap**: No schema versioning. No breaking change detection. Agent tool schemas will break silently on proto changes.
- **Compensating Controls**:
  - Protobuf wire compatibility provides implicit backward compatibility for additive changes
  - Pin agent tool definitions to specific proto field numbers
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Version the proto package (e.g., `hipstershop.v1`). Add `buf.yaml` for proto linting. Add `buf breaking` to CI for breaking change detection.
- **Evidence**: `proto/demo.proto` (`package hipstershop` — no version, shared monolith proto)

### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK
- **Finding**: IaC exists across multiple layers: Helm chart, Terraform. CODEOWNERS enforces peer review. GitHub Actions CI on PRs. However, all security-relevant infrastructure controls are disabled by default: AuthorizationPolicies, NetworkPolicies, and Sidecars are all `create: false` in `helm-chart/values.yaml`. No drift detection configured.
- **Gap**: Security policies defined in IaC but disabled. No drift detection. The integration surface is exposed without any IaC-enforced security controls active.
- **Compensating Controls**:
  - IaC definitions exist and can be enabled by changing values flags
  - CODEOWNERS enforces peer review on IaC changes
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Enable all security policies in `helm-chart/values.yaml`. Implement drift detection via ArgoCD or Flux.
- **Evidence**: `helm-chart/values.yaml` (policies disabled), `helm-chart/templates/currencyservice.yaml`, `.github/CODEOWNERS`, `.github/terraform/main.tf`

---

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: Well-documented gRPC interface in `proto/demo.proto` with `CurrencyService` defining two RPCs: `GetSupportedCurrencies(Empty) returns (GetSupportedCurrenciesResponse)` and `Convert(CurrencyConversionRequest) returns (Money)`. Proto messages include detailed comments (e.g., ISO 4217 currency codes, nanos precision). Implemented faithfully in `server.js`. Positive finding.
- **Implication**: gRPC interface can be used directly as agent tool binding. Proto enables auto-generated client code in any language.
- **Recommendation**: No remediation needed.
- **Evidence**: `proto/demo.proto`, `server.js`

### API-Q2: Machine-Readable API Specification
- **Severity**: INFO
- **Finding**: `proto/demo.proto` is a machine-readable specification. Protobuf is strongly typed with field numbers, explicit data types (`int64`, `int32`, `string`), and inline documentation comments. Spec is current with implementation — `server.js` loads `demo.proto` and implements exactly the two RPCs defined. No `buf.yaml` for proto governance, but the proto itself is a valid machine-readable spec. Positive finding.
- **Implication**: Agent tool definitions can be auto-generated from proto. gRPC reflection could enable runtime schema discovery.
- **Recommendation**: Consider enabling gRPC server reflection for runtime schema discovery. Add `buf.yaml` for proto linting governance.
- **Evidence**: `proto/demo.proto`, `server.js`

### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Both RPCs are read-only, stateless, and inherently idempotent. `GetSupportedCurrencies` returns static currency codes from `data/currency_conversion.json`. `Convert` performs deterministic arithmetic on static exchange rates. Same input always produces same output. No write side effects.
- **Implication**: No idempotency concerns for read-only scope. Pure functions with no state mutations.
- **Recommendation**: No action needed.
- **Evidence**: `server.js` (getSupportedCurrencies, convert functions), `data/currency_conversion.json`

### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Archetype-Calibrated**: stateless-utility — downgraded to INFO
- **Finding**: No JWT parsing, no token exchange, no user context headers. No identity context in gRPC calls. The service does not inspect caller identity at any layer. With Istio sidecars disabled, there is no implicit caller identity from mTLS either.
- **Implication**: For a stateless-utility returning public reference data (ECB exchange rates), identity propagation has minimal security impact — responses are not user-specific and data is public. Identity propagation becomes relevant only if the service evolves to handle user-specific data.
- **Recommendation**: No immediate action. Implement identity propagation if the service evolves to handle user-specific data.
- **Evidence**: `server.js`, `helm-chart/values.yaml` (`sidecars.create: false`)

### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No writes, deletes, or modifications. Minimal blast radius. Read-only operations on public static data. No transaction limits needed.
- **Implication**: Transaction limits not applicable for read-only operations on public data.
- **Recommendation**: Implement if write operations are added.
- **Evidence**: `server.js`

### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO
- **Finding**: Handles public ECB exchange rates and monetary amounts only. `data/currency_conversion.json` contains 33 currency-to-EUR conversion rates — all publicly available from the European Central Bank. No PII, PHI, or financial account data. Proto messages contain `currency_code` (ISO 4217), `units`, and `nanos` — no user identifiers, no account numbers, no sensitive fields. No `DATA_CLASSIFICATION.md` at the service level, but the data is inherently public.
- **Implication**: No data classification controls needed for current data. No PII exposure risk. Positive finding for agent integration — no data sensitivity gates.
- **Recommendation**: Implement classification if user-specific financial data is added. Consider creating a service-level `DATA_CLASSIFICATION.md` documenting the public nature of the data.
- **Evidence**: `data/currency_conversion.json`, `proto/demo.proto` (Money, CurrencyConversionRequest messages)

### DATA-Q6: PII Redaction in Logs
- **Severity**: INFO
- **Finding**: Pino logs contain operational messages only: startup messages, "Getting supported currencies...", "conversion request successful", and "conversion request failed: {err}". No request details (currency codes, amounts) are logged. No PII in the data model. No PII leakage risk.
- **Implication**: No PII redaction needed. Positive finding.
- **Recommendation**: No action needed. If request details are added to logs in the future, ensure no sensitive data is included.
- **Evidence**: `server.js` (Pino logger calls)

### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: gRPC Protocol Buffers — strongly-typed binary format with explicit types (`int64 units`, `int32 nanos`, `string currency_code`), field numbers, and inline documentation comments. `Money` message is well-documented with precision semantics for nanos.
- **Implication**: Protobuf is more structured than JSON. Excellent for agent integration with auto-generated client code. Binary format requires gRPC client libraries but provides type safety.
- **Recommendation**: No action needed.
- **Evidence**: `proto/demo.proto` (Money, CurrencyConversionRequest, GetSupportedCurrenciesResponse messages)

### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit headers or gRPC trailing metadata. Internal ClusterIP service with no API Gateway. K8s resource limits (CPU: 200m, memory: 256Mi) provide implicit resource capping but not request-rate signaling. No `X-RateLimit-Remaining` or `Retry-After` equivalent in gRPC responses.
- **Implication**: Agents cannot self-throttle based on server-side rate limit signals. Must rely on client-side rate configuration.
- **Recommendation**: Add gRPC trailing metadata with rate limit status when rate limiting is implemented (see STATE-Q5).
- **Evidence**: `server.js`, `helm-chart/templates/currencyservice.yaml` (resource limits)

### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No quality metrics or validation. 33 static currency entries in `data/currency_conversion.json`. No validation that rates are positive or within expected ranges. No freshness indicator — rates are fixed at build time (embedded in container image). No data profiling or quality dashboards.
- **Implication**: Quality is static and deterministic — no runtime degradation risk. However, stale exchange rates could cause incorrect conversions if the data file is not updated.
- **Recommendation**: Add validation that rates are positive and within expected ranges. Consider a freshness mechanism (e.g., periodic update from ECB API or a `last_updated` timestamp).
- **Evidence**: `data/currency_conversion.json`

### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Clear semantic names throughout: `currency_code`, `units`, `nanos`, `to_code`, `from`, `currency_codes`. Detailed inline comments explain semantics (e.g., "The 3-letter currency code defined in ISO 4217", "Number of nano (10^-9) units of the amount"). No legacy abbreviations or opaque codes.
- **Implication**: LLMs can interpret fields directly without a data dictionary. Field names are self-documenting.
- **Recommendation**: No action needed.
- **Evidence**: `proto/demo.proto` (Money, CurrencyConversionRequest messages with comments)

### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal data catalog. Proto file serves as informal schema documentation with inline comments. `data/currency_conversion.json` is self-describing (ISO 4217 currency codes as keys, EUR-relative rates as values). No Glue Data Catalog, no DataHub, no API catalog registration.
- **Implication**: Sufficient for a single-purpose utility service. Proto documentation is adequate for agent tool definition.
- **Recommendation**: Register in organization API catalog if part of a larger service mesh or data platform.
- **Evidence**: `proto/demo.proto`, `data/currency_conversion.json`

### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics. Pino logs conversion success/failure counts implicitly but does not publish metrics. No CloudWatch custom metrics, no Prometheus counters for conversion volume by currency pair. Metrics collection is disabled (`metrics: false`).
- **Implication**: No business outcome monitoring. For a utility service, operational metrics may suffice initially.
- **Recommendation**: Enable metrics collection. Publish counters for conversion volume by currency pair if business analytics are needed.
- **Evidence**: `server.js` (logger.info for conversion success), `helm-chart/values.yaml` (`metrics: false`)

### ENG-Q4: API Test Coverage
- **Severity**: INFO
- **Archetype-Calibrated**: stateless-utility — evaluated as INFO
- **Finding**: Zero test files. `package.json` has `"test": "echo \"Error: no test specified\" && exit 1"` — a stub that exits with error. CI PR workflow (`.github/workflows/ci-pr.yaml`) runs Go and C# tests only; Node.js currencyservice is not tested. No unit tests for `convert`, `_carry`, or `getSupportedCurrencies` functions. No gRPC integration tests.
- **Implication**: For a stateless-utility with simple arithmetic logic (`_carry` function, EUR-relative conversion), the risk of zero test coverage is lower than for stateful services. However, the `_carry` function has edge cases (negative amounts, overflow) that are untested.
- **Recommendation**: Add unit tests for `convert` function, `_carry` helper (especially edge cases: negative amounts, zero, large values), and `getSupportedCurrencies`. Add gRPC integration tests.
- **Evidence**: `package.json` (stub test script), `.github/workflows/ci-pr.yaml` (no Node.js tests), `server.js`

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: Well-documented gRPC interface in `proto/demo.proto` with `CurrencyService` defining `GetSupportedCurrencies(Empty) returns (GetSupportedCurrenciesResponse)` and `Convert(CurrencyConversionRequest) returns (Money)`. Proto messages include detailed comments. Implemented in `server.js`. Positive finding — BLOCKER criteria satisfied.
- **Gap**: None.
- **Recommendation**: No remediation needed.
- **Evidence**: `proto/demo.proto`, `server.js`

#### API-Q2: Machine-Readable API Specification
- **Severity**: INFO
- **Finding**: `proto/demo.proto` is a machine-readable spec. Protobuf is strongly typed with field numbers, explicit data types, and inline documentation. Current with implementation. Positive finding.
- **Gap**: None.
- **Recommendation**: Consider enabling gRPC server reflection. Add `buf.yaml` for proto governance.
- **Evidence**: `proto/demo.proto`, `server.js`

#### API-Q3: Structured Error Responses
- **Severity**: RISK
- **Finding**: `convert` calls `callback(err.message)` — plain string. No gRPC status codes set explicitly. `getSupportedCurrencies` has no error handling.
- **Gap**: Agents cannot distinguish retriable from terminal errors.
- **Recommendation**: Use explicit gRPC status codes and structured error metadata.
- **Evidence**: `server.js` (convert function catch block)

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Both RPCs are read-only, stateless, inherently idempotent. Same input always produces same output. No write side effects.
- **Gap**: N/A — no write operations.
- **Recommendation**: No action needed.
- **Evidence**: `server.js`, `data/currency_conversion.json`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: gRPC Protocol Buffers — strongly-typed binary format with explicit types, field numbers, and documentation comments.
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
- **Finding**: No rate limit headers or gRPC trailing metadata. Internal ClusterIP service. K8s resource limits provide implicit capping only.
- **Gap**: Agents cannot self-throttle based on server-side rate limit signals.
- **Recommendation**: Add gRPC trailing metadata with rate limit status when rate limiting is implemented.
- **Evidence**: `server.js`, `helm-chart/templates/currencyservice.yaml`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: The gRPC server binds with `grpc.ServerCredentials.createInsecure()` — no TLS, no mTLS, no authentication at the application layer. All mesh-layer identity controls are disabled: `authorizationPolicies.create: false`, `sidecars.create: false`, `networkPolicies.create: false` in `helm-chart/values.yaml`. Any pod in the namespace can call any RPC on port 7000 without authentication. No OAuth2 client credentials, no API keys, no service account attribution.
- **Gap**: Zero authentication at both application and mesh layers. No machine identity verification. No principal attribution.
- **Recommendation**: Enable Istio sidecars and AuthorizationPolicies. Add agent-specific K8s ServiceAccounts to the AuthorizationPolicy. Implement gRPC interceptor for application-layer identity extraction.
- **Evidence**: `server.js` (`grpc.ServerCredentials.createInsecure()`), `helm-chart/values.yaml` (all policies disabled), `helm-chart/templates/currencyservice.yaml`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK
- **Finding**: AuthorizationPolicies disabled. No permission scoping at any layer. All callers have unrestricted access to all RPCs.
- **Gap**: No per-RPC scoping. No agent-specific permissions.
- **Recommendation**: Enable AuthorizationPolicies. Create agent-specific service accounts with per-RPC path rules.
- **Evidence**: `helm-chart/values.yaml` (`authorizationPolicies.create: false`), `helm-chart/templates/currencyservice.yaml`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK
- **Finding**: No authorization checks in `server.js`. AuthorizationPolicy per-path rules defined in Helm template but disabled. No application-layer action-level authorization.
- **Gap**: No action-level authorization at any layer.
- **Recommendation**: Enable AuthorizationPolicies. Implement gRPC server interceptor for defense-in-depth.
- **Evidence**: `server.js`, `helm-chart/templates/currencyservice.yaml`, `helm-chart/values.yaml`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Archetype-Calibrated**: stateless-utility — downgraded to INFO
- **Finding**: No JWT parsing, token exchange, or user context headers. Istio sidecars disabled — no implicit mTLS caller identity. Service returns public data with no user-specific context.
- **Gap**: No identity propagation. Minimal impact for stateless-utility returning public data.
- **Recommendation**: No immediate action. Implement if service evolves to handle user-specific data.
- **Evidence**: `server.js`, `helm-chart/values.yaml` (`sidecars.create: false`)

#### AUTH-Q5: Credential Management
- **Severity**: RISK
- **Finding**: No secrets or credentials used. Static JSON data, no database connections. Google Cloud Profiler uses Workload Identity. No Secrets Manager or Vault integration. No hardcoded credentials found.
- **Gap**: No credential management framework for future agent credentials.
- **Recommendation**: Maintain credential-free architecture. Use K8s Secrets with external secrets operator if credentials are introduced.
- **Evidence**: `server.js`, `data/currency_conversion.json`, `package.json`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: No audit logging. Pino logs operational messages only with no principal attribution. Tracing disabled (`opentelemetryCollector.create: false`, `tracing: false`). Logs are ephemeral container stdout.
- **Gap**: No immutable audit trail. No principal attribution. No tracing.
- **Recommendation**: Enable tracing. Add structured audit logging with caller identity. Forward to immutable store.
- **Evidence**: `server.js` (Pino logger), `helm-chart/values.yaml` (`opentelemetryCollector.create: false`, `tracing: false`)

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK
- **Finding**: AuthorizationPolicies and NetworkPolicies both disabled. No mechanism to deny specific service accounts. No automated suspension capability.
- **Gap**: No suspension mechanism at any layer.
- **Recommendation**: Enable AuthorizationPolicies and NetworkPolicies. Implement automated suspension via policy updates triggered by anomaly detection.
- **Evidence**: `helm-chart/values.yaml` (`authorizationPolicies.create: false`, `networkPolicies.create: false`), `helm-chart/templates/currencyservice.yaml`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: Stateless service — reads static JSON, performs arithmetic. No multi-step write operations. No state mutations to compensate.
- **Gap**: No compensation mechanisms, though none operationally needed.
- **Recommendation**: Maintain stateless architecture. Implement compensation if write operations are added.
- **Evidence**: `server.js`, `data/currency_conversion.json`

#### STATE-Q2: Queryable Current State
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q3: Concurrency Controls
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
- **Finding**: No application-level rate limiting. No gRPC interceptor. Istio sidecars disabled — no Envoy-level rate limiting. K8s resource limits cap CPU/memory only. No WAF rules.
- **Gap**: Runaway agent loop could overwhelm the service. No per-caller rate limiting.
- **Recommendation**: Enable Istio sidecars. Add gRPC interceptor or Envoy rate limiting per source service account.
- **Evidence**: `server.js`, `helm-chart/values.yaml` (`sidecars.create: false`), `helm-chart/templates/currencyservice.yaml`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No writes, deletes, or modifications. Read-only operations on public static data. Minimal blast radius.
- **Gap**: N/A for read-only scope.
- **Recommendation**: Implement if write operations are added.
- **Evidence**: `server.js`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q2: Configurable Approval Gates
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK
- **Finding**: Skaffold for local development. CI deploys per-PR to ephemeral namespaces on `prs-gke-cluster`. Smoke tests via loadgenerator. No persistent agent testing environment.
- **Gap**: No dedicated agent testing environment.
- **Recommendation**: Create persistent staging namespace for agent integration testing.
- **Evidence**: `.github/workflows/ci-pr.yaml`, `Dockerfile`, `cloudbuild.yaml`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO
- **Finding**: Public ECB exchange rates and monetary amounts only. No PII, PHI, or financial account data. No `DATA_CLASSIFICATION.md` at service level. Data is inherently public.
- **Gap**: No formal data classification document, but data is public reference data.
- **Recommendation**: Create service-level `DATA_CLASSIFICATION.md` documenting public nature of data.
- **Evidence**: `data/currency_conversion.json`, `proto/demo.proto`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: Static, publicly available ECB exchange rates. No regulated data. No explicit residency documentation.
- **Gap**: No formal data residency documentation.
- **Recommendation**: Document data residency posture formally.
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
- **Finding**: No quality metrics. 33 static currency entries. No validation of rate ranges. Quality fixed at build time.
- **Gap**: No freshness indicator or validation.
- **Recommendation**: Add validation that rates are positive and within expected ranges.
- **Evidence**: `data/currency_conversion.json`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK
- **Finding**: Proto uses unversioned `package hipstershop` — no version suffix. No `buf.yaml`. No breaking change detection in CI. Shared monolith proto defining all services in a single file.
- **Gap**: No schema versioning. No breaking change detection. Agent tool schemas will break silently on proto changes.
- **Recommendation**: Version the proto package. Add `buf.yaml` and `buf breaking` to CI. Consider splitting monolith proto.
- **Evidence**: `proto/demo.proto` (`package hipstershop`)

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Clear semantic names: `currency_code`, `units`, `nanos`, `to_code`, `from`, `currency_codes`. Detailed inline comments with ISO 4217 references. No legacy abbreviations.
- **Gap**: None.
- **Recommendation**: No action needed.
- **Evidence**: `proto/demo.proto`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal catalog. Proto file serves as informal documentation. Self-describing JSON data with ISO 4217 keys.
- **Gap**: No formal catalog registration.
- **Recommendation**: Register in organization API catalog if part of larger data mesh.
- **Evidence**: `proto/demo.proto`, `data/currency_conversion.json`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK
- **Finding**: OpenTelemetry SDK present with gRPC instrumentation registered. Trace export gated behind `ENABLE_TRACING == "1"` — disabled by default (`opentelemetryCollector.create: false`, `tracing: false`). Pino provides structured JSON logging but no trace_id or correlation_id in log entries.
- **Gap**: Tracing disabled. No trace context in logs. Agent-initiated requests not traceable.
- **Recommendation**: Enable OpenTelemetry tracing. Add trace_id to Pino log entries.
- **Evidence**: `server.js`, `helm-chart/values.yaml`, `package.json`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK
- **Finding**: No alerting configured. Metrics disabled (`metrics: false`). No HPA. No monitoring alerts. K8s probes provide pod availability only.
- **Gap**: No alerting on error rates or latency.
- **Recommendation**: Enable metrics. Configure alerting on gRPC error rates and p99 latency. Add HPA.
- **Evidence**: `helm-chart/values.yaml` (`metrics: false`), `helm-chart/templates/currencyservice.yaml`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics. Pino logs conversion success/failure. Metrics collection disabled.
- **Gap**: No business outcome monitoring.
- **Recommendation**: Enable metrics. Publish conversion volume by currency pair if needed.
- **Evidence**: `server.js`, `helm-chart/values.yaml`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK
- **Finding**: IaC exists (Helm, Terraform). CODEOWNERS enforces peer review. GitHub Actions CI. However, all security policies disabled by default in values.yaml. No drift detection.
- **Gap**: Security policies defined but disabled. No drift detection.
- **Recommendation**: Enable all security policies. Implement drift detection via ArgoCD or Flux.
- **Evidence**: `helm-chart/values.yaml`, `helm-chart/templates/currencyservice.yaml`, `.github/CODEOWNERS`, `.github/terraform/main.tf`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK
- **Finding**: CI exists (Cloud Build, GitHub Actions). Smoke tests via loadgenerator. Unversioned proto (`package hipstershop`). No `buf.yaml`. No `buf breaking` in CI. No currencyservice-specific tests. CI runs Go and C# tests only.
- **Gap**: No breaking change detection. No service-specific contract tests. No proto linting.
- **Recommendation**: Add `buf.yaml`, `buf breaking` to CI. Add CurrencyService contract tests. Version proto package.
- **Evidence**: `proto/demo.proto`, `package.json`, `.github/workflows/ci-pr.yaml`, `cloudbuild.yaml`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK
- **Finding**: K8s Deployment with rollout history. Skaffold deployment. No automated rollback triggers. Manual `kubectl rollout undo` only. No canary, no Flagger, no Argo Rollouts.
- **Gap**: No automated rollback on service degradation.
- **Recommendation**: Configure automated rollback with Flagger or Argo Rollouts.
- **Evidence**: `helm-chart/templates/currencyservice.yaml`, `cloudbuild.yaml`

#### ENG-Q4: API Test Coverage
- **Severity**: INFO
- **Archetype-Calibrated**: stateless-utility — evaluated as INFO
- **Finding**: Zero test files. Stub test script in `package.json`. CI skips currencyservice. No unit tests for `convert`, `_carry`, or `getSupportedCurrencies`.
- **Gap**: Zero test coverage. Edge cases in `_carry` function untested.
- **Recommendation**: Add unit tests for `convert`, `_carry` (edge cases), and `getSupportedCurrencies`. Add gRPC integration tests.
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
| `helm-chart/values.yaml` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q6, AUTH-Q7, STATE-Q5, OBS-Q1, OBS-Q2, OBS-Q3, ENG-Q1, DISC-Q1 |
| `helm-chart/templates/currencyservice.yaml` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q7, STATE-Q5, API-Q8, OBS-Q2, ENG-Q1, ENG-Q3 |
| `.github/terraform/main.tf` | ENG-Q1 |

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `server.js` | API-Q1, API-Q2, API-Q3, API-Q4, API-Q5, API-Q8, AUTH-Q1, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q6, STATE-Q1, STATE-Q5, STATE-Q6, DATA-Q1, DATA-Q2, DATA-Q6, OBS-Q1, OBS-Q3, ENG-Q4 |
| `client.js` | API-Q1 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `proto/demo.proto` | API-Q1, API-Q2, API-Q4, API-Q5, DATA-Q1, DISC-Q1, DISC-Q2, DISC-Q3, ENG-Q2 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/ci-pr.yaml` | HITL-Q3, ENG-Q2, ENG-Q4 |
| `cloudbuild.yaml` | HITL-Q3, ENG-Q2, ENG-Q3 |
| `.github/CODEOWNERS` | ENG-Q1 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `Dockerfile` | HITL-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `package.json` | AUTH-Q5, OBS-Q1, ENG-Q2, ENG-Q4 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `data/currency_conversion.json` | API-Q4, AUTH-Q5, STATE-Q1, DATA-Q1, DATA-Q7, DISC-Q3 |
