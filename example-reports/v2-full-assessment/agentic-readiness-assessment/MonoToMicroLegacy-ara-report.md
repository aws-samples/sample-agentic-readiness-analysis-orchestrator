# Agentic Readiness Assessment Report

**Target**: MonoToMicroLegacy
**Date**: 2026-04-15
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Agent Scope**: write-enabled
**Priority**: P0
**Tags**: monolith, java, ec2, decomposition-target
**Context**: Legacy Java Spring Boot monolith on EC2 with MySQL — primary decomposition target. The agent needs access to order and return data through discrete service APIs.

---

## Readiness Profile: Not Agent-Integrable

**BLOCKERs**: 7 | **RISKs**: 32 | **INFOs**: 10

Exclude from agent toolset or plan major remediation before re-evaluation. With 7 unresolved BLOCKERs spanning authentication, data safety, write-operation integrity, and network security, this system cannot safely support autonomous agent integration — including scoped pilots. A phased remediation plan targeting identity, data classification, and network hardening is required before re-assessment.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 7 |
| RISK | 32 |
| INFO | 10 |
| N/A | 0 |
| **Total** | **49** |

**Questions Evaluated**: 49
**Questions N/A (repo_type: application)**: 0

---

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: The application has Spring Security OAuth2 configured (`ResourceServerConfig.java` with `@EnableResourceServer`) but `authorizeRequests().anyRequest().permitAll()` — effectively disabling all authentication. No machine identity authentication is enforced. No client credentials flow, no API key authentication, no mTLS. Every endpoint uses `@PreAuthorize("permitAll()")`. The OAuth2 resource server is present in dependencies (`spring-security-oauth2-autoconfigure`, `spring-cloud-starter-oauth2`, `spring-security-jwt`) but the security configuration permits all requests without requiring any credential.
- **Gap**: No authentication mechanism is enforced. Any caller — human, agent, or attacker — can invoke any endpoint without presenting credentials. There is no way to identify which agent made a call.
- **Remediation**:
  - **Immediate**: Enable OAuth2 resource server validation in `ResourceServerConfig.java` — replace `permitAll()` with `.authenticated()` and configure a JWT issuer (Amazon Cognito or external IdP). Create a Cognito User Pool with an app client using client_credentials grant for machine identity.
  - **Target State**: All API endpoints require a valid OAuth2 bearer token. Agent identities are registered as Cognito app clients with unique client IDs. Audit logs attribute every request to a specific principal.
  - **Estimated Effort**: Medium (2–4 weeks)
  - **Dependencies**: AUTH-Q7 (audit logging requires authenticated principals to log), AUTH-Q2 (scoped permissions require identity to bind to)
- **Evidence**: `src/main/java/com/monoToMicro/security/ResourceServerConfig.java`, `build.gradle`, `src/main/java/com/monoToMicro/rest/controller/UnicornController.java` (all controllers use `@PreAuthorize("permitAll()")`)

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: BLOCKER
- **Conditional**: agent_scope is "write-enabled" — evaluated as BLOCKER
- **Finding**: Write endpoints (`POST /unicorns/basket`, `DELETE /unicorns/basket`, `POST /user`) have no idempotency key support. The basket `INSERT IGNORE` in `UnicornMapper.xml` provides partial duplicate protection via the UNIQUE constraint on `(uuid, unicornUuid)`, but this is a database-level constraint — not an application-level idempotency contract. The user creation endpoint (`POST /user`) generates a random UUID server-side (`UUID.randomUUID().toString()` in `UserServiceImpl.java`) with no client-provided idempotency key — retrying the same POST creates a new user record each time (protected only by the email UNIQUE constraint, which returns a silent `INSERT IGNORE` rather than an idempotency response). No idempotency middleware or decorators exist.
- **Gap**: No client-facing idempotency key support on any write endpoint. Agent retries on `POST /user` with identical payloads will silently succeed via `INSERT IGNORE` but return inconsistent UUIDs. No `Idempotency-Key` header support.
- **Remediation**:
  - **Immediate**: Add an `Idempotency-Key` header to all write endpoints. Implement idempotency middleware that stores the key-to-response mapping (e.g., in a DynamoDB table or MySQL table) and returns the cached response on duplicate requests.
  - **Target State**: All write endpoints accept a client-provided `Idempotency-Key` header. Duplicate requests with the same key return the original response without side effects. `POST /user` returns the existing user record if the idempotency key matches a previous creation.
  - **Estimated Effort**: Medium (2–3 weeks)
  - **Dependencies**: None
- **Evidence**: `src/main/resources/com/monoToMicro/core/repository/mappers/UnicornMapper.xml` (INSERT IGNORE), `src/main/java/com/monoToMicro/core/services/UserServiceImpl.java` (UUID.randomUUID()), `src/main/java/com/monoToMicro/rest/controller/BasketController.java`

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: BLOCKER
- **Conditional**: agent_scope is "write-enabled" — evaluated as BLOCKER
- **Finding**: No compensation or rollback logic for multi-step operations. The basket add/remove operations are single SQL statements (`INSERT IGNORE` / `DELETE`), and the repository layer uses `@Transactional` annotations but only for individual operations — no cross-operation transaction coordination. There is no saga pattern, no compensating transactions, no explicit undo endpoints, no Step Functions with rollback states. If an agent performs a multi-step workflow (e.g., create user → add items to basket → process order), a failure mid-sequence leaves the system in a partial state with no automated recovery.
- **Gap**: No compensation or rollback mechanism exists for multi-step agent workflows. The application has no concept of workflow-level transactions.
- **Remediation**:
  - **Immediate**: Implement explicit undo/compensation endpoints for write operations (e.g., `DELETE /user/{uuid}` to compensate a failed workflow after user creation). For the basket, the existing `DELETE /unicorns/basket` serves as a manual compensation endpoint.
  - **Target State**: All multi-step write workflows have compensating actions defined. Consider implementing AWS Step Functions with error handling and compensation states for complex agent workflows that span multiple API calls.
  - **Estimated Effort**: High (4–8 weeks)
  - **Dependencies**: API-Q4 (idempotency is a prerequisite for safe compensation — you must be able to retry compensation actions)
- **Evidence**: `src/main/java/com/monoToMicro/core/repository/UnicornRepositoryImpl.java` (@Transactional on individual ops), `src/main/java/com/monoToMicro/core/services/UnicornServiceImpl.java`, `src/main/resources/com/monoToMicro/core/repository/mappers/UnicornMapper.xml`

### AUTH-Q7: Immutable Audit Logging ⚡

- **Severity**: BLOCKER
- **Conditional**: agent_scope is "write-enabled" — evaluated as BLOCKER
- **Finding**: No audit logging is configured in the application. The CloudFormation template defines CloudWatch Logs (`InstanceLogGroup` with 7-day retention) for application stdout (`app.log`), but this captures only `System.out.println()` output and `e.printStackTrace()` stack traces — not structured audit records of authenticated principals performing write operations. There is no CloudTrail configuration in the CloudFormation stack for application-level audit. Logs are not immutable — no S3 object lock, no CloudTrail log file validation, no tamper-evident storage. Since authentication is disabled (AUTH-Q1), there is no principal to log even if audit logging were implemented.
- **Gap**: No structured audit trail of who performed what write operation and when. Logs are unstructured, mutable, and retain for only 7 days. No immutable storage. No principal attribution.
- **Remediation**:
  - **Immediate**: Implement structured audit logging (JSON format) for all write operations, including the authenticated principal, action performed, resource affected, and timestamp. Ship logs to CloudWatch Logs with extended retention (minimum 90 days for compliance). Enable CloudTrail for API-level audit.
  - **Target State**: Every write operation logs the authenticated principal (agent identity or user identity), the action performed, the resource affected, the request payload hash, and a UTC timestamp. Logs are shipped to S3 with object lock (WORM) for immutability. CloudTrail log file validation is enabled.
  - **Estimated Effort**: Medium (2–4 weeks)
  - **Dependencies**: AUTH-Q1 (must have authenticated principals before audit logging is meaningful)
- **Evidence**: `../MonoToMicroAssets/MonoToMicroCF.yaml` (InstanceLogGroup with 7-day retention, no CloudTrail), `src/main/java/com/monoToMicro/rest/controller/BasketController.java` (no logging on write operations)

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: No sensitive data classification exists. The `unicorn_user` table contains PII fields (`email`, `first_name`, `last_name`) stored in plaintext in MySQL with no field-level classification, no field-level encryption, and no column-level access controls. No Amazon Macie integration for automated PII detection. No data classification tags on any resources in the CloudFormation template (RDS cluster, S3 buckets, EC2 instances have no classification tags). The `User.java` model exposes all PII fields directly in API responses via Jackson serialization with no redaction or filtering.
- **Gap**: PII is stored, transmitted, and exposed via API without classification, encryption, or access controls. An agent with read access to the `/user/login` endpoint receives full PII (email, first_name, last_name) in the response body.
- **Remediation**:
  - **Immediate**: Classify all data fields in the `unicorn_user` table. Tag PII fields (email, first_name, last_name) at the database level and in API response documentation. Enable Amazon Macie on the S3 buckets. Add classification tags to CloudFormation resources.
  - **Target State**: All PII fields are classified, tagged, and subject to field-level access controls. API responses support field-level filtering based on the caller's authorization scope. RDS encryption at rest is enabled. Macie monitors S3 buckets for PII exposure.
  - **Estimated Effort**: Medium (3–4 weeks)
  - **Dependencies**: AUTH-Q1 (field-level access controls require authenticated identity to enforce), ENG-Q5 (encryption at rest)
- **Evidence**: `database/create_tables.sql` (unicorn_user table with PII columns), `src/main/java/com/monoToMicro/core/model/User.java` (PII fields exposed), `../MonoToMicroAssets/MonoToMicroCF.yaml` (no classification tags)

### DATA-Q2: Data Residency and Sovereignty ⚡

- **Severity**: BLOCKER
- **Conditional**: agent_scope is "write-enabled" — evaluated as BLOCKER
- **Finding**: No data residency or sovereignty controls are documented or enforced. The CloudFormation template deploys to a single AWS region (parameterized, no region restriction) but does not enforce data residency constraints. No GDPR, LGPD, or sector-specific compliance references exist in the codebase. No cross-region replication safeguards. User PII (email, first_name, last_name) stored in the MySQL database could be sent to an LLM endpoint in any jurisdiction by an agent without controls. The DMS replication configuration copies data between MySQL instances but has no region-restriction controls.
- **Gap**: No data residency policy, no sovereignty controls, no documentation of applicable regulatory requirements. A write-enabled agent could transmit user PII to an LLM provider in a different region/jurisdiction without any guardrails.
- **Remediation**:
  - **Immediate**: Document the applicable data residency requirements for this application's user data. Define which regions and services are approved for data processing. Implement an API-level data residency filter that prevents PII from being returned to callers outside the approved region.
  - **Target State**: Data residency requirements are documented and enforced at the infrastructure level (S3 bucket policies with region restrictions, RDS in approved regions only). Agent configurations specify approved LLM endpoints in the same jurisdiction. PII fields are masked or excluded from agent responses unless the agent's identity has explicit PII access authorization.
  - **Estimated Effort**: Medium (2–4 weeks)
  - **Dependencies**: DATA-Q1 (data must be classified before residency controls can be scoped to sensitive fields)
- **Evidence**: `../MonoToMicroAssets/MonoToMicroCF.yaml` (no region restrictions, no data residency controls), `database/create_tables.sql` (PII in unicorn_user), `src/main/resources/application.properties`

### ENG-Q6: Cross-Origin and Network Policies

- **Severity**: BLOCKER
- **Finding**: CORS is configured permissively across multiple locations. `MVCConfig.java` allows all HTTP methods (`HEAD`, `GET`, `PUT`, `POST`, `DELETE`, `PATCH`, `OPTIONS`) on all paths (`/**`) with no origin restriction. `Application.java` also configures CORS allowing `GET`, `POST`, `OPTIONS` on all paths. The `WebSecurityConfigurerAdapter` in `Application.java` ignores all `OPTIONS` requests with an explicit comment: "workaround to get CORS working with this old version, not recommended for production usage!" Security groups in CloudFormation allow inbound 80/443 from `0.0.0.0/0` (entire internet). No WAF, no API Gateway access policies, no network policies restricting agent traffic to specific origins or CIDR ranges.
- **Gap**: Any origin can call any endpoint with any HTTP method. Network security groups allow unrestricted inbound access from the internet. No origin allowlist, no IP-based restrictions, no WAF rules.
- **Remediation**:
  - **Immediate**: Restrict CORS `allowedOrigins` in `MVCConfig.java` to specific known origins (the UI bucket domain and agent platform endpoints). Restrict security group inbound rules to known CIDR ranges. Deploy an API Gateway or ALB in front of the EC2 instance with WAF rules.
  - **Target State**: CORS is restricted to an explicit allowlist of origins. An API Gateway sits in front of the application with WAF rules enforcing IP-based restrictions, rate limiting, and request validation. Security groups restrict inbound traffic to the API Gateway only — no direct internet access to the EC2 instance. Network policies are documented and discoverable.
  - **Estimated Effort**: Medium (2–3 weeks)
  - **Dependencies**: STATE-Q5 (rate limiting should be implemented at the API Gateway level)
- **Evidence**: `src/main/java/com/monoToMicro/config/MVCConfig.java` (permissive CORS), `src/main/java/com/monoToMicro/Application.java` (CORS + OPTIONS workaround), `../MonoToMicroAssets/MonoToMicroCF.yaml` (EC2SecurityGroup inbound 0.0.0.0/0)

---

## RISKs — Proceed with Compensating Controls

### API-Q2: Machine-Readable API Specification
- **Severity**: RISK
- **Finding**: No OpenAPI, Swagger, AsyncAPI, GraphQL, or Smithy specification files exist anywhere in the repository. The API is defined solely through Spring Boot `@RestController` and `@RequestMapping` annotations in Java source code. No machine-readable spec is generated or maintained.
- **Gap**: No machine-readable API specification. Agent tool definitions must be authored manually by inspecting Java source code, creating drift risk.
- **Compensating Controls**:
  - Manually author an OpenAPI 3.0 spec from the existing controller annotations and commit it to the repository.
  - Use `springdoc-openapi` library to auto-generate an OpenAPI spec from the existing Spring annotations at build time.
- **Remediation Timeline**: 1–2 weeks
- **Recommendation**: Add `springdoc-openapi-ui` dependency to `build.gradle` and configure it to auto-generate and serve an OpenAPI 3.0 spec at `/v3/api-docs`.
- **Evidence**: `build.gradle` (no springdoc/swagger dependency), repository-wide search found no `.yaml`/`.json` API spec files

### API-Q3: Structured Error Responses
- **Severity**: RISK
- **Finding**: Error responses are bare HTTP status codes with no structured error body. All controllers return `ResponseEntity` with only `HttpStatus.BAD_REQUEST` — no error code, error message, or retryable indicator. Exceptions in repositories are caught with `e.printStackTrace()` and return `null`/`false`, which cascades to generic `BAD_REQUEST` responses. The `DataReplicationController.replicate()` method returns `null` on failure instead of a proper error response.
- **Gap**: Agents cannot distinguish between invalid input, server errors, or retriable failures. All failures appear as `400 Bad Request` with an empty body.
- **Compensating Controls**:
  - Implement a global `@ControllerAdvice` exception handler that returns structured JSON error responses with `errorCode`, `message`, and `retryable` fields.
  - As an interim measure, document known error conditions and expected HTTP status codes for each endpoint.
- **Remediation Timeline**: 1–2 weeks
- **Recommendation**: Create a `GlobalExceptionHandler` class with `@ControllerAdvice` that catches all exceptions and returns a standardized error JSON body.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/UnicornController.java`, `src/main/java/com/monoToMicro/rest/controller/BasketController.java`, `src/main/java/com/monoToMicro/core/repository/UnicornRepositoryImpl.java`

### API-Q5: API Versioning and Deprecation
- **Severity**: RISK
- **Finding**: No API versioning exists. Endpoints use bare paths (`/unicorns`, `/user`, `/health`). No `/v1/` URL patterns, no `Accept-Version` headers, no versioning annotations, no changelog files, no deprecation notices.
- **Gap**: Any breaking API change will silently break agent tool definitions. No versioning contract protects agents from incompatible changes.
- **Compensating Controls**:
  - Add URL path-based versioning (`/v1/unicorns`) to all endpoints before any agent integration.
  - Alternatively, add `Accept-Version` header support with a default version fallback.
- **Remediation Timeline**: 2–3 weeks
- **Recommendation**: Introduce `/v1/` prefix to all endpoints. Establish a deprecation policy that requires 90-day notice before removing API versions.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/UnicornController.java` (@RequestMapping("/unicorns")), `src/main/java/com/monoToMicro/rest/controller/UserController.java` (@RequestMapping("/user"))

### API-Q7: Asynchronous Operation Support
- **Severity**: RISK
- **Finding**: No async patterns found in the application. All operations are synchronous request/response. No background job frameworks (no Celery/Bull/SQS worker equivalent), no polling endpoints, no webhook callbacks, no Step Functions integration, no async Spring patterns (`@Async`, `DeferredResult`, `CompletableFuture`).
- **Gap**: If any operation exceeds 30 seconds (e.g., bulk basket operations, data replication), agents will hit timeout limits and potentially create orphaned processes.
- **Compensating Controls**:
  - For the current simple CRUD operations, synchronous patterns are acceptable — operations should complete in sub-second times.
  - Implement async patterns when adding longer-running operations (e.g., order processing, bulk operations).
- **Remediation Timeline**: 30–60 days (before adding complex agent workflows)
- **Recommendation**: Implement a job submission + status polling pattern for any operation that may exceed 5 seconds. Consider Spring's `@Async` or AWS Step Functions.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/BasketController.java` (synchronous only), `src/main/java/com/monoToMicro/rest/controller/DataReplicationController.java` (synchronous replication)

### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK
- **Finding**: The CloudFormation template defines an IAM role (`S3Role`/`MonoToMicroRole`) with S3 permissions scoped to specific buckets (`UIBucket`, `AssetBucket`) plus `AmazonSSMManagedInstanceCore` and `CloudWatchAgentServerPolicy` managed policies. However, the application itself has no authorization model — `@PreAuthorize("permitAll()")` on every endpoint. No role-based or resource-scoped permissions exist at the application level.
- **Gap**: At the application level, there is no permission model. Any authenticated caller (once AUTH-Q1 is fixed) inherits full access to all endpoints and all data.
- **Compensating Controls**:
  - Implement API Gateway resource policies that restrict specific agent identities to specific HTTP methods and paths.
  - Use IAM policies at the infrastructure level to scope agent access until application-level RBAC is implemented.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement Spring Security role-based access control. Define roles (e.g., `AGENT_READ`, `AGENT_WRITE`, `ADMIN`) and map them to endpoint-level `@PreAuthorize` annotations.
- **Evidence**: `src/main/java/com/monoToMicro/security/ResourceServerConfig.java` (permitAll), `../MonoToMicroAssets/MonoToMicroCF.yaml` (S3Policy scoped to buckets)

### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK
- **Finding**: No action-level authorization exists. All endpoints use `@PreAuthorize("permitAll()")`. No ABAC policies, no fine-grained RBAC, no permission checks differentiating read vs write operations. An agent that can read unicorns can also add/remove items from any user's basket and create users.
- **Gap**: No ability to grant an agent read-only access to unicorns while denying basket modifications. All actions are equally permitted.
- **Compensating Controls**:
  - At the API Gateway level, restrict HTTP methods per agent identity (allow GET, deny POST/DELETE).
  - Implement middleware that checks the caller's role before executing write operations.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement action-level authorization checks in controller methods. Use `@PreAuthorize("hasRole('WRITE')")` for write endpoints and `@PreAuthorize("hasRole('READ')")` for read endpoints.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/UnicornController.java`, `src/main/java/com/monoToMicro/rest/controller/BasketController.java`, `src/main/java/com/monoToMicro/rest/controller/UserController.java`

### AUTH-Q4: Identity Propagation
- **Severity**: RISK
- **Finding**: Spring Security OAuth2 libraries are present in dependencies (`spring-boot-starter-security`, `spring-security-oauth2-autoconfigure`, `spring-cloud-starter-oauth2`, `spring-security-jwt`). However, the configuration in `ResourceServerConfig.java` permits all requests without extracting or propagating any user identity. No JWT parsing middleware active, no token exchange, no user context headers (`X-User-Id`, `Authorization Bearer`) propagated through service calls.
- **Gap**: No identity propagation mechanism. The application cannot distinguish between requests made on behalf of different users or agents.
- **Compensating Controls**:
  - Enable JWT validation in `ResourceServerConfig.java` to extract the `sub` claim from OAuth2 tokens.
  - Pass user context as a request attribute through the Spring Security context.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure the OAuth2 resource server to validate and extract JWT claims. Use `SecurityContextHolder` to propagate user identity to service and repository layers.
- **Evidence**: `build.gradle` (OAuth2 dependencies present but unused), `src/main/java/com/monoToMicro/security/ResourceServerConfig.java` (permitAll, no JWT extraction)

### AUTH-Q5: Agent-as-Self vs Agent-on-Behalf-of-User
- **Severity**: RISK
- **Finding**: No distinction between agent-as-self and agent-on-behalf-of-user exists. The application has no identity model at all — all requests are anonymous via `permitAll`. There are no separate IAM roles or API keys for different access modes. No audit log fields distinguish the two modes.
- **Gap**: No ability to differentiate whether an agent is acting under its own service identity or on behalf of a specific human user. Both modes would be treated identically.
- **Compensating Controls**:
  - Design the Cognito integration (AUTH-Q1 remediation) with separate app clients for agent-as-self vs agent-on-behalf-of-user.
  - Include an `X-On-Behalf-Of` header convention for delegated calls.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement two OAuth2 flows: client_credentials for agent-as-self, and authorization_code with token exchange for agent-on-behalf-of-user. Log the distinction in audit records.
- **Evidence**: `src/main/java/com/monoToMicro/security/ResourceServerConfig.java`, `src/main/java/com/monoToMicro/Application.java`

### AUTH-Q6: Credential Management
- **Severity**: RISK
- **Finding**: Credentials are hardcoded in `application.properties` (`spring.datasource.username: MonoToMicroUser`, `spring.datasource.password: MonoToMicroPassword`). The DB endpoint uses an environment variable (`MONO_TO_MICRO_DB_ENDPOINT`) but username/password are plaintext in the committed file. The CloudFormation template also contains hardcoded MySQL passwords in the `cfn-init` commands (`MonoToMicroPassword`) and in the RDS cluster definition (`MasterUserPassword: MonoToMicroPassword`). DMS endpoints also have hardcoded credentials. No Secrets Manager, no Vault integration.
- **Gap**: Database credentials are committed to source code in plaintext. CloudFormation template contains hardcoded passwords. No secret rotation mechanism.
- **Compensating Controls**:
  - Rotate the hardcoded credentials immediately and move them to AWS Secrets Manager.
  - Use CloudFormation dynamic references (`{{resolve:secretsmanager:...}}`) for database credentials.
- **Remediation Timeline**: 1–2 weeks (urgent)
- **Recommendation**: Create an AWS Secrets Manager secret for the MySQL credentials. Update `application.properties` to use environment variables populated from Secrets Manager at startup. Update CloudFormation to use dynamic references. Enable automatic rotation.
- **Evidence**: `src/main/resources/application.properties` (plaintext credentials), `../MonoToMicroAssets/MonoToMicroCF.yaml` (hardcoded passwords in cfn-init, RDSCluster, DMS endpoints)

### AUTH-Q8: Agent Identity Suspension
- **Severity**: RISK
- **Finding**: No agent identity suspension mechanism exists. Since authentication is effectively disabled (`permitAll`), there are no agent identities to suspend. No API key revocation endpoints, no service account disable mechanisms, no Cognito user pool management. If an agent misbehaves, the only recourse is to shut down the entire application or block at the network level.
- **Gap**: No ability to isolate or suspend a misbehaving agent without taking down the entire platform.
- **Compensating Controls**:
  - When implementing auth (AUTH-Q1), use Cognito app clients — these can be disabled individually.
  - Implement IP-based blocking at the security group or WAF level as an emergency control.
- **Remediation Timeline**: 30–60 days (aligned with AUTH-Q1 remediation)
- **Recommendation**: Design agent identities as individual Cognito app clients or API Gateway API keys that can be revoked independently. Implement an admin endpoint or runbook for immediate agent suspension.
- **Evidence**: `src/main/java/com/monoToMicro/security/ResourceServerConfig.java` (no auth, no identities to suspend)

### STATE-Q2: Queryable Current State
- **Severity**: RISK
- **Finding**: GET endpoints exist for resource state: `GET /unicorns` returns all unicorns, `GET /unicorns/basket/{userUuid}` returns a user's basket. These allow agents to query current state before taking action. However, the query capabilities are limited — no individual unicorn GET by ID (`GET /unicorns/{uuid}`), no user GET endpoint, no basket status endpoint.
- **Gap**: Partial state queryability. Agents can read product listings and baskets but cannot look up individual resources by ID or query user details.
- **Compensating Controls**:
  - Agents can use `GET /unicorns` and filter client-side (acceptable for small datasets).
  - Add a `GET /unicorns/{uuid}` endpoint for individual resource lookup.
- **Remediation Timeline**: 1–2 weeks
- **Recommendation**: Add individual resource GET endpoints (`GET /unicorns/{uuid}`, `GET /user/{uuid}`) to support agent read-before-write patterns.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/UnicornController.java` (GET /unicorns only), `src/main/java/com/monoToMicro/rest/controller/BasketController.java` (GET /unicorns/basket/{userUuid})

### STATE-Q3: Concurrency Controls
- **Severity**: RISK
- **Finding**: Limited concurrency controls. `UserRepositoryImpl.create()` uses the `synchronized` keyword, providing basic thread-level locking for user creation. The `unicorns_basket` table has a UNIQUE constraint on `(uuid, unicornUuid)` which prevents duplicate basket entries at the database level. However, no optimistic locking exists (no version fields, no ETags, no `If-Match` headers), no `SELECT FOR UPDATE` patterns, no DynamoDB conditional writes.
- **Gap**: No application-level concurrency controls beyond `synchronized` and UNIQUE constraints. Concurrent agent instances modifying the same basket could create race conditions for operations not protected by UNIQUE constraints.
- **Compensating Controls**:
  - The UNIQUE constraint on `unicorns_basket` prevents the most common concurrent-write scenario (duplicate basket items).
  - Limit agent concurrency to 1 instance per user scope during initial pilot.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add optimistic locking with version fields to database tables. Return `ETag` headers on GET responses and require `If-Match` on write requests.
- **Evidence**: `src/main/java/com/monoToMicro/core/repository/UserRepositoryImpl.java` (synchronized), `database/create_tables.sql` (UNIQUE constraints)

### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK
- **Finding**: No circuit breakers or resilience patterns. No Resilience4j, no retry decorators, no exponential backoff, no timeout configurations on the MySQL connection or HTTP clients. Exception handling in repositories is basic `try/catch` with `e.printStackTrace()` — no retry logic, no fallback behavior. The `HealthController.ping()` catches exceptions but only prints "No instance found".
- **Gap**: If the MySQL database becomes slow or unresponsive, the application will cascade failures to all callers (including agents) with no circuit breaking or degraded-mode behavior.
- **Compensating Controls**:
  - Configure MySQL connection pool timeouts in `application.properties` (e.g., `spring.datasource.hikari.connection-timeout=5000`).
  - Implement health check monitoring via the existing `/health/dbping` endpoint to detect database issues.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add Resilience4j dependency and implement circuit breakers on all database calls. Configure connection pool timeouts and query timeouts.
- **Evidence**: `src/main/java/com/monoToMicro/core/repository/UnicornRepositoryImpl.java` (bare try/catch), `src/main/resources/application.properties` (no timeout config)

### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK
- **Finding**: No rate limiting at any layer. The application runs directly on EC2 port 8080 behind nginx with no API Gateway, no WAF, no rate limiting middleware. Nginx configuration in CloudFormation is a simple proxy pass (`proxy_pass http://127.0.0.1:8080/`) with no rate limiting directives. No Spring Boot rate limiting library (no `bucket4j`, no `resilience4j-ratelimiter`).
- **Gap**: A runaway agent loop can DDoS the application at machine speed with no throttling protection.
- **Compensating Controls**:
  - Add nginx rate limiting directives (`limit_req_zone`) as an immediate control.
  - Deploy an API Gateway with usage plans in front of the application.
- **Remediation Timeline**: 1–2 weeks
- **Recommendation**: Deploy AWS API Gateway in front of the application with usage plans and throttling limits per API key (agent identity). Set default limits at 100 requests/second with burst to 200.
- **Evidence**: `../MonoToMicroAssets/MonoToMicroCF.yaml` (nginx proxy_pass, no rate limiting)

### STATE-Q6: Blast Radius and Transaction Limits
- **Severity**: RISK
- **Finding**: No configurable transaction limits per agent identity. No `max_records_per_operation`, no `max_spend_per_hour`, no blast radius controls of any kind. The `GET /unicorns` endpoint returns all unicorns with `SELECT *` (no limit). The `DELETE /unicorns/basket` endpoint deletes by specific user+unicorn UUID (naturally bounded), but there is no limit on how many times an agent can call it.
- **Gap**: No business-level transaction limits. An agent error could repeatedly add/remove basket items or create users without any cap.
- **Compensating Controls**:
  - Implement agent-specific API Gateway usage plans with daily/hourly request quotas.
  - Add application-level rate limiting per user UUID to prevent excessive basket modifications.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement configurable transaction limits at the API Gateway level (per agent identity) and at the application level (per resource scope).
- **Evidence**: `src/main/resources/com/monoToMicro/core/repository/mappers/UnicornMapper.xml` (SELECT * with no LIMIT), `src/main/java/com/monoToMicro/rest/controller/BasketController.java`

### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: RISK
- **Finding**: The CloudFormation template deploys a single `t3.small` EC2 instance with no auto-scaling group, no load balancer, no capacity planning. The infrastructure is designed for a workshop/demo, not production agent traffic. No load test results or configurations found. The RDS cluster uses `db.r6i.2xlarge` (oversized for demo) but the application tier is severely undersized.
- **Gap**: A single t3.small instance cannot handle unpredictable agent traffic patterns. No auto-scaling, no redundancy, no load testing.
- **Compensating Controls**:
  - Limit agent concurrency to match the single-instance capacity (~10 concurrent requests).
  - Implement health checks via `/health/ishealthy` and monitor instance metrics.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Deploy the application behind an ALB with an Auto Scaling Group (minimum 2 instances, scale on CPU/request count). Run load tests simulating agent traffic patterns.
- **Evidence**: `../MonoToMicroAssets/MonoToMicroCF.yaml` (single t3.small EC2Instance, no ASG, no ALB)

### HITL-Q1: Draft/Pending State
- **Severity**: RISK
- **Finding**: No draft or pending state concept. The application performs immediate writes — `POST /unicorns/basket` directly inserts into the database, `POST /user` directly creates the user record. No two-step commit, no status-based state machine, no approval workflow. The `EventContext.java` class defines a `State` enum with `PENDING` and `IN_PROGRESS` values, but these states are never used in any controller or service — only `SUCCESS` and `FAILED` are used.
- **Gap**: All write operations are immediately committed. No draft state for agents to propose changes for human review before execution.
- **Compensating Controls**:
  - Implement human-in-the-loop gates at the agent orchestration layer (not the application) for high-risk operations.
  - Use the existing `EventContext.State.PENDING` enum to implement a pending state in the basket workflow.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement a `status` field on basket and user records that supports `DRAFT`/`PENDING`/`CONFIRMED` states. Write operations create records in `DRAFT` status; a separate confirmation endpoint commits them.
- **Evidence**: `src/main/java/com/monoToMicro/core/events/EventContext.java` (PENDING/IN_PROGRESS defined but unused), `src/main/java/com/monoToMicro/rest/controller/BasketController.java` (immediate writes)

### HITL-Q2: Configurable Approval Gates
- **Severity**: RISK
- **Finding**: No configurable approval gates. No approval API endpoints, no human approval tasks, no operation-level flags requiring confirmation before execution. No Step Functions with `waitForTaskToken` patterns. All operations execute immediately upon request.
- **Gap**: No application-level mechanism to require human approval before executing high-risk operations (e.g., bulk basket modifications, user deletions).
- **Compensating Controls**:
  - Implement approval gates at the agent orchestration layer using Step Functions with human approval tasks.
  - Add a confirmation header requirement (`X-Confirm: true`) for destructive operations.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement a lightweight approval workflow for destructive operations. Consider AWS Step Functions with `waitForTaskToken` for human approval gates.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/BasketController.java` (no approval logic)

### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK
- **Finding**: No sandbox or staging environment configuration. The CloudFormation template deploys a single environment with no staging/sandbox variants. No Docker Compose for local testing. No seed data scripts beyond the initial `create_tables.sql` with sample data. No environment-specific configuration files (`application-staging.properties`, `application-dev.properties`). The only environment variable is `MONO_TO_MICRO_DB_ENDPOINT`.
- **Gap**: No safe environment for testing agent behavior before production deployment. The first time an agent bug is discovered will be in production.
- **Compensating Controls**:
  - Deploy a second CloudFormation stack with a different stack name as a staging environment.
  - Use the existing `create_tables.sql` to seed a local MySQL instance for development testing.
- **Remediation Timeline**: 2–4 weeks
- **Recommendation**: Create environment-specific CloudFormation parameter files (staging, production). Add `application-staging.properties` with staging database credentials. Implement a Docker Compose file for local development.
- **Evidence**: `../MonoToMicroAssets/MonoToMicroCF.yaml` (single environment), `src/main/resources/application.properties` (no profile support)

### DATA-Q3: Selective Query Support
- **Severity**: RISK
- **Finding**: No pagination, filtering, or sorting on any endpoint. `GET /unicorns` executes `SELECT * FROM unicorns` with no `LIMIT`, no `OFFSET`, no `WHERE` clause, no `ORDER BY`. `GET /unicorns/basket/{userUuid}` returns all items in a user's basket with no pagination. No query parameters for filtering or sorting in any controller.
- **Gap**: Agents retrieving product listings receive the full dataset regardless of need. As the unicorns table grows, this will exhaust LLM context windows and increase latency/cost.
- **Compensating Controls**:
  - The current dataset is small (10 unicorns) so full retrieval is acceptable during initial pilot.
  - Add `limit` and `offset` query parameters to GET endpoints.
- **Remediation Timeline**: 2–3 weeks
- **Recommendation**: Add pagination support (`?limit=20&offset=0`) to all GET list endpoints. Add filter parameters (e.g., `?name=...&priceMin=...&priceMax=...`) for product search.
- **Evidence**: `src/main/resources/com/monoToMicro/core/repository/mappers/UnicornMapper.xml` (SELECT * with no LIMIT), `src/main/java/com/monoToMicro/rest/controller/UnicornController.java`

### DATA-Q4: System of Record Designations
- **Severity**: RISK
- **Finding**: No system-of-record designations. No master data management documentation, no data ownership definitions, no conflict resolution logic. The MySQL database is the only data store, but there is no documentation designating it as the authoritative source for unicorn products or user data. The DMS replication to Aurora creates a second copy with no documented system-of-record hierarchy.
- **Gap**: With DMS replication creating data copies, there is no documented authoritative source. An agent querying both systems could receive conflicting data.
- **Compensating Controls**:
  - Document the MySQL instance on the EC2 DB instance as the system of record for unicorn and user data.
  - Treat the Aurora RDS cluster as a read replica only.
- **Remediation Timeline**: 1–2 weeks (documentation)
- **Recommendation**: Create a data ownership document that designates the MySQL database as the system of record for all entities. Define which system wins in case of conflicts.
- **Evidence**: `../MonoToMicroAssets/MonoToMicroCF.yaml` (DMS replication between MySQL and Aurora), `database/create_tables.sql`

### DATA-Q5: Reliable Timestamps
- **Severity**: RISK
- **Finding**: Database tables include `creation_date` (`DEFAULT CURRENT_TIMESTAMP`) and `last_modified_date` fields. The JDBC URL includes `serverTimezone=UTC`, which is good. However, the `CoreModel.java` marks `creationDate` and `lastModifiedDate` as `@JsonIgnore`, so these timestamps are never exposed in API responses. The application code never sets `last_modified_date` on update operations. The `INSERT` statements in `UserMapper.xml` include `#{creationDate}` but the service layer (`UserServiceImpl.java`) does not set `creationDate` before calling create.
- **Gap**: Timestamps exist in the database but are not exposed via the API. `last_modified_date` is never updated on modifications. Agents cannot determine when data was last changed.
- **Compensating Controls**:
  - Remove `@JsonIgnore` from `creationDate` and `lastModifiedDate` in `CoreModel.java` to expose timestamps in API responses.
  - Add MySQL triggers or MyBatis update hooks to set `last_modified_date` on every UPDATE.
- **Remediation Timeline**: 1–2 weeks
- **Recommendation**: Expose `creationDate` and `lastModifiedDate` in API responses. Implement automatic `last_modified_date` updates using MySQL `ON UPDATE CURRENT_TIMESTAMP` or MyBatis interceptors.
- **Evidence**: `database/create_tables.sql` (timestamp columns), `src/main/java/com/monoToMicro/core/model/CoreModel.java` (@JsonIgnore on timestamps), `src/main/resources/application.properties` (serverTimezone=UTC)

### DATA-Q6: Data Freshness Signaling
- **Severity**: RISK
- **Finding**: No data freshness signaling. No `Cache-Control` headers, no `X-Data-Age` headers, no `last_refreshed` fields, no `consistency_level` indicators in API responses. All responses are served directly from the database with no caching layer, so data is current — but there is no way for an agent to verify this programmatically.
- **Gap**: Agents have no mechanism to determine whether returned data is current, cached, or stale.
- **Compensating Controls**:
  - Since data is served directly from MySQL with no caching, it is always current — document this guarantee.
  - Add `Cache-Control: no-cache` headers to make the freshness guarantee explicit.
- **Remediation Timeline**: 1–2 weeks
- **Recommendation**: Add `Cache-Control: no-cache` and `Last-Modified` headers to all GET responses. Expose `last_modified_date` (DATA-Q5) as a response field.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/UnicornController.java` (no Cache-Control headers)

### DATA-Q7: PII Redaction in Logs
- **Severity**: RISK
- **Finding**: No PII redaction in logs. Exception handling uses `e.printStackTrace()` which dumps full stack traces to stdout (shipped to CloudWatch via CloudWatch Agent). User email addresses could appear in stack traces when `UserMapper.getByEmail()` fails. The `HealthController.ping()` logs EC2 metadata including `accountId` and `instanceID` via `System.out.println()`. No log scrubbing middleware, no PII masking libraries, no CloudWatch log filters for PII.
- **Gap**: PII (user email, potentially names) could leak into application logs and be shipped to CloudWatch Logs without masking.
- **Compensating Controls**:
  - Replace `e.printStackTrace()` calls with a structured logging framework (SLF4J/Logback) with PII masking patterns.
  - Add CloudWatch Logs metric filters to detect and alert on PII patterns in log streams.
- **Remediation Timeline**: 2–3 weeks
- **Recommendation**: Replace `System.out.println()` and `e.printStackTrace()` with SLF4J/Logback structured logging. Implement a log masking pattern that redacts email addresses and names from log output.
- **Evidence**: `src/main/java/com/monoToMicro/core/repository/UnicornRepositoryImpl.java` (e.printStackTrace()), `src/main/java/com/monoToMicro/core/repository/UserRepositoryImpl.java` (e.printStackTrace()), `src/main/java/com/monoToMicro/rest/controller/HealthController.java` (System.out.println with metadata)

### DISC-Q1: Schema Documentation and Versioning
- **Severity**: RISK
- **Finding**: No data schemas are documented or versioned independently. The database schema is defined in `create_tables.sql` but there is no schema versioning tool (no Flyway, no Liquibase, no schema registry). MyBatis XML mappers define result mappings but these are not versioned API schemas. No JSON Schema files. Schema changes would be applied directly to the database with no migration tracking.
- **Gap**: No schema versioning or migration tracking. Schema changes could break agent queries silently.
- **Compensating Controls**:
  - Use `create_tables.sql` as the baseline schema reference for agent tool definition.
  - Add Flyway or Liquibase for schema migration tracking.
- **Remediation Timeline**: 2–4 weeks
- **Recommendation**: Add Flyway dependency to `build.gradle` and convert `create_tables.sql` to a Flyway migration (`V1__initial_schema.sql`). Document the API response schema in the OpenAPI spec (API-Q2).
- **Evidence**: `database/create_tables.sql` (unversioned schema), `src/main/resources/com/monoToMicro/core/repository/mappers/UnicornMapper.xml` (MyBatis result mappings), `build.gradle` (no Flyway/Liquibase dependency)

### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK
- **Finding**: No distributed tracing. No OpenTelemetry SDK, no X-Ray instrumentation, no `traceparent` header propagation. Logging is entirely unstructured — `System.out.println()` and `e.printStackTrace()` to stdout, collected by CloudWatch Agent as plain text. No JSON log format, no correlation IDs (`request_id`, `trace_id`), no structured fields.
- **Gap**: Agent-initiated requests cannot be traced through the application. Failures produce unstructured stack traces with no correlation to the originating request.
- **Compensating Controls**:
  - Add AWS X-Ray SDK to the application for distributed tracing.
  - Implement a servlet filter that generates and logs a `request_id` for each inbound request.
- **Remediation Timeline**: 2–4 weeks
- **Recommendation**: Add X-Ray SDK and SLF4J/Logback to `build.gradle`. Configure structured JSON logging with `request_id`, `trace_id`, `user_id`, and `action` fields. Add X-Ray instrumentation to Spring Boot via the `aws-xray-recorder-sdk-spring` library.
- **Evidence**: `build.gradle` (no X-Ray, no SLF4J), `src/main/java/com/monoToMicro/rest/controller/HealthController.java` (System.out.println)

### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK
- **Finding**: No alerting thresholds configured for error rates or latency. The CloudFormation template creates a CloudWatch log group (`InstanceLogGroup` with 7-day retention) but no CloudWatch alarms, no anomaly detection, no PagerDuty/OpsGenie integration, no composite alarms. No SLO-based alerting. The application exposes no metrics — Spring Boot Actuator is included in dependencies but no custom metrics are published.
- **Gap**: Application degradation affecting agent operations would go undetected until agents start failing.
- **Compensating Controls**:
  - Create CloudWatch alarms on EC2 instance CPU utilization and status checks as a minimum.
  - Monitor the `/health/dbping` endpoint externally.
- **Remediation Timeline**: 2–3 weeks
- **Recommendation**: Configure CloudWatch alarms for: (1) EC2 CPU > 80%, (2) error log patterns in CloudWatch Logs, (3) `/health/ishealthy` external health check. Enable Spring Boot Actuator metrics endpoint and publish to CloudWatch.
- **Evidence**: `../MonoToMicroAssets/MonoToMicroCF.yaml` (InstanceLogGroup, no alarms), `build.gradle` (spring-boot-starter-actuator dependency)

### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK
- **Finding**: Partial IaC governance. (1) **IaC exists**: The CloudFormation template (`MonoToMicroCF.yaml`) defines VPC, EC2, RDS, IAM, and S3 resources as code — PASS. (2) **Change review**: The GitHub Actions workflow runs cfn-nag security scanning on push (`cfn-security.yml`), but only scans `MonoToMicroAssets/` and there are no explicit PR review requirements configured in the repository — PARTIAL. (3) **Drift detection**: No AWS Config rules, no CloudFormation drift detection configuration — FAIL. Only 1 of 3 sub-checks fully passes.
- **Gap**: No drift detection. No mandatory peer review for IaC changes. Security scanning exists but does not cover all infrastructure.
- **Compensating Controls**:
  - Enable CloudFormation drift detection as a scheduled check.
  - Add branch protection rules requiring PR approval before merge.
- **Remediation Timeline**: 2–4 weeks
- **Recommendation**: Enable CloudFormation drift detection on a daily schedule. Add branch protection rules requiring at least 1 reviewer. Extend cfn-nag to scan all CloudFormation templates.
- **Evidence**: `../MonoToMicroAssets/MonoToMicroCF.yaml`, `../.github/workflows/cfn-security.yml` (scans MonoToMicroAssets only)

### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK
- **Finding**: No CI/CD pipeline for the application itself. The GitHub Actions workflow (`cfn-security.yml`) only runs cfn-nag on CloudFormation templates on push. No application build pipeline, no test execution, no API contract testing, no breaking change detection. The application is built manually via `gradlew clean build` on the EC2 instance during CloudFormation `cfn-init` initialization — not through a CI/CD pipeline.
- **Gap**: No automated pipeline builds or tests the application. API-breaking changes cannot be detected before deployment.
- **Compensating Controls**:
  - Create a GitHub Actions workflow that builds the application with `gradlew clean build` and runs tests (once tests exist — ENG-Q4).
  - Add OpenAPI spec validation to the CI pipeline (once the spec exists — API-Q2).
- **Remediation Timeline**: 2–4 weeks
- **Recommendation**: Create a CI pipeline that: (1) builds the application, (2) runs unit/integration tests, (3) validates the OpenAPI spec against the implementation, (4) checks for breaking API changes.
- **Evidence**: `../.github/workflows/cfn-security.yml` (cfn-nag only), `../MonoToMicroAssets/MonoToMicroCF.yaml` (gradlew build in cfn-init)

### ENG-Q3: Rollback Capability
- **Severity**: RISK
- **Finding**: No rollback capability. Single EC2 instance deployment with no blue/green, no canary, no CodeDeploy, no feature flags, no traffic shifting. The application is deployed via CloudFormation `cfn-init` which clones the repository and builds on the instance at stack creation time. Rollback requires redeploying the entire CloudFormation stack, which takes 15–30 minutes and includes full infrastructure recreation.
- **Gap**: No fast rollback. A broken deployment affecting agent-facing APIs requires full stack redeployment.
- **Compensating Controls**:
  - Use CloudFormation stack update rollback (automatic on failure).
  - Pre-build the application JAR and store in S3; deploy from S3 artifact instead of building on-instance.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement blue/green deployment using CodeDeploy or deploy behind an ALB with rolling updates. Pre-build JAR artifacts in CI and deploy from S3.
- **Evidence**: `../MonoToMicroAssets/MonoToMicroCF.yaml` (single EC2Instance, cfn-init build-on-instance)

### ENG-Q4: API Test Coverage
- **Severity**: RISK
- **Finding**: No automated tests found. No `src/test/` directory exists. `build.gradle` includes `spring-boot-starter-test` as a `testImplementation` dependency, but no test files exist anywhere in the source tree. No API test suites, no contract tests, no integration tests, no Postman/Newman collections.
- **Gap**: Zero test coverage. API behavior changes cannot be caught by automated testing.
- **Compensating Controls**:
  - Write basic smoke tests against the running application endpoints as a first step.
  - Create Postman/Newman API test collections for the existing endpoints.
- **Remediation Timeline**: 2–4 weeks
- **Recommendation**: Create `src/test/` directory with: (1) unit tests for services, (2) integration tests for controllers using `@SpringBootTest`, (3) API contract tests validating request/response schemas. Target minimum 80% coverage of controller endpoints.
- **Evidence**: `build.gradle` (spring-boot-starter-test dependency, no test files), repository-wide search found no test files

### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: RISK
- **Finding**: No encryption at rest configured. The RDS cluster (`RDSCluster` in CloudFormation) does not specify `StorageEncrypted: true` or `KmsKeyId`. S3 buckets (`UIBucket`, `AssetBucket`) do not specify server-side encryption configuration. The EC2 instance has no EBS encryption specified. User PII (email, first_name, last_name) is stored unencrypted at rest.
- **Gap**: All data at rest (MySQL database, S3 buckets, EBS volumes) is unencrypted. A breach exposes all data the agent can access.
- **Compensating Controls**:
  - Enable default EBS encryption at the account level.
  - Enable S3 default encryption on both buckets.
- **Remediation Timeline**: 1–2 weeks
- **Recommendation**: Add `StorageEncrypted: true` to the RDS cluster in CloudFormation. Add `BucketEncryption` with `aws:kms` to both S3 buckets. Enable account-level EBS encryption default.
- **Evidence**: `../MonoToMicroAssets/MonoToMicroCF.yaml` (RDSCluster without StorageEncrypted, UIBucket/AssetBucket without BucketEncryption)

---

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: The application exposes REST endpoints via Spring Boot `@RestController` and `@Controller` annotations. Endpoints found: `GET /unicorns`, `POST /unicorns/basket`, `DELETE /unicorns/basket`, `GET /unicorns/basket/{userUuid}`, `POST /user`, `POST /user/login`, `GET /health/ping`, `GET /health/ishealthy`, `GET /health/dbping`, `GET /data`. These are genuine REST APIs with JSON serialization — no direct database access, file-based exchange, or UI automation required by consumers. The API surface is functional but minimal and undocumented.
- **Implication**: REST APIs exist and can serve as agent tool endpoints. The surface is small enough to define as agent tools with manageable effort. However, the APIs lack documentation (API-Q2) and the endpoint design is consumer-facing (e-commerce UI) rather than service-facing (agent-optimized).
- **Recommendation**: Consider designing agent-specific API endpoints (e.g., `/api/v1/orders`, `/api/v1/returns`) that expose order and return data optimized for agent consumption, rather than repurposing the existing UI-facing endpoints.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/UnicornController.java`, `src/main/java/com/monoToMicro/rest/controller/BasketController.java`, `src/main/java/com/monoToMicro/rest/controller/UserController.java`, `src/main/java/com/monoToMicro/rest/controller/HealthController.java`, `src/main/java/com/monoToMicro/rest/controller/DataReplicationController.java`

### API-Q6: Structured Response Format
- **Severity**: INFO
- **Finding**: Responses are JSON format via Jackson serialization (Spring Boot default). Model classes use `@JsonInclude(JsonInclude.Include.NON_NULL)` for clean serialization and `@JsonSerialize(include = JsonSerialize.Inclusion.NON_NULL)` on `CoreModel`. Fields are standard Java types (String, Double, Long, Boolean, List). JSON responses are well-structured for agent consumption.
- **Implication**: JSON responses are LLM-friendly and can be consumed directly by agent tools without format conversion. The `NON_NULL` serialization strategy keeps responses clean.
- **Recommendation**: No action required. JSON is the preferred format for agent consumption.
- **Evidence**: `src/main/java/com/monoToMicro/core/model/Unicorn.java` (@JsonInclude), `src/main/java/com/monoToMicro/core/model/CoreModel.java` (@JsonSerialize)

### API-Q8: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: No event emission capability exists. No webhook endpoints, no SNS/EventBridge/SQS integration, no Kafka topics, no CDC pipelines in the application code. The DMS replication configured in CloudFormation performs database-level replication but this is not an application event system. State changes (basket additions/removals, user creation) are only reflected in the database.
- **Implication**: Agents must use request/response polling patterns to detect state changes. Proactive agent behaviors (e.g., reacting to basket changes or new user registrations) are not possible without implementing an event system. This limits initial agent deployments to request-driven patterns.
- **Recommendation**: When adding order processing capabilities, implement EventBridge integration to emit events for state changes (e.g., `basket.item.added`, `user.created`, `order.placed`). This enables event-driven agent patterns.
- **Evidence**: `src/main/java/com/monoToMicro/core/services/UnicornServiceImpl.java` (no event emission), `../MonoToMicroAssets/MonoToMicroCF.yaml` (DMS replication only)

### API-Q9: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit documentation or rate limit headers found in the application code. The application runs directly on EC2 port 8080 behind nginx with no API Gateway in front. No `X-RateLimit-Remaining` or `Retry-After` headers in response code. No `aws_api_gateway_usage_plan` in IaC. No rate limiting middleware in the application.
- **Implication**: Agents calling this API have no visibility into rate limits and cannot self-throttle. When rate limiting is implemented (STATE-Q5), agents will need headers to respect limits.
- **Recommendation**: When implementing API Gateway (STATE-Q5 remediation), configure usage plans with rate limit headers (`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After`) that agents can consume.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/UnicornController.java` (no rate limit headers), `../MonoToMicroAssets/MonoToMicroCF.yaml` (no API Gateway)

### API-Q10: API Latency Profile
- **Severity**: INFO
- **Finding**: No performance benchmarks, load test results, or APM configuration found. The application is a simple Spring Boot app with MyBatis SQL queries against a MySQL database. Operations are simple CRUD — `SELECT *` for listings, `INSERT IGNORE` for basket additions, `DELETE` for removals. Based on the operation complexity, P95 latency is likely sub-second for all current endpoints, but there is no measured evidence to confirm.
- **Implication**: The simple CRUD operations should be suitable for synchronous agent tool patterns. If the agent chains 5 sequential calls, total latency should remain under 5 seconds. However, without APM data, latency spikes under load are unpredictable.
- **Recommendation**: Add APM instrumentation (X-Ray or Spring Boot Actuator metrics) to measure P95 latency per endpoint. Establish latency baselines before agent integration.
- **Evidence**: `src/main/resources/com/monoToMicro/core/repository/mappers/UnicornMapper.xml` (simple SQL queries), `build.gradle` (spring-boot-starter-actuator dependency, but no metrics configuration)

### DATA-Q8: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics, dashboards, or profiling exist. No null rate monitoring, no duplicate detection beyond UNIQUE constraints, no data freshness SLAs, no data quality scoring. The database enforces basic integrity through NOT NULL constraints on key fields (uuid) and UNIQUE constraints on business keys (uuid, email).
- **Implication**: Agents acting on incomplete or stale data will propagate errors. The current dataset is small and seed-generated (10 unicorns), so quality is implicitly high. As the dataset grows or is populated from external sources, data quality monitoring becomes critical.
- **Recommendation**: Implement data quality checks (null rate, duplicate rate, freshness) as part of the observability stack. Consider AWS Glue DataBrew for data profiling.
- **Evidence**: `database/create_tables.sql` (UNIQUE/NOT NULL constraints), `src/main/resources/com/monoToMicro/core/repository/mappers/UnicornMapper.xml`

### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Field names are mostly human-readable and semantically meaningful: `uuid`, `name`, `description`, `price`, `image`, `email`, `first_name`, `last_name`, `creation_date`, `last_modified_date`, `active`. The database column `unicornUuid` uses camelCase in a SQL context (unconventional but readable). No legacy abbreviations requiring a data dictionary. The `CoreModel` uses standard Java naming conventions.
- **Implication**: LLM-based agents can interpret field names without a data dictionary lookup. The naming conventions are agent-friendly and reduce the risk of misinterpretation.
- **Recommendation**: Maintain the current naming conventions. When adding new fields, continue using descriptive, unabbreviated names.
- **Evidence**: `database/create_tables.sql` (column names), `src/main/java/com/monoToMicro/core/model/Unicorn.java` (field names), `src/main/java/com/monoToMicro/core/model/User.java`

### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No data catalog or metadata layer exists. No AWS Glue Data Catalog, no Collibra/Alation/DataHub integration, no metadata files, no data dictionaries, no API catalogs. The only schema documentation is the `create_tables.sql` file.
- **Implication**: When building agent tools, developers must inspect source code and SQL files to understand data structures. This slows tool definition and increases the risk of misinterpreting data semantics.
- **Recommendation**: Create a basic data dictionary documenting each table, its columns, data types, and business meaning. Consider AWS Glue Data Catalog for automated schema discovery.
- **Evidence**: `database/create_tables.sql` (only schema reference)

### DISC-Q4: Data Lineage
- **Severity**: INFO
- **Finding**: No data lineage records exist. No data lineage tools (no AWS Glue DataBrew, no Apache Atlas), no ETL documentation, no data flow diagrams, no transformation logs, no source-to-target mappings. The DMS replication configuration in CloudFormation copies data from MySQL to Aurora but there is no lineage documentation for this data flow.
- **Implication**: When an agent produces incorrect output due to bad data, there is no lineage to trace the data origin. The DMS replication creates a second data copy with no documented lineage.
- **Recommendation**: Document the data flow: seed data → MySQL (EC2) → DMS → Aurora. When adding new data sources, implement lineage tracking.
- **Evidence**: `../MonoToMicroAssets/MonoToMicroCF.yaml` (DMS replication, no lineage), `database/create_tables.sql` (seed data)

### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No business outcome metrics are published. No `cloudwatch.put_metric_data` calls for business events. No custom dashboards tracking basket conversion rates, user registration rates, or order completion rates. Spring Boot Actuator is included as a dependency but no custom metrics endpoints are configured.
- **Implication**: When agents consume this system, there will be no business-level signal for whether agent interactions produce good outcomes. Infrastructure metrics alone cannot indicate whether agents are successfully serving customers.
- **Recommendation**: Define and publish custom CloudWatch metrics for key business outcomes: basket add rate, user creation rate, basket abandonment rate. These become the primary signal for agent effectiveness.
- **Evidence**: `build.gradle` (spring-boot-starter-actuator, no custom metrics), `src/main/java/com/monoToMicro/rest/controller/BasketController.java` (no metrics emission)

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: The application exposes REST endpoints via Spring Boot `@RestController` and `@Controller` annotations: `GET /unicorns`, `POST /unicorns/basket`, `DELETE /unicorns/basket`, `GET /unicorns/basket/{userUuid}`, `POST /user`, `POST /user/login`, `GET /health/ping`, `GET /health/ishealthy`, `GET /health/dbping`, `GET /data`. Genuine REST APIs with JSON serialization. No direct DB access or UI automation required.
- **Gap**: API surface exists but is undocumented. No formal API documentation beyond source code.
- **Recommendation**: Create formal API documentation and consider agent-specific endpoints for order and return data.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/UnicornController.java`, `src/main/java/com/monoToMicro/rest/controller/BasketController.java`, `src/main/java/com/monoToMicro/rest/controller/UserController.java`, `src/main/java/com/monoToMicro/rest/controller/HealthController.java`, `src/main/java/com/monoToMicro/rest/controller/DataReplicationController.java`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK
- **Finding**: No OpenAPI, Swagger, AsyncAPI, GraphQL, or Smithy specification files found. API defined solely through Spring annotations.
- **Gap**: No machine-readable API spec for automated agent tool generation.
- **Recommendation**: Add `springdoc-openapi-ui` to `build.gradle` for auto-generated OpenAPI 3.0 spec.
- **Evidence**: `build.gradle` (no springdoc/swagger dependency)

#### API-Q3: Structured Error Responses
- **Severity**: RISK
- **Finding**: Error responses are bare `HttpStatus.BAD_REQUEST` with no structured body. Repositories catch exceptions with `e.printStackTrace()` and return `null`/`false`.
- **Gap**: No error codes, messages, or retryable indicators for agents.
- **Recommendation**: Implement `@ControllerAdvice` global exception handler with structured JSON error responses.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/UnicornController.java`, `src/main/java/com/monoToMicro/core/repository/UnicornRepositoryImpl.java`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: BLOCKER
- **Conditional**: agent_scope is "write-enabled" — evaluated as BLOCKER
- **Finding**: No idempotency key support on write endpoints. `INSERT IGNORE` provides partial DB-level protection. `POST /user` generates server-side UUID with no client idempotency key.
- **Gap**: No client-facing idempotency contract. Agent retries can cause inconsistent state.
- **Recommendation**: Implement `Idempotency-Key` header support on all write endpoints.
- **Evidence**: `src/main/resources/com/monoToMicro/core/repository/mappers/UnicornMapper.xml`, `src/main/java/com/monoToMicro/core/services/UserServiceImpl.java`

#### API-Q5: API Versioning and Deprecation
- **Severity**: RISK
- **Finding**: No API versioning. Bare paths (`/unicorns`, `/user`). No `Accept-Version` headers, no changelog.
- **Gap**: Breaking API changes will silently break agent tool definitions.
- **Recommendation**: Add `/v1/` URL prefix to all endpoints. Establish deprecation policy.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/UnicornController.java`, `src/main/java/com/monoToMicro/rest/controller/UserController.java`

#### API-Q6: Structured Response Format
- **Severity**: INFO
- **Finding**: JSON responses via Jackson serialization. `@JsonInclude(NON_NULL)` on models. Standard Java types.
- **Gap**: N/A — JSON format is agent-friendly.
- **Recommendation**: No action required.
- **Evidence**: `src/main/java/com/monoToMicro/core/model/Unicorn.java`, `src/main/java/com/monoToMicro/core/model/CoreModel.java`

#### API-Q7: Asynchronous Operation Support
- **Severity**: RISK
- **Finding**: All operations are synchronous. No async patterns, no job frameworks, no polling endpoints, no webhooks.
- **Gap**: Long-running operations would block agents.
- **Recommendation**: Implement async patterns for operations exceeding 5 seconds.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/BasketController.java`, `src/main/java/com/monoToMicro/rest/controller/DataReplicationController.java`

#### API-Q8: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: No event emission capability. No webhooks, SNS, EventBridge, SQS, or Kafka integration.
- **Gap**: N/A — agents limited to request/response patterns initially.
- **Recommendation**: Implement EventBridge events for state changes when adding complex workflows.
- **Evidence**: `src/main/java/com/monoToMicro/core/services/UnicornServiceImpl.java`

#### API-Q9: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit headers or documentation. No API Gateway. No rate limiting middleware.
- **Gap**: N/A — agents cannot self-throttle without rate limit signals.
- **Recommendation**: Include rate limit headers when implementing API Gateway.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/UnicornController.java`

#### API-Q10: API Latency Profile
- **Severity**: INFO
- **Finding**: No performance benchmarks or APM data. Simple CRUD operations likely sub-second but unmeasured.
- **Gap**: N/A — no measured latency data available.
- **Recommendation**: Add X-Ray or Actuator metrics instrumentation.
- **Evidence**: `src/main/resources/com/monoToMicro/core/repository/mappers/UnicornMapper.xml`, `build.gradle`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: Spring Security OAuth2 configured (`@EnableResourceServer`) but `authorizeRequests().anyRequest().permitAll()` disables authentication. Every endpoint uses `@PreAuthorize("permitAll()")`.
- **Gap**: No authentication enforced. Any caller invokes any endpoint without credentials.
- **Recommendation**: Enable OAuth2 validation, configure Cognito app clients for machine identity.
- **Evidence**: `src/main/java/com/monoToMicro/security/ResourceServerConfig.java`, `build.gradle`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK
- **Finding**: IAM role in CloudFormation scoped to S3 buckets. Application has no authorization model — `permitAll()` on all endpoints.
- **Gap**: No application-level permission model.
- **Recommendation**: Implement Spring Security RBAC with `AGENT_READ`/`AGENT_WRITE` roles.
- **Evidence**: `src/main/java/com/monoToMicro/security/ResourceServerConfig.java`, `../MonoToMicroAssets/MonoToMicroCF.yaml`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK
- **Finding**: No action-level authorization. All endpoints use `@PreAuthorize("permitAll()")`. No read vs write differentiation.
- **Gap**: Cannot grant read-only access to an agent.
- **Recommendation**: Implement `@PreAuthorize("hasRole('WRITE')")` for write endpoints.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/UnicornController.java`, `src/main/java/com/monoToMicro/rest/controller/BasketController.java`

#### AUTH-Q4: Identity Propagation
- **Severity**: RISK
- **Finding**: OAuth2 libraries present but unused. No JWT extraction, no token exchange, no user context propagation.
- **Gap**: Application cannot distinguish requests from different users or agents.
- **Recommendation**: Configure OAuth2 resource server JWT validation. Use `SecurityContextHolder` for identity propagation.
- **Evidence**: `build.gradle`, `src/main/java/com/monoToMicro/security/ResourceServerConfig.java`

#### AUTH-Q5: Agent-as-Self vs Agent-on-Behalf-of-User
- **Severity**: RISK
- **Finding**: No identity model exists. All requests are anonymous. No distinction between access modes.
- **Gap**: Cannot differentiate agent-as-self from agent-on-behalf-of-user.
- **Recommendation**: Design separate OAuth2 flows for each mode.
- **Evidence**: `src/main/java/com/monoToMicro/security/ResourceServerConfig.java`

#### AUTH-Q6: Credential Management
- **Severity**: RISK
- **Finding**: Plaintext credentials in `application.properties` and CloudFormation template. No Secrets Manager, no Vault.
- **Gap**: Database credentials committed to source code.
- **Recommendation**: Migrate credentials to AWS Secrets Manager with automatic rotation.
- **Evidence**: `src/main/resources/application.properties`, `../MonoToMicroAssets/MonoToMicroCF.yaml`

#### AUTH-Q7: Immutable Audit Logging ⚡
- **Severity**: BLOCKER
- **Conditional**: agent_scope is "write-enabled" — evaluated as BLOCKER
- **Finding**: No audit logging. CloudWatch Logs captures `System.out.println()` only. 7-day retention. No immutable storage, no principal attribution.
- **Gap**: No structured audit trail of write operations.
- **Recommendation**: Implement structured JSON audit logging. Ship to S3 with object lock.
- **Evidence**: `../MonoToMicroAssets/MonoToMicroCF.yaml`, `src/main/java/com/monoToMicro/rest/controller/BasketController.java`

#### AUTH-Q8: Agent Identity Suspension
- **Severity**: RISK
- **Finding**: No agent identity suspension mechanism. No identities exist to suspend (auth disabled).
- **Gap**: Cannot isolate a misbehaving agent.
- **Recommendation**: Design agent identities as individually revocable Cognito app clients.
- **Evidence**: `src/main/java/com/monoToMicro/security/ResourceServerConfig.java`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: BLOCKER
- **Conditional**: agent_scope is "write-enabled" — evaluated as BLOCKER
- **Finding**: No compensation or rollback for multi-step operations. `@Transactional` on individual operations only. No saga, no undo endpoints, no Step Functions.
- **Gap**: Multi-step agent workflows leave partial state on failure.
- **Recommendation**: Implement compensation endpoints and consider Step Functions for workflow orchestration.
- **Evidence**: `src/main/java/com/monoToMicro/core/repository/UnicornRepositoryImpl.java`, `src/main/java/com/monoToMicro/core/services/UnicornServiceImpl.java`

#### STATE-Q2: Queryable Current State
- **Severity**: RISK
- **Finding**: `GET /unicorns` and `GET /unicorns/basket/{userUuid}` provide state queries. No individual resource GETs, no user query endpoint.
- **Gap**: Partial state queryability. No individual resource lookup.
- **Recommendation**: Add `GET /unicorns/{uuid}` and `GET /user/{uuid}` endpoints.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/UnicornController.java`, `src/main/java/com/monoToMicro/rest/controller/BasketController.java`

#### STATE-Q3: Concurrency Controls
- **Severity**: RISK
- **Finding**: `synchronized` keyword on user creation. UNIQUE constraints prevent duplicate basket entries. No optimistic locking, no ETags.
- **Gap**: No application-level concurrency controls beyond basic mechanisms.
- **Recommendation**: Add version fields and ETag support for optimistic locking.
- **Evidence**: `src/main/java/com/monoToMicro/core/repository/UserRepositoryImpl.java`, `database/create_tables.sql`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK
- **Finding**: No circuit breakers. Bare `try/catch` with `e.printStackTrace()`. No timeouts, no retry logic, no fallbacks.
- **Gap**: Database failures cascade to all callers with no protection.
- **Recommendation**: Add Resilience4j circuit breakers and configure connection pool timeouts.
- **Evidence**: `src/main/java/com/monoToMicro/core/repository/UnicornRepositoryImpl.java`, `src/main/resources/application.properties`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK
- **Finding**: No rate limiting at any layer. Direct EC2 behind nginx. No API Gateway, no WAF.
- **Gap**: No protection against runaway agent loops.
- **Recommendation**: Deploy API Gateway with usage plans and throttling.
- **Evidence**: `../MonoToMicroAssets/MonoToMicroCF.yaml`

#### STATE-Q6: Blast Radius and Transaction Limits
- **Severity**: RISK
- **Finding**: No configurable transaction limits. No per-agent quotas.
- **Gap**: No business-level caps on agent operations.
- **Recommendation**: Implement agent-specific transaction limits via API Gateway usage plans.
- **Evidence**: `src/main/resources/com/monoToMicro/core/repository/mappers/UnicornMapper.xml`, `src/main/java/com/monoToMicro/rest/controller/BasketController.java`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: RISK
- **Finding**: Single t3.small EC2 instance. No ASG, no ALB, no load testing. Workshop-grade infrastructure.
- **Gap**: Cannot handle unpredictable agent traffic.
- **Recommendation**: Deploy behind ALB with Auto Scaling Group. Conduct load testing.
- **Evidence**: `../MonoToMicroAssets/MonoToMicroCF.yaml`

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State
- **Severity**: RISK
- **Finding**: No draft/pending state. Writes commit immediately. `EventContext.State` enum defines `PENDING`/`IN_PROGRESS` but neither is used.
- **Gap**: No draft state for agent proposals requiring human review.
- **Recommendation**: Implement `DRAFT`/`PENDING`/`CONFIRMED` status on records.
- **Evidence**: `src/main/java/com/monoToMicro/core/events/EventContext.java`, `src/main/java/com/monoToMicro/rest/controller/BasketController.java`

#### HITL-Q2: Configurable Approval Gates
- **Severity**: RISK
- **Finding**: No approval gates. All operations execute immediately. No Step Functions approval tasks.
- **Gap**: No mechanism to require human approval for high-risk operations.
- **Recommendation**: Implement Step Functions with `waitForTaskToken` for approval workflows.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/BasketController.java`

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK
- **Finding**: Single environment deployment. No staging/sandbox. No Docker Compose. No environment-specific configs.
- **Gap**: No safe testing environment for agent behavior.
- **Recommendation**: Create staging CloudFormation parameter files and Docker Compose for local dev.
- **Evidence**: `../MonoToMicroAssets/MonoToMicroCF.yaml`, `src/main/resources/application.properties`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: No data classification. `unicorn_user` table contains PII (email, first_name, last_name) in plaintext. No field-level encryption, no Macie, no classification tags on CloudFormation resources.
- **Gap**: PII stored and exposed without classification or access controls.
- **Recommendation**: Classify all PII fields. Enable Macie. Add field-level access controls.
- **Evidence**: `database/create_tables.sql`, `src/main/java/com/monoToMicro/core/model/User.java`, `../MonoToMicroAssets/MonoToMicroCF.yaml`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: BLOCKER
- **Conditional**: agent_scope is "write-enabled" — evaluated as BLOCKER
- **Finding**: No data residency controls. No GDPR/LGPD references. PII could be sent to any jurisdiction by an agent.
- **Gap**: No data residency policy or enforcement.
- **Recommendation**: Document residency requirements. Enforce region-restricted data processing.
- **Evidence**: `../MonoToMicroAssets/MonoToMicroCF.yaml`, `database/create_tables.sql`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK
- **Finding**: No pagination, filtering, or sorting. `SELECT *` with no LIMIT on all queries.
- **Gap**: Unbounded result sets will exhaust agent context windows.
- **Recommendation**: Add `?limit=20&offset=0` pagination to GET endpoints.
- **Evidence**: `src/main/resources/com/monoToMicro/core/repository/mappers/UnicornMapper.xml`, `src/main/java/com/monoToMicro/rest/controller/UnicornController.java`

#### DATA-Q4: System of Record Designations
- **Severity**: RISK
- **Finding**: No SoR designations. DMS replication creates data copies with no documented hierarchy.
- **Gap**: No authoritative data source documented.
- **Recommendation**: Document MySQL as system of record. Treat Aurora as read replica.
- **Evidence**: `../MonoToMicroAssets/MonoToMicroCF.yaml`, `database/create_tables.sql`

#### DATA-Q5: Reliable Timestamps
- **Severity**: RISK
- **Finding**: `creation_date` and `last_modified_date` exist in DB but are `@JsonIgnore` in `CoreModel.java`. `last_modified_date` never updated. `serverTimezone=UTC` in JDBC URL.
- **Gap**: Timestamps exist but are not exposed via API or maintained on updates.
- **Recommendation**: Remove `@JsonIgnore` from timestamps. Add `ON UPDATE CURRENT_TIMESTAMP`.
- **Evidence**: `database/create_tables.sql`, `src/main/java/com/monoToMicro/core/model/CoreModel.java`, `src/main/resources/application.properties`

#### DATA-Q6: Data Freshness Signaling
- **Severity**: RISK
- **Finding**: No `Cache-Control`, `X-Data-Age`, or freshness headers. Data served directly from DB (always current).
- **Gap**: No programmatic freshness verification for agents.
- **Recommendation**: Add `Cache-Control: no-cache` and `Last-Modified` headers.
- **Evidence**: `src/main/java/com/monoToMicro/rest/controller/UnicornController.java`

#### DATA-Q7: PII Redaction in Logs
- **Severity**: RISK
- **Finding**: `e.printStackTrace()` dumps stack traces with potential PII. No log scrubbing, no PII masking.
- **Gap**: PII can leak into CloudWatch Logs.
- **Recommendation**: Replace with SLF4J structured logging with PII masking patterns.
- **Evidence**: `src/main/java/com/monoToMicro/core/repository/UnicornRepositoryImpl.java`, `src/main/java/com/monoToMicro/core/repository/UserRepositoryImpl.java`

#### DATA-Q8: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics. UNIQUE/NOT NULL constraints provide basic integrity. Small seed dataset.
- **Gap**: N/A — dataset is small and seed-generated.
- **Recommendation**: Implement data quality monitoring as dataset grows.
- **Evidence**: `database/create_tables.sql`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Documentation and Versioning
- **Severity**: RISK
- **Finding**: Schema in `create_tables.sql` only. No Flyway/Liquibase. No JSON Schema. No schema registry.
- **Gap**: No schema versioning. Changes break agent queries silently.
- **Recommendation**: Add Flyway for migration tracking. Document API schemas in OpenAPI spec.
- **Evidence**: `database/create_tables.sql`, `build.gradle`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Fields are human-readable: `uuid`, `name`, `description`, `price`, `email`, `first_name`, `last_name`. No legacy abbreviations.
- **Gap**: N/A — naming is agent-friendly.
- **Recommendation**: Maintain current conventions.
- **Evidence**: `database/create_tables.sql`, `src/main/java/com/monoToMicro/core/model/Unicorn.java`, `src/main/java/com/monoToMicro/core/model/User.java`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No data catalog. No Glue Data Catalog, no Collibra, no metadata files.
- **Gap**: N/A — developers must inspect source code for data structures.
- **Recommendation**: Create a basic data dictionary. Consider AWS Glue Data Catalog.
- **Evidence**: `database/create_tables.sql`

#### DISC-Q4: Data Lineage
- **Severity**: INFO
- **Finding**: No data lineage. DMS replication has no documented lineage. No ETL documentation.
- **Gap**: N/A — cannot trace data origin for debugging.
- **Recommendation**: Document data flow: seed data → MySQL → DMS → Aurora.
- **Evidence**: `../MonoToMicroAssets/MonoToMicroCF.yaml`, `database/create_tables.sql`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK
- **Finding**: No distributed tracing (no X-Ray, no OpenTelemetry). Unstructured logging (`System.out.println()`, `e.printStackTrace()`). CloudWatch Agent collects plain text logs. No correlation IDs.
- **Gap**: Agent-initiated requests cannot be traced. No structured log correlation.
- **Recommendation**: Add X-Ray SDK and SLF4J/Logback with JSON formatting and correlation IDs.
- **Evidence**: `build.gradle`, `src/main/java/com/monoToMicro/rest/controller/HealthController.java`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK
- **Finding**: No CloudWatch alarms. Log group with 7-day retention only. No anomaly detection. Spring Boot Actuator present but unconfigured.
- **Gap**: Application degradation goes undetected.
- **Recommendation**: Configure CloudWatch alarms on CPU, error patterns, and external health checks.
- **Evidence**: `../MonoToMicroAssets/MonoToMicroCF.yaml`, `build.gradle`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No business metrics published. No custom CloudWatch metrics. Actuator present but no custom endpoints.
- **Gap**: N/A — no business-level signal for agent effectiveness.
- **Recommendation**: Publish CloudWatch metrics for basket add rate, user creation rate, basket abandonment.
- **Evidence**: `build.gradle`, `src/main/java/com/monoToMicro/rest/controller/BasketController.java`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK
- **Finding**: CloudFormation IaC exists. cfn-nag scans MonoToMicroAssets on push. No drift detection. No PR review requirements. 1 of 3 sub-checks passes.
- **Gap**: No drift detection. No mandatory change review.
- **Recommendation**: Enable CloudFormation drift detection. Add branch protection rules.
- **Evidence**: `../MonoToMicroAssets/MonoToMicroCF.yaml`, `../.github/workflows/cfn-security.yml`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK
- **Finding**: No application CI/CD pipeline. cfn-nag only. Application built on EC2 during cfn-init. No contract testing.
- **Gap**: No automated build, test, or breaking-change detection.
- **Recommendation**: Create GitHub Actions CI pipeline with build, test, and API contract validation.
- **Evidence**: `../.github/workflows/cfn-security.yml`, `../MonoToMicroAssets/MonoToMicroCF.yaml`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK
- **Finding**: Single EC2 deployment via cfn-init. No blue/green, no canary, no CodeDeploy. Rollback requires full stack redeployment.
- **Gap**: No fast rollback capability.
- **Recommendation**: Implement blue/green deployment with CodeDeploy or ALB-based rolling updates.
- **Evidence**: `../MonoToMicroAssets/MonoToMicroCF.yaml`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK
- **Finding**: Zero test files. `spring-boot-starter-test` dependency present but no `src/test/` directory. No test suites.
- **Gap**: Zero automated test coverage.
- **Recommendation**: Create unit tests, integration tests, and API contract tests targeting 80% endpoint coverage.
- **Evidence**: `build.gradle`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: RISK
- **Finding**: RDS cluster has no `StorageEncrypted: true`. S3 buckets have no encryption config. No EBS encryption.
- **Gap**: All data at rest is unencrypted.
- **Recommendation**: Add `StorageEncrypted: true` to RDS. Add `BucketEncryption` to S3 buckets. Enable account EBS encryption.
- **Evidence**: `../MonoToMicroAssets/MonoToMicroCF.yaml`

#### ENG-Q6: Cross-Origin and Network Policies
- **Severity**: BLOCKER
- **Finding**: Permissive CORS in `MVCConfig.java` (all methods, all paths). `Application.java` ignores all OPTIONS with "not recommended for production" comment. Security groups allow inbound 80/443 from 0.0.0.0/0. No WAF.
- **Gap**: Any origin can call any endpoint. No network access restrictions.
- **Recommendation**: Restrict CORS origins. Deploy API Gateway with WAF. Restrict security group inbound to API Gateway only.
- **Evidence**: `src/main/java/com/monoToMicro/config/MVCConfig.java`, `src/main/java/com/monoToMicro/Application.java`, `../MonoToMicroAssets/MonoToMicroCF.yaml`

---

## Evidence Index

### Infrastructure as Code
| File | Questions Referenced |
|------|---------------------|
| `../MonoToMicroAssets/MonoToMicroCF.yaml` | AUTH-Q1, AUTH-Q2, AUTH-Q6, AUTH-Q7, AUTH-Q8, STATE-Q5, STATE-Q7, HITL-Q3, DATA-Q1, DATA-Q2, DATA-Q4, DISC-Q4, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q5, ENG-Q6, API-Q8, API-Q9 |

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `src/main/java/com/monoToMicro/rest/controller/UnicornController.java` | API-Q1, API-Q2, API-Q3, API-Q5, API-Q9, AUTH-Q1, DATA-Q3, DATA-Q6 |
| `src/main/java/com/monoToMicro/rest/controller/BasketController.java` | API-Q1, API-Q3, API-Q4, API-Q7, AUTH-Q3, AUTH-Q7, STATE-Q2, STATE-Q6, HITL-Q1, HITL-Q2, OBS-Q3 |
| `src/main/java/com/monoToMicro/rest/controller/UserController.java` | API-Q1, API-Q5, AUTH-Q3 |
| `src/main/java/com/monoToMicro/rest/controller/HealthController.java` | API-Q1, DATA-Q7, OBS-Q1 |
| `src/main/java/com/monoToMicro/rest/controller/DataReplicationController.java` | API-Q1, API-Q3, API-Q7 |
| `src/main/java/com/monoToMicro/security/ResourceServerConfig.java` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q8 |
| `src/main/java/com/monoToMicro/Application.java` | AUTH-Q5, ENG-Q6 |
| `src/main/java/com/monoToMicro/config/MVCConfig.java` | ENG-Q6 |
| `src/main/java/com/monoToMicro/core/repository/UnicornRepositoryImpl.java` | API-Q3, STATE-Q1, STATE-Q4, DATA-Q7 |
| `src/main/java/com/monoToMicro/core/repository/UserRepositoryImpl.java` | STATE-Q3, DATA-Q7 |
| `src/main/java/com/monoToMicro/core/services/UnicornServiceImpl.java` | STATE-Q1, API-Q8 |
| `src/main/java/com/monoToMicro/core/services/UserServiceImpl.java` | API-Q4, DATA-Q5 |
| `src/main/java/com/monoToMicro/core/model/CoreModel.java` | API-Q6, DATA-Q5 |
| `src/main/java/com/monoToMicro/core/model/Unicorn.java` | API-Q6, DISC-Q2 |
| `src/main/java/com/monoToMicro/core/model/User.java` | DATA-Q1, DISC-Q2 |
| `src/main/java/com/monoToMicro/core/events/EventContext.java` | HITL-Q1 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `../.github/workflows/cfn-security.yml` | ENG-Q1, ENG-Q2 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `build.gradle` | AUTH-Q1, AUTH-Q4, API-Q2, API-Q10, DISC-Q1, OBS-Q1, OBS-Q2, OBS-Q3, ENG-Q4 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `src/main/resources/application.properties` | AUTH-Q6, STATE-Q4, DATA-Q2, DATA-Q5, HITL-Q3 |
| `src/main/resources/com/monoToMicro/core/repository/mappers/UnicornMapper.xml` | API-Q4, STATE-Q1, STATE-Q6, DATA-Q3, DATA-Q8, API-Q10 |
| `src/main/resources/com/monoToMicro/core/repository/mappers/UserMapper.xml` | API-Q4, DATA-Q5 |
| `database/create_tables.sql` | STATE-Q3, DATA-Q1, DATA-Q2, DATA-Q4, DATA-Q5, DATA-Q8, DISC-Q1, DISC-Q2, DISC-Q3, DISC-Q4 |
