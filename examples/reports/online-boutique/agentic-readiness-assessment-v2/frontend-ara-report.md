# Agentic Readiness Assessment Report

**Target**: services/microservices-demo/src/frontend
**Date**: 2026-04-16
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Service Archetype**: orchestrator (user-provided)
**Agent Scope**: read-only
**Priority**: P0
**Tags**: go, frontend, grpc
**Context**: Go web frontend serving the Online Boutique UI. Calls all backend services via gRPC.

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 1 | **RISKs**: 16 | **INFOs**: 23

Resolve all blockers before any agent deployment — including pilots. The single remaining BLOCKER (API-Q1) is the only BLOCKER in the entire Online Boutique portfolio: the frontend serves HTML pages via Go templates, not a machine-readable API. Agents cannot consume HTML responses as tool output. Estimated runway: 60–90 days to add a REST/JSON API layer or redirect agents to backend gRPC services directly.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 1 |
| RISK | 16 |
| INFO | 23 |
| N/A | 0 |
| Not Evaluated (extended) | 3 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 16
**Extended Questions Not Triggered**: 3
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: orchestrator (user-provided)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### API-Q1: Documented API Interface
- **Severity**: BLOCKER
- **Finding**: The frontend is an HTTP server that serves HTML pages rendered via Go `html/template`. Routes are defined in `main.go` using `gorilla/mux`: `/`, `/product/{id}`, `/cart`, `/cart/empty`, `/setCurrency`, `/logout`, `/cart/checkout`, `/assistant`. All handlers in `handlers.go` call `templates.ExecuteTemplate` to render HTML templates (`home.html`, `product.html`, `cart.html`, `order.html`, `error.html`). There is no REST/JSON API surface — responses are HTML documents, not structured data. The frontend does not expose a gRPC service definition (it is a gRPC *client* calling 7 backend services, not a gRPC server). Two minor exceptions exist: `/product-meta/{ids}` returns JSON for a single product, and `/bot` proxies JSON to the shopping assistant — but these are internal UI helpers, not a documented API. An agent cannot consume HTML pages as tool responses.
- **Gap**: No machine-readable API. Frontend serves HTML via Go templates. An agent would need to scrape HTML or use UI automation (RPA) to interact with this service — both are fragile and unscalable. This is the only remaining BLOCKER in the portfolio.
- **Remediation**:
  - **Immediate**: Add a REST/JSON API layer alongside the HTML frontend. Expose endpoints like `GET /api/v1/products`, `GET /api/v1/products/{id}`, `GET /api/v1/cart`, `POST /api/v1/cart/items`, `POST /api/v1/checkout` that return JSON responses. This can reuse the existing gRPC client calls in `rpc.go`.
  - **Target State**: REST/JSON API with OpenAPI spec, content negotiation (`Accept: application/json` returns JSON, `Accept: text/html` returns HTML), and structured error responses. Alternatively, direct agents to call backend gRPC services directly (bypassing the frontend), which is viable for read-only agents but loses the frontend's orchestration logic (currency conversion, cart aggregation, recommendation fetching).
  - **Estimated Effort**: Medium (60–90 days)
  - **Dependencies**: API-Q2 (OpenAPI spec), API-Q3 (structured errors)
- **Evidence**: `src/frontend/main.go` (mux routes returning HTML), `src/frontend/handlers.go` (`templates.ExecuteTemplate` calls), `src/frontend/templates/*.html`

---

## RISKs — Proceed with Compensating Controls

### API-Q2: Machine-Readable API Specification
- **Severity**: RISK
- **Finding**: No OpenAPI, AsyncAPI, or machine-readable specification exists for the frontend. The frontend consumes backend gRPC services defined in `protos/demo.proto` (package `hipstershop.v1`) but does not expose its own API specification. The HTML routes are not documented in any machine-readable format.
- **Gap**: No machine-readable spec for the frontend's HTTP interface. Agent tool definitions cannot be auto-generated.
- **Compensating Controls**:
  - Backend gRPC services have machine-readable proto specs (`protos/demo.proto`) that agents can consume directly
  - `buf.yaml` provides schema governance for backend proto definitions
- **Remediation Timeline**: 30–60 days (concurrent with API-Q1 remediation)
- **Recommendation**: Generate OpenAPI spec when REST/JSON API layer is added (API-Q1). Use annotations or code generation to keep spec in sync with implementation.
- **Evidence**: `src/frontend/main.go`, `protos/demo.proto`, `protos/buf.yaml`

### API-Q3: Structured Error Responses
- **Severity**: RISK
- **Finding**: Error handling in `handlers.go` uses `renderHTTPError` which renders an HTML error page via `templates.ExecuteTemplate(w, "error", ...)`. Errors are HTML pages, not structured JSON. An agent receiving an HTML error page cannot parse the error code or determine retryability.
- **Gap**: Error responses are HTML. No error code taxonomy, no retryable boolean, no machine-readable error body.
- **Compensating Controls**:
  - Backend gRPC services return gRPC status codes which are machine-readable
  - Agents calling backend services directly receive structured gRPC errors
- **Remediation Timeline**: 30–60 days
- **Recommendation**: When REST/JSON API is added (API-Q1), implement structured JSON error responses with error codes, messages, and retryable indicators.
- **Evidence**: `src/frontend/handlers.go` (`renderHTTPError`), `src/frontend/templates/error.html`

### API-Q6: Asynchronous Operation Support
- **Severity**: RISK
- **Finding**: The checkout flow (`placeOrderHandler`) calls `checkoutSvcConn.PlaceOrder` synchronously and renders an HTML order confirmation page. No job status polling endpoint or webhook callback exists. If the checkout gRPC call times out, the frontend renders an error page with no way to check whether the order was actually placed. No async pattern for long-running operations.
- **Gap**: No async operation support. Checkout is synchronous with no status tracking for timeout/failure scenarios.
- **Compensating Controls**:
  - Read-only agent scope means agents do not trigger checkout directly
  - Backend checkoutservice handles the multi-step workflow synchronously within the gRPC call
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a job status endpoint for checkout operations. Return an order reference ID that can be polled for completion status.
- **Evidence**: `src/frontend/handlers.go` (`placeOrderHandler`), `src/frontend/rpc.go`

### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicy restricts callers to known service accounts. The frontend has egress access to all 7 backend services via the Istio Sidecar configuration. No agent-specific service accounts are defined. No per-route authorization differentiation — all authorized callers can access all routes including `/cart/checkout`.
- **Gap**: No agent-specific service accounts. No per-route authorization. All callers have identical access to all frontend routes.
- **Compensating Controls**:
  - Istio AuthorizationPolicy restricts callers to known service accounts
  - NetworkPolicy restricts ingress to known pods
  - Read-only agent scope limits blast radius
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create agent-specific K8s service accounts. Add per-route AuthorizationPolicy rules restricting agent access to read-only routes.
- **Evidence**: `helm-chart/templates/frontend.yaml` (AuthorizationPolicy, NetworkPolicy, Sidecar)

### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicy allows GET and POST methods on port 8080 for all routes. No application-layer authorization — the Go HTTP server accepts all requests that pass mesh-level checks. No distinction between read operations (GET `/`, `/product/{id}`) and write operations (POST `/cart`, `/cart/checkout`).
- **Gap**: No action-level authorization at application or mesh layer. All authorized callers can perform all operations.
- **Compensating Controls**:
  - Istio mTLS ensures only mesh-authenticated callers reach the frontend
  - Read-only agent scope means agents should not trigger write operations
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement HTTP middleware checking caller identity (from Istio headers) and enforcing per-route, per-method authorization.
- **Evidence**: `src/frontend/main.go` (no auth middleware), `helm-chart/templates/frontend.yaml`

### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: RISK
- **Finding**: No JWT parsing, no token exchange, no user context headers. The frontend uses a cookie-based session ID (`shop_session-id`) generated as a random UUID in `middleware.go`. This session ID is passed as `user_id` to backend gRPC services. No distinction between agent-as-self vs agent-on-behalf-of-user. Istio mTLS provides caller service identity at the mesh layer but not user-level identity.
- **Gap**: No identity propagation through downstream service calls. Session ID is unauthenticated. An agent could impersonate any session.
- **Compensating Controls**:
  - Istio mTLS provides service-level caller identity
  - AuthorizationPolicy restricts callers to known service accounts
  - Read-only agent scope limits impersonation impact
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement JWT-based authentication. Derive user identity from tokens, not cookies. Distinguish agent-as-self vs agent-on-behalf-of-user in downstream gRPC metadata.
- **Evidence**: `src/frontend/middleware.go` (ensureSessionID), `src/frontend/rpc.go` (sessionID as user_id)

### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: Logrus provides structured JSON logging with request path, method, request ID, session ID, response status, and latency. OpenTelemetry tracing is enabled with `otelhttp.NewHandler` wrapping all routes. Istio access logs capture caller identity at the mesh layer. However, no principal attribution in application logs — logs do not identify which service account or agent made the request. No immutable storage configuration — logs are ephemeral container stdout.
- **Gap**: No principal attribution in application logs. No immutable audit trail. Istio access logs provide mesh-level identity but application logs do not.
- **Compensating Controls**:
  - OpenTelemetry traces provide request correlation across all 7 downstream services
  - Istio access logs capture mTLS peer identity
  - Structured JSON logging with request IDs enables log aggregation
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add caller identity (from Istio mTLS peer identity headers) to logrus fields. Forward logs to immutable store (CloudWatch Logs with retention, S3 with Object Lock).
- **Evidence**: `src/frontend/middleware.go` (logHandler), `src/frontend/main.go` (otelhttp handler), `helm-chart/values.yaml` (`tracing: true`)

### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicy provides a mechanism to deny specific service accounts. NetworkPolicies are enabled. However, no automated suspension mechanism — policy changes require Helm value updates or manual kubectl edits. The frontend is externally exposed via LoadBalancer service (`frontend-external`), increasing urgency.
- **Gap**: No automated or rapid suspension mechanism. External exposure increases risk.
- **Compensating Controls**:
  - Istio AuthorizationPolicy can deny specific service accounts (manual update)
  - K8s NetworkPolicy can block specific pods as emergency measure
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement automated suspension via AuthorizationPolicy updates triggered by anomaly detection. As a P0 externally-exposed service, rapid suspension is critical.
- **Evidence**: `helm-chart/templates/frontend.yaml` (AuthorizationPolicy, frontend-external LoadBalancer)

### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: The frontend orchestrates multi-step workflows: `placeOrderHandler` calls `checkoutSvcConn.PlaceOrder` which triggers a 7-step checkout workflow. The frontend itself has no compensation logic — it delegates to checkoutservice. If checkout fails mid-sequence, the frontend renders an HTML error page but does not attempt rollback.
- **Gap**: No compensation for multi-step checkout workflow. Frontend delegates to checkoutservice which also lacks compensation.
- **Compensating Controls**:
  - Read-only agent scope means agents do not directly trigger checkout
  - Single-step cart operations are inherently compensatable (add/remove items)
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement saga pattern in checkoutservice. Frontend compensation depends on backend capability.
- **Evidence**: `src/frontend/handlers.go` (placeOrderHandler), `src/frontend/rpc.go`

### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK
- **Finding**: The frontend calls 7 downstream gRPC services with no application-level circuit breakers and minimal timeout configuration. `mustConnGRPC` uses a 3-second connection timeout. Only `getAd` has an explicit per-call deadline (100ms). All other RPCs use the parent context with no explicit timeout. Istio sidecar provides mesh-level retry and timeout capabilities but no explicit configuration is present in the Helm chart.
- **Gap**: No application-level circuit breakers. Only 1 of 7 downstream RPCs has an explicit timeout. Downstream failures cascade to the frontend.
- **Compensating Controls**:
  - Istio sidecar can be configured with retry policies and timeouts at the mesh layer
  - K8s liveness/readiness probes restart unhealthy pods
  - HPA auto-scales frontend (1–10 replicas)
  - `getRecommendations` failure is gracefully handled (warning log, continues rendering)
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add per-call context deadlines to all gRPC RPCs. Implement circuit breakers (e.g., `sony/gobreaker` or Istio DestinationRule outlier detection).
- **Evidence**: `src/frontend/rpc.go` (getAd 100ms timeout, others none), `src/frontend/main.go` (mustConnGRPC 3s)

### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK
- **Finding**: An EnvoyFilter rate limiting configuration exists in `istio-manifests/rate-limit.yaml` targeting the `frontend` workload. It enforces a local rate limit of 100 requests per 60 seconds with `x-rate-limit-limit` and `x-rate-limit-remaining` response headers. However, the rate limit is global (not per-caller) — all callers share the same bucket. No per-agent rate differentiation.
- **Gap**: Rate limiting exists but is global, not per-caller. A single agent could consume the entire budget, starving human users.
- **Compensating Controls**:
  - EnvoyFilter provides baseline protection against runaway loops
  - Rate limit headers enable agent self-throttling
  - HPA auto-scales frontend (1–10 replicas) — each replica gets its own bucket
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Configure per-source-principal rate limits using Istio's rate limiting service. Differentiate agent traffic from human traffic.
- **Evidence**: `istio-manifests/rate-limit.yaml` (100 req/60s), `kubernetes-manifests/hpa.yaml`

### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: RISK
- **Finding**: HPA is configured with minReplicas=1, maxReplicas=10, targeting 70% CPU utilization. Monitoring alerts are configured for error rates and latency. However, no load testing results exist for agent traffic patterns. The frontend calls 7 downstream services — agent-induced fan-out could overwhelm downstream services even if the frontend itself scales. The frontend is externally exposed via LoadBalancer.
- **Gap**: No load testing for agent traffic patterns. Fan-out to 7 downstream services amplifies agent traffic.
- **Compensating Controls**:
  - HPA provides auto-scaling (1–10 replicas)
  - EnvoyFilter rate limiting provides baseline protection
  - Monitoring alerts detect degradation
  - All downstream services also have HPAs
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Conduct load testing with agent-like traffic patterns (burst, retry, fan-out). Ensure downstream services can handle amplified traffic.
- **Evidence**: `kubernetes-manifests/hpa.yaml`, `kubernetes-manifests/monitoring-alerts.yaml`, `istio-manifests/rate-limit.yaml`

### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: The frontend handles PCI + PII data in the checkout flow (credit card numbers, email, street address). `DATA_CLASSIFICATION.md` classifies the frontend as "PCI + PII (pass-through)". No explicit region pinning in the Helm chart or K8s manifests. Data residency depends on the cluster's deployment region. No documentation of applicable regulations.
- **Gap**: No explicit data residency policy. PCI + PII data flows through the frontend without documented residency controls.
- **Compensating Controls**:
  - K8s cluster deployment region provides implicit residency
  - Istio mTLS ensures data stays within the mesh
  - Frontend is pass-through — it does not persist PCI/PII data
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document data residency requirements. Pin deployment to specific regions. Ensure agent LLM calls do not transmit PCI/PII data cross-region.
- **Evidence**: `DATA_CLASSIFICATION.md`, `src/frontend/handlers.go` (placeOrderHandler — PCI/PII form fields)

### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK
- **Finding**: `placeOrderHandler` reads PII from form values (email, street_address, city, state, country) and PCI data (credit_card_number, credit_card_cvv). These values are passed to the checkout gRPC call but are not logged directly — positive finding. However, session IDs (which serve as `user_id` in downstream calls) appear in logs without redaction.
- **Gap**: Session IDs logged without redaction. Session IDs serve as user_id in downstream services, making them PII-adjacent.
- **Compensating Controls**:
  - PCI data (credit card) is not logged — positive finding
  - PII form fields (email, address) are not logged — positive finding
  - Session IDs are random UUIDs, not directly identifying
- **Remediation Timeline**: 30 days
- **Recommendation**: Hash or redact session IDs in log output. Implement a logrus hook that masks PII-adjacent fields.
- **Evidence**: `src/frontend/middleware.go` (session ID in logs), `src/frontend/handlers.go`

### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK
- **Finding**: CI exists (Cloud Build + Skaffold + GitHub Actions). Frontend Go tests exist in `validator/validator_test.go` and `money/money_test.go`. Proto uses versioned package (`hipstershop.v1`) and `buf.yaml` exists with `breaking: FILE` rule. However, `buf breaking` is not executed in CI. No contract tests for the 7 downstream gRPC service integrations.
- **Gap**: No automated breaking change detection in CI. No contract tests for 7 downstream gRPC integrations. Frontend is the highest-risk service for breaking changes due to 7-service fan-out.
- **Compensating Controls**:
  - Protobuf wire compatibility provides implicit backward compatibility
  - `buf.yaml` with `breaking: FILE` rule is ready to be added to CI
  - Smoke test via loadgenerator exercises the frontend end-to-end
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `buf breaking` to CI pipeline. Add contract tests for each downstream gRPC integration.
- **Evidence**: `cloudbuild.yaml`, `.github/workflows/ci-pr.yaml`, `protos/buf.yaml`

### ENG-Q3: Rollback Capability
- **Severity**: RISK
- **Finding**: K8s Deployment with rollout history. Skaffold deployment. No automated rollback triggers. Manual rollback via `kubectl rollout undo` only. No canary deployment. Liveness/readiness probes prevent traffic to unhealthy pods. Monitoring alerts can trigger manual rollback faster.
- **Gap**: No automated rollback on service degradation. Manual rollback only. P0 priority and external exposure increase urgency.
- **Compensating Controls**:
  - K8s rollout history enables manual rollback within minutes
  - Liveness/readiness probes prevent traffic to unhealthy pods
  - Monitoring alerts detect degradation
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure automated rollback triggers using Flagger or Argo Rollouts with canary analysis.
- **Evidence**: `cloudbuild.yaml`, `helm-chart/templates/frontend.yaml`, `kubernetes-manifests/hpa.yaml`

---

## INFOs — Architecture and Design Inputs

### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: Istio service mesh is enabled with mTLS enforced across all services. Every service-to-service call is authenticated via mTLS certificates managed by Istio's Citadel/istiod. The frontend's Istio sidecar authenticates all incoming requests and provides peer identity via `X-Forwarded-Client-Cert` headers. AuthorizationPolicy restricts callers to known service accounts. mTLS certificates are automatically rotated by Istio.
- **Implication**: Machine identity authentication is handled at the mesh layer. Agent service accounts can be created as K8s ServiceAccounts and authenticated via Istio mTLS. Principal attribution is available via Istio access logs (source principal field).
- **Recommendation**: Create dedicated agent K8s ServiceAccounts. Configure AuthorizationPolicy to allow agent service accounts with appropriate route restrictions.
- **Evidence**: `helm-chart/values.yaml` (`sidecars.create: true`, `authorizationPolicies.create: true`), `helm-chart/templates/frontend.yaml` (AuthorizationPolicy, Sidecar)

### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The frontend has write operations: `addToCartHandler` (POST `/cart`), `emptyCartHandler` (POST `/cart/empty`), `placeOrderHandler` (POST `/cart/checkout`). None have idempotency key support. `addToCartHandler` calls `cartSvcConn.AddItem` which is additive (not idempotent). `placeOrderHandler` calls `checkoutSvcConn.PlaceOrder` with no idempotency protection.
- **Implication**: Write operations lack idempotency. If agent scope expands to write-enabled, this becomes a BLOCKER. Plan idempotency key support before scope expansion.
- **Recommendation**: Add idempotency key headers to write endpoints when REST/JSON API is added (API-Q1).
- **Evidence**: `src/frontend/handlers.go` (addToCartHandler, placeOrderHandler)

### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: The frontend returns HTML (`text/html`) for all user-facing routes. Backend gRPC services use Protocol Buffers (binary serialization) with well-defined proto schemas in `protos/demo.proto`. The proto package is versioned (`hipstershop.v1`). Two minor JSON endpoints exist (`/product-meta/{ids}`, `/bot`).
- **Implication**: HTML responses are not consumable by agents. Proto-based gRPC backends provide structured, typed responses. Agent tool design should target gRPC backends directly or the future REST/JSON API layer.
- **Recommendation**: When REST/JSON API is added, use JSON with consistent schema derived from proto definitions.
- **Evidence**: `protos/demo.proto` (package `hipstershop.v1`), `src/frontend/handlers.go`

### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: The frontend does not emit events directly. State changes (cart updates, order placement) are delegated to backend gRPC services. The checkout flow triggers downstream events in checkoutservice. No webhook endpoints. No EventBridge/SNS/SQS integration in the frontend itself.
- **Implication**: Event-driven agent patterns should subscribe to backend service events, not frontend events. The frontend is a pass-through orchestrator.
- **Recommendation**: No action needed for the frontend. Event emission is the responsibility of backend services.
- **Evidence**: `src/frontend/handlers.go`, `src/frontend/rpc.go`

### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: The EnvoyFilter rate limiting configuration returns `x-rate-limit-limit` and `x-rate-limit-remaining` response headers. Rate limit is 100 requests per 60 seconds. This is documented in the EnvoyFilter YAML but not in any API documentation or README.
- **Implication**: Rate limit headers are present and machine-readable — agents can self-throttle. Documentation gap is minor since the headers are self-describing.
- **Recommendation**: Document rate limits in API documentation when REST/JSON API is added.
- **Evidence**: `istio-manifests/rate-limit.yaml`

### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: Istio mTLS manages all service-to-service authentication credentials automatically. Certificates are issued by istiod and rotated without application involvement. The frontend has no hardcoded credentials, no `.env` files, no Secrets Manager references. Environment variables contain only service addresses (`PRODUCT_CATALOG_SERVICE_ADDR`, `CURRENCY_SERVICE_ADDR`, etc.) and feature flags (`ENABLE_TRACING`, `ENABLE_PROFILER`). No secrets are needed beyond Istio-managed mTLS certificates.
- **Implication**: Credential management is fully automated via Istio. No manual credential rotation needed. If API keys are added for agent auth, they should be stored in a secrets manager.
- **Recommendation**: When agent-specific credentials are introduced, use K8s Secrets or a secrets manager with rotation.
- **Evidence**: `src/frontend/main.go` (env vars — service addresses only), `helm-chart/values.yaml`

### STATE-Q2: Queryable Current State
- **Severity**: INFO
- **Finding**: The frontend renders state as HTML pages (home page shows products, cart page shows cart contents). These are not machine-queryable. However, the frontend is an orchestrator — it does not own state. All state is owned by backend gRPC services which expose queryable RPCs: `CartService.GetCart`, `ProductCatalogService.ListProducts`, `ProductCatalogService.GetProduct`, `CurrencyService.GetSupportedCurrencies`. Agents can query state directly from backend services.
- **Implication**: State is queryable via backend gRPC services. The frontend's HTML rendering is not a gap for agents that can call backends directly.
- **Recommendation**: Direct agents to backend gRPC services for state queries. When REST/JSON API is added to the frontend, include query endpoints.
- **Evidence**: `protos/demo.proto` (GetCart, ListProducts, GetProduct RPCs), `src/frontend/rpc.go`

### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The frontend has no concurrency controls (no optimistic locking, no ETags, no version fields). Write operations (`addToCart`, `placeOrder`) delegate to backend services without concurrency protection. Cart operations use `CartService.AddItem` which is additive. No conflict resolution logic.
- **Implication**: Read-only agents do not perform writes, so concurrency controls are not a deployment gate. If scope expands to write-enabled, concurrency controls become RISK.
- **Recommendation**: Plan concurrency controls (ETags, version fields) for write endpoints when REST/JSON API is added.
- **Evidence**: `src/frontend/handlers.go`, `src/frontend/rpc.go`

### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No transaction limits configured. No per-agent action limits. The EnvoyFilter rate limit (100 req/60s) provides traffic-level protection but not business-level transaction limits (e.g., max orders per hour, max cart modifications per session).
- **Implication**: Read-only agents cannot trigger business-impacting transactions. If scope expands to write-enabled, transaction limits become RISK.
- **Recommendation**: Plan per-agent transaction limits before expanding to write-enabled scope.
- **Evidence**: `istio-manifests/rate-limit.yaml`

### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No draft or pending state concept. Cart operations are immediate. Checkout is a single-step commit (no review-then-confirm pattern). No approval workflow.
- **Implication**: Read-only agents do not make state changes. If scope expands to write-enabled, draft states become RISK for checkout operations.
- **Recommendation**: Consider adding a checkout preview/confirmation step before expanding agent scope to write-enabled.
- **Evidence**: `src/frontend/handlers.go` (placeOrderHandler — immediate commit)

### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable approval gates. All operations execute immediately upon request. No operation-level flags for requiring human approval.
- **Implication**: Read-only agents do not execute write operations. If scope expands, approval gates for checkout and cart-empty operations become RISK.
- **Recommendation**: Implement configurable approval gates for high-risk operations before write-enabled agent deployment.
- **Evidence**: `src/frontend/handlers.go`

### HITL-Q3: Sandbox/Staging Environment
- **Severity**: INFO
- **Finding**: Skaffold provides local development deployment (`skaffold.yaml`). Docker-compose is available for local testing. The loadgenerator provides synthetic traffic for end-to-end testing. Helm chart supports multiple environment configurations. Kustomize overlays exist for different deployment targets.
- **Implication**: Local development and testing infrastructure exists. Production-equivalent staging would require a dedicated K8s cluster with Istio, which is an infrastructure concern outside the frontend's scope.
- **Recommendation**: Deploy a staging environment with Istio mesh for agent integration testing before production deployment.
- **Evidence**: `skaffold.yaml`, `helm-chart/`, `kubernetes-manifests/`, `src/loadgenerator/`

### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO
- **Finding**: `DATA_CLASSIFICATION.md` provides a comprehensive data classification taxonomy with four levels (PUBLIC, INTERNAL, PII, PCI). The frontend is classified as "PCI + PII (pass-through)" with all checkout fields identified. `protos/demo.proto` includes inline data classification comments on every message and sensitive field (e.g., `PlaceOrderRequest` classified as "PCI + PII", `CreditCardInfo` fields annotated as "PCI: Primary Account Number", `Address` fields annotated as "PII"). Agent access policy is documented: no agent may access PCI fields without PCI-DSS compliance verification.
- **Implication**: Data classification is comprehensive and documented at both the service level and field level. Agent access policies are defined. This is a strong foundation for agent data governance.
- **Recommendation**: Enforce classification-based access controls via Istio AuthorizationPolicy and application-level field filtering when REST/JSON API is added.
- **Evidence**: `DATA_CLASSIFICATION.md`, `protos/demo.proto` (field-level classification comments)

### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: INFO
- **Finding**: Proto definitions include temporal metadata: `Cart.updated_at` (google.protobuf.Timestamp), `Product.created_at`, `Product.updated_at`, `OrderResult.created_at`. Timestamps use Protocol Buffers' well-known `google.protobuf.Timestamp` type which provides nanosecond precision with UTC normalization. The frontend passes these timestamps through from backend services.
- **Implication**: Temporal metadata is available in proto schemas. Agents can reason about data freshness using these timestamps. The frontend passes timestamps through without modification.
- **Recommendation**: Expose temporal metadata in REST/JSON API responses when added. Consider adding `Cache-Control` headers for cacheable responses.
- **Evidence**: `protos/demo.proto` (Cart.updated_at, Product.created_at, Product.updated_at, OrderResult.created_at)

### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No formal data quality scores or completeness metrics. Product catalog is a static JSON file with known completeness. Cart data is transient (Redis-backed). No data quality dashboards or monitoring.
- **Implication**: Data quality is implicitly high for this demo application (static catalog, simple cart). Production deployments should add data quality monitoring.
- **Recommendation**: Add data quality metrics if the application evolves beyond demo scope.
- **Evidence**: `src/productcatalogservice/products.json`

### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: INFO
- **Finding**: Proto definitions use versioned package (`hipstershop.v1`) with `option go_package` specifying the versioned import path. `buf.yaml` exists with `breaking: FILE` rule configured for breaking change detection. Proto schemas are well-documented with inline comments and data classification annotations. However, `buf breaking` is not yet executed in CI (see ENG-Q2).
- **Implication**: Schema versioning infrastructure is in place. Proto versioning and buf breaking change detection provide a strong foundation for agent tool stability. CI integration is the remaining gap (tracked in ENG-Q2).
- **Recommendation**: Activate `buf breaking` in CI to complete the schema governance pipeline.
- **Evidence**: `protos/demo.proto` (package `hipstershop.v1`), `protos/buf.yaml` (`breaking: FILE`)

### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Proto field names are human-readable and semantically meaningful: `product_id`, `user_id`, `street_address`, `credit_card_number`, `currency_code`, `shipping_tracking_id`, `order_id`. No legacy abbreviations or codes. Field comments provide additional context (e.g., "The 3-letter currency code defined in ISO 4217").
- **Implication**: Field names are LLM-friendly. Agents can reason about data semantics without a data dictionary.
- **Recommendation**: Maintain naming conventions when adding REST/JSON API endpoints.
- **Evidence**: `protos/demo.proto`

### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: `DATA_CLASSIFICATION.md` serves as a lightweight data catalog documenting service data ownership, classification levels, and sensitive fields. Proto definitions with inline comments provide schema-level metadata. No formal data catalog tool (Glue, Collibra, DataHub).
- **Implication**: `DATA_CLASSIFICATION.md` and annotated proto definitions provide sufficient metadata for agent tool development. A formal data catalog is not needed at this scale.
- **Recommendation**: Maintain `DATA_CLASSIFICATION.md` as the source of truth for data ownership and classification.
- **Evidence**: `DATA_CLASSIFICATION.md`, `protos/demo.proto`

### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: INFO
- **Finding**: OpenTelemetry is enabled with `otelhttp.NewHandler` wrapping all HTTP routes and `otelgrpc` interceptors on all gRPC client connections. Trace context propagates through all 7 downstream gRPC calls. Logrus provides structured JSON logging with request path, method, request ID, session ID, response status, and latency. OTel collector is deployed as a sidecar for trace export. Istio sidecar adds mesh-level tracing.
- **Implication**: Distributed tracing and structured logging are comprehensive. Agent-initiated requests can be traced end-to-end across all 7 downstream services. This is a strong observability foundation.
- **Recommendation**: Add agent identity fields to trace attributes and log entries for agent-specific diagnostics.
- **Evidence**: `src/frontend/main.go` (otelhttp, otelgrpc), `src/frontend/middleware.go` (logrus), `helm-chart/values.yaml` (`tracing: true`, `opentelemetryCollector.create: true`)

### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: INFO
- **Finding**: Monitoring alerts are configured in `kubernetes-manifests/monitoring-alerts.yaml` for error rates and latency on the frontend. HPA provides auto-scaling based on CPU utilization. OTel metrics export is enabled. Istio provides mesh-level metrics (request count, duration, error rate) via Prometheus.
- **Implication**: Alerting infrastructure is in place. Agent-induced degradation will be detected. Consider adding agent-specific alert thresholds.
- **Recommendation**: Add agent-specific alerting rules that trigger when agent traffic patterns deviate from baseline.
- **Evidence**: `kubernetes-manifests/monitoring-alerts.yaml`, `kubernetes-manifests/hpa.yaml`, `helm-chart/values.yaml`

### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business outcome metrics. Infrastructure metrics (CPU, memory, request count, error rate, latency) are available via OTel and Istio. No conversion rate, cart abandonment, or order completion metrics published as custom metrics.
- **Implication**: Business outcome metrics would help measure whether agent interactions produce good outcomes. Not a deployment gate.
- **Recommendation**: Add custom metrics for business outcomes (e.g., checkout completion rate, cart-to-order conversion) when agent integration is deployed.
- **Evidence**: `src/frontend/main.go`, `kubernetes-manifests/monitoring-alerts.yaml`

### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: INFO
- **Finding**: The frontend's infrastructure is fully defined as code: Helm chart (`helm-chart/templates/frontend.yaml`) defines Deployment, Service, ServiceAccount, AuthorizationPolicy, NetworkPolicy, and Sidecar. Kustomize manifests provide alternative deployment. K8s HPA is defined in `kubernetes-manifests/hpa.yaml`. Istio EnvoyFilter for rate limiting is defined in `istio-manifests/rate-limit.yaml`. Monitoring alerts are defined in `kubernetes-manifests/monitoring-alerts.yaml`. CI/CD via Cloud Build and GitHub Actions provides change review. No drift detection configured.
- **Implication**: Infrastructure is code-defined and subject to CI/CD review. Drift detection is the remaining gap but is a cluster-level concern, not frontend-specific.
- **Recommendation**: Enable drift detection at the cluster level (e.g., Flux/ArgoCD with drift reconciliation).
- **Evidence**: `helm-chart/templates/frontend.yaml`, `kubernetes-manifests/hpa.yaml`, `istio-manifests/rate-limit.yaml`, `kubernetes-manifests/monitoring-alerts.yaml`

### ENG-Q4: API Test Coverage
- **Severity**: INFO
- **Finding**: Frontend Go tests exist in `validator/validator_test.go` and `money/money_test.go`. The loadgenerator exercises the frontend end-to-end with synthetic traffic covering all major user flows (browse, add to cart, checkout). No dedicated API test suite, but the frontend currently has no API (HTML only). Proto contract tests via `buf` are available but not yet in CI.
- **Implication**: Test coverage is adequate for the current HTML-only frontend. When REST/JSON API is added (API-Q1), dedicated API tests should be added simultaneously.
- **Recommendation**: Add API test suite when REST/JSON endpoints are implemented.
- **Evidence**: `src/frontend/validator/validator_test.go`, `src/frontend/money/money_test.go`, `src/loadgenerator/`

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: BLOCKER
- **Finding**: The frontend serves HTML pages via Go `html/template`. Routes in `main.go` use `gorilla/mux`: `/`, `/product/{id}`, `/cart`, `/cart/empty`, `/setCurrency`, `/logout`, `/cart/checkout`, `/assistant`. All handlers call `templates.ExecuteTemplate` to render HTML. No REST/JSON API surface. The frontend is a gRPC *client* (not server) calling 7 backend services. Two minor JSON endpoints (`/product-meta/{ids}`, `/bot`) are internal UI helpers, not a documented API.
- **Gap**: No machine-readable API. HTML-only responses. Only remaining BLOCKER in the portfolio.
- **Recommendation**: Add REST/JSON API layer reusing existing gRPC client calls in `rpc.go`, or direct agents to backend gRPC services.
- **Evidence**: `src/frontend/main.go`, `src/frontend/handlers.go`, `src/frontend/templates/*.html`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK
- **Finding**: No OpenAPI or machine-readable spec for the frontend. Backend proto specs exist (`protos/demo.proto`, package `hipstershop.v1`) with `buf.yaml` governance.
- **Gap**: No machine-readable spec for frontend HTTP interface.
- **Recommendation**: Generate OpenAPI spec when REST/JSON API is added.
- **Evidence**: `src/frontend/main.go`, `protos/demo.proto`, `protos/buf.yaml`

#### API-Q3: Structured Error Responses
- **Severity**: RISK
- **Finding**: `renderHTTPError` in `handlers.go` renders HTML error pages. No structured JSON errors, no error codes, no retryable boolean.
- **Gap**: Error responses are HTML, not machine-readable.
- **Recommendation**: Implement structured JSON error responses with REST/JSON API.
- **Evidence**: `src/frontend/handlers.go`, `src/frontend/templates/error.html`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Write operations (`addToCartHandler`, `placeOrderHandler`) lack idempotency keys. `addToCartHandler` is additive. `placeOrderHandler` has no idempotency protection.
- **Gap**: No idempotency support on write endpoints. Informational for read-only scope.
- **Recommendation**: Add idempotency key support before expanding to write-enabled scope.
- **Evidence**: `src/frontend/handlers.go`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: Frontend returns HTML. Backend gRPC services use Protocol Buffers with versioned proto schemas (`hipstershop.v1`).
- **Gap**: HTML is not agent-consumable. Proto-based backends provide structured responses.
- **Recommendation**: Use JSON derived from proto definitions for future REST API.
- **Evidence**: `protos/demo.proto`, `src/frontend/handlers.go`

#### API-Q6: Asynchronous Operation Support
- **Severity**: RISK
- **Finding**: Checkout is synchronous via gRPC. No job status polling or webhook callback. Timeout failures leave order status unknown.
- **Gap**: No async operation support for long-running checkout.
- **Recommendation**: Add job status endpoint for checkout operations.
- **Evidence**: `src/frontend/handlers.go` (placeOrderHandler), `src/frontend/rpc.go`

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: Frontend does not emit events. State changes are delegated to backend gRPC services. No webhook endpoints, no EventBridge/SNS/SQS integration.
- **Gap**: No event emission from frontend. Backend services handle events.
- **Recommendation**: No action needed for frontend. Event emission is backend responsibility.
- **Evidence**: `src/frontend/handlers.go`, `src/frontend/rpc.go`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: EnvoyFilter returns `x-rate-limit-limit` and `x-rate-limit-remaining` headers. 100 req/60s. Not documented in API docs.
- **Gap**: Rate limit headers present but undocumented.
- **Recommendation**: Document rate limits when REST/JSON API is added.
- **Evidence**: `istio-manifests/rate-limit.yaml`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: Istio mTLS enforced across all services. Every call authenticated via mesh-managed certificates. AuthorizationPolicy restricts callers to known service accounts. Certificates auto-rotated by istiod.
- **Gap**: Machine identity is handled at mesh layer. No application-layer auth, but mesh-level is sufficient for K8s-native agents.
- **Recommendation**: Create dedicated agent K8s ServiceAccounts with AuthorizationPolicy rules.
- **Evidence**: `helm-chart/values.yaml`, `helm-chart/templates/frontend.yaml`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicy restricts callers. No agent-specific service accounts. No per-route authorization differentiation.
- **Gap**: No agent-specific service accounts or per-route authorization.
- **Recommendation**: Create agent-specific service accounts with per-route AuthorizationPolicy rules.
- **Evidence**: `helm-chart/templates/frontend.yaml`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK
- **Finding**: AuthorizationPolicy allows GET and POST on all routes. No application-layer authorization. No method-level differentiation.
- **Gap**: No action-level authorization.
- **Recommendation**: Add HTTP middleware enforcing per-route, per-method authorization.
- **Evidence**: `src/frontend/main.go`, `helm-chart/templates/frontend.yaml`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: RISK
- **Finding**: No JWT parsing or token exchange. Session ID (random UUID) passed as `user_id` to backends. No agent-as-self vs agent-on-behalf-of-user distinction. Istio mTLS provides service-level identity only.
- **Gap**: No identity propagation through downstream calls. Session ID is unauthenticated.
- **Recommendation**: Implement JWT-based auth. Derive user identity from tokens. Distinguish agent modes in gRPC metadata.
- **Evidence**: `src/frontend/middleware.go`, `src/frontend/rpc.go`

#### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: Istio mTLS manages all service-to-service credentials automatically with rotation. No hardcoded credentials. Environment variables contain only service addresses and feature flags. No secrets needed beyond Istio-managed certificates.
- **Gap**: No gap for current scope. Future agent-specific credentials should use secrets management.
- **Recommendation**: Use K8s Secrets or secrets manager when agent-specific credentials are introduced.
- **Evidence**: `src/frontend/main.go`, `helm-chart/values.yaml`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: Logrus structured JSON logging with OTel tracing enabled. Istio access logs capture mTLS peer identity. No principal attribution in application logs. No immutable storage.
- **Gap**: No principal attribution in application logs. No immutable audit trail.
- **Recommendation**: Add caller identity to logrus fields. Forward logs to immutable store.
- **Evidence**: `src/frontend/middleware.go`, `src/frontend/main.go`, `helm-chart/values.yaml`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicy can deny specific service accounts (manual). No automated suspension. Frontend externally exposed via LoadBalancer.
- **Gap**: No automated suspension mechanism.
- **Recommendation**: Implement automated suspension via AuthorizationPolicy updates triggered by anomaly detection.
- **Evidence**: `helm-chart/templates/frontend.yaml`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: Frontend orchestrates checkout via `checkoutSvcConn.PlaceOrder` (7-step workflow). No compensation logic — delegates to checkoutservice. Error renders HTML error page with no rollback.
- **Gap**: No compensation for multi-step checkout. Depends on backend compensation capability.
- **Recommendation**: Implement saga pattern in checkoutservice.
- **Evidence**: `src/frontend/handlers.go`, `src/frontend/rpc.go`

#### STATE-Q2: Queryable Current State
- **Severity**: INFO
- **Finding**: Frontend renders state as HTML. However, as an orchestrator, it does not own state. Backend gRPC services expose queryable RPCs: `CartService.GetCart`, `ProductCatalogService.ListProducts`, `ProductCatalogService.GetProduct`, `CurrencyService.GetSupportedCurrencies`.
- **Gap**: Frontend state is HTML-only, but backend state is queryable via gRPC.
- **Recommendation**: Direct agents to backend gRPC services for state queries.
- **Evidence**: `protos/demo.proto`, `src/frontend/rpc.go`

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No concurrency controls. Write operations delegate to backends without optimistic locking or version fields.
- **Gap**: No concurrency controls. Informational for read-only scope.
- **Recommendation**: Plan concurrency controls before write-enabled scope expansion.
- **Evidence**: `src/frontend/handlers.go`, `src/frontend/rpc.go`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK
- **Finding**: 7 downstream gRPC calls with no circuit breakers. Only `getAd` has explicit 100ms timeout. All other RPCs use parent context with no deadline. Istio sidecar provides mesh-level capabilities but no explicit configuration.
- **Gap**: No application-level circuit breakers. 1 of 7 RPCs has explicit timeout.
- **Recommendation**: Add per-call context deadlines. Implement circuit breakers or Istio DestinationRule outlier detection.
- **Evidence**: `src/frontend/rpc.go`, `src/frontend/main.go`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK
- **Finding**: EnvoyFilter rate limit: 100 req/60s with response headers. Global bucket, not per-caller.
- **Gap**: Rate limiting is global, not per-caller.
- **Recommendation**: Configure per-source-principal rate limits.
- **Evidence**: `istio-manifests/rate-limit.yaml`, `kubernetes-manifests/hpa.yaml`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No transaction limits. EnvoyFilter provides traffic-level protection only.
- **Gap**: No business-level transaction limits. Informational for read-only scope.
- **Recommendation**: Plan per-agent transaction limits before write-enabled scope expansion.
- **Evidence**: `istio-manifests/rate-limit.yaml`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: RISK
- **Finding**: HPA 1–10 replicas at 70% CPU. Monitoring alerts configured. No load testing for agent traffic patterns. 7-service fan-out amplifies agent traffic. Externally exposed via LoadBalancer.
- **Gap**: No load testing for agent traffic. Fan-out amplification risk.
- **Recommendation**: Conduct load testing with agent-like traffic patterns.
- **Evidence**: `kubernetes-manifests/hpa.yaml`, `kubernetes-manifests/monitoring-alerts.yaml`, `istio-manifests/rate-limit.yaml`

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No draft or pending state. Cart operations and checkout are immediate. No approval workflow.
- **Gap**: No draft states. Informational for read-only scope.
- **Recommendation**: Add checkout preview/confirmation step before write-enabled scope expansion.
- **Evidence**: `src/frontend/handlers.go`

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable approval gates. All operations execute immediately.
- **Gap**: No approval gates. Informational for read-only scope.
- **Recommendation**: Implement approval gates for high-risk operations before write-enabled deployment.
- **Evidence**: `src/frontend/handlers.go`

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: INFO
- **Finding**: Skaffold provides local development deployment. Docker-compose available. Loadgenerator provides synthetic traffic. Helm chart supports multiple environments. Kustomize overlays for different targets.
- **Gap**: No production-equivalent staging with Istio mesh, but local testing infrastructure is adequate for development.
- **Recommendation**: Deploy staging environment with Istio for agent integration testing.
- **Evidence**: `skaffold.yaml`, `helm-chart/`, `kubernetes-manifests/`, `src/loadgenerator/`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO
- **Finding**: `DATA_CLASSIFICATION.md` provides comprehensive taxonomy (PUBLIC, INTERNAL, PII, PCI). Frontend classified as "PCI + PII (pass-through)". `protos/demo.proto` has inline field-level classification comments. `PlaceOrderRequest` classified as "PCI + PII". Agent access policy documented.
- **Gap**: No gap. Classification is comprehensive at service and field level.
- **Recommendation**: Enforce classification-based access controls via AuthorizationPolicy and field filtering.
- **Evidence**: `DATA_CLASSIFICATION.md`, `protos/demo.proto`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: Frontend handles PCI + PII in checkout flow. No explicit region pinning. Data residency depends on cluster deployment region.
- **Gap**: No explicit data residency policy for PCI + PII data.
- **Recommendation**: Document residency requirements. Pin deployment to specific regions.
- **Evidence**: `DATA_CLASSIFICATION.md`, `src/frontend/handlers.go`

#### DATA-Q3: Selective Query Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `orchestrator`, agent_scope: `read-only`.
- **Trigger**: Service has list/query endpoints with potentially unbounded results.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q4: System of Record Designations
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `orchestrator`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway).
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: INFO
- **Finding**: Proto definitions include `Cart.updated_at`, `Product.created_at`, `Product.updated_at`, `OrderResult.created_at` using `google.protobuf.Timestamp` (nanosecond precision, UTC). Frontend passes timestamps through from backend services.
- **Gap**: No freshness signaling headers (Cache-Control, X-Data-Age). Timestamps are available in proto responses.
- **Recommendation**: Add `Cache-Control` headers when REST/JSON API is added.
- **Evidence**: `protos/demo.proto`

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK
- **Finding**: PCI/PII form fields (credit card, email, address) are not logged — positive finding. Session IDs (serving as `user_id` in downstream calls) appear in logs without redaction.
- **Gap**: Session IDs logged without redaction.
- **Recommendation**: Hash or redact session IDs in log output.
- **Evidence**: `src/frontend/middleware.go`, `src/frontend/handlers.go`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No formal data quality scores. Product catalog is static JSON with known completeness. Cart data is transient.
- **Gap**: No data quality metrics. Acceptable for demo-scale application.
- **Recommendation**: Add data quality monitoring if application evolves beyond demo scope.
- **Evidence**: `src/productcatalogservice/products.json`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: INFO
- **Finding**: Proto package versioned (`hipstershop.v1`). `buf.yaml` with `breaking: FILE` rule. Well-documented proto schemas with inline comments and data classification annotations. `buf breaking` not yet in CI (tracked in ENG-Q2).
- **Gap**: CI integration for breaking change detection is the remaining gap.
- **Recommendation**: Activate `buf breaking` in CI.
- **Evidence**: `protos/demo.proto`, `protos/buf.yaml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Proto field names are human-readable: `product_id`, `user_id`, `street_address`, `credit_card_number`, `currency_code`, `shipping_tracking_id`. No legacy abbreviations. ISO 4217 currency code reference in comments.
- **Gap**: No gap. Field names are LLM-friendly.
- **Recommendation**: Maintain naming conventions in future API endpoints.
- **Evidence**: `protos/demo.proto`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: `DATA_CLASSIFICATION.md` serves as lightweight data catalog. Proto definitions with inline comments provide schema-level metadata. No formal catalog tool.
- **Gap**: No formal data catalog. `DATA_CLASSIFICATION.md` is sufficient at this scale.
- **Recommendation**: Maintain `DATA_CLASSIFICATION.md` as source of truth.
- **Evidence**: `DATA_CLASSIFICATION.md`, `protos/demo.proto`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: INFO
- **Finding**: OpenTelemetry enabled with `otelhttp.NewHandler` (HTTP) and `otelgrpc` interceptors (gRPC). Trace context propagates through all 7 downstream calls. Logrus structured JSON logging. OTel collector deployed. Istio mesh-level tracing.
- **Gap**: No gap. Comprehensive distributed tracing and structured logging.
- **Recommendation**: Add agent identity fields to trace attributes.
- **Evidence**: `src/frontend/main.go`, `src/frontend/middleware.go`, `helm-chart/values.yaml`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: INFO
- **Finding**: Monitoring alerts configured for error rates and latency. HPA auto-scaling. OTel metrics export. Istio mesh-level metrics via Prometheus.
- **Gap**: No gap. Alerting infrastructure is in place.
- **Recommendation**: Add agent-specific alerting rules.
- **Evidence**: `kubernetes-manifests/monitoring-alerts.yaml`, `kubernetes-manifests/hpa.yaml`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business outcome metrics. Infrastructure metrics available via OTel and Istio.
- **Gap**: No business outcome metrics.
- **Recommendation**: Add custom metrics for business outcomes when agent integration is deployed.
- **Evidence**: `src/frontend/main.go`, `kubernetes-manifests/monitoring-alerts.yaml`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: INFO
- **Finding**: Infrastructure fully defined as code: Helm chart (Deployment, Service, ServiceAccount, AuthorizationPolicy, NetworkPolicy, Sidecar), Kustomize manifests, HPA, EnvoyFilter, monitoring alerts. CI/CD via Cloud Build and GitHub Actions. No drift detection.
- **Gap**: No drift detection. Infrastructure is otherwise well-governed.
- **Recommendation**: Enable drift detection at cluster level (Flux/ArgoCD).
- **Evidence**: `helm-chart/templates/frontend.yaml`, `kubernetes-manifests/hpa.yaml`, `istio-manifests/rate-limit.yaml`, `kubernetes-manifests/monitoring-alerts.yaml`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK
- **Finding**: CI exists (Cloud Build + Skaffold + GitHub Actions). Go tests exist. `buf.yaml` with `breaking: FILE` ready but not in CI. No contract tests for 7 downstream gRPC integrations.
- **Gap**: No automated breaking change detection in CI. No contract tests.
- **Recommendation**: Add `buf breaking` to CI. Add contract tests for downstream integrations.
- **Evidence**: `cloudbuild.yaml`, `.github/workflows/ci-pr.yaml`, `protos/buf.yaml`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK
- **Finding**: K8s Deployment with rollout history. Skaffold deployment. No automated rollback triggers. Manual rollback only. Liveness/readiness probes and monitoring alerts support faster manual response.
- **Gap**: No automated rollback. P0 priority and external exposure increase urgency.
- **Recommendation**: Configure automated rollback with Flagger or Argo Rollouts.
- **Evidence**: `cloudbuild.yaml`, `helm-chart/templates/frontend.yaml`, `kubernetes-manifests/hpa.yaml`

#### ENG-Q4: API Test Coverage
- **Severity**: INFO
- **Finding**: Go unit tests in `validator/validator_test.go` and `money/money_test.go`. Loadgenerator exercises end-to-end flows. No dedicated API test suite (frontend has no API currently).
- **Gap**: No API tests, but frontend has no API to test. Loadgenerator provides end-to-end coverage.
- **Recommendation**: Add API test suite when REST/JSON endpoints are implemented.
- **Evidence**: `src/frontend/validator/validator_test.go`, `src/frontend/money/money_test.go`, `src/loadgenerator/`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `orchestrator`, agent_scope: `read-only`.
- **Trigger**: Service has persistent data stores.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

---

## Evidence Index

### Infrastructure as Code
| File | Questions Referenced |
|------|---------------------|
| `helm-chart/templates/frontend.yaml` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7, STATE-Q1, ENG-Q1, ENG-Q3 |
| `helm-chart/values.yaml` | AUTH-Q1, AUTH-Q5, AUTH-Q6, OBS-Q1, OBS-Q2, ENG-Q1 |
| `kubernetes-manifests/hpa.yaml` | STATE-Q5, STATE-Q7, OBS-Q2, ENG-Q1, ENG-Q3 |
| `kubernetes-manifests/monitoring-alerts.yaml` | STATE-Q7, OBS-Q2, OBS-Q3, ENG-Q1 |
| `istio-manifests/rate-limit.yaml` | API-Q8, STATE-Q5, STATE-Q6, STATE-Q7, ENG-Q1 |

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `src/frontend/main.go` | API-Q1, AUTH-Q3, AUTH-Q5, STATE-Q4, OBS-Q1, OBS-Q3 |
| `src/frontend/handlers.go` | API-Q1, API-Q3, API-Q4, API-Q5, API-Q6, API-Q7, AUTH-Q4, STATE-Q1, STATE-Q3, HITL-Q1, HITL-Q2, DATA-Q2, DATA-Q6 |
| `src/frontend/rpc.go` | API-Q6, API-Q7, AUTH-Q4, STATE-Q1, STATE-Q2, STATE-Q3, STATE-Q4 |
| `src/frontend/middleware.go` | AUTH-Q4, AUTH-Q6, DATA-Q6, OBS-Q1 |
| `src/frontend/templates/*.html` | API-Q1 |
| `src/frontend/templates/error.html` | API-Q3 |
| `src/frontend/validator/validator_test.go` | ENG-Q2, ENG-Q4 |
| `src/frontend/money/money_test.go` | ENG-Q2, ENG-Q4 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `protos/demo.proto` | API-Q2, API-Q5, STATE-Q2, DATA-Q1, DATA-Q5, DISC-Q1, DISC-Q2, DISC-Q3 |
| `protos/buf.yaml` | API-Q2, DISC-Q1, ENG-Q2 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `cloudbuild.yaml` | ENG-Q2, ENG-Q3 |
| `.github/workflows/ci-pr.yaml` | ENG-Q2 |
| `skaffold.yaml` | HITL-Q3 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `DATA_CLASSIFICATION.md` | DATA-Q1, DATA-Q2, DISC-Q3 |
| `src/productcatalogservice/products.json` | DATA-Q7 |
| `src/loadgenerator/` | HITL-Q3, ENG-Q4 |
