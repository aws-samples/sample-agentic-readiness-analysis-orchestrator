# Agentic Readiness Analysis Report

**Target**: . (serverless/serverless monorepo)
**Date**: 2026-04-30
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**TD Version**: agentic-readiness-analysis
**Repository Type**: monorepo
**Service Archetype**: orchestrator (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: javascript, serverless, iac, cli
**Context**: Serverless Framework CLI for building and deploying serverless apps.

**Archetype Justification**: The monorepo is primarily a CLI tool that orchestrates AWS deployments across 20+ AWS services (Lambda, IAM, S3, SQS, DynamoDB, CloudFormation, ECS, CloudFront, etc.) via the engine package, and exposes a read-only MCP server for agent-based introspection of deployed resources.

**Surface Flags**:
- has_persistent_data_store: false (no databases owned; state is persisted by consumer via stateStore abstraction)
- has_http_rpc_surface: true (MCP server exposes Express SSE endpoints at GET /sse and POST /messages)
- has_auth_surface: true (sf-core has Serverless Dashboard OAuth/JWT/License Key authentication)
- has_write_operations: true (deploy/remove commands write to AWS infrastructure via CloudFormation/direct SDK calls)
- has_logging_of_user_data: false (logging is diagnostic only — OS, arch, shell, node paths — no user PII)

---

## Readiness Profile: Pilot-Ready (Safety Concerns)

**BLOCKERs**: 0 | **RISK-SAFETY**: 3 | **RISK-QUALITY**: 8 | **INFOs**: 22

Supervised pilot with elevated safety oversight: (1) all Pilot-Ready controls apply, (2) prioritize RISK-SAFETY remediation before expanding agent scope, (3) dedicated safety review cadence, (4) agent restricted to lowest-blast-radius operations until RISK-SAFETY count drops below 3.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 0 |
| RISK-SAFETY | 3 |
| RISK-QUALITY | 8 |
| INFO | 22 |
| N/A | 0 |
| Not Evaluated (extended) | 10 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 9
**Extended Questions Not Triggered**: 10
**Questions N/A (repo_type: monorepo)**: 0
**Service Archetype**: orchestrator (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

No BLOCKERs identified.

---

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The MCP server has no circuit breaker, retry, or timeout configuration for its own AWS SDK calls. Individual MCP tools (e.g., `lambda-info.js`, `sqs-info.js`) call AWS APIs directly without resilience wrappers. The engine package uses `@smithy/util-retry` for some operations, but the MCP server itself does not.
- **Gap**: No circuit breaker pattern or timeout configuration exists in the MCP server's AWS SDK calls. A cascading failure from a slow or throttled AWS API response will propagate directly to the MCP client.
- **Compensating Controls**:
  - Limit the MCP server to a single-user local process (default SSE on localhost:3001), reducing blast radius
  - AWS SDK v3 has built-in retry with exponential backoff, providing some baseline resilience
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add timeout configuration to all AWS SDK client instantiations in `packages/mcp/src/lib/aws/`. Consider wrapping calls with a circuit breaker library (e.g., `cockatiel` or `opossum`) to prevent cascading failures when AWS APIs are degraded.
- **Evidence**: `packages/mcp/src/lib/aws/*.js`, `packages/mcp/src/lib/confirmation-handler.js` (uses `AwsCloudWatchClient` without timeout config)

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The MCP server (Express app in `packages/mcp/src/server.js`) has no rate limiting middleware. Any client connected via SSE can issue unlimited tool calls at machine speed. There is no API Gateway or WAF in front of the MCP server — it runs as a bare Express process.
- **Gap**: No rate limiting exists at the API layer. A runaway agent loop could issue unlimited AWS API calls through the MCP tools, potentially hitting AWS service limits or incurring unexpected costs.
- **Compensating Controls**:
  - The MCP server defaults to localhost-only (port 3001), limiting exposure to the local machine
  - The confirmation handler in `confirmation-handler.js` provides a human-in-the-loop gate for costly CloudWatch queries, partially mitigating unbounded cost
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `express-rate-limit` middleware to the MCP server with sensible defaults (e.g., 60 requests per minute per session). For the stdio transport, consider adding a tool-call rate limiter in the analytics wrapper.
- **Evidence**: `packages/mcp/src/server.js` (no rate limiting middleware), `packages/mcp/src/lib/confirmation-handler.js`

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The sf-core Authentication class supports `unAuthenticate()` to remove user sessions and license keys from `.serverlessrc`. AWS IAM roles/profiles used by the MCP server can be suspended via standard AWS IAM controls (deactivate access keys, revoke role sessions). However, the MCP server itself has no built-in mechanism to suspend or revoke an individual agent's identity or session — there is no session revocation endpoint, no agent identity registry, and no way to block a specific MCP client without restarting the server process.
- **Gap**: No application-level agent identity suspension exists. The MCP server cannot selectively disconnect or block a specific agent session. Suspension relies entirely on external AWS IAM controls, which operate at the credential level (not the agent session level). If multiple agents share the same AWS credentials, suspending one suspends all.
- **Compensating Controls**:
  - AWS IAM provides credential-level suspension (deactivate access keys, revoke SSO sessions, modify IAM policies)
  - The MCP server's `stop()` method can terminate all connections, though this is a blunt instrument affecting all clients
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement session-level identity management in the MCP server: (1) maintain an active session registry with client metadata, (2) add an admin endpoint or mechanism to revoke individual sessions by sessionId, (3) document the AWS IAM-based suspension approach as the primary control for credential-level revocation.
- **Evidence**: `packages/sf-core/src/lib/auth/index.js` (unAuthenticate method), `packages/mcp/src/server.js` (activeTransports map — sessions tracked but no revocation mechanism)

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, or Swagger specification file exists in the repository. The MCP server defines tools using Zod schemas in `packages/mcp/src/tools-definition.js`, which the MCP SDK exposes as machine-readable tool definitions via the MCP protocol. However, there is no standalone spec file that can be consumed outside the MCP protocol.
- **Gap**: Agent tool generation outside the MCP protocol requires manual work. No static specification file exists for API documentation tooling, SDK generation, or contract testing.
- **Compensating Controls**:
  - The MCP protocol itself provides machine-readable tool schemas (Zod-based) to any connected MCP client
  - The `packages/mcp/README.md` documents all tools, inputs, and outputs comprehensively
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Generate a standalone tool schema export (JSON) from the Zod definitions for use in contract testing and documentation pipelines.
- **Evidence**: `packages/mcp/src/tools-definition.js`, `packages/mcp/README.md`

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The MCP server has a well-structured AWS credentials error handler (`aws-credentials-error-handler.js`) that maps error patterns to user-friendly messages with profile context. However, general MCP tool errors are returned as unstructured text strings — there is no consistent error code, retryable boolean, or error category in non-credential error responses.
- **Gap**: Agents cannot reliably distinguish retriable errors (AWS throttling) from terminal errors (invalid parameters) in the MCP tool response format.
- **Compensating Controls**:
  - The credentials error handler provides structured guidance for the most common failure mode (AWS credential issues)
  - MCP protocol-level errors (JSON-RPC) have standard error codes
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Wrap all MCP tool responses in a consistent envelope: `{ success: boolean, errorCode?: string, retryable?: boolean, message: string, data?: any }`.
- **Evidence**: `packages/mcp/src/lib/aws-credentials-error-handler.js`, `packages/serverless/lib/serverless-error.js`

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The MCP server version is hardcoded as `1.0.0` in both `server.js` and `stdio-server.js`. The Zod schemas in `tools-definition.js` have no versioning. The `VERSIONING.md` file describes semver policy for the Framework but does not cover MCP tool schema versioning. No breaking change detection (OpenAPI diff, Pact, buf breaking) exists in CI.
- **Gap**: MCP tool schemas can change without notice. Agent tool bindings may break silently after an update. No consumer-driven contract testing or schema comparison in the CI pipeline.
- **Compensating Controls**:
  - The MCP package is `private: true` and not published to npm, limiting distribution
  - The monorepo's semver policy (VERSIONING.md) covers CLI changes but not MCP tool schemas
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add MCP tool schema versioning (e.g., export a schema version alongside tool definitions) and add a CI step that compares tool schemas against a baseline to detect breaking changes before release.
- **Evidence**: `packages/mcp/src/server.js` (version: '1.0.0'), `packages/mcp/src/tools-definition.js`, `VERSIONING.md`

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The MCP server uses `console.error` for logging (e.g., client connected/disconnected events, errors). There is no structured JSON logging, no correlation IDs, and no distributed tracing (X-Ray, OpenTelemetry). The sf-core and engine packages use `@serverless/util` logger with named channels (`log.get('core')`, `log.get('engine')`) but these are text-based, not structured JSON.
- **Gap**: When an MCP tool call fails, there is no trace ID or correlation ID linking the request through the MCP server to the underlying AWS API calls. Debugging agent-initiated failures requires manual log correlation.
- **Compensating Controls**:
  - The MCP server runs locally, so logs are directly accessible on the same machine
  - AWS CloudTrail captures downstream API calls with request IDs
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Replace `console.error` in the MCP server with structured JSON logging (e.g., `pino` or `winston`) and propagate a request/session ID through tool calls.
- **Evidence**: `packages/mcp/src/server.js` (console.error), `packages/sf-core/src/lib/router.js`, `packages/util/src/logger/`

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No alerting configuration exists for the MCP server itself. The MCP tools CAN query CloudWatch alarms for user's deployed resources (`aws-cloudwatch-alarms` tool), but the MCP server process has no self-monitoring, no health check endpoint, and no error rate alerting.
- **Gap**: If the MCP server starts failing or experiencing high latency, there is no automated alert to the operator.
- **Compensating Controls**:
  - The MCP server is a local process — the user will notice failures immediately via the MCP client UI
  - The stdio transport mode doesn't require network monitoring
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add a `/health` endpoint to the SSE server and consider emitting basic metrics (tool call count, error count, latency) as structured log events.
- **Evidence**: `packages/mcp/src/server.js`

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The CI pipeline (`ci-framework.yml`) includes ESLint, Prettier, unit tests (sf-core, serverless, engine), and integration tests. However, there is no API contract testing for the MCP tool schemas — no Pact tests, no OpenAPI validation, no schema comparison. The MCP package has unit tests (`packages/mcp/tests/`) but these test tool behavior, not schema stability.
- **Gap**: Breaking changes to MCP tool input/output schemas are not caught by the CI pipeline before release.
- **Compensating Controls**:
  - Unit tests in `packages/mcp/tests/` exercise tool behavior and will catch functional regressions
  - The release pipeline runs cross-platform tests (ubuntu, arm-linux, windows) before publishing
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a CI step that serializes MCP tool schemas to a baseline JSON file and fails on breaking changes (parameter removal, type changes, required field additions).
- **Evidence**: `.github/workflows/ci-framework.yml`, `packages/mcp/tests/`, `packages/mcp/jest.config.js`

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The MCP package has unit tests (`deployment-history.test.js`, `docs.test.js`, `list-resources.test.js`, `service-summary.test.js`) and an e2e test for `aws-errors-info`. However, several MCP tools lack dedicated tests: `aws-lambda-info`, `aws-iam-info`, `aws-sqs-info`, `aws-s3-info`, `aws-rest-api-gateway-info`, `aws-http-api-gateway-info`, `aws-dynamodb-info`, `aws-logs-search`, `aws-logs-tail`, `aws-cloudwatch-alarms`, `list-projects`. The engine and sf-core packages have broader test coverage.
- **Gap**: Approximately 11 of 16 MCP tools have no dedicated unit test coverage. Edge cases in parameter validation, error handling, and AWS SDK response parsing are untested.
- **Compensating Controls**:
  - The tested tools cover the most complex patterns (service-summary, list-resources, errors-info)
  - Integration tests in sf-core cover end-to-end deployment flows
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add unit tests for untested MCP tools, focusing on parameter validation, error response formatting, and AWS API response parsing edge cases.
- **Evidence**: `packages/mcp/tests/`, `packages/engine/test/`, `packages/sf-core/tests/`

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The CI pipeline uses separate environments (dev/prod) with dedicated license keys (`SERVERLESS_LICENSE_KEY_DEV`, `SERVERLESS_ACCESS_KEY_DEV`). Integration tests deploy to a test stage (`pr-{username}`, `mr-{actor}`). The MCP server can be started locally (`npm start`) for development testing. However, there is no formal sandbox environment for testing agent interactions with the MCP server against mock AWS resources, and no mock/stub mode exists.
- **Gap**: No mock/stub mode for the MCP server. No formal sandbox for agent testing. Agents cannot be tested against the MCP server without real AWS credentials and live AWS resources.
- **Compensating Controls**:
  - The MCP server runs locally, providing isolation from production
  - CI integration tests deploy to ephemeral test stages, providing some environment separation
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add a mock/stub mode for the MCP server that returns synthetic AWS data for agent testing without requiring real AWS credentials. Consider a `--mock` flag or environment variable that switches AWS SDK calls to local fixtures.
- **Evidence**: `.github/workflows/ci-framework.yml`, `.github/workflows/release-framework.yml`, `packages/mcp/package.json` (start scripts)

---

## INFOs — Architecture and Design Inputs

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The MCP tools are all read-only (query/inspect AWS resources). No write endpoints exist in the MCP server. The CLI's deploy/remove commands use CloudFormation (inherently idempotent for stack operations) and the engine's state management with Zod validation.
- **Implication**: If agent_scope were expanded to write-enabled, idempotency of deploy operations would need evaluation. Currently not applicable.
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: `packages/mcp/src/tools-definition.js` (all tools are read-only queries)

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: MCP tools return structured JSON responses via the MCP protocol's `content` array with `type: "text"` entries containing formatted text/JSON. The response format is dictated by the MCP SDK standard.
- **Implication**: Agent consumers parse MCP tool responses via the standard MCP client library. The text content within responses is human-readable but well-structured.
- **Recommendation**: Consider returning structured JSON objects within MCP text content for easier programmatic parsing by agents.
- **Evidence**: `packages/mcp/src/tools-definition.js`, `packages/mcp/src/tools/aws/*.js`

### API-Q6: Asynchronous Operation Support

- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `orchestrator`, agent_scope: `read-only`.
- **Trigger**: Service has operations >30s OR long-running workflows
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### API-Q7: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: The Serverless Framework CLI orchestrates state changes (deploy, remove, rollback) across 20+ AWS services via CloudFormation. The sf-core router emits product analytics events to the Serverless Platform (`instanceUsageTrackingClient`, `platformEventClient`) tracking deployments and actions. The MCP analytics wrapper (`wrapServerWithAnalytics`) emits tool execution events. However, there are no webhook, SNS, EventBridge, or streaming event emission endpoints for external consumers to subscribe to state change notifications.
- **Implication**: Agents cannot subscribe to deployment completion, rollback, or infrastructure state change events proactively. This limits agent workflows to polling-based approaches (e.g., repeated `deployment-history` tool calls). For read-only agent scope, this is informational — agents currently only query state rather than react to changes.
- **Recommendation**: Consider adding EventBridge or webhook support for deployment lifecycle events (deploy-started, deploy-completed, deploy-failed, rollback-initiated) to enable event-driven agent workflows.
- **Evidence**: `packages/sf-core/src/lib/router.js` (platformEventClient, instanceUsageTrackingClient), `packages/mcp/src/utils/analytics-utils.js` (wrapServerWithAnalytics), `packages/mcp/src/tools-definition.js` (deployment-history tool — polling-only approach)

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: The MCP server does not document rate limits or return rate limit headers. The MCP protocol does not define standard rate limit headers. The confirmation handler in `confirmation-handler.js` provides cost-awareness gates for CloudWatch queries but this is not rate limiting.
- **Implication**: Agents have no signal to self-throttle. AWS service limits are the effective constraint.
- **Recommendation**: Document MCP server capacity expectations and consider adding a rate-limit-like response when tool calls exceed a threshold.
- **Evidence**: `packages/mcp/src/server.js`, `packages/mcp/src/lib/confirmation-handler.js`

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: INFO
- **Finding**: The sf-core Authentication class supports JWT-based user sessions, OAuth2 access keys, and license keys with `callerIdentity` validation. The MCP server delegates to the AWS credentials chain (profiles, SSO, env vars) without additional identity propagation. There is no on-behalf-of flow — the MCP tools use whatever AWS credentials are available on the host.
- **Implication**: When an agent calls MCP tools, the AWS credentials used are the host's credentials, not agent-specific credentials. This is appropriate for a local CLI tool but would need enhancement for multi-tenant scenarios.
- **Recommendation**: For enterprise deployments, consider supporting agent-specific AWS profiles or role assumption per MCP session.
- **Evidence**: `packages/sf-core/src/lib/auth/index.js`, `packages/mcp/src/tools-definition.js` (profile/region params)

### AUTH-Q5: Credential Management

- **Severity**: INFO
- **Finding**: The sf-core authentication module supports multiple credential sources: SSM Parameter Store (`/serverless-framework/license-key`), `.serverlessrc` file in home directory, environment variables (`SERVERLESS_ACCESS_KEY`, `SERVERLESS_LICENSE_KEY`), and JWT-based browser login. No credentials are hardcoded in the repository. The MCP server delegates entirely to the AWS SDK credentials chain. The engine's `obfuscateSensitiveData` function masks sensitive data before state persistence.
- **Implication**: Credential management follows AWS best practices. The `.serverlessrc` file stores tokens locally but this is standard for CLI tools (equivalent to `~/.aws/credentials`).
- **Recommendation**: No immediate action needed. Consider recommending AWS SSO over long-lived access keys in documentation.
- **Evidence**: `packages/sf-core/src/lib/auth/index.js`, `packages/engine/src/index.js` (obfuscateSensitiveData)

### AUTH-Q6: Immutable Audit Logging ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY, but surface-flag downgrade applies. The MCP server is a local CLI tool that delegates to AWS credentials. Audit logging of agent-invoked read operations is a consumer responsibility — AWS CloudTrail logs all API calls made with the host's credentials.
- **Finding**: No application-level audit logging exists in the MCP server. The sf-core router sends telemetry/analysis events to the Serverless Platform (`platformEventClient`, `instanceUsageTrackingClient`) but this is product analytics, not immutable audit trails.
- **Implication**: AWS CloudTrail provides the audit trail for all AWS API calls. The MCP server does not add its own audit layer.
- **Recommendation**: For compliance-sensitive environments, ensure CloudTrail is enabled in all regions where agents will operate.
- **Evidence**: `packages/sf-core/src/lib/router.js` (telemetry), `packages/mcp/src/utils/analytics-utils.js`

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY, but surface-flag calibration: MCP tools are read-only and have no write path that would need compensation. The CLI's rollback plugin exists for user-initiated write operations.
- **Finding**: The serverless Framework includes a rollback plugin (`packages/serverless/lib/plugins/rollback.js`). The engine manages state with Zod-validated save/load cycles and timestamp tracking (`timeCreated`, `timeLastUpdated`, `timeLastDeployed`). CloudFormation provides built-in rollback for failed stack operations.
- **Implication**: Not applicable for read-only agent scope. The MCP server performs no write operations.
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: `packages/serverless/lib/plugins/rollback.js`, `packages/engine/src/index.js`

### STATE-Q2: Queryable Current State

- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `orchestrator`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No transaction limits exist for MCP tool calls. The confirmation handler provides cost awareness for CloudWatch Insights queries (asks user confirmation for >3 hour timeframes) but this is not a configurable transaction limit.
- **Implication**: Not applicable for read-only agent scope. The confirmation handler partially addresses cost control.
- **Recommendation**: No action needed for read-only scope. If write operations are added, implement configurable transaction limits.
- **Evidence**: `packages/mcp/src/lib/confirmation-handler.js`

### DATA-Q1: Sensitive Data Classification

- **Severity**: INFO
- **Finding**: Stage A scope gate: The system handles credentials (access keys, license keys, JWT tokens, refresh tokens) in the sf-core auth module. However, the MCP server itself does NOT handle sensitive data — it queries AWS and returns resource metadata. The engine's `obfuscateSensitiveData` function explicitly masks sensitive keys (like `environment` variables) before saving state. The sf-core auth module stores credentials in `.serverlessrc` (user's home directory, standard CLI pattern).
- **Implication**: Credential handling follows standard CLI patterns. The MCP server's read-only operations return AWS resource metadata, not PII. Data classification is a consumer responsibility.
- **Recommendation**: No action needed. The `obfuscateSensitiveData` pattern in the engine is a good practice that should be maintained.
- **Evidence**: `packages/sf-core/src/lib/auth/index.js`, `packages/engine/src/index.js` (obfuscateSensitiveData)

### DATA-Q2: Data Residency and Sovereignty ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY, but surface-flag downgrade applies. `has_persistent_data_store` is `false` — the system holds no data subject to residency constraints. The MCP tools query AWS APIs in user-specified regions but do not store or transmit the results to other regions.
- **Finding**: The MCP tools accept `region` and `profile` parameters, querying AWS in the user-specified region. No cross-region data transfer occurs — results are returned to the local MCP client.
- **Implication**: Data residency is a consumer responsibility. The MCP server does not move data across regions.
- **Recommendation**: No action needed.
- **Evidence**: `packages/mcp/src/tools-definition.js` (regionParam, profileParam)

### DATA-Q6: PII Redaction in Logs

- **Severity**: INFO
- **Finding**: `has_logging_of_user_data` is `false`. The MCP server logs only session IDs (`console.error(\`Client connected: ${transport.sessionId}\`)`). The sf-core router telemetry includes machine ID (hashed MAC address), OS, architecture — no PII. The engine's `obfuscateSensitiveData` masks sensitive configuration before state persistence.
- **Implication**: No PII-in-logs risk exists. The system logs diagnostic data only.
- **Recommendation**: No action needed.
- **Evidence**: `packages/mcp/src/server.js`, `packages/sf-core/src/lib/router.js` (getMachineId — hashed MAC)

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No formal data quality metrics exist. The MCP tools query live AWS APIs, so data freshness is real-time. The confirmation handler provides cost awareness but not data quality scoring.
- **Implication**: Data quality is determined by AWS API response freshness. No additional data quality layer is needed for a CLI tool.
- **Recommendation**: No action needed.
- **Evidence**: `packages/mcp/src/tools-definition.js`

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Field names across the codebase use descriptive camelCase conventions: `functionNames`, `serviceName`, `startTime`, `endTime`, `logGroupIdentifiers`, `serviceWideAnalysis`, `alarmNamePrefix`, `confirmationToken`. The engine types use clear names: `timeCreated`, `timeLastUpdated`, `timeLastDeployed`, `isDeployed`. No legacy abbreviations or cryptic codes found.
- **Implication**: Agent LLMs can reason about field names without a data dictionary.
- **Recommendation**: Maintain current naming conventions.
- **Evidence**: `packages/mcp/src/tools-definition.js`, `packages/engine/src/types.js`

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: The `docs/` directory contains `engine-types.md` and documentation for `sf` and `scf` products. The MCP server includes a `docs` tool that provides access to Serverless Framework documentation. The `packages/engine/src/types.js` file serves as a comprehensive type catalog with Zod schema definitions and JSDoc descriptions.
- **Implication**: The docs tool enables agents to self-service documentation, which is a strong discoverability feature.
- **Recommendation**: Consider adding a schema export tool that returns the Zod schema definitions for all MCP tools in a machine-readable format.
- **Evidence**: `docs/`, `packages/mcp/src/tools/docs.js`, `packages/engine/src/types.js`

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: The sf-core router sends product analytics events via `instanceUsageTrackingClient` and `platformEventClient` to the Serverless Platform. The analytics include: action name, service unique ID, runner type, CLI options, error information, and notification tracking. The MCP server has an analytics wrapper (`wrapServerWithAnalytics`) that tracks tool execution events.
- **Implication**: Product analytics exist but are not business-outcome metrics in the traditional sense. The MCP analytics track which tools are used, useful for understanding agent behavior patterns.
- **Recommendation**: Enhance MCP analytics to track tool success/failure rates and response times for agent-experience monitoring.
- **Evidence**: `packages/sf-core/src/lib/router.js` (createUsageEvent, createAnalysisEvent), `packages/mcp/src/utils/analytics-utils.js`

### ENG-Q1: Infrastructure Governance

- **Severity**: INFO
- **Finding**: This monorepo IS an IaC tool — it does not have its own deployment infrastructure defined as IaC. The system's "infrastructure" is the npm package publishing pipeline and GitHub Actions CI/CD, which are defined as code in `.github/workflows/`. PR reviews are enforced via GitHub branch protection on `main`. Dependabot is configured for automated dependency updates across npm, Go, Maven, and GitHub Actions.
- **Implication**: Infrastructure governance is applied to the build/release pipeline, not to deployed infrastructure (the repo doesn't deploy itself).
- **Recommendation**: No action needed. The CI/CD configuration is well-governed.
- **Evidence**: `.github/workflows/release-framework.yml`, `.github/dependabot.yml`

### ENG-Q3: Rollback Capability

- **Severity**: INFO
- **Finding**: The release pipeline follows a canary → stable → npm publish flow. The `release-framework.yml` workflow uploads tarballs to S3 via CloudFront, tags versions, and publishes to npm. Rollback can be achieved by reverting the git tag and re-running the pipeline, or by publishing a patch version. The CloudFront cache invalidation step ensures the latest version is served.
- **Implication**: Rollback requires a new release cycle rather than an instant revert, but this is standard for CLI tools distributed via npm.
- **Recommendation**: Consider maintaining a "known-good" tarball URL that can be quickly pointed to the previous version without a full release cycle.
- **Evidence**: `.github/workflows/release-framework.yml` (release-canary, release-stable, release-npm jobs)

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: The MCP server exposes a documented interface via the MCP protocol (SSE at GET `/sse`, POST `/messages`). Tools are defined with Zod schemas and comprehensive descriptions in `tools-definition.js`. The `packages/mcp/README.md` provides extensive documentation for all 16 tools including inputs, outputs, use cases, and credential setup. The CLI (`sf-core`) is a command-line interface, not an HTTP API. The system does NOT require direct database access, file-based exchange, or UI automation — agents interact via the MCP protocol.
- **Gap**: None — the MCP protocol provides a documented, machine-readable interface.
- **Recommendation**: No action needed. The MCP protocol is the agent integration surface.
- **Evidence**: `packages/mcp/src/server.js`, `packages/mcp/src/tools-definition.js`, `packages/mcp/README.md`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI/Swagger file exists. MCP tools use Zod schemas exposed via the MCP SDK protocol. No standalone spec file for external consumption.
- **Gap**: No static specification file for API documentation tooling, SDK generation, or contract testing outside the MCP protocol.
- **Recommendation**: Generate a standalone tool schema export (JSON) from the Zod definitions.
- **Evidence**: `packages/mcp/src/tools-definition.js`, `packages/mcp/README.md`

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: AWS credentials errors are well-structured via `aws-credentials-error-handler.js`. General tool errors are unstructured text. No consistent error code or retryable indicator in non-credential errors.
- **Gap**: Agents cannot reliably distinguish retriable from terminal errors.
- **Recommendation**: Wrap all MCP tool responses in a consistent error envelope.
- **Evidence**: `packages/mcp/src/lib/aws-credentials-error-handler.js`, `packages/serverless/lib/serverless-error.js`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: MCP tools are all read-only. No write endpoints exist in the MCP server.
- **Gap**: N/A for read-only scope.
- **Recommendation**: No action needed.
- **Evidence**: `packages/mcp/src/tools-definition.js`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: MCP tools return structured JSON via the MCP protocol `content` array. Response format follows MCP SDK standards.
- **Gap**: None.
- **Recommendation**: Consider returning structured JSON objects within MCP text content.
- **Evidence**: `packages/mcp/src/tools-definition.js`

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `orchestrator`, agent_scope: `read-only`.
- **Trigger**: Service has operations >30s OR long-running workflows
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: Trigger condition met: archetype is `orchestrator`, which is explicitly listed in the trigger ("Service has state changes (stateful-crud, orchestrator)"). The Serverless Framework CLI orchestrates state changes (deploy, remove, rollback) across 20+ AWS services via CloudFormation. The sf-core router emits product analytics events to the Serverless Platform. The MCP analytics wrapper tracks tool execution events. However, there are no webhook, SNS, EventBridge, or streaming event emission endpoints for external consumers to subscribe to state change notifications.
- **Gap**: No event emission mechanism for external consumers to subscribe to deployment lifecycle or infrastructure state change events.
- **Recommendation**: Consider adding EventBridge or webhook support for deployment lifecycle events (deploy-started, deploy-completed, deploy-failed, rollback-initiated) to enable event-driven agent workflows.
- **Evidence**: `packages/sf-core/src/lib/router.js` (platformEventClient, instanceUsageTrackingClient), `packages/mcp/src/utils/analytics-utils.js`, `packages/mcp/src/tools-definition.js`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limits documented or headers returned by MCP server.
- **Gap**: Agents have no signal to self-throttle.
- **Recommendation**: Document capacity expectations.
- **Evidence**: `packages/mcp/src/server.js`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: The sf-core Authentication class supports machine identity via: (1) License Keys (Access Key V2) for CI/CD environments, (2) Access Keys (V1) via Serverless Dashboard OAuth, (3) SSM-stored license keys (`/serverless-framework/license-key`), (4) AWS credential chain (IAM roles, profiles, SSO) for MCP tools. The `callerIdentity` endpoint validates keys and returns orgId, orgName, userId, and userName — all attributable in audit logs. For the MCP server specifically, machine identity is the AWS IAM identity used for API calls, which is fully attributable via CloudTrail.
- **Gap**: None for the current architecture. The MCP server delegates auth to AWS IAM, which provides machine identity and attribution.
- **Recommendation**: No action needed. AWS IAM + CloudTrail provide machine identity and attribution.
- **Evidence**: `packages/sf-core/src/lib/auth/index.js`, `packages/mcp/src/tools-definition.js`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: INFO
- **Finding**: The MCP tools accept `profile` and `region` parameters, allowing scoped-down AWS credentials. Each MCP tool requires specific AWS API permissions (e.g., `aws-lambda-info` needs `lambda:GetFunction`, `aws-iam-info` needs `iam:GetRole`). The system supports scoped permissions at the AWS IAM layer — an agent can use an IAM role with read-only access to specific services.
- **Gap**: The MCP server does not enforce permission scoping itself — it delegates to AWS IAM. There is no built-in mechanism to restrict which MCP tools an agent can call.
- **Recommendation**: For enterprise use, consider implementing tool-level access controls in the MCP server (e.g., allowlist of tools per client session).
- **Evidence**: `packages/mcp/src/tools-definition.js` (profile/region params), `packages/mcp/README.md`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: INFO
- **Finding**: The MCP tools are all read-only by design. Action-level authorization is enforced by the AWS IAM policies attached to the credentials used. An agent using IAM credentials with only `lambda:GetFunction` permission cannot delete Lambda functions even if such a tool existed. The MCP server does not expose write operations.
- **Gap**: The MCP server has no built-in action-level authorization — it relies entirely on AWS IAM.
- **Recommendation**: Maintain the read-only tool design. If write tools are added, enforce action-level checks before AWS SDK calls.
- **Evidence**: `packages/mcp/src/tools-definition.js`, `packages/mcp/src/tools/aws/*.js`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: No on-behalf-of flow in the MCP server. AWS credentials are used directly from the host environment.
- **Gap**: N/A for local CLI tool architecture.
- **Recommendation**: For enterprise deployments, consider supporting agent-specific AWS profiles.
- **Evidence**: `packages/sf-core/src/lib/auth/index.js`, `packages/mcp/src/tools-definition.js`

#### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: Credentials managed via SSM Parameter Store, `.serverlessrc`, environment variables, and AWS credential chain. No hardcoded credentials. Engine obfuscates sensitive data before persistence.
- **Gap**: None.
- **Recommendation**: No action needed.
- **Evidence**: `packages/sf-core/src/lib/auth/index.js`, `packages/engine/src/index.js`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — Surface-flag downgrade: MCP server is a local CLI tool. Audit logging of agent-invoked read operations is handled by AWS CloudTrail.
- **Finding**: No application-level audit logging. Telemetry events sent to Serverless Platform for product analytics.
- **Gap**: No MCP-level audit trail. AWS CloudTrail is the audit mechanism.
- **Recommendation**: Ensure CloudTrail is enabled in all regions.
- **Evidence**: `packages/sf-core/src/lib/router.js`, `packages/mcp/src/utils/analytics-utils.js`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: The sf-core Authentication class supports `unAuthenticate()` to remove user sessions and license keys from `.serverlessrc`. AWS IAM roles/profiles used by the MCP server can be suspended via standard AWS IAM controls. However, the MCP server itself has no built-in mechanism to suspend or revoke an individual agent's identity or session — there is no session revocation endpoint, no agent identity registry, and no way to block a specific MCP client without restarting the server process. `has_auth_surface` is `true` — the system has authentication enforcement points, so the base severity of RISK-SAFETY applies (no surface-flag downgrade condition is met).
- **Gap**: No application-level agent identity suspension. Suspension relies entirely on external AWS IAM controls at the credential level, not the agent session level.
- **Recommendation**: Implement session-level identity management in the MCP server with an admin mechanism to revoke individual sessions by sessionId.
- **Evidence**: `packages/sf-core/src/lib/auth/index.js`, `packages/mcp/src/server.js` (activeTransports map)

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — Surface-flag calibration: MCP tools are read-only, no write path needs compensation.
- **Finding**: Framework rollback plugin exists. Engine manages state with Zod validation. CloudFormation provides built-in rollback.
- **Gap**: N/A for read-only scope.
- **Recommendation**: No action needed.
- **Evidence**: `packages/serverless/lib/plugins/rollback.js`, `packages/engine/src/index.js`

#### STATE-Q2: Queryable Current State
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `orchestrator`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Trigger requires agent_scope to be write-enabled AND service to have persistent state. agent_scope is `read-only`, so the trigger condition is not met.
- **Trigger**: agent_scope is write-enabled AND service has persistent state
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: No circuit breakers, retry logic, or timeout configuration in MCP server's AWS SDK calls.
- **Gap**: Cascading failure risk from slow/throttled AWS API responses.
- **Recommendation**: Add timeout configuration and circuit breaker patterns to MCP AWS SDK calls.
- **Evidence**: `packages/mcp/src/lib/aws/*.js`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No rate limiting middleware in the MCP Express server.
- **Gap**: Unlimited tool calls at machine speed possible.
- **Recommendation**: Add `express-rate-limit` middleware.
- **Evidence**: `packages/mcp/src/server.js`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No transaction limits. Confirmation handler provides cost awareness for CloudWatch queries.
- **Gap**: N/A for read-only scope.
- **Recommendation**: No action needed.
- **Evidence**: `packages/mcp/src/lib/confirmation-handler.js`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `orchestrator`, agent_scope: `read-only`. Priority P2, not on critical path.
- **Trigger**: Service is P0 priority OR is on the critical path
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Trigger requires agent_scope to be write-enabled. agent_scope is `read-only`, so the trigger condition is not met.
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Trigger requires agent_scope to be write-enabled. agent_scope is `read-only`, so the trigger condition is not met. Note: The MCP server does implement a confirmation handler pattern (`confirmation-handler.js`) for cost-sensitive operations, which demonstrates capability for approval workflows.
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: The CI pipeline uses separate environments (dev/prod) with dedicated license keys. Integration tests deploy to ephemeral test stages. The MCP server can be started locally. However, there is no formal sandbox environment for testing agent interactions with mock AWS resources, and no mock/stub mode exists. `has_http_rpc_surface` is `true`, so the surface-flag downgrade condition (requires both `has_http_rpc_surface=false` AND `has_persistent_data_store=false`) is not met — base severity of RISK-QUALITY applies.
- **Gap**: No mock/stub mode for MCP server. No formal sandbox for agent testing.
- **Recommendation**: Add a mock/stub mode for the MCP server that returns synthetic AWS data for agent testing without real AWS credentials.
- **Evidence**: `.github/workflows/ci-framework.yml`, `packages/mcp/package.json`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO
- **Finding**: Stage A scope gate: System handles credentials in sf-core auth. MCP server returns AWS resource metadata, not PII. Engine obfuscates sensitive data before state persistence.
- **Gap**: None — appropriate for CLI tool that delegates data handling to AWS.
- **Recommendation**: No action needed.
- **Evidence**: `packages/sf-core/src/lib/auth/index.js`, `packages/engine/src/index.js`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — Surface-flag downgrade: `has_persistent_data_store` is `false`. No cross-region data transfer.
- **Finding**: MCP tools query AWS in user-specified regions. No data storage or cross-region transfer.
- **Gap**: None.
- **Recommendation**: No action needed.
- **Evidence**: `packages/mcp/src/tools-definition.js`

#### DATA-Q3: Selective Query Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `orchestrator`, agent_scope: `read-only`.
- **Trigger**: Service has list/query endpoints with potentially unbounded results
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q4: System of Record Designations
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `orchestrator`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `orchestrator`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q6: PII Redaction in Logs
- **Severity**: INFO
- **Finding**: `has_logging_of_user_data` is `false`. Only diagnostic data logged. Engine obfuscates sensitive configuration.
- **Gap**: None.
- **Recommendation**: No action needed.
- **Evidence**: `packages/mcp/src/server.js`, `packages/sf-core/src/lib/router.js`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No formal data quality metrics. MCP tools query live AWS APIs for real-time data.
- **Gap**: None for a CLI tool.
- **Recommendation**: No action needed.
- **Evidence**: `packages/mcp/src/tools-definition.js`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: MCP server version hardcoded as `1.0.0`. No schema versioning. No breaking change detection in CI.
- **Gap**: Agent tool bindings may break silently.
- **Recommendation**: Add schema versioning and CI-based breaking change detection.
- **Evidence**: `packages/mcp/src/server.js`, `packages/mcp/src/tools-definition.js`, `VERSIONING.md`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Descriptive camelCase conventions throughout. No legacy abbreviations.
- **Gap**: None.
- **Recommendation**: Maintain current naming conventions.
- **Evidence**: `packages/mcp/src/tools-definition.js`, `packages/engine/src/types.js`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: Docs directory, MCP docs tool, comprehensive Zod schema definitions with JSDoc.
- **Gap**: No formal data catalog, but not expected for a CLI tool.
- **Recommendation**: Consider schema export tool for machine-readable format.
- **Evidence**: `docs/`, `packages/mcp/src/tools/docs.js`, `packages/engine/src/types.js`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: MCP server uses `console.error`. No structured JSON logging, no correlation IDs, no tracing.
- **Gap**: Cannot debug agent-initiated failures without manual log correlation.
- **Recommendation**: Replace `console.error` with structured JSON logging and request ID propagation.
- **Evidence**: `packages/mcp/src/server.js`, `packages/util/src/logger/`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: No self-monitoring or alerting for the MCP server process.
- **Gap**: No automated alert for MCP server failures.
- **Recommendation**: Add `/health` endpoint and basic metrics emission.
- **Evidence**: `packages/mcp/src/server.js`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: Product analytics via Serverless Platform. MCP analytics wrapper tracks tool executions.
- **Gap**: No business-outcome metrics in traditional sense.
- **Recommendation**: Enhance MCP analytics with success/failure rates and latency.
- **Evidence**: `packages/sf-core/src/lib/router.js`, `packages/mcp/src/utils/analytics-utils.js`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance
- **Severity**: INFO
- **Finding**: This monorepo IS an IaC tool. CI/CD defined as code in `.github/workflows/`. Dependabot configured. PR reviews enforced.
- **Gap**: None — appropriate for CLI tool distribution.
- **Recommendation**: No action needed.
- **Evidence**: `.github/workflows/`, `.github/dependabot.yml`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: CI includes lint, unit tests, integration tests, cross-platform matrix. No API contract testing for MCP tool schemas.
- **Gap**: MCP tool schema changes not caught before release.
- **Recommendation**: Add schema comparison CI step.
- **Evidence**: `.github/workflows/ci-framework.yml`, `packages/mcp/tests/`

#### ENG-Q3: Rollback Capability
- **Severity**: INFO
- **Finding**: Canary → stable → npm publish flow. Rollback via new release cycle.
- **Gap**: No instant revert capability.
- **Recommendation**: Maintain known-good tarball URL for quick rollback.
- **Evidence**: `.github/workflows/release-framework.yml`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: 5 of 16 MCP tools have dedicated tests. 11 tools lack unit test coverage.
- **Gap**: Insufficient test coverage for agent-facing MCP tools.
- **Recommendation**: Add unit tests for untested MCP tools.
- **Evidence**: `packages/mcp/tests/`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. No persistent data stores owned by the system.
- **Trigger**: Service has persistent data stores
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| packages/mcp/src/server.js | API-Q1, API-Q5, API-Q8, AUTH-Q6, AUTH-Q7, STATE-Q5, OBS-Q1, OBS-Q2, ENG-Q1 |
| packages/mcp/src/stdio-server.js | API-Q1, DISC-Q1 |
| packages/mcp/src/tools-definition.js | API-Q1, API-Q2, API-Q3, API-Q4, API-Q5, API-Q7, AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4, DATA-Q2, DATA-Q7, DISC-Q1, DISC-Q2 |
| packages/mcp/src/lib/aws-credentials-error-handler.js | API-Q3, STATE-Q4 |
| packages/mcp/src/lib/confirmation-handler.js | STATE-Q4, STATE-Q6, HITL-Q2, API-Q8 |
| packages/mcp/src/lib/parameter-validator.js | API-Q3 |
| packages/mcp/src/utils/analytics-utils.js | API-Q7, AUTH-Q6, OBS-Q3 |
| packages/mcp/src/tools/aws/*.js | API-Q5, AUTH-Q3, STATE-Q4 |
| packages/sf-core/src/lib/auth/index.js | AUTH-Q1, AUTH-Q4, AUTH-Q5, AUTH-Q7, DATA-Q1 |
| packages/sf-core/src/lib/router.js | API-Q7, AUTH-Q6, OBS-Q3, DATA-Q6 |
| packages/engine/src/index.js | STATE-Q1, DATA-Q1, AUTH-Q5 |
| packages/engine/src/types.js | DISC-Q2, DISC-Q3 |
| packages/serverless/lib/serverless-error.js | API-Q3 |
| packages/serverless/lib/plugins/rollback.js | STATE-Q1 |
| packages/serverless/lib/config-schema.js | DISC-Q1 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| .github/workflows/ci-framework.yml | ENG-Q2, ENG-Q4, HITL-Q3 |
| .github/workflows/ci-engine.yml | ENG-Q2 |
| .github/workflows/release-framework.yml | ENG-Q3, HITL-Q3 |
| .github/dependabot.yml | ENG-Q1 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| package.json (root) | ENG-Q1 |
| packages/mcp/package.json | API-Q1, HITL-Q3 |
| packages/sf-core/package.json | AUTH-Q1 |
| packages/engine/package.json | STATE-Q4 |
| packages/serverless/package.json | DISC-Q1 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| VERSIONING.md | DISC-Q1 |
| TESTING.md | ENG-Q4 |
| packages/mcp/README.md | API-Q1, API-Q2, AUTH-Q2 |

### Test Files
| File | Questions Referenced |
|------|---------------------|
| packages/mcp/tests/*.test.js | ENG-Q4 |
| packages/engine/test/*.test.js | ENG-Q4 |
| packages/sf-core/tests/ | ENG-Q4 |

### Documentation
| File | Questions Referenced |
|------|---------------------|
| docs/ | DISC-Q3 |
| packages/mcp/src/tools/docs.js | DISC-Q3 |
