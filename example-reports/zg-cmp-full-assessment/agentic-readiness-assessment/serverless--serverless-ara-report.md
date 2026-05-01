# Agentic Readiness Assessment Report

**Target**: serverless/serverless (monorepo)
**Date**: 2026-04-29
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: monorepo
**Service Archetype**: stateless-utility (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: javascript, serverless, iac, cli
**Context**: Serverless Framework CLI for building and deploying serverless apps.
**Archetype Justification**: The MCP server (primary agent-facing surface) has no database connections, no persistent state, and all tools perform read-only queries against AWS APIs. It is classified as stateless-utility.

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 2 | **RISK-SAFETY**: 9 | **RISK-QUALITY**: 11 | **INFOs**: 12

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 2 |
| RISK-SAFETY | 9 |
| RISK-QUALITY | 11 |
| INFO | 12 |
| N/A | 0 |
| Not Evaluated (extended) | 9 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 10 (API-Q5, API-Q6, API-Q8, STATE-Q4, DATA-Q3, DATA-Q7, DISC-Q2, DISC-Q3, OBS-Q3, ENG-Q4)
**Extended Questions Not Triggered**: 9 (API-Q7, STATE-Q2, STATE-Q3, STATE-Q7, HITL-Q1, HITL-Q2, DATA-Q4, DATA-Q5, ENG-Q5)
**Questions N/A (repo_type: monorepo)**: 0
**Service Archetype**: stateless-utility (auto-detected)

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: The MCP SSE server (`packages/mcp/src/server.js`) has **no authentication mechanism**. The Express server exposes `/sse` and `/messages` endpoints without any API key validation, OAuth2 client credentials flow, mTLS, or any other form of caller authentication. Any process on the network that can reach the port can connect as an SSE client and invoke any registered tool. The `activeTransports` map tracks connections by `sessionId`, but `sessionId` is an opaque transport identifier — not an authenticated principal. The stdio server (`packages/mcp/src/stdio-server.js`) similarly has no authentication layer.
- **Gap**: No machine identity authentication for agents connecting to the MCP server. The server cannot distinguish which agent made a call, and cannot attribute actions to a specific principal in audit logs.
- **Remediation**:
  - **Immediate**: Add API key or bearer token authentication middleware to the Express SSE server. Validate an `Authorization` header before establishing SSE connections on `/sse` and accepting messages on `/messages`. Map each API key to a named principal for audit attribution.
  - **Target State**: Every MCP client connection is authenticated with a unique machine identity. Each tool invocation is attributed to the authenticated principal in logs.
  - **Estimated Effort**: Medium (1–2 weeks)
  - **Dependencies**: AUTH-Q6 (audit logging) — once identity exists, log it.
- **Evidence**: `packages/mcp/src/server.js` (lines 33–54: no auth middleware), `packages/mcp/src/stdio-server.js`

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: The MCP `aws-lambda-info` tool returns Lambda function configuration including **environment variables**, which commonly contain secrets (database passwords, API keys, third-party tokens). The tool response passes raw AWS API data without field-level classification or redaction. The `obfuscateSensitiveData` function exists in `packages/sf-core/src/utils/general/index.js` (obfuscates keys like `environment`) but is **not used** in any MCP tool implementation. Similarly, `aws-iam-info` returns full IAM policy documents, and `aws-s3-info` returns bucket policies — all potentially containing sensitive resource ARNs and account IDs.
- **Gap**: No sensitive data classification or field-level redaction in MCP tool responses. An agent can retrieve Lambda environment variables containing secrets without any filtering or access controls beyond the underlying AWS IAM permissions.
- **Remediation**:
  - **Immediate**: Apply the existing `obfuscateSensitiveData` function (or a similar redaction layer) to MCP tool responses before returning them to agents. At minimum, redact `environment` variables from Lambda configurations, and flag fields containing account IDs, ARNs, and policy documents.
  - **Target State**: MCP tool responses classify sensitive fields and redact secrets by default. An optional `includeSensitive=true` parameter with elevated authorization allows retrieval of unredacted data when needed.
  - **Estimated Effort**: Medium (1–2 weeks)
  - **Dependencies**: AUTH-Q1 (identity) — redaction rules should be tied to agent permissions.
- **Evidence**: `packages/mcp/src/tools-definition.js` (Lambda info tool), `packages/sf-core/src/utils/general/index.js:255` (obfuscateSensitiveData — not used by MCP), `packages/mcp/src/tools/aws/lambda-info.js`

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The MCP server has no per-agent permission model. All MCP tool registrations in `packages/mcp/src/tools-definition.js` are available to every connected client. The `profile` and `region` parameters delegate AWS-level authorization to IAM, but the MCP server itself cannot restrict which tools or AWS accounts an agent can access. A connected agent has access to all 16 tools regardless of its intended scope.
- **Gap**: No mechanism to grant an agent read-only access to specific resources or tools without granting access to the full tool surface.
- **Compensating Controls**:
  - Use separate AWS IAM profiles with least-privilege policies for each agent use case.
  - Run separate MCP server instances with different tool registrations for different agent scopes.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement tool-level access control lists (ACLs) in the MCP server, configurable per API key or identity.
- **Evidence**: `packages/mcp/src/tools-definition.js` (all tools registered unconditionally)

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: All MCP tools are currently read-only (info, list, logs, docs). However, the MCP server has no mechanism to enforce action-level authorization. If write tools are added in the future, there is no framework to restrict specific agents to read-only operations. The tool registration in `tools-definition.js` does not support permission annotations.
- **Gap**: No action-level authorization framework within the MCP server. Cannot enforce "this agent can call `list-resources` but not `deployment-history`" at the MCP layer.
- **Compensating Controls**:
  - Current mitigation: all tools are read-only, reducing the blast radius.
  - Underlying AWS IAM enforces action-level authorization at the cloud provider layer.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add tool-level permission annotations and enforcement middleware before adding any write-capable tools.
- **Evidence**: `packages/mcp/src/tools-definition.js`

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The MCP server logs client connections and disconnections via `console.error` with `sessionId` in `server.js`. The `analytics-utils.js` wrapper sends analytics events with `toolName` after each tool execution. However: (1) no authenticated principal is logged — only an opaque `sessionId`; (2) logs are written to stderr with no immutable storage; (3) analytics events do not include the caller identity, parameters, or response metadata; (4) no CloudTrail or equivalent audit trail for MCP tool invocations.
- **Gap**: Tool invocations are not attributed to an authenticated principal. Logs are not immutable or tamper-evident. Cannot determine which agent called which tool with which parameters.
- **Compensating Controls**:
  - AWS CloudTrail captures the underlying AWS API calls made by the MCP tools (attributed to the AWS credentials used).
  - Redirect MCP server stderr to a centralized, append-only log system.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement structured audit logging for every tool invocation, including authenticated principal, tool name, parameters, and timestamp. Store in an immutable log system.
- **Evidence**: `packages/mcp/src/server.js` (console.error logging), `packages/mcp/src/utils/analytics-utils.js` (tool name only)

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The MCP server tracks active connections in the `activeTransports` map keyed by `sessionId`. The `stop()` function in `server.js` closes all transports, and individual transports are cleaned up on disconnect. However, there is no mechanism to suspend or revoke a specific agent's access while the server is running. There is no API key revocation, no blocklist, and no way to terminate a specific session by identity.
- **Gap**: Cannot isolate or suspend a misbehaving agent without restarting the entire MCP server, which disconnects all agents.
- **Compensating Controls**:
  - Restart the MCP server to disconnect all agents (blunt but effective).
  - Revoke the underlying AWS credentials used by a specific agent to stop its AWS API access.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement session termination by identity — an admin endpoint or control plane that can disconnect a specific agent by API key or principal.
- **Evidence**: `packages/mcp/src/server.js` (activeTransports map, stop() function)

#### STATE-Q1: Compensation and Rollback ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The MCP tools are exclusively read-only operations (list, info, logs, docs, search). There are no multi-step write workflows to compensate or roll back. The underlying Serverless Framework CLI has deploy/remove operations with CloudFormation stack management, but these are not exposed through the MCP tools.
- **Gap**: No compensation or rollback capability exists in the MCP server, but this is mitigated by the read-only nature of all current tools.
- **Compensating Controls**:
  - All MCP tools are read-only — no state changes to compensate.
  - If write tools are added, leverage CloudFormation's built-in rollback for deployment operations.
- **Remediation Timeline**: Address before adding any write-capable MCP tools.
- **Recommendation**: Before exposing any write operations through MCP, implement compensation patterns (e.g., undo endpoints, saga coordination).
- **Evidence**: `packages/mcp/src/tools-definition.js` (all read-only tools)

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The MCP tools call AWS APIs directly via AWS SDK v3 clients. Retry logic exists in `packages/serverless/lib/aws/request-retry.js` using exponential backoff with jitter (base 5000ms, max retries configurable). The `@smithy/util-retry` dependency is present. However, there are **no circuit breaker patterns** in the MCP tools or their underlying AWS client calls. If an AWS API is degraded, the MCP server will continue sending requests, accumulating failures and consuming resources.
- **Gap**: No circuit breaker implementation. Retry logic exists but without circuit breaker protection, a degraded AWS API can cause cascading failures in the MCP server.
- **Compensating Controls**:
  - AWS SDK v3 has built-in adaptive retry with `AWS_MAX_ATTEMPTS` configuration.
  - Individual tool calls have timeout bounds set by the AWS SDK defaults.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add circuit breaker middleware (e.g., `opossum` or custom implementation) around AWS API calls in MCP tools to fail fast when downstream services are degraded.
- **Evidence**: `packages/serverless/lib/aws/request-retry.js`, `packages/mcp/package.json` (no circuit breaker dependency)

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The MCP SSE server (`packages/mcp/src/server.js`) is a plain Express application with **no rate limiting middleware**. There is no `express-rate-limit`, no API Gateway throttling, no WAF rules, and no connection limits. An agent can send unlimited tool invocation requests at machine speed. The confirmation handler (`confirmation-handler.js`) limits costly CloudWatch Logs Insights queries by requiring confirmation tokens for extended timeframes, but this is a cost protection mechanism, not rate limiting.
- **Gap**: No rate limiting on the MCP server. A runaway agent loop could overwhelm the server and the underlying AWS APIs.
- **Compensating Controls**:
  - AWS API throttling limits provide a downstream backstop.
  - The MCP server runs locally (default usage), limiting exposure to local processes.
- **Remediation Timeline**: 30 days
- **Recommendation**: Add `express-rate-limit` middleware to the SSE server with configurable per-client rate limits. Consider per-tool rate limits for expensive operations (CloudWatch queries).
- **Evidence**: `packages/mcp/src/server.js` (no rate limiting middleware), `packages/mcp/package.json` (no rate limiting dependency)

#### DATA-Q2: Data Residency and Sovereignty ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: MCP tools accept a `region` parameter allowing agents to query AWS resources in any region. Data returned from AWS APIs (Lambda configurations, logs, IAM policies) flows through the MCP server to the agent and potentially to an LLM. There are no controls preventing an agent from requesting data from regulated regions or transmitting it cross-border to an LLM provider.
- **Gap**: No data residency controls in the MCP server. An agent could retrieve data from an EU region and transmit it to an LLM endpoint in the US.
- **Compensating Controls**:
  - AWS IAM policies on the underlying credentials can restrict region access.
  - Configure the MCP server with an allowlist of permitted regions.
- **Remediation Timeline**: 60 days
- **Recommendation**: Add a configurable region allowlist to the MCP server. Validate the `region` parameter against the allowlist before executing tools. Document data residency implications in the README.
- **Evidence**: `packages/mcp/src/tools-definition.js` (regionParam accepts any string), `packages/mcp/README.md`

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The MCP server logs to stderr using `console.error`. The `confirmation-handler.js` logs error details including log group names. Tool responses may contain PII from AWS resources (IAM user names, email addresses in policies, account IDs). The `obfuscateSensitiveData` function exists in `packages/sf-core/src/utils/general/index.js` but is not applied to MCP server logging or tool responses. No PII detection or masking is applied to logs or tool response data.
- **Gap**: No PII redaction in MCP server logs or tool responses. If an agent sends tool responses to an LLM, PII from AWS resources could be included in prompts.
- **Compensating Controls**:
  - Limit AWS IAM permissions to exclude access to resources containing PII.
  - Run the MCP server in an isolated environment where logs are not persisted.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Apply PII detection and masking to MCP server logs. Consider redacting account IDs, user names, and email addresses from tool responses before returning to agents.
- **Evidence**: `packages/mcp/src/server.js` (console.error), `packages/sf-core/src/utils/general/index.js:255` (obfuscateSensitiveData — unused by MCP)

### RISK-QUALITY — Address as Capacity Allows

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The MCP tools handle errors via `aws-credentials-error-handler.js`, which maps AWS credential error patterns to user-friendly text messages. Error responses are returned as plain text strings in the MCP `content` array — not structured objects with error codes, error categories, or retryable booleans. Parameter validation errors from `parameter-validator.js` throw JavaScript Error objects with descriptive messages.
- **Gap**: Error responses are text-based, not structured. An agent cannot programmatically distinguish a retryable timeout from a terminal permission denied error.
- **Compensating Controls**:
  - Error messages contain keywords (e.g., "expired", "Access Denied") that an LLM-based agent can interpret.
  - The MCP protocol's `isError` flag on tool results provides a binary error signal.
- **Remediation Timeline**: 30 days
- **Recommendation**: Return structured error objects with `errorCode`, `errorCategory` (credential, permission, throttling, validation, internal), and `retryable` boolean alongside the human-readable message.
- **Evidence**: `packages/mcp/src/lib/aws-credentials-error-handler.js`, `packages/mcp/src/lib/parameter-validator.js`

#### API-Q6: Asynchronous Operation Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: CloudWatch Logs Insights queries (`aws-logs-search`, `aws-errors-info`) can take 30+ seconds for large log groups. These operations are executed synchronously — the MCP tool handler awaits the AWS API response. There is no job submission, polling endpoint, or webhook callback pattern. The confirmation handler (`confirmation-handler.js`) provides a confirmation flow for extended timeframes but not an async execution pattern.
- **Gap**: Long-running CloudWatch queries may exceed agent timeout limits. No async pattern for operations that can take >30 seconds.
- **Compensating Controls**:
  - The confirmation handler limits query scope (3-hour default timeframe) to reduce query duration.
  - Log group size validation skips confirmation for groups <1GB.
- **Remediation Timeline**: 60 days
- **Recommendation**: Implement a job-based async pattern for long-running queries: submit query → return job ID → poll for results.
- **Evidence**: `packages/mcp/src/lib/confirmation-handler.js`, `packages/mcp/src/tools/aws/aws-logs-search.js`

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The MCP server can be started locally via `npm start` (port 3001) or `npm start:stdio`. Unit tests exist in `packages/mcp/tests/` with mocked AWS responses. E2E tests exist in `packages/mcp/tests/e2e/`. However, there is no formal sandbox or staging environment with production-equivalent data shape. The MCP tests use mocked data, not realistic AWS account data. No Docker Compose for local testing. No seed data scripts.
- **Gap**: No staging environment where agents can be tested against realistic (but safe) AWS data. Testing against production AWS accounts is the only option.
- **Compensating Controls**:
  - Use a dedicated sandbox AWS account with non-production data for agent testing.
  - MCP unit tests with mocked responses provide a safe testing baseline.
- **Remediation Timeline**: 60 days
- **Recommendation**: Create a Docker Compose setup with LocalStack or similar AWS mock service for local agent testing. Alternatively, document a recommended sandbox AWS account configuration.
- **Evidence**: `packages/mcp/package.json` (start scripts), `packages/mcp/tests/` (unit tests), `packages/mcp/tests/e2e/` (e2e tests)

#### DATA-Q3: Selective Query Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: MCP log tools (`aws-logs-search`, `aws-logs-tail`) accept a `limit` parameter (max 100). The `aws-errors-info` tool has `maxResults` (max 100). Time range filtering is supported on all tools with `startTime`/`endTime`. However, resource listing tools (`list-resources`, `aws-lambda-info`) return all resources without pagination. There is no cursor-based pagination for large result sets.
- **Gap**: Resource listing tools may return large unbounded result sets for AWS accounts with many resources. No cursor-based pagination.
- **Compensating Controls**:
  - Log tools have hard limits (100 events max).
  - Time range parameters limit the data window.
- **Remediation Timeline**: 30 days
- **Recommendation**: Add pagination support (cursor-based) for resource listing tools. Add configurable `maxResults` parameters where missing.
- **Evidence**: `packages/mcp/src/tools-definition.js` (limit parameters on log tools, no pagination on resource tools)

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: MCP tool schemas are defined using Zod in `packages/mcp/src/tools-definition.js`. The MCP server version is hardcoded as `1.0.0` in both `server.js` and `stdio-server.js`. The `VERSIONING.md` documents SemVer practices for the framework CLI, but there is no version tracking specific to the MCP tool interface. No breaking change detection in CI for MCP tool schemas. No consumer-driven contract tests. No OpenAPI diff or schema comparison tools in the CI pipeline.
- **Gap**: MCP tool schemas can change without detection. No breaking change detection for the agent integration surface. Agent tool bindings may break silently.
- **Compensating Controls**:
  - Zod schemas provide compile-time validation of tool parameters.
  - The MCP protocol's ListTools capability allows agents to discover current tool schemas at runtime.
- **Remediation Timeline**: 60 days
- **Recommendation**: Add schema snapshot tests that detect changes to tool definitions. Integrate into CI as a gate. Consider versioning the MCP tool interface independently from the framework version.
- **Evidence**: `packages/mcp/src/tools-definition.js`, `packages/mcp/src/server.js` (version: '1.0.0'), `VERSIONING.md`, `.github/workflows/ci-framework.yml` (no schema tests)

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The MCP server uses `console.error` for all logging — unstructured plain text to stderr. No JSON logging. No correlation IDs. No distributed tracing (no OpenTelemetry, no X-Ray). The `packages/util/src/logger/index.js` provides a rich logging framework with levels, progress tracking, and styling — but this is designed for CLI interactive output, not structured service logging. The MCP server does not use this logger.
- **Gap**: Cannot reconstruct what happened during an agent-initiated request. No trace ID propagation. No structured logs for automated analysis.
- **Compensating Controls**:
  - AWS CloudTrail traces the underlying AWS API calls.
  - MCP server stderr can be captured and parsed externally.
- **Remediation Timeline**: 30 days
- **Recommendation**: Replace `console.error` calls with a structured JSON logger. Add a request/correlation ID to each tool invocation. Consider OpenTelemetry instrumentation for distributed tracing.
- **Evidence**: `packages/mcp/src/server.js` (console.error), `packages/util/src/logger/index.js` (CLI logger, not used by MCP)

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No alerting is configured for the MCP server. No CloudWatch alarms, no PagerDuty/OpsGenie integration, no error rate or latency thresholds. The MCP server is designed to run locally as part of the CLI, not as a deployed service with monitoring. The analytics wrapper (`analytics-utils.js`) sends tool execution events but does not track error rates or latency.
- **Gap**: No automated alerting on MCP server health. If the server degrades, agents will fail without notification.
- **Compensating Controls**:
  - Local deployment model reduces blast radius — only the local user is affected.
  - Agent orchestration layer can detect tool failures and alert externally.
- **Remediation Timeline**: 60 days (if MCP server is deployed as a service)
- **Recommendation**: If the MCP server is deployed as a shared service, add health check endpoints, latency tracking, and alerting thresholds. For local use, this is lower priority.
- **Evidence**: `packages/mcp/src/server.js`, `packages/mcp/src/utils/analytics-utils.js`

#### ENG-Q1: Infrastructure Governance — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The release infrastructure (S3 tarball uploads, CloudFront cache invalidation) is defined only in CI scripts (`.github/workflows/release-framework.yml`), not in IaC. AWS credentials are configured via GitHub Actions OIDC role assumption (`arn:aws:iam::762003938904:role/GithubActionsDeploymentRole`), which is good practice. However, the S3 buckets, CloudFront distributions, and IAM roles themselves are not defined as IaC in this repository. No drift detection is configured.
- **Gap**: Release infrastructure is not defined as code in this repository. Changes to S3 buckets or CloudFront distributions are not subject to PR review in this codebase.
- **Compensating Controls**:
  - The release IaC may exist in a separate infrastructure repository.
  - GitHub Actions OIDC role assumption provides scoped, temporary credentials.
- **Remediation Timeline**: 60 days
- **Recommendation**: Either reference the IaC definitions for release infrastructure or add them to this repository. Enable drift detection.
- **Evidence**: `.github/workflows/release-framework.yml` (S3 upload, CloudFront invalidation)

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: CI/CD pipelines exist in `.github/workflows/ci-framework.yml` and `.github/workflows/ci-engine.yml` with linting, unit tests, and integration tests. The release pipeline runs cross-platform tests. However, there are **no API contract tests** for the MCP tool interface. No Pact tests. No OpenAPI schema validation. No schema comparison tools. Changes to MCP tool parameters could reach production without detection.
- **Gap**: No automated detection of breaking changes in the MCP tool interface. An agent relying on a specific tool parameter could break after a release.
- **Compensating Controls**:
  - MCP unit tests (`packages/mcp/tests/`) validate individual tool behavior.
  - Zod schemas provide parameter validation at runtime.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add MCP schema snapshot tests that fail when tool definitions change. Integrate Pact or similar consumer-driven contract testing for the MCP interface.
- **Evidence**: `.github/workflows/ci-framework.yml`, `.github/workflows/ci-engine.yml`, `packages/mcp/tests/`

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The release pipeline (`release-framework.yml`) includes a canary release step with version tagging. The release flow is: test → release-canary (upload tarballs, invalidate cache, tag) → release-stable (upload to production S3, invalidate cache) → release-npm. Git tags are created for version tracking. However, there is no automated rollback mechanism — no blue/green deployment, no canary with automatic rollback triggers, no feature flags. Rollback would require manually re-uploading a previous version's tarballs.
- **Gap**: No automated rollback capability. If a release breaks agent-facing MCP tools, rollback is manual.
- **Compensating Controls**:
  - Git tags allow identifying the previous known-good version.
  - NPM versioning allows pinning to a specific version.
- **Remediation Timeline**: 60 days
- **Recommendation**: Add a rollback script or CI job that can re-deploy the previous version's tarballs. Consider automated canary analysis with rollback triggers.
- **Evidence**: `.github/workflows/release-framework.yml` (canary release, no rollback)

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive MCP tool tests exist in `packages/mcp/tests/`: unit tests for all AWS tools (`lambda-info.test.js`, `iam-info.test.js`, `sqs-info.test.js`, etc.), non-AWS tools (`list-resources.test.js`, `docs.test.js`, `service-summary.test.js`, `deployment-history.test.js`), and E2E tests (`tests/e2e/`). The test scripts are defined in `packages/mcp/package.json`. However, the CI workflows (`.github/workflows/ci-framework.yml`) run `sf-core` unit tests, `serverless` unit tests, and integration tests — but **MCP-specific tests are not explicitly included** in the CI pipeline. The engine tests run in CI but MCP tests appear to run only locally.
- **Gap**: MCP tool tests exist but may not be running in CI, creating a risk that MCP tool regressions are not caught before release.
- **Compensating Controls**:
  - MCP tests can be run locally before PRs.
  - The engine unit tests (which run in CI) may cover some MCP-adjacent logic.
- **Remediation Timeline**: 7 days
- **Recommendation**: Add an explicit MCP test step to the CI pipeline. This is the lowest-effort, highest-impact improvement.
- **Evidence**: `packages/mcp/tests/`, `packages/mcp/package.json` (test scripts), `.github/workflows/ci-framework.yml` (no MCP test step)

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: The MCP server exposes a well-documented interface via the MCP protocol. 16 tools are registered in `packages/mcp/src/tools-definition.js` with detailed descriptions and Zod parameter schemas. Transport options include SSE (Express on port 3001) and stdio. The `packages/mcp/README.md` provides comprehensive documentation for all tools with input/output descriptions.
- **Implication**: The MCP protocol is an excellent agent integration surface. Tool descriptions are rich enough for LLM-based agents to understand tool purpose and usage.
- **Recommendation**: No action needed. The MCP tool registration with detailed descriptions is a strong foundation.
- **Evidence**: `packages/mcp/src/tools-definition.js`, `packages/mcp/src/server.js`, `packages/mcp/README.md`

### API-Q2: Machine-Readable API Specification
- **Severity**: INFO
- **Finding**: All MCP tools have machine-readable schemas defined using Zod (`zod ^4.3.6`). The MCP protocol's `ListTools` capability allows agents to discover available tools and their parameter schemas at runtime. While there is no traditional OpenAPI/Swagger file, the MCP SDK + Zod schema combination serves the same purpose for agent tool generation.
- **Implication**: Agent frameworks that support MCP can automatically generate tool definitions from the server's schema.
- **Recommendation**: No action needed for MCP-native consumers. If non-MCP consumers need access, consider generating OpenAPI from Zod schemas.
- **Evidence**: `packages/mcp/src/tools-definition.js` (Zod schemas), `packages/mcp/package.json` (`zod ^4.3.6`)

### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: All 16 MCP tools are read-only operations (list, info, logs, search, docs). There are no write operations exposed through the MCP server. Idempotency is inherently satisfied for read operations.
- **Implication**: No idempotency concerns for the current read-only tool surface. If write tools are added (e.g., deploy, update), idempotency must be evaluated.
- **Recommendation**: Maintain read-only scope as long as possible. When adding write tools, require idempotency keys.
- **Evidence**: `packages/mcp/src/tools-definition.js` (all read-only tools)

### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: MCP tools return JSON-structured responses via the MCP protocol's `content` array with `type: 'text'` entries containing stringified data. The data itself is structured (AWS API responses are JSON), but it is serialized as text within the MCP content envelope.
- **Implication**: LLM-based agents can parse the text content effectively. For programmatic consumers, an additional JSON parsing step is needed.
- **Recommendation**: Consider returning structured JSON objects in MCP content entries alongside human-readable text summaries.
- **Evidence**: `packages/mcp/src/tools-definition.js`

### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limits are documented for the MCP server. No rate limit headers (X-RateLimit-Remaining, Retry-After) are returned. The underlying AWS APIs have their own rate limits, but these are not surfaced to MCP clients. The cost-protection confirmation flow in `confirmation-handler.js` is the only throttling mechanism.
- **Implication**: Agents have no visibility into rate limits and cannot self-throttle. AWS API throttling errors will surface as tool errors.
- **Recommendation**: Document expected rate limits. After implementing rate limiting (STATE-Q5), return rate limit headers in MCP responses.
- **Evidence**: `packages/mcp/src/server.js`, `packages/mcp/src/lib/confirmation-handler.js`

### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: The MCP server is classified as stateless-utility. It accepts `profile` and `region` parameters that select AWS credentials from the local credential chain. There is no identity propagation (no JWT parsing, no on-behalf-of flows). The MCP server operates under the AWS credentials configured in the host environment or specified by profile name.
- **Implication**: For the stateless-utility archetype, identity propagation is not a safety concern. The agent acts under a single AWS identity.
- **Recommendation**: If the MCP server evolves to support multi-tenant or delegated access, implement identity propagation.
- **Evidence**: `packages/mcp/src/tools-definition.js` (profileParam, regionParam)

### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: No hardcoded credentials found in source code. AWS credentials are managed via the standard AWS SDK credential chain (environment variables, SSO, shared credentials files). The `aws-credentials-error-handler.js` provides clear error messages when credentials are misconfigured. The CLI auth module (`packages/sf-core/src/lib/auth/`) stores tokens in `~/.aws/login/cache/` and `~/.aws/sso/cache/` with `chmod 0o600` file permissions. License keys are stored in `.serverlessrc` via `saveRcAccessKeyV2`.
- **Implication**: Credential management follows AWS best practices for a CLI tool. No secret rotation needed for the MCP server itself — it delegates to the AWS credential chain.
- **Recommendation**: Ensure `.serverlessrc` files with license keys are excluded from version control (confirmed: `.gitignore` includes `.serverless` but not `.serverlessrc`). Consider adding `.serverlessrc` to `.gitignore`.
- **Evidence**: `packages/sf-core/src/lib/auth/aws-login.js` (0o600 permissions), `packages/mcp/src/lib/aws-credentials-error-handler.js`, `.gitignore`

### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: All MCP tools are read-only. There are no write operations to limit. The CloudWatch Logs Insights cost protection (confirmation handler) is the closest analog to a transaction limit — it requires human confirmation for queries spanning >3 hours or >1 month of history.
- **Implication**: No blast radius concern for read-only operations beyond cost (CloudWatch query charges).
- **Recommendation**: If write tools are added, implement per-agent transaction limits.
- **Evidence**: `packages/mcp/src/lib/confirmation-handler.js` (cost protection)

### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality scores or completeness metrics exist. The MCP tools return AWS API responses as-is. Data quality is determined by the AWS service APIs and the user's AWS account configuration.
- **Implication**: Planning input. Agents should not assume data completeness — AWS resources may have incomplete configurations or stale metrics.
- **Recommendation**: Consider adding data quality indicators to tool responses (e.g., "metrics may be delayed" for recent time ranges, "log group may be empty").
- **Evidence**: No evidence found — absence is the finding.

### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: MCP tool parameters use descriptive, semantically meaningful names: `functionNames`, `queueNames`, `bucketNames`, `tableNames`, `roleNames`, `apiIds`, `logGroupIdentifiers`, `workspaceRoots`, `serviceWideAnalysis`. Parameter descriptions are verbose and include usage guidance, format requirements, and examples. No legacy abbreviations or codes.
- **Implication**: LLM-based agents can understand parameter purpose from names and descriptions alone. This is an excellent practice.
- **Recommendation**: Maintain current naming conventions. Consider a naming standard document for future tool contributions.
- **Evidence**: `packages/mcp/src/tools-definition.js`

### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: The MCP protocol's `ListTools` capability serves as a runtime data catalog — agents can discover available tools, their descriptions, and parameter schemas. The `packages/mcp/README.md` provides a comprehensive static catalog of all tools. The `docs` tool provides access to Serverless Framework documentation from within the MCP interface.
- **Implication**: Tool discoverability is strong via both the MCP protocol and documentation. No additional metadata layer needed.
- **Recommendation**: Keep the README synchronized with tool definitions. Consider adding a tool categorization system (AWS, Framework, Documentation) in tool descriptions.
- **Evidence**: `packages/mcp/README.md`, `packages/mcp/src/tools-definition.js` (docs tool)

### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: The `analytics-utils.js` wraps tool executions with analytics tracking, sending `{ toolName }` events via a `sendAnalytics` callback. The `packages/util/src/telemetry/` module provides a `PlatformEventClient` for publishing events to the Serverless Platform API. These are usage analytics, not business outcome metrics. No custom CloudWatch metrics, no resolution rate tracking.
- **Implication**: Usage telemetry exists and can be extended to track business outcomes (e.g., agent resolution rate, tool success rate).
- **Recommendation**: Add tool execution latency, success/failure rate, and error category metrics to the analytics pipeline.
- **Evidence**: `packages/mcp/src/utils/analytics-utils.js`, `packages/util/src/telemetry/index.js`

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: The MCP server exposes a well-documented interface via the MCP protocol. 16 tools are registered in `packages/mcp/src/tools-definition.js` with detailed descriptions and Zod parameter schemas. Transport options include SSE (Express on port 3001) and stdio. The `packages/mcp/README.md` provides comprehensive documentation for all tools with input/output descriptions.
- **Gap**: None — the MCP protocol provides a robust documented API interface.
- **Recommendation**: No action needed. The MCP tool registration with detailed descriptions is a strong foundation.
- **Evidence**: `packages/mcp/src/tools-definition.js`, `packages/mcp/src/server.js`, `packages/mcp/README.md`

#### API-Q2: Machine-Readable API Specification
- **Severity**: INFO
- **Finding**: All MCP tools have machine-readable schemas defined using Zod (`zod ^4.3.6`). The MCP protocol's `ListTools` capability allows agents to discover available tools and their parameter schemas at runtime. While there is no traditional OpenAPI/Swagger file, the MCP SDK + Zod schema combination serves the same purpose for agent tool generation.
- **Gap**: No traditional OpenAPI/Swagger file, but the MCP + Zod approach is equivalent for MCP-native consumers.
- **Recommendation**: No action needed for MCP-native consumers. If non-MCP consumers need access, consider generating OpenAPI from Zod schemas.
- **Evidence**: `packages/mcp/src/tools-definition.js` (Zod schemas), `packages/mcp/package.json` (`zod ^4.3.6`)

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: The MCP tools handle errors via `aws-credentials-error-handler.js`, which maps AWS credential error patterns to user-friendly text messages. Error responses are returned as plain text strings in the MCP `content` array — not structured objects with error codes, error categories, or retryable booleans. Parameter validation errors from `parameter-validator.js` throw JavaScript Error objects with descriptive messages.
- **Gap**: Error responses are text-based, not structured. An agent cannot programmatically distinguish a retryable timeout from a terminal permission denied error.
- **Recommendation**: Return structured error objects with `errorCode`, `errorCategory` (credential, permission, throttling, validation, internal), and `retryable` boolean alongside the human-readable message.
- **Evidence**: `packages/mcp/src/lib/aws-credentials-error-handler.js`, `packages/mcp/src/lib/parameter-validator.js`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: All 16 MCP tools are read-only operations (list, info, logs, search, docs). There are no write operations exposed through the MCP server. Idempotency is inherently satisfied for read operations.
- **Gap**: No write operations exist, so idempotency is inherently satisfied.
- **Recommendation**: Maintain read-only scope as long as possible. When adding write tools, require idempotency keys.
- **Evidence**: `packages/mcp/src/tools-definition.js` (all read-only tools)

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: MCP tools return JSON-structured responses via the MCP protocol's `content` array with `type: 'text'` entries containing stringified data. The data itself is structured (AWS API responses are JSON), but it is serialized as text within the MCP content envelope.
- **Gap**: Data is serialized as text within the MCP content envelope rather than as structured JSON objects.
- **Recommendation**: Consider returning structured JSON objects in MCP content entries alongside human-readable text summaries.
- **Evidence**: `packages/mcp/src/tools-definition.js`

#### API-Q6: Asynchronous Operation Support
- **Severity**: RISK-QUALITY
- **Finding**: CloudWatch Logs Insights queries (`aws-logs-search`, `aws-errors-info`) can take 30+ seconds for large log groups. These operations are executed synchronously — the MCP tool handler awaits the AWS API response. There is no job submission, polling endpoint, or webhook callback pattern. The confirmation handler (`confirmation-handler.js`) provides a confirmation flow for extended timeframes but not an async execution pattern.
- **Gap**: Long-running CloudWatch queries may exceed agent timeout limits. No async pattern for operations that can take >30 seconds.
- **Recommendation**: Implement a job-based async pattern for long-running queries: submit query → return job ID → poll for results.
- **Evidence**: `packages/mcp/src/lib/confirmation-handler.js`, `packages/mcp/src/tools/aws/aws-logs-search.js`

#### API-Q7: Event Emission for State Changes
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has state changes (stateful-crud, orchestrator) — stateless-utility has no state changes.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limits are documented for the MCP server. No rate limit headers (X-RateLimit-Remaining, Retry-After) are returned. The underlying AWS APIs have their own rate limits, but these are not surfaced to MCP clients. The cost-protection confirmation flow in `confirmation-handler.js` is the only throttling mechanism.
- **Gap**: Agents have no visibility into rate limits and cannot self-throttle.
- **Recommendation**: Document expected rate limits. After implementing rate limiting (STATE-Q5), return rate limit headers in MCP responses.
- **Evidence**: `packages/mcp/src/server.js`, `packages/mcp/src/lib/confirmation-handler.js`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: The MCP SSE server (`packages/mcp/src/server.js`) has **no authentication mechanism**. The Express server exposes `/sse` and `/messages` endpoints without any API key validation, OAuth2 client credentials flow, mTLS, or any other form of caller authentication. Any process on the network that can reach the port can connect as an SSE client and invoke any registered tool. The `activeTransports` map tracks connections by `sessionId`, but `sessionId` is an opaque transport identifier — not an authenticated principal. The stdio server (`packages/mcp/src/stdio-server.js`) similarly has no authentication layer.
- **Gap**: No machine identity authentication for agents connecting to the MCP server. The server cannot distinguish which agent made a call, and cannot attribute actions to a specific principal in audit logs.
- **Recommendation**: Add API key or bearer token authentication middleware to the Express SSE server. Validate an `Authorization` header before establishing SSE connections on `/sse` and accepting messages on `/messages`. Map each API key to a named principal for audit attribution.
- **Evidence**: `packages/mcp/src/server.js` (lines 33–54: no auth middleware), `packages/mcp/src/stdio-server.js`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: The MCP server has no per-agent permission model. All MCP tool registrations in `packages/mcp/src/tools-definition.js` are available to every connected client. The `profile` and `region` parameters delegate AWS-level authorization to IAM, but the MCP server itself cannot restrict which tools or AWS accounts an agent can access. A connected agent has access to all 16 tools regardless of its intended scope.
- **Gap**: No mechanism to grant an agent read-only access to specific resources or tools without granting access to the full tool surface.
- **Recommendation**: Implement tool-level access control lists (ACLs) in the MCP server, configurable per API key or identity.
- **Evidence**: `packages/mcp/src/tools-definition.js` (all tools registered unconditionally)

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: All MCP tools are currently read-only (info, list, logs, docs). However, the MCP server has no mechanism to enforce action-level authorization. If write tools are added in the future, there is no framework to restrict specific agents to read-only operations. The tool registration in `tools-definition.js` does not support permission annotations.
- **Gap**: No action-level authorization framework within the MCP server. Cannot enforce "this agent can call `list-resources` but not `deployment-history`" at the MCP layer.
- **Recommendation**: Add tool-level permission annotations and enforcement middleware before adding any write-capable tools.
- **Evidence**: `packages/mcp/src/tools-definition.js`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: The MCP server is classified as stateless-utility. It accepts `profile` and `region` parameters that select AWS credentials from the local credential chain. There is no identity propagation (no JWT parsing, no on-behalf-of flows). The MCP server operates under the AWS credentials configured in the host environment or specified by profile name.
- **Gap**: No identity propagation, but not required for stateless-utility archetype.
- **Recommendation**: If the MCP server evolves to support multi-tenant or delegated access, implement identity propagation.
- **Evidence**: `packages/mcp/src/tools-definition.js` (profileParam, regionParam)

#### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: No hardcoded credentials found in source code. AWS credentials are managed via the standard AWS SDK credential chain (environment variables, SSO, shared credentials files). The `aws-credentials-error-handler.js` provides clear error messages when credentials are misconfigured. The CLI auth module (`packages/sf-core/src/lib/auth/`) stores tokens in `~/.aws/login/cache/` and `~/.aws/sso/cache/` with `chmod 0o600` file permissions. License keys are stored in `.serverlessrc` via `saveRcAccessKeyV2`.
- **Gap**: `.serverlessrc` files with license keys may not be excluded from version control (`.gitignore` includes `.serverless` but not `.serverlessrc`).
- **Recommendation**: Ensure `.serverlessrc` files with license keys are excluded from version control. Consider adding `.serverlessrc` to `.gitignore`.
- **Evidence**: `packages/sf-core/src/lib/auth/aws-login.js` (0o600 permissions), `packages/mcp/src/lib/aws-credentials-error-handler.js`, `.gitignore`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The MCP server logs client connections and disconnections via `console.error` with `sessionId` in `server.js`. The `analytics-utils.js` wrapper sends analytics events with `toolName` after each tool execution. However: (1) no authenticated principal is logged — only an opaque `sessionId`; (2) logs are written to stderr with no immutable storage; (3) analytics events do not include the caller identity, parameters, or response metadata; (4) no CloudTrail or equivalent audit trail for MCP tool invocations.
- **Gap**: Tool invocations are not attributed to an authenticated principal. Logs are not immutable or tamper-evident. Cannot determine which agent called which tool with which parameters.
- **Recommendation**: Implement structured audit logging for every tool invocation, including authenticated principal, tool name, parameters, and timestamp. Store in an immutable log system.
- **Evidence**: `packages/mcp/src/server.js` (console.error logging), `packages/mcp/src/utils/analytics-utils.js` (tool name only)

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: The MCP server tracks active connections in the `activeTransports` map keyed by `sessionId`. The `stop()` function in `server.js` closes all transports, and individual transports are cleaned up on disconnect. However, there is no mechanism to suspend or revoke a specific agent's access while the server is running. There is no API key revocation, no blocklist, and no way to terminate a specific session by identity.
- **Gap**: Cannot isolate or suspend a misbehaving agent without restarting the entire MCP server, which disconnects all agents.
- **Recommendation**: Implement session termination by identity — an admin endpoint or control plane that can disconnect a specific agent by API key or principal.
- **Evidence**: `packages/mcp/src/server.js` (activeTransports map, stop() function)

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The MCP tools are exclusively read-only operations (list, info, logs, docs, search). There are no multi-step write workflows to compensate or roll back. The underlying Serverless Framework CLI has deploy/remove operations with CloudFormation stack management, but these are not exposed through the MCP tools.
- **Gap**: No compensation or rollback capability exists in the MCP server, but this is mitigated by the read-only nature of all current tools.
- **Recommendation**: Before exposing any write operations through MCP, implement compensation patterns (e.g., undo endpoints, saga coordination).
- **Evidence**: `packages/mcp/src/tools-definition.js` (all read-only tools)

#### STATE-Q2: Queryable Current State
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled AND service has persistent state — agent_scope is read-only.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: The MCP tools call AWS APIs directly via AWS SDK v3 clients. Retry logic exists in `packages/serverless/lib/aws/request-retry.js` using exponential backoff with jitter (base 5000ms, max retries configurable). The `@smithy/util-retry` dependency is present. However, there are **no circuit breaker patterns** in the MCP tools or their underlying AWS client calls. If an AWS API is degraded, the MCP server will continue sending requests, accumulating failures and consuming resources.
- **Gap**: No circuit breaker implementation. Retry logic exists but without circuit breaker protection, a degraded AWS API can cause cascading failures in the MCP server.
- **Recommendation**: Add circuit breaker middleware (e.g., `opossum` or custom implementation) around AWS API calls in MCP tools to fail fast when downstream services are degraded.
- **Evidence**: `packages/serverless/lib/aws/request-retry.js`, `packages/mcp/package.json` (no circuit breaker dependency)

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: The MCP SSE server (`packages/mcp/src/server.js`) is a plain Express application with **no rate limiting middleware**. There is no `express-rate-limit`, no API Gateway throttling, no WAF rules, and no connection limits. An agent can send unlimited tool invocation requests at machine speed. The confirmation handler (`confirmation-handler.js`) limits costly CloudWatch Logs Insights queries by requiring confirmation tokens for extended timeframes, but this is a cost protection mechanism, not rate limiting.
- **Gap**: No rate limiting on the MCP server. A runaway agent loop could overwhelm the server and the underlying AWS APIs.
- **Recommendation**: Add `express-rate-limit` middleware to the SSE server with configurable per-client rate limits. Consider per-tool rate limits for expensive operations (CloudWatch queries).
- **Evidence**: `packages/mcp/src/server.js` (no rate limiting middleware), `packages/mcp/package.json` (no rate limiting dependency)

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: All MCP tools are read-only. There are no write operations to limit. The CloudWatch Logs Insights cost protection (confirmation handler) is the closest analog to a transaction limit — it requires human confirmation for queries spanning >3 hours or >1 month of history.
- **Gap**: No transaction limits, but not required for read-only operations.
- **Recommendation**: If write tools are added, implement per-agent transaction limits.
- **Evidence**: `packages/mcp/src/lib/confirmation-handler.js` (cost protection)

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path (priority is P2)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled — agent_scope is read-only.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled — agent_scope is read-only.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: The MCP server can be started locally via `npm start` (port 3001) or `npm start:stdio`. Unit tests exist in `packages/mcp/tests/` with mocked AWS responses. E2E tests exist in `packages/mcp/tests/e2e/`. However, there is no formal sandbox or staging environment with production-equivalent data shape. The MCP tests use mocked data, not realistic AWS account data. No Docker Compose for local testing. No seed data scripts.
- **Gap**: No staging environment where agents can be tested against realistic (but safe) AWS data. Testing against production AWS accounts is the only option.
- **Recommendation**: Create a Docker Compose setup with LocalStack or similar AWS mock service for local agent testing. Alternatively, document a recommended sandbox AWS account configuration.
- **Evidence**: `packages/mcp/package.json` (start scripts), `packages/mcp/tests/` (unit tests), `packages/mcp/tests/e2e/` (e2e tests)

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: The MCP `aws-lambda-info` tool returns Lambda function configuration including **environment variables**, which commonly contain secrets (database passwords, API keys, third-party tokens). The tool response passes raw AWS API data without field-level classification or redaction. The `obfuscateSensitiveData` function exists in `packages/sf-core/src/utils/general/index.js` (obfuscates keys like `environment`) but is **not used** in any MCP tool implementation. Similarly, `aws-iam-info` returns full IAM policy documents, and `aws-s3-info` returns bucket policies — all potentially containing sensitive resource ARNs and account IDs.
- **Gap**: No sensitive data classification or field-level redaction in MCP tool responses. An agent can retrieve Lambda environment variables containing secrets without any filtering or access controls beyond the underlying AWS IAM permissions.
- **Recommendation**: Apply the existing `obfuscateSensitiveData` function (or a similar redaction layer) to MCP tool responses before returning them to agents. At minimum, redact `environment` variables from Lambda configurations, and flag fields containing account IDs, ARNs, and policy documents.
- **Evidence**: `packages/mcp/src/tools-definition.js` (Lambda info tool), `packages/sf-core/src/utils/general/index.js:255` (obfuscateSensitiveData — not used by MCP), `packages/mcp/src/tools/aws/lambda-info.js`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: MCP tools accept a `region` parameter allowing agents to query AWS resources in any region. Data returned from AWS APIs (Lambda configurations, logs, IAM policies) flows through the MCP server to the agent and potentially to an LLM. There are no controls preventing an agent from requesting data from regulated regions or transmitting it cross-border to an LLM provider.
- **Gap**: No data residency controls in the MCP server. An agent could retrieve data from an EU region and transmit it to an LLM endpoint in the US.
- **Recommendation**: Add a configurable region allowlist to the MCP server. Validate the `region` parameter against the allowlist before executing tools. Document data residency implications in the README.
- **Evidence**: `packages/mcp/src/tools-definition.js` (regionParam accepts any string), `packages/mcp/README.md`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK-QUALITY
- **Finding**: MCP log tools (`aws-logs-search`, `aws-logs-tail`) accept a `limit` parameter (max 100). The `aws-errors-info` tool has `maxResults` (max 100). Time range filtering is supported on all tools with `startTime`/`endTime`. However, resource listing tools (`list-resources`, `aws-lambda-info`) return all resources without pagination. There is no cursor-based pagination for large result sets.
- **Gap**: Resource listing tools may return large unbounded result sets for AWS accounts with many resources. No cursor-based pagination.
- **Recommendation**: Add pagination support (cursor-based) for resource listing tools. Add configurable `maxResults` parameters where missing.
- **Evidence**: `packages/mcp/src/tools-definition.js` (limit parameters on log tools, no pagination on resource tools)

#### DATA-Q4: System of Record Designations
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator) — stateless-utility has no persistent state.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: The MCP server logs to stderr using `console.error`. The `confirmation-handler.js` logs error details including log group names. Tool responses may contain PII from AWS resources (IAM user names, email addresses in policies, account IDs). The `obfuscateSensitiveData` function exists in `packages/sf-core/src/utils/general/index.js` but is not applied to MCP server logging or tool responses. No PII detection or masking is applied to logs or tool response data.
- **Gap**: No PII redaction in MCP server logs or tool responses. If an agent sends tool responses to an LLM, PII from AWS resources could be included in prompts.
- **Recommendation**: Apply PII detection and masking to MCP server logs. Consider redacting account IDs, user names, and email addresses from tool responses before returning to agents.
- **Evidence**: `packages/mcp/src/server.js` (console.error), `packages/sf-core/src/utils/general/index.js:255` (obfuscateSensitiveData — unused by MCP)

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality scores or completeness metrics exist. The MCP tools return AWS API responses as-is. Data quality is determined by the AWS service APIs and the user's AWS account configuration.
- **Gap**: No data quality indicators in tool responses.
- **Recommendation**: Consider adding data quality indicators to tool responses (e.g., "metrics may be delayed" for recent time ranges, "log group may be empty").
- **Evidence**: No evidence found — absence is the finding.

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: MCP tool schemas are defined using Zod in `packages/mcp/src/tools-definition.js`. The MCP server version is hardcoded as `1.0.0` in both `server.js` and `stdio-server.js`. The `VERSIONING.md` documents SemVer practices for the framework CLI, but there is no version tracking specific to the MCP tool interface. No breaking change detection in CI for MCP tool schemas. No consumer-driven contract tests. No OpenAPI diff or schema comparison tools in the CI pipeline.
- **Gap**: MCP tool schemas can change without detection. No breaking change detection for the agent integration surface. Agent tool bindings may break silently.
- **Recommendation**: Add schema snapshot tests that detect changes to tool definitions. Integrate into CI as a gate. Consider versioning the MCP tool interface independently from the framework version.
- **Evidence**: `packages/mcp/src/tools-definition.js`, `packages/mcp/src/server.js` (version: '1.0.0'), `VERSIONING.md`, `.github/workflows/ci-framework.yml` (no schema tests)

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: MCP tool parameters use descriptive, semantically meaningful names: `functionNames`, `queueNames`, `bucketNames`, `tableNames`, `roleNames`, `apiIds`, `logGroupIdentifiers`, `workspaceRoots`, `serviceWideAnalysis`. Parameter descriptions are verbose and include usage guidance, format requirements, and examples. No legacy abbreviations or codes.
- **Gap**: None — field names are semantically meaningful.
- **Recommendation**: Maintain current naming conventions. Consider a naming standard document for future tool contributions.
- **Evidence**: `packages/mcp/src/tools-definition.js`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: The MCP protocol's `ListTools` capability serves as a runtime data catalog — agents can discover available tools, their descriptions, and parameter schemas. The `packages/mcp/README.md` provides a comprehensive static catalog of all tools. The `docs` tool provides access to Serverless Framework documentation from within the MCP interface.
- **Gap**: None — tool discoverability is strong via both the MCP protocol and documentation.
- **Recommendation**: Keep the README synchronized with tool definitions. Consider adding a tool categorization system (AWS, Framework, Documentation) in tool descriptions.
- **Evidence**: `packages/mcp/README.md`, `packages/mcp/src/tools-definition.js` (docs tool)

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: The MCP server uses `console.error` for all logging — unstructured plain text to stderr. No JSON logging. No correlation IDs. No distributed tracing (no OpenTelemetry, no X-Ray). The `packages/util/src/logger/index.js` provides a rich logging framework with levels, progress tracking, and styling — but this is designed for CLI interactive output, not structured service logging. The MCP server does not use this logger.
- **Gap**: Cannot reconstruct what happened during an agent-initiated request. No trace ID propagation. No structured logs for automated analysis.
- **Recommendation**: Replace `console.error` calls with a structured JSON logger. Add a request/correlation ID to each tool invocation. Consider OpenTelemetry instrumentation for distributed tracing.
- **Evidence**: `packages/mcp/src/server.js` (console.error), `packages/util/src/logger/index.js` (CLI logger, not used by MCP)

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: No alerting is configured for the MCP server. No CloudWatch alarms, no PagerDuty/OpsGenie integration, no error rate or latency thresholds. The MCP server is designed to run locally as part of the CLI, not as a deployed service with monitoring. The analytics wrapper (`analytics-utils.js`) sends tool execution events but does not track error rates or latency.
- **Gap**: No automated alerting on MCP server health. If the server degrades, agents will fail without notification.
- **Recommendation**: If the MCP server is deployed as a shared service, add health check endpoints, latency tracking, and alerting thresholds. For local use, this is lower priority.
- **Evidence**: `packages/mcp/src/server.js`, `packages/mcp/src/utils/analytics-utils.js`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: The `analytics-utils.js` wraps tool executions with analytics tracking, sending `{ toolName }` events via a `sendAnalytics` callback. The `packages/util/src/telemetry/` module provides a `PlatformEventClient` for publishing events to the Serverless Platform API. These are usage analytics, not business outcome metrics. No custom CloudWatch metrics, no resolution rate tracking.
- **Gap**: Usage telemetry exists but no business outcome metrics.
- **Recommendation**: Add tool execution latency, success/failure rate, and error category metrics to the analytics pipeline.
- **Evidence**: `packages/mcp/src/utils/analytics-utils.js`, `packages/util/src/telemetry/index.js`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance
- **Severity**: RISK-QUALITY
- **Finding**: The release infrastructure (S3 tarball uploads, CloudFront cache invalidation) is defined only in CI scripts (`.github/workflows/release-framework.yml`), not in IaC. AWS credentials are configured via GitHub Actions OIDC role assumption (`arn:aws:iam::762003938904:role/GithubActionsDeploymentRole`), which is good practice. However, the S3 buckets, CloudFront distributions, and IAM roles themselves are not defined as IaC in this repository. No drift detection is configured.
- **Gap**: Release infrastructure is not defined as code in this repository. Changes to S3 buckets or CloudFront distributions are not subject to PR review in this codebase.
- **Recommendation**: Either reference the IaC definitions for release infrastructure or add them to this repository. Enable drift detection.
- **Evidence**: `.github/workflows/release-framework.yml` (S3 upload, CloudFront invalidation)

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: CI/CD pipelines exist in `.github/workflows/ci-framework.yml` and `.github/workflows/ci-engine.yml` with linting, unit tests, and integration tests. The release pipeline runs cross-platform tests. However, there are **no API contract tests** for the MCP tool interface. No Pact tests. No OpenAPI schema validation. No schema comparison tools. Changes to MCP tool parameters could reach production without detection.
- **Gap**: No automated detection of breaking changes in the MCP tool interface. An agent relying on a specific tool parameter could break after a release.
- **Recommendation**: Add MCP schema snapshot tests that fail when tool definitions change. Integrate Pact or similar consumer-driven contract testing for the MCP interface.
- **Evidence**: `.github/workflows/ci-framework.yml`, `.github/workflows/ci-engine.yml`, `packages/mcp/tests/`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: The release pipeline (`release-framework.yml`) includes a canary release step with version tagging. The release flow is: test → release-canary (upload tarballs, invalidate cache, tag) → release-stable (upload to production S3, invalidate cache) → release-npm. Git tags are created for version tracking. However, there is no automated rollback mechanism — no blue/green deployment, no canary with automatic rollback triggers, no feature flags. Rollback would require manually re-uploading a previous version's tarballs.
- **Gap**: No automated rollback capability. If a release breaks agent-facing MCP tools, rollback is manual.
- **Recommendation**: Add a rollback script or CI job that can re-deploy the previous version's tarballs. Consider automated canary analysis with rollback triggers.
- **Evidence**: `.github/workflows/release-framework.yml` (canary release, no rollback)

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive MCP tool tests exist in `packages/mcp/tests/`: unit tests for all AWS tools (`lambda-info.test.js`, `iam-info.test.js`, `sqs-info.test.js`, etc.), non-AWS tools (`list-resources.test.js`, `docs.test.js`, `service-summary.test.js`, `deployment-history.test.js`), and E2E tests (`tests/e2e/`). The test scripts are defined in `packages/mcp/package.json`. However, the CI workflows (`.github/workflows/ci-framework.yml`) run `sf-core` unit tests, `serverless` unit tests, and integration tests — but **MCP-specific tests are not explicitly included** in the CI pipeline. The engine tests run in CI but MCP tests appear to run only locally.
- **Gap**: MCP tool tests exist but may not be running in CI, creating a risk that MCP tool regressions are not caught before release.
- **Recommendation**: Add an explicit MCP test step to the CI pipeline. This is the lowest-effort, highest-impact improvement.
- **Evidence**: `packages/mcp/tests/`, `packages/mcp/package.json` (test scripts), `.github/workflows/ci-framework.yml` (no MCP test step)

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent data stores (the MCP server has no persistent data stores)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `packages/mcp/src/server.js` | API-Q1, API-Q5, API-Q8, AUTH-Q1, AUTH-Q6, AUTH-Q7, STATE-Q5, OBS-Q1, OBS-Q2 |
| `packages/mcp/src/stdio-server.js` | API-Q1, AUTH-Q1 |
| `packages/mcp/src/tools-definition.js` | API-Q1, API-Q2, API-Q3, API-Q4, API-Q5, AUTH-Q2, AUTH-Q3, AUTH-Q4, STATE-Q1, STATE-Q6, DATA-Q1, DATA-Q2, DATA-Q3, DISC-Q1, DISC-Q2 |
| `packages/mcp/src/lib/aws-credentials-error-handler.js` | API-Q3, AUTH-Q5 |
| `packages/mcp/src/lib/confirmation-handler.js` | API-Q6, API-Q8, STATE-Q6, DATA-Q3 |
| `packages/mcp/src/lib/parameter-validator.js` | API-Q3 |
| `packages/mcp/src/utils/analytics-utils.js` | AUTH-Q6, OBS-Q2, OBS-Q3 |
| `packages/mcp/src/tools/aws/lambda-info.js` | DATA-Q1 |
| `packages/mcp/src/tools/aws/aws-logs-search.js` | API-Q6 |
| `packages/sf-core/src/lib/auth/index.js` | AUTH-Q5 |
| `packages/sf-core/src/lib/auth/aws-login.js` | AUTH-Q5 |
| `packages/sf-core/src/lib/auth/aws-sso-login.js` | AUTH-Q5 |
| `packages/sf-core/src/utils/general/index.js` | DATA-Q1, DATA-Q6 |
| `packages/serverless/lib/aws/request-retry.js` | STATE-Q4 |
| `packages/util/src/logger/index.js` | OBS-Q1 |
| `packages/util/src/telemetry/index.js` | OBS-Q3 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| No OpenAPI/AsyncAPI/Swagger files found | API-Q2 (MCP + Zod serves as equivalent) |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/ci-framework.yml` | DISC-Q1, ENG-Q2, ENG-Q4 |
| `.github/workflows/ci-engine.yml` | ENG-Q2 |
| `.github/workflows/release-framework.yml` | ENG-Q1, ENG-Q3 |
| `.github/dependabot.yml` | ENG-Q2 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `package.json` (root) | API-Q2 |
| `packages/mcp/package.json` | API-Q2, STATE-Q4, STATE-Q5, ENG-Q4 |
| `packages/serverless/package.json` | STATE-Q4 |
| `packages/sf-core/package.json` | AUTH-Q5 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `.gitignore` | AUTH-Q5 |
| `VERSIONING.md` | DISC-Q1 |
| `packages/mcp/README.md` | API-Q1, DATA-Q2, DISC-Q3 |

### Test Files
| File | Questions Referenced |
|------|---------------------|
| `packages/mcp/tests/` | ENG-Q4, HITL-Q3 |
| `packages/mcp/tests/e2e/` | ENG-Q4, HITL-Q3 |
