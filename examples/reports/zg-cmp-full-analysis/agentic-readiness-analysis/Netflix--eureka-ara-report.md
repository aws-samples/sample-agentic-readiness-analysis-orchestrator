# Agentic Readiness Analysis Report

**Target**: Netflix/eureka (monorepo)
**Date**: 2026-04-29
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**Repository Type**: monorepo
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: java, service-discovery, microservices
**Context**: Netflix service-discovery server and client.

**Archetype Justification**: Eureka server maintains an in-memory service registry (ConcurrentHashMap) with full CRUD operations (register, renew, cancel, status update) exposed via REST API, with peer-to-peer replication for high availability.

**Monorepo Service Boundaries**: The primary deployable service is `eureka-server` (the discovery server). `eureka-client` is a library component embedded by other applications. Analysis focuses on eureka-server as the system agents would interact with.

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 2 | **RISK-SAFETY**: 9 | **RISK-QUALITY**: 16 | **INFOs**: 15

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days. The 2 BLOCKERs (AUTH-Q1: no machine identity authentication; DATA-Q1: no sensitive data classification) must be resolved before agents can safely interact with the Eureka server. Once both BLOCKERs are resolved, the 9 RISK-SAFETY findings would place this at "Pilot-Ready (Safety Concerns)" — requiring supervised pilot with elevated safety oversight and prioritized safety remediation before expanding agent scope.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 2 |
| RISK-SAFETY | 9 |
| RISK-QUALITY | 16 |
| INFO | 15 |
| N/A | 0 |
| Not Evaluated (extended) | 1 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 18
**Extended Questions Not Triggered**: 1
**Questions N/A (repo_type: monorepo)**: 0
**Service Archetype**: stateful-crud (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: Eureka server has a `ServerRequestAuthFilter` that reads `DiscoveryIdentity-Name` and `DiscoveryIdentity-Version` HTTP headers and logs them via Servo `DynamicCounter`. This is **client identification, not authentication** — there is no credential verification, no OAuth2 client credentials flow, no API key validation, no mTLS. Any HTTP client can set these headers to any value. The `RateLimitingFilter` uses the same header to classify "privileged" vs "non-privileged" clients, but this classification is trivially spoofable.
- **Gap**: No machine identity authentication mechanism exists. The system cannot verify that a caller is who they claim to be. An agent calling the Eureka API would have no authenticated identity — the server cannot distinguish between authorized agents, unauthorized agents, or malicious callers.
- **Remediation**:
  - **Immediate**: Deploy Eureka behind an API Gateway (e.g., AWS API Gateway, Kong, or Envoy) with OAuth2 client credentials or API key authentication. Configure the gateway to authenticate all requests before forwarding to Eureka.
  - **Target State**: Every API request to Eureka is authenticated with a verifiable machine identity (client credentials OAuth 2.0 or mTLS). Agent identities are attributable in audit logs.
  - **Estimated Effort**: Medium (30–60 days) — requires API Gateway deployment and auth configuration, not application code changes.
  - **Dependencies**: AUTH-Q6 (audit logging) depends on authenticated identities being available.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/ServerRequestAuthFilter.java` (header-based identification only), `eureka-client/src/main/java/com/netflix/appinfo/AbstractEurekaIdentity.java` (identity header constants), `eureka-server/src/main/webapp/WEB-INF/web.xml` (filter configuration)

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: Eureka stores service instance metadata: hostnames, IP addresses, ports, VIP addresses, health check URLs, AWS metadata (AMI ID, instance ID, availability zone). No data classification tags exist. No PII/PHI/financial data is present. However, IP addresses and AWS instance IDs may be considered infrastructure-sensitive, and AWS credentials exist in configuration (though not served via API). No field-level classification or tagging of data sensitivity exists anywhere in the codebase.
- **Gap**: No field-level classification or tagging of data sensitivity. Infrastructure metadata is unclassified. Per DATA-Q1, sensitive data must be classified and tagged at the field level before agents get read access.
- **Remediation**:
  - **Immediate**: Create a data classification document that categorizes each field in `InstanceInfo` and `AmazonInfo` by sensitivity level (public, internal, infrastructure-sensitive). Tag IP addresses, instance IDs, and AWS metadata as infrastructure-sensitive.
  - **Target State**: All data fields exposed via the Eureka REST API are classified with sensitivity tags. Agent access controls can reference these classifications to restrict field-level access where needed.
  - **Estimated Effort**: Low (7–14 days) — Eureka stores infrastructure metadata, not PII/PHI. Classification is a documentation exercise, not a code rewrite.
  - **Dependencies**: None — this can be remediated independently of AUTH-Q1.
- **Evidence**: `eureka-client/src/main/java/com/netflix/appinfo/InstanceInfo.java` (unclassified fields: hostName, ipAddr, port, vipAddress, secureVipAddress, healthCheckUrl), `eureka-client/src/main/java/com/netflix/appinfo/AmazonInfo.java` (unclassified AWS metadata: amiId, instanceId, availabilityZone)

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No authorization model exists in the Eureka server. All endpoints are accessible to all callers without any permission checks. There are no IAM policies, no RBAC definitions, no API Gateway resource policies. The `RateLimitingFilter` distinguishes "privileged" and "non-privileged" clients by header values, but this is for rate-limiting purposes only — it does not restrict access to endpoints or operations.
- **Gap**: An agent identity cannot be granted read-only access to specific resources. Every caller has the same unrestricted access to all endpoints (register, cancel, status update, query).
- **Compensating Controls**:
  - Deploy an API Gateway with IAM-based or OAuth scope-based authorization that restricts agent identities to GET endpoints only.
  - Use network-level segmentation (security groups, VPC) to limit which agents can reach the Eureka server.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement API Gateway method-level authorization: agent identities should only have access to GET /apps, GET /apps/{appId}, GET /apps/{appId}/{instanceId}, and GET /apps/delta. Block POST, PUT, DELETE for agent identities.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationsResource.java` (no auth checks), `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationResource.java` (POST addInstance has no auth), `eureka-core/src/main/java/com/netflix/eureka/resources/InstanceResource.java` (PUT/DELETE with no auth)

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization exists. The `isReplication` header (`x-netflix-discovery-replication`) distinguishes peer replication traffic from client traffic, but it is **not enforced** — any caller can set this header to `"true"` to bypass normal registration logic. There are no ABAC policies, no fine-grained RBAC, no permission matrices, no middleware that checks `canRead` vs `canWrite` vs `canDelete`.
- **Gap**: The system cannot enforce that an agent can read records but not delete them within the same resource type. An agent with any access can call DELETE /{version}/apps/{appId}/{instanceId} to deregister services.
- **Compensating Controls**:
  - API Gateway method-level restrictions: allow GET only for agent identities.
  - Network segmentation: restrict write endpoints to internal service mesh traffic only.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement method-level authorization at the API Gateway layer. For a read-only agent scope, block all non-GET HTTP methods for agent identities.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/resources/InstanceResource.java` (no auth check on cancelLease DELETE), `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationResource.java` (no auth check on addInstance POST)

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: `ServerRequestAuthFilter` logs client identity headers via Servo `DynamicCounter` (incrementing a counter named `DiscoveryServerRequestAuth_Name_{clientName}-{clientVersion}`). This is a **metric counter, not an audit log**. There are no immutable audit logs, no CloudTrail integration, no tamper-evident logging, no log-level recording of which principal performed which operation.
- **Gap**: No audit trail exists for agent-initiated actions. Cannot prove compliance or conduct forensics for API calls. Log output via log4j `ConsoleAppender` is ephemeral and mutable.
- **Compensating Controls**:
  - Deploy API Gateway with access logging enabled and send logs to an immutable store (S3 with Object Lock, CloudWatch Logs with retention policies).
  - Enable CloudTrail for API Gateway API calls.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement structured access logging at the API Gateway layer with principal attribution. Send logs to an immutable store (e.g., S3 bucket with Object Lock or CloudWatch Logs with retention policy).
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/ServerRequestAuthFilter.java` (DynamicCounter only), `eureka-server/src/main/resources/log4j.properties` (ConsoleAppender, no structured logging)

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No mechanism exists to suspend or revoke individual client identities. The `RateLimitingFilter` can throttle non-privileged clients globally but cannot target individual client identities for suspension. There are no API key revocation endpoints, no IAM role deactivation procedures, no Cognito-style user disable.
- **Gap**: If an agent identity exhibits anomalous behavior, it cannot be individually revoked without taking down the broader platform or blocking all non-privileged clients.
- **Compensating Controls**:
  - If deployed behind API Gateway with API keys, individual API keys can be disabled immediately.
  - Network-level blocking of specific agent IP addresses as an emergency measure.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Deploy behind API Gateway with API key management. Each agent identity gets a unique API key that can be individually revoked.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/RateLimitingFilter.java` (global rate limiting only), `eureka-core/src/main/java/com/netflix/eureka/DefaultEurekaServerConfig.java` (rateLimiterPrivilegedClients is a set, not individual controls)

#### STATE-Q1: Compensation and Rollback ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No saga pattern, no two-phase commit, no explicit undo endpoints exist. Peer replication is fire-and-forget via `PeerEurekaNode` with batched task dispatching. If a registration or cancellation is replicated to peers and then needs to be undone, there is no compensation mechanism. Self-preservation mode prevents mass eviction when heartbeat rates drop below threshold, but this is a safety net for network partitions, not a rollback mechanism.
- **Gap**: Multi-step operations (e.g., register + replicate to N peers) that fail mid-sequence leave the system in a partially updated state. No compensation logic to reverse partial replication.
- **Compensating Controls**:
  - For read-only agent scope, this risk is lower since agents would not initiate write workflows.
  - Eureka's eventual consistency model and self-healing (re-registration on heartbeat failure) provide partial mitigation.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: For write-enabled use cases, implement compensation endpoints (explicit deregister-and-propagate). For read-only scope, accept the existing eventual consistency model as adequate.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/cluster/PeerEurekaNode.java` (fire-and-forget replication), `eureka-core/src/main/java/com/netflix/eureka/registry/AbstractInstanceRegistry.java` (no rollback logic in register/cancel)

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No explicit circuit breaker pattern exists in the server-side code. The client-side `RetryableEurekaHttpClient` provides retry logic with a quarantine list (quarantining unresponsive servers), but this is in the **client library**, not the server. The server's `PeerEurekaNode` has configurable timeouts (`peerNodeConnectTimeoutMs=1000`, `peerNodeReadTimeoutMs=5000`) and batched task dispatching via `TrafficShaper`, but no circuit breaker that opens after consecutive failures. No Resilience4j, Hystrix, or `@CircuitBreaker` annotations found.
- **Gap**: When an agent calls the Eureka server, the server may call peer nodes for replication. If peers are unresponsive, the server has no circuit breaker to prevent cascading failures. The `TrafficShaper` provides congestion delays but does not break the circuit.
- **Compensating Controls**:
  - Deploy a service mesh (e.g., Istio, App Mesh) with circuit breaker policies at the infrastructure layer.
  - Configure API Gateway timeout limits to prevent agents from being affected by slow peer replication.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement circuit breaker at the infrastructure layer (service mesh or API Gateway). For the server-side peer replication, consider adding Resilience4j circuit breaker on peer node HTTP calls.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/cluster/PeerEurekaNode.java` (timeouts but no circuit breaker), `eureka-client/src/main/java/com/netflix/discovery/shared/transport/decorator/RetryableEurekaHttpClient.java` (client-side retry only), `eureka-core/src/main/java/com/netflix/eureka/util/batcher/TrafficShaper.java` (congestion shaping only)

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: A `RateLimitingFilter` exists with a token-bucket algorithm implementation (`RateLimiter` class). It supports configurable burst size, fetch average rate, and full fetch average rate. **However, it is DISABLED by default**: `rateLimiterEnabled` defaults to `false`, and the filter-mapping in `web.xml` is **commented out**. When disabled, the filter still counts rate-limited candidates for monitoring purposes but does not enforce throttling. When enabled, it returns HTTP 503 without rate limit headers.
- **Gap**: Rate limiting is not active. A runaway agent loop could overwhelm the Eureka server with registry fetch requests at machine speed. The commented-out filter mapping in web.xml means even enabling the `rateLimiterEnabled` property would have no effect without deploying a modified web.xml.
- **Compensating Controls**:
  - Enable the rate limiting filter by uncommenting the filter-mapping in web.xml and setting `eureka.rateLimiter.enabled=true`.
  - Deploy API Gateway throttling (AWS API Gateway usage plans) as an external rate limiter.
- **Remediation Timeline**: 7–14 days (if enabling built-in rate limiter), 30 days (if deploying API Gateway throttling)
- **Recommendation**: As an immediate step, uncomment the rate limiting filter-mapping in web.xml and enable it via configuration. For production, deploy API Gateway throttling with per-client usage plans.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/RateLimitingFilter.java` (complete implementation), `eureka-core/src/main/java/com/netflix/eureka/DefaultEurekaServerConfig.java` (`rateLimiterEnabled` defaults to `false`), `eureka-server/src/main/webapp/WEB-INF/web.xml` (filter-mapping is commented out)

#### DATA-Q2: Data Residency and Sovereignty ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No data residency requirements are documented in the repository. Eureka supports multi-region deployment via `remoteRegionUrlsWithName` configuration, which enables cross-region registry synchronization. No GDPR, LGPD, or HIPAA references found. The data stored is service instance metadata (hostnames, IPs, ports, health check URLs, AWS metadata) — infrastructure metadata rather than regulated personal data.
- **Gap**: No data residency controls or documentation exist. If an agent transmits infrastructure metadata (IP addresses, hostnames, AWS instance IDs) to an LLM provider, there are no controls preventing cross-region data movement. While this data is not typically regulated, infrastructure metadata may be considered sensitive in certain compliance contexts.
- **Compensating Controls**:
  - Implement data classification at the API Gateway layer to prevent infrastructure metadata from being forwarded to external LLM providers.
  - Document data residency posture as part of operational runbooks.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Classify the data Eureka holds (infrastructure metadata) and document whether it falls under any data residency requirements. For most deployments, service metadata is not regulated, but this should be explicitly confirmed.
- **Evidence**: `eureka-server/src/main/resources/eureka-client.properties` (region configuration), `eureka-core/src/main/java/com/netflix/eureka/DefaultEurekaServerConfig.java` (remoteRegionUrls configuration)

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Logging uses SLF4J with log4j `ConsoleAppender`. Instance information (hostnames, IP addresses, application names, instance IDs) is logged in plain text throughout the codebase. No PII masking libraries, no log scrubbing middleware, no Amazon Macie integration found. However, Eureka data is **infrastructure metadata** (hostnames, IPs, ports, VIP addresses) — not customer PII (names, emails, SSNs).
- **Gap**: No log redaction mechanism exists. While Eureka does not process customer PII, infrastructure metadata (IP addresses, AWS instance IDs, availability zones) logged in plain text could be considered sensitive in some compliance contexts. If agents process responses containing this metadata and log it, there is no redaction layer.
- **Compensating Controls**:
  - Implement log filtering at the infrastructure level (CloudWatch Logs data protection policies) to redact IP addresses if required.
  - Ensure agent-side logging does not persist infrastructure metadata without controls.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Assess whether infrastructure metadata constitutes sensitive data in your compliance context. If yes, implement log redaction at the infrastructure layer. Since Eureka does not process customer PII, this may be acceptable risk for many deployments.
- **Evidence**: `eureka-server/src/main/resources/log4j.properties` (ConsoleAppender, no masking), `eureka-core/src/main/java/com/netflix/eureka/registry/AbstractInstanceRegistry.java` (logs appName, instanceId in plain text)

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, GraphQL schema, or equivalent machine-readable specification file exists in the repository. The API surface is documented only through JAX-RS annotations in Java source code (`@GET`, `@POST`, `@PUT`, `@DELETE`, `@Path`, `@Produces`) and Javadoc comments.
- **Gap**: Agent frameworks cannot auto-generate tool definitions from the codebase. Every agent integration requires manual tool authoring by reading source code, which will drift from actual behavior over time.
- **Compensating Controls**:
  - Generate an OpenAPI spec from the JAX-RS annotations using swagger-jaxrs or similar tools.
  - Manually author an OpenAPI spec and maintain it alongside the code.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Generate an OpenAPI 3.0 specification from the existing JAX-RS annotations. Tools like `swagger-jaxrs` or `enunciate` can auto-generate from Jersey 1.x annotations.
- **Evidence**: No `openapi.yaml`, `swagger.yaml`, `swagger.json`, or similar files found in the repository. API is defined in `eureka-core/src/main/java/com/netflix/eureka/resources/` via JAX-RS annotations.

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Error responses are inconsistent and unstructured. `ApplicationResource.addInstance()` returns HTTP 400 with plain text messages (e.g., `"Missing instanceId"`, `"Missing hostname"`). `InstanceResource` methods return HTTP 500 (`Response.serverError().build()`) with **no body** on exceptions, and HTTP 404 with no body when instances are not found. There are no structured error codes, no error categories (retriable vs terminal), no consistent error response format.
- **Gap**: Agents cannot distinguish retriable errors (timeout, rate limit) from terminal errors (invalid input, not found). A 500 with no body forces agents to guess. A 503 from the rate limiter has no `Retry-After` header.
- **Compensating Controls**:
  - Implement error mapping at the API Gateway layer to add structured error bodies.
  - Document known error codes and expected behaviors for agent tool definitions.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement a consistent error response format with structured JSON bodies containing `errorCode`, `message`, and `retryable` boolean. Add a Jersey `ExceptionMapper` to standardize error responses.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationResource.java` (plain text 400 errors), `eureka-core/src/main/java/com/netflix/eureka/resources/InstanceResource.java` (empty 500 responses)

#### API-Q6: Asynchronous Operation Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: All client-facing API operations are synchronous. Registry fetch (`GET /apps`), registration (`POST /apps/{appId}`), heartbeat (`PUT /apps/{appId}/{instanceId}`), and cancellation (`DELETE /apps/{appId}/{instanceId}`) are synchronous request-response. Background operations exist (peer sync via `PeerEurekaNode` batched dispatchers, eviction timer, delta retention timer) but these are internal processes — no async API patterns (job submission, polling endpoints, webhook callbacks) are exposed to clients.
- **Gap**: If peer synchronization or response cache generation takes longer than expected, synchronous API calls could be slow. No mechanism for agents to submit operations and poll for completion.
- **Compensating Controls**:
  - For read-only agent scope, registry fetch operations are served from cache (ResponseCacheImpl) with configurable TTL, minimizing latency.
  - Set appropriate timeout values on the agent-side HTTP client.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: For most Eureka use cases, synchronous APIs are adequate since response caching keeps latency low. If long-running operations are identified, consider adding async patterns for those specific operations.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationsResource.java` (synchronous GET), `eureka-core/src/main/java/com/netflix/eureka/registry/ResponseCacheImpl.java` (response caching)

#### DATA-Q3: Selective Query Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: `GET /{version}/apps` returns the **full registry** with no pagination, filtering, or sorting parameters. `GET /{version}/apps/delta` returns recent changes. Region filtering is available via `?regions=` query parameter. Individual applications can be queried via `GET /{version}/apps/{appId}` and individual instances via `GET /{version}/apps/{appId}/{instanceId}`. VIP-based lookups are available. However, there is no `limit`, `offset`, `cursor`, or result size parameter on the full registry endpoint.
- **Gap**: An agent retrieving the full registry (`GET /apps`) receives all registered instances, which could be thousands in a production environment. This can exhaust LLM context windows and increase token costs.
- **Compensating Controls**:
  - Use specific queries (`GET /apps/{appId}`) instead of full registry fetches.
  - Use delta endpoints (`GET /apps/delta`) to get only recent changes.
  - Implement response filtering at the API Gateway layer.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: For agent integration, use targeted queries (`GET /apps/{appId}` or `GET /apps/{appId}/{instanceId}`) instead of full registry fetches. Implement pagination wrapper at the API Gateway layer if full registry queries are needed.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationsResource.java` (no pagination params on getContainers)

#### DATA-Q4: System of Record Designations — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Eureka uses a peer-to-peer replication model where every server instance maintains a full copy of the registry. There is no single golden record. Conflict resolution relies on `lastDirtyTimestamp` comparison — the instance with the newer timestamp wins. `PeerAwareInstanceRegistryImpl` handles peer replication with eventual consistency.
- **Gap**: Agents querying different Eureka instances may receive different views of the registry during replication lag. No master data management process resolves conflicts beyond timestamp-based last-writer-wins.
- **Compensating Controls**:
  - For read-only queries, the response cache provides a consistent snapshot within each server's cache TTL.
  - Route all agent traffic to a single Eureka instance or use a load balancer with sticky sessions.
- **Remediation Timeline**: N/A — inherent to Eureka's architecture
- **Recommendation**: Document the eventual consistency model for agent consumers. Agents should be designed to tolerate brief inconsistencies in registry data across Eureka peers.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/registry/PeerAwareInstanceRegistryImpl.java` (peer replication), `eureka-core/src/main/java/com/netflix/eureka/resources/InstanceResource.java` (lastDirtyTimestamp conflict resolution)

#### DATA-Q5: Temporal Metadata and Freshness — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: `LeaseInfo` includes `registrationTimestamp`, `lastRenewalTimestamp`, `serviceUpTimestamp`, `evictionTimestamp`. `InstanceInfo` has `lastDirtyTimestamp` and `lastUpdatedTimestamp`. All timestamps are stored as epoch milliseconds (`System.currentTimeMillis()`). No timezone normalization is documented. No `Cache-Control`, `X-Data-Age`, or `last_refreshed` headers are returned in API responses. The response cache (`ResponseCacheImpl`) has a configurable TTL (`responseCacheAutoExpirationInSeconds=180`) and update interval (`responseCacheUpdateIntervalMs=30000`), meaning data may be up to 30 seconds stale.
- **Gap**: Agents cannot determine data freshness from the API response. The response cache means data could be up to 30 seconds old, but no header signals this. Timestamps are in epoch millis without explicit timezone documentation.
- **Compensating Controls**:
  - Add `Cache-Control` and `X-Data-Age` headers at the API Gateway layer.
  - Document the response cache TTL for agent consumers.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add `Cache-Control: max-age=30` and `X-Eureka-Cache-Age` response headers to signal data freshness to agents.
- **Evidence**: `eureka-client/src/main/java/com/netflix/appinfo/LeaseInfo.java` (timestamp fields), `eureka-core/src/main/java/com/netflix/eureka/DefaultEurekaServerConfig.java` (cache TTL configuration)

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: URL-based versioning exists: `@Path("/{version}/apps")` with a `Version` enum supporting `V1` and `V2`. A `CHANGELOG.md` exists in the repository root. However, there are no JSON Schema files, no Avro/Protobuf schemas, no consumer-driven contract tests (Pact), no breaking change detection tools in CI, and no OpenAPI spec to diff. The CI pipeline (`nebula-ci.yml`) runs `./gradlew build` which includes tests but no schema validation.
- **Gap**: Agent tool schemas can break silently when API changes are released. No automated mechanism detects breaking changes before they reach production.
- **Compensating Controls**:
  - Generate an OpenAPI spec and add schema diff detection to CI.
  - Implement consumer-driven contract tests for agent tool definitions.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Generate an OpenAPI specification and add breaking change detection (e.g., `openapi-diff`) to the CI pipeline. This protects agent tool bindings from silent breakage.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/Version.java` (V1/V2 enum), `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationsResource.java` (`@Path("/{version}/apps")`), `.github/workflows/nebula-ci.yml` (no schema validation)

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No OpenTelemetry SDK, no X-Ray instrumentation, no `traceparent` header propagation found in the codebase. Logging uses SLF4J with log4j `ConsoleAppender` producing plain-text logs with pattern `%d %-5p %C:%L [%t] [%M] %m%n`. No JSON structured logging. No `request_id` or `correlation_id` fields in log output.
- **Gap**: Agent-initiated requests cannot be traced through the Eureka server. If a registry query fails, there is no trace ID to reconstruct the request path. Plain-text logs are difficult to query and correlate.
- **Compensating Controls**:
  - Deploy a service mesh (Envoy/Istio) that adds distributed tracing at the infrastructure layer.
  - Add a request correlation filter that generates and propagates trace IDs.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement structured JSON logging and add trace ID propagation. Consider OpenTelemetry Java agent for zero-code instrumentation.
- **Evidence**: `eureka-server/src/main/resources/log4j.properties` (plain-text ConsoleAppender, no JSON layout)

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Eureka uses Netflix Servo for in-process metrics (`EurekaMonitors` enum tracks RENEW, CANCEL, GET_ALL, RATE_LIMITED counters). `AbstractInstanceRegistry` exposes `numOfRenewsInLastMin` and `numOfRenewsPerMinThreshold` as Servo gauges. Self-preservation mode triggers when heartbeat rate drops below 85% threshold — this is a form of anomaly detection. However, there are no external alerting configurations (no CloudWatch alarms, no PagerDuty/OpsGenie integration, no SLO-based alerting).
- **Gap**: Servo counters are in-process metrics that require an external monitoring system (Atlas, CloudWatch custom metrics) to be actionable. No alerting thresholds are configured in this repository for error rates or latency.
- **Compensating Controls**:
  - Expose Servo metrics via a metrics endpoint and configure external alerting (CloudWatch, Prometheus + Alertmanager).
  - Self-preservation mode provides built-in anomaly detection for heartbeat drops.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Export Servo metrics to CloudWatch or Prometheus and configure alerting thresholds for error rates and P99 latency on agent-consumed endpoints.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/util/EurekaMonitors.java` (in-process counters), `eureka-core/src/main/java/com/netflix/eureka/registry/AbstractInstanceRegistry.java` (Servo gauge annotations)

#### ENG-Q1: Infrastructure Governance — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No Infrastructure-as-Code files exist in this repository. No Terraform, CloudFormation, CDK, Helm, Kustomize, or Ansible files found. The repository is a Java application/library published as Maven artifacts. The deployment infrastructure (API Gateway, IAM roles, network configurations, load balancers) would need to be defined separately.
- **Gap**: The integration surface that agents would call is not defined as code, not subject to peer review, and not monitored for drift. Any infrastructure changes happen outside this repository.
- **Compensating Controls**:
  - This is expected for a library/framework project — deployment IaC would exist in separate deployment repositories.
  - Document the expected deployment topology and infrastructure requirements.
- **Remediation Timeline**: N/A — IaC would be in a separate deployment repository
- **Recommendation**: Create a companion deployment repository with IaC (Terraform or CDK) that defines the Eureka server deployment infrastructure, including API Gateway, IAM roles, and network configuration.
- **Evidence**: No `.tf`, `.cfn.yaml`, `cdk.json`, `Chart.yaml`, or `kustomization.yaml` files found in the repository.

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: GitHub Actions CI (`nebula-ci.yml`) runs `./gradlew --info --stacktrace build` which compiles and runs tests (JUnit 4). `nebula-publish.yml` handles release publishing to Maven Central. `nebula-snapshot.yml` publishes snapshots. No API contract tests (Pact), no OpenAPI spec validation, no schema comparison tools, no breaking change detection in the pipeline.
- **Gap**: API contract changes are not caught before agents are affected. A change to the response schema of `GET /apps` would not be detected by the current CI pipeline.
- **Compensating Controls**:
  - The existing API integration tests (ApplicationResourceTest, InstanceResourceTest) provide some coverage for API behavior.
  - Add OpenAPI spec validation and schema diff as CI steps.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add API contract testing to the CI pipeline. Generate an OpenAPI spec from annotations and run `openapi-diff` on each PR to detect breaking changes.
- **Evidence**: `.github/workflows/nebula-ci.yml` (build + test only), `.github/workflows/nebula-publish.yml` (release publishing)

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No deployment configuration exists in this repository. Eureka is published as a Maven artifact (WAR file). Rollback would mean deploying a previous version of the artifact. No blue/green deployment, no CodeDeploy, no Helm rollback, no canary deployment, no traffic shifting configurations found.
- **Gap**: Cannot roll back to a previous known-good state within 15–30 minutes from this repository alone. Rollback capability depends on the deployment infrastructure (which is not defined here).
- **Compensating Controls**:
  - Maven artifact versioning allows rolling back to a previous version.
  - Deployment infrastructure (not in this repo) should implement blue/green or canary deployment.
- **Remediation Timeline**: N/A — rollback would be in the deployment repository
- **Recommendation**: Ensure the deployment infrastructure for Eureka server includes blue/green or canary deployment with automatic rollback capability.
- **Evidence**: `build.gradle` (Nebula plugin for artifact publishing), `.github/workflows/nebula-publish.yml` (artifact publication only)

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO
- **Finding**: Eureka server exposes a well-defined REST API via Jersey JAX-RS annotations. Key resource classes: `ApplicationsResource` (`@Path("/{version}/apps")`), `ApplicationResource`, `InstanceResource`, `PeerReplicationResource` (`@Path("/{version}/peerreplication")`), `StatusResource`, `ServerInfoResource`, `VIPResource`, `SecureVIPResource`, `InstancesResource`, `ASGResource`. All produce JSON and XML (`@Produces({"application/xml", "application/json"})`). No direct database access, file-based exchange, or UI automation patterns.
- **Implication**: The REST API is a suitable integration surface for agent tools. Agents can bind to the documented endpoint paths.
- **Recommendation**: No action needed — API surface exists and is well-structured.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationsResource.java`, `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationResource.java`, `eureka-core/src/main/java/com/netflix/eureka/resources/InstanceResource.java`

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Write endpoints are effectively idempotent: POST `/apps/{appId}` (register) with the same instance ID updates the existing lease rather than creating duplicates, due to `putIfAbsent` and `lastDirtyTimestamp` comparison logic in `AbstractInstanceRegistry.register()`. PUT heartbeat (renewLease) is naturally idempotent. PUT status update is idempotent for the same status value. DELETE cancel is idempotent (returns 404 if already cancelled).
- **Implication**: For read-only agent scope, this is informational. If scope expands to write-enabled, the existing idempotency patterns provide a good foundation.
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/registry/AbstractInstanceRegistry.java` (register method with putIfAbsent)

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: Eureka API supports both JSON and XML response formats, selectable via `Accept` header. JSON is the default when the Accept header contains "json". XML is served otherwise. Response serialization uses Jackson for JSON (`EurekaJsonJacksonCodec`) and XStream/Jackson for XML. GZIP compression is supported via `Accept-Encoding: gzip` header.
- **Implication**: JSON format is ideal for LLM consumption. Agents should specify `Accept: application/json` and `Accept-Encoding: gzip` for optimal integration.
- **Recommendation**: Configure agent tools to request JSON format explicitly.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationsResource.java` (`@Produces({"application/xml", "application/json"})`)

### API-Q7: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: No webhook, SNS, EventBridge, or Kafka integration exists for external event emission. Peer replication (`PeerEurekaNode`) propagates state changes between Eureka servers but is an internal mechanism. The `recentlyChangedQueue` (delta queue) tracks recent changes for the delta API endpoint but operates as a pull-based mechanism, not event-driven.
- **Implication**: Agents must poll the Eureka API to detect changes. The delta endpoint (`GET /apps/delta`) provides efficient incremental updates. For proactive agent behavior, consider implementing a change notification mechanism.
- **Recommendation**: For initial agent integration, use the delta endpoint for efficient polling. If event-driven agent behavior is needed, consider adding EventBridge integration.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/cluster/PeerEurekaNode.java` (internal replication only), `eureka-core/src/main/java/com/netflix/eureka/registry/AbstractInstanceRegistry.java` (recentlyChangedQueue)

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: The `RateLimitingFilter` returns HTTP 503 when rate limiting is triggered but does **not** include `X-RateLimit-Remaining`, `X-RateLimit-Limit`, or `Retry-After` response headers. Rate limit configuration is available via properties (`eureka.rateLimiter.burstSize=10`, `eureka.rateLimiter.registryFetchAverageRate=500`, `eureka.rateLimiter.fullFetchAverageRate=100`) but is not documented in the API surface.
- **Implication**: Agents cannot self-throttle based on rate limit headers. When rate-limited, agents receive a bare 503 without guidance on when to retry.
- **Recommendation**: Add `Retry-After` and `X-RateLimit-Remaining` response headers to the `RateLimitingFilter` to enable agent self-throttling.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/RateLimitingFilter.java` (503 without headers), `eureka-core/src/main/java/com/netflix/eureka/DefaultEurekaServerConfig.java` (rate limiter config)

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: RISK-QUALITY
- **Finding**: The `DiscoveryIdentity-Name` and `DiscoveryIdentity-Version` headers propagate client identity across requests, but there is no JWT, OAuth token exchange, or on-behalf-of flow. The `x-netflix-discovery-replication` header distinguishes peer replication traffic from client traffic but is not authenticated. No Cognito or Okta integration. No distinction between agent-as-self and agent-on-behalf-of-user.
- **Gap**: The system cannot distinguish between an agent acting under its own identity vs. acting on behalf of a user. No identity delegation mechanism exists.
- **Recommendation**: Implement identity propagation at the API Gateway layer using JWT tokens that encode both the agent identity and the delegating user identity.
- **Evidence**: `eureka-client/src/main/java/com/netflix/appinfo/AbstractEurekaIdentity.java` (header constants), `eureka-core/src/main/java/com/netflix/eureka/ServerRequestAuthFilter.java` (header reading)

### AUTH-Q5: Credential Management

- **Severity**: RISK-QUALITY
- **Finding**: `DefaultEurekaServerConfig` has `getAWSAccessId()` and `getAWSSecretKey()` methods that read AWS credentials from Archaius configuration properties (`eureka.awsAccessId`, `eureka.awsSecretKey`). No AWS Secrets Manager or HashiCorp Vault integration found. These credentials are used for AWS ASG/EIP management, not for API authentication. No hardcoded credentials found in source code. The CI pipeline uses GitHub Secrets for publishing credentials (`NETFLIX_OSS_SIGNING_KEY`, etc.).
- **Gap**: AWS credentials are read from configuration properties without a secrets management system. No rotation mechanism. However, these are for AWS service integration, not API authentication.
- **Recommendation**: Migrate AWS credential management to IAM roles (instance profiles) or AWS Secrets Manager instead of configuration properties.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/DefaultEurekaServerConfig.java` (getAWSAccessId, getAWSSecretKey methods), `.github/workflows/nebula-publish.yml` (GitHub Secrets for CI)

### STATE-Q2: Queryable Current State

- **Severity**: INFO
- **Finding**: The registry state is fully queryable: `GET /{version}/apps` returns all applications and instances. `GET /{version}/apps/{appId}` returns a specific application. `GET /{version}/apps/{appId}/{instanceId}` returns a specific instance. `GET /{version}/apps/delta` returns recent changes. VIP-based lookups available via `GET /{version}/vips/{vipAddress}` and `GET /{version}/svips/{secureVipAddress}`. Status endpoint provides server health.
- **Implication**: Agents can inspect current service registry state before taking action. The hierarchical query structure (all apps → specific app → specific instance) supports efficient state inspection.
- **Recommendation**: No action needed — state is fully queryable.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationsResource.java` (GET endpoints), `eureka-core/src/main/java/com/netflix/eureka/resources/InstanceResource.java` (instance-level GET)

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: `AbstractInstanceRegistry` uses `ReentrantReadWriteLock` for registry operations. `ConcurrentHashMap` provides thread-safe registry storage. `putIfAbsent` pattern prevents duplicate application entries. `lastDirtyTimestamp` comparison provides conflict resolution for concurrent registrations. Write operations acquire the read lock (allowing concurrent reads), and delta operations acquire the write lock.
- **Implication**: For read-only agent scope, concurrency controls are informational. The existing controls are well-designed for concurrent access.
- **Recommendation**: No action needed for read-only scope. If expanding to write-enabled, the existing concurrency model is sound.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/registry/AbstractInstanceRegistry.java` (ReentrantReadWriteLock, ConcurrentHashMap)

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable limits on agent-initiated actions exist (no max records per query, no max operations per session). The response cache limits the computational cost of full registry fetches. No per-identity transaction limits.
- **Implication**: For read-only agent scope, blast radius is limited since agents cannot modify records. Query volume is the only concern, addressed by rate limiting.
- **Recommendation**: No action needed for read-only scope. If expanding to write-enabled, implement per-identity transaction limits.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/DefaultEurekaServerConfig.java` (no transaction limit configuration)

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No draft/pending state workflow exists. Service registration is immediate — `POST /apps/{appId}` directly adds the instance to the registry. No approval step, no two-step commit (create-then-confirm) pattern.
- **Implication**: For read-only agent scope, this is informational since agents do not make state changes.
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationResource.java` (addInstance is immediate)

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No approval workflow or human-in-the-loop gates exist. All operations execute immediately without approval. No Step Functions with human approval tasks, no configurable operation-level flags.
- **Implication**: For read-only agent scope, this is informational since agents do not execute write operations.
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: No approval endpoints or status-based workflows found in any resource class.

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Field names in `InstanceInfo` are human-readable and semantically meaningful: `appName`, `hostName`, `ipAddr`, `port`, `securePort`, `vipAddress`, `secureVipAddress`, `status`, `dataCenterInfo`, `leaseInfo`, `metadata`, `lastUpdatedTimestamp`, `lastDirtyTimestamp`, `actionType`. `LeaseInfo` fields: `registrationTimestamp`, `lastRenewalTimestamp`, `serviceUpTimestamp`, `evictionTimestamp`. No legacy abbreviations requiring a data dictionary.
- **Implication**: LLM-based agents can interpret field names directly without requiring a mapping table. This facilitates automated tool definition generation.
- **Recommendation**: No action needed — field naming is excellent for agent consumption.
- **Evidence**: `eureka-client/src/main/java/com/netflix/appinfo/InstanceInfo.java` (field definitions), `eureka-client/src/main/java/com/netflix/appinfo/LeaseInfo.java` (timestamp fields)

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No formal data catalog (AWS Glue, Collibra, Alation, DataHub) exists. The `eureka-examples` module provides sample configurations. The Eureka wiki (referenced in README) provides documentation. The data model is implicitly documented through `InstanceInfo`, `LeaseInfo`, `Application`, and `Applications` Java classes with Javadoc comments.
- **Implication**: Understanding the data model requires reading Java source code. A data catalog would accelerate agent tool definition.
- **Recommendation**: Generate API documentation (Javadoc or OpenAPI) that serves as a lightweight data catalog for the Eureka data model.
- **Evidence**: `eureka-examples/` (sample configurations), `eureka-client/src/main/java/com/netflix/appinfo/InstanceInfo.java` (data model)

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: `EurekaMonitors` provides extensive business-relevant counters: `registerCounter`, `renewCounter`, `cancelCounter`, `getAllCounter`, `getAllDeltaCounter`, `expiredCounter`, `statusUpdateCounter`, `rateLimitedRequests`, `numOfRejectedReplications`, `numOfFailedReplications`. These track actual service discovery business operations. `AbstractInstanceRegistry` exposes `numOfRenewsInLastMin` and `numOfRenewsPerMinThreshold` as Servo gauges.
- **Implication**: When agents consume the Eureka API, these business metrics can signal whether agent interactions produce good outcomes (e.g., are agent registry queries succeeding? Is the agent's query rate causing rate limiting?).
- **Recommendation**: Export these Servo metrics to an external monitoring system and create dashboards tracking agent-specific traffic patterns.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/util/EurekaMonitors.java` (business metric counters)

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No formal data quality scores or completeness metrics exist. Self-preservation mode protects against mass eviction when heartbeat rates drop below 85% threshold, which indirectly monitors data completeness (if many instances stop renewing, the registry preserves stale entries rather than removing them all). No data profiling reports, null rate monitoring, or data freshness SLAs.
- **Implication**: Agents consuming the registry should be aware that during self-preservation mode, stale entries may be returned. There is no data quality signal in the API response.
- **Recommendation**: Add a header or metadata field indicating whether self-preservation mode is active, so agents can factor this into decision-making.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/registry/AbstractInstanceRegistry.java` (self-preservation logic in evict method)

### HITL-Q3: Sandbox/Staging Environment

- **Severity**: RISK-QUALITY
- **Finding**: No separate sandbox or staging environment configuration exists in this repository. No Docker Compose for local testing. No seed data scripts or synthetic data generators. The `eureka-examples` module provides sample client and service configurations for local development. `eureka-test-utils` provides test infrastructure for integration tests. The CI pipeline runs tests against an embedded Jetty server.
- **Gap**: No production-equivalent staging environment with realistic data shape for agent testing. Agent behavior would first be tested in production.
- **Compensating Controls**:
  - Use the `eureka-examples` module to stand up a local Eureka cluster for agent testing.
  - Create a Docker Compose configuration for a multi-node staging environment.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Create a Docker Compose or Kubernetes manifest for a multi-node Eureka staging environment with synthetic service registrations.
- **Evidence**: `eureka-examples/` (sample configurations), `eureka-test-utils/` (test infrastructure)

### ENG-Q4: API Test Coverage

- **Severity**: RISK-QUALITY
- **Finding**: Test files exist for core API resources: `ApplicationsResourceTest`, `ApplicationResourceTest`, `InstanceResourceTest`, `PeerReplicationResourceTest`, `EurekaClientServerRestIntegrationTest`, `ReplicationConcurrencyTest`. Additional tests cover registry logic (`InstanceRegistryTest`, `ResponseCacheTest`), rate limiting (`RateLimitingFilterTest`), and cluster behavior (`PeerEurekaNodeTest`, `PeerEurekaNodesTest`). Tests use JUnit 4 with Mockito.
- **Gap**: Tests cover core API paths but there are no explicit contract tests that validate response schemas against a specification. No Postman/Newman collections or REST Assured tests for comprehensive API validation.
- **Compensating Controls**:
  - Existing integration tests provide reasonable coverage for API behavior.
  - Add contract testing as described in ENG-Q2.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Supplement existing tests with contract tests that validate response schemas against an OpenAPI specification.
- **Evidence**: `eureka-core/src/test/java/com/netflix/eureka/resources/` (API test classes), `eureka-server/src/test/java/com/netflix/eureka/resources/EurekaClientServerRestIntegrationTest.java`

### ENG-Q5: Encryption at Rest

- **Severity**: INFO
- **Finding**: Eureka stores all data in-memory (`ConcurrentHashMap`). There is no persistent data store (no database, no disk-based storage). The response cache (`ResponseCacheImpl`) is also in-memory (Guava cache). No KMS configuration or encryption-at-rest settings exist. AWS credentials in configuration properties are the only sensitive data at rest, but these are configuration properties, not API-served data.
- **Implication**: Since Eureka uses in-memory storage exclusively, encryption at rest is not applicable in the traditional sense. Data exists only in JVM heap memory.
- **Recommendation**: No action needed — in-memory storage does not require encryption at rest. Ensure the JVM process runs in a secure environment with appropriate memory isolation.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/registry/AbstractInstanceRegistry.java` (ConcurrentHashMap registry)

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: Eureka server exposes a well-defined REST API via Jersey JAX-RS annotations across 10+ resource classes. Endpoints produce JSON and XML. No database-direct, file-based, or UI automation patterns.
- **Gap**: N/A — API surface exists
- **Recommendation**: N/A
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationsResource.java`, `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationResource.java`, `eureka-core/src/main/java/com/netflix/eureka/resources/InstanceResource.java`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, GraphQL schema, or machine-readable specification exists. API documented only via JAX-RS annotations and Javadoc.
- **Gap**: Cannot auto-generate agent tool definitions from a specification.
- **Recommendation**: Generate OpenAPI 3.0 spec from JAX-RS annotations.
- **Evidence**: No spec files found in repository.

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: Error responses are plain text (400) or empty bodies (500/404). No structured error codes, no retryable indicators.
- **Gap**: Agents cannot programmatically distinguish error types.
- **Recommendation**: Implement consistent JSON error response format with `errorCode`, `message`, `retryable` fields.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationResource.java`, `eureka-core/src/main/java/com/netflix/eureka/resources/InstanceResource.java`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Write endpoints are effectively idempotent through `putIfAbsent` and `lastDirtyTimestamp` logic.
- **Gap**: N/A for read-only scope
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/registry/AbstractInstanceRegistry.java`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: JSON and XML supported via Accept header. GZIP compression available.
- **Gap**: N/A
- **Recommendation**: Configure agents to request JSON explicitly.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationsResource.java`

#### API-Q6: Asynchronous Operation Support
- **Severity**: RISK-QUALITY
- **Finding**: All client-facing operations are synchronous. Background operations (peer sync, eviction) are internal only.
- **Gap**: No async API patterns for long-running operations.
- **Recommendation**: Response caching mitigates latency for read operations. Acceptable for most use cases.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationsResource.java`

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: No webhook/SNS/EventBridge integration. Peer replication is internal. Delta queue is pull-based.
- **Gap**: N/A — informational
- **Recommendation**: Use delta endpoint for efficient polling.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/cluster/PeerEurekaNode.java`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: Rate limiter returns 503 without rate limit headers. Configuration available but not exposed in API.
- **Gap**: N/A — informational
- **Recommendation**: Add Retry-After and X-RateLimit-Remaining headers.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/RateLimitingFilter.java`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: Header-based client identification only (DiscoveryIdentity-Name). No credential verification, no OAuth2, no mTLS.
- **Gap**: No authentication mechanism. Any HTTP client can access all endpoints.
- **Recommendation**: Deploy behind API Gateway with OAuth2 client credentials or API key authentication.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/ServerRequestAuthFilter.java`, `eureka-client/src/main/java/com/netflix/appinfo/AbstractEurekaIdentity.java`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: No authorization model. All endpoints accessible to all callers.
- **Gap**: Cannot grant read-only access to agents.
- **Recommendation**: API Gateway method-level authorization restricting agents to GET endpoints.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationsResource.java`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: No ABAC, RBAC, or action-level checks. isReplication header is not enforced.
- **Gap**: Cannot enforce read vs write vs delete at the action level.
- **Recommendation**: API Gateway method-level restrictions for agent identities.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/resources/InstanceResource.java`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: RISK-QUALITY
- **Finding**: DiscoveryIdentity headers propagate client name but no JWT/OAuth token exchange. No agent-as-self vs agent-on-behalf-of-user distinction.
- **Gap**: No identity delegation mechanism.
- **Recommendation**: Implement JWT-based identity propagation at API Gateway layer.
- **Evidence**: `eureka-client/src/main/java/com/netflix/appinfo/AbstractEurekaIdentity.java`, `eureka-core/src/main/java/com/netflix/eureka/ServerRequestAuthFilter.java`

#### AUTH-Q5: Credential Management
- **Severity**: RISK-QUALITY
- **Finding**: AWS credentials read from Archaius configuration properties. No Secrets Manager or Vault. CI uses GitHub Secrets.
- **Gap**: No secrets management system for AWS credentials. No rotation mechanism.
- **Recommendation**: Migrate to IAM instance profiles or AWS Secrets Manager.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/DefaultEurekaServerConfig.java`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: ServerRequestAuthFilter logs identity via Servo DynamicCounter (metric counter, not audit log). No immutable audit logs, no CloudTrail.
- **Gap**: No audit trail for API calls.
- **Recommendation**: API Gateway access logging to immutable store (S3 with Object Lock).
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/ServerRequestAuthFilter.java`, `eureka-server/src/main/resources/log4j.properties`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: No mechanism to suspend individual client identities. Rate limiter is global only.
- **Gap**: Cannot revoke a specific misbehaving agent.
- **Recommendation**: API Gateway with per-identity API key revocation.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/RateLimitingFilter.java`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No saga, two-phase commit, or undo endpoints. Peer replication is fire-and-forget.
- **Gap**: No rollback for partially replicated operations.
- **Recommendation**: Accept eventual consistency model for read-only scope.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/cluster/PeerEurekaNode.java`

#### STATE-Q2: Queryable Current State
- **Severity**: INFO
- **Finding**: Registry fully queryable via GET /apps, /apps/{appId}, /apps/{appId}/{instanceId}, /apps/delta, VIP endpoints.
- **Gap**: N/A
- **Recommendation**: No action needed.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationsResource.java`

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: ReentrantReadWriteLock, ConcurrentHashMap, putIfAbsent pattern, lastDirtyTimestamp conflict resolution.
- **Gap**: N/A for read-only scope
- **Recommendation**: No action needed.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/registry/AbstractInstanceRegistry.java`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: No circuit breaker pattern. Timeouts and batching exist but no circuit breaker for peer node calls.
- **Gap**: Cascading failure risk from unresponsive peers.
- **Recommendation**: Service mesh circuit breaker or Resilience4j on peer HTTP calls.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/cluster/PeerEurekaNode.java`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: RateLimitingFilter exists but is disabled by default. Filter-mapping in web.xml is commented out.
- **Gap**: No active rate limiting. Agent traffic storms could overwhelm the server.
- **Recommendation**: Enable built-in rate limiter or deploy API Gateway throttling.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/RateLimitingFilter.java`, `eureka-server/src/main/webapp/WEB-INF/web.xml`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits per agent identity.
- **Gap**: N/A for read-only scope
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/DefaultEurekaServerConfig.java`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path. This service is P2.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No draft/pending state. Registration is immediate.
- **Gap**: N/A for read-only scope
- **Recommendation**: No action needed.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationResource.java`

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No approval workflows. All operations execute immediately.
- **Gap**: N/A for read-only scope
- **Recommendation**: No action needed.
- **Evidence**: No approval endpoints found.

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: No staging environment configuration. eureka-examples and eureka-test-utils provide development/test infrastructure.
- **Gap**: No production-equivalent staging for agent testing.
- **Recommendation**: Create Docker Compose for multi-node staging environment.
- **Evidence**: `eureka-examples/`, `eureka-test-utils/`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: Eureka stores service instance metadata: hostnames, IP addresses, ports, VIP addresses, health check URLs, AWS metadata (AMI ID, instance ID, availability zone). No data classification tags. No PII/PHI/financial data. IP addresses and AWS instance IDs may be considered infrastructure-sensitive. AWS credentials exist in configuration but are not served via API.
- **Gap**: No field-level classification or tagging of data sensitivity. Infrastructure metadata is unclassified.
- **Recommendation**: Classify infrastructure metadata fields and document sensitivity levels. While Eureka primarily stores operational infrastructure metadata (not PII/PHI), the absence of any classification framework means the gap exists per DATA-Q1 requirements. For most deployments, this is a low-effort remediation — document that registry data is infrastructure-operational, classify IP addresses and instance IDs as infrastructure-sensitive, and tag fields accordingly.
- **Evidence**: `eureka-client/src/main/java/com/netflix/appinfo/InstanceInfo.java`, `eureka-client/src/main/java/com/netflix/appinfo/AmazonInfo.java`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No data residency requirements documented. Multi-region support via remoteRegionUrls. Infrastructure metadata not typically regulated.
- **Gap**: No data residency controls.
- **Recommendation**: Document data residency posture for infrastructure metadata.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/DefaultEurekaServerConfig.java`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK-QUALITY
- **Finding**: GET /apps returns full registry without pagination. Delta endpoint and per-app/per-instance queries available.
- **Gap**: No pagination on full registry endpoint.
- **Recommendation**: Use targeted queries instead of full registry fetches for agents.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationsResource.java`

#### DATA-Q4: System of Record Designations
- **Severity**: RISK-QUALITY
- **Finding**: Peer-to-peer replication with eventual consistency. No single golden record. lastDirtyTimestamp conflict resolution.
- **Gap**: Agents may see inconsistent data across peers during replication lag.
- **Recommendation**: Document eventual consistency model for agent consumers.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/registry/PeerAwareInstanceRegistryImpl.java`

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK-QUALITY
- **Finding**: LeaseInfo and InstanceInfo include timestamps in epoch millis. No Cache-Control or freshness headers. Response cache may return up to 30-second stale data.
- **Gap**: No data freshness signal in API responses.
- **Recommendation**: Add Cache-Control and X-Data-Age response headers.
- **Evidence**: `eureka-client/src/main/java/com/netflix/appinfo/LeaseInfo.java`

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: Infrastructure metadata (IPs, hostnames) logged in plain text. No PII masking. However, data is infrastructure metadata, not customer PII.
- **Gap**: No log redaction mechanism.
- **Recommendation**: Assess compliance requirements for infrastructure metadata in logs.
- **Evidence**: `eureka-server/src/main/resources/log4j.properties`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality scores. Self-preservation mode provides indirect data completeness protection.
- **Gap**: N/A — informational
- **Recommendation**: Signal self-preservation mode status in API responses.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/registry/AbstractInstanceRegistry.java`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: URL-based versioning (V1/V2). CHANGELOG.md exists. No JSON Schema, no contract tests, no breaking change detection in CI.
- **Gap**: Agent tool schemas can break silently on API changes.
- **Recommendation**: Generate OpenAPI spec with breaking change detection in CI.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/Version.java`, `CHANGELOG.md`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Field names are human-readable: appName, hostName, ipAddr, port, status, leaseInfo, metadata. No legacy abbreviations.
- **Gap**: N/A
- **Recommendation**: No action needed.
- **Evidence**: `eureka-client/src/main/java/com/netflix/appinfo/InstanceInfo.java`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal data catalog. Data model documented through Java classes with Javadoc.
- **Gap**: N/A — informational
- **Recommendation**: Generate API documentation from source.
- **Evidence**: `eureka-examples/`, `eureka-client/src/main/java/com/netflix/appinfo/InstanceInfo.java`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: No OpenTelemetry, X-Ray, or traceparent propagation. Plain-text log4j logging. No request_id or correlation_id.
- **Gap**: Agent-initiated requests cannot be traced through the system.
- **Recommendation**: Add OpenTelemetry Java agent and structured JSON logging.
- **Evidence**: `eureka-server/src/main/resources/log4j.properties`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: Servo in-process metrics (counters and gauges). Self-preservation mode for anomaly detection. No external alerting configured.
- **Gap**: No external alerting thresholds for error rates or latency.
- **Recommendation**: Export Servo metrics to CloudWatch/Prometheus and configure alerting.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/util/EurekaMonitors.java`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: EurekaMonitors provides extensive business counters: register, renew, cancel, getAll, rateLimited, failedReplications.
- **Gap**: N/A — informational
- **Recommendation**: Export metrics to external monitoring for agent behavior dashboards.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/util/EurekaMonitors.java`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance
- **Severity**: RISK-QUALITY
- **Finding**: No IaC files in repository. Application published as Maven artifact. Deployment infrastructure would be defined separately.
- **Gap**: Integration surface not defined as code in this repository.
- **Recommendation**: Create companion deployment IaC repository.
- **Evidence**: No IaC files found.

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: GitHub Actions CI runs build + tests. No API contract tests, no schema validation, no breaking change detection.
- **Gap**: API breaking changes not caught before release.
- **Recommendation**: Add OpenAPI spec validation and contract testing to CI.
- **Evidence**: `.github/workflows/nebula-ci.yml`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: Published as Maven artifact. No deployment-level rollback configuration in this repository.
- **Gap**: Rollback depends on external deployment infrastructure.
- **Recommendation**: Ensure deployment infrastructure includes blue/green with rollback.
- **Evidence**: `build.gradle`, `.github/workflows/nebula-publish.yml`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: API integration tests exist (ApplicationResourceTest, InstanceResourceTest, PeerReplicationResourceTest, etc.). JUnit 4 + Mockito. No explicit contract tests.
- **Gap**: No schema validation tests against a specification.
- **Recommendation**: Add contract tests validating response schemas.
- **Evidence**: `eureka-core/src/test/java/com/netflix/eureka/resources/`

#### ENG-Q5: Encryption at Rest
- **Severity**: INFO
- **Finding**: In-memory storage only (ConcurrentHashMap). No persistent data store. Encryption at rest not applicable.
- **Gap**: N/A — in-memory storage
- **Recommendation**: No action needed.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/registry/AbstractInstanceRegistry.java`

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationsResource.java` | API-Q1, API-Q2, API-Q5, API-Q6, AUTH-Q2, DATA-Q3, STATE-Q2 |
| `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationResource.java` | API-Q1, API-Q3, AUTH-Q2, AUTH-Q3, HITL-Q1 |
| `eureka-core/src/main/java/com/netflix/eureka/resources/InstanceResource.java` | API-Q1, API-Q3, AUTH-Q3, DATA-Q4, STATE-Q2 |
| `eureka-core/src/main/java/com/netflix/eureka/resources/PeerReplicationResource.java` | API-Q1 |
| `eureka-core/src/main/java/com/netflix/eureka/ServerRequestAuthFilter.java` | AUTH-Q1, AUTH-Q4, AUTH-Q6 |
| `eureka-core/src/main/java/com/netflix/eureka/RateLimitingFilter.java` | API-Q8, AUTH-Q7, STATE-Q5 |
| `eureka-core/src/main/java/com/netflix/eureka/DefaultEurekaServerConfig.java` | AUTH-Q5, STATE-Q5, STATE-Q6, DATA-Q2, DATA-Q5 |
| `eureka-core/src/main/java/com/netflix/eureka/registry/AbstractInstanceRegistry.java` | API-Q4, STATE-Q1, STATE-Q3, DATA-Q6, DATA-Q7, ENG-Q5, OBS-Q2 |
| `eureka-core/src/main/java/com/netflix/eureka/registry/PeerAwareInstanceRegistryImpl.java` | DATA-Q4 |
| `eureka-core/src/main/java/com/netflix/eureka/cluster/PeerEurekaNode.java` | API-Q7, STATE-Q1, STATE-Q4 |
| `eureka-core/src/main/java/com/netflix/eureka/util/EurekaMonitors.java` | OBS-Q2, OBS-Q3 |
| `eureka-core/src/main/java/com/netflix/eureka/util/batcher/TrafficShaper.java` | STATE-Q4 |
| `eureka-core/src/main/java/com/netflix/eureka/Version.java` | DISC-Q1 |
| `eureka-client/src/main/java/com/netflix/appinfo/InstanceInfo.java` | DATA-Q1, DATA-Q5, DISC-Q2, DISC-Q3 |
| `eureka-client/src/main/java/com/netflix/appinfo/LeaseInfo.java` | DATA-Q5, DISC-Q2 |
| `eureka-client/src/main/java/com/netflix/appinfo/AbstractEurekaIdentity.java` | AUTH-Q1, AUTH-Q4 |
| `eureka-client/src/main/java/com/netflix/appinfo/AmazonInfo.java` | DATA-Q1 |
| `eureka-client/src/main/java/com/netflix/discovery/shared/transport/decorator/RetryableEurekaHttpClient.java` | STATE-Q4 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/nebula-ci.yml` | ENG-Q2, DISC-Q1 |
| `.github/workflows/nebula-publish.yml` | AUTH-Q5, ENG-Q2, ENG-Q3 |
| `.github/workflows/nebula-snapshot.yml` | ENG-Q2 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `build.gradle` | ENG-Q3 |
| `eureka-server/build.gradle` | ENG-Q4 |
| `eureka-core/build.gradle` | ENG-Q4 |
| `eureka-client/build.gradle` | ENG-Q4 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `eureka-server/src/main/webapp/WEB-INF/web.xml` | AUTH-Q1, STATE-Q5 |
| `eureka-server/src/main/resources/eureka-server.properties` | DATA-Q2 |
| `eureka-server/src/main/resources/eureka-client.properties` | DATA-Q2 |
| `eureka-server/src/main/resources/log4j.properties` | AUTH-Q6, DATA-Q6, OBS-Q1 |
| `CHANGELOG.md` | DISC-Q1 |

### Test Files
| File | Questions Referenced |
|------|---------------------|
| `eureka-core/src/test/java/com/netflix/eureka/resources/ApplicationsResourceTest.java` | ENG-Q4 |
| `eureka-core/src/test/java/com/netflix/eureka/resources/ApplicationResourceTest.java` | ENG-Q4 |
| `eureka-core/src/test/java/com/netflix/eureka/resources/InstanceResourceTest.java` | ENG-Q4 |
| `eureka-core/src/test/java/com/netflix/eureka/resources/PeerReplicationResourceTest.java` | ENG-Q4 |
| `eureka-server/src/test/java/com/netflix/eureka/resources/EurekaClientServerRestIntegrationTest.java` | ENG-Q4 |

### Notable Absences (Absence as Evidence)
| Category | Finding | Questions Referenced |
|----------|---------|---------------------|
| No IaC files | No `.tf`, `.cfn.yaml`, `cdk.json`, `Chart.yaml`, `kustomization.yaml` | ENG-Q1 |
| No API spec files | No `openapi.yaml`, `swagger.yaml`, `swagger.json`, `.graphql`, `.smithy` | API-Q2, DISC-Q1 |
| No container files | No `Dockerfile`, `docker-compose.yml` | HITL-Q3 |
| No tracing libraries | No OpenTelemetry, X-Ray dependencies | OBS-Q1 |
| No alerting configuration | No CloudWatch alarms, PagerDuty config | OBS-Q2 |
