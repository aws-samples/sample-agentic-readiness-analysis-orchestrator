# Agentic Readiness Assessment Report

**Target**: adservice (./services/microservices-demo/src/adservice)
**Date**: 2026-04-15
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Agent Scope**: read-only
**Priority**: P2
**Tags**: java, grpc, ads
**Context**: Java gRPC service serving contextual ads based on product categories.

---

## Readiness Profile: Not Agent-Integrable

**BLOCKERs**: 3 | **RISKs**: 35 | **INFOs**: 11

Exclude from agent toolset or plan major remediation before re-evaluation. Three blockers were identified: no machine identity authentication (AUTH-Q1), no sensitive data classification (DATA-Q1), and no network security configurations (ENG-Q6). All three must be resolved before this service can be safely consumed by autonomous agents. Given the read-only, low-sensitivity nature of this ad service, targeted remediation could move it to Pilot-Ready status relatively quickly.

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
- **Finding**: The gRPC server in `AdService.java` is created with `ServerBuilder.forPort(port)` with no authentication interceptor, no TLS configuration, no API key validation, and no OAuth2 or mTLS support. The client (`AdServiceClient.java`) explicitly uses `.usePlaintext()`, confirming no transport security. The service accepts unauthenticated, unencrypted connections from any caller. There is no concept of caller identity anywhere in the codebase.
- **Gap**: No machine identity authentication exists. The service cannot identify which agent (or any caller) made a request. There is no principal attribution in logs — the service logs `context_keys` but not who sent the request.
- **Remediation**:
  - **Immediate**: Add a gRPC server interceptor that validates an API key or OAuth2 client credentials token on every request. Use `io.grpc.ServerInterceptor` to extract and validate credentials from gRPC metadata headers before the request reaches the service handler.
  - **Target State**: Every gRPC call is authenticated via client credentials OAuth 2.0 or mTLS. The authenticated principal (agent identity) is logged with every request. API keys are managed through AWS Secrets Manager with rotation support.
  - **Estimated Effort**: Medium (2–4 weeks for interceptor + identity provider integration)
  - **Dependencies**: Requires an identity provider (Cognito, Okta) or API key management infrastructure. Interacts with AUTH-Q7 (audit logging) — once identity is established, audit logs must capture it.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (lines 56–62: `ServerBuilder.forPort(port)` with no auth), `src/main/java/hipstershop/AdServiceClient.java` (lines 42–46: `.usePlaintext()`)

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: The service handles ad data consisting of redirect URLs and promotional text, hardcoded in the `createAdsMap()` method of `AdService.java`. The Ad proto message (`demo.proto`) contains only `redirect_url` and `text` fields. No PII, PHI, or financial records are present in the current dataset. However, no formal data classification exists — there are no classification tags, no field-level access controls, and no data sensitivity documentation.
- **Gap**: No data classification framework exists. While the current ad data appears non-sensitive, there is no formal classification to confirm this. If the ad service were extended to serve personalized ads (user behavior, demographics), unclassified sensitive data could enter the pipeline without detection. The absence of classification is itself the gap — agents cannot programmatically verify they are authorized to access specific data fields.
- **Remediation**:
  - **Immediate**: Document the data classification for the Ad service's data fields: `redirect_url` (public, non-sensitive), `text` (public, non-sensitive), `context_keys` (potentially user-derived, classify as internal). Add classification metadata to the proto file as comments or field options.
  - **Target State**: All data fields served by the Ad service are formally classified (public / internal / confidential / restricted). Classification metadata is machine-readable and enforced through field-level access controls if sensitive data is ever introduced.
  - **Estimated Effort**: Low (1–2 weeks for classification documentation; medium if field-level controls are added)
  - **Dependencies**: None for initial classification. If personalized ads are planned, this interacts with DATA-Q2 (data residency) and DATA-Q7 (PII redaction).
- **Evidence**: `src/main/java/hipstershop/AdService.java` (`createAdsMap()` method — hardcoded ad data), `src/main/proto/demo.proto` (Ad message definition: `redirect_url`, `text` fields only)

### ENG-Q6: Cross-Origin and Network Policies

- **Severity**: BLOCKER
- **Finding**: No network security configurations exist in the repository. The Dockerfile exposes port 9555 with no associated security group rules, firewall rules, or network policies. The gRPC server binds to the port without TLS (`ServerBuilder.forPort(port)` — no `.useTransportSecurity()`). The client explicitly disables transport security with `.usePlaintext()`. No API gateway sits in front of the service. No CORS configuration (not applicable to gRPC but relevant if a gRPC-web gateway is added). No WAF rules. No Kubernetes NetworkPolicy definitions.
- **Gap**: The service has no network security boundary defined or documented. Any network-reachable client can connect without encryption. For agent integration, network policies must define which agent identities/networks can reach this service and enforce TLS for data in transit.
- **Remediation**:
  - **Immediate**: Enable TLS on the gRPC server using `ServerBuilder.useTransportSecurity(certChain, privateKey)`. Define network security policies (Kubernetes NetworkPolicy or security group rules) that restrict access to the gRPC port (9555) to authorized callers only.
  - **Target State**: TLS is enforced for all gRPC connections. Network policies restrict access to authorized agent identities and services. Security configurations are defined as IaC (Terraform/CloudFormation) and subject to peer review. An API gateway or service mesh enforces mTLS between services.
  - **Estimated Effort**: Medium (2–3 weeks for TLS + network policies in IaC)
  - **Dependencies**: Requires IaC infrastructure (interacts with ENG-Q1). TLS certificate management requires a PKI or certificate manager (ACM, cert-manager).
- **Evidence**: `Dockerfile` (line `EXPOSE 9555` — no security boundary), `src/main/java/hipstershop/AdService.java` (lines 56–62: `ServerBuilder.forPort(port)` — no TLS), `src/main/java/hipstershop/AdServiceClient.java` (lines 42–46: `.usePlaintext()`)

---

## RISKs — Proceed with Compensating Controls

### API-Q2: Machine-Readable API Specification

- **Severity**: RISK
- **Finding**: The `demo.proto` file serves as the machine-readable API specification. While protobuf definitions are inherently machine-readable and auto-generate client/server stubs, the proto file is a shared monolith containing definitions for 10+ services (CartService, RecommendationService, ProductCatalogService, etc.) — not scoped to AdService alone. The AdService-specific definitions (AdRequest, AdResponse, Ad messages) are at the bottom of the file.
- **Gap**: No standalone AdService API specification exists. The proto file is shared across the entire microservices-demo. Agent tool definitions would need to parse the full proto to extract AdService-relevant types. No versioned API specification (e.g., `v1/adservice.proto`) exists.
- **Compensating Controls**:
  - Extract AdService-specific proto definitions into a standalone `adservice.proto` file for agent tool generation
  - Use `buf` or `protoc` tooling to generate OpenAPI specs from proto definitions for broader tooling compatibility
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a standalone `adservice.proto` containing only AdService, AdRequest, AdResponse, and Ad message definitions. Consider generating an OpenAPI spec from the proto for broader agent framework compatibility.
- **Evidence**: `src/main/proto/demo.proto` (shared proto with AdService definitions at lines ~220–240)

### API-Q3: Structured Error Responses

- **Severity**: RISK
- **Finding**: The `getAds` method in `AdService.java` catches `StatusRuntimeException` and returns gRPC status codes via `responseObserver.onError(e)`. gRPC provides native status codes (OK, INVALID_ARGUMENT, INTERNAL, etc.) but no custom error detail structure is implemented. There is no structured error body with error codes, error messages, or retryable indicators beyond the gRPC status.
- **Gap**: No structured error response format beyond gRPC status codes. Agents cannot distinguish retriable errors from terminal errors without custom error details. gRPC supports `google.rpc.Status` with detail payloads, but this is not used.
- **Compensating Controls**:
  - Agents can map gRPC status codes to retry decisions (UNAVAILABLE → retry, INVALID_ARGUMENT → don't retry)
  - Wrap the gRPC client with retry logic based on status codes
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement structured error responses using gRPC's `com.google.rpc.Status` with `ErrorInfo` details. Include an error code enum, human-readable message, and `retryable` boolean in every error response.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (lines 91–97: catch block with `StatusRuntimeException`)

### API-Q5: API Versioning and Deprecation

- **Severity**: RISK
- **Finding**: No API versioning exists. The proto package is `hipstershop` with no version prefix (e.g., `hipstershop.v1`). No deprecation policy, no changelog, no version headers. The `build.gradle` has version `0.1.0-SNAPSHOT` for the build artifact, but this is not reflected in the API contract.
- **Gap**: No API versioning strategy. Breaking changes to the `GetAds` RPC or `Ad`/`AdRequest`/`AdResponse` messages would silently break agent tool schemas without warning.
- **Compensating Controls**:
  - Proto3 has built-in backward compatibility (additive field changes are non-breaking)
  - Pin agent tool definitions to specific proto file hashes and validate on each deployment
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Adopt package-level versioning in proto (e.g., `package hipstershop.ads.v1`). Establish a deprecation policy requiring downstream notification before breaking changes. Maintain a CHANGELOG.md for API changes.
- **Evidence**: `src/main/proto/demo.proto` (line 18: `package hipstershop` — no version), `build.gradle` (line 13: `version = "0.1.0-SNAPSHOT"`)

### API-Q7: Asynchronous Operation Support

- **Severity**: RISK
- **Finding**: No async patterns exist. The `GetAds` RPC is synchronous and serves from in-memory data (ImmutableListMultimap), so responses are near-instant. No background job frameworks (Celery, Bull, SQS workers), no job status APIs, no webhook callbacks, no Step Functions.
- **Gap**: No async support. While the current operation is fast enough to not need async patterns, if the service evolves to include real-time ad bidding or external ad provider integration, the lack of async patterns would become critical.
- **Compensating Controls**:
  - Current latency is sub-second for in-memory lookup — async is not needed for the current scope
  - Monitor latency; implement async patterns if P95 exceeds 5 seconds after future changes
- **Remediation Timeline**: 60–90 days (only if service scope expands to external integrations)
- **Recommendation**: No immediate action required for current scope. If the service evolves to integrate external ad providers, implement gRPC server streaming or a polling pattern for long-running ad auction operations.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (getAds method — synchronous in-memory lookup)

### AUTH-Q2: Scoped Permissions (Least Privilege)

- **Severity**: RISK
- **Finding**: No authorization model exists. No IAM policies, no role definitions, no permission checks in the application code. The service has no concept of caller identity or scoped permissions. Any caller that can reach the gRPC port can invoke the `GetAds` RPC.
- **Gap**: No scoped permissions. An agent cannot be granted read-only access because there is no permission model at all. All callers have identical (unlimited) access.
- **Compensating Controls**:
  - Deploy the service behind an API gateway or service mesh that enforces caller-level permissions
  - Use Kubernetes NetworkPolicy to restrict which pods can access the AdService
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement scoped permissions through gRPC metadata-based authorization or deploy behind an API gateway with IAM-based access control. Define per-agent permission scopes (e.g., `ads:read`).
- **Evidence**: `src/main/java/hipstershop/AdService.java` (no authorization checks in getAds or anywhere in the service)

### AUTH-Q3: Action-Level Authorization

- **Severity**: RISK
- **Finding**: No action-level authorization. The service exposes only one RPC (`GetAds`), which is a read-only operation. No permission checks exist in the code — the `getAds` handler processes all requests without inspecting caller identity or permissions.
- **Gap**: No action-level authorization mechanism. While the service currently only has a read operation, there is no infrastructure to add action-level controls if write operations are introduced.
- **Compensating Controls**:
  - The service is read-only — blast radius is inherently limited to data exposure, not data modification
  - Implement authorization at the API gateway layer before the request reaches the service
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement a gRPC interceptor for action-level authorization that checks caller permissions against a permission matrix. Even for a read-only service, distinguishing `ads:read` from future `ads:write` permissions establishes the pattern.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (AdServiceImpl.getAds — no permission checks)

### AUTH-Q4: Identity Propagation

- **Severity**: RISK
- **Finding**: No identity propagation. The gRPC service does not inspect caller identity. No JWT parsing, no OAuth2 token exchange, no user context headers. The `AdRequest` message contains only `context_keys` — no user identity fields. The service cannot distinguish requests made on behalf of different users.
- **Gap**: No identity propagation capability. The service cannot carry originating user context through service calls. If personalized ads were needed, the service has no mechanism to know which user the request is for.
- **Compensating Controls**:
  - For current scope (non-personalized ads by category), identity propagation is not functionally required
  - Add `user_id` to gRPC metadata as a first step toward identity propagation
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add JWT/OAuth2 token propagation via gRPC metadata headers. Parse the `Authorization` metadata header in a server interceptor and make the user context available to the service handler.
- **Evidence**: `src/main/proto/demo.proto` (AdRequest: only `context_keys`, no user identity), `src/main/java/hipstershop/AdService.java` (no identity inspection in getAds)

### AUTH-Q5: Agent-as-Self vs Agent-on-Behalf-of-User

- **Severity**: RISK
- **Finding**: No distinction between agent-as-self and agent-on-behalf-of-user. No identity system exists to make this distinction. The service treats all callers identically.
- **Gap**: Cannot distinguish an agent acting under its own identity from an agent acting on behalf of a user. No separate auth flows, no audit log fields for this distinction.
- **Compensating Controls**:
  - For read-only ad serving, this distinction has lower impact than for write operations
  - Implement at the orchestration layer — the agent platform tracks whether calls are agent-initiated or user-delegated
- **Remediation Timeline**: 90–120 days
- **Recommendation**: When implementing AUTH-Q1 (machine identity), include support for two auth modes: service credentials (agent-as-self) and delegated tokens (agent-on-behalf-of-user). Log the mode in audit records.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (no identity system), `src/main/java/hipstershop/AdServiceClient.java` (no identity headers)

### AUTH-Q6: Credential Management

- **Severity**: RISK
- **Finding**: No credentials management infrastructure exists. The service currently has no external dependencies requiring credentials — it serves from in-memory data. No hardcoded secrets were found (the only environment variable is `PORT`). No secrets management configuration (no AWS Secrets Manager, no HashiCorp Vault references). No `.env` files committed to the repository.
- **Gap**: No secrets management infrastructure. When authentication is added (AUTH-Q1), credentials (API keys, OAuth2 client secrets, TLS certificates) will need secure storage and rotation support.
- **Compensating Controls**:
  - No credentials exist currently, so there is no immediate exposure
  - When credentials are introduced, use Kubernetes secrets or AWS Secrets Manager from day one
- **Remediation Timeline**: 30–60 days (aligned with AUTH-Q1 implementation)
- **Recommendation**: Implement AWS Secrets Manager or HashiCorp Vault for credential storage as part of the AUTH-Q1 remediation. Ensure automatic rotation is configured for all agent-facing credentials.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (line 55: `System.getenv().getOrDefault("PORT", "9555")` — only env var), `Dockerfile` (no secret references)

### AUTH-Q7: Immutable Audit Logging ⚡

- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: The service uses Log4j2 with JSON structured logging (`log4j2.xml`), including placeholder fields for trace/span IDs (`logging.googleapis.com/trace`, `spanId`, `traceSampled`). However, no caller identity is logged — the service logs `context_keys` from requests but not who made the request. No CloudTrail configuration. No immutable log storage (S3 with object lock). Tracing is not implemented (TODO comments in `initTracing()`).
- **Gap**: No audit logging of authenticated principals (because no authentication exists — AUTH-Q1). Logs are not immutable — they go to STDOUT/console with no tamper-evident storage configured. No CloudTrail or equivalent audit trail.
- **Compensating Controls**:
  - JSON structured logging is already configured — adding identity fields is incremental once AUTH-Q1 is resolved
  - Route container logs to CloudWatch Logs with retention policies as an interim measure
- **Remediation Timeline**: 60–90 days (dependent on AUTH-Q1 completion)
- **Recommendation**: After implementing AUTH-Q1, add the authenticated principal to every log entry. Configure log shipping to CloudWatch Logs or S3 with object lock for immutability. Enable CloudTrail for API-level audit logging.
- **Evidence**: `src/main/resources/log4j2.xml` (JSON structured logging with trace ID placeholders), `src/main/java/hipstershop/AdService.java` (lines 87–88: logs `context_keys` but not caller identity; lines 163–175: `initTracing()` with TODO)

### AUTH-Q8: Agent Identity Suspension

- **Severity**: RISK
- **Finding**: No agent identity suspension capability. No API key revocation endpoints, no IAM role management, no mechanism to disable individual callers. Since no authentication exists (AUTH-Q1), there is no identity to suspend.
- **Gap**: Cannot suspend a misbehaving agent without taking down the entire service. No per-caller revocation mechanism.
- **Compensating Controls**:
  - Network-level blocking (firewall rules, security group changes) as emergency measure
  - API gateway-level API key revocation if deployed behind a gateway
- **Remediation Timeline**: 60–90 days (dependent on AUTH-Q1 completion)
- **Recommendation**: When implementing AUTH-Q1, ensure the identity system supports per-agent suspension. If using API keys, include a revocation endpoint. If using OAuth2, support token revocation. Test that suspension takes effect within seconds.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (no identity system, no revocation mechanism)

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: The service is stateless — it serves ads from an in-memory `ImmutableListMultimap` populated at startup by `createAdsMap()`. No write operations exist. No multi-step workflows. No database transactions. No state mutations of any kind.
- **Gap**: No compensation or rollback mechanism exists. For the current read-only design, this is acceptable. However, if the service evolves to support ad campaign management (create/update/delete ads), compensation patterns would be needed.
- **Compensating Controls**:
  - Service is purely read-only — no state mutations to compensate or roll back
  - No write endpoints exist in the proto definition for AdService
- **Remediation Timeline**: No immediate action required. Implement if write operations are added.
- **Recommendation**: No action needed for current read-only scope. If write operations are added, implement saga patterns or explicit undo endpoints for multi-step ad campaign operations.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (`createAdsMap()` — static, immutable data), `src/main/proto/demo.proto` (AdService: only `GetAds` RPC — read-only)

### STATE-Q2: Queryable Current State

- **Severity**: RISK
- **Finding**: The `GetAds` RPC returns current ad state based on `context_keys`. The data is static and hardcoded in `createAdsMap()`. The service exposes queryable state through the gRPC interface, but only by category — there is no endpoint to list all ads, query ad metadata, or inspect the full state of the ad inventory.
- **Gap**: Limited queryability. An agent can query ads by category but cannot inspect the full ad inventory, available categories, or ad metadata. No introspection endpoints.
- **Compensating Controls**:
  - Agents can discover available ads by querying known categories (clothing, accessories, footwear, hair, decor, kitchen)
  - Add a `ListCategories` RPC to expose available categories
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a `ListCategories` RPC that returns all available ad categories and ad counts. This enables agents to understand the full state space before querying specific categories.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (`getAdsByCategory`, `getRandomAds` — category-based and random access only), `src/main/proto/demo.proto` (AdRequest: only `context_keys` for filtering)

### STATE-Q3: Concurrency Controls

- **Severity**: RISK
- **Finding**: Data is immutable — stored in `ImmutableListMultimap` and `ImmutableMap` from Google Guava. No write operations exist, so no race conditions are possible. The service is inherently thread-safe for concurrent reads.
- **Gap**: No explicit concurrency controls (optimistic locking, ETags, version fields). For the current read-only, immutable-data design, this is acceptable. However, no infrastructure exists if write operations are introduced.
- **Compensating Controls**:
  - Immutable data structures guarantee thread safety for reads
  - gRPC handles concurrent requests natively via Netty's event loop
- **Remediation Timeline**: No immediate action required. Implement if write operations are added.
- **Recommendation**: No action needed for current scope. If write operations are added (ad CRUD), implement optimistic locking with version fields on ad records and conditional writes.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (line 99: `ImmutableListMultimap<String, Ad> adsMap` — immutable data structure)

### STATE-Q4: Circuit Breakers and Resilience

- **Severity**: RISK
- **Finding**: No circuit breakers or resilience patterns. The service has no external dependency calls — it serves entirely from in-memory data. No Resilience4j, no retry decorators, no timeout configurations on outbound HTTP clients (because there are no outbound calls). The only dependencies are gRPC framework and Log4j2.
- **Gap**: No resilience patterns exist. For the current self-contained design this is acceptable, but if the service evolves to call external ad providers or databases, circuit breakers would be needed.
- **Compensating Controls**:
  - Service has zero external dependencies — no cascading failure risk from downstream services
  - gRPC framework handles connection lifecycle and thread management
- **Remediation Timeline**: No immediate action required. Implement if external dependencies are added.
- **Recommendation**: No action needed for current scope. If external dependencies are added (ad databases, bidding services), add Resilience4j circuit breakers with exponential backoff on all outbound calls.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (no outbound HTTP/gRPC calls), `build.gradle` (no resilience library dependencies)

### STATE-Q5: Rate Limiting and Throttling

- **Severity**: RISK
- **Finding**: No rate limiting at any layer. No API Gateway throttling configuration. No WAF rate rules. No application-level rate limiting middleware. The gRPC server accepts unlimited connections on port 9555. No `grpc-max-concurrent-streams` or connection limit configuration.
- **Gap**: No rate limiting. A runaway agent loop could DDoS the service at machine speed. While the service is lightweight (in-memory lookup), unlimited request volume could exhaust memory or CPU.
- **Compensating Controls**:
  - Deploy behind an API gateway or service mesh with rate limiting enabled
  - Configure Kubernetes resource limits to cap CPU/memory per pod
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add rate limiting through one of: (1) gRPC server interceptor with per-client rate limits, (2) API gateway throttling in front of the service, or (3) service mesh rate limiting (Istio/App Mesh). Configure `maxConcurrentCallsPerConnection` on the gRPC server.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (lines 56–62: `ServerBuilder.forPort(port)` — no rate limiting config), `Dockerfile` (no resource limits)

### STATE-Q6: Blast Radius and Transaction Limits

- **Severity**: RISK
- **Finding**: No configurable transaction limits. The service is read-only with no write operations, so the blast radius from agent errors is limited to excessive read volume (resource exhaustion). `MAX_ADS_TO_SERVE = 2` limits response size but not request volume. No per-agent-identity request limits.
- **Gap**: No mechanism to limit request volume per agent identity. While blast radius is inherently low for a read-only service, uncontrolled request volume could still exhaust resources.
- **Compensating Controls**:
  - Read-only service — no data modification risk
  - `MAX_ADS_TO_SERVE = 2` caps response payload size
  - Rate limiting (STATE-Q5) would provide partial mitigation
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement per-agent-identity request quotas (e.g., max 1000 requests/minute per agent). This is best implemented at the API gateway or service mesh layer rather than in the application.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (line 46: `MAX_ADS_TO_SERVE = 2` — only limit found)

### STATE-Q7: Infrastructure Capacity for Agent Traffic

- **Severity**: RISK
- **Finding**: No load test results or auto-scaling configuration found. The Dockerfile defines a single container with no resource limits (`EXPOSE 9555`, `ENTRYPOINT` — no JVM heap size, no CPU/memory constraints). No capacity planning documentation. No auto-scaling policies. The service uses Gradle 8.14, Java 21, and serves from in-memory data.
- **Gap**: No evidence that the service has been tested for agent-level traffic patterns. No auto-scaling configuration. No resource limits defined in the container specification.
- **Compensating Controls**:
  - In-memory lookup should handle high throughput (no I/O bottleneck)
  - Kubernetes HPA can be configured externally without modifying the service
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add JVM heap configuration (`-Xmx`, `-Xms`) to the Dockerfile entrypoint. Define Kubernetes resource requests/limits. Conduct load testing to establish a baseline. Configure Horizontal Pod Autoscaler (HPA) based on CPU/request metrics.
- **Evidence**: `Dockerfile` (no JVM tuning, no resource limits), `build.gradle` (commented-out JVM agent opts)

### HITL-Q1: Draft/Pending State

- **Severity**: RISK
- **Finding**: No draft/pending state concept. The service returns ads directly from the in-memory map — no workflow states, no approval mechanisms. The service is purely a read-only query service. There is no concept of "staging" an ad before it goes live.
- **Gap**: No draft state for ads. If agents were to manage ad content in the future, there would be no mechanism for human review before publication.
- **Compensating Controls**:
  - Service is read-only — no actions that would benefit from draft/approval states
  - Implement draft states in an ad management service if write capability is added
- **Remediation Timeline**: No immediate action for current read-only scope. 60–90 days if write capability is planned.
- **Recommendation**: No action for current scope. If ad management capabilities are added, implement a status field (DRAFT → PENDING_REVIEW → ACTIVE → ARCHIVED) with explicit transition endpoints.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (createAdsMap — ads go directly into the active serving map)

### HITL-Q2: Configurable Approval Gates

- **Severity**: RISK
- **Finding**: No configurable approval gates. No approval API endpoints, no workflow engines, no Step Functions with human approval tasks. The service has no operations that modify state.
- **Gap**: No approval gate infrastructure. If write operations are added, there is no mechanism for requiring human approval for high-risk operations.
- **Compensating Controls**:
  - Read-only service — no operations that require approval
  - Implement approval at the orchestration layer (agent platform) rather than in the service
- **Remediation Timeline**: No immediate action for current scope. 60–90 days if write capability is planned.
- **Recommendation**: No action for current scope. If write capability is added, implement configurable approval gates using operation-level flags that route specific actions through a human approval workflow.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (no write operations, no approval logic), `src/main/proto/demo.proto` (AdService: only GetAds RPC)

### HITL-Q3: Sandbox/Staging Environment

- **Severity**: RISK
- **Finding**: A Dockerfile exists that enables local container builds. The README documents local build instructions (`./gradlew installDist`). However, no Docker Compose file exists for local testing with dependencies. No separate environment configurations (staging, sandbox). Data is hardcoded, so no seed data scripts are needed. No synthetic data generators.
- **Gap**: No sandbox or staging environment configuration. While the service can be built and run locally, there is no production-equivalent staging environment for agent testing.
- **Compensating Controls**:
  - Dockerfile enables local container builds for basic testing
  - Hardcoded data means any instance has the same data — no data divergence risk between environments
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a Docker Compose configuration for local integration testing. Define staging environment configuration that mirrors production topology. Add environment-specific configuration (e.g., `application-staging.yaml`) for environment differentiation.
- **Evidence**: `Dockerfile` (multi-stage build for containerization), `README.md` (local build instructions)

### DATA-Q2: Data Residency and Sovereignty ⚡

- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: The ad data is non-sensitive and hardcoded (product redirect URLs and promotional text). No data residency requirements are apparent. No GDPR/LGPD compliance references. No cross-region replication settings. No data sovereignty policies documented.
- **Gap**: No data residency documentation or controls. While the current ad data does not appear to be subject to residency requirements, there is no formal assessment. If the service processes user-derived context_keys from EU users, GDPR considerations may apply.
- **Compensating Controls**:
  - Current data (ad text, product URLs) is non-personal and non-regulated
  - Context_keys are ephemeral request parameters, not stored
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document that the AdService data (static ad content) is not subject to data residency requirements. If `context_keys` are derived from user behavior, assess whether they constitute personal data under GDPR and document accordingly.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (createAdsMap — static ad content), `src/main/proto/demo.proto` (AdRequest: context_keys — potentially user-derived)

### DATA-Q3: Selective Query Support

- **Severity**: RISK
- **Finding**: The `GetAds` RPC accepts `context_keys` for filtering ads by category. `MAX_ADS_TO_SERVE = 2` provides a hard-coded result size limit for random ads. However, there is no pagination, no sorting, no cursor-based iteration, and no configurable result size limit. Category-based filtering returns all ads in the category.
- **Gap**: Limited selective query support. No pagination or sorting. Result size is hardcoded at 2 for random ads but unbounded for category-based queries (currently 1–2 ads per category due to hardcoded data, but no enforced limit).
- **Compensating Controls**:
  - Small dataset (7 ads total) means unbounded queries return minimal data
  - `MAX_ADS_TO_SERVE = 2` limits random ad responses
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add pagination support to the `GetAds` RPC (e.g., `max_results` and `page_token` fields in `AdRequest`). Add a `ListCategories` RPC for discovery. Enforce result size limits regardless of query type.
- **Evidence**: `src/main/proto/demo.proto` (AdRequest: only `context_keys`, no pagination fields), `src/main/java/hipstershop/AdService.java` (line 46: `MAX_ADS_TO_SERVE = 2`)

### DATA-Q4: System of Record Designations

- **Severity**: RISK
- **Finding**: Ad data is hardcoded in the application source code in the `createAdsMap()` method of `AdService.java`. There is no external data store, no database, no API for ad management. The source code IS the system of record. No master data management process exists.
- **Gap**: No formal system-of-record designation. The source code serving as the data store creates tight coupling between deployment and data changes. No conflict resolution logic.
- **Compensating Controls**:
  - Source code as system of record means data is version-controlled (Git)
  - Single source of truth — no conflicting data stores
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Document the AdService source code as the current system of record for ad data. Plan migration to an external data store (DynamoDB, RDS) to decouple data management from deployment. Designate the external store as the authoritative system of record.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (createAdsMap — hardcoded ad data in source code)

### DATA-Q5: Reliable Timestamps

- **Severity**: RISK
- **Finding**: No timestamps on data. The `Ad` proto message contains only `redirect_url` and `text` — no `created_at`, `updated_at`, or `event_time` fields. The ad data is static and hardcoded, so temporal data is inherently absent.
- **Gap**: No temporal metadata on ad data. Agents performing time-sensitive reasoning (e.g., "show only recent promotions") have no timestamp data to filter on.
- **Compensating Controls**:
  - Static data means all ads are effectively "current" as of the last deployment
  - Deployment timestamp could serve as a proxy for data freshness
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `created_at` and `updated_at` fields to the `Ad` proto message. When migrating to an external data store, enforce UTC timestamps on all records.
- **Evidence**: `src/main/proto/demo.proto` (Ad message: only `redirect_url` and `text`, no timestamp fields)

### DATA-Q6: Data Freshness Signaling

- **Severity**: RISK
- **Finding**: No data freshness signaling. No `Cache-Control` equivalent in gRPC responses. No `last_refreshed` field. No `data_age` metadata. The data is static and immutable (hardcoded at compile time), but the API does not communicate this to callers.
- **Gap**: Agents have no way to know whether the data they receive is current, cached, or stale. For static data this is acceptable, but if the service moves to dynamic data, freshness signaling becomes critical.
- **Compensating Controls**:
  - Data is immutable — it cannot become stale without a redeployment
  - Document in the API specification that ad data is static until redeployment
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a `data_freshness` field to `AdResponse` indicating the data source (e.g., `STATIC`, `CACHED`, `LIVE`) and a `last_updated` timestamp. For gRPC, use response metadata headers.
- **Evidence**: `src/main/proto/demo.proto` (AdResponse: only `repeated Ad ads`, no freshness metadata), `src/main/java/hipstershop/AdService.java` (static ImmutableListMultimap — no cache/freshness logic)

### DATA-Q7: PII Redaction in Logs

- **Severity**: RISK
- **Finding**: The service logs `context_keys` from incoming requests (`logger.info("received ad request (context_words=" + req.getContextKeysList() + ")")`). Context keys could theoretically contain user-derived search terms or browsing context. Log4j2 is configured with JSON structured logging (`log4j2.xml`) but no PII masking or scrubbing middleware exists. No Amazon Macie integration. No regex-based PII filtering in the logging pipeline.
- **Gap**: No PII redaction in logs. If `context_keys` contain user-derived data (search queries, browsing categories), they would be logged without redaction. No log scrubbing middleware exists.
- **Compensating Controls**:
  - Current context_keys are product categories (clothing, accessories, etc.) — not PII
  - Implement PII detection at the log aggregation layer (CloudWatch Logs data protection)
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a log sanitization interceptor that redacts or masks potentially sensitive fields before logging. Evaluate whether `context_keys` could contain user-derived PII and implement appropriate masking. Configure CloudWatch Logs data protection policies.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (line 87: logs context_keys), `src/main/resources/log4j2.xml` (JSON structured logging — no PII masking)

### DISC-Q1: Schema Documentation and Versioning

- **Severity**: RISK
- **Finding**: The `demo.proto` file serves as schema documentation. Protobuf defines message types with field names, types, and field numbers — inherently versioned at the field level (proto3 backward compatibility). However, no schema versioning strategy exists at the API level (no `v1`, `v2` package prefixes). No schema registry. No migration files.
- **Gap**: No schema versioning beyond proto3's built-in field numbering. No formal schema evolution policy. No schema registry for discoverability.
- **Compensating Controls**:
  - Proto3 field numbering provides built-in backward compatibility for additive changes
  - The proto file is version-controlled in Git
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Adopt package-level versioning (`hipstershop.ads.v1`). Publish proto definitions to a schema registry (e.g., Buf Schema Registry) for discoverability. Document schema evolution policies.
- **Evidence**: `src/main/proto/demo.proto` (proto3 syntax, unversioned package `hipstershop`)

### OBS-Q1: Distributed Tracing and Structured Logging

- **Severity**: RISK
- **Finding**: Partial observability. `log4j2.xml` configures JSON structured logging with placeholder fields for trace/span IDs (`logging.googleapis.com/trace`, `spanId`, `traceSampled`). However, the `initTracing()` method in `AdService.java` contains `TODO(arbrown) Implement OpenTelemetry tracing` — tracing is NOT implemented. The `initStats()` method similarly has a TODO for OpenTelemetry stats. JSON structured logging works, but trace/span ID fields are empty (populated from unset MDC context variables `${ctx:traceId}`, `${ctx:spanId}`).
- **Gap**: Distributed tracing is not functional. Structured logging is configured but trace correlation IDs are not populated. Agent-initiated requests cannot be traced through the system.
- **Compensating Controls**:
  - JSON structured logging infrastructure is in place — adding tracing is incremental
  - Log4j2 MDC (Mapped Diagnostic Context) is ready for trace ID injection
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement OpenTelemetry tracing as indicated by the existing TODO. Add the OpenTelemetry Java SDK and gRPC instrumentation to `build.gradle`. Configure the OTel agent to populate Log4j2 MDC with trace/span IDs. Export traces to AWS X-Ray or a compatible backend.
- **Evidence**: `src/main/resources/log4j2.xml` (JSON layout with trace ID placeholders), `src/main/java/hipstershop/AdService.java` (lines 163–175: `initTracing()` with TODO, lines 151–161: `initStats()` with TODO)

### OBS-Q2: Alerting on Error Rates and Latency

- **Severity**: RISK
- **Finding**: No alerting thresholds configured anywhere in the repository. No CloudWatch alarms, no anomaly detection configuration, no PagerDuty or OpsGenie integration. No monitoring configuration files. No SLO definitions. No composite alarms.
- **Gap**: No alerting infrastructure. If the AdService degrades (elevated error rates, increased latency), there is no mechanism to detect or alert before agents start experiencing failures.
- **Compensating Controls**:
  - Configure alerting at the infrastructure layer (Kubernetes, CloudWatch) without modifying the service
  - JSON structured logging enables log-based alerting as an interim measure
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Define CloudWatch alarms for gRPC error rates (non-OK status codes) and P95 latency. Configure composite alarms that trigger when both error rate and latency exceed thresholds. Integrate with PagerDuty or OpsGenie for on-call notification.
- **Evidence**: No monitoring configuration files found in the repository. Absence is itself a finding.

### ENG-Q1: Infrastructure Governance for Agent-Facing Surface

- **Severity**: RISK
- **Finding**: No infrastructure-as-code for the deployment surface. No Terraform, CloudFormation, or CDK files. The Dockerfile defines the container build but no IaC defines API gateways, IAM roles, network configurations, or secrets. No peer review process for infrastructure changes is documented. No drift detection configuration (no AWS Config rules).
- **Gap**: The agent-facing integration surface (gRPC endpoint, network access, identity configuration) is not defined as code, not subject to automated review, and not monitored for drift. All three sub-checks fail: (1) no IaC for integration surface, (2) no review process, (3) no drift detection.
- **Compensating Controls**:
  - Dockerfile provides reproducible container builds
  - Infrastructure may be managed in a separate IaC repository (not assessable from this repo alone)
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Define the AdService deployment infrastructure as IaC (Terraform or CDK): API gateway/service mesh configuration, IAM roles, network policies, and secrets. Require PR review for IaC changes. Enable AWS Config drift detection for the agent-facing surface.
- **Evidence**: `Dockerfile` (container build only — no deployment infrastructure), No IaC files found in repository.

### ENG-Q2: CI/CD with API Contract Testing

- **Severity**: RISK
- **Finding**: No CI/CD pipeline defined in the repository. No GitHub Actions workflows (`.github/workflows/`), no Jenkinsfile, no `buildspec.yml`, no GitLab CI configuration. No API contract testing, no consumer-driven contract tests (Pact), no proto validation in a build pipeline.
- **Gap**: No CI/CD pipeline. API contract changes (proto modifications) cannot be automatically detected or validated before production deployment. No breaking change detection for the gRPC interface.
- **Compensating Controls**:
  - CI/CD may exist in a separate repository or platform (not assessable from this repo)
  - Proto3 backward compatibility provides some protection against accidental breaking changes
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement a CI/CD pipeline (GitHub Actions recommended) that includes: (1) proto compilation validation, (2) backward compatibility checks using `buf breaking`, (3) unit test execution, and (4) container image build and push.
- **Evidence**: No CI/CD configuration files found in repository. Absence is itself a finding.

### ENG-Q3: Rollback Capability

- **Severity**: RISK
- **Finding**: No rollback capability defined in the repository. No blue/green deployment configuration. No CodeDeploy rollback triggers. No Helm rollback configuration. No feature flags. No canary deployment with automatic rollback. No traffic shifting configuration.
- **Gap**: No rollback mechanism. If a deployment breaks the gRPC API that agents depend on, there is no defined process to revert to the previous version.
- **Compensating Controls**:
  - Container images with version tags enable manual rollback by redeploying a previous image
  - Kubernetes Deployment rollback (`kubectl rollout undo`) if deployed on Kubernetes
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement automated rollback triggers: (1) configure health checks that detect broken gRPC endpoints, (2) use Kubernetes rolling update with readiness probes, (3) define rollback criteria (error rate > 5% → automatic rollback). Target: rollback within 15 minutes.
- **Evidence**: `Dockerfile` (container build enables image-based rollback), No deployment configuration files found.

### ENG-Q4: API Test Coverage

- **Severity**: RISK
- **Finding**: No automated tests found in the repository. The `src/` directory contains only `main/java/` — no `test/` directory, no test files. No test dependencies in `build.gradle` (no JUnit, no Mockito, no gRPC testing framework). No API test suites (no Postman/Newman collections, no pytest, no REST Assured). No contract tests. No integration test configuration.
- **Gap**: Zero test coverage. No automated validation of API behavior, input handling, output format, error responses, or edge cases. Changes to the `GetAds` RPC could break agent integrations without detection.
- **Compensating Controls**:
  - `AdServiceClient.java` serves as a manual smoke test client
  - gRPC proto compilation provides compile-time contract validation
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add gRPC unit tests using `io.grpc:grpc-testing` and JUnit 5. Test: (1) GetAds with valid category returns correct ads, (2) GetAds with empty context returns random ads, (3) GetAds with unknown category returns random ads, (4) error response format. Add test dependencies to `build.gradle` and integrate into CI pipeline.
- **Evidence**: `build.gradle` (no test dependencies), No `src/test/` directory found. Absence is itself a finding.

### ENG-Q5: Encryption at Rest for Agent-Accessible Data

- **Severity**: RISK
- **Finding**: No encryption at rest configuration. No KMS key references in any file. No encryption configuration in IaC (no IaC exists). The service uses in-memory data with no persistent storage — ad data is hardcoded in the Java source and loaded into memory at startup.
- **Gap**: No encryption at rest. While the current service has no persistent storage (data is in-memory), there is no encryption framework for future data stores. No KMS integration.
- **Compensating Controls**:
  - No persistent data storage — in-memory only, so encryption at rest is less critical
  - When persistent storage is added, encryption should be configured from day one
- **Remediation Timeline**: 60–90 days (aligned with data store migration)
- **Recommendation**: When migrating ad data to an external store (DynamoDB, RDS, S3), enable encryption at rest with customer-managed KMS keys from day one. Include `kms_key_id` configuration in IaC for all data stores.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (in-memory data only — no persistent storage), `build.gradle` (no encryption/KMS dependencies)

---

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO
- **Finding**: The service exposes a documented gRPC interface. The `AdService` is defined in `demo.proto` with a `GetAds` RPC accepting `AdRequest` and returning `AdResponse`. The implementation in `AdService.java` extends `AdServiceGrpc.AdServiceImplBase`, auto-generated from the proto definition. The gRPC health check service is also registered (`healthMgr.getHealthService()`). This is a proper programmatic API — not direct database access, file-based exchange, or UI automation.
- **Implication**: The gRPC interface satisfies the minimum viable integration surface for agents. gRPC tools can auto-generate client stubs from the proto definition, enabling direct agent tool binding. The service is well-suited for agent consumption via gRPC client libraries.
- **Recommendation**: No action required. The gRPC interface is a strong foundation. Consider adding a gRPC reflection service (`io.grpc.protobuf.services.ProtoReflectionService`) to enable runtime API discovery by agents.
- **Evidence**: `src/main/proto/demo.proto` (AdService definition: `rpc GetAds(AdRequest) returns (AdResponse)`), `src/main/java/hipstershop/AdService.java` (AdServiceImpl extends AdServiceGrpc.AdServiceImplBase)

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The `GetAds` RPC is a read-only operation. No write endpoints exist in the AdService proto definition. The service serves ads from an in-memory `ImmutableListMultimap` — no state mutations occur. Idempotency is inherently satisfied for read operations.
- **Implication**: Read-only agents do not execute write operations, so idempotency is not a concern for the current scope. If write operations are added in the future and the agent scope changes to write-enabled, this would need re-evaluation as a BLOCKER.
- **Recommendation**: No action required for current read-only scope. If write operations are added, implement idempotency keys on all write endpoints.
- **Evidence**: `src/main/proto/demo.proto` (AdService: only `GetAds` RPC — read-only), `src/main/java/hipstershop/AdService.java` (no write operations)

### API-Q6: Structured Response Format

- **Severity**: INFO
- **Finding**: Response format is Protocol Buffers (protobuf) — binary, strongly-typed, and machine-readable. gRPC uses protobuf serialization natively. The `AdResponse` message contains `repeated Ad ads`, where each `Ad` has `redirect_url` (string) and `text` (string). The format is well-defined and auto-generates type-safe client code.
- **Implication**: Protobuf is strongly-typed and machine-readable, which is ideal for agent tool binding. However, it's binary — LLMs consuming raw protobuf would need serialization to text/JSON. gRPC-JSON transcoding or a gRPC-web gateway could bridge this gap.
- **Recommendation**: Consider adding gRPC-JSON transcoding (e.g., via Envoy or grpc-gateway) to expose a JSON REST API alongside gRPC for agent frameworks that prefer text-based formats.
- **Evidence**: `src/main/proto/demo.proto` (Ad message: `redirect_url` string, `text` string), `build.gradle` (protobuf and gRPC dependencies)

### API-Q8: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: No event emission capability. No webhooks, no SNS/EventBridge/SQS integration, no Kafka topics, no CDC pipelines. The service is purely request/response — it serves ads on demand and does not emit events for state changes.
- **Implication**: The service has no state changes to emit events for (static, read-only data). Event-driven agent patterns are not applicable to the current design. If the service evolves to support dynamic ad inventory (ad creation, updates, expiry), event emission would enable proactive agents that react to ad catalog changes.
- **Recommendation**: No action required for current scope. If dynamic ad management is added, consider publishing ad catalog change events to EventBridge or SNS.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (no event publishing code), `build.gradle` (no messaging library dependencies)

### API-Q9: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limit documentation or headers. No API Gateway throttle settings. No WAF rate rules. No rate limiting middleware. The gRPC server does not return rate limit headers or metadata. No `X-RateLimit-Remaining` or `Retry-After` equivalents in gRPC response metadata.
- **Implication**: Agents calling this service have no rate limit awareness. They will call at machine speed without self-throttling guidance. For a lightweight in-memory service this is less critical, but rate limit headers would enable well-behaved agent clients.
- **Recommendation**: When rate limiting is implemented (STATE-Q5), include rate limit metadata in gRPC response headers (`x-ratelimit-remaining`, `x-ratelimit-reset`) so agents can self-throttle.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (no rate limit logic or response metadata)

### API-Q10: API Latency Profile

- **Severity**: INFO
- **Finding**: No performance benchmarks or load test results found. The service uses in-memory data (`ImmutableListMultimap`) with no I/O operations — lookups are O(1) hash map operations. Expected latency is sub-millisecond for the business logic, plus gRPC framework overhead. No CloudWatch latency metrics, no APM dashboards.
- **Implication**: In-memory lookup should yield sub-millisecond P95 latency for the business logic. gRPC framework and network add overhead. For agent tool chaining, this service is unlikely to be a latency bottleneck. However, without actual measurements, this is an assumption.
- **Recommendation**: Conduct load testing to establish actual P95 latency under realistic traffic. Publish latency metrics to CloudWatch or an APM solution for ongoing monitoring.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (in-memory ImmutableListMultimap lookup — expected sub-ms), No load test results found.

### DATA-Q8: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality metrics exist. Ad data is hardcoded in `createAdsMap()` — 7 ads across 6 categories. By definition, the hardcoded data is 100% complete with no nulls, no duplicates, and no staleness. No data profiling, no quality dashboards, no freshness SLAs.
- **Implication**: Data quality is perfect for the current static dataset. However, if the service migrates to a dynamic data source, data quality monitoring becomes essential. Agents acting on incomplete or stale ad data would serve poor recommendations.
- **Recommendation**: No action for current scope. When migrating to a dynamic data source, implement data quality monitoring: null rate checks, duplicate detection, freshness SLAs, and data completeness metrics.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (createAdsMap — 7 hardcoded ads, complete by definition)

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Field names are semantically meaningful throughout the codebase. In `demo.proto`: `context_keys`, `redirect_url`, `text`, `product_id`, `quantity` — all human-readable. In Java code: `adsMap`, `getAdsByCategory`, `getRandomAds`, `MAX_ADS_TO_SERVE` — clear naming conventions. No legacy abbreviations or cryptic codes found.
- **Implication**: LLM-based agents can reason about field names without a data dictionary lookup. The clear naming reduces tool definition complexity and improves agent reasoning quality.
- **Recommendation**: No action required. Maintain current naming conventions. Document any domain-specific terms if introduced.
- **Evidence**: `src/main/proto/demo.proto` (clear field names: `context_keys`, `redirect_url`, `text`), `src/main/java/hipstershop/AdService.java` (clear method names: `getAdsByCategory`, `getRandomAds`)

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No data catalog or metadata layer. No AWS Glue Data Catalog, no Collibra, Alation, or DataHub integration. No metadata files. No API catalog. The proto file is the only schema documentation.
- **Implication**: Agent tool builders must manually inspect the proto file to understand what data the service holds. A data catalog would accelerate tool definition and enable automated discovery.
- **Recommendation**: Register the AdService proto definitions in a schema registry (e.g., Buf Schema Registry) or API catalog. Add service metadata (owner, description, SLA, data classification) to enable automated discovery.
- **Evidence**: `src/main/proto/demo.proto` (only schema documentation available), No data catalog configuration found.

### DISC-Q4: Data Lineage

- **Severity**: INFO
- **Finding**: No data lineage. Ad data is hardcoded in source code (`createAdsMap()`) with no lineage record. No ETL pipelines, no transformation logs, no source-to-target mappings. The origin of ad data is the source code itself.
- **Implication**: Data lineage is trivial for the current design — the source code IS the origin. If the service migrates to a dynamic data source (database, CMS, ad exchange), lineage becomes important for tracing bad ad recommendations back to their source.
- **Recommendation**: No action for current scope. When migrating to a dynamic data source, implement data lineage tracking using AWS Glue DataBrew or equivalent.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (createAdsMap — ad data originates in source code)

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No business outcome metrics. No custom CloudWatch metrics, no business KPI tracking. The service logs ad requests (`received ad request (context_words=...)`) but does not publish metrics for ad impressions, click-through rates, conversion rates, or ad relevance scores.
- **Implication**: When agents consume the AdService, business metrics (ad relevance, click-through rate) become the primary signal for whether agent-selected ads produce good outcomes. Without these metrics, there is no feedback loop.
- **Recommendation**: Publish custom metrics for: (1) ad requests per category, (2) random vs. targeted ad ratio, (3) ads served per request. When click tracking is available, add click-through rate and conversion metrics.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (logs requests but publishes no metrics; `initStats()` has TODO for OpenTelemetry stats)

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: The service exposes a documented gRPC interface via `AdServiceGrpc` with a `GetAds` RPC defined in `demo.proto`. The implementation in `AdService.java` extends `AdServiceGrpc.AdServiceImplBase`. This is a proper programmatic API — not direct database access, file-based exchange, or UI automation. gRPC health check service is also registered.
- **Gap**: N/A — requirement is met. The gRPC interface is a valid documented API surface.
- **Recommendation**: Consider adding gRPC reflection service (`ProtoReflectionService`) to enable runtime API discovery by agents.
- **Evidence**: `src/main/proto/demo.proto`, `src/main/java/hipstershop/AdService.java`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK
- **Finding**: `demo.proto` serves as the machine-readable API specification. Protobuf definitions auto-generate client/server stubs. However, the proto file is a shared monolith containing 10+ service definitions, not scoped to AdService alone.
- **Gap**: No standalone AdService API specification. No versioned spec. Agent tool definitions must parse the full monolith proto.
- **Recommendation**: Extract AdService-specific proto into standalone `adservice.proto`. Consider generating OpenAPI spec from proto for broader compatibility.
- **Evidence**: `src/main/proto/demo.proto`

#### API-Q3: Structured Error Responses
- **Severity**: RISK
- **Finding**: The `getAds` method catches `StatusRuntimeException` and returns gRPC status codes via `responseObserver.onError(e)`. No custom error detail structure beyond gRPC status codes. No structured error body with error codes, messages, or retryable indicators.
- **Gap**: No structured error response format beyond gRPC status codes. Agents cannot distinguish retriable from terminal errors without custom details.
- **Recommendation**: Implement `com.google.rpc.Status` with `ErrorInfo` details including error code enum, message, and `retryable` boolean.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (catch block with StatusRuntimeException)

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The `GetAds` RPC is a read-only operation. No write endpoints exist. Idempotency is inherently satisfied for read operations.
- **Gap**: N/A — no write operations exist.
- **Recommendation**: No action required for current scope. Implement idempotency keys if write operations are added.
- **Evidence**: `src/main/proto/demo.proto` (only GetAds RPC), `src/main/java/hipstershop/AdService.java`

#### API-Q5: API Versioning and Deprecation
- **Severity**: RISK
- **Finding**: No API versioning. Proto package is `hipstershop` with no version prefix. No deprecation policy, no changelog. Build artifact version is `0.1.0-SNAPSHOT` but not reflected in the API contract.
- **Gap**: No API versioning strategy. Breaking changes would silently break agent tool schemas.
- **Recommendation**: Adopt package-level versioning (`hipstershop.ads.v1`). Establish deprecation policy. Maintain CHANGELOG.md.
- **Evidence**: `src/main/proto/demo.proto` (unversioned package), `build.gradle`

#### API-Q6: Structured Response Format
- **Severity**: INFO
- **Finding**: Response format is Protocol Buffers — binary, strongly-typed, machine-readable. `AdResponse` contains `repeated Ad ads` with `redirect_url` and `text` string fields.
- **Gap**: N/A — protobuf is a well-structured format. Binary format may need JSON transcoding for some agent frameworks.
- **Recommendation**: Consider gRPC-JSON transcoding for broader agent framework compatibility.
- **Evidence**: `src/main/proto/demo.proto`, `build.gradle`

#### API-Q7: Asynchronous Operation Support
- **Severity**: RISK
- **Finding**: No async patterns. `GetAds` is synchronous, serving from in-memory data. No background job frameworks, no job status APIs, no webhooks.
- **Gap**: No async support. Current operations are fast enough, but no infrastructure for future async needs.
- **Recommendation**: No immediate action. Implement gRPC server streaming or polling if service evolves to external ad provider integration.
- **Evidence**: `src/main/java/hipstershop/AdService.java`

#### API-Q8: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: No event emission. No webhooks, SNS, EventBridge, Kafka, or CDC. Service is purely request/response with static data.
- **Gap**: N/A for current static data design.
- **Recommendation**: No action for current scope. Add event emission if dynamic ad management is introduced.
- **Evidence**: `src/main/java/hipstershop/AdService.java`, `build.gradle`

#### API-Q9: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit documentation or headers. No API Gateway throttle settings, no WAF rate rules, no rate limiting middleware. gRPC server returns no rate limit metadata.
- **Gap**: No rate limit awareness for agent callers.
- **Recommendation**: Include rate limit metadata in gRPC response headers when rate limiting is implemented (STATE-Q5).
- **Evidence**: `src/main/java/hipstershop/AdService.java`

#### API-Q10: API Latency Profile
- **Severity**: INFO
- **Finding**: No performance benchmarks or load test results. Service uses in-memory `ImmutableListMultimap` — expected sub-millisecond business logic latency. No CloudWatch metrics or APM dashboards.
- **Gap**: No measured latency profile. Sub-millisecond assumption is unvalidated.
- **Recommendation**: Conduct load testing to establish P95 latency baseline. Publish latency metrics.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (in-memory lookup)

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: No authentication mechanism. gRPC server created with `ServerBuilder.forPort(port)` — no auth interceptor, no TLS, no API key validation, no OAuth2/mTLS. Client uses `.usePlaintext()`. Service accepts unauthenticated connections.
- **Gap**: No machine identity authentication. Cannot identify which agent made a request. No principal attribution in logs.
- **Recommendation**: Add gRPC server interceptor validating API keys or OAuth2 client credentials. Implement mTLS for transport security.
- **Evidence**: `src/main/java/hipstershop/AdService.java`, `src/main/java/hipstershop/AdServiceClient.java`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK
- **Finding**: No authorization model. No IAM policies, no role definitions, no permission checks. All callers have identical unlimited access.
- **Gap**: No scoped permissions. Cannot grant read-only access because no permission model exists.
- **Recommendation**: Implement scoped permissions via gRPC metadata-based authorization or API gateway with IAM-based access control.
- **Evidence**: `src/main/java/hipstershop/AdService.java`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK
- **Finding**: No action-level authorization. Only one RPC (`GetAds`) with no permission checks. Handler processes all requests without inspecting caller identity.
- **Gap**: No action-level authorization mechanism. No infrastructure for future action-level controls.
- **Recommendation**: Implement gRPC interceptor for action-level authorization. Distinguish `ads:read` from future `ads:write`.
- **Evidence**: `src/main/java/hipstershop/AdService.java`

#### AUTH-Q4: Identity Propagation
- **Severity**: RISK
- **Finding**: No identity propagation. No JWT parsing, no OAuth2 token exchange, no user context headers. `AdRequest` contains only `context_keys` — no user identity fields.
- **Gap**: Cannot carry originating user context through service calls. Cannot personalize responses per user.
- **Recommendation**: Add JWT/OAuth2 token propagation via gRPC metadata headers. Parse `Authorization` header in server interceptor.
- **Evidence**: `src/main/proto/demo.proto`, `src/main/java/hipstershop/AdService.java`

#### AUTH-Q5: Agent-as-Self vs Agent-on-Behalf-of-User
- **Severity**: RISK
- **Finding**: No distinction between agent-as-self and agent-on-behalf-of-user. No identity system exists. All callers treated identically.
- **Gap**: Cannot distinguish agent acting under own identity from agent acting on behalf of user.
- **Recommendation**: When implementing AUTH-Q1, include support for two auth modes. Log the mode in audit records.
- **Evidence**: `src/main/java/hipstershop/AdService.java`, `src/main/java/hipstershop/AdServiceClient.java`

#### AUTH-Q6: Credential Management
- **Severity**: RISK
- **Finding**: No credentials management infrastructure. Service has no external dependencies requiring credentials. No hardcoded secrets found. Only env var is `PORT`. No `.env` files.
- **Gap**: No secrets management infrastructure for future credential needs (API keys, TLS certs when AUTH-Q1 is implemented).
- **Recommendation**: Implement AWS Secrets Manager or Vault for credential storage as part of AUTH-Q1 remediation.
- **Evidence**: `src/main/java/hipstershop/AdService.java`, `Dockerfile`

#### AUTH-Q7: Immutable Audit Logging ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: Log4j2 with JSON structured logging configured. Placeholder trace/span ID fields exist but are not populated (tracing not implemented). Logs `context_keys` but not caller identity. No CloudTrail. No immutable log storage.
- **Gap**: No audit logging of authenticated principals. Logs are not immutable. No tamper-evident storage.
- **Recommendation**: After AUTH-Q1, add authenticated principal to every log entry. Configure CloudWatch Logs or S3 with object lock.
- **Evidence**: `src/main/resources/log4j2.xml`, `src/main/java/hipstershop/AdService.java`

#### AUTH-Q8: Agent Identity Suspension
- **Severity**: RISK
- **Finding**: No agent identity suspension capability. No API key revocation, no IAM role management, no per-caller disable mechanism. No authentication exists to suspend.
- **Gap**: Cannot suspend a misbehaving agent without taking down the entire service.
- **Recommendation**: When implementing AUTH-Q1, ensure per-agent suspension support. Test suspension takes effect within seconds.
- **Evidence**: `src/main/java/hipstershop/AdService.java`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: Service is stateless — serves from in-memory `ImmutableListMultimap`. No write operations, no multi-step workflows, no database transactions.
- **Gap**: No compensation or rollback mechanism. Acceptable for current read-only design.
- **Recommendation**: No action for current scope. Implement saga patterns if write operations are added.
- **Evidence**: `src/main/java/hipstershop/AdService.java`, `src/main/proto/demo.proto`

#### STATE-Q2: Queryable Current State
- **Severity**: RISK
- **Finding**: `GetAds` returns ads by category. Data is static and hardcoded. Only category-based and random access — no endpoint to list all ads, query metadata, or inspect full inventory.
- **Gap**: Limited queryability. No introspection endpoints for full state discovery.
- **Recommendation**: Add `ListCategories` RPC to expose available categories and ad counts.
- **Evidence**: `src/main/java/hipstershop/AdService.java`, `src/main/proto/demo.proto`

#### STATE-Q3: Concurrency Controls
- **Severity**: RISK
- **Finding**: Data is immutable (`ImmutableListMultimap` from Guava). No writes, no race conditions possible. Thread-safe by design.
- **Gap**: No explicit concurrency controls. Acceptable for current immutable-data design.
- **Recommendation**: No action for current scope. Implement optimistic locking if write operations are added.
- **Evidence**: `src/main/java/hipstershop/AdService.java`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK
- **Finding**: No circuit breakers. Service has zero external dependency calls — serves from in-memory data. No Resilience4j, no retry logic.
- **Gap**: No resilience patterns. Acceptable for current self-contained design.
- **Recommendation**: No action for current scope. Add Resilience4j if external dependencies are added.
- **Evidence**: `src/main/java/hipstershop/AdService.java`, `build.gradle`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK
- **Finding**: No rate limiting at any layer. gRPC server accepts unlimited connections. No API Gateway, WAF, or application-level rate limiting.
- **Gap**: Runaway agent loop could overwhelm service at machine speed.
- **Recommendation**: Add rate limiting via gRPC server interceptor, API gateway, or service mesh.
- **Evidence**: `src/main/java/hipstershop/AdService.java`, `Dockerfile`

#### STATE-Q6: Blast Radius and Transaction Limits
- **Severity**: RISK
- **Finding**: No configurable transaction limits. `MAX_ADS_TO_SERVE = 2` limits response size but not request volume. No per-agent-identity limits.
- **Gap**: No mechanism to limit request volume per agent identity.
- **Recommendation**: Implement per-agent-identity request quotas at API gateway layer.
- **Evidence**: `src/main/java/hipstershop/AdService.java`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: RISK
- **Finding**: No load tests, no auto-scaling config. Dockerfile has no JVM heap or resource limits. No capacity planning documentation.
- **Gap**: Service not tested for agent-level traffic patterns. No auto-scaling.
- **Recommendation**: Add JVM heap config. Define Kubernetes resource limits. Conduct load testing. Configure HPA.
- **Evidence**: `Dockerfile`, `build.gradle`

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State
- **Severity**: RISK
- **Finding**: No draft/pending state concept. Service returns ads directly from in-memory map. No workflow states, no approval mechanisms. Purely read-only query service.
- **Gap**: No draft state for ads. No mechanism for human review before ad publication if write capability is added.
- **Recommendation**: No action for current scope. Implement status field (DRAFT → ACTIVE → ARCHIVED) if ad management is added.
- **Evidence**: `src/main/java/hipstershop/AdService.java`

#### HITL-Q2: Configurable Approval Gates
- **Severity**: RISK
- **Finding**: No configurable approval gates. No approval endpoints, no workflow engines. Service has no state-modifying operations.
- **Gap**: No approval gate infrastructure for future write operations.
- **Recommendation**: No action for current scope. Implement approval gates if write capability is added.
- **Evidence**: `src/main/java/hipstershop/AdService.java`, `src/main/proto/demo.proto`

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK
- **Finding**: Dockerfile enables local container builds. README documents local build. No Docker Compose, no staging environment configs, no seed data scripts (data hardcoded).
- **Gap**: No sandbox or staging environment configuration for agent testing.
- **Recommendation**: Create Docker Compose for local integration testing. Define staging environment configuration.
- **Evidence**: `Dockerfile`, `README.md`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: Service handles ad data (redirect URLs, promotional text). No PII, PHI, or financial records in hardcoded dataset. No data classification tags, no field-level access controls, no data sensitivity documentation.
- **Gap**: No data classification framework. Absence of classification means agents cannot programmatically verify authorization to access data fields.
- **Recommendation**: Document data classification for all fields. Add classification metadata to proto file.
- **Evidence**: `src/main/java/hipstershop/AdService.java`, `src/main/proto/demo.proto`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: Ad data is non-sensitive and hardcoded. No data residency requirements apparent. No GDPR/LGPD references. No cross-region replication.
- **Gap**: No data residency documentation. `context_keys` from EU users may have GDPR implications.
- **Recommendation**: Document that static ad content is not subject to residency requirements. Assess `context_keys` under GDPR.
- **Evidence**: `src/main/java/hipstershop/AdService.java`, `src/main/proto/demo.proto`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK
- **Finding**: `GetAds` accepts `context_keys` for category filtering. `MAX_ADS_TO_SERVE = 2` for random ads. No pagination, no sorting, no cursor-based iteration.
- **Gap**: Limited selective query support. No pagination or configurable result size.
- **Recommendation**: Add `max_results` and `page_token` fields to `AdRequest`. Enforce result size limits.
- **Evidence**: `src/main/proto/demo.proto`, `src/main/java/hipstershop/AdService.java`

#### DATA-Q4: System of Record Designations
- **Severity**: RISK
- **Finding**: Ad data hardcoded in `createAdsMap()`. Source code is the system of record. No external data store, no master data management.
- **Gap**: No formal system-of-record designation. Source code as data store creates tight deployment coupling.
- **Recommendation**: Document source code as current system of record. Plan migration to external data store.
- **Evidence**: `src/main/java/hipstershop/AdService.java`

#### DATA-Q5: Reliable Timestamps
- **Severity**: RISK
- **Finding**: No timestamps on data. `Ad` proto has only `redirect_url` and `text`. No `created_at`, `updated_at`, or `event_time` fields.
- **Gap**: No temporal metadata. Agents cannot perform time-sensitive reasoning.
- **Recommendation**: Add timestamp fields to `Ad` proto message. Enforce UTC timestamps.
- **Evidence**: `src/main/proto/demo.proto`

#### DATA-Q6: Data Freshness Signaling
- **Severity**: RISK
- **Finding**: No data freshness signaling. No cache headers, no `last_refreshed` field. Data is static but API does not communicate this.
- **Gap**: Agents cannot determine whether data is current, cached, or stale.
- **Recommendation**: Add `data_freshness` field to `AdResponse` or use gRPC response metadata headers.
- **Evidence**: `src/main/proto/demo.proto`, `src/main/java/hipstershop/AdService.java`

#### DATA-Q7: PII Redaction in Logs
- **Severity**: RISK
- **Finding**: Service logs `context_keys` which could contain user-derived data. No PII masking or scrubbing middleware. JSON structured logging configured but no PII filtering.
- **Gap**: No PII redaction in logs. `context_keys` logged without sanitization.
- **Recommendation**: Add log sanitization interceptor. Configure CloudWatch Logs data protection.
- **Evidence**: `src/main/java/hipstershop/AdService.java`, `src/main/resources/log4j2.xml`

#### DATA-Q8: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics. Hardcoded data is 100% complete by definition — 7 ads across 6 categories, no nulls, no duplicates.
- **Gap**: N/A for current static dataset. Quality monitoring needed when migrating to dynamic source.
- **Recommendation**: Implement data quality monitoring when migrating to dynamic data source.
- **Evidence**: `src/main/java/hipstershop/AdService.java`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Documentation and Versioning
- **Severity**: RISK
- **Finding**: `demo.proto` serves as schema documentation with field names, types, and field numbers. Proto3 provides built-in backward compatibility. No API-level versioning strategy (no `v1`/`v2`). No schema registry.
- **Gap**: No schema versioning beyond proto3 field numbering. No formal schema evolution policy.
- **Recommendation**: Adopt package-level versioning. Publish to schema registry (Buf Schema Registry).
- **Evidence**: `src/main/proto/demo.proto`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Field names are semantically meaningful. Proto: `context_keys`, `redirect_url`, `text`. Java: `adsMap`, `getAdsByCategory`, `getRandomAds`. No legacy abbreviations.
- **Gap**: N/A — naming is clear and consistent.
- **Recommendation**: Maintain current conventions. Document domain-specific terms if introduced.
- **Evidence**: `src/main/proto/demo.proto`, `src/main/java/hipstershop/AdService.java`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No data catalog. No Glue Data Catalog, Collibra, or metadata files. Proto file is the only schema documentation.
- **Gap**: No automated discovery mechanism for agent tool builders.
- **Recommendation**: Register proto in schema registry. Add service metadata for automated discovery.
- **Evidence**: `src/main/proto/demo.proto`

#### DISC-Q4: Data Lineage
- **Severity**: INFO
- **Finding**: No data lineage. Ad data hardcoded in source code. No ETL pipelines, no transformation logs. Source code is the origin.
- **Gap**: Lineage is trivial for current design. Needed when migrating to dynamic data source.
- **Recommendation**: Implement data lineage when migrating to dynamic data source.
- **Evidence**: `src/main/java/hipstershop/AdService.java`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK
- **Finding**: Partial observability. `log4j2.xml` configures JSON structured logging with trace/span ID placeholders. However, `initTracing()` has `TODO(arbrown) Implement OpenTelemetry tracing` — tracing is NOT implemented. `initStats()` also has TODO. Trace/span ID fields are empty context variables.
- **Gap**: Distributed tracing not functional. Structured logging configured but correlation IDs not populated.
- **Recommendation**: Implement OpenTelemetry tracing. Add OTel Java SDK and gRPC instrumentation to `build.gradle`. Export to X-Ray.
- **Evidence**: `src/main/resources/log4j2.xml`, `src/main/java/hipstershop/AdService.java`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK
- **Finding**: No alerting thresholds. No CloudWatch alarms, no anomaly detection, no PagerDuty/OpsGenie. No monitoring config files.
- **Gap**: No alerting infrastructure. Service degradation would not be detected before agents fail.
- **Recommendation**: Define CloudWatch alarms for gRPC error rates and P95 latency. Integrate with on-call notification.
- **Evidence**: No monitoring configuration files found. Absence is itself a finding.

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No business outcome metrics. No custom CloudWatch metrics. Service logs requests but publishes no metrics for ad impressions, click-through, or relevance.
- **Gap**: No feedback loop for agent-selected ad quality.
- **Recommendation**: Publish custom metrics: ad requests per category, random vs. targeted ratio, ads served per request.
- **Evidence**: `src/main/java/hipstershop/AdService.java`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK
- **Finding**: No IaC for deployment surface. No Terraform, CloudFormation, or CDK. Dockerfile defines container build only. No peer review for infra changes. No drift detection.
- **Gap**: Agent-facing integration surface not defined as code, not reviewed, not monitored for drift. All three sub-checks fail.
- **Recommendation**: Define deployment infrastructure as IaC. Require PR review. Enable AWS Config drift detection.
- **Evidence**: `Dockerfile`, No IaC files found.

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK
- **Finding**: No CI/CD pipeline. No GitHub Actions, Jenkinsfile, or buildspec.yml. No contract testing, no proto validation in build pipeline.
- **Gap**: No CI/CD. Proto changes cannot be automatically validated before production.
- **Recommendation**: Implement CI/CD with proto compilation validation, `buf breaking` checks, and container builds.
- **Evidence**: No CI/CD configuration files found. Absence is itself a finding.

#### ENG-Q3: Rollback Capability
- **Severity**: RISK
- **Finding**: No rollback capability defined. No blue/green, no CodeDeploy, no Helm rollback, no feature flags, no canary deployment.
- **Gap**: No rollback mechanism. Broken deployment leaves agents unable to function.
- **Recommendation**: Implement automated rollback with health checks. Target: rollback within 15 minutes.
- **Evidence**: `Dockerfile`, No deployment configuration files found.

#### ENG-Q4: API Test Coverage
- **Severity**: RISK
- **Finding**: No automated tests. No `src/test/` directory, no test files, no test dependencies in `build.gradle`. No JUnit, Mockito, or gRPC testing framework.
- **Gap**: Zero test coverage. API behavior changes undetectable.
- **Recommendation**: Add gRPC unit tests with `io.grpc:grpc-testing` and JUnit 5. Integrate into CI.
- **Evidence**: `build.gradle` (no test dependencies), No test directory found.

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: RISK
- **Finding**: No encryption at rest. No KMS key references. Service uses in-memory data with no persistent storage.
- **Gap**: No encryption framework. In-memory only currently, but no infrastructure for future data stores.
- **Recommendation**: Enable encryption at rest with customer-managed KMS when adding persistent storage.
- **Evidence**: `src/main/java/hipstershop/AdService.java`, `build.gradle`

#### ENG-Q6: Cross-Origin and Network Policies
- **Severity**: BLOCKER
- **Finding**: No network security configurations. Dockerfile exposes port 9555 with no security groups, firewall rules, or network policies. gRPC server has no TLS (`ServerBuilder.forPort(port)`). Client uses `.usePlaintext()`. No API gateway, no WAF rules.
- **Gap**: No network security boundary. Any network-reachable client can connect without encryption.
- **Recommendation**: Enable TLS. Define network policies restricting access. Deploy behind API gateway or service mesh with mTLS.
- **Evidence**: `Dockerfile`, `src/main/java/hipstershop/AdService.java`, `src/main/java/hipstershop/AdServiceClient.java`

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `src/main/java/hipstershop/AdService.java` | API-Q1, API-Q2, API-Q3, API-Q4, API-Q5, API-Q6, API-Q7, API-Q8, API-Q9, API-Q10, AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q6, AUTH-Q7, AUTH-Q8, STATE-Q1, STATE-Q2, STATE-Q3, STATE-Q4, STATE-Q5, STATE-Q6, STATE-Q7, HITL-Q1, HITL-Q2, DATA-Q1, DATA-Q2, DATA-Q3, DATA-Q4, DATA-Q5, DATA-Q6, DATA-Q7, DATA-Q8, DISC-Q2, DISC-Q4, OBS-Q1, OBS-Q3, ENG-Q5 |
| `src/main/java/hipstershop/AdServiceClient.java` | API-Q1, AUTH-Q1, AUTH-Q5, AUTH-Q6, ENG-Q6 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `src/main/proto/demo.proto` | API-Q1, API-Q2, API-Q4, API-Q5, API-Q6, AUTH-Q4, STATE-Q1, STATE-Q2, HITL-Q2, DATA-Q1, DATA-Q2, DATA-Q3, DATA-Q5, DATA-Q6, DISC-Q1, DISC-Q2 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `Dockerfile` | AUTH-Q6, STATE-Q5, STATE-Q7, HITL-Q3, ENG-Q1, ENG-Q3, ENG-Q6 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `build.gradle` | API-Q5, API-Q6, API-Q8, STATE-Q4, STATE-Q7, ENG-Q2, ENG-Q4, ENG-Q5 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `src/main/resources/log4j2.xml` | AUTH-Q7, DATA-Q7, OBS-Q1 |
| `README.md` | HITL-Q3 |
| `settings.gradle` | — (repository metadata only) |
| `gradle/wrapper/gradle-wrapper.properties` | — (build tooling only) |
| `genproto.sh` | — (build script only) |

### Notable Absences (files NOT found — absence cited as evidence)
| Absence | Questions Referenced |
|---------|---------------------|
| No IaC files (Terraform, CloudFormation, CDK) | AUTH-Q1, AUTH-Q2, AUTH-Q7, AUTH-Q8, ENG-Q1, ENG-Q5, ENG-Q6 |
| No CI/CD configuration files | ENG-Q2, ENG-Q3 |
| No test directories or test files | ENG-Q4 |
| No monitoring/alerting configuration | OBS-Q2 |
| No data catalog or metadata files | DISC-Q3 |
| No secrets management configuration | AUTH-Q6 |
