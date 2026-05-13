# Agentic Readiness Assessment Report

**Target**: eureka (Netflix/eureka monorepo)
**Date**: 2026-04-30
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**TD Version**: agentic-readiness-assessment
**Repository Type**: monorepo
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: java, service-discovery, microservices
**Context**: Netflix service-discovery server and client.

**Archetype Justification**: The eureka-server maintains an in-memory ConcurrentHashMap registry (persistent state during runtime), exposes REST CRUD endpoints for service registration (POST register, PUT renew/status, DELETE cancel), and manages instance lifecycle including creation, heartbeats, eviction, and status changes — matching the stateful-crud archetype.

**Surface flags**:
- has_persistent_data_store: true (in-memory ConcurrentHashMap registry storing InstanceInfo)
- has_http_rpc_surface: true (Jersey JAX-RS REST endpoints at /{version}/apps/*)
- has_auth_surface: false (ServerRequestAuthFilter only logs identity headers, no enforcement)
- has_write_operations: true (POST register, PUT renew/status-update, DELETE cancel)
- has_logging_of_user_data: false (logs only client identity headers and infrastructure metadata, not user PII)

**Monorepo Note**: This monorepo contains two logical service groups: (A) eureka-server (eureka-server, eureka-server-governator, eureka-core, eureka-core-jersey2) — the service discovery server; (B) eureka-client (eureka-client, eureka-client-jersey2, eureka-client-archaius2) — the client library. Assessment is driven by the server component as the primary deployable service.

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 1 | **RISK-SAFETY**: 6 | **RISK-QUALITY**: 11 | **INFOs**: 22

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days. The single BLOCKER (AUTH-Q1: no machine identity authentication) must be remediated before any agent can safely interact with the Eureka server REST API.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 1 |
| RISK-SAFETY | 6 |
| RISK-QUALITY | 11 |
| INFO | 22 |
| N/A | 0 |
| Not Evaluated (extended) | 3 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 16
**Extended Questions Not Triggered**: 3
**Questions N/A (repo_type: monorepo)**: 0
**Service Archetype**: stateful-crud (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: Eureka uses custom identity headers (`DiscoveryIdentity-Name`, `DiscoveryIdentity-Version`, `DiscoveryIdentity-Id`) defined in `AbstractEurekaIdentity.java`. However, `ServerRequestAuthFilter.java` only **logs** these headers via Netflix Servo `DynamicCounter` — it does not validate, authenticate, or reject requests based on them. The filter calls `chain.doFilter(request, response)` unconditionally after logging. There is no OAuth2 client credentials flow, no API key validation, no mTLS configuration, no Cognito integration, and no API Gateway authorizer. Any HTTP client can call any endpoint without credentials.
- **Gap**: No machine identity authentication mechanism exists. All endpoints are completely unauthenticated. An agent identity cannot be established or attributed in any log.
- **Remediation**:
  - **Immediate**: Implement an API Gateway (e.g., AWS API Gateway, Kong, or Envoy) in front of the Eureka server that enforces OAuth2 client credentials or API key authentication with principal attribution. This is the fastest path as it does not require modifying Eureka source code.
  - **Target State**: Every request to the Eureka server REST API is authenticated with a verifiable machine identity. The authenticated principal is recorded in structured logs for audit purposes.
  - **Estimated Effort**: Medium (2–4 weeks for API Gateway approach, 4–8 weeks for in-application auth)
  - **Dependencies**: AUTH-Q2 (scoped permissions), AUTH-Q3 (action-level auth), and AUTH-Q6 (audit logging) all depend on establishing identity first.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/ServerRequestAuthFilter.java`, `eureka-client/src/main/java/com/netflix/appinfo/AbstractEurekaIdentity.java`, `eureka-server/src/main/webapp/WEB-INF/web.xml`

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No authorization model exists. There are no IAM policies, no RBAC/ABAC definitions, and no role-per-service configuration in the Eureka server. All clients — whether service instances registering themselves, peer Eureka nodes replicating state, or any external caller — have identical unrestricted access to all endpoints. The `RateLimitingFilter` distinguishes "privileged" vs "standard" clients via the `DiscoveryIdentity-Name` header, but this is traffic management, not authorization.
- **Gap**: No mechanism to grant an agent read-only access to specific resources without inheriting broader privileges (e.g., register/cancel capabilities).
- **Compensating Controls**:
  - Deploy an API Gateway in front of Eureka that enforces route-level access control (e.g., allow GET `/v2/apps/*` but deny POST/PUT/DELETE for agent identities).
  - Use network-level segmentation to restrict agent access to read-only paths only.
- **Remediation Timeline**: 30–60 days (API Gateway approach)
- **Recommendation**: Implement API Gateway route-level authorization as a first step. Map agent identities to read-only IAM policies or API key usage plans.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/ServerRequestAuthFilter.java`, `eureka-core/src/main/java/com/netflix/eureka/RateLimitingFilter.java`

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization enforcement exists. Any client can register (POST), renew (PUT), cancel (DELETE), or update status (PUT) for any application. The `shouldAllowAccess()` method in `ApplicationsResource.java` is a server-readiness check (whether the server is ready to serve traffic), not an authorization check. Peer replication requests are distinguished by the `x-netflix-discovery-replication` header but this header is not validated — any client can set it.
- **Gap**: Cannot enforce that an agent identity may read records but not delete them, even within the same resource type.
- **Compensating Controls**:
  - API Gateway method-level authorization: allow GET for agent identities, deny POST/PUT/DELETE.
  - Network policy restricting agent traffic to read-only API paths.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement method-level authorization at the API Gateway layer, scoping agent identities to GET-only access on `/v2/apps/*` and `/v2/status` endpoints.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationsResource.java`, `eureka-core/src/main/java/com/netflix/eureka/resources/InstanceResource.java`

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: `ServerRequestAuthFilter` logs client identity headers (`DiscoveryIdentity-Name`, `DiscoveryIdentity-Version`) via Netflix Servo `DynamicCounter.increment()`. These are **metrics counters**, not immutable audit logs — they record aggregate counts, not individual request-level audit trails. There is no CloudTrail integration, no immutable log storage (S3 with Object Lock), no structured audit log capturing who did what and when. SLF4J logging exists for operations (e.g., "Registered instance {}/{} with status {}") but these are operational logs, not tamper-evident audit trails.
- **Gap**: No immutable, tamper-evident audit log capturing the authenticated principal for each API operation. Cannot prove which agent or client performed a specific action.
- **Compensating Controls**:
  - Deploy API Gateway with CloudWatch access logging enabled, capturing caller identity and request details.
  - Enable CloudTrail for API Gateway if using AWS API Gateway.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement structured audit logging at the API Gateway layer with CloudTrail integration. Long-term, add request-level audit logging to the Eureka server with immutable storage.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/ServerRequestAuthFilter.java`, `eureka-core/src/main/java/com/netflix/eureka/util/EurekaMonitors.java`

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No mechanism exists to suspend or revoke individual client identities. There is no API key revocation endpoint, no client blocklist, no Cognito user disable, and no IAM role deactivation. The `RateLimitingFilter` has a concept of "privileged clients" (`rateLimiterPrivilegedClients` configuration), but this is an allowlist for rate limit exemption, not a blocklist for identity suspension. Removing a client from the privileged list only subjects it to rate limiting — it does not block access.
- **Gap**: Cannot isolate a misbehaving agent without taking down the broader platform or restarting the server.
- **Compensating Controls**:
  - API Gateway API key management: disable/revoke specific API keys for misbehaving agents.
  - Network-level blocklist (WAF rules) to deny traffic from specific agent IP ranges.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement API key-based identity at the API Gateway layer with the ability to immediately revoke individual keys.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/RateLimitingFilter.java`, `eureka-core/src/main/java/com/netflix/eureka/DefaultEurekaServerConfig.java`

#### STATE-Q1: Compensation and Rollback ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No saga patterns, compensating transactions, or explicit undo endpoints exist. The in-memory registry uses `ConcurrentHashMap` with no database transaction support. Peer replication achieves eventual consistency via `lastDirtyTimestamp` comparison but provides no explicit rollback mechanism. When a registration fails mid-sequence or peer replication conflicts, the system resolves by timestamp comparison (`syncInstancesIfTimestampDiffers`), not by rolling back to a known good state. Self-preservation mode prevents mass eviction but is not a compensation mechanism.
- **Gap**: No compensation or rollback capability for multi-step operations. If a registration + peer replication sequence fails partway, there is no automatic recovery to a consistent state.
- **Compensating Controls**:
  - For read-only agent scope, compensation risk is low since agents won't initiate write workflows.
  - Eureka's self-healing via heartbeat renewal and lease expiration provides eventual consistency as a natural compensation mechanism.
- **Remediation Timeline**: 60–90 days (if write-enabled scope is planned)
- **Recommendation**: For the current read-only agent scope, this is acceptable. If agent scope expands to write-enabled, implement explicit compensation logic for registration/cancellation workflows.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/registry/AbstractInstanceRegistry.java`, `eureka-core/src/main/java/com/netflix/eureka/cluster/PeerEurekaNode.java`

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: A `RateLimitingFilter` is implemented with a token bucket algorithm in `RateLimitingFilter.java`. It supports configurable burst size (`rateLimiter.burstSize`, default 10), average rate for registry fetches (`rateLimiter.registryFetchAverageRate`, default 500/s), and full fetch rate (`rateLimiter.fullFetchAverageRate`, default 100/s). It distinguishes privileged clients (standard Eureka clients and peer servers) from non-privileged clients. **However, rate limiting is disabled by default** (`rateLimiter.enabled` defaults to `false` in `DefaultEurekaServerConfig.java`), and the rate limiting filter mapping is **commented out** in `eureka-server/src/main/webapp/WEB-INF/web.xml`. When disabled, the filter still counts would-be throttled requests (`RATE_LIMITED_CANDIDATES`) but does not reject them.
- **Gap**: Rate limiting infrastructure exists but is not active. A runaway agent could generate unbounded request volume against the Eureka API.
- **Compensating Controls**:
  - Enable the built-in rate limiter by setting `eureka.rateLimiter.enabled=true` and uncommenting the filter mapping in web.xml.
  - Deploy an API Gateway with usage plans and throttling configured for agent identities.
- **Remediation Timeline**: 1–2 weeks (enable existing filter), 2–4 weeks (API Gateway approach)
- **Recommendation**: Enable the existing `RateLimitingFilter` immediately by setting `eureka.rateLimiter.enabled=true` in the server configuration and uncommenting the web.xml filter mapping. Long-term, implement API Gateway throttling with per-agent usage plans.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/RateLimitingFilter.java`, `eureka-core/src/main/java/com/netflix/eureka/DefaultEurekaServerConfig.java`, `eureka-server/src/main/webapp/WEB-INF/web.xml`

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI/Swagger, AsyncAPI, GraphQL schema, or Smithy model files exist in the repository. The API is defined entirely through Jersey JAX-RS annotations (`@Path`, `@GET`, `@POST`, `@PUT`, `@DELETE`, `@Produces`, `@Consumes`) in Java source files. The API is documented externally via the GitHub wiki.
- **Gap**: No machine-readable API specification available. Agent frameworks cannot auto-generate tool definitions; every integration requires manual tool authoring.
- **Compensating Controls**:
  - Generate OpenAPI spec from JAX-RS annotations using tools like `swagger-jaxrs` or `enunciate`.
  - Manually author an OpenAPI specification based on the existing resource classes.
- **Remediation Timeline**: 2–4 weeks
- **Recommendation**: Generate an OpenAPI 3.0 specification from the JAX-RS resource annotations. Integrate spec generation into the CI/CD pipeline to keep it current.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationsResource.java`, `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationResource.java`, `eureka-core/src/main/java/com/netflix/eureka/resources/InstanceResource.java`

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Error responses use HTTP status codes (400, 404, 500, 204) with plain-text string entities. For example, `ApplicationResource.addInstance()` returns `Response.status(400).entity("Missing instanceId").build()` and `Response.status(400).entity("Missing hostname").build()`. The `InstanceResource` methods return `Response.serverError().build()` for caught exceptions — a bare 500 with no body. There is no consistent error response structure with error codes, machine-readable error categories, or retryable indicators.
- **Gap**: Agents cannot distinguish retriable errors (timeout, rate limit) from terminal errors (invalid input, not found). A 500 with no body forces agents to guess.
- **Compensating Controls**:
  - Implement error mapping at the API Gateway layer that wraps Eureka responses into structured JSON error objects.
  - Agent tool implementations can map HTTP status codes to retry/terminal decisions as a workaround.
- **Remediation Timeline**: 4–8 weeks
- **Recommendation**: Implement a Jersey ExceptionMapper that converts all error responses to a structured JSON format with fields: `errorCode`, `message`, `retryable`.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationResource.java`, `eureka-core/src/main/java/com/netflix/eureka/resources/InstanceResource.java`

#### DATA-Q3: Selective Query Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The `GET /v2/apps` endpoint returns ALL registered applications in a single response with no pagination, filtering, or sorting parameters. The response can be large for registries with many instances. A delta endpoint (`GET /v2/apps/delta`) exists that returns only recently changed instances, reducing payload size. Individual application queries (`GET /v2/apps/{appId}`) and instance queries (`GET /v2/apps/{appId}/{instanceId}`) provide selective access. VIP-based queries (`GET /v2/vips/{vipAddress}`) add another filtering dimension. However, the primary registry fetch endpoint is unbounded.
- **Gap**: No pagination, filtering, or sorting on the main registry fetch endpoint. Agents retrieving the full registry may exhaust LLM context windows for large deployments.
- **Compensating Controls**:
  - Use the delta endpoint (`/apps/delta`) instead of full registry fetch to reduce payload size.
  - Use application-specific and VIP-specific endpoints for targeted queries.
- **Remediation Timeline**: 4–8 weeks
- **Recommendation**: For agent integration, prefer the delta endpoint and application-specific queries. Long-term, consider adding pagination parameters to the full registry fetch endpoint.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationsResource.java`

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The API is URL-versioned with `/{version}/apps/*` path pattern, supporting V1 and V2 via the `Version` enum in `Version.java`. JSON/XML serialization is defined via Jackson annotations on `InstanceInfo.java` with custom serializers in `EurekaJacksonCodec`. `CHANGELOG.md` exists but is empty. No schema registry, no breaking change detection tools (`buf breaking`, OpenAPI diff) in CI, and no consumer-driven contract tests (Pact) are present. The CI pipeline (`nebula-ci.yml`) runs `./gradlew build` but does not include any API contract validation.
- **Gap**: URL versioning exists but no automated breaking-change detection. Schema changes could silently break agent tool bindings.
- **Compensating Controls**:
  - Pin agent tools to a specific API version (V2) and monitor for Eureka releases that change response format.
  - Implement manual review of `InstanceInfo.java` changes as part of the release process.
- **Remediation Timeline**: 4–8 weeks
- **Recommendation**: Add OpenAPI spec generation to CI and implement breaking-change detection between releases using tools like `openapi-diff`.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/Version.java`, `eureka-client/src/main/java/com/netflix/appinfo/InstanceInfo.java`, `.github/workflows/nebula-ci.yml`, `CHANGELOG.md`

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No distributed tracing framework is integrated — no OpenTelemetry, X-Ray, Zipkin, or `traceparent` header propagation. Logging uses SLF4J with log4j backend (configured in `eureka-server/src/main/resources/log4j.properties`), producing unstructured text logs. No correlation IDs or request IDs are propagated through the request processing pipeline. The server logs operational events (registrations, renewals, cancellations) with app name and instance ID but without structured JSON format or trace context.
- **Gap**: Cannot reconstruct the full request path of an agent-initiated call through the Eureka server. Failed requests cannot be debugged via distributed tracing.
- **Compensating Controls**:
  - Add a servlet filter that generates and propagates request IDs, logging them in a structured format.
  - Deploy a service mesh sidecar (e.g., Envoy) that provides trace context propagation.
- **Remediation Timeline**: 4–8 weeks
- **Recommendation**: Integrate OpenTelemetry Java agent or add manual instrumentation for trace context propagation. Switch to structured JSON logging.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/ServerRequestAuthFilter.java`, `eureka-core/src/main/java/com/netflix/eureka/util/EurekaMonitors.java`

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No alerting thresholds are configured. `EurekaMonitors` provides Netflix Servo counters for all major operations (RENEW, CANCEL, GET_ALL, REGISTER, EXPIRED, RATE_LIMITED, etc.), but these are metrics emission only — no CloudWatch alarms, PagerDuty, OpsGenie, or anomaly detection is configured. No SLO-based alerting exists. The self-preservation mode uses renewal rate thresholds (`renewalPercentThreshold` default 0.85) to detect mass failures, but this is a safety mechanism, not an alerting system.
- **Gap**: No alerting on error rates or latency for the APIs agents will consume. Service degradation would not trigger notifications.
- **Compensating Controls**:
  - Deploy Servo metrics to a monitoring backend (e.g., Atlas, CloudWatch, Prometheus) and configure alerting externally.
  - API Gateway monitoring with CloudWatch alarms for 5xx rates and p99 latency.
- **Remediation Timeline**: 2–4 weeks
- **Recommendation**: Export Servo metrics to a monitoring backend and configure alerting thresholds for error rates (CANCEL_NOT_FOUND, RENEW_NOT_FOUND) and rate limiting triggers.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/util/EurekaMonitors.java`

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No separate staging or sandbox environment configuration exists. No Docker Compose for local testing. The `eureka-examples` module provides `ExampleEurekaService.java` and `ExampleEurekaClient.java` for demonstration purposes, and integration tests (`EurekaClientServerRestIntegrationTest.java`) spin up an embedded Jetty server for testing. However, there is no production-equivalent staging environment with realistic data shape for agent testing.
- **Gap**: No sandbox or staging environment for agents to test against realistic conditions.
- **Compensating Controls**:
  - Use the embedded Jetty test server approach to create a local staging instance for agent testing.
  - Deploy a dedicated Eureka instance in a non-production environment with synthetic service registrations.
- **Remediation Timeline**: 2–4 weeks
- **Recommendation**: Create a Docker Compose configuration or Kubernetes manifest for spinning up a local Eureka cluster with synthetic registrations for agent testing.
- **Evidence**: `eureka-examples/`, `eureka-server/src/test/java/com/netflix/eureka/resources/EurekaClientServerRestIntegrationTest.java`

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No IaC files found in the repository — no Terraform, CloudFormation, CDK, Helm, Kustomize, or Ansible definitions. Eureka is published as a Java WAR/library to Maven Central; deployment infrastructure is consumer-owned. There are no API Gateway definitions, IAM role definitions, or network configuration files. The GitHub Actions CI workflows (`nebula-ci.yml`, `nebula-publish.yml`, `nebula-snapshot.yml`) manage build and publish only.
- **Gap**: No infrastructure-as-code for the agent-facing API surface. Consumers must define their own deployment IaC, which is outside this repository's scope.
- **Compensating Controls**:
  - Consumers deploying Eureka should define IaC for the deployment infrastructure (API Gateway, IAM, networking).
  - Provide reference IaC templates in the repository for recommended deployment configurations.
- **Remediation Timeline**: 4–8 weeks
- **Recommendation**: Add reference Terraform or CloudFormation templates for deploying Eureka server with API Gateway, IAM roles, and network configuration.
- **Evidence**: No IaC files found. `.github/workflows/nebula-ci.yml`, `.github/workflows/nebula-publish.yml`, `.github/workflows/nebula-snapshot.yml`

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: CI/CD exists via GitHub Actions. `nebula-ci.yml` runs `./gradlew build` on every push and pull request (Java 8, Zulu). `nebula-publish.yml` publishes releases and candidates to Maven Central. `nebula-snapshot.yml` publishes snapshots from master. The build includes unit and integration tests, but there are no API contract tests (Pact), no OpenAPI spec validation, and no breaking change detection in the CI pipeline.
- **Gap**: API contract changes are not automatically detected. A schema change in `InstanceInfo` could break agent tool bindings without CI catching it.
- **Compensating Controls**:
  - Add OpenAPI spec generation to the CI pipeline and compare against a baseline spec on every PR.
  - Implement consumer-driven contract tests if agent tools have known consumers.
- **Remediation Timeline**: 4–8 weeks
- **Recommendation**: Integrate API contract testing into the CI pipeline. Generate OpenAPI specs from JAX-RS annotations and run `openapi-diff` against the previous release.
- **Evidence**: `.github/workflows/nebula-ci.yml`, `.github/workflows/nebula-publish.yml`, `.github/workflows/nebula-snapshot.yml`

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No blue/green deployment, CodeDeploy, Helm rollback, canary deployment, or feature flag configuration exists. Eureka is published as a library/WAR to Maven Central — rollback for consumers is via Maven/Gradle version pinning (e.g., reverting from `2.0.1` to `2.0.0` in their dependency declaration). No deployment-level rollback mechanisms exist within this repository.
- **Gap**: No automated deployment rollback capability. If a new Eureka version breaks agent-facing APIs, recovery requires consumer-side dependency version changes.
- **Compensating Controls**:
  - Consumers should implement deployment rollback (blue/green, canary) in their own infrastructure.
  - Maven version pinning allows reverting to known-good Eureka versions.
- **Remediation Timeline**: 4–8 weeks (for consumers to implement)
- **Recommendation**: Add reference deployment configurations that include rollback capabilities. Document recommended rollback procedures for Eureka server deployments.
- **Evidence**: `.github/workflows/nebula-publish.yml`, `build.gradle`

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: 110 test files exist across all modules. `EurekaClientServerRestIntegrationTest.java` (297 lines) tests REST layer client/server communication by spinning up a fully configured Jersey container in an embedded Jetty server. Tests cover registration, heartbeat, status update, cancellation, and batch replication operations. Unit tests use JUnit 4, Mockito, and WireMock. However, there is no systematic API test suite that validates all endpoints' input handling, output format, error responses, and edge cases. No contract tests or API-specific test suites run in CI.
- **Gap**: Test coverage exists for core operations but is not comprehensive for all API endpoints and error scenarios. No dedicated API contract test suite.
- **Compensating Controls**:
  - The existing integration test (`EurekaClientServerRestIntegrationTest`) covers the most critical paths.
  - Add API-specific test cases for error handling, content negotiation, and edge cases.
- **Remediation Timeline**: 4–8 weeks
- **Recommendation**: Expand the integration test suite to cover all REST endpoints with positive, negative, and edge-case scenarios. Add contract tests that validate response schemas.
- **Evidence**: `eureka-server/src/test/java/com/netflix/eureka/resources/EurekaClientServerRestIntegrationTest.java`, `eureka-server/build.gradle`

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO
- **Finding**: Eureka exposes a well-defined REST API via Jersey JAX-RS resource classes with clear `@Path`, `@GET`, `@POST`, `@PUT`, `@DELETE` annotations. Endpoints include: `/{version}/apps` (all applications), `/{version}/apps/{appId}` (specific application), `/{version}/apps/{appId}/{instanceId}` (specific instance), `/{version}/status` (server status), `/{version}/peerreplication/batch` (peer replication), `/{version}/vips/{vipAddress}` (VIP lookup), `/{version}/svips/{svipAddress}` (secure VIP lookup). The API supports JSON and XML content negotiation via `@Produces({"application/xml", "application/json"})`. External documentation exists via the GitHub wiki.
- **Implication**: Agents can bind to a stable REST API surface. Tool definitions can be authored manually based on the well-structured JAX-RS resource classes.
- **Recommendation**: Generate and maintain an OpenAPI specification to enable automatic tool generation (see API-Q2).
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationsResource.java`, `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationResource.java`, `eureka-core/src/main/java/com/netflix/eureka/resources/InstanceResource.java`, `eureka-core/src/main/java/com/netflix/eureka/resources/StatusResource.java`, `eureka-core/src/main/java/com/netflix/eureka/resources/PeerReplicationResource.java`

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Registration (POST `/v2/apps/{appId}`) uses the instance ID as a natural key — re-registering the same instance updates the existing entry rather than creating a duplicate (via `registry.get(registrant.getId())` check in `AbstractInstanceRegistry.register()`). Renewals (PUT) are inherently idempotent. Status updates (PUT) are also idempotent. No explicit idempotency key headers are supported, but the natural key behavior provides functional idempotency.
- **Implication**: For read-only agent scope, idempotency of write operations is informational only. If scope expands to write-enabled, the natural-key idempotency of registration is adequate.
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationResource.java`, `eureka-core/src/main/java/com/netflix/eureka/registry/AbstractInstanceRegistry.java`

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: The API supports both JSON and XML response formats via content negotiation. `@Produces({"application/xml", "application/json"})` annotations are present on all resource classes. JSON serialization uses Jackson with custom serializers defined in `EurekaJacksonCodec`. XML serialization uses XStream and JAXB. The `Accept` header determines the response format, with XML as the default when no JSON preference is specified. GZIP compression is supported via the `Accept-Encoding: gzip` header.
- **Implication**: Agents should use `Accept: application/json` for optimal LLM consumption. JSON responses are well-structured with named fields mapping to `InstanceInfo` properties.
- **Recommendation**: Ensure agent tool configurations specify `Accept: application/json` header.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationsResource.java`, `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationResource.java`

### API-Q7: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: No webhook, SNS, EventBridge, Kafka, or external event emission mechanism exists. State changes (registrations, cancellations, status updates) are communicated only via the peer replication protocol (`PeerEurekaNode` → `ReplicationTaskProcessor` → batch POST to `/{version}/peerreplication/batch`). The delta endpoint (`/apps/delta`) provides a polling-based mechanism for clients to detect recent changes, with a configurable retention window (`retentionTimeInMSInDeltaQueue`, default 3 minutes).
- **Implication**: Agents must poll the delta endpoint to detect registry changes. Real-time event-driven agent workflows are not supported.
- **Recommendation**: For agent use cases requiring real-time notifications, consider adding a CDC (Change Data Capture) mechanism or EventBridge integration on top of the existing `recentlyChangedQueue`.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/cluster/PeerEurekaNode.java`, `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationsResource.java`

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: The `RateLimitingFilter` returns HTTP 503 (Service Unavailable) when rate limiting triggers, with no rate limit headers (`X-RateLimit-Remaining`, `Retry-After`, `X-RateLimit-Limit`). The rate limiter configuration (burst size, average rate) is not documented in any external specification. Rate limit parameters are configurable via Archaius properties (`eureka.rateLimiter.burstSize`, `eureka.rateLimiter.registryFetchAverageRate`, `eureka.rateLimiter.fullFetchAverageRate`).
- **Implication**: Agents receiving 503 responses cannot self-throttle effectively — they have no signal for when to retry or how much capacity remains.
- **Recommendation**: Add `Retry-After` and `X-RateLimit-Remaining` headers to the 503 response in `RateLimitingFilter`. Document rate limit thresholds in the API specification.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/RateLimitingFilter.java`, `eureka-core/src/main/java/com/netflix/eureka/DefaultEurekaServerConfig.java`

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: INFO
- **Finding**: No JWT parsing middleware, OAuth token exchange, or user context propagation exists. Peer replication requests are distinguished by the `x-netflix-discovery-replication` header, but this is not validated and carries no identity context. The `DiscoveryIdentity` headers carry client identification (name, version, ID) but these are not used for delegation or on-behalf-of flows. The server does not distinguish between an agent acting under its own identity vs. acting on behalf of a user.
- **Implication**: Identity propagation will need to be implemented at the API Gateway or service mesh layer if agent-on-behalf-of-user scenarios are required.
- **Recommendation**: For service discovery use cases, identity propagation is less critical since agents typically query the registry under their own identity. No immediate action needed for read-only scope.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/ServerRequestAuthFilter.java`, `eureka-core/src/main/java/com/netflix/eureka/cluster/PeerEurekaNode.java`

### AUTH-Q5: Credential Management

- **Severity**: INFO
- **Finding**: AWS access keys are read from Archaius-managed properties (`getAWSAccessId()`, `getAWSSecretKey()` in `DefaultEurekaServerConfig.java`) with no Secrets Manager or Vault integration. The remote region trust store password defaults to `"changeit"` (`getRemoteRegionTrustStorePassword()`). CI/CD workflows use GitHub Secrets for signing keys and repository credentials (`ORG_SIGNING_KEY`, `ORG_SIGNING_PASSWORD`, `ORG_NETFLIXOSS_USERNAME`, `ORG_NETFLIXOSS_PASSWORD`, `ORG_SONATYPE_USERNAME`, `ORG_SONATYPE_PASSWORD`). No hardcoded credentials found in source code — AWS keys are read from configuration at runtime.
- **Implication**: AWS credential management relies on the deployment platform (properties files, environment variables). Consumers should integrate with AWS Secrets Manager or HashiCorp Vault for production deployments.
- **Recommendation**: Document recommended credential management approach for production deployments. Replace the default trust store password in production configurations.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/DefaultEurekaServerConfig.java`, `.github/workflows/nebula-publish.yml`

### STATE-Q2: Queryable Current State

- **Severity**: INFO
- **Finding**: The registry state is fully queryable via REST endpoints: `GET /v2/apps` (all applications), `GET /v2/apps/{appId}` (specific application with all instances), `GET /v2/apps/{appId}/{instanceId}` (specific instance), `GET /v2/vips/{vipAddress}` (instances by VIP), `GET /v2/svips/{svipAddress}` (instances by secure VIP), `GET /v2/apps/delta` (recent changes). Instance status fields include `status`, `overriddenStatus`, `lastDirtyTimestamp`, `lastUpdatedTimestamp`, and lease information (`registrationTimestamp`, `lastRenewalTimestamp`, `evictionTimestamp`).
- **Implication**: Agents can inspect current registry state before taking action — a positive finding for state management.
- **Recommendation**: No action needed. The queryable state surface is well-suited for agent consumption.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationsResource.java`, `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationResource.java`, `eureka-core/src/main/java/com/netflix/eureka/resources/InstanceResource.java`

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: `AbstractInstanceRegistry` uses `ReentrantReadWriteLock` for registry operations — read lock for registrations/cancellations (allowing concurrent reads), write lock for delta computations. `ConcurrentHashMap` provides thread-safe access to the registry data structure. Peer replication conflict resolution uses `lastDirtyTimestamp` comparison — the entry with the higher dirty timestamp wins.
- **Implication**: Concurrency controls are well-implemented for the server's internal operations. For read-only agent access, these controls are informational only.
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/registry/AbstractInstanceRegistry.java`

### STATE-Q4: Circuit Breakers and Resilience

- **Severity**: INFO
- **Finding**: The eureka-server calls peer nodes for replication and optionally calls AWS services (ASG API, Route53). Peer replication uses `TaskDispatchers` with batching, retry sleep times (`RETRY_SLEEP_TIME_MS = 100ms`), and server unavailable sleep times (`SERVER_UNAVAILABLE_SLEEP_TIME_MS = 1000ms`). `RetryableEurekaHttpClient` implements retry with quarantine for failed servers. Configurable timeouts exist for peer connections (`peerNodeConnectTimeoutMs = 1000ms`, `peerNodeReadTimeoutMs = 5000ms`). However, no explicit circuit breaker pattern (Resilience4j, Hystrix) is implemented — retry is immediate with sleep, not circuit-breaker gated.
- **Implication**: Retry and timeout mechanisms exist but no formal circuit breaker prevents cascading failures. For read-only agent access, this is low risk since agents don't trigger peer replication.
- **Recommendation**: Consider adding circuit breaker patterns for peer replication and AWS service calls if the system is on the critical path.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/cluster/PeerEurekaNode.java`, `eureka-client/src/main/java/com/netflix/discovery/shared/transport/decorator/RetryableEurekaHttpClient.java`, `eureka-core/src/main/java/com/netflix/eureka/DefaultEurekaServerConfig.java`

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits exist for agent-initiated actions (no max records per run, max spend per hour, or max delete operations per session). The self-preservation mode (`shouldEnableSelfPreservation`, default true) prevents mass eviction when renewal rates drop below `renewalPercentThreshold` (default 85%), which acts as a natural blast radius limiter for the eviction process. The replication pool has a configurable max element count (`maxElementsInPeerReplicationPool`, default 10000).
- **Implication**: For read-only agent scope, transaction limits are not relevant. If scope expands to write-enabled, configurable limits should be implemented.
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/DefaultEurekaServerConfig.java`, `eureka-core/src/main/java/com/netflix/eureka/registry/AbstractInstanceRegistry.java`

### STATE-Q7: Infrastructure Capacity for Agent Traffic

- **Severity**: INFO
- **Finding**: No load test configurations, auto-scaling policies, or capacity planning documentation found. However, the Eureka server includes several capacity-related mechanisms: configurable response cache with read-only cache (`shouldUseReadOnlyResponseCache`, default true) and auto-expiration (`responseCacheAutoExpirationInSeconds`, default 180s), configurable peer connection pools (`peerNodeTotalConnections` default 1000, `peerNodeTotalConnectionsPerHost` default 500), and the rate limiting infrastructure (disabled by default). Self-preservation mode prevents cascading failures under load.
- **Implication**: The response cache is a key performance optimization for read-heavy agent traffic patterns. Agents repeatedly querying `/v2/apps` will be served from cache, reducing backend load.
- **Recommendation**: Enable and tune the rate limiter for agent traffic. Configure response cache TTL appropriately for agent polling frequency.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/DefaultEurekaServerConfig.java`, `eureka-core/src/main/java/com/netflix/eureka/registry/ResponseCacheImpl.java`

### DATA-Q1: Sensitive Data Classification

- **Severity**: INFO
- **Finding**: Stage A scope gate — Eureka stores service instance metadata: hostnames, IP addresses, port numbers, application names, VIP addresses, AWS metadata (instance IDs, AMI IDs, availability zones), health check URLs, and arbitrary key-value metadata. This is infrastructure service discovery data, not PII/PHI/financial data/credentials. IP addresses and AWS instance IDs are infrastructure-sensitive but not regulated data in the PII/PHI/financial sense. `has_persistent_data_store` is true but the data is service registration metadata, not user data.
- **Implication**: Stage A = No (not a data-handling target for regulated data). Data classification controls are not required for this infrastructure metadata.
- **Recommendation**: No action needed. If the metadata map is used to store sensitive data by consumers, document that field-level classification is the consumer's responsibility.
- **Evidence**: `eureka-client/src/main/java/com/netflix/appinfo/InstanceInfo.java`

### DATA-Q2: Data Residency and Sovereignty ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY, but calibrated to INFO due to data nature
- **Finding**: Service registration data contains infrastructure metadata (IP addresses, hostnames, AWS availability zone/region). No GDPR, LGPD, or HIPAA-regulated data is stored. AWS region awareness is built in via `eureka.region` configuration and remote region support (`getRemoteRegionUrlsWithName()`). The data is infrastructure metadata with no residency constraints — IP addresses and instance IDs are not subject to data sovereignty regulations.
- **Implication**: Data residency is not a concern for this service discovery metadata. An agent transmitting registry data to an LLM in another region does not create a legal violation.
- **Recommendation**: No action needed. If consumers store sensitive metadata in the instance metadata map, they should handle residency controls independently.
- **Evidence**: `eureka-server/src/main/resources/eureka-client.properties`, `eureka-core/src/main/java/com/netflix/eureka/DefaultEurekaServerConfig.java`

### DATA-Q4: System of Record Designations

- **Severity**: INFO
- **Finding**: Eureka IS the authoritative system of record for service instance registrations within its deployment scope. Peer replication resolves conflicts via `lastDirtyTimestamp` comparison — the entry with the higher timestamp wins. Self-preservation mode prevents the registry from being cleared during network partitions, prioritizing availability over consistency. The `syncInstancesIfTimestampDiffers()` method in `PeerEurekaNode` resolves peer-to-peer conflicts explicitly.
- **Implication**: Positive finding — Eureka has clear system-of-record semantics for service discovery data with explicit conflict resolution.
- **Recommendation**: No action needed. Document the conflict resolution semantics for agent consumers.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/cluster/PeerEurekaNode.java`, `eureka-core/src/main/java/com/netflix/eureka/registry/AbstractInstanceRegistry.java`

### DATA-Q5: Temporal Metadata and Freshness

- **Severity**: INFO
- **Finding**: `InstanceInfo` includes comprehensive temporal metadata: `lastDirtyTimestamp` (when the instance was last modified), `lastUpdatedTimestamp` (when the registry entry was last updated). `LeaseInfo` provides: `registrationTimestamp`, `lastRenewalTimestamp` (last heartbeat), `serviceUpTimestamp`, and `evictionTimestamp`. The `ResponseCache` has a configurable TTL (`responseCacheAutoExpirationInSeconds` default 180s) and update interval (`responseCacheUpdateIntervalMs` default 30s). All timestamps use `System.currentTimeMillis()` (UTC epoch milliseconds). No explicit `Cache-Control` or `X-Data-Age` headers are returned.
- **Implication**: Positive finding — temporal metadata is rich and well-structured. Agents can reason about data freshness using timestamps. The response cache introduces potential staleness (up to 30s for the read-write cache, plus read-only cache refresh interval).
- **Recommendation**: Document the response cache TTL and staleness characteristics for agent consumers. Consider adding `Cache-Control` headers to responses.
- **Evidence**: `eureka-client/src/main/java/com/netflix/appinfo/InstanceInfo.java`, `eureka-client/src/main/java/com/netflix/appinfo/LeaseInfo.java`, `eureka-core/src/main/java/com/netflix/eureka/DefaultEurekaServerConfig.java`

### DATA-Q6: PII Redaction in Logs

- **Severity**: INFO
- **Finding**: `has_logging_of_user_data` is false. Eureka logs infrastructure metadata only: application names, instance IDs, hostnames, IP addresses, status values, and replication events. The `ServerRequestAuthFilter` logs client identity headers (`DiscoveryIdentity-Name`, `DiscoveryIdentity-Version`) via metrics counters, not as log entries. Operational logs (e.g., "Registered instance {}/{} with status {}") contain infrastructure identifiers, not user PII.
- **Implication**: PII-in-logs risk is not applicable. The system does not handle user data that could leak into logs.
- **Recommendation**: No action needed.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/ServerRequestAuthFilter.java`, `eureka-core/src/main/java/com/netflix/eureka/registry/AbstractInstanceRegistry.java`

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No formal data quality scores or completeness metrics exist. Self-preservation mode tracks the ratio of renewals received vs. expected (`getNumOfRenewsInLastMin()` / `numberOfRenewsPerMinThreshold`), which serves as a proxy for registry data quality — a drop in renewals indicates stale or incomplete data. The `MeasuredRate` class tracks renewal rates per minute. No data profiling, null rate monitoring, or duplicate detection is present.
- **Implication**: Self-preservation mode provides indirect data quality signaling. Agents should monitor the self-preservation status endpoint to assess registry reliability.
- **Recommendation**: Expose the renewal rate ratio as a health signal that agents can check before relying on registry data.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/registry/AbstractInstanceRegistry.java`, `eureka-core/src/main/java/com/netflix/eureka/util/MeasuredRate.java`

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Field names in `InstanceInfo` are generally semantically meaningful: `hostName`, `ipAddr`, `appName`, `status`, `dataCenterInfo`, `leaseInfo`, `lastDirtyTimestamp`, `lastUpdatedTimestamp`, `homePageUrl`, `statusPageUrl`, `healthCheckUrl`, `metadata`, `actionType`. Minor legacy abbreviations exist (`vipAddress`, `secureVipAddress`, `ipAddr`, `sid`) but are well-documented via Javadoc and widely understood in the Eureka ecosystem.
- **Implication**: Positive finding — field names are interpretable by LLM-based reasoning without requiring a data dictionary lookup.
- **Recommendation**: No action needed. The naming conventions are adequate for agent consumption.
- **Evidence**: `eureka-client/src/main/java/com/netflix/appinfo/InstanceInfo.java`

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No formal data catalog (AWS Glue, Collibra, Alation, DataHub) exists. The `InstanceInfo` class itself serves as a de facto schema definition with Jackson annotations documenting the serialization format. The GitHub wiki provides external documentation. No metadata layer or schema registry is present.
- **Implication**: Agent tool builders must reference `InstanceInfo.java` and the GitHub wiki for data model understanding. No automated schema discovery is available.
- **Recommendation**: Consider publishing the `InstanceInfo` schema as part of an OpenAPI specification to improve discoverability.
- **Evidence**: `eureka-client/src/main/java/com/netflix/appinfo/InstanceInfo.java`, `README.md`

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: `EurekaMonitors` tracks operational counters via Netflix Servo: `REGISTER` (registrations), `RENEW` (heartbeats), `CANCEL` (cancellations), `EXPIRED` (lease expirations), `RATE_LIMITED` (throttled requests), `GET_ALL` (full registry fetches), `GET_ALL_DELTA` (delta fetches), `REJECTED_REPLICATIONS`, `FAILED_REPLICATIONS`. Self-preservation mode monitors renewal rates. For a service discovery server, these operational metrics ARE the business metrics — registration success rate, heartbeat health, and query throughput directly measure business outcome.
- **Implication**: Positive finding — the existing Servo metrics provide meaningful signals for agent-initiated request outcomes. Export to a monitoring backend for visibility.
- **Recommendation**: Ensure Servo metrics are exported to a durable metrics backend (Atlas, CloudWatch, Prometheus) and create dashboards tracking agent-specific query patterns.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/util/EurekaMonitors.java`

### ENG-Q5: Encryption at Rest for Agent-Accessible Data

- **Severity**: INFO
- **Finding**: The Eureka registry is stored entirely in-memory (`ConcurrentHashMap` in JVM heap) with no persistence to disk. No KMS, encryption-at-rest configuration, or encrypted storage exists because there is no persistent storage. The data (service instance metadata) is transient — it is rebuilt from client registrations after server restart. The response cache (`ResponseCacheImpl`) also uses in-memory storage (Guava cache).
- **Implication**: In-memory-only data stores have different security characteristics than persistent stores. Encryption at rest is not applicable for JVM heap data. JVM memory security relies on OS-level access controls.
- **Recommendation**: No action needed. If consumers deploy Eureka with persistent write-ahead logs or database backing, encryption at rest should be configured at that layer.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/registry/AbstractInstanceRegistry.java`, `eureka-core/src/main/java/com/netflix/eureka/registry/ResponseCacheImpl.java`

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: Eureka exposes a documented REST API via Jersey JAX-RS with endpoints at `/{version}/apps/*`, `/{version}/status`, `/{version}/peerreplication/batch`, `/{version}/vips/*`, `/{version}/svips/*`. API supports JSON and XML content negotiation. External wiki documentation available.
- **Gap**: No formal API specification file (OpenAPI/Swagger), but REST API surface is well-defined in code.
- **Recommendation**: Generate OpenAPI specification from JAX-RS annotations.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationsResource.java`, `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationResource.java`, `eureka-core/src/main/java/com/netflix/eureka/resources/InstanceResource.java`, `eureka-core/src/main/java/com/netflix/eureka/resources/StatusResource.java`, `eureka-core/src/main/java/com/netflix/eureka/resources/PeerReplicationResource.java`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, GraphQL schema, or Smithy specification files found. API defined through JAX-RS annotations in Java source.
- **Gap**: No machine-readable API specification for automated tool generation.
- **Recommendation**: Generate OpenAPI 3.0 specification from JAX-RS annotations and integrate into CI.
- **Evidence**: No API spec files found in repository.

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: Error responses use HTTP status codes with plain-text entities (e.g., `"Missing instanceId"`). No structured error JSON with error codes or retryable indicators.
- **Gap**: Agents cannot distinguish retriable from terminal errors programmatically.
- **Recommendation**: Implement Jersey ExceptionMapper producing structured JSON error responses.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationResource.java`, `eureka-core/src/main/java/com/netflix/eureka/resources/InstanceResource.java`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Registration uses instance ID as natural key providing functional idempotency. Renewals and status updates are inherently idempotent PUT operations.
- **Gap**: No explicit idempotency key headers, but natural key behavior is adequate.
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationResource.java`, `eureka-core/src/main/java/com/netflix/eureka/registry/AbstractInstanceRegistry.java`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: JSON and XML supported via `@Produces` annotations and content negotiation. Jackson-based JSON serialization with custom codecs. GZIP compression supported.
- **Gap**: N/A
- **Recommendation**: Agents should specify `Accept: application/json` header.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationsResource.java`

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has operations >30s OR long-running workflows. Eureka operations are sub-second; no long-running workflows detected.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: No webhook, SNS, EventBridge, or Kafka integration. State changes communicated via peer replication protocol only. Delta endpoint provides polling-based change detection.
- **Gap**: No event-driven integration surface for agents.
- **Recommendation**: Consider EventBridge integration for real-time agent workflows.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/cluster/PeerEurekaNode.java`, `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationsResource.java`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: RateLimitingFilter returns HTTP 503 with no rate limit headers. Rate limit parameters undocumented externally.
- **Gap**: No `Retry-After` or `X-RateLimit-Remaining` headers for agent self-throttling.
- **Recommendation**: Add rate limit headers to 503 responses.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/RateLimitingFilter.java`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: `ServerRequestAuthFilter` only logs identity headers — no authentication enforcement. No OAuth2, API key validation, mTLS, or Cognito integration.
- **Gap**: All endpoints completely unauthenticated. Agent identity cannot be established.
- **Recommendation**: Implement API Gateway with OAuth2 client credentials or API key authentication.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/ServerRequestAuthFilter.java`, `eureka-client/src/main/java/com/netflix/appinfo/AbstractEurekaIdentity.java`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: No authorization model. All clients have identical unrestricted access.
- **Gap**: Cannot grant agent read-only access without inheriting broader privileges.
- **Recommendation**: Deploy API Gateway with route-level access control.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/ServerRequestAuthFilter.java`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization. Any client can perform any operation. `shouldAllowAccess()` is a readiness check, not authorization.
- **Gap**: Cannot restrict agent to read-only operations at the application layer.
- **Recommendation**: Implement method-level authorization at API Gateway.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationsResource.java`, `eureka-core/src/main/java/com/netflix/eureka/resources/InstanceResource.java`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: No JWT parsing, OAuth token exchange, or user context propagation. Peer replication header (`x-netflix-discovery-replication`) is not an identity mechanism.
- **Gap**: No identity propagation or delegation support.
- **Recommendation**: Implement at API Gateway layer if needed for on-behalf-of scenarios.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/ServerRequestAuthFilter.java`

#### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: AWS credentials read from Archaius properties. Trust store password defaults to "changeit". CI/CD uses GitHub Secrets. No hardcoded credentials in source code.
- **Gap**: No Secrets Manager or Vault integration. Default trust store password is insecure.
- **Recommendation**: Integrate with AWS Secrets Manager for production deployments.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/DefaultEurekaServerConfig.java`, `.github/workflows/nebula-publish.yml`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: `ServerRequestAuthFilter` uses Servo DynamicCounter for metrics, not immutable audit logs. No CloudTrail, no immutable log storage.
- **Gap**: No immutable audit trail for API operations.
- **Recommendation**: Deploy API Gateway with CloudWatch access logging and CloudTrail.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/ServerRequestAuthFilter.java`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: No mechanism to suspend individual client identities. `rateLimiterPrivilegedClients` is an allowlist for rate limit exemption, not identity suspension.
- **Gap**: Cannot revoke a misbehaving agent without affecting all clients.
- **Recommendation**: Implement API key revocation at API Gateway layer.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/RateLimitingFilter.java`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No saga patterns, compensating transactions, or explicit undo endpoints. Peer replication uses eventual consistency via lastDirtyTimestamp. Self-preservation prevents mass eviction.
- **Gap**: No compensation or rollback capability.
- **Recommendation**: Acceptable for read-only scope. Implement compensation for write-enabled expansion.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/registry/AbstractInstanceRegistry.java`

#### STATE-Q2: Queryable Current State
- **Severity**: INFO
- **Finding**: Full registry state queryable via GET endpoints: `/apps`, `/apps/{appId}`, `/apps/{appId}/{instanceId}`, `/vips/{vipAddress}`, `/apps/delta`. Rich status and timestamp fields.
- **Gap**: N/A — positive finding.
- **Recommendation**: No action needed. Well-suited for agent consumption.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationsResource.java`

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: `ReentrantReadWriteLock` and `ConcurrentHashMap` provide robust concurrency controls. Peer conflict resolution via lastDirtyTimestamp.
- **Gap**: N/A — positive finding for internal operations.
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/registry/AbstractInstanceRegistry.java`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: INFO
- **Finding**: RetryableEurekaHttpClient implements retry with quarantine. TaskDispatchers provide batching and retry for peer replication. Configurable timeouts. No formal circuit breaker pattern (Resilience4j/Hystrix).
- **Gap**: Retry and timeout exist but no circuit breaker prevents cascading failures.
- **Recommendation**: Consider adding circuit breakers for peer replication calls.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/cluster/PeerEurekaNode.java`, `eureka-client/src/main/java/com/netflix/discovery/shared/transport/decorator/RetryableEurekaHttpClient.java`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: Token bucket `RateLimitingFilter` implemented but disabled by default (`rateLimiter.enabled=false`). Filter mapping commented out in web.xml.
- **Gap**: Rate limiting infrastructure exists but is not active.
- **Recommendation**: Enable the existing rate limiter immediately.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/RateLimitingFilter.java`, `eureka-server/src/main/webapp/WEB-INF/web.xml`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits. Self-preservation mode provides natural blast radius limiting for evictions.
- **Gap**: No agent-specific transaction limits.
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/DefaultEurekaServerConfig.java`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: INFO
- **Finding**: No load tests or auto-scaling. Response cache with read-only tier. Configurable connection pools. Self-preservation mode.
- **Gap**: No capacity planning for agent traffic patterns.
- **Recommendation**: Tune response cache and enable rate limiter for agent traffic.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/DefaultEurekaServerConfig.java`

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled. Since agent_scope is read-only, this question is not triggered.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled. Since agent_scope is read-only, this question is not triggered.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: No staging/sandbox configuration. `eureka-examples` module and integration tests provide basic testing capability but not production-equivalent environments.
- **Gap**: No sandbox for agent testing.
- **Recommendation**: Create Docker Compose for local Eureka cluster with synthetic registrations.
- **Evidence**: `eureka-examples/`, `eureka-server/src/test/java/com/netflix/eureka/resources/EurekaClientServerRestIntegrationTest.java`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO
- **Finding**: Stage A = No. Eureka stores infrastructure metadata (hostnames, IPs, ports, app names, AWS metadata), not PII/PHI/financial data.
- **Gap**: N/A — not a data-handling target for regulated data.
- **Recommendation**: No action needed.
- **Evidence**: `eureka-client/src/main/java/com/netflix/appinfo/InstanceInfo.java`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — calibrated to INFO due to infrastructure-only data nature
- **Finding**: Infrastructure metadata with no residency constraints. AWS region awareness built in. No regulated data stored.
- **Gap**: N/A — data residency not applicable for infrastructure metadata.
- **Recommendation**: No action needed.
- **Evidence**: `eureka-server/src/main/resources/eureka-client.properties`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK-QUALITY
- **Finding**: `GET /v2/apps` returns all applications with no pagination. Delta endpoint and application-specific endpoints provide partial selectivity.
- **Gap**: No pagination/filtering on main registry endpoint.
- **Recommendation**: Use delta and application-specific endpoints for agent integration.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationsResource.java`

#### DATA-Q4: System of Record Designations
- **Severity**: INFO
- **Finding**: Eureka IS the system of record for service registrations. Peer conflict resolution via lastDirtyTimestamp.
- **Gap**: N/A — positive finding.
- **Recommendation**: Document conflict resolution semantics for agent consumers.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/cluster/PeerEurekaNode.java`

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: INFO
- **Finding**: Rich temporal metadata: lastDirtyTimestamp, lastUpdatedTimestamp, LeaseInfo timestamps. Response cache TTL documented in configuration.
- **Gap**: No Cache-Control headers on responses.
- **Recommendation**: Add Cache-Control headers to responses.
- **Evidence**: `eureka-client/src/main/java/com/netflix/appinfo/InstanceInfo.java`, `eureka-client/src/main/java/com/netflix/appinfo/LeaseInfo.java`

#### DATA-Q6: PII Redaction in Logs
- **Severity**: INFO
- **Finding**: `has_logging_of_user_data` is false. Logs contain infrastructure metadata only. No user PII in logs.
- **Gap**: N/A — PII risk not applicable.
- **Recommendation**: No action needed.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/ServerRequestAuthFilter.java`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: Self-preservation mode tracks renewal rates as a proxy for data quality. No formal quality metrics.
- **Gap**: No explicit data quality scoring.
- **Recommendation**: Expose renewal rate ratio as health signal for agents.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/registry/AbstractInstanceRegistry.java`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: URL versioning (V1/V2). Jackson-annotated serialization. Empty CHANGELOG.md. No schema registry or breaking-change detection in CI.
- **Gap**: No automated breaking-change detection.
- **Recommendation**: Add OpenAPI spec generation and diff to CI pipeline.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/Version.java`, `eureka-client/src/main/java/com/netflix/appinfo/InstanceInfo.java`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Field names are semantically meaningful (hostName, ipAddr, appName, status). Minor legacy abbreviations (vipAddress, sid) are well-documented.
- **Gap**: N/A — positive finding.
- **Recommendation**: No action needed.
- **Evidence**: `eureka-client/src/main/java/com/netflix/appinfo/InstanceInfo.java`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal data catalog. InstanceInfo class and GitHub wiki serve as documentation. No schema registry.
- **Gap**: No automated schema discovery.
- **Recommendation**: Publish InstanceInfo schema as part of OpenAPI specification.
- **Evidence**: `eureka-client/src/main/java/com/netflix/appinfo/InstanceInfo.java`, `README.md`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: No OpenTelemetry, X-Ray, Zipkin, or traceparent propagation. SLF4J with log4j producing unstructured text logs. No correlation IDs.
- **Gap**: Cannot debug agent-initiated requests via distributed tracing.
- **Recommendation**: Integrate OpenTelemetry and switch to structured JSON logging.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/ServerRequestAuthFilter.java`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: Servo counters for metrics but no alerting configuration. No CloudWatch alarms, PagerDuty, or SLO-based alerting.
- **Gap**: No alerting on API error rates or latency.
- **Recommendation**: Export Servo metrics to monitoring backend and configure alerts.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/util/EurekaMonitors.java`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: EurekaMonitors tracks registrations, renewals, cancellations, expirations, and rate-limited requests. For service discovery, operational metrics are business metrics.
- **Gap**: N/A — positive finding for service discovery context.
- **Recommendation**: Export to durable metrics backend.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/util/EurekaMonitors.java`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK-QUALITY
- **Finding**: No IaC files. Published as library to Maven Central; deployment infrastructure is consumer-owned.
- **Gap**: No IaC for agent-facing API surface.
- **Recommendation**: Add reference IaC templates for recommended deployments.
- **Evidence**: No IaC files found.

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: GitHub Actions CI/CD with build and publish workflows. No API contract tests or breaking-change detection.
- **Gap**: No automated API contract validation in CI.
- **Recommendation**: Add OpenAPI spec validation and breaking-change detection to CI.
- **Evidence**: `.github/workflows/nebula-ci.yml`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: No deployment rollback. Published as library — rollback via consumer version pinning.
- **Gap**: No automated rollback capability.
- **Recommendation**: Document rollback procedures. Add reference deployment configs with rollback.
- **Evidence**: `.github/workflows/nebula-publish.yml`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: 110 test files. EurekaClientServerRestIntegrationTest covers core REST operations. JUnit 4, Mockito, WireMock. No systematic API test suite or contract tests.
- **Gap**: Test coverage incomplete for all endpoints and error scenarios.
- **Recommendation**: Expand integration tests to cover all REST endpoints.
- **Evidence**: `eureka-server/src/test/java/com/netflix/eureka/resources/EurekaClientServerRestIntegrationTest.java`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: INFO
- **Finding**: Registry is in-memory only (ConcurrentHashMap in JVM heap). No persistent storage to encrypt. Data rebuilt from client registrations after restart.
- **Gap**: N/A — encryption at rest not applicable for in-memory-only storage.
- **Recommendation**: No action needed. Configure encryption at rest if consumers add persistent backing.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/registry/AbstractInstanceRegistry.java`

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationsResource.java` | API-Q1, API-Q2, API-Q5, API-Q7, AUTH-Q3, DATA-Q3, STATE-Q2 |
| `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationResource.java` | API-Q1, API-Q2, API-Q3, API-Q4, AUTH-Q3 |
| `eureka-core/src/main/java/com/netflix/eureka/resources/InstanceResource.java` | API-Q1, API-Q2, API-Q3, AUTH-Q3, STATE-Q2 |
| `eureka-core/src/main/java/com/netflix/eureka/resources/StatusResource.java` | API-Q1 |
| `eureka-core/src/main/java/com/netflix/eureka/resources/PeerReplicationResource.java` | API-Q1, API-Q7 |
| `eureka-core/src/main/java/com/netflix/eureka/ServerRequestAuthFilter.java` | AUTH-Q1, AUTH-Q2, AUTH-Q4, AUTH-Q6, DATA-Q6, OBS-Q1 |
| `eureka-core/src/main/java/com/netflix/eureka/RateLimitingFilter.java` | API-Q8, AUTH-Q2, AUTH-Q7, STATE-Q5 |
| `eureka-core/src/main/java/com/netflix/eureka/registry/AbstractInstanceRegistry.java` | API-Q4, STATE-Q1, STATE-Q2, STATE-Q3, STATE-Q6, DATA-Q6, DATA-Q7 |
| `eureka-core/src/main/java/com/netflix/eureka/DefaultEurekaServerConfig.java` | API-Q8, AUTH-Q5, AUTH-Q7, STATE-Q5, STATE-Q6, STATE-Q7, DATA-Q2, DATA-Q5 |
| `eureka-core/src/main/java/com/netflix/eureka/cluster/PeerEurekaNode.java` | API-Q7, STATE-Q1, STATE-Q4, DATA-Q4 |
| `eureka-core/src/main/java/com/netflix/eureka/util/EurekaMonitors.java` | AUTH-Q6, OBS-Q1, OBS-Q2, OBS-Q3 |
| `eureka-core/src/main/java/com/netflix/eureka/Version.java` | DISC-Q1 |
| `eureka-client/src/main/java/com/netflix/appinfo/InstanceInfo.java` | DATA-Q1, DATA-Q5, DISC-Q1, DISC-Q2, DISC-Q3 |
| `eureka-client/src/main/java/com/netflix/appinfo/AbstractEurekaIdentity.java` | AUTH-Q1 |
| `eureka-client/src/main/java/com/netflix/appinfo/LeaseInfo.java` | DATA-Q5 |
| `eureka-client/src/main/java/com/netflix/discovery/shared/transport/decorator/RetryableEurekaHttpClient.java` | STATE-Q4 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/nebula-ci.yml` | DISC-Q1, ENG-Q2 |
| `.github/workflows/nebula-publish.yml` | AUTH-Q5, ENG-Q2, ENG-Q3 |
| `.github/workflows/nebula-snapshot.yml` | ENG-Q2 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `eureka-server/src/main/webapp/WEB-INF/web.xml` | AUTH-Q1, STATE-Q5 |
| `eureka-server/src/main/resources/eureka-server.properties` | AUTH-Q5 |
| `eureka-server/src/main/resources/eureka-client.properties` | DATA-Q2 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `build.gradle` | ENG-Q3 |
| `eureka-server/build.gradle` | ENG-Q4 |
| `eureka-client/build.gradle` | API-Q5 |

### Test Files
| File | Questions Referenced |
|------|---------------------|
| `eureka-server/src/test/java/com/netflix/eureka/resources/EurekaClientServerRestIntegrationTest.java` | ENG-Q4, HITL-Q3 |

### Documentation
| File | Questions Referenced |
|------|---------------------|
| `README.md` | DISC-Q3 |
| `CHANGELOG.md` | DISC-Q1 |
