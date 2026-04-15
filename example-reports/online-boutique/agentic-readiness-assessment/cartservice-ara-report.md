# Agentic Readiness Assessment Report

**Target**: ./services/microservices-demo/src/cartservice
**Date**: 2025-07-15
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Agent Scope**: read-only
**Priority**: P0
**Tags**: csharp, grpc, redis, stateful
**Context**: C# gRPC service managing shopping carts with Redis backing store.

---

## Readiness Profile: Not Agent-Integrable

**BLOCKERs**: 3 | **RISKs**: 35 | **INFOs**: 11

Exclude from agent toolset or plan major remediation before re-evaluation. Three blockers — absent machine identity authentication, unclassified sensitive data, and undocumented network security policies — must all be resolved before any agent integration, including scoped pilots.

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

**Remediation Prioritization:** Resolve AUTH-Q1 (machine identity) first — you cannot enforce data access controls or network security without knowing who is calling. Then address DATA-Q1 (data classification) and ENG-Q6 (network policies) in parallel. Since agent_scope is read-only, consider scoping the initial agent to read operations while remediating all three blockers.

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: The gRPC service has no authentication configured. `Startup.cs` registers gRPC services with `services.AddGrpc()` and maps them in `endpoints.MapGrpcService<CartService>()` without any authentication or authorization middleware. There is no `AddAuthentication()`, no `UseAuthentication()`, no `UseAuthorization()`, no gRPC interceptors, and no API key validation. Kestrel is configured for HTTP/2 only in `appsettings.json` but with `AllowedHosts: "*"`. Any client that can reach the service can call any RPC without identity attribution.
- **Gap**: No machine identity authentication exists. No service account, OAuth2 client credentials, API key, or mTLS configuration. The `userId` parameter in RPC calls is a plain string — it is not derived from an authenticated principal and cannot be trusted for attribution.
- **Remediation**:
  - **Immediate**: Add gRPC interceptor-based authentication. Implement an ASP.NET Core authentication middleware using JWT Bearer tokens (`AddAuthentication().AddJwtBearer()`) or mTLS for service-to-service calls. Register `UseAuthentication()` and `UseAuthorization()` in the request pipeline in `Startup.cs`.
  - **Target State**: Every gRPC call is authenticated with a machine identity (service account or API key with principal attribution). The authenticated principal is logged on every operation. The `userId` parameter is validated against the authenticated identity or passed as a claim.
  - **Estimated Effort**: Medium (2–4 weeks including testing and deployment)
  - **Dependencies**: ENG-Q6 (network policies) — authentication and network security should be deployed together.
- **Evidence**: `src/Startup.cs` (no auth middleware), `src/services/CartService.cs` (no identity validation), `src/appsettings.json` (`AllowedHosts: "*"`)

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: The cart service stores `userId` (potential PII — a user identifier that could be an email, username, or external ID), `productId`, and `quantity`. These fields are defined in `Cart.proto` and stored in Redis (as serialized Protobuf), Cloud Spanner (in a `CartItems` table), or AlloyDB (in a configurable table). There is no data classification at any level — no field-level tags, no classification metadata, no PII detection tools, no access controls distinguishing sensitive from non-sensitive fields.
- **Gap**: Sensitive data (userId) is not classified or tagged. No field-level encryption exists. No controls prevent an agent from retrieving userId values without explicit authorization. Redis stores data as untagged binary blobs. Spanner and AlloyDB table schemas have no column-level access controls defined in the codebase.
- **Remediation**:
  - **Immediate**: Classify the data fields: `userId` as PII (user identifier), `productId` and `quantity` as non-sensitive business data. Document this classification in a data dictionary or schema annotation file.
  - **Target State**: All data fields are classified with sensitivity labels. Field-level access controls prevent agents from accessing PII without explicit authorization. PII fields are encrypted at the application layer or through database-native column encryption. Amazon Macie or equivalent scanning is enabled for data stores.
  - **Estimated Effort**: Medium (3–6 weeks including classification, encryption implementation, and access control enforcement)
  - **Dependencies**: AUTH-Q1 (machine identity) — data access controls require authenticated principals to enforce.
- **Evidence**: `src/protos/Cart.proto` (defines userId, productId, quantity with no classification), `src/cartstore/RedisCartStore.cs` (stores unclassified data), `src/cartstore/SpannerCartStore.cs` (no column-level access controls), `src/cartstore/AlloyDBCartStore.cs` (no column-level access controls)

### ENG-Q6: Cross-Origin and Network Policies

- **Severity**: BLOCKER
- **Finding**: No CORS configuration, security group rules, network policies, API gateway settings, or firewall rules are defined anywhere in the repository. `appsettings.json` sets `AllowedHosts: "*"`, accepting connections from any host. The `Dockerfile` exposes port 7070 with no network restrictions. There is no IaC in the repository defining security groups, network ACLs, or Kubernetes NetworkPolicies. The gRPC service is effectively wide open to any network client.
- **Gap**: No network security configuration exists. No documentation of intended network boundaries, allowed callers, or firewall rules. Without network policies, any client on the network can reach the gRPC service — this is a deployment prerequisite for agent integration.
- **Remediation**:
  - **Immediate**: Define network policies as IaC (Terraform security groups, Kubernetes NetworkPolicy, or service mesh policies) that restrict inbound traffic to known callers only. Restrict `AllowedHosts` in `appsettings.json` to specific hostnames.
  - **Target State**: Network policies are defined as IaC, reviewed via PR, and enforced in all environments. Only authorized agent identities and known service callers can reach the gRPC port. Security group rules and/or Kubernetes NetworkPolicies restrict traffic to specific CIDRs or service accounts. CORS policies are configured if any HTTP gateway fronts the gRPC service.
  - **Estimated Effort**: Medium (2–4 weeks including IaC authoring, testing, and deployment)
  - **Dependencies**: AUTH-Q1 (machine identity) — network policies and authentication form the two layers of defense.
- **Evidence**: `src/appsettings.json` (`AllowedHosts: "*"`), `src/Dockerfile` (`EXPOSE 7070` with no restrictions), absence of any IaC, Kubernetes manifests, or network policy files in the repository

## RISKs — Proceed with Compensating Controls

### API-Q2: Machine-Readable API Specification

- **Severity**: RISK
- **Finding**: `Cart.proto` serves as the machine-readable specification for the gRPC interface. It defines 3 RPCs (`AddItem`, `GetCart`, `EmptyCart`) with typed request/response messages using proto3 syntax. The proto file is referenced in `cartservice.csproj` via `<Protobuf Include="protos\Cart.proto" GrpcServices="Both" />`, indicating server and client stubs are auto-generated from it. The proto definitions match the implementation in `CartService.cs` (all 3 RPCs are implemented). However, the proto file lacks inline documentation (no comments on fields or RPCs beyond the license header).
- **Gap**: While the proto file exists and is current with the implementation, it lacks API documentation (descriptions, examples, constraints). No schema registry is used to version or publish the proto. No OpenAPI or REST gateway spec exists for non-gRPC consumers.
- **Compensating Controls**:
  - Use the proto file directly to generate agent tool definitions via gRPC reflection or protoc tooling.
  - Add inline proto comments documenting field constraints and RPC behavior.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add descriptive comments to all RPCs and messages in `Cart.proto`. Consider enabling gRPC server reflection for runtime schema discovery. If REST access is needed, add gRPC-JSON transcoding via Envoy or grpc-gateway.
- **Evidence**: `src/protos/Cart.proto`, `src/cartservice.csproj` (Protobuf reference), `src/services/CartService.cs` (implementation matches proto)

### API-Q3: Structured Error Responses

- **Severity**: RISK
- **Finding**: All three cart store implementations (`RedisCartStore.cs`, `SpannerCartStore.cs`, `AlloyDBCartStore.cs`) throw `RpcException` with `StatusCode.FailedPrecondition` for all error conditions. Error messages include the raw exception string (e.g., `$"Can't access cart storage. {ex}"`). The gRPC `Status` object provides a status code and message, but there is no structured error body with error codes, retryable flags, or error categories. All errors are caught as generic `Exception` — no distinction between transient failures (connection timeout) and permanent failures (invalid data).
- **Gap**: No structured error response format beyond gRPC status codes. All errors use `FailedPrecondition` regardless of root cause. No retryable/non-retryable classification. Raw exception details are leaked in error messages, which could expose internal implementation details.
- **Compensating Controls**:
  - Agents can treat `FailedPrecondition` as retryable with exponential backoff as a default policy.
  - Implement error classification at the agent orchestration layer based on gRPC status codes.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement a gRPC error interceptor that maps specific exceptions to appropriate gRPC status codes (e.g., `Unavailable` for transient connection failures, `InvalidArgument` for bad input, `Internal` for unexpected errors). Add structured error details using gRPC rich error model (`google.rpc.Status` with `google.rpc.ErrorInfo`). Remove raw exception strings from client-facing error messages.
- **Evidence**: `src/cartstore/RedisCartStore.cs` (all catch blocks throw `FailedPrecondition`), `src/cartstore/SpannerCartStore.cs` (same pattern), `src/cartstore/AlloyDBCartStore.cs` (same pattern)

### API-Q5: API Versioning and Deprecation

- **Severity**: RISK
- **Finding**: The proto package is named `hipstershop` with no version identifier. There are no `/v1/`, `/v2/` URL patterns, no `Accept-Version` headers, no versioning annotations, no changelog files, and no deprecation notices. The proto file has no `option` declarations for versioning.
- **Gap**: No API versioning scheme exists. Any breaking change to `Cart.proto` (removing fields, changing types, renaming RPCs) will break all connected clients simultaneously with no migration path.
- **Compensating Controls**:
  - Treat proto3 field numbering as an implicit compatibility mechanism (new fields can be added without breaking existing clients).
  - Implement API contract tests (ENG-Q2) to catch breaking changes before deployment.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Rename the proto package to include a version (e.g., `hipstershop.cart.v1`). Establish a proto compatibility policy: additive changes only within a version, breaking changes require a new version. Add a CHANGELOG.md tracking API changes.
- **Evidence**: `src/protos/Cart.proto` (package `hipstershop` with no version)

### API-Q7: Asynchronous Operation Support

- **Severity**: RISK
- **Finding**: All 3 RPCs (`AddItem`, `GetCart`, `EmptyCart`) are synchronous request/response operations. There are no background job frameworks, no job status APIs, no polling endpoints, no webhook callbacks, and no message queue integrations. The cart operations are simple CRUD and likely complete within milliseconds, so async patterns may not be needed for the current operations. However, no infrastructure exists to support long-running operations if the scope expands.
- **Gap**: No async operation patterns exist. If any cart operation becomes long-running (e.g., cart validation against inventory, price calculation), there is no infrastructure to support it.
- **Compensating Controls**:
  - For the current CRUD scope, synchronous operations are acceptable — cart reads and writes are inherently fast.
  - Add timeout configuration at the agent orchestration layer for gRPC calls.
- **Remediation Timeline**: 60–90 days (only if scope expands to long-running operations)
- **Recommendation**: Acceptable for current scope. If the cart service adds complex operations (inventory validation, price lookups), implement async patterns using a job queue or Step Functions with status polling endpoints.
- **Evidence**: `src/services/CartService.cs` (all RPCs return directly), `src/cartstore/ICartStore.cs` (all methods return Task — C# async but not application-level async patterns)

### AUTH-Q2: Scoped Permissions (Least Privilege)

- **Severity**: RISK
- **Finding**: No authorization model is defined in the codebase. There are no IAM policies, no role definitions, no permission scoping, and no IaC files with IAM configuration. All 3 RPCs are accessible to any caller without permission checks. There is no mechanism to grant an agent read-only access to `GetCart` while denying access to `AddItem` or `EmptyCart`.
- **Gap**: No scoped permissions exist. An agent (or any caller) with network access can execute all operations including writes (AddItem, EmptyCart) without restriction.
- **Compensating Controls**:
  - Restrict agent scope at the orchestration layer — only expose `GetCart` as an agent tool, withholding `AddItem` and `EmptyCart` from tool definitions.
  - Implement network-level isolation to limit which agents can reach the service.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement gRPC authorization policies using ASP.NET Core's `[Authorize]` attribute with role or policy-based access control. Define separate roles for read-only (`GetCart`) and read-write (`AddItem`, `EmptyCart`) operations. Enforce via JWT claims or API key scopes.
- **Evidence**: `src/Startup.cs` (no authorization middleware), `src/services/CartService.cs` (no `[Authorize]` attributes)

### AUTH-Q3: Action-Level Authorization

- **Severity**: RISK
- **Finding**: No action-level authorization exists. All 3 RPCs (`AddItem`, `GetCart`, `EmptyCart`) are accessible without any permission checks. There is no ABAC, no fine-grained RBAC, no permission matrix, and no middleware checking `canRead`, `canWrite`, or `canDelete` capabilities.
- **Gap**: Cannot enforce action-level restrictions — an agent cannot be granted read access to `GetCart` while being denied `EmptyCart` at the application layer.
- **Compensating Controls**:
  - Restrict at the orchestration layer by only registering `GetCart` as an available agent tool.
  - Use network segmentation or API gateway policies to block specific RPC methods.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add ASP.NET Core authorization policies per RPC method. Implement claims-based authorization where agent identities carry specific action permissions (e.g., `cart:read`, `cart:write`, `cart:delete`).
- **Evidence**: `src/services/CartService.cs` (no authorization checks on any RPC method)

### AUTH-Q4: Identity Propagation

- **Severity**: RISK
- **Finding**: The `userId` parameter is passed as a plain string in all RPC requests (`AddItemRequest.user_id`, `GetCartRequest.user_id`, `EmptyCartRequest.user_id`). It is not derived from an authenticated JWT, OAuth token, or any identity propagation mechanism. There is no JWT parsing middleware, no OAuth2 on-behalf-of flows, no token exchange, and no `Authorization` header processing. The `ServerCallContext` parameter in `CartService.cs` is available but unused for identity extraction.
- **Gap**: No identity propagation exists. The `userId` is a caller-supplied string with no validation against an authenticated identity. An agent could pass any `userId` and access any user's cart.
- **Compensating Controls**:
  - Validate `userId` at the agent orchestration layer before passing it to the gRPC call.
  - Implement a gRPC interceptor that extracts user identity from metadata headers and validates it against the `userId` parameter.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement JWT-based identity propagation. Extract the user identity from the `ServerCallContext` metadata (e.g., `Authorization: Bearer <token>`), validate it, and ensure the `userId` parameter matches the authenticated user's identity. This prevents agents from accessing other users' carts.
- **Evidence**: `src/protos/Cart.proto` (`user_id` as plain string field), `src/services/CartService.cs` (`ServerCallContext` unused for identity)

### AUTH-Q5: Agent-as-Self vs Agent-on-Behalf-of-User

- **Severity**: RISK
- **Finding**: No identity model exists at all. There is no distinction between an agent acting under its own service identity and an agent acting on behalf of a specific human user. No separate IAM roles, no different auth flows, no audit log fields to distinguish the two modes.
- **Gap**: The system cannot differentiate between agent-as-self and agent-on-behalf-of-user access patterns. This conflation creates privilege escalation risk — an agent acting as itself could access all users' carts.
- **Compensating Controls**:
  - Define the distinction at the agent orchestration layer and pass identifying metadata (e.g., `X-Agent-Mode: on-behalf-of`, `X-User-Id: <user>`) as gRPC metadata.
  - Log the distinction in orchestration-layer logs.
- **Remediation Timeline**: 90–120 days
- **Recommendation**: Design two authentication flows: (1) agent-as-self with a service account scoped to administrative operations, (2) agent-on-behalf-of-user using OAuth2 token exchange or JWT delegation. Log the mode in every request's audit trail.
- **Evidence**: `src/Startup.cs` (no identity model), `src/services/CartService.cs` (no identity distinction)

### AUTH-Q6: Credential Management

- **Severity**: RISK
- **Finding**: Mixed credential management pattern observed. `AlloyDBCartStore.cs` uses Google Cloud Secret Manager (`SecretManagerServiceClient.Create()`) to retrieve the AlloyDB password at runtime — this is a good practice. However, the Redis connection string (`REDIS_ADDR`) and Spanner configuration (`SPANNER_PROJECT`, `SPANNER_CONNECTION_STRING`, `SPANNER_INSTANCE`, `SPANNER_DATABASE`) are read from `IConfiguration` (environment variables) with no secrets management. AlloyDB configuration also reads `ALLOYDB_PRIMARY_IP`, `ALLOYDB_DATABASE_NAME`, and `ALLOYDB_TABLE_NAME` from environment variables. A TODO comment in `AlloyDBCartStore.cs` notes: "Create a separate user for connecting within the application rather than using our superuser" — indicating the service currently uses a superuser account. No hardcoded credentials were found in source code. No `.env` files are committed.
- **Gap**: Only AlloyDB password uses secrets management. Redis and Spanner credentials are in environment variables without rotation. AlloyDB uses a superuser account instead of a least-privilege application user. No credential rotation mechanism for Redis or Spanner.
- **Compensating Controls**:
  - Environment variables are acceptable for non-secret configuration (hostnames, project IDs) but should not contain passwords or API keys.
  - Extend Secret Manager usage to all sensitive connection parameters.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Migrate all credentials (including Redis auth tokens if used) to Google Cloud Secret Manager or AWS Secrets Manager. Create a dedicated application-level database user for AlloyDB instead of the superuser. Implement credential rotation with zero-downtime reload.
- **Evidence**: `src/cartstore/AlloyDBCartStore.cs` (Secret Manager for password, TODO about superuser), `src/Startup.cs` (Redis and Spanner config from environment variables)

### AUTH-Q7: Immutable Audit Logging ⚡

- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: No audit logging exists. The application uses `Console.WriteLine` for basic operational logging (e.g., `"AddItemAsync called with userId={userId}"` in `RedisCartStore.cs`, `"GetCartAsync called for userId={userId}"` in `SpannerCartStore.cs`). These are unstructured console logs with no log level, no timestamp metadata, no authenticated principal field, and no immutability guarantees. There is no CloudTrail configuration, no CloudWatch log retention policies, no S3 bucket with object lock for logs, and no immutable log storage configuration anywhere in the repository.
- **Gap**: No audit trail exists that identifies who made a request (human or agent). Console logs are ephemeral, unstructured, and mutable. No compliance-grade logging for any operation.
- **Compensating Controls**:
  - Capture audit logs at the agent orchestration layer, recording which agent called which RPC with what parameters.
  - Route container stdout to a centralized log aggregator with immutable storage.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Replace `Console.WriteLine` with structured logging (e.g., `Microsoft.Extensions.Logging` with JSON formatter). Add an audit log interceptor that records the authenticated principal, operation, parameters, and timestamp for every RPC call. Route logs to CloudWatch Logs or S3 with object lock for immutability. Enable CloudTrail for infrastructure-level audit.
- **Evidence**: `src/cartstore/RedisCartStore.cs` (Console.WriteLine logging), `src/cartstore/SpannerCartStore.cs` (Console.WriteLine logging), `src/cartstore/AlloyDBCartStore.cs` (Console.WriteLine logging), `src/services/HealthCheckService.cs` (Console.WriteLine logging)

### AUTH-Q8: Agent Identity Suspension

- **Severity**: RISK
- **Finding**: No identity system exists, so there is no mechanism to suspend or revoke an individual agent identity. There are no API key revocation endpoints, no IAM role deactivation procedures, no service account disable mechanisms, and no user pool management.
- **Gap**: If an agent exhibits anomalous behavior, there is no way to suspend its access without taking down the entire service or blocking all traffic at the network level.
- **Compensating Controls**:
  - Implement network-level blocking (firewall rules, security group changes) to isolate a misbehaving agent by source IP.
  - Use agent orchestration-layer kill switches to stop specific agent instances.
- **Remediation Timeline**: 60–90 days (dependent on AUTH-Q1 resolution)
- **Recommendation**: Once machine identity is implemented (AUTH-Q1), ensure each agent has a distinct identity (API key or service account) that can be individually revoked or suspended without affecting other agents or users.
- **Evidence**: `src/Startup.cs` (no identity system), absence of any identity management configuration in the repository

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: No compensation or rollback logic exists. Cart operations are simple CRUD: `AddItem` adds or updates a cart item, `GetCart` reads the cart, `EmptyCart` deletes all items. There are no saga patterns, no two-phase commit, no explicit undo endpoints, no compensating transactions, and no Step Functions with rollback states. If a multi-step workflow (e.g., add multiple items then checkout) fails mid-sequence, there is no mechanism to roll back the completed steps.
- **Gap**: No compensation for partial failures in multi-step operations. `EmptyCart` is the only "undo-like" operation and it deletes all items, not specific ones.
- **Compensating Controls**:
  - For read-only agents, compensation is not needed — reads do not modify state.
  - If write operations are later enabled, implement per-item removal endpoints and transaction logging.
- **Remediation Timeline**: 90–120 days (only if agent_scope changes to write-enabled)
- **Recommendation**: Add a `RemoveItem` RPC to support per-item rollback. Implement a transaction log recording all cart modifications, enabling point-in-time recovery. Consider saga patterns if the cart service participates in multi-service workflows (e.g., cart → checkout → payment).
- **Evidence**: `src/services/CartService.cs` (only AddItem, GetCart, EmptyCart — no undo), `src/cartstore/ICartStore.cs` (interface defines no rollback methods)

### STATE-Q2: Queryable Current State

- **Severity**: RISK
- **Finding**: `GetCart` RPC provides queryable state by `userId` — an agent can inspect the current cart contents before taking action. However, the query capability is limited: only full cart retrieval by userId is supported. There is no pagination, no filtering by product, no sorting, and no ability to query cart metadata (e.g., item count, last modified time) without retrieving the full cart.
- **Gap**: Basic queryable state exists (GetCart by userId) but lacks granular query capabilities. No metadata queries. No way to check if a specific item is in the cart without retrieving the entire cart.
- **Compensating Controls**:
  - For typical cart sizes (< 100 items), full cart retrieval is acceptable.
  - Implement item-level filtering at the agent orchestration layer after retrieving the full cart.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add a `GetCartItem` RPC for single-item lookup. Add cart metadata (item count, last modified timestamp) to the `Cart` message. Consider adding pagination if cart sizes grow large.
- **Evidence**: `src/protos/Cart.proto` (GetCart returns full Cart with all items), `src/services/CartService.cs` (GetCart delegates to store)

### STATE-Q3: Concurrency Controls

- **Severity**: RISK
- **Finding**: Concurrency handling varies by cart store implementation. `RedisCartStore.cs` performs read-then-write without any locking — `GetAsync` followed by `SetAsync` creates a race condition where concurrent `AddItem` calls could overwrite each other's changes. `SpannerCartStore.cs` uses `RunWithRetriableTransactionAsync` which provides Spanner's built-in optimistic concurrency and automatic retry on conflicts. `AlloyDBCartStore.cs` uses `INSERT ... ON CONFLICT DO UPDATE` which handles insert conflicts but the read-then-write pattern for quantity aggregation is not within a database transaction, creating a potential race condition.
- **Gap**: Redis implementation has no concurrency controls. AlloyDB has partial controls (ON CONFLICT for inserts but no transaction isolation for reads). Only Spanner has proper transaction-level concurrency handling.
- **Compensating Controls**:
  - For read-only agents, concurrency is not a concern — reads do not create race conditions.
  - If using Redis, accept eventual consistency for cart data (low-stakes domain).
- **Remediation Timeline**: 60–90 days
- **Recommendation**: For Redis: implement optimistic locking using Redis WATCH/MULTI/EXEC or Lua scripts for atomic read-update-write. For AlloyDB: wrap the read-then-write in an explicit database transaction with proper isolation level. Add ETag or version fields to the Cart message for client-side concurrency detection.
- **Evidence**: `src/cartstore/RedisCartStore.cs` (read-then-write without locking), `src/cartstore/SpannerCartStore.cs` (RunWithRetriableTransactionAsync), `src/cartstore/AlloyDBCartStore.cs` (INSERT ON CONFLICT but no transaction isolation for reads)

### STATE-Q4: Circuit Breakers and Resilience

- **Severity**: RISK
- **Finding**: No resilience patterns are implemented. There are no circuit breakers, no retry decorators, no timeout configurations on database clients, and no bulkhead isolation. The `cartservice.csproj` does not reference Polly, Resilience4j, or any resilience library. All cart store implementations catch exceptions and throw `RpcException` but do not implement retry logic for transient failures. Spanner's `RunWithRetriableTransactionAsync` handles Spanner-specific transient failures, but this is database-level, not application-level resilience.
- **Gap**: No circuit breakers prevent cascading failures from Redis, Spanner, or AlloyDB outages. No timeout configurations on database connections. No retry logic for transient network failures.
- **Compensating Controls**:
  - gRPC clients calling this service can implement their own retry and timeout policies.
  - Container orchestration (Kubernetes) can restart unhealthy pods based on health check failures.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add Microsoft.Extensions.Http.Resilience or Polly for resilience patterns. Implement circuit breakers on database connections (Redis, Spanner, AlloyDB). Add timeout configurations on all database client calls. Implement retry with exponential backoff for transient failures.
- **Evidence**: `src/cartservice.csproj` (no resilience libraries), `src/cartstore/RedisCartStore.cs` (catch-all exception handling, no retry), `src/cartstore/AlloyDBCartStore.cs` (no retry logic)

### STATE-Q5: Rate Limiting and Throttling

- **Severity**: RISK
- **Finding**: No rate limiting or throttling is configured at any layer. There is no API Gateway, no rate limiting middleware, no throttling configuration, no `express-rate-limit` equivalent, and no usage plans. The gRPC service accepts unlimited concurrent requests.
- **Gap**: A runaway agent loop could DDoS the cart service and its backing stores at machine speed with no protection.
- **Compensating Controls**:
  - Implement rate limiting at the agent orchestration layer (limit tool call frequency).
  - Use a service mesh or API gateway in front of the gRPC service to enforce rate limits.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add an ASP.NET Core rate limiting middleware (`Microsoft.AspNetCore.RateLimiting`) or deploy an API gateway (e.g., Envoy, AWS API Gateway with gRPC support) with rate limit policies. Configure per-client rate limits based on authenticated identity.
- **Evidence**: `src/Startup.cs` (no rate limiting middleware), absence of API Gateway or rate limit configuration

### STATE-Q6: Blast Radius and Transaction Limits

- **Severity**: RISK
- **Finding**: No configurable limits on agent-initiated actions exist. There are no maximum records per operation, no maximum operations per session, and no per-identity transaction limits. `EmptyCart` deletes all items for a user without any confirmation or limit. An agent could call `EmptyCart` for every user in the system with no programmatic safeguard.
- **Gap**: No blast radius controls. No ability to limit the scope of agent actions (e.g., max cart modifications per hour, max carts emptied per session).
- **Compensating Controls**:
  - Implement transaction limits at the agent orchestration layer (e.g., max 50 cart operations per agent session).
  - For read-only agents, blast radius is limited to data retrieval volume.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement configurable per-identity transaction limits (e.g., `max_empty_cart_per_hour=10`, `max_add_item_per_minute=100`). Add a rate limiter per operation type, not just per endpoint. Log all operations for anomaly detection.
- **Evidence**: `src/services/CartService.cs` (no transaction limits), `src/cartstore/ICartStore.cs` (no limit parameters)

### STATE-Q7: Infrastructure Capacity for Agent Traffic

- **Severity**: RISK
- **Finding**: No load testing results, auto-scaling policies, or capacity planning documentation exist in the repository. The `Dockerfile` exposes port 7070 and runs as a single container. No horizontal pod autoscaler (HPA) configuration, no scaling policies, and no performance benchmarks are present. The service connects to a single Redis instance, Spanner database, or AlloyDB instance with no connection pooling configuration (AlloyDB creates a new `NpgsqlDataSource` per request).
- **Gap**: No evidence that the service has been tested or sized for agent-generated traffic patterns. AlloyDB connection management creates a new data source per request, which may not scale under high concurrency.
- **Compensating Controls**:
  - Start with a low-concurrency agent pilot and monitor resource utilization.
  - Rely on container orchestration (Kubernetes) for basic scaling.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Conduct load testing to establish baseline performance. Implement connection pooling for AlloyDB (use a singleton `NpgsqlDataSource`). Configure auto-scaling policies for the container. Add resource limits and requests in Kubernetes manifests.
- **Evidence**: `src/Dockerfile` (single container, EXPOSE 7070), `src/cartstore/AlloyDBCartStore.cs` (creates new NpgsqlDataSource per method call)

### HITL-Q1: Draft/Pending State

- **Severity**: RISK
- **Finding**: No draft or pending state concept exists. The `AddItem` RPC immediately commits items to the cart (Redis cache, Spanner table, or AlloyDB table). There is no "pending" status, no approval workflow, no two-step commit pattern. `EmptyCart` immediately deletes all items without confirmation.
- **Gap**: All write operations are immediate and irreversible (within the cart context). No staging area for agent-proposed changes before human approval.
- **Compensating Controls**:
  - For read-only agents, draft state is not needed — reads do not modify data.
  - If write access is enabled, implement a "proposed cart" pattern at the orchestration layer that requires human confirmation before calling `AddItem`.
- **Remediation Timeline**: 60–90 days (only if agent_scope changes to write-enabled)
- **Recommendation**: Add a `status` field to cart items (e.g., `DRAFT`, `CONFIRMED`) that requires explicit confirmation before items are committed. Alternatively, implement a separate "proposed changes" API that agents write to, with a human approval step before applying to the actual cart.
- **Evidence**: `src/services/CartService.cs` (immediate commit on AddItem), `src/cartstore/ICartStore.cs` (no draft/status concept)

### HITL-Q2: Configurable Approval Gates

- **Severity**: RISK
- **Finding**: No approval mechanism exists. All 3 RPCs execute immediately without human confirmation. There are no approval API endpoints, no status-based workflows, no configurable operation-level flags, and no Step Functions with human approval tasks.
- **Gap**: No way to require human approval for specific operations (e.g., emptying a cart with high-value items).
- **Compensating Controls**:
  - Implement approval gates at the agent orchestration layer — require human confirmation before the agent calls `EmptyCart` or `AddItem`.
  - For read-only agents, approval gates are not needed.
- **Remediation Timeline**: 60–90 days (only if agent_scope changes to write-enabled)
- **Recommendation**: Add a configurable approval gate middleware that intercepts write RPCs and requires confirmation based on operation type or cart value thresholds.
- **Evidence**: `src/services/CartService.cs` (all RPCs execute immediately), absence of any approval workflow

### HITL-Q3: Sandbox/Staging Environment

- **Severity**: RISK
- **Finding**: `Dockerfile.debug` provides a debug build variant that could be used for local development, but there is no separate staging environment configuration. No `docker-compose.yml` for local testing with Redis. No seed data scripts, no synthetic data generators, no environment-specific configuration files (e.g., `appsettings.Staging.json`). The in-memory fallback in `Startup.cs` (when no Redis address is provided) could serve as a test mode, but it is undocumented and not designed as a staging environment.
- **Gap**: No production-equivalent staging or sandbox environment defined. Agents cannot be tested against realistic conditions without risk to live systems.
- **Compensating Controls**:
  - Use the in-memory cache mode (no `REDIS_ADDR` configured) for local agent testing.
  - Deploy a separate instance with a dedicated Redis/Spanner/AlloyDB for staging.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a `docker-compose.yml` with Redis for local integration testing. Add `appsettings.Staging.json` with staging-specific configuration. Create seed data scripts that populate test carts. Document the staging environment setup for agent testing.
- **Evidence**: `src/Dockerfile.debug` (debug build), `src/Startup.cs` (in-memory fallback when REDIS_ADDR not set), absence of docker-compose, staging config, or seed data

### DATA-Q2: Data Residency and Sovereignty ⚡

- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: No data residency or sovereignty requirements are documented or enforced. Redis, Spanner, and AlloyDB connection configurations are entirely driven by environment variables (`REDIS_ADDR`, `SPANNER_PROJECT`, `ALLOYDB_PRIMARY_IP`) with no region constraints. There are no GDPR, LGPD, or HIPAA references anywhere in the codebase. No data residency policies, no region-specific storage configurations, and no cross-region replication settings.
- **Gap**: Unknown whether cart data (containing userId) is subject to data residency requirements. If the service operates in GDPR jurisdictions, sending userId to an LLM in a different region could create a compliance issue.
- **Compensating Controls**:
  - Determine data residency requirements from the organization's compliance team before agent deployment.
  - Ensure the agent's LLM endpoint is deployed in the same region as the data stores.
- **Remediation Timeline**: 30–60 days (assessment and documentation)
- **Recommendation**: Document the data residency requirements for userId and cart data. If GDPR applies, ensure all LLM endpoints used by agents are in the same jurisdiction as the data stores. Add region configuration validation in the deployment pipeline.
- **Evidence**: `src/Startup.cs` (environment-variable-driven connection strings), `src/cartstore/AlloyDBCartStore.cs` (ALLOYDB_PRIMARY_IP from env), absence of any data residency documentation

### DATA-Q3: Selective Query Support

- **Severity**: RISK
- **Finding**: `GetCart` returns all items for a given `userId` with no pagination, filtering, or sorting. The proto definition returns `repeated CartItem items` as an unbounded list. In the Redis implementation, the entire serialized cart is retrieved and deserialized. In Spanner and AlloyDB, `SELECT *` queries retrieve all items for a user with no LIMIT clause.
- **Gap**: No selective query support. Agents cannot request a subset of cart items, cannot paginate through large carts, and cannot filter by product or sort by quantity.
- **Compensating Controls**:
  - Cart sizes are typically small (< 50 items), making unbounded retrieval acceptable for most use cases.
  - Implement filtering at the agent orchestration layer after retrieving the full cart.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add optional pagination parameters to `GetCartRequest` (e.g., `int32 page_size`, `string page_token`). Add filter support (e.g., `string product_id_filter`). For Spanner and AlloyDB, add LIMIT/OFFSET to queries.
- **Evidence**: `src/protos/Cart.proto` (no pagination fields in GetCartRequest), `src/cartstore/SpannerCartStore.cs` (SELECT * with no LIMIT), `src/cartstore/AlloyDBCartStore.cs` (SELECT with no LIMIT)

### DATA-Q4: System of Record Designations

- **Severity**: RISK
- **Finding**: No system-of-record designations exist. The cart service stores cart data in one of three backing stores (Redis, Spanner, AlloyDB) depending on configuration, but there is no documentation of which store is the authoritative source. No master data management references, no data ownership definitions, no conflict resolution logic.
- **Gap**: If multiple cart services or data sources exist, there is no golden record designation for cart data. No documentation of data ownership or authority.
- **Compensating Controls**:
  - Treat the configured cart store as the single source of truth for cart state.
  - Document the system-of-record designation in an architecture decision record.
- **Remediation Timeline**: 30 days (documentation)
- **Recommendation**: Document the cart service as the system of record for shopping cart state. Define data ownership and specify which backing store is authoritative in each environment.
- **Evidence**: `src/Startup.cs` (configurable backing store selection), absence of system-of-record documentation

### DATA-Q5: Reliable Timestamps

- **Severity**: RISK
- **Finding**: The `Cart.proto` message defines only `user_id`, `product_id`, and `quantity` — no timestamp fields. There are no `created_at`, `updated_at`, or `event_time` fields in the proto messages, in the Redis stored data, or in the Spanner/AlloyDB table schemas (as defined in the code). Cart items have no temporal metadata indicating when they were added or last modified.
- **Gap**: No timestamps on any cart data. An agent cannot determine when an item was added to the cart, when the cart was last modified, or how old the cart data is.
- **Compensating Controls**:
  - Add timestamp tracking at the agent orchestration layer for agent-initiated operations.
  - Accept the limitation for read-only agents — cart freshness is determined by the backing store.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `google.protobuf.Timestamp created_at` and `google.protobuf.Timestamp updated_at` fields to the `Cart` and `CartItem` messages. Populate these timestamps in all cart store implementations. Store timestamps in UTC.
- **Evidence**: `src/protos/Cart.proto` (no timestamp fields), `src/cartstore/RedisCartStore.cs` (no timestamps stored), `src/cartstore/SpannerCartStore.cs` (no timestamp columns)

### DATA-Q6: Data Freshness Signaling

- **Severity**: RISK
- **Finding**: No data freshness signaling exists. There are no `Cache-Control` headers, no `X-Data-Age` headers, no `last_refreshed` fields, and no consistency level indicators in responses. Redis serves as a cache but has no TTL configuration in the code — cached data persists indefinitely. gRPC responses do not include metadata about data freshness or consistency guarantees. An agent reading from Redis cannot know if the data is current or stale.
- **Gap**: No mechanism to signal data freshness, cache age, or consistency level to agents. Redis-cached data could be stale with no indication.
- **Compensating Controls**:
  - Treat all cart reads as eventually consistent and implement read-before-write patterns at the orchestration layer.
  - Add freshness metadata at the gRPC metadata (trailing headers) level.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a `google.protobuf.Timestamp last_modified` field to the `Cart` message. Set TTL on Redis cache entries. Return data freshness metadata in gRPC trailing headers (e.g., `x-data-age`, `x-cache-status`).
- **Evidence**: `src/cartstore/RedisCartStore.cs` (no TTL on cache entries, `_cache.SetAsync` with no expiration), `src/protos/Cart.proto` (no freshness fields)

### DATA-Q7: PII Redaction in Logs

- **Severity**: RISK
- **Finding**: `userId` is logged directly in all cart store implementations using `Console.WriteLine`. Examples: `"AddItemAsync called with userId={userId}, productId={productId}, quantity={quantity}"` in `RedisCartStore.cs`; `"AddItemAsync for {userId} called"` in `SpannerCartStore.cs` and `AlloyDBCartStore.cs`; `"GetCartAsync called with userId={userId}"` in `RedisCartStore.cs`. `SpannerCartStore.cs` also logs the database connection string: `$"Spanner connection string: ${databaseString}"`. No log scrubbing, no PII masking libraries, no CloudWatch log filters, and no Amazon Macie integration.
- **Gap**: PII (userId) is written to unmasked logs. Database connection strings (potentially containing credentials) are logged. No log redaction controls exist.
- **Compensating Controls**:
  - Configure log routing to redact PII patterns before storage.
  - Restrict log access to authorized personnel only.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Replace `Console.WriteLine` with structured logging using `ILogger<T>`. Implement a PII-masking log processor that redacts userId values (e.g., hash or truncate). Remove connection string logging from `SpannerCartStore.cs`. Add log scrubbing middleware before logs reach persistent storage.
- **Evidence**: `src/cartstore/RedisCartStore.cs` (logs userId in plaintext), `src/cartstore/SpannerCartStore.cs` (logs userId and connection string), `src/cartstore/AlloyDBCartStore.cs` (logs userId)

### DISC-Q1: Schema Documentation and Versioning

- **Severity**: RISK
- **Finding**: `Cart.proto` provides a typed schema definition using proto3 syntax. The schema defines messages (`Cart`, `CartItem`, `AddItemRequest`, `EmptyCartRequest`, `GetCartRequest`, `Empty`) and service RPCs. The proto file is the source of truth for the API schema and is used for code generation via `cartservice.csproj`. However, there is no schema registry, no database migration files, no JSON Schema files, and no schema versioning beyond proto3's built-in field numbering.
- **Gap**: Schema exists but is not versioned, not published to a registry, and not documented beyond field names. No database schema migrations track changes to Spanner or AlloyDB table structures.
- **Compensating Controls**:
  - Use the proto file directly as the schema source for agent tool generation.
  - Track proto changes via version control (git history).
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Publish the proto file to a schema registry (e.g., Buf Schema Registry). Add database migration files for Spanner/AlloyDB table management. Version the proto file with a semantic version comment or package version.
- **Evidence**: `src/protos/Cart.proto` (proto3 schema), `src/cartservice.csproj` (Protobuf code generation reference)

### OBS-Q1: Distributed Tracing and Structured Logging

- **Severity**: RISK
- **Finding**: No distributed tracing or structured logging is implemented. There is no OpenTelemetry SDK, no X-Ray instrumentation, no `traceparent` header propagation, and no correlation IDs. All logging is via `Console.WriteLine` — unstructured plaintext with no log levels, no timestamps, no request IDs, and no trace context. The `cartservice.csproj` does not reference any tracing or structured logging packages.
- **Gap**: Agent-initiated requests that fail inside the cart service are undiagnosable. No way to correlate a failed gRPC call with its internal processing path. No structured log fields for automated analysis.
- **Compensating Controls**:
  - Add trace context at the gRPC client/agent orchestration layer and pass trace IDs as gRPC metadata.
  - Use container-level log aggregation to correlate logs by container/pod ID.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenTelemetry .NET SDK (`OpenTelemetry.Extensions.Hosting`, `OpenTelemetry.Instrumentation.AspNetCore`, `OpenTelemetry.Instrumentation.GrpcNetClient`). Replace `Console.WriteLine` with `ILogger<T>` and configure JSON log formatting. Add correlation ID middleware that propagates trace context through gRPC calls.
- **Evidence**: `src/cartservice.csproj` (no tracing packages), `src/cartstore/RedisCartStore.cs` (Console.WriteLine), `src/Startup.cs` (no tracing configuration)

### OBS-Q2: Alerting on Error Rates and Latency

- **Severity**: RISK
- **Finding**: No alerting configuration exists anywhere in the repository. There are no CloudWatch alarms, no anomaly detection rules, no PagerDuty/OpsGenie integration, no composite alarms, and no SLO-based alerting. The health check endpoint (`HealthCheckService.cs`) pings the backing store and returns a serving status, but this is not connected to any alerting infrastructure.
- **Gap**: No automated alerting for error rate spikes or latency degradation on the gRPC service. An agent-impacting outage would go undetected until downstream effects are observed.
- **Compensating Controls**:
  - Monitor the gRPC service at the infrastructure level (Kubernetes liveness/readiness probes using the health check endpoint).
  - Implement alerting at the agent orchestration layer based on tool call failure rates.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Deploy CloudWatch alarms on gRPC error rates and P95 latency. Configure anomaly detection for traffic pattern changes. Integrate with PagerDuty or OpsGenie for on-call notification. Define SLOs for the cart service (e.g., 99.9% availability, P95 < 200ms).
- **Evidence**: `src/services/HealthCheckService.cs` (basic health check, no alerting), absence of any alerting configuration

### ENG-Q1: Infrastructure Governance for Agent-Facing Surface

- **Severity**: RISK
- **Finding**: No IaC exists in the repository. The infrastructure that exposes the cart service (network configuration, IAM roles, secrets, API gateways) is not defined as code within this codebase. There is no Terraform, CloudFormation, CDK, Helm, or Kustomize. No drift detection configuration. No PR review requirements for infrastructure changes (because no infrastructure is defined).
- **Gap**: The agent-facing integration surface (network boundaries, IAM, secrets) is not governed by IaC in this repository. Infrastructure may be managed elsewhere, but there is no evidence of it here.
- **Compensating Controls**:
  - If IaC exists in a separate repository, reference it in documentation.
  - Implement infrastructure review requirements in the external IaC repository.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Define the cart service's infrastructure as IaC in this repository or a linked infrastructure repository. Include API gateway configuration, IAM roles, security groups, secrets management, and network policies. Enable drift detection via AWS Config rules. Require PR review for all IaC changes.
- **Evidence**: Absence of any IaC files (no .tf, no template.yaml, no cdk.json, no Chart.yaml, no kustomization.yaml)

### ENG-Q2: CI/CD with API Contract Testing

- **Severity**: RISK
- **Finding**: No CI/CD pipeline configuration exists in the repository. There are no GitHub Actions workflows, no GitLab CI configuration, no Jenkinsfile, no buildspec.yml, and no CodePipeline definitions. No contract testing, no API breaking change detection, and no schema comparison tools are present.
- **Gap**: No automated pipeline to detect breaking changes to the gRPC API before production. Proto file changes could break all connected agents and services without warning.
- **Compensating Controls**:
  - Implement manual review processes for proto file changes.
  - Use proto backward compatibility checks locally (e.g., `buf breaking`).
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Create a CI/CD pipeline (GitHub Actions or equivalent) that includes: proto backward compatibility checking (using `buf breaking`), automated unit test execution, container image building, and deployment with canary or blue/green strategy. Add consumer-driven contract tests using Pact or similar.
- **Evidence**: Absence of any CI/CD configuration files (no `.github/workflows/`, no `.gitlab-ci.yml`, no `Jenkinsfile`, no `buildspec.yml`)

### ENG-Q3: Rollback Capability

- **Severity**: RISK
- **Finding**: No rollback capability is defined in the repository. There is no blue/green deployment configuration, no CodeDeploy rollback triggers, no Helm rollback, no feature flags, no canary deployment with automatic rollback, and no traffic shifting configuration.
- **Gap**: If a deployment breaks the gRPC API, there is no defined mechanism to roll back to the previous version within 15–30 minutes.
- **Compensating Controls**:
  - Manual container image rollback using Kubernetes `kubectl rollout undo` if deployed to Kubernetes.
  - Maintain tagged container images for manual rollback.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement deployment rollback capability using Kubernetes rollout undo, Helm rollback, or blue/green deployment with traffic shifting. Add health check-based automatic rollback triggers. Tag all container images with version and commit SHA for traceability.
- **Evidence**: Absence of any deployment configuration, rollback triggers, or feature flag configuration

### ENG-Q4: API Test Coverage

- **Severity**: RISK
- **Finding**: `CartServiceTests.cs` contains 3 xunit tests: (1) `GetItem_NoAddItemBefore_EmptyCartReturned` — tests GetCart returns empty cart for new user, (2) `AddItem_ItemExists_Updated` — tests AddItem updates quantity for existing product, (3) `AddItem_New_Inserted` — tests AddItem inserts new product and EmptyCart clears items. Tests use `Microsoft.AspNetCore.TestHost` for in-memory integration testing with the in-memory cache store. Tests are referenced in `cartservice.tests.csproj` with xunit 2.9.3 and Microsoft.NET.Test.Sdk 18.3.0.
- **Gap**: Only 3 happy-path tests exist. No error case tests (what happens when Redis is unavailable?). No edge case tests (empty userId, negative quantity, very large carts). No contract tests validating proto compatibility. No tests for Spanner or AlloyDB store implementations. No tests running in CI.
- **Compensating Controls**:
  - The existing tests provide basic smoke testing confidence for the in-memory store.
  - Add contract tests incrementally as part of CI/CD implementation.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add error case tests (database unavailable, invalid input). Add contract tests validating proto backward compatibility. Add integration tests for Spanner and AlloyDB stores using test containers. Add edge case tests (empty strings, negative quantities, maximum cart sizes). Integrate tests into a CI pipeline.
- **Evidence**: `tests/CartServiceTests.cs` (3 tests), `tests/cartservice.tests.csproj` (xunit dependencies)

### ENG-Q5: Encryption at Rest for Agent-Accessible Data

- **Severity**: RISK
- **Finding**: No encryption-at-rest configuration exists in the repository. There are no KMS key references, no encryption configuration for Redis, Spanner, or AlloyDB, and no `kms_key_id` settings on any data store. Redis data is stored as serialized Protobuf bytes with no application-layer encryption. AlloyDB and Spanner may have encryption at rest enabled at the infrastructure level, but this is not configured or documented in this codebase.
- **Gap**: No evidence of encryption at rest for cart data (which includes userId — PII). Encryption may exist at the infrastructure level but is not defined or verified in this repository.
- **Compensating Controls**:
  - Verify encryption at rest is enabled at the infrastructure level for Redis, Spanner, and AlloyDB (these services typically encrypt at rest by default in managed configurations).
  - Document the encryption status in the service's operational runbook.
- **Remediation Timeline**: 30–60 days (verification and documentation)
- **Recommendation**: Verify and document that all backing stores have encryption at rest enabled. For Redis: ensure the Redis instance uses encryption at rest (ElastiCache or Memorystore encryption). For Spanner: verify CMEK or Google-managed encryption. For AlloyDB: verify encryption with customer-managed keys. Add IaC definitions for data store encryption configuration.
- **Evidence**: `src/cartservice.csproj` (no encryption libraries), absence of any encryption configuration in the repository

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO
- **Finding**: The application exposes a well-defined gRPC interface via `Cart.proto` with 3 RPCs: `AddItem(AddItemRequest) returns (Empty)`, `GetCart(GetCartRequest) returns (Cart)`, and `EmptyCart(EmptyCartRequest) returns (Empty)`. This is a typed, strongly-contracted interface using proto3 syntax under the `hipstershop` package. The implementation in `CartService.cs` maps 1:1 to the proto definition. Integration does not require direct database access, file-based exchange, or UI automation.
- **Implication**: gRPC is a well-structured integration surface for agent tools. Agent frameworks can generate tool definitions from the proto file. However, gRPC's binary Protobuf format requires a gRPC-aware client or a REST transcoding layer for agents that expect HTTP/JSON.
- **Recommendation**: Consider adding a gRPC-JSON transcoding layer (Envoy proxy or ASP.NET Core gRPC-Web) to enable HTTP/JSON access for agent frameworks that do not natively support gRPC.
- **Evidence**: `src/protos/Cart.proto` (3 RPCs defined), `src/services/CartService.cs` (implementation matches proto), `src/Startup.cs` (`MapGrpcService<CartService>()`)

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Write operations have mixed idempotency characteristics. `RedisCartStore.cs` performs read-then-write without idempotency keys — calling `AddItem` twice with the same parameters doubles the quantity rather than being idempotent. `SpannerCartStore.cs` uses `InsertOrUpdate` within a retriable transaction, providing atomicity but not true idempotency (same call doubles quantity). `AlloyDBCartStore.cs` uses `INSERT ON CONFLICT DO UPDATE` — same pattern. `EmptyCart` is naturally idempotent (emptying an empty cart is a no-op). No idempotency keys are accepted in the proto definition.
- **Implication**: For read-only agents, this is informational only. If agent_scope changes to write-enabled, the lack of idempotency on `AddItem` becomes a BLOCKER — agent retries or duplicate tool calls will create incorrect quantities.
- **Recommendation**: If write-enabled agents are planned, add an optional `idempotency_key` field to `AddItemRequest` and enforce at-most-once semantics using a deduplication check.
- **Evidence**: `src/cartstore/RedisCartStore.cs` (read-then-write, no idempotency), `src/cartstore/SpannerCartStore.cs` (InsertOrUpdate but quantity accumulates), `src/cartstore/AlloyDBCartStore.cs` (INSERT ON CONFLICT but quantity accumulates), `src/protos/Cart.proto` (no idempotency_key field)

### API-Q6: Structured Response Format

- **Severity**: INFO
- **Finding**: Response format is Protobuf (binary, strongly-typed) as defined by the gRPC protocol. The `Cart` message contains `user_id` (string) and `items` (repeated `CartItem` with `product_id` string and `quantity` int32). Protobuf is not directly consumable by LLMs, which work best with text-based formats like JSON. However, gRPC client libraries automatically deserialize Protobuf into native language objects.
- **Implication**: Agent tools must use a gRPC client library or a transcoding proxy to convert Protobuf responses to text/JSON before passing to an LLM. This adds a deserialization step but is well-supported by standard tooling.
- **Recommendation**: If agents need direct JSON access, deploy a gRPC-JSON transcoding proxy (Envoy, grpc-gateway, or ASP.NET Core gRPC-Web). Alternatively, implement tool wrappers that deserialize gRPC responses to JSON before passing to the LLM.
- **Evidence**: `src/protos/Cart.proto` (Protobuf message definitions), `src/cartservice.csproj` (`Grpc.AspNetCore` package)

### API-Q8: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: No event emission capability exists. There are no webhook endpoints, no SNS/EventBridge/SQS integration, no Kafka topics, no CDC pipelines, and no message queue publishing. State changes (add item, empty cart) are not published to any event stream. The service operates purely as request/response.
- **Implication**: Proactive agent patterns (e.g., "notify when a cart is abandoned for 30 minutes") are not possible without polling. Event-driven agent triggers would require adding an event emission layer.
- **Recommendation**: If event-driven agent patterns are planned, add event publishing for cart state changes (item added, cart emptied) to an event bus (SNS, EventBridge, or SQS). This enables proactive agents that react to cart events without polling.
- **Evidence**: Absence of any event publishing, webhook, or message queue integration in the codebase

### API-Q9: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limits are documented and no rate limit headers are returned. The gRPC service does not include `X-RateLimit-Remaining`, `Retry-After`, or equivalent metadata in responses. No API Gateway throttle settings, WAF rate rules, or rate limiting middleware exist.
- **Implication**: Agents calling the service at machine speed have no self-throttling signal. Combined with the absence of server-side rate limiting (STATE-Q5), this creates risk of agent-induced overload.
- **Recommendation**: When rate limiting is implemented (STATE-Q5), also return rate limit metadata in gRPC trailing headers (e.g., `x-ratelimit-remaining`, `x-ratelimit-reset`) so agents can self-throttle.
- **Evidence**: `src/Startup.cs` (no rate limit middleware), absence of rate limit documentation

### API-Q10: API Latency Profile

- **Severity**: INFO
- **Finding**: No performance benchmarks, load test results, CloudWatch latency metrics, or APM dashboards exist in the repository. Cart operations are simple key-value lookups (Redis) or single-table queries (Spanner/AlloyDB), suggesting sub-100ms P95 latency for typical operations. However, no measured data confirms this.
- **Implication**: Without measured latency data, agent timeout configurations must be set conservatively. If cart operations are indeed sub-100ms, synchronous agent patterns are appropriate. If latency spikes occur under load, async patterns may be needed.
- **Recommendation**: Conduct load testing and establish baseline P95 latency metrics. Publish latency SLOs (e.g., P95 < 100ms for GetCart, P95 < 200ms for AddItem). Integrate latency monitoring with the observability stack (OBS-Q1, OBS-Q2).
- **Evidence**: Absence of any performance benchmarks or latency metrics

### DATA-Q8: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality monitoring, profiling, or freshness SLAs exist. There are no data quality dashboards, no null rate monitoring, no duplicate detection logic, and no data quality metrics in observability. Cart data is simple (userId + productId + quantity) with limited data quality concerns, but no validation exists for data integrity (e.g., negative quantities, empty product IDs).
- **Implication**: An agent acting on corrupted cart data (negative quantities, orphaned product IDs) would propagate errors. Data validation at the API layer would catch these issues.
- **Recommendation**: Add input validation for `AddItem` (reject negative quantities, empty product IDs, empty user IDs). Add data quality checks for the backing store (detect orphaned cart items, carts with invalid product references).
- **Evidence**: `src/services/CartService.cs` (no input validation), `src/cartstore/RedisCartStore.cs` (no data validation)

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Field names in `Cart.proto` are semantically meaningful: `user_id`, `product_id`, `quantity` — clear, human-readable, and self-documenting. C# code uses PascalCase equivalents (`UserId`, `ProductId`, `Quantity`) following .NET conventions. No legacy abbreviations, no cryptic field names, no data dictionary required.
- **Implication**: LLM-based agents can reason about cart data field names without requiring a lookup table. This is a positive signal for agent readiness.
- **Recommendation**: Maintain the clear naming convention as the API evolves. Add descriptive comments to proto fields for additional context (e.g., constraints, valid ranges).
- **Evidence**: `src/protos/Cart.proto` (clear field names), `src/cartstore/ICartStore.cs` (PascalCase parameters)

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No data catalog, metadata layer, or data dictionary exists. The proto file serves as an implicit schema definition, but there is no centralized catalog describing what data the cart service holds, its relationships to other services' data, or its semantic meaning beyond field names.
- **Implication**: Building agent tools against this service requires reading the proto file directly. A data catalog would accelerate tool definition and help agents understand the data context.
- **Recommendation**: Create a lightweight data dictionary documenting the cart service's data model, field constraints, relationships (e.g., productId references the Product Catalog service), and access patterns.
- **Evidence**: Absence of any data catalog, metadata files, or data dictionary

### DISC-Q4: Data Lineage

- **Severity**: INFO
- **Finding**: No data lineage tools, ETL documentation, or data flow diagrams exist. Cart data originates from client requests (AddItem) and is stored in the backing store. There are no transformations, aggregations, or derived data. The data flow is simple: client → gRPC → cart store → backing database.
- **Implication**: For the cart service's simple data model, lineage is straightforward. However, if cart data feeds downstream systems (checkout, analytics), the lack of lineage documentation makes it harder to trace data issues.
- **Recommendation**: Document the cart data flow: source (client AddItem calls), storage (Redis/Spanner/AlloyDB), and consumers (checkout service, analytics). This is sufficient for the current simple data model.
- **Evidence**: Absence of any data lineage documentation or data flow diagrams

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No business outcome metrics are published. There are no custom CloudWatch metrics, no business KPI tracking, no dashboards tracking cart conversion rates, cart abandonment rates, or average cart value. The service only has basic operational logging (`Console.WriteLine`).
- **Implication**: Without business metrics, there is no way to measure whether agent interactions with the cart service produce good business outcomes (e.g., higher conversion rates, lower abandonment).
- **Recommendation**: Publish custom metrics for business events: cart creation rate, cart abandonment rate, average items per cart, cart-to-checkout conversion rate. These metrics will be critical for evaluating agent effectiveness once agents are integrated.
- **Evidence**: Absence of any custom metrics or business KPI tracking

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: The application exposes a documented gRPC interface via `Cart.proto` with 3 RPCs: `AddItem`, `GetCart`, `EmptyCart`. This is a well-defined, typed interface — not direct DB access or UI automation. The implementation in `CartService.cs` maps 1:1 to the proto definition.
- **Gap**: gRPC requires a gRPC-aware client or transcoding proxy for agents that expect HTTP/JSON.
- **Recommendation**: Consider adding a gRPC-JSON transcoding layer for broader agent framework compatibility.
- **Evidence**: `src/protos/Cart.proto`, `src/services/CartService.cs`, `src/Startup.cs`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK
- **Finding**: `Cart.proto` is the machine-readable specification (proto3 syntax). It matches the implementation. However, it lacks inline documentation and is not published to a schema registry.
- **Gap**: No API documentation beyond field names. No schema registry. No OpenAPI/REST spec for non-gRPC consumers.
- **Recommendation**: Add descriptive proto comments. Enable gRPC server reflection. Consider gRPC-JSON transcoding.
- **Evidence**: `src/protos/Cart.proto`, `src/cartservice.csproj`, `src/services/CartService.cs`

#### API-Q3: Structured Error Responses
- **Severity**: RISK
- **Finding**: All cart store implementations throw `RpcException` with `StatusCode.FailedPrecondition` for all errors. No structured error body. No retryable/non-retryable distinction. Raw exceptions leaked in messages.
- **Gap**: Single error code for all failures. No structured error details. Exception strings exposed to clients.
- **Recommendation**: Implement gRPC error interceptor with proper status code mapping and rich error model.
- **Evidence**: `src/cartstore/RedisCartStore.cs`, `src/cartstore/SpannerCartStore.cs`, `src/cartstore/AlloyDBCartStore.cs`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: `AddItem` is not idempotent — repeated calls accumulate quantity. No idempotency keys in proto. `EmptyCart` is naturally idempotent.
- **Gap**: No idempotency support on write operations. Would become BLOCKER if agent_scope changes to write-enabled.
- **Recommendation**: Add `idempotency_key` to `AddItemRequest` if write-enabled agents are planned.
- **Evidence**: `src/cartstore/RedisCartStore.cs`, `src/cartstore/SpannerCartStore.cs`, `src/cartstore/AlloyDBCartStore.cs`, `src/protos/Cart.proto`

#### API-Q5: API Versioning and Deprecation
- **Severity**: RISK
- **Finding**: Proto package named `hipstershop` with no version. No versioning scheme, no changelog, no deprecation notices.
- **Gap**: No API versioning. Breaking changes affect all clients simultaneously.
- **Recommendation**: Rename package to `hipstershop.cart.v1`. Establish proto compatibility policy.
- **Evidence**: `src/protos/Cart.proto`

#### API-Q6: Structured Response Format
- **Severity**: INFO
- **Finding**: Protobuf (binary, strongly-typed). Not directly consumable by LLMs but well-supported by gRPC client libraries.
- **Gap**: Binary format requires deserialization step for LLM consumption.
- **Recommendation**: Deploy gRPC-JSON transcoding proxy if agents need direct JSON access.
- **Evidence**: `src/protos/Cart.proto`, `src/cartservice.csproj`

#### API-Q7: Asynchronous Operation Support
- **Severity**: RISK
- **Finding**: All RPCs are synchronous request/response. No background jobs, polling, or webhook patterns. Current CRUD operations are fast, but no infrastructure for long-running operations.
- **Gap**: No async operation support. Acceptable for current scope but limits future expansion.
- **Recommendation**: Acceptable for current CRUD scope. Add async patterns if operations become long-running.
- **Evidence**: `src/services/CartService.cs`, `src/cartstore/ICartStore.cs`

#### API-Q8: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: No event emission. No webhooks, no message queues, no CDC pipelines. Purely request/response.
- **Gap**: No proactive agent patterns possible without polling.
- **Recommendation**: Add event publishing to an event bus if event-driven agent patterns are planned.
- **Evidence**: Absence of event publishing in the codebase

#### API-Q9: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limits documented. No rate limit headers returned. No API Gateway or WAF configuration.
- **Gap**: Agents have no self-throttling signal.
- **Recommendation**: Return rate limit metadata in gRPC trailing headers when rate limiting is implemented.
- **Evidence**: `src/Startup.cs`, absence of rate limit configuration

#### API-Q10: API Latency Profile
- **Severity**: INFO
- **Finding**: No performance benchmarks or latency metrics. Simple key-value operations suggest sub-100ms P95 but no measured data.
- **Gap**: No latency data for agent timeout configuration.
- **Recommendation**: Conduct load testing. Publish P95 latency SLOs.
- **Evidence**: Absence of performance benchmarks

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: No authentication configured. No `AddAuthentication()`, `UseAuthentication()`, `UseAuthorization()`, gRPC interceptors, or API key validation. `AllowedHosts: "*"` in `appsettings.json`. Any network-reachable client can call any RPC.
- **Gap**: No machine identity authentication. The `userId` parameter is a plain string with no principal attribution.
- **Recommendation**: Add ASP.NET Core JWT Bearer or mTLS authentication. Register auth middleware in `Startup.cs`.
- **Evidence**: `src/Startup.cs`, `src/services/CartService.cs`, `src/appsettings.json`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK
- **Finding**: No authorization model. No IAM policies, no roles, no permission scoping. All RPCs accessible without permission checks.
- **Gap**: No mechanism to grant read-only access while denying write operations.
- **Recommendation**: Implement gRPC authorization policies with role-based access control per RPC method.
- **Evidence**: `src/Startup.cs`, `src/services/CartService.cs`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK
- **Finding**: No action-level authorization. No ABAC, no RBAC, no permission checks on individual RPCs.
- **Gap**: Cannot restrict an agent to `GetCart` while denying `EmptyCart` at the application layer.
- **Recommendation**: Add per-RPC authorization policies with claims-based action permissions.
- **Evidence**: `src/services/CartService.cs`

#### AUTH-Q4: Identity Propagation
- **Severity**: RISK
- **Finding**: `userId` is a plain string parameter, not derived from an authenticated principal. No JWT parsing, no token exchange, no on-behalf-of flows. `ServerCallContext` unused for identity.
- **Gap**: No identity propagation. An agent could access any user's cart by passing any userId.
- **Recommendation**: Implement JWT-based identity propagation and validate `userId` against the authenticated identity.
- **Evidence**: `src/protos/Cart.proto`, `src/services/CartService.cs`

#### AUTH-Q5: Agent-as-Self vs Agent-on-Behalf-of-User
- **Severity**: RISK
- **Finding**: No identity model exists. No distinction between agent-as-self and agent-on-behalf-of-user.
- **Gap**: Cannot differentiate access patterns. Privilege escalation risk.
- **Recommendation**: Design separate auth flows for agent-as-self and agent-on-behalf-of-user with distinct logging.
- **Evidence**: `src/Startup.cs`, `src/services/CartService.cs`

#### AUTH-Q6: Credential Management
- **Severity**: RISK
- **Finding**: Mixed pattern. `AlloyDBCartStore.cs` uses Google Cloud Secret Manager for password retrieval. Redis/Spanner credentials from environment variables. AlloyDB uses superuser account (per TODO comment). No hardcoded credentials in source.
- **Gap**: Inconsistent secrets management. Superuser account. No credential rotation for Redis/Spanner.
- **Recommendation**: Extend Secret Manager to all credentials. Create dedicated app user for AlloyDB. Implement rotation.
- **Evidence**: `src/cartstore/AlloyDBCartStore.cs`, `src/Startup.cs`

#### AUTH-Q7: Immutable Audit Logging ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: No audit logging. Only `Console.WriteLine` for operational logging. No CloudTrail, no immutable storage, no authenticated principal in logs.
- **Gap**: No audit trail identifying who made requests. Console logs are ephemeral and mutable.
- **Recommendation**: Implement structured logging with audit interceptor. Route to immutable storage.
- **Evidence**: `src/cartstore/RedisCartStore.cs`, `src/cartstore/SpannerCartStore.cs`, `src/cartstore/AlloyDBCartStore.cs`, `src/services/HealthCheckService.cs`

#### AUTH-Q8: Agent Identity Suspension
- **Severity**: RISK
- **Finding**: No identity system exists to suspend. No API key revocation, no IAM deactivation, no service account disable.
- **Gap**: Cannot isolate a misbehaving agent without taking down the service.
- **Recommendation**: Implement per-agent identity with individual revocation capability (dependent on AUTH-Q1).
- **Evidence**: `src/Startup.cs`, absence of identity management

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: No compensation or rollback. Simple CRUD only. No saga patterns, no undo endpoints, no compensating transactions.
- **Gap**: No rollback for partial multi-step failures. `EmptyCart` deletes all items — no selective undo.
- **Recommendation**: Add `RemoveItem` RPC. Implement transaction logging for write-enabled scope.
- **Evidence**: `src/services/CartService.cs`, `src/cartstore/ICartStore.cs`

#### STATE-Q2: Queryable Current State
- **Severity**: RISK
- **Finding**: `GetCart` provides queryable state by userId. Basic read-before-write is possible. However, no pagination, filtering, sorting, or metadata queries.
- **Gap**: Limited query capability. Full cart retrieval only.
- **Recommendation**: Add `GetCartItem` RPC, cart metadata, and pagination support.
- **Evidence**: `src/protos/Cart.proto`, `src/services/CartService.cs`

#### STATE-Q3: Concurrency Controls
- **Severity**: RISK
- **Finding**: Redis: read-then-write without locking (race condition). Spanner: `RunWithRetriableTransactionAsync` (proper concurrency). AlloyDB: `INSERT ON CONFLICT` but read-then-write without transaction isolation.
- **Gap**: Redis and AlloyDB implementations have race conditions. No ETags or version fields.
- **Recommendation**: Redis: use WATCH/MULTI/EXEC. AlloyDB: wrap in explicit transaction. Add version fields.
- **Evidence**: `src/cartstore/RedisCartStore.cs`, `src/cartstore/SpannerCartStore.cs`, `src/cartstore/AlloyDBCartStore.cs`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK
- **Finding**: No resilience patterns. No Polly, no circuit breakers, no timeout configs, no retry logic. Only Spanner has built-in transaction retry.
- **Gap**: No protection against cascading failures from backing store outages.
- **Recommendation**: Add Polly or Microsoft.Extensions.Http.Resilience. Implement circuit breakers and timeouts.
- **Evidence**: `src/cartservice.csproj`, `src/cartstore/RedisCartStore.cs`, `src/cartstore/AlloyDBCartStore.cs`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK
- **Finding**: No rate limiting at any layer. No API Gateway, no middleware, no throttling.
- **Gap**: Runaway agent loops could DDoS the service.
- **Recommendation**: Add ASP.NET Core rate limiting or deploy an API gateway with throttling.
- **Evidence**: `src/Startup.cs`, absence of rate limit configuration

#### STATE-Q6: Blast Radius and Transaction Limits
- **Severity**: RISK
- **Finding**: No configurable limits on agent actions. No max records per operation, no per-identity limits.
- **Gap**: No blast radius controls. `EmptyCart` has no safeguards.
- **Recommendation**: Implement per-identity transaction limits per operation type.
- **Evidence**: `src/services/CartService.cs`, `src/cartstore/ICartStore.cs`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: RISK
- **Finding**: No load testing, auto-scaling, or capacity planning. Single container. AlloyDB creates new data source per request.
- **Gap**: Not tested for agent traffic patterns. Connection management may not scale.
- **Recommendation**: Load test. Implement connection pooling for AlloyDB. Add auto-scaling.
- **Evidence**: `src/Dockerfile`, `src/cartstore/AlloyDBCartStore.cs`

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State
- **Severity**: RISK
- **Finding**: No draft or pending state. `AddItem` commits immediately. No approval workflow or two-step commit.
- **Gap**: All write operations are immediate. No staging for agent-proposed changes.
- **Recommendation**: Add status field (DRAFT/CONFIRMED) for write-enabled agents.
- **Evidence**: `src/services/CartService.cs`, `src/cartstore/ICartStore.cs`

#### HITL-Q2: Configurable Approval Gates
- **Severity**: RISK
- **Finding**: No approval mechanism. All RPCs execute immediately without confirmation.
- **Gap**: No human-in-the-loop for high-risk operations.
- **Recommendation**: Add configurable approval gates at application or orchestration layer.
- **Evidence**: `src/services/CartService.cs`, absence of approval workflow

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK
- **Finding**: `Dockerfile.debug` provides debug build. In-memory fallback when no Redis configured. No docker-compose, no staging config, no seed data.
- **Gap**: No production-equivalent staging environment for agent testing.
- **Recommendation**: Create docker-compose with Redis. Add staging config and seed data scripts.
- **Evidence**: `src/Dockerfile.debug`, `src/Startup.cs`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: Stores `userId` (PII), `productId`, `quantity` with no data classification, no field-level tags, no PII detection, no access controls distinguishing sensitive from non-sensitive fields.
- **Gap**: Sensitive data unclassified. No field-level encryption. No agent-specific access controls.
- **Recommendation**: Classify data fields. Implement field-level access controls and encryption for PII.
- **Evidence**: `src/protos/Cart.proto`, `src/cartstore/RedisCartStore.cs`, `src/cartstore/SpannerCartStore.cs`, `src/cartstore/AlloyDBCartStore.cs`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: No data residency requirements documented. Connection configs from environment variables with no region constraints. No GDPR/LGPD/HIPAA references.
- **Gap**: Unknown data residency requirements. Potential compliance risk if sending userId to LLM in different region.
- **Recommendation**: Document data residency requirements. Ensure LLM endpoints co-located with data stores.
- **Evidence**: `src/Startup.cs`, `src/cartstore/AlloyDBCartStore.cs`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK
- **Finding**: `GetCart` returns all items for a userId. No pagination, filtering, or sorting. Unbounded result sets.
- **Gap**: No selective query support for agents.
- **Recommendation**: Add pagination and filter parameters to `GetCartRequest`.
- **Evidence**: `src/protos/Cart.proto`, `src/cartstore/SpannerCartStore.cs`, `src/cartstore/AlloyDBCartStore.cs`

#### DATA-Q4: System of Record Designations
- **Severity**: RISK
- **Finding**: No system-of-record designation. Three possible backing stores with no documented authority.
- **Gap**: No golden record designation for cart data.
- **Recommendation**: Document cart service as system of record for cart state.
- **Evidence**: `src/Startup.cs`

#### DATA-Q5: Reliable Timestamps
- **Severity**: RISK
- **Finding**: No timestamp fields in proto or backing stores. No `created_at`, `updated_at`, or `event_time`.
- **Gap**: Agents cannot determine data age or modification time.
- **Recommendation**: Add timestamp fields to proto messages and all store implementations.
- **Evidence**: `src/protos/Cart.proto`, `src/cartstore/RedisCartStore.cs`, `src/cartstore/SpannerCartStore.cs`

#### DATA-Q6: Data Freshness Signaling
- **Severity**: RISK
- **Finding**: No freshness signaling. No Cache-Control, no TTL on Redis entries, no consistency level indicators.
- **Gap**: Agents cannot determine if data is current, stale, or cached.
- **Recommendation**: Add `last_modified` field. Set TTL on Redis entries. Return freshness metadata in gRPC headers.
- **Evidence**: `src/cartstore/RedisCartStore.cs`, `src/protos/Cart.proto`

#### DATA-Q7: PII Redaction in Logs
- **Severity**: RISK
- **Finding**: `userId` logged in plaintext via `Console.WriteLine` in all cart stores. Spanner connection string also logged. No PII masking.
- **Gap**: PII exposed in logs. Connection strings potentially logged.
- **Recommendation**: Replace Console.WriteLine with ILogger. Implement PII masking. Remove connection string logging.
- **Evidence**: `src/cartstore/RedisCartStore.cs`, `src/cartstore/SpannerCartStore.cs`, `src/cartstore/AlloyDBCartStore.cs`

#### DATA-Q8: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality monitoring. No input validation (negative quantities, empty IDs accepted). Simple data model with limited quality concerns.
- **Gap**: No data quality metrics or input validation.
- **Recommendation**: Add input validation for AddItem. Monitor data quality metrics.
- **Evidence**: `src/services/CartService.cs`, `src/cartstore/RedisCartStore.cs`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Documentation and Versioning
- **Severity**: RISK
- **Finding**: `Cart.proto` provides typed schema (proto3). Used for code generation. No schema registry, no database migrations, no JSON Schema, no schema versioning beyond field numbering.
- **Gap**: Schema not versioned or published. No database migration files.
- **Recommendation**: Publish proto to schema registry. Add database migration files. Version the schema.
- **Evidence**: `src/protos/Cart.proto`, `src/cartservice.csproj`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Field names are clear and self-documenting: `user_id`, `product_id`, `quantity`. PascalCase equivalents in C#. No legacy abbreviations.
- **Gap**: N/A — field names are semantically meaningful.
- **Recommendation**: Maintain naming convention. Add proto field comments.
- **Evidence**: `src/protos/Cart.proto`, `src/cartstore/ICartStore.cs`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No data catalog, metadata layer, or data dictionary. Proto file serves as implicit schema.
- **Gap**: No centralized data description beyond proto file.
- **Recommendation**: Create lightweight data dictionary documenting data model and relationships.
- **Evidence**: Absence of data catalog or metadata files

#### DISC-Q4: Data Lineage
- **Severity**: INFO
- **Finding**: No data lineage tools or documentation. Simple data flow: client → gRPC → backing store.
- **Gap**: No documented data flow for downstream tracing.
- **Recommendation**: Document data flow: source, storage, and consumers.
- **Evidence**: Absence of data lineage documentation

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK
- **Finding**: No OpenTelemetry, no X-Ray, no traceparent propagation, no correlation IDs. Only `Console.WriteLine` — unstructured, no log levels, no timestamps, no request IDs.
- **Gap**: Agent-initiated failures are undiagnosable. No structured log fields.
- **Recommendation**: Add OpenTelemetry .NET SDK. Replace Console.WriteLine with ILogger and JSON formatting.
- **Evidence**: `src/cartservice.csproj`, `src/cartstore/RedisCartStore.cs`, `src/Startup.cs`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK
- **Finding**: No alerting. No CloudWatch alarms, no anomaly detection, no PagerDuty integration. Health check exists but not connected to alerting.
- **Gap**: No automated detection of service degradation.
- **Recommendation**: Deploy CloudWatch alarms. Configure anomaly detection. Define SLOs.
- **Evidence**: `src/services/HealthCheckService.cs`, absence of alerting configuration

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No business metrics. No custom CloudWatch metrics, no KPI tracking.
- **Gap**: Cannot measure business impact of agent interactions.
- **Recommendation**: Publish cart conversion, abandonment, and average value metrics.
- **Evidence**: Absence of custom metrics

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK
- **Finding**: No IaC in repository. No Terraform, CloudFormation, CDK, Helm, or Kustomize. No drift detection.
- **Gap**: Agent-facing infrastructure not governed by IaC in this repo.
- **Recommendation**: Define infrastructure as IaC. Enable drift detection. Require PR review.
- **Evidence**: Absence of IaC files

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK
- **Finding**: No CI/CD pipeline. No GitHub Actions, GitLab CI, Jenkins, or CodeBuild. No contract testing.
- **Gap**: No automated detection of breaking API changes.
- **Recommendation**: Create CI/CD with proto compatibility checking (buf breaking) and contract tests.
- **Evidence**: Absence of CI/CD configuration files

#### ENG-Q3: Rollback Capability
- **Severity**: RISK
- **Finding**: No rollback capability. No blue/green, no canary, no feature flags, no traffic shifting.
- **Gap**: No fast rollback if deployment breaks agent-facing APIs.
- **Recommendation**: Implement Kubernetes rollout undo or Helm rollback with health-based triggers.
- **Evidence**: Absence of deployment configuration

#### ENG-Q4: API Test Coverage
- **Severity**: RISK
- **Finding**: 3 xunit integration tests covering happy paths: GetCart (empty), AddItem (update), AddItem (insert) + EmptyCart. Uses in-memory store via TestHost.
- **Gap**: No error tests, no edge cases, no contract tests, no Spanner/AlloyDB store tests, no CI integration.
- **Recommendation**: Add error and edge case tests. Add contract tests. Integrate into CI.
- **Evidence**: `tests/CartServiceTests.cs`, `tests/cartservice.tests.csproj`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: RISK
- **Finding**: No encryption-at-rest configuration in repository. No KMS keys. Managed services may encrypt by default but not documented.
- **Gap**: No evidence of encryption for PII data at rest.
- **Recommendation**: Verify and document encryption at rest for all backing stores. Add IaC for encryption config.
- **Evidence**: `src/cartservice.csproj`, absence of encryption configuration

#### ENG-Q6: Cross-Origin and Network Policies
- **Severity**: BLOCKER
- **Finding**: No CORS, no security groups, no network policies, no API gateway, no firewall rules. `AllowedHosts: "*"`. Port 7070 exposed with no restrictions. No IaC defining network boundaries.
- **Gap**: No network security. Service is wide open to any network client.
- **Recommendation**: Define network policies as IaC. Restrict AllowedHosts. Add security groups and NetworkPolicies.
- **Evidence**: `src/appsettings.json`, `src/Dockerfile`, absence of IaC and network policy files

## Evidence Index

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `src/protos/Cart.proto` | API-Q1, API-Q2, API-Q4, API-Q5, API-Q6, STATE-Q2, DATA-Q1, DATA-Q3, DATA-Q5, DATA-Q6, DISC-Q1, DISC-Q2 |

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `src/services/CartService.cs` | API-Q1, API-Q7, AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q5, STATE-Q1, STATE-Q2, STATE-Q6, HITL-Q1, HITL-Q2, DATA-Q8 |
| `src/services/HealthCheckService.cs` | AUTH-Q7, OBS-Q2 |
| `src/cartstore/ICartStore.cs` | API-Q7, STATE-Q1, STATE-Q6, HITL-Q1, DISC-Q2 |
| `src/cartstore/RedisCartStore.cs` | API-Q3, API-Q4, AUTH-Q7, STATE-Q3, STATE-Q4, DATA-Q1, DATA-Q6, DATA-Q7, DATA-Q8, OBS-Q1 |
| `src/cartstore/SpannerCartStore.cs` | API-Q3, API-Q4, AUTH-Q7, STATE-Q3, DATA-Q1, DATA-Q3, DATA-Q5, DATA-Q7 |
| `src/cartstore/AlloyDBCartStore.cs` | API-Q3, API-Q4, AUTH-Q6, AUTH-Q7, STATE-Q3, STATE-Q4, STATE-Q7, DATA-Q1, DATA-Q2, DATA-Q3, DATA-Q7 |
| `src/Program.cs` | AUTH-Q1 |
| `src/Startup.cs` | API-Q1, API-Q9, AUTH-Q1, AUTH-Q2, AUTH-Q5, AUTH-Q6, AUTH-Q8, STATE-Q5, HITL-Q3, DATA-Q2, DATA-Q4, OBS-Q1 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `src/Dockerfile` | STATE-Q7, ENG-Q6 |
| `src/Dockerfile.debug` | HITL-Q3 |
| `src/.dockerignore` | — (scanned during discovery) |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `src/cartservice.csproj` | API-Q2, API-Q6, STATE-Q4, DISC-Q1, OBS-Q1, ENG-Q5 |
| `tests/cartservice.tests.csproj` | ENG-Q4 |
| `cartservice.sln` | — (scanned during discovery) |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `src/appsettings.json` | AUTH-Q1, ENG-Q6 |

### Test Files
| File | Questions Referenced |
|------|---------------------|
| `tests/CartServiceTests.cs` | ENG-Q4 |
