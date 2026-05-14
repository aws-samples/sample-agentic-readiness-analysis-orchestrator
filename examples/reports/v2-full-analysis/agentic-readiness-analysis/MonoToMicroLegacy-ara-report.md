# Agentic Readiness Analysis Report

**Target**: MonoToMicroLegacy (./services/unishop-monolith-to-microservices/MonoToMicroLegacy)
**Date**: 2026-04-17
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**Repository Type**: application
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P0
**Tags**: monolith, java, ec2, decomposition-target
**Context**: Legacy Java Spring Boot monolith on EC2 with MySQL — primary decomposition target. The agent needs access to order and return data through discrete service APIs.

**Archetype Justification**: The application has MySQL database connections via MyBatis, exposes CRUD operations (POST/GET/DELETE on baskets, POST for users), and manages user-specific data with entity lifecycle fields (creation_date, last_modified_date, active). This matches the stateful-crud archetype.

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 2 | **RISK-SAFETY**: 8 | **RISK-QUALITY**: 14 | **INFOs**: 13

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days. The two BLOCKERs (AUTH-Q1: no machine identity authentication, DATA-Q1: unclassified PII) represent fundamental gaps that must be addressed before any agent — even a read-only pilot — can safely interact with this system.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 2 |
| RISK-SAFETY | 8 |
| RISK-QUALITY | 14 |
| RISK | 4 |
| INFO | 13 |
| N/A | 0 |
| Not Evaluated (extended) | 2 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 9 (STATE-Q2, STATE-Q7, DATA-Q3, DATA-Q4, DATA-Q5, ENG-Q4, ENG-Q5, API-Q7, API-Q8 — note: API-Q5, API-Q7, API-Q8, DATA-Q7, DISC-Q2, DISC-Q3, OBS-Q3, ENG-Q4 are always-evaluated INFO/extended)
**Extended Questions Not Triggered**: 2 (API-Q6, STATE-Q4)
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: stateful-crud (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: The application uses Spring Security OAuth2 with `@EnableResourceServer` in `ResourceServerConfig.java`, but the security configuration is entirely disabled: `authorizeRequests().anyRequest().permitAll()`. Every controller method uses `@PreAuthorize("permitAll()")`. There are no service accounts, no machine identity authentication, no API key authentication, no mTLS configuration, and no principal attribution. The OAuth2 framework is present as a dependency but provides zero effective authentication.
- **Gap**: No machine identity authentication exists. Any caller — human, agent, or malicious actor — can invoke any endpoint without identifying themselves. There is no way to distinguish which agent made a call, and no principal to record in audit logs.
- **Remediation**:
  - **Immediate**: Enable the existing Spring Security OAuth2 resource server configuration with a real OAuth2 provider (e.g., Amazon Cognito). Replace `permitAll()` with `authenticated()` as the default policy. Create a dedicated Cognito App Client (client_credentials grant) for agent authentication with a unique `client_id` that is logged with every request.
  - **Target State**: All API endpoints require a valid OAuth2 Bearer token. Agent identities are represented as Cognito App Clients with unique `client_id` values that appear in request logs and CloudTrail.
  - **Estimated Effort**: Medium (2–4 weeks) — OAuth2 infrastructure exists in dependencies, needs activation and provider configuration.
  - **Dependencies**: Interacts with AUTH-Q2 (scoped permissions), AUTH-Q6 (audit logging), AUTH-Q7 (identity suspension). Solving AUTH-Q1 enables solutions for all three.
- **Evidence**: `src/main/java/com/monoToMicro/security/ResourceServerConfig.java` (permitAll config), `src/main/java/com/monoToMicro/rest/controller/BasketController.java` (@PreAuthorize("permitAll()")), `build.gradle` (spring-security-oauth2-autoconfigure dependency)

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: The `unicorn_user` table stores PII fields: `email` (VARCHAR(64), UNIQUE constraint), `first_name` (VARCHAR(64)), and `last_name` (VARCHAR(64)). The `User.java` model class exposes these fields in API responses via `getEmail()`, `getFirstName()`, `getLastName()` without any classification, masking, or access control. The `POST /user/login` endpoint returns the full User object including PII. There are no data classification tags, no field-level encryption, no column-level access controls, and no Amazon Macie integration.
- **Gap**: PII (email, first_name, last_name) is stored, processed, and returned in API responses without classification, access controls, or encryption. An agent with read access to the `/user/login` endpoint receives unredacted PII with no governance boundary.
- **Remediation**:
  - **Immediate**: Classify the `email`, `first_name`, and `last_name` fields as PII in a data classification document. Implement field-level response filtering to exclude PII from agent-accessible responses. Add `@JsonIgnore` to PII fields in `User.java` for agent-facing API responses, or create a separate DTO that excludes PII.
  - **Target State**: All PII fields are classified and tagged. API responses to agents exclude or mask PII unless explicitly authorized. Field-level encryption is applied to PII at rest in MySQL. Amazon Macie is configured to scan for PII exposure.
  - **Estimated Effort**: Medium (2–4 weeks for classification and response filtering; 4–8 weeks for field-level encryption).
  - **Dependencies**: Requires AUTH-Q1 (machine identity) to enforce per-caller PII access controls. Without identity, you cannot restrict which callers see PII.
- **Evidence**: `database/create_tables.sql` (unicorn_user table with email, first_name, last_name), `src/main/java/com/monoToMicro/core/model/User.java` (PII fields exposed), `src/main/java/com/monoToMicro/rest/controller/UserController.java` (login returns full User object), `src/main/resources/com/monoToMicro/core/repository/mappers/UserMapper.xml` (getByEmail returns all user fields)

**Remediation Prioritization**: Resolve AUTH-Q1 (machine identity) first — you cannot enforce data access controls (DATA-Q1) without knowing who is calling. Once identity is in place, implement PII classification and response filtering. Consider scoping the initial agent to read-only operations on the `/unicorns` endpoint (which contains no PII) while remediating both BLOCKERs.
## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The authorization model is `permitAll()` across all endpoints in `ResourceServerConfig.java`. There are no IAM policies scoping permissions, no role-per-service configuration, no API Gateway resource policies, and no condition keys. Every caller has full access to every endpoint — there are no permission boundaries whatsoever.
- **Gap**: No least-privilege enforcement. An agent identity (once created via AUTH-Q1 remediation) would inherit access to all endpoints including user PII endpoints, basket modifications, and health/diagnostic endpoints.
- **Compensating Controls**:
  - Deploy an API Gateway in front of the EC2 application with resource policies that restrict the agent's API key to specific read-only paths (e.g., `GET /unicorns` only).
  - Use network-level controls (security groups) to limit which agent infrastructure can reach the application.
- **Remediation Timeline**: 30–60 days (implement after AUTH-Q1)
- **Recommendation**: After enabling OAuth2 authentication (AUTH-Q1), implement role-based access control with Spring Security. Define an `AGENT_READER` role with access limited to `GET /unicorns` and `GET /unicorns/basket/{uuid}`. Deny access to `POST /user`, `POST /user/login`, and write endpoints.
- **Evidence**: `src/main/java/com/monoToMicro/security/ResourceServerConfig.java` (permitAll), all controller classes (@PreAuthorize("permitAll()"))

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization exists. All endpoints use `@PreAuthorize("permitAll()")`. There are no ABAC policies, no fine-grained RBAC definitions, no permission matrices, and no `canRead`/`canWrite`/`canDelete` checks in any controller or service class.
- **Gap**: An agent cannot be granted read-only access to a resource while being denied write/delete access to the same resource type. The basket resource supports GET, POST, and DELETE — all are equally accessible.
- **Compensating Controls**:
  - Use API Gateway method-level authorization to restrict agent API keys to GET methods only.
  - Configure the agent orchestration layer to only invoke GET endpoints, enforced by the agent tool definitions.
- **Remediation Timeline**: 30–60 days (implement alongside AUTH-Q2)
- **Recommendation**: Implement Spring Security method-level authorization with distinct roles for read vs. write operations. Apply `@PreAuthorize("hasRole('READER')")` to GET endpoints and `@PreAuthorize("hasRole('WRITER')")` to POST/DELETE endpoints.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/BasketController.java` (POST, DELETE, GET all permitAll), `src/main/java/com/monoToMicro/rest/controller/UserController.java` (POST permitAll)

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY (would be BLOCKER if write-enabled)
- **Finding**: No audit logging exists. The only logging in the application is `System.out.println` in `HealthController.java` for EC2 instance metadata. No CloudTrail configuration exists (no IaC in the repository). No CloudWatch log retention policies. No immutable log storage. Exception handling uses `e.printStackTrace()` which goes to stderr with no structured format.
- **Gap**: No audit trail for any API call. If an agent reads user PII or modifies a basket, there is no log recording which principal performed the action, when, or what data was accessed.
- **Compensating Controls**:
  - Add a Spring Boot request logging filter that records method, path, timestamp, and caller IP for every request to stdout (captured by EC2 instance logs).
  - Configure CloudWatch Logs agent on EC2 to capture application logs with a 90-day retention policy.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Replace `System.out.println` with SLF4J/Logback structured JSON logging. Add a request interceptor that logs the authenticated principal (after AUTH-Q1), HTTP method, endpoint, timestamp, and response status for every request. Ship logs to CloudWatch Logs with object lock retention. Enable CloudTrail for the AWS account.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/HealthController.java` (System.out.println), `src/main/java/com/monoToMicro/core/repository/UnicornRepositoryImpl.java` (e.printStackTrace()), `src/main/java/com/monoToMicro/core/repository/UserRepositoryImpl.java` (e.printStackTrace())

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No agent identity concept exists in the application. Since all endpoints are `permitAll()`, there is no identity to suspend. There are no API key revocation endpoints, no IAM role deactivation procedures, no service account disable mechanisms, and no Cognito user pool integration.
- **Gap**: If an agent exhibits anomalous behavior, there is no mechanism to suspend or revoke its access without taking down the entire application or modifying network rules.
- **Compensating Controls**:
  - Use network-level controls (security group rules) to block agent traffic by source IP as an emergency kill switch.
  - If API Gateway is added (per AUTH-Q2 compensating control), use API key disabling as the suspension mechanism.
- **Remediation Timeline**: 30–60 days (implement alongside AUTH-Q1)
- **Recommendation**: When implementing Cognito App Clients for agent identity (AUTH-Q1), ensure each agent has a unique App Client. Suspension is then achieved by disabling the specific App Client in Cognito without affecting other agents or users.
- **Evidence**: `src/main/java/com/monoToMicro/security/ResourceServerConfig.java` (no identity model), `build.gradle` (OAuth2 dependency exists but unused)

#### STATE-Q1: Compensation and Rollback ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY (would be BLOCKER if write-enabled)
- **Finding**: No saga patterns, no two-phase commit, no explicit undo endpoints, and no compensating transactions exist in the codebase. Basket operations (`addUnicornToBasket`, `removeUnicornFromBasket`) are simple INSERT/DELETE SQL operations in `UnicornMapper.xml` with no multi-step coordination. User creation in `UserServiceImpl.java` performs a single INSERT with no rollback logic.
- **Gap**: No compensation or rollback mechanism for any operation. If a multi-step agent workflow fails mid-sequence, there is no way to undo prior steps.
- **Compensating Controls**:
  - Scope the agent to read-only operations only (current agent_scope), which eliminates the need for write rollback.
  - For future write-enabled scope, implement compensating actions at the agent orchestration layer (e.g., agent removes basket item if subsequent step fails).
- **Remediation Timeline**: 60–90 days (required before expanding to write-enabled scope)
- **Recommendation**: Before expanding agent_scope to write-enabled, implement explicit undo endpoints (e.g., `DELETE /unicorns/basket` already exists) and document compensating transaction patterns for multi-step workflows.
- **Evidence**: `src/main/java/com/monoToMicro/core/services/UnicornServiceImpl.java` (no compensation logic), `src/main/resources/com/monoToMicro/core/repository/mappers/UnicornMapper.xml` (simple INSERT/DELETE)

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No rate limiting exists at any layer. The application runs directly on EC2 (port 8080) with no API Gateway, no WAF, and no application-level rate limiting middleware. There is no `spring-boot-starter-web` rate limiter, no Bucket4j, no Resilience4j rate limiter. The Spring Boot application accepts unlimited concurrent requests.
- **Gap**: A runaway agent loop or misconfigured agent could send thousands of requests per second directly to the application, potentially overwhelming the EC2 instance and MySQL database.
- **Compensating Controls**:
  - Deploy an AWS API Gateway in front of the EC2 application with usage plans and throttling (e.g., 100 requests/second default, 50 requests/second per agent API key).
  - Configure an AWS WAF rate-based rule to limit requests from any single IP to 2000 per 5-minute window.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add API Gateway with throttling as the immediate fix. This also provides the infrastructure for AUTH-Q1 (API key authentication) and AUTH-Q2 (resource policies). For defense in depth, add application-level rate limiting with Bucket4j or Spring Cloud Gateway.
- **Evidence**: `build.gradle` (no rate limiting dependencies), `src/main/resources/application.properties` (server.port=8080, direct EC2 exposure), absence of any IaC defining API Gateway or WAF

#### DATA-Q2: Data Residency and Sovereignty ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY (would be BLOCKER if write-enabled)
- **Finding**: No data residency documentation or controls exist. The MySQL database endpoint is parameterized via `MONO_TO_MICRO_DB_ENDPOINT` environment variable in `application.properties`, but there are no region constraints, no GDPR/LGPD compliance references, and no cross-region replication controls. The database stores PII (email, names) with no documented residency requirements.
- **Gap**: If the agent transmits user PII (email, names) to an LLM provider endpoint in a different region or jurisdiction, it may create a compliance violation. The absence of residency documentation means the compliance boundary is unknown.
- **Compensating Controls**:
  - Document the AWS region where the MySQL database is deployed and establish a data residency policy.
  - Configure the agent to use Amazon Bedrock in the same region as the database to ensure PII does not cross regional boundaries.
- **Remediation Timeline**: 14–30 days (documentation); 30–60 days (enforcement)
- **Recommendation**: Document data residency requirements for the unicorn_user table PII. If GDPR applies, ensure all agent-LLM communication stays within the same AWS region. Use Amazon Bedrock's regional endpoints to guarantee data locality.
- **Evidence**: `src/main/resources/application.properties` (MONO_TO_MICRO_DB_ENDPOINT env var, no region constraint), `database/create_tables.sql` (unicorn_user table with PII)

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No PII redaction exists in any logging path. The application uses `System.out.println` and `e.printStackTrace()` for all logging. Exception handlers in `UnicornRepositoryImpl.java` and `UserRepositoryImpl.java` call `e.printStackTrace()` which dumps full stack traces that may contain user data (email addresses in SQL queries, user objects in method parameters). There is no log scrubbing middleware, no PII masking library, no CloudWatch log filters, and no Amazon Macie integration.
- **Gap**: If an agent triggers an error on the `/user/login` endpoint, the `e.printStackTrace()` may dump the user's email address into the application's stderr stream. Agent-initiated requests processing PII will leak that PII into observable log surfaces.
- **Compensating Controls**:
  - Add a log sanitization filter that redacts email patterns (`[^@]+@[^@]+\.[^@]+`) and name fields from all log output before writing.
  - Restrict log access to authorized security personnel only.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Replace all `e.printStackTrace()` calls with SLF4J/Logback structured logging that applies PII masking patterns. Implement a custom Logback encoder that redacts email addresses, names, and other PII patterns. Configure CloudWatch Logs metric filters to alert on PII patterns that escape redaction.
- **Evidence**: `src/main/java/com/monoToMicro/core/repository/UnicornRepositoryImpl.java` (e.printStackTrace()), `src/main/java/com/monoToMicro/core/repository/UserRepositoryImpl.java` (e.printStackTrace()), `src/main/java/com/monoToMicro/rest/controller/HealthController.java` (System.out.println)

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, Swagger, AsyncAPI, GraphQL schema, or Smithy specification files exist anywhere in the repository. The API surface is defined exclusively through Spring annotations in Java controller classes (`@RequestMapping`, `@RestController`, `@Controller`). The spec is not auto-generated from annotations — no Springdoc or SpringFox dependencies are present in `build.gradle`.
- **Gap**: Agent frameworks cannot auto-generate tool definitions from the API. Every integration requires manual tool authoring based on reading Java source code, which will drift from actual behavior over time.
- **Compensating Controls**:
  - Manually create agent tool definitions based on the controller annotations until an OpenAPI spec is generated.
  - Add Springdoc OpenAPI dependency to auto-generate a spec from existing annotations.
- **Remediation Timeline**: 7–14 days
- **Recommendation**: Add `springdoc-openapi-ui` dependency to `build.gradle` and annotate controllers with `@Operation` and `@ApiResponse`. This auto-generates an OpenAPI 3.0 spec at `/v3/api-docs` from existing Spring annotations.
- **Evidence**: `build.gradle` (no springdoc/springfox dependency), absence of any `openapi.yaml`, `swagger.yaml`, or `.graphql` files in the repository

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Error responses use only HTTP status codes with no structured body. Controllers return `ResponseEntity<Void>(HttpStatus.BAD_REQUEST)` for errors — an empty body with a 400 status. There are no error codes, no error messages, no retryable indicators, and no consistent error response format. Success responses return the model object or `HttpStatus.OK`/`HttpStatus.CREATED`.
- **Gap**: An agent receiving a 400 response cannot determine whether the error is due to invalid input (terminal), a missing resource (terminal), or a transient condition (retryable). The agent must guess, leading to unnecessary retries or premature failures.
- **Compensating Controls**:
  - Define error interpretation rules in the agent tool definitions (e.g., "400 = terminal, do not retry; 500 = retryable with backoff").
  - Add a Spring `@ControllerAdvice` exception handler that returns structured JSON error bodies.
- **Remediation Timeline**: 7–14 days
- **Recommendation**: Implement a global `@ControllerAdvice` exception handler that returns a consistent JSON error body: `{"error_code": "BASKET_NOT_FOUND", "message": "...", "retryable": false}`. Map all existing exception paths to structured error responses.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/BasketController.java` (ResponseEntity<Void>(HttpStatus.BAD_REQUEST)), `src/main/java/com/monoToMicro/rest/controller/UnicornController.java` (HttpStatus.BAD_REQUEST with no body)

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No separate environment configurations exist in the repository. There is no docker-compose for local testing, no environment-specific application properties (e.g., `application-staging.properties`), no seed data scripts beyond the initial `create_tables.sql`, no synthetic data generators, and no staging environment references.
- **Gap**: There is no safe environment to test agent behavior before production. The first time an agent interacts with this system will be against live data.
- **Compensating Controls**:
  - Create a separate MySQL instance with anonymized data for agent testing.
  - Use the `MONO_TO_MICRO_DB_ENDPOINT` environment variable to point the application at a test database.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Create a `docker-compose.yml` with MySQL and the application for local agent testing. Add `application-staging.properties` with a staging database endpoint. Create a seed data script with synthetic (non-PII) test data.
- **Evidence**: `src/main/resources/application.properties` (single environment config), `database/create_tables.sql` (production seed data only), absence of Docker or environment-specific configuration files

#### DATA-Q3: Selective Query Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The `GET /unicorns` endpoint executes `SELECT * FROM unicorns` with no pagination, filtering, or sorting (per `UnicornMapper.xml`). The `GET /data` endpoint in `DataReplicationController.java` retrieves all baskets via `getAllBaskets()` which also has no pagination. The `GET /unicorns/basket/{userUuid}` endpoint returns all items for a user with no limit.
- **Gap**: An agent retrieving unicorns gets the entire table in a single response. As the product catalog grows, this will exhaust LLM context windows and increase token costs. There is no way for an agent to request "the first 10 unicorns" or "unicorns under $50".
- **Compensating Controls**:
  - Implement pagination at the agent orchestration layer by parsing full responses and processing in chunks.
  - The current dataset is small (10 unicorn records) — this is not an immediate operational risk but will become one at scale.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add pagination parameters (`?limit=20&offset=0`) to the `GET /unicorns` endpoint. Update `UnicornMapper.xml` to use `LIMIT` and `OFFSET` in the SQL query. Add filter parameters for price range and name search.
- **Evidence**: `src/main/resources/com/monoToMicro/core/repository/mappers/UnicornMapper.xml` (SELECT * FROM unicorns, no LIMIT), `src/main/java/com/monoToMicro/rest/controller/DataReplicationController.java` (getAllBaskets with no pagination)

#### DATA-Q4: System of Record Designations — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No system-of-record designations exist. There is no documentation identifying this application as the authoritative source for unicorn products, user accounts, or basket data. No master data management references, no data ownership documentation, and no conflict resolution logic exist in the codebase.
- **Gap**: An agent querying multiple systems may encounter conflicting product or user data. Without a golden record designation, the agent cannot determine which source to trust.
- **Compensating Controls**:
  - Document in the agent tool definitions that this system is the authoritative source for unicorn product data and user basket data.
- **Remediation Timeline**: 7–14 days (documentation only)
- **Recommendation**: Create a data ownership document identifying this monolith as the system of record for unicorns, user accounts, and baskets. As decomposition proceeds, update ownership as each microservice assumes authority for its domain.
- **Evidence**: Absence of any data ownership or system-of-record documentation in the repository

#### DATA-Q5: Temporal Metadata and Freshness — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Database tables have `creation_date` (TIMESTAMP DEFAULT CURRENT_TIMESTAMP) and `last_modified_date` (TIMESTAMP NULL) columns in `create_tables.sql`. The `CoreModel.java` base class has `DateTime creationDate` and `DateTime lastModifiedDate` fields with `DateTimeTypeHandler` for UTC conversion. However, both fields are annotated `@JsonIgnore` — they exist in the database but are **not exposed** in API responses. No `Cache-Control` headers, no `X-Data-Age` headers, and no freshness signaling exist.
- **Gap**: An agent has no way to know when data was last updated. The timestamps exist in the database but are hidden from API consumers. An agent cannot reason about data freshness or detect stale data.
- **Compensating Controls**:
  - Remove `@JsonIgnore` from `creationDate` and `lastModifiedDate` in `CoreModel.java` to expose temporal metadata in API responses.
- **Remediation Timeline**: 7–14 days (simple code change)
- **Recommendation**: Remove `@JsonIgnore` from temporal fields in `CoreModel.java`, or create response DTOs that include `createdAt` and `updatedAt` fields. Add `Cache-Control` response headers to indicate data freshness.
- **Evidence**: `database/create_tables.sql` (creation_date, last_modified_date columns), `src/main/java/com/monoToMicro/core/model/CoreModel.java` (@JsonIgnore on creationDate, lastModifiedDate), `src/main/java/com/monoToMicro/config/DateTimeTypeHandler.java` (UTC conversion)

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No schema versioning exists. There are no JSON Schema files, no schema registry, no Avro/Protobuf schemas, and no database migration files (only `create_tables.sql` with no versioning). API URLs have no version prefix (`/unicorns` instead of `/v1/unicorns`). No changelog files, no deprecation notices, and no breaking change detection tools exist.
- **Gap**: Agent tool schemas will break silently when API changes are deployed. There is no mechanism to detect breaking changes before they affect agent behavior, and no versioning to allow gradual migration.
- **Compensating Controls**:
  - Pin agent tool definitions to specific response field expectations and add validation in the agent orchestration layer.
  - Add OpenAPI spec (per API-Q2 recommendation) with spec diff comparison in any future CI/CD pipeline.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add API version prefix (`/v1/`) to all endpoints. Generate an OpenAPI spec and commit it to the repository. Add a schema comparison step to any future CI/CD pipeline to detect breaking changes.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/UnicornController.java` (@RequestMapping("/unicorns") — no version prefix), absence of any schema files or migration tools

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No distributed tracing exists — no OpenTelemetry SDK, no AWS X-Ray instrumentation, no `traceparent` header propagation. Logging is exclusively `System.out.println` (in `HealthController.java`) and `e.printStackTrace()` (in repository implementations). Logs are unstructured plain text with no JSON format, no correlation IDs, and no `request_id` fields.
- **Gap**: When an agent-initiated request fails, there is no way to trace it through the system. The unstructured logs cannot be queried, correlated, or filtered to diagnose agent-specific issues.
- **Compensating Controls**:
  - Add SLF4J/Logback with JSON formatting as an immediate improvement to enable log querying.
  - Add a Spring request interceptor that generates and logs a `request_id` for every inbound request.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Replace all `System.out.println` and `e.printStackTrace()` with SLF4J logging. Configure Logback with JSON encoder (logstash-logback-encoder). Add AWS X-Ray SDK to `build.gradle` for distributed tracing. Add a Spring `HandlerInterceptor` that generates and propagates `X-Request-Id`.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/HealthController.java` (System.out.println), `src/main/java/com/monoToMicro/core/repository/UnicornRepositoryImpl.java` (e.printStackTrace()), `build.gradle` (no tracing dependencies)

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No alerting configuration exists anywhere in the repository. No CloudWatch alarms, no anomaly detection, no PagerDuty/OpsGenie integration, no composite alarms, and no SLO-based alerting. The only health check is the `GET /health/ishealthy` endpoint returning a static string. Spring Boot Actuator is included as a dependency but no custom health indicators or metrics are configured.
- **Gap**: If the system degrades (high error rates, increased latency), there is no alert to notify operators. Agents will continue calling a degraded system, cascading failures without anyone being notified.
- **Compensating Controls**:
  - Configure CloudWatch alarms on EC2 instance metrics (CPU, memory) as a proxy for application health.
  - Use Spring Boot Actuator's `/actuator/health` endpoint with a monitoring tool to detect application-level issues.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Configure CloudWatch alarms for HTTP 5xx error rate > 5% and P99 latency > 2 seconds on the endpoints agents will consume. Integrate with SNS for alert notification. Add custom CloudWatch metrics from the application using the AWS SDK.
- **Evidence**: `build.gradle` (spring-boot-starter-actuator dependency), `src/main/java/com/monoToMicro/rest/controller/HealthController.java` (basic health endpoints), absence of any CloudWatch alarm configuration

#### ENG-Q1: Infrastructure Governance — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No Infrastructure as Code files exist in the repository. No Terraform, CloudFormation, CDK, Helm, or Kustomize definitions were found. The application runs on EC2 but the infrastructure is not defined as code — there are no peer review requirements for infrastructure changes and no drift detection. The context confirms this is an EC2 deployment with MySQL.
- **Gap**: The agent-facing integration surface (EC2 instance, security groups, MySQL database) is not governed by IaC. Changes to the infrastructure are manual, unreviewed, and untracked. A misconfigured security group could expose the application without any code review.
- **Compensating Controls**:
  - Document the existing infrastructure configuration manually and implement change management procedures.
  - Implement AWS Config rules to detect drift from the expected configuration.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Define the application infrastructure in CloudFormation or CDK: EC2 instance, security groups, RDS MySQL, and (new) API Gateway. Store IaC in this repository. Require PR review for all IaC changes. Enable AWS Config for drift detection.
- **Evidence**: Absence of any `.tf`, `.cfn.yaml`, `cdk.json`, `Chart.yaml`, or `kustomization.yaml` files in the repository

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No CI/CD pipeline files exist in the repository. No GitHub Actions, GitLab CI, Jenkins, CodeBuild, or any other pipeline configuration was found. There are no API contract tests, no consumer-driven contract testing (Pact), no OpenAPI spec validation, and no schema comparison tools.
- **Gap**: API changes can be deployed without any automated validation. Agent tool bindings may break on deployment with no pre-production detection. There is no automated build, test, or deployment process.
- **Compensating Controls**:
  - Manual deployment with checklist review until CI/CD is implemented.
  - Document the API contract in agent tool definitions and manually validate after each deployment.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a GitHub Actions or CodePipeline CI/CD pipeline. Include build, unit test, API contract test (once OpenAPI spec exists), and deployment stages. Add breaking change detection with OpenAPI diff on PR.
- **Evidence**: Absence of any `.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`, or `buildspec.yml` files in the repository

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No deployment or rollback configuration exists. No blue/green deployment, no CodeDeploy rollback triggers, no Helm rollback, no feature flags, no canary deployment, and no traffic shifting. The application is deployed directly on EC2 with no evident deployment orchestration.
- **Gap**: If a deployment breaks agent-facing APIs, there is no automated mechanism to roll back to the previous version. Recovery requires manual intervention on the EC2 instance.
- **Compensating Controls**:
  - Maintain a backup of the previous application JAR on the EC2 instance for manual rollback.
  - Use EC2 AMI snapshots before deployments as a rollback mechanism.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement CodeDeploy with blue/green deployment for the EC2 application. Configure automatic rollback on CloudWatch alarm triggers (e.g., 5xx rate exceeds threshold). Target rollback time: 15 minutes.
- **Evidence**: Absence of any deployment configuration files, `build.gradle` (bootJar task with launchScript — suggests direct JAR deployment on EC2)

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No test files exist in the repository. While `spring-boot-starter-test` is declared as a `testImplementation` dependency in `build.gradle`, no actual test classes were found. No test directories (`src/test/`), no Postman/Newman collections, no pytest API tests, no REST Assured test classes, and no contract tests exist.
- **Gap**: There are zero automated tests for the APIs agents will consume. Any code change could break agent-facing endpoints without detection.
- **Compensating Controls**:
  - Manually test API endpoints after each deployment using curl or Postman.
  - Define agent tool definitions with response validation that detects unexpected changes.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create integration tests for all agent-facing endpoints using Spring Boot Test with MockMvc or REST Assured. Prioritize tests for `GET /unicorns` and `GET /unicorns/basket/{uuid}` — the endpoints the agent will consume. Include tests for error responses and edge cases.
- **Evidence**: `build.gradle` (testImplementation('org.springframework.boot:spring-boot-starter-test')), absence of any `src/test/` directory or test files

#### ENG-Q5: Encryption at Rest — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No encryption at rest configuration exists. No `kms_key_id` settings, no customer-managed KMS keys, and no encryption configuration in IaC (no IaC exists). The MySQL connection string in `application.properties` uses `jdbc:mysql://` with no SSL/TLS parameters (no `useSSL=true`, no `requireSSL=true`). The database stores PII (email, names) and financial data (prices) without evident encryption.
- **Gap**: Data at rest in the MySQL database (including PII) is not demonstrably encrypted. Data in transit between the application and MySQL is not encrypted. An agent accessing this data through the API is reading from potentially unencrypted storage.
- **Compensating Controls**:
  - Enable MySQL encryption at rest using Amazon RDS encryption (if using RDS) or LUKS on EC2 EBS volumes.
  - Add `useSSL=true&requireSSL=true` to the JDBC connection string for encryption in transit.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: If using Amazon RDS, enable encryption at rest with a KMS customer-managed key. Add SSL parameters to the JDBC connection string. If using EC2 with self-managed MySQL, encrypt the EBS volume. Document the encryption configuration in IaC.
- **Evidence**: `src/main/resources/application.properties` (jdbc:mysql:// with no SSL parameters), absence of any IaC with KMS or encryption configuration

#### AUTH-Q4: Identity Propagation and Delegation — RISK

- **Severity**: RISK
- **Finding**: No identity propagation exists. Beyond the disabled OAuth2 resource server in `ResourceServerConfig.java`, there is no JWT parsing middleware, no on-behalf-of flows, no token exchange patterns, no Cognito/Okta integration, and no user context headers passed through service calls. The application cannot distinguish between an agent acting under its own identity vs. acting on behalf of a specific user.
- **Gap**: If an agent queries basket data on behalf of a user, the system has no mechanism to propagate the user's identity or enforce the user's permission scope. The agent's access is undifferentiated.
- **Compensating Controls**:
  - In the read-only agent scope, pass user context as a query parameter (e.g., `GET /unicorns/basket/{userUuid}`) rather than relying on identity propagation.
  - Document that the agent acts under its own service identity for all operations.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: When implementing OAuth2 (AUTH-Q1), add support for JWT token exchange so the system can distinguish agent-as-self vs. agent-on-behalf-of-user. Log both identities in audit records.
- **Evidence**: `src/main/java/com/monoToMicro/security/ResourceServerConfig.java` (disabled OAuth2), absence of JWT parsing or token exchange logic

#### AUTH-Q5: Credential Management — RISK

- **Severity**: RISK
- **Finding**: Database credentials are hardcoded in `application.properties`: `spring.datasource.username: MonoToMicroUser`, `spring.datasource.password: MonoToMicroPassword`. Only the database endpoint is parameterized via `MONO_TO_MICRO_DB_ENDPOINT` environment variable. No AWS Secrets Manager, no HashiCorp Vault, no credential rotation mechanism exists. The password is committed to the Git repository in plain text.
- **Gap**: Hardcoded credentials in source code are a security vulnerability. A prompt injection attack or agent bug that exposes configuration could leak database credentials. There is no credential rotation, meaning a compromised password requires a code change and redeployment.
- **Compensating Controls**:
  - Rotate the database password and move it to an environment variable as an immediate step (still not ideal but better than hardcoded).
  - Restrict repository access to limit credential exposure.
- **Remediation Timeline**: 7–14 days
- **Recommendation**: Move database credentials to AWS Secrets Manager. Update `application.properties` to use Spring Cloud AWS Secrets Manager integration or environment variable injection from Secrets Manager. Enable automatic credential rotation with a 30-day schedule. Remove hardcoded credentials from the repository and rotate the current password immediately.
- **Evidence**: `src/main/resources/application.properties` (spring.datasource.username: MonoToMicroUser, spring.datasource.password: MonoToMicroPassword)

#### STATE-Q2: Queryable Current State — RISK

- **Severity**: RISK
- **Finding**: Basic state query support exists via GET endpoints: `GET /unicorns` returns all unicorn products, `GET /unicorns/basket/{userUuid}` returns a user's basket contents, and `GET /health/dbping` returns database connectivity status. However, there are no comprehensive status APIs, no resource versioning, and no ETag support for conditional reads.
- **Gap**: An agent can query basic resource state but cannot perform conditional reads (If-None-Match), cannot detect concurrent modifications, and has no way to verify the freshness of the data it reads without timestamps (see DATA-Q5).
- **Compensating Controls**:
  - The existing GET endpoints provide sufficient read access for a read-only agent pilot.
  - Add ETag headers in a future iteration for conditional reads.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add ETag support (based on `last_modified_date`) to GET responses. Add `If-None-Match` header support to avoid unnecessary data transfer. Expose temporal metadata (see DATA-Q5 recommendation).
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/UnicornController.java` (GET /unicorns), `src/main/java/com/monoToMicro/rest/controller/BasketController.java` (GET /unicorns/basket/{userUuid})

#### STATE-Q7: Infrastructure Capacity for Agent Traffic — RISK

- **Severity**: RISK
- **Finding**: No load test results, no auto-scaling policies, no capacity planning documentation, and no circuit breakers exist. The application runs on a single EC2 instance (confirmed by `HealthController.java` using `EC2MetadataUtils`). There is no evidence of auto-scaling groups, load balancers, or any capacity planning for additional traffic.
- **Gap**: The single EC2 instance is not sized or tested for agent traffic patterns. Agent-generated traffic (burst reads, exploratory queries, retries) may overwhelm the instance, especially the MySQL connection pool.
- **Compensating Controls**:
  - Rate limit agent traffic at API Gateway (see STATE-Q5) to cap maximum requests per second.
  - Monitor EC2 CPU/memory during initial agent pilot and scale if needed.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Conduct load testing with representative agent traffic patterns (burst reads of /unicorns at 50–100 requests/second). Implement an Auto Scaling Group behind an ALB. Size the MySQL connection pool for concurrent agent access.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/HealthController.java` (EC2MetadataUtils — single instance), absence of auto-scaling or load testing configuration
## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO
- **Finding**: The application exposes a documented REST interface via Spring Boot `@RestController` and `@Controller` annotations. Endpoints: `GET /unicorns` (product catalog), `POST /unicorns/basket` (add to basket), `DELETE /unicorns/basket` (remove from basket), `GET /unicorns/basket/{userUuid}` (view basket), `POST /user` (register), `POST /user/login` (authenticate), `GET /health/ping` (instance info), `GET /health/ishealthy` (health check), `GET /health/dbping` (database health), `GET /data` (all baskets). Integration is via REST APIs — no direct database access, file-based exchange, or UI automation required.
- **Implication**: The REST API surface is the minimum viable integration point for agent tools. Agents can bind to these endpoints. The agent's primary read endpoints are `GET /unicorns` and `GET /unicorns/basket/{userUuid}`.
- **Recommendation**: For the agent's intended use case (order and return data access), the current endpoints provide basket data. Consider adding dedicated order/return endpoints if those concepts are distinct from baskets in the domain model.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/UnicornController.java`, `src/main/java/com/monoToMicro/rest/controller/BasketController.java`, `src/main/java/com/monoToMicro/rest/controller/UserController.java`, `src/main/java/com/monoToMicro/rest/controller/HealthController.java`, `src/main/java/com/monoToMicro/rest/controller/DataReplicationController.java`

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Write endpoints use `INSERT IGNORE` in `UnicornMapper.xml` for basket adds (partial idempotency — duplicate inserts are silently ignored due to UNIQUE constraint on `(uuid, unicornUuid)`). User creation also uses `INSERT IGNORE` in `UserMapper.xml`. However, there are no explicit idempotency key headers, no idempotency middleware, and no idempotency tokens. The `DELETE` endpoint for basket removal is inherently idempotent.
- **Implication**: For the current read-only agent scope, idempotency of write endpoints is informational. If agent_scope is expanded to write-enabled, the `INSERT IGNORE` pattern provides basic safety for basket adds but not for all write operations.
- **Recommendation**: If expanding to write-enabled scope, add explicit idempotency key support (e.g., `Idempotency-Key` header) for all POST endpoints.
- **Evidence**: `src/main/resources/com/monoToMicro/core/repository/mappers/UnicornMapper.xml` (INSERT IGNORE), `src/main/resources/com/monoToMicro/core/repository/mappers/UserMapper.xml` (insert ignore)

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: API responses are structured JSON, which is the default for Spring Boot with Jackson. Model classes use `@JsonInclude(JsonInclude.Include.NON_NULL)` to exclude null fields from responses. `@JsonSerialize(include = JsonSerialize.Inclusion.NON_NULL)` is used on `CoreModel`. Responses are standard JSON objects and arrays.
- **Implication**: JSON responses are optimal for LLM consumption. Agents can parse responses directly without format conversion. The `NON_NULL` inclusion policy keeps responses clean.
- **Recommendation**: No action needed. JSON responses are the preferred format for agent tool integration.
- **Evidence**: `src/main/java/com/monoToMicro/core/model/Unicorn.java` (@JsonInclude), `src/main/java/com/monoToMicro/core/model/CoreModel.java` (@JsonSerialize)

### API-Q7: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: No event emission patterns exist. There are no webhook endpoints, no SNS/EventBridge/SQS integration, no Kafka topic producers, and no CDC pipelines. The application has internal event classes (`CreateEvent`, `ReadEvent`, `WriteUnicornsBasketEvent`, etc.) in `com.monoToMicro.core.events`, but these are in-memory domain events used for internal service communication — they are not published externally.
- **Implication**: Agents cannot subscribe to state changes proactively. They must poll endpoints to detect changes. For the current read-only scope (reading product catalog and basket data), polling `GET /unicorns` is sufficient.
- **Recommendation**: As the decomposition proceeds, consider adding SNS/EventBridge event publishing for basket state changes. This enables reactive agent patterns (e.g., agent notified when a basket is modified).
- **Evidence**: `src/main/java/com/monoToMicro/core/events/` (internal event classes only), absence of SNS/SQS/EventBridge/Kafka dependencies in `build.gradle`

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limit documentation exists. No `X-RateLimit-Remaining` or `Retry-After` headers are returned in any API response. No API Gateway throttle settings, no WAF rate rules, and no rate limiting middleware are configured. The application accepts unlimited requests with no self-throttle signaling.
- **Implication**: Agents have no visibility into rate limits and cannot self-throttle based on server feedback. This must be addressed when adding rate limiting infrastructure (STATE-Q5).
- **Recommendation**: When adding API Gateway with throttling (STATE-Q5), configure it to return `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `Retry-After` headers. Document rate limits in the OpenAPI spec (API-Q2).
- **Evidence**: All controller classes (no rate limit headers in ResponseEntity), `build.gradle` (no rate limiting dependencies)

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Minimal concurrency controls exist. `UserRepositoryImpl.create()` uses the `synchronized` keyword for thread-level mutual exclusion. `UnicornMapper.xml` uses `INSERT IGNORE` which handles duplicate key conflicts silently. However, there is no optimistic locking (no version fields, no ETags, no `If-Match` headers), no pessimistic locking (`SELECT FOR UPDATE`), and no DynamoDB conditional writes.
- **Implication**: For read-only agent scope, concurrency controls for write operations are informational. If expanded to write-enabled, the `synchronized` keyword provides basic protection for user creation but does not scale across multiple instances.
- **Recommendation**: If expanding to write-enabled scope, implement optimistic locking with a `version` column in database tables and ETags in API responses.
- **Evidence**: `src/main/java/com/monoToMicro/core/repository/UserRepositoryImpl.java` (synchronized create method), `src/main/resources/com/monoToMicro/core/repository/mappers/UnicornMapper.xml` (INSERT IGNORE)

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits exist. There are no maximum records per operation, no maximum spend limits, no per-agent action caps. The application does not enforce any business-logic limits on agent-initiated actions.
- **Implication**: For read-only agent scope, transaction limits for write operations are informational. The only risk is unbounded read queries (addressed in DATA-Q3). If expanded to write-enabled, transaction limits become critical.
- **Recommendation**: If expanding to write-enabled scope, implement configurable per-agent limits (e.g., `max_basket_adds_per_hour=100`).
- **Evidence**: All service implementation classes (no limit enforcement logic), all controller classes (no per-request limits)

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No draft or pending state concepts exist. Basket operations (`addUnicornToBasket`, `removeUnicornFromBasket`) take effect immediately. User creation is immediate with no confirmation step. There are no status fields, no approval workflows, and no two-step commit patterns.
- **Implication**: For read-only agent scope, draft states are informational. If expanded to write-enabled, the absence of draft states means all agent-initiated writes are immediately committed with no human review.
- **Recommendation**: If expanding to write-enabled scope, add a `status` field to the `unicorns_basket` table (e.g., `PENDING`, `CONFIRMED`) and require a separate confirmation step for agent-initiated basket modifications.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/BasketController.java` (immediate write), `database/create_tables.sql` (no status fields)

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No approval gate mechanism exists. There are no approval API endpoints, no status-based workflows requiring explicit confirmation, no configurable operation-level flags, and no Step Functions with human approval tasks.
- **Implication**: For read-only agent scope, approval gates are informational. If expanded to write-enabled, high-risk operations (e.g., basket checkout, user deletion) should require human approval.
- **Recommendation**: If expanding to write-enabled scope, implement a configurable approval gate using Amazon Step Functions with `waitForTaskToken` for high-value operations.
- **Evidence**: All controller classes (no approval logic), absence of Step Functions or workflow definitions

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality metrics, dashboards, profiling reports, null rate monitoring, or duplicate detection logic exist. The only data quality mechanism is the UNIQUE constraint on `uuid` in the unicorns table and `email` in the unicorn_user table. Initial seed data in `create_tables.sql` contains 10 hardcoded unicorn records with uniform pricing ($100 each).
- **Implication**: An agent cannot assess data quality before acting on it. With uniform pricing and limited product data, the current dataset quality is high but synthetic. Real production data may have quality issues that the agent cannot detect.
- **Recommendation**: Add data profiling for key fields (null rates, uniqueness, completeness) as the dataset grows. Consider adding a `/data/quality` endpoint that returns basic statistics for agent consumption.
- **Evidence**: `database/create_tables.sql` (UNIQUE constraints, seed data), absence of data quality tooling

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Field names are reasonably semantic and human-readable. Java model fields use camelCase: `uuid`, `name`, `description`, `price`, `image`, `email`, `firstName`, `lastName`. Database columns use snake_case: `first_name`, `last_name`, `creation_date`, `last_modified_date`. No legacy abbreviations or cryptic codes were found. MyBatis mappers handle the camelCase-to-snake_case translation transparently.
- **Implication**: LLM-based agents can interpret field names without a data dictionary. The naming conventions are consistent and self-documenting.
- **Recommendation**: No action needed. Maintain these naming conventions as the application is decomposed into microservices.
- **Evidence**: `src/main/java/com/monoToMicro/core/model/Unicorn.java` (uuid, name, description, price, image), `src/main/java/com/monoToMicro/core/model/User.java` (uuid, email, firstName, lastName), `database/create_tables.sql` (snake_case columns)

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No data catalog or metadata layer exists. No AWS Glue Data Catalog, no Collibra, no Alation, no DataHub, no metadata files, no data dictionaries beyond what is implied by the schema definition in `create_tables.sql`.
- **Implication**: Tool definition for agents must be done manually by reading the schema and controller code. There is no machine-readable catalog describing what data the system holds.
- **Recommendation**: As the decomposition proceeds, create an AWS Glue Data Catalog entry for the MySQL database. Document data semantics in the OpenAPI spec descriptions (per API-Q2 recommendation).
- **Evidence**: Absence of any data catalog configuration, `database/create_tables.sql` (schema is the only metadata source)

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No custom business metrics exist. No `cloudwatch.put_metric_data` calls, no custom dashboards, and no business KPI alarms. Spring Boot Actuator is included as a dependency (`spring-boot-starter-actuator` in `build.gradle`), providing default infrastructure metrics (JVM, HTTP request counts), but no custom business outcome metrics are configured.
- **Implication**: When agents interact with the system, there is no way to measure whether those interactions produce good business outcomes (e.g., basket conversion rate, user registration success rate). Only infrastructure metrics are available.
- **Recommendation**: Add custom CloudWatch metrics for key business events: baskets created, items added to basket, user registrations. These metrics become the primary signal for agent effectiveness when agents start consuming the API.
- **Evidence**: `build.gradle` (spring-boot-starter-actuator dependency), absence of custom metric publishing code
## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO (passes BLOCKER check — REST API exists)
- **Finding**: The application exposes REST endpoints via Spring Boot `@RestController` and `@Controller` annotations. Endpoints: `GET /unicorns`, `POST /unicorns/basket`, `DELETE /unicorns/basket`, `GET /unicorns/basket/{userUuid}`, `POST /user`, `POST /user/login`, `GET /health/*`, `GET /data`. Integration is via documented REST APIs — no direct database access, file-based exchange, or UI automation required.
- **Gap**: N/A — REST API surface exists.
- **Recommendation**: For the agent's intended use case (order and return data), consider adding dedicated order/return endpoints if distinct from baskets.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/UnicornController.java`, `src/main/java/com/monoToMicro/rest/controller/BasketController.java`, `src/main/java/com/monoToMicro/rest/controller/UserController.java`, `src/main/java/com/monoToMicro/rest/controller/HealthController.java`, `src/main/java/com/monoToMicro/rest/controller/DataReplicationController.java`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, Swagger, AsyncAPI, GraphQL schema, or Smithy specification files exist. API surface defined only through Spring annotations in Java code. No Springdoc or SpringFox dependencies in `build.gradle`.
- **Gap**: No machine-readable API specification for agent tool auto-generation.
- **Recommendation**: Add `springdoc-openapi-ui` to `build.gradle` for OpenAPI 3.0 auto-generation.
- **Evidence**: `build.gradle` (no spec generation dependency), absence of spec files

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: Error responses use only HTTP status codes (`HttpStatus.BAD_REQUEST`) with empty bodies. No structured error codes, messages, or retryable indicators. Controllers return `ResponseEntity<Void>(HttpStatus.BAD_REQUEST)` for all error cases.
- **Gap**: Agents cannot distinguish retriable from terminal errors.
- **Recommendation**: Implement `@ControllerAdvice` with structured JSON error bodies.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/BasketController.java`, `src/main/java/com/monoToMicro/rest/controller/UnicornController.java`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Write endpoints use `INSERT IGNORE` (partial idempotency via UNIQUE constraints). No explicit idempotency keys or middleware. `DELETE` is inherently idempotent.
- **Gap**: No formal idempotency mechanism — informational for read-only scope.
- **Recommendation**: Add `Idempotency-Key` header support before expanding to write-enabled scope.
- **Evidence**: `src/main/resources/com/monoToMicro/core/repository/mappers/UnicornMapper.xml` (INSERT IGNORE)

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: JSON responses via Spring Boot Jackson defaults. `@JsonInclude(NON_NULL)` on model classes. Standard JSON objects and arrays.
- **Gap**: N/A — JSON is the preferred format.
- **Recommendation**: No action needed.
- **Evidence**: `src/main/java/com/monoToMicro/core/model/Unicorn.java`, `src/main/java/com/monoToMicro/core/model/CoreModel.java`

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has operations >30s OR long-running workflows. This is a simple CRUD app with direct MySQL queries — no operations exceed 30 seconds.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: No event emission patterns. Internal event classes exist (`com.monoToMicro.core.events`) but are in-memory only — not published externally. No SNS, SQS, EventBridge, Kafka, or webhook code.
- **Gap**: Agents cannot subscribe to state changes proactively.
- **Recommendation**: Add SNS/EventBridge publishing for basket state changes during decomposition.
- **Evidence**: `src/main/java/com/monoToMicro/core/events/` (internal only), `build.gradle` (no messaging dependencies)

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit documentation, headers, or middleware. Application accepts unlimited requests with no self-throttle signaling.
- **Gap**: Agents cannot self-throttle based on server feedback.
- **Recommendation**: Configure rate limit headers when adding API Gateway (STATE-Q5).
- **Evidence**: All controller classes (no rate limit headers)

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: Spring Security OAuth2 with `@EnableResourceServer` is present but disabled: `authorizeRequests().anyRequest().permitAll()`. All controllers use `@PreAuthorize("permitAll()")`. No machine identity, no API keys, no mTLS, no principal attribution.
- **Gap**: No machine identity authentication exists. Any caller can invoke any endpoint without identification.
- **Recommendation**: Enable OAuth2 with Cognito App Clients for agent machine identity.
- **Evidence**: `src/main/java/com/monoToMicro/security/ResourceServerConfig.java`, `build.gradle`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: `permitAll()` across all endpoints. No IAM policies, no role-per-service, no API Gateway resource policies. Zero permission boundaries.
- **Gap**: No least-privilege enforcement for agent identities.
- **Recommendation**: Implement RBAC with `AGENT_READER` role after AUTH-Q1 remediation.
- **Evidence**: `src/main/java/com/monoToMicro/security/ResourceServerConfig.java`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization. All methods use `@PreAuthorize("permitAll()")`. No ABAC, no fine-grained RBAC.
- **Gap**: Cannot restrict agent to read-only access on resources that support both read and write.
- **Recommendation**: Apply method-level Spring Security with read/write role separation.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/BasketController.java` (GET, POST, DELETE all permitAll)

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: RISK
- **Finding**: No identity propagation. Disabled OAuth2 resource server. No JWT parsing, no token exchange, no user context headers.
- **Gap**: Cannot distinguish agent-as-self vs. agent-on-behalf-of-user.
- **Recommendation**: Implement JWT token exchange when enabling OAuth2 (AUTH-Q1).
- **Evidence**: `src/main/java/com/monoToMicro/security/ResourceServerConfig.java`

#### AUTH-Q5: Credential Management
- **Severity**: RISK
- **Finding**: Database credentials hardcoded in `application.properties`: username `MonoToMicroUser`, password `MonoToMicroPassword`. Only DB endpoint uses environment variable. No Secrets Manager, no Vault, no rotation.
- **Gap**: Credentials in source code — security vulnerability. No credential rotation.
- **Recommendation**: Move to AWS Secrets Manager with automatic rotation.
- **Evidence**: `src/main/resources/application.properties`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No audit logging. Only `System.out.println` and `e.printStackTrace()`. No CloudTrail, no CloudWatch log retention, no immutable storage.
- **Gap**: No audit trail for any API call. Cannot prove who accessed what.
- **Recommendation**: Implement SLF4J/Logback JSON logging with request interceptor and CloudWatch Logs.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/HealthController.java`, `src/main/java/com/monoToMicro/core/repository/UnicornRepositoryImpl.java`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: No identity concept exists to suspend. `permitAll()` means no identity is tracked. No API key revocation, no service account disable.
- **Gap**: Cannot suspend a misbehaving agent without application-wide disruption.
- **Recommendation**: Use per-agent Cognito App Clients with individual disable capability.
- **Evidence**: `src/main/java/com/monoToMicro/security/ResourceServerConfig.java`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No saga, two-phase commit, undo endpoints, or compensating transactions. Operations are simple INSERT/DELETE with no multi-step coordination.
- **Gap**: No compensation for failed multi-step operations.
- **Recommendation**: Implement compensating transaction patterns before expanding to write-enabled scope.
- **Evidence**: `src/main/java/com/monoToMicro/core/services/UnicornServiceImpl.java`, `src/main/resources/com/monoToMicro/core/repository/mappers/UnicornMapper.xml`

#### STATE-Q2: Queryable Current State
- **Severity**: RISK
- **Finding**: Basic state queryable via `GET /unicorns` and `GET /unicorns/basket/{userUuid}`. No resource versioning, no ETags, no conditional reads.
- **Gap**: No conditional read support (If-None-Match, ETags).
- **Recommendation**: Add ETag support and expose temporal metadata.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/UnicornController.java`, `src/main/java/com/monoToMicro/rest/controller/BasketController.java`

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: `synchronized` keyword on user creation. `INSERT IGNORE` for conflict resolution. No optimistic/pessimistic locking.
- **Gap**: Minimal — informational for read-only scope.
- **Recommendation**: Add optimistic locking before expanding to write-enabled scope.
- **Evidence**: `src/main/java/com/monoToMicro/core/repository/UserRepositoryImpl.java`, `src/main/resources/com/monoToMicro/core/repository/mappers/UnicornMapper.xml`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has external dependencies (calls other services or external APIs). This monolith is self-contained — only MySQL dependency, no external service calls.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No rate limiting at any layer. Direct EC2 exposure on port 8080. No API Gateway, WAF, or application-level rate limiter.
- **Gap**: No protection against runaway agent traffic.
- **Recommendation**: Deploy API Gateway with throttling as immediate fix.
- **Evidence**: `build.gradle`, `src/main/resources/application.properties`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits. No per-agent action caps.
- **Gap**: Informational for read-only scope.
- **Recommendation**: Implement per-agent limits before expanding to write-enabled scope.
- **Evidence**: All service and controller classes

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: RISK
- **Finding**: Single EC2 instance. No load tests, no auto-scaling, no capacity planning. Uses `EC2MetadataUtils` confirming EC2 deployment.
- **Gap**: Not sized for agent traffic patterns.
- **Recommendation**: Load test, implement Auto Scaling Group, size MySQL connection pool.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/HealthController.java`

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No draft/pending state concepts. All operations are immediate. No status fields in database tables.
- **Gap**: Informational for read-only scope.
- **Recommendation**: Add status fields before expanding to write-enabled scope.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/BasketController.java`, `database/create_tables.sql`

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No approval gates. No approval endpoints, no Step Functions, no configurable flags.
- **Gap**: Informational for read-only scope.
- **Recommendation**: Implement Step Functions with `waitForTaskToken` for write-enabled scope.
- **Evidence**: All controller classes

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: No staging environment. Single `application.properties`. No docker-compose, no seed data scripts beyond `create_tables.sql`.
- **Gap**: No safe environment to test agent behavior before production.
- **Recommendation**: Create docker-compose with MySQL for local agent testing.
- **Evidence**: `src/main/resources/application.properties`, `database/create_tables.sql`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: PII (email, first_name, last_name) in `unicorn_user` table. Exposed in API responses without classification, masking, or access controls. No field-level encryption, no Macie.
- **Gap**: Unclassified PII exposed to all callers.
- **Recommendation**: Classify PII fields. Implement response filtering for agent-facing endpoints.
- **Evidence**: `database/create_tables.sql`, `src/main/java/com/monoToMicro/core/model/User.java`, `src/main/java/com/monoToMicro/rest/controller/UserController.java`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No data residency documentation or controls. DB endpoint parameterized via env var but no region constraints. PII stored with no residency policy.
- **Gap**: Compliance boundary unknown for agent-LLM data transmission.
- **Recommendation**: Document residency requirements. Use same-region Bedrock endpoints.
- **Evidence**: `src/main/resources/application.properties`, `database/create_tables.sql`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK-QUALITY
- **Finding**: `GET /unicorns` returns `SELECT * FROM unicorns` with no pagination. `GET /data` returns all baskets. No filters, sorting, or limits.
- **Gap**: Unbounded result sets for agent queries.
- **Recommendation**: Add pagination (`?limit=20&offset=0`) and filter parameters.
- **Evidence**: `src/main/resources/com/monoToMicro/core/repository/mappers/UnicornMapper.xml`

#### DATA-Q4: System of Record Designations
- **Severity**: RISK-QUALITY
- **Finding**: No system-of-record designations. No data ownership documentation.
- **Gap**: No golden record designation for agent decision-making.
- **Recommendation**: Document this monolith as system of record for unicorns, users, baskets.
- **Evidence**: Absence of data ownership documentation

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK-QUALITY
- **Finding**: `creation_date` and `last_modified_date` columns exist in DB. `CoreModel.java` has DateTime fields but annotated `@JsonIgnore`. Timestamps not exposed in API responses. No Cache-Control headers.
- **Gap**: Timestamps exist but hidden from API consumers.
- **Recommendation**: Remove `@JsonIgnore` from temporal fields or create DTOs that include them.
- **Evidence**: `database/create_tables.sql`, `src/main/java/com/monoToMicro/core/model/CoreModel.java`

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: No PII redaction. `e.printStackTrace()` may dump email addresses in SQL errors. `System.out.println` for logging. No log scrubbing, no masking.
- **Gap**: PII leaks into observable log surfaces on errors.
- **Recommendation**: Replace `e.printStackTrace()` with SLF4J with PII masking.
- **Evidence**: `src/main/java/com/monoToMicro/core/repository/UnicornRepositoryImpl.java`, `src/main/java/com/monoToMicro/core/repository/UserRepositoryImpl.java`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics. UNIQUE constraints provide basic deduplication. Seed data is synthetic with uniform pricing.
- **Gap**: Agent cannot assess data quality.
- **Recommendation**: Add data profiling for key fields as dataset grows.
- **Evidence**: `database/create_tables.sql`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: No schema versioning. No JSON Schema, no schema registry, no migration tools. No API version prefixes. No breaking change detection.
- **Gap**: Agent tool schemas break silently on API changes.
- **Recommendation**: Add `/v1/` prefix and OpenAPI spec with diff detection.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/UnicornController.java`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Semantic field names: `uuid`, `name`, `description`, `price`, `email`, `firstName`, `lastName`. No legacy abbreviations.
- **Gap**: N/A — names are self-documenting.
- **Recommendation**: Maintain naming conventions during decomposition.
- **Evidence**: `src/main/java/com/monoToMicro/core/model/Unicorn.java`, `src/main/java/com/monoToMicro/core/model/User.java`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No data catalog. Schema in `create_tables.sql` is the only metadata source.
- **Gap**: No machine-readable catalog for tool definition.
- **Recommendation**: Create Glue Data Catalog entry during decomposition.
- **Evidence**: `database/create_tables.sql`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: No OpenTelemetry, no X-Ray, no traceparent propagation. `System.out.println` and `e.printStackTrace()` only. No JSON logs, no correlation IDs.
- **Gap**: Agent-initiated failures not debuggable.
- **Recommendation**: Add SLF4J/Logback JSON logging and X-Ray SDK.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/HealthController.java`, `build.gradle`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: No CloudWatch alarms, no anomaly detection, no alerting. Spring Boot Actuator dependency present but unconfigured.
- **Gap**: No alerts for system degradation affecting agent operations.
- **Recommendation**: Configure CloudWatch alarms for 5xx rate and P99 latency.
- **Evidence**: `build.gradle`, absence of monitoring configuration

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics. Actuator provides only infrastructure metrics.
- **Gap**: Cannot measure agent interaction business outcomes.
- **Recommendation**: Add custom CloudWatch metrics for baskets created, items added, registrations.
- **Evidence**: `build.gradle`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance
- **Severity**: RISK-QUALITY
- **Finding**: No IaC files. EC2 deployment with no Terraform, CloudFormation, CDK, Helm. No peer review, no drift detection.
- **Gap**: Integration surface not governed by code.
- **Recommendation**: Define infrastructure in CDK/CloudFormation. Enable AWS Config drift detection.
- **Evidence**: Absence of IaC files

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: No CI/CD pipeline files. No GitHub Actions, GitLab CI, Jenkins, CodeBuild. No contract tests.
- **Gap**: API changes deployed without validation.
- **Recommendation**: Create CI/CD pipeline with API contract testing.
- **Evidence**: Absence of pipeline configuration files

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: No deployment orchestration. No blue/green, no CodeDeploy, no feature flags. Direct JAR deployment on EC2.
- **Gap**: No automated rollback for agent-breaking deployments.
- **Recommendation**: Implement CodeDeploy with blue/green and automatic rollback.
- **Evidence**: `build.gradle` (bootJar with launchScript)

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: Zero test files. `spring-boot-starter-test` declared but no test classes exist. No `src/test/` directory.
- **Gap**: No automated tests for agent-facing APIs.
- **Recommendation**: Create integration tests with MockMvc or REST Assured.
- **Evidence**: `build.gradle`

#### ENG-Q5: Encryption at Rest
- **Severity**: RISK-QUALITY
- **Finding**: No encryption at rest configuration. No KMS keys, no encryption in IaC. JDBC connection without SSL/TLS parameters. PII stored potentially unencrypted.
- **Gap**: Data at rest and in transit not demonstrably encrypted.
- **Recommendation**: Enable RDS encryption with KMS. Add SSL to JDBC connection string.
- **Evidence**: `src/main/resources/application.properties`
## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `src/main/java/com/monoToMicro/Application.java` | AUTH-Q1 |
| `src/main/java/com/monoToMicro/security/ResourceServerConfig.java` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q7 |
| `src/main/java/com/monoToMicro/rest/controller/BasketController.java` | API-Q1, API-Q3, AUTH-Q1, AUTH-Q3, STATE-Q2, HITL-Q1 |
| `src/main/java/com/monoToMicro/rest/controller/UnicornController.java` | API-Q1, API-Q3, STATE-Q2, DISC-Q1 |
| `src/main/java/com/monoToMicro/rest/controller/UserController.java` | API-Q1, AUTH-Q3, DATA-Q1 |
| `src/main/java/com/monoToMicro/rest/controller/HealthController.java` | API-Q1, AUTH-Q6, OBS-Q1, STATE-Q7, DATA-Q6 |
| `src/main/java/com/monoToMicro/rest/controller/DataReplicationController.java` | API-Q1, DATA-Q3 |
| `src/main/java/com/monoToMicro/rest/controller/CoreController.java` | API-Q1 |
| `src/main/java/com/monoToMicro/core/model/CoreModel.java` | API-Q5, DATA-Q5 |
| `src/main/java/com/monoToMicro/core/model/Unicorn.java` | API-Q5, DISC-Q2 |
| `src/main/java/com/monoToMicro/core/model/UnicornBasket.java` | API-Q1 |
| `src/main/java/com/monoToMicro/core/model/User.java` | DATA-Q1, DISC-Q2 |
| `src/main/java/com/monoToMicro/core/repository/UnicornRepositoryImpl.java` | AUTH-Q6, DATA-Q6, OBS-Q1 |
| `src/main/java/com/monoToMicro/core/repository/UserRepositoryImpl.java` | STATE-Q3, AUTH-Q6, DATA-Q6 |
| `src/main/java/com/monoToMicro/core/services/UnicornServiceImpl.java` | STATE-Q1 |
| `src/main/java/com/monoToMicro/core/services/UserServiceImpl.java` | STATE-Q1 |
| `src/main/java/com/monoToMicro/config/MyBatisConfig.java` | API-Q1 |
| `src/main/java/com/monoToMicro/config/CoreConfig.java` | AUTH-Q1 |
| `src/main/java/com/monoToMicro/config/DateTimeTypeHandler.java` | DATA-Q5 |
| `src/main/java/com/monoToMicro/config/MVCConfig.java` | API-Q1 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `build.gradle` | AUTH-Q1, AUTH-Q7, API-Q2, API-Q8, STATE-Q5, OBS-Q1, OBS-Q2, OBS-Q3, ENG-Q3, ENG-Q4 |
| `gradle/wrapper/gradle-wrapper.properties` | ENG-Q1 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `src/main/resources/application.properties` | AUTH-Q5, DATA-Q2, STATE-Q5, ENG-Q5, HITL-Q3 |
| `src/main/resources/com/monoToMicro/core/repository/mappers/UnicornMapper.xml` | API-Q4, STATE-Q1, STATE-Q3, DATA-Q3 |
| `src/main/resources/com/monoToMicro/core/repository/mappers/UserMapper.xml` | API-Q4, DATA-Q1 |
| `src/main/resources/com/monoToMicro/core/repository/mappers/HealthMapper.xml` | API-Q1 |

### Database Scripts
| File | Questions Referenced |
|------|---------------------|
| `database/create_tables.sql` | DATA-Q1, DATA-Q2, DATA-Q5, DATA-Q7, DISC-Q2, DISC-Q3, HITL-Q1 |

### Notable Absences (evidence by absence)
| Category | Absence | Questions Impacted |
|----------|---------|-------------------|
| IaC files | No `.tf`, `.cfn.yaml`, `cdk.json`, `Chart.yaml`, `kustomization.yaml` | ENG-Q1, AUTH-Q6, STATE-Q5 |
| API specifications | No `openapi.yaml`, `swagger.yaml`, `.graphql`, `.smithy` | API-Q2, DISC-Q1 |
| CI/CD configurations | No `.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`, `buildspec.yml` | ENG-Q2, ENG-Q3 |
| Container definitions | No `Dockerfile`, `docker-compose.yml` | HITL-Q3 |
| Test files | No `src/test/` directory, no test classes | ENG-Q4 |
| Environment files | No `.env`, no `application-staging.properties` | HITL-Q3 |
| Monitoring config | No CloudWatch alarm definitions, no alerting config | OBS-Q2 |

---

*End of Agentic Readiness Analysis Report*
