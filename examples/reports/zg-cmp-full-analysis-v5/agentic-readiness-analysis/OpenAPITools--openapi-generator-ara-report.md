# Agentic Readiness Analysis Report

**Target**: OpenAPITools/openapi-generator
**Date**: 2026-04-30
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**TD Version**: 3g1ipe93e5d2wb6n5d4yqaf9
**Repository Type**: application
**Service Archetype**: stateless-utility (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: java, code-generation, api
**Context**: Code-generation toolkit that produces clients/servers from OpenAPI specs.

**Archetype Justification**: The repository is a code-generation toolkit (library + CLI + optional web wrapper). The online module has no persistent data store, no database connections, no message queues, and performs stateless code generation to temporary files — consistent with stateless-utility.

**Surface flags**:
- has_persistent_data_store: false
- has_http_rpc_surface: true
- has_auth_surface: false
- has_write_operations: true
- has_logging_of_user_data: false

> **INFO — Dev-Library-Application Override Applied**: The original `repo_type` of `application` is preserved in metadata. However, `service_archetype` is `stateless-utility` and 3 of 5 surface flags are `false` (has_persistent_data_store, has_auth_surface, has_logging_of_user_data). This triggers the dev-library-application scoring override per Step 1.5. The `library` N/A mapping is used as the scoring baseline, then surface-flag downgrades are applied for remaining questions. The project's primary purpose is a build/development tool; the online module is a secondary convenience wrapper with no sensitive data, no persistent state, and no authentication surface.

---

## Readiness Profile: Pilot-Ready

**BLOCKERs**: 0 | **RISK-SAFETY**: 1 | **RISK-QUALITY**: 2 | **INFOs**: 32

Supervised pilot with: (1) human approval gates on irreversible actions, (2) agent limited to low-blast-radius operations, (3) compensating controls for each open RISK-SAFETY, (4) remediation timeline before expanding scope.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 0 |
| RISK-SAFETY | 1 |
| RISK-QUALITY | 2 |
| INFO | 32 |
| N/A | 0 |
| Not Evaluated (extended) | 8 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 11 (API-Q5, API-Q6, API-Q8, STATE-Q4, DATA-Q3, DATA-Q7, DISC-Q2, DISC-Q3, OBS-Q3, ENG-Q4, and HITL-Q3 is core)
**Extended Questions Not Triggered**: 8 (API-Q7, STATE-Q2, STATE-Q7, HITL-Q1, HITL-Q2, DATA-Q4, DATA-Q5, ENG-Q5)
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: stateless-utility (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

No BLOCKERs identified.

All four conditional BLOCKER questions (API-Q4, STATE-Q1, AUTH-Q6, DATA-Q2) resolved to INFO due to `agent_scope: read-only` combined with surface-flag calibrations and the dev-library-application override. The remaining two absolute BLOCKERs (API-Q1, AUTH-Q1) were evaluated: API-Q1 passed (documented REST interface exists via Swagger-annotated Spring Boot endpoints), and AUTH-Q1 was downgraded to INFO under the dev-library-application override (code-generation utility with no sensitive data and no auth surface). DATA-Q1 passed Stage A scope gate (no sensitive data handled).

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The online module's `Generator.java` fetches OpenAPI specs from user-provided URLs via `OpenAPIParser().readLocation()`. This external HTTP call has no circuit breaker, retry logic, timeout configuration, or error isolation. A slow or unresponsive remote URL will block the request thread indefinitely, and repeated failures will not trigger any protective fallback.
- **Gap**: No resilience patterns (circuit breaker, timeout, retry with backoff) are implemented for external HTTP calls to user-provided URLs.
- **Compensating Controls**:
  - Deploy behind an API Gateway or reverse proxy with request-level timeout enforcement (e.g., 60-second hard timeout) to prevent indefinite hangs.
  - Limit agent interactions to endpoints that accept inline spec content (`spec` field in `GeneratorInput`) rather than remote URL fetching, avoiding the external dependency entirely.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add HTTP client timeout configuration (connect timeout: 10s, read timeout: 60s) to the OpenAPI parser's HTTP client. Consider wrapping the `readLocation()` call in a circuit breaker (e.g., Resilience4j) to fail fast when remote URLs are repeatedly unresponsive.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/Generator.java` (lines 73–87: `OpenAPIParser().readLocation()` calls with no timeout or circuit breaker)

### RISK-QUALITY — Address as Capacity Allows

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The project uses Maven versioning (7.22.0-SNAPSHOT) and Swagger annotations define the API contract in code. CI workflows verify that generated samples are up-to-date via `bin/generate-samples.sh` with git-status verification. However, there is no dedicated API contract testing (no Pact, no OpenAPI diff tool), no URL versioning (`/v1/`, `/v2/`) on the online module's endpoints, and no breaking change detection tool in the CI pipeline for the online module's API surface.
- **Gap**: No dedicated API contract testing or breaking change detection for the online module's REST API. Schema stability depends on manual review.
- **Compensating Controls**:
  - Agent tool bindings can pin to specific Docker image versions (e.g., `openapitools/openapi-generator-online:v7.22.0`) to avoid unexpected contract changes.
  - The samples-up-to-date CI check provides indirect contract stability verification since generated samples would change if the core API contract changed.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add an OpenAPI spec diff step to CI that compares the auto-generated Swagger spec (from springfox annotations) against a committed baseline, flagging breaking changes before merge.
- **Evidence**: `.github/workflows/openapi-generator.yaml` (samples verification workflow), `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/GenApi.java` (Swagger annotations as contract)

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The online module has a single test file `GenApiControllerTest.java` with 10+ meaningful tests covering: GET endpoints for client/server language lists, GET for options, POST for code generation (clients and servers), file download, forwarded headers, invalid URLs, and OpenAPI normalizer functionality. This provides good breadth coverage of the API surface. However, edge cases like concurrent access to the in-memory `fileMap`, large spec handling, and authorization value passthrough are not covered.
- **Gap**: No negative test for malformed `GeneratorInput` bodies, no tests for concurrent access patterns, and no contract tests. Coverage is adequate for a dev tool but thin for production agent consumption.
- **Compensating Controls**:
  - The existing test suite validates all primary API paths, which is sufficient for a read-only agent pilot.
  - Docker workflow (`.github/workflows/docker.yaml`) provides end-to-end build and run verification.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add contract tests using a committed OpenAPI spec baseline. Add negative tests for malformed inputs, concurrent access scenarios, and boundary conditions (very large specs, unsupported languages).
- **Evidence**: `modules/openapi-generator-online/src/test/java/org/openapitools/codegen/online/api/GenApiControllerTest.java`, `.github/workflows/docker.yaml`

## INFOs — Architecture and Design Inputs

### API-Q2: Machine-Readable API Specification

- **Severity**: INFO
- **Finding**: No standalone OpenAPI/Swagger spec file exists for the online module's API. The Swagger annotations in code (via springfox 3.0.0) auto-generate a spec at runtime at `/api-docs`, but no committed spec file was found in the repository.
- **Implication**: Dev-library-application override applied. For libraries, API contracts are expressed via package manifests and typed exports. The runtime-generated spec is sufficient for agent tool generation during integration.
- **Recommendation**: Consider committing a generated OpenAPI spec to the repository for offline tool generation.
- **Evidence**: `modules/openapi-generator-online/pom.xml` (springfox-swagger2 dependency), `modules/openapi-generator-online/src/main/resources/application.properties` (springfox.documentation.swagger.v2.path=/api-docs)

### API-Q3: Structured Error Responses

- **Severity**: INFO
- **Finding**: Error handling uses Spring's `ResponseStatusException` with HTTP status codes (NOT_FOUND, BAD_REQUEST, INTERNAL_SERVER_ERROR) and message strings. No structured error body with error codes, retryable flags, or machine-readable error categories.
- **Implication**: Dev-library-application override applied. Agent callers can infer retriability from HTTP status codes (4xx = terminal, 5xx = potentially retriable), which is adequate for a code-generation utility.
- **Recommendation**: No immediate action needed for read-only agent use. Consider adding structured error bodies if write-enabled agent scope is planned.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/Generator.java`, `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java`

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: POST endpoints generate code to temp files with new UUIDs per call — inherently non-idempotent by design. Each POST creates a fresh code generation output.
- **Implication**: Read-only agents do not execute write operations. If agent scope is expanded to write-enabled, idempotency would need to be addressed, though the transient nature of code generation makes exact idempotency less critical than in business-data mutation scenarios.
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java` (UUID.randomUUID() per generation request)

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: API responses use JSON for metadata (ResponseCode with code/link fields, CliOption maps, List<String> for language lists). File downloads use `application/zip` binary format. JSON serialization is configured via Spring Boot's Jackson integration with RFC3339 date formatting.
- **Implication**: JSON responses are directly consumable by LLM-based agents. Binary zip downloads would require the agent to handle file I/O separately.
- **Recommendation**: No action needed.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java`, `modules/openapi-generator-online/src/main/resources/application.properties`

### API-Q6: Asynchronous Operation Support

- **Severity**: INFO
- **Finding**: Code generation is synchronous — the POST endpoint blocks until generation completes, then returns a download link. For large OpenAPI specs, generation could exceed 30 seconds. No async patterns (job submission, polling, webhooks) are implemented.
- **Implication**: Extended question triggered (potential >30s operations). However, for a stateless-utility archetype with no persistent state, synchronous processing is architecturally appropriate. Agent callers should configure adequate HTTP timeouts.
- **Recommendation**: For agent integration, set HTTP client timeout to ≥120s for generation endpoints. Consider adding async generation with polling for large specs if agent timeouts become a recurring issue.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/Generator.java` (synchronous `generate()` method)

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limiting headers (`X-RateLimit-Remaining`, `Retry-After`), no API Gateway throttle configuration, and no rate limiting middleware found. The application runs as a bare Spring Boot server with no rate protection.
- **Implication**: Agents calling at machine speed could overwhelm the service. Rate limiting should be enforced at the deployment layer (API Gateway, reverse proxy).
- **Recommendation**: Document expected rate limits when deploying. Consider adding Spring Boot rate limiting (e.g., Bucket4j) or deploying behind an API Gateway with throttle configuration.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/ApiOriginFilter.java` (no rate limit headers), `modules/openapi-generator-online/pom.xml` (no rate limiting dependency)

### AUTH-Q1: Machine Identity Authentication

- **Severity**: INFO
- **Finding**: No authentication mechanism found. No Spring Security dependency, no OAuth2, no JWT, no API key validation, no mTLS. CORS is configured to allow all origins (`*`). The application is completely open.
- **Implication**: Dev-library-application override applied. This is a code-generation utility with no sensitive data, no persistent data store, and no auth surface. Authentication is a deployment-layer concern — operators deploying the online module should place it behind an API Gateway with appropriate auth controls.
- **Recommendation**: When deploying for agent consumption, place behind an API Gateway with API key or OAuth2 client credentials authentication. Do not expose the bare Spring Boot server directly.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/OpenAPI2SpringBoot.java` (CORS `allowedOrigins("*")`), `modules/openapi-generator-online/pom.xml` (no security dependencies)

### AUTH-Q2: Scoped Permissions (Least Privilege)

- **Severity**: INFO
- **Finding**: No IAM policies, no role definitions, no permission models, and no authorization checks in code. The application has no concept of permissions — all endpoints are equally accessible.
- **Implication**: Dev-library-application override applied (`has_auth_surface` is false). Permission scoping is a deployment-layer concern. The service itself performs no sensitive operations that require permission differentiation.
- **Recommendation**: When deploying behind an API Gateway, configure different API keys or OAuth2 scopes for different agent identities if needed.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/GenApi.java` (no auth annotations), `modules/openapi-generator-online/pom.xml` (no security dependencies)

### AUTH-Q3: Action-Level Authorization

- **Severity**: INFO
- **Finding**: No action-level authorization. No RBAC, no ABAC, no middleware permission checks. All endpoints (GET and POST) are equally accessible without authentication.
- **Implication**: Dev-library-application override applied (`has_auth_surface` is false). Action-level auth is a deployment-layer concern for this utility.
- **Recommendation**: If differentiating read-only vs. write-enabled agent access is needed, implement at the API Gateway level (e.g., allow GET only for read-only agents).
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/GenApiController.java`

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: INFO
- **Finding**: No identity propagation mechanism. No JWT parsing, no token exchange, no user context headers. The application does not distinguish between callers.
- **Implication**: Archetype calibration: stateless-utility → INFO. Stateless services returning public/reference data (supported language lists, code generation) are not affected by caller identity.
- **Recommendation**: No action needed for current use case.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java`

### AUTH-Q5: Credential Management

- **Severity**: INFO
- **Finding**: No hardcoded credentials found in the codebase. The only environment variable is `GENERATOR_HOST` (non-sensitive, used for download link generation). The application does not connect to databases or external services requiring persistent credentials. Users may pass `authorizationValue` in the request body for fetching remote specs, but these are transient and not stored.
- **Implication**: No credential management concern exists for this service.
- **Recommendation**: No action needed.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java` (`GENERATOR_HOST` env var), `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/model/GeneratorInput.java` (transient `authorizationValue`)

### AUTH-Q6: Immutable Audit Logging ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity RISK-SAFETY. Surface-flag calibration: `has_auth_surface` is false and dev-library-application override active — downgraded to INFO.
- **Finding**: No audit logging. No CloudTrail configuration, no immutable log storage, no principal attribution in logs. Logging is limited to `System.out.println` of file IDs and language names.
- **Implication**: The system does not execute agent-invoked write operations on business data — audit logging is a consumer/deployment responsibility. The code-generation utility has no operations that require audit attribution.
- **Recommendation**: When deploying behind an API Gateway, enable API Gateway access logging with CloudWatch for audit trail of all requests.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java` (System.out.println only)

### AUTH-Q7: Agent Identity Suspension

- **Severity**: INFO
- **Finding**: No agent identity management. No API key revocation, no service account disable, no identity lifecycle management. The application has no authentication surface.
- **Implication**: Dev-library-application override applied (`has_auth_surface` is false). Identity suspension is a consumer/platform responsibility. Agent identity lifecycle would be managed at the API Gateway or IAM layer.
- **Recommendation**: When deploying for agent consumption, ensure the API Gateway supports API key revocation or OAuth2 client disable.
- **Evidence**: `modules/openapi-generator-online/pom.xml` (no security dependencies)

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity RISK-SAFETY. Archetype calibration: stateless-utility → INFO.
- **Finding**: No compensation or rollback logic. Code generation writes to temporary directories which are cleaned up after download (via `FileUtils.deleteDirectory` and `file.delete()`). There are no persistent state mutations requiring rollback.
- **Implication**: The service has no multi-step write workflows that could leave partial state. Temporary files are self-cleaning. Rollback is architecturally unnecessary.
- **Recommendation**: No action needed.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/Generator.java` (temp file cleanup), `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java` (FileUtils.deleteDirectory in downloadFile)

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The in-memory `fileMap` (static `HashMap<String, Generated>`) in `GenApiService` has no synchronization. Concurrent PUT/GET operations could cause `ConcurrentModificationException` or lost updates. However, each generation creates a unique UUID key, so write conflicts are unlikely in practice.
- **Implication**: Read-only agents do not perform writes. The race condition risk in `fileMap` is low due to UUID uniqueness and is a design limitation of the in-memory approach, not a data integrity concern.
- **Recommendation**: Replace `HashMap` with `ConcurrentHashMap` for thread safety if the online module is used in production.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java` (static `HashMap<String, Generated> fileMap`)

### STATE-Q5: Rate Limiting and Throttling

- **Severity**: INFO
- **Finding**: No rate limiting middleware or API Gateway throttle configuration found. The Spring Boot server accepts unlimited concurrent requests. Archetype calibration for stateless-utility applies but the online module does expose a persistent HTTP surface.
- **Implication**: Agent traffic storms could overwhelm the service. This is a deployment-layer concern — rate limiting should be enforced at the API Gateway or reverse proxy level.
- **Recommendation**: Deploy behind an API Gateway with throttle configuration (e.g., AWS API Gateway usage plan with burst/rate limits).
- **Evidence**: `modules/openapi-generator-online/pom.xml` (no rate limiting dependency), `modules/openapi-generator-online/src/main/resources/application.properties`

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits. The service has no concept of per-agent limits on operations.
- **Implication**: Read-only agents cannot modify records, trigger spend, or delete data. Transaction limits are informational for future scope expansion.
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java`

### HITL-Q3: Sandbox/Staging Environment

- **Severity**: INFO
- **Finding**: Docker-based local testing is available via multiple Dockerfiles (`Dockerfile`, `.hub.online.dockerfile`, `modules/openapi-generator-online/Dockerfile`). The `docker-compose.yml` is for Docusaurus documentation only. No dedicated staging or sandbox environment configuration exists.
- **Implication**: Dev-library-application override applied. The service can be run locally via Docker for testing, which is sufficient for a dev tool. Libraries and utilities rely on their consumers for staging environments.
- **Recommendation**: For agent integration testing, run the online module locally via Docker: `docker build -f .hub.online.dockerfile -t openapi-gen-online . && docker run -p 8080:8080 openapi-gen-online`
- **Evidence**: `.hub.online.dockerfile`, `modules/openapi-generator-online/Dockerfile`, `docker-compose.yml`

### DATA-Q1: Sensitive Data Classification

- **Severity**: INFO
- **Finding**: Stage A scope gate: The system does not store, process, or transmit sensitive data. It generates source code from OpenAPI specifications. Users may pass `authorizationValue` (for fetching remote specs) in request bodies, but these are transient — used in a single HTTP call and not persisted. No database, no user profiles, no PII/PHI/financial records.
- **Implication**: Not a data-handling target — no PII/PHI/financial/credential data is stored, processed, or logged. Stage A = No, classification controls are not applicable.
- **Recommendation**: No action needed.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/model/GeneratorInput.java` (transient authorizationValue), `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java` (no data persistence)

### DATA-Q2: Data Residency and Sovereignty ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity RISK-SAFETY. Surface-flag calibration: `has_persistent_data_store` is false AND `has_logging_of_user_data` is false → INFO.
- **Finding**: The system holds no persistent data subject to residency constraints. Generated code files are temporary and contain no user PII. The only data is OpenAPI spec content provided by the caller, which is processed transiently.
- **Implication**: No persistent data store and no user-data logging — residency requirements do not apply.
- **Recommendation**: No action needed.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/Generator.java` (temp file generation only)

### DATA-Q3: Selective Query Support

- **Severity**: INFO
- **Finding**: Extended question triggered (list endpoints). GET `/api/gen/clients` and GET `/api/gen/servers` return lists of supported generators. These lists are bounded and finite (determined by registered CodegenConfig implementations — approximately 80+ clients and 50+ servers). No pagination needed as the lists are small and static.
- **Implication**: Result sets are inherently bounded. No risk of unbounded queries exhausting LLM context windows.
- **Recommendation**: No action needed.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java` (static `clients` and `servers` lists populated from CodegenConfigLoader)

### DATA-Q6: PII Redaction in Logs

- **Severity**: INFO
- **Finding**: Logging is limited to `System.out.println` of file IDs, filenames, and language names in `GenApiService.java`, and `LOGGER.debug` of generation type and language in `Generator.java`. No user PII is logged. No request body logging. No user identifiers in logs.
- **Implication**: Dev-library-application override applied. System does not log user data and holds no user data — PII-in-logs risk is not applicable.
- **Recommendation**: No action needed.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java` (System.out.println of code UUIDs), `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/Generator.java` (LOGGER.debug of language/type)

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality metrics, dashboards, or freshness SLAs. The system generates code on-demand from user-provided specs — there is no persisted dataset to measure quality against.
- **Implication**: Expected for a code-generation toolkit. Data quality concerns do not apply to transient code generation.
- **Recommendation**: No action needed.
- **Evidence**: No evidence found — absence is itself the expected finding for this service type.

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Code uses clear, semantic field names throughout: `language`, `framework`, `generatorInput`, `openAPIUrl`, `spec`, `options`, `code`, `link`, `filename`, `friendlyName`, `authorizationValue`, `openapiNormalizer`. Java code follows standard naming conventions. API response models use descriptive names: `ResponseCode` (with `code` and `link` fields), `GeneratorInput`, `CliOption`.
- **Implication**: Field names are directly interpretable by LLM-based agents without requiring a data dictionary.
- **Recommendation**: No action needed.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/model/GeneratorInput.java`, `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/model/ResponseCode.java`

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No formal data catalog. The project maintains extensive documentation in `docs/` directory and the `website/` folder. Generator configurations are self-documenting via `CliOption` objects returned by GET `/api/gen/clients/{language}` and GET `/api/gen/servers/{framework}`. The `openapitools.json` file provides project metadata.
- **Implication**: The API itself serves as a discovery mechanism for available generators and their options. Agents can query available generators programmatically.
- **Recommendation**: No action needed for agent integration. The self-describing API is sufficient.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java` (getClientOptions, getServerOptions returning CliOption maps), `docs/`, `openapitools.json`

### OBS-Q1: Distributed Tracing and Structured Logging

- **Severity**: INFO
- **Finding**: The online module uses SLF4J + Logback (via Spring Boot's `spring-boot-starter-web`). No OpenTelemetry, no X-Ray, no trace ID propagation. Logging is unstructured — `System.out.println` in `GenApiService.java` and `LOGGER.debug` in `Generator.java`. No JSON logging configured, no correlation IDs, no `traceparent` header handling.
- **Implication**: Dev-library-application override applied. Library/utility — tracing and correlation are consumer concerns. The online module's diagnostic logging is adequate for its role as a dev tool.
- **Recommendation**: If deploying for production agent consumption, add Spring Boot Actuator with Micrometer tracing and configure JSON logging format.
- **Evidence**: `modules/openapi-generator-online/pom.xml` (spring-boot-starter-web, no tracing dependencies), `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/Generator.java` (LOGGER.debug)

### OBS-Q2: Alerting on Error Rates and Latency

- **Severity**: INFO
- **Finding**: No CloudWatch alarms, no anomaly detection, no PagerDuty/OpsGenie integration, no monitoring configuration found. The application has no alerting infrastructure.
- **Implication**: Dev-library-application override applied. Alerting on error rates and latency is a consumer/deployment concern. Libraries and utilities expose errors via return values and HTTP status codes.
- **Recommendation**: When deploying for agent consumption, configure API Gateway CloudWatch metrics with alarms on 5xx error rate and p99 latency.
- **Evidence**: No monitoring configuration found in repository — absence is itself the finding.

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No custom business metrics. No `cloudwatch.put_metric_data`, no custom dashboards. Standard Spring Boot Actuator is not configured (no `spring-boot-starter-actuator` dependency).
- **Implication**: Expected for a code-generation toolkit. Business outcome metrics (e.g., successful generations, popular languages) would be useful for operational visibility but are not a deployment gate.
- **Recommendation**: Consider adding Spring Boot Actuator with Micrometer for basic health and generation count metrics.
- **Evidence**: `modules/openapi-generator-online/pom.xml` (no actuator dependency)

### ENG-Q1: Infrastructure Governance

- **Severity**: INFO
- **Finding**: No IaC for API gateways, IAM roles, or networking. The application is deployed via Docker images built from Dockerfiles. No Terraform, CloudFormation, or CDK definitions exist in the repository.
- **Implication**: Dev-library-application override applied. Libraries, CLIs, and dev tools do not own the IaC for API gateways, IAM roles, or networking — their consumers do. The library's engineering governance is its own build/release pipeline.
- **Recommendation**: When deploying for agent consumption, define the deployment infrastructure (API Gateway, IAM, networking) as IaC in the consumer's infrastructure repository.
- **Evidence**: No IaC files found in repository — absence confirmed by directory scan.

### ENG-Q2: CI/CD with API Contract Testing

- **Severity**: INFO
- **Finding**: Robust CI/CD exists: GitHub Actions (105 workflow files), CircleCI, with build, unit tests, sample generation verification, and documentation checks. The `openapi-generator.yaml` workflow runs build, unit tests, documentation freshness, and sample generation freshness checks. Docker workflows verify Docker builds. However, no API contract testing (no Pact, no OpenAPI spec validation, no breaking change detection) exists for the online module.
- **Implication**: Dev-library-application override applied. Library build pipelines validate package contracts (semver, typed exports), not API contracts. The samples-up-to-date check provides indirect contract validation.
- **Recommendation**: No immediate action needed for read-only agent pilot. Contract testing would be valuable if the online module becomes a primary agent integration surface.
- **Evidence**: `.github/workflows/openapi-generator.yaml`, `.github/workflows/docker.yaml`, `.circleci/config.yml`

### ENG-Q3: Rollback Capability

- **Severity**: INFO
- **Finding**: Docker images are built and published to DockerHub via `docker-release.yml` (triggered on tags and master pushes). Maven artifacts are published via `maven-release.yml`. Rollback requires re-deploying a previous Docker image version — no blue/green, no canary, no automated rollback.
- **Implication**: Dev-library-application override applied. No deployed HTTP/RPC surface owned by this repository — deployment rollback is a consumer concern. Library rollback is handled via package version pinning by consumers.
- **Recommendation**: When deploying the online module for agent consumption, use versioned Docker image tags and implement blue/green or canary deployment at the platform level.
- **Evidence**: `.github/workflows/docker-release.yml`, `.github/workflows/maven-release.yml`

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: The openapi-generator-online module exposes a documented REST interface via Spring Boot. Endpoints are defined in `GenApi.java` with Swagger annotations (`@ApiOperation`, `@ApiResponses`): GET `/api/gen/clients`, GET `/api/gen/servers`, GET `/api/gen/clients/{language}`, GET `/api/gen/servers/{framework}`, POST `/api/gen/clients/{language}`, POST `/api/gen/servers/{framework}`, GET `/api/gen/download/{fileId}`. The controller delegates to `GenApiService` which implements all business logic. This is a genuine REST API — not database-direct or file-based integration.
- **Gap**: The API exists and is documented via Swagger annotations. No gap for this question. However, per the dev-library-application override, the analysis acknowledges this is a secondary web wrapper around the primary CLI/library tools.
- **Recommendation**: No remediation needed. The API surface is well-defined and documented.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/GenApi.java`, `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/GenApiController.java`

#### API-Q2: Machine-Readable API Specification
- **Severity**: INFO
- **Finding**: No standalone OpenAPI/Swagger spec file committed for the online module's API. Runtime spec available at `/api-docs` via springfox 3.0.0. Dev-library-application override: INFO — for libraries, API contracts are expressed via package manifests and typed exports.
- **Gap**: No committed spec file. Runtime-generated only.
- **Recommendation**: Consider committing a generated OpenAPI spec for offline tool generation.
- **Evidence**: `modules/openapi-generator-online/pom.xml` (springfox-swagger2 dependency), `modules/openapi-generator-online/src/main/resources/application.properties`

#### API-Q3: Structured Error Responses
- **Severity**: INFO
- **Finding**: Errors use Spring's `ResponseStatusException` with HTTP status codes and message strings. No structured error body (no error code enum, no retryable flag). Dev-library-application override: INFO.
- **Gap**: No structured error response format beyond HTTP status codes.
- **Recommendation**: No immediate action needed for read-only agent use.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/Generator.java`, `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: POST endpoints generate code with new UUIDs per call — non-idempotent by design. Read-only agents do not execute these.
- **Gap**: N/A for read-only scope.
- **Recommendation**: No action needed.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: JSON for metadata (ResponseCode, CliOption maps, List<String>). Binary `application/zip` for downloads. Jackson with RFC3339 dates.
- **Gap**: N/A
- **Recommendation**: No action needed.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java`, `modules/openapi-generator-online/src/main/resources/application.properties`

#### API-Q6: Asynchronous Operation Support
- **Severity**: INFO
- **Finding**: Extended question triggered (potential >30s operations for large specs). Code generation is synchronous with no async patterns. Architecturally appropriate for stateless-utility.
- **Gap**: No async support for long-running generation.
- **Recommendation**: Configure agent HTTP client timeout ≥120s for generation endpoints.
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
- **Finding**: No rate limiting headers, no throttle configuration, no rate limiting middleware.
- **Gap**: No rate limit visibility for agent callers.
- **Recommendation**: Deploy behind API Gateway with documented rate limits.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/ApiOriginFilter.java`, `modules/openapi-generator-online/pom.xml`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: No authentication mechanism. No Spring Security, no OAuth2, no JWT, no API keys, no mTLS. CORS allows all origins (`*`). Dev-library-application override: INFO — code-generation utility with no sensitive data and no auth surface.
- **Gap**: No machine identity authentication.
- **Recommendation**: Deploy behind API Gateway with auth controls for agent consumption.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/OpenAPI2SpringBoot.java`, `modules/openapi-generator-online/pom.xml`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: INFO
- **Finding**: No IAM policies, no role definitions, no permission models, no authorization checks. Dev-library-application override: INFO (`has_auth_surface` is false).
- **Gap**: No permission model.
- **Recommendation**: Implement scoping at API Gateway layer when deploying.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/GenApi.java`, `modules/openapi-generator-online/pom.xml`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: INFO
- **Finding**: No action-level authorization. No RBAC, no ABAC. Dev-library-application override: INFO (`has_auth_surface` is false).
- **Gap**: No action-level auth.
- **Recommendation**: Implement at API Gateway if needed.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/GenApiController.java`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: No identity propagation. Archetype calibration: stateless-utility → INFO. Stateless services returning public/reference data not affected by caller identity.
- **Gap**: No identity propagation.
- **Recommendation**: No action needed.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java`

#### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: No hardcoded credentials. Only env var is `GENERATOR_HOST` (non-sensitive). No database connections. Transient `authorizationValue` in request bodies not stored.
- **Gap**: No gap — no credentials to manage.
- **Recommendation**: No action needed.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java`, `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/model/GeneratorInput.java`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity RISK-SAFETY. Surface-flag calibration: `has_auth_surface` false + dev-library-application override → INFO.
- **Finding**: No audit logging. `System.out.println` of file IDs and language names only.
- **Gap**: No immutable audit trail.
- **Recommendation**: Enable API Gateway access logging when deploying.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: INFO
- **Finding**: No identity management. Dev-library-application override: INFO (`has_auth_surface` is false).
- **Gap**: No identity suspension capability.
- **Recommendation**: Manage at API Gateway/IAM layer.
- **Evidence**: `modules/openapi-generator-online/pom.xml`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity RISK-SAFETY. Archetype calibration: stateless-utility → INFO.
- **Finding**: No compensation logic. Temp files cleaned up after download. No persistent state mutations.
- **Gap**: No gap — rollback is architecturally unnecessary.
- **Recommendation**: No action needed.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/Generator.java`, `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java`

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
- **Finding**: In-memory `HashMap<String, Generated> fileMap` has no synchronization. UUID uniqueness mitigates conflict risk.
- **Gap**: No thread-safe data structure for fileMap.
- **Recommendation**: Replace HashMap with ConcurrentHashMap for production use.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: Extended question triggered (external dependency: OpenAPIParser fetches user-provided URLs). No circuit breaker, retry logic, or timeout on external HTTP calls via `OpenAPIParser().readLocation()`. Slow/unresponsive URLs block threads indefinitely.
- **Gap**: No resilience patterns for external HTTP calls.
- **Recommendation**: Add HTTP client timeout configuration and consider Resilience4j circuit breaker.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/Generator.java`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: INFO
- **Finding**: No rate limiting. Archetype calibration for stateless-utility applied. Deployment-layer concern.
- **Gap**: No rate limiting at application layer.
- **Recommendation**: Deploy behind API Gateway with throttle config.
- **Evidence**: `modules/openapi-generator-online/pom.xml`, `modules/openapi-generator-online/src/main/resources/application.properties`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No transaction limits. Informational for read-only scope.
- **Gap**: No per-agent transaction limits.
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q2: Configurable Approval Gates
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: INFO
- **Finding**: Docker-based local testing available via multiple Dockerfiles. No dedicated staging environment. Dev-library-application override: INFO.
- **Gap**: No dedicated staging environment.
- **Recommendation**: Use Docker for agent integration testing.
- **Evidence**: `.hub.online.dockerfile`, `modules/openapi-generator-online/Dockerfile`, `docker-compose.yml`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO
- **Finding**: Stage A = No. System does not store, process, or transmit sensitive data. Code generation from OpenAPI specs only. Transient `authorizationValue` not persisted. Dev-library-application override further supports INFO.
- **Gap**: N/A — not a data-handling target.
- **Recommendation**: No action needed.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/model/GeneratorInput.java`, `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity RISK-SAFETY. Surface-flag calibration: `has_persistent_data_store` false + `has_logging_of_user_data` false → INFO.
- **Finding**: No persistent data. No residency constraints apply.
- **Gap**: N/A
- **Recommendation**: No action needed.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/Generator.java`

#### DATA-Q3: Selective Query Support
- **Severity**: INFO
- **Finding**: Extended question triggered (list endpoints). Lists are bounded and finite (CodegenConfig implementations). No unbounded result risk.
- **Gap**: No pagination, but not needed for bounded lists.
- **Recommendation**: No action needed.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java`

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
- **Finding**: Logs contain file IDs and language names only. No PII. Dev-library-application override: INFO (`has_logging_of_user_data` false + `has_persistent_data_store` false).
- **Gap**: N/A — no PII in logs.
- **Recommendation**: No action needed.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java`, `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/Generator.java`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics. Expected for a code-generation toolkit with no persisted dataset.
- **Gap**: No data quality measurement.
- **Recommendation**: No action needed.
- **Evidence**: No evidence found — absence is itself the expected finding.

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: Maven versioning (7.22.0-SNAPSHOT). Swagger annotations define contract. CI verifies samples are up-to-date. No dedicated API contract testing, no URL versioning on endpoints, no breaking change detection tool.
- **Gap**: No dedicated API contract testing or breaking change detection.
- **Recommendation**: Add OpenAPI spec diff to CI comparing auto-generated spec against committed baseline.
- **Evidence**: `.github/workflows/openapi-generator.yaml`, `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/GenApi.java`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Clear semantic field names: `language`, `framework`, `generatorInput`, `openAPIUrl`, `spec`, `code`, `link`. Standard Java naming conventions.
- **Gap**: N/A
- **Recommendation**: No action needed.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/model/GeneratorInput.java`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal data catalog. Extensive docs in `docs/` and `website/`. Self-describing API via CliOption endpoints.
- **Gap**: No formal data catalog.
- **Recommendation**: No action needed — self-describing API is sufficient.
- **Evidence**: `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java`, `docs/`, `openapitools.json`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: INFO
- **Finding**: SLF4J + Logback via Spring Boot. No OpenTelemetry, no X-Ray, no trace IDs, no JSON logging, no correlation IDs. Dev-library-application override: INFO.
- **Gap**: No distributed tracing or structured logging.
- **Recommendation**: Add Spring Boot Actuator with Micrometer tracing if deploying for production agent consumption.
- **Evidence**: `modules/openapi-generator-online/pom.xml`, `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/Generator.java`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: INFO
- **Finding**: No monitoring or alerting configuration. Dev-library-application override: INFO.
- **Gap**: No alerting infrastructure.
- **Recommendation**: Configure API Gateway CloudWatch metrics and alarms when deploying.
- **Evidence**: No monitoring configuration found.

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics. No Spring Boot Actuator. Expected for a code-generation toolkit.
- **Gap**: No business outcome metrics.
- **Recommendation**: Consider Spring Boot Actuator with Micrometer.
- **Evidence**: `modules/openapi-generator-online/pom.xml`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance
- **Severity**: INFO
- **Finding**: No IaC found. Docker-based deployment only. Dev-library-application override: INFO.
- **Gap**: No IaC for deployment infrastructure.
- **Recommendation**: Define deployment IaC in consumer's infrastructure repository.
- **Evidence**: No IaC files found. `Dockerfile`, `.hub.online.dockerfile` (Docker-based deployment)

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: INFO
- **Finding**: Robust CI/CD (GitHub Actions, CircleCI). Build, tests, sample verification, Docker builds. No API contract testing. Dev-library-application override: INFO.
- **Gap**: No API contract testing.
- **Recommendation**: No immediate action for read-only pilot.
- **Evidence**: `.github/workflows/openapi-generator.yaml`, `.github/workflows/docker.yaml`, `.circleci/config.yml`

#### ENG-Q3: Rollback Capability
- **Severity**: INFO
- **Finding**: Docker images published to DockerHub with version tags. Maven releases to Central. No automated rollback. Dev-library-application override: INFO.
- **Gap**: No automated deployment rollback.
- **Recommendation**: Use versioned Docker image tags for rollback. Implement blue/green at deployment layer.
- **Evidence**: `.github/workflows/docker-release.yml`, `.github/workflows/maven-release.yml`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: `GenApiControllerTest.java` with 10+ tests covering all primary API paths: GET clients/servers lists, GET options, POST generation, download, forwarded headers, invalid URLs, OpenAPI normalizer. Good breadth but no contract tests, no concurrency tests, no edge cases.
- **Gap**: No contract tests, limited negative testing, no concurrent access tests.
- **Recommendation**: Add contract tests and expand edge case coverage.
- **Evidence**: `modules/openapi-generator-online/src/test/java/org/openapitools/codegen/online/api/GenApiControllerTest.java`, `.github/workflows/docker.yaml`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent data stores
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/GenApi.java` | API-Q1, API-Q2, API-Q8, AUTH-Q2, DISC-Q1 |
| `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/GenApiController.java` | API-Q1, AUTH-Q3 |
| `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/GenApiService.java` | API-Q3, API-Q4, API-Q5, AUTH-Q4, AUTH-Q5, AUTH-Q6, STATE-Q1, STATE-Q3, STATE-Q5, STATE-Q6, DATA-Q1, DATA-Q3, DATA-Q6, DISC-Q3 |
| `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/service/Generator.java` | API-Q3, API-Q6, STATE-Q1, STATE-Q4, DATA-Q2, DATA-Q6, OBS-Q1 |
| `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/api/ApiOriginFilter.java` | API-Q8 |
| `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/OpenAPI2SpringBoot.java` | AUTH-Q1 |
| `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/model/GeneratorInput.java` | AUTH-Q5, DATA-Q1, DISC-Q2 |
| `modules/openapi-generator-online/src/main/java/org/openapitools/codegen/online/configuration/OpenAPIDocumentationConfig.java` | API-Q2 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/openapi-generator.yaml` | DISC-Q1, ENG-Q2 |
| `.github/workflows/docker.yaml` | ENG-Q2, ENG-Q4 |
| `.github/workflows/docker-release.yml` | ENG-Q3 |
| `.github/workflows/maven-release.yml` | ENG-Q3 |
| `.circleci/config.yml` | ENG-Q2 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `Dockerfile` | ENG-Q1, HITL-Q3 |
| `.hub.online.dockerfile` | ENG-Q1, ENG-Q3, HITL-Q3 |
| `modules/openapi-generator-online/Dockerfile` | HITL-Q3 |
| `docker-compose.yml` | HITL-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `modules/openapi-generator-online/pom.xml` | API-Q2, API-Q8, AUTH-Q1, AUTH-Q2, AUTH-Q7, STATE-Q5, OBS-Q1, OBS-Q3, ENG-Q1 |
| `pom.xml` | ENG-Q2 (root project configuration) |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `modules/openapi-generator-online/src/main/resources/application.properties` | API-Q2, API-Q5, STATE-Q5 |
| `openapitools.json` | DISC-Q3 |

### Test Files
| File | Questions Referenced |
|------|---------------------|
| `modules/openapi-generator-online/src/test/java/org/openapitools/codegen/online/api/GenApiControllerTest.java` | ENG-Q4 |

### Documentation
| File | Questions Referenced |
|------|---------------------|
| `docs/` | DISC-Q3 |
