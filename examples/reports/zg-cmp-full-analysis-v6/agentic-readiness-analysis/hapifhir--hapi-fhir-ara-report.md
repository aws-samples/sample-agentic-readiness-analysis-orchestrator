# Agentic Readiness Analysis Report

**Target**: /Users/lucasdu/Documents/AWS-MAC/2026-projects/sample-agentic-readiness-analysis/services/hapifhir--hapi-fhir
**Date**: 2026-05-08
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**Repository Type**: application
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: java, healthcare, rest-api
**Context**: Open-source Java implementation of the HL7 FHIR healthcare standard.

**Archetype Justification**: HAPI FHIR provides a full JPA/Hibernate persistence layer with CRUD operations on FHIR resources (Patient, Observation, etc.), database migrations, and entity lifecycle management. Although consumed as a library, when deployed it operates as a stateful CRUD service owning persistent healthcare data.

**Surface flags**:
- has_persistent_data_store: true
- has_http_rpc_surface: true
- has_auth_surface: true
- has_write_operations: true
- has_logging_of_user_data: true

---

## Readiness Profile: Pilot-Ready (Safety Concerns)

**BLOCKERs**: 0 | **RISK-SAFETY**: 7 | **RISK-QUALITY**: 12 | **INFOs**: 10

Supervised pilot with elevated safety oversight: (1) all Pilot-Ready controls apply, (2) prioritize RISK-SAFETY remediation before expanding agent scope, (3) dedicated safety review cadence, (4) agent restricted to lowest-blast-radius operations until RISK-SAFETY count drops below 3.

**Classification Rationale**: This repo has 0 BLOCKER findings and 7 RISK-SAFETY findings. Per the readiness profile rules, 0 BLOCKERs with 3+ RISK-SAFETY findings yields "Pilot-Ready (Safety Concerns)." The V6 unified classification maps to 0 High findings, 19 Medium findings (7 safety-impact), matching the rule "0 High, ≥2 Medium, ≥3 safety-impact Medium → Pilot-Ready (Safety Concerns)."

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 0 |
| RISK-SAFETY | 7 |
| RISK-QUALITY | 12 |
| INFO | 10 |
| N/A | 0 |
| Not Evaluated (extended) | 4 |
| PASS (no finding) | 10 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 15
**Extended Questions Not Triggered**: 4
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: stateful-crud (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

No BLOCKERs identified.

---

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: HAPI FHIR provides a comprehensive `AuthorizationInterceptor` with `RuleBuilder` supporting fine-grained rules (allow read on Patient, deny write on Observation, etc.). However, no IAM policies, API Gateway resource policies, or platform-level least-privilege enforcement are defined in this repository — no IaC exists.
- **Gap**: No infrastructure-as-code defining IAM roles, API Gateway policies, or platform-level permission scoping for agent identities. The authorization framework exists but requires deployment-time configuration.
- **Compensating Controls**:
  - Deploy with API Gateway authorizers that enforce agent-specific IAM roles with read-only resource policies
  - Configure `AuthorizationInterceptor` rules at deployment time to limit agent identities to specific FHIR resource types and operations
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create deployment templates (IaC) defining agent-specific IAM roles with explicit action-level permissions integrated with the existing `AuthorizationInterceptor`.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/AuthorizationInterceptor.java`, `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/RuleBuilder.java`

#### AUTH-Q6: Immutable Audit Logging — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: HAPI FHIR provides a BALP (IHE Basic Audit Logging Pattern) interceptor generating FHIR AuditEvent resources and Hibernate Envers for entity-level audit trails. However, audit events are stored in the same mutable database. No immutable log storage (CloudTrail, S3 Object Lock) is configured.
- **Gap**: Audit events generated but stored in mutable datastore. No immutable, tamper-evident audit log storage defined.
- **Compensating Controls**:
  - Forward AuditEvent resources to an external immutable log sink (CloudWatch Logs with retention lock, S3 with Object Lock)
  - Deploy with AWS CloudTrail enabled for API-level audit trail
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement an `IAuditDataStore` that writes to an immutable external store (S3 with Object Lock or CloudWatch Logs with retention policy).
- **Evidence**: `hapi-fhir-storage/src/main/java/ca/uhn/fhir/jpa/interceptor/BalpAuditCaptureInterceptor.java`, `hapi-fhir-jpaserver-base/src/main/java/ca/uhn/fhir/jpa/config/EnversAuditConfig.java`

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: HAPI FHIR does not include built-in mechanisms for suspending or revoking individual agent identities. The `BearerTokenAuthInterceptor` validates tokens but provides no revocation interface.
- **Gap**: No mechanism to immediately suspend or revoke a specific agent identity without impacting other consumers.
- **Compensating Controls**:
  - Use an external identity provider (Cognito, Okta) with per-client disable capability
  - Deploy behind API Gateway with per-API-key revocation
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Integrate with an external identity provider supporting immediate per-client credential revocation.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/BearerTokenAuthInterceptor.java`

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: HAPI FHIR includes Spring Retry (`Retrier` class) with exponential backoff (500ms to 60s, 2x multiplier) and `RetryingMessageHandlerWrapper` for subscription messages. However, no formal circuit breaker pattern (Resilience4j, Hystrix) exists. When the server calls external terminology services or subscription endpoints, cascading failures are not prevented.
- **Gap**: No circuit breaker implementation. External dependency calls (terminology servers, subscription endpoints) can cascade failures back to agent-initiated requests.
- **Compensating Controls**:
  - Add Resilience4j circuit breaker at deployment for external service calls
  - Configure timeout limits on HTTP client connections to external services
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add Resilience4j circuit breaker annotations on methods that call external terminology servers and subscription endpoints.
- **Evidence**: `hapi-fhir-storage/src/main/java/ca/uhn/fhir/jpa/util/Retrier.java`

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No production rate limiting middleware exists. The `TransactionConcurrencySemaphoreInterceptor` limits concurrent transaction bundle processing but does not provide per-client rate limiting.
- **Gap**: No per-client or per-endpoint rate limiting to prevent runaway agent loops from overwhelming the FHIR server.
- **Compensating Controls**:
  - Deploy behind AWS API Gateway with usage plans and throttle settings
  - Add WAF rate-based rules at the infrastructure layer
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Deploy with API Gateway usage plans defining per-agent throttle limits.
- **Evidence**: `hapi-fhir-jpaserver-base/src/main/java/ca/uhn/fhir/jpa/interceptor/TransactionConcurrencySemaphoreInterceptor.java`

#### DATA-Q2: Data Residency and Sovereignty — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: HAPI FHIR stores healthcare data (PHI) subject to HIPAA, GDPR, and jurisdiction-specific health data regulations. Multi-tenancy and partitioning are supported but no data residency enforcement exists. No region-locking controls are implemented.
- **Gap**: No data residency enforcement. Healthcare PHI subject to HIPAA/GDPR with no controls preventing agent transmission to LLM endpoints in other jurisdictions.
- **Compensating Controls**:
  - Deploy with region-locked infrastructure (single-region database, VPC endpoints to Bedrock in same region)
  - Implement VPC endpoints ensuring LLM calls stay within the same jurisdiction
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Deploy with region-locked infrastructure ensuring LLM endpoints are co-located with data. Implement data classification identifying fields requiring residency controls.
- **Evidence**: `hapi-fhir-jpaserver-base/src/main/java/ca/uhn/fhir/jpa/partition/` (partitioning framework, no residency enforcement)

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: HAPI FHIR logs request details via `LoggingInterceptor` with configurable templates that can include request headers, parameters, and response bodies. No built-in PII/PHI scrubbing or log redaction middleware exists.
- **Gap**: Healthcare data (patient names, identifiers, clinical data) in request/response bodies can leak into application logs when verbose logging is configured.
- **Compensating Controls**:
  - Configure `LoggingInterceptor` to log only request metadata (method, path, status) without body content
  - Deploy with CloudWatch log filters that mask PHI patterns
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement a custom logging interceptor that scrubs PHI from log entries. Integrate with Amazon Macie for log-level PII detection.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/LoggingInterceptor.java`

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: `OpenApiInterceptor` auto-generates OpenAPI 3.x specifications at runtime from CapabilityStatement. No static OpenAPI spec file committed to the repository.
- **Gap**: No static, version-controlled OpenAPI specification for offline agent tool generation or CI contract testing.
- **Compensating Controls**:
  - Export generated OpenAPI spec as a build artifact and version-control it
  - Use the FHIR CapabilityStatement (machine-readable) as the canonical interface contract
- **Remediation Timeline**: 30 days
- **Recommendation**: Add a build step that exports the generated OpenAPI spec as a static artifact.
- **Evidence**: `hapi-fhir-server-openapi/src/main/java/ca/uhn/fhir/rest/openapi/OpenApiInterceptor.java`

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: All errors converted to FHIR OperationOutcome with severity, code, and diagnostics. No explicit `retryable` signal in the response body.
- **Gap**: Missing retryable indicator. Agents must infer retryability from HTTP status codes rather than structured response data.
- **Compensating Controls**:
  - Document mapping from OperationOutcome issue codes to retryable/terminal
  - Agents infer retryability from HTTP status codes (429, 503 → retryable; 400, 403 → terminal)
- **Remediation Timeline**: 30 days
- **Recommendation**: Add a retryable extension to OperationOutcome responses.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/ExceptionHandlingInterceptor.java`

#### AUTH-Q5: Credential Management — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No built-in secrets management integration (no Vault, no AWS Secrets Manager client). Credentials configured via Spring application properties or environment variables. `@SensitiveNoDisplay` and `@PasswordField` annotations prevent serialization of credentials but do not manage rotation.
- **Gap**: No secrets management system integration. Credentials rely on deployment-time configuration without rotation support.
- **Compensating Controls**:
  - Configure Spring Boot to read secrets from AWS Secrets Manager via Spring Cloud AWS
  - Use environment variables injected from secrets store at deployment time
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Integrate with AWS Secrets Manager via Spring Cloud AWS for credential management with automatic rotation.
- **Evidence**: `hapi-fhir-base/src/main/java/ca/uhn/fhir/model/api/annotation/SensitiveNoDisplay.java`, `hapi-fhir-base/src/main/java/ca/uhn/fhir/model/api/annotation/PasswordField.java`

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Spring Boot auto-configuration allows local testing with in-memory databases. Sample applications demonstrate server setup. However, no dedicated sandbox or staging environment configuration exists in the repository. No seed data scripts or synthetic data generators for production-equivalent testing.
- **Gap**: No staging environment with production-equivalent data shape for safe agent testing.
- **Compensating Controls**:
  - Use Spring Boot with H2 in-memory database for local agent testing
  - Create Docker Compose environment with sample FHIR data
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a Docker Compose-based staging environment with synthetic FHIR data (Synthea-generated patients) for agent testing.
- **Evidence**: `hapi-fhir-spring-boot/hapi-fhir-spring-boot-samples/`

#### DATA-Q4: System of Record Designations — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: HAPI FHIR does not include system-of-record designations or master data management processes. When deployed alongside other clinical systems, there is no built-in mechanism to resolve conflicting records across systems.
- **Gap**: No golden record pattern or system-of-record designation. Agents querying multiple FHIR servers may encounter conflicting data without conflict resolution.
- **Compensating Controls**:
  - Use FHIR resource `meta.source` to identify the originating system
  - Implement MDM (Master Data Management) module for patient matching
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Configure FHIR resource provenance tracking and implement the HAPI FHIR MDM module for entity resolution.
- **Evidence**: No system-of-record configuration found. FHIR `meta.source` available but not enforced.

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Multi-version FHIR support (DSTU2 through R5) with content negotiation. No CI-based breaking change detection tooling.
- **Gap**: No automated contract testing in CI. Breaking API changes not automatically detected before release.
- **Compensating Controls**:
  - FHIR specification versioning provides strong stability guarantees within a version
  - CapabilityStatement declares supported operations as a machine-readable contract
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add OpenAPI spec diff or Pact contract tests to CI pipeline.
- **Evidence**: `hapi-fhir-converter/src/main/java/ca/uhn/hapi/converters/server/VersionedApiConverterInterceptor.java`

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: OpenTelemetry instrumentation annotations as a dependency. MDC usage for remote address and user agent. No explicit trace context propagation (`traceparent`) in server interceptors. No structured JSON logging built-in.
- **Gap**: No trace context propagation. No JSON structured logging. No consistent correlation_id.
- **Compensating Controls**:
  - Configure Logback with JSON encoder at deployment time
  - Add OpenTelemetry Java agent at deployment for automatic trace propagation
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a server interceptor propagating `traceparent` headers and injecting trace/span IDs into MDC.
- **Evidence**: `pom.xml` (OpenTelemetry dependency), `hapi-fhir-jpaserver-base/src/main/java/ca/uhn/fhir/jpa/provider/BaseJpaProvider.java`

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No alerting configuration in repository. `PerformanceTracingLoggingInterceptor` tracks search performance but only logs — no threshold alerting.
- **Gap**: No alerting infrastructure. Error rate spikes and latency degradation would go unnoticed.
- **Compensating Controls**:
  - Configure CloudWatch alarms on API Gateway metrics at deployment
  - Use AWS X-Ray service map with anomaly detection
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add IaC defining CloudWatch alarms for 5xx error rates and p99 latency.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/PerformanceTracingLoggingInterceptor.java`

#### ENG-Q1: Infrastructure Governance — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No infrastructure-as-code exists in this repository. No Terraform, CloudFormation, CDK, Helm, or Kustomize files.
- **Gap**: Agent-facing integration surface (API gateway, IAM, secrets, networking) is not defined as code.
- **Compensating Controls**:
  - Create a separate IaC repository for HAPI FHIR deployment infrastructure
  - Use CDK or Terraform to define the deployment stack
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Create deployment IaC defining API Gateway, IAM roles, VPC, database, and secrets management.
- **Evidence**: No IaC files found in repository. Absence is itself a finding.

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Extensive CI/CD via GitHub Actions and Azure Pipelines with parallel testing (256 modules), CodeQL security scanning, and Codecov. No API contract testing (Pact, Spring Cloud Contract) or OpenAPI spec validation in pipelines.
- **Gap**: CI/CD mature for unit/integration testing but lacks API contract testing.
- **Compensating Controls**:
  - 313+ REST API integration tests provide significant API behavior coverage
  - FHIR specification compliance tests serve as de facto contract tests
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add consumer-driven contract tests to CI pipeline.
- **Evidence**: `.github/workflows/parallel-pipeline-build.yml`, `.github/workflows/codeql-analysis.yml`

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No deployment rollback mechanism defined. No blue/green, canary, or CodeDeploy rollback. Release workflow handles version tagging only.
- **Gap**: No rollback strategy for broken agent-facing APIs.
- **Compensating Controls**:
  - Maven Central artifact versioning allows consumers to pin to previous versions
  - Deployment-level rollback at the infrastructure layer
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Define deployment IaC with blue/green or canary deployment and automatic rollback triggers.
- **Evidence**: `.github/workflows/release.yml`

#### ENG-Q5: Encryption at Rest — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No encryption-at-rest configuration in the repository. The library delegates entirely to infrastructure (database TDE, AWS EBS/S3 encryption). No `kms_key_id` references, no encryption config in IaC (because no IaC exists).
- **Gap**: No encryption-at-rest defined. Healthcare PHI stored in FHIR server databases may be unencrypted if infrastructure is not configured properly.
- **Compensating Controls**:
  - Configure RDS/Aurora encryption with KMS at deployment time
  - Enable EBS encryption for all volumes hosting FHIR data
- **Remediation Timeline**: 30 days
- **Recommendation**: Define IaC with `kms_key_id` on all data stores (RDS, S3, EBS) used by the FHIR server.
- **Evidence**: No encryption configuration found. Delegated to infrastructure layer.

---

## INFOs — Architecture and Design Inputs

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Strong idempotency support: ETag-based versioning, optimistic locking, conditional creates (`If-None-Exist`), `UserRequestRetryVersionConflictsInterceptor` for automatic retry on HTTP 409.
- **Implication**: When scope expands to write-enabled, idempotency controls are already in place.
- **Recommendation**: Ensure ETag support is enabled in deployment configuration.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/ETagSupportEnum.java`

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: JSON (`application/fhir+json`) and XML (`application/fhir+xml`) with content negotiation. JSON is the default.
- **Implication**: JSON responses are ideal for LLM-based agent consumption. FHIR resources are well-structured.
- **Recommendation**: Default to JSON for agent-facing deployments.
- **Evidence**: `hapi-fhir-spring-boot/hapi-fhir-spring-boot-samples/hapi-fhir-spring-boot-sample-server-jersey/src/main/resources/application.yml`

### API-Q7: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: HAPI FHIR supports FHIR Subscription resources (R5 topic-based subscriptions) for event-driven notifications on resource changes. Channels include REST-hook, websocket, and email. This enables reactive agent patterns.
- **Implication**: Event-driven patterns are available for proactive agents reacting to clinical data changes.
- **Recommendation**: Configure R5 topic-based subscriptions for agent-relevant resource changes.
- **Evidence**: `hapi-fhir-storage/src/main/java/ca/uhn/fhir/jpa/subscription/` (subscription framework)

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limit headers (`X-RateLimit-Remaining`, `Retry-After`) returned. Rate limiting expected at infrastructure layer.
- **Implication**: Agents cannot self-throttle based on server-reported limits.
- **Recommendation**: Add an interceptor returning rate limit headers when deployed behind a rate-limiting layer.
- **Evidence**: No rate limit header code found.

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: FHIR transaction bundles provide all-or-nothing semantics via database transactions. No multi-step saga pattern for cross-request workflows.
- **Implication**: When scope expands to write-enabled, transaction bundles provide atomicity for single-request operations. Multi-request sagas need application-level compensation.
- **Recommendation**: Implement compensation logic for write-enabled multi-step agent workflows.
- **Evidence**: `hapi-fhir-jpaserver-base/src/main/java/ca/uhn/fhir/jpa/dao/TransactionProcessor.java`

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits (max records per operation, max spend). `TransactionConcurrencySemaphoreInterceptor` limits concurrency but not scope.
- **Implication**: When scope expands to write-enabled, transaction limits should be implemented.
- **Recommendation**: Implement configurable per-agent limits on batch operation size.
- **Evidence**: `hapi-fhir-jpaserver-base/src/main/java/ca/uhn/fhir/jpa/interceptor/TransactionConcurrencySemaphoreInterceptor.java`

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: FHIR resource validation (profile, terminology binding) ensures structural quality. No data completeness scores, null rate monitoring, or freshness SLAs.
- **Implication**: Agents may encounter incomplete records. Validation ensures structure but not completeness.
- **Recommendation**: Implement data quality dashboards tracking resource completeness rates.
- **Evidence**: `hapi-fhir-validation/` module

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: FHIR field names are semantically meaningful by specification design (`Patient.birthDate`, `Observation.valueQuantity`, `MedicationRequest.dosageInstruction`). No legacy abbreviations.
- **Implication**: Excellent for LLM-based agent reasoning — no data dictionary needed.
- **Recommendation**: No action needed.
- **Evidence**: FHIR structure definitions in `hapi-fhir-structures-r4/`, `hapi-fhir-structures-r5/`

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: FHIR CapabilityStatement serves as metadata layer declaring resource types, search parameters, operations. StructureDefinitions describe schemas. SearchParameter resources define queryable fields.
- **Implication**: Rich, machine-readable metadata for agent tool discovery at runtime.
- **Recommendation**: Ensure CapabilityStatement is complete and accurate at deployment.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/provider/ServerCapabilityStatementProvider.java`

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No custom business outcome metrics published. Performance tracking exists but no business KPIs.
- **Implication**: No visibility into whether agent interactions produce good clinical outcomes.
- **Recommendation**: Implement business outcome metrics relevant to the deployment context.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/PerformanceTracingLoggingInterceptor.java`

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: PASS (no finding)
- **Finding**: HAPI FHIR exposes a documented RESTful API conforming to HL7 FHIR specification with CRUD operations on all resource types, search operations, batch/transaction bundles, and extended operations. Self-documenting via CapabilityStatement and runtime-generated OpenAPI.
- **Gap**: None.
- **Recommendation**: None.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/RestfulServer.java`, `hapi-fhir-server-openapi/src/main/java/ca/uhn/fhir/rest/openapi/OpenApiInterceptor.java`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: `OpenApiInterceptor` auto-generates OpenAPI 3.x at runtime. No static spec committed.
- **Gap**: No static, version-controlled OpenAPI specification.
- **Recommendation**: Export and version-control the generated OpenAPI spec as a build artifact.
- **Evidence**: `hapi-fhir-server-openapi/src/main/java/ca/uhn/fhir/rest/openapi/OpenApiInterceptor.java`

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: All errors returned as FHIR OperationOutcome with severity, code, and diagnostics. No explicit `retryable` signal.
- **Gap**: Missing retryable indicator in error responses.
- **Recommendation**: Add retryable extension to OperationOutcome.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/ExceptionHandlingInterceptor.java`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Strong idempotency: ETag versioning, optimistic locking, conditional creates, retry interceptor.
- **Gap**: N/A for read-only scope.
- **Recommendation**: Ensure ETag support enabled at deployment.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/ETagSupportEnum.java`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: JSON and XML FHIR responses with content negotiation. JSON is default.
- **Gap**: N/A
- **Recommendation**: Default to JSON for agent consumers.
- **Evidence**: `hapi-fhir-spring-boot/hapi-fhir-spring-boot-samples/hapi-fhir-spring-boot-sample-server-jersey/src/main/resources/application.yml`

#### API-Q6: Asynchronous Operation Support
- **Severity**: PASS (no finding)
- **Finding**: HAPI FHIR supports FHIR async request pattern and Bulk Data `$export` operation for long-running data exports. Batch processing via `hapi-fhir-storage-batch2` module implements job-based async execution with status polling. Step Functions-style workflow via internal job coordination.
- **Gap**: None. Async patterns exist for long-running operations.
- **Recommendation**: Ensure `$export` and async patterns are enabled in deployment.
- **Evidence**: `hapi-fhir-storage-batch2/` module, `hapi-fhir-jpaserver-base/src/main/java/ca/uhn/fhir/jpa/bulk/export/`

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: FHIR Subscription resources support event-driven notifications (REST-hook, websocket channels). R5 topic-based subscriptions available.
- **Gap**: N/A — capability exists.
- **Recommendation**: Configure topic-based subscriptions for agent-relevant resource changes.
- **Evidence**: `hapi-fhir-storage/src/main/java/ca/uhn/fhir/jpa/subscription/`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit headers or documentation. Expected at infrastructure layer.
- **Gap**: Agents cannot self-throttle based on server-reported limits.
- **Recommendation**: Add rate limit headers or document expected limits.
- **Evidence**: No rate limit header code found.

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: PASS (no finding)
- **Finding**: HAPI FHIR supports machine identity authentication via `BearerTokenAuthInterceptor` (OAuth2 Bearer tokens), custom interceptor implementations for API key validation, and integration points for external identity providers. Per-request principal attribution through `RequestDetails`.
- **Gap**: None. Framework provides the mechanism.
- **Recommendation**: Deploy with concrete identity provider (Cognito, Okta).
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/BearerTokenAuthInterceptor.java`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: `AuthorizationInterceptor` with `RuleBuilder` exists. No IaC for platform-level scoping.
- **Gap**: No infrastructure-level least-privilege enforcement defined.
- **Recommendation**: Create IaC with agent-specific IAM roles.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/AuthorizationInterceptor.java`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: PASS (no finding)
- **Finding**: `AuthorizationInterceptor` supports action-level authorization natively. Rules can allow `read` while denying `write` or `delete` on specific resource types. `SearchNarrowingInterceptor` restricts search results per authorization rules.
- **Gap**: None. Action-level authorization is a core framework feature.
- **Recommendation**: Configure rules per agent identity at deployment.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/RuleBuilder.java`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: PASS (no finding)
- **Finding**: HAPI FHIR supports identity propagation through request context. `RequestDetails` carries authenticated principal information through the entire request lifecycle. Multi-tenancy support (`UrlBaseTenantIdentificationStrategy`) allows distinguishing between tenants. The framework can differentiate caller identity for partition-based data access. JWT parsing is supported for extracting user context from tokens.
- **Gap**: None. Identity propagation mechanism exists through RequestDetails and tenant identification strategies.
- **Recommendation**: Configure deployment to pass `Authorization` headers through to downstream interceptors and ensure audit logs distinguish agent-as-self from agent-on-behalf-of-user.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/api/server/RequestDetails.java`, `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/tenant/UrlBaseTenantIdentificationStrategy.java`

#### AUTH-Q5: Credential Management
- **Severity**: RISK-QUALITY
- **Finding**: No built-in secrets management integration. Credentials configured via Spring properties or environment variables. `@SensitiveNoDisplay` prevents serialization but does not manage rotation.
- **Gap**: No secrets management system integration. No rotation support.
- **Recommendation**: Integrate with AWS Secrets Manager via Spring Cloud AWS.
- **Evidence**: `hapi-fhir-base/src/main/java/ca/uhn/fhir/model/api/annotation/SensitiveNoDisplay.java`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: BALP audit interceptor and Hibernate Envers provide audit trail generation. No immutable storage configured.
- **Gap**: Audit events stored in mutable datastore. No tamper-evident log pipeline.
- **Recommendation**: Implement immutable external audit store.
- **Evidence**: `hapi-fhir-storage/src/main/java/ca/uhn/fhir/jpa/interceptor/BalpAuditCaptureInterceptor.java`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: No built-in mechanism to suspend individual agent identities.
- **Gap**: Cannot isolate a misbehaving agent without external identity provider.
- **Recommendation**: Integrate with external IdP supporting per-client revocation.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/BearerTokenAuthInterceptor.java`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Transaction bundles provide all-or-nothing semantics. No multi-step saga pattern.
- **Gap**: No compensation for multi-request workflows.
- **Recommendation**: Implement compensation for write-enabled workflows.
- **Evidence**: `hapi-fhir-jpaserver-base/src/main/java/ca/uhn/fhir/jpa/dao/TransactionProcessor.java`

#### STATE-Q2: Queryable Current State
- **Severity**: PASS (no finding)
- **Finding**: HAPI FHIR exposes full read access to current resource state via standard FHIR read operations (GET /[type]/[id]), search operations, and _history operations for version history. Agents can always inspect current state before deciding next steps.
- **Gap**: None. Full queryable state via FHIR REST API.
- **Recommendation**: None.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/RestfulServer.java`

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled AND service has persistent state
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: Spring Retry with exponential backoff (500ms to 60s, 2x multiplier). No formal circuit breaker pattern. External calls to terminology servers and subscription endpoints lack circuit breaker protection.
- **Gap**: No circuit breaker. Cascading failures from external dependencies not prevented.
- **Recommendation**: Add Resilience4j circuit breaker for external service calls.
- **Evidence**: `hapi-fhir-storage/src/main/java/ca/uhn/fhir/jpa/util/Retrier.java`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No production rate limiting. Only concurrency semaphore for transactions.
- **Gap**: No per-client rate limiting.
- **Recommendation**: Deploy with API Gateway usage plans.
- **Evidence**: `hapi-fhir-jpaserver-base/src/main/java/ca/uhn/fhir/jpa/interceptor/TransactionConcurrencySemaphoreInterceptor.java`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits for agent operations.
- **Gap**: No per-agent operation limits.
- **Recommendation**: Implement for write-enabled scope.
- **Evidence**: `hapi-fhir-jpaserver-base/src/main/java/ca/uhn/fhir/jpa/interceptor/TransactionConcurrencySemaphoreInterceptor.java`

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
- **Finding**: Spring Boot auto-configuration allows local testing with in-memory databases. Sample applications exist. No dedicated sandbox environment configuration with production-equivalent data shape.
- **Gap**: No staging environment with production-equivalent data for safe agent testing.
- **Recommendation**: Create Docker Compose-based staging with synthetic FHIR data (Synthea-generated patients).
- **Evidence**: `hapi-fhir-spring-boot/hapi-fhir-spring-boot-samples/`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification ⚡
- **Severity**: PASS (no finding)
- **Finding**: **Stage A**: Yes — healthcare data system storing PHI. **Stage B**: B1 (CLEAR) — `ConsentInterceptor` and `IConsentService` provide field-level/resource-level filtering. `@SensitiveNoDisplay` prevents serialization of sensitive fields. B2 (CLEAR) — `AuthorizationInterceptor` with `RuleBuilder` provides access control differentiation by resource type and operation. B3 (INFO) — No formal machine-readable classification schema.
- **Gap**: B3 only — no formal classification metadata. B1 and B2 controls present.
- **Recommendation**: Consider adding formal data classification annotations.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/consent/ConsentInterceptor.java`, `hapi-fhir-base/src/main/java/ca/uhn/fhir/model/api/annotation/SensitiveNoDisplay.java`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Healthcare PHI subject to HIPAA/GDPR. Multi-tenancy supported but no residency enforcement.
- **Gap**: No data residency enforcement for healthcare PHI.
- **Recommendation**: Deploy with region-locked infrastructure.
- **Evidence**: `hapi-fhir-jpaserver-base/src/main/java/ca/uhn/fhir/jpa/partition/`

#### DATA-Q3: Selective Query Support
- **Severity**: PASS (no finding)
- **Finding**: Full pagination via `IPagingProvider` with configurable page sizes (`_count` parameter), offset paging, cursor-based paging, total counts. FHIR search includes rich filtering via search parameters, sorting via `_sort`, and field selection via `_elements`. Bundle responses include next/prev navigation links.
- **Gap**: None. Comprehensive query filtering and pagination.
- **Recommendation**: None.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/IPagingProvider.java`, `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/FifoMemoryPagingProvider.java`

#### DATA-Q4: System of Record Designations
- **Severity**: RISK-QUALITY
- **Finding**: No system-of-record designations or master data management processes built in. FHIR `meta.source` available but not enforced.
- **Gap**: No golden record pattern. Agents querying multiple systems encounter conflicting data.
- **Recommendation**: Configure FHIR resource provenance tracking. Implement MDM module.
- **Evidence**: No system-of-record configuration found.

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: PASS (no finding)
- **Finding**: All FHIR resources include `meta.lastUpdated` (automatic timestamp on every write) and `meta.versionId` (version tracking). Resources have `created_at` semantics via resource history. Timezone handling uses UTC. The `_since` parameter allows querying for resources modified after a given time. No staleness signaling headers but resource versioning provides freshness context.
- **Gap**: None. Temporal metadata is comprehensive via FHIR `meta` element.
- **Recommendation**: None.
- **Evidence**: `hapi-fhir-jpaserver-base/src/main/java/ca/uhn/fhir/jpa/model/entity/ResourceTable.java` (updatedDate field)

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: No PHI scrubbing in logging pipeline. `LoggingInterceptor` can log request/response bodies.
- **Gap**: PHI can leak into application logs.
- **Recommendation**: Implement log scrubbing interceptor.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/LoggingInterceptor.java`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: FHIR validation ensures structural quality. No completeness scores or freshness SLAs.
- **Gap**: No data quality metrics beyond structural validation.
- **Recommendation**: Implement data quality dashboards.
- **Evidence**: `hapi-fhir-validation/` module

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: Multi-version FHIR support with content negotiation. No CI-based breaking change detection.
- **Gap**: No automated contract testing in CI.
- **Recommendation**: Add contract tests to CI pipeline.
- **Evidence**: `hapi-fhir-converter/src/main/java/ca/uhn/hapi/converters/server/VersionedApiConverterInterceptor.java`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: FHIR field names semantically meaningful by specification design.
- **Gap**: N/A
- **Recommendation**: No action needed.
- **Evidence**: FHIR structure definitions in `hapi-fhir-structures-r4/`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: FHIR CapabilityStatement and StructureDefinitions serve as metadata layer.
- **Gap**: N/A
- **Recommendation**: Ensure CapabilityStatement is complete at deployment.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/provider/ServerCapabilityStatementProvider.java`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: OpenTelemetry dependency exists, MDC usage present. No trace propagation or JSON logging built-in.
- **Gap**: No trace context propagation. No structured JSON logging.
- **Recommendation**: Add trace propagation interceptor and JSON logging.
- **Evidence**: `pom.xml`, `hapi-fhir-jpaserver-base/src/main/java/ca/uhn/fhir/jpa/provider/BaseJpaProvider.java`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: No alerting configuration in repository.
- **Gap**: No alerting infrastructure.
- **Recommendation**: Add CloudWatch alarm definitions in IaC.
- **Evidence**: `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/PerformanceTracingLoggingInterceptor.java`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics published.
- **Gap**: No business outcome visibility.
- **Recommendation**: Implement business metrics for deployed context.
- **Evidence**: No custom metrics code found.

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance
- **Severity**: RISK-QUALITY
- **Finding**: No IaC in repository.
- **Gap**: Agent-facing infrastructure not defined as code.
- **Recommendation**: Create deployment IaC.
- **Evidence**: No IaC files found.

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: Extensive CI/CD. No API contract testing.
- **Gap**: Breaking API changes not automatically detected.
- **Recommendation**: Add consumer-driven contract tests.
- **Evidence**: `.github/workflows/parallel-pipeline-build.yml`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: No deployment rollback mechanism defined.
- **Gap**: No rollback strategy.
- **Recommendation**: Define blue/green or canary deployment in IaC.
- **Evidence**: `.github/workflows/release.yml`

#### ENG-Q4: API Test Coverage
- **Severity**: PASS (no finding)
- **Finding**: 1,932 test files with 313 REST API integration tests running in CI via parallel pipeline build. Tests cover input handling, output format, error responses, and edge cases for FHIR operations across DSTU2, DSTU3, R4, R4B, and R5 versions. Codecov integration reports coverage metrics.
- **Gap**: None. Comprehensive API test coverage.
- **Recommendation**: None.
- **Evidence**: `.github/workflows/parallel-pipeline-build.yml`, `hapi-fhir-jpaserver-test-*/src/test/java/`

#### ENG-Q5: Encryption at Rest
- **Severity**: RISK-QUALITY
- **Finding**: No encryption-at-rest configuration. Delegated entirely to infrastructure.
- **Gap**: No encryption config defined. Healthcare PHI may be unencrypted without infrastructure configuration.
- **Recommendation**: Define IaC with KMS encryption on all data stores.
- **Evidence**: No encryption configuration found.

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/RestfulServer.java` | API-Q1, STATE-Q2 |
| `hapi-fhir-server-openapi/src/main/java/ca/uhn/fhir/rest/openapi/OpenApiInterceptor.java` | API-Q1, API-Q2 |
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/ExceptionHandlingInterceptor.java` | API-Q3 |
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/ETagSupportEnum.java` | API-Q4 |
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/UserRequestRetryVersionConflictsInterceptor.java` | API-Q4 |
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/AuthorizationInterceptor.java` | AUTH-Q2, AUTH-Q3 |
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/RuleBuilder.java` | AUTH-Q2, AUTH-Q3 |
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/BearerTokenAuthInterceptor.java` | AUTH-Q1, AUTH-Q7 |
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/auth/SearchNarrowingInterceptor.java` | AUTH-Q3, DATA-Q1 |
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/api/server/RequestDetails.java` | AUTH-Q4 |
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/tenant/UrlBaseTenantIdentificationStrategy.java` | AUTH-Q4 |
| `hapi-fhir-storage/src/main/java/ca/uhn/fhir/jpa/interceptor/BalpAuditCaptureInterceptor.java` | AUTH-Q6 |
| `hapi-fhir-jpaserver-base/src/main/java/ca/uhn/fhir/jpa/config/EnversAuditConfig.java` | AUTH-Q6 |
| `hapi-fhir-jpaserver-base/src/main/java/ca/uhn/fhir/jpa/dao/TransactionProcessor.java` | STATE-Q1 |
| `hapi-fhir-jpaserver-base/src/main/java/ca/uhn/fhir/jpa/interceptor/TransactionConcurrencySemaphoreInterceptor.java` | STATE-Q5, STATE-Q6 |
| `hapi-fhir-storage/src/main/java/ca/uhn/fhir/jpa/util/Retrier.java` | STATE-Q4 |
| `hapi-fhir-jpaserver-base/src/main/java/ca/uhn/fhir/jpa/model/entity/ResourceTable.java` | DATA-Q5 |
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/consent/ConsentInterceptor.java` | DATA-Q1 |
| `hapi-fhir-base/src/main/java/ca/uhn/fhir/model/api/annotation/SensitiveNoDisplay.java` | AUTH-Q5, DATA-Q1 |
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/LoggingInterceptor.java` | DATA-Q6 |
| `hapi-fhir-jpaserver-base/src/main/java/ca/uhn/fhir/jpa/partition/` | DATA-Q2 |
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/IPagingProvider.java` | DATA-Q3 |
| `hapi-fhir-converter/src/main/java/ca/uhn/hapi/converters/server/VersionedApiConverterInterceptor.java` | DISC-Q1 |
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/provider/ServerCapabilityStatementProvider.java` | DISC-Q3 |
| `hapi-fhir-server/src/main/java/ca/uhn/fhir/rest/server/interceptor/PerformanceTracingLoggingInterceptor.java` | OBS-Q2, OBS-Q3 |
| `hapi-fhir-jpaserver-base/src/main/java/ca/uhn/fhir/jpa/provider/BaseJpaProvider.java` | OBS-Q1 |
| `hapi-fhir-storage/src/main/java/ca/uhn/fhir/jpa/subscription/` | API-Q7 |
| `hapi-fhir-storage-batch2/` | API-Q6 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/parallel-pipeline-build.yml` | ENG-Q2, ENG-Q4 |
| `.github/workflows/codeql-analysis.yml` | ENG-Q2 |
| `.github/workflows/release.yml` | ENG-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `pom.xml` | OBS-Q1 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `hapi-fhir-spring-boot/hapi-fhir-spring-boot-samples/hapi-fhir-spring-boot-sample-server-jersey/src/main/resources/application.yml` | API-Q5 |
