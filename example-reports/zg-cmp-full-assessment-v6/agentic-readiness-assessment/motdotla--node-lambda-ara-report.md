# Agentic Readiness Assessment Report

**Target**: motdotla--node-lambda
**Date**: 2025-05-08
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Service Archetype**: stateless-utility (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: javascript, serverless, cli
**Context**: Node.js CLI for deploying AWS Lambda functions.

**Archetype Justification**: This is a command-line tool (`node-lambda`) that packages and deploys Node.js Lambda functions via imperative AWS SDK calls. It has no HTTP server, no persistent data store, no authentication surface, and no write API of its own — it is a pure CLI utility.

**Dev-Library-Application Override**: This repository is classified as `application` (has source + bin entry point) but functions as a CLI deployment tool. Service archetype is `stateless-utility` and all 5 surface flags are `false`. Per Step 1.5, the `library` N/A mapping is applied for scoring purposes. The original `repo_type` value (`application`) is preserved.

**Surface flags**:
  - has_persistent_data_store: false
  - has_http_rpc_surface: false
  - has_auth_surface: false
  - has_write_operations: false
  - has_logging_of_user_data: false

---

## Readiness Profile: Agent-Ready

**BLOCKERs**: 0 | **RISK-SAFETY**: 0 | **RISK-QUALITY**: 0 | **INFOs**: 38

Cleared for autonomous operation. Instrument observability. Define scope explicitly. Run controlled pilot first.

**Classification Rationale**: This repo has 0 High findings, 0 Medium findings, and 0 safety-impact Medium findings. The matched rule is "0 High, ≤1 Medium → Agent-Ready". The V6 classification aligns with the V5 Readiness Profile: with 0 BLOCKERs and 0 RISK-SAFETY findings, the system is Agent-Ready. The overwhelming majority of questions resolve to INFO or N/A because this CLI tool does not expose an agent-callable surface — it IS a tool that agents might invoke, but the systems it interacts with (AWS Lambda, S3, CloudWatch) are the actual agent targets, not this CLI wrapper itself.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 0 |
| RISK-SAFETY | 0 |
| RISK-QUALITY | 0 |
| INFO | 38 |
| N/A | 5 |
| Not Evaluated (extended) | 0 |
| **Total** | **43** |

**Core Questions Evaluated**: 24 (19 resolved to INFO due to dev-library-application override + surface-flag downgrades; 5 N/A per library mapping)
**Extended Questions Triggered**: 14 (all resolved to INFO due to surface-flag/archetype calibration)
**Extended Questions Not Triggered**: 0
**Questions N/A (repo_type: application, library mapping override)**: 5
**Service Archetype**: stateless-utility (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

No BLOCKERs identified.

---

## RISKs

No RISKs identified.

---

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO
- **Finding**: This CLI tool exposes 4 commands (`setup`, `run`, `package`, `deploy`) via the `commander` library. There is no REST, GraphQL, or AsyncAPI interface. The CLI is invoked via `node-lambda <command>` and is not a network-accessible service.
- **Implication**: Agents invoking this tool would do so via shell execution (`node-lambda deploy`), not HTTP calls. Agent tool definitions would wrap CLI arguments, not API endpoints.
- **Recommendation**: If agent invocation is planned, document CLI arguments and exit codes in a machine-readable format (e.g., JSON schema of CLI options).
- **Evidence**: `bin/node-lambda`, `lib/main.js`, `package.json` (bin field)

### API-Q2: Machine-Readable API Specification

- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — machine-readable spec is not applicable. The CLI interface is defined via `commander` option declarations in `bin/node-lambda`.
- **Implication**: Agent tool generation would need to parse CLI help output or documentation rather than an OpenAPI spec.
- **Recommendation**: No action required for current use case.
- **Evidence**: `package.json`, `bin/node-lambda`

### API-Q3: Structured Error Responses

- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — structured error responses are not applicable. The CLI uses `process.exitCode` (0 for success, 1/254/255 for various errors) and `console.log`/`console.error` for output.
- **Implication**: Agents invoking via shell would rely on exit codes and stdout/stderr parsing.
- **Recommendation**: No action required for current use case.
- **Evidence**: `lib/main.js` (process.exitCode assignments)

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The CLI performs write operations against AWS (Lambda create/update, S3 putObject, CloudWatch Events putRule) which are largely idempotent by nature (create-or-update pattern). However, as agent_scope is read-only, this is informational.
- **Implication**: If agent_scope changes to write-enabled, the idempotent nature of AWS API operations provides natural safety.
- **Recommendation**: No action required for read-only scope.
- **Evidence**: `lib/main.js` (_uploadExisting, _uploadNew patterns)

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: CLI output is unstructured console.log text. AWS SDK responses (JSON) are logged to stdout but not in a consistent machine-parseable envelope.
- **Implication**: Agents parsing CLI output would need to handle unstructured text.
- **Recommendation**: Consider adding a `--json` output flag for machine consumption if agent invocation is planned.
- **Evidence**: `lib/main.js` (console.log throughout)

### API-Q6: Asynchronous Operation Support

- **Severity**: INFO
- **Finding**: The deploy command is inherently asynchronous — it waits for Lambda `LastUpdateStatus` to reach `Successful` via polling (up to 10 iterations with 3s delays). The CLI handles this internally.
- **Implication**: Agents invoking this CLI would block until completion. The internal polling is adequate for CLI use.
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js` (_uploadExisting method, polling loop)

### API-Q7: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: The CLI does not emit events or webhooks. It logs results to stdout upon completion.
- **Implication**: Agents would need to poll or parse stdout for completion signals.
- **Recommendation**: No action required for a CLI tool.
- **Evidence**: `lib/main.js` (_printDeployResults)

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No API surface to rate-limit. The CLI is subject to AWS API throttling on the AWS side, which is handled by SDK retry logic.
- **Implication**: Agent invocations are bounded by AWS service limits, not by this tool.
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js` (retry handlers on Lambda API calls)

### AUTH-Q1: Machine Identity Authentication

- **Severity**: INFO
- **Finding**: The CLI consumes AWS credentials (access key/secret, profile, session token) configured by the caller. It does not issue or validate identities itself — it delegates authentication entirely to the AWS SDK.
- **Implication**: Agent identity for AWS operations is managed at the AWS IAM layer, not within this tool. This is architecturally correct for a CLI.
- **Recommendation**: No action required. Agents invoking this CLI would authenticate via IAM roles/profiles passed as CLI arguments or environment variables.
- **Evidence**: `lib/aws.js` (SharedIniFileCredentials, accessKeyId/secretAccessKey), `lib/.env.example`

### AUTH-Q2: Scoped Permissions (Least Privilege)

- **Severity**: INFO
- **Finding**: The CLI operates under whatever IAM permissions the caller provides. It does not enforce permission scoping itself — that responsibility belongs to the IAM policy attached to the caller's credentials.
- **Implication**: An agent invoking this CLI should use an IAM role scoped to only the Lambda/S3/CloudWatch/IAM actions needed.
- **Recommendation**: Document minimum IAM policy required for each CLI command (deploy vs package vs run).
- **Evidence**: `lib/aws.js`, `lib/main.js` (AWS API calls: createFunction, updateFunctionConfiguration, putObject, etc.)

### AUTH-Q3: Action-Level Authorization

- **Severity**: INFO
- **Finding**: The CLI does not enforce action-level authorization. It exposes separate commands (setup, run, package, deploy) but authorization is delegated to AWS IAM policies on the credentials used.
- **Implication**: Action-level control is enforced at the IAM layer. Agents can be granted different IAM policies for read-only (describe) vs write (deploy) operations.
- **Recommendation**: No action required. IAM provides adequate action-level authorization.
- **Evidence**: `lib/main.js` (distinct CLI commands), `lib/aws.js`

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: INFO
- **Finding**: No HTTP/RPC surface and stateless-utility archetype — identity propagation is not applicable. The CLI uses provided credentials directly against AWS APIs.
- **Implication**: No multi-hop identity context needed for a CLI tool.
- **Recommendation**: No action required.
- **Evidence**: `lib/aws.js`

### AUTH-Q5: Credential Management

- **Severity**: INFO
- **Finding**: Credentials are sourced from environment variables, AWS profiles, or CLI arguments. The `.env.example` file contains placeholder values (`your_key`, `your_secret`). No hardcoded production credentials found. The `deploy.env.example` contains a placeholder secret (`mysecretval`). The tool supports AWS profile-based credentials which leverage the AWS credential chain.
- **Implication**: Credential management is delegated to the AWS credential provider chain and user-managed `.env` files. This is standard for CLI tools.
- **Recommendation**: No action required. The use of AWS profiles and environment variables is appropriate.
- **Evidence**: `lib/aws.js`, `lib/.env.example`, `lib/deploy.env.example`

### AUTH-Q6: Immutable Audit Logging ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO (surface-flag downgrade)
- **Finding**: System does not execute agent-invoked write operations — audit logging is a consumer responsibility. The CLI's AWS API calls are audited by CloudTrail on the AWS account side, not within this tool.
- **Implication**: Audit trails for operations performed by this CLI exist in CloudTrail, not in the tool itself.
- **Recommendation**: No action required. AWS CloudTrail provides the audit layer.
- **Evidence**: `lib/main.js` (AWS SDK calls), `lib/aws.js`

### AUTH-Q7: Agent Identity Suspension

- **Severity**: INFO
- **Finding**: System does not issue or enforce agent identities — suspension is a consumer responsibility. Agent identity lifecycle is managed via IAM (deactivate access keys, revoke role sessions).
- **Implication**: Suspending an agent using this CLI means revoking its AWS credentials at the IAM layer.
- **Recommendation**: No action required.
- **Evidence**: `lib/aws.js`

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO (surface-flag downgrade)
- **Finding**: System exposes no write operations of its own — compensation logic is not applicable. The CLI deploys to AWS Lambda which supports versioning and aliases for rollback at the AWS service layer.
- **Implication**: Rollback of deployments is handled via Lambda versioning ($LATEST, aliases) configured through this tool's `--lambdaVersion` flag.
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js` (_alias method, Publish parameter)

### STATE-Q2: Queryable Current State

- **Severity**: INFO
- **Finding**: The CLI does not expose queryable state. It performs operations and exits. AWS service state (Lambda function configuration) is queryable via AWS APIs directly.
- **Implication**: Agents needing to check current state would query AWS APIs directly, not through this CLI.
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js` (getFunction call used internally only)

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The CLI has no internal concurrency controls. Multiple concurrent invocations of `node-lambda deploy` could race on the same Lambda function, but AWS SDK handles this via `LastUpdateStatus` polling.
- **Implication**: AWS Lambda's own update serialization provides adequate concurrency control for deployments.
- **Recommendation**: No action required for read-only scope.
- **Evidence**: `lib/main.js` (LastUpdateStatus polling loop)

### STATE-Q4: Circuit Breakers and Resilience

- **Severity**: INFO
- **Finding**: The CLI uses AWS SDK built-in retry logic (retry event handlers on Lambda API calls). No explicit circuit breaker library is present, which is appropriate for a CLI tool that exits after each invocation.
- **Implication**: Resilience is adequate for single-invocation CLI usage. AWS SDK retry handles transient failures.
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js` (request.on('retry') handlers)

### STATE-Q5: Rate Limiting and Throttling

- **Severity**: INFO
- **Finding**: System exposes no HTTP/RPC surface — API-layer rate limiting is not applicable. AWS API throttling is enforced on the AWS side.
- **Implication**: Multiple agent invocations of this CLI are bounded by AWS API rate limits, not by this tool.
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js`

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The CLI has no configurable transaction limits. It deploys to however many regions are specified in the `--region` comma-separated list.
- **Implication**: For read-only scope, blast radius is not a concern. If write-enabled, the multi-region deploy capability could be scoped via IAM.
- **Recommendation**: No action required for read-only scope.
- **Evidence**: `lib/main.js` (deploy method, regions.split(','))

### STATE-Q7: Infrastructure Capacity for Agent Traffic

- **Severity**: INFO
- **Finding**: This is a CLI tool, not a running service. There is no infrastructure to size — each invocation is a local process that makes AWS API calls.
- **Implication**: Capacity concerns apply to the AWS APIs being called (Lambda, S3, CloudWatch), not to this tool.
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js`

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The CLI has no draft/pending state concept. The `package` command creates a local zip file (a form of staging), but there is no approval workflow before deploy.
- **Implication**: If human-in-the-loop is desired, the workflow would be: agent runs `package`, human reviews, then agent (or human) runs `deploy`.
- **Recommendation**: No action required for read-only scope. The two-step package→deploy pattern provides a natural approval gate if needed.
- **Evidence**: `lib/main.js` (package method vs deploy method)

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No approval gates configured. The CLI executes immediately upon invocation.
- **Implication**: Approval gates would be implemented at the orchestration layer (CI/CD pipeline approval steps, not within this tool).
- **Recommendation**: No action required for read-only scope.
- **Evidence**: `lib/main.js`

### HITL-Q3: Sandbox/Staging Environment

- **Severity**: INFO
- **Finding**: Library/utility — does not own staging environments. The CLI supports an `--environment` flag that appends to the function name (e.g., `myFunction-staging`), providing a naming convention for environment separation.
- **Implication**: Environment isolation is achieved via the `--environment` parameter and separate AWS accounts/regions, not via environments owned by this tool.
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js` (_params method: `program.environment`), `lib/.env.example` (AWS_ENVIRONMENT=development)

### DATA-Q1: Sensitive Data Classification ⚡

- **Severity**: INFO
- **Finding**: Not a data-handling target — no PII/PHI/financial/credential data is stored, processed, or logged. The CLI reads local config files and passes them to AWS APIs. It does not persist user data.
- **Implication**: Data classification concerns apply to the Lambda functions being deployed, not to this deployment tool.
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js`, `lib/.env.example`

### DATA-Q2: Data Residency and Sovereignty ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO (surface-flag downgrade)
- **Finding**: No persistent data store and no user-data logging — residency requirements do not apply. The CLI deploys to user-specified AWS regions but holds no data itself.
- **Implication**: Data residency is a concern for the deployed Lambda functions and their associated resources, not for this CLI tool.
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js` (region parameter), `lib/s3_deploy.js` (S3_LOCATION_POSSIBLE_VALUES)

### DATA-Q3: Selective Query Support

- **Severity**: INFO
- **Finding**: No data query surface. The CLI does not return data sets — it performs deployment operations.
- **Implication**: Not applicable for a deployment CLI.
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js`

### DATA-Q4: System of Record Designations

- **Severity**: INFO
- **Finding**: The CLI is not a system of record for any data. It reads configuration files and deploys artifacts to AWS.
- **Implication**: AWS Lambda service itself is the system of record for deployed function configurations.
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js`

### DATA-Q5: Temporal Metadata and Freshness

- **Severity**: INFO
- **Finding**: No persistent data store — temporal metadata is not applicable. The CLI operates on current configuration files at invocation time.
- **Implication**: Not applicable for a stateless CLI tool.
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js`

### DATA-Q6: PII Redaction in Logs

- **Severity**: INFO
- **Finding**: System does not log user data and holds no user data — PII-in-logs risk is not applicable. Console output includes AWS SDK responses (function ARNs, configuration) but no user PII.
- **Implication**: PII concerns apply to the deployed Lambda functions' logging, not to this CLI's output.
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js` (console.log of deployment results)

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data sets managed by this tool. Quality metrics are not applicable.
- **Implication**: Not applicable for a deployment CLI.
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js`

### DISC-Q1: Schema Versioning and API Contracts

- **Severity**: INFO
- **Finding**: The CLI uses semver versioning (currently 1.3.0 in `package.json`). CLI options are defined via `commander` in `bin/node-lambda`. No formal schema versioning or breaking change detection is present in CI. The npm package version serves as the contract version.
- **Implication**: CLI argument changes between versions could break agent tool definitions. Semver communicates intent but breaking changes are not automatically detected.
- **Recommendation**: Consider adding CLI argument stability tests to CI to detect breaking changes in the command interface.
- **Evidence**: `package.json` (version: "1.3.0"), `bin/node-lambda`

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: CLI option names are semantically meaningful and self-documenting (`--functionName`, `--memorySize`, `--timeout`, `--region`, `--handler`). No legacy codes or abbreviations requiring lookup.
- **Implication**: Agent tool definitions can map CLI options directly without translation.
- **Recommendation**: No action required. Naming is clear.
- **Evidence**: `lib/.env.example`, `lib/main.js` (_params method)

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No data catalog or metadata layer. Not applicable for a CLI deployment tool.
- **Implication**: Not applicable.
- **Recommendation**: No action required.
- **Evidence**: N/A — absence is expected for a CLI tool

### OBS-Q1: Distributed Tracing and Structured Logging

- **Severity**: INFO
- **Finding**: Library/utility — tracing and correlation are consumer concerns. The CLI integrates AWS X-Ray SDK for local Lambda execution tracing (when running handlers locally), but the CLI itself does not emit structured logs or trace IDs for its own operations.
- **Implication**: Debugging agent-initiated CLI invocations would rely on stdout/stderr capture and AWS CloudTrail for API calls.
- **Recommendation**: No action required. The X-Ray integration serves the local-run use case adequately.
- **Evidence**: `lib/main.js` (AWSXRay.Segment usage in _runHandler), `package.json` (aws-xray-sdk-core dependency)

### OBS-Q2: Alerting on Error Rates and Latency

- **Severity**: INFO
- **Finding**: Library/utility — alerting on error rates and latency is a consumer concern. The CLI exits with status codes (0, 1, 254, 255) that orchestration systems can monitor.
- **Implication**: Alerting on CLI invocation failures is the responsibility of the orchestrating system (CI/CD pipeline, agent framework).
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js` (process.exitCode assignments)

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No custom business metrics published. The CLI reports success/failure to stdout.
- **Implication**: Deployment success metrics would be tracked by the orchestrating system.
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js`

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: CLI tool with 4 commands (setup, run, package, deploy) via commander. No REST/GraphQL/AsyncAPI interface. Not a network-accessible service.
- **Gap**: No network API surface exists — this is by design for a CLI tool.
- **Recommendation**: If agent invocation is planned, document CLI arguments in a machine-readable format.
- **Evidence**: `bin/node-lambda`, `lib/main.js`, `package.json`

#### API-Q2: Machine-Readable API Specification
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — machine-readable spec is not applicable.
- **Gap**: N/A for a CLI tool
- **Recommendation**: No action required.
- **Evidence**: `package.json`

#### API-Q3: Structured Error Responses
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — structured error responses are not applicable. Uses exit codes (0, 1, 254, 255).
- **Gap**: N/A for a CLI tool
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: AWS operations performed by the CLI are largely idempotent (create-or-update pattern for Lambda functions).
- **Gap**: N/A for read-only scope
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js` (_uploadExisting, _uploadNew)

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: CLI output is unstructured console.log text mixed with JSON-stringified AWS responses.
- **Gap**: No consistent machine-parseable output envelope
- **Recommendation**: Consider adding `--json` output flag for machine consumption.
- **Evidence**: `lib/main.js`

#### API-Q6: Asynchronous Operation Support
- **Severity**: INFO
- **Finding**: Deploy command polls for completion internally (LastUpdateStatus loop). CLI blocks until done.
- **Gap**: No external async pattern needed for CLI invocation
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js` (_uploadExisting)

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: No events/webhooks emitted. Results logged to stdout.
- **Gap**: N/A for a CLI tool
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No API surface to rate-limit. AWS-side throttling applies.
- **Gap**: N/A for a CLI tool
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: CLI consumes AWS credentials (access key/secret, profile, session token) from caller. Does not issue or validate identities itself. Authentication is delegated to AWS SDK/IAM.
- **Gap**: No gap — this is architecturally correct for a CLI tool. Machine identity is managed at the IAM layer.
- **Recommendation**: No action required.
- **Evidence**: `lib/aws.js`, `lib/.env.example`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: INFO
- **Finding**: CLI operates under caller-provided IAM permissions. Does not enforce permission scoping — that is delegated to IAM policies.
- **Gap**: No minimum IAM policy documented for each CLI command
- **Recommendation**: Document minimum IAM policy per command.
- **Evidence**: `lib/aws.js`, `lib/main.js`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: INFO
- **Finding**: Authorization delegated to AWS IAM. Separate CLI commands (setup/run/package/deploy) naturally map to different IAM permission sets.
- **Gap**: No gap — IAM provides adequate action-level authorization.
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: Stateless-utility archetype — identity propagation not applicable. CLI uses provided credentials directly.
- **Gap**: N/A
- **Recommendation**: No action required.
- **Evidence**: `lib/aws.js`

#### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: Credentials sourced from environment variables, AWS profiles, or CLI arguments. Supports AWS credential provider chain. No hardcoded production credentials. Example files contain placeholders only.
- **Gap**: No gap — appropriate for a CLI tool
- **Recommendation**: No action required.
- **Evidence**: `lib/aws.js`, `lib/.env.example`, `lib/deploy.env.example`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO (surface-flag downgrade)
- **Finding**: System does not execute agent-invoked write operations — audit logging is a consumer responsibility. AWS CloudTrail audits all API calls made by this CLI.
- **Gap**: N/A — audit exists at the AWS platform layer
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js`, `lib/aws.js`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: INFO
- **Finding**: System does not issue or enforce agent identities — suspension is a consumer responsibility. Managed via IAM credential revocation.
- **Gap**: N/A
- **Recommendation**: No action required.
- **Evidence**: `lib/aws.js`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO (surface-flag downgrade)
- **Finding**: System exposes no write operations of its own. Lambda versioning/aliases provide rollback at the AWS layer.
- **Gap**: N/A
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js` (_alias method)

#### STATE-Q2: Queryable Current State
- **Severity**: INFO
- **Finding**: CLI does not expose queryable state. AWS APIs provide current state for deployed functions.
- **Gap**: N/A for a CLI tool
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js`

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No internal concurrency controls. AWS Lambda's update serialization provides adequate protection.
- **Gap**: N/A for read-only scope
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: INFO
- **Finding**: Uses AWS SDK built-in retry logic. No explicit circuit breaker library — appropriate for a CLI tool.
- **Gap**: N/A — SDK retry is adequate
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js` (retry event handlers)

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: INFO
- **Finding**: System exposes no HTTP/RPC surface — API-layer rate limiting is not applicable.
- **Gap**: N/A
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits. Multi-region deploy controlled by comma-separated region parameter.
- **Gap**: N/A for read-only scope
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: INFO
- **Finding**: CLI tool, not a running service. No infrastructure to size.
- **Gap**: N/A
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js`

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No draft/pending state. The `package` command provides a natural staging step before `deploy`.
- **Gap**: N/A for read-only scope
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js`

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No approval gates. CLI executes immediately upon invocation.
- **Gap**: N/A for read-only scope
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js`

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: INFO
- **Finding**: Library/utility — does not own staging environments. Supports `--environment` flag for environment separation via function naming.
- **Gap**: N/A
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js`, `lib/.env.example`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification ⚡
- **Severity**: INFO
- **Finding**: Not a data-handling target — no PII/PHI/financial/credential data is stored, processed, or logged by this tool.
- **Gap**: N/A
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js`, `lib/.env.example`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO (surface-flag downgrade)
- **Finding**: No persistent data store and no user-data logging — residency requirements do not apply.
- **Gap**: N/A
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js`, `lib/s3_deploy.js`

#### DATA-Q3: Selective Query Support
- **Severity**: INFO
- **Finding**: No data query surface. CLI performs deployment operations, not data retrieval.
- **Gap**: N/A
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js`

#### DATA-Q4: System of Record Designations
- **Severity**: INFO
- **Finding**: Not a system of record. AWS Lambda service is the SoR for function configurations.
- **Gap**: N/A
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js`

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: INFO
- **Finding**: No persistent data store — temporal metadata not applicable.
- **Gap**: N/A
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js`

#### DATA-Q6: PII Redaction in Logs
- **Severity**: INFO
- **Finding**: System does not log user data and holds no user data — PII-in-logs risk is not applicable.
- **Gap**: N/A
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data sets managed. Quality metrics not applicable.
- **Gap**: N/A
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: INFO
- **Finding**: Uses semver (1.3.0). CLI options defined via commander. No formal breaking change detection in CI for CLI arguments.
- **Gap**: No automated CLI argument stability testing
- **Recommendation**: Consider adding CLI argument stability tests.
- **Evidence**: `package.json`, `bin/node-lambda`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: CLI options use clear, self-documenting names (`--functionName`, `--memorySize`, `--timeout`, `--region`).
- **Gap**: No gap
- **Recommendation**: No action required.
- **Evidence**: `lib/.env.example`, `lib/main.js`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No data catalog. Not applicable for a CLI deployment tool.
- **Gap**: N/A
- **Recommendation**: No action required.
- **Evidence**: N/A

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: INFO
- **Finding**: Library/utility — tracing and correlation are consumer concerns. X-Ray SDK integrated for local Lambda handler execution tracing.
- **Gap**: N/A — library obligation is trace propagation which X-Ray integration satisfies
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js`, `package.json` (aws-xray-sdk-core)

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: INFO
- **Finding**: Library/utility — alerting is a consumer concern. CLI provides exit codes for orchestration-layer monitoring.
- **Gap**: N/A
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics published. Success/failure reported to stdout.
- **Gap**: N/A for a CLI tool
- **Recommendation**: No action required.
- **Evidence**: `lib/main.js`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: N/A
- **Finding**: This is a `application` repository with library N/A mapping applied (dev-library-application override). This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: N/A
- **Finding**: This is a `application` repository with library N/A mapping applied (dev-library-application override). This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q3: Rollback Capability
- **Severity**: N/A
- **Finding**: This is a `application` repository with library N/A mapping applied (dev-library-application override). This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q4: API Test Coverage
- **Severity**: N/A
- **Finding**: This is a `application` repository with library N/A mapping applied (dev-library-application override). This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: N/A
- **Finding**: This is a `application` repository with library N/A mapping applied (dev-library-application override). This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `lib/main.js` | API-Q1, API-Q3, API-Q4, API-Q5, API-Q6, API-Q7, API-Q8, AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q6, STATE-Q1, STATE-Q2, STATE-Q3, STATE-Q4, STATE-Q5, STATE-Q6, STATE-Q7, HITL-Q1, HITL-Q2, HITL-Q3, DATA-Q1, DATA-Q2, DATA-Q3, DATA-Q4, DATA-Q5, DATA-Q6, DATA-Q7, OBS-Q1, OBS-Q2, OBS-Q3, DISC-Q1, DISC-Q2 |
| `lib/aws.js` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q6, AUTH-Q7 |
| `lib/s3_deploy.js` | DATA-Q2 |
| `lib/cloudwatch_logs.js` | (referenced in archetype detection) |
| `lib/schedule_events.js` | (referenced in archetype detection) |
| `lib/s3_events.js` | (referenced in archetype detection) |
| `index.js` | (sample Lambda handler, archetype detection) |
| `bin/node-lambda` | API-Q1, API-Q2, DISC-Q1 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/workflow.yml` | (referenced in archetype detection — CI pipeline structure) |
| `.github/workflows/codeql-analysis.yml` | (referenced in archetype detection — security scanning) |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `package.json` | API-Q1, API-Q2, DISC-Q1, OBS-Q1 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `lib/.env.example` | AUTH-Q1, AUTH-Q5, DATA-Q1, HITL-Q3, DISC-Q2 |
| `lib/deploy.env.example` | AUTH-Q5 |
