# Agentic Readiness Assessment Report

**Target**: . (apache/druid)
**Date**: 2026-04-29
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: monorepo
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: java, analytics, database
**Context**: Apache Druid: high-performance real-time analytics database.

**Archetype Justification**: Apache Druid is a distributed analytics database that owns persistent state (deep storage via S3/HDFS/local, metadata store via PostgreSQL/MySQL), exposes CRUD operations on datasources, segments, and tasks, and manages entity lifecycle (task states, supervisor states, segment versioning). This maps to the `stateful-crud` archetype as the most representative and conservative classification.

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 1 | **RISK-SAFETY**: 7 | **RISK-QUALITY**: 17 | **INFOs**: 12

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 1 |
| RISK-SAFETY | 7 |
| RISK-QUALITY | 17 |
| INFO | 12 |
| N/A | 0 |
| Not Evaluated (extended) | 1 |
| PASS (no gap) | 5 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 18
**Extended Questions Not Triggered**: 1
**Questions N/A (repo_type: monorepo)**: 0
**Service Archetype**: stateful-crud (auto-detected)

> **Note**: 5 questions (API-Q1, AUTH-Q1, AUTH-Q2, AUTH-Q3, STATE-Q2) were evaluated and found to have no gap — the required capability exists. These are marked as PASS in the detailed findings and do not contribute to BLOCKER, RISK-SAFETY, or RISK-QUALITY counts.

---

## BLOCKERs — Must Resolve Before Agent Deployment

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: No data classification tags, field-level encryption, or PII detection tooling found in the repository. Druid stores arbitrary user-provided data in datasources without built-in classification controls. There are no column-level access controls or data sensitivity annotations. Druid ingests data from Kafka, Kinesis, S3, and other sources with no field-level sensitivity tagging.
- **Gap**: Sensitive data (PII, PHI, financial records) is not classified or tagged at the field level. No controls prevent an agent from retrieving sensitive fields without explicit authorization. An agent querying Druid datasources could inadvertently retrieve unclassified PII.
- **Remediation**:
  - **Immediate**: Audit existing datasources for PII and sensitive fields. Create a data classification policy mapping datasource columns to sensitivity levels (public, internal, confidential, restricted).
  - **Target State**: Field-level classification metadata attached to datasource schemas, with query-time access controls that filter sensitive fields based on the authenticated principal's permissions. Consider Druid's VIEW resource type for creating pre-filtered views that exclude sensitive fields.
  - **Estimated Effort**: High
  - **Dependencies**: AUTH-Q2 (scoped permissions needed to enforce field-level controls), DATA-Q6 (PII in logs must also be addressed)
- **Evidence**: `distribution/docker/environment` (no classification config), `docs/operations/security-user-auth.md` (authorization is per-datasource, not per-field), `server/src/main/java/org/apache/druid/server/security/ResourceType.java` (DATASOURCE is the finest granularity)

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Druid provides audit logging via `SQLAuditManager` (stores audit entries in metadata store) and `LoggingAuditManager` (writes to log files). `AuditEntry` captures request details. Request logging is configurable via `druid.request.logging.type` but disabled by default (`noop`). No immutable log storage (CloudTrail, S3 Object Lock) is configured in the repository. The docker-compose default configuration does not enable request logging.
- **Gap**: Audit logs are stored in the metadata store (PostgreSQL) which is mutable. No tamper-evident or immutable log configuration found. Request logging is disabled by default.
- **Compensating Controls**:
  - Enable `SQLAuditManager` and configure request logging to an external immutable sink (S3 with Object Lock, CloudWatch Logs)
  - Deploy an API gateway in front of Druid that provides immutable access logging
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Enable request logging (`druid.request.logging.type=slf4j` or `emitter`), route audit entries to an immutable store. Configure the emitter to send audit events to a Kafka topic with retention or S3 bucket with Object Lock.
- **Evidence**: `server/src/main/java/org/apache/druid/server/audit/SQLAuditManager.java`, `server/src/main/java/org/apache/druid/server/audit/LoggingAuditManager.java`, `docs/operations/request-logging.md`, `distribution/docker/environment` (no request logging config)

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Druid's `druid-basic-security` extension supports user management (create/delete users via REST API at `/druid-ext/basic-security/authentication`). Users can be deleted to revoke access. However, there is no documented instant-revoke mechanism for machine identities — credential cache propagation is periodic (`druid.auth.basic.common.pollingPeriod`), meaning revocation may not take effect immediately across all cluster nodes.
- **Gap**: No instant identity suspension. Credential cache propagation delay means a revoked identity may still authenticate for seconds to minutes after revocation. No circuit breaker to immediately block a specific agent identity.
- **Compensating Controls**:
  - Configure `enableCacheNotifications=true` on the authenticator/authorizer to push revocations immediately
  - Deploy an API gateway with instant key revocation capability in front of Druid
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure cache notification push for immediate credential propagation. Document a runbook for agent identity revocation that includes both Druid user deletion and API gateway key revocation.
- **Evidence**: `docs/operations/security-user-auth.md` (Configuration propagation section), `docs/operations/auth.md`, `extensions-core/druid-basic-security/`

#### STATE-Q1: Compensation and Rollback ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Druid tasks support failure handling — tasks can be killed via `DELETE /druid/indexer/v1/task/{taskId}/shutdown`, and supervisors can be reset. Segment publishing uses atomic metadata store transactions. However, there is no explicit saga pattern, compensation logic, or undo endpoints for multi-step operations. If an ingestion task partially completes and fails, manual cleanup of partial segments may be required.
- **Gap**: No compensation or rollback patterns for multi-step workflows. Partial task failures require manual intervention.
- **Compensating Controls**:
  - For read-only agents, this risk is mitigated since read operations do not create partial state
  - Implement task monitoring with automatic cleanup of orphaned segments via compaction
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Document rollback procedures for common agent-initiated workflows. For future write-enabled scope, implement compensating actions in the agent orchestration layer.
- **Evidence**: `docs/api-reference/tasks-api.md` (task lifecycle), `server/src/main/java/org/apache/druid/server/coordinator/` (segment management)

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: resilience4j `bulkhead` (v1.3.1) is declared as a dependency in `pom.xml` and used in `QueryScheduler.java` for query concurrency limiting (bulkhead pattern). However, this is an internal concurrency limiter, not a circuit breaker for external dependency calls. Druid depends on ZooKeeper, the metadata store (PostgreSQL/MySQL), and deep storage (S3/HDFS), but no circuit breaker pattern was found protecting calls to these external dependencies. The only circuit breaker usage found was in `extensions-contrib/consul-extensions` for Consul discovery, not core service dependencies.
- **Gap**: No circuit breakers configured for core external dependencies (ZooKeeper, metadata store, deep storage). A runaway agent loop could cascade through Druid to overwhelm these dependencies.
- **Compensating Controls**:
  - Druid's QueryScheduler bulkhead limits query concurrency, providing partial protection against query-path overload
  - Deploy an API gateway with circuit breaker capability in front of Druid endpoints
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Evaluate adding circuit breakers around metadata store and deep storage connections. Consider retry budgets at the agent orchestration layer to prevent cascading failures.
- **Evidence**: `pom.xml` (resilience4j-bulkhead v1.3.1), `server/src/main/java/org/apache/druid/server/QueryScheduler.java` (Bulkhead import and usage), `extensions-contrib/consul-extensions/` (only location with circuit breaker reference)

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No API-level rate limiting found in the codebase. No `X-RateLimit-Remaining` headers, no WAF rate rules, no application-level rate limiting middleware. Druid's `QueryScheduler` provides internal query concurrency limiting via resilience4j Bulkhead and query laning, but this is not a per-client rate limit — it limits total query parallelism. The security documentation in `docs/operations/security-overview.md` explicitly recommends "Use an API gateway to... Implement account lockout and throttling features."
- **Gap**: No per-client or per-identity rate limiting. An agent sending queries at machine speed could exhaust the QueryScheduler bulkhead limit, blocking all other users.
- **Compensating Controls**:
  - Druid's QueryScheduler and query laning provide partial protection against query overload
  - Deploy API Gateway (AWS API Gateway with usage plans, or nginx rate limiting) in front of Druid
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Deploy an API gateway with per-client rate limiting and usage plans. Configure query laning in Druid to reserve capacity for non-agent traffic.
- **Evidence**: `server/src/main/java/org/apache/druid/server/QueryScheduler.java`, `docs/operations/security-overview.md` ("Implement account lockout and throttling features"), `distribution/docker/environment` (no rate limit config)

#### DATA-Q2: Data Residency and Sovereignty ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No data residency configuration or enforcement found in the repository. Druid's deep storage location is configurable (`druid_storage_type=local` in docker-compose, configurable to S3, HDFS, Azure, GCS). The data storage region depends entirely on the deployment configuration — the Druid codebase does not enforce or validate data residency constraints. An agent sending query results to an LLM endpoint in a different region would have no guardrails.
- **Gap**: No data residency enforcement at the application layer. Data sovereignty compliance depends entirely on deployment-time infrastructure configuration, which is not governed by this repository.
- **Compensating Controls**:
  - Configure deep storage in a compliant region at deployment time
  - Deploy the agent and LLM endpoints in the same region as the Druid cluster
- **Remediation Timeline**: 30–60 days (deployment configuration, not code change)
- **Recommendation**: Document data residency requirements for each Druid deployment. Enforce region constraints at the infrastructure layer (VPC endpoints, S3 bucket policies with region conditions).
- **Evidence**: `distribution/docker/environment` (`druid_storage_type=local`), `extensions-core/s3-extensions/` (S3 deep storage), `docs/operations/security-overview.md`

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No PII redaction middleware, log scrubbing, or masking libraries found in the codebase. Request logging (when enabled) logs full SQL queries and native queries, which may contain PII in WHERE clauses, filters, and predicates (e.g., `WHERE customer_email = 'john@example.com'`). The Log4j2 configuration in docker-compose uses a basic `PatternLayout` with no field masking. Druid's emitter framework sends metrics and events without PII filtering.
- **Gap**: PII may leak into query logs, request logs, and emitted metrics. No log scrubbing or PII masking detected.
- **Compensating Controls**:
  - Configure request logging to redact query text or use the `filtered` request logger type to exclude sensitive queries
  - Deploy a log aggregation pipeline with PII scrubbing before storage
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement a custom `RequestLogger` extension that redacts PII patterns from logged queries. Alternatively, use the `filtered` request logger to only log queries that exceed a time threshold, reducing exposure surface.
- **Evidence**: `docs/operations/request-logging.md` (request logging types, no mention of PII redaction), `distribution/docker/environment` (DRUID_LOG4J config with no masking), `server/src/main/java/org/apache/druid/server/RequestLogLine.java`

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, GraphQL schema, or Smithy specification files found in the repository. Druid's APIs are documented in 14 Markdown files under `docs/api-reference/` covering SQL API, Tasks API, Supervisors API, Data Management API, etc. These are human-readable but not machine-consumable for automatic tool generation.
- **Gap**: No machine-readable API specification. Agent tool definitions must be manually authored and maintained, increasing drift risk.
- **Compensating Controls**:
  - Generate OpenAPI specs from JAX-RS annotations using tools like swagger-jaxrs2
  - Manually create OpenAPI specs for the most critical agent-facing endpoints (SQL API, Tasks API)
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Generate OpenAPI specifications from the existing JAX-RS annotations using swagger-jaxrs2 or similar tooling. Integrate spec generation into the CI pipeline.
- **Evidence**: `docs/api-reference/api-reference.md`, `docs/api-reference/sql-api.md`, No OpenAPI/Swagger files found in repository scan

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Druid uses `DruidException` with structured error responses including `errorCode`, `persona` (USER/ADMIN/OPERATOR/DEVELOPER), `category` (TIMEOUT/UNAUTHORIZED/RUNTIME_FAILURE/INVALID_INPUT/CAPACITY_EXCEEDED/CANCELED/UNSUPPORTED/UNCATEGORIZED/DEFENSIVE), and `errorMessage`. The `ErrorResponse` class serializes errors to JSON with these fields plus a `context` map. HTTP status codes are mapped from exception categories. However, there is no explicit `retryable` boolean or flag in the error response structure.
- **Gap**: Error responses are well-structured with category classification, but lack an explicit `retryable` indicator. An agent must infer retryability from the category (e.g., TIMEOUT → retry, INVALID_INPUT → don't retry).
- **Compensating Controls**:
  - Map Druid error categories to retry logic in the agent tool definition (TIMEOUT, CAPACITY_EXCEEDED → retry; INVALID_INPUT, UNAUTHORIZED → don't retry)
  - Use the `category` field as a proxy for retryability
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Consider adding an explicit `retryable` boolean to the `ErrorResponse` JSON schema. In the interim, document the category-to-retryability mapping for agent developers.
- **Evidence**: `processing/src/main/java/org/apache/druid/error/DruidException.java` (Category enum), `processing/src/main/java/org/apache/druid/error/ErrorResponse.java` (JSON serialization), `server/src/main/java/org/apache/druid/server/QueryResultPusher.java` (error handling)

#### API-Q6: Asynchronous Operation Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Druid supports asynchronous patterns for long-running operations. Ingestion tasks are submitted via `POST /druid/indexer/v1/task` and return a task ID. Task status is polled via `GET /druid/indexer/v1/task/{taskId}/status`. Supervisors manage ongoing ingestion workflows. Compaction tasks follow the same async submit-and-poll pattern. However, there are no webhook callbacks — all async monitoring requires polling.
- **Gap**: Async patterns exist for ingestion and compaction but rely on polling. No webhook or callback mechanism for task completion notification.
- **Compensating Controls**:
  - Implement polling-based monitoring in agent tools with configurable intervals
  - Use Druid's emitter framework to emit task completion events to a message queue the agent can subscribe to
- **Remediation Timeline**: 60–90 days
- **Recommendation**: For agent integration, implement polling-based task monitoring tools with exponential backoff. Consider building a webhook adapter that listens to Druid metric emissions and triggers callbacks on task state changes.
- **Evidence**: `docs/api-reference/tasks-api.md` (task submission and status endpoints), `docs/api-reference/supervisor-api.md` (supervisor lifecycle)

#### AUTH-Q4: Identity Propagation and Delegation — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Druid supports internal service-to-service authentication via the Escalator (`druid.escalator.type`), which creates escalated HTTP clients for internal communications (Broker → Historical, Coordinator → Historical). The `AuthenticationResult` carries identity information through the request chain. However, there is no JWT token exchange, OAuth2 on-behalf-of flow, or delegated identity propagation for distinguishing agent-as-self vs. agent-on-behalf-of-user.
- **Gap**: No delegated identity propagation. The system cannot distinguish between an agent acting under its own identity versus acting on behalf of a specific user. All internal service calls use the escalated "druid_system" identity.
- **Compensating Controls**:
  - Create separate Druid user accounts for each agent use case with scoped permissions
  - Pass user context as query context parameters for audit purposes
- **Remediation Timeline**: 60–90 days
- **Recommendation**: For read-only agents, use dedicated Druid user accounts with per-datasource READ permissions. Pass the original user identity as a query context parameter for audit trail purposes.
- **Evidence**: `docs/operations/auth.md` (Escalator documentation), `server/src/main/java/org/apache/druid/server/security/Escalator.java`, `server/src/main/java/org/apache/druid/server/security/AuthenticationResult.java`

#### AUTH-Q5: Credential Management — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Druid provides `EnvironmentVariableDynamicConfigProvider` for managing secrets via environment variables and a pluggable `PasswordProvider` interface for custom secret management. These are documented in `docs/operations/dynamic-config-provider.md` and `docs/operations/password-provider.md`. However, the default docker-compose configuration contains hardcoded credentials: `POSTGRES_PASSWORD=FoolishPassword` and `druid_metadata_storage_connector_password=FoolishPassword` in both `docker-compose.yml` and the `environment` file.
- **Gap**: Secret management capability exists but the default reference deployment uses hardcoded plaintext passwords. No integration with AWS Secrets Manager, HashiCorp Vault, or similar rotation-capable systems found in the repository.
- **Compensating Controls**:
  - Use the `EnvironmentVariableDynamicConfigProvider` to externalize all secrets
  - Deploy a secrets management sidecar or init container in production Kubernetes deployments
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Remove hardcoded credentials from the docker-compose example (or document them clearly as development-only). Implement a Vault or AWS Secrets Manager-backed `PasswordProvider` extension for production deployments.
- **Evidence**: `distribution/docker/docker-compose.yml` (`POSTGRES_PASSWORD=FoolishPassword`), `distribution/docker/environment` (`druid_metadata_storage_connector_password=FoolishPassword`), `docs/operations/dynamic-config-provider.md`, `docs/operations/password-provider.md`

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: `distribution/docker/docker-compose.yml` provides a complete local development environment with all Druid services (Coordinator, Broker, Historical, MiddleManager, Router) plus PostgreSQL and ZooKeeper. The `examples/` directory contains quickstart tutorial files. However, no seed data scripts, synthetic data generators, or production-equivalent staging environment configuration were found.
- **Gap**: Local testing environment exists but lacks seed data and production-equivalent data shape. No separate staging environment configuration for agent testing.
- **Compensating Controls**:
  - Use docker-compose for local agent testing with manually loaded sample data
  - Use Druid's batch ingestion to load sample datasets in the test environment
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create seed data scripts that load representative (but synthetic) datasources into the docker-compose environment. Document an agent testing workflow using the local stack.
- **Evidence**: `distribution/docker/docker-compose.yml`, `distribution/docker/environment`, `distribution/docker/Dockerfile`, `examples/`

#### DATA-Q3: Selective Query Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Druid SQL API supports `LIMIT` clauses for result set size control. Native JSON queries support limit parameters. The metadata APIs support query parameters for filtering (e.g., `state`, `type` filters on the tasks API). However, Druid does not support traditional offset-based pagination for query results — it relies on LIMIT and time-based filtering rather than cursor-based pagination.
- **Gap**: Result size limiting via LIMIT exists, but no cursor-based pagination for incremental result retrieval. Large result sets must be managed via time-range partitioning.
- **Compensating Controls**:
  - Use LIMIT and time-based filtering in agent queries to bound result sizes
  - Implement query result caching at the agent layer for pagination
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Define query templates for agent tools that include LIMIT clauses and time-range filters by default. Document maximum recommended result sizes per query type.
- **Evidence**: `docs/api-reference/sql-api.md`, `docs/api-reference/tasks-api.md` (query parameters)

#### DATA-Q4: System of Record Designations — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Druid datasources serve as the system of record for ingested time-series analytics data by design. Each datasource is the authoritative source for the data it contains. However, there is no formal system-of-record documentation, master data management process, or conflict resolution logic for data that may also exist in upstream source systems.
- **Gap**: No formal system-of-record designations or master data management documentation. Agents querying Druid alongside other systems may encounter conflicting records without guidance on which is authoritative.
- **Compensating Controls**:
  - Document Druid as the authoritative source for analytics queries; upstream systems as authoritative for transactional data
  - Include data source provenance metadata in agent tool descriptions
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document system-of-record designations for each datasource. Include provenance metadata in datasource descriptions accessible via INFORMATION_SCHEMA.
- **Evidence**: `docs/api-reference/data-management-api.md`, `docs/operations/` (no SoR documentation found)

#### DATA-Q5: Temporal Metadata and Freshness — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Druid mandates a `__time` column for all datasources (timestamp required for ingestion). Segments have version strings based on creation timestamps. Datasource metadata includes creation and modification timestamps via system tables (`sys.segments`, `sys.tasks`). However, no `Cache-Control`, `X-Data-Age`, `last_refreshed`, or data freshness headers were found in API responses. Druid does not signal whether query results are from real-time or historical segments.
- **Gap**: Temporal metadata is present in the data model (`__time` column, segment versions) but not exposed in API response headers. Agents cannot determine data freshness from API responses alone.
- **Compensating Controls**:
  - Query `sys.segments` to determine the most recent segment version for a datasource
  - Include data freshness metadata in agent tool responses by querying `MAX(__time)` alongside business queries
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement a wrapper or proxy that adds data freshness headers to Druid API responses based on segment metadata.
- **Evidence**: `docs/operations/metrics.md`, `docs/api-reference/data-management-api.md`

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Druid APIs use versioned URL patterns (`/druid/v2/`, `/druid/coordinator/v1/`, `/druid/indexer/v1/`). Database migration files exist for metadata store schema evolution. However, no breaking change detection tools (OpenAPI diff, buf breaking), consumer-driven contract tests (Pact), or automated API compatibility checks were found in the CI pipeline. CI includes comprehensive unit tests and static checks but no API contract testing.
- **Gap**: URL-based API versioning exists but no automated detection of breaking API changes in CI. Agent tool bindings could break silently when API responses change.
- **Compensating Controls**:
  - Pin agent tool definitions to specific API versions (e.g., `/druid/v2/sql`)
  - Monitor Druid release notes for API deprecation notices
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add API contract tests to the CI pipeline. Consider generating OpenAPI specs from JAX-RS annotations and adding OpenAPI diff checks to PRs that modify API classes.
- **Evidence**: `server/src/main/java/org/apache/druid/server/QueryResource.java` (`@Path("/druid/v2/")`), `.github/workflows/ci.yml`, `.github/workflows/static-checks.yml` (no API contract tests)

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: OpenTelemetry support exists via `extensions-contrib/opentelemetry-emitter`, which processes `ServiceMetricEvent` events for `query/time` metrics and supports W3C Trace Context (`traceparent` header propagation). Druid queries have `queryId` and `sqlQueryId` for correlation. Log4j2 is configured for logging (visible in docker-compose environment). However, OpenTelemetry is a contrib extension (not core), not loaded by default. The default logging configuration uses `PatternLayout` rather than JSON structured logging.
- **Gap**: Tracing capability exists but requires loading a contrib extension. Default logging is not JSON-structured. queryId/sqlQueryId provide correlation but are not automatically linked to distributed traces without the OpenTelemetry extension.
- **Compensating Controls**:
  - Load the `opentelemetry-emitter` extension and configure `traceparent` propagation in agent requests
  - Configure Log4j2 to use `JsonLayout` for structured logging
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `opentelemetry-emitter` to `druid.extensions.loadList` and configure structured JSON logging in production deployments. Pass `traceparent` headers from agent requests to enable end-to-end tracing.
- **Evidence**: `extensions-contrib/opentelemetry-emitter/README.md`, `distribution/docker/environment` (DRUID_LOG4J with PatternLayout), `server/src/main/java/org/apache/druid/server/QueryResource.java` (QUERY_ID_RESPONSE_HEADER)

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Druid has a built-in alert system that emits JSON alert objects with severity levels (anomaly, component-failure, service-failure) as documented in `docs/operations/alerts.md`. The Prometheus emitter extension (`extensions-contrib/prometheus-emitter`) exports extensive metrics including `query/time`, `query/failed/count`, `query/timeout/count`, and Jetty request metrics. Metrics documentation (`docs/operations/metrics.md`, 658 lines) covers query, ingestion, coordination, and system metrics. However, no pre-configured alerting thresholds or CloudWatch alarms are defined in the repository.
- **Gap**: Metric emission infrastructure is rich but alerting thresholds are deployment-dependent. No pre-configured alerts for error rate spikes or latency degradation on agent-facing APIs.
- **Compensating Controls**:
  - Deploy the Prometheus emitter and configure alerting rules in Prometheus/Grafana
  - Use Druid's built-in alert emitter with a monitoring service subscription
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Deploy the Prometheus emitter, export `query/time`, `query/failed/count`, and `query/bytes` metrics, and configure alerting rules for error rate > 5% and p99 latency > configured threshold.
- **Evidence**: `docs/operations/alerts.md`, `docs/operations/metrics.md`, `extensions-contrib/prometheus-emitter/`

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No IaC files (Terraform, CloudFormation, CDK) found in the repository. Apache Druid is an open-source project — deployment infrastructure is expected to be defined in downstream consumer repositories. The Docker distribution (`distribution/docker/`) provides a reference deployment with Dockerfile and docker-compose.yml. No drift detection configuration found.
- **Gap**: No infrastructure-as-code in the repository. The agent-facing integration surface (API gateway, IAM roles, networking) must be defined by the deploying organization.
- **Compensating Controls**:
  - Deploy Druid using community Helm charts or CDK constructs with IaC governance
  - Define the agent-facing API gateway and IAM roles in a separate IaC repository
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Create IaC templates (Terraform modules or CDK constructs) for deploying Druid with agent-ready configuration including API Gateway, IAM roles, and network policies.
- **Evidence**: No `.tf`, `.cfn.yaml`, or `cdk.json` files found. `distribution/docker/Dockerfile`, `distribution/docker/docker-compose.yml`

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive CI/CD via GitHub Actions: unit tests (`ci.yml` with JDK 17/21 matrix), integration tests (`docker-tests.yml`), static checks (`static-checks.yml` with packaging, Maven checks, strict compilation, OpenRewrite), CodeQL security scanning (`codeql.yml`), PR checks (`pr-checks.yml`), and JaCoCo coverage reporting. However, no API contract testing — no Pact tests, no OpenAPI spec validation, no schema comparison tools, and no breaking change detection in the pipeline.
- **Gap**: Strong CI/CD pipeline but no automated API contract testing. API changes that break agent tool bindings are not caught in CI.
- **Compensating Controls**:
  - Extensive integration tests provide indirect API compatibility validation
  - Manual API review during PR process
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add API contract tests to the CI pipeline. Start with snapshot-based API response testing for the SQL and Tasks APIs that agents will consume most frequently.
- **Evidence**: `.github/workflows/ci.yml`, `.github/workflows/static-checks.yml`, `.github/workflows/docker-tests.yml`, `.github/workflows/codeql.yml`

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: `docs/operations/rolling-updates.md` documents a rolling update procedure with a specific order (Historical → Middle Manager → Broker → Router → Overlord → Coordinator) and reverse order for rollback. Middle Managers support graceful termination via the disable API. Autoscaling-based replacement is supported for Middle Managers. However, no automated rollback triggers (CodeDeploy, canary deployment, traffic shifting) are defined in the repository.
- **Gap**: Rolling update/rollback procedure is documented but manual. No automated rollback triggers or canary deployment configuration.
- **Compensating Controls**:
  - Follow the documented rollback order for manual rollback
  - Use Kubernetes rolling deployment strategies with readiness probes for automated rollback
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement automated rollback triggers in the deployment pipeline. If deploying on Kubernetes, use rollout strategies with health checks that automatically roll back on API error rate increases.
- **Evidence**: `docs/operations/rolling-updates.md`

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Extensive test infrastructure: unit tests across all modules, QTest (quidem-ut) for SQL query testing, integration tests via Docker, JaCoCo coverage, JDK 17/21 matrix. Resource test files exist (`OverlordResourceTest.java`, `SupervisorResourceTest.java`, `CatalogResourceTest.java`, etc.). However, these are unit/integration tests, not dedicated API contract tests. No automated API response format validation against a specification.
- **Gap**: API resource tests exist but no dedicated API contract tests or response format validation.
- **Compensating Controls**:
  - Existing resource tests provide indirect API compatibility validation
  - QTest framework validates SQL query behavior
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add explicit API response format assertions to existing resource tests. Consider E2E API tests in the docker-tests workflow.
- **Evidence**: `.github/workflows/ci.yml`, `indexing-service/src/test/java/org/apache/druid/indexing/overlord/http/OverlordResourceTest.java`, `quidem-ut/`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Druid's S3 extension supports server-side encryption via a pluggable `ServerSideEncryption` interface with implementations for KMS (`KmsServerSideEncryption`), S3-managed keys (`S3ServerSideEncryption`), customer-provided keys (`CustomServerSideEncryption`), and noop. The encryption type is configurable via `druid.storage.sse.type`. However, no encryption configuration is found in the default docker-compose setup (`druid_storage_type=local` with no encryption). The metadata store (PostgreSQL) has no encryption configuration in the docker-compose setup.
- **Gap**: Encryption-at-rest capability exists for S3 deep storage but is not configured by default. Local storage and metadata store are unencrypted in the reference deployment.
- **Compensating Controls**:
  - Configure `druid.storage.sse.type=kms` for S3 deep storage in production
  - Use RDS with encryption enabled for the metadata store
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure S3 SSE-KMS for deep storage and enable encryption at rest for the metadata store (RDS encryption, EBS encryption). Document encryption requirements in the deployment guide.
- **Evidence**: `extensions-core/s3-extensions/src/main/java/org/apache/druid/storage/s3/KmsServerSideEncryption.java`, `extensions-core/s3-extensions/src/main/java/org/apache/druid/storage/s3/ServerSideEncryption.java`, `distribution/docker/environment` (`druid_storage_type=local`)

## INFOs — Architecture and Design Inputs

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Druid SQL queries (the primary read-only agent surface) are inherently idempotent. Write endpoints (POST `/druid/indexer/v1/task`, POST `/druid/coordinator/v1/datasources`) lack explicit idempotency key support. Task IDs are auto-generated rather than client-provided.
- **Implication**: For read-only agents, idempotency is not a concern. If scope expands to write-enabled, idempotency key support would need to be added to write endpoints.
- **Recommendation**: If write-enabled scope is planned, evaluate adding client-provided idempotency keys to the task submission API.
- **Evidence**: `docs/api-reference/tasks-api.md`, `server/src/main/java/org/apache/druid/server/QueryResource.java`

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: Druid APIs return JSON (`MediaType.APPLICATION_JSON`) as the primary format, with optional SMILE binary support (`SmileMediaTypes.APPLICATION_JACKSON_SMILE`). The SQL API returns results as JSON arrays with column metadata. Native query API also returns JSON.
- **Implication**: JSON is an ideal format for LLM consumption. SMILE binary format would require additional parsing. Agent tools should specify `Accept: application/json` to ensure text-based responses.
- **Recommendation**: Ensure agent tools set `Accept: application/json` headers. The SQL API's JSON response format is well-suited for agent consumption.
- **Evidence**: `server/src/main/java/org/apache/druid/server/QueryResource.java` (`@Produces` annotations), `docs/api-reference/sql-api.md`

### API-Q7: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: Druid supports event/metric emission via a pluggable emitter framework with extensions for Kafka (`extensions-contrib/kafka-emitter`), Prometheus (`extensions-contrib/prometheus-emitter`), OpenTelemetry, StatsD, Graphite, and InfluxDB. These emit operational metrics (query time, ingestion status, segment events) rather than business state change events. No webhook callback endpoints for state changes (e.g., "ingestion completed", "compaction finished") are available.
- **Implication**: Agents cannot subscribe to state change events from Druid. Proactive agent patterns (reacting to ingestion completion, schema changes) would require polling or building an adapter on top of the emitter framework.
- **Recommendation**: For future proactive agent patterns, build a webhook adapter that subscribes to Druid's emitter events and triggers agent workflows.
- **Evidence**: `extensions-contrib/kafka-emitter/`, `extensions-contrib/prometheus-emitter/`, `docs/operations/metrics.md`

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No `X-RateLimit-Remaining`, `Retry-After`, or similar rate limit headers found in API response code. Druid's documentation recommends deploying an API gateway for throttling. Query scheduling provides internal concurrency limits but these are not exposed to clients via headers.
- **Implication**: Agents have no visibility into remaining rate budget. Self-throttling must be implemented at the agent layer rather than being guided by server headers.
- **Recommendation**: When deploying an API gateway, configure it to return rate limit headers that agent tools can consume for self-throttling.
- **Evidence**: `docs/operations/security-overview.md`, `server/src/main/java/org/apache/druid/server/QueryResource.java` (response headers)

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Druid uses optimistic concurrency at the metadata store level for segment publishing. Segment versioning provides implicit conflict resolution — newer versions supersede older ones. The QueryScheduler uses resilience4j Bulkhead for query concurrency control. For read-only agents, these controls are sufficient since queries do not create write conflicts.
- **Implication**: For read-only agents, concurrency controls are adequate. If scope expands to write-enabled operations, explicit concurrency controls for multi-agent write scenarios would need evaluation.
- **Recommendation**: No action needed for read-only scope. Document concurrency constraints for future write-enabled agent planning.
- **Evidence**: `server/src/main/java/org/apache/druid/server/QueryScheduler.java`, `pom.xml` (resilience4j-bulkhead)

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits per agent identity found. Druid's QueryScheduler provides query concurrency limits, and query laning can reserve capacity by lane, but there are no per-identity spend limits, record modification limits, or session-scoped operation caps.
- **Implication**: For read-only agents, blast radius is limited to query resource consumption (CPU, memory). If scope expands to write-enabled, transaction limits would be critical.
- **Recommendation**: For read-only agents, configure query laning to limit agent traffic to a specific lane with bounded capacity.
- **Evidence**: `server/src/main/java/org/apache/druid/server/QueryScheduler.java`

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Druid supervisors have lifecycle states (RUNNING, SUSPENDED, PENDING). Tasks have lifecycle states (RUNNING, SUCCESS, FAILED, WAITING). Supervisor suspension is a form of pause-before-action. However, there is no explicit draft/pending state for data query operations — queries execute immediately upon submission.
- **Implication**: Read-only agents execute queries immediately; no approval step is needed for reads. If scope expands to write-enabled (task submission), supervisor suspension could serve as a partial HITL mechanism.
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: `docs/api-reference/supervisor-api.md`, `docs/api-reference/tasks-api.md`

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable approval gates found in the Druid codebase. There are no human-approval steps in task, compaction, or query workflows. All operations execute immediately upon API call.
- **Implication**: Read-only agents do not need approval gates for query execution. If scope expands to write-enabled, approval gates would need to be implemented at the agent orchestration layer.
- **Recommendation**: No action needed for read-only scope. For future write-enabled scope, implement approval gates in the agent orchestration framework.
- **Evidence**: `docs/api-reference/tasks-api.md`, `docs/api-reference/supervisor-api.md`

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Druid field names in APIs are generally semantic and human-readable: `dataSource`, `interval`, `segments`, `queryType`, `granularity`, `filter`, `aggregator`, `dimension`, `metric`. System table columns use clear names (`datasource`, `start`, `end`, `version`, `is_active`, `is_published`, `is_available`). Some internal metrics use abbreviated but still readable names (e.g., `query/time`, `query/bytes`, `segment/scan/active`).
- **Implication**: LLM-based agents can reason effectively about Druid field names without needing a data dictionary lookup. Field names are self-documenting.
- **Recommendation**: Maintain the current clear naming convention. No action needed.
- **Evidence**: `docs/api-reference/sql-api.md`, `docs/api-reference/api-reference.md`, `server/src/main/java/org/apache/druid/server/QueryResource.java`

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: Druid has built-in system tables (`sys` schema) including `sys.segments`, `sys.tasks`, `sys.supervisors`, `sys.server_segments` that provide a metadata layer for datasource discovery. INFORMATION_SCHEMA tables provide column-level metadata for each datasource. No external data catalog (Glue, Collibra, Alation, DataHub) integration found.
- **Implication**: Druid's built-in system tables provide sufficient metadata for agent tool discovery. Agents can query `INFORMATION_SCHEMA.COLUMNS` to discover datasource schemas and `sys.segments` for datasource inventory.
- **Recommendation**: Use INFORMATION_SCHEMA and system tables as the metadata discovery layer for agent tools. Consider integrating with an external data catalog for cross-system metadata if Druid is part of a larger data platform.
- **Evidence**: `docs/operations/security-user-auth.md` (SYSTEM_TABLE resource type), `docs/api-reference/sql-api.md`

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: Druid emits extensive business-level metrics via its emitter framework: `query/time`, `query/bytes`, `query/count`, `query/success/count`, `query/failed/count`, `query/timeout/count`, `sqlQuery/time`, `sqlQuery/bytes`, `ingest/events/processed`, `ingest/events/thrownAway`, `ingest/events/unparseable`, `segment/count`, `segment/size`, and many more. The metrics documentation (`docs/operations/metrics.md`) spans 658 lines covering Router, Broker, Historical, Realtime, Coordinator, and General categories.
- **Implication**: These metrics provide rich signals for monitoring agent behavior against Druid — query patterns, latency changes, error rates, and data ingestion health can all be tracked.
- **Recommendation**: Deploy the Prometheus or Kafka emitter and create dashboards tracking agent-specific query patterns (filtering by agent identity in query context).
- **Evidence**: `docs/operations/metrics.md` (658 lines), `extensions-contrib/prometheus-emitter/`, `extensions-contrib/kafka-emitter/`

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality dashboards, profiling reports, or completeness metrics found in the repository. Druid has segment-level quality indicators: rows per segment, compaction status (compacted vs uncompacted), segment size, and ingestion metrics (`ingest/events/processed`, `ingest/events/thrownAway`, `ingest/events/unparseable`). These provide signals about data completeness at the ingestion level but not at the field level.
- **Implication**: Agents have no direct signal about data quality (null rates, duplicate detection, field completeness). Ingestion metrics can serve as a proxy for data quality at the pipeline level.
- **Recommendation**: Monitor ingestion metrics (`events/unparseable`, `events/thrownAway`) as proxy indicators for data quality. Consider building data profiling queries that agents can run to assess datasource quality.
- **Evidence**: `docs/operations/metrics.md` (ingestion metrics section)

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: BLOCKER (PASS — no gap)
- **Finding**: Druid exposes well-documented REST APIs across all service types: `/druid/v2/` (native queries), `/druid/v2/sql` (SQL queries), `/druid/coordinator/v1/` (coordination, segment management, rules), `/druid/indexer/v1/` (task management, supervisor management), `/druid/worker/v1/` (worker management), and `/status` (service status). These are documented in 14 markdown files under `docs/api-reference/`. JAX-RS `@Path` annotations in `server/src/main/java/org/apache/druid/server/` confirm the API implementation. No direct database access, file-based exchange, or UI automation is required for integration.
- **Gap**: None — documented REST interface exists.
- **Recommendation**: Use the SQL API (`POST /druid/v2/sql`) as the primary agent query interface for its simplicity and standardized SQL semantics.
- **Evidence**: `docs/api-reference/api-reference.md`, `docs/api-reference/sql-api.md`, `docs/api-reference/tasks-api.md`, `server/src/main/java/org/apache/druid/server/QueryResource.java` (`@Path("/druid/v2/")`)

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, GraphQL schema, or Smithy specification files found in the repository. APIs documented in Markdown only.
- **Gap**: No machine-readable spec. Agent tool definitions require manual authoring.
- **Recommendation**: Generate OpenAPI specs from JAX-RS annotations.
- **Evidence**: No OpenAPI/Swagger files found. `docs/api-reference/` (14 Markdown files)

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: DruidException provides structured errors with `errorCode`, `persona`, `category`, `errorMessage`, and `context`. ErrorResponse serializes to JSON. No explicit `retryable` flag.
- **Gap**: Missing retryable indicator in error responses.
- **Recommendation**: Add a `retryable` boolean to ErrorResponse or document category-to-retryability mapping.
- **Evidence**: `processing/src/main/java/org/apache/druid/error/DruidException.java`, `processing/src/main/java/org/apache/druid/error/ErrorResponse.java`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Read operations are inherently idempotent. Write endpoints lack explicit idempotency key support.
- **Gap**: Write endpoints lack idempotency keys (informational for read-only scope).
- **Recommendation**: No action for read-only scope.
- **Evidence**: `docs/api-reference/tasks-api.md`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: JSON primary format with optional SMILE binary. SQL API returns JSON arrays.
- **Gap**: None for agent consumption.
- **Recommendation**: Use `Accept: application/json` in agent tools.
- **Evidence**: `server/src/main/java/org/apache/druid/server/QueryResource.java`

#### API-Q6: Asynchronous Operation Support
- **Severity**: RISK-QUALITY
- **Finding**: Async submit-and-poll pattern for ingestion tasks. No webhook callbacks.
- **Gap**: Polling-only async monitoring; no push notifications.
- **Recommendation**: Implement polling with exponential backoff in agent tools.
- **Evidence**: `docs/api-reference/tasks-api.md`

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: Emitter framework supports Kafka, Prometheus, OpenTelemetry metric emission. No webhook callbacks for state changes.
- **Gap**: No push-based state change notifications.
- **Recommendation**: Build webhook adapter on emitter framework for future proactive agents.
- **Evidence**: `extensions-contrib/kafka-emitter/`, `docs/operations/metrics.md`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit headers in API responses. Docs recommend API gateway for throttling.
- **Gap**: No self-throttling signals for agents.
- **Recommendation**: Deploy API gateway with rate limit headers.
- **Evidence**: `docs/operations/security-overview.md`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER (PASS — capability exists)
- **Finding**: Druid supports pluggable authentication via `druid.auth.authenticatorChain`. Core extensions include: `druid-basic-security` (HTTP Basic auth with internal credential store), `druid-kerberos` (Kerberos/SPNEGO), and `druid-pac4j` (OIDC/SAML/OAuth2). TLS/mTLS is documented in `docs/operations/tls-support.md`. The system supports a `druid_system` internal user for service-to-service auth. By default, authentication is disabled (`allowAll` authenticator), but the capability for machine identity authentication clearly exists and is well-documented.
- **Gap**: None — machine identity authentication is supported via extensions. Default insecure configuration is expected for an OSS project and must be configured at deployment time.
- **Recommendation**: Enable `druid-basic-security` or `druid-pac4j` extension with dedicated agent service accounts. Configure mTLS for inter-service communication.
- **Evidence**: `docs/operations/auth.md`, `docs/operations/security-overview.md`, `docs/operations/tls-support.md`, `extensions-core/druid-basic-security/`, `extensions-core/druid-kerberos/`, `extensions-core/druid-pac4j/`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY (PASS — capability exists)
- **Finding**: Druid's authorization model supports resource types (DATASOURCE, CONFIG, EXTERNAL, STATE, SYSTEM_TABLE, QUERY_CONTEXT, VIEW) with actions (READ, WRITE). Permissions can be scoped per datasource and per action. `@ResourceFilters` annotations enforce per-resource authorization throughout the codebase. An agent identity can be granted READ-only access to specific datasources.
- **Gap**: None — scoped permissions are supported. Requires deployment-time configuration.
- **Recommendation**: Create agent-specific roles with READ-only permissions on specific datasources.
- **Evidence**: `docs/operations/security-user-auth.md`, `server/src/main/java/org/apache/druid/server/security/ResourceType.java`, `server/src/main/java/org/apache/druid/server/security/Action.java`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY (PASS — capability exists)
- **Finding**: Action-level authorization is built into the security model with READ and WRITE actions on each resource type. GET requests require READ permissions; POST and DELETE require WRITE permissions. This allows an agent to read datasources but not delete them.
- **Gap**: None — action-level authorization is supported.
- **Recommendation**: Assign agent identities READ-only action permissions. Ensure WRITE permission is not granted to read-only agents.
- **Evidence**: `docs/operations/security-user-auth.md` (Actions section), `server/src/main/java/org/apache/druid/server/security/Action.java`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: RISK-QUALITY
- **Finding**: Druid uses Escalator for internal service-to-service authentication. No JWT token exchange or on-behalf-of flow for distinguishing agent-as-self vs. agent-on-behalf-of-user.
- **Gap**: No delegated identity propagation.
- **Recommendation**: Use dedicated Druid user accounts per agent use case; pass user context in query context parameters.
- **Evidence**: `docs/operations/auth.md`, `server/src/main/java/org/apache/druid/server/security/Escalator.java`

#### AUTH-Q5: Credential Management
- **Severity**: RISK-QUALITY
- **Finding**: EnvironmentVariableDynamicConfigProvider and PasswordProvider support secret externalization. Default docker-compose uses hardcoded `POSTGRES_PASSWORD=FoolishPassword`.
- **Gap**: Secret management capability exists but default config has hardcoded credentials.
- **Recommendation**: Use environment variable or custom PasswordProvider for production. Remove hardcoded passwords from examples.
- **Evidence**: `distribution/docker/docker-compose.yml`, `distribution/docker/environment`, `docs/operations/dynamic-config-provider.md`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: SQLAuditManager and LoggingAuditManager exist. Request logging disabled by default. No immutable log storage configured.
- **Gap**: Audit logs in mutable metadata store. No tamper-evident logging.
- **Recommendation**: Enable request logging to immutable external sink.
- **Evidence**: `server/src/main/java/org/apache/druid/server/audit/SQLAuditManager.java`, `docs/operations/request-logging.md`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: Basic-security extension supports user deletion via REST API. Credential cache propagation is periodic, causing delay in revocation effectiveness.
- **Gap**: No instant identity suspension. Propagation delay.
- **Recommendation**: Enable cache push notifications; deploy API gateway with instant key revocation.
- **Evidence**: `docs/operations/security-user-auth.md`, `extensions-core/druid-basic-security/`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Task kill endpoints and supervisor reset available. Segment publishing is atomic. No saga pattern or compensation logic for multi-step operations.
- **Gap**: No compensation patterns for multi-step workflows.
- **Recommendation**: Document rollback procedures. For read-only agents, risk is mitigated since reads don't create partial state.
- **Evidence**: `docs/api-reference/tasks-api.md`, `server/src/main/java/org/apache/druid/server/coordinator/`

#### STATE-Q2: Queryable Current State
- **Severity**: RISK-QUALITY
- **Finding**: Druid exposes rich queryable state via REST APIs: `GET /druid/coordinator/v1/datasources` (datasource inventory), `GET /status` (service health), `GET /druid/coordinator/v1/loadstatus` (segment load state), `GET /druid/coordinator/v1/compaction/status` (compaction progress). System tables (`sys` schema) provide comprehensive queryable metadata about segments, tasks, supervisors, and servers.
- **Gap**: None — queryable state is well-exposed through REST APIs and system tables.
- **Recommendation**: Use system tables as the primary state query mechanism for agent tools.
- **Evidence**: `docs/api-reference/service-status-api.md`, `docs/api-reference/data-management-api.md`, `docs/operations/security-user-auth.md` (system tables)

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Optimistic concurrency for segment publishing. QueryScheduler with Bulkhead for query concurrency. Sufficient for read-only agents.
- **Gap**: Informational for read-only scope.
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: `server/src/main/java/org/apache/druid/server/QueryScheduler.java`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: resilience4j Bulkhead used for query concurrency only. No circuit breakers for external dependencies (ZooKeeper, metadata store, deep storage). Consul extension has circuit breaker reference but is not core.
- **Gap**: No circuit breakers for core external dependencies.
- **Recommendation**: Add circuit breakers around metadata store and deep storage connections. Use retry budgets at agent layer.
- **Evidence**: `pom.xml` (resilience4j-bulkhead), `server/src/main/java/org/apache/druid/server/QueryScheduler.java`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No per-client rate limiting. QueryScheduler limits total query parallelism but not per-identity. Documentation recommends API gateway for throttling.
- **Gap**: No external rate limiting. Agent traffic could overwhelm the system.
- **Recommendation**: Deploy API gateway with per-client rate limiting and usage plans.
- **Evidence**: `server/src/main/java/org/apache/druid/server/QueryScheduler.java`, `docs/operations/security-overview.md`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No per-identity transaction limits. QueryScheduler provides query concurrency limits via laning.
- **Gap**: Informational for read-only scope.
- **Recommendation**: Configure query laning to limit agent traffic.
- **Evidence**: `server/src/main/java/org/apache/druid/server/QueryScheduler.java`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path. Priority is P2, not on critical path.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Supervisors have lifecycle states (RUNNING, SUSPENDED, PENDING). Tasks have lifecycle states. No draft/pending state for query operations.
- **Gap**: Informational for read-only scope.
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: `docs/api-reference/supervisor-api.md`, `docs/api-reference/tasks-api.md`

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable approval gates. All operations execute immediately.
- **Gap**: Informational for read-only scope.
- **Recommendation**: No action for read-only scope. Implement at agent orchestration layer for future write-enabled scope.
- **Evidence**: `docs/api-reference/tasks-api.md`

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: docker-compose.yml provides complete local environment. No seed data scripts or production-equivalent staging config.
- **Gap**: Local testing available but lacks seed data and staging parity.
- **Recommendation**: Create seed data scripts for agent testing workflows.
- **Evidence**: `distribution/docker/docker-compose.yml`, `distribution/docker/environment`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: No data classification tags, field-level encryption, or PII detection tooling. Druid stores arbitrary user-provided data without built-in classification.
- **Gap**: No sensitive data classification system. Agent could retrieve unclassified PII.
- **Recommendation**: Audit datasources for PII. Implement field-level classification and access controls using VIEWs.
- **Evidence**: `distribution/docker/environment`, `docs/operations/security-user-auth.md`, `server/src/main/java/org/apache/druid/server/security/ResourceType.java`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No data residency enforcement. Deep storage location is deployment-configurable. No region validation.
- **Gap**: Data residency depends on deployment configuration, not application controls.
- **Recommendation**: Document residency requirements. Enforce at infrastructure layer.
- **Evidence**: `distribution/docker/environment`, `extensions-core/s3-extensions/`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK-QUALITY
- **Finding**: LIMIT clauses supported in SQL. Metadata APIs support filtering parameters. No cursor-based pagination.
- **Gap**: Result limiting via LIMIT exists but no cursor-based pagination.
- **Recommendation**: Use LIMIT and time-range filters in agent query templates.
- **Evidence**: `docs/api-reference/sql-api.md`, `docs/api-reference/tasks-api.md`

#### DATA-Q4: System of Record Designations
- **Severity**: RISK-QUALITY
- **Finding**: Datasources serve as system of record for analytics data by design. No formal SoR documentation.
- **Gap**: No formal system-of-record designations.
- **Recommendation**: Document SoR designations per datasource.
- **Evidence**: `docs/api-reference/data-management-api.md`

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK-QUALITY
- **Finding**: Mandatory `__time` column. Segment versions with timestamps. No freshness headers in API responses.
- **Gap**: Temporal metadata in data model but not in API response headers.
- **Recommendation**: Add freshness headers or query `MAX(__time)` alongside business queries.
- **Evidence**: `docs/operations/metrics.md`, `docs/api-reference/data-management-api.md`

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: No PII redaction in request logging or emitter output. Full queries logged including potential PII in filters.
- **Gap**: PII may leak into logs and metrics.
- **Recommendation**: Implement custom RequestLogger with PII scrubbing. Use filtered request logger.
- **Evidence**: `docs/operations/request-logging.md`, `distribution/docker/environment`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: Segment-level quality indicators (rows per segment, compaction status). Ingestion metrics for data completeness. No field-level quality scoring.
- **Gap**: Informational — no field-level data quality metrics.
- **Recommendation**: Use ingestion metrics as proxy. Build data profiling queries for agent use.
- **Evidence**: `docs/operations/metrics.md`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: Versioned URL patterns (`/druid/v2/`, `/druid/coordinator/v1/`). No breaking change detection in CI. No Pact or OpenAPI diff.
- **Gap**: URL versioning exists but no automated breaking change detection.
- **Recommendation**: Add API contract tests to CI pipeline.
- **Evidence**: `server/src/main/java/org/apache/druid/server/QueryResource.java`, `.github/workflows/ci.yml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Field names are semantic and human-readable (dataSource, interval, granularity, queryType). System tables use clear names.
- **Gap**: None — field naming is clear.
- **Recommendation**: Maintain current naming conventions.
- **Evidence**: `docs/api-reference/sql-api.md`, `docs/api-reference/api-reference.md`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: Built-in system tables (sys.segments, sys.tasks, sys.supervisors). INFORMATION_SCHEMA for column metadata. No external data catalog integration.
- **Gap**: None for agent discovery. External catalog integration is optional.
- **Recommendation**: Use INFORMATION_SCHEMA and system tables for agent tool discovery.
- **Evidence**: `docs/operations/security-user-auth.md`, `docs/api-reference/sql-api.md`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: OpenTelemetry emitter (contrib extension) supports W3C Trace Context. queryId/sqlQueryId for correlation. Default logging uses PatternLayout, not JSON.
- **Gap**: Tracing requires loading a contrib extension. Default logging is not structured.
- **Recommendation**: Load opentelemetry-emitter extension. Configure JsonLayout for structured logging.
- **Evidence**: `extensions-contrib/opentelemetry-emitter/README.md`, `distribution/docker/environment`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: Built-in alert system with severity levels. Prometheus emitter for metric export. 658 lines of metrics documentation. No pre-configured alerting thresholds.
- **Gap**: Rich metrics but no pre-configured alerts for agent-facing APIs.
- **Recommendation**: Deploy Prometheus emitter and configure alerting rules.
- **Evidence**: `docs/operations/alerts.md`, `docs/operations/metrics.md`, `extensions-contrib/prometheus-emitter/`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: Extensive business metrics: query/time, query/bytes, query/count, sqlQuery/time, ingestion metrics. Emitted via configurable emitter framework.
- **Gap**: None — rich business metrics available.
- **Recommendation**: Deploy Prometheus/Kafka emitter and create agent-behavior dashboards.
- **Evidence**: `docs/operations/metrics.md`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK-QUALITY
- **Finding**: No IaC in repository. Open-source project; deployment infrastructure is consumer-provided. Docker reference deployment available.
- **Gap**: No IaC. Agent-facing surface must be defined by deployer.
- **Recommendation**: Create IaC templates for agent-ready Druid deployment.
- **Evidence**: No `.tf`/`.cfn.yaml`/`cdk.json` found. `distribution/docker/Dockerfile`, `distribution/docker/docker-compose.yml`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive CI/CD (unit tests, integration tests, static checks, CodeQL, JaCoCo). No API contract testing.
- **Gap**: No automated API contract testing in CI.
- **Recommendation**: Add API contract tests for SQL and Tasks APIs.
- **Evidence**: `.github/workflows/ci.yml`, `.github/workflows/static-checks.yml`, `.github/workflows/docker-tests.yml`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: Documented rolling update/rollback procedure (docs/operations/rolling-updates.md). Manual process, no automated triggers.
- **Gap**: Rollback is manual. No automated canary or rollback triggers.
- **Recommendation**: Implement automated rollback with Kubernetes rolling deployments.
- **Evidence**: `docs/operations/rolling-updates.md`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: Extensive test infrastructure: unit tests across all modules, QTest (quidem-ut) for SQL query testing, integration tests via Docker, JaCoCo coverage, JDK 17/21 matrix. Resource test files found: `OverlordResourceTest.java`, `SupervisorResourceTest.java`, `CatalogResourceTest.java`, `BasicAuthorizerResourceTest.java`, and others. API endpoints are tested through these resource tests.
- **Gap**: While API resource tests exist, they are unit/integration tests, not dedicated API contract tests. No automated API response format validation against a specification.
- **Recommendation**: Supplement existing resource tests with explicit API response format assertions. Consider adding E2E API tests in the docker-tests workflow.
- **Evidence**: `.github/workflows/ci.yml`, `indexing-service/src/test/java/org/apache/druid/indexing/overlord/http/OverlordResourceTest.java`, `quidem-ut/` (SQL query tests)

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: RISK-QUALITY
- **Finding**: S3 ServerSideEncryption interface with KMS, S3-managed, and customer-provided key implementations. Not configured in default deployment. Metadata store unencrypted in docker-compose.
- **Gap**: Encryption capability exists for S3 but not configured by default. Local storage and metadata store unencrypted.
- **Recommendation**: Configure S3 SSE-KMS for deep storage. Use encrypted RDS for metadata store.
- **Evidence**: `extensions-core/s3-extensions/src/main/java/org/apache/druid/storage/s3/KmsServerSideEncryption.java`, `distribution/docker/environment`

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `server/src/main/java/org/apache/druid/server/QueryResource.java` | API-Q1, API-Q4, API-Q5, API-Q8, DISC-Q1, DISC-Q2, OBS-Q1 |
| `server/src/main/java/org/apache/druid/server/QueryResultPusher.java` | API-Q3 |
| `server/src/main/java/org/apache/druid/server/QueryScheduler.java` | STATE-Q3, STATE-Q4, STATE-Q5, STATE-Q6 |
| `server/src/main/java/org/apache/druid/server/StatusResource.java` | API-Q1 |
| `server/src/main/java/org/apache/druid/server/RequestLogLine.java` | DATA-Q6 |
| `server/src/main/java/org/apache/druid/server/security/ResourceType.java` | AUTH-Q2, DATA-Q1 |
| `server/src/main/java/org/apache/druid/server/security/Action.java` | AUTH-Q2, AUTH-Q3 |
| `server/src/main/java/org/apache/druid/server/security/Escalator.java` | AUTH-Q4 |
| `server/src/main/java/org/apache/druid/server/security/AuthenticationResult.java` | AUTH-Q4 |
| `server/src/main/java/org/apache/druid/server/audit/SQLAuditManager.java` | AUTH-Q6 |
| `server/src/main/java/org/apache/druid/server/audit/LoggingAuditManager.java` | AUTH-Q6 |
| `processing/src/main/java/org/apache/druid/error/DruidException.java` | API-Q3 |
| `processing/src/main/java/org/apache/druid/error/ErrorResponse.java` | API-Q3 |
| `extensions-core/s3-extensions/src/main/java/org/apache/druid/storage/s3/KmsServerSideEncryption.java` | ENG-Q5 |
| `extensions-core/s3-extensions/src/main/java/org/apache/druid/storage/s3/ServerSideEncryption.java` | ENG-Q5 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| No OpenAPI/Swagger/AsyncAPI files found | API-Q2 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/ci.yml` | ENG-Q2, ENG-Q4, DISC-Q1 |
| `.github/workflows/static-checks.yml` | ENG-Q2, DISC-Q1 |
| `.github/workflows/docker-tests.yml` | ENG-Q2 |
| `.github/workflows/codeql.yml` | ENG-Q2 |
| `.github/workflows/pr-checks.yml` | ENG-Q2 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `distribution/docker/Dockerfile` | ENG-Q1, HITL-Q3 |
| `distribution/docker/docker-compose.yml` | AUTH-Q5, HITL-Q3, ENG-Q1 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `pom.xml` | STATE-Q4 (resilience4j-bulkhead v1.3.1) |
| `web-console/package.json` | Step 1 (inventory) |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `distribution/docker/environment` | AUTH-Q5, AUTH-Q6, DATA-Q1, DATA-Q2, DATA-Q6, STATE-Q5, ENG-Q5, OBS-Q1 |

### Documentation
| File | Questions Referenced |
|------|---------------------|
| `docs/api-reference/api-reference.md` | API-Q1, DISC-Q2 |
| `docs/api-reference/sql-api.md` | API-Q1, API-Q5, DATA-Q3, DISC-Q2, DISC-Q3 |
| `docs/api-reference/tasks-api.md` | API-Q1, API-Q4, API-Q6, STATE-Q1, DATA-Q3, HITL-Q1, HITL-Q2 |
| `docs/api-reference/supervisor-api.md` | API-Q6, HITL-Q1, HITL-Q2 |
| `docs/api-reference/data-management-api.md` | DATA-Q4, DATA-Q5, STATE-Q2 |
| `docs/api-reference/service-status-api.md` | STATE-Q2 |
| `docs/operations/auth.md` | AUTH-Q1, AUTH-Q4, AUTH-Q7 |
| `docs/operations/security-overview.md` | AUTH-Q1, STATE-Q5, DATA-Q2, API-Q8 |
| `docs/operations/security-user-auth.md` | AUTH-Q2, AUTH-Q3, AUTH-Q7, DISC-Q3, DATA-Q1, STATE-Q2 |
| `docs/operations/tls-support.md` | AUTH-Q1 |
| `docs/operations/dynamic-config-provider.md` | AUTH-Q5 |
| `docs/operations/password-provider.md` | AUTH-Q5 |
| `docs/operations/request-logging.md` | AUTH-Q6, DATA-Q6 |
| `docs/operations/metrics.md` | OBS-Q2, OBS-Q3, DATA-Q5, DATA-Q7 |
| `docs/operations/alerts.md` | OBS-Q2 |
| `docs/operations/rolling-updates.md` | ENG-Q3 |

### Extensions
| File | Questions Referenced |
|------|---------------------|
| `extensions-core/druid-basic-security/` | AUTH-Q1, AUTH-Q7 |
| `extensions-core/druid-kerberos/` | AUTH-Q1 |
| `extensions-core/druid-pac4j/` | AUTH-Q1 |
| `extensions-contrib/opentelemetry-emitter/README.md` | OBS-Q1 |
| `extensions-contrib/prometheus-emitter/` | OBS-Q2 |
| `extensions-contrib/kafka-emitter/` | API-Q7, OBS-Q3 |
| `extensions-contrib/consul-extensions/` | STATE-Q4 |
