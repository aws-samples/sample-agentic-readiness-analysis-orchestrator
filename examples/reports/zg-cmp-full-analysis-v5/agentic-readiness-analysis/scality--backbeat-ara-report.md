# Agentic Readiness Analysis Report

**Target**: scality/backbeat
**Date**: 2025-01-30
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**TD Version**: 3g1ipe93e5d2wb6n5d4yqaf9
**Repository Type**: application
**Service Archetype**: orchestrator (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: javascript, storage, replication
**Context**: Scality backend engine for replication, lifecycle, and metadata workflows.

**Archetype Justification**: Backbeat coordinates 6+ downstream services (S3/CloudServer, Vault/IAM, MongoDB, Redis, Kafka, Zookeeper) to orchestrate multi-service replication, lifecycle, and metadata ingestion workflows. It consumes Kafka messages, coordinates cross-site data replication, and manages workflow state — matching the orchestrator pattern.

- **Surface flags**:
  - has_persistent_data_store: true (MongoDB for metadata/location-status, Redis for metrics/failure-tracking sorted sets)
  - has_http_rpc_surface: true (BackbeatServer.js on port 8900 — healthcheck, metrics, CRR retry, pause/resume, workflow configuration)
  - has_auth_surface: true (IP-based CIDR allowlist in BackbeatServer.js, service account credentials via AccountCredentials.js, role-based credentials via RoleCredentials.js/Vault)
  - has_write_operations: true (POST endpoints for retry CRR, pause/resume, workflow configuration; writes to Redis sorted sets and MongoDB; produces to Kafka topics)
  - has_logging_of_user_data: true (werelogs structured logging includes bucket names, object keys, version IDs, replication status, error details)

---

## Readiness Profile: Pilot-Ready (Safety Concerns)

**BLOCKERs**: 0 | **RISK-SAFETY**: 8 | **RISK-QUALITY**: 13 | **INFOs**: 20

Supervised pilot with elevated safety oversight: (1) all Pilot-Ready controls apply, (2) prioritize RISK-SAFETY remediation before expanding agent scope, (3) dedicated safety review cadence, (4) agent restricted to lowest-blast-radius operations until RISK-SAFETY count drops below 3.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 0 |
| RISK-SAFETY | 8 |
| RISK-QUALITY | 13 |
| INFO | 20 |
| N/A | 0 |
| Not Evaluated (extended) | 2 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 17
**Extended Questions Not Triggered**: 2
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: orchestrator (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

No BLOCKERs identified. All conditional BLOCKER questions (API-Q4, STATE-Q1, AUTH-Q6, DATA-Q2) resolved to lower severity under `read-only` agent_scope. API-Q1 passes (documented REST interface exists). AUTH-Q1 passes (machine identity authentication via Vault and IP-based access control). DATA-Q1 is recorded as INFO because the system primarily handles infrastructure metadata and service credentials managed through Vault, not end-user PII.

---

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: IAM-style policies in `policies/queue_populator_policy.json` and `policies/read_accounts.json` scope actions to `vaultadmin:GetAccountInfo` on `arn:aws:iam::*:root`. Per-extension service accounts exist (service-replication, service-lifecycle, service-gc, service-md-ingestion). However, the wildcard `*` in the Resource field grants access to all accounts. The IP-based `allowFrom` CIDR (`127.0.0.1/8`) is coarse-grained.
- **Gap**: Resource-level scoping uses wildcards. No per-agent permission granularity — all callers within the allowed CIDR range get identical access.
- **Compensating Controls**:
  - Restrict `allowFrom` CIDR to specific agent host IPs
  - Deploy an API gateway or service mesh for per-caller scoped permissions
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Replace wildcard Resource ARNs with specific account ARNs. Introduce per-caller identity-based access controls.
- **Evidence**: `policies/queue_populator_policy.json`, `policies/read_accounts.json`, `conf/config.json`

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: BackbeatServer.js validates HTTP methods (GET, POST, DELETE) per route. However, all clients within the `allowFrom` CIDR have access to all routes — there is no RBAC or ABAC enforcement.
- **Gap**: No action-level authorization beyond HTTP method matching. Any authorized caller can execute any action.
- **Compensating Controls**:
  - Limit agent access to GET-only endpoints via API gateway method-level restrictions
  - Use network segmentation to restrict POST endpoint access
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement route-level authorization middleware with per-principal access policies.
- **Evidence**: `lib/api/BackbeatServer.js`, `lib/api/routes.js`, `lib/api/BackbeatAPI.js`

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: werelogs structured logging logs clientIp, httpMethod, httpURL, httpCode per request. However, no immutable audit log configuration exists (no CloudTrail, S3 object lock, or tamper-evident storage).
- **Gap**: No immutable, tamper-evident audit log storage.
- **Compensating Controls**:
  - Forward werelogs to immutable log store (CloudWatch Logs with retention lock, S3 with Object Lock)
  - Enable CloudTrail at platform layer
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure immutable log shipping. Add agent identity fields to log entries.
- **Evidence**: `lib/api/BackbeatServer.js`, absence of CloudTrail/IaC

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: IP-based `allowFrom` changes require config modification and service restart. No instant per-agent credential revocation.
- **Gap**: No instant per-agent identity suspension mechanism.
- **Compensating Controls**:
  - Use Vault token revocation at platform layer
  - Deploy API gateway with per-client key management
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement authentication layer supporting per-agent credential revocation without restart.
- **Evidence**: `lib/api/BackbeatServer.js`, `conf/config.json`, `lib/credentials/RoleCredentials.js`

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No API-layer rate limiting. No rate limiting middleware, headers, or API Gateway throttling. Kafka consumer concurrency is internal flow control, not API rate limiting.
- **Gap**: Unlimited request rate from authorized callers at machine speed.
- **Compensating Controls**:
  - Deploy reverse proxy or API gateway with rate limiting
  - Implement in-process rate limiting middleware
- **Remediation Timeline**: 30 days
- **Recommendation**: Add rate limiting middleware and return `X-RateLimit-Remaining`/`Retry-After` headers.
- **Evidence**: `lib/api/BackbeatServer.js`, `package.json`

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: werelogs logs bucket names, object keys, version IDs, error details without redaction. No log scrubbing or PII masking middleware. Object keys may contain user-identifiable patterns.
- **Gap**: No PII redaction in logs.
- **Compensating Controls**:
  - Configure log output filters at platform layer to mask sensitive fields
  - Implement werelogs formatter that redacts sensitive patterns
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add log sanitization layer to mask sensitive fields before output.
- **Evidence**: `lib/api/BackbeatServer.js`, `lib/api/BackbeatAPI.js`, `lib/credentials/RoleCredentials.js`

#### STATE-Q1: Compensation and Rollback ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The replication workflow uses status tracking (PENDING → COMPLETED/FAILED/REPLICA). `retryFailedCRR` provides retry for failed operations. Failed entries tracked in Redis sorted sets. No formal saga pattern, no explicit undo/compensation endpoints.
- **Gap**: No formal compensation or rollback for multi-step operations. Relies on retry rather than compensation.
- **Compensating Controls**:
  - Retry mechanism (retryFailedCRR) provides eventual consistency
  - Status tracking enables manual intervention for stuck operations
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement explicit compensation logic for replication workflows. Add dead-letter mechanism.
- **Evidence**: `DESIGN.md`, `lib/api/BackbeatAPI.js`, `conf/config.json`

#### DATA-Q2: Data Residency and Sovereignty ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Cross-region data replication is core function. `bootstrapList` defines multi-site destinations including aws_s3, azure, gcp locations. No GDPR/LGPD compliance documentation. No data residency policy configuration in the application.
- **Gap**: No data residency policy enforcement or documentation in application layer.
- **Compensating Controls**:
  - Data residency enforcement at S3/CloudServer layer (replication rules define allowed destinations)
  - Read-only agent scope limits risk to metadata exposure, not data movement
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Document data residency boundaries. Add residency-aware metadata to configurations.
- **Evidence**: `conf/config.json`, `conf/locationConfig.json`, `DESIGN.md`

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI/AsyncAPI/GraphQL specs. Routes defined programmatically in `lib/api/routes.js`. Markdown docs exist but are not machine-readable.
- **Gap**: No machine-readable spec. Agent tool generation requires manual authoring.
- **Compensating Controls**:
  - Generate OpenAPI spec from route definitions as one-time effort
  - Use markdown docs + route definitions as manual tool source
- **Remediation Timeline**: 30 days
- **Recommendation**: Generate OpenAPI 3.0 spec. Automate spec generation from route metadata.
- **Evidence**: `lib/api/routes.js`, absence of spec files, `docs/*.md`

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Arsenal errors with `code` and `description` returned as JSON. Consistent error types. Missing `retryable` boolean field.
- **Gap**: No `retryable` field. Agents cannot distinguish retriable vs terminal errors programmatically.
- **Compensating Controls**:
  - Agent-side mapping of HTTP status codes (500/503 → retry; 400/403/404 → terminal)
- **Remediation Timeline**: 15–30 days
- **Recommendation**: Add `retryable` boolean to error response schema.
- **Evidence**: `lib/api/BackbeatServer.js` (Arsenal errors)

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Joi schema for config but not API contracts. No API versioning, schema registry, or breaking change detection in CI.
- **Gap**: No API versioning or schema contract enforcement.
- **Compensating Controls**:
  - Pin agent tool definitions to specific Backbeat versions
  - Add API integration tests for contract changes
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add API versioning. Implement OpenAPI diff in CI.
- **Evidence**: `lib/config.joi.js`, `lib/api/routes.js`, `.github/workflows/tests.yaml`

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: werelogs structured logging with request UIDs. Prometheus metrics. No OpenTelemetry/X-Ray. No traceparent propagation.
- **Gap**: No standardized distributed tracing across service boundaries.
- **Compensating Controls**:
  - werelogs request UIDs provide partial correlation
  - Kafka message keys provide per-object tracing
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add OpenTelemetry instrumentation. Propagate traceparent headers.
- **Evidence**: `lib/api/BackbeatServer.js`, `package.json`

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Prometheus alert rules in `monitoring/*/alerts.yaml` with CI test validation. Covers replication errors, RPO, latency. Missing: HTTP API endpoint-specific alerts.
- **Gap**: No API-endpoint-specific error rate and latency alerting.
- **Compensating Controls**:
  - Prometheus metrics endpoint enables custom alerting
  - Existing workflow alerts cover primary concerns
- **Remediation Timeline**: 30 days
- **Recommendation**: Add alerts for BackbeatServer HTTP endpoint error rates and latency.
- **Evidence**: `monitoring/replication/alerts.yaml`, `.github/workflows/alerts.yaml`

#### ENG-Q1: Infrastructure Governance — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No IaC (Terraform/CloudFormation/CDK/Helm). Configuration via JSON files and env vars. No drift detection.
- **Gap**: No IaC for agent-facing infrastructure.
- **Compensating Controls**:
  - Config changes go through git PR review
  - Docker builds are CI-controlled
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Define Kubernetes manifests or Helm charts. Implement GitOps.
- **Evidence**: Absence of IaC files, `conf/config.json`, `docker-entrypoint.sh`

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive CI/CD with functional API tests, unit tests, linting, coverage. No contract testing or breaking change detection.
- **Gap**: No API contract testing or breaking change detection in CI.
- **Compensating Controls**:
  - Functional API tests catch behavioral regressions
  - PR review provides human verification
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenAPI spec validation step. Implement consumer-driven contract tests.
- **Evidence**: `.github/workflows/tests.yaml`, `tests/functional/api/`

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Docker-based deployment with tagged images. No automated rollback, blue/green, or canary deployment.
- **Gap**: No automated rollback mechanism.
- **Compensating Controls**:
  - Docker image tags enable manual rollback
  - GitHub releases track versions
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement Kubernetes rolling update with automatic rollback on health check failure.
- **Evidence**: `Dockerfile`, `.github/workflows/docker-build.yaml`, `.github/workflows/release.yaml`

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Functional API tests at `tests/functional/api/routes.js` and `retry.js`. Unit tests in `tests/unit/`. Coverage collected via nyc/c8 in CI.
- **Gap**: No comprehensive API endpoint coverage verification. No response schema contract tests.
- **Compensating Controls**:
  - Existing functional tests cover critical paths
- **Remediation Timeline**: 30 days
- **Recommendation**: Expand API tests to validate response schemas for all endpoints.
- **Evidence**: `tests/functional/api/routes.js`, `tests/functional/api/retry.js`, `.github/workflows/tests.yaml`

#### API-Q6: Asynchronous Operation Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Backbeat's replication, lifecycle, and ingestion workflows are inherently long-running (minutes to hours). Kafka-based asynchronous processing handles workflow execution internally. However, the HTTP API surface does not expose formal async patterns — no job submission endpoint that returns a job ID, no polling endpoint for job status, and no webhook callback mechanism. The `retryFailedCRR` POST endpoint initiates retries but returns synchronously with results. The `getSiteFailedCRR` endpoint queries historical failures but is not a job-polling pattern.
- **Gap**: No formal async API patterns (job submission → polling → completion) on the HTTP surface. Agents cannot submit a replication task and poll for completion through the API.
- **Compensating Controls**:
  - Kafka topic events provide async completion signals (requires Kafka consumer, not HTTP)
  - Metrics endpoints (`/_/metrics/crr/<site>/progress`) provide indirect progress monitoring
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add async job API: POST to submit replication/lifecycle tasks returning a job ID, GET to poll job status by ID.
- **Evidence**: `lib/api/BackbeatAPI.js`, `lib/api/routes.js`, `DESIGN.md`

#### DATA-Q5: Temporal Metadata and Freshness — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: API responses include `LastModified` timestamps for objects (e.g., in `getFailedCRR` and `retryFailedCRR` responses). Redis sorted set scores use `Date.now()` timestamps for failure tracking. Replication latency is computed as `Date.now() - lastModified`. However, no `Cache-Control`, `X-Data-Age`, or freshness signaling headers exist on API responses. No timezone normalization documentation. No indication of whether data returned is current, cached, or eventually consistent — metrics are computed from Redis which uses in-memory counters with 5-minute intervals and 24-hour expiry.
- **Gap**: No freshness signaling on API responses. Agents cannot determine if metrics data is current or stale. Redis-based metrics have implicit staleness (5-minute aggregation windows) that is not communicated to callers.
- **Compensating Controls**:
  - `LastModified` field in object responses provides per-object temporal context
  - Metrics EXPIRY (86400s) and INTERVAL (300s) constants are known but not exposed to callers
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `Cache-Control` and `X-Data-Age` headers to metrics responses. Document temporal characteristics of each endpoint.
- **Evidence**: `lib/api/BackbeatAPI.js` (INTERVAL=300, EXPIRY=86400, LastModified in responses), `lib/api/Metrics.js`, `extensions/replication/tasks/UpdateReplicationStatus.js`

#### ENG-Q5: Encryption at Rest — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Backbeat uses MongoDB (metadata database) and Redis (metrics, failure tracking, sorted sets) as persistent data stores. No encryption-at-rest configuration exists in the application layer — MongoDB connection strings have no TLS/encryption options, Redis connections use plaintext. No KMS key references, no `kms_key_id`, no disk encryption configuration. The `conf/config.json` contains `certFilePaths` with empty values for key, cert, and ca. Replication tasks reference SSE/KMS for S3 object encryption (`SSEKMSKeyId` in `ReplicateObject.js`), but this is for replicated object data, not for Backbeat's own data stores.
- **Gap**: No encryption-at-rest for MongoDB and Redis data stores. No IaC defining encrypted storage volumes.
- **Compensating Controls**:
  - Enable MongoDB encryption at rest at the database layer (WiredTiger encryption)
  - Enable Redis encryption at rest via cloud provider managed service (ElastiCache)
  - Deploy on encrypted EBS volumes
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure MongoDB WiredTiger encryption. Use TLS for Redis connections. Define encrypted storage in IaC.
- **Evidence**: `conf/config.json` (empty certFilePaths, plaintext Redis/MongoDB connections), `extensions/replication/tasks/ReplicateObject.js` (SSEKMSKeyId for replicated objects only), absence of encryption IaC

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: CI provides sandbox with service containers (Redis, Kafka, MongoDB, Zookeeper) for automated testing. No documented staging environment with production-equivalent data shape. Docker Compose not provided for local staging.
- **Gap**: No production-like staging environment for agent testing. CI sandbox is ephemeral and test-scoped, not a persistent staging environment.
- **Compensating Controls**:
  - CI sandbox with real service containers provides functional validation
  - Docker-based deployment enables local environment creation
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document staging procedure. Create Docker Compose for local staging with seed data scripts.
- **Evidence**: `.github/workflows/tests.yaml`, `tests/config.json`, `Dockerfile`

---

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface
- **Severity**: INFO (compliant)
- **Finding**: REST interface on port 8900 with routes for healthcheck, metrics, CRR operations, pause/resume, and workflow configuration. Documented in `docs/healthcheck.md`, `docs/metrics.md`, `docs/pause-resume.md`.
- **Implication**: Agents can bind to the HTTP API for monitoring replication workflows.
- **Evidence**: `lib/api/BackbeatServer.js`, `lib/api/routes.js`, `docs/*.md`

### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO (compliant)
- **Finding**: Machine identity via IP-based CIDR allowlist, static account credentials, and Vault role-based temporary credentials. Per-extension service accounts enable principal attribution.
- **Implication**: Machine identity infrastructure exists for agent authentication.
- **Evidence**: `lib/credentials/AccountCredentials.js`, `lib/credentials/RoleCredentials.js`, `conf/config.json`

### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Finding**: Redis lock keys provide idempotency for CRR retry. Pause/resume inherently idempotent. Informational for read-only scope.
- **Evidence**: `lib/api/BackbeatAPI.js`

### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: JSON for business responses, Prometheus text format for monitoring endpoint.
- **Evidence**: `lib/api/BackbeatServer.js`

### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: Kafka topics emit events for all state changes. Redis pub/sub for pause/resume. No HTTP webhooks.
- **Evidence**: `conf/config.json`, `DESIGN.md`

### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit documentation or headers. Agents have no rate limit awareness.
- **Evidence**: `lib/api/BackbeatServer.js`

### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO (partially compliant)
- **Finding**: Vault assume-role propagates identity for replication. Request UIDs propagated. No explicit agent on-behalf-of flow.
- **Evidence**: `lib/credentials/RoleCredentials.js`

### AUTH-Q5: Credential Management
- **Severity**: INFO (partially compliant)
- **Finding**: Vault auto-rotation for production. Static dev credentials in `conf/authdata.json`. No hardcoded credentials in source.
- **Evidence**: `conf/authdata.json`, `lib/credentials/RoleCredentials.js`

### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO (partially compliant)
- **Finding**: Handles credentials (Vault-managed) and infrastructure metadata. No formal classification tags. Data is primarily infrastructure metadata, not end-user PII.
- **Evidence**: `conf/authdata.json`, `lib/credentials/RoleCredentials.js`, `conf/config.json`

### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO (scope-calibrated)
- **Finding**: Redis lock keys and Kafka offset management. Informational for read-only scope.
- **Evidence**: `lib/api/BackbeatAPI.js`, `lib/OffsetLedger.js`

### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: INFO (compliant)
- **Finding**: Well-implemented circuit breakers via breakbeat. Retry with exponential backoff per destination type.
- **Evidence**: `lib/CircuitBreaker.js`, `lib/BackbeatConsumer.js`, `conf/config.json`

### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO (scope-calibrated)
- **Finding**: Listing limit of 100 provides implicit bounds. Informational for read-only scope.
- **Evidence**: `lib/api/BackbeatAPI.js`

### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO (scope-calibrated)
- **Finding**: Operational states exist but are workflow states, not approval gates. Informational for read-only scope.
- **Evidence**: `DESIGN.md`, `lib/api/BackbeatAPI.js`

### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO (scope-calibrated)
- **Finding**: No approval gates. Informational for read-only scope.
- **Evidence**: `lib/api/BackbeatAPI.js`

### STATE-Q2: Queryable Current State
- **Severity**: INFO (compliant)
- **Finding**: Backbeat exposes queryable state via multiple GET endpoints: `/_/crr/status/<location>` returns pause/resume state per site; `/_/metrics/crr/<site>/all` returns current backlog, completions, throughput, and pending counts; `/_/crr/failed?site=<site>` returns failed CRR operations; `/_/healthcheck` returns Kafka consumer/producer health. Agents can read current workflow state before deciding next actions.
- **Implication**: Agents can query replication and lifecycle state programmatically before taking action.
- **Recommendation**: Consider consolidating state endpoints into a single comprehensive status API.
- **Evidence**: `lib/api/routes.js`, `lib/api/BackbeatAPI.js` (getServiceStatus, getSiteFailedCRR, getHealthcheck, getAllMetrics)

### DATA-Q3: Selective Query Support
- **Severity**: INFO (compliant)
- **Finding**: `getSiteFailedCRR` implements marker-based pagination with a `listingLimit` of 100 entries per response. Responses include `IsTruncated` boolean and `NextMarker` for cursor-based pagination. Metrics endpoints support per-site filtering via URL path parameters (e.g., `/_/metrics/crr/<site>/backlog`). Failed CRR queries support site filtering via `?site=<sitename>` query parameter and specific object lookup via `/_/crr/failed/<bucket>/<key>/<versionId>`.
- **Implication**: Agents can paginate through failed operations and filter by site, preventing unbounded result sets.
- **Recommendation**: Add sorting options and configurable page sizes.
- **Evidence**: `lib/api/BackbeatAPI.js` (`_getEntriesBySite`, `listingLimit = 100`, `IsTruncated`, `NextMarker`), `lib/api/routes.js`

### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality scores. Operational metrics track health but not quality.
- **Evidence**: `lib/api/Metrics.js`

### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO (compliant)
- **Finding**: Semantically clear names: Bucket, Key, VersionId, StorageClass. No legacy abbreviations.
- **Evidence**: `lib/api/BackbeatAPI.js`, `lib/api/routes.js`

### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal data catalog. Semantics documented in markdown and JSDoc.
- **Evidence**: `docs/metrics.md`, `DESIGN.md`

### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO (compliant)
- **Finding**: Rich business metrics: replication ops/bytes, RPO, throughput, circuit breaker state. Grafana dashboards and Prometheus alerts.
- **Evidence**: `lib/CircuitBreaker.js`, `monitoring/*/alerts.yaml`, `monitoring/*/dashboard.json`

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO (compliant)
- **Finding**: REST interface on port 8900 with documented routes (healthcheck, metrics, CRR operations, pause/resume, workflow configuration, Prometheus monitoring). Docs in `docs/healthcheck.md`, `docs/metrics.md`, `docs/pause-resume.md`.
- **Gap**: Markdown docs, not machine-readable spec.
- **Recommendation**: Formalize with OpenAPI 3.0 spec.
- **Evidence**: `lib/api/BackbeatServer.js`, `lib/api/routes.js`, `docs/*.md`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI/AsyncAPI/GraphQL/Smithy specs. Routes programmatic in `lib/api/routes.js`.
- **Gap**: No machine-readable spec.
- **Recommendation**: Generate OpenAPI 3.0 from routes.
- **Evidence**: `lib/api/routes.js`, absence of spec files

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: Arsenal errors with code/description as JSON. Missing `retryable` boolean.
- **Gap**: No retryable field.
- **Recommendation**: Add `retryable` boolean.
- **Evidence**: `lib/api/BackbeatServer.js`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Redis lock keys provide idempotency for retry. Pause/resume inherently idempotent.
- **Gap**: Informational for read-only scope.
- **Recommendation**: Add idempotency keys if write-enabled.
- **Evidence**: `lib/api/BackbeatAPI.js`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: JSON for business responses, Prometheus for monitoring.
- **Gap**: None.
- **Recommendation**: No action needed.
- **Evidence**: `lib/api/BackbeatServer.js`

#### API-Q6: Asynchronous Operation Support
- **Severity**: RISK-QUALITY
- **Finding**: Backbeat's core function is orchestrating long-running workflows (replication across sites can take minutes to hours, lifecycle transitions, metadata ingestion). Internally, Kafka provides asynchronous processing — the Queue Populator publishes entries, and Queue Processors consume and execute them asynchronously. However, the HTTP API surface lacks formal async patterns: `retryFailedCRR` (POST) initiates retries and returns synchronously with results; there is no job-submission endpoint returning a job ID, no polling endpoint for individual job status, and no webhook/callback mechanism. The `/_/metrics/crr/<site>/progress/<bucket>/<key>` endpoint provides indirect progress monitoring for replication objects but is not a formal async job-status API.
- **Gap**: No formal async API patterns (submit → poll → complete) on HTTP surface. Agents cannot submit a replication task via HTTP and poll for its completion.
- **Recommendation**: Implement async job API: POST endpoint to submit tasks returning a job ID, GET endpoint to poll job status by ID.
- **Evidence**: `lib/api/BackbeatAPI.js` (retryFailedCRR), `lib/api/routes.js` (progress route), `DESIGN.md` (Kafka async architecture)

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: Kafka topics emit state changes. Redis pub/sub for pause/resume. No HTTP webhooks.
- **Gap**: No webhook/EventBridge integration.
- **Recommendation**: Consider webhook adapter for agents.
- **Evidence**: `conf/config.json`, `DESIGN.md`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit docs or headers.
- **Gap**: No rate limit awareness for agents.
- **Recommendation**: Add rate limit headers when rate limiting implemented.
- **Evidence**: `lib/api/BackbeatServer.js`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO (compliant)
- **Finding**: IP-based CIDR, static account credentials, Vault role-based temporary credentials with per-extension service accounts.
- **Gap**: IP-based lacks per-principal granularity.
- **Recommendation**: Extend Vault auth to API surface.
- **Evidence**: `lib/credentials/AccountCredentials.js`, `lib/credentials/RoleCredentials.js`, `conf/config.json`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: Wildcard resources in IAM policies. Coarse IP-based access.
- **Gap**: No per-agent permission granularity.
- **Recommendation**: Replace wildcards. Add identity-based controls.
- **Evidence**: `policies/queue_populator_policy.json`, `conf/config.json`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: HTTP method validation per route. No RBAC/ABAC.
- **Gap**: No action-level auth beyond method matching.
- **Recommendation**: Implement per-principal route-level authorization.
- **Evidence**: `lib/api/BackbeatServer.js`, `lib/api/routes.js`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO (partially compliant)
- **Finding**: Vault assume-role with identity propagation. Request UIDs. No agent on-behalf-of flow.
- **Gap**: No agent-specific delegation.
- **Recommendation**: Add distinct agent roles if needed.
- **Evidence**: `lib/credentials/RoleCredentials.js`

#### AUTH-Q5: Credential Management
- **Severity**: INFO (partially compliant)
- **Finding**: Vault auto-rotation for production. Static dev credentials.
- **Gap**: Dev credentials in git.
- **Recommendation**: Exclude `conf/authdata.json` from production.
- **Evidence**: `conf/authdata.json`, `lib/credentials/RoleCredentials.js`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: werelogs logs request details. No immutable storage.
- **Gap**: No tamper-evident audit trail.
- **Recommendation**: Ship logs to immutable store.
- **Evidence**: `lib/api/BackbeatServer.js`, absence of CloudTrail

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: IP allowlist requires restart to change. No instant revocation.
- **Gap**: No instant per-agent suspension.
- **Recommendation**: Add API gateway with key revocation.
- **Evidence**: `lib/api/BackbeatServer.js`, `conf/config.json`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Status tracking (PENDING/COMPLETED/FAILED/REPLICA). Retry via retryFailedCRR. No formal saga.
- **Gap**: No formal compensation logic.
- **Recommendation**: Implement compensation for multi-step workflows.
- **Evidence**: `DESIGN.md`, `lib/api/BackbeatAPI.js`

#### STATE-Q2: Queryable Current State
- **Severity**: INFO (compliant)
- **Finding**: Backbeat exposes current state through multiple queryable GET endpoints: (1) `/_/crr/status/<location>` and `/_/ingestion/status/<location>` and `/_/lifecycle/status/<location>` return pause/resume state per site via `getServiceStatus`; (2) `/_/metrics/crr/<site>/all` returns current backlog (opsPending, bytesPending), completions (opsDone, bytesDone), throughput, and failure counts; (3) `/_/crr/failed?site=<site>&marker=<marker>` returns paginated list of failed CRR operations with object details; (4) `/_/healthcheck` returns Kafka consumer/producer connectivity state. Agents can inspect workflow state before deciding actions.
- **Gap**: No single unified state endpoint — state is distributed across metrics, status, and failure endpoints.
- **Recommendation**: Consider a consolidated state summary endpoint combining status, metrics, and health.
- **Evidence**: `lib/api/routes.js` (status, metrics, failed, healthcheck routes), `lib/api/BackbeatAPI.js` (getServiceStatus, getAllMetrics, getSiteFailedCRR, getHealthcheck)

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Redis lock keys and Kafka offset management. No ETags.
- **Gap**: Informational for read-only scope.
- **Recommendation**: Add ETags if write-enabled.
- **Evidence**: `lib/api/BackbeatAPI.js`, `lib/OffsetLedger.js`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: INFO (compliant)
- **Finding**: breakbeat circuit breakers with Prometheus metrics. Retry with exponential backoff per destination.
- **Gap**: None.
- **Recommendation**: Expose circuit breaker state via API.
- **Evidence**: `lib/CircuitBreaker.js`, `lib/BackbeatConsumer.js`, `conf/config.json`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No API-layer rate limiting.
- **Gap**: Unlimited request rate.
- **Recommendation**: Add rate limiting middleware.
- **Evidence**: `lib/api/BackbeatServer.js`, `package.json`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Listing limit of 100. No per-agent caps.
- **Gap**: Informational for read-only scope.
- **Recommendation**: Add per-agent limits if write-enabled.
- **Evidence**: `lib/api/BackbeatAPI.js`

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
- **Finding**: Workflow states (PENDING/COMPLETED/FAILED), not approval gates.
- **Gap**: Informational for read-only scope.
- **Recommendation**: No action for read-only.
- **Evidence**: `DESIGN.md`, `lib/api/BackbeatAPI.js`

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No approval gates. POST operations execute immediately.
- **Gap**: Informational for read-only scope.
- **Recommendation**: No action for read-only.
- **Evidence**: `lib/api/BackbeatAPI.js`

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: CI provides sandbox with service containers (Redis, Kafka, MongoDB, Zookeeper) for automated testing via GitHub Actions. No documented staging environment with production-equivalent data shape. No Docker Compose for local staging. No seed data scripts for realistic testing.
- **Gap**: No production-like staging environment for agent testing. CI sandbox is ephemeral and test-scoped.
- **Recommendation**: Document staging procedure. Create Docker Compose for local staging with seed data scripts.
- **Evidence**: `.github/workflows/tests.yaml`, `tests/config.json`, `Dockerfile`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO (partially compliant)
- **Finding**: Handles credentials (Vault-managed) and infrastructure metadata (bucket names, keys, version IDs). No formal classification tags. Primarily infrastructure metadata, not end-user PII.
- **Gap**: No formal classification framework.
- **Recommendation**: Add classification tags. Document sensitivity levels.
- **Evidence**: `conf/authdata.json`, `lib/credentials/RoleCredentials.js`, `conf/config.json`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Cross-region replication is core function. No residency policy in application.
- **Gap**: No data residency controls.
- **Recommendation**: Document residency boundaries. Add residency-aware metadata.
- **Evidence**: `conf/config.json`, `conf/locationConfig.json`, `DESIGN.md`

#### DATA-Q3: Selective Query Support
- **Severity**: INFO (compliant)
- **Finding**: `getSiteFailedCRR` implements marker-based pagination with a hard `listingLimit` of 100 entries per response. The response includes `IsTruncated` (boolean) and `NextMarker` (integer score) for cursor-based pagination. Metrics endpoints support per-site filtering via URL path parameters (e.g., `/_/metrics/crr/<site>/backlog` where `<site>` can be a specific site name or `all`). Failed CRR queries support site filtering via `?site=<sitename>` query parameter and specific object lookup via `/_/crr/failed/<bucket>/<key>/<versionId>`. Result sets are bounded: listing is capped at 100 entries, metrics are aggregated.
- **Gap**: No configurable page size (hardcoded at 100). No sorting options beyond Redis sorted set score order.
- **Recommendation**: Add configurable `limit` query parameter. Consider sorting options.
- **Evidence**: `lib/api/BackbeatAPI.js` (`_getEntriesBySite`, `listingLimit = 100`, `IsTruncated`, `NextMarker`), `lib/api/routes.js`

#### DATA-Q4: System of Record Designations
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `orchestrator`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK-QUALITY
- **Finding**: API responses include `LastModified` timestamps for objects in `getFailedCRR` and `retryFailedCRR` responses. Redis sorted set scores use `Date.now()` millisecond timestamps for failure tracking and marker-based pagination. Replication latency metrics are computed using `Date.now() - lastModified` (in `UpdateReplicationStatus.js`, `ReplicateObject.js`). Metrics use 5-minute intervals (INTERVAL=300) with 24-hour expiry (EXPIRY=86400). However: no `Cache-Control`, `X-Data-Age`, or `last_refreshed` headers on API responses; no documentation of data freshness characteristics; no indication to callers whether metrics data is current, aggregated, or stale; no timezone normalization documentation (uses JavaScript `Date.now()` which returns UTC milliseconds).
- **Gap**: No freshness signaling headers on API responses. Agents cannot programmatically determine if metrics data is current or stale. 5-minute aggregation window creates implicit staleness not communicated to callers.
- **Recommendation**: Add `Cache-Control: max-age=300` to metrics responses. Add `X-Data-Age` header. Document temporal characteristics per endpoint.
- **Evidence**: `lib/api/BackbeatAPI.js` (INTERVAL=300, EXPIRY=86400, LastModified in responses), `lib/api/Metrics.js`, `extensions/replication/tasks/UpdateReplicationStatus.js` (replication latency computation)

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: Bucket names, object keys, version IDs logged without redaction. No masking middleware.
- **Gap**: No PII redaction.
- **Recommendation**: Add log sanitization layer.
- **Evidence**: `lib/api/BackbeatServer.js`, `lib/api/BackbeatAPI.js`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality scores. Operational metrics only.
- **Gap**: No quality monitoring.
- **Recommendation**: Add quality metrics.
- **Evidence**: `lib/api/Metrics.js`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: Joi schema for config only. No API versioning, schema registry, or breaking change detection.
- **Gap**: No API versioning or contract enforcement.
- **Recommendation**: Add versioning and breaking change detection.
- **Evidence**: `lib/config.joi.js`, `lib/api/routes.js`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO (compliant)
- **Finding**: Clear names: Bucket, Key, VersionId, StorageClass, opsPending, bytesDone.
- **Gap**: None.
- **Recommendation**: No action needed.
- **Evidence**: `lib/api/BackbeatAPI.js`, `lib/api/routes.js`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal catalog. Docs in markdown and JSDoc.
- **Gap**: No machine-readable catalog.
- **Recommendation**: Publish via OpenAPI spec.
- **Evidence**: `docs/metrics.md`, `DESIGN.md`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: werelogs with request UIDs. Prometheus metrics. No OpenTelemetry/X-Ray.
- **Gap**: No standardized distributed tracing.
- **Recommendation**: Add OpenTelemetry.
- **Evidence**: `lib/api/BackbeatServer.js`, `package.json`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: Prometheus alerts for workflows (replication, lifecycle, notification). Missing HTTP endpoint alerts.
- **Gap**: No API-specific alerting.
- **Recommendation**: Add HTTP endpoint alerts.
- **Evidence**: `monitoring/*/alerts.yaml`, `.github/workflows/alerts.yaml`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO (compliant)
- **Finding**: Rich metrics: ops/bytes (pending/done/failed), RPO, throughput, circuit breaker. Dashboards and alerts.
- **Gap**: None.
- **Recommendation**: Expose KPIs via API endpoint.
- **Evidence**: `lib/CircuitBreaker.js`, `monitoring/*/dashboard.json`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance
- **Severity**: RISK-QUALITY
- **Finding**: No IaC. JSON config and env vars. No drift detection.
- **Gap**: No IaC for agent-facing infrastructure.
- **Recommendation**: Define Helm charts or Kubernetes manifests.
- **Evidence**: Absence of IaC, `conf/config.json`, `docker-entrypoint.sh`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: CI/CD with functional tests. No contract testing.
- **Gap**: No breaking change detection.
- **Recommendation**: Add OpenAPI validation and contract tests.
- **Evidence**: `.github/workflows/tests.yaml`, `tests/functional/api/`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: Docker images with tags. No automated rollback.
- **Gap**: Manual rollback only.
- **Recommendation**: Add Kubernetes rolling update with auto-rollback.
- **Evidence**: `Dockerfile`, `.github/workflows/release.yaml`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: Functional API tests exist. Coverage collected. No schema validation tests.
- **Gap**: No comprehensive schema coverage.
- **Recommendation**: Expand tests to validate response schemas.
- **Evidence**: `tests/functional/api/routes.js`, `tests/functional/api/retry.js`

#### ENG-Q5: Encryption at Rest
- **Severity**: RISK-QUALITY
- **Finding**: Backbeat uses MongoDB (`metadata` database via `queuePopulator.mongo` config) and Redis (port 6379) as persistent data stores for operational state, metrics, and failure tracking. No encryption-at-rest configuration exists in the application layer: MongoDB connection string (`localhost:27017,localhost:27018,localhost:27019`) has no TLS/SSL parameters; Redis connection (`localhost:6379`) uses plaintext. `conf/config.json` contains `certFilePaths` with empty values (`"key": "", "cert": "", "ca": ""`). No KMS key references, no `kms_key_id`, no IaC defining encrypted storage volumes. The `extensions/replication/tasks/ReplicateObject.js` references `SSEKMSKeyId` for S3 object encryption during replication, but this encrypts replicated object data at the destination — not Backbeat's own MongoDB/Redis data stores.
- **Gap**: No encryption-at-rest for MongoDB and Redis data stores. No IaC defining encrypted storage. Empty TLS certificate paths suggest TLS is not configured.
- **Recommendation**: Configure MongoDB WiredTiger encryption at rest. Use TLS for Redis connections. Populate `certFilePaths` in config. Define encrypted storage volumes in IaC.
- **Evidence**: `conf/config.json` (empty certFilePaths, plaintext Redis/MongoDB connections), `extensions/replication/tasks/ReplicateObject.js` (SSEKMSKeyId for replicated objects only), absence of encryption IaC

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| lib/api/BackbeatServer.js | API-Q1, API-Q3, API-Q5, API-Q8, AUTH-Q1, AUTH-Q3, AUTH-Q6, AUTH-Q7, STATE-Q5, DATA-Q6 |
| lib/api/BackbeatAPI.js | API-Q1, API-Q4, API-Q6, AUTH-Q3, STATE-Q1, STATE-Q2, STATE-Q3, STATE-Q6, DATA-Q3, DATA-Q5, DATA-Q6, HITL-Q1, HITL-Q2 |
| lib/api/routes.js | API-Q1, API-Q2, API-Q6, API-Q7, AUTH-Q3, STATE-Q2, DATA-Q3, DISC-Q1, DISC-Q2 |
| lib/credentials/AccountCredentials.js | AUTH-Q1, AUTH-Q4, AUTH-Q5 |
| lib/credentials/RoleCredentials.js | AUTH-Q1, AUTH-Q4, AUTH-Q5, AUTH-Q7, DATA-Q6 |
| lib/clients/VaultClientCache.js | AUTH-Q7 |
| lib/CircuitBreaker.js | STATE-Q4, OBS-Q3 |
| lib/BackbeatConsumer.js | STATE-Q4 |
| lib/OffsetLedger.js | STATE-Q3 |
| lib/config.joi.js | DISC-Q1 |
| lib/BackbeatMetadataProxy.js | AUTH-Q4 |
| lib/api/Metrics.js | DATA-Q5, DATA-Q7 |
| extensions/replication/tasks/UpdateReplicationStatus.js | DATA-Q5 |
| extensions/replication/tasks/ReplicateObject.js | ENG-Q5 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| conf/config.json | AUTH-Q1, AUTH-Q2, AUTH-Q5, AUTH-Q7, STATE-Q1, STATE-Q4, STATE-Q5, API-Q7, DATA-Q2, ENG-Q5 |
| conf/authdata.json | AUTH-Q1, AUTH-Q5, DATA-Q1 |
| conf/locationConfig.json | DATA-Q2 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| .github/workflows/tests.yaml | ENG-Q2, ENG-Q4, HITL-Q3 |
| .github/workflows/release.yaml | ENG-Q3 |
| .github/workflows/docker-build.yaml | ENG-Q1, ENG-Q3 |
| .github/workflows/alerts.yaml | OBS-Q2 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| Dockerfile | ENG-Q1, ENG-Q3, HITL-Q3 |
| docker-entrypoint.sh | ENG-Q1 |

### IAM Policies
| File | Questions Referenced |
|------|---------------------|
| policies/queue_populator_policy.json | AUTH-Q2 |
| policies/read_accounts.json | AUTH-Q2 |

### Documentation
| File | Questions Referenced |
|------|---------------------|
| DESIGN.md | API-Q1, API-Q6, API-Q7, STATE-Q1, DATA-Q2, HITL-Q1, DISC-Q3 |
| docs/healthcheck.md | API-Q1, DISC-Q3 |
| docs/metrics.md | API-Q1, DISC-Q3 |
| docs/pause-resume.md | API-Q1 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| package.json | STATE-Q4, STATE-Q5, OBS-Q1 |

### Monitoring
| File | Questions Referenced |
|------|---------------------|
| monitoring/replication/alerts.yaml | OBS-Q2, OBS-Q3 |
| monitoring/lifecycle/alerts.yaml | OBS-Q2 |
| monitoring/replication/dashboard.json | OBS-Q3 |

### Test Files
| File | Questions Referenced |
|------|---------------------|
| tests/functional/api/routes.js | ENG-Q4 |
| tests/functional/api/retry.js | ENG-Q4 |
| tests/config.json | HITL-Q3 |
