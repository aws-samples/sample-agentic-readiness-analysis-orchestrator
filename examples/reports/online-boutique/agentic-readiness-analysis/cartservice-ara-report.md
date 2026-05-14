# Agentic Readiness Analysis Report

**Target**: ./services/microservices-demo/src/cartservice
**Date**: 2026-04-16
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**Repository Type**: application
**Service Archetype**: stateful-crud (user-provided)
**Agent Scope**: read-only
**Priority**: P0
**Tags**: csharp, grpc, redis, stateful
**Context**: C# gRPC service managing shopping carts with Redis backing store.

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 2 | **RISKs**: 27 | **INFOs**: 10

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 2 |
| RISK | 27 |
| INFO | 10 |
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

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: The cartservice gRPC application has no authentication middleware at the application layer. No OAuth2 client credentials flow, no API key authentication, no mTLS configuration in application code. `Startup.cs` configures gRPC endpoints (`MapGrpcService<CartService>()`) with no authentication/authorization middleware in the pipeline. A Kubernetes ServiceAccount named `cartservice` exists in the Helm chart, but this is pod-level identity, not request-level authentication. Istio AuthorizationPolicy is defined in `helm-chart/templates/cartservice.yaml` but is disabled by default (`authorizationPolicies.create: false` in `helm-chart/values.yaml`). No audit logging of authenticated principal — `Console.WriteLine` logs include `userId` but not the calling service identity.
- **Gap**: No mechanism exists to authenticate an agent calling this service or to attribute gRPC calls to a specific machine identity in audit logs. Any client with network access to port 7070 can call all three RPCs (`AddItem`, `GetCart`, `EmptyCart`) without presenting credentials.
- **Remediation**:
  - **Immediate**: Enable Istio AuthorizationPolicies by setting `authorizationPolicies.create: true` in Helm values. This provides mTLS-based service identity authentication using Kubernetes ServiceAccount principals. The existing Helm chart template already defines per-operation authorization rules restricting access to frontend and checkoutservice principals.
  - **Target State**: Every gRPC call to cartservice is authenticated with a verifiable machine identity. Audit logs include the authenticated principal for every request. Agent-specific service accounts are created with scoped access to only the `GetCart` operation for read-only agents.
  - **Estimated Effort**: Low (Istio AuthorizationPolicy enablement) to Medium (application-level auth with interceptors)
  - **Dependencies**: AUTH-Q6 (audit logging)
- **Evidence**: `src/Startup.cs`, `src/services/CartService.cs`, `helm-chart/templates/cartservice.yaml`, `helm-chart/values.yaml`

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: No data classification exists at any level. Cart data stored in Redis, Spanner, or AlloyDB contains `userId` (string), `productId` (string), and `quantity` (int32) as defined in `Cart.proto`. The `userId` field is a PII-candidate depending on format (could be email, phone number, or opaque UUID). No data classification tags on the Redis `emptyDir` volume. No field-level encryption in any cart store implementation. No PII detection tools. No `DATA_CLASSIFICATION.md` file exists in the repository. The AlloyDB cart store (`AlloyDBCartStore.cs`) stores data in a table with columns `userId`, `productId`, `quantity` with no classification metadata.
- **Gap**: Sensitive data in the cart (particularly `userId`) is not classified or tagged, and there are no controls preventing an agent from retrieving it without explicit authorization. Without classification, data governance policies cannot be enforced.
- **Remediation**:
  - **Immediate**: Classify the `userId` field as PII-candidate. Document the classification in a `DATA_CLASSIFICATION.md` file. If `userId` is an opaque session token or UUID, document that determination. If it contains email or identifiable information, treat it as PII and implement field-level access controls.
  - **Target State**: All fields in the cart data model are classified (PII, sensitive, public). Classification tags are applied to infrastructure resources (Redis/Spanner/AlloyDB). Field-level access controls enforce that agent identities can only access non-sensitive fields unless explicitly authorized.
  - **Estimated Effort**: Low (classification documentation) to Medium (field-level encryption and access controls)
  - **Dependencies**: AUTH-Q1 (identity must exist before data access controls can be enforced)
- **Evidence**: `src/protos/Cart.proto`, `src/cartstore/RedisCartStore.cs`, `src/cartstore/SpannerCartStore.cs`, `src/cartstore/AlloyDBCartStore.cs`

## RISKs — Proceed with Compensating Controls

### API-Q2: Machine-Readable API Specification

- **Severity**: RISK
- **Finding**: `Cart.proto` serves as the machine-readable specification. Protocol Buffer files define service methods, request/response types with fully typed fields. Proto files are auto-consumed by gRPC tooling (code generation, client libraries). The proto file is compiled via `cartservice.csproj` (`<Protobuf Include="protos\Cart.proto" GrpcServices="Both" />`), ensuring it stays in sync with the implementation. However, no `buf.yaml` configuration exists for linting or breaking change detection.
- **Gap**: While the proto file is functionally equivalent to an OpenAPI spec for gRPC services, there is no schema registry, no breaking change detection tooling, and no published proto artifact for external consumers.
- **Compensating Controls**:
  - Proto compilation dependency ensures the spec stays current with the implementation.
  - Agent tool definitions can be derived directly from the proto file.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `buf` for proto linting and breaking change detection. Consider publishing the proto file to a schema registry for versioned consumption.
- **Evidence**: `src/protos/Cart.proto`, `src/cartservice.csproj`

### API-Q3: Structured Error Responses

- **Severity**: RISK
- **Finding**: All cart store implementations (`RedisCartStore.cs`, `SpannerCartStore.cs`, `AlloyDBCartStore.cs`) throw `RpcException` with `StatusCode.FailedPrecondition` and a string message (e.g., `"Can't access cart storage. {ex}"`). gRPC status codes provide basic error categorization, but there are no structured error codes, no retryable boolean, and no error categorization beyond the single status code. All errors — whether transient (Redis connection timeout) or permanent (invalid data) — are surfaced as the same `FailedPrecondition` status.
- **Gap**: Agents cannot distinguish retriable errors from terminal errors. A Redis timeout and a data corruption error produce the same gRPC status code.
- **Compensating Controls**:
  - Agent-side retry logic can treat `FailedPrecondition` as retriable with exponential backoff, since the most common cause is transient storage unavailability.
  - Wrap agent tool calls with timeout-based retry, limiting retry count to 3.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement a gRPC interceptor that classifies exceptions into retriable vs. terminal categories and returns structured error metadata in gRPC trailing metadata (e.g., `x-error-code`, `x-retryable`).
- **Evidence**: `src/cartstore/RedisCartStore.cs`, `src/cartstore/SpannerCartStore.cs`, `src/cartstore/AlloyDBCartStore.cs`

### AUTH-Q2: Scoped Permissions (Least Privilege)

- **Severity**: RISK
- **Finding**: No IAM policies or permission scoping for agent identities at the application level. The Kubernetes manifests define a ServiceAccount `cartservice` but no RBAC roles or role bindings. The Istio AuthorizationPolicy in the Helm chart (when enabled) restricts access by source principal to `frontend` and `checkoutservice` — this provides scoped access at the infrastructure layer. However, the authorization policy is disabled by default (`authorizationPolicies.create: false`). No fine-grained permission model within the application code itself.
- **Gap**: An agent identity, once granted network access to the cartservice, can call all three RPCs with no permission scoping. There is no mechanism to grant an agent read-only access (`GetCart` only) without also granting write access (`AddItem`, `EmptyCart`).
- **Compensating Controls**:
  - Enable Istio AuthorizationPolicy and define an agent-specific principal that is only authorized for `GetCart` operations.
  - Use network policies to restrict which pods can reach cartservice on port 7070.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Enable Istio AuthorizationPolicies and add an agent-specific service account principal with access restricted to `/hipstershop.CartService/GetCart` only.
- **Evidence**: `helm-chart/templates/cartservice.yaml`, `helm-chart/values.yaml`

### AUTH-Q3: Action-Level Authorization

- **Severity**: RISK
- **Finding**: No action-level authorization in application code. The `CartService.cs` gRPC service delegates directly to the cart store with no permission checks. The Helm chart AuthorizationPolicy (when enabled) does define per-operation paths (`/hipstershop.CartService/AddItem`, `/hipstershop.CartService/GetCart`, `/hipstershop.CartService/EmptyCart`) with method-level control — this is infrastructure-level action authorization. However, it is disabled by default.
- **Gap**: Without Istio AuthorizationPolicy enabled, there is no way to allow an agent to read carts but not empty them within the same service.
- **Compensating Controls**:
  - Enable Istio AuthorizationPolicy to enforce per-operation authorization at the service mesh layer.
  - For read-only agent scope, this risk is partially mitigated by not granting write tool definitions to the agent.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Enable Istio AuthorizationPolicy. For defense-in-depth, add a gRPC server interceptor that validates operation-level permissions based on caller identity metadata.
- **Evidence**: `src/services/CartService.cs`, `helm-chart/templates/cartservice.yaml`

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: RISK
- **Finding**: No JWT parsing middleware, no OAuth2 token exchange, no user context propagation in the application code. The `userId` field in gRPC requests (`AddItemRequest.user_id`, `GetCartRequest.user_id`, `EmptyCartRequest.user_id`) is a plain string parameter passed by the caller — there is no verification that the caller is authorized to access that user's cart. Any caller can pass any `userId` and access any user's cart data. No distinction between service identity and delegated user identity. The application has no concept of "who is calling" vs. "on whose behalf." No separate auth flows for service-to-service calls vs. user-delegated calls.
- **Gap**: The system cannot verify that an agent acting on behalf of a user is authorized to access that specific user's cart. Identity propagation does not exist — the `userId` is trusted without verification. Cannot distinguish between an agent querying a cart for its own analytical purposes and an agent querying a cart on behalf of a specific user.
- **Compensating Controls**:
  - Restrict agent access to only its own designated test user IDs via agent configuration.
  - Enforce user ID allowlists at the orchestration layer before calling the cart service.
  - For read-only scope, restrict agent to service-as-self mode with documentation that all cart reads are attributed to the agent identity.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement a gRPC interceptor that validates the `userId` in requests against the authenticated caller's authorized scope. Implement request-level identity headers (e.g., `x-agent-identity`, `x-on-behalf-of`) validated by the interceptor.
- **Evidence**: `src/protos/Cart.proto`, `src/services/CartService.cs`, `src/cartstore/RedisCartStore.cs`

### AUTH-Q5: Credential Management

- **Severity**: RISK
- **Finding**: Mixed credential management practices. AlloyDB store uses Google Cloud Secret Manager (`Google.Cloud.SecretManager.V1` in `AlloyDBCartStore.cs`) to retrieve database passwords — this is best practice. However, the TODO comment notes: "Create a separate user for connecting within the application rather than using our superuser" — the service connects as `postgres` superuser. Redis connection uses the `REDIS_ADDR` environment variable containing only host:port (`redis-cart:6379`) — no authentication required for in-cluster Redis. Spanner uses GCP application default credentials. No hardcoded secrets found in source code.
- **Gap**: Redis has no authentication (password-less), which means any pod with network access can read/write all cart data. AlloyDB uses superuser credentials rather than a least-privilege application user. No credential rotation mechanism documented.
- **Compensating Controls**:
  - Network policies (when enabled) restrict Redis access to only the cartservice pod, partially mitigating the lack of Redis authentication.
  - For read-only agent scope, the agent does not connect to Redis directly — it calls the gRPC API.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Enable Redis AUTH with a password stored in Kubernetes Secrets or Secret Manager. Create a dedicated AlloyDB application user with least-privilege permissions instead of `postgres` superuser.
- **Evidence**: `src/cartstore/AlloyDBCartStore.cs`, `src/cartstore/RedisCartStore.cs`, `src/Startup.cs`, `helm-chart/values.yaml`


### AUTH-Q6: Immutable Audit Logging ⚡

- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: No audit logging configured at any level. The application uses `Console.WriteLine` for operational logging (e.g., `"AddItemAsync called with userId={userId}"`, `"GetCartAsync called with userId={userId}"`), but these are unstructured console logs with no principal attribution, no request metadata, and no immutable storage. No CloudTrail or equivalent audit service configured in Terraform IaC. No S3 bucket with object lock for logs. The Terraform `main.tf` enables `cloudtrace.googleapis.com` and `monitoring.googleapis.com` APIs but no audit logging services.
- **Gap**: No immutable audit trail exists. Cannot prove which service or agent accessed which user's cart data. Forensics and compliance auditing are impossible.
- **Compensating Controls**:
  - Enable GKE audit logging at the cluster level (Kubernetes API audit logs).
  - For Istio-enabled deployments, Istio access logs provide request-level audit with source/destination identity.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement structured JSON logging with principal attribution. Configure GKE audit logging. Enable Istio access logs for request-level audit trails. Store logs in an immutable destination (e.g., BigQuery with access controls or Cloud Logging with retention policies).
- **Evidence**: `src/cartstore/RedisCartStore.cs`, `src/cartstore/SpannerCartStore.cs`, `src/services/CartService.cs`, `terraform/main.tf`

### AUTH-Q7: Agent Identity Suspension

- **Severity**: RISK
- **Finding**: No mechanism to suspend individual agent identities without broader platform impact. No API key revocation endpoints. No agent-specific service account disable capability in the application. If Istio AuthorizationPolicies are enabled, removing a principal from the policy would block access, but this requires a Helm/Kubernetes deployment change — not an immediate suspension action.
- **Gap**: If an agent exhibits anomalous behavior, there is no rapid kill switch to suspend that specific agent without affecting other services or deploying configuration changes.
- **Compensating Controls**:
  - Network policies can be updated to block specific source pods, though this requires kubectl access.
  - Agent orchestration layer can implement a circuit breaker that stops tool invocations.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement agent identity as distinct Kubernetes ServiceAccounts. Create a runbook for immediate suspension via `kubectl delete serviceaccount` or Istio AuthorizationPolicy update.
- **Evidence**: `helm-chart/templates/cartservice.yaml`, `helm-chart/values.yaml`

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: No saga pattern, no compensation logic, no undo endpoints. `AddItem` modifies quantity cumulatively with no rollback — once quantity is incremented, there is no `RemoveItem` or `UndoAddItem` RPC. `EmptyCart` deletes all items for a user with no undo capability. In Spanner (`SpannerCartStore.cs`), `RunWithRetriableTransactionAsync` provides atomic single-operation transactions, but no multi-step compensation. AlloyDB (`AlloyDBCartStore.cs`) uses `INSERT...ON CONFLICT` for upsert but no compensation.
- **Gap**: Multi-step operations that fail mid-sequence leave the cart in a partial state with no recovery mechanism.
- **Compensating Controls**:
  - For read-only agent scope, the agent does not execute write workflows, so compensation risk is lower.
  - Agent orchestration layer can implement saga-style compensation for multi-step reads if needed.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement a `RemoveItem` RPC for granular cart management. For write-enabled scope, consider implementing an event-sourced cart model with undo capability.
- **Evidence**: `src/services/CartService.cs`, `src/cartstore/RedisCartStore.cs`, `src/cartstore/SpannerCartStore.cs`, `src/cartstore/AlloyDBCartStore.cs`

### STATE-Q5: Rate Limiting and Throttling

- **Severity**: RISK
- **Finding**: No API-level rate limiting. No API Gateway in front of the gRPC service. No application-level rate limiting middleware (no `AspNetCoreRateLimit` or equivalent in `cartservice.csproj`). The service is exposed directly as a Kubernetes ClusterIP service on port 7070 with no throttling layer. Kubernetes resource limits (CPU: 200-300m, Memory: 128-256Mi) provide resource isolation at the container level but not request-level throttling.
- **Gap**: A runaway agent loop calling `GetCart` at machine speed can consume all CPU/memory allocated to the cartservice pod, degrading service for other consumers (frontend, checkoutservice).
- **Compensating Controls**:
  - Kubernetes resource limits prevent the pod from consuming cluster-wide resources.
  - Agent orchestration layer can enforce request-per-second limits on tool invocations.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add gRPC rate limiting middleware or deploy an Envoy sidecar with rate limiting in front of the service.
- **Evidence**: `src/Startup.cs`, `src/cartservice.csproj`, `helm-chart/templates/cartservice.yaml`

### HITL-Q3: Sandbox/Staging Environment

- **Severity**: RISK
- **Finding**: The CI/CD pipeline (`.github/workflows/ci-pr.yaml`) deploys PR-specific namespaces to a GKE cluster for testing — this provides temporary staging environments. Skaffold (`skaffold.yaml`) is configured for local development. The application supports an in-memory cache fallback when `REDIS_ADDR` is not set (`Startup.cs`), enabling local testing without Redis infrastructure. However: no Docker Compose file for self-contained local testing. No synthetic data generators or seed data scripts. The test environment uses in-memory cache, not Redis, so it does not match production data behavior.
- **Gap**: While PR environments and local development exist, there is no sandbox with production-equivalent data shape. The in-memory fallback does not replicate Redis persistence characteristics. No dedicated agent testing environment.
- **Compensating Controls**:
  - Use PR-deployed environments for agent integration testing.
  - Local testing with Skaffold + Minikube provides a basic sandbox.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a dedicated agent-testing namespace with Redis and seed data. Add a Docker Compose file for self-contained local development with Redis.
- **Evidence**: `.github/workflows/ci-pr.yaml`, `skaffold.yaml`, `src/Startup.cs`

### DATA-Q2: Data Residency and Sovereignty ⚡

- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: No data residency requirements documented anywhere in the repository. Terraform deploys to `us-central1` by default (`terraform/variables.tf`). Memorystore Redis is deployed in the same region. No GDPR, LGPD, or data sovereignty compliance references. No cross-region replication configuration. Cart data (userId, productId, quantity) may be subject to residency requirements depending on the business context.
- **Gap**: No documented data residency posture. If cart data contains PII subject to GDPR (e.g., EU user IDs), sending it to an LLM endpoint outside the EU may create a legal violation.
- **Compensating Controls**:
  - For read-only agent scope, configure the agent to use LLM endpoints in the same region as the data store (`us-central1`).
  - Document the data residency determination and update as business context evolves.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Conduct a data residency analysis. Document whether cart data is subject to any residency or sovereignty requirements. If so, configure the agent's LLM endpoint to respect those boundaries.
- **Evidence**: `terraform/variables.tf`, `terraform/memorystore.tf`

### DISC-Q1: Schema Versioning and API Contracts

- **Severity**: RISK
- **Finding**: `Cart.proto` defines the schema with typed fields (`CartItem`, `AddItemRequest`, `EmptyCartRequest`, `GetCartRequest`, `Cart`, `Empty`). However, the schema is not versioned — the proto package is `hipstershop` with no version qualifier (e.g., `hipstershop.v1`). No version field in proto messages. No schema registry. No `buf.yaml` for breaking change detection. No database migration files for Spanner or AlloyDB table schemas. The `cartservice.csproj` compiles `Cart.proto` with `GrpcServices="Both"` but there is no proto versioning or backward-compatibility validation.
- **Gap**: Schema changes to `Cart.proto` could break downstream consumers silently. No versioning mechanism to manage schema evolution. No breaking change detection in CI.
- **Compensating Controls**:
  - Proto files are inherently backward-compatible when following proto3 best practices (additive changes only).
  - Pin agent tool definitions to a specific proto file hash.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Adopt proto package versioning (e.g., `hipstershop.cart.v1`). Add `buf` linting and breaking change detection to CI. Create database migration scripts for Spanner/AlloyDB table schemas.
- **Evidence**: `src/protos/Cart.proto`, `src/cartservice.csproj`

### OBS-Q1: Distributed Tracing and Structured Logging

- **Severity**: RISK
- **Finding**: No distributed tracing instrumentation in the application. No OpenTelemetry SDK imports in `cartservice.csproj`. No X-Ray instrumentation. No `traceparent` header propagation. The Helm chart defines an optional OpenTelemetry collector (`opentelemetryCollector.create: true` in `helm-chart/values.yaml`), but the application code has no OTel instrumentation to emit traces even if the collector is enabled. Logging uses `Console.WriteLine` exclusively — unstructured text format, no JSON logging, no correlation IDs, no `request_id` field. Tracing is disabled in the analysis context (`tracing: false`).
- **Gap**: Agent-initiated requests that fail inside the cartservice cannot be traced end-to-end. No correlation between agent tool call → gRPC request → cart store operation. Diagnosis requires manual log correlation by timestamp.
- **Compensating Controls**:
  - Istio sidecar proxy (if enabled) provides basic request-level tracing without application instrumentation.
  - GKE Cloud Logging captures container stdout, enabling timestamp-based correlation.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenTelemetry .NET SDK (`OpenTelemetry.Extensions.Hosting`, `OpenTelemetry.Instrumentation.GrpcNetClient`, `OpenTelemetry.Instrumentation.StackExchangeRedis`). Replace `Console.WriteLine` with `ILogger<T>` and configure JSON structured logging with correlation IDs.
- **Evidence**: `src/cartservice.csproj`, `src/Startup.cs`, `src/cartstore/RedisCartStore.cs`, `helm-chart/values.yaml`

### OBS-Q2: Alerting on Error Rates and Latency

- **Severity**: RISK
- **Finding**: No alerting configuration found anywhere in the repository. No Cloud Monitoring alerting policies. No PagerDuty or OpsGenie integration. No SLO-based alerting. The gRPC health check service (`HealthCheckService.cs`) reports serving status based on `_cartStore.Ping()`, but this is a liveness/readiness signal for Kubernetes — not proactive alerting. The Terraform `main.tf` enables `monitoring.googleapis.com` API but defines no alert policies.
- **Gap**: Target system degradation (Redis connection failures, Spanner latency spikes) is not alerted on. Agents will fail silently, and operators will not know until agents report errors at the orchestration layer.
- **Compensating Controls**:
  - gRPC health probes in Kubernetes detect and restart unhealthy pods automatically.
  - Agent orchestration layer can implement health monitoring of downstream services.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create Cloud Monitoring alerting policies for: gRPC error rate > 1%, P95 latency > 500ms, Redis connection failures. Configure notification channels.
- **Evidence**: `src/services/HealthCheckService.cs`, `terraform/main.tf`, `helm-chart/values.yaml`

### ENG-Q1: Infrastructure Governance for Agent-Facing Surface

- **Severity**: RISK
- **Finding**: Terraform IaC defines the GKE cluster (`main.tf`) and optional Memorystore Redis (`memorystore.tf`). Kubernetes manifests define the deployment topology. Helm chart provides templated deployment. Terraform validation CI exists (`.github/workflows/terraform-validate-ci.yaml`) running `terraform init` and `terraform validate` on changes. However: (1) No explicit Terraform plan review step in CI. (2) No drift detection. (3) No peer review enforcement specifically for IaC changes.
- **Gap**: IaC changes to the agent-facing surface can be applied without plan review or drift detection. Infrastructure may drift from declared state without alerting.
- **Compensating Controls**:
  - Terraform validation CI prevents syntax errors from reaching production.
  - PR-based workflow provides opportunity for peer review, even if not enforced.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `terraform plan` output to PR comments for review. Implement drift detection. Enforce required reviews for changes to `terraform/` directories.
- **Evidence**: `terraform/main.tf`, `terraform/memorystore.tf`, `.github/workflows/terraform-validate-ci.yaml`

### ENG-Q2: CI/CD with API Contract Testing

- **Severity**: RISK
- **Finding**: GitHub Actions CI runs C# unit tests (`dotnet test src/cartservice/` in `.github/workflows/ci-pr.yaml`). Deployment tests deploy to GKE and run smoke tests. However: no API contract testing — no Pact, no consumer-driven contracts. No proto schema comparison or breaking change detection (no `buf breaking`). The smoke test validates overall system health but not individual API contract compliance.
- **Gap**: A breaking change to `Cart.proto` (e.g., renaming a field, changing a type) would not be caught by the current CI pipeline until deployment-time smoke tests fail.
- **Compensating Controls**:
  - Proto3 wire format is inherently backward-compatible for additive changes.
  - Unit tests validate basic API behavior (add, get, empty cart).
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `buf` to CI for proto linting and breaking change detection. Implement gRPC contract tests that validate request/response schemas against a pinned proto definition.
- **Evidence**: `.github/workflows/ci-pr.yaml`, `.github/workflows/ci-main.yaml`, `tests/CartServiceTests.cs`

### ENG-Q3: Rollback Capability

- **Severity**: RISK
- **Finding**: Deployment uses Skaffold with `kubectl apply` via Kustomize manifests (`skaffold.yaml`). No explicit rollback triggers. No blue/green deployment configuration. No canary deployment with automatic rollback. No feature flags. Kubernetes deployments support `kubectl rollout undo` as a manual rollback mechanism, but this is not automated. The Helm chart supports `helm rollback` if Helm is used for deployment.
- **Gap**: Rollback is manual and requires kubectl access. No automated rollback on error rate spikes or health check failures.
- **Compensating Controls**:
  - Kubernetes rolling deployment strategy provides some protection — new pods must pass health checks before old pods are terminated.
  - If Helm is used, `helm rollback` provides one-command rollback to previous release.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement automated rollback triggers based on gRPC error rate metrics. Document the `helm rollback` procedure. Consider canary deployment with Istio traffic shifting.
- **Evidence**: `skaffold.yaml`, `cloudbuild.yaml`, `helm-chart/templates/cartservice.yaml`


## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO
- **Finding**: The cartservice exposes a gRPC interface defined in `Cart.proto` with package `hipstershop`. Three RPCs are defined: `AddItem(AddItemRequest) returns (Empty)`, `GetCart(GetCartRequest) returns (Cart)`, `EmptyCart(EmptyCartRequest) returns (Empty)`. The proto file defines strongly-typed request/response messages. This is a documented, typed, machine-readable interface. No direct database access, file-based exchange, or UI automation is required for integration.
- **Implication**: Agents can bind to the gRPC interface using proto-generated client stubs. The interface is stable and well-defined. Tool definitions can be auto-generated from the proto file.
- **Recommendation**: The gRPC interface meets the minimum viable integration surface requirement. No action needed.
- **Evidence**: `src/protos/Cart.proto`, `src/services/CartService.cs`

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: `AddItem` is not idempotent — calling it twice with the same parameters doubles the quantity (quantity is cumulative). In `RedisCartStore.cs`: `existingItem.Quantity += quantity`. In `SpannerCartStore.cs`: `currentQuantity + quantity`. In `AlloyDBCartStore.cs`: `totalQuantity = quantity + currentQuantity`. `EmptyCart` is idempotent. `GetCart` is inherently idempotent (read operation). No idempotency key support in any RPC.
- **Implication**: For read-only agent scope, idempotency is informational only since the agent will only call `GetCart`. If scope expands to write-enabled, `AddItem` idempotency becomes a BLOCKER.
- **Recommendation**: If write-enabled scope is planned, implement idempotency keys for `AddItem` before enabling write access.
- **Evidence**: `src/cartstore/RedisCartStore.cs`, `src/cartstore/SpannerCartStore.cs`, `src/cartstore/AlloyDBCartStore.cs`

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: gRPC with Protocol Buffers is a strongly-typed binary serialization format. Responses are schema-defined (`Cart` message with `user_id` string and repeated `CartItem` messages). Not directly consumable by LLMs (binary wire format), but serializable to JSON via proto's JSON mapping. The format is more compact and faster than JSON but requires proto-aware tooling.
- **Implication**: Agent tool implementations will need a gRPC client stub (generated from proto) rather than raw HTTP/JSON calls. Proto-to-JSON serialization is straightforward and can be done in the tool wrapper.
- **Recommendation**: Consider adding a grpc-gateway or gRPC-Web proxy to expose JSON/HTTP endpoints for simpler agent tool integration.
- **Evidence**: `src/protos/Cart.proto`, `src/cartservice.csproj`

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limiting documentation. No rate limit headers in gRPC responses (no `X-RateLimit-Remaining` or equivalent gRPC metadata). No API Gateway throttle configuration. The service has no awareness of rate limits at the application layer.
- **Implication**: Agents calling the service have no feedback mechanism to self-throttle. Rate limit enforcement (STATE-Q5) is the higher-priority concern; documentation and headers are secondary.
- **Recommendation**: When rate limiting is implemented (STATE-Q5), include rate limit metadata in gRPC response trailing metadata so agents can self-throttle.
- **Evidence**: `src/Startup.cs`, `src/services/CartService.cs`

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits. No maximum records per operation. `EmptyCart` deletes all items for a user with no limit or confirmation. `AddItem` has no maximum quantity per call. No configurable limits per agent identity.
- **Implication**: For read-only agent scope, transaction limits for write operations are informational. `GetCart` reads have no blast radius concern. If scope expands to write-enabled, lack of transaction limits becomes RISK.
- **Recommendation**: For future write-enabled scope, implement configurable operation limits per agent identity.
- **Evidence**: `src/services/CartService.cs`, `src/cartstore/RedisCartStore.cs`

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Field names in `Cart.proto` are human-readable and semantically meaningful: `user_id`, `product_id`, `quantity`, `items`. No legacy codes or abbreviations. The protobuf naming convention uses snake_case, which is standard for proto3. Class names in C# follow PascalCase conventions (`CartService`, `RedisCartStore`, `CartItem`).
- **Implication**: Agent tools and LLM reasoning can interpret field names without a data dictionary. Proto field names map directly to semantic concepts.
- **Recommendation**: No action needed. Maintain naming convention as schema evolves.
- **Evidence**: `src/protos/Cart.proto`

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No data catalog. No metadata layer beyond proto definition. No data dictionary. No description annotations in proto file.
- **Implication**: Agent tool builders derive semantics from field names only. For a simple schema (cart with items), this is sufficient.
- **Recommendation**: Add proto comments on messages and fields. Consider service catalog for broader discoverability.
- **Evidence**: `src/protos/Cart.proto`

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No custom business metrics. No cart operation metrics (adds, empties, gets per minute). No business KPI dashboards. Terraform enables monitoring API but no custom metrics defined.
- **Implication**: Cannot measure agent effectiveness or impact on cart operations. No business-level signal for agent interaction quality.
- **Recommendation**: Publish custom metrics via Cloud Monitoring or OpenTelemetry. Track agent traffic separately from human traffic.
- **Evidence**: `src/services/CartService.cs`, `terraform/main.tf`


## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: The cartservice exposes a gRPC interface defined in `Cart.proto` with package `hipstershop`. Three RPCs: `AddItem`, `GetCart`, `EmptyCart`. Strongly-typed request/response messages. No direct database access, file-based exchange, or UI automation required.
- **Gap**: N/A — gRPC interface is the sole integration surface.
- **Recommendation**: No action needed. The gRPC interface meets the minimum viable integration surface requirement.
- **Evidence**: `src/protos/Cart.proto`, `src/services/CartService.cs`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK
- **Finding**: `Cart.proto` serves as the machine-readable specification. Compiled via `cartservice.csproj`. No `buf.yaml` for linting or breaking change detection. No schema registry.
- **Gap**: No breaking change detection tooling. No published proto artifact for external consumers.
- **Recommendation**: Add `buf` for proto linting and breaking change detection. Publish proto to schema registry.
- **Evidence**: `src/protos/Cart.proto`, `src/cartservice.csproj`

#### API-Q3: Structured Error Responses
- **Severity**: RISK
- **Finding**: All cart store implementations throw `RpcException` with `StatusCode.FailedPrecondition` and a string message. No structured error codes, no retryable boolean. All errors surfaced as the same status code.
- **Gap**: Agents cannot distinguish retriable errors from terminal errors.
- **Recommendation**: Implement gRPC interceptor with structured error metadata in trailing metadata.
- **Evidence**: `src/cartstore/RedisCartStore.cs`, `src/cartstore/SpannerCartStore.cs`, `src/cartstore/AlloyDBCartStore.cs`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: `AddItem` is not idempotent — quantity is cumulative. `EmptyCart` is idempotent. `GetCart` is inherently idempotent. No idempotency key support.
- **Gap**: Non-idempotent `AddItem` is informational for read-only scope.
- **Recommendation**: Implement idempotency keys for `AddItem` before enabling write-enabled scope.
- **Evidence**: `src/cartstore/RedisCartStore.cs`, `src/cartstore/SpannerCartStore.cs`, `src/cartstore/AlloyDBCartStore.cs`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: gRPC with Protocol Buffers — strongly-typed binary serialization. Schema-defined responses. Serializable to JSON via proto JSON mapping.
- **Gap**: N/A — proto format is well-structured.
- **Recommendation**: Consider grpc-gateway for JSON/HTTP endpoints for simpler agent integration.
- **Evidence**: `src/protos/Cart.proto`, `src/cartservice.csproj`

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has operations >30s OR long-running workflows
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: No event emission found. No webhook endpoints. No SNS, EventBridge, SQS, Kafka, or Pub/Sub integration. Cart state changes are not published to any event stream. The service operates in pure request-response mode.
- **Gap**: Agents cannot subscribe to cart change events for proactive behavior. Monitoring requires polling `GetCart`.
- **Recommendation**: For future proactive agent patterns, consider publishing cart events to Google Cloud Pub/Sub.
- **Evidence**: `src/services/CartService.cs`, `src/cartstore/RedisCartStore.cs`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limiting documentation. No rate limit headers in gRPC responses. No API Gateway throttle configuration.
- **Gap**: Agents have no feedback mechanism to self-throttle.
- **Recommendation**: When rate limiting is implemented (STATE-Q5), include rate limit metadata in gRPC trailing metadata.
- **Evidence**: `src/Startup.cs`, `src/services/CartService.cs`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: No authentication middleware. No OAuth2 client credentials, no API key auth, no mTLS in application code. Istio AuthorizationPolicy available but disabled (`authorizationPolicies.create: false`). Any client with network access to port 7070 can call all RPCs.
- **Gap**: No mechanism to authenticate an agent or attribute gRPC calls to a machine identity.
- **Recommendation**: Enable Istio AuthorizationPolicies. Create agent-specific service accounts scoped to `GetCart` only.
- **Evidence**: `src/Startup.cs`, `src/services/CartService.cs`, `helm-chart/templates/cartservice.yaml`, `helm-chart/values.yaml`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK
- **Finding**: No agent-specific permission scoping. Istio AuthorizationPolicy (disabled) restricts by source principal. No fine-grained permission model in application code.
- **Gap**: Cannot grant agent read-only access (`GetCart` only) without also granting write access.
- **Recommendation**: Enable Istio AuthorizationPolicies with agent-specific principal restricted to `/hipstershop.CartService/GetCart`.
- **Evidence**: `helm-chart/templates/cartservice.yaml`, `helm-chart/values.yaml`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK
- **Finding**: No action-level authorization in application code. Helm chart AuthorizationPolicy (disabled) defines per-operation paths.
- **Gap**: Without Istio AuthorizationPolicy enabled, no per-operation access control.
- **Recommendation**: Enable Istio AuthorizationPolicy. Add gRPC server interceptor for defense-in-depth.
- **Evidence**: `src/services/CartService.cs`, `helm-chart/templates/cartservice.yaml`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: RISK
- **Finding**: No JWT parsing, no token exchange, no user context propagation. `userId` is a plain string trusted without verification. No distinction between service identity and delegated user identity. No separate auth flows for service-to-service vs user-delegated calls.
- **Gap**: Cannot verify agent is authorized to access a specific user's cart. Cannot distinguish agent-as-self from agent-on-behalf-of-user.
- **Recommendation**: Implement gRPC interceptor validating `userId` against caller's authorized scope. Add identity headers for agent vs. user distinction.
- **Evidence**: `src/protos/Cart.proto`, `src/services/CartService.cs`, `src/cartstore/RedisCartStore.cs`

#### AUTH-Q5: Credential Management
- **Severity**: RISK
- **Finding**: AlloyDB uses Secret Manager (best practice) but connects as `postgres` superuser. Redis has no authentication. Spanner uses GCP default credentials. No hardcoded secrets found.
- **Gap**: Redis password-less. AlloyDB uses superuser. No credential rotation documented.
- **Recommendation**: Enable Redis AUTH. Create dedicated AlloyDB application user with least-privilege.
- **Evidence**: `src/cartstore/AlloyDBCartStore.cs`, `src/cartstore/RedisCartStore.cs`, `src/Startup.cs`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: No audit logging. `Console.WriteLine` for operational logging — unstructured, no principal attribution, no immutable storage. No CloudTrail equivalent configured.
- **Gap**: No immutable audit trail. Cannot prove which agent accessed which user's cart data.
- **Recommendation**: Implement structured JSON logging with principal attribution. Configure GKE audit logging and Istio access logs.
- **Evidence**: `src/cartstore/RedisCartStore.cs`, `src/cartstore/SpannerCartStore.cs`, `src/services/CartService.cs`, `terraform/main.tf`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK
- **Finding**: No mechanism to suspend individual agent identities. Istio AuthorizationPolicy changes require deployment. No immediate kill switch.
- **Gap**: No rapid suspension capability for misbehaving agents.
- **Recommendation**: Create agent-specific ServiceAccounts with documented suspension runbook.
- **Evidence**: `helm-chart/templates/cartservice.yaml`, `helm-chart/values.yaml`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: No saga pattern, no compensation logic, no undo endpoints. `AddItem` is cumulative with no rollback. `EmptyCart` is destructive with no undo. Spanner uses `RunWithRetriableTransactionAsync` for atomic operations but no multi-step compensation.
- **Gap**: Multi-step operations that fail mid-sequence leave cart in partial state.
- **Recommendation**: Implement `RemoveItem` RPC. For write-enabled scope, consider event-sourced cart model.
- **Evidence**: `src/services/CartService.cs`, `src/cartstore/RedisCartStore.cs`, `src/cartstore/SpannerCartStore.cs`, `src/cartstore/AlloyDBCartStore.cs`

#### STATE-Q2: Queryable Current State
- **Severity**: RISK
- **Finding**: `GetCart` provides queryable current state per `userId`. No list/search across carts. No administrative query interface. Only query parameter is `userId`.
- **Gap**: Agent cannot discover which carts exist without knowing specific user IDs.
- **Recommendation**: For analytics use cases, consider adding `ListCarts` RPC with pagination.
- **Evidence**: `src/protos/Cart.proto`, `src/services/CartService.cs`

#### STATE-Q3: Concurrency Controls
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled AND service has persistent state
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK
- **Finding**: No circuit breakers, retry decorators, or timeout configurations. No Polly or equivalent in `cartservice.csproj`. Exceptions caught and re-thrown as gRPC `FailedPrecondition`.
- **Gap**: No graceful degradation when backing store is degraded. No circuit breaker to prevent cascading failures.
- **Recommendation**: Add Polly for retry policies and circuit breaker patterns on data store calls.
- **Evidence**: `src/cartstore/RedisCartStore.cs`, `src/cartstore/SpannerCartStore.cs`, `src/cartstore/AlloyDBCartStore.cs`, `src/cartservice.csproj`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK
- **Finding**: No API-level rate limiting. No API Gateway. No application-level rate limiting middleware. Kubernetes resource limits provide container-level isolation only.
- **Gap**: Runaway agent loop can consume all cartservice pod resources.
- **Recommendation**: Add gRPC rate limiting middleware or Envoy sidecar with rate limiting.
- **Evidence**: `src/Startup.cs`, `src/cartservice.csproj`, `helm-chart/templates/cartservice.yaml`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits. No maximum records per operation. No spend limits. `EmptyCart` deletes all items with no limit.
- **Gap**: No blast radius protection for write operations. Informational for read-only scope.
- **Recommendation**: For write-enabled scope, implement configurable operation limits per agent identity.
- **Evidence**: `src/services/CartService.cs`, `src/cartstore/RedisCartStore.cs`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: RISK
- **Finding**: No load test results. No HPA. Static resource limits (CPU: 200-300m, Memory: 128-256Mi). Redis uses `emptyDir` (ephemeral). CI smoke test validates ~50 requests, not capacity.
- **Gap**: Infrastructure sized for human-paced interaction. Agent traffic patterns untested.
- **Recommendation**: Deploy HPA. Run load tests simulating agent traffic. Size Redis appropriately.
- **Evidence**: `helm-chart/templates/cartservice.yaml`, `.github/workflows/ci-pr.yaml`

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q2: Configurable Approval Gates
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK
- **Finding**: PR-specific namespaces deployed via CI/CD. Skaffold for local development. In-memory cache fallback for local testing. No Docker Compose. No synthetic data generators. Test environment uses in-memory cache, not Redis.
- **Gap**: No sandbox with production-equivalent data shape. No dedicated agent testing environment.
- **Recommendation**: Create dedicated agent-testing namespace with Redis and seed data. Add Docker Compose file.
- **Evidence**: `.github/workflows/ci-pr.yaml`, `skaffold.yaml`, `src/Startup.cs`


### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: No data classification at any level. Cart data contains `userId` (PII-candidate), `productId`, `quantity`. No classification tags on data stores. No field-level encryption. No PII detection tools. No `DATA_CLASSIFICATION.md`.
- **Gap**: Sensitive data not classified or tagged. No controls preventing agent access without authorization.
- **Recommendation**: Classify `userId` field. Create `DATA_CLASSIFICATION.md`. Implement field-level access controls.
- **Evidence**: `src/protos/Cart.proto`, `src/cartstore/RedisCartStore.cs`, `src/cartstore/SpannerCartStore.cs`, `src/cartstore/AlloyDBCartStore.cs`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: No data residency requirements documented. Terraform defaults to `us-central1`. No GDPR/LGPD compliance references. No cross-region replication.
- **Gap**: Data residency posture unknown. May create legal violation if PII sent to LLM in different region.
- **Recommendation**: Conduct data residency analysis. Configure agent LLM endpoint in same region as data.
- **Evidence**: `terraform/variables.tf`, `terraform/memorystore.tf`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK
- **Finding**: `GetCart` queries by `userId` only. Returns all items for a given user. No pagination, filtering, sorting, or result size limits. Cart data naturally bounded (typical user has <50 items).
- **Gap**: No mechanism to limit data returned to what agent needs.
- **Recommendation**: Consider `GetCartItem` RPC for specific items. Add pagination for large carts.
- **Evidence**: `src/protos/Cart.proto`, `src/services/CartService.cs`

#### DATA-Q4: System of Record Designations
- **Severity**: RISK
- **Finding**: No system-of-record designation documented. Three mutually exclusive backends (Redis, Spanner, AlloyDB) selected at startup via environment variables. No documentation of which is authoritative per deployment.
- **Gap**: Multiple backend options create ambiguity about authoritative data source.
- **Recommendation**: Document active backend per environment as system of record.
- **Evidence**: `src/Startup.cs`, `helm-chart/values.yaml`

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK
- **Finding**: No timestamps on cart data. The `Cart.proto` schema defines `user_id`, `product_id`, and `quantity` — no `created_at`, `updated_at`, or `event_time` fields. Redis stores serialized protobuf with no temporal metadata. Spanner and AlloyDB table schemas define `userId`, `productId`, `quantity` columns only — no timestamp columns. No data freshness signaling. No `Cache-Control` or equivalent headers in gRPC responses. No `X-Data-Age` metadata. Redis uses `emptyDir` volume (ephemeral, data lost on restart). Spanner provides strong consistency but this is not signaled to clients.
- **Gap**: Agents cannot determine when a cart was last modified. Time-sensitive reasoning is impossible. Agent has no way to determine whether cart data is from a fresh read, a stale cache, or a reconstructed-after-restart empty state.
- **Recommendation**: Add `last_modified` timestamp field to the `Cart` proto message and update all cart store implementations. Add gRPC response metadata indicating backend type and consistency guarantees.
- **Evidence**: `src/protos/Cart.proto`, `src/cartstore/RedisCartStore.cs`, `src/cartstore/SpannerCartStore.cs`, `src/cartstore/AlloyDBCartStore.cs`

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK
- **Finding**: `Console.WriteLine` statements in all cart store implementations log `userId` in plaintext. Specific examples: `RedisCartStore.cs` logs `"AddItemAsync called with userId={userId}"`, `"GetCartAsync called with userId={userId}"`. `AlloyDBCartStore.cs` includes raw SQL with user data interpolated. No log scrubbing middleware. No PII masking libraries.
- **Gap**: If `userId` contains PII (email, phone number), it leaks into container logs without redaction.
- **Recommendation**: Replace `Console.WriteLine` with `ILogger<T>` and implement log sanitizer. Confirm `userId` format.
- **Evidence**: `src/cartstore/RedisCartStore.cs`, `src/cartstore/SpannerCartStore.cs`, `src/cartstore/AlloyDBCartStore.cs`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics or profiling. Cart data quality maintained implicitly by application logic. Missing data possible after Redis restarts (ephemeral `emptyDir` volume).
- **Gap**: No formal data quality monitoring.
- **Recommendation**: Add input validation for `userId` format and `quantity` range. Monitor Redis data loss events.
- **Evidence**: `src/protos/Cart.proto`, `src/services/CartService.cs`, `src/cartstore/RedisCartStore.cs`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK
- **Finding**: `Cart.proto` defines typed schema. Not versioned — package `hipstershop` with no version qualifier. No `buf.yaml`. No schema registry. No database migration files. No breaking change detection in CI.
- **Gap**: Schema changes could break downstream consumers silently. No versioning mechanism.
- **Recommendation**: Adopt proto package versioning (`hipstershop.cart.v1`). Add `buf` to CI. Create DB migration scripts.
- **Evidence**: `src/protos/Cart.proto`, `src/cartservice.csproj`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Field names are human-readable: `user_id`, `product_id`, `quantity`, `items`. Standard proto3 snake_case naming. No legacy codes or abbreviations.
- **Gap**: None — names are self-documenting.
- **Recommendation**: No action needed.
- **Evidence**: `src/protos/Cart.proto`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No data catalog. No metadata layer beyond proto definition. No description annotations in proto file.
- **Gap**: Agent tool builders derive semantics from field names only.
- **Recommendation**: Add proto comments on messages and fields. Consider service catalog.
- **Evidence**: `src/protos/Cart.proto`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK
- **Finding**: No distributed tracing (no OpenTelemetry SDK, no X-Ray). Helm chart has optional OTel collector but application has no instrumentation. Logging uses `Console.WriteLine` — unstructured, no JSON, no correlation IDs. Tracing disabled.
- **Gap**: Agent-initiated requests cannot be traced end-to-end. Diagnosis requires manual log correlation.
- **Recommendation**: Add OpenTelemetry .NET SDK. Replace `Console.WriteLine` with `ILogger<T>` and JSON structured logging.
- **Evidence**: `src/cartservice.csproj`, `src/Startup.cs`, `src/cartstore/RedisCartStore.cs`, `helm-chart/values.yaml`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK
- **Finding**: No alerting configuration. No Cloud Monitoring alerting policies. No PagerDuty/OpsGenie. gRPC health check exists but is not proactive alerting. Terraform enables `monitoring.googleapis.com` but no alert policies defined.
- **Gap**: Target system degradation is not alerted on. Agents fail silently.
- **Recommendation**: Create alerting policies for error rate, latency, Redis failures. Configure notification channels.
- **Evidence**: `src/services/HealthCheckService.cs`, `terraform/main.tf`, `helm-chart/values.yaml`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics. No cart operation metrics. No business KPI dashboards. Terraform enables monitoring API but no custom metrics.
- **Gap**: Cannot measure agent effectiveness or impact on cart operations.
- **Recommendation**: Publish custom metrics via Cloud Monitoring or OpenTelemetry. Track agent traffic separately.
- **Evidence**: `src/services/CartService.cs`, `terraform/main.tf`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK
- **Finding**: Terraform IaC defines GKE cluster and Memorystore Redis. Kubernetes manifests and Helm chart define deployment. Terraform validation CI exists (syntax check only). No drift detection. No explicit IaC plan review step. No enforced peer review for IaC changes.
- **Gap**: IaC changes can be applied without plan review or drift detection.
- **Recommendation**: Add `terraform plan` to PR comments. Implement drift detection. Enforce required reviews for IaC changes.
- **Evidence**: `terraform/main.tf`, `terraform/memorystore.tf`, `.github/workflows/terraform-validate-ci.yaml`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK
- **Finding**: CI runs C# unit tests and deployment smoke tests. No API contract testing (no Pact, no proto breaking change detection). Smoke test validates system health, not API contract compliance.
- **Gap**: Breaking proto changes not caught until deployment-time smoke tests.
- **Recommendation**: Add `buf` to CI for proto linting and breaking change detection. Implement gRPC contract tests.
- **Evidence**: `.github/workflows/ci-pr.yaml`, `.github/workflows/ci-main.yaml`, `tests/CartServiceTests.cs`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK
- **Finding**: Skaffold-based deployment with `kubectl apply`. No explicit rollback triggers. No blue/green. No canary. No feature flags. Helm supports `helm rollback` if used. Manual `kubectl rollout undo` available.
- **Gap**: Rollback is manual. No automated rollback on error rate spikes. Time depends on operator availability.
- **Recommendation**: Implement automated rollback triggers. Document `helm rollback` procedure. Consider canary with Istio traffic shifting.
- **Evidence**: `skaffold.yaml`, `cloudbuild.yaml`, `helm-chart/templates/cartservice.yaml`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK
- **Finding**: 3 unit/integration tests in `CartServiceTests.cs`: empty cart retrieval, quantity update, new item insertion. Tests use `TestServer` with gRPC client against in-memory cache. No edge case tests (concurrent access, error scenarios, large carts, invalid input). No contract tests. No load tests.
- **Gap**: Only happy-path tested. Error handling, edge cases, and concurrent access untested.
- **Recommendation**: Add error scenario tests, contract tests, and load tests simulating agent patterns.
- **Evidence**: `tests/CartServiceTests.cs`, `tests/cartservice.tests.csproj`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: RISK
- **Finding**: In-cluster Redis uses `emptyDir` (no encryption, ephemeral). Memorystore Redis (`terraform/memorystore.tf`) has no encryption-at-rest configuration. No KMS key references. Spanner and AlloyDB use default Google-managed encryption (no CMEK). AlloyDB connection string does not specify SSL/TLS mode.
- **Gap**: Cart data at rest in Redis is unencrypted. No customer-managed encryption keys. Memorystore Redis has no authentication.
- **Recommendation**: Enable transit encryption on Memorystore Redis. Configure CMEK for managed databases. Implement Redis persistence with encrypted PVCs.
- **Evidence**: `terraform/memorystore.tf`, `src/cartstore/AlloyDBCartStore.cs`


## Evidence Index

### Infrastructure as Code
| File | Questions Referenced |
|------|---------------------|
| `terraform/main.tf` | AUTH-Q6, OBS-Q2, OBS-Q3, ENG-Q1 |
| `terraform/memorystore.tf` | DATA-Q2, ENG-Q1, ENG-Q5 |
| `terraform/variables.tf` | DATA-Q2 |

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `src/Program.cs` | API-Q1 |
| `src/Startup.cs` | AUTH-Q1, AUTH-Q5, STATE-Q5, HITL-Q3, DATA-Q4, OBS-Q1, API-Q8 |
| `src/services/CartService.cs` | API-Q1, AUTH-Q1, AUTH-Q3, AUTH-Q4, STATE-Q1, STATE-Q2, STATE-Q6, DATA-Q3, DATA-Q7, OBS-Q3 |
| `src/services/HealthCheckService.cs` | OBS-Q2 |
| `src/cartstore/ICartStore.cs` | API-Q7 |
| `src/cartstore/RedisCartStore.cs` | API-Q3, API-Q4, AUTH-Q4, AUTH-Q5, AUTH-Q6, STATE-Q1, STATE-Q4, DATA-Q5, DATA-Q6, OBS-Q1 |
| `src/cartstore/SpannerCartStore.cs` | API-Q3, API-Q4, AUTH-Q6, STATE-Q1, STATE-Q4, DATA-Q5, DATA-Q6 |
| `src/cartstore/AlloyDBCartStore.cs` | API-Q3, API-Q4, AUTH-Q5, STATE-Q1, STATE-Q4, DATA-Q1, DATA-Q5, DATA-Q6, ENG-Q5 |
| `tests/CartServiceTests.cs` | ENG-Q2, ENG-Q4 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `src/protos/Cart.proto` | API-Q1, API-Q2, API-Q4, API-Q5, AUTH-Q4, STATE-Q2, DATA-Q1, DATA-Q3, DATA-Q5, DATA-Q7, DISC-Q1, DISC-Q2, DISC-Q3 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/ci-pr.yaml` | HITL-Q3, STATE-Q7, ENG-Q2, ENG-Q4 |
| `.github/workflows/ci-main.yaml` | ENG-Q2 |
| `.github/workflows/terraform-validate-ci.yaml` | ENG-Q1 |
| `cloudbuild.yaml` | ENG-Q3 |
| `skaffold.yaml` | HITL-Q3, ENG-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `src/cartservice.csproj` | API-Q2, API-Q5, STATE-Q4, STATE-Q5, DISC-Q1, OBS-Q1 |
| `tests/cartservice.tests.csproj` | ENG-Q4 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `helm-chart/templates/cartservice.yaml` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q7, STATE-Q5, STATE-Q7, ENG-Q3 |
| `helm-chart/values.yaml` | AUTH-Q1, AUTH-Q2, AUTH-Q5, AUTH-Q7, DATA-Q4, OBS-Q1, OBS-Q2 |

### Notable Absences — Files Not Found
| Expected Artifact | Impact |
|-------------------|--------|
| `buf.yaml` (proto linting/breaking change detection) | API-Q2, DISC-Q1, ENG-Q2 |
| `DATA_CLASSIFICATION.md` | DATA-Q1, DATA-Q2 |
| OpenTelemetry SDK packages in `cartservice.csproj` | OBS-Q1 |
| Resilience library (Polly) in `cartservice.csproj` | STATE-Q4 |
| Rate limiting middleware in `cartservice.csproj` | STATE-Q5 |
| Load test results or HPA configuration | STATE-Q7 |
| CloudTrail / audit logging configuration | AUTH-Q6 |
| Alerting policy definitions | OBS-Q2 |