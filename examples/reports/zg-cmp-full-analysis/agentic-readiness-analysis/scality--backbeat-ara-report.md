# Agentic Readiness Analysis Report

**Target**: scality/backbeat
**Date**: 2026-04-29
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**Repository Type**: application
**Service Archetype**: orchestrator (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: javascript, storage, replication
**Context**: Scality backend engine for replication, lifecycle, and metadata workflows.

**Archetype Justification**: Backbeat coordinates multi-service workflows by consuming events from MongoDB oplog, publishing to Kafka topics, and orchestrating replication/lifecycle tasks across multiple sites. It calls 6+ downstream services (S3/CloudServer, Vault, Kafka, Zookeeper, MongoDB, Redis), exhibiting high fan-out characteristic of an orchestrator archetype.

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 2 | **RISK-SAFETY**: 9 | **RISK-QUALITY**: 15 | **INFOs**: 15

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 2 |
| RISK-SAFETY | 9 |
| RISK-QUALITY | 15 |
| INFO | 15 |
| N/A | 0 |
| Not Evaluated (extended) | 2 |
| **Total** | **43** |

*Note: 17 extended questions triggered (evaluated), 2 not triggered.*

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 17
**Extended Questions Not Triggered**: 2
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: orchestrator (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: The Backbeat REST API (port 8900) authenticates callers exclusively via IP allowlist (`ipCheck.ipMatchCidrList` against `healthChecks.allowFrom` in `conf/config.json`). The default allowlist is `["127.0.0.1/8", "::1"]`. There is no OAuth2 client credentials flow, no API key authentication with principal attribution, no mTLS, and no service account mechanism for API callers. While `CredentialsManager.js` supports service accounts (`authTypeService`, `authTypeAccount`) and STS `AssumeRole` for downstream S3/Vault interactions, the Backbeat API itself has no machine identity authentication.
- **Gap**: No mechanism to authenticate individual agent identities on the Backbeat REST API. IP allowlisting provides network-level access control but cannot distinguish between different callers from the same IP range. All callers from allowed IPs are treated identically with no principal attribution in audit logs.
- **Remediation**:
  - **Immediate**: Add API key or bearer token authentication to `BackbeatServer._isValidRequest()` with principal attribution. Each agent identity should receive a unique API key that is logged with every request.
  - **Target State**: The Backbeat API supports machine identity authentication (API key with principal attribution or OAuth2 client credentials), and every request is logged with the authenticated principal identity.
  - **Estimated Effort**: Medium (2–4 weeks)
  - **Dependencies**: AUTH-Q6 (audit logging should capture the new principal identity)
- **Evidence**: `lib/api/BackbeatServer.js` (lines: `_isValidRequest` method using `ipCheck.ipMatchCidrList`), `conf/config.json` (`server.healthChecks.allowFrom`)

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: Backbeat processes object metadata, bucket names, object keys, replication credentials, and cross-region replication data. No data classification tags, field-level encryption, or PII detection controls are present. Object metadata is processed by `ObjectQueueEntry` and transmitted across replication sites without classification awareness. The `conf/authdata.json` file contains access/secret key pairs (sample values, but the pattern supports real credentials). No Amazon Macie integration or equivalent PII detection.
- **Gap**: No sensitive data classification at any level. Object keys and metadata may contain PII (e.g., user-identifiable bucket names, object keys with personal information). Replication credentials are handled but not classified as sensitive data.
- **Remediation**:
  - **Immediate**: Classify data fields processed by Backbeat — identify which object metadata fields may contain PII, which contain credentials, and which are operational metrics. Tag the data classification in documentation.
  - **Target State**: Sensitive data fields are classified and tagged. Field-level access controls prevent an agent from retrieving credential material without explicit authorization. PII-bearing fields are identified and protected.
  - **Estimated Effort**: Medium (4–6 weeks)
  - **Dependencies**: DATA-Q6 (PII redaction in logs should follow classification)
- **Evidence**: `lib/models/ObjectQueueEntry.js` (implicit), `conf/authdata.json`, `lib/credentials/CredentialsManager.js`, `extensions/replication/utils/ObjectFailureEntry.js`

---

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: For downstream S3/Vault interactions, the system uses per-extension service accounts (`service-replication`, `service-lifecycle`, `service-gc`, `service-md-ingestion`) and STS `AssumeRole` with role ARNs scoped to specific accounts. However, the Backbeat REST API itself has no per-identity permission scoping. All callers from allowed IP ranges have identical access to all endpoints — healthcheck, metrics, pause/resume, retry, and workflow configuration.
- **Gap**: No mechanism to grant an agent identity read-only access to metrics endpoints while denying access to pause/resume or retry endpoints. The IP allowlist is binary: full access or no access.
- **Compensating Controls**:
  - Network segmentation: restrict agent traffic to a specific IP range that only reaches read-only endpoints via a reverse proxy
  - Deploy a lightweight API gateway in front of the Backbeat API that enforces per-identity route-level authorization
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement route-level authorization on the Backbeat API, allowing different agent identities to access different endpoint groups (e.g., read-only metrics vs. operational controls).
- **Evidence**: `lib/api/BackbeatServer.js` (`_isValidRequest`), `conf/config.json` (`server.healthChecks.allowFrom`), `lib/api/routes.js`

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No RBAC, ABAC, or action-level authorization exists on the Backbeat API. All callers from allowed IPs can invoke any endpoint including destructive operations (POST to retry, POST to pause/resume, POST to apply workflow configuration, DELETE scheduled resume). The `routes.js` file defines both GET (read) and POST/DELETE (write) routes, but no authorization differentiates access to them.
- **Gap**: An agent intended for read-only metrics monitoring has the same access as an operator performing pause/resume operations. No `canRead`/`canWrite` permission checks exist.
- **Compensating Controls**:
  - Deploy an API gateway that maps agent identities to allowed HTTP methods (GET only for read-only agents)
  - Use network-level controls to expose only GET endpoints to agent traffic
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add middleware to BackbeatServer that checks the caller's identity (once AUTH-Q1 is resolved) against an allowed-actions list per identity.
- **Evidence**: `lib/api/BackbeatServer.js`, `lib/api/routes.js` (POST/DELETE routes alongside GET routes)

#### AUTH-Q6: Immutable Audit Logging ⚡

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: `BackbeatServer._logRequestEnd()` logs `clientIp`, `httpMethod`, `httpURL`, `httpCode`, and `description` using werelogs. Structured JSON logging is present throughout the codebase. However, there is no immutable log storage configuration (no CloudTrail, no S3 object lock, no tamper-evident logging). Log retention policies are not defined. The authenticated principal is not logged because no principal-based authentication exists (AUTH-Q1).
- **Gap**: Logs are structured but not immutable or tamper-evident. No authenticated principal is recorded per request. No CloudWatch log retention or S3 bucket with object lock for log storage.
- **Compensating Controls**:
  - Forward werelogs output to a centralized logging system with write-once storage
  - Enable CloudTrail logging at the infrastructure level for API Gateway if one is added
- **Remediation Timeline**: 30–60 days
- **Recommendation**: After resolving AUTH-Q1, include the authenticated principal in every log entry. Configure log forwarding to immutable storage (S3 with object lock or CloudWatch Logs with retention policy).
- **Evidence**: `lib/api/BackbeatServer.js` (`_logRequestEnd` method), `conf/config.json` (`log` section)

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The only access control mechanism is the IP allowlist in `conf/config.json`. There is no mechanism to suspend or revoke individual agent identities — only the entire IP range can be modified, which requires a configuration change and service restart. No API key revocation, no IAM role deactivation, no Cognito user disable.
- **Gap**: Cannot isolate a misbehaving agent without affecting all callers from the same IP range. Suspension requires config file modification and service restart.
- **Compensating Controls**:
  - Firewall rules to block a specific agent IP address at the network level
  - API gateway with per-key revocation capability
- **Remediation Timeline**: 30–60 days (dependent on AUTH-Q1 resolution)
- **Recommendation**: Implement API key-based authentication (AUTH-Q1) with a revocation mechanism — deleting or disabling an API key should immediately deny that agent's access.
- **Evidence**: `lib/api/BackbeatServer.js` (`_isValidRequest`), `conf/config.json` (`server.healthChecks.allowFrom`)

#### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Backbeat has a retry mechanism for failed CRR operations: failed entries are stored in Redis sorted sets with timestamps, and the `retryFailedCRR` endpoint re-queues them through Kafka topics. The `_applyRetryLockKey` method prevents duplicate retries. Replication status tracking (PENDING → COMPLETED/FAILED) provides state machine semantics. Kafka offset management provides at-least-once delivery. However, there is no formal saga pattern, no compensating transactions, and no explicit undo/rollback endpoints for multi-step replication workflows.
- **Gap**: If a multi-step replication operation fails mid-sequence (e.g., data copied to destination but metadata update fails), there is no automated compensation. The system relies on retry and eventual consistency rather than explicit rollback.
- **Compensating Controls**:
  - The retry mechanism (`retryFailedCRR`) serves as a partial compensation pattern
  - Kafka's at-least-once delivery ensures failed messages are re-processed
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Document the failure modes and recovery procedures for multi-step replication operations. Consider implementing explicit compensation actions for partially completed replication tasks.
- **Evidence**: `lib/api/BackbeatAPI.js` (`retryFailedCRR`, `_applyRetryLockKey`, `_pushToCRRRetryKafkaTopics`), `extensions/replication/constants.js`

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Kafka consumer-level concurrency controls exist: `BackbeatConsumer` has `_concurrency` (default: 1) and `_maxQueued` (default: 1000) settings that limit parallel processing. Each processor has configurable concurrency (e.g., `queueProcessor.concurrency: 10`). However, the Backbeat REST API on port 8900 has **no rate limiting** — no API Gateway throttling, no WAF rate rules, no express-rate-limit or equivalent middleware. Any caller from an allowed IP can make unlimited requests.
- **Gap**: No rate limiting on the REST API endpoint. A runaway agent loop could overwhelm the Backbeat API server. While Kafka consumers have concurrency limits, the API itself is unprotected.
- **Compensating Controls**:
  - Deploy a reverse proxy (nginx) with rate limiting in front of the Backbeat API
  - The single-worker Clustering (WORKERS=1) in BackbeatServer provides implicit request serialization
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add rate limiting middleware to BackbeatServer or deploy an API gateway with throttling configuration in front of port 8900.
- **Evidence**: `lib/api/BackbeatServer.js` (no rate limiting), `lib/BackbeatConsumer.js` (`_concurrency`, `_maxQueued`), `conf/config.json` (concurrency settings)

#### DATA-Q2: Data Residency and Sovereignty ⚡

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Cross-region replication is the core function of Backbeat. The `bootstrapList` in `conf/config.json` defines destination sites including `aws_s3` locations. Replication copies data across geographic regions by design. No data residency constraints are documented or enforced in code. No GDPR/LGPD compliance references found. No region-specific filtering or data sovereignty checks.
- **Gap**: An agent querying Backbeat metrics or failed CRR operations would receive object keys, bucket names, and storage class information for data that may be subject to residency requirements. No controls prevent exposure of residency-sensitive metadata through the API.
- **Compensating Controls**:
  - Restrict agent access to aggregate metrics only (no object-level details)
  - Document which API endpoints expose cross-region metadata
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document data residency implications of the Backbeat API responses. Add metadata tagging that marks which objects/buckets are subject to residency constraints. Consider filtering API responses to exclude residency-sensitive details.
- **Evidence**: `conf/config.json` (`extensions.replication.destination.bootstrapList`), `lib/api/BackbeatAPI.js` (`getFailedCRR`, `getSiteFailedCRR`)

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: werelogs is used throughout the codebase for structured JSON logging. Object keys, bucket names, version IDs, storage classes, and client IP addresses are logged freely. `BackbeatServer._logRequestEnd` logs `clientIp`, `httpURL`. `BackbeatAPI` logs bucket names, object keys, and error details. No log scrubbing middleware, no PII masking libraries, no regex patterns for PII detection in logging utilities.
- **Gap**: Object keys and bucket names may contain PII (e.g., user identifiers in key paths). These are logged without redaction. Client IP addresses are logged without masking.
- **Compensating Controls**:
  - Configure log retention policies to limit exposure duration
  - Restrict log access to authorized operators only
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement log scrubbing for object keys and bucket names that match PII patterns. Add a logging middleware that redacts or hashes potentially sensitive fields before they reach log storage.
- **Evidence**: `lib/api/BackbeatServer.js` (`_logRequestEnd`), `lib/api/BackbeatAPI.js` (multiple logging calls with bucket/key details)

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Circuit breakers are implemented via the `breakbeat` library (`CircuitBreaker` class). `BackbeatConsumer` imports and uses `CircuitBreaker` with state-change handlers that pause Kafka consumption when tripped (`BreakerState.Tripped`) and resume when nominal (`BreakerState.Nominal`). Circuit breaker state is exported as Prometheus metrics (`s3_circuit_breaker` gauge, `s3_circuit_breaker_errors_count` counter). Exponential backoff retry is configured per destination type in `conf/config.json` (e.g., `aws_s3.backoff.min: 60000, max: 900000, factor: 1.5, jitter: 0.1`). However, the REST API layer (`lib/api/`) has no circuit breaker, retry, or timeout logic for its own downstream calls (e.g., S3 metadata retrieval during `retryFailedCRR`, Redis calls for failed CRR lookups).
- **Gap**: Circuit breakers protect Kafka consumers but not the REST API's downstream calls. An agent calling the Backbeat REST API triggers synchronous downstream calls to S3 and Redis that lack circuit breaker protection. A runaway agent loop hitting the retry endpoint could cascade failures to downstream services without tripping any circuit breaker.
- **Compensating Controls**:
  - Kafka-level circuit breakers (`lib/BackbeatConsumer.js`) protect the asynchronous processing pipeline from cascading failures
  - Exponential backoff retry is configured per destination type in `conf/config.json`
  - Prometheus metrics (`s3_circuit_breaker` gauge) provide visibility into circuit breaker state
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add circuit breakers for the REST API's synchronous downstream calls using the existing `breakbeat` library. Prioritize S3 metadata retrieval during `retryFailedCRR` and Redis calls in `BackbeatAPI`.
- **Evidence**: `lib/BackbeatConsumer.js` (CircuitBreaker usage), `lib/CircuitBreaker.js` (Prometheus metrics), `conf/config.json` (retry/backoff config), `lib/api/BackbeatAPI.js` (no circuit breaker for downstream calls)

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, GraphQL schema, or Smithy specification exists in the repository. The API is documented only in markdown files (`docs/healthcheck.md`, `docs/pause-resume.md`, `docs/metrics.md`). Route definitions in `lib/api/routes.js` are programmatic but not exported as a machine-readable spec.
- **Gap**: Agent frameworks cannot auto-generate tool definitions from the Backbeat API. Every integration requires manual tool authoring.
- **Compensating Controls**:
  - Generate an OpenAPI spec from the route definitions in `routes.js`
  - Manually author tool definitions based on the markdown documentation
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Generate an OpenAPI 3.0 specification from the route definitions in `lib/api/routes.js`. Include request/response schemas, error codes, and authentication requirements.
- **Evidence**: No files found: `openapi.yaml`, `swagger.yaml`, `asyncapi.yaml`. Markdown docs: `docs/healthcheck.md`, `docs/pause-resume.md`, `docs/metrics.md`

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The Backbeat API uses Arsenal error objects (`errors.InternalError`, `errors.RouteNotFound`, `errors.MethodNotAllowed`, `errors.MalformedPOSTRequest`, `errors.AccessDenied`, `errors.InvalidQueryParameter`) with customizable descriptions. Error responses are serialized as JSON via `BackbeatServer._response()`. Each error includes an HTTP status code and a message. However, there is no explicit `retryable` boolean or error category field, and the error response structure is not formally documented.
- **Gap**: No `retryable` indicator in error responses. Agents cannot programmatically distinguish retriable errors (e.g., 500 InternalError due to Kafka unavailability) from terminal errors (e.g., 404 RouteNotFound). No error code enumeration.
- **Compensating Controls**:
  - Map Arsenal error codes to retryable/terminal categories in agent tool definitions
  - Use HTTP status code ranges as a proxy (5xx → retryable, 4xx → terminal)
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Extend error responses to include a structured body with `errorCode`, `message`, and `retryable` fields.
- **Evidence**: `lib/api/BackbeatServer.js` (`_errorResponse`, `_response`), Arsenal error objects throughout `lib/api/BackbeatAPI.js`

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Structured JSON logging is present via werelogs with `newRequestLogger()` for request-scoped logging. However, no distributed tracing SDK is present — no OpenTelemetry, no X-Ray, no `traceparent` header propagation. No correlation ID is propagated across service boundaries (Backbeat → S3, Backbeat → Vault, Backbeat → Kafka). Request IDs exist within werelogs but are not propagated to downstream calls.
- **Gap**: Cannot trace an agent-initiated request through Backbeat to its downstream services. Debugging agent-initiated failures requires manual log correlation across multiple systems.
- **Compensating Controls**:
  - werelogs request-scoped logging provides within-service traceability
  - Kafka message keys provide implicit correlation for replication workflows
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenTelemetry SDK instrumentation. Propagate `traceparent` headers in HTTP requests to downstream services (S3, Vault). Include trace IDs in Kafka message headers.
- **Evidence**: `lib/api/BackbeatServer.js` (`_requestListener` uses `this._logger.newRequestLogger()`), `package.json` (no opentelemetry or x-ray dependencies)

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive Prometheus alerting rules exist in `monitoring/replication/alerts.yaml` covering: `ReplicationProducerCritical`, `ReplicationDataProcessorCritical`, `ReplicationErrorsWarning/Critical`, `ReplicationRpoWarning/Critical`, `ReplicationLatencyWarning/Critical`, `ReplicationBacklogGrowing`. Warning and critical thresholds are configurable. However, these alerts cover the replication pipeline — there are no specific alerts for the Backbeat REST API error rates or latency that agents would consume.
- **Gap**: No alerting on the Backbeat REST API (port 8900) error rates or response latency. Existing alerts cover the Kafka processing pipeline but not the API surface agents would call.
- **Compensating Controls**:
  - The Prometheus `/monitoring/metrics` endpoint exposes metrics that could be used to create API-level alerts
  - Existing pipeline alerts provide indirect signal of system health
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add Prometheus alerts for HTTP error rate and latency on the Backbeat API endpoint (port 8900). Monitor 5xx rates and p99 latency.
- **Evidence**: `monitoring/replication/alerts.yaml`, `lib/api/BackbeatAPI.js` (`monitoringHandler`)

#### ENG-Q1: Infrastructure Governance — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No Terraform, CloudFormation, CDK, or other IaC files exist in this repository. A Dockerfile is present for container building, and `docker-entrypoint.sh` configures the application via environment variables and jq filters. No IaC definitions for API Gateway, IAM roles, network configuration, or secrets management. No drift detection configuration.
- **Gap**: The infrastructure exposing Backbeat to agents (network, IAM, API gateway) is not defined as code in this repository. Changes to infrastructure are not subject to automated review or drift detection.
- **Compensating Controls**:
  - Infrastructure may be defined in a separate repository (common for microservices architectures)
  - Docker-based deployment provides some reproducibility
- **Remediation Timeline**: 60–90 days
- **Recommendation**: If infrastructure is defined in a separate repository, document the linkage. If not, define the agent-facing infrastructure (network policies, API gateway, IAM roles) as IaC.
- **Evidence**: No `.tf`, `.cfn.yaml`, `cdk.json` files found. `Dockerfile` present. `docker-entrypoint.sh` present.

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive CI/CD pipeline in `.github/workflows/tests.yaml`: lint, unit tests, functional tests across 8+ test suites (api:routes, api:retry, replication, lifecycle, ingestion, lib, notification, oplogPopulator), performance/ballooning tests, and queue-populator integration tests. Code coverage via nyc/c8 with Codecov integration. However, no API contract testing (Pact), no OpenAPI validation, and no breaking change detection for the REST API.
- **Gap**: API changes are not validated against a contract. An API-breaking change (e.g., modifying the healthcheck response format) would not be caught automatically in CI.
- **Compensating Controls**:
  - Functional API tests (`tests/functional/api/routes.js`, `tests/functional/api/retry.js`) validate API behavior
  - These tests catch behavioral regressions but not schema-level breaking changes
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenAPI spec validation in CI. Implement consumer-driven contract tests (Pact) for the REST API endpoints. Add breaking change detection when an OpenAPI spec is created.
- **Evidence**: `.github/workflows/tests.yaml`, `tests/functional/api/routes.js`, `tests/functional/api/retry.js`

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Releases are created via `.github/workflows/release.yaml` using `softprops/action-gh-release`. Docker images are built via `.github/workflows/docker-build.yaml`. No blue/green deployment, no canary deployment, no CodeDeploy rollback triggers, no Helm rollback configuration, no feature flags, and no automatic rollback capability.
- **Gap**: If a deployment breaks agent-facing APIs, rollback requires manually deploying the previous Docker image version. No automated rollback within the 15–30 minute target.
- **Compensating Controls**:
  - Docker image versioning allows manual rollback to a previous tag
  - GitHub releases provide tagged versions for rollback reference
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement automated rollback in the deployment pipeline (e.g., health check-based rollback in container orchestration). Add canary deployment with automatic rollback on error rate increase.
- **Evidence**: `.github/workflows/release.yaml`, `.github/workflows/docker-build.yaml`

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Functional API tests exist in `tests/functional/api/` with `routes.js` and `retry.js` test files. The mocha test framework is used with 30-second timeouts. Unit tests cover core components (`tests/unit/api/`). Code coverage is tracked via nyc/c8 with Codecov integration, targeting 80% patch coverage. However, the functional tests are limited to route matching and retry logic — no comprehensive edge case testing for all API endpoints (metrics, pause/resume, workflow configuration).
- **Gap**: API test coverage is partial. Not all endpoints have dedicated test cases for input validation, error responses, and edge cases.
- **Compensating Controls**:
  - Existing functional tests cover the most critical API paths (routes, retry)
  - Unit tests provide component-level coverage
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Expand API functional tests to cover all endpoints including metrics, pause/resume, workflow configuration. Add edge case tests for malformed inputs, concurrent requests, and error scenarios.
- **Evidence**: `tests/functional/api/routes.js`, `tests/functional/api/retry.js`, `.nycrc`, `codecov.yml`

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Configuration schema is validated via joi in `lib/config.joi.js` and `lib/config/configItems.joi.js`. No API versioning (no `/v1/` URL patterns, no `Accept-Version` headers). No breaking change detection tools in CI. No consumer-driven contract tests. The REST API routes use the `/_/backbeat/api/` prefix but no version segment.
- **Gap**: API changes are not versioned. Agent tool bindings could break silently when the API response format changes. No schema registry or breaking change detection.
- **Compensating Controls**:
  - joi schema validation prevents internal configuration drift
  - Functional API tests catch some behavioral changes
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add API versioning (e.g., `/_/backbeat/api/v1/`) to the REST endpoints. Generate and version an OpenAPI spec. Add breaking change detection in CI.
- **Evidence**: `lib/config.joi.js`, `lib/api/routes.js` (no version prefix), `.github/workflows/tests.yaml` (no schema validation step)

#### AUTH-Q4: Identity Propagation and Delegation — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: `CredentialsManager.js` handles STS `AssumeRole` for downstream S3/Vault calls with per-extension credentials. The REST API has no JWT/OAuth token exchange or on-behalf-of flows. No distinction between agent-as-self vs. agent-on-behalf-of-user.
- **Gap**: No identity propagation through the REST API. Downstream calls use service-level credentials.
- **Compensating Controls**:
  - Service-level credentials limit blast radius for downstream calls
  - Per-extension credential separation provides some isolation
- **Remediation Timeline**: 60–90 days
- **Recommendation**: If agent use cases require user-delegated actions, implement token exchange flows.
- **Evidence**: `lib/credentials/CredentialsManager.js`, `conf/config.json`

#### AUTH-Q5: Credential Management — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: `conf/authdata.json` contains sample access/secret key pairs. `CredentialsManager.resolveExternalFileSync()` supports external file-based credential retrieval. STS temporary credentials with expiration used for role assumption. No secrets management integration (Secrets Manager, Vault) for API credentials.
- **Gap**: Sample credentials committed to repo. No secrets management integration for API-level credentials.
- **Compensating Controls**:
  - External file pattern (`resolveExternalFileSync`) supports tmpfs-mounted secrets
  - STS temporary credentials expire automatically
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Remove sample credentials from repo. Integrate with secrets management system.
- **Evidence**: `conf/authdata.json`, `lib/credentials/CredentialsManager.js`

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Docker Compose setup for functional testing with all dependencies (Kafka, Zookeeper, Redis, MongoDB). GitHub Actions CI runs comprehensive tests. No persistent staging environment with production-equivalent data shape.
- **Gap**: No staging/sandbox environment for agent integration testing outside CI.
- **Compensating Controls**:
  - Docker Compose setup can be used locally for agent testing
  - CI functional tests validate API behavior against containerized services
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a persistent staging environment with production-equivalent data shape.
- **Evidence**: `tests/config.json`, `.github/dockerfiles/ft/`, `.github/workflows/tests.yaml`

#### DATA-Q3: Selective Query Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: `getSiteFailedCRR` implements marker-based pagination with `listingLimit=100`. Metrics endpoints return aggregated data. Cross-site failure lookup (`_getEntriesAcrossSites`) iterates all sites without pagination.
- **Gap**: Cross-site failure listing lacks pagination.
- **Compensating Controls**:
  - Per-site queries are paginated with marker support
  - Metrics endpoints return bounded aggregated data
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add pagination to the cross-site failure listing endpoint.
- **Evidence**: `lib/api/BackbeatAPI.js`

#### DATA-Q5: Temporal Metadata and Freshness — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Object-level temporal metadata is partially present. `LastModified` timestamps are included in failed CRR API responses via `getLastModified()`. `MetricsModel` records `timestamp: Date.now()` for each event. Kafka backlog metrics track `latestPublishedMessageTimestamp`, `latestConsumedMessageTimestamp`, and `latestConsumeEventTimestamp` as Prometheus gauges. However, no `Cache-Control`, `X-Data-Age`, or freshness signaling headers are returned by the REST API. Agents cannot determine if data returned is current, stale, cached, or eventually consistent.
- **Gap**: The REST API provides no freshness signaling. Redis-stored metrics and sorted set data is eventually consistent, but this is not communicated to API consumers. No response headers indicate data age or consistency level.
- **Compensating Controls**:
  - `LastModified` timestamps on individual objects provide per-record temporal metadata
  - Prometheus timestamp gauges (`latestConsumedMessageTimestamp`) provide indirect freshness signals
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add `Cache-Control` or `X-Data-Age` response headers to REST API endpoints. Document the consistency model for metrics and failed CRR data.
- **Evidence**: `lib/api/BackbeatAPI.js` (`LastModified` in responses), `lib/models/MetricsModel.js` (`timestamp` field), `lib/KafkaBacklogMetrics.js` (timestamp gauges)

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No KMS configuration, no encryption-at-rest settings for Redis or MongoDB. Redis password defaults to empty string. No TLS configured for data store connections in default config.
- **Gap**: Data at rest in Redis and MongoDB is not encrypted.
- **Compensating Controls**:
  - Network-level encryption (if deployed in VPC with encryption)
  - Data store encryption may be configured at the infrastructure level (outside this repo)
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Enable encryption at rest for MongoDB and Redis. Configure TLS for data store connections.
- **Evidence**: `conf/config.json` (redis and mongo sections)

---

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO
- **Finding**: Backbeat exposes a REST API on port 8900 via `BackbeatServer.js`. Routes are defined in `lib/api/routes.js` covering: healthcheck (GET), monitoring/metrics (GET), CRR metrics (GET), failed CRR listing (GET), retry failed CRR (POST), pause/resume service (POST/DELETE/GET), service status (GET), and workflow configuration (POST). Documentation exists in markdown: `docs/healthcheck.md`, `docs/pause-resume.md`, `docs/metrics.md`. The API does not require direct database access, file-based exchange, or UI automation for integration.
- **Implication**: The API surface is suitable for agent integration. The operational nature of the API (healthcheck, metrics, pause/resume) is well-suited for read-only agent consumption.
- **Recommendation**: The API is functional and documented. Formalize the documentation as an OpenAPI spec (see API-Q2).
- **Evidence**: `lib/api/BackbeatServer.js`, `lib/api/routes.js`, `docs/healthcheck.md`, `docs/pause-resume.md`, `docs/metrics.md`

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Write endpoints include: `retryFailedCRR` (POST — uses `_applyRetryLockKey` with Redis to prevent duplicate retries), `pauseService`/`resumeService` (POST — idempotent by nature: pausing an already-paused service is a no-op), `deleteScheduledResumeService` (DELETE — idempotent), `applyWorkflowConfiguration` (POST — applies configuration overlay). The retry lock mechanism provides partial idempotency for the most critical write operation.
- **Implication**: Read-only agents do not execute write operations. For future write-enabled scope, the existing lock mechanism on retries provides a foundation for idempotency.
- **Recommendation**: If agent scope expands to write-enabled, ensure all POST endpoints support idempotency keys.
- **Evidence**: `lib/api/BackbeatAPI.js` (`_applyRetryLockKey`, `retryFailedCRR`, `pauseService`, `resumeService`)

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: API responses are JSON (`application/json` content type) via `BackbeatServer._response()`. The monitoring endpoint returns Prometheus text format via `ZenkoMetrics.asPrometheusContentType()`. No XML, binary, or protobuf formats.
- **Implication**: JSON responses are directly consumable by LLM-based agents. The Prometheus format for monitoring metrics requires parsing but is well-structured.
- **Recommendation**: No action needed. JSON is the preferred format for agent consumption.
- **Evidence**: `lib/api/BackbeatServer.js` (`_response` method, content type handling)

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limit headers (`X-RateLimit-Remaining`, `Retry-After`) are returned in API responses. `BackbeatServer._response()` only sets `Content-Type` and `Content-Length` headers. No API Gateway usage plans or WAF rate rules are configured (no IaC in repo).
- **Implication**: Agents cannot self-throttle based on rate limit headers. Without rate limit feedback, agents must implement their own throttling logic.
- **Recommendation**: When rate limiting is added (STATE-Q5), include `X-RateLimit-Remaining` and `Retry-After` headers in responses.
- **Evidence**: `lib/api/BackbeatServer.js` (`_response` method — only Content-Type and Content-Length headers)

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: `BackbeatConsumer` uses `OffsetLedger` for Kafka offset tracking to ensure ordered processing. `_applyRetryLockKey` in `BackbeatAPI.js` provides Redis-based locking for CRR retry operations. `TaskScheduler` provides ordered queue processing with configurable concurrency. No optimistic locking (ETags, version fields) or `If-Match` headers on the REST API.
- **Implication**: Read-only agents do not perform writes, so concurrency controls on write operations are informational. For future write-enabled scope, the Redis lock mechanism provides a foundation.
- **Recommendation**: If agent scope expands to write-enabled, add optimistic locking (ETags) to API responses for state-changing operations.
- **Evidence**: `lib/BackbeatConsumer.js` (`OffsetLedger`), `lib/api/BackbeatAPI.js` (`_applyRetryLockKey`), `lib/tasks/TaskScheduler.js`

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Kafka consumer concurrency (`concurrency: 10`) and max queued messages (`maxQueued: 1000`) are configurable per processor. No per-agent transaction limits (max records modified per run, max spend per hour). These limits are system-wide, not per-identity.
- **Implication**: Read-only agents cannot modify records. For future write-enabled scope, per-agent transaction limits should be implemented.
- **Recommendation**: If agent scope expands to write-enabled, implement per-agent transaction limits for operations like retry and workflow configuration.
- **Evidence**: `conf/config.json` (concurrency settings), `lib/BackbeatConsumer.js` (`_concurrency`, `_maxQueued`)

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Replication uses PENDING status before COMPLETED/FAILED state transitions. The pause/resume mechanism allows operational control over replication workflows. Scheduled resume (with configurable hours) provides a time-delayed execution pattern.
- **Implication**: The PENDING state and pause/resume controls could serve as a foundation for human-in-the-loop patterns if agent scope expands to write-enabled.
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: `lib/api/BackbeatAPI.js` (`pauseService`, `resumeService`), `docs/pause-resume.md`

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No approval workflow endpoints exist. The pause/resume mechanism is the closest operational control but is not approval-based — it's a binary on/off toggle per service per location. No Step Functions with human approval tasks or two-step commit patterns.
- **Implication**: No immediate concern for read-only agents. If write-enabled scope is adopted, approval gates should be considered for destructive operations.
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: `lib/api/BackbeatAPI.js`, `lib/api/routes.js`

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality dashboards, data profiling reports, null rate monitoring, duplicate detection logic, or data freshness SLAs are present. The system tracks operational metrics (backlog, completions, throughput, failures) but not data quality metrics.
- **Implication**: Agents consuming Backbeat data cannot assess data quality programmatically.
- **Recommendation**: Consider adding data quality metrics to the Prometheus endpoint — e.g., completeness ratios, stale data indicators.
- **Evidence**: `lib/api/Metrics.js`, `monitoring/replication/alerts.yaml` (operational metrics only)

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Field names are human-readable and semantically meaningful: `getBucket()`, `getObjectKey()`, `getEncodedVersionId()`, `getContentLength()`, `getLastModified()`, `replicationStatus`, `StorageClass`, `IsTruncated`, `NextMarker`. No legacy abbreviations or cryptic codes requiring a data dictionary.
- **Implication**: Agent tool definitions can use these field names directly without translation.
- **Recommendation**: No action needed. Field naming is clear.
- **Evidence**: `lib/api/BackbeatAPI.js` (response object construction in `_getFailedCRRResponse`)

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No data catalog (Glue, Collibra, DataHub) or metadata layer exists. The `DESIGN.md` provides architectural overview. `lib/config.joi.js` defines configuration schema but not data schema.
- **Implication**: Agent tool builders must manually discover what data Backbeat holds by reading source code and documentation.
- **Recommendation**: Create a data dictionary documenting the entities Backbeat processes (objects, buckets, replication status, metrics) and their relationships.
- **Evidence**: `DESIGN.md`, `lib/config.joi.js`

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: Backbeat exposes a REST API on port 8900 with routes for healthcheck, monitoring/metrics, CRR operations, pause/resume, service status, and workflow configuration. Documentation exists in markdown files. No direct database access, file-based exchange, or UI automation required.
- **Gap**: Documentation is informal markdown rather than a formal specification, but the API is present and functional.
- **Recommendation**: Formalize documentation as an OpenAPI specification.
- **Evidence**: `lib/api/BackbeatServer.js`, `lib/api/routes.js`, `docs/healthcheck.md`, `docs/pause-resume.md`, `docs/metrics.md`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, GraphQL schema, or Smithy specification exists. API documentation is markdown only.
- **Gap**: No machine-readable API specification for agent tool auto-generation.
- **Recommendation**: Generate an OpenAPI 3.0 specification from route definitions.
- **Evidence**: No spec files found. `lib/api/routes.js`, `docs/`

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: Arsenal error objects provide structured error codes and descriptions. JSON serialization via `BackbeatServer._response()`. Missing `retryable` indicator.
- **Gap**: No `retryable` boolean or error categorization in error responses.
- **Recommendation**: Add structured error body with `errorCode`, `message`, and `retryable` fields.
- **Evidence**: `lib/api/BackbeatServer.js`, `lib/api/BackbeatAPI.js`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Retry operations use Redis lock keys (`_applyRetryLockKey`). Pause/resume are naturally idempotent.
- **Gap**: N/A for read-only scope.
- **Recommendation**: No action for read-only scope.
- **Evidence**: `lib/api/BackbeatAPI.js`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: JSON (`application/json`) and Prometheus text format responses. No XML or binary.
- **Gap**: None.
- **Recommendation**: No action needed.
- **Evidence**: `lib/api/BackbeatServer.js`

#### API-Q6: Asynchronous Operation Support
- **Severity**: INFO
- **Finding**: The entire system is built on asynchronous patterns. Kafka-based message processing with background workers handles all long-running operations. The REST API is synchronous for queries/commands but the underlying work (replication, lifecycle) is fully asynchronous via Kafka queues. Failed operations are tracked and retryable.
- **Gap**: None — the system's core architecture is asynchronous by design.
- **Recommendation**: No action needed. The Kafka-based architecture provides robust async patterns.
- **Evidence**: `lib/BackbeatConsumer.js`, `lib/BackbeatProducer.js`, `conf/config.json` (Kafka topics)

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: Kafka topics serve as the event mechanism: `backbeat-replication-status` for replication status changes, `backbeat-replication-failed` for failures, `backbeat-lifecycle-*` topics for lifecycle events. No SNS/EventBridge/webhook integration — events are internal Kafka topics. Redis pub/sub is used for operational commands (pause/resume).
- **Gap**: Events are Kafka-internal, not exposed as webhooks or cloud-native events for external agent consumption.
- **Recommendation**: Consider exposing key state change events (replication completed/failed) as webhooks or CloudEvents for agent consumption.
- **Evidence**: `conf/config.json` (topic definitions), `lib/api/BackbeatAPI.js` (Redis pub/sub for pause/resume)

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit headers in API responses. No rate limiting documentation.
- **Gap**: Agents cannot self-throttle based on rate limit feedback.
- **Recommendation**: Add rate limit headers when rate limiting is implemented.
- **Evidence**: `lib/api/BackbeatServer.js`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: API authenticates via IP allowlist only. No OAuth2, API key, mTLS, or service account authentication for API callers.
- **Gap**: No machine identity authentication. Cannot distinguish between different agent callers.
- **Recommendation**: Add API key or bearer token authentication with principal attribution.
- **Evidence**: `lib/api/BackbeatServer.js`, `conf/config.json`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: Per-extension service accounts exist for downstream access. Backbeat API has no per-identity permission scoping.
- **Gap**: All callers from allowed IPs have identical full access to all endpoints.
- **Recommendation**: Implement route-level authorization per agent identity.
- **Evidence**: `lib/api/BackbeatServer.js`, `conf/config.json`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: No RBAC or ABAC on Backbeat API. All allowed callers can invoke GET, POST, and DELETE endpoints equally.
- **Gap**: Cannot restrict an agent to read-only operations at the API level.
- **Recommendation**: Add action-level middleware differentiating read (GET) from write (POST/DELETE) operations.
- **Evidence**: `lib/api/BackbeatServer.js`, `lib/api/routes.js`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: RISK-QUALITY
- **Finding**: `CredentialsManager.js` handles STS `AssumeRole` for downstream S3/Vault calls with per-extension credentials (`source.auth`, `destination.auth`). The REST API has no JWT/OAuth token exchange or on-behalf-of flows. No distinction between agent-as-self vs agent-on-behalf-of-user.
- **Gap**: No identity propagation through the REST API layer. Downstream calls use service-level credentials, not caller-specific credentials.
- **Recommendation**: If agent use cases require user-delegated actions, implement token exchange or on-behalf-of flows.
- **Evidence**: `lib/credentials/CredentialsManager.js`, `conf/config.json` (auth sections)

#### AUTH-Q5: Credential Management
- **Severity**: RISK-QUALITY
- **Finding**: `conf/authdata.json` contains sample access/secret key pairs (placeholder values `accessKey1`/`verySecretKey1`). `CredentialsManager.resolveExternalFileSync()` supports reading credentials from external files (likely tmpfs-mounted secrets). STS temporary credentials with expiration are used for role assumption. `docker-entrypoint.sh` uses environment variables for configuration (not credential values directly). No Secrets Manager or Vault integration for the Backbeat API credentials.
- **Gap**: Sample credentials are committed to the repository. While likely not production values, the pattern encourages hardcoded credentials. No secrets management integration for API-level credentials.
- **Recommendation**: Remove sample credentials from `conf/authdata.json`. Integrate with a secrets management system (AWS Secrets Manager, HashiCorp Vault) for all credential retrieval.
- **Evidence**: `conf/authdata.json`, `lib/credentials/CredentialsManager.js` (`resolveExternalFileSync`), `docker-entrypoint.sh`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: werelogs structured logging present. No immutable storage. No principal attribution (due to AUTH-Q1 gap).
- **Gap**: Logs are not immutable or tamper-evident. No authenticated principal recorded.
- **Recommendation**: Configure immutable log storage. Include authenticated principal after AUTH-Q1 resolution.
- **Evidence**: `lib/api/BackbeatServer.js`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: Only IP allowlist exists. No individual identity suspension mechanism.
- **Gap**: Cannot revoke a specific agent identity without affecting all callers.
- **Recommendation**: Implement API key authentication with revocation capability.
- **Evidence**: `lib/api/BackbeatServer.js`, `conf/config.json`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Retry mechanism exists for failed CRR. No formal saga or compensating transactions.
- **Gap**: No automated compensation for partially completed multi-step operations.
- **Recommendation**: Document failure modes and recovery procedures.
- **Evidence**: `lib/api/BackbeatAPI.js`

#### STATE-Q2: Queryable Current State
- **Severity**: INFO
- **Finding**: Multiple state-querying endpoints exist: `getServiceStatus` (pause/resume status), `getResumeSchedule`, `getHealthcheck`, `getFailedCRR`/`getSiteFailedCRR` (failed operation listings), and comprehensive metrics endpoints (backlog, completions, throughput, pending, failures). State is queryable and inspectable.
- **Gap**: None — state is well-exposed through the API.
- **Recommendation**: No action needed. State queryability is strong.
- **Evidence**: `lib/api/BackbeatAPI.js`, `lib/api/routes.js`

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: OffsetLedger for Kafka offset tracking, Redis lock keys for retry operations, TaskScheduler for ordered processing.
- **Gap**: No optimistic locking on REST API. Informational for read-only scope.
- **Recommendation**: No action for read-only scope.
- **Evidence**: `lib/BackbeatConsumer.js`, `lib/api/BackbeatAPI.js`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: Circuit breakers are implemented via the `breakbeat` library (`CircuitBreaker` class). `BackbeatConsumer` imports and uses `CircuitBreaker` with state-change handlers that pause Kafka consumption when tripped (`BreakerState.Tripped`) and resume when nominal (`BreakerState.Nominal`). Circuit breaker state is exported as Prometheus metrics (`s3_circuit_breaker` gauge, `s3_circuit_breaker_errors_count` counter). Exponential backoff retry is configured per destination type in `conf/config.json` (e.g., `aws_s3.backoff.min: 60000, max: 900000, factor: 1.5, jitter: 0.1`). Timeout configurations are present per processor. However, the REST API layer (`lib/api/`) has no circuit breaker, retry, or timeout logic for its own downstream calls (e.g., S3 metadata retrieval during `retryFailedCRR`, Redis calls for failed CRR lookups).
- **Gap**: Circuit breakers protect Kafka consumers but not the REST API's downstream calls. An agent calling the Backbeat REST API triggers synchronous downstream calls to S3 and Redis that lack circuit breaker protection. A runaway agent loop hitting the retry endpoint could cascade failures to downstream services without tripping any circuit breaker.
- **Recommendation**: Add circuit breakers for the REST API's synchronous downstream calls using the existing `breakbeat` library. Prioritize S3 metadata retrieval during `retryFailedCRR` and Redis calls in `BackbeatAPI`.
- **Evidence**: `lib/BackbeatConsumer.js` (CircuitBreaker usage), `lib/CircuitBreaker.js` (Prometheus metrics), `conf/config.json` (retry/backoff config), `lib/api/BackbeatAPI.js` (no circuit breaker for downstream calls)

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: Kafka consumer concurrency limits exist. No API-level rate limiting on port 8900.
- **Gap**: REST API is unprotected against traffic storms.
- **Recommendation**: Add rate limiting middleware or deploy an API gateway with throttling.
- **Evidence**: `lib/api/BackbeatServer.js`, `lib/BackbeatConsumer.js`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: System-wide concurrency limits exist. No per-agent transaction limits.
- **Gap**: Informational for read-only scope.
- **Recommendation**: No action for read-only scope.
- **Evidence**: `conf/config.json`, `lib/BackbeatConsumer.js`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `orchestrator`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path. This service is P2.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: PENDING status exists in replication workflow. Pause/resume provides operational control.
- **Gap**: Informational for read-only scope.
- **Recommendation**: No action for read-only scope.
- **Evidence**: `lib/api/BackbeatAPI.js`, `docs/pause-resume.md`

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No approval workflow endpoints. Pause/resume is binary operational control.
- **Gap**: Informational for read-only scope.
- **Recommendation**: No action for read-only scope.
- **Evidence**: `lib/api/BackbeatAPI.js`, `lib/api/routes.js`

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: `tests/config.json` provides test configuration. `.github/dockerfiles/ft/` contains Docker Compose setup for functional testing with Kafka, Zookeeper, Redis, MongoDB, and synthetic bucketd services. GitHub Actions CI runs tests against these containerized services. No dedicated staging environment with production-equivalent data shape.
- **Gap**: Testing infrastructure exists for CI but no persistent staging/sandbox environment for agent testing.
- **Recommendation**: Create a persistent staging environment with production-equivalent data shape for agent integration testing.
- **Evidence**: `tests/config.json`, `.github/dockerfiles/ft/`, `.github/workflows/tests.yaml`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: No data classification tags, field-level encryption, or PII detection. Object metadata processed without classification.
- **Gap**: No sensitive data classification at any level.
- **Recommendation**: Classify data fields. Implement field-level access controls.
- **Evidence**: `conf/authdata.json`, `lib/credentials/CredentialsManager.js`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Cross-region replication by design. No residency constraints enforced.
- **Gap**: API responses expose cross-region metadata without residency controls.
- **Recommendation**: Document residency implications. Add metadata tagging for residency constraints.
- **Evidence**: `conf/config.json`, `lib/api/BackbeatAPI.js`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK-QUALITY
- **Finding**: `getSiteFailedCRR` implements marker-based pagination with `listingLimit=100`. The `marker` query parameter controls listing start position. Metrics endpoints return aggregated data (not unbounded lists). However, `_getEntriesAcrossSites` iterates all sites without pagination.
- **Gap**: Most endpoints support pagination or return aggregated data. The cross-site failure lookup has no built-in pagination.
- **Recommendation**: Add pagination to the cross-site failure listing endpoint.
- **Evidence**: `lib/api/BackbeatAPI.js` (`_getEntriesBySite` with `listingLimit=100`, `getSiteFailedCRR`)

#### DATA-Q4: System of Record Designations
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `orchestrator`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway). Orchestrator does not own persistent state.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK-QUALITY
- **Finding**: Object-level temporal metadata is partially present. The `getLastModified()` method on queue entries provides `LastModified` timestamps in API responses for failed CRR listings (e.g., `_getFailedCRRResponse` at `lib/api/BackbeatAPI.js:464` and `:784`). `MetricsModel` records `timestamp: Date.now()` for each metrics event (`lib/models/MetricsModel.js:18`). Kafka backlog metrics track `latestPublishedMessageTimestamp`, `latestConsumedMessageTimestamp`, and `latestConsumeEventTimestamp` as Prometheus gauges (`lib/KafkaBacklogMetrics.js`, `lib/constants.js`). Replication latency is calculated from `lastModified` timestamps (`extensions/replication/tasks/UpdateReplicationStatus.js:230`). However, no `Cache-Control`, `X-Data-Age`, or `last_refreshed` headers are returned by the REST API. No freshness signaling exists — agents cannot determine if data returned is current, stale, cached, or eventually consistent. Timezone normalization is implicit (JavaScript `Date.now()` returns UTC milliseconds) but not formally documented.
- **Gap**: While temporal metadata exists at the object level (`LastModified`) and metrics level (`timestamp`), the REST API provides no freshness signaling. An agent querying failed CRR entries or metrics has no way to know whether the data is current or stale. No `Cache-Control` or equivalent headers indicate data age. The eventually consistent nature of Redis-stored metrics and sorted set data is not communicated to API consumers.
- **Recommendation**: Add `Cache-Control` or `X-Data-Age` response headers to the Backbeat REST API endpoints. For metrics endpoints, indicate the time window of the data. For failed CRR listings, indicate when the sorted set was last updated. Document the consistency model (Redis eventual consistency) in the API documentation.
- **Evidence**: `lib/api/BackbeatAPI.js` (`LastModified` in responses at lines 464, 784), `lib/models/MetricsModel.js` (`timestamp` field), `lib/KafkaBacklogMetrics.js` (timestamp gauges), `lib/constants.js` (Prometheus metric names), `extensions/replication/tasks/UpdateReplicationStatus.js` (lastModified usage)

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: Object keys, bucket names, version IDs, and client IPs logged without redaction. No PII scrubbing.
- **Gap**: Potentially PII-bearing fields logged freely.
- **Recommendation**: Implement log scrubbing for sensitive fields.
- **Evidence**: `lib/api/BackbeatServer.js`, `lib/api/BackbeatAPI.js`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: Operational metrics (backlog, completions, failures) tracked. No data quality metrics.
- **Gap**: No data quality scoring or completeness metrics.
- **Recommendation**: Consider adding data quality metrics to the Prometheus endpoint.
- **Evidence**: `lib/api/Metrics.js`, `monitoring/replication/alerts.yaml`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: joi schema validation for config. No API versioning or breaking change detection.
- **Gap**: API changes not versioned. No schema registry.
- **Recommendation**: Add API versioning and OpenAPI spec with breaking change detection.
- **Evidence**: `lib/config.joi.js`, `lib/api/routes.js`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Field names are clear and readable (getBucket, getObjectKey, replicationStatus, StorageClass).
- **Implication**: Agent tool definitions can use field names directly.
- **Recommendation**: No action needed.
- **Evidence**: `lib/api/BackbeatAPI.js`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No data catalog or metadata layer. DESIGN.md provides architectural overview.
- **Implication**: Manual discovery required for agent tool builders.
- **Recommendation**: Create a data dictionary for entities processed by Backbeat.
- **Evidence**: `DESIGN.md`, `lib/config.joi.js`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: Structured JSON logging via werelogs with request-scoped loggers. No distributed tracing (OpenTelemetry, X-Ray).
- **Gap**: Cannot trace requests across service boundaries.
- **Recommendation**: Add OpenTelemetry SDK instrumentation.
- **Evidence**: `lib/api/BackbeatServer.js`, `package.json`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive Prometheus alerting for replication pipeline. No specific alerts for the REST API endpoint.
- **Gap**: No alerting on API error rates or latency.
- **Recommendation**: Add API-level Prometheus alerts.
- **Evidence**: `monitoring/replication/alerts.yaml`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: Rich custom Prometheus metrics: `s3_replication_status_changed_total`, `s3_replication_rpo_seconds`, `s3_replication_latency_seconds`, `s3_circuit_breaker`, plus Kafka backlog metrics. Grafana dashboard in `monitoring/replication/dashboard.json`. These are business-relevant metrics tracking replication success, RPO, latency, and backlog — not just infrastructure metrics.
- **Implication**: Strong foundation for agent-visible business outcome metrics. Agents can consume these metrics to assess replication health.
- **Recommendation**: Expose key business metrics through the REST API in addition to the Prometheus endpoint for easier agent consumption.
- **Evidence**: `lib/CircuitBreaker.js` (Prometheus metrics), `monitoring/replication/alerts.yaml`, `monitoring/replication/dashboard.json`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK-QUALITY
- **Finding**: No IaC in this repository. Dockerfile and docker-entrypoint.sh present.
- **Gap**: Infrastructure not defined as code in this repo.
- **Recommendation**: Define agent-facing infrastructure as IaC or document linkage to infrastructure repo.
- **Evidence**: No `.tf`, `.cfn.yaml`, `cdk.json` files. `Dockerfile`, `docker-entrypoint.sh`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive CI/CD pipeline with 8+ test suites. No API contract testing or breaking change detection.
- **Gap**: API-breaking changes not caught automatically.
- **Recommendation**: Add OpenAPI validation and consumer-driven contract tests.
- **Evidence**: `.github/workflows/tests.yaml`, `tests/functional/api/`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: GitHub releases and Docker image builds. No automated rollback.
- **Gap**: Rollback requires manual Docker image redeployment.
- **Recommendation**: Implement health-check-based automated rollback.
- **Evidence**: `.github/workflows/release.yaml`, `.github/workflows/docker-build.yaml`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: Functional API tests exist for routes and retry. Code coverage tracked. Partial coverage of API endpoints.
- **Gap**: Not all endpoints have comprehensive edge case tests.
- **Recommendation**: Expand API test coverage to all endpoints.
- **Evidence**: `tests/functional/api/routes.js`, `tests/functional/api/retry.js`, `.nycrc`, `codecov.yml`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: RISK-QUALITY
- **Finding**: No KMS configuration, no encryption-at-rest settings for Redis or MongoDB in `conf/config.json`. Redis `password` field defaults to empty string. MongoDB connection uses `replicaSetHosts` without TLS or encryption configuration in the default config. No `aws_kms` references.
- **Gap**: Data at rest in Redis (failed CRR entries, metrics) and MongoDB (location status, metadata) is not encrypted. No encryption-at-rest configuration for the data stores agents would indirectly access.
- **Recommendation**: Enable encryption at rest for MongoDB and Redis. Configure TLS for connections to data stores. Add KMS key references for sensitive data storage.
- **Evidence**: `conf/config.json` (redis and mongo sections), `lib/api/BackbeatAPI.js` (Redis and MongoDB connections)

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `lib/api/BackbeatServer.js` | API-Q1, API-Q3, API-Q4, API-Q5, API-Q8, AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7, STATE-Q5, DATA-Q6 |
| `lib/api/BackbeatAPI.js` | API-Q1, API-Q3, API-Q4, API-Q6, API-Q7, AUTH-Q4, STATE-Q1, STATE-Q2, STATE-Q3, STATE-Q4, STATE-Q5, DATA-Q2, DATA-Q3, DATA-Q5, DATA-Q6, DISC-Q2, HITL-Q1, HITL-Q2 |
| `lib/api/routes.js` | API-Q1, API-Q2, AUTH-Q2, AUTH-Q3, DISC-Q1, HITL-Q2 |
| `lib/api/Healthcheck.js` | API-Q1, STATE-Q2 |
| `lib/api/Metrics.js` | DATA-Q7, STATE-Q2 |
| `lib/BackbeatConsumer.js` | STATE-Q3, STATE-Q4, STATE-Q5, STATE-Q6 |
| `lib/CircuitBreaker.js` | STATE-Q4, OBS-Q3 |
| `lib/credentials/CredentialsManager.js` | AUTH-Q4, AUTH-Q5, DATA-Q1 |
| `lib/config.joi.js` | DISC-Q1, DISC-Q3 |
| `lib/tasks/TaskScheduler.js` | STATE-Q3 |
| `lib/OffsetLedger.js` | STATE-Q3 |
| `lib/models/MetricsModel.js` | DATA-Q5 |
| `lib/KafkaBacklogMetrics.js` | DATA-Q5 |
| `lib/constants.js` | DATA-Q5 |
| `extensions/replication/tasks/UpdateReplicationStatus.js` | DATA-Q5 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| No API specification files found | API-Q2 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/tests.yaml` | ENG-Q2, ENG-Q4, HITL-Q3 |
| `.github/workflows/release.yaml` | ENG-Q3 |
| `.github/workflows/docker-build.yaml` | ENG-Q3 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `Dockerfile` | ENG-Q1 |
| `docker-entrypoint.sh` | AUTH-Q5, ENG-Q1 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `package.json` | OBS-Q1, STATE-Q4, OBS-Q3 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `conf/config.json` | AUTH-Q1, AUTH-Q2, STATE-Q5, STATE-Q6, DATA-Q2, ENG-Q5, API-Q7 |
| `conf/authdata.json` | AUTH-Q5, DATA-Q1 |
| `tests/config.json` | HITL-Q3 |
| `.nycrc` | ENG-Q4 |
| `codecov.yml` | ENG-Q4 |

### Documentation
| File | Questions Referenced |
|------|---------------------|
| `docs/healthcheck.md` | API-Q1 |
| `docs/pause-resume.md` | API-Q1, HITL-Q1 |
| `docs/metrics.md` | API-Q1 |
| `DESIGN.md` | DISC-Q3 |

### Monitoring
| File | Questions Referenced |
|------|---------------------|
| `monitoring/replication/alerts.yaml` | OBS-Q2, DATA-Q7 |
| `monitoring/replication/dashboard.json` | OBS-Q3 |
