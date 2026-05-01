# Agentic Readiness Assessment Report

**Target**: node-lambda
**Date**: 2026-04-30
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Service Archetype**: stateless-utility (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: javascript, serverless, cli
**Context**: Node.js CLI for deploying AWS Lambda functions.

**Archetype Justification**: No HTTP server, no database connections, no message queue consumers. The tool is a command-line utility that invokes AWS SDK APIs to package and deploy Lambda functions. All operations are initiated by the CLI user (not by inbound requests).

**INFO — Dev-Library-Application Override Applied**: This repository's `repo_type` is `application`, but its `service_archetype` is `stateless-utility` and all 5 surface flags are `false`. Per ARA Step 1.5, the dev-library-application override is applied: the `library` N/A mapping is used as the scoring baseline (ENG-Q1 through ENG-Q5 become N/A), and surface-flag downgrades are applied to remaining questions. The original `repo_type` value (`application`) is preserved.

- **Surface flags**:
  - has_persistent_data_store: false
  - has_http_rpc_surface: false
  - has_auth_surface: false
  - has_write_operations: false
  - has_logging_of_user_data: false

---

## Readiness Profile: Agent-Ready

**BLOCKERs**: 0 | **RISK-SAFETY**: 0 | **RISK-QUALITY**: 1 | **INFOs**: 29

Cleared for autonomous operation. Instrument observability. Define scope explicitly. Run controlled pilot first.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 0 |
| RISK-SAFETY | 0 |
| RISK-QUALITY | 1 |
| INFO | 29 |
| N/A | 5 |
| Not Evaluated (extended) | 8 |
| **Total** | **43** |

**Core Questions Evaluated**: 21 (of 24 core; 3 core are N/A via dev-library-application override: ENG-Q1, ENG-Q2, ENG-Q3)
**Extended Questions Triggered**: 8 (API-Q5, API-Q6, API-Q8, STATE-Q4, DATA-Q7, DISC-Q2, DISC-Q3, OBS-Q3)
**Extended Questions Not Triggered**: 8 (API-Q7, STATE-Q2, STATE-Q7, HITL-Q1, HITL-Q2, DATA-Q3, DATA-Q4, DATA-Q5)
**Extended Questions N/A (dev-library-application override)**: 2 (ENG-Q4, ENG-Q5)
**Questions N/A (repo_type: application, dev-library-application override)**: 5
**Service Archetype**: stateless-utility (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

No BLOCKERs identified.

---

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

No RISK-SAFETY findings identified.

### RISK-QUALITY — Address as Capacity Allows

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The package uses semantic versioning (version `1.3.0` in `package.json`) and maintains a `CHANGELOG.md` with release notes dating back to `0.8.0`. The npm ecosystem provides semver-based versioning which is the standard contract for CLI/library packages. However, there is no breaking change detection in CI (no `buf breaking`, no OpenAPI diff, no consumer-driven contract tests like Pact). The CI pipeline (`workflow.yml`) runs lint and unit tests but does not validate that CLI option names, environment variable names, or exported API shapes have not changed in a breaking way.
- **Gap**: No automated breaking change detection in the CI pipeline. CLI option changes or export signature changes could silently break agent tool bindings. The CHANGELOG is manually maintained.
- **Compensating Controls**:
  - Semver discipline — the project follows Keep a Changelog format and semver, so major version bumps signal breaking changes.
  - Dependabot is configured to monitor npm dependencies monthly, reducing transitive breakage risk.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a snapshot-based CLI contract test (e.g., run `node-lambda --help` and diff against a golden snapshot) to the CI pipeline. This catches unintentional option renames or removals before release.
- **Evidence**: `package.json` (version field), `CHANGELOG.md`, `.github/workflows/workflow.yml`, `.github/dependabot.yml`

---

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO
- **Finding**: The CLI exposes a command-line interface with four commands (`setup`, `run`, `package`, `deploy`) defined via `commander` in `bin/node-lambda`. The interface is documented in `README.md` with full `--help` output for each command. The library also exports its API via `lib/main.js` (as `index.js` re-exports it). Since `has_http_rpc_surface` is `false` and the dev-library-application override applies, this is not a REST/GraphQL/AsyncAPI interface — agents would invoke the CLI as a subprocess or import the library module directly. The CLI commands and README documentation constitute the interface contract for agent consumption.
- **Implication**: Agents integrating with this tool would invoke it as a subprocess (`node-lambda deploy ...`) or use its programmatic API. MCP tool bindings would wrap CLI commands rather than HTTP endpoints.
- **Recommendation**: Consider publishing a machine-readable CLI schema (e.g., JSON output of all commands and options) to simplify agent tool generation.
- **Evidence**: `bin/node-lambda`, `README.md`, `lib/main.js`, `index.js`

### API-Q2: Machine-Readable API Specification

- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — machine-readable spec is not applicable. The CLI's interface is defined by `commander` option definitions in `bin/node-lambda` and documented in `README.md`. No OpenAPI, AsyncAPI, GraphQL schema, or Smithy model exists (nor would one be expected for a CLI tool).
- **Implication**: Agent tool definitions must be authored from the README documentation or `--help` output rather than auto-generated from a spec.
- **Recommendation**: No action required for current architecture.
- **Evidence**: `bin/node-lambda`, `README.md`

### API-Q3: Structured Error Responses

- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — structured error responses are not applicable. The CLI uses `process.exitCode` (0 for success, 1 for deploy failure, 254 for unsupported runtime, 255 for handler errors) and `console.log`/`console.error` for output. Error messages are unstructured text strings.
- **Implication**: Agent subprocess invocations must parse exit codes and stderr/stdout text to determine success/failure. There is no structured JSON error envelope.
- **Recommendation**: For future agent integration, consider a `--json` output mode that wraps all output (including errors) in structured JSON with error codes, messages, and retryable flags.
- **Evidence**: `lib/main.js` (lines with `process.exitCode`, `console.error`, `console.log`)

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The `deploy` command creates or updates Lambda functions. The `_uploadExisting` path uses `updateFunctionConfiguration` + `updateFunctionCode`, which are inherently idempotent (re-deploying the same code produces the same result). The `_uploadNew` path uses `createFunction`, which will fail with `ResourceConflictException` if the function already exists — the CLI handles this by checking `getFunction` first. However, since agent_scope is read-only, idempotency of write operations is informational only.
- **Implication**: If agent_scope is expanded to write-enabled in the future, the deploy operation is effectively idempotent. The `createFunction` / `updateFunctionCode` pattern is safe for retries.
- **Recommendation**: No action required for read-only scope.
- **Evidence**: `lib/main.js` (`_uploadExisting`, `_uploadNew`, `_deployToRegion`)

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: CLI output is a mix of plain text log messages (`console.log`) and JSON-serialized AWS API responses. The `run` command outputs handler results as `JSON.stringify(result)`. The `deploy` command outputs AWS SDK response objects via `console.log(results)`. There is no consistent structured output format — operational messages are interspersed with data.
- **Implication**: Agents parsing CLI output must distinguish operational log lines from data output. A structured output mode would improve agent consumption.
- **Recommendation**: Consider adding a `--output json` flag that emits only machine-readable JSON (suppressing operational log messages).
- **Evidence**: `lib/main.js` (`_runHandler`, `_deployToRegion`, `_printDeployResults`)

### API-Q6: Asynchronous Operation Support

- **Severity**: INFO
- **Finding**: Extended question triggered — the `deploy` operation can take >30 seconds (`DEPLOY_TIMEOUT` defaults to 120000ms / 2 minutes). The CLI executes deployment synchronously: it builds the archive, uploads to Lambda (with retry-on-failure via AWS SDK's `on('retry')` handler), waits for `LastUpdateStatus === 'Successful'` via polling (up to 10 retries with 3-second delays), then uploads code. There is no async job submission pattern — the CLI blocks until deployment completes or fails. This is expected for a CLI tool.
- **Implication**: Agent subprocess invocations of `node-lambda deploy` will block for the duration of deployment. Agents must set appropriate timeouts (≥120 seconds). For multi-region deployments, the CLI deploys to all regions in parallel via `Promise.all`.
- **Recommendation**: No action required for CLI usage. If agent orchestration requires async patterns, the agent should manage timeout and concurrency externally.
- **Evidence**: `lib/main.js` (`deploy`, `_deployToRegion`, `_uploadExisting`), `bin/node-lambda` (`DEPLOY_TIMEOUT`)

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limit documentation or headers. The CLI calls AWS APIs directly via the AWS SDK, which is subject to AWS service-level rate limits (Lambda API throttling, S3 throttling). The CLI does not document these limits or implement client-side rate limit awareness. The AWS SDK provides built-in retry with exponential backoff for throttled requests.
- **Implication**: Agents invoking this CLI repeatedly may trigger AWS API throttling. The AWS SDK's built-in retry behavior provides some protection, but agents should implement their own rate limiting for batch operations.
- **Recommendation**: Document AWS API rate limits in README for agent operators. Consider adding a `--dry-run` mode to allow agents to validate parameters without consuming API quota.
- **Evidence**: `lib/main.js`, `lib/aws.js`

### AUTH-Q1: Machine Identity Authentication

- **Severity**: INFO
- **Finding**: The CLI delegates authentication entirely to the AWS SDK credential chain. It accepts credentials via: (1) environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`), (2) CLI options (`--accessKey`, `--secretKey`, `--sessionToken`), (3) AWS profile (`--profile` / `AWS_PROFILE`), and (4) the default AWS SDK credential chain (instance profiles, container credentials, etc.). The CLI does not issue, validate, or manage identity itself — it is a consumer of AWS IAM credentials. Since `has_auth_surface` is `false`, machine identity authentication is a consumer/platform responsibility, not a property of this tool.
- **Implication**: An agent invoking this CLI would provide its own AWS credentials (e.g., via IAM role assumption, environment variables). The CLI correctly supports all standard AWS credential mechanisms.
- **Recommendation**: No action required. Document recommended credential patterns for agent use (e.g., "use IAM roles with session tokens, not long-lived access keys").
- **Evidence**: `bin/node-lambda`, `lib/aws.js`, `lib/.env.example`

### AUTH-Q2: Scoped Permissions (Least Privilege)

- **Severity**: INFO
- **Finding**: The CLI uses whatever IAM credentials are provided and does not enforce scoped permissions itself. Permission scoping is the responsibility of IAM policies attached to the caller's identity. The CLI requires permissions for: `lambda:CreateFunction`, `lambda:UpdateFunctionCode`, `lambda:UpdateFunctionConfiguration`, `lambda:GetFunction`, `lambda:AddPermission`, `lambda:ListEventSourceMappings`, `lambda:CreateEventSourceMapping`, `lambda:UpdateEventSourceMapping`, `lambda:DeleteEventSourceMapping`, `lambda:ListTags`, `lambda:TagResource`, `lambda:UntagResource`, `lambda:GetAlias`, `lambda:CreateAlias`, `lambda:UpdateAlias`, `s3:CreateBucket`, `s3:PutObject`, `s3:PutBucketNotificationConfiguration`, `events:PutRule`, `events:PutTargets`, `logs:CreateLogGroup`, `logs:PutRetentionPolicy`. Since `has_auth_surface` is `false`, this is a consumer responsibility.
- **Implication**: Agent operators must create IAM policies with least-privilege permissions scoped to the specific Lambda functions and resources the agent is authorized to manage.
- **Recommendation**: Publish a recommended minimum IAM policy document in the README for agent integration use cases.
- **Evidence**: `lib/main.js`, `lib/s3_deploy.js`, `lib/s3_events.js`, `lib/schedule_events.js`, `lib/cloudwatch_logs.js`

### AUTH-Q3: Action-Level Authorization

- **Severity**: INFO
- **Finding**: The CLI does not enforce action-level authorization — it delegates to AWS IAM. AWS IAM natively supports action-level authorization (e.g., allow `lambda:GetFunction` but deny `lambda:DeleteFunction`). Since `has_auth_surface` is `false`, action-level authorization is a platform/consumer responsibility.
- **Implication**: Agent operators can use IAM policies to restrict agent identities to read-only actions (e.g., `lambda:GetFunction`, `lambda:ListFunctions`) while denying write actions (`lambda:CreateFunction`, `lambda:UpdateFunctionCode`).
- **Recommendation**: No action required. The AWS IAM model fully supports this.
- **Evidence**: `lib/main.js`, `lib/aws.js`

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: INFO
- **Finding**: For stateless-utility archetype, downgraded to INFO. The CLI does not propagate identity — it uses the provided AWS credentials directly. There is no on-behalf-of flow or identity delegation pattern. The CLI is the terminal caller in the chain.
- **Implication**: If an agent invokes this CLI on behalf of a user, the agent must assume the user's IAM role before invoking the CLI. The CLI has no mechanism to distinguish "agent-as-self" vs "agent-on-behalf-of-user."
- **Recommendation**: No action required for CLI tool architecture.
- **Evidence**: `lib/aws.js`

### AUTH-Q5: Credential Management

- **Severity**: INFO
- **Finding**: Credentials are sourced from environment variables and `.env` files, not from a secrets management system. The `.env.example` file contains placeholder values (`AWS_ACCESS_KEY_ID=your_key`, `AWS_SECRET_ACCESS_KEY=your_secret`). The `.gitignore` correctly excludes `.env` and `deploy.env` from version control. No AWS Secrets Manager or HashiCorp Vault integration exists. The CLI supports AWS profiles (`--profile`), which can leverage IAM roles and the AWS credential chain — this is the recommended secure credential mechanism.
- **Implication**: Agents using this CLI should provide credentials via IAM role assumption (instance profiles, container credentials, OIDC federation) rather than long-lived access keys in environment variables.
- **Recommendation**: Add a documentation note recommending IAM role-based credentials over access keys for automated/agent usage. Consider deprecating `--accessKey` and `--secretKey` CLI options in favor of `--profile` and the default credential chain.
- **Evidence**: `bin/node-lambda`, `lib/aws.js`, `lib/.env.example`, `.gitignore`

### AUTH-Q6: Immutable Audit Logging ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity would be RISK-SAFETY, but surface-flag calibration applies
- **Finding**: System does not execute agent-invoked write operations — audit logging is a consumer responsibility. The CLI is a tool invoked by users/agents; it does not own an audit surface. All actions performed by the CLI are logged by AWS CloudTrail in the target AWS account (Lambda API calls, S3 API calls, CloudWatch API calls). `has_auth_surface` is `false` AND `has_write_operations` is `false`.
- **Implication**: Audit trails for agent-initiated deployments are captured by AWS CloudTrail in the target account. The CLI itself has no audit logging to assess.
- **Recommendation**: Ensure CloudTrail is enabled in target AWS accounts where agents will invoke this CLI.
- **Evidence**: `lib/main.js`, `lib/aws.js`

### AUTH-Q7: Agent Identity Suspension

- **Severity**: INFO
- **Finding**: System does not issue or enforce agent identities — suspension is a consumer responsibility. The CLI delegates identity to AWS IAM. Agent identity suspension is handled by revoking/disabling the IAM credentials provided to the agent.
- **Implication**: To suspend an agent's ability to use this CLI, revoke its IAM credentials or deactivate its IAM user/role.
- **Recommendation**: No action required. AWS IAM natively supports credential revocation.
- **Evidence**: `lib/aws.js`

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity would be RISK-SAFETY, but surface-flag and archetype calibrations apply
- **Finding**: System exposes no write operations to callers and has no HTTP/RPC surface — compensation logic is not applicable. The CLI itself performs writes to AWS (deploying Lambda functions), but it is the caller, not the target system. Stateless-utility archetype further confirms INFO. The CLI does not implement saga patterns or compensation logic — a failed multi-region deployment leaves some regions deployed and others not. This is expected for a deployment tool.
- **Implication**: If a multi-region deployment partially fails, the operator must re-run the deployment or manually clean up. This is standard for deployment tooling.
- **Recommendation**: No action required for read-only agent scope.
- **Evidence**: `lib/main.js` (`deploy`, `_deployToRegion`)

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The CLI has no concurrency controls for write operations. Multiple concurrent `node-lambda deploy` invocations targeting the same Lambda function could race. AWS Lambda's `updateFunctionConfiguration` and `updateFunctionCode` have eventual consistency — the CLI polls for `LastUpdateStatus === 'Successful'` before updating code, which provides some ordering. However, since agent_scope is read-only, concurrent write controls are informational only.
- **Implication**: If agent_scope is expanded to write-enabled, operators should ensure only one agent instance deploys to a given function at a time (e.g., via external locks or deployment pipeline serialization).
- **Recommendation**: No action required for read-only scope.
- **Evidence**: `lib/main.js` (`_uploadExisting`)

### STATE-Q4: Circuit Breakers and Resilience

- **Severity**: INFO
- **Finding**: Extended question triggered — the CLI has external dependencies (AWS Lambda, S3, CloudWatch, CloudWatchEvents APIs). The CLI relies on the AWS SDK's built-in retry mechanism. In `_uploadExisting`, the code attaches `on('retry')` handlers that log retry attempts. The AWS SDK provides exponential backoff for throttled/transient errors. The `DEPLOY_TIMEOUT` (default 120000ms) is set as `aws.config.httpOptions.timeout` in `lib/aws.js`. However, there are no circuit breaker patterns (e.g., Resilience4j, Polly). For a CLI tool, this is expected — circuit breakers are a server-side pattern. The dev-library-application override downgrades this from RISK-SAFETY to INFO because the CLI is the caller, not the called system.
- **Implication**: The AWS SDK retry + timeout behavior is sufficient for a CLI tool. If an agent wraps this CLI, the agent's own resilience layer should handle repeated CLI failures.
- **Recommendation**: No action required. The AWS SDK provides adequate retry behavior for a CLI.
- **Evidence**: `lib/main.js` (`_uploadExisting` — `on('retry')`), `lib/aws.js` (`config.httpOptions.timeout`)

### STATE-Q5: Rate Limiting and Throttling

- **Severity**: INFO
- **Finding**: System exposes no HTTP/RPC surface — API-layer rate limiting is not applicable. The CLI is invoked as a subprocess. Rate limiting of the underlying AWS API calls is handled by AWS service-level throttling and the SDK's built-in retry/backoff.
- **Implication**: Agent orchestration layers should rate-limit how frequently they invoke the CLI to avoid hitting AWS API throttle limits.
- **Recommendation**: No action required at the CLI level.
- **Evidence**: `lib/main.js`, `lib/aws.js`

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The CLI has no configurable transaction limits. A single `deploy` invocation can deploy to multiple regions (comma-separated `--region` values), and there are no per-invocation limits on the number of regions or functions affected. Since agent_scope is read-only, blast radius controls are informational only.
- **Implication**: If agent_scope is expanded to write-enabled, consider limiting the number of regions per deployment invocation.
- **Recommendation**: No action required for read-only scope.
- **Evidence**: `lib/main.js` (`deploy`), `bin/node-lambda`

### HITL-Q3: Sandbox/Staging Environment

- **Severity**: INFO
- **Finding**: The CLI supports a `--endpoint` flag that allows deployment to custom endpoints such as LocalStack (`http://127.0.0.1:4574`). This effectively provides a sandbox/staging capability for testing deployments without affecting real AWS resources. The README documents this feature. The CLI also supports `--environment` to distinguish dev/staging/production configurations. Since this is a dev-library-application with no HTTP/RPC surface and no persistent data store, the override applies — staging environments are a consumer concern.
- **Implication**: Agents can use `--endpoint` to test deployments against LocalStack or similar local simulators before targeting production AWS accounts.
- **Recommendation**: No action required. The `--endpoint` flag provides adequate sandbox support.
- **Evidence**: `bin/node-lambda` (`--endpoint` option), `README.md`, `lib/aws.js` (`config.endpoint`)

### DATA-Q1: Sensitive Data Classification

- **Severity**: INFO
- **Finding**: Not a data-handling target — no PII/PHI/financial/credential data is stored, processed, or logged. The CLI passes AWS credentials to the AWS SDK but does not persist them. The `.env` files containing credentials are excluded from version control via `.gitignore`. The CLI does not store user data in any persistent data store.
- **Implication**: No data classification controls are needed for this tool.
- **Recommendation**: No action required.
- **Evidence**: `lib/.env.example`, `.gitignore`, `lib/main.js`

### DATA-Q2: Data Residency and Sovereignty ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity would be RISK-SAFETY, but surface-flag and archetype calibrations apply
- **Finding**: No persistent data store and no user-data logging — residency requirements do not apply. The CLI deploys code to user-specified AWS regions but does not store or process data itself. Stateless-utility archetype further confirms INFO.
- **Implication**: Data residency for deployed Lambda functions is controlled by the `--region` parameter, which is the operator's responsibility.
- **Recommendation**: No action required.
- **Evidence**: `bin/node-lambda` (`--region`), `lib/main.js`

### DATA-Q6: PII Redaction in Logs

- **Severity**: INFO
- **Finding**: System does not log user data and holds no user data — PII-in-logs risk is not applicable. The CLI outputs operational messages (`console.log`) about deployment progress, AWS API responses, and error messages. These do not contain user PII. AWS credentials are not logged (they are passed to the SDK, not printed). Stateless-utility archetype confirms INFO.
- **Implication**: No PII redaction is needed in this tool's output.
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js`

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality metrics or profiling. The CLI does not manage a dataset — it packages and deploys code. Data quality concepts do not apply.
- **Implication**: No action required.
- **Recommendation**: Not applicable for a deployment CLI.
- **Evidence**: No evidence found — absence is expected for this tool type.

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: CLI option names and environment variable names are semantically clear and self-documenting. Examples: `--functionName`, `--handler`, `--memorySize`, `--timeout`, `--region`, `--role`, `--runtime`, `--vpcSubnets`, `--vpcSecurityGroups`, `--kmsKeyArn`, `--tracingConfig`, `--layers`. Environment variables follow the `AWS_*` prefix convention. Code field names in `lib/main.js` are readable (`FunctionName`, `Code`, `Handler`, `Runtime`, `MemorySize`, `VpcConfig`, `Environment`, `DeadLetterConfig`, `TracingConfig`). No legacy abbreviations or opaque codes.
- **Implication**: Agent tool definitions can use the CLI option names directly — they are self-explanatory.
- **Recommendation**: No action required. Naming conventions are excellent.
- **Evidence**: `bin/node-lambda`, `lib/main.js`, `lib/.env.example`

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No data catalog or metadata layer. The CLI does not manage a dataset. The `README.md` serves as the primary documentation of all CLI options and environment variables. `CHANGELOG.md` documents version history.
- **Implication**: Agent tool builders can use the README as the primary reference for tool definition.
- **Recommendation**: No action required.
- **Evidence**: `README.md`, `CHANGELOG.md`

### OBS-Q1: Distributed Tracing and Structured Logging

- **Severity**: INFO
- **Finding**: Library/utility — tracing and correlation are consumer concerns. The CLI does include `aws-xray-sdk-core` as a dependency, but this is used to provide X-Ray tracing support for locally-run Lambda handlers (via the `run` command), not for tracing the CLI's own operations. The CLI's logging is unstructured `console.log` output without correlation IDs or JSON formatting.
- **Implication**: The X-Ray integration is a feature of the tool (enabling tracing for the Lambda functions it runs locally), not observability of the tool itself.
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js` (AWSXRay import, `_runHandler`), `package.json` (`aws-xray-sdk-core`)

### OBS-Q2: Alerting on Error Rates and Latency

- **Severity**: INFO
- **Finding**: Library/utility — alerting on error rates and latency is a consumer concern. The CLI is invoked as a subprocess; there are no persistent services to alert on. No CloudWatch alarms, PagerDuty, or OpsGenie integration exists (nor would one be expected for a CLI tool).
- **Implication**: Agent orchestration layers should monitor CLI exit codes and execution duration externally.
- **Recommendation**: No action required at the CLI level.
- **Evidence**: `.github/workflows/workflow.yml` (CI testing only, no deployment monitoring)

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No custom business metrics published. The CLI does not emit CloudWatch metrics or any telemetry about deployment outcomes. This is expected for an open-source CLI tool.
- **Implication**: Agent operators who want to track deployment success rates must instrument their own metrics externally.
- **Recommendation**: No action required.
- **Evidence**: No evidence found — absence is expected for this tool type.

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: The CLI exposes a command-line interface with four commands (`setup`, `run`, `package`, `deploy`) defined via `commander` in `bin/node-lambda`. The interface is documented in `README.md` with full `--help` output. The library also exports its API via `lib/main.js`. Since `has_http_rpc_surface` is `false` and the dev-library-application override applies, this is not a REST/GraphQL/AsyncAPI interface — agents would invoke the CLI as a subprocess or import the library module directly.
- **Gap**: No HTTP API surface. CLI commands and README documentation constitute the interface contract.
- **Recommendation**: Consider publishing a machine-readable CLI schema (e.g., JSON output of all commands and options).
- **Evidence**: `bin/node-lambda`, `README.md`, `lib/main.js`, `index.js`

#### API-Q2: Machine-Readable API Specification
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — machine-readable spec is not applicable. The CLI's interface is defined by `commander` option definitions in `bin/node-lambda` and documented in `README.md`. No OpenAPI, AsyncAPI, GraphQL schema, or Smithy model exists.
- **Gap**: N/A — not applicable for CLI tools.
- **Recommendation**: No action required.
- **Evidence**: `bin/node-lambda`, `README.md`

#### API-Q3: Structured Error Responses
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — structured error responses are not applicable. The CLI uses `process.exitCode` (0 for success, 1 for deploy failure, 254 for unsupported runtime, 255 for handler errors) and unstructured text output.
- **Gap**: N/A — not applicable for CLI tools without HTTP surface.
- **Recommendation**: Consider a `--json` output mode for agent consumption.
- **Evidence**: `lib/main.js`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The `deploy` command creates or updates Lambda functions. `_uploadExisting` uses `updateFunctionConfiguration` + `updateFunctionCode` (idempotent). `_uploadNew` uses `createFunction` with pre-check via `getFunction`. Since agent_scope is read-only, idempotency is informational only.
- **Gap**: None for read-only scope.
- **Recommendation**: No action required for read-only scope.
- **Evidence**: `lib/main.js` (`_uploadExisting`, `_uploadNew`, `_deployToRegion`)

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: CLI output is a mix of plain text log messages and JSON-serialized AWS API responses. The `run` command outputs `JSON.stringify(result)`. The `deploy` command outputs AWS SDK response objects. No consistent structured output format.
- **Gap**: No structured output mode.
- **Recommendation**: Consider adding a `--output json` flag.
- **Evidence**: `lib/main.js` (`_runHandler`, `_deployToRegion`, `_printDeployResults`)

#### API-Q6: Asynchronous Operation Support
- **Severity**: INFO
- **Finding**: Extended question triggered (deploy operation >30s, `DEPLOY_TIMEOUT` defaults to 120000ms). The CLI executes deployment synchronously with polling for `LastUpdateStatus === 'Successful'`. No async job submission pattern. Multi-region deployments run in parallel via `Promise.all`. This is expected for a CLI tool.
- **Gap**: No async job pattern. CLI blocks until completion.
- **Recommendation**: Agents should set appropriate timeouts (≥120 seconds).
- **Evidence**: `lib/main.js` (`deploy`, `_deployToRegion`, `_uploadExisting`), `bin/node-lambda` (`DEPLOY_TIMEOUT`)

#### API-Q7: Event Emission for State Changes
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has state changes (stateful-crud, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit documentation or headers. The CLI calls AWS APIs via the SDK, subject to AWS service-level rate limits. The AWS SDK provides built-in retry with exponential backoff.
- **Gap**: AWS API rate limits not documented in README.
- **Recommendation**: Document AWS API rate limits for agent operators.
- **Evidence**: `lib/main.js`, `lib/aws.js`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: The CLI delegates authentication entirely to the AWS SDK credential chain. It accepts credentials via environment variables, CLI options, AWS profiles, and the default SDK credential chain. Since `has_auth_surface` is `false`, machine identity authentication is a consumer/platform responsibility.
- **Gap**: The CLI does not manage identity. This is by design for a CLI tool.
- **Recommendation**: Document recommended credential patterns for agent use.
- **Evidence**: `bin/node-lambda`, `lib/aws.js`, `lib/.env.example`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: INFO
- **Finding**: The CLI uses whatever IAM credentials are provided and does not enforce scoped permissions itself. It requires permissions for Lambda, S3, CloudWatch, and CloudWatchEvents API operations. Since `has_auth_surface` is `false`, permission scoping is a consumer responsibility.
- **Gap**: No built-in permission scoping. Expected for CLI tools.
- **Recommendation**: Publish a recommended minimum IAM policy document in the README.
- **Evidence**: `lib/main.js`, `lib/s3_deploy.js`, `lib/s3_events.js`, `lib/schedule_events.js`, `lib/cloudwatch_logs.js`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: INFO
- **Finding**: The CLI does not enforce action-level authorization — it delegates to AWS IAM. AWS IAM natively supports action-level authorization. Since `has_auth_surface` is `false`, this is a platform responsibility.
- **Gap**: None — delegated to IAM.
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js`, `lib/aws.js`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: For stateless-utility archetype, downgraded to INFO. The CLI does not propagate identity — it uses provided AWS credentials directly. No on-behalf-of flow exists.
- **Gap**: None for CLI architecture.
- **Recommendation**: No action required.
- **Evidence**: `lib/aws.js`

#### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: Credentials sourced from environment variables and `.env` files. `.env.example` contains placeholder values (`AWS_ACCESS_KEY_ID=your_key`). `.gitignore` excludes `.env` and `deploy.env`. No Secrets Manager or Vault integration. AWS profiles (`--profile`) are supported, enabling IAM role-based credentials.
- **Gap**: No secrets management integration. Credentials managed via env vars and files.
- **Recommendation**: Document IAM role-based credentials as the recommended approach for agent usage.
- **Evidence**: `bin/node-lambda`, `lib/aws.js`, `lib/.env.example`, `.gitignore`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity would be RISK-SAFETY, but `has_auth_surface` is `false` AND `has_write_operations` is `false`
- **Finding**: System does not execute agent-invoked write operations — audit logging is a consumer responsibility. All CLI actions are logged by AWS CloudTrail in the target AWS account.
- **Gap**: None — audit is at the platform layer (CloudTrail).
- **Recommendation**: Ensure CloudTrail is enabled in target AWS accounts.
- **Evidence**: `lib/main.js`, `lib/aws.js`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: INFO
- **Finding**: System does not issue or enforce agent identities — suspension is a consumer responsibility. The CLI delegates identity to AWS IAM. Agent suspension is handled by revoking IAM credentials.
- **Gap**: None — delegated to IAM.
- **Recommendation**: No action required.
- **Evidence**: `lib/aws.js`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity would be RISK-SAFETY, but surface-flag and archetype calibrations apply
- **Finding**: System exposes no write operations to callers and has no HTTP/RPC surface — compensation logic is not applicable. Stateless-utility archetype confirms INFO. A failed multi-region deployment leaves some regions deployed and others not, which is expected for deployment tooling.
- **Gap**: None for read-only scope with no exposed write surface.
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js` (`deploy`, `_deployToRegion`)

#### STATE-Q2: Queryable Current State
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No concurrency controls for write operations. Multiple concurrent `node-lambda deploy` invocations could race. The CLI polls for `LastUpdateStatus === 'Successful'` which provides some ordering. Since agent_scope is read-only, this is informational only.
- **Gap**: None for read-only scope.
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js` (`_uploadExisting`)

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: INFO
- **Finding**: Extended question triggered — the CLI has external dependencies (AWS Lambda, S3, CloudWatch, CloudWatchEvents APIs). The CLI relies on the AWS SDK's built-in retry mechanism. `_uploadExisting` attaches `on('retry')` handlers. `DEPLOY_TIMEOUT` (120000ms) is set as `httpOptions.timeout`. No explicit circuit breaker patterns. For a CLI tool (caller, not called system), dev-library-application override downgrades from RISK-SAFETY to INFO.
- **Gap**: No circuit breaker patterns. AWS SDK retry is the only resilience mechanism.
- **Recommendation**: No action required. AWS SDK retry is adequate for a CLI.
- **Evidence**: `lib/main.js` (`_uploadExisting`), `lib/aws.js` (`config.httpOptions.timeout`)

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: INFO
- **Finding**: System exposes no HTTP/RPC surface — API-layer rate limiting is not applicable. The CLI is invoked as a subprocess. AWS API throttling is handled by the SDK's built-in retry/backoff.
- **Gap**: None — not applicable for CLI tools.
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js`, `lib/aws.js`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits. A single `deploy` can target multiple regions. Since agent_scope is read-only, blast radius controls are informational only.
- **Gap**: None for read-only scope.
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js` (`deploy`), `bin/node-lambda`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: INFO
- **Finding**: The CLI supports a `--endpoint` flag for custom endpoints (e.g., LocalStack `http://127.0.0.1:4574`) and `--environment` for dev/staging/production configurations. Dev-library-application override applies (`has_http_rpc_surface` is `false` AND `has_persistent_data_store` is `false`).
- **Gap**: None — staging is a consumer concern for CLI tools.
- **Recommendation**: No action required. `--endpoint` provides adequate sandbox support.
- **Evidence**: `bin/node-lambda` (`--endpoint`), `README.md`, `lib/aws.js`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO
- **Finding**: Not a data-handling target — no PII/PHI/financial/credential data is stored, processed, or logged. Dev-library-application override applies. The CLI passes AWS credentials to the SDK but does not persist them. `.env` files are excluded from version control via `.gitignore`.
- **Gap**: None — no data to classify.
- **Recommendation**: No action required.
- **Evidence**: `lib/.env.example`, `.gitignore`, `lib/main.js`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity would be RISK-SAFETY, but `has_persistent_data_store` is `false` AND `has_logging_of_user_data` is `false`. Stateless-utility archetype also confirms INFO.
- **Finding**: No persistent data store and no user-data logging — residency requirements do not apply. The CLI deploys code to user-specified AWS regions but does not store or process data itself.
- **Gap**: None — no data to govern.
- **Recommendation**: No action required.
- **Evidence**: `bin/node-lambda` (`--region`), `lib/main.js`

#### DATA-Q3: Selective Query Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has list/query endpoints with potentially unbounded results
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

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
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q6: PII Redaction in Logs
- **Severity**: INFO
- **Finding**: System does not log user data and holds no user data — PII-in-logs risk is not applicable. The CLI outputs operational messages about deployment progress and AWS API responses. No user PII is logged. AWS credentials are passed to the SDK, not printed. Stateless-utility archetype confirms INFO.
- **Gap**: None — no PII to redact.
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics or profiling. The CLI does not manage a dataset — it packages and deploys code. Data quality concepts do not apply.
- **Gap**: None — not applicable for deployment CLI.
- **Recommendation**: Not applicable.
- **Evidence**: No evidence found — absence is expected for this tool type.

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: The package uses semantic versioning (version `1.3.0` in `package.json`) and maintains a `CHANGELOG.md` with release notes dating back to `0.8.0`. The npm semver convention is the standard contract for CLI/library packages. However, there is no breaking change detection in CI — the CI pipeline runs lint and unit tests but does not validate that CLI option names, environment variable names, or exported API shapes have not changed in a breaking way. The CHANGELOG is manually maintained.
- **Gap**: No automated breaking change detection in CI. CLI option changes could silently break agent tool bindings.
- **Recommendation**: Add a snapshot-based CLI contract test (e.g., run `node-lambda --help` and diff against a golden snapshot) to the CI pipeline.
- **Evidence**: `package.json`, `CHANGELOG.md`, `.github/workflows/workflow.yml`, `.github/dependabot.yml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: CLI option names and environment variable names are semantically clear. Examples: `--functionName`, `--handler`, `--memorySize`, `--timeout`, `--region`, `--runtime`. Environment variables follow the `AWS_*` prefix convention. Code field names are readable. No legacy abbreviations or opaque codes.
- **Gap**: None — naming is excellent.
- **Recommendation**: No action required.
- **Evidence**: `bin/node-lambda`, `lib/main.js`, `lib/.env.example`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No data catalog or metadata layer. The CLI does not manage a dataset. `README.md` documents all CLI options and environment variables. `CHANGELOG.md` documents version history.
- **Gap**: None — not applicable for CLI tools.
- **Recommendation**: No action required.
- **Evidence**: `README.md`, `CHANGELOG.md`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: INFO
- **Finding**: Library/utility — tracing and correlation are consumer concerns. The CLI includes `aws-xray-sdk-core` as a dependency, but this is for X-Ray tracing support in locally-run Lambda handlers (via `run` command), not for tracing the CLI's own operations. Logging is unstructured `console.log` without correlation IDs.
- **Gap**: None — tracing is a consumer concern for CLI tools.
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js`, `package.json` (`aws-xray-sdk-core`)

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: INFO
- **Finding**: Library/utility — alerting is a consumer concern. The CLI is invoked as a subprocess with no persistent services. No CloudWatch alarms or monitoring integration exists.
- **Gap**: None — not applicable for CLI tools.
- **Recommendation**: No action required.
- **Evidence**: `.github/workflows/workflow.yml`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics published. The CLI does not emit CloudWatch metrics or telemetry. This is expected for an open-source CLI tool.
- **Gap**: None — not applicable for CLI tools.
- **Recommendation**: No action required.
- **Evidence**: No evidence found — absence is expected for this tool type.

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: N/A
- **Finding**: This is an `application` repository with `dev-library-application` override applied (library N/A mapping). Libraries, CLIs, and formatters do not own IaC for API gateways, IAM roles, or networking. No IaC files found in the repository.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: N/A
- **Finding**: This is an `application` repository with `dev-library-application` override applied (library N/A mapping). CI exists (`.github/workflows/workflow.yml`) with lint + unit tests on Node 22.x and 24.x across Ubuntu/Mac/Windows. CodeQL security scanning present. No API contract tests (expected — library build pipelines validate package contracts via semver, not API contracts).
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q3: Rollback Capability
- **Severity**: N/A
- **Finding**: This is an `application` repository with `dev-library-application` override applied (library N/A mapping). No deployed HTTP/RPC surface to roll back. Library rollback is handled via npm package version pinning by consumers.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q4: API Test Coverage
- **Severity**: N/A
- **Finding**: This is an `application` repository with `dev-library-application` override applied (library N/A mapping). Comprehensive test suite exists in `test/` using Mocha + Chai + `aws-sdk-mock`. Tests cover: `_params`, `_cleanDirectory`, `_fileCopy`, `_shouldUseNpmCi`, `_getNpmInstallCommand`, `_getYarnInstallCommand`, `_packageInstall`, `_postInstallScript`, `_zip`, `_archive`, `_readArchive`, `_listEventSourceMappings`, `_getStartingPosition`, `_updateEventSources`, `_updateScheduleEvents`, `_updateS3Events`, `_uploadNew`, `_uploadExisting`, `_alias`, `_setLogsRetentionPolicy`, `_deployToRegion`, `deploy`, and `_updateTags`.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: N/A
- **Finding**: This is an `application` repository with `dev-library-application` override applied (library N/A mapping). No persistent data stores — encryption at rest does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `bin/node-lambda` | API-Q1, API-Q2, API-Q3, API-Q4, API-Q5, API-Q6, API-Q8, AUTH-Q1, AUTH-Q2, AUTH-Q5, AUTH-Q6, STATE-Q6, HITL-Q3, DATA-Q2, DISC-Q2 |
| `index.js` | API-Q1 |
| `lib/main.js` | API-Q1, API-Q3, API-Q4, API-Q5, API-Q6, API-Q8, AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q6, STATE-Q1, STATE-Q3, STATE-Q4, STATE-Q5, STATE-Q6, DATA-Q1, DATA-Q2, DATA-Q6, DISC-Q1, DISC-Q2, OBS-Q1 |
| `lib/aws.js` | API-Q8, AUTH-Q1, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q6, AUTH-Q7, STATE-Q4, STATE-Q5, HITL-Q3 |
| `lib/cloudwatch_logs.js` | AUTH-Q2 |
| `lib/s3_deploy.js` | AUTH-Q2 |
| `lib/s3_events.js` | AUTH-Q2 |
| `lib/schedule_events.js` | AUTH-Q2 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/workflow.yml` | DISC-Q1, OBS-Q2 |
| `.github/workflows/codeql-analysis.yml` | (referenced in discovery, not cited in specific findings) |
| `.github/dependabot.yml` | DISC-Q1 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `package.json` | API-Q1, DISC-Q1, OBS-Q1 |
| `CHANGELOG.md` | DISC-Q1, DISC-Q3 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `lib/.env.example` | AUTH-Q1, AUTH-Q5, DATA-Q1, DISC-Q2 |
| `lib/deploy.env.example` | AUTH-Q5 |
| `.gitignore` | AUTH-Q5, DATA-Q1 |
| `README.md` | API-Q1, API-Q2, API-Q8, HITL-Q3, DISC-Q3 |

### Test Files
| File | Questions Referenced |
|------|---------------------|
| `test/main.js` | (referenced in discovery for test coverage assessment) |
| `test/node-lambda.js` | (referenced in discovery for test coverage assessment) |
| `test/cloudwatch_logs.js` | (referenced in discovery for test coverage assessment) |
| `test/s3_deploy.js` | (referenced in discovery for test coverage assessment) |
| `test/s3_events.js` | (referenced in discovery for test coverage assessment) |
| `test/schedule_events.js` | (referenced in discovery for test coverage assessment) |
