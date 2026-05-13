# Agentic Readiness Assessment Report

**Target**: apache/druid (monorepo)
**Date**: 2026-04-30
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**TD Version**: 3g1ipe93e5d2wb6n5d4yqaf9
**Repository Type**: monorepo
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: java, analytics, database
**Context**: Apache Druid: high-performance real-time analytics database.

**Archetype Justification**: Druid is a distributed analytics database with persistent state (deep storage segments, metadata store in PostgreSQL/MySQL/Derby), CRUD operations on datasources/segments/tasks/supervisors, and extensive REST APIs across all node types. The stateful-crud archetype is the most conservative classification covering all these characteristics.

- **Surface flags**:
  - has_persistent_data_store: true
  - has_http_rpc_surface: true
  - has_auth_surface: true
  - has_write_operations: true
  - has_logging_of_user_data: true

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 1 | **RISK-SAFETY**: 5 | **RISK-QUALITY**: 11 | **INFOs**: 25

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 1 |
| RISK-SAFETY | 5 |
| RISK-QUALITY | 11 |
| INFO | 25 |
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

### DATA-Q1: Sensitive Data Classification ⚡ (Tiered)

- **Severity**: BLOCKER
- **Stage A**: Yes — Druid ingests arbitrary user datasets (potentially PII/PHI) and stores credentials for external ingestion sources (Kafka SASL passwords, Kinesis AWS keys/assumed-role ARNs, JDBC passwords) in supervisor specs persisted to metadata storage.
- **B1 — API response scoping: BLOCKER.** `SupervisorResource.specGet()` / `specGetStatus()` (`indexing-service/src/main/java/org/apache/druid/indexing/overlord/supervisor/SupervisorResource.java:282-290`) returns the full supervisor spec via `Response.ok(spec.get()).build()` with no field filtering. `KafkaIndexTaskIOConfig.getConsumerProperties()` (`extensions-core/kafka-indexing-service/.../KafkaIndexTaskIOConfig.java:165-168`) is `@JsonProperty`-serialized as a `Map<String, Object>` — **no `@JsonIgnore`** — so every Kafka SASL JAAS credential and SSL keystore password round-trips verbatim. `KinesisIndexTaskIOConfig` serializes `awsAssumedRoleArn` and `awsExternalId` with `@JsonProperty` (`extensions-core/kinesis-indexing-service/.../KinesisIndexTaskIOConfig.java:220-230`). No `PasswordProvider`-style abstraction hides secrets at serialization time. A single `GET /druid/indexer/v1/supervisor?full=true` call exfiltrates all ingestion-source credentials cluster-wide.
- **B2 — Access control differentiation: PARTIAL / RISK-SAFETY.** `druid-basic-security` extension provides `BasicRoleBasedAuthorizer` (`extensions-core/druid-basic-security/.../BasicRoleBasedAuthorizer.java`) with resource/action granularity (DATASOURCE, TASK, CONFIG, STATE, QUERY × READ, WRITE). `SupervisorResource` uses `@ResourceFilters(SupervisorResourceFilter.class)`. But there is **no field-level authorization** — any user with DATASOURCE:READ receives the full supervisor spec including embedded credentials. B2 is not strong enough to prevent B1's leakage.
- **B3 — Formal classification metadata: INFO.** No `@Sensitive`/`@Secret` annotations; no secrets manager integration (Vault/AWS Secrets Manager) for inline credentials.
- **Overall (read-only scope)**: B1 fires as BLOCKER — read-only access is sufficient to exfiltrate cluster-wide ingestion credentials. → **DATA-Q1 = BLOCKER**.
- **Gap**: Supervisor spec serialization returns credentials in plaintext; no masking layer; no secrets manager abstraction.
- **Remediation**:
  - **Immediate**: Add `@JsonIgnore` on `consumerProperties` map keys matching SASL/SSL password patterns (or introduce a filtered response DTO). Mask `awsAssumedRoleArn`/`awsExternalId` behind an explicit "reveal credentials" endpoint gated by a new permission.
  - **Target State**: Integrate with a secrets manager; supervisor specs reference secret names, not inline values. Field-level authorization checks before serialization.
  - **Estimated Effort**: Medium for masking; High for full secrets-manager refactor.
  - **Dependencies**: Reinforces AUTH-Q2 and AUTH-Q3.
- **Evidence**: `indexing-service/src/main/java/org/apache/druid/indexing/overlord/supervisor/SupervisorResource.java:282-290`, `extensions-core/kafka-indexing-service/src/main/java/org/apache/druid/indexing/kafka/KafkaIndexTaskIOConfig.java:165-168`, `extensions-core/kinesis-indexing-service/src/main/java/org/apache/druid/indexing/kinesis/KinesisIndexTaskIOConfig.java:220-230`, `extensions-core/druid-basic-security/src/main/java/org/apache/druid/security/basic/authorization/BasicRoleBasedAuthorizer.java`.

---

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q6: Immutable Audit Logging — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Druid implements audit logging via `SQLAuditManager` (stores audit entries in metadata database with author, key, type, comment, created_date, payload) and `LoggingAuditManager` (writes to application logs). The audit system records the authenticated principal (`author` field from `AuditInfo`) for configuration changes. However, audit logs are stored in the metadata database (PostgreSQL/MySQL/Derby) which is a mutable store — rows can be updated or deleted. The `removeAuditLogsOlderThan()` method in `SQLAuditManager` explicitly deletes old audit entries. No immutable storage (S3 with Object Lock, CloudTrail) is configured.
- **Gap**: Audit logs are not immutable or tamper-evident. They reside in a mutable database and can be deleted by the `removeAuditLogsOlderThan` cleanup process or by direct database access.
- **Compensating Controls**:
  - Route audit log output to an immutable log sink (CloudWatch Logs with retention policy, S3 with Object Lock) alongside the database storage.
  - Enable database-level audit logging on the metadata store (PostgreSQL audit extension).
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure `EmittingRequestLogger` to forward audit events to an external immutable log store. Implement database-level protections against audit log tampering.
- **Evidence**: `server/src/main/java/org/apache/druid/server/audit/SQLAuditManager.java` (lines: doAudit(), removeAuditLogsOlderThan()), `server/src/main/java/org/apache/druid/server/audit/LoggingAuditManager.java`

#### STATE-Q1: Compensation and Rollback — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Druid's indexing service supports task lifecycle states (RUNNING, SUCCESS, FAILED) with task cancellation via `DELETE /druid/indexer/v1/task/{taskid}/shutdown`. However, there are no formal saga or compensation patterns for multi-step operations. If an ingestion task partially completes, there is no automated rollback — partial segments may be published. Segment management operations (mark used/unused) are individual operations without multi-step compensation.
- **Gap**: No formal compensation or rollback mechanism for multi-step operations. Task cancellation stops future work but does not undo completed steps.
- **Compensating Controls**:
  - For read-only agent scope, this is mitigated because agents will not initiate write operations. Risk applies if scope expands.
  - Manual segment cleanup APIs (`POST /druid/coordinator/v1/datasources/{dataSourceName}/markUnused`) can be used for ad-hoc rollback.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: If agent scope expands to write-enabled, implement compensation logic for multi-step ingestion workflows. Consider Step Functions or saga patterns for task orchestration.
- **Evidence**: `indexing-service/src/main/java/org/apache/druid/indexing/overlord/http/OverlordResource.java`, `server/src/main/java/org/apache/druid/server/http/DataSourcesResource.java`

#### DATA-Q2: Data Residency and Sovereignty — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Druid stores data in configurable deep storage (S3, HDFS, local, Azure, GCS) and metadata in PostgreSQL/MySQL/Derby. Storage location is configured via `druid_storage_type` and `druid_storage_storageDirectory` properties. However, there are no explicit data residency enforcement mechanisms, cross-region replication controls, or compliance-aware (GDPR, LGPD) configurations in the codebase. An agent querying Druid could retrieve data that is subject to residency requirements without any system-level enforcement preventing cross-boundary transmission.
- **Gap**: No data residency or sovereignty controls exist in the codebase. Storage location is a deployment-time configuration, not a code-level enforcement mechanism.
- **Compensating Controls**:
  - Deploy Druid within the required jurisdiction and configure deep storage (S3 bucket) in the same region.
  - Implement network-level controls (VPC, security groups) to prevent cross-region data transmission from the Druid cluster.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document data residency requirements per datasource. Configure deep storage and metadata store within the required jurisdiction at deployment time. Implement network-level controls to prevent cross-boundary access.
- **Evidence**: `distribution/docker/environment` (druid_storage_type=local, druid_storage_storageDirectory=/opt/shared/segments), `extensions-core/s3-extensions/`, `extensions-core/azure-extensions/`, `extensions-core/google-extensions/`

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Druid has partial log masking: `StartupLoggingConfig` masks properties containing "Password", "password", "Secret", "secret" in startup logs. However, the request logging framework (`FileRequestLogger`, `LoggingRequestLogger`, `EmittingRequestLogger`) logs full query details including query predicates, datasource names, and context parameters. Query predicates may contain user-supplied PII (e.g., `WHERE customer_email = 'user@example.com'`). The `FilteredRequestLoggerProvider` filters by query time threshold and query type but does not redact PII from query content.
- **Gap**: No comprehensive PII redaction exists for request/query logs. Query predicates containing user data are logged verbatim. Only credential-like strings (passwords, secrets) are masked in startup logs.
- **Compensating Controls**:
  - Configure `FilteredRequestLoggerProvider` with aggressive time thresholds to reduce log volume containing PII.
  - Implement a custom `RequestLogger` wrapper that sanitizes query predicates before logging.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement a PII-aware log filter that redacts or hashes user-supplied values in query predicates before they are written to request logs. Extend `StartupLoggingConfig.maskProperties` to cover additional sensitive field patterns.
- **Evidence**: `server/src/main/java/org/apache/druid/server/log/StartupLoggingConfig.java` (maskProperties: Password, password, Secret, secret), `server/src/main/java/org/apache/druid/server/log/FilteredRequestLoggerProvider.java`, `server/src/main/java/org/apache/druid/server/log/FileRequestLoggerProvider.java`

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Druid uses `resilience4j-bulkhead` (declared in pom.xml) for query capacity management in `QueryScheduler`. However, no explicit circuit breaker patterns were found for Druid's own external dependency calls to ZooKeeper (via Apache Curator) or the metadata database (PostgreSQL/MySQL/Derby via JDBI). Curator has built-in retry policies for ZooKeeper connections, but these are basic retries, not circuit breakers. A metadata database outage could cascade through all Druid nodes without circuit breaker protection.
- **Gap**: No circuit breakers for metadata database or ZooKeeper dependency calls. A dependency outage could cascade to all query and management operations.
- **Compensating Controls**:
  - Curator's built-in retry policies provide basic resilience for ZooKeeper connections.
  - Deploy metadata database with high availability (PostgreSQL replication, Aurora).
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement circuit breakers for metadata database calls using Resilience4j CircuitBreaker (already a dependency). Configure fallback behavior when the metadata store is unavailable.
- **Evidence**: `pom.xml` (resilience4j.version = 1.3.1), `server/src/main/java/org/apache/druid/server/QueryScheduler.java` (Bulkhead only, no CircuitBreaker), ZooKeeper connection via Apache Curator.

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, GraphQL schema, or Smithy specification files were found in the repository. Druid's REST API is documented through code annotations (`@Path`, `@GET`, `@POST`, `@Produces`) and external documentation (docs/), but there is no machine-readable specification that agent frameworks could use to auto-generate tool definitions.
- **Gap**: No machine-readable API specification exists. Agent tool definitions must be manually authored from documentation and source code inspection.
- **Compensating Controls**:
  - Generate OpenAPI spec from JAX-RS annotations using tools like swagger-jaxrs or enunciate.
  - Manually create an OpenAPI spec covering the most critical agent-facing endpoints (/druid/v2/, /druid/coordinator/v1/).
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Generate an OpenAPI 3.0 specification from JAX-RS annotations. Integrate spec generation into the CI pipeline to ensure it stays current.
- **Evidence**: Absence of any file matching `openapi*`, `swagger*`, `*.graphql`, `*.smithy`, `asyncapi*` in the entire repository.

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Druid implements structured error responses via `QueryException` and `DruidException`. `QueryException` includes typed error codes (`JSON_PARSE_ERROR_CODE`, `QUERY_CAPACITY_EXCEEDED_ERROR_CODE`, `QUERY_TIMEOUT_ERROR_CODE`, etc.) and a `FailType` enum mapping to HTTP status codes (400, 401, 429, 500, 501, 504). `DruidException` provides structured error bodies with error code, persona, and category. However, not all API endpoints use this structured format consistently — some endpoints return plain text or unstructured error messages.
- **Gap**: Error response format is partially structured. Query endpoints use `QueryException` with typed error codes, but management endpoints (coordinator, overlord) may return inconsistent error formats.
- **Compensating Controls**:
  - For read-only agent integration, focus on the query API (/druid/v2/) which has well-structured errors with `QueryException.FailType`.
  - Implement error response normalization middleware in the agent layer.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Standardize all API endpoints to use `DruidException` for error responses with consistent JSON format including error code, message, and category.
- **Evidence**: `processing/src/main/java/org/apache/druid/query/QueryException.java` (FailType enum, error code constants), `server/src/main/java/org/apache/druid/server/QueryResultPusher.java` (handleDruidException), `processing/src/main/java/org/apache/druid/error/DruidException.java`

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Druid uses URL-based API versioning (`/druid/v2/`, `/druid/coordinator/v1/`, `/druid/indexer/v1/`). However, there is no breaking change detection in CI, no consumer-driven contract tests (Pact), no OpenAPI diff tooling, and no schema registry. API changes are reviewed through PR code review but without automated contract validation.
- **Gap**: No automated breaking change detection for APIs. Schema changes could break agent tool bindings silently.
- **Compensating Controls**:
  - Pin agent tool definitions to specific API version paths (/druid/v2/).
  - Druid's versioned URL paths provide basic protection against breaking changes.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement API contract testing in CI (e.g., OpenAPI spec diff against previous release). Consider consumer-driven contract tests for critical agent-facing endpoints.
- **Evidence**: `server/src/main/java/org/apache/druid/server/QueryResource.java` (@Path("/druid/v2/")), `indexing-service/src/main/java/org/apache/druid/indexing/overlord/http/OverlordResource.java` (@Path("/druid/indexer/v1")), `.github/workflows/ci.yml` (no contract testing steps)

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Druid has an OpenTelemetry emitter extension (`extensions-contrib/opentelemetry-emitter/`) that can export metrics and traces. The request logging framework supports JSON-formatted output via `FileRequestLogger` and `EmittingRequestLogger`. Query IDs (`X-Druid-Query-Id` response header) provide correlation capability. However, OpenTelemetry is a community-contributed extension (not core), trace ID propagation via `traceparent` header is not built into the core request processing pipeline, and structured JSON logging requires explicit configuration.
- **Gap**: Distributed tracing and structured logging are available via extensions but not enabled by default. Trace ID propagation is not built into the core request processing path.
- **Compensating Controls**:
  - Enable the OpenTelemetry emitter extension and configure trace export.
  - Use the `X-Druid-Query-Id` header as a correlation ID for agent-initiated queries.
- **Remediation Timeline**: 30 days
- **Recommendation**: Enable the OpenTelemetry emitter extension in production deployments. Configure structured JSON logging via `FileRequestLogger`. Ensure query IDs are propagated across all Druid node types.
- **Evidence**: `extensions-contrib/opentelemetry-emitter/src/main/java/org/apache/druid/emitter/opentelemetry/OpenTelemetryEmitter.java`, `server/src/main/java/org/apache/druid/server/QueryResource.java` (QUERY_ID_RESPONSE_HEADER = "X-Druid-Query-Id"), `server/src/main/java/org/apache/druid/server/log/FileRequestLoggerProvider.java`

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Druid has a comprehensive metrics framework with emitters for Prometheus (`extensions-contrib/prometheus-emitter/`), Graphite (`extensions-contrib/graphite-emitter/`), StatsD (`extensions-contrib/statsd-emitter/`), and Dropwizard (`extensions-contrib/dropwizard-emitter/`). Metrics monitors include `QueryCountStatsMonitor` (successful/failed/interrupted/timed-out queries), `HistoricalMetricsMonitor`, `TaskCountStatsMonitor`, and many others. However, alert threshold configuration is not defined in the codebase — alerting depends on external systems (Prometheus Alertmanager, Grafana, CloudWatch) that consume the emitted metrics.
- **Gap**: No alert thresholds are defined in the codebase. Alerting is delegated entirely to external monitoring systems that must be configured separately at deployment time.
- **Compensating Controls**:
  - Enable Prometheus emitter and configure Prometheus Alertmanager with thresholds for query error rates and latency.
  - Use Druid's built-in metrics (query/time, query/failed/count) to define alerting rules.
- **Remediation Timeline**: 30 days
- **Recommendation**: Deploy with Prometheus emitter enabled and configure Alertmanager rules for query error rates, latency P95/P99, and capacity exceeded events.
- **Evidence**: `extensions-contrib/prometheus-emitter/src/main/java/org/apache/druid/emitter/prometheus/PrometheusEmitter.java`, `server/src/main/java/org/apache/druid/server/metrics/QueryCountStatsMonitor.java`, `server/src/main/java/org/apache/druid/server/metrics/HistoricalMetricsMonitor.java`

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No Infrastructure-as-Code (Terraform, CloudFormation, CDK, Helm, Kustomize) was found in the repository. The `distribution/docker/docker-compose.yml` provides a development/quickstart deployment but is not production-grade IaC. No drift detection, peer review requirements for infrastructure changes, or IaC governance controls exist in the repo.
- **Gap**: No production IaC exists. Infrastructure provisioning is not codified, reviewed, or monitored for drift.
- **Compensating Controls**:
  - Use the docker-compose.yml as a reference to create production IaC (Helm chart, Terraform, or CloudFormation).
  - The Kubernetes extensions (`extensions-core/kubernetes-extensions/`, `extensions-core/kubernetes-overlord-extensions/`) suggest Kubernetes-based deployment is supported.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Create production IaC (Helm chart recommended given Kubernetes extension support) with peer review requirements and drift detection (AWS Config or equivalent).
- **Evidence**: Absence of `*.tf`, `*.tfvars`, `Chart.yaml`, `kustomization.yaml`, `*.cfn.yaml`, `cdk.json` in repository. `distribution/docker/docker-compose.yml` (development-only).

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Druid has a mature CI/CD pipeline with GitHub Actions workflows: `ci.yml` (unit tests with JDK 17/21 matrix), `static-checks.yml` (checkstyle, PMD, spotbugs, forbiddenapis), `unit-and-integration-tests-unified.yml`, `docker-tests.yml`, `codeql.yml` (security scanning), and `pr-checks.yml`. However, there are no API contract tests (Pact), no OpenAPI spec validation, and no breaking change detection for REST APIs.
- **Gap**: Comprehensive CI/CD exists but lacks API contract testing. Breaking API changes could reach production without automated detection.
- **Compensating Controls**:
  - The extensive integration test suite (3,186+ test files, embedded-tests/, quidem-ut/) provides coverage of API behavior, though not as formal contracts.
  - Static checks (checkstyle, PMD, spotbugs) catch code quality issues but not API contract violations.
- **Remediation Timeline**: 60 days
- **Recommendation**: Add API contract tests for critical agent-facing endpoints. Generate and validate OpenAPI spec in CI to detect breaking changes.
- **Evidence**: `.github/workflows/ci.yml`, `.github/workflows/static-checks.yml`, `.github/workflows/unit-and-integration-tests-unified.yml`, `.github/workflows/codeql.yml`

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The Docker-based deployment (`distribution/docker/Dockerfile`) uses versioned images (`apache/druid:37.0.0`), which enables rollback by reverting to a previous image version. However, no blue/green deployment, canary deployment, traffic shifting, feature flags, or automated rollback triggers are defined in the repository. Rollback is a manual Docker image version change process.
- **Gap**: No automated rollback capability. Rollback requires manual image version change and service restart.
- **Compensating Controls**:
  - Docker image versioning allows manual rollback to previous known-good version.
  - Kubernetes deployment (via kubernetes-extensions) would provide native rollback capabilities.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement deployment automation with rollback triggers (e.g., Kubernetes rollout undo, CodeDeploy with health checks). Define rollback procedures for the Druid cluster.
- **Evidence**: `distribution/docker/Dockerfile` (versioned image: `apache/druid:37.0.0`), `distribution/docker/docker-compose.yml`

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Druid provides a `docker-compose.yml` for local development/testing with all node types (coordinator, broker, historical, middlemanager, router) plus PostgreSQL and ZooKeeper. The `examples/` directory contains quickstart data for testing. The `DRUID_SINGLE_NODE_CONF=micro-quickstart` configuration is designed for local development. However, there is no dedicated staging environment configuration with production-equivalent data shape, no synthetic data generators, and no environment-specific IaC.
- **Gap**: Local development environment exists via docker-compose but no staging environment with production-equivalent data shape for agent testing.
- **Compensating Controls**:
  - Use docker-compose environment with sample data from `examples/` for initial agent testing.
  - Create a staging Druid cluster with anonymized production data for realistic agent testing.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a dedicated staging environment with anonymized production-equivalent data for agent testing. Include seed data scripts that replicate production datasource schemas.
- **Evidence**: `distribution/docker/docker-compose.yml`, `distribution/docker/environment` (DRUID_SINGLE_NODE_CONF=micro-quickstart), `examples/`

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Druid has extensive test infrastructure (3,186+ test files, embedded-tests/, quidem-ut/, e2e-tests/) but no dedicated API contract test suite (Postman, REST Assured, Pact). API behavior is tested implicitly through integration tests.
- **Gap**: No formal API contract tests for agent-facing endpoints.
- **Compensating Controls**:
  - Large integration test suite covers API behavior implicitly.
  - Quidem tests validate SQL query behavior.
- **Remediation Timeline**: 60 days
- **Recommendation**: Create dedicated API contract tests for critical agent-facing endpoints.
- **Evidence**: `embedded-tests/`, `quidem-ut/`, `.github/workflows/ci.yml`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No encryption-at-rest configuration was found in the codebase. The S3 extension (`extensions-core/s3-extensions/`) supports S3 storage but does not configure server-side encryption (SSE-S3, SSE-KMS, SSE-C) by default. The PostgreSQL metadata store connection (`distribution/docker/environment`) uses plaintext. No KMS key references, DynamoDB encryption, or disk-level encryption configurations exist.
- **Gap**: No encryption-at-rest is configured in the codebase. Deep storage (S3/HDFS/local) and metadata store contents are stored unencrypted by default.
- **Compensating Controls**:
  - Configure S3 server-side encryption (SSE-KMS) at the bucket level for deep storage.
  - Enable PostgreSQL encryption at rest (TDE or volume-level encryption) for the metadata store.
- **Remediation Timeline**: 30 days
- **Recommendation**: Configure encryption at rest for all persistent stores: S3 with SSE-KMS for deep storage, PostgreSQL with disk encryption for metadata, and local disk encryption for segment cache.
- **Evidence**: `extensions-core/s3-extensions/` (no SSE configuration), `distribution/docker/environment` (plaintext metadata connection), `distribution/docker/docker-compose.yml` (no encryption configuration)

---

## INFOs — Architecture and Design Inputs

### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No idempotency key support was found on write endpoints (task submission, segment management). Task submission via `POST /druid/indexer/v1/task` does not accept an idempotency key. However, since agent_scope is read-only, this is informational.
- **Implication**: If agent scope expands to write-enabled, idempotency must be addressed before deployment. Task re-submission could create duplicate ingestion jobs.
- **Recommendation**: Add idempotency key support to write endpoints before expanding agent scope to write-enabled.
- **Evidence**: `indexing-service/src/main/java/org/apache/druid/indexing/overlord/http/OverlordResource.java` (@Path("/task"))

### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: Druid APIs produce structured JSON responses (`@Produces(MediaType.APPLICATION_JSON)`) with Smile binary JSON also supported (`SmileMediaTypes.APPLICATION_JACKSON_SMILE`). All API resources use Jackson serialization for consistent JSON output.
- **Implication**: JSON response format is well-suited for agent consumption. Smile format is a binary alternative for performance but requires specific client support.
- **Recommendation**: Use JSON format for agent integrations. Consider Smile only for high-throughput agent scenarios.
- **Evidence**: `server/src/main/java/org/apache/druid/server/QueryResource.java` (@Produces({MediaType.APPLICATION_JSON, SmileMediaTypes.APPLICATION_JACKSON_SMILE}))

### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: Druid has a comprehensive emitter framework that publishes metrics and events. Extensions include Kafka emitter (`extensions-contrib/kafka-emitter/`), which can publish events to Kafka topics. Druid publishes metrics for query completion, task status changes, segment load/drop events through ServiceMetricEvent. However, there is no webhook endpoint or structured event stream specifically designed for external consumers to react to state changes.
- **Implication**: Event-driven agent patterns are possible via Kafka emitter but require custom integration. No out-of-the-box webhook support.
- **Recommendation**: If agent use cases require reactive patterns, configure the Kafka emitter to publish task completion and segment change events to dedicated topics.
- **Evidence**: `extensions-contrib/kafka-emitter/`, `server/src/main/java/org/apache/druid/server/emitter/`, `server/src/main/java/org/apache/druid/server/metrics/`

### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: Druid does not return standard rate limit headers (`X-RateLimit-Remaining`, `Retry-After`). Rate limiting is handled internally via `QueryScheduler` with Bulkhead pattern (Resilience4j) and `QueryCapacityExceededException` when capacity is exceeded. The HTTP 429 status code is used for capacity exceeded responses, but without rate limit headers.
- **Implication**: Agents cannot proactively self-throttle based on rate limit headers. They must react to 429 responses.
- **Recommendation**: Add `X-RateLimit-Remaining` and `Retry-After` headers to query responses based on QueryScheduler capacity metrics.
- **Evidence**: `server/src/main/java/org/apache/druid/server/QueryScheduler.java` (BulkheadRegistry, QueryCapacityExceededException), `processing/src/main/java/org/apache/druid/query/QueryException.java` (CAPACITY_EXCEEDED = 429)

### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: Druid supports internal identity propagation via the `Escalator` interface. The `Escalator.createEscalatedClient()` method creates an HTTP client that sends requests with internal system user credentials for inter-node communication (broker→historical, coordinator→historical). The `AuthenticationResult` carries identity information including the authenticated identity string and the authorizer name. However, there is no OAuth2 on-behalf-of flow or explicit distinction between agent-as-self vs agent-on-behalf-of-user.
- **Implication**: Identity propagation exists for internal system calls but does not support on-behalf-of delegation for agent workflows.
- **Recommendation**: For agent integration, use a dedicated service account identity. On-behalf-of delegation is not needed for read-only analytics queries.
- **Evidence**: `server/src/main/java/org/apache/druid/server/security/Escalator.java`, `server/src/main/java/org/apache/druid/server/security/AuthenticationResult.java`

### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: The docker-compose `environment` file contains plaintext credentials (`POSTGRES_PASSWORD=FoolishPassword`, `druid_metadata_storage_connector_password=FoolishPassword`). These are development defaults, not production configuration. The codebase supports environment variable-based configuration, and no explicit Secrets Manager or Vault integration was found as a core feature. However, Druid's extensible configuration system allows external secrets injection at deployment time.
- **Implication**: Production deployments must use external secrets management. Development defaults include plaintext passwords.
- **Recommendation**: Integrate with AWS Secrets Manager or HashiCorp Vault for production deployments. Replace plaintext credentials in environment configuration with secret references.
- **Evidence**: `distribution/docker/environment` (druid_metadata_storage_connector_password=FoolishPassword), `distribution/docker/docker-compose.yml` (POSTGRES_PASSWORD=FoolishPassword)

### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Druid uses version-based segment management and atomic segment publishing. The metadata store uses transactions for segment allocation and publishing. However, there are no explicit optimistic locking patterns (ETags, version fields, If-Match headers) on REST API endpoints.
- **Implication**: For read-only agent scope, concurrency controls for writes are not relevant. If scope expands, API-level optimistic locking should be added.
- **Recommendation**: No action needed for read-only scope. Address before expanding to write-enabled scope.
- **Evidence**: `server/src/main/java/org/apache/druid/server/http/DataSourcesResource.java`

### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits per agent identity exist (e.g., max records per query, max query frequency per identity). The QueryScheduler provides lane-based capacity limits but these are per-lane, not per-identity.
- **Implication**: For read-only scope, blast radius is limited to query load. No mechanism to limit an individual agent's query volume independently of general capacity controls.
- **Recommendation**: No action needed for read-only scope. Consider per-identity query quotas before write-enabled scope expansion.
- **Evidence**: `server/src/main/java/org/apache/druid/server/QueryScheduler.java` (lane-based capacity, not identity-based)

### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Druid's ingestion system supports task lifecycle states (RUNNING, PENDING, WAITING, SUCCESS, FAILED). Supervisors can be suspended and resumed. However, these are operational states for data ingestion, not HITL draft/approval states for agent-initiated actions.
- **Implication**: Relevant only if agent scope expands to write-enabled operations like task submission.
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: `indexing-service/src/main/java/org/apache/druid/indexing/overlord/http/OverlordResource.java`

### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable approval gates for operations exist. Operations execute immediately upon API call.
- **Implication**: Relevant only if agent scope expands to write-enabled operations.
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: No approval workflow code found in the repository.

### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality scoring, completeness metrics, or data profiling capabilities were found as built-in features. Druid tracks segment row counts (`SegmentRowCountDistribution` monitor) and segment metadata but does not assess data quality dimensions (null rates, duplicate detection, freshness SLAs).
- **Implication**: Agents cannot assess data quality before reasoning on query results. Data quality must be established externally.
- **Recommendation**: Implement data quality monitoring for datasources exposed to agents. Track null rates, row counts, and freshness metrics.
- **Evidence**: `server/src/main/java/org/apache/druid/server/metrics/SegmentRowCountDistribution.java`, `server/src/main/java/org/apache/druid/server/metrics/SegmentStatsMonitor.java`

### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Druid uses human-readable, semantically meaningful field names throughout its API and data model. Examples: `dataSource`, `interval`, `queryType`, `granularity`, `dimension`, `metric`, `segmentId`, `created_date`, `numRows`, `size`. API resource types are clearly named: `DATASOURCE`, `VIEW`, `CONFIG`, `STATE`, `SYSTEM_TABLE`, `QUERY_CONTEXT`, `EXTERNAL`. No legacy abbreviations requiring a data dictionary were observed.
- **Implication**: Agent tool definitions can use Druid's field names directly without translation. This accelerates tool authoring and improves LLM reasoning quality.
- **Recommendation**: Maintain current naming conventions. Document any domain-specific terms (e.g., "segment", "granularity", "deep storage") in agent tool descriptions.
- **Evidence**: `server/src/main/java/org/apache/druid/server/security/ResourceType.java`, `server/src/main/java/org/apache/druid/server/http/DataSourcesResource.java`

### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: Druid provides built-in metadata capabilities through SQL system tables: `sys.segments` (segment metadata), `sys.tasks` (task metadata), `sys.servers` (server metadata), `sys.server_segments`, and `INFORMATION_SCHEMA` tables. These provide a queryable catalog of all datasources, their schemas, segments, and operational state. This is a strong foundation for agent discoverability.
- **Implication**: Agents can query system tables to discover available datasources, their schemas, and operational state before executing analytics queries.
- **Recommendation**: Expose system table queries as agent tools for self-service datasource discovery.
- **Evidence**: `sql/src/` (SQL module with system tables), `server/src/main/java/org/apache/druid/server/security/ResourceType.java` (SYSTEM_TABLE resource type)

### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: Druid publishes extensive operational and business-relevant metrics via `ServiceMetricEvent`: query success/failure/interrupted/timeout counts (`QueryCountStatsMonitor`), task success/failure counts (`TaskCountStatsMonitor`), segment statistics (`SegmentStatsMonitor`), supervisor stats (`SupervisorStatsMonitor`), historical metrics (`HistoricalMetricsMonitor`), and subquery counts (`SubqueryCountStatsMonitor`). The emitter framework supports custom metric publication.
- **Implication**: Rich metrics are available for monitoring agent-initiated query patterns. Query success/failure rates can serve as business outcome metrics for agent interactions.
- **Recommendation**: Define agent-specific dashboards tracking query success rates, latency distributions, and data freshness for agent-initiated queries.
- **Evidence**: `server/src/main/java/org/apache/druid/server/metrics/QueryCountStatsMonitor.java`, `server/src/main/java/org/apache/druid/server/metrics/TaskCountStatsMonitor.java`, `server/src/main/java/org/apache/druid/server/metrics/SegmentStatsMonitor.java`

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: Druid exposes a comprehensive documented REST API via JAX-RS annotations. Major API surfaces include: `/druid/v2/` (query API via `QueryResource`), `/druid/coordinator/v1/` (coordinator management), `/druid/indexer/v1/` (indexing/task management via `OverlordResource`), plus datasource, metadata, rules, segments, servers, tiers, lookups, and compaction endpoints. Over 20 resource classes with `@Path` annotations were identified. The `docs/` directory contains extensive API documentation.
- **Gap**: None — API integration surface exists and is well-documented.
- **Recommendation**: No action needed. The REST API is the primary integration surface for agent tools.
- **Evidence**: `server/src/main/java/org/apache/druid/server/QueryResource.java` (@Path("/druid/v2/")), `server/src/main/java/org/apache/druid/server/http/DataSourcesResource.java`, `server/src/main/java/org/apache/druid/server/http/MetadataResource.java`, `indexing-service/src/main/java/org/apache/druid/indexing/overlord/http/OverlordResource.java` (@Path("/druid/indexer/v1"))

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section above.
- **Gap**: No machine-readable API spec found.
- **Recommendation**: Generate OpenAPI spec from JAX-RS annotations.
- **Evidence**: Absence of openapi/swagger/graphql/smithy/asyncapi files in repository.

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section above.
- **Gap**: Partially structured — query API well-structured, management endpoints inconsistent.
- **Recommendation**: Standardize on DruidException for all endpoints.
- **Evidence**: `processing/src/main/java/org/apache/druid/query/QueryException.java`, `processing/src/main/java/org/apache/druid/error/DruidException.java`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No idempotency key support on write endpoints. Read-only scope makes this informational.
- **Gap**: No idempotency keys on write endpoints.
- **Recommendation**: Address before expanding to write-enabled scope.
- **Evidence**: `indexing-service/src/main/java/org/apache/druid/indexing/overlord/http/OverlordResource.java`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: JSON and Smile (binary JSON) response formats. See INFOs section.
- **Gap**: N/A
- **Recommendation**: Use JSON for agent integrations.
- **Evidence**: `server/src/main/java/org/apache/druid/server/QueryResource.java`

#### API-Q6: Asynchronous Operation Support
- **Severity**: INFO
- **Finding**: Druid supports asynchronous patterns for long-running tasks via the indexing service. Task submission (`POST /druid/indexer/v1/task`) returns immediately with a task ID. Task status can be polled via `GET /druid/indexer/v1/task/{taskId}/status`. Supervisors provide ongoing management of streaming ingestion tasks. This pattern supports agent workflows that need to submit ingestion tasks and poll for completion. Since agent_scope is read-only, agents will not initiate tasks, making this informational.
- **Implication**: Async task management is well-implemented for ingestion workflows. Relevant if agent scope expands to include task management.
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: `indexing-service/src/main/java/org/apache/druid/indexing/overlord/http/OverlordResource.java` (@Path("/task"), @Path("/task/{taskid}"))

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: Emitter framework with Kafka emitter extension. See INFOs section.
- **Gap**: No webhook support.
- **Recommendation**: Configure Kafka emitter for event-driven agent patterns.
- **Evidence**: `extensions-contrib/kafka-emitter/`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit headers. QueryScheduler returns 429 on capacity exceeded. See INFOs section.
- **Gap**: No X-RateLimit-Remaining or Retry-After headers.
- **Recommendation**: Add rate limit response headers.
- **Evidence**: `server/src/main/java/org/apache/druid/server/QueryScheduler.java`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: Druid implements a pluggable authentication framework via the `Authenticator` interface with multiple implementations: `AllowAllAuthenticator`, `AnonymousAuthenticator`, `TrustedDomainAuthenticator` (core), plus `BasicHTTPAuthenticator` (basic-security extension with username/password), Kerberos (`druid-kerberos` extension), PAC4J/OIDC (`druid-pac4j` extension), and TLS/mTLS support (`simple-client-sslcontext` extension). Machine identity is supported through HTTP Basic auth with service accounts, Kerberos service principals, or mTLS client certificates. The `AuthenticationResult` carries the authenticated identity string, authorizer name, and authentication context — enabling principal attribution in downstream authorization and audit logging.
- **Gap**: None — machine identity authentication is well-supported via pluggable framework with multiple credential mechanisms.
- **Recommendation**: Configure `druid-basic-security` with dedicated service accounts for agent identities, or use mTLS for stronger machine identity.
- **Evidence**: `server/src/main/java/org/apache/druid/server/security/Authenticator.java`, `server/src/main/java/org/apache/druid/server/security/AuthenticationResult.java`, `extensions-core/druid-basic-security/`, `extensions-core/druid-kerberos/`, `extensions-core/druid-pac4j/`, `extensions-core/simple-client-sslcontext/`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: INFO
- **Finding**: Druid's authorization model supports scoped permissions via `Resource(type, name)` + `Action(READ, WRITE)`. Resource types include: `DATASOURCE`, `VIEW`, `CONFIG`, `STATE`, `SYSTEM_TABLE`, `QUERY_CONTEXT`, `EXTERNAL`. The basic-security extension implements role-based authorization (`BasicRoleBasedAuthorizer`) with user→role→permission mappings. Permissions can be scoped to specific datasource names with specific actions (e.g., READ access to datasource "wikipedia" only). This supports least-privilege: an agent identity can be granted READ access to specific datasources without inheriting broader privileges.
- **Gap**: None — scoped permissions with resource-type and action-level granularity are supported.
- **Recommendation**: Create dedicated agent roles with READ-only access to specific datasources. Avoid granting STATE or CONFIG resource access to agent identities.
- **Evidence**: `server/src/main/java/org/apache/druid/server/security/ResourceType.java`, `server/src/main/java/org/apache/druid/server/security/Action.java` (READ, WRITE), `server/src/main/java/org/apache/druid/server/security/Resource.java`, `extensions-core/druid-basic-security/src/main/java/org/apache/druid/security/basic/authorization/BasicRoleBasedAuthorizer.java`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: INFO
- **Finding**: Druid enforces action-level authorization on every API endpoint via `@ResourceFilters` annotations. Each endpoint specifies required `ResourceAction` pairs combining a `Resource` (type + name) and `Action` (READ or WRITE). For example, `DataSourcesResource` uses `@ResourceFilters(DatasourceResourceFilter.class)` which checks READ or WRITE permission per endpoint. The authorization check happens in `AuthorizationUtils.authorizeAllResourceActions()` which validates the authenticated principal has the required action on the required resource.
- **Gap**: None — action-level (READ/WRITE) authorization is enforced per endpoint.
- **Recommendation**: Ensure agent roles are configured with READ action only. WRITE action should be explicitly denied for read-only agent identities.
- **Evidence**: `server/src/main/java/org/apache/druid/server/http/DataSourcesResource.java` (@ResourceFilters on all endpoints), `server/src/main/java/org/apache/druid/server/security/AuthorizationUtils.java`, `server/src/main/java/org/apache/druid/server/security/ResourceAction.java`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: See INFOs section.
- **Gap**: No on-behalf-of delegation support. Internal escalation via Escalator interface.
- **Recommendation**: Use dedicated service accounts for agent identities.
- **Evidence**: `server/src/main/java/org/apache/druid/server/security/Escalator.java`

#### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: See INFOs section.
- **Gap**: Development defaults include plaintext passwords. No built-in Secrets Manager integration.
- **Recommendation**: Use external secrets management for production.
- **Evidence**: `distribution/docker/environment`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: See RISKs section above.
- **Gap**: Audit logs are mutable (stored in database, can be deleted).
- **Recommendation**: Route audit events to immutable log store.
- **Evidence**: `server/src/main/java/org/apache/druid/server/audit/SQLAuditManager.java`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: INFO
- **Finding**: The basic-security extension provides user management APIs: create users, delete users, assign/revoke roles. Via the `BasicAuthorizerResource` endpoint, individual user accounts can be deleted or have their roles revoked, effectively suspending their access immediately. The basic-security authenticator can also disable specific users. This provides the mechanism to suspend a misbehaving agent identity without affecting other agents or users.
- **Gap**: None — user deletion and role revocation provide immediate suspension capability.
- **Recommendation**: Implement automated monitoring that triggers agent identity suspension via the basic-security API on anomaly detection.
- **Evidence**: `extensions-core/druid-basic-security/src/main/java/org/apache/druid/security/basic/authorization/endpoint/BasicAuthorizerResource.java`, `extensions-core/druid-basic-security/src/main/java/org/apache/druid/security/basic/authorization/endpoint/CoordinatorBasicAuthorizerResourceHandler.java`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: See RISKs section above.
- **Gap**: No formal compensation/rollback for multi-step operations.
- **Recommendation**: Implement compensation logic if scope expands to write-enabled.
- **Evidence**: `indexing-service/src/main/java/org/apache/druid/indexing/overlord/http/OverlordResource.java`

#### STATE-Q2: Queryable Current State
- **Severity**: INFO
- **Finding**: Druid exposes extensive queryable state via REST APIs. Datasource metadata is available via `GET /druid/coordinator/v1/datasources`, segment state via `GET /druid/coordinator/v1/datasources/{dataSource}/segments`, task state via `GET /druid/indexer/v1/task/{taskId}/status`, supervisor state via `GET /druid/indexer/v1/supervisor`, and server state via `GET /druid/coordinator/v1/servers`. SQL system tables (`sys.segments`, `sys.tasks`, `sys.servers`) provide an additional queryable interface. All state is inspectable before agents take action.
- **Gap**: None — comprehensive queryable state is available.
- **Recommendation**: Use coordinator and system table APIs for agent state inspection before operations.
- **Evidence**: `server/src/main/java/org/apache/druid/server/http/DataSourcesResource.java`, `server/src/main/java/org/apache/druid/server/http/ServersResource.java`, `server/src/main/java/org/apache/druid/server/http/MetadataResource.java`

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: See INFOs section.
- **Gap**: No API-level optimistic locking (ETags, If-Match).
- **Recommendation**: No action for read-only scope.
- **Evidence**: `server/src/main/java/org/apache/druid/server/http/DataSourcesResource.java`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: See RISKs section above. Resilience4j Bulkhead used for query capacity but no circuit breakers for ZooKeeper or metadata database dependency calls.
- **Gap**: No circuit breakers for external dependency calls.
- **Recommendation**: Implement circuit breakers for metadata database calls.
- **Evidence**: `pom.xml`, `server/src/main/java/org/apache/druid/server/QueryScheduler.java`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: INFO
- **Finding**: Druid implements sophisticated query capacity management via `QueryScheduler` using Resilience4j `Bulkhead` pattern. The scheduler supports lane-based capacity control (`HiLoQueryLaningStrategy`, `ManualQueryLaningStrategy`) with configurable total and per-lane concurrent query limits. When capacity is exceeded, `QueryCapacityExceededException` is thrown with HTTP 429 status. The `SubqueryGuardrailHelper` provides additional guardrails for subquery resource limits. This effectively prevents agent query storms from overwhelming the system.
- **Gap**: None — rate limiting and capacity management are well-implemented via QueryScheduler.
- **Recommendation**: Configure appropriate lane limits for agent query traffic. Consider creating a dedicated query lane for agent identities.
- **Evidence**: `server/src/main/java/org/apache/druid/server/QueryScheduler.java` (Bulkhead pattern), `server/src/main/java/org/apache/druid/server/scheduling/HiLoQueryLaningStrategy.java`, `server/src/main/java/org/apache/druid/server/scheduling/ManualQueryLaningStrategy.java`, `server/src/main/java/org/apache/druid/server/SubqueryGuardrailHelper.java`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: See INFOs section.
- **Gap**: No per-identity transaction limits.
- **Recommendation**: Consider per-identity query quotas before write-enabled expansion.
- **Evidence**: `server/src/main/java/org/apache/druid/server/QueryScheduler.java`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path. This service is P2 priority and not identified as critical path.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: See INFOs section.
- **Gap**: No HITL draft states for agent actions.
- **Recommendation**: No action for read-only scope.
- **Evidence**: `indexing-service/src/main/java/org/apache/druid/indexing/overlord/http/OverlordResource.java`

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: See INFOs section.
- **Gap**: No approval gates.
- **Recommendation**: No action for read-only scope.
- **Evidence**: No approval workflow code found.

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section above.
- **Gap**: Docker-compose for local dev only; no staging with production-equivalent data.
- **Recommendation**: Create staging environment with anonymized data.
- **Evidence**: `distribution/docker/docker-compose.yml`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification ⚡ (Tiered)
- **Severity**: BLOCKER
- **Finding**: B1 BLOCKER — `SupervisorResource.specGet()` returns supervisor specs via `Response.ok(spec.get()).build()` with no field filtering; `KafkaIndexTaskIOConfig.getConsumerProperties()` and `KinesisIndexTaskIOConfig` serialize SASL/SSL/AWS credentials as `@JsonProperty` with no `@JsonIgnore`. A read-only agent calling `GET /druid/indexer/v1/supervisor?full=true` exfiltrates all ingestion-source credentials cluster-wide. B2 RISK-SAFETY (basic-security RBAC is datasource-level, no field-level authorization). B3 INFO (no secrets-manager abstraction). See BLOCKERs section above.
- **Gap**: Supervisor spec serialization returns credentials unmasked; no `PasswordProvider`-style abstraction.
- **Recommendation**: Add `@JsonIgnore` on sensitive `consumerProperties` keys; integrate secrets manager.
- **Evidence**: `indexing-service/src/main/java/org/apache/druid/indexing/overlord/supervisor/SupervisorResource.java:282-290`, `extensions-core/kafka-indexing-service/.../KafkaIndexTaskIOConfig.java:165-168`, `extensions-core/kinesis-indexing-service/.../KinesisIndexTaskIOConfig.java:220-230`.

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: See RISKs section above.
- **Gap**: No residency enforcement in code.
- **Recommendation**: Deploy within required jurisdiction with network-level controls.
- **Evidence**: `distribution/docker/environment`, `extensions-core/s3-extensions/`

#### DATA-Q3: Selective Query Support
- **Severity**: INFO
- **Finding**: Druid's native query API and SQL interface both support selective query features. The native query JSON format supports `limit` parameter, `threshold` for TopN queries, and `intervals` for time-range filtering. The SQL interface supports `LIMIT`, `OFFSET`, `WHERE` clauses, and `ORDER BY` for result set control. Metadata endpoints such as `MetadataResource` support pagination with `limit` and `cursor` parameters for unused segments listing. Result sets are bounded by query configuration.
- **Gap**: None — comprehensive selective query support exists across native and SQL interfaces.
- **Recommendation**: Configure default query result limits for agent identities to prevent unbounded result sets.
- **Evidence**: `server/src/main/java/org/apache/druid/server/http/MetadataResource.java`, `server/src/main/java/org/apache/druid/server/QueryResource.java`

#### DATA-Q4: System of Record Designations
- **Severity**: INFO
- **Finding**: Druid is designed as an analytics database — it is a derived data store, not typically the system of record for business entities. Data is ingested from source systems (Kafka, S3, batch files) into Druid for analytics. The metadata store tracks segment lifecycle as the source of truth for segment management. However, there are no formal system-of-record designations or master data management processes documented in the codebase.
- **Gap**: No formal system-of-record designations. Druid is typically a derived analytics store, not the golden record.
- **Recommendation**: Document Druid's role as an analytics data store (not system of record) in agent tool descriptions. Agents should treat Druid data as derived, not authoritative.
- **Evidence**: `distribution/docker/environment` (data ingestion configuration), `server/src/main/java/org/apache/druid/server/http/DataSourcesResource.java`

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: INFO
- **Finding**: Druid is inherently temporal — all data is organized by time intervals. Segments contain `interval` metadata (start/end timestamps). The `sys.segments` system table includes `start`, `end`, `last_compaction_state` fields. Query results include time-based granularity. Data freshness is observable via segment metadata — the latest segment's interval end time indicates data recency. However, there are no explicit `Cache-Control` or `X-Data-Age` response headers, and no freshness signaling for eventually consistent reads.
- **Gap**: Temporal metadata is excellent (time-series native) but no HTTP-level freshness headers for API consumers.
- **Recommendation**: Add `X-Data-Freshness` headers to query responses indicating the latest segment timestamp for the queried datasource.
- **Evidence**: `server/src/main/java/org/apache/druid/server/http/DataSourcesResource.java`, SQL system tables (`sys.segments`)

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: See RISKs section above.
- **Gap**: Partial masking for passwords/secrets only. Query predicates logged verbatim.
- **Recommendation**: Implement PII-aware log filter.
- **Evidence**: `server/src/main/java/org/apache/druid/server/log/StartupLoggingConfig.java`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: See INFOs section.
- **Gap**: No data quality scoring.
- **Recommendation**: Implement data quality monitoring for agent-accessible datasources.
- **Evidence**: `server/src/main/java/org/apache/druid/server/metrics/SegmentRowCountDistribution.java`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section above.
- **Gap**: URL-based versioning but no automated breaking change detection.
- **Recommendation**: Add API contract testing to CI.
- **Evidence**: `server/src/main/java/org/apache/druid/server/QueryResource.java`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: See INFOs section.
- **Gap**: None — field names are semantically clear.
- **Recommendation**: Maintain current naming conventions.
- **Evidence**: `server/src/main/java/org/apache/druid/server/security/ResourceType.java`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: See INFOs section.
- **Gap**: None — SQL system tables provide built-in metadata catalog.
- **Recommendation**: Expose system table queries as agent tools.
- **Evidence**: `sql/src/`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section above.
- **Gap**: Tracing available via extension but not default. No traceparent propagation in core.
- **Recommendation**: Enable OpenTelemetry emitter in production.
- **Evidence**: `extensions-contrib/opentelemetry-emitter/`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section above.
- **Gap**: Metrics available but no alert thresholds configured in code.
- **Recommendation**: Configure Prometheus Alertmanager rules.
- **Evidence**: `extensions-contrib/prometheus-emitter/`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: See INFOs section.
- **Gap**: None — extensive metrics framework.
- **Recommendation**: Define agent-specific metric dashboards.
- **Evidence**: `server/src/main/java/org/apache/druid/server/metrics/QueryCountStatsMonitor.java`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section above.
- **Gap**: No production IaC.
- **Recommendation**: Create Helm chart or Terraform for production.
- **Evidence**: Absence of IaC files.

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section above.
- **Gap**: Mature CI/CD but no API contract tests.
- **Recommendation**: Add OpenAPI validation and contract tests to CI.
- **Evidence**: `.github/workflows/ci.yml`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section above.
- **Gap**: Manual rollback via Docker image versioning only.
- **Recommendation**: Implement automated rollback with health checks.
- **Evidence**: `distribution/docker/Dockerfile`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: Druid has extensive test infrastructure: 3,186+ Java test files across the repository, embedded integration tests (`embedded-tests/`), Quidem-based SQL tests (`quidem-ut/`), web console end-to-end tests (`web-console/e2e-tests/`), and comprehensive CI workflows running tests with JDK 17 and 21. However, there is no dedicated API contract test suite (Postman/Newman collections, REST Assured API tests, Pact consumer-driven tests). API behavior is tested as part of unit and integration tests but not as standalone API contract validation.
- **Gap**: No dedicated API test suite validating input handling, output format, error responses, and edge cases as formal API contracts.
- **Compensating Controls**:
  - The large integration test suite covers API behavior implicitly.
  - Quidem tests validate SQL query behavior systematically.
- **Remediation Timeline**: 60 days
- **Recommendation**: Create dedicated API contract tests for critical agent-facing endpoints (/druid/v2/, coordinator, indexer APIs). Consider REST Assured or Newman for API test automation.
- **Evidence**: `embedded-tests/`, `quidem-ut/`, `.github/workflows/ci.yml` (unit-test matrix), `web-console/e2e-tests/`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section above.
- **Gap**: No encryption at rest configured in codebase.
- **Recommendation**: Configure SSE-KMS for S3 deep storage and encryption for metadata DB.
- **Evidence**: `extensions-core/s3-extensions/`, `distribution/docker/environment`

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| server/src/main/java/org/apache/druid/server/QueryResource.java | API-Q1, API-Q3, API-Q5, API-Q8, OBS-Q1 |
| server/src/main/java/org/apache/druid/server/QueryScheduler.java | STATE-Q5, STATE-Q6, API-Q8 |
| server/src/main/java/org/apache/druid/server/QueryResultPusher.java | API-Q3 |
| server/src/main/java/org/apache/druid/server/http/DataSourcesResource.java | API-Q1, AUTH-Q3, STATE-Q1, STATE-Q3, DISC-Q2 |
| server/src/main/java/org/apache/druid/server/http/MetadataResource.java | API-Q1 |
| server/src/main/java/org/apache/druid/server/security/Authenticator.java | AUTH-Q1 |
| server/src/main/java/org/apache/druid/server/security/Authorizer.java | AUTH-Q1, AUTH-Q2 |
| server/src/main/java/org/apache/druid/server/security/Action.java | AUTH-Q2, AUTH-Q3 |
| server/src/main/java/org/apache/druid/server/security/ResourceType.java | AUTH-Q2, AUTH-Q3, DATA-Q1, DISC-Q2 |
| server/src/main/java/org/apache/druid/server/security/Resource.java | AUTH-Q2 |
| server/src/main/java/org/apache/druid/server/security/ResourceAction.java | AUTH-Q3 |
| server/src/main/java/org/apache/druid/server/security/AuthorizationUtils.java | AUTH-Q3 |
| server/src/main/java/org/apache/druid/server/security/AuthenticationResult.java | AUTH-Q1, AUTH-Q4 |
| server/src/main/java/org/apache/druid/server/security/Escalator.java | AUTH-Q4 |
| server/src/main/java/org/apache/druid/server/audit/SQLAuditManager.java | AUTH-Q6 |
| server/src/main/java/org/apache/druid/server/audit/LoggingAuditManager.java | AUTH-Q6 |
| server/src/main/java/org/apache/druid/server/log/StartupLoggingConfig.java | DATA-Q6 |
| server/src/main/java/org/apache/druid/server/log/FilteredRequestLoggerProvider.java | DATA-Q6 |
| server/src/main/java/org/apache/druid/server/log/FileRequestLoggerProvider.java | DATA-Q6, OBS-Q1 |
| server/src/main/java/org/apache/druid/server/scheduling/HiLoQueryLaningStrategy.java | STATE-Q5 |
| server/src/main/java/org/apache/druid/server/scheduling/ManualQueryLaningStrategy.java | STATE-Q5 |
| server/src/main/java/org/apache/druid/server/SubqueryGuardrailHelper.java | STATE-Q5 |
| server/src/main/java/org/apache/druid/server/metrics/QueryCountStatsMonitor.java | OBS-Q2, OBS-Q3 |
| server/src/main/java/org/apache/druid/server/metrics/HistoricalMetricsMonitor.java | OBS-Q2 |
| server/src/main/java/org/apache/druid/server/metrics/TaskCountStatsMonitor.java | OBS-Q3 |
| server/src/main/java/org/apache/druid/server/metrics/SegmentStatsMonitor.java | OBS-Q3, DATA-Q7 |
| server/src/main/java/org/apache/druid/server/metrics/SegmentRowCountDistribution.java | DATA-Q7 |
| processing/src/main/java/org/apache/druid/query/QueryException.java | API-Q3 |
| processing/src/main/java/org/apache/druid/error/DruidException.java | API-Q3 |
| indexing-service/src/main/java/org/apache/druid/indexing/overlord/http/OverlordResource.java | API-Q1, API-Q4, STATE-Q1, HITL-Q1 |
| extensions-core/druid-basic-security/src/main/java/.../BasicRoleBasedAuthorizer.java | AUTH-Q2 |
| extensions-core/druid-basic-security/src/main/java/.../BasicAuthorizerResource.java | AUTH-Q7 |
| extensions-contrib/opentelemetry-emitter/src/main/java/.../OpenTelemetryEmitter.java | OBS-Q1 |
| extensions-contrib/prometheus-emitter/src/main/java/.../PrometheusEmitter.java | OBS-Q2 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| .github/workflows/ci.yml | ENG-Q2, DISC-Q1 |
| .github/workflows/static-checks.yml | ENG-Q2 |
| .github/workflows/unit-and-integration-tests-unified.yml | ENG-Q2 |
| .github/workflows/codeql.yml | ENG-Q2 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| distribution/docker/Dockerfile | ENG-Q3 |
| distribution/docker/docker-compose.yml | HITL-Q3, ENG-Q1, DATA-Q2, ENG-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| pom.xml (root) | API-Q1 (Maven multi-module structure), STATE-Q5 (resilience4j dependency) |
| web-console/package.json | API-Q1 (frontend) |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| distribution/docker/environment | AUTH-Q5, DATA-Q2, ENG-Q5 |
