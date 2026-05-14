# Agentic Readiness Analysis Report

**Target**: hapi-fhir (HAPI FHIR Monorepo)
**Date**: 2026-04-30
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**Repository Type**: monorepo
**Service Archetype**: stateful-crud (auto-detected) — assessed as a composite FHIR server framework
**Agent Scope**: read-only
**Priority**: P2
**Tags**: java, healthcare, rest-api
**Context**: Open-source Java implementation of the HL7 FHIR healthcare standard.

**Archetype Justification**: The primary logical sub-service (hapi-fhir-jpaserver-base) owns persistent state via JPA/Hibernate, exposes full CRUD operations on FHIR resources, and manages entity lifecycle — matching the stateful-crud archetype. Supporting modules (base, client, structures) are libraries, but the monorepo's dominant persona is a stateful FHIR server framework.

**Surface flags**:
- has_persistent_data_store: true
- has_http_rpc_surface: true
- has_auth_surface: true
- has_write_operations: true
- has_logging_of_user_data: true

**Note**: This is an open-source framework/library monorepo, not a deployed cloud service. It provides the building blocks for FHIR servers. Findings reflect the capabilities the framework provides to deployers, not the configuration of a running instance. Deployer-controlled aspects (IaC, secrets management, audit log storage, encryption at rest) are evaluated as gaps in the framework's defaults, with recommendations for deployers.

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 1 | **RISK-SAFETY**: 8 | **RISK-QUALITY**: 9 | **INFOs**: 23

Under the new tiered DATA-Q1 model, the "framework provides hooks but does not enforce security by default" finding resolves to RISK-SAFETY rather than BLOCKER (HAPI FHIR is a framework — consuming apps must configure `AuthorizationInterceptor`, `SearchNarrowingInterceptor`, and compartment rules). Only AUTH-Q1 (machine identity) remains as a BLOCKER that deployers must resolve before agent integration. Estimated runway: 30–90 days.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 2 |
| RISK-SAFETY | 8 |
| RISK-QUALITY | 9 |
| INFO | 22 |
| N/A | 0 |
| Not Evaluated (extended) | 2 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 17
**Extended Questions Not Triggered**: 2
**Questions N/A (repo_type: monorepo)**: 0
**Service Archetype**: stateful-crud (auto-detected)

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: HAPI FHIR provides a comprehensive interceptor framework (`AuthorizationInterceptor`, `IServerInterceptor` hooks at `Pointcut.SERVER_INCOMING_REQUEST_PRE_HANDLED`) that allows deployers to plug in authentication logic. However, the framework does not ship with a built-in machine identity authentication mechanism (no OAuth2 client credentials flow, no API key authentication with principal attribution, no mTLS support out of the box). Authentication is entirely delegated to the deployer's interceptor configuration or external gateway.
- **Gap**: No built-in machine identity authentication. Deployers must implement or integrate an authentication interceptor (e.g., SMART on FHIR, OAuth2 bearer token validation) to distinguish which agent made a call. Without this, all agent requests are anonymous or undifferentiated.
- **Remediation**:
  - **Immediate**: Implement an authentication interceptor that validates OAuth2 bearer tokens or API keys and attributes the authenticated principal to each request via `RequestDetails.setAttribute()`. Consider using the SMART on FHIR authorization profile.
  - **Target State**: Every API request from an agent carries a validated machine identity that is captured in `RequestDetails` and available for audit logging and authorization decisions.
  - **Estimated Effort**: Medium (30–60 days for deployer integration with an identity provider like Keycloak, Cognito, or Okta)
  - **Dependencies**: AUTH-Q6 (audit logging requires identity to be meaningful)
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/AuthorizationInterceptor.java`, `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/RestfulServer.java`

### DATA-Q1: Sensitive Data Classification ⚡ (Tiered) — Demoted from BLOCKER

_Resolved to RISK-SAFETY under the tiered model. See RISK-SAFETY section below._

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### DATA-Q1: Sensitive Data Classification ⚡ (Tiered) — Demoted from BLOCKER

- **Severity**: RISK-SAFETY
- **Stage A**: Yes — HAPI FHIR handles PHI, PII, and clinical data across all FHIR resource types (Patient, Observation, MedicationRequest, etc.) by design.
- **B1 — Agent-facing API response scoping: CLEAR at framework level.** The framework provides robust hooks: `SearchNarrowingInterceptor` (`hapi-fhir-server/.../SearchNarrowingInterceptor.java:93-250`) narrows searches to authorized compartments via `buildAuthorizedList()`. `AuthorizationInterceptor` (`.../AuthorizationInterceptor.java:77-150`) applies rules at `SERVER_INCOMING_REQUEST_PRE_HANDLED`, `STORAGE_PRESHOW_RESOURCES`, and `SERVER_OUTGOING_RESPONSE` pointcuts. FHIR-native `_summary` and `_elements` parameters support field selection.
- **B2 — Access control differentiation: CLEAR at framework level.** `RuleBuilder` (`.../RuleBuilder.java:49-1088`) supports fluent allow/deny rules scoped by resource type, operation, instance, compartment (e.g., `inCompartment("Patient", patientId)`), and tenant. Default policy is `PolicyEnum.DENY` when the interceptor is registered.
- **B3 — Formal classification metadata: CLEAR.** FHIR's native `Meta.security` IS formal, machine-readable classification — HL7 security-label CodeSystem with values like `ANONYMIZE`/`ENCRYPT`/`REDACT`. Framework supports the structure; enforcement is app responsibility.
- **Framework default behavior concern**: If a deployer registers NO `AuthorizationInterceptor`, the server returns all PHI fields without authentication/authorization. This is the canonical framework-vs-application pattern; for any PHI deployment, configuring security is non-optional.
- **Overall**: RISK-SAFETY at the framework level — hooks exist, defaults-deny works when enabled. A correctly-configured deployment moves this to CLEAR. The severity reflects the risk that a consumer might deploy without registering the interceptor.
- **Compensating Controls**:
  - Register `AuthorizationInterceptor` with explicit allow rules and default-deny
  - Register `SearchNarrowingInterceptor` with compartment narrowing
  - Apply `Meta.security` labels per HL7 confidentiality taxonomy on stored resources
  - Test rules with representative PHI scenarios before agent exposure
- **Remediation Timeline**: 30–60 days (configuration effort; the framework primitives exist)
- **Recommendation**: Treat `AuthorizationInterceptor` registration as a required deployment step. Document the minimum rule set for agent access.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/SearchNarrowingInterceptor.java:93-250`, `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/AuthorizationInterceptor.java:77-150`, `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/RuleBuilder.java:49-1088`, `hapi-fhir-docs/src/main/java/ca/uhn/hapi/fhir/docs/AuthorizationInterceptors.java` (reference compartment rules).

#### AUTH-Q2: Scoped Permissions — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The `RuleBuilder` class (52+ auth classes in the `auth` package) provides a fluent API for defining fine-grained authorization rules scoped by resource type, operation type, and compartment. Rules can be constructed like: `allow().read().resourcesOfType("Patient").inCompartment("Patient", patientId)`. This enables least-privilege scoping per agent identity. However, the framework provides the capability — the deployer must configure it. No default authorization rules are shipped.
- **Gap**: Authorization rules are not configured by default. A deployment without explicit `AuthorizationInterceptor` rules allows unrestricted access. Deployers must explicitly configure scoped permissions for agent identities.
- **Compensating Controls**:
  - Deploy the `AuthorizationInterceptor` with read-only rules restricting agent access to specific resource types
  - Use API Gateway policies to enforce resource-level access control upstream of HAPI FHIR
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement a custom `AuthorizationInterceptor` subclass that defines read-only rules for agent identities, scoped to the specific FHIR resource types the agent needs.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/RuleBuilder.java`, `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/IAuthRuleBuilder.java`

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: HAPI FHIR provides a `LoggingInterceptor` that can log request details including request type, URL, user agent, and request ID. The framework also supports FHIR AuditEvent resource creation. However, there is no built-in immutable audit log mechanism — no CloudTrail integration, no tamper-evident log storage, no automatic audit event generation for every operation. The `LoggingInterceptor` logs to SLF4J which delegates to the deployer's logging backend (logback, log4j2) with no immutability guarantees.
- **Gap**: No immutable, tamper-evident audit logging configured by default. Audit events are not automatically generated for all operations. Log immutability depends entirely on the deployer's logging infrastructure.
- **Compensating Controls**:
  - Configure the `LoggingInterceptor` to log all operations with principal identity and ship logs to an append-only store (S3 with Object Lock, CloudWatch Logs)
  - Implement a custom interceptor that creates FHIR AuditEvent resources for every agent-initiated request
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement an AuditEvent-generating interceptor and configure immutable log storage at the infrastructure layer.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/LoggingInterceptor.java`

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The framework does not provide a built-in mechanism for suspending or revoking individual agent identities. Since authentication is delegated to external interceptors (AUTH-Q1), identity lifecycle management (creation, suspension, revocation) is also an external concern. The `AuthorizationInterceptor` can dynamically evaluate rules per request, which could be used to implement suspension by returning deny rules for specific identities, but this pattern is not implemented out of the box.
- **Gap**: No built-in agent identity suspension mechanism. Revoking a misbehaving agent requires changes at the identity provider or API gateway level, not within HAPI FHIR itself.
- **Compensating Controls**:
  - Implement identity suspension at the API gateway or identity provider (e.g., revoke OAuth2 client credentials, disable API key)
  - Build a custom `AuthorizationInterceptor` that checks a suspension list before evaluating authorization rules
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement agent identity suspension at the identity provider layer (Keycloak, Cognito) and ensure HAPI FHIR's auth interceptor validates token freshness.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/AuthorizationInterceptor.java`

#### STATE-Q1: Compensation and Rollback ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: HAPI FHIR's JPA layer uses Spring `@Transactional` annotations for database operations, and FHIR transaction bundles are processed atomically (all-or-nothing) at the database level. The storage layer (`hapi-fhir-storage`) supports transaction rollback on failure. However, there is no explicit saga pattern or application-level compensation logic for multi-step operations that span multiple services or external systems. For the Batch2 framework (used for bulk operations), job steps have error handling but no built-in compensating transactions.
- **Gap**: No application-level compensation or saga pattern for complex multi-step workflows. Database-level transaction rollback exists for single-database operations, but cross-service compensation is not implemented.
- **Compensating Controls**:
  - Limit agent operations to single-step reads (aligned with read-only scope)
  - For future write scope, implement saga patterns in the orchestration layer above HAPI FHIR
- **Remediation Timeline**: 60–90 days (for write-scope enablement)
- **Recommendation**: For read-only agents, database transaction rollback is sufficient. Before enabling write scope, implement compensation logic for multi-step FHIR operations.
- **Evidence**: `hapi-fhir-jpaserver-base/`, `hapi-fhir-storage/`, `hapi-fhir-storage-batch2/src/main/java/ca/uhn/fhir/batch2/coordinator/JobStepExecutor.java`

#### DATA-Q2: Data Residency and Sovereignty ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Healthcare data has residency requirements (HIPAA, GDPR). The framework does not enforce data residency — database region, replication, and data sovereignty are deployer infrastructure decisions. No region configuration or cross-region data transfer controls found in the codebase.
- **Gap**: No framework-level data residency enforcement. Entirely deployer responsibility. An agent sending healthcare data to an LLM endpoint in another region could create a compliance violation.
- **Compensating Controls**:
  - Configure database and server deployment in compliant regions at the infrastructure layer
  - Use VPC endpoints and data transfer policies to prevent cross-region data movement
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document data residency requirements in the HAPI FHIR deployment guide. Enforce region constraints at the infrastructure layer.
- **Evidence**: No region or residency configuration found.

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: HAPI FHIR does not include built-in rate limiting middleware or interceptors. A search for rate limiting patterns found only `PersistedJpaBundleProvider.java` with pagination-related limits, not API-layer rate limiting. The framework's interceptor architecture could support a custom rate limiting interceptor, but none is provided. There is no `X-RateLimit-Remaining` or `Retry-After` header support.
- **Gap**: No API-layer rate limiting to prevent runaway agent loops from overwhelming the server. A misconfigured or misbehaving agent could issue requests at machine speed with no throttling.
- **Compensating Controls**:
  - Deploy rate limiting at the API gateway or load balancer level (AWS API Gateway usage plans, NGINX rate limiting)
  - Implement a custom HAPI FHIR interceptor that enforces per-client rate limits
- **Remediation Timeline**: 30 days
- **Recommendation**: Implement rate limiting at the API gateway layer and configure per-agent-identity throttling. Consider building a `RateLimitingInterceptor` for HAPI FHIR.
- **Evidence**: `hapi-fhir-jpaserver-base/src/main/java/ca/uhn/fhir/jpa/search/PersistedJpaBundleProvider.java`, No rate limiting interceptor found in `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/`

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The `AuthorizationInterceptor` and `RuleBuilder` support action-level authorization at a granular level. Rules can be defined per FHIR operation type: `allow().read()`, `allow().write()`, `allow().delete()`, `allow().operation()`, `allow().transaction()`, `allow().patch()`, `allow().graphQL()`, etc. The `RuleImplOp` class evaluates `RestOperationTypeEnum` which includes READ, VREAD, SEARCH, CREATE, UPDATE, DELETE, PATCH, HISTORY, and EXTENDED_OPERATION. This provides fine-grained action-level authorization. However, since AUTH-Q2 already covers scoped permissions as RISK-SAFETY and the action-level mechanism is the same RuleBuilder framework, and the framework ships unconfigured, the practical risk is the same: deployers must configure it.
- **Gap**: Action-level authorization capability exists but is not configured by default. Same gap as AUTH-Q2: deployers must implement and configure rules.
- **Compensating Controls**:
  - Use the RuleBuilder to restrict agent identities to read-only operations: `allow().read().allResources().withAnyId()`
  - Enforce action-level restrictions at the API gateway (allow only GET methods for agent API keys)
- **Remediation Timeline**: 30 days
- **Recommendation**: Configure action-level rules in the AuthorizationInterceptor for agent identities, limiting to read operations.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/RuleBuilder.java`, `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/RuleImplOp.java`

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The `LoggingInterceptor` logs request details using a configurable message format with template variables (`${requestUrl}`, `${requestHeader.Authorization}`, etc.). It can log request bodies and response bodies. In a healthcare context, request and response bodies contain PHI by definition. There is no built-in PII/PHI masking or redaction in the logging interceptor. The standardization interceptors (`StandardizingInterceptor`, `EmailStandardizer`, etc.) operate on FHIR resource data, not on log output. No Amazon Macie integration or log scrubbing middleware found.
- **Gap**: No PII/PHI redaction in logs. If the `LoggingInterceptor` is configured to log request/response bodies (common for debugging), PHI will appear in log output. This creates a compliance risk (HIPAA, GDPR) when logs are shipped to centralized logging systems.
- **Compensating Controls**:
  - Configure the LoggingInterceptor to exclude request/response bodies from logs
  - Implement a custom logging interceptor that masks PHI fields before logging
- **Remediation Timeline**: 30 days
- **Recommendation**: Configure logging to exclude PHI-containing fields. Implement log scrubbing or field-level masking before shipping logs to centralized systems.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/LoggingInterceptor.java`

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: HAPI FHIR uses FHIR OperationOutcome resources as structured error responses. The `ExceptionHandlingInterceptor` converts exceptions into OperationOutcome resources with severity, code, and diagnostics fields. `BaseServerResponseException` carries HTTP status codes and can include an `IBaseOperationOutcome`. This is a well-structured, standard-compliant error format. However, OperationOutcome does not include an explicit machine-readable "retryable" flag — agents must infer retryability from the HTTP status code and issue type.
- **Gap**: No explicit retryable/non-retryable indicator in error responses. Agents must infer retryability from HTTP status codes (429, 503 = retryable; 400, 404 = terminal) and FHIR issue types.
- **Compensating Controls**:
  - Document the retryable/non-retryable mapping for agents in the API documentation
  - Implement a custom interceptor that adds `Retry-After` headers for retryable errors
- **Remediation Timeline**: 14 days
- **Recommendation**: Extend the `ExceptionHandlingInterceptor` or add a post-processing interceptor that includes `Retry-After` headers for 429/503 responses and documents the retryability mapping.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/ExceptionHandlingInterceptor.java`, `hapi-fhir-base/src/main/java/ca/uhn/fhir/rest/server/exceptions/BaseServerResponseException.java`

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: HAPI FHIR uses FHIR OperationOutcome resources as structured error responses. The `ExceptionHandlingInterceptor` converts exceptions into OperationOutcome resources with severity, code, and diagnostics fields. `BaseServerResponseException` carries HTTP status codes and can include an `IBaseOperationOutcome`. This is a well-structured, standard-compliant error format. However, OperationOutcome does not include an explicit machine-readable "retryable" flag — agents must infer retryability from the HTTP status code and issue type.
- **Gap**: No explicit retryable/non-retryable indicator in error responses. Agents must infer retryability from HTTP status codes (429, 503 = retryable; 400, 404 = terminal) and FHIR issue types.
- **Compensating Controls**:
  - Document the retryable/non-retryable mapping for agents in the API documentation
  - Implement a custom interceptor that adds `Retry-After` headers for retryable errors
- **Remediation Timeline**: 14 days
- **Recommendation**: Extend the `ExceptionHandlingInterceptor` or add a post-processing interceptor that includes `Retry-After` headers for 429/503 responses and documents the retryability mapping.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/ExceptionHandlingInterceptor.java`, `hapi-fhir-base/src/main/java/ca/uhn/fhir/rest/server/exceptions/BaseServerResponseException.java`

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY
- **Finding**: HAPI FHIR has excellent built-in FHIR version support: DSTU2, DSTU2.1, DSTU3, R4, R4B, R5 are all supported via dedicated `hapi-fhir-structures-*` modules. The `FhirVersionEnum` provides programmatic version detection. The CapabilityStatement resource serves as a machine-readable API contract describing supported resources, operations, and search parameters. The server auto-generates CapabilityStatement at runtime. However, there is no breaking change detection in CI (no Pact tests, no OpenAPI diff, no `buf breaking` equivalent). The project uses Maven versioning (currently 8.9.8-SNAPSHOT) but API contract changes are not automatically detected in the CI pipeline.
- **Gap**: No automated breaking change detection for API contracts in CI. Version support for the FHIR standard is excellent, but changes to the HAPI server API itself (custom operations, extensions) are not tested for backward compatibility.
- **Compensating Controls**:
  - Pin agent tool definitions to a specific HAPI FHIR version
  - Use the CapabilityStatement to validate API surface at agent startup
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenAPI spec comparison to the CI pipeline that detects breaking changes between PR branches and the baseline.
- **Evidence**: `hapi-fhir-structures-r4/`, `hapi-fhir-structures-r5/`, `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/provider/ServerCapabilityStatementProvider.java`

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: HAPI FHIR includes OpenTelemetry instrumentation annotations as a root dependency (`io.opentelemetry.instrumentation:opentelemetry-instrumentation-annotations`). The `BatchJobOpenTelemetryUtils` class provides tracing for batch operations. The `BaseInterceptorService` has OpenTelemetry integration. The `ValidationSupportChain` includes `@WithSpan` annotations. However, tracing is not enabled by default — it requires the OpenTelemetry Java agent or manual SDK configuration by the deployer. Logging uses SLF4J throughout, which supports structured JSON logging via Logback/Log4j2 configuration, but no default JSON log format is configured. No correlation ID / request ID propagation is built into the default configuration.
- **Gap**: OpenTelemetry annotations are present but tracing is not enabled by default. Structured JSON logging is not configured by default. Request correlation ID propagation requires deployer configuration.
- **Compensating Controls**:
  - Deploy the OpenTelemetry Java agent alongside HAPI FHIR to enable tracing automatically
  - Configure Logback with JSON encoder and MDC-based correlation IDs
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Document the recommended OpenTelemetry configuration for HAPI FHIR deployments. Add default structured logging configuration examples.
- **Evidence**: `pom.xml` (OpenTelemetry dependency), `hapi-fhir-storage-batch2/src/main/java/ca/uhn/fhir/batch2/util/BatchJobOpenTelemetryUtils.java`, `hapi-fhir-base/src/main/java/ca/uhn/fhir/interceptor/executor/BaseInterceptorService.java`

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No alerting configuration found in the repository. No CloudWatch alarms, no PagerDuty/OpsGenie integration, no SLO-based alerting, no anomaly detection configuration. This is expected for an open-source framework — alerting is a deployment-time concern. The `ResponseSizeCapturingInterceptor` captures response sizes but does not integrate with alerting systems.
- **Gap**: No alerting infrastructure for error rates or latency. Deployers must configure alerting at the infrastructure layer.
- **Compensating Controls**:
  - Configure CloudWatch or Prometheus alerting on the deployed HAPI FHIR server
  - Use the OpenTelemetry metrics exporter to publish error rate and latency metrics
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Deploy monitoring infrastructure with alerting on HTTP 5xx error rates, P95 latency, and agent-specific traffic anomalies.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/ResponseSizeCapturingInterceptor.java`. No alerting configuration found.

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: HAPI FHIR has a mature CI/CD pipeline: GitHub Actions (`pull-request.yml` → `parallel-pipeline-build.yml`) runs per-module tests in parallel with matrix strategy (up to 256 parallel jobs). Azure Pipelines handles releases (`release-pipeline.yml`, `snapshot-pipeline.yml`). CodeQL security scanning runs on push/PR/weekly schedule. Checkstyle validation runs in CI. The test suite is extensive (~1814 test files). However, there are no consumer-driven contract tests (no Pact), no OpenAPI spec validation in the build, and no explicit API breaking change detection.
- **Gap**: No API contract testing or breaking change detection in CI. Tests validate functionality but do not guard the agent-facing API surface against breaking changes.
- **Compensating Controls**:
  - Pin agent tool definitions to specific HAPI FHIR versions
  - Manual API review during pull request review process
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenAPI spec generation and comparison as a CI step. Consider adding Pact contract tests for the FHIR REST API surface.
- **Evidence**: `.github/workflows/pull-request.yml`, `.github/workflows/parallel-pipeline-build.yml`, `.github/workflows/codeql-analysis.yml`, `release-pipeline.yml`

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface
- **Severity**: INFO (met — no gap)
- **Finding**: HAPI FHIR exposes a fully documented FHIR REST API. The `RestfulServer` (2163 lines) implements the HL7 FHIR REST specification, exposing CRUD operations, search, transaction bundles, batch operations, and custom operations via resource providers. The API surface is defined by the FHIR standard itself, and the server auto-generates a FHIR CapabilityStatement describing all supported resources and operations. No direct database access, file-based exchange, or UI automation required.
- **Implication**: Agents can integrate via standard FHIR REST APIs. The FHIR standard provides a well-defined, interoperable interface surface. Tool definitions can be derived from the CapabilityStatement.
- **Recommendation**: No action required. The API surface is excellent for agent integration.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/RestfulServer.java`

### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: FHIR supports conditional create (`If-None-Exist` header), conditional update, and ETag-based optimistic locking (`If-Match` header). The `UpdateMethodBinding` and `PatchMethodBinding` classes support these idempotency mechanisms. The JPA layer uses version-based optimistic locking. For read-only agents, this is informational.
- **Implication**: If write scope is enabled in the future, idempotency mechanisms are available through FHIR standard headers.
- **Recommendation**: Document the idempotency patterns available for future write-enabled agents.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/method/UpdateMethodBinding.java`, `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/ETagSupportEnum.java`

### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: FHIR natively supports JSON and XML response formats. The `EncodingEnum` defines `JSON` and `XML` encodings. Response format is negotiated via the `_format` parameter or `Accept` header. JSON is the default and preferred format for agent consumption. All FHIR resources have well-defined JSON schemas.
- **Implication**: JSON responses are ideal for LLM-based agent consumption. No extra parsing required.
- **Recommendation**: Configure FHIR servers to default to JSON format for agent-facing endpoints.
- **Evidence**: `hapi-fhir-base/src/main/java/ca/uhn/fhir/rest/api/EncodingEnum.java`

### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit headers (`X-RateLimit-Remaining`, `Retry-After`) are emitted by the HAPI FHIR server framework. No rate limit documentation found in the codebase. Rate limiting is a deployer concern (see STATE-Q5).
- **Implication**: Agents cannot self-throttle based on rate limit headers from the FHIR server.
- **Recommendation**: If rate limiting is implemented at the gateway layer, ensure rate limit headers are passed through to clients.
- **Evidence**: No rate limit header references found in source code.

### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: The `RequestDetails` class carries user-level context through the request lifecycle. The `ServletRequestDetails` has access to HTTP headers including `Authorization`, and the interceptor framework can extract and propagate user identity. The `SearchNarrowingInterceptor` and `SearchNarrowingConsentService` use identity context to narrow search results by compartment. However, there is no built-in OAuth2 token exchange or on-behalf-of flow. Identity propagation for agent-as-self vs. agent-on-behalf-of-user is not distinguished at the framework level.
- **Implication**: Deployers must implement identity propagation patterns (JWT parsing, token exchange) via interceptors. The framework provides the hooks but not the implementation.
- **Recommendation**: Implement a JWT-parsing interceptor that distinguishes agent-as-self vs. agent-on-behalf-of-user and stores both identities in RequestDetails.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/api/server/RequestDetails.java`, `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/SearchNarrowingInterceptor.java`

### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: No hardcoded credentials found in the source code. No `.env` files committed. No `password=`, `secret=`, or `api_key=` patterns in application code. The framework delegates credential management to the deployer's environment configuration. Database connection credentials are expected to be provided via Spring configuration or environment variables at deployment time. The `.github/workflows/` files use GitHub Secrets for `CODECOV_TOKEN` and `GITHUB_TOKEN`.
- **Implication**: Credential management is clean at the framework level. Deployers must use secrets management (AWS Secrets Manager, Vault) for database and identity provider credentials.
- **Recommendation**: Document recommended secrets management patterns for HAPI FHIR deployments.
- **Evidence**: `.github/workflows/pull-request.yml` (uses secrets), `pom.xml` (no hardcoded credentials)

### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: HAPI FHIR supports optimistic locking via FHIR ETags and version IDs. The `ETagSupportEnum` class defines ETag behavior (ENABLED, DISABLED, REQUIRED_FOR_UPDATE). The `If-Match` header support in `UpdateMethodBinding` and `PatchMethodBinding` enforces optimistic locking on updates. The JPA layer uses Hibernate `@Version` annotations for database-level optimistic locking. DynamoDB conditional writes are not relevant (JPA-based). For read-only agents, concurrency controls for writes are informational.
- **Implication**: Strong concurrency controls exist for write operations. Read-only agents are not affected by write concurrency.
- **Recommendation**: No action for read-only scope. For future write scope, ensure agents use `If-Match` headers.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/ETagSupportEnum.java`, `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/method/UpdateMethodBinding.java`

### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable per-agent transaction limits found. The Batch2 framework supports job-level configuration (batch size, step limits), but these are not per-identity. Read-only agents cannot modify records, trigger spend, or delete data, so transaction limits are informational only.
- **Implication**: For future write-enabled scope, transaction limits should be implemented per agent identity.
- **Recommendation**: For future write scope, implement per-agent-identity limits on bulk operations.
- **Evidence**: `hapi-fhir-storage-batch2/` (batch configuration, no per-identity limits)

### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: FHIR resources support status fields (e.g., `MedicationRequest.status` = draft, active, completed). The FHIR Task resource supports workflow states. However, there is no framework-level "draft" state that applies universally to all resource creates. Draft/pending states are resource-type-specific per the FHIR specification.
- **Implication**: Read-only agents do not create resources. For future write scope, FHIR's resource-type-specific status fields can serve as draft states.
- **Recommendation**: No action for read-only scope.
- **Evidence**: FHIR standard resource status fields.

### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No built-in approval gate mechanism. The interceptor framework could support a custom approval interceptor that holds write operations pending human approval, but none is provided. The FHIR Task resource could model approval workflows.
- **Implication**: Read-only agents do not require approval gates. For future write scope, approval gates should be implemented at the orchestration layer or via a custom interceptor.
- **Recommendation**: No action for read-only scope.
- **Evidence**: No approval workflow found. `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/` (no approval interceptor)

### HITL-Q3: Sandbox/Staging Environment
- **Severity**: INFO
- **Finding**: HAPI FHIR provides extensive test infrastructure: `hapi-fhir-test-utilities` and `hapi-fhir-jpaserver-test-utilities` modules provide embedded server support for testing. The test modules use Testcontainers (`testcontainers_version=2.0.2`) for database instances, H2 in-memory database for unit tests, and a dedicated `hapi-fhir-jpaserver-uhnfhirtest` module for integration testing. No Docker Compose file for local staging, but the testing infrastructure provides production-equivalent data shape via embedded servers.
- **Implication**: The test infrastructure can be adapted for agent testing in sandbox environments.
- **Recommendation**: Create a Docker Compose file or Helm chart for deploying a sandbox HAPI FHIR server with seed data for agent testing.
- **Evidence**: `hapi-fhir-test-utilities/`, `hapi-fhir-jpaserver-test-utilities/`, `pom.xml` (testcontainers dependency)

### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: HAPI FHIR includes a comprehensive validation framework (`hapi-fhir-validation/`) supporting FHIR profile validation, StructureDefinition validation, and terminology validation. The `RequestValidatingInterceptor` and `ResponseValidatingInterceptor` can validate resources against FHIR profiles on request/response. No data quality score or completeness metrics are published, but the validation framework provides structural data quality assurance.
- **Implication**: FHIR profile validation provides structural data quality. No business-level data quality metrics are available for agent reasoning.
- **Recommendation**: Consider publishing data quality metrics (null rate, validation pass rate) via custom metrics.
- **Evidence**: `hapi-fhir-validation/`, `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/RequestValidatingInterceptor.java`

### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: FHIR resources use standard, semantically meaningful field names defined by the HL7 standard: `Patient.name`, `Patient.birthDate`, `Observation.value`, `MedicationRequest.dosageInstruction`, `DiagnosticReport.result`. No legacy codes or abbreviations. FHIR field names are designed for human readability and interoperability.
- **Implication**: Excellent for LLM-based agent reasoning. No data dictionary lookup required.
- **Recommendation**: No action required.
- **Evidence**: FHIR standard resource definitions via `hapi-fhir-structures-r4/`, `hapi-fhir-structures-r5/`

### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: The FHIR CapabilityStatement serves as a built-in data catalog describing all supported resources, search parameters, operations, and interactions. StructureDefinition resources describe data models. SearchParameter resources describe queryable fields. The server auto-generates and serves these metadata resources at runtime.
- **Implication**: The FHIR metadata layer (CapabilityStatement, StructureDefinition, SearchParameter) provides a rich data catalog for agent tool discovery.
- **Recommendation**: Expose CapabilityStatement to agent tooling for automatic tool definition generation.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/provider/ServerCapabilityStatementProvider.java`

### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business outcome metrics found. The framework provides infrastructure metrics via OpenTelemetry annotations and the `ResponseSizeCapturingInterceptor`, but no business-level metrics (e.g., records retrieved per query, search result relevance, validation pass rates).
- **Implication**: Business outcome metrics must be implemented by deployers to evaluate agent interaction quality.
- **Recommendation**: Implement custom metrics interceptors that publish agent-relevant business metrics (query result counts, resource access patterns).
- **Evidence**: No custom business metrics found. `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/ResponseSizeCapturingInterceptor.java`

### ENG-Q1: Infrastructure Governance
- **Severity**: INFO
- **Finding**: No IaC files found in the repository (no Terraform, CloudFormation, CDK, Helm charts, or Kubernetes manifests). This is expected for an open-source framework — infrastructure governance is a deployer concern. The framework provides configuration options but no deployment infrastructure definitions.
- **Implication**: Deployers must define their own IaC for API gateways, IAM roles, secrets, and networking.
- **Recommendation**: Provide reference IaC templates for common deployment patterns (AWS ECS/Fargate, Kubernetes).
- **Evidence**: No IaC files found in repository root or subdirectories.

### ENG-Q3: Rollback Capability
- **Severity**: INFO
- **Finding**: The release pipeline uses Azure Pipelines with Maven versioning. Releases are tagged in git (`v${NEW_RELEASE_VERSION}`). The `release-pipeline.yml` includes version verification. However, there is no blue/green deployment, canary deployment, or feature flag infrastructure in the repository. Rollback for a deployed HAPI FHIR server depends on the deployer's deployment strategy. The `hapi-fhir-sql-migrate` module provides database migration support via Flyway, which supports rollback for schema changes.
- **Implication**: Deployers must implement deployment rollback at their infrastructure layer. Database schema rollback is supported via Flyway.
- **Recommendation**: Implement blue/green or canary deployment in the deployer's infrastructure and test rollback procedures.
- **Evidence**: `release-pipeline.yml`, `hapi-fhir-sql-migrate/` (Flyway migrations)

### ENG-Q4: API Test Coverage
- **Severity**: INFO
- **Finding**: HAPI FHIR has extensive test coverage: ~1814 test files across dedicated test modules (`hapi-fhir-jpaserver-test-dstu2`, `-test-dstu3`, `-test-r4`, `-test-r4b`, `-test-r5`). The CI pipeline runs all tests in parallel via GitHub Actions. JaCoCo code coverage is configured. Architecture tests use ArchUnit. The test infrastructure includes `hapi-fhir-test-utilities` and `hapi-fhir-jpaserver-test-utilities` with embedded servers for integration testing. Tests cover FHIR resource CRUD, search, transactions, batch operations, and interceptor behavior.
- **Implication**: Strong test coverage provides confidence in API behavior stability. However, tests are not specifically structured as agent-facing API contract tests.
- **Recommendation**: Consider adding agent-specific API test scenarios that validate the exact operations agents will use.
- **Evidence**: `hapi-fhir-jpaserver-test-r4/`, `hapi-fhir-jpaserver-test-r5/`, `hapi-fhir-test-utilities/`, `.github/workflows/parallel-pipeline-build.yml` (JaCoCo profile)

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO (met — no gap)
- **Finding**: HAPI FHIR exposes a fully documented FHIR REST API via `RestfulServer` (2163 lines). The HL7 FHIR standard defines the interface. CapabilityStatement auto-generated at runtime describes all resources, operations, and interactions.
- **Gap**: None. The API surface is well-documented via the FHIR standard and CapabilityStatement.
- **Recommendation**: No action required.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/RestfulServer.java`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: `OpenApiInterceptor.java` dynamically generates OpenAPI specs from CapabilityStatement at runtime. No static OpenAPI file ships with the repository.
- **Gap**: No static machine-readable API spec file. Requires running server to generate.
- **Recommendation**: Add CI step to export generated OpenAPI spec as a static artifact.
- **Evidence**: `hapi-fhir-server-openapi/src/main/java/ca/uhn/fhir/rest/openapi/OpenApiInterceptor.java`

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: Uses FHIR OperationOutcome as structured error responses via `ExceptionHandlingInterceptor`. `BaseServerResponseException` carries HTTP status codes and OperationOutcome. No explicit retryable flag.
- **Gap**: No machine-readable retryable/non-retryable indicator.
- **Recommendation**: Add `Retry-After` headers for 429/503 responses.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/ExceptionHandlingInterceptor.java`, `hapi-fhir-base/src/main/java/ca/uhn/fhir/rest/server/exceptions/BaseServerResponseException.java`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: FHIR supports conditional create/update, ETag-based optimistic locking. Informational for read-only scope.
- **Gap**: N/A for read-only scope.
- **Recommendation**: Document idempotency patterns for future write-enabled agents.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/method/UpdateMethodBinding.java`, `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/ETagSupportEnum.java`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: FHIR natively supports JSON and XML. `EncodingEnum` defines both. JSON is default and preferred for agents.
- **Gap**: None.
- **Recommendation**: Default to JSON for agent endpoints.
- **Evidence**: `hapi-fhir-base/src/main/java/ca/uhn/fhir/rest/api/EncodingEnum.java`

#### API-Q6: Asynchronous Operation Support
- **Severity**: INFO
- **Finding**: HAPI FHIR has the Batch2 framework (`hapi-fhir-storage-batch2/`) that implements a job-based asynchronous processing system for long-running operations such as bulk export, bulk import, reindexing, and terminology operations. The `JobCoordinator` manages job lifecycle with states (QUEUED, IN_PROGRESS, COMPLETED, ERRORED, CANCELLED). Job status can be polled via the `$export-poll-status` operation. The FHIR Bulk Data Access specification is supported. However, there is no generic async job submission endpoint or webhook callback for arbitrary operations.
- **Gap**: Async patterns exist for built-in bulk operations but are not generalized for arbitrary custom operations. No webhook callback mechanism.
- **Recommendation**: Document the Batch2 framework's async capabilities for agent consumption. Consider exposing job status via a generic polling API.
- **Evidence**: `hapi-fhir-storage-batch2/src/main/java/ca/uhn/fhir/batch2/coordinator/JobCoordinator.java`, `hapi-fhir-storage-batch2/`

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: HAPI FHIR has a comprehensive subscription and event notification system. The `IResourceChangeListenerRegistry` provides an in-memory resource change notification framework. The Subscription module (`hapi-fhir-jpaserver-subscription/`) supports FHIR Subscriptions (REST-hook, WebSocket, and email channels) that fire on resource state changes. The `SubscriptionTriggeringSvc` allows programmatic subscription triggering. FHIR R5 SubscriptionTopic support is implemented via `BaseSubscriptionTopicLoader`. However, these are FHIR-standard subscription mechanisms, not general-purpose event emission (no SNS/EventBridge/Kafka integration out of the box).
- **Gap**: Event emission is tied to FHIR Subscription model. No general-purpose event bus or webhook integration for arbitrary agent consumption.
- **Recommendation**: Leverage FHIR Subscriptions for agent event consumption. For broader event patterns, implement an interceptor that publishes to external event buses.
- **Evidence**: `hapi-fhir-jpaserver-subscription/`, `hapi-fhir-jpaserver-base/src/main/java/ca/uhn/fhir/jpa/cache/IResourceChangeListenerRegistry.java`, `hapi-fhir-jpaserver-base/src/main/java/ca/uhn/fhir/jpa/subscription/triggering/SubscriptionTriggeringSvcImpl.java`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit headers or documentation found in the framework.
- **Gap**: No rate limit headers emitted.
- **Recommendation**: Implement rate limit headers at the gateway layer.
- **Evidence**: No rate limit header references found in source code.

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: Framework provides interceptor hooks for authentication but ships no built-in machine identity authentication (no OAuth2 client credentials, no API key validation, no mTLS). Authentication is entirely delegated to deployer interceptors.
- **Gap**: No built-in machine identity authentication mechanism.
- **Recommendation**: Implement OAuth2 bearer token validation interceptor integrated with an identity provider.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/AuthorizationInterceptor.java`, `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/RestfulServer.java`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: `RuleBuilder` provides fine-grained rule definition per resource type, operation type, and compartment. Not configured by default.
- **Gap**: Authorization rules not configured by default — unrestricted access without explicit configuration.
- **Recommendation**: Configure `AuthorizationInterceptor` with read-only rules scoped to specific resource types for agent identities.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/RuleBuilder.java`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: `RuleBuilder` supports action-level authorization (read, write, delete, patch, search, operation, etc.). Not configured by default.
- **Gap**: Capability exists but unconfigured. Same practical gap as AUTH-Q2.
- **Recommendation**: Configure action-level rules limiting agents to read operations.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/RuleImplOp.java`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: `RequestDetails` carries user context. `SearchNarrowingInterceptor` uses identity for compartment narrowing. No built-in token exchange or on-behalf-of flows.
- **Gap**: No framework-level distinction between agent-as-self and agent-on-behalf-of-user.
- **Recommendation**: Implement JWT-parsing interceptor distinguishing both modes.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/api/server/RequestDetails.java`

#### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: No hardcoded credentials found. Framework delegates credential management to deployer. CI uses GitHub Secrets.
- **Gap**: No framework-level secrets management integration. Deployer responsibility.
- **Recommendation**: Document secrets management best practices for HAPI FHIR deployments.
- **Evidence**: `.github/workflows/pull-request.yml`, `pom.xml`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: `LoggingInterceptor` logs to SLF4J with no immutability guarantees. No automatic AuditEvent generation. No CloudTrail integration.
- **Gap**: No immutable, tamper-evident audit logging by default.
- **Recommendation**: Implement AuditEvent-generating interceptor and configure immutable log storage.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/LoggingInterceptor.java`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: No built-in identity suspension mechanism. Identity lifecycle is an external concern.
- **Gap**: Cannot revoke agent identity within HAPI FHIR itself.
- **Recommendation**: Implement suspension at the identity provider layer.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/AuthorizationInterceptor.java`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Spring `@Transactional` provides database-level rollback. FHIR transaction bundles are atomic. No saga pattern for cross-service operations. Batch2 framework has error handling but no compensating transactions.
- **Gap**: No application-level compensation for multi-step workflows.
- **Recommendation**: For read-only scope, existing rollback is sufficient. Implement sagas before enabling write scope.
- **Evidence**: `hapi-fhir-jpaserver-base/`, `hapi-fhir-storage-batch2/`

#### STATE-Q2: Queryable Current State
- **Severity**: INFO
- **Finding**: HAPI FHIR exposes current state of all FHIR resources via standard REST read and search operations. Every resource type has GET endpoints for individual read (`GET /Patient/123`) and search (`GET /Patient?name=Smith`). The `_history` operation provides version history. The `_summary` and `_elements` parameters allow partial resource retrieval. The `PersistedJpaBundleProvider` implements paginated search results. Resources can be queried by any indexed search parameter. The current state is always queryable — this is a core FHIR feature.
- **Gap**: None. Current state is fully queryable via standard FHIR REST operations.
- **Recommendation**: No action required. The FHIR REST API provides comprehensive state queryability for agent consumption.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/RestfulServer.java`, `hapi-fhir-jpaserver-base/src/main/java/ca/uhn/fhir/jpa/search/PersistedJpaBundleProvider.java`

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: ETag support, If-Match headers, Hibernate `@Version` optimistic locking. Strong concurrency controls for writes.
- **Gap**: None for read-only scope.
- **Recommendation**: Ensure agents use If-Match headers if write scope is enabled.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/ETagSupportEnum.java`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has external dependencies (calls other services or external APIs)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No built-in rate limiting middleware or interceptors. No X-RateLimit-Remaining or Retry-After headers.
- **Gap**: No API-layer rate limiting to prevent runaway agent loops.
- **Recommendation**: Implement rate limiting at the API gateway or via custom interceptor.
- **Evidence**: No rate limiting interceptor found.

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No per-agent transaction limits. Read-only agents cannot cause blast-radius damage.
- **Gap**: None for read-only scope.
- **Recommendation**: Implement per-agent limits before enabling write scope.
- **Evidence**: `hapi-fhir-storage-batch2/`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: FHIR resources have resource-type-specific status fields (draft, active, completed). No universal draft mechanism.
- **Gap**: None for read-only scope.
- **Recommendation**: No action for read-only scope.
- **Evidence**: FHIR standard resource status fields.

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No built-in approval gate mechanism. FHIR Task resource could model workflows.
- **Gap**: None for read-only scope.
- **Recommendation**: No action for read-only scope.
- **Evidence**: No approval interceptor found.

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: INFO
- **Finding**: Extensive test infrastructure with embedded servers, Testcontainers, H2 in-memory database. No Docker Compose for local staging.
- **Gap**: No turnkey sandbox deployment, but building blocks exist.
- **Recommendation**: Create Docker Compose or Helm chart for sandbox deployment with seed data.
- **Evidence**: `hapi-fhir-test-utilities/`, `hapi-fhir-jpaserver-test-utilities/`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification ⚡ (Tiered)
- **Severity**: RISK-SAFETY
- **Stage A**: Yes — healthcare data (PHI/PII) by definition across all FHIR resource types.
- **B1 — API response scoping**: CLEAR at framework level. HAPI FHIR provides robust hooks: `SearchNarrowingInterceptor` (compartment-based narrowing via `buildAuthorizedList()`), `AuthorizationInterceptor` with multi-pointcut hooks (`SERVER_INCOMING_REQUEST_PRE_HANDLED`, `STORAGE_PRESHOW_RESOURCES`, `SERVER_OUTGOING_RESPONSE`), and FHIR-native `_summary` / `_elements` parameters.
- **B2 — Access control differentiation**: CLEAR at framework level. `RuleBuilder` supports fluent allow/deny rules scoped by resource type, operation, compartment, and tenant; default policy is `PolicyEnum.DENY` when the interceptor is registered.
- **B3 — Formal classification metadata**: CLEAR. FHIR's native `Meta.security` is a formal, machine-readable classification primitive (HL7 security-label CodeSystem with `ANONYMIZE`/`ENCRYPT`/`REDACT`/etc.).
- **Framework default behavior**: If a deployer registers no `AuthorizationInterceptor`, the server returns all PHI fields unfiltered. This is the framework pattern (consumers configure security); for any PHI deployment, configuring `AuthorizationInterceptor` is mandatory.
- **Overall**: RISK-SAFETY at the framework level — hooks exist and work; the severity reflects the "unconfigured default returns all PHI" risk. A correctly configured deployment moves this to CLEAR.
- **Recommendation**: Deployers must register `AuthorizationInterceptor` with explicit allow rules, register `SearchNarrowingInterceptor` for compartment narrowing, set default policy to `PolicyEnum.DENY`, and apply `Meta.security` labels per the HL7 confidentiality taxonomy.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/SearchNarrowingInterceptor.java:93-250`, `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/AuthorizationInterceptor.java:77-150`, `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/RuleBuilder.java:49-1088`, `hapi-fhir-docs/src/main/java/ca/uhn/hapi/fhir/docs/AuthorizationInterceptors.java` (example compartment rules).

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Healthcare data has residency requirements (HIPAA, GDPR). The framework does not enforce data residency — database region, replication, and data sovereignty are deployer infrastructure decisions. No region configuration or cross-region data transfer controls found in the codebase.
- **Gap**: No framework-level data residency enforcement. Entirely deployer responsibility.
- **Recommendation**: Configure database and server deployment in compliant regions. Document residency requirements in deployment guide.
- **Evidence**: No region or residency configuration found.

#### DATA-Q3: Selective Query Support
- **Severity**: RISK-QUALITY
- **Finding**: HAPI FHIR provides comprehensive selective query support. The FHIR search specification supports `_count` (pagination size), `_offset` (paging offset), `_sort` (sorting), `_include`/`_revinclude` (referenced resources), `_summary` (summary mode), and `_elements` (field selection). The `PersistedJpaBundleProvider` implements paginated result delivery. Search parameters support filtering by resource fields. The `SearchParameterMap` class provides a rich API for constructing queries. Default page sizes are configurable via `JpaStorageSettings`. However, unbounded search queries are possible if no `_count` parameter is provided — the server returns results in pages but the total result set can be very large.
- **Gap**: Pagination and filtering are fully supported, but agents can still issue unbounded search queries. No default maximum result set size is enforced unless configured by the deployer.
- **Recommendation**: Configure default `_count` limits and maximum result set sizes in `JpaStorageSettings` for agent-facing endpoints.
- **Evidence**: `hapi-fhir-jpaserver-base/src/main/java/ca/uhn/fhir/jpa/search/PersistedJpaBundleProvider.java`, `hapi-fhir-jpaserver-base/src/main/java/ca/uhn/fhir/jpa/search/builder/SearchBuilder.java`

#### DATA-Q4: System of Record Designations
- **Severity**: RISK-QUALITY
- **Finding**: HAPI FHIR is designed as the system of record for FHIR resources it stores. The JPA storage layer provides authoritative storage for all FHIR resource types. Resource versioning (`meta.versionId`) provides version history. The `_history` operation exposes the full change history. However, the framework does not include master data management, conflict resolution for cross-system data, or golden record patterns. When HAPI FHIR is deployed alongside other clinical systems, there is no built-in mechanism to designate which system is authoritative for each resource type.
- **Gap**: No cross-system master data management or system-of-record designations. HAPI FHIR is authoritative for what it stores, but conflict resolution with external systems is not addressed.
- **Recommendation**: Document system-of-record designations in deployment architecture. Implement FHIR Provenance resources to track data source for agent reasoning.
- **Evidence**: `hapi-fhir-jpaserver-base/` (JPA storage as authoritative store)

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK-QUALITY
- **Finding**: HAPI FHIR provides strong temporal metadata support. Every resource has `meta.lastUpdated` (automatically populated by the JPA layer), `meta.versionId` (incremented on each update), and the `_history` operation provides full version history with timestamps. The `ResourceMetadataKeyEnum.UPDATED` and `ResourceMetadataKeyEnum.PUBLISHED` keys track update and creation times. All timestamps are stored in UTC. The `ETag` and `Last-Modified` HTTP headers are supported. However, there is no `X-Data-Age` or `consistency_level` header — the server always returns the current committed state (strong consistency via JPA transactions), but this is not signaled explicitly.
- **Gap**: Temporal metadata (lastUpdated, versionId) is comprehensive. No explicit freshness signaling (Cache-Control, X-Data-Age, consistency_level headers) — though the system provides strong consistency by default via JPA transactions.
- **Recommendation**: Document the strong consistency model for agent consumers. Consider adding Cache-Control headers to indicate data freshness.
- **Evidence**: `hapi-fhir-base/src/main/java/ca/uhn/fhir/model/api/ResourceMetadataKeyEnum.java` (UPDATED, PUBLISHED), `hapi-fhir-jpaserver-base/`

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: `LoggingInterceptor` can log request/response bodies containing PHI. No built-in PII/PHI masking or redaction.
- **Gap**: No PII redaction in logs. PHI may appear in log output.
- **Recommendation**: Configure logging to exclude PHI-containing fields. Implement log scrubbing.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/LoggingInterceptor.java`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: Comprehensive FHIR profile validation framework. No data quality score or completeness metrics.
- **Gap**: No business-level data quality metrics.
- **Recommendation**: Consider publishing data quality metrics.
- **Evidence**: `hapi-fhir-validation/`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: Excellent FHIR version support (DSTU2–R5). CapabilityStatement as API contract. Maven versioning. No breaking change detection in CI.
- **Gap**: No automated breaking change detection in CI.
- **Recommendation**: Add OpenAPI spec comparison to CI pipeline.
- **Evidence**: `hapi-fhir-structures-r4/`, `hapi-fhir-structures-r5/`, `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/provider/ServerCapabilityStatementProvider.java`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: FHIR resources use standard, semantically meaningful field names. No legacy codes.
- **Gap**: None.
- **Recommendation**: No action required.
- **Evidence**: FHIR standard resource definitions.

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: CapabilityStatement, StructureDefinition, SearchParameter provide a rich metadata layer.
- **Gap**: None.
- **Recommendation**: Expose CapabilityStatement to agent tooling.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/provider/ServerCapabilityStatementProvider.java`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: OpenTelemetry annotations present as root dependency. `BatchJobOpenTelemetryUtils` provides batch tracing. Not enabled by default. SLF4J logging without default JSON format.
- **Gap**: Tracing not enabled by default. No default structured logging or correlation IDs.
- **Recommendation**: Deploy OpenTelemetry Java agent. Configure JSON logging with correlation IDs.
- **Evidence**: `pom.xml`, `hapi-fhir-storage-batch2/src/main/java/ca/uhn/fhir/batch2/util/BatchJobOpenTelemetryUtils.java`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: No alerting configuration found. Expected for open-source framework.
- **Gap**: No alerting infrastructure.
- **Recommendation**: Deploy alerting at infrastructure layer.
- **Evidence**: No alerting configuration found.

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business outcome metrics. Infrastructure metrics via OpenTelemetry annotations.
- **Gap**: No business-level metrics for agent interaction quality.
- **Recommendation**: Implement custom metrics interceptors.
- **Evidence**: No custom business metrics found.

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: INFO
- **Finding**: No IaC files found. Expected for open-source framework — deployer concern.
- **Gap**: No IaC in repository. Deployer must provide.
- **Recommendation**: Provide reference IaC templates.
- **Evidence**: No IaC files found.

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: Mature CI/CD (GitHub Actions parallel builds, Azure Pipelines releases, CodeQL, Checkstyle). ~1814 test files. No contract testing or breaking change detection.
- **Gap**: No API contract testing in CI.
- **Recommendation**: Add OpenAPI spec comparison and consider Pact contract tests.
- **Evidence**: `.github/workflows/pull-request.yml`, `.github/workflows/parallel-pipeline-build.yml`

#### ENG-Q3: Rollback Capability
- **Severity**: INFO
- **Finding**: Git-tagged releases, Flyway database migrations. No blue/green or canary deployment in repository.
- **Gap**: Deployment rollback is deployer's responsibility.
- **Recommendation**: Implement rollback strategy at infrastructure layer.
- **Evidence**: `release-pipeline.yml`, `hapi-fhir-sql-migrate/`

#### ENG-Q4: API Test Coverage
- **Severity**: INFO
- **Finding**: ~1814 test files, dedicated test modules per FHIR version, JaCoCo coverage, ArchUnit architecture tests, Testcontainers for integration testing.
- **Gap**: Tests are functional, not specifically agent-facing contract tests.
- **Recommendation**: Add agent-specific API test scenarios.
- **Evidence**: `hapi-fhir-jpaserver-test-r4/`, `hapi-fhir-jpaserver-test-r5/`, `hapi-fhir-test-utilities/`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: INFO
- **Finding**: No encryption-at-rest configuration found in the repository. This is expected for an open-source framework — HAPI FHIR delegates database encryption to the deployer's infrastructure. The framework uses JPA/Hibernate for data access, which is agnostic to the underlying storage encryption. Encryption at rest is typically configured at the database level (e.g., AWS RDS encryption, Azure SQL TDE) or disk level (EBS encryption), not at the application layer. No `kms_key_id`, KMS configuration, or application-level encryption utilities found.
- **Gap**: No encryption-at-rest configuration in the framework. Entirely a deployer infrastructure concern.
- **Recommendation**: Ensure the database backing HAPI FHIR uses encryption at rest (RDS encryption, KMS). Document encryption requirements in the deployment guide.
- **Evidence**: No encryption configuration found. `hapi-fhir-jpaserver-base/` (JPA storage layer — no encryption utilities)

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/RestfulServer.java` | API-Q1, AUTH-Q1 |
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/AuthorizationInterceptor.java` | AUTH-Q1, AUTH-Q2, AUTH-Q7 |
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/RuleBuilder.java` | AUTH-Q2, AUTH-Q3 |
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/IAuthRuleBuilder.java` | AUTH-Q2 |
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/RuleImplOp.java` | AUTH-Q3 |
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/SearchNarrowingInterceptor.java` | AUTH-Q4 |
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/ExceptionHandlingInterceptor.java` | API-Q3 |
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/LoggingInterceptor.java` | AUTH-Q6, DATA-Q6 |
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/ResponseSizeCapturingInterceptor.java` | OBS-Q2, OBS-Q3 |
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/consent/ConsentInterceptor.java` | DATA-Q1 |
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/consent/IConsentService.java` | DATA-Q1 |
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/RequestValidatingInterceptor.java` | DATA-Q7 |
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/ETagSupportEnum.java` | API-Q4, STATE-Q3 |
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/method/UpdateMethodBinding.java` | API-Q4, STATE-Q3 |
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/provider/ServerCapabilityStatementProvider.java` | DISC-Q1, DISC-Q3 |
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/api/server/RequestDetails.java` | AUTH-Q4 |
| `hapi-fhir-server-openapi/src/main/java/ca/uhn/fhir/rest/openapi/OpenApiInterceptor.java` | API-Q2 |
| `hapi-fhir-base/src/main/java/ca/uhn/fhir/rest/server/exceptions/BaseServerResponseException.java` | API-Q3 |
| `hapi-fhir-base/src/main/java/ca/uhn/fhir/rest/api/EncodingEnum.java` | API-Q5 |
| `hapi-fhir-base/src/main/java/ca/uhn/fhir/interceptor/executor/BaseInterceptorService.java` | OBS-Q1 |
| `hapi-fhir-storage-batch2/src/main/java/ca/uhn/fhir/batch2/util/BatchJobOpenTelemetryUtils.java` | OBS-Q1 |
| `hapi-fhir-storage-batch2/src/main/java/ca/uhn/fhir/batch2/coordinator/JobStepExecutor.java` | STATE-Q1 |
| `hapi-fhir-jpaserver-base/src/main/java/ca/uhn/fhir/jpa/search/PersistedJpaBundleProvider.java` | STATE-Q5 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `hapi-fhir-server-openapi/src/main/java/ca/uhn/fhir/rest/openapi/OpenApiInterceptor.java` | API-Q2 (dynamically generates OpenAPI) |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/pull-request.yml` | ENG-Q2, AUTH-Q5 |
| `.github/workflows/parallel-pipeline-build.yml` | ENG-Q2, ENG-Q4 |
| `.github/workflows/codeql-analysis.yml` | ENG-Q2 |
| `release-pipeline.yml` | ENG-Q2, ENG-Q3 |
| `snapshot-pipeline.yml` | ENG-Q2 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `.github/docker/Dockerfile` | (Build infrastructure only — not a deployment Dockerfile) |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `pom.xml` (root) | OBS-Q1 (OpenTelemetry dependency), AUTH-Q5 (no hardcoded credentials), ENG-Q4 (test dependencies) |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `.github/dependabot.yml` | (Dependency update automation) |
| `.editorconfig` | (Code formatting standards) |
| `.pre-commit-config.yaml` | (Pre-commit hooks) |

### Module Directories (Referenced as Evidence)
| Directory | Questions Referenced |
|-----------|---------------------|
| `hapi-fhir-jpaserver-base/` | AUTH-Q1, DATA-Q1, STATE-Q1 |
| `hapi-fhir-storage/` | STATE-Q1 |
| `hapi-fhir-storage-batch2/` | STATE-Q1, STATE-Q6 |
| `hapi-fhir-validation/` | DATA-Q7 |
| `hapi-fhir-test-utilities/` | HITL-Q3 |
| `hapi-fhir-jpaserver-test-utilities/` | HITL-Q3 |
| `hapi-fhir-jpaserver-test-r4/` | ENG-Q4 |
| `hapi-fhir-jpaserver-test-r5/` | ENG-Q4 |
| `hapi-fhir-structures-r4/` | DISC-Q1 |
| `hapi-fhir-structures-r5/` | DISC-Q1 |
| `hapi-fhir-sql-migrate/` | ENG-Q3 |
