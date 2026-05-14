# Agentic Readiness Analysis Report

**Target**: Flowise (monorepo)
**Date**: 2025-07-21
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**Repository Type**: monorepo
**Service Archetype**: stateful-crud (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: typescript, ai, llm
**Context**: Low-code UI for building LLM flows and agents.

**Archetype Justification**: The primary deployable service (packages/server) uses TypeORM with SQLite/PostgreSQL/MySQL for persistent state, exposes full CRUD endpoints for 19+ entity types (ChatFlow, ChatMessage, ApiKey, Credential, Tool, Variable, etc.), and manages user-specific data via workspaceId scoping on all entities.

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 1 | **RISK-SAFETY**: 5 | **RISK-QUALITY**: 16 | **INFOs**: 20

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days. The single BLOCKER (DATA-Q1: Sensitive Data Classification) must be resolved before any agent can be granted read access to this system. With 5 RISK-SAFETY findings, once the BLOCKER is resolved, the system would be "Pilot-Ready (Safety Concerns)" requiring a supervised pilot with elevated safety oversight.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 1 |
| RISK-SAFETY | 5 |
| RISK-QUALITY | 16 |
| INFO | 20 |
| N/A | 0 |
| Not Evaluated (extended) | 1 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 18
**Extended Questions Not Triggered**: 1 (STATE-Q7)
**Questions N/A (repo_type: monorepo)**: 0
**Service Archetype**: stateful-crud (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: The Flowise database contains PII and sensitive data without field-level classification or tagging. The `Lead` entity (`packages/server/src/database/entities/Lead.ts`) stores `name`, `email`, and `phone` fields with no classification markers, no field-level encryption, and no access controls distinguishing PII from non-sensitive data. The `Credential` entity stores an `encryptedData` field (application-level encryption via `crypto-js`), but this is not a classification system. The `ChatMessage` entity stores `content` (user conversations) and `leadEmail` fields which may contain PII. No Amazon Macie integration, no data classification tags, and no field-level access control policies were found.
- **Gap**: No sensitive data is classified or tagged at the field level. An agent granted read access would receive PII without any system-level control preventing it.
- **Remediation**:
  - **Immediate**: Create a data classification inventory mapping each entity field to a sensitivity level (PUBLIC, INTERNAL, CONFIDENTIAL, PII). At minimum, classify `Lead.email`, `Lead.phone`, `Lead.name`, `ChatMessage.content`, `ChatMessage.leadEmail`, and `Credential.encryptedData`.
  - **Target State**: Field-level classification tags on all entities with PII, enforced at the API layer so agent identities with read-only permissions cannot retrieve PII fields unless explicitly authorized.
  - **Estimated Effort**: Medium (30–60 days)
  - **Dependencies**: AUTH-Q2 (scoped permissions) is already in place; classification enforcement can leverage the existing RBAC model.
- **Evidence**: `packages/server/src/database/entities/Lead.ts`, `packages/server/src/database/entities/ChatMessage.ts`, `packages/server/src/database/entities/Credential.ts`

---

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Enterprise audit system is limited to login activity tracking only (`fetchLoginActivity`). No general-purpose audit logging for API operations. No CloudTrail, no immutable log storage. Application logs via Winston record HTTP requests but are not immutable audit trails.
- **Gap**: No immutable, tamper-evident audit trail for API operations.
- **Compensating Controls**:
  - Deploy behind an API Gateway with access logging enabled
  - Enable CloudTrail for the AWS account
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement audit logging middleware recording the authenticated principal for every API operation, with logs shipped to immutable storage.
- **Evidence**: `packages/server/src/enterprise/routes/audit/index.ts`, `packages/server/src/utils/logger.ts`

#### STATE-Q1: Compensation and Rollback ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No saga patterns, compensation logic, or rollback handlers found. TypeORM migration revert is a schema tool, not runtime compensation.
- **Gap**: No compensation or rollback for multi-step operations.
- **Compensating Controls**:
  - Scope initial agent operations to single-resource reads only
  - Implement database transactions at the service layer
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Wrap multi-step write operations in TypeORM transactions.
- **Evidence**: `packages/server/src/services/` (absence of compensation patterns)

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No circuit breakers, retry logic with backoff, or timeout configurations on LLM provider calls. AbortControllerPool provides cancellation but not circuit-breaking.
- **Gap**: No circuit breakers to prevent cascading failures when LLM providers are unavailable.
- **Compensating Controls**:
  - Configure HTTP client timeouts via environment variables
  - Deploy a service mesh with circuit breaker policies
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add circuit breaker middleware (e.g., `opossum`) around LLM provider calls.
- **Evidence**: `packages/server/src/AbortControllerPool.ts`, `packages/components/package.json`

#### DATA-Q2: Data Residency and Sovereignty ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Multi-region storage backends (S3, GCS, Azure) with no residency enforcement. No GDPR/LGPD compliance controls.
- **Gap**: No data residency controls. Data can be stored and accessed across jurisdictions without enforcement.
- **Compensating Controls**:
  - Document which data classes are subject to residency requirements
  - Deploy within a single compliance-approved region
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add data residency configuration enforcing storage region constraints.
- **Evidence**: `packages/server/.env.example`, `docker/docker-compose.yml`

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Log sanitization exists via `LOG_SANITIZE_BODY_FIELDS` and `LOG_SANITIZE_HEADER_FIELDS` env vars but is opt-in. Default deployments have no PII redaction. The `.env.example` documents recommended fields but they must be explicitly set.
- **Gap**: PII sanitization in logs is opt-in, not default-on.
- **Compensating Controls**:
  - Set sanitization env vars in deployment configuration
  - Deploy CloudWatch log filters for PII patterns
- **Remediation Timeline**: Immediate (config) to 30 days (code change for defaults)
- **Recommendation**: Make sanitization fields default-on in code rather than requiring env var configuration.
- **Evidence**: `packages/server/src/utils/logger.ts`, `packages/server/.env.example`

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: OpenAPI 3.0.3 spec exists (2,665 lines, ~14 tag groups) but covers ~28% of the 50+ actual route groups. Manually maintained.
- **Gap**: Spec covers less than a third of the API surface.
- **Compensating Controls**:
  - Use existing spec for initial agent tools (prediction/chatflow endpoints are documented)
  - Supplement with runtime API exploration
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Migrate to annotation-based spec generation.
- **Evidence**: `packages/api-documentation/src/yml/swagger.yml`, `packages/server/src/routes/index.ts`

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Error handler returns `{statusCode, success, message}` JSON. No `retryable` field or error code enumeration.
- **Gap**: Agents cannot distinguish retriable from terminal errors.
- **Compensating Controls**:
  - Map HTTP status codes to retry logic at the agent orchestration layer
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `errorCode` and `retryable` fields to error responses.
- **Evidence**: `packages/server/src/middlewares/errors/index.ts`

#### AUTH-Q4: Identity Propagation and Delegation — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: JWT-based identity via Passport.js. No distinction between agent-as-self vs agent-on-behalf-of-user.
- **Gap**: No identity delegation or agent/human distinction.
- **Compensating Controls**:
  - Create dedicated API keys with descriptive keyNames for agent use
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add `identity_type` field to API key entity.
- **Evidence**: `packages/server/src/utils/validateKey.ts`, `packages/server/src/database/entities/ApiKey.ts`

#### AUTH-Q5: Credential Management — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Supports AWS Secrets Manager but defaults to local filesystem. Weak defaults detected and overridden. No secret rotation.
- **Gap**: Default deployment uses local filesystem secrets with no rotation.
- **Compensating Controls**:
  - Configure `SECRETKEY_STORAGE_TYPE=aws`
  - Use container orchestration for secret injection
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Make AWS Secrets Manager the recommended default.
- **Evidence**: `packages/server/src/enterprise/utils/authSecrets.ts`, `packages/server/.env.example`

#### DATA-Q3: Selective Query Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Some endpoints have pagination (page/limit). Inconsistent across routes. No cursor-based pagination.
- **Gap**: Unbounded result sets possible on some endpoints.
- **Compensating Controls**:
  - Configure agent tools with explicit `limit` parameters
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Standardize pagination with default limits.
- **Evidence**: `packages/api-documentation/src/yml/swagger.yml`, `packages/server/src/services/apikey/index.ts`

#### DATA-Q4: System of Record Designations — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No system-of-record designations or data ownership documentation.
- **Gap**: No formal SoR designations.
- **Compensating Controls**:
  - Document Flowise as SoR for its domain entities
- **Remediation Timeline**: 30 days
- **Recommendation**: Create data ownership matrix.
- **Evidence**: `packages/server/src/database/entities/`

#### DATA-Q5: Temporal Metadata and Freshness — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Entities have `createdDate`/`updatedDate` via TypeORM. No freshness headers or UTC enforcement.
- **Gap**: No freshness signaling in API responses.
- **Compensating Controls**:
  - Note Flowise data is strongly consistent (direct DB reads)
- **Remediation Timeline**: 30 days
- **Recommendation**: Add Last-Modified headers. Enforce UTC storage.
- **Evidence**: `packages/server/src/database/entities/ChatFlow.ts`, `packages/server/src/database/entities/Variable.ts`

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: `/api/v1/` URL versioning. TypeORM migrations. No breaking change detection in CI.
- **Gap**: No automated breaking change detection.
- **Compensating Controls**:
  - Pin agent tools to specific API versions
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenAPI diff check to CI pipeline.
- **Evidence**: `packages/server/src/index.ts`, `.github/workflows/main.yml`

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: OpenTelemetry metrics + Winston JSON logging. Trace exporter deps present but tracer provider not active. No correlation IDs.
- **Gap**: Trace propagation not active. Logs lack correlation IDs.
- **Compensating Controls**:
  - Enable OpenTelemetry auto-instrumentation
- **Remediation Timeline**: 30 days
- **Recommendation**: Enable tracer provider. Add request ID middleware.
- **Evidence**: `packages/server/src/metrics/OpenTelemetry.ts`, `packages/server/src/utils/logger.ts`

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Metrics collected but no alerting configuration in the codebase.
- **Gap**: No alerting on error rates or latency.
- **Compensating Controls**:
  - Configure Prometheus Alertmanager or CloudWatch alarms externally
- **Remediation Timeline**: 30 days
- **Recommendation**: Define alerting rules for HTTP error rates and latency.
- **Evidence**: `packages/server/src/metrics/Prometheus.ts`, `packages/server/src/metrics/OpenTelemetry.ts`

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Docker-compose for local development. No dedicated staging environment, seed data, or synthetic data generators.
- **Gap**: No production-equivalent staging environment.
- **Compensating Controls**:
  - Use Docker-compose with PostgreSQL for agent testing
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Define staging environment config with seed data.
- **Evidence**: `docker/docker-compose.yml`, `.github/workflows/main.yml`

#### ENG-Q1: Infrastructure Governance — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No IaC files. Docker files and docker-compose only. No drift detection.
- **Gap**: Agent-facing surface not defined as code.
- **Compensating Controls**:
  - Use container orchestration platforms with IaC templates
- **Remediation Timeline**: 60–120 days
- **Recommendation**: Create IaC for deployment infrastructure.
- **Evidence**: `Dockerfile`, `docker/Dockerfile`, `docker/docker-compose.yml`

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: CI pipeline exists but no API contract testing or breaking change detection.
- **Gap**: No API contract tests in CI.
- **Compensating Controls**:
  - Add OpenAPI validation step to CI
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenAPI diff and contract tests.
- **Evidence**: `.github/workflows/main.yml`

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Docker image tags for versioning. Manual rollback only.
- **Gap**: No automated rollback capability.
- **Compensating Controls**:
  - Use versioned tags (not `latest`)
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement health-check-based automatic rollback.
- **Evidence**: `.github/workflows/docker-image-dockerhub.yml`, `docker/docker-compose.yml`

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Jest + Cypress configured. Only 8 test files across server and components. No API integration tests.
- **Gap**: Minimal test coverage for 50+ route groups.
- **Compensating Controls**:
  - Prioritize tests for agent-consumed endpoints
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Create API integration tests using supertest.
- **Evidence**: `packages/server/jest.config.js`, `packages/server/cypress.config.ts`

#### ENG-Q5: Encryption at Rest — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Application-level encryption for credentials. No database-level encryption config. No KMS. S3 storage has no enforced encryption.
- **Gap**: Encryption at rest depends on deployment infrastructure.
- **Compensating Controls**:
  - Deploy with RDS encryption enabled; enable S3 default encryption
- **Remediation Timeline**: 30 days
- **Recommendation**: Document encryption requirements. Add S3 encryption config option.
- **Evidence**: `packages/server/src/database/entities/Credential.ts`, `packages/server/src/DataSource.ts`

---

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface
- **Severity**: INFO (control present)
- **Finding**: Comprehensive REST API via Express.js with 50+ route groups under `/api/v1/`. OpenAPI 3.0.3 specification exists.
- **Implication**: Agents can bind to the REST API as the integration surface.
- **Recommendation**: Expand OpenAPI spec coverage.
- **Evidence**: `packages/server/src/routes/index.ts`, `packages/api-documentation/src/yml/swagger.yml`

### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO (control present)
- **Finding**: API key auth with workspace scoping and principal attribution. JWT via Passport.js.
- **Implication**: Machine identity supported. Agents can authenticate via dedicated API keys.
- **Recommendation**: Create dedicated API keys for agent identities.
- **Evidence**: `packages/server/src/utils/validateKey.ts`, `packages/server/src/database/entities/ApiKey.ts`

### AUTH-Q2: Scoped Permissions
- **Severity**: INFO (control present)
- **Finding**: Fine-grained RBAC with 15 permission categories. API keys carry scoped permissions.
- **Implication**: Agent identities can be granted read-only access to specific resources.
- **Recommendation**: Create a minimal agent role with view-only permissions.
- **Evidence**: `packages/server/src/enterprise/rbac/Permissions.ts`

### AUTH-Q3: Action-Level Authorization
- **Severity**: INFO (control present)
- **Finding**: `checkPermission` middleware on every route. Separate view/create/update/delete per resource.
- **Implication**: Agents can be restricted to reads only.
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: `packages/server/src/enterprise/rbac/PermissionCheck.ts`

### AUTH-Q7: Agent Identity Suspension
- **Severity**: INFO (control present)
- **Finding**: API key deletion via `DELETE /api/v1/apikey/:id`. Immediate revocation.
- **Implication**: Agent identities can be suspended immediately.
- **Recommendation**: Add `disabled` boolean for reversible suspension.
- **Evidence**: `packages/server/src/routes/apikey/index.ts`, `packages/server/src/services/apikey/index.ts`

### STATE-Q5: Rate Limiting and Throttling
- **Severity**: INFO (control present)
- **Finding**: `express-rate-limit` with per-chatflow config. Redis-backed. `standardHeaders: true` in queue mode.
- **Implication**: Agent traffic throttled. Rate limit headers available for self-throttling.
- **Recommendation**: Enable standardHeaders in all modes.
- **Evidence**: `packages/server/src/utils/rateLimit.ts`

### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO (read-only scope)
- **Finding**: No idempotency keys on write endpoints.
- **Implication**: Informational. Becomes BLOCKER if write access is planned.
- **Evidence**: `packages/server/src/` (absence)

### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: All responses JSON. No XML or binary.
- **Implication**: Optimal for LLM agents.
- **Evidence**: `packages/server/src/middlewares/errors/index.ts`

### API-Q6: Asynchronous Operation Support
- **Severity**: INFO (control present)
- **Finding**: BullMQ queues + SSE streaming for long-running predictions.
- **Implication**: Agents can consume streaming or poll for results.
- **Evidence**: `packages/server/src/queue/QueueManager.ts`, `packages/server/src/utils/SSEStreamer.ts`

### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: Redis pub/sub + SSE during sessions. No external webhooks/SNS.
- **Implication**: Event-driven agents need polling.
- **Evidence**: `packages/server/src/utils/SSEStreamer.ts`

### API-Q8: Rate Limit Documentation
- **Severity**: INFO
- **Finding**: `standardHeaders: true` in queue mode. Not documented in OpenAPI spec.
- **Implication**: Agents detect limits via headers but documentation gap exists.
- **Evidence**: `packages/server/src/utils/rateLimit.ts`

### STATE-Q2: Queryable Current State
- **Severity**: INFO (control present)
- **Finding**: All entities expose GET endpoints.
- **Implication**: Agents can inspect state before acting.
- **Evidence**: `packages/server/src/routes/index.ts`

### STATE-Q3: Concurrency Controls ⚡ (INFO, read-only)
- **Severity**: INFO
- **Finding**: No optimistic locking or version columns.
- **Implication**: Informational for read-only scope.
- **Evidence**: `packages/server/src/database/entities/`

### STATE-Q6: Transaction Limits ⚡ (INFO, read-only)
- **Severity**: INFO
- **Finding**: No configurable transaction limits.
- **Implication**: Informational for read-only scope.
- **Evidence**: `packages/server/src/utils/rateLimit.ts`

### HITL-Q1: Draft/Pending State ⚡ (INFO, read-only)
- **Severity**: INFO
- **Finding**: ChatFlow `deployed` field. `humanInputAgentflow` node for HITL.
- **Implication**: Native HITL capability exists.
- **Evidence**: `packages/server/src/database/entities/ChatFlow.ts`

### HITL-Q2: Approval Gates ⚡ (INFO, read-only)
- **Severity**: INFO
- **Finding**: `humanInputAgentflow` provides configurable approval gates.
- **Implication**: Strong foundation for human oversight.
- **Evidence**: `packages/server/src/services/predictions/`

### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics or monitoring.
- **Implication**: No quality signal for agents.
- **Evidence**: No evidence — absence is the finding.

### DISC-Q2: Semantic Field Names
- **Severity**: INFO
- **Finding**: Semantic camelCase names. No legacy abbreviations.
- **Implication**: LLMs can interpret without data dictionary.
- **Evidence**: `packages/server/src/database/entities/`

### DISC-Q3: Data Catalog
- **Severity**: INFO
- **Finding**: No data catalog. TypeORM entities as implicit docs.
- **Implication**: Manual discovery required.
- **Evidence**: `packages/server/src/database/entities/`

### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: chatflow_created, prediction counters via Prometheus/OpenTelemetry.
- **Implication**: Agent predictions captured with internal/external distinction.
- **Evidence**: `packages/server/src/Interface.Metrics.ts`

### STATE-Q7: Infrastructure Capacity (Not Evaluated)
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered. Priority P2 (not P0/critical path).
- **Trigger**: Service is P0 priority OR on the critical path.

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: Comprehensive REST API via Express.js with 50+ route groups under `/api/v1/`. OpenAPI 3.0.3 specification exists in `packages/api-documentation/src/yml/swagger.yml`. All integration is API-based — no direct database access, file-based exchange, or UI automation is required.
- **Gap**: No gap — documented REST API exists as the integration surface.
- **Recommendation**: Expand OpenAPI spec coverage to match the full route surface.
- **Evidence**: `packages/server/src/routes/index.ts`, `packages/api-documentation/src/yml/swagger.yml`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: OpenAPI 3.0.3 spec exists (2,665 lines, ~14 tag groups) but covers ~28% of the 50+ actual route groups. The spec is manually maintained and not auto-generated from code annotations.
- **Gap**: Spec covers less than a third of the API surface. Manual maintenance creates drift risk.
- **Recommendation**: Migrate to annotation-based spec generation (e.g., `tsoa` or `swagger-jsdoc`) to ensure spec stays current with implementation.
- **Evidence**: `packages/api-documentation/src/yml/swagger.yml`, `packages/server/src/routes/index.ts`

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: Error handler returns `{statusCode, success, message}` JSON structure. Consistent across endpoints via centralized error middleware.
- **Gap**: No `errorCode` enumeration or `retryable` field. Agents cannot programmatically distinguish retriable from terminal errors.
- **Recommendation**: Add `errorCode` and `retryable` fields to the error response structure.
- **Evidence**: `packages/server/src/middlewares/errors/index.ts`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No idempotency keys on write endpoints. POST endpoints for entity creation do not support idempotency headers or business-key deduplication.
- **Gap**: Write endpoints are not idempotent. Informational for read-only scope — becomes BLOCKER if write access is planned.
- **Recommendation**: When planning write-enabled agent access, implement idempotency key support on POST endpoints.
- **Evidence**: `packages/server/src/` (absence of idempotency patterns)

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: All API responses are JSON. No XML, binary, or Protobuf formats. Content-Type consistently `application/json`.
- **Gap**: No gap — JSON is optimal for LLM-based agent consumption.
- **Recommendation**: No action needed. JSON format is ideal for agent tool integration.
- **Evidence**: `packages/server/src/middlewares/errors/index.ts`

#### API-Q6: Asynchronous Operation Support
- **Severity**: INFO
- **Finding**: BullMQ queues for background prediction processing. SSE (Server-Sent Events) streaming for long-running LLM predictions. `QueueManager` handles job submission and status tracking.
- **Gap**: No gap — async patterns exist for long-running operations.
- **Recommendation**: Expose a polling endpoint for job status as an alternative to SSE for agent consumers that prefer request/response patterns.
- **Evidence**: `packages/server/src/queue/QueueManager.ts`, `packages/server/src/utils/SSEStreamer.ts`

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: Redis pub/sub for real-time events during chat sessions. SSE streaming for active connections. No external webhook endpoints, SNS topics, or EventBridge integration for state change notifications.
- **Gap**: Event emission is session-scoped. No persistent event stream for external consumers.
- **Recommendation**: Consider adding webhook or EventBridge integration for key state changes (chatflow deployment, prediction completion) if event-driven agent patterns are planned.
- **Evidence**: `packages/server/src/utils/SSEStreamer.ts`, `packages/server/src/queue/RedisEventSubscriber.ts`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: `express-rate-limit` with `standardHeaders: true` in queue mode returns `RateLimit-*` headers. Rate limits are not documented in the OpenAPI spec.
- **Gap**: Rate limit headers available in queue mode only. No documentation in API spec.
- **Recommendation**: Enable `standardHeaders` in all rate-limit modes. Document rate limits in the OpenAPI specification.
- **Evidence**: `packages/server/src/utils/rateLimit.ts`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: API key authentication with workspace scoping and principal attribution via `ApiKey` entity. JWT-based auth via Passport.js for UI users. API keys carry `keyName` for identity attribution and are scoped to workspaces.
- **Gap**: No gap — machine identity authentication is supported via API keys with principal attribution.
- **Recommendation**: Create dedicated API keys with descriptive `keyName` values for agent identities (e.g., "agent-readonly-chatflow-reader").
- **Evidence**: `packages/server/src/utils/validateKey.ts`, `packages/server/src/database/entities/ApiKey.ts`, `packages/server/src/index.ts`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: INFO
- **Finding**: Fine-grained RBAC with 15 permission categories (chatflows, tools, assistants, credentials, variables, etc.). Each category supports separate view/create/update/delete permissions. API keys inherit permissions from the associated role.
- **Gap**: No gap — scoped permissions exist at the action and resource level.
- **Recommendation**: Create a minimal agent role with view-only permissions for the specific resource types the agent needs.
- **Evidence**: `packages/server/src/enterprise/rbac/Permissions.ts`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: INFO
- **Finding**: `checkPermission` middleware enforced on every route. Separate `view`, `create`, `update`, `delete` permissions per resource type. An agent can be granted read access without write permissions.
- **Gap**: No gap — action-level authorization is enforced per route.
- **Recommendation**: No action needed for read-only scope. Verify permission checks cover all 50+ route groups.
- **Evidence**: `packages/server/src/enterprise/rbac/PermissionCheck.ts`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: RISK-QUALITY
- **Finding**: JWT-based identity via Passport.js. API key validation identifies the key but does not distinguish between agent-as-self vs agent-on-behalf-of-user. No OAuth2 on-behalf-of flows or token exchange patterns.
- **Gap**: No identity delegation capability. Cannot distinguish agent acting autonomously from agent acting on behalf of a specific user.
- **Recommendation**: Add `identity_type` field (machine/human) and optional `on_behalf_of` field to the API key entity to support delegation tracking.
- **Evidence**: `packages/server/src/utils/validateKey.ts`, `packages/server/src/database/entities/ApiKey.ts`, `packages/server/src/IdentityManager.ts`

#### AUTH-Q5: Credential Management
- **Severity**: RISK-QUALITY
- **Finding**: Supports AWS Secrets Manager (`SECRETKEY_STORAGE_TYPE=aws`) but defaults to local filesystem storage. Application-level encryption via `crypto-js` for credential storage. No secret rotation mechanism.
- **Gap**: Default deployment uses local filesystem secrets with no rotation capability.
- **Recommendation**: Make AWS Secrets Manager the recommended default in documentation and deployment templates. Implement credential rotation support.
- **Evidence**: `packages/server/src/enterprise/utils/authSecrets.ts`, `packages/server/.env.example`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Enterprise audit system is limited to login activity tracking only (`fetchLoginActivity`). No general-purpose audit logging for API operations. No CloudTrail, no immutable log storage. Application logs via Winston record HTTP requests but are mutable and not tamper-evident.
- **Gap**: No immutable, tamper-evident audit trail for API operations. Cannot prove which agent performed which operation.
- **Recommendation**: Implement audit logging middleware recording the authenticated principal for every API operation, with logs shipped to immutable storage (S3 with Object Lock or CloudWatch with retention policy).
- **Evidence**: `packages/server/src/enterprise/routes/audit/index.ts`, `packages/server/src/utils/logger.ts`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: INFO
- **Finding**: API key deletion via `DELETE /api/v1/apikey/:id` provides immediate revocation. Key validation occurs on every request, so deleted keys are rejected immediately.
- **Gap**: No gap — agent identities can be suspended immediately via key deletion.
- **Recommendation**: Add a `disabled` boolean field for reversible suspension without permanent deletion.
- **Evidence**: `packages/server/src/routes/apikey/index.ts`, `packages/server/src/services/apikey/index.ts`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No saga patterns, compensation logic, or rollback handlers found in the codebase. TypeORM migration revert is a schema migration tool, not runtime compensation. Service methods perform sequential operations without transaction wrappers.
- **Gap**: No compensation or rollback for multi-step operations. A failed multi-step write operation would leave partial state.
- **Recommendation**: Wrap multi-step write operations in TypeORM transactions. Implement compensation patterns for critical workflows.
- **Evidence**: `packages/server/src/services/` (absence of compensation patterns)

#### STATE-Q2: Queryable Current State
- **Severity**: INFO
- **Finding**: All 19+ entity types expose GET endpoints for retrieving current state. Agents can inspect resource state before taking action. Standard CRUD read patterns throughout.
- **Gap**: No gap — all entities are queryable via REST GET endpoints.
- **Recommendation**: No action needed. Ensure new entities continue to expose GET endpoints.
- **Evidence**: `packages/server/src/routes/index.ts`

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No optimistic locking, version columns, or ETag support on entities. TypeORM entities do not use `@VersionColumn()`. No `If-Match` header handling.
- **Gap**: No concurrency controls for write operations. Informational for read-only scope.
- **Recommendation**: When planning write-enabled agent access, add `@VersionColumn()` to critical entities and implement ETag-based concurrency control.
- **Evidence**: `packages/server/src/database/entities/`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: No circuit breakers, retry logic with backoff, or timeout configurations on external dependency calls (LLM provider calls, vector store connections). `AbortControllerPool` provides request cancellation but not circuit-breaking or automatic recovery.
- **Gap**: No circuit breakers to prevent cascading failures when LLM providers or external dependencies are unavailable.
- **Recommendation**: Add circuit breaker middleware (e.g., `opossum`) around LLM provider calls and external API calls. Configure HTTP client timeouts.
- **Evidence**: `packages/server/src/AbortControllerPool.ts`, `packages/components/package.json`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: INFO
- **Finding**: `express-rate-limit` with per-chatflow configuration. Redis-backed rate store for distributed deployments. `standardHeaders: true` in queue mode provides rate limit response headers.
- **Gap**: No gap — rate limiting is enforced at the API layer.
- **Recommendation**: Enable `standardHeaders` in all rate-limit modes (not just queue mode) so agents always receive rate limit headers.
- **Evidence**: `packages/server/src/utils/rateLimit.ts`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits per agent identity. Rate limiting exists (STATE-Q5) but no separate business-level limits (e.g., max records per query, max operations per session).
- **Gap**: No transaction-level limits. Informational for read-only scope.
- **Recommendation**: When planning write-enabled agent access, implement configurable per-identity transaction limits.
- **Evidence**: `packages/server/src/utils/rateLimit.ts`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path. This service is P2.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: ChatFlow entity has a `deployed` boolean field supporting draft/deployed state transitions. The `humanInputAgentflow` node provides native HITL capability for agent workflows within Flowise.
- **Gap**: No gap for read-only scope. Draft state capability exists natively.
- **Recommendation**: Leverage the existing `deployed` field and HITL nodes when planning write-enabled agent workflows.
- **Evidence**: `packages/server/src/database/entities/ChatFlow.ts`

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: `humanInputAgentflow` node provides configurable human approval gates within agent flows. Users can insert approval steps at any point in a flow.
- **Gap**: No gap for read-only scope. Approval gate capability exists natively.
- **Recommendation**: Document the HITL node patterns as the approval gate mechanism for future write-enabled agent operations.
- **Evidence**: `packages/server/src/services/predictions/`

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: Docker-compose configuration for local development with optional PostgreSQL. No dedicated staging environment configuration, no seed data scripts, no synthetic data generators.
- **Gap**: No production-equivalent staging environment for safe agent testing.
- **Recommendation**: Define a staging environment configuration with seed data. Use Docker-compose with PostgreSQL as the base for an agent testing environment.
- **Evidence**: `docker/docker-compose.yml`, `.github/workflows/main.yml`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: The Flowise database contains PII and sensitive data without field-level classification or tagging. The `Lead` entity (`packages/server/src/database/entities/Lead.ts`) stores `name`, `email`, and `phone` fields with no classification markers, no field-level encryption, and no access controls distinguishing PII from non-sensitive data. The `Credential` entity stores an `encryptedData` field (application-level encryption via `crypto-js`), but this is not a classification system. The `ChatMessage` entity stores `content` (user conversations) and `leadEmail` fields which may contain PII. No Amazon Macie integration, no data classification tags, and no field-level access control policies were found.
- **Gap**: No sensitive data is classified or tagged at the field level. An agent granted read access would receive PII without any system-level control preventing it.
- **Recommendation**: Create a data classification inventory mapping each entity field to a sensitivity level (PUBLIC, INTERNAL, CONFIDENTIAL, PII). Implement field-level access controls enforced at the API layer.
- **Evidence**: `packages/server/src/database/entities/Lead.ts`, `packages/server/src/database/entities/ChatMessage.ts`, `packages/server/src/database/entities/Credential.ts`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Multi-region storage backends supported (S3, GCS, Azure Blob) with no residency enforcement. Database can be SQLite (local), PostgreSQL, MySQL, or MariaDB with no region constraints. No GDPR/LGPD compliance controls or data residency configuration.
- **Gap**: No data residency controls. Data can be stored and accessed across jurisdictions without enforcement.
- **Recommendation**: Add data residency configuration enforcing storage region constraints. Document which data classes are subject to residency requirements.
- **Evidence**: `packages/server/.env.example`, `docker/docker-compose.yml`, `docker/.env.example`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK-QUALITY
- **Finding**: Some endpoints support pagination via `page` and `limit` parameters. Inconsistent across routes — not all list endpoints enforce pagination. No cursor-based pagination. No default result size limits on some endpoints.
- **Gap**: Unbounded result sets possible on some endpoints. Inconsistent pagination support.
- **Recommendation**: Standardize pagination with default limits across all list endpoints. Implement cursor-based pagination for large collections.
- **Evidence**: `packages/api-documentation/src/yml/swagger.yml`, `packages/server/src/services/apikey/index.ts`

#### DATA-Q4: System of Record Designations
- **Severity**: RISK-QUALITY
- **Finding**: No system-of-record designations or data ownership documentation found. Flowise implicitly owns its domain entities (chatflows, credentials, tools, variables) but this is not formally documented.
- **Gap**: No formal system-of-record designations. Agents querying multiple systems cannot determine authoritative data sources.
- **Recommendation**: Create a data ownership matrix documenting Flowise as the SoR for its domain entities.
- **Evidence**: `packages/server/src/database/entities/`

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK-QUALITY
- **Finding**: TypeORM entities have `createdDate` and `updatedDate` columns (via `@CreateDateColumn()` and `@UpdateDateColumn()`). No UTC enforcement in column definitions. No `Cache-Control`, `Last-Modified`, or freshness signaling headers in API responses.
- **Gap**: Timestamps exist at the database level but no freshness signaling in API responses. No UTC enforcement.
- **Recommendation**: Add `Last-Modified` headers to GET responses. Enforce UTC storage for all timestamp columns. Add `X-Data-Consistency: strong` header since Flowise reads directly from the database.
- **Evidence**: `packages/server/src/database/entities/ChatFlow.ts`, `packages/server/src/database/entities/Variable.ts`

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: Log sanitization exists via `LOG_SANITIZE_BODY_FIELDS` and `LOG_SANITIZE_HEADER_FIELDS` environment variables but is opt-in. Default deployments have no PII redaction active. The `.env.example` documents recommended fields to sanitize but they must be explicitly configured.
- **Gap**: PII sanitization in logs is opt-in, not default-on. Default deployments log PII in request/response bodies.
- **Recommendation**: Make sanitization fields default-on in code rather than requiring explicit environment variable configuration. Add regex-based PII detection as a fallback.
- **Evidence**: `packages/server/src/utils/logger.ts`, `packages/server/.env.example`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics, completeness scores, data profiling reports, or freshness SLAs found in the codebase.
- **Implication**: Agents have no quality signal for the data they consume. Data quality issues are not surfaced programmatically.
- **Recommendation**: Consider adding data quality metrics for critical entities (e.g., chatflow completeness, credential validity checks).
- **Evidence**: No evidence found — absence is the finding.

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: URL-based versioning (`/api/v1/`). TypeORM migrations for schema evolution. OpenAPI spec exists but no breaking change detection in CI. No consumer-driven contract tests (Pact).
- **Gap**: No automated breaking change detection in CI pipeline. Schema changes could break agent tool bindings silently.
- **Recommendation**: Add OpenAPI diff check to CI pipeline (e.g., `openapi-diff` or `oasdiff`). Consider adding Pact contract tests for agent-consumed endpoints.
- **Evidence**: `packages/server/src/index.ts`, `.github/workflows/main.yml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Semantic camelCase field names throughout (e.g., `chatflowId`, `createdDate`, `updatedDate`, `encryptedData`, `leadEmail`). No legacy abbreviations or opaque codes.
- **Implication**: LLMs can interpret field names without requiring a data dictionary. Agent tool generation is straightforward.
- **Recommendation**: No action needed. Maintain current naming conventions.
- **Evidence**: `packages/server/src/database/entities/`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal data catalog (no Glue, Collibra, DataHub). TypeORM entity definitions serve as implicit schema documentation. No standalone data dictionary.
- **Implication**: Agent tool builders must inspect TypeORM entities or the partial OpenAPI spec to understand data structures. Manual discovery process.
- **Recommendation**: Consider auto-generating a data dictionary from TypeORM entity metadata.
- **Evidence**: `packages/server/src/database/entities/`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: OpenTelemetry metrics SDK configured (`@opentelemetry/sdk-metrics`). Winston logger outputs JSON-structured logs. However, trace exporter dependencies are present but the tracer provider is not actively configured. No correlation IDs (request_id or trace_id) in log entries.
- **Gap**: Trace propagation not active despite dependencies being present. Logs lack correlation IDs for request-level debugging.
- **Recommendation**: Enable the OpenTelemetry tracer provider. Add request ID middleware injecting correlation IDs into all log entries.
- **Evidence**: `packages/server/src/metrics/OpenTelemetry.ts`, `packages/server/src/utils/logger.ts`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: Prometheus and OpenTelemetry metrics are collected (HTTP request duration, error counts) but no alerting rules, CloudWatch alarms, or Alertmanager configuration found in the codebase.
- **Gap**: Metrics collected but no alerting configured. Degradation of agent-consumed APIs would go undetected.
- **Recommendation**: Define Prometheus Alertmanager rules or CloudWatch alarms for HTTP error rate thresholds and latency P99 on agent-consumed endpoints.
- **Evidence**: `packages/server/src/metrics/Prometheus.ts`, `packages/server/src/metrics/OpenTelemetry.ts`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: Custom metrics published via Prometheus and OpenTelemetry: `chatflow_created`, prediction counters with `internal`/`external` labels distinguishing API-initiated predictions from UI-initiated ones.
- **Implication**: Agent-initiated predictions are already distinguishable via the `external` label. Business outcome tracking exists at a basic level.
- **Recommendation**: Expand business metrics to cover resolution rates, flow execution success/failure, and agent-specific outcome tracking.
- **Evidence**: `packages/server/src/Interface.Metrics.ts`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK-QUALITY
- **Finding**: No IaC files (no Terraform, CloudFormation, or CDK). Deployment defined via Dockerfiles and docker-compose only. No drift detection. No peer review requirement specific to infrastructure changes.
- **Gap**: Agent-facing infrastructure surface is not defined as code. No IaC governance, no change review process for infrastructure, no drift detection.
- **Recommendation**: Create IaC definitions (Terraform or CDK) for the deployment infrastructure including API Gateway, IAM roles, and networking. Implement drift detection via AWS Config.
- **Evidence**: `Dockerfile`, `docker/Dockerfile`, `docker/docker-compose.yml`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: GitHub Actions CI pipeline exists with build, lint, and basic test steps. No API contract testing, no OpenAPI spec validation, no breaking change detection in the pipeline.
- **Gap**: No API contract tests in CI. Breaking API changes would not be caught before production.
- **Recommendation**: Add OpenAPI validation step to CI. Implement consumer-driven contract tests for agent-consumed endpoints.
- **Evidence**: `.github/workflows/main.yml`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: Docker image tags for version pinning. Docker Hub and ECR publishing workflows. No automated rollback triggers, no blue/green deployment, no canary deployments. Rollback is manual (redeploy previous tag).
- **Gap**: No automated rollback capability. Recovery from a broken deployment requires manual intervention.
- **Recommendation**: Implement health-check-based automatic rollback. Use versioned image tags (not `latest`) in deployment configurations.
- **Evidence**: `.github/workflows/docker-image-dockerhub.yml`, `.github/workflows/docker-image-ecr.yml`, `docker/docker-compose.yml`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: Jest and Cypress configured. Only ~8 test files across server and components packages. No API integration tests (no supertest, no Postman/Newman collections). Test coverage for 50+ route groups is minimal.
- **Gap**: Minimal test coverage for agent-consumed API endpoints. Behavioral changes would go undetected.
- **Recommendation**: Create API integration tests using supertest targeting agent-consumed endpoints. Prioritize prediction and chatflow endpoints.
- **Evidence**: `packages/server/jest.config.js`, `packages/server/cypress.config.ts`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: RISK-QUALITY
- **Finding**: Application-level encryption for credential data via `crypto-js`. No database-level encryption configuration in the codebase. No KMS integration. S3 storage configuration has no enforced encryption settings.
- **Gap**: Encryption at rest depends entirely on deployment infrastructure configuration. No enforcement in code or IaC.
- **Recommendation**: Document encryption-at-rest requirements for deployment. Add S3 encryption configuration option (`SSE-KMS` or `SSE-S3`). Recommend RDS encryption for database deployments.
- **Evidence**: `packages/server/src/database/entities/Credential.ts`, `packages/server/src/DataSource.ts`

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `packages/server/src/routes/index.ts` | API-Q1, API-Q2, STATE-Q2, DISC-Q1 |
| `packages/server/src/middlewares/errors/index.ts` | API-Q3, API-Q5 |
| `packages/server/src/utils/rateLimit.ts` | API-Q8, STATE-Q5, STATE-Q6 |
| `packages/server/src/utils/SSEStreamer.ts` | API-Q5, API-Q6, API-Q7 |
| `packages/server/src/utils/validateKey.ts` | AUTH-Q1, AUTH-Q4 |
| `packages/server/src/utils/logger.ts` | AUTH-Q6, DATA-Q6, OBS-Q1 |
| `packages/server/src/queue/QueueManager.ts` | API-Q6 |
| `packages/server/src/queue/RedisEventSubscriber.ts` | API-Q7 |
| `packages/server/src/IdentityManager.ts` | AUTH-Q4 |
| `packages/server/src/enterprise/rbac/Permissions.ts` | AUTH-Q2 |
| `packages/server/src/enterprise/rbac/PermissionCheck.ts` | AUTH-Q3 |
| `packages/server/src/enterprise/utils/authSecrets.ts` | AUTH-Q5 |
| `packages/server/src/enterprise/routes/audit/index.ts` | AUTH-Q6 |
| `packages/server/src/services/apikey/index.ts` | AUTH-Q2, AUTH-Q7, DATA-Q3 |
| `packages/server/src/routes/apikey/index.ts` | AUTH-Q3, AUTH-Q7 |
| `packages/server/src/database/entities/ApiKey.ts` | AUTH-Q1, AUTH-Q4 |
| `packages/server/src/database/entities/ChatFlow.ts` | HITL-Q1, DATA-Q5 |
| `packages/server/src/database/entities/Lead.ts` | DATA-Q1 |
| `packages/server/src/database/entities/ChatMessage.ts` | DATA-Q1 |
| `packages/server/src/database/entities/Credential.ts` | DATA-Q1, ENG-Q5 |
| `packages/server/src/database/entities/Variable.ts` | DATA-Q5 |
| `packages/server/src/DataSource.ts` | ENG-Q5 |
| `packages/server/src/AbortControllerPool.ts` | STATE-Q4 |
| `packages/server/src/index.ts` | AUTH-Q1, DISC-Q1 |
| `packages/server/src/metrics/OpenTelemetry.ts` | OBS-Q1, OBS-Q2 |
| `packages/server/src/metrics/Prometheus.ts` | OBS-Q1, OBS-Q2 |
| `packages/server/src/Interface.Metrics.ts` | OBS-Q3 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `packages/api-documentation/src/yml/swagger.yml` | API-Q1, API-Q2, API-Q8, DATA-Q3, DISC-Q1 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/main.yml` | ENG-Q2, DISC-Q1, HITL-Q3 |
| `.github/workflows/docker-image-dockerhub.yml` | ENG-Q2, ENG-Q3 |
| `.github/workflows/docker-image-ecr.yml` | ENG-Q3 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `Dockerfile` | ENG-Q1 |
| `docker/Dockerfile` | ENG-Q1 |
| `docker/docker-compose.yml` | DATA-Q2, HITL-Q3, ENG-Q1, ENG-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `packages/server/package.json` | AUTH-Q5, STATE-Q4, OBS-Q1 |
| `packages/components/package.json` | STATE-Q4 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `packages/server/.env.example` | AUTH-Q5, DATA-Q2, DATA-Q6, ENG-Q5 |
| `docker/.env.example` | DATA-Q2 |
| `packages/server/jest.config.js` | ENG-Q4 |
| `packages/server/cypress.config.ts` | ENG-Q4 |

