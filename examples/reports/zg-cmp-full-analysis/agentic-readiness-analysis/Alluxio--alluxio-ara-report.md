# Agentic Readiness Analysis Report

**Target**: Alluxio (alluxio/alluxio)
**Date**: 2026-04-29
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**Repository Type**: monorepo
**Service Archetype**: orchestrator (auto-detected) — primary agent-facing surface is the Proxy (S3/REST API gateway)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: java, storage, distributed
**Context**: Data orchestration / virtual distributed file system. JVM, distributed storage caching layer.

**Archetype Justification**: The Alluxio Proxy is classified as an orchestrator because it serves as an S3/REST API gateway that proxies all file system requests to the Alluxio Master and Worker services (calls 2+ downstream services), with minimal persistent state of its own. The overall monorepo contains stateful-crud components (Master, Worker) and a data-gateway (FUSE), but the primary agent-facing surface is the Proxy.

**Component Archetypes**:
| Component | Archetype | Justification |
|-----------|-----------|---------------|
| Alluxio Proxy | orchestrator | S3/REST API gateway, proxies to Master/Worker |
| Alluxio Master | stateful-crud | Metadata management, RocksDB metastore, journal |
| Alluxio Worker | stateful-crud | Block storage cache, persistent local state |
| Job Master/Worker | orchestrator | Distributed job orchestration (load, migrate) |
| FUSE | data-gateway | POSIX mount interface, read-heavy data access |

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 2 | **RISK-SAFETY**: 9 | **RISK-QUALITY**: 13 | **INFOs**: 15

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days. The two BLOCKERs (AUTH-Q1: Machine Identity, DATA-Q1: Sensitive Data Classification) must be remediated before agents can safely interact with the Alluxio S3/REST API surface. Once BLOCKERs are resolved, the 9 RISK-SAFETY findings would place this system in "Pilot-Ready (Safety Concerns)" status.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 2 |
| RISK-SAFETY | 9 |
| RISK-QUALITY | 13 |
| INFO | 15 |
| N/A | 0 |
| Not Evaluated (extended) | 4 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 15
**Extended Questions Not Triggered**: 4
**Questions N/A (repo_type: monorepo)**: 0
**Service Archetype**: orchestrator (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: Alluxio supports multiple authentication types via the `AuthType` enum (`NOSASL`, `SIMPLE`, `CUSTOM`, `KERBEROS`) defined in `core/common/src/main/java/alluxio/security/authentication/AuthType.java`. The S3 API proxy uses `S3AuthenticationFilter.java` which extracts the user from the `Authorization` header and maps it to an internal user name. However, the default authentication mode is `SIMPLE`, which trusts the client-provided username without verification. There is no OAuth2 client credentials flow, API key with principal attribution, or mTLS configuration for the REST/S3 API surface. The `CUSTOM` auth type allows a pluggable `AuthenticationProvider`, but no default machine identity provider is included. The S3 authentication parses AWS Signature V4 headers but maps them to an Alluxio username — there is no distinct machine identity concept that differentiates agent callers from human callers in audit logs.
- **Gap**: No machine identity authentication mechanism that can distinguish which agent made a call. The S3 auth signature maps to a username but does not provide principal attribution sufficient for agent forensics. Default `SIMPLE` auth trusts the client without verification.
- **Remediation**:
  - **Immediate**: Configure `CUSTOM` authentication with a provider that validates agent credentials (e.g., API key validation against an external identity store). Configure `alluxio.security.authentication.type=CUSTOM` and implement a `CustomAuthenticationProvider` that validates agent-specific credentials.
  - **Target State**: Each agent identity has a unique, verifiable credential (API key or service account) that is recorded in audit logs with full principal attribution. The system can distinguish agent-initiated vs. human-initiated requests.
  - **Estimated Effort**: Medium (30–60 days)
  - **Dependencies**: AUTH-Q6 (audit logging must capture the authenticated principal)
- **Evidence**: `core/common/src/main/java/alluxio/security/authentication/AuthType.java`, `core/server/proxy/src/main/java/alluxio/proxy/s3/S3AuthenticationFilter.java`, `core/server/proxy/src/main/java/alluxio/proxy/s3/S3AuditContext.java`

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: Alluxio functions as a distributed caching layer that sits between compute and underlying storage (S3, HDFS, etc.). It caches and serves data from underlying file systems but has no data classification system at the field level. The S3 proxy API exposes all data that the authenticated user has POSIX permission to access — there is no mechanism to tag, classify, or restrict access to specific data fields based on sensitivity (PII, PHI, financial records). The Helm chart `values.yaml` and IaC definitions contain no data classification tags. There is no integration with Amazon Macie or equivalent data classification tooling. Data cached by Alluxio inherits no sensitivity metadata from the underlying storage system.
- **Gap**: No field-level or object-level sensitive data classification. No controls to prevent an agent from retrieving sensitive data (PII, PHI, financial records) without explicit authorization beyond POSIX file permissions. Alluxio caches data transparently — any data accessible to the agent's POSIX identity is returned without classification-based filtering.
- **Remediation**:
  - **Immediate**: Implement data classification at the Alluxio mount point level — classify entire mount paths by sensitivity tier (e.g., `/sensitive/`, `/public/`). Use Alluxio's ACL system to restrict agent identities to non-sensitive mount paths only.
  - **Target State**: Data sensitivity metadata propagated from underlying storage (e.g., S3 object tags) is enforced by Alluxio proxy before returning data to agents. Field-level or path-level classification controls prevent agents from accessing sensitive data without explicit authorization.
  - **Estimated Effort**: High (90–180 days)
  - **Dependencies**: AUTH-Q1 (machine identity must be established before data access controls can be enforced per-agent)
- **Evidence**: `core/server/proxy/src/main/java/alluxio/proxy/s3/S3RestServiceHandler.java`, `integration/kubernetes/helm-chart/alluxio/values.yaml`, `core/common/src/main/java/alluxio/security/authorization/AccessControlList.java`

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Alluxio implements a POSIX-style permission model with owner/group/other bits (read/write/execute) via `Mode.java` and ACL support via `AccessControlList.java`, `AclEntry.java`, and `AclAction.java`. The `DefaultPermissionChecker.java` enforces these permissions at the file system level. However, permissions are coarse-grained — they operate at the file/directory path level with POSIX semantics, not at the API operation level. There is no concept of scoped API permissions (e.g., "agent X can read `/data/public/*` but not `/data/sensitive/*`" at the API layer). The S3 proxy maps all requests to the user's POSIX identity, inheriting all paths accessible to that user.
- **Gap**: No fine-grained, API-level scoping of agent permissions. An agent identity inherits all POSIX permissions of its mapped user — there is no mechanism to grant an agent read-only access to specific resources without inheriting broader file system privileges.
- **Compensating Controls**:
  - Create dedicated OS users for each agent with minimal POSIX permissions scoped to specific mount paths
  - Use Alluxio's ACL system to create restrictive access control entries per agent user
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a dedicated Alluxio user per agent identity with POSIX permissions restricted to only the mount paths the agent needs. Use Alluxio's extended ACL entries to further limit access.
- **Evidence**: `core/common/src/main/java/alluxio/security/authorization/Mode.java`, `core/common/src/main/java/alluxio/security/authorization/AccessControlList.java`, `core/server/master/src/main/java/alluxio/master/file/DefaultPermissionChecker.java`

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Alluxio's POSIX permission model supports read/write/execute granularity via `Mode.Bits` and `AclAction` (READ, WRITE, EXECUTE). The `DefaultPermissionChecker` checks these bits before allowing file system operations. The S3 proxy maps S3 operations to file system calls with the user's POSIX identity. For example, GET maps to read permission, PUT maps to write permission, and DELETE maps to write permission. This provides action-level authorization at the file system layer.
- **Gap**: While read/write/execute granularity exists at the POSIX level, there is no ability to grant "read but not delete" on the same resource via the S3 API — both DELETE and PUT require write permission. Fine-grained ABAC policies (e.g., "can read records but not delete them") are not supported.
- **Compensating Controls**:
  - Configure the agent user with read-only POSIX permissions (no write bit) on all paths to prevent delete operations
  - Use an API gateway or reverse proxy in front of Alluxio S3 proxy to filter HTTP methods (block DELETE, PUT for agent identities)
- **Remediation Timeline**: 30–60 days
- **Recommendation**: For read-only agent scope, set agent user permissions to read+execute only (no write) on all Alluxio paths. This effectively prevents all write/delete operations at the file system layer.
- **Evidence**: `core/common/src/main/java/alluxio/security/authorization/AclAction.java`, `core/common/src/main/java/alluxio/security/authorization/Mode.java`, `core/server/master/src/main/java/alluxio/master/file/DefaultPermissionChecker.java`

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Alluxio has a comprehensive audit logging system. The `log4j.properties` configures separate audit log appenders: `MASTER_AUDIT_LOGGER` (writes to `master_audit.log`), `JOB_MASTER_AUDIT_LOGGER` (writes to `job_master_audit.log`), and `PROXY_AUDIT_LOGGER` (writes to `proxy_audit.log`). The `S3AuditContext.java` logs authenticated user (UGI), IP address, command, bucket, object, success/failure, and execution time for every S3 API operation. The `AsyncUserAccessAuditLogWriter` handles asynchronous audit log writing. However, audit logs are written to local rolling files (`RollingFileAppender`) with no immutability or tamper-evidence controls. There is no CloudTrail integration, no S3 bucket with object lock, and no log file validation mechanism.
- **Gap**: Audit logs are not immutable. They are stored as local rolling files that can be modified or deleted by anyone with filesystem access. No tamper-evidence mechanism (checksums, append-only storage, object lock).
- **Compensating Controls**:
  - Ship audit logs to an external immutable log store (e.g., CloudWatch Logs with retention lock, S3 with Object Lock) via the remote log appender configuration already present in log4j.properties
  - Use the Alluxio LogServer (already configured with REMOTE_*_LOGGER appenders) to centralize logs on a hardened, append-only log server
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure the Alluxio LogServer as a centralized audit log collector and ship logs to an immutable store (e.g., S3 with Object Lock enabled). Enable the remote log appenders already defined in `log4j.properties`.
- **Evidence**: `conf/log4j.properties`, `core/server/proxy/src/main/java/alluxio/proxy/s3/S3AuditContext.java`, `core/server/common/src/main/java/alluxio/master/audit/AsyncUserAccessAuditLogWriter.java` (referenced)

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Alluxio has no mechanism to suspend or revoke individual agent identities without restarting the service or modifying OS-level user accounts. The authentication model maps S3 Authorization headers to OS usernames. There is no API key revocation endpoint, no IAM role deactivation, no user disable feature in the Alluxio security framework. To disable an agent, the administrator would need to change the underlying OS user or modify POSIX permissions on the file system — neither of which provides immediate, granular suspension.
- **Gap**: No mechanism to immediately suspend a specific agent identity without affecting other users. No API key revocation, no user disable API, no runtime identity management.
- **Compensating Controls**:
  - Place an API gateway in front of the Alluxio proxy with API key management that supports instant revocation
  - Use network-level controls (security groups, firewall rules) to block a misbehaving agent's IP address
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement an API gateway (e.g., AWS API Gateway, Kong) in front of the Alluxio S3 proxy that provides API key management with instant revocation capabilities.
- **Evidence**: `core/common/src/main/java/alluxio/security/authentication/AuthType.java`, `core/server/proxy/src/main/java/alluxio/proxy/s3/S3AuthenticationFilter.java`

#### STATE-Q1: Compensation and Rollback ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Alluxio Master uses a journal system (Raft-based via `RaftJournalSystem` or UFS-based via `UfsJournalSystem`) for metadata persistence and crash recovery. The journal supports replaying operations for recovery but does not expose explicit compensation or rollback endpoints for multi-step API operations. The S3 proxy has no saga pattern or explicit undo endpoints. Multi-part upload operations have an abort mechanism (`abortMultipartUpload`), which provides partial compensation for upload workflows. However, there is no general-purpose rollback capability for arbitrary multi-step file system operations.
- **Gap**: No general-purpose compensation or rollback for multi-step operations. The journal provides crash recovery but not application-level undo. Only multipart upload has an abort/cleanup mechanism.
- **Compensating Controls**:
  - For read-only agent scope, compensation risk is minimal since no write operations are performed
  - The multipart upload abort mechanism covers the primary write workflow in the S3 API
- **Remediation Timeline**: 90–180 days (for general compensation support)
- **Recommendation**: For read-only agents, this is low priority. If write scope is needed in the future, implement explicit undo/compensation endpoints for critical write operations (create bucket, delete object).
- **Evidence**: `core/server/common/src/main/java/alluxio/master/journal/raft/RaftJournalSystem.java` (referenced), `core/server/proxy/src/main/java/alluxio/proxy/s3/S3RestServiceHandler.java` (abortMultipartUpload method)

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Alluxio implements retry logic via the `alluxio.retry` package (`ExponentialBackoffRetry`, `CountingRetry`, `TimeoutRetry`, `RetryPolicy`). The `AbstractClient.java` uses `RetryPolicy` for gRPC RPC calls with configurable retry behavior. Timeout configurations exist for gRPC clients. However, there are no circuit breaker implementations (no Resilience4j, no Hystrix, no `@CircuitBreaker` annotations). The search for "CircuitBreaker" found only references to "short-circuit" read/write (a data locality optimization, not a resilience pattern). If the Master becomes overloaded, the Proxy will continue retrying without breaking the circuit.
- **Gap**: No circuit breaker pattern implemented. Retry logic exists but without circuit breakers, a degraded Master or Worker service can cause cascading failures through the Proxy to all agent callers.
- **Compensating Controls**:
  - Configure aggressive timeout values on Proxy-to-Master and Proxy-to-Worker gRPC connections to limit blast radius
  - Deploy an API gateway or service mesh (Istio) in front of the Proxy with circuit breaker policies
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add circuit breaker logic to the `AbstractClient` RPC retry path or deploy an Istio/Envoy sidecar with circuit breaker configuration for the Proxy service.
- **Evidence**: `core/common/src/main/java/alluxio/retry/ExponentialBackoffRetry.java`, `core/common/src/main/java/alluxio/retry/RetryPolicy.java`, `core/common/src/main/java/alluxio/AbstractClient.java`

#### DATA-Q2: Data Residency and Sovereignty ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Alluxio caches data from underlying storage systems (S3, HDFS, GCS, Azure, etc.) and serves it through its API. The data residency characteristics are inherited from the underlying file system (UFS) configuration. Alluxio's `PropertyKey.java` defines properties for S3 regions, HDFS namenode addresses, and other UFS connection parameters. However, Alluxio itself has no data residency enforcement — it will cache data from any configured UFS regardless of region. Data cached locally on Alluxio Workers may reside in a different region than the underlying storage. There are no controls to prevent an agent from reading data that may be subject to GDPR, LGPD, or HIPAA residency requirements.
- **Gap**: No data residency enforcement within Alluxio. Data cached on Workers may reside in different regions than the source. No controls to restrict agent access based on data sovereignty requirements.
- **Compensating Controls**:
  - Configure Alluxio Workers to only cache data from same-region UFS mounts
  - Use Alluxio's tiered locality (rack-aware, region-aware) to ensure cached data stays within compliance boundaries
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Document data residency requirements for each UFS mount. Configure Alluxio tiered locality to ensure Worker caches respect regional boundaries. Consider separate Alluxio clusters per compliance zone.
- **Evidence**: `core/common/src/main/java/alluxio/conf/PropertyKey.java` (UFS region properties), `integration/kubernetes/helm-chart/alluxio/values.yaml`

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Alluxio has Swagger annotations (`@Api`, `@ApiOperation`) in `PathsRestServiceHandler.java` and a `swagger-maven-plugin` configured in `pom.xml` for generating specs at build time. Protobuf definitions in `core/transport/src/main/proto/grpc/` serve as machine-readable specs for the gRPC interface. The S3 API (`S3RestServiceHandler.java`) follows the AWS S3 API specification, which is publicly documented. However, no standalone OpenAPI/Swagger spec file (`openapi.yaml`, `swagger.json`) was found in the repository. The generated spec would be available as a build artifact but is not committed to the repository.
- **Gap**: No committed OpenAPI/Swagger specification file. The Swagger annotations and maven plugin can generate one at build time, but it is not available as a static artifact in the repository. The S3 API follows the AWS S3 spec but an Alluxio-specific spec documenting supported/unsupported operations is absent.
- **Compensating Controls**:
  - Use the existing `swagger-maven-plugin` to generate and commit the OpenAPI spec as a build artifact
  - Document Alluxio-specific S3 API deviations (unsupported operations) in a machine-readable format
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Run the swagger-maven-plugin during CI and commit the generated OpenAPI spec to the repository. Create an Alluxio-specific S3 API compatibility matrix documenting supported operations.
- **Evidence**: `pom.xml` (swagger-maven-plugin), `core/server/proxy/src/main/java/alluxio/proxy/PathsRestServiceHandler.java` (@Api, @ApiOperation annotations), `core/transport/src/main/proto/grpc/file_system_master.proto`

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The S3 API has well-structured error responses. `S3ErrorCode.java` defines 20+ error codes with HTTP status mapping (e.g., `BAD_DIGEST` → 400, `NO_SUCH_BUCKET` → 404, `INTERNAL_ERROR` → 500). `S3ErrorResponse.java` generates XML error responses following the AWS S3 error format. However, the REST Paths API (`PathsRestServiceHandler.java`) uses generic `RestUtils.call()` which returns less structured error responses. The gRPC interface uses standard gRPC status codes. No explicit "retryable" boolean or error category field is returned — agents must infer retryability from HTTP status codes.
- **Gap**: S3 API has structured errors following AWS conventions, but no explicit retryability indicator. The Alluxio REST API (non-S3) has less structured error responses. No consistent error taxonomy across all API surfaces (S3, REST, gRPC).
- **Compensating Controls**:
  - For S3 API consumers, standard AWS S3 SDK error handling logic applies (well-understood retryability rules)
  - Document which Alluxio-specific error codes are retriable
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a `Retryable` field to S3 error responses. Standardize error response format across the REST Paths API to match S3 API structure.
- **Evidence**: `core/server/proxy/src/main/java/alluxio/proxy/s3/S3ErrorCode.java`, `core/server/proxy/src/main/java/alluxio/proxy/s3/S3ErrorResponse.java` (referenced)

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Alluxio implements rate limiting at the S3 proxy layer. `S3RestServiceHandler.java` uses a `RateLimiter` (Guava) as `mGlobalRateLimiter` for global request rate limiting. `RateLimitInputStream.java` provides per-connection read rate limiting configured via `PropertyKey.PROXY_S3_SINGLE_CONNECTION_READ_RATE_LIMIT_MB`. The rate limiter is configured as a servlet context attribute via `ProxyWebServer.GLOBAL_RATE_LIMITER_SERVLET_RESOURCE_KEY`. However, rate limiting is only implemented at the S3 proxy layer — there is no rate limiting on the gRPC API used for direct client connections, and no per-identity rate limiting (all identities share the same global rate limiter).
- **Gap**: Rate limiting exists but is global (not per-identity) and only applies to the S3 proxy API. The gRPC interface has no rate limiting. An agent sharing the rate limit pool with all other clients could be starved, or a misbehaving agent could consume the entire rate limit budget.
- **Compensating Controls**:
  - Deploy an API gateway in front of the S3 proxy with per-API-key rate limiting
  - Configure the global rate limiter conservatively to limit total throughput
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement per-identity rate limiting in the S3 proxy (extend the existing `RateLimiter` to maintain per-user buckets). Add rate limiting to the gRPC interface.
- **Evidence**: `core/server/proxy/src/main/java/alluxio/proxy/s3/S3RestServiceHandler.java` (mGlobalRateLimiter), `core/server/proxy/src/main/java/alluxio/proxy/s3/RateLimitInputStream.java`

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Alluxio has a `SensitiveConfigMask` interface for masking sensitive configuration information and an `RpcSensitiveConfigMask.CREDENTIAL_FIELD_MASKER` for masking credential fields in RPC messages. The audit logs (`S3AuditContext.toString()`) log user names, IP addresses, bucket names, and object names — which could contain PII if the data model includes PII in file/object paths. The `log4j.properties` has no PII scrubbing filters configured. Log4j appenders write raw log messages without any redaction middleware.
- **Gap**: Credential masking exists for RPC messages, but no PII redaction in audit logs or application logs. File paths, bucket names, and object names logged in audit entries could contain PII. No log scrubbing middleware or PII detection integration (e.g., Macie).
- **Compensating Controls**:
  - Ensure file/object naming conventions do not include PII
  - Restrict audit log access to authorized security personnel only
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a log4j filter or custom appender that redacts PII patterns (email, SSN, phone numbers) from audit log entries. Integrate with a log scrubbing library.
- **Evidence**: `core/common/src/main/java/alluxio/conf/SensitiveConfigMask.java`, `core/server/proxy/src/main/java/alluxio/proxy/s3/S3AuditContext.java` (toString method logs UGI, IP, bucket, object), `conf/log4j.properties`

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Alluxio uses `proto.lock` (290KB, 11,685 lines) in `core/transport/src/main/proto/` for protobuf schema backward compatibility checking. The `proto-backwards-compatibility` Maven dependency (version 1.0.7) is configured in `pom.xml` for breaking change detection. The gRPC proto files are versioned with the protobuf package. The S3 API follows the AWS S3 versioning (API version 2006-03-01). The REST Paths API uses URL path versioning (`/api/v1/`). However, there is no consumer-driven contract testing (no Pact) and no automated breaking change detection in the CI pipeline for the REST/S3 APIs.
- **Gap**: Protobuf schema versioning is strong (proto.lock + backwards compatibility checker). REST/S3 API versioning relies on the AWS S3 standard but has no automated breaking change detection in CI.
- **Compensating Controls**:
  - The S3 API follows the stable AWS S3 specification, minimizing unexpected changes
  - Proto.lock provides backward compatibility checks for the gRPC interface
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenAPI diff checking to CI for the REST API. The proto.lock mechanism should be validated in CI builds (verify the proto-backwards-compatibility plugin runs in CI).
- **Evidence**: `core/transport/src/main/proto/proto.lock`, `pom.xml` (proto-backwards-compatibility dependency)

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Alluxio has OpenTelemetry (OTel) integration configured in `integration/metrics/` with `otel-agent-config.yaml`, `otel-collector-config.yaml`, and `prometheus.yaml`. The OTel collector exports traces to Jaeger and metrics to Prometheus. Docker Compose files (`docker-compose-master.yaml`, `docker-compose-worker.yaml`) configure the OTel agent. Log4j is configured with ISO8601 timestamps and structured pattern layouts (`%d{ISO8601} %-5p [%t](%F:%L) - %m%n`). However, logs are not JSON-structured — they use a human-readable pattern layout. No `correlation_id` or `request_id` field is propagated through log entries. The OTel integration is provided as an optional deployment configuration, not embedded in the application code.
- **Gap**: OTel tracing infrastructure exists but is optional (not embedded in code). Logs are not JSON-structured. No correlation ID linking log entries for a single request. Tracing configuration requires external agent attachment.
- **Compensating Controls**:
  - Deploy with the OTel Java agent attached (configured in docker-compose files)
  - Use the existing Prometheus metrics endpoint for operational visibility
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Switch log4j to JSON layout for machine-parseable logs. Add a correlation ID middleware to the S3 proxy that propagates a request ID through all log entries. Embed OTel SDK instrumentation in the application code for trace context propagation.
- **Evidence**: `integration/metrics/otel-collector-config.yaml`, `integration/metrics/otel-agent-config.yaml`, `conf/log4j.properties`

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Alluxio has a Prometheus metrics integration (`integration/metrics/prometheus.yaml`) and a Grafana monitoring stack (`integration/kubernetes/helm-chart/monitor/`). The `MetricKey.java` defines extensive metrics (2,845 lines) including Proxy-specific metrics (`Proxy.AuditLogEntriesSize`, `Proxy.CheckUploadIDStatusLatency`, `Proxy.CompleteMPUploadMergeLatency`). The `metrics.properties.template` documents multiple metric sinks (Console, CSV, JMX, Graphite, Prometheus, Slf4j). However, no alerting rules were found — no Prometheus alert rules, no CloudWatch alarms, no PagerDuty/OpsGenie integration. The monitoring infrastructure exists for visualization but not for proactive alerting.
- **Gap**: Metrics collection and visualization infrastructure exists, but no alerting rules are configured. No error rate or latency threshold alerts for the S3/REST API surface.
- **Compensating Controls**:
  - Configure Prometheus alerting rules for the existing metrics endpoints
  - Use the Grafana dashboards to manually monitor during pilot phase
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Create Prometheus alerting rules for S3 proxy error rates (5xx responses), latency P99, and availability. Integrate with an alerting channel (PagerDuty, OpsGenie, SNS).
- **Evidence**: `integration/metrics/prometheus.yaml`, `conf/metrics.properties.template`, `core/common/src/main/java/alluxio/metrics/MetricKey.java`, `integration/kubernetes/helm-chart/monitor/`

#### ENG-Q1: Infrastructure Governance — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Alluxio provides Helm charts (`integration/kubernetes/helm-chart/alluxio/`) with `Chart.yaml`, `values.yaml`, and templates for deploying Master, Worker, Proxy, and supporting services. A Kubernetes operator is provided (`integration/kubernetes/operator/`). Docker definitions exist for building the Alluxio container image. GitHub Actions workflows trigger on pull requests, enforcing peer review. However, there is no Terraform/CloudFormation/CDK for cloud infrastructure (API gateways, IAM roles, networking). No drift detection is configured. The Helm charts define the Kubernetes deployment but not the surrounding cloud infrastructure.
- **Gap**: Kubernetes deployment is defined as Helm IaC with PR-based review. However, no cloud infrastructure IaC exists (no Terraform/CFN for IAM, API Gateway, networking). No drift detection.
- **Compensating Controls**:
  - The Helm chart provides reproducible Kubernetes deployments with peer review via GitHub PRs
  - The Kubernetes operator provides automated deployment management
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Create IaC definitions (Terraform or CDK) for the cloud infrastructure surrounding Alluxio — IAM roles, security groups, API Gateway (if used), secrets management. Enable Kubernetes resource drift detection.
- **Evidence**: `integration/kubernetes/helm-chart/alluxio/Chart.yaml`, `integration/kubernetes/helm-chart/alluxio/values.yaml`, `integration/kubernetes/operator/`

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Alluxio has comprehensive CI via GitHub Actions: `checkstyle.yml` (checkstyle, findbugs, license check), `java8_unit_tests.yml` (unit tests), `java8_integration_tests.yml` (integration tests with multiple module matrices), `fuse_integration_tests.yml`. The `proto-backwards-compatibility` plugin checks protobuf schema changes. SpotBugs runs during compilation. However, there is no API contract testing (no Pact, no OpenAPI validation in CI). The CI does not validate that S3/REST API responses conform to a specification. Breaking changes to the REST/S3 API surface would not be automatically detected.
- **Gap**: No API contract testing for the S3/REST API. CI validates code quality (checkstyle, findbugs) and runs unit/integration tests, but does not validate API contracts or detect breaking API changes.
- **Compensating Controls**:
  - The S3 API follows the AWS S3 specification, reducing likelihood of unexpected changes
  - The `S3ClientRestApiTest.java` integration test exercises S3 API endpoints
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenAPI spec generation to CI and compare against baseline for breaking changes. Add consumer-driven contract tests for the S3 API endpoints.
- **Evidence**: `.github/workflows/java8_unit_tests.yml`, `.github/workflows/checkstyle.yml`, `.github/workflows/java8_integration_tests.yml`, `pom.xml` (proto-backwards-compatibility)

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Alluxio's Helm chart supports standard Helm rollback (`helm rollback`). The Kubernetes StatefulSet deployment model for Master and Worker supports rolling updates. However, there is no explicit blue/green or canary deployment configuration in the Helm chart. No CodeDeploy rollback triggers or feature flags were found. The `values.yaml` does not define deployment strategies beyond the Kubernetes default (`RollingUpdate`).
- **Gap**: Basic Helm rollback is available but no automated rollback triggers, no canary deployment, no feature flag system for gradual rollout.
- **Compensating Controls**:
  - Use Helm rollback for manual recovery
  - Kubernetes rolling update provides zero-downtime deployment
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add canary deployment configuration to the Helm chart. Implement health check-based automatic rollback in the Helm deployment. Consider feature flags for API changes.
- **Evidence**: `integration/kubernetes/helm-chart/alluxio/values.yaml`, `integration/kubernetes/helm-chart/alluxio/Chart.yaml`

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Alluxio has API test suites: `S3RestServiceHandlerTest.java` (proxy S3 unit tests), `S3ClientRestApiTest.java` (integration tests for S3 API), `S3RangeSpecTest.java`, `RateLimitInputStreamTest.java`, `AlluxioMasterRestServiceHandlerTest.java`, `AlluxioWorkerRestApiTest.java`. Integration tests exercise the full S3 API surface. The CI matrix covers multiple test module groups. JaCoCo is configured for code coverage reporting. However, no API-specific test coverage metrics were found for the S3/REST surface, and there are no dedicated contract tests validating input handling, error responses, and edge cases systematically.
- **Gap**: API tests exist but no dedicated API contract test suite with systematic coverage of input validation, error responses, and edge cases. No API-specific coverage metrics.
- **Compensating Controls**:
  - Existing integration tests (`S3ClientRestApiTest.java`) exercise the S3 API surface
  - JaCoCo provides general code coverage metrics
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a dedicated S3 API contract test suite that systematically validates all supported operations, error responses, and edge cases. Track API-specific test coverage separately.
- **Evidence**: `core/server/proxy/src/test/java/alluxio/proxy/s3/S3RestServiceHandlerTest.java`, `tests/src/test/java/alluxio/client/rest/S3ClientRestApiTest.java`

#### STATE-Q2: Queryable Current State — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Alluxio exposes current state in a queryable form through multiple APIs. The REST Paths API provides `getStatus` (GET `/api/v1/paths/{path}/get-status`) returning `URIStatus` with full file metadata, and `listStatus` (GET `/api/v1/paths/{path}/list-status`) returning children statuses. The S3 API provides `getBucket` (GET `/{bucket}`) for listing objects with metadata, `headObject` (HEAD `/{bucket}/{object}`) for object metadata, and `listAllMyBuckets` (GET `/`) for bucket listing. The Master REST API exposes system state via `getInfo` (GET `/api/v1/master/info`) returning cluster configuration, worker info, metrics, and capacity. The gRPC interface provides `GetStatus`, `ListStatus`, and `GetFileInfo` RPCs via `file_system_master.proto`. These endpoints allow an agent to inspect file system state before taking action.
- **Gap**: While queryable state endpoints exist for file system metadata, there is no consolidated "system health" or "cluster state" API that an agent can call to assess overall system readiness before issuing requests. The Master REST API provides cluster info but it is a web UI-oriented API, not an agent-friendly status endpoint. No read-before-write pattern is enforced at the API layer — agents must implement this pattern themselves.
- **Compensating Controls**:
  - Use the S3 HEAD Object endpoint to check object state before any operation
  - Use the Master REST `getInfo` endpoint for cluster-level health checks
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a dedicated agent-friendly health/status endpoint on the S3 proxy that returns cluster readiness, capacity utilization, and component health in a structured JSON format. Document recommended read-before-write patterns for agent consumers.
- **Evidence**: `core/server/proxy/src/main/java/alluxio/proxy/PathsRestServiceHandler.java` (getStatus, listStatus), `core/server/proxy/src/main/java/alluxio/proxy/s3/S3RestServiceHandler.java` (getBucket, headObject, listAllMyBuckets), `core/server/master/src/main/java/alluxio/master/meta/AlluxioMasterRestServiceHandler.java` (getInfo)

#### DATA-Q3: Selective Query Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The S3 API implements pagination for list operations via `ListBucketOptions` and `ListBucketResult`. The `getBucket` endpoint supports `max-keys` (default 1000), `marker` (v1 pagination), `continuation-token` (v2 pagination), `prefix` (filtering), `delimiter` (hierarchical listing), and `start-after` (v2 start position). The `ListBucketResult` correctly implements `IsTruncated`, `NextMarker`, and `NextContinuationToken` for paginated iteration. Both ListObjects v1 and v2 are supported. The `listAllMyBuckets` endpoint returns all buckets without pagination. The REST Paths API `listStatus` endpoint returns all children in a single response without pagination support.
- **Gap**: S3 API has robust pagination for object listing (max-keys, marker, continuation-token). However, the `listAllMyBuckets` endpoint has no pagination (returns all buckets in one response). The REST Paths API `listStatus` has no pagination — it returns all children of a directory in a single response, which can be unbounded for directories with millions of files. No sorting options are available on any endpoint.
- **Compensating Controls**:
  - Use the S3 API with `max-keys` parameter to limit result set sizes for object listing
  - Use `prefix` and `delimiter` filtering to narrow result sets before retrieval
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add pagination support to the REST Paths API `listStatus` endpoint. Add pagination to the `listAllMyBuckets` S3 endpoint (or document the expected scale). Document recommended `max-keys` values for agent consumers to avoid unbounded result sets.
- **Evidence**: `core/server/proxy/src/main/java/alluxio/proxy/s3/ListBucketOptions.java` (DEFAULT_MAX_KEYS=1000, marker, prefix, delimiter, continuationToken), `core/server/proxy/src/main/java/alluxio/proxy/s3/ListBucketResult.java` (IsTruncated, NextMarker, NextContinuationToken), `core/server/proxy/src/main/java/alluxio/proxy/s3/S3RestServiceHandler.java` (getBucket with pagination params), `core/server/proxy/src/main/java/alluxio/proxy/PathsRestServiceHandler.java` (listStatus without pagination)

#### DATA-Q5: Temporal Metadata and Freshness — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Alluxio provides temporal metadata through `URIStatus` which exposes `getCreationTimeMs()`, `getLastModificationTimeMs()`, and `getLastAccessTimeMs()` — all as epoch milliseconds. The S3 API returns `LastModified` timestamps in S3 date format (ISO 8601) for objects in `ListBucketResult.Content`, `headObject` responses, and `CopyObjectResult`. The `S3RestUtils.toS3Date()` method converts epoch milliseconds to the standard S3 date format. The gRPC proto files define `creation_time_ms`, `last_modification_time_ms`, and `last_access_time_ms` fields for file info. However, there is no freshness signaling — no `Cache-Control` headers, no `X-Data-Age` header, no indication of whether data returned is from Alluxio cache or the underlying file system (UFS). The S3 API does not distinguish between cached data (potentially stale if UFS was modified directly) and fresh data read through from the UFS.
- **Gap**: Temporal metadata (creation time, modification time, access time) exists and is returned in API responses. However, there is no data freshness signaling — agents cannot determine whether data returned is from the Alluxio cache (potentially stale) or read through from the underlying storage. No `Cache-Control`, `X-Data-Age`, or consistency-level headers are returned. Timezone normalization relies on server-local timezone settings.
- **Compensating Controls**:
  - Use the Alluxio `syncInterval` configuration to control cache-to-UFS synchronization frequency
  - Agents can force a UFS metadata sync by using the `checkContent` option before critical reads
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `X-Alluxio-Cache-Status` response header indicating whether the response was served from cache or UFS (similar to CDN cache hit/miss headers). Add `X-Data-Age` header indicating time since last UFS sync. Document cache consistency semantics for agent consumers.
- **Evidence**: `core/common/src/main/java/alluxio/client/file/URIStatus.java` (getCreationTimeMs, getLastModificationTimeMs, getLastAccessTimeMs), `core/server/proxy/src/main/java/alluxio/proxy/s3/S3RestUtils.java` (toS3Date), `core/server/proxy/src/main/java/alluxio/proxy/s3/ListBucketResult.java` (LastModified in Content)

## INFOs — Architecture and Design Inputs

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The S3 API `PUT` operations (`createObjectOrUploadPart` in `S3RestServiceHandler.java`) use `setOverwrite(true)` in `CreateFilePOptions`, making PUT idempotent (re-uploading the same object replaces it). Multipart uploads use UUID-based upload IDs. Bucket creation is idempotent for the same owner. However, `POST` operations (DeleteObjects, initiateMultipartUpload) are not inherently idempotent — there is no idempotency key support.
- **Implication**: If agents are later scoped for write operations, the lack of idempotency keys on POST operations could cause duplicate actions on retry. PUT operations are safe.
- **Recommendation**: When expanding to write scope, implement idempotency key support for POST operations (e.g., `X-Amz-Idempotency-Key` header).
- **Evidence**: `core/server/proxy/src/main/java/alluxio/proxy/s3/S3RestServiceHandler.java`

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: The S3 API produces XML responses (via `XmlMapper` from Jackson) conforming to the AWS S3 XML format. The REST Paths API produces JSON responses. The gRPC interface uses Protocol Buffers. All three formats are well-structured and machine-readable.
- **Implication**: The S3 API's XML format is standard and well-supported by all AWS S3 SDKs. Agents using the S3 API will work with any standard S3 client library. The JSON REST API is directly consumable by LLMs. Protobuf requires generated client stubs.
- **Recommendation**: For agent integration, prefer the S3 API (widely supported) or the REST Paths API (JSON). The gRPC interface is best for programmatic clients.
- **Evidence**: `core/server/proxy/src/main/java/alluxio/proxy/s3/S3RestServiceHandler.java` (@Produces APPLICATION_XML), `core/server/proxy/src/main/java/alluxio/proxy/PathsRestServiceHandler.java`

### API-Q7: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: Alluxio does not emit events or webhooks for state changes. There is no SNS, EventBridge, Kafka, or webhook integration in the codebase. The S3 proxy handles the `notification` query parameter in the `S3Handler.java` supported sub-resources list, but this maps to the S3 Bucket Notification Configuration API which is not implemented — it is only listed as a recognized query parameter. Internally, the Alluxio Master uses a journal system (Raft-based or UFS-based) to record all metadata state changes, but these journal entries are for internal replication and recovery — they are not exposed as external events. The journal entries (`JournalEntry` protobuf) capture file creates, deletes, renames, permission changes, and mount operations, but there is no mechanism to subscribe to these as external events.
- **Implication**: Agents must poll for state changes (e.g., periodically list objects to detect new files). This limits the ability to build event-driven agent workflows that react to data arrivals or file system changes in real time. For the read-only scope, polling-based approaches are adequate but less efficient.
- **Recommendation**: Consider implementing S3 Bucket Notification support (SNS/SQS/Lambda triggers on object events) to enable event-driven agent patterns. Alternatively, expose the internal journal stream as an external event subscription mechanism for real-time change detection.
- **Evidence**: `core/server/proxy/src/main/java/alluxio/proxy/s3/S3Handler.java` (notification in supported sub-resources), `core/server/master/src/main/java/alluxio/master/journal/` (internal journal system), `core/server/master/src/main/java/alluxio/master/file/FileSystemJournalEntryMerger.java` (journal entries for file operations)

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: Alluxio implements rate limiting via `mGlobalRateLimiter` in the S3 proxy and per-connection read rate limiting via `RateLimitInputStream`. However, rate limit information is not returned in response headers — there are no `X-RateLimit-Remaining`, `X-RateLimit-Limit`, or `Retry-After` headers in the S3 API responses. Rate limits are not documented in the S3 API documentation.
- **Implication**: Agents cannot self-throttle based on rate limit feedback. Rate-limited requests will fail without the agent knowing it is approaching the limit.
- **Recommendation**: Add `X-RateLimit-Remaining` and `Retry-After` headers to S3 API responses. Document the configured rate limits.
- **Evidence**: `core/server/proxy/src/main/java/alluxio/proxy/s3/S3RestServiceHandler.java` (mGlobalRateLimiter), `core/server/proxy/src/main/java/alluxio/proxy/s3/RateLimitInputStream.java`

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: INFO
- **Finding**: Alluxio propagates the authenticated user via `AuthenticatedClientUser` through gRPC call context using `AuthenticatedUserInjector` and `ClientContextServerInjector`. The S3 proxy extracts the user from the Authorization header and passes it as an internal header (`ALLUXIO_USER_HEADER`). The user identity is propagated to the Master for permission checks. However, there is no distinction between "agent acting as itself" vs. "agent acting on behalf of a user" — the S3 auth maps to a single user identity.
- **Implication**: For read-only agents accessing reference/storage data, identity propagation is adequate. The user context is correctly passed through service calls for permission checks.
- **Recommendation**: When expanding to user-delegated operations, implement an on-behalf-of flow that distinguishes agent identity from user identity in audit logs.
- **Evidence**: `core/server/proxy/src/main/java/alluxio/proxy/s3/S3AuthenticationFilter.java`, `core/common/src/main/java/alluxio/security/authentication/AuthenticatedClientUser.java` (referenced)

### AUTH-Q5: Credential Management

- **Severity**: INFO
- **Finding**: Alluxio uses Kubernetes Secrets for credential management in the Helm deployment (`values.yaml` has a `secrets` section for mounting K8s secrets into pods). The `SensitiveConfigMask` interface provides credential masking in RPC messages. `RpcSensitiveConfigMask.CREDENTIAL_FIELD_MASKER` redacts credential fields. UFS connector credentials (S3 access keys, HDFS keytabs) are expected to be provided via configuration properties or mounted secrets, not hardcoded. No hardcoded credential patterns were found in the source code or configuration templates. However, there is no AWS Secrets Manager or HashiCorp Vault integration for dynamic credential rotation.
- **Implication**: Credentials are managed via K8s Secrets (static) rather than dynamic secrets management. This is acceptable for read-only agents but limits credential rotation without pod restart.
- **Recommendation**: Consider integrating with AWS Secrets Manager or HashiCorp Vault for dynamic credential rotation, especially for UFS connector credentials.
- **Evidence**: `integration/kubernetes/helm-chart/alluxio/values.yaml` (secrets section), `core/common/src/main/java/alluxio/conf/SensitiveConfigMask.java`, `core/server/common/src/test/java/alluxio/RpcSensitiveConfigMaskTest.java`

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Alluxio has no concept of draft or pending state for file system operations. All write operations (PUT, POST, DELETE) are immediately committed. The multipart upload workflow provides a staging mechanism (parts uploaded to a temporary directory before completion), but this is specific to the S3 multipart upload protocol, not a general-purpose draft state.
- **Implication**: For read-only agents, this is not relevant. If write scope is needed, a draft/approval layer would need to be added at the orchestration level (outside Alluxio).
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: `core/server/proxy/src/main/java/alluxio/proxy/s3/S3RestServiceHandler.java`

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Alluxio has no configurable approval workflow. Operations are executed immediately upon authentication and authorization. There are no human-in-the-loop approval gates for any operation.
- **Implication**: For read-only agents, approval gates are not needed. For future write scope, approval gates would need to be implemented at the orchestration layer.
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: No evidence of approval workflow logic found in codebase.

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Alluxio has extensive concurrency controls: `InodeLockManager` for inode-level locking in the Master, `BlockLockManager` for block-level locking in the Worker, `RWLockResource` and `LockResource` for general read-write locks, and the Raft consensus protocol for Master HA. These controls are well-implemented for the file system's internal consistency.
- **Implication**: Concurrency controls are robust for internal operations. Read-only agents benefit from these controls (consistent reads). If write scope is added, the existing locking infrastructure provides strong consistency guarantees.
- **Recommendation**: No action needed for read-only scope. Existing concurrency controls are adequate.
- **Evidence**: `core/server/master/src/main/java/alluxio/master/file/meta/InodeLockManager.java` (referenced), `core/common/src/main/java/alluxio/resource/LockResource.java` (referenced)

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Alluxio has no configurable transaction limits per agent identity. The rate limiter applies globally but does not limit the number of records returned, data volume transferred, or operations per session on a per-identity basis.
- **Implication**: For read-only agents, blast radius is limited to data retrieval volume (bounded by rate limiting). No risk of destructive write operations. If write scope is added, transaction limits would be needed.
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: `core/server/proxy/src/main/java/alluxio/proxy/s3/S3RestServiceHandler.java`

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: Alluxio does not maintain data quality metrics. As a caching layer, it reflects the data quality of the underlying file systems. There are no data profiling reports, null rate monitoring, or data freshness SLAs within Alluxio itself. The `MetricKey.java` tracks operational metrics (block counts, cache hit ratios) but not data quality metrics.
- **Implication**: Agents cannot assess data quality from Alluxio metadata. Data quality analysis must be performed against the underlying storage systems.
- **Recommendation**: Document expected data quality characteristics of each UFS mount for agent consumers.
- **Evidence**: `core/common/src/main/java/alluxio/metrics/MetricKey.java`

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: The S3 API uses standard AWS S3 field names (e.g., `Key`, `ETag`, `LastModified`, `ContentLength`, `BucketName`). The REST Paths API uses clear Java-style naming (e.g., `getStatus`, `listStatus`, `createFile`, `createDirectory`). gRPC proto fields use descriptive names (`file_name`, `block_size_bytes`, `creation_time_ms`). No legacy abbreviations or cryptic codes were found.
- **Implication**: Field names are semantically meaningful and LLM-interpretable. No data dictionary needed for standard operations.
- **Recommendation**: No action needed. Naming conventions are clear and follow AWS S3 standards.
- **Evidence**: `core/transport/src/main/proto/grpc/file_system_master.proto`, `core/server/proxy/src/main/java/alluxio/proxy/s3/S3RestServiceHandler.java`

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: Alluxio has a `table/` module that provides a structured table metadata layer (catalog service). The Master maintains a complete file system namespace metadata including path hierarchy, file sizes, timestamps, and ACLs. However, there is no data catalog in the AWS Glue or Collibra sense — no semantic descriptions of what data exists or what it means.
- **Implication**: Agents can discover file/object structure through the S3 API (ListBucket, GetObject metadata) but cannot discover semantic meaning of the data. Tool builders must provide contextual documentation.
- **Recommendation**: Consider publishing a metadata catalog describing the data available through Alluxio mount points for agent tool definition.
- **Evidence**: `table/` module directory, `core/server/proxy/src/main/java/alluxio/proxy/s3/S3RestServiceHandler.java` (listAllMyBuckets, getBucket endpoints)

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: Alluxio publishes extensive operational metrics via `MetricKey.java` (2,845 lines of metric definitions) including cache hit rates, bytes read/written, RPC latencies, and capacity utilization. Proxy-specific metrics include audit log entries size and multipart upload latencies. Metrics are available via JMX, Prometheus, Graphite, and CSV sinks. However, these are infrastructure/operational metrics — no business outcome metrics (e.g., agent task completion rates, data retrieval success rates for agent workflows) are published.
- **Implication**: When agents consume Alluxio, business-level metrics (agent cache hit rates, agent-specific latency) should be added to measure agent interaction quality.
- **Recommendation**: Define and publish agent-interaction-specific metrics (e.g., `Agent.RequestLatencyP99`, `Agent.CacheHitRate`, `Agent.ErrorRate`) once agent integration begins.
- **Evidence**: `core/common/src/main/java/alluxio/metrics/MetricKey.java`, `conf/metrics.properties.template`

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO (no gap — documented interfaces exist)
- **Finding**: Alluxio exposes three documented API surfaces: (1) S3-compatible REST API via `S3RestServiceHandler.java` with full JAX-RS annotations (GET, PUT, POST, DELETE, HEAD), (2) Alluxio REST API via `PathsRestServiceHandler.java` with Swagger annotations (`@Api`, `@ApiOperation`), and (3) gRPC services defined in protobuf files (`file_system_master.proto`, `block_worker.proto`, etc.). API documentation exists in `docs/en/api/` (REST-API.md, S3-API.md, POSIX-API.md, Java-API.md). No direct database access or UI automation is required for integration.
- **Gap**: None — documented REST, S3, and gRPC interfaces are available.
- **Recommendation**: Continue maintaining the S3 API as the primary agent-facing interface.
- **Evidence**: `core/server/proxy/src/main/java/alluxio/proxy/s3/S3RestServiceHandler.java`, `core/server/proxy/src/main/java/alluxio/proxy/PathsRestServiceHandler.java`, `docs/en/api/S3-API.md`, `docs/en/api/REST-API.md`, `core/transport/src/main/proto/grpc/file_system_master.proto`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section above.
- **Gap**: No committed OpenAPI/Swagger spec file.
- **Recommendation**: Generate and commit OpenAPI spec via swagger-maven-plugin.
- **Evidence**: `pom.xml`, `core/server/proxy/src/main/java/alluxio/proxy/PathsRestServiceHandler.java`

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section above.
- **Gap**: No explicit retryability indicator.
- **Recommendation**: Add retryable field to error responses.
- **Evidence**: `core/server/proxy/src/main/java/alluxio/proxy/s3/S3ErrorCode.java`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: See INFOs section above.
- **Gap**: POST operations lack idempotency key support.
- **Recommendation**: Implement idempotency keys when expanding to write scope.
- **Evidence**: `core/server/proxy/src/main/java/alluxio/proxy/s3/S3RestServiceHandler.java`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: See INFOs section above.
- **Gap**: N/A — all formats are structured and machine-readable.
- **Recommendation**: Prefer S3 API (XML) or REST API (JSON) for agent integration.
- **Evidence**: `core/server/proxy/src/main/java/alluxio/proxy/s3/S3RestServiceHandler.java`

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `orchestrator`, agent_scope: `read-only`.
- **Trigger**: Service has operations >30s OR long-running workflows
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: Alluxio does not emit events or webhooks for state changes. No SNS, EventBridge, Kafka, or webhook integration exists. The S3 proxy lists `notification` as a recognized sub-resource in `S3Handler.java` but the S3 Bucket Notification Configuration API is not implemented. The Master's internal journal system records all metadata state changes (creates, deletes, renames, permission changes) but these are for internal replication/recovery and not exposed as external events.
- **Gap**: No external event emission mechanism. Agents must poll for state changes.
- **Recommendation**: Implement S3 Bucket Notification support or expose the internal journal stream as an external event subscription mechanism.
- **Evidence**: `core/server/proxy/src/main/java/alluxio/proxy/s3/S3Handler.java`, `core/server/master/src/main/java/alluxio/master/file/FileSystemJournalEntryMerger.java`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: See INFOs section above.
- **Gap**: No rate limit headers in API responses.
- **Recommendation**: Add X-RateLimit-Remaining headers.
- **Evidence**: `core/server/proxy/src/main/java/alluxio/proxy/s3/S3RestServiceHandler.java`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: See BLOCKERs section above.
- **Gap**: No machine identity authentication with principal attribution.
- **Recommendation**: Implement CUSTOM auth provider for agent credentials.
- **Evidence**: `core/common/src/main/java/alluxio/security/authentication/AuthType.java`, `core/server/proxy/src/main/java/alluxio/proxy/s3/S3AuthenticationFilter.java`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: See RISKs section above.
- **Gap**: POSIX permissions are coarse-grained.
- **Recommendation**: Create dedicated users per agent with minimal POSIX permissions.
- **Evidence**: `core/common/src/main/java/alluxio/security/authorization/Mode.java`, `core/server/master/src/main/java/alluxio/master/file/DefaultPermissionChecker.java`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: See RISKs section above.
- **Gap**: Cannot grant "read but not delete" on same resource via S3 API.
- **Recommendation**: Use read-only POSIX permissions for agent users.
- **Evidence**: `core/common/src/main/java/alluxio/security/authorization/AclAction.java`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: See INFOs section above.
- **Gap**: No agent-as-self vs agent-on-behalf-of distinction.
- **Recommendation**: Implement on-behalf-of flow for future scope.
- **Evidence**: `core/server/proxy/src/main/java/alluxio/proxy/s3/S3AuthenticationFilter.java`

#### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: See INFOs section above.
- **Gap**: Static secrets via K8s, no dynamic rotation.
- **Recommendation**: Consider Secrets Manager integration.
- **Evidence**: `integration/kubernetes/helm-chart/alluxio/values.yaml`, `core/common/src/main/java/alluxio/conf/SensitiveConfigMask.java`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: See RISKs section above.
- **Gap**: Audit logs are not immutable.
- **Recommendation**: Ship logs to immutable store.
- **Evidence**: `conf/log4j.properties`, `core/server/proxy/src/main/java/alluxio/proxy/s3/S3AuditContext.java`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: See RISKs section above.
- **Gap**: No identity suspension mechanism.
- **Recommendation**: Deploy API gateway with key management.
- **Evidence**: `core/common/src/main/java/alluxio/security/authentication/AuthType.java`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: See RISKs section above.
- **Gap**: No general-purpose compensation/rollback.
- **Recommendation**: Low priority for read-only scope.
- **Evidence**: `core/server/proxy/src/main/java/alluxio/proxy/s3/S3RestServiceHandler.java`

#### STATE-Q2: Queryable Current State
- **Severity**: RISK-QUALITY
- **Finding**: Alluxio exposes current state through the REST Paths API (`getStatus`, `listStatus`), the S3 API (`getBucket`, `headObject`, `listAllMyBuckets`), the Master REST API (`getInfo`), and the gRPC interface (`GetStatus`, `ListStatus`, `GetFileInfo`). Agents can inspect file system metadata before taking action.
- **Gap**: No consolidated agent-friendly health/status endpoint. Master REST API is web UI-oriented. No read-before-write enforcement at the API layer.
- **Recommendation**: Create a dedicated health/status endpoint on the S3 proxy for agent consumers.
- **Evidence**: `core/server/proxy/src/main/java/alluxio/proxy/PathsRestServiceHandler.java`, `core/server/proxy/src/main/java/alluxio/proxy/s3/S3RestServiceHandler.java`, `core/server/master/src/main/java/alluxio/master/meta/AlluxioMasterRestServiceHandler.java`

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: See INFOs section above.
- **Gap**: N/A — robust concurrency controls exist.
- **Recommendation**: No action for read-only scope.
- **Evidence**: `core/server/master/src/main/java/alluxio/master/file/meta/InodeLockManager.java`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: See RISKs section above.
- **Gap**: No circuit breaker pattern.
- **Recommendation**: Add circuit breakers or deploy service mesh.
- **Evidence**: `core/common/src/main/java/alluxio/retry/ExponentialBackoffRetry.java`, `core/common/src/main/java/alluxio/AbstractClient.java`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: See RISKs section above.
- **Gap**: Global rate limiting only, no per-identity limits.
- **Recommendation**: Implement per-identity rate limiting.
- **Evidence**: `core/server/proxy/src/main/java/alluxio/proxy/s3/S3RestServiceHandler.java`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: See INFOs section above.
- **Gap**: No per-identity transaction limits.
- **Recommendation**: No action for read-only scope.
- **Evidence**: `core/server/proxy/src/main/java/alluxio/proxy/s3/S3RestServiceHandler.java`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `orchestrator`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: See INFOs section above.
- **Gap**: No draft/pending state support.
- **Recommendation**: No action for read-only scope.
- **Evidence**: `core/server/proxy/src/main/java/alluxio/proxy/s3/S3RestServiceHandler.java`

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: See INFOs section above.
- **Gap**: No approval workflow support.
- **Recommendation**: No action for read-only scope.
- **Evidence**: No evidence found (absence is the finding).

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: Alluxio provides a `minicluster/` module for local testing that spins up a complete Alluxio cluster (Master, Worker, Proxy) in a single JVM. Docker-based local testing is available via `integration/docker/` with Dockerfile and docker-compose files (`docker-compose-master.yaml`, `docker-compose-worker.yaml`). The Helm chart supports multiple environment configurations. However, there is no production-equivalent staging environment with production-scale data shape, and no synthetic data generators.
- **Gap**: Local testing environments exist (minicluster, Docker) but no production-equivalent staging with realistic data shape for agent testing.
- **Compensating Controls**:
  - Use minicluster for unit/integration testing of agent interactions
  - Deploy a dedicated Alluxio cluster for staging with sample data
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a staging Alluxio deployment with production-representative mount points and data samples for agent testing.
- **Evidence**: `minicluster/` directory, `integration/docker/Dockerfile`, `integration/metrics/docker-compose-master.yaml`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: See BLOCKERs section above.
- **Gap**: No data classification system.
- **Recommendation**: Implement path-level classification.
- **Evidence**: `core/server/proxy/src/main/java/alluxio/proxy/s3/S3RestServiceHandler.java`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: See RISKs section above.
- **Gap**: No data residency enforcement.
- **Recommendation**: Configure tiered locality for regional compliance.
- **Evidence**: `core/common/src/main/java/alluxio/conf/PropertyKey.java`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK-QUALITY
- **Finding**: The S3 API supports pagination via `max-keys` (default 1000), `marker` (v1), `continuation-token` (v2), `prefix`, `delimiter`, and `start-after`. `ListBucketResult` implements `IsTruncated`, `NextMarker`, and `NextContinuationToken`. Both ListObjects v1 and v2 are supported. However, `listAllMyBuckets` has no pagination and the REST Paths API `listStatus` returns all children without pagination.
- **Gap**: S3 object listing has robust pagination. Bucket listing and REST Paths API `listStatus` lack pagination and can return unbounded results.
- **Recommendation**: Add pagination to REST Paths API `listStatus` and `listAllMyBuckets`. Document recommended `max-keys` values for agents.
- **Evidence**: `core/server/proxy/src/main/java/alluxio/proxy/s3/ListBucketOptions.java`, `core/server/proxy/src/main/java/alluxio/proxy/s3/ListBucketResult.java`, `core/server/proxy/src/main/java/alluxio/proxy/s3/S3RestServiceHandler.java`

#### DATA-Q4: System of Record Designations
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `orchestrator`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK-QUALITY
- **Finding**: Alluxio provides temporal metadata via `URIStatus` (`getCreationTimeMs`, `getLastModificationTimeMs`, `getLastAccessTimeMs`). The S3 API returns `LastModified` timestamps in ISO 8601 S3 date format. However, there is no freshness signaling — no `Cache-Control`, `X-Data-Age`, or consistency-level headers. Agents cannot determine whether data is from cache (potentially stale) or UFS (fresh).
- **Gap**: Temporal metadata exists but no data freshness signaling. Timezone normalization relies on server-local settings.
- **Recommendation**: Add `X-Alluxio-Cache-Status` and `X-Data-Age` headers. Document cache consistency semantics for agents.
- **Evidence**: `core/common/src/main/java/alluxio/client/file/URIStatus.java`, `core/server/proxy/src/main/java/alluxio/proxy/s3/S3RestUtils.java`, `core/server/proxy/src/main/java/alluxio/proxy/s3/ListBucketResult.java`

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: See RISKs section above.
- **Gap**: No PII redaction in audit logs.
- **Recommendation**: Add log scrubbing middleware.
- **Evidence**: `core/common/src/main/java/alluxio/conf/SensitiveConfigMask.java`, `conf/log4j.properties`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: See INFOs section above.
- **Gap**: No data quality metrics.
- **Recommendation**: Document data quality characteristics per UFS mount.
- **Evidence**: `core/common/src/main/java/alluxio/metrics/MetricKey.java`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section above.
- **Gap**: No REST/S3 API breaking change detection in CI.
- **Recommendation**: Add OpenAPI diff to CI pipeline.
- **Evidence**: `core/transport/src/main/proto/proto.lock`, `pom.xml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: See INFOs section above.
- **Gap**: None — field names are clear.
- **Recommendation**: No action needed.
- **Evidence**: `core/transport/src/main/proto/grpc/file_system_master.proto`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: See INFOs section above.
- **Gap**: No semantic data catalog.
- **Recommendation**: Publish metadata catalog for agent tool builders.
- **Evidence**: `table/` module

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section above.
- **Gap**: OTel is optional, logs not JSON-structured, no correlation IDs.
- **Recommendation**: Embed OTel instrumentation, switch to JSON logging.
- **Evidence**: `integration/metrics/otel-collector-config.yaml`, `conf/log4j.properties`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section above.
- **Gap**: No alerting rules configured.
- **Recommendation**: Create Prometheus alerting rules.
- **Evidence**: `integration/metrics/prometheus.yaml`, `core/common/src/main/java/alluxio/metrics/MetricKey.java`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: See INFOs section above.
- **Gap**: Only infrastructure metrics, no business outcomes.
- **Recommendation**: Define agent-specific metrics.
- **Evidence**: `core/common/src/main/java/alluxio/metrics/MetricKey.java`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section above.
- **Gap**: No cloud infrastructure IaC, no drift detection.
- **Recommendation**: Create Terraform/CDK for surrounding infrastructure.
- **Evidence**: `integration/kubernetes/helm-chart/alluxio/Chart.yaml`, `integration/kubernetes/helm-chart/alluxio/values.yaml`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section above.
- **Gap**: No API contract testing in CI.
- **Recommendation**: Add OpenAPI validation and contract tests to CI.
- **Evidence**: `.github/workflows/java8_unit_tests.yml`, `.github/workflows/checkstyle.yml`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section above.
- **Gap**: Basic Helm rollback only, no automated rollback.
- **Recommendation**: Add canary deployment and automated rollback.
- **Evidence**: `integration/kubernetes/helm-chart/alluxio/values.yaml`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: See RISKs section above.
- **Gap**: No systematic API contract test suite.
- **Recommendation**: Create dedicated S3 API contract test suite.
- **Evidence**: `core/server/proxy/src/test/java/alluxio/proxy/s3/S3RestServiceHandlerTest.java`, `tests/src/test/java/alluxio/client/rest/S3ClientRestApiTest.java`

#### ENG-Q5: Encryption at Rest
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `orchestrator`, agent_scope: `read-only`.
- **Trigger**: Service has persistent data stores
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `core/server/proxy/src/main/java/alluxio/proxy/s3/S3RestServiceHandler.java` | API-Q1, API-Q2, API-Q3, API-Q4, API-Q5, API-Q8, AUTH-Q1, DATA-Q1, DATA-Q3, STATE-Q1, STATE-Q2, STATE-Q5, STATE-Q6, HITL-Q1 |
| `core/server/proxy/src/main/java/alluxio/proxy/PathsRestServiceHandler.java` | API-Q1, API-Q2, API-Q5, DATA-Q3, STATE-Q2 |
| `core/server/proxy/src/main/java/alluxio/proxy/s3/S3ErrorCode.java` | API-Q3 |
| `core/server/proxy/src/main/java/alluxio/proxy/s3/S3ErrorResponse.java` | API-Q3 |
| `core/server/proxy/src/main/java/alluxio/proxy/s3/S3AuditContext.java` | AUTH-Q1, AUTH-Q6, DATA-Q6 |
| `core/server/proxy/src/main/java/alluxio/proxy/s3/S3AuthenticationFilter.java` | AUTH-Q1, AUTH-Q4, AUTH-Q7 |
| `core/server/proxy/src/main/java/alluxio/proxy/s3/RateLimitInputStream.java` | API-Q8, STATE-Q5 |
| `core/server/proxy/src/main/java/alluxio/proxy/s3/S3Handler.java` | API-Q7 |
| `core/server/proxy/src/main/java/alluxio/proxy/s3/ListBucketOptions.java` | DATA-Q3 |
| `core/server/proxy/src/main/java/alluxio/proxy/s3/ListBucketResult.java` | DATA-Q3, DATA-Q5 |
| `core/common/src/main/java/alluxio/security/authentication/AuthType.java` | AUTH-Q1, AUTH-Q7 |
| `core/common/src/main/java/alluxio/security/authorization/Mode.java` | AUTH-Q2, AUTH-Q3 |
| `core/common/src/main/java/alluxio/security/authorization/AccessControlList.java` | AUTH-Q2, DATA-Q1 |
| `core/common/src/main/java/alluxio/security/authorization/AclAction.java` | AUTH-Q3 |
| `core/server/master/src/main/java/alluxio/master/file/DefaultPermissionChecker.java` | AUTH-Q2, AUTH-Q3 |
| `core/common/src/main/java/alluxio/conf/SensitiveConfigMask.java` | AUTH-Q5, DATA-Q6 |
| `core/common/src/main/java/alluxio/conf/PropertyKey.java` | DATA-Q2 |
| `core/common/src/main/java/alluxio/retry/ExponentialBackoffRetry.java` | STATE-Q4 |
| `core/common/src/main/java/alluxio/retry/RetryPolicy.java` | STATE-Q4 |
| `core/common/src/main/java/alluxio/AbstractClient.java` | STATE-Q4 |
| `core/common/src/main/java/alluxio/metrics/MetricKey.java` | OBS-Q2, OBS-Q3, DATA-Q7 |
| `core/common/src/main/java/alluxio/client/file/URIStatus.java` | DATA-Q5 |
| `core/server/proxy/src/main/java/alluxio/proxy/s3/S3RestUtils.java` | DATA-Q5 |
| `core/server/master/src/main/java/alluxio/master/meta/AlluxioMasterRestServiceHandler.java` | STATE-Q2 |
| `core/server/master/src/main/java/alluxio/master/file/FileSystemJournalEntryMerger.java` | API-Q7 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `core/transport/src/main/proto/grpc/file_system_master.proto` | API-Q1, API-Q2, DISC-Q2 |
| `core/transport/src/main/proto/grpc/block_worker.proto` | API-Q1 |
| `core/transport/src/main/proto/proto.lock` | DISC-Q1, ENG-Q2 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/java8_unit_tests.yml` | ENG-Q2, ENG-Q4 |
| `.github/workflows/checkstyle.yml` | ENG-Q2 |
| `.github/workflows/java8_integration_tests.yml` | ENG-Q2 |
| `.github/workflows/fuse_integration_tests.yml` | ENG-Q2 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `integration/docker/Dockerfile` | HITL-Q3 |
| `integration/metrics/docker-compose-master.yaml` | HITL-Q3, OBS-Q1 |
| `integration/metrics/docker-compose-worker.yaml` | HITL-Q3, OBS-Q1 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `pom.xml` | API-Q2, DISC-Q1, ENG-Q2 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `conf/log4j.properties` | AUTH-Q6, DATA-Q6, OBS-Q1 |
| `conf/metrics.properties.template` | OBS-Q2, OBS-Q3 |
| `integration/kubernetes/helm-chart/alluxio/values.yaml` | AUTH-Q5, DATA-Q2, ENG-Q1, ENG-Q3, STATE-Q5, DATA-Q1 |
| `integration/kubernetes/helm-chart/alluxio/Chart.yaml` | ENG-Q1, ENG-Q3 |
| `integration/metrics/otel-collector-config.yaml` | OBS-Q1 |
| `integration/metrics/otel-agent-config.yaml` | OBS-Q1 |
| `integration/metrics/prometheus.yaml` | OBS-Q2 |

### Documentation
| File | Questions Referenced |
|------|---------------------|
| `docs/en/api/S3-API.md` | API-Q1 |
| `docs/en/api/REST-API.md` | API-Q1 |

### Test Suites
| File | Questions Referenced |
|------|---------------------|
| `core/server/proxy/src/test/java/alluxio/proxy/s3/S3RestServiceHandlerTest.java` | ENG-Q4 |
| `tests/src/test/java/alluxio/client/rest/S3ClientRestApiTest.java` | ENG-Q4 |
| `core/server/common/src/test/java/alluxio/RpcSensitiveConfigMaskTest.java` | AUTH-Q5 |
