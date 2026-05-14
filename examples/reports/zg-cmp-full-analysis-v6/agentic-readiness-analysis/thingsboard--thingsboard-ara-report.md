# Agentic Readiness Analysis Report

**Target**: /Users/lucasdu/Documents/AWS-MAC/2026-projects/sample-agentic-readiness-analysis/services/thingsboard--thingsboard
**Date**: 2025-05-08
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**Repository Type**: application
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: java, iot, platform
**Context**: Open-source IoT platform for device management, data collection, and visualization.
**Archetype Justification**: The platform owns persistent state in PostgreSQL/Cassandra, exposes CRUD operations on business entities (devices, assets, customers, dashboards, alarms), manages entity lifecycle, and stores user-specific multi-tenant data.

- **Surface flags**:
  - has_persistent_data_store: true
  - has_http_rpc_surface: true
  - has_auth_surface: true
  - has_write_operations: true
  - has_logging_of_user_data: true

---

## Readiness Profile: Pilot-Ready (Safety Concerns)

**BLOCKERs**: 1 | **RISK-SAFETY**: 5 | **RISK-QUALITY**: 10 | **INFOs**: 11

Remediation Required — Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days.

### Classification Rationale

This repository has 1 BLOCKER finding (AUTH-Q1: Machine Identity Authentication), 5 RISK-SAFETY findings, and 10 RISK-QUALITY findings. The presence of 1 BLOCKER triggers the "Remediation Required" profile per the classification rule "1-2 High → Remediation Required." The BLOCKER must be resolved before any agent deployment, including supervised pilots.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 1 |
| RISK-SAFETY | 5 |
| RISK-QUALITY | 10 |
| INFO | 11 |
| N/A | 0 |
| Not Evaluated (extended) | 16 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 3
**Extended Questions Not Triggered**: 16
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: stateful-crud (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: ThingsBoard supports JWT-based authentication (username/password login producing a bearer token) and API key authentication via Personal Access Tokens (PATs) with `X-Authorization: ApiKey <token>` header. However, these PATs are tied to human user accounts — there is no dedicated machine identity or service account mechanism that distinguishes agent callers from human users in audit logs. The JWT `sub` claim carries the user's email address, and the `userId` claim identifies the user UUID. There is no separate `agent_id`, `client_id`, or machine-identity field.
- **Gap**: No dedicated machine identity authentication mechanism exists that allows an agent to authenticate as a distinct principal (separate from a human user). PATs inherit the human user's identity and permissions. Audit logs cannot distinguish whether an action was performed by a human or an agent using the same PAT.
- **Remediation**:
  - **Immediate**: Create a dedicated "service account" user type (distinct from SYS_ADMIN/TENANT_ADMIN/CUSTOMER_USER) with a machine-identity flag that appears in audit log entries. Alternatively, extend the PAT mechanism to include an `agent_name` or `client_id` field that is persisted in audit logs alongside the user identity.
  - **Target State**: Agent callers authenticate with a distinct identity that is separately attributable in audit logs, separately revocable, and can have independent permission scopes.
  - **Estimated Effort**: Medium
  - **Dependencies**: AUTH-Q6 (audit logging attribution depends on identity), AUTH-Q7 (suspension depends on distinct identity)
- **Evidence**: `application/src/main/java/org/thingsboard/server/service/security/model/token/JwtTokenFactory.java`, `application/src/main/java/org/thingsboard/server/config/ThingsboardSecurityConfiguration.java`, `common/data/src/main/java/org/thingsboard/server/common/data/security/Authority.java`

---

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: ThingsBoard has a three-tier RBAC model (SYS_ADMIN > TENANT_ADMIN > CUSTOMER_USER) with resource-level and operation-level checks. However, the permission model is coarse-grained at the role level — a TENANT_ADMIN has full access to all entity types within the tenant, and a CUSTOMER_USER has access to all entities assigned to their customer. There is no mechanism to grant an agent read-only access to only specific resource types (e.g., read devices but not customers) within the same role tier.
- **Gap**: No fine-grained permission scoping below the three fixed authority levels. An agent operating as TENANT_ADMIN inherits full CRUD on all tenant resources — it cannot be restricted to only read devices or only manage alarms.
- **Compensating Controls**:
  - Create a dedicated CUSTOMER_USER account for the agent with only the specific entities assigned to it (leveraging customer-level isolation)
  - Implement an API gateway or proxy layer in front of ThingsBoard that restricts which endpoints the agent can call
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Introduce a custom permission system or API key scope mechanism that allows per-resource-type and per-operation permission grants for agent identities.
- **Evidence**: `application/src/main/java/org/thingsboard/server/service/security/permission/DefaultAccessControlService.java`, `application/src/main/java/org/thingsboard/server/service/security/permission/TenantAdminPermissions.java`

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The permission model does support action-level authorization via the `Operation` enum (CREATE, READ, UPDATE, DELETE, WRITE_ATTRIBUTES, READ_ATTRIBUTES, READ_TELEMETRY, etc.) checked against `Resource` types. Each authority role (SysAdmin, TenantAdmin, CustomerUser) has a permission matrix mapping (Resource, Operation) → allowed/denied. However, these are hardcoded per authority level and not configurable per user or per agent identity.
- **Gap**: Action-level authorization exists but is not configurable per agent identity. A TENANT_ADMIN can always read AND delete within the same resource type — you cannot create a TENANT_ADMIN that can read devices but not delete them.
- **Compensating Controls**:
  - Use CUSTOMER_USER role for agents (which has a more restrictive permission set by default)
  - Implement API gateway path-based restrictions to block DELETE methods for agent traffic
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Make the permission matrix configurable per user/service account, allowing per-identity (Resource, Operation) overrides beyond the fixed role-based defaults.
- **Evidence**: `application/src/main/java/org/thingsboard/server/service/security/permission/DefaultAccessControlService.java`, `application/src/main/java/org/thingsboard/server/service/security/permission/CustomerUserPermissions.java`

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: User accounts can be disabled via the `enabled` field on `UserCredentials`, and user sessions can be invalidated via `UserSessionInvalidationEvent`. However, there is no rapid, API-driven mechanism to suspend a single agent identity (PAT) independently without disabling the entire user account it belongs to. PAT revocation would require deleting the token from the database, which is not exposed as a first-class admin API operation separate from user management.
- **Gap**: No independent, rapid agent identity suspension mechanism. Revoking agent access requires disabling the underlying user account or manually removing the PAT from the database.
- **Compensating Controls**:
  - Create a dedicated user account per agent so that disabling the user account effectively suspends only that agent
  - Implement a short JWT token expiry (reduce from 2.5 hours) to limit the window of exposure
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Expose a first-class API endpoint for immediate PAT revocation (e.g., `DELETE /api/auth/pat/{id}`) that takes effect within seconds, independently of user account lifecycle.
- **Evidence**: `common/data/src/main/java/org/thingsboard/server/common/data/security/UserCredentials.java`, `application/src/main/java/org/thingsboard/server/controller/AuthController.java`

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Rate limiting is implemented via `RateLimitProcessingFilter` with per-tenant and per-customer REST request limits defined in Tenant Profiles (database-driven, configurable). However, system administrators (SYS_ADMIN) are explicitly exempt from rate limiting. The rate limit values are configured per tenant profile, not per individual identity, meaning all agents within the same tenant share the same rate limit pool.
- **Gap**: SYS_ADMIN exemption from rate limiting creates risk if an agent operates at the SYS_ADMIN level. No per-agent-identity rate limiting exists — a runaway agent loop shares the tenant's rate limit pool with all other users, potentially starving human users.
- **Compensating Controls**:
  - Never grant agents SYS_ADMIN authority — always use TENANT_ADMIN or CUSTOMER_USER (which are rate-limited)
  - Implement an external API gateway (e.g., AWS API Gateway with usage plans) in front of ThingsBoard to enforce per-agent rate limits
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add per-identity (per-PAT or per-user) rate limiting configuration, separate from per-tenant limits. Remove or limit the SYS_ADMIN exemption.
- **Evidence**: `application/src/main/java/org/thingsboard/server/config/RateLimitProcessingFilter.java`, `application/src/main/resources/thingsboard.yml`

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The logback configuration uses plain-text log format (`%d{ISO8601} [%thread] %-5level %logger{36} - %msg%n`) with no PII scrubbing or masking. The application logs request processing that may include user emails, device names, and tenant identifiers. Audit logs store full action data (including `actionData` as JSON) in PostgreSQL. While audit logs are access-controlled, application-level logs (file-based) contain no PII filtering.
- **Gap**: No log scrubbing or PII masking middleware exists in the logging pipeline. User emails, device credentials, and entity identifiers may appear in application logs without redaction.
- **Compensating Controls**:
  - Restrict access to log files at the OS/infrastructure level
  - Implement a log aggregation pipeline with PII scrubbing (e.g., CloudWatch Logs with data masking)
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a custom logback encoder or filter that masks known PII patterns (emails, phone numbers, token values) before writing to log appenders. Consider switching to structured JSON logging with an explicit allowlist of fields.
- **Evidence**: `docker/tb-node/conf/logback.xml`, `application/src/main/resources/thingsboard.yml` (audit-log section)

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: ThingsBoard generates an OpenAPI 3.1 specification programmatically via SpringDoc/Swagger annotations in `SwaggerConfiguration.java`. The spec is available at runtime when `springdoc.api-docs.enabled=true` (via `/v3/api-docs`). However, no static OpenAPI spec file is committed to the repository — the spec can only be obtained from a running instance.
- **Gap**: No static, version-controlled OpenAPI specification file exists in the repository. The spec is only available from a running instance, making it difficult for agent tool generation pipelines to consume without first deploying the application.
- **Compensating Controls**:
  - Generate the spec during CI/CD and publish it as a build artifact
  - Use the `thingsboard-openapi.properties` profile to generate and export the spec during development
- **Remediation Timeline**: 30 days
- **Recommendation**: Add a CI step that generates the OpenAPI spec (using the `openapi` Spring profile) and commits it as a static file (e.g., `openapi.json`) in the repository.
- **Evidence**: `application/src/main/java/org/thingsboard/server/config/SwaggerConfiguration.java`, `application/src/main/resources/thingsboard-openapi.properties`

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: ThingsBoard implements a consistent structured error response via `ThingsboardErrorResponse` with fields: `message`, `errorCode` (numeric), `status` (HTTP code), and `timestamp`. The `ThingsboardErrorCode` enum provides typed error codes (GENERAL=2, AUTHENTICATION=10, JWT_TOKEN_EXPIRED=11, PERMISSION_DENIED=20, BAD_REQUEST_PARAMS=31, ITEM_NOT_FOUND=32, TOO_MANY_REQUESTS=33, etc.). However, there is no `retryable` boolean or retry-category field in the error response — agents must infer retryability from the error code or HTTP status.
- **Gap**: Error responses lack an explicit `retryable` field or retry-category indicator. Agents must hardcode knowledge of which error codes are retriable (429, 503) vs terminal (401, 403, 404).
- **Compensating Controls**:
  - Document retry semantics per error code in the API specification
  - Implement retry logic in the agent tool layer based on HTTP status codes (429 → retry with backoff, 4xx → terminal, 5xx → retry)
- **Remediation Timeline**: 30 days
- **Recommendation**: Add a `retryable` boolean field to `ThingsboardErrorResponse` and populate it based on error code classification.
- **Evidence**: `application/src/main/java/org/thingsboard/server/exception/ThingsboardErrorResponse.java`, `application/src/main/java/org/thingsboard/server/exception/ThingsboardErrorResponseHandler.java`

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The management API uses an unversioned `/api/` prefix with no version path segment. Only the device transport API is versioned at `/api/v1/`. There is no breaking change detection in CI, no consumer-driven contract tests (Pact), and no OpenAPI diff tooling configured. Database migrations use a custom service (not Flyway/Liquibase) with SQL upgrade scripts, but API schema evolution is not tracked.
- **Gap**: No API versioning strategy for the management API. No breaking change detection in the CI pipeline. Agent tool bindings could break silently when the platform is upgraded.
- **Compensating Controls**:
  - Pin agent deployments to specific ThingsBoard versions
  - Monitor the ThingsBoard changelog for breaking changes before upgrading
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Introduce API version prefixes (e.g., `/api/v1/`) for the management API and add OpenAPI diff checks in CI to detect breaking changes before release.
- **Evidence**: `application/src/main/java/org/thingsboard/server/controller/BaseController.java`, `common/transport/http/src/main/java/org/thingsboard/server/transport/http/DeviceApiController.java`

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: ThingsBoard has no OpenTelemetry integration, no distributed tracing library (Zipkin, Jaeger), and no correlation ID / X-Request-Id header propagation. The logging format is plain text without MDC tenant/user context. Prometheus metrics are exposed via Spring Actuator (`/actuator/prometheus`), but there is no request-level tracing across the microservices architecture.
- **Gap**: No distributed tracing or correlation ID propagation. Agent-initiated requests that traverse multiple services (tb-core → tb-rule-engine → tb-transport) cannot be traced end-to-end. Debugging agent-initiated failures requires manual log correlation.
- **Compensating Controls**:
  - Use the audit log system (which captures userId per action) as a partial substitute for request-level tracing
  - Implement request correlation at the API gateway/load balancer level (HAProxy can inject unique request IDs)
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Integrate OpenTelemetry Java agent or SDK for distributed tracing with trace ID propagation. Add MDC context (tenantId, userId, requestId) to the logback pattern.
- **Evidence**: `docker/tb-node/conf/logback.xml`, `pom.xml` (no OpenTelemetry dependency), `docker/monitoring/prometheus/prometheus.yml`

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Prometheus metrics are collected via Spring Actuator with pre-provisioned Grafana dashboards for transport metrics, rule engine latency, DB metrics, and connection monitoring. A dedicated `ThingsboardMonitoringApplication` performs active health checks on all transports with configurable failure thresholds. However, no alerting rules (Prometheus AlertManager, CloudWatch Alarms, PagerDuty integration) are configured in the repository for error rate or latency SLO violations.
- **Gap**: Metrics collection and dashboards exist but no automated alerting rules are defined. Degradation affecting agent consumers would not trigger proactive notifications.
- **Compensating Controls**:
  - Configure Prometheus AlertManager rules in the monitoring stack
  - Use the monitoring service's Slack webhook notifications as a basic alerting mechanism
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Define Prometheus alerting rules for API error rates (>5% 5xx), P99 latency thresholds, and transport health check failures. Configure AlertManager with notification channels.
- **Evidence**: `docker/docker-compose.prometheus-grafana.yml`, `docker/monitoring/prometheus/prometheus.yml`, `monitoring/src/main/resources/tb-monitoring.yml`

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No Infrastructure as Code (Terraform, CloudFormation, CDK, Helm, Kustomize) exists in the repository. Deployment is defined via Docker Compose files and OS packaging scripts (deb/rpm via Gradle). There is no drift detection, no PR-based review for infrastructure changes, and no declarative definition of the API gateway, IAM roles, or network configuration.
- **Gap**: The entire infrastructure surface is defined imperatively via Docker Compose and manual configuration. No IaC governance, no drift detection, no peer-review-enforced infrastructure changes.
- **Compensating Controls**:
  - Manage Docker Compose files in version control with required PR reviews
  - Implement a wrapper IaC layer (e.g., Terraform for cloud deployments) around the Docker Compose definitions
- **Remediation Timeline**: 90–180 days
- **Recommendation**: Define the deployment infrastructure (load balancer, network, secrets, service definitions) in a declarative IaC tool (Terraform, CDK, or Helm) with CI-enforced plan review and drift detection.
- **Evidence**: `docker/docker-compose.yml`, `docker/` (17+ compose files), absence of any `.tf`, `template.yaml`, or `Chart.yaml` files

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The repository has three GitHub Actions workflows: ATX transformation, license header formatting, and configuration file validation. None of these execute automated tests, build the application, or perform API contract testing. The 867 test files exist but are never run in CI.
- **Gap**: No CI/CD pipeline runs automated tests or detects API contract changes. Breaking API changes could reach production without any automated detection.
- **Compensating Controls**:
  - Run tests locally before releases
  - Implement a basic CI workflow that at minimum compiles the project and runs unit tests
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a GitHub Actions workflow that runs `mvn verify` on pull requests, including API controller tests. Add OpenAPI spec diff detection.
- **Evidence**: `.github/workflows/atx-transform.yml`, `.github/workflows/license-header-format.yml`, `.github/workflows/check-configuration-files.yml`

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No rollback mechanism is defined in the repository. Docker Compose deployments rely on manual image tag management. No blue/green, canary, or automated rollback configuration exists. The database migration system is forward-only (custom SQL upgrade scripts with no down-migration support).
- **Gap**: No automated or documented rollback procedure. A broken deployment affecting agent-facing APIs requires manual intervention to restore the previous version. Database migrations are irreversible.
- **Compensating Controls**:
  - Pin Docker image tags to specific versions and maintain a runbook for manual rollback
  - Take database snapshots before upgrades
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement a deployment strategy with automated rollback (e.g., Docker Compose with versioned image tags + a rollback script, or migrate to Kubernetes with Helm rollback). Add reversible migration support.
- **Evidence**: `docker/docker-compose.yml`, `docker/.env` (TB_VERSION variable), `application/src/main/java/org/thingsboard/server/service/install/update/DefaultDataUpdateService.java`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No encryption at rest configuration is defined in the repository. PostgreSQL, Cassandra, and Redis/Valkey data stores are configured without encryption at rest settings. No KMS key references, no transparent data encryption (TDE) configuration, and no encrypted volume definitions exist in the Docker Compose files.
- **Gap**: Data at rest (including device credentials, user data, telemetry) is not encrypted at the application or infrastructure layer as defined in this repository.
- **Compensating Controls**:
  - Enable encryption at rest at the infrastructure layer (encrypted EBS volumes, RDS encryption, managed Cassandra encryption)
  - Use encrypted Docker volumes or encrypted file systems
- **Remediation Timeline**: 30–60 days
- **Recommendation**: When deploying to cloud infrastructure, enable encryption at rest on all data stores (RDS with KMS, encrypted EBS, Cassandra with TDE). Document the encryption configuration in IaC.
- **Evidence**: `application/src/main/resources/thingsboard.yml` (database configuration sections), `docker/docker-compose.yml`

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Docker Compose files provide a local development/testing environment with the full microservices stack. The `msa/black-box-tests/` directory uses `DockerComposeExecutor` to spin up complete test environments. However, there is no named "staging" or "sandbox" environment configuration, no synthetic data generators for production-equivalent testing, and no documented procedure for creating an isolated agent testing environment.
- **Gap**: No dedicated sandbox/staging environment definition. The Docker Compose setup serves as a development environment but is not framed as a production-equivalent staging for agent testing.
- **Compensating Controls**:
  - Use the existing Docker Compose setup as a local sandbox for agent testing
  - Create a separate Docker Compose profile (e.g., `docker-compose.staging.yml`) with seed data for agent testing
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a named staging environment configuration with seed data scripts that populate representative IoT entities (devices, assets, customers, dashboards) for agent testing.
- **Evidence**: `docker/docker-compose.yml`, `msa/black-box-tests/`

---

## INFOs — Architecture and Design Inputs

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No idempotency key mechanism exists for write endpoints. POST operations (e.g., creating devices, assets, customers) do not support idempotency keys. Token-based operations (activation, password reset) are inherently single-use.
- **Implication**: If agent scope expands to write-enabled in the future, non-idempotent write endpoints will risk duplicate resource creation on retries.
- **Recommendation**: Plan to implement idempotency key support (e.g., `X-Idempotency-Key` header) for POST endpoints before expanding agent scope to write operations.
- **Evidence**: Absence of any idempotency mechanism in controllers and filters.

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO (originally RISK-SAFETY for read-only scope, but downgraded further: read-only agents do not execute multi-step write workflows)
- **Finding**: No explicit saga pattern, compensating transaction, or undo endpoints exist. The rule engine processes multi-step workflows but has no built-in rollback mechanism for partially completed sequences. Step Functions or similar orchestration with error-handling rollback is not used.
- **Implication**: If agent scope expands to write-enabled multi-step workflows, partial failures would leave the system in inconsistent states.
- **Recommendation**: Before enabling write-enabled agent scope, implement compensation logic or saga patterns for critical multi-step operations (e.g., device provisioning workflows).
- **Evidence**: Absence of saga/compensation patterns in `rule-engine/` and `application/` source code.

### AUTH-Q5: Credential Management

- **Severity**: INFO
- **Finding**: All credentials are externalized via environment variables with the `${ENV_VAR:default}` pattern. The JWT signing key is persisted in the database (auto-generated on fresh install). However, no integration with a dedicated secrets management system (AWS Secrets Manager, HashiCorp Vault) exists. Default development values are present in `thingsboard.yml` (e.g., `thingsboardDefaultSigningKey`, `postgres` for DB password).
- **Implication**: In production deployments, credentials must be managed externally. The default values in YAML pose a risk if environment variables are not properly set. No automated credential rotation exists.
- **Recommendation**: Integrate with a secrets management system (AWS Secrets Manager or HashiCorp Vault) for production deployments. Remove default credential values from configuration files or mark them clearly as development-only.
- **Evidence**: `application/src/main/resources/thingsboard.yml` (JWT and datasource sections)

### AUTH-Q6: Immutable Audit Logging ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY per conditional rules, but the audit log system captures authenticated principal (userId + userName) for all write operations with configurable per-entity-type granularity. The logs are stored in PostgreSQL with partitioning but without immutability guarantees (no write-once storage, no tamper-evident hash chain). External Elasticsearch sink is available.
- **Finding**: Audit logging captures the authenticated principal (userId, userName) for all logged actions. 37 action types are tracked. Logging level is configurable per entity type (OFF/W/RW). Logs are stored in PostgreSQL with weekly partitioning and configurable TTL. An Elasticsearch external sink is available. However, logs are not immutable — they reside in a standard PostgreSQL table without write-once storage or tamper-evident mechanisms.
- **Implication**: Audit logs exist and capture identity but could theoretically be modified by a database admin. For compliance-sensitive deployments, immutable log storage (S3 with object lock, CloudTrail) would be required.
- **Recommendation**: For production deployments, configure the Elasticsearch audit sink with write-once index lifecycle policies, or replicate audit logs to immutable storage (S3 with Object Lock, CloudWatch Logs with retention policies).
- **Evidence**: `application/src/main/resources/thingsboard.yml` (audit-log section), `dao/src/main/java/org/thingsboard/server/dao/audit/AuditLogServiceImpl.java`, `common/data/src/main/java/org/thingsboard/server/common/data/audit/ActionType.java`

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: INFO
- **Finding**: JWT tokens carry full user context (userId, tenantId, customerId, authority scopes) propagated through the request lifecycle. The multi-tenant architecture enforces tenant isolation at the DAO layer via `HasTenantId` checks. However, there is no OAuth2 on-behalf-of flow or token exchange mechanism to distinguish between an agent acting under its own identity vs. acting on behalf of a specific user.
- **Implication**: Agents operating on behalf of users cannot have their actions bounded by that user's permissions — the agent always operates with its own fixed permission set.
- **Recommendation**: Consider implementing a token exchange or delegation mechanism if agent-on-behalf-of-user workflows are planned.
- **Evidence**: `application/src/main/java/org/thingsboard/server/service/security/model/token/JwtTokenFactory.java`, `application/src/main/java/org/thingsboard/server/service/security/permission/DefaultAccessControlService.java`

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The platform uses optimistic locking via `version` fields on entities (visible in User, Device, and other entity classes). The audit log system tracks `VERSION_CONFLICT` as an error code. DynamoDB-style conditional writes are not applicable (PostgreSQL/Cassandra backend), but PostgreSQL row-level locking is available.
- **Implication**: Concurrency controls exist for write operations. Read-only agents are not affected. If scope expands to write-enabled, the version-based optimistic locking provides protection against concurrent modifications.
- **Recommendation**: No action required for read-only agent scope. If expanding to write-enabled, verify that all agent-facing write endpoints properly check and propagate version fields.
- **Evidence**: `common/data/src/main/java/org/thingsboard/server/common/data/User.java` (version field), `application/src/main/java/org/thingsboard/server/exception/ThingsboardErrorResponse.java` (VERSION_CONFLICT error code)

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits (max records per operation, max spend per session) exist. Rate limiting (per-tenant request count) is the only throttle. Bulk operations (e.g., bulk device provisioning) have no per-invocation size caps defined in the API.
- **Implication**: Read-only agents are not affected by lack of transaction limits. If scope expands to write-enabled, uncapped bulk operations could be exploited by a runaway agent.
- **Recommendation**: Before expanding to write-enabled scope, implement configurable per-operation limits (e.g., max entities per bulk create, max records per export).
- **Evidence**: `application/src/main/java/org/thingsboard/server/config/RateLimitProcessingFilter.java`, `application/src/main/resources/thingsboard.yml`

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: All REST API responses use JSON format (Spring Boot default serialization with Jackson). WebSocket communication also uses JSON. Internal inter-service communication uses Protocol Buffers (gRPC). The API produces `application/json` Content-Type.
- **Implication**: JSON responses are well-suited for LLM-based agent consumption. No adaptation layer is needed for format translation.
- **Recommendation**: No action required. JSON is the optimal format for agent tool integration.
- **Evidence**: `application/src/main/java/org/thingsboard/server/config/SwaggerConfiguration.java`, `common/proto/src/main/proto/queue.proto`

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: Rate limiting is enforced (per-tenant via Tenant Profiles) and returns HTTP 429 with `ThingsboardErrorCode.TOO_MANY_REQUESTS` (code 33). However, the response does not include standard rate limit headers (`X-RateLimit-Remaining`, `X-RateLimit-Limit`, `Retry-After`). Rate limit configuration values are stored in the database (Tenant Profiles), not documented in the API spec.
- **Implication**: Agents cannot proactively self-throttle because rate limit status is not communicated via headers. Agents must reactively handle 429 responses.
- **Recommendation**: Add standard rate limit headers to all API responses. Document rate limit defaults in the API specification.
- **Evidence**: `application/src/main/java/org/thingsboard/server/config/RateLimitProcessingFilter.java`, `application/src/main/java/org/thingsboard/server/exception/ThingsboardErrorResponseHandler.java`

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality scores, completeness metrics, or data profiling tools are integrated. Telemetry data has timestamps but no quality indicators. The platform stores whatever devices report without validation beyond type checking.
- **Implication**: Agents consuming telemetry data cannot assess data quality or completeness without additional tooling.
- **Recommendation**: Consider adding data quality metadata (e.g., completeness score, last-known-good timestamp) for critical datasets that agents will consume.
- **Evidence**: `dao/src/main/resources/sql/schema-ts-psql.sql`, `dao/src/main/resources/sql/schema-entities.sql`

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: PASS (no finding)
- **Finding**: ThingsBoard exposes a comprehensive REST API via Spring Boot controllers with 50+ controller classes covering all platform operations. The API is documented via SpringDoc/OpenAPI 3.1 annotations. GraphQL is not used. Integration is through well-defined REST endpoints, not direct database access.
- **Gap**: None — a documented REST interface exists.
- **Recommendation**: N/A
- **Evidence**: `application/src/main/java/org/thingsboard/server/controller/` (56 controller classes), `application/src/main/java/org/thingsboard/server/config/SwaggerConfiguration.java`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: OpenAPI 3.1 specification is generated programmatically via SpringDoc but no static spec file is committed to the repository.
- **Gap**: No static, version-controlled OpenAPI specification file.
- **Recommendation**: Add a CI step to generate and commit the OpenAPI spec as a static file.
- **Evidence**: `application/src/main/java/org/thingsboard/server/config/SwaggerConfiguration.java`, `application/src/main/resources/thingsboard-openapi.properties`

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: Consistent `ThingsboardErrorResponse` with `message`, `errorCode`, `status`, `timestamp`. Missing explicit `retryable` indicator.
- **Gap**: No retryable boolean or retry-category field in error responses.
- **Recommendation**: Add a `retryable` field to the error response schema.
- **Evidence**: `application/src/main/java/org/thingsboard/server/exception/ThingsboardErrorResponse.java`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No idempotency key mechanism for write operations.
- **Gap**: Non-idempotent write endpoints.
- **Recommendation**: Implement idempotency key support before expanding to write-enabled scope.
- **Evidence**: Absence of idempotency patterns in codebase.

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: All REST APIs return JSON. Internal services use Protocol Buffers.
- **Gap**: None for agent integration.
- **Recommendation**: No action required.
- **Evidence**: `application/src/main/java/org/thingsboard/server/config/SwaggerConfiguration.java`

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has operations >30s OR long-running workflows
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: The rule engine internally processes entity state change events (ENTITY_CREATED, ENTITY_UPDATED, ENTITY_DELETED, ALARM_*, etc.) via TbMsg types. However, no external webhook registration or event subscription API is exposed to external consumers. Notifications are outbound-only (Slack, Teams, email).
- **Gap**: No external event subscription mechanism for agents to register for state change notifications.
- **Recommendation**: Consider exposing a webhook registration API or EventBridge integration for agent-driven event-reactive patterns.
- **Evidence**: `common/data/src/main/java/org/thingsboard/server/common/data/audit/ActionType.java` (TbMsgType mappings)

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: Rate limiting enforced via 429 responses but no standard rate limit headers included.
- **Gap**: No `X-RateLimit-Remaining`, `Retry-After` headers.
- **Recommendation**: Add standard rate limit headers.
- **Evidence**: `application/src/main/java/org/thingsboard/server/config/RateLimitProcessingFilter.java`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: JWT and PAT (Personal Access Token) authentication exists but tied to human user accounts with no distinct machine identity.
- **Gap**: No dedicated machine identity mechanism distinguishable from human users in audit logs.
- **Recommendation**: Implement a service account or machine identity type with separate attribution.
- **Evidence**: `application/src/main/java/org/thingsboard/server/service/security/model/token/JwtTokenFactory.java`, `common/data/src/main/java/org/thingsboard/server/common/data/security/Authority.java`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: Three-tier RBAC (SYS_ADMIN/TENANT_ADMIN/CUSTOMER_USER) with resource and operation checks, but no fine-grained per-identity permission customization.
- **Gap**: Cannot restrict an agent to only specific resource types within its role tier.
- **Recommendation**: Introduce configurable per-identity permission overrides.
- **Evidence**: `application/src/main/java/org/thingsboard/server/service/security/permission/DefaultAccessControlService.java`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: Operation enum (CREATE, READ, UPDATE, DELETE, etc.) checked per resource, but fixed per authority level — not configurable per identity.
- **Gap**: Cannot create a TENANT_ADMIN that can read but not delete devices.
- **Recommendation**: Make permission matrix configurable per user/service account.
- **Evidence**: `application/src/main/java/org/thingsboard/server/service/security/permission/DefaultAccessControlService.java`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: JWT carries full user context (tenantId, customerId, authority). No on-behalf-of flow or token exchange.
- **Gap**: No delegation mechanism for agent-on-behalf-of-user scenarios.
- **Recommendation**: Consider token exchange if delegation workflows are planned.
- **Evidence**: `application/src/main/java/org/thingsboard/server/service/security/model/token/JwtTokenFactory.java`

#### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: Credentials externalized via environment variables. No secrets management integration. Default values in YAML.
- **Gap**: No Vault/Secrets Manager integration; development defaults present.
- **Recommendation**: Integrate secrets management for production.
- **Evidence**: `application/src/main/resources/thingsboard.yml`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Audit logging captures userId/userName for all logged actions (37 action types). Stored in PostgreSQL with weekly partitioning. External Elasticsearch sink available. Logs are NOT immutable — standard PostgreSQL table without write-once guarantees.
- **Gap**: Audit logs are mutable (can be modified/deleted by database admin). No tamper-evident mechanism.
- **Recommendation**: Configure immutable storage for audit logs (Elasticsearch with write-once ILM, or replicate to S3 with Object Lock).
- **Evidence**: `dao/src/main/java/org/thingsboard/server/dao/audit/AuditLogServiceImpl.java`, `application/src/main/resources/thingsboard.yml`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: User accounts can be disabled and sessions invalidated. No rapid, independent PAT revocation API separate from user account management.
- **Gap**: No independent agent identity suspension mechanism.
- **Recommendation**: Expose a first-class PAT revocation API endpoint.
- **Evidence**: `common/data/src/main/java/org/thingsboard/server/common/data/security/UserCredentials.java`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No saga pattern or compensation logic. Rule engine has no built-in rollback.
- **Gap**: No compensation mechanism for multi-step operations.
- **Recommendation**: Implement before expanding to write-enabled agent scope.
- **Evidence**: Absence of saga/compensation patterns.

#### STATE-Q2: Queryable Current State
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Optimistic locking via version fields on entities. VERSION_CONFLICT error code exists.
- **Gap**: N/A for read-only scope.
- **Recommendation**: No action required for current scope.
- **Evidence**: `common/data/src/main/java/org/thingsboard/server/common/data/User.java`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has external dependencies (calls other services or external APIs)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: Per-tenant rate limiting exists via `RateLimitProcessingFilter` but SYS_ADMIN is exempt and no per-agent-identity limiting exists.
- **Gap**: SYS_ADMIN exemption; no per-identity rate limiting.
- **Recommendation**: Add per-identity rate limiting; remove SYS_ADMIN exemption.
- **Evidence**: `application/src/main/java/org/thingsboard/server/config/RateLimitProcessingFilter.java`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits for bulk operations.
- **Gap**: N/A for read-only scope.
- **Recommendation**: Implement before expanding to write-enabled scope.
- **Evidence**: `application/src/main/resources/thingsboard.yml`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: Docker Compose provides local development environment. Black-box tests use DockerComposeExecutor. No named staging environment or seed data for agent testing.
- **Gap**: No dedicated sandbox/staging for agent testing.
- **Recommendation**: Create a named staging configuration with representative seed data.
- **Evidence**: `docker/docker-compose.yml`, `msa/black-box-tests/`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: Stage A = Yes (system stores user emails, passwords, device credentials, tenant data). Stage B evaluation:
  - B1: `UserCredentials.password` field has no `@JsonIgnore` annotation — relies on service layer not serializing the entity. The controller layer returns `User` objects (which do not contain passwords) rather than `UserCredentials` directly. Device credentials are managed via separate endpoints with proper authorization. Under read-only scope → RISK-SAFETY.
  - B2: Three-tier RBAC differentiates access (SYS_ADMIN/TENANT_ADMIN/CUSTOMER_USER) with tenant isolation. However, within a tier, no differentiation between sensitive and non-sensitive data access exists. → RISK-SAFETY.
  - B3: No formal data classification metadata, no PII tagging, no Macie integration. → INFO.
  - Overall: RISK-SAFETY (B1 + B2 fire)
- **Finding**: The system stores sensitive data (user emails, hashed passwords, device credentials, access tokens). Password is separated into `UserCredentials` entity (not exposed via main User API), but lacks `@JsonIgnore` protection. No formal data classification or field-level access control differentiation exists.
- **Gap**: No field-level sensitivity annotations; `UserCredentials.password` relies on service-layer discipline rather than serialization-level protection; no differentiation of API scopes by data sensitivity.
- **Recommendation**: Add `@JsonIgnore` to `UserCredentials.password`. Implement OAuth scopes or API key permissions that separate access to sensitive operations (credential management) from general entity operations.
- **Evidence**: `common/data/src/main/java/org/thingsboard/server/common/data/security/UserCredentials.java`, `common/data/src/main/java/org/thingsboard/server/common/data/User.java`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY per rules. However, no GDPR, data residency, or sovereignty requirements are referenced anywhere in the codebase. The platform is region-agnostic (self-hosted).
- **Finding**: No data residency or sovereignty requirements are referenced in the codebase. The platform is designed for self-hosted deployment — data residency is determined by the deployment location, not the application code. No cross-region replication or data transfer mechanisms are built into the application.
- **Gap**: No data residency controls are needed at the application layer because deployment location determines residency. This is an operational concern, not a code concern.
- **Recommendation**: For production deployments, document the data residency implications of the chosen deployment region. If multi-region deployment is planned, add data residency tagging to tenant configuration.
- **Evidence**: Absence of GDPR/residency references in codebase. `application/src/main/resources/thingsboard.yml` (single-region database configuration)

#### DATA-Q3: Selective Query Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has list/query endpoints with potentially unbounded results
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q4: System of Record Designations
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: Plain-text logging with no PII masking. User emails and entity identifiers may appear in logs.
- **Gap**: No log scrubbing or PII masking.
- **Recommendation**: Implement log masking for PII patterns.
- **Evidence**: `docker/tb-node/conf/logback.xml`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics or completeness scores. Telemetry stored as-is from devices.
- **Gap**: No data quality awareness layer.
- **Recommendation**: Consider adding quality metadata for critical datasets.
- **Evidence**: `dao/src/main/resources/sql/schema-ts-psql.sql`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: Management API unversioned. No breaking change detection. No contract tests in CI.
- **Gap**: No API versioning or breaking change detection.
- **Recommendation**: Introduce API version prefixes and OpenAPI diff in CI.
- **Evidence**: Controller classes with unversioned `/api/` prefix.

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Field names are human-readable and semantically meaningful throughout the codebase (e.g., `deviceName`, `tenantId`, `customerId`, `createdTime`, `additionalInfo`). No legacy abbreviations or code-based identifiers found.
- **Implication**: LLM-based agents can interpret field names without requiring a data dictionary.
- **Recommendation**: No action required. The naming conventions are agent-friendly.
- **Evidence**: `common/data/src/main/java/org/thingsboard/server/common/data/Device.java`, `common/data/src/main/java/org/thingsboard/server/common/data/User.java`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No data catalog, metadata layer, or schema registry exists. Database schemas are defined in SQL files without semantic annotations. Entity relationships are documented through JPA annotations in code.
- **Implication**: Building agent tools against this system requires reading the code and API documentation rather than querying a metadata catalog.
- **Recommendation**: Consider generating a schema documentation artifact from the JPA entities and SQL schemas.
- **Evidence**: `dao/src/main/resources/sql/schema-entities.sql`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: No OpenTelemetry, no distributed tracing, no correlation IDs. Plain-text logging without MDC context.
- **Gap**: Cannot trace agent-initiated requests across services.
- **Recommendation**: Integrate OpenTelemetry and add MDC context to log patterns.
- **Evidence**: `docker/tb-node/conf/logback.xml`, `pom.xml`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: Prometheus metrics collected; Grafana dashboards provisioned. No alerting rules defined.
- **Gap**: No automated alerting on error rates or latency.
- **Recommendation**: Define Prometheus alerting rules for API error rates and latency.
- **Evidence**: `docker/docker-compose.prometheus-grafana.yml`, `docker/monitoring/prometheus/prometheus.yml`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: Prometheus metrics focus on infrastructure (request counts, latency, DB pool, transport connections). The monitoring service tracks transport health. Business outcome metrics (device onboarding success rate, alarm resolution time, rule engine effectiveness) are not published as custom metrics.
- **Implication**: When agents interact with the system, there are no business outcome metrics to measure whether agent actions produce good results.
- **Recommendation**: Define and publish custom metrics for key business outcomes relevant to agent interactions.
- **Evidence**: `docker/monitoring/prometheus/prometheus.yml`, Grafana dashboard definitions.

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK-QUALITY
- **Finding**: No IaC. Deployment via Docker Compose and OS packages.
- **Gap**: No declarative infrastructure governance.
- **Recommendation**: Define infrastructure in IaC with peer review and drift detection.
- **Evidence**: `docker/docker-compose.yml`, absence of IaC files.

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: CI workflows exist for config validation and license formatting only. No test execution or contract testing.
- **Gap**: No automated test execution or API contract testing in CI.
- **Recommendation**: Add CI workflow running `mvn verify` with API contract tests.
- **Evidence**: `.github/workflows/`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: No rollback mechanism defined. Forward-only database migrations.
- **Gap**: No automated rollback procedure.
- **Recommendation**: Implement deployment strategy with rollback capability.
- **Evidence**: `docker/docker-compose.yml`, `docker/.env`

#### ENG-Q4: API Test Coverage
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Always evaluated (but INFO for stateless-utility)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: RISK-QUALITY
- **Finding**: No encryption at rest configuration in the repository.
- **Gap**: Data at rest not encrypted at the application/infra layer.
- **Recommendation**: Enable encryption at rest on all data stores in production.
- **Evidence**: `application/src/main/resources/thingsboard.yml`, `docker/docker-compose.yml`

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `application/src/main/java/org/thingsboard/server/config/ThingsboardSecurityConfiguration.java` | AUTH-Q1, API-Q1 |
| `application/src/main/java/org/thingsboard/server/service/security/permission/DefaultAccessControlService.java` | AUTH-Q2, AUTH-Q3, AUTH-Q4 |
| `application/src/main/java/org/thingsboard/server/service/security/permission/TenantAdminPermissions.java` | AUTH-Q2 |
| `application/src/main/java/org/thingsboard/server/service/security/permission/CustomerUserPermissions.java` | AUTH-Q3 |
| `application/src/main/java/org/thingsboard/server/config/RateLimitProcessingFilter.java` | STATE-Q5, API-Q8, STATE-Q6 |
| `application/src/main/java/org/thingsboard/server/config/SwaggerConfiguration.java` | API-Q1, API-Q2, API-Q5 |
| `application/src/main/java/org/thingsboard/server/service/security/model/token/JwtTokenFactory.java` | AUTH-Q1, AUTH-Q4 |
| `application/src/main/java/org/thingsboard/server/controller/AuthController.java` | AUTH-Q1, AUTH-Q7 |
| `application/src/main/java/org/thingsboard/server/controller/BaseController.java` | API-Q3, DISC-Q1 |
| `application/src/main/java/org/thingsboard/server/exception/ThingsboardErrorResponse.java` | API-Q3, STATE-Q3 |
| `application/src/main/java/org/thingsboard/server/exception/ThingsboardErrorResponseHandler.java` | API-Q3, API-Q8 |
| `common/data/src/main/java/org/thingsboard/server/common/data/security/Authority.java` | AUTH-Q1 |
| `common/data/src/main/java/org/thingsboard/server/common/data/security/UserCredentials.java` | AUTH-Q7, DATA-Q1 |
| `common/data/src/main/java/org/thingsboard/server/common/data/User.java` | DATA-Q1, STATE-Q3, DISC-Q2 |
| `common/data/src/main/java/org/thingsboard/server/common/data/Device.java` | DISC-Q2 |
| `common/data/src/main/java/org/thingsboard/server/common/data/audit/ActionType.java` | AUTH-Q6, API-Q7 |
| `common/data/src/main/java/org/thingsboard/server/common/data/page/PageLink.java` | DATA-Q3 |
| `common/data/src/main/java/org/thingsboard/server/common/data/page/PageData.java` | DATA-Q3 |
| `dao/src/main/java/org/thingsboard/server/dao/audit/AuditLogServiceImpl.java` | AUTH-Q6 |
| `common/transport/http/src/main/java/org/thingsboard/server/transport/http/DeviceApiController.java` | DISC-Q1 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `application/src/main/resources/thingsboard-openapi.properties` | API-Q2 |
| `common/proto/src/main/proto/queue.proto` | API-Q5 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/atx-transform.yml` | ENG-Q2 |
| `.github/workflows/license-header-format.yml` | ENG-Q2 |
| `.github/workflows/check-configuration-files.yml` | ENG-Q2 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `docker/docker-compose.yml` | ENG-Q1, ENG-Q3, ENG-Q5, HITL-Q3 |
| `docker/docker-compose.prometheus-grafana.yml` | OBS-Q2 |
| `msa/black-box-tests/` | HITL-Q3, ENG-Q4 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `pom.xml` | OBS-Q1 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `application/src/main/resources/thingsboard.yml` | AUTH-Q5, AUTH-Q6, STATE-Q5, STATE-Q6, DATA-Q2, ENG-Q5 |
| `docker/tb-node/conf/logback.xml` | DATA-Q6, OBS-Q1 |
| `docker/monitoring/prometheus/prometheus.yml` | OBS-Q1, OBS-Q2, OBS-Q3 |

### Database Schemas
| File | Questions Referenced |
|------|---------------------|
| `dao/src/main/resources/sql/schema-entities.sql` | DATA-Q7, DISC-Q3 |
| `dao/src/main/resources/sql/schema-ts-psql.sql` | DATA-Q7 |
