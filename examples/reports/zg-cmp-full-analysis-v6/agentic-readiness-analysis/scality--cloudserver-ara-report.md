# Agentic Readiness Analysis Report

**Target**: /Users/lucasdu/Documents/AWS-MAC/2026-projects/sample-agentic-readiness-analysis/services/scality--cloudserver
**Date**: 2025-01-08
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**TD Version**: agentic-readiness-analysis
**Repository Type**: application
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: javascript, storage, s3
**Context**: Scality open-source S3-compatible object-storage server.

**Archetype Justification**: The application owns persistent state (MongoDB for metadata, multiple data backends for objects), exposes full CRUD operations on S3 objects/buckets, and manages per-user data with entity lifecycle (versioning, lifecycle policies, object lock).

**Surface flags**:
- has_persistent_data_store: true
- has_http_rpc_surface: true
- has_auth_surface: true
- has_write_operations: true
- has_logging_of_user_data: true

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 1 | **RISK-SAFETY**: 9 | **RISK-QUALITY**: 9 | **INFOs**: 14

**Classification Rationale**: This repo has 1 High finding (AUTH-Q1 BLOCKER for no machine-identity authentication with principal attribution), 9 Medium safety-impact findings (RISK-SAFETY), and 9 Medium non-safety findings (RISK-QUALITY). The matched rule is "1-2 High → Remediation Required." The V6 unified classification maps 1 BLOCKER → 1 High, placing the repo in the Remediation Required tier.

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 1 |
| RISK-SAFETY | 9 |
| RISK-QUALITY | 9 |
| INFO | 14 |
| PASS | 1 |
| N/A | 0 |
| Not Evaluated (extended) | 9 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 10
**Extended Questions Not Triggered**: 9
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: stateful-crud (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: The application authenticates via AWS Signature V2/V4 validated against either an in-memory credential store (`conf/authdata.json`) or an external Vault service. However, there is no support for service account or machine identity authentication with principal attribution (no OAuth2 client credentials flow, no mTLS, no API key scheme with per-agent identity tracking). The in-memory backend uses static access key/secret key pairs with no agent-specific identity. The Vault backend delegates identity to an external service but the CloudServer itself has no mechanism to attribute requests to specific agent identities in audit logs.
- **Gap**: No machine identity authentication mechanism exists that can distinguish which agent made a call. The system authenticates S3 access keys but has no concept of machine/agent identity attribution beyond the access key itself.
- **Remediation**:
  - **Immediate**: Create dedicated IAM-style accounts per agent in the Vault backend with distinct access keys. Ensure the server access log (which already records `requester` and `awsAccessKeyID`) is enabled by default so agent actions are attributable.
  - **Target State**: Each agent has a unique identity with its own access key, and all operations are attributed to that identity in immutable audit logs.
  - **Estimated Effort**: Medium
  - **Dependencies**: AUTH-Q6 (audit logging must be enabled to make attribution meaningful)
- **Evidence**: `lib/auth/vault.js`, `conf/authdata.json`, `lib/utilities/serverAccessLogger.js`

---

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The authorization model supports bucket policies with condition keys, ACLs, and IAM-style policies. However, the system relies on an external Vault service for IAM policy evaluation, and the code contains a `TODO: Add IAM checks` comment in `permissionChecks.js` suggesting incomplete IAM integration. Service users bypass authorization checks entirely (`lib/api/apiUtils/authorization/serviceUser.js`).
- **Gap**: IAM-level scoped permissions may be incomplete per the TODO comment. Service user bypass means any identity designated as a service user gets full access with no permission scoping.
- **Compensating Controls**:
  - Use bucket policies to restrict agent access to specific buckets and operations
  - Create agent-specific S3 access keys in Vault with scoped IAM policies at the Vault layer
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Complete IAM integration per the TODO, and ensure agent identities are never classified as service users.
- **Evidence**: `lib/api/apiUtils/authorization/permissionChecks.js`, `lib/api/apiUtils/authorization/serviceUser.js`

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The bucket policy engine supports action-level conditions (e.g., `s3:GetObject` vs `s3:DeleteObject`). ACLs provide coarser-grained READ/WRITE/FULL_CONTROL. The system can enforce action-level authorization through bucket policies, but the completeness depends on the external Vault IAM evaluation (which has a TODO for full IAM checks).
- **Gap**: Action-level authorization is available through bucket policies but IAM-level action enforcement may be incomplete per the noted TODO.
- **Compensating Controls**:
  - Deploy bucket policies on every bucket that agent identities access, explicitly listing allowed actions
  - Use Vault IAM policies to restrict agent accounts to specific S3 actions
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Ensure bucket policies are applied to all agent-accessible buckets with explicit action-level allow/deny.
- **Evidence**: `lib/api/apiUtils/authorization/permissionChecks.js`, `lib/api/bucketPutPolicy.js`

#### AUTH-Q6: Immutable Audit Logging — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The server access logger (`lib/utilities/serverAccessLogger.js`) implements comprehensive S3-compatible access logging with requester identity, operation, timing, and error details in JSON format. However: (1) logging is disabled by default in `config.json`, (2) logs are written to local files with no immutability guarantee, (3) there is no CloudTrail equivalent or tamper-evident storage, and (4) logs can be dropped under backpressure.
- **Gap**: Audit logging exists but is not immutable — file-based logs can be modified or deleted. No tamper-evident storage. Logging disabled by default.
- **Compensating Controls**:
  - Enable server access logging in configuration and ship logs to an immutable store (S3 with Object Lock, CloudWatch Logs with retention policies)
  - Configure log streaming to a SIEM for real-time monitoring
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Enable server access logging by default and forward logs to an immutable, append-only store external to the server.
- **Evidence**: `lib/utilities/serverAccessLogger.js`, `config.json`

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: There is no built-in mechanism to suspend or revoke individual agent identities without restarting the server. The in-memory backend requires editing `conf/authdata.json` and restarting. The Vault backend delegates identity management to an external service — suspension depends on Vault's capabilities, which are outside this repository's control.
- **Gap**: No immediate identity suspension mechanism within the application. Requires external Vault operations or server restart for in-memory mode.
- **Compensating Controls**:
  - Use the Vault backend where accounts can be disabled externally without CloudServer restart
  - Implement a deny-list at the rate-limiting layer to block specific access keys
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement a hot-reloadable deny-list for access keys that can be updated without server restart.
- **Evidence**: `lib/auth/vault.js`, `conf/authdata.json`, `lib/auth/in_memory/backend.js`

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The application makes calls to multiple external dependencies (MongoDB, Redis, Vault, KMIP, cloud storage backends). No circuit breaker pattern is implemented. The rate limiter fails open when Redis is unavailable (grants tokens regardless). No retry with exponential backoff is implemented for backend failures. No timeout configuration on external calls beyond Node.js defaults.
- **Gap**: No circuit breakers, no retry logic with backoff, no configurable timeouts on external dependency calls. Rate limiter fails open.
- **Compensating Controls**:
  - Deploy a service mesh (e.g., Istio) in front of CloudServer with circuit breaker and retry policies
  - Set `requestTimeout` to a non-zero value in configuration
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement circuit breaker patterns for MongoDB, Redis, and Vault clients. Add configurable timeouts to all external calls.
- **Evidence**: `lib/auth/vault.js`, `lib/api/apiUtils/rateLimit/tokenBucket.js`, `lib/server.js`

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The application implements a sophisticated Redis-backed token bucket rate limiter with GCRA algorithm (`lib/api/apiUtils/rateLimit/`). However: (1) rate limiting is per-S3-bucket only, not per-user/per-agent, (2) it is disabled by default in `config.json`, (3) the rate limiter fails open when Redis is unavailable, and (4) service user ARNs are exempt from rate limiting.
- **Gap**: Rate limiting exists but is per-bucket only (not per-agent identity), disabled by default, and fails open. A runaway agent with service user status would bypass all rate limits.
- **Compensating Controls**:
  - Enable rate limiting in configuration and set conservative per-bucket limits
  - Deploy an API gateway or reverse proxy in front of CloudServer with per-identity rate limiting
  - Ensure agent identities are never given service user ARN status
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Enable rate limiting by default, add per-access-key rate limiting, and ensure the fail-open behavior logs an alert.
- **Evidence**: `lib/api/apiUtils/rateLimit/tokenBucket.js`, `lib/api/apiUtils/rateLimit/config.js`, `config.json`

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The server access logger records `clientIP`, `awsAccessKeyID`, `userAgent`, `requester` (canonical ID or IAM user name), `objectKey` (which may contain PII in key names), and `requestURI` (which includes the full URL with query parameters). No PII redaction or masking is applied before writing to the log file. The `werelogs` structured logger may also emit request context in error scenarios.
- **Gap**: No PII redaction in access logs. Object keys, access key IDs, and IP addresses are logged in full. If S3 objects are named with PII (e.g., `users/john.doe@email.com/profile.json`), that PII appears in logs unredacted.
- **Compensating Controls**:
  - Implement a log scrubbing layer before forwarding logs to external systems
  - Enforce naming conventions that prevent PII in object keys
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a configurable PII redaction filter to the server access logger that masks access keys, IP octets, and detects common PII patterns in object key names.
- **Evidence**: `lib/utilities/serverAccessLogger.js`

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, GraphQL schema, or Smithy specification exists in the repository. The API implements the AWS S3 protocol implicitly through code in `lib/api/` with ~60+ handlers. The only schema files are JSON schemas for access log format and Veeam route validation.
- **Gap**: No machine-readable API specification. Agent tool generation would require manual definition based on AWS S3 API documentation or code inspection.
- **Compensating Controls**:
  - Use the official AWS S3 API model (available as a Smithy model) as the machine-readable spec since this server implements the S3 protocol
  - Generate an OpenAPI spec from the route definitions in `lib/api/api.js`
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Either reference the AWS S3 OpenAPI spec (since this is protocol-compatible) or generate one from the route handlers.
- **Evidence**: `lib/api/api.js`, `schema/server_access_log.schema.json`

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Error responses use Arsenal's pre-defined S3-compatible error objects which include an error code (e.g., `AccessDenied`, `NoSuchBucket`, `SlowDown`), HTTP status code, and XML-formatted error body matching the AWS S3 error response format. This is a well-structured error system. However, there is no explicit `retryable` boolean — agents must infer retryability from the HTTP status code (429, 503 = retry; 400, 403, 404 = do not retry).
- **Gap**: No explicit retryable indicator in error responses. Agents must map error codes to retry decisions using S3 protocol conventions.
- **Compensating Controls**:
  - Document the retry semantics per error code for agent tool definitions
  - S3 SDKs already implement retry logic for known error codes — leverage this
- **Remediation Timeline**: 30–60 days
- **Recommendation**: The S3 protocol's well-established error code taxonomy is largely sufficient. Document which codes are retryable in the agent tool definition layer.
- **Evidence**: `lib/api/apiUtils/rateLimit/tokenBucket.js` (SlowDown error), Arsenal errors (external dependency)

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Structured logging is implemented via `werelogs` library. Prometheus metrics capture HTTP request counts, duration histograms, and custom gauges. However, there is no distributed tracing (no OpenTelemetry, no X-Ray, no `traceparent` header propagation). The server generates a `requestID` per request that appears in access logs, but this is not propagated to downstream calls (MongoDB, Redis, Vault, cloud backends).
- **Gap**: No distributed tracing. Cannot trace an agent-initiated request through the CloudServer to its backend dependencies (MongoDB, Redis, Vault, cloud storage).
- **Compensating Controls**:
  - Use the `requestID` from server access logs to correlate requests at the CloudServer level
  - Add OpenTelemetry instrumentation to trace requests through backend calls
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add OpenTelemetry SDK instrumentation with trace context propagation to MongoDB, Redis, and Vault clients.
- **Evidence**: `lib/utilities/logger.js`, `lib/utilities/monitoringHandler.js`, `lib/utilities/serverAccessLogger.js`

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Prometheus alerting rules exist in `monitoring/alerts.yaml` covering: endpoint degraded/critical (5xx rate >3%/>5%), listing latency (>300ms/>500ms), delete latency (>500ms/>1s), quota availability, and system errors. These are well-defined operational alerts.
- **Gap**: Alerts exist but are defined as Prometheus rules — they require an external AlertManager deployment to fire. No alerting infrastructure is defined in this repository (no PagerDuty/OpsGenie integration, no CloudWatch alarms). No alerts specifically for authentication failures or rate limit exhaustion.
- **Compensating Controls**:
  - Deploy Prometheus AlertManager alongside CloudServer and route alerts to an on-call system
  - Add auth failure rate alerts and rate limit exhaustion alerts
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Deploy AlertManager with the existing rules and add auth-specific anomaly alerts.
- **Evidence**: `monitoring/alerts.yaml`

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The API implements the AWS S3 protocol which has its own versioning (S3 API versions). The repository has no explicit schema versioning, no breaking change detection in CI, no consumer-driven contract tests. The CI pipeline (`tests.yaml`) runs comprehensive functional tests against the S3 API but does not validate API contracts against a specification.
- **Gap**: No API contract testing, no breaking change detection, no schema versioning strategy within the repository. Changes to API behavior are validated by functional tests but not against a formal contract.
- **Compensating Controls**:
  - The comprehensive functional test suite (395+ test files) serves as a de facto contract — any S3 API behavior change would fail tests
  - AWS SDK compatibility tests provide implicit contract validation
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add OpenAPI spec generation and diff checking in CI to detect breaking changes before merge.
- **Evidence**: `.github/workflows/tests.yaml`, `tests/functional/`

#### ENG-Q1: Infrastructure Governance — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No Infrastructure as Code exists in this repository. No Terraform, CloudFormation, CDK, Helm charts, or Kustomize files. Deployment is container-based (Dockerfile present) but the infrastructure that runs the container (API gateways, IAM roles, networking, secrets) is not defined as code here.
- **Gap**: No IaC for the deployment infrastructure. The integration surface (network config, secrets, IAM) is not defined declaratively in this repository.
- **Compensating Controls**:
  - IaC may exist in a separate deployment repository (common for open-source projects)
  - Docker Compose in `.github/docker/` provides reproducible local/CI environments
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Create IaC definitions (Terraform/CDK/Helm) for production deployment including networking, secrets management, and IAM configuration.
- **Evidence**: Absence of IaC files. `Dockerfile`, `.github/docker/docker-compose.yaml` exist for containerization only.

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: CI/CD exists via GitHub Actions (`tests.yaml`, `release.yaml`). The test pipeline includes linting, unit tests, functional tests (AWS SDK, multi-backend, KMIP, SSE, etc.), and code coverage. However, there are no API contract tests (no Pact, no OpenAPI validation, no schema diffing). The release workflow pushes Docker images to GHCR but has no API contract validation gate.
- **Gap**: No API contract testing in CI. No breaking change detection for the S3 API surface.
- **Compensating Controls**:
  - Functional tests against the AWS SDK serve as implicit API contract tests
  - CodeQL scanning provides security analysis
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add S3 API compatibility tests against the official AWS S3 test suite or add OpenAPI spec validation in CI.
- **Evidence**: `.github/workflows/tests.yaml`, `.github/workflows/release.yaml`

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The release workflow (`release.yaml`) pushes tagged Docker images to GHCR. There is no blue-green deployment, no canary, no automatic rollback trigger. Rollback would require manually deploying the previous Docker image tag. No deployment orchestration exists in this repository.
- **Gap**: No automated rollback capability. Manual Docker image tag revert is the only option.
- **Compensating Controls**:
  - Docker image tags are immutable — rolling back means deploying the previous tag
  - Implement deployment orchestration externally (Kubernetes rollback, ECS service update)
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Define deployment strategy with automated rollback triggers (health check failures → previous version).
- **Evidence**: `.github/workflows/release.yaml`

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Docker Compose in `.github/docker/docker-compose.yaml` provides a full local testing environment with CloudServer, Redis, MongoDB, Vault, Ceph, KMIP, and squid proxy. The `DockerfileMem` provides an in-memory variant for lightweight testing. Multiple test configurations exist for different backends.
- **Gap**: Local testing environment exists but no production-equivalent staging/sandbox with realistic data shape is defined. Docker Compose is CI-focused, not a staging environment.
- **Compensating Controls**:
  - Use Docker Compose environment as a functional sandbox for agent testing
  - The in-memory backend (`S3BACKEND=mem`) provides a zero-risk testing surface
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Define a staging environment configuration with seed data scripts that provide production-equivalent S3 bucket structures.
- **Evidence**: `.github/docker/docker-compose.yaml`, `DockerfileMem`

---

## INFOs — Architecture and Design Inputs

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: S3 PUT operations are naturally idempotent (PUT to the same key overwrites). No explicit idempotency key support exists for POST operations (InitiateMultipartUpload, CompleteMultipartUpload). Versioned buckets preserve history of all writes.
- **Implication**: If agent scope expands to write-enabled, evaluate whether POST-based operations need idempotency keys.
- **Recommendation**: For write-enabled scope, add idempotency key support for multipart upload initiation.
- **Evidence**: `lib/api/objectPut.js`, `lib/api/completeMultipartUpload.js`

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: Responses are XML-formatted following the AWS S3 protocol specification. Some internal routes (Veeam, health checks) return JSON. Binary data (object content) is streamed directly.
- **Implication**: Agents consuming S3 data will receive XML for management operations and binary for object data. AWS S3 SDKs handle XML parsing transparently.
- **Recommendation**: Agent tool definitions should use AWS S3 SDKs rather than raw HTTP to handle XML/binary response formats.
- **Evidence**: `lib/api/`, `lib/routes/veeam/`

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: The rate limiter returns HTTP 429 with S3-compatible `SlowDown` error code when limits are exceeded. No `X-RateLimit-Remaining` or `Retry-After` headers are returned to clients.
- **Implication**: Agents cannot self-throttle based on remaining quota — they only learn about limits when they hit them.
- **Recommendation**: Add `X-RateLimit-Remaining` and `Retry-After` headers to responses when rate limiting is enabled.
- **Evidence**: `lib/api/apiUtils/rateLimit/tokenBucket.js`

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: INFO
- **Finding**: The system authenticates requests via AWS Signature V4 which identifies the caller. No on-behalf-of flows or token exchange patterns exist. The system does not distinguish between "agent acting as itself" vs "agent acting on behalf of a user" — all requests are attributed to the signing access key. Downgraded to INFO per archetype calibration (stateful-crud with read-only scope evaluates identity propagation as a design input rather than a risk).
- **Implication**: For multi-tenant agent scenarios, each agent must use its own access key. There is no mechanism for an agent to act with a user's permissions without having that user's credentials.
- **Recommendation**: Consider implementing STS-like temporary credential issuance if agents need to act on behalf of specific users.
- **Evidence**: `lib/auth/vault.js`

### AUTH-Q5: Credential Management

- **Severity**: INFO
- **Finding**: The in-memory backend stores credentials in `conf/authdata.json` (plaintext, committed to repo — for development only). The Vault backend delegates credential management to an external service. The management agent generates RSA keypairs stored in the metadata database with 7-day rotation warnings but no auto-rotation. CI secrets are properly managed via GitHub Actions secrets.
- **Implication**: Production deployments using Vault have proper credential management. The in-memory credentials in the repo are development-only but represent a security hygiene concern.
- **Recommendation**: Add `.gitignore` entry for custom `authdata.json` files and document that the committed credentials are for development-only use.
- **Evidence**: `conf/authdata.json`, `lib/management/credentials.js`, `.github/workflows/tests.yaml`

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO (scope-calibrated from RISK-SAFETY)
- **Finding**: No explicit compensation or rollback mechanisms exist. If a multi-step operation (e.g., data write + metadata update) fails partway through, there is no automated recovery. The `async.waterfall` pattern in API handlers does not include compensation steps.
- **Implication**: If agent scope expands to write-enabled, this becomes a significant safety concern for multi-step operations.
- **Recommendation**: For write-enabled scope expansion, implement compensation logic for the data-write → metadata-update sequence.
- **Evidence**: `lib/data/wrapper.js`, `lib/metadata/wrapper.js`

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: S3's natural model handles concurrency through last-writer-wins for non-versioned buckets and version creation for versioned buckets. DynamoDB conditional writes and MongoDB write concern `majority` provide backend-level concurrency safety. No application-level optimistic locking (ETags/If-Match) for S3 operations beyond the S3 protocol's built-in mechanisms.
- **Implication**: For read-only agents, concurrency is not a concern. For write-enabled expansion, S3's last-writer-wins model may cause silent data loss without explicit conditional operations.
- **Recommendation**: For write-enabled scope, implement S3 conditional operations (If-Match/If-None-Match) for critical write paths.
- **Evidence**: `config.json` (MongoDB writeConcern: majority), `lib/api/objectPut.js`

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits exist (no max records per run, no max operations per session). The quota system (`lib/api/apiUtils/quotas/quotaUtils.js`) limits storage capacity per bucket but does not limit operation counts or blast radius.
- **Implication**: For write-enabled scope expansion, there would be no limit on how many objects an agent could delete or modify in a single session.
- **Recommendation**: For write-enabled scope, implement per-session operation limits configurable per agent identity.
- **Evidence**: `lib/api/apiUtils/quotas/quotaUtils.js`, `lib/api/apiUtils/rateLimit/`

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No draft/pending state concept exists for S3 operations. S3's model is immediate — PUTs are immediately visible, DELETEs are immediate. Object Lock provides immutability (cannot delete locked objects) but not draft semantics.
- **Implication**: For write-enabled scope, agents cannot propose changes for human review before committing.
- **Recommendation**: For write-enabled scope, consider implementing a staged-write pattern using a "pending" prefix or separate staging bucket.
- **Evidence**: `lib/api/objectPut.js`, `lib/api/bucketPutObjectLock.js`

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No approval gate mechanism exists. All authorized operations execute immediately. No configurable human-in-the-loop capability.
- **Implication**: For write-enabled scope, high-risk operations (bulk delete, lifecycle policy changes) would execute without human oversight.
- **Recommendation**: For write-enabled scope, implement approval gates for destructive operations at the orchestration layer.
- **Evidence**: `lib/api/api.js`

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality scoring or completeness metrics exist. S3 is a blob store — data quality is the responsibility of the data producer, not the storage layer.
- **Implication**: Agents consuming objects from this S3 server cannot rely on the storage layer for quality signals.
- **Recommendation**: Quality metadata should be stored as S3 object metadata (custom headers) or in a separate data catalog.
- **Evidence**: No data quality mechanisms found.

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: PASS (no finding)
- **Finding**: The application exposes a well-defined REST HTTP interface implementing the AWS S3 protocol. Over 60 API handlers in `lib/api/` cover the full S3 API surface (bucket CRUD, object CRUD, multipart upload, versioning, ACLs, policies, encryption, lifecycle, replication, tagging, object lock, etc.). Additional REST routes exist for Veeam, backbeat, and metadata operations.
- **Gap**: None — a comprehensive REST API exists.
- **Recommendation**: N/A
- **Evidence**: `lib/api/api.js`, `lib/routes/`, `index.js`, `lib/server.js`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, or Smithy specification file exists in the repository. The API follows the AWS S3 protocol spec implicitly.
- **Gap**: No machine-readable API specification in the repository.
- **Recommendation**: Reference the AWS S3 API model or generate an OpenAPI spec from route definitions.
- **Evidence**: Absence of spec files. `lib/api/api.js`, `schema/server_access_log.schema.json` (only for log format)

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: S3-compatible error responses with structured error codes (XML body with Code, Message, Resource, RequestId). No explicit retryable indicator.
- **Gap**: No retryable boolean in error responses.
- **Recommendation**: Document retry semantics per error code in agent tool definitions.
- **Evidence**: Arsenal errors (external dependency), `lib/api/apiUtils/rateLimit/tokenBucket.js`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: S3 PUT operations are naturally idempotent. No explicit idempotency keys for POST operations.
- **Gap**: N/A for read-only scope.
- **Recommendation**: For write-enabled scope expansion, add idempotency key support for POST-based operations.
- **Evidence**: `lib/api/objectPut.js`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: XML responses for S3 management operations, binary streaming for object data, JSON for internal routes.
- **Implication**: AWS S3 SDKs handle XML parsing transparently. Agent tools should use SDKs.
- **Recommendation**: Use AWS S3 SDKs in agent tool definitions.
- **Evidence**: `lib/api/`

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has operations >30s OR long-running workflows
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has state changes (stateful-crud, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: HTTP 429 with `SlowDown` error code returned. No `X-RateLimit-Remaining` or `Retry-After` headers.
- **Implication**: Agents cannot proactively self-throttle.
- **Recommendation**: Add rate limit headers to responses.
- **Evidence**: `lib/api/apiUtils/rateLimit/tokenBucket.js`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: AWS Signature V2/V4 authentication via static access keys. No OAuth2 client credentials, no mTLS, no agent-specific identity mechanism with principal attribution beyond the access key itself.
- **Gap**: No machine identity authentication with principal attribution suitable for agent differentiation.
- **Recommendation**: Create dedicated per-agent access keys in Vault with distinct canonical IDs.
- **Evidence**: `lib/auth/vault.js`, `conf/authdata.json`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: Bucket policies and ACLs provide scoping. IAM integration incomplete (TODO comment). Service users bypass all checks.
- **Gap**: Incomplete IAM scoping. Service user bypass.
- **Recommendation**: Complete IAM integration. Never classify agents as service users.
- **Evidence**: `lib/api/apiUtils/authorization/permissionChecks.js`, `lib/api/apiUtils/authorization/serviceUser.js`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: Bucket policies support action-level conditions. IAM completeness uncertain.
- **Gap**: IAM action-level enforcement may be incomplete.
- **Recommendation**: Apply explicit bucket policies to agent-accessible buckets.
- **Evidence**: `lib/api/apiUtils/authorization/permissionChecks.js`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: No on-behalf-of flows. All requests attributed to signing access key. No agent-as-self vs agent-on-behalf-of distinction.
- **Implication**: Multi-tenant agent scenarios require separate access keys per context.
- **Recommendation**: Consider STS-like temporary credentials for delegated access.
- **Evidence**: `lib/auth/vault.js`

#### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: In-memory backend: plaintext credentials in repo (dev-only). Vault backend: external credential management. Management agent: RSA keys with 7-day rotation warning, no auto-rotation. CI: secrets via GitHub Actions.
- **Implication**: Production (Vault) has proper management. Dev credentials in repo are a hygiene concern.
- **Recommendation**: Document development-only nature of `authdata.json`. Implement auto-rotation for management credentials.
- **Evidence**: `conf/authdata.json`, `lib/management/credentials.js`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Server access logging exists with comprehensive fields but is file-based (mutable), disabled by default, and drops entries under backpressure.
- **Gap**: Audit logs are not immutable. Disabled by default.
- **Recommendation**: Enable by default. Forward to immutable store.
- **Evidence**: `lib/utilities/serverAccessLogger.js`, `config.json`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: No immediate suspension mechanism within the application. Requires external Vault operations or server restart.
- **Gap**: No hot-reloadable identity suspension.
- **Recommendation**: Implement access key deny-list with hot-reload.
- **Evidence**: `lib/auth/vault.js`, `conf/authdata.json`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No compensation or rollback mechanisms. Partial failures possible (data written, metadata update fails).
- **Gap**: N/A for read-only scope.
- **Recommendation**: For write-enabled expansion, implement compensation logic.
- **Evidence**: `lib/data/wrapper.js`, `lib/metadata/wrapper.js`

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
- **Finding**: S3 last-writer-wins model. MongoDB write concern majority. No application-level optimistic locking.
- **Gap**: N/A for read-only scope.
- **Recommendation**: For write-enabled scope, implement conditional operations.
- **Evidence**: `config.json`, `lib/api/objectPut.js`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: No circuit breakers, no retry with backoff, no configurable timeouts. Rate limiter fails open.
- **Gap**: No resilience patterns for external dependency calls.
- **Recommendation**: Implement circuit breakers for MongoDB, Redis, Vault.
- **Evidence**: `lib/auth/vault.js`, `lib/api/apiUtils/rateLimit/tokenBucket.js`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: Token bucket rate limiter exists but is per-bucket only, disabled by default, fails open.
- **Gap**: No per-agent rate limiting. Disabled by default. Fails open.
- **Recommendation**: Enable by default. Add per-identity limiting. Fix fail-open.
- **Evidence**: `lib/api/apiUtils/rateLimit/tokenBucket.js`, `config.json`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No transaction limits. Quota system limits storage only, not operation counts.
- **Gap**: N/A for read-only scope.
- **Recommendation**: For write-enabled scope, implement per-session operation limits.
- **Evidence**: `lib/api/apiUtils/quotas/quotaUtils.js`

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
- **Finding**: No draft/pending state concept. S3 operations are immediate.
- **Gap**: N/A for read-only scope.
- **Recommendation**: For write-enabled scope, implement staged-write patterns.
- **Evidence**: `lib/api/objectPut.js`

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No approval gate mechanism. All authorized operations execute immediately.
- **Gap**: N/A for read-only scope.
- **Recommendation**: For write-enabled scope, implement approval gates for destructive operations.
- **Evidence**: `lib/api/api.js`

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: Docker Compose provides local testing environment. In-memory backend for lightweight testing. No production-equivalent staging.
- **Gap**: No production-equivalent staging/sandbox with realistic data.
- **Recommendation**: Define staging configuration with seed data.
- **Evidence**: `.github/docker/docker-compose.yaml`, `DockerfileMem`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: RISK-SAFETY (resolved via Stage B, B2)
- **Finding**: **Stage A = Yes** — The system stores user-specific data (S3 objects, metadata with user IDs, access keys, bucket ownership). **Stage B evaluation**: B1 (CLEAR) — API responses return object data as-is (S3's model is that the user owns the data); the server does not add sensitive fields to listing responses beyond what the user stored. B2 (RISK-SAFETY) — Access control differentiation exists (bucket policies, ACLs) but the system has a single "full access" service user bypass with no granularity between sensitive and non-sensitive data access. B3 (INFO) — No formal data classification metadata exists.
- **Gap**: B2: Service user bypass provides undifferentiated access to all data. No OAuth scopes or role granularity below "full admin vs service user vs bucket-policy-scoped."
- **Compensating Controls**:
  - Use bucket policies to create data-domain separation (sensitive data in restricted buckets)
  - Never grant agent identities service user status
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement role-based access tiers in Vault that distinguish between sensitive and non-sensitive bucket access.
- **Evidence**: `lib/api/apiUtils/authorization/serviceUser.js`, `lib/api/apiUtils/authorization/permissionChecks.js`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The system supports multiple storage locations including AWS regions, Azure, GCP, and on-premises backends (`locationConfig.json`). Data residency is configurable per bucket via location constraints. However, there are no enforcement controls to prevent an agent from reading data from a region-restricted bucket and transmitting it to an LLM in another jurisdiction.
- **Gap**: Data residency configuration exists at the storage layer but no application-level controls prevent data from being transmitted outside its residency boundary once read via the API.
- **Compensating Controls**:
  - Implement network-level controls (VPC endpoints, private links) to prevent data egress
  - Tag buckets with residency requirements and enforce at the agent orchestration layer
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add metadata to bucket/location configurations indicating residency restrictions that agent orchestration layers can enforce.
- **Evidence**: `locationConfig.json`, `config.json`

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
- **Finding**: No PII redaction in server access logs. IP addresses, access keys, object keys (potentially containing PII), and user identifiers are logged unredacted.
- **Gap**: No PII masking or redaction.
- **Recommendation**: Add configurable PII redaction filter.
- **Evidence**: `lib/utilities/serverAccessLogger.js`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics. S3 is a blob store — quality is the producer's responsibility.
- **Implication**: Agents cannot rely on the storage layer for quality signals.
- **Recommendation**: Store quality metadata as S3 object metadata.
- **Evidence**: No data quality mechanisms found.

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: No explicit schema versioning or breaking change detection. Functional tests serve as implicit contract validation.
- **Gap**: No formal API contract testing or schema diffing in CI.
- **Recommendation**: Add OpenAPI spec and diff checking in CI.
- **Evidence**: `.github/workflows/tests.yaml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: The S3 API uses AWS's well-documented, semantically meaningful field names (BucketName, ObjectKey, ContentType, LastModified, ETag, etc.). Internal code uses clear variable names. No legacy abbreviations observed.
- **Implication**: Agent tool definitions can use S3 field names directly without a data dictionary.
- **Recommendation**: No action needed — S3's naming conventions are well-established.
- **Evidence**: `lib/api/`, AWS S3 protocol compatibility

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal data catalog. S3's own metadata model (bucket listing, object metadata headers, tagging) serves as a basic discovery mechanism. The metadata search capability (`metadataSearch` API) enables querying objects by metadata attributes.
- **Implication**: Agents can discover data through S3 listing and metadata search operations.
- **Recommendation**: For large deployments, consider integrating with AWS Glue Data Catalog or similar for cross-bucket discovery.
- **Evidence**: `lib/api/metadataSearch.js`, `bin/search_bucket.js`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: Structured logging via werelogs. Prometheus metrics. Request IDs generated. No distributed tracing (no OpenTelemetry, no X-Ray).
- **Gap**: No distributed tracing. Cannot trace requests through backend dependencies.
- **Recommendation**: Add OpenTelemetry instrumentation.
- **Evidence**: `lib/utilities/logger.js`, `lib/utilities/monitoringHandler.js`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: Prometheus alerting rules for 5xx rates and latency. Requires external AlertManager deployment. No auth-specific alerts.
- **Gap**: No alerting infrastructure deployment. No auth anomaly alerts.
- **Recommendation**: Deploy AlertManager. Add auth failure rate alerts.
- **Evidence**: `monitoring/alerts.yaml`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: Prometheus metrics track HTTP requests, duration, disk usage, object counts, and quota utilization. These are operational metrics. No business outcome metrics (e.g., data retrieval success rate by consumer, SLA compliance per tenant).
- **Implication**: Cannot measure whether agent interactions with the storage layer produce good business outcomes.
- **Recommendation**: Add custom metrics for agent-specific access patterns (e.g., agent request success rate, agent data volume accessed).
- **Evidence**: `lib/utilities/monitoringHandler.js`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance
- **Severity**: RISK-QUALITY
- **Finding**: No IaC in this repository. Deployment infrastructure not defined declaratively.
- **Gap**: No IaC for integration surface.
- **Recommendation**: Create IaC for production deployment.
- **Evidence**: Absence of IaC files.

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: CI/CD via GitHub Actions with comprehensive functional tests. No API contract testing or breaking change detection.
- **Gap**: No formal contract testing.
- **Recommendation**: Add OpenAPI validation or Pact tests in CI.
- **Evidence**: `.github/workflows/tests.yaml`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: Docker image tagging only. No automated rollback. Manual revert required.
- **Gap**: No automated rollback capability.
- **Recommendation**: Implement deployment orchestration with health-check-based rollback.
- **Evidence**: `.github/workflows/release.yaml`

#### ENG-Q4: API Test Coverage
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Always evaluated (but INFO for stateless-utility)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### ENG-Q5: Encryption at Rest
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service has persistent data stores
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `lib/auth/vault.js` | AUTH-Q1, AUTH-Q2, AUTH-Q4, AUTH-Q7, STATE-Q4 |
| `lib/api/apiUtils/authorization/permissionChecks.js` | AUTH-Q2, AUTH-Q3, DATA-Q1 |
| `lib/api/apiUtils/authorization/serviceUser.js` | AUTH-Q2, DATA-Q1 |
| `lib/server.js` | STATE-Q4 |
| `lib/api/api.js` | API-Q1, API-Q2, HITL-Q2 |
| `lib/api/objectPut.js` | API-Q4, STATE-Q3, HITL-Q1 |
| `lib/api/bucketPutPolicy.js` | AUTH-Q3 |
| `lib/api/apiUtils/rateLimit/tokenBucket.js` | API-Q3, API-Q8, STATE-Q4, STATE-Q5 |
| `lib/api/apiUtils/rateLimit/config.js` | STATE-Q5 |
| `lib/api/apiUtils/quotas/quotaUtils.js` | STATE-Q6 |
| `lib/utilities/serverAccessLogger.js` | AUTH-Q1, AUTH-Q6, DATA-Q6 |
| `lib/utilities/monitoringHandler.js` | OBS-Q1, OBS-Q3 |
| `lib/utilities/logger.js` | OBS-Q1 |
| `lib/data/wrapper.js` | STATE-Q1 |
| `lib/metadata/wrapper.js` | STATE-Q1 |
| `lib/management/credentials.js` | AUTH-Q5 |
| `lib/auth/in_memory/backend.js` | AUTH-Q7 |
| `lib/api/metadataSearch.js` | DISC-Q3 |
| `lib/routes/veeam/` | API-Q5 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/tests.yaml` | AUTH-Q5, DISC-Q1, ENG-Q2 |
| `.github/workflows/release.yaml` | ENG-Q3 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `Dockerfile` | ENG-Q3 |
| `DockerfileMem` | HITL-Q3 |
| `.github/docker/docker-compose.yaml` | HITL-Q3, ENG-Q1 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `config.json` | AUTH-Q6, STATE-Q3, STATE-Q5 |
| `conf/authdata.json` | AUTH-Q1, AUTH-Q5, AUTH-Q7 |
| `locationConfig.json` | DATA-Q2 |

### Monitoring
| File | Questions Referenced |
|------|---------------------|
| `monitoring/alerts.yaml` | OBS-Q2 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `package.json` | OBS-Q1 (werelogs, prom-client dependencies) |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `schema/server_access_log.schema.json` | API-Q2 |
