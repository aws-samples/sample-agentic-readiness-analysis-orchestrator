# Agentic Readiness Assessment Report

**Target**: services/microservices-demo/src/productcatalogservice
**Date**: 2026-04-16
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Service Archetype**: stateless-utility (user-provided)
**Agent Scope**: read-only
**Priority**: P0
**Tags**: go, grpc, catalog
**Context**: Go gRPC service serving product catalog from a JSON file.

---

## Readiness Profile: Pilot-Ready

**BLOCKERs**: 0 | **RISKs**: 5 | **INFOs**: 27

Supervised pilot with: (1) human approval gates on irreversible actions, (2) agent limited to low-blast-radius operations, (3) compensating controls for each open RISK, (4) remediation timeline before expanding scope.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 0 |
| RISK | 5 |
| INFO | 27 |
| N/A | 0 |
| Not Evaluated (extended) | 11 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 8
**Extended Questions Not Triggered**: 11
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: stateless-utility (user-provided)

---

## BLOCKERs — Must Resolve Before Agent Deployment

No BLOCKERs identified.

---

## RISKs — Proceed with Compensating Controls

### AUTH-Q5: Credential Management
- **Severity**: RISK
- **Finding**: No secrets management system (AWS Secrets Manager, HashiCorp Vault) is configured. The service currently uses no credentials for its default JSON-file mode. However, `catalog_loader.go` contains an AlloyDB integration path that uses Google Cloud Secret Manager (`cloud.google.com/go/secretmanager`) to retrieve database passwords at runtime. No `.env` files committed. No hardcoded credentials in source code. Workload Identity is used for GCP library authentication.
- **Gap**: No formal credential management framework for agent API keys or service credentials. The AlloyDB path uses Secret Manager, but the default deployment path has no secrets infrastructure.
- **Compensating Controls**:
  - Credential-free architecture (JSON file mode) eliminates current secret rotation concerns
  - Workload Identity for GCP libraries avoids hardcoded credentials
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Maintain credential-free architecture for default mode. If agent-specific API keys are introduced, use K8s Secrets with external secrets operator or AWS Secrets Manager. Ensure Secret Manager integration in AlloyDB path includes rotation.
- **Evidence**: `src/productcatalogservice/catalog_loader.go` (Secret Manager import), `src/productcatalogservice/server.go`, `go.mod`

### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicy is enabled, providing a mechanism to deny specific service accounts by updating the policy. NetworkPolicies are enabled. However, there is no automated suspension mechanism — policy changes require Helm value updates or manual kubectl edits. No API key revocation endpoint, no service account disable mechanism.
- **Gap**: No automated or rapid suspension mechanism. Isolating a misbehaving agent requires manual AuthorizationPolicy or NetworkPolicy changes.
- **Compensating Controls**:
  - Istio AuthorizationPolicy can be updated to deny specific service accounts (manual process)
  - K8s NetworkPolicy (enabled) can block specific pods as emergency measure
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement automated suspension via AuthorizationPolicy updates triggered by anomaly detection. Consider an operator or webhook that can instantly deny a service account.
- **Evidence**: `helm-chart/templates/productcatalogservice.yaml` (AuthorizationPolicy section), `helm-chart/values.yaml` (`authorizationPolicies.create: true`, `networkPolicies.create: true`)

### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK
- **Finding**: Skaffold provides local development with Docker build. Cloud Build deploys via Skaffold. No persistent agent testing environment with production-equivalent data shape. The `products.json` file provides a static seed dataset suitable for testing.
- **Gap**: No dedicated agent testing environment. No persistent staging namespace for agent integration testing.
- **Compensating Controls**:
  - Use Skaffold for local instance with Docker build for isolated testing
  - `products.json` provides deterministic test data
- **Remediation Timeline**: 30 days
- **Recommendation**: Create persistent staging namespace for agent integration testing with production-equivalent configuration. Use `products.json` as seed data.
- **Evidence**: `skaffold.yaml`, `src/productcatalogservice/Dockerfile`, `src/productcatalogservice/products.json`, `cloudbuild.yaml`

### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK
- **Finding**: CI exists (Cloud Build + Skaffold + GitHub Actions). Proto uses versioned package (`hipstershop.v1`) and `buf.yaml` exists for proto linting. However, no `buf breaking` is configured in CI for breaking change detection. No productcatalogservice-specific contract tests. Smoke testing via loadgenerator only.
- **Gap**: No automated breaking change detection in CI pipeline. No service-specific API contract tests.
- **Compensating Controls**:
  - Protobuf wire compatibility provides implicit backward compatibility for additive changes
  - `buf.yaml` enables linting but breaking change detection requires `buf breaking` in CI
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `buf breaking` to CI pipeline. Add ProductCatalogService-specific contract tests validating input/output schemas for `ListProducts`, `GetProduct`, and `SearchProducts`.
- **Evidence**: `cloudbuild.yaml`, `.github/workflows/`, `buf.yaml`, `protos/demo.proto`

### ENG-Q3: Rollback Capability
- **Severity**: RISK
- **Finding**: K8s Deployment with rollout history. Skaffold deployment. Liveness and readiness probes configured (gRPC health check on port 3550). No automated rollback triggers. Manual rollback via `kubectl rollout undo` only. No canary deployment, no Flagger, no Argo Rollouts.
- **Gap**: No automated rollback on service degradation. Manual rollback only.
- **Compensating Controls**:
  - K8s rollout history enables manual rollback within minutes
  - Liveness/readiness probes prevent traffic to unhealthy pods
  - Monitoring alerts (configured) can trigger manual rollback faster
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure automated rollback triggers using Flagger or Argo Rollouts with canary analysis.
- **Evidence**: `kubernetes-manifests/productcatalogservice.yaml`, `helm-chart/templates/productcatalogservice.yaml`, `skaffold.yaml`

---

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: Well-documented gRPC interface in `protos/demo.proto` with `ProductCatalogService` defining `ListProducts`, `GetProduct`, and `SearchProducts` RPCs. Proto uses versioned package `hipstershop.v1`. Implemented in Go (`product_catalog.go`). All three RPCs are read-only. Positive finding.
- **Implication**: gRPC interface can be used directly as agent tool binding. Proto enables auto-generated client code in any language.
- **Recommendation**: No remediation needed.
- **Evidence**: `protos/demo.proto`, `src/productcatalogservice/product_catalog.go`

### API-Q2: Machine-Readable API Specification
- **Severity**: INFO
- **Finding**: `protos/demo.proto` is a machine-readable spec. Protobuf is strongly typed with field numbers, data classification comments (`Data Classification: PUBLIC`), and timestamp fields (`created_at`, `updated_at`). `buf.yaml` provides proto linting. Spec is current with implementation. Positive finding.
- **Implication**: Agent tool definitions can be auto-generated from proto. `buf` tooling enables schema governance.
- **Recommendation**: Consider enabling gRPC server reflection for runtime schema discovery.
- **Evidence**: `protos/demo.proto`, `buf.yaml`, `src/productcatalogservice/product_catalog.go`

### API-Q3: Structured Error Responses
- **Severity**: INFO
- **Finding**: The `GetProduct` function in `product_catalog.go` returns proper gRPC status codes: `status.Errorf(codes.NotFound, "no product with ID %s", req.Id)` for missing products. The `SearchProducts` function returns an empty result set (not an error) for no matches. `ListProducts` returns the full catalog. gRPC status codes provide structured, machine-readable error classification (NOT_FOUND, UNIMPLEMENTED for health Watch). For a stateless-utility with only read operations, this error handling is sufficient.
- **Implication**: Agents can distinguish NOT_FOUND from server errors via gRPC status codes. Positive finding for a read-only service.
- **Recommendation**: Consider adding a gRPC interceptor for consistent error metadata (retryable boolean) across all RPCs.
- **Evidence**: `src/productcatalogservice/product_catalog.go` (GetProduct with codes.NotFound)

### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: All three RPCs (`ListProducts`, `GetProduct`, `SearchProducts`) are read-only, stateless, and inherently idempotent. No write operations exist. Same input always produces same output (deterministic reads from static JSON or AlloyDB).
- **Implication**: No idempotency concerns for read-only scope.
- **Recommendation**: No action needed.
- **Evidence**: `src/productcatalogservice/product_catalog.go`, `src/productcatalogservice/products.json`

### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: Istio AuthorizationPolicy is enabled (`authorizationPolicies.create: true` in `helm-chart/values.yaml`), providing service-mesh-level identity verification using mTLS between pods. Callers are restricted to `frontend`, `checkoutservice`, and `recommendationservice` service accounts. Istio sidecars are enabled (`sidecars.create: true`), ensuring mTLS is enforced. The gRPC server in `server.go` uses `grpc.NewServer()` with OTel stats handler at the application layer — Istio sidecar terminates mTLS before traffic reaches the application (standard Istio pattern).
- **Implication**: Machine identity is authenticated at the mesh layer via mTLS with per-service principal attribution. This satisfies the core requirement for agent identity verification. Application-layer auth is defense-in-depth, not a prerequisite.
- **Recommendation**: For defense in depth, consider implementing a gRPC interceptor that extracts the Istio peer identity from request headers for application-level logging.
- **Evidence**: `helm-chart/values.yaml` (`authorizationPolicies.create: true`, `sidecars.create: true`), `helm-chart/templates/productcatalogservice.yaml` (AuthorizationPolicy section), `src/productcatalogservice/server.go`

### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: INFO
- **Finding**: Istio AuthorizationPolicy restricts callers to `frontend`, `checkoutservice`, and `recommendationservice` service accounts. The policy further scopes access to specific RPC paths: `/hipstershop.ProductCatalogService/GetProduct` and `/hipstershop.ProductCatalogService/ListProducts` on port 3550. NetworkPolicies restrict ingress to the same three services on port 3550. No agent-specific service accounts are defined, but the mesh-level scoping is well-implemented.
- **Implication**: Per-caller, per-RPC scoping is already in place via Istio AuthorizationPolicy. Adding agent-specific service accounts with tailored path rules is straightforward.
- **Recommendation**: Create agent-specific K8s ServiceAccounts and add them to the AuthorizationPolicy with per-path rules when agent integration begins.
- **Evidence**: `helm-chart/templates/productcatalogservice.yaml` (AuthorizationPolicy with path-level rules, NetworkPolicy), `helm-chart/values.yaml`

### AUTH-Q3: Action-Level Authorization
- **Severity**: INFO
- **Finding**: Istio AuthorizationPolicy defines per-path rules for specific RPCs (`GetProduct`, `ListProducts`) on port 3550. The application code itself has no action-level authorization — the gRPC server accepts all calls that reach it. Authorization is entirely at the mesh layer. For a stateless-utility serving public catalog data, mesh-level authorization is sufficient.
- **Implication**: Action-level authorization is effectively implemented at the mesh layer. The AuthorizationPolicy already restricts which RPCs each caller can invoke.
- **Recommendation**: Implement a gRPC server interceptor for action-level authorization as defense in depth if the service evolves beyond public data.
- **Evidence**: `helm-chart/templates/productcatalogservice.yaml` (AuthorizationPolicy), `src/productcatalogservice/product_catalog.go`

### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Archetype-Calibrated**: stateless-utility — downgraded to INFO
- **Finding**: No JWT parsing, no token exchange, no user context headers. No identity context in gRPC calls. Istio mTLS provides implicit caller identity at the mesh layer.
- **Implication**: For a stateless-utility returning public product catalog data, identity propagation has minimal security impact — responses are not user-specific and data is classified as PUBLIC. Istio provides caller identity at the mesh layer.
- **Recommendation**: No immediate action. Implement identity propagation if the service evolves to handle user-specific data.
- **Evidence**: `src/productcatalogservice/server.go`, `src/productcatalogservice/product_catalog.go`, `helm-chart/values.yaml`

### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No audit logging exists at the application layer. Logrus logs operational messages only (startup, catalog loading). No principal attribution in log output. Logs are ephemeral container stdout. OpenTelemetry tracing is enabled (`tracing: true`, `metrics: true` in values.yaml), which provides request-level trace context. OpenTelemetry Collector is deployed (`opentelemetryCollector.create: true`). No CloudTrail or equivalent immutable log storage.
- **Implication**: For read-only agent scope, audit logging is important but not a deployment blocker. OpenTelemetry traces provide request correlation as a partial audit signal.
- **Recommendation**: Add structured audit logging with caller identity (extracted from Istio mTLS peer identity). Forward to immutable store. Depends on AUTH-Q1 for principal attribution.
- **Evidence**: `src/productcatalogservice/server.go` (Logrus logger), `helm-chart/values.yaml` (`tracing: true`, `opentelemetryCollector.create: true`)

### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Service is stateless — reads product catalog from a static JSON file or AlloyDB (read-only queries). No multi-step write operations. No state mutations to compensate.
- **Implication**: No compensation concerns for read-only scope. Stateless architecture eliminates rollback requirements.
- **Recommendation**: No action needed. Maintain stateless architecture.
- **Evidence**: `src/productcatalogservice/product_catalog.go`, `src/productcatalogservice/catalog_loader.go`, `src/productcatalogservice/products.json`

### STATE-Q5: Rate Limiting and Throttling
- **Severity**: INFO
- **Finding**: Rate-limit EnvoyFilter is configured at the Istio/Envoy level, providing per-caller rate limiting for gRPC traffic. K8s resource limits cap CPU (200m) and memory (128Mi). HPAs are configured for auto-scaling based on metrics. ClusterIP service with no external API Gateway.
- **Implication**: Envoy-level rate limiting provides protection against runaway agent loops. Combined with HPAs, the service can handle traffic spikes while enforcing per-caller limits.
- **Recommendation**: Tune rate limit thresholds based on agent traffic patterns during pilot. Monitor rate limit rejection metrics.
- **Evidence**: `helm-chart/templates/productcatalogservice.yaml`, `helm-chart/values.yaml`, `kubernetes-manifests/productcatalogservice.yaml`

### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No writes, deletes, or modifications. Minimal blast radius. Read-only operations on public product catalog data.
- **Implication**: Transaction limits not applicable for read-only operations on public data.
- **Recommendation**: Implement if write operations are added.
- **Evidence**: `src/productcatalogservice/product_catalog.go`

### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: INFO
- **Finding**: HPAs are configured for auto-scaling. K8s resource limits defined (CPU: 100m request / 200m limit, memory: 64Mi request / 128Mi limit). Liveness and readiness probes configured (gRPC health check). Monitoring alerts configured for error rates and latency. Rate-limit EnvoyFilter provides traffic shaping. No formal load test results found.
- **Implication**: Auto-scaling and rate limiting provide capacity elasticity. The service's stateless nature (JSON file reads, in-memory catalog) means it can scale horizontally without shared-state bottlenecks.
- **Recommendation**: Run load tests simulating agent traffic patterns (burst reads, concurrent SearchProducts queries) to validate scaling behavior.
- **Evidence**: `helm-chart/templates/productcatalogservice.yaml`, `helm-chart/values.yaml`, `kubernetes-manifests/productcatalogservice.yaml`

### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO
- **Finding**: Product catalog data is classified as PUBLIC in both `DATA_CLASSIFICATION.md` and `protos/demo.proto` (comment: `Data Classification: PUBLIC`). No PII, PHI, or financial account data. Product fields are: id, name, description, picture, price_usd, categories, created_at, updated_at. The `DATA_CLASSIFICATION.md` explicitly states productcatalogservice classification is PUBLIC with no sensitive fields.
- **Implication**: No data classification controls needed. No PII exposure risk. Positive finding — classification exists and is documented.
- **Recommendation**: No action needed. Maintain classification documentation.
- **Evidence**: `DATA_CLASSIFICATION.md`, `protos/demo.proto` (data classification comments), `src/productcatalogservice/products.json`

### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Static, publicly available product catalog data. No regulated data. No PII. `DATA_CLASSIFICATION.md` classifies productcatalogservice as PUBLIC. No GDPR, LGPD, or HIPAA applicability. No cross-region replication configured. The data (product names, descriptions, prices, categories) carries no regulatory residency requirements.
- **Implication**: Public product catalog data has no residency restrictions. Formal classification exists in `DATA_CLASSIFICATION.md`.
- **Recommendation**: No immediate action. Re-evaluate if the catalog is extended to include user-specific data (e.g., personalized pricing, purchase history).
- **Evidence**: `DATA_CLASSIFICATION.md`, `src/productcatalogservice/products.json`, `protos/demo.proto`

### DATA-Q6: PII Redaction in Logs
- **Severity**: INFO
- **Finding**: Logs contain operational messages only (startup, catalog loading success/failure). No request details logged. No PII in data model — product catalog is PUBLIC data. No PII leakage risk.
- **Implication**: No PII redaction needed. Positive finding.
- **Recommendation**: No action needed.
- **Evidence**: `src/productcatalogservice/server.go`, `src/productcatalogservice/catalog_loader.go`

### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: INFO
- **Finding**: Proto uses versioned package `hipstershop.v1`. `buf.yaml` exists for proto linting. Proto defines typed schemas with data classification comments, timestamp fields (`created_at`, `updated_at`), and explicit field numbers. Breaking change detection (`buf breaking`) not yet in CI but tooling is in place.
- **Implication**: Schema versioning is established. Proto versioning enables safe evolution. `buf` tooling provides a path to automated breaking change detection.
- **Recommendation**: Add `buf breaking` to CI pipeline to complete the contract testing story (tracked under ENG-Q2).
- **Evidence**: `protos/demo.proto` (`hipstershop.v1`), `buf.yaml`

### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: INFO
- **Finding**: OpenTelemetry SDK with gRPC instrumentation is enabled (`tracing: true` in `helm-chart/values.yaml`). The Go server initializes OTel tracing via `otlptracegrpc` exporter to the OpenTelemetry Collector (`opentelemetryCollector.create: true`). gRPC server uses `otelgrpc.NewServerHandler()` for automatic trace propagation. Metrics enabled (`metrics: true`). Logrus provides structured JSON logging with timestamp, severity, and message fields. Trace context is propagated via OpenTelemetry.
- **Implication**: Distributed tracing is operational. Trace context enables end-to-end request correlation across services. Structured JSON logging supports log aggregation. The remaining gap (no trace_id in Logrus logs) is minor — OpenTelemetry trace IDs serve the same purpose.
- **Recommendation**: Add trace_id to Logrus log entries for log-to-trace correlation. This is a minor enhancement, not a gap.
- **Evidence**: `src/productcatalogservice/server.go` (OTel setup, otelgrpc handler), `helm-chart/values.yaml` (`tracing: true`, `opentelemetryCollector.create: true`, `metrics: true`), `go.mod` (OTel dependencies)

### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: INFO
- **Finding**: Monitoring alerts are configured for error rates and latency. Metrics collection is enabled (`metrics: true`). K8s liveness and readiness probes provide pod availability monitoring (gRPC health check on port 3550). HPAs configured for auto-scaling based on metrics.
- **Implication**: Alerting infrastructure is in place. Service degradation will be detected before agents cascade failures.
- **Recommendation**: Tune alert thresholds based on agent traffic patterns during pilot.
- **Evidence**: `helm-chart/templates/productcatalogservice.yaml`, `helm-chart/values.yaml` (`metrics: true`), `kubernetes-manifests/productcatalogservice.yaml`

### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: INFO
- **Finding**: Comprehensive IaC across multiple layers: K8s manifests (`kubernetes-manifests/productcatalogservice.yaml`), Helm chart (`helm-chart/templates/productcatalogservice.yaml`), Kustomize (`kustomize/base/productcatalogservice.yaml`). AuthorizationPolicies, NetworkPolicies, and Sidecars are all defined in IaC and enabled. GitHub Actions CI on PRs. CODEOWNERS enforces peer review. No drift detection configured.
- **Implication**: Infrastructure governance is strong — IaC coverage is comprehensive and peer review is enforced. The drift detection gap is minor for a K8s-native deployment where Helm/Kustomize reconciliation provides implicit drift correction on deploy.
- **Recommendation**: Implement drift detection for completeness. Consider ArgoCD or Flux for GitOps-based continuous reconciliation.
- **Evidence**: `kubernetes-manifests/productcatalogservice.yaml`, `helm-chart/templates/productcatalogservice.yaml`, `kustomize/base/productcatalogservice.yaml`, `helm-chart/values.yaml`, `.github/`

### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: gRPC Protocol Buffers — strongly-typed binary format with explicit types, field numbers, data classification comments, and timestamp fields. Product messages include `id`, `name`, `description`, `picture`, `price_usd` (Money type), `categories`, `created_at`, `updated_at`.
- **Implication**: Protobuf is more structured than JSON. Excellent for agent integration with auto-generated client code. Well-defined Money type prevents currency ambiguity.
- **Recommendation**: No action needed.
- **Evidence**: `protos/demo.proto`

### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: Rate-limit EnvoyFilter is configured at the Istio/Envoy level. No rate limit headers in gRPC responses (`X-RateLimit-Remaining`, `Retry-After`). Internal ClusterIP service. K8s resource limits provide implicit capping.
- **Implication**: Agents cannot self-throttle based on server-side rate limit signals. Envoy-level rate limiting provides server-side protection but clients are not informed of remaining quota.
- **Recommendation**: Add gRPC trailing metadata with rate limit status (remaining quota, retry-after) so agents can self-throttle proactively.
- **Evidence**: `src/productcatalogservice/server.go`, `helm-chart/templates/productcatalogservice.yaml`

### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No quality metrics. 9 static product entries in `products.json`. No validation of price ranges or category consistency. Quality is fixed at build time with no runtime degradation. AlloyDB path provides an alternative data source but no quality monitoring for either path.
- **Implication**: Quality is static and deterministic for JSON mode. No runtime degradation risk. AlloyDB mode would benefit from quality monitoring.
- **Recommendation**: Add validation that prices are positive and categories are from a known set. Monitor AlloyDB data quality if that path is used.
- **Evidence**: `src/productcatalogservice/products.json`, `src/productcatalogservice/catalog_loader.go`

### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Clear semantic names: `product_id`, `name`, `description`, `picture`, `price_usd`, `currency_code`, `units`, `nanos`, `categories`, `created_at`, `updated_at`. Detailed comments in proto. No abbreviations. Data classification comments on messages.
- **Implication**: LLMs can interpret fields directly. No translation or data dictionary needed.
- **Recommendation**: No action needed.
- **Evidence**: `protos/demo.proto`

### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal data catalog. Proto file serves as informal documentation with data classification comments and system-of-record designation (`System of Record: productcatalogservice owns product data (JSON file-backed)`). `DATA_CLASSIFICATION.md` provides service-level classification taxonomy. Self-describing JSON data.
- **Implication**: Sufficient for single-purpose utility service. `DATA_CLASSIFICATION.md` and proto comments provide good metadata coverage.
- **Recommendation**: Register in organization API catalog if part of larger data mesh.
- **Evidence**: `protos/demo.proto`, `DATA_CLASSIFICATION.md`, `src/productcatalogservice/products.json`

### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics. Operational logging and OpenTelemetry metrics provide infrastructure-level visibility. No product lookup volume metrics by category or search query analytics.
- **Implication**: No business outcome monitoring. Operational metrics may suffice initially for a utility service.
- **Recommendation**: Publish metrics for product lookup volume by category and search query frequency if business analytics are needed.
- **Evidence**: `src/productcatalogservice/server.go`, `src/productcatalogservice/product_catalog.go`

### ENG-Q4: API Test Coverage
- **Severity**: INFO
- **Finding**: No productcatalogservice-specific test files found. CI runs via Cloud Build + Skaffold. Smoke testing via loadgenerator only. Simple service logic (JSON parsing, in-memory search) reduces untested-code risk. Go test infrastructure is available but no `_test.go` files exist.
- **Implication**: For a stateless-utility with simple read logic, the risk of zero test coverage is lower than for stateful services. Still recommended for regression safety.
- **Recommendation**: Add Go unit tests for `ListProducts`, `GetProduct`, `SearchProducts`, and `parseCatalog`. Add gRPC integration tests. Include in CI.
- **Evidence**: `src/productcatalogservice/product_catalog.go`, `src/productcatalogservice/catalog_loader.go`, `cloudbuild.yaml`

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: Well-documented gRPC interface in `protos/demo.proto` with `ProductCatalogService` defining `ListProducts`, `GetProduct`, and `SearchProducts` RPCs. Proto uses versioned package `hipstershop.v1`. Implemented in Go (`product_catalog.go`). All RPCs are read-only. Positive finding.
- **Gap**: None — BLOCKER criteria satisfied.
- **Recommendation**: No remediation needed.
- **Evidence**: `protos/demo.proto`, `src/productcatalogservice/product_catalog.go`

#### API-Q2: Machine-Readable API Specification
- **Severity**: INFO
- **Finding**: `protos/demo.proto` is a machine-readable spec. Protobuf is strongly typed with field numbers, data classification comments, and timestamps. `buf.yaml` provides proto linting. Current with implementation. Positive finding.
- **Gap**: None.
- **Recommendation**: Consider enabling gRPC server reflection for runtime schema discovery.
- **Evidence**: `protos/demo.proto`, `buf.yaml`, `src/productcatalogservice/product_catalog.go`

#### API-Q3: Structured Error Responses
- **Severity**: INFO
- **Finding**: `GetProduct` returns `status.Errorf(codes.NotFound, ...)` for missing products. gRPC status codes provide structured error classification. `SearchProducts` returns empty results (not errors) for no matches. Sufficient for a read-only stateless-utility.
- **Gap**: No retryable boolean in error metadata. Minor for read-only service with well-defined gRPC status codes.
- **Recommendation**: Consider adding a gRPC interceptor for consistent error metadata across all RPCs.
- **Evidence**: `src/productcatalogservice/product_catalog.go`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: All three RPCs are read-only, stateless, inherently idempotent. Same input always produces same output.
- **Gap**: N/A — no write operations.
- **Recommendation**: No action needed.
- **Evidence**: `src/productcatalogservice/product_catalog.go`, `src/productcatalogservice/products.json`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: gRPC Protocol Buffers — strongly-typed binary format with explicit types, field numbers, data classification comments, and timestamp fields.
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
- **Finding**: Rate-limit EnvoyFilter configured at Istio/Envoy level. No rate limit headers in gRPC responses. Internal ClusterIP service. K8s resource limits provide implicit capping.
- **Gap**: Agents cannot self-throttle based on server-side rate limit signals.
- **Recommendation**: Add gRPC trailing metadata with rate limit status when agent integration begins.
- **Evidence**: `src/productcatalogservice/server.go`, `helm-chart/templates/productcatalogservice.yaml`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: Istio AuthorizationPolicy is enabled (`authorizationPolicies.create: true`), providing mTLS-based identity verification. Callers restricted to `frontend`, `checkoutservice`, and `recommendationservice` service accounts. Istio sidecars enabled (`sidecars.create: true`). The gRPC server uses `grpc.NewServer()` with OTel stats handler — Istio sidecar terminates mTLS before traffic reaches the application (standard Istio pattern).
- **Gap**: None — mesh-level mTLS with per-service AuthorizationPolicy satisfies machine identity authentication.
- **Recommendation**: For defense in depth, consider extracting Istio peer identity from request headers for application-level audit logging.
- **Evidence**: `helm-chart/values.yaml` (`authorizationPolicies.create: true`, `sidecars.create: true`), `helm-chart/templates/productcatalogservice.yaml`, `src/productcatalogservice/server.go`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: INFO
- **Finding**: Istio AuthorizationPolicy restricts callers to `frontend`, `checkoutservice`, and `recommendationservice`. Policy scopes access to specific RPC paths (`/hipstershop.ProductCatalogService/GetProduct`, `/hipstershop.ProductCatalogService/ListProducts`) on port 3550. NetworkPolicies restrict ingress to the same three services.
- **Gap**: `SearchProducts` RPC is not listed in the AuthorizationPolicy paths — may be blocked by default-deny. No agent-specific service accounts.
- **Recommendation**: Verify `SearchProducts` accessibility. Create agent-specific service accounts with per-RPC AuthorizationPolicy rules.
- **Evidence**: `helm-chart/templates/productcatalogservice.yaml` (AuthorizationPolicy, NetworkPolicy), `helm-chart/values.yaml`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: INFO
- **Finding**: Istio AuthorizationPolicy defines per-path rules for specific RPCs on port 3550. Application code has no action-level authorization. For a stateless-utility serving public catalog data, mesh-level authorization is sufficient.
- **Gap**: No application-layer authorization. Mesh bypass would expose all RPCs.
- **Recommendation**: Implement gRPC server interceptor for action-level authorization as defense in depth if the service evolves beyond public data.
- **Evidence**: `helm-chart/templates/productcatalogservice.yaml`, `src/productcatalogservice/product_catalog.go`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Archetype-Calibrated**: stateless-utility — downgraded to INFO
- **Finding**: No JWT parsing, token exchange, or user context headers. Istio mTLS provides implicit caller identity at mesh layer.
- **Gap**: No application-level identity propagation. Minimal impact for stateless-utility returning public data.
- **Recommendation**: No immediate action. Implement if service evolves to handle user-specific data.
- **Evidence**: `src/productcatalogservice/server.go`, `src/productcatalogservice/product_catalog.go`, `helm-chart/values.yaml`

#### AUTH-Q5: Credential Management
- **Severity**: RISK
- **Finding**: No secrets management for default JSON-file mode. AlloyDB path uses Google Cloud Secret Manager (`catalog_loader.go`). No hardcoded credentials. Workload Identity for GCP libraries.
- **Gap**: No credential management framework for agent API keys or service credentials.
- **Recommendation**: Maintain credential-free architecture. Adopt K8s external secrets operator if credentials are needed.
- **Evidence**: `src/productcatalogservice/catalog_loader.go`, `src/productcatalogservice/server.go`, `go.mod`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No audit logging. Logrus operational messages only. No principal attribution. OpenTelemetry tracing enabled provides request correlation. Logs are ephemeral container stdout.
- **Gap**: No immutable audit trail. Cannot attribute actions to specific agent identities.
- **Recommendation**: Add structured audit logging with caller identity. Forward to immutable store.
- **Evidence**: `src/productcatalogservice/server.go`, `helm-chart/values.yaml` (`tracing: true`)

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicy provides mechanism to deny specific service accounts. NetworkPolicies enabled. No automated suspension — requires manual policy changes.
- **Gap**: No automated or rapid suspension mechanism.
- **Recommendation**: Implement automated suspension via AuthorizationPolicy updates triggered by anomaly detection.
- **Evidence**: `helm-chart/templates/productcatalogservice.yaml`, `helm-chart/values.yaml`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Stateless service. Reads product catalog from JSON file or AlloyDB. No write operations, no transactions, no state mutations to compensate.
- **Gap**: No compensation mechanisms — but no state mutations exist.
- **Recommendation**: Maintain stateless architecture. Implement compensation if write operations added.
- **Evidence**: `src/productcatalogservice/product_catalog.go`, `src/productcatalogservice/catalog_loader.go`

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
- **Severity**: INFO
- **Finding**: Rate-limit EnvoyFilter configured at Istio/Envoy level. K8s resource limits cap CPU/memory. HPAs configured for auto-scaling. ClusterIP service with no external API Gateway.
- **Gap**: None — Envoy-level rate limiting provides per-caller protection.
- **Recommendation**: Tune rate limit thresholds based on agent traffic patterns during pilot.
- **Evidence**: `helm-chart/templates/productcatalogservice.yaml`, `helm-chart/values.yaml`, `kubernetes-manifests/productcatalogservice.yaml`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No writes, deletes, or modifications. Minimal blast radius. Read-only operations on public data.
- **Gap**: None for read-only scope.
- **Recommendation**: Implement if write operations added.
- **Evidence**: `src/productcatalogservice/product_catalog.go`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: INFO
- **Finding**: HPAs configured for auto-scaling. K8s resource limits defined. Liveness/readiness probes configured. Monitoring alerts configured. Rate-limit EnvoyFilter provides traffic shaping. No formal load test results.
- **Gap**: No load test results for agent traffic patterns.
- **Recommendation**: Run load tests simulating agent traffic patterns.
- **Evidence**: `helm-chart/templates/productcatalogservice.yaml`, `helm-chart/values.yaml`, `kubernetes-manifests/productcatalogservice.yaml`

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
- **Finding**: Skaffold local dev. Cloud Build deployment. No persistent agent testing environment. `products.json` provides deterministic test data.
- **Gap**: No dedicated agent testing environment.
- **Recommendation**: Create persistent staging namespace for agent integration testing.
- **Evidence**: `skaffold.yaml`, `src/productcatalogservice/Dockerfile`, `src/productcatalogservice/products.json`, `cloudbuild.yaml`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO
- **Finding**: Product catalog classified as PUBLIC in `DATA_CLASSIFICATION.md` and `protos/demo.proto`. No PII/PHI/financial data. Positive finding — classification exists and is documented.
- **Gap**: None.
- **Recommendation**: Maintain classification documentation.
- **Evidence**: `DATA_CLASSIFICATION.md`, `protos/demo.proto`, `src/productcatalogservice/products.json`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Public product catalog data. No regulated data. `DATA_CLASSIFICATION.md` classifies as PUBLIC. No residency restrictions.
- **Gap**: None — public data with formal classification.
- **Recommendation**: Re-evaluate if catalog extended to include user-specific data.
- **Evidence**: `DATA_CLASSIFICATION.md`, `src/productcatalogservice/products.json`, `protos/demo.proto`

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
- **Finding**: Logs contain operational messages only. No PII in data model. No PII leakage risk.
- **Gap**: None.
- **Recommendation**: No action needed.
- **Evidence**: `src/productcatalogservice/server.go`, `src/productcatalogservice/catalog_loader.go`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No quality metrics. 9 static product entries. Quality fixed at build time. No runtime degradation.
- **Gap**: No quality monitoring. Static data has fixed quality characteristics.
- **Recommendation**: Add validation for price ranges and category consistency.
- **Evidence**: `src/productcatalogservice/products.json`, `src/productcatalogservice/catalog_loader.go`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: INFO
- **Finding**: Proto uses versioned package `hipstershop.v1`. `buf.yaml` for proto linting. Typed schemas with data classification comments and timestamps. `buf breaking` not yet in CI.
- **Gap**: `buf breaking` not in CI (tracked under ENG-Q2).
- **Recommendation**: Add `buf breaking` to CI pipeline.
- **Evidence**: `protos/demo.proto`, `buf.yaml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Clear semantic names: `product_id`, `name`, `description`, `picture`, `price_usd`, `currency_code`, `units`, `nanos`, `categories`, `created_at`, `updated_at`. Detailed comments. No abbreviations. Data classification comments on messages.
- **Gap**: None.
- **Recommendation**: No action needed.
- **Evidence**: `protos/demo.proto`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal catalog. Proto file with data classification comments and system-of-record designation. `DATA_CLASSIFICATION.md` provides service-level taxonomy. Self-describing JSON data.
- **Gap**: No formal catalog. Sufficient for single-purpose utility service.
- **Recommendation**: Register in organization API catalog if part of larger data mesh.
- **Evidence**: `protos/demo.proto`, `DATA_CLASSIFICATION.md`, `src/productcatalogservice/products.json`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: INFO
- **Finding**: OpenTelemetry SDK with gRPC instrumentation enabled (`tracing: true`). OTel Collector deployed (`opentelemetryCollector.create: true`). Metrics enabled (`metrics: true`). Go server uses `otelgrpc.NewServerHandler()` and `otelgrpc.NewClientHandler()` for automatic trace propagation. Logrus structured JSON logging with timestamp, severity, message fields.
- **Gap**: No trace_id in Logrus log entries (minor — OTel trace IDs serve the same purpose).
- **Recommendation**: Add trace_id to Logrus log entries for log-to-trace correlation.
- **Evidence**: `src/productcatalogservice/server.go`, `helm-chart/values.yaml`, `go.mod`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: INFO
- **Finding**: Monitoring alerts configured. Metrics collection enabled. K8s health probes (gRPC on port 3550). HPAs for auto-scaling.
- **Gap**: None — alerting infrastructure is in place.
- **Recommendation**: Tune alert thresholds based on agent traffic patterns during pilot.
- **Evidence**: `helm-chart/templates/productcatalogservice.yaml`, `helm-chart/values.yaml`, `kubernetes-manifests/productcatalogservice.yaml`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics. Operational logging and OTel metrics provide infrastructure-level visibility.
- **Gap**: No business outcome monitoring. Operational metrics may suffice for a utility service.
- **Recommendation**: Publish metrics for product lookup volume by category and search query frequency.
- **Evidence**: `src/productcatalogservice/server.go`, `src/productcatalogservice/product_catalog.go`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: INFO
- **Finding**: Comprehensive IaC: K8s manifests, Helm, Kustomize. AuthorizationPolicies, NetworkPolicies, Sidecars all defined in IaC and enabled. GitHub Actions CI. CODEOWNERS for peer review. No drift detection.
- **Gap**: Drift detection missing (minor for K8s-native with Helm reconciliation).
- **Recommendation**: Implement drift detection or GitOps (ArgoCD/Flux).
- **Evidence**: `kubernetes-manifests/productcatalogservice.yaml`, `helm-chart/templates/productcatalogservice.yaml`, `kustomize/base/productcatalogservice.yaml`, `helm-chart/values.yaml`, `.github/`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK
- **Finding**: CI exists (Cloud Build + Skaffold + GitHub Actions). Proto versioned (`hipstershop.v1`). `buf.yaml` for linting. No `buf breaking` in CI. No service-specific contract tests.
- **Gap**: No automated breaking change detection in CI.
- **Recommendation**: Add `buf breaking` to CI. Add ProductCatalogService contract tests.
- **Evidence**: `cloudbuild.yaml`, `.github/workflows/`, `buf.yaml`, `protos/demo.proto`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK
- **Finding**: K8s rollout history. Skaffold deployment. Manual rollback only. No canary or automated rollback.
- **Gap**: No automated rollback on service degradation.
- **Recommendation**: Configure automated rollback triggers (Flagger, Argo Rollouts).
- **Evidence**: `kubernetes-manifests/productcatalogservice.yaml`, `helm-chart/templates/productcatalogservice.yaml`, `skaffold.yaml`

#### ENG-Q4: API Test Coverage
- **Severity**: INFO
- **Finding**: No `_test.go` files for productcatalogservice. CI runs via Cloud Build + Skaffold. Smoke testing via loadgenerator only. Simple read-only logic reduces untested-code risk.
- **Gap**: Zero test coverage. For a stateless-utility with simple read logic, the risk is lower than for stateful services.
- **Recommendation**: Add Go unit tests for `ListProducts`, `GetProduct`, `SearchProducts`, and `parseCatalog`. Include in CI.
- **Evidence**: `src/productcatalogservice/product_catalog.go`, `src/productcatalogservice/catalog_loader.go`, `cloudbuild.yaml`

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
| `kubernetes-manifests/productcatalogservice.yaml` | AUTH-Q1, AUTH-Q2, STATE-Q5, STATE-Q7, OBS-Q2, API-Q8, ENG-Q1, ENG-Q3 |
| `kustomize/base/productcatalogservice.yaml` | ENG-Q1 |
| `helm-chart/templates/productcatalogservice.yaml` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q7, STATE-Q5, STATE-Q7, OBS-Q2, API-Q8, ENG-Q1, ENG-Q3 |
| `helm-chart/values.yaml` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q6, AUTH-Q7, OBS-Q1, OBS-Q2, ENG-Q1, STATE-Q5, STATE-Q7 |

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `src/productcatalogservice/server.go` | API-Q1, API-Q3, API-Q8, AUTH-Q1, AUTH-Q4, AUTH-Q6, STATE-Q5, DATA-Q6, OBS-Q1, OBS-Q3, ENG-Q4 |
| `src/productcatalogservice/product_catalog.go` | API-Q1, API-Q2, API-Q3, API-Q4, AUTH-Q3, AUTH-Q4, STATE-Q1, STATE-Q6, STATE-Q7, OBS-Q3, ENG-Q4 |
| `src/productcatalogservice/catalog_loader.go` | AUTH-Q5, STATE-Q1, DATA-Q6, DATA-Q7, ENG-Q4 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `protos/demo.proto` | API-Q1, API-Q2, API-Q4, API-Q5, DATA-Q1, DATA-Q2, DISC-Q1, DISC-Q2, DISC-Q3, ENG-Q2 |
| `buf.yaml` | API-Q2, DISC-Q1, ENG-Q2 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `cloudbuild.yaml` | HITL-Q3, ENG-Q2, ENG-Q4 |
| `skaffold.yaml` | HITL-Q3, ENG-Q1, ENG-Q3 |
| `.github/workflows/` | ENG-Q1, ENG-Q2 |
| `.github/CODEOWNERS` | ENG-Q1 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `src/productcatalogservice/Dockerfile` | HITL-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `src/productcatalogservice/go.mod` | AUTH-Q5, OBS-Q1 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `src/productcatalogservice/products.json` | API-Q4, STATE-Q1, DATA-Q1, DATA-Q2, DATA-Q7, DISC-Q3, HITL-Q3 |
| `DATA_CLASSIFICATION.md` | DATA-Q1, DATA-Q2, DISC-Q3 |
