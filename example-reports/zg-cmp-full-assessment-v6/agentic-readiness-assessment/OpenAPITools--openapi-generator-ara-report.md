# Agentic Readiness Assessment Report

**Target**: /Users/lucasdu/Documents/AWS-MAC/2026-projects/sample-agentic-readiness-assessment/services/OpenAPITools--openapi-generator
**Date**: 2026-05-08
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Service Archetype**: stateless-utility (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: java, code-generation, api
**Context**: Code-generation toolkit that produces clients/servers from OpenAPI specs.

**Archetype Justification**: This is a code-generation toolkit distributed as a CLI JAR, Docker image, and build plugins (Maven/Gradle/Mill). The optional online Spring Boot service is a stateless wrapper around the CLI with no persistent data store, no authentication, and no user-specific state — generated files are written to a temporary filesystem directory for immediate download.

**Dev-Library-Application Override**: This repository classifies as `application` (has source + entry points) but functions as a developer tool / code-generation library. Service archetype is `stateless-utility` AND 3 of 5 surface flags are `false` (`has_persistent_data_store`, `has_auth_surface`, `has_logging_of_user_data`). Applying the `library` N/A mapping for ENG-Q1 through ENG-Q5 per Step 1.5 override rules.

- **Surface flags**:
  - has_persistent_data_store: false
  - has_http_rpc_surface: true
  - has_auth_surface: false
  - has_write_operations: true (POST endpoints generate code, but no persistent state mutation)
  - has_logging_of_user_data: false

---

## Readiness Profile: Pilot-Ready (Safety Concerns)

**BLOCKERs**: 0 | **RISK-SAFETY**: 3 | **RISK-QUALITY**: 5 | **INFOs**: 16

This repository has 0 BLOCKER findings and 3 RISK-SAFETY findings. With 0 BLOCKERs and 3+ RISK-SAFETY findings, the profile is **Pilot-Ready (Safety Concerns)**.

Supervised pilot with elevated safety oversight: (1) all Pilot-Ready controls apply, (2) prioritize RISK-SAFETY remediation before expanding agent scope, (3) dedicated safety review cadence, (4) agent restricted to lowest-blast-radius operations until RISK-SAFETY count drops below 3.

**V6 Classification Rationale**: This repo has 0 High findings (no BLOCKERs), 8 Medium findings (3 safety-impact + 5 non-safety-impact), and 16 Low findings (INFOs). The matched rule is: "0 High, ≥2 Medium, ≥3 safety-impact Medium → Pilot-Ready (Safety Concerns)." The V6 classification aligns with the V5 Readiness Profile — both yield Pilot-Ready (Safety Concerns) because the 3 RISK-SAFETY findings map to 3 safety-impact Medium findings under the unified severity vocabulary.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 0 |
| RISK-SAFETY | 3 |
| RISK-QUALITY | 5 |
| INFO | 16 |
| N/A | 5 |
| Not Evaluated (extended) | 14 |
| **Total** | **43** |

**Core Questions Evaluated**: 19 (24 minus 5 N/A from library mapping)
**Extended Questions Triggered**: 0
**Extended Questions Not Triggered**: 14
**Questions N/A (repo_type: application, dev-library-application override)**: 5
**Service Archetype**: stateless-utility (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

No BLOCKERs identified.

---

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The online service has no authentication or authorization mechanism. All endpoints are publicly accessible with no identity differentiation. There are no IAM policies, role definitions, or permission scopes defined anywhere in the repository. CORS is configured as wide-open (`allowedOrigins("*")`).
- **Gap**: No scoped permission model exists. Any caller (including a potential agent) would have identical unrestricted access to all endpoints.
- **Compensating Controls**:
  - Deploy the online service behind an API Gateway with IAM-based authorization and usage plans that scope agent access to read-only GET endpoints.
  - Use network-level controls (security groups, VPC) to restrict access to the online service during pilot.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: If the online service is to be exposed to agents, deploy it behind AWS API Gateway with resource-level IAM policies that restrict agent identities to specific endpoints (e.g., GET-only for read-only agents).
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/OpenAPI2SpringBoot.java` (CORS `*`), absence of Spring Security dependency in `modules/openapi-generator-online/pom.xml`

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The online service has no authorization controls of any kind. There is no distinction between read operations (GET /api/gen/clients, GET /api/gen/servers) and write operations (POST /api/gen/clients/{language}, POST /api/gen/servers/{framework}). Any caller can invoke any endpoint.
- **Gap**: No action-level authorization exists. An agent intended for read-only access could invoke code-generation (POST) endpoints without restriction.
- **Compensating Controls**:
  - Deploy behind API Gateway with method-level authorization (allow GET, deny POST for read-only agent identities).
  - Implement a lightweight Spring Security filter that checks a request header/token for action-level permissions.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add API Gateway method-level authorization or Spring Security configuration to differentiate read (GET) from write (POST) operations at the API layer.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/GenApiController.java`, absence of any `@PreAuthorize`, `@Secured`, or role-check annotations

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The online service has no rate limiting at any layer. No API Gateway throttling configuration, no WAF rules, no application-level rate limiting middleware exists. The POST endpoints trigger CPU-intensive code generation (Maven template rendering for 210+ languages) which could be abused by a runaway agent loop.
- **Gap**: No rate limiting exists. A runaway agent could overwhelm the service by calling POST /api/gen/clients or /api/gen/servers repeatedly, causing CPU exhaustion and denial of service.
- **Compensating Controls**:
  - Deploy behind API Gateway with usage plans and throttle settings (e.g., 10 requests/second burst, 5 requests/second steady-state for POST endpoints).
  - Add a reverse proxy (nginx, HAProxy) with request rate limiting before the Spring Boot application.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Deploy behind AWS API Gateway with usage plans that enforce rate limits (low burst for POST code-generation endpoints, higher for GET metadata endpoints). Alternatively, add `spring-boot-starter-actuator` with a rate limiting filter.
- **Evidence**: Absence of rate limiting in `modules/openapi-generator-online/src/main/resources/application.properties`, absence of API Gateway or WAF configuration in repository, absence of any `@RateLimiter` annotations

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The online module uses Springfox 3.0.0 which auto-generates a Swagger/OpenAPI specification at runtime (available at `/api-docs`). However, no committed, static OpenAPI specification file exists in the repository for the online service's own API. The spec is only available when the service is running.
- **Gap**: No static machine-readable API specification is committed to the repository. Agent tool generation requires a spec file at build time, not just a runtime endpoint.
- **Compensating Controls**:
  - Export the runtime-generated spec from a running instance and commit it to the repository.
  - Use `springdoc-openapi-maven-plugin` to generate the spec during build.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a build step that exports the Springfox-generated OpenAPI spec to a static `openapi.yaml` file committed to the repository, or migrate from Springfox to springdoc-openapi which has better static export support.
- **Evidence**: `modules/openapi-generator-online/pom.xml` (Springfox 3.0.0 dependency), `modules/openapi-generator-online/src/main/resources/application.properties` (api-docs path), absence of static OpenAPI spec file for the online service

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The online service uses Spring Boot's default error handling. The `ResponseCode` class defines error codes but there is no consistent structured error response format with error code, message, and retryable classification across all endpoints.
- **Gap**: No standardized error response structure with retryable classification. Default Spring Boot error responses provide HTTP status and message but no machine-readable error category to help agents distinguish retriable from terminal failures.
- **Compensating Controls**:
  - Agents can rely on HTTP status codes (4xx = terminal, 5xx = retriable) as a baseline strategy.
  - Document error codes in the exported OpenAPI spec for agent tool generation.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add a global `@ControllerAdvice` exception handler that returns structured JSON errors with fields: `error_code`, `message`, `retryable`, and `details`.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/model/ResponseCode.java`, default Spring Boot error handling

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The online service has no distributed tracing (no X-Ray, no OpenTelemetry SDK, no Spring Cloud Sleuth). Logging relies entirely on Spring Boot defaults (embedded Logback) with no structured JSON logging configuration and no correlation ID propagation.
- **Gap**: No trace ID propagation, no structured JSON logs, no correlation IDs. If an agent-initiated request fails, there is no way to trace the request through the system.
- **Compensating Controls**:
  - Add Spring Cloud Sleuth (or Micrometer Tracing for Boot 3) for automatic trace ID injection.
  - Configure Logback to output JSON format with a request-scoped MDC correlation ID.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `spring-cloud-sleuth` or migrate to Spring Boot 3 with Micrometer Tracing for automatic trace context propagation. Configure Logback with a JSON encoder (`logstyle-logback-encoder`) and MDC correlation IDs.
- **Evidence**: Absence of tracing dependencies in `modules/openapi-generator-online/pom.xml`, absence of `logback.xml` or `logback-spring.xml`, absence of OpenTelemetry or X-Ray SDK

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No alerting configuration exists anywhere in the repository. No CloudWatch alarms, no PagerDuty/OpsGenie integration, no health check monitoring, no SLO-based alerting. The `spring-boot-starter-actuator` dependency is not present.
- **Gap**: No alerting for error rates or latency. Degradation of the online service would not be detected until users report failures.
- **Compensating Controls**:
  - Add Spring Boot Actuator with health and metrics endpoints for external monitoring.
  - Deploy behind an ALB with health check configured.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `spring-boot-starter-actuator` for metrics exposure, then configure CloudWatch or Prometheus/Grafana alerting on p99 latency and 5xx error rate.
- **Evidence**: Absence of actuator dependency in `modules/openapi-generator-online/pom.xml`, absence of any monitoring/alerting configuration in the repository

---

## INFOs — Architecture and Design Inputs

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: POST endpoints (generate client/server) are not idempotent — each call generates a new ZIP file with a unique fileId. However, since agent_scope is read-only, write operations are not in scope.
- **Implication**: If agent_scope expands to write-enabled, idempotency keys should be added to POST endpoints to prevent duplicate code generation on retry.
- **Recommendation**: If write-enabled agents are planned, add idempotency key support (e.g., hash of input spec + language + options as a cache key).
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/GenApiController.java`

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: The online service returns JSON responses for metadata endpoints (GET) and a binary ZIP file download for generated code. Content-types are `application/json` for metadata and `application/octet-stream` for downloads.
- **Implication**: JSON metadata is directly consumable by agents. Generated code downloads (ZIP binary) require file-handling capabilities in the agent tooling.
- **Recommendation**: No change needed. JSON metadata endpoints are well-suited for agent consumption.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/GenApiController.java`

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limits are documented, and no rate limit headers (X-RateLimit-Remaining, Retry-After) are returned in responses.
- **Implication**: Agents have no programmatic way to self-throttle. If rate limiting is added at the gateway layer, ensure headers are propagated to responses.
- **Recommendation**: When deploying behind API Gateway with rate limits, ensure gateway passes through rate-limit headers to callers.
- **Evidence**: Absence of rate limit headers in controller responses

### AUTH-Q1: Machine Identity Authentication

- **Severity**: INFO
- **Finding**: No authentication mechanism exists on the online service. There are no OAuth2, API key, mTLS, or Cognito configurations. The service is designed to run as a public utility.
- **Implication**: The system does not issue or enforce machine identities. If agents are to interact with this service in a controlled manner, authentication must be added at the gateway/platform layer.
- **Recommendation**: Deploy behind API Gateway with API key or IAM-based authentication for agent identities. The application itself does not need modification if platform-layer identity is used.
- **Evidence**: Absence of Spring Security in `modules/openapi-generator-online/pom.xml`, absence of any auth configuration

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: INFO
- **Finding**: No identity propagation exists because there is no authentication at all. The system does not distinguish callers.
- **Implication**: For a stateless code-generation utility, identity propagation has minimal security impact. Archetype calibration applies: stateless-utility → INFO.
- **Recommendation**: If deployed in a multi-tenant context, add caller identification at the gateway layer for audit attribution.
- **Evidence**: Absence of authentication mechanism

### AUTH-Q5: Credential Management

- **Severity**: INFO
- **Finding**: CI/CD workflows use GitHub Actions secrets for GPG signing keys and Maven credentials (`${{ secrets.GPG_KEY_ID }}`, `${{ secrets.OSSRH_USERNAME }}`). No application-level secrets are hardcoded. The application itself has no secrets to manage (no database connections, no external service keys).
- **Implication**: CI/CD credential management is appropriate for a public open-source project. No application secrets exist to manage.
- **Recommendation**: No change needed. Continue using GitHub Actions secrets for CI/CD credentials.
- **Evidence**: `.github/workflows/maven-release.yml`, `.github/workflows/docker-release.yml`

### AUTH-Q6: Immutable Audit Logging ⚡

- **Severity**: INFO
- **Conditional**: System does not execute agent-invoked write operations in a persistent-state context — audit logging is a consumer responsibility. The dev-library-application override applies.
- **Finding**: No audit logging exists. The online service has no persistent state to audit — generated code is a transient artifact. There is no CloudTrail configuration, no immutable log storage.
- **Implication**: For a stateless code-generation tool, the audit concern is minimal. If compliance requires tracking which agent generated what code, add request logging at the gateway layer.
- **Recommendation**: If deployed in a compliance-sensitive context, add API Gateway access logging with principal attribution.
- **Evidence**: Absence of CloudTrail, absence of audit logging configuration

### AUTH-Q7: Agent Identity Suspension

- **Severity**: INFO
- **Finding**: System does not issue or enforce agent identities — there is no authentication mechanism to suspend. The dev-library-application override applies.
- **Implication**: Identity suspension would be handled at the platform layer (API Gateway API key revocation, IAM role deactivation) if authentication is added.
- **Recommendation**: When platform-layer auth is added, ensure API keys can be revoked independently per agent identity.
- **Evidence**: Absence of authentication mechanism

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — and system has no persistent multi-step write workflows. The stateless-utility archetype override applies.
- **Finding**: The online service has no multi-step write workflows requiring compensation. Code generation is a single atomic operation: input spec → output ZIP. There is no partial state to roll back.
- **Implication**: Compensation logic is not applicable for a stateless code-generation operation.
- **Recommendation**: No change needed.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/GenApiController.java`

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No concurrency controls exist. Each code generation request operates independently with no shared mutable state beyond temporary file system writes (unique fileId per request).
- **Implication**: Concurrent requests are naturally isolated by design (each generates to a unique temp directory). No write contention exists.
- **Recommendation**: No change needed for read-only scope.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/GenApiController.java`

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No transaction limits are configured. Code generation is a compute-intensive operation but produces no persistent state changes.
- **Implication**: For read-only agents, blast radius is limited to resource consumption (CPU, disk space for temp files). Rate limiting (STATE-Q5) is the primary control.
- **Recommendation**: If write-enabled scope is adopted, add per-agent limits on concurrent code generation requests.
- **Evidence**: Absence of transaction limit configuration

### DATA-Q1: Sensitive Data Classification

- **Severity**: INFO
- **Finding**: Not a data-handling target. The tool processes OpenAPI specifications provided by callers and generates code. It does not store, process, or transmit PII, PHI, financial records, or credentials. Input specs are processed transiently and discarded after code generation. The `stateless-utility` archetype calibration applies.
- **Implication**: No data classification controls are needed for the code-generation tool itself. Callers are responsible for the sensitivity of their input specifications.
- **Recommendation**: No change needed.
- **Evidence**: Absence of database connections, absence of user data models, transient processing only

### DATA-Q2: Data Residency and Sovereignty ⚡

- **Severity**: INFO
- **Conditional**: No persistent data store and no user-data logging — residency requirements do not apply. The stateless-utility archetype calibration applies.
- **Finding**: The tool holds no persistent data subject to residency constraints. Input specs are processed in memory and discarded.
- **Implication**: Data residency is a caller concern — if callers send regulated specs to the service, they must ensure the service endpoint is in an appropriate region.
- **Recommendation**: Document that callers are responsible for data residency of their input specifications when using the hosted service.
- **Evidence**: Absence of persistent data store, absence of data retention

### DATA-Q6: PII Redaction in Logs

- **Severity**: INFO
- **Finding**: System does not log user data and holds no user data. Default Spring Boot logging captures request metadata (URL, method, status) but not request bodies containing API specifications. The stateless-utility archetype calibration applies.
- **Implication**: PII-in-logs risk is not applicable for a stateless code-generation tool.
- **Recommendation**: No change needed. If request-body logging is ever enabled for debugging, ensure PII redaction is applied.
- **Evidence**: Absence of request-body logging configuration, default Spring Boot logging

### HITL-Q3: Sandbox/Staging Environment

- **Severity**: INFO
- **Finding**: Docker Compose and Dockerfile configurations allow running the service locally for testing. No dedicated staging environment with production-equivalent data shape exists, but for a stateless code-generation tool, "production-equivalent data" is simply any valid OpenAPI specification.
- **Implication**: Local Docker execution serves as an adequate sandbox for testing agent interactions with this tool. The dev-library-application override applies — libraries/CLIs do not own staging environments.
- **Recommendation**: No change needed. Docker-based local execution is sufficient for agent integration testing.
- **Evidence**: `Dockerfile`, `docker-compose.yml`, `.hub.online.dockerfile`, `modules/openapi-generator-online/Dockerfile`

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: PASS
- **Finding**: The online module exposes a documented REST API with well-defined endpoints: GET/POST for `/api/gen/clients/{language}`, GET/POST for `/api/gen/servers/{framework}`, and GET for `/api/gen/download/{fileId}`. Endpoints are annotated with `@ApiOperation` (Springfox) providing descriptions. Runtime Swagger documentation is available at `/api-docs`.
- **Gap**: None — a REST interface exists and is accessible.
- **Recommendation**: None.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/GenApi.java`, `modules/openapi-generator-online/src/main/resources/application.properties`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: Springfox 3.0.0 generates an OpenAPI specification at runtime (`/api-docs`), but no static OpenAPI spec file is committed to the repository.
- **Gap**: No static machine-readable spec available at build time for agent tool generation.
- **Recommendation**: Export and commit the runtime-generated spec as a static `openapi.yaml` file.
- **Evidence**: `modules/openapi-generator-online/pom.xml` (Springfox dependency), absence of static spec file

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: Default Spring Boot error handling provides HTTP status + message. The `ResponseCode` model class exists but no consistent structured error format with retryable classification is implemented across all endpoints.
- **Gap**: No machine-readable error category (retryable vs terminal) in error responses.
- **Recommendation**: Add `@ControllerAdvice` with structured error response format.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/model/ResponseCode.java`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: POST endpoints generate unique artifacts per call. Not idempotent by design.
- **Gap**: No idempotency keys on POST endpoints.
- **Recommendation**: Add idempotency support if write-enabled scope is adopted.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/GenApiController.java`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: JSON responses for metadata, binary ZIP for generated code downloads.
- **Gap**: N/A
- **Recommendation**: No change needed.
- **Evidence**: Controller response annotations

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has operations >30s OR long-running workflows
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has state changes (stateful-crud, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limits documented, no rate limit headers returned.
- **Gap**: Agents cannot self-throttle based on response headers.
- **Recommendation**: Add rate-limit headers when gateway-layer throttling is configured.
- **Evidence**: Absence of rate limit headers in controller code

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: No authentication mechanism exists. The service is designed as a public utility. The dev-library-application override applies — the system does not issue or enforce agent identities.
- **Gap**: No machine identity authentication.
- **Recommendation**: Deploy behind API Gateway with API key or IAM authentication for agent access control.
- **Evidence**: Absence of Spring Security, absence of auth configuration in `modules/openapi-generator-online/pom.xml`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: No authorization model exists. All endpoints equally accessible to all callers.
- **Gap**: Cannot grant read-only access to specific resources without broader privileges.
- **Recommendation**: Add API Gateway with resource-level IAM policies.
- **Evidence**: Absence of any permission model, wide-open CORS

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization. GET (read) and POST (generate) operations have identical access controls (none).
- **Gap**: Cannot restrict an agent to read-only while blocking write operations.
- **Recommendation**: Add method-level authorization at gateway or application layer.
- **Evidence**: Absence of `@PreAuthorize`, `@Secured`, or any role-based checks

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: No identity propagation — no authentication exists. Archetype calibration applies: stateless-utility → INFO.
- **Gap**: N/A for stateless utility.
- **Recommendation**: If multi-tenant deployment is planned, add caller identification at gateway layer.
- **Evidence**: Absence of authentication mechanism

#### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: CI/CD uses GitHub Actions secrets appropriately. No application-level secrets exist.
- **Gap**: None — no application secrets to manage.
- **Recommendation**: No change needed.
- **Evidence**: `.github/workflows/maven-release.yml`, `.github/workflows/docker-release.yml`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: INFO
- **Conditional**: Dev-library-application override — system does not execute agent-invoked write operations with persistent state. Audit logging is a consumer responsibility.
- **Finding**: No audit logging. No persistent state to audit.
- **Gap**: No audit trail for API calls.
- **Recommendation**: Add API Gateway access logging if compliance tracking is needed.
- **Evidence**: Absence of CloudTrail, absence of audit log configuration

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: INFO
- **Finding**: System does not issue or enforce agent identities. Dev-library-application override applies.
- **Gap**: No identity mechanism to suspend.
- **Recommendation**: Handle at platform layer when auth is added.
- **Evidence**: Absence of authentication mechanism

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" and stateless-utility archetype — evaluated as INFO. No persistent multi-step write workflows exist.
- **Finding**: Code generation is atomic and stateless. No partial state to compensate or roll back.
- **Gap**: N/A for stateless operations.
- **Recommendation**: No change needed.
- **Evidence**: Stateless code-generation architecture

#### STATE-Q2: Queryable Current State
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Each request operates independently with unique temp directories. No shared mutable state.
- **Gap**: N/A — natural isolation by design.
- **Recommendation**: No change needed.
- **Evidence**: Independent request processing architecture

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has external dependencies (calls other services or external APIs)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No rate limiting at any layer. POST endpoints are CPU-intensive.
- **Gap**: No protection against runaway agent loops.
- **Recommendation**: Deploy behind API Gateway with usage plans and throttle settings.
- **Evidence**: Absence of rate limiting configuration

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No transaction limits. No persistent state mutations.
- **Gap**: Resource consumption is the only blast radius concern.
- **Recommendation**: Rate limiting (STATE-Q5) is the primary mitigation.
- **Evidence**: Absence of transaction limit configuration

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: INFO
- **Finding**: Docker-based local execution serves as sandbox. Dev-library-application override applies.
- **Gap**: No dedicated staging environment, but not needed for a stateless utility.
- **Recommendation**: No change needed.
- **Evidence**: `Dockerfile`, `docker-compose.yml`, `.hub.online.dockerfile`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification ⚡
- **Severity**: INFO
- **Finding**: Not a data-handling target. Processes transient OpenAPI specs and generates code. No PII/PHI/financial/credential data stored. Stateless-utility archetype calibration applies.
- **Gap**: N/A — no sensitive data handled.
- **Recommendation**: No change needed.
- **Evidence**: Absence of database connections, transient processing model

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO
- **Conditional**: No persistent data store and no user-data logging — residency requirements do not apply.
- **Finding**: No persistent data subject to residency constraints.
- **Gap**: N/A — no data retention.
- **Recommendation**: Document caller responsibility for input spec residency.
- **Evidence**: Absence of persistent data store

#### DATA-Q3: Selective Query Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has list/query endpoints with potentially unbounded results
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q4: System of Record Designations
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q6: PII Redaction in Logs
- **Severity**: INFO
- **Finding**: System does not log user data. Stateless-utility archetype calibration applies.
- **Gap**: N/A — no PII-in-logs risk.
- **Recommendation**: No change needed.
- **Evidence**: Default Spring Boot logging, no request-body logging

#### DATA-Q7: Data Quality Awareness
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Always evaluated as INFO
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: The online service API has no explicit versioning (no `/v1/` prefix, no `Accept-Version` header). No breaking change detection tools are configured. The Springfox-generated spec is runtime-only.
- **Gap**: No API versioning, no breaking change detection in CI. Changes to the GenApi interface could break agent tool bindings without notice.
- **Recommendation**: Add URL-based versioning (e.g., `/v1/api/gen/...`) and integrate OpenAPI diff tooling in CI to detect breaking changes.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/GenApi.java` (no version prefix), absence of contract testing in CI

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Field names in API responses are semantically meaningful and human-readable (e.g., `language`, `framework`, `options`, `cliOptions`). No legacy abbreviations or codes requiring a data dictionary.
- **Gap**: None.
- **Recommendation**: No change needed.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/model/`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Always evaluated as INFO
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: No distributed tracing, no structured JSON logging, no correlation IDs.
- **Gap**: Cannot trace agent-initiated requests through the system.
- **Recommendation**: Add Spring Cloud Sleuth and JSON logging.
- **Evidence**: Absence of tracing/logging dependencies in `modules/openapi-generator-online/pom.xml`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: No alerting configuration. No actuator, no CloudWatch alarms, no monitoring integration.
- **Gap**: Service degradation would go undetected.
- **Recommendation**: Add Spring Boot Actuator and configure alerting.
- **Evidence**: Absence of monitoring configuration

#### OBS-Q3: Business Outcome Metrics
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Always evaluated as INFO
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: N/A
- **Finding**: This is a `application` repository with dev-library-application override. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: N/A
- **Finding**: This is a `application` repository with dev-library-application override. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q3: Rollback Capability
- **Severity**: N/A
- **Finding**: This is a `application` repository with dev-library-application override. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q4: API Test Coverage
- **Severity**: N/A
- **Finding**: This is a `application` repository with dev-library-application override. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: N/A
- **Finding**: This is a `application` repository with dev-library-application override. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/OpenAPI2SpringBoot.java | AUTH-Q2, AUTH-Q3, API-Q1 |
| modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/GenApi.java | API-Q1, DISC-Q1 |
| modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/GenApiController.java | API-Q4, API-Q5, STATE-Q1, STATE-Q3, STATE-Q5 |
| modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/model/ResponseCode.java | API-Q3 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| .github/workflows/maven-release.yml | AUTH-Q5 |
| .github/workflows/docker-release.yml | AUTH-Q5 |
| .circleci/config.yml | (Discovery) |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| Dockerfile | HITL-Q3 |
| docker-compose.yml | HITL-Q3 |
| .hub.online.dockerfile | HITL-Q3 |
| modules/openapi-generator-online/Dockerfile | HITL-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| pom.xml | (Discovery) |
| modules/openapi-generator-online/pom.xml | AUTH-Q1, AUTH-Q2, API-Q2, OBS-Q1, OBS-Q2, STATE-Q5 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| modules/openapi-generator-online/src/main/resources/application.properties | API-Q1, API-Q2, STATE-Q5 |
