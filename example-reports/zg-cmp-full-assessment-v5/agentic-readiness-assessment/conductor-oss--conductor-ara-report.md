# Agentic Readiness Assessment Report

**Target**: conductor (monorepo — assessed as unified application service)
**Date**: 2026-04-30
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**TD Version**: agentic-readiness-assessment
**Repository Type**: monorepo
**Service Archetype**: orchestrator (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: java, workflow, orchestration
**Context**: Workflow orchestration engine originally from Netflix.
**Archetype Justification**: Conductor orchestrates multi-step workflows with SUB_WORKFLOW tasks, FORK/JOIN parallelism, dynamic forks, and fan-out to external task workers. The core engine coordinates execution across multiple downstream services and persistence backends — a textbook orchestrator archetype.

- **Surface flags**:
  - has_persistent_data_store: true
  - has_http_rpc_surface: true
  - has_auth_surface: false
  - has_write_operations: true
  - has_logging_of_user_data: true

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 2 | **RISK-SAFETY**: 8 | **RISK-QUALITY**: 11 | **INFOs**: 20

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days. The two BLOCKERs (AUTH-Q1: no authentication, DATA-Q1: no data classification) are fundamental gaps that must be addressed before any agent can safely interact with Conductor's APIs.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 2 |
| RISK-SAFETY | 8 |
| RISK-QUALITY | 11 |
| INFO | 20 |
| N/A | 0 |
| Not Evaluated (extended) | 2 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 17
**Extended Questions Not Triggered**: 2
**Questions N/A (repo_type: monorepo)**: 0
**Service Archetype**: orchestrator (auto-detected)

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: Conductor OSS ships with **no built-in authentication or authorization**. No Spring Security dependency exists in any `build.gradle`. No `@PreAuthorize`, `@Secured`, `SecurityFilterChain`, or JWT/OAuth middleware was found across 40+ sub-modules. All REST endpoints (`/api/workflow`, `/api/tasks`, `/api/metadata`, `/api/admin`, `/api/event`) and gRPC services are open and unauthenticated. The grep for `spring-security`, `JWT`, `OAuth`, `SecurityFilterChain` returned zero matches in Java source files. Any caller — human or machine — can invoke any endpoint without identity attribution.
- **Gap**: No machine identity authentication mechanism exists. An agent calling Conductor cannot be distinguished from any other caller. No principal attribution in audit logs. No API key, OAuth2 client credentials, or mTLS configuration.
- **Remediation**:
  - **Immediate**: Deploy an API Gateway (e.g., AWS API Gateway, Kong, Envoy) in front of Conductor with API key authentication and principal attribution headers. This provides machine identity without modifying Conductor's codebase.
  - **Target State**: Every API request carries an authenticated machine identity (client credentials OAuth2 or API key with principal attribution). The identity is propagated to audit logs.
  - **Estimated Effort**: Medium (API Gateway: 2–4 weeks; Spring Security integration: 4–8 weeks)
  - **Dependencies**: AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7 all depend on this — identity infrastructure is the prerequisite for scoped permissions, action-level auth, audit logging attribution, and identity suspension.
- **Evidence**: `build.gradle`, `dependencies.gradle`, `rest/src/main/java/com/netflix/conductor/rest/controllers/WorkflowResource.java`, `server/src/main/java/com/netflix/conductor/Conductor.java` — no security imports or configurations found.

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: **Stage A = Yes.** Conductor stores workflow execution data including input/output payloads (`has_persistent_data_store=true`). Workflow payloads can contain any user-defined data — the orchestrated workflows may process PII, PHI, financial records, or credentials depending on the business processes being automated. The `ApplicationExceptionMapper.java` logs exception messages including request URIs, and `has_logging_of_user_data=true` based on the logging patterns observed. **Stage B**: While Conductor provides a `maskedFields` property in `WorkflowDef` (found in `common/src/main/java/com/netflix/conductor/common/metadata/workflow/WorkflowDef.java:113`), there is no systematic data classification or tagging at the field level. No data classification tags were found in any configuration. No integration with AWS Macie or equivalent data classification tools. The `maskedFields` feature is opt-in per workflow definition and has no enforcement mechanism — workflow authors must manually specify which fields to mask.
- **Gap**: No field-level data classification or tagging system. The `maskedFields` feature is a partial control (opt-in, no enforcement, no classification taxonomy). An agent reading workflow execution data has no way to know which fields contain sensitive information.
- **Remediation**:
  - **Immediate**: Implement a data classification policy that categorizes workflow payload fields. Use the existing `maskedFields` mechanism to define mandatory masking for known-sensitive field patterns (e.g., `ssn`, `creditCard`, `password`, `email`).
  - **Target State**: Field-level data classification taxonomy applied to all workflow definitions. Enforcement mechanism that rejects workflow definitions handling sensitive data without appropriate `maskedFields` configuration. Integration with a data classification tool (e.g., Macie) for payload scanning.
  - **Estimated Effort**: High (classification taxonomy: 4–6 weeks; enforcement mechanism: 6–8 weeks; tooling integration: 8–12 weeks)
  - **Dependencies**: DATA-Q6 (PII in logs) is closely related — classification informs redaction rules.
- **Evidence**: `common/src/main/java/com/netflix/conductor/common/metadata/workflow/WorkflowDef.java` (maskedFields), `schemas/WorkflowDef.json` (maskedFields schema), `rest/src/main/java/com/netflix/conductor/rest/controllers/ApplicationExceptionMapper.java` (request URI logging).

**Note on BLOCKER count**: AUTH-Q1 and DATA-Q1 are definitive BLOCKERs. AUTH-Q6 resolves to RISK-SAFETY for read-only scope. DATA-Q2 resolves to RISK-SAFETY for read-only scope.

**Final BLOCKER count**: After applying conditional BLOCKER rules for `agent_scope=read-only`:
- AUTH-Q1: BLOCKER ✓
- DATA-Q1: BLOCKER ✓  
- API-Q4: INFO (read-only scope)
- STATE-Q1: RISK-SAFETY (read-only scope)
- AUTH-Q6: RISK-SAFETY (read-only scope)
- DATA-Q2: RISK-SAFETY (read-only scope)

---

**Readiness Profile**: With 2 BLOCKERs and 8 RISK-SAFETY findings, the readiness profile is **Remediation Required**.

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Without any authentication mechanism (AUTH-Q1), scoped permissions cannot be enforced. No IAM policies, API Gateway resource policies, or role-per-service configurations were found. No IaC (Terraform, CloudFormation, CDK) exists in the repository, so no IAM policy definitions were found. All endpoints are equally accessible to all callers.
- **Gap**: No mechanism to grant an agent identity read-only access to specific resources. Every caller has full access to every endpoint — workflow definitions, task updates, admin operations, and metadata management.
- **Compensating Controls**:
  - Deploy API Gateway with usage plans and API keys scoped to specific endpoint groups (e.g., read-only key for GET endpoints only).
  - Network-level isolation: restrict agent traffic to specific IP ranges with security groups.
- **Remediation Timeline**: 30–60 days (dependent on AUTH-Q1 resolution)
- **Recommendation**: Implement scoped API keys or IAM policies at the API Gateway layer. Define at minimum three permission scopes: read-only (GET), workflow-operator (GET + POST to workflow/execute), and admin (all operations).
- **Evidence**: `build.gradle`, `dependencies.gradle` — no Spring Security or authorization dependencies. No `.tf`, `.cfn.yaml`, or `cdk.json` files found.

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization exists. No ABAC or fine-grained RBAC definitions found. No `@PreAuthorize`, permission matrices, or action-level checks in middleware. The REST controllers (`WorkflowResource.java`, `TaskResource.java`, `MetadataResource.java`) accept all requests without any authorization check.
- **Gap**: An agent with read access cannot be prevented from also deleting workflows (`DELETE /{workflowId}`) or modifying metadata (`PUT /metadata/workflow`). No distinction between read and write permissions at the endpoint level.
- **Compensating Controls**:
  - API Gateway method-level authorization: configure different API keys or IAM policies for GET vs POST/PUT/DELETE methods.
  - Reverse proxy rules (nginx/Envoy) to block write endpoints for specific caller identities.
- **Remediation Timeline**: 30–60 days (dependent on AUTH-Q1 resolution)
- **Recommendation**: Implement method-level authorization at the API Gateway or add Spring Security with method-level security annotations to the REST controllers.
- **Evidence**: `rest/src/main/java/com/netflix/conductor/rest/controllers/WorkflowResource.java`, `MetadataResource.java`, `TaskResource.java` — no authorization annotations or checks.

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY (not BLOCKER)
- **Finding**: Conductor has an `@Audit` annotation (`core/src/main/java/com/netflix/conductor/annotations/Audit.java`) and an `Auditable` base class (`common/src/main/java/com/netflix/conductor/common/metadata/Auditable.java`) with `createdBy` and `updatedBy` fields. However, the `@Audit` annotation is a marker interface with no AOP implementation found — it does not automatically produce audit log entries. The `Auditable` fields (`createdBy`, `updatedBy`) exist on metadata objects but are not populated by any authentication context (since AUTH-Q1 shows no auth exists). No CloudTrail, CloudWatch log immutability, S3 object lock for logs, or tamper-evident log configuration was found. Log4j2 is configured but with no immutable storage target.
- **Gap**: No immutable audit trail. The `@Audit` annotation is a stub with no implementation. The `createdBy`/`updatedBy` fields are empty because there is no authenticated principal. Logs go to standard output with no immutability guarantee.
- **Compensating Controls**:
  - Route application logs to CloudWatch Logs with a retention policy and log group with immutable log settings.
  - Enable CloudTrail for API Gateway calls if a gateway is deployed.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement the `@Audit` annotation with an AOP aspect that writes structured audit events. Populate `createdBy`/`updatedBy` from authenticated principal (requires AUTH-Q1 fix first). Ship logs to immutable storage (S3 with Object Lock or CloudWatch Logs with retention policy).
- **Evidence**: `core/src/main/java/com/netflix/conductor/annotations/Audit.java` (marker only), `common/src/main/java/com/netflix/conductor/common/metadata/Auditable.java` (fields exist but unpopulated), `server/src/main/resources/application.properties` (no CloudTrail config).

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Without authentication infrastructure (AUTH-Q1), there is no mechanism to suspend or revoke individual agent identities. No API key revocation endpoints, IAM role deactivation procedures, or service account disable mechanisms were found. The only way to stop an agent would be to shut down network access entirely.
- **Gap**: Cannot isolate a misbehaving agent without affecting all other callers. No agent identity lifecycle management.
- **Compensating Controls**:
  - API Gateway API key deletion: if an API Gateway with per-agent API keys is deployed, individual keys can be revoked.
  - Network-level blocking: security group rules to block specific IP addresses.
- **Remediation Timeline**: 30–60 days (dependent on AUTH-Q1)
- **Recommendation**: Deploy identity infrastructure with per-agent API keys or service accounts, each independently revocable. Integrate with API Gateway usage plans for immediate revocation capability.
- **Evidence**: No security configuration files found across the entire codebase.

#### STATE-Q1: Compensation and Rollback ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY (not BLOCKER)
- **Finding**: Conductor has **strong built-in compensation and rollback capabilities**: (1) `failureWorkflow` property in `WorkflowDef` triggers a compensation workflow on failure; (2) `retry`, `restart`, `rerun` endpoints in `WorkflowResource.java` enable explicit recovery; (3) `TaskDef` supports configurable retry logic with `FIXED`, `EXPONENTIAL_BACKOFF`, and `LINEAR_BACKOFF` retry policies; (4) workflows can be paused and resumed. These are application-level compensation mechanisms, not infrastructure-level. However, there is no automatic compensation/saga pattern for partial multi-step failures — the `failureWorkflow` must be explicitly defined by the workflow author.
- **Gap**: Compensation is opt-in per workflow definition. If a workflow author does not define a `failureWorkflow`, partial failures leave workflows in an incomplete state. No automatic saga pattern or two-phase commit.
- **Compensating Controls**:
  - Enforce `failureWorkflow` as mandatory for all workflow definitions (can be done via validation rules).
  - Use the existing `retry` and `restart` API endpoints for manual recovery.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a validation rule requiring `failureWorkflow` for all workflow definitions that contain write operations. Document the compensation pattern for workflow authors.
- **Evidence**: `schemas/WorkflowDef.json` (failureWorkflow property), `rest/src/main/java/com/netflix/conductor/rest/controllers/WorkflowResource.java` (retry, restart, rerun endpoints), `schemas/TaskDef.json` (retryLogic, retryDelaySeconds).

#### DATA-Q2: Data Residency and Sovereignty ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY (not BLOCKER)
- **Finding**: No data residency configuration, GDPR/LGPD compliance references, or region-specific data storage configurations were found in the codebase. Conductor stores workflow execution data in configured persistence backends (Redis, Postgres, MySQL, SQLite, Cassandra, Elasticsearch) with no residency constraints defined. External payload storage (S3, Azure Blob) is configurable but has no region pinning configuration. The workflow payloads may contain data subject to residency requirements depending on the business context.
- **Gap**: No data residency controls. An agent sending workflow data to an LLM provider in a different region could create a compliance violation if the workflow processes regulated data.
- **Compensating Controls**:
  - Deploy Conductor in a single region with all persistence backends co-located.
  - Configure S3 bucket policies to enforce region restrictions on external payload storage.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document data residency requirements for the deployment environment. Configure persistence backends and external storage with explicit region constraints. Add residency metadata to workflow definitions.
- **Evidence**: `server/src/main/resources/application.properties`, `docker/server/config/config-redis.properties` — no residency configuration. `awss3-storage/` module — no region pinning.

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Conductor has task-level rate limiting (`RateLimitingDAO` interface, `RedisRateLimitingDAO` implementation, `rateLimitPerFrequency`/`rateLimitFrequencyInSeconds` in `TaskDef`, `rateLimitConfig` in `WorkflowDef`). However, **no API-level rate limiting** exists on the HTTP endpoints. No API Gateway throttling, WAF rate rules, or application-level rate limiting middleware was found. An agent could call the REST API at machine speed without any throttling.
- **Gap**: No API-level rate limiting. Task-level rate limiting only controls internal workflow execution speed, not the HTTP API surface.
- **Compensating Controls**:
  - Deploy API Gateway with throttling configuration (usage plans, rate limits per API key).
  - Add Spring Boot rate limiting middleware (e.g., Bucket4j or spring-boot-starter-cache with rate limit filter).
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Deploy API Gateway with per-agent rate limits. Configure throttling at minimum: 100 req/s per agent for read endpoints, 10 req/s for write endpoints.
- **Evidence**: `core/src/main/java/com/netflix/conductor/dao/RateLimitingDAO.java`, `redis-persistence/src/main/java/com/netflix/conductor/redis/dao/RedisRateLimitingDAO.java`, `schemas/TaskDef.json` (rateLimitPerFrequency). No API Gateway or HTTP middleware rate limiting found.

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The `ApplicationExceptionMapper.java` logs exception type and request URI but NOT request bodies. No request body logging middleware was found. Conductor provides `maskedFields` in `WorkflowDef` for field-level masking. No log scrubbing middleware, PII masking libraries, or Amazon Macie integration was found. The report declares `has_logging_of_user_data: true` — error logs include request URIs, and workflow input/output payloads are stored in the persistence layer. Per TD surface-flag calibration, the INFO downgrade for DATA-Q6 requires `has_logging_of_user_data` to be `false`; since it is `true`, RISK-SAFETY applies.
- **Gap**: No systematic PII redaction in logs. The `maskedFields` feature is opt-in and only applies to workflow payload masking, not to log output. No log scrubbing middleware exists.
- **Compensating Controls**:
  - Use the existing `maskedFields` mechanism in all workflow definitions that handle sensitive data.
  - Deploy a log scrubbing filter at the infrastructure layer (CloudWatch Logs subscription filter or Fluentd/Fluent Bit with PII redaction plugin).
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a log scrubbing filter that redacts PII patterns (emails, SSNs, credit card numbers) from all log output. Enforce `maskedFields` usage for workflow definitions handling sensitive data.
- **Evidence**: `rest/src/main/java/com/netflix/conductor/rest/controllers/ApplicationExceptionMapper.java` (error logging pattern), `common/src/main/java/com/netflix/conductor/common/metadata/workflow/WorkflowDef.java` (maskedFields).

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Conductor uses `springdoc-openapi-starter-webmvc-ui` (version `2.1.0` in `dependencies.gradle`) which auto-generates an OpenAPI specification at runtime via the `/api-docs` endpoint. All REST controllers use `@Operation` annotations from `io.swagger.v3.oas.annotations`. Additionally, gRPC `.proto` files in `grpc/src/main/proto/grpc/` provide machine-readable service definitions. JSON Schema files in `schemas/` directory (`WorkflowDef.json`, `TaskDef.json`, `Workflow.json`, `Task.json`) define data models. However, no static `openapi.yaml` or `openapi.json` file is committed to the repository.
- **Gap**: The OpenAPI spec is only available at runtime (server must be running). No static spec file for offline tool generation. No validation that the runtime spec matches actual behavior.
- **Compensating Controls**:
  - Generate a static OpenAPI spec from the running server and commit it to the repository.
  - Use gRPC `.proto` files directly for agent tool generation.
- **Remediation Timeline**: 7–14 days
- **Recommendation**: Add a CI step that starts the server, exports the OpenAPI spec from `/api-docs`, and commits it as `openapi.json` to the repository. Alternatively, use SpringDoc's build-time generation.
- **Evidence**: `dependencies.gradle` (`revSpringDoc = '2.1.0'`), `server/src/main/resources/application.properties` (`springdoc.api-docs.path=/api-docs`), `grpc/src/main/proto/grpc/workflow_service.proto`, `schemas/WorkflowDef.json`.

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Conductor implements structured error responses via `ApplicationExceptionMapper.java` and `ErrorResponse.java`. The `ErrorResponse` class includes `status` (HTTP status code), `code` (string), `message` (string), `retryable` (boolean), `validationErrors` (list), and `instance` (server hostname). The `retryable` flag is set to `true` for `TransientException` instances. This is a well-structured error model that allows agents to distinguish retriable from terminal errors.
- **Gap**: The `code` field is not consistently populated — it is set in the class but the `ApplicationExceptionMapper` only sets `status`, `message`, `instance`, and `retryable`. No standardized error code taxonomy (e.g., `WORKFLOW_NOT_FOUND`, `RATE_LIMIT_EXCEEDED`).
- **Compensating Controls**:
  - Agents can use the `retryable` boolean and HTTP status codes for retry logic.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Populate the `code` field consistently with a standardized error code taxonomy. Document error codes in the API specification.
- **Evidence**: `rest/src/main/java/com/netflix/conductor/rest/controllers/ApplicationExceptionMapper.java`, `common/src/main/java/com/netflix/conductor/common/validation/ErrorResponse.java`.

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Conductor has **partial schema versioning**: (1) `WorkflowDef` includes a `version` field and `schemaVersion` field (fixed at 2); (2) REST API has `/search` and `/search-v2` endpoint variants indicating API evolution; (3) gRPC `.proto` files are versioned via package names; (4) JSON Schema files in `schemas/` directory document data models. However, no breaking change detection tools (e.g., `buf breaking`, OpenAPI diff) are configured in CI. No consumer-driven contract tests (Pact) were found.
- **Gap**: No automated breaking change detection in CI pipeline. Schema evolution is manual. Agent tool bindings could break silently on API changes.
- **Compensating Controls**:
  - Use proto-level backward compatibility checks for gRPC.
  - Pin agent integrations to specific API versions (e.g., `/search-v2`).
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add OpenAPI diff or `buf breaking` to CI pipeline to detect breaking changes before merge. Implement consumer-driven contract tests for critical agent-facing endpoints.
- **Evidence**: `schemas/WorkflowDef.json` (version, schemaVersion), `rest/src/main/java/com/netflix/conductor/rest/controllers/WorkflowResource.java` (search vs search-v2), `grpc/src/main/proto/grpc/workflow_service.proto`.

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No OpenTelemetry SDK, AWS X-Ray instrumentation, or `traceparent` header propagation was found in any source file or dependency. Conductor uses Micrometer for metrics collection (Prometheus-compatible) but not for distributed tracing. Logging uses Log4j2 (all submodules include `log4j-core`, `log4j-api`, `log4j-slf4j-impl`). The logging output format is not confirmed to be structured JSON — no JSON log layout configuration was found in `application.properties`. The `correlationId` field exists on workflows and is propagated through execution, which provides partial request correlation.
- **Gap**: No distributed tracing. No structured JSON logging configuration. No trace ID propagation across service boundaries. The `correlationId` provides workflow-level correlation but not request-level distributed tracing.
- **Compensating Controls**:
  - Conductor's `correlationId` provides workflow-level correlation for debugging.
  - Micrometer metrics provide latency and error rate visibility.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenTelemetry Java agent or SDK integration. Configure Log4j2 JSON layout for structured logging. Propagate trace context through REST and gRPC handlers.
- **Evidence**: `build.gradle` (log4j dependencies), `dependencies.gradle` (`revMicrometer = '1.14.6'`), `server/src/main/resources/application.properties` (Prometheus metrics enabled, no tracing config).

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Conductor exposes Prometheus metrics via Spring Boot Actuator (`management.endpoints.web.exposure.include=health,info,prometheus` in `application.properties`). Micrometer is configured with percentile tracking (`management.metrics.web.server.request.autotime.percentiles=0.50,0.75,0.90,0.95,0.99`). However, no alerting configuration was found — no CloudWatch alarms, PagerDuty/OpsGenie integration, or alerting rules. Prometheus metrics are exposed but no alerting layer is configured.
- **Gap**: Metrics are collected and exposed but no alerting thresholds are configured. Target system degradation would go unnoticed until manually observed.
- **Compensating Controls**:
  - Prometheus metrics endpoint can be scraped by external monitoring tools (Grafana + Prometheus stack).
  - Spring Boot health endpoint (`/health`) provides basic health checking.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Configure Prometheus alerting rules or CloudWatch alarms for key metrics: API error rate >5%, p99 latency >5s, workflow failure rate, task queue depth. Integrate with PagerDuty or OpsGenie.
- **Evidence**: `server/src/main/resources/application.properties` (Prometheus and Micrometer config), `core/src/main/java/com/netflix/conductor/metrics/Monitors.java` (business metrics defined).

#### ENG-Q1: Infrastructure Governance — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No Infrastructure-as-Code was found. No Terraform (`.tf`), CloudFormation (`.cfn.yaml`/`.cfn.json`), CDK (`cdk.json`), Helm charts, or Kustomize configurations exist in the repository. Deployment is defined via `Dockerfile` and `docker-compose.yaml` files. The Docker configurations do not define API Gateway, IAM roles, secrets management, or network configurations — they only define the application container and its supporting services (Redis, Elasticsearch).
- **Gap**: No IaC for the agent-facing integration surface. API gateways, IAM roles, secrets, and network configurations are either absent or managed outside this repository. No peer review process for infrastructure changes. No drift detection.
- **Compensating Controls**:
  - Docker Compose provides reproducible local environments.
  - GitHub Actions CI validates code changes.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Define the deployment infrastructure (API Gateway, IAM, networking, secrets) as IaC (Terraform or CDK). Add PR-based review requirements for infrastructure changes. Implement drift detection with AWS Config.
- **Evidence**: No `.tf`, `.cfn.yaml`, `.cfn.json`, or `cdk.json` files found. `docker/server/Dockerfile`, `docker/docker-compose.yaml` provide container definitions only.

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: GitHub Actions CI pipeline (`.github/workflows/ci.yml`) runs `./gradlew build` which includes unit tests. A separate `test-harness` job runs integration tests. Test reports are published via `mikepenz/action-junit-report`. SonarCloud integration is configured for code quality analysis. However, no API contract tests (Pact), OpenAPI spec validation, or schema comparison tools were found in the CI pipeline. The build does not validate API backward compatibility.
- **Gap**: No API contract testing in CI. Breaking API changes would not be detected before production deployment.
- **Compensating Controls**:
  - REST controller tests (`WorkflowResourceTest.java`, `TaskResourceTest.java`, etc.) provide implicit contract validation.
  - Integration test harness validates end-to-end behavior.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add OpenAPI spec generation and diff checking to CI. Implement Pact consumer-driven contract tests for agent-facing endpoints.
- **Evidence**: `.github/workflows/ci.yml` (build and test steps), `rest/src/test/java/com/netflix/conductor/rest/controllers/WorkflowResourceTest.java` (controller tests exist).

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The `publish.yml` workflow builds and pushes Docker images with version tags (`conductoross/conductor:$VERSION`) and a `latest` tag. Multi-platform builds (linux/arm64, linux/amd64) are supported. However, no blue/green deployment, canary deployment, CodeDeploy rollback triggers, feature flags, or traffic shifting configuration was found. Rollback would require manually pulling a previous Docker image version.
- **Gap**: No automated rollback mechanism. A broken deployment affecting agent-facing APIs requires manual intervention to roll back to a previous version.
- **Compensating Controls**:
  - Docker image version tags enable manual rollback to any previous release.
  - GitHub Releases track all published versions.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement automated rollback via health-check-driven deployment (e.g., ECS with circuit breaker, Kubernetes rollback on failed health check). Add canary deployment for gradual rollout.
- **Evidence**: `.github/workflows/publish.yml` (Docker image tagging), `docker/server/Dockerfile` (health check defined).

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: 354 test files found across the repository. REST controller tests exist for all major resources: `WorkflowResourceTest.java`, `TaskResourceTest.java`, `MetadataResourceTest.java`, `EventResourceTest.java`, `AdminResourceTest.java`. JaCoCo code coverage is configured with aggregated reporting. The test harness provides end-to-end integration tests. Cypress E2E and component tests cover the UI. However, no API-specific contract tests (Postman/Newman, REST Assured, Pact) were found — the tests are Spring MVC mock-based controller tests, not full API integration tests.
- **Gap**: Tests validate controller logic via mocks but do not validate the full HTTP contract (serialization, headers, content negotiation). No standalone API test suite that an agent integration team could run.
- **Compensating Controls**:
  - Controller-level mock tests provide good coverage of business logic.
  - Test harness provides integration-level validation.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add Postman/Newman or REST Assured API tests that validate the full HTTP contract. Include these in CI as a separate job.
- **Evidence**: `rest/src/test/java/com/netflix/conductor/rest/controllers/WorkflowResourceTest.java`, `.github/workflows/ci.yml` (JaCoCo, test-harness job).

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Multiple Docker Compose configurations provide local development environments: `docker-compose.yaml` (Redis + Elasticsearch), `docker-compose-postgres.yaml`, `docker-compose-mysql.yaml`, `docker-compose-redis-os.yaml`, and more. The default SQLite configuration in `application.properties` enables zero-dependency local startup. A `KitchenSinkInitializer` loads sample workflows. Config files for different backends (`config-redis.properties`, `config-postgres.properties`) provide environment-specific configurations. However, no production-equivalent staging environment with realistic data shape is defined.
- **Gap**: Local dev environments exist but no staging environment with production-equivalent data shape and configuration. The first time an agent encounters production-scale data would be in production.
- **Compensating Controls**:
  - Docker Compose configurations enable realistic local testing with multiple backend combinations.
  - `KitchenSinkInitializer` provides sample workflows for basic testing.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Define a staging environment configuration with production-equivalent data shapes and synthetic workflow definitions. Create data seeding scripts that populate the staging environment with representative workflow data.
- **Evidence**: `docker/docker-compose.yaml`, `docker/docker-compose-postgres.yaml`, `server/src/main/resources/application.properties` (SQLite default).

#### ENG-Q5: Encryption at Rest — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No KMS key references, encryption-at-rest configuration, or customer-managed encryption keys were found in any configuration file, IaC, or source code. Persistence modules (Redis, Postgres, MySQL, SQLite, Elasticsearch, Cassandra) do not configure encryption at the application level — encryption at rest would depend on the deployment environment (e.g., AWS RDS encryption, EBS encryption). The S3 external storage module (`awss3-storage/`) does not configure server-side encryption.
- **Gap**: No encryption-at-rest configuration in the application. Relies entirely on infrastructure-level encryption which is not defined in this repository.
- **Compensating Controls**:
  - Enable encryption at the infrastructure layer (RDS encryption, EBS encryption, S3 default encryption) outside of the application repository.
  - Use deployment automation to enforce encryption-at-rest for all provisioned resources.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure encryption at rest for all persistence backends. For S3 external storage, enable SSE-S3 or SSE-KMS. Document encryption requirements for production deployments.
- **Evidence**: No `kms_key_id`, `SSEAlgorithm`, or encryption configuration found in any file.

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO
- **Finding**: Conductor exposes a fully documented REST API via Spring Boot `@RestController` annotations with Swagger/OpenAPI `@Operation` annotations on every endpoint. REST controllers: `WorkflowResource`, `TaskResource`, `MetadataResource`, `AdminResource`, `EventResource`, `QueueAdminResource`, `HealthCheckResource`. Additionally, gRPC service definitions in `.proto` files provide an alternative RPC interface. No gap was found — the API surface is well-documented and accessible.
- **Implication**: Conductor's API surface is well-suited for agent integration. No additional documentation effort needed for API discoverability.
- **Recommendation**: Continue maintaining `@Operation` annotations on all new endpoints.
- **Evidence**: `rest/src/main/java/com/netflix/conductor/rest/controllers/WorkflowResource.java`, `grpc/src/main/proto/grpc/workflow_service.proto`.

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Conductor's `SubWorkflowParams` schema includes `idempotencyKey` and `idempotencyStrategy` fields (`RETURN_EXISTING`, `FAIL`). The `executeWorkflow` endpoint generates a `requestId` (UUID) if not provided. However, not all write endpoints support idempotency keys — `POST /workflow` (startWorkflow) does not enforce idempotency natively.
- **Implication**: If agent scope expands to write-enabled, idempotency for all write endpoints would need to be addressed. The existing sub-workflow idempotency is a partial implementation.
- **Recommendation**: When scope expansion is planned, add idempotency key support to all POST endpoints that create state.
- **Evidence**: `schemas/WorkflowDef.json` (SubWorkflowParams.idempotencyKey), `rest/src/main/java/com/netflix/conductor/rest/controllers/WorkflowResource.java` (requestId generation).

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: All REST API responses are JSON (Spring Boot default `application/json`). gRPC services use Protocol Buffers (`proto3`). The combination provides well-structured, machine-parseable response formats ideal for agent consumption.
- **Implication**: JSON + Protobuf is an optimal response format stack for LLM-based agents. No additional parsing logic needed.
- **Recommendation**: No action required.
- **Evidence**: `rest/src/main/java/com/netflix/conductor/rest/controllers/WorkflowResource.java` (JSON produces), `grpc/src/main/proto/grpc/workflow_service.proto` (Protobuf).

### API-Q6: Asynchronous Operation Support

- **Severity**: INFO
- **Finding**: Conductor has native async support: `execute/{name}/{version}` endpoint with `waitForSeconds` parameter, polling-based task execution model, workflow status query via `GET /{workflowId}`, and `WAIT`/`HUMAN` task types for long-running pauses. The entire workflow engine is designed for async orchestration.
- **Implication**: No async gap — Conductor's core design supports long-running operations natively.
- **Recommendation**: No action required.
- **Evidence**: `rest/src/main/java/com/netflix/conductor/rest/controllers/WorkflowResource.java`, `core/src/main/java/com/netflix/conductor/core/execution/tasks/Wait.java`.

### API-Q7: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: Conductor supports event emission: `workflowStatusListenerEnabled` and `workflowStatusListenerSink` in `WorkflowDef`, `onStateChange` in `WorkflowTask`, event handler framework with SNS/SQS/Kafka/AMQP/NATS modules, and `task-status-listener`/`workflow-event-listener` modules.
- **Implication**: Rich event emission capabilities enable proactive agent patterns.
- **Recommendation**: No action required.
- **Evidence**: `schemas/WorkflowDef.json`, `rest/src/main/java/com/netflix/conductor/rest/controllers/EventResource.java`.

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: Conductor has built-in task-level rate limiting (`rateLimitPerFrequency`, `rateLimitFrequencyInSeconds` in `TaskDef`) and workflow-level rate limiting (`rateLimitConfig` in `WorkflowDef`). However, no API-level rate limit headers (`X-RateLimit-Remaining`, `Retry-After`) are returned in HTTP responses. No API Gateway throttle settings or WAF rate rules were found.
- **Implication**: Agents calling at machine speed have no way to self-throttle based on rate limit headers. The task-level rate limiting protects the workflow engine internally but not the HTTP API surface.
- **Recommendation**: Add rate limit headers to HTTP responses. Document API-level rate limits in the OpenAPI specification.
- **Evidence**: `schemas/TaskDef.json` (rateLimitPerFrequency), `schemas/WorkflowDef.json` (rateLimitConfig), `rest/src/main/java/com/netflix/conductor/rest/controllers/` (no rate limit headers).

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: INFO
- **Finding**: Conductor passes `correlationId` and `workerId` through workflow execution. The `WorkflowContext` class exists but is not used for identity propagation. No JWT parsing, OAuth2 on-behalf-of flows, or token exchange patterns were found. The `Auditable` base class has `createdBy`/`updatedBy` fields but they are not populated from an authentication context. Without AUTH-Q1, identity propagation is moot.
- **Implication**: Once authentication is implemented (AUTH-Q1 remediation), identity propagation should be designed to distinguish agent-as-self from agent-on-behalf-of-user.
- **Recommendation**: Design identity propagation as part of the AUTH-Q1 remediation. Include user context headers in the authentication flow.
- **Evidence**: `core/src/main/java/com/netflix/conductor/core/WorkflowContext.java`, `common/src/main/java/com/netflix/conductor/common/metadata/Auditable.java`.

### AUTH-Q5: Credential Management

- **Severity**: INFO
- **Finding**: AI provider API keys are configured via environment variables with empty defaults (`${OPENAI_API_KEY:}`, `${ANTHROPIC_API_KEY:}`, etc.) in `application.properties`. No hardcoded credentials (`password=`, `secret=`, `api_key=` patterns) were found in source code. No `.env` files committed to git. Redis and database passwords in Docker config files use container-internal networking (no exposed credentials). No AWS Secrets Manager or HashiCorp Vault integration was found, but no credentials are hardcoded either.
- **Implication**: Environment variable-based credential management is acceptable for development. Production deployments should use Secrets Manager.
- **Recommendation**: Integrate with AWS Secrets Manager or HashiCorp Vault for production deployments.
- **Evidence**: `server/src/main/resources/application.properties` (env var references), `docker/server/config/config-redis.properties` (container networking).

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Conductor has **robust concurrency controls**: (1) Workflow execution locking via Redis (`conductor.workflow-execution-lock.type=redis`, `workflowExecutionLockEnabled=true`); (2) Lock configuration with `lockLeaseTime=60000ms` and `lockTimeToTry=500ms`; (3) Redis-lock module provides distributed locking; (4) `concurrentExecLimit` in `TaskDef` limits concurrent task executions. These controls prevent race conditions during workflow execution.
- **Implication**: Conductor's concurrency controls are well-designed for multi-worker scenarios. When agent scope expands to write-enabled, these controls will protect against concurrent agent writes.
- **Recommendation**: No action required for read-only scope. Validate lock behavior under agent-scale concurrent reads when piloting.
- **Evidence**: `core/src/main/java/com/netflix/conductor/core/config/ConductorProperties.java` (lock config), `redis-lock/` module, `docker/server/config/config-redis.properties` (lock enabled).

### STATE-Q2: Queryable Current State

- **Severity**: INFO
- **Finding**: Conductor exposes comprehensive state query APIs: `GET /workflow/{workflowId}` (workflow status), `GET /workflow/{workflowId}/tasks` (task list with pagination), `GET /workflow/search` and `/search-v2` (search with filters), `GET /tasks/{taskId}` (task details), `GET /workflow/running/{name}` (running workflows). All state is queryable before taking action.
- **Implication**: Excellent state queryability enables agents to make informed decisions.
- **Recommendation**: No action required.
- **Evidence**: `rest/src/main/java/com/netflix/conductor/rest/controllers/WorkflowResource.java`, `TaskResource.java`.

### STATE-Q4: Circuit Breakers and Resilience

- **Severity**: INFO
- **Finding**: Conductor's `HttpTask` has configurable `connectionTimeOut` (3000ms) and `readTimeOut` (3000ms). `TaskDef` supports configurable retry logic with exponential backoff. However, no explicit circuit breaker pattern (Resilience4j, `@CircuitBreaker`) was found.
- **Implication**: Retry logic provides resilience but not circuit breaking. For agent scenarios with high call volumes, circuit breakers would prevent cascading failures.
- **Recommendation**: Add circuit breaker configuration for HTTP tasks. Consider Resilience4j integration.
- **Evidence**: `http-task/src/main/java/com/netflix/conductor/tasks/http/HttpTask.java`, `schemas/TaskDef.json`.

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Conductor has configurable payload size limits (`workflowInputPayloadSizeThreshold`, `maxWorkflowInputPayloadSizeThreshold` in `ConductorProperties.java`) and task execution log size limits (`taskExecLogSizeLimit`). The `rateLimitConfig` in `WorkflowDef` limits concurrent workflow executions. However, no configurable limits on agent-initiated actions (max records per run, max operations per session) were found.
- **Implication**: Read-only agents cannot modify records, so transaction limits are not critical. For future write-enabled scope, implement per-agent operation limits.
- **Recommendation**: When expanding to write-enabled scope, add configurable per-agent transaction limits.
- **Evidence**: `core/src/main/java/com/netflix/conductor/core/config/ConductorProperties.java` (payload limits), `schemas/WorkflowDef.json` (rateLimitConfig).

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Conductor has **excellent built-in HITL capabilities**: (1) `HUMAN` task type (`core/src/main/java/com/netflix/conductor/core/execution/tasks/Human.java`) pauses workflow execution in `IN_PROGRESS` state until a human completes the task; (2) `WAIT` task type pauses execution until a condition or duration is met; (3) Workflow `pause` and `resume` endpoints allow manual workflow control; (4) Workflows support status-based state machines with explicit state transitions.
- **Implication**: Conductor's built-in HUMAN task type provides a native approval gate pattern that agents can leverage for high-stakes operations.
- **Recommendation**: Document the HUMAN task pattern for agent integration teams.
- **Evidence**: `core/src/main/java/com/netflix/conductor/core/execution/tasks/Human.java`, `core/src/main/java/com/netflix/conductor/core/execution/tasks/Wait.java`, `rest/src/main/java/com/netflix/conductor/rest/controllers/WorkflowResource.java` (pause/resume endpoints).

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Conductor's workflow definition language supports configurable approval gates through: (1) `HUMAN` task type as explicit approval gates; (2) `WAIT` tasks with configurable conditions; (3) Workflow-level `timeoutPolicy` for automatic escalation; (4) The `onStateChange` property in `WorkflowTask` can trigger events when tasks change state. These are configurable per workflow definition, not globally.
- **Implication**: Approval gates can be inserted at any point in a workflow definition without code changes.
- **Recommendation**: No action required for read-only scope.
- **Evidence**: `schemas/WorkflowDef.json` (WorkflowTask.onStateChange, HUMAN task type), `core/src/main/java/com/netflix/conductor/core/execution/tasks/Human.java`.

### DATA-Q3: Selective Query Support

- **Severity**: INFO
- **Finding**: Excellent query support: `start`, `size`, `sort`, `freeText`, `query` parameters on search endpoints. Pagination on task lists. `GET /workflow/{workflowId}/tasks` with `start` and `count` parameters.
- **Implication**: Conductor's query capabilities prevent unbounded result sets, enabling efficient agent data retrieval.
- **Recommendation**: No action required.
- **Evidence**: `rest/src/main/java/com/netflix/conductor/rest/controllers/WorkflowResource.java`.

### DATA-Q5: Temporal Metadata and Freshness

- **Severity**: INFO
- **Finding**: `Auditable` base class provides `createTime`, `updateTime`, `createdBy`, `updatedBy` on all metadata objects. Workflow and task models include execution timestamps (`startTime`, `endTime`, `scheduledTime`, `updateTime`). Timestamps are stored as epoch milliseconds (Long). No `Cache-Control` or data freshness headers on API responses.
- **Implication**: Strong temporal metadata exists but no freshness signaling headers.
- **Recommendation**: Add `Cache-Control` headers and consider a `X-Data-Freshness` header for API responses.
- **Evidence**: `common/src/main/java/com/netflix/conductor/common/metadata/Auditable.java`.

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality dashboards, profiling reports, null rate monitoring, or data freshness SLAs were found. Conductor does not have built-in data quality metrics for workflow execution data.
- **Implication**: Agents acting on incomplete or stale workflow data would have no quality signal. Planning input for future observability improvements.
- **Recommendation**: Add data quality metrics for key entities (workflow completion rate, task success rate, payload validation error rate) to the existing Micrometer metrics.
- **Evidence**: `core/src/main/java/com/netflix/conductor/metrics/Monitors.java` (existing business metrics do not include data quality dimensions).

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Field names across Conductor's API and data models are consistently **human-readable and semantically meaningful**: `workflowId`, `taskReferenceName`, `correlationId`, `failureWorkflow`, `rateLimitPerFrequency`, `timeoutPolicy`, `retryLogic`, `concurrentExecLimit`. No legacy abbreviations or cryptic codes requiring a data dictionary were found. The JSON Schema files in `schemas/` include `description` fields for all properties.
- **Implication**: LLM-based agents can effectively reason about Conductor's data model without a separate data dictionary. Field names are self-documenting.
- **Recommendation**: Maintain the current naming conventions. No action required.
- **Evidence**: `schemas/WorkflowDef.json`, `schemas/TaskDef.json` (all properties include semantic names and descriptions).

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: Conductor has JSON Schema files in `schemas/` that describe `WorkflowDef`, `TaskDef`, `Workflow`, and `Task` data models. The `springdoc-openapi` library generates API documentation at runtime. The `schemas/README.md` provides guidance. However, no formal data catalog (AWS Glue, Collibra, DataHub), metadata registry, or API catalog was found.
- **Implication**: Schema files accelerate agent tool definition but a formal data catalog would further improve discoverability.
- **Recommendation**: Consider publishing data models to a data catalog for cross-team discoverability.
- **Evidence**: `schemas/WorkflowDef.json`, `schemas/TaskDef.json`, `schemas/Workflow.json`, `schemas/Task.json`, `schemas/README.md`.

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO (extended, always evaluated as INFO)
- **Finding**: Conductor's `Monitors.java` publishes extensive business metrics via Micrometer: `workflow_failure` (workflow termination by type), `workflow_start_success`, `workflow_start_error`, `task_poll`, `task_poll_error`, `task_update_conflict`, `task_update_error`, `workflow_completion` (by type and status), `workflow_archived`. These are genuine business outcome metrics — not just infrastructure metrics. Prometheus endpoint is enabled.
- **Implication**: Rich business metrics exist and can be leveraged for agent behavior monitoring (e.g., tracking workflow failure rates for agent-initiated workflows).
- **Recommendation**: When deploying agents, add agent-specific metric dimensions (e.g., `initiator=agent-X`) to existing metrics.
- **Evidence**: `core/src/main/java/com/netflix/conductor/metrics/Monitors.java` (workflow_failure, workflow_completion, task_poll metrics).

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: Conductor exposes a fully documented REST API via Spring Boot `@RestController` annotations with Swagger/OpenAPI `@Operation` annotations on every endpoint. REST controllers: `WorkflowResource`, `TaskResource`, `MetadataResource`, `AdminResource`, `EventResource`, `QueueAdminResource`, `HealthCheckResource`. Additionally, gRPC service definitions in `.proto` files (`workflow_service.proto`, `task_service.proto`, `metadata_service.proto`, `event_service.proto`) provide an alternative RPC interface. Integration is through documented APIs — no direct database access, file-based exchange, or UI automation required.
- **Gap**: None. The API surface is well-documented and accessible.
- **Recommendation**: Continue maintaining `@Operation` annotations on all new endpoints.
- **Evidence**: `rest/src/main/java/com/netflix/conductor/rest/controllers/WorkflowResource.java`, `grpc/src/main/proto/grpc/workflow_service.proto`.

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: Runtime OpenAPI spec via springdoc at `/api-docs`. gRPC `.proto` files committed. JSON Schema files in `schemas/`. No static `openapi.yaml`/`openapi.json` committed.
- **Gap**: No static OpenAPI spec file for offline tool generation.
- **Recommendation**: Generate and commit a static OpenAPI spec file in CI.
- **Evidence**: `dependencies.gradle` (`revSpringDoc = '2.1.0'`), `schemas/WorkflowDef.json`, `grpc/src/main/proto/grpc/`.

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: `ErrorResponse` class provides `status`, `code`, `message`, `retryable`, `validationErrors`, `instance`, `metadata`. The `retryable` boolean distinguishes transient from terminal errors. The `code` field is not consistently populated.
- **Gap**: No standardized error code taxonomy.
- **Recommendation**: Populate `code` consistently with a documented error taxonomy.
- **Evidence**: `common/src/main/java/com/netflix/conductor/common/validation/ErrorResponse.java`, `rest/src/main/java/com/netflix/conductor/rest/controllers/ApplicationExceptionMapper.java`.

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Partial idempotency: `SubWorkflowParams` has `idempotencyKey`/`idempotencyStrategy`. `executeWorkflow` generates `requestId`. Not all write endpoints support idempotency keys.
- **Gap**: Incomplete idempotency coverage on write endpoints.
- **Recommendation**: Add idempotency key support to all write endpoints before expanding to write-enabled scope.
- **Evidence**: `schemas/WorkflowDef.json` (SubWorkflowParams), `rest/src/main/java/com/netflix/conductor/rest/controllers/WorkflowResource.java`.

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: JSON (REST) and Protocol Buffers (gRPC). Both are well-structured, machine-parseable formats.
- **Gap**: None.
- **Recommendation**: No action required.
- **Evidence**: `rest/src/main/java/com/netflix/conductor/rest/controllers/WorkflowResource.java`, `grpc/src/main/proto/grpc/workflow_service.proto`.

#### API-Q6: Asynchronous Operation Support
- **Severity**: INFO (extended — triggered: orchestrator has long-running operations >30s)
- **Finding**: Conductor has native async support: (1) `execute/{name}/{version}` endpoint with `waitForSeconds` parameter for synchronous execution with timeout; (2) Polling-based task execution model — workflows are inherently async; (3) Workflow status can be queried via `GET /{workflowId}`; (4) `WAIT` and `HUMAN` task types support long-running pauses. The entire workflow engine is designed for async orchestration.
- **Gap**: None. Async patterns are a core strength.
- **Recommendation**: No action required.
- **Evidence**: `rest/src/main/java/com/netflix/conductor/rest/controllers/WorkflowResource.java` (executeWorkflow with polling), `core/src/main/java/com/netflix/conductor/core/execution/tasks/Wait.java`.

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO (extended — triggered for orchestrator with state changes)
- **Finding**: Conductor supports event emission: (1) `workflowStatusListenerEnabled` and `workflowStatusListenerSink` in `WorkflowDef` for workflow status events; (2) `onStateChange` property in `WorkflowTask` for task-level events; (3) Event handler framework (`EventResource.java`) with SNS, SQS, Kafka, AMQP, and NATS event queue modules; (4) `task-status-listener` and `workflow-event-listener` modules for webhook notifications.
- **Gap**: None. Rich event emission capabilities.
- **Recommendation**: No action required.
- **Evidence**: `schemas/WorkflowDef.json` (workflowStatusListenerSink, onStateChange), `rest/src/main/java/com/netflix/conductor/rest/controllers/EventResource.java`, `awssqs-event-queue/`, `kafka-event-queue/`.

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: Task-level rate limiting via `rateLimitPerFrequency`/`rateLimitFrequencyInSeconds`. No API-level rate limit headers or documentation.
- **Gap**: No `X-RateLimit-Remaining` or `Retry-After` headers.
- **Recommendation**: Add rate limit headers and document API-level limits.
- **Evidence**: `schemas/TaskDef.json` (rate limit fields), `rest/src/main/java/com/netflix/conductor/rest/controllers/` (no rate limit headers).

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: No authentication mechanism. No Spring Security, JWT, OAuth2, API key, or mTLS configuration. All endpoints are open.
- **Gap**: No machine identity authentication. Agent calls cannot be attributed to a principal.
- **Recommendation**: Deploy API Gateway with authentication or integrate Spring Security.
- **Evidence**: `build.gradle`, `dependencies.gradle` — no security dependencies.

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: No scoped permissions. All endpoints equally accessible to all callers. No IAM policies.
- **Gap**: Cannot grant agent read-only access to specific resources.
- **Recommendation**: Implement scoped API keys or IAM policies at the API Gateway layer.
- **Evidence**: No security configuration files found.

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization. No ABAC, RBAC, or `@PreAuthorize` annotations.
- **Gap**: Cannot distinguish read from write permissions at endpoint level.
- **Recommendation**: Implement method-level authorization.
- **Evidence**: `rest/src/main/java/com/netflix/conductor/rest/controllers/WorkflowResource.java` — no auth checks.

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: `correlationId` and `workerId` propagated but no identity context. No JWT parsing or token exchange. Moot without AUTH-Q1.
- **Gap**: No identity propagation mechanism.
- **Recommendation**: Design identity propagation as part of AUTH-Q1 remediation.
- **Evidence**: `core/src/main/java/com/netflix/conductor/core/WorkflowContext.java`.

#### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: AI API keys via environment variables with empty defaults. No hardcoded credentials. No Secrets Manager integration.
- **Gap**: No Secrets Manager integration for production.
- **Recommendation**: Integrate with Secrets Manager for production deployments.
- **Evidence**: `server/src/main/resources/application.properties` (env var references).

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: `@Audit` annotation is a marker with no AOP implementation. `Auditable` base class has `createdBy`/`updatedBy` fields but they are unpopulated. No CloudTrail or immutable log storage.
- **Gap**: No immutable audit trail.
- **Recommendation**: Implement `@Audit` AOP aspect and ship logs to immutable storage.
- **Evidence**: `core/src/main/java/com/netflix/conductor/annotations/Audit.java`, `common/src/main/java/com/netflix/conductor/common/metadata/Auditable.java`.

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: No identity suspension mechanism. No API key revocation or service account disable.
- **Gap**: Cannot isolate a misbehaving agent.
- **Recommendation**: Deploy per-agent API keys with revocation capability.
- **Evidence**: No security configuration files found.

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Strong built-in compensation: `failureWorkflow`, retry/restart/rerun endpoints, configurable retry logic (FIXED, EXPONENTIAL_BACKOFF, LINEAR_BACKOFF). Compensation is opt-in per workflow.
- **Gap**: No mandatory compensation pattern. Opt-in `failureWorkflow`.
- **Recommendation**: Enforce `failureWorkflow` for write-operation workflows.
- **Evidence**: `schemas/WorkflowDef.json` (failureWorkflow), `rest/src/main/java/com/netflix/conductor/rest/controllers/WorkflowResource.java` (retry endpoints).

#### STATE-Q2: Queryable Current State
- **Severity**: INFO (extended — triggered for orchestrator)
- **Finding**: Conductor exposes comprehensive state query APIs: `GET /workflow/{workflowId}` (workflow status), `GET /workflow/{workflowId}/tasks` (task list with pagination), `GET /workflow/search` and `/search-v2` (search with filters), `GET /tasks/{taskId}` (task details), `GET /workflow/running/{name}` (running workflows). All state is queryable before taking action.
- **Gap**: None. Excellent state queryability.
- **Recommendation**: No action required.
- **Evidence**: `rest/src/main/java/com/netflix/conductor/rest/controllers/WorkflowResource.java`, `TaskResource.java`.

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Robust concurrency controls: Redis distributed locking, `concurrentExecLimit` in `TaskDef`, workflow execution lock.
- **Gap**: None for read-only scope.
- **Recommendation**: Validate under agent-scale concurrent reads when piloting.
- **Evidence**: `core/src/main/java/com/netflix/conductor/core/config/ConductorProperties.java`, `redis-lock/` module.

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: INFO (extended — triggered for orchestrator with external dependencies)
- **Finding**: Conductor's `HttpTask` has configurable `connectionTimeOut` (3000ms) and `readTimeOut` (3000ms). `TaskDef` supports configurable retry logic with exponential backoff. However, no explicit circuit breaker pattern (Resilience4j, `@CircuitBreaker`) was found. The retry logic provides resilience but not circuit breaking (fail-fast when downstream is unhealthy).
- **Gap**: No circuit breaker pattern. Retry logic without circuit breaking can amplify downstream failures.
- **Recommendation**: Add circuit breaker configuration for HTTP tasks. Consider Resilience4j integration.
- **Evidence**: `http-task/src/main/java/com/netflix/conductor/tasks/http/HttpTask.java` (timeout config), `schemas/TaskDef.json` (retry logic).

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: Conductor has task-level rate limiting (`RateLimitingDAO` interface, `RedisRateLimitingDAO` implementation, `rateLimitPerFrequency`/`rateLimitFrequencyInSeconds` in `TaskDef`, `rateLimitConfig` in `WorkflowDef`). However, **no API-level rate limiting** exists on the HTTP endpoints. No API Gateway throttling, WAF rate rules, or application-level rate limiting middleware (`express-rate-limit` equivalent) was found. An agent could call the REST API at machine speed without any throttling.
- **Gap**: No API-level rate limiting. Task-level rate limiting only controls internal workflow execution speed, not the HTTP API surface.
- **Recommendation**: Deploy API Gateway with throttling configuration or add Spring Boot rate limiting middleware. Configure per-agent rate limits.
- **Evidence**: `core/src/main/java/com/netflix/conductor/dao/RateLimitingDAO.java`, `redis-persistence/src/main/java/com/netflix/conductor/redis/dao/RedisRateLimitingDAO.java`, `schemas/TaskDef.json` (rateLimitPerFrequency). No API Gateway or HTTP middleware rate limiting found.

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Payload size limits exist. No per-agent transaction limits.
- **Gap**: No per-agent operation limits.
- **Recommendation**: Add per-agent transaction limits for write-enabled scope expansion.
- **Evidence**: `core/src/main/java/com/netflix/conductor/core/config/ConductorProperties.java`.

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
- **Finding**: HUMAN task type, WAIT task type, pause/resume endpoints provide native draft/pending state.
- **Gap**: None.
- **Recommendation**: Document the HUMAN task pattern for agent teams.
- **Evidence**: `core/src/main/java/com/netflix/conductor/core/execution/tasks/Human.java`.

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: HUMAN task and WAIT task as configurable approval gates in workflow definitions.
- **Gap**: None.
- **Recommendation**: No action required.
- **Evidence**: `schemas/WorkflowDef.json` (WorkflowTask types).

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: Docker Compose configs for multiple backends. SQLite zero-dependency local startup. KitchenSinkInitializer for sample data. No production-equivalent staging.
- **Gap**: No staging environment with production-equivalent data shape.
- **Recommendation**: Define staging configuration with representative data.
- **Evidence**: `docker/docker-compose.yaml`, `server/src/main/resources/application.properties`.

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: Stage A = Yes (stores workflow payloads that may contain PII). Stage B: `maskedFields` is opt-in with no enforcement. No data classification taxonomy.
- **Gap**: No field-level data classification or enforcement.
- **Recommendation**: Implement classification taxonomy and enforcement mechanism.
- **Evidence**: `common/src/main/java/com/netflix/conductor/common/metadata/workflow/WorkflowDef.java` (maskedFields), `schemas/WorkflowDef.json`.

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No data residency configuration. No GDPR/LGPD references. No region pinning.
- **Gap**: No data residency controls.
- **Recommendation**: Document residency requirements and configure region constraints.
- **Evidence**: `server/src/main/resources/application.properties`, `awss3-storage/` module.

#### DATA-Q3: Selective Query Support
- **Severity**: INFO (extended — triggered for orchestrator with list/query endpoints)
- **Finding**: Excellent query support: `start`, `size`, `sort`, `freeText`, `query` parameters on search endpoints. Pagination on task lists. `GET /workflow/{workflowId}/tasks` with `start` and `count` parameters.
- **Gap**: None. Strong selective query support.
- **Recommendation**: No action required.
- **Evidence**: `rest/src/main/java/com/netflix/conductor/rest/controllers/WorkflowResource.java` (search endpoints with pagination).

#### DATA-Q4: System of Record Designations
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `orchestrator`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: INFO (extended — triggered for orchestrator)
- **Finding**: `Auditable` base class provides `createTime`, `updateTime`, `createdBy`, `updatedBy` on all metadata objects. Workflow and task models include execution timestamps (`startTime`, `endTime`, `scheduledTime`, `updateTime`). Timestamps are stored as epoch milliseconds (Long). No timezone normalization concern (epoch is timezone-agnostic). No `Cache-Control` or data freshness headers on API responses.
- **Gap**: No freshness signaling headers. No explicit consistency level indicator.
- **Recommendation**: Add `Cache-Control` headers and consider a `X-Data-Freshness` header for API responses.
- **Evidence**: `common/src/main/java/com/netflix/conductor/common/metadata/Auditable.java` (createTime, updateTime).

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: The `ApplicationExceptionMapper.java` logs exception type and request URI but NOT request bodies. No request body logging middleware was found. Conductor provides `maskedFields` in `WorkflowDef` for field-level masking. No log scrubbing middleware, PII masking libraries, or Amazon Macie integration was found. The report declares `has_logging_of_user_data: true`; per TD surface-flag calibration, the INFO downgrade for DATA-Q6 requires `has_logging_of_user_data` to be `false` — since it is `true`, RISK-SAFETY applies.
- **Gap**: No systematic PII redaction in logs. The `maskedFields` feature is opt-in and applies only to workflow payload masking, not to log output.
- **Recommendation**: Add a log scrubbing filter that redacts PII patterns from all log output. Enforce `maskedFields` usage for workflow definitions handling sensitive data.
- **Evidence**: `rest/src/main/java/com/netflix/conductor/rest/controllers/ApplicationExceptionMapper.java`, `common/src/main/java/com/netflix/conductor/common/metadata/workflow/WorkflowDef.java` (maskedFields).

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics or dashboards.
- **Gap**: No data quality signal for agents.
- **Recommendation**: Add quality metrics to Micrometer.
- **Evidence**: `core/src/main/java/com/netflix/conductor/metrics/Monitors.java`.

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: Partial versioning: `version` field in WorkflowDef, `/search-v2` endpoints, gRPC proto versions. No breaking change detection in CI.
- **Gap**: No automated breaking change detection.
- **Recommendation**: Add OpenAPI diff or `buf breaking` to CI.
- **Evidence**: `schemas/WorkflowDef.json`, `grpc/src/main/proto/grpc/workflow_service.proto`.

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: All field names are human-readable and semantically meaningful. No legacy abbreviations.
- **Gap**: None.
- **Recommendation**: Maintain current conventions.
- **Evidence**: `schemas/WorkflowDef.json`, `schemas/TaskDef.json`.

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: JSON Schema files and SpringDoc runtime documentation. No formal data catalog.
- **Gap**: No data catalog.
- **Recommendation**: Consider publishing to a data catalog.
- **Evidence**: `schemas/` directory.

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: No OpenTelemetry, X-Ray, or tracing. Log4j2 without confirmed JSON layout. `correlationId` provides partial correlation.
- **Gap**: No distributed tracing. No structured JSON logging.
- **Recommendation**: Add OpenTelemetry and configure JSON log layout.
- **Evidence**: `build.gradle` (log4j dependencies), `dependencies.gradle` (Micrometer).

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: Prometheus metrics exposed. No alerting configuration.
- **Gap**: No alerting thresholds.
- **Recommendation**: Configure Prometheus alerting rules or CloudWatch alarms.
- **Evidence**: `server/src/main/resources/application.properties`.

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: Extensive business metrics in `Monitors.java`: workflow_failure, workflow_completion, task_poll, task_update_conflict.
- **Gap**: No agent-specific metric dimensions.
- **Recommendation**: Add agent-specific dimensions when deploying agents.
- **Evidence**: `core/src/main/java/com/netflix/conductor/metrics/Monitors.java`.

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance
- **Severity**: RISK-QUALITY
- **Finding**: No IaC. Docker Compose and Dockerfile only. No API Gateway, IAM, or networking IaC.
- **Gap**: No IaC governance.
- **Recommendation**: Define deployment infrastructure as IaC.
- **Evidence**: No `.tf` or `.cfn.yaml` files found.

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: GitHub Actions CI with Gradle build, tests, SonarCloud. No API contract tests or breaking change detection.
- **Gap**: No API contract testing.
- **Recommendation**: Add OpenAPI diff and Pact contract tests to CI.
- **Evidence**: `.github/workflows/ci.yml`.

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: Docker image version tags. No automated rollback, blue/green, or canary deployment.
- **Gap**: Manual rollback only.
- **Recommendation**: Implement automated rollback with health checks.
- **Evidence**: `.github/workflows/publish.yml`.

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: 354 test files. Controller tests for all major resources. JaCoCo coverage. No standalone API contract tests.
- **Gap**: Mock-based tests only, no full HTTP contract validation.
- **Recommendation**: Add Postman/Newman or REST Assured API tests.
- **Evidence**: `rest/src/test/java/com/netflix/conductor/rest/controllers/WorkflowResourceTest.java`.

#### ENG-Q5: Encryption at Rest
- **Severity**: RISK-QUALITY (extended — triggered: persistent data stores)
- **Finding**: No KMS key references, encryption-at-rest configuration, or customer-managed encryption keys were found in any configuration file, IaC, or source code. Persistence modules (Redis, Postgres, MySQL, SQLite, Elasticsearch, Cassandra) do not configure encryption at the application level — encryption at rest would depend on the deployment environment (e.g., AWS RDS encryption, EBS encryption). The S3 external storage module (`awss3-storage/`) does not configure server-side encryption.
- **Gap**: No encryption-at-rest configuration in the application. Relies entirely on infrastructure-level encryption which is not defined in this repository.
- **Recommendation**: Configure encryption at rest for all persistence backends. For S3 external storage, enable SSE-S3 or SSE-KMS. Document encryption requirements for production deployments.
- **Evidence**: No `kms_key_id`, `SSEAlgorithm`, or encryption configuration found in any file.

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `rest/src/main/java/com/netflix/conductor/rest/controllers/WorkflowResource.java` | API-Q1, API-Q4, API-Q6, STATE-Q1, STATE-Q2, DATA-Q3 |
| `rest/src/main/java/com/netflix/conductor/rest/controllers/TaskResource.java` | API-Q1, AUTH-Q3, STATE-Q2 |
| `rest/src/main/java/com/netflix/conductor/rest/controllers/MetadataResource.java` | API-Q1, AUTH-Q3 |
| `rest/src/main/java/com/netflix/conductor/rest/controllers/EventResource.java` | API-Q1, API-Q7 |
| `rest/src/main/java/com/netflix/conductor/rest/controllers/ApplicationExceptionMapper.java` | API-Q3, DATA-Q6 |
| `common/src/main/java/com/netflix/conductor/common/validation/ErrorResponse.java` | API-Q3 |
| `common/src/main/java/com/netflix/conductor/common/metadata/Auditable.java` | AUTH-Q6, DATA-Q5 |
| `common/src/main/java/com/netflix/conductor/common/metadata/workflow/WorkflowDef.java` | DATA-Q1, DATA-Q6 |
| `core/src/main/java/com/netflix/conductor/annotations/Audit.java` | AUTH-Q6 |
| `core/src/main/java/com/netflix/conductor/core/config/ConductorProperties.java` | STATE-Q3, STATE-Q6 |
| `core/src/main/java/com/netflix/conductor/core/WorkflowContext.java` | AUTH-Q4 |
| `core/src/main/java/com/netflix/conductor/core/execution/tasks/Human.java` | HITL-Q1, HITL-Q2 |
| `core/src/main/java/com/netflix/conductor/core/execution/tasks/Wait.java` | API-Q6, HITL-Q1 |
| `core/src/main/java/com/netflix/conductor/dao/RateLimitingDAO.java` | STATE-Q5 |
| `core/src/main/java/com/netflix/conductor/metrics/Monitors.java` | OBS-Q2, OBS-Q3, DATA-Q7 |
| `http-task/src/main/java/com/netflix/conductor/tasks/http/HttpTask.java` | STATE-Q4 |
| `redis-persistence/src/main/java/com/netflix/conductor/redis/dao/RedisRateLimitingDAO.java` | STATE-Q5 |
| `server/src/main/java/com/netflix/conductor/Conductor.java` | AUTH-Q1 |
| `rest/src/test/java/com/netflix/conductor/rest/controllers/WorkflowResourceTest.java` | ENG-Q4 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `grpc/src/main/proto/grpc/workflow_service.proto` | API-Q1, API-Q2, API-Q5, DISC-Q1 |
| `grpc/src/main/proto/grpc/task_service.proto` | API-Q1, API-Q2 |
| `grpc/src/main/proto/grpc/metadata_service.proto` | API-Q1 |
| `grpc/src/main/proto/grpc/event_service.proto` | API-Q1 |
| `schemas/WorkflowDef.json` | API-Q2, API-Q4, API-Q7, API-Q8, STATE-Q1, STATE-Q6, HITL-Q2, DATA-Q1, DISC-Q1, DISC-Q2 |
| `schemas/TaskDef.json` | API-Q8, STATE-Q1, STATE-Q4, STATE-Q5, DISC-Q2 |
| `schemas/Workflow.json` | DISC-Q3 |
| `schemas/Task.json` | DISC-Q3 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/ci.yml` | ENG-Q2, ENG-Q4 |
| `.github/workflows/publish.yml` | ENG-Q3 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `docker/server/Dockerfile` | ENG-Q1, ENG-Q3 |
| `docker/docker-compose.yaml` | ENG-Q1, HITL-Q3 |
| `docker/docker-compose-postgres.yaml` | HITL-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `build.gradle` | AUTH-Q1, OBS-Q1 |
| `dependencies.gradle` | API-Q2, OBS-Q1, OBS-Q2 |
| `settings.gradle` | Discovery scan |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `server/src/main/resources/application.properties` | API-Q2, AUTH-Q5, OBS-Q2, DATA-Q2, ENG-Q5, HITL-Q3 |
| `docker/server/config/config-redis.properties` | STATE-Q3, DATA-Q2 |
| `docker/server/config/config.properties` | ENG-Q1 |
