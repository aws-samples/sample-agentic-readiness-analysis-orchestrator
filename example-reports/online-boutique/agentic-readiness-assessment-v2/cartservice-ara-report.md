# Agentic Readiness Assessment Report

**Target**: services/microservices-demo/src/cartservice
**Date**: 2026-04-16
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Service Archetype**: stateful-crud (user-provided)
**Agent Scope**: read-only
**Priority**: P0
**Tags**: csharp, grpc, redis, stateful
**Context**: C# gRPC service managing shopping carts with Redis backing store.

---

## Readiness Profile: Pilot-Ready

**BLOCKERs**: 0 | **RISKs**: 13 | **INFOs**: 26

Supervised pilot with: (1) human approval gates on irreversible actions, (2) agent limited to low-blast-radius operations, (3) compensating controls for each open RISK, (4) remediation timeline before expanding scope.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 0 |
| RISK | 13 |
| INFO | 26 |
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
- **Finding**: The shared `protos/demo.proto` defines the `CartService` with versioned package `hipstershop.v1`, data classification comments, and timestamps. However, the local `src/cartservice/src/protos/Cart.proto` uses the unversioned `hipstershop` package and lacks data classification annotations, timestamps, and `buf.yaml` integration. The local proto is what the C# build actually compiles (`cartservice.csproj` references `protos\Cart.proto`).
- **Gap**: The compiled proto lacks versioning, data classification comments, and `updated_at` timestamp. Two proto sources exist with divergent schemas — the shared proto is richer but the local proto is what ships.
- **Compensating Controls**:
  - Use the shared `protos/demo.proto` as the authoritative spec for agent tool generation
  - Align the local `Cart.proto` with the shared proto in a follow-up
- **Remediation Timeline**: 30 days
- **Recommendation**: Consolidate to a single proto source. Update `cartservice.csproj` to compile from the shared `protos/demo.proto` (which already has `hipstershop.v1`, data classification, and timestamps).
- **Evidence**: `protos/demo.proto`, `src/cartservice/src/protos/Cart.proto`, `src/cartservice/src/cartservice.csproj`

### API-Q3: Structured Error Responses
- **Severity**: RISK
- **Finding**: `RedisCartStore.cs` catches exceptions and throws `RpcException` with `StatusCode.FailedPrecondition` and a message string including the raw exception (`$"Can't access cart storage. {ex}"`). All three operations (AddItem, GetCart, EmptyCart) use the same status code regardless of error type. No structured error metadata, no retryable indicator, no error codes beyond the gRPC status.
- **Gap**: Agents cannot distinguish retriable errors (Redis timeout) from terminal errors (invalid input). Raw exception details leak in error messages. Single status code for all failure modes.
- **Compensating Controls**:
  - Wrap agent tool calls with client-side error classification based on gRPC status codes
  - Implement retry with exponential backoff for UNAVAILABLE/DEADLINE_EXCEEDED status codes
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Differentiate error types: use `StatusCode.Unavailable` for Redis connection failures (retriable), `StatusCode.InvalidArgument` for bad input, `StatusCode.NotFound` for missing carts. Remove raw exception from error messages. Add structured error metadata via gRPC trailing metadata.
- **Evidence**: `src/cartservice/src/cartstore/RedisCartStore.cs` (catch blocks in AddItemAsync, GetCartAsync, EmptyCartAsync)

### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicy restricts callers to `frontend` and `checkoutservice` service accounts with per-path rules for all three RPCs (`AddItem`, `GetCart`, `EmptyCart`). However, both allowed callers have access to all three RPCs — no differentiation. No agent-specific service accounts are defined. No IAM policies or application-level RBAC.
- **Gap**: No per-RPC scoping for different callers. No agent-specific service accounts with tailored permissions (e.g., agent can `GetCart` but not `EmptyCart`).
- **Compensating Controls**:
  - Istio AuthorizationPolicy restricts callers to known service accounts (defense in depth)
  - Define agent-specific K8s ServiceAccounts and add them to the AuthorizationPolicy with per-path rules
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create agent-specific service accounts with per-RPC AuthorizationPolicy rules. For read-only agents, restrict to `GetCart` only.
- **Evidence**: `helm-chart/templates/cartservice.yaml` (AuthorizationPolicy section), `helm-chart/values.yaml` (`authorizationPolicies.create: true`)

### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicy defines per-path rules for the three RPCs. The application code itself has no action-level authorization — `CartService.cs` accepts all calls that reach it. Authorization is entirely at the mesh layer.
- **Gap**: No application-layer action-level authorization. If the mesh is bypassed, all RPCs are accessible to any caller.
- **Compensating Controls**:
  - Istio sidecar injection (`sidecars.create: true`) ensures mesh-level enforcement
  - Network policies (`networkPolicies.create: true`) provide additional defense in depth
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement a gRPC server interceptor for action-level authorization as defense in depth beyond the mesh layer.
- **Evidence**: `src/cartservice/src/services/CartService.cs`, `helm-chart/templates/cartservice.yaml`, `helm-chart/values.yaml`

### AUTH-Q5: Credential Management
- **Severity**: RISK
- **Finding**: Redis connection string is passed via environment variable `REDIS_ADDR` (value: `redis-cart:6379`) — no authentication, no password. The `cartservice.csproj` includes `Google.Cloud.SecretManager.V1` as a dependency, but no code references Secret Manager. No Vault integration. No credential rotation mechanism.
- **Gap**: Redis has no authentication — any pod that can reach `redis-cart:6379` can read/write cart data. No credential management framework despite Secret Manager dependency being present.
- **Compensating Controls**:
  - NetworkPolicy restricts Redis access to cartservice pods only
  - Istio AuthorizationPolicy on redis-cart restricts access to cartservice service account
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Enable Redis AUTH with a password managed via K8s Secrets or Secret Manager. Implement credential rotation. Use the existing `Google.Cloud.SecretManager.V1` dependency.
- **Evidence**: `src/cartservice/src/Startup.cs` (REDIS_ADDR env var), `src/cartservice/src/cartservice.csproj` (SecretManager dependency), `helm-chart/templates/cartservice.yaml` (REDIS_ADDR value), `helm-chart/values.yaml` (`cartDatabase.connectionString`)

### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: No audit logging exists. `RedisCartStore.cs` uses `Console.WriteLine` for operational messages (e.g., `AddItemAsync called with userId=...`). No principal attribution in any log output. Logs are ephemeral container stdout with no immutable storage configuration. No CloudTrail or equivalent. OpenTelemetry tracing is enabled (`tracing: true` in values.yaml), providing request-level trace context but not audit-grade principal attribution. The `Console.WriteLine` calls log `userId` in plaintext — a PII-CANDIDATE field — without redaction.
- **Gap**: No immutable audit trail. Cannot determine who called the service or attribute actions to specific agent identities. PII-CANDIDATE field logged in plaintext.
- **Compensating Controls**:
  - Configure K8s log forwarding to immutable store (e.g., CloudWatch Logs with retention policy, S3 with Object Lock)
  - OpenTelemetry traces provide request correlation as a partial audit signal
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add structured audit logging with caller identity (extracted from Istio mTLS peer identity). Forward to immutable store. Redact `userId` from operational logs (see DATA-Q6).
- **Evidence**: `src/cartservice/src/cartstore/RedisCartStore.cs` (Console.WriteLine with userId), `helm-chart/values.yaml` (`tracing: true`)

### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicy provides a mechanism to deny specific service accounts by updating the policy. NetworkPolicies are enabled. However, there is no automated suspension mechanism — policy changes require Helm value updates or manual kubectl edits. No API key revocation, no service account disable endpoint.
- **Gap**: No automated or rapid suspension mechanism. Isolating a misbehaving agent requires manual AuthorizationPolicy or NetworkPolicy changes.
- **Compensating Controls**:
  - Istio AuthorizationPolicy can be updated to deny specific service accounts (manual process)
  - K8s NetworkPolicy can block specific pods as emergency measure
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement automated suspension via AuthorizationPolicy updates triggered by anomaly detection. Consider an operator or webhook that can instantly deny a service account.
- **Evidence**: `helm-chart/templates/cartservice.yaml`, `helm-chart/values.yaml` (`authorizationPolicies.create: true`, `networkPolicies.create: true`)

### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: Cart operations are individual Redis writes — `AddItem` reads cart, modifies in memory, writes back. `EmptyCart` overwrites with empty cart. No multi-step transactions, no saga pattern, no undo endpoints. `AddItem` is not atomic (read-modify-write without locking). No compensation logic exists.
- **Gap**: No compensation mechanisms for partial failures. The read-modify-write pattern in `AddItemAsync` is not atomic — concurrent calls could lose updates. No undo endpoint for `EmptyCart`.
- **Compensating Controls**:
  - Cart data is low-criticality (user can re-add items)
  - Read-only agent scope means agents won't trigger write operations
  - Document non-atomic behavior for agent integration teams
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement Redis WATCH/MULTI for atomic read-modify-write. Add an undo endpoint or cart history for compensation. Consider event sourcing for cart state changes.
- **Evidence**: `src/cartservice/src/cartstore/RedisCartStore.cs` (AddItemAsync read-modify-write pattern)

### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK
- **Finding**: Rate-limit EnvoyFilter is configured at the Istio mesh level, providing per-caller rate limiting for gRPC traffic. However, no application-level rate limiting exists in the C# code. K8s resource limits cap CPU/memory but not request rates. HPA is configured for auto-scaling based on metrics.
- **Gap**: Application-level rate limiting is absent — rate limiting depends entirely on the Envoy mesh layer. If the mesh is bypassed, no rate protection exists.
- **Compensating Controls**:
  - EnvoyFilter rate limiting provides mesh-level protection
  - HPA auto-scaling absorbs traffic spikes
  - K8s resource limits prevent resource exhaustion
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add application-level rate limiting as defense in depth (e.g., ASP.NET Core rate limiting middleware). Tune EnvoyFilter rate limits for agent traffic patterns.
- **Evidence**: `kubernetes-manifests/cartservice.yaml`, `helm-chart/values.yaml` (`sidecars.create: true`), `src/cartservice/src/Startup.cs`

### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK
- **Finding**: Skaffold provides local development. CI deploys per-PR to ephemeral namespaces on `prs-gke-cluster`. Docker Compose available for local testing. No persistent agent testing environment with production-equivalent data shape and Redis state.
- **Gap**: No dedicated agent testing environment with persistent Redis state.
- **Compensating Controls**:
  - Use Skaffold for local instance with Docker build for isolated testing
  - Leverage per-PR ephemeral namespaces for integration testing
- **Remediation Timeline**: 30 days
- **Recommendation**: Create persistent staging namespace for agent integration testing with production-equivalent Redis configuration and seed data.
- **Evidence**: `skaffold.yaml`, `src/cartservice/src/Dockerfile`, `.github/workflows/ci-pr.yaml`

### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: Cart data contains `user_id` (classified as PII-CANDIDATE in proto and DATA_CLASSIFICATION.md) and product selections. Redis uses `emptyDir` volume (ephemeral, in-memory). No explicit residency requirements or documentation. No cross-region replication configured.
- **Gap**: No formal data residency documentation. `user_id` is PII-CANDIDATE — if it contains email addresses or other PII, residency requirements may apply. No formal assessment of whether cart data crosses jurisdictional boundaries.
- **Compensating Controls**:
  - Document that cart data is ephemeral (Redis emptyDir) and does not persist across pod restarts
  - Implement residency controls proactively if user_id format is confirmed as PII
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document data residency posture formally. Determine whether `user_id` format constitutes PII (email vs opaque ID). Implement residency-aware controls if PII is confirmed.
- **Evidence**: `protos/demo.proto` (PII-CANDIDATE annotations), `DATA_CLASSIFICATION.md`, `helm-chart/templates/cartservice.yaml` (Redis emptyDir volume)

### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK
- **Finding**: CI exists (Cloud Build + Skaffold + GitHub Actions). C# unit tests run in CI (`dotnet test src/cartservice/`). Proto uses versioned package (`hipstershop.v1`) in shared proto. `buf.yaml` exists with `breaking` rules configured (`FILE` strategy). However, `buf breaking` is not integrated into the CI pipeline. No cartservice-specific contract tests validating gRPC request/response schemas.
- **Gap**: No automated breaking change detection in CI pipeline despite `buf.yaml` being configured for it. No service-specific API contract tests.
- **Compensating Controls**:
  - Protobuf wire compatibility provides implicit backward compatibility for additive changes
  - `buf.yaml` with `breaking` rules is ready — just needs CI integration
  - Existing unit tests validate basic CRUD operations
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `buf breaking` step to GitHub Actions CI pipeline. Add CartService-specific contract tests validating proto schema compliance.
- **Evidence**: `cloudbuild.yaml`, `.github/workflows/ci-pr.yaml`, `protos/buf.yaml`, `protos/demo.proto`

### ENG-Q3: Rollback Capability
- **Severity**: RISK
- **Finding**: K8s Deployment with rollout history. Skaffold deployment. No automated rollback triggers. Manual rollback via `kubectl rollout undo` only. No canary deployment, no Flagger, no Argo Rollouts. Monitoring alerts are configured, which can trigger manual rollback faster.
- **Gap**: No automated rollback on service degradation. Manual rollback only.
- **Compensating Controls**:
  - K8s rollout history enables manual rollback within minutes
  - Liveness/readiness probes prevent traffic to unhealthy pods
  - Monitoring alerts can trigger manual rollback faster
  - HPA provides auto-scaling resilience
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure automated rollback triggers using Flagger or Argo Rollouts with canary analysis. Integrate with monitoring alerts for automatic rollback on error rate spikes.
- **Evidence**: `skaffold.yaml`, `kubernetes-manifests/cartservice.yaml`

---

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: Well-documented gRPC interface in `protos/demo.proto` with `CartService` defining `AddItem`, `GetCart`, and `EmptyCart` RPCs. Proto uses versioned package `hipstershop.v1` with data classification comments and `updated_at` timestamp on `Cart` message. Implemented in C# (`CartService.cs`, `RedisCartStore.cs`). Local `Cart.proto` also exists but is less complete. Positive finding.
- **Implication**: gRPC interface can be used directly as agent tool binding. Proto enables auto-generated client code. Three clear CRUD operations with well-defined request/response types.
- **Recommendation**: No remediation needed. Consolidate to single proto source (tracked under API-Q2).
- **Evidence**: `protos/demo.proto`, `src/cartservice/src/services/CartService.cs`

### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: `AddItem` is additive (increments quantity) — calling it twice doubles the quantity. `EmptyCart` is idempotent (repeated calls produce same empty state). `GetCart` is read-only and inherently idempotent. No idempotency keys supported.
- **Implication**: For read-only agent scope, idempotency is informational only. If scope expands to write-enabled, `AddItem` non-idempotency becomes a BLOCKER.
- **Recommendation**: Implement idempotency keys for `AddItem` before expanding agent scope to write-enabled.
- **Evidence**: `src/cartservice/src/cartstore/RedisCartStore.cs` (AddItemAsync)

### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: Istio AuthorizationPolicy is enabled (`authorizationPolicies.create: true` in `helm-chart/values.yaml`), providing service-mesh-level identity verification using mTLS between pods. Callers are restricted to `frontend` and `checkoutservice` service accounts. Istio sidecars are enabled (`sidecars.create: true`), ensuring mTLS is enforced. The gRPC server in `Startup.cs` uses standard ASP.NET Core Kestrel without application-layer TLS, but the Istio sidecar terminates mTLS before traffic reaches the application — standard Istio pattern.
- **Implication**: Machine identity is authenticated at the mesh layer via mTLS with per-service principal attribution. This satisfies the core requirement for agent identity verification.
- **Recommendation**: For defense in depth, consider implementing a gRPC interceptor that extracts the Istio peer identity from request headers for application-level audit logging.
- **Evidence**: `helm-chart/values.yaml` (`authorizationPolicies.create: true`, `sidecars.create: true`), `helm-chart/templates/cartservice.yaml` (AuthorizationPolicy section), `src/cartservice/src/Startup.cs`

### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Archetype-Calibrated**: stateful-crud — evaluated as RISK by default, but cart data is keyed by `user_id` passed in each request (explicit user context), not by caller identity. The service does not parse JWTs or propagate identity — it trusts the `user_id` field in the gRPC request. Istio mTLS provides implicit caller identity at the mesh layer.
- **Finding**: No JWT parsing, no token exchange, no OAuth on-behalf-of flows. User context is passed via the `user_id` field in each gRPC request. The service trusts this field without validation. Istio mTLS provides caller identity at the mesh layer.
- **Implication**: An agent calling `GetCart` with a `user_id` can access any user's cart. The `user_id` field is the only access control — no verification that the caller is authorized to access that specific user's cart. For read-only scope, this is an architecture input rather than a deployment gate.
- **Recommendation**: Implement user_id validation against the caller's identity (e.g., extract user context from Istio headers and verify it matches the requested user_id). Critical before expanding to write-enabled scope.
- **Evidence**: `src/cartservice/src/services/CartService.cs`, `protos/demo.proto` (user_id field), `helm-chart/values.yaml`

### STATE-Q2: Queryable Current State
- **Severity**: INFO
- **Finding**: `GetCart` RPC returns the full current cart state for a given `user_id`, including all items with product IDs and quantities. The `Cart` message in the shared proto includes an `updated_at` timestamp. State is directly queryable via a single RPC call. Positive finding.
- **Implication**: Agents can inspect current cart state before taking action. The `GetCart` RPC provides a complete read-before-write capability.
- **Recommendation**: No action needed. Ensure `updated_at` is populated in the response (currently only in shared proto, not local proto).
- **Evidence**: `protos/demo.proto` (GetCart RPC, Cart message), `src/cartservice/src/cartstore/RedisCartStore.cs` (GetCartAsync)

### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: INFO
- **Finding**: The cartservice calls Redis as its only external dependency. No circuit breaker pattern is implemented — `RedisCartStore.cs` catches exceptions and throws `RpcException` immediately. No retry logic, no exponential backoff, no timeout configuration on the Redis client. The `IDistributedCache` abstraction provides basic connection pooling via StackExchange.Redis.
- **Implication**: A Redis outage causes immediate gRPC failures for all cart operations. No graceful degradation. For a single-dependency service, the blast radius is contained to cart functionality.
- **Recommendation**: Add Polly circuit breaker around Redis calls. Configure Redis client timeouts. Consider a fallback to in-memory cache during Redis outages.
- **Evidence**: `src/cartservice/src/cartstore/RedisCartStore.cs`, `src/cartservice/src/Startup.cs` (Redis configuration)

### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Cart operations are scoped to individual users (`user_id` key). No bulk operations. `EmptyCart` affects only one user's cart. No cross-user operations. Redis data is ephemeral (emptyDir volume).
- **Implication**: Blast radius is inherently limited to a single user's cart per operation. Transaction limits not applicable for read-only scope.
- **Recommendation**: Implement transaction limits if write operations are enabled for agents (e.g., max items per AddItem call, max EmptyCart calls per hour per agent).
- **Evidence**: `src/cartservice/src/cartstore/RedisCartStore.cs`, `src/cartservice/src/services/CartService.cs`

### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: INFO
- **Finding**: HPA is configured for auto-scaling based on metrics. K8s resource limits are defined (200m CPU request, 300m limit; 128Mi memory request, 256Mi limit). Monitoring alerts are configured for error rates and latency. Redis has resource limits (125m CPU, 256Mi memory). Redis uses emptyDir volume — no persistent storage bottleneck.
- **Implication**: Auto-scaling and monitoring are in place. P0 service has capacity planning infrastructure. Redis emptyDir means no disk I/O bottleneck but also no persistence guarantee.
- **Recommendation**: Load test with agent-pattern traffic (burst reads, concurrent GetCart calls). Validate HPA scaling thresholds are appropriate for agent traffic patterns.
- **Evidence**: `helm-chart/values.yaml` (cartService.resources), `kubernetes-manifests/cartservice.yaml` (resource limits)

### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO
- **Finding**: Data classification exists at multiple levels: (1) `protos/demo.proto` has inline comments classifying Cart as `INTERNAL` and `user_id` as `PII-CANDIDATE`, (2) `DATA_CLASSIFICATION.md` formally classifies cartservice as `INTERNAL / PII-CANDIDATE` with `user_id` as the sensitive field, (3) Agent Access Policy in DATA_CLASSIFICATION.md defines read-only agent access rules. Positive finding.
- **Implication**: Data classification is documented and consistent across proto and documentation. `PII-CANDIDATE` status for `user_id` means the field requires monitoring — if user_id format is confirmed as PII (e.g., email), controls must be tightened.
- **Recommendation**: Resolve the PII-CANDIDATE status: determine whether `user_id` contains PII (email, phone) or is an opaque identifier. Update classification accordingly.
- **Evidence**: `protos/demo.proto` (data classification comments), `DATA_CLASSIFICATION.md`

### DATA-Q3: Selective Query Support
- **Severity**: INFO
- **Finding**: `GetCart` returns the complete cart for a single user — no pagination needed as carts are bounded by practical shopping limits. No list/query endpoint that returns multiple users' carts. No unbounded result set risk. The API is inherently selective (one user, one cart).
- **Implication**: No unbounded query risk. Cart size is naturally bounded. No pagination needed for agent consumption.
- **Recommendation**: No action needed. If a "list all carts" admin endpoint is added, implement pagination.
- **Evidence**: `protos/demo.proto` (GetCart RPC), `src/cartservice/src/cartstore/RedisCartStore.cs`

### DATA-Q4: System of Record Designations
- **Severity**: INFO
- **Finding**: `protos/demo.proto` explicitly designates cartservice as the system of record for cart state (`System of Record: cartservice owns cart state (Redis-backed)`). `DATA_CLASSIFICATION.md` confirms cartservice owns shopping cart state. No conflicting ownership claims. Positive finding.
- **Implication**: Clear system-of-record designation. Agents know cartservice is authoritative for cart data. No cross-system conflict resolution needed.
- **Recommendation**: No action needed.
- **Evidence**: `protos/demo.proto` (system of record comment), `DATA_CLASSIFICATION.md`

### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: INFO
- **Finding**: The shared `protos/demo.proto` includes `updated_at` (google.protobuf.Timestamp) on the `Cart` message. However, the local `Cart.proto` compiled by cartservice does not include this field. Redis provides no built-in temporal metadata. No `Cache-Control` or freshness headers in gRPC responses. No consistency level signaling.
- **Implication**: Temporal metadata is defined in the shared proto but not implemented in the compiled service. Agents cannot determine when a cart was last modified.
- **Recommendation**: Implement `updated_at` population in `RedisCartStore.cs` when writing cart state. Align local proto with shared proto to include the timestamp field.
- **Evidence**: `protos/demo.proto` (updated_at field), `src/cartservice/src/protos/Cart.proto` (missing updated_at), `src/cartservice/src/cartstore/RedisCartStore.cs`

### DATA-Q6: PII Redaction in Logs
- **Severity**: INFO
- **Finding**: `RedisCartStore.cs` logs `userId` in plaintext via `Console.WriteLine` (e.g., `AddItemAsync called with userId={userId}`). The `user_id` field is classified as PII-CANDIDATE. No log scrubbing middleware. No PII masking. Structured logging not configured — using raw `Console.WriteLine`.
- **Implication**: If `user_id` is confirmed as PII, current logging creates a compliance risk. Even as PII-CANDIDATE, logging it in plaintext is a concern.
- **Recommendation**: Replace `Console.WriteLine` with structured logging (e.g., Serilog or Microsoft.Extensions.Logging). Implement PII redaction for `userId` field. At minimum, hash or truncate the value in logs.
- **Evidence**: `src/cartservice/src/cartstore/RedisCartStore.cs` (Console.WriteLine calls)

### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: INFO
- **Finding**: Shared proto uses versioned package `hipstershop.v1`. `buf.yaml` exists with both `lint` (STANDARD) and `breaking` (FILE) rules configured. Proto defines typed schemas with data classification comments, timestamps, and field numbers. Breaking change detection tooling is in place but not yet integrated into CI.
- **Implication**: Schema versioning is established. Proto versioning enables safe evolution. `buf` tooling with breaking change rules provides a path to automated contract enforcement.
- **Recommendation**: Integrate `buf breaking` into CI pipeline (tracked under ENG-Q2). Consolidate proto sources.
- **Evidence**: `protos/demo.proto` (`hipstershop.v1`), `protos/buf.yaml`

### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: INFO
- **Finding**: OpenTelemetry is enabled by default (`tracing: true`, `metrics: true` in `helm-chart/values.yaml`). OpenTelemetry Collector is deployed (`opentelemetryCollector.create: true`). Istio sidecar provides automatic trace context propagation for gRPC traffic. However, application logging uses `Console.WriteLine` (unstructured) rather than structured JSON logging. No correlation_id/request_id in application logs.
- **Implication**: Distributed tracing is operational via OpenTelemetry + Istio. The gap is in application-level logging — `Console.WriteLine` produces unstructured output that is harder to correlate with traces.
- **Recommendation**: Replace `Console.WriteLine` with structured logging (Serilog or Microsoft.Extensions.Logging with JSON formatter). Add trace_id to log entries for log-to-trace correlation.
- **Evidence**: `helm-chart/values.yaml` (`tracing: true`, `opentelemetryCollector.create: true`, `metrics: true`), `src/cartservice/src/cartstore/RedisCartStore.cs` (Console.WriteLine)

### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: INFO
- **Finding**: Monitoring alerts are configured for error rates and latency. Metrics collection is enabled (`metrics: true`). K8s health probes (liveness and readiness) provide pod availability monitoring. HPA is configured for auto-scaling based on metrics. OpenTelemetry metrics provide service-level observability.
- **Implication**: Alerting infrastructure is in place. Service degradation will be detected before agents cascade failures. Positive finding.
- **Recommendation**: Tune alert thresholds based on agent traffic patterns during pilot. Add Redis-specific alerts (connection failures, latency).
- **Evidence**: `kubernetes-manifests/cartservice.yaml` (health probes), `helm-chart/values.yaml` (`metrics: true`)

### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: INFO
- **Finding**: Comprehensive IaC across multiple layers: K8s manifests, Helm chart with templates, Skaffold. CODEOWNERS enforces peer review. GitHub Actions CI on PRs. AuthorizationPolicies, NetworkPolicies, and Sidecars are all defined in IaC and enabled. HPA and monitoring alerts defined in IaC. No drift detection configured, but Helm-based deployment provides implicit reconciliation.
- **Implication**: Infrastructure governance is strong — IaC coverage is comprehensive and peer review is enforced. The drift detection gap is minor for a K8s-native deployment where Helm reconciliation provides implicit drift correction on deploy.
- **Recommendation**: Implement drift detection or GitOps (ArgoCD/Flux) for continuous reconciliation.
- **Evidence**: `kubernetes-manifests/cartservice.yaml`, `helm-chart/templates/cartservice.yaml`, `.github/workflows/ci-pr.yaml`, `helm-chart/values.yaml`

### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: gRPC Protocol Buffers — strongly-typed binary format with explicit types, field numbers, and data classification comments. `Cart` message includes `user_id`, repeated `CartItem` (product_id + quantity), and `updated_at` timestamp (in shared proto).
- **Implication**: Protobuf is more structured than JSON. Excellent for agent integration with auto-generated client code.
- **Recommendation**: No action needed.
- **Evidence**: `protos/demo.proto`

### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: No event emission for cart state changes. `AddItem`, `EmptyCart` modify Redis state directly with no event publication. No SNS/SQS/EventBridge/Kafka integration. No webhook endpoints. No CDC pipeline on Redis.
- **Implication**: Agents cannot subscribe to cart change events. Must poll `GetCart` to detect changes. For a shopping cart with short-lived state, polling is acceptable.
- **Recommendation**: Consider publishing cart change events to a message bus if proactive agent workflows are needed (e.g., abandoned cart detection).
- **Evidence**: `src/cartservice/src/cartstore/RedisCartStore.cs`, `src/cartservice/src/services/CartService.cs`

### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: EnvoyFilter rate limiting is configured at the mesh level. No rate limit headers in gRPC responses. No `X-RateLimit-Remaining` or `Retry-After` metadata in gRPC trailing metadata. Rate limits are not documented in proto or API documentation.
- **Implication**: Agents cannot self-throttle based on server-side rate limit signals. Rate limiting exists but is invisible to callers.
- **Recommendation**: Add gRPC trailing metadata with rate limit status. Document rate limits in proto comments or service documentation.
- **Evidence**: `src/cartservice/src/services/CartService.cs`, `kubernetes-manifests/cartservice.yaml`

### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics. Cart data is user-generated (items added by users). No validation of product_id existence or quantity ranges in `AddItemAsync`. No duplicate detection. Quality is determined by caller input.
- **Implication**: Invalid product IDs or negative quantities could be stored. No data quality monitoring.
- **Recommendation**: Add input validation (verify product_id exists, quantity > 0). Add metrics for cart data anomalies.
- **Evidence**: `src/cartservice/src/cartstore/RedisCartStore.cs` (AddItemAsync — no input validation)

### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Clear semantic names: `user_id`, `product_id`, `quantity`, `items`, `updated_at`. No abbreviations. Data classification comments in proto. Message names are descriptive (`AddItemRequest`, `GetCartRequest`, `EmptyCartRequest`, `Cart`, `CartItem`).
- **Implication**: LLMs can interpret fields directly. No translation needed. Excellent semantic clarity.
- **Recommendation**: No action needed.
- **Evidence**: `protos/demo.proto`

### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: `DATA_CLASSIFICATION.md` serves as a formal data catalog with service ownership, classification levels, sensitive fields, and agent access policies. Proto file includes inline data classification and system-of-record comments. No formal API catalog (Backstage, Swagger Hub).
- **Implication**: Documentation-level catalog exists and is comprehensive for the service. Sufficient for agent tool definition.
- **Recommendation**: Register in organization API catalog if part of larger data mesh. Consider Backstage integration.
- **Evidence**: `DATA_CLASSIFICATION.md`, `protos/demo.proto`

### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics. No cart abandonment rate, no items-per-cart metrics, no cart conversion tracking. Operational metrics via OpenTelemetry provide infrastructure-level visibility only.
- **Implication**: No business outcome monitoring. Cannot measure whether agent interactions produce good cart management outcomes.
- **Recommendation**: Publish metrics for cart operations (add rate, empty rate, average items per cart, cart-to-checkout conversion).
- **Evidence**: `src/cartservice/src/services/CartService.cs`

### ENG-Q4: API Test Coverage
- **Severity**: INFO
- **Finding**: Three xUnit integration tests exist in `CartServiceTests.cs`: (1) `GetItem_NoAddItemBefore_EmptyCartReturned`, (2) `AddItem_ItemExists_Updated`, (3) `AddItem_New_Inserted`. Tests use `TestServer` with in-memory gRPC client. Tests run in CI (`dotnet test src/cartservice/`). Tests cover basic CRUD operations but not error cases, edge cases, or concurrent access.
- **Implication**: Basic test coverage exists — significantly better than zero. Tests validate happy-path CRUD operations. Missing: error handling tests, Redis failure tests, concurrent access tests, empty/null input tests.
- **Recommendation**: Add tests for error scenarios (Redis unavailable), edge cases (empty user_id, negative quantity), and concurrent AddItem calls.
- **Evidence**: `src/cartservice/tests/CartServiceTests.cs`, `.github/workflows/ci-pr.yaml` (C# Unit Tests step)

### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: INFO
- **Finding**: Redis uses `emptyDir` volume — data is stored in memory/tmpfs on the node. No persistent disk, no encryption-at-rest configuration needed for ephemeral in-memory storage. If external Redis (Memorystore, ElastiCache) is used, encryption at rest depends on the managed service configuration. The `externalRedisTlsOrigination` option in Helm values supports TLS for external Redis connections.
- **Implication**: In-cluster Redis with emptyDir has no encryption-at-rest concern (data is ephemeral and in-memory). External Redis configurations should verify encryption at rest is enabled on the managed service.
- **Recommendation**: If migrating to external Redis (Memorystore/ElastiCache), ensure encryption at rest is enabled. Document the ephemeral nature of in-cluster Redis data.
- **Evidence**: `helm-chart/templates/cartservice.yaml` (Redis emptyDir volume), `helm-chart/values.yaml` (`cartDatabase` configuration, `externalRedisTlsOrigination`)

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: Well-documented gRPC interface in `protos/demo.proto` with `CartService` defining `AddItem`, `GetCart`, and `EmptyCart` RPCs. Proto uses versioned package `hipstershop.v1` with data classification comments and `updated_at` timestamp. Implemented in C# (`CartService.cs`, `RedisCartStore.cs`). Positive finding.
- **Gap**: None — BLOCKER criteria satisfied.
- **Recommendation**: No remediation needed.
- **Evidence**: `protos/demo.proto`, `src/cartservice/src/services/CartService.cs`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK
- **Finding**: Shared `protos/demo.proto` is a rich machine-readable spec with versioned package, data classification, and timestamps. Local `src/cartservice/src/protos/Cart.proto` is the compiled source — it uses unversioned `hipstershop` package and lacks classification/timestamps. Two divergent proto sources.
- **Gap**: Compiled proto lacks versioning and data classification. Divergent proto sources.
- **Recommendation**: Consolidate to single proto source. Update `cartservice.csproj` to compile from shared proto.
- **Evidence**: `protos/demo.proto`, `src/cartservice/src/protos/Cart.proto`, `src/cartservice/src/cartservice.csproj`

#### API-Q3: Structured Error Responses
- **Severity**: RISK
- **Finding**: All errors throw `RpcException` with `StatusCode.FailedPrecondition` and raw exception in message. Single status code for all failure modes.
- **Gap**: Agents cannot distinguish retriable from terminal errors.
- **Recommendation**: Differentiate error types with appropriate gRPC status codes.
- **Evidence**: `src/cartservice/src/cartstore/RedisCartStore.cs`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: `AddItem` is additive (not idempotent). `EmptyCart` is idempotent. `GetCart` is read-only. No idempotency keys.
- **Gap**: `AddItem` non-idempotency is informational for read-only scope.
- **Recommendation**: Implement idempotency keys before expanding to write-enabled scope.
- **Evidence**: `src/cartservice/src/cartstore/RedisCartStore.cs`

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
- **Finding**: No event emission for cart state changes. No message bus integration. No webhook endpoints.
- **Gap**: Agents must poll `GetCart` to detect changes.
- **Recommendation**: Consider publishing cart change events if proactive agent workflows are needed.
- **Evidence**: `src/cartservice/src/cartstore/RedisCartStore.cs`, `src/cartservice/src/services/CartService.cs`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: EnvoyFilter rate limiting configured at mesh level. No rate limit headers in gRPC responses. Rate limits not documented.
- **Gap**: Agents cannot self-throttle based on server-side signals.
- **Recommendation**: Add gRPC trailing metadata with rate limit status.
- **Evidence**: `src/cartservice/src/services/CartService.cs`, `kubernetes-manifests/cartservice.yaml`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: Istio AuthorizationPolicy is enabled (`authorizationPolicies.create: true`), providing mTLS-based identity verification. Callers restricted to `frontend` and `checkoutservice` service accounts. Istio sidecars enabled (`sidecars.create: true`). Standard Istio pattern — sidecar terminates mTLS before traffic reaches the application.
- **Gap**: None — mesh-level mTLS with per-service AuthorizationPolicy satisfies machine identity authentication.
- **Recommendation**: For defense in depth, extract Istio peer identity from request headers for application-level audit logging.
- **Evidence**: `helm-chart/values.yaml` (`authorizationPolicies.create: true`, `sidecars.create: true`), `helm-chart/templates/cartservice.yaml`, `src/cartservice/src/Startup.cs`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicy restricts callers to `frontend` and `checkoutservice`. Both have access to all three RPCs. No agent-specific service accounts.
- **Gap**: No per-RPC scoping for different callers. No agent-specific permissions.
- **Recommendation**: Create agent-specific service accounts with per-RPC AuthorizationPolicy rules.
- **Evidence**: `helm-chart/templates/cartservice.yaml`, `helm-chart/values.yaml`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicy defines per-path rules. No application-layer action-level authorization in `CartService.cs`.
- **Gap**: No application-layer authorization. Mesh bypass exposes all RPCs.
- **Recommendation**: Implement gRPC server interceptor for action-level authorization.
- **Evidence**: `src/cartservice/src/services/CartService.cs`, `helm-chart/templates/cartservice.yaml`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: No JWT parsing, token exchange, or OAuth on-behalf-of flows. User context passed via `user_id` field in gRPC requests. Service trusts `user_id` without validation. Istio mTLS provides caller identity at mesh layer.
- **Gap**: No verification that caller is authorized to access the specific user's cart. `user_id` is trusted without validation.
- **Recommendation**: Implement user_id validation against caller identity before expanding to write-enabled scope.
- **Evidence**: `src/cartservice/src/services/CartService.cs`, `protos/demo.proto`, `helm-chart/values.yaml`

#### AUTH-Q5: Credential Management
- **Severity**: RISK
- **Finding**: Redis has no authentication. Connection string is `redis-cart:6379` via env var. Secret Manager dependency exists but is unused.
- **Gap**: No Redis authentication. No credential management framework.
- **Recommendation**: Enable Redis AUTH. Use Secret Manager for credential management.
- **Evidence**: `src/cartservice/src/Startup.cs`, `src/cartservice/src/cartservice.csproj`, `helm-chart/values.yaml`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: No audit logging. `Console.WriteLine` operational messages only. No principal attribution. PII-CANDIDATE `userId` logged in plaintext. OpenTelemetry tracing enabled but not audit-grade.
- **Gap**: No immutable audit trail. PII-CANDIDATE field in plaintext logs.
- **Recommendation**: Add structured audit logging with caller identity. Forward to immutable store. Redact userId.
- **Evidence**: `src/cartservice/src/cartstore/RedisCartStore.cs`, `helm-chart/values.yaml`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicy provides manual suspension mechanism. NetworkPolicies enabled. No automated suspension.
- **Gap**: No automated or rapid suspension mechanism.
- **Recommendation**: Implement automated suspension via AuthorizationPolicy updates triggered by anomaly detection.
- **Evidence**: `helm-chart/templates/cartservice.yaml`, `helm-chart/values.yaml`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: Cart operations are individual Redis writes. `AddItemAsync` uses non-atomic read-modify-write. No saga pattern, no undo endpoints, no compensation logic.
- **Gap**: Non-atomic read-modify-write. No compensation mechanisms.
- **Recommendation**: Implement Redis WATCH/MULTI for atomicity. Add cart history for compensation.
- **Evidence**: `src/cartservice/src/cartstore/RedisCartStore.cs`

#### STATE-Q2: Queryable Current State
- **Severity**: INFO
- **Finding**: `GetCart` RPC returns full current cart state for a given `user_id`. Directly queryable. Shared proto includes `updated_at` timestamp. Positive finding.
- **Gap**: `updated_at` not implemented in compiled service (local proto missing the field).
- **Recommendation**: Implement `updated_at` population. Align local proto with shared proto.
- **Evidence**: `protos/demo.proto`, `src/cartservice/src/cartstore/RedisCartStore.cs`

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled AND service has persistent state
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: INFO
- **Finding**: No circuit breaker on Redis calls. Exceptions caught and re-thrown as `RpcException`. No retry logic, no timeout configuration. `IDistributedCache` provides connection pooling.
- **Gap**: No graceful degradation on Redis outage.
- **Recommendation**: Add Polly circuit breaker. Configure Redis client timeouts.
- **Evidence**: `src/cartservice/src/cartstore/RedisCartStore.cs`, `src/cartservice/src/Startup.cs`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK
- **Finding**: EnvoyFilter rate limiting at mesh level. No application-level rate limiting. HPA for auto-scaling. K8s resource limits.
- **Gap**: No application-level rate limiting as defense in depth.
- **Recommendation**: Add ASP.NET Core rate limiting middleware. Tune EnvoyFilter for agent traffic.
- **Evidence**: `kubernetes-manifests/cartservice.yaml`, `helm-chart/values.yaml`, `src/cartservice/src/Startup.cs`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Operations scoped to individual users. No bulk operations. Ephemeral Redis data.
- **Gap**: None for read-only scope.
- **Recommendation**: Implement transaction limits if write operations enabled for agents.
- **Evidence**: `src/cartservice/src/cartstore/RedisCartStore.cs`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: INFO
- **Finding**: HPA configured. Resource limits defined. Monitoring alerts configured. Redis has resource limits. Ephemeral storage — no disk I/O bottleneck.
- **Gap**: No agent-specific load testing.
- **Recommendation**: Load test with agent-pattern traffic. Validate HPA thresholds.
- **Evidence**: `helm-chart/values.yaml`, `kubernetes-manifests/cartservice.yaml`

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
- **Finding**: Skaffold local dev. CI per-PR ephemeral namespaces. No persistent agent testing environment with Redis state.
- **Gap**: No dedicated agent testing environment.
- **Recommendation**: Create persistent staging namespace with production-equivalent Redis configuration.
- **Evidence**: `skaffold.yaml`, `src/cartservice/src/Dockerfile`, `.github/workflows/ci-pr.yaml`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO
- **Finding**: Data classification exists in proto (inline comments) and `DATA_CLASSIFICATION.md`. Cart classified as `INTERNAL / PII-CANDIDATE`. `user_id` classified as `PII-CANDIDATE`. Agent access policy defined. Positive finding.
- **Gap**: None — classification exists and is consistent.
- **Recommendation**: Resolve PII-CANDIDATE status for `user_id`.
- **Evidence**: `protos/demo.proto`, `DATA_CLASSIFICATION.md`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: Cart data contains PII-CANDIDATE `user_id`. Redis uses ephemeral emptyDir. No explicit residency documentation.
- **Gap**: No formal data residency documentation for PII-CANDIDATE data.
- **Recommendation**: Document data residency posture. Determine user_id PII status.
- **Evidence**: `protos/demo.proto`, `DATA_CLASSIFICATION.md`, `helm-chart/templates/cartservice.yaml`

#### DATA-Q3: Selective Query Support
- **Severity**: INFO
- **Finding**: `GetCart` returns one user's cart. No unbounded result sets. Inherently selective.
- **Gap**: None.
- **Recommendation**: No action needed.
- **Evidence**: `protos/demo.proto`, `src/cartservice/src/cartstore/RedisCartStore.cs`

#### DATA-Q4: System of Record Designations
- **Severity**: INFO
- **Finding**: Explicitly designated as system of record for cart state in proto and DATA_CLASSIFICATION.md. Positive finding.
- **Gap**: None.
- **Recommendation**: No action needed.
- **Evidence**: `protos/demo.proto`, `DATA_CLASSIFICATION.md`

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: INFO
- **Finding**: `updated_at` defined in shared proto but not in compiled local proto. Not implemented in RedisCartStore. No freshness signaling.
- **Gap**: Temporal metadata defined but not implemented.
- **Recommendation**: Implement `updated_at` population. Align local proto with shared proto.
- **Evidence**: `protos/demo.proto`, `src/cartservice/src/protos/Cart.proto`, `src/cartservice/src/cartstore/RedisCartStore.cs`

#### DATA-Q6: PII Redaction in Logs
- **Severity**: INFO
- **Finding**: `userId` (PII-CANDIDATE) logged in plaintext via `Console.WriteLine`. No log scrubbing. No structured logging.
- **Gap**: PII-CANDIDATE field in plaintext logs.
- **Recommendation**: Implement structured logging with PII redaction for userId.
- **Evidence**: `src/cartservice/src/cartstore/RedisCartStore.cs`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics. No input validation on product_id or quantity. Quality determined by caller input.
- **Gap**: No input validation or quality monitoring.
- **Recommendation**: Add input validation (product_id exists, quantity > 0).
- **Evidence**: `src/cartservice/src/cartstore/RedisCartStore.cs`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: INFO
- **Finding**: Shared proto uses `hipstershop.v1`. `buf.yaml` with lint and breaking rules configured. Breaking change detection not yet in CI.
- **Gap**: `buf breaking` not in CI (tracked under ENG-Q2).
- **Recommendation**: Integrate `buf breaking` into CI pipeline.
- **Evidence**: `protos/demo.proto`, `protos/buf.yaml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Clear semantic names: `user_id`, `product_id`, `quantity`, `items`, `updated_at`. No abbreviations. Data classification comments.
- **Gap**: None.
- **Recommendation**: No action needed.
- **Evidence**: `protos/demo.proto`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: `DATA_CLASSIFICATION.md` serves as formal data catalog. Proto includes inline classification and system-of-record comments. No formal API catalog.
- **Gap**: No formal API catalog (Backstage, etc.).
- **Recommendation**: Register in organization API catalog.
- **Evidence**: `DATA_CLASSIFICATION.md`, `protos/demo.proto`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: INFO
- **Finding**: OpenTelemetry enabled (`tracing: true`, `metrics: true`). OTel Collector deployed. Istio sidecar provides trace propagation. Application uses `Console.WriteLine` (unstructured). No trace_id in application logs.
- **Gap**: Unstructured application logging. No log-to-trace correlation.
- **Recommendation**: Replace `Console.WriteLine` with structured logging. Add trace_id to log entries.
- **Evidence**: `helm-chart/values.yaml`, `src/cartservice/src/cartstore/RedisCartStore.cs`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: INFO
- **Finding**: Monitoring alerts configured. Metrics enabled. Health probes active. HPA configured. OpenTelemetry metrics operational.
- **Gap**: None — alerting infrastructure is in place.
- **Recommendation**: Tune alert thresholds for agent traffic. Add Redis-specific alerts.
- **Evidence**: `kubernetes-manifests/cartservice.yaml`, `helm-chart/values.yaml`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics. No cart abandonment, items-per-cart, or conversion tracking.
- **Gap**: No business outcome monitoring.
- **Recommendation**: Publish cart operation metrics (add rate, empty rate, average items per cart).
- **Evidence**: `src/cartservice/src/services/CartService.cs`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: INFO
- **Finding**: Comprehensive IaC: K8s manifests, Helm chart, Skaffold. CODEOWNERS enforces peer review. GitHub Actions CI. AuthorizationPolicies, NetworkPolicies, Sidecars all in IaC. HPA and alerts in IaC. No drift detection.
- **Gap**: Drift detection missing (minor for Helm-based deployment).
- **Recommendation**: Implement drift detection or GitOps.
- **Evidence**: `kubernetes-manifests/cartservice.yaml`, `helm-chart/templates/cartservice.yaml`, `.github/workflows/ci-pr.yaml`, `helm-chart/values.yaml`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK
- **Finding**: CI exists. C# unit tests in CI. Proto versioned. `buf.yaml` with breaking rules. No `buf breaking` in CI. No service-specific contract tests.
- **Gap**: No automated breaking change detection in CI.
- **Recommendation**: Add `buf breaking` to CI. Add CartService contract tests.
- **Evidence**: `cloudbuild.yaml`, `.github/workflows/ci-pr.yaml`, `protos/buf.yaml`, `protos/demo.proto`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK
- **Finding**: K8s Deployment with rollout history. Skaffold deployment. Manual rollback only. No canary or automated rollback. Monitoring alerts can trigger manual rollback faster.
- **Gap**: No automated rollback on service degradation.
- **Recommendation**: Configure automated rollback (Flagger, Argo Rollouts).
- **Evidence**: `skaffold.yaml`, `kubernetes-manifests/cartservice.yaml`

#### ENG-Q4: API Test Coverage
- **Severity**: INFO
- **Finding**: Three xUnit integration tests covering basic CRUD operations. Tests run in CI. Missing: error handling, edge cases, concurrent access tests.
- **Gap**: No error scenario or edge case tests.
- **Recommendation**: Add error, edge case, and concurrency tests.
- **Evidence**: `src/cartservice/tests/CartServiceTests.cs`, `.github/workflows/ci-pr.yaml`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: INFO
- **Finding**: Redis uses emptyDir (ephemeral, in-memory). No persistent disk. Helm supports external Redis with TLS origination. In-cluster Redis has no encryption-at-rest concern.
- **Gap**: None for in-cluster ephemeral Redis.
- **Recommendation**: Ensure encryption at rest if migrating to external Redis.
- **Evidence**: `helm-chart/templates/cartservice.yaml`, `helm-chart/values.yaml`

---

## Evidence Index

### Infrastructure as Code
| File | Questions Referenced |
|------|---------------------|
| `kubernetes-manifests/cartservice.yaml` | AUTH-Q1, AUTH-Q2, STATE-Q5, STATE-Q7, OBS-Q2, API-Q8, ENG-Q1, ENG-Q3 |
| `helm-chart/templates/cartservice.yaml` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q5, AUTH-Q6, AUTH-Q7, DATA-Q2, ENG-Q1, ENG-Q5, STATE-Q7 |
| `helm-chart/values.yaml` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q6, AUTH-Q7, OBS-Q1, OBS-Q2, ENG-Q1, STATE-Q5, STATE-Q7 |

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `src/cartservice/src/services/CartService.cs` | API-Q1, API-Q7, API-Q8, AUTH-Q3, AUTH-Q4, STATE-Q6, OBS-Q3 |
| `src/cartservice/src/cartstore/RedisCartStore.cs` | API-Q2, API-Q3, API-Q4, API-Q7, AUTH-Q6, STATE-Q1, STATE-Q2, STATE-Q4, STATE-Q5, STATE-Q6, DATA-Q3, DATA-Q5, DATA-Q6, DATA-Q7, OBS-Q1 |
| `src/cartservice/src/cartstore/ICartStore.cs` | API-Q1 |
| `src/cartservice/src/Startup.cs` | AUTH-Q1, AUTH-Q5, STATE-Q4, STATE-Q5 |
| `src/cartservice/src/cartservice.csproj` | API-Q2, AUTH-Q5 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `protos/demo.proto` | API-Q1, API-Q2, API-Q4, API-Q5, AUTH-Q4, STATE-Q2, DATA-Q1, DATA-Q2, DATA-Q3, DATA-Q4, DATA-Q5, DISC-Q1, DISC-Q2, DISC-Q3, ENG-Q2 |
| `src/cartservice/src/protos/Cart.proto` | API-Q2, DATA-Q5 |
| `protos/buf.yaml` | API-Q2, DISC-Q1, ENG-Q2 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `cloudbuild.yaml` | ENG-Q2 |
| `skaffold.yaml` | HITL-Q3, ENG-Q1, ENG-Q3 |
| `.github/workflows/ci-pr.yaml` | HITL-Q3, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `src/cartservice/src/Dockerfile` | HITL-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `src/cartservice/src/cartservice.csproj` | API-Q2, AUTH-Q5 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `DATA_CLASSIFICATION.md` | DATA-Q1, DATA-Q2, DATA-Q4, DISC-Q3 |

### Test Files
| File | Questions Referenced |
|------|---------------------|
| `src/cartservice/tests/CartServiceTests.cs` | ENG-Q4 |