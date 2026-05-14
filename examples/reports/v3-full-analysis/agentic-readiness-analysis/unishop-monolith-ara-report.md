# Agentic Readiness Analysis Report

**Target**: MonoToMicroLegacy (./services/unishop-monolith-to-microservices/MonoToMicroLegacy)
**Date**: 2026-04-27
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**Repository Type**: application
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P0
**Tags**: monolith, java, ec2, decomposition-target
**Context**: Legacy Java Spring Boot monolith on EC2 with MySQL — primary decomposition target. The agent needs access to order and return data through discrete service APIs.

**Archetype Justification**: The repository has MySQL database connections with CRUD operations (INSERT, SELECT, DELETE on `unicorns_basket`; INSERT/SELECT on `unicorn_user`; SELECT on `unicorns`), user-specific data (user UUID, email, first/last name), and entity lifecycle management via `CoreModel` base class with creation/modification timestamps. This matches the **stateful-crud** archetype.

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 2 | **RISK-SAFETY**: 9 | **RISK-QUALITY**: 18 | **INFOs**: 10

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days. The two BLOCKERs (AUTH-Q1: no effective authentication, DATA-Q1: unclassified PII) represent fundamental security gaps that must be addressed before any agent — even a read-only one — can safely interact with this system. Additionally, 9 RISK-SAFETY findings indicate significant safety gaps across identity management, rate limiting, audit logging, and data residency that will need prioritized remediation after BLOCKERs are resolved.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 2 |
| RISK-SAFETY | 9 |
| RISK-QUALITY | 18 |
| INFO | 10 |
| N/A | 0 |
| Not Evaluated (extended) | 4 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 15
**Extended Questions Not Triggered**: 4
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: stateful-crud (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: The application uses Spring Security OAuth2 (`@EnableResourceServer` in `ResourceServerConfig.java`) but configures `authorizeRequests().anyRequest().permitAll()` — effectively disabling all authentication. Every controller endpoint uses `@PreAuthorize("permitAll()")`. No service account, API key, mTLS, or Cognito client configuration exists. The OAuth2 resource server framework is present but is a no-op.
- **Gap**: No effective authentication mechanism exists. Any caller — human, agent, or attacker — can invoke any endpoint without providing identity credentials. The system cannot distinguish which agent (or any caller) made a request.
- **Remediation**:
  - **Immediate**: Implement OAuth2 client credentials flow or API key authentication with principal attribution. Configure `ResourceServerConfig` to require valid Bearer tokens on all non-health endpoints. Add an API Gateway (AWS API Gateway or ALB with Cognito) in front of the EC2 instance to enforce authentication at the infrastructure layer.
  - **Target State**: Every API call requires a valid machine identity credential. Authenticated principal is recorded in request context and available for audit logging. Agent identities are distinguishable from human user identities.
  - **Estimated Effort**: High (60–90 days) — requires implementing authentication infrastructure, issuing credentials, and updating all clients.
  - **Dependencies**: Resolving this BLOCKER is a prerequisite for AUTH-Q2 (scoped permissions), AUTH-Q3 (action-level authorization), AUTH-Q6 (audit logging), and AUTH-Q7 (agent identity suspension). Fix identity first.
- **Evidence**: `src/main/java/com/monoToMicro/security/ResourceServerConfig.java` (permitAll config), all controller files (`@PreAuthorize("permitAll()")`), `build.gradle` (spring-security-oauth2 dependency present but unused)

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: The `unicorn_user` table stores PII fields: `email`, `first_name`, `last_name`. The `User.java` model exposes all PII fields (`email`, `firstName`, `lastName`) directly in API responses via `/user` (POST) and `/user/login` (POST) endpoints with no filtering, masking, or field-level access controls. No data classification tags exist on any database table or column. No Amazon Macie integration. No field-level encryption.
- **Gap**: Sensitive data (PII) is stored and transmitted without classification, tagging, or access controls. An agent retrieving user data would receive raw PII (email, full name) with no mechanism to restrict access based on data sensitivity. This creates regulatory exposure (GDPR, CCPA) and reputational risk.
- **Remediation**:
  - **Immediate**: Classify all fields in `unicorn_user` table by sensitivity level. Tag `email`, `first_name`, `last_name` as PII. Implement field-level response filtering — create a separate DTO for agent-facing responses that excludes or masks PII fields not required for the agent's task. Add Amazon Macie to scan the MySQL data store for PII.
  - **Target State**: All sensitive data fields are classified and tagged. API responses to agent callers include only the fields necessary for the task, with PII masked or excluded by default. Field-level access controls are enforced based on the caller's authorization scope.
  - **Estimated Effort**: Medium (30–60 days) — classification is fast; implementing field-level filtering requires API changes.
  - **Dependencies**: AUTH-Q1 must be resolved first — you cannot enforce field-level access controls without knowing who is calling. Interacts with DATA-Q6 (PII in logs).
- **Evidence**: `database/create_tables.sql` (PII columns: email, first_name, last_name in unicorn_user), `src/main/java/com/monoToMicro/core/model/User.java` (exposes email, firstName, lastName), `src/main/resources/com/monoToMicro/core/repository/mappers/UserMapper.xml` (SELECT returns PII without filtering)

**Remediation Prioritization**: Resolve AUTH-Q1 (identity) first — you cannot enforce data access controls (DATA-Q1) without knowing who is calling. Consider scoping the initial agent to read-only product catalog data (`/unicorns` GET endpoint, which contains no PII) while remediating identity and data classification for user-facing endpoints.

---

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No authorization model exists. All endpoints are configured with `permitAll()`. No IAM policies, no role definitions, no scoped permission model. There is no mechanism to grant an agent read-only access to `/unicorns` without also granting write access to `/unicorns/basket` and `/user`.
- **Gap**: Cannot restrict agent access to specific resources or operations. Any authenticated caller (once AUTH-Q1 is resolved) would have full access to all endpoints.
- **Compensating Controls**:
  - Deploy an API Gateway in front of the application with resource-level IAM policies that restrict agent identities to specific endpoints (e.g., agent can only call GET /unicorns and GET /unicorns/basket/{id}).
  - Use network-level controls (Security Groups, VPC endpoints) to limit which services can reach the application.
- **Remediation Timeline**: 30–60 days (after AUTH-Q1 is resolved)
- **Recommendation**: Implement role-based access control in Spring Security with agent-specific roles (e.g., `ROLE_AGENT_READ`) that restrict access to read-only endpoints. Alternatively, place an API Gateway with resource policies in front of the application.
- **Evidence**: `src/main/java/com/monoToMicro/security/ResourceServerConfig.java`, all controller files with `@PreAuthorize("permitAll()")`

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization exists. `@PreAuthorize("permitAll()")` is applied to every endpoint. No `canRead`/`canWrite`/`canDelete` checks. No ABAC or fine-grained RBAC. A caller with access to `/unicorns/basket` can both POST (add) and DELETE (remove) items — there is no way to grant add-only or read-only access within the same resource type.
- **Gap**: Cannot enforce action-level restrictions on agent operations within a resource type.
- **Compensating Controls**:
  - API Gateway method-level authorization (allow GET but deny POST/DELETE for agent identities).
  - Agent orchestration layer limits which HTTP methods the agent tool definitions expose.
- **Remediation Timeline**: 30–60 days (after AUTH-Q1 is resolved)
- **Recommendation**: Replace `@PreAuthorize("permitAll()")` annotations with method-level security expressions (e.g., `@PreAuthorize("hasRole('ADMIN') or hasRole('AGENT_READ')")`) that distinguish read vs write operations.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/BasketController.java` (POST/DELETE/GET all use permitAll), `src/main/java/com/monoToMicro/rest/controller/UserController.java`, `src/main/java/com/monoToMicro/rest/controller/UnicornController.java`

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No audit logging exists. No CloudTrail configuration. No structured logging framework. The application uses `System.out.println()` for output (in `HealthController.ping()`) and `e.printStackTrace()` for exception handling across all repository implementations. No log retention policies. No immutable log storage. No request-level logging that captures the authenticated principal.
- **Gap**: No audit trail exists for any operation. When an agent reads user data or product catalogs, there is no record of who accessed what and when. Cannot conduct forensics or prove compliance.
- **Compensating Controls**:
  - Add a reverse proxy or API Gateway that logs all requests with caller identity, timestamp, and endpoint.
  - Implement structured logging (Logback/SLF4J with JSON format) as a first step before full audit trail.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Replace `System.out.println()` and `e.printStackTrace()` with SLF4J/Logback structured JSON logging. Add a servlet filter that logs authenticated principal, request method, endpoint, and timestamp for every request. Ship logs to CloudWatch Logs with retention and immutability policies.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/HealthController.java` (System.out.println), `src/main/java/com/monoToMicro/core/repository/UnicornRepositoryImpl.java` (e.printStackTrace), `src/main/java/com/monoToMicro/core/repository/UserRepositoryImpl.java` (e.printStackTrace), `src/main/java/com/monoToMicro/core/repository/HealthRepositoryImpl.java` (e.printStackTrace)

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No agent identity mechanism exists (AUTH-Q1 found no effective authentication). Therefore, there is no mechanism to suspend or revoke an individual agent identity. No API key revocation, no IAM role deactivation, no service account disable mechanism, no Cognito user pool management.
- **Gap**: If an agent behaves anomalously, the only recourse is to block all traffic (firewall/security group change) or shut down the application entirely. Cannot isolate a single misbehaving agent without disrupting all consumers.
- **Compensating Controls**:
  - Network-level blocking (Security Group rule changes) to block specific source IPs.
  - API Gateway with API keys — individual keys can be revoked without affecting others.
- **Remediation Timeline**: 30–60 days (after AUTH-Q1 is resolved — identity suspension requires identity to exist first)
- **Recommendation**: When implementing authentication (AUTH-Q1), choose a mechanism that supports individual credential revocation — API keys via API Gateway, or OAuth2 client credentials where individual clients can be disabled.
- **Evidence**: `src/main/java/com/monoToMicro/security/ResourceServerConfig.java` (no auth = no suspension mechanism)

#### STATE-Q1: Compensation and Rollback ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No saga pattern, no two-phase commit, no explicit undo endpoints, no compensating transactions. Spring `@Transactional` annotation on repository classes (`UnicornRepositoryImpl`, `UserRepositoryImpl`) provides single-operation atomicity within a single database call, but no multi-step compensation logic exists. The `addUnicornToBasket` and `removeUnicornFromBasket` operations are independent — a failed sequence of basket operations leaves partial state.
- **Gap**: No mechanism to roll back multi-step operations that fail mid-sequence. If a future write-enabled agent executes a multi-step workflow (e.g., add items to basket then create order), failure partway through leaves the system in an inconsistent state.
- **Compensating Controls**:
  - Limit agent to single-step read operations (current read-only scope already does this).
  - For future write scope, implement compensation logic at the agent orchestration layer.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Before expanding to write-enabled agent scope, implement compensation/undo endpoints for critical write operations. Consider implementing the Saga pattern for multi-step workflows.
- **Evidence**: `src/main/java/com/monoToMicro/core/repository/UnicornRepositoryImpl.java` (@Transactional, no compensation), `src/main/java/com/monoToMicro/core/repository/UserRepositoryImpl.java` (@Transactional, no compensation)

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No circuit breakers, retry logic, or timeout configurations exist. The application calls EC2MetadataUtils (AWS SDK) in `HealthController.ping()` with no timeout or error handling beyond a try-catch that prints "No instance found". MySQL connections through MyBatis have no explicit timeout configuration in `application.properties`. No Resilience4j, Hystrix, or custom retry patterns found. No exponential backoff.
- **Gap**: If MySQL becomes unresponsive or EC2 metadata service is unavailable, the application will hang or cascade failures back to the agent. A runaway agent loop hitting a hung endpoint would create cascading failures.
- **Compensating Controls**:
  - Set database connection timeouts in `application.properties` (e.g., `spring.datasource.hikari.connection-timeout=5000`).
  - Add API Gateway integration timeout limits.
- **Remediation Timeline**: 14–30 days (relatively quick win)
- **Recommendation**: Add connection timeout, socket timeout, and query timeout to the MySQL datasource configuration. Add Resilience4j circuit breaker for the EC2MetadataUtils call. Configure Spring Boot's server timeout settings.
- **Evidence**: `src/main/resources/application.properties` (no timeout config), `src/main/java/com/monoToMicro/rest/controller/HealthController.java` (unprotected EC2MetadataUtils call), `build.gradle` (no resilience library dependency)

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No rate limiting at any layer. No API Gateway, no WAF rate rules, no application-level rate limiting middleware. The application runs directly on EC2 port 8080 with no traffic management. No `express-rate-limit` equivalent for Spring, no `spring-cloud-gateway` rate limiter, no `bucket4j` or `guava RateLimiter` usage.
- **Gap**: A runaway agent loop (or any client) can send unlimited requests to the application at machine speed, potentially exhausting MySQL connections, consuming all EC2 CPU/memory, and causing denial of service for all consumers.
- **Compensating Controls**:
  - Deploy AWS API Gateway in front of the application with usage plans and throttle settings.
  - Deploy AWS WAF with rate-based rules.
  - Agent orchestration layer can implement client-side rate limiting.
- **Remediation Timeline**: 14–30 days (API Gateway deployment is relatively quick)
- **Recommendation**: Deploy an API Gateway (AWS API Gateway or Application Load Balancer) in front of the EC2 instance with rate limiting configured per API key/caller identity. This also helps address AUTH-Q1 (authentication) simultaneously.
- **Evidence**: `src/main/resources/application.properties` (no rate limit config), `build.gradle` (no rate limiting library), absence of any API Gateway or WAF configuration in the repository

#### DATA-Q2: Data Residency and Sovereignty ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No data residency requirements are documented anywhere in the repository. The MySQL connection string uses an environment variable for the endpoint (`${MONO_TO_MICRO_DB_ENDPOINT}`) with no region enforcement — the database could be in any region. No GDPR, LGPD, or HIPAA compliance references. No data sovereignty policies. No cross-region replication configuration visible.
- **Gap**: If the user data (email, names) is subject to data residency requirements (e.g., EU users' PII must stay in eu-west-1), there is no mechanism to prevent an agent from transmitting that data to an LLM endpoint in a different region. The absence of documented residency requirements is itself a gap — it doesn't mean requirements don't exist.
- **Compensating Controls**:
  - Document data residency requirements for the user data in the `unicorn_user` table.
  - Configure the agent to use Amazon Bedrock in the same region as the database.
  - Implement data filtering at the API layer to strip PII before agent access.
- **Remediation Timeline**: 30–60 days (documentation and policy decisions)
- **Recommendation**: Conduct a data residency analysis for the PII stored in `unicorn_user`. Document which regulatory frameworks apply. Configure region-locked deployments and ensure agent LLM endpoints are co-located with the data.
- **Evidence**: `src/main/resources/application.properties` (MySQL endpoint via env var, no region config), `database/create_tables.sql` (PII in unicorn_user table)

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No PII redaction in logging. No log scrubbing middleware. The application uses `System.out.println()` and `e.printStackTrace()` for all output. `HealthController.ping()` logs EC2 metadata (accountId, instanceID) to stdout. Exception handling in all repository implementations uses `e.printStackTrace()` which could include PII from SQL queries or request bodies in stack traces. The `UserMapper.xml` SELECT query includes email, first_name, last_name — if a database exception occurs during this query, the stack trace could contain PII.
- **Gap**: PII (email, names) could leak into logs via exception stack traces during database operations on the `unicorn_user` table. No structured logging means no PII masking can be applied at the logging layer.
- **Compensating Controls**:
  - Replace `e.printStackTrace()` with structured logging that excludes request/response bodies.
  - Add log scrubbing regex patterns for email addresses and names.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Replace all `System.out.println()` and `e.printStackTrace()` calls with SLF4J/Logback structured logging. Implement a custom log appender or converter that redacts PII patterns (email addresses, names). Configure exception handlers to log error codes without full stack traces containing query parameters.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/HealthController.java` (System.out.println with metadata), `src/main/java/com/monoToMicro/core/repository/UnicornRepositoryImpl.java` (e.printStackTrace), `src/main/java/com/monoToMicro/core/repository/UserRepositoryImpl.java` (e.printStackTrace), `src/main/java/com/monoToMicro/core/repository/HealthRepositoryImpl.java` (e.printStackTrace)

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, Swagger, AsyncAPI, GraphQL schema, or Smithy specification files exist in the repository. No auto-generation annotations (springdoc-openapi, springfox) in `build.gradle`. The API surface is defined only in Java controller source code via `@RequestMapping` annotations.
- **Gap**: Agent frameworks cannot auto-generate tool definitions from machine-readable specs. Every tool binding must be manually authored by reading the Java source code, creating drift risk.
- **Compensating Controls**:
  - Manually author OpenAPI spec from controller annotations as a one-time effort.
  - Add springdoc-openapi dependency to auto-generate spec from existing annotations.
- **Remediation Timeline**: 7–14 days
- **Recommendation**: Add `springdoc-openapi-ui` dependency to `build.gradle` to auto-generate OpenAPI 3.0 spec from existing Spring MVC annotations. This is a low-effort, high-value improvement.
- **Evidence**: `build.gradle` (no openapi/swagger dependency), absence of any `*.yaml`/`*.json` OpenAPI files in repository

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Controllers return only HTTP status codes (`HttpStatus.OK`, `HttpStatus.BAD_REQUEST`, `HttpStatus.CREATED`) with no error body, no error codes, and no structured error format. `DataReplicationController.replicate()` returns `null` on failure (line: `return null;`). Error responses contain no information about what went wrong or whether the error is retryable.
- **Gap**: An agent receiving a 400 BAD_REQUEST cannot distinguish between invalid input, missing required fields, or a server-side data issue. No retryable vs terminal error distinction.
- **Compensating Controls**:
  - Agent orchestration layer can implement retry logic based on HTTP status codes alone (retry 5xx, don't retry 4xx).
  - Wrapper service can add structured error bodies.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Implement a global `@ControllerAdvice` exception handler that returns structured JSON error responses with `error_code`, `message`, and `retryable` fields. Fix `DataReplicationController.replicate()` to return a proper error response instead of `null`.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/BasketController.java` (bare HttpStatus returns), `src/main/java/com/monoToMicro/rest/controller/DataReplicationController.java` (returns null on failure), `src/main/java/com/monoToMicro/rest/controller/UnicornController.java`, `src/main/java/com/monoToMicro/rest/controller/UserController.java`

#### AUTH-Q4: Identity Propagation and Delegation — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No identity propagation mechanism exists. No JWT parsing middleware, no OAuth2 on-behalf-of flows, no token exchange patterns. No user context headers (`X-User-Id`, `Authorization Bearer`) are parsed or propagated. The application has no concept of "acting on behalf of" a user — the `/user/login` endpoint is a simple email lookup, not an OAuth flow. No distinction between agent-as-self vs agent-on-behalf-of-user.
- **Gap**: Cannot distinguish whether an agent is acting under its own identity or on behalf of a specific human user. User-scoped permissions cannot be enforced.
- **Compensating Controls**:
  - Agent orchestration layer manages user context and passes user identity as a request parameter.
  - API Gateway can inject caller identity headers.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement JWT-based identity propagation. Configure the OAuth2 resource server (already present but unused) to parse Bearer tokens and extract user context. Add support for the `on-behalf-of` pattern so agents acting for a user inherit that user's permissions.
- **Evidence**: `src/main/java/com/monoToMicro/security/ResourceServerConfig.java` (OAuth2 present but permitAll), `src/main/java/com/monoToMicro/rest/controller/UserController.java` (login is email lookup, not OAuth)

#### AUTH-Q5: Credential Management — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Database credentials are hardcoded in plaintext in `application.properties`: `spring.datasource.username: MonoToMicroUser` and `spring.datasource.password: MonoToMicroPassword`. The database endpoint uses an environment variable (`${MONO_TO_MICRO_DB_ENDPOINT}`), but the username and password are committed to source control in plaintext. No AWS Secrets Manager, no HashiCorp Vault, no encrypted properties.
- **Gap**: Hardcoded credentials in source control are a security vulnerability. If an agent or attacker gains read access to the repository or configuration, database credentials are immediately compromised. No credential rotation capability.
- **Compensating Controls**:
  - Move credentials to environment variables immediately (same pattern as the DB endpoint).
  - Restrict repository access to authorized personnel.
- **Remediation Timeline**: 7–14 days
- **Recommendation**: Move database credentials to AWS Secrets Manager. Update `application.properties` to use the AWS Secrets Manager Spring integration or environment variables. Rotate the current credentials immediately since they are committed to source control.
- **Evidence**: `src/main/resources/application.properties` (plaintext username and password)

#### STATE-Q2: Queryable Current State — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Partial queryable state exists. GET endpoints are available for: unicorn catalog (`GET /unicorns`), user basket (`GET /unicorns/basket/{userUuid}`), health checks (`GET /health/ping`, `GET /health/ishealthy`, `GET /health/dbping`), and user lookup (`POST /user/login` — although this is POST, it's functionally a read). However, there are no order or return state endpoints — the system does not expose order history or return status, which are the primary data the agent needs per the portfolio context.
- **Gap**: The agent needs access to "order and return data" per the context, but no order or return entities or endpoints exist in this application. The agent can query product catalog and user basket state but not order/return state.
- **Compensating Controls**:
  - If order/return data exists in another system, the agent can access it there.
  - Build new order/return APIs as part of the microservices decomposition.
- **Remediation Timeline**: 60–90 days (new feature development)
- **Recommendation**: As part of the monolith decomposition, create dedicated order and return microservices with queryable REST APIs. This aligns with the portfolio goal of building a customer support agent.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/UnicornController.java` (GET /unicorns), `src/main/java/com/monoToMicro/rest/controller/BasketController.java` (GET /unicorns/basket/{userUuid}), `src/main/java/com/monoToMicro/rest/controller/HealthController.java`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No load test results, no auto-scaling policies, no capacity planning documentation. The application runs on a single EC2 instance (evidenced by `EC2MetadataUtils.getInstanceInfo()` usage in `HealthController`). No evidence of Auto Scaling Group, no ELB/ALB configuration, no container orchestration. Server port is hardcoded to 8080 in `application.properties`.
- **Gap**: A single EC2 instance with no auto-scaling cannot handle unpredictable agent traffic patterns. No evidence the application has been load-tested for concurrent agent usage.
- **Compensating Controls**:
  - Agent client-side rate limiting to avoid overwhelming the single instance.
  - Monitor EC2 instance CPU/memory via CloudWatch basic monitoring.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: As part of the modernization effort, containerize the application and deploy to EKS/ECS with auto-scaling policies. In the interim, deploy behind an ALB with health checks and at least 2 EC2 instances in an ASG.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/HealthController.java` (EC2MetadataUtils single-instance pattern), `src/main/resources/application.properties` (server.port: 8080, single instance config)

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No separate environment configurations found. Single `application.properties` with no Spring profiles (no `application-dev.properties`, `application-staging.properties`). No docker-compose for local testing. No seed data scripts beyond `database/create_tables.sql` with sample product inserts. No environment-specific IaC. No feature flags.
- **Gap**: No sandbox or staging environment exists for testing agent behavior against realistic data without risking production systems. The first time you discover an agent bug will be in production.
- **Compensating Controls**:
  - Use `create_tables.sql` to stand up a local MySQL instance for testing.
  - Create a separate EC2 instance with the same application for agent testing.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Create Spring Boot profiles for dev/staging/prod environments. Create a docker-compose file for local testing with MySQL. Build a synthetic data generator for realistic test data. Deploy a staging environment.
- **Evidence**: `src/main/resources/application.properties` (single config, no profiles), `database/create_tables.sql` (only schema definition, minimal seed data)

#### DATA-Q3: Selective Query Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The `getUnicorns` query (`SELECT * FROM unicorns`) returns all records with no pagination, no filtering, no sorting, and no LIMIT clause. The `getAllBaskets` query similarly returns all basket records unbounded. The `getUnicornBasket` query filters by `userUuid` (bounded). The `getByEmail` query filters by email (bounded, single result).
- **Gap**: An agent retrieving the product catalog receives all records in a single response. As the catalog grows, this will exhaust LLM context windows, increase latency, and increase API costs. No mechanism to request "first 10 unicorns sorted by price."
- **Compensating Controls**:
  - Agent orchestration layer can process large responses in chunks.
  - For now, the catalog is small (10 seed records) — bounded in practice but not by design.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add pagination parameters (limit, offset or cursor-based) to the `GET /unicorns` endpoint. Add filter and sort query parameters. Update `UnicornMapper.xml` to include `LIMIT` and `ORDER BY` clauses.
- **Evidence**: `src/main/resources/com/monoToMicro/core/repository/mappers/UnicornMapper.xml` (SELECT * FROM unicorns — no LIMIT), `src/main/java/com/monoToMicro/rest/controller/UnicornController.java` (no pagination parameters)

#### DATA-Q4: System of Record Designations — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No master data management references, no system-of-record designations, no data ownership definitions. The `unicorns` table is presumably the source of truth for product data, `unicorn_user` for user data, and `unicorns_basket` for basket data, but this is not documented or enforced.
- **Gap**: As the monolith is decomposed into microservices, there is no documented authority for which system owns which entity. Agents reasoning across multiple decomposed services will encounter conflicting data without a golden record.
- **Compensating Controls**:
  - Document system-of-record designations as part of the decomposition planning.
  - Until decomposition, the monolith is the de facto SoR for all entities.
- **Remediation Timeline**: 14–30 days (documentation effort)
- **Recommendation**: Document system-of-record designations for each entity (unicorns, users, baskets) as part of the microservices decomposition plan. This will determine which decomposed service owns which data.
- **Evidence**: `database/create_tables.sql` (schema defines entities but no ownership metadata)

#### DATA-Q5: Temporal Metadata and Freshness — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Database schema includes `creation_date` (timestamp DEFAULT CURRENT_TIMESTAMP) and `last_modified_date` (timestamp NULL) on all three tables. UTC timezone is configured in the JDBC URL (`serverTimezone=UTC`). However, the `CoreModel.java` class uses `@JsonIgnore` on both `creationDate` and `lastModifiedDate`, meaning these timestamps are never exposed in API responses. No `Cache-Control` headers, no `X-Data-Age` headers, no freshness signaling in responses.
- **Gap**: An agent cannot determine when data was last updated or whether it is stale. Temporal metadata exists in the database but is explicitly hidden from API consumers by `@JsonIgnore`.
- **Compensating Controls**:
  - Agent can assume data is current since it reads directly from the database (no caching layer visible).
  - Add created/modified timestamps to API responses by removing `@JsonIgnore`.
- **Remediation Timeline**: 7–14 days
- **Recommendation**: Remove `@JsonIgnore` from `creationDate` and `lastModifiedDate` in `CoreModel.java` (or create an agent-facing DTO that includes them). Add `Cache-Control` response headers.
- **Evidence**: `src/main/java/com/monoToMicro/core/model/CoreModel.java` (@JsonIgnore on creationDate, lastModifiedDate), `database/create_tables.sql` (creation_date, last_modified_date columns), `src/main/resources/application.properties` (serverTimezone=UTC in JDBC URL)

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No schema versioning or API contract management. No JSON Schema files, no Avro/Protobuf schemas, no schema registry. No OpenAPI definitions. No versioned API URLs (no `/v1/`, `/v2/` patterns). No changelog files. No deprecation notices. No breaking change detection tools. No consumer-driven contract tests (Pact). Database migration is a single `create_tables.sql` file with no migration tool (no Flyway, no Liquibase). Schema changes would require manual SQL scripts.
- **Gap**: Agent tool bindings break silently when API schemas change. There is no mechanism to detect or communicate breaking changes before they affect agents.
- **Compensating Controls**:
  - Agent tool definitions can include schema validation that detects unexpected response changes.
  - Manual testing after each deployment.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add Flyway or Liquibase for database migrations. Implement API versioning (URL-based `/v1/` prefix). Add OpenAPI spec generation (see API-Q2) and integrate schema diff tools into the build process.
- **Evidence**: `database/create_tables.sql` (single file, no migration tool), absence of versioned URL patterns in any controller, absence of schema files

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No distributed tracing. No OpenTelemetry SDK, no AWS X-Ray instrumentation, no Zipkin/Jaeger integration. `spring-boot-starter-actuator` is included in dependencies (provides health endpoints and basic metrics) but no tracing configuration. Application uses `System.out.println()` and `e.printStackTrace()` for all logging — no structured JSON logging, no SLF4J/Logback configuration, no correlation ID or request_id in any log output.
- **Gap**: Cannot trace an agent-initiated request through the application. If a request fails, there is no correlation ID to link the agent's request to the application's internal processing. Unstructured stdout logging cannot be searched, filtered, or aggregated.
- **Compensating Controls**:
  - API Gateway can generate and log trace IDs for incoming requests.
  - CloudWatch Logs Insights can search unstructured logs (with reduced capability).
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add SLF4J/Logback with JSON format. Add Spring Cloud Sleuth or OpenTelemetry Java agent for automatic trace ID propagation. Configure `correlation-id` header propagation.
- **Evidence**: `build.gradle` (spring-boot-starter-actuator present, no tracing deps), `src/main/java/com/monoToMicro/rest/controller/HealthController.java` (System.out.println), absence of logback.xml or logback-spring.xml

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No alerting configuration of any kind. No CloudWatch alarms, no anomaly detection, no PagerDuty/OpsGenie integration, no SLO-based alerting. No monitoring configuration files. Spring Boot Actuator is present but no custom metric endpoints or alarm definitions.
- **Gap**: If the APIs agents consume experience elevated error rates or increased latency, no one is notified. Agent-caused problems (e.g., excessive load) go undetected until users complain.
- **Compensating Controls**:
  - Manually configure CloudWatch alarms on the EC2 instance (CPU, memory, disk) as a baseline.
  - Agent orchestration layer can track response times and error rates client-side.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Configure CloudWatch alarms for HTTP 5xx error rate, p99 latency, and database connection pool saturation. Integrate with SNS for notifications.
- **Evidence**: `build.gradle` (spring-boot-starter-actuator present but no alarm config), absence of any monitoring/alerting configuration files

#### ENG-Q1: Infrastructure Governance — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No Terraform, CloudFormation, CDK, or any IaC files found in the repository. Infrastructure is presumably manually managed — EC2 instances, MySQL database, security groups, and networking are configured through the AWS Console or CLI with no version-controlled definitions. No drift detection. No peer review for infrastructure changes.
- **Gap**: The integration surface (EC2 instance, network config, security groups) is not defined as code. Changes to infrastructure are manual, unaudited, and unreviewed. Drift between expected and actual state is undetectable.
- **Compensating Controls**:
  - AWS Config can detect configuration drift for existing resources.
  - Manual change management process with documentation.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Define the EC2 instance, MySQL (RDS) database, security groups, and networking as CloudFormation or Terraform. Require pull request review for IaC changes. Enable AWS Config for drift detection.
- **Evidence**: Absence of any `.tf`, `.cfn.yaml`, `cdk.json`, or other IaC files in the repository

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No CI/CD pipeline configuration found. No GitHub Actions workflows, no GitLab CI, no Jenkinsfile, no `buildspec.yml`, no CodePipeline definitions. The repository contains only `build.gradle` and `gradlew` for building the application locally. No API contract tests, no consumer-driven contract testing (Pact), no schema comparison tools.
- **Gap**: No automated pipeline to build, test, and deploy the application. API changes are not validated before deployment. Breaking changes to agent-facing APIs would not be caught before production.
- **Compensating Controls**:
  - Manual build and deploy process with testing.
  - Agent tool definitions can include response validation.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a CI/CD pipeline (GitHub Actions or AWS CodePipeline) that builds the application, runs tests, validates API contracts (OpenAPI spec diff), and deploys with approval gates.
- **Evidence**: Absence of `.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`, `buildspec.yml` in the repository; `build.gradle` (build tool exists but no pipeline config)

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No deployment configuration of any kind. No blue/green deployment, no CodeDeploy, no Helm charts, no feature flags, no canary deployment. The `bootJar` task in `build.gradle` creates an executable JAR with `launchScript()`, suggesting manual deployment to EC2 by copying the JAR. No rollback mechanism.
- **Gap**: If a deployment breaks agent-facing APIs, there is no automated way to roll back to the previous version. Recovery depends on manual intervention — finding the previous JAR, stopping the application, copying, and restarting.
- **Compensating Controls**:
  - Keep previous JAR versions on the EC2 instance for manual rollback.
  - Agent orchestration layer can detect failures and circuit-break until recovery.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement CodeDeploy with automatic rollback triggers, or containerize the application and use ECS/EKS with rolling deployment and automatic rollback.
- **Evidence**: `build.gradle` (bootJar with launchScript — manual deployment pattern), absence of any deployment configuration

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No test files exist in the repository. No `src/test/` directory with test classes. No API test suites (Postman collections, REST Assured tests). `build.gradle` includes `spring-boot-starter-test` as a test dependency but no tests are written. Zero API test coverage.
- **Gap**: No automated verification that API behavior is correct. Any code change could silently break agent-facing endpoints without detection.
- **Compensating Controls**:
  - Manual testing before deployment.
  - Agent tool validation can catch response format changes.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Write integration tests for all API endpoints using Spring Boot Test with MockMvc or REST Assured. Add tests to a CI pipeline. Prioritize testing the endpoints agents will consume: `GET /unicorns`, `GET /unicorns/basket/{userUuid}`.
- **Evidence**: `build.gradle` (spring-boot-starter-test dependency present), absence of `src/test/` directory or any test files

#### ENG-Q5: Encryption at Rest — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No encryption at rest configuration. No KMS key references. No IaC exists to verify RDS/EBS encryption settings. The MySQL connection string in `application.properties` has no `useSSL` or `requireSSL` parameter, suggesting database connections may not use TLS. No evidence of encrypted EBS volumes for the EC2 instance.
- **Gap**: Data at rest (MySQL database, EC2 EBS volumes) may be unencrypted. PII in the `unicorn_user` table (email, names) stored without encryption at rest means a breach exposes everything.
- **Compensating Controls**:
  - AWS default encryption may be enabled at the account level for new EBS volumes and RDS instances.
  - Verify encryption status directly in AWS Console.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Enable encryption at rest on the MySQL database (if using RDS, enable encryption; if using EC2-hosted MySQL, encrypt the EBS volume). Add `useSSL=true&requireSSL=true` to the JDBC URL. Use customer-managed KMS keys for encryption.
- **Evidence**: `src/main/resources/application.properties` (JDBC URL without SSL params), absence of IaC with encryption configuration

---

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO
- **Finding**: The application exposes REST endpoints via Spring `@RestController` and `@Controller` annotations: `GET /unicorns`, `POST /unicorns/basket`, `DELETE /unicorns/basket`, `GET /unicorns/basket/{userUuid}`, `POST /user`, `POST /user/login`, `GET /data`, `GET /health/ping`, `GET /health/ishealthy`, `GET /health/dbping`. These are functional REST endpoints — integration does not require direct database access, file-based exchange, or UI automation.
- **Implication**: The API surface exists and can serve as the integration layer for agent tools. However, the endpoints are not formally documented (see API-Q2) and the current endpoints do not include the order/return data the agent needs.
- **Recommendation**: The existing REST endpoints satisfy the minimum requirement for API-based integration. Focus on API-Q2 (machine-readable spec) and building new endpoints for order/return data.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/UnicornController.java`, `src/main/java/com/monoToMicro/rest/controller/BasketController.java`, `src/main/java/com/monoToMicro/rest/controller/UserController.java`, `src/main/java/com/monoToMicro/rest/controller/HealthController.java`, `src/main/java/com/monoToMicro/rest/controller/DataReplicationController.java`

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Write operations exist but are not the focus for a read-only agent. Basket add uses `INSERT IGNORE` (MyBatis `UnicornMapper.xml`) which provides partial idempotency — duplicate inserts are silently ignored due to the UNIQUE constraint on `(uuid, unicornUuid)`. User creation also uses `INSERT IGNORE`. However, there is no explicit idempotency key support, no idempotency middleware, and no idempotency header processing.
- **Implication**: If agent scope is expanded to write-enabled in the future, idempotency must be addressed. The `INSERT IGNORE` pattern provides basic deduplication for basket operations but is not a robust idempotency solution (it ignores errors silently rather than returning the existing resource).
- **Recommendation**: Before expanding to write-enabled scope, implement proper idempotency keys for write endpoints. Consider returning 200 (with existing resource) instead of silently ignoring duplicates.
- **Evidence**: `src/main/resources/com/monoToMicro/core/repository/mappers/UnicornMapper.xml` (INSERT IGNORE), `src/main/resources/com/monoToMicro/core/repository/mappers/UserMapper.xml` (insert ignore)

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: API responses are structured JSON. The application uses Jackson serialization with `@JsonInclude(JsonInclude.Include.NON_NULL)` on model classes (`Unicorn.java`, `User.java`) and `@JsonSerialize(include = JsonSerialize.Inclusion.NON_NULL)` on `CoreModel.java`. Spring Boot defaults to `application/json` content type. No XML, no binary, no Protobuf.
- **Implication**: JSON responses are directly consumable by LLMs and agent frameworks. No additional parsing or format conversion is needed.
- **Recommendation**: No action needed. JSON is the ideal format for agent consumption.
- **Evidence**: `src/main/java/com/monoToMicro/core/model/Unicorn.java` (@JsonInclude), `src/main/java/com/monoToMicro/core/model/User.java` (@JsonInclude), `src/main/java/com/monoToMicro/core/model/CoreModel.java` (@JsonSerialize)

### API-Q7: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: No external event emission capability. No SNS, EventBridge, SQS, Kafka, or webhook endpoints. The codebase contains internal event classes (`ReadEvent`, `WriteEvent`, `CreateEvent`, etc. in `com.monoToMicro.core.events` package), but these are in-process DTOs used for internal service-to-repository communication — not external event emission. No event publishing infrastructure.
- **Implication**: The system cannot notify agents of state changes proactively. Agents must poll for changes (e.g., periodically call `GET /unicorns/basket/{userUuid}` to check basket state). This is acceptable for initial request-driven agent patterns but limits future event-driven agent architectures.
- **Recommendation**: As part of the microservices decomposition, consider adding event emission (SNS/EventBridge) for state changes (basket modified, user created). This enables proactive agent workflows without polling.
- **Evidence**: `src/main/java/com/monoToMicro/core/events/` (17 event classes — all in-process DTOs), absence of SNS/SQS/EventBridge/Kafka configuration

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limiting exists at any layer (also captured in STATE-Q5 as RISK-SAFETY). No API Gateway throttle settings, no WAF rate rules, no application-level rate limiting middleware. No `X-RateLimit-Remaining` or `Retry-After` headers in response code. No rate limit documentation.
- **Implication**: Agents cannot self-throttle because there is no rate limit information available. When rate limiting is implemented (per STATE-Q5 recommendation), rate limit headers should be included in responses so agents can adjust their calling patterns.
- **Recommendation**: When implementing rate limiting (STATE-Q5), also add `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `Retry-After` headers to API responses.
- **Evidence**: Absence of rate limiting configuration or headers in any source file

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No transaction limits, no configurable limits per agent identity, no maximum records per operation, no maximum spend per session. The `GET /unicorns` endpoint returns all records with no limit. The `GET /data` (replicate) endpoint retrieves all baskets with no limit.
- **Implication**: Read-only agents cannot cause data modification damage, but unbounded reads could still stress the database. If agent scope expands to write-enabled, transaction limits become critical to prevent an agent from modifying or deleting excessive records.
- **Recommendation**: Before expanding to write-enabled scope, implement configurable transaction limits for write operations (e.g., max basket items per operation, max users created per hour).
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/UnicornController.java` (no result limits), `src/main/java/com/monoToMicro/rest/controller/DataReplicationController.java` (getAllBaskets unbounded)

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality monitoring. No data quality dashboards, no data profiling reports, no null rate monitoring, no duplicate detection beyond UNIQUE constraints on `uuid` and `email` fields. The `unicorn_user` table has `UNIQUE(email)` and the `unicorns` table has `UNIQUE(uuid)`, providing basic deduplication. No data freshness SLAs.
- **Implication**: Agents acting on incomplete or stale data propagate errors faster than human workflows. The seed data in `create_tables.sql` suggests a controlled dataset, but there is no monitoring for data quality in production.
- **Recommendation**: Add basic data quality checks — null rate monitoring on required fields, duplicate detection, and data freshness tracking.
- **Evidence**: `database/create_tables.sql` (UNIQUE constraints provide basic dedup), absence of data quality monitoring configuration

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Field names are generally human-readable and semantically meaningful. Database columns: `uuid`, `name`, `description`, `price`, `image`, `email`, `first_name`, `last_name`, `creation_date`, `last_modified_date`, `created_by_user_id`, `unicornUuid`. Java model fields: `uuid`, `name`, `description`, `price`, `image`, `email`, `firstName`, `lastName`. No legacy codes, no cryptic abbreviations. Database uses snake_case, Java uses camelCase — standard convention.
- **Implication**: LLMs can reason about these field names without a data dictionary. `firstName` is self-explanatory; no lookup table needed. This accelerates agent tool definition.
- **Recommendation**: Maintain this naming convention in new APIs and decomposed services.
- **Evidence**: `database/create_tables.sql` (clear column names), `src/main/java/com/monoToMicro/core/model/Unicorn.java`, `src/main/java/com/monoToMicro/core/model/User.java`

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No data catalog or metadata layer. No AWS Glue Data Catalog, no Collibra, Alation, or DataHub. No metadata files or data dictionaries. The only schema documentation is the `database/create_tables.sql` file and the MyBatis mapper XMLs.
- **Implication**: Building agent tools requires reading source code and database schema to understand what data exists. No automated discovery mechanism.
- **Recommendation**: As part of modernization, register the database schema in AWS Glue Data Catalog. Document entity relationships and business semantics in a data dictionary.
- **Evidence**: `database/create_tables.sql` (schema definition is the only metadata), `src/main/resources/com/monoToMicro/core/repository/mappers/UnicornMapper.xml`, `src/main/resources/com/monoToMicro/core/repository/mappers/UserMapper.xml`

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No custom business metrics. No CloudWatch `put_metric_data` calls. No business KPI dashboards. No business event tracking (orders placed, baskets abandoned, users registered). Spring Boot Actuator provides basic JVM/HTTP metrics (memory, CPU, request count) but no business-level metrics.
- **Implication**: When agents consume the system, business metrics are the primary signal for whether agent interactions produce good outcomes. Without them, you cannot measure agent effectiveness (e.g., "did the agent increase basket completion rates?").
- **Recommendation**: Add custom CloudWatch metrics for business events: basket additions per hour, user registrations per hour, basket abandonment rate. These become the KPIs for measuring agent impact.
- **Evidence**: `build.gradle` (spring-boot-starter-actuator present), absence of custom metric publishing in any source file

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: The application exposes REST endpoints via Spring `@RestController` and `@Controller` annotations: `GET /unicorns`, `POST /unicorns/basket`, `DELETE /unicorns/basket`, `GET /unicorns/basket/{userUuid}`, `POST /user`, `POST /user/login`, `GET /data`, `GET /health/ping`, `GET /health/ishealthy`, `GET /health/dbping`. Integration does not require direct database access, file-based exchange, or UI automation.
- **Gap**: Endpoints exist but are not formally documented. No API documentation beyond source code comments.
- **Recommendation**: Focus on API-Q2 (machine-readable spec generation) to formalize the existing API surface.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/UnicornController.java`, `BasketController.java`, `UserController.java`, `HealthController.java`, `DataReplicationController.java`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, Swagger, AsyncAPI, GraphQL schema, or Smithy specification files. No auto-generation annotations (springdoc-openapi, springfox) in build.gradle.
- **Gap**: Agent frameworks cannot auto-generate tool definitions. Manual tool authoring required.
- **Recommendation**: Add `springdoc-openapi-ui` dependency to auto-generate OpenAPI 3.0 spec.
- **Evidence**: `build.gradle` (no openapi dependency), absence of spec files

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: Controllers return bare HTTP status codes with no error body. `DataReplicationController.replicate()` returns `null` on failure.
- **Gap**: Agents cannot distinguish error types or retryability.
- **Recommendation**: Implement `@ControllerAdvice` with structured JSON error responses.
- **Evidence**: `BasketController.java`, `DataReplicationController.java`, `UnicornController.java`, `UserController.java`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Write operations use `INSERT IGNORE` providing partial idempotency. No explicit idempotency key support.
- **Gap**: Not a current concern for read-only scope.
- **Recommendation**: Implement proper idempotency keys before expanding to write-enabled scope.
- **Evidence**: `UnicornMapper.xml` (INSERT IGNORE), `UserMapper.xml` (insert ignore)

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: Structured JSON responses via Jackson serialization. `@JsonInclude(NON_NULL)` on model classes. Spring Boot defaults to application/json.
- **Gap**: None — JSON is ideal for agent consumption.
- **Recommendation**: No action needed.
- **Evidence**: `Unicorn.java`, `User.java`, `CoreModel.java` (Jackson annotations)

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has operations >30s OR long-running workflows. This is a simple CRUD app with synchronous MySQL queries. No evidence of long-running operations.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: No external event emission. Internal event classes (`ReadEvent`, `WriteEvent`, etc.) are in-process DTOs, not external event publishers. No SNS/EventBridge/SQS/Kafka.
- **Gap**: System cannot proactively notify agents of state changes.
- **Recommendation**: Add event emission (SNS/EventBridge) as part of microservices decomposition.
- **Evidence**: `src/main/java/com/monoToMicro/core/events/` (17 in-process DTO classes)

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limiting at any layer. No rate limit headers. No rate limit documentation.
- **Gap**: Agents cannot self-throttle.
- **Recommendation**: Include rate limit headers when implementing STATE-Q5 rate limiting.
- **Evidence**: Absence of rate limiting configuration in repository

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: Spring Security OAuth2 is configured (`@EnableResourceServer`) but `authorizeRequests().anyRequest().permitAll()` disables all authentication. All endpoints use `@PreAuthorize("permitAll()")`. No service account, API key, mTLS, or Cognito configuration.
- **Gap**: No effective authentication. Any caller can access any endpoint without credentials.
- **Recommendation**: Implement OAuth2 client credentials flow or API Gateway with API key authentication.
- **Evidence**: `ResourceServerConfig.java` (permitAll), all controller files

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: No authorization model. All endpoints open via `permitAll()`. No IAM policies, roles, or scoped permissions.
- **Gap**: Cannot grant agent read-only access without also granting write access.
- **Recommendation**: Implement RBAC with agent-specific roles. Deploy API Gateway with resource-level policies.
- **Evidence**: `ResourceServerConfig.java`, all controller files

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization. `@PreAuthorize("permitAll()")` on every endpoint. No canRead/canWrite/canDelete checks.
- **Gap**: Cannot enforce action-level restrictions within a resource type.
- **Recommendation**: Replace permitAll with method-level security expressions.
- **Evidence**: `BasketController.java` (POST/DELETE/GET all permitAll), `UserController.java`, `UnicornController.java`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: RISK-QUALITY
- **Finding**: No identity propagation. No JWT parsing, no token exchange, no user context headers. Login is a simple email lookup, not an OAuth flow.
- **Gap**: Cannot distinguish agent-as-self vs agent-on-behalf-of-user.
- **Recommendation**: Implement JWT-based identity propagation using the existing OAuth2 resource server framework.
- **Evidence**: `ResourceServerConfig.java`, `UserController.java`

#### AUTH-Q5: Credential Management
- **Severity**: RISK-QUALITY
- **Finding**: Database credentials hardcoded in plaintext: `spring.datasource.username: MonoToMicroUser`, `spring.datasource.password: MonoToMicroPassword`. DB endpoint uses env var but credentials are in source control.
- **Gap**: Credentials compromised if repository is accessed. No rotation capability.
- **Recommendation**: Move to AWS Secrets Manager. Rotate current credentials immediately.
- **Evidence**: `src/main/resources/application.properties`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No audit logging. Uses `System.out.println()` and `e.printStackTrace()`. No CloudTrail, no structured logging, no immutable log storage.
- **Gap**: No audit trail for any operation. Cannot prove compliance or conduct forensics.
- **Recommendation**: Implement SLF4J/Logback structured logging. Add request-level audit logging with caller identity.
- **Evidence**: `HealthController.java` (System.out.println), `UnicornRepositoryImpl.java` (e.printStackTrace), `UserRepositoryImpl.java` (e.printStackTrace)

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: No identity mechanism exists (per AUTH-Q1), so no suspension mechanism. No API key revocation, no IAM role deactivation.
- **Gap**: Cannot isolate misbehaving agent without blocking all traffic.
- **Recommendation**: Choose auth mechanism (AUTH-Q1) that supports individual credential revocation.
- **Evidence**: `ResourceServerConfig.java`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No saga pattern, no two-phase commit, no undo endpoints. `@Transactional` provides single-operation atomicity only.
- **Gap**: No multi-step compensation. Partial state on failure.
- **Recommendation**: Implement compensation logic before expanding to write-enabled scope.
- **Evidence**: `UnicornRepositoryImpl.java` (@Transactional), `UserRepositoryImpl.java` (@Transactional)

#### STATE-Q2: Queryable Current State
- **Severity**: RISK-QUALITY
- **Finding**: Partial queryable state. GET endpoints for unicorns and basket exist. No order/return state (needed by agent per context).
- **Gap**: Agent needs order/return data but no endpoints exist for these entities.
- **Recommendation**: Build order/return APIs as part of decomposition.
- **Evidence**: `UnicornController.java`, `BasketController.java`, `HealthController.java`

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled AND service has persistent state. Current scope is read-only — trigger condition not met.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: No circuit breakers, retry logic, or timeout configurations. EC2MetadataUtils call in HealthController has no timeout. MySQL connections have no explicit timeout. No Resilience4j or Hystrix.
- **Gap**: Hung dependencies cascade failures to agents.
- **Recommendation**: Add connection timeouts and circuit breakers. Quick win: add Hikari connection pool timeouts.
- **Evidence**: `application.properties` (no timeouts), `HealthController.java` (unprotected EC2MetadataUtils call), `build.gradle` (no resilience library)

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No rate limiting at any layer. Application runs directly on EC2 port 8080 with no traffic management.
- **Gap**: Unlimited request rate from any caller. Runaway agent can DDoS the service.
- **Recommendation**: Deploy API Gateway with rate limiting and usage plans.
- **Evidence**: `application.properties`, `build.gradle`, absence of API Gateway/WAF configuration

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No transaction limits. Unbounded reads possible.
- **Gap**: Not a concern for read-only scope.
- **Recommendation**: Implement transaction limits before expanding to write-enabled scope.
- **Evidence**: `UnicornController.java` (no result limits), `DataReplicationController.java` (unbounded getAllBaskets)

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: RISK-QUALITY
- **Finding**: Single EC2 instance. No auto-scaling, no load tests, no capacity planning. P0 priority triggered this extended question.
- **Gap**: Cannot handle unpredictable agent traffic patterns.
- **Recommendation**: Containerize and deploy with auto-scaling. In interim, add ASG with minimum 2 instances.
- **Evidence**: `HealthController.java` (EC2MetadataUtils single-instance), `application.properties` (server.port: 8080)

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled. Current scope is read-only.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled. Current scope is read-only.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: No separate environments. Single `application.properties` with no profiles. No docker-compose. No staging IaC.
- **Gap**: No safe environment for testing agent behavior.
- **Recommendation**: Create Spring profiles and docker-compose for local testing. Deploy staging environment.
- **Evidence**: `application.properties` (single config), `database/create_tables.sql` (minimal seed data)

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: `unicorn_user` table stores PII (email, first_name, last_name). No classification tags, no field-level encryption, no access controls. User model exposes all PII in API responses.
- **Gap**: Unclassified PII exposed to any caller without restriction.
- **Recommendation**: Classify PII fields. Implement field-level response filtering for agent callers.
- **Evidence**: `database/create_tables.sql` (PII columns), `User.java` (exposes PII), `UserMapper.xml` (SELECT returns PII)

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No data residency documentation. MySQL endpoint via env var with no region enforcement. No GDPR/LGPD references.
- **Gap**: No mechanism to prevent agent from transmitting PII to LLM in different region.
- **Recommendation**: Conduct data residency analysis. Document regulatory requirements. Configure region-locked deployments.
- **Evidence**: `application.properties` (MySQL endpoint via env var), `database/create_tables.sql` (PII in unicorn_user)

#### DATA-Q3: Selective Query Support
- **Severity**: RISK-QUALITY
- **Finding**: `SELECT * FROM unicorns` returns all records — no pagination, filtering, or sorting. `getAllBaskets` similarly unbounded. `getUnicornBasket` filters by userUuid (bounded).
- **Gap**: Unbounded result sets will exhaust LLM context windows as data grows.
- **Recommendation**: Add pagination (limit/offset or cursor) to GET /unicorns. Add LIMIT to SQL queries.
- **Evidence**: `UnicornMapper.xml` (SELECT * no LIMIT), `UnicornController.java` (no pagination params)

#### DATA-Q4: System of Record Designations
- **Severity**: RISK-QUALITY
- **Finding**: No SoR designations. No data ownership definitions. Monolith is de facto SoR for all entities.
- **Gap**: Conflicting data across decomposed services without golden record authority.
- **Recommendation**: Document SoR designations as part of decomposition planning.
- **Evidence**: `database/create_tables.sql`

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK-QUALITY
- **Finding**: Database has `creation_date` and `last_modified_date`. UTC configured in JDBC URL. However, `CoreModel.java` uses `@JsonIgnore` on both, hiding timestamps from API responses. No Cache-Control or freshness headers.
- **Gap**: Agents cannot determine data freshness.
- **Recommendation**: Remove `@JsonIgnore` from temporal fields or create agent-facing DTO that includes them.
- **Evidence**: `CoreModel.java` (@JsonIgnore), `database/create_tables.sql` (timestamp columns), `application.properties` (UTC timezone)

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: No PII redaction. `System.out.println()` and `e.printStackTrace()` used throughout. Stack traces from database operations could contain PII.
- **Gap**: PII could leak into logs via exception stack traces.
- **Recommendation**: Replace with SLF4J/Logback structured logging with PII redaction patterns.
- **Evidence**: `HealthController.java`, `UnicornRepositoryImpl.java`, `UserRepositoryImpl.java`, `HealthRepositoryImpl.java`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality monitoring. UNIQUE constraints provide basic dedup. No null rate monitoring, no freshness SLAs.
- **Gap**: No data quality visibility for agents.
- **Recommendation**: Add basic data quality checks and monitoring.
- **Evidence**: `database/create_tables.sql` (UNIQUE constraints)

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: No schema versioning. No OpenAPI definitions. No versioned URLs. No changelog. No migration tool (no Flyway/Liquibase). Single `create_tables.sql`.
- **Gap**: Agent tool bindings break silently on schema changes.
- **Recommendation**: Add Flyway for DB migrations. Implement API versioning. Add OpenAPI spec generation.
- **Evidence**: `database/create_tables.sql`, absence of versioned URLs, absence of schema files

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Clear field names: `uuid`, `name`, `description`, `price`, `email`, `firstName`, `lastName`. No legacy codes or cryptic abbreviations.
- **Gap**: None — naming is good.
- **Recommendation**: Maintain this convention in new APIs.
- **Evidence**: `database/create_tables.sql`, `Unicorn.java`, `User.java`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No data catalog. Only `create_tables.sql` and MyBatis mapper XMLs serve as schema documentation.
- **Gap**: No automated discovery for agent tool builders.
- **Recommendation**: Register schema in AWS Glue Data Catalog.
- **Evidence**: `database/create_tables.sql`, mapper XML files

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: No tracing (no OpenTelemetry, no X-Ray). No structured logging (System.out.println, e.printStackTrace). Spring Boot Actuator present but no tracing config. No correlation IDs.
- **Gap**: Cannot trace agent-initiated requests. Unstructured logs unsearchable.
- **Recommendation**: Add SLF4J/Logback JSON logging. Add Spring Cloud Sleuth or OpenTelemetry.
- **Evidence**: `build.gradle` (actuator present, no tracing), `HealthController.java`, absence of logback config

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: No alerting. No CloudWatch alarms, no anomaly detection, no PagerDuty/OpsGenie.
- **Gap**: Agent-caused degradation goes undetected.
- **Recommendation**: Configure CloudWatch alarms for error rate and latency.
- **Evidence**: Absence of monitoring configuration

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics. Actuator provides JVM/HTTP metrics only.
- **Gap**: Cannot measure agent effectiveness.
- **Recommendation**: Add custom CloudWatch metrics for business events.
- **Evidence**: `build.gradle` (actuator present), absence of custom metrics

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance
- **Severity**: RISK-QUALITY
- **Finding**: No IaC. Infrastructure manually managed. No drift detection, no peer review.
- **Gap**: Integration surface not defined as code.
- **Recommendation**: Define infrastructure as CloudFormation or Terraform. Enable AWS Config.
- **Evidence**: Absence of IaC files

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: No CI/CD pipeline. No GitHub Actions, GitLab CI, Jenkinsfile, or buildspec.yml. No contract tests.
- **Gap**: API changes not validated before deployment.
- **Recommendation**: Create CI/CD pipeline with API contract validation.
- **Evidence**: Absence of CI/CD configuration files; `build.gradle` exists but no pipeline

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: No deployment configuration. Manual JAR deployment to EC2 (`bootJar` with `launchScript()`). No rollback mechanism.
- **Gap**: No automated rollback if deployment breaks agent APIs.
- **Recommendation**: Implement CodeDeploy with rollback triggers, or containerize with ECS/EKS.
- **Evidence**: `build.gradle` (bootJar launchScript), absence of deployment config

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: Zero test files. No `src/test/` directory. `spring-boot-starter-test` dependency present but unused.
- **Gap**: No automated verification of API behavior.
- **Recommendation**: Write integration tests for agent-facing endpoints using Spring Boot Test.
- **Evidence**: `build.gradle` (test dependency), absence of test files

#### ENG-Q5: Encryption at Rest
- **Severity**: RISK-QUALITY
- **Finding**: No encryption configuration. No KMS references. JDBC URL lacks `useSSL`/`requireSSL`. No IaC to verify RDS/EBS encryption.
- **Gap**: PII stored potentially unencrypted at rest.
- **Recommendation**: Enable RDS encryption. Add `useSSL=true` to JDBC URL. Use KMS keys.
- **Evidence**: `application.properties` (JDBC URL without SSL), absence of IaC

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `src/main/java/com/monoToMicro/Application.java` | AUTH-Q1 |
| `src/main/java/com/monoToMicro/security/ResourceServerConfig.java` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q7 |
| `src/main/java/com/monoToMicro/rest/controller/UnicornController.java` | API-Q1, API-Q2, API-Q3, AUTH-Q2, AUTH-Q3, STATE-Q2, STATE-Q6, DATA-Q3 |
| `src/main/java/com/monoToMicro/rest/controller/BasketController.java` | API-Q1, API-Q3, AUTH-Q2, AUTH-Q3, STATE-Q2 |
| `src/main/java/com/monoToMicro/rest/controller/UserController.java` | API-Q1, API-Q3, AUTH-Q2, AUTH-Q3, AUTH-Q4 |
| `src/main/java/com/monoToMicro/rest/controller/HealthController.java` | API-Q1, AUTH-Q6, STATE-Q2, STATE-Q4, STATE-Q7, DATA-Q6, OBS-Q1 |
| `src/main/java/com/monoToMicro/rest/controller/DataReplicationController.java` | API-Q1, API-Q3, STATE-Q6 |
| `src/main/java/com/monoToMicro/rest/controller/CoreController.java` | API-Q1 |
| `src/main/java/com/monoToMicro/core/model/CoreModel.java` | API-Q5, DATA-Q5 |
| `src/main/java/com/monoToMicro/core/model/Unicorn.java` | API-Q5, DISC-Q2 |
| `src/main/java/com/monoToMicro/core/model/User.java` | API-Q5, DATA-Q1, DISC-Q2 |
| `src/main/java/com/monoToMicro/core/model/UnicornBasket.java` | API-Q5 |
| `src/main/java/com/monoToMicro/core/repository/UnicornRepositoryImpl.java` | AUTH-Q6, STATE-Q1, DATA-Q6 |
| `src/main/java/com/monoToMicro/core/repository/UserRepositoryImpl.java` | AUTH-Q6, STATE-Q1, DATA-Q6 |
| `src/main/java/com/monoToMicro/core/repository/HealthRepositoryImpl.java` | AUTH-Q6, DATA-Q6 |
| `src/main/java/com/monoToMicro/core/services/UnicornServiceImpl.java` | STATE-Q1 |
| `src/main/java/com/monoToMicro/core/services/UserServiceImpl.java` | STATE-Q1 |
| `src/main/java/com/monoToMicro/core/events/` (17 event classes) | API-Q7 |
| `src/main/java/com/monoToMicro/config/CoreConfig.java` | AUTH-Q1 |
| `src/main/java/com/monoToMicro/config/MyBatisConfig.java` | STATE-Q4 |
| `src/main/java/com/monoToMicro/config/MVCConfig.java` | API-Q1 |

### Database Schema
| File | Questions Referenced |
|------|---------------------|
| `database/create_tables.sql` | DATA-Q1, DATA-Q2, DATA-Q3, DATA-Q4, DATA-Q5, DATA-Q7, DISC-Q1, DISC-Q2, DISC-Q3, HITL-Q3, ENG-Q5 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `src/main/resources/application.properties` | AUTH-Q5, AUTH-Q6, STATE-Q4, STATE-Q5, STATE-Q7, DATA-Q2, DATA-Q5, HITL-Q3, ENG-Q5, OBS-Q1 |

### MyBatis Mapper XMLs
| File | Questions Referenced |
|------|---------------------|
| `src/main/resources/com/monoToMicro/core/repository/mappers/UnicornMapper.xml` | API-Q4, DATA-Q3, DISC-Q3 |
| `src/main/resources/com/monoToMicro/core/repository/mappers/UserMapper.xml` | API-Q4, DATA-Q1, DISC-Q3 |
| `src/main/resources/com/monoToMicro/core/repository/mappers/HealthMapper.xml` | STATE-Q4 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `build.gradle` | AUTH-Q1, STATE-Q4, STATE-Q5, API-Q2, OBS-Q1, OBS-Q2, OBS-Q3, ENG-Q2, ENG-Q3, ENG-Q4 |

### Notable Absences (No Files Found)
| Category | Impact on Analysis |
|----------|---------------------|
| No IaC files (Terraform, CloudFormation, CDK) | ENG-Q1 (RISK-QUALITY), AUTH-Q6 (no CloudTrail config), ENG-Q5 (cannot verify encryption) |
| No CI/CD configuration | ENG-Q2 (RISK-QUALITY), ENG-Q3 (RISK-QUALITY) |
| No API specification files (OpenAPI/Swagger) | API-Q2 (RISK-QUALITY), DISC-Q1 (RISK-QUALITY) |
| No test files | ENG-Q4 (RISK-QUALITY) |
| No Dockerfile or docker-compose | HITL-Q3 (RISK-QUALITY) |
| No monitoring/alerting configuration | OBS-Q2 (RISK-QUALITY) |
| No logback.xml or logging configuration | OBS-Q1 (RISK-QUALITY), AUTH-Q6 (RISK-SAFETY), DATA-Q6 (RISK-SAFETY) |
