# Agentic Readiness Analysis Report

**Target**: conductor-oss--conductor
**Date**: 2026-05-08
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**Repository Type**: application
**Service Archetype**: orchestrator (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: java, workflow, orchestration
**Context**: Workflow orchestration engine originally from Netflix.

**Archetype Justification**: Conductor coordinates multi-step workflows by scheduling tasks across worker services and managing workflow state machines. It calls downstream task workers, maintains workflow/task state, and orchestrates complex execution sequences — classic orchestrator characteristics.

**Surface flags**:
  - has_persistent_data_store: true
  - has_http_rpc_surface: true
  - has_auth_surface: false
  - has_write_operations: true
  - has_logging_of_user_data: true

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 1 | **RISK-SAFETY**: 7 | **RISK-QUALITY**: 10 | **INFOs**: 11

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days.

### V6 Classification Rationale

This repo has 1 High finding, 17 Medium findings (7 safety-impact), and 11 Low findings. 1 High finding → "Remediation Required" per V6 classification rule. The V5 Readiness Profile ("Remediation Required") and V6 tier align: 1 BLOCKER maps to 1 High, requiring resolution before any agent deployment.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 1 |
| RISK-SAFETY | 7 |
| RISK-QUALITY | 10 |
| INFO | 11 |
| N/A | 0 |
| Not Evaluated (extended) | 14 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 5
**Extended Questions Not Triggered**: 14
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: orchestrator (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: The Conductor OSS codebase has no authentication mechanism whatsoever. There is no `spring-boot-starter-security` dependency, no `SecurityFilterChain`, no OAuth2/JWT enforcement, no API key authentication, and no auth filters or interceptors. The UI uses a `NoAuthProvider` that returns null for all auth functions. All REST and gRPC API endpoints are completely open and unauthenticated.
- **Gap**: No machine identity authentication exists. Any caller — human, agent, or malicious actor — can invoke any API operation without identification. There is no way to attribute actions to a specific principal.
- **Remediation**:
  - **Immediate**: Add `spring-boot-starter-security` and configure a `SecurityFilterChain` with OAuth2 resource server (JWT) or API key authentication. Define a machine identity scheme (client credentials flow or API key with principal attribution) for agent callers.
  - **Target State**: Every API request is authenticated with a verifiable machine identity. Audit logs include the authenticated principal for each operation.
  - **Estimated Effort**: Medium
  - **Dependencies**: AUTH-Q6 (audit logging requires identity to log)
- **Evidence**: `rest/build.gradle` (no security dependency), `server/build.gradle`, all REST controllers in `rest/src/main/java/com/netflix/conductor/rest/controllers/` (no auth annotations)

---

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Without any authentication mechanism (AUTH-Q1), there is no authorization model at all. Every caller has full access to all operations — workflow start, terminate, delete, metadata management, admin operations, and queue management.
- **Gap**: No permission scoping exists. An agent identity cannot be restricted to read-only access or limited to specific workflow types/resources.
- **Compensating Controls**:
  - Deploy an API Gateway in front of Conductor with route-level authorization policies that restrict agent callers to specific endpoints
  - Use network-level segmentation to limit which services can reach Conductor's API
- **Remediation Timeline**: 60–90 days (dependent on AUTH-Q1 resolution)
- **Recommendation**: After implementing AUTH-Q1, define IAM-style scoped permissions per agent identity (e.g., `workflow:read`, `workflow:execute`, `metadata:read`, `admin:*`).
- **Evidence**: All REST controllers have no `@PreAuthorize` or role annotations; no Spring Security configuration exists anywhere in the codebase

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization exists. All endpoints are equally accessible to all callers. There is no mechanism to allow an agent to read workflows but not terminate them, or to poll tasks but not update metadata definitions.
- **Gap**: Cannot enforce action-level granularity (e.g., read vs write vs delete on the same resource type).
- **Compensating Controls**:
  - API Gateway method-level policies (allow GET but deny DELETE for agent callers)
  - Proxy layer that intercepts and blocks specific HTTP methods per caller identity
- **Remediation Timeline**: 60–90 days (dependent on AUTH-Q1)
- **Recommendation**: Implement method-level authorization using Spring Security's `@PreAuthorize` with fine-grained roles (WORKFLOW_READ, WORKFLOW_EXECUTE, WORKFLOW_TERMINATE, METADATA_WRITE, ADMIN).
- **Evidence**: `rest/src/main/java/com/netflix/conductor/rest/controllers/WorkflowResource.java`, `TaskResource.java`, `AdminResource.java` — no authorization annotations

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The `@Audit` annotation exists and is applied to service classes (`WorkflowServiceImpl`, `TaskServiceImpl`, `AdminServiceImpl`), but there is NO AOP aspect or interceptor that actually processes it. The annotation is a no-op. The `Auditable` base class provides `createdBy`/`updatedBy` fields on metadata entities, but no actual audit log writing occurs. No CloudTrail or equivalent audit trail integration exists.
- **Gap**: No immutable audit logging for any API operation. Cannot determine who performed what action or when.
- **Compensating Controls**:
  - Deploy an API Gateway with access logging enabled (captures all requests)
  - Enable CloudTrail for API Gateway invocations to create an immutable record
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement the `@Audit` AOP aspect to write structured audit events (principal, action, resource, timestamp) to an append-only log store. Integrate with CloudWatch Logs with Object Lock or S3 with immutable retention.
- **Evidence**: `common/src/main/java/com/netflix/conductor/common/metadata/Auditable.java`, `core/src/main/java/com/netflix/conductor/service/WorkflowServiceImpl.java` (@Audit annotation present but unprocessed)

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Since no authentication mechanism exists (AUTH-Q1), there is no concept of an agent identity that could be suspended or revoked. If a misbehaving agent is discovered, the only option is network-level blocking.
- **Gap**: No mechanism to suspend or revoke individual agent identities without affecting other callers.
- **Compensating Controls**:
  - API Gateway with API key management — keys can be individually disabled
  - Network security groups / firewall rules to block specific caller IPs
- **Remediation Timeline**: 60–90 days (dependent on AUTH-Q1)
- **Recommendation**: Implement identity management with revocation capability. API key approach with per-agent keys allows instant revocation via key deletion.
- **Evidence**: No security framework, no identity store, no API key management in the codebase

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Conductor has retry logic for database deadlocks (Spring `RetryTemplate`, 3 attempts) and task-level retries (FIXED, EXPONENTIAL_BACKOFF, LINEAR_BACKOFF). Distributed locking exists via Redisson, Postgres, and local implementations. However, there is NO circuit breaker pattern for external dependency calls. The HTTP task module connects to arbitrary external URLs without circuit breakers.
- **Gap**: No circuit breaker (Resilience4j, Hystrix) on external calls. A failing downstream service could cause cascading failures through Conductor's task execution pipeline.
- **Compensating Controls**:
  - Task-level timeouts (150ms read, 100ms connect) provide partial protection
  - The distributed lock with configurable lease time prevents runaway decide loops
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add Resilience4j circuit breakers on the HTTP task executor and any external service calls (Elasticsearch, Redis, message queues).
- **Evidence**: `http-task/` module (no circuit breaker on HTTP calls), `core/src/main/java/com/netflix/conductor/core/execution/` (RetryTemplate for DB, but no circuit breaker), no `resilience4j` in any `build.gradle`

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Task-level rate limiting exists via `RateLimitingDAO` (Redis sorted-set sliding window) configured per `TaskDef` with `rateLimitPerFrequency` and `rateLimitFrequencyInSeconds`. Concurrency limits exist via `ConcurrentExecutionLimitDAO`. However, there is NO HTTP/API-level rate limiting. No request throttling middleware, no Bucket4j, no API Gateway throttle configuration, and no WAF rate rules.
- **Gap**: No API-level rate limiting. A runaway agent calling REST endpoints at machine speed cannot be throttled by the application itself.
- **Compensating Controls**:
  - Task-level rate limiting partially constrains the execution pipeline
  - Deploy an API Gateway with usage plans and throttling configuration in front of Conductor
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `spring-boot-starter-web` rate limiting (e.g., Bucket4j with Spring Boot integration) or deploy behind an API Gateway with usage plan throttles per API key.
- **Evidence**: `redis-concurrency-limit/` module (task-level only), `rest/build.gradle` (no rate-limiting dependency), no throttling middleware in REST controllers

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Conductor logs request URIs and full exception details including request context. The `ApplicationExceptionMapper` logs `request.getRequestURI()` with exceptions. Workflow and task data (which may contain user-submitted input/output as arbitrary JSON) is stored and potentially logged without redaction. The application has no PII masking library, no log scrubbing middleware, and no field-level redaction.
- **Gap**: No PII redaction in logs. Workflow input/output data — which can contain arbitrary user data — may leak into log files without filtering.
- **Compensating Controls**:
  - Configure log levels to minimize data exposure in production
  - Deploy a log aggregation pipeline with PII detection/scrubbing (e.g., Amazon Macie on log buckets)
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a log filter that redacts sensitive fields from workflow input/output before logging. Implement structured logging with explicit field allowlists.
- **Evidence**: `rest/src/main/java/com/netflix/conductor/rest/controllers/ApplicationExceptionMapper.java` (logs request URI + full exception), `server/src/main/resources/application.properties` (no log scrubbing config)

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The application uses `springdoc-openapi-starter-webmvc-ui` to generate OpenAPI documentation at runtime (accessible at `/api-docs`). Swagger annotations (`@Operation`) are present on REST controllers. Additionally, 32 Protocol Buffer `.proto` files define the gRPC service API, and 4 JSON Schema files exist in `/schemas/`. However, there is no static OpenAPI spec file committed to the repository — the spec is only available when the server is running.
- **Gap**: No static, version-controlled OpenAPI specification file. Agent tool generation requires a running server or a CI step to export the spec.
- **Compensating Controls**:
  - The springdoc runtime generation means the spec is always current with the implementation
  - Proto files provide a static, machine-readable definition for gRPC consumers
- **Remediation Timeline**: 30 days
- **Recommendation**: Add a Gradle task (springdoc-openapi-gradle-plugin) to export the OpenAPI spec at build time and commit the generated `openapi.json` to the repository.
- **Evidence**: `rest/build.gradle` (springdoc dependency), `grpc/src/main/proto/` (32 proto files), `schemas/` (4 JSON Schema files), no `openapi.yaml` or `swagger.json` committed

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The application provides well-structured error responses via `ApplicationExceptionMapper` and `ValidationExceptionMapper`. The `ErrorResponse` class includes `status` (HTTP code), `message`, `instance` (server ID), and `retryable` boolean. Custom exceptions distinguish retriable (`TransientException`) from terminal errors (`NotFoundException`, `ConflictException`). This is a solid error handling pattern.
- **Gap**: Minor gap — no machine-readable error `code` field (only HTTP status and message). Error classification relies on exception type mapping rather than an explicit error code enum.
- **Compensating Controls**:
  - The `retryable` boolean field enables agent retry decisions
  - HTTP status codes combined with exception class names provide reasonable error classification
- **Remediation Timeline**: 30 days
- **Recommendation**: Add an explicit `errorCode` string field to `ErrorResponse` (e.g., `WORKFLOW_NOT_FOUND`, `CONFLICT_EXISTING_WORKFLOW`, `TRANSIENT_DB_ERROR`) for more precise agent error handling.
- **Evidence**: `rest/src/main/java/com/netflix/conductor/rest/controllers/ApplicationExceptionMapper.java`, `common/src/main/java/com/netflix/conductor/common/validation/ErrorResponse.java`

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The application maintains JSON Schema files for core entities (Workflow, Task, WorkflowDef, TaskDef) in `/schemas/` and gRPC proto files in `/grpc/src/main/proto/`. The API uses a fixed `/api/` prefix without versioning (no `/v1/`, `/v2/` patterns). No breaking change detection tools (OpenAPI diff, buf breaking) are configured in CI. No consumer-driven contract tests (Pact) exist.
- **Gap**: No API versioning strategy. No breaking change detection in CI pipeline. Schema changes could silently break agent tool bindings.
- **Compensating Controls**:
  - Proto files provide typed contracts for gRPC consumers
  - The CI pipeline runs comprehensive integration tests that would catch breaking changes
- **Remediation Timeline**: 60 days
- **Recommendation**: Introduce API version prefixes (`/api/v1/`), add OpenAPI diff checking in the CI pipeline, and consider consumer-driven contract tests for critical agent-facing endpoints.
- **Evidence**: `schemas/` (JSON Schemas), `grpc/src/main/proto/` (Proto definitions), `.github/workflows/ci.yml` (no contract testing step), `rest/src/main/java/com/netflix/conductor/rest/config/RequestMappingConstants.java`

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Conductor uses SLF4J/Log4j for logging with `@Slf4j` annotations throughout. Metrics are published via Micrometer with 14 registry backends supported (Prometheus, CloudWatch, Datadog, OTLP, etc.). The Prometheus endpoint is enabled by default. However, there is NO distributed tracing (no OpenTelemetry SDK, no X-Ray instrumentation, no `traceparent` header propagation). Logs are not structured (JSON) — they use traditional format with Log4j. The `correlationId` field exists as a first-class model attribute on workflows but is not propagated into log MDC context.
- **Gap**: No distributed tracing. No structured JSON logging. Cannot trace an agent-initiated request through the system's internal execution path.
- **Compensating Controls**:
  - Workflow `correlationId` provides business-level correlation
  - Rich Micrometer metrics allow monitoring of workflow/task execution patterns
- **Remediation Timeline**: 60 days
- **Recommendation**: Add OpenTelemetry Java agent or SDK instrumentation. Configure Log4j with JSON layout and include MDC fields (correlationId, workflowId, taskId) in every log entry.
- **Evidence**: `server/src/main/resources/application.properties` (metrics config, no tracing config), `docker/server/config/log4j.properties` (non-JSON format), no OpenTelemetry dependency in any `build.gradle`

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The application exposes Prometheus metrics via `/actuator/prometheus` with percentile configurations (p50, p75, p90, p95, p99). Rich custom metrics exist via the `Monitors` class (workflow start/completion/termination times, task execution, queue depth, errors). However, no alerting thresholds are configured within the application or its repository — no CloudWatch alarms, no Prometheus alert rules, no PagerDuty/OpsGenie integration.
- **Gap**: No alerting configuration. Metrics are available but no thresholds are defined to trigger alerts when error rates spike or latency degrades.
- **Compensating Controls**:
  - Prometheus endpoint enables external alerting systems (Grafana/Alertmanager) to be configured separately
  - Health check endpoint provides basic availability monitoring
- **Remediation Timeline**: 30 days
- **Recommendation**: Add Prometheus alerting rules or CloudWatch alarms for: API error rate > 5%, p99 latency > 5s, workflow failure rate anomaly, queue depth growth.
- **Evidence**: `server/src/main/resources/application.properties` (metrics enabled, no alerting config), `metrics/` module (Micrometer registries), no alert rules files in repository

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No Infrastructure as Code exists in this repository. No Terraform, CloudFormation, CDK, Helm charts, or Kustomize manifests were found. The repository provides only Docker Compose files for local development orchestration. The infrastructure that would expose Conductor to agents (API gateways, IAM roles, secrets, networking) is not defined anywhere in this codebase.
- **Gap**: No IaC governance for the agent-facing integration surface. Infrastructure is either managed manually or defined in a separate, unlinked repository.
- **Compensating Controls**:
  - Docker Compose files provide reproducible local environments
  - The application is packaged as a Docker image, enabling deployment to managed container platforms
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Define the deployment infrastructure as IaC (Terraform or CDK) in this repository or a linked infrastructure repository. Include API Gateway, IAM roles, security groups, and secrets configuration.
- **Evidence**: No `.tf`, `.cfn.yaml`, `cdk.json`, `Chart.yaml`, or `kustomization.yaml` files found anywhere in the repository; only `docker/docker-compose*.yaml` files exist

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The CI pipeline (`.github/workflows/ci.yml`) runs Gradle build, JUnit tests, integration tests (test-harness with Testcontainers), JaCoCo coverage, SonarCloud analysis, and Cypress UI tests. However, there are no API contract tests (no Pact, no Spring Cloud Contract), no OpenAPI spec validation in the build, and no schema comparison or breaking change detection.
- **Gap**: No API contract testing in CI. Breaking API changes (removed endpoints, changed response structures) would not be caught before production.
- **Compensating Controls**:
  - Integration tests in `test-harness/` exercise API endpoints end-to-end
  - Cypress E2E tests verify UI-facing API behavior
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenAPI spec generation and diff comparison in CI (fail on breaking changes). Consider adding Pact consumer-driven contract tests for critical workflow/task endpoints.
- **Evidence**: `.github/workflows/ci.yml` (comprehensive but no contract testing), `test-harness/` module (integration tests but not contract-specific)

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The CI/CD pipeline publishes Docker images to Docker Hub and artifacts to Maven Central. The publish workflows (`.github/workflows/publish.yml`, `publish_build.yaml`) push versioned Docker images. However, no deployment rollback mechanism is defined — no blue/green configuration, no CodeDeploy rollback triggers, no Helm rollback, no canary deployment. The repository does not define the deployment target infrastructure.
- **Gap**: No rollback capability defined. If a deployment breaks agent-facing APIs, there is no automated mechanism to revert to the previous version.
- **Compensating Controls**:
  - Versioned Docker images on Docker Hub allow manual rollback by re-deploying the previous tag
  - The application's stateless REST layer (state is in external DB) simplifies rollback
- **Remediation Timeline**: 60 days
- **Recommendation**: Define deployment with rollback capability (blue/green via CodeDeploy, Kubernetes rollback, or traffic shifting at load balancer). Include health-check-based automatic rollback triggers.
- **Evidence**: `.github/workflows/publish.yml` (Docker Hub push), `.github/workflows/publish_build.yaml` (versioned artifacts), no deployment/rollback configuration

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No encryption at rest configuration exists in the repository. There are no KMS key references, no encryption configuration for the supported data stores (Redis, PostgreSQL, MySQL, Elasticsearch, SQLite), and no field-level encryption. SSL/TLS support exists for transport (Redis, AMQP, Elasticsearch connections), but data at rest is unencrypted.
- **Gap**: No encryption at rest for workflow/task data stored in persistent backends. Agent-accessible workflow data (which may contain sensitive input/output) is stored unencrypted.
- **Compensating Controls**:
  - Database-level encryption can be enabled at the infrastructure layer (RDS encryption, encrypted EBS volumes) without application changes
  - SSL/TLS for transport protects data in transit
- **Remediation Timeline**: 30 days
- **Recommendation**: Enable encryption at rest at the infrastructure level (RDS encrypted instances, Redis encryption at rest, encrypted S3 buckets for any file storage). Document the encryption configuration in IaC.
- **Evidence**: `server/src/main/resources/application.properties` (no encryption config), `docker/server/config/config-redis.properties` (SSL for transport only), no KMS references in any file

---

## INFOs — Architecture and Design Inputs

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Internal deduplication exists: `dedupAndAddTasks()` prevents duplicate task scheduling within a workflow using `referenceTaskName + retryCount`. Distributed locking (`ExecutionLockService`) prevents concurrent workflow decide loops. However, there is no HTTP-level idempotency key support (no `Idempotency-Key` header handling).
- **Implication**: If agent scope is expanded to write-enabled, the lack of HTTP-level idempotency would become a BLOCKER. Agent retries on `POST /api/workflow` could create duplicate workflows.
- **Recommendation**: Plan for idempotency key support in write endpoints (especially `POST /api/workflow` and task update endpoints) before expanding agent scope.
- **Evidence**: `core/src/main/java/com/netflix/conductor/core/execution/WorkflowExecutorOps.java` (dedupAndAddTasks), no idempotency key handling in REST controllers

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: All API responses are structured JSON (`application/json` content type). The gRPC interface uses Protocol Buffers. Response structures are well-defined with consistent Java POJO serialization via Jackson.
- **Implication**: JSON responses are ideal for LLM consumption. No additional parsing logic needed for agent tool integration.
- **Recommendation**: No action needed. JSON is the optimal format for agent consumption.
- **Evidence**: `rest/src/main/java/com/netflix/conductor/rest/controllers/WorkflowResource.java` (produces APPLICATION_JSON_VALUE), `grpc/src/main/proto/` (protobuf for gRPC)

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limit headers are returned in API responses. No `X-RateLimit-Remaining` or `Retry-After` headers. Task-level rate limiting is documented per `TaskDef` configuration but HTTP-level rate limits are not documented or signaled.
- **Implication**: Agents cannot self-throttle based on rate limit signals. If an API Gateway with rate limits is deployed in front, it should return these headers.
- **Recommendation**: When implementing API-level rate limiting (STATE-Q5), include rate limit headers in responses.
- **Evidence**: REST controllers return no rate limit headers; no throttling middleware configured

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO (orchestrator has multi-step operations, but read-only scope does not trigger write concerns)
- **Finding**: Conductor has built-in workflow lifecycle operations: retry (re-execute failed tasks), restart (reset from beginning), rerun (re-execute from specific point), and terminate. Failure workflows can be defined per workflow definition to handle cleanup. However, there is no explicit saga/compensation pattern — recovery is achieved through retry/restart semantics rather than compensating transactions.
- **Implication**: If agent scope is expanded to write-enabled, the lack of explicit compensation for agent-initiated multi-step actions should be evaluated as a BLOCKER.
- **Recommendation**: For write-enabled scope, define explicit compensation logic for agent-initiated workflow operations (e.g., if an agent starts a workflow and it needs to be undone, what cleanup occurs?).
- **Evidence**: `core/src/main/java/com/netflix/conductor/core/execution/WorkflowExecutorOps.java` (retry, restart, rerun, terminate methods), workflow definition `failureWorkflow` field

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Distributed locking via `ExecutionLockService` (Redisson, Postgres, local implementations) prevents concurrent workflow decide loops. Task-level concurrency limits exist via `ConcurrentExecutionLimitDAO`. Database deadlock retry (3 attempts) handles concurrent write conflicts.
- **Implication**: Strong concurrency controls exist for the workflow execution engine. If agents expand to write scope, these controls provide good protection.
- **Recommendation**: No immediate action. The existing concurrency controls are well-designed for the orchestration use case.
- **Evidence**: `redis-lock/` module (Redisson), `core/src/main/java/com/netflix/conductor/core/execution/` (ExecutionLockService), `redis-concurrency-limit/` module

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Task-level rate limiting (`rateLimitPerFrequency`) and concurrency limits (`concurrentExecLimit`) exist per TaskDef. Bulk operations (`WorkflowBulkResource`) exist but have no configurable maximum batch size. No per-agent transaction limits.
- **Implication**: If agents gain write access, the bulk endpoints (bulk pause/resume/restart/retry/terminate/delete) could affect large numbers of workflows in a single call.
- **Recommendation**: Before enabling write scope, add configurable maximum batch sizes on bulk endpoints and per-agent operation limits.
- **Evidence**: `rest/src/main/java/com/netflix/conductor/rest/controllers/WorkflowBulkResource.java`, `common/src/main/java/com/netflix/conductor/common/metadata/tasks/TaskDef.java` (rateLimitPerFrequency)

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Workflow state includes PAUSED status. Workflows can be started in a paused state or paused mid-execution. This provides a partial draft/approval pattern — a workflow can be created and paused before full execution.
- **Implication**: The PAUSED state could serve as an approval gate for write-enabled agents in the future.
- **Recommendation**: No immediate action for read-only scope.
- **Evidence**: `core/src/main/java/com/netflix/conductor/model/WorkflowModel.java` (Status.PAUSED)

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Conductor supports HUMAN tasks (task type `HUMAN`) that explicitly wait for human input/approval before proceeding. Workflows can include WAIT tasks that pause until an external signal. These are configurable per workflow definition.
- **Implication**: Built-in HUMAN task type provides native approval gate capability for write-enabled agent workflows.
- **Recommendation**: No immediate action for read-only scope. The HUMAN task type is a strong foundation for future agent approval workflows.
- **Evidence**: `core/src/main/java/com/netflix/conductor/core/execution/tasks/` (task type implementations), workflow definition schema supports HUMAN task type

### DATA-Q2: Data Residency and Sovereignty ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY normally, but downgraded to INFO because no data residency constraints are evident in the codebase. Conductor is a self-hosted workflow engine with configurable backends — data residency is determined by the deployment infrastructure, not the application itself.
- **Finding**: Conductor stores workflow/task data in configurable backends (PostgreSQL, Redis, MySQL, Elasticsearch). No data residency requirements are documented. No region-specific configurations exist. Data residency is entirely determined by where the infrastructure is deployed.
- **Implication**: Data residency compliance is an infrastructure concern for this self-hosted application. Agents reading workflow data must ensure the deployment region matches their compliance requirements.
- **Recommendation**: Document data residency requirements in the deployment infrastructure. Ensure the chosen persistence backends are deployed in compliant regions.
- **Evidence**: `server/src/main/resources/application.properties` (configurable backends, no region constraints), `docker/docker-compose*.yaml` (local deployment only)

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality scores, completeness metrics, or freshness SLAs exist. Workflow and task data is stored as JSON blobs with minimal validation beyond JSON Schema constraints.
- **Implication**: Agents reading workflow data cannot assess data quality or completeness programmatically.
- **Recommendation**: Consider adding data quality monitoring for agent-consumed data (workflow completion rates, task failure rates as quality signals).
- **Evidence**: `schemas/` (JSON Schema validation), no data quality monitoring configuration

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: Rich custom metrics exist via the `Monitors` class: workflow start count, completion rate, failure rate, execution time, task queue depth, poll rates, and error counts. These are published via Micrometer to configurable backends (Prometheus, CloudWatch, Datadog, etc.).
- **Implication**: Good foundation for tracking agent-driven workflow outcomes. The metrics can answer "are agent-initiated workflows succeeding?" without additional instrumentation.
- **Recommendation**: Define agent-specific metric dimensions (tag by caller identity once AUTH-Q1 is resolved) to distinguish agent-initiated workflows from human-initiated ones.
- **Evidence**: `core/src/main/java/com/netflix/conductor/metrics/Monitors.java`, `server/src/main/resources/application.properties` (14 metrics backends configured)

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: PASS (no finding)
- **Finding**: Conductor exposes a comprehensive, well-documented REST API with 10 controllers covering workflow lifecycle, task management, metadata CRUD, admin operations, events, scheduling, and health checks. All endpoints are under `/api/` prefix with Swagger/OpenAPI annotations (`@Operation`). A gRPC interface is also available via 32 proto files. The API is the primary integration surface — no direct database access or file-based exchange is required.
- **Gap**: None — the API surface is well-defined and documented.
- **Recommendation**: None.
- **Evidence**: `rest/src/main/java/com/netflix/conductor/rest/controllers/` (10 REST controllers), `grpc/src/main/proto/` (32 proto files), `schemas/` (4 JSON Schema files)

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: Runtime-generated OpenAPI via springdoc-openapi-starter-webmvc-ui. No static spec file committed. Proto files provide static gRPC contracts.
- **Gap**: No version-controlled static OpenAPI spec file.
- **Recommendation**: Add Gradle task to export OpenAPI spec at build time.
- **Evidence**: `rest/build.gradle`, `grpc/src/main/proto/`

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: Well-implemented `ErrorResponse` with status, message, instance, and retryable fields. Missing explicit error code field.
- **Gap**: No machine-readable error code enum — relies on HTTP status + message text.
- **Recommendation**: Add errorCode field to ErrorResponse.
- **Evidence**: `rest/src/main/java/com/netflix/conductor/rest/controllers/ApplicationExceptionMapper.java`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Internal deduplication exists but no HTTP-level idempotency key support.
- **Gap**: No `Idempotency-Key` header handling on write endpoints.
- **Recommendation**: Plan idempotency before expanding to write scope.
- **Evidence**: `core/src/main/java/com/netflix/conductor/core/execution/WorkflowExecutorOps.java`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: All responses are structured JSON. gRPC uses Protocol Buffers. Ideal for agent consumption.
- **Gap**: None.
- **Recommendation**: No action needed.
- **Evidence**: REST controllers produce `APPLICATION_JSON_VALUE`

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `orchestrator`, agent_scope: `read-only`.
- **Trigger**: Service has operations >30s OR long-running workflows
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `orchestrator`, agent_scope: `read-only`.
- **Trigger**: Service has state changes (stateful-crud, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit headers returned in responses.
- **Gap**: Agents cannot self-throttle based on rate limit signals.
- **Recommendation**: Include rate limit headers when implementing STATE-Q5.
- **Evidence**: REST controllers return no rate limit headers

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: No authentication mechanism exists. All API endpoints are completely open. No Spring Security, no OAuth2, no JWT, no API key authentication.
- **Gap**: No machine identity authentication of any kind.
- **Recommendation**: Implement OAuth2 resource server or API key authentication with principal attribution.
- **Evidence**: `rest/build.gradle` (no security dependency), all REST controllers (no auth annotations)

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: No authorization model. Every caller has full access to all operations.
- **Gap**: Cannot scope agent access to specific operations or resources.
- **Recommendation**: Implement role-based scoped permissions after AUTH-Q1.
- **Evidence**: No `@PreAuthorize` annotations, no Spring Security configuration

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization. Cannot differentiate read vs write vs delete permissions.
- **Gap**: Cannot allow read but deny delete on the same resource type.
- **Recommendation**: Implement method-level authorization with fine-grained roles.
- **Evidence**: REST controllers have no authorization annotations

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `orchestrator`, agent_scope: `read-only`.
- **Trigger**: Always evaluated but INFO for orchestrator archetype due to calibration (orchestrator's primary concern is workflow coordination, not per-user data scoping)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### AUTH-Q5: Credential Management
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `orchestrator`, agent_scope: `read-only`.
- **Trigger**: Evaluated as extended for this context
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: `@Audit` annotation exists but is unprocessed (no AOP aspect). No audit log writing mechanism. No CloudTrail integration.
- **Gap**: No immutable audit logging for any operation.
- **Recommendation**: Implement the @Audit AOP aspect; integrate with immutable log store.
- **Evidence**: `common/src/main/java/com/netflix/conductor/common/metadata/Auditable.java`, `core/src/main/java/com/netflix/conductor/service/WorkflowServiceImpl.java`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: No authentication mechanism means no identity to suspend or revoke.
- **Gap**: No agent identity management or revocation capability.
- **Recommendation**: Implement identity management with revocation after AUTH-Q1.
- **Evidence**: No security framework in codebase

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Workflow retry/restart/rerun/terminate operations exist. Failure workflows provide cleanup hooks. No explicit saga compensation.
- **Gap**: No explicit compensation logic for agent-initiated operations (acceptable for read-only scope).
- **Recommendation**: Plan compensation logic before enabling write scope.
- **Evidence**: `core/src/main/java/com/netflix/conductor/core/execution/WorkflowExecutorOps.java`

#### STATE-Q2: Queryable Current State
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `orchestrator`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Strong concurrency controls: distributed locking (Redisson, Postgres), task concurrency limits, deadlock retry.
- **Gap**: None for read-only scope.
- **Recommendation**: No immediate action.
- **Evidence**: `redis-lock/` module, `redis-concurrency-limit/` module

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: Retry logic and distributed locking exist, but no circuit breaker pattern for external calls.
- **Gap**: No circuit breaker on HTTP task executor or external dependency calls.
- **Recommendation**: Add Resilience4j circuit breakers on external calls.
- **Evidence**: `http-task/` module, no `resilience4j` dependency in build files

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: Task-level rate limiting exists but no HTTP/API-level rate limiting.
- **Gap**: No API-level rate limiting to prevent agent traffic storms.
- **Recommendation**: Add API-level rate limiting or deploy behind API Gateway with throttles.
- **Evidence**: `redis-concurrency-limit/` module (task-level only), `rest/build.gradle` (no throttling dependency)

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Task-level rate/concurrency limits exist. Bulk operations have no maximum batch size. No per-agent transaction limits.
- **Gap**: Informational for read-only scope.
- **Recommendation**: Add maximum batch sizes before enabling write scope.
- **Evidence**: `rest/src/main/java/com/netflix/conductor/rest/controllers/WorkflowBulkResource.java`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `orchestrator`, agent_scope: `read-only`. Trigger requires P0 priority or critical path status.
- **Trigger**: Service is P0 priority OR is on the critical path
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Workflow PAUSED status exists. HUMAN task type provides explicit approval gates within workflows.
- **Gap**: Informational for read-only scope.
- **Recommendation**: No immediate action.
- **Evidence**: `core/src/main/java/com/netflix/conductor/model/WorkflowModel.java`

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: HUMAN task type and WAIT tasks provide native approval gates within workflow definitions.
- **Gap**: Informational for read-only scope.
- **Recommendation**: No immediate action.
- **Evidence**: Workflow definition schema, task type implementations

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: Docker Compose files provide 10 different local development environments (Redis+OpenSearch, PostgreSQL, MySQL, ES7, ES8, etc.). These serve as sandbox environments with production-equivalent architecture. Testcontainers-based integration tests provide isolated test environments. However, no dedicated staging environment with production-equivalent data shape is defined.
- **Gap**: No formally defined staging environment with production-equivalent data. Docker Compose is for development, not staging.
- **Recommendation**: Define a staging environment configuration with seed data scripts that populate realistic workflow/task definitions for agent testing.
- **Evidence**: `docker/docker-compose*.yaml` (10 local environments), `test-harness/` (Testcontainers-based testing)

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO
- **Finding**: Stage A evaluation: Conductor stores workflow and task data in persistent backends. This data includes arbitrary user-submitted JSON input/output, workflow correlation IDs, and metadata. The data is user-workflow-specific but the sensitivity depends entirely on what users put into their workflow inputs/outputs. Conductor itself does not define or store inherently sensitive data types (no PII fields, no financial instruments, no credentials in its own schema). AI provider API keys are stored as environment variables.
- **Implication**: Data sensitivity is determined by the workflow content that users define, not by Conductor's own data model. Agent-facing APIs return workflow input/output as-is without field-level filtering, because Conductor cannot know which fields are sensitive in user-defined schemas.
- **Recommendation**: For deployments handling sensitive workflow data, implement a response filter that redacts user-defined sensitive fields based on configurable rules.
- **Evidence**: `server/src/main/resources/application.properties` (AI API keys as env vars), `common/src/main/java/com/netflix/conductor/common/run/Workflow.java` (input/output as Map)

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO. Self-hosted application with no inherent residency constraints.
- **Finding**: Conductor is deployed on customer-chosen infrastructure. No data residency requirements are imposed by the application. Residency is an infrastructure deployment decision.
- **Gap**: None at the application level.
- **Recommendation**: Document data residency requirements in deployment infrastructure.
- **Evidence**: `server/src/main/resources/application.properties` (configurable backends)

#### DATA-Q3: Selective Query Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `orchestrator`, agent_scope: `read-only`.
- **Trigger**: Service has list/query endpoints with potentially unbounded results
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q4: System of Record Designations
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `orchestrator`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `orchestrator`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: No PII redaction in logs. Workflow input/output data (arbitrary user JSON) may leak into log files.
- **Gap**: No log scrubbing, no PII masking, no field-level redaction.
- **Recommendation**: Add log filter with field-level redaction for workflow input/output.
- **Evidence**: `rest/src/main/java/com/netflix/conductor/rest/controllers/ApplicationExceptionMapper.java`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality scores or completeness metrics.
- **Gap**: Informational.
- **Recommendation**: Consider data quality monitoring for agent-consumed data.
- **Evidence**: No data quality monitoring configuration

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: JSON Schema files and Proto files exist, but no API versioning or breaking change detection in CI.
- **Gap**: No versioning strategy or contract testing in pipeline.
- **Recommendation**: Add API versioning and OpenAPI diff in CI.
- **Evidence**: `schemas/`, `grpc/src/main/proto/`, `.github/workflows/ci.yml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Field names throughout the codebase are well-named and semantically meaningful: `workflowId`, `taskId`, `correlationId`, `workflowType`, `taskType`, `startTime`, `endTime`, `status`, `input`, `output`, `failedReferenceTaskNames`. No legacy abbreviations or cryptic codes.
- **Implication**: Agent tool definitions can be generated directly from the API schema without a data dictionary lookup.
- **Recommendation**: No action needed. Field naming is exemplary.
- **Evidence**: `common/src/main/java/com/netflix/conductor/common/run/Workflow.java`, `schemas/Workflow.json`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: JSON Schema files in `/schemas/` describe the core entities (Workflow, Task, WorkflowDef, TaskDef). Swagger annotations on REST controllers document endpoints. The MetadataResource provides runtime access to workflow/task definitions. No external data catalog (Glue, DataHub) integration.
- **Implication**: The metadata API (`/api/metadata`) itself serves as a runtime catalog of available workflow/task definitions — useful for agent discovery.
- **Recommendation**: Consider publishing the metadata schema to an external catalog for cross-service discovery.
- **Evidence**: `schemas/` directory, `rest/src/main/java/com/netflix/conductor/rest/controllers/MetadataResource.java`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: No distributed tracing. Non-structured logging (Log4j traditional format). Correlation ID exists as workflow model field but not in log MDC.
- **Gap**: Cannot trace agent-initiated requests; logs are not machine-parseable.
- **Recommendation**: Add OpenTelemetry instrumentation and JSON log layout.
- **Evidence**: No OpenTelemetry dependency, `docker/server/config/log4j.properties`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: Prometheus metrics with percentiles are available. No alerting thresholds configured.
- **Gap**: No alert rules for error rate spikes or latency degradation.
- **Recommendation**: Add Prometheus alert rules or CloudWatch alarms.
- **Evidence**: `server/src/main/resources/application.properties` (metrics config)

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: Rich custom metrics via Monitors class (workflow/task lifecycle, queue depth, errors).
- **Implication**: Good foundation for tracking agent-driven workflow outcomes.
- **Recommendation**: Add agent-specific metric dimensions after AUTH-Q1 is resolved.
- **Evidence**: `core/src/main/java/com/netflix/conductor/metrics/Monitors.java`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK-QUALITY
- **Finding**: No IaC in repository. Only Docker Compose for local development.
- **Gap**: No infrastructure governance for agent-facing surface.
- **Recommendation**: Define deployment infrastructure as IaC.
- **Evidence**: No `.tf`, `.cfn.yaml`, `cdk.json`, `Chart.yaml` files found

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive CI with build/test/coverage/SonarCloud. No API contract tests.
- **Gap**: No contract testing or breaking change detection for APIs.
- **Recommendation**: Add OpenAPI spec validation and contract tests.
- **Evidence**: `.github/workflows/ci.yml`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: Versioned Docker images published. No deployment rollback mechanism defined.
- **Gap**: No automated rollback capability.
- **Recommendation**: Define deployment with rollback (blue/green, canary).
- **Evidence**: `.github/workflows/publish.yml`

#### ENG-Q4: API Test Coverage
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `orchestrator`, agent_scope: `read-only`.
- **Trigger**: Always evaluated (but INFO for stateless-utility)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: RISK-QUALITY
- **Finding**: No encryption at rest configuration. SSL/TLS for transport only.
- **Gap**: Workflow/task data stored unencrypted at rest.
- **Recommendation**: Enable database-level encryption (RDS encryption, encrypted EBS).
- **Evidence**: `server/src/main/resources/application.properties`, no KMS references

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| rest/src/main/java/com/netflix/conductor/rest/controllers/ApplicationExceptionMapper.java | API-Q3, DATA-Q6 |
| rest/src/main/java/com/netflix/conductor/rest/controllers/WorkflowResource.java | API-Q1, API-Q5, AUTH-Q2, AUTH-Q3 |
| rest/src/main/java/com/netflix/conductor/rest/controllers/WorkflowBulkResource.java | STATE-Q6 |
| rest/src/main/java/com/netflix/conductor/rest/controllers/MetadataResource.java | DISC-Q3 |
| core/src/main/java/com/netflix/conductor/core/execution/WorkflowExecutorOps.java | API-Q4, STATE-Q1, STATE-Q3 |
| core/src/main/java/com/netflix/conductor/model/WorkflowModel.java | HITL-Q1, STATE-Q1 |
| core/src/main/java/com/netflix/conductor/metrics/Monitors.java | OBS-Q2, OBS-Q3 |
| core/src/main/java/com/netflix/conductor/service/WorkflowServiceImpl.java | AUTH-Q6 |
| common/src/main/java/com/netflix/conductor/common/metadata/Auditable.java | AUTH-Q6 |
| common/src/main/java/com/netflix/conductor/common/run/Workflow.java | DATA-Q1, DISC-Q2 |
| common/src/main/java/com/netflix/conductor/common/metadata/tasks/TaskDef.java | STATE-Q5, STATE-Q6 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| grpc/src/main/proto/ (32 proto files) | API-Q1, API-Q2, DISC-Q1 |
| schemas/Workflow.json | API-Q2, DISC-Q1, DISC-Q2 |
| schemas/Task.json | API-Q2, DISC-Q1 |
| schemas/WorkflowDef.json | API-Q2, DISC-Q1 |
| schemas/TaskDef.json | API-Q2, DISC-Q1 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| .github/workflows/ci.yml | ENG-Q2, DISC-Q1 |
| .github/workflows/publish.yml | ENG-Q3 |
| .github/workflows/publish_build.yaml | ENG-Q3 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| docker/docker-compose.yaml | HITL-Q3, DATA-Q2 |
| docker/server/Dockerfile | ENG-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| rest/build.gradle | API-Q2, AUTH-Q1, STATE-Q5 |
| server/build.gradle | AUTH-Q1 |
| build.gradle (root) | STATE-Q4 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| server/src/main/resources/application.properties | OBS-Q1, OBS-Q2, ENG-Q5, DATA-Q1, DATA-Q2, STATE-Q5 |
| docker/server/config/log4j.properties | OBS-Q1 |
| docker/server/config/config-redis.properties | ENG-Q5 |
