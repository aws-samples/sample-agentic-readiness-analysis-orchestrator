# Agentic Readiness Assessment Report

**Target**: ThingsBoard IoT Platform (monorepo)
**Date**: 2026-04-30
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**TD Version**: unavailable (TD version ID could not be resolved at assessment time)
**Repository Type**: monorepo
**Service Archetype**: stateful-crud (auto-detected — dominant archetype for platform-wide assessment)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: java, iot, platform
**Context**: Open-source IoT platform for device management, data collection, and visualization.

**Archetype Justification**: ThingsBoard is a multi-service IoT platform. The dominant service (tb-core) manages persistent entities (devices, assets, users, dashboards, rule chains) with full CRUD operations backed by PostgreSQL/Cassandra. Secondary services include an orchestrator (tb-rule-engine), event processors (MQTT/HTTP/CoAP transports), and a data-gateway (edqs). Assessed as stateful-crud — the most conservative archetype — to ensure no extended questions are missed.

**Surface flags**:
- has_persistent_data_store: true
- has_http_rpc_surface: true
- has_auth_surface: true
- has_write_operations: true
- has_logging_of_user_data: true

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 1 | **RISK-SAFETY**: 6 | **RISK-QUALITY**: 13 | **INFOs**: 21

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days. The single BLOCKER (DATA-Q1: Sensitive Data Classification) must be resolved first. Once resolved, the 6 RISK-SAFETY findings would place the system at "Pilot-Ready (Safety Concerns)" — a supervised pilot with elevated safety oversight is possible once the BLOCKER is cleared.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 1 |
| RISK-SAFETY | 6 |
| RISK-QUALITY | 13 |
| INFO | 21 |
| N/A | 0 |
| Not Evaluated (extended) | 2 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 17
**Extended Questions Not Triggered**: 2
**Questions N/A (repo_type: monorepo)**: 0
**Service Archetype**: stateful-crud (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### DATA-Q1: Sensitive Data Classification — BLOCKER ⚡ (Tiered)

- **Severity**: BLOCKER
- **Stage A**: Yes — ThingsBoard stores tenant PII (email, names, phone), user auth credentials (separate `UserCredentials` entity with password hash), device credentials (access tokens, MQTT basic, X.509 certificates, LwM2M RPK), OAuth2 client secrets, and integration configs with embedded broker/HTTP endpoint credentials.
- **B1 — Agent-facing API response scoping: BLOCKER.**
  - **User endpoint: CLEAR.** `User` entity (`common/data/.../User.java`) does not carry the password field — password lives in a separate `UserCredentials` entity that is never serialized via `GET /api/user/{id}`.
  - **Device credentials endpoint: BLOCKER.** `DeviceController.getDeviceCredentialsByDeviceId()` (`application/src/main/java/org/thingsboard/server/controller/DeviceController.java:307-318`) returns the full `DeviceCredentials` entity (`common/data/.../DeviceCredentials.java`) with `credentialsId` and `credentialsValue` fields serialized **without `@JsonIgnore`**. A CUSTOMER_USER or TENANT_ADMIN calling `GET /api/device/{deviceId}/credentials` receives access tokens, MQTT passwords, X.509 PEM certificates, and LwM2M RPK credentials in plaintext. Service layer (`DefaultTbDeviceService.getDeviceCredentialsByDeviceId`) applies tenant isolation but does not mask the credentials themselves. A read-only agent with CUSTOMER_USER scope can iterate devices and exfiltrate every device's credentials.
- **B2 — Access control differentiation: CLEAR (with caveat).** Three-tier authority model (`SYS_ADMIN` / `TENANT_ADMIN` / `CUSTOMER_USER` — `common/data/.../security/Authority.java`) with `@PreAuthorize` enforcement on every endpoint and `checkDeviceId(deviceId, Operation.READ_CREDENTIALS)` verifying tenant-scope. Tenant isolation is strong. Caveat: CUSTOMER_USER retains `READ_CREDENTIALS` for devices assigned to their customer — there is no finer read-only / no-credentials split.
- **B3 — Formal classification metadata: INFO.** `DeviceCredentials` is separated from `Device` (good practice) and `UserCredentials` is separated from `User` (good practice) — structural classification exists, but no `@Sensitive`/`@Secret` annotations and no `@JsonIgnore` on `credentialsValue`.
- **Overall (read-only scope)**: B1 fires as BLOCKER — device credentials endpoint returns access tokens and certificates in plaintext to any CUSTOMER_USER. A read-only agent scoped to a customer can exfiltrate every device's authentication material. → **DATA-Q1 = BLOCKER**.
- **Gap**: Device credentials endpoint returns plaintext secrets. The structural separation of `DeviceCredentials` from `Device` is correct; the endpoint needs to either mask the value, return a reference-only shape, or be restricted to TENANT_ADMIN only (removing CUSTOMER_USER).
- **Remediation**:
  - **Immediate**: Apply `@JsonIgnore` to `credentialsValue` on `DeviceCredentials` and introduce a `DeviceCredentialsSummary` DTO that returns `credentialsType` only (no value). Gate any value-revealing endpoint behind TENANT_ADMIN + explicit "reveal" intent.
  - **Target State**: Device credentials are never returned in read responses; rotation and delivery of new credentials uses a secure out-of-band channel. Field-level encryption at rest (consider integration with a secrets manager).
  - **Estimated Effort**: Medium (2–4 weeks for DTO + endpoint gating).
  - **Dependencies**: Tenant isolation (B2) already in place; AUTH-Q6 audit logging should capture any credential-reveal call.
- **Evidence**: `application/src/main/java/org/thingsboard/server/controller/DeviceController.java:307-318`, `common/data/src/main/java/org/thingsboard/server/common/data/security/DeviceCredentials.java` (unmasked `credentialsValue`/`credentialsId`), `application/src/main/java/org/thingsboard/server/service/entitiy/device/DefaultTbDeviceService.java:173-181`, `common/data/src/main/java/org/thingsboard/server/common/data/security/Authority.java`, `common/data/src/main/java/org/thingsboard/server/common/data/User.java` (no password field — correctly isolated).

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: ThingsBoard implements a role-based permission system with three built-in roles: `SYS_ADMIN`, `TENANT_ADMIN`, and `CUSTOMER_USER` (see `SysAdminPermissions.java`, `TenantAdminPermissions.java`, `CustomerUserPermissions.java`). Controllers use `@PreAuthorize("hasAnyAuthority('SYS_ADMIN','TENANT_ADMIN','CUSTOMER_USER')")` annotations. The `Operation` enum provides fine-grained operations (READ, WRITE, DELETE, RPC_CALL, READ_CREDENTIALS, etc.) and `accessControlService.checkPermission()` enforces per-entity-type access. However, there is no mechanism for creating custom roles with narrower scopes (e.g., read-only access to devices but not dashboards). An agent identity authenticated via API key inherits the full permission set of the user role.
- **Gap**: No custom role or per-resource scoping mechanism exists to grant an agent identity only the specific permissions it needs. API keys inherit the full authority of the associated user role.
- **Compensating Controls**:
  - Create a dedicated `CUSTOMER_USER` with minimal entity assignments to scope down agent access
  - Use the tenant isolation boundary to limit agent access to a dedicated tenant
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement custom API key scoping that allows restricting an API key to specific entity types and operations independently of the user role.
- **Evidence**: `application/src/main/java/org/thingsboard/server/service/security/permission/Operation.java`, `application/src/main/java/org/thingsboard/server/service/security/permission/Resource.java`, `application/src/main/java/org/thingsboard/server/service/security/permission/CustomerUserPermissions.java`

#### AUTH-Q6: Immutable Audit Logging — RISK-SAFETY ⚡

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: ThingsBoard has a comprehensive audit logging system enabled by default (`audit-log.enabled: true` in `thingsboard.yml`). Audit logs capture write operations per entity type with configurable masks (device, asset, dashboard, user, rule_chain, alarm, etc. — all default to "W" for write logging). Audit logs are persisted to PostgreSQL with configurable partition sizes and TTL. An optional Elasticsearch sink is available for external forwarding. The `BaseController` logs entity actions with `logEntityAction()` capturing the authenticated principal. However, the audit logs are stored in the same database as application data — they are **not immutable or tamper-evident**. No object lock, write-once storage, or append-only mechanisms are configured. The TTL mechanism (`SQL_TTL_AUDIT_LOGS_SECS:0` disabled by default) could be used to delete audit records.
- **Gap**: Audit logs lack immutability guarantees. They are stored in the application database where an admin could modify or delete them. No tamper-evident logging mechanism (CloudTrail, S3 Object Lock, or write-once storage) is configured.
- **Compensating Controls**:
  - Enable the Elasticsearch audit sink with write-once index policies to create a tamper-resistant copy
  - Stream audit logs to an immutable external system (S3 with Object Lock, CloudWatch Logs with retention lock)
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure the Elasticsearch audit sink with immutable index policies or add a log shipping mechanism to S3 with Object Lock enabled.
- **Evidence**: `application/src/main/resources/thingsboard.yml` (lines 980–1021), `application/src/main/java/org/thingsboard/server/controller/BaseController.java`

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: ThingsBoard's audit logging system records entity action details including the authenticated principal and action metadata. The application uses SLF4J/Logback for general logging. The audit log configuration (`thingsboard.yml` lines 982–1021) logs write operations per entity type. However, no PII redaction or masking framework was found in the codebase. No log scrubbing middleware, PII masking libraries, or regex-based PII filters were identified. The `BaseController.handleException()` method logs error messages that may contain user context. The `transport.log.max_length` setting (1024 chars) limits transport message log size but does not filter PII.
- **Gap**: No PII redaction or masking mechanism exists for application logs or audit logs. User email addresses, device credentials in error messages, and tenant-specific data could appear in log output.
- **Compensating Controls**:
  - Configure log levels to minimize verbose logging of request/response bodies in production
  - Deploy a log filtering proxy (e.g., Fluentd with PII masking plugins) between the application and log storage
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement a PII masking Logback filter or structured logging framework that automatically redacts fields matching PII patterns (email, phone, credential tokens) before writing to log sinks.
- **Evidence**: `application/src/main/resources/thingsboard.yml` (lines 1165–1169), `application/src/main/java/org/thingsboard/server/controller/BaseController.java`

#### DATA-Q2: Data Residency and Sovereignty — RISK-SAFETY ⚡

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: ThingsBoard is a self-hosted platform where the deployment operator controls data residency. The database connection is configured via environment variables (`SPRING_DATASOURCE_URL` in `thingsboard.yml`). There are no hard-coded data residency constraints or cross-region replication settings in the codebase. No GDPR, LGPD, or data sovereignty compliance references were found in the configuration. The platform stores user PII, device telemetry, and business data that may be subject to residency requirements depending on the deployment context.
- **Gap**: No data residency controls are defined in the codebase. If an agent transmits IoT device data or user PII to an LLM provider in a different jurisdiction, compliance violations could occur. The platform relies entirely on deployment-time infrastructure decisions for residency compliance.
- **Compensating Controls**:
  - Document data residency requirements at the deployment level and restrict LLM provider endpoints to same-region services
  - Implement data classification (DATA-Q1) as a prerequisite to identify which data has residency constraints
- **Remediation Timeline**: 60–90 days (dependent on DATA-Q1 classification)
- **Recommendation**: Add data residency metadata to the platform's data model and create deployment-level guardrails that prevent agent APIs from exposing residency-controlled data to cross-region endpoints.
- **Evidence**: `application/src/main/resources/thingsboard.yml` (lines 943–951), `dao/src/main/resources/sql/schema-entities.sql`

### RISK-QUALITY — Address as Capacity Allows

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: ThingsBoard uses SLF4J/Logback for application logging. Spring Boot Actuator endpoints are configured (`management.endpoints.web.exposure.include: info` by default, can be changed to `prometheus`). Prometheus metrics scraping is configured for all services in `docker/monitoring/prometheus/prometheus.yml`. However, no OpenTelemetry SDK, X-Ray instrumentation, or `traceparent` header propagation was found. Logs are standard text format via Logback — no JSON structured logging was configured by default. No `request_id` or `correlation_id` fields were found in the logging configuration.
- **Gap**: No distributed tracing (OpenTelemetry/X-Ray) or structured JSON logging with correlation IDs is implemented. Agent-initiated requests cannot be traced end-to-end through the multi-service architecture.
- **Compensating Controls**:
  - Enable Spring Boot Actuator metrics with Prometheus to get basic request metrics
  - Add a custom logging filter that injects request IDs into the MDC (Mapped Diagnostic Context)
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Integrate OpenTelemetry Java agent or Micrometer Tracing with a trace collector. Configure Logback for JSON output with `traceId` and `spanId` fields.
- **Evidence**: `application/src/main/resources/thingsboard.yml` (lines 2160–2167), `docker/monitoring/prometheus/prometheus.yml`

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Prometheus and Grafana integration exists via `docker/docker-compose.prometheus-grafana.yml` and `docker/monitoring/prometheus/prometheus.yml`, which scrapes `/actuator/prometheus` from all services. However, no alert rules (Prometheus alert rules, Grafana alert definitions) were found in the repository. No PagerDuty/OpsGenie integration was configured. The monitoring setup provides metrics collection but not automated alerting.
- **Gap**: No alerting thresholds for error rates or latency are defined in the repository. Degradation of APIs that agents consume would not trigger automated alerts.
- **Compensating Controls**:
  - Use Grafana dashboards with manual monitoring until alert rules are defined
  - Define Prometheus alert rules for HTTP 5xx rates and p99 latency thresholds
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add Prometheus alerting rules for API error rates (>1% 5xx) and latency (p99 > 2s) with Alertmanager integration for PagerDuty/email notifications.
- **Evidence**: `docker/monitoring/prometheus/prometheus.yml`, `docker/docker-compose.prometheus-grafana.yml`

#### ENG-Q1: Infrastructure Governance — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: ThingsBoard's infrastructure is defined via Docker Compose files (`docker/docker-compose.yml` and variants). HAProxy load balancer configuration exists in `docker/haproxy/`. No Terraform, CloudFormation, CDK, or Kubernetes manifests with IaC governance were found. The Docker Compose files define the deployment topology but are not subject to automated plan review, drift detection, or peer review enforcement. GitHub Actions workflows exist for configuration file validation (`check-configuration-files.yml`) but not for infrastructure changes.
- **Gap**: No formal IaC governance (Terraform/CloudFormation) for the production deployment surface. Docker Compose provides repeatability but lacks drift detection, automated plan review, and peer review enforcement for infrastructure changes.
- **Compensating Controls**:
  - Use Git-based review (PR approval) for changes to Docker Compose files and HAProxy configs
  - Implement a Kubernetes-based deployment with GitOps (ArgoCD/Flux) for production environments
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Migrate production deployment definitions to Kubernetes with Helm charts or Terraform, adding drift detection and requiring PR approval for infrastructure changes.
- **Evidence**: `docker/docker-compose.yml`, `docker/haproxy/`, `.github/workflows/check-configuration-files.yml`

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: GitHub Actions workflows exist: `check-configuration-files.yml` validates YAML config changes, `license-header-format.yml` checks license headers. Extensive controller test classes exist (50+ test files in `application/src/test/java/.../controller/`). However, no API contract testing tools (Pact, OpenAPI spec validation, schema comparison) were found in the CI pipelines. The GitHub Actions workflows do not run the test suite or validate API contracts. The OpenAPI spec is auto-generated at runtime but not validated against a baseline in CI.
- **Gap**: No API contract testing in CI pipeline. Breaking API changes are not detected before production. The auto-generated OpenAPI spec is not compared against a baseline for backwards compatibility.
- **Compensating Controls**:
  - The extensive controller test suite provides some regression protection for API behavior
  - Manual code review of API-affecting PRs
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenAPI spec generation to CI and compare against a committed baseline using tools like `openapi-diff`. Consider adding Pact or Schemathesis for contract testing.
- **Evidence**: `.github/workflows/check-configuration-files.yml`, `application/src/test/java/org/thingsboard/server/controller/`

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: ThingsBoard uses Docker image versioning (`${DOCKER_REPO}/${TB_NODE_DOCKER_NAME}:${TB_VERSION}`) in Docker Compose for deployment. Database schema migrations exist in `application/src/main/data/upgrade/`. The Docker Compose setup supports rolling back to a previous image tag. However, no automated rollback triggers, blue/green deployment configurations, canary deployments, or feature flags were found. Database migrations are forward-only with no explicit rollback scripts.
- **Gap**: No automated rollback mechanism. Rollback requires manual Docker image tag change and restart. Database schema migrations are forward-only — rolling back a schema change requires manual intervention.
- **Compensating Controls**:
  - Pin Docker image versions and maintain a known-good version log for manual rollback
  - Take database snapshots before upgrades to enable point-in-time recovery
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement blue/green deployment with health-check-based automatic rollback. Add rollback scripts for each database migration. Consider Kubernetes with rolling update and automatic rollback on health check failure.
- **Evidence**: `docker/docker-compose.yml`, `docker/.env`

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Extensive API test coverage exists: 50+ controller test files in `application/src/test/java/.../controller/` including `DeviceControllerTest.java`, `AuthControllerTest.java`, `ApiKeyControllerTest.java`, `AlarmControllerTest.java`, etc. Black-box integration tests exist in `msa/black-box-tests/`. The `AbstractControllerTest.java` and `AbstractWebTest.java` provide test infrastructure for REST API testing. However, these tests are not explicitly executed in the GitHub Actions CI workflows found in the repository.
- **Gap**: While comprehensive API tests exist, they are not visibly executed in the CI pipeline defined in the repository's GitHub Actions workflows. Test execution may happen in an external CI system not represented in this repo.
- **Compensating Controls**:
  - The extensive test suite can be run locally or in an external CI system
  - Black-box tests in `msa/black-box-tests/` provide end-to-end coverage
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add a GitHub Actions workflow that runs the controller test suite and black-box tests on every PR targeting the main branch.
- **Evidence**: `application/src/test/java/org/thingsboard/server/controller/`, `msa/black-box-tests/`

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The OpenAPI 3.1 spec is auto-generated from code annotations via SpringDoc (`SwaggerConfiguration.java`). The API uses a single `/api/**` path without URL-based versioning (no `/v1/`, `/v2/` patterns). Database schema migrations exist in upgrade directories. The `tb_schema_settings` table tracks schema versions. However, no breaking change detection tools (OpenAPI diff, `buf breaking`, Pact) are integrated into the CI pipeline. No API deprecation notices or changelog files were found. The version field in `pom.xml` is `4.4.0-SNAPSHOT`.
- **Gap**: No API versioning strategy (URL-based or header-based), no breaking change detection in CI, and no API deprecation workflow. Agent tool bindings could break silently when the API changes.
- **Compensating Controls**:
  - Pin the ThingsBoard version used by agent integrations to a specific release
  - Monitor the ThingsBoard release notes for breaking API changes manually
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement API versioning (URL-based `/api/v1/` or `Accept-Version` header). Commit the generated OpenAPI spec to the repo and add breaking change detection to CI.
- **Evidence**: `application/src/main/java/org/thingsboard/server/config/SwaggerConfiguration.java`, `pom.xml`, `dao/src/main/resources/sql/schema-entities.sql`

#### STATE-Q1: Compensation and Rollback — RISK-SAFETY ⚡

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: ThingsBoard does not implement saga patterns, compensating transactions, or explicit rollback mechanisms for multi-step API operations. The rule engine processes messages through chains of rule nodes, but errors result in message routing to failure branches rather than compensating previously completed steps. Database operations use standard Spring transactional boundaries (`@Transactional`) for individual operations, but multi-entity workflows (e.g., creating a device + assigning it to a customer + setting attributes) do not have cross-operation compensation. The `sql.batch_sort: true` setting prevents deadlocks but does not provide rollback.
- **Gap**: No compensation or rollback capability for multi-step operations. If an agent-initiated workflow fails mid-sequence, previous steps cannot be automatically undone.
- **Compensating Controls**:
  - Limit agent operations to single-step read-only actions (consistent with read-only scope)
  - Implement application-level compensation in the agent orchestration layer for any multi-step workflows
- **Remediation Timeline**: 90–180 days
- **Recommendation**: For write-enabled scope expansion, implement saga patterns for multi-step entity management workflows with explicit compensation endpoints.
- **Evidence**: `application/src/main/resources/thingsboard.yml` (line 461), `application/src/main/java/org/thingsboard/server/controller/BaseController.java`

#### AUTH-Q5: Credential Management — RISK-QUALITY

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: ThingsBoard's rule engine makes external HTTP calls via `TbRestApiCallNode`, sends messages to Kafka (`TbKafkaNode`), RabbitMQ (`TbRabbitMqNode`), AWS SNS (`TbSnsNode`), AWS SQS (`TbSqsNode`), GCP Pub/Sub (`TbPubSubNode`), MQTT brokers (`TbMqttNode`), and Azure IoT Hub (`TbAzureIotHubNode`). No Resilience4j, circuit breaker annotations, or retry-with-backoff patterns were found wrapping these external calls. The `TbHttpClient` uses basic timeout configuration but no circuit breaker. Message processing uses retry strategies at the queue consumer level for internal reprocessing, not for protecting against external dependency failures.
- **Gap**: No circuit breaker, bulkhead, or resilience patterns protect the rule engine's external dependency calls. A failing external endpoint could cause cascading failures through the rule engine processing pipeline, affecting all tenants.
- **Compensating Controls**:
  - Configure timeouts on external rule engine nodes to limit blast radius
  - Use the rule engine's failure branch routing to handle external call failures gracefully
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Integrate Resilience4j circuit breakers around external HTTP, Kafka, and messaging calls in rule engine nodes.
- **Evidence**: `rule-engine/rule-engine-components/src/main/java/org/thingsboard/rule/engine/rest/TbRestApiCallNode.java`, `rule-engine/rule-engine-components/src/main/java/org/thingsboard/rule/engine/rest/TbHttpClient.java`


- **Severity**: RISK-QUALITY
- **Finding**: ThingsBoard uses environment variables for all sensitive configuration values: database credentials (`SPRING_DATASOURCE_PASSWORD`), JWT signing keys, SSL certificates, and Elasticsearch sink credentials. The `thingsboard.yml` file references environment variables with defaults (e.g., `password: "${SPRING_DATASOURCE_PASSWORD:postgres}"`). Some default credential values are present in the config file (e.g., `SSL_KEY_STORE_PASSWORD:thingsboard`, `SPRING_DATASOURCE_PASSWORD:postgres`). No integration with AWS Secrets Manager, HashiCorp Vault, or other secrets management systems was found. The `.env` file in the `docker/` directory may contain credential values.
- **Gap**: No secrets management system integration. Default credentials exist in configuration files. Credential rotation would require manual environment variable updates and service restarts.
- **Compensating Controls**:
  - Override all default credentials via environment variables in production deployments
  - Use Docker secrets or Kubernetes secrets for credential injection
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Integrate with a secrets management system (AWS Secrets Manager, HashiCorp Vault) for credential storage and automated rotation. Remove all default credential values from configuration files.
- **Evidence**: `application/src/main/resources/thingsboard.yml` (lines 943–951, 1017–1021), `docker/.env`

#### ENG-Q5: Encryption at Rest — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: ThingsBoard stores sensitive data in PostgreSQL/Cassandra/TimescaleDB. SSL/TLS for database connections is configurable via `thingsboard.yml` (SSL_ENABLED, SSL_CREDENTIALS_TYPE). However, no encryption-at-rest configuration was found in the codebase. There are no KMS key references, no encrypted column definitions in the SQL schema, and no Cassandra transparent data encryption (TDE) settings. Database-level encryption at rest is a deployment infrastructure concern delegated to the operator.
- **Gap**: No encryption-at-rest configuration in the codebase. Sensitive data (user credentials, device tokens, PII) is stored unencrypted at the application layer, relying entirely on database/infrastructure-level encryption configured by the operator.
- **Compensating Controls**:
  - Enable database-level encryption at rest (PostgreSQL pgcrypto, AWS RDS encryption, Cassandra TDE)
  - Use encrypted EBS volumes for all data storage in cloud deployments
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document encryption-at-rest requirements in deployment guides. Consider adding application-level encryption for highly sensitive fields (device credentials, API keys) using a KMS-backed encryption service.
- **Evidence**: `application/src/main/resources/thingsboard.yml` (SSL configuration), `dao/src/main/resources/sql/schema-entities.sql`


#### AUTH-Q4: Identity Propagation and Delegation — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: ThingsBoard uses JWT tokens for user authentication and API keys for machine identity. The `SecurityUser` model carries user context (tenant ID, customer ID, authority) through the request lifecycle. Service-to-service communication within the platform uses internal messaging (Kafka/gRPC) with tenant context propagation. However, no explicit OAuth2 on-behalf-of flows, token exchange patterns, or delegated identity mechanisms were found. API keys are always associated with a single user — there is no mechanism to distinguish "agent acting as itself" from "agent acting on behalf of user X." The `X-User-Id` or similar delegation headers are not supported. All actions through an API key are attributed to the key's owner, not to the end-user the agent may be serving.
- **Gap**: No identity propagation or delegation mechanism exists. An agent cannot act on behalf of a specific user with that user's permissions. All agent actions inherit the API key owner's full role permissions, conflating agent-as-self with agent-on-behalf-of-user.
- **Compensating Controls**:
  - Create per-user API keys scoped to specific agent workflows
  - Log the intended user context as metadata alongside the API key principal in audit records
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement OAuth2 token exchange or an on-behalf-of header mechanism that allows agents to declare which user they are acting for, with the system enforcing that user's permission boundaries.
- **Evidence**: `application/src/main/java/org/thingsboard/server/service/security/model/SecurityUser.java`, `application/src/main/java/org/thingsboard/server/controller/ApiKeyController.java`

#### DATA-Q4: System of Record Designations — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: ThingsBoard is the system of record for IoT entities it manages (devices, assets, customers, dashboards, rule chains). Entity ownership is defined by tenant isolation — each tenant owns its entity hierarchy. However, no explicit system-of-record designations, master data management processes, or golden record patterns were found in the codebase. No documentation or metadata identifies which system is authoritative for shared entity types (e.g., customer records that may also exist in a CRM). No conflict resolution logic exists for data received from external systems.
- **Gap**: No explicit system-of-record designations for key entities. When ThingsBoard data overlaps with external systems (CRM, ERP, CMDB), there is no defined authority or conflict resolution mechanism.
- **Compensating Controls**:
  - Document ThingsBoard as the authoritative source for device and telemetry data in the organization's data governance framework
  - Use ThingsBoard entity IDs as the primary keys for agent tool bindings
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add system-of-record metadata to the platform's entity model, documenting which entity types ThingsBoard owns authoritatively vs. which are replicated from external systems.
- **Evidence**: `dao/src/main/resources/sql/schema-entities.sql`, `application/src/main/resources/thingsboard.yml`

#### DATA-Q5: Temporal Metadata and Freshness — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: ThingsBoard entities include `created_time` (bigint epoch milliseconds) fields in all major database tables (devices, assets, customers, users, alarms, dashboards, rule chains). Telemetry data includes timestamps via the time-series storage layer. However, no `updated_time` or `last_modified` fields were found on entity tables — only `created_time`. No `Cache-Control`, `X-Data-Age`, or `last_refreshed` response headers are returned by API endpoints. No consistency-level signaling (strong/eventual/cached) exists. Timezone handling relies on epoch milliseconds (inherently UTC) but no explicit timezone normalization documentation was found.
- **Gap**: Entity tables lack `updated_time` fields — agents cannot determine when an entity was last modified. No HTTP freshness headers or consistency-level signaling inform agents whether returned data is current, cached, or eventually consistent.
- **Compensating Controls**:
  - Use the audit log timestamps as a proxy for entity modification times
  - Query telemetry timestamps directly for time-sensitive data freshness
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `updated_time` columns to all major entity tables. Return `Last-Modified` and `Cache-Control` headers on entity GET endpoints. Consider adding a `consistency_level` field to API responses.
- **Evidence**: `dao/src/main/resources/sql/schema-entities.sql`, `application/src/main/java/org/thingsboard/server/controller/ImageController.java`

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface
- **Severity**: INFO (No gap — passes as BLOCKER check)
- **Finding**: ThingsBoard exposes a comprehensive REST API via 68+ Spring MVC `@RestController` classes under `/api/**`. The API covers all platform functions: authentication, device management, telemetry, alarms, dashboards, rule chains, and more. Integration through the API is the primary and intended method. No direct database access or file-based exchange is required for agents.
- **Implication**: The API surface is well-suited for agent tool integration. Agents can bind to documented REST endpoints for all platform operations.
- **Evidence**: `application/src/main/java/org/thingsboard/server/controller/` (68+ controllers)

### API-Q2: Machine-Readable API Specification
- **Severity**: INFO (No gap — passes as RISK-QUALITY check)
- **Finding**: OpenAPI 3.1 specification is auto-generated from code annotations via SpringDoc (`SwaggerConfiguration.java`). Controllers use `io.swagger.v3.oas.annotations` for endpoint documentation. The spec includes structured error responses, security schemes (JWT + API Key), and data models. The spec stays current with the implementation because it is generated from annotations.
- **Implication**: Agent tool definitions can be auto-generated from the OpenAPI spec. The auto-generation approach ensures the spec stays synchronized with the implementation.
- **Evidence**: `application/src/main/java/org/thingsboard/server/config/SwaggerConfiguration.java`

### API-Q3: Structured Error Responses
- **Severity**: INFO (No gap — passes as RISK-QUALITY check)
- **Finding**: ThingsBoard implements structured error responses via `ThingsboardErrorResponse` and `ThingsboardErrorCode` enum with 14 distinct error codes (GENERAL=2, AUTHENTICATION=10, JWT_TOKEN_EXPIRED=11, PERMISSION_DENIED=20, BAD_REQUEST_PARAMS=31, ITEM_NOT_FOUND=32, TOO_MANY_REQUESTS=33, VERSION_CONFLICT=35, etc.). The `BaseController` maps all exceptions to appropriate error codes. The `SwaggerConfiguration` documents standard error responses (400, 401, 403, 404, 429) in the OpenAPI spec.
- **Implication**: Agents can reliably distinguish error types: authentication failures (10, 11, 15), permission denials (20), rate limits (33), not-found (32), and bad inputs (30, 31). This enables proper retry and error-handling logic.
- **Evidence**: `common/data/src/main/java/org/thingsboard/server/common/data/exception/ThingsboardErrorCode.java`, `application/src/main/java/org/thingsboard/server/controller/BaseController.java`

### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Write endpoints (POST /api/device, POST /api/asset, etc.) use UUID-based entity IDs. Updates are PUT-based (naturally idempotent for the same entity). No explicit idempotency key support was found for creation endpoints. Unique constraints exist on some business keys (e.g., `mobile_app_pkg_name_platform_unq_key`).
- **Implication**: For read-only agent scope, this is informational. If scope expands to write-enabled, idempotency key support should be added to creation endpoints.
- **Evidence**: `application/src/main/java/org/thingsboard/server/controller/DeviceController.java`, `dao/src/main/resources/sql/schema-entities.sql`

### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: All API responses are JSON, serialized via Jackson. Content-Type is `application/json`. The OpenAPI spec documents JSON response schemas for all endpoints.
- **Implication**: JSON responses are optimal for agent consumption — no extra parsing required.
- **Evidence**: `application/src/main/java/org/thingsboard/server/config/SwaggerConfiguration.java`

### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: Rate limiting is enforced via `RateLimitProcessingFilter` at the tenant and customer levels. The filter returns a `ThingsboardErrorResponse` with error code `TOO_MANY_REQUESTS` (33) when limits are exceeded, mapped to HTTP 429. However, no `X-RateLimit-Remaining` or `Retry-After` headers are returned. Rate limits are configurable per tenant profile but not publicly documented in the API spec.
- **Implication**: Agents will receive HTTP 429 when rate-limited but cannot proactively self-throttle because remaining quota is not communicated. Agent retry logic should implement exponential backoff on 429 responses.
- **Evidence**: `application/src/main/java/org/thingsboard/server/config/RateLimitProcessingFilter.java`, `application/src/main/resources/thingsboard.yml`

### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO (No gap — passes as BLOCKER check)
- **Finding**: ThingsBoard supports API key authentication via `ApiKeyTokenAuthenticationProcessingFilter` with `X-Authorization: ApiKey <value>` header format. API keys are tied to specific users with principal attribution. JWT bearer token authentication is also supported. The `ApiKeyController` provides full CRUD for API keys including enable/disable. OAuth2 is supported for delegated authentication. The `ThingsboardSecurityConfiguration` registers both JWT and API key authentication providers.
- **Implication**: Agents can authenticate using API keys with full principal attribution in audit logs. The API key model supports the machine identity requirements for agent integration.
- **Evidence**: `application/src/main/java/org/thingsboard/server/config/ThingsboardSecurityConfiguration.java`, `application/src/main/java/org/thingsboard/server/controller/ApiKeyController.java`

### AUTH-Q3: Action-Level Authorization
- **Severity**: INFO (No gap — passes as RISK-SAFETY check)
- **Finding**: ThingsBoard implements action-level authorization via the `Operation` enum (READ, WRITE, DELETE, CREATE, RPC_CALL, READ_CREDENTIALS, WRITE_CREDENTIALS, READ_ATTRIBUTES, WRITE_ATTRIBUTES, READ_TELEMETRY, WRITE_TELEMETRY, etc.) and the `Resource` enum (30+ resource types). The `accessControlService.checkPermission()` method is called before every entity operation in `BaseController`. Permission matrices are defined in `SysAdminPermissions`, `TenantAdminPermissions`, and `CustomerUserPermissions`.
- **Implication**: The granularity of authorization is excellent. An agent identity can be checked at the action + resource level, supporting read-but-not-delete scenarios.
- **Evidence**: `application/src/main/java/org/thingsboard/server/service/security/permission/Operation.java`, `application/src/main/java/org/thingsboard/server/service/security/permission/Resource.java`

### AUTH-Q7: Agent Identity Suspension
- **Severity**: INFO (No gap — passes as RISK-SAFETY check)
- **Finding**: The `ApiKeyController.enableApiKey()` endpoint (`PUT /api/apiKey/{id}/enabled/{enabledValue}`) allows immediate enable/disable of individual API keys. The `ApiKeyController.deleteApiKey()` provides permanent revocation. User accounts can also be disabled (`userService.setUserCredentialsEnabled()`). These mechanisms allow isolating a misbehaving agent without disrupting other agents or users.
- **Implication**: Agent identity suspension is fully supported via the API key enable/disable mechanism. This meets the requirement for immediate isolation of compromised agent identities.
- **Evidence**: `application/src/main/java/org/thingsboard/server/controller/ApiKeyController.java`

### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: ThingsBoard uses `sql.batch_sort: true` to prevent deadlocks in batch operations. The `ShallowEtagHeaderFilter` provides weak ETags for static resources. The `VERSION_CONFLICT` error code (35) and `EntityVersionMismatchException` indicate some version conflict detection. However, no explicit optimistic locking (version fields, `If-Match` headers) was found on entity write endpoints.
- **Implication**: For read-only scope, concurrency controls are informational. If expanding to write-enabled scope, optimistic locking should be added to entity mutation endpoints.
- **Evidence**: `application/src/main/resources/thingsboard.yml` (line 461), `common/data/src/main/java/org/thingsboard/server/common/data/exception/ThingsboardErrorCode.java`

### STATE-Q5: Rate Limiting and Throttling
- **Severity**: INFO (No gap — passes as RISK-SAFETY check)
- **Finding**: Comprehensive rate limiting exists at multiple levels: REST API per tenant (`RateLimitProcessingFilter` with `LimitedApi.REST_REQUESTS_PER_TENANT`), per customer (`REST_REQUESTS_PER_CUSTOMER`), WebSocket subscriptions per tenant/user, transport IP limits, mail sending per tenant, Cassandra query rate limits per tenant, rule engine debug mode rate limits per tenant, and password reset per user. Rate limit configuration is cached with 120-minute TTL and 200K max entries.
- **Implication**: The multi-level rate limiting provides strong protection against agent traffic storms. Agents will be throttled at the tenant level, preventing one agent from overwhelming the platform.
- **Evidence**: `application/src/main/java/org/thingsboard/server/config/RateLimitProcessingFilter.java`, `application/src/main/resources/thingsboard.yml`

### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: ThingsBoard has usage quotas per tenant (API usage states), entity limits (max devices, assets, etc.), and rate limits per tenant. However, no agent-specific transaction limits (e.g., max records per run, max spend per hour) were found. The limits are scoped to tenant profiles, not agent identities.
- **Implication**: For read-only scope, blast radius limits are informational. If expanding to write-enabled scope, agent-specific transaction limits should be implemented.
- **Evidence**: `application/src/main/resources/thingsboard.yml`

### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: ThingsBoard alarm workflows support status transitions (ACTIVE_UNACK → ACTIVE_ACK → CLEARED). OTA package deployment has staged rollout patterns. However, no general-purpose draft/pending state mechanism exists for entity creation (devices, assets, dashboards). Entities are created directly in their final state.
- **Implication**: For read-only scope, draft states are not needed. For future write-enabled scope, consider adding draft status support for high-risk entity types.
- **Evidence**: `dao/src/main/resources/sql/schema-entities.sql` (alarm table)

### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable approval gate mechanism was found in the codebase. Operations execute immediately upon authorized API calls. No Step Functions with human approval tasks or status-based approval workflows were identified.
- **Implication**: For read-only scope, approval gates are not needed. For write-enabled scope, consider implementing approval workflows for high-risk operations (e.g., device credential rotation, bulk entity deletion).
- **Evidence**: No evidence found — absence is the finding.


### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: ThingsBoard has a comprehensive notification system (`NotificationCenter`, `NotificationTargetService`) and rule engine that emits events for entity state changes. The rule engine processes messages through chains of rule nodes that can trigger external integrations via Kafka (`TbKafkaNode`), RabbitMQ (`TbRabbitMqNode`), MQTT (`TbMqttNode`), AWS SNS (`TbSnsNode`), AWS SQS (`TbSqsNode`), and REST API calls (`TbRestApiCallNode`). Webhook-style notifications can be configured through rule chains. Edge events are emitted via `EdgeEventService` for edge synchronization.
- **Implication**: Agents can subscribe to state change events through the rule engine's external integration nodes. This enables proactive agent patterns that react to device telemetry changes, alarm state transitions, and entity lifecycle events without polling.
- **Evidence**: `rule-engine/rule-engine-components/src/main/java/org/thingsboard/rule/engine/rest/TbRestApiCallNode.java`, `dao/src/main/java/org/thingsboard/server/dao/notification/DefaultNotificationTargetService.java`

### STATE-Q2: Queryable Current State
- **Severity**: INFO
- **Finding**: ThingsBoard exposes comprehensive GET endpoints for all entity types with full `PageLink`-based pagination (`PageLink` with `pageSize`, `page`, `textSearch`, `sortOrder`). The `PageData` response includes `totalPages`, `totalElements`, and `hasNext` fields. Entity state is queryable via REST API: GET `/api/device/{id}`, GET `/api/asset/{id}`, GET `/api/customer/{id}`, etc. Telemetry can be queried via GET `/api/plugins/telemetry/{entityType}/{entityId}/values/timeseries`. EDQS (Entity Data Query Service) provides advanced entity data querying with filtering, sorting, and aggregation.
- **Implication**: Agents can inspect current entity state before taking any action. The comprehensive query surface with pagination, filtering, and sorting supports agent read-before-write patterns.
- **Evidence**: `common/data/src/main/java/org/thingsboard/server/common/data/page/PageLink.java`, `common/data/src/main/java/org/thingsboard/server/common/data/page/PageData.java`, `rest-client/src/main/java/org/thingsboard/rest/client/RestClient.java`

### DATA-Q3: Selective Query Support
- **Severity**: INFO
- **Finding**: ThingsBoard implements comprehensive selective query support via the `PageLink` class with `pageSize`, `page`, `textSearch`, and `sortOrder` parameters. The `PageData<T>` response wrapper includes `totalPages`, `totalElements`, `hasNext`, and the data list. All list endpoints support pagination by default. The EDQS service provides advanced entity data queries with filters, key filters, and entity filters. Telemetry queries support time-range filtering with aggregation. Result size limits are enforced — `pageSize` has configurable maximum bounds.
- **Implication**: Agents can query with precise pagination, filtering, and sorting to limit result set sizes. The `hasNext` field enables cursor-style iteration without fetching all results at once.
- **Evidence**: `common/data/src/main/java/org/thingsboard/server/common/data/page/PageLink.java`, `common/data/src/main/java/org/thingsboard/server/common/data/page/PageData.java`

### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality scores, completeness metrics, or data profiling reports were found in the codebase. No null rate monitoring, duplicate detection logic, or data freshness SLAs are defined. Telemetry data quality depends on device connectivity and protocol compliance. No data quality dashboards or alerting mechanisms exist in the platform itself.
- **Implication**: Agents consuming ThingsBoard data have no visibility into data quality. Planning consideration for agent workflows that require high data reliability — implement data quality monitoring at the deployment level.
- **Evidence**: No evidence found — absence is the finding.

### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: ThingsBoard uses semantically meaningful, human-readable field names throughout its data model. Entity types use clear names: `device`, `asset`, `customer`, `dashboard`, `rule_chain`, `alarm`. Fields follow camelCase Java conventions in the API (e.g., `createdTime`, `tenantId`, `deviceProfileId`, `additionalInfo`) and snake_case in the SQL schema (e.g., `created_time`, `tenant_id`, `device_profile_id`, `additional_info`). No legacy abbreviations or codes requiring a data dictionary were found. The OpenAPI spec documents all field names with descriptions.
- **Implication**: Agent LLM reasoning can work effectively with ThingsBoard field names — no data dictionary or code translation is needed. Field names are self-documenting.
- **Evidence**: `dao/src/main/resources/sql/schema-entities.sql`, `application/src/main/java/org/thingsboard/server/config/SwaggerConfiguration.java`

### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal data catalog (AWS Glue, Collibra, Alation, DataHub) or metadata layer was found. The OpenAPI spec auto-generated from code annotations serves as the primary schema documentation. Database schema is documented through SQL migration files. No standalone data dictionary, entity relationship documentation, or semantic metadata layer exists in the repository.
- **Implication**: Agent tool builders must rely on the OpenAPI spec and database schema files as the de facto data catalog. Consider generating a data catalog from the existing schema for accelerated tool development.
- **Evidence**: `application/src/main/java/org/thingsboard/server/config/SwaggerConfiguration.java`, `dao/src/main/resources/sql/schema-entities.sql`

### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: ThingsBoard uses Micrometer with Prometheus integration for metrics (`io.micrometer.core.instrument.Timer` used in `TbRuleEngineConsumerStats` and `TbMsgPackCallback`). Spring Boot Actuator exposes infrastructure metrics via `/actuator/prometheus`. However, no custom business outcome metrics were found — metrics focus on infrastructure concerns (queue processing times, message throughput) rather than business outcomes (device connectivity rates, alarm resolution times, tenant activity levels). No business KPI dashboards or custom CloudWatch metric publishing was identified.
- **Implication**: When agents interact with ThingsBoard, there are no business-level metrics to measure whether agent actions produce good outcomes. Business outcome metrics (e.g., alarm resolution rate by agent, device provisioning success rate) should be added to evaluate agent effectiveness.
- **Evidence**: `application/src/main/java/org/thingsboard/server/service/queue/TbRuleEngineConsumerStats.java`, `docker/monitoring/prometheus/prometheus.yml`

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: ThingsBoard exposes 68+ REST controllers at `/api/**` with full OpenAPI 3.1 documentation. Integration is API-first with no DB-direct or file-based exchange patterns.
- **Gap**: None
- **Recommendation**: None
- **Evidence**: `application/src/main/java/org/thingsboard/server/controller/` (68+ controllers)

#### API-Q2: Machine-Readable API Specification
- **Severity**: INFO
- **Finding**: OpenAPI 3.1 auto-generated from SpringDoc annotations in `SwaggerConfiguration.java`. Kept current by code-generation approach.
- **Gap**: None
- **Recommendation**: Commit the generated spec to the repo for CI validation.
- **Evidence**: `application/src/main/java/org/thingsboard/server/config/SwaggerConfiguration.java`

#### API-Q3: Structured Error Responses
- **Severity**: INFO
- **Finding**: `ThingsboardErrorCode` enum with 14 error codes. Structured `ThingsboardErrorResponse` returned for all errors. Documented in OpenAPI spec.
- **Gap**: None — error responses include error code, message, and HTTP status.
- **Recommendation**: Add a `retryable` boolean field to error responses for agent-friendly error handling.
- **Evidence**: `common/data/src/main/java/org/thingsboard/server/common/data/exception/ThingsboardErrorCode.java`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No explicit idempotency key support. PUT updates are naturally idempotent. POST creates use server-generated UUIDs.
- **Gap**: No idempotency keys on creation endpoints.
- **Recommendation**: Informational for read-only scope.
- **Evidence**: `application/src/main/java/org/thingsboard/server/controller/DeviceController.java`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: All responses are JSON via Jackson serialization.
- **Gap**: None
- **Recommendation**: None
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
- **Finding**: Rule engine emits events for state changes via Kafka, RabbitMQ, MQTT, SNS, SQS, and REST API call nodes. Notification system supports webhook-style notifications. Edge events via `EdgeEventService`.
- **Gap**: None — comprehensive event emission capability exists via rule engine.
- **Recommendation**: Document recommended rule chain patterns for agent-consumable event streams.
- **Evidence**: `rule-engine/rule-engine-components/src/main/java/org/thingsboard/rule/engine/rest/TbRestApiCallNode.java`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: Rate limiting enforced via `RateLimitProcessingFilter`. HTTP 429 with TOO_MANY_REQUESTS error code returned. No `X-RateLimit-Remaining` or `Retry-After` headers.
- **Gap**: No rate limit headers for proactive throttling.
- **Recommendation**: Add `X-RateLimit-Remaining` and `Retry-After` response headers.
- **Evidence**: `application/src/main/java/org/thingsboard/server/config/RateLimitProcessingFilter.java`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: API key authentication with principal attribution (`ApiKeyTokenAuthenticationProcessingFilter`). JWT bearer token support. OAuth2 support. API keys tied to users for audit attribution.
- **Gap**: None
- **Recommendation**: None
- **Evidence**: `application/src/main/java/org/thingsboard/server/config/ThingsboardSecurityConfiguration.java`, `application/src/main/java/org/thingsboard/server/controller/ApiKeyController.java`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: Three built-in roles (SYS_ADMIN, TENANT_ADMIN, CUSTOMER_USER). No custom role creation. API keys inherit full user role permissions.
- **Gap**: No custom role scoping for agent identities.
- **Recommendation**: Implement API key scoping mechanism.
- **Evidence**: `application/src/main/java/org/thingsboard/server/service/security/permission/`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: INFO
- **Finding**: Fine-grained `Operation` enum (READ, WRITE, DELETE, CREATE, RPC_CALL, etc.) with `accessControlService.checkPermission()` enforced on every entity operation.
- **Gap**: None — action-level authorization is implemented.
- **Recommendation**: None
- **Evidence**: `application/src/main/java/org/thingsboard/server/service/security/permission/Operation.java`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: RISK-QUALITY
- **Finding**: JWT tokens carry user context (tenant ID, customer ID, authority) through request lifecycle. API keys are tied to single users. No OAuth2 on-behalf-of flows or token exchange patterns found. No mechanism to distinguish agent-as-self from agent-on-behalf-of-user.
- **Gap**: No identity propagation or delegation mechanism. Agent cannot act on behalf of a specific user with that user's permissions.
- **Recommendation**: Implement OAuth2 token exchange or on-behalf-of header mechanism.
- **Evidence**: `application/src/main/java/org/thingsboard/server/service/security/model/SecurityUser.java`, `application/src/main/java/org/thingsboard/server/controller/ApiKeyController.java`

#### AUTH-Q5: Credential Management
- **Severity**: RISK-QUALITY
- **Finding**: Environment variables used for all credentials. Default values in config files (e.g., `postgres`, `thingsboard`). No Secrets Manager/Vault integration.
- **Gap**: Default credentials in config. No secrets management system.
- **Recommendation**: Integrate secrets management system; remove defaults.
- **Evidence**: `application/src/main/resources/thingsboard.yml` (lines 943–951)

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Comprehensive audit logging enabled by default with per-entity-type masks. Stored in PostgreSQL. Optional Elasticsearch sink. Not immutable — stored in mutable database.
- **Gap**: Audit logs lack immutability guarantees.
- **Recommendation**: Enable Elasticsearch sink with write-once index policies.
- **Evidence**: `application/src/main/resources/thingsboard.yml` (lines 980–1021)

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: INFO
- **Finding**: `PUT /api/apiKey/{id}/enabled/{enabledValue}` provides immediate API key enable/disable. `DELETE /api/apiKey/{id}` for permanent revocation.
- **Gap**: None
- **Recommendation**: None
- **Evidence**: `application/src/main/java/org/thingsboard/server/controller/ApiKeyController.java`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No saga patterns or compensating transactions. Standard Spring `@Transactional` for individual operations.
- **Gap**: No multi-step rollback capability.
- **Recommendation**: Implement saga patterns for write-enabled scope expansion.
- **Evidence**: `application/src/main/java/org/thingsboard/server/controller/BaseController.java`

#### STATE-Q2: Queryable Current State
- **Severity**: INFO
- **Finding**: Comprehensive GET endpoints for all entity types with `PageLink`-based pagination. `PageData` response includes `totalPages`, `totalElements`, `hasNext`. EDQS provides advanced entity data querying.
- **Gap**: None — current state is fully queryable via REST API.
- **Recommendation**: None.
- **Evidence**: `common/data/src/main/java/org/thingsboard/server/common/data/page/PageLink.java`, `common/data/src/main/java/org/thingsboard/server/common/data/page/PageData.java`

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: `sql.batch_sort: true` for deadlock prevention. `VERSION_CONFLICT` error code exists. No explicit optimistic locking on write endpoints.
- **Gap**: No explicit optimistic locking.
- **Recommendation**: Informational for read-only scope.
- **Evidence**: `application/src/main/resources/thingsboard.yml`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: Rule engine makes external calls via `TbRestApiCallNode`, `TbKafkaNode`, `TbRabbitMqNode`, `TbSnsNode`, `TbSqsNode`, `TbPubSubNode`, `TbMqttNode`, `TbAzureIotHubNode`. No circuit breaker or resilience patterns found.
- **Gap**: No circuit breakers protect external dependency calls in the rule engine.
- **Recommendation**: Integrate Resilience4j circuit breakers around external calls in rule engine nodes.
- **Evidence**: `rule-engine/rule-engine-components/src/main/java/org/thingsboard/rule/engine/rest/TbRestApiCallNode.java`, `rule-engine/rule-engine-components/src/main/java/org/thingsboard/rule/engine/rest/TbHttpClient.java`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: INFO
- **Finding**: Multi-level rate limiting: REST per tenant, per customer, WebSocket, transport IP, mail, Cassandra query, rule engine debug.
- **Gap**: None — comprehensive rate limiting is implemented.
- **Recommendation**: None
- **Evidence**: `application/src/main/java/org/thingsboard/server/config/RateLimitProcessingFilter.java`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Tenant-level usage quotas and entity limits exist. No agent-specific transaction limits.
- **Gap**: No agent-specific limits.
- **Recommendation**: Informational for read-only scope.
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
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Alarm status transitions exist (ACTIVE_UNACK → ACTIVE_ACK → CLEARED). No general draft/pending pattern for entity creation.
- **Gap**: No general-purpose draft state.
- **Recommendation**: Informational for read-only scope.
- **Evidence**: `dao/src/main/resources/sql/schema-entities.sql`

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No approval gate mechanism found.
- **Gap**: No approval workflows.
- **Recommendation**: Informational for read-only scope.
- **Evidence**: No evidence found — absence is the finding.

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: Docker Compose files provide local development/testing environments. Multiple compose variants (postgres, kafka, prometheus-grafana) enable local staging. Separate `.env` files per service. No dedicated staging environment with production-equivalent data shape.
- **Gap**: No production-equivalent staging with seed data.
- **Recommendation**: Create a staging Docker Compose profile with synthetic seed data for agent testing.
- **Evidence**: `docker/docker-compose.yml`, `docker/docker-compose.postgres.yml`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification ⚡ (Tiered)
- **Severity**: BLOCKER
- **Finding**: B1 BLOCKER — `DeviceController.getDeviceCredentialsByDeviceId()` returns plaintext access tokens, MQTT passwords, and X.509 certificates to any CUSTOMER_USER via `GET /api/device/{deviceId}/credentials`. User endpoint is CLEAR (password lives in separate `UserCredentials` entity, not serialized with `User`). B2 CLEAR (three-tier `Authority` model with strong tenant isolation via `checkDeviceId` + `Operation.READ_CREDENTIALS`), but CUSTOMER_USER still retains `READ_CREDENTIALS`. B3 INFO (no `@JsonIgnore` or `@Sensitive` on `credentialsValue`). See BLOCKERs section above.
- **Gap**: `credentialsValue` serialized unmasked; CUSTOMER_USER-scope read access sufficient to exfiltrate device credentials.
- **Recommendation**: `@JsonIgnore` on `credentialsValue`; separate read endpoint gated to TENANT_ADMIN; out-of-band credential rotation.
- **Evidence**: `application/src/main/java/org/thingsboard/server/controller/DeviceController.java:307-318`, `common/data/src/main/java/org/thingsboard/server/common/data/security/DeviceCredentials.java`, `common/data/src/main/java/org/thingsboard/server/common/data/User.java` (correctly isolated).

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Self-hosted platform; residency is operator-controlled. No residency controls in codebase.
- **Gap**: No data residency controls or metadata.
- **Recommendation**: See RISKs section.
- **Evidence**: `application/src/main/resources/thingsboard.yml`

#### DATA-Q3: Selective Query Support
- **Severity**: INFO
- **Finding**: Comprehensive `PageLink`-based pagination with `pageSize`, `page`, `textSearch`, `sortOrder`. `PageData<T>` includes `totalPages`, `totalElements`, `hasNext`. EDQS provides advanced entity data queries with filters. Result size limits enforced via `pageSize` bounds.
- **Gap**: None — selective query support is comprehensive.
- **Recommendation**: None.
- **Evidence**: `common/data/src/main/java/org/thingsboard/server/common/data/page/PageLink.java`, `common/data/src/main/java/org/thingsboard/server/common/data/page/PageData.java`

#### DATA-Q4: System of Record Designations
- **Severity**: RISK-QUALITY
- **Finding**: ThingsBoard is the de facto system of record for IoT entities it manages. No explicit system-of-record designations, master data management processes, or golden record patterns found. No conflict resolution logic for data from external systems.
- **Gap**: No explicit system-of-record designations or conflict resolution for shared entity types.
- **Recommendation**: Document ThingsBoard as authoritative source for device/telemetry data; add system-of-record metadata to entity model.
- **Evidence**: `dao/src/main/resources/sql/schema-entities.sql`

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK-QUALITY
- **Finding**: All major tables include `created_time` (bigint epoch ms). Telemetry has timestamps. No `updated_time` fields on entity tables. No `Cache-Control`, `X-Data-Age`, or consistency-level response headers. Epoch ms is inherently UTC.
- **Gap**: No `updated_time` fields. No HTTP freshness or consistency-level signaling.
- **Recommendation**: Add `updated_time` columns; return `Last-Modified` and `Cache-Control` headers.
- **Evidence**: `dao/src/main/resources/sql/schema-entities.sql`

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: No PII redaction or masking framework. Audit logs may contain user data.
- **Gap**: No PII masking in logging.
- **Recommendation**: See RISKs section.
- **Evidence**: `application/src/main/resources/thingsboard.yml`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality scores, completeness metrics, or data profiling reports found. No null rate monitoring, duplicate detection, or data freshness SLAs defined.
- **Gap**: No data quality monitoring or metrics.
- **Recommendation**: Implement data quality monitoring at the deployment level for agent-consumed datasets.
- **Evidence**: No evidence found — absence is the finding.

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: No API versioning. No breaking change detection in CI. Auto-generated OpenAPI spec not committed.
- **Gap**: No versioning strategy or CI-based contract validation.
- **Recommendation**: See RISKs section.
- **Evidence**: `application/src/main/java/org/thingsboard/server/config/SwaggerConfiguration.java`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Semantically meaningful field names throughout: `device`, `asset`, `customer`, `dashboard`, `rule_chain`. CamelCase in API (`createdTime`, `tenantId`), snake_case in SQL (`created_time`, `tenant_id`). No legacy abbreviations or codes.
- **Gap**: None — field names are human-readable and self-documenting.
- **Recommendation**: None.
- **Evidence**: `dao/src/main/resources/sql/schema-entities.sql`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal data catalog (Glue, Collibra, DataHub). OpenAPI spec and SQL schema files serve as de facto documentation. No standalone data dictionary or semantic metadata layer.
- **Gap**: No formal data catalog.
- **Recommendation**: Generate a data catalog from existing schema for accelerated agent tool development.
- **Evidence**: `application/src/main/java/org/thingsboard/server/config/SwaggerConfiguration.java`, `dao/src/main/resources/sql/schema-entities.sql`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: SLF4J/Logback logging. Prometheus metrics via Actuator. No OpenTelemetry, no structured JSON logs, no correlation IDs.
- **Gap**: No distributed tracing or structured logging.
- **Recommendation**: See RISKs section.
- **Evidence**: `docker/monitoring/prometheus/prometheus.yml`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: Prometheus/Grafana integration for metrics collection. No alert rules defined.
- **Gap**: No automated alerting.
- **Recommendation**: See RISKs section.
- **Evidence**: `docker/monitoring/prometheus/prometheus.yml`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: Micrometer with Prometheus for infrastructure metrics. No custom business outcome metrics (alarm resolution rates, device connectivity rates, tenant activity). Metrics focus on queue processing and message throughput.
- **Gap**: No business-level outcome metrics for evaluating agent effectiveness.
- **Recommendation**: Add business outcome metrics (e.g., alarm resolution rate, device provisioning success rate) via custom Micrometer gauges.
- **Evidence**: `application/src/main/java/org/thingsboard/server/service/queue/TbRuleEngineConsumerStats.java`, `docker/monitoring/prometheus/prometheus.yml`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance
- **Severity**: RISK-QUALITY
- **Finding**: Docker Compose IaC. No Terraform/CloudFormation. No drift detection or automated plan review.
- **Gap**: No formal IaC governance.
- **Recommendation**: See RISKs section.
- **Evidence**: `docker/docker-compose.yml`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: GitHub Actions for config validation. No API contract testing in CI.
- **Gap**: No contract testing.
- **Recommendation**: See RISKs section.
- **Evidence**: `.github/workflows/check-configuration-files.yml`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: Docker image versioning supports manual rollback. No automated rollback triggers.
- **Gap**: No automated rollback.
- **Recommendation**: See RISKs section.
- **Evidence**: `docker/docker-compose.yml`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: 50+ controller test files. Black-box tests in `msa/black-box-tests/`. Not visibly executed in GitHub Actions CI.
- **Gap**: Tests not in CI pipeline.
- **Recommendation**: See RISKs section.
- **Evidence**: `application/src/test/java/org/thingsboard/server/controller/`

#### ENG-Q5: Encryption at Rest
- **Severity**: RISK-QUALITY
- **Finding**: No encryption-at-rest configuration in codebase. Delegated to infrastructure operator.
- **Gap**: No application-level encryption at rest.
- **Recommendation**: See RISKs section.
- **Evidence**: `dao/src/main/resources/sql/schema-entities.sql`

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `application/src/main/java/org/thingsboard/server/controller/` (68+ controllers) | API-Q1, API-Q4 |
| `application/src/main/java/org/thingsboard/server/config/SwaggerConfiguration.java` | API-Q2, API-Q3, API-Q5, DISC-Q1 |
| `application/src/main/java/org/thingsboard/server/config/RateLimitProcessingFilter.java` | API-Q8, STATE-Q5 |
| `application/src/main/java/org/thingsboard/server/config/ThingsboardSecurityConfiguration.java` | AUTH-Q1 |
| `application/src/main/java/org/thingsboard/server/controller/AuthController.java` | AUTH-Q1 |
| `application/src/main/java/org/thingsboard/server/controller/ApiKeyController.java` | AUTH-Q1, AUTH-Q4, AUTH-Q7 |
| `application/src/main/java/org/thingsboard/server/controller/BaseController.java` | API-Q3, AUTH-Q6, DATA-Q6, STATE-Q1 |
| `application/src/main/java/org/thingsboard/server/service/security/model/SecurityUser.java` | AUTH-Q4 |
| `application/src/main/java/org/thingsboard/server/service/security/permission/Operation.java` | AUTH-Q2, AUTH-Q3 |
| `application/src/main/java/org/thingsboard/server/service/security/permission/Resource.java` | AUTH-Q2, AUTH-Q3 |
| `application/src/main/java/org/thingsboard/server/service/security/permission/CustomerUserPermissions.java` | AUTH-Q2 |
| `common/data/src/main/java/org/thingsboard/server/common/data/exception/ThingsboardErrorCode.java` | API-Q3, STATE-Q3 |
| `common/data/src/main/java/org/thingsboard/server/common/data/page/PageLink.java` | STATE-Q2, DATA-Q3 |
| `common/data/src/main/java/org/thingsboard/server/common/data/page/PageData.java` | STATE-Q2, DATA-Q3 |
| `rule-engine/rule-engine-components/src/main/java/org/thingsboard/rule/engine/rest/TbRestApiCallNode.java` | API-Q7, STATE-Q4 |
| `rule-engine/rule-engine-components/src/main/java/org/thingsboard/rule/engine/rest/TbHttpClient.java` | STATE-Q4 |
| `rule-engine/rule-engine-components/src/main/java/org/thingsboard/rule/engine/kafka/TbKafkaNode.java` | STATE-Q4 |
| `application/src/main/java/org/thingsboard/server/service/queue/TbRuleEngineConsumerStats.java` | OBS-Q3 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `application/src/main/resources/thingsboard.yml` | AUTH-Q5, AUTH-Q6, STATE-Q3, STATE-Q5, STATE-Q6, DATA-Q2, DATA-Q6, API-Q8, OBS-Q1, ENG-Q5 |
| `docker/.env` | AUTH-Q5, ENG-Q3 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `docker/docker-compose.yml` | ENG-Q1, ENG-Q3, STATE-Q7, HITL-Q3 |
| `docker/docker-compose.postgres.yml` | HITL-Q3 |
| `docker/docker-compose.prometheus-grafana.yml` | OBS-Q2 |
| `docker/haproxy/` | ENG-Q1 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/check-configuration-files.yml` | ENG-Q1, ENG-Q2 |
| `.github/workflows/license-header-format.yml` | ENG-Q2 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `pom.xml` | DISC-Q1 |

### Database Schema
| File | Questions Referenced |
|------|---------------------|
| `dao/src/main/resources/sql/schema-entities.sql` | DATA-Q1, DATA-Q2, DATA-Q4, DATA-Q5, DISC-Q2, API-Q4, HITL-Q1, ENG-Q5 |

### Monitoring
| File | Questions Referenced |
|------|---------------------|
| `docker/monitoring/prometheus/prometheus.yml` | OBS-Q1, OBS-Q2, OBS-Q3 |

### Test Files
| File | Questions Referenced |
|------|---------------------|
| `application/src/test/java/org/thingsboard/server/controller/` (50+ test files) | ENG-Q4 |
| `msa/black-box-tests/` | ENG-Q4 |
