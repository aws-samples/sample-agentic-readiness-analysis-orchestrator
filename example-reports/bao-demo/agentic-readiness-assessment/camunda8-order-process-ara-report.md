# Agentic Readiness Assessment Report

**Target**: camunda8-order-process
**Date**: 2025-07-15
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Service Archetype**: stateless-utility (auto-detected)
**Agent Scope**: read-only
**Priority**: P0
**Tags**: camunda-c8, orders, zeebe
**Context**: Camunda 8 order processing with Zeebe job workers, BPMN error events, timer escalation patterns, and event subprocesses.
**Archetype Justification**: The repository contains a single Zeebe job worker (`Worker.java`) with no persistent state, no database connections, no HTTP API surface, and no downstream service calls beyond the Zeebe engine. The worker receives jobs via the Zeebe client SDK, processes them (with optional sleep for long-running simulation), and completes or fails them — a pure stateless utility pattern.

---

## Readiness Profile: Not Agent-Integrable

**BLOCKERs**: 3 | **RISK-SAFETY**: 9 | **RISK-QUALITY**: 11 | **INFOs**: 11

Exclude from agent toolset or plan major remediation before re-evaluation. This Camunda 8 Zeebe job worker has no direct API surface for agent integration, no sensitive data classification, and no machine identity authentication for inbound callers. Agent interaction with the underlying order process would need to go through the Camunda 8 / Zeebe engine APIs (outside this repository's scope), not through this worker directly.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 3 |
| RISK-SAFETY | 9 |
| RISK-QUALITY | 11 |
| INFO | 11 |
| N/A | 0 |
| Not Evaluated (extended) | 9 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 10
**Extended Questions Not Triggered**: 9
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: stateless-utility (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### API-Q1: Documented API Interface

- **Severity**: BLOCKER
- **Finding**: The application does NOT expose any REST, GraphQL, or AsyncAPI interface. `Worker.java` is a Zeebe job worker that consumes jobs from the Camunda 8 engine via the `spring-zeebe-starter` SDK. It uses `@JobWorker(type = "DoWork")` and `@JobWorker(type = "DoLongWork")` annotations to subscribe to Zeebe job types. There are no HTTP endpoints, no `@RestController`, no Express routes, no API routes of any kind. The only integration path is through the Zeebe engine's job worker protocol.
- **Gap**: Agents cannot call this service directly. There is no addressable API surface — the worker pulls jobs from Zeebe rather than accepting inbound requests. An agent would need to interact with the Camunda 8 Zeebe engine API (e.g., to start process instances, send messages, or complete user tasks) — which is outside this repository.
- **Remediation**:
  - **Immediate**: Expose a thin REST API layer (e.g., Spring `@RestController`) that wraps key operations: starting process instances, querying process status, and sending messages. Alternatively, define the agent integration surface at the Zeebe engine API level rather than at this worker level.
  - **Target State**: A documented REST or GraphQL API that agents can call to trigger and monitor order processing workflows, with the worker remaining as the backend execution engine.
  - **Estimated Effort**: Medium (2–4 weeks for REST API layer + OpenAPI spec)
  - **Dependencies**: AUTH-Q1 (the new API surface needs machine identity authentication)
- **Evidence**: `src/main/java/io/camunda/getstarted/genericWorker/Worker.java` — no HTTP endpoints; `pom.xml` — no web framework dependency (only `spring-zeebe-starter`); `README.md` — confirms worker-only architecture.

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: The application connects to Camunda 8 SaaS using OAuth2 client credentials (`clientId`/`clientSecret`) configured in `application.yml`. This authenticates the worker *to* the Zeebe engine. However, the application itself has no API surface and therefore no mechanism for authenticating inbound callers. There is no API Gateway, no OAuth2 resource server configuration, no API key validation, and no mTLS setup. The worker cannot be called by agents because it has no callable interface (see API-Q1).
- **Gap**: No machine identity authentication for inbound agent requests. Even if an API surface were added, there is currently no auth infrastructure to support it.
- **Remediation**:
  - **Immediate**: When adding the REST API surface (API-Q1 remediation), simultaneously implement OAuth2 resource server or API Gateway with API key authentication. Use Cognito, Okta, or API Gateway authorizers to authenticate agent identities.
  - **Target State**: Agent callers authenticate via OAuth2 client credentials or API keys with principal attribution in audit logs. Each agent identity is distinguishable.
  - **Estimated Effort**: Medium (2–3 weeks, concurrent with API-Q1 remediation)
  - **Dependencies**: API-Q1 (need an API surface before adding auth to it)
- **Evidence**: `src/main/resources/application.yml` — contains Zeebe client credentials (outbound auth only); `src/main/java/io/camunda/getstarted/genericWorker/Worker.java` — no security annotations, no auth middleware; `pom.xml` — no Spring Security dependency.

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: No sensitive data classification exists anywhere in the repository. The DMN decision table `decide-on-assignee.dmn` contains a hardcoded email address (`<REDACTED_EMAIL>@camunda.com`) used as the `processOwner` output for all complexity levels — this is PII (personal email). Process variables flow through the worker without any classification or access controls. The `application.yml` contains hardcoded Zeebe client credentials (clientId and clientSecret in plain text) committed to the repository.
- **Gap**: No data classification tags, no field-level encryption, no PII detection, no access controls on sensitive fields. PII (email address) is embedded directly in business rule definitions. Credentials are stored in plain text in version control.
- **Remediation**:
  - **Immediate**: (1) Remove the hardcoded email from the DMN table and replace with a role-based or parameterized assignment. (2) Rotate and remove the Zeebe client credentials from `application.yml` — move to AWS Secrets Manager or environment variables injected at runtime. (3) Add a `.gitguardian.yml` or pre-commit hook to prevent future credential commits.
  - **Target State**: All sensitive data fields (PII, credentials) are classified, tagged, and protected with appropriate access controls. Credentials are managed via secrets management with rotation.
  - **Estimated Effort**: Low (1–2 weeks for credential rotation and PII removal from DMN)
  - **Dependencies**: AUTH-Q5 (credential management remediation is a subset of this)
- **Evidence**: `BPMN_DMN/decide-on-assignee.dmn` — hardcoded email address in all 3 decision rules; `src/main/resources/application.yml` — plaintext `clientId` and `clientSecret`; No data classification files or policies found anywhere in the repository.

---

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No IAM policies, RBAC definitions, or permission scoping found in the repository. The Zeebe client credentials in `application.yml` provide access to the Camunda 8 SaaS cluster with no evidence of least-privilege configuration. The `clientId` (`DhS9SVqb8psF5YatlashhrAvVN8.058i`) appears to grant broad cluster access — there are no role restrictions, resource-level permissions, or conditional access controls defined.
- **Gap**: No mechanism to grant an agent identity read-only access to specific resources without inheriting broader privileges. All operations use the same credential set with no permission boundaries.
- **Compensating Controls**:
  - Create separate Camunda 8 API clients with minimal permissions (e.g., one for job workers, one for process start, one for task queries) and bind each agent to the appropriate client.
  - Use Camunda 8 Identity service to define fine-grained roles and assign them to specific API clients.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Define IAM/role-based permission boundaries per agent use case using Camunda 8 Identity roles. Create separate API clients per agent with minimal required permissions.
- **Evidence**: `src/main/resources/application.yml` — single set of Zeebe credentials with no scoping; No IAM policies or RBAC configurations in repository.

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization controls exist. The `Worker.java` processes any activated Zeebe job (types `DoWork` and `DoLongWork`) without permission checks — any job that matches the type subscription is executed. There is no distinction between read and write operations at the application level, no ABAC policies, and no action-level middleware.
- **Gap**: Cannot enforce that an agent may read job results but not complete tasks, or that it may trigger `DoWork` but not `DoLongWork`. All Zeebe job types are treated uniformly.
- **Compensating Controls**:
  - Implement action-level checks within the worker by inspecting process variables for an `agent_role` field and rejecting unauthorized operations.
  - Use Camunda 8 RBAC at the engine level to restrict which API clients can activate specific job types.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement authorization middleware that validates agent permissions per operation type before processing Zeebe jobs.
- **Evidence**: `src/main/java/io/camunda/getstarted/genericWorker/Worker.java` — `DoWork()` and `DoMoreWork()` methods have no authorization checks.

#### AUTH-Q5: Credential Management — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: **CRITICAL** — `application.yml` contains hardcoded Zeebe client credentials in plain text: `clientId: DhS9SVqb8psF5YatlashhrAvVN8.058i` and `clientSecret: zEG_xpsDOY0J6Di_RYPu99gRSuK70PJIqJzKO-sCrfUPLr0uJ6ssoC6ZlDmBvCE8`. These credentials are committed to the Git repository. No secrets manager (AWS Secrets Manager, HashiCorp Vault) is used. No `.env` file pattern — credentials are directly in the YAML configuration file.
- **Gap**: Hardcoded credentials in version control. No secret rotation capability. If compromised, an attacker gains full access to the Camunda 8 SaaS cluster. Any prompt injection or agent bug could potentially expose these credentials.
- **Compensating Controls**:
  - Immediately rotate the exposed Zeebe client credentials via the Camunda 8 Console.
  - Use environment variables (`ZEEBE_CLIENT_ID`, `ZEEBE_CLIENT_SECRET`) as an interim measure before implementing a secrets manager.
- **Remediation Timeline**: Immediate (credential rotation: 1 day; secrets manager integration: 1–2 weeks)
- **Recommendation**: (1) Rotate the exposed credentials immediately. (2) Remove credentials from `application.yml` and `git history`. (3) Integrate AWS Secrets Manager or Spring Cloud Vault for credential injection at runtime.
- **Evidence**: `src/main/resources/application.yml` — lines 5–6 contain plaintext `clientId` and `clientSecret`.

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No audit logging configuration found anywhere in the repository. No CloudTrail integration, no CloudWatch log configuration, no application-level audit logging. The worker uses `System.out.println` for console output — these are unstructured, non-immutable, and do not capture the authenticated principal. There is no log retention policy, no immutable log storage (S3 with object lock), and no tamper-evident logging.
- **Gap**: No audit trail for any operation. If an agent were to interact with this system, there would be no way to determine what actions were taken, by whom, or when.
- **Compensating Controls**:
  - Rely on Camunda 8 SaaS audit logs (Camunda Operate/Optimize) for process-level audit trail as an interim measure.
  - Add structured logging with SLF4J/Logback that includes principal identity, action, and timestamp.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement structured audit logging with SLF4J/Logback. Configure CloudWatch Logs or an equivalent immutable log sink. Ensure every job completion/failure logs the authenticated principal.
- **Evidence**: `src/main/java/io/camunda/getstarted/genericWorker/Worker.java` — only `System.out.println` statements; No logging framework configuration; No CloudTrail or CloudWatch configuration.

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No mechanism exists to suspend or revoke individual agent identities. The single set of Zeebe client credentials in `application.yml` is the only identity. Revoking it would disable the entire worker — there is no way to isolate a specific agent without affecting others. No API key management, no Cognito user pool, no identity provider integration for agent identities.
- **Gap**: Cannot suspend a misbehaving agent without taking down the entire worker. No granular identity management.
- **Compensating Controls**:
  - Create multiple Camunda 8 API clients (one per agent or agent group) so that individual clients can be revoked via the Camunda 8 Console without affecting others.
  - Implement a feature flag or circuit breaker that can disable specific agent behaviors at the application level.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement per-agent API client credentials with individual revocation capability via Camunda 8 Identity or an API Gateway with per-agent API keys.
- **Evidence**: `src/main/resources/application.yml` — single credential set; No identity management configuration.

#### STATE-Q1: Compensation and Rollback ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The BPMN process model (`process-five.bpmn`) includes BPMN error boundary events on the "Update External Audit" send task and timer-based escalation on the "Process Data" service task, plus a cancel event subprocess triggered by `CancelMessage`. These provide process-level compensation patterns handled by the Zeebe engine. However, the worker code itself (`Worker.java`) has no compensation or rollback logic — it either completes a job (`newCompleteCommand`) or fails it (`newFailCommand` with decremented retries) or throws a BPMN error (`newThrowErrorCommand`). There is no saga pattern, no undo endpoint, and no compensating transaction at the application code level.
- **Gap**: Compensation exists at the BPMN process level (engine-managed) but not at the application code level. If the worker completes a job that should have been rolled back, there is no application-level mechanism to undo it.
- **Compensating Controls**:
  - Rely on the Zeebe engine's BPMN-level compensation (error boundary events, cancel event subprocess) for process-level rollback.
  - Implement explicit compensation handlers in BPMN for critical service tasks.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add BPMN compensation events for critical tasks. For application-level rollback, implement idempotent job handlers with explicit undo capabilities.
- **Evidence**: `BPMN_DMN/process-five.bpmn` — error boundary event on `Activity_0hepvma`, timer events on `Activity_0ord4u7`, cancel event subprocess; `src/main/java/io/camunda/getstarted/genericWorker/Worker.java` — no compensation logic, only complete/fail/throwError.

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No rate limiting or throttling configured at any layer. No API Gateway (the service has no API surface), no WAF rules, no application-level rate limiting middleware. The Zeebe job worker protocol inherently controls job activation rate through the Zeebe engine's job activation mechanism (workers poll for jobs), but this is not an explicit rate limit — it is a pull-based concurrency model. There is no protection against a runaway agent that floods the Zeebe engine with process instance creation requests.
- **Gap**: No explicit rate limiting. If agents interact through the Zeebe engine API, there are no throttling controls defined in this repository to prevent overwhelming the worker or the process engine.
- **Compensating Controls**:
  - Configure Zeebe job worker `maxJobsActive` setting to limit concurrent job processing.
  - Add API Gateway with throttling if a REST API surface is introduced (per API-Q1 remediation).
- **Remediation Timeline**: 30–60 days (concurrent with API-Q1 remediation)
- **Recommendation**: When adding the REST API surface, include API Gateway with usage plans and throttling. Configure `maxJobsActive` on the Zeebe job worker to limit concurrency.
- **Evidence**: `src/main/java/io/camunda/getstarted/genericWorker/Worker.java` — no rate limiting; `pom.xml` — no rate limiting libraries; No API Gateway or WAF configuration.

#### DATA-Q2: Data Residency and Sovereignty ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The Zeebe cluster is configured in region `bru-2` (Brussels, Belgium) per `application.yml`. Process variables — which may include PII such as email addresses (as seen in the DMN table) — flow through the Camunda 8 SaaS platform hosted in this region. No data residency policies are documented. No assessment of whether sending process variable data to an LLM provider in a different region would violate GDPR or other data sovereignty requirements.
- **Gap**: No documented data residency requirements or compliance assessment. If an agent sends process variables containing EU-resident PII to a non-EU LLM endpoint, this could violate GDPR.
- **Compensating Controls**:
  - Document the data residency requirements for all process variables.
  - Ensure any LLM endpoint used by agents is hosted in the same region (EU) or is compliant with GDPR data transfer requirements.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Conduct a data residency assessment. Document which process variables contain PII and their residency requirements. Ensure agent architectures route data only to compliant LLM endpoints.
- **Evidence**: `src/main/resources/application.yml` — `region: bru-2`; `BPMN_DMN/decide-on-assignee.dmn` — contains PII (email address); No data residency documentation.

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The worker uses `System.out.println` for all logging — no structured logging, no PII redaction, no log scrubbing. The `DoWork` method logs process variable values (`throwError` variable) directly: `System.out.println("Lets find out if i can throw an error "+ throwError)`. The `DoMoreWork` method logs the `minutes` variable. Process variables accessed via `job.getVariablesAsMap()` could contain PII (e.g., `processOwner` email), and if any additional logging were added, those values would be printed unmasked. No log masking libraries, no regex-based PII filtering, no Amazon Macie integration.
- **Gap**: No PII redaction capability. Any process variable containing PII that is logged will appear in plain text in console output.
- **Compensating Controls**:
  - Replace `System.out.println` with SLF4J/Logback with a custom appender that masks known PII patterns (email, phone, SSN).
  - Restrict log access to authorized personnel only.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Replace all `System.out.println` with SLF4J structured logging. Implement a PII masking filter in the logging pipeline.
- **Evidence**: `src/main/java/io/camunda/getstarted/genericWorker/Worker.java` — lines using `System.out.println` with variable interpolation; No logging framework configured.

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, GraphQL schema, or Smithy files found in the repository. The Zeebe job types (`DoWork`, `DoLongWork`) are defined only in Java annotations (`@JobWorker(type = "DoWork")`) and BPMN XML (`<zeebe:taskDefinition type="DoLongWork" />`). The process variable schema (e.g., `complexity`, `throwError`, `minutes`, `processOwner`, `needsUser`) is implicit — defined only through code usage and BPMN/DMN models, not in a machine-readable specification.
- **Gap**: No machine-readable specification exists for the job worker interface. Agent tool definitions would need to be authored manually by reverse-engineering the BPMN models and Java code.
- **Compensating Controls**:
  - Create an AsyncAPI specification documenting the Zeebe job types, their input/output variable schemas, and error codes.
  - Use `bpmn-analysis.json` (already in the repo) as a starting point for documenting the process interface.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Create an AsyncAPI or OpenAPI specification for the service interface. Document all job types, input variables, output variables, and error conditions.
- **Evidence**: No `openapi.yaml`, `swagger.json`, `asyncapi.yaml`, `.graphql`, or `.smithy` files in repository; `src/main/java/io/camunda/getstarted/genericWorker/Worker.java` — job types defined only in annotations.

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The worker uses Zeebe's error handling mechanisms: `newThrowErrorCommand` with error code `"Problem"` and error message `"Something bad happened and it was your fault"`, and `newFailCommand` with decremented retries. These are Zeebe protocol-level error signals, not structured HTTP error responses. The error code `"Problem"` is a single generic code — no error taxonomy distinguishing retriable vs. terminal errors, no machine-readable error body, no error categorization.
- **Gap**: No structured error response format. A single error code (`"Problem"`) covers all business errors. No distinction between retriable and terminal failures at the application level (retries are managed by decrementing `job.getRetries()` but the error classification is opaque).
- **Compensating Controls**:
  - Define a Zeebe error code taxonomy (e.g., `VALIDATION_ERROR`, `TIMEOUT_ERROR`, `BUSINESS_RULE_VIOLATION`) with documented retry semantics.
  - Add error metadata to process variables when throwing BPMN errors.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Implement a structured error code taxonomy with distinct codes for retriable vs. terminal errors. Include error metadata in Zeebe error commands.
- **Evidence**: `src/main/java/io/camunda/getstarted/genericWorker/Worker.java` — `errorCode("Problem")` is the only error code; `newFailCommand` uses simple retry decrement.

#### API-Q6: Asynchronous Operation Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The `DoLongWork` job handler uses `TimeUnit.MINUTES.sleep(mins)` to simulate long-running operations — this blocks the worker thread for a configurable number of minutes (default 1 minute, up to the value of the `minutes` process variable). There is no async pattern — no background job submission, no polling endpoint, no webhook callback. The Zeebe engine handles the async coordination (the process instance waits for the job to complete), but the worker itself blocks synchronously. If `minutes` is set to 6 (as suggested in `README.md`), the worker thread is blocked for 6 minutes.
- **Gap**: Long-running operations block the worker thread with no async pattern. No job status API, no polling mechanism, and no webhook callback for completion notification.
- **Compensating Controls**:
  - Rely on the Zeebe engine's built-in async coordination (the process instance waits for job completion) as the async pattern — this is architecturally valid for Zeebe workflows.
  - Add worker thread pool configuration to prevent a single long-running job from blocking all other job processing.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure the Zeebe job worker thread pool to isolate long-running jobs. Consider using `@JobWorker` with `autoComplete = false` and non-blocking patterns for long operations.
- **Evidence**: `src/main/java/io/camunda/getstarted/genericWorker/Worker.java` — `TimeUnit.MINUTES.sleep(mins)` in `DoMoreWork` method; `README.md` — suggests starting with `"minutes": 6`.

#### STATE-Q7: Infrastructure Capacity for Agent Traffic — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No infrastructure capacity planning, no auto-scaling policies, no load test configurations found. The worker runs as a single Spring Boot application with no deployment configuration. No Dockerfile, no Kubernetes manifests, no ECS task definitions. The Camunda 8 SaaS cluster (`clusterId: 01a4dee5-75d1-4c74-8cfa-36070ec57c22`) is a managed service, but the worker itself has no scaling story. The `DoLongWork` handler blocks threads for minutes at a time, further limiting capacity.
- **Gap**: No capacity planning for agent-generated traffic. Single-instance worker with blocking operations would be overwhelmed by agent-speed traffic.
- **Compensating Controls**:
  - Deploy multiple worker instances with containerization (Docker/ECS/EKS) and auto-scaling based on Zeebe job backlog metrics.
  - Configure `maxJobsActive` on the Zeebe worker to match available thread capacity.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Containerize the worker, deploy to ECS/EKS with auto-scaling based on Zeebe job activation backlog. Load-test with agent-representative traffic patterns.
- **Evidence**: No Dockerfile, no Kubernetes manifests, no ECS/EKS configuration; `src/main/java/io/camunda/getstarted/genericWorker/Worker.java` — blocking `sleep()` call limits throughput.

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No sandbox or staging environment configuration found. The `application.yml` points directly to a single Camunda 8 SaaS cluster with no environment separation. No Docker Compose for local testing. No environment-specific configuration files (e.g., `application-staging.yml`, `application-dev.yml`). No seed data scripts. No synthetic data generators. The README instructs users to connect directly to a production Camunda 8 cluster.
- **Gap**: No safe environment to test agent behavior before production. The first time an agent interacts with this system, it would be against the only configured Camunda 8 cluster.
- **Compensating Controls**:
  - Create a separate Camunda 8 trial cluster for staging/testing.
  - Add Spring profiles (`application-dev.yml`, `application-staging.yml`) with separate cluster configurations.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Create environment-specific configuration profiles. Set up a dedicated staging Camunda 8 cluster for agent testing.
- **Evidence**: `src/main/resources/application.yml` — single cluster configuration; No `application-dev.yml` or `application-staging.yml`; No Docker Compose files.

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No schema versioning or API contract management. The BPMN model (`process-five.bpmn`) and DMN table (`decide-on-assignee.dmn`) have no version identifiers in filenames or metadata beyond the Camunda modeler export version. Job types (`DoWork`, `DoLongWork`) are string-based identifiers with no schema definition — a change to the job type string or expected variable schema would silently break any agent tool binding. No JSON Schema files, no Avro/Protobuf schemas, no schema registry. No breaking change detection in CI (no CI exists). No consumer-driven contract tests.
- **Gap**: Any change to BPMN process variables, job types, or DMN inputs/outputs would break agent integrations without warning. No versioning, no change detection, no contract testing.
- **Compensating Controls**:
  - Add version identifiers to BPMN/DMN file names (e.g., `process-five-v1.bpmn`).
  - Document the process variable schema in a JSON Schema file and validate it in CI.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement schema versioning for BPMN/DMN models. Create JSON Schema definitions for process variables. Add breaking change detection to CI pipeline.
- **Evidence**: `BPMN_DMN/process-five.bpmn` — no version identifier; `BPMN_DMN/decide-on-assignee.dmn` — no version identifier; No schema files in repository.

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No distributed tracing instrumentation. No OpenTelemetry SDK, no X-Ray integration, no `traceparent` header propagation. No structured logging — the worker uses only `System.out.println` and `e.printStackTrace()` for output. These are unstructured, have no JSON format, no correlation IDs, no request_id fields. When a job fails or an error is thrown, there is no trace linking the failure back to the originating process instance or the agent that triggered it.
- **Gap**: Agent-initiated requests cannot be traced end-to-end. No correlation between process instance ID, job key, and worker execution. Debugging agent-initiated failures is impossible.
- **Compensating Controls**:
  - Add SLF4J/Logback with MDC (Mapped Diagnostic Context) to include `processInstanceKey`, `jobKey`, and `jobType` in every log entry.
  - Integrate OpenTelemetry Java agent for automatic trace propagation.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Replace `System.out.println` with SLF4J structured logging. Add MDC context for Zeebe job metadata. Integrate OpenTelemetry for distributed tracing.
- **Evidence**: `src/main/java/io/camunda/getstarted/genericWorker/Worker.java` — `System.out.println` and `e.printStackTrace()` only; `pom.xml` — no logging or tracing dependencies.

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No alerting configuration of any kind. No CloudWatch alarms, no anomaly detection, no PagerDuty/OpsGenie integration, no SLO-based alerting. The worker has no health check endpoint, no metrics endpoint, no Prometheus scraping configuration. If the worker fails or becomes unresponsive, there is no automated detection or notification mechanism.
- **Gap**: Target system degradation would not be detected until agents begin failing. No proactive alerting.
- **Compensating Controls**:
  - Use Camunda 8 Operate dashboard to monitor process instance health and incident rates.
  - Add Spring Boot Actuator health endpoint and configure external monitoring.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add Spring Boot Actuator for health and metrics endpoints. Configure CloudWatch alarms or Prometheus/Grafana for error rate and latency alerting.
- **Evidence**: No alerting configuration; No monitoring configuration; `pom.xml` — no Spring Boot Actuator dependency.

#### ENG-Q1: Infrastructure Governance — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No Infrastructure as Code (IaC) files found in the repository. No Terraform, CloudFormation, CDK, Helm, Kustomize, or Ansible configurations. The Camunda 8 SaaS cluster is configured via the Camunda 8 Console (outside this repository). The worker has no deployment infrastructure defined — no Dockerfile, no ECS task definition, no Kubernetes manifests. Infrastructure changes are manual and untracked.
- **Gap**: No IaC governance. The agent-facing surface (when created) would have no code-defined infrastructure, no peer review process for infra changes, and no drift detection.
- **Compensating Controls**:
  - Define the Camunda 8 cluster configuration and worker deployment infrastructure in Terraform or CDK.
  - Implement PR-based review for all infrastructure changes.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Define deployment infrastructure as code (Terraform/CDK for AWS resources, Helm for Kubernetes). Implement IaC review requirements and drift detection.
- **Evidence**: No `.tf`, `.cfn.yaml`, `cdk.json`, `Chart.yaml`, `kustomization.yaml`, or Ansible files found in repository.

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No CI/CD configuration files found. No GitHub Actions (`.github/workflows/`), no GitLab CI (`.gitlab-ci.yml`), no Jenkinsfile, no AWS CodeBuild (`buildspec.yml`). The README instructs users to "load the project in your IDE of choice and run the Worker class" — this is a manual deployment process with no pipeline. No contract testing, no OpenAPI validation, no schema comparison tools.
- **Gap**: No automated build, test, or deployment pipeline. No mechanism to detect breaking changes before they reach production. BPMN/DMN model changes are not validated in CI.
- **Compensating Controls**:
  - Implement a minimal GitHub Actions pipeline with Maven build and BPMN schema validation.
  - Add Pact or similar contract tests for Zeebe job type interfaces.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a CI/CD pipeline (GitHub Actions recommended) with Maven build, unit tests, BPMN/DMN validation, and contract testing for job type schemas.
- **Evidence**: No `.github/`, `.gitlab-ci.yml`, `Jenkinsfile`, or `buildspec.yml` in repository; `README.md` — manual deployment instructions only.

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No deployment infrastructure, so no rollback capability exists. No blue/green deployment, no canary deployment, no CodeDeploy rollback triggers, no Helm rollback, no feature flags. The worker is run directly from an IDE per the README. BPMN/DMN models are deployed manually to the Camunda 8 Modeler — there is no automated rollback for process model deployments either.
- **Gap**: If a worker code change or BPMN model deployment breaks agent-facing behavior, there is no mechanism to roll back to the previous version within any defined timeframe.
- **Compensating Controls**:
  - Use Camunda 8's process model versioning (each deployment creates a new version) to revert to previous BPMN versions.
  - Implement blue/green deployment for the worker when containerized.
- **Remediation Timeline**: 60–90 days (dependent on ENG-Q1 infrastructure)
- **Recommendation**: Containerize the worker and deploy with rollback-capable strategies (blue/green or canary). Leverage Camunda 8 process versioning for BPMN model rollback.
- **Evidence**: No deployment configuration; `README.md` — manual "run from IDE" deployment; No Dockerfile or container orchestration.

---

## INFOs — Architecture and Design Inputs

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The application has no write API endpoints. The worker processes Zeebe jobs but does not expose any HTTP write operations. The Zeebe job completion command is inherently idempotent at the engine level (completing an already-completed job is a no-op). The BPMN error throw command is also idempotent.
- **Implication**: If the agent scope is expanded to write-enabled in the future, idempotency controls would need to be implemented on any new write endpoints. The Zeebe engine provides some inherent idempotency guarantees for job operations.
- **Recommendation**: When adding write endpoints (per API-Q1 remediation), implement idempotency keys from the start.
- **Evidence**: `src/main/java/io/camunda/getstarted/genericWorker/Worker.java` — no write endpoints; Zeebe job commands are inherently idempotent at the engine level.

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: The worker communicates with the Zeebe engine using the Zeebe client protocol — process variables are exchanged as Java `Map<String, Object>` (key-value pairs that serialize to JSON internally). The `DoWork` handler sets `variables.put("variable", "Value")` when completing a job. The format is structured (JSON-compatible Maps), but it is not a REST API response — it is Zeebe's internal variable exchange format.
- **Implication**: If a REST API layer is added (per API-Q1), responses should use structured JSON. The existing variable exchange pattern is already JSON-compatible, which simplifies the transition.
- **Recommendation**: When exposing a REST API, use JSON response format with a consistent envelope structure. The existing variable maps can be serialized directly.
- **Evidence**: `src/main/java/io/camunda/getstarted/genericWorker/Worker.java` — `HashMap<String, Object> variables` used for job completion.

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: The service has no HTTP API surface, so rate limit headers (X-RateLimit-Remaining, Retry-After) are not applicable. No API Gateway usage plans, no WAF rate rules, no rate limiting documentation. The Zeebe engine manages job activation rates internally, but this is not documented or exposed as rate limit headers to callers.
- **Implication**: When an API surface is added, rate limit headers should be included from the start. Agent frameworks can use these headers to self-throttle.
- **Recommendation**: When implementing the REST API (per API-Q1), configure API Gateway with usage plans and return standard rate limit headers.
- **Evidence**: No API surface; No rate limit configuration; No API documentation.

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: INFO
- **Finding**: No identity propagation mechanisms. No JWT parsing, no OAuth2 on-behalf-of flows, no token exchange, no user context headers. The worker operates as a single service identity (the Zeebe client credentials) with no concept of "acting on behalf of" a human user. The BPMN process has user tasks assigned to `=processOwner`, but this is task assignment within the process engine — not identity delegation from an agent. Downgraded to INFO for stateless-utility archetype — the worker processes generic jobs without user-specific data access patterns.
- **Implication**: If agents are introduced to complete user tasks on behalf of users, identity propagation would need to be implemented to ensure the agent operates within the user's permission scope.
- **Recommendation**: Plan identity propagation architecture if agents will act on behalf of users. Consider Camunda 8 Identity's user impersonation capabilities.
- **Evidence**: `src/main/java/io/camunda/getstarted/genericWorker/Worker.java` — no identity propagation; `src/main/resources/application.yml` — single service identity.

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No concurrency controls in the worker code. No optimistic locking, no ETags, no version fields, no `If-Match` headers. The worker does not write to any data store, so write-level concurrency is not directly applicable. The Zeebe engine handles job-level concurrency (each job is activated to exactly one worker), providing inherent concurrency control at the job activation level.
- **Implication**: If agent scope is expanded to write-enabled and a data store is introduced, concurrency controls would need to be added. The Zeebe engine's job activation model provides single-assignment guarantees that serve as a natural concurrency boundary for job processing.
- **Recommendation**: If write operations are added, implement optimistic locking with version fields. Rely on Zeebe's single-assignment job model for job-level concurrency.
- **Evidence**: `src/main/java/io/camunda/getstarted/genericWorker/Worker.java` — no concurrency controls; Zeebe provides job-level single-assignment.

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No transaction limits configured. No maximum records per operation, no spend limits, no delete operation caps. The worker processes jobs individually (one at a time per thread), which provides implicit blast radius limitation — each job execution is independent. However, there are no configurable limits on how many process instances an agent could start, how many jobs it could trigger, or how many operations could execute in a time window.
- **Implication**: If agent scope is expanded to write-enabled, transaction limits should be implemented to prevent cascading failures from agent errors (e.g., max 100 process instances started per hour per agent).
- **Recommendation**: When adding write capabilities, implement configurable transaction limits per agent identity at the API Gateway or application layer.
- **Evidence**: No transaction limit configuration; `src/main/java/io/camunda/getstarted/genericWorker/Worker.java` — processes jobs individually with no batch operations.

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality metrics, no completeness scoring, no freshness SLAs, no data profiling. The process variables (`complexity`, `throwError`, `minutes`) are set by the process initiator with no validation — the worker does not validate input types (e.g., `DoMoreWork` casts `minutes` to `Integer` with no null-safe handling beyond a default value of 1). The DMN table hard-codes outputs with no quality monitoring.
- **Implication**: Agents acting on process variable data have no way to assess data quality or completeness. Invalid or missing variables could cause silent failures.
- **Recommendation**: Add input validation for process variables in the worker. Consider implementing data quality checks in the BPMN process before agent-handled tasks.
- **Evidence**: `src/main/java/io/camunda/getstarted/genericWorker/Worker.java` — minimal input validation (null check for `mins` only); `BPMN_DMN/decide-on-assignee.dmn` — static output values.

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Field names are human-readable and semantically meaningful. Process variables include: `complexity` (string: "High", "Medium", "Low"), `throwError` (boolean), `minutes` (integer), `processOwner` (email string), `needsUser` (boolean), `variable` (generic). BPMN task names are descriptive: "Validate Data", "Process Data", "Decide on Assignee", "Update External Audit", "Send SLA Warning", "Manual Check", "Enter Cancellation Details". Job types `DoWork` and `DoLongWork` are readable though generic. No legacy abbreviations or coded field names.
- **Implication**: The semantic clarity of field names is a positive signal for agent integration — LLM-based agents can reason about `complexity`, `processOwner`, and `needsUser` without a data dictionary.
- **Recommendation**: Consider renaming the generic `DoWork` and `DoLongWork` job types to more descriptive names (e.g., `UpdateExternalAudit`, `ProcessOrderData`) when refactoring.
- **Evidence**: `BPMN_DMN/process-five.bpmn` — descriptive task and variable names; `BPMN_DMN/decide-on-assignee.dmn` — clear input/output labels; `src/main/java/io/camunda/getstarted/genericWorker/Worker.java` — readable variable names.

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No data catalog or metadata layer. No AWS Glue Data Catalog, no Collibra, no Alation, no DataHub. No metadata files describing what data the system holds. The `bpmn-analysis.json` file provides structural analysis of the BPMN process (tasks, dependencies, scores) but is not a data catalog — it describes the process topology, not the data semantics.
- **Implication**: Teams building agent tools against this system would need to manually discover and document data semantics by reading source code and BPMN models.
- **Recommendation**: Create a data dictionary or metadata document describing all process variables, their types, valid values, and business meaning.
- **Evidence**: `bpmn-analysis.json` — process structural analysis (not a data catalog); No data catalog configuration.

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No business outcome metrics. No `cloudwatch.put_metric_data` calls, no custom dashboards, no business KPI tracking. The worker logs execution messages to console but does not publish metrics on process completion rates, error rates by type, average processing times, or SLA adherence. The BPMN process has timer-based SLA escalation (1-minute SLA warning, 5-minute cancellation), but the outcomes of these escalations are not tracked as metrics.
- **Implication**: Without business outcome metrics, there is no way to measure whether agent interactions produce better or worse outcomes than human-driven workflows.
- **Recommendation**: Implement custom metrics for: process completion rate, average processing duration, SLA breach rate, error rate by type. Use CloudWatch custom metrics or Prometheus.
- **Evidence**: `src/main/java/io/camunda/getstarted/genericWorker/Worker.java` — no metrics publishing; `BPMN_DMN/process-five.bpmn` — SLA timers exist but outcomes not tracked.

### ENG-Q4: API Test Coverage

- **Severity**: INFO
- **Finding**: No test directory exists — no `src/test/` directory, no test classes, no test configurations. Zero automated tests of any kind: no unit tests, no integration tests, no API tests, no contract tests. The `pom.xml` has no test dependencies (no JUnit, no Mockito, no Spring Test). Evaluated as INFO for stateless-utility archetype (severity downgrade from RISK-QUALITY).
- **Implication**: Any behavior changes to the worker (job handling logic, error throwing conditions, variable processing) cannot be validated automatically. Agent tool schemas derived from this codebase have no test-based guarantees.
- **Recommendation**: Add JUnit 5 and Spring Boot Test dependencies. Create unit tests for `DoWork` and `DoMoreWork` job handlers covering normal completion, error throwing, and failure scenarios.
- **Evidence**: No `src/test/` directory; `pom.xml` — no test dependencies; No test files anywhere in repository.

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: BLOCKER
- **Finding**: The application does NOT expose any REST, GraphQL, or AsyncAPI interface. `Worker.java` is a Zeebe job worker consuming jobs from the Camunda 8 engine via `@JobWorker` annotations. No HTTP endpoints, no REST controllers, no API routes. Integration is solely through the Zeebe engine's job worker protocol.
- **Gap**: No addressable API surface for agents. Agents cannot call this service directly.
- **Recommendation**: Expose a REST API layer wrapping key operations (start process, query status, send messages) or define agent integration at the Zeebe engine API level.
- **Evidence**: `src/main/java/io/camunda/getstarted/genericWorker/Worker.java`, `pom.xml`, `README.md`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, GraphQL schema, or Smithy files found. Zeebe job types (`DoWork`, `DoLongWork`) defined only in Java annotations and BPMN XML. Process variable schema is implicit.
- **Gap**: No machine-readable specification. Agent tools must be manually authored.
- **Recommendation**: Create an AsyncAPI specification documenting job types, input/output variables, and error codes.
- **Evidence**: No API spec files in repository; `src/main/java/io/camunda/getstarted/genericWorker/Worker.java`

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: Worker uses Zeebe error handling: `newThrowErrorCommand` with error code `"Problem"` and `newFailCommand` with decremented retries. Single generic error code with no taxonomy.
- **Gap**: No structured error format. No retriable vs. terminal error distinction.
- **Recommendation**: Define a Zeebe error code taxonomy with documented retry semantics.
- **Evidence**: `src/main/java/io/camunda/getstarted/genericWorker/Worker.java`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No write API endpoints exist. Zeebe job commands are inherently idempotent at the engine level.
- **Gap**: N/A for read-only scope
- **Recommendation**: Implement idempotency keys when write endpoints are added.
- **Evidence**: `src/main/java/io/camunda/getstarted/genericWorker/Worker.java`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: Worker communicates via Zeebe protocol using Java `Map<String, Object>` (JSON-compatible). Not a REST API response format.
- **Gap**: No HTTP response format (no API surface exists)
- **Recommendation**: Use structured JSON when REST API is added.
- **Evidence**: `src/main/java/io/camunda/getstarted/genericWorker/Worker.java`

#### API-Q6: Asynchronous Operation Support
- **Severity**: RISK-QUALITY
- **Finding**: `DoLongWork` uses `TimeUnit.MINUTES.sleep(mins)` blocking the worker thread for configurable minutes. No async pattern, no polling endpoint, no webhook callback. Zeebe engine handles async coordination, but the worker blocks synchronously.
- **Gap**: Long-running operations block threads with no async pattern.
- **Recommendation**: Configure worker thread pool to isolate long-running jobs. Use non-blocking patterns for long operations.
- **Evidence**: `src/main/java/io/camunda/getstarted/genericWorker/Worker.java`, `README.md`

#### API-Q7: Event Emission for State Changes
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has state changes (stateful-crud, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No HTTP API surface, so rate limit headers are not applicable. No API Gateway usage plans or WAF rate rules. Zeebe engine manages job activation rates internally but does not expose rate limit headers.
- **Gap**: No rate limit documentation or headers.
- **Recommendation**: Configure API Gateway with usage plans and rate limit headers when REST API is added.
- **Evidence**: No API surface; No rate limit configuration

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: Application connects to Camunda 8 SaaS using OAuth2 client credentials in `application.yml` (outbound auth). No mechanism for authenticating inbound callers — no API Gateway, no OAuth2 resource server, no API key validation. Worker has no callable interface.
- **Gap**: No inbound machine identity authentication. No auth infrastructure for agent callers.
- **Recommendation**: Implement OAuth2 resource server or API Gateway with API key authentication when adding REST API surface.
- **Evidence**: `src/main/resources/application.yml`, `src/main/java/io/camunda/getstarted/genericWorker/Worker.java`, `pom.xml`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: No IAM policies, RBAC, or permission scoping. Single Zeebe client credential with broad cluster access. No least-privilege configuration.
- **Gap**: Cannot scope agent access to specific resources or operations.
- **Recommendation**: Create separate Camunda 8 API clients with minimal permissions per agent use case.
- **Evidence**: `src/main/resources/application.yml`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization. Worker processes any activated Zeebe job without permission checks. No ABAC policies, no action-level middleware.
- **Gap**: Cannot distinguish read vs. write agent operations.
- **Recommendation**: Implement authorization middleware validating agent permissions per operation type.
- **Evidence**: `src/main/java/io/camunda/getstarted/genericWorker/Worker.java`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: No identity propagation. No JWT parsing, no token exchange, no user context headers. Worker operates as a single service identity. Downgraded to INFO for stateless-utility archetype.
- **Gap**: No distinction between agent-as-self and agent-on-behalf-of-user.
- **Recommendation**: Plan identity propagation architecture if agents will act on behalf of users.
- **Evidence**: `src/main/java/io/camunda/getstarted/genericWorker/Worker.java`, `src/main/resources/application.yml`

#### AUTH-Q5: Credential Management
- **Severity**: RISK-SAFETY
- **Finding**: **CRITICAL** — `application.yml` contains hardcoded Zeebe client credentials in plain text committed to Git. No secrets manager. No vault. No `.env` file pattern.
- **Gap**: Hardcoded credentials in version control with no rotation capability.
- **Recommendation**: Immediately rotate credentials. Remove from `application.yml` and git history. Integrate AWS Secrets Manager.
- **Evidence**: `src/main/resources/application.yml` — plaintext `clientId` and `clientSecret`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No audit logging. No CloudTrail, no CloudWatch, no application-level audit logs. Only `System.out.println` statements — unstructured, non-immutable, no principal captured.
- **Gap**: No audit trail for any operation.
- **Recommendation**: Implement structured audit logging with SLF4J/Logback. Configure immutable log storage.
- **Evidence**: `src/main/java/io/camunda/getstarted/genericWorker/Worker.java`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: No mechanism to suspend individual agent identities. Single credential set — revoking it disables the entire worker.
- **Gap**: Cannot isolate a misbehaving agent without full service disruption.
- **Recommendation**: Implement per-agent API client credentials with individual revocation capability.
- **Evidence**: `src/main/resources/application.yml`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: BPMN process has error boundary events and cancel event subprocess (engine-level compensation). Worker code has no application-level compensation — only complete, fail, or throw error.
- **Gap**: No application-level rollback. Compensation exists only at BPMN process level.
- **Recommendation**: Add BPMN compensation events for critical tasks. Implement idempotent job handlers with undo capabilities.
- **Evidence**: `BPMN_DMN/process-five.bpmn`, `src/main/java/io/camunda/getstarted/genericWorker/Worker.java`

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
- **Finding**: No concurrency controls in worker code. Zeebe engine provides job-level single-assignment guarantees. No data store writes requiring locking.
- **Gap**: No application-level concurrency controls (not needed for current stateless design).
- **Recommendation**: Implement optimistic locking if write operations and data stores are added.
- **Evidence**: `src/main/java/io/camunda/getstarted/genericWorker/Worker.java`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has external dependencies (calls other services or external APIs)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No rate limiting at any layer. No API Gateway, no WAF, no application-level throttling. Zeebe job activation is pull-based but not an explicit rate limit.
- **Gap**: No protection against runaway agent loops overwhelming the worker or engine.
- **Recommendation**: Configure `maxJobsActive` on worker. Add API Gateway throttling when REST API is introduced.
- **Evidence**: `src/main/java/io/camunda/getstarted/genericWorker/Worker.java`, `pom.xml`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No transaction limits. Worker processes jobs individually, providing implicit single-job blast radius. No configurable limits on agent-initiated operations.
- **Gap**: No configurable transaction limits (informational for read-only scope).
- **Recommendation**: Implement transaction limits per agent identity when write capabilities are added.
- **Evidence**: `src/main/java/io/camunda/getstarted/genericWorker/Worker.java`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: RISK-QUALITY
- **Finding**: No capacity planning, no auto-scaling, no load tests. Single Spring Boot instance with blocking `sleep()` operations. No Dockerfile or container orchestration.
- **Gap**: Single-instance worker cannot handle agent-speed traffic.
- **Recommendation**: Containerize worker. Deploy with auto-scaling. Load-test with agent traffic patterns.
- **Evidence**: `src/main/java/io/camunda/getstarted/genericWorker/Worker.java`, `pom.xml`

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
- **Severity**: RISK-QUALITY
- **Finding**: No sandbox or staging environment. Single Camunda 8 SaaS cluster configured. No environment-specific profiles, no Docker Compose, no seed data.
- **Gap**: No safe environment for agent testing.
- **Recommendation**: Create environment-specific profiles and a dedicated staging Camunda 8 cluster.
- **Evidence**: `src/main/resources/application.yml`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: No data classification. DMN table contains hardcoded PII (email address). `application.yml` contains plaintext credentials committed to Git. No field-level encryption, no PII detection, no access controls.
- **Gap**: Unclassified PII and exposed credentials throughout the repository.
- **Recommendation**: Remove PII from DMN. Rotate and externalize credentials. Implement data classification.
- **Evidence**: `BPMN_DMN/decide-on-assignee.dmn`, `src/main/resources/application.yml`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Zeebe cluster in region `bru-2` (Brussels). Process variables with potential PII flow through Camunda 8 SaaS. No data residency policies documented.
- **Gap**: No data residency assessment. Potential GDPR risk if process variables are sent to non-EU LLM endpoints.
- **Recommendation**: Conduct data residency assessment. Ensure agent LLM endpoints comply with GDPR.
- **Evidence**: `src/main/resources/application.yml`, `BPMN_DMN/decide-on-assignee.dmn`

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
- **Finding**: Worker uses `System.out.println` with no PII redaction. Process variables (potentially containing PII) logged without masking. No structured logging, no log scrubbing middleware.
- **Gap**: No PII redaction capability in logging pipeline.
- **Recommendation**: Replace `System.out.println` with SLF4J structured logging with PII masking filters.
- **Evidence**: `src/main/java/io/camunda/getstarted/genericWorker/Worker.java`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics. Minimal input validation (null check for `minutes` only). DMN table hard-codes outputs with no quality monitoring.
- **Gap**: No data quality assessment capability.
- **Recommendation**: Add input validation for process variables. Implement data quality checks in BPMN process.
- **Evidence**: `src/main/java/io/camunda/getstarted/genericWorker/Worker.java`, `BPMN_DMN/decide-on-assignee.dmn`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: No schema versioning. BPMN/DMN files have no version identifiers. Job types are string-based with no schema definition. No breaking change detection, no contract tests, no schema registry.
- **Gap**: Changes to process variables or job types break agent integrations without warning.
- **Recommendation**: Implement schema versioning for BPMN/DMN. Create JSON Schema for process variables. Add breaking change detection to CI.
- **Evidence**: `BPMN_DMN/process-five.bpmn`, `BPMN_DMN/decide-on-assignee.dmn`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Field names are human-readable and semantically meaningful: `complexity`, `processOwner`, `needsUser`, `throwError`, `minutes`. BPMN task names are descriptive. No legacy abbreviations.
- **Gap**: Job types `DoWork` and `DoLongWork` are generic.
- **Recommendation**: Rename job types to more descriptive names when refactoring.
- **Evidence**: `BPMN_DMN/process-five.bpmn`, `BPMN_DMN/decide-on-assignee.dmn`, `src/main/java/io/camunda/getstarted/genericWorker/Worker.java`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No data catalog or metadata layer. `bpmn-analysis.json` describes process topology but not data semantics. No AWS Glue, Collibra, or DataHub.
- **Gap**: No automated data discovery for agent tool builders.
- **Recommendation**: Create a data dictionary for all process variables with types, valid values, and business meaning.
- **Evidence**: `bpmn-analysis.json`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: No distributed tracing (no OpenTelemetry, no X-Ray). No structured logging — only `System.out.println` and `e.printStackTrace()`. No correlation IDs.
- **Gap**: Agent-initiated requests cannot be traced. Debugging failures is impossible.
- **Recommendation**: Replace with SLF4J structured logging. Add MDC for Zeebe job metadata. Integrate OpenTelemetry.
- **Evidence**: `src/main/java/io/camunda/getstarted/genericWorker/Worker.java`, `pom.xml`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: No alerting configuration. No CloudWatch alarms, no anomaly detection, no PagerDuty/OpsGenie. No health check endpoint, no metrics endpoint.
- **Gap**: No proactive detection of system degradation.
- **Recommendation**: Add Spring Boot Actuator. Configure CloudWatch alarms or Prometheus/Grafana alerting.
- **Evidence**: No alerting configuration; `pom.xml`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No business outcome metrics. No custom CloudWatch metrics, no dashboards, no KPI tracking. BPMN has SLA timers but outcomes are not tracked as metrics.
- **Gap**: Cannot measure whether agent interactions produce good outcomes.
- **Recommendation**: Implement custom metrics for process completion rate, SLA breach rate, error rate by type.
- **Evidence**: `src/main/java/io/camunda/getstarted/genericWorker/Worker.java`, `BPMN_DMN/process-five.bpmn`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK-QUALITY
- **Finding**: No IaC files. No Terraform, CloudFormation, CDK, Helm. Camunda 8 SaaS managed outside this repository. No deployment infrastructure defined.
- **Gap**: No IaC governance. Manual, untracked infrastructure changes.
- **Recommendation**: Define deployment infrastructure as code. Implement IaC review and drift detection.
- **Evidence**: No IaC files in repository

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: No CI/CD configuration. No GitHub Actions, GitLab CI, Jenkinsfile, or buildspec.yml. Manual deployment from IDE per README. No contract testing.
- **Gap**: No automated pipeline. No breaking change detection.
- **Recommendation**: Create GitHub Actions pipeline with Maven build, tests, and BPMN validation.
- **Evidence**: No CI/CD configuration files; `README.md`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: No deployment infrastructure, so no rollback. No blue/green, no canary, no feature flags. Manual IDE-based deployment. BPMN models deployed manually.
- **Gap**: No rollback mechanism for any component.
- **Recommendation**: Containerize and deploy with rollback strategies. Leverage Camunda 8 process versioning.
- **Evidence**: No deployment configuration; `README.md`

#### ENG-Q4: API Test Coverage
- **Severity**: INFO
- **Finding**: No tests exist. No `src/test/` directory, no test classes, no test dependencies in `pom.xml`. Evaluated as INFO for stateless-utility archetype.
- **Gap**: Zero automated test coverage.
- **Recommendation**: Add JUnit 5 and Spring Boot Test. Create unit tests for job handlers.
- **Evidence**: No `src/test/` directory; `pom.xml`

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
| `src/main/java/io/camunda/getstarted/genericWorker/Worker.java` | API-Q1, API-Q2, API-Q3, API-Q4, API-Q5, API-Q6, API-Q8, AUTH-Q1, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q3, STATE-Q5, STATE-Q6, STATE-Q7, DATA-Q6, DATA-Q7, DISC-Q2, OBS-Q1, OBS-Q2, OBS-Q3, ENG-Q4 |

### BPMN/DMN Models
| File | Questions Referenced |
|------|---------------------|
| `BPMN_DMN/process-five.bpmn` | API-Q1, API-Q6, STATE-Q1, DISC-Q1, DISC-Q2, OBS-Q3 |
| `BPMN_DMN/decide-on-assignee.dmn` | DATA-Q1, DATA-Q2, DATA-Q7, DISC-Q1, DISC-Q2 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `pom.xml` | API-Q1, AUTH-Q1, STATE-Q5, STATE-Q7, OBS-Q1, OBS-Q2, ENG-Q4 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `src/main/resources/application.yml` | AUTH-Q1, AUTH-Q2, AUTH-Q4, AUTH-Q5, AUTH-Q6, AUTH-Q7, DATA-Q1, DATA-Q2, HITL-Q3, STATE-Q5 |
| `bpmn-analysis.json` | DISC-Q3 |

### Documentation
| File | Questions Referenced |
|------|---------------------|
| `README.md` | API-Q1, API-Q6, ENG-Q2, ENG-Q3 |

### Notable Absences
| Absent Artifact | Questions Impacted |
|----------------|-------------------|
| No IaC files (Terraform, CDK, CloudFormation, Helm) | AUTH-Q6, STATE-Q5, ENG-Q1 |
| No CI/CD configuration (GitHub Actions, Jenkinsfile, buildspec.yml) | ENG-Q2, ENG-Q3 |
| No API specification files (OpenAPI, AsyncAPI, GraphQL) | API-Q2, DISC-Q1 |
| No Dockerfile or container definitions | STATE-Q7, ENG-Q1, ENG-Q3 |
| No test directory (`src/test/`) | ENG-Q4 |
| No logging framework configuration | AUTH-Q6, DATA-Q6, OBS-Q1 |
| No alerting or monitoring configuration | OBS-Q2 |
| No environment-specific configuration files | HITL-Q3 |
