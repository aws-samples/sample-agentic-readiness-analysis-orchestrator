# Agentic Readiness Analysis Report

**Target**: OpenAPITools/openapi-generator
**Date**: 2026-04-29
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**Repository Type**: application
**Service Archetype**: stateless-utility (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: java, code-generation, api
**Context**: Code-generation toolkit that produces clients/servers from OpenAPI specs.

**Archetype Justification**: The openapi-generator-online module is a Spring Boot REST API that generates code from OpenAPI specifications. It has no database connections, no persistent state, no cache writes — all data is ephemeral (temp files deleted after download). Classification: stateless-utility.

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 2 | **RISK-SAFETY**: 9 | **RISK-QUALITY**: 10 | **INFOs**: 15

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 2 |
| RISK-SAFETY | 9 |
| RISK-QUALITY | 10 |
| INFO | 15 |
| N/A | 0 |
| Not Evaluated (extended) | 7 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 5 (API-Q5, API-Q6, API-Q8, ENG-Q4, STATE-Q4)
**Extended Questions Not Triggered**: 7 (API-Q7, STATE-Q2, STATE-Q7, DATA-Q3, DATA-Q4, DATA-Q5, ENG-Q5)
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: stateless-utility (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: The openapi-generator-online module has **zero authentication**. No Spring Security dependency exists in `modules/openapi-generator-online/pom.xml`. No OAuth2, API key, mTLS, Cognito, or any authentication mechanism is configured. The `application.properties` contains only SpringFox, port, and Jackson settings — no security configuration. `ApiOriginFilter.java` sets `Access-Control-Allow-Origin: *` and `OpenAPI2SpringBoot.java` configures CORS with `allowedOrigins("*")`. All API endpoints are completely open to anonymous access.
- **Gap**: No machine identity authentication exists. An agent cannot be attributed as a distinct principal. All requests are anonymous — there is no way to distinguish agent calls from human calls or to attribute actions to specific agent identities.
- **Remediation**:
  - **Immediate**: Add Spring Security dependency and configure API key-based authentication as a minimum viable control. Define a `SecurityFilterChain` that requires an API key header (e.g., `X-API-Key`) for all `/api/gen/**` endpoints.
  - **Target State**: OAuth 2.0 client credentials flow with principal attribution in logs, or API key authentication with per-key identity tracking.
  - **Estimated Effort**: Medium (2–4 weeks)
  - **Dependencies**: AUTH-Q2 (scoped permissions), AUTH-Q6 (audit logging), AUTH-Q7 (identity suspension) all depend on having an authentication mechanism first.
- **Evidence**: `modules/openapi-generator-online/pom.xml` (no spring-boot-starter-security), `modules/openapi-generator-online/src/main/resources/application.properties`, `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/ApiOriginFilter.java`, `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/OpenAPI2SpringBoot.java`

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: The `GeneratorInput` model in `GeneratorInput.java` accepts an `AuthorizationValue` object (`io.swagger.v3.parser.core.models.AuthorizationValue`) that can contain API keys, tokens, and credentials. These credentials are passed to the `OpenAPIParser` to fetch remote OpenAPI specifications. No data classification exists for these sensitive fields. No field-level encryption, no PII/credential detection, no access controls prevent any caller from submitting credentials through the API. The data is transient (processed in memory, not persisted to a database), but during processing it exists in memory and could be logged or leaked.
- **Gap**: Sensitive data (user-provided API credentials in `AuthorizationValue`) flows through the system without classification, tagging, or field-level protection. No controls prevent an agent from retrieving or transmitting these credentials. The `AuthorizationValue` field is not marked as sensitive, redacted from logs, or encrypted in transit within the application.
- **Remediation**:
  - **Immediate**: Classify the `AuthorizationValue` field as SENSITIVE/CREDENTIAL. Add `@JsonProperty(access = JsonProperty.Access.WRITE_ONLY)` to prevent credential echo in responses. Ensure `AuthorizationValue` contents are never logged (see DATA-Q6).
  - **Target State**: Field-level sensitivity annotations on `GeneratorInput.authorizationValue`, log redaction for all credential fields, and documentation of data classification policy for the service.
  - **Estimated Effort**: Low (1–2 weeks)
  - **Dependencies**: DATA-Q6 (PII redaction in logs) — credential redaction in logs should be addressed simultaneously.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/model/GeneratorInput.java`, `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/Generator.java`

**Remediation Prioritization:**
1. **AUTH-Q1 first** — Identity before data access. You cannot enforce data access controls or audit agent actions without knowing who is calling.
2. **DATA-Q1 second** — Classify and protect the `AuthorizationValue` credential field. This is a low-effort fix that immediately reduces exposure.
3. **Consider read-only scoping** — Since `agent_scope` is `read-only`, focus initial agent integration on the GET endpoints (`/api/gen/clients`, `/api/gen/servers`, `/api/gen/clients/{language}`, `/api/gen/servers/{framework}`) which do not handle credentials. This unblocks value while POST endpoint security is remediated.

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No authorization model exists. The application has no authentication (AUTH-Q1), so scoped permissions cannot exist. No IAM policies, no role definitions, no API Gateway resource policies, no permission checks in code. All endpoints are equally accessible to all callers.
- **Gap**: An agent identity cannot be granted read-only access to specific resources without inheriting broader privileges. Every caller has full access to every endpoint including code generation (POST) and file download (GET).
- **Compensating Controls**:
  - Deploy behind an API Gateway with IAM-based authorization, restricting agent identity to GET endpoints only.
  - Use a reverse proxy (nginx, Envoy) with path-based access control to limit agent access to read-only endpoints.
- **Remediation Timeline**: 30–60 days (depends on AUTH-Q1 completion)
- **Recommendation**: After implementing AUTH-Q1, define role-based access where agent identities can be scoped to specific endpoint groups (read-only vs. code-generation).
- **Evidence**: `modules/openapi-generator-online/pom.xml` (no spring-boot-starter-security), all source files in `modules/openapi-generator-online/src/main/java/` (no authorization checks)

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization exists. No ABAC, RBAC, fine-grained permission checks, or action-level middleware. Every caller can invoke every operation — GET (list generators, get options), POST (generate client/server code), and GET (download generated files).
- **Gap**: An agent intended for read-only operations (listing supported generators) cannot be prevented from invoking code generation (POST) or downloading arbitrary files (GET /download/{fileId}) at the application layer.
- **Compensating Controls**:
  - Configure API Gateway method-level authorization: allow GET `/api/gen/clients`, GET `/api/gen/servers`, GET `/api/gen/clients/{language}`, GET `/api/gen/servers/{framework}`; deny POST endpoints and GET `/api/gen/download/{fileId}` for agent identities.
  - Use network policies to restrict agent traffic to read-only paths at the load balancer or proxy layer.
- **Remediation Timeline**: 30–60 days (depends on AUTH-Q1 completion)
- **Recommendation**: Implement method-level authorization in Spring Security after AUTH-Q1 is resolved.
- **Evidence**: All source files in `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/` (no `@PreAuthorize`, no `@Secured`, no role checks)

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No audit logging infrastructure exists. The application uses `System.out.println` in `GenApiService.java` for operational logging (file IDs, filenames) and `SLF4J Logger` in `Generator.java` for debug logging (language, generation type). No structured audit logging with principal attribution. No CloudTrail configuration, no CloudWatch log retention policies, no immutable log storage. Logs are unstructured text with no request context.
- **Gap**: No audit trail exists for any API call. Cannot determine who called what endpoint, when, or with what parameters. Agent-initiated actions are indistinguishable from any other caller.
- **Compensating Controls**:
  - Deploy behind an API Gateway with access logging enabled (captures requester IP, request path, response code).
  - Use a reverse proxy (nginx, ALB) with structured access logs forwarded to CloudWatch Logs or S3 with object lock.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add structured logging middleware (Spring's `CommonsRequestLoggingFilter` or a custom `OncePerRequestFilter`) that logs request method, path, authenticated principal (after AUTH-Q1), timestamp, and response status in JSON format. Configure log retention and immutable storage.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java` (System.out.println logging), `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/Generator.java` (SLF4J debug logging), `modules/openapi-generator-online/src/main/resources/application.properties` (no logging configuration)

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No authentication system exists (AUTH-Q1), so there is no mechanism to suspend or revoke agent identities. No API key management, no IAM role deactivation procedures, no user pool management, no token revocation endpoints.
- **Gap**: A misbehaving agent cannot be individually suspended without taking down the entire service or applying network-level blocks (IP banning).
- **Compensating Controls**:
  - Use API Gateway API key management — individual keys can be deleted/disabled immediately.
  - Deploy behind a WAF with IP-based blocking as an emergency measure.
- **Remediation Timeline**: 30–60 days (depends on AUTH-Q1 completion)
- **Recommendation**: When implementing AUTH-Q1, choose an authentication mechanism that supports per-identity revocation (API keys with per-key disable, or OAuth 2.0 with token revocation).
- **Evidence**: `modules/openapi-generator-online/pom.xml` (no security dependencies), all configuration files (no identity management)

#### STATE-Q1: Compensation and Rollback ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No compensation or rollback mechanisms exist. Code generation is functionally atomic — a single POST request produces a zip file stored in a temp directory with a UUID reference in an in-memory `HashMap<String, Generated>`. The `fileMap` static HashMap in `GenApiService.java` has no cleanup mechanism, no TTL, no eviction. Failed code generation throws `ResponseStatusException` but leaves no partial state to roll back (temp files are cleaned up in `Generator.java` after successful zip creation).
- **Gap**: The in-memory `fileMap` grows unboundedly over time (no eviction policy). If a code generation succeeds but the download fails or is never requested, temp files persist on disk. No compensation mechanism for this leak.
- **Compensating Controls**:
  - The stateless-utility nature of the service means the blast radius is limited to temp disk space and memory consumption.
  - Monitor disk usage on the container to detect temp file accumulation.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a TTL-based eviction mechanism to `fileMap` (e.g., Guava `CacheBuilder` with expireAfterWrite) and a scheduled cleanup of orphaned temp files.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java` (`static Map<String, Generated> fileMap = new HashMap<>()`), `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/Generator.java` (temp file management)

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The `Generator.java` class calls external URLs via `new OpenAPIParser().readLocation(opts.getOpenAPIUrl(), ...)` to fetch user-provided OpenAPI specifications. No circuit breakers, no retry logic with backoff, no timeout configuration on the HTTP client used by `OpenAPIParser`. If a user-provided URL is slow or unresponsive, the request thread blocks indefinitely. No resilience libraries (Resilience4j, Spring Retry) are present in `pom.xml`.
- **Gap**: A runaway agent providing URLs to slow or malicious endpoints could exhaust all request threads, causing a denial of service. No circuit breaker prevents cascading failures from external dependency calls.
- **Compensating Controls**:
  - Set JVM-level socket timeouts via system properties (`sun.net.client.defaultConnectTimeout`, `sun.net.client.defaultReadTimeout`).
  - Deploy behind an API Gateway with request timeout configured (e.g., 30-second integration timeout).
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure HTTP client timeouts on the `OpenAPIParser` calls. Add Resilience4j or Spring Retry with circuit breaker pattern for external URL fetching.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/Generator.java` (`new OpenAPIParser().readLocation(opts.getOpenAPIUrl(), ...)`), `modules/openapi-generator-online/pom.xml` (no resilience4j, no spring-retry dependencies)

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No rate limiting exists at any layer. No API Gateway throttling configuration, no WAF rate rules, no application-level rate limiting middleware. The application has no usage plans, no request quotas, no `X-RateLimit-*` headers. The code generation endpoints (POST) are computationally expensive — each request triggers full code generation, file system writes, and zip compression.
- **Gap**: A runaway agent loop could submit unlimited code generation requests at machine speed, exhausting CPU, memory, and disk resources. No protection against agent-initiated traffic storms.
- **Compensating Controls**:
  - Deploy behind an API Gateway with usage plans and throttling (e.g., 10 requests/minute per API key).
  - Use a WAF rate-based rule to limit requests per source IP.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add rate limiting at the infrastructure layer (API Gateway usage plan) or application layer (Spring `bucket4j-spring-boot-starter` or `spring-boot-starter-webflux` with `RateLimiter`).
- **Evidence**: `modules/openapi-generator-online/pom.xml` (no rate-limiting dependencies), all source files (no rate-limit logic), no IaC files (no API Gateway or WAF configuration)

#### DATA-Q2: Data Residency and Sovereignty ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No data residency configuration exists. The service processes user-provided OpenAPI specifications fetched from arbitrary URLs. Generated code artifacts are stored in temporary directories on the local filesystem. No region-specific storage configuration, no GDPR/LGPD references, no data residency policies. The `Dockerfile` and deployment configuration specify no region constraints. All data (input specs, authorization values, generated code) is processed ephemerally.
- **Gap**: If the service is deployed in one region and an agent submits an OpenAPI spec containing regulated data (e.g., EU customer API definitions with GDPR-relevant fields), the data crosses jurisdictions without controls. No data residency documentation or enforcement.
- **Compensating Controls**:
  - Document that the service processes ephemeral technical data only (API specifications) and does not persist regulated personal data.
  - Deploy the service in the same region as the agent to eliminate cross-region data flow.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document data residency posture. If the service will handle specs with regulated content, deploy region-specific instances and configure agents to use the appropriate regional endpoint.
- **Evidence**: `modules/openapi-generator-online/Dockerfile` (no region configuration), `modules/openapi-generator-online/src/main/resources/application.properties` (no residency settings), no IaC files

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: `GenApiService.java` uses `System.out.println` to log file IDs and filenames (`"looking for fileId " + fileId`, `"got filename " + g.getFilename()`). `Generator.java` uses SLF4J to log language and generation type. No log scrubbing middleware, no PII/credential masking libraries. Critically, the `AuthorizationValue` object (which may contain API keys/tokens) is passed to `OpenAPIParser` — if the parser or its dependencies log the authorization header value, credentials would appear in plaintext in logs.
- **Gap**: No redaction mechanism exists for sensitive data in logs. User-provided credentials (`AuthorizationValue`) could be logged by downstream libraries (OpenAPI Parser) without redaction. The application's own logging does not log credentials directly but does not prevent downstream logging either.
- **Compensating Controls**:
  - Configure logback to filter/redact patterns matching API keys, bearer tokens, and authorization headers.
  - Wrap `AuthorizationValue` in a proxy that overrides `toString()` to mask sensitive fields.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a log sanitization filter. Override `toString()` on any model containing credentials. Configure SLF4J/Logback with pattern-based redaction for common credential formats.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java` (System.out.println logging), `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/Generator.java` (SLF4J logging), `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/model/GeneratorInput.java` (AuthorizationValue field)

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No standalone OpenAPI/Swagger spec file is committed to the repository for the online module's API. The `OpenAPIDocumentationConfig.java` configures SpringFox (`@EnableSwagger2`) to generate a Swagger 2.0 spec at runtime, accessible at the `/api-docs` endpoint. The spec is runtime-generated and not version-controlled — it cannot be used for agent tool generation without first running the service.
- **Gap**: Agent frameworks that generate tool definitions from OpenAPI specs cannot consume a spec file from the repository. The spec exists only at runtime, making it impossible to detect breaking changes in CI or auto-generate agent tools from the repo alone.
- **Compensating Controls**:
  - Export the runtime-generated spec (GET `/api-docs`) and commit it as `openapi.json` in the repository.
  - Use SpringDoc (replacement for SpringFox) with Maven plugin to generate the spec at build time.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Migrate from SpringFox (deprecated, Swagger 2.0) to SpringDoc OpenAPI (active, OpenAPI 3.0). Use the `springdoc-openapi-maven-plugin` to generate the spec at build time and commit it to the repository.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/configuration/OpenAPIDocumentationConfig.java` (@EnableSwagger2), `modules/openapi-generator-online/pom.xml` (springfox-swagger2 3.0.0 dependency), no OpenAPI spec files in the repository

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Error responses use Spring's `ResponseStatusException` with HTTP status codes and reason phrases. `Generator.java` throws `ResponseStatusException(HttpStatus.BAD_REQUEST, "No options were supplied")`, `ResponseStatusException(HttpStatus.NOT_FOUND, ...)`, etc. An `ApiResponse` model class exists with error categories (ERROR=1, WARNING=2, INFO=3, OK=4, TOO_BUSY=5) but it is not consistently used in error responses. Most errors return only HTTP status + text reason — no structured JSON error body.
- **Gap**: Agents cannot distinguish retriable errors (timeout, rate limit, server overload) from terminal errors (invalid input, unsupported language). No error code taxonomy, no `retryable` boolean, no machine-readable error category in responses.
- **Compensating Controls**:
  - Build agent-side error classification based on HTTP status codes (4xx = terminal, 5xx = retriable).
  - Wrap responses at the API Gateway layer with structured error bodies.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement a global `@ControllerAdvice` exception handler that returns structured JSON error bodies with `errorCode`, `message`, and `retryable` fields. Use the existing `ApiResponse` model as the base.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/Generator.java` (ResponseStatusException usage), `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/model/ApiResponse.java` (unused error model)

#### API-Q6: Asynchronous Operation Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Code generation runs synchronously in the request thread. The `Generator.generate()` method in `Generator.java` performs spec parsing, code generation, file writing, and zip compression — all within a single HTTP request/response cycle. No background job frameworks (Celery, Bull, SQS workers), no async/polling patterns, no job status APIs, no webhook callbacks. For complex OpenAPI specs, generation could take 30+ seconds.
- **Gap**: Agents calling the code generation endpoints with complex specs may hit HTTP timeout limits. No way to submit a generation job and poll for completion.
- **Compensating Controls**:
  - Configure longer HTTP timeouts at the API Gateway or load balancer for code generation endpoints.
  - Limit agent usage to the GET (list/options) endpoints which are fast.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement async code generation: POST returns a job ID immediately, agent polls GET `/api/gen/status/{jobId}` for completion, then downloads the result.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/Generator.java` (synchronous generation), `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java`

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The `docker-compose.yml` at the repository root is for the documentation site (Docusaurus) only — not for the online generator. `modules/openapi-generator-online/Dockerfile` exists and can be used to build and run the service locally. `GenApiControllerTest.java` uses MockMvc for API testing. No separate staging environment configuration, no environment-specific profiles, no seed data scripts. The service can be run locally via Docker, but there is no production-equivalent staging environment definition.
- **Gap**: No dedicated sandbox or staging environment for testing agent interactions. Agents must be tested against either the local Docker container or the production instance.
- **Compensating Controls**:
  - Use the existing `modules/openapi-generator-online/Dockerfile` to spin up a local test instance.
  - Add a `docker-compose.yml` for the online generator service specifically.
- **Remediation Timeline**: 30 days
- **Recommendation**: Create a `docker-compose.yml` (or extend the existing one) that includes the openapi-generator-online service. Add a staging environment profile in `application.properties` for non-production testing.
- **Evidence**: `docker-compose.yml` (Docusaurus only), `modules/openapi-generator-online/Dockerfile`, `modules/openapi-generator-online/src/test/java/org/openapitools/codegen/online/api/GenApiControllerTest.java`

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No API versioning exists. Endpoints are at `/api/gen/...` with no version prefix (`/v1/`, `/v2/`). No `Accept-Version` headers. The Maven project version is `7.22.0-SNAPSHOT` but this is a project version, not an API contract version. No breaking change detection tools in CI. No consumer-driven contract tests (Pact). The SpringFox-generated spec is not version-controlled, so changes to the API surface cannot be tracked.
- **Gap**: Agent tool bindings could break silently when API behavior changes. No mechanism to detect or prevent breaking changes to the agent-facing API surface.
- **Compensating Controls**:
  - Pin the agent tool definition to a specific Docker image tag (e.g., `openapitools/openapi-generator-online:v7.21.0`).
  - Export and commit the OpenAPI spec to enable diff-based breaking change detection in CI.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add API versioning (URL prefix `/v1/` or header-based). Commit the OpenAPI spec and add an OpenAPI diff check in the GitHub Actions CI pipeline.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/GenApiController.java` (`@RequestMapping("/api")`), `.github/workflows/openapi-generator.yaml` (no contract testing step), `pom.xml` (project version 7.22.0-SNAPSHOT)

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No distributed tracing exists. No OpenTelemetry SDK, no X-Ray instrumentation, no `traceparent` header propagation. Logging uses `SLF4J Logger` in `Generator.java` and `System.out.println` in `GenApiService.java`. Logs are unstructured text — not JSON. No correlation IDs, no request IDs. No Logback configuration file in the online module. Spring Boot's default console logging is active.
- **Gap**: Agent-initiated requests cannot be traced through the system. When a code generation request fails, there is no correlation ID to reconstruct what happened. Logs are unstructured and cannot be queried efficiently.
- **Compensating Controls**:
  - Add Spring Boot's built-in MDC (Mapped Diagnostic Context) with a request-scoped UUID for basic correlation.
  - Deploy behind an API Gateway or ALB that injects trace headers.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `spring-boot-starter-actuator` for health/metrics endpoints. Configure structured JSON logging via Logback. Add MDC-based correlation IDs. Consider adding OpenTelemetry for distributed tracing.
- **Evidence**: `modules/openapi-generator-online/pom.xml` (no actuator, no tracing dependencies), `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/Generator.java` (SLF4J), `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java` (System.out.println)

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No alerting infrastructure exists. No CloudWatch alarms, no anomaly detection, no PagerDuty/OpsGenie integration, no SLO-based alerting. No Spring Boot Actuator (`spring-boot-starter-actuator` not in `pom.xml`), so no metrics endpoints are available. No monitoring dashboard configuration.
- **Gap**: Degradation of the code generation service (high error rates, increased latency) would not be detected until agents begin failing. No proactive alerting exists.
- **Compensating Controls**:
  - Monitor Docker container health checks and restart policies.
  - Use API Gateway-level metrics (if deployed behind one) for basic error rate and latency alerting.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `spring-boot-starter-actuator` for Prometheus-compatible metrics. Configure CloudWatch or Prometheus alerting on error rates (5xx > threshold) and latency (p99 > threshold).
- **Evidence**: `modules/openapi-generator-online/pom.xml` (no actuator dependency), no IaC files (no CloudWatch alarm configuration)

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No Infrastructure-as-Code files exist in the repository. No Terraform, CloudFormation, CDK, Helm charts, or Kustomize files. The deployment artifact is a Docker image published to DockerHub via GitHub Actions (`docker-release.yml`). The `Dockerfile` and `.hub.online.dockerfile` define the container build but not the deployment infrastructure (no API Gateway, no IAM roles, no networking configuration).
- **Gap**: The agent-facing integration surface (API gateway, IAM roles, secrets, network configuration) is not defined as code, not subject to peer review, and cannot be monitored for drift. Infrastructure changes are manual and unauditable.
- **Compensating Controls**:
  - Docker image versioning provides some deployment governance (tagged releases via `docker-release.yml`).
  - GitHub Actions workflows provide CI/CD automation for builds.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Define deployment infrastructure as code (Terraform or CDK) including API Gateway configuration, IAM roles, and networking. Integrate IaC changes into the existing GitHub Actions pipeline with plan/review steps.
- **Evidence**: No IaC files in repository, `.github/workflows/docker-release.yml` (Docker image publishing), `modules/openapi-generator-online/Dockerfile`

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Extensive CI/CD exists: GitHub Actions (`openapi-generator.yaml` with build, test, docs verification, samples verification), CircleCI (`.circleci/config.yml` with parallel test nodes), Docker build testing (`docker.yaml`), release workflows (`docker-release.yml`, `maven-release.yml`). Dependabot is configured for GitHub Actions and Maven dependencies. Unit tests exist including `GenApiControllerTest.java` with MockMvc API tests. However, no API contract testing (no Pact, no OpenAPI spec validation in build, no breaking change detection for the online module's API).
- **Gap**: API changes that break agent tool bindings are not caught in the CI pipeline. The extensive test suite validates functionality but not API contract stability.
- **Compensating Controls**:
  - The existing MockMvc tests in `GenApiControllerTest.java` partially cover API behavior (status codes, content types, JSON paths).
  - Pin agent tools to specific Docker image tags to avoid unexpected API changes.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add an OpenAPI spec validation step to the CI pipeline: generate the spec at build time, diff against the committed spec, and fail on breaking changes.
- **Evidence**: `.github/workflows/openapi-generator.yaml`, `.circleci/config.yml`, `.github/workflows/docker.yaml`, `modules/openapi-generator-online/src/test/java/org/openapitools/codegen/online/api/GenApiControllerTest.java`

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Docker images are published to DockerHub with version tags. The `docker-release.yml` workflow creates tagged images on `v*` Git tags (e.g., `openapitools/openapi-generator-online:v7.21.0`) and a `latest` tag on master pushes. This provides a basic rollback mechanism — switch to a previous tagged image. However, no blue/green deployment, no CodeDeploy rollback triggers, no canary deployment with automatic rollback, no feature flags.
- **Gap**: Rollback requires manual intervention to switch Docker image tags. No automated rollback based on health checks or error rates. Rollback time depends on deployment infrastructure (not defined in this repo).
- **Compensating Controls**:
  - Docker image tag versioning allows manual rollback to any previous version.
  - Maven Central artifact versioning provides an additional rollback path for library consumers.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: When defining deployment IaC (ENG-Q1), include blue/green or canary deployment with automatic rollback triggers based on health check failures.
- **Evidence**: `.github/workflows/docker-release.yml` (tag-based Docker image publishing), `.github/workflows/maven-release.yml`

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO
- **Finding**: The openapi-generator-online module exposes a well-documented REST API via Spring MVC. `GenApi.java` defines the interface with Swagger2 annotations (`@ApiOperation`, `@ApiResponses`, `@ApiParam`). `GenApiController.java` maps endpoints under `/api`. Endpoints: GET `/api/gen/clients`, GET `/api/gen/servers`, POST `/api/gen/clients/{language}`, POST `/api/gen/servers/{framework}`, GET `/api/gen/clients/{language}`, GET `/api/gen/servers/{framework}`, GET `/api/gen/download/{fileId}`. The API is REST-based with JSON responses. No direct database access, no file-based exchange, no UI automation required.
- **Implication**: The API surface is well-suited for agent tool integration. Agents can bind to the documented REST endpoints directly. The existing Swagger2 annotations provide self-documentation at runtime.
- **Recommendation**: No immediate action needed. The API surface is the minimum viable integration layer for agents.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/GenApi.java`, `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/GenApiController.java`

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: POST endpoints (`generateClient`, `generateServerForLanguage`) are not idempotent. Each call generates a new UUID code and new temporary files — repeating the same request produces a different result (new UUID, new files). No idempotency key support. The `getResponse()` method in `GenApiService.java` creates `UUID.randomUUID().toString()` for each request.
- **Implication**: If agent scope is expanded to write-enabled in the future, idempotency must be addressed before deployment. For the current read-only scope, this is informational only.
- **Recommendation**: For future write-enabled scope: implement idempotency keys based on a hash of (language + spec content + options) to detect duplicate generation requests.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java` (`UUID.randomUUID().toString()`)

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: API responses are JSON (Spring MVC default with Jackson serialization). The `ResponseCode` model returns `{code, link}` as JSON. The download endpoint (`/api/gen/download/{fileId}`) returns `application/zip` (binary). Client/server option endpoints return JSON maps of `CliOption` objects. `application.properties` configures Jackson date formatting.
- **Implication**: JSON responses are well-suited for LLM consumption. The binary zip download requires separate handling in agent tools (download as file, not parse as text).
- **Recommendation**: No action needed. The JSON format is optimal for agent consumption.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/model/ResponseCode.java`, `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java`, `modules/openapi-generator-online/src/main/resources/application.properties`

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limits are documented. No `X-RateLimit-Remaining`, `X-RateLimit-Limit`, or `Retry-After` headers are returned by any endpoint. No API Gateway usage plans or WAF rate rules exist. No rate limit documentation in README or API docs.
- **Implication**: Agents have no way to self-throttle. Without rate limit headers, agent frameworks cannot implement adaptive backoff. This becomes critical when STATE-Q5 (rate limiting) is implemented — the limits should be communicated via headers.
- **Recommendation**: When implementing rate limiting (STATE-Q5), include `X-RateLimit-Remaining`, `X-RateLimit-Limit`, and `Retry-After` headers in responses so agents can self-throttle.
- **Evidence**: All source files in `modules/openapi-generator-online/src/main/java/` (no rate limit headers), `modules/openapi-generator-online/pom.xml` (no rate-limiting dependencies)

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: INFO
- **Finding**: No identity propagation exists. No JWT parsing middleware, no OAuth2 token exchange, no on-behalf-of flows. All requests are anonymous. No user context headers.
- **Implication**: For a stateless-utility service processing technical API specifications, identity propagation is not critical. The service does not hold user-specific data and all operations produce the same result regardless of caller identity. Downgraded to INFO for stateless-utility archetype.
- **Recommendation**: No immediate action needed for this archetype. If the service is extended to handle user-specific configurations, identity propagation should be revisited.
- **Evidence**: All source files in `modules/openapi-generator-online/src/main/java/` (no identity/auth logic)

### AUTH-Q5: Credential Management

- **Severity**: INFO
- **Finding**: No secrets management system is used. The only environment variable is `GENERATOR_HOST` (non-sensitive, used for URL construction in `GenApiService.java` and `OpenAPIDocumentationConfig.java`). No hardcoded credentials found in the online module source code. `.envrc` contains only `has nix && use flake`. No `.env` files with secrets committed. The `docker-release.yml` and `maven-release.yml` workflows use GitHub Secrets for DockerHub and Maven Central credentials (`DOCKER_USERNAME`, `DOCKER_PASSWORD`, `GPG_PRIVATE_KEY`, `GPG_PASSPHRASE`, `OSS_USERNAME`, `OSS_PASSWORD`).
- **Implication**: The application itself does not handle secrets — it's a stateless code generator. CI/CD secrets are managed through GitHub Secrets, which is acceptable. No credential management concern for the runtime application. Evaluated as INFO because there are no application-level secrets to manage.
- **Recommendation**: No action needed for the application. Ensure GitHub Secrets are rotated periodically for CI/CD credentials.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java` (`System.getenv("GENERATOR_HOST")`), `.envrc`, `.github/workflows/docker-release.yml` (GitHub Secrets usage), `.github/workflows/maven-release.yml`

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No concurrency controls exist. The `fileMap` in `GenApiService.java` is a `static HashMap` (not `ConcurrentHashMap`). Multiple concurrent code generation requests could race on the `fileMap.put()` operation, potentially losing entries. The `getTmpFolder()` in `Generator.java` uses `Files.createTempDirectory()` which is inherently safe for concurrent calls (unique directory per call).
- **Implication**: For read-only agent scope, concurrency concerns are limited to the GET endpoints which are stateless and thread-safe (they read from immutable static lists). Concurrency issues in the POST endpoints are informational for read-only scope.
- **Recommendation**: For future write-enabled scope: replace `HashMap` with `ConcurrentHashMap` for `fileMap` to prevent race conditions.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java` (`static Map<String, Generated> fileMap = new HashMap<>()`)

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits exist. No per-agent limits on records modified, spend, or delete operations. The service is a code generator — the primary "transaction" is generating a code package, which consumes CPU and disk space but does not modify business data.
- **Implication**: For read-only agent scope, transaction limits are not applicable. For future write-enabled scope, limits on concurrent code generation jobs and disk usage would be relevant.
- **Recommendation**: No action needed for read-only scope. If expanding to write-enabled, implement limits on concurrent code generation requests per agent identity.
- **Evidence**: All source files in `modules/openapi-generator-online/src/main/java/` (no transaction limit logic)

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No draft/pending state concept exists. Code generation produces a final zip file immediately — there is no two-phase commit pattern, no approval workflow, no draft state. The service is designed for immediate output.
- **Implication**: For read-only agent scope, draft states are not needed. For future write-enabled scope, a two-phase pattern (submit spec → review generated code → confirm download) could provide human oversight for production code generation.
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java`

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable approval gates exist. No approval API endpoints, no status-based workflows requiring explicit confirmation, no Step Functions with human approval tasks. All operations execute immediately.
- **Implication**: For read-only agent scope, approval gates are not applicable. For future write-enabled scope, approval gates on code generation (particularly when used in automated deployment pipelines) would be valuable.
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: All source files in `modules/openapi-generator-online/src/main/java/` (no approval logic)

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality scores or completeness metrics exist. The service does not maintain a persistent dataset — it processes user-provided OpenAPI specifications and generates code. Data quality is inherently a function of the input spec provided by the caller, not of data the service owns.
- **Implication**: Agent-side validation of OpenAPI spec quality (completeness, correctness) would improve generation outcomes. The service itself does basic validation via `OpenAPIParser` (returns null for invalid specs).
- **Recommendation**: Document that the service validates input specs via the OpenAPI Parser and returns 400 for invalid specs. Consider adding a "spec quality score" endpoint that evaluates an OpenAPI spec without generating code.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/Generator.java` (OpenAPI validation: `if (openapi == null) throw ResponseStatusException(HttpStatus.BAD_REQUEST, ...)`)

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Field names are semantically meaningful throughout the codebase. API parameters use clear names: `language`, `framework`, `generatorInput`, `fileId`. Model fields: `code`, `link`, `spec`, `options`, `openAPIUrl`, `authorizationValue`, `openapiNormalizer`, `filename`, `friendlyName`. No legacy abbreviations or cryptic codes. The `ResponseCode` model has descriptive `@ApiModelProperty` annotations with examples.
- **Implication**: LLM-based agents can interpret field names without a data dictionary. The clear naming convention reduces the risk of agent misinterpretation.
- **Recommendation**: Maintain current naming conventions. No action needed.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/model/GeneratorInput.java`, `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/model/ResponseCode.java`

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No formal data catalog or metadata layer exists. No AWS Glue Data Catalog, no Collibra, no Alation, no DataHub. The SpringFox-generated Swagger UI serves as a runtime API catalog. The `website/` directory contains a Docusaurus documentation site. `README.md` provides extensive project documentation.
- **Implication**: When building agent tools, the runtime Swagger UI and README serve as the primary reference. No programmatic metadata layer exists for automated tool discovery.
- **Recommendation**: The runtime Swagger UI is sufficient for this service's scope. Committing the OpenAPI spec (see API-Q2) would provide a programmatic metadata source.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/configuration/OpenAPIDocumentationConfig.java` (Swagger UI configuration), `README.md`, `website/` directory

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No custom business metrics exist. No `cloudwatch.put_metric_data`, no Prometheus counters, no business KPI dashboards. No Spring Boot Actuator dependency — `/actuator/metrics` is not available. The service logs generation events via `System.out.println` but does not track metrics (generation success rate, language popularity, generation duration, error rates by language).
- **Implication**: When agents consume this service, there will be no visibility into whether agent-initiated code generation produces successful outcomes. Business metrics (generation success rate by language, average generation time, error rate) would enable quality-of-service monitoring.
- **Recommendation**: Add `spring-boot-starter-actuator` and custom Micrometer counters for: generation requests by language, generation success/failure rate, generation duration (histogram).
- **Evidence**: `modules/openapi-generator-online/pom.xml` (no actuator dependency), `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java` (no metrics instrumentation)

### ENG-Q4: API Test Coverage

- **Severity**: INFO
- **Finding**: `GenApiControllerTest.java` contains comprehensive MockMvc API tests covering all major endpoints: `clientLanguages()`, `serverFrameworks()`, `clientOptions()`, `clientOptionsUnknown()`, `serverOptions()`, `serverOptionsUnknown()`, `generateClient()`, `generateServer()`, `generateWIthForwardedHeaders()`, `generateClientWithInvalidOpenAPIUrl()`, `generateWithOpenAPINormalizer()`. Tests validate status codes, content types, JSON path values, and response structure. The `generateAndDownload()` helper method tests the full generate-then-download flow. Evaluated as INFO for stateless-utility archetype.
- **Implication**: Good test coverage for the agent-facing API. The MockMvc tests validate the key agent interaction patterns (list generators, get options, generate code, download result). Missing: negative test cases for malformed JSON input, boundary testing for very large specs.
- **Recommendation**: Add edge case tests: malformed JSON input, very large OpenAPI specs, concurrent generation requests, missing required fields.
- **Evidence**: `modules/openapi-generator-online/src/test/java/org/openapitools/codegen/online/api/GenApiControllerTest.java`

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: The openapi-generator-online module exposes a documented REST API via Spring MVC with Swagger2 annotations. 7 endpoints defined in `GenApi.java`: GET `/api/gen/clients`, GET `/api/gen/servers`, POST `/api/gen/clients/{language}`, POST `/api/gen/servers/{framework}`, GET `/api/gen/clients/{language}`, GET `/api/gen/servers/{framework}`, GET `/api/gen/download/{fileId}`. No direct database access, file-based exchange, or UI automation patterns detected.
- **Gap**: No gap — documented REST API exists.
- **Recommendation**: No action needed.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/GenApi.java`, `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/GenApiController.java`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: No standalone OpenAPI/Swagger spec file committed. SpringFox (`@EnableSwagger2`) generates spec at runtime at `/api-docs`. Spec is not version-controlled.
- **Gap**: No committed machine-readable spec for offline tool generation or CI-based contract testing.
- **Recommendation**: Migrate to SpringDoc OpenAPI and generate spec at build time via Maven plugin. Commit as `openapi.json`.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/configuration/OpenAPIDocumentationConfig.java`, `modules/openapi-generator-online/pom.xml`

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: Errors use `ResponseStatusException` with HTTP status + text reason. `ApiResponse` model exists (ERROR/WARNING/INFO/OK/TOO_BUSY codes) but is not used consistently in error paths. No structured JSON error body with retryable classification.
- **Gap**: Agents cannot distinguish retriable from terminal errors programmatically.
- **Recommendation**: Implement `@ControllerAdvice` exception handler returning structured JSON with `errorCode`, `message`, `retryable` fields.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/Generator.java`, `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/model/ApiResponse.java`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: POST endpoints not idempotent — each call generates new UUID and temp files. No idempotency key support.
- **Gap**: No idempotency controls (informational for read-only scope).
- **Recommendation**: For future write-enabled scope, add idempotency keys.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: Responses are JSON (Jackson). Download endpoint returns `application/zip`. Structured JSON for all metadata endpoints.
- **Gap**: N/A
- **Recommendation**: No action needed.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/model/ResponseCode.java`, `modules/openapi-generator-online/src/main/resources/application.properties`

#### API-Q6: Asynchronous Operation Support
- **Severity**: RISK-QUALITY
- **Finding**: Code generation runs synchronously. No async patterns, job queues, or polling endpoints. Complex specs could take 30+ seconds.
- **Gap**: No async operation support for long-running code generation.
- **Recommendation**: Implement async generation with job status polling.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/Generator.java`

#### API-Q7: Event Emission for State Changes
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has state changes (stateful-crud, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limits documented. No `X-RateLimit-*` headers returned. No API Gateway usage plans.
- **Gap**: Agents have no way to discover or self-throttle against rate limits.
- **Recommendation**: When implementing rate limiting (STATE-Q5), include standard rate limit headers.
- **Evidence**: All source files in `modules/openapi-generator-online/src/main/java/`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: Zero authentication. No Spring Security, no OAuth2, no API keys, no mTLS. CORS allows all origins. All endpoints completely open.
- **Gap**: No machine identity authentication. Agent calls cannot be attributed.
- **Recommendation**: Add Spring Security with API key authentication as minimum viable control.
- **Evidence**: `modules/openapi-generator-online/pom.xml`, `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/ApiOriginFilter.java`, `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/OpenAPI2SpringBoot.java`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: No authorization model. No IAM policies, no role definitions, no permission checks. All endpoints equally accessible.
- **Gap**: Cannot grant agent identity read-only access without broader privileges.
- **Recommendation**: Implement role-based access after AUTH-Q1.
- **Evidence**: `modules/openapi-generator-online/pom.xml`, all source files (no authorization logic)

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization. No ABAC, RBAC, or permission middleware.
- **Gap**: Cannot restrict agent to read operations while blocking write operations at the application layer.
- **Recommendation**: Implement method-level authorization in Spring Security.
- **Evidence**: All source files in `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: No identity propagation. All requests anonymous. Downgraded to INFO for stateless-utility archetype.
- **Gap**: No identity propagation (acceptable for stateless-utility processing public/reference data).
- **Recommendation**: No action needed for current archetype.
- **Evidence**: All source files (no auth logic)

#### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: No application-level secrets. Only env var is `GENERATOR_HOST` (non-sensitive). CI/CD credentials managed via GitHub Secrets. No hardcoded credentials found.
- **Gap**: No gap — no application-level secrets to manage.
- **Recommendation**: No action needed.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java`, `.envrc`, `.github/workflows/docker-release.yml`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No audit logging. `System.out.println` and SLF4J debug logging only. No structured audit logging, no principal attribution, no immutable log storage.
- **Gap**: No audit trail for any API call. Agent actions indistinguishable from other callers.
- **Recommendation**: Add structured logging middleware with JSON format, principal attribution, and immutable log storage.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java`, `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/Generator.java`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: No authentication system → no identity suspension mechanism. No API key revocation, no token invalidation.
- **Gap**: Cannot suspend a misbehaving agent without taking down the entire service.
- **Recommendation**: Choose auth mechanism (AUTH-Q1) that supports per-identity revocation.
- **Evidence**: `modules/openapi-generator-online/pom.xml` (no security dependencies)

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No compensation/rollback. Code generation is atomic (single request). `fileMap` (HashMap) grows unboundedly with no TTL/eviction.
- **Gap**: Orphaned temp files and unbounded in-memory map entries.
- **Recommendation**: Add TTL-based eviction to `fileMap` and scheduled temp file cleanup.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java`

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
- **Finding**: `fileMap` is `HashMap` (not thread-safe). GET endpoints read from immutable static lists (thread-safe).
- **Gap**: Race conditions on `fileMap` for POST endpoints (informational for read-only scope).
- **Recommendation**: Replace `HashMap` with `ConcurrentHashMap` for future write-enabled scope.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: External URL calls via `OpenAPIParser.readLocation()` have no circuit breakers, no retry logic, no timeouts. No resilience libraries in pom.xml.
- **Gap**: Slow/malicious external URLs can exhaust request threads.
- **Recommendation**: Add HTTP client timeouts and Resilience4j circuit breaker for external URL fetching.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/Generator.java`, `modules/openapi-generator-online/pom.xml`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No rate limiting at any layer. Code generation endpoints are computationally expensive.
- **Gap**: Unlimited agent requests at machine speed can exhaust resources.
- **Recommendation**: Add rate limiting at API Gateway or application layer.
- **Evidence**: `modules/openapi-generator-online/pom.xml`, all source files

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits. Service generates code — no business data modification.
- **Gap**: No transaction limits (informational for read-only scope).
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: All source files

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No draft/pending state. Code generation produces final zip immediately. No two-phase commit pattern.
- **Gap**: No draft state (informational for read-only scope).
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java`

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable approval gates. No approval endpoints, no confirmation workflows.
- **Gap**: No approval gates (informational for read-only scope).
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: All source files in `modules/openapi-generator-online/src/main/java/`

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: `docker-compose.yml` is for Docusaurus docs site only. `modules/openapi-generator-online/Dockerfile` exists for local testing. MockMvc tests in `GenApiControllerTest.java`. No staging environment config, no environment profiles.
- **Gap**: No dedicated sandbox/staging for agent testing.
- **Recommendation**: Create a docker-compose config for the online generator service.
- **Evidence**: `docker-compose.yml`, `modules/openapi-generator-online/Dockerfile`, `modules/openapi-generator-online/src/test/java/org/openapitools/codegen/online/api/GenApiControllerTest.java`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: `GeneratorInput.java` accepts `AuthorizationValue` containing API keys/tokens/credentials. No data classification, no field-level encryption, no access controls on credential fields.
- **Gap**: Sensitive credentials flow through system without classification or protection.
- **Recommendation**: Classify `AuthorizationValue` as SENSITIVE/CREDENTIAL. Prevent credential echo in responses. Add log redaction.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/model/GeneratorInput.java`, `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/Generator.java`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No data residency configuration. Service processes OpenAPI specs from arbitrary URLs. All data ephemeral. No region constraints in deployment config.
- **Gap**: No data residency documentation or enforcement.
- **Recommendation**: Document data residency posture. Deploy region-specific instances if needed.
- **Evidence**: `modules/openapi-generator-online/Dockerfile`, `modules/openapi-generator-online/src/main/resources/application.properties`

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
- **Severity**: RISK-SAFETY
- **Finding**: `System.out.println` logging in `GenApiService.java`. SLF4J in `Generator.java`. No log scrubbing. `AuthorizationValue` credentials could be logged by downstream libraries.
- **Gap**: No PII/credential redaction in logs.
- **Recommendation**: Add log sanitization filter and `toString()` override for credential models.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java`, `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/Generator.java`, `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/model/GeneratorInput.java`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics. Service processes user-provided specs — data quality is a function of input, not of data the service owns. OpenAPI Parser validates specs and returns 400 for invalid ones.
- **Gap**: No data quality scoring (expected for a stateless code generation tool).
- **Recommendation**: Consider adding a spec quality/validation endpoint.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/Generator.java`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: No API versioning (`/v1/`, `/v2/`). No `Accept-Version` headers. No breaking change detection in CI. No contract tests. SpringFox spec not version-controlled.
- **Gap**: Agent tool bindings could break silently on API changes.
- **Recommendation**: Add API versioning and OpenAPI spec diffing in CI.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/GenApiController.java`, `.github/workflows/openapi-generator.yaml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Field names are semantically meaningful: `language`, `framework`, `generatorInput`, `fileId`, `code`, `link`, `spec`, `options`, `openAPIUrl`, `authorizationValue`, `openapiNormalizer`. No legacy abbreviations.
- **Gap**: No gap — good naming conventions.
- **Recommendation**: Maintain current naming conventions.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/model/GeneratorInput.java`, `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/model/ResponseCode.java`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal data catalog. SpringFox Swagger UI as runtime API catalog. Docusaurus documentation site in `website/`.
- **Gap**: No programmatic metadata layer for automated tool discovery.
- **Recommendation**: Commit OpenAPI spec (see API-Q2) for programmatic access.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/configuration/OpenAPIDocumentationConfig.java`, `README.md`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: No distributed tracing (no OTEL, no X-Ray). Logging is unstructured text (SLF4J + System.out.println). No correlation IDs. No Logback configuration in online module.
- **Gap**: Agent-initiated requests cannot be traced or correlated.
- **Recommendation**: Add structured JSON logging via Logback, MDC correlation IDs, and consider OpenTelemetry.
- **Evidence**: `modules/openapi-generator-online/pom.xml`, `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/Generator.java`, `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: No alerting infrastructure. No CloudWatch alarms, no PagerDuty, no Actuator metrics. No monitoring dashboards.
- **Gap**: Service degradation would not be detected proactively.
- **Recommendation**: Add `spring-boot-starter-actuator` and configure alerting on error rates and latency.
- **Evidence**: `modules/openapi-generator-online/pom.xml`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics. No Actuator, no Prometheus counters, no KPI dashboards. Generation events logged via System.out.println without metrics.
- **Gap**: No visibility into agent-initiated code generation outcomes.
- **Recommendation**: Add Micrometer counters for generation requests, success/failure rates, and duration.
- **Evidence**: `modules/openapi-generator-online/pom.xml`, `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK-QUALITY
- **Finding**: No IaC files. Deployment artifact is Docker image on DockerHub via GitHub Actions. No API Gateway, IAM, or networking defined as code.
- **Gap**: Agent-facing integration surface not defined as code, not peer-reviewed, no drift detection.
- **Recommendation**: Define deployment infrastructure as IaC (Terraform/CDK).
- **Evidence**: No IaC files in repository, `.github/workflows/docker-release.yml`, `modules/openapi-generator-online/Dockerfile`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: Extensive CI/CD (GitHub Actions, CircleCI, Dependabot). MockMvc API tests exist. No API contract testing (no Pact, no OpenAPI diff, no breaking change detection).
- **Gap**: API breaking changes not caught in CI pipeline.
- **Recommendation**: Add OpenAPI spec validation step to CI.
- **Evidence**: `.github/workflows/openapi-generator.yaml`, `.circleci/config.yml`, `modules/openapi-generator-online/src/test/java/org/openapitools/codegen/online/api/GenApiControllerTest.java`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: Docker images published with version tags on `v*` Git tags. Basic rollback via image tag switching. No blue/green, no canary, no automated rollback.
- **Gap**: Manual rollback only. No automated rollback on health check failures.
- **Recommendation**: Add automated rollback when defining deployment IaC.
- **Evidence**: `.github/workflows/docker-release.yml`, `.github/workflows/maven-release.yml`

#### ENG-Q4: API Test Coverage
- **Severity**: INFO
- **Finding**: `GenApiControllerTest.java` has comprehensive MockMvc tests covering all endpoints: list generators, get options, generate client/server, download, forwarded headers, invalid URL, OpenAPI normalizer. Evaluated as INFO for stateless-utility archetype.
- **Gap**: Missing edge case tests (malformed JSON, large specs, concurrent requests).
- **Recommendation**: Add edge case and boundary tests.
- **Evidence**: `modules/openapi-generator-online/src/test/java/org/openapitools/codegen/online/api/GenApiControllerTest.java`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent data stores
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/GenApi.java` | API-Q1, API-Q2, DISC-Q1 |
| `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/GenApiController.java` | API-Q1, DISC-Q1 |
| `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/GenApiDelegate.java` | API-Q1 |
| `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/ApiOriginFilter.java` | AUTH-Q1 |
| `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/OpenAPI2SpringBoot.java` | AUTH-Q1 |
| `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java` | API-Q4, API-Q5, API-Q6, AUTH-Q5, AUTH-Q6, STATE-Q1, STATE-Q3, STATE-Q5, DATA-Q6, OBS-Q1, OBS-Q3, HITL-Q1 |
| `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/Generator.java` | API-Q3, API-Q6, AUTH-Q6, STATE-Q4, DATA-Q1, DATA-Q6, DATA-Q7, OBS-Q1 |
| `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/ZipUtil.java` | API-Q6 |
| `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/model/GeneratorInput.java` | DATA-Q1, DATA-Q6, DISC-Q2 |
| `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/model/ResponseCode.java` | API-Q5, DISC-Q2 |
| `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/model/ApiResponse.java` | API-Q3 |
| `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/model/Generated.java` | STATE-Q1 |
| `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/configuration/OpenAPIDocumentationConfig.java` | API-Q2, AUTH-Q5, DISC-Q3 |
| `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/configuration/ParameterAllowableValuesPlugin.java` | API-Q2 |
| `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/configuration/HomeController.java` | API-Q1 |
| `modules/openapi-generator-online/src/test/java/org/openapitools/codegen/online/api/GenApiControllerTest.java` | HITL-Q3, ENG-Q2, ENG-Q4 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/openapi-generator.yaml` | ENG-Q2, DISC-Q1 |
| `.github/workflows/docker.yaml` | ENG-Q2 |
| `.github/workflows/docker-release.yml` | AUTH-Q5, ENG-Q1, ENG-Q3 |
| `.github/workflows/maven-release.yml` | AUTH-Q5, ENG-Q3 |
| `.circleci/config.yml` | ENG-Q2 |
| `.github/dependabot.yml` | ENG-Q2 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `Dockerfile` | ENG-Q1 |
| `modules/openapi-generator-online/Dockerfile` | DATA-Q2, ENG-Q1, HITL-Q3 |
| `.hub.online.dockerfile` | ENG-Q1 |
| `.hub.cli.dockerfile` | ENG-Q1 |
| `docker-compose.yml` | HITL-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `pom.xml` | DISC-Q1, ENG-Q2 |
| `modules/openapi-generator-online/pom.xml` | AUTH-Q1, AUTH-Q2, AUTH-Q7, API-Q2, STATE-Q4, STATE-Q5, OBS-Q1, OBS-Q2, OBS-Q3 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `modules/openapi-generator-online/src/main/resources/application.properties` | AUTH-Q1, AUTH-Q6, API-Q5, DATA-Q2 |
| `.envrc` | AUTH-Q5 |
