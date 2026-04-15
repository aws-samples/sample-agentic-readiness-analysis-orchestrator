# Agentic Readiness Assessment Report

**Target**: services/microservices-demo/src/checkoutservice
**Date**: 2026-04-15
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Agent Scope**: read-only
**Priority**: P0
**Tags**: go, grpc, orchestrator, critical-path
**Context**: Go gRPC service orchestrating the checkout workflow — calls cart, product, shipping, currency, payment, and email services.

---

## Readiness Profile: Not Agent-Integrable

**BLOCKERs**: 3 | **RISKs**: 35 | **INFOs**: 11

Exclude from agent toolset or plan major remediation before re-evaluation. Three blockers must be resolved before any agent deployment — including pilots. The service lacks machine identity authentication (AUTH-Q1), has unclassified PCI-sensitive data flowing through it (DATA-Q1), and has no network security configuration (ENG-Q6). These are foundational gaps that create compliance exposure, data integrity risk, and failure-at-scale risk for any agent integration.

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
- **Finding**: The gRPC server in `main.go` is created with `grpc.NewServer()` using only an OpenTelemetry stats handler — no TLS, no authentication interceptors, no OAuth2 client credentials flow, no API key authentication, and no mTLS configuration. All downstream gRPC client connections use `insecure.NewCredentials()` (line: `grpc.WithTransportCredentials(insecure.NewCredentials())`). There is no mechanism to authenticate or attribute the calling principal. Any network-reachable client can invoke `PlaceOrder` without identification.
- **Gap**: No machine identity authentication exists. The service cannot distinguish who is calling it — human, agent, or rogue process. No principal attribution in any logs.
- **Remediation**:
  - **Immediate**: Add a gRPC server interceptor that validates an authentication token (mTLS certificate, OAuth2 bearer token, or API key with principal attribution) on every incoming request. Use `grpc.UnaryInterceptor()` or `grpc.ChainUnaryInterceptor()` in the server options.
  - **Target State**: Every gRPC call to CheckoutService is authenticated with a machine identity that is logged and auditable. Agents have distinct service accounts from human-facing frontends.
  - **Estimated Effort**: Medium (2–4 weeks including infrastructure changes for cert management or token issuer)
  - **Dependencies**: ENG-Q6 (network policies) — authentication and network security should be implemented together.
- **Evidence**: `main.go` (lines creating gRPC server and client connections), `go.mod` (no auth libraries present)

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: The `PlaceOrderRequest` protobuf message in `genproto/demo.pb.go` includes `CreditCardInfo` with fields: `credit_card_number` (string), `credit_card_cvv` (int32), `credit_card_expiration_year` (int32), `credit_card_expiration_month` (int32). The request also includes `email` (string — PII) and `Address` with `street_address`, `city`, `state`, `country`, `zip_code` (PII). Credit card data flows through the checkout service to the payment service via `chargeCard()` in `main.go` without any field-level encryption, tokenization, or classification tags. The email address is logged in plaintext: `log.Infof("order confirmation email sent to %q", req.Email)`.
- **Gap**: PCI-DSS sensitive data (credit card number, CVV) and PII (email, address) are not classified, tagged, or protected at the field level. No access controls prevent an agent from retrieving this data. Credit card data transits in-memory without tokenization.
- **Remediation**:
  - **Immediate**: Implement credit card tokenization before the data reaches the checkout service — the frontend or an API gateway should tokenize card data and pass only a token. At minimum, add field-level classification annotations to the protobuf schema marking `CreditCardInfo` fields as PCI-DSS and `email`/`Address` as PII.
  - **Target State**: Credit card data never transits the checkout service in plaintext. All sensitive fields are classified in the schema. Agent-facing APIs do not expose raw PCI data. PII is redacted from logs.
  - **Estimated Effort**: High (4–8 weeks — requires tokenization infrastructure and schema changes across services)
  - **Dependencies**: DATA-Q7 (PII in logs) — resolving DATA-Q1 should include log redaction.
- **Evidence**: `genproto/demo.pb.go` (CreditCardInfo, PlaceOrderRequest types), `main.go` (chargeCard function, email logging)

### ENG-Q6: Cross-Origin and Network Policies

- **Severity**: BLOCKER
- **Finding**: No CORS configuration, security group rules, firewall rules, network policies, API gateway access policies, or WAF rules are defined anywhere in this repository. The gRPC server in `main.go` binds to `0.0.0.0:5050` (via `net.Listen("tcp", fmt.Sprintf(":%s", port))`) with no access restrictions. All downstream gRPC connections use `insecure.NewCredentials()` — unencrypted plaintext communication. The `Dockerfile` exposes port 5050 without any network security context. No Kubernetes NetworkPolicy, Istio AuthorizationPolicy, or equivalent is present.
- **Gap**: The service has no network security boundary. Any process that can reach port 5050 can invoke PlaceOrder (which charges credit cards). No TLS encryption in transit. No documentation of network security controls even if they exist elsewhere.
- **Remediation**:
  - **Immediate**: Enable TLS on the gRPC server using `grpc.Creds(credentials.NewTLS(tlsConfig))`. Define Kubernetes NetworkPolicy (or equivalent) restricting ingress to the checkout service to only authorized callers. Document all network security controls.
  - **Target State**: gRPC server uses mTLS. Network policies restrict access to authorized services only. All in-transit communication is encrypted. Controls are documented and discoverable.
  - **Estimated Effort**: Medium (2–4 weeks for TLS + network policy implementation)
  - **Dependencies**: AUTH-Q1 (machine identity) — mTLS implementation addresses both authentication and encryption in transit.
- **Evidence**: `main.go` (grpc.NewServer with no TLS, insecure.NewCredentials), `Dockerfile` (EXPOSE 5050), absence of any IaC, network policy, or security configuration files

**Remediation Prioritization**: Resolve AUTH-Q1 and ENG-Q6 together (mTLS addresses both). Then resolve DATA-Q1 (tokenization). Identity before data access — you cannot enforce data access controls without knowing who is calling. Consider scoping the initial agent to read-only operations on other services while remediating the checkout service's write-path security.

---

## RISKs — Proceed with Compensating Controls

### API-Q2: Machine-Readable API Specification

- **Severity**: RISK
- **Finding**: The protobuf definition (`demo.proto`, referenced by `genproto.sh`) is a machine-readable interface specification. Generated Go code in `genproto/demo.pb.go` and `genproto/demo_grpc.pb.go` defines typed messages and service stubs. However, no OpenAPI, AsyncAPI, or Smithy specification exists. The `.proto` source file is not in this repository (referenced as `../../protos/demo.proto` in `genproto.sh`).
- **Gap**: While protobuf is machine-readable, the source `.proto` file is not co-located with the service. No standalone API specification document exists for agent tool generation. Agent frameworks typically consume OpenAPI or gRPC reflection — neither is configured.
- **Compensating Controls**:
  - Enable gRPC server reflection (`reflection.Register(srv)`) to allow runtime schema discovery
  - Generate an OpenAPI spec from the protobuf using `grpc-gateway` or `buf` tooling for REST-based agent consumption
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add gRPC reflection to the server and co-locate the `.proto` source file with the service.
- **Evidence**: `genproto.sh` (protoc command referencing `../../protos/demo.proto`), `genproto/demo_grpc.pb.go` (generated service stubs)

### API-Q3: Structured Error Responses

- **Severity**: RISK
- **Finding**: Error handling uses gRPC status codes: `status.Errorf(codes.Internal, "failed to generate order uuid")`, `status.Errorf(codes.Internal, err.Error())`, `status.Errorf(codes.Unavailable, "shipping error: %+v", err)`. The `codes.Internal` vs `codes.Unavailable` distinction provides some structure. However, error messages embed raw Go error strings (`err.Error()`, `%+v` formatting of wrapped errors). There is no structured error body with error codes, retryable booleans, or error categories beyond the gRPC status code.
- **Gap**: Missing structured error bodies. Agents cannot distinguish retryable from terminal errors without parsing raw error message strings. No consistent error code taxonomy (e.g., `PAYMENT_FAILED`, `CART_EMPTY`).
- **Compensating Controls**:
  - Agent-side: Map gRPC status codes to retry behavior (`Unavailable` → retry, `Internal` → do not retry)
  - Implement gRPC error details using `google.rpc.Status` with `google.rpc.ErrorInfo` for structured error metadata
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add gRPC rich error details (`errdetails.ErrorInfo`) to all error responses with domain-specific error codes and retryable flags.
- **Evidence**: `main.go` (PlaceOrder, chargeCard, shipOrder error handling)

### API-Q5: API Versioning and Deprecation

- **Severity**: RISK
- **Finding**: The gRPC service uses package `hipstershop` with no version prefix. The full method name is `/hipstershop.CheckoutService/PlaceOrder` — no `/v1/` or version header. No changelog, deprecation notice, or versioning policy found in the repository. The `README.md` contains only a single line about `dep ensure`.
- **Gap**: No API versioning strategy. Breaking changes to the protobuf schema would silently break agent tool definitions. No deprecation notification mechanism.
- **Compensating Controls**:
  - Use protobuf field numbering conventions (never reuse or remove field numbers) as an implicit compatibility guarantee
  - Add a `buf breaking` check in CI to detect breaking protobuf changes before merge
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Adopt semantic versioning for the protobuf package (e.g., `hipstershop.v1`) and implement `buf breaking` checks in CI.
- **Evidence**: `genproto/demo_grpc.pb.go` (CheckoutService_PlaceOrder_FullMethodName), `README.md`

### API-Q7: Asynchronous Operation Support

- **Severity**: RISK
- **Finding**: `PlaceOrder` in `main.go` is synchronous. It sequentially calls: `getUserCart` → `prepareOrderItemsAndShippingQuoteFromCart` (which calls `GetProduct` per item + `convertCurrency` + `quoteShipping`) → `chargeCard` → `shipOrder` → `emptyUserCart` → `sendOrderConfirmation`. For a cart with N items, this is at minimum 6+N downstream gRPC calls executed sequentially. No background job framework, polling endpoint, or webhook callback pattern exists.
- **Gap**: Long-running synchronous operation with no async alternative. Agent calls to PlaceOrder will block for the entire multi-step workflow duration, risking timeouts for large carts.
- **Compensating Controls**:
  - Set generous gRPC client timeouts on the agent side (30–60 seconds)
  - Limit agent usage to small carts to reduce latency
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement an async pattern: return an order_id immediately, process the workflow asynchronously, and expose a `GetOrderStatus` RPC for polling.
- **Evidence**: `main.go` (PlaceOrder method, sequential downstream calls)

### AUTH-Q2: Scoped Permissions (Least Privilege)

- **Severity**: RISK
- **Finding**: No IAM policies, RBAC definitions, or scoped permission model found in the codebase. The gRPC server registers `CheckoutServiceServer` with no authorization interceptor. Any authenticated caller (once AUTH-Q1 is resolved) would have full access to PlaceOrder — there is no way to grant read-only access or restrict to specific operations.
- **Gap**: No scoped permission model. An agent identity cannot be restricted to specific actions or resources.
- **Compensating Controls**:
  - Enforce scoped permissions at the platform layer (API gateway, service mesh authorization policy) rather than in application code
  - Use separate service accounts with distinct IAM policies for different agent scopes
- **Remediation Timeline**: 30–60 days (after AUTH-Q1 is resolved)
- **Recommendation**: Implement a gRPC authorization interceptor that checks caller permissions per-method, or enforce via Istio AuthorizationPolicy / Kubernetes RBAC.
- **Evidence**: `main.go` (grpc.NewServer with no auth interceptor)

### AUTH-Q3: Action-Level Authorization

- **Severity**: RISK
- **Finding**: The service exposes a single RPC (`PlaceOrder`) which is a write operation. No action-level authorization exists — there are no permission checks, no middleware for distinguishing read vs write callers, and no ABAC/RBAC logic.
- **Gap**: Cannot enforce action-level authorization. An agent granted any access can execute PlaceOrder (a high-impact write operation that charges credit cards and ships orders).
- **Compensating Controls**:
  - Restrict agent access to the checkout service entirely at the network/service mesh level until write-enabled scope is approved
  - Implement a gRPC interceptor that checks method-level permissions against the authenticated identity
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add per-method authorization checks in a gRPC interceptor. For a read-only agent scope, block all access to PlaceOrder at the authorization layer.
- **Evidence**: `main.go` (single RPC registration, no auth middleware)

### AUTH-Q4: Identity Propagation

- **Severity**: RISK
- **Finding**: The `PlaceOrderRequest` includes a `user_id` field (`req.UserId`) which is logged: `log.Infof("[PlaceOrder] user_id=%q user_currency=%q", req.UserId, req.UserCurrency)`. However, this user_id is a request parameter — not an authenticated identity. There is no JWT parsing, OAuth2 on-behalf-of flow, or token exchange. The caller can pass any user_id value without verification. The user_id is passed downstream to cart and other services without validation.
- **Gap**: No identity propagation. The system trusts the caller-supplied user_id without verification. An agent (or any caller) can act as any user by supplying their user_id.
- **Compensating Controls**:
  - Validate user_id against the authenticated caller's identity at the gateway/interceptor layer
  - Implement JWT-based identity propagation where user_id is extracted from a verified token
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement token-based identity propagation using JWT or OAuth2 on-behalf-of flows. Extract user_id from verified tokens, not request parameters.
- **Evidence**: `main.go` (PlaceOrder uses req.UserId without verification), `genproto/demo.pb.go` (PlaceOrderRequest.UserId field)

### AUTH-Q5: Agent-as-Self vs Agent-on-Behalf-of-User

- **Severity**: RISK
- **Finding**: No distinction exists between agent-as-self and agent-on-behalf-of-user modes. The service has no authentication (AUTH-Q1) and no identity propagation (AUTH-Q4), so there is no mechanism to differentiate these two access patterns. No separate auth flows, no audit log fields distinguishing the modes.
- **Gap**: Cannot distinguish agent acting under its own identity from agent acting on behalf of a user. Both would use the same unauthenticated path.
- **Compensating Controls**:
  - Design the authentication implementation (AUTH-Q1) to support both modes from the start — separate service account tokens for agent-as-self vs delegated user tokens for agent-on-behalf-of-user
- **Remediation Timeline**: 60–90 days (implement alongside AUTH-Q1 and AUTH-Q4)
- **Recommendation**: Define two authentication flows: (1) service account for agent autonomous actions, (2) delegated token for agent-on-behalf-of-user. Log the mode in audit records.
- **Evidence**: `main.go` (no authentication, no identity distinction)

### AUTH-Q6: Credential Management

- **Severity**: RISK
- **Finding**: Service addresses are configured via environment variables: `SHIPPING_SERVICE_ADDR`, `PRODUCT_CATALOG_SERVICE_ADDR`, `CART_SERVICE_ADDR`, `CURRENCY_SERVICE_ADDR`, `EMAIL_SERVICE_ADDR`, `PAYMENT_SERVICE_ADDR`, `COLLECTOR_SERVICE_ADDR`. These are service addresses, not secrets. No hardcoded passwords, API keys, or credentials were found in the code. However, no secrets management system (AWS Secrets Manager, HashiCorp Vault) is referenced anywhere. The `go.mod` contains no Vault or Secrets Manager client libraries.
- **Gap**: No secrets management infrastructure. When authentication is added (AUTH-Q1), credentials will need secure storage and rotation. Current architecture has no provision for this.
- **Compensating Controls**:
  - Use Kubernetes Secrets mounted as environment variables for initial credential management
  - Plan for AWS Secrets Manager or HashiCorp Vault integration when implementing AUTH-Q1
- **Remediation Timeline**: 30–60 days (implement alongside AUTH-Q1)
- **Recommendation**: Integrate AWS Secrets Manager or HashiCorp Vault for credential storage and rotation. Add client libraries to `go.mod`.
- **Evidence**: `main.go` (mustMapEnv function, env var configuration), `go.mod` (no secrets management libraries)

### AUTH-Q7: Immutable Audit Logging ⚡

- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: The service uses logrus with JSON formatter for structured logging. Application logs capture `user_id` and `user_currency` for PlaceOrder calls, and `email` for order confirmations. However, these are application logs — not immutable audit logs. No CloudTrail configuration, S3 object lock for log storage, CloudWatch log retention policies, or log file validation is found. No log immutability guarantee exists.
- **Gap**: No immutable audit trail. Application logs can be modified or deleted. No tamper-evident log storage. If an agent executes operations, there is no forensic-grade audit record.
- **Compensating Controls**:
  - Ship application logs to a centralized, append-only log aggregation system (CloudWatch Logs with retention lock, S3 with object lock)
  - Add audit-specific log entries with caller identity, action, timestamp, and outcome
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement structured audit logging with caller identity, action, and outcome fields. Ship to immutable storage (S3 with object lock or CloudWatch Logs with retention policy).
- **Evidence**: `main.go` (logrus JSON logging, PlaceOrder log statements)

### AUTH-Q8: Agent Identity Suspension

- **Severity**: RISK
- **Finding**: No mechanism to suspend or revoke individual agent identities exists. The service has no authentication (AUTH-Q1), so there are no identities to suspend. No API key revocation endpoints, no IAM role deactivation procedures, no service account disable functionality.
- **Gap**: Cannot isolate a misbehaving agent without shutting down the entire service.
- **Compensating Controls**:
  - At the network layer, block specific source IPs or service accounts via network policy updates
  - Design the authentication system (AUTH-Q1) with per-agent identity revocation from the start
- **Remediation Timeline**: 30–60 days (implement alongside AUTH-Q1)
- **Recommendation**: Implement per-agent API key or certificate management with instant revocation capability.
- **Evidence**: `main.go` (no authentication or identity management), absence of any identity management configuration
### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: The `PlaceOrder` method in `main.go` executes a multi-step workflow: (1) `getUserCart`, (2) `prepareOrderItemsAndShippingQuoteFromCart` (get products, convert currency, get shipping quote), (3) `chargeCard`, (4) `shipOrder`, (5) `emptyUserCart`, (6) `sendOrderConfirmation`. If `shipOrder` fails after `chargeCard` succeeds, the card is charged but no shipment occurs — and there is NO compensation or rollback logic (no refund call). The `emptyUserCart` failure is silently ignored: `_ = cs.emptyUserCart(ctx, req.UserId)`. The `sendOrderConfirmation` failure is logged as a warning but does not fail the order.
- **Gap**: No saga pattern, no compensating transactions, no undo endpoints. Partial failure leaves the system in an inconsistent state (charged but not shipped).
- **Compensating Controls**:
  - Add a refund/reversal call to the payment service if `shipOrder` fails after `chargeCard` succeeds
  - For agent scope: read-only agents would not invoke PlaceOrder, limiting exposure to this gap
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement a saga pattern with compensating transactions. At minimum, add a `chargeCard` reversal when `shipOrder` fails.
- **Evidence**: `main.go` (PlaceOrder method — chargeCard before shipOrder, no rollback on shipOrder failure, emptyUserCart error silently ignored)

### STATE-Q2: Queryable Current State

- **Severity**: RISK
- **Finding**: The CheckoutService exposes only one RPC: `PlaceOrder` (a write operation). There are no query endpoints to inspect order state, checkout status, or cart contents through this service. The service is a write-only orchestrator.
- **Gap**: No queryable state. An agent cannot inspect order status, verify cart contents, or check checkout progress through this service.
- **Compensating Controls**:
  - Agent can query cart state directly from the cart service (if accessible)
  - Add a `GetOrderStatus` or `PreviewOrder` RPC that returns order details without executing the checkout
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a `PreviewOrder` RPC that calculates totals and shipping without charging, and a `GetOrderStatus` RPC for post-checkout queries.
- **Evidence**: `genproto/demo_grpc.pb.go` (only PlaceOrder RPC registered for CheckoutService)

### STATE-Q3: Concurrency Controls

- **Severity**: RISK
- **Finding**: No optimistic locking, version fields, ETags, or conditional writes found. Multiple concurrent `PlaceOrder` calls for the same `user_id` could race: both read the same cart contents, both charge the card, and both ship the order — resulting in duplicate orders. The `getUserCart` → `chargeCard` → `emptyUserCart` sequence has no atomicity guarantees.
- **Gap**: No concurrency controls on the checkout workflow. Concurrent agent invocations (or agent + human) could create duplicate orders.
- **Compensating Controls**:
  - Rate-limit agent invocations of PlaceOrder per user_id to 1 concurrent request at the gateway
  - Add a distributed lock (Redis lock, DynamoDB conditional write) on user_id during checkout
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement a distributed lock on `user_id` during the PlaceOrder workflow to prevent concurrent checkouts for the same user.
- **Evidence**: `main.go` (PlaceOrder — no locking, no conditional operations)

### STATE-Q4: Circuit Breakers and Resilience

- **Severity**: RISK
- **Finding**: No circuit breakers, retry logic, or per-call timeout configurations on downstream gRPC calls. The `mustConnGRPC` function uses a 3-second timeout for initial connection (`context.WithTimeout(ctx, time.Second*3)`) but this is connection-time only — there are no runtime call timeouts, no exponential backoff, no circuit breaker annotations. If the payment service hangs, the checkout service hangs indefinitely. No resilience libraries (Resilience4j equivalent for Go, `sony/gobreaker`) in `go.mod`.
- **Gap**: Downstream service failures cascade directly to callers. A failing payment service takes down the checkout service.
- **Compensating Controls**:
  - Add per-RPC deadlines using `context.WithTimeout` on each downstream call
  - Implement a circuit breaker (e.g., `sony/gobreaker`) on downstream connections
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `context.WithTimeout` to every downstream gRPC call and implement circuit breakers using `sony/gobreaker` or similar.
- **Evidence**: `main.go` (mustConnGRPC with 3s connect timeout only, no per-call timeouts), `go.mod` (no circuit breaker libraries)

### STATE-Q5: Rate Limiting and Throttling

- **Severity**: RISK
- **Finding**: No rate limiting middleware, throttling configuration, or API Gateway throttle settings found. The gRPC server accepts unlimited concurrent connections. No `grpc.MaxConcurrentStreams`, `grpc.ConnectionTimeout`, or equivalent server options configured. No WAF or API Gateway sits in front of this service within this repository's scope.
- **Gap**: A runaway agent loop could call PlaceOrder at machine speed, creating unlimited orders and charges.
- **Compensating Controls**:
  - Add `grpc.MaxConcurrentStreams` server option to limit concurrent requests
  - Implement rate limiting at the service mesh / API gateway layer
- **Remediation Timeline**: 30 days
- **Recommendation**: Add gRPC server options for concurrency limits and implement per-identity rate limiting at the gateway or service mesh.
- **Evidence**: `main.go` (grpc.NewServer with no rate limiting options)

### STATE-Q6: Blast Radius and Transaction Limits

- **Severity**: RISK
- **Finding**: No configurable transaction limits found. No max-orders-per-hour, max-spend-per-session, max-charge-amount, or similar blast radius controls. The `chargeCard` function passes the full calculated amount to the payment service without any ceiling or guard.
- **Gap**: No transaction limits. An agent error could create unlimited orders with unlimited charges.
- **Compensating Controls**:
  - Implement transaction limits at the payment service level (max charge amount per transaction)
  - Add per-agent-identity transaction limits at the gateway
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add configurable transaction limits: max orders per hour per user_id, max charge amount per transaction, and max total spend per session.
- **Evidence**: `main.go` (chargeCard with no amount ceiling), absence of any limit configuration

### STATE-Q7: Infrastructure Capacity for Agent Traffic

- **Severity**: RISK
- **Finding**: No load test results, auto-scaling policies, or capacity planning documentation found. The `Dockerfile` produces a single static binary with no scaling configuration. No Kubernetes HPA, no resource limits in container specs, no load testing frameworks in the repository.
- **Gap**: Unknown capacity. The service has not been tested for the bursty, exploratory traffic patterns agents generate.
- **Compensating Controls**:
  - Deploy with Kubernetes HPA based on CPU/memory metrics
  - Run load tests simulating agent traffic patterns before enabling agent access
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Conduct load testing simulating agent traffic patterns (burst, retry, fan-out). Configure Kubernetes HPA with appropriate scaling thresholds.
- **Evidence**: `Dockerfile` (single binary, EXPOSE 5050), absence of any capacity configuration

### HITL-Q1: Draft/Pending State

- **Severity**: RISK
- **Finding**: `PlaceOrder` executes immediately — there is no draft, pending, or provisional state. When called, it charges the card, ships the order, empties the cart, and sends confirmation in one synchronous call. No two-step commit pattern (create-then-confirm). No "preview order" capability.
- **Gap**: No draft/pending state for agent-proposed orders. An agent calling PlaceOrder immediately triggers an irreversible financial transaction.
- **Compensating Controls**:
  - Implement a `PreviewOrder` RPC that returns pricing and shipping without executing the checkout
  - Add a human approval gate at the agent orchestration layer before calling PlaceOrder
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Split PlaceOrder into two phases: `CreateDraftOrder` (returns preview) and `ConfirmOrder` (executes the checkout).
- **Evidence**: `main.go` (PlaceOrder — immediate execution, no draft state)

### HITL-Q2: Configurable Approval Gates

- **Severity**: RISK
- **Finding**: No configurable approval gates exist. There are no approval API endpoints, no status-based workflows requiring explicit confirmation, no configurable operation-level flags, and no Step Functions with human approval tasks. PlaceOrder executes without any human approval step.
- **Gap**: No application-level human approval gate for high-risk operations like payment processing.
- **Compensating Controls**:
  - Implement human-in-the-loop gates at the agent orchestration layer (not in this service)
  - Add a confirmation step to the PlaceOrder workflow that requires explicit approval for orders above a threshold
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add configurable approval gates — e.g., orders above a configurable threshold require human confirmation before `chargeCard` is called.
- **Evidence**: `main.go` (PlaceOrder — no approval step), absence of any approval workflow configuration

### HITL-Q3: Sandbox/Staging Environment

- **Severity**: RISK
- **Finding**: No sandbox or staging environment configuration found. No `docker-compose.yml` for local testing (only `Dockerfile`). No seed data scripts, no synthetic data generators, no environment-specific configuration files. The `Dockerfile` is a production build only.
- **Gap**: No sandbox environment for agent testing. The first time an agent bug is discovered would be in production.
- **Compensating Controls**:
  - Create a docker-compose configuration that spins up mock versions of all 6 downstream services
  - Use the existing Dockerfile with environment variables pointing to mock services
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a `docker-compose.yml` with mock downstream services and seed data for agent testing. Add staging environment IaC.
- **Evidence**: `Dockerfile` (production-only build), absence of docker-compose, staging config, or seed data

### DATA-Q2: Data Residency and Sovereignty ⚡

- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: No data residency documentation found. The service connects to 6 downstream services via environment variable addresses with no evidence of region constraints or data sovereignty controls. The protobuf definitions carry credit card data and PII (address, email) with no region or jurisdiction metadata. No GDPR, LGPD, or HIPAA compliance references anywhere.
- **Gap**: Unknown data residency posture. If downstream services are in different regions, PCI/PII data may transit jurisdictional boundaries.
- **Compensating Controls**:
  - Document the deployment topology and confirm all services are in the same region/jurisdiction
  - Add data residency metadata to the deployment configuration
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document data residency requirements. Verify all downstream services are in the same AWS region. Add region constraints to deployment manifests.
- **Evidence**: `main.go` (env var-based service addressing with no region constraints), absence of any data residency documentation

### DATA-Q3: Selective Query Support

- **Severity**: RISK
- **Finding**: The single `PlaceOrder` RPC takes a complete `PlaceOrderRequest` and returns a complete `PlaceOrderResponse` containing the full `OrderResult`. No pagination, filtering, sorting, or field selection is available. The response includes all order items, shipping details, and addresses — the caller cannot request a subset.
- **Gap**: No selective query support. An agent cannot request partial data or limit response size.
- **Compensating Controls**:
  - Since the response size is bounded by cart size (typically small), this is a low-impact risk for the checkout service specifically
  - For querying order history (if added), implement pagination from the start
- **Remediation Timeline**: 60–90 days (low priority for this service)
- **Recommendation**: If read endpoints are added (STATE-Q2), implement pagination and field selection from the start.
- **Evidence**: `genproto/demo.pb.go` (PlaceOrderRequest, PlaceOrderResponse — no pagination fields)

### DATA-Q4: System of Record Designations

- **Severity**: RISK
- **Finding**: No system-of-record designations found. The checkout service orchestrates across 6 downstream services (cart, product catalog, currency, payment, shipping, email) but has no golden record pattern. The `OrderResult` is assembled in-memory from multiple service responses and returned to the caller — but it is not persisted. There is no order database in this service.
- **Gap**: No system of record for orders. The OrderResult exists only in the gRPC response — if the caller loses it, there is no way to retrieve the order.
- **Compensating Controls**:
  - Designate one service as the order system of record and persist OrderResult
  - Agent should persist the OrderResult response for its own records
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add order persistence to the checkout service or designate an order management service as the system of record.
- **Evidence**: `main.go` (OrderResult assembled but not persisted), absence of any database or persistence configuration

### DATA-Q5: Reliable Timestamps

- **Severity**: RISK
- **Finding**: The `OrderResult` protobuf message has no timestamp fields — no `created_at`, `updated_at`, or `event_time`. The `order_id` is a UUID (`uuid.NewUUID()` in `main.go`) which is a v1 UUID containing an embedded timestamp, but this is not a reliable or explicit timestamp field. Application logs use RFC3339Nano timestamps (configured in logrus), but these are not part of the API response.
- **Gap**: No timestamps in the API response. An agent cannot determine when an order was placed from the response data alone.
- **Compensating Controls**:
  - Agent can record its own timestamp when receiving the response
  - Add `created_at` timestamp field to the OrderResult protobuf
- **Remediation Timeline**: 30 days
- **Recommendation**: Add a `google.protobuf.Timestamp created_at` field to the `OrderResult` message in the protobuf schema.
- **Evidence**: `genproto/demo.pb.go` (OrderResult — no timestamp fields), `main.go` (uuid.NewUUID for order_id)

### DATA-Q6: Data Freshness Signaling

- **Severity**: RISK
- **Finding**: No data freshness signaling found. No `Cache-Control` headers, no `X-Data-Age` headers, no `last_refreshed` fields, no `consistency_level` indicators. The PlaceOrder response is generated in real-time from live downstream calls, but there is no signal to the caller indicating this.
- **Gap**: No freshness metadata. An agent cannot distinguish live data from cached or stale data.
- **Compensating Controls**:
  - For PlaceOrder specifically, the response is always live (generated from real-time downstream calls), so staleness is low risk
  - If read endpoints are added, include freshness metadata from the start
- **Remediation Timeline**: 30–60 days (low priority for write-only service)
- **Recommendation**: Add response metadata indicating data freshness when read endpoints are implemented.
- **Evidence**: `main.go` (real-time downstream calls, no freshness metadata in responses)

### DATA-Q7: PII Redaction in Logs

- **Severity**: RISK
- **Finding**: PII is logged directly in `main.go`: `log.Infof("[PlaceOrder] user_id=%q user_currency=%q", req.UserId, req.UserCurrency)` logs the user_id. `log.Infof("order confirmation email sent to %q", req.Email)` logs the email address in plaintext. `log.Warnf("failed to send order confirmation to %q: %+v", req.Email, err)` also logs the email. The service config is logged with `log.Infof("service config: %+v", svc)` which includes all downstream service addresses. No PII masking libraries, log scrubbing middleware, or redaction filters found.
- **Gap**: PII (email, user_id) is logged in plaintext. If logs are forwarded to LLM prompt/response pairs or external systems, this is a compliance violation.
- **Compensating Controls**:
  - Add a logrus hook that redacts email addresses and sensitive fields before writing
  - Configure log aggregation to apply PII filters on ingestion
- **Remediation Timeline**: 30 days
- **Recommendation**: Implement a logrus hook for PII redaction. Replace `req.Email` in log statements with a masked version (e.g., `u***@example.com`). Remove user_id from debug logs or hash it.
- **Evidence**: `main.go` (PlaceOrder log statements with user_id and email)

### DISC-Q1: Schema Documentation and Versioning

- **Severity**: RISK
- **Finding**: The protobuf schema exists as generated Go code (`genproto/demo.pb.go`) and is auto-generated from `demo.proto` via `genproto.sh`. The protobuf itself provides typed schema documentation with field names, types, and numbers. However, the source `.proto` file is not in this repository (referenced as `../../protos/demo.proto`). No formal schema versioning, changelog, or schema registry is present. No `buf.yaml` or `buf.lock` for schema management.
- **Gap**: Schema is auto-generated but not versioned. Source proto is not co-located. No breaking change detection.
- **Compensating Controls**:
  - Co-locate the `.proto` file or add a git submodule reference
  - Add `buf` for schema linting and breaking change detection
- **Remediation Timeline**: 30 days
- **Recommendation**: Co-locate the `.proto` file, add `buf.yaml` for schema management, and implement breaking change detection in CI.
- **Evidence**: `genproto.sh` (references ../../protos/demo.proto), `genproto/demo.pb.go` (generated schema)

### OBS-Q1: Distributed Tracing and Structured Logging

- **Severity**: RISK
- **Finding**: OpenTelemetry tracing is implemented: OTLP trace exporter via `otlptracegrpc`, trace context propagation configured (`propagation.TraceContext`, `propagation.Baggage`), gRPC server and all clients use `otelgrpc` handlers for automatic span creation. Logging uses logrus with JSON formatter and RFC3339Nano timestamps. However, no `trace_id`, `span_id`, or `correlation_id` fields are logged alongside application log messages — tracing and logging are not correlated. An operator seeing a log entry cannot link it to a trace without external tooling.
- **Gap**: Tracing and logging are independently implemented but not correlated. Cannot link a log entry to a distributed trace.
- **Compensating Controls**:
  - Use a logrus hook that extracts trace_id/span_id from the context and adds them to every log entry
  - Correlate traces and logs in the observability backend (e.g., Grafana Tempo + Loki)
- **Remediation Timeline**: 7–14 days
- **Recommendation**: Add an OpenTelemetry logrus hook that injects `trace_id` and `span_id` into every log entry from the request context.
- **Evidence**: `main.go` (OpenTelemetry setup, otelgrpc handlers, logrus JSON logging without trace correlation), `go.mod` (OpenTelemetry dependencies present)

### OBS-Q2: Alerting on Error Rates and Latency

- **Severity**: RISK
- **Finding**: No alerting thresholds configured. No CloudWatch alarms, no anomaly detection, no PagerDuty/OpsGenie integration, no SLO-based alerting found in the repository. No alerting configuration files. OpenTelemetry traces are exported but no alerting rules are defined on them.
- **Gap**: No proactive alerting. If PlaceOrder starts failing or latency increases, there is no automated detection.
- **Compensating Controls**:
  - Configure alerting in the observability backend (e.g., Grafana alerts on OTLP metrics)
  - Add CloudWatch alarms on container-level metrics if deployed on ECS/EKS
- **Remediation Timeline**: 30 days
- **Recommendation**: Define SLOs for PlaceOrder (e.g., 99% success rate, P95 latency < 5s) and configure alerts when SLOs are breached.
- **Evidence**: Absence of any alerting configuration in the repository

### ENG-Q1: Infrastructure Governance for Agent-Facing Surface

- **Severity**: RISK
- **Finding**: No IaC files found in this repository. No Terraform, CloudFormation, CDK, Helm, or Kustomize definitions for API gateways, IAM roles, secrets, or networking. The infrastructure that exposes this service to callers is not defined within this service's scope.
- **Gap**: The agent-facing integration surface (network ingress, IAM, secrets) is not defined as code in this repository. No peer review on infrastructure changes. No drift detection.
- **Compensating Controls**:
  - Infrastructure may be defined in a separate repository (common in microservice architectures) — verify and document the location
  - Add a reference to the infrastructure repository in this service's README
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Co-locate Kubernetes manifests (Deployment, Service, NetworkPolicy) with this service, or document the infrastructure repository location. Implement drift detection.
- **Evidence**: Absence of any IaC files in the repository

### ENG-Q2: CI/CD with API Contract Testing

- **Severity**: RISK
- **Finding**: No CI/CD pipeline definitions found. No GitHub Actions workflows, GitLab CI configuration, Jenkins files, or CodeBuild buildspec. No API contract tests, no consumer-driven contract testing (Pact), no OpenAPI spec validation, no `buf breaking` checks.
- **Gap**: No CI/CD pipeline. No automated detection of API-breaking changes before they reach production.
- **Compensating Controls**:
  - CI/CD may be defined in a parent repository or platform-level config — verify and document
  - Add a `.github/workflows/` or equivalent pipeline with protobuf breaking change detection
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement a CI/CD pipeline with `buf breaking` checks on protobuf changes, unit tests, and integration tests.
- **Evidence**: Absence of any CI/CD configuration files in the repository

### ENG-Q3: Rollback Capability

- **Severity**: RISK
- **Finding**: No rollback capability configured within this repository. No blue/green deployment config, no CodeDeploy rollback triggers, no Helm rollback, no feature flags, no canary deployment configuration. The `Dockerfile` builds a single binary with no rollback mechanism.
- **Gap**: No documented rollback capability. If a deployment breaks agent-facing APIs, there is no defined fast-rollback procedure.
- **Compensating Controls**:
  - Use Kubernetes rolling update with `maxUnavailable: 0` for zero-downtime deploys
  - Maintain previous container image tags for manual rollback
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement Kubernetes rollback (or equivalent) with automated health checks. Target rollback within 15 minutes.
- **Evidence**: `Dockerfile` (single build stage, no rollback mechanism), absence of deployment configuration

### ENG-Q4: API Test Coverage

- **Severity**: RISK
- **Finding**: The only test file is `money/money_test.go`, which tests currency arithmetic functions (IsValid, IsZero, IsPositive, IsNegative, AreSameCurrency, AreEquals, Negate, Must, Sum). These are unit tests for the money utility package. No tests exist for the `PlaceOrder` RPC, no gRPC integration tests, no contract tests, no end-to-end tests. The PlaceOrder handler — the only agent-facing API — has zero test coverage.
- **Gap**: Zero API test coverage for PlaceOrder. Input validation, error handling, and edge cases are untested.
- **Compensating Controls**:
  - Add gRPC integration tests using mock downstream service clients
  - Add contract tests validating PlaceOrder request/response schema
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement gRPC integration tests for PlaceOrder using mock clients. Test error paths (downstream failures, invalid inputs, concurrent calls).
- **Evidence**: `money/money_test.go` (only test file — tests currency arithmetic, not API), `main.go` (PlaceOrder handler — untested)

### ENG-Q5: Encryption at Rest for Agent-Accessible Data

- **Severity**: RISK
- **Finding**: No encryption at rest configuration found. No KMS key references, no `kms_key_id` on any resources, no encryption configuration in IaC (no IaC exists). The service is stateless (no local database), but it processes PCI-sensitive credit card data and PII in memory and passes it to downstream services.
- **Gap**: No encryption at rest configuration. While the service is stateless, the downstream services it calls (payment, cart) may store data — and this service has no visibility into their encryption posture.
- **Compensating Controls**:
  - Verify encryption at rest is configured on downstream services (payment service, cart service data stores)
  - Enable encryption by default on any future data stores added to this service
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document encryption at rest requirements. Verify downstream service data stores are encrypted. Add KMS-based encryption if this service adds local persistence.
- **Evidence**: Absence of any encryption configuration, `main.go` (stateless service processing PCI data)

---

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO
- **Finding**: CheckoutService exposes a documented gRPC interface via protobuf. The service definition `hipstershop.CheckoutService` has one RPC: `PlaceOrder(PlaceOrderRequest) returns (PlaceOrderResponse)`. This is a stable, typed, machine-readable interface — NOT direct database access, file-based exchange, or UI automation. The protobuf schema fully defines request/response types with field names, types, and numbers.
- **Implication**: The gRPC interface satisfies the minimum viable integration surface requirement. Agent tools can be built against the protobuf definition. However, gRPC requires a gRPC client — REST-based agent frameworks would need a gRPC-to-REST gateway (grpc-gateway or Envoy transcoding).
- **Recommendation**: Consider adding a gRPC-REST transcoding layer (e.g., grpc-gateway or Envoy gRPC-JSON transcoder) to make the API accessible to REST-based agent frameworks.
- **Evidence**: `genproto/demo_grpc.pb.go` (CheckoutService definition, PlaceOrder RPC), `genproto/demo.pb.go` (PlaceOrderRequest, PlaceOrderResponse types)

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: PlaceOrder is a write operation that charges a credit card, ships an order, and empties a cart. No idempotency key support was found — no idempotency middleware, no duplicate check on order UUID, no idempotency key header or request field. The `orderID` is generated with `uuid.NewUUID()` on every call — each call creates a new unique order regardless of identical inputs. Two identical PlaceOrder calls will create two separate orders with two separate charges.
- **Implication**: For read-only agent scope, this is informational only. If the agent scope is elevated to write-enabled in the future, this becomes a BLOCKER — agents retry on failure, and duplicate PlaceOrder calls would create duplicate charges.
- **Recommendation**: Add an `idempotency_key` field to `PlaceOrderRequest` and implement server-side deduplication before elevating to write-enabled agent scope.
- **Evidence**: `main.go` (uuid.NewUUID for each order, no duplicate check), `genproto/demo.pb.go` (PlaceOrderRequest — no idempotency_key field)

### API-Q6: Structured Response Format

- **Severity**: INFO
- **Finding**: gRPC uses Protocol Buffers (binary format) for serialization. The `PlaceOrderResponse` contains an `OrderResult` with strongly typed fields: `order_id` (string), `shipping_tracking_id` (string), `shipping_cost` (Money), `shipping_address` (Address), `items` (repeated OrderItem). This is well-structured, strongly typed, and machine-readable.
- **Implication**: Protobuf binary format is not directly consumable by LLMs without conversion to text/JSON. Agent tooling will need to deserialize protobuf responses into JSON or text for LLM reasoning. gRPC-JSON transcoding (Envoy) or `protojson` marshaling can convert automatically.
- **Recommendation**: If agents consume this API, add JSON transcoding via Envoy or grpc-gateway, or ensure agent tooling handles protobuf deserialization.
- **Evidence**: `genproto/demo.pb.go` (PlaceOrderResponse, OrderResult message types — protobuf binary format)

### API-Q8: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: No event emission found. The checkout service does not publish events to SNS, EventBridge, SQS, Kafka, or any webhook endpoint. When an order is placed, the only notification is the email sent via the email service. State changes (order created, payment charged, shipment initiated) are not published as events.
- **Implication**: Agents cannot reactively respond to checkout events (e.g., "order placed" → trigger fulfillment workflow). All agent interaction must be request-driven (pull) rather than event-driven (push). This limits proactive agent architectures.
- **Recommendation**: Add event emission for key state changes (order_placed, payment_charged, shipment_initiated) to an event bus (EventBridge or SNS) for future event-driven agent integration.
- **Evidence**: `main.go` (no event publishing, only email notification via gRPC)

### API-Q9: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limit documentation or rate limit response headers found. No `X-RateLimit-Remaining`, `Retry-After`, or equivalent gRPC metadata in the server code. No API Gateway usage plan or WAF rate rules.
- **Implication**: Agents cannot self-throttle based on server-side rate limits. If rate limiting is added (STATE-Q5), rate limit metadata should be included in gRPC response trailers.
- **Recommendation**: When implementing rate limiting, include rate limit metadata in gRPC trailing metadata (equivalent to HTTP rate limit headers).
- **Evidence**: `main.go` (no rate limit metadata in responses), absence of API Gateway configuration

### API-Q10: API Latency Profile

- **Severity**: INFO
- **Finding**: No latency benchmarks, load test results, APM dashboards, or performance documentation found. PlaceOrder makes 6+ sequential downstream gRPC calls (cart, N×product, N×currency, shipping, payment, cart empty, email). Expected latency is the sum of all downstream call latencies — likely 1–5 seconds under normal conditions, potentially longer for large carts.
- **Implication**: Sequential downstream calls mean latency scales linearly with cart size. Agents should account for 5–10 second response times. For large carts, async patterns (API-Q7) become necessary.
- **Recommendation**: Instrument PlaceOrder latency metrics using OpenTelemetry. Establish P50/P95/P99 baselines. Consider parallelizing independent downstream calls (e.g., product lookups).
- **Evidence**: `main.go` (sequential downstream calls — getUserCart, prepOrderItems, quoteShipping, chargeCard, shipOrder)

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Field names are semantically meaningful and follow consistent snake_case convention: `user_id`, `product_id`, `currency_code`, `street_address`, `credit_card_number`, `order_id`, `shipping_tracking_id`, `shipping_cost`, `credit_card_expiration_year`. No legacy abbreviations or cryptic codes requiring a data dictionary.
- **Implication**: Good naming conventions facilitate agent reasoning. LLMs can interpret field names without additional context or lookup tables.
- **Recommendation**: Maintain current naming conventions. Consider adding protobuf field comments for complex fields.
- **Evidence**: `genproto/demo.pb.go` (all message type field definitions — consistent, readable naming)

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No data catalog or metadata layer found. No AWS Glue Data Catalog, Collibra, Alation, DataHub, or equivalent. No metadata files or data dictionary documents. The protobuf schema itself serves as a lightweight schema catalog.
- **Implication**: Agent tool builders must read the protobuf schema directly to understand data structures. No centralized discovery mechanism for what data the checkout service holds or processes.
- **Recommendation**: Register the protobuf schema in a schema registry (e.g., Buf Schema Registry, Confluent Schema Registry) for centralized discovery.
- **Evidence**: Absence of any data catalog or metadata layer in the repository

### DISC-Q4: Data Lineage

- **Severity**: INFO
- **Finding**: No data lineage tooling found. No AWS Glue DataBrew, Apache Atlas, or equivalent. No ETL pipeline documentation or data flow diagrams. The code in `main.go` shows the data flow (cart → products → currency → payment → shipping → email) but this is not formally documented as lineage.
- **Implication**: When an agent produces incorrect output due to bad data, lineage tracing depends on reading source code and distributed traces rather than a formal lineage system.
- **Recommendation**: Document the data flow through the checkout orchestration as a formal data lineage diagram. OpenTelemetry traces provide implicit lineage — leverage this.
- **Evidence**: `main.go` (data flow visible in PlaceOrder: getUserCart → prepOrderItems → quoteShipping → chargeCard → shipOrder)

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No business outcome metrics found. No `cloudwatch.put_metric_data`, no custom dashboards, no business KPI tracking. Application logs capture operational events (order placed, email sent) but these are not published as metrics.
- **Implication**: When agents consume this service, there are no business metrics to determine whether agent interactions produce good outcomes (e.g., order completion rate, average order value, checkout abandonment).
- **Recommendation**: Publish custom metrics for: orders_placed (counter), order_total_amount (histogram), checkout_duration (histogram), payment_failures (counter).
- **Evidence**: `main.go` (log statements only, no metric publication), `go.mod` (no metrics-specific libraries beyond OpenTelemetry)

### DATA-Q8: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality metrics, profiling reports, null rate monitoring, duplicate detection, or data freshness SLAs found. The service assembles order data from 6 downstream services but does not validate data quality (e.g., does not check if product prices are null, if cart is empty, if currency conversion returned valid amounts).
- **Implication**: Agents acting on incomplete or low-quality data from downstream services would propagate errors silently. The checkout service trusts all downstream data without validation.
- **Recommendation**: Add input validation in PlaceOrder: check for empty cart, validate currency codes, verify product prices are positive. Publish data quality metrics for downstream responses.
- **Evidence**: `main.go` (no input validation beyond what gRPC/protobuf enforces), absence of any data quality tooling

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: CheckoutService exposes a documented gRPC interface via protobuf (`hipstershop.CheckoutService/PlaceOrder`). This is a stable, typed, machine-readable interface — not direct DB access or UI automation.
- **Gap**: gRPC requires a gRPC client; REST-based agent frameworks need a transcoding layer.
- **Recommendation**: Add gRPC-REST transcoding via Envoy or grpc-gateway.
- **Evidence**: `genproto/demo_grpc.pb.go`, `genproto/demo.pb.go`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK
- **Finding**: Protobuf is machine-readable and auto-generated from `demo.proto` via `genproto.sh`. No OpenAPI, AsyncAPI, or Smithy spec exists. Source `.proto` is not co-located (referenced as `../../protos/demo.proto`).
- **Gap**: No standalone API spec for agent tool generation. No gRPC reflection enabled.
- **Recommendation**: Enable gRPC server reflection and co-locate the `.proto` file.
- **Evidence**: `genproto.sh`, `genproto/demo_grpc.pb.go`

#### API-Q3: Structured Error Responses
- **Severity**: RISK
- **Finding**: Uses gRPC status codes (`codes.Internal`, `codes.Unavailable`) but error messages embed raw Go error strings. No structured error bodies with retryable flags.
- **Gap**: Agents cannot distinguish retryable from terminal errors.
- **Recommendation**: Add gRPC rich error details (`errdetails.ErrorInfo`) to all responses.
- **Evidence**: `main.go`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No idempotency key support. `uuid.NewUUID()` generates a unique order_id per call. Duplicate calls create duplicate orders and charges.
- **Gap**: Non-idempotent write operation. Becomes BLOCKER if agent_scope is elevated to write-enabled.
- **Recommendation**: Add `idempotency_key` field to `PlaceOrderRequest`.
- **Evidence**: `main.go`, `genproto/demo.pb.go`

#### API-Q5: API Versioning and Deprecation
- **Severity**: RISK
- **Finding**: Package `hipstershop` with no version prefix. No changelog or deprecation policy.
- **Gap**: No versioning strategy. Breaking schema changes silently break agent tools.
- **Recommendation**: Adopt `hipstershop.v1` package versioning and `buf breaking` checks.
- **Evidence**: `genproto/demo_grpc.pb.go`, `README.md`

#### API-Q6: Structured Response Format
- **Severity**: INFO
- **Finding**: gRPC/Protobuf binary format. Strongly typed with well-defined message structures.
- **Gap**: Not directly consumable by LLMs without JSON conversion.
- **Recommendation**: Add JSON transcoding via Envoy or grpc-gateway.
- **Evidence**: `genproto/demo.pb.go`

#### API-Q7: Asynchronous Operation Support
- **Severity**: RISK
- **Finding**: PlaceOrder is synchronous with 6+ sequential downstream calls. No async/polling/webhook patterns.
- **Gap**: Long-running synchronous operation risks agent timeouts.
- **Recommendation**: Implement async pattern with `GetOrderStatus` polling RPC.
- **Evidence**: `main.go`

#### API-Q8: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: No event emission. No SNS, EventBridge, SQS, Kafka, or webhook integration.
- **Gap**: Agents cannot reactively respond to checkout events.
- **Recommendation**: Add event emission for order_placed, payment_charged, shipment_initiated.
- **Evidence**: `main.go`

#### API-Q9: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit documentation or response headers. No API Gateway throttle settings.
- **Gap**: Agents cannot self-throttle.
- **Recommendation**: Include rate limit metadata in gRPC trailing metadata when rate limiting is implemented.
- **Evidence**: `main.go`

#### API-Q10: API Latency Profile
- **Severity**: INFO
- **Finding**: No latency benchmarks or load test results. Expected 1–5s P95 for small carts based on sequential downstream calls.
- **Gap**: No performance baseline.
- **Recommendation**: Instrument P50/P95/P99 metrics. Consider parallelizing independent downstream calls.
- **Evidence**: `main.go`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: gRPC server created with `grpc.NewServer()` — no TLS, no auth interceptors, no mTLS. Uses `insecure.NewCredentials()`. No mechanism to authenticate calling principal.
- **Gap**: No machine identity authentication. Any network-reachable client can invoke PlaceOrder.
- **Recommendation**: Add gRPC auth interceptor with mTLS or OAuth2 bearer token validation.
- **Evidence**: `main.go`, `go.mod`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK
- **Finding**: No IAM policies, RBAC, or scoped permission model. Any caller has full PlaceOrder access.
- **Gap**: Cannot restrict agent to specific operations or resources.
- **Recommendation**: Implement gRPC authorization interceptor or service mesh AuthorizationPolicy.
- **Evidence**: `main.go`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK
- **Finding**: Single RPC (PlaceOrder) with no permission checks. No read vs write distinction.
- **Gap**: Cannot enforce action-level authorization.
- **Recommendation**: Add per-method authorization checks in gRPC interceptor.
- **Evidence**: `main.go`

#### AUTH-Q4: Identity Propagation
- **Severity**: RISK
- **Finding**: `user_id` is a request parameter, not an authenticated identity. No JWT parsing or token exchange. Caller can supply any user_id.
- **Gap**: No identity propagation. System trusts caller-supplied user_id without verification.
- **Recommendation**: Implement JWT-based identity propagation; extract user_id from verified tokens.
- **Evidence**: `main.go`, `genproto/demo.pb.go`

#### AUTH-Q5: Agent-as-Self vs Agent-on-Behalf-of-User
- **Severity**: RISK
- **Finding**: No distinction between agent-as-self and agent-on-behalf-of-user. No authentication exists.
- **Gap**: Cannot differentiate access patterns.
- **Recommendation**: Design auth system with both modes from the start.
- **Evidence**: `main.go`

#### AUTH-Q6: Credential Management
- **Severity**: RISK
- **Finding**: Service addresses via env vars. No hardcoded credentials. No Secrets Manager or Vault integration.
- **Gap**: No secrets management infrastructure for future credential needs.
- **Recommendation**: Integrate AWS Secrets Manager or Vault for credential lifecycle management.
- **Evidence**: `main.go`, `go.mod`

#### AUTH-Q7: Immutable Audit Logging ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: Logrus JSON logging captures user_id and email. These are application logs — not immutable audit logs. No CloudTrail, no immutable storage.
- **Gap**: No immutable audit trail. Logs can be modified or deleted.
- **Recommendation**: Ship logs to immutable storage (S3 with object lock) and add structured audit entries.
- **Evidence**: `main.go`

#### AUTH-Q8: Agent Identity Suspension
- **Severity**: RISK
- **Finding**: No mechanism to suspend or revoke individual agent identities. No authentication system exists.
- **Gap**: Cannot isolate a misbehaving agent without shutting down the service.
- **Recommendation**: Implement per-agent identity management with instant revocation.
- **Evidence**: `main.go`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: Multi-step PlaceOrder workflow with no compensation. If shipOrder fails after chargeCard succeeds, card is charged with no refund. `emptyUserCart` error silently ignored.
- **Gap**: No saga pattern or compensating transactions. Partial failure leaves inconsistent state.
- **Recommendation**: Implement saga pattern with chargeCard reversal on shipOrder failure.
- **Evidence**: `main.go`

#### STATE-Q2: Queryable Current State
- **Severity**: RISK
- **Finding**: Only PlaceOrder RPC (write). No query endpoints for order state or checkout status.
- **Gap**: Write-only orchestrator. Agents cannot inspect state before acting.
- **Recommendation**: Add PreviewOrder and GetOrderStatus RPCs.
- **Evidence**: `genproto/demo_grpc.pb.go`

#### STATE-Q3: Concurrency Controls
- **Severity**: RISK
- **Finding**: No optimistic locking, ETags, or conditional writes. Concurrent PlaceOrder calls for same user_id can create duplicate orders.
- **Gap**: No concurrency controls on checkout workflow.
- **Recommendation**: Add distributed lock on user_id during PlaceOrder.
- **Evidence**: `main.go`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK
- **Finding**: No circuit breakers, per-call timeouts, or retry logic. 3s connect timeout only. Downstream failures cascade.
- **Gap**: No resilience patterns. Service hangs if downstream services fail.
- **Recommendation**: Add per-call timeouts and circuit breakers (`sony/gobreaker`).
- **Evidence**: `main.go`, `go.mod`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK
- **Finding**: No rate limiting. gRPC server accepts unlimited concurrent connections.
- **Gap**: Runaway agent loop could DDoS the service.
- **Recommendation**: Add gRPC concurrency limits and gateway-level rate limiting.
- **Evidence**: `main.go`

#### STATE-Q6: Blast Radius and Transaction Limits
- **Severity**: RISK
- **Finding**: No configurable transaction limits. No max-orders-per-hour or max-charge-amount.
- **Gap**: No blast radius controls. Agent error could create unlimited charges.
- **Recommendation**: Add per-identity transaction limits.
- **Evidence**: `main.go`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: RISK
- **Finding**: No load tests, auto-scaling policies, or capacity documentation.
- **Gap**: Unknown capacity for agent traffic patterns.
- **Recommendation**: Load test with agent-like patterns. Configure Kubernetes HPA.
- **Evidence**: `Dockerfile`

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State
- **Severity**: RISK
- **Finding**: PlaceOrder executes immediately. No draft/pending state. No two-step commit.
- **Gap**: No draft state for agent-proposed orders.
- **Recommendation**: Split into CreateDraftOrder and ConfirmOrder.
- **Evidence**: `main.go`

#### HITL-Q2: Configurable Approval Gates
- **Severity**: RISK
- **Finding**: No approval gates. PlaceOrder executes without human confirmation.
- **Gap**: No application-level approval for high-risk operations.
- **Recommendation**: Add configurable threshold-based approval gates.
- **Evidence**: `main.go`

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK
- **Finding**: No docker-compose, staging config, seed data, or synthetic data generators.
- **Gap**: No sandbox for agent testing.
- **Recommendation**: Create docker-compose with mock downstream services.
- **Evidence**: `Dockerfile`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: CreditCardInfo (card number, CVV, expiration) and email/address are PCI/PII fields with no classification, encryption, or access controls. Credit card data flows to payment service in plaintext.
- **Gap**: Unclassified PCI-DSS and PII data.
- **Recommendation**: Implement tokenization for credit card data. Add field-level classification annotations.
- **Evidence**: `genproto/demo.pb.go`, `main.go`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: No data residency documentation. Service connects to 6 downstream services via env var addresses with no region constraints.
- **Gap**: Unknown data residency posture.
- **Recommendation**: Document deployment topology and verify single-region deployment.
- **Evidence**: `main.go`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK
- **Finding**: Single PlaceOrder RPC with full request/response. No pagination, filtering, or field selection.
- **Gap**: No selective query support.
- **Recommendation**: Implement pagination and field selection on future read endpoints.
- **Evidence**: `genproto/demo.pb.go`

#### DATA-Q4: System of Record Designations
- **Severity**: RISK
- **Finding**: OrderResult assembled in-memory but not persisted. No order database.
- **Gap**: No system of record for orders.
- **Recommendation**: Add order persistence or designate an order management service.
- **Evidence**: `main.go`

#### DATA-Q5: Reliable Timestamps
- **Severity**: RISK
- **Finding**: No timestamp fields on OrderResult. Order_id is a UUID with no explicit temporal data.
- **Gap**: No timestamps in API response.
- **Recommendation**: Add `google.protobuf.Timestamp created_at` to OrderResult.
- **Evidence**: `genproto/demo.pb.go`, `main.go`

#### DATA-Q6: Data Freshness Signaling
- **Severity**: RISK
- **Finding**: No freshness metadata. Response is real-time but no signal to caller.
- **Gap**: No freshness signaling.
- **Recommendation**: Add freshness metadata when read endpoints are implemented.
- **Evidence**: `main.go`

#### DATA-Q7: PII Redaction in Logs
- **Severity**: RISK
- **Finding**: Email and user_id logged in plaintext. No PII masking.
- **Gap**: PII in logs creates compliance risk.
- **Recommendation**: Add logrus PII redaction hook.
- **Evidence**: `main.go`

#### DATA-Q8: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics or input validation beyond protobuf type checks.
- **Gap**: Downstream data quality issues propagate silently.
- **Recommendation**: Add input validation and data quality metrics.
- **Evidence**: `main.go`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Documentation and Versioning
- **Severity**: RISK
- **Finding**: Protobuf schema generated from `demo.proto` but source not co-located. No formal versioning or schema registry.
- **Gap**: No schema versioning or breaking change detection.
- **Recommendation**: Co-locate proto file. Add `buf.yaml` for schema management.
- **Evidence**: `genproto.sh`, `genproto/demo.pb.go`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Field names follow consistent snake_case convention. Semantically meaningful (user_id, product_id, order_id, etc.).
- **Gap**: N/A — naming conventions are good.
- **Recommendation**: Maintain conventions. Add protobuf field comments.
- **Evidence**: `genproto/demo.pb.go`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No data catalog. Protobuf schema serves as lightweight catalog.
- **Gap**: No centralized discovery mechanism.
- **Recommendation**: Register proto in schema registry.
- **Evidence**: Absence of data catalog

#### DISC-Q4: Data Lineage
- **Severity**: INFO
- **Finding**: No formal data lineage. Data flow visible in code but not documented.
- **Gap**: No lineage system for tracing data quality issues.
- **Recommendation**: Document data flow as formal lineage diagram.
- **Evidence**: `main.go`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK
- **Finding**: OpenTelemetry tracing implemented with otelgrpc handlers. Logrus JSON logging. But tracing and logging are not correlated — no trace_id in log entries.
- **Gap**: Cannot link log entries to distributed traces.
- **Recommendation**: Add OpenTelemetry logrus hook for trace_id injection.
- **Evidence**: `main.go`, `go.mod`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK
- **Finding**: No alerting configuration. Traces exported but no alert rules defined.
- **Gap**: No proactive alerting on service degradation.
- **Recommendation**: Define SLOs and configure alerts.
- **Evidence**: Absence of alerting configuration

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No business outcome metrics published. Logs capture events but not as metrics.
- **Gap**: No business KPIs for agent interaction quality.
- **Recommendation**: Publish orders_placed, order_total, checkout_duration metrics.
- **Evidence**: `main.go`, `go.mod`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK
- **Finding**: No IaC in this repository. Infrastructure not defined as code within service scope.
- **Gap**: Agent-facing surface not governed as code.
- **Recommendation**: Co-locate K8s manifests or document infrastructure repo location.
- **Evidence**: Absence of IaC files

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK
- **Finding**: No CI/CD pipeline definitions. No contract tests or breaking change detection.
- **Gap**: No automated API contract validation.
- **Recommendation**: Implement CI/CD with `buf breaking` checks.
- **Evidence**: Absence of CI/CD configuration

#### ENG-Q3: Rollback Capability
- **Severity**: RISK
- **Finding**: No rollback configuration. Single Dockerfile build.
- **Gap**: No fast-rollback procedure.
- **Recommendation**: Implement K8s rollback with automated health checks.
- **Evidence**: `Dockerfile`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK
- **Finding**: Only `money/money_test.go` (currency arithmetic tests). Zero test coverage for PlaceOrder RPC.
- **Gap**: Agent-facing API is untested.
- **Recommendation**: Add gRPC integration tests for PlaceOrder.
- **Evidence**: `money/money_test.go`, `main.go`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: RISK
- **Finding**: No encryption at rest configuration. Service is stateless but processes PCI data.
- **Gap**: No encryption config. Downstream encryption posture unknown.
- **Recommendation**: Verify downstream encryption. Add KMS config if persistence is added.
- **Evidence**: Absence of encryption configuration

#### ENG-Q6: Cross-Origin and Network Policies
- **Severity**: BLOCKER
- **Finding**: No CORS, security groups, firewall rules, or network policies. gRPC server on 0.0.0.0:5050 with insecure credentials. No TLS.
- **Gap**: No network security boundary. Unencrypted communication.
- **Recommendation**: Enable mTLS. Add Kubernetes NetworkPolicy. Document network controls.
- **Evidence**: `main.go`, `Dockerfile`

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `main.go` | API-Q1, API-Q3, API-Q4, API-Q7, API-Q8, API-Q9, API-Q10, AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q6, AUTH-Q7, AUTH-Q8, STATE-Q1, STATE-Q2, STATE-Q3, STATE-Q4, STATE-Q5, STATE-Q6, HITL-Q1, HITL-Q2, DATA-Q1, DATA-Q2, DATA-Q5, DATA-Q6, DATA-Q7, DATA-Q8, DISC-Q4, OBS-Q1, OBS-Q3 |
| `money/money.go` | (Referenced as utility library — no direct question citations) |
| `money/money_test.go` | ENG-Q4 |

### Generated Protobuf
| File | Questions Referenced |
|------|---------------------|
| `genproto/demo.pb.go` | API-Q1, API-Q2, API-Q4, API-Q6, AUTH-Q4, DATA-Q1, DATA-Q3, DATA-Q5, DISC-Q2 |
| `genproto/demo_grpc.pb.go` | API-Q1, API-Q2, API-Q5, STATE-Q2 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `Dockerfile` | ENG-Q3, ENG-Q6, STATE-Q7, HITL-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `go.mod` | AUTH-Q1, AUTH-Q6, STATE-Q4, OBS-Q1, OBS-Q3 |

### Build Scripts
| File | Questions Referenced |
|------|---------------------|
| `genproto.sh` | API-Q2, DISC-Q1 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `.dockerignore` | (Referenced in inventory — no direct question citations) |
| `README.md` | API-Q5 |

### Notable Absences (Absence as Evidence)
| Missing Artifact | Questions Referenced |
|-----------------|---------------------|
| No IaC files (Terraform, CloudFormation, CDK, Helm) | ENG-Q1, ENG-Q5, ENG-Q6, AUTH-Q7 |
| No OpenAPI/AsyncAPI/Smithy spec | API-Q2 |
| No CI/CD pipeline definitions | ENG-Q2 |
| No Kubernetes manifests or network policies | ENG-Q6, ENG-Q1 |
| No secrets management configuration | AUTH-Q6 |
| No audit logging configuration | AUTH-Q7 |
| No alerting configuration | OBS-Q2 |
| No docker-compose or staging configuration | HITL-Q3 |
| No data residency documentation | DATA-Q2 |
| No data catalog or metadata layer | DISC-Q3 |
| No data lineage tooling | DISC-Q4 |
| No load test results or capacity planning | STATE-Q7 |
| No encryption configuration | ENG-Q5 |
