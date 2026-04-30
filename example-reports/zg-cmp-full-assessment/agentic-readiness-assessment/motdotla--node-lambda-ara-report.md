# Agentic Readiness Assessment Report

**Target**: node-lambda (https://github.com/motdotla/node-lambda)
**Date**: 2026-04-29
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Service Archetype**: stateless-utility (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: javascript, serverless, cli
**Context**: Node.js CLI for deploying AWS Lambda functions.

**Archetype Justification**: This is a CLI tool distributed as an npm package with no database connections, no persistent state, no REST/GraphQL API endpoints, and no user-specific data storage. It packages and deploys code to AWS Lambda using the AWS SDK — a pure utility tool.

---

## Readiness Profile: Not Agent-Integrable

**BLOCKERs**: 3 | **RISK-SAFETY**: 9 | **RISK-QUALITY**: 11 | **INFOs**: 13

Exclude from agent toolset or plan major remediation before re-evaluation.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 3 |
| RISK-SAFETY | 9 |
| RISK-QUALITY | 11 |
| INFO | 13 |
| N/A | 0 |
| Not Evaluated (extended) | 7 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 2 (API-Q6, STATE-Q4)
**Extended Questions Not Triggered**: 7 (API-Q7, STATE-Q2, STATE-Q7, DATA-Q3, DATA-Q4, DATA-Q5, ENG-Q5)
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: stateless-utility (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### API-Q1: Documented API Interface

- **Severity**: BLOCKER
- **Finding**: The application is a command-line tool built with `commander.js` that exposes four CLI commands: `setup`, `run`, `package`, and `deploy`. It does **not** expose any REST, GraphQL, or AsyncAPI interface. There are no HTTP server listeners, no Express/Fastify/Koa routes, and no API Gateway integration in the codebase. The only programmatic interface is the Node.js module export (`lib/main.js` exports a `Lambda` class instance), which is not a documented API surface suitable for agent tool binding. An agent would need to invoke shell commands (`node-lambda deploy ...`) or import the module directly — both are brittle, non-auditable integration patterns.
- **Gap**: No API interface exists for agent consumption. The CLI is designed for human use with command-line arguments and environment variables. There is no HTTP endpoint, no RPC interface, and no machine-callable API.
- **Remediation**:
  - **Immediate**: Wrap the core `Lambda` class methods (`deploy`, `package`, `run`, `setup`) in a lightweight REST API (e.g., Express or Fastify) with JSON request/response bodies. Alternatively, create a well-documented Node.js SDK with typed interfaces that agents can call programmatically.
  - **Target State**: A documented HTTP API or programmatic SDK with structured JSON inputs and outputs, suitable for agent tool definition.
  - **Estimated Effort**: Medium (2–4 weeks for API wrapper + OpenAPI spec)
  - **Dependencies**: API-Q2 (machine-readable spec), API-Q3 (structured errors)
- **Evidence**: `bin/node-lambda` (commander.js CLI definition), `lib/main.js` (Lambda class with CLI-oriented methods), `package.json` (`"bin": {"node-lambda": "./bin/node-lambda"}`)

---

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: The CLI authenticates to AWS using human-style credentials passed via CLI arguments (`--accessKey`, `--secretKey`, `--sessionToken`, `--profile`) or environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_PROFILE`, `AWS_SESSION_TOKEN`). In `lib/aws.js`, credentials are configured directly on the AWS SDK via `aws.config.credentials = new aws.SharedIniFileCredentials({profile})` or `awsSecurity.accessKeyId = config.accessKey`. There is no support for OAuth2 client credentials, mTLS, API keys with principal attribution, or any machine identity mechanism. There is no way to attribute which agent made a specific call — the credential holder is the only identity.
- **Gap**: No machine identity authentication. No agent identity attribution. The CLI assumes a single human operator providing credentials directly. An agent using this tool would need to pass raw AWS credentials, which cannot be attributed to a specific agent instance in audit logs.
- **Remediation**:
  - **Immediate**: Add support for IAM role assumption with external ID and session name tagging (e.g., `agent-deployment-bot-instance-123`). This enables principal attribution in CloudTrail logs via the session name.
  - **Target State**: Support for AWS STS AssumeRole with session tags that identify the calling agent, enabling per-agent audit trails in CloudTrail.
  - **Estimated Effort**: Medium (1–2 weeks)
  - **Dependencies**: AUTH-Q6 (audit logging)
- **Evidence**: `lib/aws.js` (credential configuration), `bin/node-lambda` (CLI argument definitions for `--accessKey`, `--secretKey`, `--profile`), `lib/.env.example` (`AWS_ACCESS_KEY_ID=your_key`, `AWS_SECRET_ACCESS_KEY=your_secret`)

---

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: The CLI handles sensitive data including AWS access keys, secret keys, session tokens, IAM role ARNs, KMS key ARNs, VPC security group IDs, and deploy environment variables (which may contain application secrets via `deploy.env`). In `lib/.env.example`, credentials are shown as `AWS_ACCESS_KEY_ID=your_key` and `AWS_SECRET_ACCESS_KEY=your_secret`. In `lib/deploy.env.example`, `SECRET_VARIABLE=mysecretval` demonstrates secret handling. The `_params` method in `lib/main.js` reads `configFile` (deploy.env) and passes all key-value pairs as Lambda environment variables. None of this data is classified, tagged, or given field-level protection. The CLI passes all parameters including credentials through `console.log(params)` in `_deployToRegion` without any filtering.
- **Gap**: No sensitive data classification or tagging at the field level. Credentials and secrets are handled as plain text throughout the application. No distinction between sensitive parameters (access keys, secrets) and non-sensitive parameters (function name, memory size).
- **Remediation**:
  - **Immediate**: Classify credential fields (accessKey, secretKey, sessionToken, configFile contents) as sensitive and implement masking in all logging paths. Add metadata annotations to distinguish sensitive vs. non-sensitive parameters.
  - **Target State**: Field-level sensitivity classification with masking in logs, and integration with AWS Secrets Manager for credential retrieval instead of plain-text environment variables.
  - **Estimated Effort**: Medium (1–2 weeks for classification + log masking; 2–4 weeks for Secrets Manager integration)
  - **Dependencies**: DATA-Q6 (PII redaction in logs), AUTH-Q5 (credential management)
- **Evidence**: `lib/.env.example` (plain-text credential patterns), `lib/deploy.env.example` (`SECRET_VARIABLE=mysecretval`), `lib/main.js` (`console.log(params)` in `_deployToRegion`, `_params` method reading configFile)

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The CLI provides no application-level permission scoping. Once credentials are provided (via `--accessKey`/`--secretKey` or `--profile`), the CLI has access to all AWS permissions granted to those credentials. In `lib/aws.js`, the full credentials are set on the global `aws.config` object without any restriction. The `deploy` command calls `lambda.createFunction`, `lambda.updateFunctionConfiguration`, `lambda.updateFunctionCode`, `s3.createBucket`, `s3.putObject`, `cloudwatchevents.putRule`, `lambda.addPermission`, and more — all with the same credential set. There is no per-command permission boundary.
- **Gap**: No scoped permissions at the application layer. An agent given credentials to deploy one Lambda function has the same credentials to deploy to any function, create S3 buckets, modify CloudWatch Events rules, and manage IAM permissions — limited only by the IAM policy attached to the credentials, not by the CLI.
- **Compensating Controls**:
  - Use tightly scoped IAM policies with resource-level conditions (e.g., restrict to specific Lambda function ARNs, specific S3 bucket names) for the credentials provided to the agent.
  - Use AWS Organizations Service Control Policies (SCPs) as a guardrail.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement a permission model within the CLI that validates the intended operation against an allow-list before executing AWS API calls. At minimum, add a `--dry-run` mode that shows what operations would be performed without executing them.
- **Evidence**: `lib/aws.js` (global credential configuration), `lib/main.js` (`_deployToRegion` calls multiple AWS services with same credentials)

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The CLI has no internal authorization model. All four commands (`setup`, `run`, `package`, `deploy`) are available to any user with credentials. There are no role-based restrictions, no command-level access control, and no configuration to restrict which operations an agent can perform. In `bin/node-lambda`, each command is registered with `program.command()` and `.action()` with no authorization check. An agent with access to this CLI can execute `deploy` (which modifies Lambda functions, creates S3 buckets, and updates event sources) with the same ease as `run` (which only executes locally).
- **Gap**: No action-level authorization. Cannot restrict an agent to read-only operations (e.g., `run` only) while blocking write operations (e.g., `deploy`).
- **Compensating Controls**:
  - Wrap CLI invocations in a proxy layer that validates the command before execution.
  - Use IAM policies to restrict write operations at the AWS API level, making `deploy` fail at the AWS layer even if the CLI attempts it.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a configuration-driven command allow-list (e.g., `--allowed-commands run,package`) that restricts which CLI commands can be executed in a given context.
- **Evidence**: `bin/node-lambda` (all commands available without authorization checks)

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The CLI has no application-level audit logging. All output goes to `console.log` and `console.error`, which are ephemeral stdout/stderr streams. There is no structured log file, no immutable log storage, and no log-level configuration. The `_deployToRegion` method logs `console.log(params)` which includes deployment parameters, but this is informational output, not an audit trail. AWS CloudTrail would capture the underlying AWS API calls made by the SDK, but the CLI itself does not log the authenticated principal, the CLI command executed, or the parameters in an auditable format.
- **Gap**: No immutable audit trail for CLI operations. Cannot determine which agent instance executed which command with which parameters after the fact. CloudTrail provides partial coverage (AWS API calls only), but CLI-level context (command name, original parameters, user intent) is lost.
- **Compensating Controls**:
  - Pipe all CLI stdout/stderr to a log aggregation service (e.g., CloudWatch Logs) with immutable retention.
  - Enable AWS CloudTrail for the account to capture underlying API calls.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add structured JSON logging with fields for: timestamp, command, parameters (with sensitive fields masked), caller identity, and outcome. Write logs to a configurable output (file, CloudWatch Logs, or S3) with retention policy.
- **Evidence**: `lib/main.js` (`console.log` used throughout), `lib/aws.js` (no audit logging)

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The CLI has no concept of agent identities and therefore no mechanism to suspend or revoke a specific agent's access. Access is controlled entirely by AWS credentials — to revoke an agent's access, you must rotate or delete the IAM user/role credentials it uses, which may affect other users or services sharing those credentials. There are no API key management endpoints, no identity registry, and no disable mechanism in the CLI.
- **Gap**: No agent-specific identity suspension. Revoking access requires IAM credential changes outside the application.
- **Compensating Controls**:
  - Assign each agent instance its own IAM user or assumed role with unique credentials, so revoking one agent's access does not affect others.
  - Use short-lived STS session tokens so credentials expire automatically.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: If the CLI is wrapped in an API layer, implement API key-per-agent with revocation capability. For direct CLI use, enforce unique IAM roles per agent with session expiry.
- **Evidence**: `lib/aws.js` (no identity management), `bin/node-lambda` (no agent identity concept)

#### STATE-Q1: Compensation and Rollback ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The deploy process in `_deployToRegion` is a multi-step sequential operation: (1) archive code → (2) upload to S3 (if `deployUseS3`) → (3) create or update Lambda function (first `updateFunctionConfiguration`, wait for success, then `updateFunctionCode`) → (4) update event source mappings → (5) update schedule events → (6) update S3 events → (7) set CloudWatch Logs retention → (8) create alias. If any step fails after step 3, the Lambda function configuration may be updated but event sources, schedules, or other configurations may be inconsistent. The `_uploadExisting` method performs `updateFunctionConfiguration` followed by `updateFunctionCode` with a polling loop waiting for `LastUpdateStatus === 'Successful'`, but no compensation if the code update fails after config was already changed. There is retry logic (`on('retry')`) but no rollback or compensation.
- **Gap**: No rollback or compensation for partial deployment failures. A failed deploy can leave the Lambda function in an inconsistent state (e.g., configuration updated but code not updated, or function updated but event sources not).
- **Compensating Controls**:
  - Implement a pre-deploy snapshot (capture current function configuration and code) that can be restored manually.
  - Use Lambda function versioning and aliases to maintain the previous known-good version alongside the new deployment.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement a `--rollback` command that restores the previous Lambda function version. Use Lambda versioning (`Publish: true`) and aliases to point to the last known-good version, with automatic rollback on deploy failure.
- **Evidence**: `lib/main.js` (`_uploadExisting` method — sequential updates without compensation, `_deployToRegion` — multi-step process with no rollback)

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The CLI calls multiple AWS services (Lambda, S3, CloudWatch Events, CloudWatch Logs, IAM) via the AWS SDK. The AWS SDK provides built-in retry logic with exponential backoff, and the code adds `on('retry')` event handlers that log retry messages. However, there are no circuit breakers to prevent cascading failures. The `_deployToRegion` method makes 6+ sequential AWS API calls — if the Lambda service is degraded, the CLI will keep retrying each call according to SDK defaults without any circuit-breaking behavior. In `_uploadExisting`, there is a polling loop (`for (let i = 0; i < 10; i++)`) with a 3-second sleep waiting for `LastUpdateStatus`, but this is a fixed-iteration wait, not a circuit breaker. Multi-region deploys (`regions.map(region => _deployToRegion(...))`) run in parallel via `Promise.all`, so a failure in one region does not stop others, but there is no isolation mechanism.
- **Gap**: No circuit breaker pattern. A degraded AWS service will cause the CLI to hang or fail slowly, potentially causing an agent to retry the entire deployment sequence repeatedly.
- **Compensating Controls**:
  - Set a maximum deploy timeout (already exists: `--deployTimeout`, default 120000ms) and ensure the agent respects it.
  - Implement agent-side circuit breaking (stop retrying after N consecutive deploy failures).
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a circuit breaker around the deploy workflow that fails fast after detecting persistent AWS service errors. Consider using the `opossum` or similar Node.js circuit breaker library.
- **Evidence**: `lib/main.js` (`_uploadExisting` — retry handlers, polling loop; `_deployToRegion` — sequential AWS calls without circuit breaking), `lib/aws.js` (`deployTimeout` configuration)

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The CLI makes direct AWS API calls with no application-level rate limiting or throttling. When deploying to multiple regions (`program.region` defaults to `'us-east-1,us-west-2,eu-west-1'`), `Promise.all` fires parallel deployments to all regions simultaneously. Each region deployment makes 6+ API calls. There is no queue, no concurrency limiter, and no rate control. The AWS SDK has service-level throttling (which returns `ThrottlingException`), but the CLI does not proactively limit request rates. An agent invoking this CLI repeatedly could generate a high volume of AWS API calls and hit service limits.
- **Gap**: No application-level rate limiting. No throttling controls for AWS API calls. An agent loop invoking `deploy` repeatedly could exhaust AWS API quotas.
- **Compensating Controls**:
  - Use AWS Service Quotas and request rate limits at the AWS account level.
  - Implement agent-side rate limiting (e.g., minimum interval between deploy invocations).
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a concurrency limiter for multi-region deployments (e.g., deploy to 1 region at a time instead of parallel). Add a configurable minimum interval between deployments.
- **Evidence**: `lib/main.js` (`deploy` method — `Promise.all(regions.map(...))` fires parallel region deployments), `bin/node-lambda` (`AWS_REGION` default is `'us-east-1,us-west-2,eu-west-1'`)

#### DATA-Q2: Data Residency and Sovereignty ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The CLI deploys Lambda functions to user-specified AWS regions. The default region string is `'us-east-1,us-west-2,eu-west-1'` (defined in `bin/node-lambda`). There are no data residency controls — the user (or agent) can deploy to any region. The deploy environment variables (`deploy.env`) may contain sensitive data that gets set as Lambda environment variables in the target region. The code in `_params` reads the config file and passes all values as `params.Environment.Variables`. There is no validation that the target region complies with data residency requirements for the data being deployed.
- **Gap**: No data residency validation or controls. An agent could deploy application secrets to a region that violates compliance requirements (e.g., deploying EU customer data processing code with embedded configuration to a US region).
- **Compensating Controls**:
  - Restrict the `--region` parameter to approved regions via agent configuration.
  - Use AWS Organizations SCPs to deny Lambda operations in non-approved regions.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a configurable region allow-list that restricts which regions the CLI can deploy to. Validate the target region against the allow-list before executing any AWS API calls.
- **Evidence**: `bin/node-lambda` (`AWS_REGION` default `'us-east-1,us-west-2,eu-west-1'`), `lib/main.js` (`_params` passes config file contents to `Environment.Variables`)

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The CLI logs deployment parameters to stdout via `console.log(params)` in the `_deployToRegion` method. The `params` object contains sensitive fields including `Environment.Variables` (from `deploy.env`, which may contain secrets), `Role` (IAM role ARN), `VpcConfig` (subnet and security group IDs), `KMSKeyArn`, and `DeadLetterConfig.TargetArn`. Additionally, `_uploadExisting` and `_uploadNew` results are logged via `console.log(results)`. The `_printDeployResults` method recursively logs all deploy results. There is no log scrubbing, no PII masking, and no sensitive field filtering anywhere in the codebase.
- **Gap**: No PII or sensitive data redaction in any logging path. Credentials, secrets, and infrastructure details are logged in plain text to stdout.
- **Compensating Controls**:
  - Redirect CLI stdout to a log aggregation service with PII detection and masking (e.g., Amazon Macie on log storage).
  - Use the `--silent` flag on the `deploy` command to suppress all console output (but this also suppresses useful non-sensitive output).
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement a log sanitizer that masks sensitive fields (`Environment.Variables`, `accessKey`, `secretKey`, `sessionToken`, `KMSKeyArn`) before logging. Apply the sanitizer to all `console.log` calls that output parameters or results.
- **Evidence**: `lib/main.js` (`_deployToRegion`: `console.log(params)`, `console.log(results)`; `_printDeployResults` recursive logging)

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, GraphQL schema, or equivalent machine-readable specification exists. The CLI interface is documented only in `README.md` (human-readable usage instructions and command descriptions) and via `commander.js` `--help` output. The `package.json` defines the CLI entry point (`"bin": {"node-lambda": "./bin/node-lambda"}`) but no API schema.
- **Gap**: No machine-readable specification for the CLI interface. Agent tool definitions must be manually authored from README documentation, with no automated way to keep them synchronized with CLI changes.
- **Compensating Controls**:
  - Manually author an agent tool definition based on the CLI arguments and document it alongside the README.
  - Auto-generate a tool schema from the commander.js option definitions in `bin/node-lambda`.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: If an API wrapper is built (per API-Q1 remediation), generate an OpenAPI specification. For CLI use, create a JSON schema document describing all commands, their parameters, types, and defaults — extractable from the commander.js definitions.
- **Evidence**: `README.md` (human-readable docs), `bin/node-lambda` (commander.js option definitions), no OpenAPI/AsyncAPI/GraphQL/Smithy files found

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Error handling uses `console.error()` for text messages and `process.exitCode` for exit codes. In `lib/main.js`, errors are caught and logged via `console.log(err)` (e.g., in `deploy` catch block: `process.exitCode = 1; console.log(err)`). The `run` command sets `process.exitCode = 255` for errors. There are no structured error codes, no error categorization (retriable vs. terminal), and no machine-readable error format. AWS SDK errors propagate with their original error codes (e.g., `ResourceNotFoundException`, `ResourceConflictException`) but these are logged as unstructured text, not returned in a consistent JSON format.
- **Gap**: No structured error responses. An agent cannot distinguish retriable errors (AWS throttling, network timeout) from terminal errors (invalid parameters, missing permissions) without parsing unstructured console output.
- **Compensating Controls**:
  - Parse exit codes (0 = success, 1 = deploy error, 254 = unsupported runtime, 255 = handler error) as a basic error classification.
  - Implement agent-side error parsing for known AWS SDK error patterns in stdout/stderr.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement a structured error output mode (e.g., `--output json`) that returns errors as JSON objects with fields: `errorCode`, `errorMessage`, `retryable`, `command`, `region`.
- **Evidence**: `lib/main.js` (`deploy` catch: `process.exitCode = 1; console.log(err)`; `run`: `process.exitCode = 255`; `_isFunctionDoesNotExist` checks error codes internally but doesn't expose them)

#### API-Q6: Asynchronous Operation Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The `deploy` command is a long-running synchronous operation with a default timeout of 120,000ms (2 minutes). It performs archiving, uploading, and multi-region deployment sequentially. The `_uploadExisting` method includes a polling loop (up to 10 iterations × 3-second sleep = 30 seconds) waiting for `LastUpdateStatus === 'Successful'`. There is no asynchronous job submission pattern — the CLI blocks until the entire deployment completes or fails. There are no job IDs, no polling endpoints, and no webhook callbacks. An agent calling this tool must wait synchronously for the full deployment duration.
- **Gap**: No async patterns for the long-running deploy operation. An agent must block for up to 2+ minutes per deployment, with no way to check progress or cancel in-flight.
- **Compensating Controls**:
  - Implement agent-side timeout handling to avoid indefinite blocking.
  - Run the CLI in a background process and poll for completion via process status.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement a `--async` mode that submits the deployment as a background job and returns a job ID. Add a `status` command to check deployment progress by job ID.
- **Evidence**: `lib/main.js` (`deploy` method — synchronous `await`, `_uploadExisting` — polling loop with 3s sleep, `DEPLOY_TIMEOUT` default 120000ms in `bin/node-lambda`)

#### AUTH-Q5: Credential Management — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Credentials are managed through environment variables and `.env` files. The `lib/.env.example` shows `AWS_ACCESS_KEY_ID=your_key` and `AWS_SECRET_ACCESS_KEY=your_secret` patterns. The `lib/deploy.env.example` shows `SECRET_VARIABLE=mysecretval`. Credentials can also be passed via CLI arguments (`--accessKey`, `--secretKey`). The `.gitignore` correctly excludes `.env` and `deploy.env` files from version control. However, there is no integration with AWS Secrets Manager, HashiCorp Vault, or any secrets management system. The `@dotenvx/dotenvx` library is used for `.env` file loading but provides no encryption or rotation capabilities. AWS profile support (`--profile`) is available, which is better than raw key/secret, but still relies on local credential files.
- **Gap**: No secrets management integration. Credentials stored in plain-text `.env` files or passed as CLI arguments. No rotation mechanism. No encryption at rest for stored credentials.
- **Compensating Controls**:
  - Use AWS profiles (`--profile`) instead of raw access keys to leverage the AWS credential chain (including IAM roles, SSO).
  - Store credentials in AWS Systems Manager Parameter Store or Secrets Manager and inject them into the environment at runtime.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add native integration with AWS Secrets Manager for credential retrieval. Support AWS SSO credential resolution. Deprecate the `--accessKey`/`--secretKey` CLI arguments in favor of profile-based or role-based authentication.
- **Evidence**: `lib/.env.example` (plain-text credential patterns), `lib/deploy.env.example` (`SECRET_VARIABLE=mysecretval`), `lib/aws.js` (credential configuration from config object), `.gitignore` (`.env` excluded)

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The CLI provides two partial sandbox capabilities: (1) The `--endpoint` flag allows pointing to a custom AWS endpoint (e.g., LocalStack at `http://127.0.0.1:4574`), enabling local testing against a mock AWS environment. This is set in `lib/aws.js` via `aws.config.endpoint = config.endpoint`. (2) The `run` command executes the Lambda function locally using `node-lambda run`, which invokes the handler with a test event file (`event.json`) and context file (`context.json`). However, there is no dedicated staging environment configuration, no seed data scripts, no synthetic data generators, and no environment-specific deployment profiles.
- **Gap**: Partial sandbox capability via LocalStack endpoint support and local run command, but no production-equivalent staging environment with realistic data. No automated environment provisioning.
- **Compensating Controls**:
  - Use LocalStack with the `--endpoint` flag for integration testing against mock AWS services.
  - Maintain a separate AWS account for staging deployments.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document a recommended LocalStack-based testing workflow for agent validation. Add an `--environment` flag that maps to pre-configured deployment profiles (dev, staging, production) with appropriate safety guardrails per environment.
- **Evidence**: `bin/node-lambda` (`--endpoint` option), `lib/aws.js` (`aws.config.endpoint = config.endpoint`), `bin/node-lambda` (`run` command for local execution)

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The CLI version is tracked in `package.json` (`"version": "1.3.0"`) and follows semantic versioning for npm distribution. A `CHANGELOG.md` file exists. However, there is no API contract versioning, no schema versioning, no breaking change detection in CI, and no consumer-driven contract testing. The commander.js option definitions in `bin/node-lambda` can change between versions without automated detection. There are no schema registry entries, no OpenAPI diff tools, and no compatibility checks in the CI pipeline (`.github/workflows/workflow.yml` runs lint + unit tests only).
- **Gap**: No API contract versioning or breaking change detection. CLI argument changes between versions are not caught by automated testing. An agent's tool definition could silently break when the CLI is updated.
- **Compensating Controls**:
  - Pin the CLI version in agent tool definitions (e.g., `npx node-lambda@1.3.0`).
  - Review CHANGELOG.md for breaking changes before upgrading.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a CLI interface snapshot test that captures all command definitions, options, and defaults, and fails if they change unexpectedly. Add this test to the CI pipeline to catch breaking changes before release.
- **Evidence**: `package.json` (`"version": "1.3.0"`), `CHANGELOG.md` (exists but no automated checks), `.github/workflows/workflow.yml` (no contract testing)

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The codebase imports `aws-xray-sdk-core` and `continuation-local-storage` in `lib/main.js`. However, the X-Ray integration is used only in the `_runHandler` method for the `run` command — it creates an X-Ray namespace and segment to provide tracing context for the user's Lambda function during local execution. It does not trace the CLI tool's own operations. All logging is unstructured `console.log()` and `console.error()` output. There are no correlation IDs, no request IDs, no structured JSON log format, and no trace ID propagation across the multi-step deployment process.
- **Gap**: No distributed tracing for CLI operations. No structured logging. No correlation IDs linking deployment steps. The X-Ray SDK is included but used only for local Lambda execution context, not for CLI tool observability.
- **Compensating Controls**:
  - Generate a unique deployment ID at the start of each `deploy` invocation and prepend it to all log output.
  - Redirect CLI output to a structured log aggregator.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement structured JSON logging with a deployment correlation ID. Add optional X-Ray tracing for the deployment workflow itself (not just the user's Lambda code).
- **Evidence**: `lib/main.js` (X-Ray used only in `_runHandler` for `run` command; `console.log` used for all output)

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No alerting configuration exists. The CLI is a command-line tool, not a running service, so there are no CloudWatch alarms, no error rate thresholds, no latency monitoring, and no PagerDuty/OpsGenie integration. Deployment failures are surfaced only via non-zero exit codes and console error output. There is no mechanism to detect patterns of repeated deployment failures or degraded AWS service performance.
- **Gap**: No alerting capability. Repeated agent deployment failures would go undetected without external monitoring of the agent's execution environment.
- **Compensating Controls**:
  - Monitor the agent's execution logs for non-zero exit codes and error patterns.
  - Set up CloudWatch alarms on the AWS APIs being called (Lambda, S3) to detect service-side issues.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: If the CLI is wrapped in a service layer, add CloudWatch metrics for deployment success/failure rates and latency. For CLI use, implement a `--metrics` flag that publishes deployment outcome metrics to CloudWatch.
- **Evidence**: No alerting configuration found in repository. `.github/workflows/workflow.yml` (CI/CD only — no runtime alerting)

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No Infrastructure as Code (IaC) files exist in the repository. There are no Terraform files, no CloudFormation templates, no CDK stacks, no Helm charts, and no Kubernetes manifests. The CLI is distributed as an npm package (`npm install -g node-lambda`) and has no infrastructure to manage — it runs on the user's machine and calls AWS APIs directly. There is no API Gateway, no server infrastructure, and no deployment infrastructure managed by IaC. Consequently, there is no drift detection and no peer review for infrastructure changes (because there is no infrastructure).
- **Gap**: No IaC governance. The CLI has no infrastructure to govern — it is a client-side tool. However, if wrapped in a service for agent consumption, the service infrastructure would need IaC governance.
- **Compensating Controls**:
  - For the current CLI distribution model, npm versioning and GitHub releases serve as the governance mechanism.
  - If migrating to a service-based model, define all infrastructure in IaC from the start.
- **Remediation Timeline**: N/A (no infrastructure to govern in current architecture); 60–90 days if migrating to a service model
- **Recommendation**: If building an API wrapper for agent consumption (per API-Q1), define the hosting infrastructure (API Gateway, Lambda, ECS, etc.) using Terraform or CDK from day one.
- **Evidence**: No IaC files found in repository. No `.tf`, `.cfn.yaml`, `cdk.json`, or Kubernetes manifests.

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: CI/CD exists via GitHub Actions (`.github/workflows/workflow.yml`). The pipeline runs on push and pull request events, testing on Node.js 22.x and 24.x across Ubuntu, macOS, and Windows. It executes `npm ci` and `npm test` (which runs `standard` linting + `mocha` unit tests). CodeQL security scanning runs on the `master` branch (`.github/workflows/codeql-analysis.yml`). Dependabot is configured for monthly updates of GitHub Actions and npm dependencies (`.github/dependabot.yml`). However, there is no API contract testing, no CLI interface snapshot testing, no consumer-driven contract tests (Pact), no OpenAPI validation, and no breaking change detection.
- **Gap**: CI/CD exists with good test coverage and security scanning, but no contract testing or breaking change detection for the CLI interface. An agent tool definition could break silently when CLI options change.
- **Compensating Controls**:
  - The comprehensive unit test suite (6 test files, using `aws-sdk-mock`) provides regression coverage for core functionality.
  - CodeQL provides security scanning for vulnerability detection.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a CLI interface snapshot test that captures all commander.js command definitions, options, defaults, and descriptions, and fails if they change. This serves as an automated contract test for agent tool definitions.
- **Evidence**: `.github/workflows/workflow.yml` (Node CI), `.github/workflows/codeql-analysis.yml` (CodeQL), `.github/dependabot.yml` (dependency updates), `test/` directory (6 test files)

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The CLI is distributed as an npm package. Rollback means publishing or installing a previous npm version (`npm install -g node-lambda@<previous-version>`). There is no explicit rollback mechanism in the CI/CD pipeline — the GitHub Actions workflow does `npm test` but does not handle automated publishing or rollback. There are no blue/green deployments, no canary releases, and no feature flags. For Lambda deployments performed by the CLI, there is no `rollback` command to revert a deployed Lambda function to its previous state.
- **Gap**: No automated rollback for CLI releases or for Lambda deployments performed by the CLI. Recovery requires manual intervention (installing a previous npm version or manually reverting Lambda configuration).
- **Compensating Controls**:
  - Pin the CLI version to a known-good release in agent configurations.
  - Use Lambda versioning and aliases to maintain the previous known-good function version.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a `node-lambda rollback` command that reverts a Lambda function to its previous published version using the Lambda versioning API. For CLI distribution, add a release workflow with automated npm publishing and rollback capability.
- **Evidence**: `package.json` (`"version": "1.3.0"`), `.github/workflows/workflow.yml` (no publish/release/rollback steps)

## INFOs — Architecture and Design Inputs

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The CLI's write operations (deploy, which calls `createFunction`/`updateFunctionConfiguration`/`updateFunctionCode`) are not idempotent. Deploying the same code twice creates the same result (Lambda functions are update-or-create), but event source mappings, schedule events, and S3 events are managed with create-or-update logic that is not strictly idempotent — `_updateEventSources` creates new mappings if they don't exist and updates existing ones, but the comparison is by `EventSourceArn` only. However, the underlying AWS Lambda `updateFunctionCode` is naturally idempotent (uploading the same code ZIP produces the same function state).
- **Implication**: For a read-only agent scope, idempotency of write operations is informational. If the agent scope expands to write-enabled, the lack of explicit idempotency keys on deploy operations would become a concern.
- **Recommendation**: Consider adding idempotency keys (e.g., deployment ID or content hash) to prevent duplicate deployments when agent scope expands to write-enabled.
- **Evidence**: `lib/main.js` (`_uploadExisting`, `_uploadNew`, `_updateEventSources`)

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: All output is unstructured text via `console.log()`. Deploy results are logged as JavaScript objects (which Node.js formats as `[Object]` for nested structures). The `run` command outputs the Lambda handler result as `JSON.stringify(result)`. There is a `--silent` flag that suppresses all `console.log` output for the `deploy` command. There is no JSON output mode, no structured response format option, and no machine-parseable output mode.
- **Implication**: Agent tool integration would require parsing unstructured text output or wrapping the CLI in an adapter that captures and structures the output. The `run` command's JSON output of handler results is the most agent-friendly output in the CLI.
- **Recommendation**: Add a `--output json` mode that formats all command output as structured JSON objects with consistent fields (status, result, errors).
- **Evidence**: `lib/main.js` (`console.log` throughout, `--silent` option in `deploy` action, `JSON.stringify(result)` in `_runHandler`)

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: The CLI does not expose an API and therefore does not return rate limit headers. AWS API rate limits apply to the underlying AWS SDK calls, but these are not documented or surfaced by the CLI. The AWS SDK handles `ThrottlingException` with automatic retry and backoff, but the CLI does not expose rate limit information to the caller.
- **Implication**: An agent using this CLI has no visibility into how close it is to AWS API rate limits. Rate limit awareness must be implemented at the agent level or through AWS CloudWatch metrics.
- **Recommendation**: Document AWS Lambda, S3, CloudWatch Events, and CloudWatch Logs API rate limits in the README. If building an API wrapper, include rate limit headers in responses.
- **Evidence**: `lib/main.js` (no rate limit headers), `lib/aws.js` (no rate limit configuration)

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: INFO
- **Finding**: The CLI has no identity propagation or delegation patterns. It operates with a single set of AWS credentials for all operations. There is no JWT parsing, no OAuth2 on-behalf-of flows, no token exchange, and no user context headers. The `--profile` option selects a named AWS profile, but this is credential selection, not identity propagation.
- **Implication**: For a stateless-utility archetype, identity propagation is not critical — the CLI operates as a utility tool, not a multi-tenant service. If the CLI is wrapped in a service, identity propagation would become relevant.
- **Recommendation**: No action needed for current architecture. If migrating to a service model, implement identity context propagation.
- **Evidence**: `lib/aws.js` (single credential set), `bin/node-lambda` (no user context)

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No concurrency controls exist. If multiple CLI instances deploy to the same Lambda function simultaneously, there are no locks, no optimistic concurrency (version checks), and no conflict detection. The `_uploadExisting` method updates configuration and code sequentially without checking if another deployment is in progress. The polling loop for `LastUpdateStatus` provides a weak form of coordination (waiting for a previous update to complete) but does not prevent concurrent deployments from interleaving.
- **Implication**: For read-only agent scope, concurrency controls for write operations are informational. If expanded to write-enabled, concurrent agent deployments could corrupt Lambda function state.
- **Recommendation**: Add a deployment lock mechanism (e.g., DynamoDB-based lock or S3 object lock) to prevent concurrent deployments to the same function.
- **Evidence**: `lib/main.js` (`_uploadExisting` — no locking, polling loop for `LastUpdateStatus`)

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No transaction limits or blast radius controls exist. The CLI can deploy to unlimited regions in a single invocation (the `--region` flag accepts a comma-separated list of any number of regions). There are no limits on the number of event source mappings, schedule events, or S3 events that can be created per deployment. The `deploy` command has no maximum operations limit, no spend cap, and no configurable safety bounds.
- **Implication**: For read-only agent scope, blast radius controls are informational. If expanded to write-enabled, an agent could deploy to many regions simultaneously without any safety cap.
- **Recommendation**: Add configurable limits: maximum regions per deployment, maximum event sources per function, and a `--dry-run` mode to preview changes before execution.
- **Evidence**: `lib/main.js` (`deploy` — `regions.map` with no limit), `bin/node-lambda` (`--region` accepts unlimited comma-separated regions)

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The CLI has no draft or pending state concept. The `deploy` command directly creates or updates Lambda functions — there is no "plan" step followed by an "apply" step (unlike Terraform's plan/apply workflow). The `package` command creates a ZIP file without deploying it, which could serve as a partial "draft" capability (create the package, review it, then deploy separately), but this is not designed as an approval workflow.
- **Implication**: For read-only agent scope, draft states are informational. The `package` command provides a natural separation point that could be leveraged for human review.
- **Recommendation**: Implement a `--plan` mode for the `deploy` command that shows what changes would be made (like `terraform plan`) without executing them. This enables a two-step deploy workflow suitable for human-in-the-loop patterns.
- **Evidence**: `bin/node-lambda` (`package` and `deploy` as separate commands), `lib/main.js` (`deploy` executes immediately)

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable approval gates exist. The CLI does not support requiring human confirmation before executing any operation. The `deploy` command executes immediately upon invocation. There are no `--confirm` flags, no interactive prompts, no Step Functions with human approval tasks, and no webhook-based approval flows.
- **Implication**: For read-only agent scope, approval gates are informational. If expanded to write-enabled, the absence of approval gates means an agent could deploy without any human review.
- **Recommendation**: Add a `--require-approval` flag that pauses before execution and requires explicit confirmation (via stdin for interactive use, or via a callback URL for automated use).
- **Evidence**: `bin/node-lambda` (no confirmation or approval options in any command)

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality scores, completeness metrics, or freshness SLAs exist. The CLI does not manage business data — it deploys code and configuration to AWS Lambda. Data quality concepts do not directly apply to the deployment artifacts managed by this tool.
- **Implication**: Not directly relevant for a deployment CLI tool. If the CLI were extended to manage data pipelines or data-aware deployments, data quality metrics would become relevant.
- **Recommendation**: No action needed for the current tool's purpose.
- **Evidence**: No data quality metrics, dashboards, or monitoring found in the repository.

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Field names in the codebase are semantically meaningful and human-readable. The CLI uses AWS SDK parameter names (`FunctionName`, `MemorySize`, `Runtime`, `Handler`, `Timeout`, `Description`, `VpcConfig`, `TracingConfig`, `Layers`, `Tags`) which are well-documented by AWS. The commander.js option names (`--functionName`, `--memorySize`, `--handler`, `--timeout`) are descriptive. Environment variable names (`AWS_FUNCTION_NAME`, `AWS_MEMORY_SIZE`, `AWS_HANDLER`) follow standard AWS conventions.
- **Implication**: Agent tool definitions can use the existing field names directly without requiring a data dictionary or lookup table. The naming convention is consistent and self-documenting.
- **Recommendation**: No action needed. The existing naming conventions are agent-friendly.
- **Evidence**: `bin/node-lambda` (descriptive option names), `lib/main.js` (`_params` method uses AWS SDK naming conventions)

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No data catalog or metadata layer exists. There is no AWS Glue Data Catalog, no DataHub, no Collibra, and no metadata files describing the data managed by the tool. The CLI manages deployment artifacts (code ZIPs, Lambda configuration, event sources) but does not have a formal metadata layer describing these artifacts.
- **Implication**: Agent tool builders must understand the CLI's capabilities from the README and source code, with no centralized metadata registry to query.
- **Recommendation**: Consider publishing the CLI's capabilities as a structured metadata document (tool manifest) that agent frameworks can consume for tool discovery.
- **Evidence**: No data catalog or metadata files found in the repository.

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No business outcome metrics are published. The CLI does not emit custom CloudWatch metrics for deployment success rates, deployment duration, deployment frequency, or deployment failure reasons. There are no custom dashboards, no business KPI tracking, and no `cloudwatch.put_metric_data` calls.
- **Implication**: There is no visibility into how agent-driven deployments perform compared to human-driven deployments. Deployment analytics must be built externally.
- **Recommendation**: Add optional metric emission (`--metrics` flag) that publishes deployment outcome metrics (success/failure, duration, region, function name) to CloudWatch for operational visibility.
- **Evidence**: No custom metrics or metric emission found in the codebase.

### ENG-Q4: API Test Coverage

- **Severity**: INFO
- **Finding**: The repository has a comprehensive test suite with 6 test files: `test/main.js` (1,717 lines — extensive testing of core Lambda class), `test/node-lambda.js` (398 lines — CLI integration tests), `test/s3_deploy.js` (198 lines), `test/s3_events.js` (236 lines), `test/schedule_events.js` (188 lines), `test/cloudwatch_logs.js` (77 lines). Tests use `aws-sdk-mock` for mocking AWS services and `chai` for assertions. The CI pipeline runs tests on Node.js 22.x and 24.x across Ubuntu, macOS, and Windows. For a stateless-utility archetype, this represents good test coverage.
- **Implication**: The existing test suite provides confidence in the core functionality. However, tests do not cover agent-specific scenarios (concurrent deployments, error recovery, parameter validation edge cases).
- **Recommendation**: Consider adding agent-specific test scenarios: concurrent deployment handling, error response format validation, and parameter boundary testing.
- **Evidence**: `test/main.js`, `test/node-lambda.js`, `test/s3_deploy.js`, `test/s3_events.js`, `test/schedule_events.js`, `test/cloudwatch_logs.js`, `.github/workflows/workflow.yml` (CI runs `npm test`)

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: BLOCKER
- **Finding**: The application is a CLI tool built with `commander.js`. It exposes four CLI commands (`setup`, `run`, `package`, `deploy`) but no REST, GraphQL, or AsyncAPI interface. No HTTP endpoints exist. The only programmatic interface is the Node.js module export (`lib/main.js`), which is not a documented API surface for agent consumption.
- **Gap**: No API interface for agent consumption. CLI-only tool designed for human use.
- **Recommendation**: Build a REST API wrapper around core Lambda class methods or create a well-documented programmatic SDK with typed interfaces.
- **Evidence**: `bin/node-lambda`, `lib/main.js`, `package.json`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, GraphQL schema, or machine-readable specification exists. Documentation is in `README.md` and `--help` output only.
- **Gap**: No machine-readable spec. Agent tool definitions must be manually authored.
- **Recommendation**: Generate a JSON schema from commander.js definitions; create an OpenAPI spec if building an API wrapper.
- **Evidence**: `README.md`, `bin/node-lambda`, no spec files found

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: Errors use `console.error()` and `process.exitCode` (0=success, 1=deploy error, 254=unsupported runtime, 255=handler error). No structured error codes, no error categorization (retriable vs. terminal), no machine-readable format.
- **Gap**: No structured error responses. Agent cannot distinguish error types.
- **Recommendation**: Implement `--output json` mode with structured error objects.
- **Evidence**: `lib/main.js` (error handling patterns)

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Write operations are not explicitly idempotent. AWS Lambda `updateFunctionCode` is naturally idempotent, but event source and schedule management lacks idempotency keys.
- **Gap**: No explicit idempotency mechanisms.
- **Recommendation**: Add idempotency keys for deployment operations when expanding to write-enabled scope.
- **Evidence**: `lib/main.js` (`_uploadExisting`, `_updateEventSources`)

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: All output is unstructured text via `console.log()`. The `run` command outputs handler results as JSON. No `--output json` mode exists.
- **Gap**: No structured response format option.
- **Recommendation**: Add `--output json` mode for all commands.
- **Evidence**: `lib/main.js` (`console.log` throughout)

#### API-Q6: Asynchronous Operation Support
- **Severity**: RISK-QUALITY
- **Finding**: The `deploy` command is a long-running synchronous operation (default timeout 120s). It blocks until complete. No async job submission, no polling endpoint, no job IDs.
- **Gap**: No async patterns for long-running deploy operations.
- **Recommendation**: Implement `--async` mode with job ID and status polling.
- **Evidence**: `lib/main.js` (`deploy`, `_uploadExisting` polling loop), `bin/node-lambda` (`DEPLOY_TIMEOUT=120000`)

#### API-Q7: Event Emission for State Changes
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has state changes (stateful-crud, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: The CLI does not expose an API, so no rate limit headers are returned. AWS API rate limits apply to SDK calls but are not documented or surfaced.
- **Gap**: No rate limit documentation or visibility.
- **Recommendation**: Document underlying AWS API rate limits; add rate limit headers if building an API wrapper.
- **Evidence**: `lib/main.js`, `lib/aws.js`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: Uses human-style AWS credentials (access key/secret key, profile, session token) via CLI args and env vars. No OAuth2 client credentials, no mTLS, no API keys with principal attribution. No agent identity attribution.
- **Gap**: No machine identity authentication or agent attribution.
- **Recommendation**: Add IAM role assumption with session name tagging for agent identity attribution.
- **Evidence**: `lib/aws.js`, `bin/node-lambda`, `lib/.env.example`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: No application-level permission scoping. Full AWS credentials are set globally. All CLI commands use the same credential set without restriction.
- **Gap**: No scoped permissions at the application layer.
- **Recommendation**: Use tightly scoped IAM policies; implement a permission model within the CLI.
- **Evidence**: `lib/aws.js`, `lib/main.js`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: No internal authorization model. All four commands available to anyone with credentials. No role-based restrictions.
- **Gap**: Cannot restrict agent to specific commands (e.g., `run` only, no `deploy`).
- **Recommendation**: Add a command allow-list configuration.
- **Evidence**: `bin/node-lambda`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: No identity propagation patterns. Single credential set for all operations. Archetype calibration: downgraded to INFO for stateless-utility.
- **Gap**: No identity propagation. Not critical for stateless-utility archetype.
- **Recommendation**: No action needed for current architecture.
- **Evidence**: `lib/aws.js`, `bin/node-lambda`

#### AUTH-Q5: Credential Management
- **Severity**: RISK-QUALITY
- **Finding**: Credentials managed via `.env` files and CLI arguments. No Secrets Manager or Vault integration. `.env` excluded from git. `@dotenvx/dotenvx` provides no encryption. AWS profile support available as a better alternative.
- **Gap**: No secrets management integration. Plain-text credential storage.
- **Recommendation**: Add Secrets Manager integration; deprecate `--accessKey`/`--secretKey` in favor of profiles/roles.
- **Evidence**: `lib/.env.example`, `lib/deploy.env.example`, `lib/aws.js`, `.gitignore`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No application-level audit logging. All output is ephemeral `console.log`/`console.error`. No structured log file, no immutable storage. CloudTrail captures underlying AWS API calls but not CLI-level context.
- **Gap**: No immutable audit trail for CLI operations.
- **Recommendation**: Add structured JSON logging with immutable storage.
- **Evidence**: `lib/main.js`, `lib/aws.js`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: No agent identity concept. Access controlled by AWS credentials. Revoking requires IAM changes outside the application.
- **Gap**: No agent-specific identity suspension mechanism.
- **Recommendation**: Assign unique IAM roles per agent with session expiry.
- **Evidence**: `lib/aws.js`, `bin/node-lambda`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Multi-step deploy (archive → upload → create/update function → update event sources → schedule events → S3 events → logs retention → alias) has no rollback. `_uploadExisting` updates config then code sequentially with no compensation if code update fails.
- **Gap**: No rollback or compensation for partial deployment failures.
- **Recommendation**: Implement a rollback command using Lambda versioning and aliases.
- **Evidence**: `lib/main.js` (`_uploadExisting`, `_deployToRegion`)

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
- **Finding**: No concurrency controls. Multiple simultaneous CLI instances deploying to the same function have no locking or conflict detection.
- **Gap**: No concurrency controls for write operations.
- **Recommendation**: Add deployment locking mechanism for write-enabled scope expansion.
- **Evidence**: `lib/main.js` (`_uploadExisting`)

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: AWS SDK provides retry logic. Code has `on('retry')` handlers. But no circuit breakers. Degraded AWS services cause slow failure, not fast failure. Polling loop in `_uploadExisting` (10 iterations × 3s) is not a circuit breaker.
- **Gap**: No circuit breaker pattern for external dependency calls.
- **Recommendation**: Add circuit breaker around deploy workflow using a library like `opossum`.
- **Evidence**: `lib/main.js` (`_uploadExisting`, `_deployToRegion`), `lib/aws.js`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No application-level rate limiting. Multi-region deploys fire in parallel via `Promise.all`. No queue, no concurrency limiter, no rate control.
- **Gap**: No rate limiting for AWS API calls. Agent loops could exhaust API quotas.
- **Recommendation**: Add concurrency limiter and configurable minimum interval between deployments.
- **Evidence**: `lib/main.js` (`deploy` — `Promise.all`), `bin/node-lambda`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No transaction limits. Unlimited regions per deployment, unlimited event sources per function. No safety bounds.
- **Gap**: No blast radius controls.
- **Recommendation**: Add configurable limits and `--dry-run` mode.
- **Evidence**: `lib/main.js`, `bin/node-lambda`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No draft or pending state concept. `deploy` executes immediately. `package` creates a ZIP without deploying, providing a partial separation point.
- **Gap**: No draft/pending state for deployments.
- **Recommendation**: Implement a `--plan` mode for previewing changes before execution.
- **Evidence**: `bin/node-lambda`, `lib/main.js`

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable approval gates. No `--confirm` flags, no interactive prompts, no human-in-the-loop mechanisms.
- **Gap**: No approval gates for any operation.
- **Recommendation**: Add `--require-approval` flag for high-risk operations.
- **Evidence**: `bin/node-lambda`

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: Partial sandbox: (1) `--endpoint` flag supports LocalStack. (2) `run` command executes Lambda locally with test event/context files. No dedicated staging environment, no seed data, no environment profiles.
- **Gap**: Partial sandbox capability only. No production-equivalent staging.
- **Recommendation**: Document LocalStack testing workflow; add environment-specific deployment profiles.
- **Evidence**: `bin/node-lambda` (`--endpoint`), `lib/aws.js` (`aws.config.endpoint`)

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: Handles AWS credentials, IAM role ARNs, KMS key ARNs, VPC IDs, and deployment secrets (`deploy.env`). No field-level classification, no tagging, no protection. All handled as plain text.
- **Gap**: No sensitive data classification or field-level protection.
- **Recommendation**: Classify credential fields as sensitive; implement masking; integrate with Secrets Manager.
- **Evidence**: `lib/.env.example`, `lib/deploy.env.example`, `lib/main.js`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Deploys to user-specified regions with no data residency validation. Default regions span US and EU (`us-east-1,us-west-2,eu-west-1`). Config file contents are passed as Lambda environment variables to any specified region.
- **Gap**: No data residency controls or region validation.
- **Recommendation**: Add a configurable region allow-list validated before execution.
- **Evidence**: `bin/node-lambda`, `lib/main.js` (`_params`)

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
- **Severity**: RISK-SAFETY
- **Finding**: `console.log(params)` in `_deployToRegion` logs sensitive fields including `Environment.Variables`, `Role`, `VpcConfig`, `KMSKeyArn`. `console.log(results)` logs full deployment results. No log scrubbing, no PII masking.
- **Gap**: No PII or sensitive data redaction in any logging path.
- **Recommendation**: Implement a log sanitizer for sensitive fields before all `console.log` calls.
- **Evidence**: `lib/main.js` (`_deployToRegion`, `_printDeployResults`)

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics. The CLI does not manage business data — it deploys code and configuration. Data quality concepts do not directly apply.
- **Gap**: Not applicable to a deployment CLI tool.
- **Recommendation**: No action needed.
- **Evidence**: No data quality metrics found

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: CLI version tracked in `package.json` (1.3.0) with semantic versioning. `CHANGELOG.md` exists. No contract versioning, no breaking change detection in CI, no consumer-driven contract testing.
- **Gap**: No API contract versioning or breaking change detection.
- **Recommendation**: Add CLI interface snapshot test to CI pipeline.
- **Evidence**: `package.json`, `CHANGELOG.md`, `.github/workflows/workflow.yml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Field names are semantically meaningful. Uses AWS SDK naming conventions (`FunctionName`, `MemorySize`, `Runtime`, `Handler`). CLI options are descriptive (`--functionName`, `--memorySize`).
- **Gap**: No gap. Naming conventions are agent-friendly.
- **Recommendation**: No action needed.
- **Evidence**: `bin/node-lambda`, `lib/main.js`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No data catalog or metadata layer. No AWS Glue, DataHub, or metadata files.
- **Gap**: No centralized metadata registry for tool discovery.
- **Recommendation**: Consider publishing a structured tool manifest.
- **Evidence**: No metadata files found

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: `aws-xray-sdk-core` imported but used only in `_runHandler` for local Lambda execution context. No tracing for CLI operations. All logging is unstructured `console.log`/`console.error`. No correlation IDs.
- **Gap**: No distributed tracing or structured logging for CLI operations.
- **Recommendation**: Implement structured JSON logging with deployment correlation IDs.
- **Evidence**: `lib/main.js`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: No alerting configuration. CLI tool, not a running service. No CloudWatch alarms, no error rate thresholds.
- **Gap**: No alerting capability for deployment operations.
- **Recommendation**: Add `--metrics` flag for CloudWatch metric emission.
- **Evidence**: No alerting configuration found

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No business outcome metrics published. No custom CloudWatch metrics for deployment outcomes.
- **Gap**: No visibility into deployment performance patterns.
- **Recommendation**: Add optional deployment outcome metrics.
- **Evidence**: No custom metrics found

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK-QUALITY
- **Finding**: No IaC files in repository. CLI distributed as npm package with no infrastructure to manage. No API Gateway, no server infrastructure.
- **Gap**: No IaC governance (no infrastructure exists to govern).
- **Recommendation**: If building an API wrapper, define infrastructure as IaC from day one.
- **Evidence**: No IaC files found

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: GitHub Actions CI/CD with Node 22.x/24.x, cross-platform testing, `standard` linting, `mocha` unit tests, CodeQL scanning, Dependabot. No API contract testing or breaking change detection.
- **Gap**: No contract testing for CLI interface.
- **Recommendation**: Add CLI interface snapshot test to CI.
- **Evidence**: `.github/workflows/workflow.yml`, `.github/workflows/codeql-analysis.yml`, `.github/dependabot.yml`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: CLI distributed via npm — rollback means installing a previous version. No automated rollback in CI/CD. No `rollback` command for Lambda deployments.
- **Gap**: No automated rollback for CLI releases or Lambda deployments.
- **Recommendation**: Add `node-lambda rollback` command; add release workflow with rollback.
- **Evidence**: `package.json`, `.github/workflows/workflow.yml`

#### ENG-Q4: API Test Coverage
- **Severity**: INFO
- **Finding**: Comprehensive test suite: `test/main.js` (1,717 lines), `test/node-lambda.js` (398 lines), `test/s3_deploy.js` (198 lines), `test/s3_events.js` (236 lines), `test/schedule_events.js` (188 lines), `test/cloudwatch_logs.js` (77 lines). Uses `aws-sdk-mock` and `chai`. CI runs across Node 22.x/24.x on Ubuntu/macOS/Windows. Downgraded to INFO for stateless-utility archetype.
- **Gap**: Good coverage, but no agent-specific test scenarios.
- **Recommendation**: Add agent-specific test scenarios.
- **Evidence**: `test/` directory, `.github/workflows/workflow.yml`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent data stores
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated


---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `lib/main.js` | API-Q1, API-Q2, API-Q3, API-Q4, API-Q5, API-Q6, AUTH-Q2, AUTH-Q6, STATE-Q1, STATE-Q3, STATE-Q4, STATE-Q5, STATE-Q6, HITL-Q1, DATA-Q1, DATA-Q6, DISC-Q2, OBS-Q1 |
| `lib/aws.js` | API-Q8, AUTH-Q1, AUTH-Q2, AUTH-Q4, AUTH-Q5, AUTH-Q6, AUTH-Q7, STATE-Q4, STATE-Q5, DATA-Q2, HITL-Q3 |
| `lib/s3_deploy.js` | STATE-Q1, STATE-Q4 |
| `lib/s3_events.js` | STATE-Q1 |
| `lib/schedule_events.js` | STATE-Q1 |
| `lib/cloudwatch_logs.js` | STATE-Q1 |
| `bin/node-lambda` | API-Q1, API-Q4, API-Q6, API-Q8, AUTH-Q1, AUTH-Q3, AUTH-Q4, AUTH-Q7, STATE-Q5, STATE-Q6, HITL-Q1, HITL-Q2, HITL-Q3, DATA-Q2, DISC-Q2 |
| `index.js` | API-Q5 |
| `index_mjs.mjs` | API-Q5 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/workflow.yml` | DISC-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4 |
| `.github/workflows/codeql-analysis.yml` | ENG-Q2 |
| `.github/dependabot.yml` | ENG-Q2 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `package.json` | API-Q1, API-Q2, DISC-Q1, ENG-Q3 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `lib/.env.example` | AUTH-Q1, AUTH-Q5, DATA-Q1 |
| `lib/deploy.env.example` | AUTH-Q5, DATA-Q1 |
| `.gitignore` | AUTH-Q5 |
| `lib/event_sources.json.example` | STATE-Q1 |

### Documentation
| File | Questions Referenced |
|------|---------------------|
| `README.md` | API-Q2 |
| `CHANGELOG.md` | DISC-Q1 |

### Test Files
| File | Questions Referenced |
|------|---------------------|
| `test/main.js` | ENG-Q4 |
| `test/node-lambda.js` | ENG-Q4 |
| `test/s3_deploy.js` | ENG-Q4 |
| `test/s3_events.js` | ENG-Q4 |
| `test/schedule_events.js` | ENG-Q4 |
| `test/cloudwatch_logs.js` | ENG-Q4 |
