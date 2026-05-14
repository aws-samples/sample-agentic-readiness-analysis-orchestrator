# Agentic Readiness Analysis Report

**Target**: Netflix--eureka
**Date**: 2025-05-08
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**TD Version**: agentic-readiness-analysis
**Repository Type**: application
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: java, service-discovery, microservices
**Context**: Netflix service-discovery server and client.

**Archetype Justification**: The application maintains an in-memory registry of service instances with full CRUD operations (register, renew, cancel, status update) exposed via REST endpoints, matching the stateful-crud pattern despite lacking an external database.

**Surface Flags**:
- has_persistent_data_store: false
- has_http_rpc_surface: true
- has_auth_surface: false
- has_write_operations: true
- has_logging_of_user_data: false

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 1 | **RISK-SAFETY**: 5 | **RISK-QUALITY**: 8 | **INFOs**: 10

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days.

**Classification Rationale**: This repo has 1 BLOCKER finding (AUTH-Q1: no machine identity authentication). Under V6 mapping, 1 High finding → Remediation Required. The V5 Readiness Profile aligns: 1 BLOCKER → Remediation Required regardless of RISK counts.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 1 |
| RISK-SAFETY | 5 |
| RISK-QUALITY | 8 |
| INFO | 10 |
| N/A | 0 |
| Not Evaluated (extended) | 19 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 0
**Extended Questions Not Triggered**: 19
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: stateful-crud (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: The application has no authentication enforcement. `ServerRequestAuthFilter.java` only logs client identification headers (`DiscoveryIdentity-Name`, `DiscoveryIdentity-Version`) via Netflix Servo counters — it does not validate, reject, or enforce any identity. The filter chain calls `chain.doFilter(request, response)` unconditionally regardless of header presence or value.
- **Gap**: No machine identity authentication mechanism exists. No OAuth2, API key validation, mTLS, or any form of credential verification. Any client can call all endpoints without proving identity.
- **Remediation**:
  - **Immediate**: Implement API Gateway or service mesh authentication in front of Eureka server endpoints. Add JWT or mTLS validation to the servlet filter chain.
  - **Target State**: All API calls require a validated machine identity with principal attribution in audit logs.
  - **Estimated Effort**: Medium
  - **Dependencies**: None
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/ServerRequestAuthFilter.java`, `eureka-server/src/main/webapp/WEB-INF/web.xml`

---

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No authorization model exists in the application. All endpoints are accessible to any caller without any permission checks. There are no IAM policies, RBAC definitions, or role-per-service configurations in the repository.
- **Gap**: No scoped permission enforcement. An agent identity (once authentication is added) cannot be granted read-only access to specific resources without inheriting broader privileges.
- **Compensating Controls**:
  - Deploy behind an API Gateway with resource-level policies restricting agent access to GET endpoints only.
  - Use network-level segmentation to limit which callers can reach Eureka write endpoints.
- **Remediation Timeline**: 60–90 days (dependent on AUTH-Q1 resolution)
- **Recommendation**: After implementing machine identity (AUTH-Q1), add method-level authorization using IAM policies or API Gateway resource policies to distinguish read vs write access.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/ServerRequestAuthFilter.java` (no authorization logic), `eureka-core/src/main/java/com/netflix/eureka/resources/InstanceResource.java` (no permission checks on PUT/DELETE)

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization exists. The application does not distinguish between read, write, and delete operations from an authorization perspective. All endpoints (GET, POST, PUT, DELETE) are equally accessible to any caller.
- **Gap**: Cannot enforce action-level restrictions — an agent granted any access could register, cancel, or modify instances as easily as querying them.
- **Compensating Controls**:
  - API Gateway method-level authorization (restrict agent to GET only at the gateway layer).
  - Network-level controls separating read and write traffic paths.
- **Remediation Timeline**: 60–90 days (dependent on AUTH-Q1 resolution)
- **Recommendation**: Implement fine-grained RBAC or ABAC in the servlet filter chain or via API Gateway method-level authorization.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/resources/InstanceResource.java`, `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationResource.java`

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No identity management system exists within the application. Since there is no authentication (AUTH-Q1), there is no mechanism to suspend or revoke individual agent identities. The `ServerRequestAuthFilter` reads identity headers but has no capability to block specific identities.
- **Gap**: Cannot isolate a misbehaving agent without taking down the broader platform or applying network-level blocks.
- **Compensating Controls**:
  - IP-based blocking at load balancer or firewall level.
  - Header-based blocking rules in a WAF or reverse proxy.
- **Remediation Timeline**: 60–90 days (dependent on AUTH-Q1 resolution)
- **Recommendation**: Once machine identity is implemented, add an API key revocation mechanism or integrate with Cognito/IAM for identity lifecycle management.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/ServerRequestAuthFilter.java`

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: A rate limiting filter (`RateLimitingFilter.java`) exists in the codebase with a token-bucket implementation. However, it is **commented out** in the default `web.xml` deployment descriptor, meaning rate limiting is disabled by default. The filter only applies to registry fetch operations (`/v2/apps` and `/v2/apps/*`) and does not cover write operations (register, cancel, status update).
- **Gap**: Rate limiting is not active by default. When enabled, it only protects read (fetch) endpoints — write operations have no rate limiting. A runaway agent loop could overwhelm the server with registrations or status updates.
- **Compensating Controls**:
  - Uncomment the rate limiting filter mapping in `web.xml` to enable for read endpoints.
  - Deploy behind an API Gateway with throttling configuration covering all endpoints.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Enable the existing rate limiting filter and extend coverage to write endpoints. Better: deploy behind an API Gateway with per-client throttle configuration.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/RateLimitingFilter.java`, `eureka-server/src/main/webapp/WEB-INF/web.xml` (rate limiter mapping commented out)

#### DATA-Q2: Data Residency and Sovereignty ⚡

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The Eureka registry stores service instance metadata including hostnames, IP addresses, port numbers, AWS metadata (instance IDs, AMI IDs, availability zones), and custom metadata key-value pairs. No data residency configuration or region-restriction controls exist in the repository. The peer replication system replicates data across configured peer nodes with no region boundary enforcement.
- **Gap**: No data residency controls. Service instance metadata replicated across peer nodes could cross region boundaries without governance. If an agent transmits registry data to an LLM endpoint, there are no controls preventing cross-region data flow.
- **Compensating Controls**:
  - Restrict agent access to read-only operations against a single-region Eureka cluster.
  - Ensure LLM endpoints are co-located in the same region as the Eureka cluster.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document data residency requirements for service registry metadata. Configure peer replication to respect region boundaries.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/registry/PeerAwareInstanceRegistryImpl.java`, `eureka-core/src/main/java/com/netflix/eureka/cluster/PeerEurekaNode.java`

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, Swagger, AsyncAPI, GraphQL schema, or Smithy model files exist in the repository. The REST API is defined implicitly through JAX-RS annotations in Java source code.
- **Gap**: No machine-readable API specification. Agent tool generation requires manual tool authoring from source code annotations.
- **Compensating Controls**:
  - Generate OpenAPI spec from JAX-RS annotations using tools like Swagger Core or Enunciate.
  - Manually author an OpenAPI specification based on the JAX-RS resource classes.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Generate an OpenAPI 3.0 specification from the existing JAX-RS annotations using swagger-jaxrs2 or similar tooling.
- **Evidence**: No spec files found. API defined in `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationsResource.java`, `ApplicationResource.java`, `InstanceResource.java`

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Error responses use HTTP status codes only (403 Forbidden, 404 Not Found, 500 Internal Server Error) without structured error bodies. Most error responses are empty (`Response.status(Status.NOT_FOUND).build()`) or contain plain-text strings (`Response.status(400).entity("Missing instanceId").build()`). No consistent error response format with error codes, categories, or retryable indicators.
- **Gap**: Agents cannot distinguish retriable errors from terminal errors. A 500 with no body forces agents to guess whether to retry.
- **Compensating Controls**:
  - Implement error-mapping middleware that wraps raw HTTP status codes into structured JSON error objects.
  - Document error patterns externally for agent tool definitions.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement a Jersey `ExceptionMapper` that produces structured JSON error responses with error code, message, and retryable flag.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/resources/InstanceResource.java` (lines returning `Response.status(Status.NOT_FOUND).build()`), `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationResource.java` (400 errors with plain text)

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The API uses URL-based versioning (`/{version}/apps`) with version path parameter. However, there is no formal schema documentation, no breaking change detection in CI, and no consumer-driven contract tests. The CI pipeline (`nebula-ci.yml`) runs `./gradlew build` without API contract validation. The CHANGELOG.md exists but no automated schema comparison tools are configured.
- **Gap**: No breaking change detection in CI. Agent tool schemas could break silently when API responses change.
- **Compensating Controls**:
  - Pin agent tool definitions to a specific API version (v2).
  - Add contract tests to the CI pipeline.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenAPI spec diffing or consumer-driven contract tests (Pact) to the CI pipeline to detect breaking changes before release.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationsResource.java` (`@Path("/{version}/apps")`), `.github/workflows/nebula-ci.yml` (no contract test step)

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No distributed tracing is implemented. No OpenTelemetry, X-Ray, or Zipkin instrumentation exists. Logging uses Log4j 1.x with unstructured text format (`%d %-5p %C:%L [%t] [%M] %m%n`). No JSON structured logging. No correlation IDs or request IDs are propagated through the request chain.
- **Gap**: Cannot trace agent-initiated requests through the system. Logs are unstructured and lack correlation IDs for debugging.
- **Compensating Controls**:
  - Add a servlet filter that generates and propagates request IDs.
  - Migrate to SLF4J + Logback with JSON layout.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenTelemetry instrumentation and migrate from Log4j 1.x to a structured logging framework with JSON output and correlation IDs.
- **Evidence**: `eureka-server/src/main/resources/log4j.properties` (unstructured text format), no tracing libraries in `build.gradle`

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The application uses Netflix Servo for metrics collection (`EurekaMonitors.java` defines counters for operations like RENEW, CANCEL, GET_ALL, RATE_LIMITED). However, no alerting thresholds, CloudWatch alarms, PagerDuty integration, or anomaly detection configuration exists in the repository.
- **Gap**: No alerting configured. Target system degradation would not trigger notifications before agents start cascading failures.
- **Compensating Controls**:
  - Configure external monitoring (CloudWatch, Datadog) to scrape Servo metrics and alert on thresholds.
  - Add health check endpoint monitoring.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure alerting on the Servo metrics (error rates, rate-limited counts, renewal failures) using CloudWatch or equivalent.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/util/EurekaMonitors.java` (metrics defined, no alerting), no IaC with alarm definitions

#### ENG-Q1: Infrastructure Governance — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No Infrastructure as Code exists in this repository. No Terraform, CloudFormation, CDK, Helm, or Kubernetes manifests. The application is packaged as a WAR file deployed to a servlet container with no defined infrastructure configuration for the deployment target.
- **Gap**: The integration surface (API endpoint, network, IAM) is not defined as code. No peer review of infrastructure changes. No drift detection.
- **Compensating Controls**:
  - Manage infrastructure in a separate IaC repository with PR-based review.
  - Use AWS Config rules for drift detection on the deployment environment.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Define the Eureka server deployment infrastructure (compute, networking, API gateway, IAM) as IaC in a dedicated repository or add IaC to this repo.
- **Evidence**: No IaC files found in repository. WAR packaging in `eureka-server/build.gradle`.

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: CI/CD pipelines exist (GitHub Actions: `nebula-ci.yml` for build, `nebula-publish.yml` for release). The CI pipeline runs `./gradlew build` which includes unit tests. However, no API contract testing, no OpenAPI validation, no consumer-driven contract tests (Pact), and no breaking change detection are configured.
- **Gap**: API-breaking changes are not caught in the pipeline. Agent tool bindings could break silently after a deployment.
- **Compensating Controls**:
  - Add manual API review step before releases.
  - Pin agent tools to specific API version and monitor for 4xx spikes.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add API contract validation to the CI pipeline — either OpenAPI spec comparison or Pact-style consumer-driven contract tests.
- **Evidence**: `.github/workflows/nebula-ci.yml`, `.github/workflows/nebula-publish.yml`

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The CI/CD pipeline publishes artifacts to Maven Central and NetflixOSS repositories. No deployment rollback mechanism is defined in the repository. No blue/green deployment, no canary deployment, no CodeDeploy configuration, and no feature flags exist.
- **Gap**: Cannot roll back the Eureka server deployment to a previous known-good state if a change breaks agent-facing APIs.
- **Compensating Controls**:
  - Maintain the previous WAR artifact and redeploy manually.
  - Implement deployment rollback in the hosting infrastructure (external to this repo).
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement deployment automation with rollback capability (blue/green or canary deployment with automatic rollback triggers).
- **Evidence**: `.github/workflows/nebula-publish.yml` (publish only, no deployment or rollback)

---

## INFOs — Architecture and Design Inputs

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Write endpoints (register, renew, cancel, status update) do not implement explicit idempotency keys. The register endpoint (`POST /{version}/apps/{appId}`) uses the instance ID as a natural idempotency mechanism — re-registering the same instance ID overwrites the existing entry. Heartbeat renewal (`PUT`) is inherently idempotent.
- **Implication**: If agent scope is expanded to write-enabled, idempotency should be validated for all write paths, particularly for metadata updates.
- **Recommendation**: Document natural idempotency guarantees. If write-enabled agent scope is planned, validate that all write operations handle duplicate calls safely.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationResource.java` (addInstance), `eureka-core/src/main/java/com/netflix/eureka/resources/InstanceResource.java` (renewLease)

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: API responses are available in both JSON and XML formats, controlled by the `Accept` header. The `@Produces({"application/xml", "application/json"})` annotation is present on all resource classes. JSON is well-supported via Jackson serialization.
- **Implication**: JSON responses are directly consumable by LLM-based agents without additional parsing. XML support is available for legacy clients.
- **Recommendation**: Prefer JSON in agent tool definitions. The dual-format support is adequate.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationsResource.java` (`@Produces({"application/xml", "application/json"})`)

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: The rate limiting filter (`RateLimitingFilter.java`) exists but does not return rate limit headers (`X-RateLimit-Remaining`, `Retry-After`) to clients. When rate-limited, it returns `HTTP 503 Service Unavailable` with no additional information.
- **Implication**: Agents cannot self-throttle based on rate limit feedback. They must rely on external configuration to avoid triggering rate limits.
- **Recommendation**: If rate limiting is enabled, add `X-RateLimit-Remaining` and `Retry-After` headers to responses to enable agent self-throttling.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/RateLimitingFilter.java`

### AUTH-Q5: Credential Management

- **Severity**: INFO
- **Finding**: No credentials are managed within the application code. The CI/CD pipeline uses GitHub Actions secrets (`${{ secrets.ORG_SIGNING_KEY }}`, `${{ secrets.ORG_SONATYPE_PASSWORD }}`) for publishing — these are properly managed via GitHub's secrets infrastructure, not hardcoded. No hardcoded passwords, API keys, or connection strings found in source code or configuration files.
- **Implication**: Credential management is not a concern within this repository. When deployed behind an API Gateway with authentication, credentials for agent identities would be managed externally.
- **Recommendation**: When adding machine identity authentication, use AWS Secrets Manager or equivalent for credential rotation.
- **Evidence**: `.github/workflows/nebula-publish.yml` (uses GitHub Actions secrets properly)

### AUTH-Q6: Immutable Audit Logging ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — since `has_auth_surface` is false, evaluated as INFO
- **Finding**: No audit logging infrastructure exists. The `ServerRequestAuthFilter` logs client identity headers to Netflix Servo counters (metrics) but does not produce immutable audit logs of operations. Application logging is unstructured text via Log4j 1.x without immutability guarantees.
- **Implication**: System does not execute authenticated agent-invoked operations — audit logging is a consumer/platform responsibility until machine identity is implemented.
- **Recommendation**: When implementing machine identity (AUTH-Q1), simultaneously implement immutable audit logging for all write operations with principal attribution.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/ServerRequestAuthFilter.java`, `eureka-server/src/main/resources/log4j.properties`

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO (further: stateful-crud with write operations, but read-only scope makes compensation informational)
- **Finding**: No compensation or rollback mechanisms for multi-step operations. Instance registration is a single atomic operation. Peer replication is fire-and-forget with retry but no compensation. If a replication to one peer succeeds and another fails, no rollback of the successful replication occurs.
- **Implication**: For read-only agent scope, compensation is not relevant. If scope is expanded to write-enabled, the lack of compensation for registration + replication sequences becomes a BLOCKER.
- **Recommendation**: If write-enabled agent scope is planned, implement saga-style compensation for multi-step registration/replication workflows.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/cluster/PeerEurekaNode.java`, `eureka-core/src/main/java/com/netflix/eureka/registry/PeerAwareInstanceRegistryImpl.java`

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The registry uses `ReentrantReadWriteLock` and `ConcurrentHashMap` for thread-safe access. The `AbstractInstanceRegistry` employs read/write locks for registry operations, providing concurrent read access while serializing writes. `lastDirtyTimestamp` comparison provides optimistic-locking-style conflict detection during peer replication.
- **Implication**: Concurrency controls exist for internal operations. For read-only agent scope, these are informational. If write-enabled, the timestamp-based conflict detection should be evaluated for agent-specific race conditions.
- **Recommendation**: Current concurrency controls are adequate for the read-only scope.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/registry/AbstractInstanceRegistry.java` (ReentrantReadWriteLock), `eureka-core/src/main/java/com/netflix/eureka/resources/InstanceResource.java` (lastDirtyTimestamp validation)

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits exist for agent-initiated actions. The rate limiting filter (when enabled) provides per-second request throttling but not per-session or per-run operation limits.
- **Implication**: Read-only agents cannot modify records, so transaction limits are informational only.
- **Recommendation**: If agent scope is expanded to write-enabled, implement per-agent operation limits (max registrations per minute, max status changes per session).
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/RateLimitingFilter.java`

### DATA-Q1: Sensitive Data Classification ⚡

- **Severity**: INFO
- **Conditional**: Stage A = No. The Eureka registry stores service discovery metadata (application names, hostnames, IP addresses, ports, health status, AWS instance metadata). This is infrastructure operational data, not user PII, PHI, financial records, or credentials. No user-specific personal data is stored, processed, or transmitted.
- **Implication**: Not a data-handling target for PII/PHI/financial data. No data classification controls needed for the registry's operational metadata.
- **Recommendation**: No action needed. If custom metadata fields are used by consuming services to store sensitive data, the consuming services bear classification responsibility.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/registry/AbstractInstanceRegistry.java` (stores InstanceInfo with hostnames, ports, status)

### DATA-Q6: PII Redaction in Logs

- **Severity**: INFO
- **Finding**: `has_logging_of_user_data` is false. The application logs service instance metadata (application names, instance IDs, status changes) — not user PII. Log output contains infrastructure operational data only.
- **Implication**: PII-in-logs risk is not applicable. The system does not handle user personal data.
- **Recommendation**: No action needed.
- **Evidence**: `eureka-server/src/main/resources/log4j.properties`, `eureka-core/src/main/java/com/netflix/eureka/resources/InstanceResource.java` (logs app names and instance IDs only)

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: PASS (no finding)
- **Finding**: The application exposes a well-defined REST API via JAX-RS annotations. Endpoints include `/{version}/apps` (GET all applications), `/{version}/apps/{appId}` (GET/POST application), `/{version}/apps/{appId}/{id}` (GET/PUT/DELETE instance), `/{version}/peerreplication` (POST peer replication), `/{version}/status` (GET server status), `/{version}/vips` and `/{version}/svips` (GET VIP lookups). No database-direct or file-based integration patterns.
- **Gap**: None — API surface exists and is clearly defined in code.
- **Recommendation**: N/A
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationsResource.java`, `ApplicationResource.java`, `InstanceResource.java`, `PeerReplicationResource.java`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: No machine-readable API specification files exist. API is defined implicitly through JAX-RS annotations only.
- **Gap**: No OpenAPI, AsyncAPI, or equivalent spec. Agent tool generation requires manual authoring.
- **Recommendation**: Generate OpenAPI 3.0 specification from JAX-RS annotations.
- **Evidence**: No spec files found in repository.

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: Error responses use HTTP status codes without structured bodies. Errors returned as plain text or empty responses.
- **Gap**: No structured error format with error code, message, and retryable indicator.
- **Recommendation**: Implement structured JSON error responses via Jersey ExceptionMapper.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/resources/InstanceResource.java`, `ApplicationResource.java`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Register uses instance ID as natural idempotency key. Heartbeat renewal is inherently idempotent.
- **Gap**: No explicit idempotency key mechanism for write operations.
- **Recommendation**: Document natural idempotency guarantees.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationResource.java`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: Supports JSON and XML via content negotiation (Accept header).
- **Gap**: None
- **Recommendation**: Prefer JSON in agent tool definitions.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationsResource.java`

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has operations >30s OR long-running workflows
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has state changes (stateful-crud, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: Rate limiting filter exists but does not return rate limit headers. Returns 503 with no rate limit feedback.
- **Gap**: No self-throttling signals for agents.
- **Recommendation**: Add X-RateLimit-Remaining and Retry-After headers.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/RateLimitingFilter.java`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: No authentication enforcement. ServerRequestAuthFilter logs headers only — does not validate or reject requests.
- **Gap**: No machine identity authentication mechanism exists.
- **Recommendation**: Implement API Gateway authentication or servlet-level JWT/mTLS validation.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/ServerRequestAuthFilter.java`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: No authorization model exists. All endpoints accessible to any caller.
- **Gap**: No scoped permission enforcement.
- **Recommendation**: Add method-level authorization via API Gateway or servlet filter.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/ServerRequestAuthFilter.java`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization. GET/POST/PUT/DELETE equally accessible.
- **Gap**: Cannot restrict agent to read operations at application layer.
- **Recommendation**: Implement RBAC with action-level granularity.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/resources/InstanceResource.java`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Always evaluated for stateful-crud but archetype-calibrated — downgraded for service-discovery infrastructure that does not process user-specific data flows.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: No credentials in application code. CI/CD uses GitHub Actions secrets properly.
- **Gap**: None within repository scope.
- **Recommendation**: Use AWS Secrets Manager when adding machine identity.
- **Evidence**: `.github/workflows/nebula-publish.yml`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — since `has_auth_surface` is false, evaluated as INFO
- **Finding**: No audit logging infrastructure. ServerRequestAuthFilter logs to Servo counters (metrics, not audit trail).
- **Gap**: No immutable audit log of operations.
- **Recommendation**: Implement audit logging when machine identity is added.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/ServerRequestAuthFilter.java`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: No identity management system. No mechanism to suspend individual identities.
- **Gap**: Cannot isolate misbehaving agent without platform-level intervention.
- **Recommendation**: Add API key revocation or identity disable mechanism.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/ServerRequestAuthFilter.java`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No compensation mechanisms for multi-step operations. Peer replication is fire-and-forget.
- **Gap**: No rollback for failed multi-step operations.
- **Recommendation**: Implement compensation for write workflows if scope expands.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/cluster/PeerEurekaNode.java`

#### STATE-Q2: Queryable Current State
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: ReentrantReadWriteLock and ConcurrentHashMap provide thread-safe access. Timestamp-based conflict detection for peer replication.
- **Gap**: None for read-only scope.
- **Recommendation**: Current controls adequate for read-only scope.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/registry/AbstractInstanceRegistry.java`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has external dependencies (calls other services or external APIs)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: Rate limiting filter exists but is disabled by default. Only covers read endpoints when enabled.
- **Gap**: No active rate limiting. Write endpoints unprotected.
- **Recommendation**: Enable rate limiting and extend to write endpoints.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/RateLimitingFilter.java`, `eureka-server/src/main/webapp/WEB-INF/web.xml`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No per-agent transaction limits. Rate limiter provides per-second throttling only.
- **Gap**: No operation limits for agent sessions.
- **Recommendation**: Add per-agent operation limits if write scope is planned.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/RateLimitingFilter.java`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: No sandbox or staging environment configuration exists in the repository. No Docker Compose for local testing, no seed data scripts, no environment-specific configurations beyond the commented-out properties in `eureka-server.properties`. The `eureka-examples` module provides basic client/service examples but not a production-equivalent test environment.
- **Gap**: No staging environment with production-equivalent data shape for agent testing.
- **Recommendation**: Create a Docker Compose-based local environment or document staging deployment procedures.
- **Evidence**: `eureka-server/src/main/resources/eureka-server.properties` (minimal config), `eureka-examples/` (basic examples only)

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification ⚡
- **Severity**: INFO
- **Finding**: Stage A = No. System stores service discovery metadata (hostnames, IPs, ports, status) — not PII/PHI/financial/credential data.
- **Gap**: N/A — not a data-handling target for sensitive data.
- **Recommendation**: No action needed.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/registry/AbstractInstanceRegistry.java`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No data residency controls. Peer replication crosses region boundaries without governance.
- **Gap**: No region-restriction controls for registry metadata.
- **Recommendation**: Configure peer replication with region boundaries. Document residency requirements.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/cluster/PeerEurekaNode.java`

#### DATA-Q3: Selective Query Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has list/query endpoints with potentially unbounded results
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q4: System of Record Designations
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q6: PII Redaction in Logs
- **Severity**: INFO
- **Finding**: `has_logging_of_user_data` is false. System logs infrastructure metadata only, not user PII.
- **Gap**: N/A — PII-in-logs risk not applicable.
- **Recommendation**: No action needed.
- **Evidence**: `eureka-server/src/main/resources/log4j.properties`

#### DATA-Q7: Data Quality Awareness
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Always evaluated as INFO
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: URL-based versioning exists but no schema documentation or breaking change detection in CI.
- **Gap**: No automated contract validation. Agent tool schemas could break silently.
- **Recommendation**: Add contract testing to CI pipeline.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationsResource.java`, `.github/workflows/nebula-ci.yml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Always evaluated as INFO
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Always evaluated as INFO
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: No distributed tracing. Log4j 1.x with unstructured text format. No correlation IDs.
- **Gap**: Cannot trace agent-initiated requests. No structured logging.
- **Recommendation**: Add OpenTelemetry and migrate to structured JSON logging.
- **Evidence**: `eureka-server/src/main/resources/log4j.properties`, `build.gradle`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: Servo metrics defined but no alerting thresholds configured.
- **Gap**: No alerting on API degradation.
- **Recommendation**: Configure alerting on Servo metrics.
- **Evidence**: `eureka-core/src/main/java/com/netflix/eureka/util/EurekaMonitors.java`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Always evaluated as INFO
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance
- **Severity**: RISK-QUALITY
- **Finding**: No IaC in repository. WAR-based deployment with no infrastructure definition.
- **Gap**: Integration surface not defined as code. No peer review or drift detection.
- **Recommendation**: Define deployment infrastructure as IaC.
- **Evidence**: No IaC files found.

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: CI/CD exists but no API contract testing or breaking change detection.
- **Gap**: API-breaking changes not caught in pipeline.
- **Recommendation**: Add API contract validation to CI.
- **Evidence**: `.github/workflows/nebula-ci.yml`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: No deployment rollback mechanism defined. Publish-only CI/CD.
- **Gap**: Cannot roll back to previous known-good state.
- **Recommendation**: Implement blue/green or canary deployment with automatic rollback.
- **Evidence**: `.github/workflows/nebula-publish.yml`

#### ENG-Q4: API Test Coverage
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Always evaluated (but INFO for stateless-utility)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### ENG-Q5: Encryption at Rest
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has persistent data stores
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `eureka-core/src/main/java/com/netflix/eureka/ServerRequestAuthFilter.java` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7 |
| `eureka-core/src/main/java/com/netflix/eureka/RateLimitingFilter.java` | STATE-Q5, STATE-Q6, API-Q8 |
| `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationsResource.java` | API-Q1, API-Q2, API-Q5, DISC-Q1 |
| `eureka-core/src/main/java/com/netflix/eureka/resources/ApplicationResource.java` | API-Q1, API-Q3, API-Q4 |
| `eureka-core/src/main/java/com/netflix/eureka/resources/InstanceResource.java` | API-Q1, API-Q3, API-Q4, AUTH-Q2, AUTH-Q3, STATE-Q3, DATA-Q6 |
| `eureka-core/src/main/java/com/netflix/eureka/resources/PeerReplicationResource.java` | API-Q1 |
| `eureka-core/src/main/java/com/netflix/eureka/registry/AbstractInstanceRegistry.java` | STATE-Q3, DATA-Q1 |
| `eureka-core/src/main/java/com/netflix/eureka/registry/PeerAwareInstanceRegistryImpl.java` | DATA-Q2, STATE-Q1 |
| `eureka-core/src/main/java/com/netflix/eureka/cluster/PeerEurekaNode.java` | DATA-Q2, STATE-Q1 |
| `eureka-core/src/main/java/com/netflix/eureka/util/EurekaMonitors.java` | OBS-Q2 |
| `eureka-core/src/main/java/com/netflix/eureka/EurekaBootStrap.java` | API-Q1 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/nebula-ci.yml` | ENG-Q2, DISC-Q1 |
| `.github/workflows/nebula-publish.yml` | ENG-Q3, AUTH-Q5 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `eureka-server/src/main/webapp/WEB-INF/web.xml` | AUTH-Q1, STATE-Q5 |
| `eureka-server/src/main/resources/log4j.properties` | OBS-Q1, AUTH-Q6, DATA-Q6 |
| `eureka-server/src/main/resources/eureka-server.properties` | HITL-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `build.gradle` | OBS-Q1 |
