# Agentic Readiness Assessment Report

**Target**: ./services/microservices-demo/src/shippingservice
**Date**: 2026-04-15
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Agent Scope**: read-only
**Priority**: P1
**Tags**: go, grpc, shipping
**Context**: Go gRPC service providing shipping cost estimates and tracking.

---

## Readiness Profile: Not Agent-Integrable

**BLOCKERs**: 3 | **RISKs**: 35 | **INFOs**: 11

Exclude from agent toolset or plan major remediation before re-evaluation. Three or more blockers indicate fundamental gaps in authentication, data classification, and network security that must be addressed before any agent interaction — including pilots — can proceed safely.

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
- **Finding**: The gRPC server is created with `grpc.NewServer()` in `main.go` with no interceptors, no TLS configuration, and no authentication middleware. Any client can connect to port 50051 and invoke `GetQuote` or `ShipOrder` without providing any identity. No service account definitions, no OAuth2 client credentials flow, no API key authentication, and no mTLS configuration exist anywhere in the codebase.
- **Gap**: No machine identity authentication mechanism exists. The service cannot distinguish which agent (or any caller) made a request. There is no principal attribution for audit purposes.
- **Remediation**:
  - **Immediate**: Add a gRPC unary server interceptor that validates a bearer token or API key from gRPC metadata. Use `grpc.UnaryInterceptor()` server option to register it. At minimum, require an API key in the `authorization` metadata field and validate it against a known set of keys.
  - **Target State**: mTLS or OAuth2 client credentials authentication with per-caller principal attribution. Each agent identity has a unique credential that is logged with every request.
  - **Estimated Effort**: Medium (2–4 weeks for mTLS; 1–2 weeks for API key interceptor)
  - **Dependencies**: ENG-Q6 (network policies must also be addressed to secure the transport layer)
- **Evidence**: `main.go` (lines 73–85: `grpc.NewServer()` with no options)

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: The protobuf message `Address` in `genproto/demo.pb.go` (line 917) includes PII fields: `street_address`, `city`, `state`, `country`, `zip_code`. The `ShipOrderRequest` and `GetQuoteRequest` both accept `Address` as a required field. The broader shared proto definition (generated from `../../protos/demo.proto`) also includes `CreditCardInfo` (credit_card_number, credit_card_cvv, credit_card_expiration_year/month) and email fields, though this service only processes Address data. No data classification tags, field-level encryption, or access controls exist on any of these fields.
- **Gap**: PII (shipping addresses) is processed without classification or field-level access controls. An agent calling `GetQuote` or `ShipOrder` must submit address data with no mechanism to restrict which agents can access which address fields.
- **Remediation**:
  - **Immediate**: Document a data classification policy that tags `Address` fields as PII. Add proto field-level annotations or comments classifying sensitivity. Implement field-level access controls in a gRPC interceptor that masks or redacts address fields based on the caller's permissions.
  - **Target State**: All PII fields classified and tagged at the schema level. Field-level access controls enforced per caller identity. Integration with AWS Macie or equivalent for ongoing PII detection.
  - **Estimated Effort**: Medium (2–4 weeks for classification and basic controls)
  - **Dependencies**: AUTH-Q1 (cannot enforce field-level access controls without knowing who is calling)
- **Evidence**: `genproto/demo.pb.go` (lines 917–927: Address struct with PII fields), `main.go` (lines 107–114: ShipOrder uses `in.Address.StreetAddress`, `in.Address.City`, `in.Address.State`)

### ENG-Q6: Cross-Origin and Network Policies

- **Severity**: BLOCKER
- **Finding**: The gRPC server in `main.go` listens on port 50051 (`net.Listen("tcp", port)`) with no TLS configuration, no network restrictions, and no firewall rules. The `Dockerfile` exposes port 50051 (`EXPOSE 50051`) with no security constraints. No security group rules, no Kubernetes NetworkPolicy, no API Gateway access policies, no WAF rules, and no service mesh configuration exist in the repository. The server accepts plaintext gRPC connections from any source.
- **Gap**: No network security controls are documented or defined. The service is completely open to any network client. No TLS means traffic is transmitted in plaintext, including PII (addresses).
- **Remediation**:
  - **Immediate**: Add TLS to the gRPC server using `grpc.Creds(credentials.NewTLS(tlsConfig))`. Define Kubernetes NetworkPolicy or security group rules that restrict inbound traffic to known callers only.
  - **Target State**: mTLS between all service-to-service calls. Network policies defined as IaC (Terraform/CloudFormation) restricting port 50051 to authorized CIDR ranges or service mesh peers only. All policies subject to peer review and drift detection.
  - **Estimated Effort**: Medium (1–2 weeks for TLS; 2–4 weeks for full network policy IaC)
  - **Dependencies**: AUTH-Q1 (mTLS solves both authentication and transport security simultaneously)
- **Evidence**: `main.go` (line 75: `net.Listen("tcp", port)` — no TLS), `Dockerfile` (line 33: `EXPOSE 50051` — no security constraints)

## RISKs — Proceed with Compensating Controls

### API-Q2: Machine-Readable API Specification

- **Severity**: RISK
- **Finding**: The protobuf generated code (`genproto/demo.pb.go`, `genproto/demo_grpc.pb.go`) defines the schema for `ShippingService` with `GetQuote` and `ShipOrder` RPCs. gRPC reflection is enabled in `main.go` via `reflection.Register(srv)`, allowing runtime schema discovery. However, the source `.proto` file is not in this repository — it is referenced as `../../protos/demo.proto` in `genproto.sh`. No OpenAPI or standalone machine-readable spec exists in the repo.
- **Gap**: The source proto definition is external to this repository. While generated code and gRPC reflection provide runtime discoverability, agent tool authors must access a separate repository to obtain the canonical `.proto` file.
- **Compensating Controls**:
  - Use gRPC reflection at runtime to discover the service schema dynamically.
  - Copy the relevant `.proto` file into this repository as a versioned artifact.
- **Remediation Timeline**: 1–2 weeks
- **Recommendation**: Include the `demo.proto` file (or the shipping-specific subset) in this repository. Add a CI step that validates generated code matches the proto source.
- **Evidence**: `genproto.sh` (references `../../protos/demo.proto`), `main.go` (line 91: `reflection.Register(srv)`), `genproto/demo_grpc.pb.go` (ShippingService definition)

### API-Q3: Structured Error Responses

- **Severity**: RISK
- **Finding**: The gRPC framework provides structured error codes via the `codes` and `status` packages (imported in `main.go`). The `Watch` health check method uses `status.Errorf(codes.Unimplemented, ...)`. However, the core business RPCs `GetQuote` and `ShipOrder` never return errors — they always succeed. No custom error types exist, no retryable/non-retryable classification, and no structured error bodies beyond the standard gRPC status code.
- **Gap**: No error classification for agent consumption. When errors do occur (e.g., nil address pointer), the service will panic rather than return a structured error. Agents cannot distinguish retriable from terminal errors.
- **Compensating Controls**:
  - Agents can rely on gRPC status codes for basic error classification (UNAVAILABLE = retriable, INVALID_ARGUMENT = terminal).
  - Wrap agent tool calls with retry logic keyed on standard gRPC codes.
- **Remediation Timeline**: 2–4 weeks
- **Recommendation**: Add input validation to `GetQuote` and `ShipOrder` that returns `codes.InvalidArgument` for malformed requests. Implement structured error details using `google.rpc.Status` with retryable classification.
- **Evidence**: `main.go` (lines 96–120: GetQuote and ShipOrder implementations — no error returns)

### API-Q5: API Versioning and Deprecation

- **Severity**: RISK
- **Finding**: The gRPC service is registered as `hipstershop.ShippingService` with no version suffix in `genproto/demo_grpc.pb.go`. No `/v1/` or `/v2/` URL patterns. No `Accept-Version` headers. No changelog files. No deprecation notices.
- **Gap**: No API versioning strategy. Breaking changes to the proto definition would silently break agent tool schemas.
- **Compensating Controls**:
  - Pin agent tool definitions to the current proto schema and validate on each deployment.
  - Use gRPC's built-in forward compatibility (adding fields is non-breaking in protobuf).
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Adopt protobuf package versioning (e.g., `hipstershop.v1.ShippingService`). Establish a deprecation policy with downstream notification.
- **Evidence**: `genproto/demo_grpc.pb.go` (ServiceName: `hipstershop.ShippingService` — no version)

### API-Q7: Asynchronous Operation Support

- **Severity**: RISK
- **Finding**: Both `GetQuote` and `ShipOrder` are synchronous unary RPCs. No background job frameworks, no polling endpoints, no webhook callbacks, no Step Functions, no async invocation patterns found anywhere in the codebase.
- **Gap**: No async support for long-running operations. While the current operations are lightweight and sub-second, there is no mechanism for async patterns if operations become longer-running in the future.
- **Compensating Controls**:
  - Current operations are lightweight (in-memory computation) and unlikely to exceed timeout limits.
  - Agent orchestration can implement its own timeout handling for these fast operations.
- **Remediation Timeline**: 60–90 days (if async patterns become needed)
- **Recommendation**: For current lightweight operations, this is low priority. If shipping cost estimation or order fulfillment becomes more complex (e.g., real carrier API calls), implement async patterns with job submission and polling endpoints.
- **Evidence**: `main.go` (lines 96–120: synchronous RPC implementations), `quote.go` (in-memory computation), `tracker.go` (in-memory random ID generation)

### AUTH-Q2: Scoped Permissions (Least Privilege)

- **Severity**: RISK
- **Finding**: No authorization model exists. No IAM policies, no role definitions, no permission checks in code. The gRPC server accepts all requests from any caller without any identity verification. Both `GetQuote` (read) and `ShipOrder` (write) are equally accessible.
- **Gap**: No scoped permissions. An agent cannot be granted read-only access to `GetQuote` without also having access to `ShipOrder`.
- **Compensating Controls**:
  - Restrict agent scope at the orchestration layer — configure agent tools to only call `GetQuote` and not expose `ShipOrder` as a tool.
  - Implement an API Gateway or service mesh proxy that enforces method-level access control.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement a gRPC interceptor that checks caller identity against a permission matrix (e.g., agent-readonly can call GetQuote but not ShipOrder).
- **Evidence**: `main.go` (lines 73–85: `grpc.NewServer()` with no interceptors or authorization)

### AUTH-Q3: Action-Level Authorization

- **Severity**: RISK
- **Finding**: No action-level authorization exists. Both `GetQuote` and `ShipOrder` are accessible to any caller without permission checks. No ABAC policies, no fine-grained RBAC, no method-level authorization.
- **Gap**: Cannot enforce that an agent may read (GetQuote) but not write (ShipOrder) within the same service.
- **Compensating Controls**:
  - Restrict at the orchestration layer by only exposing `GetQuote` as an agent tool.
  - Use an external authorization service (e.g., OPA) as a gRPC interceptor.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a gRPC unary interceptor that maps the authenticated principal to allowed methods. Use a configuration file or external policy engine to define the mapping.
- **Evidence**: `main.go` (no authorization interceptors), `genproto/demo_grpc.pb.go` (both methods registered without any authorization middleware)

### AUTH-Q4: Identity Propagation

- **Severity**: RISK
- **Finding**: No identity propagation found. No JWT parsing middleware, no OAuth2 token exchange, no user context headers. The gRPC `context.Context` is passed through but carries no identity information. No `X-User-Id` or `Authorization` metadata extraction.
- **Gap**: The service cannot carry originating user context through requests. An agent acting on behalf of a user cannot have that user's identity propagated to the shipping service.
- **Compensating Controls**:
  - For read-only agent scope, identity propagation is less critical since no user-specific data is returned.
  - Agents can include user context in request metadata even if the service doesn't currently validate it.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add gRPC metadata extraction for identity tokens. Implement a middleware that parses JWT/bearer tokens from the `authorization` metadata key and makes the user identity available to handlers.
- **Evidence**: `main.go` (lines 96–120: context used but no identity extraction)

### AUTH-Q5: Agent-as-Self vs Agent-on-Behalf-of-User

- **Severity**: RISK
- **Finding**: No distinction between agent identity modes exists. No separate IAM roles or API keys for different agent access patterns. No audit log fields distinguishing agent-as-self from agent-on-behalf-of-user.
- **Gap**: The service cannot differentiate between an agent acting under its own service identity and an agent acting on behalf of a specific human user. This conflation creates privilege escalation risk.
- **Compensating Controls**:
  - For read-only agent scope, this risk is reduced since agents are not modifying data.
  - Document the expected agent identity model in operational runbooks.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Define separate credential types for agent-as-self and agent-on-behalf-of-user. Log the identity mode with every request.
- **Evidence**: `main.go` (no authentication or identity distinction in any RPC handler)

### AUTH-Q6: Credential Management

- **Severity**: RISK
- **Finding**: No hardcoded credentials found in the codebase. No `.env` files committed. No Secrets Manager or Vault references. The service uses environment-based GCP authentication for the profiler (`cloud.google.com/go/profiler`). The `Dockerfile` does not embed any secrets. However, there is no secrets management integration for service credentials.
- **Gap**: No secrets management system is integrated. When authentication is added (AUTH-Q1), credentials must be managed through AWS Secrets Manager or HashiCorp Vault with rotation support — not environment variables or config files.
- **Compensating Controls**:
  - Current service has no credentials to manage (it connects to no external services requiring auth beyond GCP profiler).
  - GCP profiler uses workload identity or environment-based auth, which is acceptable.
- **Remediation Timeline**: 30–60 days (concurrent with AUTH-Q1 remediation)
- **Recommendation**: When implementing authentication (AUTH-Q1), integrate with AWS Secrets Manager for credential storage and rotation. Do not store credentials in environment variables or config files.
- **Evidence**: `main.go` (lines 131–148: GCP profiler uses environment-based auth), `Dockerfile` (no secrets embedded), `go.mod` (no secrets management dependencies)

### AUTH-Q7: Immutable Audit Logging ⚡

- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: The service uses logrus with JSON formatting (`logrus.JSONFormatter` in `main.go`). Structured logs with `timestamp`, `severity`, and `message` fields are produced. However, log messages are generic: `[GetQuote] received request` and `[ShipOrder] received request`. No authenticated principal is logged. No CloudTrail integration. No immutable log storage configuration. No S3 bucket with object lock.
- **Gap**: Logs do not include caller identity. Even if authentication were added, the current logging does not capture who made the request. No immutable log storage ensures logs cannot be tampered with.
- **Compensating Controls**:
  - Structured JSON logging is already in place — adding identity fields is an incremental change.
  - Ship logs to CloudWatch Logs with retention policies as an interim measure.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add caller identity (principal, agent ID) to every log entry. Configure log shipping to an immutable store (S3 with Object Lock or CloudWatch Logs with resource policies preventing deletion).
- **Evidence**: `main.go` (lines 39–49: logrus JSONFormatter configured; lines 97, 99, 108, 110: generic log messages with no identity)

### AUTH-Q8: Agent Identity Suspension

- **Severity**: RISK
- **Finding**: No mechanism for suspending or revoking agent identities exists. Since there is no authentication at all (AUTH-Q1), there is nothing to suspend. No API key revocation, no IAM role deactivation, no Cognito user pool disable mechanism.
- **Gap**: If an agent misbehaves, there is no way to suspend its access to this service without shutting down the service entirely.
- **Compensating Controls**:
  - Network-level blocking (firewall rules) can block a specific agent's IP as an emergency measure.
  - Service mesh policies can be updated to deny traffic from specific service identities.
- **Remediation Timeline**: 30–60 days (concurrent with AUTH-Q1 remediation)
- **Recommendation**: When implementing authentication (AUTH-Q1), ensure the credential store supports per-identity revocation. Implement an API key revocation endpoint or integrate with a centralized identity provider that supports instant suspension.
- **Evidence**: `main.go` (no authentication framework to provide suspension capability)

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: No compensation or rollback logic exists. `ShipOrder` is a simple function that generates a random tracking ID using `CreateTrackingId(baseAddress)` in `tracker.go`. There are no multi-step operations, no saga pattern, no undo endpoints, no Step Functions with error handling.
- **Gap**: `ShipOrder` is a one-way operation with no way to cancel or reverse a shipment. The generated tracking ID cannot be invalidated.
- **Compensating Controls**:
  - For read-only agent scope, agents would only call `GetQuote` (which has no side effects), making compensation unnecessary.
  - If `ShipOrder` is exposed, wrap it in an orchestration layer with human approval.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add a `CancelShipment` RPC that invalidates a tracking ID. Implement a state machine for shipment lifecycle (pending → confirmed → shipped → cancelled).
- **Evidence**: `main.go` (lines 107–117: ShipOrder implementation — no rollback), `tracker.go` (CreateTrackingId — one-way generation)

### STATE-Q2: Queryable Current State

- **Severity**: RISK
- **Finding**: The service is entirely stateless. `GetQuote` returns a computed value based on item count. `ShipOrder` generates a random tracking ID that is not stored anywhere. There are no GET endpoints for resource state, no status query APIs, no database schemas.
- **Gap**: No queryable state. An agent cannot check the status of a previously created shipment or retrieve historical quotes. There is no read-before-write pattern possible.
- **Compensating Controls**:
  - For `GetQuote`, the operation is deterministic (same count → same quote) so state is implicit.
  - Agents can store tracking IDs externally for reference.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add a `GetShipmentStatus` RPC that accepts a tracking ID and returns shipment state. Implement a data store (DynamoDB or PostgreSQL) to persist shipment records.
- **Evidence**: `main.go` (only two RPCs: GetQuote and ShipOrder — no query endpoints), `tracker.go` (tracking ID generated but not stored)

### STATE-Q3: Concurrency Controls

- **Severity**: RISK
- **Finding**: No concurrency controls exist. No optimistic locking, no version fields, no `SELECT FOR UPDATE`, no DynamoDB conditional writes. The service is stateless, so there is no shared mutable state to protect. However, `ShipOrder` generates tracking IDs using `rand.Intn()` which is not concurrency-safe in older Go versions (Go's default global rand became safe in Go 1.20+).
- **Gap**: No concurrency controls. If the service becomes stateful (e.g., storing shipments), concurrent agent calls could create race conditions.
- **Compensating Controls**:
  - Current stateless design minimizes concurrency risk.
  - Go 1.25+ (as specified in go.mod) has a concurrency-safe global rand, mitigating the `rand.Intn()` concern.
- **Remediation Timeline**: 60–90 days (when stateful features are added)
- **Recommendation**: When adding persistence, implement optimistic locking with version fields on all mutable records. Use DynamoDB conditional writes or database-level constraints.
- **Evidence**: `tracker.go` (uses `rand.Intn()` for ID generation), `go.mod` (go 1.25.0 — safe global rand), `main.go` (stateless service)

### STATE-Q4: Circuit Breakers and Resilience

- **Severity**: RISK
- **Finding**: No circuit breaker or resilience patterns found for core service operations. The `initProfiling` function in `main.go` (lines 131–148) has retry logic with exponential backoff for GCP Profiler initialization, but this is not a core service pattern. No Resilience4j, no Polly, no circuit breaker annotations. The service does not call external dependencies for its core operations.
- **Gap**: No resilience patterns. If the service is extended to call external carrier APIs, there are no circuit breakers to prevent cascading failures.
- **Compensating Controls**:
  - Current implementation has no external dependencies for core operations (GetQuote and ShipOrder are fully in-memory), so circuit breakers are not currently needed.
  - gRPC framework provides built-in deadline/timeout propagation via context.
- **Remediation Timeline**: 60–90 days (when external dependencies are added)
- **Recommendation**: When adding external service calls (e.g., carrier rate APIs), implement circuit breakers using a Go resilience library (e.g., `sony/gobreaker`). Configure timeout and retry policies.
- **Evidence**: `main.go` (lines 131–148: retry logic for profiler only), `quote.go` (in-memory computation), `tracker.go` (in-memory ID generation)

### STATE-Q5: Rate Limiting and Throttling

- **Severity**: RISK
- **Finding**: No rate limiting configuration found. No API Gateway throttling. No WAF rate rules. No application-level rate limiting middleware. The gRPC server has no interceptors for throttling. No `aws_api_gateway_usage_plan` or equivalent in IaC (no IaC exists).
- **Gap**: A runaway agent loop could overwhelm the service with requests at machine speed. No mechanism to prevent or detect this.
- **Compensating Controls**:
  - Implement rate limiting at the infrastructure layer (API Gateway, service mesh, or load balancer) outside this service.
  - Add a gRPC interceptor for per-client rate limiting as a quick fix.
- **Remediation Timeline**: 2–4 weeks
- **Recommendation**: Add a gRPC unary interceptor that enforces per-client rate limits using a token bucket algorithm. Store rate limit state in Redis or in-memory. Return `codes.ResourceExhausted` when limits are exceeded.
- **Evidence**: `main.go` (lines 73–85: `grpc.NewServer()` with no interceptors)

### STATE-Q6: Blast Radius and Transaction Limits

- **Severity**: RISK
- **Finding**: No transaction limits or blast radius controls exist. No configurable limits per agent identity (e.g., max shipments per hour, max quotes per minute). No `max_refunds_per_hour` or equivalent configuration.
- **Gap**: An agent could call `ShipOrder` thousands of times per second with no limit. While currently the operation is lightweight (generating random IDs), if the service becomes production-grade with real carrier integrations, uncapped agent operations could have significant business impact.
- **Compensating Controls**:
  - For read-only agent scope, limit agent tools to `GetQuote` only — which has no side effects.
  - Implement blast radius controls at the orchestration layer.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement per-identity transaction limits configurable via environment variables or configuration. Example: `MAX_SHIP_ORDERS_PER_HOUR=100` per agent identity.
- **Evidence**: `main.go` (no transaction limit logic), no configuration files with limit definitions

### STATE-Q7: Infrastructure Capacity for Agent Traffic

- **Severity**: RISK
- **Finding**: No load testing results, no auto-scaling configuration, and no capacity planning documentation found. The `Dockerfile` builds a single binary with no horizontal scaling configuration. No Kubernetes HPA (Horizontal Pod Autoscaler), no ECS service auto-scaling, no load test configurations.
- **Gap**: Unknown capacity limits. The service has not been tested for agent-scale traffic patterns (high concurrency, burst requests, exploratory retries).
- **Compensating Controls**:
  - The service is lightweight (in-memory computation, no I/O) and likely has high throughput capacity.
  - Container orchestration (Kubernetes/ECS) can provide horizontal scaling externally.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Run load tests simulating agent traffic patterns (high concurrency, burst requests). Define auto-scaling policies based on CPU/memory thresholds. Document capacity limits.
- **Evidence**: `Dockerfile` (single binary, no scaling config), no load test files, no auto-scaling configuration

### HITL-Q1: Draft/Pending State

- **Severity**: RISK
- **Finding**: No draft or pending state concept exists. The service is stateless. `ShipOrder` immediately generates and returns a tracking ID — there is no "pending shipment" state that could be reviewed before confirmation.
- **Gap**: No ability for an agent to propose a shipment and have a human review/approve it before execution.
- **Compensating Controls**:
  - For read-only agent scope, agents would only use `GetQuote` which has no side effects.
  - Implement approval gates in the agent orchestration layer.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add a `CreatePendingShipment` RPC that creates a shipment in PENDING state, and a `ConfirmShipment` RPC that transitions it to CONFIRMED. Only confirmed shipments generate tracking IDs.
- **Evidence**: `main.go` (lines 107–117: ShipOrder immediately returns tracking ID, no pending state)

### HITL-Q2: Configurable Approval Gates

- **Severity**: RISK
- **Finding**: No approval workflow exists. No human-in-the-loop gates. No Step Functions with `waitForTaskToken`. No approval API endpoints. No configurable operation-level flags.
- **Gap**: No mechanism to require human approval for specific operations (e.g., high-value shipments, bulk operations).
- **Compensating Controls**:
  - Implement approval gates in the agent orchestration layer (e.g., require human approval in the agent workflow before calling ShipOrder).
  - Use Amazon Step Functions with human approval tasks in the agent pipeline.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add configurable approval gates at the service level. For example, shipments exceeding a configurable item count threshold require explicit approval via a separate `ApproveShipment` RPC.
- **Evidence**: No approval-related code or configuration found in any repository file

### HITL-Q3: Sandbox/Staging Environment

- **Severity**: RISK
- **Finding**: A `Dockerfile` exists for containerization, and the `README.md` documents `docker build ./` for building. However, no docker-compose file, no staging environment configuration, no seed data scripts, no synthetic data generators, and no environment-specific configuration files exist.
- **Gap**: No sandbox or staging environment for testing agent interactions without risk to production. No environment separation configuration.
- **Compensating Controls**:
  - The service is stateless with no external dependencies — it can be run locally via Docker for testing.
  - `go test .` provides unit test coverage for core functionality.
- **Remediation Timeline**: 2–4 weeks
- **Recommendation**: Create a `docker-compose.yml` for local development and testing. Define environment-specific configurations (dev/staging/prod) via environment variables. Create a test harness that simulates agent interactions.
- **Evidence**: `Dockerfile` (containerization exists), `README.md` (documents `docker build ./` and `go test .`), no docker-compose.yml or staging config

### DATA-Q2: Data Residency and Sovereignty ⚡

- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: No data residency requirements are documented. The service is stateless and does not persist data. However, it processes address data (PII) in transit — `GetQuoteRequest` and `ShipOrderRequest` both include `Address` with `street_address`, `city`, `state`, `country`, `zip_code`. No region-specific configuration, no GDPR/LGPD references, no data sovereignty policies.
- **Gap**: No documentation of data residency requirements for the address data processed by this service. If an agent sends address data to an LLM endpoint in a different jurisdiction, there may be compliance implications.
- **Compensating Controls**:
  - The service is stateless — address data is processed in memory and not stored.
  - For read-only scope (GetQuote), address data is used only for cost calculation.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document data residency requirements for the address data processed by this service. Determine if GDPR or other regulations apply based on the deployment region and customer base. Ensure the agent orchestration layer does not send address data to LLM endpoints in restricted jurisdictions.
- **Evidence**: `genproto/demo.pb.go` (lines 917–927: Address struct with location data), no data residency documentation

### DATA-Q3: Selective Query Support

- **Severity**: RISK
- **Finding**: The service has only two RPCs with fixed request/response types. `GetQuote` accepts items and returns a single cost. `ShipOrder` accepts items/address and returns a single tracking ID. No pagination, no filtering, no sorting. The protobuf messages define exactly what fields are returned.
- **Gap**: No selective query support. While the current API returns small, fixed-size responses (a single cost or tracking ID), there is no mechanism for agents to request subsets of data if the API grows.
- **Compensating Controls**:
  - Current responses are small and fixed-size — agents receive exactly what they need without unbounded result sets.
  - Protobuf's strongly typed schema inherently limits what is returned per call.
- **Remediation Timeline**: Low priority (not a current concern)
- **Recommendation**: If the API evolves to return lists (e.g., shipment history), implement pagination parameters in the protobuf messages (e.g., `page_token`, `page_size`).
- **Evidence**: `genproto/demo.pb.go` (GetQuoteResponse has single CostUsd field; ShipOrderResponse has single TrackingId field)

### DATA-Q4: System of Record Designations

- **Severity**: RISK
- **Finding**: No system-of-record documentation exists. No master data management references. No data ownership definitions. The service is part of the `hipstershop` microservices demo but there is no documentation of which service is authoritative for which data entities.
- **Gap**: If multiple services handle shipping-related data, agents may encounter conflicting records without knowing which source is authoritative.
- **Compensating Controls**:
  - The shipping service is the only service generating tracking IDs — it is implicitly the system of record for tracking IDs.
  - Document service data ownership in a central architecture document.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a data ownership matrix documenting which service owns which data entities (e.g., ShippingService owns tracking IDs and shipping quotes). Publish this as part of the service documentation.
- **Evidence**: No data ownership documentation in any repository file

### DATA-Q5: Reliable Timestamps

- **Severity**: RISK
- **Finding**: No timestamps are included in the data model or API responses. `GetQuoteResponse` returns only `CostUsd` (a `Money` message). `ShipOrderResponse` returns only `TrackingId` (a string). No `created_at`, `updated_at`, `quote_timestamp`, or `shipped_at` fields. Log timestamps exist (logrus JSONFormatter uses `time.RFC3339Nano`) but these are not in API responses.
- **Gap**: Agents performing time-sensitive reasoning cannot determine when a quote was generated or when a shipment was created. Stale quotes cannot be detected.
- **Compensating Controls**:
  - Agents can record timestamps on their side when receiving responses.
  - Quotes are deterministic (same count → same price), so staleness is less of a concern currently.
- **Remediation Timeline**: 2–4 weeks
- **Recommendation**: Add `timestamp` fields to `GetQuoteResponse` and `ShipOrderResponse` in the protobuf definition. Use UTC (`google.protobuf.Timestamp`) for all timestamps.
- **Evidence**: `genproto/demo.pb.go` (GetQuoteResponse and ShipOrderResponse — no timestamp fields), `main.go` (log timestamps exist but not in API responses)

### DATA-Q6: Data Freshness Signaling

- **Severity**: RISK
- **Finding**: No data freshness signaling exists. No `Cache-Control` headers (not applicable to gRPC), no `X-Data-Age` metadata, no `last_refreshed` field, no `consistency_level` field. The service computes responses in real-time (no caching).
- **Gap**: Agents have no way to know if data is current, cached, or eventually consistent. While the current service computes in real-time, the protocol does not signal this.
- **Compensating Controls**:
  - The service is stateless and computes all responses in real-time — data is always "fresh" by definition.
  - Document this behavior in the service API documentation.
- **Remediation Timeline**: Low priority
- **Recommendation**: Add gRPC response metadata indicating data freshness (e.g., `x-data-source: computed` or `x-cache-status: none`). This is useful documentation even if the service currently has no caching.
- **Evidence**: `main.go` (lines 96–117: real-time computation, no caching), `quote.go` (deterministic in-memory computation)

### DATA-Q7: PII Redaction in Logs

- **Severity**: RISK
- **Finding**: Log statements in `main.go` log only generic messages: `[GetQuote] received request`, `[GetQuote] completed request`, `[ShipOrder] received request`, `[ShipOrder] completed request`. Address data from `ShipOrder` is used in `baseAddress` string (`fmt.Sprintf("%s, %s, %s", in.Address.StreetAddress, in.Address.City, in.Address.State)`) for tracking ID generation but is NOT logged. However, no log scrubbing middleware exists, and if debug logging or error logging is added in the future, PII could leak into logs.
- **Gap**: No PII redaction framework exists. While current logs do not contain PII, there is no systematic protection against PII leaking into logs as the service evolves.
- **Compensating Controls**:
  - Current log statements do not include PII — address data is used only for computation and not logged.
  - Add a linting rule or code review checklist item to prevent logging PII.
- **Remediation Timeline**: 2–4 weeks
- **Recommendation**: Add a log scrubbing middleware or logrus hook that redacts known PII patterns (addresses, phone numbers, email) from log messages. Implement a pre-commit hook or CI check that detects potential PII in log statements.
- **Evidence**: `main.go` (lines 97–110: log messages are generic, no PII logged; line 112: `baseAddress` constructed from PII but not logged)

### DISC-Q1: Schema Documentation and Versioning

- **Severity**: RISK
- **Finding**: Protobuf generated code exists in `genproto/demo.pb.go` and `genproto/demo_grpc.pb.go`, generated by `protoc v3.6.1` and `protoc-gen-go v1.34.2`. The source `.proto` file is external (`../../protos/demo.proto` per `genproto.sh`). No schema versioning is evident — no version tags in the proto package name, no schema registry, no migration files. The generated code header indicates `protoc v3.6.1` which is outdated.
- **Gap**: Schema source is external and not version-controlled within this repository. No schema versioning strategy. Protoc version (3.6.1) is significantly outdated.
- **Compensating Controls**:
  - Generated code is committed to the repository, providing a snapshot of the current schema.
  - gRPC reflection enables runtime schema discovery.
- **Remediation Timeline**: 2–4 weeks
- **Recommendation**: Include the `.proto` file in this repository. Implement a CI step that validates generated code matches the proto source. Add schema version tags to the proto package. Update protoc to a current version.
- **Evidence**: `genproto.sh` (references `../../protos`), `genproto/demo_grpc.pb.go` (line 18: `protoc v3.6.1`), `genproto/demo.pb.go` (line 19: `protoc-gen-go v1.34.2`)

### OBS-Q1: Distributed Tracing and Structured Logging

- **Severity**: RISK
- **Finding**: Structured JSON logging IS configured using logrus with `JSONFormatter` in `main.go` (lines 39–49), producing logs with `timestamp`, `severity`, and `message` fields. However, distributed tracing is NOT implemented — `initTracing()` (line 128) and `initStats()` (line 124) are TODO stubs with no implementation. OpenTelemetry packages appear in `go.mod` as indirect dependencies (via GCP profiler and gRPC) but are not used directly. No trace ID propagation, no `traceparent` header handling, no correlation IDs in log entries.
- **Gap**: No distributed tracing. When an agent-initiated request fails, there is no trace ID to correlate the request across services. Log entries lack correlation IDs for request-level debugging.
- **Compensating Controls**:
  - Structured JSON logging is in place — adding correlation IDs is incremental.
  - OpenTelemetry libraries are already indirect dependencies — minimal new dependencies needed.
- **Remediation Timeline**: 2–4 weeks
- **Recommendation**: Implement `initTracing()` using OpenTelemetry SDK. Add a gRPC interceptor (`otelgrpc`) for automatic trace propagation. Include `trace_id` and `span_id` in log entries. The `go.opentelemetry.io/contrib/instrumentation/google.golang.org/grpc/otelgrpc` package is already an indirect dependency.
- **Evidence**: `main.go` (lines 39–49: structured logging configured; lines 124, 128: TODO stubs for tracing/stats), `go.mod` (OpenTelemetry indirect dependencies present)

### OBS-Q2: Alerting on Error Rates and Latency

- **Severity**: RISK
- **Finding**: No alerting configuration found. No CloudWatch alarms, no anomaly detection, no PagerDuty/OpsGenie integration, no SLO-based alerting. No monitoring configuration files exist in the repository.
- **Gap**: No alerting on error rates or latency. If the service degrades, agents will experience failures without any proactive notification.
- **Compensating Controls**:
  - gRPC health checking is implemented (`health.NewServer()` in `main.go`), enabling basic liveness detection.
  - External monitoring tools can be configured outside this repository.
- **Remediation Timeline**: 2–4 weeks
- **Recommendation**: Define CloudWatch alarms for gRPC error rates (status codes ≠ OK) and P95 latency. Configure anomaly detection for traffic patterns. Integrate with PagerDuty/OpsGenie for on-call alerting.
- **Evidence**: `main.go` (lines 87–88: health checking configured but no alerting), no monitoring configuration files

### ENG-Q1: Infrastructure Governance

- **Severity**: RISK
- **Finding**: No IaC files exist in the repository. No Terraform, CloudFormation, CDK, Helm charts, or Kustomize definitions. The infrastructure exposing this service (API gateways, IAM roles, secrets, network configurations) is not defined as code in this repository. A `Dockerfile` exists but defines only the container build, not the infrastructure.
- **Gap**: No infrastructure governance. The service's deployment infrastructure is not defined, reviewed, or monitored for drift within this repository.
- **Compensating Controls**:
  - Infrastructure may be defined in a separate infrastructure repository (common in microservices architectures).
  - The Dockerfile provides container build reproducibility.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Define the service's infrastructure as code (Terraform or CDK) within this repository or link to the infrastructure repository. Include API Gateway, IAM roles, security groups, and secrets configuration. Subject IaC changes to peer review and enable drift detection.
- **Evidence**: No IaC files found in repository, `Dockerfile` (container build only)

### ENG-Q2: CI/CD with API Contract Testing

- **Severity**: RISK
- **Finding**: No CI/CD configuration found. No `.github/workflows/` directory, no `Jenkinsfile`, no `buildspec.yml`, no GitLab CI configuration. No contract testing (Pact or equivalent). No OpenAPI spec validation in build. No breaking change detection.
- **Gap**: No CI/CD pipeline. API changes cannot be automatically tested or validated before deployment. No mechanism to detect breaking proto changes.
- **Compensating Controls**:
  - Unit tests exist in `shippingservice_test.go` that validate core RPC behavior.
  - Proto changes would cause compilation errors if incompatible, providing a basic safety net.
- **Remediation Timeline**: 2–4 weeks
- **Recommendation**: Create a CI pipeline (GitHub Actions or CodeBuild) that runs `go test ./...`, validates proto compatibility using `buf breaking`, and checks for API contract compliance. Add consumer-driven contract tests.
- **Evidence**: No CI/CD configuration files in repository, `shippingservice_test.go` (unit tests exist but no CI to run them)

### ENG-Q3: Rollback Capability

- **Severity**: RISK
- **Finding**: No deployment or rollback configuration found. No blue/green deployment, no canary deployment, no CodeDeploy rollback triggers, no Helm rollback configuration, no feature flags, no traffic shifting.
- **Gap**: If a deployment breaks agent-facing APIs, there is no documented or configured mechanism to roll back to a known-good state.
- **Compensating Controls**:
  - Container image tagging allows manual rollback to a previous image version.
  - Kubernetes rollback (`kubectl rollout undo`) is available if deployed on Kubernetes.
- **Remediation Timeline**: 2–4 weeks
- **Recommendation**: Implement deployment configuration with automatic rollback triggers. Use blue/green or canary deployment strategy. Define rollback procedures in an operational runbook.
- **Evidence**: `Dockerfile` (container build exists but no deployment config), no deployment configuration files

### ENG-Q4: API Test Coverage

- **Severity**: RISK
- **Finding**: Unit tests exist in `shippingservice_test.go` with good coverage: `TestGetQuote` (validates quote value), `TestGetQuoteEmptyCart` (edge case), `TestShipOrder` (validates tracking ID length), `TestTrackingIdFormat` (regex validation), `TestTrackingIdUniqueness` (50 IDs for uniqueness), `TestCreateQuoteFromFloat` (5 sub-tests), `TestCreateQuoteFromCount`, `TestGetRandomLetterCode` (100 iterations), `TestGetRandomNumber` (5 digit counts), `TestQuoteString`. Tests directly invoke gRPC handlers. However, no contract tests, no integration tests, no error handling tests (missing address, nil items), and no CI pipeline to run tests.
- **Gap**: Unit tests cover happy path but not error cases. No contract tests to validate proto compatibility. No CI pipeline ensures tests run before deployment.
- **Compensating Controls**:
  - Existing unit tests provide basic API behavior validation.
  - Protobuf schema provides compile-time type safety.
- **Remediation Timeline**: 2–4 weeks
- **Recommendation**: Add error case tests (nil address, empty items, boundary values). Add contract tests using `buf breaking` for proto compatibility. Create a CI pipeline that runs all tests. Add test coverage reporting.
- **Evidence**: `shippingservice_test.go` (11 test functions with good happy-path coverage but no error case testing)

### ENG-Q5: Encryption at Rest

- **Severity**: RISK
- **Finding**: No encryption at rest configuration found. No KMS key references, no `kms_key_id` on any resource. The service is stateless with no data stores (no S3, no RDS, no DynamoDB, no EBS volumes). No IaC defining encrypted storage.
- **Gap**: While the service is currently stateless, there is no encryption configuration for any future data storage. If persistence is added (STATE-Q2 recommendation), encryption at rest must be configured from the start.
- **Compensating Controls**:
  - Service is stateless — no data at rest to encrypt currently.
  - AWS services default to encryption at rest (S3, DynamoDB) when properly configured.
- **Remediation Timeline**: When data persistence is added
- **Recommendation**: When adding data persistence, ensure all data stores are encrypted at rest using customer-managed KMS keys. Define encryption configuration in IaC.
- **Evidence**: No IaC files, no data store configuration, `main.go` (no database connections)

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO
- **Finding**: The service exposes a well-defined gRPC interface via Protocol Buffers. `ShippingService` implements two RPCs: `GetQuote` (shipping cost estimation) and `ShipOrder` (tracking ID generation). The generated code in `genproto/demo_grpc.pb.go` defines the full service contract with strongly typed request/response messages. gRPC reflection is enabled via `reflection.Register(srv)` in `main.go`, allowing runtime schema discovery. The service does NOT require direct database access, file-based exchange, or UI automation for integration.
- **Implication**: gRPC with protobuf is an excellent agent integration surface. Agent tools can be auto-generated from the proto definition. gRPC reflection further enhances runtime discoverability.
- **Recommendation**: Continue using gRPC as the primary integration interface. Consider adding a gRPC-Web or gRPC-Gateway proxy if HTTP/REST clients need to integrate alongside gRPC agents.
- **Evidence**: `main.go` (line 86: `pb.RegisterShippingServiceServer(srv, svc)`; line 91: `reflection.Register(srv)`), `genproto/demo_grpc.pb.go` (ShippingService definition with GetQuote and ShipOrder RPCs)

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: `ShipOrder` is a write operation that generates a random tracking ID via `CreateTrackingId(baseAddress)` in `tracker.go`. The same input (same address and items) produces a different tracking ID each time — the operation is NOT idempotent. `GetQuote` IS idempotent (same item count always returns $8.99). No idempotency key support, no unique constraint enforcement on business keys.
- **Implication**: For read-only agent scope, this is informational only since agents would only call `GetQuote`. If the agent scope expands to write-enabled, `ShipOrder` non-idempotency becomes a BLOCKER — duplicate agent retries would create duplicate shipments.
- **Recommendation**: When expanding to write-enabled agent scope, add idempotency key support to `ShipOrder`. Accept an `idempotency_key` field in the request and return the same tracking ID for duplicate keys.
- **Evidence**: `tracker.go` (CreateTrackingId uses `rand.Intn()` — non-deterministic), `quote.go` (CreateQuoteFromCount — deterministic), `main.go` (lines 107–117: ShipOrder implementation)

### API-Q6: Structured Response Format

- **Severity**: INFO
- **Finding**: gRPC uses Protocol Buffers — a strongly typed, structured binary format. `GetQuoteResponse` returns a `Money` message with `CurrencyCode` (string), `Units` (int64), and `Nanos` (int32). `ShipOrderResponse` returns a `TrackingId` (string). All response types are defined in `genproto/demo.pb.go` with full type information.
- **Implication**: Protocol Buffers are excellent for machine consumption. Agent tools can parse responses with zero ambiguity. The strongly typed schema eliminates format-related parsing errors.
- **Recommendation**: No action needed. Protobuf is the ideal response format for agent integration. If HTTP/REST access is needed, gRPC-Gateway can auto-generate JSON REST endpoints from the proto definition.
- **Evidence**: `genproto/demo.pb.go` (GetQuoteResponse with Money message, ShipOrderResponse with TrackingId), `genproto/demo_grpc.pb.go` (typed service interface)

### API-Q8: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: No event emission capability found. No SNS/SQS/EventBridge/Kafka integration. No webhook endpoints. No CDC pipelines. The service does not emit events when shipping quotes are generated or orders are shipped.
- **Implication**: Agents cannot subscribe to shipping events for proactive workflows (e.g., "notify when shipment status changes"). All agent interaction must be request/response. For initial read-only deployment, this is acceptable.
- **Recommendation**: When the service becomes stateful, add event emission for key state changes (shipment created, shipment shipped, shipment delivered) via SNS or EventBridge. This enables event-driven agent patterns.
- **Evidence**: No event/webhook code or configuration in any repository file

### API-Q9: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limiting configuration found. No API Gateway throttle settings. No WAF rate rules. No rate limiting middleware. No `X-RateLimit-Remaining` or `Retry-After` response headers (or gRPC metadata equivalents). No `aws_api_gateway_usage_plan` in IaC.
- **Implication**: Agents calling this service at machine speed have no self-throttling signal. Without rate limit information in responses, agents must rely on external configuration to manage call frequency.
- **Recommendation**: When rate limiting is implemented (STATE-Q5), add gRPC response metadata for rate limit status: `x-ratelimit-remaining`, `x-ratelimit-reset`. Document rate limits in the service API documentation.
- **Evidence**: `main.go` (no rate limiting interceptors), no IaC files with API Gateway throttling

### API-Q10: API Latency Profile

- **Severity**: INFO
- **Finding**: No performance benchmarks, load test results, or latency metrics found. The service performs only in-memory computation: `GetQuote` multiplies item count by a fixed price (`quote.go`), and `ShipOrder` generates a random string (`tracker.go`). No I/O, no database calls, no external API calls. P95 latency is expected to be sub-millisecond but no evidence exists to confirm this.
- **Implication**: The lightweight in-memory implementation suggests sub-second P95 latency, making synchronous agent tool calls practical. However, without actual latency measurements, this is an assumption. If carrier API integrations are added, latency will increase significantly.
- **Recommendation**: Add latency benchmarks using Go's `testing.B` benchmarks. When deployed, configure CloudWatch or Prometheus metrics to track P95/P99 latency.
- **Evidence**: `quote.go` (simple arithmetic — no I/O), `tracker.go` (random string generation — no I/O), `main.go` (no external service calls in RPC handlers)

### DATA-Q8: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality scores, completeness metrics, duplicate detection, or data freshness SLAs found. The service is stateless — it does not store data, so traditional data quality metrics do not apply. `GetQuote` returns a hardcoded $8.99 for any non-empty cart. `ShipOrder` generates random tracking IDs.
- **Implication**: Data quality is not a concern for the current stateless implementation. If the service evolves to use real carrier data (actual shipping rates, real tracking), data quality metrics become important for agent decision-making.
- **Recommendation**: When integrating with real carrier APIs, add data quality monitoring for carrier rate freshness, tracking status accuracy, and delivery estimate reliability.
- **Evidence**: `quote.go` (hardcoded `8.99` rate), `tracker.go` (random ID generation), `main.go` (stateless implementation)

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Protobuf field names are clear and semantically meaningful: `product_id`, `quantity`, `street_address`, `city`, `state`, `country`, `zip_code`, `currency_code`, `units`, `nanos`, `tracking_id`, `cost_usd`. No legacy abbreviations or cryptic codes. Go struct tags include JSON field names for serialization.
- **Implication**: Field names are immediately interpretable by LLM-based agents. No data dictionary lookup required. This is a positive finding that accelerates agent tool definition.
- **Recommendation**: Maintain current naming conventions. Add field-level documentation comments in the `.proto` source file to further enhance agent understanding.
- **Evidence**: `genproto/demo.pb.go` (Address struct fields: `StreetAddress`, `City`, `State`, `Country`, `ZipCode`; Money: `CurrencyCode`, `Units`, `Nanos`)

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No data catalog or metadata layer exists. No AWS Glue Data Catalog, no Collibra, no Alation, no DataHub. No metadata files or data dictionaries in the repository.
- **Implication**: Agent tool authors must read the proto definition to understand what data the service handles. No centralized metadata discovery for this service.
- **Recommendation**: For a microservice this simple, the proto definition serves as the de facto metadata layer. For the broader microservices platform, consider a service catalog (e.g., Backstage) that indexes all services and their proto definitions.
- **Evidence**: No metadata or data catalog files in the repository

### DISC-Q4: Data Lineage

- **Severity**: INFO
- **Finding**: No data lineage tools or documentation exist. No Apache Atlas, no AWS Glue DataBrew, no ETL pipeline documentation, no data flow diagrams, no source-to-target mappings.
- **Implication**: If an agent produces incorrect output based on shipping data, there is no lineage to trace where the data originated (e.g., which frontend submitted the address, which service called ShipOrder).
- **Recommendation**: For the current simple service, implement request-level tracing (OBS-Q1) as a lightweight lineage mechanism. For the broader platform, consider data lineage tooling.
- **Evidence**: No lineage tools or documentation in the repository

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No custom business metrics published. No `cloudwatch.put_metric_data` calls. No business KPI dashboards. No metrics for quote accuracy, shipment success rate, or tracking ID usage. Only infrastructure-level metrics (if deployed with monitoring) would exist.
- **Implication**: When agents consume this service, there are no business-level signals to determine whether agent interactions produce good outcomes (e.g., are agent-initiated quotes converting to orders? Are agent-generated shipments being delivered successfully?).
- **Recommendation**: Add custom metrics for: quotes generated per minute, shipments created per minute, average items per shipment. When deployed, track these in CloudWatch custom metrics or Prometheus.
- **Evidence**: `main.go` (no metrics publication code), no monitoring configuration files

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: The service exposes a well-defined gRPC interface via Protocol Buffers. `ShippingService` implements two RPCs: `GetQuote` and `ShipOrder`. gRPC reflection is enabled via `reflection.Register(srv)`. No direct database access, file-based exchange, or UI automation required.
- **Gap**: N/A — the service passes this check. gRPC with protobuf is a documented, typed API interface.
- **Recommendation**: Continue using gRPC. Consider adding gRPC-Gateway for HTTP/REST agent clients.
- **Evidence**: `main.go`, `genproto/demo_grpc.pb.go`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK
- **Finding**: Generated protobuf code defines the schema. Source `.proto` file is external (`../../protos/demo.proto`). gRPC reflection enabled for runtime discovery. No OpenAPI spec in repo.
- **Gap**: Source proto definition is not in this repository.
- **Recommendation**: Include `demo.proto` in this repository. Add CI validation step.
- **Evidence**: `genproto.sh`, `main.go`, `genproto/demo_grpc.pb.go`

#### API-Q3: Structured Error Responses
- **Severity**: RISK
- **Finding**: gRPC provides structured error codes via `codes` and `status` packages. Core RPCs never return errors — they always succeed. No custom error types or retryable classification.
- **Gap**: No error classification for agent consumption. Missing input validation.
- **Recommendation**: Add input validation returning appropriate gRPC status codes. Implement structured error details.
- **Evidence**: `main.go` (GetQuote and ShipOrder implementations)

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: `ShipOrder` generates a random tracking ID — not idempotent. `GetQuote` is idempotent. No idempotency key support.
- **Gap**: `ShipOrder` is non-idempotent (informational for read-only scope).
- **Recommendation**: Add idempotency key support when expanding to write-enabled scope.
- **Evidence**: `tracker.go`, `quote.go`, `main.go`

#### API-Q5: API Versioning and Deprecation
- **Severity**: RISK
- **Finding**: Service registered as `hipstershop.ShippingService` with no version suffix. No changelog or deprecation policy.
- **Gap**: No API versioning strategy.
- **Recommendation**: Adopt protobuf package versioning (e.g., `hipstershop.v1.ShippingService`).
- **Evidence**: `genproto/demo_grpc.pb.go`

#### API-Q6: Structured Response Format
- **Severity**: INFO
- **Finding**: gRPC uses Protocol Buffers — strongly typed, structured binary format. Excellent for machine consumption.
- **Gap**: N/A — positive finding.
- **Recommendation**: No action needed. Protobuf is ideal for agent integration.
- **Evidence**: `genproto/demo.pb.go`, `genproto/demo_grpc.pb.go`

#### API-Q7: Asynchronous Operation Support
- **Severity**: RISK
- **Finding**: Both RPCs are synchronous. No async patterns, no background job frameworks, no polling endpoints.
- **Gap**: No async support. Current operations are lightweight, so this is low-impact.
- **Recommendation**: Implement async patterns if operations become long-running.
- **Evidence**: `main.go`, `quote.go`, `tracker.go`

#### API-Q8: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: No event emission. No SNS/SQS/EventBridge/Kafka/webhook integration.
- **Gap**: No event-driven patterns for proactive agent workflows.
- **Recommendation**: Add event emission for state changes when service becomes stateful.
- **Evidence**: No event/webhook code in any repository file

#### API-Q9: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limiting configuration. No rate limit headers in responses.
- **Gap**: No self-throttling signal for agents.
- **Recommendation**: Add rate limit response metadata when rate limiting is implemented.
- **Evidence**: `main.go` (no rate limiting interceptors)

#### API-Q10: API Latency Profile
- **Severity**: INFO
- **Finding**: No latency benchmarks. In-memory computation suggests sub-millisecond P95 but no evidence confirms this.
- **Gap**: No measured latency profile.
- **Recommendation**: Add Go benchmarks and production latency metrics.
- **Evidence**: `quote.go`, `tracker.go`, `main.go`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: gRPC server created with `grpc.NewServer()` — no interceptors, no TLS, no auth middleware. Any client can connect and invoke RPCs.
- **Gap**: No machine identity authentication. No principal attribution.
- **Recommendation**: Add gRPC auth interceptor. Implement mTLS or OAuth2 client credentials.
- **Evidence**: `main.go` (lines 73–85)

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK
- **Finding**: No authorization model. Both RPCs accessible to all callers equally.
- **Gap**: Cannot grant read-only access to `GetQuote` without also granting access to `ShipOrder`.
- **Recommendation**: Implement method-level authorization via gRPC interceptor.
- **Evidence**: `main.go`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK
- **Finding**: No action-level authorization. No ABAC, no fine-grained RBAC.
- **Gap**: Cannot enforce read vs write distinction per caller.
- **Recommendation**: Add gRPC interceptor mapping principals to allowed methods.
- **Evidence**: `main.go`, `genproto/demo_grpc.pb.go`

#### AUTH-Q4: Identity Propagation
- **Severity**: RISK
- **Finding**: No JWT parsing, no OAuth2 token exchange, no user context in gRPC metadata.
- **Gap**: Cannot propagate originating user context through requests.
- **Recommendation**: Add gRPC metadata extraction for identity tokens.
- **Evidence**: `main.go`

#### AUTH-Q5: Agent-as-Self vs Agent-on-Behalf-of-User
- **Severity**: RISK
- **Finding**: No distinction between agent identity modes. No separate credentials or audit fields.
- **Gap**: Cannot differentiate agent-as-self from agent-on-behalf-of-user.
- **Recommendation**: Define separate credential types for each mode.
- **Evidence**: `main.go`

#### AUTH-Q6: Credential Management
- **Severity**: RISK
- **Finding**: No hardcoded credentials found. No secrets management integration. GCP Profiler uses environment-based auth.
- **Gap**: No secrets management system for when authentication is added.
- **Recommendation**: Integrate with AWS Secrets Manager when implementing auth.
- **Evidence**: `main.go`, `Dockerfile`, `go.mod`

#### AUTH-Q7: Immutable Audit Logging ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: Structured JSON logging configured (logrus JSONFormatter). Logs are generic with no caller identity. No immutable storage.
- **Gap**: No principal attribution in logs. No immutable log storage.
- **Recommendation**: Add caller identity to log entries. Configure immutable log storage.
- **Evidence**: `main.go` (lines 39–49, 97–110)

#### AUTH-Q8: Agent Identity Suspension
- **Severity**: RISK
- **Finding**: No mechanism for suspending agent identities. No authentication framework to provide suspension.
- **Gap**: Cannot suspend a misbehaving agent without shutting down the service.
- **Recommendation**: Implement per-identity revocation when adding authentication.
- **Evidence**: `main.go`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: No compensation or rollback logic. `ShipOrder` generates a random tracking ID — one-way operation.
- **Gap**: No way to cancel or reverse a shipment.
- **Recommendation**: Add `CancelShipment` RPC. Implement shipment lifecycle state machine.
- **Evidence**: `main.go`, `tracker.go`

#### STATE-Q2: Queryable Current State
- **Severity**: RISK
- **Finding**: Service is entirely stateless. No stored state, no query endpoints.
- **Gap**: Cannot query shipment status or historical quotes.
- **Recommendation**: Add `GetShipmentStatus` RPC with persistent data store.
- **Evidence**: `main.go`, `tracker.go`

#### STATE-Q3: Concurrency Controls
- **Severity**: RISK
- **Finding**: No concurrency controls. Stateless design minimizes risk. Go 1.25+ provides safe global rand.
- **Gap**: No concurrency controls for future stateful features.
- **Recommendation**: Implement optimistic locking when adding persistence.
- **Evidence**: `tracker.go`, `go.mod`, `main.go`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK
- **Finding**: No circuit breakers for core operations. Profiler init has retry logic. No external dependencies for core RPCs.
- **Gap**: No resilience patterns for future external dependencies.
- **Recommendation**: Implement circuit breakers when adding external service calls.
- **Evidence**: `main.go`, `quote.go`, `tracker.go`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK
- **Finding**: No rate limiting. No API Gateway, no WAF, no interceptors for throttling.
- **Gap**: Runaway agent loop could overwhelm the service.
- **Recommendation**: Add gRPC rate limiting interceptor.
- **Evidence**: `main.go`

#### STATE-Q6: Blast Radius and Transaction Limits
- **Severity**: RISK
- **Finding**: No transaction limits per agent identity.
- **Gap**: No configurable blast radius controls.
- **Recommendation**: Implement per-identity transaction limits.
- **Evidence**: `main.go`, no configuration files

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: RISK
- **Finding**: No load testing, no auto-scaling, no capacity planning.
- **Gap**: Unknown capacity limits for agent traffic patterns.
- **Recommendation**: Run load tests. Define auto-scaling policies.
- **Evidence**: `Dockerfile`

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State
- **Severity**: RISK
- **Finding**: No draft/pending state. Service is stateless. `ShipOrder` immediately returns a tracking ID.
- **Gap**: No ability for human review before shipment execution.
- **Recommendation**: Add `CreatePendingShipment` and `ConfirmShipment` RPCs.
- **Evidence**: `main.go`

#### HITL-Q2: Configurable Approval Gates
- **Severity**: RISK
- **Finding**: No approval workflow. No human-in-the-loop gates. No Step Functions with approval tasks.
- **Gap**: No mechanism to require human approval for high-risk operations.
- **Recommendation**: Add configurable approval gates at the service level.
- **Evidence**: No approval-related code in any repository file

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK
- **Finding**: Dockerfile exists. No docker-compose, no staging config, no seed data, no environment-specific configuration.
- **Gap**: No sandbox/staging environment for agent testing.
- **Recommendation**: Create docker-compose.yml and environment-specific configurations.
- **Evidence**: `Dockerfile`, `README.md`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: `Address` message includes PII fields (street_address, city, state, country, zip_code). The broader proto includes CreditCardInfo and email. No data classification tags or field-level access controls.
- **Gap**: PII processed without classification or access controls.
- **Recommendation**: Document data classification. Add field-level access controls via gRPC interceptor.
- **Evidence**: `genproto/demo.pb.go` (lines 917–927), `main.go` (lines 107–114)

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: No data residency documentation. Service is stateless but processes address PII in transit. No GDPR/LGPD references.
- **Gap**: No documented data residency requirements.
- **Recommendation**: Document data residency requirements. Ensure agent orchestration respects jurisdictional boundaries.
- **Evidence**: `genproto/demo.pb.go` (lines 917–927)

#### DATA-Q3: Selective Query Support
- **Severity**: RISK
- **Finding**: Two RPCs with fixed, small responses. No pagination, filtering, or sorting needed.
- **Gap**: No selective query mechanism (low impact for current API).
- **Recommendation**: Add pagination if API evolves to return lists.
- **Evidence**: `genproto/demo.pb.go`

#### DATA-Q4: System of Record Designations
- **Severity**: RISK
- **Finding**: No system-of-record documentation. No data ownership definitions.
- **Gap**: No documented data authority.
- **Recommendation**: Create data ownership matrix.
- **Evidence**: No data ownership documentation

#### DATA-Q5: Reliable Timestamps
- **Severity**: RISK
- **Finding**: No timestamps in API responses. Log timestamps exist but not in data model.
- **Gap**: Agents cannot determine when data was generated.
- **Recommendation**: Add `google.protobuf.Timestamp` fields to responses.
- **Evidence**: `genproto/demo.pb.go`, `main.go`

#### DATA-Q6: Data Freshness Signaling
- **Severity**: RISK
- **Finding**: No freshness signaling. Service computes in real-time. No caching.
- **Gap**: Protocol does not signal data freshness.
- **Recommendation**: Add freshness metadata to gRPC responses.
- **Evidence**: `main.go`, `quote.go`

#### DATA-Q7: PII Redaction in Logs
- **Severity**: RISK
- **Finding**: Current logs do not contain PII. Address data used in computation but not logged. No log scrubbing framework.
- **Gap**: No systematic PII protection in logging.
- **Recommendation**: Add log scrubbing middleware/hook.
- **Evidence**: `main.go` (lines 97–112)

#### DATA-Q8: Data Quality Awareness
- **Severity**: INFO
- **Finding**: Service is stateless. No data quality metrics applicable. Hardcoded $8.99 shipping rate.
- **Gap**: No data quality monitoring (not applicable for current implementation).
- **Recommendation**: Add quality monitoring when integrating real carrier data.
- **Evidence**: `quote.go`, `tracker.go`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Documentation and Versioning
- **Severity**: RISK
- **Finding**: Generated protobuf code committed to repo. Source `.proto` external. `protoc v3.6.1` is outdated. No schema versioning.
- **Gap**: Schema source external. No versioning strategy. Outdated protoc.
- **Recommendation**: Include `.proto` file. Add CI validation. Update protoc.
- **Evidence**: `genproto.sh`, `genproto/demo_grpc.pb.go`, `genproto/demo.pb.go`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Field names are clear: `product_id`, `quantity`, `street_address`, `city`, `currency_code`, `tracking_id`. No legacy abbreviations.
- **Gap**: N/A — positive finding.
- **Recommendation**: Maintain naming conventions. Add field-level comments in proto.
- **Evidence**: `genproto/demo.pb.go`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No data catalog. No metadata files. Proto definition serves as de facto metadata.
- **Gap**: No centralized metadata discovery.
- **Recommendation**: Consider service catalog (e.g., Backstage) for broader platform.
- **Evidence**: No metadata files

#### DISC-Q4: Data Lineage
- **Severity**: INFO
- **Finding**: No data lineage tools or documentation.
- **Gap**: Cannot trace data origin through service calls.
- **Recommendation**: Implement request-level tracing (OBS-Q1) as lightweight lineage.
- **Evidence**: No lineage documentation

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK
- **Finding**: Structured JSON logging configured (logrus JSONFormatter with `timestamp`, `severity`, `message`). Distributed tracing NOT implemented — `initTracing()` and `initStats()` are TODO stubs. OpenTelemetry is indirect dependency only. No trace ID propagation, no correlation IDs.
- **Gap**: No distributed tracing. No correlation IDs in logs.
- **Recommendation**: Implement OpenTelemetry tracing with `otelgrpc` interceptor. Add trace_id to log entries.
- **Evidence**: `main.go` (lines 39–49, 124, 128), `go.mod`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK
- **Finding**: No alerting configuration. gRPC health checking is implemented but no error rate or latency alerting.
- **Gap**: No proactive alerting for service degradation.
- **Recommendation**: Define CloudWatch alarms for gRPC error rates and P95 latency.
- **Evidence**: `main.go` (lines 87–88)

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics. No metric publication code.
- **Gap**: No business-level signals for agent outcome quality.
- **Recommendation**: Add custom metrics for quotes/shipments per minute.
- **Evidence**: `main.go`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance
- **Severity**: RISK
- **Finding**: No IaC files in repository. No Terraform, CloudFormation, CDK, Helm, or Kustomize. Dockerfile exists for container build only.
- **Gap**: Infrastructure not defined as code in this repository.
- **Recommendation**: Define service infrastructure as IaC. Subject changes to peer review.
- **Evidence**: No IaC files, `Dockerfile`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK
- **Finding**: No CI/CD configuration. No contract testing. No breaking change detection.
- **Gap**: No automated pipeline for testing or deploying.
- **Recommendation**: Create CI pipeline with `go test`, `buf breaking`, and contract tests.
- **Evidence**: No CI/CD files, `shippingservice_test.go`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK
- **Finding**: No deployment or rollback configuration. No blue/green, canary, or feature flags.
- **Gap**: No mechanism to roll back broken deployments.
- **Recommendation**: Implement deployment strategy with automatic rollback triggers.
- **Evidence**: `Dockerfile`, no deployment configuration

#### ENG-Q4: API Test Coverage
- **Severity**: RISK
- **Finding**: 11 unit test functions in `shippingservice_test.go` with good happy-path coverage. No error case tests, no contract tests, no CI pipeline.
- **Gap**: Missing error case tests and CI integration.
- **Recommendation**: Add error case tests. Create CI pipeline. Add coverage reporting.
- **Evidence**: `shippingservice_test.go`

#### ENG-Q5: Encryption at Rest
- **Severity**: RISK
- **Finding**: No encryption configuration. Service is stateless with no data stores.
- **Gap**: No encryption at rest configuration (not applicable currently but needed when persistence is added).
- **Recommendation**: Ensure encryption at rest when adding data persistence.
- **Evidence**: No IaC files, `main.go`

#### ENG-Q6: Cross-Origin and Network Policies
- **Severity**: BLOCKER
- **Finding**: gRPC server listens on port 50051 with no TLS, no network restrictions, no firewall rules, no security groups, no service mesh. Plaintext connections from any source.
- **Gap**: No network security controls. Plaintext transport including PII.
- **Recommendation**: Add TLS. Define network policies as IaC.
- **Evidence**: `main.go` (line 75), `Dockerfile` (EXPOSE 50051)

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `main.go` | API-Q1, API-Q2, API-Q3, API-Q4, API-Q6, API-Q7, API-Q8, API-Q9, API-Q10, AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q6, AUTH-Q7, AUTH-Q8, STATE-Q1, STATE-Q2, STATE-Q3, STATE-Q4, STATE-Q5, STATE-Q6, HITL-Q1, DATA-Q1, DATA-Q5, DATA-Q6, DATA-Q7, OBS-Q1, OBS-Q2, OBS-Q3, ENG-Q5, ENG-Q6 |
| `quote.go` | API-Q4, API-Q7, API-Q10, STATE-Q4, DATA-Q6, DATA-Q8 |
| `tracker.go` | API-Q4, API-Q7, API-Q10, STATE-Q1, STATE-Q2, STATE-Q3, STATE-Q4, DATA-Q8 |
| `shippingservice_test.go` | ENG-Q2, ENG-Q4 |
| `genproto/demo_grpc.pb.go` | API-Q1, API-Q2, API-Q5, API-Q6, AUTH-Q3 |
| `genproto/demo.pb.go` | API-Q1, API-Q6, DATA-Q1, DATA-Q2, DATA-Q3, DATA-Q5, DISC-Q1, DISC-Q2 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `Dockerfile` | AUTH-Q6, STATE-Q7, HITL-Q3, ENG-Q3, ENG-Q6 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `go.mod` | AUTH-Q6, STATE-Q3, OBS-Q1 |

### Scripts
| File | Questions Referenced |
|------|---------------------|
| `genproto.sh` | API-Q2, DISC-Q1 |

### Documentation
| File | Questions Referenced |
|------|---------------------|
| `README.md` | HITL-Q3 |
