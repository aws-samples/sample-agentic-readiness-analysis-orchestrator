# Agentic Readiness Analysis Report

**Target**: conductor (monorepo)
**Date**: 2026-04-29
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**Repository Type**: monorepo
**Service Archetype**: orchestrator (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: java, workflow, orchestration
**Context**: Workflow orchestration engine originally from Netflix.

**Archetype Justification**: Conductor is a workflow orchestration engine that coordinates multi-service/multi-task workflows via HTTP tasks, Kafka, SQS, and AMQP. It manages workflow execution state (not individual business entity CRUD) with high fan-out patterns including dynamic forks, sub-workflows, and distributed task execution — matching the orchestrator archetype.

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 2 | **RISK-SAFETY**: 8 | **RISK-QUALITY**: 16 | **INFOs**: 16

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days. The 2 BLOCKERs (AUTH-Q1: machine identity authentication, DATA-Q1: sensitive data classification) must be resolved before any agent can safely interact with Conductor's APIs. The 8 RISK-SAFETY findings indicate significant gaps in authorization, audit logging, resilience, and data privacy controls that must be addressed for safe agent operation.

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 2 |
| RISK-SAFETY | 8 |
| RISK-QUALITY | 16 |
| INFO | 16 |
| N/A | 0 |
| Not Evaluated (extended) | 1 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 18
**Extended Questions Not Triggered**: 1
**Questions N/A (repo_type: monorepo)**: 0
**Service Archetype**: orchestrator (auto-detected)

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication — BLOCKER

- **Severity**: BLOCKER
- **Finding**: No authentication middleware, security filter chain, or Spring Security dependency exists in the Conductor codebase. The REST API is open and unauthenticated by default. No OAuth2 client credentials flow, no API key authentication, no mTLS configuration, and no Cognito/Bedrock AgentCore Identity integration found. The `WorkflowContext` class (`core/src/main/java/.../WorkflowContext.java`) stores `clientApp` and `userName` as thread-local context but these are not populated from HTTP request headers or authentication tokens — they default to empty strings.
- **Gap**: The application has zero authentication controls. Any network-reachable client can call any endpoint. There is no mechanism to identify which agent (or any caller) made a request. The `spring-boot-starter-security` dependency is absent from `server/build.gradle`.
- **Remediation**:
  - **Immediate**: Add `spring-boot-starter-security` and configure a `SecurityFilterChain` with OAuth2 resource server or API key authentication. At minimum, require a `Bearer` token or `X-API-Key` header on all endpoints.
  - **Target State**: Every API request is authenticated with a machine identity (OAuth2 client credentials or API key with principal attribution). The authenticated principal is available in `WorkflowContext` for audit logging.
  - **Estimated Effort**: Medium (2–4 weeks for Spring Security integration with OAuth2/API key support)
  - **Dependencies**: AUTH-Q6 (audit logging requires authenticated principal), AUTH-Q2 (scoped permissions require authentication first)
- **Evidence**: `server/build.gradle` (no spring-security dependency), `core/src/main/java/com/netflix/conductor/core/WorkflowContext.java` (empty context), `rest/src/main/java/com/netflix/conductor/rest/controllers/WorkflowResource.java` (no auth annotations)

### DATA-Q1: Sensitive Data Classification — BLOCKER

- **Severity**: BLOCKER
- **Finding**: No data classification tags, field-level encryption, or data sensitivity labeling exists in the codebase. Workflow and task input/output payloads are arbitrary JSON that may contain sensitive business data (PII, financial records, credentials). The `maskedFields` property in `WorkflowDef` (see `schemas/WorkflowDef.json`) provides a field masking capability for workflow outputs, but this is opt-in per workflow definition and does not constitute systematic data classification.
- **Gap**: There is no systematic classification of what data is sensitive. An agent reading workflow payloads could inadvertently access PII, credentials, or regulated data with no controls preventing retrieval. No Macie integration, no field-level access controls, no data classification policies.
- **Remediation**:
  - **Immediate**: Audit all workflow definitions currently registered to identify payloads containing PII, credentials, or regulated data. Enforce `maskedFields` on all workflow definitions that handle sensitive data.
  - **Target State**: All sensitive fields in workflow/task payloads are classified and tagged. Field-level access controls prevent agents from retrieving classified data without explicit authorization. A data classification policy governs what data flows through Conductor.
  - **Estimated Effort**: High (4–8 weeks — requires data audit, classification framework, and enforcement mechanism)
  - **Dependencies**: AUTH-Q1 (authentication must exist before field-level access controls can be enforced)
- **Evidence**: `schemas/WorkflowDef.json` (`maskedFields` property exists but is opt-in), `server/src/main/resources/application.properties` (no data classification configuration), absence of any Macie/classification tooling

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No authorization model exists in the codebase. All REST endpoints are accessible without any permission checks. No IAM policies, RBAC roles, or ABAC attributes are defined. There are no wildcard vs. scoped permission distinctions because there are no permissions at all.
- **Gap**: An agent identity (once authentication is implemented) cannot be granted read-only access to specific resources. Every authenticated caller inherits the same unrestricted surface.
- **Compensating Controls**:
  - Deploy an API Gateway (e.g., AWS API Gateway) in front of Conductor with resource policies that restrict agent access to specific HTTP methods and paths (e.g., allow GET only).
  - Use network-level isolation to limit which agents can reach specific Conductor endpoints.
- **Remediation Timeline**: 30–60 days (after AUTH-Q1 authentication is implemented)
- **Recommendation**: Implement RBAC with predefined roles (e.g., `workflow-reader`, `workflow-admin`, `task-worker`) using Spring Security method-level annotations (`@PreAuthorize`).
- **Evidence**: `rest/src/main/java/com/netflix/conductor/rest/controllers/WorkflowResource.java` (no auth annotations), `server/build.gradle` (no spring-security)

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization exists. All endpoints (GET, POST, PUT, DELETE) are equally accessible. An agent that should only read workflows can also terminate, pause, restart, or delete them. No `canRead`/`canWrite`/`canDelete` checks exist in any controller.
- **Gap**: Cannot enforce read-only access for an agent at the application level. The API exposes destructive operations (DELETE /{workflowId}, POST /{workflowId}/terminate) alongside read operations with no differentiation.
- **Compensating Controls**:
  - Configure API Gateway to allow only GET methods for agent-scoped API keys, blocking POST/PUT/DELETE.
  - Use a reverse proxy with method-based access control lists.
- **Remediation Timeline**: 30–60 days (implement alongside AUTH-Q2)
- **Recommendation**: Add Spring Security method-level authorization annotations to controllers, separating read operations from write/admin operations.
- **Evidence**: `rest/src/main/java/com/netflix/conductor/rest/controllers/WorkflowResource.java` (DELETE, POST terminate endpoints accessible), `rest/src/main/java/com/netflix/conductor/rest/controllers/MetadataResource.java` (POST/PUT/DELETE for definitions)

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No immutable audit logging is configured. No CloudTrail integration, no S3 bucket with object lock for logs, no CloudWatch log retention policies with immutability. Logging uses Log4j with `PatternLayout` to console (`docker/server/config/log4j.properties`). Application-level logs do not record the authenticated principal (because there is none — see AUTH-Q1).
- **Gap**: No tamper-evident audit trail exists. Cannot determine which caller performed any operation. Even if authentication were added, there is no mechanism to produce immutable, tamper-evident logs.
- **Compensating Controls**:
  - Route Conductor container logs to a centralized log management system (CloudWatch Logs, Splunk) with retention policies and write-once storage.
  - Deploy an API Gateway with access logging enabled, forwarding logs to an immutable store.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Enable structured JSON logging with caller identity fields. Ship logs to CloudWatch Logs with log group retention and resource policies preventing deletion.
- **Evidence**: `docker/server/config/log4j.properties` (PatternLayout, no structured logging), `server/src/main/resources/application.properties` (no audit config)

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No mechanism exists to suspend or revoke individual agent identities. There are no API key management endpoints, no IAM role deactivation procedures, no service account disable mechanisms, and no Cognito user pool integration. Since there is no authentication (AUTH-Q1), there is nothing to suspend.
- **Gap**: If an agent were to exhibit anomalous behavior, there is no way to revoke its access without shutting down the entire Conductor instance or reconfiguring network rules.
- **Compensating Controls**:
  - Use API Gateway API key management — individual keys can be disabled without affecting other consumers.
  - Implement IP-based allow/deny lists at the network layer for rapid agent isolation.
- **Remediation Timeline**: 30–60 days (implement alongside AUTH-Q1)
- **Recommendation**: When implementing authentication (AUTH-Q1), choose a mechanism that supports individual identity revocation (e.g., API Gateway API keys, Cognito app clients).
- **Evidence**: `server/build.gradle` (no security dependencies), absence of any identity management endpoints in controllers

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No circuit breaker library (Resilience4j, Hystrix) is present in the dependency tree. The `http-task` module makes outbound HTTP calls to external services but has only timeout configuration — no circuit breaker wrapping. `spring-retry` is included as a dependency but is not configured as a circuit breaker pattern. The only retry reference found is in `DefaultEventProcessor.java`, which is for event processing, not external service calls.
- **Gap**: When an agent calls Conductor, which in turn calls external services via HTTP tasks, a failing external dependency will cascade failures back through Conductor to the agent. No circuit breaker prevents cascading failure loops.
- **Compensating Controls**:
  - Implement circuit breakers at the infrastructure layer (e.g., service mesh with Istio circuit breaking).
  - Configure aggressive timeouts on HTTP tasks to limit blast radius of downstream failures.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add Resilience4j to the `http-task` module and wrap outbound HTTP calls with circuit breaker, retry, and timeout decorators.
- **Evidence**: `server/build.gradle` (spring-retry present but no circuit breaker library), `dependencies.gradle` (no Resilience4j/Hystrix), `core/src/main/java/com/netflix/conductor/core/events/DefaultEventProcessor.java` (only retry usage found)

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Task-level rate limiting exists via `RedisRateLimitingDAO` using Redis sorted sets, configurable per task definition through `rateLimitPerFrequency` and `rateLimitFrequencyInSeconds` fields in `TaskDef`. However, there is no API-layer rate limiting. No API Gateway throttling configuration, no WAF rate rules, no application-level rate limiting middleware on REST endpoints. Any client can call Conductor's REST API at unlimited speed.
- **Gap**: A runaway agent loop can overwhelm Conductor's REST API at machine speed. Task-level rate limiting only controls task execution frequency, not API call frequency. There are no `X-RateLimit-Remaining` or `Retry-After` headers in responses.
- **Compensating Controls**:
  - Deploy an API Gateway (AWS API Gateway with usage plans) or WAF with rate limiting rules in front of Conductor.
  - Use reverse proxy (nginx) rate limiting at the container level.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add API Gateway with usage plans and throttling configuration. Alternatively, add Spring Boot rate limiting middleware (e.g., bucket4j-spring-boot-starter) to REST controllers.
- **Evidence**: `redis-persistence/src/main/java/.../RedisRateLimitingDAO.java` (task-level rate limiting only), `schemas/TaskDef.json` (rateLimitPerFrequency, rateLimitFrequencyInSeconds), absence of API-layer rate limiting in controllers or configuration

#### DATA-Q2: Data Residency and Sovereignty ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No explicit data residency requirements or data sovereignty controls exist in the codebase. The AI provider configurations in `application.properties` reference region settings (e.g., `conductor.ai.bedrock.region=${AWS_REGION:us-east-1}`) but these are for outbound AI API calls, not for controlling where workflow data is stored or processed. Database and Redis connections do not specify region constraints.
- **Gap**: Workflow payloads may contain regulated data subject to GDPR, LGPD, or other residency requirements. An agent reading this data could transmit it to an LLM endpoint in a different jurisdiction with no controls preventing this.
- **Compensating Controls**:
  - Deploy Conductor in a region-locked environment where all data storage and processing occurs within a single compliance boundary.
  - Implement data residency policies at the agent orchestration layer, preventing agents from sending Conductor data to cross-region LLM endpoints.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document data residency requirements for all workflow types. Configure deployment infrastructure to enforce single-region data processing.
- **Evidence**: `server/src/main/resources/application.properties` (AI provider region configs but no data residency controls), `docker/server/config/config-postgres.properties` (no region constraints on database)

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No PII redaction exists in the logging pipeline. Log4j is configured with `PatternLayout` (`%-4r [%t] %-5p %c %x - %m%n`) which outputs full exception messages and stack traces. The `ApplicationExceptionMapper` logs the full exception with `LOGGER.error("Error {} url: '{}'", exception.getClass().getSimpleName(), request.getRequestURI(), exception)` — request URIs may contain workflow IDs or correlation IDs. The `RedisRateLimitingDAO` logs full task details. The `maskedFields` feature in `WorkflowDef` masks fields in workflow output but does NOT mask data in application logs.
- **Gap**: PII in workflow/task payloads can leak into application logs, error messages, and observability data. Agent-initiated requests processing customer data will log that data without redaction.
- **Compensating Controls**:
  - Configure log shipping with PII scrubbing filters before logs reach persistent storage.
  - Restrict log access to authorized personnel only.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement a Log4j filter or custom `PatternLayout` that redacts known PII patterns (email, phone, SSN, credit card). Extend the `maskedFields` concept to the logging layer.
- **Evidence**: `docker/server/config/log4j.properties` (PatternLayout with no filtering), `rest/src/main/java/.../ApplicationExceptionMapper.java` (logs full exceptions), `redis-persistence/src/main/java/.../RedisRateLimitingDAO.java` (logs task details)

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No standalone OpenAPI/Swagger YAML/JSON specification file exists in the repository. However, the `springdoc-openapi-starter-webmvc-ui` dependency (version 2.1.0) is configured in `server/build.gradle`, which auto-generates an OpenAPI spec at `/api-docs` at runtime. All REST controllers use `@Operation` annotations from `io.swagger.v3.oas.annotations`. Additionally, gRPC service definitions exist in `grpc/src/main/proto/` (workflow_service.proto, task_service.proto, metadata_service.proto, event_service.proto) and JSON Schema files exist in `schemas/` (WorkflowDef.json, TaskDef.json, Workflow.json, Task.json).
- **Gap**: The OpenAPI spec is runtime-generated only — it is not committed to the repository as a static artifact. This means agents or tooling cannot reference it without a running Conductor instance. No validation ensures the spec stays current with implementation.
- **Compensating Controls**:
  - Export the runtime-generated OpenAPI spec and commit it to the repository as a build artifact.
  - Use the protobuf definitions and JSON schemas as alternative machine-readable specs for tool generation.
- **Remediation Timeline**: 7–14 days
- **Recommendation**: Add a CI step that starts Conductor, exports the `/api-docs` endpoint to `openapi.json`, and commits or validates it as part of the build pipeline.
- **Evidence**: `server/build.gradle` (springdoc-openapi dependency), `grpc/src/main/proto/grpc/workflow_service.proto`, `schemas/WorkflowDef.json`, `schemas/TaskDef.json`

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Conductor implements structured error responses via the `ErrorResponse` class with fields: `status` (int), `code` (String), `message` (String), `instance` (String), `retryable` (boolean), `validationErrors` (List), and `metadata` (Map). The `ApplicationExceptionMapper` maps exceptions to appropriate HTTP status codes and sets `retryable=true` for `TransientException` instances. A separate `ValidationExceptionMapper` handles constraint violations.
- **Gap**: The `code` field is not consistently populated — the `ApplicationExceptionMapper` sets `status` and `message` but does not set `code`. The `retryable` flag is only `true` for `TransientException`; other retriable scenarios (e.g., rate limiting, temporary unavailability) are not distinguished.
- **Compensating Controls**:
  - Agents can use HTTP status codes (429, 503) as retriable signals in addition to the `retryable` field.
  - The `instance` field provides server identification for debugging.
- **Remediation Timeline**: 7–14 days
- **Recommendation**: Populate the `code` field consistently across all exception types. Add error codes for common scenarios (e.g., `RATE_LIMITED`, `WORKFLOW_NOT_FOUND`, `CONFLICT`).
- **Evidence**: `common/src/main/java/com/netflix/conductor/common/validation/ErrorResponse.java`, `rest/src/main/java/.../ApplicationExceptionMapper.java`

#### AUTH-Q4: Identity Propagation and Delegation — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The `WorkflowContext` class stores `clientApp` and `userName` as thread-local context, providing a framework for identity propagation. However, these fields are not populated from HTTP request headers or authentication tokens — they default to empty strings. No JWT parsing middleware, no OAuth2 on-behalf-of flows, no token exchange patterns exist. There is no distinction between agent-as-self and agent-on-behalf-of-user.
- **Gap**: The system cannot distinguish between an agent acting under its own identity vs. acting on behalf of a specific human user. All internal service calls are trusted equally.
- **Compensating Controls**:
  - Implement identity context at the API Gateway level, injecting caller identity headers that Conductor can read into `WorkflowContext`.
- **Remediation Timeline**: 30–60 days (implement alongside AUTH-Q1)
- **Recommendation**: Extend `WorkflowContext` to parse identity from HTTP headers (e.g., `Authorization Bearer`, `X-Agent-Id`, `X-On-Behalf-Of`) and propagate it through workflow execution.
- **Evidence**: `core/src/main/java/com/netflix/conductor/core/WorkflowContext.java` (empty defaults)

#### AUTH-Q5: Credential Management — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Credentials are managed through environment variables for AI provider API keys (`${OPENAI_API_KEY:}`, `${ANTHROPIC_API_KEY:}`, etc. in `application.properties`). The Postgres configuration in `config-postgres.properties` contains a hardcoded password: `spring.datasource.password=conductor`. The Redis configuration does not use authentication. No AWS Secrets Manager, HashiCorp Vault, or other secrets management integration is present.
- **Gap**: Database credentials are hardcoded in configuration files committed to the repository. While AI provider keys use environment variables (better), there is no secrets rotation mechanism. A prompt injection attack or agent bug could potentially leak credentials from configuration.
- **Compensating Controls**:
  - Override hardcoded credentials with environment variables at deployment time.
  - Use container orchestration secrets (Kubernetes Secrets, ECS secrets) to inject credentials.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Remove hardcoded credentials from configuration files. Integrate AWS Secrets Manager or HashiCorp Vault for all credential management with automatic rotation.
- **Evidence**: `docker/server/config/config-postgres.properties` (`spring.datasource.password=conductor`), `server/src/main/resources/application.properties` (AI keys via env vars)

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: `WorkflowDef` includes a `version` field for workflow definition versioning. gRPC protobuf definitions use package-level versioning. JSON Schema files exist in `schemas/` with `$id` URIs (e.g., `https://conductoross.org/schemas/WorkflowDef.json`). However, REST API endpoints use no URL versioning (`/v1/`, `/v2/`) and no `Accept-Version` headers. No breaking change detection exists in CI — no Pact consumer-driven contract tests, no OpenAPI diff tools, no `buf breaking` for protobuf.
- **Gap**: Agent tool bindings can break silently when API changes are deployed. There is no automated mechanism to detect breaking changes before production.
- **Compensating Controls**:
  - Use the gRPC protobuf definitions as the stable contract surface (protobuf has built-in backward compatibility rules).
  - Monitor the runtime-generated OpenAPI spec for changes manually.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add API contract testing to the CI pipeline. Use `openapi-diff` or `oasdiff` to detect breaking changes. Consider adding URL versioning to REST endpoints.
- **Evidence**: `schemas/WorkflowDef.json` (version field), `grpc/src/main/proto/grpc/workflow_service.proto` (package versioning), `.github/workflows/ci.yml` (no contract testing steps)

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Logging uses Log4j with `PatternLayout` (`%-4r [%t] %-5p %c %x - %m%n`) — not JSON structured logging. No OpenTelemetry SDK, no X-Ray instrumentation, no `traceparent` header propagation found in dependencies or code. No `request_id` or `correlation_id` field appears in log output patterns. Micrometer is present for metrics but not for distributed tracing.
- **Gap**: Agent-initiated requests cannot be traced through Conductor's internal processing. When a request fails, there is no trace ID linking the agent's call to Conductor's internal logs.
- **Compensating Controls**:
  - Use Conductor's `correlationId` (available on workflows and tasks) as a partial tracing mechanism — agents can pass a correlation ID and search logs by it.
  - Deploy a service mesh with automatic trace injection.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Switch to JSON structured logging (Log4j JSON Layout). Add OpenTelemetry or X-Ray instrumentation. Propagate `traceparent` headers through HTTP task calls.
- **Evidence**: `docker/server/config/log4j.properties` (PatternLayout), `dependencies.gradle` (no OpenTelemetry/X-Ray), `server/build.gradle` (no tracing dependencies)

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Prometheus metrics are enabled (`conductor.metrics-prometheus.enabled=true`) with extensive metric recording via `Monitors.java` — including counters for errors, timers for workflow execution, gauges for queue depths and running workflows. Multiple metrics registry backends are supported (Prometheus, Datadog, CloudWatch, etc.). However, no alerting thresholds are configured in the codebase — no CloudWatch alarms, no Prometheus alerting rules, no PagerDuty/OpsGenie integration.
- **Gap**: Target system degradation is not automatically detected. When agents start experiencing elevated error rates or latency, no alert is triggered.
- **Compensating Controls**:
  - Configure Prometheus alerting rules externally (in a Prometheus server or Grafana) based on Conductor's exported metrics.
  - Use CloudWatch metric alarms if metrics are shipped to CloudWatch.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Define Prometheus alerting rules for key metrics: `workflow_server_error` rate, `workflow_execution` latency p99, `task_queue_depth` thresholds. Integrate with PagerDuty or OpsGenie.
- **Evidence**: `server/src/main/resources/application.properties` (Prometheus enabled), `core/src/main/java/com/netflix/conductor/metrics/Monitors.java` (extensive metrics), absence of alerting configuration

#### ENG-Q1: Infrastructure Governance — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No Terraform, CloudFormation, or CDK infrastructure-as-code exists in the repository. Docker-compose files (`docker/docker-compose.yaml` and variants) define local development and testing environments but do not constitute production infrastructure governance. No drift detection configuration (AWS Config rules) exists. No peer review requirements specific to infrastructure changes are configured.
- **Gap**: The infrastructure exposing Conductor to agents — API gateways, IAM roles, secrets, network configurations — is not defined as code. Changes to production infrastructure are not subject to automated plan review or drift detection.
- **Compensating Controls**:
  - Maintain IaC in a separate infrastructure repository (common for open-source applications that are deployed separately).
  - Use deployment-specific IaC (Helm charts, Kubernetes manifests) created by the operations team.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Create IaC for the production deployment surface (API Gateway, IAM roles, KMS keys, networking). Use Terraform or CDK with PR-based review workflows.
- **Evidence**: Absence of `.tf`, `.cfn.yaml`, `cdk.json` files in the repository. `docker/docker-compose.yaml` (local dev only)

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: A CI pipeline exists (`.github/workflows/ci.yml`) that runs `./gradlew build` (compilation + unit tests), test-harness integration tests in a separate job, and Cypress E2E tests for the UI. However, no API contract testing exists — no Pact consumer-driven tests, no OpenAPI spec validation in the build, no schema comparison tools, no breaking change detection.
- **Gap**: API changes that break agent tool bindings are not caught in the pipeline. An API change could deploy and break all agents consuming the API.
- **Compensating Controls**:
  - The extensive test suite (391 test files) provides some coverage of API behavior, though not specifically contract testing.
  - Manually validate OpenAPI spec changes before releases.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add API contract testing to CI. Export the runtime OpenAPI spec and compare against a committed baseline using `oasdiff`. Add Pact tests for critical consumer contracts.
- **Evidence**: `.github/workflows/ci.yml` (build + test but no contract tests), absence of Pact or OpenAPI diff configuration

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The publish workflow (`.github/workflows/publish.yml`) builds and pushes Docker images to Docker Hub with version tags (e.g., `conductoross/conductor:v1.0.0`) and a `latest` tag. However, no blue/green deployment, no CodeDeploy rollback triggers, no canary deployment, no feature flags, and no traffic shifting configuration exist in the repository.
- **Gap**: If a deployment breaks agent-facing APIs, rollback requires manually redeploying the previous Docker image version. No automated rollback mechanism exists.
- **Compensating Controls**:
  - Docker image versioning allows manual rollback to a previous version (`docker pull conductoross/conductor:<previous-version>`).
  - Implement deployment rollback at the orchestration layer (Kubernetes rolling update with rollback, ECS service rollback).
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement deployment automation with rollback triggers based on health check failures. Use Kubernetes rolling deployments with automatic rollback or ECS deployment circuit breakers.
- **Evidence**: `.github/workflows/publish.yml` (versioned Docker images), `docker/docker-compose.yaml` (no deployment strategy)

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: 391 test files exist across the repository. JaCoCo code coverage is configured with aggregated reporting. The `test-harness` module runs integration tests with real backends (Redis, Elasticsearch via Testcontainers). Cypress E2E tests cover the UI. However, no explicit API contract tests exist for the REST API — no Postman/Newman collections, no REST Assured API tests, no consumer-driven contract tests.
- **Gap**: While integration tests exercise API behavior indirectly, there are no tests specifically validating the API contract (input handling, output format, error responses, edge cases) that agents will rely on.
- **Compensating Controls**:
  - The test-harness integration tests provide substantial coverage of API behavior through service-layer testing.
  - JaCoCo coverage reporting tracks overall test coverage.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add dedicated REST API tests using REST Assured or MockMvc that validate request/response contracts for all agent-facing endpoints. Include error scenario testing.
- **Evidence**: `.github/workflows/ci.yml` (build + test jobs), `build.gradle` (JaCoCo configuration), `test-harness/` (integration tests)

#### ENG-Q5: Encryption at Rest — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No encryption at rest configuration exists. The default SQLite database URL (`jdbc:sqlite:c123.db`) has no encryption. The Postgres configuration uses plain JDBC (`jdbc:postgresql://postgresdb:5432/postgres`). Redis SSL is explicitly disabled (`conductor.redis.ssl=false`). No KMS key references, no encrypted storage configuration in any configuration file.
- **Gap**: Data at rest in all persistence backends (Redis, Postgres, Elasticsearch, SQLite) is unencrypted at the application level. Workflow and task payloads containing sensitive data are stored in plaintext.
- **Compensating Controls**:
  - Enable encryption at rest at the infrastructure layer (AWS RDS encryption, ElastiCache encryption, EBS encryption) — this is outside the application's responsibility.
  - Enable Redis SSL for data in transit.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Enable `conductor.redis.ssl=true` for Redis connections. Deploy databases with encryption at rest enabled (RDS, ElastiCache, OpenSearch managed service all support this). Document encryption requirements for all persistence backends.
- **Evidence**: `server/src/main/resources/application.properties` (plain JDBC URLs), `docker/server/config/config-redis.properties` (`conductor.redis.ssl=false`), `docker/server/config/config-postgres.properties` (unencrypted connection)

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Docker-compose files provide local testing environments with multiple backend configurations: `docker-compose.yaml` (Redis + ES7), `docker-compose-postgres.yaml`, `docker-compose-mysql.yaml`, `docker-compose-es8.yaml`, `docker-compose-postgres-e2e.yaml`. The `loadSample=true` property loads a sample "kitchen sink" workflow for testing. However, no dedicated staging or sandbox environment configuration exists beyond local Docker development.
- **Gap**: No production-equivalent sandbox environment with realistic data shape exists for testing agent behavior before production deployment.
- **Compensating Controls**:
  - Use docker-compose environments for local agent testing with sample workflows.
  - Create a dedicated test Conductor instance using the existing Docker images.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Create a staging environment configuration (e.g., `docker-compose-staging.yaml`) with production-equivalent data shape. Add seed data scripts that create representative workflow definitions.
- **Evidence**: `docker/docker-compose.yaml`, `docker/docker-compose-postgres.yaml`, `docker/docker-compose-postgres-e2e.yaml`

#### DATA-Q3: Selective Query Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Search endpoints support pagination (`start`, `size`), sorting (`sort`), free text search (`freeText`), and structured queries (`query`). The workflow tasks endpoint supports `start` and `count` parameters with status filtering. `SearchResult` objects include `totalHits` for result set awareness. Default page size is 100 with configurable size parameter.
- **Gap**: While pagination and filtering are well-supported, there is no hard maximum on the `size` parameter — an agent could request `size=10000` and receive an unbounded result set. No `cursor`-based pagination is available for consistent paging through large result sets.
- **Compensating Controls**:
  - Agents should be instructed to use small page sizes (50–100) in tool definitions.
  - The `freeText` and `query` parameters allow targeted searches that naturally limit result sizes.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Enforce a maximum page size (e.g., `max_size=500`) on search endpoints. Consider adding cursor-based pagination for large datasets.
- **Evidence**: `rest/src/main/java/.../WorkflowResource.java` (search endpoints with start/size/sort), `rest/src/main/java/.../TaskResource.java` (search with pagination)

#### DATA-Q4: System of Record Designations — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Conductor is inherently the system of record for workflow execution state — it is the authoritative source for workflow definitions, task definitions, workflow instance status, and task execution history. However, no explicit system-of-record documentation exists, no master data management processes are defined, and no conflict resolution logic is implemented for cases where external systems disagree with Conductor's state.
- **Gap**: No documentation establishes Conductor as the golden record for workflow orchestration state. Agents may not know which source to trust when data conflicts arise.
- **Compensating Controls**:
  - Document Conductor as the system of record for workflow execution state in the agent tool definitions.
- **Remediation Timeline**: 7–14 days
- **Recommendation**: Add explicit system-of-record documentation to the API documentation and README. Define which entities Conductor is authoritative for.
- **Evidence**: `schemas/WorkflowDef.json`, `schemas/Workflow.json` (workflow state model), absence of SoR documentation

#### DATA-Q5: Temporal Metadata and Freshness — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Rich temporal metadata exists: `WorkflowDef` has `createTime` and `updateTime` fields. Task executions include `scheduledTime`, `startTime`, `endTime`, and `updateTime`. Workflow instances have `startTime`, `endTime`, and `updateTime`. All timestamps are epoch milliseconds (long). However, no timezone normalization documentation exists, no `Cache-Control` headers are set on responses, no `X-Data-Age` or `consistency_level` headers signal data freshness.
- **Gap**: While timestamps are comprehensive, agents cannot determine if the data returned is current, cached, or eventually consistent. No freshness signaling in API responses.
- **Compensating Controls**:
  - Agents can compare `updateTime` against current time to assess data freshness.
  - Conductor's direct database queries return current state (no caching layer by default).
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add `Cache-Control: no-cache` headers to workflow/task GET endpoints. Document that all timestamps are epoch milliseconds in UTC.
- **Evidence**: `schemas/WorkflowDef.json` (createTime, updateTime), `schemas/TaskDef.json` (createTime, updateTime)

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO
- **Finding**: Conductor exposes a well-documented REST API via Spring `@RestController` annotations with `@Operation` summaries on all endpoints (WorkflowResource, TaskResource, MetadataResource, EventResource, AdminResource, HealthCheckResource, QueueAdminResource, WorkflowBulkResource). A parallel gRPC interface is defined via protobuf service definitions (workflow_service.proto, task_service.proto, metadata_service.proto, event_service.proto). No direct database access or UI automation is required for integration.
- **Implication**: Agents can bind to Conductor via REST or gRPC — both are well-defined integration surfaces. The REST API is the preferred surface for agent tool generation due to springdoc-openapi support.
- **Recommendation**: No action needed. API interface is well-documented.
- **Evidence**: `rest/src/main/java/com/netflix/conductor/rest/controllers/` (10 controller files), `grpc/src/main/proto/grpc/` (5 proto files)

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Partial idempotency support exists. `SubWorkflowParams` includes `idempotencyKey` and `idempotencyStrategy` (RETURN_EXISTING, FAIL) for sub-workflow execution. The `executeWorkflow` endpoint uses a `requestId` parameter for identification. However, general write endpoints (POST /workflow, POST /metadata/workflow, POST /tasks) lack idempotency key support.
- **Implication**: If agent scope is expanded to write-enabled, idempotency gaps on write endpoints become a BLOCKER — duplicate orders or workflow definitions could be created on retry.
- **Recommendation**: If planning future write-enabled agent scope, add idempotency key support to all POST endpoints. The existing `SubWorkflowParams.idempotencyKey` pattern can be extended.
- **Evidence**: `schemas/WorkflowDef.json` (SubWorkflowParams with idempotencyKey), `rest/src/main/java/.../WorkflowResource.java` (executeWorkflow with requestId)

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: All API responses use structured JSON serialization via Jackson. Content-type is `application/json` for all data endpoints and `text/plain` for ID-returning endpoints. gRPC uses Protocol Buffers (protobuf) for binary serialization. No XML marshaling or complex binary formats are used. The `SearchResult` wrapper provides consistent structure with `totalHits` and typed `results` arrays.
- **Implication**: JSON responses are LLM-friendly and can be consumed by agent tools with minimal parsing. gRPC requires protobuf deserialization but provides strong typing.
- **Recommendation**: No action needed. JSON format is well-suited for agent consumption.
- **Evidence**: `rest/src/main/java/.../WorkflowResource.java` (produces APPLICATION_JSON_VALUE, TEXT_PLAIN_VALUE)

### API-Q6: Asynchronous Operation Support

- **Severity**: INFO
- **Finding**: Conductor is inherently asynchronous. Workflow execution is async by default — `POST /workflow` returns a workflow ID immediately. The `POST /workflow/execute/{name}/{version}` endpoint provides synchronous execution with configurable `waitForSeconds` timeout and polling. Long-running workflows proceed in the background via task queues. Task workers poll for tasks asynchronously. Event listeners (Kafka, SQS, AMQP, NATS) provide event-driven async patterns.
- **Implication**: Agents can use the synchronous execute endpoint for short workflows and the standard async workflow start for long-running operations, polling by workflow ID for status.
- **Recommendation**: No action needed. Async patterns are well-supported.
- **Evidence**: `rest/src/main/java/.../WorkflowResource.java` (startWorkflow, executeWorkflow endpoints), `kafka-event-queue/`, `awssqs-event-queue/`, `amqp/`, `nats/`

### API-Q7: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: Conductor supports event emission through multiple mechanisms: `workflowStatusListenerEnabled` and `workflowStatusListenerSink` in WorkflowDef for workflow status events; EventResource for event handler management; modules for Kafka (`kafka-event-queue`), SQS (`awssqs-event-queue`), AMQP (`amqp`), and NATS (`nats`, `nats-streaming`). Tasks support `onStateChange` events. The `workflow-event-listener` module handles workflow completion/failure events.
- **Implication**: Agents can be notified of workflow state changes via event queues, enabling proactive agent patterns without polling.
- **Recommendation**: Document which events are available for agent consumption and their payload schemas.
- **Evidence**: `schemas/WorkflowDef.json` (workflowStatusListenerSink, onStateChange), `rest/src/main/java/.../EventResource.java`, `kafka-event-queue/`, `awssqs-event-queue/`

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: Task-level rate limiting is documented in the `TaskDef` schema (`rateLimitPerFrequency`, `rateLimitFrequencyInSeconds`) and implemented in `RedisRateLimitingDAO`. However, no API-level rate limit headers (`X-RateLimit-Remaining`, `Retry-After`) are returned in REST responses. No API Gateway throttle settings or WAF rate rules are configured. Rate limiting documentation exists only for task execution, not for API consumption.
- **Implication**: Agents calling Conductor's API at machine speed have no visibility into rate limits. They cannot self-throttle based on remaining quota.
- **Recommendation**: Add `X-RateLimit-Remaining` and `Retry-After` response headers. Document API-level rate limits in the OpenAPI spec.
- **Evidence**: `schemas/TaskDef.json` (rate limit fields), `redis-persistence/src/main/java/.../RedisRateLimitingDAO.java`, absence of rate limit headers in controllers

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO (base severity RISK-SAFETY)
- **Finding**: Conductor provides inherent compensation capabilities: `failureWorkflow` in WorkflowDef triggers a compensation workflow on failure; configurable retries with FIXED, EXPONENTIAL_BACKOFF, and LINEAR_BACKOFF strategies; `restart`, `rerun`, and `retry` endpoints for manual recovery; workflow `pause` and `resume` for controlled intervention.
- **Implication**: For read-only agent scope, compensation is informational. If scope expands to write-enabled, the existing failure workflow and retry mechanisms provide a foundation for safe multi-step operations.
- **Recommendation**: No immediate action for read-only scope. Document the failure workflow pattern for future write-enabled agent scenarios.
- **Evidence**: `schemas/WorkflowDef.json` (failureWorkflow, retryLogic), `rest/src/main/java/.../WorkflowResource.java` (restart, retry, rerun endpoints)

### STATE-Q2: Queryable Current State

- **Severity**: INFO
- **Finding**: Comprehensive queryable state exists. GET endpoints provide: workflow status by ID (`GET /workflow/{workflowId}`), running workflows (`GET /workflow/running/{name}`), workflows by correlation ID (`GET /workflow/{name}/correlated/{correlationId}`), task status (`GET /tasks/{taskId}`), search across workflows and tasks with filtering and pagination. The `includeTasks` parameter controls detail level.
- **Implication**: Agents can inspect workflow and task state before taking action. The query surface is rich and well-suited for agent consumption.
- **Recommendation**: No action needed. Queryable state is well-supported.
- **Evidence**: `rest/src/main/java/.../WorkflowResource.java` (GET endpoints), `rest/src/main/java/.../TaskResource.java` (GET endpoints)

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Conductor implements concurrency controls: workflow execution lock via Redis (`workflowExecutionLockEnabled=true`, `RedisLock` using Redisson), concurrent task execution limits (`concurrentExecLimit` in TaskDef, `ConcurrentExecutionLimitDAO`). These prevent race conditions during concurrent workflow processing.
- **Implication**: For read-only agent scope, concurrency controls are informational. The existing Redis-based locking provides a solid foundation if scope expands to write-enabled.
- **Recommendation**: No immediate action for read-only scope.
- **Evidence**: `docker/server/config/config-redis.properties` (workflowExecutionLockEnabled=true), `redis-lock/src/main/java/.../RedisLock.java`, `schemas/TaskDef.json` (concurrentExecLimit)

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits exist for agent-initiated actions. No `max_refunds_per_hour`, `max_records_per_bulk_operation`, or similar blast-radius controls are configurable per agent identity. Payload size limits exist (`maxWorkflowInputPayloadSizeThreshold`, `maxTaskOutputPayloadSizeThreshold`) but these are system-wide, not per-agent.
- **Implication**: For read-only agent scope, transaction limits are informational. If scope expands to write-enabled, blast-radius controls would need to be implemented.
- **Recommendation**: No immediate action for read-only scope. Plan per-agent configurable limits for write-enabled scenarios.
- **Evidence**: `core/src/main/java/.../ConductorProperties.java` (payload size thresholds)

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Conductor supports WAIT task type (waits for external signal), pause/resume workflow capabilities, and HUMAN task types. Workflows can be paused at any point, and tasks can wait indefinitely for human input. The `executeWorkflow` endpoint with `waitUntilTaskRef` parameter enables synchronous execution that pauses at specified tasks.
- **Implication**: For read-only agent scope, draft/pending states are informational. The existing WAIT and HUMAN task types provide a natural mechanism for human-in-the-loop if write-enabled scope is adopted.
- **Recommendation**: No immediate action for read-only scope. Document the WAIT task pattern for future HITL use cases.
- **Evidence**: `rest/src/main/java/.../WorkflowResource.java` (pause, resume, executeWorkflow with waitUntilTaskRef)

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable approval gates per operation type exist at the application layer. However, Conductor's WAIT task can serve as an approval gate within workflow definitions — a workflow can include a WAIT task that pauses execution until an external signal is received. This is configurable per workflow definition but not per API operation type.
- **Implication**: For read-only agent scope, approval gates are informational. Conductor's WAIT task mechanism can be leveraged for approval workflows if needed.
- **Recommendation**: No immediate action for read-only scope.
- **Evidence**: `schemas/WorkflowDef.json` (WAIT task type), `rest/src/main/java/.../WorkflowResource.java` (pause/resume)

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality scores, completeness metrics, or data profiling reports exist. No duplicate detection logic, null rate monitoring, or data freshness SLAs are defined. Conductor does not track data quality of workflow/task payloads.
- **Implication**: Agents acting on Conductor data have no visibility into data quality. Planning input for future data quality monitoring.
- **Recommendation**: Consider adding payload validation metrics (schema compliance rate, null field rate) as custom Micrometer metrics alongside existing workflow metrics.
- **Evidence**: Absence of data quality configuration or metrics in the codebase

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Field names across the codebase are consistently semantically meaningful: `workflowId`, `taskReferenceName`, `correlationId`, `taskType`, `rateLimitPerFrequency`, `workflowExecutionLockEnabled`, `failureWorkflow`, `concurrentExecLimit`, `retryDelaySeconds`. No legacy abbreviations or encoded field names were found. The naming conventions are clear and self-documenting.
- **Implication**: LLM-based agent reasoning can interpret Conductor's field names directly without requiring a data dictionary lookup.
- **Recommendation**: No action needed. Field naming is exemplary.
- **Evidence**: `schemas/WorkflowDef.json`, `schemas/TaskDef.json`, `core/src/main/java/.../ConductorProperties.java`

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No formal data catalog (Glue Data Catalog, Collibra, DataHub) exists. JSON Schema files in `schemas/` (WorkflowDef.json, TaskDef.json, Workflow.json, Task.json) serve as partial schema documentation with descriptions on all fields. The springdoc-openapi integration auto-generates API documentation at runtime. The `@Operation` annotations provide summary descriptions for all endpoints.
- **Implication**: Schema documentation exists in machine-readable format (JSON Schema + OpenAPI), which accelerates agent tool definition. A formal data catalog would improve discoverability at the portfolio level.
- **Recommendation**: Consider registering Conductor's schemas in a centralized data catalog if one exists in the organization.
- **Evidence**: `schemas/WorkflowDef.json`, `schemas/TaskDef.json`, `server/build.gradle` (springdoc-openapi)

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: `Monitors.java` records extensive business-level metrics: `workflow_start_success` / `workflow_start_error` (workflow initiation), `workflow_execution` timer (completion time), `workflow_failure` (termination by status), `task_execution` timer, `task_rate_limited`, `task_concurrent_execution_limited`, `task_queue_depth`, `workflow_running` gauge, `event_queue_messages_processed/handled/error`. These are published via Micrometer to configurable backends (Prometheus, Datadog, CloudWatch).
- **Implication**: When agents consume Conductor, these business metrics become the primary signal for whether agent interactions produce good outcomes. The metrics infrastructure is mature.
- **Recommendation**: Add agent-specific metric dimensions (e.g., tag by `agent_id`) when agent authentication is implemented.
- **Evidence**: `core/src/main/java/com/netflix/conductor/metrics/Monitors.java`

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: Conductor exposes a well-documented REST API with 10 Spring `@RestController` classes and a parallel gRPC interface with 5 protobuf service definitions. All REST endpoints have `@Operation` annotations. No direct database access or UI automation required.
- **Gap**: None — API interface is well-documented.
- **Recommendation**: No action needed.
- **Evidence**: `rest/src/main/java/com/netflix/conductor/rest/controllers/` (10 files), `grpc/src/main/proto/grpc/` (5 proto files)

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: Runtime-generated OpenAPI spec via springdoc-openapi at `/api-docs`. gRPC protobuf definitions and JSON Schemas in `schemas/`. No static OpenAPI file committed to repository.
- **Gap**: No static, committed OpenAPI specification file. Runtime-only generation means spec not available without a running instance.
- **Recommendation**: Export and commit OpenAPI spec as CI build artifact.
- **Evidence**: `server/build.gradle` (springdoc-openapi), `grpc/src/main/proto/grpc/workflow_service.proto`, `schemas/WorkflowDef.json`

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: `ErrorResponse` class with `status`, `code`, `message`, `instance`, `retryable`, `validationErrors`, `metadata` fields. `ApplicationExceptionMapper` maps exceptions to HTTP status codes. `retryable=true` for `TransientException`.
- **Gap**: `code` field not consistently populated. `retryable` only covers `TransientException`.
- **Recommendation**: Populate `code` field consistently. Add error codes for all scenarios.
- **Evidence**: `common/src/main/java/.../ErrorResponse.java`, `rest/src/main/java/.../ApplicationExceptionMapper.java`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Partial idempotency: `SubWorkflowParams.idempotencyKey`, `executeWorkflow` requestId. General write endpoints lack idempotency keys.
- **Gap**: General write endpoints lack idempotency support (informational for read-only scope).
- **Recommendation**: Add idempotency keys to all POST endpoints if scope expands to write-enabled.
- **Evidence**: `schemas/WorkflowDef.json` (SubWorkflowParams), `rest/src/main/java/.../WorkflowResource.java`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: JSON via Jackson for REST, Protocol Buffers for gRPC. `SearchResult` wrapper with `totalHits` and typed results.
- **Gap**: None.
- **Recommendation**: No action needed.
- **Evidence**: `rest/src/main/java/.../WorkflowResource.java`

#### API-Q6: Asynchronous Operation Support
- **Severity**: INFO
- **Finding**: Inherently async. `POST /workflow` returns immediately. Synchronous execute endpoint with configurable timeout. Event listeners via Kafka, SQS, AMQP, NATS.
- **Gap**: None — well-supported.
- **Recommendation**: No action needed.
- **Evidence**: `rest/src/main/java/.../WorkflowResource.java`, `kafka-event-queue/`, `awssqs-event-queue/`

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: `workflowStatusListenerSink`, `onStateChange` events, event handlers via Kafka/SQS/AMQP/NATS. `workflow-event-listener` module.
- **Gap**: None — events well-supported.
- **Recommendation**: Document event payloads for agent consumption.
- **Evidence**: `schemas/WorkflowDef.json`, `rest/src/main/java/.../EventResource.java`, `kafka-event-queue/`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: Task-level rate limiting documented and implemented. No API-level rate limit headers in responses.
- **Gap**: No `X-RateLimit-Remaining` or `Retry-After` headers.
- **Recommendation**: Add rate limit response headers.
- **Evidence**: `schemas/TaskDef.json`, `redis-persistence/src/main/java/.../RedisRateLimitingDAO.java`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: No authentication exists. REST API is open/unauthenticated by default. No Spring Security, OAuth2, JWT, API key, or mTLS configuration. `WorkflowContext` stores `clientApp`/`userName` but defaults to empty strings.
- **Gap**: Zero authentication controls. Any network-reachable client can call any endpoint.
- **Recommendation**: Add `spring-boot-starter-security` with OAuth2 resource server or API key authentication.
- **Evidence**: `server/build.gradle`, `core/src/main/java/.../WorkflowContext.java`, `rest/src/main/java/.../WorkflowResource.java`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: No authorization model. All endpoints equally accessible. No IAM policies, RBAC, or ABAC.
- **Gap**: Cannot grant read-only access to agents. No permission scoping possible.
- **Recommendation**: Implement RBAC with Spring Security `@PreAuthorize`.
- **Evidence**: `rest/src/main/java/com/netflix/conductor/rest/controllers/WorkflowResource.java`, `server/build.gradle`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization. GET, POST, PUT, DELETE all equally accessible. No `canRead`/`canWrite`/`canDelete` checks.
- **Gap**: Cannot enforce read-only access at the application level.
- **Recommendation**: Add method-level authorization to controllers.
- **Evidence**: `rest/src/main/java/.../WorkflowResource.java`, `rest/src/main/java/.../MetadataResource.java`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: RISK-QUALITY
- **Finding**: `WorkflowContext` class provides framework for identity propagation (clientApp, userName) but fields are not populated from HTTP requests. No JWT parsing, no on-behalf-of flows.
- **Gap**: Cannot distinguish agent-as-self vs agent-on-behalf-of-user.
- **Recommendation**: Extend `WorkflowContext` to parse identity from HTTP headers.
- **Evidence**: `core/src/main/java/com/netflix/conductor/core/WorkflowContext.java`

#### AUTH-Q5: Credential Management
- **Severity**: RISK-QUALITY
- **Finding**: AI provider API keys use environment variables. Postgres password hardcoded (`spring.datasource.password=conductor`). Redis has no authentication. No Secrets Manager or Vault integration.
- **Gap**: Hardcoded credentials in committed configuration files. No secrets rotation.
- **Recommendation**: Integrate AWS Secrets Manager or HashiCorp Vault.
- **Evidence**: `docker/server/config/config-postgres.properties`, `server/src/main/resources/application.properties`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No immutable audit logging. Log4j PatternLayout to console. No CloudTrail, no immutable log storage. No authenticated principal in logs.
- **Gap**: No tamper-evident audit trail. Cannot determine which caller performed any operation.
- **Recommendation**: Enable structured JSON logging with caller identity. Ship to immutable log store.
- **Evidence**: `docker/server/config/log4j.properties`, `server/src/main/resources/application.properties`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: No mechanism to suspend/revoke agent identities. No API key management, no identity revocation endpoints.
- **Gap**: Cannot isolate a misbehaving agent without shutting down Conductor.
- **Recommendation**: Implement identity revocation when adding authentication (AUTH-Q1).
- **Evidence**: `server/build.gradle`, absence of identity management endpoints

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO (base severity RISK-SAFETY)
- **Finding**: Inherent compensation: `failureWorkflow` in WorkflowDef, configurable retries (FIXED, EXPONENTIAL_BACKOFF, LINEAR_BACKOFF), restart/rerun/retry endpoints.
- **Gap**: No gap for read-only scope. Write-enabled would need review.
- **Recommendation**: No action for read-only scope.
- **Evidence**: `schemas/WorkflowDef.json` (failureWorkflow), `rest/src/main/java/.../WorkflowResource.java`

#### STATE-Q2: Queryable Current State
- **Severity**: INFO
- **Finding**: Comprehensive GET endpoints for workflow status, task status, search, running workflows. Filtering, pagination, and detail-level control (`includeTasks`).
- **Gap**: None — well-supported.
- **Recommendation**: No action needed.
- **Evidence**: `rest/src/main/java/.../WorkflowResource.java`, `rest/src/main/java/.../TaskResource.java`

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Workflow execution lock via Redis/Redisson (`workflowExecutionLockEnabled=true`). Concurrent task execution limits (`concurrentExecLimit` in TaskDef).
- **Gap**: None for read-only scope.
- **Recommendation**: No action for read-only scope.
- **Evidence**: `docker/server/config/config-redis.properties`, `redis-lock/src/main/java/.../RedisLock.java`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: No circuit breaker library (Resilience4j, Hystrix). HTTP task has timeout only. `spring-retry` present but not configured as circuit breaker.
- **Gap**: No circuit breaker prevents cascading failures from external dependencies.
- **Recommendation**: Add Resilience4j to `http-task` module.
- **Evidence**: `server/build.gradle`, `dependencies.gradle`, `core/src/main/java/.../DefaultEventProcessor.java`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: Task-level rate limiting via `RedisRateLimitingDAO`. No API-layer rate limiting on REST endpoints.
- **Gap**: Runaway agent loop can overwhelm REST API at machine speed.
- **Recommendation**: Deploy API Gateway with throttling or add application-level rate limiting middleware.
- **Evidence**: `redis-persistence/src/main/java/.../RedisRateLimitingDAO.java`, `schemas/TaskDef.json`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable per-agent transaction limits. System-wide payload size limits exist.
- **Gap**: No per-agent blast radius controls (informational for read-only).
- **Recommendation**: Plan per-agent limits for write-enabled scenarios.
- **Evidence**: `core/src/main/java/.../ConductorProperties.java`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `orchestrator`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path. This service is P2 priority.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: WAIT task type, pause/resume capabilities, HUMAN task types. `executeWorkflow` with `waitUntilTaskRef`.
- **Gap**: Informational for read-only scope.
- **Recommendation**: No action for read-only scope. WAIT tasks serve as HITL mechanism for write-enabled.
- **Evidence**: `rest/src/main/java/.../WorkflowResource.java`, `schemas/WorkflowDef.json`

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable approval gates per operation type. WAIT tasks can serve as approval gates within workflow definitions.
- **Gap**: Informational for read-only scope.
- **Recommendation**: No action for read-only scope.
- **Evidence**: `schemas/WorkflowDef.json`, `rest/src/main/java/.../WorkflowResource.java`

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: Docker-compose files for multiple backend configurations. `loadSample=true` for test workflows. No dedicated staging/sandbox environment.
- **Gap**: No production-equivalent sandbox for testing agent behavior.
- **Recommendation**: Create staging environment with production-equivalent data shape.
- **Evidence**: `docker/docker-compose.yaml`, `docker/docker-compose-postgres.yaml`, `docker/docker-compose-postgres-e2e.yaml`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: No data classification. Workflow/task payloads are arbitrary JSON that may contain sensitive data. `maskedFields` in WorkflowDef is opt-in field masking, not systematic classification.
- **Gap**: No systematic data classification. No field-level access controls. No Macie integration.
- **Recommendation**: Audit workflows for sensitive data. Enforce `maskedFields`. Implement classification framework.
- **Evidence**: `schemas/WorkflowDef.json` (maskedFields), `server/src/main/resources/application.properties`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No data residency controls. AI provider configs reference region settings but no data sovereignty enforcement on workflow data.
- **Gap**: Workflow payloads may contain regulated data with no residency controls.
- **Recommendation**: Document residency requirements. Deploy in region-locked environment.
- **Evidence**: `server/src/main/resources/application.properties`, `docker/server/config/config-postgres.properties`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK-QUALITY
- **Finding**: Search endpoints with `start`/`size`/`sort`/`freeText`/`query` pagination. `SearchResult` with `totalHits`. Default page size 100.
- **Gap**: No hard maximum on `size` parameter. No cursor-based pagination.
- **Recommendation**: Enforce maximum page size. Consider cursor-based pagination.
- **Evidence**: `rest/src/main/java/.../WorkflowResource.java`, `rest/src/main/java/.../TaskResource.java`

#### DATA-Q4: System of Record Designations
- **Severity**: RISK-QUALITY
- **Finding**: Conductor is inherently the SoR for workflow execution state. No explicit documentation of SoR designations.
- **Gap**: No documented system-of-record designations.
- **Recommendation**: Document Conductor as SoR for workflow orchestration state.
- **Evidence**: `schemas/WorkflowDef.json`, `schemas/Workflow.json`

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK-QUALITY
- **Finding**: Rich timestamps: `createTime`, `updateTime` on definitions; `scheduledTime`, `startTime`, `endTime`, `updateTime` on tasks. Epoch milliseconds. No `Cache-Control` or freshness signaling headers.
- **Gap**: No freshness signaling in API responses.
- **Recommendation**: Add `Cache-Control: no-cache` headers. Document timestamp format.
- **Evidence**: `schemas/WorkflowDef.json`, `schemas/TaskDef.json`

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: No PII redaction. Log4j PatternLayout logs full messages. `ApplicationExceptionMapper` logs full exceptions. `maskedFields` masks outputs but not logs.
- **Gap**: PII can leak into logs via workflow/task payloads.
- **Recommendation**: Implement Log4j PII scrubbing filter. Extend `maskedFields` to logging layer.
- **Evidence**: `docker/server/config/log4j.properties`, `rest/src/main/java/.../ApplicationExceptionMapper.java`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality scores, completeness metrics, or data profiling. No duplicate detection or null rate monitoring.
- **Gap**: No data quality visibility.
- **Recommendation**: Consider adding payload validation metrics via Micrometer.
- **Evidence**: Absence of data quality configuration

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: `WorkflowDef.version` field. gRPC protobuf package versioning. JSON Schemas in `schemas/` with `$id` URIs. No REST API URL versioning. No breaking change detection in CI.
- **Gap**: Agent tool bindings can break silently. No automated breaking change detection.
- **Recommendation**: Add `openapi-diff` to CI. Consider URL versioning for REST endpoints.
- **Evidence**: `schemas/WorkflowDef.json`, `grpc/src/main/proto/grpc/workflow_service.proto`, `.github/workflows/ci.yml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Consistently meaningful field names: `workflowId`, `taskReferenceName`, `correlationId`, `rateLimitPerFrequency`. No legacy abbreviations.
- **Gap**: None.
- **Recommendation**: No action needed. Exemplary field naming.
- **Evidence**: `schemas/WorkflowDef.json`, `schemas/TaskDef.json`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal data catalog. JSON Schema files serve as partial documentation. Springdoc-openapi auto-generates API docs.
- **Gap**: No centralized data catalog.
- **Recommendation**: Register schemas in organizational data catalog if one exists.
- **Evidence**: `schemas/WorkflowDef.json`, `schemas/TaskDef.json`, `server/build.gradle`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: Log4j with PatternLayout (not JSON). No OpenTelemetry, X-Ray, or traceparent propagation. No request_id/correlation_id in log output. Micrometer present for metrics only.
- **Gap**: Cannot trace agent-initiated requests through Conductor. No structured logging.
- **Recommendation**: Switch to JSON structured logging. Add OpenTelemetry instrumentation.
- **Evidence**: `docker/server/config/log4j.properties`, `dependencies.gradle`, `server/build.gradle`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: Prometheus metrics enabled. Extensive Micrometer metrics via `Monitors.java`. Multiple backend support (Prometheus, Datadog, CloudWatch). No alerting thresholds configured.
- **Gap**: No alerts for error rate or latency degradation.
- **Recommendation**: Define Prometheus alerting rules for key metrics. Integrate with PagerDuty/OpsGenie.
- **Evidence**: `server/src/main/resources/application.properties`, `core/src/main/java/.../Monitors.java`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: Extensive business metrics: `workflow_start_success/error`, `workflow_execution` timer, `workflow_failure`, `task_execution`, `task_rate_limited`, `task_queue_depth`, `workflow_running`. Published via Micrometer.
- **Gap**: No agent-specific metric dimensions.
- **Recommendation**: Add `agent_id` tag to metrics when authentication is implemented.
- **Evidence**: `core/src/main/java/com/netflix/conductor/metrics/Monitors.java`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK-QUALITY
- **Finding**: No Terraform/CloudFormation/CDK IaC. Docker-compose for local dev only. No drift detection. No peer review for infra changes.
- **Gap**: Production infrastructure not defined as code. No governance on agent-facing surface.
- **Recommendation**: Create IaC for production deployment (API Gateway, IAM, networking).
- **Evidence**: Absence of IaC files, `docker/docker-compose.yaml`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: CI with `./gradlew build` + tests. Test-harness integration tests. Cypress E2E. No API contract testing (no Pact, no OpenAPI validation).
- **Gap**: API breaking changes not caught in pipeline.
- **Recommendation**: Add API contract testing. Export and validate OpenAPI spec in CI.
- **Evidence**: `.github/workflows/ci.yml`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: Docker images published with version tags. No blue/green, canary, or automated rollback.
- **Gap**: No automated rollback mechanism. Manual Docker image rollback required.
- **Recommendation**: Implement Kubernetes rolling deployments with automatic rollback triggers.
- **Evidence**: `.github/workflows/publish.yml`, `docker/docker-compose.yaml`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: 391 test files. JaCoCo coverage with aggregation. Test-harness integration tests. Cypress E2E. No explicit REST API contract tests.
- **Gap**: No tests specifically validating API contracts for agent consumption.
- **Recommendation**: Add REST API contract tests using REST Assured or MockMvc.
- **Evidence**: `.github/workflows/ci.yml`, `build.gradle` (JaCoCo), `test-harness/`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: RISK-QUALITY
- **Finding**: No encryption at rest. SQLite with no encryption. Plain JDBC for Postgres. Redis SSL disabled (`conductor.redis.ssl=false`). No KMS keys.
- **Gap**: All persistence backends store data unencrypted.
- **Recommendation**: Enable Redis SSL. Deploy databases with encryption at rest (RDS, ElastiCache).
- **Evidence**: `server/src/main/resources/application.properties`, `docker/server/config/config-redis.properties`, `docker/server/config/config-postgres.properties`

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `rest/src/main/java/com/netflix/conductor/rest/controllers/WorkflowResource.java` | API-Q1, API-Q4, API-Q5, API-Q6, AUTH-Q1, AUTH-Q2, AUTH-Q3, STATE-Q1, STATE-Q2, HITL-Q1, HITL-Q2 |
| `rest/src/main/java/com/netflix/conductor/rest/controllers/TaskResource.java` | API-Q1, STATE-Q2, DATA-Q3 |
| `rest/src/main/java/com/netflix/conductor/rest/controllers/MetadataResource.java` | API-Q1, AUTH-Q3 |
| `rest/src/main/java/com/netflix/conductor/rest/controllers/EventResource.java` | API-Q1, API-Q7 |
| `rest/src/main/java/com/netflix/conductor/rest/controllers/AdminResource.java` | API-Q1 |
| `rest/src/main/java/com/netflix/conductor/rest/controllers/ApplicationExceptionMapper.java` | API-Q3, DATA-Q6 |
| `common/src/main/java/com/netflix/conductor/common/validation/ErrorResponse.java` | API-Q3 |
| `core/src/main/java/com/netflix/conductor/core/WorkflowContext.java` | AUTH-Q1, AUTH-Q4 |
| `core/src/main/java/com/netflix/conductor/core/config/ConductorProperties.java` | STATE-Q6, DISC-Q2 |
| `core/src/main/java/com/netflix/conductor/metrics/Monitors.java` | OBS-Q2, OBS-Q3 |
| `core/src/main/java/com/netflix/conductor/core/events/DefaultEventProcessor.java` | STATE-Q4 |
| `redis-persistence/src/main/java/com/netflix/conductor/redis/dao/RedisRateLimitingDAO.java` | STATE-Q5, API-Q8, DATA-Q6 |
| `redis-lock/src/main/java/com/netflix/conductor/redislock/lock/RedisLock.java` | STATE-Q3 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `grpc/src/main/proto/grpc/workflow_service.proto` | API-Q1, API-Q2, DISC-Q1 |
| `grpc/src/main/proto/grpc/task_service.proto` | API-Q1, API-Q2 |
| `grpc/src/main/proto/grpc/metadata_service.proto` | API-Q1 |
| `grpc/src/main/proto/grpc/event_service.proto` | API-Q1 |
| `schemas/WorkflowDef.json` | API-Q2, API-Q4, API-Q7, STATE-Q1, STATE-Q3, HITL-Q1, HITL-Q2, DATA-Q1, DATA-Q4, DATA-Q5, DISC-Q1, DISC-Q2, DISC-Q3 |
| `schemas/TaskDef.json` | API-Q2, API-Q8, STATE-Q5, DATA-Q5, DISC-Q2 |
| `schemas/Workflow.json` | DATA-Q4 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/ci.yml` | ENG-Q2, ENG-Q4, DISC-Q1 |
| `.github/workflows/publish.yml` | ENG-Q3 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `docker/server/Dockerfile` | ENG-Q3 |
| `docker/docker-compose.yaml` | HITL-Q3, ENG-Q1, ENG-Q3 |
| `docker/docker-compose-postgres.yaml` | HITL-Q3 |
| `docker/docker-compose-postgres-e2e.yaml` | HITL-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `build.gradle` | ENG-Q4 |
| `server/build.gradle` | API-Q2, AUTH-Q1, AUTH-Q2, AUTH-Q7, STATE-Q4, DISC-Q3 |
| `dependencies.gradle` | STATE-Q4, OBS-Q1 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `server/src/main/resources/application.properties` | AUTH-Q5, AUTH-Q6, DATA-Q1, DATA-Q2, OBS-Q2, ENG-Q5 |
| `docker/server/config/config-redis.properties` | STATE-Q3, STATE-Q5, ENG-Q5 |
| `docker/server/config/config-postgres.properties` | AUTH-Q5, DATA-Q2, ENG-Q5 |
| `docker/server/config/log4j.properties` | AUTH-Q6, OBS-Q1, DATA-Q6 |
