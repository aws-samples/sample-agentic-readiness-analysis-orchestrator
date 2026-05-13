# Agentic Readiness Assessment Report

**Target**: scality/cloudserver (Zenko CloudServer)
**Date**: 2026-04-29
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: javascript, storage, s3
**Context**: Scality open-source S3-compatible object-storage server.

**Archetype Justification**: The application has persistent state via MongoDB and file-based storage, exposes full S3 CRUD operations (PUT/GET/DELETE/HEAD on buckets and objects), manages entity lifecycle (versioning, multipart uploads, object lock/retention), and handles user-specific data (per-account credentials, canonical IDs, bucket ownership).

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 1 | **RISK-SAFETY**: 6 | **RISK-QUALITY**: 10 | **INFOs**: 9

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 1 |
| RISK-SAFETY | 6 |
| RISK-QUALITY | 10 |
| INFO | 9 |
| N/A | 0 |
| Not Evaluated (extended) | 4 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 15
**Extended Questions Not Triggered**: 4
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: stateful-crud (auto-detected)

> **Note**: 13 questions evaluated with no gap found (controls present). These are included in the Detailed Findings section with positive findings but excluded from the severity counts above.

---

## BLOCKERs — Must Resolve Before Agent Deployment

### DATA-Q1: Sensitive Data Classification — BLOCKER

- **Severity**: BLOCKER
- **Finding**: CloudServer is a general-purpose S3-compatible object storage server that stores arbitrary user data. The KMS integration (`lib/kms/wrapper.js`) provides server-side encryption (SSE-S3, SSE-KMS via AWS KMS or KMIP), and bucket-level encryption configuration exists (`lib/api/bucketPutEncryption.js`). However, there is no field-level or object-level data classification system. The server stores objects with user-defined metadata but does not classify data as PII, PHI, financial, or otherwise sensitive. There are no data classification tags on storage resources, no Macie-equivalent integration, and no controls preventing an agent from retrieving sensitive data without explicit authorization beyond standard S3 ACL/policy checks.
- **Gap**: No data classification at the field or object level. An agent with read access to a bucket can retrieve any object regardless of data sensitivity. There is no mechanism to tag objects as containing PII or regulated data and enforce differential access controls based on classification.
- **Remediation**:
  - **Immediate**: Implement object tagging conventions for data classification (e.g., `x-amz-tagging: classification=pii`) and add bucket policies that restrict agent identities from accessing objects with specific classification tags.
  - **Target State**: All buckets containing sensitive data have classification tags, and agent access is scoped by classification level via bucket policies or tag-based access control.
  - **Estimated Effort**: Medium (30–60 days for policy framework, ongoing for classification)
  - **Dependencies**: AUTH-Q2 (scoped permissions) must be functional to enforce classification-based restrictions.
- **Evidence**: `lib/kms/wrapper.js`, `lib/api/bucketPutEncryption.js`, `config.json` (defaultEncryptionKeyPerAccount setting). No data classification tags or PII detection found in codebase.

---

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q6: Immutable Audit Logging — RISK-SAFETY ⚡

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Server access logs are implemented in `lib/utilities/serverAccessLogger.js` with comprehensive log entries including requester identity, operation, bucket, object key, HTTP status, IP, and timing data. The log schema is well-defined in `schema/server_access_log.schema.json`. Logs are written to a local file (`/logs/server-access.log` per `config.json`). The `ServerAccessLogger` class uses a file stream with rotation detection.
- **Gap**: Logs are written to a local filesystem path with no immutability or tamper-evidence guarantees. There is no CloudTrail integration, no S3 Object Lock on log storage, no log file validation (checksums/signing), and no centralized immutable log sink. A compromised system could modify or delete logs. The `loggingEnabled` flag in access logs is controlled per-bucket, meaning some operations may not be logged.
- **Compensating Controls**:
  - Ship log files to a centralized, immutable log store (e.g., CloudWatch Logs with retention policies, S3 with Object Lock) via a sidecar or log shipper.
  - Enable OS-level file immutability attributes on the log directory.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Integrate log shipping to an immutable store (S3 with Object Lock or CloudWatch Logs with mandatory retention). Add log integrity verification (file checksums).
- **Evidence**: `lib/utilities/serverAccessLogger.js`, `schema/server_access_log.schema.json`, `config.json` (`serverAccessLogs` section)

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Authentication is handled via Vault (`lib/auth/vault.js`) which supports three modes: in-memory backend (static credentials from `conf/authdata.json`), Vault client (external vaultclient service), and ChainBackend (both). The in-memory backend uses a static credential list that can be refreshed via config reload (`config.on('authdata-update')`). The external Vault service likely supports account/key management operations.
- **Gap**: The in-memory auth backend does not expose an API to disable individual accounts or revoke specific API keys at runtime. Key revocation requires modifying `authdata.json` and triggering a config reload or service restart. There is no instant, API-driven suspension mechanism visible in the codebase for the in-memory backend. The external Vault service may support this, but it is an external dependency not present in this repository.
- **Compensating Controls**:
  - Use the external Vault service (vaultclient) which supports account management, rather than the in-memory backend, for agent identities.
  - Implement a bucket policy that explicitly denies the agent's canonical ID as a fast revocation mechanism.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: When deploying with agent identities, use the external Vault service (not in-memory) and ensure Vault's account disable/key revocation APIs are accessible to operators.
- **Evidence**: `lib/auth/vault.js`, `lib/auth/in_memory/backend.js`, `conf/authdata.json`

#### STATE-Q1: Compensation and Rollback — RISK-SAFETY ⚡

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The application supports multipart upload abort (`lib/api/multipartDelete.js`) which cleans up incomplete uploads, and object versioning enables recovery from unintended modifications. Object Lock and retention (`lib/api/objectPutRetention.js`, `lib/api/objectPutLegalHold.js`) provide write-once-read-many protection.
- **Gap**: There is no general-purpose saga pattern, compensating transaction framework, or explicit undo/rollback API for multi-step operations. If a complex operation (e.g., multi-object delete, batch operations through lifecycle rules) fails partway through, there is no built-in mechanism to roll back the completed steps. The multipart upload abort is the only compensation pattern present, and it applies only to that specific workflow.
- **Compensating Controls**:
  - For read-only agents, this risk is reduced since agents will not initiate multi-step write operations.
  - Enable object versioning on buckets the agent interacts with to provide an implicit safety net.
- **Remediation Timeline**: 60–90 days (for a general compensation framework)
- **Recommendation**: Enable object versioning on all agent-accessible buckets. If write scope is added later, implement explicit rollback APIs for critical multi-step operations.
- **Evidence**: `lib/api/multipartDelete.js`, `lib/api/bucketPutVersioning.js`, `lib/api/objectPutRetention.js`

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The application proxies requests to multiple external backends including AWS S3, Azure Blob Storage, and GCP Cloud Storage (`lib/data/wrapper.js`, `config.json` `externalBackends` section). HTTP agent configuration exists with `keepAlive`, `maxSockets`, and `maxFreeSockets` settings. The health check system (`lib/utilities/healthcheckHandler.js`) performs client health checks across data, metadata, vault, and KMS backends.
- **Gap**: No circuit breaker pattern (e.g., Resilience4j equivalent, opossum) is implemented. No exponential backoff or retry logic with jitter is visible for external backend calls. The `externalBackends` configuration controls HTTP agent pooling but not failure isolation. If an external backend (e.g., AWS S3) becomes degraded, CloudServer will continue sending requests, potentially cascading the failure to all clients including agents.
- **Compensating Controls**:
  - Implement application-level timeouts on all external backend HTTP clients.
  - Use infrastructure-level circuit breakers (e.g., service mesh) in front of external backends.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement circuit breakers (e.g., `opossum` npm package) for each external backend client. Add exponential backoff with jitter for retries. The existing health check infrastructure can feed circuit breaker state.
- **Evidence**: `lib/data/wrapper.js`, `config.json` (`externalBackends` section), `lib/utilities/healthcheckHandler.js`

#### DATA-Q2: Data Residency and Sovereignty — RISK-SAFETY ⚡

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The application has a location constraint system (`locationConfig.json`) that maps region names to storage backends. Buckets are associated with location constraints at creation time. The `replicationEndpoints` configuration in `config.json` defines cross-region replication targets. The system supports multiple storage backends across AWS regions, Azure, and GCP.
- **Gap**: While location constraints exist, there is no enforcement mechanism preventing data from being read by an agent and transmitted to an LLM provider in a different region/jurisdiction. The location configuration defines where data IS stored, not where it CAN be accessed from. No data residency policy enforcement (e.g., geo-fencing read access, preventing cross-region API responses) exists. Cross-region replication is configured without residency boundary checks.
- **Compensating Controls**:
  - Deploy agents in the same region as the CloudServer instance to minimize cross-region data movement.
  - Use network-level controls (VPC, security groups) to restrict which regions can access the CloudServer API.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement data residency awareness in agent tool design — agents consuming this data should be configured to use same-region LLM endpoints. Add bucket tagging for residency requirements and enforce residency-aware access at the bucket policy level.
- **Evidence**: `locationConfig.json`, `config.json` (`restEndpoints`, `replicationEndpoints` sections)

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Server access logs (`lib/utilities/serverAccessLogger.js`) record the requester's canonical ID, AWS access key ID, client IP address, and user agent for every request. The log schema (`schema/server_access_log.schema.json`) includes fields `awsAccessKeyID`, `clientIP`, `requester`, `userName`, `accountName`, and `objectKey`. Application logs via werelogs (`lib/utilities/logger.js`) log request details with structured JSON.
- **Gap**: No PII redaction or masking is applied to log entries. AWS access key IDs are logged in full. Client IP addresses are logged without masking. Object keys (which may contain PII in the key name) are logged verbatim. There is no log scrubbing middleware, no PII detection (no Macie integration), and no field-level masking for sensitive log fields. If an agent accesses objects with PII-containing keys, those keys appear in cleartext in access logs.
- **Compensating Controls**:
  - Restrict access to log files and log aggregation systems.
  - Implement log scrubbing at the log shipping layer before logs reach the analysis platform.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add PII masking to `serverAccessLogger.js` — at minimum, mask the middle portion of access key IDs and the last octets of client IP addresses. Add a configurable allow-list of fields that should not be masked. Evaluate object key patterns to detect and mask PII in keys.
- **Evidence**: `lib/utilities/serverAccessLogger.js`, `schema/server_access_log.schema.json`, `lib/utilities/logger.js`

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, GraphQL, or Smithy specification file exists in the repository. The API is defined implicitly through the S3 protocol implementation in `lib/api/api.js` (70+ route handlers) and the arsenal library's S3 route handling.
- **Gap**: While the S3 API is a well-documented public protocol (AWS's own documentation serves as the de facto specification), the repository contains no machine-readable spec. Agent tool generation requires either manual authoring or referencing the external AWS S3 API documentation. Deviations from the standard S3 API (e.g., Scality-specific extensions like metadata search, backbeat routes, rate limiting APIs) are not documented in any machine-readable format.
- **Compensating Controls**:
  - Use the AWS S3 SDK/API specification as the base tool definition for agents.
  - Document Scality-specific extensions separately.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Generate an OpenAPI specification for the CloudServer API, starting with the S3-compatible endpoints and adding Scality-specific extensions (metadata search, backbeat, rate limiting admin).
- **Evidence**: `lib/api/api.js`, `lib/routes/` directory. No `openapi.*`, `swagger.*`, or `asyncapi.*` files found.

#### API-Q6: Asynchronous Operation Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The application supports multipart uploads (`lib/api/initiateMultipartUpload.js`, `lib/api/completeMultipartUpload.js`) and object restore from cold storage (`lib/api/objectRestore.js`). These are inherently long-running operations. Multipart uploads use the standard S3 multi-step pattern (initiate → upload parts → complete). Object restore transitions objects from cold to warm storage.
- **Gap**: While multipart uploads follow the S3 standard async pattern, there is no generic job submission / status polling / webhook callback pattern for long-running operations. Object restore does not expose a polling endpoint for restore status beyond checking the object's `x-amz-restore` header. There is no progress tracking for large multi-object deletions.
- **Compensating Controls**:
  - Agents can poll object metadata (HEAD requests) to check restore status.
  - Multipart upload status can be queried via listParts.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document the existing async patterns (multipart upload, object restore) as agent-consumable workflows. Consider adding a generic job status API for long-running batch operations.
- **Evidence**: `lib/api/initiateMultipartUpload.js`, `lib/api/completeMultipartUpload.js`, `lib/api/objectRestore.js`

#### AUTH-Q4: Identity Propagation and Delegation — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Authentication flows through Vault (`lib/auth/vault.js`) using AWS Signature V4 (via arsenal's auth module). The system supports assumed roles (`isRequesterASessionUser` in `permissionChecks.js`) and IAM users (`isRequesterAnIAMUser`). Request context includes the authenticated principal's ARN, canonical ID, and account information. Internal service requests are identified via `req.isInternalServiceRequest` flag.
- **Gap**: No OAuth2 token exchange or on-behalf-of flow exists. The system distinguishes between service accounts and user accounts (via `isServiceAccount()` checking canonical ID patterns) but does not support an agent acting on behalf of a specific user with that user's permissions. The `x-scal-request-uids` header is used for request correlation, not identity propagation. There is no mechanism for an agent to present both its own identity and the delegating user's identity.
- **Compensating Controls**:
  - Use separate API keys per agent scope (read-only, per-bucket) to simulate scoped delegation.
  - Log both the agent identity and the originating user context at the agent orchestration layer.
- **Remediation Timeline**: 90–180 days
- **Recommendation**: For read-only agents, identity propagation is less critical. If write-enabled scope is planned, implement assumed role support where agents can assume roles with the delegating user's permission boundaries.
- **Evidence**: `lib/auth/vault.js`, `lib/api/apiUtils/authorization/permissionChecks.js`, `lib/server.js`

#### AUTH-Q5: Credential Management — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The repository contains `conf/authdata.json` with sample account credentials (`accessKey1`/`verySecretKey1`, etc.). The `config.json` file includes `kmsAWS` section with `"ak": "tbd"` and `"sk": "tbd"` placeholder values. The `docker-entrypoint.sh` reads credentials from `/run/secrets/s3-credentials` (Docker Swarm secrets). The CI configuration uses GitHub Actions secrets for external backend credentials.
- **Gap**: The in-memory auth backend relies on `authdata.json` which ships with sample/placeholder credentials. While marked as samples, the file is in the repository and could be deployed as-is. The `kmsAWS` section has placeholder access/secret keys in `config.json`. No integration with AWS Secrets Manager or HashiCorp Vault (the secrets manager, distinct from Scality Vault) for runtime credential rotation is present. Docker Swarm secrets support exists but is limited to that orchestrator.
- **Compensating Controls**:
  - Use the external Vault service (vaultclient) instead of the in-memory backend for production credentials.
  - Override credentials via environment variables or Docker Swarm secrets rather than filesystem.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Remove sample credentials from repository files. Add support for external secrets management (AWS Secrets Manager, HashiCorp Vault) with credential rotation. Ensure `authdata.json` is never deployed with sample credentials.
- **Evidence**: `conf/authdata.json`, `config.json` (`kmsAWS` section), `docker-entrypoint.sh` (Docker secrets handling)

#### DATA-Q4: System of Record Designations — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: CloudServer stores object data and metadata across multiple backends (file, MongoDB, in-memory, AWS S3, Azure, GCP). The metadata system tracks object ownership, versioning, and storage location. Cross-region replication is configured via `replicationEndpoints` in `config.json`.
- **Gap**: No system-of-record designation exists. When data is replicated across multiple backends or regions, there is no documented golden record or conflict resolution strategy. An agent querying replicated data may receive different versions depending on which replica it hits. No master data management documentation exists.
- **Compensating Controls**:
  - Configure agent tools to always read from the primary replica/region.
  - Use versioned reads (with version ID) for consistency.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document which storage backend is authoritative for each data location. Implement read-after-write consistency guarantees for agent-facing endpoints.
- **Evidence**: `config.json` (`replicationEndpoints`, `mongodb` sections), `locationConfig.json`

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The application implements the S3 protocol, which is versioned externally by AWS. The `schema/server_access_log.schema.json` includes a `logFormatVersion` field (currently "0"). The `package.json` shows version `9.2.32`. The CI pipeline (`.github/workflows/tests.yaml`) runs extensive functional tests against the S3 API using the AWS SDK.
- **Gap**: No breaking change detection tooling (e.g., OpenAPI diff, buf breaking) exists in the CI pipeline. No consumer-driven contract tests (Pact) are implemented. The S3 API compatibility is verified through functional tests, but there is no automated mechanism to detect if a code change breaks the S3 API contract. Schema versioning for the access log format is present but informal (`logFormatVersion: "0"`).
- **Compensating Controls**:
  - The extensive functional test suite using the AWS SDK serves as an implicit contract test.
  - S3 protocol compliance provides a stable external contract.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add API contract testing to the CI pipeline — compare current API behavior against a baseline specification. Implement breaking change detection for any Scality-specific API extensions.
- **Evidence**: `schema/server_access_log.schema.json`, `.github/workflows/tests.yaml`, `package.json`

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The application uses structured JSON logging via werelogs (`lib/utilities/logger.js`). Request IDs are generated and propagated through the system (`x-scal-request-uids` header). Server access logs record `req_id` for request correlation. Log fields include service, action, bucketName, objectKey, accountName, and userName.
- **Gap**: No distributed tracing (OpenTelemetry, X-Ray) is implemented. There is no `traceparent` header propagation. While `x-scal-request-uids` provides request correlation within CloudServer, traces do not extend to external backends (AWS S3, Azure, GCP, MongoDB). Agent-initiated requests cannot be traced end-to-end through the storage pipeline.
- **Compensating Controls**:
  - Use `x-scal-request-uids` for request correlation within CloudServer.
  - Correlate agent request IDs with CloudServer access log `req_id` at the log aggregation layer.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement OpenTelemetry instrumentation to enable end-to-end distributed tracing. Propagate trace context to external backend calls (AWS S3, Azure, GCP).
- **Evidence**: `lib/utilities/logger.js`, `lib/utilities/serverAccessLogger.js` (`req_id` field), `lib/server.js` (request ID handling)

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No Terraform, CloudFormation, CDK, Helm, or Kustomize files exist in the repository. The infrastructure is defined through Docker configurations (`Dockerfile`, `DockerfileMem`, `.github/docker/docker-compose.yaml`) and application-level config files (`config.json`, `locationConfig.json`). The CI pipeline builds and pushes Docker images. GitHub pull request templates exist (`.github/PULL_REQUEST_TEMPLATE.md`).
- **Gap**: The API gateway, IAM roles, secrets, and network configurations that would expose CloudServer to agents are not defined as code in this repository. There is no IaC definition, no drift detection, and no automated plan review for infrastructure changes. Infrastructure is configured via environment variables and config files, not IaC.
- **Compensating Controls**:
  - Manage the infrastructure surrounding CloudServer (load balancer, network, IAM) in a separate IaC repository.
  - Use Docker Compose configurations as a minimal infrastructure-as-code definition.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Define CloudServer deployment infrastructure as IaC (Terraform, Helm, or CDK). Include API Gateway/load balancer configuration, IAM roles, network policies, and secrets management.
- **Evidence**: `Dockerfile`, `DockerfileMem`, `.github/docker/docker-compose.yaml`, `config.json`. No `.tf`, `.cfn.yaml`, `cdk.json`, `Chart.yaml`, or `kustomization.yaml` files found.

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: A comprehensive CI/CD pipeline exists (`.github/workflows/tests.yaml`) with lint, unit tests, functional tests (file backend, MongoDB v0/v1, S3C integration, KMIP), and coverage reporting. The pipeline builds Docker images and pushes to GHCR. CodeQL static analysis (`.github/workflows/codeql.yaml`) and dependency review (`.github/workflows/dependency-review.yaml`) are present. Release workflow (`.github/workflows/release.yaml`) builds tagged images.
- **Gap**: No API contract testing (Pact, OpenAPI validation) exists in the CI pipeline. The functional tests validate S3 API behavior using the AWS SDK, but there is no formal contract test that would detect breaking changes before production. No OpenAPI spec validation step exists because no OpenAPI spec exists.
- **Compensating Controls**:
  - The extensive functional test suite (ft_awssdk, ft_s3cmd, ft_s3curl, ft_node) provides implicit API contract validation.
  - CodeQL and dependency review add security verification.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add formal API contract testing. Generate an OpenAPI specification and validate it in CI. Add breaking change detection by diffing API specs between commits.
- **Evidence**: `.github/workflows/tests.yaml`, `.github/workflows/codeql.yaml`, `.github/workflows/dependency-review.yaml`, `.github/workflows/release.yaml`

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The release workflow (`.github/workflows/release.yaml`) builds tagged Docker images and creates GitHub releases with release notes. Docker images are tagged with version numbers (e.g., `ghcr.io/scality/cloudserver:9.2.32`). The CI pipeline builds images tagged with commit SHAs.
- **Gap**: No explicit rollback mechanism is defined. There is no blue/green deployment, no canary release, no CodeDeploy rollback trigger, and no feature flag system. Rolling back to a previous version requires manually changing the image tag in the deployment configuration. The release workflow is manual (workflow_dispatch), which helps prevent accidental releases but does not provide automated rollback.
- **Compensating Controls**:
  - Docker image tags provide point-in-time recovery — deploy a previous image tag to roll back.
  - Version-tagged images (e.g., `9.2.32`) are immutable and available in GHCR.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement automated rollback triggers based on error rate increases after deployment. Add canary deployment support to the release workflow.
- **Evidence**: `.github/workflows/release.yaml`, `Dockerfile`

---

## INFOs — Architecture and Design Inputs

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Write endpoints (PUT object, DELETE object, POST multipart) follow S3 protocol semantics. PUT operations are naturally idempotent (same key + same content = same result). No explicit idempotency key mechanism is implemented beyond S3's inherent PUT idempotency.
- **Implication**: If agent scope expands to write-enabled, idempotency for non-PUT operations (POST-based multipart, multi-object delete) should be evaluated as a BLOCKER.
- **Evidence**: `lib/api/objectPut.js`, `lib/api/objectDelete.js`, `lib/api/multiObjectDelete.js`

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: The S3 API uses XML for request/response bodies (standard S3 protocol). Internal routes (healthcheck, metrics) use JSON. Prometheus metrics endpoint returns text format. Error responses use standard S3 XML error format.
- **Implication**: Agents consuming the S3 API must parse XML responses. The AWS SDK handles this automatically, but custom agent tool implementations need XML parsing capability. Consider JSON-based wrapper APIs for agent-specific use cases.
- **Evidence**: `lib/api/bucketGet.js` (XML response generation), `lib/utilities/healthcheckHandler.js` (JSON responses)

### API-Q7: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: Bucket notification configuration is supported (`lib/api/bucketPutNotification.js`, `lib/api/bucketGetNotification.js`). The `config.json` includes `bucketNotificationDestinations` with configurable targets. The system supports notification events for object lifecycle changes.
- **Implication**: Event-driven agent patterns could leverage bucket notifications to react to state changes. This is valuable for proactive agent workflows (e.g., processing newly uploaded objects).
- **Evidence**: `lib/api/bucketPutNotification.js`, `lib/api/bucketGetNotification.js`, `config.json` (`bucketNotificationDestinations`)

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: A comprehensive rate limiting system exists (`lib/api/apiUtils/rateLimit/`) with token bucket algorithm, per-bucket configuration, global defaults, Redis-backed token distribution, and cache-based fast path. Rate limiting is configurable via environment variables (`RATE_LIMIT_SERVICE_USER_ARN`, `RATE_LIMIT_NODES`). Rate limiting events are logged in server access logs (`rateLimited`, `rateLimitSource` fields).
- **Implication**: The rate limiting infrastructure is robust, but standard HTTP headers (`X-RateLimit-Remaining`, `Retry-After`) are not returned in API responses. Agents cannot self-throttle based on remaining quota without these headers.
- **Recommendation**: Add standard rate limit headers to HTTP responses so agents can self-throttle proactively.
- **Evidence**: `lib/api/apiUtils/rateLimit/helpers.js`, `lib/api/apiUtils/rateLimit/tokenBucket.js`, `config.json`, `docker-entrypoint.sh` (rate limit env vars)

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Rate limiting is per-bucket with configurable limits. Quota enforcement exists for storage capacity. No per-agent transaction limits (max records per run, max operations per session) are implemented.
- **Implication**: If agent scope expands to write-enabled, per-agent transaction limits should be implemented to bound the blast radius of agent errors.
- **Evidence**: `lib/api/apiUtils/rateLimit/helpers.js`, `lib/api/apiUtils/quotas/`

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality scores, completeness metrics, or data profiling are implemented. The monitoring dashboard (`monitoring/dashboard.json`) tracks infrastructure metrics (request counts, latency, error rates, disk usage) but not data quality metrics.
- **Implication**: Agents acting on data stored in CloudServer have no signal about data completeness or quality. This should be addressed at the data pipeline level, not necessarily in the storage server.
- **Evidence**: `monitoring/dashboard.json`, `lib/utilities/monitoringHandler.js`

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: The S3 API uses well-established, semantically meaningful field names (e.g., `BucketName`, `ObjectKey`, `LastModified`, `ContentType`, `ETag`, `StorageClass`). The server access log schema uses descriptive field names (`requester`, `operation`, `objectSize`, `totalTime`, `turnAroundTime`). Internal code uses clear naming conventions.
- **Implication**: Field names are agent-friendly and require no data dictionary for interpretation. The S3 protocol's widespread adoption means LLMs have extensive training data on these field semantics.
- **Evidence**: `schema/server_access_log.schema.json`, `lib/api/bucketGet.js` (XML field names)

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: The application has documentation (`docs/` directory with ARCHITECTURE.rst, GETTING_STARTED.rst, CLIENTS.rst, INTEGRATIONS.rst, BUCKET_POLICIES.md). No formal data catalog (AWS Glue, Collibra, DataHub) or metadata layer exists. The S3 API itself serves as a self-describing metadata layer (ListBuckets, ListObjects, HeadObject).
- **Implication**: Agent tool builders can use the S3 API's intrinsic discoverability (listing, head requests) to understand what data exists. A formal data catalog would accelerate multi-service agent workflows.
- **Evidence**: `docs/` directory, `lib/api/serviceGet.js` (ListBuckets), `lib/api/bucketGet.js` (ListObjects)

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: Prometheus metrics (`lib/utilities/monitoringHandler.js`) include operational metrics: `s3_cloudserver_http_requests_total`, `s3_cloudserver_http_request_duration_seconds`, `s3_cloudserver_buckets_count`, `s3_cloudserver_objects_count`, `s3_cloudserver_disk_*_bytes`, and quota-related metrics. The Grafana dashboard (`monitoring/dashboard.json`, 3630 lines) provides comprehensive operational visualization.
- **Implication**: Business outcome metrics (e.g., successful agent interactions, data retrieval latency per agent, agent-specific error rates) are not yet defined. When agents start consuming CloudServer, add agent-specific metric labels to track agent-driven traffic patterns.
- **Evidence**: `lib/utilities/monitoringHandler.js`, `monitoring/dashboard.json`, `monitoring/alerts.yaml`

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: BLOCKER (evaluated — no gap)
- **Finding**: CloudServer implements the full S3 REST API with 70+ route handlers in `lib/api/api.js`, covering bucket operations (PUT, GET, DELETE, HEAD), object operations (PUT, GET, DELETE, HEAD, COPY), multipart uploads, ACLs, bucket policies, versioning, lifecycle, encryption, object lock, tagging, notifications, and more. Routes are handled by arsenal's S3 route library (`arsenal.s3routes.routes`). No direct database access is exposed to clients.
- **Gap**: None — the application exposes a comprehensive, well-known REST API (S3 protocol).
- **Recommendation**: N/A
- **Evidence**: `lib/api/api.js`, `lib/server.js`, `lib/routes/` directory

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, GraphQL, or Smithy specification file exists in the repository. The S3 API is well-documented externally but no machine-readable spec is bundled.
- **Gap**: Agent tool generation requires manual authoring or external AWS S3 specification reference. Scality-specific extensions are undocumented in machine-readable format.
- **Recommendation**: Generate an OpenAPI specification for the CloudServer API.
- **Evidence**: No `openapi.*`, `swagger.*`, `asyncapi.*`, or `*.graphql` files found.

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY (evaluated — no gap)
- **Finding**: The application uses arsenal's error system which provides structured S3-compatible XML error responses with error code, message, and HTTP status code. Error codes follow the S3 standard (e.g., `AccessDenied`, `NoSuchBucket`, `InvalidArgument`, `InternalError`). Custom error descriptions are supported (`error.customizeDescription()`).
- **Gap**: None — error responses follow the S3 XML error format with structured error codes, messages, and HTTP status codes.
- **Recommendation**: N/A
- **Evidence**: `lib/api/api.js` (error handling), `lib/api/apiUtils/authorization/permissionChecks.js` (error instances)

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: S3 PUT operations are naturally idempotent. No explicit idempotency key mechanism for POST operations.
- **Gap**: Informational only for read-only scope.
- **Recommendation**: Evaluate idempotency for POST operations if write scope is added.
- **Evidence**: `lib/api/objectPut.js`, `lib/api/completeMultipartUpload.js`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: S3 API uses XML for responses. Internal endpoints use JSON. Prometheus metrics use text format.
- **Gap**: Informational — XML requires parsing capability in agent tools.
- **Recommendation**: Consider JSON wrapper APIs for agent-specific use cases.
- **Evidence**: `lib/api/bucketGet.js`, `lib/utilities/healthcheckHandler.js`

#### API-Q6: Asynchronous Operation Support
- **Severity**: RISK-QUALITY
- **Finding**: Multipart uploads and object restore are long-running operations. Multipart follows S3 async pattern. Object restore relies on polling object metadata.
- **Gap**: No generic job submission/polling pattern for long-running operations.
- **Recommendation**: Document async patterns for agent consumption.
- **Evidence**: `lib/api/initiateMultipartUpload.js`, `lib/api/objectRestore.js`

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: Bucket notification configuration supported with configurable destinations.
- **Gap**: Informational — event emission exists and can be leveraged.
- **Recommendation**: Evaluate bucket notifications for proactive agent patterns.
- **Evidence**: `lib/api/bucketPutNotification.js`, `config.json`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: Comprehensive rate limiting system exists but standard HTTP rate limit headers are not returned.
- **Gap**: Informational — agents cannot self-throttle without rate limit headers.
- **Recommendation**: Add `X-RateLimit-Remaining` and `Retry-After` headers.
- **Evidence**: `lib/api/apiUtils/rateLimit/helpers.js`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER (evaluated — no gap)
- **Finding**: CloudServer supports machine identity authentication via AWS Signature V4 with API access key/secret key pairs. Three auth backends are supported: in-memory (static credentials from `conf/authdata.json`), external Vault service (vaultclient), and ChainBackend (both). Service accounts are identified via canonical ID patterns (`lib/api/apiUtils/authorization/permissionChecks.js`). The authenticated principal is attributed in server access logs (`requester`, `awsAccessKeyID`, `accountName`, `userName` fields).
- **Gap**: None — machine identity authentication with principal attribution is supported.
- **Recommendation**: N/A
- **Evidence**: `lib/auth/vault.js`, `conf/authdata.json`, `lib/utilities/serverAccessLogger.js`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY (evaluated — no gap)
- **Finding**: The authorization model supports scoped permissions through IAM-style policy evaluation via arsenal's policies module. The `prepareRequestContexts.js` generates action-specific request contexts (e.g., `objectGet`, `objectPut`, `objectDelete`, `objectGetTagging`). Bucket policies support principal-specific, action-specific, resource-specific, and condition-based access control. Service accounts have properties-based permission scoping.
- **Gap**: None — scoped permissions are supported through the IAM-compatible policy model.
- **Recommendation**: N/A
- **Evidence**: `lib/api/apiUtils/authorization/prepareRequestContexts.js`, `lib/api/apiUtils/authorization/permissionChecks.js`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY (evaluated — no gap)
- **Finding**: Action-level authorization is enforced. The `prepareRequestContexts.js` generates separate request contexts for each S3 action (e.g., `objectGet` vs `objectDelete` vs `objectPutTagging`). Bucket policies evaluate `checkBucketPolicy()` per action with Allow/Deny/Default-Deny logic. ACL checks (`checkBucketAcls`, `checkObjectAcls`) differentiate between read, write, and ACL operations. Cross-account access control distinguishes between same-account and cross-account requests.
- **Gap**: None — the system can enforce action-level authorization allowing an agent to read but not delete.
- **Recommendation**: N/A
- **Evidence**: `lib/api/apiUtils/authorization/prepareRequestContexts.js`, `lib/api/apiUtils/authorization/permissionChecks.js`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: RISK-QUALITY
- **Finding**: Supports assumed roles and IAM users but no on-behalf-of flows.
- **Gap**: No delegation mechanism for agents acting on behalf of users.
- **Recommendation**: Implement assumed role support for agent delegation if write scope is planned.
- **Evidence**: `lib/auth/vault.js`, `lib/api/apiUtils/authorization/permissionChecks.js`

#### AUTH-Q5: Credential Management
- **Severity**: RISK-QUALITY
- **Finding**: Sample credentials in `authdata.json`, placeholder KMS keys in `config.json`. Docker secrets support exists.
- **Gap**: No secrets manager integration (AWS Secrets Manager, HashiCorp Vault) for runtime rotation.
- **Recommendation**: Remove sample credentials; add secrets management integration.
- **Evidence**: `conf/authdata.json`, `config.json`, `docker-entrypoint.sh`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Comprehensive server access logs exist but lack immutability guarantees.
- **Gap**: Logs written to local file without tamper-evidence.
- **Recommendation**: Ship logs to immutable storage.
- **Evidence**: `lib/utilities/serverAccessLogger.js`, `schema/server_access_log.schema.json`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: In-memory backend lacks runtime key revocation API. External Vault service likely supports this.
- **Gap**: No instant agent identity suspension for in-memory auth backend.
- **Recommendation**: Use external Vault service for agent identities.
- **Evidence**: `lib/auth/vault.js`, `lib/auth/in_memory/backend.js`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Multipart upload abort exists. No general saga/rollback framework.
- **Gap**: Limited compensation patterns.
- **Recommendation**: Enable versioning on agent-accessible buckets.
- **Evidence**: `lib/api/multipartDelete.js`, `lib/api/bucketPutVersioning.js`

#### STATE-Q2: Queryable Current State
- **Severity**: RISK-QUALITY (evaluated — no gap)
- **Finding**: Full GET/HEAD endpoints for all resources (objectGet, objectHead, bucketGet, bucketHead, serviceGet). Status can be queried before taking action.
- **Gap**: None — comprehensive queryable state.
- **Recommendation**: N/A
- **Evidence**: `lib/api/objectHead.js`, `lib/api/bucketHead.js`, `lib/api/objectGet.js`

#### STATE-Q3: Concurrency Controls
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled AND service has persistent state
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: External backends configured but no circuit breakers present.
- **Gap**: No failure isolation for external backend calls.
- **Recommendation**: Implement circuit breakers for external backends.
- **Evidence**: `lib/data/wrapper.js`, `config.json`, `lib/utilities/healthcheckHandler.js`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY (evaluated — no gap)
- **Finding**: Comprehensive rate limiting with token bucket algorithm (`lib/api/apiUtils/rateLimit/`), per-bucket and global configuration, Redis-backed token distribution, cache-based fast path in `api.js`. Rate limiting is configurable via environment variables and applied before API processing.
- **Gap**: None — rate limiting is enforced at the API layer.
- **Recommendation**: N/A
- **Evidence**: `lib/api/apiUtils/rateLimit/helpers.js`, `lib/api/api.js`, `docker-entrypoint.sh`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No per-agent transaction limits implemented.
- **Gap**: Informational for read-only scope.
- **Recommendation**: Implement if write scope is added.
- **Evidence**: `lib/api/apiUtils/rateLimit/helpers.js`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q2: Configurable Approval Gates
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY (evaluated — no gap)
- **Finding**: Multiple testing configurations are available: `DockerfileMem` provides an in-memory backend for testing, `S3BACKEND=mem` environment variable enables in-memory mode, `.github/docker/docker-compose.yaml` provides a full testing environment with Redis, MongoDB, PyKMIP, and sproxyd. Extensive functional test suites exist (`tests/functional/`) covering aws-node-sdk, s3cmd, s3curl, raw-node, healthchecks, backbeat, KMIP, SSE migration, and more. Unit tests cover API, auth, encryption, healthchecks, routes, metadata, and quotas.
- **Gap**: None — comprehensive sandbox/testing infrastructure exists.
- **Recommendation**: N/A
- **Evidence**: `DockerfileMem`, `.github/docker/docker-compose.yaml`, `tests/` directory

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: KMS encryption exists but no field-level data classification.
- **Gap**: No data classification system.
- **Recommendation**: Implement object tagging for data classification.
- **Evidence**: `lib/kms/wrapper.js`, `lib/api/bucketPutEncryption.js`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Location constraints exist but no residency enforcement.
- **Gap**: No controls preventing cross-region data access by agents.
- **Recommendation**: Implement residency-aware agent tool design.
- **Evidence**: `locationConfig.json`, `config.json`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK-QUALITY (evaluated — no gap)
- **Finding**: S3 ListObjects supports pagination (`max-keys`, `marker`/`continuation-token`), prefix filtering, and delimiter-based hierarchical listing. ListMultipartUploads and ListParts also support pagination. The `bucketGet.js` implementation handles both V1 and V2 listing protocols with `MaxKeys`, `Marker`, `ContinuationToken`, and `StartAfter` parameters.
- **Gap**: None — comprehensive pagination and filtering support.
- **Recommendation**: N/A
- **Evidence**: `lib/api/bucketGet.js`, `lib/api/listMultipartUploads.js`, `lib/api/listParts.js`

#### DATA-Q4: System of Record Designations
- **Severity**: RISK-QUALITY
- **Finding**: No SoR designations for replicated data.
- **Gap**: No golden record or conflict resolution strategy.
- **Recommendation**: Document authoritative storage backend per location.
- **Evidence**: `config.json`, `locationConfig.json`

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK-QUALITY (evaluated — no gap)
- **Finding**: S3 objects include `Last-Modified` timestamps in responses. Object metadata includes creation and modification timestamps. The server access log records precise timestamps (`startTime` as DateTime64(3)). ETags provide content-based versioning.
- **Gap**: None — temporal metadata is present and standardized.
- **Recommendation**: N/A
- **Evidence**: `lib/api/bucketGet.js` (LastModified in XML), `schema/server_access_log.schema.json` (startTime)

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: No PII redaction in server access logs.
- **Gap**: Access keys, IPs, object keys logged verbatim.
- **Recommendation**: Add PII masking to log entries.
- **Evidence**: `lib/utilities/serverAccessLogger.js`, `schema/server_access_log.schema.json`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics or profiling.
- **Gap**: Informational — address at data pipeline level.
- **Recommendation**: Consider data quality metrics for storage monitoring.
- **Evidence**: `monitoring/dashboard.json`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: S3 protocol provides external versioning. No breaking change detection in CI.
- **Gap**: No formal schema versioning or API contract testing.
- **Recommendation**: Add API contract testing to CI.
- **Evidence**: `schema/server_access_log.schema.json`, `.github/workflows/tests.yaml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: S3 API uses well-established, semantically meaningful field names.
- **Gap**: Informational — field names are agent-friendly.
- **Recommendation**: N/A
- **Evidence**: `schema/server_access_log.schema.json`, `lib/api/bucketGet.js`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: Documentation exists. S3 API provides self-describing metadata layer.
- **Gap**: Informational — no formal data catalog.
- **Recommendation**: Consider data catalog for multi-service agent workflows.
- **Evidence**: `docs/` directory

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: Structured JSON logging with request IDs but no distributed tracing.
- **Gap**: No OpenTelemetry/X-Ray instrumentation.
- **Recommendation**: Implement OpenTelemetry for end-to-end tracing.
- **Evidence**: `lib/utilities/logger.js`, `lib/utilities/serverAccessLogger.js`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY (evaluated — no gap)
- **Finding**: Comprehensive Prometheus alerting rules in `monitoring/alerts.yaml` with: `DataAccessS3EndpointDegraded`/`Critical` (endpoint availability), `SystemErrorsWarning`/`Critical` (5xx error rate thresholds at 3%/5%), `ListingLatencyWarning`/`Critical` (300ms/500ms), `DeleteLatencyWarning`/`Critical` (500ms/1s), `QuotaMetricsNotAvailable` (warning/critical).
- **Gap**: None — alerting thresholds are configured for error rates and latency.
- **Recommendation**: N/A
- **Evidence**: `monitoring/alerts.yaml`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: Infrastructure metrics present. No business outcome metrics.
- **Gap**: Informational — add agent-specific metrics when agents are deployed.
- **Recommendation**: Add agent traffic labels to Prometheus metrics.
- **Evidence**: `lib/utilities/monitoringHandler.js`, `monitoring/dashboard.json`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK-QUALITY
- **Finding**: No IaC in repository. Docker configurations serve as minimal infrastructure definition.
- **Gap**: No IaC, drift detection, or automated plan review.
- **Recommendation**: Define deployment infrastructure as IaC.
- **Evidence**: `Dockerfile`, `.github/docker/docker-compose.yaml`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive CI/CD exists. No formal API contract testing.
- **Gap**: No breaking change detection for API contracts.
- **Recommendation**: Add OpenAPI validation and contract testing.
- **Evidence**: `.github/workflows/tests.yaml`, `.github/workflows/release.yaml`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: Docker image tags enable manual rollback. No automated rollback.
- **Gap**: No automated rollback mechanism.
- **Recommendation**: Add canary deployment with automated rollback.
- **Evidence**: `.github/workflows/release.yaml`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY (evaluated — no gap)
- **Finding**: Extensive test suites: unit tests (`tests/unit/`) covering API, auth, encryption, healthchecks, routes, metadata, quotas; functional tests (`tests/functional/`) with AWS SDK tests, s3cmd tests, s3curl tests, raw-node tests, healthcheck tests, backbeat tests, KMIP tests, SSE migration tests. Coverage reporting via nyc/istanbul with Codecov integration. Tests run in CI on every push.
- **Gap**: None — comprehensive API test coverage running in CI.
- **Recommendation**: N/A
- **Evidence**: `tests/unit/`, `tests/functional/`, `.github/workflows/tests.yaml`, `.nycrc`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: RISK-QUALITY (evaluated — no gap)
- **Finding**: Comprehensive KMS integration (`lib/kms/wrapper.js`) supporting multiple backends: in-memory, file-based, AWS KMS (`kmsAWS`), KMIP, and Scality KMS. Server-side encryption supports SSE-S3 (AES-256) and SSE-KMS. Bucket-level default encryption configuration is supported (`lib/api/bucketPutEncryption.js`). Per-account default encryption keys are supported (`config.json` `defaultEncryptionKeyPerAccount: true`). The KMS wrapper handles cipher/decipher bundle creation with data key management.
- **Gap**: None — encryption at rest is supported through multiple KMS backends.
- **Recommendation**: N/A
- **Evidence**: `lib/kms/wrapper.js`, `lib/api/bucketPutEncryption.js`, `config.json`

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `lib/api/api.js` | API-Q1, API-Q3, API-Q4, STATE-Q5 |
| `lib/api/bucketGet.js` | API-Q5, DATA-Q3, DATA-Q5, DISC-Q2 |
| `lib/api/objectPut.js` | API-Q4 |
| `lib/api/objectGet.js` | STATE-Q2 |
| `lib/api/objectHead.js` | STATE-Q2 |
| `lib/api/bucketHead.js` | STATE-Q2 |
| `lib/api/objectDelete.js` | API-Q4 |
| `lib/api/multiObjectDelete.js` | API-Q4 |
| `lib/api/multipartDelete.js` | STATE-Q1 |
| `lib/api/initiateMultipartUpload.js` | API-Q6 |
| `lib/api/completeMultipartUpload.js` | API-Q6 |
| `lib/api/objectRestore.js` | API-Q6 |
| `lib/api/bucketPutNotification.js` | API-Q7 |
| `lib/api/bucketGetNotification.js` | API-Q7 |
| `lib/api/bucketPutVersioning.js` | STATE-Q1 |
| `lib/api/bucketPutEncryption.js` | DATA-Q1, ENG-Q5 |
| `lib/api/listMultipartUploads.js` | DATA-Q3 |
| `lib/api/listParts.js` | DATA-Q3 |
| `lib/api/objectPutRetention.js` | STATE-Q1 |
| `lib/api/serviceGet.js` | DISC-Q3 |
| `lib/api/apiUtils/authorization/prepareRequestContexts.js` | AUTH-Q2, AUTH-Q3 |
| `lib/api/apiUtils/authorization/permissionChecks.js` | AUTH-Q2, AUTH-Q3, AUTH-Q4 |
| `lib/api/apiUtils/rateLimit/helpers.js` | API-Q8, STATE-Q5, STATE-Q6 |
| `lib/api/apiUtils/rateLimit/tokenBucket.js` | STATE-Q5 |
| `lib/auth/vault.js` | AUTH-Q1, AUTH-Q4, AUTH-Q7 |
| `lib/auth/in_memory/backend.js` | AUTH-Q7 |
| `lib/data/wrapper.js` | STATE-Q4 |
| `lib/kms/wrapper.js` | DATA-Q1, ENG-Q5 |
| `lib/utilities/serverAccessLogger.js` | AUTH-Q1, AUTH-Q6, DATA-Q6, OBS-Q1 |
| `lib/utilities/logger.js` | DATA-Q6, OBS-Q1 |
| `lib/utilities/healthcheckHandler.js` | API-Q5, STATE-Q4 |
| `lib/utilities/monitoringHandler.js` | OBS-Q2, OBS-Q3 |
| `lib/server.js` | API-Q1, AUTH-Q4, OBS-Q1 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `Dockerfile` | ENG-Q1, ENG-Q3, HITL-Q3 |
| `DockerfileMem` | HITL-Q3 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/tests.yaml` | DISC-Q1, ENG-Q2, ENG-Q4 |
| `.github/workflows/release.yaml` | ENG-Q2, ENG-Q3 |
| `.github/workflows/codeql.yaml` | ENG-Q2 |
| `.github/workflows/dependency-review.yaml` | ENG-Q2 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `config.json` | AUTH-Q5, API-Q7, API-Q8, STATE-Q4, STATE-Q5, DATA-Q2, DATA-Q4, ENG-Q5 |
| `locationConfig.json` | DATA-Q2, DATA-Q4 |
| `conf/authdata.json` | AUTH-Q1, AUTH-Q5, AUTH-Q7 |
| `docker-entrypoint.sh` | AUTH-Q5, STATE-Q5 |
| `.github/docker/docker-compose.yaml` | HITL-Q3, ENG-Q1 |

### Schemas and Documentation
| File | Questions Referenced |
|------|---------------------|
| `schema/server_access_log.schema.json` | AUTH-Q6, DATA-Q5, DATA-Q6, DISC-Q1, DISC-Q2 |
| `monitoring/alerts.yaml` | OBS-Q2 |
| `monitoring/dashboard.json` | DATA-Q7, OBS-Q3 |
| `docs/` | DISC-Q3 |
| `.nycrc` | ENG-Q4 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `package.json` | Multiple (technology stack identification) |
