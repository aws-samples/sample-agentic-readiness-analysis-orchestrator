# Agentic Readiness Assessment Report

**Target**: camunda-rest-service
**Date**: 2025-07-14
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Service Archetype**: orchestrator (auto-detected)
**Agent Scope**: read-only
**Priority**: P1
**Tags**: camunda-c7, rest-api, integration
**Context**: REST API integration patterns from Camunda 7 BPMN processes including HTTP connectors and Java delegates.

**Archetype Justification**: The application coordinates calls to 4 GitHub API endpoints through a BPMN workflow process (search repo, search contributors, get community profile, get repo languages), with minimal persistent state of its own (H2 embedded database for Camunda engine state only).

---

## Readiness Profile: Not Agent-Integrable

**BLOCKERs**: 3 | **RISK-SAFETY**: 9 | **RISK-QUALITY**: 18 | **INFOs**: 12

Exclude from agent toolset or plan major remediation before re-evaluation. The repository has 3 BLOCKERs (API-Q1, AUTH-Q1, DATA-Q1) which exceed the threshold for any agent deployment including pilots. Major remediation is required across API surface documentation, machine identity authentication, and data classification before this system can be considered for agent integration.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 3 |
| RISK-SAFETY | 9 |
| RISK-QUALITY | 18 |
| INFO | 12 |
| N/A | 0 |
| Not Evaluated (extended) | 1 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 18 (API-Q5, API-Q6, API-Q7, API-Q8, STATE-Q2, STATE-Q4, DATA-Q3, DATA-Q4, DATA-Q5, DATA-Q7, DISC-Q2, DISC-Q3, OBS-Q3, ENG-Q4, ENG-Q5)
**Extended Questions Not Triggered**: 1 (STATE-Q7)
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: orchestrator (auto-detected)

## BLOCKERs — Must Resolve Before Agent Deployment

### API-Q1: Documented API Interface

- **Severity**: BLOCKER
- **Finding**: The application exposes the Camunda REST API via `camunda-bpm-spring-boot-starter-rest` (version 7.16.0) at `/engine-rest`. The `SearchContributorService/service.js` connects to `http://localhost:8080/engine-rest`. No custom REST controllers are defined in the repository. While Camunda publishes its own REST API documentation externally, no API documentation is bundled or maintained in this repository. The integration surface for an agent would be the Camunda engine REST API endpoints (start process instance, query tasks, complete tasks), but there is no documented, stable application-specific API surface.
- **Gap**: No application-specific API interface is documented. The only integration surface is the generic Camunda engine REST API, which is a platform interface, not a business API. An agent integrating with this system would need to understand Camunda process semantics (process definitions, task management, variable schemas) rather than calling a clean business API.
- **Remediation**:
  - **Immediate**: Create a facade REST API layer with documented endpoints (e.g., `POST /api/repos/{owner}/{name}/check-popularity`) that abstracts the Camunda engine internals. Document the API with an OpenAPI specification.
  - **Target State**: A documented, versioned REST API with business-meaningful endpoints that agents can call without needing to understand Camunda internals.
  - **Estimated Effort**: Medium (2–4 weeks for API design + implementation + OpenAPI spec)
  - **Dependencies**: Resolving this blocker also addresses API-Q2 (machine-readable spec) if an OpenAPI spec is generated.
- **Evidence**: `CamundaApplication/pom.xml` (camunda-bpm-spring-boot-starter-rest dependency), `SearchContributorService/service.js` (baseUrl: `http://localhost:8080/engine-rest`), `README.md` (documents Camunda REST API usage)

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: No machine identity authentication is configured. The `application.yaml` contains hardcoded admin credentials (`id: demo`, `password: demo`). The Camunda REST API is exposed without any documented authentication mechanism for machine-to-machine calls. No OAuth2 client credentials flow, no API key authentication with principal attribution, no mTLS configuration found. The `SearchContributorService/service.js` connects to the Camunda engine REST API at `http://localhost:8080/engine-rest` with no authentication headers. Outbound calls to `api.github.com` are also unauthenticated.
- **Gap**: There is no mechanism to authenticate an agent identity, attribute agent actions in audit logs, or distinguish between different agent callers. The hardcoded `demo/demo` credentials are a security vulnerability — any caller with network access has full admin privileges.
- **Remediation**:
  - **Immediate**: (1) Remove hardcoded credentials from `application.yaml` and move to environment variables or a secrets manager. (2) Enable Camunda's built-in authentication filter or add Spring Security with OAuth2 client credentials support.
  - **Target State**: Machine identity authentication via OAuth2 client credentials or API keys with principal attribution. Each agent identity is uniquely identifiable in audit logs.
  - **Estimated Effort**: High (4–6 weeks including identity provider setup, auth filter configuration, and agent identity provisioning)
  - **Dependencies**: This blocker should be resolved before AUTH-Q2 (scoped permissions) and AUTH-Q6 (audit logging), as those controls depend on having an authenticated identity.
- **Evidence**: `CamundaApplication/src/main/resources/application.yaml` (hardcoded `id: demo`, `password: demo`), `SearchContributorService/service.js` (no auth headers on engine-rest calls), `CamundaApplication/src/main/java/com/example/workflow/FindGitHubRepo.java` (no auth on GitHub API calls)

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: No data classification is implemented at any level. The application processes GitHub repository metadata (repo names, owners, fork counts, contributor counts, programming languages, community health percentage) which is primarily public data. However, the Camunda engine stores process instance data — including user-submitted input (repoOwner, repoName) — in the H2 file database (`jdbc:h2:file:./camunda-h2-database`). No data classification tags exist on any data stores. No field-level encryption or column-level access controls. No PII detection tools (e.g., Amazon Macie) are configured.
- **Gap**: Without data classification, there is no formal determination of what data is sensitive and what controls are required. While the current data processed is largely public GitHub data, the lack of classification means there is no gate preventing sensitive data from entering the system unclassified as the application evolves.
- **Remediation**:
  - **Immediate**: Conduct a data classification exercise to categorize all data fields handled by the application (process variables, H2 database tables, external API response data). Tag data stores with classification levels.
  - **Target State**: All data fields classified (public, internal, confidential, restricted). Classification tags applied to database tables and process variables. Field-level access controls for any data classified as confidential or above.
  - **Estimated Effort**: Low (1–2 weeks for a demo/tutorial application with limited data types)
  - **Dependencies**: None — data classification can proceed independently.
- **Evidence**: `CamundaApplication/src/main/resources/application.yaml` (H2 database URL with no classification), `CamundaApplication/src/main/resources/static/forms/startForm.form` (repoName, repoOwner inputs), `CamundaApplication/src/main/resources/process.bpmn` (process variables: forks, contributors, healthPercentage, programingLanguages)

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No scoped permission model found. No IAM policies, role definitions, or least-privilege access controls exist in the repository. The single admin user `demo` in `application.yaml` has full Camunda admin privileges. No evidence of role-per-service or resource-level access restrictions.
- **Gap**: An agent identity cannot be granted limited access (e.g., read-only to process instances, no admin operations). Any authenticated caller inherits full admin privileges.
- **Compensating Controls**:
  - Deploy an API Gateway in front of the Camunda REST API that restricts allowed HTTP methods and paths per API key/token.
  - Use Camunda's authorization service to create granular permissions before granting agent access.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure Camunda's built-in authorization service to define roles with scoped permissions. Create an agent-specific role with read-only access to process instances and variables.
- **Evidence**: `CamundaApplication/src/main/resources/application.yaml` (single admin user with full access)

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization found. No ABAC or fine-grained RBAC definitions. No method-level authorization checks in source code. No middleware or interceptors enforcing action-level access control on the Camunda REST API.
- **Gap**: Cannot enforce that an agent can read process instance state but not delete process instances or modify variables, even within the same resource type.
- **Compensating Controls**:
  - Restrict agent access to specific API Gateway routes (e.g., only GET endpoints).
  - Use Camunda's authorization API to define permission grants per resource type and action.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement Camunda authorization with action-level grants (READ, CREATE, UPDATE, DELETE) per resource type (process instance, task, deployment). Assign agent identities read-only grants.
- **Evidence**: `CamundaApplication/src/main/java/com/example/workflow/FindGitHubRepo.java` (no auth checks), `SearchContributorService/service.js` (no auth checks)

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No audit logging configuration found. No CloudTrail integration. No immutable log storage. The only logging is basic console output via logback (`logback-test.xml`) with plain-text pattern formatting. The application uses `System.out.println(response.body())` in `FindGitHubRepo.java` and `println()` in the Groovy script, which is diagnostic output, not audit logging. No log retention policies configured.
- **Gap**: No immutable audit trail exists for any operations. Cannot determine which principal performed which action after the fact.
- **Compensating Controls**:
  - Enable Camunda's history service (already enabled by default with Spring Boot starter) to capture process execution history as a partial audit trail.
  - Ship application logs to a centralized, append-only log system (e.g., CloudWatch Logs with retention policy).
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure structured audit logging that captures authenticated principal, action, resource, and timestamp for every API call. Ship logs to an immutable store (S3 with object lock or CloudWatch Logs with retention).
- **Evidence**: `CamundaApplication/src/test/resources/logback-test.xml` (plain-text pattern, no audit format), `CamundaApplication/src/main/resources/application.yaml` (no audit logging config)

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No mechanism for suspending or revoking individual agent identities found. No API key management, no identity revocation capability, no service account disable mechanism. The only identity is the hardcoded `demo` admin user.
- **Gap**: If an agent identity exhibits anomalous behavior, there is no way to suspend it without taking down the entire application.
- **Compensating Controls**:
  - Implement API key management at an API Gateway layer where individual keys can be revoked.
  - Use Camunda's user management API to disable specific user accounts.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement API key management or OAuth2 client credentials with the ability to revoke individual agent identities. Integrate with an identity provider that supports immediate suspension.
- **Evidence**: `CamundaApplication/src/main/resources/application.yaml` (single hardcoded admin user, no key management)

#### STATE-Q1: Compensation and Rollback ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The BPMN process has partial error handling. `FindGitHubRepo.java` throws `BpmnError("NO_DOWNLOAD_OPTION")` and generic `Exception` for non-200 responses. `service.js` calls `taskService.handleBpmnError()` and `taskService.handleFailure()`. The Groovy script throws `BpmnError("error-scala-detected")` and catches `RESTClientException`. The process has an error event subprocess (`Activity_1kavuhs`) that routes to a "Look at Error" user task. Camunda supports transaction rollback via `camunda:asyncBefore` and `camunda:asyncAfter` flags (set on the start event and "Search for contributors" task). However, there are no explicit saga patterns, no undo/compensation endpoints, and no rollback of partial state beyond the BPMN engine's internal transaction mechanism.
- **Gap**: While BPMN error events provide process-level error routing, there is no application-level compensation for partial multi-step failures. If a GitHub API call succeeds but subsequent processing fails, the already-fetched data and set process variables cannot be rolled back.
- **Compensating Controls**:
  - Leverage Camunda's built-in transaction boundaries (async before/after) to isolate failure points.
  - Use the error event subprocess pattern (already present) to route all failures to human review.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement explicit compensation handlers in the BPMN process for each service task. Add BPMN compensation events to revert process variables on failure.
- **Evidence**: `CamundaApplication/src/main/resources/process.bpmn` (error event subprocess, async flags), `CamundaApplication/src/main/java/com/example/workflow/FindGitHubRepo.java` (BpmnError handling), `SearchContributorService/service.js` (handleBpmnError, handleFailure)

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No circuit breaker, retry logic, or timeout configuration found on any external dependency calls. `FindGitHubRepo.java` creates a new `HttpClient.newHttpClient()` per call with no timeout, no retry logic, and no circuit breaker. The Groovy script uses `RESTClient` from groovy-wslite with no resilience configuration. `service.js` uses `node-fetch` with basic try/catch but no circuit breaker, no retry with backoff, and no timeout. No Resilience4j, Hystrix, Polly, or equivalent resilience library found in dependencies.
- **Gap**: A GitHub API outage or slow response will cascade into the Camunda engine, blocking process instances and potentially exhausting thread pools. A runaway agent triggering many process instances could amplify this cascading failure.
- **Compensating Controls**:
  - Configure HTTP client timeouts as a first step (Java HttpClient supports `.timeout()`, node-fetch supports `{timeout}` option).
  - Add API Gateway throttling in front of the Camunda REST API to limit inbound request rates.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add Resilience4j circuit breaker to the Java delegate. Add timeout and retry configuration to all HTTP clients. Add node-fetch timeout to `service.js`.
- **Evidence**: `CamundaApplication/src/main/java/com/example/workflow/FindGitHubRepo.java` (HttpClient with no timeout/retry), `SearchContributorService/service.js` (fetch with no timeout), `CamundaApplication/src/main/resources/static/scripts/GetRepoLang.groovy` (RESTClient with no resilience)

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No rate limiting found at any layer. No API Gateway with throttling configuration. No WAF rate rules. No application-level rate limiting middleware (e.g., Spring Security rate limiter, express-rate-limit). The Camunda REST API has no rate limit configuration. No `aws_api_gateway_usage_plan` or equivalent in IaC (no IaC exists).
- **Gap**: A runaway agent loop can start unlimited process instances at machine speed, overwhelming both the Camunda engine and the downstream GitHub API. There is no protection against traffic storms.
- **Compensating Controls**:
  - Deploy an API Gateway or reverse proxy (e.g., NGINX) in front of the Camunda REST API with rate limiting rules.
  - Add Spring Security rate limiting at the application level.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Deploy an API Gateway (AWS API Gateway or NGINX) in front of the application with per-client rate limits. Configure GitHub API authentication to get higher rate limits (currently using unauthenticated access with 60 req/hour limit).
- **Evidence**: `CamundaApplication/src/main/resources/application.yaml` (no rate limit config), `CamundaApplication/pom.xml` (no rate limiting library), No IaC files found.

#### DATA-Q2: Data Residency and Sovereignty ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No data residency configuration found. Data is stored locally in an H2 file database (`jdbc:h2:file:./camunda-h2-database`) with no region specification. The application makes external calls to `api.github.com` which is a US-based service. No GDPR, LGPD, or other data sovereignty references found in the codebase or documentation. No region-specific deployment configuration.
- **Gap**: If this application were deployed in a regulated environment, there is no mechanism to enforce data residency. The H2 database location is relative to the application directory with no explicit region control. Data transmitted to GitHub API crosses network boundaries without controls.
- **Compensating Controls**:
  - Document the data flows explicitly (what data goes where) as a first step.
  - Deploy the application in a specific AWS region and use region-locked services (RDS instead of H2) when moving to production.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Replace H2 with a managed database service (e.g., Amazon RDS) in a specific region. Document all external data flows and classify their residency requirements.
- **Evidence**: `CamundaApplication/src/main/resources/application.yaml` (`jdbc:h2:file:./camunda-h2-database`), `CamundaApplication/src/main/java/com/example/workflow/FindGitHubRepo.java` (calls to `api.github.com`), `SearchContributorService/service.js` (calls to `api.github.com`)

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The application logs full response bodies from external APIs without any redaction. `FindGitHubRepo.java` uses `System.out.println(response.body())` to print the entire GitHub API response. The Groovy script uses `println(response.contentAsString)` to print full response content. The `application.yaml` configures DEBUG-level logging for HTTP wire traffic: `org.apache.http.wire: DEBUG`, `org.apache.http.headers: DEBUG`, which logs raw HTTP request/response content including headers and body. No PII scrubbing, log masking, or structured log filtering is configured. No Amazon Macie or equivalent PII detection.
- **Gap**: While the current data is public GitHub data, the logging configuration will capture all HTTP traffic at wire level. If the application evolves to handle sensitive data, or if GitHub API responses include user email addresses or other PII, this will be exposed in logs without redaction.
- **Compensating Controls**:
  - Disable DEBUG-level HTTP wire logging in production (set to WARN or ERROR).
  - Remove `System.out.println(response.body())` calls from production code.
- **Remediation Timeline**: 7–14 days
- **Recommendation**: (1) Set HTTP wire logging to WARN in production `application.yaml`. (2) Remove `System.out.println(response.body())` from `FindGitHubRepo.java`. (3) Remove `println(response.contentAsString)` from the Groovy script. (4) Add a log sanitization filter if structured logging is adopted.
- **Evidence**: `CamundaApplication/src/main/java/com/example/workflow/FindGitHubRepo.java` (`System.out.println(response.body())`), `CamundaApplication/src/main/resources/static/scripts/GetRepoLang.groovy` (`println(response.contentAsString)`), `CamundaApplication/src/main/resources/application.yaml` (DEBUG-level HTTP wire logging)

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, GraphQL schema, or other machine-readable specification found in the repository. The Camunda REST API has its own OpenAPI specification published externally by Camunda, but nothing is bundled or maintained in this repository.
- **Gap**: Agent frameworks cannot auto-generate tool definitions from a local spec. Every integration requires manual tool authoring.
- **Compensating Controls**:
  - Reference the external Camunda REST API OpenAPI spec for tool generation.
  - Manually author agent tool definitions based on the README documentation.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: If a custom business API is created (per API-Q1 remediation), generate an OpenAPI spec from annotations (e.g., SpringDoc/Swagger).
- **Evidence**: No API specification files found in repository. `README.md` (documents REST call patterns but not a machine-readable spec).

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Error handling is inconsistent and unstructured across the 4 integration patterns. `FindGitHubRepo.java` throws `new Exception("Error from REST call, Response code: " + response.statusCode())` for non-200 responses — a plain text error message. `service.js` sends failure with `errorMessage` and `errorDetails` fields via `taskService.handleFailure()`. The Groovy script catches `RESTClientException`, prints it, then throws `new Exception(e)`. The HTTP connector's execution listener throws `new Error("Error from REST, response Code: " + statusCode)`. None of these follow a structured error format with error code, category, and retryable boolean.
- **Gap**: An agent cannot distinguish retriable errors (timeout, rate limit) from terminal errors (invalid input, resource not found). All errors are generic exceptions or BPMN errors.
- **Compensating Controls**:
  - Map Camunda incident types to structured error categories in an agent orchestration layer.
  - Use HTTP status codes from the Camunda REST API as a proxy for error classification.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Implement a structured error response format in any new business API layer: `{ "error_code": "...", "error_message": "...", "retryable": true/false, "details": {...} }`.
- **Evidence**: `CamundaApplication/src/main/java/com/example/workflow/FindGitHubRepo.java` (generic Exception throw), `SearchContributorService/service.js` (handleFailure with errorMessage/errorDetails), `CamundaApplication/src/main/resources/process.bpmn` (execution listener Error throw)

#### API-Q6: Asynchronous Operation Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The BPMN process is inherently long-running (involves human user tasks). Camunda supports asynchronous execution via `camunda:asyncBefore` (set on start event `Event_1ck1sdz`) and `camunda:asyncAfter` (set on "Search for contributors" task `Activity_0827gcj` and "Get repo languages" script task `Activity_0u7shp8`). External task pattern via `service.js` is inherently async. However, there is no explicit job status polling API for the business process — an agent would need to poll Camunda's process instance API to check completion status, which is a platform-level concern, not a business API pattern.
- **Gap**: No business-level async pattern (job submission with polling endpoint or webhook callback). An agent starting a process instance has no clean way to know when the workflow completes without polling the Camunda REST API for process instance state.
- **Compensating Controls**:
  - Use Camunda's process instance query API to poll for completion status.
  - Implement a webhook callback from a process end event listener.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add an execution listener on end events that sends a webhook/callback to notify callers of process completion. Alternatively, expose a business-level `/api/repos/{id}/status` endpoint.
- **Evidence**: `CamundaApplication/src/main/resources/process.bpmn` (asyncBefore on start event, asyncAfter on service tasks, external task pattern)

#### AUTH-Q4: Identity Propagation and Delegation — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No identity propagation patterns found. No JWT parsing middleware, no OAuth2 on-behalf-of flows, no token exchange. Outbound calls to GitHub API from `FindGitHubRepo.java` are unauthenticated — `HttpRequest.newBuilder().uri(URI.create(uri)).build()` with no Authorization header. The Groovy script's `RESTClient` and `service.js`'s `fetch()` also send no auth headers. There is no mechanism to distinguish between an agent acting under its own identity vs. on behalf of a user.
- **Gap**: Cannot distinguish the actor (agent) from the subject (user on whose behalf the agent acts). All calls appear as the same identity.
- **Compensating Controls**:
  - Pass a user context header (`X-User-Id`) through agent-initiated requests for attribution.
  - Add GitHub API authentication tokens to increase rate limits and enable attribution.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement token propagation for the Camunda REST API. Add GitHub API OAuth token for outbound calls. Add user context headers for agent-on-behalf-of-user scenarios.
- **Evidence**: `CamundaApplication/src/main/java/com/example/workflow/FindGitHubRepo.java` (no auth headers on GitHub calls), `SearchContributorService/service.js` (no auth headers), `CamundaApplication/src/main/resources/static/scripts/GetRepoLang.groovy` (no auth on RESTClient)

#### AUTH-Q5: Credential Management — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Hardcoded credentials found in `application.yaml`: `camunda.bpm.admin-user.id: demo` and `camunda.bpm.admin-user.password: demo`. No secrets management integration (no AWS Secrets Manager, no HashiCorp Vault). No `.env` files found, but credentials are directly in the committed configuration file. The GitHub API calls are made without authentication tokens.
- **Gap**: Credentials are committed to source control in plaintext. No secret rotation capability. A prompt injection attack or agent bug could expose these credentials.
- **Compensating Controls**:
  - Move credentials to environment variables as an immediate step.
  - Use Spring Boot's externalized configuration to read secrets from environment.
- **Remediation Timeline**: 7–14 days
- **Recommendation**: (1) Remove hardcoded credentials from `application.yaml`. (2) Use Spring Boot environment variable substitution (`${CAMUNDA_ADMIN_PASSWORD}`). (3) Integrate with AWS Secrets Manager or HashiCorp Vault for production deployments.
- **Evidence**: `CamundaApplication/src/main/resources/application.yaml` (`password: demo` in plaintext)

#### STATE-Q2: Queryable Current State — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The Camunda REST API exposes process instance state queries at `/engine-rest/process-instance`, `/engine-rest/task`, and `/engine-rest/variable-instance`. Process variables (forks, contributors, healthPercentage, programingLanguages, popularRepo) can be queried via the Camunda REST API. However, this is platform-level state exposure, not a business API. There is no application-specific state query endpoint.
- **Gap**: An agent can query process state only through Camunda's generic REST API, requiring knowledge of Camunda semantics (process instance IDs, activity IDs, variable names).
- **Compensating Controls**:
  - Use Camunda REST API process instance queries as the interim state query mechanism.
  - Document the process variable schema for agent tool builders.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create business-level state query endpoints that abstract Camunda internals (e.g., `GET /api/repos/{owner}/{name}/popularity-check-status`).
- **Evidence**: `CamundaApplication/pom.xml` (camunda-bpm-spring-boot-starter-rest provides REST API), `CamundaApplication/src/main/resources/process.bpmn` (process variables as queryable state)

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The test configuration uses an H2 in-memory database (`jdbc:h2:mem:camunda-h2-database;DB_CLOSE_ON_EXIT=FALSE` in `src/test/resources/application.yaml`). `WorkflowTest.java` provides 3 integration tests running against an embedded Camunda engine with Spring Boot test context. However, there is no separate staging or sandbox environment configuration, no docker-compose for local development, no synthetic data generators, and no environment-specific deployment configurations.
- **Gap**: No production-equivalent staging environment for agent testing. The test suite validates BPMN process behavior against live GitHub API endpoints, meaning tests depend on external service availability.
- **Compensating Controls**:
  - Use the existing Spring Boot test context with mocked external services as a sandbox.
  - Create a docker-compose setup for isolated local testing.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Create a docker-compose setup with the Camunda application and a mock GitHub API (e.g., WireMock) for isolated agent testing. Add environment-specific configuration profiles.
- **Evidence**: `CamundaApplication/src/test/resources/application.yaml` (H2 in-memory test config), `CamundaApplication/src/test/java/com/example/workflow/WorkflowTest.java` (3 integration tests)

#### DATA-Q3: Selective Query Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The `SearchContributorService/service.js` fetches all contributors from `https://api.github.com/repos/{owner}/{repo}/contributors` without pagination parameters (no `?per_page=` or `?page=`). The GitHub API returns paginated results by default (30 per page), but the code does not handle pagination — it only processes the first page. The Camunda REST API supports pagination for process instance queries with `firstResult` and `maxResults` parameters.
- **Gap**: Agent queries against the contributors endpoint may receive incomplete data (only first page) without realizing it. No explicit result size limits are enforced at the application level.
- **Compensating Controls**:
  - Add pagination parameters to GitHub API calls to explicitly control result set sizes.
  - Use Camunda REST API pagination for process state queries.
- **Remediation Timeline**: 7–14 days
- **Recommendation**: Add `?per_page=100` and pagination handling to the GitHub API calls in `service.js`. Document pagination behavior in any business API layer.
- **Evidence**: `SearchContributorService/service.js` (fetch to `/contributors` with no pagination params)

#### DATA-Q4: System of Record Designations — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No system-of-record designations found. The GitHub API is the de facto source of truth for repository data (forks, contributors, languages, community health). The Camunda H2 database stores process instance state (a snapshot of values at execution time). No master data management process or conflict resolution logic exists. No documentation of which system is authoritative for which entity.
- **Gap**: An agent querying Camunda process variables may get stale data (values captured at execution time) that differ from current GitHub API values. No mechanism to signal which source is authoritative.
- **Compensating Controls**:
  - Document GitHub API as the system of record for repository data.
  - Treat Camunda process variables as execution-time snapshots, not authoritative current state.
- **Remediation Timeline**: 7–14 days
- **Recommendation**: Document system-of-record designations: GitHub API for live repository data, Camunda engine for process execution state.
- **Evidence**: `CamundaApplication/src/main/java/com/example/workflow/FindGitHubRepo.java` (fetches from GitHub, stores in process), `SearchContributorService/service.js` (fetches from GitHub, stores in process)

#### DATA-Q5: Temporal Metadata and Freshness — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The Camunda engine tracks process instance timestamps internally (start time, end time, task create/complete times via the history service). However, no explicit temporal metadata is exposed in application responses. No `Cache-Control` headers, no `X-Data-Age` headers, no `last_refreshed` indicators. Process variables do not include timestamps indicating when the data was fetched from GitHub. No timezone handling configuration.
- **Gap**: An agent cannot determine when process variable data was last fetched from GitHub. A process that completed hours ago has the same data representation as one completed seconds ago.
- **Compensating Controls**:
  - Use Camunda history service timestamps as proxy for data freshness.
  - Add a `fetchedAt` process variable when setting data from external API calls.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add `fetchedAt` timestamp process variables when storing external API response data. Include temporal metadata in any business API responses.
- **Evidence**: `CamundaApplication/src/main/java/com/example/workflow/FindGitHubRepo.java` (sets `forks` variable without timestamp), `SearchContributorService/service.js` (sets `contributors` variable without timestamp)

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No schema versioning found. The Camunda REST API version is implicit via the Spring Boot starter version (7.16.0, with BOM at 7.15.0), but no explicit API versioning in URL patterns (no `/v1/`, `/v2/`). No schema registry. No breaking change detection in CI (no CI pipeline exists). The DMN decision table (`DecideOnPopularity.dmn`) has no versioning beyond git. No consumer-driven contract tests (no Pact or equivalent). No changelog files or deprecation notices.
- **Gap**: Agent tool bindings could break silently when the Camunda version is upgraded or when process definitions change. No automated mechanism to detect breaking changes.
- **Compensating Controls**:
  - Pin the Camunda version in `pom.xml` (already done via version-specific dependencies).
  - Document the process variable schema as a contract.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add API versioning to any custom business API. Implement contract tests for process variable schemas. Add OpenAPI spec diff checking to CI when CI is established.
- **Evidence**: `CamundaApplication/pom.xml` (Camunda 7.16.0, Spring Boot 2.5.4), `CamundaApplication/src/main/resources/DecideOnPopularity.dmn` (no version metadata)

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No distributed tracing found — no X-Ray SDK, no OpenTelemetry instrumentation, no `traceparent` header propagation. Logging is configured in `logback-test.xml` with plain-text pattern layout: `%d{HH:mm:ss.SSS} [%thread] %-5level %logger{36} - %msg%n`. Application output uses `System.out.println` in `FindGitHubRepo.java` and `println()` in the Groovy script — unstructured console output. No JSON structured logging. No `request_id` or `correlation_id` fields.
- **Gap**: Agent-initiated requests cannot be traced across the system. When a process fails, there is no way to correlate the failure across the Camunda engine, the Java delegate, the external task worker, and the GitHub API calls.
- **Compensating Controls**:
  - Add SLF4J MDC (Mapped Diagnostic Context) with a request ID to correlate log entries.
  - Switch to JSON log format for structured log analysis.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: (1) Add OpenTelemetry Java agent for distributed tracing. (2) Switch logback to JSON format. (3) Add correlation IDs via SLF4J MDC. (4) Propagate trace context through external task worker.
- **Evidence**: `CamundaApplication/src/test/resources/logback-test.xml` (plain-text pattern), `CamundaApplication/src/main/java/com/example/workflow/FindGitHubRepo.java` (System.out.println), `CamundaApplication/pom.xml` (no tracing dependencies)

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No alerting configuration found. No CloudWatch alarms, no anomaly detection, no PagerDuty/OpsGenie integration. No SLO-based alerting. No monitoring dashboard configuration. The application has no health check endpoint beyond Spring Boot Actuator defaults (if enabled, which is not confirmed).
- **Gap**: Target system degradation is invisible. If the GitHub API starts returning errors or the Camunda engine becomes overloaded, there is no automated alerting mechanism.
- **Compensating Controls**:
  - Enable Spring Boot Actuator health endpoints and monitor externally.
  - Add Camunda's built-in metrics (job executor, external tasks) to a monitoring system.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Enable Spring Boot Actuator with health and metrics endpoints. Configure CloudWatch alarms on error rates and response latency. Add alerts for Camunda job executor failures.
- **Evidence**: `CamundaApplication/pom.xml` (no actuator or monitoring dependencies), No IaC files with alarm configurations found.

#### ENG-Q1: Infrastructure Governance — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No Infrastructure as Code found in the repository. No Terraform, CloudFormation, CDK, Helm charts, or Kustomize configurations. The entire infrastructure surface is undefined — no API Gateway, no IAM roles, no networking configuration, no load balancer, no managed database. No drift detection configuration.
- **Gap**: The agent-facing infrastructure surface is completely undefined. Any deployment would require manual infrastructure provisioning, which is error-prone and unauditable.
- **Compensating Controls**:
  - Document the target deployment architecture before provisioning infrastructure.
  - Use a managed platform (e.g., AWS App Runner, ECS) that provides some infrastructure governance by default.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Define the deployment infrastructure as code (Terraform or CDK) including: compute (ECS/EKS), database (RDS), API Gateway, IAM roles, networking, and monitoring. Subject IaC changes to peer review.
- **Evidence**: No IaC files found in repository. Entire repository is application code only.

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No CI/CD pipeline configuration found. No GitHub Actions, GitLab CI, Jenkins, or CodeBuild configurations. No API contract tests. No breaking change detection. No automated build or deployment process.
- **Gap**: There is no automated mechanism to detect API-breaking changes before they affect agents. Changes are manual and unvalidated.
- **Compensating Controls**:
  - Implement a basic CI pipeline (GitHub Actions) with build and test as a first step.
  - Add API contract tests when a business API layer is established.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: (1) Add a GitHub Actions workflow with Maven build and test. (2) Add API contract tests when business API is established. (3) Add OpenAPI spec validation in the pipeline.
- **Evidence**: No CI/CD configuration files found (no `.github/workflows/`, no `Jenkinsfile`, no `buildspec.yml`).

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No deployment configuration found. No blue/green deployment, no canary deployment, no CodeDeploy configuration, no Helm rollback capability, no feature flags. No evidence of any deployment strategy or rollback mechanism.
- **Gap**: If a deployment breaks agent-facing APIs, there is no way to roll back to the previous known-good state. Recovery would require manual intervention.
- **Compensating Controls**:
  - Use a container-based deployment (Docker + ECS) that supports rollback by reverting to previous task definition.
  - Maintain versioned artifacts for manual rollback.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement container-based deployment with automated rollback triggers. Use blue/green or canary deployment strategy with health check gates.
- **Evidence**: No Dockerfile, no deployment configuration, no IaC found.

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: `WorkflowTest.java` contains 3 integration tests: (1) `shouldExecuteScriptTask` — tests Groovy script task with camunda/camunda-bpm-platform repo, verifying programming language detection; (2) `testConnectorCallSuccessfully` — tests HTTP connector task, verifying healthPercentage is 71; (3) `testConnectorCallBpmnError` — tests BPMN error flow when health < 70, verifying error routing to "Look at Error" task. Tests run against Spring Boot test context with embedded Camunda engine. `SearchContributorService/package.json` has `"test": "echo \"Error: no test specified\" && exit 1"` — no tests defined.
- **Gap**: Tests validate BPMN process behavior, not the REST API surface. No API-level tests (Postman, REST Assured). No contract tests. No edge case coverage (invalid inputs, timeout scenarios, concurrent process instances). No tests for the external task worker. Tests depend on live GitHub API availability.
- **Compensating Controls**:
  - Add WireMock or MockServer for GitHub API mocking to make tests deterministic.
  - Add API-level tests when a business API layer is created.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: (1) Add mock-based tests that don't depend on live GitHub API. (2) Add tests for the external task worker in `SearchContributorService`. (3) Add edge case tests (non-existent repos, rate-limited responses, timeout scenarios).
- **Evidence**: `CamundaApplication/src/test/java/com/example/workflow/WorkflowTest.java` (3 integration tests), `SearchContributorService/package.json` (no tests defined)

#### ENG-Q5: Encryption at Rest — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The H2 file database (`jdbc:h2:file:./camunda-h2-database`) has no encryption configuration. No KMS key references. No encryption at rest for any data store. H2 supports built-in AES encryption via the `CIPHER=AES` parameter, but it is not configured.
- **Gap**: Process instance data (including user-submitted inputs and external API responses) is stored unencrypted on disk.
- **Compensating Controls**:
  - Use H2's built-in encryption (`CIPHER=AES`) as a quick fix.
  - Migrate to a managed database (RDS) with KMS encryption at rest.
- **Remediation Timeline**: 7–14 days (H2 encryption) or 60–90 days (RDS migration)
- **Recommendation**: For immediate improvement, add H2 CIPHER=AES encryption. For production readiness, migrate to Amazon RDS with KMS-managed encryption at rest.
- **Evidence**: `CamundaApplication/src/main/resources/application.yaml` (`jdbc:h2:file:./camunda-h2-database` — no encryption parameters)

## INFOs — Architecture and Design Inputs

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No idempotency keys or idempotency middleware found. Starting a process instance via the Camunda REST API (`POST /engine-rest/process-definition/key/{key}/start`) creates a new process instance on every call — no duplicate detection. The `businessKey` parameter can be set (as documented in README) but is not enforced as a uniqueness constraint.
- **Implication**: If agent scope is expanded to write-enabled in the future, process instance creation could result in duplicate instances on retry. Idempotency mechanisms would need to be added before write-enabled agents are deployed.
- **Recommendation**: When expanding to write-enabled scope, implement idempotency via business key uniqueness enforcement or idempotency key middleware on the business API layer.
- **Evidence**: `README.md` (documents businessKey parameter), `CamundaApplication/src/main/resources/process.bpmn` (no idempotency enforcement)

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: The Camunda REST API returns JSON responses. GitHub API responses are parsed as JSON — `FindGitHubRepo.java` uses `new JSONObject(body)` to parse responses, `service.js` uses `response.json()`, and the HTTP connector uses Spin JSON parsing (`${S(response).prop("health_percentage")}`). All data interchange is JSON-based, which is well-suited for LLM consumption.
- **Implication**: JSON format is optimal for agent tool integration. No additional format conversion is needed.
- **Recommendation**: Maintain JSON as the response format for any new business API layer.
- **Evidence**: `CamundaApplication/src/main/java/com/example/workflow/FindGitHubRepo.java` (JSONObject parsing), `SearchContributorService/service.js` (response.json()), `CamundaApplication/src/main/resources/process.bpmn` (Spin JSON parsing)

### API-Q7: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: No external event emission found. No webhook endpoints, no SNS/EventBridge/SQS integration, no Kafka topics, no CDC pipelines. The Camunda engine has an internal event mechanism (execution listeners, task listeners) that is used for process-internal logic (e.g., execution listeners on the HTTP connector task), but no events are published to external consumers.
- **Implication**: Agents cannot react to process state changes (e.g., process completed, task created) without polling. Event-driven agent patterns are not supported.
- **Recommendation**: Consider adding event publication via SNS or EventBridge on process completion and error events if proactive agent behavior is needed.
- **Evidence**: `CamundaApplication/src/main/resources/process.bpmn` (execution listeners are internal only, no external event publishing)

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No API rate limits are documented. No API Gateway throttle settings. No WAF rate rules. No rate limiting middleware. No `X-RateLimit-Remaining` or `Retry-After` headers in response code. The Camunda REST API does not natively include rate limit headers. The GitHub API returns rate limit headers, but the application does not propagate them.
- **Implication**: An agent has no way to self-throttle based on server-side capacity. Without rate limit information, agents will discover limits only through failures.
- **Recommendation**: Document rate limits when an API Gateway is deployed. Propagate rate limit headers in any business API response.
- **Evidence**: `CamundaApplication/src/main/resources/application.yaml` (no rate limit config), `CamundaApplication/pom.xml` (no rate limiting dependencies)

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The Camunda engine uses internal optimistic locking for process instance state management (the engine's database schema includes `REV_` columns for optimistic locking). No application-level concurrency controls (ETag, `If-Match` headers, version fields) are implemented beyond what Camunda provides internally. No DynamoDB conditional writes or equivalent.
- **Implication**: Camunda's internal locking protects engine state from concurrent writes. If agent scope is expanded to write-enabled, application-level concurrency controls may be needed for business operations.
- **Recommendation**: Document Camunda's built-in optimistic locking. If expanding to write-enabled scope, add ETag or version-based concurrency controls on any custom business API endpoints.
- **Evidence**: `CamundaApplication/pom.xml` (Camunda engine provides internal locking), `CamundaApplication/src/main/resources/process.bpmn` (async flags enable transaction isolation)

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits found. No maximum records per operation, no spend limits, no delete limits. No per-identity action limits beyond what the Camunda engine enforces internally.
- **Implication**: If agent scope is expanded to write-enabled, there are no guardrails on the blast radius of agent-initiated operations (e.g., starting thousands of process instances in a loop).
- **Recommendation**: When expanding to write-enabled scope, implement per-agent-identity limits on process instance creation rate, concurrent active instances, and API call volume.
- **Evidence**: No transaction limit configuration found in any repository files.

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The BPMN process has user tasks that function as human approval/review points: "Display Details" (`Activity_0scbww2`), "Display unpopular results" (`Activity_1vv3176`), and "Look at Error" (`Activity_0hbvr03`). These user tasks create a "pending" state where the process waits for human interaction. The Camunda task API supports claim/complete patterns that can function as approve/reject workflows.
- **Implication**: The existing BPMN user task pattern provides a natural mechanism for human-in-the-loop workflows. If agents are given write access, user tasks can serve as approval gates.
- **Recommendation**: Leverage existing user task patterns as HITL gates if expanding to write-enabled agent scope.
- **Evidence**: `CamundaApplication/src/main/resources/process.bpmn` (user tasks: Display Details, Display unpopular results, Look at Error)

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: BPMN processes inherently support configurable approval gates via user tasks. The error event subprocess routes errors to a "Look at Error" user task for human review — a built-in approval gate for error scenarios. The Camunda Tasklist web application provides a UI for human task completion. However, there is no configurable per-operation approval flag — the approval points are hardcoded in the BPMN process definition.
- **Implication**: Adding new approval gates requires modifying the BPMN process definition, not runtime configuration. This is a design-time concern, not a runtime concern.
- **Recommendation**: Consider parameterizing approval gates (e.g., a process variable `requireApproval` that routes through a user task conditionally) if write-enabled agents are deployed.
- **Evidence**: `CamundaApplication/src/main/resources/process.bpmn` (error subprocess with user task, user tasks in main flow)

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality metrics, dashboards, profiling, or monitoring found. No null rate monitoring, no duplicate detection logic, no data freshness SLAs. The application consumes GitHub API data without validation beyond basic status code checking.
- **Implication**: Agents acting on incomplete or inaccurate GitHub API data (e.g., contributor counts from paginated responses, stale cache) may propagate errors through the workflow.
- **Recommendation**: Add validation checks on GitHub API response data quality (e.g., verify expected fields are present, contributor count matches pagination expectations).
- **Evidence**: `SearchContributorService/service.js` (no data validation beyond status code), `CamundaApplication/src/main/java/com/example/workflow/FindGitHubRepo.java` (basic JSON parsing, no validation of data completeness)

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Process variables use readable, semantically meaningful names: `repoName`, `repoOwner`, `forks`, `contributors`, `healthPercentage`, `programingLanguages` (misspelled but readable), `java`, `javaScript`, `python`, `ruby`, `closure`, `scala`, `popularRepo`, `errorMessage`, `errorCode`. DMN decision table inputs/outputs use readable names (`forks`, `contributors`, `popularRepo`). Form field keys are descriptive (`repoName`, `repoOwner`, `programingLanguages`, `forks`, `contributors`, `healthPercentage`). One minor typo: `programingLanguages` should be `programmingLanguages`.
- **Implication**: LLM-based agents can reason about field semantics without a data dictionary. The naming convention is agent-friendly.
- **Recommendation**: Fix the `programingLanguages` typo to `programmingLanguages`. Maintain the human-readable naming convention for all new variables.
- **Evidence**: `CamundaApplication/src/main/resources/process.bpmn` (variable names), `CamundaApplication/src/main/resources/DecideOnPopularity.dmn` (input/output names), `CamundaApplication/src/main/resources/static/forms/startForm.form` (field keys)

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No formal data catalog found. No AWS Glue Data Catalog, Collibra, Alation, or DataHub integration. No metadata files or data dictionary. The `README.md` provides comprehensive documentation of the process, integration patterns, and REST call examples — serving as informal documentation. The `bpmn-analysis.json` provides machine-readable process analysis but is not a data catalog.
- **Implication**: Tool builders must reverse-engineer data schemas from code and BPMN definitions. The README partially compensates but is not machine-readable.
- **Recommendation**: Create a data dictionary documenting all process variables, their types, sources, and semantics. Consider publishing this as a machine-readable schema file.
- **Evidence**: `README.md` (comprehensive documentation), `bpmn-analysis.json` (process analysis), No data catalog files found.

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No custom business metrics found. No `cloudwatch.put_metric_data`, no custom dashboards, no business KPI alarms. The Camunda engine tracks internal metrics (process instance counts, task completion times, job executor throughput) via its built-in history service, but no custom business outcome metrics are published externally.
- **Implication**: There is no way to measure whether agent interactions produce good business outcomes (e.g., process completion rates, average resolution time, popularity check accuracy).
- **Recommendation**: Add custom metrics for business outcomes: process completion rate, average end-to-end duration, error subprocess trigger rate, popular vs. unpopular classification distribution.
- **Evidence**: `CamundaApplication/pom.xml` (no metrics publishing dependencies), `CamundaApplication/src/main/resources/application.yaml` (no metrics config)

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: BLOCKER
- **Finding**: The application exposes the Camunda REST API via `camunda-bpm-spring-boot-starter-rest` (version 7.16.0) at `/engine-rest`. No custom REST controllers are defined. The integration surface is the generic Camunda engine REST API, not a business-specific API.
- **Gap**: No application-specific documented API interface for agent integration. Agents must understand Camunda process semantics.
- **Recommendation**: Create a business facade REST API with documented endpoints abstracting Camunda internals.
- **Evidence**: `CamundaApplication/pom.xml`, `SearchContributorService/service.js`, `README.md`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, GraphQL schema, or Smithy model found in the repository. The Camunda REST API has an external OpenAPI spec published by Camunda, but nothing is bundled locally.
- **Gap**: No machine-readable spec for auto-generating agent tool definitions.
- **Recommendation**: Generate an OpenAPI spec when a business API layer is created (use SpringDoc/Swagger).
- **Evidence**: No API specification files found in repository.

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: Error handling is inconsistent across 4 integration patterns. `FindGitHubRepo.java` throws generic Exception. `service.js` sends handleFailure with errorMessage/errorDetails. Groovy script throws wrapped Exception. HTTP connector execution listener throws Error. No structured error format.
- **Gap**: No machine-readable error categorization (error code, retryable boolean).
- **Recommendation**: Implement structured error response format in business API layer.
- **Evidence**: `CamundaApplication/src/main/java/com/example/workflow/FindGitHubRepo.java`, `SearchContributorService/service.js`, `CamundaApplication/src/main/resources/process.bpmn`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No idempotency keys found. Process start via REST creates duplicate instances on repeat calls. `businessKey` parameter is available but not enforced as uniqueness constraint.
- **Gap**: No idempotency enforcement on write operations.
- **Recommendation**: Implement idempotency via business key uniqueness when expanding to write-enabled scope.
- **Evidence**: `README.md`, `CamundaApplication/src/main/resources/process.bpmn`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: All data interchange uses JSON. Camunda REST API returns JSON. GitHub API responses parsed as JSON via JSONObject (Java), response.json() (JS), and Spin JSON (BPMN connector).
- **Gap**: N/A — JSON is appropriate for agent consumption.
- **Recommendation**: Maintain JSON format.
- **Evidence**: `CamundaApplication/src/main/java/com/example/workflow/FindGitHubRepo.java`, `SearchContributorService/service.js`, `CamundaApplication/src/main/resources/process.bpmn`

#### API-Q6: Asynchronous Operation Support
- **Severity**: RISK-QUALITY
- **Finding**: BPMN workflow is inherently long-running. Camunda supports async via `asyncBefore`/`asyncAfter` flags and external task pattern. No business-level async API (job submission + polling endpoint or webhook callback).
- **Gap**: No clean business-level async pattern for agents to track process completion.
- **Recommendation**: Add webhook/callback from process end events or expose a business status polling endpoint.
- **Evidence**: `CamundaApplication/src/main/resources/process.bpmn` (asyncBefore, asyncAfter flags, external task)

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: No external event emission. Camunda execution listeners are internal only. No webhook, SNS, EventBridge, Kafka, or CDC integration.
- **Gap**: Agents cannot react to state changes without polling.
- **Recommendation**: Add event publication via SNS or EventBridge on key process events.
- **Evidence**: `CamundaApplication/src/main/resources/process.bpmn`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limits documented. No API Gateway throttle settings. No rate limit headers. GitHub API rate limit headers not propagated.
- **Gap**: Agents have no rate limit awareness.
- **Recommendation**: Document and expose rate limits via headers when API Gateway is deployed.
- **Evidence**: `CamundaApplication/src/main/resources/application.yaml`, `CamundaApplication/pom.xml`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: No machine identity authentication configured. Hardcoded admin credentials (`id: demo`, `password: demo`) in `application.yaml`. No OAuth2, API key, or mTLS configuration. Camunda REST API exposed without machine-to-machine auth. External task worker connects without authentication.
- **Gap**: No mechanism to authenticate or attribute agent identities.
- **Recommendation**: Enable Spring Security with OAuth2 client credentials. Remove hardcoded credentials.
- **Evidence**: `CamundaApplication/src/main/resources/application.yaml`, `SearchContributorService/service.js`, `CamundaApplication/src/main/java/com/example/workflow/FindGitHubRepo.java`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: No scoped permissions. Single admin user `demo` has full Camunda admin privileges. No IAM policies, no role definitions, no resource-level access restrictions.
- **Gap**: Cannot grant agent identities limited access. All callers inherit full admin privileges.
- **Recommendation**: Configure Camunda's built-in authorization service with agent-specific roles.
- **Evidence**: `CamundaApplication/src/main/resources/application.yaml`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization. No ABAC/RBAC. No method-level auth checks in code. No middleware enforcing action-level access on the Camunda REST API.
- **Gap**: Cannot restrict agents to read-only operations within a resource type.
- **Recommendation**: Implement Camunda authorization with action-level grants per resource type.
- **Evidence**: `CamundaApplication/src/main/java/com/example/workflow/FindGitHubRepo.java`, `SearchContributorService/service.js`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: RISK-QUALITY
- **Finding**: No identity propagation. No JWT parsing, no OAuth2 on-behalf-of flows. GitHub API calls unauthenticated. No distinction between agent-as-self and agent-on-behalf-of-user.
- **Gap**: Cannot distinguish actor (agent) from subject (user).
- **Recommendation**: Implement token propagation and add GitHub API OAuth token.
- **Evidence**: `CamundaApplication/src/main/java/com/example/workflow/FindGitHubRepo.java`, `SearchContributorService/service.js`, `CamundaApplication/src/main/resources/static/scripts/GetRepoLang.groovy`

#### AUTH-Q5: Credential Management
- **Severity**: RISK-QUALITY
- **Finding**: Hardcoded credentials in `application.yaml`: `password: demo`. No secrets management. No .env files, but credentials in committed config. GitHub API calls unauthenticated (no tokens).
- **Gap**: Credentials in source control. No secret rotation. No secrets management integration.
- **Recommendation**: Move credentials to environment variables. Integrate with AWS Secrets Manager.
- **Evidence**: `CamundaApplication/src/main/resources/application.yaml`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No audit logging. No CloudTrail. No immutable log storage. Only console logging via logback with plain-text pattern. `System.out.println` diagnostic output is not audit logging.
- **Gap**: No immutable audit trail for any operations.
- **Recommendation**: Configure structured audit logging shipped to immutable storage.
- **Evidence**: `CamundaApplication/src/test/resources/logback-test.xml`, `CamundaApplication/src/main/resources/application.yaml`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: No mechanism to suspend/revoke agent identities. No API key management, no identity revocation, no service account disable. Only identity is hardcoded `demo` admin.
- **Gap**: Cannot isolate a misbehaving agent without taking down the application.
- **Recommendation**: Implement API key management with individual revocation capability.
- **Evidence**: `CamundaApplication/src/main/resources/application.yaml`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Partial error handling via BPMN error events. BpmnError thrown in Java delegate, external task, and Groovy script. Error event subprocess routes to human review. `asyncBefore`/`asyncAfter` flags enable transaction isolation. No explicit saga patterns or undo endpoints.
- **Gap**: No application-level compensation for partial multi-step failures beyond BPMN error routing.
- **Recommendation**: Implement BPMN compensation events for each service task.
- **Evidence**: `CamundaApplication/src/main/resources/process.bpmn`, `CamundaApplication/src/main/java/com/example/workflow/FindGitHubRepo.java`, `SearchContributorService/service.js`

#### STATE-Q2: Queryable Current State
- **Severity**: RISK-QUALITY
- **Finding**: Camunda REST API exposes process instance state queries. Process variables queryable via `/engine-rest/variable-instance`. Platform-level state exposure, not a business API.
- **Gap**: State query requires Camunda-specific knowledge.
- **Recommendation**: Create business-level state query endpoints.
- **Evidence**: `CamundaApplication/pom.xml`, `CamundaApplication/src/main/resources/process.bpmn`

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Camunda engine uses internal optimistic locking. No application-level concurrency controls beyond engine internals.
- **Gap**: No application-level concurrency controls for business operations.
- **Recommendation**: Document Camunda's built-in locking. Add concurrency controls if expanding to write-enabled scope.
- **Evidence**: `CamundaApplication/pom.xml`, `CamundaApplication/src/main/resources/process.bpmn`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: No circuit breaker, retry, or timeout on any external calls. Java HttpClient, groovy-wslite RESTClient, and node-fetch all operate without resilience configuration. No Resilience4j or equivalent in dependencies.
- **Gap**: External dependency failures cascade into Camunda engine. No protection against runaway agents amplifying failures.
- **Recommendation**: Add Resilience4j circuit breaker and timeout configuration to all HTTP clients.
- **Evidence**: `CamundaApplication/src/main/java/com/example/workflow/FindGitHubRepo.java`, `SearchContributorService/service.js`, `CamundaApplication/src/main/resources/static/scripts/GetRepoLang.groovy`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No rate limiting at any layer. No API Gateway, WAF, or application-level rate limiting. No IaC with throttling configuration.
- **Gap**: Unlimited request volume possible. Runaway agents can overwhelm the system.
- **Recommendation**: Deploy API Gateway with per-client rate limits. Add GitHub API authentication for higher rate limits.
- **Evidence**: `CamundaApplication/src/main/resources/application.yaml`, `CamundaApplication/pom.xml`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits. No per-identity action limits.
- **Gap**: No guardrails on blast radius of agent-initiated operations.
- **Recommendation**: Implement per-agent-identity limits when expanding to write-enabled scope.
- **Evidence**: No transaction limit configuration found.

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `orchestrator`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path. This service is P1, not P0.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: BPMN user tasks (Display Details, Display unpopular results, Look at Error) create pending states awaiting human interaction. Camunda task API supports claim/complete patterns.
- **Gap**: No configurable draft/pending state beyond BPMN user tasks.
- **Recommendation**: Leverage existing user task patterns as HITL gates if expanding scope.
- **Evidence**: `CamundaApplication/src/main/resources/process.bpmn`

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: BPMN supports approval gates via user tasks. Error subprocess routes to "Look at Error" user task. Approval points hardcoded in BPMN definition, not runtime-configurable.
- **Gap**: No runtime-configurable per-operation approval flags.
- **Recommendation**: Parameterize approval gates with process variables for conditional routing.
- **Evidence**: `CamundaApplication/src/main/resources/process.bpmn`

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: H2 in-memory test database. 3 integration tests in WorkflowTest.java. No staging/sandbox environment. No docker-compose. No synthetic data. Tests depend on live GitHub API.
- **Gap**: No production-equivalent staging for agent testing.
- **Recommendation**: Create docker-compose with WireMock for isolated agent testing.
- **Evidence**: `CamundaApplication/src/test/resources/application.yaml`, `CamundaApplication/src/test/java/com/example/workflow/WorkflowTest.java`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: No data classification at any level. Application processes public GitHub data (repo names, owners, forks, contributors, languages, health percentage). Camunda H2 database stores process instance data including user inputs. No classification tags on data stores. No field-level encryption or PII detection.
- **Gap**: No formal data classification. No gate preventing sensitive data from entering unclassified.
- **Recommendation**: Conduct data classification exercise for all data fields. Tag data stores with classification levels.
- **Evidence**: `CamundaApplication/src/main/resources/application.yaml`, `CamundaApplication/src/main/resources/static/forms/startForm.form`, `CamundaApplication/src/main/resources/process.bpmn`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No data residency configuration. H2 file database stored locally. Calls to api.github.com cross network boundaries. No GDPR/LGPD references. No region-specific configuration.
- **Gap**: No data residency enforcement mechanism.
- **Recommendation**: Replace H2 with managed database in specific region. Document external data flows.
- **Evidence**: `CamundaApplication/src/main/resources/application.yaml`, `CamundaApplication/src/main/java/com/example/workflow/FindGitHubRepo.java`, `SearchContributorService/service.js`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK-QUALITY
- **Finding**: `service.js` fetches contributors without pagination parameters. GitHub API returns first page only (30 results default). Camunda REST API supports pagination with `firstResult`/`maxResults`.
- **Gap**: Incomplete data from unpaginated GitHub API calls. No explicit result size limits at application level.
- **Recommendation**: Add pagination parameters to GitHub API calls. Document pagination in business API.
- **Evidence**: `SearchContributorService/service.js`

#### DATA-Q4: System of Record Designations
- **Severity**: RISK-QUALITY
- **Finding**: No system-of-record designations. GitHub API is de facto source of truth. Camunda H2 stores execution-time snapshots. No master data management or conflict resolution.
- **Gap**: Agents may get stale data from process variables vs. live GitHub data. No authoritative source documented.
- **Recommendation**: Document GitHub API as system of record for live data, Camunda for execution state.
- **Evidence**: `CamundaApplication/src/main/java/com/example/workflow/FindGitHubRepo.java`, `SearchContributorService/service.js`

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK-QUALITY
- **Finding**: Camunda engine tracks internal timestamps. No explicit temporal metadata in responses. No Cache-Control or freshness headers. Process variables lack fetch timestamps.
- **Gap**: Cannot determine data freshness. No signaling of stale/cached data.
- **Recommendation**: Add `fetchedAt` process variables. Include temporal metadata in API responses.
- **Evidence**: `CamundaApplication/src/main/java/com/example/workflow/FindGitHubRepo.java`, `SearchContributorService/service.js`

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: Full response bodies logged via `System.out.println(response.body())` in Java delegate and `println(response.contentAsString)` in Groovy. DEBUG-level HTTP wire logging configured (`org.apache.http.wire: DEBUG`). No PII scrubbing or log masking.
- **Gap**: All HTTP traffic logged at wire level without redaction.
- **Recommendation**: Disable DEBUG HTTP wire logging in production. Remove println of response bodies. Add log sanitization.
- **Evidence**: `CamundaApplication/src/main/java/com/example/workflow/FindGitHubRepo.java`, `CamundaApplication/src/main/resources/static/scripts/GetRepoLang.groovy`, `CamundaApplication/src/main/resources/application.yaml`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics, dashboards, or profiling. No null rate monitoring or duplicate detection. GitHub API data consumed without validation beyond status code.
- **Gap**: No data quality awareness.
- **Recommendation**: Add validation checks on GitHub API response completeness.
- **Evidence**: `SearchContributorService/service.js`, `CamundaApplication/src/main/java/com/example/workflow/FindGitHubRepo.java`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: No schema versioning. Camunda REST API version implicit via starter version (7.16.0). No explicit URL versioning. No schema registry. No breaking change detection (no CI). No consumer-driven contract tests.
- **Gap**: Agent tool bindings could break silently on Camunda upgrades or process definition changes.
- **Recommendation**: Add API versioning. Implement contract tests for process variable schemas.
- **Evidence**: `CamundaApplication/pom.xml`, `CamundaApplication/src/main/resources/DecideOnPopularity.dmn`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Process variables use readable names: `repoName`, `repoOwner`, `forks`, `contributors`, `healthPercentage`, `programingLanguages` (misspelled), `popularRepo`. DMN inputs/outputs readable. Form keys descriptive.
- **Gap**: Minor typo: `programingLanguages` should be `programmingLanguages`.
- **Recommendation**: Fix typo. Maintain naming convention.
- **Evidence**: `CamundaApplication/src/main/resources/process.bpmn`, `CamundaApplication/src/main/resources/DecideOnPopularity.dmn`, `CamundaApplication/src/main/resources/static/forms/startForm.form`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal data catalog. README.md provides comprehensive documentation. `bpmn-analysis.json` provides machine-readable process analysis but is not a data catalog.
- **Gap**: Tool builders must reverse-engineer data schemas from code.
- **Recommendation**: Create data dictionary for process variables with types, sources, and semantics.
- **Evidence**: `README.md`, `bpmn-analysis.json`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: No distributed tracing (no X-Ray, no OpenTelemetry). Logging uses plain-text pattern in logback-test.xml: `%d{HH:mm:ss.SSS} [%thread] %-5level %logger{36} - %msg%n`. Application uses `System.out.println` for output. No JSON logging. No correlation IDs.
- **Gap**: Agent-initiated requests cannot be traced across system components.
- **Recommendation**: Add OpenTelemetry, switch to JSON logging, add correlation IDs.
- **Evidence**: `CamundaApplication/src/test/resources/logback-test.xml`, `CamundaApplication/src/main/java/com/example/workflow/FindGitHubRepo.java`, `CamundaApplication/pom.xml`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: No alerting configuration. No CloudWatch alarms, anomaly detection, PagerDuty, or SLO-based alerting. No monitoring dashboards.
- **Gap**: Target system degradation is invisible.
- **Recommendation**: Enable Spring Boot Actuator. Configure CloudWatch alarms on error rates and latency.
- **Evidence**: `CamundaApplication/pom.xml`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics. Camunda tracks internal engine metrics but no external business outcome metrics are published.
- **Gap**: Cannot measure whether agent interactions produce good outcomes.
- **Recommendation**: Add custom metrics for process completion rates and durations.
- **Evidence**: `CamundaApplication/pom.xml`, `CamundaApplication/src/main/resources/application.yaml`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK-QUALITY
- **Finding**: No IaC found. No Terraform, CloudFormation, CDK, or Helm. Infrastructure surface completely undefined. No API Gateway, IAM roles, networking configuration. No drift detection.
- **Gap**: Agent-facing infrastructure surface is completely undefined.
- **Recommendation**: Define deployment infrastructure as code including compute, database, API Gateway, IAM, and networking.
- **Evidence**: No IaC files found in repository.

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: No CI/CD pipeline. No GitHub Actions, GitLab CI, Jenkins, or CodeBuild. No API contract tests. No breaking change detection.
- **Gap**: No automated mechanism to detect API-breaking changes.
- **Recommendation**: Add GitHub Actions with Maven build/test. Add contract tests when business API is established.
- **Evidence**: No CI/CD configuration files found.

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: No deployment configuration. No blue/green, canary, CodeDeploy, Helm rollback, or feature flags. No deployment strategy.
- **Gap**: No rollback capability for broken deployments.
- **Recommendation**: Implement container-based deployment with automated rollback.
- **Evidence**: No Dockerfile, no deployment configuration found.

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: 3 integration tests in `WorkflowTest.java` testing BPMN process behavior against embedded Camunda with live GitHub API. `SearchContributorService/package.json` has no tests. Tests validate process logic, not API surface.
- **Gap**: No API-level tests. No contract tests. No edge case coverage. No external task worker tests. Tests depend on external service availability.
- **Recommendation**: Add mock-based tests, external task worker tests, and edge case coverage.
- **Evidence**: `CamundaApplication/src/test/java/com/example/workflow/WorkflowTest.java`, `SearchContributorService/package.json`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: RISK-QUALITY
- **Finding**: H2 file database (`jdbc:h2:file:./camunda-h2-database`) has no encryption. No KMS keys. H2 supports `CIPHER=AES` but not configured.
- **Gap**: Process instance data stored unencrypted on disk.
- **Recommendation**: Add H2 CIPHER=AES encryption immediately. Migrate to RDS with KMS for production.
- **Evidence**: `CamundaApplication/src/main/resources/application.yaml`

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `CamundaApplication/src/main/java/com/example/workflow/Application.java` | API-Q1 (Spring Boot entry point) |
| `CamundaApplication/src/main/java/com/example/workflow/FindGitHubRepo.java` | API-Q1, API-Q3, API-Q5, AUTH-Q1, AUTH-Q3, AUTH-Q4, STATE-Q1, STATE-Q4, DATA-Q2, DATA-Q4, DATA-Q5, DATA-Q6, DATA-Q7, OBS-Q1 |
| `SearchContributorService/service.js` | API-Q1, API-Q3, AUTH-Q1, AUTH-Q3, AUTH-Q4, STATE-Q1, STATE-Q4, DATA-Q2, DATA-Q3, DATA-Q4, DATA-Q5, DATA-Q7 |
| `CamundaApplication/src/main/resources/static/scripts/GetRepoLang.groovy` | AUTH-Q4, STATE-Q4, DATA-Q6 |

### BPMN/DMN Process Definitions
| File | Questions Referenced |
|------|---------------------|
| `CamundaApplication/src/main/resources/process.bpmn` | API-Q1, API-Q3, API-Q4, API-Q5, API-Q6, API-Q7, STATE-Q1, STATE-Q2, STATE-Q3, HITL-Q1, HITL-Q2, DATA-Q1, DISC-Q2 |
| `CamundaApplication/src/main/resources/DecideOnPopularity.dmn` | DISC-Q1, DISC-Q2 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `CamundaApplication/src/main/resources/application.yaml` | API-Q1, API-Q8, AUTH-Q1, AUTH-Q2, AUTH-Q5, AUTH-Q6, AUTH-Q7, STATE-Q5, DATA-Q1, DATA-Q2, DATA-Q6, ENG-Q5, OBS-Q3 |
| `CamundaApplication/src/test/resources/application.yaml` | HITL-Q3 |
| `CamundaApplication/src/test/resources/logback-test.xml` | AUTH-Q6, OBS-Q1 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `CamundaApplication/pom.xml` | API-Q1, API-Q2, API-Q8, AUTH-Q1, STATE-Q2, STATE-Q3, STATE-Q5, DISC-Q1, OBS-Q1, OBS-Q2, OBS-Q3, ENG-Q4 |
| `SearchContributorService/package.json` | ENG-Q4 |

### Form Definitions
| File | Questions Referenced |
|------|---------------------|
| `CamundaApplication/src/main/resources/static/forms/startForm.form` | DATA-Q1, DISC-Q2 |
| `CamundaApplication/src/main/resources/static/forms/popularRepoForm.form` | DISC-Q2 |
| `CamundaApplication/src/main/resources/static/forms/unpopularRepoForm.form` | DISC-Q2 |

### Test Files
| File | Questions Referenced |
|------|---------------------|
| `CamundaApplication/src/test/java/com/example/workflow/WorkflowTest.java` | HITL-Q3, ENG-Q4 |

### Documentation
| File | Questions Referenced |
|------|---------------------|
| `README.md` | API-Q1, API-Q2, API-Q4, DISC-Q3 |
| `bpmn-analysis.json` | DISC-Q3 |
