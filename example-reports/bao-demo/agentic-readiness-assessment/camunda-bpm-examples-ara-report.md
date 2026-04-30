# Agentic Readiness Assessment Report

**Target**: camunda-bpm-examples
**Date**: 2025-07-17
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: monorepo
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P1
**Tags**: camunda-c7, examples, multi-pattern
**Context**: Official Camunda Platform 7 usage examples covering service tasks, external tasks, multi-tenancy, and Spring Boot integration patterns.
**Archetype Justification**: The dominant sub-modules are Spring Boot applications with embedded Camunda engine, H2 database connections, REST APIs for process management (start/query/complete), user task forms, and process variable CRUD operations — characteristic of stateful-crud.

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 2 | **RISK-SAFETY**: 9 | **RISK-QUALITY**: 16 | **INFOs**: 15

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days.

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

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: No machine identity authentication (OAuth2 client credentials, API keys with principal attribution, or mTLS) is configured in any example module. The only authentication present is hardcoded basic auth with default credentials (`demo:demo`) in `spring-boot-starter/example-web/src/main/resources/application.yml`, `spring-boot-starter/example-twitter/src/main/resources/application.yaml`, `spring-boot-starter/example-webapp/src/main/resources/application.yaml`, and `spring-boot-starter/example-webapp-ee/src/main/resources/application.yaml`. The `spring-boot-starter/example-web/pom.xml` includes `spring-boot-starter-security` but no custom security configuration exists — only the default Spring Security auto-configuration with hardcoded username/password. The `authentication/basic/README.md` references a deprecated basic auth example that is no longer actively maintained. No OAuth2, JWT, mTLS, Cognito, or API Gateway authorizer configuration found.
- **Gap**: No machine identity authentication mechanism exists. Agents cannot authenticate with a service-level identity. All access uses shared hardcoded credentials (`demo:demo`) with no principal attribution in audit logs.
- **Remediation**:
  - **Immediate**: Implement OAuth2 client credentials flow or API key authentication with principal attribution for the Camunda REST API. Configure Spring Security with a custom `SecurityFilterChain` that supports service account authentication.
  - **Target State**: Each agent identity authenticates via a unique client credential or API key. Audit logs record the specific agent principal for every request.
  - **Estimated Effort**: Medium (2–4 weeks)
  - **Dependencies**: AUTH-Q6 (audit logging) depends on this — cannot log agent principal without machine identity.
- **Evidence**: `spring-boot-starter/example-web/pom.xml` (spring-boot-starter-security dep), `spring-boot-starter/example-web/src/main/resources/application.yml` (hardcoded demo:demo), `authentication/basic/README.md` (deprecated)

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: No sensitive data classification or field-level tagging found anywhere in the repository. Process variables (which may contain PII, financial data, or business-sensitive information) are stored in Camunda's process engine database (H2 in examples) with no classification metadata. The `spring-boot-starter/example-invoice` module handles invoice data including amounts, approver names, and creditor information — none classified. The `multi-tenancy/schema-isolation` module handles tenant-specific process data with no data sensitivity tagging. No Amazon Macie integration, no data classification tags on any storage resources (no IaC exists), no field-level encryption, and no column-level access controls found.
- **Gap**: Sensitive data (process variables, user task form data, invoice details) is neither classified nor tagged. An agent reading process variables has no way to know which fields contain sensitive data. No access controls distinguish sensitive from non-sensitive process data.
- **Remediation**:
  - **Immediate**: Inventory all process variables across BPMN definitions and classify each as PII, business-sensitive, or public. Document the classification in a data dictionary.
  - **Target State**: Process variables have classification metadata. Field-level access controls prevent agents from retrieving PII/sensitive fields without explicit authorization. Data classification is enforced at the Camunda REST API layer.
  - **Estimated Effort**: High (4–8 weeks)
  - **Dependencies**: DATA-Q6 (PII redaction in logs) depends on knowing which fields are sensitive.
- **Evidence**: `spring-boot-starter/example-invoice/src/main/resources/application.yaml`, `spring-boot-starter/example-invoice/src/main/resources/static/forms/start-form.html`, all BPMN process definitions, `multi-tenancy/schema-isolation/standalone.xml`

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No scoped permission model found. No IAM policies exist (no IaC). The Spring Boot examples use a single shared credential (`demo:demo`) with full access to the Camunda REST API. The `example-invoice` application.yaml has `camunda.bpm.authorization.enabled: true`, and the `multi-tenancy/schema-isolation/standalone.xml` has `authorizationEnabled: true` — Camunda's built-in authorization is enabled in some modules, but no role-per-agent or resource-level scoping is configured. All authenticated users receive the same broad access.
- **Gap**: No least-privilege model exists. An agent identity would inherit full read/write access to all process definitions, instances, tasks, and variables.
- **Compensating Controls**:
  - Configure Camunda's authorization framework to create agent-specific groups with read-only permissions on specific process definitions
  - Deploy an API Gateway in front of the Camunda REST API that restricts agent access to specific endpoints (GET only)
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure Camunda's built-in authorization service to define agent-specific roles with read-only permissions scoped to specific process definitions and task types.
- **Evidence**: `spring-boot-starter/example-invoice/src/main/resources/application.yaml` (authorization.enabled: true), `multi-tenancy/schema-isolation/standalone.xml` (authorizationEnabled: true), `spring-boot-starter/example-web/src/main/resources/application.yml`

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization (ABAC or fine-grained RBAC) implemented. The TenantInterceptor in `multi-tenancy/schema-isolation` performs tenant-level filtering based on query parameters but not action-level (read vs. write vs. delete) authorization. No `canRead`, `canWrite`, `canDelete` checks found in any REST resource classes. The Camunda engine supports built-in authorization checks at the resource/permission level, but none of the example modules configure granular permissions.
- **Gap**: An authenticated agent could potentially execute any operation (start processes, complete tasks, modify variables, delete instances) — no action-level control distinguishes read from write.
- **Compensating Controls**:
  - Use Camunda's authorization service to assign READ permission without WRITE/DELETE/CREATE permissions to agent groups
  - Implement a reverse proxy or API Gateway that blocks non-GET HTTP methods for agent identities
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Leverage Camunda's built-in `Authorization` resource to define fine-grained permissions per resource type (Process Definition, Process Instance, Task) per action (READ, CREATE, UPDATE, DELETE).
- **Evidence**: `multi-tenancy/schema-isolation/src/main/java/org/camunda/bpm/tutorial/multitenancy/TenantInterceptor.java`, `multi-tenancy/schema-isolation/src/main/java/org/camunda/bpm/tutorial/multitenancy/ProcessDefinitionResource.java`

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No immutable audit logging configured. No CloudTrail, no S3 bucket with object lock, no CloudWatch log retention policies. The WildFly standalone.xml in `multi-tenancy/schema-isolation` configures a `json-formatter` audit log and `file-audit-log` at the Elytron security layer, but the audit logger is explicitly `enabled="false"`. Camunda's history service tracks process execution events but this is not immutable or tamper-evident — it uses the same H2 database as the process engine.
- **Gap**: No immutable, tamper-evident audit trail for API operations. Agent-initiated requests are not logged with principal attribution. Camunda history events are mutable (stored in the same database).
- **Compensating Controls**:
  - Enable the WildFly audit logger (`enabled="true"`) in standalone.xml as an immediate step
  - Configure Spring Boot Actuator audit events to write to an append-only log store
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement structured audit logging with agent identity fields (principal, action, resource, timestamp) written to an immutable log store (e.g., CloudWatch Logs with retention lock, S3 with Object Lock).
- **Evidence**: `multi-tenancy/schema-isolation/standalone.xml` (audit-log enabled="false"), `spring-boot-starter/example-web/pom.xml` (spring-boot-starter-actuator)

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No mechanism for suspending or revoking individual agent identities. Since the only authentication is shared hardcoded credentials (`demo:demo`), there is no concept of individual agent identity to suspend. No API key revocation endpoints, no service account disable mechanism, no Cognito user pool configuration found.
- **Gap**: If an agent exhibits anomalous behavior, the only option is to change the shared `demo:demo` password, which would disrupt all other consumers.
- **Compensating Controls**:
  - Implement agent-specific API keys or OAuth2 client IDs that can be individually revoked
  - Use an API Gateway with per-agent API keys that support key-level disabling
- **Remediation Timeline**: 30–60 days (depends on AUTH-Q1 resolution)
- **Recommendation**: Once machine identity (AUTH-Q1) is implemented, ensure each agent has an individually revocable identity. Implement a "kill switch" API or IAM mechanism for immediate agent suspension.
- **Evidence**: `spring-boot-starter/example-web/src/main/resources/application.yml` (shared demo:demo credential)

#### STATE-Q1: Compensation and Rollback ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The Camunda BPM engine natively supports BPMN compensation events and rollback patterns. However, no compensation handlers or boundary compensation events are defined in any of the 53 BPMN process definitions in this repository. The `servicetask/service-invocation-asynchronous` example demonstrates the signallable activity behavior pattern (wait state with callback) but not compensation. No saga patterns, two-phase commit, or explicit undo endpoints found. The `TwitterDemoProcess.bpmn` shows a simple linear flow with no error handling or compensation.
- **Gap**: No compensation or rollback mechanisms are implemented in any example process. If a multi-step workflow fails mid-sequence, processes are left in an incomplete state.
- **Compensating Controls**:
  - Camunda's built-in process instance cancellation API can terminate stuck instances
  - BPMN error boundary events could be added to critical service tasks for graceful failure handling
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add BPMN compensation boundary events and compensation handlers to critical process steps, particularly in the invoice and loan-granting workflows.
- **Evidence**: All 53 `.bpmn` files (no compensation events found), `servicetask/service-invocation-asynchronous/src/main/java/org/camunda/quickstart/servicetask/invocation/AsynchronousServiceTask.java`, `spring-boot-starter/example-twitter/src/main/resources/TwitterDemoProcess.bpmn`

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No rate limiting or throttling configured at any layer. No API Gateway throttle settings, no WAF rate rules, no application-level rate limiting middleware. No `express-rate-limit`, `spring-cloud-gateway`, or similar dependencies found. No `aws_api_gateway_usage_plan` in IaC (no IaC exists). The Camunda REST API is exposed directly via `camunda-bpm-spring-boot-starter-rest` with no rate limit protection.
- **Gap**: A runaway agent loop could flood the Camunda REST API at machine speed with no throttling protection, potentially overwhelming the embedded process engine and H2 database.
- **Compensating Controls**:
  - Deploy an API Gateway (AWS API Gateway, Kong, or nginx) in front of the Camunda REST API with rate limit configuration
  - Use Spring Boot's `WebMvcConfigurer` to add a request rate interceptor
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Implement rate limiting at the API Gateway layer. Configure per-client throttling that limits agent request rates to a safe throughput for the backend.
- **Evidence**: `spring-boot-starter/example-web/pom.xml` (no rate limit deps), all `application.yaml/yml` files (no rate limit config)

#### DATA-Q2: Data Residency and Sovereignty ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No data residency or sovereignty requirements documented. No GDPR, LGPD, or HIPAA compliance references found. All data stores use H2 in-memory or file-based databases with no region configuration. The `spring-boot-starter/example-invoice/src/main/resources/application.yaml` shows commented-out connection strings for PostgreSQL, MySQL, Oracle, DB2, and SQL Server — indicating the intent to support multiple database backends — but no region-specific configurations exist. No cross-region replication settings.
- **Gap**: If process variables contain regulated data (PII, financial data), there are no controls preventing an agent from transmitting this data to an LLM endpoint in a different region or jurisdiction. Data residency requirements are unknown.
- **Compensating Controls**:
  - Document data residency requirements before agent deployment
  - Configure LLM endpoints to use same-region Bedrock instances to keep data within jurisdiction
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Conduct a data residency assessment. Document which process variables contain regulated data and what jurisdictional constraints apply. Configure agent LLM interactions to comply with identified constraints.
- **Evidence**: `spring-boot-starter/example-invoice/src/main/resources/application.yaml` (database URLs), `quarkus-extension/datasource-example/src/main/resources/application.properties`

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No PII redaction in logs found. No log scrubbing middleware, no PII masking libraries, no CloudWatch log filters, no Amazon Macie integration, no regex patterns for PII in logging utilities. The examples use standard SLF4J/Logback logging with no filtering. Process variables (which may contain names, addresses, financial amounts) are logged as-is by the Camunda engine's default logging.
- **Gap**: Process variables containing PII flow into logs without redaction. Agent-initiated queries that return process variable data could leak PII into LLM prompt/response logs.
- **Compensating Controls**:
  - Implement a Logback filter that masks known PII fields (e.g., email, name, address patterns)
  - Configure log levels to minimize process variable logging in production
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Implement PII-aware log filtering using a Logback `TurboFilter` or Camunda history event handler that masks sensitive process variable values before logging.
- **Evidence**: All `application.yaml/yml` files (no log filtering config), all Java source files (no PII masking logic)

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No circuit breakers, retry logic (application-level), or timeout configurations found. No Resilience4j, Polly, or `@CircuitBreaker` annotations. The `process-engine-plugin/failed-job-retry-profile` module implements retry configuration for BPMN job failures but this is internal engine retry, not external dependency protection. The `clients/java/order-handling/src/main/java/org/camunda/bpm/App.java` configures HTTP response timeout (`Timeout.ofSeconds(15)`) but no circuit breaker.
- **Gap**: No circuit breakers protect against cascading failures when the target system's dependencies fail. A runaway agent calling a degraded service will amplify the failure.
- **Compensating Controls**:
  - Add Resilience4j circuit breaker to external HTTP clients
  - Configure timeout values on all outbound connections
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add Resilience4j circuit breaker and retry patterns to modules that call external services. Configure timeout budgets for all downstream dependencies.
- **Evidence**: `clients/java/order-handling/src/main/java/org/camunda/bpm/App.java` (timeout config only), `process-engine-plugin/failed-job-retry-profile/` (internal retry only)

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, GraphQL schema, or Smithy files found in the repository. The Camunda REST API (exposed via `camunda-bpm-spring-boot-starter-rest`) has an OpenAPI spec available in the external Camunda documentation, but it is not co-located with the repository. Custom JAX-RS endpoints in `quarkus-extension/datasource-example` and `multi-tenancy/schema-isolation` have no API specification.
- **Gap**: No machine-readable API specification in-repository. Agent tool generation requires manual authoring. Custom endpoints lack any specification.
- **Compensating Controls**:
  - Reference the external Camunda REST API OpenAPI spec for tool generation
  - Generate OpenAPI specs from JAX-RS annotations using `smallrye-open-api` (Quarkus) or `springdoc-openapi` (Spring Boot)
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add `springdoc-openapi-starter-webmvc-ui` to Spring Boot modules and `quarkus-smallrye-openapi` to Quarkus modules to auto-generate OpenAPI specs from existing REST controllers.
- **Evidence**: Repository-wide search for `openapi.yaml`, `swagger.yaml`, `*.graphql`, `*.smithy` — none found

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Minimal structured error handling. The Quarkus `ApprovalProcessService.java` catches `IllegalArgumentException` but returns a plain text string ("Please provide a positive integer value") — not a structured error response. The `TenantInterceptor.java` throws `WebApplicationException(Status.BAD_REQUEST)` without a structured body. The Camunda REST API provides its own error response format (JSON with `type`, `message`), but custom endpoints do not follow this pattern. No consistent error code/message/retryable structure found.
- **Gap**: Custom endpoints lack structured error responses. Agents cannot distinguish retriable from terminal errors in custom REST resources.
- **Compensating Controls**:
  - Rely on Camunda REST API's built-in error format for the majority of agent interactions
  - Add JAX-RS `ExceptionMapper` implementations for custom endpoints
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Implement a global exception handler (`@ControllerAdvice` for Spring Boot, JAX-RS `ExceptionMapper` for Quarkus/Jakarta) that returns structured JSON error responses with error code, message, and retryable flag.
- **Evidence**: `quarkus-extension/datasource-example/src/main/java/org/camunda/bpm/quarkus/example/datasource/rest/ApprovalProcessService.java`, `multi-tenancy/schema-isolation/src/main/java/org/camunda/bpm/tutorial/multitenancy/TenantInterceptor.java`

#### API-Q6: Asynchronous Operation Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: BPMN processes are inherently long-running. The Camunda engine supports async continuation (enabled in example-invoice via `job-execution.core-pool-size: 10`). The `servicetask/service-invocation-asynchronous` module demonstrates the asynchronous service task pattern with signal callbacks. The external task client pattern (`clients/java/order-handling`, `spring-boot-starter/external-task-client/loan-granting-spring-boot-webapp`) implements long-polling for asynchronous task processing. However, no explicit job status polling endpoints or webhook callback mechanisms are exposed to external consumers.
- **Gap**: While the engine supports async internally, there is no standardized polling or webhook API for external consumers (agents) to track long-running process completion.
- **Compensating Controls**:
  - Use the Camunda REST API's process instance query endpoint to poll for completion
  - Implement a webhook notification mechanism using Camunda execution listeners
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Expose a process status polling endpoint or implement webhook callbacks that notify agents when long-running BPMN processes complete or reach a milestone.
- **Evidence**: `servicetask/service-invocation-asynchronous/src/main/java/org/camunda/quickstart/servicetask/invocation/AsynchronousServiceTask.java`, `spring-boot-starter/example-invoice/src/main/resources/application.yaml` (job-execution config), `clients/java/order-handling/src/main/java/org/camunda/bpm/App.java`

#### STATE-Q2: Queryable Current State — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The Camunda REST API exposes comprehensive state query endpoints (process instance state, task state, variable values, history). The `ProcessDefinitionResource.java` in multi-tenancy/schema-isolation queries process definitions via the repository service. The Camunda REST API at `/engine-rest` provides GET endpoints for process instances, tasks, variables, and history — enabling read-before-act patterns. However, this capability is provided by the Camunda framework, not custom application code.
- **Gap**: State is queryable via the Camunda REST API, but there is no application-specific state query abstraction. Agents must understand Camunda's API model to query state.
- **Compensating Controls**:
  - Leverage Camunda REST API's query capabilities directly — these are well-documented
  - Build agent tool definitions that abstract Camunda API queries into domain-specific operations
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Create domain-specific query endpoints that abstract Camunda's process state model into business-meaningful queries (e.g., "get pending invoices" instead of "query process instances by process definition key").
- **Evidence**: `multi-tenancy/schema-isolation/src/main/java/org/camunda/bpm/tutorial/multitenancy/ProcessDefinitionResource.java`, `spring-boot-starter/example-web/src/test/java/org/camunda/bpm/spring/boot/example/web/CamundaBpmRestTest.java`

#### DATA-Q3: Selective Query Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The Camunda REST API supports pagination (`firstResult`, `maxResults` query parameters), filtering (by process definition key, business key, variables), and sorting on most query endpoints. The custom `ProcessDefinitionResource.java` in `multi-tenancy/schema-isolation` uses `createProcessDefinitionQuery().list()` — an unbounded query with no pagination. Custom Quarkus endpoints similarly lack pagination support.
- **Gap**: Camunda REST API has built-in pagination, but custom endpoints do not implement it. Unbounded queries from custom endpoints could exhaust LLM context windows.
- **Compensating Controls**:
  - Direct agent interactions to the Camunda REST API's paginated endpoints rather than custom endpoints
  - Add `firstResult`/`maxResults` parameters to custom query endpoints
- **Remediation Timeline**: 7–14 days
- **Recommendation**: Add pagination parameters to custom JAX-RS endpoints. Use Camunda's query API with `.listPage(firstResult, maxResults)` instead of `.list()`.
- **Evidence**: `multi-tenancy/schema-isolation/src/main/java/org/camunda/bpm/tutorial/multitenancy/ProcessDefinitionResource.java` (unbounded `.list()`)

#### DATA-Q4: System of Record Designations — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No system-of-record designations found. No master data management references, no data ownership definitions, no conflict resolution logic. Each example module operates independently with its own H2 database — no shared data store or golden record pattern.
- **Gap**: If agents query multiple example modules, there is no designated system of record for any entity. No conflict resolution mechanism exists.
- **Compensating Controls**:
  - Document which Camunda process engine instance is authoritative for each process definition
  - Limit agent access to a single engine instance per domain
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Document system-of-record designations for process definitions and process instance data.
- **Evidence**: All `application.yaml/yml` files (independent H2 databases per module), `pom.xml` (root — independent modules)

#### DATA-Q5: Temporal Metadata and Freshness — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Camunda's process engine automatically records timestamps for process instance start/end, task creation/completion, and variable updates in its history tables. However, no timezone normalization is configured, no `Cache-Control` or `X-Data-Age` headers are set on REST responses, and no data freshness signaling exists. The H2 in-memory databases have no configured consistency level signaling.
- **Gap**: While Camunda records temporal metadata internally, REST responses do not signal data freshness, caching, or consistency characteristics to consuming agents.
- **Compensating Controls**:
  - Agents can query Camunda's history API for temporal metadata on process events
  - Add `Last-Modified` or `Cache-Control` headers to custom REST endpoints
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add `Cache-Control` and `Last-Modified` response headers to custom endpoints. Document the eventual consistency characteristics of Camunda history data.
- **Evidence**: All `application.yaml/yml` files (no cache/freshness config)

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No schema versioning or API contract testing found. No JSON Schema files, no Avro/Protobuf schemas, no schema registry, no `/v1/` URL patterns. The Camunda REST API has versioning managed externally by Camunda (tied to the engine version 7.24.0), but no in-repository contract tests or breaking change detection. No Pact tests, no OpenAPI diff tools, no `buf breaking` configuration. The two GitHub Actions workflows (`.github/workflows/main.yml` and `.github/workflows/bump-versions.yml`) handle version bumping only — no CI/CD with contract validation.
- **Gap**: No schema versioning or breaking change detection. API changes could break agent tool bindings silently.
- **Compensating Controls**:
  - Pin agent tool definitions to specific Camunda REST API version (7.24.0)
  - Monitor Camunda release notes for REST API breaking changes
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add consumer-driven contract tests (Pact) or OpenAPI spec diffing to the CI pipeline to detect breaking API changes.
- **Evidence**: `.github/workflows/main.yml`, `.github/workflows/bump-versions.yml`, `pom.xml` (root)

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No distributed tracing (X-Ray, OpenTelemetry) or structured logging found. No OpenTelemetry SDK, no X-Ray instrumentation, no `traceparent` header propagation. Logging uses SLF4J with default unstructured text format. No `request_id` or `correlation_id` fields in log output. The Spring Boot Actuator is included in `example-web` but only for health checks — no tracing configuration.
- **Gap**: Agent-initiated requests cannot be traced through the system. No correlation IDs link log entries for a single request. Debugging agent failures requires manual log correlation.
- **Compensating Controls**:
  - Add Micrometer Tracing (Spring Boot 3.x built-in) with a trace ID propagation filter
  - Configure Logback with `%X{traceId}` MDC pattern for structured correlation
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add `micrometer-tracing-bridge-otel` and configure OpenTelemetry export. Switch to structured JSON logging with correlation ID fields.
- **Evidence**: `spring-boot-starter/example-web/pom.xml` (actuator present, no tracing), all `application.yaml/yml` files (no tracing config)

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No alerting thresholds configured. No CloudWatch alarms, no anomaly detection, no PagerDuty/OpsGenie integration, no SLO-based alerting. The Spring Boot Actuator in `example-web` provides basic health endpoints but no alerting. Camunda metrics are explicitly disabled (`camunda.bpm.metrics.enabled: false`) in `example-web` and `example-simple`.
- **Gap**: No alerting for API error rates or latency. Target system degradation would not be detected before agents start cascading failures.
- **Compensating Controls**:
  - Enable Camunda metrics and Spring Boot Actuator metrics endpoints
  - Integrate with Prometheus/Grafana for alerting
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Enable `camunda.bpm.metrics.enabled: true`, configure Micrometer metrics export, and set up alerting thresholds for error rates and latency.
- **Evidence**: `spring-boot-starter/example-web/src/main/resources/application.yml` (metrics disabled), `spring-boot-starter/example-simple/src/main/resources/application.yaml` (metrics disabled)

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No infrastructure-as-code found. No Terraform, CloudFormation, CDK, Helm, or Kustomize files in the repository. The agent-facing integration surface (REST API, database, network configuration) is not defined as code. No drift detection, no peer review on infrastructure changes (because there is no IaC to review).
- **Gap**: The entire infrastructure is undefined as code. Changes to the agent-facing surface are manual and untracked.
- **Compensating Controls**:
  - Document the target deployment architecture before agent integration
  - Define the agent-facing surface in IaC as a prerequisite for agent deployment
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Define the deployment infrastructure (API Gateway, database, IAM roles, networking) in Terraform or CDK before production agent deployment.
- **Evidence**: Repository-wide search for `.tf`, `template.yaml`, `cdk.json`, `Chart.yaml` — none found

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The two GitHub Actions workflows (`.github/workflows/main.yml` and `.github/workflows/bump-versions.yml`) are version bumping workflows only — no build, test, or deployment pipeline. No API contract tests, no consumer-driven contract testing (Pact), no OpenAPI spec validation, no schema comparison tools, no breaking change detection in CI.
- **Gap**: No CI/CD pipeline for building, testing, or deploying the examples. No automated detection of API breaking changes.
- **Compensating Controls**:
  - Run `mvn verify` manually before deploying changes
  - Add a CI workflow that runs Maven tests and validates API contracts
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a GitHub Actions CI workflow that runs `mvn verify` across all modules and includes API contract validation.
- **Evidence**: `.github/workflows/main.yml`, `.github/workflows/bump-versions.yml`

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No rollback capability configured. No blue/green deployment, no CodeDeploy rollback triggers, no Helm rollback, no feature flags, no canary deployment. No deployment infrastructure exists — the examples are designed to run locally or in development environments.
- **Gap**: No mechanism to roll back to a previous known-good state if a change breaks agent-facing APIs.
- **Compensating Controls**:
  - Use Git tag-based version pinning (the repo already uses version tags: 7.24, 7.23, etc.)
  - Deploy behind an API Gateway with traffic shifting capability
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Define a deployment strategy with rollback capability (blue/green, canary) as part of the IaC implementation (ENG-Q1).
- **Evidence**: `README.md` (version tags listed), `.github/workflows/` (no deployment pipeline)

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: 32 test files found across the repository. Tests include Camunda BPM Assert tests (`testing/assert/`, `testing/junit5/`), Spring Boot integration tests (`CamundaBpmRestTest.java`, `CamundaBpmActuatorTest.java`), process engine plugin tests, and unit tests for service tasks. The `CamundaBpmRestTest.java` validates the REST API returns process definitions correctly. However, test coverage is limited — most modules have 1–2 test files covering the happy path only. No API contract tests, no error response validation, no edge case testing for agent consumption patterns.
- **Gap**: Basic test coverage exists but is insufficient for agent-facing API validation. No error response testing, no pagination testing, no concurrent access testing.
- **Compensating Controls**:
  - Add API integration tests specifically for agent consumption patterns
  - Use Postman/Newman collections for REST API validation
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Expand test coverage to include error scenarios, pagination edge cases, and concurrent request handling — patterns that agents will exercise.
- **Evidence**: `spring-boot-starter/example-web/src/test/java/org/camunda/bpm/spring/boot/example/web/CamundaBpmRestTest.java`, `spring-boot-starter/example-web/src/test/java/org/camunda/bpm/spring/boot/example/web/CamundaBpmActuatorTest.java`, `testing/assert/`, `testing/junit5/`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No encryption at rest configured. All data stores use H2 in-memory or file-based databases with no encryption. No KMS keys, no customer-managed encryption keys, no `kms_key_id` settings (no IaC exists). The `spring-boot-starter/example-invoice/src/main/resources/application.yaml` shows `jdbc:h2:./camunda-h2-default/process-engine` — a file-based H2 database with no encryption. The `multi-tenancy/schema-isolation/standalone.xml` defines datasources with `jdbc:h2:mem:test` and `jdbc:h2:./camunda-h2-dbs/process-engine` — neither encrypted.
- **Gap**: Process data stored in H2 file databases is unencrypted at rest. A breach exposes all process variables and history data.
- **Compensating Controls**:
  - Use H2's built-in CIPHER option for file-based databases (`jdbc:h2:./db;CIPHER=AES`)
  - Migrate to a managed database service (RDS, Aurora) with KMS encryption for production
- **Remediation Timeline**: 14–30 days
- **Recommendation**: For production deployment, replace H2 with a managed database (RDS PostgreSQL, Aurora) with KMS encryption at rest. For development, enable H2 CIPHER.
- **Evidence**: `spring-boot-starter/example-invoice/src/main/resources/application.yaml` (H2 file URL), `multi-tenancy/schema-isolation/standalone.xml` (H2 datasources), `quarkus-extension/datasource-example/src/main/resources/application.properties` (H2 mem)

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No dedicated sandbox or staging environment configuration found. No separate environment configs (staging, sandbox), no Docker Compose for local testing, no seed data scripts, no synthetic data generators. The examples are designed to run locally with H2 in-memory databases, which provides a form of isolation, but there is no production-equivalent staging environment with realistic data shapes.
- **Gap**: No staging environment for testing agent behavior before production. The first time agent behavior would be tested is against real process data.
- **Compensating Controls**:
  - Use the H2 in-memory configuration as a lightweight sandbox
  - Create a Docker Compose setup that mimics production topology
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a Docker Compose-based staging environment with seed data that mirrors production process definitions and variable structures.
- **Evidence**: All `application.yaml/yml` files (single environment config), no `docker-compose.yml` found

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO
- **Finding**: The Spring Boot examples (`example-web`, `example-invoice`, `example-webapp`) expose the Camunda REST API via `camunda-bpm-spring-boot-starter-rest` at the `/engine-rest` path. The Quarkus examples expose custom JAX-RS endpoints (`/approval-process`, `/store-order-items`, `/process-definition`). The `deployment/embedded-spring-rest` module embeds the Camunda REST API in a plain Spring/Tomcat application. The Camunda REST API is a well-documented, comprehensive REST interface for process engine operations. Integration does not require direct database access or UI automation.
- **Implication**: Agents can bind to the Camunda REST API as a stable integration surface. The external Camunda REST API documentation serves as the interface contract.
- **Recommendation**: Document custom JAX-RS endpoints alongside the Camunda REST API surface to provide a complete integration map for agent tool builders.
- **Evidence**: `spring-boot-starter/example-web/pom.xml` (camunda-bpm-spring-boot-starter-rest), `spring-boot-starter/example-web/src/main/java/org/camunda/bpm/spring/boot/example/web/RestApplication.java`, `quarkus-extension/datasource-example/src/main/java/org/camunda/bpm/quarkus/example/datasource/rest/ApprovalProcessService.java`

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No idempotency key support found in any write endpoints. The Quarkus `StartProcessRestResource.java` exposes a POST endpoint that starts a process instance with no idempotency protection. The Camunda REST API's process start endpoint does not support idempotency keys natively. No unique constraint enforcement on business keys for deduplication. No idempotency middleware or decorators found.
- **Implication**: If agent scope is ever expanded to write-enabled, idempotency must be addressed first. Duplicate process instance creation on retry would be a data integrity risk at machine speed.
- **Recommendation**: Evaluate idempotency needs before expanding to write-enabled scope. Consider adding business key uniqueness constraints and idempotency middleware.
- **Evidence**: `quarkus-extension/spin-plugin-example/src/main/java/org/camunda/bpm/quarkus/example/rest/StartProcessRestResource.java` (POST with no idempotency)

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: The Camunda REST API returns JSON responses (confirmed by `@Produces(MediaType.APPLICATION_JSON)` annotations and Spring Boot auto-configuration). Custom endpoints return JSON (`ProcessDefinitionResource.java`) or plain text (`ApprovalProcessService.java` returns `MediaType.TEXT_PLAIN`). No XML, Protobuf, or binary response formats found.
- **Implication**: JSON responses are well-suited for LLM consumption. The plain text response in `ApprovalProcessService` is a minor concern — agents prefer structured JSON.
- **Recommendation**: Standardize all custom endpoints to return structured JSON responses.
- **Evidence**: `multi-tenancy/schema-isolation/src/main/java/org/camunda/bpm/tutorial/multitenancy/ProcessDefinitionResource.java`, `quarkus-extension/datasource-example/src/main/java/org/camunda/bpm/quarkus/example/datasource/rest/ApprovalProcessService.java`

### API-Q7: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: BPMN processes support signal and message events natively. The `startevent/message-start` module demonstrates message start events. The `servicetask/service-invocation-asynchronous` module demonstrates asynchronous signal patterns. The `TwitterDemoProcess.bpmn` uses service tasks with delegate expressions that could emit events. However, no webhook endpoints, no SNS/EventBridge integration, no Kafka topics, and no CDC pipelines are configured.
- **Implication**: The Camunda engine supports event-driven patterns internally, but no external event emission mechanism exists. Proactive agent patterns (reacting to process state changes) would require polling.
- **Recommendation**: Implement Camunda execution listeners that publish process state changes to an event bus (SNS, EventBridge) for agent consumption.
- **Evidence**: `startevent/message-start/src/main/resources/message_start_process.bpmn`, `servicetask/service-invocation-asynchronous/src/main/resources/asynchronousServiceInvocation.bpmn`

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limit documentation or headers found. No `X-RateLimit-Remaining`, `Retry-After`, or `X-RateLimit-Limit` headers in any response code. No API Gateway usage plans. No rate limit documentation in README or API docs.
- **Implication**: Agents calling at machine speed have no visibility into rate limits (which don't exist — see STATE-Q5). Once rate limits are implemented, documenting them and returning headers enables agent self-throttling.
- **Recommendation**: When rate limits are implemented (STATE-Q5), include `X-RateLimit-Remaining` and `Retry-After` headers in API responses.
- **Evidence**: All Java source files (no rate limit header code)

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: INFO
- **Finding**: No identity propagation patterns found. No JWT parsing middleware, no OAuth2 on-behalf-of flows, no token exchange patterns. The `TenantInterceptor.java` extracts a `user` query parameter to determine tenant context — this is a demonstration pattern, not a secure identity propagation mechanism. No separation between agent-as-self and agent-on-behalf-of-user call patterns.
- **Implication**: For stateful-crud archetype, this would normally be RISK. However, downgraded to INFO because the examples are demonstration code and identity propagation would be an architecture decision for production deployment.
- **Recommendation**: When productionizing, implement JWT-based identity propagation that distinguishes agent-as-self from agent-on-behalf-of-user.
- **Evidence**: `multi-tenancy/schema-isolation/src/main/java/org/camunda/bpm/tutorial/multitenancy/TenantInterceptor.java`

### AUTH-Q5: Credential Management

- **Severity**: INFO
- **Finding**: Credentials are hardcoded in configuration files across the repository. `spring-boot-starter/example-web/src/main/resources/application.yml` has `password: demo`. `spring-boot-starter/example-invoice/src/main/resources/application.yaml` has `password: camunda` for database credentials. `quarkus-extension/datasource-example/src/main/resources/application.properties` has `password=sa`. `multi-tenancy/schema-isolation/standalone.xml` has `password="sa"` in datasource security elements. No AWS Secrets Manager, no HashiCorp Vault, no environment variable indirection for secrets.
- **Implication**: Hardcoded credentials are expected in example code but are a security vulnerability in production. For agent deployment, credentials must be externalized.
- **Recommendation**: Migrate all credentials to AWS Secrets Manager or HashiCorp Vault before production deployment. Use Spring Boot's `spring-cloud-starter-aws-secrets-manager-config` for seamless integration.
- **Evidence**: `spring-boot-starter/example-web/src/main/resources/application.yml`, `spring-boot-starter/example-invoice/src/main/resources/application.yaml`, `quarkus-extension/datasource-example/src/main/resources/application.properties`, `multi-tenancy/schema-isolation/standalone.xml`

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The Camunda BPM engine uses optimistic locking internally for process instance state management. The H2 database supports `TRANSACTION_READ_COMMITTED` isolation level (configured in `multi-tenancy/schema-isolation/standalone.xml`). However, no application-level concurrency controls (ETags, version fields, `If-Match` headers) are exposed in REST responses. Custom endpoints have no concurrency protection.
- **Implication**: Read-only agents are not affected by write concurrency. If agent scope expands to write-enabled, application-level concurrency controls must be added.
- **Recommendation**: Prepare ETags or version headers on state-modifying endpoints before expanding agent scope.
- **Evidence**: `multi-tenancy/schema-isolation/standalone.xml` (TRANSACTION_READ_COMMITTED)

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits found. No `max_records_per_bulk_operation`, no `max_spend_per_session`, no per-agent operation caps. The Camunda engine does not natively enforce per-client operation limits.
- **Implication**: Read-only agents cannot trigger destructive actions. If scope expands to write-enabled, transaction limits must be implemented to prevent catastrophic agent errors.
- **Recommendation**: Plan transaction limit implementation (per-agent process start limits, per-agent variable modification limits) before write-enabled expansion.
- **Evidence**: All configuration files (no transaction limit config)

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: BPMN user tasks inherently implement a draft/pending pattern. The `TwitterDemoProcess.bpmn` has a "Review Tweet" user task that waits for human approval before publishing. The `example-invoice` has user task forms for invoice approval (`approve-invoice.html`, `review-invoice.html`). These patterns demonstrate human-in-the-loop approval workflows natively.
- **Implication**: The Camunda user task pattern maps well to HITL requirements. If agents are given write scope, user tasks can serve as human approval gates.
- **Recommendation**: Leverage Camunda's user task pattern for agent-initiated writes that require human approval.
- **Evidence**: `spring-boot-starter/example-twitter/src/main/resources/TwitterDemoProcess.bpmn` (user_task_review_tweet), `spring-boot-starter/example-invoice/src/main/resources/static/forms/approve-invoice.html`

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: BPMN process definitions inherently support configurable approval gates via user tasks and exclusive gateways. The `TwitterDemoProcess.bpmn` has an approval gateway ("Approved?") that routes to either "Publish on Twitter" or "Send rejection notification." Approval is per-process-definition, not per-operation-type configurable at runtime.
- **Implication**: For read-only scope, approval gates are informational. The BPMN model supports the pattern, but runtime configurability (per-agent, per-operation-type) would require additional implementation.
- **Recommendation**: Design configurable approval policies per operation type before write-enabled expansion.
- **Evidence**: `spring-boot-starter/example-twitter/src/main/resources/TwitterDemoProcess.bpmn` (gateway_approved)

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality scores, completeness metrics, or profiling reports found. No null rate monitoring, no duplicate detection logic, no data freshness SLAs. The examples use synthetic/demo data with no quality measurement.
- **Implication**: When agents consume real process data, data quality issues (incomplete variables, stale history records) could cause incorrect agent reasoning.
- **Recommendation**: Implement data quality monitoring before agent deployment, particularly for process variable completeness.
- **Evidence**: No evidence found — absence is itself a finding

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Field names in the codebase are generally semantically meaningful. Java classes use clear names: `ProcessDefinitionDto`, `ApprovalServiceBean`, `TweetContentDelegate`, `RejectionNotificationDelegate`. Process variable names in BPMN are readable: `approved`, `invoiceId`, `tweet`. The Camunda REST API uses semantic field names (`processDefinitionKey`, `businessKey`, `taskName`). No legacy abbreviations or opaque codes found.
- **Implication**: The semantic clarity of field names is favorable for LLM-based agent reasoning. Agents can interpret variable names without a data dictionary.
- **Recommendation**: Maintain the current naming conventions. Document any domain-specific abbreviations.
- **Evidence**: `multi-tenancy/schema-isolation/src/main/java/org/camunda/bpm/tutorial/multitenancy/ProcessDefinitionDto.java`, `spring-boot-starter/example-twitter/src/main/resources/TwitterDemoProcess.bpmn`

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No data catalog or metadata layer found. No AWS Glue Data Catalog, no Collibra, no DataHub, no data dictionaries, no schema documentation beyond the BPMN process definitions themselves. The BPMN files serve as partial metadata (process flow, variable names, task definitions) but are not a formal data catalog.
- **Implication**: Agent tool builders must reverse-engineer data semantics from BPMN definitions and source code. A data catalog would accelerate tool definition.
- **Recommendation**: Create a simple data dictionary documenting process variables, their types, and business meanings across all process definitions.
- **Evidence**: All `.bpmn` files (informal metadata), `bpmn-analysis.json`

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No business outcome metrics found. No `cloudwatch.put_metric_data` for business events, no custom dashboards, no KPI tracking. Camunda metrics are explicitly disabled. The `TwitterDemoProcess.bpmn` has KPI-related process extension properties (`KPI-Ratio`, `KPI-Cycle-Start`, `KPI-Cycle-End`) as metadata annotations, but these are not connected to any metrics collection system.
- **Implication**: No visibility into whether agent interactions with the process engine produce good business outcomes. When agents consume the system, business metrics become the primary feedback signal.
- **Recommendation**: Implement custom metrics for business outcomes (process completion rates, approval times, error rates) connected to the BPMN KPI annotations already present.
- **Evidence**: `spring-boot-starter/example-twitter/src/main/resources/TwitterDemoProcess.bpmn` (KPI properties), `spring-boot-starter/example-web/src/main/resources/application.yml` (metrics disabled)

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: REST API exposed via `camunda-bpm-spring-boot-starter-rest` at `/engine-rest`. Custom JAX-RS endpoints at `/approval-process`, `/store-order-items`, `/process-definition`. Camunda REST API is well-documented externally.
- **Gap**: Custom endpoints lack in-repository documentation.
- **Recommendation**: Document custom endpoints alongside the Camunda REST API surface.
- **Evidence**: `spring-boot-starter/example-web/pom.xml`, `quarkus-extension/datasource-example/src/main/java/.../ApprovalProcessService.java`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, GraphQL, or Smithy specs in repository. External Camunda REST API spec exists but is not co-located.
- **Gap**: No machine-readable spec in-repo. Agent tool generation requires manual authoring.
- **Recommendation**: Add `springdoc-openapi` to Spring Boot modules for auto-generated OpenAPI specs.
- **Evidence**: Repository-wide search — no spec files found

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: Custom endpoints return plain text errors. Camunda REST API has its own error format. No consistent error code/message/retryable structure.
- **Gap**: Agents cannot distinguish retriable from terminal errors in custom endpoints.
- **Recommendation**: Implement `@ControllerAdvice` / `ExceptionMapper` for structured JSON errors.
- **Evidence**: `quarkus-extension/datasource-example/.../ApprovalProcessService.java`, `multi-tenancy/schema-isolation/.../TenantInterceptor.java`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No idempotency keys or business key uniqueness constraints found.
- **Gap**: Write endpoints are non-idempotent. Informational for read-only scope.
- **Recommendation**: Address before write-enabled scope expansion.
- **Evidence**: `quarkus-extension/spin-plugin-example/.../StartProcessRestResource.java`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: JSON via Camunda REST API and most custom endpoints. One custom endpoint returns plain text.
- **Gap**: Minor inconsistency in response format.
- **Recommendation**: Standardize all endpoints to JSON.
- **Evidence**: `multi-tenancy/schema-isolation/.../ProcessDefinitionResource.java`, `quarkus-extension/datasource-example/.../ApprovalProcessService.java`

#### API-Q6: Asynchronous Operation Support
- **Severity**: RISK-QUALITY
- **Finding**: BPMN processes are long-running. Async continuation and external task patterns exist internally. No standardized polling/webhook API for external consumers.
- **Gap**: No external async pattern for agent consumption.
- **Recommendation**: Expose process status polling endpoint or webhook callbacks.
- **Evidence**: `servicetask/service-invocation-asynchronous/.../AsynchronousServiceTask.java`, `clients/java/order-handling/.../App.java`

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: BPMN signal/message events supported internally. No external event emission (webhooks, SNS, EventBridge).
- **Gap**: No external event emission mechanism.
- **Recommendation**: Implement execution listeners publishing to an event bus.
- **Evidence**: `startevent/message-start/src/main/resources/message_start_process.bpmn`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit documentation or headers found.
- **Gap**: No rate limit visibility for agents.
- **Recommendation**: Add rate limit headers when rate limiting is implemented (STATE-Q5).
- **Evidence**: All Java source files — no rate limit header code

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: No machine identity auth. Only hardcoded basic auth (`demo:demo`). `spring-boot-starter-security` included but unconfigured beyond defaults.
- **Gap**: No machine identity. Agents cannot authenticate with service-level identity.
- **Recommendation**: Implement OAuth2 client credentials or API key auth with principal attribution.
- **Evidence**: `spring-boot-starter/example-web/pom.xml`, `spring-boot-starter/example-web/src/main/resources/application.yml`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: Single shared credential with full access. Camunda authorization enabled in some modules but no agent-specific scoping.
- **Gap**: No least-privilege model. Agent would inherit full read/write access.
- **Recommendation**: Configure Camunda authorization service for agent-specific read-only roles.
- **Evidence**: `spring-boot-starter/example-invoice/src/main/resources/application.yaml`, `multi-tenancy/schema-isolation/standalone.xml`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization. TenantInterceptor filters by tenant, not by action type. Camunda supports granular auth but none configured.
- **Gap**: No read vs. write vs. delete distinction for agents.
- **Recommendation**: Leverage Camunda's Authorization resource for fine-grained per-action permissions.
- **Evidence**: `multi-tenancy/schema-isolation/.../TenantInterceptor.java`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: No JWT/OAuth2 identity propagation. TenantInterceptor uses query parameter for tenant — not secure. No agent-as-self vs. agent-on-behalf-of-user distinction.
- **Gap**: No identity propagation mechanism.
- **Recommendation**: Implement JWT-based identity propagation for production.
- **Evidence**: `multi-tenancy/schema-isolation/.../TenantInterceptor.java`

#### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: Credentials hardcoded across all config files (`demo:demo`, `camunda:camunda`, `sa:sa`). No Secrets Manager or Vault integration.
- **Gap**: All credentials in source. Expected for examples but blocks production agent deployment.
- **Recommendation**: Externalize to AWS Secrets Manager before production.
- **Evidence**: `spring-boot-starter/example-web/src/main/resources/application.yml`, `spring-boot-starter/example-invoice/src/main/resources/application.yaml`, `quarkus-extension/datasource-example/src/main/resources/application.properties`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No immutable audit logging. WildFly audit logger explicitly `enabled="false"`. Camunda history uses same mutable H2 database.
- **Gap**: No immutable audit trail for agent operations.
- **Recommendation**: Implement structured audit logging to immutable store (CloudWatch Logs, S3 Object Lock).
- **Evidence**: `multi-tenancy/schema-isolation/standalone.xml`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: No mechanism to suspend individual agent identity. Only shared hardcoded credentials exist.
- **Gap**: Cannot isolate a misbehaving agent without disrupting all consumers.
- **Recommendation**: Implement per-agent revocable identities (depends on AUTH-Q1).
- **Evidence**: `spring-boot-starter/example-web/src/main/resources/application.yml`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Camunda engine supports BPMN compensation natively. No compensation handlers in any of the 53 BPMN files. No saga patterns or undo endpoints.
- **Gap**: No compensation or rollback for multi-step workflows.
- **Recommendation**: Add BPMN compensation events to critical process steps.
- **Evidence**: All `.bpmn` files, `TwitterDemoProcess.bpmn`

#### STATE-Q2: Queryable Current State
- **Severity**: RISK-QUALITY
- **Finding**: Camunda REST API provides comprehensive state queries (process instances, tasks, variables, history). Custom `ProcessDefinitionResource` queries process definitions. Framework capability, not custom application code.
- **Gap**: No domain-specific state query abstraction.
- **Recommendation**: Create domain-specific query endpoints abstracting Camunda API.
- **Evidence**: `multi-tenancy/schema-isolation/.../ProcessDefinitionResource.java`

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Camunda uses internal optimistic locking. H2 supports TRANSACTION_READ_COMMITTED. No application-level ETags or version headers.
- **Gap**: No external concurrency controls. Informational for read-only scope.
- **Recommendation**: Prepare ETags/version headers before write-enabled expansion.
- **Evidence**: `multi-tenancy/schema-isolation/standalone.xml`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: No circuit breakers or application-level retry. Failed-job-retry-profile is internal engine retry only. External task client has timeout but no circuit breaker.
- **Gap**: No cascading failure protection.
- **Recommendation**: Add Resilience4j circuit breakers to external HTTP clients.
- **Evidence**: `clients/java/order-handling/.../App.java`, `process-engine-plugin/failed-job-retry-profile/`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No rate limiting at any layer. Camunda REST API exposed directly with no throttling.
- **Gap**: No protection against agent traffic storms.
- **Recommendation**: Deploy API Gateway with rate limiting.
- **Evidence**: `spring-boot-starter/example-web/pom.xml`, all config files

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits. Camunda does not natively enforce per-client limits.
- **Gap**: No blast radius controls. Informational for read-only scope.
- **Recommendation**: Plan transaction limits before write-enabled expansion.
- **Evidence**: All configuration files

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path. This service is P1 priority.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: BPMN user tasks implement draft/pending pattern natively. TwitterDemoProcess has "Review Tweet" user task. Invoice example has approval forms.
- **Gap**: Informational for read-only scope. User task pattern available for write scope.
- **Recommendation**: Leverage Camunda user tasks for HITL on write operations.
- **Evidence**: `spring-boot-starter/example-twitter/src/main/resources/TwitterDemoProcess.bpmn`, `spring-boot-starter/example-invoice/src/main/resources/static/forms/approve-invoice.html`

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: BPMN exclusive gateways support configurable approval. TwitterDemoProcess has "Approved?" gateway. Approval is per-process-definition, not runtime-configurable per operation type.
- **Gap**: Informational for read-only scope. Runtime per-agent configurability would require additional implementation.
- **Recommendation**: Design configurable approval policies before write-enabled expansion.
- **Evidence**: `spring-boot-starter/example-twitter/src/main/resources/TwitterDemoProcess.bpmn`

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: No dedicated sandbox/staging environment. Examples run locally with H2 in-memory databases. No Docker Compose, no seed data, no synthetic data generators.
- **Gap**: No production-equivalent staging for agent testing.
- **Recommendation**: Create Docker Compose staging environment with seed data.
- **Evidence**: All `application.yaml/yml` files, no `docker-compose.yml` found

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: No data classification, field-level tagging, or access controls. Process variables stored without classification metadata. Invoice module handles financial data unclassified.
- **Gap**: Sensitive data is neither classified nor tagged. No access controls for sensitive process variables.
- **Recommendation**: Inventory and classify all process variables. Implement field-level access controls.
- **Evidence**: `spring-boot-starter/example-invoice/src/main/resources/application.yaml`, all BPMN files

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No data residency requirements documented. H2 databases with no region config. No GDPR/LGPD references.
- **Gap**: No controls preventing cross-region data transmission to LLM endpoints.
- **Recommendation**: Conduct data residency assessment before agent deployment.
- **Evidence**: `spring-boot-starter/example-invoice/src/main/resources/application.yaml`, `quarkus-extension/datasource-example/src/main/resources/application.properties`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK-QUALITY
- **Finding**: Camunda REST API supports pagination. Custom `ProcessDefinitionResource` uses unbounded `.list()`. Custom Quarkus endpoints lack pagination.
- **Gap**: Custom endpoints lack pagination. Unbounded queries possible.
- **Recommendation**: Add pagination parameters to custom endpoints using `.listPage()`.
- **Evidence**: `multi-tenancy/schema-isolation/.../ProcessDefinitionResource.java`

#### DATA-Q4: System of Record Designations
- **Severity**: RISK-QUALITY
- **Finding**: No system-of-record designations. Each module operates independently with its own H2 database. No master data management.
- **Gap**: No authoritative system of record for any entity.
- **Recommendation**: Document system-of-record designations for process data.
- **Evidence**: All `application.yaml/yml` files, `pom.xml` (root)

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK-QUALITY
- **Finding**: Camunda records timestamps internally (history tables). No timezone normalization configured. No Cache-Control or freshness headers on REST responses.
- **Gap**: REST responses do not signal data freshness or consistency.
- **Recommendation**: Add Cache-Control/Last-Modified headers to custom endpoints.
- **Evidence**: All config files

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: No PII redaction. Standard SLF4J/Logback with no filtering. Process variables logged as-is.
- **Gap**: PII flows into logs without redaction.
- **Recommendation**: Implement PII-aware Logback filter for process variable masking.
- **Evidence**: All config files, all Java source files

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality scores or completeness metrics. Examples use synthetic demo data.
- **Gap**: No data quality monitoring.
- **Recommendation**: Implement data quality monitoring before agent deployment.
- **Evidence**: No evidence found — absence is itself a finding

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: No schema versioning, contract testing, or breaking change detection. Camunda REST API version managed externally (7.24.0). No Pact tests, no OpenAPI diff tools.
- **Gap**: API changes could break agent tool bindings silently.
- **Recommendation**: Add contract tests and OpenAPI spec diffing to CI pipeline.
- **Evidence**: `.github/workflows/main.yml`, `.github/workflows/bump-versions.yml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Field names are semantically meaningful. Java classes use clear names (`ProcessDefinitionDto`, `ApprovalServiceBean`). BPMN variables are readable (`approved`, `invoiceId`). No legacy abbreviations.
- **Gap**: None — field naming is favorable for LLM reasoning.
- **Recommendation**: Maintain current naming conventions.
- **Evidence**: `multi-tenancy/schema-isolation/.../ProcessDefinitionDto.java`, `TwitterDemoProcess.bpmn`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No data catalog. BPMN files serve as informal metadata but not a formal catalog. No Glue Data Catalog, DataHub, or data dictionaries.
- **Gap**: Agent tool builders must reverse-engineer data semantics.
- **Recommendation**: Create a data dictionary for process variables across all definitions.
- **Evidence**: All `.bpmn` files, `bpmn-analysis.json`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: No distributed tracing or structured logging. No OpenTelemetry, X-Ray, or traceparent headers. SLF4J with unstructured text logging. Spring Boot Actuator present for health only.
- **Gap**: Agent-initiated requests cannot be traced. No correlation IDs.
- **Recommendation**: Add Micrometer Tracing with OpenTelemetry. Switch to structured JSON logging.
- **Evidence**: `spring-boot-starter/example-web/pom.xml`, all config files

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: No alerting thresholds. No CloudWatch alarms, PagerDuty, or SLO alerting. Camunda metrics explicitly disabled.
- **Gap**: No alerting for system degradation.
- **Recommendation**: Enable Camunda metrics, configure Micrometer export, set alerting thresholds.
- **Evidence**: `spring-boot-starter/example-web/src/main/resources/application.yml`, `spring-boot-starter/example-simple/src/main/resources/application.yaml`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No business outcome metrics. KPI annotations in BPMN (`KPI-Ratio`, `KPI-Cycle-Start`) but not connected to metrics collection.
- **Gap**: No visibility into agent interaction outcomes.
- **Recommendation**: Implement custom metrics connected to BPMN KPI annotations.
- **Evidence**: `spring-boot-starter/example-twitter/src/main/resources/TwitterDemoProcess.bpmn`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK-QUALITY
- **Finding**: No IaC found. No Terraform, CloudFormation, CDK, Helm, or Kustomize. Agent-facing surface not defined as code.
- **Gap**: Entire infrastructure undefined as code.
- **Recommendation**: Define deployment infrastructure in Terraform or CDK before production.
- **Evidence**: Repository-wide search — no IaC files found

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: Two GitHub Actions workflows for version bumping only. No build/test/deploy pipeline. No contract tests.
- **Gap**: No CI/CD for testing or deployment. No API breaking change detection.
- **Recommendation**: Create CI workflow with `mvn verify` and API contract validation.
- **Evidence**: `.github/workflows/main.yml`, `.github/workflows/bump-versions.yml`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: No rollback capability. No blue/green, CodeDeploy, Helm rollback, or feature flags. Git tags exist for version pinning.
- **Gap**: No deployment rollback mechanism.
- **Recommendation**: Define deployment strategy with rollback as part of IaC (ENG-Q1).
- **Evidence**: `README.md` (version tags)

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: 32 test files. CamundaBpmRestTest validates REST API returns process definitions. Most modules have 1–2 tests for happy path. No error response or edge case testing.
- **Gap**: Insufficient test coverage for agent-facing APIs.
- **Recommendation**: Expand tests to cover error scenarios, pagination, and concurrent access.
- **Evidence**: `spring-boot-starter/example-web/src/test/java/.../CamundaBpmRestTest.java`, `testing/assert/`, `testing/junit5/`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: RISK-QUALITY
- **Finding**: No encryption at rest. H2 file and in-memory databases with no encryption. No KMS keys.
- **Gap**: Process data unencrypted at rest.
- **Recommendation**: Migrate to managed database (RDS/Aurora) with KMS encryption for production.
- **Evidence**: `spring-boot-starter/example-invoice/src/main/resources/application.yaml`, `multi-tenancy/schema-isolation/standalone.xml`

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `spring-boot-starter/example-web/src/main/java/org/camunda/bpm/spring/boot/example/web/RestApplication.java` | API-Q1 |
| `multi-tenancy/schema-isolation/src/main/java/org/camunda/bpm/tutorial/multitenancy/ProcessDefinitionResource.java` | API-Q1, API-Q3, API-Q5, STATE-Q2, DATA-Q3 |
| `multi-tenancy/schema-isolation/src/main/java/org/camunda/bpm/tutorial/multitenancy/ProcessDefinitionDto.java` | DISC-Q2 |
| `multi-tenancy/schema-isolation/src/main/java/org/camunda/bpm/tutorial/multitenancy/TenantInterceptor.java` | API-Q3, AUTH-Q3, AUTH-Q4 |
| `quarkus-extension/datasource-example/src/main/java/org/camunda/bpm/quarkus/example/datasource/rest/ApprovalProcessService.java` | API-Q1, API-Q3, API-Q5 |
| `quarkus-extension/spin-plugin-example/src/main/java/org/camunda/bpm/quarkus/example/rest/StartProcessRestResource.java` | API-Q4 |
| `deployment/embedded-spring-rest/src/main/java/org/camunda/bpm/example/loanapproval/rest/RestProcessEngineProvider.java` | API-Q1 |
| `servicetask/service-invocation-asynchronous/src/main/java/org/camunda/quickstart/servicetask/invocation/AsynchronousServiceTask.java` | API-Q6, STATE-Q1 |
| `clients/java/order-handling/src/main/java/org/camunda/bpm/App.java` | API-Q6, STATE-Q4 |
| `spring-boot-starter/external-task-client/loan-granting-spring-boot-webapp/src/main/java/org/camunda/bpm/spring/boot/example/HandlerConfiguration.java` | API-Q6 |
| `process-engine-plugin/failed-job-retry-profile/src/main/java/org/camunda/bpm/example/FailedJobRetryProfilePlugin.java` | STATE-Q4 |
| `process-engine-plugin/command-interceptor-blocking/src/main/java/org/camunda/bpm/example/engine/BlockingCommandInterceptor.java` | STATE-Q4 |
| `spring-boot-starter/example-web/src/test/java/org/camunda/bpm/spring/boot/example/web/CamundaBpmRestTest.java` | STATE-Q2, ENG-Q4 |
| `spring-boot-starter/example-web/src/test/java/org/camunda/bpm/spring/boot/example/web/CamundaBpmActuatorTest.java` | ENG-Q4 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/main.yml` | DISC-Q1, ENG-Q2 |
| `.github/workflows/bump-versions.yml` | DISC-Q1, ENG-Q2 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `pom.xml` (root) | DISC-Q1, DATA-Q4 |
| `spring-boot-starter/example-web/pom.xml` | API-Q1, AUTH-Q1, AUTH-Q6, OBS-Q1, STATE-Q5 |
| `spring-boot-starter/example-invoice/pom.xml` | API-Q1 |
| `testing/assert/job-announcement-publication-process/pom.xml` | ENG-Q4 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `spring-boot-starter/example-web/src/main/resources/application.yml` | AUTH-Q1, AUTH-Q2, AUTH-Q5, AUTH-Q7, OBS-Q2 |
| `spring-boot-starter/example-invoice/src/main/resources/application.yaml` | AUTH-Q2, AUTH-Q5, DATA-Q1, DATA-Q2, ENG-Q5 |
| `spring-boot-starter/example-twitter/src/main/resources/application.yaml` | AUTH-Q1 |
| `spring-boot-starter/example-simple/src/main/resources/application.yaml` | OBS-Q2 |
| `spring-boot-starter/example-webapp/src/main/resources/application.yaml` | AUTH-Q1 |
| `spring-boot-starter/example-webapp-ee/src/main/resources/application.yaml` | AUTH-Q1 |
| `spring-boot-starter/external-task-client/loan-granting-spring-boot-webapp/src/main/resources/application.yml` | API-Q6 |
| `quarkus-extension/datasource-example/src/main/resources/application.properties` | AUTH-Q5, DATA-Q2, ENG-Q5 |
| `quarkus-extension/spin-plugin-example/src/main/resources/application.properties` | ENG-Q5 |
| `multi-tenancy/schema-isolation/standalone.xml` | AUTH-Q2, AUTH-Q6, STATE-Q3, ENG-Q5 |
| `authentication/basic/README.md` | AUTH-Q1 |
| `README.md` | ENG-Q3 |

### BPMN Process Definitions
| File | Questions Referenced |
|------|---------------------|
| `spring-boot-starter/example-twitter/src/main/resources/TwitterDemoProcess.bpmn` | API-Q7, STATE-Q1, HITL-Q1, HITL-Q2, OBS-Q3, DISC-Q2 |
| `startevent/message-start/src/main/resources/message_start_process.bpmn` | API-Q7 |
| `servicetask/service-invocation-asynchronous/src/main/resources/asynchronousServiceInvocation.bpmn` | API-Q6, API-Q7 |
| `spring-boot-starter/example-invoice/src/main/resources/static/forms/approve-invoice.html` | HITL-Q1, DATA-Q1 |
| All 53 `.bpmn` files | STATE-Q1, DATA-Q1, DISC-Q3 |
