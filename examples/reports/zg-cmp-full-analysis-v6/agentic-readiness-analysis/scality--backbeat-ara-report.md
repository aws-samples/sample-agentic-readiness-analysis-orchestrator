# Agentic Readiness Analysis Report

**Target**: /Users/lucasdu/Documents/AWS-MAC/2026-projects/sample-agentic-readiness-analysis/services/scality--backbeat
**Date**: 2025-05-08
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**TD Version**: agentic-readiness-analysis
**Repository Type**: application
**Service Archetype**: event-processor (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: javascript, storage, replication
**Context**: Scality backend engine for replication, lifecycle, and metadata workflows.

**Archetype Justification**: Backbeat is primarily a message queue consumer system that reads MongoDB oplogs and Kafka topics to process replication, lifecycle, and notification events asynchronously. Its HTTP API surface is minimal (internal metrics/healthcheck/pause-resume), and its core work is event-driven batch processing.

**Surface flags**:
- has_persistent_data_store: true
- has_http_rpc_surface: true
- has_auth_surface: true
- has_write_operations: true
- has_logging_of_user_data: false

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 2 | **RISK-SAFETY**: 6 | **RISK-QUALITY**: 9 | **INFOs**: 20

This repo has 2 High findings, 15 Medium findings (6 of which are safety-impact), and 20 Low findings. The matched classification rule is: "1-2 High → Remediation Required."

Resolve all blockers before any agent deployment — including pilots. The primary blockers are: (1) absence of a documented, stable API interface suitable for agent tool binding, and (2) absence of machine identity authentication on the management API.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 2 |
| RISK-SAFETY | 6 |
| RISK-QUALITY | 9 |
| INFO | 20 |
| N/A | 0 |
| Not Evaluated (extended) | 6 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 13
**Extended Questions Not Triggered**: 6
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: event-processor (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: The management API server uses IP-based access control only (`ipCheck.ipMatchCidrList` with `allowFrom` CIDR list in `BackbeatServer.js`). There is no machine identity authentication — no OAuth2 client credentials, no API keys with principal attribution, no mTLS. Internally, Backbeat uses STS AssumeRole and Vault-based auth for its own downstream calls, but the management API itself accepts any request from an allowed IP without identity verification.
- **Gap**: No machine identity authentication on the agent-facing API. IP-based ACL provides no principal attribution for audit, no identity lifecycle management, and cannot distinguish between different agent instances.
- **Remediation**:
  - **Immediate**: Deploy an API Gateway (e.g., Kong, AWS API Gateway) in front of the Backbeat management API with OAuth2 or API key authentication that attributes each request to a specific principal.
  - **Target State**: Token-based authentication (OAuth2 client credentials or mTLS) on the management API with principal attribution in request context and audit logs.
  - **Estimated Effort**: Medium
  - **Dependencies**: AUTH-Q6 (audit logging) depends on this being resolved first — you cannot log principal identity until identity exists.
- **Evidence**: `lib/api/BackbeatServer.js` (`_isValidRequest` — `ipCheck.ipMatchCidrList` only), `conf/config.json` (`server.healthChecks.allowFrom`)

### API-Q1: Documented API Interface

- **Severity**: BLOCKER
- **Finding**: Backbeat exposes an HTTP API server on port 8900 with 15+ endpoints defined programmatically in `lib/api/routes.js`. Routes include healthcheck, metrics (backlog/completions/throughput/pending/failures), CRR failed object management (GET/POST), pause/resume/status for CRR/ingestion/lifecycle, and workflow configuration. However, the API is designed as an internal management interface protected by IP-based CIDR allowlisting (`server.healthChecks.allowFrom` in `conf/config.json`), not as a documented external-facing API. There is no API documentation beyond code comments describing route patterns.
- **Gap**: No formal, versioned, documented API contract exists. The API is internal-only with IP-based access control. Agents cannot reliably bind to an undocumented, internal-only interface without risk of breaking changes.
- **Remediation**:
  - **Immediate**: Create an OpenAPI specification documenting all routes from `lib/api/routes.js`, including request/response schemas, error codes, and authentication requirements.
  - **Target State**: A versioned OpenAPI spec maintained alongside the code, with breaking changes detected in CI.
  - **Estimated Effort**: Medium
  - **Dependencies**: None
- **Evidence**: `lib/api/routes.js`, `lib/api/BackbeatServer.js`, `conf/config.json`

---

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: IAM policies in `policies/` directory show scoped permissions (e.g., `queue_populator_policy.json` grants only `vaultadmin:GetAccountInfo`). Extension-specific policies exist for lifecycle, GC, etc. However, the API server itself uses only IP-based access control (`ipCheck.ipMatchCidrList` in `BackbeatServer.js`) with no per-identity permission scoping. Any request from an allowed IP has full access to all API endpoints.
- **Gap**: No per-identity (per-agent) permission scoping at the API layer. All callers from allowed IPs have identical access to all operations.
- **Compensating Controls**:
  - Restrict agent-accessible IPs to a narrow CIDR range in `server.healthChecks.allowFrom`
  - Deploy an API Gateway in front of Backbeat's API with per-identity route-level authorization
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement token-based authentication (OAuth2 or API keys) with per-identity route-level permissions at the API layer, replacing or supplementing IP-based access control.
- **Evidence**: `lib/api/BackbeatServer.js`, `policies/queue_populator_policy.json`, `conf/config.json`

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The BackbeatServer validates only HTTP method and route prefix. There is no action-level authorization — any authenticated caller (i.e., from an allowed IP) can execute any operation: read metrics, pause replication, resume services, retry failed CRR, or apply workflow configuration.
- **Gap**: No RBAC, ABAC, or action-level permissions enforced. A read-only agent could invoke POST endpoints (pause/resume, retryFailedCRR, applyWorkflowConfiguration).
- **Compensating Controls**:
  - Enforce agent read-only access at the network layer (firewall rules blocking POST/DELETE to Backbeat)
  - Deploy an API Gateway with method-level authorization policies
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add middleware in `BackbeatServer._isValidRequest()` that checks caller identity against an action-permission matrix before routing to handler methods.
- **Evidence**: `lib/api/BackbeatServer.js`

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Since authentication is IP-based only, there is no concept of individual agent identities that can be suspended. The only mechanism to revoke access is to modify the `allowFrom` CIDR list in configuration and restart the server.
- **Gap**: No individual identity suspension capability. Revoking one agent's access requires reconfiguring and restarting the service, which affects all callers.
- **Compensating Controls**:
  - Use network-level controls (security groups, firewall rules) to block specific agent IPs
  - Deploy an API Gateway with API key management that supports individual key revocation
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement token-based or API-key-based authentication that supports individual identity revocation without service restart.
- **Evidence**: `lib/api/BackbeatServer.js`, `conf/config.json` (`server.healthChecks.allowFrom`)

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No HTTP-level rate limiting is implemented on the API server. The `BackbeatServer` has no rate limiting middleware. Concurrency controls exist for Kafka consumers (`concurrency: 10`, `MAX_QUEUED_DEFAULT: 1000`) but these protect queue processing, not the API endpoints. An agent or any caller could flood the API with requests.
- **Gap**: No API-layer rate limiting. The management API endpoints are unprotected against traffic storms.
- **Compensating Controls**:
  - Deploy an API Gateway or reverse proxy (nginx) with rate limiting in front of the Backbeat API
  - Implement `express-rate-limit` or equivalent middleware in BackbeatServer
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add rate limiting middleware to the HTTP server in `BackbeatServer`, or deploy behind an API Gateway with usage plans and throttling.
- **Evidence**: `lib/api/BackbeatServer.js`, `lib/BackbeatConsumer.js` (consumer-level concurrency only)

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Backbeat uses `werelogs` for structured logging. Logs include client IP addresses, HTTP methods, URLs, and status codes (visible in `BackbeatServer._logRequestEnd`). The system processes S3 object metadata including bucket names, object keys, and version IDs, which may contain user-identifiable information. No PII redaction or scrubbing middleware was found in the logging pipeline.
- **Gap**: No PII redaction mechanism in the logging pipeline. Object keys and bucket names (which could contain PII) are logged as part of normal request processing and replication workflows.
- **Compensating Controls**:
  - Configure log retention policies to limit PII exposure window
  - Implement log scrubbing at the log aggregation layer (e.g., CloudWatch log filters)
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a log sanitization layer that redacts or hashes potentially sensitive fields (object keys, bucket names, client IPs) before writing to persistent logs.
- **Evidence**: `lib/api/BackbeatServer.js` (`_logRequestEnd` method), `conf/config.json` (log configuration)

#### AUTH-Q6: Immutable Audit Logging — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No audit logging of authenticated principals was found. The API server logs request metadata (IP, method, URL, status code) via `werelogs` but does not log the identity of the caller (since auth is IP-based, there is no principal to log). No CloudTrail, immutable log storage, or tamper-evident logging configuration exists.
- **Gap**: No audit trail attributing API actions to specific callers. Without identity-based auth, there is no principal to attribute.
- **Compensating Controls**:
  - Implement identity-based auth first (prerequisite for meaningful audit logging)
  - Log all requests with source IP, timestamp, and action for basic traceability
- **Remediation Timeline**: 60–90 days (depends on AUTH-Q1 identity implementation)
- **Recommendation**: After implementing token-based auth, add audit logging that records the authenticated principal for every operation, stored in an append-only log.
- **Evidence**: `lib/api/BackbeatServer.js` (`_logRequestEnd` — logs IP but not identity)

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, GraphQL schema, or Smithy specification file exists in the repository. API routes are defined programmatically in `lib/api/routes.js` as a JavaScript array.
- **Gap**: No machine-readable API specification. Agent tool generation requires manual route analysis and tool authoring.
- **Compensating Controls**:
  - Generate an OpenAPI spec from the `routes.js` definitions manually or with tooling
  - Document the API surface in a structured README or wiki
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create an OpenAPI 3.0 specification covering all endpoints, request/response schemas, and error formats. Consider auto-generating from route definitions.
- **Evidence**: `lib/api/routes.js`, absence of any `openapi.*`, `swagger.*`, or `*.graphql` files

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Error responses use Arsenal's error objects which include HTTP status codes and customized descriptions (`errors.AccessDenied.customizeDescription(...)`, `errors.MethodNotAllowed`, `errors.RouteNotFound`, `errors.InternalError`, `errors.InvalidQueryParameter`). The error response format is JSON with status code and description. However, there is no explicit `retryable` field or error categorization (terminal vs retriable) in responses.
- **Gap**: Error responses lack a machine-readable `retryable` boolean or error category. Agents cannot programmatically distinguish retriable from terminal errors without parsing description text.
- **Compensating Controls**:
  - Document which HTTP status codes are retriable (5xx) vs terminal (4xx) for agent consumers
  - Add error category metadata to agent tool definitions
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Extend error response bodies to include a `retryable` boolean and `errorCode` string, leveraging the existing Arsenal error structure.
- **Evidence**: `lib/api/BackbeatServer.js` (`_errorResponse` method), `lib/api/BackbeatAPI.js` (validation errors)

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The API has no versioning scheme (no `/v1/` prefix, no `Accept-Version` headers). Routes are exposed under `/_/` prefix only. No schema registry, no breaking change detection in CI, no consumer-driven contract tests (Pact). The CI pipeline (`tests.yaml`) includes functional API tests but no contract validation against a specification.
- **Gap**: No API versioning, no schema documentation, no breaking change detection. Agent tool bindings could break silently on any deployment.
- **Compensating Controls**:
  - Pin agent tool definitions to specific known-good API behavior validated by functional tests
  - Add API contract tests to CI pipeline
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement API versioning (URL prefix or header-based), create an OpenAPI spec, and add spec validation to the CI pipeline using tools like `spectral` or OpenAPI diff.
- **Evidence**: `lib/api/routes.js`, `.github/workflows/tests.yaml`

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Backbeat uses `werelogs` for structured logging with per-request loggers (`logger.newRequestLogger()`), providing correlation via request-scoped log context. Prometheus metrics are exported via `prom-client` and `ZenkoMetrics`. However, no distributed tracing is implemented — no OpenTelemetry, X-Ray, or `traceparent` header propagation was found.
- **Gap**: No distributed tracing capability. While structured logging exists with request-scoped loggers, there is no trace ID propagation for correlating requests across service boundaries.
- **Compensating Controls**:
  - Use Kafka message headers for correlation across async workflows
  - Implement request ID injection at API Gateway level
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Integrate OpenTelemetry SDK into the Node.js application to enable trace context propagation and distributed tracing across Kafka consumers, API calls, and external service calls.
- **Evidence**: `lib/api/BackbeatServer.js` (werelogs request logger), `lib/util/probe.js` (metrics only), absence of OpenTelemetry/X-Ray imports

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive Prometheus alerting rules exist across 6 alert files covering replication, lifecycle, notification, ingestion, and oplog-populator. Alerts include error rates (ReplicationErrorsWarning/Critical), latency (ReplicationLatencyWarning/Critical), RPO thresholds, and service degradation (processor up/down). However, these alerts target the event-processing workflows, not the HTTP API endpoints specifically.
- **Gap**: Alerting covers the event-processing pipeline well but does not specifically cover HTTP API error rates and latency for the management API that agents would consume.
- **Compensating Controls**:
  - Add Prometheus alerts for the API server's HTTP response codes and latency
  - Monitor the API server's health via the existing healthcheck endpoint
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add Prometheus alerting rules for the BackbeatServer HTTP API covering 5xx error rate and P95 latency thresholds.
- **Evidence**: `monitoring/replication/alerts.yaml`, `monitoring/lifecycle/alerts.yaml`, `monitoring/notification/alerts.yaml`

#### ENG-Q1: Infrastructure Governance — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No Terraform, CloudFormation, CDK, Helm charts, or Kustomize files exist in the repository. Infrastructure is configured via environment variables injected through `docker-entrypoint.sh` and `conf/config.json`. Deployment is Docker-container-based. Prometheus alert rules and Grafana dashboards exist but represent observability configuration, not infrastructure provisioning.
- **Gap**: No infrastructure-as-code for the agent-facing API surface. Infrastructure configuration (networking, IAM, API gateway, secrets) is not codified, reviewed, or drift-detected.
- **Compensating Controls**:
  - IaC may exist in a separate deployment repository (Helm charts, Kubernetes manifests)
  - Use Docker image tagging and registry governance for deployment control
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Define infrastructure for the Backbeat API (networking, auth, ingress, secrets) as IaC (Helm chart or Terraform) with PR-based review and drift detection.
- **Evidence**: Absence of `*.tf`, `*.cfn.*`, `cdk.json`, `Chart.yaml`, `kustomization.yaml`; `docker-entrypoint.sh`, `Dockerfile`

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The CI pipeline (`.github/workflows/tests.yaml`) includes unit tests, functional tests (including `api:routes` and `api:retry` test suites), lint, and performance tests. Docker images are built and pushed to GHCR. However, there is no API contract testing (Pact), no OpenAPI spec validation, and no breaking change detection in the pipeline.
- **Gap**: No contract testing or breaking change detection for the API. Functional tests validate behavior but do not guard against schema-level breaking changes that would break agent tool bindings.
- **Compensating Controls**:
  - Functional API tests (`tests/functional/api/routes.js`) provide some regression coverage
  - Manual review of API changes via PR process
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenAPI spec validation and schema diff checking to the CI pipeline. Consider consumer-driven contract tests (Pact) for the management API.
- **Evidence**: `.github/workflows/tests.yaml`, `tests/functional/api/routes.js`

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The Docker build workflow (`.github/workflows/docker-build.yaml`) builds and pushes images to GHCR tagged by git SHA. No blue/green deployment, canary deployment, CodeDeploy rollback, or feature flag mechanism is visible in the repository. Rollback would require redeploying a previous Docker image tag.
- **Gap**: No automated rollback mechanism visible in the repository. Manual Docker image redeployment is the implied rollback strategy.
- **Compensating Controls**:
  - Docker image immutability (SHA-tagged) enables manual rollback to previous version
  - Kubernetes deployment rollback (if deployed via k8s) provides native rollback
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement automated rollback triggers (health-check-based) in the deployment orchestration layer. If using Kubernetes, document the rollback procedure using `kubectl rollout undo`.
- **Evidence**: `.github/workflows/docker-build.yaml`, `Dockerfile`

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Docker-compose configurations exist in `.github/dockerfiles/ft/` for functional testing with all dependencies (Kafka, ZooKeeper, MongoDB, Redis, CloudServer). The CI pipeline spins up a full environment for functional tests. However, no production-equivalent staging environment is documented or provisioned for agent testing.
- **Gap**: CI testing environment exists but no production-equivalent staging/sandbox documented for agent testing.
- **Compensating Controls**:
  - Use the existing Docker-compose CI infrastructure as a sandbox template
  - Provision a dedicated staging namespace in Kubernetes using the Docker images
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document how to provision a staging environment using the existing Docker-compose infrastructure. Create a dedicated sandbox configuration for agent integration testing.
- **Evidence**: `.github/workflows/tests.yaml` (services section), `.github/dockerfiles/`

---

## INFOs — Architecture and Design Inputs

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Write endpoints exist (POST for retryFailedCRR, pauseService, resumeService, applyWorkflowConfiguration). The retryFailedCRR endpoint processes a list of failed objects for retry. No explicit idempotency keys are used on these endpoints.
- **Implication**: If agent_scope is expanded to write-enabled, idempotency must be evaluated as BLOCKER. Currently informational since read-only agents will not invoke write endpoints.
- **Recommendation**: Plan idempotency key support for write endpoints before expanding agent scope.
- **Evidence**: `lib/api/routes.js` (POST routes), `lib/api/BackbeatAPI.js`

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: API responses are JSON (`application/json` content type set in `BackbeatServer._response`). The response serialization uses `JSON.stringify(data)`. Prometheus metrics endpoint returns plain text (Prometheus exposition format).
- **Implication**: JSON responses are well-suited for agent consumption via LLM-based tool parsing.
- **Recommendation**: No action needed. JSON is the ideal format for agent tool responses.
- **Evidence**: `lib/api/BackbeatServer.js` (`_response` method)

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limit headers (`X-RateLimit-Remaining`, `Retry-After`) are returned by the API. No rate limit documentation exists.
- **Implication**: Agents have no visibility into capacity limits and cannot self-throttle. If rate limiting is added (per STATE-Q5 recommendation), headers should be included.
- **Recommendation**: When implementing rate limiting, include standard rate limit headers in API responses.
- **Evidence**: `lib/api/BackbeatServer.js` (response headers include only Content-Type and Content-Length)

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: INFO
- **Finding**: Backbeat uses service-level authentication (STS AssumeRole, account credentials, Vault-based auth) for internal service-to-service communication. The `CredentialsManager` manages role-based credentials for downstream S3 and Vault calls. However, these are all service identities — there is no concept of propagating a caller's identity through the processing pipeline.
- **Implication**: For an event-processor archetype, identity propagation is less critical since the system acts under its own service identity to process events asynchronously. Agent calls to the management API do not trigger on-behalf-of workflows.
- **Recommendation**: No immediate action for read-only agent scope. Consider identity propagation if agents are given write access to the management API.
- **Evidence**: `lib/credentials/CredentialsManager.js`, `conf/config.json` (auth sections)

### AUTH-Q5: Credential Management

- **Severity**: INFO
- **Finding**: Credentials are managed through multiple mechanisms: (1) STS AssumeRole for temporary credentials with automatic refresh (`CredentialsManager.js`), (2) external credential files on tmpfs (`resolveExternalFileSync`), (3) configuration-based auth accounts in `conf/config.json`. A test-only `conf/authdata.json` contains static credentials but is clearly for development. Production credentials are sourced from Vault or STS.
- **Implication**: The credential management approach (STS + Vault + external files) is reasonable for a self-hosted system. No hardcoded production credentials were found.
- **Recommendation**: Ensure `conf/authdata.json` is excluded from production deployments (it appears to be dev-only).
- **Evidence**: `lib/credentials/CredentialsManager.js`, `conf/authdata.json` (dev-only), `conf/config.json`

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO (event-processor archetype)
- **Finding**: For the event-processing workflows, Backbeat implements retry with exponential backoff and configurable max retries per destination type. Failed replication objects are tracked in a dedicated Kafka topic (`backbeat-replication-failed`) with retry capability via the API. Replay topics exist for re-processing. However, there is no formal saga/compensation pattern for multi-step workflows.
- **Implication**: For read-only agent scope, compensation is informational. The retry and replay mechanisms provide partial compensation for event-processing failures.
- **Recommendation**: If agent scope expands to write-enabled, evaluate whether pause/resume operations need rollback capability.
- **Evidence**: `conf/config.json` (retry configurations), `lib/api/routes.js` (retryFailedCRR endpoint)

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Kafka consumer concurrency is controlled via configurable `concurrency` parameter (default 10). MongoDB writes use `writeConcern: "majority"`. ZooKeeper is used for distributed coordination and leader election. However, the API layer has no optimistic locking or concurrency controls for concurrent API calls.
- **Implication**: Read-only agents do not perform writes, so API-level concurrency controls are informational. The event-processing layer has appropriate concurrency management.
- **Recommendation**: If agent scope expands to write-enabled, implement optimistic locking on stateful API operations (pause/resume/configuration).
- **Evidence**: `conf/config.json` (concurrency settings), `lib/BackbeatConsumer.js`

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Batch size controls exist for queue processing (`batchMaxRead: 10000`, `batchTimeoutMs: 9000`). Concurrency limits cap parallel processing. However, no per-caller transaction limits exist for API operations.
- **Implication**: Read-only agents cannot trigger write-based blast radius. Event-processing batch limits provide operational bounds.
- **Recommendation**: If expanding to write-enabled scope, implement per-caller limits on operations like retryFailedCRR (limit records per request).
- **Evidence**: `conf/config.json` (batch and concurrency settings)

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The pause/resume mechanism provides a form of human-gatable workflow control — services can be paused (no processing) and resumed with optional scheduling. However, there is no draft/pending state for API write operations themselves.
- **Implication**: Read-only agents do not need draft states. The pause/resume capability provides operational control for human oversight.
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: `lib/api/routes.js` (pause/resume routes)

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable approval gates exist. Operations execute immediately when invoked via the API.
- **Implication**: Informational for read-only scope. If agents gain write access, approval gates should be considered for destructive operations.
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: `lib/api/BackbeatServer.js`, `lib/api/BackbeatAPI.js`

### DATA-Q2: Data Residency and Sovereignty ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO (event-processor; data is S3 object metadata, not PII-bearing)
- **Finding**: Backbeat processes S3 object metadata (bucket names, keys, version IDs) and replicates objects across configured destinations (AWS S3, Azure, GCP, Scality). Data residency is determined by the replication configuration (source/destination sites). No explicit residency constraints or compliance markers are present in the code.
- **Implication**: The data processed (S3 object metadata) is typically not subject to strict PII residency requirements. Actual object data residency is governed by S3 bucket configurations, not Backbeat itself.
- **Recommendation**: If agents process data that includes customer content paths or metadata with PII implications, document residency boundaries in the replication configuration.
- **Evidence**: `conf/config.json` (destination bootstrapList with site locations)

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No formal data quality scores or completeness metrics exist. The system tracks operational metrics (backlog, completions, failures, throughput) which serve as indirect data quality signals for replication and lifecycle operations.
- **Implication**: Operational metrics (RPO, failure rates) provide proxy signals for data pipeline quality. No formal data quality framework is needed for this system type.
- **Recommendation**: No action needed. Operational metrics serve the data quality awareness purpose for an event processor.
- **Evidence**: `monitoring/replication/alerts.yaml` (RPO and error rate alerts)

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: Custom Prometheus metrics track replication completions, failures, latency, RPO, backlog size, and throughput per location. Grafana dashboards visualize these business outcomes. These are genuine business outcome metrics (replication SLA compliance, lifecycle execution rates) rather than just infrastructure metrics.
- **Implication**: Strong business outcome observability exists for the event-processing workflows. These metrics could inform agent decision-making about system health.
- **Recommendation**: Expose metrics via a documented endpoint that agents can query for operational awareness.
- **Evidence**: `monitoring/replication/dashboard.json`, `monitoring/lifecycle/dashboard.json`, `lib/util/metrics.js`

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: BLOCKER
- **Finding**: HTTP API exists on port 8900 with 15+ endpoints defined in `lib/api/routes.js`, but it is an internal management interface with IP-based access control and no formal documentation or versioning.
- **Gap**: No formal, documented, versioned API contract suitable for stable agent tool binding.
- **Recommendation**: Create an OpenAPI specification documenting all routes, schemas, and error formats.
- **Evidence**: `lib/api/routes.js`, `lib/api/BackbeatServer.js`, `conf/config.json`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, GraphQL schema, or Smithy specification file exists. Routes defined programmatically only.
- **Gap**: No machine-readable specification for automated tool generation.
- **Recommendation**: Create OpenAPI 3.0 specification from route definitions.
- **Evidence**: `lib/api/routes.js`, absence of spec files

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: Arsenal error objects provide HTTP codes and descriptions in JSON, but lack a `retryable` boolean or error category field.
- **Gap**: No machine-readable retryability signal in error responses.
- **Recommendation**: Add `retryable` boolean and `errorCode` to error response body.
- **Evidence**: `lib/api/BackbeatServer.js` (`_errorResponse`)

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Write endpoints (POST for retry, pause, resume, config) lack idempotency keys.
- **Gap**: No idempotency mechanism on write endpoints.
- **Recommendation**: Plan idempotency support before expanding agent scope to write-enabled.
- **Evidence**: `lib/api/routes.js`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: Responses are JSON (`application/json`). Metrics endpoint returns Prometheus text format.
- **Gap**: N/A — JSON is ideal for agent consumption.
- **Recommendation**: No action needed.
- **Evidence**: `lib/api/BackbeatServer.js`

#### API-Q6: Asynchronous Operation Support
- **Severity**: INFO
- **Finding**: Backbeat is inherently asynchronous — its entire architecture is built around Kafka message queues with background workers. The management API supports async patterns: pause/resume operations affect background processing, and the retryFailedCRR endpoint submits retry jobs to Kafka topics for async processing. The system exposes status/metrics endpoints for monitoring progress of async operations.
- **Gap**: None significant for the current use case. The system is natively async with queue-based job submission and metrics/status polling.
- **Recommendation**: No action needed. The architecture naturally supports async patterns.
- **Evidence**: `lib/api/routes.js` (status/metrics polling endpoints), `conf/config.json` (Kafka topics for job submission)

#### API-Q7: Event Emission for State Changes
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `event-processor`, agent_scope: `read-only`.
- **Trigger**: Service has state changes (stateful-crud, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit headers or documentation exist.
- **Gap**: Agents cannot discover or self-throttle against rate limits.
- **Recommendation**: Include standard rate limit headers when rate limiting is implemented.
- **Evidence**: `lib/api/BackbeatServer.js`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: The API server uses IP-based access control only (`ipCheck.ipMatchCidrList` with `allowFrom` CIDR list). There is no machine identity authentication (no OAuth2, no API keys with principal attribution, no mTLS). Internally, Backbeat uses STS AssumeRole and Vault-based auth for service-to-service calls to S3/Vault, but the management API itself has no identity-based authentication.
- **Gap**: No machine identity authentication on the agent-facing API. IP-based ACL provides no principal attribution for audit, no identity lifecycle management, and no fine-grained access control.
- **Recommendation**: Implement token-based authentication (OAuth2 client credentials or API keys with principal attribution) on the management API.
- **Evidence**: `lib/api/BackbeatServer.js` (`_isValidRequest` — ipCheck only), `conf/config.json` (`server.healthChecks.allowFrom`)

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: IP-based access grants full access to all endpoints. IAM policies in `policies/` show scoped permissions for internal service operations but not for the management API.
- **Gap**: No per-identity permission scoping at the API layer.
- **Recommendation**: Implement per-identity route-level authorization.
- **Evidence**: `lib/api/BackbeatServer.js`, `policies/queue_populator_policy.json`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization. All callers from allowed IPs can execute all operations.
- **Gap**: No RBAC/ABAC enforcement differentiating read from write operations.
- **Recommendation**: Add action-permission matrix middleware.
- **Evidence**: `lib/api/BackbeatServer.js`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: Service-level identity used for downstream calls (STS AssumeRole). No caller identity propagation through event processing.
- **Gap**: No on-behalf-of identity propagation (appropriate for event-processor archetype).
- **Recommendation**: No action for current scope.
- **Evidence**: `lib/credentials/CredentialsManager.js`

#### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: Credentials managed via STS AssumeRole (temporary, auto-refreshing), external files on tmpfs, and Vault integration. Dev-only `authdata.json` contains static credentials.
- **Gap**: No production credential exposure found. Dev credentials in `conf/authdata.json` are clearly test-only.
- **Recommendation**: Ensure `authdata.json` is never deployed to production.
- **Evidence**: `lib/credentials/CredentialsManager.js`, `conf/authdata.json`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No audit logging of authenticated principals. API logs request metadata but not caller identity.
- **Gap**: No audit trail for API actions. No immutable log storage.
- **Recommendation**: Implement identity-based auth first, then add principal-attributed audit logging.
- **Evidence**: `lib/api/BackbeatServer.js` (`_logRequestEnd`)

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: No individual identity suspension. Access control is CIDR-list-based; revocation requires config change and restart.
- **Gap**: Cannot suspend individual agent access without affecting all callers.
- **Recommendation**: Implement API key or token-based auth with individual revocation.
- **Evidence**: `lib/api/BackbeatServer.js`, `conf/config.json`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO (event-processor archetype with no agent-invoked write workflows)
- **Finding**: Retry with exponential backoff, replay topics, and failed-CRR tracking provide partial compensation for event processing failures. No formal saga pattern.
- **Gap**: No formal compensation/rollback for API write operations.
- **Recommendation**: Evaluate compensation needs if agent scope expands to write-enabled.
- **Evidence**: `conf/config.json` (retry configurations)

#### STATE-Q2: Queryable Current State
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `event-processor`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Kafka consumer concurrency controlled, MongoDB writeConcern, ZooKeeper coordination. No API-level concurrency controls.
- **Gap**: No optimistic locking on API operations (informational for read-only scope).
- **Recommendation**: Add concurrency controls to write APIs if scope expands.
- **Evidence**: `conf/config.json`, `lib/BackbeatConsumer.js`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: INFO
- **Finding**: Extensive circuit breaker implementation exists using the `breakbeat` library. `CircuitBreakerGroup` (`extensions/lifecycle/CircuitBreakerGroup.js`) implements per-workflow, per-topic, and per-location circuit breakers. Circuit breaker states are monitored via Prometheus metrics (`s3_circuit_breaker` gauge, `s3_circuit_breaker_errors_count` counter). Probes include `kafkaConsumerLag` for Kafka-based circuit breaking. Retry with exponential backoff is configured per destination type (aws_s3, azure, gcp, scality) with configurable `maxRetries`, `timeoutS`, and backoff parameters.
- **Gap**: None significant — circuit breakers and retry logic are well-implemented for the event-processing pipeline's external dependencies.
- **Recommendation**: Ensure circuit breaker coverage extends to all external dependency calls, including the management API's calls to Redis, ZooKeeper, and MongoDB.
- **Evidence**: `lib/CircuitBreaker.js`, `extensions/lifecycle/CircuitBreakerGroup.js`, `lib/BackbeatConsumer.js`, `conf/config.json` (retry configurations)

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No HTTP-level rate limiting on the API server. Consumer-level concurrency and batch size limits exist but do not protect the API endpoints.
- **Gap**: No API-layer rate limiting to prevent agent traffic storms.
- **Recommendation**: Add rate limiting middleware to the HTTP server.
- **Evidence**: `lib/api/BackbeatServer.js`, `lib/BackbeatConsumer.js`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Batch size and concurrency limits exist for event processing. No per-caller transaction limits on API.
- **Gap**: No per-caller transaction limits (informational for read-only scope).
- **Recommendation**: Implement per-caller limits before expanding to write-enabled scope.
- **Evidence**: `conf/config.json`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `event-processor`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Pause/resume mechanism provides operational gating. No draft state for API writes.
- **Gap**: No draft/pending state (informational for read-only scope).
- **Recommendation**: No action needed for current scope.
- **Evidence**: `lib/api/routes.js`

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable approval gates. Operations execute immediately.
- **Gap**: No approval gates (informational for read-only scope).
- **Recommendation**: No action needed for current scope.
- **Evidence**: `lib/api/BackbeatServer.js`

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: Docker-compose configurations exist in `.github/dockerfiles/ft/` for functional testing with all dependencies (Kafka, ZooKeeper, MongoDB, Redis, CloudServer). The CI pipeline spins up a full environment for functional tests. However, no production-equivalent staging environment is documented or provisioned.
- **Gap**: CI testing environment exists but no production-equivalent staging/sandbox documented for agent testing.
- **Recommendation**: Document how to provision a staging environment using the existing Docker-compose infrastructure. Consider creating a dedicated sandbox configuration.
- **Evidence**: `.github/workflows/tests.yaml` (services section), `.github/dockerfiles/`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification ⚡
- **Severity**: INFO
- **Finding**: Stage A evaluation: Backbeat processes S3 object metadata (bucket names, object keys, version IDs, replication status). It does not store user PII, PHI, financial records, or credentials in its own data stores. The metadata it processes belongs to the S3 system (CloudServer/Vault). `conf/authdata.json` contains test credentials only. The service's purpose is event-driven data movement, not user data storage.
- **Gap**: N/A — Not a data-handling target for PII/sensitive data. Object metadata (keys, buckets) is operational data belonging to the S3 platform.
- **Recommendation**: No action needed. Data classification is the responsibility of the S3 platform that owns the objects being replicated.
- **Evidence**: `conf/config.json`, `lib/models/ObjectQueueEntry.js`, `conf/authdata.json` (dev-only)

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Replication destinations are configurable by site (AWS S3, Azure, GCP, Scality locations). Residency is a property of the S3 replication configuration, not of Backbeat itself.
- **Gap**: No residency constraints applicable to the event-processor's operational metadata.
- **Recommendation**: No action needed for the Backbeat service itself. Data residency is governed by S3 bucket replication configurations.
- **Evidence**: `conf/config.json` (destination.bootstrapList)

#### DATA-Q3: Selective Query Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `event-processor`, agent_scope: `read-only`.
- **Trigger**: Service has list/query endpoints with potentially unbounded results
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q4: System of Record Designations
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `event-processor`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `event-processor`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: Structured logging via `werelogs` captures request metadata (IPs, URLs with object keys/bucket names). No PII redaction middleware found.
- **Gap**: Object keys and bucket names logged without redaction; these may contain user-identifiable path components.
- **Recommendation**: Add log sanitization for potentially sensitive fields.
- **Evidence**: `lib/api/BackbeatServer.js` (`_logRequestEnd`)

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: Operational metrics (RPO, failure rates, backlog) serve as data quality proxies.
- **Gap**: No formal data quality score (appropriate for event-processor).
- **Recommendation**: No action needed.
- **Evidence**: `monitoring/replication/alerts.yaml`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: No API versioning, no schema registry, no contract testing, no breaking change detection in CI.
- **Gap**: Agent tool bindings can break silently on any deployment.
- **Recommendation**: Implement API versioning and contract testing.
- **Evidence**: `lib/api/routes.js`, `.github/workflows/tests.yaml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Field names in code and config are readable and semantic: `opsPending`, `bytesDone`, `completions`, `throughput`, `backlog`, `replicationStatus`, `bucketName`, `objectKey`. No legacy abbreviations or codes requiring a data dictionary.
- **Gap**: None — field naming is clear and semantic.
- **Recommendation**: No action needed.
- **Evidence**: `lib/api/routes.js` (dataPoints), `conf/config.json`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal data catalog. Documentation in `docs/` describes features but not data schemas. Configuration validation via Joi schemas (`lib/config.joi.js`) provides some schema documentation.
- **Gap**: No formal metadata catalog. Joi schemas provide implicit documentation.
- **Recommendation**: Consider documenting the Kafka topic schemas and API response formats in a structured catalog.
- **Evidence**: `lib/config.joi.js`, `docs/`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: Structured logging with `werelogs` and per-request loggers. No distributed tracing (OpenTelemetry/X-Ray).
- **Gap**: No trace ID propagation across service boundaries.
- **Recommendation**: Integrate OpenTelemetry SDK.
- **Evidence**: `lib/api/BackbeatServer.js`, `lib/util/probe.js`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive Prometheus alerting for event-processing workflows but not specifically for the HTTP management API.
- **Gap**: No alerting on the API server's error rate and latency.
- **Recommendation**: Add HTTP API alerting rules.
- **Evidence**: `monitoring/replication/alerts.yaml`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: Custom Prometheus metrics track replication completions, failures, latency, RPO, backlog. Grafana dashboards visualize business outcomes.
- **Gap**: None — strong business outcome metrics exist.
- **Recommendation**: Expose metrics in an agent-queryable format.
- **Evidence**: `monitoring/`, `lib/util/metrics.js`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance
- **Severity**: RISK-QUALITY
- **Finding**: No IaC in this repository. Docker-based deployment with env-var configuration.
- **Gap**: No IaC for agent-facing infrastructure. May exist in separate deployment repo.
- **Recommendation**: Define agent-facing infrastructure as IaC.
- **Evidence**: `Dockerfile`, `docker-entrypoint.sh`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: CI has unit, functional, and performance tests including API route tests. No contract testing or breaking change detection.
- **Gap**: No API contract testing in CI.
- **Recommendation**: Add OpenAPI spec validation and contract tests.
- **Evidence**: `.github/workflows/tests.yaml`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: Docker images tagged by SHA on GHCR. No automated rollback mechanism in repository.
- **Gap**: No automated rollback. Manual Docker image redeployment required.
- **Recommendation**: Implement health-check-based automated rollback.
- **Evidence**: `.github/workflows/docker-build.yaml`

#### ENG-Q4: API Test Coverage
- **Severity**: INFO
- **Finding**: Functional API tests exist in `tests/functional/api/routes.js` and `tests/functional/api/retry.js`, run as separate CI jobs (`api:routes` and `api:retry` in the test matrix). These tests validate route behavior, error responses, and retry logic against a full service stack with real dependencies (Kafka, ZooKeeper, MongoDB, Redis). Unit tests in `tests/unit/api/` provide additional coverage.
- **Gap**: None significant for the current API surface. Functional tests cover the management API endpoints with real service dependencies.
- **Recommendation**: Add response schema validation to API tests to catch response format changes that could break agent tool bindings.
- **Evidence**: `.github/workflows/tests.yaml` (api:routes, api:retry test suites), `tests/functional/api/`

#### ENG-Q5: Encryption at Rest
- **Severity**: INFO
- **Finding**: No encryption-at-rest configuration exists in this repository. Backbeat itself does not define or manage data stores — it connects to externally provisioned MongoDB, Redis, Kafka, and S3 instances via connection strings in `conf/config.json`. Encryption at rest for these stores is the responsibility of the infrastructure provisioning layer (which is not in this repository).
- **Gap**: No encryption-at-rest configuration in the application repository. This is expected since data store provisioning is external.
- **Recommendation**: Verify encryption-at-rest is configured in the infrastructure provisioning layer for MongoDB, Redis, and Kafka broker storage. Document the encryption status of dependent data stores.
- **Evidence**: `conf/config.json` (connection strings only, no encryption config), absence of IaC in repository

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| lib/api/routes.js | API-Q1, API-Q2, API-Q3, API-Q4, API-Q5, API-Q8, DISC-Q1, DISC-Q2, STATE-Q1, HITL-Q1 |
| lib/api/BackbeatServer.js | API-Q1, API-Q3, API-Q5, API-Q8, AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7, STATE-Q5, DATA-Q6, OBS-Q1, HITL-Q2 |
| lib/api/BackbeatAPI.js | API-Q1, API-Q3, API-Q4 |
| lib/credentials/CredentialsManager.js | AUTH-Q4, AUTH-Q5 |
| lib/CircuitBreaker.js | STATE-Q4 |
| extensions/lifecycle/CircuitBreakerGroup.js | STATE-Q4 |
| lib/BackbeatConsumer.js | STATE-Q3, STATE-Q5 |
| lib/util/probe.js | OBS-Q1 |
| lib/util/metrics.js | OBS-Q3 |
| extensions/notification/utils/auth.js | AUTH-Q5 |
| lib/config.joi.js | DISC-Q3 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| .github/workflows/tests.yaml | DISC-Q1, ENG-Q2, ENG-Q4, HITL-Q3 |
| .github/workflows/docker-build.yaml | ENG-Q3 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| Dockerfile | ENG-Q1, ENG-Q3 |
| docker-entrypoint.sh | ENG-Q1, AUTH-Q5 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| conf/config.json | API-Q1, AUTH-Q1, AUTH-Q5, AUTH-Q7, STATE-Q1, STATE-Q3, STATE-Q5, STATE-Q6, DATA-Q1, DATA-Q2, DISC-Q2 |
| conf/authdata.json | AUTH-Q5, DATA-Q1 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| package.json | ENG-Q2 |

### Monitoring / Alerting
| File | Questions Referenced |
|------|---------------------|
| monitoring/replication/alerts.yaml | OBS-Q2, DATA-Q7 |
| monitoring/lifecycle/alerts.yaml | OBS-Q2 |
| monitoring/notification/alerts.yaml | OBS-Q2 |

### IAM Policies
| File | Questions Referenced |
|------|---------------------|
| policies/queue_populator_policy.json | AUTH-Q2 |
