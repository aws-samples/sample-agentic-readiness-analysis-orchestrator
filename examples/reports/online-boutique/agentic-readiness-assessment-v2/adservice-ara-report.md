# Agentic Readiness Assessment Report

**Target**: services/microservices-demo/src/adservice
**Date**: 2026-04-16
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Service Archetype**: stateless-utility (user-provided)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: java, grpc, ads
**Context**: Java gRPC service serving contextual ads based on product categories.

---

## Readiness Profile: Pilot-Ready

**BLOCKERs**: 0 | **RISKs**: 5 | **INFOs**: 26

Supervised pilot with: (1) human approval gates on irreversible actions, (2) agent limited to low-blast-radius operations, (3) compensating controls for each open RISK, (4) remediation timeline before expanding scope.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 0 |
| RISK | 5 |
| INFO | 26 |
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
- **Finding**: The `getAds` method in `AdServiceImpl` catches `StatusRuntimeException` and forwards it via `responseObserver.onError(e)`. gRPC provides standard status codes (OK, INTERNAL, UNAVAILABLE) which are machine-readable. However, there is no structured error body beyond the gRPC status code — no error code taxonomy, no retryable boolean, no detailed error message format using the gRPC rich error model (`com.google.rpc.ErrorInfo`). An agent receiving `INTERNAL` cannot determine whether to retry.
- **Gap**: No rich error model. Agents cannot distinguish retriable from terminal errors based on gRPC status alone.
- **Compensating Controls**:
  - Wrap agent tool calls with client-side error classification based on gRPC status codes (UNAVAILABLE → retry, INVALID_ARGUMENT → terminal)
  - Implement retry with exponential backoff for UNKNOWN/UNAVAILABLE status codes
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement gRPC rich error model using `com.google.rpc.ErrorInfo` to include error codes, retryable flags, and detailed messages in error responses.
- **Evidence**: `src/adservice/src/main/java/hipstershop/AdService.java` (catch block with `responseObserver.onError(e)`)

### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicy is enabled (`authorizationPolicies.create: true` in `helm-chart/values.yaml`), restricting callers to the `frontend` service account on the `/hipstershop.AdService/GetAds` path. However, no agent-specific service accounts are defined. No IAM policies or application-level RBAC. All authorized callers have identical access — no differentiation between human-initiated and agent-initiated requests.
- **Gap**: No agent-specific service accounts with tailored permissions. No per-caller differentiation.
- **Compensating Controls**:
  - Istio AuthorizationPolicy restricts callers to known service accounts (defense in depth)
  - Define agent-specific K8s ServiceAccounts and add them to the AuthorizationPolicy with per-path rules
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create agent-specific service accounts with per-RPC AuthorizationPolicy rules scoping agent access to `GetAds`.
- **Evidence**: `helm-chart/templates/adservice.yaml` (AuthorizationPolicy section), `helm-chart/values.yaml` (`authorizationPolicies.create: true`)

### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicy is enabled and defines per-path rules (`/hipstershop.AdService/GetAds`, method POST, port 9555). However, the application code itself has no action-level authorization — the gRPC server in `AdService.java` accepts all calls that reach it via `ServerBuilder.forPort(port)` with no `ServerInterceptor` for authorization. Authorization is entirely at the mesh layer.
- **Gap**: No application-layer action-level authorization. If the mesh is bypassed or misconfigured, all RPCs are open.
- **Compensating Controls**:
  - Istio sidecar injection (`sidecars.create: true`) ensures mesh-level enforcement
  - Network policies (`networkPolicies.create: true`) provide additional defense in depth restricting ingress to frontend only
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement a gRPC `ServerInterceptor` for action-level authorization as defense in depth beyond the mesh layer.
- **Evidence**: `src/adservice/src/main/java/hipstershop/AdService.java`, `helm-chart/templates/adservice.yaml`, `helm-chart/values.yaml`

### AUTH-Q5: Credential Management
- **Severity**: RISK
- **Finding**: No secrets or credentials are used by the service — ad data is hardcoded in-memory in `AdService.java`. No database connections, no external API calls. No Secrets Manager or Vault integration. No `.env` files or hardcoded credential patterns found.
- **Gap**: No formal credential management framework. While the service currently has no credentials to manage, there is no framework for credential lifecycle management if credentials are introduced.
- **Compensating Controls**:
  - Credential-free architecture eliminates current secret rotation concerns
  - K8s ServiceAccount provides pod identity without explicit credential management
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Maintain credential-free architecture. If credentials are introduced (e.g., external ad provider API keys), use K8s Secrets with external secrets operator or AWS Secrets Manager.
- **Evidence**: `src/adservice/src/main/java/hipstershop/AdService.java`, `src/adservice/build.gradle`

### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK
- **Finding**: An EnvoyFilter rate limiting configuration exists in `istio-manifests/rate-limit.yaml`, but it targets only the `frontend` workload (`workloadSelector.labels.app: frontend`). The adservice has no rate limiting applied — no application-level rate limiting middleware, no Envoy rate limiting on the adservice sidecar, and no API Gateway. K8s resource limits cap CPU/memory but not request rates. The HPA in `kubernetes-manifests/hpa.yaml` provides auto-scaling (1–3 replicas at 70% CPU) but does not prevent request flooding.
- **Gap**: Rate limiting EnvoyFilter exists but only protects frontend, not adservice. A runaway agent loop could overwhelm the adservice directly. No per-caller rate limiting on the adservice.
- **Compensating Controls**:
  - Extend the existing EnvoyFilter pattern to include adservice workload selector
  - Configure agent-side request rate caps in the agent orchestration layer
  - HPA provides elastic capacity as a partial mitigation
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Create an additional EnvoyFilter targeting the adservice workload, or modify the existing `rate-limit.yaml` to include adservice. Configure per-source-principal rate limits using Istio's rate limiting service.
- **Evidence**: `istio-manifests/rate-limit.yaml` (`workloadSelector.labels.app: frontend`), `kubernetes-manifests/hpa.yaml` (adservice HPA), `helm-chart/values.yaml` (`sidecars.create: true`)

---

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: Well-documented gRPC interface in `protos/demo.proto` with `AdService` defining a single `GetAds` RPC. Proto uses versioned package `hipstershop.v1`. Data classification comment marks adservice data as PUBLIC. Implemented in `AdService.java` with `AdServiceImpl` extending generated `AdServiceGrpc.AdServiceImplBase`. Positive finding.
- **Implication**: gRPC interface can be used directly as agent tool binding. Proto enables auto-generated client code in any language.
- **Recommendation**: No remediation needed.
- **Evidence**: `protos/demo.proto`, `src/adservice/src/main/java/hipstershop/AdService.java`

### API-Q2: Machine-Readable API Specification
- **Severity**: INFO
- **Finding**: `protos/demo.proto` is a machine-readable spec. Protobuf is strongly typed with field numbers, data classification comments, and versioned package (`hipstershop.v1`). `protos/buf.yaml` provides proto linting with STANDARD rules and FILE-level breaking change detection. Spec is current with implementation. Positive finding.
- **Implication**: Agent tool definitions can be auto-generated from proto. `buf` tooling enables schema governance.
- **Recommendation**: Consider enabling gRPC server reflection by adding `ProtoReflectionService` to the server builder for runtime schema discovery.
- **Evidence**: `protos/demo.proto`, `protos/buf.yaml`, `src/adservice/build.gradle`

### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The single `GetAds` RPC is read-only, stateless, and inherently idempotent. Ad data is served from an in-memory `ImmutableListMultimap` with no write side effects. Same input always produces the same category-based results (random ads are non-deterministic but have no side effects).
- **Implication**: No idempotency concerns for read-only scope.
- **Recommendation**: No action needed.
- **Evidence**: `src/adservice/src/main/java/hipstershop/AdService.java`

### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: gRPC Protocol Buffers — strongly-typed binary format with explicit types, field numbers, and data classification comments. `AdResponse` contains a repeated `Ad` message with `redirect_url` (string) and `text` (string) fields.
- **Implication**: Protobuf is more structured than JSON. Excellent for agent integration with auto-generated client code. Text fields are LLM-friendly.
- **Recommendation**: No action needed.
- **Evidence**: `protos/demo.proto`

### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit headers on adservice responses. The EnvoyFilter in `istio-manifests/rate-limit.yaml` adds `x-rate-limit-limit` and `x-rate-limit-remaining` headers but only for the frontend workload. Internal ClusterIP service with no API Gateway. K8s resource limits provide implicit capping.
- **Implication**: Agents calling adservice cannot self-throttle based on server-side rate limit signals.
- **Recommendation**: When rate limiting is extended to adservice (see STATE-Q5), configure the EnvoyFilter to include rate limit response headers for agent self-throttling.
- **Evidence**: `istio-manifests/rate-limit.yaml`, `helm-chart/templates/adservice.yaml`

### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: Istio AuthorizationPolicy is enabled (`authorizationPolicies.create: true` in `helm-chart/values.yaml`), providing mTLS-based identity verification. Callers are restricted to the `frontend` service account principal (`cluster.local/ns/<namespace>/sa/frontend`). Istio sidecars are enabled (`sidecars.create: true`), ensuring mTLS is enforced. The gRPC server in `AdService.java` uses `ServerBuilder.forPort(port)` with no application-layer TLS, but the Istio sidecar terminates mTLS before traffic reaches the application — this is the standard Istio pattern. Network policies further restrict ingress to frontend pods only.
- **Implication**: Machine identity is authenticated at the mesh layer via mTLS with per-service principal attribution. This satisfies the core requirement for agent identity verification. Application-layer auth is defense-in-depth, not a prerequisite.
- **Recommendation**: For defense in depth, consider implementing a gRPC `ServerInterceptor` that extracts the Istio peer identity from request headers for application-level logging.
- **Evidence**: `helm-chart/values.yaml` (`authorizationPolicies.create: true`, `sidecars.create: true`, `networkPolicies.create: true`), `helm-chart/templates/adservice.yaml` (AuthorizationPolicy + NetworkPolicy sections), `src/adservice/src/main/java/hipstershop/AdService.java`

### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Archetype-Calibrated**: stateless-utility — downgraded to INFO
- **Finding**: No JWT parsing, no token exchange, no user context headers. No identity context in gRPC calls. However, Istio mTLS provides implicit caller identity at the mesh layer. The `AdRequest` message contains only `context_keys` (product categories) — no user-specific fields.
- **Implication**: For a stateless-utility returning public ad data, identity propagation has minimal security impact — responses are not user-specific and data is classified as PUBLIC. Istio provides caller identity at the mesh layer.
- **Recommendation**: No immediate action. Implement identity propagation if the service evolves to handle user-specific or personalized ad targeting.
- **Evidence**: `src/adservice/src/main/java/hipstershop/AdService.java`, `protos/demo.proto` (AdRequest message), `helm-chart/values.yaml`

### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO (downgraded from RISK due to stateless-utility serving public data)
- **Finding**: No audit logging exists at the application layer. Log4j2 logs operational messages only (startup, ad request context words, errors). No principal attribution in any log output. Logs are ephemeral container stdout with no immutable storage configuration. OpenTelemetry tracing is enabled (`tracing: true` in `values.yaml`) and the OTel Collector is deployed (`opentelemetryCollector.create: true`), providing request-level trace context. However, traces are not audit-grade — they lack principal attribution.
- **Implication**: For a read-only agent accessing public ad data, the audit risk is low. OpenTelemetry traces provide request correlation as a partial audit signal. Full audit logging becomes important if agent scope expands to write-enabled.
- **Recommendation**: Add structured audit logging with caller identity (extracted from Istio mTLS peer identity) when agent scope expands. Forward to immutable store.
- **Evidence**: `src/adservice/src/main/java/hipstershop/AdService.java` (Log4j2 logger), `helm-chart/values.yaml` (`tracing: true`, `opentelemetryCollector.create: true`)

### AUTH-Q7: Agent Identity Suspension
- **Severity**: INFO
- **Finding**: Istio AuthorizationPolicy is enabled, providing a mechanism to deny specific service accounts by updating the policy. NetworkPolicies are enabled (`networkPolicies.create: true`), providing an additional isolation mechanism. However, there is no automated suspension mechanism — policy changes require Helm value updates or manual kubectl edits. No API key revocation, no service account disable endpoint.
- **Implication**: For a read-only agent accessing public data, the urgency of automated suspension is lower. Manual AuthorizationPolicy updates provide a workable suspension path for pilot scope.
- **Recommendation**: Implement automated suspension via AuthorizationPolicy updates triggered by anomaly detection as agent scope expands.
- **Evidence**: `helm-chart/templates/adservice.yaml` (AuthorizationPolicy), `helm-chart/values.yaml` (`authorizationPolicies.create: true`, `networkPolicies.create: true`)

### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO (downgraded from RISK due to stateless-utility with no state mutations)
- **Finding**: Service is stateless — reads from an in-memory `ImmutableListMultimap` of hardcoded ad data. No multi-step write operations. No state mutations to compensate. No database, no cache writes, no external state.
- **Implication**: No compensation mechanisms needed. Stateless architecture eliminates rollback concerns entirely.
- **Recommendation**: Maintain stateless architecture. Implement compensation if write operations or external state are added.
- **Evidence**: `src/adservice/src/main/java/hipstershop/AdService.java`

### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No writes, deletes, or modifications. Minimal blast radius. Read-only operations on public ad data served from in-memory store.
- **Implication**: Transaction limits not applicable for read-only operations on public data.
- **Recommendation**: Implement if write operations are added.
- **Evidence**: `src/adservice/src/main/java/hipstershop/AdService.java`

### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO
- **Finding**: Handles public ad data only — redirect URLs and ad text. No PII, PHI, or financial data. Proto includes data classification comment: "Data Classification: PUBLIC (ad categories and text are non-sensitive)". `DATA_CLASSIFICATION.md` at repo root classifies adservice as PUBLIC with no sensitive fields. The `AdRequest` contains only `context_keys` (product category strings). The `AdResponse` contains only `redirect_url` and `text` — both public.
- **Implication**: No data classification controls needed. No PII exposure risk. Positive finding.
- **Recommendation**: No action needed. Maintain classification documentation as service evolves.
- **Evidence**: `protos/demo.proto` (AdService data classification comment), `DATA_CLASSIFICATION.md` (adservice: PUBLIC, no sensitive fields), `src/adservice/src/main/java/hipstershop/AdService.java`

### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO (downgraded from RISK due to public, non-regulated data)
- **Finding**: Ad data is hardcoded in-memory — static redirect URLs and promotional text. No regulated data. No PII. No GDPR/LGPD/HIPAA applicability. `DATA_CLASSIFICATION.md` confirms PUBLIC classification with no residency restrictions.
- **Implication**: No data residency concerns. Public ad text has no jurisdictional restrictions. An agent sending ad data to an LLM in any region creates no compliance risk.
- **Recommendation**: No action needed. Reassess if personalized or user-specific ad data is introduced.
- **Evidence**: `DATA_CLASSIFICATION.md`, `protos/demo.proto`, `src/adservice/src/main/java/hipstershop/AdService.java`

### DATA-Q6: PII Redaction in Logs
- **Severity**: INFO
- **Finding**: Logs contain operational messages only — startup info, ad request context words, and error status. No request/response payloads logged. No PII in data model. No PII leakage risk. Log4j2 logger outputs to stdout.
- **Implication**: No PII redaction needed. Positive finding.
- **Recommendation**: No action needed.
- **Evidence**: `src/adservice/src/main/java/hipstershop/AdService.java`

### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: INFO
- **Finding**: Proto uses versioned package `hipstershop.v1`. `protos/buf.yaml` exists with STANDARD lint rules and FILE-level breaking change detection configured. Proto defines typed schemas with data classification comments and `google.protobuf.Timestamp` imports. Breaking change detection (`buf breaking`) is configured in `buf.yaml` but not yet integrated into CI pipeline.
- **Implication**: Schema versioning is established. Proto versioning enables safe evolution. `buf` tooling provides a path to automated breaking change detection. The gap is CI integration, not tooling.
- **Recommendation**: Add `buf breaking` to CI pipeline to complete the contract testing story (tracked under ENG-Q2).
- **Evidence**: `protos/demo.proto` (`package hipstershop.v1`), `protos/buf.yaml`

### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: INFO
- **Finding**: OpenTelemetry tracing is enabled (`tracing: true` in `helm-chart/values.yaml`). OpenTelemetry Collector is deployed (`opentelemetryCollector.create: true`). Metrics collection is enabled (`metrics: true`). The adservice Java code has `initTracing()` and `initStats()` methods that initialize OpenTelemetry instrumentation. Log4j2 provides structured logging. The `grpc-census` dependency in `build.gradle` provides gRPC metrics integration.
- **Implication**: Distributed tracing is operational. Trace context enables end-to-end request correlation across services. The remaining gap (no trace_id in Log4j2 log entries) is minor — OpenTelemetry trace IDs serve the same purpose.
- **Recommendation**: Add trace_id to Log4j2 log pattern for log-to-trace correlation. This is a minor enhancement, not a gap.
- **Evidence**: `helm-chart/values.yaml` (`tracing: true`, `opentelemetryCollector.create: true`, `metrics: true`), `src/adservice/src/main/java/hipstershop/AdService.java` (`initTracing()`, `initStats()`), `src/adservice/build.gradle` (`grpc-census` dependency)

### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: INFO
- **Finding**: Prometheus alerting rules are configured in `kubernetes-manifests/monitoring-alerts.yaml` with three alert groups: (1) `HighGrpcErrorRate` at 1% threshold for 5m, (2) `CriticalGrpcErrorRate` at 5% threshold for 2m, (3) `HighP95Latency` at 500ms threshold for 5m, and (4) `ServiceDown` for availability. Alerts apply to all gRPC services including adservice. Metrics collection is enabled (`metrics: true`). K8s health probes (liveness + readiness) provide pod availability monitoring. HPA is configured for auto-scaling.
- **Implication**: Alerting infrastructure is comprehensive. Service degradation will be detected before agents cascade failures. Both error rate and latency thresholds are configured with appropriate severity levels.
- **Recommendation**: Tune alert thresholds based on agent traffic patterns during pilot. Consider adding adservice-specific alert rules if agent traffic patterns differ from human traffic.
- **Evidence**: `kubernetes-manifests/monitoring-alerts.yaml`, `helm-chart/values.yaml` (`metrics: true`), `helm-chart/templates/adservice.yaml` (health probes), `kubernetes-manifests/hpa.yaml` (adservice HPA)

### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: INFO
- **Finding**: Comprehensive IaC coverage: Helm chart defines Deployment, Service, ServiceAccount, NetworkPolicy, Sidecar, and AuthorizationPolicy for adservice. All security policies are enabled in IaC (`authorizationPolicies.create: true`, `networkPolicies.create: true`, `sidecars.create: true`). K8s manifests, Kustomize overlays, and Terraform exist. CODEOWNERS enforces peer review. GitHub Actions CI on PRs (`ci-pr.yaml`). Helm chart CI (`helm-chart-ci.yaml`). No drift detection configured.
- **Implication**: Infrastructure governance is strong — IaC coverage is comprehensive, all security controls are enabled, and peer review is enforced. The drift detection gap is minor for a K8s-native deployment where Helm reconciliation provides implicit drift correction on deploy.
- **Recommendation**: Implement drift detection for completeness. Consider ArgoCD or Flux for GitOps-based continuous reconciliation.
- **Evidence**: `helm-chart/templates/adservice.yaml`, `helm-chart/values.yaml`, `.github/CODEOWNERS`, `.github/workflows/ci-pr.yaml`, `.github/workflows/helm-chart-ci.yaml`

### HITL-Q3: Sandbox/Staging Environment
- **Severity**: INFO
- **Finding**: Skaffold provides local development with Docker build. Cloud Build deploys to GKE staging cluster. CI deploys per-PR to ephemeral namespaces. Docker Compose not available but Skaffold + minikube provides local testing. No persistent agent-specific testing environment, but the existing CI infrastructure provides production-equivalent deployment for testing.
- **Implication**: For a read-only agent accessing a stateless-utility with public data, the risk of testing in production is low. Existing CI infrastructure provides adequate testing paths.
- **Recommendation**: Create persistent staging namespace for agent integration testing if agent scope expands.
- **Evidence**: `cloudbuild.yaml`, `src/adservice/Dockerfile`, `.github/workflows/ci-pr.yaml`

### ENG-Q4: API Test Coverage
- **Severity**: INFO
- **Finding**: No adservice-specific unit or integration tests found. The `build.gradle` has no test dependencies or test source sets. CI smoke test via loadgenerator exercises the `GetAds` RPC indirectly. Simple service logic (category lookup in static map, random ad selection) reduces untested-code risk.
- **Implication**: For a stateless-utility with simple in-memory lookup logic, the risk of zero test coverage is lower than for stateful services. Still recommended for regression safety.
- **Recommendation**: Add unit tests for `getAdsByCategory` and `getRandomAds` methods. Add gRPC integration tests for the `GetAds` RPC. Include in CI.
- **Evidence**: `src/adservice/build.gradle`, `src/adservice/src/main/java/hipstershop/AdService.java`, `.github/workflows/ci-pr.yaml`

### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No quality metrics. 7 static ad entries across 6 categories hardcoded in `createAdsMap()`. Quality is fixed at build time — no runtime data ingestion, no external data sources, no data degradation risk.
- **Implication**: Quality is static and deterministic. No runtime degradation risk. Agent will always receive well-formed ad data.
- **Recommendation**: Add validation that ad URLs are valid and text is non-empty if dynamic ad loading is introduced.
- **Evidence**: `src/adservice/src/main/java/hipstershop/AdService.java` (`createAdsMap()`)

### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Clear semantic names: `context_keys`, `redirect_url`, `text`, `ads`. Detailed comments in proto ("url to redirect to when an ad is clicked", "short advertisement text to display"). No abbreviations or legacy codes.
- **Implication**: LLMs can interpret fields directly. No translation or data dictionary needed.
- **Recommendation**: No action needed.
- **Evidence**: `protos/demo.proto`

### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal data catalog. Proto file serves as informal documentation with data classification comments. `DATA_CLASSIFICATION.md` provides service-level data ownership and classification taxonomy. Self-describing proto with semantic field names.
- **Implication**: Sufficient for single-purpose utility service. `DATA_CLASSIFICATION.md` provides portfolio-level data governance context.
- **Recommendation**: Register in organization API catalog if part of larger data mesh.
- **Evidence**: `protos/demo.proto`, `DATA_CLASSIFICATION.md`

### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics. Operational logging and OpenTelemetry metrics provide infrastructure-level visibility. No ad impression or click-through rate metrics.
- **Implication**: No business outcome monitoring. Operational metrics may suffice initially for a utility service. Business metrics (ad impressions, CTR) would be valuable for measuring agent interaction quality.
- **Recommendation**: Publish metrics for ad impressions by category and click-through rates if business analytics are needed.
- **Evidence**: `src/adservice/src/main/java/hipstershop/AdService.java`

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: Well-documented gRPC interface in `protos/demo.proto` with `AdService` defining a single `GetAds` RPC. Proto uses versioned package `hipstershop.v1`. Data classification comment marks adservice data as PUBLIC. Implemented in `AdService.java` with `AdServiceImpl` extending generated `AdServiceGrpc.AdServiceImplBase`. Positive finding.
- **Gap**: None — BLOCKER criteria satisfied.
- **Recommendation**: No remediation needed.
- **Evidence**: `protos/demo.proto`, `src/adservice/src/main/java/hipstershop/AdService.java`

#### API-Q2: Machine-Readable API Specification
- **Severity**: INFO
- **Finding**: `protos/demo.proto` is a machine-readable spec. Protobuf is strongly typed with field numbers, data classification comments, and versioned package (`hipstershop.v1`). `protos/buf.yaml` provides proto linting with STANDARD rules and FILE-level breaking change detection. Current with implementation. Positive finding.
- **Gap**: None.
- **Recommendation**: Consider enabling gRPC server reflection by adding `ProtoReflectionService` to the server builder for runtime schema discovery.
- **Evidence**: `protos/demo.proto`, `protos/buf.yaml`, `src/adservice/build.gradle`

#### API-Q3: Structured Error Responses
- **Severity**: RISK
- **Finding**: The `getAds` method catches `StatusRuntimeException` and forwards it via `responseObserver.onError(e)`. gRPC provides standard status codes but no structured error body — no error code taxonomy, no retryable boolean, no rich error model (`com.google.rpc.ErrorInfo`).
- **Gap**: Agents cannot distinguish retriable from terminal errors based on gRPC status alone.
- **Recommendation**: Implement gRPC rich error model using `com.google.rpc.ErrorInfo`.
- **Evidence**: `src/adservice/src/main/java/hipstershop/AdService.java`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The single `GetAds` RPC is read-only, stateless, and inherently idempotent. Ad data served from in-memory `ImmutableListMultimap` with no write side effects.
- **Gap**: N/A — no write operations.
- **Recommendation**: No action needed.
- **Evidence**: `src/adservice/src/main/java/hipstershop/AdService.java`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: gRPC Protocol Buffers — strongly-typed binary format with explicit types, field numbers, and data classification comments. `AdResponse` contains repeated `Ad` messages with `redirect_url` and `text` string fields.
- **Gap**: None.
- **Recommendation**: No action needed.
- **Evidence**: `protos/demo.proto`

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
- **Finding**: No rate limit headers on adservice responses. EnvoyFilter in `istio-manifests/rate-limit.yaml` adds `x-rate-limit-limit` and `x-rate-limit-remaining` headers but only for frontend. Internal ClusterIP service with no API Gateway.
- **Gap**: Agents cannot self-throttle based on server-side rate limit signals.
- **Recommendation**: Extend EnvoyFilter rate limit headers to adservice when rate limiting is applied (see STATE-Q5).
- **Evidence**: `istio-manifests/rate-limit.yaml`, `helm-chart/templates/adservice.yaml`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: Istio AuthorizationPolicy is enabled (`authorizationPolicies.create: true`), providing mTLS-based identity verification. Callers restricted to `frontend` service account principal. Istio sidecars enabled (`sidecars.create: true`). Network policies enabled (`networkPolicies.create: true`). The gRPC server uses `ServerBuilder.forPort(port)` with no application-layer TLS, but Istio sidecar terminates mTLS before traffic reaches the application — standard Istio pattern.
- **Gap**: None — mesh-level mTLS with per-service AuthorizationPolicy satisfies machine identity authentication.
- **Recommendation**: For defense in depth, implement a gRPC `ServerInterceptor` that extracts Istio peer identity from request headers.
- **Evidence**: `helm-chart/values.yaml`, `helm-chart/templates/adservice.yaml`, `src/adservice/src/main/java/hipstershop/AdService.java`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicy restricts callers to `frontend` service account on `/hipstershop.AdService/GetAds`. No agent-specific service accounts. No per-caller differentiation.
- **Gap**: No agent-specific service accounts with tailored permissions.
- **Recommendation**: Create agent-specific service accounts with per-RPC AuthorizationPolicy rules.
- **Evidence**: `helm-chart/templates/adservice.yaml`, `helm-chart/values.yaml`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicy defines per-path rules. No application-layer action-level authorization — gRPC server accepts all calls that reach it.
- **Gap**: No application-layer authorization. Mesh bypass exposes all RPCs.
- **Recommendation**: Implement gRPC `ServerInterceptor` for action-level authorization as defense in depth.
- **Evidence**: `src/adservice/src/main/java/hipstershop/AdService.java`, `helm-chart/templates/adservice.yaml`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Archetype-Calibrated**: stateless-utility — downgraded to INFO
- **Finding**: No JWT parsing, token exchange, or user context headers. `AdRequest` contains only `context_keys` — no user-specific fields. Istio mTLS provides implicit caller identity at mesh layer.
- **Gap**: No application-level identity propagation. Minimal impact for stateless-utility returning public data.
- **Recommendation**: No immediate action. Implement if service evolves to handle personalized ads.
- **Evidence**: `src/adservice/src/main/java/hipstershop/AdService.java`, `protos/demo.proto`, `helm-chart/values.yaml`

#### AUTH-Q5: Credential Management
- **Severity**: RISK
- **Finding**: No secrets or credentials used. Ad data hardcoded in-memory. No database connections. No Secrets Manager or Vault integration.
- **Gap**: No credential management framework if credentials are introduced.
- **Recommendation**: Maintain credential-free architecture. Adopt K8s external secrets operator if credentials are needed.
- **Evidence**: `src/adservice/src/main/java/hipstershop/AdService.java`, `src/adservice/build.gradle`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No audit logging. Log4j2 operational messages only. No principal attribution. OpenTelemetry tracing enabled (`tracing: true`) with OTel Collector deployed — provides request correlation but not audit-grade attribution. Logs are ephemeral container stdout.
- **Gap**: No immutable audit trail. Acceptable for read-only agent accessing public data.
- **Recommendation**: Add structured audit logging with caller identity when agent scope expands.
- **Evidence**: `src/adservice/src/main/java/hipstershop/AdService.java`, `helm-chart/values.yaml`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: INFO
- **Finding**: Istio AuthorizationPolicy and NetworkPolicy provide mechanisms to deny specific service accounts. No automated suspension — requires manual policy changes.
- **Gap**: No automated or rapid suspension mechanism. Acceptable for read-only pilot scope.
- **Recommendation**: Implement automated suspension via AuthorizationPolicy updates triggered by anomaly detection.
- **Evidence**: `helm-chart/templates/adservice.yaml`, `helm-chart/values.yaml`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Stateless service. No write operations, no transactions, no state mutations. In-memory read-only data.
- **Gap**: No compensation mechanisms — but no state mutations exist.
- **Recommendation**: Maintain stateless architecture. Implement compensation if write operations added.
- **Evidence**: `src/adservice/src/main/java/hipstershop/AdService.java`

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
- **Finding**: EnvoyFilter rate limiting exists in `istio-manifests/rate-limit.yaml` but targets only the `frontend` workload. No rate limiting on adservice. No application-level rate limiting. HPA provides auto-scaling (1–3 replicas) but does not prevent request flooding.
- **Gap**: Rate limiting exists but does not cover adservice. Runaway agent loop risk.
- **Recommendation**: Extend EnvoyFilter to include adservice workload or add gRPC rate limiting interceptor.
- **Evidence**: `istio-manifests/rate-limit.yaml`, `kubernetes-manifests/hpa.yaml`, `helm-chart/values.yaml`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No writes, deletes, or modifications. Minimal blast radius. Read-only operations on public ad data.
- **Gap**: None for read-only scope.
- **Recommendation**: Implement if write operations added.
- **Evidence**: `src/adservice/src/main/java/hipstershop/AdService.java`

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
- **Severity**: INFO
- **Finding**: Skaffold local dev. Cloud Build deploys to GKE staging. CI per-PR ephemeral namespaces. No persistent agent-specific testing environment, but existing CI infrastructure provides production-equivalent deployment.
- **Gap**: No dedicated agent testing environment. Acceptable for read-only pilot on stateless-utility with public data.
- **Recommendation**: Create persistent staging namespace for agent integration testing if scope expands.
- **Evidence**: `cloudbuild.yaml`, `src/adservice/Dockerfile`, `.github/workflows/ci-pr.yaml`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO
- **Finding**: Public ad data only. No PII/PHI/financial data. Proto includes data classification comment: "Data Classification: PUBLIC". `DATA_CLASSIFICATION.md` classifies adservice as PUBLIC with no sensitive fields.
- **Gap**: None — public data with no sensitivity classification required.
- **Recommendation**: Maintain classification documentation as service evolves.
- **Evidence**: `protos/demo.proto`, `DATA_CLASSIFICATION.md`, `src/adservice/src/main/java/hipstershop/AdService.java`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Hardcoded in-memory ad data. No regulated data. No PII. `DATA_CLASSIFICATION.md` confirms PUBLIC classification. No jurisdictional restrictions.
- **Gap**: None for public, non-regulated data.
- **Recommendation**: Reassess if personalized or user-specific ad data is introduced.
- **Evidence**: `DATA_CLASSIFICATION.md`, `protos/demo.proto`, `src/adservice/src/main/java/hipstershop/AdService.java`

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
- **Finding**: Logs contain operational messages only. No request/response payloads logged. No PII in data model. No PII leakage risk.
- **Gap**: None.
- **Recommendation**: No action needed.
- **Evidence**: `src/adservice/src/main/java/hipstershop/AdService.java`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No quality metrics. 7 static ad entries across 6 categories. Quality fixed at build time. No runtime data degradation risk.
- **Gap**: No quality monitoring, but static data has fixed quality characteristics.
- **Recommendation**: Add validation if dynamic ad loading is introduced.
- **Evidence**: `src/adservice/src/main/java/hipstershop/AdService.java`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: INFO
- **Finding**: Proto uses versioned package `hipstershop.v1`. `protos/buf.yaml` with STANDARD lint rules and FILE-level breaking change detection. Typed schemas with data classification comments. `buf breaking` configured but not yet in CI.
- **Gap**: `buf breaking` not in CI (tracked under ENG-Q2).
- **Recommendation**: Add `buf breaking` to CI pipeline.
- **Evidence**: `protos/demo.proto`, `protos/buf.yaml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Clear semantic names: `context_keys`, `redirect_url`, `text`, `ads`. Detailed comments in proto. No abbreviations or legacy codes.
- **Gap**: None.
- **Recommendation**: No action needed.
- **Evidence**: `protos/demo.proto`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal catalog. Proto file with data classification comments. `DATA_CLASSIFICATION.md` provides service-level data ownership taxonomy.
- **Gap**: No formal catalog. Sufficient for single-purpose utility service.
- **Recommendation**: Register in organization API catalog if part of larger data mesh.
- **Evidence**: `protos/demo.proto`, `DATA_CLASSIFICATION.md`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: INFO
- **Finding**: OpenTelemetry tracing enabled (`tracing: true`). OTel Collector deployed (`opentelemetryCollector.create: true`). Metrics enabled (`metrics: true`). `initTracing()` and `initStats()` in AdService.java. Log4j2 structured logging. `grpc-census` dependency for gRPC metrics.
- **Gap**: No trace_id in Log4j2 log entries (minor — OpenTelemetry trace IDs serve the same purpose).
- **Recommendation**: Add trace_id to Log4j2 log pattern for log-to-trace correlation.
- **Evidence**: `helm-chart/values.yaml`, `src/adservice/src/main/java/hipstershop/AdService.java`, `src/adservice/build.gradle`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: INFO
- **Finding**: Prometheus alerting rules in `kubernetes-manifests/monitoring-alerts.yaml`: `HighGrpcErrorRate` (1%, 5m), `CriticalGrpcErrorRate` (5%, 2m), `HighP95Latency` (500ms, 5m), `ServiceDown`. Metrics enabled. K8s health probes. HPA configured.
- **Gap**: None — alerting infrastructure is comprehensive.
- **Recommendation**: Tune thresholds based on agent traffic patterns during pilot.
- **Evidence**: `kubernetes-manifests/monitoring-alerts.yaml`, `helm-chart/values.yaml`, `helm-chart/templates/adservice.yaml`, `kubernetes-manifests/hpa.yaml`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics. Operational logging and OpenTelemetry metrics provide infrastructure-level visibility.
- **Gap**: No business outcome monitoring.
- **Recommendation**: Publish ad impression and click-through rate metrics if business analytics are needed.
- **Evidence**: `src/adservice/src/main/java/hipstershop/AdService.java`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: INFO
- **Finding**: Comprehensive IaC: Helm chart defines Deployment, Service, ServiceAccount, NetworkPolicy, Sidecar, AuthorizationPolicy. All security policies enabled (`authorizationPolicies.create: true`, `networkPolicies.create: true`, `sidecars.create: true`). CODEOWNERS enforces peer review. GitHub Actions CI. No drift detection.
- **Gap**: Drift detection missing (minor for K8s-native deployment with Helm reconciliation).
- **Recommendation**: Implement drift detection or GitOps (ArgoCD/Flux).
- **Evidence**: `helm-chart/templates/adservice.yaml`, `helm-chart/values.yaml`, `.github/CODEOWNERS`, `.github/workflows/ci-pr.yaml`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: INFO
- **Finding**: CI exists (Cloud Build + Skaffold + GitHub Actions). Proto versioned (`hipstershop.v1`). `protos/buf.yaml` with STANDARD lint and FILE-level breaking change detection configured. However, `buf breaking` is not yet integrated into CI pipeline. No adservice-specific contract tests. Protobuf wire compatibility provides implicit backward compatibility for additive changes.
- **Gap**: `buf breaking` not in CI pipeline. No service-specific contract tests.
- **Recommendation**: Add `buf breaking` to CI pipeline. Add AdService-specific contract tests.
- **Evidence**: `cloudbuild.yaml`, `.github/workflows/ci-pr.yaml`, `protos/buf.yaml`, `protos/demo.proto`

#### ENG-Q3: Rollback Capability
- **Severity**: INFO
- **Finding**: K8s Deployment with rollout history. Skaffold deployment. Manual rollback via `kubectl rollout undo`. No automated rollback triggers. No canary deployment. Liveness/readiness probes prevent traffic to unhealthy pods. Monitoring alerts (now configured) can trigger manual rollback faster.
- **Gap**: No automated rollback on service degradation. Manual rollback only.
- **Recommendation**: Configure automated rollback triggers using Flagger or Argo Rollouts with canary analysis.
- **Evidence**: `cloudbuild.yaml`, `helm-chart/templates/adservice.yaml`

#### ENG-Q4: API Test Coverage
- **Severity**: INFO
- **Finding**: No adservice-specific tests. `build.gradle` has no test dependencies. CI smoke test via loadgenerator exercises `GetAds` indirectly. Simple in-memory lookup logic reduces untested-code risk.
- **Gap**: Zero test coverage. Lower risk for stateless-utility with simple logic.
- **Recommendation**: Add unit tests for `getAdsByCategory` and `getRandomAds`. Add gRPC integration tests.
- **Evidence**: `src/adservice/build.gradle`, `src/adservice/src/main/java/hipstershop/AdService.java`

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
| `helm-chart/templates/adservice.yaml` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q7, API-Q8, OBS-Q2, ENG-Q1, ENG-Q3, STATE-Q5 |
| `helm-chart/values.yaml` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q6, AUTH-Q7, OBS-Q1, OBS-Q2, ENG-Q1, STATE-Q5 |
| `kubernetes-manifests/hpa.yaml` | STATE-Q5, OBS-Q2 |
| `kubernetes-manifests/monitoring-alerts.yaml` | OBS-Q2 |
| `istio-manifests/rate-limit.yaml` | STATE-Q5, API-Q8 |

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `src/adservice/src/main/java/hipstershop/AdService.java` | API-Q1, API-Q3, API-Q4, AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q6, STATE-Q1, STATE-Q6, DATA-Q1, DATA-Q2, DATA-Q6, DATA-Q7, OBS-Q1, OBS-Q3, ENG-Q4, HITL-Q3 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `protos/demo.proto` | API-Q1, API-Q2, API-Q4, API-Q5, AUTH-Q4, DATA-Q1, DATA-Q2, DISC-Q1, DISC-Q2, DISC-Q3, ENG-Q2 |
| `protos/buf.yaml` | API-Q2, DISC-Q1, ENG-Q2 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `cloudbuild.yaml` | HITL-Q3, ENG-Q1, ENG-Q2, ENG-Q3 |
| `.github/workflows/ci-pr.yaml` | HITL-Q3, ENG-Q1, ENG-Q2, ENG-Q4 |
| `.github/workflows/helm-chart-ci.yaml` | ENG-Q1 |
| `.github/CODEOWNERS` | ENG-Q1 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `src/adservice/Dockerfile` | HITL-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `src/adservice/build.gradle` | API-Q2, AUTH-Q5, OBS-Q1, ENG-Q4 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `DATA_CLASSIFICATION.md` | DATA-Q1, DATA-Q2, DISC-Q3 |
