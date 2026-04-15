# Agentic Readiness Assessment Report

**Target**: ./services/microservices-demo/src/frontend
**Date**: 2026-04-15
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Agent Scope**: read-only
**Priority**: P0
**Tags**: go, frontend, grpc
**Context**: Go web frontend serving the Online Boutique UI. Calls all backend services via gRPC.

---

## Readiness Profile: Not Agent-Integrable

**BLOCKERs**: 3 | **RISKs**: 35 | **INFOs**: 11

Exclude from agent toolset or plan major remediation before re-evaluation.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 3 |
| RISK | 35 |
| INFO | 11 |
| N/A | 0 |
| **Total** | **49** |

**Questions Evaluated**: 49
**Questions N/A (repo_type: application)**: 0

---

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: No authentication mechanism exists in the frontend application. Session identity is managed via a random UUID stored in an unsigned cookie (`middleware.go` `ensureSessionID`). All gRPC connections to backend services use `insecure.NewCredentials()` (`main.go` `mustConnGRPC`). There is no OAuth2 client credentials flow, no API key authentication, no mTLS, and no service account authentication at the application layer. The `ENABLE_SINGLE_SHARED_SESSION` environment variable uses a hard-coded session ID `12345678-1234-1234-1234-123456789123` (`middleware.go`). No principal attribution exists in any log entries — logs contain only `session` (random UUID), `http.req.id`, `http.req.path`, and `http.req.method`.
- **Gap**: The application has zero authentication. Any caller can access any endpoint without identity verification. There is no mechanism to authenticate an agent identity, attribute API calls to a specific agent principal, or distinguish agent traffic from human traffic.
- **Remediation**:
  - **Immediate**: Implement API key or OAuth2 client credentials authentication on the JSON-serving endpoints (`/product-meta/{ids}`, `/bot`) that an agent would consume. Use an API Gateway (e.g., AWS API Gateway, GCP API Gateway, or Istio AuthorizationPolicy) as the enforcement point.
  - **Target State**: All agent-facing endpoints require a machine identity credential (API key with principal attribution or OAuth2 client credentials). Each agent instance has a unique identity. Audit logs include the authenticated principal for every request.
  - **Estimated Effort**: Medium (2-4 weeks for API Gateway-based auth; 4-8 weeks for application-level OAuth2 integration)
  - **Dependencies**: AUTH-Q7 (audit logging requires identity to log), AUTH-Q2 (scoped permissions require identity first)
- **Evidence**: `main.go` (mustConnGRPC with insecure.NewCredentials), `middleware.go` (ensureSessionID with random UUID), `handlers.go` (sessionID used as userId in gRPC calls)

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: The `placeOrderHandler` in `handlers.go` processes sensitive data directly: `email`, `street_address`, `credit_card_number`, `credit_card_cvv`, `credit_card_expiration_month`, `credit_card_expiration_year`. Credit card data is extracted from form values and passed directly to the checkout gRPC service (`pb.NewCheckoutServiceClient(fe.checkoutSvcConn).PlaceOrder`) without field-level encryption, classification, or access controls. The `validator/validator.go` validates input format (e.g., `credit_card` tag on `CcNumber`) but provides no data classification, PII tagging, or access restriction. No PII detection tools (e.g., Amazon Macie) are configured. No data classification tags exist on any infrastructure resources in the Terraform or Kubernetes manifests.
- **Gap**: Sensitive data (PCI-relevant credit card numbers, CVV, email, address) flows through the application without classification, tagging, or field-level access controls. An agent with read access to this service's data layer could retrieve PII without explicit authorization. No data sensitivity metadata exists anywhere in the codebase.
- **Remediation**:
  - **Immediate**: Classify all data fields handled by `placeOrderHandler` as PCI-DSS sensitive. Add field-level classification metadata to the protobuf definitions or an external data dictionary. Implement field-level encryption for credit card data before transmission to the checkout service.
  - **Target State**: All sensitive fields are classified (PII, PCI, PHI) with enforceable access controls. Agents cannot retrieve sensitive fields without explicit authorization scoped to their identity. A data classification policy document exists and is enforced at the application layer.
  - **Estimated Effort**: High (4-8 weeks for classification framework; 8-12 weeks for field-level encryption and access controls)
  - **Dependencies**: AUTH-Q1 (access controls require identity first)
- **Evidence**: `handlers.go` (placeOrderHandler processing credit_card_number, credit_card_cvv, email, street_address), `validator/validator.go` (PlaceOrderPayload struct with credit_card validation tag), `genproto/demo.pb.go` (CreditCardInfo proto message)

### ENG-Q6: Cross-Origin and Network Policies

- **Severity**: BLOCKER
- **Finding**: Network security configurations exist in the Helm chart but are **disabled by default**. The `helm-chart/values.yaml` sets `networkPolicies.create: false` and `authorizationPolicies.create: false`. When disabled, no Kubernetes NetworkPolicy restricts ingress/egress for the frontend pod. The `frontend-external` service in `kubernetes-manifests/frontend.yaml` is a `LoadBalancer` type exposing port 80 directly to the internet with no restrictions. The Istio gateway in `istio-manifests/frontend-gateway.yaml` accepts HTTP traffic on port 80 from all hosts (`hosts: ["*"]`). No CORS configuration exists in application code (`handlers.go`, `main.go`) or in any infrastructure manifest. No WAF rules are defined. The Dockerfile exposes port 8080 (`EXPOSE 8080`) with no TLS configuration. GKE Autopilot manages underlying firewall rules, but these are not defined or documented in the repository.
- **Gap**: The frontend is exposed to the internet via LoadBalancer with no CORS policy, no network policy enforcement (disabled by default), no WAF, and no TLS at the application layer. An agent running on a different origin or cloud platform would encounter undocumented network behavior. The absence of CORS configuration means cross-origin agent calls may be silently blocked or unexpectedly allowed depending on the deployment environment.
- **Remediation**:
  - **Immediate**: Enable network policies by setting `networkPolicies.create: true` in the Helm chart values for all deployed environments. Add CORS middleware to the Go application for the JSON-serving endpoints (`/product-meta/{ids}`, `/bot`). Document the expected network topology.
  - **Target State**: NetworkPolicies are enabled and enforced in all environments. CORS policies explicitly define allowed origins for agent-facing endpoints. TLS termination is configured (at load balancer or Istio gateway). Network topology is documented and discoverable.
  - **Estimated Effort**: Low-Medium (1-2 weeks for enabling network policies and adding CORS middleware; 2-4 weeks for full TLS and documentation)
  - **Dependencies**: None
- **Evidence**: `helm-chart/values.yaml` (networkPolicies.create: false, authorizationPolicies.create: false), `helm-chart/templates/frontend.yaml` (NetworkPolicy and AuthorizationPolicy definitions gated by disabled flags), `kubernetes-manifests/frontend.yaml` (frontend-external LoadBalancer service), `istio-manifests/frontend-gateway.yaml` (Gateway with hosts: ["*"])

## RISKs — Proceed with Compensating Controls

### API-Q2: Machine-Readable API Specification

- **Severity**: RISK
- **Finding**: No OpenAPI, AsyncAPI, GraphQL schema, or Smithy specification files found in the repository. The protobuf schema (`genproto/demo.pb.go`, generated from `demo.proto` via `genproto.sh`) defines gRPC service interfaces for internal backend communication but does not describe the HTTP surface exposed by the frontend. The HTTP routes are defined only in application code (`main.go` via gorilla/mux).
- **Gap**: No machine-readable specification exists for the HTTP endpoints an agent would consume (`/product-meta/{ids}`, `/bot`, etc.). Agent tool definitions must be authored manually and will drift from implementation.
- **Compensating Controls**:
  - Generate an OpenAPI spec from the gorilla/mux routes using `swag` or manual documentation as a short-term measure
  - Use the protobuf definitions as a reference for data structures when building agent tools
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenAPI annotations or generate an OpenAPI 3.0 spec from the existing route definitions. Integrate spec validation into the CI pipeline to prevent drift.
- **Evidence**: `main.go` (route definitions), `genproto.sh` (protobuf generation), absence of any `openapi.yaml`, `swagger.yaml`, or `.graphql` files

### API-Q3: Structured Error Responses

- **Severity**: RISK
- **Finding**: Error handling uses `renderHTTPError` in `handlers.go`, which renders HTML error pages via the `templates/error.html` template. Error responses include HTTP status code, status text, and error message — but rendered as HTML, not structured JSON. The JSON endpoints (`/product-meta/{ids}`, `/bot`) do not return structured error bodies. The `getProductByID` handler silently returns empty responses on errors (no status code, no error body). The `chatBotHandler` returns HTML-rendered errors via `renderHTTPError` even though it's a JSON endpoint.
- **Gap**: No machine-readable error responses with error codes, error categories, or retryable booleans. Agents cannot programmatically distinguish retriable errors from terminal errors.
- **Compensating Controls**:
  - Wrap agent tool calls with error classification logic in the agent orchestration layer
  - Map HTTP status codes to retry/no-retry decisions at the agent framework level
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement structured JSON error responses for the JSON endpoints (`/product-meta/{ids}`, `/bot`) with fields: `error_code`, `message`, `retryable`. Add content negotiation to return JSON errors when `Accept: application/json` is present.
- **Evidence**: `handlers.go` (renderHTTPError function), `templates/error.html` (HTML error template), `handlers.go` (getProductByID silently returns empty, chatBotHandler uses renderHTTPError)

### API-Q5: API Versioning and Deprecation

- **Severity**: RISK
- **Finding**: No API versioning exists. All routes are unversioned (e.g., `/product/{id}`, not `/v1/product/{id}`). No version headers (`Accept-Version`), no version annotations, no changelog files, and no deprecation policy. The protobuf definitions are auto-generated from `demo.proto` without versioning.
- **Gap**: API changes will silently break agent tool schemas. No mechanism exists to notify consumers of breaking changes or maintain backward compatibility.
- **Compensating Controls**:
  - Pin agent tool definitions to the current API behavior and test on every deployment
  - Add API contract tests (ENG-Q2) to catch breaking changes before they affect agents
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Introduce URL-based versioning (`/v1/product-meta/{ids}`) for agent-facing endpoints. Maintain a changelog. Define a deprecation policy with notification mechanisms.
- **Evidence**: `main.go` (route definitions without version prefixes)

### API-Q7: Asynchronous Operation Support

- **Severity**: RISK
- **Finding**: All HTTP handlers are synchronous request-response. The `placeOrderHandler` makes a synchronous gRPC call to the checkout service. No background job frameworks, no job status APIs, no polling endpoints, no webhook callbacks, no async invocation patterns. The ad service call has a 100ms timeout (`rpc.go` `getAd`), but this is a timeout, not an async pattern.
- **Gap**: Any operation exceeding 30 seconds will cause agent timeouts. The checkout operation is synchronous — if the backend checkout service is slow, the agent will time out.
- **Compensating Controls**:
  - Configure agent-side timeouts with retry logic for the checkout flow
  - Use the cart as an implicit async buffer (add items, then checkout separately)
- **Remediation Timeline**: 60–90 days
- **Recommendation**: For long-running operations like checkout, implement an async pattern: accept the order request, return a job ID, and provide a status polling endpoint.
- **Evidence**: `handlers.go` (all handlers are synchronous), `rpc.go` (getAd 100ms timeout is the only timeout pattern)

### AUTH-Q2: Scoped Permissions (Least Privilege)

- **Severity**: RISK
- **Finding**: No authorization model exists at the application level. All endpoints are accessible to any caller without permission checks. The Kubernetes ServiceAccount `frontend` is defined in `kubernetes-manifests/frontend.yaml` but has no associated RBAC policies. The Helm chart supports Istio AuthorizationPolicies (`helm-chart/templates/frontend.yaml`) that would restrict access to GET/POST on port 8080 from specific service accounts, but this is disabled by default (`authorizationPolicies.create: false` in `helm-chart/values.yaml`).
- **Gap**: An agent identity cannot be granted scoped permissions (e.g., read-only access to product data without cart write access). All-or-nothing access model.
- **Compensating Controls**:
  - Enable Istio AuthorizationPolicies to restrict which service identities can reach the frontend
  - Use an API Gateway with route-level authorization to scope agent access
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Enable `authorizationPolicies.create: true` in the Helm chart and define per-route authorization rules. Create separate agent identities with scoped permissions.
- **Evidence**: `kubernetes-manifests/frontend.yaml` (ServiceAccount with no RBAC), `helm-chart/values.yaml` (authorizationPolicies.create: false), `helm-chart/templates/frontend.yaml` (AuthorizationPolicy template)

### AUTH-Q3: Action-Level Authorization

- **Severity**: RISK
- **Finding**: No action-level authorization exists. All endpoints are accessible without permission checks. No ABAC policies, no fine-grained RBAC, no permission matrices, no action-level middleware (`canRead`, `canWrite`, `canDelete`). The Istio AuthorizationPolicy in the Helm chart restricts by HTTP method (GET, POST) and port (8080), but this is disabled by default and does not distinguish between different POST endpoints.
- **Gap**: An agent cannot be restricted to read-only operations (GET endpoints) while being denied access to write operations (POST endpoints for cart, checkout) at the application level.
- **Compensating Controls**:
  - Use API Gateway method-level authorization to restrict agent access to specific HTTP methods and paths
  - Configure Istio AuthorizationPolicy with path-based rules
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement route-level authorization middleware in the Go application or configure Istio AuthorizationPolicies with path-based rules to enforce action-level access control.
- **Evidence**: `handlers.go` (no permission checks in any handler), `main.go` (no authorization middleware in handler chain)

### AUTH-Q4: Identity Propagation

- **Severity**: RISK
- **Finding**: No identity propagation mechanism exists. The session ID is a random UUID stored in an unsigned cookie (`middleware.go` `ensureSessionID`). This session ID is passed as `userId` in gRPC calls to backend services (`handlers.go` `placeOrderHandler` uses `sessionID(r)` as `UserId`). There is no JWT parsing, no OAuth2 token exchange, no on-behalf-of flows. The session ID is not an authenticated identity — it is a random value that does not carry user context.
- **Gap**: The system cannot carry originating user context end-to-end through service calls. Backend services receive a random UUID, not an authenticated user identity. Agents acting on behalf of specific users cannot propagate that user's authorization context.
- **Compensating Controls**:
  - Implement JWT-based identity propagation with a token exchange at the API Gateway
  - Use request headers (X-User-Id) with server-side validation
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Replace the random session UUID with JWT-based authentication. Propagate the JWT through gRPC metadata to backend services for end-to-end identity context.
- **Evidence**: `middleware.go` (ensureSessionID with random UUID), `handlers.go` (sessionID(r) used as UserId in gRPC calls)

### AUTH-Q5: Agent-as-Self vs Agent-on-Behalf-of-User

- **Severity**: RISK
- **Finding**: No concept of agent identity exists in the application. There is no distinction between different types of callers (human users, agents, service accounts). The application treats all callers identically — as anonymous sessions identified by a random UUID cookie. No separate IAM roles, API keys, or auth flows exist for different access patterns.
- **Gap**: The system cannot distinguish between an agent acting under its own service identity and an agent acting on behalf of a specific human user. Both modes would appear identical in logs and access patterns.
- **Compensating Controls**:
  - Use distinct API keys or service account identifiers at the API Gateway layer to differentiate agent traffic
  - Add a custom header (e.g., `X-Agent-Mode: self` or `X-Agent-Mode: delegated`) and log it
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Define two authentication modes: agent-as-self (service account credentials) and agent-on-behalf-of-user (delegated token). Log the mode and originating identity separately.
- **Evidence**: `middleware.go` (single session model for all callers), `handlers.go` (no identity differentiation)

### AUTH-Q6: Credential Management

- **Severity**: RISK
- **Finding**: Backend service addresses are passed via environment variables (`main.go` `mustMapEnv`). gRPC connections use insecure credentials (`insecure.NewCredentials()`). No secrets management system is referenced (no AWS Secrets Manager, no HashiCorp Vault, no GCP Secret Manager). The `ENABLE_SINGLE_SHARED_SESSION` feature uses a hard-coded session ID `12345678-1234-1234-1234-123456789123` in `middleware.go`. No `.env` files are committed to the repository. Environment variables in `kubernetes-manifests/frontend.yaml` contain service addresses but no credentials/secrets.
- **Gap**: While no explicit passwords or API keys are hardcoded, the application uses insecure gRPC connections and has no secrets management infrastructure. The hard-coded session ID in the shared session feature is a security concern. No mechanism exists for credential rotation without redeployment.
- **Compensating Controls**:
  - Store any future credentials (API keys, tokens) in Kubernetes Secrets or a secrets management system
  - Use Workload Identity for GKE-based authentication to backend services
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement mTLS for gRPC connections using Istio's automatic mTLS. Integrate a secrets management system for any application-level credentials. Remove the hard-coded session ID.
- **Evidence**: `main.go` (mustMapEnv for service addresses, mustConnGRPC with insecure.NewCredentials), `middleware.go` (hard-coded session ID), `kubernetes-manifests/frontend.yaml` (env vars with service addresses)

### AUTH-Q7: Immutable Audit Logging ⚡

- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: Structured JSON logging is implemented via logrus (`main.go`, `deployment_details.go`) with fields: `timestamp`, `severity`, `message`, `http.req.path`, `http.req.method`, `http.req.id`, `session`, `http.resp.took_ms`, `http.resp.status`, `http.resp.bytes`. However: (1) No authenticated principal field exists in logs — only a random session UUID. (2) No CloudTrail or equivalent immutable audit logging is configured. (3) No immutable log storage (no S3 bucket with object lock, no CloudWatch log retention with protection). (4) The `chatBotHandler` uses `fmt.Printf` to print raw response bodies to stdout, which may include sensitive data but is not structured.
- **Gap**: Logs do not identify who made a request (no authenticated principal). Log storage is not immutable or tamper-evident. The logging foundation is strong (structured JSON with request IDs) but lacks identity attribution and immutability guarantees.
- **Compensating Controls**:
  - Configure log shipping to an immutable storage backend (e.g., S3 with Object Lock, CloudWatch Logs with retention policies)
  - Add a custom log field for agent identity once AUTH-Q1 is resolved
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add authenticated principal fields to log entries once identity is implemented (AUTH-Q1). Configure immutable log storage. Replace `fmt.Printf` in `chatBotHandler` with structured logging.
- **Evidence**: `main.go` (logrus JSON formatter), `middleware.go` (logHandler with request fields), `handlers.go` (chatBotHandler fmt.Printf)

### AUTH-Q8: Agent Identity Suspension

- **Severity**: RISK
- **Finding**: No agent identity suspension mechanism exists. There are no API keys to revoke, no IAM roles to deactivate, no service account disable mechanisms, and no concept of agent identities in the application. The only identity is the random session UUID cookie, which cannot be selectively suspended.
- **Gap**: If an agent misbehaves, there is no way to isolate or suspend it without taking down the entire frontend service or blocking all traffic.
- **Compensating Controls**:
  - Use API Gateway API key management to enable/disable specific agent credentials
  - Implement IP-based blocking at the load balancer or WAF layer
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement API key-based authentication (AUTH-Q1) with the ability to revoke individual keys. Add a mechanism to disable specific agent identities without affecting other agents or users.
- **Evidence**: `middleware.go` (no identity management), absence of any API key or credential management code

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: No compensation or rollback exists for multi-step operations. The `placeOrderHandler` in `handlers.go` calls `pb.NewCheckoutServiceClient(fe.checkoutSvcConn).PlaceOrder` as a single synchronous gRPC call. There is no saga pattern, no compensating transactions, no undo endpoints, no Step Functions. The cart-to-checkout flow (add items → set currency → place order) has no compensation if a step fails midway. If the checkout call fails after cart items have been added, no automatic rollback of the cart occurs.
- **Gap**: Multi-step agent workflows (browse → add to cart → checkout) have no compensation logic. A failed checkout leaves the cart in a modified state with no automatic recovery.
- **Compensating Controls**:
  - Implement agent-side rollback logic (e.g., call `/cart/empty` on checkout failure)
  - Use the cart as a staging area and verify cart state before checkout
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement compensation endpoints (e.g., cancel order, reverse cart changes). Add error handling in the checkout flow that includes cleanup of intermediate state on failure.
- **Evidence**: `handlers.go` (placeOrderHandler with no rollback), `rpc.go` (emptyCart and insertCart as independent operations)

### STATE-Q2: Queryable Current State

- **Severity**: RISK
- **Finding**: The frontend exposes several GET endpoints that return current state: `GET /` returns all products, `GET /product/{id}` returns product details, `GET /cart` returns cart contents (HTML), `GET /product-meta/{ids}` returns product data as JSON. However, most endpoints return HTML — only `/product-meta/{ids}` returns JSON that an agent can parse programmatically. There are no status query APIs for operations (e.g., order status, checkout progress). Cart state is retrievable but only as HTML.
- **Gap**: Limited machine-readable state queries. Only one endpoint (`/product-meta/{ids}`) returns JSON. Cart and product listing are HTML-only. No operation status APIs exist.
- **Compensating Controls**:
  - Use `/product-meta/{ids}` for product state queries
  - Scrape HTML responses for cart state (fragile but functional for a pilot)
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add JSON-returning endpoints for cart state (`GET /api/cart`) and order status. Add content negotiation to existing endpoints to return JSON when `Accept: application/json` is present.
- **Evidence**: `main.go` (route definitions), `handlers.go` (getProductByID returns JSON, other handlers return HTML via templates)

### STATE-Q3: Concurrency Controls

- **Severity**: RISK
- **Finding**: No concurrency controls exist. No optimistic locking (no version fields, no ETags, no `If-Match` headers), no pessimistic locking (`SELECT FOR UPDATE`), no conditional writes. Cart operations (`insertCart`, `emptyCart`) in `rpc.go` make direct gRPC calls to the cart service without any concurrency safeguards. Multiple agent instances could simultaneously modify the same cart (identified by session ID), causing race conditions.
- **Gap**: Concurrent agent operations on the same session/cart could produce inconsistent state. No mechanism prevents two agents from adding conflicting items or emptying a cart simultaneously.
- **Compensating Controls**:
  - Ensure only one agent instance operates per session at a time through orchestration-layer serialization
  - Use unique session IDs per agent instance to avoid shared-state conflicts
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement optimistic locking on cart operations using version fields or ETags. Add concurrency-safe patterns to the checkout flow.
- **Evidence**: `rpc.go` (insertCart, emptyCart with no locking), `handlers.go` (addToCartHandler, emptyCartHandler with no concurrency checks)

### STATE-Q4: Circuit Breakers and Resilience

- **Severity**: RISK
- **Finding**: Limited resilience patterns. The ad service call has a 100ms timeout via `context.WithTimeout` (`rpc.go` `getAd`). gRPC connections have a 3-second timeout (`main.go` `mustConnGRPC`). Recommendation service failures are handled gracefully — logged as warnings and not propagated to the user (`handlers.go` productHandler, viewCartHandler). However: no circuit breakers exist (no Resilience4j, no Go circuit breaker libraries, no `@CircuitBreaker` patterns). No retry logic with exponential backoff. No bulkhead isolation between backend service calls. A single slow backend service can cascade failures to all frontend requests.
- **Gap**: No circuit breaker protection for backend service calls. A failing backend service will cause the frontend to accumulate pending connections and degrade for all callers including agents.
- **Compensating Controls**:
  - Implement circuit breakers at the Istio service mesh layer (DestinationRule with outlier detection)
  - Configure gRPC client-side deadlines and retry policies
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add circuit breaker middleware using a Go library (e.g., `sony/gobreaker`) or configure Istio DestinationRules with outlier detection for all backend service connections.
- **Evidence**: `rpc.go` (getAd 100ms timeout), `main.go` (mustConnGRPC 3-second timeout), `handlers.go` (recommendation failures logged as warnings)

### STATE-Q5: Rate Limiting and Throttling

- **Severity**: RISK
- **Finding**: No rate limiting exists at any layer. No API Gateway throttling, no WAF rate rules, no application-level rate limiting middleware. The Helm chart does not include rate limiting configuration. The Istio gateway accepts all traffic without throttling. No `express-rate-limit` equivalent for Go is imported in `go.mod`.
- **Gap**: A runaway agent loop could send requests at machine speed with no throttling, potentially overwhelming the frontend and cascading to all 7 backend gRPC services.
- **Compensating Controls**:
  - Configure rate limiting at the Istio ingress gateway or an API Gateway
  - Implement agent-side rate limiting in the orchestration layer
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add rate limiting middleware to the Go application (e.g., `golang.org/x/time/rate`) or configure Istio rate limiting via EnvoyFilter. Define per-client rate limits.
- **Evidence**: `go.mod` (no rate limiting libraries), `main.go` (no rate limiting middleware in handler chain), `helm-chart/values.yaml` (no rate limiting configuration)

### STATE-Q6: Blast Radius and Transaction Limits

- **Severity**: RISK
- **Finding**: No configurable limits on agent-initiated actions. The `AddToCartPayload` validator limits quantity to 1-10 per add-to-cart operation (`validator/validator.go` `validate:"required,gte=1,lte=10"`), but this is an input validation constraint, not a per-agent transaction limit. No maximum records per run, no maximum spend per hour, no maximum operations per session. No configurable limits per agent identity.
- **Gap**: An agent could place unlimited orders, add items to unlimited carts, or call checkout repeatedly with no business-level safeguards. The only constraint is the per-request quantity limit of 10 items.
- **Compensating Controls**:
  - Implement per-agent transaction limits in the orchestration layer
  - Monitor agent activity and set alerting thresholds for unusual volumes
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement configurable per-agent limits: maximum orders per hour, maximum cart value, maximum operations per session. Enforce at the application or API Gateway layer.
- **Evidence**: `validator/validator.go` (quantity limit 1-10 on AddToCartPayload), `handlers.go` (no per-session or per-agent limits)

### STATE-Q7: Infrastructure Capacity for Agent Traffic

- **Severity**: RISK
- **Finding**: Kubernetes resource limits are defined: CPU 100m-200m, memory 64Mi-128Mi (`kubernetes-manifests/frontend.yaml`). GKE Autopilot is used (`terraform/main.tf` `enable_autopilot = true`), which provides automatic node scaling. However: no load test results or configurations found in the repository. No explicit auto-scaling policies (HPA) defined. No capacity planning documentation. The CI pipeline uses a `loadgenerator` for smoke testing (`ci-pr.yaml`) but this validates functionality, not capacity under agent-scale traffic.
- **Gap**: No evidence that the infrastructure has been sized or tested for agent-generated traffic patterns (rapid exploration, concurrent retries, fan-out requests). GKE Autopilot provides implicit scaling but without explicit HPA or load testing, capacity under agent traffic is unknown.
- **Compensating Controls**:
  - Leverage GKE Autopilot's automatic scaling as a baseline
  - Conduct load testing simulating agent traffic patterns before enabling agent access
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Define HPA policies for the frontend deployment. Conduct load testing simulating agent traffic patterns (burst requests, concurrent sessions, rapid retries). Document capacity limits.
- **Evidence**: `kubernetes-manifests/frontend.yaml` (resource requests/limits), `terraform/main.tf` (GKE Autopilot), `.github/workflows/ci-pr.yaml` (loadgenerator smoke test)

### HITL-Q1: Draft/Pending State

- **Severity**: RISK
- **Finding**: No formal draft or pending state exists. The `placeOrderHandler` in `handlers.go` immediately executes the order via the gRPC `PlaceOrder` call. There is no two-step commit, no pending status, no approval workflow. The cart can be considered an implicit draft state (add items → review cart → checkout), but there is no formal "pending order" state that requires human confirmation before execution.
- **Gap**: Agents cannot propose actions for human review before execution. The checkout flow is immediate — once an agent calls the checkout endpoint, the order is placed irrevocably.
- **Compensating Controls**:
  - Use the cart as a de facto staging area — agent adds items, human reviews cart via UI, human clicks checkout
  - Implement approval gates in the agent orchestration layer (human approves before agent calls checkout)
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Introduce a "pending order" state between cart completion and order placement. Add an API endpoint to review and confirm pending orders.
- **Evidence**: `handlers.go` (placeOrderHandler immediately calls PlaceOrder)

### HITL-Q2: Configurable Approval Gates

- **Severity**: RISK
- **Finding**: No configurable approval gates exist. No operations require human approval. No Step Functions with human approval tasks. No status-based workflows requiring explicit confirmation. All write operations (add to cart, empty cart, set currency, place order) execute immediately upon invocation.
- **Gap**: High-risk operations (e.g., checkout with payment) cannot be configured to require a human approval step before execution.
- **Compensating Controls**:
  - Implement approval gates in the agent orchestration layer (e.g., require human approval before the agent calls `/cart/checkout`)
  - Use agent framework guardrails to pause before irreversible actions
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add configurable operation-level flags that require explicit confirmation for specific endpoints. Implement a confirmation API pattern (propose → approve → execute).
- **Evidence**: `handlers.go` (all handlers execute immediately), `main.go` (no approval middleware)

### HITL-Q3: Sandbox/Staging Environment

- **Severity**: RISK
- **Finding**: The CI/CD pipeline deploys to a PR-specific Kubernetes namespace (`ci-pr.yaml`: `NAMESPACE="pr${PR_NUMBER}"`) for testing. The Helm chart and Kustomize support multiple environment configurations. The `ENABLE_SINGLE_SHARED_SESSION` environment variable in `middleware.go` provides a shared session for testing scenarios. The Dockerfile supports local builds. However: no documented sandbox environment with production-equivalent data shape exists. No seed data scripts. No synthetic data generators. No environment-specific IaC for staging.
- **Gap**: While PR-based deployments provide functional testing environments, there is no documented sandbox with production-equivalent data for agent testing. Agents cannot be tested against realistic conditions before production.
- **Compensating Controls**:
  - Use PR-based Kubernetes namespaces as ad-hoc staging environments
  - Deploy the full microservices stack locally using Skaffold for agent testing
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a dedicated staging environment with production-equivalent data shape (anonymized product catalog, synthetic cart data). Document the environment setup and provide seed data scripts.
- **Evidence**: `.github/workflows/ci-pr.yaml` (PR namespace deployment), `middleware.go` (ENABLE_SINGLE_SHARED_SESSION), `Dockerfile` (local build support)

### DATA-Q2: Data Residency and Sovereignty ⚡

- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: No explicit data residency configuration found. Terraform deploys to `us-central1` by default (`terraform/variables.tf` `default = "us-central1"`). No GDPR/LGPD compliance references anywhere in the codebase. No cross-region replication settings. No data sovereignty policies documented. The application processes customer PII (email, address, credit card information) that may be subject to residency requirements depending on the customer base.
- **Gap**: No data residency controls or documentation. If customer data is subject to GDPR or other residency requirements, sending it to an LLM endpoint in another region could create a legal violation. The default `us-central1` deployment region is not explicitly chosen for compliance reasons.
- **Compensating Controls**:
  - Ensure the LLM endpoint used by agents is in the same region as the data
  - Implement data anonymization before sending any data to external LLM providers
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Document data residency requirements for the customer data processed by this frontend. Ensure deployment region aligns with residency requirements. Add data residency metadata to the data classification framework (DATA-Q1).
- **Evidence**: `terraform/variables.tf` (region default: us-central1), `handlers.go` (placeOrderHandler processes customer PII)

### DATA-Q3: Selective Query Support

- **Severity**: RISK
- **Finding**: No pagination, filtering, or sorting on any endpoint. `GET /` returns all products via `rpc.go` `getProducts` which calls `ListProducts` with no filters. `GET /product-meta/{ids}` returns a single product by ID. Recommendations are hard-capped at 4 (`rpc.go` `getRecommendations`: `if len(out) > 4 { out = out[:4] }`). No `limit`, `offset`, `cursor`, or filter query parameters on any endpoint.
- **Gap**: Agents retrieving product data get the full catalog with no ability to filter, paginate, or limit result size. This wastes LLM context window tokens and increases cost.
- **Compensating Controls**:
  - Use `/product-meta/{ids}` to retrieve individual products by ID (natural filter)
  - Implement client-side filtering in the agent orchestration layer
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add pagination and filtering parameters to the product listing endpoint. Implement a JSON API for product search with `limit`, `offset`, and filter parameters.
- **Evidence**: `rpc.go` (getProducts with no filters, getRecommendations capped at 4), `handlers.go` (getProductByID accepts single ID)

### DATA-Q4: System of Record Designations

- **Severity**: RISK
- **Finding**: No system-of-record designations exist. The frontend is a gateway that delegates to 7 backend gRPC services (product catalog, currency, cart, recommendation, checkout, shipping, ad). No documentation designates which backend service is the authoritative source for each entity. No master data management, no golden record patterns, no data ownership definitions.
- **Gap**: Agents consuming data from this frontend have no way to know which backend service is the authoritative source. Conflicting data between services (e.g., product price in catalog vs. cart) has no documented resolution.
- **Compensating Controls**:
  - Document the service ownership model in agent tool definitions
  - Always query the product catalog service (via frontend) as the authoritative product source
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Create a data ownership document mapping each entity (products, cart, orders, pricing) to its authoritative backend service. Make this available as part of the API documentation.
- **Evidence**: `main.go` (7 backend service connections), `rpc.go` (delegating to different services for different data)

### DATA-Q5: Reliable Timestamps

- **Severity**: RISK
- **Finding**: No timestamps in API responses. The frontend renders HTML for most endpoints, which does not include metadata timestamps. The JSON endpoint `/product-meta/{ids}` returns the product protobuf message which does not contain `created_at`, `updated_at`, or `event_time` fields. Logging uses RFC3339Nano timestamps (`main.go` logrus configuration). Internal log entries have reliable timestamps, but API responses do not.
- **Gap**: Agents performing time-sensitive reasoning have no temporal metadata in API responses. They cannot determine data freshness or order events chronologically.
- **Compensating Controls**:
  - Use response timestamps from HTTP headers (Date header) as an approximate timestamp
  - Track freshness at the agent orchestration layer by recording when data was fetched
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `created_at` and `updated_at` fields to product and order data. Include temporal metadata in JSON API responses.
- **Evidence**: `handlers.go` (getProductByID returns Product proto without timestamps), `genproto/demo.pb.go` (Product message without timestamp fields), `main.go` (logrus with RFC3339Nano)

### DATA-Q6: Data Freshness Signaling

- **Severity**: RISK
- **Finding**: No data freshness signaling exists. No `Cache-Control` headers, no `X-Data-Age` headers, no `last_refreshed` fields, no `consistency_level` fields in any response. The application makes real-time gRPC calls to backend services for every request — data is current at the time of request, but this is not signaled to the caller. No caching layer is visible in the frontend code.
- **Gap**: Agents have no way to know whether data returned is current, cached, or eventually consistent. This is mitigated somewhat by the real-time nature of the gRPC calls, but the freshness guarantee is not explicit.
- **Compensating Controls**:
  - Assume data is fresh on each request (gRPC calls are synchronous to backend services)
  - Add cache-control metadata if caching is introduced in the future
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `Cache-Control` and freshness headers to JSON API responses. If caching is introduced, include `X-Data-Age` or equivalent headers.
- **Evidence**: `rpc.go` (synchronous gRPC calls to backend), `handlers.go` (no cache-control headers set)

### DATA-Q7: PII Redaction in Logs

- **Severity**: RISK
- **Finding**: No PII redaction in logs. The `chatBotHandler` in `handlers.go` uses `fmt.Printf("%+v\n", body)` to print raw response bodies to stdout, which may include customer data. Log entries include `http.req.path` which could contain product IDs but not PII directly. The `placeOrderHandler` processes credit card data (`credit_card_number`, `credit_card_cvv`) that flows through the application — while it is not explicitly logged, there is no PII scrubbing middleware to prevent accidental logging. No log scrubbing libraries, no Amazon Macie integration, no regex patterns for PII in logging utilities.
- **Gap**: No systematic PII redaction. The `fmt.Printf` in `chatBotHandler` prints unfiltered response data. No guardrails prevent future code changes from accidentally logging sensitive fields.
- **Compensating Controls**:
  - Replace `fmt.Printf` with structured logging that excludes sensitive fields
  - Add a log sanitization middleware to the logging pipeline
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Replace all `fmt.Printf` calls with structured logrus logging. Implement a PII scrubbing middleware that redacts credit card numbers, email addresses, and other sensitive fields from log output. Add log sanitization to the CI pipeline as a code review check.
- **Evidence**: `handlers.go` (chatBotHandler fmt.Printf printing raw bodies), `middleware.go` (logHandler logs path, method, session, status — no PII scrubbing)

### DISC-Q1: Schema Documentation and Versioning

- **Severity**: RISK
- **Finding**: The protobuf schema (`genproto/demo.pb.go`, auto-generated from `demo.proto` via `genproto.sh`) provides machine-readable data structure definitions for gRPC services: `CartItem`, `Product`, `Money`, `PlaceOrderRequest`, `CreditCardInfo`, `Address`, etc. However: (1) The schema is auto-generated and not versioned independently. (2) No JSON Schema files exist for the HTTP endpoints. (3) No database migration files. (4) No schema registry. (5) The protobuf source (`demo.proto`) is referenced in `genproto.sh` as `../../protos/demo.proto` — it exists outside this repository and its versioning is not visible.
- **Gap**: While protobuf definitions provide data structure documentation for gRPC, the HTTP API surface has no schema documentation. Schema changes to the protobuf would break both gRPC and HTTP interfaces without warning.
- **Compensating Controls**:
  - Use the protobuf definitions as reference documentation for data structures
  - Add OpenAPI schema definitions for the HTTP endpoints
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Version the protobuf definitions independently with a changelog. Add JSON Schema or OpenAPI schema definitions for the HTTP API endpoints. Integrate schema validation into the CI pipeline.
- **Evidence**: `genproto/demo.pb.go` (auto-generated protobuf), `genproto.sh` (generation script referencing external proto file)

### OBS-Q1: Distributed Tracing and Structured Logging

- **Severity**: RISK
- **Finding**: Strong observability foundations exist but are not fully enabled. OpenTelemetry is integrated: `otelgrpc.NewClientHandler()` for gRPC calls (`main.go`), `otelhttp.NewHandler` for HTTP (`main.go`), OTLP trace exporter via `otlptracegrpc` (`main.go` `initTracing`). Trace propagation uses `TraceContext` and `Baggage` (`main.go`). Logging is structured JSON via logrus with fields: `timestamp`, `severity`, `message`, `http.req.path`, `http.req.method`, `http.req.id`, `session`, `http.resp.took_ms`, `http.resp.status`, `http.resp.bytes` (`middleware.go`). Request IDs are UUIDs (`middleware.go`). However: tracing is gated by `ENABLE_TRACING=1` environment variable and is **disabled by default** (`helm-chart/values.yaml` `googleCloudOperations.tracing: false`). The correlation between `http.req.id` and OpenTelemetry `trace_id` is not explicit in log entries.
- **Gap**: Tracing is available but disabled by default. Logs lack trace ID correlation. Without tracing enabled, diagnosing agent-initiated request failures across the 7 backend services requires manual log correlation.
- **Compensating Controls**:
  - Enable tracing by setting `ENABLE_TRACING=1` in the deployment environment
  - Use the `http.req.id` as a correlation ID for log-based debugging
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Enable tracing by default in all environments. Add `trace_id` and `span_id` fields to structured log entries for correlation. Configure the OpenTelemetry collector to export traces to a centralized backend.
- **Evidence**: `main.go` (OpenTelemetry setup, ENABLE_TRACING gate), `middleware.go` (structured logging with request_id), `helm-chart/values.yaml` (tracing disabled by default)

### OBS-Q2: Alerting on Error Rates and Latency

- **Severity**: RISK
- **Finding**: No alerting configuration found anywhere in the repository. No CloudWatch alarms, no GCP Monitoring alerts, no anomaly detection, no PagerDuty/OpsGenie integration, no SLO-based alerting. The CI pipeline includes a smoke test using the `loadgenerator` (`ci-pr.yaml`) that checks for zero errors after 50 requests, but this is a deployment-time validation, not runtime alerting. No Prometheus `ServiceMonitor` or alerting rules.
- **Gap**: Target system degradation is not automatically detected. Agents consuming this service will not receive warnings before the service degrades, and operations teams will not be alerted to agent-induced load problems.
- **Compensating Controls**:
  - Implement alerting at the Kubernetes/GKE monitoring layer (GCP Monitoring, Prometheus)
  - Configure agent-side health checks that probe the `/_healthz` endpoint before making requests
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure alerting thresholds for error rates (>1% 5xx errors), latency (P95 > 2 seconds), and throughput anomalies on the frontend service. Integrate with an incident management platform.
- **Evidence**: `.github/workflows/ci-pr.yaml` (smoke test, not runtime alerting), absence of any alerting configuration files

### ENG-Q1: Infrastructure Governance for Agent-Facing Surface

- **Severity**: RISK
- **Finding**: Infrastructure is partially defined as code: Terraform defines the GKE cluster and Memorystore Redis (`terraform/main.tf`, `terraform/memorystore.tf`). Kubernetes manifests define the frontend deployment, service, and service account (`kubernetes-manifests/frontend.yaml`). Helm chart provides templated deployment (`helm-chart/`). Istio manifests define the gateway and virtual service (`istio-manifests/`). However: (1) No drift detection is configured (no AWS Config rules, no Terraform Cloud drift detection, no `terraform plan` in CI). (2) PR review is implied by GitHub Actions (`ci-pr.yaml` runs on `pull_request`) but no explicit `terraform plan` review step exists in the CI pipeline. (3) The Terraform CI workflow (`terraform-validate-ci.yaml`) exists separately but only validates — it does not run `plan` for review. (4) IaC is GCP-focused, not AWS.
- **Gap**: IaC exists but two of three governance sub-checks are incomplete: no drift detection and no automated plan review in CI. Changes to the agent-facing infrastructure surface (API Gateway, network policies) could be deployed without proper review.
- **Compensating Controls**:
  - Add `terraform plan` output to PR reviews
  - Implement drift detection using GCP Config Connector or Terraform Cloud
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a `terraform plan` step to the CI pipeline that outputs the plan as a PR comment. Configure drift detection for the GKE cluster, network policies, and Istio configurations.
- **Evidence**: `terraform/main.tf` (GKE cluster IaC), `kubernetes-manifests/frontend.yaml` (K8s manifests), `helm-chart/` (Helm templates), `.github/workflows/ci-pr.yaml` (PR-triggered CI without terraform plan)

### ENG-Q2: CI/CD with API Contract Testing

- **Severity**: RISK
- **Finding**: CI/CD pipelines exist via GitHub Actions (`ci-pr.yaml`, `ci-main.yaml`) and Cloud Build (`cloudbuild.yaml`). The CI pipeline runs Go unit tests for `frontend/validator` and other services (`ci-pr.yaml`). Deployment uses Skaffold to GKE. A smoke test validates end-to-end functionality using the `loadgenerator`. However: no API contract testing exists (no Pact, no OpenAPI spec validation, no schema comparison tools). No breaking change detection. Tests are unit-level only (validator input validation, money arithmetic). The smoke test validates that the system works end-to-end but does not validate API contract stability.
- **Gap**: API changes that break agent tool schemas are not detected before deployment. No contract tests exist for the agent-facing endpoints.
- **Compensating Controls**:
  - Use the loadgenerator smoke test as a basic integration check
  - Pin agent tool definitions to specific API behavior and test manually on each release
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add API contract tests for the JSON endpoints (`/product-meta/{ids}`, `/bot`). Integrate OpenAPI spec validation into the CI pipeline once a spec is created (API-Q2). Add consumer-driven contract tests (Pact) for the gRPC interfaces.
- **Evidence**: `.github/workflows/ci-pr.yaml` (unit tests and smoke test), `validator/validator_test.go` (input validation tests), `money/money_test.go` (arithmetic tests)

### ENG-Q3: Rollback Capability

- **Severity**: RISK
- **Finding**: Deployment uses Skaffold to GKE with namespace-based PR environments (`ci-pr.yaml`). Kubernetes supports rolling updates by default. The Helm chart would support rollback via `helm rollback`, but no automated rollback triggers are configured. No blue/green deployment, no canary deployment, no CodeDeploy rollback triggers, no traffic shifting at the Istio gateway. No feature flags for gradual rollout.
- **Gap**: No automated rollback mechanism. If a deployment breaks agent-facing APIs, rollback requires manual intervention. Target: rollback within 15-30 minutes.
- **Compensating Controls**:
  - Use `helm rollback` or `kubectl rollout undo` for manual rollback
  - Use PR-based staging environments to validate before merging to main
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure automated rollback triggers based on error rate thresholds. Implement canary deployments with automatic rollback using Istio traffic splitting or Flagger.
- **Evidence**: `.github/workflows/ci-pr.yaml` (Skaffold deployment), `helm-chart/` (Helm chart supports rollback), `istio-manifests/frontend.yaml` (VirtualService for traffic routing)

### ENG-Q4: API Test Coverage

- **Severity**: RISK
- **Finding**: Unit tests exist for: `validator/validator_test.go` (28 test cases covering AddToCart, PlaceOrder, SetCurrency input validation) and `money/money_test.go` (comprehensive money arithmetic tests). The CI pipeline (`ci-pr.yaml`) runs these tests and a smoke test using the `loadgenerator`. However: no API-level tests exist for the HTTP handlers. No integration tests for the gRPC client calls. No tests for the JSON endpoints (`/product-meta/{ids}`, `/bot`). No tests for error handling paths. No tests for the middleware chain.
- **Gap**: Agent-facing endpoints have zero direct test coverage. Input validation is tested, but the HTTP handler behavior (routing, response format, error handling, middleware chain) is not tested.
- **Compensating Controls**:
  - Rely on the loadgenerator smoke test for basic end-to-end validation
  - Add manual testing of agent-facing endpoints to the release process
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add HTTP handler tests for the JSON-serving endpoints (`/product-meta/{ids}`, `/bot`). Test error responses, edge cases (invalid IDs, malformed requests), and response format consistency. Run these tests in CI.
- **Evidence**: `validator/validator_test.go` (28 test cases), `money/money_test.go` (comprehensive arithmetic tests), `.github/workflows/ci-pr.yaml` (smoke test via loadgenerator)

### ENG-Q5: Encryption at Rest for Agent-Accessible Data

- **Severity**: RISK
- **Finding**: No encryption-at-rest configuration found for agent-accessible data. The Terraform defines a GKE Autopilot cluster (`terraform/main.tf`) — GKE Autopilot encrypts data at rest by default using Google-managed keys, but no customer-managed KMS keys are configured. The Memorystore Redis instance (`terraform/memorystore.tf`) has no explicit encryption settings (Redis 7.0 supports in-transit encryption but at-rest encryption depends on configuration). No `kms_key_id` on any resource. No explicit encryption configuration in Kubernetes manifests.
- **Gap**: While GKE Autopilot provides default encryption, there is no explicit customer-managed encryption configuration. The Redis instance lacks documented encryption settings. Sensitive data (credit card info, customer PII) may be stored in transit through Redis without explicit encryption guarantees.
- **Compensating Controls**:
  - Rely on GKE Autopilot's default encryption at rest (Google-managed keys)
  - Enable Memorystore Redis in-transit encryption
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure customer-managed KMS keys for the GKE cluster and Memorystore Redis. Document the encryption posture for all data stores. Add `kms_key_id` to Terraform resource configurations.
- **Evidence**: `terraform/main.tf` (GKE Autopilot, no KMS config), `terraform/memorystore.tf` (Redis instance, no encryption config)

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO
- **Finding**: The frontend exposes HTTP routes via gorilla/mux (`main.go`): `GET /` (home), `GET /product/{id}` (product page), `GET /cart`, `POST /cart` (add to cart), `POST /cart/empty`, `POST /setCurrency`, `GET /logout`, `POST /cart/checkout`, `GET /assistant`, `GET /product-meta/{ids}` (JSON), `POST /bot` (JSON), `GET /_healthz`. The application primarily serves HTML via Go templates, with two JSON-serving endpoints: `/product-meta/{ids}` returns product data as JSON, `/bot` returns chatbot responses as JSON. The frontend also communicates with 7 backend gRPC services. An HTTP interface exists — the application does not require direct database access, file-based exchange, or UI automation for integration.
- **Implication**: Agent integration is feasible through the JSON-serving endpoints (`/product-meta/{ids}`, `/bot`). The HTML-serving endpoints require either HTML parsing or new JSON APIs. The gRPC backend connections could be used directly for a more efficient integration surface.
- **Recommendation**: Create dedicated JSON API endpoints for all data an agent needs (products, cart, checkout). Consider exposing the gRPC service definitions as a first-class agent integration surface.
- **Evidence**: `main.go` (route definitions via gorilla/mux), `handlers.go` (getProductByID returns JSON, chatBotHandler returns JSON)

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No idempotency key support on write endpoints. `POST /cart` (addToCartHandler) adds items without idempotency checks — duplicate POSTs add duplicate quantities. `POST /cart/checkout` (placeOrderHandler) places a new order on every call with no idempotency key. `POST /cart/empty` (emptyCartHandler) is naturally idempotent (emptying an empty cart is a no-op). `POST /setCurrency` (setCurrencyHandler) is naturally idempotent (setting the same currency is a no-op).
- **Implication**: For a read-only agent scope, this is informational only. If the agent scope is later expanded to write-enabled, idempotency on `/cart` and `/cart/checkout` becomes a BLOCKER.
- **Recommendation**: Plan for idempotency key support on write endpoints (`POST /cart`, `POST /cart/checkout`) before enabling write-access agents.
- **Evidence**: `handlers.go` (addToCartHandler, placeOrderHandler with no idempotency keys)

### API-Q6: Structured Response Format

- **Severity**: INFO
- **Finding**: Mixed response format. Most endpoints return HTML via Go templates (`templates/*.html`): `home.html`, `product.html`, `cart.html`, `order.html`, `error.html`. Two endpoints return JSON: `/product-meta/{ids}` returns a JSON-marshaled `pb.Product` protobuf message, `/bot` returns `{"message": "..."}`. The gRPC backend communication uses protobuf. No XML, no binary response formats for the HTTP surface.
- **Implication**: The JSON endpoints are directly consumable by agents. The HTML endpoints require either HTML parsing (fragile) or new JSON API endpoints. The protobuf-based gRPC interfaces are efficient but require gRPC client integration.
- **Recommendation**: Prioritize creating JSON API versions of the product listing and cart endpoints for agent consumption.
- **Evidence**: `handlers.go` (getProductByID uses json.Marshal, chatBotHandler uses json.NewEncoder), `templates/` (HTML templates for other endpoints)

### API-Q8: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: No event emission capability exists. No webhook endpoints, no SNS/EventBridge/SQS/Pub/Sub integration, no Kafka topics, no CDC pipelines. The application is purely request-response. State changes (cart updates, order placement) are not emitted as events. The `placeOrderHandler` logs the order ID but does not publish an event.
- **Implication**: Agents must poll for state changes rather than react to events. For the current read-only scope, this is acceptable. For future use cases requiring real-time reaction to order completions or cart changes, event emission would be needed.
- **Recommendation**: Consider adding event emission for key state changes (order placed, cart updated) via GCP Pub/Sub or equivalent when expanding to proactive agent use cases.
- **Evidence**: `handlers.go` (placeOrderHandler logs but does not emit events), `main.go` (no event infrastructure)

### API-Q9: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No API rate limits are documented. No `X-RateLimit-Remaining`, `X-RateLimit-Limit`, or `Retry-After` headers in any response. No API Gateway throttle settings. No WAF rate rules. No rate limiting documentation in the repository.
- **Implication**: Agents calling endpoints at machine speed have no feedback mechanism to self-throttle. Without rate limit headers, agents cannot proactively slow down before hitting limits.
- **Recommendation**: When rate limiting is implemented (STATE-Q5), include rate limit headers in responses so agents can self-throttle.
- **Evidence**: `handlers.go` (no rate limit headers set), `main.go` (no rate limiting middleware)

### API-Q10: API Latency Profile

- **Severity**: INFO
- **Finding**: No performance benchmarks or load test results found. Observable timeouts: ad service call has a 100ms timeout (`rpc.go` `getAd`), gRPC connection establishment has a 3-second timeout (`main.go` `mustConnGRPC`). The home page handler makes multiple sequential gRPC calls (getCurrencies, getProducts, getCart, convertCurrency per product, chooseAd), which creates additive latency. No CloudWatch/GCP Monitoring latency metrics configured. The smoke test in CI validates functionality but not latency.
- **Implication**: The home page's sequential gRPC call pattern creates cumulative latency. An agent calling this endpoint may experience 1-5 second response times depending on backend service performance. The ad service 100ms timeout limits that specific call's impact. No P95 baseline exists for capacity planning.
- **Recommendation**: Conduct latency profiling of the agent-facing endpoints. Consider parallelizing independent gRPC calls (e.g., getCurrencies and getProducts can be concurrent). Establish P95 latency baselines.
- **Evidence**: `rpc.go` (getAd 100ms timeout), `main.go` (mustConnGRPC 3-second timeout), `handlers.go` (homeHandler sequential calls)

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Field names are semantically meaningful throughout the codebase. Protobuf fields use clear naming: `product_id`, `quantity`, `currency_code`, `street_address`, `credit_card_number`, `credit_card_cvv`, `credit_card_expiration_month`. Go structs use readable names: `frontendServer`, `productCatalogSvcAddr`, `currencySvcConn`, `AddToCartPayload`, `PlaceOrderPayload`. Validator fields are self-documenting: `Email`, `StreetAddress`, `ZipCode`, `City`, `State`, `Country`. No legacy abbreviations found.
- **Implication**: LLM-based agents can interpret field names directly without a data dictionary lookup. This accelerates tool definition and reduces interpretation errors.
- **Recommendation**: Maintain this naming convention. Document any domain-specific terms (e.g., `Nanos` in the Money type) for agent tool builders.
- **Evidence**: `genproto/demo.pb.go` (protobuf field names), `validator/validator.go` (payload struct fields), `main.go` (Go struct fields)

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No data catalog or metadata layer exists. No AWS Glue Data Catalog, no Collibra, no Alation, no DataHub, no metadata files, no data dictionaries. The protobuf definitions (`genproto/demo.pb.go`) serve as an implicit schema catalog for the gRPC service interfaces but are not published as a discoverable metadata layer.
- **Implication**: Building agent tools against this system requires reading the source code directly. There is no discovery mechanism for what data the system holds or what it means.
- **Recommendation**: Create a lightweight data dictionary documenting the entities (Product, Cart, Order, Currency), their fields, and their relationships. Publish this alongside the API documentation.
- **Evidence**: Absence of any data catalog, metadata, or data dictionary files in the repository

### DISC-Q4: Data Lineage

- **Severity**: INFO
- **Finding**: No data lineage exists. No lineage tools (AWS Glue DataBrew, Apache Atlas), no ETL documentation, no data flow diagrams, no source-to-target mappings, no transformation logs. The frontend is a pass-through gateway — data flows from backend gRPC services through the frontend to the user. The data transformation is minimal (currency conversion, price multiplication).
- **Implication**: If an agent produces incorrect output due to bad data, tracing the data source requires manual investigation across the 7 backend services. The minimal transformation in the frontend means most data quality issues originate in backend services.
- **Recommendation**: Document the data flow from each backend service through the frontend to the user. Identify which transformations occur in the frontend (currency conversion, price calculation).
- **Evidence**: `rpc.go` (backend service delegation), `handlers.go` (currency conversion, price multiplication in viewCartHandler)

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No business outcome metrics are published. No custom CloudWatch metrics, no GCP custom metrics, no business KPI dashboards. The application logs order placement (`handlers.go`: `log.WithField("order", order.GetOrder().GetOrderId()).Info("order placed")`) but this is a log entry, not a metric. No tracking of order completion rates, cart abandonment, conversion rates, or customer satisfaction.
- **Implication**: When agents consume this system, there is no way to measure whether agent interactions produce good business outcomes. Infrastructure metrics (latency, error rates) alone are insufficient for evaluating agent effectiveness.
- **Recommendation**: Publish custom metrics for key business events: orders placed, cart abandonment rate, average order value. These become the primary signal for whether agent interactions produce value.
- **Evidence**: `handlers.go` (order placed log entry, no metrics), absence of any metrics publishing code

### DATA-Q8: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality metrics, dashboards, or monitoring exist. No duplicate detection, no freshness SLAs, no null rate monitoring, no data profiling reports. The frontend trusts data from backend services without quality validation (beyond format validation in `validator/validator.go`). Product data, pricing, and recommendations are consumed as-is from backend gRPC services.
- **Implication**: Agents acting on incomplete or stale data from backend services will propagate errors. There is no visibility into data quality issues until they manifest as agent errors.
- **Recommendation**: Add data quality checks for critical data paths: validate product prices are positive, verify currency codes are valid, check that recommended products exist. Publish data quality metrics.
- **Evidence**: `rpc.go` (backend data consumed without quality checks), `validator/validator.go` (input format validation only)

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: The frontend exposes HTTP routes via gorilla/mux (`main.go`) including `GET /`, `GET /product/{id}`, `GET /cart`, `POST /cart`, `POST /cart/empty`, `POST /setCurrency`, `GET /logout`, `POST /cart/checkout`, `GET /assistant`, `GET /product-meta/{ids}` (JSON), `POST /bot` (JSON), `GET /_healthz`. An HTTP interface exists. The application does not require direct database access, file-based exchange, or UI automation.
- **Gap**: The interface is primarily HTML-serving with only 2 JSON endpoints. Not optimized for machine consumption.
- **Recommendation**: Create dedicated JSON API endpoints for agent-consumable data.
- **Evidence**: `main.go`, `handlers.go`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK
- **Finding**: No OpenAPI, AsyncAPI, GraphQL schema, or Smithy specification found. Protobuf definitions exist for gRPC but not for the HTTP surface.
- **Gap**: No machine-readable spec for the HTTP endpoints an agent would consume.
- **Recommendation**: Generate an OpenAPI 3.0 spec from the gorilla/mux route definitions.
- **Evidence**: `main.go`, `genproto.sh`, absence of `openapi.yaml`/`swagger.yaml`

#### API-Q3: Structured Error Responses
- **Severity**: RISK
- **Finding**: `renderHTTPError` in `handlers.go` renders HTML error pages. JSON endpoints return HTML errors or silently fail. No structured error codes, categories, or retryable booleans.
- **Gap**: Agents cannot programmatically distinguish retriable errors from terminal errors.
- **Recommendation**: Implement structured JSON error responses with `error_code`, `message`, `retryable` fields.
- **Evidence**: `handlers.go` (renderHTTPError), `templates/error.html`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No idempotency key support on write endpoints. `POST /cart` and `POST /cart/checkout` are non-idempotent. `POST /cart/empty` and `POST /setCurrency` are naturally idempotent.
- **Gap**: Non-idempotent write endpoints. Informational for read-only agent scope.
- **Recommendation**: Plan idempotency key support before enabling write-access agents.
- **Evidence**: `handlers.go` (addToCartHandler, placeOrderHandler)

#### API-Q5: API Versioning and Deprecation
- **Severity**: RISK
- **Finding**: No API versioning. No `/v1/` paths, no version headers, no changelog, no deprecation policy.
- **Gap**: API changes will silently break agent tool schemas.
- **Recommendation**: Introduce URL-based versioning for agent-facing endpoints.
- **Evidence**: `main.go` (unversioned route definitions)

#### API-Q6: Structured Response Format
- **Severity**: INFO
- **Finding**: Mixed format — most endpoints return HTML via Go templates. `/product-meta/{ids}` and `/bot` return JSON. gRPC backend uses protobuf.
- **Gap**: Limited JSON surface for agent consumption.
- **Recommendation**: Create JSON API versions of product listing and cart endpoints.
- **Evidence**: `handlers.go`, `templates/`

#### API-Q7: Asynchronous Operation Support
- **Severity**: RISK
- **Finding**: All handlers are synchronous request-response. No background job frameworks, polling endpoints, or webhook callbacks.
- **Gap**: Long-running operations (checkout) may cause agent timeouts.
- **Recommendation**: Implement async pattern for checkout with job ID and polling endpoint.
- **Evidence**: `handlers.go`, `rpc.go` (getAd 100ms timeout)

#### API-Q8: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: No event emission. No webhooks, no Pub/Sub, no Kafka. Purely request-response.
- **Gap**: Agents must poll for state changes.
- **Recommendation**: Add event emission for key state changes when expanding to proactive agent use cases.
- **Evidence**: `handlers.go`, `main.go`

#### API-Q9: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limits documented. No `X-RateLimit-Remaining` or `Retry-After` headers. No API Gateway throttle or WAF rate rules.
- **Gap**: Agents have no self-throttling feedback.
- **Recommendation**: Include rate limit headers when rate limiting is implemented.
- **Evidence**: `handlers.go`, `main.go`

#### API-Q10: API Latency Profile
- **Severity**: INFO
- **Finding**: No performance benchmarks. Ad service has 100ms timeout (`rpc.go`). gRPC connection timeout is 3 seconds (`main.go`). Home page makes sequential gRPC calls creating additive latency.
- **Gap**: No P95 baseline. Sequential call pattern creates cumulative latency.
- **Recommendation**: Conduct latency profiling. Parallelize independent gRPC calls.
- **Evidence**: `rpc.go`, `main.go`, `handlers.go`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: No authentication mechanism exists. Session identity is a random UUID in an unsigned cookie (`middleware.go`). gRPC connections use `insecure.NewCredentials()` (`main.go`). No OAuth2, API key, mTLS, or service account auth. No principal attribution in logs.
- **Gap**: Zero authentication. No mechanism to authenticate agent identities or attribute API calls.
- **Recommendation**: Implement API key or OAuth2 client credentials authentication on agent-facing endpoints.
- **Evidence**: `main.go`, `middleware.go`, `handlers.go`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK
- **Finding**: No authorization model. All endpoints accessible without permission checks. Kubernetes ServiceAccount `frontend` has no RBAC. Istio AuthorizationPolicies disabled by default.
- **Gap**: All-or-nothing access. No scoped permissions for agents.
- **Recommendation**: Enable Istio AuthorizationPolicies with per-route rules.
- **Evidence**: `kubernetes-manifests/frontend.yaml`, `helm-chart/values.yaml`, `helm-chart/templates/frontend.yaml`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK
- **Finding**: No action-level authorization. No ABAC, RBAC, or method-level middleware. Istio AuthorizationPolicy (disabled) restricts by method/port but not by path.
- **Gap**: Agents cannot be restricted to read-only operations.
- **Recommendation**: Implement route-level authorization middleware or Istio path-based rules.
- **Evidence**: `handlers.go`, `main.go`

#### AUTH-Q4: Identity Propagation
- **Severity**: RISK
- **Finding**: No identity propagation. Session ID is random UUID passed as `userId` in gRPC calls. No JWT, no OAuth2 token exchange, no on-behalf-of flows.
- **Gap**: Cannot carry user context end-to-end. Backend services receive random UUID, not authenticated identity.
- **Recommendation**: Implement JWT-based identity propagation through gRPC metadata.
- **Evidence**: `middleware.go`, `handlers.go`

#### AUTH-Q5: Agent-as-Self vs Agent-on-Behalf-of-User
- **Severity**: RISK
- **Finding**: No agent identity concept. All callers treated identically as anonymous sessions. No differentiation between agent modes.
- **Gap**: Cannot distinguish agent-as-self from agent-on-behalf-of-user.
- **Recommendation**: Define separate authentication modes for each access pattern.
- **Evidence**: `middleware.go`, `handlers.go`

#### AUTH-Q6: Credential Management
- **Severity**: RISK
- **Finding**: Service addresses via env vars. gRPC uses insecure credentials. Hard-coded session ID `12345678-1234-1234-1234-123456789123` in `middleware.go`. No secrets management system.
- **Gap**: Insecure gRPC connections. Hard-coded session ID. No credential rotation mechanism.
- **Recommendation**: Implement mTLS via Istio. Integrate secrets management. Remove hard-coded session ID.
- **Evidence**: `main.go`, `middleware.go`, `kubernetes-manifests/frontend.yaml`

#### AUTH-Q7: Immutable Audit Logging ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: Structured JSON logging via logrus with request fields. No authenticated principal in logs. No immutable log storage. `chatBotHandler` uses `fmt.Printf` for raw output.
- **Gap**: Logs lack identity attribution and immutability guarantees.
- **Recommendation**: Add principal fields to logs. Configure immutable log storage. Replace `fmt.Printf` with structured logging.
- **Evidence**: `main.go`, `middleware.go`, `handlers.go`

#### AUTH-Q8: Agent Identity Suspension
- **Severity**: RISK
- **Finding**: No agent identity suspension mechanism. No API keys, IAM roles, or service accounts to revoke. No concept of agent identities.
- **Gap**: Cannot isolate a misbehaving agent without affecting all traffic.
- **Recommendation**: Implement API key-based auth with per-key revocation capability.
- **Evidence**: `middleware.go`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: No compensation or rollback for multi-step operations. `placeOrderHandler` calls `PlaceOrder` as a single gRPC call. No saga pattern, no undo endpoints, no Step Functions. Cart-to-checkout flow has no compensation.
- **Gap**: Failed multi-step workflows leave application in partial state.
- **Recommendation**: Implement compensation endpoints and error handling with cleanup.
- **Evidence**: `handlers.go`, `rpc.go`

#### STATE-Q2: Queryable Current State
- **Severity**: RISK
- **Finding**: GET endpoints return current state but mostly as HTML. Only `/product-meta/{ids}` returns JSON. No operation status APIs.
- **Gap**: Limited machine-readable state queries.
- **Recommendation**: Add JSON-returning endpoints for cart and order status.
- **Evidence**: `main.go`, `handlers.go`

#### STATE-Q3: Concurrency Controls
- **Severity**: RISK
- **Finding**: No concurrency controls. No optimistic locking, ETags, version fields, or conditional writes. Cart operations make direct gRPC calls without safeguards.
- **Gap**: Concurrent agents on same session could produce inconsistent state.
- **Recommendation**: Implement optimistic locking on cart operations.
- **Evidence**: `rpc.go`, `handlers.go`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK
- **Finding**: Ad service has 100ms timeout. gRPC connection has 3-second timeout. Recommendation failures handled gracefully. No circuit breakers, no retry with backoff, no bulkhead isolation.
- **Gap**: No circuit breaker protection. Failing backend cascades to all callers.
- **Recommendation**: Add circuit breakers via Go library or Istio DestinationRules.
- **Evidence**: `rpc.go`, `main.go`, `handlers.go`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK
- **Finding**: No rate limiting at any layer. No API Gateway throttling, no WAF, no application-level middleware.
- **Gap**: Runaway agent loops could overwhelm the system.
- **Recommendation**: Add rate limiting middleware or configure Istio rate limiting.
- **Evidence**: `go.mod`, `main.go`, `helm-chart/values.yaml`

#### STATE-Q6: Blast Radius and Transaction Limits
- **Severity**: RISK
- **Finding**: No per-agent transaction limits. Only input validation (quantity 1-10 per cart add). No max orders/hour, max spend, or per-session limits.
- **Gap**: Agents can execute unlimited operations with no business safeguards.
- **Recommendation**: Implement configurable per-agent limits for high-impact operations.
- **Evidence**: `validator/validator.go`, `handlers.go`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: RISK
- **Finding**: K8s resource limits defined (100m-200m CPU, 64Mi-128Mi memory). GKE Autopilot provides auto-scaling. No load tests, no HPA, no capacity documentation.
- **Gap**: Capacity under agent traffic patterns is unknown.
- **Recommendation**: Define HPA policies. Conduct load testing simulating agent traffic.
- **Evidence**: `kubernetes-manifests/frontend.yaml`, `terraform/main.tf`, `.github/workflows/ci-pr.yaml`

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State
- **Severity**: RISK
- **Finding**: No formal draft/pending state. `placeOrderHandler` immediately executes via gRPC `PlaceOrder`. Cart serves as an implicit draft but no formal pending order state.
- **Gap**: Agents cannot propose actions for human review before execution.
- **Recommendation**: Introduce a "pending order" state between cart and order placement.
- **Evidence**: `handlers.go`

#### HITL-Q2: Configurable Approval Gates
- **Severity**: RISK
- **Finding**: No configurable approval gates. All operations execute immediately. No Step Functions with human approval tasks.
- **Gap**: High-risk operations cannot require human approval.
- **Recommendation**: Add configurable operation-level confirmation requirements.
- **Evidence**: `handlers.go`, `main.go`

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK
- **Finding**: CI/CD deploys to PR-specific K8s namespaces. Helm/Kustomize support multiple environments. `ENABLE_SINGLE_SHARED_SESSION` for testing. No documented sandbox with production-equivalent data.
- **Gap**: No production-equivalent sandbox for agent testing.
- **Recommendation**: Create dedicated staging environment with seed data scripts.
- **Evidence**: `.github/workflows/ci-pr.yaml`, `middleware.go`, `Dockerfile`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: `placeOrderHandler` processes sensitive data: email, street_address, credit_card_number, credit_card_cvv. Credit card data passed directly to checkout gRPC service without encryption or classification. `validator/validator.go` validates format only. No PII detection, tagging, or field-level access controls.
- **Gap**: PCI-relevant data flows without classification or access controls.
- **Recommendation**: Classify all sensitive fields. Implement field-level encryption for credit card data.
- **Evidence**: `handlers.go`, `validator/validator.go`, `genproto/demo.pb.go`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: No data residency configuration. Terraform defaults to `us-central1`. No GDPR/LGPD references. No sovereignty policies documented.
- **Gap**: No data residency controls or documentation for customer PII.
- **Recommendation**: Document residency requirements. Ensure deployment region aligns with compliance needs.
- **Evidence**: `terraform/variables.tf`, `handlers.go`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK
- **Finding**: No pagination, filtering, or sorting. `getProducts` returns all products with no filters. Recommendations capped at 4. No limit/offset/cursor parameters.
- **Gap**: Full catalog returned with no selective query capability.
- **Recommendation**: Add pagination and filtering to product endpoints.
- **Evidence**: `rpc.go`, `handlers.go`

#### DATA-Q4: System of Record Designations
- **Severity**: RISK
- **Finding**: No system-of-record designations. Frontend delegates to 7 backend services. No documentation of authoritative sources per entity.
- **Gap**: Agents cannot determine authoritative data sources.
- **Recommendation**: Create data ownership documentation mapping entities to authoritative services.
- **Evidence**: `main.go`, `rpc.go`

#### DATA-Q5: Reliable Timestamps
- **Severity**: RISK
- **Finding**: No timestamps in API responses. Product protobuf lacks temporal fields. Logging uses RFC3339Nano internally.
- **Gap**: No temporal metadata for agent reasoning.
- **Recommendation**: Add `created_at`/`updated_at` to API responses.
- **Evidence**: `handlers.go`, `genproto/demo.pb.go`, `main.go`

#### DATA-Q6: Data Freshness Signaling
- **Severity**: RISK
- **Finding**: No freshness signaling. No Cache-Control, X-Data-Age, or consistency_level headers. Real-time gRPC calls provide de facto freshness.
- **Gap**: Freshness not explicitly communicated to callers.
- **Recommendation**: Add Cache-Control and freshness headers to JSON responses.
- **Evidence**: `rpc.go`, `handlers.go`

#### DATA-Q7: PII Redaction in Logs
- **Severity**: RISK
- **Finding**: No PII redaction. `chatBotHandler` uses `fmt.Printf` to print raw response bodies. No log scrubbing middleware. Credit card data flows through `placeOrderHandler` without logging safeguards.
- **Gap**: No systematic PII redaction in logs.
- **Recommendation**: Replace `fmt.Printf` with structured logging. Implement PII scrubbing middleware.
- **Evidence**: `handlers.go`, `middleware.go`

#### DATA-Q8: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics, dashboards, or monitoring. Frontend trusts backend data without quality validation.
- **Gap**: No visibility into data quality issues.
- **Recommendation**: Add quality checks for critical data paths.
- **Evidence**: `rpc.go`, `validator/validator.go`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Documentation and Versioning
- **Severity**: RISK
- **Finding**: Protobuf schema (`genproto/demo.pb.go`) provides machine-readable data structures for gRPC. Auto-generated, not versioned independently. No JSON Schema for HTTP endpoints. No schema registry. Proto source external to this repo.
- **Gap**: HTTP API surface has no schema documentation. Protobuf changes break interfaces without warning.
- **Recommendation**: Version protobuf definitions independently. Add OpenAPI schemas for HTTP endpoints.
- **Evidence**: `genproto/demo.pb.go`, `genproto.sh`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Field names are semantically meaningful: `product_id`, `quantity`, `currency_code`, `street_address`, `AddToCartPayload`, `PlaceOrderPayload`. No legacy abbreviations.
- **Gap**: None — naming is clear.
- **Recommendation**: Maintain naming conventions. Document domain-specific terms.
- **Evidence**: `genproto/demo.pb.go`, `validator/validator.go`, `main.go`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No data catalog. No Glue, Collibra, Alation, or DataHub. Protobuf serves as implicit schema catalog.
- **Gap**: No discovery mechanism for system data.
- **Recommendation**: Create lightweight data dictionary for entities and relationships.
- **Evidence**: Absence of data catalog files

#### DISC-Q4: Data Lineage
- **Severity**: INFO
- **Finding**: No data lineage tools, documentation, or flow diagrams. Frontend is a pass-through gateway with minimal transformation.
- **Gap**: Data source tracing requires manual investigation.
- **Recommendation**: Document data flow from backend services through frontend.
- **Evidence**: `rpc.go`, `handlers.go`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK
- **Finding**: OpenTelemetry integrated (otelgrpc, otelhttp, OTLP exporter). Trace propagation via TraceContext and Baggage. Structured JSON logging via logrus with request fields. However, tracing disabled by default (`ENABLE_TRACING` not set, `helm-chart/values.yaml` `tracing: false`). No trace_id/log correlation.
- **Gap**: Strong foundation but disabled by default. No trace-log correlation.
- **Recommendation**: Enable tracing by default. Add trace_id to log entries.
- **Evidence**: `main.go`, `middleware.go`, `helm-chart/values.yaml`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK
- **Finding**: No alerting configuration. No CloudWatch/GCP Monitoring alerts. No PagerDuty/OpsGenie. CI smoke test is deployment-time only.
- **Gap**: No runtime alerting on degradation.
- **Recommendation**: Configure error rate and latency alerting thresholds.
- **Evidence**: `.github/workflows/ci-pr.yaml`, absence of alerting config

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No business metrics. Order placement logged but not published as metric. No dashboards for conversion, abandonment, or satisfaction.
- **Gap**: No business outcome visibility for agent interactions.
- **Recommendation**: Publish custom metrics for key business events.
- **Evidence**: `handlers.go`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK
- **Finding**: IaC exists (Terraform, K8s manifests, Helm, Istio). No drift detection. No `terraform plan` in CI. Terraform CI only validates syntax.
- **Gap**: Two of three governance sub-checks incomplete (no drift detection, no plan review).
- **Recommendation**: Add terraform plan to CI. Configure drift detection.
- **Evidence**: `terraform/main.tf`, `kubernetes-manifests/frontend.yaml`, `helm-chart/`, `.github/workflows/ci-pr.yaml`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK
- **Finding**: CI/CD via GitHub Actions and Cloud Build. Unit tests for validator and money. Smoke test via loadgenerator. No API contract testing, no Pact, no OpenAPI validation, no breaking change detection.
- **Gap**: API contract changes not detected before deployment.
- **Recommendation**: Add contract tests for JSON endpoints. Integrate OpenAPI spec validation.
- **Evidence**: `.github/workflows/ci-pr.yaml`, `validator/validator_test.go`, `money/money_test.go`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK
- **Finding**: Skaffold deploys to GKE. K8s rolling updates by default. Helm supports `helm rollback`. No automated rollback triggers, no canary, no blue/green.
- **Gap**: No automated rollback. Manual intervention required.
- **Recommendation**: Configure automated rollback triggers. Implement canary with Istio/Flagger.
- **Evidence**: `.github/workflows/ci-pr.yaml`, `helm-chart/`, `istio-manifests/frontend.yaml`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK
- **Finding**: Unit tests for validator (28 cases) and money arithmetic. CI smoke test. No HTTP handler tests, no integration tests, no JSON endpoint tests.
- **Gap**: Zero direct test coverage for agent-facing endpoints.
- **Recommendation**: Add HTTP handler tests for `/product-meta/{ids}` and `/bot`.
- **Evidence**: `validator/validator_test.go`, `money/money_test.go`, `.github/workflows/ci-pr.yaml`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: RISK
- **Finding**: GKE Autopilot provides default encryption. No customer-managed KMS keys. Memorystore Redis has no explicit encryption settings. No `kms_key_id` on any resource.
- **Gap**: No explicit customer-managed encryption. Redis encryption undocumented.
- **Recommendation**: Configure customer-managed KMS keys. Document encryption posture.
- **Evidence**: `terraform/main.tf`, `terraform/memorystore.tf`

#### ENG-Q6: Cross-Origin and Network Policies
- **Severity**: BLOCKER
- **Finding**: NetworkPolicies disabled by default (`networkPolicies.create: false`). AuthorizationPolicies disabled (`authorizationPolicies.create: false`). `frontend-external` LoadBalancer exposes port 80 to internet. Istio gateway accepts all hosts (`*`). No CORS in application code or infrastructure. No WAF.
- **Gap**: No network policy enforcement, no CORS, no WAF. Frontend exposed to internet with no restrictions.
- **Recommendation**: Enable network policies. Add CORS middleware. Document network topology.
- **Evidence**: `helm-chart/values.yaml`, `helm-chart/templates/frontend.yaml`, `kubernetes-manifests/frontend.yaml`, `istio-manifests/frontend-gateway.yaml`

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `main.go` | API-Q1, API-Q2, API-Q5, API-Q6, API-Q7, API-Q8, API-Q9, API-Q10, AUTH-Q1, AUTH-Q3, AUTH-Q4, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q4, STATE-Q5, OBS-Q1, DATA-Q5, DISC-Q2 |
| `handlers.go` | API-Q1, API-Q3, API-Q4, API-Q6, API-Q7, API-Q8, API-Q10, AUTH-Q1, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q7, STATE-Q1, STATE-Q2, STATE-Q3, STATE-Q4, STATE-Q6, HITL-Q1, HITL-Q2, DATA-Q1, DATA-Q2, DATA-Q3, DATA-Q5, DATA-Q6, DATA-Q7, DISC-Q4, OBS-Q3 |
| `rpc.go` | API-Q7, API-Q10, STATE-Q1, STATE-Q2, STATE-Q3, STATE-Q4, DATA-Q3, DATA-Q4, DATA-Q6, DISC-Q4 |
| `middleware.go` | AUTH-Q1, AUTH-Q4, AUTH-Q5, AUTH-Q6, AUTH-Q7, AUTH-Q8, DATA-Q7, OBS-Q1, HITL-Q3 |
| `deployment_details.go` | AUTH-Q7, OBS-Q1 |
| `validator/validator.go` | DATA-Q1, STATE-Q6, DISC-Q2, DATA-Q8 |
| `validator/validator_test.go` | ENG-Q2, ENG-Q4 |
| `money/money.go` | — (utility, not directly cited) |
| `money/money_test.go` | ENG-Q2, ENG-Q4 |
| `genproto/demo.pb.go` | DATA-Q1, DATA-Q5, DISC-Q1, DISC-Q2 |
| `genproto.sh` | API-Q2, DISC-Q1 |

### Infrastructure as Code
| File | Questions Referenced |
|------|---------------------|
| `terraform/main.tf` | STATE-Q7, ENG-Q1, ENG-Q5 |
| `terraform/memorystore.tf` | ENG-Q5 |
| `terraform/variables.tf` | DATA-Q2 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `Dockerfile` | ENG-Q6, HITL-Q3 |

### Kubernetes Manifests
| File | Questions Referenced |
|------|---------------------|
| `kubernetes-manifests/frontend.yaml` | AUTH-Q2, AUTH-Q6, ENG-Q1, ENG-Q6, STATE-Q7 |

### Helm Chart
| File | Questions Referenced |
|------|---------------------|
| `helm-chart/values.yaml` | AUTH-Q2, STATE-Q5, OBS-Q1, ENG-Q6 |
| `helm-chart/templates/frontend.yaml` | AUTH-Q2, ENG-Q6 |

### Istio Manifests
| File | Questions Referenced |
|------|---------------------|
| `istio-manifests/frontend-gateway.yaml` | ENG-Q6 |
| `istio-manifests/frontend.yaml` | ENG-Q3 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/ci-pr.yaml` | ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4, STATE-Q7, OBS-Q2, HITL-Q3 |
| `.github/workflows/ci-main.yaml` | ENG-Q2 |
| `cloudbuild.yaml` | ENG-Q2 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `templates/error.html` | API-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `go.mod` | STATE-Q5 |
