# Agentic Readiness Assessment Report

**Target**: ThingsBoard (monorepo)
**Date**: 2026-04-29
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: monorepo
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: java, iot, platform
**Context**: Open-source IoT platform for device management, data collection, and visualization.

**Archetype Justification**: ThingsBoard owns persistent state in PostgreSQL/Cassandra databases and exposes full CRUD operations on 30+ entity types (devices, assets, customers, dashboards, alarms, rule chains, users, etc.) via an extensive REST API with 64+ controller classes. While it has orchestrator characteristics (rule engine coordinates multi-step workflows via Kafka), the dominant pattern is stateful CRUD with entity lifecycle management.

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 1 | **RISK-SAFETY**: 6 | **RISK-QUALITY**: 16 | **INFOs**: 19

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 1 |
| RISK-SAFETY | 6 |
| RISK-QUALITY | 16 |
| INFO | 19 |
| N/A | 0 |
| Not Evaluated (extended) | 1 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 18
**Extended Questions Not Triggered**: 1
**Questions N/A (repo_type: monorepo)**: 0
**Service Archetype**: stateful-crud (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### DATA-Q1: Sensitive Data Classification — BLOCKER

- **Severity**: BLOCKER
- **Finding**: ThingsBoard stores sensitive data across multiple tables including `user_credentials` (passwords, activation tokens, reset tokens), `device_credentials` (credentials_id, credentials_value, credentials_type), `oauth2_client_registration` (client_secret), and user PII (email, first_name, last_name in the `tb_user` table). No data classification tags, field-level encryption, or PII detection tooling (e.g., AWS Macie) was found anywhere in the codebase or configuration. The `schema-entities.sql` schema defines these sensitive fields as plain `varchar` columns with no classification metadata.
- **Gap**: Sensitive data (PII, credentials, secrets) is not classified or tagged at the field level. No controls exist to prevent an agent from retrieving sensitive fields without explicit authorization beyond role-based access. An agent with TENANT_ADMIN authority could retrieve device credentials, user emails, and OAuth2 secrets through the REST API.
- **Remediation**:
  - **Immediate**: Create a data classification inventory mapping all sensitive fields in `schema-entities.sql` to classification levels (PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED). At minimum, classify `user_credentials.password`, `device_credentials.credentials_value`, `oauth2_client_registration.client_secret`, and `tb_user.email`/`first_name`/`last_name`.
  - **Target State**: Field-level classification metadata applied to all sensitive data. API responses enforce classification-aware filtering — agent identities should not receive RESTRICTED fields unless explicitly authorized. Consider implementing response field filtering middleware.
  - **Estimated Effort**: Medium (30–60 days for classification inventory; 60–120 days for enforcement)
  - **Dependencies**: AUTH-Q2 (scoped permissions) — classification is meaningless without enforcement through authorization.
- **Evidence**: `dao/src/main/resources/sql/schema-entities.sql` (lines 352–361: device_credentials, lines 482–490: user_credentials, line 588: client_secret), `application/src/main/resources/thingsboard.yml`

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: ThingsBoard implements role-based access control with three authority levels: `SYS_ADMIN`, `TENANT_ADMIN`, and `CUSTOMER_USER`. Controllers use `@PreAuthorize("hasAuthority('TENANT_ADMIN')")` or `@PreAuthorize("hasAnyAuthority('TENANT_ADMIN', 'CUSTOMER_USER')")` annotations. The `TenantAdminPermissions.java` class grants `tenantEntityPermissionChecker` (which returns `true` for all operations if tenant matches) to most resources. This means a TENANT_ADMIN agent identity has full CRUD on all entity types within the tenant — there is no ability to create a scoped agent identity with, for example, read-only access to devices but no access to users or rule chains.
- **Gap**: No mechanism to create a narrowly scoped agent identity. An agent identity inherits the full permission set of its role (TENANT_ADMIN or CUSTOMER_USER). The API Key system (`ApiKeyController.java`) creates keys tied to user identities, inheriting all of that user's permissions — no per-key permission scoping.
- **Compensating Controls**:
  - Create a dedicated CUSTOMER_USER account for agent access (more restricted than TENANT_ADMIN) and limit to read-only operations at the orchestration layer
  - Implement API gateway or proxy-level restrictions to limit which endpoints the agent identity can call
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Introduce custom role definitions with granular permission sets per resource type and operation. Allow API keys to be scoped to specific resources and operations independently of the underlying user role.
- **Evidence**: `application/src/main/java/org/thingsboard/server/service/security/permission/TenantAdminPermissions.java`, `application/src/main/java/org/thingsboard/server/service/security/permission/Operation.java`, `application/src/main/java/org/thingsboard/server/controller/ApiKeyController.java`

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: ThingsBoard has a comprehensive audit logging system. The `audit_log` table (in `schema-entities.sql`) records `tenant_id`, `customer_id`, `entity_id`, `entity_type`, `entity_name`, `user_id`, `user_name`, `action_type`, `action_data`, `action_status`, and `action_failure_details`. Audit logging is configurable per entity type in `thingsboard.yml` (lines 982–1027) with levels OFF/W/RW. The system also supports forwarding audit logs to Elasticsearch as an external sink. However, audit logs are stored in the application PostgreSQL database with TTL-based cleanup (`SQL_TTL_AUDIT_LOGS_ENABLED:true`). There is no immutability or tamper-evidence mechanism — logs can be modified or deleted by anyone with database access.
- **Gap**: Audit logs are mutable. No object lock, write-once storage, or cryptographic tamper-evidence is configured. TTL-based cleanup means logs may be deleted before forensic review. No CloudTrail or equivalent immutable audit trail for agent actions.
- **Compensating Controls**:
  - Enable the Elasticsearch sink to create a secondary copy of audit logs in an external system with append-only policies
  - Configure the Elasticsearch sink with index lifecycle management (ILM) to enforce immutability on audit log indices
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Enable the Elasticsearch audit log sink and configure write-once indices. Alternatively, forward audit logs to an immutable log storage service (e.g., S3 with Object Lock, CloudWatch Logs with retention policies). Ensure agent identity (`user_id`, `user_name`) is captured in all audit log entries.
- **Evidence**: `dao/src/main/resources/sql/schema-entities.sql` (lines 78–92: audit_log table), `application/src/main/resources/thingsboard.yml` (lines 982–1027: audit-log config)

#### STATE-Q1: Compensation and Rollback ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No saga pattern, compensation logic, or explicit undo/rollback endpoints were found in the codebase. The rule engine processes messages through a chain of rule nodes, but there is no compensating transaction mechanism when a multi-step workflow fails partway. Device operations (save, assign to customer, assign to edge) are individual transactional operations — if an agent-orchestrated multi-step workflow (e.g., create device → assign to customer → configure rule chain) fails at step 3, steps 1 and 2 are not automatically rolled back. The RPC subsystem has timeout handling but no compensation for timed-out operations.
- **Gap**: No compensation or rollback mechanism for multi-step operations. The system relies on individual operation atomicity but has no workflow-level transaction management.
- **Compensating Controls**:
  - For read-only agent scope, this risk is reduced since the agent does not execute write workflows
  - Implement compensating logic in the agent orchestration layer rather than the target system
- **Remediation Timeline**: 90–180 days (architectural change)
- **Recommendation**: For the current read-only scope, document the absence and plan remediation for when write-enabled scope is required. When expanding to write-enabled, implement saga patterns for multi-step device provisioning workflows or expose explicit undo endpoints for key operations.
- **Evidence**: `application/src/main/java/org/thingsboard/server/controller/DeviceController.java`, `application/src/main/java/org/thingsboard/server/controller/RpcV2Controller.java`, `application/src/main/resources/thingsboard.yml`

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No circuit breaker library (Resilience4j, Hystrix, Sentinel) was found in `pom.xml` or the codebase. ThingsBoard's internal service-to-service communication uses Kafka message queues (not synchronous HTTP), which provides some inherent resilience through message buffering. The MQTT client has retry logic with exponential backoff (`thingsboard.yml` lines 2195–2208). However, for external dependency calls (Elasticsearch audit log sink, OAuth2 providers, external HTTP integrations in rule engine), there are no circuit breakers to prevent cascading failures. The `timeout` configurations exist for RPC calls (`MIN_SERVER_SIDE_RPC_TIMEOUT:5000`, `DEFAULT_SERVER_SIDE_RPC_TIMEOUT:10000`) but these are timeouts, not circuit breakers.
- **Gap**: No circuit breaker pattern implemented for external dependency calls. If an external system (Elasticsearch, OAuth2 provider, custom rule node HTTP endpoint) becomes unresponsive, ThingsBoard will continue sending requests until timeouts accumulate, potentially degrading the entire platform.
- **Compensating Controls**:
  - Kafka-based internal messaging provides inherent resilience (message buffering) between ThingsBoard services
  - Timeout configurations exist for RPC and transport layers, limiting individual request duration
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add Resilience4j or similar circuit breaker library to external HTTP client calls, particularly for the Elasticsearch audit log sink, OAuth2 token endpoints, and rule engine REST API call nodes. Configure circuit breaker thresholds and fallback behaviors.
- **Evidence**: `pom.xml` (no circuit breaker dependency), `application/src/main/resources/thingsboard.yml` (timeout configs), `common/queue/` (Kafka-based messaging)

#### DATA-Q2: Data Residency and Sovereignty ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: ThingsBoard's configuration (`thingsboard.yml`) specifies database connection URLs with environment variables (`SPRING_DATASOURCE_URL:jdbc:postgresql://localhost:5432/thingsboard`) but includes no data residency configuration, cross-region replication settings, or data sovereignty policies. The platform is designed as a self-hosted IoT platform, giving operators full control over data placement, but the codebase itself has no built-in data residency enforcement or region-awareness. As an open-source IoT platform handling device telemetry and potentially customer PII, data residency requirements depend on the deployment context.
- **Gap**: No data residency controls or sovereignty enforcement in the codebase. Data location depends entirely on where the operator deploys the database. An agent reading data from this system and sending it to an LLM endpoint could violate residency requirements if the LLM endpoint is in a different jurisdiction.
- **Compensating Controls**:
  - Document data residency requirements for each deployment and enforce at the infrastructure/network layer
  - Configure agent orchestration layer to filter sensitive data before sending to LLM endpoints
- **Remediation Timeline**: 30–60 days (documentation and policy)
- **Recommendation**: Document data residency requirements and create a data residency policy for agent access. Implement data filtering at the agent orchestration layer to prevent regulated data from crossing jurisdictional boundaries. For self-hosted deployments, ensure database and agent infrastructure are co-located in the same region/jurisdiction.
- **Evidence**: `application/src/main/resources/thingsboard.yml` (database config), `dao/src/main/resources/sql/schema-entities.sql`

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No PII redaction, log scrubbing middleware, or PII masking libraries were found in the codebase. The logging configuration uses `json-file` Docker log driver with size rotation (`max-size: 200m`, `max-file: 30`) but no content filtering. The `thingsboard.yml` transport log configuration (`TB_TRANSPORT_LOG_ENABLED:true`, `TB_TRANSPORT_LOG_MAX_LENGTH:1024`) logs transport messages to telemetry without PII filtering. User names appear in audit logs (`user_name` field in `audit_log` table). No Amazon Macie, regex-based PII scrubbing, or structured log redaction was found.
- **Gap**: PII (user emails, device names, customer names) can appear in application logs, transport logs, and audit logs without redaction. If an agent processes customer data and triggers logging, PII may leak into observable surfaces.
- **Compensating Controls**:
  - Limit log access to authorized personnel only
  - Implement log retention policies to minimize PII exposure window
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement a logging filter/interceptor that redacts known PII patterns (email addresses, user names) from log output. Add PII masking to the audit log `action_data` field for sensitive operations. Consider using a structured logging framework with built-in PII redaction capabilities.
- **Evidence**: `application/src/main/resources/thingsboard.yml` (transport log config, lines 1170–1175), `docker/docker-compose.yml` (json-file log driver), `dao/src/main/resources/sql/schema-entities.sql` (audit_log table with user_name field)

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: ThingsBoard integrates springdoc-openapi-starter-webmvc-ui v2.8.8TB with swagger-annotations-jakarta v2.2.30 to auto-generate OpenAPI documentation from code annotations. The `thingsboard.yml` configuration (lines 1653–1691) enables the Swagger UI at `/api-docs` with `SWAGGER_ENABLED:true` and `default-produces-media-type:application/json`. Controllers use `@ApiOperation` annotations with detailed description text. However, no standalone OpenAPI spec file (`openapi.yaml`, `openapi.json`) is committed to the repository — the spec is generated at runtime only.
- **Gap**: No static, version-controlled API specification file. The spec is only available from a running instance. Agent tool definitions cannot be generated from the repository alone — they require a running ThingsBoard instance.
- **Compensating Controls**:
  - Export the auto-generated OpenAPI spec from a running instance and commit it to the repository
  - Use the springdoc Maven plugin to generate the spec at build time
- **Remediation Timeline**: 7–14 days
- **Recommendation**: Add a build step to generate and commit the OpenAPI specification file. Use the springdoc-openapi-maven-plugin to generate `openapi.json` during the build and version-control it alongside the source code.
- **Evidence**: `pom.xml` (lines 102–103, 1623–1629: springdoc/swagger dependencies), `application/src/main/resources/thingsboard.yml` (lines 1653–1691: springdoc config)

#### API-Q6: Asynchronous Operation Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: ThingsBoard supports asynchronous patterns for several operations. The `RpcV2Controller.java` uses `DeferredResult<ResponseEntity>` for RPC commands with configurable timeouts (`MIN_SERVER_SIDE_RPC_TIMEOUT:5000`, `DEFAULT_SERVER_SIDE_RPC_TIMEOUT:10000`). The `DeviceController.java` uses `DeferredResult` for device claiming operations. The `TelemetryController` supports server-side RPC with async responses. However, for truly long-running operations (bulk import, rule chain deployment, OTA package distribution), there is no job submission + polling pattern — bulk import returns synchronously with results.
- **Gap**: While async patterns exist for RPC operations, long-running operations like bulk device import (`/api/device/bulk_import`) and OTA package distribution lack job-based async patterns with status polling endpoints.
- **Compensating Controls**:
  - Set appropriate timeouts for agent tool calls to long-running endpoints
  - Use the `JobController` for operations that support it
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement a job submission + polling pattern for bulk operations. The existing `JobController.java` suggests some job infrastructure exists — extend it to cover bulk import and other long-running operations.
- **Evidence**: `application/src/main/java/org/thingsboard/server/controller/RpcV2Controller.java` (DeferredResult usage), `application/src/main/java/org/thingsboard/server/controller/DeviceController.java` (DeferredResult for claim), `application/src/main/resources/thingsboard.yml` (RPC timeout configs)

#### STATE-Q2: Queryable Current State — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: ThingsBoard exposes extensive GET endpoints for querying current state. Every entity type (devices, assets, customers, dashboards, alarms, etc.) has dedicated GET endpoints returning current state. The `DeviceController.java` provides `getDeviceById`, `getTenantDevices`, `getCustomerDevices`, and `getDeviceInfoById`. Alarm state is queryable with filters. Telemetry and attribute data is accessible via dedicated endpoints. However, there is no explicit "read-before-write" enforcement — the API does not require or encourage checking current state before performing mutations.
- **Gap**: While state is fully queryable, there is no read-before-write enforcement pattern. An agent could issue write operations without first checking current state, potentially creating inconsistent outcomes.
- **Compensating Controls**:
  - Implement read-before-write patterns in the agent orchestration layer
  - Use the VERSION_CONFLICT error code (35) to detect concurrent modification
- **Remediation Timeline**: 14–30 days (documentation)
- **Recommendation**: Document recommended read-before-write patterns for agent integrations. The existing `ThingsboardErrorCode.VERSION_CONFLICT(35)` suggests some optimistic concurrency exists — document how agents should handle this error.
- **Evidence**: `application/src/main/java/org/thingsboard/server/controller/DeviceController.java`, `common/data/src/main/java/org/thingsboard/server/common/data/exception/ThingsboardErrorCode.java` (VERSION_CONFLICT)

#### AUTH-Q4: Identity Propagation and Delegation — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: ThingsBoard uses JWT tokens for authentication with the `JwtTokenAuthenticationProcessingFilter`. Internal service-to-service communication uses Kafka message queues rather than HTTP, so JWT propagation between microservices is handled through message metadata. The platform supports both JWT bearer tokens and API keys (`ApiKey` prefix) for authentication. However, there is no explicit on-behalf-of flow or token exchange pattern — the system cannot distinguish between an agent acting under its own identity vs. acting on behalf of a specific human user. The `SecurityUser` model captures user context but there is no delegation mechanism.
- **Gap**: No on-behalf-of flow or identity delegation pattern. All API calls are attributed to the authenticated principal (the API key owner), with no mechanism to indicate the agent is acting on behalf of a different user.
- **Compensating Controls**:
  - Create dedicated API keys for agent identities (not shared with human users)
  - Log both the API key identity and the intended user context in the agent orchestration layer
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement a custom header (e.g., `X-On-Behalf-Of`) that agents can use to indicate delegation context. Capture this in audit logs alongside the authenticated principal.
- **Evidence**: `application/src/main/java/org/thingsboard/server/config/ThingsboardSecurityConfiguration.java`, `application/src/main/java/org/thingsboard/server/controller/ApiKeyController.java`

#### AUTH-Q5: Credential Management — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: ThingsBoard configuration (`thingsboard.yml`) uses environment variable references for most sensitive values (e.g., `${SPRING_DATASOURCE_PASSWORD:postgres}`, `${JWT_TOKEN_SIGNING_KEY:thingsboardDefaultSigningKey}`). However, insecure default values are embedded: the JWT signing key defaults to `thingsboardDefaultSigningKey` (line 161), the database password defaults to `postgres` (line 949). No integration with AWS Secrets Manager, HashiCorp Vault, or similar secrets management systems was found. The `.env` files in the `docker/` directory contain environment variable values for container configuration.
- **Gap**: Default credential values are insecure. No secrets management integration. Environment variables are the only mechanism for secret injection, which is better than hardcoding but lacks rotation, versioning, and audit capabilities.
- **Compensating Controls**:
  - Ensure all default values are overridden in production deployments via environment variables
  - Use Docker secrets or Kubernetes secrets for container deployments
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Remove insecure default values from `thingsboard.yml` (especially `thingsboardDefaultSigningKey` and `postgres` password defaults). Integrate with a secrets management system (AWS Secrets Manager, HashiCorp Vault) for credential storage and rotation. Document mandatory credential rotation procedures.
- **Evidence**: `application/src/main/resources/thingsboard.yml` (line 161: JWT signing key default, line 949: database password default), `docker/.env`, `docker/tb-node.env`

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: ThingsBoard provides extensive Docker Compose configurations for local development and testing: 17+ compose files covering PostgreSQL, Cassandra hybrid, Kafka, Valkey (Redis), Prometheus/Grafana monitoring, and EDQS setups. The `msa/black-box-tests/` module contains 128 test Java files with integration test infrastructure (`TestRestClient.java`, `ContainerTestSuite.java`). Test configurations exist at `application/src/test/resources/application-test.properties` and `dao/src/test/resources/application-test.properties`. However, these are developer-oriented test environments, not production-equivalent staging environments with realistic data shape.
- **Gap**: No production-equivalent staging environment with production data shape for agent testing. Docker Compose environments are suitable for development but may not replicate production scale, data volume, or configuration complexity.
- **Compensating Controls**:
  - Use Docker Compose environments with seed data scripts for initial agent testing
  - Create a dedicated staging deployment with anonymized production data for pre-production agent validation
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a staging environment configuration with synthetic but production-representative data (realistic device counts, telemetry volumes, and entity relationships). Document the process for provisioning a staging environment from Docker Compose with seed data.
- **Evidence**: `docker/docker-compose.yml`, `docker/docker-compose.postgres.yml`, `msa/black-box-tests/` (128 test files), `application/src/test/resources/application-test.properties`

#### DATA-Q4: System of Record Designations — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: ThingsBoard is designed as a self-contained IoT platform that serves as the system of record for device management, telemetry, and alarm data within its scope. Entity types (devices, assets, customers, users, dashboards, rule chains) are managed within the platform's PostgreSQL database. However, there is no formal system-of-record designation documented in the codebase. In real deployments, ThingsBoard may coexist with enterprise systems (CRM, ERP, CMDB) that also manage overlapping entity data (e.g., customer records, asset inventories).
- **Gap**: No formal system-of-record designations or master data management documentation. An agent querying both ThingsBoard and an enterprise CRM may encounter conflicting customer records with no resolution mechanism.
- **Compensating Controls**:
  - Document ThingsBoard's role as the SoR for device telemetry and IoT-specific entities
  - Implement data reconciliation logic in the agent orchestration layer for shared entities
- **Remediation Timeline**: 14–30 days (documentation)
- **Recommendation**: Document system-of-record ownership for each entity type (devices → ThingsBoard, customers → CRM, etc.). Create a data ownership matrix for agent consumers.
- **Evidence**: `dao/src/main/resources/sql/schema-entities.sql`, `application/src/main/java/org/thingsboard/server/controller/DeviceController.java`

#### DATA-Q5: Temporal Metadata and Freshness — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: ThingsBoard consistently uses `created_time bigint NOT NULL` across all entity tables in `schema-entities.sql`. Timestamps are stored as epoch milliseconds (bigint), providing timezone-independent storage. The alarm table includes `start_ts`, `end_ts`, `ack_ts`, `clear_ts`, and `assign_ts` for temporal event tracking. However, no `updated_at` or `last_modified` timestamp was found on most entity tables. API responses do not include `Cache-Control`, `X-Data-Age`, or freshness signaling headers. The EDQS (Eventually Consistent Data Query Service) module implies eventual consistency for some queries, but no consistency level is surfaced to API consumers.
- **Gap**: No `updated_at` field on most entities — agents cannot determine when data was last modified. No freshness signaling headers in API responses. The EDQS module introduces eventual consistency without signaling this to consumers.
- **Compensating Controls**:
  - Use the `created_time` field for entities that don't change after creation
  - For mutable entities, query the audit log to determine last modification time
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `updated_time` columns to mutable entity tables. Include freshness headers (`Last-Modified`, `X-Data-Consistency-Level`) in API responses, especially for EDQS-served queries.
- **Evidence**: `dao/src/main/resources/sql/schema-entities.sql` (created_time across all tables), `application/src/main/resources/thingsboard.yml` (EDQS config)

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: ThingsBoard uses SQL migration files for schema versioning (`application/src/main/data/upgrade/basic/schema_update.sql`). API versioning is partially implemented — the `TbUrlConstants.java` defines separate URL prefixes for RPC v1 (`/api/plugins/rpc`) and v2 (`/api/rpc`), indicating version-aware API evolution. Protobuf schemas in `common/proto/src/main/proto/` provide schema evolution support for internal messaging. The CI workflow `check-configuration-files.yml` validates configuration file changes. However, no breaking change detection tools (OpenAPI diff, Pact, buf breaking) are present in CI. The `ThingsboardErrorCode.VERSION_CONFLICT(35)` enum value suggests some versioning awareness.
- **Gap**: No automated API breaking change detection in CI. Schema migrations exist for database evolution, but API contract changes are not automatically validated against consumer expectations. No consumer-driven contract tests.
- **Compensating Controls**:
  - The configuration file check CI workflow provides some change detection for config files
  - Manual review of API changes through PR review process
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add an OpenAPI diff step to the CI pipeline that compares the generated spec against the previous version and flags breaking changes. Consider implementing consumer-driven contract tests using Pact.
- **Evidence**: `application/src/main/java/org/thingsboard/server/controller/TbUrlConstants.java` (v1/v2 URL prefixes), `application/src/main/data/upgrade/basic/schema_update.sql`, `.github/workflows/check-configuration-files.yml`, `common/proto/src/main/proto/`

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No distributed tracing integration (OpenTelemetry, AWS X-Ray, Jaeger) was found in the codebase or `pom.xml` dependencies. The Docker Compose configuration uses `json-file` log driver for structured JSON log output. ThingsBoard has a dedicated `monitoring` module with transport monitoring capabilities (`TbStopWatch.java`, `MonitoringConfig.java`), but this is focused on transport health monitoring (MQTT, CoAP, HTTP, LwM2M) rather than distributed request tracing. No `traceparent` header propagation, `request_id`, or `correlation_id` fields were found in the controller or filter layer.
- **Gap**: No distributed tracing. No correlation IDs linking all log entries for a single request. When an agent-initiated API call triggers rule engine processing and downstream service calls, there is no way to trace the request across services.
- **Compensating Controls**:
  - The `monitoring` module provides basic transport health monitoring
  - Audit logs capture user_id and action_type, providing some after-the-fact tracing for write operations
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Integrate OpenTelemetry Java agent or SDK for distributed tracing across ThingsBoard services. Add a correlation ID filter to the HTTP request pipeline that generates and propagates a request ID through all internal processing. Configure structured JSON logging with correlation ID fields.
- **Evidence**: `pom.xml` (no tracing dependencies), `docker/docker-compose.yml` (json-file log driver), `monitoring/src/main/java/` (transport monitoring module)

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: ThingsBoard includes Prometheus and Grafana integration via `docker/docker-compose.prometheus-grafana.yml` with Prometheus configuration in `docker/monitoring/prometheus/`. The `thingsboard.yml` metrics configuration (lines 2127–2166) supports actuator metrics with `METRICS_ENDPOINTS_EXPOSE:info` (defaulting to info endpoint, not Prometheus). When enabled with `METRICS_ENABLED:true`, it exposes timer percentiles. However, no alerting rules are configured in the Prometheus setup. No PagerDuty, OpsGenie, or alertmanager integration was found. The default metrics endpoint exposure is `info`, not `prometheus`.
- **Gap**: Prometheus/Grafana infrastructure exists but no alerting rules are configured. Metrics endpoint is not exposed for Prometheus by default. No alerting thresholds for API error rates or latency that would detect agent-induced degradation.
- **Compensating Controls**:
  - Enable Prometheus metrics endpoint (`METRICS_ENDPOINTS_EXPOSE=prometheus`)
  - Create Grafana dashboards with manual threshold monitoring
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Enable Prometheus metrics endpoint by default for monitoring deployments. Configure Alertmanager with thresholds for API error rates (>1% 5xx), latency (p99 > 5s), and queue depth. Add alert routing to an incident management system.
- **Evidence**: `docker/docker-compose.prometheus-grafana.yml`, `docker/monitoring/prometheus/`, `application/src/main/resources/thingsboard.yml` (lines 2127–2166: metrics config)

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No Infrastructure-as-Code (Terraform, CloudFormation, CDK, Helm charts, Kustomize) was found in the repository. The deployment infrastructure is defined entirely through Docker Compose files (`docker/docker-compose.yml` and variants) and shell scripts (`docker-install-tb.sh`, `docker-start-services.sh`, etc.). HAProxy configuration for load balancing is defined in `docker/haproxy/`. While Docker Compose provides reproducible deployments, it does not constitute cloud infrastructure governance — there are no IAM role definitions, API Gateway configurations, network policies, or security group rules defined as code.
- **Gap**: No IaC for the cloud infrastructure that would expose ThingsBoard to agents. API gateways, IAM roles, network configurations, and secrets management are not defined as code. No drift detection. No peer review enforcement for infrastructure changes (beyond Docker Compose file changes).
- **Compensating Controls**:
  - Docker Compose provides reproducible local/development deployments
  - The CI workflow validates configuration file changes
- **Remediation Timeline**: 60–120 days
- **Recommendation**: Create IaC definitions (Terraform, CDK, or CloudFormation) for the production deployment infrastructure including API Gateway, IAM roles, network configurations, and secrets management. Implement drift detection using AWS Config or equivalent.
- **Evidence**: No `.tf`, `.tfvars`, `cdk.json`, `kustomization.yaml`, or `Chart.yaml` files found. `docker/docker-compose.yml` (deployment config), `docker/haproxy/` (load balancer config)

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The repository contains 3 GitHub Actions workflows: `atx-transform.yml` (transformation tooling), `check-configuration-files.yml` (validates thingsboard.yml and transport config changes), and `license-header-format.yml` (license header enforcement). None of these workflows include build, test, or deployment steps. No API contract testing (Pact, OpenAPI validation, schema comparison), no automated build pipeline, and no deployment automation was found in the repository CI/CD configuration. The `msa/black-box-tests/` module contains integration tests but there is no CI workflow that runs them.
- **Gap**: No CI/CD pipeline for building, testing, or deploying the application. No API contract testing or breaking change detection. The 754 test files in the repository are not executed in any visible CI pipeline.
- **Compensating Controls**:
  - The check-configuration-files workflow provides basic validation of config changes
  - Tests can be run manually during development
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement a CI pipeline that builds the project, runs unit and integration tests, generates the OpenAPI spec, and validates API contracts against the previous version. Add API contract tests using Pact or OpenAPI diff tooling.
- **Evidence**: `.github/workflows/check-configuration-files.yml`, `.github/workflows/license-header-format.yml`, `.github/workflows/atx-transform.yml`

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No automated rollback capability was found. The deployment model is based on Docker Compose with manual shell scripts (`docker-update-service.sh`, `docker-upgrade-tb.sh`). No blue/green deployment, canary deployment, CodeDeploy rollback triggers, Helm rollback, or feature flag system was found. Database schema upgrades (`schema_update.sql`) appear to be forward-only with no down migration scripts.
- **Gap**: No automated rollback mechanism. If a deployment breaks agent-facing APIs, manual intervention is required to restore the previous version. Database schema migrations are forward-only.
- **Compensating Controls**:
  - Docker image tagging allows manual rollback to previous image versions
  - Database backups before upgrades allow manual restoration
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement blue/green or canary deployment strategy. Create rollback procedures documented as runbooks. Add down migration scripts for database schema changes. Consider implementing feature flags for gradual rollout of API changes.
- **Evidence**: `docker/docker-update-service.sh`, `docker/docker-upgrade-tb.sh`, `application/src/main/data/upgrade/basic/schema_update.sql`

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The repository contains 754 test files including unit tests across all modules and 128 black-box integration test files in `msa/black-box-tests/`. The `TestRestClient.java` in the black-box tests module provides a REST API test client. However, no CI pipeline executes these tests. There are no visible API contract tests (Pact), no Postman/Newman collections, and no explicit API test coverage measurement. The test infrastructure exists but is not integrated into automated CI.
- **Gap**: Tests exist but are not executed in CI. No API contract test coverage. No measurement of which API endpoints are covered by tests vs. untested.
- **Compensating Controls**:
  - The existing test infrastructure can be activated with minimal CI pipeline work
  - Black-box tests provide integration-level API testing when run manually
- **Remediation Timeline**: 14–30 days (to integrate existing tests into CI)
- **Recommendation**: Create a CI pipeline step that runs the existing test suites. Implement API endpoint coverage tracking. Add dedicated API contract tests for the endpoints agents will consume.
- **Evidence**: `msa/black-box-tests/` (128 test files), `msa/black-box-tests/src/test/java/org/thingsboard/server/msa/TestRestClient.java`, `.github/workflows/` (no test execution workflows)

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No encryption-at-rest configuration was found in the codebase. The `thingsboard.yml` configuration references database connection URLs for PostgreSQL and Cassandra but includes no KMS key references, encryption configuration, or encrypted storage settings. The `schema-entities.sql` defines sensitive data fields (credentials, secrets) as plain varchar columns. No `kms_key_id`, customer-managed KMS keys, or transparent data encryption (TDE) configuration was found. Encryption at rest is delegated entirely to the deployment infrastructure (e.g., encrypted EBS volumes, RDS encryption), but no guidance or configuration for this exists in the repository.
- **Gap**: No encryption-at-rest configuration in the application or its deployment artifacts. Sensitive data (device credentials, user passwords, OAuth2 secrets) stored in the database relies on the infrastructure layer for encryption.
- **Compensating Controls**:
  - Deploy on infrastructure with encryption at rest enabled (e.g., encrypted RDS, encrypted EBS volumes)
  - Use PostgreSQL's built-in pgcrypto extension for field-level encryption of the most sensitive columns
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document encryption-at-rest requirements for production deployments. Create IaC templates that enforce encrypted storage for all data stores. Consider implementing field-level encryption for the most sensitive data (device credentials, OAuth2 secrets) using application-level encryption.
- **Evidence**: `application/src/main/resources/thingsboard.yml` (database config, no encryption settings), `dao/src/main/resources/sql/schema-entities.sql` (plain varchar for sensitive fields)

## INFOs — Architecture and Design Inputs

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: ThingsBoard's write endpoints use a save-or-update pattern where `POST /api/device` creates or updates based on the presence of an `id` field. Device names are unique per tenant, and `NameConflictPolicy` (FAIL, REPLACE, etc.) controls duplicate handling. The `VERSION_CONFLICT(35)` error code suggests some conflict detection. However, no explicit idempotency key support (e.g., `Idempotency-Key` header) was found in write endpoints.
- **Implication**: If agent scope expands to write-enabled, the lack of idempotency keys means retried POST requests could create duplicate entities. The `NameConflictPolicy` parameter provides partial mitigation for device creation but not for other entity types.
- **Recommendation**: When expanding to write-enabled scope, implement idempotency key support on all POST endpoints. The existing `NameConflictPolicy` pattern can serve as a template.
- **Evidence**: `application/src/main/java/org/thingsboard/server/controller/DeviceController.java` (NameConflictPolicy), `common/data/src/main/java/org/thingsboard/server/common/data/exception/ThingsboardErrorCode.java` (VERSION_CONFLICT)

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: ThingsBoard produces JSON responses exclusively for its REST API. The `thingsboard.yml` configures `default-produces-media-type:application/json` for springdoc. All controllers return Java objects serialized to JSON via Jackson. Protobuf (`.proto` files in `common/proto/`) is used for internal inter-service messaging via Kafka, not for external API responses.
- **Implication**: JSON-only responses are ideal for LLM-based agents. No additional parsing or format conversion is needed. Protobuf internal messaging does not affect agent integration.
- **Recommendation**: No action needed. JSON is the optimal format for agent consumption.
- **Evidence**: `application/src/main/resources/thingsboard.yml` (springdoc config), `pom.xml` (Jackson dependencies)

### API-Q7: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: ThingsBoard has extensive event emission capabilities. The rule engine processes messages through Kafka topics for state changes. WebSocket subscriptions (`/api/ws/**`) provide real-time push notifications for telemetry updates, alarm state changes, and entity modifications. The rule engine supports webhook notification nodes that can call external endpoints on state changes. Edge synchronization uses event-driven patterns via the `edge.proto` specification.
- **Implication**: Agents can subscribe to real-time state changes via WebSocket or configure rule engine nodes to emit webhooks. This enables proactive agent patterns (e.g., respond to alarm creation, device connectivity changes) without polling.
- **Recommendation**: Document the WebSocket subscription API and rule engine webhook node configuration for agent integration patterns.
- **Evidence**: `application/src/main/java/org/thingsboard/server/config/ThingsboardSecurityConfiguration.java` (WS_ENTRY_POINT), `common/edge-api/src/main/proto/edge.proto`, `common/queue/` (Kafka integration)

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: ThingsBoard implements comprehensive rate limiting via `DefaultRateLimitService` using Bucket4j (v8.10.1). Rate limits are configurable per tenant profile, per API type, and per transport. The `thingsboard.yml` configures rate limits for WebSocket subscriptions, REST password reset, transport IP limits, and device state changes. The `ThingsboardErrorCode.TOO_MANY_REQUESTS(33)` provides a machine-readable error code when limits are hit. However, the API does not return `X-RateLimit-Remaining`, `X-RateLimit-Limit`, or `Retry-After` headers in responses.
- **Implication**: Agents will receive HTTP 429 with error code 33 when rate-limited, but cannot proactively self-throttle because remaining quota is not surfaced in response headers. Agents must implement backoff on 429 responses.
- **Recommendation**: Add `X-RateLimit-Remaining`, `X-RateLimit-Limit`, and `Retry-After` headers to API responses. This allows agents to self-throttle before hitting limits.
- **Evidence**: `common/cache/src/main/java/org/thingsboard/server/cache/limits/DefaultRateLimitService.java`, `application/src/main/resources/thingsboard.yml` (rate limit configs), `common/data/src/main/java/org/thingsboard/server/common/data/exception/ThingsboardErrorCode.java` (TOO_MANY_REQUESTS)

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: ThingsBoard has limited optimistic concurrency support. The `ThingsboardErrorCode.VERSION_CONFLICT(35)` enum value indicates version conflict detection exists. ETags are used for resource management (`RESOURCE_ETAG_COLUMN` in `ModelConstants.java`). However, most entity tables in `schema-entities.sql` do not include a version field for optimistic locking. The `attribute_kv` table uses a sequence (`attribute_kv_version_seq`) for versioning.
- **Implication**: For read-only agent scope, concurrency controls are not critical. If expanding to write-enabled, the lack of widespread optimistic locking could lead to lost updates when multiple writers (agent + human) modify the same entity.
- **Recommendation**: When planning write-enabled scope, add version fields to key entity tables and implement ETag-based conditional updates.
- **Evidence**: `common/data/src/main/java/org/thingsboard/server/common/data/exception/ThingsboardErrorCode.java` (VERSION_CONFLICT), `dao/src/main/java/org/thingsboard/server/dao/model/ModelConstants.java` (RESOURCE_ETAG_COLUMN)

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: ThingsBoard's rate limiting system (`DefaultRateLimitService`) operates per tenant and per API type, which provides some blast radius containment. The `LimitedApi` enum controls different categories of API calls. However, there are no configurable transaction-level limits (e.g., max records modified per operation, max bulk import size) beyond the rate limits. The `PayloadSizeFilter` limits request body size, providing some containment.
- **Implication**: For read-only agent scope, transaction limits are not critical. If expanding to write-enabled, an agent could execute correct-but-catastrophic bulk operations without per-operation limits.
- **Recommendation**: When planning write-enabled scope, implement configurable per-operation limits (max bulk import records, max delete batch size) as tenant profile settings.
- **Evidence**: `common/cache/src/main/java/org/thingsboard/server/cache/limits/DefaultRateLimitService.java`, `application/src/main/java/org/thingsboard/server/config/ThingsboardSecurityConfiguration.java` (PayloadSizeFilter)

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: ThingsBoard has some state machine patterns. Alarms have acknowledgement and clear states (`acknowledged`, `cleared` boolean fields, `ack_ts`, `clear_ts` timestamps). Device provisioning supports claiming workflows with a two-step pattern (claim → confirm). However, there is no general-purpose draft/pending state for entity creation or modification. Devices, assets, and other entities are created in their final state immediately.
- **Implication**: For read-only agent scope, draft states are not needed. If expanding to write-enabled, the absence of draft states means agents cannot propose changes for human review before committing.
- **Recommendation**: When planning write-enabled scope, consider implementing a draft/pending state pattern for high-stakes entity changes (device deletion, rule chain modification).
- **Evidence**: `dao/src/main/resources/sql/schema-entities.sql` (alarm table with acknowledged/cleared fields), `application/src/main/java/org/thingsboard/server/controller/DeviceController.java` (claim flow)

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable approval gate mechanism was found. The rule engine supports custom workflow logic, but there is no built-in approval workflow pattern for API operations. Operations execute immediately upon API call without approval gates.
- **Implication**: For read-only agent scope, approval gates are not needed. If expanding to write-enabled, consider adding human-in-the-loop approval for high-risk operations (device deletion, rule chain modification, bulk operations).
- **Recommendation**: When planning write-enabled scope, implement approval gates using the rule engine notification system. The existing `NotificationRuleProcessor` and notification targets could be extended to support approval workflows.
- **Evidence**: `application/src/main/resources/thingsboard.yml` (notification system config)

### DATA-Q3: Selective Query Support

- **Severity**: INFO
- **Finding**: ThingsBoard implements comprehensive pagination, filtering, and sorting through the `PageLink`/`PageData` pattern used across all list endpoints. The `PageLink` class supports `pageSize`, `page`, `textSearch`, and `sortOrder` parameters. All entity list endpoints (`getTenantDevices`, `getCustomerDevices`, `getEdgeDevices`, etc.) require pagination parameters. The `EntityQueryController` supports complex entity queries with filters. Result sets are bounded by the `pageSize` parameter. This is evaluated as INFO because the implementation is strong — no gap.
- **Implication**: Agents can efficiently query data with bounded result sets. The pagination pattern prevents context window exhaustion from unbounded queries.
- **Recommendation**: Document recommended `pageSize` values for agent integrations (e.g., 100 for entity lists, 1000 for telemetry).
- **Evidence**: `common/data/src/main/java/org/thingsboard/server/common/data/page/PageLink.java`, `common/data/src/main/java/org/thingsboard/server/common/data/page/PageData.java`, `application/src/main/java/org/thingsboard/server/controller/DeviceController.java`

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality scoring, completeness metrics, or data profiling capabilities were found in the codebase. ThingsBoard does not expose data quality indicators for telemetry or entity data. The platform focuses on data ingestion and storage without quality assessment. No null rate monitoring, duplicate detection, or data freshness SLAs were found.
- **Implication**: Agents acting on potentially incomplete or stale device telemetry cannot assess data quality. This is a planning input — not a deployment gate — but affects agent reasoning quality for data-intensive use cases.
- **Recommendation**: Consider implementing data quality metrics as custom attributes or telemetry (e.g., telemetry completeness rate per device, time since last telemetry update). These can be computed by rule engine nodes.
- **Evidence**: `application/src/main/resources/thingsboard.yml` (no data quality config)

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: ThingsBoard uses consistently semantic, human-readable field names throughout its schema and API. Database columns use clear names: `created_time`, `tenant_id`, `customer_id`, `entity_type`, `entity_name`, `device_profile_id`, `action_type`, `action_status`. API response objects mirror these names. Java class names are descriptive (`DeviceInfo`, `PageData`, `AlarmController`). No legacy abbreviations or cryptic codes were found.
- **Implication**: Field names are LLM-friendly. Agents can reason about field meanings from names alone without a data dictionary. This accelerates tool definition and reduces prompt engineering complexity.
- **Recommendation**: No action needed. Naming conventions are excellent for agent consumption.
- **Evidence**: `dao/src/main/resources/sql/schema-entities.sql`, `application/src/main/java/org/thingsboard/server/controller/DeviceController.java`

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No formal data catalog or metadata layer (AWS Glue Data Catalog, Collibra, Alation, DataHub) was found. The Swagger/OpenAPI auto-generated documentation serves as the closest equivalent for API schema discovery. The SQL schema files (`schema-entities.sql`) serve as the ground truth for data structure. The `@ApiOperation` annotations provide semantic descriptions for API endpoints.
- **Implication**: Agent tool builders must rely on the auto-generated Swagger documentation and SQL schema files to understand what data the system holds. A formal data catalog would accelerate discovery.
- **Recommendation**: Consider publishing the auto-generated OpenAPI spec as a static artifact alongside the codebase. For large deployments, consider integrating with a data catalog tool.
- **Evidence**: `application/src/main/resources/thingsboard.yml` (springdoc config), `dao/src/main/resources/sql/schema-entities.sql`

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: ThingsBoard's metrics configuration (`thingsboard.yml` lines 2127–2166) focuses on system metrics (CPU, memory, actuator endpoints). The `monitoring` module provides transport health monitoring (MQTT, CoAP, HTTP connectivity). No custom business outcome metrics (device connectivity rates, telemetry ingestion rates, alarm resolution times, rule engine processing success rates) are published as custom CloudWatch or Prometheus metrics. System info metrics (`persist_frequency`, `ttl`) track infrastructure health but not business KPIs.
- **Implication**: When agents consume the system, business metrics (device connectivity rate, alarm resolution time) become the primary signal for whether agent interactions produce good outcomes. Without these metrics, agent effectiveness cannot be measured.
- **Recommendation**: Implement custom Prometheus metrics for key business outcomes: device connectivity rate, average alarm resolution time, telemetry ingestion rate per device profile, rule engine message processing success rate.
- **Evidence**: `application/src/main/resources/thingsboard.yml` (lines 2127–2166: metrics config), `monitoring/src/main/java/` (transport monitoring)

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: BLOCKER — **PASS** (no gap found)
- **Finding**: ThingsBoard exposes a comprehensive, documented REST API with 64+ controller classes under `application/src/main/java/org/thingsboard/server/controller/`. Controllers use `@RestController`, `@RequestMapping("/api")`, `@GetMapping`, `@PostMapping`, `@DeleteMapping`, `@PutMapping`, and `@RequestMapping` annotations. Every endpoint has `@ApiOperation` annotations with detailed description text. The API covers device management, asset management, customer management, alarm handling, telemetry, rule engine, RPC, dashboard, user administration, and more. No direct database access, file-based exchange, or UI automation patterns were found for integration.
- **Gap**: None. The REST API is well-documented and comprehensive.
- **Recommendation**: None — this is a strength.
- **Evidence**: `application/src/main/java/org/thingsboard/server/controller/DeviceController.java`, `application/src/main/java/org/thingsboard/server/controller/BaseController.java`, all 64+ controller files

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section above (API-Q2).
- **Gap**: No static, version-controlled API specification file.
- **Recommendation**: Add build-time OpenAPI spec generation.
- **Evidence**: `pom.xml` (springdoc dependencies), `application/src/main/resources/thingsboard.yml` (springdoc config)

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY — **PASS** (no gap found)
- **Finding**: ThingsBoard implements a well-structured error response model. `ThingsboardErrorResponse.java` returns JSON with `status` (HTTP code), `message` (human-readable), `errorCode` (machine-readable `ThingsboardErrorCode` enum), and `timestamp`. The `ThingsboardErrorCode` enum provides 15 distinct error codes: GENERAL(2), AUTHENTICATION(10), JWT_TOKEN_EXPIRED(11), CREDENTIALS_EXPIRED(15), PERMISSION_DENIED(20), INVALID_ARGUMENTS(30), BAD_REQUEST_PARAMS(31), ITEM_NOT_FOUND(32), TOO_MANY_REQUESTS(33), TOO_MANY_UPDATES(34), VERSION_CONFLICT(35), SUBSCRIPTION_VIOLATION(40), ENTITIES_LIMIT_EXCEEDED(41), PASSWORD_VIOLATION(45), DATABASE(46). This enables agents to distinguish retriable errors (33: rate limit) from terminal errors (20: permission denied).
- **Gap**: None. Error responses are structured and machine-readable.
- **Recommendation**: None — error handling is well-designed for agent consumption.
- **Evidence**: `application/src/main/java/org/thingsboard/server/exception/ThingsboardErrorResponse.java`, `common/data/src/main/java/org/thingsboard/server/common/data/exception/ThingsboardErrorCode.java`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: See INFOs section above (API-Q4).
- **Gap**: No explicit idempotency key support.
- **Recommendation**: Plan for idempotency keys when expanding to write-enabled scope.
- **Evidence**: `application/src/main/java/org/thingsboard/server/controller/DeviceController.java`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: See INFOs section above (API-Q5).
- **Gap**: None.
- **Recommendation**: No action needed.
- **Evidence**: `application/src/main/resources/thingsboard.yml`

#### API-Q6: Asynchronous Operation Support
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section above (API-Q6). Trigger: service has operations >30s (RPC, bulk import). Triggered for stateful-crud archetype.
- **Gap**: Long-running operations lack job-based async patterns.
- **Recommendation**: Implement job submission + polling for bulk operations.
- **Evidence**: `application/src/main/java/org/thingsboard/server/controller/RpcV2Controller.java`

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: See INFOs section above (API-Q7). Trigger: service has state changes (stateful-crud). Triggered.
- **Gap**: None — event emission capabilities are present.
- **Recommendation**: Document WebSocket and webhook patterns for agent integration.
- **Evidence**: `application/src/main/java/org/thingsboard/server/config/ThingsboardSecurityConfiguration.java`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: See INFOs section above (API-Q8).
- **Gap**: No rate limit headers in responses.
- **Recommendation**: Add X-RateLimit-* headers.
- **Evidence**: `common/cache/src/main/java/org/thingsboard/server/cache/limits/DefaultRateLimitService.java`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER — **PASS** (no gap found)
- **Finding**: ThingsBoard supports machine identity authentication through multiple mechanisms. The `ThingsboardSecurityConfiguration.java` configures: (1) JWT token authentication via `JwtTokenAuthenticationProcessingFilter` with `X-Authorization` and `Authorization` headers, (2) API Key authentication via `ApiKeyTokenAuthenticationProcessingFilter` with `ApiKey` prefix, (3) OAuth2 login via Spring Security OAuth2 integration. The `ApiKeyController.java` provides full CRUD for API keys with enable/disable capability. API keys are tied to user identities, providing principal attribution in audit logs (`user_id`, `user_name` fields in `audit_log` table). The `RestAuthenticationProvider` handles credential-based login.
- **Gap**: None. Machine identity authentication is well-supported with principal attribution.
- **Recommendation**: Create dedicated user accounts for agent identities with API keys. Do not reuse human user API keys for agents.
- **Evidence**: `application/src/main/java/org/thingsboard/server/config/ThingsboardSecurityConfiguration.java`, `application/src/main/java/org/thingsboard/server/controller/ApiKeyController.java`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: See RISKs section above (AUTH-Q2).
- **Gap**: No mechanism to create narrowly scoped agent identities.
- **Recommendation**: Introduce custom role definitions with granular permission sets.
- **Evidence**: `application/src/main/java/org/thingsboard/server/service/security/permission/TenantAdminPermissions.java`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY — **PASS** (no gap found)
- **Finding**: ThingsBoard implements action-level authorization through the `Operation` enum with 17 distinct operations: `ALL`, `CREATE`, `READ`, `WRITE`, `DELETE`, `ASSIGN_TO_CUSTOMER`, `UNASSIGN_FROM_CUSTOMER`, `RPC_CALL`, `READ_CREDENTIALS`, `WRITE_CREDENTIALS`, `READ_ATTRIBUTES`, `WRITE_ATTRIBUTES`, `READ_TELEMETRY`, `WRITE_TELEMETRY`, `CLAIM_DEVICES`, `ASSIGN_TO_TENANT`, `READ_CALCULATED_FIELD`, `WRITE_CALCULATED_FIELD`. Controllers check specific operations: `checkDeviceId(deviceId, Operation.READ)` for read, `checkDeviceId(deviceId, Operation.DELETE)` for delete, `checkDeviceId(deviceId, Operation.WRITE)` for update. The `Resource` enum maps 30+ resource types. Permission checkers in `CustomerUserPermissions`, `TenantAdminPermissions`, and `SysAdminPermissions` define per-role, per-resource, per-operation permissions.
- **Gap**: None. Action-level authorization is well-implemented.
- **Recommendation**: None — this is a strength.
- **Evidence**: `application/src/main/java/org/thingsboard/server/service/security/permission/Operation.java`, `application/src/main/java/org/thingsboard/server/service/security/permission/Resource.java`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section above (AUTH-Q4).
- **Gap**: No on-behalf-of flow.
- **Recommendation**: Implement delegation context header.
- **Evidence**: `application/src/main/java/org/thingsboard/server/config/ThingsboardSecurityConfiguration.java`

#### AUTH-Q5: Credential Management
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section above (AUTH-Q5).
- **Gap**: Insecure defaults, no secrets management integration.
- **Recommendation**: Remove insecure defaults, integrate secrets management.
- **Evidence**: `application/src/main/resources/thingsboard.yml`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: See RISKs section above (AUTH-Q6).
- **Gap**: Audit logs are mutable.
- **Recommendation**: Enable Elasticsearch sink with write-once indices.
- **Evidence**: `dao/src/main/resources/sql/schema-entities.sql`, `application/src/main/resources/thingsboard.yml`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY — **PASS** (no gap found)
- **Finding**: ThingsBoard supports immediate agent identity suspension through the `ApiKeyController.enableApiKey` endpoint (`PUT /api/apiKey/{id}/enabled/{enabledValue}`), which can disable an API key without deleting it. The `deleteApiKey` endpoint (`DELETE /api/apiKey/{id}`) provides permanent revocation. These operations are available to `SYS_ADMIN`, `TENANT_ADMIN`, and `CUSTOMER_USER` with appropriate permissions. Additionally, the underlying user account can be disabled, which would invalidate all API keys associated with that user.
- **Gap**: None. Agent identity suspension is supported.
- **Recommendation**: Document the API key disable endpoint as the primary mechanism for agent identity suspension. Create runbook procedures for emergency agent suspension.
- **Evidence**: `application/src/main/java/org/thingsboard/server/controller/ApiKeyController.java` (enableApiKey, deleteApiKey methods)

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: See RISKs section above (STATE-Q1).
- **Gap**: No compensation or rollback mechanism.
- **Recommendation**: Plan saga patterns for write-enabled scope expansion.
- **Evidence**: `application/src/main/java/org/thingsboard/server/controller/DeviceController.java`

#### STATE-Q2: Queryable Current State
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section above (STATE-Q2). Trigger: service has persistent state (stateful-crud). Triggered.
- **Gap**: No read-before-write enforcement.
- **Recommendation**: Document read-before-write patterns.
- **Evidence**: `application/src/main/java/org/thingsboard/server/controller/DeviceController.java`

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: See INFOs section above (STATE-Q3).
- **Gap**: Limited optimistic locking.
- **Recommendation**: Add version fields when expanding to write-enabled scope.
- **Evidence**: `common/data/src/main/java/org/thingsboard/server/common/data/exception/ThingsboardErrorCode.java`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: See RISKs section above (STATE-Q4). Trigger: service has external dependencies. Triggered.
- **Gap**: No circuit breakers for external dependency calls.
- **Recommendation**: Add Resilience4j circuit breakers.
- **Evidence**: `pom.xml`, `application/src/main/resources/thingsboard.yml`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY — **PASS** (no gap found)
- **Finding**: ThingsBoard implements comprehensive, multi-layer rate limiting. The `DefaultRateLimitService` uses Bucket4j (v8.10.1) with per-tenant, per-API rate limits configurable via tenant profiles. The `RateLimitProcessingFilter` is integrated into the Spring Security filter chain. Rate limits are configured for: WebSocket subscriptions per tenant/user, REST API password reset, transport IP-based limits (`TB_TRANSPORT_IP_RATE_LIMITS_ENABLED`), wrong credentials per IP (`TB_TRANSPORT_MAX_WRONG_CREDENTIALS_PER_IP:10`), device state rate limits (`1:1,30:60,60:3600`), Cassandra query rate limits, and rule engine debug mode rate limits. The `ThingsboardErrorCode.TOO_MANY_REQUESTS(33)` error code signals rate limiting to consumers.
- **Gap**: None. Rate limiting is comprehensive and configurable.
- **Recommendation**: Configure tenant profile rate limits appropriate for agent traffic patterns. Document expected agent request rates and configure limits accordingly.
- **Evidence**: `common/cache/src/main/java/org/thingsboard/server/cache/limits/DefaultRateLimitService.java`, `application/src/main/resources/thingsboard.yml` (multiple rate limit configs), `application/src/main/java/org/thingsboard/server/config/ThingsboardSecurityConfiguration.java` (RateLimitProcessingFilter)

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: See INFOs section above (STATE-Q6).
- **Gap**: No per-operation transaction limits.
- **Recommendation**: Plan transaction limits for write-enabled scope.
- **Evidence**: `common/cache/src/main/java/org/thingsboard/server/cache/limits/DefaultRateLimitService.java`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path. Priority is P2 — not triggered.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: See INFOs section above (HITL-Q1).
- **Gap**: No general-purpose draft/pending state.
- **Recommendation**: Plan draft states for write-enabled scope.
- **Evidence**: `dao/src/main/resources/sql/schema-entities.sql`

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: See INFOs section above (HITL-Q2).
- **Gap**: No approval gate mechanism.
- **Recommendation**: Plan approval gates for write-enabled scope.
- **Evidence**: `application/src/main/resources/thingsboard.yml`

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section above (HITL-Q3).
- **Gap**: No production-equivalent staging environment.
- **Recommendation**: Create staging environment with representative data.
- **Evidence**: `docker/docker-compose.yml`, `msa/black-box-tests/`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: See BLOCKERs section above (DATA-Q1).
- **Gap**: No data classification or field-level tagging.
- **Recommendation**: Create data classification inventory.
- **Evidence**: `dao/src/main/resources/sql/schema-entities.sql`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: See RISKs section above (DATA-Q2).
- **Gap**: No data residency controls.
- **Recommendation**: Document and enforce data residency policies.
- **Evidence**: `application/src/main/resources/thingsboard.yml`

#### DATA-Q3: Selective Query Support
- **Severity**: INFO
- **Finding**: See INFOs section above (DATA-Q3). Trigger: service has list/query endpoints with potentially unbounded results. Triggered for stateful-crud. Evaluated as INFO because implementation is strong.
- **Gap**: None — comprehensive pagination support.
- **Recommendation**: Document recommended pageSize values.
- **Evidence**: `common/data/src/main/java/org/thingsboard/server/common/data/page/PageLink.java`

#### DATA-Q4: System of Record Designations
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section above (DATA-Q4). Trigger: service has persistent state (stateful-crud). Triggered.
- **Gap**: No formal SoR designations.
- **Recommendation**: Document data ownership matrix.
- **Evidence**: `dao/src/main/resources/sql/schema-entities.sql`

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section above (DATA-Q5). Trigger: service has persistent state (stateful-crud). Triggered.
- **Gap**: No updated_at fields, no freshness headers.
- **Recommendation**: Add updated_time columns and freshness headers.
- **Evidence**: `dao/src/main/resources/sql/schema-entities.sql`

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: See RISKs section above (DATA-Q6).
- **Gap**: No PII redaction in logs.
- **Recommendation**: Implement logging filter with PII masking.
- **Evidence**: `application/src/main/resources/thingsboard.yml`, `docker/docker-compose.yml`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: See INFOs section above (DATA-Q7).
- **Gap**: No data quality metrics.
- **Recommendation**: Implement data quality telemetry via rule engine.
- **Evidence**: `application/src/main/resources/thingsboard.yml`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section above (DISC-Q1).
- **Gap**: No automated breaking change detection in CI.
- **Recommendation**: Add OpenAPI diff to CI pipeline.
- **Evidence**: `application/src/main/java/org/thingsboard/server/controller/TbUrlConstants.java`, `.github/workflows/check-configuration-files.yml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: See INFOs section above (DISC-Q2).
- **Gap**: None — field names are excellent.
- **Recommendation**: No action needed.
- **Evidence**: `dao/src/main/resources/sql/schema-entities.sql`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: See INFOs section above (DISC-Q3).
- **Gap**: No formal data catalog.
- **Recommendation**: Publish static OpenAPI spec alongside code.
- **Evidence**: `application/src/main/resources/thingsboard.yml`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section above (OBS-Q1).
- **Gap**: No distributed tracing, no correlation IDs.
- **Recommendation**: Integrate OpenTelemetry.
- **Evidence**: `pom.xml`, `docker/docker-compose.yml`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section above (OBS-Q2).
- **Gap**: No alerting rules configured.
- **Recommendation**: Configure Alertmanager thresholds.
- **Evidence**: `docker/docker-compose.prometheus-grafana.yml`, `application/src/main/resources/thingsboard.yml`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: See INFOs section above (OBS-Q3).
- **Gap**: No business outcome metrics.
- **Recommendation**: Implement custom Prometheus metrics for business KPIs.
- **Evidence**: `application/src/main/resources/thingsboard.yml`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section above (ENG-Q1).
- **Gap**: No IaC for cloud infrastructure.
- **Recommendation**: Create Terraform/CDK definitions.
- **Evidence**: No IaC files found. `docker/docker-compose.yml`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section above (ENG-Q2).
- **Gap**: No CI/CD pipeline for build/test/deploy.
- **Recommendation**: Implement CI pipeline with API contract testing.
- **Evidence**: `.github/workflows/`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section above (ENG-Q3).
- **Gap**: No automated rollback.
- **Recommendation**: Implement blue/green deployment.
- **Evidence**: `docker/docker-update-service.sh`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section above (ENG-Q4). Trigger: always evaluated. Triggered.
- **Gap**: Tests exist but not in CI.
- **Recommendation**: Integrate existing tests into CI.
- **Evidence**: `msa/black-box-tests/`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section above (ENG-Q5). Trigger: service has persistent data stores. Triggered.
- **Gap**: No encryption-at-rest configuration.
- **Recommendation**: Document encryption requirements, create IaC with encrypted storage.
- **Evidence**: `application/src/main/resources/thingsboard.yml`

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| application/src/main/java/org/thingsboard/server/controller/DeviceController.java | API-Q1, API-Q4, API-Q6, STATE-Q1, STATE-Q2, DATA-Q3, DATA-Q4, DISC-Q2, HITL-Q1 |
| application/src/main/java/org/thingsboard/server/controller/BaseController.java | API-Q1 |
| application/src/main/java/org/thingsboard/server/controller/RpcV2Controller.java | API-Q6, STATE-Q1 |
| application/src/main/java/org/thingsboard/server/controller/ApiKeyController.java | AUTH-Q1, AUTH-Q2, AUTH-Q4, AUTH-Q7 |
| application/src/main/java/org/thingsboard/server/controller/TbUrlConstants.java | DISC-Q1 |
| application/src/main/java/org/thingsboard/server/exception/ThingsboardErrorResponse.java | API-Q3 |
| application/src/main/java/org/thingsboard/server/config/ThingsboardSecurityConfiguration.java | AUTH-Q1, AUTH-Q4, API-Q7, STATE-Q5, STATE-Q6 |
| application/src/main/java/org/thingsboard/server/service/security/permission/Operation.java | AUTH-Q2, AUTH-Q3 |
| application/src/main/java/org/thingsboard/server/service/security/permission/Resource.java | AUTH-Q3 |
| application/src/main/java/org/thingsboard/server/service/security/permission/TenantAdminPermissions.java | AUTH-Q2 |
| common/data/src/main/java/org/thingsboard/server/common/data/exception/ThingsboardErrorCode.java | API-Q3, API-Q4, API-Q8, STATE-Q2, STATE-Q3 |
| common/cache/src/main/java/org/thingsboard/server/cache/limits/DefaultRateLimitService.java | API-Q8, STATE-Q5, STATE-Q6 |
| common/data/src/main/java/org/thingsboard/server/common/data/page/PageLink.java | DATA-Q3 |
| common/data/src/main/java/org/thingsboard/server/common/data/page/PageData.java | DATA-Q3 |
| dao/src/main/java/org/thingsboard/server/dao/model/ModelConstants.java | STATE-Q3 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| application/src/main/resources/thingsboard.yml | API-Q2, API-Q5, API-Q6, API-Q8, AUTH-Q5, AUTH-Q6, STATE-Q1, STATE-Q4, STATE-Q5, STATE-Q6, DATA-Q1, DATA-Q2, DATA-Q5, DATA-Q6, DATA-Q7, DISC-Q3, OBS-Q2, OBS-Q3, HITL-Q2, ENG-Q5 |
| docker/.env | AUTH-Q5 |
| docker/tb-node.env | AUTH-Q5 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| .github/workflows/check-configuration-files.yml | DISC-Q1, ENG-Q2 |
| .github/workflows/license-header-format.yml | ENG-Q2 |
| .github/workflows/atx-transform.yml | ENG-Q2 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| docker/docker-compose.yml | STATE-Q4, DATA-Q6, OBS-Q1, ENG-Q1, HITL-Q3 |
| docker/docker-compose.prometheus-grafana.yml | OBS-Q2 |
| docker/docker-compose.postgres.yml | HITL-Q3 |
| docker/docker-update-service.sh | ENG-Q3 |
| docker/docker-upgrade-tb.sh | ENG-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| pom.xml | API-Q2, API-Q5, STATE-Q4, OBS-Q1 |

### SQL Schemas
| File | Questions Referenced |
|------|---------------------|
| dao/src/main/resources/sql/schema-entities.sql | AUTH-Q6, DATA-Q1, DATA-Q2, DATA-Q4, DATA-Q5, DATA-Q6, DISC-Q1, DISC-Q2, HITL-Q1, STATE-Q3, ENG-Q5 |
| application/src/main/data/upgrade/basic/schema_update.sql | DISC-Q1, ENG-Q3 |

### Protobuf Schemas
| File | Questions Referenced |
|------|---------------------|
| common/proto/src/main/proto/ | DISC-Q1, API-Q5 |
| common/edge-api/src/main/proto/edge.proto | API-Q7 |

### Test Files
| File | Questions Referenced |
|------|---------------------|
| msa/black-box-tests/ (128 files) | ENG-Q4, HITL-Q3 |
| msa/black-box-tests/src/test/java/org/thingsboard/server/msa/TestRestClient.java | ENG-Q4 |
| application/src/test/resources/application-test.properties | HITL-Q3 |

### Monitoring
| File | Questions Referenced |
|------|---------------------|
| docker/monitoring/prometheus/ | OBS-Q2 |
| monitoring/src/main/java/ | OBS-Q1, OBS-Q3 |
