# Agentic Readiness Analysis Report

**Target**: serverless-lift (https://github.com/getlift/lift)
**Date**: 2026-04-29
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**Repository Type**: application
**Service Archetype**: stateless-utility (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: typescript, serverless, iac
**Context**: Serverless Framework plugin providing higher-level AWS constructs.
**Archetype Justification**: The repository is an npm-published Serverless Framework plugin that synthesizes CloudFormation templates using AWS CDK constructs. It has no persistent state, no database connections, no message queue consumers, and no synchronous API surface — it operates as a build-time code-generation tool.

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 2 | **RISK-SAFETY**: 7 | **RISK-QUALITY**: 7 | **INFOs**: 19

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 2 |
| RISK-SAFETY | 7 |
| RISK-QUALITY | 7 |
| INFO | 19 |
| N/A | 0 |
| Not Evaluated (extended) | 8 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 11
**Extended Questions Not Triggered**: 8
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: stateless-utility (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### API-Q1: Documented API Interface

- **Severity**: BLOCKER
- **Finding**: The plugin does not expose a REST, GraphQL, or AsyncAPI interface. Its interface is a Serverless Framework plugin configuration schema defined in `serverless.yml` via the `constructs` and `providers` top-level properties. The plugin operates through Serverless Framework lifecycle hooks (`initialize`, `after:package:compileEvents`, `after:deploy:deploy`, etc.) and CLI commands (e.g., `serverless lift eject`, `serverless <construct>:logs`). There is no HTTP endpoint, no RPC interface, and no event-driven API that an agent could call via standard protocols.
- **Gap**: No standard API interface (REST, GraphQL, AsyncAPI) exists. An agent cannot consume this plugin through standard API protocols. Integration requires running the Serverless Framework CLI or using the plugin programmatically within a Node.js process.
- **Remediation**:
  - **Immediate**: Define a wrapper API (REST or CLI-to-API bridge) that exposes the plugin's capabilities as callable endpoints. Alternatively, document the CLI commands as a structured agent tool interface with input/output schemas.
  - **Target State**: A machine-callable interface (REST API, MCP server, or documented CLI tool schema) that an agent can invoke with predictable inputs and outputs.
  - **Estimated Effort**: Medium
  - **Dependencies**: API-Q2 (machine-readable spec would follow from a documented API)
- **Evidence**: `src/plugin.ts` (hooks, commands, configurationVariablesSources), `README.md` (YAML-based configuration examples), `src/constructs/StaticConstructInterface.ts` (command definitions)

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: The plugin generates AWS infrastructure (S3 buckets, DynamoDB tables, SQS queues, CloudFront distributions, VPCs) but applies no data classification tags to generated resources. The Storage construct enables encryption (`BucketEncryption.S3_MANAGED` by default, `KMS_MANAGED` optional) and blocks public access (`BlockPublicAccess.BLOCK_ALL`), which is a positive security posture. The Queue construct supports encryption (`kms`, `kmsManaged`). The DatabaseDynamoDBSingleTable construct enables point-in-time recovery. However, none of the generated resources include classification tags (e.g., `data-classification: confidential`, `contains-pii: true`). The Stripe provider handles API keys sourced from `STRIPE_API_KEY` environment variable or `~/.config/stripe/config.toml` files — these are credentials with no classification framework applied.
- **Gap**: No field-level or resource-level data classification exists. Generated resources have no classification tags. There is no mechanism to prevent an agent from accessing sensitive data without explicit authorization.
- **Remediation**:
  - **Immediate**: Add a `tags` or `classification` configuration option to each construct schema that allows users to specify data classification labels. Propagate these as AWS resource tags on generated S3 buckets, DynamoDB tables, SQS queues, etc.
  - **Target State**: Every generated resource includes data classification tags. A `classification` field in the construct schema maps to AWS resource tags and can be enforced by IAM policies and AWS Config rules.
  - **Estimated Effort**: Medium
  - **Dependencies**: None
- **Evidence**: `src/constructs/aws/Storage.ts` (encryption config, no classification tags), `src/constructs/aws/Queue.ts` (encryption support, no tags), `src/constructs/aws/DatabaseDynamoDBSingleTable.ts` (no tags), `src/providers/StripeProvider.ts` (API key handling)

---

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The plugin generates scoped IAM policy statements per construct type: Queue grants `sqs:SendMessage` and `sqs:ChangeMessageVisibility`; Storage grants `s3:PutObject`, `s3:GetObject`, `s3:DeleteObject`, `s3:ListBucket`; DatabaseDynamoDBSingleTable grants `dynamodb:GetItem`, `dynamodb:BatchGetItem`, `dynamodb:Query`, `dynamodb:Scan`, `dynamodb:PutItem`, `dynamodb:DeleteItem`, `dynamodb:BatchWriteItem`, `dynamodb:UpdateItem`, `dynamodb:ConditionCheckItem`. However, the `automaticPermissions` feature (enabled by default) appends these permissions to ALL Lambda functions in the stack via `iamRoleStatements`. There is no per-function scoping — every function gets every construct's permissions.
- **Gap**: Permissions are construct-scoped (specific actions on specific resources) but not function-scoped. All Lambda functions in the stack inherit all construct permissions. An agent using any function gets access to all constructs.
- **Compensating Controls**:
  - Disable automatic permissions (`lift.automaticPermissions: false`) and manually assign per-function IAM statements.
  - Use separate Serverless Framework services for different security domains.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement per-function permission scoping. Allow constructs to declare which functions should receive their permissions (e.g., `permissions: [myFunction]`).
- **Evidence**: `src/plugin.ts` (appendPermissions method), `src/constructs/aws/Queue.ts` (permissions()), `src/constructs/aws/Storage.ts` (permissions()), `src/constructs/aws/DatabaseDynamoDBSingleTable.ts` (permissions()), `docs/permissions.md`

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The plugin does not configure or generate audit logging infrastructure. There is no CloudTrail configuration, no immutable log storage, no S3 bucket with object lock for logs, and no CloudWatch log retention policies in the generated CloudFormation resources. The plugin's own operations (S3 sync, CloudFront invalidation, SQS message operations) are not logged with caller identity at the application layer. AWS CloudTrail would capture API calls at the AWS layer if enabled externally, but the plugin does not ensure this.
- **Gap**: No audit logging configuration exists in the plugin or its generated resources. Agent-initiated actions through the plugin have no application-level audit trail.
- **Compensating Controls**:
  - Enable AWS CloudTrail in the target AWS account to capture all API calls with principal attribution.
  - Use AWS Config rules to verify CloudTrail is enabled in all regions.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add an optional CloudTrail or application-level audit logging construct that can be included in the stack. At minimum, document the dependency on CloudTrail for audit compliance.
- **Evidence**: `src/providers/AwsProvider.ts` (no audit config), `src/classes/aws.ts` (no logging of caller identity), `src/utils/s3-sync.ts` (no audit trail for file operations)

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The plugin has no mechanism to suspend or revoke individual agent identities. The plugin runs with the caller's AWS credentials — identity management is fully delegated to AWS IAM. There are no plugin-specific API keys, no user management, and no revocation endpoints. Suspending an agent requires revoking the underlying IAM credentials externally through AWS IAM.
- **Gap**: No plugin-level agent identity suspension. Relies entirely on external AWS IAM management.
- **Compensating Controls**:
  - Use separate IAM roles per agent with the ability to deactivate access keys or modify role trust policies.
  - Implement AWS IAM Access Analyzer to detect and respond to anomalous agent behavior.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Document the IAM-based identity management approach and provide guidance for agent-specific IAM role configuration with suspension procedures.
- **Evidence**: `src/providers/AwsProvider.ts` (delegates to Serverless Framework AWS provider), `src/providers/StripeProvider.ts` (no revocation mechanism for Stripe API keys)

#### STATE-Q1: Compensation and Rollback ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The plugin generates CloudFormation resources. CloudFormation natively provides stack-level rollback on deployment failure, which is a significant compensating control. However, the plugin's post-deploy operations (S3 file synchronization in `s3-sync.ts`, CloudFront cache invalidation in `aws.ts`) execute outside of CloudFormation and have no compensation or rollback mechanism. If S3 sync uploads 50 files and fails on file 51, the first 50 files remain uploaded with no undo. The `preRemove` hook empties S3 buckets before CloudFormation deletion, but this is a destructive operation with no rollback.
- **Gap**: Post-deploy operations (S3 sync, CloudFront invalidation, SQS operations) have no rollback or compensation. CloudFormation rollback covers only the infrastructure provisioning phase.
- **Compensating Controls**:
  - Use S3 versioning (enabled by default in the Storage construct) to recover previous file states.
  - Implement CloudFormation changesets for review before deployment.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement a transactional wrapper for post-deploy operations that can undo partial S3 uploads on failure. Consider a dry-run mode for `s3-sync` that previews changes before executing.
- **Evidence**: `src/utils/s3-sync.ts` (no rollback on partial upload), `src/classes/aws.ts` (emptyBucket has no undo), `src/constructs/aws/abstracts/StaticWebsiteAbstract.ts` (preRemove empties bucket)

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The plugin makes AWS API calls (S3 ListObjects, PutObject, DeleteObjects; CloudFormation DescribeStacks; SQS SendMessage, ReceiveMessage; CloudFront CreateInvalidation) with no application-level rate limiting. The `s3-sync.ts` module uploads files in batches of 2 (`chunk(filesToUpload, 2)`) which provides some implicit throttling, but there is no formal rate limiting middleware, no configurable throttling, and no backoff on AWS API rate limit errors. The SQS polling in `queue/sqs.ts` makes 3 parallel requests with 200ms delays — minimal throttling. A runaway agent invoking these operations repeatedly could hit AWS API rate limits.
- **Gap**: No rate limiting on AWS API calls. No exponential backoff on throttling errors. No configurable concurrency limits.
- **Compensating Controls**:
  - AWS SDK has built-in retry with exponential backoff for throttling errors (HTTP 429).
  - AWS service quotas and API Gateway throttling provide external rate protection.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add configurable concurrency and rate limits to file upload operations. Implement exponential backoff with jitter for all AWS API calls.
- **Evidence**: `src/utils/s3-sync.ts` (batch size of 2, no rate limiting), `src/constructs/aws/queue/sqs.ts` (3 parallel requests, 200ms delay), `src/classes/aws.ts` (no retry/backoff)

#### DATA-Q2: Data Residency and Sovereignty ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The plugin sources the AWS region from the Serverless Framework provider configuration (`serverless.getProvider("aws").getRegion()`). All generated resources are deployed to this region. However, the plugin has no explicit data residency controls, no documentation about data sovereignty implications, and no guardrails to prevent deploying to regions that violate residency requirements. The Stripe provider makes API calls to Stripe's global infrastructure with no region control.
- **Gap**: No explicit data residency controls or documentation. Region is configurable but not validated against residency policies.
- **Compensating Controls**:
  - AWS Organizations SCPs can restrict deployable regions.
  - Serverless Framework provider region is explicitly configured by the user.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document data residency considerations. Consider adding a region validation check against a configurable allow-list.
- **Evidence**: `src/providers/AwsProvider.ts` (region from Serverless provider), `src/providers/StripeProvider.ts` (no region control for Stripe API calls)

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The plugin's logger (`src/utils/logger.ts`) is a thin wrapper around `console.log` with no PII redaction, scrubbing, or filtering capabilities. Log output includes file paths, S3 bucket names, S3 object keys, SQS queue URLs, CloudFront distribution IDs, and CloudFormation stack names. The SQS queue operations (`Queue.ts`) log message IDs and display full SQS message bodies to the console (`formatMessageBody`). Error messages in `s3-sync.ts` include S3 error details. While the plugin does not directly process customer PII, the SQS message bodies displayed via `listDlq` may contain PII if the queue processes user data.
- **Gap**: No PII redaction in logs. SQS message bodies are printed in full. No log scrubbing middleware.
- **Compensating Controls**:
  - Run the plugin in environments where console output is not persisted or is redirected to secure log storage.
  - Ensure SQS queues used with the plugin do not contain PII in message bodies.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a log sanitization layer that masks sensitive patterns (API keys, PII-like data) before output. Add a `--redact` flag to the `failed` command that masks SQS message bodies.
- **Evidence**: `src/utils/logger.ts` (no scrubbing), `src/constructs/aws/Queue.ts` (formatMessageBody prints full message body), `src/utils/s3-sync.ts` (logs file paths and S3 keys)

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, GraphQL schema, or equivalent machine-readable specification file exists in the repository. The plugin defines JSON Schema objects for each construct type directly in TypeScript code (e.g., `QUEUE_DEFINITION`, `STORAGE_DEFINITION`, `WEBHOOK_DEFINITION`, `DATABASE_DEFINITION`). These schemas are registered with the Serverless Framework's `configSchemaHandler` for validation but are not extracted as standalone, published schema files.
- **Gap**: Configuration schemas exist but are embedded in TypeScript code. No standalone machine-readable specification for agent tool generation.
- **Compensating Controls**:
  - Extract JSON Schema definitions from TypeScript source as a build step and publish them as standalone files.
  - The Serverless Framework's schema validation provides some runtime contract enforcement.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a build step that extracts the JSON Schema definitions from TypeScript and publishes them as `schemas/*.json` files alongside the npm package.
- **Evidence**: `src/constructs/aws/Queue.ts` (QUEUE_DEFINITION), `src/constructs/aws/Storage.ts` (STORAGE_DEFINITION), `src/constructs/aws/Webhook.ts` (WEBHOOK_DEFINITION), `src/plugin.ts` (registerConfigSchema)

#### AUTH-Q5: Credential Management — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The Stripe provider reads API keys from the `STRIPE_API_KEY` environment variable or from a TOML configuration file at `~/.config/stripe/config.toml`. No secrets management system (AWS Secrets Manager, HashiCorp Vault) is integrated. AWS credentials are managed by the Serverless Framework and typically sourced from `~/.aws/credentials` or environment variables. No hardcoded credentials were found in the source code. The `.gitignore` is properly configured. No `.env` files are committed.
- **Gap**: Credentials are managed via environment variables and local config files, not through a centralized secrets management system with rotation.
- **Compensating Controls**:
  - AWS credentials can be sourced from IAM roles (EC2, ECS, Lambda) which rotate automatically.
  - CI/CD pipelines can source secrets from GitHub Actions secrets or AWS Secrets Manager.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add optional Secrets Manager integration for the Stripe provider to read API keys from Secrets Manager instead of environment variables.
- **Evidence**: `src/providers/StripeProvider.ts` (STRIPE_API_KEY env var, TOML config file), `src/providers/AwsProvider.ts` (delegates to Serverless Framework AWS provider)

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The repository has a comprehensive unit test suite (3,115 lines across 13 test files) with test fixtures in `test/fixtures/`. The CI pipeline runs tests across Node.js 20, 22, and 24 with Serverless Framework v3. Tests use `runServerless()` to simulate Serverless Framework operations and validate generated CloudFormation templates. However, there is no production-equivalent staging environment, no docker-compose for local testing, no seed data scripts, and no synthetic data generators. Testing is limited to unit tests against generated CloudFormation templates — there is no integration testing against actual AWS resources.
- **Gap**: No staging or sandbox environment. Unit tests validate CloudFormation template generation but not deployed resource behavior.
- **Compensating Controls**:
  - Use a dedicated AWS account/environment for testing deployments.
  - The `serverless package` command generates templates without deploying — enables dry-run validation.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add integration tests that deploy to a test AWS account and validate resource creation. Consider adding `docker-compose` or LocalStack configuration for local testing.
- **Evidence**: `test/unit/` (13 test files, 3115 lines), `test/fixtures/` (14 fixture directories), `.github/workflows/ci.yml` (Node matrix, unit tests only), `jest.config.js`

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The plugin defines JSON Schema objects for each construct type in TypeScript, but there is no schema versioning mechanism. Configuration schemas are not versioned independently — they change with the npm package version. No breaking change detection tool runs in CI (no `buf breaking`, no OpenAPI diff, no schema comparison). The GitHub release workflow (`release.yml`) publishes to npm with semantic versioning, and the README documents constructs with configuration examples. However, there is no CHANGELOG file, no deprecation notices in code, and no automated detection of schema breaking changes.
- **Gap**: No independent schema versioning. No breaking change detection in CI. Schema changes are only caught by downstream test failures, not proactively.
- **Compensating Controls**:
  - npm semantic versioning signals breaking changes (major version bumps).
  - JSON Schema definitions in TypeScript are type-checked, preventing accidental type changes.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a schema snapshot test that detects configuration schema changes. Implement a CHANGELOG and deprecation notice mechanism for schema changes.
- **Evidence**: `src/constructs/aws/Queue.ts` (QUEUE_DEFINITION), `src/constructs/aws/Storage.ts` (STORAGE_DEFINITION), `.github/workflows/release.yml` (npm publish, no schema diff), `package.json` (version field)

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The plugin uses a custom logger (`src/utils/logger.ts`) that wraps `console.log` with color formatting. Logs are plain text, not structured JSON. There is no distributed tracing (no OpenTelemetry, no X-Ray), no trace ID propagation, and no correlation IDs linking operations. The logger supports `debug`, `verbose`, `success`, `warning`, and `error` levels but outputs unstructured text. When the plugin runs as a Serverless Framework plugin, log output goes to the terminal.
- **Gap**: No structured logging (JSON). No distributed tracing. No correlation IDs.
- **Compensating Controls**:
  - AWS CloudTrail captures AWS API calls with request IDs that can be correlated.
  - The Serverless Framework provides its own logging context for plugin operations.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Migrate the logger to structured JSON output with correlation IDs. Consider integrating OpenTelemetry for plugin operations tracing.
- **Evidence**: `src/utils/logger.ts` (console.log wrapper, no JSON, no correlation IDs)

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The Queue construct generates CloudWatch Alarms for DLQ message counts — this is a positive finding for generated resources. The alarm triggers when `ApproximateNumberOfMessagesVisible > 0` in the DLQ with email notification via SNS. However, no alerting exists for the plugin's own operations — S3 sync failures, CloudFront invalidation failures, or CloudFormation deployment failures have no alerting configured at the plugin level.
- **Gap**: Alerting exists for generated Queue DLQ resources but not for the plugin's own operational failures.
- **Compensating Controls**:
  - CI/CD pipeline failures surface deployment errors.
  - AWS CloudWatch can alert on CloudFormation stack failure events.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document recommended CloudWatch alarms for monitoring Lift-generated resources. Consider adding a monitoring/alerting construct.
- **Evidence**: `src/constructs/aws/Queue.ts` (Alarm construct with SNS topic), `src/classes/aws.ts` (no error alerting)

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The CI pipeline (`.github/workflows/ci.yml`) runs three jobs: unit tests (across Node 20/22/24 with Serverless v3), lint (ESLint + Prettier), and type checks (TypeScript `tsc --noEmit`). Unit tests validate generated CloudFormation template structure using Jest snapshots and `toMatchObject` assertions. However, there is no consumer-driven contract testing (Pact), no schema comparison tool, and no automated detection of breaking changes to the plugin's configuration schema or generated CloudFormation output.
- **Gap**: CI validates CloudFormation output via unit tests but has no formal API contract testing or breaking change detection for the plugin's configuration interface.
- **Compensating Controls**:
  - Unit tests with `toMatchObject` and `toStrictEqual` assertions serve as informal schema contracts.
  - TypeScript type checking catches type-level breaking changes.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add schema snapshot tests that fail when configuration schemas change. Consider adding a breaking change detection step to CI.
- **Evidence**: `.github/workflows/ci.yml` (unit tests, lint, type checks), `test/unit/queues.test.ts` (CloudFormation template validation), `test/unit/storage.test.ts` (property assertions)

---

## INFOs — Architecture and Design Inputs

### API-Q3: Structured Error Responses

- **Severity**: INFO
- **Finding**: The plugin uses a custom `ServerlessError` class (`src/utils/error.ts`) that provides structured errors with a `message` (human-readable) and a `code` (machine-readable, e.g., `LIFT_UNKNOWN_CONSTRUCT_TYPE`, `LIFT_INVALID_CONSTRUCT_CONFIGURATION`, `LIFT_VARIABLE_UNKNOWN_CONSTRUCT`). Error codes follow a consistent `LIFT_*` prefix pattern. All constructs throw `ServerlessError` for configuration validation failures. This is a well-structured error handling pattern for a CLI tool.
- **Implication**: Agent tool wrappers can parse error codes to distinguish configuration errors from runtime errors.
- **Recommendation**: Document the complete list of error codes in a reference page.
- **Evidence**: `src/utils/error.ts` (ServerlessError class), `src/plugin.ts` (error codes), `src/constructs/aws/Queue.ts` (LIFT_INVALID_CONSTRUCT_CONFIGURATION)

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The plugin generates CloudFormation resources. CloudFormation deployments are inherently idempotent — deploying the same template produces the same stack state. The S3 sync operation (`s3-sync.ts`) computes ETags and skips unchanged files, providing idempotent upload behavior. SQS message operations (send, purge, retry) are not idempotent.
- **Implication**: For read-only agent scope, idempotency is not a concern. If write scope is added, SQS operations would need idempotency keys.
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: `src/utils/s3-sync.ts` (ETag comparison for idempotent uploads), `src/constructs/aws/Queue.ts` (sendMessage — not idempotent)

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: The plugin's output is structured CloudFormation JSON/YAML templates (generated via CDK `app.synth()`). CLI output includes structured information via `CfnOutput` values (queue URLs, bucket names, website domains). The `eject` command outputs formatted YAML. All construct `variables()` methods return structured key-value objects.
- **Implication**: Agent tool wrappers can parse CloudFormation JSON output and CfnOutput values reliably.
- **Recommendation**: Consider adding a `--json` output flag for CLI commands to produce machine-parseable output.
- **Evidence**: `src/plugin.ts` (info(), eject()), `src/providers/AwsProvider.ts` (appendCloudformationResources)

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limit documentation exists for the plugin's operations. The plugin does not impose its own rate limits and does not return rate limit headers. Rate limiting is delegated to the underlying AWS services (S3, SQS, CloudFormation, CloudFront), each of which has its own service quotas and throttling behavior.
- **Implication**: Agents invoking the plugin should be aware of AWS service quotas for the operations being performed (e.g., S3 PutObject, CloudFormation API limits).
- **Recommendation**: Document AWS service quota dependencies for each construct type.
- **Evidence**: `src/utils/s3-sync.ts` (no rate limit headers), `src/constructs/aws/queue/sqs.ts` (no throttling documentation)

### AUTH-Q1: Machine Identity Authentication

- **Severity**: INFO
- **Finding**: The plugin delegates authentication entirely to AWS IAM credentials managed by the Serverless Framework provider. AWS IAM supports machine identity via IAM users, IAM roles, OIDC federation, and service accounts. CloudTrail provides principal attribution for all AWS API calls. The Stripe provider authenticates via API keys sourced from environment variables or TOML config files. Both authentication paths support machine identity at the platform layer.
- **Implication**: Agent integration should use dedicated IAM roles with CloudTrail enabled for attribution.
- **Recommendation**: Document recommended IAM role configuration for agent-based deployments.
- **Evidence**: `src/providers/AwsProvider.ts` (delegates to Serverless Framework AWS provider), `src/providers/StripeProvider.ts` (API key authentication)

### AUTH-Q3: Action-Level Authorization

- **Severity**: INFO
- **Finding**: The plugin generates granular, action-level IAM policy statements per construct. Queue: `sqs:SendMessage`, `sqs:ChangeMessageVisibility`. Storage: `s3:PutObject`, `s3:GetObject`, `s3:DeleteObject`, `s3:ListBucket`. DatabaseDynamoDBSingleTable: `dynamodb:GetItem`, `dynamodb:BatchGetItem`, `dynamodb:Query`, `dynamodb:Scan`, `dynamodb:PutItem`, `dynamodb:DeleteItem`, `dynamodb:BatchWriteItem`, `dynamodb:UpdateItem`, `dynamodb:ConditionCheckItem`. The Webhook construct generates IAM role with `events:PutEvents` scoped to the specific EventBus. This is a strong action-level authorization pattern.
- **Implication**: Generated IAM policies support fine-grained action-level authorization. Agents can be constrained to specific actions per resource.
- **Recommendation**: Consider offering read-only permission profiles (e.g., `Storage` with only `s3:GetObject`, `s3:ListBucket`) as an option.
- **Evidence**: `src/constructs/aws/Queue.ts` (permissions()), `src/constructs/aws/Storage.ts` (permissions()), `src/constructs/aws/DatabaseDynamoDBSingleTable.ts` (permissions()), `src/CloudFormation.ts` (PolicyStatement class)

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: INFO
- **Finding**: The plugin is a build-time CLI tool — identity propagation is not applicable in the traditional sense. The plugin runs with the deployer's AWS credentials and does not proxy requests between services. The generated resources (Lambda functions, API Gateway, SQS) would handle identity propagation at runtime, which is outside the plugin's scope.
- **Implication**: Identity propagation is a runtime concern for the generated infrastructure, not the plugin itself.
- **Recommendation**: No action needed. This is correctly handled by the generated infrastructure.
- **Evidence**: `src/providers/AwsProvider.ts` (single credential context)

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The plugin has no concurrency controls. S3 sync operations do not use optimistic locking or conditional writes. Multiple concurrent deployments of the same stack could conflict. The `s3-sync.ts` uses ETag comparison for upload decisions but does not handle concurrent modifications.
- **Implication**: For read-only agent scope, concurrency controls are not a concern. If multiple agents deploy concurrently, CloudFormation's own locking (stack operations are serialized) provides protection.
- **Recommendation**: Document that concurrent deployments of the same stack should be avoided.
- **Evidence**: `src/utils/s3-sync.ts` (no locking), `src/constructs/aws/queue/sqs.ts` (no concurrency control)

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The plugin has no configurable transaction limits. S3 sync uploads all files found in the source directory with no maximum. SQS retry operations process all messages in the DLQ with no limit. The `emptyBucket` function deletes all objects with no safeguard.
- **Implication**: For read-only agent scope, transaction limits are not a concern. If write scope is added, the `emptyBucket` and SQS retry operations would need configurable limits.
- **Recommendation**: Add configurable limits for batch operations (e.g., `maxFilesPerSync`, `maxMessagesPerRetry`).
- **Evidence**: `src/utils/s3-sync.ts` (no file count limit), `src/constructs/aws/Queue.ts` (retryDlq processes all messages), `src/classes/aws.ts` (emptyBucket deletes all)

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The plugin leverages CloudFormation's deployment lifecycle, which inherently provides a plan/review/execute pattern. The `serverless package` command generates CloudFormation templates without deploying — this is a "draft" stage. CloudFormation changesets allow reviewing proposed changes before execution. The `lift eject` command exports the generated CloudFormation for manual review.
- **Implication**: CloudFormation's changeset model provides a natural HITL pattern for infrastructure changes.
- **Recommendation**: Document the `serverless package` → review → `serverless deploy` workflow as the recommended HITL pattern.
- **Evidence**: `src/plugin.ts` (eject command, package hook), `src/providers/AwsProvider.ts` (appendCloudformationResources)

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: CloudFormation changesets provide a review step that can be used as an approval gate. The `serverless package` command generates the template without deploying. The `lift eject` command outputs the CloudFormation template for manual review. However, there is no plugin-level configurable approval gate (e.g., "require human approval before deploying this construct type").
- **Implication**: Approval gates can be implemented at the CI/CD layer using CloudFormation changeset review.
- **Recommendation**: Consider adding a `requireApproval` option per construct that pauses deployment until human confirmation.
- **Evidence**: `src/plugin.ts` (eject command), `.github/workflows/release.yml` (manual release trigger)

### DATA-Q5: Temporal Metadata and Freshness

- **Severity**: INFO
- **Finding**: The plugin does not handle temporal metadata. It generates static CloudFormation templates based on configuration. There are no timestamps, no cache headers, no freshness signals. The `computeS3ETag` function uses MD5 hashes for content comparison, not temporal metadata.
- **Implication**: As a stateless-utility generating static infrastructure definitions, temporal metadata is not applicable.
- **Recommendation**: No action needed.
- **Evidence**: `src/utils/s3-sync.ts` (ETag-based content comparison, no timestamps)

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality metrics, profiling, or completeness monitoring exists. The plugin validates configuration input against JSON Schema definitions, which provides input quality assurance. TypeScript type checking provides compile-time quality for the plugin's code.
- **Implication**: Input validation via JSON Schema provides a form of data quality control for configuration.
- **Recommendation**: No action needed for a build-time tool.
- **Evidence**: `src/plugin.ts` (registerConfigSchema), `src/constructs/aws/Queue.ts` (QUEUE_DEFINITION with validation rules)

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Configuration field names are highly semantic and human-readable: `worker`, `maxRetries`, `alarm`, `batchSize`, `maxBatchingWindow`, `maxConcurrency`, `fifo`, `delay`, `encryption`, `encryptionKey`, `path`, `domain`, `certificate`, `errorPage`, `assets`, `forwardedHeaders`, `redirectToMainDomain`, `localSecondaryIndexes`, `gsiCount`, `authorizer`, `insecure`, `eventType`, `method`. No legacy abbreviations or codes are used.
- **Implication**: Agent tool definitions can use these field names directly without a data dictionary.
- **Recommendation**: Maintain this naming convention.
- **Evidence**: `src/constructs/aws/Queue.ts` (QUEUE_DEFINITION), `src/constructs/aws/Storage.ts` (STORAGE_DEFINITION), `src/constructs/aws/Webhook.ts` (WEBHOOK_DEFINITION)

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No formal data catalog exists. Documentation in `docs/` provides per-construct reference pages: `queue.md`, `storage.md`, `webhook.md`, `single-page-app.md`, `static-website.md`, `server-side-website.md`, `database-dynamodb-single-table.md`. The README provides a constructs overview with configuration examples. The `permissions.md` documents IAM permission behavior.
- **Implication**: Documentation serves as an informal metadata layer. Agent tool builders can reference `docs/` for construct capabilities.
- **Recommendation**: Consider generating a machine-readable construct catalog from the TypeScript schema definitions.
- **Evidence**: `docs/` (7 construct docs + permissions + configuration + comparison), `README.md`

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No custom business outcome metrics are published. The Queue construct generates CloudWatch alarms for DLQ message counts, which is an operational metric. No broader business metrics (deployment success rate, construct usage, configuration errors) are tracked.
- **Implication**: For a build-time CLI tool, business metrics would be "deployment success rate" and "construct adoption." These are better tracked at the CI/CD or platform level.
- **Recommendation**: Consider adding telemetry for construct usage and deployment outcomes (opt-in).
- **Evidence**: `src/constructs/aws/Queue.ts` (Alarm construct — operational metric only)

### ENG-Q1: Infrastructure Governance for Agent-Facing Surface

- **Severity**: INFO
- **Finding**: The plugin IS infrastructure-as-code — it generates CloudFormation templates via AWS CDK. The plugin itself has no deployed infrastructure to govern (it's an npm package). Changes to the plugin are subject to peer review via GitHub PRs (`.github/CONTRIBUTING.md`, `pull_request_template.md`). The CI pipeline validates changes via tests, lint, and type checks. No drift detection is needed because the plugin is not deployed infrastructure.
- **Implication**: The plugin's governance model is appropriate for a library — peer review + CI + npm versioning.
- **Recommendation**: No action needed.
- **Evidence**: `.github/workflows/ci.yml` (CI pipeline), `.github/CONTRIBUTING.md`, `.github/pull_request_template.md`, `.github/workflows/release.yml` (npm publish on GitHub release)

### ENG-Q3: Rollback Capability

- **Severity**: INFO
- **Finding**: Rollback is achieved through npm package versioning — consumers can pin to a specific version (`serverless-lift@1.x.y`) and roll back by changing the version. GitHub releases provide tagged, immutable release artifacts. The npm publish workflow uses GitHub's release mechanism. CloudFormation stacks generated by the plugin can be rolled back via CloudFormation's native rollback capability.
- **Implication**: Rollback to a known-good plugin version is straightforward via version pinning.
- **Recommendation**: Document the version rollback procedure for consumers.
- **Evidence**: `package.json` (version field), `.github/workflows/release.yml` (version from GitHub release tag)

### ENG-Q4: API Test Coverage

- **Severity**: INFO
- **Finding**: The test suite covers all 8 construct types and both providers with 13 test files totaling 3,115 lines. Tests validate: CloudFormation template structure (resource types, properties), IAM policy generation, configuration validation (error cases), CLI command behavior (queue send, failed, retry), variable resolution, VPC configuration, and Stripe provider integration. Tests use the `runServerless()` utility to simulate full Serverless Framework lifecycle including template generation.
- **Implication**: Test coverage is comprehensive for a plugin of this type. Tests validate the plugin's "API" (configuration → CloudFormation output).
- **Recommendation**: Consider adding schema snapshot tests to detect configuration schema changes.
- **Evidence**: `test/unit/queues.test.ts` (782 lines), `test/unit/serverSideWebsite.test.ts` (706 lines), `test/unit/staticWebsite.test.ts` (653 lines), `test/unit/` (13 test files, 3115 lines total)

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: BLOCKER
- **Finding**: The plugin does not expose a REST, GraphQL, or AsyncAPI interface. Its interface is a Serverless Framework plugin configuration schema defined in `serverless.yml` via `constructs` and `providers` top-level properties. The plugin operates through Serverless Framework lifecycle hooks and CLI commands. There is no HTTP endpoint or event-driven API that an agent could call via standard protocols.
- **Gap**: No standard API interface exists. Agent integration requires running the Serverless Framework CLI or using the plugin programmatically.
- **Recommendation**: Define a wrapper API or MCP server that exposes the plugin's capabilities as callable endpoints with documented input/output schemas.
- **Evidence**: `src/plugin.ts`, `README.md`, `src/constructs/StaticConstructInterface.ts`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: No standalone machine-readable specification exists. JSON Schema objects are defined in TypeScript for each construct type but are embedded in code, not published as standalone schema files.
- **Gap**: No extractable machine-readable specification for agent tool generation.
- **Recommendation**: Extract JSON Schema definitions as standalone `schemas/*.json` files in the npm package.
- **Evidence**: `src/constructs/aws/Queue.ts` (QUEUE_DEFINITION), `src/constructs/aws/Storage.ts` (STORAGE_DEFINITION), `src/plugin.ts` (registerConfigSchema)

#### API-Q3: Structured Error Responses
- **Severity**: INFO
- **Finding**: `ServerlessError` class provides structured errors with machine-readable codes (`LIFT_*` prefix) and human-readable messages. Consistent pattern across all constructs and providers.
- **Gap**: N/A — structured errors are well-implemented.
- **Recommendation**: Document the complete list of error codes.
- **Evidence**: `src/utils/error.ts`, `src/plugin.ts`, `src/constructs/aws/Queue.ts`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: CloudFormation deployments are inherently idempotent. S3 sync uses ETag comparison for idempotent uploads. SQS operations are not idempotent.
- **Gap**: SQS message send operations lack idempotency keys (relevant only for write scope).
- **Recommendation**: No action for read-only scope.
- **Evidence**: `src/utils/s3-sync.ts`, `src/constructs/aws/Queue.ts`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: Output is structured CloudFormation JSON/YAML. CLI outputs include CfnOutput values. The `eject` command outputs formatted YAML.
- **Gap**: CLI output is text-formatted, not machine-parseable JSON by default.
- **Recommendation**: Consider adding `--json` output flag for CLI commands.
- **Evidence**: `src/plugin.ts`, `src/providers/AwsProvider.ts`

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
- **Finding**: No rate limit documentation. The plugin delegates to AWS services which have their own rate limits and throttling. No `X-RateLimit-Remaining` or `Retry-After` headers.
- **Gap**: AWS service quota dependencies are not documented per construct type.
- **Recommendation**: Document AWS service quota dependencies.
- **Evidence**: `src/utils/s3-sync.ts`, `src/constructs/aws/queue/sqs.ts`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: Authentication is delegated to AWS IAM via the Serverless Framework provider. AWS IAM supports machine identity (users, roles, OIDC). CloudTrail provides attribution. The Stripe provider uses API keys from environment or config files.
- **Gap**: No plugin-specific agent identity mechanism, but AWS IAM provides this at the platform layer.
- **Recommendation**: Document recommended IAM role configuration for agent-based deployments.
- **Evidence**: `src/providers/AwsProvider.ts`, `src/providers/StripeProvider.ts`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: Generated IAM policies use specific actions per construct, but `automaticPermissions` grants all construct permissions to all Lambda functions in the stack. No per-function scoping.
- **Gap**: Permissions are construct-scoped but not function-scoped.
- **Recommendation**: Implement per-function permission scoping.
- **Evidence**: `src/plugin.ts` (appendPermissions), `docs/permissions.md`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: INFO
- **Finding**: Granular action-level IAM policies per construct. Queue: `sqs:SendMessage`, `sqs:ChangeMessageVisibility`. Storage: S3 CRUD operations. Database: DynamoDB read/write operations. Webhook: `events:PutEvents`.
- **Gap**: N/A — action-level authorization is well-implemented.
- **Recommendation**: Offer read-only permission profiles as a construct option.
- **Evidence**: `src/constructs/aws/Queue.ts`, `src/constructs/aws/Storage.ts`, `src/constructs/aws/DatabaseDynamoDBSingleTable.ts`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: Build-time CLI tool — identity propagation not applicable. The plugin runs with a single set of AWS credentials.
- **Gap**: N/A for stateless-utility archetype.
- **Recommendation**: No action needed.
- **Evidence**: `src/providers/AwsProvider.ts`

#### AUTH-Q5: Credential Management
- **Severity**: RISK-QUALITY
- **Finding**: Stripe API keys read from `STRIPE_API_KEY` env var or TOML config file. AWS credentials from Serverless Framework provider. No secrets manager integration. No hardcoded secrets found.
- **Gap**: No centralized secrets management with rotation.
- **Recommendation**: Add optional Secrets Manager integration for the Stripe provider.
- **Evidence**: `src/providers/StripeProvider.ts`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No audit logging configuration in the plugin or generated resources. Plugin operations have no application-level audit trail. AWS CloudTrail would capture API calls if enabled externally.
- **Gap**: No audit logging. Depends on external CloudTrail configuration.
- **Recommendation**: Add optional audit logging construct or document CloudTrail dependency.
- **Evidence**: `src/providers/AwsProvider.ts`, `src/classes/aws.ts`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: No plugin-level identity suspension. Relies on external AWS IAM management to revoke credentials.
- **Gap**: No plugin-level agent identity revocation mechanism.
- **Recommendation**: Document IAM-based identity management for agent suspension.
- **Evidence**: `src/providers/AwsProvider.ts`, `src/providers/StripeProvider.ts`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: CloudFormation provides native stack rollback. Post-deploy operations (S3 sync, CloudFront invalidation) have no rollback. S3 versioning provides file recovery as a partial compensating control.
- **Gap**: Post-deploy operations have no compensation or rollback mechanism.
- **Recommendation**: Implement transactional wrapper for post-deploy operations with dry-run mode.
- **Evidence**: `src/utils/s3-sync.ts`, `src/classes/aws.ts`, `src/constructs/aws/abstracts/StaticWebsiteAbstract.ts`

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
- **Finding**: No concurrency controls. CloudFormation serializes stack operations natively.
- **Gap**: No application-level concurrency controls for S3 sync operations.
- **Recommendation**: Document that concurrent deployments of the same stack should be avoided.
- **Evidence**: `src/utils/s3-sync.ts`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has external dependencies (calls other services or external APIs)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No rate limiting on AWS API calls. S3 sync batches files in groups of 2. SQS polling makes 3 parallel requests with 200ms delays. No formal rate limits, no exponential backoff.
- **Gap**: No rate limiting. No backoff on throttling errors.
- **Recommendation**: Add configurable concurrency limits and exponential backoff for AWS API calls.
- **Evidence**: `src/utils/s3-sync.ts`, `src/constructs/aws/queue/sqs.ts`, `src/classes/aws.ts`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits. S3 sync uploads all files. SQS retry processes all messages. `emptyBucket` deletes all objects.
- **Gap**: No transaction limits on batch operations.
- **Recommendation**: Add configurable limits for batch operations.
- **Evidence**: `src/utils/s3-sync.ts`, `src/constructs/aws/Queue.ts`, `src/classes/aws.ts`

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
- **Finding**: CloudFormation changesets and `serverless package` provide draft/review capabilities. The `lift eject` command exports templates for review.
- **Gap**: No plugin-level draft state beyond CloudFormation's model.
- **Recommendation**: Document the package → review → deploy workflow.
- **Evidence**: `src/plugin.ts`

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: CloudFormation changesets provide review. No plugin-level approval gates.
- **Gap**: No per-construct approval gate configuration.
- **Recommendation**: Consider adding `requireApproval` option per construct.
- **Evidence**: `src/plugin.ts`, `.github/workflows/release.yml`

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive unit test suite (3,115 lines, 13 files) with test fixtures. CI tests across Node 20/22/24. No production-equivalent staging, no docker-compose, no integration tests against real AWS resources.
- **Gap**: No staging environment. Testing limited to CloudFormation template validation.
- **Recommendation**: Add integration tests with a test AWS account or LocalStack.
- **Evidence**: `test/unit/`, `test/fixtures/`, `.github/workflows/ci.yml`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: No data classification tags on generated resources. Storage construct has encryption (S3_MANAGED or KMS_MANAGED) and `BlockPublicAccess.BLOCK_ALL`. Queue supports KMS encryption. Database has point-in-time recovery. But no classification tagging framework.
- **Gap**: No field-level or resource-level data classification.
- **Recommendation**: Add `classification` configuration option and propagate as AWS resource tags.
- **Evidence**: `src/constructs/aws/Storage.ts`, `src/constructs/aws/Queue.ts`, `src/constructs/aws/DatabaseDynamoDBSingleTable.ts`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Region from Serverless Framework provider. No explicit data residency controls. Stripe provider makes calls to Stripe global infrastructure without region control.
- **Gap**: No data residency controls or documentation.
- **Recommendation**: Document data residency considerations and add region validation.
- **Evidence**: `src/providers/AwsProvider.ts`, `src/providers/StripeProvider.ts`

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
- **Severity**: INFO
- **Finding**: No temporal metadata. Plugin generates static CloudFormation templates. S3 sync uses ETag content hashing, not timestamps.
- **Gap**: N/A — temporal metadata not applicable for static infrastructure generation.
- **Recommendation**: No action needed.
- **Evidence**: `src/utils/s3-sync.ts`

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: Logger is a plain console.log wrapper with no PII redaction. SQS message bodies printed in full via `formatMessageBody`. Log output includes S3 keys, bucket names, queue URLs.
- **Gap**: No PII redaction. SQS message bodies may contain PII.
- **Recommendation**: Add log sanitization and `--redact` flag for SQS commands.
- **Evidence**: `src/utils/logger.ts`, `src/constructs/aws/Queue.ts`, `src/utils/s3-sync.ts`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics. JSON Schema validation provides input quality assurance for configuration.
- **Gap**: N/A — data quality not applicable for a build-time tool.
- **Recommendation**: No action needed.
- **Evidence**: `src/plugin.ts` (registerConfigSchema)

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: JSON schemas defined in TypeScript per construct. No independent schema versioning. No breaking change detection in CI. GitHub releases with semantic versioning. No CHANGELOG.
- **Gap**: No breaking change detection. No schema versioning independent of npm version.
- **Recommendation**: Add schema snapshot tests and breaking change detection.
- **Evidence**: `src/constructs/aws/Queue.ts`, `.github/workflows/release.yml`, `package.json`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: All field names are semantic and human-readable: `worker`, `maxRetries`, `batchSize`, `encryption`, `path`, `domain`, `certificate`, etc.
- **Gap**: N/A — excellent naming conventions.
- **Recommendation**: Maintain this standard.
- **Evidence**: `src/constructs/aws/Queue.ts`, `src/constructs/aws/Storage.ts`, `src/constructs/aws/Webhook.ts`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: Documentation in `docs/` with per-construct reference pages. README provides overview. No formal data catalog.
- **Gap**: No machine-readable construct catalog.
- **Recommendation**: Generate a machine-readable catalog from TypeScript schemas.
- **Evidence**: `docs/`, `README.md`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: Custom logger wraps console.log with text output. No structured JSON. No tracing. No correlation IDs.
- **Gap**: No structured logging, no tracing, no correlation IDs.
- **Recommendation**: Migrate to structured JSON logging with correlation IDs.
- **Evidence**: `src/utils/logger.ts`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: Queue construct generates CloudWatch Alarms for DLQ messages. No alerting for plugin operations.
- **Gap**: No alerting for plugin operational failures.
- **Recommendation**: Document recommended alarms for Lift-generated resources.
- **Evidence**: `src/constructs/aws/Queue.ts`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No business outcome metrics. Queue DLQ alarm is operational only.
- **Gap**: No business metrics tracking.
- **Recommendation**: Consider opt-in telemetry for construct usage.
- **Evidence**: `src/constructs/aws/Queue.ts`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: INFO
- **Finding**: The plugin IS IaC (generates CloudFormation via CDK). No deployed infrastructure to govern. Peer review via GitHub PRs. CI validates changes.
- **Gap**: N/A — governance model appropriate for a library.
- **Recommendation**: No action needed.
- **Evidence**: `.github/workflows/ci.yml`, `.github/CONTRIBUTING.md`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: CI runs unit tests, lint, TypeScript checks. Tests validate CloudFormation output. No formal contract testing or breaking change detection for configuration schema.
- **Gap**: No API contract testing. No schema breaking change detection.
- **Recommendation**: Add schema snapshot tests and breaking change detection.
- **Evidence**: `.github/workflows/ci.yml`, `test/unit/queues.test.ts`

#### ENG-Q3: Rollback Capability
- **Severity**: INFO
- **Finding**: npm version pinning allows rollback. GitHub releases provide tagged versions. CloudFormation native rollback for generated stacks.
- **Gap**: N/A — rollback appropriate for library distribution.
- **Recommendation**: Document version rollback procedure.
- **Evidence**: `package.json`, `.github/workflows/release.yml`

#### ENG-Q4: API Test Coverage
- **Severity**: INFO
- **Finding**: 13 test files, 3,115 lines covering all 8 construct types and both providers. Tests validate CloudFormation template structure, configuration validation, CLI commands, and variable resolution.
- **Gap**: No integration tests against real AWS resources.
- **Recommendation**: Consider schema snapshot tests for change detection.
- **Evidence**: `test/unit/` (13 files, 3115 lines)

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
| `src/plugin.ts` | API-Q1, API-Q3, API-Q4, API-Q5, AUTH-Q1, AUTH-Q2, AUTH-Q3, STATE-Q6, HITL-Q1, HITL-Q2, DATA-Q7, ENG-Q1 |
| `src/utils/error.ts` | API-Q3 |
| `src/utils/logger.ts` | OBS-Q1, DATA-Q6 |
| `src/utils/s3-sync.ts` | API-Q4, STATE-Q1, STATE-Q3, STATE-Q5, STATE-Q6, DATA-Q5, DATA-Q6 |
| `src/utils/naming.ts` | — |
| `src/utils/sleep.ts` | — |
| `src/providers/AwsProvider.ts` | AUTH-Q1, AUTH-Q4, AUTH-Q6, AUTH-Q7, DATA-Q2, STATE-Q5 |
| `src/providers/StripeProvider.ts` | AUTH-Q1, AUTH-Q5, AUTH-Q7, DATA-Q1, DATA-Q2 |
| `src/providers/ProviderInterface.ts` | — |
| `src/providers/StaticProviderInterface.ts` | — |
| `src/CloudFormation.ts` | AUTH-Q3 |
| `src/classes/aws.ts` | AUTH-Q6, STATE-Q1, STATE-Q5, STATE-Q6, OBS-Q2 |
| `src/classes/cloudfrontFunctions.ts` | — |
| `src/constructs/ConstructInterface.ts` | API-Q1 |
| `src/constructs/StaticConstructInterface.ts` | API-Q1 |
| `src/constructs/aws/Queue.ts` | API-Q2, API-Q4, AUTH-Q2, AUTH-Q3, DATA-Q1, DATA-Q6, STATE-Q5, STATE-Q6, DISC-Q1, DISC-Q2, OBS-Q2, OBS-Q3 |
| `src/constructs/aws/Storage.ts` | API-Q2, AUTH-Q2, AUTH-Q3, DATA-Q1, DISC-Q2 |
| `src/constructs/aws/Webhook.ts` | API-Q2, AUTH-Q3, DISC-Q2 |
| `src/constructs/aws/DatabaseDynamoDBSingleTable.ts` | AUTH-Q2, AUTH-Q3, DATA-Q1 |
| `src/constructs/aws/ServerSideWebsite.ts` | STATE-Q1 |
| `src/constructs/aws/SinglePageApp.ts` | — |
| `src/constructs/aws/StaticWebsite.ts` | — |
| `src/constructs/aws/Vpc.ts` | — |
| `src/constructs/aws/abstracts/StaticWebsiteAbstract.ts` | STATE-Q1 |
| `src/constructs/aws/queue/sqs.ts` | STATE-Q5 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/ci.yml` | HITL-Q3, ENG-Q1, ENG-Q2 |
| `.github/workflows/release.yml` | DISC-Q1, ENG-Q3, HITL-Q2 |
| `.github/CONTRIBUTING.md` | ENG-Q1 |
| `.github/pull_request_template.md` | ENG-Q1 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `package.json` | DISC-Q1, ENG-Q3 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `jest.config.js` | HITL-Q3 |
| `tsconfig.json` | — |
| `.eslintrc` | — |

### Documentation
| File | Questions Referenced |
|------|---------------------|
| `README.md` | API-Q1, DISC-Q3 |
| `docs/permissions.md` | AUTH-Q2 |
| `docs/` (directory) | DISC-Q3 |

### Test Files
| File | Questions Referenced |
|------|---------------------|
| `test/unit/` (directory, 13 files) | HITL-Q3, ENG-Q2, ENG-Q4 |
| `test/fixtures/` (directory, 14 fixtures) | HITL-Q3 |
