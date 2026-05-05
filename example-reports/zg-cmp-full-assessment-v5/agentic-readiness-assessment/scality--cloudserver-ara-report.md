# Agentic Readiness Assessment Report
# Agentic Readiness Assessment Report

**Target**: cloudserver (scality/S3)
**Date**: 2025-07-14
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**TD Version**: N/A
**Repository Type**: application
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: javascript, storage, s3
**Context**: Scality open-source S3-compatible object-storage server.

**Archetype Justification**: CloudServer owns persistent state (object data in file/MongoDB backends, metadata in MongoDB/LevelDB) and exposes full S3 CRUD operations (PUT/GET/DELETE objects, buckets, multipart uploads, versioning, lifecycle). It manages entity lifecycle including object lock, retention, replication, and tagging — a textbook stateful-crud archetype.

**Surface Flags**:
- has_persistent_data_store: true
- has_http_rpc_surface: true
- has_auth_surface: true
- has_write_operations: true
- has_logging_of_user_data: true

---

## Readiness Profile: Pilot-Ready (Safety Concerns)

**BLOCKERs**: 0 | **RISK-SAFETY**: 6 | **RISK-QUALITY**: 9 | **INFOs**: 27

With DATA-Q1 reclassified from BLOCKER to INFO under the new tiered model (see INFOs below), CloudServer has no remaining BLOCKERs. Proceed with a supervised pilot; prioritize RISK-SAFETY remediation before expanding scope.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 0 |
| RISK-SAFETY | 6 |
| RISK-QUALITY | 9 |
| INFO | 27 |
| N/A | 0 |
| Not Evaluated (extended) | 1 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 18
**Extended Questions Not Triggered**: 1
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: stateful-crud (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

_None. DATA-Q1 was previously BLOCKER under the binary "formal classification absent" rule; under the tiered model it resolves to INFO (see INFOs section) because CloudServer is content-agnostic by design (S3 API), IAM authorization is enforced via Vault integration on every request, and S3-native primitives (object tags, bucket tagging, SSE-S3/SSE-KMS) provide the classification building blocks — classification is an operator responsibility, not a code defect._

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: CloudServer implements server access logging via `lib/utilities/serverAccessLogger.js`. Logs capture requester identity (canonical ID, IAM user name, account name), operation, bucket, object key, HTTP status, client IP, timestamps, and authentication details. Log format follows AWS S3 server access log conventions and is documented in `schema/server_access_log.schema.json`. However, logs are written to a local file (`/logs/server-access.log` per `config.json`) with no immutability guarantees — no CloudTrail integration, no S3 Object Lock on log storage, no append-only or tamper-evident log storage mechanism. Logs can be modified or deleted by anyone with filesystem access. Default mode is `DISABLED`.
- **Gap**: No immutable or tamper-evident log storage. Log files written to local filesystem with standard file permissions (0o644). No CloudTrail integration. Server access logs disabled by default.
- **Compensating Controls**:
  - Ship server access logs to an immutable log aggregation system (e.g., S3 bucket with Object Lock, CloudWatch Logs with retention policies) at the deployment layer.
  - Enable server access logs (`S3_SERVER_ACCESS_LOGS_MODE=ENABLED`) and configure log rotation to a write-once storage target.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Enable server access logging by default and integrate with an immutable log storage backend. Add log integrity verification (e.g., log signing or hash chaining).
- **Evidence**: `lib/utilities/serverAccessLogger.js`, `schema/server_access_log.schema.json`, `config.json` (serverAccessLogs section), `lib/server.js` (log initialization)

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: CloudServer supports two auth backends: in-memory (`conf/authdata.json`) and external vault (`vaultclient`). The in-memory backend loads access keys from a static JSON file — there is no runtime revocation mechanism; the file must be manually edited and the server restarted or config reloaded via `authdata-update` event. The vault backend delegates to an external vault service which may support key revocation, but CloudServer itself has no API endpoint or mechanism to immediately suspend a specific agent identity without affecting other identities or requiring a service restart.
- **Gap**: No runtime API for individual identity suspension. In-memory auth requires config file edit + reload. No circuit-breaker for anomalous agent behavior at the identity level.
- **Compensating Controls**:
  - Use the external vault backend in production, which may provide identity disable capabilities.
  - Implement an API Gateway or reverse proxy in front of CloudServer with per-identity blocklist capability.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement a runtime API or vault integration that allows immediate revocation of specific access keys without service restart.
- **Evidence**: `lib/auth/vault.js`, `conf/authdata.json`, `lib/auth/in_memory/backend.js`

#### STATE-Q1: Compensation and Rollback ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: CloudServer provides partial compensation mechanisms: multipart uploads can be aborted via `multipartDelete.js`, which cleans up incomplete uploads. Object versioning enables access to previous object versions (a form of logical rollback). Object Lock with retention policies prevents premature deletion. However, there is no general-purpose saga pattern, compensating transaction framework, or explicit undo/rollback API for multi-step operations (e.g., "undo a batch of PutObject + PutBucketPolicy" as a unit). The `multiObjectDelete` operation in `lib/api/multiObjectDelete.js` processes deletions individually with a concurrency limit of 50 but has no transactional rollback if some deletions succeed and others fail.
- **Gap**: No general compensation/rollback framework for multi-step workflows. Multipart upload abort exists but is operation-specific. No saga pattern implementation.
- **Compensating Controls**:
  - Leverage object versioning as a logical undo mechanism — agents can retrieve previous versions.
  - Implement orchestration-layer compensation (the agent framework handles rollback logic, not the target system).
- **Remediation Timeline**: 90–180 days (architectural change)
- **Recommendation**: For read-only agents, this is informational. If scope expands to write-enabled, implement compensation endpoints or leverage S3 versioning as the rollback mechanism and document it as such.
- **Evidence**: `lib/api/multipartDelete.js`, `lib/api/multiObjectDelete.js`, `lib/api/bucketPutVersioning.js`, `constants.js` (multiObjectDeleteConcurrency)

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: CloudServer connects to multiple external dependencies: vaultd (authentication, port 8500), bucketd (metadata, port 9000), backbeat (replication, port 8900), workflowEngineOperator (port 3001), and external storage backends (AWS S3, Azure Blob, GCP). The codebase uses `node-fetch`, `request`, and custom HTTP clients for these connections. However, no circuit breaker library (e.g., Resilience4j, opossum, cockatiel) is imported or used. No explicit circuit breaker, bulkhead, or retry-with-backoff patterns were found in the HTTP client configurations. The `externalBackends` section in `config.json` configures HTTP agent keepAlive and maxSockets but not circuit breaking or retry policies. Healthcheck logic exists (`lib/utilities/healthcheckHandler.js`) but serves as a readiness probe, not a circuit breaker.
- **Gap**: No circuit breaker patterns for external dependency calls. No retry-with-backoff. No bulkhead isolation. A cascading failure in vault or bucketd propagates directly to the S3 API surface.
- **Compensating Controls**:
  - Deploy a service mesh (Istio, Linkerd) in front of CloudServer's external dependencies to provide circuit breaking at the network layer.
  - Configure timeout settings at the HTTP agent level in `config.json` (externalBackends.httpAgent).
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a circuit breaker library (e.g., `opossum` for Node.js) around vault, bucketd, and external backend calls. Configure retry-with-exponential-backoff and timeout policies.
- **Evidence**: `config.json` (vaultd, bucketd, backbeat, workflowEngineOperator, externalBackends sections), `lib/data/wrapper.js`, `lib/auth/vault.js`, `lib/metadata/wrapper.js`

#### DATA-Q2: Data Residency and Sovereignty ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: CloudServer supports multi-region location constraints via `locationConfig.json`, which defines regions (us-east-1, eu-central-1, etc.) and backend types (file, aws_s3, azure, gcp, tlp, crr). Cross-region replication is configurable via `replicationEndpoints` in `config.json`. The system allows data to be placed in specific locations via bucket location constraints. However, there are no explicit data residency enforcement policies — the system does not prevent an agent from reading data from an EU-located bucket and forwarding it to an LLM endpoint in a different region. No GDPR/LGPD compliance controls are implemented at the application level. Residency is a configuration concern at the deployment layer, not enforced by the application.
- **Gap**: No application-level data residency enforcement. Location constraints exist but do not restrict who can read data from which region. No compliance tagging or residency policy engine.
- **Compensating Controls**:
  - Implement data residency restrictions at the agent orchestration layer — configure the agent to only access buckets in approved regions.
  - Use bucket policies to restrict access by source IP or VPC endpoint to region-specific boundaries.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Document data residency requirements per location constraint. Implement bucket-level metadata tags for residency classification. Consider adding a policy engine that restricts cross-region data reads for agent identities.
- **Evidence**: `locationConfig.json`, `config.json` (replicationEndpoints, restEndpoints), `lib/api/bucketPut.js` (location constraint validation)

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Server access logs (`lib/utilities/serverAccessLogger.js`) capture the following user-identifiable data: `requester` (canonical user ID or IAM user:account name), `accountName`, `userName`, `clientIP`, `awsAccessKeyID`, `bucketName`, `objectKey`, `userAgent`, `referer`, and `hostHeader`. Object keys may contain user-identifiable information if naming conventions include PII (e.g., `users/john.doe@example.com/profile.jpg`). The `buildLogEntry` function in `serverAccessLogger.js` emits all these fields without any masking, redaction, or filtering. No PII scrubbing middleware, log masking library, or Macie integration was found. The `schema/server_access_log.schema.json` schema documents all fields that may contain PII but does not specify any redaction rules.
- **Gap**: No PII redaction in server access logs. Account names, user names, access key IDs, client IPs, and potentially PII-containing object keys are logged in plaintext.
- **Compensating Controls**:
  - Implement a log processing pipeline that redacts PII fields before forwarding to log storage.
  - Use a log masking library at the application level to hash or redact sensitive fields (accountName, userName, awsAccessKeyID, clientIP).
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a configurable PII redaction layer to `serverAccessLogger.js` that masks sensitive fields (e.g., hash account names, redact last octets of IPs, truncate access key IDs). Provide configuration to control which fields are redacted.
- **Evidence**: `lib/utilities/serverAccessLogger.js` (buildLogEntry function), `schema/server_access_log.schema.json`

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, Swagger, AsyncAPI, or Smithy specification file exists in the repository. The S3 API is de facto documented by Amazon's S3 API reference, but there is no project-specific machine-readable spec that describes CloudServer's exact API surface, including Scality-specific extensions (metadata search, rate limiting, quota management, backbeat routes, workflow operator routes). Routes are defined programmatically via `arsenal.s3routes` in `lib/server.js` and API methods are mapped in `lib/api/api.js`.
- **Gap**: No machine-readable API specification. Agent tool generation requires manual authoring referencing the AWS S3 API docs plus Scality-specific extensions.
- **Compensating Controls**:
  - Use the AWS S3 SDK/OpenAPI spec as a base and extend it with CloudServer-specific endpoints.
  - Generate an OpenAPI spec from the route definitions in `arsenal.s3routes`.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Generate an OpenAPI 3.0 specification from the `arsenal.s3routes` route table and the API method map in `lib/api/api.js`. Include Scality-specific extensions (metadata search, backbeat, rate limiting APIs).
- **Evidence**: `lib/server.js` (arsenal.s3routes), `lib/api/api.js` (API method map), `lib/routes/routeBackbeat.js`, `lib/routes/routeMetadata.js`

#### API-Q6: Asynchronous Operation Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: CloudServer supports multipart uploads (which can be long-running) with a clear lifecycle: initiate → upload parts → complete/abort. Object restore from cold storage (`lib/api/objectRestore.js`) submits a restore request but relies on the external lifecycle/backbeat system for completion — there is no built-in polling endpoint for restore status (restore status is returned via the `x-amz-restore` header on subsequent HEAD/GET requests). However, there are no general-purpose job submission + polling patterns for other long-running operations. The backbeat integration handles cross-region replication asynchronously but this is internal infrastructure, not an agent-facing async pattern.
- **Gap**: No general async job submission/polling pattern. Object restore relies on external systems with status available only via object metadata headers. No webhook callback mechanism for operation completion.
- **Compensating Controls**:
  - Agents can poll HEAD requests on restored objects to check `x-amz-restore` header status.
  - Implement an orchestration-layer polling pattern for multipart uploads (list parts + check status).
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Document the async patterns available (multipart upload lifecycle, object restore polling via HEAD) for agent tool authors. Consider adding a dedicated restore status API.
- **Evidence**: `lib/api/objectRestore.js`, `lib/api/initiateMultipartUpload.js`, `lib/api/completeMultipartUpload.js`, `lib/api/listParts.js`

#### AUTH-Q4: Identity Propagation and Delegation — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: CloudServer authenticates requests via AWS Signature V4 (or V2) and propagates `userInfo` through the request processing pipeline in `lib/api/api.js`. The auth flow extracts account display name, IAM display name, canonical ID, and session name from the vault response. Internal backbeat routes use `x-scal-canonical-id` headers for identity context. However, there is no explicit on-behalf-of flow, OAuth token exchange, or mechanism to distinguish between "agent acting as itself" vs. "agent acting on behalf of a specific human user." All requests are authenticated with a single identity (the access key owner).
- **Gap**: No on-behalf-of identity propagation. No distinction between agent-as-self and agent-on-behalf-of-user. Internal service calls bypass user bucket policies (`req.bypassUserBucketPolicies = true` in `internalRouteRequest`).
- **Compensating Controls**:
  - Use separate access keys per agent use case to create identity isolation.
  - Implement identity propagation at the agent orchestration layer using custom headers.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add support for an on-behalf-of header that carries the delegating user's identity through vault for authorization scoping.
- **Evidence**: `lib/api/api.js` (auth flow, userInfo propagation), `lib/server.js` (internalRouteRequest), `lib/auth/vault.js`

#### AUTH-Q5: Credential Management — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: CloudServer ships with `conf/authdata.json` containing sample access keys and secret keys in plaintext (`accessKey1/verySecretKey1`, `accessKey2/verySecretKey2`, etc.). These are intended for development/testing with the in-memory auth backend. The production auth path uses the vault backend (`vaultclient`), which manages credentials externally. Environment variables are used for backend credentials (AWS, Azure, GCP keys) in CI workflows. The `config.json` contains `kmsAWS.ak` and `kmsAWS.sk` fields with placeholder values (`"tbd"`). No AWS Secrets Manager or HashiCorp Vault integration for secret rotation is present in the CloudServer codebase itself.
- **Gap**: Sample credentials in plaintext in `conf/authdata.json` (development). KMS AWS credentials as plaintext config fields. No integrated secrets rotation mechanism. Production credential management delegated entirely to external vault.
- **Compensating Controls**:
  - Ensure `conf/authdata.json` is not used in production (use vault backend exclusively).
  - Manage KMS and backend credentials via environment variables injected from a secrets manager at deployment time.
- **Remediation Timeline**: 30 days
- **Recommendation**: Remove sample credentials from the shipped `conf/authdata.json` or clearly mark as development-only. Add documentation requiring external secrets management for production deployments. Consider supporting Secrets Manager or vault-based credential retrieval for KMS and backend credentials.
- **Evidence**: `conf/authdata.json`, `config.json` (kmsAWS section), `lib/auth/vault.js`, `.github/docker/creds.env`

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The server access log has a versioned JSON schema (`schema/server_access_log.schema.json` with `logFormatVersion: "0"`). The S3 API itself follows Amazon's S3 protocol versioning implicitly. However, there is no explicit API versioning in CloudServer's URL patterns (no `/v1/`, `/v2/` prefixes), no `Accept-Version` header support, and no breaking change detection in CI. The CI pipeline (`tests.yaml`) runs extensive functional tests against the AWS SDK but does not include schema comparison tools, consumer-driven contract tests (Pact), or OpenAPI diff checks. There is no changelog file tracking API changes.
- **Gap**: No explicit API versioning. No breaking change detection in CI. No consumer-driven contract testing. Schema documentation limited to server access log format.
- **Compensating Controls**:
  - The AWS S3 API compatibility provides implicit versioning stability — changes must maintain backward compatibility with AWS SDKs.
  - Functional tests using aws-sdk serve as de facto contract tests.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add an OpenAPI spec (see API-Q2) and integrate schema diff checks into CI. Establish a changelog for API surface changes. Consider Pact-style contract tests.
- **Evidence**: `schema/server_access_log.schema.json`, `.github/workflows/tests.yaml`, `package.json` (test scripts)

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: CloudServer uses the `werelogs` library for structured JSON logging with configurable log levels (`lib/utilities/logger.js`). Each request gets a unique request logger with serialized UIDs (`x-scal-request-uids` headers) for correlation across service boundaries. The server generates `req_id` fields in server access logs for request identification. However, there is no OpenTelemetry SDK, AWS X-Ray instrumentation, or `traceparent` header propagation. Distributed tracing across vault, bucketd, backbeat, and external backends relies on proprietary `x-scal-request-uids` headers rather than W3C Trace Context or OpenTelemetry standards.
- **Gap**: No standard distributed tracing (OpenTelemetry, X-Ray). Proprietary request UID correlation only. No W3C Trace Context propagation.
- **Compensating Controls**:
  - The existing `x-scal-request-uids` system provides request correlation across Scality services.
  - Deploy an OpenTelemetry collector as a sidecar to extract trace signals from structured logs.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Integrate OpenTelemetry SDK for distributed tracing. Add W3C Trace Context header propagation. Map existing request UIDs to trace IDs for backward compatibility.
- **Evidence**: `lib/utilities/logger.js`, `lib/server.js` (request UID handling), `lib/utilities/serverAccessLogger.js` (req_id field)

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No Infrastructure-as-Code files exist in the repository. There is no Terraform, CloudFormation, CDK, Helm chart, or Kustomize configuration for the deployment environment (API gateway, IAM, networking, load balancers). The repository contains `Dockerfile` and `DockerfileMem` for container builds, and `.github/docker/docker-compose.yaml` for CI testing, but these define application packaging, not infrastructure governance. As an open-source project, CloudServer's infrastructure is typically managed by the deploying organization — but the absence of reference IaC means every deployment must create its own from scratch.
- **Gap**: No IaC for deployment infrastructure. No reference architecture for API gateway, IAM roles, networking. No drift detection configuration.
- **Compensating Controls**:
  - Deploying organizations must provide their own IaC (Terraform modules, Helm charts) for the CloudServer deployment environment.
  - Use the Scality/Zenko Helm charts (if available externally) for production deployment.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add reference Helm charts or Terraform modules for common deployment patterns (single node, clustered, with vault). Include IAM role definitions and API gateway configuration templates.
- **Evidence**: `Dockerfile`, `DockerfileMem`, `.github/docker/docker-compose.yaml` (CI-only)

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: CloudServer has an extensive CI pipeline (`.github/workflows/tests.yaml`) that includes: linting (eslint), unit tests with coverage (nyc), functional tests against multiple backends (file, MongoDB v0/v1, S3C integration), AWS SDK compatibility tests (ft_awssdk), s3cmd/s3curl tests, KMIP encryption tests, SSE migration tests, and utapi v2 tests. CodeQL security scanning and dependency review workflows exist. However, there is no explicit API contract testing: no Pact consumer-driven contracts, no OpenAPI spec validation in the build, no schema comparison tools, and no automated detection of API-breaking changes.
- **Gap**: No explicit API contract testing. No OpenAPI spec validation. No breaking change detection tooling. Functional tests using aws-sdk serve as implicit contract tests but do not catch subtle breaking changes in response format or error codes.
- **Compensating Controls**:
  - Extensive AWS SDK functional tests provide strong implicit contract testing for S3 API compatibility.
  - Multiple client tests (aws-sdk, s3cmd, s3curl) validate interoperability.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenAPI spec validation to CI (once spec exists per API-Q2). Consider Pact tests for critical consumers. Add response format assertions to existing functional tests.
- **Evidence**: `.github/workflows/tests.yaml`, `.github/workflows/codeql.yaml`, `.github/workflows/dependency-review.yaml`, `package.json` (test scripts)

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The release workflow (`.github/workflows/release.yaml`) builds and pushes Docker images tagged with the release version to GitHub Container Registry. There is no blue/green deployment configuration, no CodeDeploy rollback triggers, no canary deployment with automatic rollback, and no feature flag system. Rollback requires manually deploying a previous Docker image tag. The release process is a manual `workflow_dispatch` that tags a specific version — there is no automated rollback mechanism if a release breaks the API surface.
- **Gap**: No automated rollback mechanism. No blue/green or canary deployment. No feature flags. Manual Docker image tag rollback only.
- **Compensating Controls**:
  - Container-based deployment enables manual rollback by re-deploying a previous image tag.
  - The deploying organization can implement Kubernetes rolling update with rollback at the orchestration layer.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add Kubernetes deployment manifests with rollback triggers. Implement health-check-based automatic rollback in the deployment pipeline. Document the manual rollback procedure.
- **Evidence**: `.github/workflows/release.yaml`, `Dockerfile`

## INFOs — Architecture and Design Inputs

### DATA-Q1: Sensitive Data Classification ⚡ (Tiered) — Demoted from BLOCKER

- **Severity**: INFO
- **Stage A**: Yes — CloudServer stores user-uploaded objects of any content type, object metadata with owner info, and access keys in `conf/authdata.json`.
- **B1 — API response scoping: CLEAR.** S3 API is content-agnostic by design; no credentials echoed in responses. Vault-backed IAM validates credentials without returning them. `GetBucketPolicy`/`GetBucketACL`/`ServiceGet` expose only canonical IDs and policy documents (intentional).
- **B2 — Access control differentiation: CLEAR.** Every API call validates authorization via Vault-backed IAM before returning data (`lib/api/apiUtils/authorization/permissionChecks.js`, `lib/metadata/metadataUtils.js`). No policy-bypass paths detected in read-only scope.
- **B3 — Formal classification metadata: INFO.** Native S3 primitives (object tags, bucket tags, bucket-level SSE-S3/SSE-KMS) provide classification building blocks; enforcement is operator-configured.
- **Overall**: Only B3 fires → **DATA-Q1 = INFO**. CloudServer correctly delegates classification to the S3 framework and operator configuration.
- **Recommendation (aspirational)**: Enable default bucket encryption globally; adopt object-tag conventions; integrate with Macie where deployed.
- **Evidence**: `lib/auth/vault.js`, `lib/api/bucketGetPolicy.js`, `lib/api/bucketGetACL.js`, `lib/api/objectGetTagging.js`, `lib/api/bucketGetEncryption.js`, `lib/metadata/metadataUtils.js`, `lib/kms/wrapper.js`.

### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: CloudServer exposes a REST HTTP interface implementing the Amazon S3 protocol on port 8000. Routes are handled via `arsenal.s3routes` in `lib/server.js`. The API surface includes 70+ S3 operations (object CRUD, bucket management, multipart uploads, versioning, lifecycle, ACLs, policies, tagging, encryption, replication, object lock, website hosting). The API is well-documented by Amazon's S3 API specification. Additional Scality-specific routes exist for backbeat (`lib/routes/routeBackbeat.js`), metadata search (`lib/routes/routeMetadata.js`), veeam integration, and workflow engine operations.
- **Implication**: The S3 protocol provides a well-understood, widely-tooled integration surface. Agent tools can be built using standard AWS S3 SDKs. Scality-specific extensions require separate documentation.
- **Recommendation**: Document Scality-specific API extensions separately from the standard S3 surface.
- **Evidence**: `lib/server.js`, `lib/api/api.js`, `lib/routes/routeBackbeat.js`, `lib/routes/routeMetadata.js`

### API-Q3: Structured Error Responses
- **Severity**: INFO
- **Finding**: CloudServer uses the `arsenal` library's error framework to generate structured XML error responses following the S3 protocol. Errors include `<Code>`, `<Message>`, and `<Resource>` fields in XML format. The `checkAuthResults` function in `lib/api/api.js` maps authentication failures to specific S3 error codes (e.g., `AccessDenied`, `InvalidRequest`, `InternalError`). Error codes are well-defined by the S3 specification and include both retriable (5xx) and terminal (4xx) categories.
- **Implication**: Agents can parse S3 XML error responses to distinguish retriable from terminal errors. Standard AWS SDK error handling works out of the box.
- **Recommendation**: No action required. Error structure follows S3 protocol.
- **Evidence**: `lib/api/api.js` (checkAuthResults), `constants.js`

### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: S3 PUT operations are naturally idempotent (PUT with same key overwrites). Multipart uploads use upload IDs for tracking. However, no explicit idempotency key support exists for non-idempotent operations. For read-only agents, this is not relevant.
- **Implication**: If agent scope expands to write-enabled, idempotency of multipart upload completion and multi-object delete should be evaluated.
- **Recommendation**: No action for read-only scope.
- **Evidence**: `lib/api/objectPut.js`, `lib/api/completeMultipartUpload.js`

### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: S3 API responses use XML format with well-defined schemas (ListBucketResult, ListPartsResult, CopyObjectResult, etc.). Internal routes (backbeat, metadata) use JSON. Metrics endpoint (port 8002) returns Prometheus text format. The `xml2js` library is used for XML parsing, and the `arsenal` library handles XML serialization.
- **Implication**: Agents consuming the S3 surface must handle XML parsing. Standard AWS SDKs abstract this. Internal routes provide JSON which is more LLM-friendly.
- **Recommendation**: Consider offering a JSON response mode for the S3 API surface to simplify agent consumption.
- **Evidence**: `lib/api/bucketGet.js`, `lib/api/serviceGet.js`, `lib/utilities/collectResponseHeaders.js`, `package.json` (xml2js dependency)

### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: CloudServer supports S3 bucket notification configuration via `bucketPutNotification` and `bucketGetNotification` APIs. The `bucketNotificationDestinations` in `config.json` defines notification targets (currently a dummy target for testing). The notification system supports filtering by event type (ObjectCreated, ObjectRemoved, etc.). Cross-region replication via backbeat provides event-driven data movement. The `recordLog` feature in `config.json` enables an append-only record of metadata changes.
- **Implication**: Agents can subscribe to object lifecycle events via bucket notifications. This enables proactive agent patterns (react to new objects, deletions, etc.).
- **Recommendation**: Document available notification event types and configure production notification destinations (SNS, SQS, or webhook endpoints).
- **Evidence**: `lib/api/bucketPutNotification.js`, `lib/api/bucketGetNotification.js`, `config.json` (bucketNotificationDestinations, recordLog)

### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: CloudServer has a built-in rate limiting system (`lib/api/apiUtils/rateLimit/`) with per-bucket and global default configurations, token bucket algorithm, cache-based fast path, background token refill, and cleanup jobs. Rate limiting is configurable via `config.json` (`rateLimiting` section) and per-bucket via the `bucketPutRateLimit` API. Rate-limited requests are logged in server access logs with `rateLimited` and `rateLimitSource` fields. However, the server does not return standard rate limit headers (`X-RateLimit-Remaining`, `X-RateLimit-Limit`, `Retry-After`) in HTTP responses — rate-limited requests receive a 503 error response.
- **Implication**: Agents cannot self-throttle based on rate limit headers. They must handle 503 errors with retry logic. The rate limiting system is sophisticated but not discoverable via HTTP headers.
- **Recommendation**: Add `X-RateLimit-Remaining`, `X-RateLimit-Limit`, and `Retry-After` response headers so agents can self-throttle proactively.
- **Evidence**: `lib/api/apiUtils/rateLimit/helpers.js`, `lib/api/apiUtils/rateLimit/tokenBucket.js`, `lib/api/api.js` (rate limit integration), `config.json`

### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: CloudServer supports machine identity authentication via: (1) In-memory auth backend with access key/secret key pairs defined in `conf/authdata.json`, (2) External vault backend via `vaultclient` for production auth, (3) Chain backend combining both. Each authenticated request yields a `userInfo` object with canonical ID, account display name, IAM display name, and auth version. The authenticated principal is attributed in server access logs (requester, accountName, userName, awsAccessKeyID fields). AWS Signature V4 and V2 are supported. Service accounts (replication, lifecycle, gc, md-ingestion) are defined in `constants.js`.
- **Implication**: Agent identities can be created as access key/secret key pairs and attributed in audit logs. The auth model supports per-agent identity.
- **Recommendation**: Use the vault backend for production agent identities. Create dedicated service accounts per agent use case.
- **Evidence**: `lib/auth/vault.js`, `conf/authdata.json`, `lib/api/api.js` (auth flow), `constants.js` (serviceAccountProperties)

### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: INFO
- **Finding**: CloudServer implements S3-compatible authorization with bucket policies (`lib/api/bucketPutPolicy.js`), ACLs (`lib/api/bucketPutACL.js`, `lib/api/objectPutACL.js`), and IAM-style action-level permissions via the vault backend. Bucket policies support condition keys, principal matching, and resource-level permissions. The `prepareRequestContexts.js` module generates fine-grained RequestContext objects for each S3 action (e.g., `s3:GetObject`, `s3:PutObject`, `s3:DeleteObject`). The `bucketOwnerActions` list in `constants.js` defines operations restricted to bucket owners.
- **Implication**: Agent identities can be granted read-only access to specific buckets without inheriting write or delete permissions. Least-privilege is achievable.
- **Recommendation**: Define bucket policies that grant agent identities only `s3:GetObject`, `s3:ListBucket`, and `s3:HeadObject` permissions for read-only agents.
- **Evidence**: `lib/api/apiUtils/authorization/prepareRequestContexts.js`, `lib/api/bucketPutPolicy.js`, `constants.js` (bucketOwnerActions)

### AUTH-Q3: Action-Level Authorization
- **Severity**: INFO
- **Finding**: The `prepareRequestContexts.js` module generates action-specific authorization contexts for every API method. For example, `objectGet` generates both `s3:GetObject` and `s3:GetObjectTagging` contexts; `objectPut` generates `s3:PutObject`, `s3:PutObjectTagging`, `s3:PutObjectACL`, and `s3:PutObjectRetention` contexts as appropriate. The vault backend evaluates these contexts against IAM policies, supporting explicit allow/deny at the action level. This enables an agent to read records but not delete them within the same resource type.
- **Implication**: Action-level authorization is fully supported. An agent can be given `s3:GetObject` without `s3:DeleteObject` on the same bucket.
- **Recommendation**: No action required. Action-level authorization is well-implemented.
- **Evidence**: `lib/api/apiUtils/authorization/prepareRequestContexts.js`, `lib/api/api.js` (checkAuthResults)

### STATE-Q2: Queryable Current State
- **Severity**: INFO
- **Finding**: CloudServer exposes GET endpoints for every S3 resource: `objectGet`, `objectHead`, `bucketGet` (list objects), `bucketHead`, `serviceGet` (list buckets), `bucketGetACL`, `bucketGetPolicy`, `bucketGetVersioning`, `bucketGetEncryption`, `bucketGetLifecycle`, `bucketGetNotification`, `bucketGetObjectLock`, `bucketGetTagging`, `objectGetACL`, `objectGetTagging`, `objectGetLegalHold`, `objectGetRetention`. Listing supports pagination via marker/continuation-token parameters with a hard limit of 1000 items per page.
- **Implication**: Agents can inspect any S3 resource's current state before deciding next steps. The full read surface is well-suited for agent consumption.
- **Recommendation**: No action required.
- **Evidence**: `lib/api/api.js` (complete API method map), `lib/api/bucketGet.js`, `lib/api/objectHead.js`

### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: S3 provides ETag-based conditional operations (`If-Match`, `If-None-Match` headers). Object versioning provides conflict-free writes (each write creates a new version). MongoDB backend supports atomic operations. However, no explicit optimistic locking (version fields) or pessimistic locking (`SELECT FOR UPDATE`) exists at the application level. For read-only agents, concurrent read operations do not create data integrity risks.
- **Implication**: For read-only agents, no concurrency concern. If scope expands to write-enabled, evaluate ETag-based conditional writes.
- **Recommendation**: No action for read-only scope.
- **Evidence**: `lib/api/objectPut.js`, `lib/api/objectGet.js`, `constants.js`

### STATE-Q5: Rate Limiting and Throttling
- **Severity**: INFO
- **Finding**: CloudServer implements a comprehensive rate limiting system in `lib/api/apiUtils/rateLimit/`. Features include: (1) Per-bucket rate limits configurable via `bucketPutRateLimit` API, (2) Global default rate limits configurable in `config.json`, (3) Token bucket algorithm with in-memory token consumption, (4) Redis-backed token refill for distributed deployments, (5) Cache-based fast path (no metadata fetch) for cached configurations, (6) Background cleanup and refill jobs, (7) Rate-limited requests logged in server access logs. Internal service requests and rate limit admin actions are exempt from limiting.
- **Implication**: Agent traffic can be rate-limited at the bucket level, preventing runaway agent loops from overwhelming the service.
- **Recommendation**: Configure appropriate per-bucket rate limits for buckets agents will access. Monitor rate-limited request counts via Prometheus metrics.
- **Evidence**: `lib/api/apiUtils/rateLimit/helpers.js`, `lib/api/apiUtils/rateLimit/tokenBucket.js`, `lib/api/apiUtils/rateLimit/refillJob.js`, `lib/api/api.js`

### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: CloudServer enforces several operational limits: `maxMultiObjectDeleteLen: 1000` objects per batch delete, `multiObjectDeleteConcurrency: 50` concurrent deletions, `maximumAllowedUploadSize: 5GB` per PUT, `listingHardLimit: 1000` items per listing, `maximumAllowedPartCount: 10000` parts per multipart upload, and configurable `apiBodySizeLimits` per API method. Rate limiting provides per-bucket request limits. However, there are no configurable per-agent transaction limits (e.g., max operations per session).
- **Implication**: For read-only agents, blast radius is limited to read traffic volume (handled by rate limiting). If scope expands to write-enabled, per-agent transaction limits should be implemented.
- **Recommendation**: No action for read-only scope.
- **Evidence**: `constants.js` (multiObjectDeleteConcurrency, listingHardLimit, maximumAllowedPartCount), `config.json` (apiBodySizeLimits)

### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: CloudServer supports several pending/draft-like patterns: multipart uploads have a pending lifecycle (initiated → parts uploaded → completed/aborted), S3 Object Lock provides governance and compliance modes that prevent premature modifications, and bucket versioning enables suspended/enabled states. However, there is no general-purpose draft/pending state for arbitrary operations.
- **Implication**: For read-only agents, draft states are not relevant. Write-enabled agents could leverage multipart upload's pending lifecycle for staged operations.
- **Recommendation**: No action for read-only scope.
- **Evidence**: `lib/api/initiateMultipartUpload.js`, `lib/api/bucketPutObjectLock.js`, `lib/api/objectPutRetention.js`

### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable approval gate mechanism exists in CloudServer. There is no concept of "require human approval before executing operation X." Object Lock provides compliance-mode retention (cannot be shortened even by root), but this is a data protection feature, not an approval gate.
- **Implication**: For read-only agents, approval gates are not needed. If scope expands to write-enabled, implement approval gates at the agent orchestration layer.
- **Recommendation**: No action for read-only scope.
- **Evidence**: `lib/api/objectPutRetention.js`, `lib/api/objectPutLegalHold.js`

### HITL-Q3: Sandbox/Staging Environment
- **Severity**: INFO
- **Finding**: CloudServer provides excellent local testing capabilities: `DockerfileMem` for in-memory-only operation, `S3BACKEND=mem` environment variable for memory backend, `.github/docker/docker-compose.yaml` with full service stack (Redis, MongoDB, vault, sproxyd, pykmip), multiple test location configs (`tests/locationConfig/`), comprehensive functional test suites, and seed data patterns in CI workflows. The `yarn run mem_backend` script starts a minimal server suitable for agent testing.
- **Implication**: Agents can be tested against a local CloudServer instance with in-memory backends — zero risk to production data.
- **Recommendation**: Document the recommended sandbox setup for agent developers (docker-compose + in-memory backend).
- **Evidence**: `DockerfileMem`, `.github/docker/docker-compose.yaml`, `package.json` (mem_backend script), `tests/locationConfig/`

### DATA-Q3: Selective Query Support
- **Severity**: INFO
- **Finding**: CloudServer implements S3-compatible list operations with pagination: `bucketGet` supports `max-keys` (default/max 1000), `marker`/`start-after`, `continuation-token`, `prefix`, and `delimiter` parameters. `listMultipartUploads` supports `max-uploads`, `key-marker`, `upload-id-marker`. `listParts` supports `max-parts` and `part-number-marker`. The `metadataSearch` API supports SQL-like WHERE clauses for filtered queries. All list operations enforce `listingHardLimit: 1000`.
- **Implication**: Agents can query data with precise filters, pagination, and bounded result sets — avoiding context window overflow.
- **Recommendation**: No action required. Pagination is well-implemented.
- **Evidence**: `lib/api/bucketGet.js`, `lib/api/listMultipartUploads.js`, `lib/api/listParts.js`, `lib/api/metadataSearch.js`, `constants.js` (listingHardLimit)

### DATA-Q4: System of Record Designations
- **Severity**: INFO
- **Finding**: CloudServer IS the system of record for S3 object storage within its deployment scope. It owns the authoritative copy of object data, metadata, ACLs, policies, lifecycle configurations, versioning state, encryption configuration, and notification settings. The replication system (backbeat) creates copies to other locations but CloudServer maintains the primary record. No conflicting system-of-record claims exist.
- **Implication**: Agents reading from CloudServer access the authoritative data. No master data reconciliation needed.
- **Recommendation**: Document CloudServer as the system of record for S3 data in the deployment context.
- **Evidence**: `lib/metadata/wrapper.js`, `lib/data/wrapper.js`, `config.json` (replicationEndpoints)

### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: INFO
- **Finding**: CloudServer provides rich temporal metadata: `Last-Modified` header on objects, `ETag` for content fingerprinting, `Date` response headers, `x-amz-expiration` for lifecycle-managed objects, `x-amz-restore` with restore expiry dates, and version-specific timestamps. The `x-amz-meta-x-scal-last-modified` custom header preserves original modification time for ingested objects. Object versioning creates timestamped version chains. Cache-Control headers can signal freshness policies. MongoDB backend uses consistent reads (`readPreference: primary`, `writeConcern: majority`).
- **Implication**: Agents can reason about data freshness using Last-Modified, ETag, and versioning metadata. Strong consistency via MongoDB primary reads.
- **Recommendation**: No action required. Temporal metadata is comprehensive.
- **Evidence**: `lib/utilities/collectResponseHeaders.js`, `constants.js` (lastModifiedHeader), `config.json` (mongodb settings)

### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: CloudServer enforces data integrity via Content-MD5 validation on PUT operations, ETag generation (MD5 hash of object data), multipart upload checksum validation, and configurable integrity checks (`config.json` integrityChecks section). Prometheus metrics track object counts, bucket counts, disk usage, and data ingestion volume. However, there are no formal data quality scores, completeness metrics, or data profiling capabilities.
- **Implication**: Data integrity is enforced at the object level (checksum validation). No data quality scoring exists but integrity is guaranteed at the storage layer.
- **Recommendation**: For agent use cases requiring data quality scores, implement a metadata enrichment layer that tags objects with quality metrics.
- **Evidence**: `config.json` (integrityChecks), `lib/utilities/monitoringHandler.js` (numberOfObjects, dataIngested gauges), `constants.js` (emptyFileMd5)

### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: CloudServer uses S3 protocol standard field names throughout: `Key`, `ETag`, `LastModified`, `ContentType`, `ContentLength`, `VersionId`, `StorageClass`, `Owner`, `Bucket`, `Prefix`, `MaxKeys`, `Delimiter`. These are well-known, semantically meaningful, and documented by the S3 specification. Internal fields use camelCase JavaScript conventions. Server access log fields use descriptive names (`bucketName`, `objectKey`, `requester`, `operation`, `errorCode`). No legacy abbreviations or codes requiring a data dictionary.
- **Implication**: LLM-based agents can interpret field names without external lookup. The S3 naming convention is industry-standard.
- **Recommendation**: No action required.
- **Evidence**: `lib/utilities/collectResponseHeaders.js`, `schema/server_access_log.schema.json`, `lib/api/bucketGet.js`

### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal data catalog (AWS Glue, Collibra, DataHub) exists. The `docs/` directory contains architecture documentation (`ARCHITECTURE.rst`), API guides (`BUCKET_POLICIES.md`, `GET_BUCKET_V2.md`, `MD_SEARCH.rst`), integration guides, and operational documentation. The `schema/server_access_log.schema.json` provides a JSON schema for log format. S3 object metadata (user-defined `x-amz-meta-*` headers) serves as a lightweight metadata layer.
- **Implication**: No formal data catalog for agent discovery. S3 object tagging and metadata provide basic semantic annotation. Agents must know bucket structures in advance.
- **Recommendation**: Consider implementing S3 object tagging conventions for semantic annotation. Document bucket-level data dictionaries for agent consumers.
- **Evidence**: `docs/ARCHITECTURE.rst`, `docs/MD_SEARCH.rst`, `schema/server_access_log.schema.json`

### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: INFO
- **Finding**: CloudServer provides comprehensive Prometheus alerting rules in `monitoring/alerts.yaml`: `DataAccessS3EndpointDegraded` (warning when <100% endpoints up), `DataAccessS3EndpointCritical` (<50% endpoints up), `SystemErrorsWarning` (>3% 5xx errors), `SystemErrorsCritical` (>5% 5xx errors), `ListingLatencyWarning` (>300ms), `ListingLatencyCritical` (>500ms), `DeleteLatencyWarning` (>500ms), `DeleteLatencyCritical` (>1s), and quota availability alerts. Alerting thresholds are configurable via template variables.
- **Implication**: Target system degradation is detectable via Prometheus alerts. Agents consuming CloudServer APIs will benefit from these alerts for anomaly detection.
- **Recommendation**: Add agent-specific alerting rules (e.g., alert when agent-identified traffic exceeds thresholds). Consider adding alert rules for put/get latency in addition to listing/delete.
- **Evidence**: `monitoring/alerts.yaml`, `lib/utilities/monitoringHandler.js` (metric definitions)

### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: CloudServer publishes custom Prometheus metrics via `lib/utilities/monitoringHandler.js`: `s3_cloudserver_buckets_count`, `s3_cloudserver_objects_count`, `s3_cloudserver_ingested_bytes`, `s3_cloudserver_disk_available_bytes`, `s3_cloudserver_disk_free_bytes`, `s3_cloudserver_disk_total_bytes`, `s3_cloudserver_http_requests_total` (with method/action/code labels), `s3_cloudserver_http_request_duration_seconds`, `s3_cloudserver_http_active_requests`, quota evaluation metrics, and lifecycle duration metrics. A Grafana dashboard definition exists in `monitoring/dashboard.json`.
- **Implication**: Rich business metrics are available for monitoring agent impact on the storage system. Agents can be correlated with storage growth, request patterns, and performance.
- **Recommendation**: Add agent-specific metric labels to distinguish agent traffic from human traffic in dashboards.
- **Evidence**: `lib/utilities/monitoringHandler.js`, `monitoring/dashboard.json`, `monitoring/alerts.yaml`

### ENG-Q4: API Test Coverage
- **Severity**: INFO
- **Finding**: CloudServer has extensive automated test coverage: unit tests in `tests/unit/` covering API logic, functional tests using the AWS SDK (`ft_awssdk`) covering buckets, objects, versioning, multipart uploads, and service operations; s3cmd tests (`ft_s3cmd`), s3curl tests (`ft_s3curl`), raw node HTTP tests (`ft_node`), healthcheck tests, backbeat route tests, multiple backend tests, KMIP encryption tests, SSE KMS migration tests, utapi v2 tests, and SUR quota tests. Tests run across multiple storage backends (file, mem, MongoDB v0, MongoDB v1, S3C). Coverage is tracked via nyc/istanbul and reported to Codecov.
- **Implication**: The API surface agents will consume is well-tested across multiple clients and backends. High confidence in API behavior stability.
- **Recommendation**: Add agent-specific test scenarios (e.g., rapid sequential reads, pagination exhaustion, error handling patterns).
- **Evidence**: `.github/workflows/tests.yaml`, `package.json` (test scripts), `tests/unit/`, `tests/functional/`

### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: INFO
- **Finding**: CloudServer implements server-side encryption at rest via `lib/kms/wrapper.js` with multiple backends: (1) In-memory KMS for testing, (2) File-based KMS for development, (3) KMIP protocol (Thales) for production, (4) AWS KMS for cloud deployments. Supports SSE-S3 (AES256) and SSE-KMS (aws:kms) algorithms. Per-account default encryption keys are supported (`defaultEncryptionKeyPerAccount: true` in config). Bucket-level encryption is configurable via `bucketPutEncryption` API. KMS health checks ensure encryption service availability. SSE migration between KMS providers is supported.
- **Implication**: Data agents access can be encrypted at rest. Encryption is opt-in per bucket but can be enforced via bucket policies.
- **Recommendation**: Enforce encryption at rest for all buckets that agents will access. Use KMIP or AWS KMS backends in production.
- **Evidence**: `lib/kms/wrapper.js`, `lib/kms/common.js`, `lib/api/bucketPutEncryption.js`, `config.json` (defaultEncryptionKeyPerAccount, kmsAWS, kmip sections)

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: CloudServer exposes a documented REST HTTP interface implementing the Amazon S3 protocol. Routes handled via `arsenal.s3routes`. 70+ S3 operations supported. API is well-documented by Amazon's S3 API specification. Scality-specific extensions exist for backbeat, metadata search, veeam, and workflow operations.
- **Gap**: Scality-specific extensions not separately documented in a machine-readable format.
- **Recommendation**: Document Scality-specific extensions separately.
- **Evidence**: `lib/server.js`, `lib/api/api.js`, `lib/routes/routeBackbeat.js`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, Swagger, AsyncAPI, or Smithy specification exists. S3 API documented by Amazon. No project-specific machine-readable spec.
- **Gap**: No machine-readable API specification for agent tool generation.
- **Recommendation**: Generate OpenAPI 3.0 spec from route definitions.
- **Evidence**: `lib/server.js`, `lib/api/api.js`

#### API-Q3: Structured Error Responses
- **Severity**: INFO
- **Finding**: Arsenal error framework generates structured XML errors with `<Code>`, `<Message>`, `<Resource>`. S3 error codes well-defined. Retriable (5xx) vs terminal (4xx) distinction clear.
- **Gap**: None. Error structure follows S3 protocol.
- **Recommendation**: No action required.
- **Evidence**: `lib/api/api.js`, `constants.js`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: S3 PUT operations are naturally idempotent. No explicit idempotency key support. Not relevant for read-only agents.
- **Gap**: No explicit idempotency keys (informational for read-only scope).
- **Recommendation**: No action for read-only scope.
- **Evidence**: `lib/api/objectPut.js`, `lib/api/completeMultipartUpload.js`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: XML responses for S3 API. JSON for internal routes. Prometheus text for metrics.
- **Gap**: N/A
- **Recommendation**: Consider JSON response option for agent consumption.
- **Evidence**: `lib/api/bucketGet.js`, `lib/api/serviceGet.js`

#### API-Q6: Asynchronous Operation Support
- **Severity**: RISK-QUALITY
- **Finding**: Multipart uploads have lifecycle (initiate→parts→complete). Object restore relies on external backbeat with status via `x-amz-restore` header. No general async polling pattern.
- **Gap**: No general async job/polling pattern. No webhook callbacks.
- **Recommendation**: Document async patterns for agent tool authors.
- **Evidence**: `lib/api/objectRestore.js`, `lib/api/initiateMultipartUpload.js`

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: S3 bucket notification configuration supported. Notification destinations configurable. Event filtering by type supported. Cross-region replication via backbeat. Record log for metadata changes.
- **Gap**: None significant. Notification system exists.
- **Recommendation**: Configure production notification destinations.
- **Evidence**: `lib/api/bucketPutNotification.js`, `config.json`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: Rate limiting implemented with per-bucket and global configs. No `X-RateLimit-Remaining` or `Retry-After` response headers. Rate-limited requests get 503.
- **Gap**: No rate limit response headers for agent self-throttling.
- **Recommendation**: Add standard rate limit response headers.
- **Evidence**: `lib/api/apiUtils/rateLimit/helpers.js`, `lib/api/api.js`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: Machine identity supported via access key/secret key pairs (in-memory or vault backends). Principal attribution in server access logs. AWS Signature V4/V2 supported. Service accounts defined.
- **Gap**: None. Machine identity with attribution is supported.
- **Recommendation**: Use vault backend for production. Create dedicated agent service accounts.
- **Evidence**: `lib/auth/vault.js`, `conf/authdata.json`, `lib/api/api.js`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: INFO
- **Finding**: S3 bucket policies, ACLs, IAM-style permissions via vault. Fine-grained RequestContext objects per action. Resource-level permissions supported.
- **Gap**: None. Least-privilege achievable via bucket policies.
- **Recommendation**: Define read-only bucket policies for agent identities.
- **Evidence**: `lib/api/apiUtils/authorization/prepareRequestContexts.js`, `lib/api/bucketPutPolicy.js`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: INFO
- **Finding**: Action-specific authorization contexts for every API method. Vault evaluates against IAM policies with explicit allow/deny.
- **Gap**: None. Action-level authorization fully implemented.
- **Recommendation**: No action required.
- **Evidence**: `lib/api/apiUtils/authorization/prepareRequestContexts.js`, `lib/api/api.js`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: RISK-QUALITY
- **Finding**: Auth propagates `userInfo` through request pipeline. No explicit on-behalf-of flow or OAuth token exchange. Internal routes bypass user bucket policies.
- **Gap**: No on-behalf-of identity propagation. No agent-as-self vs agent-on-behalf-of distinction.
- **Recommendation**: Add on-behalf-of header support via vault integration.
- **Evidence**: `lib/api/api.js`, `lib/server.js`, `lib/auth/vault.js`

#### AUTH-Q5: Credential Management
- **Severity**: RISK-QUALITY
- **Finding**: Sample credentials in `conf/authdata.json` (plaintext, development use). Vault backend for production. KMS credentials as config fields. No integrated secrets rotation.
- **Gap**: Hardcoded sample credentials. No secrets rotation mechanism.
- **Recommendation**: Mark sample creds as dev-only. Require external secrets management.
- **Evidence**: `conf/authdata.json`, `config.json`, `lib/auth/vault.js`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Server access logs capture requester identity, operations, and details. Logs written to local file with no immutability. Disabled by default.
- **Gap**: No immutable log storage. No tamper-evidence. Disabled by default.
- **Recommendation**: Enable logging by default. Integrate with immutable log storage.
- **Evidence**: `lib/utilities/serverAccessLogger.js`, `config.json`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: In-memory auth requires config edit + restart. Vault may support revocation externally. No runtime API for identity suspension.
- **Gap**: No runtime identity suspension mechanism.
- **Recommendation**: Implement runtime API or vault integration for key revocation.
- **Evidence**: `lib/auth/vault.js`, `conf/authdata.json`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Partial compensation: multipart upload abort, object versioning as rollback. No general saga pattern or compensating transaction framework.
- **Gap**: No general compensation/rollback for multi-step workflows.
- **Recommendation**: Leverage versioning as rollback mechanism. Implement orchestration-layer compensation.
- **Evidence**: `lib/api/multipartDelete.js`, `lib/api/multiObjectDelete.js`, `lib/api/bucketPutVersioning.js`

#### STATE-Q2: Queryable Current State
- **Severity**: INFO
- **Finding**: GET endpoints for every S3 resource. Listing with pagination. Full read surface for agent consumption.
- **Gap**: None. All state is queryable.
- **Recommendation**: No action required.
- **Evidence**: `lib/api/api.js`, `lib/api/bucketGet.js`, `lib/api/objectHead.js`

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: ETag-based conditional operations. Object versioning for conflict-free writes. MongoDB atomic operations. No explicit optimistic locking at application level.
- **Gap**: No explicit optimistic locking (informational for read-only scope).
- **Recommendation**: No action for read-only scope.
- **Evidence**: `lib/api/objectPut.js`, `lib/api/objectGet.js`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: No circuit breaker library. No retry-with-backoff. No bulkhead isolation. External dependency failures propagate to API surface.
- **Gap**: No circuit breaker patterns for vault, bucketd, backbeat, or external backend calls.
- **Recommendation**: Add `opossum` circuit breaker library. Configure retry-with-backoff.
- **Evidence**: `config.json`, `lib/data/wrapper.js`, `lib/auth/vault.js`, `lib/metadata/wrapper.js`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: INFO
- **Finding**: Comprehensive rate limiting: per-bucket and global configs, token bucket algorithm, Redis-backed distributed refill, cache-based fast path, background jobs. Internal requests exempt.
- **Gap**: None. Rate limiting is well-implemented.
- **Recommendation**: Configure per-bucket rate limits for agent-accessed buckets.
- **Evidence**: `lib/api/apiUtils/rateLimit/helpers.js`, `lib/api/apiUtils/rateLimit/tokenBucket.js`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Operational limits enforced (1000 items/listing, 50 concurrent deletes, 5GB max upload). No per-agent transaction limits.
- **Gap**: No per-agent transaction limits (informational for read-only scope).
- **Recommendation**: No action for read-only scope.
- **Evidence**: `constants.js`, `config.json`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path. CloudServer is P2 priority.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Multipart upload pending lifecycle, Object Lock governance/compliance modes, bucket versioning states. No general draft/pending state.
- **Gap**: No general-purpose draft state (informational for read-only scope).
- **Recommendation**: No action for read-only scope.
- **Evidence**: `lib/api/initiateMultipartUpload.js`, `lib/api/bucketPutObjectLock.js`

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No approval gate mechanism. Object Lock provides data protection but not operation approval.
- **Gap**: No approval gates (informational for read-only scope).
- **Recommendation**: No action for read-only scope.
- **Evidence**: `lib/api/objectPutRetention.js`, `lib/api/objectPutLegalHold.js`

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: INFO
- **Finding**: Excellent testing infrastructure: DockerfileMem, S3BACKEND=mem, docker-compose with full stack, multiple test configs, comprehensive functional tests, `yarn run mem_backend`.
- **Gap**: None. Sandbox environment well-supported.
- **Recommendation**: Document sandbox setup for agent developers.
- **Evidence**: `DockerfileMem`, `.github/docker/docker-compose.yaml`, `package.json`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
#### DATA-Q1: Sensitive Data Classification ⚡ (Tiered)
- **Severity**: INFO
- **Stage A**: Yes — CloudServer stores user-uploaded objects of any content type, object metadata with owner information (canonical IDs, account names), and access keys/secrets in `conf/authdata.json`.
- **B1 — API response scoping: CLEAR.** S3 API is content-agnostic by design — CloudServer does not echo credentials in responses. Auth/IAM uses Vault integration for credential validation; credentials are never returned. `GetBucketPolicy`/`GetBucketACL`/`ServiceGet` return canonical IDs and policy documents (intentional), not secrets.
- **B2 — Access control differentiation: CLEAR.** Every API call validates authorization via Vault-backed IAM before returning data. Bucket policies, bucket ACLs, and IAM policies are evaluated in `lib/api/apiUtils/authorization/permissionChecks.js` and `lib/metadata/metadataUtils.js`. No policy-bypass paths detected in read-only scope.
- **B3 — Formal classification metadata: INFO.** Native S3 primitives (object tags via `bucketPutTagging`/`objectGetTagging`, bucket-level SSE via `bucketPutEncryption`/SSE-KMS through KMIP and AWS KMS) provide the classification building blocks. No automatic enforcement; classification is an operator responsibility.
- **Overall**: Only B3 fires → **DATA-Q1 = INFO**. CloudServer provides S3 framework primitives for classification.
- **Recommendation (aspirational)**: Enable default bucket encryption globally; adopt object-tag–based classification conventions; integrate with Macie for automated sensitivity scanning where deployed.
- **Evidence**: `lib/auth/vault.js`, `lib/api/bucketGetPolicy.js`, `lib/api/bucketGetACL.js`, `lib/api/objectGetTagging.js`, `lib/api/bucketGetEncryption.js`, `lib/metadata/metadataUtils.js`, `lib/kms/wrapper.js`.

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Multi-region location constraints in `locationConfig.json`. Cross-region replication configurable. No application-level residency enforcement.
- **Gap**: No residency enforcement. Location constraints exist but don't restrict reads.
- **Recommendation**: Implement residency restrictions at agent orchestration layer.
- **Evidence**: `locationConfig.json`, `config.json`

#### DATA-Q3: Selective Query Support
- **Severity**: INFO
- **Finding**: S3-compatible pagination (max-keys, marker, continuation-token, prefix, delimiter). Metadata search with SQL-like WHERE. Hard limit 1000 items.
- **Gap**: None. Pagination well-implemented.
- **Recommendation**: No action required.
- **Evidence**: `lib/api/bucketGet.js`, `lib/api/metadataSearch.js`, `constants.js`

#### DATA-Q4: System of Record Designations
- **Severity**: INFO
- **Finding**: CloudServer IS the system of record for S3 object storage. Owns authoritative data, metadata, policies.
- **Gap**: None.
- **Recommendation**: Document as system of record.
- **Evidence**: `lib/metadata/wrapper.js`, `lib/data/wrapper.js`

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: INFO
- **Finding**: Last-Modified, ETag, versioning timestamps, x-amz-restore expiry, consistent reads via MongoDB primary.
- **Gap**: None. Temporal metadata comprehensive.
- **Recommendation**: No action required.
- **Evidence**: `lib/utilities/collectResponseHeaders.js`, `config.json`

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: Server access logs contain account names, user names, access key IDs, client IPs, object keys in plaintext. No PII scrubbing or masking.
- **Gap**: No PII redaction in logs.
- **Recommendation**: Add configurable PII redaction layer to serverAccessLogger.
- **Evidence**: `lib/utilities/serverAccessLogger.js`, `schema/server_access_log.schema.json`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: Content-MD5 validation, ETag integrity, configurable integrity checks. Prometheus metrics for counts and disk usage. No formal data quality scores.
- **Gap**: No data quality scoring (informational).
- **Recommendation**: Implement metadata enrichment for quality metrics if needed.
- **Evidence**: `config.json`, `lib/utilities/monitoringHandler.js`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: Versioned JSON schema for server access logs. S3 protocol implicit versioning. No explicit API versioning, no breaking change detection in CI, no Pact tests.
- **Gap**: No explicit API versioning. No breaking change detection.
- **Recommendation**: Add OpenAPI spec and schema diff checks to CI.
- **Evidence**: `schema/server_access_log.schema.json`, `.github/workflows/tests.yaml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: S3 standard field names (Key, ETag, LastModified, etc.). Descriptive server access log fields. No legacy abbreviations.
- **Gap**: None.
- **Recommendation**: No action required.
- **Evidence**: `lib/utilities/collectResponseHeaders.js`, `schema/server_access_log.schema.json`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal data catalog. Documentation in `docs/`. JSON schema for log format. S3 object metadata as lightweight metadata layer.
- **Gap**: No formal data catalog.
- **Recommendation**: Implement S3 tagging conventions for semantic annotation.
- **Evidence**: `docs/ARCHITECTURE.rst`, `schema/server_access_log.schema.json`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: Werelogs structured JSON logging. Proprietary `x-scal-request-uids` for correlation. `req_id` in server access logs. No OpenTelemetry, X-Ray, or W3C Trace Context.
- **Gap**: No standard distributed tracing. Proprietary correlation only.
- **Recommendation**: Integrate OpenTelemetry SDK. Add W3C Trace Context propagation.
- **Evidence**: `lib/utilities/logger.js`, `lib/server.js`, `lib/utilities/serverAccessLogger.js`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: INFO
- **Finding**: Comprehensive Prometheus alerting: endpoint degradation, system errors (3%/5% thresholds), listing latency (300ms/500ms), delete latency (500ms/1s), quota availability. Configurable thresholds.
- **Gap**: None. Alerting well-configured.
- **Recommendation**: Add agent-specific alerting rules.
- **Evidence**: `monitoring/alerts.yaml`, `lib/utilities/monitoringHandler.js`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: Custom Prometheus metrics: bucket counts, object counts, data ingested, disk usage, HTTP request duration/counts, quota metrics, lifecycle duration. Grafana dashboard provided.
- **Gap**: No agent-specific metric labels.
- **Recommendation**: Add agent-specific labels to distinguish agent traffic.
- **Evidence**: `lib/utilities/monitoringHandler.js`, `monitoring/dashboard.json`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK-QUALITY
- **Finding**: No IaC in repository. No Terraform, CloudFormation, CDK, Helm, Kustomize. Dockerfile and docker-compose for CI only. Open-source project — infra managed by deployers.
- **Gap**: No IaC for deployment infrastructure. No reference architecture.
- **Recommendation**: Add reference Helm charts or Terraform modules.
- **Evidence**: `Dockerfile`, `DockerfileMem`, `.github/docker/docker-compose.yaml`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: Extensive CI: linting, unit tests, functional tests (AWS SDK, s3cmd, s3curl), multiple backend tests, KMIP, SSE migration. CodeQL and dependency review. No explicit contract testing (Pact, OpenAPI diff).
- **Gap**: No API contract testing. No breaking change detection.
- **Recommendation**: Add OpenAPI spec validation and contract tests to CI.
- **Evidence**: `.github/workflows/tests.yaml`, `.github/workflows/codeql.yaml`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: Docker image tag-based releases. No blue/green, canary, or automated rollback. Manual image tag rollback only.
- **Gap**: No automated rollback. No canary deployment.
- **Recommendation**: Add Kubernetes deployment with rollback triggers.
- **Evidence**: `.github/workflows/release.yaml`, `Dockerfile`

#### ENG-Q4: API Test Coverage
- **Severity**: INFO
- **Finding**: Extensive test coverage: unit tests, AWS SDK functional tests, s3cmd, s3curl, raw node tests, healthcheck, backbeat, multiple backends, KMIP, SSE migration, utapi, SUR. Multi-backend coverage. nyc/istanbul coverage tracking.
- **Gap**: None. Test coverage is comprehensive.
- **Recommendation**: Add agent-specific test scenarios.
- **Evidence**: `.github/workflows/tests.yaml`, `package.json`, `tests/unit/`, `tests/functional/`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: INFO
- **Finding**: SSE-S3 (AES256) and SSE-KMS (KMIP, AWS KMS). Per-account default keys. Bucket-level encryption. KMS health checks. SSE migration support.
- **Gap**: Encryption opt-in per bucket (not mandatory by default).
- **Recommendation**: Enforce encryption for agent-accessed buckets. Use KMIP/AWS KMS in production.
- **Evidence**: `lib/kms/wrapper.js`, `config.json`, `lib/api/bucketPutEncryption.js`

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `lib/server.js` | API-Q1, API-Q5, API-Q7, API-Q8, AUTH-Q1, AUTH-Q4, OBS-Q1, STATE-Q5 |
| `lib/api/api.js` | API-Q1, API-Q2, API-Q3, API-Q4, AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4, STATE-Q2, STATE-Q5 |
| `lib/api/apiUtils/authorization/prepareRequestContexts.js` | AUTH-Q2, AUTH-Q3 |
| `lib/api/apiUtils/rateLimit/helpers.js` | API-Q8, STATE-Q5 |
| `lib/api/apiUtils/rateLimit/tokenBucket.js` | API-Q8, STATE-Q5 |
| `lib/api/apiUtils/rateLimit/refillJob.js` | STATE-Q5 |
| `lib/auth/vault.js` | AUTH-Q1, AUTH-Q4, AUTH-Q5, AUTH-Q7 |
| `lib/utilities/serverAccessLogger.js` | AUTH-Q6, DATA-Q6, OBS-Q1 |
| `lib/utilities/monitoringHandler.js` | OBS-Q2, OBS-Q3, DATA-Q7 |
| `lib/utilities/logger.js` | OBS-Q1 |
| `lib/utilities/collectResponseHeaders.js` | API-Q5, DATA-Q5, DISC-Q2 |
| `lib/kms/wrapper.js` | DATA-Q1, ENG-Q5 |
| `lib/kms/common.js` | ENG-Q5 |
| `lib/data/wrapper.js` | STATE-Q4, DATA-Q4 |
| `lib/metadata/wrapper.js` | STATE-Q4, DATA-Q4 |
| `lib/api/objectPut.js` | API-Q4, STATE-Q3 |
| `lib/api/objectGet.js` | STATE-Q3 |
| `lib/api/objectHead.js` | STATE-Q2 |
| `lib/api/objectRestore.js` | API-Q6 |
| `lib/api/bucketGet.js` | API-Q5, STATE-Q2, DATA-Q3, DISC-Q2 |
| `lib/api/serviceGet.js` | API-Q5 |
| `lib/api/bucketPutNotification.js` | API-Q7 |
| `lib/api/bucketGetNotification.js` | API-Q7 |
| `lib/api/bucketPutPolicy.js` | AUTH-Q2 |
| `lib/api/bucketPutEncryption.js` | DATA-Q1, ENG-Q5 |
| `lib/api/bucketPutVersioning.js` | STATE-Q1 |
| `lib/api/multipartDelete.js` | STATE-Q1 |
| `lib/api/multiObjectDelete.js` | STATE-Q1 |
| `lib/api/initiateMultipartUpload.js` | API-Q6, HITL-Q1 |
| `lib/api/completeMultipartUpload.js` | API-Q4, API-Q6 |
| `lib/api/listMultipartUploads.js` | DATA-Q3 |
| `lib/api/listParts.js` | API-Q6, DATA-Q3 |
| `lib/api/metadataSearch.js` | DATA-Q3 |
| `lib/api/objectPutRetention.js` | HITL-Q1, HITL-Q2 |
| `lib/api/objectPutLegalHold.js` | HITL-Q2 |
| `lib/api/bucketPutObjectLock.js` | HITL-Q1 |
| `lib/routes/routeBackbeat.js` | API-Q1, API-Q2 |
| `lib/routes/routeMetadata.js` | API-Q1, API-Q2 |
| `constants.js` | API-Q3, STATE-Q1, STATE-Q6, DATA-Q3, DATA-Q5, DATA-Q7, AUTH-Q1 |
| `index.js` | API-Q1 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `config.json` | API-Q7, API-Q8, AUTH-Q5, AUTH-Q6, STATE-Q4, STATE-Q5, STATE-Q6, DATA-Q1, DATA-Q2, DATA-Q5, DATA-Q7, ENG-Q5 |
| `conf/authdata.json` | AUTH-Q1, AUTH-Q5, AUTH-Q7, DATA-Q1 |
| `locationConfig.json` | DATA-Q2 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/tests.yaml` | DISC-Q1, ENG-Q2, ENG-Q4 |
| `.github/workflows/release.yaml` | ENG-Q3 |
| `.github/workflows/codeql.yaml` | ENG-Q2 |
| `.github/workflows/dependency-review.yaml` | ENG-Q2 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `Dockerfile` | ENG-Q1, ENG-Q3 |
| `DockerfileMem` | HITL-Q3, ENG-Q1 |
| `.github/docker/docker-compose.yaml` | HITL-Q3, ENG-Q1 |

### Schema Files
| File | Questions Referenced |
|------|---------------------|
| `schema/server_access_log.schema.json` | AUTH-Q6, DATA-Q6, DISC-Q1, DISC-Q2 |

### Monitoring
| File | Questions Referenced |
|------|---------------------|
| `monitoring/alerts.yaml` | OBS-Q2, OBS-Q3 |
| `monitoring/dashboard.json` | OBS-Q3 |

### Documentation
| File | Questions Referenced |
|------|---------------------|
| `docs/ARCHITECTURE.rst` | DISC-Q3 |
| `docs/MD_SEARCH.rst` | DISC-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `package.json` | API-Q5, HITL-Q3, DISC-Q1, ENG-Q4 |

### Test Files
| File | Questions Referenced |
|------|---------------------|
| `tests/unit/` | ENG-Q4 |
| `tests/functional/` | ENG-Q4 |
| `tests/locationConfig/` | HITL-Q3 |
