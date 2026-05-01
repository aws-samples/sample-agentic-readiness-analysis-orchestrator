# Agentic Readiness Assessment Report

**Target**: hapifhir/hapi-fhir
**Date**: 2026-04-29
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: monorepo
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: java, healthcare, rest-api
**Context**: Open-source Java implementation of the HL7 FHIR healthcare standard.

**Archetype Justification**: HAPI FHIR, when deployed as its JPA server (hapi-fhir-jpaserver-base), has database connections (JPA/Hibernate with SQL databases), full CRUD endpoints for all FHIR resource types, entity lifecycle management via ResourceTable, and user/patient-specific data — matching the stateful-crud archetype.

---

## Readiness Profile: Pilot-Ready (Safety Concerns)

**BLOCKERs**: 0 | **RISK-SAFETY**: 8 | **RISK-QUALITY**: 12 | **INFOs**: 23

Supervised pilot with elevated safety oversight: (1) all Pilot-Ready controls apply, (2) prioritize RISK-SAFETY remediation before expanding agent scope, (3) dedicated safety review cadence, (4) agent restricted to lowest-blast-radius operations until RISK-SAFETY count drops below 3.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 0 |
| RISK-SAFETY | 8 |
| RISK-QUALITY | 12 |
| INFO | 23 |
| N/A | 0 |
| Not Evaluated (extended) | 0 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 19
**Extended Questions Not Triggered**: 0
**Questions N/A (repo_type: monorepo)**: 0
**Service Archetype**: stateful-crud (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

No BLOCKERs identified.

All four conditional BLOCKER questions (API-Q4, STATE-Q1, AUTH-Q6, DATA-Q2) resolve to INFO or RISK-SAFETY under the `read-only` agent scope. The two core BLOCKERs (API-Q1: Documented API Interface, AUTH-Q1: Machine Identity Authentication, DATA-Q1: Sensitive Data Classification) are satisfied by the HAPI FHIR framework's capabilities, though AUTH-Q1 and DATA-Q1 require deployer configuration.

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: HAPI FHIR provides the `AuthorizationInterceptor` with fine-grained `RuleBuilder` that supports per-resource-type, per-compartment (patient-level) scoping. However, the framework ships with **no default authorization rules enabled** — a deployer must configure rules explicitly. Without deployer configuration, all operations are permitted.
- **Gap**: The framework provides the capability but does not enforce least-privilege by default. A deployment without authorization interceptor configuration would grant unrestricted access to an agent identity.
- **Compensating Controls**:
  - Register `AuthorizationInterceptor` with read-only rules for the agent identity before any pilot
  - Use the `RuleBuilder.allow().read().allResources().withAnyId().andThen().denyAll()` pattern for read-only agents
- **Remediation Timeline**: 7–14 days (configuration, not code change)
- **Recommendation**: Document a reference `AuthorizationInterceptor` configuration for agent identities with read-only access scoped to specific resource types.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/AuthorizationInterceptor.java`, `RuleBuilder.java`, `RuleOpEnum.java`

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: HAPI FHIR provides the `BalpAuditCaptureInterceptor` implementing IHE Basic Audit Logging Pattern (BALP), which auto-generates FHIR R4 `AuditEvent` resources conformant to the BALP profile. The `LoggingInterceptor` provides configurable request/response logging. However, immutability of audit logs is **not enforced by the framework** — it depends on the storage backend and deployment configuration.
- **Gap**: Audit event generation capability exists but audit log immutability (tamper-evidence, object lock) is not provided at the framework level. No CloudTrail, no S3 object lock, no immutable log storage configuration exists in this repository.
- **Compensating Controls**:
  - Enable `BalpAuditCaptureInterceptor` to generate AuditEvent resources for all agent-initiated requests
  - Deploy audit events to a write-once storage backend (S3 with object lock, CloudTrail)
- **Remediation Timeline**: 30–60 days (deployment infrastructure change)
- **Recommendation**: Deploy BalpAuditCaptureInterceptor with an `IBalpAuditEventSink` implementation that writes to immutable storage. Document the audit architecture for agent interactions.
- **Evidence**: `hapi-fhir-storage/src/main/java/ca/uhn/fhir/storage/interceptor/balp/BalpAuditCaptureInterceptor.java`, `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/LoggingInterceptor.java`

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: HAPI FHIR does not provide a built-in mechanism to suspend or revoke individual agent identities at runtime. The `AuthorizationInterceptor` evaluates rules per-request but does not maintain a deny-list of suspended identities. Identity management is delegated entirely to the deployer's authentication layer (OAuth2 provider, API Gateway, etc.).
- **Gap**: No framework-level identity suspension mechanism. A compromised agent identity cannot be revoked without modifying the external authentication system or redeploying the authorization interceptor rules.
- **Compensating Controls**:
  - Implement identity suspension at the API Gateway or OAuth2 provider level (revoke client credentials, disable API key)
  - Add a custom interceptor that checks a deny-list before processing requests
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Implement an identity deny-list interceptor that can be updated at runtime without redeployment. Integrate with the deployer's identity provider for real-time revocation.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/AuthorizationInterceptor.java`

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: HAPI FHIR provides retry logic via `Retrier.java` (exponential backoff with configurable max retries via Spring Retry) and `RetryingMessageHandlerWrapper` for subscription message delivery. However, there are **no circuit breaker implementations** in the codebase. The retry patterns exist for internal operations (search parameter indexing, subscription delivery) but no circuit breaker protects against cascading failures from external dependency calls (e.g., terminology servers, remote validation services).
- **Gap**: Retry logic exists but no circuit breaker pattern (Resilience4j, Hystrix) is implemented. A runaway agent could trigger cascading failures to downstream terminology or validation services.
- **Compensating Controls**:
  - Deploy a service mesh (Istio) or API Gateway with circuit breaker configuration for downstream calls
  - Configure timeouts on all external HTTP clients used by the HAPI FHIR server
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add Resilience4j circuit breaker wrapping for external dependency calls (terminology services, remote validation endpoints). Configure timeout and retry policies on all outbound HTTP clients.
- **Evidence**: `hapi-fhir-jpaserver-searchparam/src/main/java/ca/uhn/fhir/jpa/searchparam/retry/Retrier.java`

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: HAPI FHIR does **not include any built-in rate limiting or throttling mechanism**. No rate limiting middleware, no `X-RateLimit-*` headers, no API Gateway throttling configuration exists in the repository. Rate limiting is expected to be handled entirely at the deployment layer (reverse proxy, API Gateway, WAF).
- **Gap**: No rate limiting at any layer within the framework. An agent calling endpoints at machine speed would not be throttled by the HAPI FHIR server itself.
- **Compensating Controls**:
  - Deploy behind an API Gateway (AWS API Gateway, NGINX) with rate limiting configured per agent identity
  - Add a custom `SERVER_INCOMING_REQUEST_PRE_PROCESSED` interceptor that implements per-identity rate limiting
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Deploy an API Gateway with usage plans and rate limits configured per agent API key. As a defense-in-depth measure, implement a rate-limiting interceptor within the HAPI FHIR server.
- **Evidence**: No rate limiting code found in the repository. Absence confirmed by searching all source files for rate limit patterns.

#### STATE-Q1: Compensation and Rollback ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: FHIR transaction Bundles (Bundle.type = "transaction") are processed atomically by the JPA server — if any entry fails, the entire transaction is rolled back via JPA/Hibernate transaction management. `TransactionDetails` tracks the state of multi-step operations. However, there is no saga pattern or explicit compensation API for cross-service workflows.
- **Gap**: Single-server transactions are atomic, but no compensation mechanism for cross-service orchestration. No explicit undo/compensation endpoints.
- **Compensating Controls**:
  - Use FHIR transaction Bundles for all multi-step operations to ensure atomicity
  - Implement compensation logic at the agent orchestration layer for cross-service workflows
- **Remediation Timeline**: 60–90 days
- **Recommendation**: For the read-only pilot, no action needed. For future write-enabled scope, ensure all write operations use FHIR transaction Bundles for atomicity and implement saga patterns at the orchestration layer.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/api/server/storage/TransactionDetails.java`

#### DATA-Q2: Data Residency and Sovereignty ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Healthcare data is subject to strict residency requirements (HIPAA, GDPR, provincial health data laws). HAPI FHIR is a library — it does not enforce data residency at the framework level. Data residency depends entirely on the deployment topology (database region, server location). No region-specific configuration or cross-region replication controls exist in the codebase.
- **Gap**: No data residency enforcement at the framework level. A read-only agent accessing a HAPI FHIR server could transmit PHI to an LLM endpoint in a different jurisdiction.
- **Compensating Controls**:
  - Co-locate HAPI FHIR server, database, and LLM endpoint in the same jurisdiction
  - Implement data residency checks at the agent orchestration layer
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Ensure the HAPI FHIR server, database, and LLM endpoint are co-located in the same jurisdiction. Implement data residency validation at the agent orchestration layer before any data leaves the server boundary.
- **Evidence**: No data residency configuration found in the repository.

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The `LoggingInterceptor` logs request metadata (URL, method, user agent, request ID) but does **not log request/response bodies by default**. However, when verbose logging is enabled or when exceptions include diagnostic details, FHIR resource content containing PHI/PII can leak into logs. The `ExceptionHandlingInterceptor` populates `OperationOutcome` with exception messages which may contain patient-identifiable data. No PII redaction middleware or log scrubbing is implemented in the framework.
- **Gap**: No automated PII/PHI redaction in logging. Healthcare data (patient names, identifiers, clinical data) can appear in exception logs and diagnostic outputs. No Amazon Macie integration, no log masking libraries.
- **Compensating Controls**:
  - Configure `LoggingInterceptor` to log only metadata (URL, method, request ID, timing) — avoid logging request/response bodies
  - Deploy log scrubbing at the infrastructure layer (CloudWatch Logs data protection policies)
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement a PII-aware logging interceptor that redacts sensitive FHIR resource fields (Patient.name, Patient.identifier, etc.) before they reach log outputs. Configure CloudWatch Logs data protection policies as a safety net.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/LoggingInterceptor.java`, `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/ExceptionHandlingInterceptor.java`

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The `hapi-fhir-server-openapi` module provides `OpenApiInterceptor` which **dynamically generates** OpenAPI 3.0 specifications from the server's FHIR CapabilityStatement at runtime. This is generated on-the-fly, not statically maintained. No static `openapi.yaml` or `swagger.json` file exists in the repository. The generated spec is comprehensive — it covers all registered resource providers, operations, and search parameters.
- **Gap**: No static, version-controlled OpenAPI specification file. The dynamic generation is functional but means the spec is only available from a running server instance.
- **Compensating Controls**:
  - Use the running server's `/api-docs` endpoint to export the OpenAPI spec for agent tool generation
  - Generate and commit a static OpenAPI spec as part of the CI/CD pipeline
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add a CI step that starts a test server, exports the OpenAPI specification, and commits it to the repository for version-controlled agent tool binding.
- **Evidence**: `hapi-fhir-server-openapi/src/main/java/ca/uhn/fhir/rest/openapi/OpenApiInterceptor.java`

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: HAPI FHIR returns FHIR `OperationOutcome` resources for all error responses via `ExceptionHandlingInterceptor`. Each error maps to a specific HTTP status code via `BaseServerResponseException` subclasses (400 InvalidRequest, 401 Authentication, 403 Forbidden, 404 NotFound, 409 VersionConflict, 412 PreconditionFailed, 422 Unprocessable). OperationOutcome includes severity, code, and diagnostics fields. However, there is **no explicit retryable/non-retryable classification** in the error response.
- **Gap**: Error responses use FHIR OperationOutcome with severity and code, which is richer than most APIs. However, agents must infer retryability from HTTP status codes (429, 503 = retry; 400, 403 = do not retry) rather than an explicit `retryable` field.
- **Compensating Controls**:
  - Build agent tool definitions that map HTTP status codes to retry/no-retry decisions
  - Document the retry semantics for each error code in agent tool metadata
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Consider adding a custom extension to OperationOutcome responses that includes a `retryable` boolean, or document retry semantics per HTTP status code for agent consumers.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/ExceptionHandlingInterceptor.java`, `hapi-fhir-base/src/main/java/ca/uhn/fhir/rest/server/exceptions/BaseServerResponseException.java`

#### API-Q6: Asynchronous Operation Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: HAPI FHIR provides robust asynchronous operation support via the Batch2 framework (`hapi-fhir-storage-batch2`). The `BulkDataExportProvider` implements the FHIR Bulk Data Export ($export) with async patterns: job submission returns a `Content-Location` header for polling, and the `$export-poll-status` operation provides job progress. Reindexing operations also use the Batch2 async framework. OpenTelemetry tracing is integrated for batch jobs via `BatchJobOpenTelemetryUtils`.
- **Gap**: Async support is well-implemented for FHIR-defined async operations. No webhook callback pattern exists — polling is the only async consumption pattern.
- **Compensating Controls**:
  - Use the `$export-poll-status` endpoint for agent polling of long-running operations
  - Implement a custom interceptor that emits webhook notifications on job completion
- **Remediation Timeline**: 60–90 days (for webhook support)
- **Recommendation**: For agent integration, document the polling intervals and expected completion times for async operations. Consider adding webhook callback support for long-running batch operations.
- **Evidence**: `hapi-fhir-storage-batch2-jobs/src/main/java/ca/uhn/fhir/batch2/jobs/export/BulkDataExportProvider.java`, `hapi-fhir-storage-batch2/src/main/java/ca/uhn/fhir/batch2/util/BatchJobOpenTelemetryUtils.java`

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: FHIR is a versioned specification with formal versioning (DSTU2, DSTU3, R4, R4B, R5). HAPI FHIR supports all versions via separate modules (`hapi-fhir-structures-r4`, `hapi-fhir-structures-r5`, etc.). The FHIR CapabilityStatement exposes the server's supported FHIR version. However, there is **no breaking change detection in CI** — no consumer-driven contract tests (Pact), no OpenAPI diff, no `buf breaking` equivalent. Schema changes within a FHIR version are governed by the FHIR specification's compatibility rules, but breaking changes in HAPI's own API surface are not automatically detected.
- **Gap**: FHIR specification versioning is strong, but no automated breaking-change detection exists in CI for the HAPI FHIR Java API surface or the generated REST endpoints.
- **Compensating Controls**:
  - Pin agent tool definitions to a specific FHIR version (e.g., R4) and HAPI FHIR release version
  - Monitor HAPI FHIR release changelogs for breaking changes before upgrading
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add OpenAPI diff checks to CI that compare the generated OpenAPI spec against the previous release to detect breaking changes automatically.
- **Evidence**: `hapi-fhir-structures-r4/`, `hapi-fhir-structures-r5/`, `.github/workflows/parallel-pipeline-build.yml`

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: HAPI FHIR provides: (1) `ServletRequestTracing` which assigns/propagates X-Request-ID headers for request correlation, (2) `BatchJobOpenTelemetryUtils` with OpenTelemetry span integration for Batch2 jobs, (3) `LoggingInterceptor` with configurable log message templates. However, full distributed tracing (OpenTelemetry SDK integration for all REST requests, not just batch jobs) is **not built-in**. Logs use SLF4J but are not structured JSON by default — the log format depends on the deployer's logging configuration (logback/log4j2).
- **Gap**: Request ID correlation exists. OpenTelemetry is integrated for batch jobs only. No full distributed tracing for REST API requests. Logs are not structured JSON by default.
- **Compensating Controls**:
  - Configure logback/log4j2 with JSON layout (e.g., logstash-logback-encoder) at deployment time
  - Add OpenTelemetry Java agent (-javaagent) at deployment for full request tracing
- **Remediation Timeline**: 14–30 days (deployment configuration)
- **Recommendation**: Document a reference logback configuration with JSON structured logging and OpenTelemetry auto-instrumentation for deployers integrating with agents.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/ServletRequestTracing.java`, `hapi-fhir-storage-batch2/src/main/java/ca/uhn/fhir/batch2/util/BatchJobOpenTelemetryUtils.java`, `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/LoggingInterceptor.java`

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: HAPI FHIR does not include any alerting configuration, CloudWatch alarms, PagerDuty integration, or SLO-based alerting. The `PerformanceTracingLoggingInterceptor` logs performance metrics (search timing, database query counts) but does not publish custom metrics to a monitoring system. Alerting is entirely deployment-dependent.
- **Gap**: No alerting infrastructure in the framework. No health check endpoints beyond the FHIR CapabilityStatement metadata endpoint.
- **Compensating Controls**:
  - Deploy with a monitoring stack (CloudWatch, Prometheus + Grafana) and configure alarms on HTTP error rates and latency
  - Use the `PerformanceTracingLoggingInterceptor` output to feed metrics dashboards
- **Remediation Timeline**: 30–60 days (deployment infrastructure)
- **Recommendation**: Implement a custom interceptor that publishes CloudWatch metrics (request count, error rate, latency percentiles) per FHIR resource type and operation.
- **Evidence**: `hapi-fhir-jpaserver-base/src/main/java/ca/uhn/fhir/jpa/interceptor/PerformanceTracingLoggingInterceptor.java`

#### ENG-Q1: Infrastructure Governance — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: **No Infrastructure-as-Code exists in this repository.** No Terraform, CloudFormation, CDK, Helm, Kustomize, or Kubernetes manifests were found. This is expected for an open-source library — infrastructure is managed by each deployer independently. The single Dockerfile (`.github/docker/Dockerfile`) is a build image for Maven publishing, not a deployable application image.
- **Gap**: No IaC governance for the agent-facing integration surface. Infrastructure configuration (API Gateway, IAM, secrets, networking) is entirely outside this repository.
- **Compensating Controls**:
  - Provide reference IaC templates (Terraform/CDK modules) for deploying HAPI FHIR with agent-ready infrastructure
  - Document the required infrastructure components for agent integration
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Create a companion repository or documentation with reference IaC for deploying HAPI FHIR with API Gateway, IAM roles, secrets management, and monitoring — pre-configured for agent integration.
- **Evidence**: No IaC files found. `.github/docker/Dockerfile` (build image only).

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: HAPI FHIR has a mature CI/CD pipeline: GitHub Actions (`pull-request.yml` → `parallel-pipeline-build.yml`) with parallel module testing, Checkstyle validation, Spotless formatting, CodeQL security analysis, and Codecov integration. Azure DevOps pipelines handle release builds. However, **no API contract testing** exists — no Pact tests, no OpenAPI validation in CI, no schema comparison between versions.
- **Gap**: Comprehensive build and test pipeline exists but lacks API contract testing specifically. Breaking changes to REST endpoints are caught by integration tests but not by dedicated contract validation.
- **Compensating Controls**:
  - Use the extensive JPA server integration test suite as a proxy for API contract validation
  - Add pre-upgrade API compatibility testing before agent tool updates
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenAPI spec generation and diff as a CI step to detect breaking API changes before they reach releases.
- **Evidence**: `.github/workflows/pull-request.yml`, `.github/workflows/parallel-pipeline-build.yml`, `.github/workflows/codeql-analysis.yml`, `.github/workflows/spotless.yml`

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: HAPI FHIR is published as Maven artifacts to Maven Central. Rollback is version-based: deployers revert to a previous artifact version. The release pipeline (`release-pipeline.yml`, `release.yml`) uses git tagging and version normalization. However, there is **no blue/green deployment, no canary deployment, no automatic rollback trigger** in the CI/CD pipeline — these are deployment-layer concerns.
- **Gap**: Library versioning supports rollback by version pinning, but no automated deployment rollback exists in this repository.
- **Compensating Controls**:
  - Pin agent deployments to specific HAPI FHIR versions with tested compatibility
  - Implement blue/green deployment at the deployer level with health check verification
- **Remediation Timeline**: 30–60 days (deployer responsibility)
- **Recommendation**: Document a versioning and rollback strategy for deployers integrating HAPI FHIR with agent systems, including database migration rollback considerations.
- **Evidence**: `release-pipeline.yml`, `.github/workflows/release.yml`

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: HAPI FHIR has **extensive test coverage**. The test infrastructure includes: `hapi-fhir-jpaserver-test-r4` (307 test files), `hapi-fhir-jpaserver-test-r5`, `hapi-fhir-jpaserver-test-dstu2`, `hapi-fhir-jpaserver-test-dstu3`, `hapi-fhir-jpaserver-test-r4b`, `hapi-fhir-test-utilities`, `hapi-fhir-jpaserver-test-utilities`, and `hapi-fhir-storage-test-utilities`. Total: 1,815 test Java files. CI runs all tests in parallel with Codecov integration. However, tests are focused on **FHIR compliance and JPA correctness** rather than agent-specific scenarios (tool binding, error recovery, concurrent access patterns).
- **Gap**: High test coverage for FHIR operations but no agent-specific test scenarios. No contract tests for agent tool definitions.
- **Compensating Controls**:
  - Leverage existing integration tests as a baseline and add agent-specific test scenarios during pilot
  - Use the test utilities framework to build agent interaction test suites
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create an agent-focused test suite that validates tool binding, error handling, pagination behavior, and concurrent access patterns expected from agent consumers.
- **Evidence**: `hapi-fhir-jpaserver-test-r4/`, `hapi-fhir-test-utilities/`, `hapi-fhir-jpaserver-test-utilities/`, `.github/workflows/parallel-pipeline-build.yml`

#### ENG-Q5: Encryption at Rest — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: **No encryption-at-rest configuration exists in this repository.** No KMS key references, no encrypted storage configuration, no database encryption settings. This is expected for an open-source library — encryption at rest is configured at the deployment layer (AWS RDS encryption, S3 bucket encryption, EBS encryption).
- **Gap**: Encryption at rest is entirely deployment-dependent. The library does not enforce or validate encryption configuration.
- **Compensating Controls**:
  - Configure encryption at rest at the database layer (RDS encryption enabled, S3 SSE-KMS)
  - Document encryption requirements in deployment guides
- **Remediation Timeline**: 14–30 days (deployment configuration)
- **Recommendation**: Document minimum encryption requirements for deployments handling PHI: RDS encryption with customer-managed KMS keys, S3 bucket encryption for binary storage, EBS encryption for all volumes.
- **Evidence**: No encryption configuration found in the repository. Absence confirmed by searching all configuration files.

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: HAPI FHIR provides several mechanisms for testing: (1) Spring Boot sample applications (`hapi-fhir-spring-boot-samples`) with pre-configured server setups, (2) extensive test utilities (`hapi-fhir-jpaserver-test-utilities` with `BaseJpaR4Test`), (3) the live demo server at `http://hapi.fhir.org`. However, there is **no Docker Compose file for local testing**, no seed data scripts for agent-representative data, and no synthetic data generator included.
- **Gap**: Test infrastructure exists for developers but no turnkey sandbox/staging environment for agent testing with production-representative data shape.
- **Compensating Controls**:
  - Use the hapi-fhir-jpaserver-starter (separate repo) as a sandbox environment
  - Generate synthetic FHIR data using Synthea for agent testing
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Create a Docker Compose setup with a pre-loaded FHIR server containing Synthea-generated patient data for agent sandbox testing.
- **Evidence**: `hapi-fhir-spring-boot/hapi-fhir-spring-boot-samples/`, `.github/docker/Dockerfile`, `hapi-fhir-jpaserver-test-utilities/`

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO (PASS — not a blocker)
- **Finding**: HAPI FHIR exposes a fully documented FHIR REST API via `RestfulServer.java` (2,163 lines). The FHIR specification itself serves as the API contract — every resource type, operation, and search parameter is defined by the HL7 FHIR standard. The server auto-generates a FHIR CapabilityStatement (metadata endpoint) that documents all supported resources, operations, and search parameters.
- **Implication**: Agent tools can be generated from the FHIR specification and the server's CapabilityStatement. No custom API documentation is needed beyond FHIR standard references.
- **Recommendation**: Use the FHIR CapabilityStatement as the authoritative source for agent tool definitions.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/RestfulServer.java`

### AUTH-Q1: Machine Identity Authentication

- **Severity**: INFO (PASS — not a blocker)
- **Finding**: HAPI FHIR provides extensible authentication hook points via the interceptor framework. The `AuthorizationInterceptor` integrates with any authentication mechanism — OAuth2 client credentials, API keys, mTLS — via the `RequestDetails` object which carries authenticated principal information. Authentication itself is not built into the framework but is fully pluggable. The deployer must configure authentication at the servlet filter or interceptor level.
- **Implication**: Machine identity authentication is achievable but requires deployer configuration. The framework supports principal attribution in all request processing paths.
- **Recommendation**: Configure OAuth2 client credentials or API key authentication at the servlet/interceptor level with principal attribution for agent identities.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/AuthorizationInterceptor.java`, `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/RestfulServer.java`

### AUTH-Q3: Action-Level Authorization

- **Severity**: INFO (PASS — capability exists)
- **Finding**: HAPI FHIR supports granular action-level authorization via `RuleOpEnum` which defines: READ, WRITE, CREATE, DELETE, PATCH, TRANSACTION, METADATA, OPERATION, GRAPHQL. The `RuleBuilder` allows constructing rules like `allow().read().resourcesOfType("Patient").withAnyId()` while denying write and delete operations. This maps directly to agent scope requirements.
- **Implication**: Agents can be restricted to specific FHIR operations per resource type. The authorization model is rich enough for agent use cases.
- **Recommendation**: Leverage `RuleOpEnum.READ` restriction for read-only agents. For future write-enabled agents, define action-level rules per resource type.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/RuleOpEnum.java`, `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/IAuthRuleBuilder.java`

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: INFO
- **Finding**: HAPI FHIR supports multi-tenancy via `ITenantIdentificationStrategy` (URL path-based or header-based tenant routing) and request partitioning. The `RequestDetails` object carries user context through the entire request lifecycle. The `ConsentInterceptor` can further scope data access based on the authenticated user's context. However, there is no explicit "on-behalf-of" flow distinguishing agent-as-self vs agent-on-behalf-of-user.
- **Implication**: For read-only agents, identity propagation is sufficient via request headers. For future user-delegated agent access, an on-behalf-of pattern would need to be implemented via custom interceptors.
- **Recommendation**: For the read-only pilot, pass the agent identity via standard authentication headers. Document the pattern for future on-behalf-of agent access.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/AuthorizationInterceptor.java`

### AUTH-Q5: Credential Management

- **Severity**: INFO (PASS — no hardcoded credentials)
- **Finding**: No hardcoded credentials, API keys, or secrets were found in the source code or configuration files. The repository does not include `.env` files, hardcoded passwords, or embedded secrets. Credential management is delegated to the deployer. CI/CD pipelines reference secrets via GitHub Actions secrets (`CODECOV_TOKEN`, `GITHUB_TOKEN`) and Azure DevOps variable groups — no secrets are committed to the repository.
- **Implication**: The library itself is clean of credential artifacts. Deployers must integrate with a secrets management system (AWS Secrets Manager, HashiCorp Vault) for agent credentials.
- **Recommendation**: Document the recommended secrets management approach for agent API keys and OAuth2 client secrets.
- **Evidence**: No hardcoded credentials found in any source or configuration files.

### DATA-Q1: Sensitive Data Classification

- **Severity**: INFO (PASS — capability exists)
- **Finding**: FHIR inherently classifies data sensitivity via Resource.meta.security (security labels), Resource.meta.tag, and the FHIR Consent resource type. HAPI FHIR implements the `ConsentInterceptor` and `IConsentService` interface which provide field-level access controls — the consent service can AUTHORIZE, REJECT, or PROCEED for each resource, and can modify returned resources to redact sensitive fields. The `SearchNarrowingInterceptor` automatically adds search parameter restrictions based on the authenticated user's access scope.
- **Implication**: Sensitive data classification and field-level access control is available via the FHIR specification's built-in mechanisms and HAPI's consent framework. Deployers must configure consent rules for agent access patterns.
- **Recommendation**: Configure `ConsentInterceptor` with an `IConsentService` implementation that restricts agent access to non-sensitive FHIR resources or redacts sensitive fields from agent-accessible responses.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/consent/ConsentInterceptor.java`, `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/SearchNarrowingInterceptor.java`

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: FHIR defines idempotent conditional create (`If-None-Exist` header) and conditional update patterns. HAPI FHIR's JPA server implements these patterns. ETags are supported via `ETagSupportEnum` for optimistic concurrency. However, since agent_scope is read-only, write idempotency is informational only.
- **Implication**: If agent scope expands to write-enabled in the future, idempotency patterns are already available in the framework.
- **Recommendation**: No action needed for read-only scope. Document conditional create/update patterns for future write-enabled agent integration.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/ETagSupportEnum.java`

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: FHIR mandates JSON and XML response formats. HAPI FHIR supports both via the `EncodingEnum` (JSON, XML) with content negotiation via `Accept` headers. JSON is the default and preferred format. All responses are structured FHIR resources conforming to published StructureDefinitions.
- **Implication**: JSON responses are ideal for LLM consumption. Agent tools can parse FHIR JSON directly with well-defined schemas.
- **Recommendation**: Configure agents to request JSON responses (`Accept: application/fhir+json`) for optimal LLM processing.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/RestfulServer.java`

### API-Q7: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: HAPI FHIR provides comprehensive event emission: (1) FHIR Subscriptions (REST-hook, WebSocket, email) via `hapi-fhir-jpaserver-subscription` module that trigger on resource changes matching subscription criteria, (2) the interceptor pointcut system with hooks at `STORAGE_PRESTORAGE_RESOURCE_CREATED`, `STORAGE_PRESTORAGE_RESOURCE_UPDATED`, `STORAGE_PRESTORAGE_RESOURCE_DELETED` for custom event processing. No external event bus integration (SNS, EventBridge, Kafka) is built-in.
- **Implication**: Event-driven agent patterns are supportable via FHIR Subscriptions. For proactive agents that respond to data changes, configure FHIR Subscriptions with REST-hook delivery to the agent orchestration layer.
- **Recommendation**: Use FHIR topic-based Subscriptions (R5) or channel Subscriptions (R4) to notify agents of relevant state changes.
- **Evidence**: `hapi-fhir-jpaserver-subscription/`, `hapi-fhir-server/src/main/java/ca/uhn/fhir/subscription/SubscriptionConstants.java`

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limit documentation or rate limit headers (`X-RateLimit-Remaining`, `Retry-After`) are implemented in the HAPI FHIR framework. Rate limiting is expected to be handled at the deployment layer (API Gateway, reverse proxy).
- **Implication**: Agents will not receive rate limit feedback from the HAPI FHIR server itself. Rate limit headers must be added at the deployment layer for agent self-throttling.
- **Recommendation**: Configure the API Gateway or reverse proxy to include `X-RateLimit-Remaining` and `Retry-After` headers in responses to agent requests.
- **Evidence**: No rate limit headers found in source code.

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: FHIR transaction Bundles (Bundle.type = "transaction") are processed atomically by the JPA server — if any entry fails, the entire transaction is rolled back via JPA/Hibernate transaction management. `TransactionDetails` tracks the state of multi-step operations. However, there is no saga pattern or explicit compensation API for cross-service workflows.
- **Implication**: Single-server transactions are atomic. Cross-service orchestration compensation would need to be implemented by the deployer or agent orchestration layer.
- **Recommendation**: For the read-only pilot, no action needed. For future write-enabled scope, ensure all write operations use FHIR transaction Bundles for atomicity.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/api/server/storage/TransactionDetails.java`

### STATE-Q2: Queryable Current State

- **Severity**: INFO (PASS)
- **Finding**: FHIR is fundamentally a queryable API. Every resource type supports GET (read), search with extensive search parameters, _include/_revinclude, and _history for previous versions. The JPA server supports all FHIR search features including chained parameters, reverse chaining, and composite search parameters. The `BasePagingProvider` with default page size of 10 and max page size of 50 ensures bounded result sets.
- **Implication**: Agents can query current state for any FHIR resource type with rich filtering. This is a strength of the FHIR API model.
- **Recommendation**: Provide agent tools with search parameter documentation from the CapabilityStatement for each resource type.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/BasePagingProvider.java`

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: HAPI FHIR supports optimistic locking via ETags. `ETagSupportEnum.ENABLED` causes the server to return ETag headers based on resource version IDs. The `ResourceTable` entity tracks `myVersion` (incrementing version counter) for each resource. Conditional updates require `If-Match` headers with the current ETag. `PreconditionFailedException` (HTTP 412) is thrown on version conflicts.
- **Implication**: Concurrency controls are robust for write operations. For read-only agents, this is informational — no concurrent write conflicts can occur.
- **Recommendation**: No action for read-only scope. For future write-enabled agents, require `If-Match` headers on all update operations.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/ETagSupportEnum.java`, `hapi-fhir-jpaserver-model/src/main/java/ca/uhn/fhir/jpa/model/entity/ResourceTable.java`

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: HAPI FHIR provides configurable limits for batch operations via `JpaStorageSettings` (e.g., `setMaximumSearchResultCountInTransaction`, `setBulkExportFileMaximumCapacity`). The `BasePagingProvider` limits result set sizes (default max 50). However, there are no agent-identity-specific transaction limits — limits apply globally, not per-caller.
- **Implication**: Read-only agents cannot trigger transaction limits. For future write-enabled scope, per-agent limits would need to be implemented via custom interceptors.
- **Recommendation**: No action for read-only scope. Document global limits for agent awareness.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/BasePagingProvider.java`

### STATE-Q7: Infrastructure Capacity

- **Severity**: INFO
- **Finding**: HAPI FHIR is a library/framework — infrastructure capacity is entirely deployment-dependent. No auto-scaling policies, load test configurations, or capacity planning documentation exists in this repository. The JPA server can be deployed on any infrastructure from a single server to a horizontally scaled cluster.
- **Implication**: Agent traffic impact on infrastructure must be assessed during deployment planning, not at the library level.
- **Recommendation**: Conduct load testing with agent-representative traffic patterns before pilot deployment.
- **Evidence**: No infrastructure capacity configuration found in the repository.

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: FHIR resources have inherent status fields (e.g., `Patient.active`, `Observation.status` with values like "preliminary", "final", "cancelled"). The FHIR specification defines draft/active/completed lifecycle for many resource types. However, there is no universal "draft" state enforced by the server — status semantics are resource-type specific.
- **Implication**: Read-only agents do not create or modify resources. For future write-enabled scope, the FHIR resource status model can support draft-then-commit workflows.
- **Recommendation**: No action for read-only scope.
- **Evidence**: FHIR specification resource status fields.

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: HAPI FHIR does not include built-in approval workflows. The interceptor framework (`SERVER_INCOMING_REQUEST_PRE_HANDLED` pointcut) could be used to implement approval gates — a custom interceptor could hold write requests pending human approval. No such interceptor exists in the framework.
- **Implication**: Read-only agents do not need approval gates. For future write-enabled scope, approval gates would need to be implemented as custom interceptors.
- **Recommendation**: No action for read-only scope. For write-enabled expansion, implement approval interceptors for high-risk FHIR operations (e.g., Patient delete, MedicationRequest create).
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/AuthorizationInterceptor.java` (interceptor framework)

### DATA-Q2: Data Residency and Sovereignty ⚡

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Healthcare data is subject to strict residency requirements (HIPAA, GDPR, provincial health data laws). HAPI FHIR is a library — it does not enforce data residency at the framework level. Data residency depends entirely on the deployment topology (database region, server location). No region-specific configuration or cross-region replication controls exist in the codebase.
- **Implication**: A read-only agent accessing a HAPI FHIR server could transmit PHI to an LLM endpoint in a different jurisdiction. Data residency must be enforced at the deployment and agent orchestration layers.
- **Recommendation**: Ensure the HAPI FHIR server, database, and LLM endpoint are co-located in the same jurisdiction. Implement data residency checks at the agent orchestration layer.
- **Evidence**: No data residency configuration found in the repository.

### DATA-Q3: Selective Query Support

- **Severity**: INFO (PASS)
- **Finding**: FHIR defines comprehensive selective query support implemented by HAPI FHIR: `_count` (page size, default 10, max 50), `_offset` (pagination), `_sort` (sorting), resource-specific search parameters (date ranges, string matching, token search, reference chaining), `_elements` (field selection), `_summary` (summary views). The `BasePagingProvider` enforces bounded result sets.
- **Implication**: Agents can construct precise queries that return only the data they need, within bounded result sets. This is a strength of the FHIR search model.
- **Recommendation**: Provide agent tools with search parameter documentation and recommend using `_count` and `_elements` to minimize response size and LLM token consumption.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/BasePagingProvider.java`

### DATA-Q4: System of Record Designations

- **Severity**: INFO (PASS)
- **Finding**: FHIR is designed as a system of record. Each FHIR resource has a unique server-assigned ID and a monotonically incrementing version ID (`meta.versionId`). The JPA server maintains the authoritative record via `ResourceTable` with version tracking. Master Data Management (MDM) is supported via the `hapi-fhir-jpaserver-mdm` module for patient matching and golden record management.
- **Implication**: The HAPI FHIR server is the system of record for the FHIR resources it stores. MDM support addresses the golden record requirement for healthcare data.
- **Recommendation**: Document which FHIR resource types are authoritative in the deployed server for agent consumption.
- **Evidence**: `hapi-fhir-jpaserver-model/src/main/java/ca/uhn/fhir/jpa/model/entity/ResourceTable.java`, `hapi-fhir-jpaserver-mdm/`

### DATA-Q5: Temporal Metadata and Freshness

- **Severity**: INFO (PASS)
- **Finding**: Every FHIR resource includes `meta.lastUpdated` (timestamp of last modification, managed by the server) and `meta.versionId` (version counter). The JPA server automatically maintains these fields via `ResourceTable.myUpdated` (DATE type) and `ResourceTable.myVersion` (LONG type). Timestamps are stored in UTC. No `Cache-Control` or `X-Data-Age` headers are returned, but the FHIR resource metadata itself provides freshness information.
- **Implication**: Agents can use `meta.lastUpdated` and `meta.versionId` to reason about data freshness. The `_lastUpdated` search parameter allows filtering by recency.
- **Recommendation**: Agent tools should extract and evaluate `meta.lastUpdated` before making decisions based on FHIR data freshness.
- **Evidence**: `hapi-fhir-jpaserver-model/src/main/java/ca/uhn/fhir/jpa/model/entity/ResourceTable.java`

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: HAPI FHIR provides comprehensive data validation via `RequestValidatingInterceptor` and `ResponseValidatingInterceptor` which validate FHIR resources against StructureDefinitions. The `hapi-fhir-validation` module with FHIR Profile validation can enforce data quality rules. However, there are no data quality dashboards, completeness metrics, null rate monitoring, or freshness SLAs built into the framework.
- **Implication**: Data validation exists at the input and output layers. Data quality metrics would need to be implemented as custom interceptors or external monitoring.
- **Recommendation**: Enable `RequestValidatingInterceptor` to enforce data quality at write time. Consider implementing a data quality metrics interceptor for agent-consumed data.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/RequestValidatingInterceptor.java`, `hapi-fhir-validation/`

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO (PASS)
- **Finding**: FHIR resources use semantically meaningful, human-readable field names defined by the HL7 specification: `Patient.name`, `Patient.birthDate`, `Observation.valueQuantity`, `MedicationRequest.dosageInstruction`, etc. No legacy abbreviations or encoded field names exist. The FHIR specification provides comprehensive documentation for every field.
- **Implication**: Agent LLMs can interpret FHIR field names without a data dictionary. This is a major advantage of the FHIR standard for agent consumption.
- **Recommendation**: No action needed. FHIR's semantic field naming is a strength for agent integration.
- **Evidence**: FHIR specification field names (inherent to all HAPI FHIR structure modules).

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO (PASS)
- **Finding**: FHIR provides a built-in metadata layer: (1) the CapabilityStatement (metadata endpoint) describes all supported resources, operations, and search parameters, (2) StructureDefinitions define the schema for every resource type, (3) SearchParameter resources document queryable fields. HAPI FHIR serves all of these via the `IServerConformanceProvider` interface. The `hapi-fhir-docs` module provides additional documentation.
- **Implication**: Agent tool generation can leverage the CapabilityStatement and StructureDefinitions as a comprehensive data catalog. No external data catalog is needed.
- **Recommendation**: Use the FHIR CapabilityStatement as the primary data catalog for agent tool definitions.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/IServerConformanceProvider.java`, `hapi-fhir-docs/`

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: HAPI FHIR's interceptor pointcut system provides hooks for all business events (`STORAGE_PRESTORAGE_RESOURCE_CREATED/UPDATED/DELETED`, `SERVER_PROCESSING_COMPLETED`, etc.) that can be used to publish custom business metrics. The `PerformanceTracingLoggingInterceptor` logs operation-level performance data. However, no pre-built business outcome metrics (resolution rates, query success rates) are included.
- **Implication**: The interceptor framework makes it straightforward to implement custom business metrics. Deployers need to build metric-publishing interceptors for agent-relevant outcomes.
- **Recommendation**: Implement a custom interceptor that publishes business metrics (successful queries per resource type, error rates per operation, search result counts) to CloudWatch or Prometheus.
- **Evidence**: `hapi-fhir-jpaserver-base/src/main/java/ca/uhn/fhir/jpa/interceptor/PerformanceTracingLoggingInterceptor.java`

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO (PASS — not a blocker)
- **Finding**: HAPI FHIR exposes a fully documented FHIR REST API via `RestfulServer.java`. The FHIR specification itself serves as the API contract. The server auto-generates a CapabilityStatement documenting all supported resources and operations.
- **Gap**: N/A — API surface is well-documented via the FHIR specification.
- **Recommendation**: Use the FHIR CapabilityStatement as the authoritative source for agent tool definitions.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/RestfulServer.java`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: `OpenApiInterceptor` dynamically generates OpenAPI 3.0 specs from the server's CapabilityStatement at runtime. No static `openapi.yaml` exists.
- **Gap**: No static, version-controlled OpenAPI specification file.
- **Recommendation**: Add a CI step to export and commit the OpenAPI spec for version-controlled agent tool binding.
- **Evidence**: `hapi-fhir-server-openapi/src/main/java/ca/uhn/fhir/rest/openapi/OpenApiInterceptor.java`

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: All errors return FHIR `OperationOutcome` resources with severity, code, and diagnostics. Each exception maps to a specific HTTP status code. No explicit `retryable` field.
- **Gap**: Agents must infer retryability from HTTP status codes rather than an explicit field.
- **Recommendation**: Document retry semantics per HTTP status code for agent consumers.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/ExceptionHandlingInterceptor.java`, `hapi-fhir-base/src/main/java/ca/uhn/fhir/rest/server/exceptions/BaseServerResponseException.java`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: FHIR conditional create/update patterns with `If-None-Exist` headers are supported. ETag support via `ETagSupportEnum`. Read-only scope makes this informational.
- **Gap**: N/A for read-only scope.
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/ETagSupportEnum.java`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: FHIR mandates JSON and XML formats. HAPI FHIR supports both with content negotiation. JSON is default and preferred.
- **Gap**: N/A.
- **Recommendation**: Configure agents to request `application/fhir+json`.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/RestfulServer.java`

#### API-Q6: Asynchronous Operation Support
- **Severity**: RISK-QUALITY
- **Finding**: Batch2 framework provides robust async support. BulkDataExportProvider implements $export with polling pattern. No webhook callbacks.
- **Gap**: Polling only — no webhook callback pattern.
- **Recommendation**: Document polling intervals for async operations. Consider webhook support.
- **Evidence**: `hapi-fhir-storage-batch2-jobs/src/main/java/ca/uhn/fhir/batch2/jobs/export/BulkDataExportProvider.java`

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: FHIR Subscriptions and interceptor pointcut system support event emission. No external event bus integration built-in.
- **Gap**: No SNS/EventBridge/Kafka integration built-in.
- **Recommendation**: Use FHIR Subscriptions with REST-hook delivery for agent event patterns.
- **Evidence**: `hapi-fhir-jpaserver-subscription/`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit documentation or headers implemented. Deployment-layer concern.
- **Gap**: No rate limit feedback to agents from the server itself.
- **Recommendation**: Configure API Gateway to return rate limit headers.
- **Evidence**: No rate limit code found in the repository.

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO (PASS — not a blocker)
- **Finding**: Extensible authentication via interceptor framework. Supports OAuth2, API keys, mTLS via pluggable configuration. Deployer must configure.
- **Gap**: No built-in authentication — requires deployer configuration.
- **Recommendation**: Configure OAuth2 client credentials authentication for agent identities.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/AuthorizationInterceptor.java`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: `AuthorizationInterceptor` with `RuleBuilder` supports per-resource-type, per-compartment scoping. No default rules enabled.
- **Gap**: Framework provides capability but does not enforce least-privilege by default.
- **Recommendation**: Document reference `AuthorizationInterceptor` configuration for agent identities.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/RuleBuilder.java`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: INFO (PASS — capability exists)
- **Finding**: `RuleOpEnum` defines READ, WRITE, CREATE, DELETE, PATCH, TRANSACTION, METADATA, OPERATION, GRAPHQL. Full action-level granularity.
- **Gap**: N/A — capability is comprehensive.
- **Recommendation**: Use `RuleOpEnum.READ` restriction for read-only agents.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/RuleOpEnum.java`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: Multi-tenancy and request partitioning supported. `RequestDetails` carries user context. No explicit on-behalf-of flow.
- **Gap**: No agent-as-self vs agent-on-behalf-of-user distinction.
- **Recommendation**: Pass agent identity via standard auth headers for the read-only pilot.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/AuthorizationInterceptor.java`

#### AUTH-Q5: Credential Management
- **Severity**: INFO (PASS)
- **Finding**: No hardcoded credentials found. CI secrets managed via GitHub Actions and Azure DevOps. Clean repository.
- **Gap**: N/A.
- **Recommendation**: Document secrets management approach for deployers.
- **Evidence**: No hardcoded credentials found in any files.

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: `BalpAuditCaptureInterceptor` generates FHIR AuditEvent resources (IHE BALP compliant). Immutability depends on deployment storage backend.
- **Gap**: Audit generation exists but immutability is not enforced by the framework.
- **Recommendation**: Deploy with `IBalpAuditEventSink` writing to immutable storage.
- **Evidence**: `hapi-fhir-storage/src/main/java/ca/uhn/fhir/storage/interceptor/balp/BalpAuditCaptureInterceptor.java`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: No built-in identity suspension mechanism. Identity management delegated to deployment authentication layer.
- **Gap**: No framework-level identity revocation.
- **Recommendation**: Implement identity deny-list interceptor or leverage external identity provider revocation.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/AuthorizationInterceptor.java`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: FHIR transaction Bundles are atomic via JPA/Hibernate. `TransactionDetails` tracks multi-step operations. No saga pattern for cross-service workflows.
- **Gap**: No explicit compensation API for cross-service workflows.
- **Recommendation**: Use FHIR transaction Bundles for atomicity in future write-enabled scope.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/api/server/storage/TransactionDetails.java`

#### STATE-Q2: Queryable Current State
- **Severity**: INFO (PASS)
- **Finding**: FHIR is fundamentally queryable. All resources support GET, search with extensive parameters, _history. Bounded result sets via `BasePagingProvider`.
- **Gap**: N/A.
- **Recommendation**: Provide agent tools with search parameter documentation.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/BasePagingProvider.java`

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: ETag support with optimistic locking. `ResourceTable.myVersion` tracks versions. HTTP 412 on conflicts.
- **Gap**: N/A for read-only scope.
- **Recommendation**: No action for read-only scope.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/ETagSupportEnum.java`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: Retry logic via `Retrier.java` (Spring Retry, exponential backoff). No circuit breaker implementations.
- **Gap**: No circuit breaker pattern for external dependency calls.
- **Recommendation**: Add Resilience4j circuit breakers for terminology/validation service calls.
- **Evidence**: `hapi-fhir-jpaserver-searchparam/src/main/java/ca/uhn/fhir/jpa/searchparam/retry/Retrier.java`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No built-in rate limiting or throttling mechanism. Deployment-layer concern.
- **Gap**: No rate limiting at any layer within the framework.
- **Recommendation**: Deploy behind API Gateway with rate limits per agent identity.
- **Evidence**: No rate limiting code found.

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Configurable batch operation limits via `JpaStorageSettings`. `BasePagingProvider` limits result sets. No per-agent limits.
- **Gap**: Global limits only, not per-agent identity.
- **Recommendation**: No action for read-only scope.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/BasePagingProvider.java`

#### STATE-Q7: Infrastructure Capacity
- **Severity**: INFO
- **Finding**: Library/framework — capacity is deployment-dependent. No load test configs or auto-scaling in repo.
- **Gap**: Entirely deployment-dependent.
- **Recommendation**: Conduct load testing with agent-representative traffic before pilot.
- **Evidence**: No infrastructure capacity configuration found.

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: FHIR resources have inherent status fields. No universal "draft" state enforced by server.
- **Gap**: N/A for read-only scope.
- **Recommendation**: No action for read-only scope.
- **Evidence**: FHIR specification resource status fields.

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No built-in approval workflows. Interceptor framework could support custom approval gates.
- **Gap**: N/A for read-only scope.
- **Recommendation**: No action for read-only scope.
- **Evidence**: Interceptor framework in `AuthorizationInterceptor.java`.

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: Spring Boot samples, extensive test utilities, live demo server exist. No Docker Compose, no seed data scripts.
- **Gap**: No turnkey sandbox for agent testing with production-representative data.
- **Recommendation**: Create Docker Compose setup with Synthea-generated patient data.
- **Evidence**: `hapi-fhir-spring-boot/hapi-fhir-spring-boot-samples/`, `hapi-fhir-jpaserver-test-utilities/`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO (PASS — capability exists)
- **Finding**: FHIR security labels, `ConsentInterceptor`, `IConsentService`, and `SearchNarrowingInterceptor` provide field-level access controls. Deployer configuration required.
- **Gap**: Deployer must configure consent rules for agent access.
- **Recommendation**: Configure `ConsentInterceptor` for agent access patterns.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/consent/ConsentInterceptor.java`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No data residency enforcement at framework level. Deployment-dependent.
- **Gap**: No region-specific configuration. PHI could cross jurisdictions via agent-LLM interactions.
- **Recommendation**: Co-locate HAPI FHIR server, database, and LLM endpoint in same jurisdiction.
- **Evidence**: No data residency configuration found.

#### DATA-Q3: Selective Query Support
- **Severity**: INFO (PASS)
- **Finding**: Comprehensive FHIR search with `_count`, `_offset`, `_sort`, `_elements`, `_summary`. Bounded result sets.
- **Gap**: N/A.
- **Recommendation**: Use `_count` and `_elements` to minimize response size.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/BasePagingProvider.java`

#### DATA-Q4: System of Record Designations
- **Severity**: INFO (PASS)
- **Finding**: FHIR resources have unique IDs and version tracking. MDM module supports golden records.
- **Gap**: N/A.
- **Recommendation**: Document authoritative resource types for agent consumption.
- **Evidence**: `hapi-fhir-jpaserver-model/src/main/java/ca/uhn/fhir/jpa/model/entity/ResourceTable.java`

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: INFO (PASS)
- **Finding**: `meta.lastUpdated` and `meta.versionId` maintained automatically. UTC timestamps. `_lastUpdated` search parameter available.
- **Gap**: No `Cache-Control` or `X-Data-Age` headers.
- **Recommendation**: Agent tools should evaluate `meta.lastUpdated` for freshness.
- **Evidence**: `hapi-fhir-jpaserver-model/src/main/java/ca/uhn/fhir/jpa/model/entity/ResourceTable.java`

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: `LoggingInterceptor` logs metadata not bodies by default. No PII redaction middleware. PHI can leak via exception diagnostics.
- **Gap**: No automated PII/PHI redaction in logging.
- **Recommendation**: Implement PII-aware logging interceptor. Configure CloudWatch Logs data protection.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/LoggingInterceptor.java`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: `RequestValidatingInterceptor` and `ResponseValidatingInterceptor` validate against StructureDefinitions. No data quality dashboards.
- **Gap**: No data quality metrics or monitoring.
- **Recommendation**: Enable validation interceptors. Consider data quality metrics interceptor.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/RequestValidatingInterceptor.java`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: FHIR specification versioning (DSTU2–R5) via separate modules. CapabilityStatement exposes version. No breaking change detection in CI.
- **Gap**: No automated breaking-change detection for the REST API surface.
- **Recommendation**: Add OpenAPI diff checks to CI.
- **Evidence**: `hapi-fhir-structures-r4/`, `hapi-fhir-structures-r5/`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO (PASS)
- **Finding**: FHIR uses semantically meaningful field names: `Patient.name`, `Observation.valueQuantity`, etc.
- **Gap**: N/A.
- **Recommendation**: No action needed.
- **Evidence**: FHIR specification field names.

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO (PASS)
- **Finding**: CapabilityStatement, StructureDefinitions, and SearchParameter resources serve as a comprehensive metadata layer.
- **Gap**: N/A.
- **Recommendation**: Use CapabilityStatement as primary data catalog for agent tools.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/IServerConformanceProvider.java`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: `ServletRequestTracing` for X-Request-ID. `BatchJobOpenTelemetryUtils` for batch job tracing. Not full distributed tracing for REST requests. Logs not structured JSON by default.
- **Gap**: Partial tracing (batch only). No structured JSON logging by default.
- **Recommendation**: Deploy with OpenTelemetry Java agent and JSON logback configuration.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/ServletRequestTracing.java`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: No alerting configuration. `PerformanceTracingLoggingInterceptor` logs metrics. Alerting is deployment-dependent.
- **Gap**: No alerting infrastructure in the framework.
- **Recommendation**: Deploy monitoring stack and configure alarms.
- **Evidence**: `hapi-fhir-jpaserver-base/src/main/java/ca/uhn/fhir/jpa/interceptor/PerformanceTracingLoggingInterceptor.java`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: Interceptor pointcut system enables custom business metrics. No pre-built metrics.
- **Gap**: No pre-built business outcome metrics.
- **Recommendation**: Implement custom metrics-publishing interceptor.
- **Evidence**: Interceptor pointcut system.

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance
- **Severity**: RISK-QUALITY
- **Finding**: No IaC in repository. Expected for open-source library. Single build Dockerfile.
- **Gap**: No IaC governance for agent-facing infrastructure.
- **Recommendation**: Create companion IaC repository for agent-ready deployment.
- **Evidence**: No IaC files found. `.github/docker/Dockerfile` (build image only).

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: Mature CI/CD: GitHub Actions parallel builds, Checkstyle, Spotless, CodeQL, Codecov. No API contract testing (Pact, OpenAPI diff).
- **Gap**: No dedicated API contract testing.
- **Recommendation**: Add OpenAPI diff checks to CI pipeline.
- **Evidence**: `.github/workflows/pull-request.yml`, `.github/workflows/parallel-pipeline-build.yml`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: Maven artifact versioning supports version-based rollback. No automated deployment rollback.
- **Gap**: No automated deployment rollback in repository.
- **Recommendation**: Document rollback strategy for deployers.
- **Evidence**: `release-pipeline.yml`, `.github/workflows/release.yml`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: 1,815 test Java files. Extensive FHIR compliance testing. Parallel CI with Codecov. No agent-specific test scenarios.
- **Gap**: No agent-specific test scenarios.
- **Recommendation**: Create agent-focused test suite.
- **Evidence**: `hapi-fhir-jpaserver-test-r4/`, `hapi-fhir-test-utilities/`

#### ENG-Q5: Encryption at Rest
- **Severity**: RISK-QUALITY
- **Finding**: No encryption configuration in repository. Deployment-dependent.
- **Gap**: Encryption at rest entirely deployment-dependent.
- **Recommendation**: Document encryption requirements for PHI-handling deployments.
- **Evidence**: No encryption configuration found.

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/RestfulServer.java` | API-Q1, API-Q5, AUTH-Q1 |
| `hapi-fhir-server-openapi/src/main/java/ca/uhn/fhir/rest/openapi/OpenApiInterceptor.java` | API-Q2 |
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/ExceptionHandlingInterceptor.java` | API-Q3, DATA-Q6 |
| `hapi-fhir-base/src/main/java/ca/uhn/fhir/rest/server/exceptions/BaseServerResponseException.java` | API-Q3 |
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/ETagSupportEnum.java` | API-Q4, STATE-Q3 |
| `hapi-fhir-storage-batch2-jobs/src/main/java/ca/uhn/fhir/batch2/jobs/export/BulkDataExportProvider.java` | API-Q6 |
| `hapi-fhir-storage-batch2/src/main/java/ca/uhn/fhir/batch2/util/BatchJobOpenTelemetryUtils.java` | API-Q6, OBS-Q1 |
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/AuthorizationInterceptor.java` | AUTH-Q1, AUTH-Q2, AUTH-Q4, AUTH-Q7, HITL-Q2 |
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/RuleBuilder.java` | AUTH-Q2 |
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/RuleOpEnum.java` | AUTH-Q2, AUTH-Q3 |
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/IAuthRuleBuilder.java` | AUTH-Q3 |
| `hapi-fhir-storage/src/main/java/ca/uhn/fhir/storage/interceptor/balp/BalpAuditCaptureInterceptor.java` | AUTH-Q6 |
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/LoggingInterceptor.java` | AUTH-Q6, DATA-Q6, OBS-Q1 |
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/api/server/storage/TransactionDetails.java` | STATE-Q1 |
| `hapi-fhir-jpaserver-searchparam/src/main/java/ca/uhn/fhir/jpa/searchparam/retry/Retrier.java` | STATE-Q4 |
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/BasePagingProvider.java` | STATE-Q2, STATE-Q6, DATA-Q3 |
| `hapi-fhir-jpaserver-model/src/main/java/ca/uhn/fhir/jpa/model/entity/ResourceTable.java` | STATE-Q3, DATA-Q4, DATA-Q5 |
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/consent/ConsentInterceptor.java` | DATA-Q1 |
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/SearchNarrowingInterceptor.java` | DATA-Q1 |
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/RequestValidatingInterceptor.java` | DATA-Q7 |
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/IServerConformanceProvider.java` | DISC-Q3 |
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/ServletRequestTracing.java` | OBS-Q1 |
| `hapi-fhir-jpaserver-base/src/main/java/ca/uhn/fhir/jpa/interceptor/PerformanceTracingLoggingInterceptor.java` | OBS-Q2, OBS-Q3 |
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/subscription/SubscriptionConstants.java` | API-Q7 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/pull-request.yml` | ENG-Q2 |
| `.github/workflows/parallel-pipeline-build.yml` | ENG-Q2, ENG-Q4, DISC-Q1 |
| `.github/workflows/release.yml` | ENG-Q3 |
| `.github/workflows/codeql-analysis.yml` | ENG-Q2 |
| `.github/workflows/spotless.yml` | ENG-Q2 |
| `release-pipeline.yml` | ENG-Q3 |
| `snapshot-pipeline.yml` | ENG-Q3 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `.github/docker/Dockerfile` | ENG-Q1, HITL-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `pom.xml` (root) | Service archetype detection |
| 63 module `pom.xml` files | Service archetype detection |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `hapi-fhir-spring-boot/hapi-fhir-spring-boot-samples/*/src/main/resources/application.yml` | HITL-Q3 |
| `.editorconfig` | Code quality (background) |
| `.pre-commit-config.yaml` | Code quality (background) |

### Module Directories Referenced
| Directory | Questions Referenced |
|-----------|---------------------|
| `hapi-fhir-jpaserver-subscription/` | API-Q7 |
| `hapi-fhir-jpaserver-mdm/` | DATA-Q4 |
| `hapi-fhir-structures-r4/` | DISC-Q1 |
| `hapi-fhir-structures-r5/` | DISC-Q1 |
| `hapi-fhir-validation/` | DATA-Q7 |
| `hapi-fhir-docs/` | DISC-Q3 |
| `hapi-fhir-jpaserver-test-r4/` | ENG-Q4 |
| `hapi-fhir-test-utilities/` | ENG-Q4, HITL-Q3 |
| `hapi-fhir-jpaserver-test-utilities/` | ENG-Q4, HITL-Q3 |
| `hapi-fhir-spring-boot/hapi-fhir-spring-boot-samples/` | HITL-Q3 |
