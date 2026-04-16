# Agentic Readiness Assessment Report

**Target**: services/microservices-demo/src/checkoutservice
**Date**: 2026-04-16
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Service Archetype**: orchestrator (user-provided)
**Agent Scope**: read-only
**Priority**: P0
**Tags**: go, grpc, orchestrator, critical-path
**Context**: Go gRPC service orchestrating the checkout workflow — calls cart, product, shipping, currency, payment, and email services.

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 2 | **RISKs**: 25 | **INFOs**: 11

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days. The two blockers — AUTH-Q1 (no machine identity authentication) and DATA-Q1 (unclassified PCI and PII data) — must be resolved before any agent can safely call this service. AUTH-Q1 is the prerequisite for all authorization, audit, and suspension controls. DATA-Q1 is critical because the service handles credit card numbers, CVVs, email addresses, and physical addresses with no classification or protection.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 2 |
| RISK | 25 |
| INFO | 11 |
| N/A | 0 |
| Not Evaluated (extended) | 5 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 14
**Extended Questions Not Triggered**: 5
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: orchestrator (user-provided)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: The gRPC server in `main.go` is created with `grpc.NewServer(grpc.StatsHandler(otelgrpc.NewServerHandler()))` — no authentication interceptors, no TLS, no mTLS, no API key validation, and no OAuth2 configuration. All outbound gRPC client connections use `insecure.NewCredentials()` in the `mustConnGRPC` function. The server accepts any connection on port 5050 without verifying caller identity. Istio AuthorizationPolicies are disabled (`authorizationPolicies.create: false` in `helm-chart/values.yaml`), so there is no mesh-level caller identity enforcement. The Helm template defines an AuthorizationPolicy resource restricting access to `hipstershop.CheckoutService/PlaceOrder` from the frontend ServiceAccount, but this is gated behind the disabled flag.
- **Gap**: No machine identity authentication exists at any layer — application or mesh. Any network-reachable client can call the PlaceOrder RPC without presenting credentials. There is no way to attribute a request to a specific machine principal. Audit attribution is impossible.
- **Remediation**:
  - **Immediate**: Enable Istio AuthorizationPolicies (`authorizationPolicies.create: true` in `helm-chart/values.yaml`) to enforce mTLS-based caller identity at the mesh layer. The existing AuthorizationPolicy template already restricts PlaceOrder access to the frontend ServiceAccount — enabling it provides immediate machine identity via Istio principals without application code changes.
  - **Target State**: Mesh-level mTLS authentication with per-caller AuthorizationPolicy rules. Agent-specific K8s ServiceAccounts with dedicated Istio principals (e.g., `cluster.local/ns/default/sa/agent-checkout-reader-v1`). Application-layer gRPC `UnaryServerInterceptor` for defense-in-depth identity verification. The authenticated principal is available in the request context and logged with every operation.
  - **Estimated Effort**: Low (Helm value change for immediate), Medium (application-layer interceptor for defense-in-depth, 2–4 weeks)
  - **Dependencies**: AUTH-Q2 (scoped permissions require identity first), AUTH-Q6 (audit logging requires principal attribution), AUTH-Q7 (suspension requires identity)
- **Evidence**: `main.go` (`mustConnGRPC` function using `insecure.NewCredentials()`; `grpc.NewServer()` with no auth interceptors), `helm-chart/values.yaml` (`authorizationPolicies.create: false`), `helm-chart/templates/checkoutservice.yaml` (AuthorizationPolicy template gated by disabled flag)

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: The `PlaceOrderRequest` message (defined in `genproto/demo.pb.go`) contains unclassified PII and PCI-scope payment data: `email` (string), `credit_card` (`CreditCardInfo` with `credit_card_number`, `credit_card_cvv`, `credit_card_expiration_year`, `credit_card_expiration_month`), and `address` (`Address` with `street_address`, `city`, `state`, `country`, `zip_code`). The `user_id` field is also present. None of these fields are tagged with sensitivity classifications. No field-level encryption, no access controls on sensitive fields, and no data masking. The `chargeCard` function in `main.go` passes raw `CreditCardInfo` to the payment service over insecure gRPC. PII (`email`, `user_id`) is logged directly to stdout via logrus: `log.Infof("[PlaceOrder] user_id=%q user_currency=%q", req.UserId, req.UserCurrency)` and `log.Infof("order confirmation email sent to %q", req.Email)`.
- **Gap**: Sensitive data (PII, PCI-scope credit card data) flows through the service unclassified and unprotected. No field-level tagging, no encryption in transit between services (insecure gRPC), and PII is written to logs in cleartext. An agent with read access to this service would have unrestricted access to all sensitive data.
- **Remediation**:
  - **Immediate**: Classify all fields in the protobuf schema with sensitivity tags (e.g., `[(sensitivity) = "PCI"]` for credit card fields, `[(sensitivity) = "PII"]` for email and address). Implement log scrubbing to redact PII from log output before any agent integration.
  - **Target State**: All sensitive fields are classified at the schema level. Field-level access controls prevent agents from retrieving credit card or PII data without explicit authorization. PII is redacted from all logs and observability data. Credit card data never transits over unencrypted connections.
  - **Estimated Effort**: High (4–8 weeks — involves schema changes, log scrubbing, TLS enablement, and access control implementation)
  - **Dependencies**: AUTH-Q1 (machine identity must exist before field-level access controls can be enforced). Enabling TLS (AUTH-Q1 remediation) also addresses the insecure transit concern.
- **Evidence**: `genproto/demo.pb.go` (PlaceOrderRequest, CreditCardInfo, Address structs — no sensitivity tags), `main.go` (PlaceOrder function logging PII; chargeCard function passing raw credit card data over insecure gRPC)

---

## RISKs — Proceed with Compensating Controls

### API-Q2: Machine-Readable API Specification

- **Severity**: RISK
- **Finding**: Generated protobuf files exist in `genproto/demo.pb.go` and `genproto/demo_grpc.pb.go`, providing a machine-readable schema for the CheckoutService. The `genproto.sh` script references the source `.proto` file at `../../protos/demo.proto`, which is external to this repository. The generated files define the `PlaceOrderRequest`, `PlaceOrderResponse`, and all dependent message types with full type information.
- **Gap**: The source `.proto` file is not co-located in this repository — it lives at `../../protos/demo.proto`. No way to verify whether the generated Go files are current with the source proto. No schema versioning or changelog.
- **Compensating Controls**:
  - Use the generated `genproto/demo_grpc.pb.go` as the de facto machine-readable spec for agent tool definition — it contains full method signatures and message types.
  - Add a CI step to regenerate proto files and fail if they differ from checked-in versions (drift detection).
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Copy or symlink the source `demo.proto` into this repository. Add proto file versioning and a `CHANGELOG.md` for the proto.
- **Evidence**: `genproto.sh`, `genproto/demo_grpc.pb.go`, `genproto/demo.pb.go`

### API-Q3: Structured Error Responses

- **Severity**: RISK
- **Finding**: The PlaceOrder RPC in `main.go` returns gRPC status errors using `status.Errorf(codes.Internal, ...)` and `status.Errorf(codes.Unavailable, ...)`. Error messages include raw internal error strings (e.g., `"failed to charge card: %+v"`, `"shipping error: %+v"`). No structured error response bodies — no error codes, no retryable boolean, no error categories. The gRPC status code is the only machine-readable signal.
- **Gap**: Agents cannot distinguish retriable errors from terminal errors beyond the gRPC status code. Internal error details leak implementation specifics (e.g., `%+v` stack traces from `pkg/errors`). No consistent error schema.
- **Compensating Controls**:
  - Map gRPC status codes to retry behavior in the agent tool definition (e.g., `Unavailable` → retry, `Internal` → do not retry).
  - Add gRPC error details using `google.golang.org/grpc/status` with `errdetails.ErrorInfo` to provide structured error metadata.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement structured gRPC error details using `status.WithDetails()` with `errdetails.ErrorInfo` containing error_code, retryable flag, and error domain. Stop leaking internal error strings in status messages.
- **Evidence**: `main.go` (PlaceOrder function, chargeCard, shipOrder error returns)

### AUTH-Q2: Scoped Permissions (Least Privilege)

- **Severity**: RISK
- **Finding**: No authorization model exists in the checkoutservice. The gRPC server has no interceptors that check permissions. Any authenticated caller (once AUTH-Q1 is resolved) would have full access to the PlaceOrder RPC. No IAM policies, no RBAC definitions, no permission matrices, and no role definitions in the codebase. The Helm template's AuthorizationPolicy (currently disabled) restricts by source principal and operation path, which provides coarse-grained scoping at the mesh layer.
- **Gap**: No mechanism to grant an agent read-only access vs. write access. Once connected, all callers have identical privileges. Blast-radius risk — a compromised agent identity has full access to the checkout workflow.
- **Compensating Controls**:
  - Enable the Istio AuthorizationPolicy (AUTH-Q1 remediation) to restrict PlaceOrder access to the frontend ServiceAccount only.
  - For read-only agent scope, block the PlaceOrder RPC at the mesh layer and only allow health check calls.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a gRPC unary interceptor that checks caller roles/permissions before executing the RPC. Define at minimum two roles: `checkout:read` and `checkout:write`. Leverage Istio AuthorizationPolicy for mesh-level enforcement.
- **Evidence**: `main.go` (grpc.NewServer with no authorization interceptors), `helm-chart/templates/checkoutservice.yaml` (AuthorizationPolicy template — disabled)

### AUTH-Q3: Action-Level Authorization

- **Severity**: RISK
- **Finding**: The service exposes only a single RPC (`PlaceOrder`) which is inherently a write operation. No read-only RPCs exist (no GetOrder, no GetOrderStatus). No action-level permission checks — there is no distinction between read and write operations at the application level.
- **Gap**: Cannot enforce "allow an agent to read order status but not place orders" because no read RPCs exist. The entire service surface is a single write operation.
- **Compensating Controls**:
  - Block PlaceOrder at the mesh layer for read-only agents.
  - Add read-only RPCs (e.g., GetOrderStatus) that agents can call without write permissions.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add read-only RPCs to the CheckoutService proto definition (e.g., `GetOrderStatus`, `ValidateCart`). Implement per-RPC authorization checks.
- **Evidence**: `genproto/demo_grpc.pb.go` (CheckoutService_ServiceDesc — single method PlaceOrder), `main.go`

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: RISK
- **Finding**: No identity propagation exists. The PlaceOrder RPC accepts `user_id` as a string field in the request message (`req.UserId`), but this is caller-provided — no JWT parsing, no token exchange, no `Authorization` header processing, and no middleware that validates the claimed user identity. Any caller can provide any `user_id` value. The `user_id` is passed downstream to CartService.GetCart without validation. No distinction exists between service-to-service calls and user-delegated calls — the service has no concept of caller identity (AUTH-Q1), so there is no way to distinguish an agent acting under its own identity from an agent acting on behalf of a user.
- **Gap**: No technical mechanism to carry authenticated user context end-to-end. The `user_id` is a self-asserted claim, not a verified identity. An agent could access any user's cart by providing an arbitrary `user_id`. Cannot implement different authorization policies for agent-as-self vs agent-on-behalf-of-user.
- **Compensating Controls**:
  - Restrict which user_ids an agent identity is authorized to access (e.g., agent can only call with user_ids from its assigned scope).
  - Add a gRPC metadata interceptor that validates a JWT token and extracts the user_id from the token claims rather than the request body.
  - Once AUTH-Q1 is resolved, define separate service accounts for each mode (e.g., `agent-checkout-service` vs `agent-checkout-delegated`).
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement JWT-based identity propagation. Extract `user_id` from the authenticated token claims rather than the request body. Add gRPC metadata fields to distinguish agent-as-self from agent-on-behalf-of-user. Implement different authorization paths for each.
- **Evidence**: `main.go` (PlaceOrder uses `req.UserId` directly; no identity handling), `genproto/demo.pb.go` (PlaceOrderRequest.UserId is a plain string field)

### AUTH-Q5: Credential Management

- **Severity**: RISK
- **Finding**: Service configuration is loaded from environment variables: `SHIPPING_SERVICE_ADDR`, `PRODUCT_CATALOG_SERVICE_ADDR`, `CART_SERVICE_ADDR`, `CURRENCY_SERVICE_ADDR`, `EMAIL_SERVICE_ADDR`, `PAYMENT_SERVICE_ADDR`, `COLLECTOR_SERVICE_ADDR`. These are service addresses, not credentials. No secrets management system in use — no AWS Secrets Manager, no Vault client, no credential rotation. Credit card data (`CreditCardInfo`) flows through the service in plaintext over insecure gRPC connections. No `.env` files are committed (positive).
- **Gap**: No secrets management infrastructure. When authentication is added (AUTH-Q1), credentials (TLS certs, API keys, JWT signing keys) will need secure storage and rotation. Credit card data currently transits unencrypted.
- **Compensating Controls**:
  - Use Kubernetes Secrets or AWS Secrets Manager for any credentials added as part of AUTH-Q1 remediation.
  - Enable TLS on all gRPC connections to encrypt credit card data in transit.
- **Remediation Timeline**: 30–60 days (concurrent with AUTH-Q1)
- **Recommendation**: Integrate AWS Secrets Manager or HashiCorp Vault for credential storage. Implement automatic rotation. Enable TLS on all inter-service gRPC connections.
- **Evidence**: `main.go` (mustMapEnv function reading service addresses from env vars; mustConnGRPC using insecure.NewCredentials())

### AUTH-Q6: Immutable Audit Logging ⚡

- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: No audit logging is configured. The application logs operational messages via logrus JSON logger (e.g., `[PlaceOrder] user_id=... user_currency=...`, `payment went through (transaction_id: ...)`, `order confirmation email sent to ...`), but these are informational application logs written to stdout — not immutable audit logs. No CloudTrail configuration, no immutable log storage (S3 with object lock), no log file validation, and no IaC defining audit infrastructure. Log output goes to stdout and relies entirely on the container orchestrator for log collection. Tracing is disabled (`tracing: false` in `helm-chart/values.yaml`), so `ENABLE_TRACING` is not set in the deployment.
- **Gap**: No immutable audit trail. Application logs are ephemeral (stdout). No tamper-evident log storage. Cannot prove after the fact which caller performed which operation. For read-only agent scope, this is a RISK rather than BLOCKER, but must be resolved before expanding to write-enabled scope.
- **Compensating Controls**:
  - Configure the container orchestrator (Kubernetes) to ship stdout logs to an immutable log store (e.g., CloudWatch Logs with retention policy, S3 with object lock).
  - Add caller identity to log entries once AUTH-Q1 is resolved.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement structured audit logging with caller identity, operation type, and timestamp. Ship logs to an immutable store. Enable CloudTrail for API-level audit if deploying behind API Gateway.
- **Evidence**: `main.go` (logrus JSON logger to stdout; no audit logging infrastructure), `helm-chart/values.yaml` (`tracing: false`)

### AUTH-Q7: Agent Identity Suspension

- **Severity**: RISK
- **Finding**: No agent identity management exists. Since there is no authentication mechanism (AUTH-Q1), there are no agent identities to suspend. No API key revocation endpoints, no IAM role deactivation, no service account disable mechanisms. The only way to block a caller is to shut down the entire service or change network rules.
- **Gap**: Cannot isolate a misbehaving agent without disrupting all callers. No surgical suspension capability.
- **Compensating Controls**:
  - Use network-level controls (Kubernetes NetworkPolicies) to block specific source pods.
  - Once AUTH-Q1 is resolved with Istio AuthorizationPolicies, update the policy to remove the agent's ServiceAccount principal.
- **Remediation Timeline**: 30–60 days (concurrent with AUTH-Q1)
- **Recommendation**: As part of AUTH-Q1 remediation, include per-identity suspension capability. With Istio AuthorizationPolicies, removing a principal from the allowed list immediately blocks that identity.
- **Evidence**: `main.go` (no identity management; no auth interceptors), `helm-chart/templates/checkoutservice.yaml` (AuthorizationPolicy template supports principal-based access — once enabled)

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: The PlaceOrder workflow in `main.go` executes a multi-step sequence: (1) `prepareOrderItemsAndShippingQuoteFromCart` — reads cart and products, (2) `chargeCard` — charges the credit card via PaymentService, (3) `shipOrder` — initiates shipping via ShippingService, (4) `emptyUserCart` — empties the cart via CartService, (5) `sendOrderConfirmation` — sends email via EmailService. If `shipOrder` fails after `chargeCard` succeeds, the payment charge is NOT reversed — there is no compensation transaction. If `emptyUserCart` fails, the error is silently discarded (`_ = cs.emptyUserCart(ctx, req.UserId)`). If `sendOrderConfirmation` fails, it is logged as a warning but the order is still returned as successful.
- **Gap**: No saga pattern, no compensation transactions, no undo endpoints. A failed multi-step checkout leaves the system in an inconsistent state: payment charged but no shipment, or cart not emptied despite order completion.
- **Compensating Controls**:
  - For read-only agent scope, this risk is limited to observability — an agent reading order status would see inconsistent state but cannot cause it.
  - Implement manual compensation procedures for operations teams to reverse charges when shipping fails.
- **Remediation Timeline**: 90–180 days
- **Recommendation**: Implement a saga pattern with explicit compensation steps: if `shipOrder` fails, call a `refundCharge` operation. If `emptyUserCart` fails, log an error (not silently discard) and retry or alert.
- **Evidence**: `main.go` (PlaceOrder function — sequential workflow with no rollback; `_ = cs.emptyUserCart` silently discarding error)

### STATE-Q5: Rate Limiting and Throttling

- **Severity**: RISK
- **Finding**: No rate limiting exists at any layer. The gRPC server in `main.go` has no rate-limiting interceptor. No API Gateway sits in front of the service. No WAF rules. The server accepts connections on port 5050 without throttling. The `go.mod` file shows no rate-limiting library dependencies. The Helm chart defines a ClusterIP Service with no throttling configuration.
- **Gap**: A runaway agent loop could call PlaceOrder at machine speed, potentially charging credit cards and creating shipments at an unbounded rate. No mechanism to throttle any caller.
- **Compensating Controls**:
  - Implement rate limiting at the service mesh layer (e.g., Istio rate limit filter, Envoy rate limit service).
  - Add a gRPC server interceptor with a token bucket rate limiter per caller identity.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a gRPC unary interceptor implementing per-caller rate limiting (e.g., using `golang.org/x/time/rate`). Configure rate limits per agent identity once AUTH-Q1 is resolved.
- **Evidence**: `main.go` (no rate limiting interceptors), `go.mod` (no rate limiting libraries), `helm-chart/templates/checkoutservice.yaml` (ClusterIP Service, no throttling)

### HITL-Q3: Sandbox/Staging Environment

- **Severity**: RISK
- **Finding**: No sandbox, staging, or test environment configuration exists in this repository. No environment-specific configuration files (no `values-staging.yaml`). No docker-compose for local testing. No seed data scripts or synthetic data generators. The Helm chart deploys a single environment configuration with no staging variant.
- **Gap**: No staging environment for agent testing. The first time an agent bug is discovered would be in production, which is unacceptable for a P0 critical-path service that processes payments.
- **Compensating Controls**:
  - Use the containerized service (Dockerfile) with mocked downstream services for local testing.
  - Deploy to a non-production Kubernetes namespace with test data.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a docker-compose configuration with mocked downstream services for local agent testing. Define a staging Helm values override with synthetic data in the deployment infrastructure.
- **Evidence**: `Dockerfile`, `helm-chart/templates/checkoutservice.yaml` (single environment config)

### DATA-Q2: Data Residency and Sovereignty ⚡

- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: No data residency or sovereignty controls are configured. The service processes PII (email, address) and PCI data (credit card) but there is no region configuration, no data residency policy documentation, and no IaC defining regional deployment constraints. Service addresses for downstream services come from environment variables with no region indicators. The `go.mod` includes `cloud.google.com/go/profiler`, suggesting the service may target GCP — but no region is configured.
- **Gap**: If an agent sends data from this service to an LLM endpoint in a different jurisdiction, it could violate GDPR (address data of EU residents), PCI DSS (credit card data), or other regulations. No technical controls prevent cross-region data transmission.
- **Compensating Controls**:
  - Deploy the agent's LLM endpoint in the same region as the checkout service.
  - For read-only agents, ensure any data retrieved is not forwarded to LLM endpoints without region validation.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Document data residency requirements. Configure region-locked deployment in IaC. Implement data classification (DATA-Q1) that includes residency constraints per field.
- **Evidence**: `main.go` (no region configuration), `go.mod` (GCP profiler dependency), `genproto/demo.pb.go` (Address struct with country field — implies international data)

### DISC-Q1: Schema Versioning and API Contracts

- **Severity**: RISK
- **Finding**: The generated protobuf files in `genproto/` provide typed schema definitions for all messages. The proto source file (`demo.proto`) is referenced at `../../protos/demo.proto` per `genproto.sh` but is not present in this repository. No schema versioning exists — the proto package is `hipstershop` with no version suffix. No schema changelog, no migration files. The gRPC service is registered as `hipstershop.CheckoutService` with no version identifier. No deprecation notices, no breaking change detection in CI.
- **Gap**: Schema is auto-generated but not versioned or documented beyond the proto field names. The source proto is external — schema evolution is not tracked within this repository. Any breaking change to the PlaceOrder RPC would break agent tool definitions silently.
- **Compensating Controls**:
  - Use the generated proto files as the de facto schema documentation.
  - Track schema changes through Git history of the `genproto/` directory.
  - Use protobuf's built-in backward compatibility (additive-only changes) as a de facto versioning discipline.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add the source `demo.proto` to this repository. Add version to the proto package (e.g., `hipstershop.checkout.v1`). Add a `SCHEMA_CHANGELOG.md` tracking proto message changes. Integrate `buf breaking` in CI for breaking change detection.
- **Evidence**: `genproto.sh` (references `../../protos/demo.proto`), `genproto/demo.pb.go` (generated, no versioning), `genproto/demo_grpc.pb.go` (ServiceName: `hipstershop.CheckoutService` — no version)

### OBS-Q1: Distributed Tracing and Structured Logging

- **Severity**: RISK
- **Finding**: **Tracing**: OpenTelemetry is integrated — the service imports `go.opentelemetry.io/contrib/instrumentation/google.golang.org/grpc/otelgrpc` and configures both server-side (`grpc.StatsHandler(otelgrpc.NewServerHandler())`) and client-side (`grpc.WithStatsHandler(otelgrpc.NewClientHandler())`) instrumentation. Trace context propagation is configured via `otel.SetTextMapPropagator`. However, tracing initialization is conditional — it only runs when `ENABLE_TRACING == "1"`, and the Helm values have `tracing: false`, so `ENABLE_TRACING` is not set in the deployment. **Logging**: JSON structured logging is configured via logrus with `JSONFormatter`, RFC3339Nano timestamps, and severity levels. However, log entries do not include `request_id`, `correlation_id`, `trace_id`, or `span_id` fields. Trace context and log entries are not correlated.
- **Gap**: Tracing is disabled in the current deployment configuration. Log entries lack correlation IDs — you cannot link a log entry to a specific trace or request. The two observability signals (traces and logs) are disconnected.
- **Compensating Controls**:
  - Set `tracing: true` in `helm-chart/values.yaml` to enable tracing in the deployment.
  - Add a logrus hook that extracts the OpenTelemetry trace_id and span_id from the context and injects them into log entries.
- **Remediation Timeline**: 30 days
- **Recommendation**: Enable tracing in the Helm values (`tracing: true`). Make tracing non-conditional in code (always enabled, with sampling control via the collector). Add trace_id and span_id to all log entries.
- **Evidence**: `main.go` (initTracing function gated by ENABLE_TRACING; otelgrpc instrumentation on server and clients; logrus JSONFormatter with no correlation IDs), `helm-chart/values.yaml` (`tracing: false`), `go.mod` (OpenTelemetry dependencies)

### OBS-Q2: Alerting on Error Rates and Latency

- **Severity**: RISK
- **Finding**: No alerting configuration exists in this repository. No CloudWatch alarms, no Prometheus alerting rules, no PagerDuty/OpsGenie integration, no SLO definitions. The `initStats()` function in `main.go` contains only a TODO comment: `//TODO(arbrown) Implement OpenTelemetry stats`. No custom metrics are published.
- **Gap**: No alerting on error rates or latency for the PlaceOrder RPC. If the service degrades, there is no automated notification. Agents calling a degraded service will experience failures with no operational awareness.
- **Compensating Controls**:
  - If deploying behind a service mesh, configure alerting at the mesh observability layer.
  - Monitor OpenTelemetry trace data for error rate spikes using the configured collector (once tracing is enabled).
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement the TODO in `initStats()`. Publish custom metrics for PlaceOrder success/failure rates and latency. Configure alerting thresholds (e.g., error rate > 5%, P95 latency > 5s).
- **Evidence**: `main.go` (initStats function with TODO; no metrics or alerting configuration)

### ENG-Q1: Infrastructure Governance for Agent-Facing Surface

- **Severity**: RISK
- **Finding**: The Helm chart in `helm-chart/templates/checkoutservice.yaml` defines the Kubernetes Deployment, Service, NetworkPolicy, Istio Sidecar, and AuthorizationPolicy as code. This provides IaC governance for the deployment surface. However, the AuthorizationPolicy and tracing are disabled in the current values. No drift detection (no AWS Config rules, no ArgoCD sync status monitoring). Peer review enforcement is not visible in this repository (no CODEOWNERS file, no branch protection rules).
- **Gap**: IaC exists (Helm chart) but key security controls are disabled. No drift detection. Peer review enforcement not visible. 1 of 3 governance sub-checks fully present (IaC defined), 2 partially present (peer review implied by Git, drift detection absent).
- **Compensating Controls**:
  - All infrastructure is Helm-defined, reducing manual configuration drift risk.
  - GitOps deployment (if used) ensures consistent deployment from source control.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Enable AuthorizationPolicies in Helm values. Add a CODEOWNERS file requiring review for Helm chart changes. Implement drift detection via ArgoCD sync monitoring or equivalent.
- **Evidence**: `helm-chart/templates/checkoutservice.yaml` (Deployment, Service, NetworkPolicy, Sidecar, AuthorizationPolicy), `helm-chart/values.yaml` (`authorizationPolicies.create: false`)

### ENG-Q2: CI/CD with API Contract Testing

- **Severity**: RISK
- **Finding**: No CI/CD pipeline definitions exist in this repository. No `.github/workflows/`, no `.gitlab-ci.yml`, no `Jenkinsfile`, no `buildspec.yml`. No API contract tests, no consumer-driven contract testing (Pact), no proto compatibility checks. The `genproto.sh` script generates proto code but is not integrated into any automated pipeline.
- **Gap**: No automated testing of agent-facing APIs. Proto changes could break agent tool definitions with no detection. No build or test automation.
- **Compensating Controls**:
  - Run `genproto.sh` manually and diff the output to detect proto changes.
  - Add `buf breaking` or `protolock` to detect backward-incompatible proto changes.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a CI pipeline that: (1) runs `go test ./...`, (2) regenerates proto files and checks for drift, (3) runs `buf breaking` against the previous version to detect API-breaking changes.
- **Evidence**: No CI/CD configuration files found in repository. `genproto.sh` (manual proto generation)

### ENG-Q3: Rollback Capability

- **Severity**: RISK
- **Finding**: No rollback capability is configured in this repository. No blue/green deployment configuration, no canary deployment, no rollback triggers, no feature flags. The Dockerfile builds a single static binary with no version-specific deployment metadata. The Helm chart does not define rollback annotations or deployment strategies beyond the default.
- **Gap**: If a deployment breaks agent-facing APIs, there is no documented or automated way to roll back. Recovery depends entirely on Kubernetes `kubectl rollout undo` or Helm rollback capabilities not configured here.
- **Compensating Controls**:
  - Kubernetes supports rollback via `kubectl rollout undo` by default.
  - Tag container images with version-specific tags (not just `latest`) to enable rollback.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add deployment strategy configuration to the Helm chart (e.g., `RollingUpdate` with `maxUnavailable: 0`). Tag images with Git SHA for traceable rollback. Consider canary deployment with automatic rollback on error rate increase.
- **Evidence**: `Dockerfile` (no version metadata beyond build args), `helm-chart/templates/checkoutservice.yaml` (no deployment strategy or rollback config)

---

### STATE-Q2: Queryable Current State

- **Severity**: RISK
- **Finding**: The CheckoutService exposes only one RPC: `PlaceOrder`. There is no `GetOrder`, `GetOrderStatus`, or `ListOrders` RPC. The `PlaceOrderResponse` contains an `OrderResult` with `order_id`, `shipping_tracking_id`, items, and costs, but this is returned only once at checkout time — there is no way to query the order state later. The service is stateless — it does not persist orders to a database.
- **Gap**: An agent cannot query current order state. PlaceOrder is fire-and-forget — once the response is returned, the order state is distributed across downstream services (cart, payment, shipping) with no single point of query.
- **Compensating Controls**:
  - Agents must cache the PlaceOrderResponse if they need to reference the order later.
  - Query downstream services (ShippingService, PaymentService) directly for state information.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add read RPCs to CheckoutService: `GetOrderStatus(order_id)` and `ListOrders(user_id)`. This requires adding a persistence layer (e.g., DynamoDB) to store order state.
- **Evidence**: `genproto/demo_grpc.pb.go` (CheckoutService_ServiceDesc — single method PlaceOrder), `main.go` (no database, no order persistence)

### STATE-Q4: Circuit Breakers and Resilience

- **Severity**: RISK
- **Finding**: The `mustConnGRPC` function in `main.go` creates gRPC client connections with a 3-second context timeout for connection establishment, but no circuit breaker, no retry logic, and no timeout configuration on individual RPC calls. The downstream service calls (`chargeCard`, `shipOrder`, `getUserCart`, etc.) use the request context directly with no per-call timeout override. If a downstream service hangs, the entire PlaceOrder call hangs. No resilience libraries are imported. The service calls 6 downstream services — a single slow dependency can cascade.
- **Gap**: No circuit breakers to prevent cascading failures. No retry logic with exponential backoff. No per-call timeouts on downstream RPCs.
- **Compensating Controls**:
  - Implement timeout at the agent/client level to prevent indefinite blocking.
  - Use the Istio service mesh (if enabled) to add circuit breaking and retry at the infrastructure layer.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add per-RPC context timeouts (e.g., 5s for payment, 10s for shipping). Implement a circuit breaker library (e.g., `sony/gobreaker`). Add retry with exponential backoff for idempotent downstream calls.
- **Evidence**: `main.go` (mustConnGRPC with 3-second connection timeout only; no per-call timeouts), `go.mod` (no resilience libraries)

### STATE-Q7: Infrastructure Capacity for Agent Traffic

- **Severity**: RISK
- **Finding**: No auto-scaling configuration exists. The Helm chart Deployment has no HPA definition and no replica count configuration. The service connects to 6 downstream services — agent traffic amplification means 1 agent call generates 6+ downstream calls. No load test results or capacity planning documentation exists.
- **Gap**: No evidence the infrastructure is sized for agent-speed traffic patterns. The 1:6+ call amplification means agent-induced load is multiplied across the entire backend.
- **Compensating Controls**:
  - Conduct load testing before agent deployment to establish baseline capacity.
  - Deploy with Kubernetes HPA and resource limits.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add Kubernetes HPA configuration with CPU/memory-based autoscaling. Conduct load tests simulating agent traffic patterns.
- **Evidence**: `Dockerfile` (single binary, EXPOSE 5050), `helm-chart/templates/checkoutservice.yaml` (Deployment with no HPA)

### DATA-Q5: Temporal Metadata and Freshness

- **Severity**: RISK
- **Finding**: The `OrderResult` message has no `created_at`, `updated_at`, or `event_time` timestamp fields. No data freshness signaling exists — no `Cache-Control` headers, no `X-Data-Age` headers, no consistency level indicators in gRPC metadata.
- **Gap**: No timestamps in API responses. No freshness metadata — agent cannot know if prices/rates are current or stale.
- **Compensating Controls**:
  - Add a `created_at` field to the `OrderResult` proto message.
  - Accept that for synchronous calls, data is as fresh as the downstream service provides — document this assumption.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `google.protobuf.Timestamp created_at` to the `OrderResult` message. Add gRPC trailing metadata with data freshness indicators.
- **Evidence**: `genproto/demo.pb.go` (OrderResult — no timestamps), `main.go` (no freshness metadata)

### DATA-Q6: PII Redaction in Logs

- **Severity**: RISK
- **Finding**: PII is logged directly to stdout in `main.go`: `user_id` and `email` appear in cleartext via logrus. No log scrubbing, no PII masking, no redaction filters.
- **Gap**: PII in cleartext logs — compliance risk under GDPR and other privacy regulations.
- **Compensating Controls**:
  - Configure the log shipping pipeline to redact PII patterns before storage.
  - Implement a logrus hook that masks PII fields before log emission.
- **Remediation Timeline**: 30 days
- **Recommendation**: Add a logrus `Hook` that detects and masks PII patterns. Replace direct PII logging with hashed or truncated values.
- **Evidence**: `main.go` (log.Infof with user_id, log.Warnf/Infof with email)

### ENG-Q4: API Test Coverage

- **Severity**: RISK
- **Finding**: The only test file is `money/money_test.go` — unit tests for monetary arithmetic. Zero tests for the PlaceOrder RPC, no integration tests, no API contract tests.
- **Gap**: Agent-facing API surface entirely untested.
- **Compensating Controls**:
  - Write integration tests using gRPC test helpers with mocked downstream services.
  - Add the PlaceOrder RPC to a Postman/Newman collection for manual testing.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Write integration tests for PlaceOrder using `google.golang.org/grpc/test/bufconn` with mocked downstream service clients.
- **Evidence**: `money/money_test.go` (arithmetic tests only)

### ENG-Q5: Encryption at Rest for Agent-Accessible Data

- **Severity**: RISK
- **Finding**: Service is stateless — no persistent data. However, it processes PCI-scope credit card data and PII that is logged to stdout. No KMS configuration, no encrypted storage definitions.
- **Gap**: No encryption controls for log storage. PCI data transits unencrypted.
- **Compensating Controls**:
  - Ensure the log shipping destination has encryption at rest enabled with KMS.
  - Resolve DATA-Q6 (PII redaction) to reduce the sensitivity of persisted log data.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Ensure all log storage destinations use KMS encryption. Consider encrypting PCI data at the application layer.
- **Evidence**: `Dockerfile` (stateless container), `helm-chart/templates/checkoutservice.yaml` (no encryption config)

---

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO
- **Finding**: The application exposes a documented gRPC interface: `hipstershop.CheckoutService` with a single RPC `PlaceOrder`. The interface is defined via protobuf — generated Go code in `genproto/demo_grpc.pb.go` and `genproto/demo.pb.go`. The source proto file is at `../../protos/demo.proto` (per `genproto.sh`). The service does not require direct database access, file-based exchange, or UI automation — it is a proper API-based service.
- **Implication**: The gRPC/protobuf interface is a well-structured, machine-consumable API surface. Agent tools can be generated from the proto definitions. This is a positive architectural foundation for agent integration.
- **Recommendation**: Ensure the proto definitions remain the single source of truth for the API contract.
- **Evidence**: `genproto/demo_grpc.pb.go` (CheckoutService_ServiceDesc), `genproto/demo.pb.go` (message definitions), `genproto.sh` (proto generation script)

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The PlaceOrder RPC has no idempotency mechanism. Each call generates a new UUID (`uuid.NewUUID()`) for the order, creates a new payment charge, and initiates a new shipment. There is no idempotency key in the `PlaceOrderRequest` message. Calling PlaceOrder twice with identical input creates two separate orders with two charges.
- **Implication**: For the current read-only agent scope, this is informational — read-only agents will not call PlaceOrder. If agent scope expands to write-enabled, this becomes a BLOCKER (agents retry on failure, creating duplicate orders and charges at machine speed).
- **Recommendation**: Before expanding to write-enabled agent scope, add an `idempotency_key` field to `PlaceOrderRequest` and implement deduplication logic.
- **Evidence**: `main.go` (PlaceOrder function — `uuid.NewUUID()` generates new ID per call, no idempotency check), `genproto/demo.pb.go` (PlaceOrderRequest has no idempotency_key field)

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: The service uses Protocol Buffers (protobuf) for request/response serialization — a strongly-typed, schema-defined binary format. The `PlaceOrderResponse` contains a structured `OrderResult` message with typed fields: `order_id` (string), `shipping_tracking_id` (string), `shipping_cost` (Money), `shipping_address` (Address), and `items` (repeated OrderItem).
- **Implication**: Protobuf is an excellent format for agent consumption — strongly typed, compact, and schema-defined. Agent tool definitions can map directly to proto message fields. However, agents using LLM-based reasoning may need a JSON transcoding layer since LLMs work better with text-based formats.
- **Recommendation**: Consider adding a gRPC-JSON transcoding proxy (e.g., grpc-gateway) to expose the service as a REST/JSON API for LLM-based agent frameworks.
- **Evidence**: `genproto/demo.pb.go` (PlaceOrderResponse, OrderResult message definitions), `go.mod` (google.golang.org/protobuf dependency)

### API-Q7: Asynchronous Operation Support

- **Severity**: INFO
- **Finding**: The PlaceOrder RPC is a synchronous multi-step operation that sequentially calls 6 downstream services: cart (GetCart), product catalog (GetProduct per item), currency (Convert per item), payment (Charge), shipping (ShipOrder), and email (SendOrderConfirmation). All calls are blocking. No background job submission, no polling endpoint, no webhook callback.
- **Implication**: An agent calling PlaceOrder synchronously will block until all 6+ downstream calls complete. Timeout risk is high for agent frameworks with connection timeout limits. This informs agent tool definition — generous timeouts (e.g., 60 seconds) should be configured.
- **Recommendation**: For future scope expansion, introduce an async checkout pattern: PlaceOrder returns an order_id immediately; a background worker processes the checkout steps; a GetOrderStatus RPC allows polling for completion.
- **Evidence**: `main.go` (PlaceOrder function — sequential calls to prepareOrderItemsAndShippingQuoteFromCart, chargeCard, shipOrder, emptyUserCart, sendOrderConfirmation)

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limits are documented and no rate limit headers are returned. The gRPC service does not include `X-RateLimit-Remaining`, `Retry-After`, or equivalent gRPC metadata in responses. No API documentation exists specifying call frequency limits.
- **Implication**: Agents calling this service have no signal about when they are approaching rate limits (once rate limiting is implemented per STATE-Q5). Self-throttling by agents is impossible without this metadata.
- **Recommendation**: When implementing rate limiting (STATE-Q5), include gRPC response metadata with remaining quota and retry-after values. Document rate limits in the service API documentation.
- **Evidence**: `main.go` (no rate limit metadata in responses)

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No transaction limits exist. No configurable limits on agent-initiated actions — no maximum orders per hour, no maximum spend per session, no maximum operations per agent identity. The PlaceOrder RPC processes any valid request without volume constraints.
- **Implication**: For read-only agent scope, transaction limits for write operations are informational only. If scope expands to write-enabled, the absence of transaction limits means an agent bug could place unlimited orders, charge unlimited amounts, or trigger unlimited shipments.
- **Recommendation**: Before expanding to write-enabled agent scope, implement configurable transaction limits per agent identity (e.g., `max_orders_per_hour=10`, `max_total_amount_per_session=$5000`).
- **Evidence**: `main.go` (no transaction limit logic)

### DATA-Q3: Selective Query Support

- **Severity**: INFO
- **Finding**: The CheckoutService exposes a single write RPC (`PlaceOrder`). There are no query RPCs, no pagination parameters, no filtering, no field selection, and no result size limits. The service does not support selective data retrieval — it accepts a complete `PlaceOrderRequest` and returns a complete `PlaceOrderResponse`.
- **Implication**: Since the current response size (single order result) is bounded, this is manageable. When adding read RPCs (per STATE-Q2 recommendation), pagination and filtering support must be designed in from the start.
- **Recommendation**: When adding read RPCs, implement gRPC server-side pagination using `page_token` and `page_size` fields. Add field masks for selective field retrieval.
- **Evidence**: `genproto/demo_grpc.pb.go` (single PlaceOrder RPC — no query methods)

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality metrics, dashboards, or monitoring exist. The checkout service does not publish data quality scores, completeness metrics, or freshness SLAs. Since the service is stateless and acts as an orchestrator, data quality depends on the 6 downstream services it calls. No data profiling or quality validation is performed on data received from downstream services.
- **Implication**: Agent decisions based on data from this service (prices, availability, shipping costs) could be affected by data quality issues in downstream services that the checkout service does not detect or signal.
- **Recommendation**: Add validation logic for critical downstream responses (e.g., verify that product prices are positive, currency codes are valid). Log data quality anomalies.
- **Evidence**: `main.go` (no data validation beyond what the money package provides for monetary arithmetic)

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Protobuf field names are well-structured and semantically meaningful. Examples from `genproto/demo.pb.go`: `user_id`, `user_currency`, `credit_card_number`, `credit_card_cvv`, `credit_card_expiration_year`, `street_address`, `city`, `state`, `country`, `zip_code`, `shipping_tracking_id`, `shipping_cost`, `product_id`, `quantity`, `order_id`. No legacy abbreviations or opaque codes. The `snake_case` naming convention is consistent across all messages.
- **Implication**: Field names are immediately interpretable by LLM-based agents. No data dictionary is needed. Agent tool definitions can use field names directly without translation.
- **Recommendation**: Maintain the current naming conventions. Document any non-obvious field semantics in proto comments.
- **Evidence**: `genproto/demo.pb.go` (PlaceOrderRequest, OrderResult, CreditCardInfo, Address — all with semantic field names)

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No data catalog or metadata layer exists. No AWS Glue Data Catalog, no Collibra, no DataHub, no metadata files beyond the proto definitions themselves. The proto files serve as a de facto schema catalog, but there is no higher-level catalog describing what data the system holds, its business meaning, or its relationships to other systems.
- **Implication**: Building agent tools against this service requires reading the proto files directly. There is no discoverable catalog that an agent orchestration framework could query to auto-discover available tools.
- **Recommendation**: Consider publishing the CheckoutService proto definitions to a service catalog or API registry (e.g., Buf Schema Registry, Backstage).
- **Evidence**: No data catalog or metadata files found. `genproto/demo.pb.go` serves as de facto schema.

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No business outcome metrics are published. No custom CloudWatch metrics, no business KPI dashboards, no metrics for checkout success rate, cart abandonment, payment failure rate, or order value distribution. The `initStats()` function contains only a TODO comment: `//TODO(arbrown) Implement OpenTelemetry stats`. Only infrastructure-level observability (traces via OpenTelemetry when enabled, logs via logrus) exists.
- **Implication**: When agents interact with the checkout service, there is no way to measure business impact (e.g., "did agent-initiated checkouts have a higher success rate than human-initiated ones?"). Business metrics are essential for evaluating agent effectiveness.
- **Recommendation**: Implement business metrics: checkout success/failure rate, average order value, payment failure rate, shipping success rate. Segment by caller identity (human vs agent) once AUTH-Q1 is resolved.
- **Evidence**: `main.go` (initStats function with TODO; no business metrics published)

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: The application exposes a documented gRPC interface: `hipstershop.CheckoutService` with a single RPC `PlaceOrder`. Defined via protobuf — generated Go code in `genproto/demo_grpc.pb.go` and `genproto/demo.pb.go`. Source proto at `../../protos/demo.proto` (per `genproto.sh`). No direct database access, file-based exchange, or UI automation required.
- **Gap**: N/A — a documented API interface exists.
- **Recommendation**: Ensure the proto definitions remain the single source of truth for the API contract.
- **Evidence**: `genproto/demo_grpc.pb.go`, `genproto/demo.pb.go`, `genproto.sh`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK
- **Finding**: Generated protobuf files provide a machine-readable schema. Source `.proto` file at `../../protos/demo.proto` is external to this repository. No schema versioning or changelog.
- **Gap**: Source proto not co-located; cannot verify generated code is current with source.
- **Recommendation**: Copy the source `demo.proto` into this repository. Add proto versioning.
- **Evidence**: `genproto.sh`, `genproto/demo_grpc.pb.go`, `genproto/demo.pb.go`

#### API-Q3: Structured Error Responses
- **Severity**: RISK
- **Finding**: PlaceOrder returns gRPC status errors (`codes.Internal`, `codes.Unavailable`) with raw error strings. No structured error bodies, no error codes, no retryable boolean.
- **Gap**: Agents cannot distinguish retriable from terminal errors beyond the gRPC status code.
- **Recommendation**: Implement `status.WithDetails()` with `errdetails.ErrorInfo` for structured error metadata.
- **Evidence**: `main.go` (PlaceOrder, chargeCard, shipOrder error returns)

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No idempotency mechanism. Each PlaceOrder call generates a new UUID, creates a new charge and shipment. No `idempotency_key` field in `PlaceOrderRequest`.
- **Gap**: Duplicate calls create duplicate orders. Not a concern for read-only agents.
- **Recommendation**: Add `idempotency_key` before expanding to write-enabled scope.
- **Evidence**: `main.go` (uuid.NewUUID per call), `genproto/demo.pb.go` (no idempotency_key field)

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: Protocol Buffers — strongly-typed, schema-defined binary format. `PlaceOrderResponse` contains structured `OrderResult` with typed fields.
- **Gap**: Binary format may require JSON transcoding for LLM-based agents.
- **Recommendation**: Consider adding gRPC-JSON transcoding proxy (grpc-gateway).
- **Evidence**: `genproto/demo.pb.go` (PlaceOrderResponse, OrderResult), `go.mod`

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `orchestrator`, agent_scope: `read-only`.
- **Trigger**: Service has operations >30s OR long-running workflows
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: No event emission, webhooks, or messaging integration. State changes happen synchronously within PlaceOrder. No SNS, EventBridge, SQS, or Kafka integration.
- **Gap**: Agents cannot reactively respond to checkout events.
- **Recommendation**: Add event emission to SNS/EventBridge for order lifecycle events.
- **Evidence**: `main.go` (no event publishing), `go.mod` (no messaging dependencies)

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limits documented. No rate limit headers or gRPC metadata in responses.
- **Gap**: Agents have no self-throttling signal.
- **Recommendation**: When implementing rate limiting (STATE-Q5), include quota metadata in responses.
- **Evidence**: `main.go` (no rate limit metadata)

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: gRPC server created with no authentication interceptors. All client connections use `insecure.NewCredentials()`. Server accepts any connection without identity verification. Istio AuthorizationPolicies disabled in Helm values.
- **Gap**: No machine identity authentication at any layer. Any network-reachable client can call PlaceOrder.
- **Recommendation**: Enable Istio AuthorizationPolicies (immediate). Add application-layer gRPC auth interceptor (defense-in-depth).
- **Evidence**: `main.go` (mustConnGRPC, grpc.NewServer — no auth), `helm-chart/values.yaml` (`authorizationPolicies.create: false`)

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK
- **Finding**: No authorization model. No interceptors checking permissions. All callers have identical access. Helm AuthorizationPolicy template exists but is disabled.
- **Gap**: No mechanism to grant read-only vs write access.
- **Recommendation**: Enable AuthorizationPolicy. Add authorization interceptor with role-based access control.
- **Evidence**: `main.go` (no authorization interceptors), `helm-chart/templates/checkoutservice.yaml` (AuthorizationPolicy — disabled)

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK
- **Finding**: Single RPC (PlaceOrder) is a write operation. No read-only RPCs. No per-action permission checks.
- **Gap**: Cannot allow read without write. Entire surface is write-only.
- **Recommendation**: Add read RPCs (GetOrderStatus). Implement per-RPC authorization.
- **Evidence**: `genproto/demo_grpc.pb.go` (single method), `main.go`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: RISK
- **Finding**: `user_id` is a caller-provided string — no JWT validation, no token exchange. Any caller can provide any user_id. No distinction between agent-as-self and agent-on-behalf-of-user modes.
- **Gap**: No verified identity propagation. user_id is self-asserted. Cannot distinguish agent identity modes.
- **Recommendation**: Implement JWT-based identity propagation. Add gRPC metadata for agent mode distinction.
- **Evidence**: `main.go` (req.UserId used directly; no identity handling), `genproto/demo.pb.go` (PlaceOrderRequest.UserId)

#### AUTH-Q5: Credential Management
- **Severity**: RISK
- **Finding**: Service addresses from env vars (not credentials). No secrets management. Credit card data transits over insecure gRPC. No .env files committed (positive).
- **Gap**: No secrets management infrastructure for future credential needs. Credit card data unencrypted in transit.
- **Recommendation**: Integrate AWS Secrets Manager. Enable TLS on all gRPC connections.
- **Evidence**: `main.go` (mustMapEnv, insecure.NewCredentials)

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: Application logs to stdout via logrus JSON. No immutable audit logs, no CloudTrail, no tamper-evident storage. Tracing disabled in Helm values.
- **Gap**: No immutable audit trail. Logs are ephemeral.
- **Recommendation**: Ship logs to immutable store. Add caller identity to audit entries. Enable tracing.
- **Evidence**: `main.go` (logrus to stdout), `helm-chart/values.yaml` (`tracing: false`)

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK
- **Finding**: No identity management. No suspension capability. Only option is to shut down service or change network rules. AuthorizationPolicy (once enabled) would support principal-based blocking.
- **Gap**: Cannot isolate a misbehaving agent.
- **Recommendation**: Enable AuthorizationPolicies. Include per-identity suspension in AUTH-Q1 remediation.
- **Evidence**: `main.go` (no identity management), `helm-chart/templates/checkoutservice.yaml` (AuthorizationPolicy supports principal removal)

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: PlaceOrder has no compensation logic. If shipOrder fails after chargeCard, payment is not reversed. emptyUserCart failure is silently discarded (`_ = cs.emptyUserCart`).
- **Gap**: No saga pattern. Partial failures leave inconsistent state.
- **Recommendation**: Implement saga with compensation steps (refund on shipping failure).
- **Evidence**: `main.go` (PlaceOrder sequential workflow, `_ = cs.emptyUserCart`)

#### STATE-Q2: Queryable Current State
- **Severity**: RISK
- **Finding**: Only PlaceOrder RPC exists. No GetOrder, GetOrderStatus, or ListOrders. Service is stateless — no persistence. Orchestrator pattern — state distributed across downstream services.
- **Gap**: Agent cannot query order state after placement. State is distributed across 6 downstream services with no single point of query.
- **Recommendation**: Add read RPCs with persistence layer (e.g., `GetOrderStatus(order_id)`, `ListOrders(user_id)`).
- **Evidence**: `genproto/demo_grpc.pb.go` (single method), `main.go` (no database)

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `orchestrator`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled AND service has persistent state
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK
- **Finding**: 3-second connection timeout only. No circuit breakers, no per-call timeouts, no retry logic. 6 downstream dependencies — single slow service cascades. No resilience libraries in go.mod.
- **Gap**: No resilience patterns. Cascading failure risk across 6 dependencies.
- **Recommendation**: Add per-RPC timeouts and circuit breaker library (sony/gobreaker).
- **Evidence**: `main.go` (mustConnGRPC timeout only), `go.mod` (no resilience libraries)

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK
- **Finding**: No rate limiting at any layer. Server accepts unlimited connections. No rate-limiting libraries in go.mod.
- **Gap**: Runaway agent could call PlaceOrder at machine speed.
- **Recommendation**: Add gRPC rate-limiting interceptor with per-caller limits.
- **Evidence**: `main.go` (no rate limiting), `go.mod` (no rate limit libraries), `helm-chart/templates/checkoutservice.yaml` (no throttling)

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No transaction limits exist. No configurable limits on agent-initiated actions — no maximum orders per hour, no maximum spend per session, no maximum operations per agent identity. The PlaceOrder RPC processes any valid request without volume constraints.
- **Gap**: Not relevant for read-only scope. Critical for write-enabled expansion.
- **Recommendation**: Before expanding to write-enabled agent scope, implement configurable transaction limits per agent identity (e.g., `max_orders_per_hour=10`, `max_total_amount_per_session=$5000`).
- **Evidence**: `main.go` (no transaction limit logic)

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: RISK
- **Finding**: No autoscaling, no load tests, no capacity planning. 1 agent call = 6+ downstream calls (amplification). No HPA in Helm chart.
- **Gap**: No evidence infrastructure is sized for agent traffic.
- **Recommendation**: Add HPA configuration. Conduct load testing.
- **Evidence**: `Dockerfile` (single binary), `helm-chart/templates/checkoutservice.yaml` (no HPA)

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `orchestrator`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `orchestrator`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK
- **Finding**: No staging environment, no docker-compose, no seed data. Helm chart deploys single environment configuration.
- **Gap**: No safe environment for agent testing.
- **Recommendation**: Create docker-compose with mocked downstream services. Define staging Helm values override.
- **Evidence**: `Dockerfile`, `helm-chart/templates/checkoutservice.yaml`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: PlaceOrderRequest contains unclassified PII (email, address) and PCI data (credit_card_number, credit_card_cvv). No field-level classification, no encryption, no access controls. PII logged in cleartext.
- **Gap**: Sensitive data flows unclassified and unprotected.
- **Recommendation**: Classify all proto fields with sensitivity tags. Implement log scrubbing. Enable TLS.
- **Evidence**: `genproto/demo.pb.go` (PlaceOrderRequest, CreditCardInfo, Address), `main.go` (PII logging, insecure gRPC)

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: No data residency controls. PII and PCI data processed with no region configuration.
- **Gap**: No technical controls preventing cross-region data transmission.
- **Recommendation**: Document residency requirements. Configure region-locked deployment.
- **Evidence**: `main.go` (no region config), `go.mod` (GCP profiler), `genproto/demo.pb.go` (Address with country)

#### DATA-Q3: Selective Query Support
- **Severity**: INFO
- **Finding**: Single write RPC. No query RPCs, no pagination, no filtering. Response size is bounded (single order result).
- **Gap**: No selective query support, but current response size is manageable.
- **Recommendation**: When adding read RPCs, include pagination and field masks.
- **Evidence**: `genproto/demo_grpc.pb.go` (single PlaceOrder)

#### DATA-Q4: System of Record Designations
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `orchestrator`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK
- **Finding**: OrderResult has no timestamp fields. No freshness metadata in responses. UUID includes time component but not exposed. No Cache-Control or consistency signaling.
- **Gap**: Agent cannot determine when order was placed or whether data is current.
- **Recommendation**: Add `created_at` Timestamp to OrderResult. Add freshness indicators to gRPC metadata.
- **Evidence**: `genproto/demo.pb.go` (OrderResult — no timestamps), `main.go` (uuid.NewUUID, no freshness metadata)

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK
- **Finding**: user_id and email logged in cleartext via logrus. No log scrubbing or PII masking.
- **Gap**: PII in cleartext logs — compliance risk under GDPR and other privacy regulations.
- **Recommendation**: Add logrus Hook for PII masking. Replace direct PII with hashed values.
- **Evidence**: `main.go` (log.Infof with user_id, log.Warnf/Infof with email)

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics. Orchestrator depends on downstream service data quality with no validation.
- **Gap**: No quality signals for agent decision-making.
- **Recommendation**: Add validation for critical downstream responses.
- **Evidence**: `main.go` (no data validation)

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK
- **Finding**: Generated proto files provide schema. Source proto external. Proto package is `hipstershop` with no version. No versioning, changelog, or breaking change detection in CI.
- **Gap**: Schema evolution not tracked. Breaking changes undetected.
- **Recommendation**: Add source proto. Version the package (`hipstershop.checkout.v1`). Add `buf breaking` to CI.
- **Evidence**: `genproto.sh`, `genproto/demo.pb.go`, `genproto/demo_grpc.pb.go`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Proto fields use clear snake_case names: user_id, credit_card_number, shipping_tracking_id, street_address, etc. No legacy codes.
- **Gap**: None — naming is excellent.
- **Recommendation**: Maintain current conventions.
- **Evidence**: `genproto/demo.pb.go` (all message types)

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No data catalog beyond proto definitions.
- **Gap**: No discoverable catalog for agent auto-discovery.
- **Recommendation**: Publish to service catalog (Buf Schema Registry, Backstage).
- **Evidence**: No catalog files found.

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK
- **Finding**: OpenTelemetry tracing integrated but disabled in deployment (`tracing: false` in Helm values). JSON structured logging via logrus. No correlation IDs linking traces to logs.
- **Gap**: Tracing disabled. Logs and traces disconnected.
- **Recommendation**: Enable tracing (`tracing: true`). Add trace_id to log entries.
- **Evidence**: `main.go` (initTracing, otelgrpc, logrus JSONFormatter), `helm-chart/values.yaml` (`tracing: false`), `go.mod` (OTel deps)

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK
- **Finding**: No alerting. initStats() has TODO comment. No metrics published.
- **Gap**: No automated notification on service degradation.
- **Recommendation**: Implement OTel stats. Configure error rate and latency alerts.
- **Evidence**: `main.go` (initStats TODO)

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No business metrics. Only infrastructure observability (traces when enabled, logs).
- **Gap**: Cannot measure agent business impact.
- **Recommendation**: Implement checkout success/failure rate and order value metrics.
- **Evidence**: `main.go` (initStats TODO, no business metrics)

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK
- **Finding**: Helm chart defines Deployment, Service, NetworkPolicy, Sidecar, AuthorizationPolicy as IaC. AuthorizationPolicy disabled. No drift detection. No CODEOWNERS.
- **Gap**: IaC exists but key controls disabled. No drift detection or peer review enforcement.
- **Recommendation**: Enable AuthorizationPolicies. Add CODEOWNERS. Implement drift detection.
- **Evidence**: `helm-chart/templates/checkoutservice.yaml`, `helm-chart/values.yaml`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK
- **Finding**: No CI/CD pipelines. No contract testing. genproto.sh is manual.
- **Gap**: Proto changes undetected. No build automation.
- **Recommendation**: Create CI pipeline with `go test`, proto drift detection, and `buf breaking`.
- **Evidence**: No CI/CD files. `genproto.sh`.

#### ENG-Q3: Rollback Capability
- **Severity**: RISK
- **Finding**: No rollback configuration. No blue/green, no canary, no feature flags. Helm chart has no deployment strategy.
- **Gap**: No automated rollback if deployment breaks APIs.
- **Recommendation**: Add deployment strategy to Helm chart. Tag images with Git SHA.
- **Evidence**: `Dockerfile` (no rollback metadata), `helm-chart/templates/checkoutservice.yaml` (no deployment strategy)

#### ENG-Q4: API Test Coverage
- **Severity**: RISK
- **Finding**: Only `money/money_test.go` exists — unit tests for monetary arithmetic. Zero tests for PlaceOrder RPC.
- **Gap**: Agent-facing API surface entirely untested.
- **Recommendation**: Write integration tests using grpc/test/bufconn with mocked services.
- **Evidence**: `money/money_test.go` (arithmetic tests only)

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: RISK
- **Finding**: Service is stateless. No encryption config. Log output contains PII (DATA-Q6) that may be persisted. Handles PCI data in memory.
- **Gap**: No encryption controls for log storage. PCI data transits unencrypted.
- **Recommendation**: Ensure log destinations use KMS encryption. Encrypt PCI data at application layer.
- **Evidence**: `Dockerfile` (stateless), `helm-chart/templates/checkoutservice.yaml` (no encryption config)

---

## Evidence Index

### Infrastructure as Code
| File | Questions Referenced |
|------|---------------------|
| `helm-chart/templates/checkoutservice.yaml` | AUTH-Q1, AUTH-Q2, AUTH-Q7, STATE-Q5, STATE-Q7, HITL-Q3, ENG-Q1, ENG-Q3, ENG-Q5 |
| `helm-chart/values.yaml` | AUTH-Q1, AUTH-Q6, OBS-Q1, ENG-Q1 |

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `main.go` | API-Q1, API-Q2, API-Q3, API-Q4, API-Q5, API-Q7, API-Q8, AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q2, STATE-Q4, STATE-Q5, STATE-Q7, DATA-Q1, DATA-Q2, DATA-Q3, DATA-Q5, DATA-Q6, DATA-Q7, OBS-Q1, OBS-Q2, OBS-Q3, ENG-Q4 |
| `money/money_test.go` | ENG-Q4 |
| `genproto/demo.pb.go` | API-Q1, API-Q2, API-Q4, API-Q5, AUTH-Q4, DATA-Q1, DATA-Q2, DATA-Q3, DATA-Q5, DISC-Q1, DISC-Q2 |
| `genproto/demo_grpc.pb.go` | API-Q1, API-Q2, AUTH-Q3, STATE-Q2, DATA-Q3, DISC-Q1 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `Dockerfile` | STATE-Q7, HITL-Q3, ENG-Q3, ENG-Q5 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `go.mod` | API-Q5, API-Q7, AUTH-Q5, STATE-Q4, STATE-Q5, DATA-Q2, OBS-Q1 |

### Scripts
| File | Questions Referenced |
|------|---------------------|
| `genproto.sh` | API-Q1, API-Q2, DISC-Q1, ENG-Q2 |
