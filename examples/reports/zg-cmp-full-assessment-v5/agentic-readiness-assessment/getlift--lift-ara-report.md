# Agentic Readiness Assessment Report

**Target**: serverless-lift (https://github.com/getlift/lift)
**Date**: 2026-04-30
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Service Archetype**: stateless-utility (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: typescript, serverless, iac
**Context**: Serverless Framework plugin providing higher-level AWS constructs.

**Archetype Justification**: This is a Serverless Framework plugin (NPM package `serverless-lift`) that generates CloudFormation resources via AWS CDK constructs. It has no HTTP server, no database connections, no persistent state, no authentication surface, and no user-data logging — it runs as a CLI plugin within the Serverless Framework lifecycle.

**Surface flags**:
- has_persistent_data_store: false
- has_http_rpc_surface: false
- has_auth_surface: false
- has_write_operations: false
- has_logging_of_user_data: false

**INFO — Dev-Library-Application Override Applied**: This repository classifies as `application` (repo_type) but functions as a Serverless Framework plugin/library. The service archetype is `stateless-utility` and all 5 surface flags are `false`. Per the ARA transformation definition Step 1.5, the `library` N/A mapping is applied for scoring purposes. The original `repo_type` value (`application`) is preserved. Questions that would otherwise score BLOCKER or RISK are evaluated as INFO where the surface-flag calibration or dev-library-application override applies — the plugin does not own APIs, data stores, authentication, or operational infrastructure that agents would call directly.

---

## Readiness Profile: Agent-Ready

**BLOCKERs**: 0 | **RISK-SAFETY**: 0 | **RISK-QUALITY**: 0 | **INFOs**: 32

Cleared for autonomous operation. Instrument observability. Define scope explicitly. Run controlled pilot first.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 0 |
| RISK-SAFETY | 0 |
| RISK-QUALITY | 0 |
| INFO | 32 |
| N/A | 0 |
| Not Evaluated (extended) | 11 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 8
**Extended Questions Not Triggered**: 11
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: stateless-utility (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

No BLOCKERs identified.

---

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

No RISK-SAFETY findings identified.

### RISK-QUALITY — Address as Capacity Allows

No RISK-QUALITY findings identified.

---

## INFOs — Architecture and Design Inputs

<!-- TODO: INFOs section - filled in Detailed Findings below -->

All 32 INFO findings are documented in the Detailed Findings section below. Key themes:

1. **No agent-callable API surface**: This plugin exposes a programmatic TypeScript API consumed by the Serverless Framework CLI, not an HTTP/RPC surface that agents would call directly. All API, AUTH, STATE, HITL, and DATA questions resolve to INFO via the dev-library-application override.
2. **Strong schema contracts**: Each construct defines a JSON Schema (`STORAGE_DEFINITION`, `QUEUE_DEFINITION`, etc.) and TypeScript type declarations (`dist/src/plugin.d.ts`), providing machine-readable contracts for consumers.
3. **Solid CI pipeline**: GitHub Actions CI runs unit tests across Node 20/22/24, linting, formatting, and TypeScript type checking — though no explicit API contract testing or breaking-change detection exists.
4. **Encryption-aware generated resources**: The Storage construct defaults to S3-managed encryption and supports KMS; the Queue construct supports KMS encryption options. These are properties of the resources the plugin *generates*, not of the plugin itself.

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: This plugin does not expose a REST, GraphQL, or AsyncAPI interface. It is a Serverless Framework plugin that exposes a programmatic TypeScript API via `src/plugin.ts` (the `LiftPlugin` class) and construct classes (`Storage`, `Queue`, `Webhook`, etc.). The plugin's interface is consumed by the Serverless Framework CLI lifecycle hooks, not by HTTP clients. Construct schemas (e.g., `STORAGE_DEFINITION`, `QUEUE_DEFINITION`, `WEBHOOK_DEFINITION`) define the configuration contracts in JSON Schema format. TypeScript declarations are published via `"types": "dist/src/plugin.d.ts"` in `package.json`.
- **Implication**: Agents consuming services built *with* this plugin would interact with the generated CloudFormation resources (API Gateways, SQS queues, S3 buckets), not with the plugin itself. The plugin's interface is the YAML configuration schema documented in `docs/`.
- **Recommendation**: No action required for agent readiness. The plugin's consumers (generated resources) are the relevant agent integration surface.
- **Evidence**: `src/plugin.ts`, `package.json` (types field), `src/constructs/aws/Storage.ts` (STORAGE_DEFINITION), `src/constructs/aws/Queue.ts` (QUEUE_DEFINITION), `src/constructs/aws/Webhook.ts` (WEBHOOK_DEFINITION)

#### API-Q2: Machine-Readable API Specification
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — machine-readable spec is not applicable. The plugin does expose machine-readable construct schemas as JSON Schema objects (e.g., `STORAGE_DEFINITION`, `QUEUE_DEFINITION`) embedded in the TypeScript source, and publishes TypeScript declaration files. These serve as the "API spec" for this library. No OpenAPI/AsyncAPI/GraphQL spec files exist in the repository, which is expected for a CLI plugin.
- **Implication**: For libraries, API contracts are expressed via package manifests and typed exports, which DISC-Q1 evaluates.
- **Recommendation**: No action required.
- **Evidence**: `src/constructs/aws/Storage.ts`, `src/constructs/aws/Queue.ts`, `package.json` (types field)

#### API-Q3: Structured Error Responses
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — structured error responses are not applicable. The plugin does implement a custom `ServerlessError` class (`src/utils/error.ts`) with `message` and `code` fields, following the Serverless Framework's error convention. Errors are thrown with descriptive codes (e.g., `LIFT_UNKNOWN_CONSTRUCT_TYPE`, `LIFT_INVALID_CONSTRUCT_CONFIGURATION`, `LIFT_VARIABLE_UNKNOWN_CONSTRUCT`).
- **Implication**: Libraries communicate failure via typed exceptions. The `ServerlessError` class with error codes is a well-structured error pattern for CLI consumers.
- **Recommendation**: No action required.
- **Evidence**: `src/utils/error.ts`, `src/plugin.ts` (error throws with codes), `src/constructs/aws/Queue.ts` (validation errors with codes)

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Read-only agent scope; idempotency evaluation is informational. The plugin itself does not expose write API endpoints. It generates CloudFormation templates as a build-time tool. CLI commands like `queue:send` send SQS messages but these are developer-facing CLI operations, not agent-callable APIs.
- **Implication**: Idempotency of generated resources (e.g., SQS message deduplication via `contentBasedDeduplication` for FIFO queues in `Queue.ts`) is a property of the resources the plugin creates, not of the plugin itself.
- **Recommendation**: No action required.
- **Evidence**: `src/constructs/aws/Queue.ts` (FIFO contentBasedDeduplication)

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: The plugin does not return HTTP responses. Its outputs are CloudFormation templates (JSON), CLI console output (text via `chalk` and `ora`), and TypeScript objects. CloudFormation template generation uses `aws-cdk-lib`'s synthesis pipeline, producing well-structured JSON.
- **Implication**: Agent interaction would be with the generated CloudFormation resources, not with the plugin's output format.
- **Recommendation**: No action required.
- **Evidence**: `src/providers/AwsProvider.ts` (appendCloudformationResources), `src/plugin.ts` (eject command outputs YAML)

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has operations >30s OR long-running workflows
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has state changes (stateful-crud, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — rate limit documentation and headers are not applicable. The plugin does not serve API traffic. Rate limiting for the generated resources (e.g., API Gateway throttling) would be configured by the consuming application's infrastructure.
- **Implication**: Rate limits are a concern for the deployed resources, not for the plugin build tool.
- **Recommendation**: No action required.
- **Evidence**: No evidence of rate limit headers in the codebase — expected for a CLI plugin.

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: System does not execute agent-invoked operations — authentication is a consumer responsibility. The plugin runs within the Serverless Framework CLI using the developer's AWS credentials (inherited from the environment or AWS profile). It does not implement its own authentication mechanism. The `AwsProvider` class delegates all AWS API calls to the Serverless Framework's built-in AWS provider (`serverless.getProvider("aws")`).
- **Implication**: Machine identity for the generated resources (API Gateway authorizers, IAM roles) is defined by the constructs the plugin creates (e.g., `Webhook.ts` creates IAM roles for API Gateway). The plugin itself is a build-time tool.
- **Recommendation**: No action required for the plugin. Consumers should ensure the generated resources have proper machine identity configuration.
- **Evidence**: `src/providers/AwsProvider.ts` (delegates to legacyProvider), `src/constructs/aws/Webhook.ts` (creates IAM roles)

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: INFO
- **Finding**: System does not enforce agent identities — scoped permissions are a consumer responsibility. The plugin generates IAM policy statements via each construct's `permissions()` method. These are scoped to specific actions and resources (e.g., Storage grants `s3:PutObject`, `s3:GetObject`, `s3:DeleteObject`, `s3:ListBucket` on the specific bucket ARN; Queue grants `sqs:SendMessage`, `sqs:ChangeMessageVisibility` on the specific queue ARN; DatabaseDynamoDBSingleTable grants specific DynamoDB actions on the table ARN and its indexes).
- **Implication**: The plugin demonstrates good least-privilege patterns in the IAM policies it generates. These generated policies support scoped agent access when the consuming application is deployed.
- **Recommendation**: No action required. The plugin's generated IAM policies follow least-privilege principles.
- **Evidence**: `src/constructs/aws/Storage.ts` (permissions()), `src/constructs/aws/Queue.ts` (permissions()), `src/constructs/aws/DatabaseDynamoDBSingleTable.ts` (permissions()), `src/CloudFormation.ts` (PolicyStatement class)

#### AUTH-Q3: Action-Level Authorization
- **Severity**: INFO
- **Finding**: System does not enforce agent identities — action-level authorization is a consumer responsibility. The plugin generates fine-grained IAM policies with action-level specificity (e.g., separate read vs. write DynamoDB actions in `DatabaseDynamoDBSingleTable.ts`). The Webhook construct creates API Gateway authorizers with Lambda-based custom authorization.
- **Implication**: The generated resources support action-level authorization. Agent access control is determined at deployment time by the consuming application.
- **Recommendation**: No action required.
- **Evidence**: `src/constructs/aws/DatabaseDynamoDBSingleTable.ts` (granular DynamoDB actions), `src/constructs/aws/Webhook.ts` (CfnAuthorizer)

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: System does not issue or enforce agent identities — identity propagation is a consumer responsibility. The plugin is a build-time tool with no runtime identity propagation. For `stateless-utility` archetype, this is downgraded to INFO.
- **Implication**: Identity propagation is a concern for the resources the plugin generates and the applications that deploy them.
- **Recommendation**: No action required.
- **Evidence**: `src/providers/AwsProvider.ts`, `src/plugin.ts`

#### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: The plugin handles credentials in two patterns: (1) AWS credentials are inherited from the Serverless Framework's AWS provider — no direct credential handling in the plugin code. (2) Stripe API keys are sourced from the `STRIPE_API_KEY` environment variable or from a TOML configuration file at `~/.config/stripe/config.toml` (see `StripeProvider.ts` `resolveConfiguration` method). No credentials are hardcoded in source code. No `.env` files are committed.
- **Implication**: The Stripe credential handling follows reasonable patterns for a CLI tool (environment variable with fallback to a local config file). No secrets are embedded in the codebase.
- **Recommendation**: No action required. The credential sourcing patterns are appropriate for a CLI plugin.
- **Evidence**: `src/providers/StripeProvider.ts` (resolveConfiguration method — reads STRIPE_API_KEY from env, falls back to ~/.config/stripe/config.toml), `.gitignore`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity RISK-SAFETY, further downgraded via dev-library-application override to INFO
- **Finding**: System does not execute agent-invoked write operations — audit logging is a consumer responsibility. The library/utility is called by applications that own the audit context. The plugin's logging (`src/utils/logger.ts`) is a simple console logger for CLI output, not an audit trail. has_auth_surface=false AND has_write_operations=false.
- **Implication**: Audit logging for agent operations would be implemented by the consuming application and the generated AWS resources (e.g., CloudTrail for API Gateway calls).
- **Recommendation**: No action required.
- **Evidence**: `src/utils/logger.ts`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: INFO
- **Finding**: System does not issue or enforce agent identities — suspension is a consumer responsibility. Libraries and utilities are invoked by applications that own identity lifecycle. has_auth_surface=false.
- **Implication**: Agent identity lifecycle management is a concern for the deployed application infrastructure.
- **Recommendation**: No action required.
- **Evidence**: `src/providers/AwsProvider.ts`, `src/plugin.ts`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity RISK-SAFETY, further downgraded via dev-library-application override to INFO
- **Finding**: System exposes no write operations — compensation logic is not applicable. The plugin is a build-time tool that generates CloudFormation templates. has_write_operations=false AND has_http_rpc_surface=false. The plugin itself delegates deployment to CloudFormation, which has its own rollback semantics.
- **Implication**: Rollback for deployed resources is handled by CloudFormation stack rollback, not by the plugin.
- **Recommendation**: No action required.
- **Evidence**: `src/providers/AwsProvider.ts` (appendCloudformationResources)

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
- **Trigger**: agent_scope is write-enabled AND service has persistent state
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: INFO
- **Finding**: The plugin does not implement circuit breakers, retry logic, or timeout configurations for its AWS API calls. AWS API calls in `src/classes/aws.ts` and `src/CloudFormation.ts` are simple `await` calls delegated to the Serverless Framework's AWS provider, which handles its own retry logic internally. The `sleep` utility (`src/utils/sleep.ts`) is used for UX timing (500ms delay after purge), not for resilience.
- **Implication**: As a dev-library-application with no agent-callable surface, resilience patterns are the responsibility of the consuming application and the Serverless Framework runtime.
- **Recommendation**: No action required for agent readiness. The Serverless Framework's AWS SDK client handles retries internally.
- **Evidence**: `src/classes/aws.ts` (awsRequest — no retry/circuit breaker), `src/CloudFormation.ts` (direct await), `src/utils/sleep.ts`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: INFO
- **Finding**: System exposes no HTTP/RPC surface — API-layer rate limiting is not applicable. The plugin is a CLI tool. Libraries invoked by consuming applications inherit the consumer's rate limiting, not their own. Stateless-utility archetype without a persistent API surface.
- **Implication**: Rate limiting is configured on the generated resources (e.g., API Gateway throttling for Webhook and ServerSideWebsite constructs).
- **Recommendation**: No action required.
- **Evidence**: No rate limiting middleware or configuration — expected for a CLI plugin.

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Read-only agent scope; transaction limits for write operations are informational only. The plugin does not perform write operations as an API. CLI commands like `queue:send` and `queue:failed:retry` operate on SQS messages but are developer-facing tools, not agent-callable endpoints.
- **Implication**: Blast radius controls would be implemented at the deployed application layer.
- **Recommendation**: No action required.
- **Evidence**: `src/constructs/aws/Queue.ts` (CLI commands)

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
- **Finding**: Library/utility — dev-library-application override applies. has_http_rpc_surface=false AND has_persistent_data_store=false. Libraries, CLIs, and scaffolds do not own staging environments — their consumers do. The plugin can be tested locally via `npm test` (Jest test suite with fixtures). The CI pipeline (`ci.yml`) runs tests across Node 20/22/24 with Serverless Framework v3. Test fixtures in `test/fixtures/` provide configuration examples.
- **Implication**: The plugin's own test infrastructure (Jest + fixtures + CI matrix) provides adequate testing. Staging environments are a concern for the deployed application.
- **Recommendation**: No action required.
- **Evidence**: `.github/workflows/ci.yml`, `jest.config.js`, `test/fixtures/`, `test/unit/`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO
- **Finding**: Dev-library-application override — skip directly to INFO. Libraries, CLIs, and scaffolds do not own the data that consuming applications store. The plugin generates CloudFormation for data resources (S3 buckets, DynamoDB tables, SQS queues) but does not itself store, process, or classify sensitive data. The Stripe provider reads API keys from environment/config at build time but does not persist them.
- **Implication**: Data classification is a responsibility of the deployed application using the generated resources.
- **Recommendation**: No action required.
- **Evidence**: `src/providers/StripeProvider.ts`, `src/constructs/aws/DatabaseDynamoDBSingleTable.ts`, `src/constructs/aws/Storage.ts`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity RISK-SAFETY, further downgraded via surface-flag calibration to INFO
- **Finding**: No persistent data store and no user-data logging — residency requirements do not apply. has_persistent_data_store=false AND has_logging_of_user_data=false. The plugin generates resources deployed in the AWS region configured in the Serverless Framework (via `provider.region`), but does not itself hold data subject to residency constraints.
- **Implication**: Data residency is configured at the deployment level by the consuming application.
- **Recommendation**: No action required.
- **Evidence**: `src/providers/AwsProvider.ts` (this.region = serverless.getProvider("aws").getRegion())

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
- **Finding**: System does not log user data and holds no user data — PII-in-logs risk is not applicable. has_logging_of_user_data=false AND has_persistent_data_store=false. The plugin's logger (`src/utils/logger.ts`) outputs diagnostic messages (e.g., "Uploading assets", "Message sent to SQS") with no user PII. The Queue `listDlq` command prints SQS message bodies, but these are developer-initiated CLI operations on the developer's own data, not agent-accessible log streams.
- **Implication**: PII in logs is a concern for the deployed application, not for the build-time plugin.
- **Recommendation**: No action required.
- **Evidence**: `src/utils/logger.ts`, `src/constructs/aws/Queue.ts` (listDlq prints message bodies to CLI stdout)

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: The plugin does not manage datasets. No data quality metrics or monitoring are applicable to a build-time CLI plugin. The generated DynamoDB tables include point-in-time recovery (`pointInTimeRecovery: true` in `DatabaseDynamoDBSingleTable.ts`), supporting data durability in the deployed application.
- **Implication**: Data quality is a concern for the consuming application.
- **Recommendation**: No action required.
- **Evidence**: `src/constructs/aws/DatabaseDynamoDBSingleTable.ts` (pointInTimeRecovery)

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: INFO
- **Finding**: The plugin uses semantic versioning via GitHub Releases (`.github/workflows/release.yml` runs `npm version $RELEASE_VERSION`). TypeScript declaration files are published (`"types": "dist/src/plugin.d.ts"` in `package.json`). Each construct defines a JSON Schema for its configuration (e.g., `STORAGE_DEFINITION`, `QUEUE_DEFINITION`, `WEBHOOK_DEFINITION`), which are registered with the Serverless Framework's config schema handler. However, no explicit breaking-change detection tool (e.g., `buf breaking`, OpenAPI diff, Pact) is configured in CI. The CI pipeline runs unit tests and type checks but does not explicitly validate schema backward compatibility.
- **Implication**: Schema stability relies on TypeScript compilation and unit tests catching regressions, but there is no automated breaking-change detection for the construct configuration schemas. For a dev-library-application, this is an INFO concern — consumers pin versions via `package.json`.
- **Recommendation**: Consider adding a schema comparison step in CI to detect breaking changes in construct configuration schemas before release.
- **Evidence**: `package.json` (types, version), `.github/workflows/release.yml` (npm version), `src/constructs/aws/Storage.ts` (STORAGE_DEFINITION), `src/constructs/aws/Queue.ts` (QUEUE_DEFINITION), `src/plugin.ts` (registerConfigSchema)

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Field names throughout the codebase are semantically meaningful and self-documenting. Construct configuration properties use clear names: `encryption`, `archive`, `maxRetries`, `batchSize`, `maxBatchingWindow`, `maxConcurrency`, `fifo`, `delay`, `worker`, `alarm`, `path`, `authorizer`, `insecure`, `errorPage`, `domain`, `certificate`, `forwardedHeaders`. Variable outputs use descriptive names: `bucketName`, `bucketArn`, `queueUrl`, `queueArn`, `dlqUrl`, `dlqArn`, `tableName`, `tableArn`, `busName`, `url`, `cname`. No legacy abbreviations or cryptic codes found.
- **Implication**: The naming conventions support LLM reasoning about the plugin's configuration and outputs without requiring a data dictionary.
- **Recommendation**: No action required — naming quality is high.
- **Evidence**: `src/constructs/aws/Storage.ts` (variables()), `src/constructs/aws/Queue.ts` (QUEUE_DEFINITION, variables()), `src/constructs/aws/Webhook.ts` (WEBHOOK_DEFINITION, variables()), `src/constructs/aws/DatabaseDynamoDBSingleTable.ts` (variables())

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: The plugin has comprehensive documentation in `docs/` covering each construct: `storage.md`, `queue.md`, `webhook.md`, `server-side-website.md`, `single-page-app.md`, `static-website.md`, `database-dynamodb-single-table.md`, `configuration.md`, `permissions.md`, and `comparison.md`. The README provides a quick-start guide and construct overview. JSON Schema definitions embedded in each construct serve as machine-readable metadata for configuration validation.
- **Implication**: The documentation quality is good for understanding what constructs are available and how to configure them.
- **Recommendation**: No action required.
- **Evidence**: `docs/storage.md`, `docs/queue.md`, `docs/webhook.md`, `docs/server-side-website.md`, `README.md`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: INFO
- **Finding**: Library/utility — tracing and correlation are consumer concerns. The library's obligation is to propagate trace context if provided, which DISC-Q1 evaluates. has_http_rpc_surface=false. The plugin uses a simple logger (`src/utils/logger.ts`) that outputs to console with color formatting via `chalk`. The logger supports debug-level logging when `SLS_DEBUG` environment variable is set. No OpenTelemetry, X-Ray instrumentation, or structured JSON logging. This is expected for a CLI plugin — tracing would be on the generated resources.
- **Implication**: The Queue construct generates CloudWatch alarms for dead letter queues, and the Webhook construct creates API Gateway resources that can be instrumented with X-Ray. Observability is a property of the deployed resources.
- **Recommendation**: No action required for the plugin. Consumers should ensure generated resources have appropriate tracing and structured logging.
- **Evidence**: `src/utils/logger.ts` (console.log-based logger), `src/constructs/aws/Queue.ts` (CloudWatch Alarm generation)

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: INFO
- **Finding**: Library/utility — alerting on error rates and latency is a consumer concern. has_http_rpc_surface=false. The plugin generates CloudWatch alarms for the Queue construct's dead letter queue (`src/constructs/aws/Queue.ts` creates `Alarm` with `ApproximateNumberOfMessagesVisible` metric and SNS email subscription). No self-monitoring alerts exist on the plugin itself — expected for a build-time tool.
- **Implication**: The generated alerting (Queue DLQ alarm) is a positive indicator that the plugin provisions observability-aware resources.
- **Recommendation**: No action required.
- **Evidence**: `src/constructs/aws/Queue.ts` (Alarm, Topic, Subscription resources)

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics are published by the plugin. As a build-time CLI tool, the plugin has no runtime business metrics. The generated resources could be instrumented with custom CloudWatch metrics by the consuming application.
- **Implication**: Business outcome metrics are a concern for the deployed application, not for the build-time plugin.
- **Recommendation**: No action required.
- **Evidence**: No `cloudwatch.put_metric_data` or custom metric publishing found in the codebase — expected.

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: INFO
- **Finding**: Library/utility — dev-library-application override applies. has_http_rpc_surface=false AND has_auth_surface=false. Libraries, CLIs, and formatters do not own the IaC for API gateways, IAM roles, or networking — their consumers do. The plugin generates well-structured CloudFormation via CDK (IaC-as-code), but does not own deployed infrastructure for itself. The repository uses GitHub PR reviews (`.github/CONTRIBUTING.md`, `.github/pull_request_template.md`) and lint-staged hooks for code quality.
- **Implication**: Infrastructure governance is a concern for the deployed application. The plugin's contribution guidelines support code review.
- **Recommendation**: No action required.
- **Evidence**: `.github/workflows/ci.yml`, `.github/CONTRIBUTING.md`, `.github/pull_request_template.md`, `.husky/`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — API contract testing is not applicable. Library contract stability is evaluated by DISC-Q1 (schema/typed-export versioning). The CI pipeline (`.github/workflows/ci.yml`) includes: (1) Unit tests across Node 20/22/24 with Serverless v3, (2) ESLint linting with TypeScript rules, (3) Prettier format checking, (4) TypeScript type checking (`tsc --noEmit`). Release pipeline publishes to NPM on GitHub Release. No explicit contract testing (Pact) or breaking-change detection. Unit tests validate generated CloudFormation output against expected templates.
- **Implication**: The CI pipeline provides solid quality gates. Library contract stability is maintained via semver and TypeScript declarations.
- **Recommendation**: No action required for agent readiness. Consider adding automated breaking-change detection for construct schemas.
- **Evidence**: `.github/workflows/ci.yml` (unit-tests, lint, type jobs), `.github/workflows/release.yml` (npm publish), `jest.config.js`

#### ENG-Q3: Rollback Capability
- **Severity**: INFO
- **Finding**: No deployed HTTP/RPC surface — deployment rollback is a consumer concern. Library rollback is handled via package version pinning by consumers. The plugin is published to NPM; consumers can pin to specific versions in `package.json`. If a release breaks compatibility, consumers downgrade the version. The generated CloudFormation resources support CloudFormation stack rollback natively.
- **Implication**: Rollback for the plugin is NPM version pinning. Rollback for generated resources is CloudFormation stack rollback.
- **Recommendation**: No action required.
- **Evidence**: `.github/workflows/release.yml`, `package.json`

#### ENG-Q4: API Test Coverage
- **Severity**: INFO
- **Finding**: The plugin has comprehensive unit tests in `test/unit/`: `storage.test.ts`, `queues.test.ts`, `webhooks.test.ts`, `serverSideWebsite.test.ts`, `singlePageApp.test.ts`, `staticWebsite.test.ts`, `databasesDynamoDBSingleTable.test.ts`, `vpc.test.ts`, `stripe.test.ts`, `common.test.ts`, `extensions.test.ts`, `permissions.test.ts`, `variables.test.ts`. Tests validate the CloudFormation template output (resource properties, IAM policies, configuration validation). The CI matrix runs tests on Node 20, 22, 24. For a stateless-utility/library, this is INFO — the plugin's "API" is the construct configuration, not HTTP endpoints.
- **Implication**: Test coverage for construct behavior and CloudFormation output is solid. The test fixtures in `test/fixtures/` provide realistic configuration scenarios.
- **Recommendation**: No action required.
- **Evidence**: `test/unit/storage.test.ts`, `test/unit/queues.test.ts`, `test/unit/webhooks.test.ts`, `test/unit/serverSideWebsite.test.ts`, `test/unit/databasesDynamoDBSingleTable.test.ts`, `test/unit/vpc.test.ts`, `jest.config.js`, `.github/workflows/ci.yml`

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
| src/plugin.ts | API-Q1, API-Q4, API-Q5, AUTH-Q1, AUTH-Q4, AUTH-Q7, HITL-Q2 |
| src/providers/AwsProvider.ts | API-Q5, AUTH-Q1, AUTH-Q4, AUTH-Q7, DATA-Q2, STATE-Q1, ENG-Q1 |
| src/providers/StripeProvider.ts | AUTH-Q5, DATA-Q1 |
| src/constructs/aws/Storage.ts | API-Q1, API-Q2, AUTH-Q2, DISC-Q1, DISC-Q2, DATA-Q1, ENG-Q5 |
| src/constructs/aws/Queue.ts | API-Q1, API-Q2, API-Q7, AUTH-Q2, STATE-Q2, STATE-Q3, STATE-Q6, DATA-Q3, DATA-Q6, DISC-Q1, DISC-Q2, OBS-Q1, OBS-Q2, HITL-Q1, ENG-Q5 |
| src/constructs/aws/Webhook.ts | API-Q1, API-Q7, AUTH-Q1, AUTH-Q3 |
| src/constructs/aws/DatabaseDynamoDBSingleTable.ts | AUTH-Q2, DATA-Q1, DATA-Q3, DATA-Q4, DATA-Q5, DATA-Q7, DISC-Q2, ENG-Q5 |
| src/constructs/aws/ServerSideWebsite.ts | API-Q5 |
| src/constructs/aws/SinglePageApp.ts | — |
| src/constructs/aws/StaticWebsite.ts | — |
| src/constructs/aws/Vpc.ts | — |
| src/constructs/ConstructInterface.ts | API-Q1 |
| src/constructs/StaticConstructInterface.ts | API-Q1 |
| src/constructs/aws/index.ts | API-Q1 |
| src/CloudFormation.ts | AUTH-Q2, STATE-Q2 |
| src/classes/aws.ts | STATE-Q4 |
| src/utils/error.ts | API-Q3 |
| src/utils/logger.ts | AUTH-Q6, DATA-Q6, OBS-Q1 |
| src/utils/s3-sync.ts | STATE-Q4 |
| src/utils/sleep.ts | STATE-Q4 |
| src/utils/naming.ts | — |
| src/types/serverless.ts | API-Q1 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| .github/workflows/ci.yml | HITL-Q3, ENG-Q1, ENG-Q2, ENG-Q4 |
| .github/workflows/release.yml | DISC-Q1, ENG-Q2, ENG-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| package.json | API-Q1, API-Q2, DISC-Q1, ENG-Q3 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| tsconfig.json | ENG-Q2 |
| jest.config.js | ENG-Q4 |
| .eslintrc | ENG-Q2 |
| .prettierrc | ENG-Q2 |

### Documentation
| File | Questions Referenced |
|------|---------------------|
| README.md | DISC-Q3 |
| docs/storage.md | DISC-Q3 |
| docs/queue.md | DISC-Q3 |
| docs/webhook.md | DISC-Q3 |
| docs/server-side-website.md | DISC-Q3 |
| .github/CONTRIBUTING.md | ENG-Q1 |
| .github/pull_request_template.md | ENG-Q1 |

### Test Files
| File | Questions Referenced |
|------|---------------------|
| test/unit/storage.test.ts | ENG-Q4 |
| test/unit/queues.test.ts | ENG-Q4 |
| test/unit/webhooks.test.ts | ENG-Q4 |
| test/unit/serverSideWebsite.test.ts | ENG-Q4 |
| test/unit/databasesDynamoDBSingleTable.test.ts | ENG-Q4 |
| test/unit/vpc.test.ts | ENG-Q4 |
