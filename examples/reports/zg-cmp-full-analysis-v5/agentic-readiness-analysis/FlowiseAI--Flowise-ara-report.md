# Agentic Readiness Analysis Report

**Target**: Flowise (monorepo — packages/server primary analysis target)
**Date**: 2026-04-30
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**TD Version**: 3g1ipe93e5d2wb6n5d4yqaf9
**Repository Type**: monorepo
**Service Archetype**: stateful-crud (auto-detected — primary service: packages/server)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: typescript, ai, llm
**Context**: Low-code UI for building LLM flows and agents.

**Archetype Justification**: The primary service (packages/server) is an Express.js backend with TypeORM database connections (SQLite/MySQL/MariaDB/PostgreSQL), full CRUD endpoints for 19+ entity types (ChatFlow, ChatMessage, Credential, Tool, Variable, Assistant, DocumentStore, Lead, etc.), user-specific data (workspaceId on all entities), and entity lifecycle management. This matches the stateful-crud archetype.

**Monorepo Analysis Strategy**: The monorepo contains 5 packages. The primary agent-callable service is `packages/server` (Flowise backend). `packages/ui` and `packages/agentflow` are frontend packages. `packages/components` is a shared library consumed by the server. `packages/api-documentation` serves Swagger UI docs. All 43 questions are evaluated against the server package.

- **Surface flags** (packages/server):
  - has_persistent_data_store: true
  - has_http_rpc_surface: true
  - has_auth_surface: true
  - has_write_operations: true
  - has_logging_of_user_data: true

**Severity Convention Note**: Questions with a base severity of BLOCKER or RISK in the TD are recorded at their base severity only when a gap is identified. When evaluation finds the control is fully satisfied (no gap), the question is recorded as INFO to indicate the control exists and no remediation is needed. This convention applies to API-Q1, AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q5, AUTH-Q7, and similar questions where the assessed system meets the requirement.

---

## Readiness Profile: Pilot-Ready (Safety Concerns)

**BLOCKERs**: 0 | **RISK-SAFETY**: 5 | **RISK-QUALITY**: 13 | **INFOs**: 22

With DATA-Q1 reclassified from BLOCKER to RISK-SAFETY under the new tiered model (see RISK-SAFETY section), Flowise has no remaining BLOCKERs. Proceed with a supervised pilot with elevated safety oversight; prioritize RISK-SAFETY remediation — especially the credential plaintext path in `GET /api/v1/credentials/:id` — before expanding agent scope.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 1 |
| RISK-SAFETY | 4 |
| RISK-QUALITY | 13 |
| INFO | 21 |
| N/A | 0 |
| Not Evaluated (extended) | 4 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 15
**Extended Questions Not Triggered**: 4
**Questions N/A (repo_type: monorepo)**: 0
**Service Archetype**: stateful-crud (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

_None. DATA-Q1 was previously BLOCKER under the binary "formal classification absent" rule; under the tiered model it resolves to RISK-SAFETY (see RISK-SAFETY section) because Flowise encrypts credentials at rest with AES-256 + ENCRYPTION_KEY (file-based or AWS Secrets Manager), strips `encryptedData` from list endpoints via `omit()`, and enforces workspace-scoped RBAC with per-permission subset filtering on API keys — but the GET-by-ID credential endpoint decrypts to plaintext and the `apiKey` field is stored/returned plaintext._

---

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### DATA-Q1: Sensitive Data Classification ⚡ (Tiered) — Demoted from BLOCKER

- **Severity**: RISK-SAFETY
- **Stage A**: Yes — Lead PII (name/email/phone), Credential entity (encrypted API keys/secrets), ChatMessage content, ApiKey entity (plaintext `apiKey` column + hashed `apiSecret`).
- **B1 — Agent-facing API response scoping: MIXED.**
  - **Credential list (`GET /api/v1/credentials`)**: CLEAR. `getAllCredentials` strips `encryptedData` via `omit(c, ['encryptedData'])` (`packages/server/src/services/credentials/index.ts:63,71,102`).
  - **Credential by ID (`GET /api/v1/credentials/:id`)**: RISK. `getCredentialById` calls `decryptCredentialData()` and returns `plainDataObj` containing the decrypted credential in plaintext (`packages/server/src/services/credentials/index.ts:138-147`). Intentional for UI use; a read-only agent scoped to this endpoint can extract decrypted LLM provider API keys and integration credentials one at a time.
  - **API keys (`GET /api/v1/apikey`)**: RISK. List endpoint returns the full `ApiKey` object including the plaintext `apiKey` column (`packages/server/src/services/apikey/index.ts:109-131`); `apiSecret` is hashed.
- **B2 — Access control differentiation: CLEAR.** Workspace-scoped queries (`api_key.workspaceId = :workspaceId`). Role-based filtering — non-admin users only see API keys whose permissions are a subset of their own (`packages/server/src/services/apikey/index.ts:118-124`). `validatePermissions` prevents API keys from carrying `workspace:*` or `admin:*` scopes.
- **B3 — Formal classification metadata: INFO.** AES-256 encryption via `ENCRYPTION_KEY` (file-based or AWS Secrets Manager — `packages/server/src/utils/index.ts:1550-1598`) is classification-by-encryption; no formal decorators. Filesystem storage of the encryption key is acceptable for self-hosted but weaker than HSM/KMS.
- **Overall (read-only scope)**: B1 fires as RISK-SAFETY (plaintext credentials returned on GET-by-ID; plaintext API keys in list). Because the agent is read-only, the damage is bounded to exfiltration (no escalation). → **DATA-Q1 = RISK-SAFETY**, not BLOCKER.
- **Compensating Controls**:
  - Restrict agent to endpoints that never call `getCredentialById` (list-only access)
  - Rotate LLM provider keys regularly and monitor for anomalous usage
  - Enforce per-workspace scoping in the agent's session
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Default `getCredentialById` to returning the encrypted blob; require an explicit `reveal=true` parameter + additional auth to decrypt. Mask `apiKey` in list responses (return truncated prefix). Consider migrating `apiKey` to hashed storage with a derived display key.
- **Evidence**: `packages/server/src/services/credentials/index.ts:63,71,102,138-147`, `packages/server/src/services/apikey/index.ts:109-131`, `packages/server/src/database/entities/Credential.ts`, `packages/server/src/database/entities/ApiKey.ts:7-8`, `packages/server/src/utils/index.ts:1550-1598`.

#### AUTH-Q6: Immutable Audit Logging — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The server has an enterprise audit route (`/audit`) gated behind `feat:login-activity`. Request logging exists via Winston (`packages/server/src/utils/logger.ts`) with structured JSON format and timestamps. However, there is no immutable or tamper-evident log storage configuration. No CloudTrail, no S3 object lock, no log file validation. The request logger records HTTP method, URL, and params but does not log the authenticated principal (API key name, workspaceId, or user identity) for every request. Logs are written to local filesystem or cloud storage transports without immutability guarantees.
- **Gap**: No immutable audit trail. Authenticated principal not consistently logged with each request. Log storage is mutable (filesystem, standard cloud storage without object lock).
- **Compensating Controls**:
  - Route all agent traffic through an API Gateway or reverse proxy that provides immutable access logging with principal attribution
  - Enable cloud provider audit logging (AWS CloudTrail, GCP Audit Logs) for the infrastructure layer
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add the authenticated principal (API key keyName, workspaceId, or JWT user identity) to every request log entry. Configure immutable log storage (S3 with object lock, or CloudWatch with retention policy).
- **Evidence**: `packages/server/src/utils/logger.ts`, `packages/server/src/routes/index.ts` (audit route), `packages/server/.env.example` (LOG_PATH config)

#### STATE-Q1: Compensation and Rollback — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The server uses TypeORM with database migrations (`packages/server/src/DataSource.ts`) that run with `transaction: 'each'`. However, there are no saga patterns, compensating transactions, or explicit undo endpoints for multi-step operations. The prediction flow (which orchestrates LLM calls, vector store operations, and tool executions) does not have rollback logic for partial failures. The AbortControllerPool (`packages/server/src/AbortControllerPool.ts`) can abort in-flight operations but does not compensate for completed steps.
- **Gap**: No compensation or rollback mechanism for multi-step workflows (predictions, document store upserts). Partial failures leave the system in an inconsistent state.
- **Compensating Controls**:
  - For read-only agent scope, this is mitigated by limiting agent access to GET endpoints only
  - Implement idempotent retry logic at the agent orchestration layer
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement compensation logic for the prediction pipeline (e.g., if vector upsert succeeds but LLM call fails, clean up the upserted vectors). Add explicit undo endpoints for reversible operations.
- **Evidence**: `packages/server/src/DataSource.ts`, `packages/server/src/AbortControllerPool.ts`, `packages/server/src/queue/QueueManager.ts`

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The server makes extensive external API calls via `packages/components` — to LLM providers (OpenAI, Anthropic, Google, AWS Bedrock, Ollama), vector stores (Pinecone, Qdrant, Weaviate, Chroma, Milvus, Elasticsearch), and external tools. However, there are no circuit breaker patterns (no Resilience4j, no Polly, no `opossum`). The `AbortControllerPool` provides request cancellation, and BullMQ provides job queue resilience with retry support, but there is no circuit breaker to prevent cascading failures when external dependencies are degraded.
- **Gap**: No circuit breaker implementation for external dependency calls. A degraded LLM provider or vector store could cascade failures to all prediction requests.
- **Compensating Controls**:
  - Configure shorter timeouts on HTTP clients calling external APIs
  - Use BullMQ retry policies with exponential backoff as a partial circuit breaker substitute
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a circuit breaker library (e.g., `opossum` for Node.js) around external API calls in the components package. Configure per-provider circuit breaker thresholds.
- **Evidence**: `packages/components/package.json` (extensive external SDK dependencies, no circuit breaker library), `packages/server/src/AbortControllerPool.ts`, `packages/server/src/queue/QueueManager.ts`

#### DATA-Q2: Data Residency and Sovereignty — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The server supports configurable storage regions (S3_STORAGE_REGION, DATABASE_HOST, GOOGLE_CLOUD_STORAGE_PROJ_ID, AZURE_BLOB_STORAGE_ACCOUNT_NAME) via environment variables. However, there are no explicit data residency controls or enforcement mechanisms. The system stores user chat messages, credentials, leads (with PII: name, email, phone), and document store content. Data can be stored in any configured region without residency validation. The prediction flow sends user data to LLM providers which may be in different regions/jurisdictions.
- **Gap**: No data residency enforcement. No controls to prevent data from crossing jurisdiction boundaries when sent to LLM providers. Region configuration is deployment-level, not data-level.
- **Compensating Controls**:
  - Deploy the Flowise instance in the same region as the target data residency requirement
  - Use LLM providers with regional endpoints (e.g., AWS Bedrock in specific regions) to keep data within jurisdictional boundaries
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Document data residency requirements per deployment. Add region validation for storage and LLM provider configurations. Consider implementing data classification that prevents cross-region data flows.
- **Evidence**: `packages/server/.env.example` (S3_STORAGE_REGION, DATABASE_HOST), `packages/server/src/database/entities/Lead.ts` (PII fields), `packages/server/src/database/entities/ChatMessage.ts` (user content)

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: An OpenAPI 3.0.3 specification exists at `packages/api-documentation/src/yml/swagger.yml` covering 13 tag groups (assistants, attachments, chatmessage, chatflows, document-store, feedback, leads, ping, prediction, tools, upsert-history, variables, vector). The spec includes request/response schemas, security definitions (bearerAuth), and detailed parameter descriptions. However, the server exposes 60+ routes (`packages/server/src/routes/index.ts`) and the swagger spec covers approximately 40% of them. Missing routes include: credentials, settings, stats, nodes, marketplaces, components-credentials, evaluations, evaluators, datasets, export-import, node-configs, node-custom-functions, oauth2, openai-assistants, executions, and all enterprise routes (auth, audit, user, organization, role, workspace).
- **Gap**: OpenAPI spec covers only ~40% of server routes. Missing coverage for credentials management, node configuration, marketplace, evaluations, and all enterprise/admin endpoints.
- **Compensating Controls**:
  - Limit agent tool bindings to the documented endpoints (which cover the primary agent interaction surface: predictions, chatflows, document stores)
  - Manually author agent tool definitions for undocumented endpoints as needed
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Extend the swagger.yml to cover all public API endpoints. Consider auto-generating OpenAPI spec from Express route annotations to prevent drift.
- **Evidence**: `packages/api-documentation/src/yml/swagger.yml`, `packages/server/src/routes/index.ts`

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The error handler middleware (`packages/server/src/middlewares/errors/index.ts`) returns structured JSON: `{ statusCode, success, message, stack }`. The `InternalFlowiseError` class (`packages/server/src/errors/internalFlowiseError/index.ts`) supports custom status codes. The swagger.yml documents HTTP status codes (200, 400, 401, 404, 413, 422, 500) for the prediction endpoint. However, there is no `retryable` boolean or error category field in the response body. Agents cannot programmatically distinguish between retriable errors (e.g., upstream LLM timeout) and terminal errors (e.g., invalid chatflow ID) without parsing the message string.
- **Gap**: No `retryable` or `error_code` field in error responses. Error differentiation relies on HTTP status codes and message string parsing.
- **Compensating Controls**:
  - Define a mapping of HTTP status codes to retry behavior in the agent orchestration layer (e.g., 429/503 → retry, 400/401/404 → terminal)
- **Remediation Timeline**: 30 days
- **Recommendation**: Add an `error_code` enum and `retryable` boolean to the error response schema. Example: `{ statusCode: 503, success: false, error_code: "UPSTREAM_TIMEOUT", retryable: true, message: "..." }`.
- **Evidence**: `packages/server/src/middlewares/errors/index.ts`, `packages/server/src/errors/internalFlowiseError/index.ts`

#### API-Q6: Asynchronous Operation Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The server supports asynchronous processing via BullMQ when running in queue mode (`MODE=queue`). The `QueueManager` (`packages/server/src/queue/QueueManager.ts`) manages prediction and upsert queues with Redis-backed job processing. SSE streaming (`packages/server/src/utils/SSEStreamer.ts`) provides real-time event streaming for long-running predictions. However, there is no standard async job polling endpoint (e.g., `GET /jobs/{id}/status`). The async pattern is SSE-only — agents that cannot consume SSE streams have no way to poll for completion. The BullMQ dashboard is available only in queue mode with authentication.
- **Gap**: No standard job status polling endpoint. Async pattern requires SSE stream consumption. Non-streaming agents have no mechanism to check job completion status.
- **Compensating Controls**:
  - Use the non-streaming prediction endpoint (streaming=false) which blocks until completion
  - Implement a polling wrapper at the agent orchestration layer
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a `GET /api/v1/jobs/{id}/status` endpoint that returns job state (queued, processing, completed, failed) for agents that cannot consume SSE streams.
- **Evidence**: `packages/server/src/queue/QueueManager.ts`, `packages/server/src/utils/SSEStreamer.ts`, `packages/server/.env.example` (MODE=queue)

#### DATA-Q3: Selective Query Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The chat messages endpoint supports filtering by chatType, chatId, memoryType, sessionId, startDate, endDate, feedback, and feedbackType with ordering (ASC/DESC). The document-store chunks endpoint supports pagination via pageNo. The feedback endpoint supports filtering by chatId, sortOrder, startDate, and endDate. However, many list endpoints (chatflows, tools, variables, assistants) lack filtering and pagination parameters. No cursor-based pagination is available.
- **Gap**: Inconsistent pagination and filtering across endpoints. Core entity list endpoints (chatflows, tools, variables) return unbounded result sets.
- **Compensating Controls**:
  - Agents should query by specific IDs rather than listing all resources
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add consistent pagination (limit, offset or cursor), filtering, and sorting parameters to all list endpoints.
- **Evidence**: `packages/api-documentation/src/yml/swagger.yml` (chatmessage, feedback, document-store endpoints with filters)

#### DATA-Q4: System of Record Designations — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The Flowise server is the system of record for chatflows, agents, tools, credentials, document stores, and chat messages. All entities have workspaceId for multi-tenancy. However, there is no formal system-of-record documentation, no master data management process, and no conflict resolution logic for data that may be replicated across instances. The prediction flow interacts with external LLM providers and vector stores, but the canonical state (chatflow definitions, credentials, conversation history) resides in the Flowise database.
- **Gap**: No formal system-of-record designations. No documentation of which data is authoritative in Flowise vs. external systems (e.g., OpenAI assistant state vs. Flowise assistant entity).
- **Compensating Controls**:
  - Treat Flowise as the authoritative source for chatflow definitions, credentials, and conversation history. Treat external LLM/vector store state as derivative.
- **Remediation Timeline**: 30 days
- **Recommendation**: Document system-of-record designations for each entity type.
- **Evidence**: `packages/server/src/database/entities/` (19 entity types)

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: API versioning exists — all routes are mounted under `/api/v1/`. The OpenAPI spec declares version `1.0.0`. TypeORM database migrations are versioned and managed in `packages/server/src/database/migrations/` for all supported database types (sqlite, mysql, mariadb, postgres). However, there is no breaking change detection in CI (no `buf breaking`, no OpenAPI diff, no consumer-driven contract tests like Pact). Schema changes are managed through TypeORM migrations but API contract stability is not validated in the pipeline.
- **Gap**: No automated API contract breaking change detection in CI. No consumer-driven contract testing.
- **Compensating Controls**:
  - Pin agent tool definitions to specific API response schemas and test against them
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenAPI spec diff validation to the CI pipeline (e.g., `oasdiff` or `openapi-diff`) to catch breaking changes before they reach production.
- **Evidence**: `packages/server/src/routes/index.ts` (/api/v1/ prefix), `packages/api-documentation/src/configs/swagger.config.ts` (version 1.0.0), `packages/server/src/database/migrations/`

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The server has comprehensive OpenTelemetry SDK integration (`packages/server/src/metrics/OpenTelemetry.ts`) with metric exporters for gRPC, HTTP, and proto protocols. Prometheus metrics (`packages/server/src/metrics/Prometheus.ts`) are also available with a `/api/v1/metrics` endpoint. Winston structured logging (`packages/server/src/utils/logger.ts`) produces JSON-formatted logs with timestamps. However, OpenTelemetry is configured for **metrics only** — there is no trace exporter configured (trace SDK imports exist in package.json but the OpenTelemetry.ts class only initializes metric readers, not trace providers). There is no trace ID propagation (no `traceparent` header handling). No correlation ID (request_id) is generated or logged per request.
- **Gap**: OpenTelemetry configured for metrics only, not distributed tracing. No trace ID propagation. No request correlation ID in logs.
- **Compensating Controls**:
  - Enable OpenTelemetry auto-instrumentation (`@opentelemetry/auto-instrumentations-node` is already a dependency) to get basic trace propagation
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Initialize the OpenTelemetry trace SDK alongside the metrics SDK. Enable auto-instrumentation for Express. Add a request correlation ID middleware that injects a unique ID into every log entry.
- **Evidence**: `packages/server/src/metrics/OpenTelemetry.ts` (metrics only), `packages/server/package.json` (`@opentelemetry/exporter-trace-otlp-*` dependencies present but unused), `packages/server/src/utils/logger.ts`

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Prometheus and OpenTelemetry metrics are available for HTTP request counts, request duration, and business metrics (chatflow_created, prediction counts). HTTP request duration histogram has defined buckets (1ms to 500ms). However, there are no alerting thresholds, CloudWatch alarms, PagerDuty/OpsGenie integration, or SLO-based alerting configured in the repository. Alert configuration would need to be done externally (e.g., in Prometheus Alertmanager or Grafana).
- **Gap**: No alerting thresholds or alert rules defined in the repository. Metrics are collected but not acted upon automatically.
- **Compensating Controls**:
  - Configure alerting in an external monitoring platform (Grafana, Prometheus Alertmanager) using the exposed metrics endpoint
- **Remediation Timeline**: 30 days
- **Recommendation**: Add alerting rules for: error rate > 5%, p99 latency > 30s, prediction failure rate anomalies. Configure alerting via Prometheus Alertmanager or cloud provider monitoring.
- **Evidence**: `packages/server/src/metrics/Prometheus.ts` (http_request_duration_ms histogram, http_requests_total counter), `packages/server/src/metrics/OpenTelemetry.ts`

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No Infrastructure as Code (Terraform, CloudFormation, CDK, Helm, Kustomize) was found in the repository. Infrastructure is defined only through Docker/docker-compose files (`Dockerfile`, `docker/docker-compose.yml`, `docker/docker-compose-queue-prebuilt.yml`). There is no drift detection, no automated plan review for infrastructure changes, and no IaC governance for API Gateway, IAM, secrets, or networking. The docker-compose files define the deployment topology but lack security controls (no network policies, no resource limits).
- **Gap**: No IaC for the agent-facing infrastructure surface. No drift detection. No peer review enforcement for infrastructure changes (only application code review via GitHub PRs).
- **Compensating Controls**:
  - Manage Flowise deployment infrastructure through external IaC (e.g., Terraform module for ECS/EKS deployment with IAM, security groups, and API Gateway)
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Create IaC definitions for the production deployment of Flowise (ECS/EKS task definitions, IAM roles, security groups, API Gateway configuration). Enable drift detection via AWS Config or similar.
- **Evidence**: `Dockerfile`, `docker/docker-compose.yml`, absence of any `.tf`, `.cfn.yaml`, `cdk.json`, `Chart.yaml`, or `kustomization.yaml` files

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The CI pipeline (`.github/workflows/main.yml`) runs on push to main and all PRs with: `pnpm install` → `pnpm lint` → `pnpm build` → `pnpm test:coverage` → Cypress e2e tests (Chrome browser, wait-on localhost:3000). Docker image builds are handled by separate workflows (`docker-image-dockerhub.yml`, `docker-image-ecr.yml`) triggered manually. However, there is no API contract testing (no Pact, no OpenAPI validation, no schema comparison) in the CI pipeline. Cypress e2e tests exercise the server but do not validate API contract stability.
- **Gap**: No API contract testing in CI. No OpenAPI spec validation against actual endpoints. No breaking change detection.
- **Compensating Controls**:
  - Add OpenAPI spec validation as a CI step (e.g., `swagger-cli validate` on the swagger.yml)
- **Remediation Timeline**: 30 days
- **Recommendation**: Add API contract testing to the CI pipeline: (1) validate swagger.yml syntax, (2) diff swagger.yml against previous version to detect breaking changes, (3) optionally add Pact consumer-driven contract tests.
- **Evidence**: `.github/workflows/main.yml`

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Deployment is Docker-based with manual workflow dispatch for building and pushing images to DockerHub and ECR. Docker tags are configurable (default: `latest`). TypeORM supports migration revert (`pnpm typeorm:migration-revert`). However, there is no blue/green deployment, no canary deployment, no CodeDeploy rollback triggers, and no automated rollback mechanism. Rollback would require manually deploying a previous Docker image tag. The docker-compose files have health checks (`curl -f http://localhost:${PORT}/api/v1/ping`) but no automated rollback on health check failure.
- **Gap**: No automated rollback capability. No blue/green or canary deployment. Rollback is a manual process requiring re-tagging or re-deploying a previous Docker image.
- **Compensating Controls**:
  - Tag all Docker images with semantic versions (not just `latest`) to enable quick manual rollback to a known-good image
  - Use container orchestration (ECS, Kubernetes) with rolling update and automatic rollback on health check failure
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement automated rollback via container orchestration (ECS rolling update with rollback, Kubernetes deployment rollback). Pin Docker image tags to specific versions.
- **Evidence**: `.github/workflows/docker-image-dockerhub.yml`, `docker/docker-compose.yml` (health check), `packages/server/package.json` (typeorm:migration-revert script)

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The server has Jest for unit testing (`packages/server/package.json` — jest, ts-jest, supertest dependencies) and Cypress for e2e testing (cypress dependency, `packages/server/cypress.config.ts`). The CI pipeline runs `pnpm test:coverage` and Cypress tests. The components package also has Jest tests. However, the test suites are not focused on API contract validation — there is no evidence of comprehensive API endpoint testing (input validation, output format, error responses, edge cases) in the Jest test configuration. Cypress tests exercise the web UI flow, not the API contract specifically.
- **Gap**: Test coverage exists but is not focused on API contract validation. No dedicated API test suite verifying input handling, output format consistency, and error responses for agent-consumed endpoints.
- **Compensating Controls**:
  - Use the supertest dependency to create API-level integration tests for the agent-facing endpoints (predictions, chatflows, document stores)
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create dedicated API integration tests using supertest for the primary agent-facing endpoints: `/prediction/{id}`, `/chatflows`, `/document-store`, `/chatmessage`. Test input validation, error responses, and output schema consistency.
- **Evidence**: `packages/server/package.json` (jest, supertest, cypress dependencies), `.github/workflows/main.yml` (test:coverage step)

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Docker and docker-compose files (`Dockerfile`, `docker/docker-compose.yml`) enable local deployment. The `.env.example` file provides configurable environment settings for database, storage, auth, and queue configuration. SQLite is the default database (no external dependency required). However, there is no dedicated staging environment configuration, no seed data scripts for production-equivalent data shape, and no synthetic data generators. The test setup (Cypress) runs against a fresh local instance, not a staging environment with realistic data.
- **Gap**: No dedicated staging/sandbox environment configuration with production-equivalent data shape. Local development environment exists but lacks seed data and realistic test data.
- **Compensating Controls**:
  - Deploy a separate Flowise instance with Docker using a copy of production chatflow definitions (without real credentials) as a staging environment
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a staging environment configuration with seed data scripts that populate representative chatflows, tools, and document stores. Add a `docker-compose.staging.yml` with staging-specific configuration.
- **Evidence**: `Dockerfile`, `docker/docker-compose.yml`, `packages/server/.env.example`

---

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO
- **Finding**: The server exposes a comprehensive REST API under `/api/v1/` with 60+ routes documented in `packages/server/src/routes/index.ts`. An OpenAPI 3.0.3 specification exists at `packages/api-documentation/src/yml/swagger.yml` covering the primary agent interaction endpoints (predictions, chatflows, assistants, document-stores, tools, variables, feedback, leads). The API uses standard REST conventions with JSON request/response bodies and Bearer token authentication.
- **Implication**: Agents can integrate via a well-structured REST API. The OpenAPI spec enables automated tool generation for the documented endpoints.
- **Recommendation**: Extend the OpenAPI spec coverage to all endpoints for complete agent tooling.
- **Evidence**: `packages/server/src/routes/index.ts`, `packages/api-documentation/src/yml/swagger.yml`, `packages/api-documentation/src/configs/swagger.config.ts`

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Write endpoints (POST/PUT/DELETE) exist for all major entities. No idempotency key support was found on write endpoints. POST endpoints create new resources without deduplication. However, PUT endpoints are idempotent by nature (updating by ID). No idempotency middleware or decorators were found. Since agent_scope is read-only, this is informational.
- **Implication**: If agent scope is expanded to write-enabled in the future, idempotency keys should be added to POST endpoints (especially `/prediction/{id}` and `/document-store/upsert/{id}`).
- **Recommendation**: Add idempotency key support to POST endpoints before expanding to write-enabled agent scope.
- **Evidence**: `packages/server/src/routes/index.ts`, `packages/api-documentation/src/yml/swagger.yml`

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: All API responses use JSON format with `Content-Type: application/json`. The error handler explicitly sets `res.setHeader('Content-Type', 'application/json')`. SSE streaming responses use Server-Sent Events format. The prediction endpoint returns structured JSON with fields: text, json, question, chatId, chatMessageId, sessionId, memoryType, sourceDocuments, usedTools.
- **Implication**: JSON responses are well-suited for agent consumption. LLMs can parse structured JSON effectively. SSE streaming requires event-stream parsing capability in the agent framework.
- **Recommendation**: No action needed. JSON format is optimal for agent integration.
- **Evidence**: `packages/server/src/middlewares/errors/index.ts`, `packages/api-documentation/src/yml/swagger.yml` (prediction response schema)

### API-Q7: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: The server has comprehensive SSE streaming via `SSEStreamer` (`packages/server/src/utils/SSEStreamer.ts`) with event types including: start, token, thinking, sourceDocuments, artifacts, usedTools, calledTools, agentReasoning, nextAgent, agentFlowEvent, action, abort, error, metadata, usageMetadata, and TTS events. A Redis event subscriber (`packages/server/src/queue/RedisEventSubscriber.ts`) enables cross-worker event propagation in queue mode. However, there is no webhook system for external event notification — events are SSE-only, consumed by connected clients.
- **Implication**: SSE streaming enables real-time agent interaction during predictions. For event-driven agent architectures, a webhook or event bus integration would be needed.
- **Recommendation**: Consider adding webhook endpoints or SNS/EventBridge integration for state change notifications.
- **Evidence**: `packages/server/src/utils/SSEStreamer.ts`, `packages/server/src/queue/RedisEventSubscriber.ts`

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: Rate limiting is implemented via `express-rate-limit` (`packages/server/src/utils/rateLimit.ts`) with per-chatflow configuration. Rate limiters are configured with `standardHeaders: true` which returns `RateLimit-Limit`, `RateLimit-Remaining`, and `RateLimit-Reset` headers. In queue mode, rate limiting uses Redis-backed stores for distributed consistency. Rate limits are configurable per chatflow via the `apiConfig.rateLimit` field (limitDuration, limitMax, limitMsg). The BullMQ admin dashboard also has its own rate limiter (60s window, 100 max).
- **Implication**: Agents can read rate limit headers to self-throttle. Per-chatflow rate limiting allows fine-grained control over agent traffic per flow.
- **Recommendation**: Document the default rate limit values and per-chatflow configuration in the API documentation.
- **Evidence**: `packages/server/src/utils/rateLimit.ts` (standardHeaders: true, Redis-backed store), `packages/server/.env.example`

### AUTH-Q1: Machine Identity Authentication

- **Severity**: INFO
- **Finding**: The server supports API key authentication via Bearer tokens. The `ApiKey` entity (`packages/server/src/database/entities/ApiKey.ts`) includes: apiKey, apiSecret, keyName, permissions[], workspaceId. The auth middleware in `packages/server/src/index.ts` validates API keys, resolves the associated workspace and organization, and attaches permissions, features, and workspace context to `req.user`. Enterprise features add JWT cookie authentication, session management (with Redis/PostgreSQL/MySQL/SQLite session stores), and SSO (Auth0, Azure, Google, GitHub). API keys provide machine identity with workspace-level attribution.
- **Implication**: Machine identity authentication is available and sufficient for agent integration. API keys provide principal attribution via keyName and workspaceId.
- **Recommendation**: Ensure each agent instance uses a dedicated API key with a descriptive keyName for audit trail clarity.
- **Evidence**: `packages/server/src/database/entities/ApiKey.ts`, `packages/server/src/utils/validateKey.ts`, `packages/server/src/index.ts`

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: INFO
- **Finding**: The auth middleware extracts user identity from JWT cookies (enterprise) or API keys and attaches it to `req.user` with fields: permissions, features, activeOrganizationId, activeWorkspaceId. For API key access, the workspace and organization are resolved from the key's workspaceId. The `x-request-from: internal` header bypasses API key validation and uses JWT cookie auth instead. However, there is no explicit on-behalf-of flow — API keys represent a service identity, not a delegated human identity.
- **Implication**: For read-only agent scope, direct API key authentication is sufficient. For on-behalf-of scenarios (agent acting with a specific user's permissions), additional identity delegation mechanisms would be needed.
- **Recommendation**: For current read-only scope, no action needed. For future write-enabled on-behalf-of flows, implement a token exchange or delegation mechanism.
- **Evidence**: `packages/server/src/index.ts` (auth middleware), `packages/server/src/utils/validateKey.ts`

### AUTH-Q5: Credential Management

- **Severity**: INFO
- **Finding**: The server supports AWS Secrets Manager for encryption key storage (`SECRETKEY_STORAGE_TYPE=aws` with `@aws-sdk/client-secrets-manager`). Auth secrets (TOKEN_HASH_SECRET, EXPRESS_SESSION_SECRET, JWT secrets) can be sourced from environment variables, local file storage, or AWS Secrets Manager — with a priority chain: env → AWS → filesystem. Credentials stored in the database are encrypted using `crypto-js` (`packages/server/src/database/entities/Credential.ts` — encryptedData field). No hardcoded secrets were found in source code. The `.env.example` file contains placeholder values only. The `docker-compose.yml` passes secrets via environment variables (deployment configuration, not hardcoded).
- **Implication**: Credential management has appropriate options for different deployment environments. AWS Secrets Manager integration provides production-grade secret rotation capability.
- **Recommendation**: Ensure production deployments use AWS Secrets Manager (not local file storage) for encryption keys and auth secrets. Document the secret rotation procedure.
- **Evidence**: `packages/server/.env.example` (SECRETKEY_STORAGE_TYPE, SECRETKEY_AWS_* config), `packages/server/package.json` (@aws-sdk/client-secrets-manager), `packages/server/src/database/entities/Credential.ts` (encryptedData)

### AUTH-Q7: Agent Identity Suspension

- **Severity**: INFO
- **Finding**: API keys can be managed via the `/apikey` route with full CRUD operations. The RBAC permissions include `apikeys:create`, `apikeys:update`, `apikeys:delete`. Deleting an API key immediately invalidates it — the next request with that key will fail validation in `validateAPIKey()`. However, there is no soft-disable/suspend mechanism — revocation is permanent deletion. Enterprise features add user account management with organization and workspace controls.
- **Implication**: Agent identities (API keys) can be immediately revoked by deletion. For a more graceful suspension (disable without deleting), an `enabled` field on the ApiKey entity would be needed.
- **Recommendation**: Add an `enabled` boolean field to the ApiKey entity to allow suspension without permanent deletion, preserving audit trail and enabling re-activation.
- **Evidence**: `packages/server/src/database/entities/ApiKey.ts`, `packages/server/src/routes/index.ts` (apikey route), `packages/server/src/enterprise/rbac/Permissions.ts` (apikeys:delete permission)

### AUTH-Q2: Scoped Permissions (Least Privilege)

- **Severity**: INFO
- **Finding**: The RBAC system (`packages/server/src/enterprise/rbac/Permissions.ts`) defines granular permissions across 14 categories with action-level granularity (view, create, update, delete, export, import, config, domains, share, etc.). API keys carry a `permissions[]` field that can be scoped to specific actions. Enterprise and Cloud platforms enforce these permissions. Open-source deployments have a subset of permissions available. The permission model supports workspace-level isolation via workspaceId on all entities.
- **Implication**: Scoped permissions exist and are granular enough for agent identity management. An agent API key can be restricted to read-only operations (e.g., `chatflows:view`, `tools:view`, `chatmessage:view` only).
- **Recommendation**: Create a dedicated "agent" role with minimal required permissions and assign it to all agent API keys.
- **Evidence**: `packages/server/src/enterprise/rbac/Permissions.ts`, `packages/server/src/database/entities/ApiKey.ts` (permissions[] field)

### AUTH-Q3: Action-Level Authorization

- **Severity**: INFO
- **Finding**: The RBAC system supports action-level authorization (e.g., `chatflows:view` vs. `chatflows:delete`). The enterprise middleware enforces these permissions on a per-request basis. API keys carry a permissions array that restricts which actions the key can perform. The IdentityManager checks features by plan, gating advanced features behind license tiers. However, the enforcement of action-level permissions on API key access (as opposed to JWT-authenticated users) depends on the platform tier — open-source may have limited enforcement.
- **Implication**: Action-level authorization is available in enterprise/cloud tiers. For read-only agent scope, restricting API key permissions to view-only actions provides adequate access control.
- **Recommendation**: Verify that action-level permission enforcement applies to API key-authenticated requests on the target deployment tier (enterprise/cloud vs. open-source).
- **Evidence**: `packages/server/src/enterprise/rbac/Permissions.ts`, `packages/server/src/index.ts` (req.user.permissions assignment for API keys)

### STATE-Q5: Rate Limiting and Throttling

- **Severity**: INFO
- **Finding**: Rate limiting is implemented and enforced at the API layer via `express-rate-limit` with per-chatflow configuration. In queue mode, Redis-backed rate limiting provides distributed consistency. Rate limiters return standard headers (`standardHeaders: true`). The BullMQ admin dashboard has its own rate limiter. Rate limits are configurable per chatflow via `apiConfig.rateLimit` (duration, max requests, message). The rate limiter is initialized at server startup for all existing chatflows.
- **Implication**: Rate limiting is adequate to prevent agent traffic storms. Per-chatflow configuration allows fine-grained control.
- **Recommendation**: Set default rate limits for chatflows that do not have custom rate limit configuration to provide baseline protection.
- **Evidence**: `packages/server/src/utils/rateLimit.ts`, `packages/server/src/index.ts` (rateLimiterManager initialization)

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits (max records per run, max spend per hour, max delete operations) were found. Rate limiting (STATE-Q5) protects against traffic overload but does not protect against correct-but-catastrophic write operations. Since agent_scope is read-only, this is informational — read-only agents cannot trigger bulk writes or deletes.
- **Implication**: If agent scope is expanded to write-enabled, transaction limits should be implemented before deployment.
- **Recommendation**: Implement configurable per-agent-key transaction limits before enabling write-enabled agent access.
- **Evidence**: `packages/server/src/utils/rateLimit.ts` (rate limiting only, no transaction limits)

### DATA-Q5: Temporal Metadata and Freshness

- **Severity**: INFO
- **Finding**: All major entities have temporal metadata via TypeORM decorators: `@CreateDateColumn()` (createdDate) and `@UpdateDateColumn()` (updatedDate) on ChatFlow, Credential, ChatMessage, Tool, Variable, Assistant, DocumentStore, and others. Timestamps use the database's timestamp type. Document stores have a status field (EMPTY, SYNC, SYNCING, STALE, NEW, UPSERTING, UPSERTED) that signals data freshness. However, there are no `Cache-Control` headers, no `X-Data-Age` headers, and no consistency level indicators in API responses.
- **Implication**: Agents can reason about data freshness using createdDate/updatedDate fields. Document store status provides explicit freshness signaling.
- **Recommendation**: Add `Last-Modified` or `Cache-Control` headers to GET responses to enable agent-side caching decisions.
- **Evidence**: `packages/server/src/database/entities/ChatFlow.ts` (createdDate, updatedDate), `packages/server/src/database/entities/DocumentStore.ts` (status field)

### DATA-Q6: PII Redaction in Logs

- **Severity**: INFO
- **Finding**: The logger (`packages/server/src/utils/logger.ts`) implements configurable PII redaction via `LOG_SANITIZE_BODY_FIELDS` and `LOG_SANITIZE_HEADER_FIELDS` environment variables. The default sanitize list includes: password, pwd, pass, secret, token, apikey, api_key, accesstoken, access_token, refreshtoken, refresh_token, clientsecret, client_secret, privatekey, private_key, secretkey, secret_key, auth, authorization, credential, credentials. The `sanitizeObject` function masks matching fields with `'********'` and detects email patterns (`@` and `.`), replacing them with `'**********'`. Header sanitization covers: authorization, x-api-key, x-auth-token, cookie. Request body and query sanitization is only applied when log level is debug.
- **Implication**: PII redaction is implemented and configurable. The default field list covers common sensitive fields. Email detection provides an additional layer of protection. However, sanitization of request bodies only occurs at debug log level.
- **Recommendation**: Apply body sanitization at all log levels, not just debug. Add PII redaction to error log output (which may include request context).
- **Evidence**: `packages/server/src/utils/logger.ts` (sanitizeObject, getSensitiveBodyFields), `packages/server/.env.example` (LOG_SANITIZE_BODY_FIELDS, LOG_SANITIZE_HEADER_FIELDS)

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No formal data quality score, completeness metric, or data profiling is implemented. The document store has a status field that tracks processing state (EMPTY, SYNC, SYNCING, STALE, NEW, UPSERTING, UPSERTED), which provides some freshness and completeness signaling. Entity fields use TypeORM nullable constraints. No null rate monitoring, duplicate detection, or data quality dashboards were found.
- **Implication**: Data quality monitoring would improve agent reasoning confidence, especially for document store content and chat message history.
- **Recommendation**: Add data quality metrics for document store completeness (e.g., percentage of chunks successfully upserted, stale document count).
- **Evidence**: `packages/server/src/database/entities/DocumentStore.ts` (status field)

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Entity field names are generally readable and semantically meaningful: `chatflowid`, `chatId`, `content`, `createdDate`, `updatedDate`, `encryptedData`, `flowData`, `deployed`, `isPublic`, `keyName`, `workspaceId`. Some abbreviations exist (`apikeyid` instead of `apiKeyId`) but are self-explanatory. The swagger.yml schema definitions use descriptive field names with examples. No legacy codes or cryptic abbreviations requiring a data dictionary were found.
- **Implication**: Agent LLM reasoning can interpret field names without requiring a lookup table. Minor naming inconsistencies (camelCase vs. lowercase) do not impede understanding.
- **Recommendation**: Standardize field naming to consistent camelCase across all entities.
- **Evidence**: `packages/server/src/database/entities/`, `packages/api-documentation/src/yml/swagger.yml` (component schemas)

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No formal data catalog, Glue Data Catalog, or metadata layer was found. The swagger.yml components/schemas section serves as a partial data dictionary for the API surface. TypeORM entity definitions provide the schema documentation for the database layer. The enterprise package includes feature flags and permission definitions that serve as metadata for access control.
- **Implication**: The swagger.yml and TypeORM entities together provide schema documentation, but a unified data catalog would accelerate agent tool definition.
- **Recommendation**: Consider generating a data dictionary from the TypeORM entity definitions and swagger.yml schemas.
- **Evidence**: `packages/api-documentation/src/yml/swagger.yml` (components/schemas), `packages/server/src/database/entities/`

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: The server defines business-level metrics via `FLOWISE_METRIC_COUNTERS` (`packages/server/src/Interface.Metrics.ts`): `chatflow_created`, `agentflow_created`, `assistant_created`, `tool_created`, `vector_upserted`, `chatflow_prediction_internal`, `chatflow_prediction_external`, `agentflow_prediction_internal`, `agentflow_prediction_external`. These are tracked via both Prometheus and OpenTelemetry. Additionally, HTTP request total and duration metrics provide operational visibility. PostHog integration is available for product analytics.
- **Implication**: Business outcome metrics exist and cover the primary agent interaction points (predictions, chatflow creation). These can be used to monitor agent effectiveness.
- **Recommendation**: Add agent-specific metrics (e.g., `agent_prediction_count`, `agent_api_key_usage`) to distinguish agent-originated traffic from human traffic.
- **Evidence**: `packages/server/src/Interface.Metrics.ts`, `packages/server/src/metrics/Prometheus.ts`, `packages/server/src/metrics/OpenTelemetry.ts`

### ENG-Q5: Encryption at Rest for Agent-Accessible Data

- **Severity**: INFO
- **Finding**: Credentials stored in the database are encrypted at the application level using `crypto-js` (the Credential entity has an `encryptedData` field). The encryption key is managed via `FLOWISE_SECRETKEY_OVERWRITE` or AWS Secrets Manager. Database connections support SSL (`DATABASE_SSL=true`, `DATABASE_SSL_KEY_BASE64`). S3 storage supports server-side encryption (configurable via AWS S3 settings). However, database-level encryption at rest (e.g., KMS-encrypted RDS, encrypted SQLite) is not configured in the application — it is a deployment-level concern. No customer-managed KMS keys are referenced.
- **Implication**: Application-level credential encryption is in place. Full encryption at rest depends on deployment configuration (e.g., RDS encryption, EBS encryption). This is adequate for the application layer.
- **Recommendation**: Ensure production deployments use encrypted database instances (RDS with KMS encryption) and encrypted storage volumes.
- **Evidence**: `packages/server/src/database/entities/Credential.ts` (encryptedData), `packages/server/.env.example` (DATABASE_SSL, FLOWISE_SECRETKEY_OVERWRITE, SECRETKEY_STORAGE_TYPE=aws)

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: The server exposes a comprehensive REST API under `/api/v1/` with 60+ routes. An OpenAPI 3.0.3 specification exists at `packages/api-documentation/src/yml/swagger.yml`. The API uses standard REST conventions with JSON bodies and Bearer token authentication. Integration does not require direct database access, file-based exchange, or UI automation.
- **Gap**: None — documented API interface exists.
- **Recommendation**: Extend OpenAPI spec coverage to all endpoints.
- **Evidence**: `packages/server/src/routes/index.ts`, `packages/api-documentation/src/yml/swagger.yml`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: OpenAPI 3.0.3 spec exists but covers only ~40% of server routes (13 tag groups out of 60+ routes). Missing coverage for credentials, settings, stats, nodes, marketplaces, evaluations, datasets, and all enterprise routes.
- **Gap**: Partial API spec coverage. Many endpoints undocumented.
- **Recommendation**: Extend swagger.yml to cover all public API endpoints. Consider auto-generating from Express route annotations.
- **Evidence**: `packages/api-documentation/src/yml/swagger.yml`, `packages/server/src/routes/index.ts`

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: Error handler returns `{ statusCode, success, message, stack }`. No `retryable` boolean or `error_code` enum. Agents cannot programmatically distinguish retriable from terminal errors without parsing message strings.
- **Gap**: No retryable indicator or structured error code in error responses.
- **Recommendation**: Add `error_code` enum and `retryable` boolean to error response schema.
- **Evidence**: `packages/server/src/middlewares/errors/index.ts`, `packages/server/src/errors/internalFlowiseError/index.ts`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No idempotency key support on write endpoints. PUT endpoints are naturally idempotent. POST endpoints lack deduplication. Since agent_scope is read-only, this is informational.
- **Gap**: No idempotency keys on POST endpoints.
- **Recommendation**: Add idempotency key support before expanding to write-enabled agent scope.
- **Evidence**: `packages/server/src/routes/index.ts`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: All API responses use JSON format. SSE streaming uses event-stream format. Prediction responses include structured fields (text, json, chatId, sourceDocuments, usedTools).
- **Implication**: JSON format is optimal for agent consumption.
- **Recommendation**: No action needed.
- **Evidence**: `packages/server/src/middlewares/errors/index.ts`, `packages/api-documentation/src/yml/swagger.yml`

#### API-Q6: Asynchronous Operation Support
- **Severity**: RISK-QUALITY
- **Finding**: BullMQ queue mode provides async prediction processing. SSE streaming enables real-time event consumption. However, no standard job status polling endpoint exists. Agents that cannot consume SSE streams have no way to poll for completion.
- **Gap**: No job status polling endpoint. Async pattern is SSE-only.
- **Recommendation**: Add `GET /api/v1/jobs/{id}/status` endpoint for non-streaming agents.
- **Evidence**: `packages/server/src/queue/QueueManager.ts`, `packages/server/src/utils/SSEStreamer.ts`

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: Comprehensive SSE streaming with 15+ event types (start, token, thinking, sourceDocuments, artifacts, usedTools, agentReasoning, action, etc.). Redis event subscriber enables cross-worker event propagation. No webhook system for external notification.
- **Implication**: SSE enables real-time agent interaction during predictions. Webhook integration would be needed for event-driven agent architectures.
- **Recommendation**: Consider adding webhook or SNS/EventBridge integration.
- **Evidence**: `packages/server/src/utils/SSEStreamer.ts`, `packages/server/src/queue/RedisEventSubscriber.ts`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: Rate limiting via express-rate-limit with `standardHeaders: true` returning `RateLimit-Limit`, `RateLimit-Remaining`, `RateLimit-Reset` headers. Per-chatflow configurable rate limits with Redis-backed distributed stores.
- **Implication**: Agents can read rate limit headers to self-throttle.
- **Recommendation**: Document default rate limit values in API documentation.
- **Evidence**: `packages/server/src/utils/rateLimit.ts`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: API key authentication via Bearer tokens with workspaceId attribution. Enterprise features add JWT cookies, session management, and SSO (Auth0, Azure, Google, GitHub). API keys provide machine identity with workspace-level attribution.
- **Gap**: None — machine identity authentication exists.
- **Recommendation**: Ensure each agent instance uses a dedicated API key with a descriptive keyName.
- **Evidence**: `packages/server/src/database/entities/ApiKey.ts`, `packages/server/src/utils/validateKey.ts`, `packages/server/src/index.ts`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: INFO
- **Finding**: Granular RBAC with 14 permission categories and action-level granularity. API keys carry a permissions[] field. Workspace-level isolation via workspaceId. Enterprise/Cloud tiers enforce permissions fully.
- **Gap**: None for current read-only scope — scoped permissions exist.
- **Recommendation**: Create a dedicated "agent-readonly" role with minimal required permissions.
- **Evidence**: `packages/server/src/enterprise/rbac/Permissions.ts`, `packages/server/src/database/entities/ApiKey.ts`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: INFO
- **Finding**: RBAC supports action-level authorization (e.g., `chatflows:view` vs `chatflows:delete`). Enterprise middleware enforces per-request permission checks. API keys carry permissions arrays.
- **Gap**: None for current scope — action-level authorization exists.
- **Recommendation**: Verify action-level enforcement applies to API key auth on the target deployment tier.
- **Evidence**: `packages/server/src/enterprise/rbac/Permissions.ts`, `packages/server/src/index.ts`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: Auth middleware attaches identity to req.user (permissions, features, workspaceId, organizationId). No explicit on-behalf-of flow. API keys represent service identity, not delegated human identity.
- **Gap**: No on-behalf-of delegation mechanism.
- **Recommendation**: For current read-only scope, no action needed. Implement token delegation for future write-enabled on-behalf-of flows.
- **Evidence**: `packages/server/src/index.ts`, `packages/server/src/utils/validateKey.ts`

#### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: AWS Secrets Manager supported for encryption keys. Auth secrets sourced via priority chain: env → AWS SM → filesystem. Database credentials encrypted with crypto-js. No hardcoded secrets in source code.
- **Gap**: None — credential management is adequate with AWS SM option.
- **Recommendation**: Ensure production uses AWS Secrets Manager, not local file storage.
- **Evidence**: `packages/server/.env.example`, `packages/server/package.json`, `packages/server/src/database/entities/Credential.ts`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Enterprise audit route exists (`/audit`). Winston request logging with JSON format. However, no immutable log storage, no CloudTrail, no principal attribution per request. Logs are mutable filesystem/cloud storage without object lock.
- **Gap**: No immutable audit trail. Authenticated principal not logged per request.
- **Recommendation**: Add principal to every log entry. Configure immutable log storage (S3 with object lock).
- **Evidence**: `packages/server/src/utils/logger.ts`, `packages/server/src/routes/index.ts`, `packages/server/.env.example`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: INFO
- **Finding**: API keys can be deleted via `/apikey` route, immediately invalidating them. RBAC permissions include `apikeys:delete`. However, no soft-disable/suspend mechanism exists — revocation is permanent deletion.
- **Gap**: No suspend/disable toggle — only permanent deletion.
- **Recommendation**: Add an `enabled` boolean to ApiKey entity for suspension without deletion.
- **Evidence**: `packages/server/src/database/entities/ApiKey.ts`, `packages/server/src/enterprise/rbac/Permissions.ts`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: TypeORM migrations run with `transaction: 'each'`. No saga patterns, compensating transactions, or undo endpoints for multi-step operations. Prediction flow lacks rollback logic for partial failures. AbortControllerPool can abort in-flight operations but does not compensate completed steps.
- **Gap**: No compensation or rollback for multi-step workflows.
- **Recommendation**: Implement compensation logic for the prediction pipeline and document store upsert operations.
- **Evidence**: `packages/server/src/DataSource.ts`, `packages/server/src/AbortControllerPool.ts`, `packages/server/src/queue/QueueManager.ts`

#### STATE-Q2: Queryable Current State
- **Severity**: INFO
- **Finding**: GET endpoints exist for all major entities (chatflows, assistants, tools, variables, credentials, document stores, chat messages, leads, feedback, upsert history, executions). GET by ID returns current state. Some list endpoints return unbounded results without pagination.
- **Gap**: Some list endpoints lack pagination.
- **Recommendation**: Add pagination to all list endpoints.
- **Evidence**: `packages/server/src/routes/index.ts`, `packages/api-documentation/src/yml/swagger.yml`

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled AND service has persistent state
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: The server calls 20+ external services via packages/components (LLM providers, vector stores, external tools). No circuit breaker library found (no opossum, no Resilience4j). AbortControllerPool and BullMQ retry provide partial resilience. No timeout configurations on external HTTP clients.
- **Gap**: No circuit breaker implementation for external dependency calls.
- **Recommendation**: Add a circuit breaker library (e.g., opossum) around external API calls in the components package.
- **Evidence**: `packages/components/package.json`, `packages/server/src/AbortControllerPool.ts`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: INFO
- **Finding**: Rate limiting implemented via express-rate-limit with per-chatflow configuration. Redis-backed distributed stores in queue mode. Standard headers returned (RateLimit-Limit, RateLimit-Remaining, RateLimit-Reset). Rate limits configurable per chatflow.
- **Gap**: None — rate limiting is adequately implemented.
- **Recommendation**: Set default rate limits for chatflows without custom configuration.
- **Evidence**: `packages/server/src/utils/rateLimit.ts`, `packages/server/src/index.ts`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits found. Rate limiting protects against traffic overload but not correct-but-catastrophic write operations. Read-only agents cannot trigger bulk writes.
- **Gap**: No transaction limits.
- **Recommendation**: Implement per-agent-key transaction limits before enabling write-enabled access.
- **Evidence**: `packages/server/src/utils/rateLimit.ts`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path. Priority is P2.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateful-crud`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: Docker and docker-compose files enable local deployment. `.env.example` provides configurable settings. SQLite is the default database. However, no dedicated staging environment, no seed data scripts, no synthetic data generators.
- **Gap**: No staging/sandbox environment with production-equivalent data shape.
- **Recommendation**: Create staging environment configuration with seed data scripts.
- **Evidence**: `Dockerfile`, `docker/docker-compose.yml`, `packages/server/.env.example`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification ⚡ (Tiered)
- **Severity**: RISK-SAFETY
- **Stage A**: Yes — Lead PII (name/email/phone), Credential encrypted data, ChatMessage content, ApiKey plaintext+hashed.
- **B1 — Agent-facing API response scoping**: MIXED. Credential list (`getAllCredentials`) strips `encryptedData` via `omit(c, ['encryptedData'])` (`packages/server/src/services/credentials/index.ts:63,71,102`). But `getCredentialById` **decrypts** via `decryptCredentialData` and returns `plainDataObj` with the credential in plaintext (`packages/server/src/services/credentials/index.ts:138-147`). API keys list returns `apiKey` column in plaintext (`packages/server/src/services/apikey/index.ts:109-131`); `apiSecret` is hashed. Under `read-only` scope this is RISK-SAFETY (not BLOCKER) — the agent can call the endpoints but cannot escalate via writes.
- **B2 — Access control differentiation**: CLEAR. Workspace-scoped queries; role-based filtering on API keys (non-admins see only permissions subset of their own); `validatePermissions` enforces that API keys cannot carry `workspace:*` / `admin:*`.
- **B3 — Formal classification metadata**: INFO. AES-256 at-rest via `ENCRYPTION_KEY` (file or AWS Secrets Manager per `packages/server/src/utils/index.ts:1550-1598`) is a classification-by-encryption primitive; no formal decorators.
- **Overall**: B1 fires as RISK-SAFETY under read-only → **DATA-Q1 = RISK-SAFETY**.
- **Recommendation**: Mask `apiKey` in list responses (return truncated prefix only); require explicit intent parameter for `getCredentialById` to decrypt (default to encrypted blob); add field-level decorators for documentation.
- **Evidence**: `packages/server/src/services/credentials/index.ts`, `packages/server/src/services/apikey/index.ts:109-131`, `packages/server/src/database/entities/Credential.ts`, `packages/server/src/database/entities/ApiKey.ts`, `packages/server/src/utils/index.ts:1550-1598`.

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Configurable storage regions via environment variables (S3_STORAGE_REGION, DATABASE_HOST). However, no explicit data residency enforcement. Prediction flow sends user data to LLM providers potentially in different jurisdictions. No controls to prevent cross-region data flows.
- **Gap**: No data residency enforcement. No controls preventing cross-jurisdiction data flows to LLM providers.
- **Recommendation**: Document residency requirements per deployment. Add region validation for storage and LLM provider configurations.
- **Evidence**: `packages/server/.env.example`, `packages/server/src/database/entities/Lead.ts`, `packages/server/src/database/entities/ChatMessage.ts`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK-QUALITY
- **Finding**: Chat messages endpoint supports filtering (chatType, chatId, sessionId, startDate, endDate, feedback). Document-store chunks has pagination (pageNo). Feedback supports filtering and sorting. However, core entity list endpoints (chatflows, tools, variables, assistants) lack filtering and pagination.
- **Gap**: Inconsistent pagination and filtering. Core list endpoints return unbounded results.
- **Recommendation**: Add consistent pagination, filtering, and sorting to all list endpoints.
- **Evidence**: `packages/api-documentation/src/yml/swagger.yml`

#### DATA-Q4: System of Record Designations
- **Severity**: RISK-QUALITY
- **Finding**: Flowise is the system of record for chatflows, agents, tools, credentials, document stores, and chat messages. All entities have workspaceId for multi-tenancy. No formal system-of-record documentation or conflict resolution logic.
- **Gap**: No formal system-of-record designations or documentation.
- **Recommendation**: Document system-of-record designations for each entity type.
- **Evidence**: `packages/server/src/database/entities/`

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: INFO
- **Finding**: All major entities have `@CreateDateColumn()` (createdDate) and `@UpdateDateColumn()` (updatedDate). Document stores have status fields (EMPTY, SYNC, SYNCING, STALE, NEW, UPSERTING, UPSERTED) for freshness signaling. However, no Cache-Control headers, no X-Data-Age headers, no consistency level indicators in API responses.
- **Gap**: No HTTP-level freshness headers in responses.
- **Recommendation**: Add Last-Modified or Cache-Control headers to GET responses.
- **Evidence**: `packages/server/src/database/entities/ChatFlow.ts`, `packages/server/src/database/entities/DocumentStore.ts`

#### DATA-Q6: PII Redaction in Logs
- **Severity**: INFO
- **Finding**: Logger implements configurable PII redaction via `LOG_SANITIZE_BODY_FIELDS` and `LOG_SANITIZE_HEADER_FIELDS`. Default sanitize list covers passwords, tokens, API keys, credentials, and authorization headers. Email pattern detection replaces email addresses. Header sanitization covers authorization, x-api-key, x-auth-token, cookie. Request body sanitization only applied at debug log level.
- **Gap**: Body sanitization limited to debug level. Error logs may include unsanitized request context.
- **Recommendation**: Apply body sanitization at all log levels. Add PII redaction to error log output.
- **Evidence**: `packages/server/src/utils/logger.ts`, `packages/server/.env.example`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No formal data quality scoring. Document store status field tracks processing state. Entity fields use TypeORM nullable constraints. No null rate monitoring, duplicate detection, or data quality dashboards.
- **Implication**: Data quality monitoring would improve agent reasoning confidence.
- **Recommendation**: Add data quality metrics for document store completeness.
- **Evidence**: `packages/server/src/database/entities/DocumentStore.ts`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: API versioning exists (`/api/v1/`). OpenAPI spec version 1.0.0. TypeORM database migrations are versioned. However, no breaking change detection in CI, no OpenAPI diff, no consumer-driven contract tests.
- **Gap**: No automated API contract breaking change detection in CI.
- **Recommendation**: Add OpenAPI spec diff validation to CI pipeline.
- **Evidence**: `packages/server/src/routes/index.ts`, `packages/api-documentation/src/configs/swagger.config.ts`, `packages/server/src/database/migrations/`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Field names are generally readable and semantically meaningful (chatflowid, content, createdDate, encryptedData, flowData, deployed, isPublic, keyName, workspaceId). Minor inconsistencies (camelCase vs. lowercase). No legacy codes or cryptic abbreviations.
- **Implication**: Agent LLM reasoning can interpret field names without a lookup table.
- **Recommendation**: Standardize to consistent camelCase.
- **Evidence**: `packages/server/src/database/entities/`, `packages/api-documentation/src/yml/swagger.yml`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal data catalog. Swagger.yml components/schemas serves as partial data dictionary. TypeORM entity definitions provide database schema documentation. No Glue Data Catalog, Collibra, or similar.
- **Implication**: Schema documentation exists across swagger.yml and TypeORM entities but is not unified.
- **Recommendation**: Generate a unified data dictionary from TypeORM entities and swagger.yml.
- **Evidence**: `packages/api-documentation/src/yml/swagger.yml`, `packages/server/src/database/entities/`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: OpenTelemetry SDK integration for metrics (gRPC, HTTP, proto exporters). Prometheus metrics with `/api/v1/metrics` endpoint. Winston structured JSON logging with timestamps. However, OpenTelemetry is configured for metrics only — no trace exporter initialized. No trace ID propagation, no correlation ID per request.
- **Gap**: No distributed tracing. No request correlation ID. Metrics only, not traces.
- **Recommendation**: Initialize OpenTelemetry trace SDK. Enable auto-instrumentation. Add request correlation ID middleware.
- **Evidence**: `packages/server/src/metrics/OpenTelemetry.ts`, `packages/server/package.json`, `packages/server/src/utils/logger.ts`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: Prometheus and OpenTelemetry metrics available (http_requests_total, http_request_duration_ms, business counters). HTTP duration histogram with defined buckets. However, no alerting thresholds, no CloudWatch alarms, no PagerDuty/OpsGenie integration configured in the repository.
- **Gap**: No alerting thresholds or alert rules. Metrics collected but not automatically acted upon.
- **Recommendation**: Configure alerting rules for error rate, p99 latency, and prediction failure rate.
- **Evidence**: `packages/server/src/metrics/Prometheus.ts`, `packages/server/src/metrics/OpenTelemetry.ts`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: Business metrics defined via FLOWISE_METRIC_COUNTERS: chatflow_created, agentflow_created, assistant_created, tool_created, vector_upserted, chatflow_prediction_internal/external, agentflow_prediction_internal/external. Tracked via Prometheus and OpenTelemetry. PostHog integration for product analytics.
- **Implication**: Business outcome metrics cover primary agent interaction points and can monitor agent effectiveness.
- **Recommendation**: Add agent-specific metrics to distinguish agent-originated traffic from human traffic.
- **Evidence**: `packages/server/src/Interface.Metrics.ts`, `packages/server/src/metrics/Prometheus.ts`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK-QUALITY
- **Finding**: No IaC (Terraform, CloudFormation, CDK, Helm, Kustomize) found. Infrastructure defined only through Docker/docker-compose. No drift detection, no automated plan review, no IaC governance for API Gateway, IAM, secrets, or networking.
- **Gap**: No IaC for agent-facing infrastructure. No drift detection.
- **Recommendation**: Create IaC definitions for production deployment (ECS/EKS, IAM, security groups, API Gateway).
- **Evidence**: `Dockerfile`, `docker/docker-compose.yml`, absence of `.tf`, `.cfn.yaml`, `cdk.json` files

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: CI pipeline runs lint, build, test:coverage, and Cypress e2e tests on push/PR. Docker image builds via manual workflows. However, no API contract testing, no OpenAPI validation, no breaking change detection in CI.
- **Gap**: No API contract testing in CI pipeline.
- **Recommendation**: Add OpenAPI spec validation and breaking change detection to CI.
- **Evidence**: `.github/workflows/main.yml`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: Docker-based deployment with manual workflow dispatch. TypeORM supports migration revert. Health checks configured. However, no blue/green, no canary, no automated rollback. Rollback requires manual Docker image re-deployment.
- **Gap**: No automated rollback capability. Manual process only.
- **Recommendation**: Implement automated rollback via container orchestration (ECS/Kubernetes rolling update).
- **Evidence**: `.github/workflows/docker-image-dockerhub.yml`, `docker/docker-compose.yml`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: Jest unit tests and Cypress e2e tests with supertest available. CI runs test:coverage. However, no dedicated API contract validation test suite. Cypress exercises web UI flows, not API contracts specifically.
- **Gap**: No dedicated API test suite for agent-consumed endpoints.
- **Recommendation**: Create API integration tests using supertest for prediction, chatflows, and document-store endpoints.
- **Evidence**: `packages/server/package.json`, `.github/workflows/main.yml`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: INFO
- **Finding**: Credentials encrypted at application level via crypto-js (encryptedData field). Encryption key managed via FLOWISE_SECRETKEY_OVERWRITE or AWS Secrets Manager. Database connections support SSL. S3 supports server-side encryption. Database-level encryption at rest is a deployment concern, not configured in the application.
- **Gap**: Full encryption at rest depends on deployment configuration.
- **Recommendation**: Ensure production uses encrypted database instances (RDS with KMS) and encrypted storage volumes.
- **Evidence**: `packages/server/src/database/entities/Credential.ts`, `packages/server/.env.example`

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| packages/server/src/index.ts | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q5, STATE-Q5 |
| packages/server/src/routes/index.ts | API-Q1, API-Q2, AUTH-Q1, AUTH-Q7, STATE-Q2 |
| packages/server/src/utils/validateKey.ts | AUTH-Q1, AUTH-Q4 |
| packages/server/src/utils/rateLimit.ts | API-Q8, STATE-Q5, STATE-Q6 |
| packages/server/src/utils/logger.ts | AUTH-Q6, DATA-Q6, OBS-Q1 |
| packages/server/src/utils/SSEStreamer.ts | API-Q6, API-Q7 |
| packages/server/src/middlewares/errors/index.ts | API-Q3, API-Q5 |
| packages/server/src/errors/internalFlowiseError/index.ts | API-Q3 |
| packages/server/src/IdentityManager.ts | AUTH-Q1, AUTH-Q4, AUTH-Q5 |
| packages/server/src/DataSource.ts | STATE-Q1, ENG-Q5 |
| packages/server/src/AbortControllerPool.ts | STATE-Q1, STATE-Q4 |
| packages/server/src/queue/QueueManager.ts | API-Q6, STATE-Q1, STATE-Q4 |
| packages/server/src/queue/RedisEventSubscriber.ts | API-Q7 |
| packages/server/src/metrics/OpenTelemetry.ts | OBS-Q1, OBS-Q2, OBS-Q3 |
| packages/server/src/metrics/Prometheus.ts | OBS-Q1, OBS-Q2, OBS-Q3 |
| packages/server/src/Interface.Metrics.ts | OBS-Q3 |
| packages/server/src/enterprise/rbac/Permissions.ts | AUTH-Q2, AUTH-Q3, AUTH-Q7 |
| packages/server/src/database/entities/ApiKey.ts | AUTH-Q1, AUTH-Q2, AUTH-Q7, DATA-Q1 |
| packages/server/src/database/entities/ChatFlow.ts | HITL-Q1, DATA-Q5, STATE-Q2 |
| packages/server/src/database/entities/Credential.ts | DATA-Q1, ENG-Q5 |
| packages/server/src/database/entities/Lead.ts | DATA-Q1, DATA-Q2 |
| packages/server/src/database/entities/ChatMessage.ts | DATA-Q1, DATA-Q2, DATA-Q5 |
| packages/server/src/database/entities/DocumentStore.ts | HITL-Q1, DATA-Q5, DATA-Q7 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| packages/api-documentation/src/yml/swagger.yml | API-Q1, API-Q2, API-Q3, API-Q4, API-Q5, HITL-Q1, HITL-Q2, DATA-Q3, DISC-Q1, DISC-Q2 |
| packages/api-documentation/src/configs/swagger.config.ts | API-Q1, API-Q2, DISC-Q1 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| .github/workflows/main.yml | ENG-Q2, ENG-Q3, ENG-Q4 |
| .github/workflows/docker-image-dockerhub.yml | ENG-Q3 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| Dockerfile | ENG-Q1, ENG-Q3, HITL-Q3 |
| docker/docker-compose.yml | ENG-Q1, ENG-Q3, HITL-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| packages/server/package.json | AUTH-Q5, STATE-Q4, OBS-Q1, ENG-Q4, ENG-Q5 |
| packages/components/package.json | STATE-Q4 |
| package.json | ENG-Q2 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| packages/server/.env.example | AUTH-Q5, AUTH-Q6, DATA-Q2, DATA-Q6, OBS-Q1, ENG-Q5, STATE-Q5, HITL-Q3 |
| artillery-load-test.yml | STATE-Q7 |
