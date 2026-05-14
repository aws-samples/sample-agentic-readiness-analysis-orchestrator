# Agentic Readiness Analysis Report

**Target**: services/microservices-demo/src/frontend
**Date**: 2026-04-16
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**Repository Type**: application
**Service Archetype**: orchestrator (user-provided)
**Agent Scope**: read-only
**Priority**: P0
**Tags**: go, frontend, grpc
**Context**: Go web frontend serving the Online Boutique UI. Calls all backend services via gRPC.

---

## Readiness Profile: Not Agent-Integrable

**BLOCKERs**: 3 | **RISKs**: 18 | **INFOs**: 11

Three or more blockers indicate this service is not suitable for agent integration in its current form. The frontend serves HTML pages for human consumption — it has no machine-readable API (API-Q1 BLOCKER), no machine identity authentication (AUTH-Q1 BLOCKER), and processes PCI+PII data without classification (DATA-Q1 BLOCKER). Agent integration should target the backend gRPC services directly, not the HTML frontend.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 3 |
| RISK | 18 |
| INFO | 11 |
| N/A | 0 |
| Not Evaluated (extended) | 11 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 8
**Extended Questions Not Triggered**: 11
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: orchestrator (user-provided)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: The HTTP server is created via `http.ListenAndServe(addr+":"+srvPort, handler)` in `main.go` with no TLS, no authentication middleware, and no credential verification. The server accepts all incoming HTTP connections on port 8080. The frontend is exposed externally via a LoadBalancer Service (`frontend-external`). Istio AuthorizationPolicies are disabled (`authorizationPolicies.create: false`). The AuthorizationPolicy template allows all traffic when `frontend.externalService: true` (no `from` restriction). No OAuth2, no API key, no session-based authentication for API calls.
- **Gap**: No machine identity authentication. The frontend is publicly accessible via LoadBalancer. Any internet-reachable client can access all endpoints. No mechanism to identify or attribute agent callers.
- **Remediation**:
  - **Immediate**: Enable Istio AuthorizationPolicies. For external access, implement API key or OAuth2 authentication middleware.
  - **Target State**: Machine-readable API endpoints (see API-Q1) with OAuth2 client credentials for agent access. Separate agent API from human UI.
  - **Estimated Effort**: High (requires API layer creation, not just auth enablement)
  - **Dependencies**: API-Q1 (machine-readable API must exist before agent auth is meaningful)
- **Evidence**: `main.go` (line 155, `http.ListenAndServe` — no TLS), `helm-chart/templates/frontend.yaml` (LoadBalancer Service, AuthorizationPolicy allows all when externalService=true), `helm-chart/values.yaml` (`authorizationPolicies.create: false`, `frontend.externalService: true`)

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: The frontend processes both PCI and PII data. The `placeOrderHandler` in `handlers.go` collects credit card data (`credit_card_number`, `credit_card_expiration_month`, `credit_card_expiration_year`, `credit_card_cvv`) and PII (`email`, `street_address`, `city`, `state`, `country`, `zip_code`) from HTML form submissions. This data is passed to `checkoutservice` via gRPC. Session IDs are stored in cookies (`shop_session-id`). No formal data classification exists. The frontend is the primary entry point for all sensitive data in the system.
- **Gap**: PCI+PII data collected and forwarded without formal classification. Credit card data and personal information flow through the frontend without field-level protection. No `DATA_CLASSIFICATION.md` in service directory.
- **Remediation**:
  - **Immediate**: Create `DATA_CLASSIFICATION.md` documenting PCI (credit card) and PII (email, address) data flows. Classify as RESTRICTED/PCI and CONFIDENTIAL/PII.
  - **Target State**: Field-level encryption for PCI data before forwarding to backend. PII minimization. Client-side tokenization.
  - **Estimated Effort**: Medium (classification), High (field-level encryption)
- **Evidence**: `handlers.go` (placeOrderHandler — collects credit card and address data from form), `main.go` (session cookie management), `rpc.go` (forwards data to backend services)

### API-Q1: Documented API Interface

- **Severity**: BLOCKER
- **Finding**: The frontend serves HTML pages via HTTP — it is a web UI, not a machine-readable API. Routes are defined in `main.go` using `gorilla/mux`: `/` (home), `/product/{id}`, `/cart`, `/cart/checkout`, `/setCurrency`, `/logout`, `/assistant`, `/bot`, `/product-meta/{ids}`. All routes return HTML via Go templates (`templates/*.html`) except `/product-meta/{ids}` (returns JSON) and `/bot` (returns JSON). There is no OpenAPI spec, no gRPC API, no machine-readable interface documentation. The `/product-meta/{ids}` and `/bot` endpoints are informal JSON APIs without documentation or schema.
- **Gap**: No machine-readable API. The frontend is designed for human browser interaction, not agent consumption. HTML responses cannot be reliably parsed by agents. The two JSON endpoints (`/product-meta/{ids}`, `/bot`) are undocumented and informal.
- **Remediation**:
  - **Immediate**: Agents should target backend gRPC services directly (productcatalog, cart, checkout, etc.) rather than the HTML frontend.
  - **Target State**: If frontend agent integration is required, create a dedicated REST/gRPC API layer with OpenAPI documentation, separate from the HTML UI.
  - **Estimated Effort**: High (new API layer)
- **Evidence**: `main.go` (lines 139–153, route definitions — all return HTML), `handlers.go` (template rendering via `templates.ExecuteTemplate`), `templates/` directory (HTML templates)

---

## RISKs — Proceed with Compensating Controls

### API-Q2: Machine-Readable API Specification

- **Severity**: RISK
- **Finding**: No machine-readable API specification. No OpenAPI, no AsyncAPI, no Smithy model. Routes are defined in Go code using `gorilla/mux`. The two JSON endpoints (`/product-meta/{ids}`, `/bot`) have no schema documentation.
- **Gap**: No API specification. Routes defined only in source code.
- **Recommendation**: Create OpenAPI spec for the JSON endpoints. For full agent integration, create a dedicated API layer.
- **Evidence**: `main.go` (route definitions), `handlers.go` (getProductByID, chatBotHandler — JSON responses)

### API-Q3: Structured Error Responses

- **Severity**: RISK
- **Finding**: Errors are rendered as HTML pages via `renderHTTPError()` in `handlers.go`. The error template displays a human-readable error message, HTTP status code, and status text. No JSON error responses, no error code taxonomy, no retryable flags. The `/product-meta/{ids}` endpoint silently returns empty on error (no error response at all).
- **Gap**: HTML error responses. No structured error format for machine consumption.
- **Recommendation**: Implement JSON error responses for API endpoints. Add error codes and retryable flags.
- **Evidence**: `handlers.go` (renderHTTPError function — HTML template), `templates/error.html`

### API-Q7: Event Emission for State Changes

- **Severity**: RISK
- **Finding**: The frontend orchestrates state changes across multiple backend services: adding items to cart (`insertCart`), emptying cart (`emptyCart`), placing orders (`PlaceOrder`), and setting currency preferences (cookie). No events are emitted for any of these state changes. No webhooks, no event bus, no change notifications.
- **Gap**: No event emission for state changes. Agents cannot subscribe to cart or order events.
- **Recommendation**: Implement event emission for cart modifications and order placement.
- **Evidence**: `handlers.go` (addToCartHandler, emptyCartHandler, placeOrderHandler), `rpc.go` (insertCart, emptyCart)

### AUTH-Q2: Scoped Permissions (Least Privilege)

- **Severity**: RISK
- **Finding**: AuthorizationPolicies disabled. The Helm template allows all traffic when `frontend.externalService: true`. No agent-specific access controls. All routes are equally accessible to any caller.
- **Gap**: No caller restriction. No agent-specific permission scoping. All endpoints (including checkout with PCI data) are publicly accessible.
- **Recommendation**: Enable AuthorizationPolicies. Implement route-level access controls for sensitive endpoints (checkout, cart modification).
- **Evidence**: `helm-chart/values.yaml`, `helm-chart/templates/frontend.yaml` (AuthorizationPolicy allows all)

### AUTH-Q3: Action-Level Authorization

- **Severity**: RISK
- **Finding**: No action-level authorization. All HTTP routes are accessible without authentication. The `placeOrderHandler` (which processes credit card data) has the same access controls as the home page (none). No middleware for authorization beyond session ID management.
- **Gap**: No action-level authorization. PCI-processing endpoints have no access restrictions.
- **Recommendation**: Implement route-level authorization middleware. Restrict checkout and cart modification endpoints.
- **Evidence**: `main.go` (route definitions — no auth middleware), `handlers.go` (placeOrderHandler — no auth check)

### AUTH-Q5: Credential Management

- **Severity**: RISK
- **Finding**: The frontend connects to 7 backend services via `grpc.NewClient()` with `insecure.NewCredentials()` (no TLS). Service addresses are read from environment variables. No secrets, no API keys, no Secrets Manager. All gRPC connections are insecure. Session IDs are stored in cookies with no encryption.
- **Gap**: Insecure gRPC connections to all backend services. No credential management. Session cookies without encryption.
- **Recommendation**: Rely on Istio mTLS for inter-service encryption. Encrypt session cookies. Use external secrets operator if credentials are introduced.
- **Evidence**: `main.go` (mustConnGRPC — `insecure.NewCredentials()`), `middleware.go` (session cookie management)

### AUTH-Q6: Immutable Audit Logging ⚡

- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: Logging uses `logrus` with JSON formatter. The `logHandler` middleware logs request path, method, request ID, session ID, response status, response time, and response bytes. No principal attribution beyond session ID. Logs are ephemeral container stdout. No immutable storage. Tracing is gated by `ENABLE_TRACING` env var.
- **Gap**: No immutable audit trail. Session ID provides some attribution but no machine identity. No immutable log storage.
- **Recommendation**: Add caller identity to logs. Forward to immutable store. Enable tracing.
- **Evidence**: `middleware.go` (logHandler — logs request metadata), `main.go` (logrus JSON formatter)

### AUTH-Q7: Agent Identity Suspension

- **Severity**: RISK
- **Finding**: No agent identity suspension mechanism. No agent-specific identities. AuthorizationPolicies disabled. The only way to block access is to modify the LoadBalancer Service or add network-level restrictions.
- **Gap**: No mechanism to suspend misbehaving agent.
- **Recommendation**: Implement API key-based authentication with revocation capability for agent access.
- **Evidence**: `helm-chart/values.yaml`, `helm-chart/templates/frontend.yaml`

### STATE-Q2: Queryable Current State

- **Severity**: RISK
- **Finding**: The frontend does not own state — it orchestrates state across backend services. Cart state is in cartservice, product data in productcatalogservice, orders in checkoutservice. The frontend's only state is the session cookie and currency preference cookie. No API to query frontend-specific state.
- **Gap**: No queryable frontend state. State is distributed across backend services.
- **Recommendation**: Agents should query backend services directly for state.
- **Evidence**: `rpc.go` (all state operations delegate to backend services), `middleware.go` (session cookie)

### STATE-Q4: Circuit Breakers and Resilience

- **Severity**: RISK
- **Finding**: The frontend calls 7 backend services with no circuit breakers, no retry logic, and no timeout configuration (except a 100ms timeout on ad service calls in `rpc.go`). If any backend service is down, the corresponding frontend page fails entirely. No fallback rendering, no graceful degradation. The `getRecommendations` and `chooseAd` calls have error handling that logs warnings and continues, but other service calls fail the entire request.
- **Gap**: No circuit breakers for 7 backend dependencies. Most failures cascade to the user. Limited graceful degradation (recommendations and ads only).
- **Recommendation**: Implement circuit breakers for all backend service calls. Add fallback rendering for non-critical services (recommendations, ads, currency).
- **Evidence**: `rpc.go` (7 backend service calls — no circuit breakers; line 97, 100ms timeout on ads only), `handlers.go` (error handling varies by service)

### STATE-Q7: Infrastructure Capacity for Agent Traffic

- **Severity**: RISK
- **Finding**: P0 service with modest resources (CPU: 100m–200m, memory: 64Mi–128Mi). No HPA configured. Single replica default. The frontend is the entry point for all user and agent traffic. As an orchestrator calling 7 backend services, each frontend request generates multiple downstream calls — agent traffic at machine speed would amplify load across the entire system.
- **Gap**: No autoscaling. Modest resources for P0 orchestrator. Agent traffic amplification across 7 backend services.
- **Recommendation**: Configure HPA. Set minimum 2 replicas. Conduct load testing. Implement rate limiting to prevent agent traffic amplification.
- **Evidence**: `helm-chart/templates/frontend.yaml` (no HPA), `helm-chart/values.yaml` (CPU: 100m–200m, memory: 64Mi–128Mi)

### DATA-Q5: Temporal Metadata and Freshness

- **Severity**: RISK
- **Finding**: HTML responses have no temporal metadata. No `Last-Modified` headers, no `ETag`, no cache control headers for dynamic content. The JSON endpoints (`/product-meta/{ids}`, `/bot`) also lack temporal metadata. Agents cannot determine data freshness.
- **Gap**: No temporal metadata on any response.
- **Recommendation**: Add `Last-Modified` and `ETag` headers. Add timestamps to JSON responses.
- **Evidence**: `handlers.go` (no cache headers), `main.go` (no cache middleware)

### OBS-Q1: Distributed Tracing and Structured Logging

- **Severity**: RISK
- **Finding**: OpenTelemetry is integrated — `otelhttp.NewHandler` wraps the HTTP handler, `otelgrpc.NewClientHandler` instruments gRPC clients, and OTLP trace exporter is configured. However, tracing is gated by `ENABLE_TRACING` env var (disabled in analysis context). Logrus JSON structured logging with request ID, session ID, path, method, status, and response time. Logs lack trace correlation when tracing is disabled.
- **Gap**: Tracing disabled. Logs lack trace correlation. OpenTelemetry is fully integrated but inactive.
- **Recommendation**: Enable tracing. The OpenTelemetry integration is comprehensive and will activate automatically.
- **Evidence**: `main.go` (lines 153–154, otelhttp and otelgrpc; lines 163–175, initTracing), `middleware.go` (logHandler)

### OBS-Q2: Alerting on Error Rates and Latency

- **Severity**: RISK
- **Finding**: No alerting configuration. HTTP health probe (`/_healthz`) exists but no error rate or latency alerting. No custom metrics. `initStats()` is a TODO stub. For a P0 frontend orchestrator, lack of alerting is critical.
- **Gap**: No alerting on error rates or latency.
- **Recommendation**: Configure alerting for HTTP error rates, p99 latency, and backend service call failures.
- **Evidence**: `main.go` (line 160, initStats TODO), `helm-chart/templates/frontend.yaml` (health probe only)

### DISC-Q1: Schema Versioning and API Contracts

- **Severity**: RISK
- **Finding**: No API versioning. HTTP routes have no version prefix (not `/v1/`). No OpenAPI spec to version. The proto definitions used by gRPC clients use `package hipstershop` with no version suffix. No breaking change detection.
- **Gap**: No API versioning. No schema versioning. No breaking change detection.
- **Recommendation**: If a machine-readable API is created (per API-Q1), implement API versioning from the start.
- **Evidence**: `main.go` (route definitions — no version prefix), `genproto/demo.pb.go`

### ENG-Q1: Infrastructure Governance for Agent-Facing Surface

- **Severity**: RISK
- **Finding**: Helm charts and Terraform with PR-based review. No drift detection.
- **Gap**: No drift detection.
- **Recommendation**: Implement GitOps with ArgoCD or Flux.
- **Evidence**: `helm-chart/templates/frontend.yaml`, `helm-chart/values.yaml`

### ENG-Q2: CI/CD with API Contract Testing

- **Severity**: RISK
- **Finding**: CI/CD exists. The frontend has some test files (`money/money_test.go`, `validator/validator_test.go`) covering money formatting and input validation. No HTTP integration tests, no API contract tests, no end-to-end tests for the frontend specifically.
- **Gap**: Limited test coverage. No HTTP integration tests. No contract tests.
- **Recommendation**: Add HTTP integration tests for key routes. Add contract tests for backend service interactions.
- **Evidence**: `money/money_test.go`, `validator/validator_test.go`, `.github/workflows/ci-pr.yaml`

### ENG-Q4: API Test Coverage

- **Severity**: RISK
- **Finding**: Unit tests exist for `money` package (money formatting) and `validator` package (input validation for AddToCart and PlaceOrder payloads). No HTTP handler tests, no route tests, no integration tests. Test coverage is limited to utility packages.
- **Gap**: No HTTP handler test coverage. No route testing.
- **Recommendation**: Add handler tests for key routes (home, product, cart, checkout).
- **Evidence**: `money/money_test.go`, `validator/validator_test.go`

### ENG-Q5: Encryption at Rest for Agent-Accessible Data

- **Severity**: RISK
- **Finding**: The frontend does not persist data. PCI and PII data flows through in-memory during request processing and is forwarded to backend services. Session cookies are stored client-side. Log output may contain request metadata but not PCI/PII data (logHandler logs path, method, status — not request body).
- **Gap**: No persistent data. PCI/PII data in-memory only during request processing.
- **Recommendation**: Ensure PCI/PII data is never logged. Encrypt session cookies.
- **Evidence**: `middleware.go` (logHandler — logs metadata only), `handlers.go` (PCI/PII in request processing)

---

## INFOs — Architecture and Design Inputs

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Write operations exist: `addToCartHandler` (POST /cart), `emptyCartHandler` (POST /cart/empty), `placeOrderHandler` (POST /cart/checkout), `setCurrencyHandler` (POST /setCurrency). None are idempotent — repeated cart additions increase quantity, repeated orders create duplicate orders. No idempotency keys. Read-only scope mitigates.
- **Implication**: Non-idempotent writes. Critical if scope changes to write-enabled.
- **Recommendation**: No action for read-only scope. Add idempotency keys if write-enabled.
- **Evidence**: `handlers.go` (addToCartHandler, placeOrderHandler — non-idempotent)

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: Most responses are HTML via Go templates. Two JSON endpoints exist: `/product-meta/{ids}` returns product data as JSON, `/bot` returns chatbot response as JSON. No consistent response format.
- **Implication**: HTML responses are not machine-parseable. JSON endpoints are informal.
- **Recommendation**: If agent integration is needed, create dedicated JSON API endpoints.
- **Evidence**: `handlers.go` (getProductByID — JSON, chatBotHandler — JSON, all others — HTML)

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limiting. No rate limit documentation. The frontend is publicly accessible via LoadBalancer.
- **Implication**: Publicly accessible with no rate limiting. Vulnerable to abuse.
- **Recommendation**: Implement rate limiting at the LoadBalancer or Istio ingress level.
- **Evidence**: `main.go` (no rate limiting), `helm-chart/templates/frontend.yaml` (LoadBalancer)

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: INFO
- **Finding**: The frontend uses session IDs (UUID cookies) as user identity. Session IDs are passed to backend services as `user_id` in gRPC calls (e.g., `getCart(ctx, sessionID(r))`, `insertCart(ctx, sessionID(r), ...)`). No JWT, no OAuth2, no real user authentication. The session ID is the only identity context.
- **Implication**: Session-based identity propagation via cookies. No real user authentication. Agents would need to manage session cookies.
- **Recommendation**: Implement proper user authentication if agent integration is needed.
- **Evidence**: `middleware.go` (ensureSessionID), `handlers.go` (sessionID(r) used in all backend calls), `rpc.go`

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The frontend orchestrates multi-service workflows (checkout involves cart, payment, shipping, email) with no compensation. If `PlaceOrder` fails partway through, there is no rollback of partial state changes. Read-only scope mitigates.
- **Implication**: No compensation for orchestrated workflows. Critical if write-enabled.
- **Recommendation**: No action for read-only scope. Implement saga pattern if write-enabled.
- **Evidence**: `handlers.go` (placeOrderHandler — single PlaceOrder call, no compensation), `rpc.go`

### STATE-Q5: Rate Limiting and Throttling

- **Severity**: INFO
- **Finding**: No rate limiting. Resource limits (CPU: 200m, memory: 128Mi). No request-level throttling. Publicly accessible via LoadBalancer.
- **Implication**: Publicly accessible with no throttling. Agent traffic amplified across 7 backend services.
- **Recommendation**: Implement rate limiting at ingress level.
- **Evidence**: `helm-chart/templates/frontend.yaml`, `helm-chart/values.yaml`

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Write operations (cart modification, order placement) have no transaction limits. Read-only scope mitigates.
- **Gap**: N/A for read-only scope.
- **Recommendation**: No action for current scope.
- **Evidence**: `handlers.go` (write handlers)

### HITL-Q3: Sandbox/Staging Environment

- **Severity**: INFO
- **Finding**: Staging GKE cluster with per-PR namespaces. Full stack via Skaffold.
- **Gap**: No agent testing documentation.
- **Recommendation**: Document staging environment for agent testing.
- **Evidence**: `.github/workflows/ci-pr.yaml`, `cloudbuild.yaml`

### DATA-Q2: Data Residency and Sovereignty ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: PCI and PII data flows through in-memory during request processing. Not persisted by the frontend. Session cookies stored client-side. Processing region determined by GKE cluster.
- **Gap**: No data residency documentation for PCI/PII processing.
- **Recommendation**: Document processing region for PCI/GDPR compliance.
- **Evidence**: `handlers.go` (in-memory processing), `helm-chart/values.yaml`

### DATA-Q6: PII Redaction in Logs

- **Severity**: INFO
- **Finding**: The logHandler middleware logs request path, method, request ID, session ID, response status, and timing. It does not log request bodies, form values, or PCI/PII data. Credit card and address data from the checkout form are not logged.
- **Gap**: None — PCI/PII data not logged.
- **Recommendation**: Maintain current practice. Ensure form data is never added to logs.
- **Evidence**: `middleware.go` (logHandler — logs metadata only)

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: Input validation exists via the `validator` package. `AddToCartPayload` validates quantity and product ID. `PlaceOrderPayload` validates email, address, and credit card fields. `SetCurrencyPayload` validates currency code. Validation uses `go-playground/validator/v10`.
- **Implication**: Input validation provides data quality assurance at the entry point.
- **Recommendation**: No action required. Validation is well-implemented.
- **Evidence**: `validator/validator.go`, `handlers.go` (payload.Validate() calls)

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: HTTP route paths are human-readable: `/product/{id}`, `/cart`, `/cart/checkout`, `/setCurrency`. Form field names are semantic: `email`, `street_address`, `credit_card_number`. JSON response fields are semantic.
- **Gap**: None.
- **Recommendation**: No action required.
- **Evidence**: `main.go` (route definitions), `handlers.go` (form field names)

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No formal data catalog. No API documentation. Route definitions in source code only.
- **Gap**: No metadata layer.
- **Recommendation**: Create API documentation if machine-readable API is implemented.
- **Evidence**: `main.go` (route definitions)

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No custom business metrics. `initStats()` is a TODO stub. No conversion tracking, no cart abandonment metrics, no page view analytics.
- **Gap**: No business outcome measurement.
- **Recommendation**: Implement conversion and cart abandonment metrics.
- **Evidence**: `main.go` (initStats TODO)

### ENG-Q3: Rollback Capability

- **Severity**: INFO
- **Finding**: Helm rollback available. K8s rolling update. No automated rollback. For a P0 frontend, automated rollback is important.
- **Gap**: No automated rollback.
- **Recommendation**: Implement Flagger or Argo Rollouts for P0 service.
- **Evidence**: `helm-chart/Chart.yaml`, `helm-chart/templates/frontend.yaml`

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: BLOCKER
- **Finding**: HTML-only web UI. No machine-readable API. Routes return HTML via Go templates. Two informal JSON endpoints exist (`/product-meta/{ids}`, `/bot`) but are undocumented.
- **Gap**: No machine-readable API for agent consumption.
- **Recommendation**: Agents should target backend gRPC services directly. Create dedicated REST API if frontend integration is required.
- **Evidence**: `main.go` (route definitions), `handlers.go` (HTML template rendering), `templates/`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK
- **Finding**: No API specification. Routes in Go code only. No OpenAPI.
- **Gap**: No API spec.
- **Recommendation**: Create OpenAPI spec for JSON endpoints.
- **Evidence**: `main.go`, `handlers.go`

#### API-Q3: Structured Error Responses
- **Severity**: RISK
- **Finding**: HTML error pages via renderHTTPError(). No JSON errors. /product-meta silently returns empty on error.
- **Gap**: HTML errors. No structured error format.
- **Recommendation**: Implement JSON error responses for API endpoints.
- **Evidence**: `handlers.go` (renderHTTPError), `templates/error.html`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Non-idempotent writes (cart add, order placement). Read-only scope mitigates.
- **Gap**: Non-idempotent writes.
- **Recommendation**: No action for read-only scope.
- **Evidence**: `handlers.go` (addToCartHandler, placeOrderHandler)

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: HTML responses. Two JSON endpoints. No consistent format.
- **Gap**: HTML not machine-parseable.
- **Recommendation**: Create dedicated JSON API.
- **Evidence**: `handlers.go`

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered.
- **Trigger**: Service has operations >30s OR long-running workflows
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: RISK
- **Finding**: Orchestrates state changes (cart, orders, currency) with no event emission.
- **Gap**: No event emission for state changes.
- **Recommendation**: Implement event emission for cart and order changes.
- **Evidence**: `handlers.go` (addToCartHandler, placeOrderHandler), `rpc.go`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limiting. Publicly accessible via LoadBalancer.
- **Gap**: No rate limit feedback.
- **Recommendation**: Implement rate limiting at ingress.
- **Evidence**: `main.go`, `helm-chart/templates/frontend.yaml`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: `http.ListenAndServe` with no TLS, no auth. Publicly accessible via LoadBalancer. AuthorizationPolicies disabled.
- **Gap**: No machine identity authentication. Publicly accessible.
- **Recommendation**: Implement OAuth2 or API key authentication for agent access.
- **Evidence**: `main.go` (line 155), `helm-chart/templates/frontend.yaml`, `helm-chart/values.yaml`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK
- **Finding**: AuthorizationPolicies disabled. All routes equally accessible. No agent-specific controls.
- **Gap**: No caller restriction.
- **Recommendation**: Implement route-level access controls.
- **Evidence**: `helm-chart/values.yaml`, `helm-chart/templates/frontend.yaml`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK
- **Finding**: No authorization. PCI-processing checkout has same access as home page (none).
- **Gap**: No action-level authorization.
- **Recommendation**: Implement route-level authorization middleware.
- **Evidence**: `main.go`, `handlers.go`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: Session ID cookies as user identity. Passed to backend as user_id. No real authentication.
- **Gap**: Session-based identity only.
- **Recommendation**: Implement proper user authentication.
- **Evidence**: `middleware.go` (ensureSessionID), `rpc.go`

#### AUTH-Q5: Credential Management
- **Severity**: RISK
- **Finding**: Insecure gRPC connections to 7 backend services. Session cookies without encryption.
- **Gap**: No credential management. Insecure inter-service communication.
- **Recommendation**: Rely on Istio mTLS. Encrypt session cookies.
- **Evidence**: `main.go` (mustConnGRPC — insecure.NewCredentials())

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: Logrus JSON logging with request metadata. Session ID attribution. No immutable storage. Tracing gated by env var.
- **Gap**: No immutable audit trail.
- **Recommendation**: Add caller identity. Forward to immutable store. Enable tracing.
- **Evidence**: `middleware.go` (logHandler), `main.go` (logrus, initTracing)

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK
- **Finding**: No suspension mechanism. No agent identities. Publicly accessible.
- **Gap**: No mechanism to suspend agent.
- **Recommendation**: Implement API key authentication with revocation.
- **Evidence**: `helm-chart/values.yaml`, `helm-chart/templates/frontend.yaml`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Orchestrates multi-service workflows with no compensation. Read-only scope mitigates.
- **Gap**: No compensation for orchestrated workflows.
- **Recommendation**: No action for read-only scope.
- **Evidence**: `handlers.go` (placeOrderHandler), `rpc.go`

#### STATE-Q2: Queryable Current State
- **Severity**: RISK
- **Finding**: Frontend doesn't own state. Orchestrates across backend services. Session cookies only.
- **Gap**: No queryable frontend state.
- **Recommendation**: Agents should query backend services directly.
- **Evidence**: `rpc.go`, `middleware.go`

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered. agent_scope is read-only.
- **Trigger**: agent_scope is write-enabled AND service has persistent state
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK
- **Finding**: 7 backend dependencies with no circuit breakers. 100ms timeout on ads only. Most failures cascade.
- **Gap**: No circuit breakers. Limited graceful degradation.
- **Recommendation**: Implement circuit breakers for all backend calls. Add fallback rendering.
- **Evidence**: `rpc.go` (7 service calls, 100ms timeout on ads only)

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: INFO
- **Finding**: No rate limiting. Publicly accessible. Agent traffic amplified across 7 services.
- **Gap**: No throttling.
- **Recommendation**: Implement rate limiting at ingress.
- **Evidence**: `helm-chart/templates/frontend.yaml`, `helm-chart/values.yaml`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Write operations without limits. Read-only scope mitigates.
- **Gap**: N/A for read-only.
- **Recommendation**: No action.
- **Evidence**: `handlers.go`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: RISK
- **Finding**: P0 orchestrator with modest resources. No HPA. Agent traffic amplified across 7 services.
- **Gap**: No autoscaling. Traffic amplification risk.
- **Recommendation**: Configure HPA. Set minimum 2 replicas. Implement rate limiting.
- **Evidence**: `helm-chart/templates/frontend.yaml`, `helm-chart/values.yaml`

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered. agent_scope is read-only.
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered. agent_scope is read-only.
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: INFO
- **Finding**: Staging GKE cluster with per-PR namespaces.
- **Gap**: No agent testing documentation.
- **Recommendation**: Document staging environment.
- **Evidence**: `.github/workflows/ci-pr.yaml`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: PCI (credit card) and PII (email, address) collected via checkout form. No classification.
- **Gap**: PCI+PII without classification.
- **Recommendation**: Create DATA_CLASSIFICATION.md. Classify as RESTRICTED/PCI and CONFIDENTIAL/PII.
- **Evidence**: `handlers.go` (placeOrderHandler), `rpc.go`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: PCI/PII in-memory only. Not persisted by frontend.
- **Gap**: No data residency documentation.
- **Recommendation**: Document processing region.
- **Evidence**: `handlers.go`, `helm-chart/values.yaml`

#### DATA-Q3: Selective Query Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered. Orchestrator archetype — no list/query endpoints with unbounded results.
- **Trigger**: Service has list/query endpoints with potentially unbounded results
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q4: System of Record Designations
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered. Orchestrator does not own persistent state.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK
- **Finding**: No temporal metadata on any response. No Last-Modified, no ETag, no cache headers.
- **Gap**: No temporal metadata.
- **Recommendation**: Add cache headers and timestamps.
- **Evidence**: `handlers.go`, `main.go`

#### DATA-Q6: PII Redaction in Logs
- **Severity**: INFO
- **Finding**: LogHandler logs metadata only. PCI/PII not logged.
- **Gap**: None.
- **Recommendation**: Maintain current practice.
- **Evidence**: `middleware.go` (logHandler)

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: Input validation via validator package. Validates email, address, credit card, quantity.
- **Gap**: None — validation well-implemented.
- **Recommendation**: No action required.
- **Evidence**: `validator/validator.go`, `handlers.go`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK
- **Finding**: No API versioning. No version prefix on routes. Proto uses `package hipstershop` — no version.
- **Gap**: No versioning. No breaking change detection.
- **Recommendation**: Implement API versioning if machine-readable API is created.
- **Evidence**: `main.go` (routes), `genproto/demo.pb.go`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Human-readable routes and form fields.
- **Gap**: None.
- **Recommendation**: No action required.
- **Evidence**: `main.go`, `handlers.go`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No data catalog. No API documentation.
- **Gap**: No metadata layer.
- **Recommendation**: Create API documentation if API is implemented.
- **Evidence**: `main.go`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK
- **Finding**: OpenTelemetry fully integrated (otelhttp, otelgrpc, OTLP exporter) but disabled. Logrus JSON logging.
- **Gap**: Tracing disabled. No trace correlation.
- **Recommendation**: Enable tracing. Integration is comprehensive.
- **Evidence**: `main.go` (otelhttp, otelgrpc, initTracing), `middleware.go`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK
- **Finding**: No alerting. Health probe only. initStats TODO. P0 service.
- **Gap**: No alerting.
- **Recommendation**: Configure alerting for HTTP errors and latency.
- **Evidence**: `main.go` (initStats TODO), `helm-chart/templates/frontend.yaml`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom metrics. initStats TODO. No conversion tracking.
- **Gap**: No business outcome measurement.
- **Recommendation**: Implement conversion and cart abandonment metrics.
- **Evidence**: `main.go` (initStats TODO)

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK
- **Finding**: Helm charts and Terraform with PR review. No drift detection.
- **Gap**: No drift detection.
- **Recommendation**: Implement GitOps.
- **Evidence**: `helm-chart/templates/frontend.yaml`, `helm-chart/values.yaml`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK
- **Finding**: Unit tests for money and validator packages. No HTTP integration tests. No contract tests.
- **Gap**: Limited test coverage. No integration tests.
- **Recommendation**: Add HTTP handler tests. Add contract tests.
- **Evidence**: `money/money_test.go`, `validator/validator_test.go`

#### ENG-Q3: Rollback Capability
- **Severity**: INFO
- **Finding**: Helm rollback available. No automated rollback. P0 service.
- **Gap**: No automated rollback.
- **Recommendation**: Implement Flagger or Argo Rollouts.
- **Evidence**: `helm-chart/Chart.yaml`, `helm-chart/templates/frontend.yaml`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK
- **Finding**: Unit tests for utility packages only. No handler tests. No route tests.
- **Gap**: No HTTP handler test coverage.
- **Recommendation**: Add handler tests for key routes.
- **Evidence**: `money/money_test.go`, `validator/validator_test.go`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: RISK
- **Finding**: No persistent data. PCI/PII in-memory only. Session cookies client-side.
- **Gap**: No persistent data to encrypt. Session cookies unencrypted.
- **Recommendation**: Encrypt session cookies. Ensure PCI/PII never logged.
- **Evidence**: `middleware.go`, `handlers.go`

---

## Evidence Index

### Infrastructure as Code
| File | Questions Referenced |
|------|---------------------|
| `helm-chart/templates/frontend.yaml` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q7, OBS-Q2, ENG-Q1, ENG-Q3, STATE-Q5, STATE-Q7 |
| `helm-chart/values.yaml` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q5, AUTH-Q6, AUTH-Q7, OBS-Q1, STATE-Q5, STATE-Q7, ENG-Q1 |

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `main.go` | API-Q1, API-Q2, API-Q8, AUTH-Q1, AUTH-Q4, AUTH-Q5, AUTH-Q6, STATE-Q5, DISC-Q1, DISC-Q2, OBS-Q1, OBS-Q2, OBS-Q3, ENG-Q3 |
| `handlers.go` | API-Q1, API-Q2, API-Q3, API-Q4, API-Q5, API-Q7, AUTH-Q3, STATE-Q1, STATE-Q6, DATA-Q1, DATA-Q5, DATA-Q7, ENG-Q4 |
| `rpc.go` | API-Q7, AUTH-Q4, STATE-Q2, STATE-Q4, DATA-Q1 |
| `middleware.go` | AUTH-Q4, AUTH-Q5, AUTH-Q6, STATE-Q2, DATA-Q6, ENG-Q5 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `genproto/demo.pb.go` | DISC-Q1 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/ci-pr.yaml` | HITL-Q3, ENG-Q2, ENG-Q4 |
| `cloudbuild.yaml` | ENG-Q2, ENG-Q3 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `Dockerfile` | AUTH-Q5 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `go.mod` | API-Q2, OBS-Q1 |

### Test Files
| File | Questions Referenced |
|------|---------------------|
| `money/money_test.go` | ENG-Q2, ENG-Q4 |
| `validator/validator_test.go` | ENG-Q2, ENG-Q4 |
| `validator/validator.go` | DATA-Q7 |

### Templates
| File | Questions Referenced |
|------|---------------------|
| `templates/*.html` | API-Q1, API-Q3 |