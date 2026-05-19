# Agentic Readiness Analysis Report

**Target**: MonoToMicroLegacy
**Date**: 2026-05-18
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**TD Version**: agentic-readiness-analysis
**Repository Type**: application
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P0
**Tags**: monolith, java, ec2, decomposition-target
**Context**: Legacy Java Spring Boot monolith on EC2 with MySQL — primary decomposition target. The agent needs access to order and return data through discrete service APIs.

**Archetype Justification**: MySQL database with CRUD operations on users and shopping baskets (POST/DELETE basket items, POST user), entity lifecycle management with UUID-based identifiers, and user-specific data access patterns.

**Surface flags**:
  - has_persistent_data_store: true
  - has_http_rpc_surface: true
  - has_auth_surface: false
  - has_write_operations: true
  - has_logging_of_user_data: false

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 1 | **RISK-SAFETY**: 11 | **RISK-QUALITY**: 15 | **INFOs**: 11

This repo has 1 BLOCKER finding and 11 RISK-SAFETY findings. Rule matched: "1-2 BLOCKER → Remediation Required".

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 1 |
| RISK-SAFETY | 11 |
| RISK-QUALITY | 15 |
| INFO | 11 |
| Pass | 3 |
| N/A | 0 |
| Not Evaluated (extended) | 2 |
| **Total** | **43** |

**Core Questions Evaluated**: 25
**Extended Questions Triggered**: 16
**Extended Questions Not Triggered**: 2
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: stateful-crud (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: The application has Spring Security OAuth2 configured (`ResourceServerConfig.java` with `@EnableResourceServer`) but all endpoints are set to `permitAll()`. No authentication is enforced. No machine identity (service account, API key, mTLS, or client credentials flow) exists. The OAuth2 configuration is a skeleton that was never completed.
- **Gap**: No mechanism exists to authenticate agent callers or attribute actions to specific agent identities. Any caller can access all endpoints without identification.
- **Remediation**:
  - **Immediate**: Implement API key authentication or OAuth2 client credentials flow with principal attribution. Deploy an API Gateway with IAM or Cognito authorizers in front of the EC2 instance.
  - **Target State**: Every API call is authenticated with a machine-readable principal identifier that appears in audit logs. Agent identities are distinguishable from human identities.
  - **Estimated Effort**: Medium
  - **Dependencies**: None — this is the foundational control that enables AUTH-Q2, AUTH-Q3, AUTH-Q6, and AUTH-Q7.
- **Evidence**: `src/main/java/com/monoToMicro/security/ResourceServerConfig.java` (line: `authorizeRequests().anyRequest().permitAll()`)

---

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: All endpoints use `@PreAuthorize("permitAll()")`. No role differentiation, no scoped permissions, no mechanism to grant read-only vs read-write access per caller.
- **Gap**: Cannot create a scoped agent identity with restricted access. All callers get identical unlimited access.
- **Compensating Controls**:
  - Deploy an API Gateway with resource policies that restrict agent identities to specific endpoints (e.g., GET-only)
  - Implement network-level segmentation to limit which services can reach which endpoints
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement RBAC with at minimum two roles (read-only, read-write) enforced at the Spring Security level or via API Gateway resource policies.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/BasketController.java`, `UserController.java`, `UnicornController.java` — all annotated with `@PreAuthorize("permitAll()")`

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization exists. All endpoints — read and write — are open to any caller. No distinction between read (GET /unicorns) and write (POST /unicorns/basket, DELETE /unicorns/basket) operations from an authorization perspective.
- **Gap**: Cannot restrict an agent to read-only access while allowing another agent or user write access to the same resource type.
- **Compensating Controls**:
  - API Gateway method-level authorization (allow GET, deny POST/DELETE per API key)
  - Network segmentation: only expose read endpoints to agent-facing network segments
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement method-level security annotations (`@PreAuthorize("hasRole('AGENT_READ')")`) or API Gateway method-level auth.
- **Evidence**: `src/main/java/com/monoToMicro/security/ResourceServerConfig.java`

#### AUTH-Q4: Identity Propagation and Delegation — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No identity propagation exists. The OAuth2 token exchange is configured but non-functional (`permitAll()` bypasses all token validation). No mechanism distinguishes between agent-as-self vs agent-on-behalf-of-user.
- **Gap**: Cannot determine whether an API call was made by an agent under its own authority or on behalf of a specific user. User context is passed only as a URL path parameter (`/unicorns/basket/{userUuid}`), not authenticated.
- **Compensating Controls**:
  - Audit log correlation: require agents to pass a `X-On-Behalf-Of` header that is logged (informational, not enforced)
  - Restrict initial agent scope to operations that don't require user delegation
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement JWT-based identity propagation where the token carries both the agent identity and the delegated user identity with scoped permissions.
- **Evidence**: `src/main/java/com/monoToMicro/security/ResourceServerConfig.java`, `src/main/java/com/monoToMicro/rest/controller/BasketController.java` (userUuid from path, not from token)

#### AUTH-Q5: Credential Management — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Database credentials are hardcoded in `application.properties`: username `MonoToMicroUser` and password `MonoToMicroPassword`. No secrets management system (Secrets Manager, Vault) is used. The DB host is externalized via environment variable `MONO_TO_MICRO_DB_ENDPOINT`, but credentials are static.
- **Gap**: Hardcoded credentials with no rotation. A prompt injection or agent bug that reads application config exposes database credentials.
- **Compensating Controls**:
  - Move credentials to AWS Secrets Manager with automatic rotation
  - Restrict database network access to only the EC2 instance security group
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Migrate credentials to AWS Secrets Manager with IAM-based access and enable automatic rotation.
- **Evidence**: `src/main/resources/application.properties` (lines: `spring.datasource.username: MonoToMicroUser`, `spring.datasource.password: MonoToMicroPassword`)

#### AUTH-Q6: Immutable Audit Logging — RISK-SAFETY ⚡

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No audit logging exists. No CloudTrail configuration, no application-level audit log, no immutable log storage. The only logging is `System.out.println` in the HealthController for EC2 metadata.
- **Gap**: Cannot determine who made any API call (human or agent), when, or what the outcome was. No forensic trail for compliance or incident response.
- **Compensating Controls**:
  - Deploy ALB/API Gateway with access logging enabled (captures caller IP, request path, timestamp)
  - Enable CloudTrail for AWS API-level audit trail
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement structured audit logging with principal attribution, store in CloudWatch Logs with retention policy or S3 with Object Lock.
- **Evidence**: No audit logging configuration found. Searched: CloudTrail references in IaC (none), logging framework config (none), audit interceptor/filter classes (none).

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No identity management system exists. Since authentication is disabled (`permitAll()`), there is no mechanism to revoke or suspend any identity — agent or otherwise.
- **Gap**: Cannot isolate or disable a misbehaving agent without taking down the entire application.
- **Compensating Controls**:
  - Deploy API Gateway with API keys; revoke individual keys to suspend agents
  - Network-level blocking via security group rules
- **Remediation Timeline**: 30–60 days (coupled with AUTH-Q1 remediation)
- **Recommendation**: Implement API key-based or OAuth2 client-based identity with a revocation mechanism (API Gateway API key deletion, Cognito user disable).
- **Evidence**: `src/main/java/com/monoToMicro/security/ResourceServerConfig.java` — no identity enforcement

#### STATE-Q1: Compensation and Rollback — RISK-SAFETY ⚡

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No compensation or rollback mechanisms exist. The basket operations (add/remove unicorn) are single INSERT/DELETE statements with no transaction coordination. No saga pattern, no undo endpoints, no Step Functions.
- **Gap**: If a multi-step agent workflow fails mid-sequence in a write-enabled future, partial state cannot be reverted.
- **Compensating Controls**:
  - Restrict initial agent deployment to read-only operations only
  - Add explicit "remove from basket" as compensation action for "add to basket"
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement compensation endpoints and wrap multi-step operations in database transactions. Consider saga pattern for cross-service operations during decomposition.
- **Evidence**: `src/main/java/com/monoToMicro/core/services/UnicornServiceImpl.java` — individual operations with no transaction management, `src/main/resources/com/monoToMicro/core/repository/mappers/UnicornMapper.xml` — INSERT IGNORE and DELETE as standalone operations

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No rate limiting exists at any layer. No API Gateway, no WAF rate rules, no application-level rate limiting middleware. The Spring Boot application on EC2 accepts unlimited requests.
- **Gap**: A runaway agent loop can overwhelm the application at machine speed. No protection against traffic storms.
- **Compensating Controls**:
  - Deploy ALB with connection limits
  - Add API Gateway with usage plans and throttling in front of the application
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Deploy API Gateway with throttling (e.g., 100 requests/second per API key) or add `spring-boot-starter-resilience4j` with rate limiter.
- **Evidence**: No rate limiting configuration found. Searched: API Gateway references (none), WAF rules (none), rate-limit middleware in dependencies (none), application.properties throttle settings (none).

#### DATA-Q1: Sensitive Data Classification — RISK-SAFETY ⚡

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The system stores user PII (email, first_name, last_name, uuid) in the `unicorn_user` table. The User model exposes all fields via API responses with no filtering (`@JsonInclude(NON_NULL)` only excludes null values, not sensitive fields). The `/user/login` endpoint returns the full User object including email.
- **Gap**:
  - B1 (API response scoping): PII fields (email) returned in login response without filtering. Under read-only scope → RISK-SAFETY.
  - B2 (Access control differentiation): No access control differentiation — all callers get identical access. Fires as RISK-SAFETY.
  - B3 (Classification metadata): No formal data classification. Fires as INFO.
- **Compensating Controls**:
  - Create separate response DTOs that exclude email for agent-facing endpoints
  - Implement field-level serialization control (`@JsonView` or separate agent response models)
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create agent-facing response DTOs that exclude PII fields. Implement OAuth scopes that differentiate sensitive vs non-sensitive data access.
- **Evidence**: `src/main/java/com/monoToMicro/core/model/User.java` (no @JsonIgnore on email), `src/main/java/com/monoToMicro/rest/controller/UserController.java` (returns full User in login response), `database/create_tables.sql` (email, first_name, last_name in unicorn_user table)

#### DATA-Q2: Data Residency and Sovereignty — RISK-SAFETY ⚡

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No data residency configuration found. The database endpoint is externalized via environment variable but no region constraints, data sovereignty policies, or cross-region replication controls are defined. User PII (email, names) is stored with no documented residency requirements.
- **Gap**: No mechanism to prevent an agent from transmitting user PII to an LLM endpoint in a different region. No documented data residency requirements.
- **Compensating Controls**:
  - Document data classification and residency requirements
  - Configure agent orchestration layer to use same-region LLM endpoints only
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document data residency requirements. Implement region-aware agent orchestration that keeps PII within the same jurisdiction.
- **Evidence**: `src/main/resources/application.properties` (DB endpoint via env var, no region constraints), `database/create_tables.sql` (PII in unicorn_user table)

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No PII redaction controls exist. While current logging is minimal (only `System.out.println` in HealthController printing EC2 metadata), no log scrubbing middleware, no PII masking libraries, and no CloudWatch log filters are configured. Spring Boot's default request logging, if enabled, would expose user UUIDs in URL paths and potentially request bodies containing emails.
- **Gap**: No systematic PII protection in the logging pipeline. Any increase in log verbosity (debug mode, request logging) would leak PII without safeguards.
- **Compensating Controls**:
  - Keep logging at minimal level (current state)
  - Add log scrubbing middleware before increasing log verbosity
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement structured logging with PII field masking before enabling request-level logging. Add log filter patterns for email addresses and user identifiers.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/HealthController.java` (System.out.println), no logging framework configuration found, no PII masking libraries in `build.gradle`

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, Swagger, AsyncAPI, GraphQL schema, or Smithy model exists. The API is defined only in Java annotations (`@RequestMapping`, `@RestController`) within source code.
- **Gap**: Agent tool definitions must be manually authored and maintained. No auto-generation possible from spec. Drift between tool definitions and actual behavior is likely.
- **Compensating Controls**:
  - Generate OpenAPI spec from Spring annotations using springdoc-openapi
  - Manually document the 10 endpoints as a stop-gap
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add `springdoc-openapi-ui` dependency to auto-generate OpenAPI spec from existing annotations.
- **Evidence**: Searched: openapi.*, swagger.*, *.graphql, *.smithy — none found. API defined only in controller source files.

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Error responses are bare HTTP status codes with empty bodies. Controllers return `new ResponseEntity<Void>(HttpStatus.BAD_REQUEST)` with no error code, no error message, and no retryable indicator. An agent receiving a 400 cannot distinguish between "invalid input" and "resource not found."
- **Gap**: No structured error response format. Agent cannot determine if an error is retriable, what field failed validation, or what the accepted format is.
- **Compensating Controls**:
  - Document error conditions per endpoint in a README or spec
  - Add a global exception handler with structured error bodies
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Implement a `@ControllerAdvice` global exception handler returning structured JSON error bodies: `{ "error_code": "...", "message": "...", "retryable": false }`.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/BasketController.java` (returns BAD_REQUEST with no body), `UserController.java` (same pattern)

#### STATE-Q7: Graceful Degradation Signaling — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The health endpoints (`/health/ping`, `/health/ishealthy`, `/health/dbping`) provide basic binary health status. `/health/ishealthy` returns a static string regardless of system state. No machine-readable degradation indicators, no `X-Degraded` headers, no `Retry-After` signals.
- **Gap**: An agent cannot detect when the system is operating in degraded mode (e.g., database slow, partial failures). Agents will reason on potentially stale or incomplete data without awareness.
- **Compensating Controls**:
  - Monitor health endpoints from the agent orchestration layer before making calls
  - Implement circuit breaker at the agent orchestration layer
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Enhance health endpoints to return granular JSON status (`{ "status": "degraded", "database": "slow", "response_time_ms": 2000 }`). Add `X-Data-Freshness` headers to data responses.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/HealthController.java` — returns static strings and simple boolean reachability checks

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No sandbox, staging, or local development environment configuration exists. No Docker Compose for local testing, no environment-specific profiles, no seed data generators beyond the initial `create_tables.sql`.
- **Gap**: No safe environment to test agent behavior against production-equivalent data. First agent integration testing would occur against the production database.
- **Compensating Controls**:
  - Create a Docker Compose setup with MySQL and seed data for local testing
  - Deploy a separate staging environment on a smaller EC2 instance
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Create a `docker-compose.yml` with MySQL and the application for local/staging agent testing. Add environment-specific Spring profiles.
- **Evidence**: No Dockerfile, no docker-compose.yml, no environment profiles beyond single `application.properties`. Only `database/create_tables.sql` for schema + seed data.

#### DATA-Q3: Selective Query Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The `GET /unicorns` endpoint returns ALL records with no pagination, filtering, or sorting. The `GET /data` endpoint returns ALL baskets. MyBatis queries use unbounded `SELECT *` and `SELECT ... FROM ... JOIN` with no LIMIT clause.
- **Gap**: Agents retrieving product catalogs or basket data receive the entire dataset. No mechanism to request a subset. Will exhaust LLM context windows as data grows.
- **Compensating Controls**:
  - Add LIMIT clause to SQL queries as a hard cap
  - Implement pagination at the agent orchestration layer (though the API doesn't support it)
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add pagination parameters (`?page=1&size=20`) to list endpoints. Implement cursor-based or offset pagination in MyBatis queries.
- **Evidence**: `src/main/resources/com/monoToMicro/core/repository/mappers/UnicornMapper.xml` (unbounded SELECT queries), `src/main/java/com/monoToMicro/rest/controller/UnicornController.java` (returns full collection)

#### DATA-Q4: Input Validation and Schema Enforcement — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Input validation is limited to null checks in controllers (`if(unicornBasket!=null && unicornBasket.getUnicorns()!=null)`). No validation framework (javax.validation, Hibernate Validator) is used. No `@Valid` annotations. No structured validation error responses. SQL uses parameterized queries (MyBatis `#{param}`) which prevents injection, but no business rule validation exists.
- **Gap**: Malformed agent payloads (missing fields, invalid formats, oversized strings) are not rejected with structured feedback. The only response is a generic 400 with no body.
- **Compensating Controls**:
  - Add Bean Validation annotations (`@NotNull`, `@Email`, `@Size`) to model classes
  - Implement a validation error handler returning field-level errors
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add `spring-boot-starter-validation` dependency, annotate request models with Bean Validation constraints, and implement a `@ControllerAdvice` that returns structured validation errors.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/BasketController.java` (null checks only), `build.gradle` (no validation dependency)

#### DATA-Q5: Temporal Metadata and Freshness — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The database schema includes `creation_date` and `last_modified_date` timestamp columns on all tables. However, these fields are not exposed through the API — the Unicorn model only maps `uuid`, `name`, `description`, `price`, `image`. No freshness signaling headers (`Cache-Control`, `X-Data-Age`) exist in responses.
- **Gap**: Agents cannot determine data freshness from API responses. Temporal metadata exists in the database but is not surfaced.
- **Compensating Controls**:
  - Add `last_modified_date` to API response models
  - Add `Last-Modified` response headers
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Map `creation_date` and `last_modified_date` to response DTOs. Add `Last-Modified` HTTP headers to GET responses.
- **Evidence**: `database/create_tables.sql` (creation_date, last_modified_date columns exist), `src/main/java/com/monoToMicro/core/model/Unicorn.java` (timestamp fields not mapped), `src/main/resources/com/monoToMicro/core/repository/mappers/UnicornMapper.xml` (SELECT * but model doesn't expose timestamps)

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No API versioning (no `/v1/` paths, no `Accept-Version` headers). No schema documentation beyond source code. No breaking change detection (no CI/CD pipeline at all). No changelog or deprecation notices.
- **Gap**: Agent tool bindings will break silently when API changes are deployed. No mechanism to detect or communicate breaking changes.
- **Compensating Controls**:
  - Version API paths (e.g., `/v1/unicorns`)
  - Maintain a CHANGELOG file documenting API changes
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add API version prefix to all routes. Implement OpenAPI spec diffing in CI (requires CI/CD first — see ENG-Q2).
- **Evidence**: Controller `@RequestMapping` paths: `/unicorns`, `/user`, `/health`, `/data` — no version prefix. No changelog file.

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No distributed tracing (no X-Ray, no OpenTelemetry). No structured logging — only `System.out.println` calls. No correlation IDs or request IDs in responses or logs. Spring Boot Actuator is included but no tracing configuration.
- **Gap**: Cannot trace agent-initiated requests through the system. Cannot correlate failures across components. Debugging agent interactions is impossible.
- **Compensating Controls**:
  - Enable Spring Boot Actuator metrics endpoint (already in dependencies)
  - Add AWS X-Ray SDK as a filter
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add `aws-xray-sdk-spring` or `opentelemetry-javaagent`. Replace `System.out.println` with SLF4J structured JSON logging with MDC correlation IDs.
- **Evidence**: `build.gradle` (spring-boot-starter-actuator present but no tracing dependency), `src/main/java/com/monoToMicro/rest/controller/HealthController.java` (System.out.println only)

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No alerting configuration exists. No CloudWatch alarms, no anomaly detection, no PagerDuty/OpsGenie integration. No IaC to define monitoring infrastructure.
- **Gap**: Target system degradation cannot be detected proactively. Agents will continue calling failed endpoints without operational awareness.
- **Compensating Controls**:
  - Manual monitoring via CloudWatch console
  - Set up basic CloudWatch alarms on EC2 instance metrics
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Deploy CloudWatch alarms for HTTP 5xx error rate and p99 latency. Configure SNS notification for on-call.
- **Evidence**: No IaC files, no monitoring configuration, no alerting setup found in any file.

#### ENG-Q1: Infrastructure Governance — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No Infrastructure as Code exists. No Terraform, CloudFormation, CDK, Helm, or any IaC files. The application is presumably deployed manually to EC2.
- **Gap**: Infrastructure changes are manual, not peer-reviewed, and not drift-detected. The agent-facing surface (EC2 instance, network config, database) cannot be audited or reproduced.
- **Compensating Controls**:
  - Document current infrastructure manually
  - Implement IaC as part of the decomposition effort
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Define infrastructure in CloudFormation or CDK: VPC, EC2 instance, RDS MySQL, security groups, and (future) API Gateway.
- **Evidence**: No .tf, .tfvars, template.yaml, template.json, cdk.json, or any IaC files found in repository.

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No CI/CD pipeline exists. No GitHub Actions, GitLab CI, Jenkins, or CodeBuild configuration. No automated testing of any kind. No contract testing.
- **Gap**: API changes are deployed without automated verification. Breaking changes reach production uncaught.
- **Compensating Controls**:
  - Manual testing before deployment
  - Add a basic CI pipeline as first step
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement GitHub Actions or CodePipeline with: build, unit test, API contract test (Pact or OpenAPI validation), and deploy stages.
- **Evidence**: No .github/workflows/, .gitlab-ci.yml, Jenkinsfile, or buildspec.yml found.

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No deployment configuration exists in the repository. No blue/green, no canary, no CodeDeploy, no Helm rollback. Deployment appears to be manual JAR deployment to EC2.
- **Gap**: If a deployment breaks agent-facing APIs, there is no automated rollback mechanism. Recovery requires manual intervention.
- **Compensating Controls**:
  - Keep previous JAR version on the EC2 instance for manual rollback
  - Implement health check-based auto-rollback
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement CodeDeploy with automatic rollback on health check failure, or migrate to ECS/EKS with rolling deployment and circuit breaker.
- **Evidence**: No deployment configuration found. `build.gradle` has `bootJar { launchScript() }` indicating direct JAR execution on EC2.

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Zero test files exist in the repository. No unit tests, no integration tests, no API tests. The `testImplementation('org.springframework.boot:spring-boot-starter-test')` dependency exists in build.gradle but no test classes use it.
- **Gap**: No automated verification of API behavior. Agent tool assumptions about endpoint behavior cannot be validated.
- **Compensating Controls**:
  - Add integration tests for the critical agent-facing endpoints first
  - Use Postman/Newman collections for API smoke testing
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create API integration tests using Spring Boot Test for each controller endpoint. Priority: GET /unicorns, GET /unicorns/basket/{uuid}, POST /unicorns/basket.
- **Evidence**: No *Test.java or *Tests.java files found. `build.gradle` includes test dependency but `src/test/` directory does not exist.

#### ENG-Q5: Encryption at Rest — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No encryption at rest configuration found. No IaC exists to verify KMS encryption on database storage. No references to KMS keys, encrypted volumes, or encrypted RDS instances.
- **Gap**: User PII (email, names) stored in MySQL may be unencrypted at rest. A disk-level breach exposes all data the agent can access.
- **Compensating Controls**:
  - Verify encryption at rest is enabled on the actual MySQL RDS/EC2 EBS volumes (outside repo scope)
  - Enable RDS encryption if using managed database
- **Remediation Timeline**: 14–30 days
- **Recommendation**: If using RDS, enable encryption at rest with KMS. If using EC2-hosted MySQL, enable EBS volume encryption. Document in IaC when created.
- **Evidence**: No IaC files. No KMS references. Cannot verify encryption state from repository alone.

---

## INFOs — Architecture and Design Inputs

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Write endpoints lack explicit idempotency keys. `POST /unicorns/basket` uses `INSERT IGNORE` which provides database-level idempotency for the (uuid, unicornUuid) combination. `POST /user` has a UNIQUE constraint on email. However, no idempotency key headers or request-level deduplication exists.
- **Implication**: If agent scope is expanded to write-enabled, the `INSERT IGNORE` pattern provides partial idempotency for basket operations but no general idempotency mechanism exists.
- **Recommendation**: When expanding to write-enabled scope, implement explicit idempotency key support for all write endpoints.
- **Evidence**: `src/main/resources/com/monoToMicro/core/repository/mappers/UnicornMapper.xml` (INSERT IGNORE), `database/create_tables.sql` (UNIQUE constraints)

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: All API responses use JSON serialization via Jackson (Spring Boot default). Models use `@JsonInclude(JsonInclude.Include.NON_NULL)`. No XML, binary, or non-standard formats.
- **Implication**: JSON is the ideal format for LLM consumption. No additional parsing logic required for agent tool integration.
- **Recommendation**: No action needed. JSON responses are agent-friendly.
- **Evidence**: `src/main/java/com/monoToMicro/core/model/User.java` (`@JsonInclude`), Spring Boot auto-configuration provides Jackson JSON serialization.

### API-Q7: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: No event emission capability exists. No webhooks, no SNS/SQS/EventBridge integration, no Kafka. The internal event objects (`core/events/` package with 17 classes) are in-process DTOs, not distributed events.
- **Implication**: Agents cannot subscribe to state changes reactively. All agent interactions must be request/response polling-based.
- **Recommendation**: Consider adding EventBridge integration for basket state changes during decomposition. This enables event-reactive agent workflows.
- **Evidence**: `src/main/java/com/monoToMicro/core/events/` (17 event classes — all in-process DTOs), no messaging dependencies in `build.gradle`

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limits are documented. No `X-RateLimit-Remaining` or `Retry-After` headers in responses. No API documentation mentions throttling thresholds.
- **Implication**: Agents have no visibility into call budget. Cannot self-throttle based on remaining capacity.
- **Recommendation**: When rate limiting is implemented (STATE-Q5), also add rate limit response headers and document limits in the API spec.
- **Evidence**: No rate limit headers in controller response construction. No API documentation.

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No optimistic locking or concurrency controls. No version fields, no ETags, no `If-Match` headers. The `INSERT IGNORE` in basket operations prevents duplicate inserts but does not constitute general concurrency control.
- **Implication**: Under write-enabled scope, concurrent agent instances could create race conditions on basket operations. Under read-only scope, this is informational only.
- **Recommendation**: When expanding to write-enabled scope, add version fields to entities and implement optimistic locking.
- **Evidence**: `database/create_tables.sql` (no version column), `src/main/resources/com/monoToMicro/core/repository/mappers/UnicornMapper.xml` (no conditional updates)

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No transaction limits or blast radius controls. No configurable limits on operations per session, maximum records per request, or spend caps. The `GET /data` endpoint returns ALL baskets with no cap.
- **Implication**: Under write-enabled scope, an agent could theoretically add unlimited items to unlimited baskets with no business-domain cap. Under read-only scope, informational only.
- **Recommendation**: When expanding to write-enabled scope, implement per-caller transaction limits (e.g., max basket additions per hour).
- **Evidence**: No transaction limit configuration found. `src/main/java/com/monoToMicro/rest/controller/DataReplicationController.java` (returns all baskets unbounded)

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No draft or pending state exists. Basket additions are immediately committed. User creation is immediate. No two-step confirm pattern.
- **Implication**: Under write-enabled scope, agents would commit all changes immediately with no human review opportunity. Under read-only scope, informational only.
- **Recommendation**: When expanding to write-enabled scope, consider adding an `ORDER` entity with PENDING status that requires confirmation before fulfillment.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/BasketController.java` (immediate write on POST)

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No approval gate mechanism exists. All operations execute immediately without configurable review steps.
- **Implication**: Under write-enabled scope, high-risk operations cannot be gated behind human approval. Under read-only scope, informational only.
- **Recommendation**: Consider implementing Step Functions with human approval tasks for high-value operations when moving to write-enabled scope.
- **Evidence**: No approval workflow endpoints or status-based workflows found in any controller.

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality metrics, profiling, or completeness monitoring exists. No null rate tracking, no duplicate detection, no freshness SLAs.
- **Implication**: Agents acting on incomplete or stale data cannot know the data quality level. The seed data has uniform pricing ($100 for all items) suggesting the data may be test/demo quality.
- **Recommendation**: Add data quality monitoring as part of the operational maturity improvements.
- **Evidence**: `database/create_tables.sql` (seed data with uniform $100 pricing), no data quality tooling references.

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No data catalog, no Glue Data Catalog, no metadata layer describing what data the system holds. The only schema documentation is the `create_tables.sql` file.
- **Implication**: Agent tool builders must reverse-engineer the data model from source code and SQL files. No machine-readable metadata for auto-generating tool descriptions.
- **Recommendation**: Document the data model in a structured format (e.g., add table/column descriptions to an OpenAPI spec or a dedicated data dictionary file).
- **Evidence**: `database/create_tables.sql` (only schema reference)

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No custom business metrics published. No CloudWatch `put_metric_data` calls. No dashboards tracking basket conversion, user registration rates, or product popularity.
- **Implication**: Cannot measure whether agent interactions produce good business outcomes. No signal for agent effectiveness beyond HTTP status codes.
- **Recommendation**: Publish business metrics (basket additions/hour, user registrations, popular products) to CloudWatch or a metrics service.
- **Evidence**: No metrics publishing code found. Spring Boot Actuator included but only provides infrastructure metrics.

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: Pass
- **Finding**: The application exposes a documented REST interface via Spring Boot `@RestController` and `@RequestMapping` annotations. Endpoints: GET /unicorns, POST/DELETE /unicorns/basket, GET /unicorns/basket/{userUuid}, POST /user, POST /user/login, GET /health/ping, GET /health/ishealthy, GET /health/dbping, GET /data. Integration does not require direct database access or UI automation.
- **Gap**: N/A — the application provides a REST API surface suitable for agent integration.
- **Recommendation**: N/A
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/` (5 controller classes)

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, Swagger, AsyncAPI, or machine-readable specification exists.
- **Gap**: Agent tool definitions must be manually authored.
- **Recommendation**: Add springdoc-openapi to auto-generate OpenAPI spec.
- **Evidence**: No openapi.*, swagger.*, *.graphql, *.smithy files found.

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: Errors return bare HTTP status codes with empty bodies.
- **Gap**: Agents cannot distinguish error types or determine retryability.
- **Recommendation**: Implement `@ControllerAdvice` with structured error responses.
- **Evidence**: `BasketController.java`, `UserController.java` — `ResponseEntity(HttpStatus.BAD_REQUEST)` with no body.

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Database-level idempotency via INSERT IGNORE and UNIQUE constraints, but no explicit idempotency key support.
- **Gap**: No request-level idempotency mechanism.
- **Recommendation**: Implement idempotency keys when expanding to write-enabled scope.
- **Evidence**: `UnicornMapper.xml` (INSERT IGNORE), `create_tables.sql` (UNIQUE constraints)

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: All responses are JSON via Jackson. Agent-friendly format.
- **Gap**: None.
- **Recommendation**: No action needed.
- **Evidence**: `User.java` (@JsonInclude), Spring Boot Jackson auto-configuration.

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has operations >30s OR long-running workflows
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: No event emission. Internal event objects are in-process DTOs only.
- **Gap**: No reactive agent integration possible.
- **Recommendation**: Add EventBridge integration during decomposition.
- **Evidence**: `src/main/java/com/monoToMicro/core/events/` (17 in-process DTO classes)

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit documentation or response headers.
- **Gap**: Agents cannot self-throttle.
- **Recommendation**: Add rate limit headers when implementing STATE-Q5.
- **Evidence**: No rate limit references found.

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: OAuth2 configured but `permitAll()` on all endpoints. No authentication enforced.
- **Gap**: No machine identity mechanism. Cannot identify agent callers.
- **Recommendation**: Implement API Gateway with IAM/Cognito authorizers or OAuth2 client credentials.
- **Evidence**: `ResourceServerConfig.java` — `authorizeRequests().anyRequest().permitAll()`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: All endpoints `permitAll()`. No scope differentiation.
- **Gap**: Cannot create restricted agent identities.
- **Recommendation**: Implement RBAC with read-only and read-write roles.
- **Evidence**: All controller methods annotated `@PreAuthorize("permitAll()")`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization. Read and write operations have identical access.
- **Gap**: Cannot restrict agent to read-only operations via authorization.
- **Recommendation**: Implement method-level security annotations differentiated by HTTP method.
- **Evidence**: `ResourceServerConfig.java`, all controllers

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: RISK-SAFETY
- **Finding**: No identity propagation. User context passed as URL parameter, not authenticated token.
- **Gap**: Cannot distinguish agent-as-self vs agent-on-behalf-of-user.
- **Recommendation**: Implement JWT-based identity propagation.
- **Evidence**: `BasketController.java` (`@PathVariable String userUuid`)

#### AUTH-Q5: Credential Management
- **Severity**: RISK-SAFETY
- **Finding**: Hardcoded database credentials in application.properties.
- **Gap**: No secrets management, no rotation.
- **Recommendation**: Migrate to AWS Secrets Manager.
- **Evidence**: `application.properties` — username and password in plaintext.

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No audit logging exists at any layer.
- **Gap**: Cannot attribute actions to callers. No forensic trail.
- **Recommendation**: Implement structured audit logging with immutable storage.
- **Evidence**: No logging configuration, no CloudTrail, no audit interceptors.

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: No identity system exists. Cannot suspend any identity.
- **Gap**: Cannot isolate misbehaving agents.
- **Recommendation**: Implement identity with revocation mechanism (API keys, OAuth2 clients).
- **Evidence**: `ResourceServerConfig.java` — no identity enforcement.

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No compensation or rollback mechanisms. Single-statement operations only.
- **Gap**: Partial state cannot be reverted in multi-step workflows.
- **Recommendation**: Implement compensation endpoints and transaction management.
- **Evidence**: `UnicornServiceImpl.java`, `UnicornMapper.xml`

#### STATE-Q2: Queryable Current State
- **Severity**: Pass
- **Finding**: The application exposes queryable state via GET endpoints: GET /unicorns (all products), GET /unicorns/basket/{userUuid} (user's basket). Agents can inspect current state before deciding actions.
- **Gap**: N/A — queryable state exists.
- **Recommendation**: N/A
- **Evidence**: `UnicornController.java` (GET /unicorns), `BasketController.java` (GET /unicorns/basket/{userUuid})

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No optimistic locking or concurrency controls.
- **Gap**: Concurrent writes could cause race conditions under write-enabled scope.
- **Recommendation**: Add version fields and optimistic locking when expanding scope.
- **Evidence**: `create_tables.sql` (no version column)

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has external dependencies (calls other services or external APIs)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No rate limiting at any layer.
- **Gap**: Runaway agent loops can overwhelm the application.
- **Recommendation**: Deploy API Gateway with throttling or add rate limiting middleware.
- **Evidence**: No rate limiting in build.gradle, application.properties, or IaC.

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No transaction limits or blast radius controls.
- **Gap**: Under write-enabled scope, unbounded operations possible.
- **Recommendation**: Implement per-caller transaction limits for write-enabled scope.
- **Evidence**: No limit configuration found.

#### STATE-Q7: Graceful Degradation Signaling
- **Severity**: RISK-QUALITY
- **Finding**: Health endpoints provide binary status only. No machine-readable degradation signals.
- **Gap**: Agents cannot detect degraded mode.
- **Recommendation**: Enhance health endpoints with granular status and add degradation headers.
- **Evidence**: `HealthController.java`

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No draft or pending state. All writes commit immediately.
- **Gap**: No human review opportunity for agent-proposed changes.
- **Recommendation**: Add PENDING status for write operations under write-enabled scope.
- **Evidence**: `BasketController.java` (immediate commit)

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No approval gate mechanism.
- **Gap**: Cannot configure human approval for specific operations.
- **Recommendation**: Consider Step Functions approval tasks for high-risk operations.
- **Evidence**: No approval workflow found.

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: No staging/sandbox environment configuration.
- **Gap**: No safe testing environment for agent integration.
- **Recommendation**: Create Docker Compose setup for local/staging testing.
- **Evidence**: No Dockerfile, no docker-compose, no environment profiles.

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: PII (email, names) stored and returned via API without filtering. No access control differentiation.
- **Gap**: B1: PII fields exposed. B2: No access differentiation. B3: No classification metadata.
- **Recommendation**: Create agent-facing DTOs excluding PII. Implement scoped access.
- **Evidence**: `User.java`, `UserController.java`, `create_tables.sql`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No data residency configuration. PII stored with no documented residency constraints.
- **Gap**: No mechanism to restrict data transmission across regions.
- **Recommendation**: Document residency requirements. Use same-region LLM endpoints.
- **Evidence**: `application.properties`, `create_tables.sql`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK-QUALITY
- **Finding**: Unbounded SELECT queries with no pagination or filtering.
- **Gap**: Agents receive entire datasets. Context window exhaustion risk.
- **Recommendation**: Add pagination parameters to list endpoints.
- **Evidence**: `UnicornMapper.xml`, `UnicornController.java`

#### DATA-Q4: Input Validation and Schema Enforcement
- **Severity**: RISK-QUALITY
- **Finding**: Only null checks. No validation framework. No structured validation errors.
- **Gap**: Malformed agent payloads not rejected with useful feedback.
- **Recommendation**: Add spring-boot-starter-validation with Bean Validation annotations.
- **Evidence**: `BasketController.java`, `build.gradle`

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK-QUALITY
- **Finding**: Timestamps exist in DB but not exposed via API. No freshness headers.
- **Gap**: Agents cannot determine data freshness.
- **Recommendation**: Map timestamp fields to response DTOs. Add Last-Modified headers.
- **Evidence**: `create_tables.sql`, `UnicornMapper.xml`

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: No PII redaction controls. Minimal current logging but no safeguards.
- **Gap**: Any log verbosity increase leaks PII without protection.
- **Recommendation**: Implement log scrubbing middleware before enabling detailed logging.
- **Evidence**: `HealthController.java` (System.out.println), no log config

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics or monitoring.
- **Implication**: Cannot assess data reliability for agent decisions.
- **Recommendation**: Add data quality monitoring.
- **Evidence**: No quality metrics found.

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: No API versioning, no schema versioning, no breaking change detection.
- **Gap**: Agent tool bindings break silently on API changes.
- **Recommendation**: Version API paths and implement contract testing.
- **Evidence**: Controller @RequestMapping paths without version prefix.

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: Pass
- **Finding**: Field names are human-readable and semantically meaningful: `uuid`, `email`, `firstName`, `lastName`, `unicornUuid`, `name`, `description`, `price`, `image`. No legacy abbreviations requiring data dictionaries.
- **Gap**: N/A — field names are agent-interpretable.
- **Recommendation**: N/A
- **Evidence**: `User.java`, `Unicorn.java`, `UnicornBasket.java`, `create_tables.sql`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No data catalog. Only schema reference is create_tables.sql.
- **Implication**: Agent tool builders must reverse-engineer the data model.
- **Recommendation**: Document data model in structured format.
- **Evidence**: `database/create_tables.sql`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: No tracing, no structured logging, no correlation IDs.
- **Gap**: Cannot debug agent-initiated requests.
- **Recommendation**: Add X-Ray or OpenTelemetry. Implement structured JSON logging.
- **Evidence**: `build.gradle` (actuator present, no tracing), `HealthController.java`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: No alerting configuration.
- **Gap**: Cannot detect target system degradation proactively.
- **Recommendation**: Deploy CloudWatch alarms for error rates and latency.
- **Evidence**: No monitoring/alerting configuration found.

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics. Only infrastructure metrics via Actuator.
- **Implication**: Cannot measure agent interaction quality.
- **Recommendation**: Publish business metrics (basket operations, user registrations).
- **Evidence**: No metrics code found. Actuator in `build.gradle`.

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance
- **Severity**: RISK-QUALITY
- **Finding**: No IaC. Infrastructure presumably managed manually.
- **Gap**: Agent-facing infrastructure is unauditable and non-reproducible.
- **Recommendation**: Define infrastructure in CloudFormation or CDK.
- **Evidence**: No IaC files found.

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: No CI/CD pipeline.
- **Gap**: API changes deployed without verification.
- **Recommendation**: Implement CI/CD with contract testing.
- **Evidence**: No CI/CD configuration files found.

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: No deployment or rollback configuration.
- **Gap**: Cannot roll back broken deployments.
- **Recommendation**: Implement CodeDeploy with health-check-based rollback.
- **Evidence**: `build.gradle` (`bootJar { launchScript() }` — direct JAR execution)

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: Zero test files. Test dependency present but unused.
- **Gap**: No automated verification of API behavior.
- **Recommendation**: Create integration tests for controller endpoints.
- **Evidence**: No test files. `build.gradle` has `testImplementation` unused.

#### ENG-Q5: Encryption at Rest
- **Severity**: RISK-QUALITY
- **Finding**: No encryption configuration verifiable from repo. No IaC with KMS references.
- **Gap**: PII may be unencrypted at rest.
- **Recommendation**: Enable RDS/EBS encryption with KMS.
- **Evidence**: No IaC, no KMS references.

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| src/main/java/com/monoToMicro/Application.java | API-Q1 |
| src/main/java/com/monoToMicro/security/ResourceServerConfig.java | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q7 |
| src/main/java/com/monoToMicro/rest/controller/BasketController.java | API-Q1, API-Q3, AUTH-Q2, AUTH-Q4, DATA-Q4, HITL-Q1 |
| src/main/java/com/monoToMicro/rest/controller/UserController.java | API-Q3, DATA-Q1 |
| src/main/java/com/monoToMicro/rest/controller/UnicornController.java | API-Q1, DATA-Q3 |
| src/main/java/com/monoToMicro/rest/controller/DataReplicationController.java | STATE-Q6 |
| src/main/java/com/monoToMicro/rest/controller/HealthController.java | OBS-Q1, DATA-Q6, STATE-Q7 |
| src/main/java/com/monoToMicro/core/model/User.java | DATA-Q1, DISC-Q2 |
| src/main/java/com/monoToMicro/core/services/UnicornServiceImpl.java | STATE-Q1 |
| src/main/resources/com/monoToMicro/core/repository/mappers/UnicornMapper.xml | API-Q4, STATE-Q1, DATA-Q3, DATA-Q5 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| src/main/resources/application.properties | AUTH-Q5, DATA-Q2 |
| build.gradle | API-Q2, DATA-Q4, OBS-Q1, ENG-Q4 |

### Database Schema
| File | Questions Referenced |
|------|---------------------|
| database/create_tables.sql | API-Q4, DATA-Q1, DATA-Q2, DATA-Q5, STATE-Q3, DISC-Q2 |
