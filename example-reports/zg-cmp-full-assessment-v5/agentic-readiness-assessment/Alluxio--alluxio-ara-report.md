# Agentic Readiness Assessment Report

**Target**: alluxio-parent (Alluxio 2.10.0-SNAPSHOT monorepo)
**Date**: 2026-04-30
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**TD Version**: agentic-readiness-assessment
**Repository Type**: monorepo
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: java, storage, distributed
**Context**: Data orchestration / virtual distributed file system. JVM, distributed storage caching layer.

**Archetype Justification**: Alluxio is a distributed storage caching system with Masters managing persistent metadata state (journal + RocksDB metastore) and Workers caching data blocks. It exposes CRUD operations on file system entities (create, delete, rename, setAttribute) via REST proxy (S3 API, Paths/Streams REST) and gRPC services. This matches the stateful-crud archetype — it owns persistent state and exposes CRUD operations on business entities (files/directories).

- **Surface flags**:
  - has_persistent_data_store: true
  - has_http_rpc_surface: true
  - has_auth_surface: true
  - has_write_operations: true
  - has_logging_of_user_data: true

---

## Readiness Profile: Pilot-Ready (Safety Concerns)

**BLOCKERs**: 0 | **RISK-SAFETY**: 8 | **RISK-QUALITY**: 15 | **INFOs**: 18

With the DATA-Q1 reclassification from BLOCKER to INFO (see INFOs below), Alluxio has no remaining BLOCKERs. Proceed with a supervised pilot; prioritize RISK-SAFETY remediation before expanding agent scope.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 0 |
| RISK-SAFETY | 8 |
| RISK-QUALITY | 15 |
| INFO | 18 |
| N/A | 0 |
| Not Evaluated (extended) | 2 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 17
**Extended Questions Not Triggered**: 2
**Questions N/A (repo_type: monorepo)**: 0
**Service Archetype**: stateful-crud (auto-detected)

## BLOCKERs — Must Resolve Before Agent Deployment

_None. DATA-Q1 was previously BLOCKER under the binary "formal classification absent" rule; under the tiered model it resolves to INFO (see INFOs section). No BLOCKERs remain._

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Alluxio implements POSIX-style permissions (owner/group/other with read/write/execute bits) and extended ACLs (`AccessControlList.java`, `AclEntry.java`, `AclAction.java`). The ACL model supports per-file/directory permissions with `Mode` (rwx bits) and named user/group ACL entries. However, permissions are coarse-grained at the file/directory level — there is no concept of scoping an agent identity to specific API operations or resource subsets beyond the POSIX model. All principals with `read` permission on a directory can read all files within it; there is no attribute-based access control (ABAC) or fine-grained resource scoping.
- **Gap**: No ABAC or fine-grained resource scoping beyond POSIX permissions. An agent identity cannot be restricted to specific subtrees without manual ACL management on each directory. No IAM-style policy mechanism exists to grant "read-only access to /data/public but not /data/confidential" declaratively.
- **Compensating Controls**:
  - Use Alluxio's POSIX ACLs to restrict agent user identity to specific directory subtrees via `setAcl` operations
  - Deploy agents behind a gateway/proxy that restricts accessible paths before forwarding to Alluxio
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Create dedicated agent user identities with minimal ACLs. Use Alluxio's `setAcl` to restrict agent access to designated directories. Document the permission model for agent identities.
- **Evidence**: `core/common/src/main/java/alluxio/security/authorization/AccessControlList.java`, `core/common/src/main/java/alluxio/security/authorization/AclEntry.java`, `core/common/src/main/java/alluxio/security/authorization/Mode.java`

#### AUTH-Q6: Immutable Audit Logging — RISK-SAFETY ⚡

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Alluxio has a comprehensive audit logging framework. Three audit loggers are configured: `AUDIT_LOG` (master), `JOB_MASTER_AUDIT_LOG` (job master), `PROXY_AUDIT_LOG` (proxy). The `S3AuditContext` captures user (ugi), command, IP, bucket, object, allowed/succeeded status, and execution time. `AsyncUserAccessAuditLogWriter` writes audit entries asynchronously. Audit logging is configurable via `PropertyKey.PROXY_AUDIT_LOGGING_ENABLED`. However, audit logs are written to local rolling files (`RollingFileAppender` with MaxFileSize=10MB, MaxBackupIndex=100) — they are **not immutable or tamper-evident**. No S3 Object Lock, no CloudTrail integration, no write-once storage, and no log file validation/checksumming is configured.
- **Gap**: Audit logs exist but are not immutable. Local file-based rolling logs can be modified or deleted by any process with filesystem access. No tamper-evident storage mechanism.
- **Compensating Controls**:
  - Forward audit logs to an immutable log store (e.g., CloudWatch Logs with retention policy, S3 with Object Lock) using the remote log appender (`REMOTE_*_LOGGER`)
  - Enable Alluxio's log server (`logserver` module) to centralize logs, then ship to immutable storage
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure the remote log appender to ship audit logs to the centralized log server, then configure the log server to forward to an immutable store (S3 with Object Lock or CloudWatch Logs with resource policy preventing deletion).
- **Evidence**: `conf/log4j.properties` (MASTER_AUDIT_LOGGER, PROXY_AUDIT_LOGGER, JOB_MASTER_AUDIT_LOGGER), `core/server/proxy/src/main/java/alluxio/proxy/s3/S3AuditContext.java`, `core/server/proxy/src/main/java/alluxio/proxy/s3/S3Handler.java` (createAuditContext method)

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Alluxio's authentication model uses SASL (SIMPLE, CUSTOM, KERBEROS types). In SIMPLE mode, user identity is derived from the OS user or connection header. There is no built-in mechanism to suspend or revoke an individual agent identity without modifying filesystem ACLs or restarting services. The S3 proxy authentication filter (`S3AuthenticationFilter`) extracts user from the Authorization header but has no user-disable or blocklist capability. The `ImpersonationAuthenticator` supports impersonation but not identity suspension.
- **Gap**: No runtime agent identity suspension mechanism. Disabling an agent identity requires modifying ACLs on every path the agent accesses, or changing the underlying authentication provider. No API endpoint exists to disable/block a specific user identity.
- **Compensating Controls**:
  - Implement a deny-list at the proxy layer to reject requests from specific agent identities
  - Use external authentication (CUSTOM AuthenticationProvider) that delegates to an IdP supporting user disable
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement a CUSTOM AuthenticationProvider that delegates to an external IdP (e.g., LDAP, Cognito) supporting user disable/suspend. Alternatively, add a configurable deny-list to the S3AuthenticationFilter for immediate agent identity blocking.
- **Evidence**: `core/common/src/main/java/alluxio/security/authentication/DefaultAuthenticationServer.java`, `core/common/src/main/java/alluxio/security/authentication/ImpersonationAuthenticator.java`, `core/server/proxy/src/main/java/alluxio/proxy/s3/S3AuthenticationFilter.java`

#### STATE-Q1: Compensation and Rollback — RISK-SAFETY ⚡

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Alluxio uses a journal-based state management system (UFS journal or embedded Raft journal). The journal records all metadata mutations and supports replay for recovery. `FsOpPId` (operation ID) in the protobuf definitions suggests operation tracking for idempotency. However, there is no explicit compensation or rollback mechanism for multi-step operations at the API level. The journal provides crash recovery (redo log), not user-facing undo/compensation for failed multi-step workflows. If a multi-step operation (e.g., create directory + create files + rename) fails mid-sequence, there is no automatic compensation to undo completed steps.
- **Gap**: No application-level compensation or rollback API. Journal provides crash recovery but not user-facing undo. Multi-step agent workflows that fail mid-sequence cannot be automatically compensated.
- **Compensating Controls**:
  - For read-only agents (current scope), this is less critical since reads don't create partial state
  - Implement agent-side compensation logic that tracks operations and issues reverse operations on failure
- **Remediation Timeline**: 90–180 days
- **Recommendation**: For read-only agent scope, accept current state. If agent scope expands to write-enabled, implement explicit compensation endpoints or saga-style undo operations for multi-step file system operations.
- **Evidence**: `core/transport/src/main/proto/grpc/file_system_master.proto` (FsOpPId, CreateFile, Delete, Rename operations), `core/server/master/src/main/java/alluxio/master/journal/DefaultJournalMaster.java`

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Audit logs capture user identity (ugi), IP address, command, bucket name, and object name (file paths) as shown in `S3AuditContext.toString()`. The log format is: `succeeded=%b allowed=%b ugi=%s ip=%s cmd=%s bucket=%s object=%s executionTimeUs=%d`. File paths stored in Alluxio may contain PII in path names (e.g., `/users/john.doe@example.com/documents/`). No log scrubbing, PII masking, or redaction middleware was found in the codebase. The `PatternLayout` in log4j.properties outputs raw log messages without filtering.
- **Gap**: No PII redaction in audit logs or application logs. File paths (which may contain PII) are logged verbatim. No masking library or log scrubbing filter is integrated.
- **Compensating Controls**:
  - Restrict access to audit log files via filesystem permissions
  - Implement a log4j filter or custom appender that redacts known PII patterns before writing
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement a log4j PatternLayout wrapper or custom appender that redacts PII patterns (email addresses, SSNs, etc.) from file paths in audit log entries. Consider integrating with a PII detection library.
- **Evidence**: `core/server/proxy/src/main/java/alluxio/proxy/s3/S3AuditContext.java` (toString method), `conf/log4j.properties` (PROXY_AUDIT_LOGGER pattern)

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Alluxio has some rate limiting capabilities. `RateLimitInputStream` in the S3 proxy uses Guava `RateLimiter` to throttle data transfer rates. The master has a throttle subsystem (`DefaultThrottleMaster`, `SystemMonitor`, `FileSystemIndicator`, `ServerIndicator`) that monitors system metrics and can throttle operations based on system load. However, there is no per-client or per-identity rate limiting at the API layer. The Helm chart does not configure any API gateway throttling. No `X-RateLimit-Remaining` or `Retry-After` headers are returned.
- **Gap**: No per-identity API-layer rate limiting. The existing throttling is bandwidth-based (data transfer) and system-load-based (master throttle), not request-rate-based per client. A runaway agent loop could overwhelm the proxy with requests.
- **Compensating Controls**:
  - Deploy an API gateway (e.g., Kong, NGINX) in front of the Alluxio proxy with per-client rate limiting
  - Leverage the master's throttle system to protect against overload (already exists for system-level protection)
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add per-identity request rate limiting to the S3 proxy. The simplest approach is deploying an API gateway with rate limiting in front of the Alluxio proxy service. Return `X-RateLimit-Remaining` and `Retry-After` headers.
- **Evidence**: `core/server/proxy/src/main/java/alluxio/proxy/s3/RateLimitInputStream.java`, `core/server/master/src/main/java/alluxio/master/throttle/DefaultThrottleMaster.java`

#### DATA-Q2: Data Residency and Sovereignty — RISK-SAFETY ⚡

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Alluxio caches data from underlying file systems across multiple storage backends (S3, HDFS, GCS, OSS, COS, etc.) configured via mount points. Data is cached on Alluxio worker nodes, which may be in a different region than the original data. Since `has_persistent_data_store=true` and `has_logging_of_user_data=true`, the surface-flag downgrade to INFO does not apply. The archetype is `stateful-crud`, so the archetype downgrade to INFO does not apply. An agent reading cached data from Alluxio may retrieve data that was originally stored in a jurisdiction with residency requirements (GDPR, LGPD), and the cached copy on the Alluxio worker resides wherever the cluster is deployed. No data residency configuration or region-restriction mechanisms exist at the Alluxio application layer.
- **Gap**: No application-level data residency controls. Alluxio caches data across mount points without awareness of residency requirements. The caching layer could hold copies of region-restricted data on nodes outside the required jurisdiction. No mechanism prevents an agent from reading cached data that crosses compliance boundaries.
- **Compensating Controls**:
  - Ensure Alluxio cluster is deployed within the same region as the data's regulatory jurisdiction
  - Restrict mount points to only expose data from the same compliance region
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement region-aware mount point policies. Document which mount points contain region-restricted data. Configure agent access to only query mount points within the compliant region. Consider per-mount-point metadata tags for residency classification.
- **Evidence**: `underfs/s3a/`, `underfs/hdfs/`, `underfs/gcs/`, `integration/kubernetes/helm-chart/alluxio/values.yaml`, `core/common/src/main/java/alluxio/conf/PropertyKey.java`

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Alluxio calls external Under File Systems (S3, HDFS, GCS, Azure, etc.) for data operations. The codebase has a comprehensive retry framework (`core/common/src/main/java/alluxio/retry/`) with `ExponentialBackoffRetry`, `ExponentialTimeBoundedRetry`, `CountingRetry`, `TimeoutRetry`, and `RetryUtils`. The `ActiveSyncManager` uses `ExponentialTimeBoundedRetry` for UFS sync operations. However, no circuit breaker pattern (Resilience4j, Hystrix, custom circuit breaker) was found in the codebase. When a UFS backend becomes unavailable, Alluxio will retry with exponential backoff but has no circuit breaker to fail fast and protect itself from cascading failures. The master and worker processes will continue attempting UFS operations, accumulating blocked threads.
- **Gap**: No circuit breaker pattern for external UFS dependencies. Retry logic exists but without fast-fail circuit breaking. A degraded UFS backend could cause cascading resource exhaustion in Alluxio master/worker processes.
- **Compensating Controls**:
  - The master throttle system (`DefaultThrottleMaster`) provides system-level load protection that partially mitigates cascading failures
  - Timeout configurations on UFS operations prevent indefinite blocking
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement circuit breakers for UFS operations — when a UFS backend exceeds error/latency thresholds, fail fast rather than queuing retries. Consider Resilience4j integration or a custom circuit breaker wrapping UFS client calls.
- **Evidence**: `core/common/src/main/java/alluxio/retry/ExponentialBackoffRetry.java`, `core/common/src/main/java/alluxio/retry/RetryUtils.java`, `core/server/master/src/main/java/alluxio/master/file/activesync/ActiveSyncManager.java`, `core/server/master/src/main/java/alluxio/master/throttle/DefaultThrottleMaster.java`

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No standalone OpenAPI/Swagger spec file (openapi.yaml, swagger.json, etc.) exists in the repository. The REST proxy handlers (`PathsRestServiceHandler.java`, `S3RestServiceHandler.java`) use Swagger `@ApiOperation` annotations, and a `swagger-maven-plugin` (version 3.1.7) is configured in the root `pom.xml` to generate specs at compile time. The gRPC interfaces are fully defined in `.proto` files (`file_system_master.proto`, `block_master.proto`, `block_worker.proto`, `meta_master.proto`), which serve as machine-readable specs for the gRPC surface. However, no pre-generated OpenAPI spec file is committed to the repository.
- **Gap**: No committed OpenAPI spec file for the REST API surface. Agent tool generation for the REST API requires running the Maven build to generate the spec. The gRPC proto files are available but require tooling to convert to agent tool definitions.
- **Compensating Controls**:
  - Use the swagger-maven-plugin to generate and commit the OpenAPI spec to the repository
  - Use the proto files directly for gRPC-based agent tool generation
- **Remediation Timeline**: 7–14 days
- **Recommendation**: Generate the OpenAPI spec via `swagger-maven-plugin` and commit it to the repository (e.g., `docs/api/openapi.yaml`). This enables automated agent tool generation without requiring a build.
- **Evidence**: `pom.xml` (swagger-maven-plugin configuration), `core/server/proxy/src/main/java/alluxio/proxy/PathsRestServiceHandler.java` (@ApiOperation annotations), `core/transport/src/main/proto/grpc/file_system_master.proto`

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The S3 API surface has well-structured error responses. `S3ErrorCode.java` defines 20+ error codes with code name, description, and HTTP status (e.g., `BAD_DIGEST`, `NO_SUCH_BUCKET`, `ACCESS_DENIED_ERROR`). `S3ErrorResponse` generates XML error responses following the AWS S3 error format. However, the Paths/Streams REST API uses `RestUtils` for error handling, which wraps exceptions in generic JSON responses without standardized error codes or a retryable/terminal distinction. The gRPC surface uses standard gRPC status codes.
- **Gap**: The Paths/Streams REST API lacks structured error codes with retryable classification. Only the S3 API has well-defined error codes. Agents consuming the Paths/Streams REST API cannot reliably distinguish retryable from terminal errors.
- **Compensating Controls**:
  - Use the S3-compatible API surface for agent integration (which has proper error codes)
  - Map HTTP status codes to retry logic at the agent layer (5xx = retryable, 4xx = terminal)
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Standardize error response format across all REST APIs with error code, message, and retryable boolean. Prioritize the S3 API for agent integration since it already has structured errors.
- **Evidence**: `core/server/proxy/src/main/java/alluxio/proxy/s3/S3ErrorCode.java`, `core/server/proxy/src/main/java/alluxio/proxy/s3/S3ErrorResponse.java`, `core/server/proxy/src/main/java/alluxio/proxy/PathsRestServiceHandler.java`

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The gRPC proto files use the `proto-backwards-compatibility` Maven plugin (version 1.0.7, `com.salesforce.servicelibs:proto-backwards-compatibility`) configured in `core/transport/pom.xml` to detect breaking changes in proto definitions. This provides automated breaking-change detection in the build for the gRPC surface. Proto files use `optional` fields and numeric field IDs, following protobuf backward compatibility conventions. However, the REST API has no versioning scheme (no `/v1/`, `/v2/` URL patterns) and no API contract testing framework (no Pact, no OpenAPI diff in CI).
- **Gap**: REST API lacks versioning and breaking change detection. gRPC surface has backward compatibility checking but REST API does not.
- **Compensating Controls**:
  - Prioritize gRPC surface for agent integration (which has backward compatibility checking)
  - Add OpenAPI spec diffing to the CI pipeline for the REST API
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Generate and commit the OpenAPI spec, then add an API diff step to CI that detects breaking changes in the REST surface. Consider versioning the REST API paths.
- **Evidence**: `core/transport/pom.xml` (proto-backwards-compatibility plugin), `pom.xml` (proto-backwards-compatibility dependency), `core/transport/src/main/proto/grpc/file_system_master.proto`

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Alluxio has OpenTelemetry (OTEL) agent and collector configurations in `integration/metrics/` (otel-agent-config.yaml, otel-collector-config.yaml, otel-agent-config-worker.yaml). The OTEL pipeline supports traces and metrics, exported to Jaeger (traces) and Prometheus (metrics). However, the OTEL integration is provided as Docker Compose sidecar configuration — it is not built into the application code. Logs use Log4j `PatternLayout` with `%d{ISO8601} %-5p [%t](%F:%L) - %m%n` format — this is not structured JSON. No correlation ID or trace ID propagation in log entries was found. Metrics are collected via Dropwizard Metrics and Prometheus client libraries.
- **Gap**: Logs are not structured (plain text, not JSON). No correlation ID in log entries. OTEL tracing is configured as a sidecar but not integrated into the application code for trace context propagation within log entries. Agent-initiated request failures cannot be correlated across services via log entries.
- **Compensating Controls**:
  - Deploy the OTEL agent sidecar (already configured) to capture traces
  - Use the Prometheus metrics endpoint for operational visibility
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Switch to structured JSON logging (e.g., Log4j2 JSONLayout). Add trace ID and correlation ID fields to log entries. Integrate OpenTelemetry SDK into the application code for automatic trace context propagation.
- **Evidence**: `integration/metrics/otel-agent-config.yaml`, `integration/metrics/otel-collector-config.yaml`, `conf/log4j.properties` (PatternLayout format)

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The Helm chart has a `metrics` section with various sinks (Console, CSV, JMX, Graphite, Slf4j, PrometheusMetricsServlet) but all are disabled by default. Prometheus scrape annotations are commented out. No alerting thresholds (CloudWatch alarms, Prometheus alerting rules, PagerDuty/OpsGenie integration) were found in the repository. The OTEL collector can export metrics to Prometheus but no alerting rules are defined.
- **Gap**: No alerting configuration exists in the repository. All metrics sinks are disabled by default. No error rate or latency thresholds are defined for automated alerting.
- **Compensating Controls**:
  - Enable Prometheus metrics in the Helm chart and deploy Prometheus alerting rules externally
  - Configure Grafana dashboards with alerting from the Prometheus endpoint
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Enable PrometheusMetricsServlet in Helm chart `values.yaml`. Define alerting rules for S3 proxy error rates, master RPC latency, and worker data transfer failures. Integrate with a notification system (PagerDuty, OpsGenie, SNS).
- **Evidence**: `integration/kubernetes/helm-chart/alluxio/values.yaml` (metrics section, all disabled), `integration/metrics/prometheus.yaml`, `conf/metrics.properties.template`

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Alluxio's infrastructure is defined via Helm charts (`integration/kubernetes/helm-chart/alluxio/`) and a Kubernetes operator (`integration/kubernetes/operator/`). Dockerfiles exist for container builds. However, there is no cloud-native IaC (no Terraform, CloudFormation, or CDK). The Helm chart defines API gateway-equivalent configuration (proxy ports, resource limits) but not API Gateway or WAF resources. No drift detection configuration was found. The GitHub Actions CI workflows include build and test automation but do not include Helm chart validation or drift detection.
- **Gap**: IaC is limited to Helm charts and Dockerfiles — no cloud-native IaC for the infrastructure layer (API gateways, IAM, networking, load balancers). No drift detection. The Helm chart changes are subject to PR review (GitHub PR process) but no automated plan review (e.g., `helm diff` in CI).
- **Compensating Controls**:
  - Add `helm diff` or `helm template` validation to the CI pipeline
  - Define the surrounding infrastructure (load balancer, IAM, networking) in Terraform/CloudFormation
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add cloud-native IaC (Terraform or CloudFormation) for the deployment infrastructure surrounding Alluxio (load balancer, IAM roles, network policies, secrets management). Add Helm chart validation to CI.
- **Evidence**: `integration/kubernetes/helm-chart/alluxio/` (Helm chart), `integration/kubernetes/operator/` (K8s operator), `integration/docker/Dockerfile`, `.github/workflows/` (CI workflows without Helm validation)

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: GitHub Actions CI pipelines exist for unit tests (`java8_unit_tests.yml`), integration tests (`java8_integration_tests.yml`, `java8_integration_tests_ft.yml`), fuse integration tests (`fuse_integration_tests.yml`), and checkstyle (`checkstyle.yml`). The `proto-backwards-compatibility` plugin detects breaking changes in protobuf definitions during the build. However, no API contract testing framework (Pact, consumer-driven contracts) exists. No OpenAPI spec validation step is in the CI pipeline. The REST API surface has no breaking change detection in CI.
- **Gap**: No consumer-driven contract testing. No OpenAPI spec validation in CI for the REST API. gRPC backward compatibility is checked via the proto-backwards-compatibility plugin, but the REST surface is uncovered.
- **Compensating Controls**:
  - The proto-backwards-compatibility plugin provides partial coverage for the gRPC surface
  - Integration tests provide functional validation of API behavior
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenAPI spec generation and validation to CI. Add a contract testing framework (Pact) for the S3 API surface. Ensure breaking REST API changes are detected before merge.
- **Evidence**: `.github/workflows/java8_unit_tests.yml`, `.github/workflows/java8_integration_tests.yml`, `core/transport/pom.xml` (proto-backwards-compatibility plugin)

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Alluxio provides multiple testing environments: `minicluster` module for embedded testing, Docker-based environments, Docker Compose files for metrics testing, Jenkins Dockerfiles for CI builds, and Vagrant-based multi-node environments. However, no production-equivalent staging environment with seed data is provided.
- **Gap**: Test environments exist for functional testing but no production-equivalent staging with realistic data shape.
- **Compensating Controls**:
  - Use the minicluster module for local agent testing
  - Use Docker-based environments for integration testing with representative data
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a staging environment configuration that mirrors production topology with representative data volumes.
- **Evidence**: `minicluster/`, `integration/docker/Dockerfile`, `integration/metrics/docker-compose-master.yaml`

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Helm charts support `helm rollback`. Kubernetes-native rollback via StatefulSet/Deployment. No canary deployments, no automated rollback triggers, no feature flags.
- **Gap**: Basic rollback only. No canary or automated rollback triggers.
- **Compensating Controls**:
  - Kubernetes-native rollback is functional for the proxy component
  - Manual `helm rollback` provides a recovery path
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add canary deployment configuration for the proxy. Configure automated rollback triggers.
- **Evidence**: `integration/kubernetes/helm-chart/alluxio/values.yaml`

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The repository contains 766 test files (*Test.java) and a dedicated `tests/` module with 257 test files for integration testing. The CI pipeline runs unit tests and integration tests across multiple test groups. Tests cover S3 API operations, file system client operations, master operations, and worker operations. However, no explicit API contract tests (Postman/Newman collections, REST Assured test suites targeting the S3/Paths/Streams APIs) were found. The tests are Java unit/integration tests, not dedicated API endpoint tests with input/output validation.
- **Gap**: No dedicated API test suite that validates input handling, output format, error responses, and edge cases for the agent-facing API surface. Tests are functional but not API-contract-focused.
- **Compensating Controls**:
  - Integration tests in `tests/` module provide functional coverage of API behavior
  - S3 proxy tests validate S3-compatible behavior
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a dedicated API test suite (REST Assured or Postman/Newman) that validates the S3 API and Paths/Streams REST API endpoints for correct response formats, error codes, pagination, and edge cases. Add this to the CI pipeline.
- **Evidence**: `tests/` (257 integration test files), `.github/workflows/java8_integration_tests.yml`, `.github/workflows/java8_unit_tests.yml`

#### STATE-Q2: Queryable Current State — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Alluxio exposes its current state in queryable form through multiple APIs. The Paths REST API provides `get-status` (returns `URIStatus` with file metadata) and `list-status` (returns list of `URIStatus` for directory children). The S3 API provides `HeadObject`, `GetObject`, `ListObjects`, and `ListBuckets`. The gRPC surface provides `GetStatus`, `ListStatus`, and `ListStatusPartial` RPCs. The `FileInfo` protobuf message contains comprehensive state fields: `fileId`, `name`, `path`, `ufsPath`, `length`, `blockSizeBytes`, `creationTimeMs`, `completed`, `folder`, `pinned`, `cacheable`, `persisted`, `owner`, `group`, `mode`, `mountPoint`, and more. Agents can inspect file/directory state before taking action.
- **Gap**: State is queryable but no explicit "read-before-write" enforcement exists — agents are not required to check current state before modifying it. For read-only scope, this is acceptable.
- **Compensating Controls**:
  - Agents can be designed to always query state (GET/HEAD) before any action
  - The `exists` endpoint provides a lightweight state check
- **Remediation Timeline**: N/A — current state is adequate for read-only scope
- **Recommendation**: Document the recommended read-before-act pattern for agent integration. For write-enabled scope expansion, consider enforcing conditional writes (If-Match/ETags).
- **Evidence**: `core/server/proxy/src/main/java/alluxio/proxy/PathsRestServiceHandler.java` (getStatus, listStatus, exists endpoints), `core/transport/src/main/proto/grpc/file_system_master.proto` (FileInfo, GetStatus, ListStatus RPCs), `core/server/proxy/src/main/java/alluxio/proxy/s3/S3BucketTask.java`

#### DATA-Q3: Selective Query Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Alluxio supports selective query operations with pagination and filtering. The S3 API implements `ListObjects` (v1 and v2) with `MaxKeys` (default 1000), `Marker`/`ContinuationToken` pagination, `Prefix` filtering, and `Delimiter` for hierarchical listing via `ListBucketOptions` and `ListBucketResult`. The `ListBucketResult` includes `IsTruncated` to signal partial results. The gRPC surface provides `ListStatusPartial` RPC with `batchSize`, `startAfter`/`offsetId`/`offsetCount` pagination options, `prefix` filtering, and `isTruncated` response field. The Paths REST `list-status` endpoint returns the full list without built-in pagination. The `ListStatusPartialPResponse` includes `fileCount` for total result size.
- **Gap**: The Paths REST `list-status` endpoint has no pagination — it returns all children in a single response. For directories with millions of files, this produces unbounded results. The S3 API and gRPC `ListStatusPartial` have proper pagination.
- **Compensating Controls**:
  - Use the S3 API or gRPC `ListStatusPartial` for agent integration (both have pagination)
  - Avoid the Paths REST `list-status` for large directories
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add pagination support to the Paths REST `list-status` endpoint. Prioritize the S3 API or gRPC `ListStatusPartial` for agent integration since they already support bounded result sets.
- **Evidence**: `core/server/proxy/src/main/java/alluxio/proxy/s3/ListBucketOptions.java` (maxKeys, marker, continuationToken), `core/server/proxy/src/main/java/alluxio/proxy/s3/ListBucketResult.java` (isTruncated, maxKeys), `core/transport/src/main/proto/grpc/file_system_master.proto` (ListStatusPartialPOptions, batchSize, isTruncated), `core/server/proxy/src/main/java/alluxio/proxy/PathsRestServiceHandler.java` (listStatus — no pagination)

#### DATA-Q4: System of Record Designations — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Alluxio is explicitly a caching layer, not a system of record. The authoritative data resides in the Under File Systems (S3, HDFS, GCS, etc.) mounted via `MountTable`. Alluxio's master metastore (Heap or RocksDB) manages file system metadata, and the `ActiveSyncManager` provides active synchronization between Alluxio metadata and UFS state for HDFS backends. The `persisted` field in `FileInfo` indicates whether a file has been written to the UFS. However, there is no formal system-of-record designation or documentation — the relationship between Alluxio's cached state and the UFS source of truth is implicit.
- **Gap**: No formal system-of-record designation. The UFS is the authoritative source but this is not documented or enforced. Agents may not know that Alluxio data could be stale relative to the UFS.
- **Compensating Controls**:
  - Document Alluxio's role as a cache, not a system of record, in agent integration guides
  - Use the `persisted` flag to verify data is written through to UFS
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Document the data authority model: UFS is the system of record, Alluxio is a caching layer. Expose cache freshness metadata to agents. Flag the `loadMetadata` sync behavior in agent documentation.
- **Evidence**: `core/server/master/src/main/java/alluxio/master/file/activesync/ActiveSyncManager.java`, `core/server/master/src/main/java/alluxio/master/file/meta/MountTable.java`, `core/transport/src/main/proto/grpc/file_system_master.proto` (FileInfo.persisted field)

#### DATA-Q5: Temporal Metadata and Freshness — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Alluxio provides temporal metadata on file system entities. The `FileInfo` protobuf message includes `creationTimeMs` (field 7), `lastModificationTimeMs` (field 14), and `lastAccessTimeMs` (field 31) — all stored as epoch milliseconds. The `MutableInode` class manages these timestamps internally. Timestamps are consistent (UTC epoch millis) across the API surface. However, there is no freshness signaling — no `Cache-Control`, `X-Data-Age`, or `last_refreshed` headers indicating whether the metadata returned is current, stale, or cached. The `ActiveSyncManager` syncs metadata from HDFS UFS periodically, but the sync interval is not communicated to API clients.
- **Gap**: Timestamps exist but no freshness signaling. An agent cannot determine whether the returned metadata reflects the current UFS state or a stale cached version. No `Cache-Control` or data-age headers in API responses.
- **Compensating Controls**:
  - Agents can trigger metadata sync via `loadMetadata` before reading (forces UFS check)
  - The `ActiveSyncManager` provides periodic sync for HDFS mounts
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add freshness headers (`X-Data-Age`, `X-Cache-Status`) to S3 proxy and REST API responses indicating when the metadata was last synced with the UFS. Document the metadata sync behavior and intervals for agent consumers.
- **Evidence**: `core/transport/src/main/proto/grpc/file_system_master.proto` (FileInfo: creationTimeMs, lastModificationTimeMs, lastAccessTimeMs), `core/server/master/src/main/java/alluxio/master/file/meta/MutableInode.java`, `core/server/master/src/main/java/alluxio/master/file/activesync/ActiveSyncManager.java`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Alluxio supports server-side encryption for data stored in S3 UFS backends via `PropertyKey.UNDERFS_S3_SERVER_SIDE_ENCRYPTION_ENABLED` (`alluxio.underfs.s3.server.side.encryption.enabled`). This delegates encryption to the UFS (S3's SSE). However, data cached on Alluxio worker nodes (local disk, SSD, MEM tiers) is **not encrypted at rest** by Alluxio itself. The master's metastore (RocksDB or Heap-based) stores metadata without application-level encryption. The Helm chart does not configure volume-level encryption for worker data directories. No KMS integration exists for Alluxio-managed data.
- **Gap**: Data cached on Alluxio workers is unencrypted at rest. Metadata in the master metastore (RocksDB) is unencrypted. Encryption is delegated to the UFS (S3 SSE) for persisted data, but cached copies on worker nodes are unprotected. An agent accessing cached data reads from unencrypted local storage.
- **Compensating Controls**:
  - Enable UFS-level encryption (S3 SSE) for all mounted backends
  - Use encrypted volumes (EBS encryption, LUKS) for Alluxio worker data directories at the infrastructure layer
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure encrypted volumes for Alluxio worker data directories in the Helm chart / IaC. Enable `UNDERFS_S3_SERVER_SIDE_ENCRYPTION_ENABLED=true` for all S3 mount points. Document the encryption-at-rest model for agent consumers.
- **Evidence**: `core/common/src/main/java/alluxio/conf/PropertyKey.java` (UNDERFS_S3_SERVER_SIDE_ENCRYPTION_ENABLED), `integration/kubernetes/helm-chart/alluxio/values.yaml`, `core/server/master/src/main/java/alluxio/master/metastore/rocks/RocksInodeStore.java`

## INFOs — Architecture and Design Inputs

### DATA-Q1: Sensitive Data Classification ⚡ (Tiered) — Demoted from BLOCKER

- **Severity**: INFO
- **Stage A**: Yes — Alluxio caches arbitrary UFS content and stores UFS credentials (S3/HDFS/GCS) in configuration.
- **B1 — API response scoping: CLEAR.** Configuration REST endpoints (`/master/info`, `/worker/info`, `/proxy/info`) use `useDisplayValue(true)` which triggers `InstancedConfiguration.java:131-133` to mask any property with `DisplayType.CREDENTIALS` as `"******"`. `CredentialPropertyKeys` provides a centralized, reflection-based registry of credential properties.
- **B2 — Access control differentiation: CLEAR.** POSIX-style permissions with owner/group/world mode bits enforced by `PermissionChecker` on every file operation; extended ACLs via `AccessControlList`.
- **B3 — Formal classification metadata: INFO.** `DisplayType.CREDENTIALS` is a property-level primitive; no file/path content classification.
- **Overall**: Only B3 fires → **DATA-Q1 = INFO**. UFS credentials are properly masked via the `DisplayType.CREDENTIALS` pattern.
- **Recommendation (aspirational)**: Add xattr-based path classification convention; integrate with UFS-level data governance.
- **Evidence**: `core/common/src/main/java/alluxio/conf/InstancedConfiguration.java:131-133`, `core/common/src/main/java/alluxio/conf/CredentialPropertyKeys.java`, `core/common/src/main/java/alluxio/conf/PropertyKey.java` (DisplayType enum), `core/common/src/main/java/alluxio/security/authorization/AccessControlList.java`.

### API-Q1: Documented API Interface — INFO

- **Severity**: INFO (BLOCKER resolved to INFO — see detailed findings)
- **Finding**: Alluxio exposes documented REST and gRPC interfaces. The REST proxy provides S3-compatible API (S3RestServiceHandler), Paths REST API (PathsRestServiceHandler), and Streams REST API (StreamsRestServiceHandler) with Swagger annotations. gRPC services (FileSystemMasterClientService, BlockMasterClientService, etc.) are fully defined in proto files. These constitute a well-defined programmatic interface — NOT direct database access or UI automation.
- **Implication**: Agents can integrate via the S3-compatible REST API or gRPC. The S3 API provides the most standardized integration surface for agents since it follows the AWS S3 API contract.
- **Recommendation**: Prioritize the S3-compatible API for agent integration due to its standardized interface, structured errors, and wide tooling support.
- **Evidence**: `core/server/proxy/src/main/java/alluxio/proxy/PathsRestServiceHandler.java`, `core/server/proxy/src/main/java/alluxio/proxy/s3/S3RestServiceHandler.java`, `core/transport/src/main/proto/grpc/file_system_master.proto`

### API-Q4: Idempotent Write Operations — INFO ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: `FsOpPId` (operation ID with mostSignificantBits/leastSignificantBits) exists in `FileSystemMasterCommonPOptions`, suggesting idempotency support for file system operations. The S3 multipart upload has explicit upload ID tracking. Read-only agents do not execute write operations, so idempotency is informational only.
- **Implication**: If agent scope expands to write-enabled, the FsOpPId mechanism may provide idempotency support, but its implementation would need verification.
- **Recommendation**: Verify FsOpPId-based idempotency behavior before enabling write operations for agents.
- **Evidence**: `core/transport/src/main/proto/grpc/file_system_master.proto` (FsOpPId message, FileSystemMasterCommonPOptions.operationId)

### API-Q5: Structured Response Format — INFO

- **Severity**: INFO
- **Finding**: Alluxio APIs return responses in multiple structured formats: JSON for Paths/Streams REST API, XML for S3 API (following AWS S3 response format), and Protobuf for gRPC services. All formats are machine-parseable. The S3 API also supports JSON response format for specific operations.
- **Implication**: LLMs and agent frameworks can consume JSON and XML formats effectively. The S3 API's XML format is standard and well-tooled.
- **Recommendation**: Use JSON endpoints (Paths/Streams REST) or the S3 API for agent integration. Protobuf/gRPC is also suitable with appropriate client libraries.
- **Evidence**: `core/server/proxy/src/main/java/alluxio/proxy/s3/S3Handler.java`, `core/server/proxy/src/main/java/alluxio/proxy/PathsRestServiceHandler.java`

### API-Q8: Rate Limit Documentation and Headers — INFO

- **Severity**: INFO
- **Finding**: No rate limit documentation or rate limit headers (`X-RateLimit-Remaining`, `Retry-After`) are returned by any API endpoint. The master throttle system adjusts system-level throttling dynamically but this is not exposed to clients. No `aws_api_gateway_usage_plan` or equivalent configuration exists.
- **Implication**: Agents have no signal to self-throttle. Without rate limit headers, agents will call at maximum speed until they hit system-level throttling or cause degradation.
- **Recommendation**: Add rate limit headers to the S3 proxy responses. Document rate limits in API documentation or OpenAPI spec.
- **Evidence**: `core/server/proxy/src/main/java/alluxio/proxy/s3/S3Handler.java`, `core/server/master/src/main/java/alluxio/master/throttle/DefaultThrottleMaster.java`

### AUTH-Q1: Machine Identity Authentication — INFO

- **Severity**: INFO (BLOCKER resolved — authentication exists)
- **Finding**: Alluxio supports machine identity authentication through multiple mechanisms: SASL authentication with SIMPLE, CUSTOM, and KERBEROS types. The S3 proxy has dedicated authentication via `S3AuthenticationFilter` with AWS Signature V2/V4 support (`AwsSignatureProcessor`, `AuthorizationV4Validator`). API key-style authentication is supported through S3 access key/secret key pairs. The `ImpersonationAuthenticator` supports service-to-service identity delegation. CUSTOM authentication allows plugging in external authentication providers.
- **Implication**: Agent identities can authenticate via S3 access keys (for the S3 API) or SASL (for gRPC). The CUSTOM authentication type allows integration with external IdPs for more robust agent identity management.
- **Recommendation**: Use S3 access key authentication for agent identities on the S3 API surface. For enhanced security, use CUSTOM authentication with an external IdP that supports per-agent credentials.
- **Evidence**: `core/common/src/main/java/alluxio/security/authentication/DefaultAuthenticationServer.java`, `core/server/proxy/src/main/java/alluxio/proxy/s3/S3AuthenticationFilter.java`, `core/server/proxy/src/main/java/alluxio/proxy/s3/signature/AwsSignatureProcessor.java`, `core/server/proxy/src/main/java/alluxio/proxy/s3/auth/Authenticator.java`

### AUTH-Q3: Action-Level Authorization — INFO

- **Severity**: INFO (RISK-SAFETY resolved — action-level auth exists)
- **Finding**: Alluxio enforces action-level authorization through POSIX-style permissions: read (R), write (W), execute (X) bits at the file/directory level. The `CheckAccessPRequest` gRPC method accepts `Bits` specifying the required access mode. The ACL model (`AclAction` enum with READ, WRITE, EXECUTE) allows per-entity action-level authorization. An agent can be granted read access but not write/delete access on specific paths.
- **Implication**: Action-level authorization is functional for file system operations. An agent with only read permission cannot delete or modify files.
- **Recommendation**: Configure agent identities with read-only ACLs (no write/execute bits) on all accessible paths to enforce least privilege.
- **Evidence**: `core/common/src/main/java/alluxio/security/authorization/AclAction.java`, `core/transport/src/main/proto/grpc/file_system_master.proto` (CheckAccessPRequest, Bits)

### AUTH-Q4: Identity Propagation and Delegation — INFO

- **Severity**: INFO (RISK calibrated for stateful-crud, but functional)
- **Finding**: Alluxio supports identity propagation through gRPC calls via `AuthenticatedClientUser` and `ClientContextServerInjector`. The `ImpersonationAuthenticator` allows services to impersonate users. The S3 proxy extracts user identity from the Authorization header and propagates it through Alluxio's internal calls. User context (owner, group) is maintained on file metadata.
- **Implication**: Agent identity can be propagated from the S3 proxy to the master/worker layer. The system can distinguish which agent identity initiated an operation.
- **Recommendation**: Ensure agent identities are propagated through all service calls. Use the impersonation framework if agents need to act on behalf of specific users.
- **Evidence**: `core/common/src/main/java/alluxio/security/authentication/AuthenticatedClientUser.java`, `core/common/src/main/java/alluxio/security/authentication/ClientContextServerInjector.java`, `core/common/src/main/java/alluxio/security/authentication/ImpersonationAuthenticator.java`

### AUTH-Q5: Credential Management — INFO

- **Severity**: INFO (RISK resolved — credentials managed via configuration)
- **Finding**: Alluxio manages credentials through configuration properties (`alluxio-site.properties`) and Helm chart secrets. The Helm chart has a `secrets` section for mounting external secrets (e.g., HDFS config). No hardcoded credentials were found in source code. Underfs modules (S3, GCS, etc.) use credential configuration properties. The `alluxio-site.properties.template` has commented-out security properties. No AWS Secrets Manager or HashiCorp Vault integration exists in the codebase, but credentials can be injected via environment variables and Kubernetes secrets.
- **Implication**: Credentials are externalized via configuration and Kubernetes secrets, which is adequate for Kubernetes deployments. No secrets management rotation service is integrated.
- **Recommendation**: Integrate with a secrets management system (AWS Secrets Manager, HashiCorp Vault) for credential rotation. Ensure agent credentials (S3 access keys) are stored in Kubernetes secrets with automated rotation.
- **Evidence**: `conf/alluxio-site.properties.template`, `integration/kubernetes/helm-chart/alluxio/values.yaml` (secrets section)

### STATE-Q3: Concurrency Controls — INFO ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Alluxio's master uses internal locking for concurrent metadata operations. The Raft-based journal provides consensus for distributed state. RocksDB metastore handles concurrent reads. File-level locking exists within the master for concurrent modifications. However, no application-level optimistic locking (ETags, version fields, If-Match headers) is exposed to clients.
- **Implication**: For read-only agents, concurrency controls are informational only. If agent scope expands to write-enabled, the lack of client-visible optimistic locking would need addressing.
- **Recommendation**: No action required for read-only scope. For write-enabled scope expansion, implement ETag/version-based optimistic locking on the S3 API.
- **Evidence**: `core/server/master/src/main/java/alluxio/master/metastore/rocks/RocksInodeStore.java`, `core/server/master/src/main/java/alluxio/master/journal/DefaultJournalMaster.java`

### STATE-Q6: Blast Radius and Transaction Limits — INFO ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits per agent identity were found (e.g., max records per bulk operation, max delete operations per session). The master throttle system provides system-level load protection but not per-identity business logic limits.
- **Implication**: For read-only agents, transaction limits are not critical. For future write-enabled scope, configurable limits would be necessary.
- **Recommendation**: No action for read-only scope. Plan per-identity transaction limits before enabling write operations.
- **Evidence**: `core/server/master/src/main/java/alluxio/master/throttle/DefaultThrottleMaster.java`

### HITL-Q1: Draft/Pending State — INFO ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Alluxio has `WritePType` (MUST_CACHE, CACHE_THROUGH, THROUGH, ASYNC_THROUGH) for controlling write semantics but no explicit draft/pending state for human approval of file system operations. No two-step commit pattern exists.
- **Implication**: Not relevant for read-only agents.
- **Recommendation**: No action for read-only scope.
- **Evidence**: `core/transport/src/main/proto/grpc/file_system_master.proto` (WritePType enum)

### HITL-Q2: Configurable Approval Gates — INFO ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable approval gate mechanism exists. Alluxio is designed for high-throughput file operations without human-in-the-loop approval.
- **Implication**: Not relevant for read-only agents.
- **Recommendation**: No action for read-only scope. Consider adding approval gates if agent scope expands to high-risk write operations (e.g., recursive delete).
- **Evidence**: No evidence of approval mechanisms found

### API-Q7: Event Emission for State Changes — INFO

- **Severity**: INFO
- **Finding**: Alluxio has a `JournalSink` interface (`core/server/common/src/main/java/alluxio/master/journal/sink/JournalSink.java`) that allows consumers to receive journal entries (state mutations) in real-time via `append(JournalEntry)` and `flush()` callbacks. This is an internal event mechanism for state change propagation. The `ActiveSyncManager` provides active synchronization for HDFS UFS changes. However, no external event emission exists — no webhook endpoints, no SNS/EventBridge/SQS/Kafka integration, no CDC pipeline, and no external event bus for notifying agents of file system state changes (file created, deleted, modified).
- **Implication**: Agents cannot subscribe to state change notifications. They must poll Alluxio's API to detect changes. The `JournalSink` interface provides an internal extension point that could be used to build an event bridge.
- **Recommendation**: For reactive agent use cases, implement a `JournalSink` that publishes state change events to an external event bus (SNS, SQS, EventBridge, or Kafka). This would enable event-driven agent patterns without polling.
- **Evidence**: `core/server/common/src/main/java/alluxio/master/journal/sink/JournalSink.java`, `core/server/master/src/main/java/alluxio/master/file/activesync/ActiveSyncManager.java`

### DATA-Q7: Data Quality Awareness — INFO

- **Severity**: INFO
- **Finding**: No data quality scores, completeness metrics, or data profiling reports were found in the codebase. Alluxio caches data from underlying file systems without assessing or tracking data quality. No null-rate monitoring, duplicate detection, or data freshness SLAs exist. The `MetricsStore` tracks operational metrics (bytes read/written, RPC counts, cache hit rates) but not data quality metrics. The Alluxio metrics framework (`MetricKey`, `MetricsSystem`) focuses on system health and performance, not data quality.
- **Implication**: Agents have no signal about the quality or completeness of data retrieved from Alluxio. Data quality is the responsibility of the upstream data producers (UFS owners).
- **Recommendation**: For agent use cases requiring data quality awareness, integrate with an external data quality framework (e.g., Great Expectations, Deequ) at the UFS level. Consider exposing data quality metadata via Alluxio's xattr mechanism.
- **Evidence**: `core/server/master/src/main/java/alluxio/master/metrics/MetricsStore.java`, `core/common/src/main/java/alluxio/metrics/MetricKey.java`

### OBS-Q3: Business Outcome Metrics — INFO

- **Severity**: INFO
- **Finding**: Alluxio publishes extensive operational metrics via the Dropwizard Metrics framework and Prometheus integration. The `MetricKey` class defines cluster-level metrics including `CLUSTER_BYTES_READ_CACHE`, `CLUSTER_BYTES_READ_UFS`, `CLUSTER_BYTES_WRITTEN_UFS`, `CLUSTER_CACHE_HIT_RATE`, `CLUSTER_CAPACITY_TOTAL`, `CLUSTER_CAPACITY_USED`, `CLUSTER_CAPACITY_FREE`, and `CLUSTER_ROOT_UFS_CAPACITY_TOTAL`. The `MetricsStore` aggregates worker and client metrics at the master level. These are infrastructure and caching performance metrics, not business outcome metrics. No custom business metrics (e.g., data pipeline completion rates, query success rates per tenant, agent interaction outcomes) are published.
- **Implication**: When agents consume Alluxio, the existing cache hit rate and throughput metrics provide operational visibility, but no business-outcome-level metrics exist to measure whether agent interactions produce good results.
- **Recommendation**: Define and publish business outcome metrics relevant to agent use cases (e.g., agent query success rate, data retrieval latency per agent, cache efficiency for agent workloads). Use the existing Prometheus metrics pipeline.
- **Evidence**: `core/common/src/main/java/alluxio/metrics/MetricKey.java` (CLUSTER_BYTES_READ_CACHE, CLUSTER_CACHE_HIT_RATE, etc.), `core/server/master/src/main/java/alluxio/master/metrics/MetricsStore.java`

### DISC-Q2: Semantically Meaningful Field Names — INFO

- **Severity**: INFO
- **Finding**: Proto field names are semantically meaningful and human-readable: `creationTimeMs`, `lastModificationTimeMs`, `blockSizeBytes`, `owner`, `group`, `path`, `ufsPath`. S3 API follows AWS naming conventions (`ListBucketResult`, `CompleteMultipartUploadResult`). No legacy abbreviations or cryptic codes found.
- **Implication**: Agent tool definitions can use field names directly without requiring a data dictionary.
- **Recommendation**: Maintain current naming conventions.
- **Evidence**: `core/transport/src/main/proto/grpc/file_system_master.proto` (FileInfo message)

### DISC-Q3: Data Catalog / Metadata Layer — INFO

- **Severity**: INFO
- **Finding**: No data catalog (Glue, Collibra, DataHub) or metadata layer exists. The Alluxio master's metastore (Heap or RocksDB) stores file system metadata (inodes, blocks, ACLs) but this is not a discoverable data catalog. The `table` module provides some table-level metadata management (table master) but it is a secondary feature.
- **Implication**: Agents cannot discover what data exists in Alluxio without listing directories. No semantic metadata layer describes the meaning of stored data.
- **Recommendation**: For agent use cases requiring data discovery, implement a metadata tagging layer using Alluxio's xattr support.
- **Evidence**: `core/server/master/src/main/java/alluxio/master/metastore/`, `table/` module

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO (BLOCKER question — resolved as no gap: documented API interfaces exist)
- **Finding**: Alluxio exposes documented REST and gRPC interfaces. REST proxy: S3-compatible API (`S3RestServiceHandler`), Paths REST API (`PathsRestServiceHandler`), Streams REST API (`StreamsRestServiceHandler`) with Swagger `@ApiOperation` annotations. gRPC: `FileSystemMasterClientService`, `BlockMasterClientService`, `MetaMasterClientService`, etc., defined in `.proto` files. No direct-database-access or UI-automation integration required.
- **Gap**: No gap — APIs exist and are documented via Swagger annotations and proto files.
- **Recommendation**: Prioritize S3 API for agent integration.
- **Evidence**: `core/server/proxy/src/main/java/alluxio/proxy/PathsRestServiceHandler.java`, `core/server/proxy/src/main/java/alluxio/proxy/s3/S3RestServiceHandler.java`, `core/transport/src/main/proto/grpc/file_system_master.proto`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: No committed OpenAPI spec file. Swagger annotations exist on REST handlers, and `swagger-maven-plugin` is configured. gRPC proto files serve as machine-readable specs for the gRPC surface.
- **Gap**: No pre-generated OpenAPI spec committed to repository.
- **Recommendation**: Generate and commit OpenAPI spec via swagger-maven-plugin.
- **Evidence**: `pom.xml` (swagger-maven-plugin), `core/server/proxy/src/main/java/alluxio/proxy/PathsRestServiceHandler.java`, proto files

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: S3 API has structured errors (`S3ErrorCode.java` with 20+ error codes, HTTP status mapping). Paths/Streams REST uses generic error handling via `RestUtils`. gRPC uses standard status codes.
- **Gap**: Paths/Streams REST API lacks structured error codes with retryable classification.
- **Recommendation**: Standardize error responses across all REST APIs; use S3 API for agent integration.
- **Evidence**: `core/server/proxy/src/main/java/alluxio/proxy/s3/S3ErrorCode.java`, `core/server/proxy/src/main/java/alluxio/proxy/s3/S3ErrorResponse.java`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: `FsOpPId` (operation ID) exists in protobuf, suggesting idempotency support. S3 multipart upload has upload ID tracking.
- **Gap**: Not evaluated for severity — read-only scope.
- **Recommendation**: Verify FsOpPId idempotency before enabling write agent scope.
- **Evidence**: `core/transport/src/main/proto/grpc/file_system_master.proto` (FsOpPId)

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: JSON (Paths/Streams REST), XML (S3 API), Protobuf (gRPC). All structured and machine-parseable.
- **Gap**: No gap.
- **Recommendation**: Use JSON or S3 API for agent integration.
- **Evidence**: `core/server/proxy/src/main/java/alluxio/proxy/s3/S3Handler.java`

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has operations >30s OR long-running workflows
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: Alluxio has a `JournalSink` interface that allows consumers to receive journal entries (state mutations) in real-time. The `ActiveSyncManager` provides active synchronization for HDFS UFS changes. No external event emission — no webhooks, SNS/EventBridge/SQS/Kafka, CDC pipeline, or external event bus.
- **Gap**: No external event emission for file system state changes. Agents must poll to detect changes.
- **Recommendation**: Implement a `JournalSink` that publishes state change events to an external event bus (SNS, SQS, EventBridge, or Kafka).
- **Evidence**: `core/server/common/src/main/java/alluxio/master/journal/sink/JournalSink.java`, `core/server/master/src/main/java/alluxio/master/file/activesync/ActiveSyncManager.java`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit headers returned. No rate limit documentation. Master throttle system is internal.
- **Gap**: No rate limit signaling to clients.
- **Recommendation**: Add `X-RateLimit-Remaining` and `Retry-After` headers.
- **Evidence**: `core/server/proxy/src/main/java/alluxio/proxy/s3/S3Handler.java`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO (BLOCKER resolved — machine identity authentication exists)
- **Finding**: SASL (SIMPLE, CUSTOM, KERBEROS) authentication. S3 proxy: AWS Signature V2/V4 authentication via `S3AuthenticationFilter`, `AwsSignatureProcessor`. Access key/secret key pairs supported.
- **Gap**: No gap — multiple authentication mechanisms available.
- **Recommendation**: Use S3 access keys or CUSTOM auth for agent identities.
- **Evidence**: `core/common/src/main/java/alluxio/security/authentication/DefaultAuthenticationServer.java`, `core/server/proxy/src/main/java/alluxio/proxy/s3/S3AuthenticationFilter.java`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: POSIX-style permissions + extended ACLs. Coarse-grained at file/directory level. No ABAC.
- **Gap**: No declarative policy mechanism for fine-grained agent scoping beyond POSIX ACLs.
- **Recommendation**: Use ACLs to restrict agent identities to specific directory subtrees.
- **Evidence**: `core/common/src/main/java/alluxio/security/authorization/AccessControlList.java`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: INFO (RISK-SAFETY resolved — action-level auth exists via POSIX R/W/X)
- **Finding**: POSIX R/W/X permissions enforced at file/directory level. `CheckAccessPRequest` validates access mode. `AclAction` enum: READ, WRITE, EXECUTE.
- **Gap**: No gap for basic action-level authorization.
- **Recommendation**: Configure read-only ACLs for agent identities.
- **Evidence**: `core/common/src/main/java/alluxio/security/authorization/AclAction.java`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO (RISK — functional identity propagation exists)
- **Finding**: `AuthenticatedClientUser`, `ClientContextServerInjector` propagate identity through gRPC. `ImpersonationAuthenticator` supports delegation. S3 proxy propagates user identity from Authorization header.
- **Gap**: No gap for basic identity propagation.
- **Recommendation**: Ensure agent identities are consistently propagated across all service tiers.
- **Evidence**: `core/common/src/main/java/alluxio/security/authentication/AuthenticatedClientUser.java`, `core/common/src/main/java/alluxio/security/authentication/ClientContextServerInjector.java`

#### AUTH-Q5: Credential Management
- **Severity**: INFO (RISK — credentials externalized via config/K8s secrets)
- **Finding**: Credentials managed via `alluxio-site.properties` and Helm chart secrets. No hardcoded credentials. No Secrets Manager/Vault integration.
- **Gap**: No automated credential rotation mechanism.
- **Recommendation**: Integrate with secrets management for rotation.
- **Evidence**: `conf/alluxio-site.properties.template`, `integration/kubernetes/helm-chart/alluxio/values.yaml`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Audit logging exists (3 audit loggers: master, job master, proxy). `S3AuditContext` captures user/command/IP/bucket/object. Logs written to local rolling files — not immutable.
- **Gap**: Audit logs not immutable or tamper-evident. Local rolling file storage.
- **Recommendation**: Ship audit logs to immutable storage (S3 Object Lock, CloudWatch).
- **Evidence**: `conf/log4j.properties`, `core/server/proxy/src/main/java/alluxio/proxy/s3/S3AuditContext.java`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: No runtime identity suspension mechanism. No deny-list or user disable API. SASL/S3 auth filter has no blocking capability.
- **Gap**: Cannot suspend an agent identity without modifying ACLs on every path or changing auth provider.
- **Recommendation**: Implement deny-list in S3AuthenticationFilter or use CUSTOM auth provider with IdP.
- **Evidence**: `core/server/proxy/src/main/java/alluxio/proxy/s3/S3AuthenticationFilter.java`, `core/common/src/main/java/alluxio/security/authentication/DefaultAuthenticationServer.java`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Journal-based crash recovery (redo log). `FsOpPId` for operation tracking. No user-facing compensation/rollback API.
- **Gap**: No application-level undo/compensation for multi-step operations.
- **Recommendation**: Accept for read-only scope. Implement saga patterns for write-enabled expansion.
- **Evidence**: `core/transport/src/main/proto/grpc/file_system_master.proto`, `core/server/master/src/main/java/alluxio/master/journal/DefaultJournalMaster.java`

#### STATE-Q2: Queryable Current State
- **Severity**: RISK-QUALITY
- **Finding**: Alluxio exposes its current state in queryable form through multiple APIs: Paths REST `get-status`/`list-status`, S3 API `HeadObject`/`GetObject`/`ListObjects`/`ListBuckets`, gRPC `GetStatus`/`ListStatus`/`ListStatusPartial`. The `FileInfo` message contains comprehensive state fields. Agents can inspect file/directory state before taking action.
- **Gap**: State is queryable but no explicit "read-before-write" enforcement exists.
- **Recommendation**: Document read-before-act pattern for agents. For write-enabled scope, consider conditional writes.
- **Evidence**: `core/server/proxy/src/main/java/alluxio/proxy/PathsRestServiceHandler.java`, `core/transport/src/main/proto/grpc/file_system_master.proto`

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Internal master locking. Raft journal consensus. RocksDB concurrent reads. No client-visible optimistic locking.
- **Gap**: No ETags/version fields for client-side concurrency control.
- **Recommendation**: No action for read-only scope.
- **Evidence**: `core/server/master/src/main/java/alluxio/master/metastore/rocks/RocksInodeStore.java`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: Alluxio calls external UFS backends (S3, HDFS, GCS, etc.). Comprehensive retry framework exists (`ExponentialBackoffRetry`, `ExponentialTimeBoundedRetry`, `RetryUtils`). No circuit breaker pattern (Resilience4j, Hystrix, custom) found. UFS failures trigger retries but no fast-fail circuit breaking.
- **Gap**: No circuit breaker for UFS dependencies. Degraded UFS backends could cause cascading resource exhaustion.
- **Recommendation**: Implement circuit breakers for UFS operations. Consider Resilience4j integration.
- **Evidence**: `core/common/src/main/java/alluxio/retry/ExponentialBackoffRetry.java`, `core/common/src/main/java/alluxio/retry/RetryUtils.java`, `core/server/master/src/main/java/alluxio/master/file/activesync/ActiveSyncManager.java`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: `RateLimitInputStream` for bandwidth throttling. Master throttle subsystem. No per-identity API-layer rate limiting.
- **Gap**: No per-client request rate limiting at the API layer.
- **Recommendation**: Deploy API gateway with per-client rate limiting.
- **Evidence**: `core/server/proxy/src/main/java/alluxio/proxy/s3/RateLimitInputStream.java`, `core/server/master/src/main/java/alluxio/master/throttle/DefaultThrottleMaster.java`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No per-identity transaction limits. System-level throttle only.
- **Gap**: No configurable per-agent transaction limits.
- **Recommendation**: No action for read-only scope.
- **Evidence**: `core/server/master/src/main/java/alluxio/master/throttle/DefaultThrottleMaster.java`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path (P2 priority)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No draft/pending state. `WritePType` controls write semantics but not approval workflows.
- **Gap**: N/A for read-only scope.
- **Recommendation**: No action for read-only scope.
- **Evidence**: `core/transport/src/main/proto/grpc/file_system_master.proto`

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No approval gate mechanism exists.
- **Gap**: N/A for read-only scope.
- **Recommendation**: No action for read-only scope.
- **Evidence**: No approval mechanism evidence found

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: Alluxio provides multiple testing environments: `minicluster` module for embedded testing, Docker-based environments (`integration/docker/Dockerfile`, `Dockerfile-dev`), Docker Compose files for metrics testing (`integration/metrics/docker-compose-master.yaml`, `docker-compose-worker.yaml`). Jenkins Dockerfiles for CI builds. Vagrant-based multi-node environments (`integration/vagrant/`). However, no production-equivalent staging environment with seed data is provided — the test environments are functional testing environments, not production-shape staging.
- **Gap**: Test environments exist for functional testing but no production-equivalent staging with realistic data shape. No seed data scripts for creating production-like conditions.
- **Recommendation**: Create a staging environment configuration that mirrors production topology (multi-master, multi-worker) with representative data volumes and mount points.
- **Evidence**: `minicluster/`, `integration/docker/Dockerfile`, `integration/metrics/docker-compose-master.yaml`, `integration/vagrant/`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification ⚡ (Tiered)
- **Severity**: INFO
- **Stage A**: Yes — Alluxio caches arbitrary UFS content which may include PII/credentials depending on source, and stores UFS connection credentials (S3 keys, HDFS Kerberos, GCS secrets) as configuration.
- **B1 — API response scoping: CLEAR.** All configuration REST endpoints (`/master/info`, `/worker/info`, `/proxy/info`) call `getConfigurationInternal()` which applies `ConfigurationValueOptions.defaults().useDisplayValue(true)`. In `InstancedConfiguration.java:131-133`, any property whose `PropertyKey.DisplayType == CREDENTIALS` is masked to `"******"` before serialization. `CredentialPropertyKeys` provides a centralized registry of credential properties via reflection.
- **B2 — Access control differentiation: CLEAR.** POSIX-style permissions with owner/group/world mode bits enforced by `PermissionChecker` on all file operations. Extended ACLs via `AccessControlList.java`. Audit context extracts owner/group/mode for logging.
- **B3 — Formal classification metadata: INFO.** `DisplayType.CREDENTIALS` is a property-level classification primitive but not a field-level file/path classification system.
- **Overall**: B1 CLEAR + B2 CLEAR + B3 INFO → **DATA-Q1 = INFO**. UFS credential exfiltration via config API is prevented by masking.
- **Recommendation (aspirational)**: Add xattr-based path classification convention; integrate with UFS-level data governance.
- **Evidence**: `core/common/src/main/java/alluxio/conf/InstancedConfiguration.java:131-133` (CREDENTIALS masking), `core/common/src/main/java/alluxio/conf/CredentialPropertyKeys.java`, `core/common/src/main/java/alluxio/conf/PropertyKey.java` (DisplayType.CREDENTIALS enum), `core/common/src/main/java/alluxio/security/authorization/AccessControlList.java`, `core/common/src/main/java/alluxio/security/authorization/Mode.java`.

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Alluxio caches data from underlying file systems across multiple storage backends (S3, HDFS, GCS, OSS, COS, etc.) configured via mount points. Data cached on worker nodes may reside in a different region than the original data. Since `has_persistent_data_store=true` and `has_logging_of_user_data=true`, no INFO downgrade applies. Archetype is `stateful-crud`, so no archetype downgrade applies.
- **Gap**: No application-level data residency controls. Cached data may cross compliance boundaries.
- **Recommendation**: Implement region-aware mount point policies. Document which mount points contain region-restricted data.
- **Evidence**: `underfs/s3a/`, `underfs/hdfs/`, `underfs/gcs/`, `integration/kubernetes/helm-chart/alluxio/values.yaml`, `core/common/src/main/java/alluxio/conf/PropertyKey.java`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK-QUALITY
- **Finding**: S3 API implements `ListObjects` with `MaxKeys`, `Marker`/`ContinuationToken` pagination, `Prefix` filtering, and `IsTruncated`. gRPC `ListStatusPartial` provides `batchSize`, `startAfter`/`offsetId`/`offsetCount` pagination. Paths REST `list-status` has no pagination.
- **Gap**: Paths REST `list-status` returns unbounded results. S3 API and gRPC have proper pagination.
- **Recommendation**: Use S3 API or gRPC `ListStatusPartial` for agent integration. Add pagination to Paths REST.
- **Evidence**: `core/server/proxy/src/main/java/alluxio/proxy/s3/ListBucketOptions.java`, `core/server/proxy/src/main/java/alluxio/proxy/s3/ListBucketResult.java`, `core/transport/src/main/proto/grpc/file_system_master.proto`

#### DATA-Q4: System of Record Designations
- **Severity**: RISK-QUALITY
- **Finding**: Alluxio is a caching layer, not a system of record. Authoritative data resides in UFS (S3, HDFS, GCS). `ActiveSyncManager` syncs metadata with UFS. `persisted` field in `FileInfo` indicates UFS write-through status. No formal system-of-record designation or documentation.
- **Gap**: No formal system-of-record designation. Agents may not know data could be stale.
- **Recommendation**: Document the data authority model: UFS is system of record, Alluxio is cache.
- **Evidence**: `core/server/master/src/main/java/alluxio/master/file/activesync/ActiveSyncManager.java`, `core/transport/src/main/proto/grpc/file_system_master.proto`

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK-QUALITY
- **Finding**: `FileInfo` includes `creationTimeMs`, `lastModificationTimeMs`, `lastAccessTimeMs` (UTC epoch millis). Timestamps are consistent. No freshness signaling — no `Cache-Control`, `X-Data-Age`, or `last_refreshed` headers. `ActiveSyncManager` syncs from HDFS periodically but sync interval not communicated to clients.
- **Gap**: Timestamps exist but no freshness signaling. Agents cannot determine if metadata reflects current UFS state.
- **Recommendation**: Add freshness headers (`X-Data-Age`, `X-Cache-Status`) to API responses.
- **Evidence**: `core/transport/src/main/proto/grpc/file_system_master.proto`, `core/server/master/src/main/java/alluxio/master/file/meta/MutableInode.java`

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: Audit logs capture user identity, IP, file paths verbatim. No PII redaction in any logging component. File paths may contain PII.
- **Gap**: No PII masking or log scrubbing.
- **Recommendation**: Implement PII-aware log filtering.
- **Evidence**: `core/server/proxy/src/main/java/alluxio/proxy/s3/S3AuditContext.java`, `conf/log4j.properties`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality scores, completeness metrics, or data profiling reports found. `MetricsStore` tracks operational metrics (bytes read/written, cache hit rates) but not data quality. Alluxio caches data without assessing quality.
- **Gap**: No data quality signaling for agents.
- **Recommendation**: Integrate with external data quality framework at UFS level. Expose quality metadata via xattr.
- **Evidence**: `core/server/master/src/main/java/alluxio/master/metrics/MetricsStore.java`, `core/common/src/main/java/alluxio/metrics/MetricKey.java`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: `proto-backwards-compatibility` plugin detects breaking gRPC changes. REST API has no versioning or breaking change detection.
- **Gap**: REST API lacks versioning and breaking change detection.
- **Recommendation**: Add OpenAPI diff to CI; version REST API paths.
- **Evidence**: `core/transport/pom.xml`, `pom.xml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Proto fields are human-readable (`creationTimeMs`, `lastModificationTimeMs`, `owner`, `group`, `path`). S3 API follows AWS naming conventions.
- **Gap**: No gap.
- **Recommendation**: Maintain naming conventions.
- **Evidence**: `core/transport/src/main/proto/grpc/file_system_master.proto`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No external data catalog. Master metastore stores FS metadata. `table` module provides limited table metadata.
- **Gap**: No discoverable data catalog for agent use.
- **Recommendation**: Implement metadata tagging via xattr for agent data discovery.
- **Evidence**: `core/server/master/src/main/java/alluxio/master/metastore/`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: OTEL agent/collector configs exist as sidecars. Logs are plain text (not JSON). No correlation IDs in logs. Dropwizard Metrics + Prometheus client libraries for metrics.
- **Gap**: No structured logging. No trace ID in log entries. OTEL is sidecar-only, not application-integrated.
- **Recommendation**: Switch to JSON logging. Add trace/correlation IDs. Integrate OTEL SDK.
- **Evidence**: `integration/metrics/otel-agent-config.yaml`, `conf/log4j.properties`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: All metrics sinks disabled by default. No alerting rules defined. Prometheus integration configured but not enabled.
- **Gap**: No alerting configuration in repository.
- **Recommendation**: Enable Prometheus metrics. Define alerting rules for error rates and latency.
- **Evidence**: `integration/kubernetes/helm-chart/alluxio/values.yaml` (metrics section)

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: Extensive operational metrics via Dropwizard Metrics and Prometheus. `MetricKey` defines `CLUSTER_BYTES_READ_CACHE`, `CLUSTER_CACHE_HIT_RATE`, `CLUSTER_CAPACITY_TOTAL/USED/FREE`, `CLUSTER_BYTES_READ_UFS`, etc. These are infrastructure metrics, not business outcome metrics.
- **Gap**: No business outcome metrics. No agent interaction outcome metrics.
- **Recommendation**: Define and publish business outcome metrics for agent use cases (e.g., agent query success rate, cache efficiency per agent).
- **Evidence**: `core/common/src/main/java/alluxio/metrics/MetricKey.java`, `core/server/master/src/main/java/alluxio/master/metrics/MetricsStore.java`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK-QUALITY
- **Finding**: Helm charts and K8s operator define deployment. No Terraform/CloudFormation/CDK. No drift detection. No automated Helm validation in CI.
- **Gap**: No cloud-native IaC. No drift detection. No automated plan review.
- **Recommendation**: Add cloud-native IaC. Add Helm validation to CI.
- **Evidence**: `integration/kubernetes/helm-chart/alluxio/`, `integration/kubernetes/operator/`, `.github/workflows/`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: GitHub Actions CI with unit/integration tests. `proto-backwards-compatibility` for gRPC. No contract testing for REST API.
- **Gap**: No consumer-driven contract tests. No REST API breaking change detection in CI.
- **Recommendation**: Add OpenAPI validation and contract testing to CI.
- **Evidence**: `.github/workflows/java8_unit_tests.yml`, `core/transport/pom.xml`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: Helm charts support `helm rollback` for Kubernetes deployments. StatefulSet (master) and DaemonSet/Deployment (worker) support Kubernetes-native rollback. No blue/green or canary deployment configuration found in the repository. No feature flag framework. The Helm chart's logserver uses `strategy: Recreate`.
- **Gap**: Rollback relies on Kubernetes/Helm-native mechanisms (adequate but basic). No canary deployments, no automated rollback triggers, no feature flags for gradual rollout.
- **Recommendation**: Add canary deployment configuration for the proxy component (the agent-facing surface). Configure automated rollback triggers based on error rate thresholds.
- **Evidence**: `integration/kubernetes/helm-chart/alluxio/values.yaml` (StatefulSet, DaemonSet configurations)

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: 766 test files. 257 integration tests. CI runs unit and integration tests. No dedicated API contract test suite.
- **Gap**: No dedicated API endpoint tests for agent-facing surface.
- **Recommendation**: Create API test suite with REST Assured or Postman/Newman.
- **Evidence**: `tests/`, `.github/workflows/`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: RISK-QUALITY
- **Finding**: S3 UFS backend supports server-side encryption via `UNDERFS_S3_SERVER_SIDE_ENCRYPTION_ENABLED`. Data cached on Alluxio workers (local disk, SSD, MEM) is not encrypted by Alluxio. Master metastore (RocksDB) has no application-level encryption. Helm chart does not configure encrypted volumes.
- **Gap**: Cached data on workers is unencrypted at rest. Encryption delegated to UFS but cached copies unprotected.
- **Recommendation**: Use encrypted volumes for worker data directories. Enable `UNDERFS_S3_SERVER_SIDE_ENCRYPTION_ENABLED=true`.
- **Evidence**: `core/common/src/main/java/alluxio/conf/PropertyKey.java` (UNDERFS_S3_SERVER_SIDE_ENCRYPTION_ENABLED), `integration/kubernetes/helm-chart/alluxio/values.yaml`

## Evidence Index

### Infrastructure as Code
| File | Questions Referenced |
|------|---------------------|
| `integration/kubernetes/helm-chart/alluxio/values.yaml` | AUTH-Q5, STATE-Q5, OBS-Q2, ENG-Q1, ENG-Q3, DATA-Q2 |
| `integration/kubernetes/helm-chart/alluxio/Chart.yaml` | ENG-Q1 |
| `integration/kubernetes/operator/` | ENG-Q1 |
| `integration/docker/Dockerfile` | ENG-Q1, HITL-Q3 |
| `integration/docker/Dockerfile-dev` | HITL-Q3 |
| `integration/metrics/otel-agent-config.yaml` | OBS-Q1 |
| `integration/metrics/otel-collector-config.yaml` | OBS-Q1 |
| `integration/metrics/docker-compose-master.yaml` | HITL-Q3 |
| `integration/metrics/docker-compose-worker.yaml` | HITL-Q3 |
| `integration/metrics/prometheus.yaml` | OBS-Q2 |

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `core/server/proxy/src/main/java/alluxio/proxy/PathsRestServiceHandler.java` | API-Q1, API-Q2, API-Q3, STATE-Q2, DATA-Q3 |
| `core/server/proxy/src/main/java/alluxio/proxy/StreamsRestServiceHandler.java` | API-Q1 |
| `core/server/proxy/src/main/java/alluxio/proxy/s3/S3RestServiceHandler.java` | API-Q1 |
| `core/server/proxy/src/main/java/alluxio/proxy/s3/S3ErrorCode.java` | API-Q3 |
| `core/server/proxy/src/main/java/alluxio/proxy/s3/S3ErrorResponse.java` | API-Q3 |
| `core/server/proxy/src/main/java/alluxio/proxy/s3/S3Handler.java` | API-Q5, API-Q8, AUTH-Q6 |
| `core/server/proxy/src/main/java/alluxio/proxy/s3/S3AuditContext.java` | AUTH-Q6, DATA-Q6 |
| `core/server/proxy/src/main/java/alluxio/proxy/s3/S3AuthenticationFilter.java` | AUTH-Q1, AUTH-Q7 |
| `core/server/proxy/src/main/java/alluxio/proxy/s3/RateLimitInputStream.java` | STATE-Q5 |
| `core/server/proxy/src/main/java/alluxio/proxy/s3/auth/Authenticator.java` | AUTH-Q1 |
| `core/server/proxy/src/main/java/alluxio/proxy/s3/auth/PassAllAuthenticator.java` | AUTH-Q1 |
| `core/server/proxy/src/main/java/alluxio/proxy/s3/signature/AwsSignatureProcessor.java` | AUTH-Q1 |
| `core/server/proxy/src/main/java/alluxio/proxy/s3/signature/AuthorizationV4Validator.java` | AUTH-Q1 |
| `core/common/src/main/java/alluxio/security/authentication/DefaultAuthenticationServer.java` | AUTH-Q1, AUTH-Q7 |
| `core/common/src/main/java/alluxio/security/authentication/AuthenticatedClientUser.java` | AUTH-Q4 |
| `core/common/src/main/java/alluxio/security/authentication/ClientContextServerInjector.java` | AUTH-Q4 |
| `core/common/src/main/java/alluxio/security/authentication/ImpersonationAuthenticator.java` | AUTH-Q4, AUTH-Q7 |
| `core/common/src/main/java/alluxio/security/authorization/AccessControlList.java` | AUTH-Q2, DATA-Q1 |
| `core/common/src/main/java/alluxio/security/authorization/AclEntry.java` | AUTH-Q2 |
| `core/common/src/main/java/alluxio/security/authorization/AclAction.java` | AUTH-Q3 |
| `core/common/src/main/java/alluxio/security/authorization/Mode.java` | AUTH-Q2 |
| `core/common/src/main/java/alluxio/retry/ExponentialBackoffRetry.java` | STATE-Q4 |
| `core/server/master/src/main/java/alluxio/master/journal/DefaultJournalMaster.java` | STATE-Q1 |
| `core/server/master/src/main/java/alluxio/master/metastore/rocks/RocksInodeStore.java` | STATE-Q3 |
| `core/server/master/src/main/java/alluxio/master/throttle/DefaultThrottleMaster.java` | STATE-Q5, STATE-Q6, API-Q8, STATE-Q4 |
| `core/server/common/src/main/java/alluxio/master/journal/sink/JournalSink.java` | API-Q7 |
| `core/server/master/src/main/java/alluxio/master/file/activesync/ActiveSyncManager.java` | API-Q7, STATE-Q4, DATA-Q4, DATA-Q5 |
| `core/server/master/src/main/java/alluxio/master/file/meta/MutableInode.java` | DATA-Q5 |
| `core/server/master/src/main/java/alluxio/master/file/meta/MountTable.java` | DATA-Q4 |
| `core/server/master/src/main/java/alluxio/master/metrics/MetricsStore.java` | DATA-Q7, OBS-Q3 |
| `core/server/proxy/src/main/java/alluxio/proxy/s3/ListBucketOptions.java` | DATA-Q3 |
| `core/server/proxy/src/main/java/alluxio/proxy/s3/ListBucketResult.java` | DATA-Q3 |
| `core/server/proxy/src/main/java/alluxio/proxy/s3/S3BucketTask.java` | STATE-Q2 |
| `core/common/src/main/java/alluxio/retry/RetryUtils.java` | STATE-Q4 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `core/transport/src/main/proto/grpc/file_system_master.proto` | API-Q1, API-Q2, API-Q4, API-Q5, AUTH-Q3, STATE-Q1, STATE-Q2, DATA-Q1, DATA-Q3, DATA-Q4, DATA-Q5, DISC-Q1, DISC-Q2, HITL-Q1 |
| `core/transport/src/main/proto/grpc/block_master.proto` | API-Q1 |
| `core/transport/src/main/proto/grpc/block_worker.proto` | API-Q1 |
| `core/transport/src/main/proto/grpc/meta_master.proto` | API-Q1 |
| `core/transport/src/main/proto/grpc/sasl_server.proto` | AUTH-Q1 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/java8_unit_tests.yml` | ENG-Q2, ENG-Q4 |
| `.github/workflows/java8_integration_tests.yml` | ENG-Q2, ENG-Q4 |
| `.github/workflows/java8_integration_tests_ft.yml` | ENG-Q2 |
| `.github/workflows/checkstyle.yml` | ENG-Q2 |
| `.github/workflows/fuse_integration_tests.yml` | ENG-Q2 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `integration/docker/Dockerfile` | ENG-Q1, HITL-Q3 |
| `integration/docker/Dockerfile-dev` | HITL-Q3 |
| `dev/jenkins/Dockerfile-jdk8` | ENG-Q2 |
| `integration/kubernetes/operator/alluxio/Dockerfile` | ENG-Q1 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `pom.xml` (root) | API-Q2, DISC-Q1, ENG-Q2 |
| `core/transport/pom.xml` | DISC-Q1, ENG-Q2 |
| `webui/package.json` | Discovery inventory |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `conf/log4j.properties` | AUTH-Q6, DATA-Q6, OBS-Q1 |
| `conf/alluxio-site.properties.template` | AUTH-Q1, AUTH-Q5, DATA-Q1 |
| `conf/metrics.properties.template` | OBS-Q2 |
| `core/common/src/main/java/alluxio/metrics/MetricKey.java` | DATA-Q7, OBS-Q3 |
| `core/common/src/main/java/alluxio/conf/PropertyKey.java` | DATA-Q2, ENG-Q5 |
