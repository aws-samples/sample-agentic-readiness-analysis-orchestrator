# Agentic Readiness Assessment Report

**Target**: Zappa (.)
**Date**: 2026-04-29
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Service Archetype**: orchestrator (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: python, serverless
**Context**: Python framework for deploying WSGI apps on AWS Lambda.

**Archetype Justification**: Zappa orchestrates 15+ downstream AWS services (Lambda, S3, API Gateway, IAM, ELB, DynamoDB, SNS, CloudFormation, ACM, Cognito, EFS, Route53, STS, CloudWatch, Logs) via boto3 clients initialized in `core.py`. It coordinates multi-service deployment workflows with high fan-out, matching the orchestrator archetype.

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 2 | **RISK-SAFETY**: 9 | **RISK-QUALITY**: 16 | **INFOs**: 12

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days.

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 2 |
| RISK-SAFETY | 9 |
| RISK-QUALITY | 16 |
| INFO | 12 |
| N/A | 0 |
| Not Evaluated (extended) | 4 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 15
**Extended Questions Not Triggered**: 4
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: orchestrator (auto-detected)

---

<!-- SECTION: BLOCKERS -->
## BLOCKERs — Must Resolve Before Agent Deployment

### API-Q1: Documented API Interface

- **Severity**: BLOCKER
- **Finding**: Zappa does not expose a documented REST, GraphQL, or AsyncAPI interface for agent consumption. It is a CLI-driven deployment framework — users interact via `zappa deploy`, `zappa update`, `zappa rollback` etc. (defined in `zappa/cli.py`). The API Gateway and Lambda resources Zappa *creates* are for user applications, not for Zappa itself. The only programmatic interface is the Python `Zappa` class in `core.py` and the `ZappaCLI` class in `cli.py`, which are library/SDK interfaces, not network APIs.
- **Gap**: No network-accessible API (REST, GraphQL, or AsyncAPI) exists for agent integration. Agents would need to either invoke the CLI (brittle, unstructured output) or import and call Python classes directly (tight coupling, no authentication layer).
- **Remediation**:
  - **Immediate**: Define a REST or gRPC API surface that wraps core Zappa operations (deploy, update, rollback, status, tail) with structured JSON request/response. Consider a lightweight FastAPI wrapper around `ZappaCLI` operations.
  - **Target State**: A documented, versioned API that agents can bind to as tool definitions, with OpenAPI spec.
  - **Estimated Effort**: High
  - **Dependencies**: API-Q2 (machine-readable spec), AUTH-Q1 (machine identity auth)
- **Evidence**: `zappa/cli.py` (CLI-only interface), `zappa/core.py` (Python library interface)

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: Zappa handles AWS credentials (access keys, session tokens, IAM role ARNs), S3 bucket contents (deployment packages), and user environment variables that may contain secrets. No data classification tags, field-level encryption, or PII detection mechanisms are implemented. The `load_remote_settings` method in `handler.py` loads arbitrary JSON from S3 into environment variables without classification. The `attach_policy.json` grants `s3:*`, `dynamodb:*`, `sns:*`, `sqs:*`, `kinesis:*`, `logs:*` and `route53:*` with broad resource patterns, but the data behind these resources is not classified.
- **Gap**: No sensitive data classification exists. AWS credentials flow through the system without field-level tagging. Environment variables (which may contain secrets, API keys, database passwords) are loaded and set without classification or access control.
- **Remediation**:
  - **Immediate**: Classify data types handled by Zappa (AWS credentials, user secrets in env vars, deployment artifacts). Tag sensitive fields in configuration schemas.
  - **Target State**: Field-level data classification with controls preventing agent retrieval of classified data without explicit authorization.
  - **Estimated Effort**: Medium
  - **Dependencies**: AUTH-Q2 (scoped permissions)
- **Evidence**: `zappa/handler.py` (lines: `load_remote_settings`, environment variable loading), `zappa/policies/attach_policy.json` (broad resource access), `zappa/cli.py` (`aws_environment_variables`, `environment_variables` handling)

---

<!-- SECTION: RISKS -->
## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The default IAM policy in `zappa/policies/attach_policy.json` uses wildcard actions and resources extensively: `logs:*` on `arn:aws:logs:*:*:*`, `lambda:InvokeFunction` and `lambda:InvokeFunctionUrl` on `*`, `s3:*` on `arn:aws:s3:::*`, `kinesis:*`, `sns:*`, `sqs:*`, `dynamodb:*` on `arn:aws:dynamodb:*:*:*`, `route53:*` on `*`. This grants far broader permissions than necessary for any single deployment operation.
- **Gap**: No scoped, least-privilege IAM policies exist. An agent identity using Zappa's default execution role inherits access to all S3 buckets, all DynamoDB tables, all SNS topics, etc. in the account.
- **Compensating Controls**:
  - Create custom IAM policies per deployment stage with specific resource ARNs instead of wildcards
  - Use the `extra_permissions` and custom `attach_policy` settings in `zappa_settings.json` to override defaults
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Replace wildcard policies with resource-scoped policies. Document a least-privilege policy template for agent use cases.
- **Evidence**: `zappa/policies/attach_policy.json`

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Zappa supports API Gateway authorizers (TOKEN, COGNITO_USER_POOLS, AWS_IAM) via the `authorizer` setting in `zappa_settings.json`, and IAM authorization via `iam_authorization` setting. However, these are coarse-grained — they gate access to the entire API, not to individual actions. The `example/authmodule.py` shows a custom authorizer that calls `policy.allowAllMethods()`, granting blanket access. There is no built-in mechanism to allow read but deny write at the API method level within Zappa's configuration.
- **Gap**: No action-level authorization (ABAC or fine-grained RBAC) exists. An authenticated agent gets the same access to all endpoints — it cannot be restricted to read-only operations at the Zappa framework level.
- **Compensating Controls**:
  - Configure API Gateway resource policies to restrict HTTP methods per API key or IAM principal
  - Implement custom authorizer logic that checks method-level permissions
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add method-level authorization support to the authorizer configuration, allowing per-method allow/deny rules.
- **Evidence**: `zappa/core.py` (`create_authorizer` method), `example/authmodule.py`, `zappa/cli.py` (`iam_authorization`, `authorizer` settings)

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Zappa does not configure CloudTrail, immutable log storage, or audit-specific logging. CloudWatch Logs integration exists (`logs:*` in IAM policy, `fetch_logs` in `core.py`, `cloudwatch_log_level` setting) but these are application logs, not audit logs. There is no log file validation, no S3 object lock for logs, and no tamper-evident log configuration. The logging in `handler.py` and `wsgi.py` uses Apache NCSA Common Log Format via `ApacheNCSAFormatters`, which records request method, path, status code, and timing — but does not record the authenticated principal identity.
- **Gap**: No immutable audit logging. Application logs exist but are not audit-grade — they lack principal attribution, tamper-evidence, and immutability guarantees.
- **Compensating Controls**:
  - Enable AWS CloudTrail for API Gateway and Lambda API calls
  - Configure CloudWatch Logs with retention policies and export to S3 with Object Lock
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add CloudTrail configuration guidance to documentation. Include authenticated principal in access logs.
- **Evidence**: `zappa/policies/attach_policy.json` (`logs:*`), `zappa/wsgi.py` (`common_log`), `zappa/utilities.py` (`ApacheNCSAFormatters`), `zappa/handler.py` (logging setup)

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Zappa provides API key management via `create_api_key`, `remove_api_key`, and `get_api_keys` methods in `core.py`. IAM roles are managed via `create_iam_roles` and `get_credentials_arn`. However, there is no dedicated mechanism to suspend or revoke an individual agent identity without affecting other consumers. API key deletion (`delete_api_key` via `remove_api_key`) is the closest mechanism, but this is an all-or-nothing operation — there are no per-agent API keys managed by Zappa.
- **Gap**: No granular agent identity suspension. Revoking access requires deleting the shared API key or modifying the IAM role, which affects all consumers of that deployment.
- **Compensating Controls**:
  - Create separate API keys per agent identity using API Gateway usage plans
  - Use IAM roles with session policies that can be revoked per agent
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add support for per-agent API key management and usage plans in Zappa settings.
- **Evidence**: `zappa/core.py` (`create_api_key`, `remove_api_key`, `get_api_keys`)

#### STATE-Q1: Compensation and Rollback ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Zappa has a `rollback` command that rolls back Lambda function code to a previous version via `rollback_lambda_function_version` in `core.py`. This works by listing previous versions and updating function code to a specified prior version. However, this only rolls back Lambda code — it does not roll back API Gateway configuration, CloudFormation stacks, IAM roles, scheduled events, or other infrastructure changes made during `deploy` or `update`. There are no saga patterns, compensating transactions, or multi-step rollback mechanisms.
- **Gap**: Rollback is limited to Lambda code only. Multi-step deployment operations (which modify Lambda, API Gateway, CloudFormation, IAM, CloudWatch Events, SNS, DynamoDB, Cognito) cannot be atomically rolled back.
- **Compensating Controls**:
  - Use CloudFormation stack rollback (Zappa uses CF stacks for API Gateway)
  - Maintain deployment state snapshots before operations
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement comprehensive rollback that covers API Gateway, CloudFormation stack, scheduled events, and IAM changes in addition to Lambda code.
- **Evidence**: `zappa/core.py` (`rollback_lambda_function_version`), `zappa/cli.py` (`rollback` command)

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Zappa's logging does not include PII redaction or log scrubbing. The `common_log` function in `wsgi.py` logs full request paths (which may contain PII in query parameters), IP addresses, user agents, and referer headers. The `load_remote_settings` method in `handler.py` logs environment variable keys and values when `LOG_LEVEL` is `DEBUG` (line: `print("Adding {} -> {} to environment".format(key, value))`). There are no log scrubbing middleware, PII masking libraries, or Amazon Macie integration.
- **Gap**: No PII redaction in logs. Sensitive data (query parameters, environment variables containing secrets, IP addresses) flows directly into CloudWatch Logs without masking.
- **Compensating Controls**:
  - Set `LOG_LEVEL` to `INFO` or higher to avoid debug-level secret logging
  - Add CloudWatch Logs subscription filters to detect PII patterns
- **Remediation Timeline**: 30 days
- **Recommendation**: Add log scrubbing middleware to redact PII from request paths and headers. Remove the debug logging of environment variable values in `handler.py`.
- **Evidence**: `zappa/wsgi.py` (`common_log`), `zappa/handler.py` (`load_remote_settings` debug logging), `zappa/utilities.py` (`ApacheNCSAFormatters`)

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Zappa calls 15+ AWS services without circuit breakers, systematic retry patterns, or timeout management. Boto3 default retry is the only resilience mechanism. No Resilience4j, Polly, or equivalent patterns.
- **Gap**: No circuit breakers for downstream AWS service calls. A failing service call cascades without isolation.
- **Compensating Controls**:
  - Rely on boto3 built-in retry behavior
  - Configure botocore retry policies per client
- **Remediation Timeline**: 60 days
- **Recommendation**: Add configurable retry policies and circuit breaker patterns for critical AWS service calls.
- **Evidence**: `zappa/core.py` (`long_config` — timeout only, no circuit breaker)

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No explicit rate limiting configuration. API Gateway default throttling is the only protection. No WAF rules, no application-level rate limiting, no usage plans configured.
- **Gap**: No rate limiting to prevent agent traffic storms.
- **Compensating Controls**:
  - Configure API Gateway usage plans manually
  - Add WAF rate rules
- **Remediation Timeline**: 30 days
- **Recommendation**: Add usage plan and throttling configuration to zappa_settings.json.
- **Evidence**: `zappa/core.py` (`deploy_api_gateway` — no usage plan config)

#### DATA-Q2: Data Residency and Sovereignty ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Zappa deploys to user-specified regions. ACM certificates are hardcoded to `us-east-1`. No data residency documentation or cross-region transfer controls.
- **Gap**: No data residency controls or documentation.
- **Compensating Controls**:
  - Restrict deployments to compliant AWS regions via configuration
  - Document data residency requirements per stage
- **Remediation Timeline**: 30 days
- **Recommendation**: Add data residency documentation and region-restriction configuration.
- **Evidence**: `zappa/core.py` (`ACM_CERTIFICATE_REGION = "us-east-1"`, `AWS_REGIONS`)

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, GraphQL schema, or any machine-readable specification exists in the repository. There are no files matching `openapi.*`, `swagger.*`, `*.graphql`, `*.gql`, or `*.smithy`.
- **Gap**: Agents cannot auto-generate tool definitions from a machine-readable spec. Manual tool authoring would be required.
- **Compensating Controls**:
  - Generate an OpenAPI spec from the CLI argument parser structure
  - Document the Python API surface in a structured format
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create an OpenAPI spec documenting the programmatic interface.
- **Evidence**: Absence of any API spec files in repository.

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Error handling in `handler.py` (`_handle_request_exception`) returns a JSON response with `statusCode: 500` and a `body` containing `message` and optionally `traceback` (when `DEBUG=True`). However, there is no structured error code, no retryable boolean, and no consistent error response format across all event types. CLI errors use Click exceptions which produce human-readable strings.
- **Gap**: No consistent, machine-readable error response format with error codes and retryability indicators.
- **Compensating Controls**:
  - Wrap Zappa operations in a standardized error response envelope
  - Map known error types to structured error codes
- **Remediation Timeline**: 30 days
- **Recommendation**: Define a structured error response schema with error_code, message, and retryable fields.
- **Evidence**: `zappa/handler.py` (`_handle_request_exception`)

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Zappa uses semantic versioning (`__version__ = "0.62.1"` in `zappa/__init__.py`) and maintains a comprehensive `CHANGELOG.md` documenting changes per release. However, there is no API contract versioning (no `/v1/`, `/v2/` patterns for the framework's own interface), no breaking change detection in CI, no consumer-driven contract tests (Pact), and no schema registry. The `zappa_settings.json` schema is implicitly defined by code but not formally versioned or validated.
- **Gap**: No formal schema versioning or breaking change detection. Settings schema changes are not validated against a published contract.
- **Compensating Controls**:
  - Pin Zappa version in agent tool definitions
  - Monitor CHANGELOG.md for breaking changes before updating
- **Remediation Timeline**: 60 days
- **Recommendation**: Add JSON Schema validation for `zappa_settings.json`. Implement breaking change detection in CI.
- **Evidence**: `zappa/__init__.py` (`__version__`), `CHANGELOG.md`, `zappa/cli.py` (`load_settings_file`)

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Zappa supports AWS X-Ray tracing via the `xray_tracing` configuration setting. When enabled, Lambda functions are created with `TracingConfig: {"Mode": "Active"}` (see `core.py`, `create_lambda_function`). The IAM policy includes `xray:PutTraceSegments` and `xray:PutTelemetryRecords`. However, logs are not structured JSON — they use the Apache NCSA Common Log Format (plain text). There is no `correlation_id` or `request_id` field consistently propagated through log entries. No OpenTelemetry SDK is present.
- **Gap**: X-Ray tracing is supported but optional (off by default). Logs are plain text, not structured JSON. No correlation ID propagation.
- **Compensating Controls**:
  - Enable `xray_tracing: true` in zappa_settings.json
  - Use Lambda's built-in request ID from context for correlation
- **Remediation Timeline**: 30 days
- **Recommendation**: Default `xray_tracing` to `true`. Add structured JSON logging with request_id correlation.
- **Evidence**: `zappa/core.py` (`xray_tracing`, `TracingConfig`), `zappa/policies/attach_policy.json` (X-Ray permissions), `zappa/wsgi.py` (`common_log` — plain text format)

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Zappa's `status` command retrieves CloudWatch metrics (Invocations, Errors) via `cloudwatch.get_metric_statistics` in `cli.py`. API Gateway stage configuration supports `cloudwatch_log_level`, `cloudwatch_data_trace`, and `cloudwatch_metrics_enabled` settings. However, no CloudWatch alarms, anomaly detection, PagerDuty/OpsGenie integration, or SLO-based alerting is configured or managed by Zappa.
- **Gap**: Metrics collection exists but no alerting thresholds are configured. Error rate and latency spikes go undetected.
- **Compensating Controls**:
  - Manually create CloudWatch alarms on Lambda error rate and API Gateway latency
  - Use AWS CloudWatch Anomaly Detection on deployed functions
- **Remediation Timeline**: 30 days
- **Recommendation**: Add CloudWatch alarm configuration support to zappa_settings.json (error rate, latency, throttle thresholds).
- **Evidence**: `zappa/cli.py` (`status` method — CloudWatch metrics), `zappa/cli.py` (`cloudwatch_log_level`, `cloudwatch_metrics_enabled`)

#### ENG-Q1: Infrastructure Governance — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Zappa generates CloudFormation templates via Troposphere (`core.py`) for API Gateway routes and deploys them via `update_stack`. IAM roles are created/updated programmatically. However: (1) The IaC is generated at deploy-time, not stored as reviewable files — templates are created, uploaded to S3, applied, then deleted. (2) No PR review requirements exist on infrastructure changes. (3) No drift detection (AWS Config rules) is configured or recommended.
- **Gap**: Infrastructure is code-generated but ephemeral — not stored as reviewable, version-controlled IaC. No peer review on infra changes. No drift detection.
- **Compensating Controls**:
  - Use the `template` command to generate and review CF templates before deployment
  - Store generated templates in version control
- **Remediation Timeline**: 60 days
- **Recommendation**: Persist generated CloudFormation templates to version control. Add drift detection configuration.
- **Evidence**: `zappa/core.py` (`create_stack_template`, `update_stack` — template generation and ephemeral upload), `zappa/cli.py` (`template` command)

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The CI pipeline (`.github/workflows/ci.yml`) runs linting (flake8, black, isort) and pytest across Python 3.9–3.14 with coverage reporting. The CD pipeline (`.github/workflows/cd.yml`) builds and publishes to PyPI. However, there are no API contract tests, no consumer-driven contract testing (Pact), no OpenAPI spec validation, and no breaking change detection in the pipeline.
- **Gap**: CI tests framework functionality but does not validate API contracts or detect breaking changes in the framework's interface.
- **Compensating Controls**:
  - Add snapshot tests for CLI output format
  - Add settings schema validation tests
- **Remediation Timeline**: 60 days
- **Recommendation**: Add contract tests that validate zappa_settings.json schema compatibility across versions.
- **Evidence**: `.github/workflows/ci.yml`, `.github/workflows/cd.yml`, `Makefile` (test targets)

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Zappa provides a `rollback` CLI command and `rollback_lambda_function_version` in `core.py`. This lists Lambda function versions and updates code to a prior version. The rollback is code-only — it does not roll back Lambda configuration, API Gateway, or CloudFormation changes. Docker-based deployments explicitly raise `NotImplementedError` for rollback.
- **Gap**: Rollback is limited to Lambda code. Configuration changes, API Gateway updates, and CloudFormation stack changes are not rolled back.
- **Compensating Controls**:
  - Use CloudFormation stack rollback for API Gateway changes
  - Keep deployment artifacts for manual recovery
- **Remediation Timeline**: 60 days
- **Recommendation**: Extend rollback to cover configuration and API Gateway changes, not just code.
- **Evidence**: `zappa/core.py` (`rollback_lambda_function_version`), `zappa/cli.py` (`rollback`)

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The test suite includes `test_handler.py`, `test_core.py`, `test_placebo.py`, `test_middleware.py`, `test_async.py`, `test_utilities.py`, `test_asgi.py`, and `test_docs.py`. Tests use placebo (AWS API mocking) for AWS service calls. Coverage reporting is configured (`--cov=zappa`). However, there are no dedicated API contract tests, no integration tests against live AWS services, and no tests validating the structured output format of CLI commands.
- **Gap**: Good unit test coverage exists but no API contract tests or integration tests for agent-facing interfaces.
- **Compensating Controls**:
  - Use existing placebo tests as a foundation for contract tests
  - Add output format assertion tests for CLI commands
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add contract tests for CLI output format and settings schema validation.
- **Evidence**: `tests/` directory, `.github/workflows/ci.yml`, `Makefile` (test targets)

#### ENG-Q5: Encryption at Rest — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Zappa supports `aws_kms_key_arn` setting for Lambda function environment variable encryption. The `create_lambda_function` and `update_lambda_configuration` methods pass `KMSKeyArn` to AWS Lambda API. EFS creation in `core.py` sets `Encrypted=True`. However, S3 buckets created by Zappa for deployment packages do not have default encryption configured. There is no KMS key management for S3 objects.
- **Gap**: Lambda env var encryption and EFS encryption are supported. S3 bucket encryption for deployment artifacts is not configured by default.
- **Compensating Controls**:
  - Enable S3 default encryption on the deployment bucket manually
  - Use `aws_kms_key_arn` setting for Lambda encryption
- **Remediation Timeline**: 30 days
- **Recommendation**: Add default S3 bucket encryption (SSE-S3 or SSE-KMS) when creating deployment buckets.
- **Evidence**: `zappa/core.py` (`create_lambda_function` — `KMSKeyArn`, `create_efs` — `Encrypted=True`, `upload_to_s3` — no encryption config), `zappa/cli.py` (`aws_kms_key_arn` setting)

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Zappa supports multiple stages via `zappa_settings.json` (e.g., `dev`, `staging`, `prod`) with stage-specific configuration. The `extends` feature allows stages to inherit from other stages. The `test_settings.json` demonstrates multiple test stages. However, there is no built-in sandbox with production-equivalent data shape, no seed data scripts, and no docker-compose for local testing. Local testing requires a live AWS account.
- **Gap**: Multi-stage deployment supported but no local sandbox or staging environment with synthetic data for safe testing.
- **Compensating Controls**:
  - Use separate AWS accounts for staging
  - Use LocalStack for local AWS service emulation
- **Remediation Timeline**: 60 days
- **Recommendation**: Add LocalStack-based local testing support and document staging environment setup.
- **Evidence**: `example/zappa_settings.json` (multi-stage config), `test_settings.json` (`extends` feature), `zappa/cli.py` (`stage_config`)

---

## INFOs — Architecture and Design Inputs

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Zappa's deployment operations (deploy, update, undeploy) are not idempotent — running `deploy` twice fails with "This application is already deployed." Running `update` is partially idempotent for code updates but not for infrastructure changes. No idempotency keys exist.
- **Implication**: If agents were given write-enabled scope in the future, non-idempotent operations would create data integrity risks on retry.
- **Recommendation**: Add idempotency checks to deployment operations for future write-enabled agent support.
- **Evidence**: `zappa/cli.py` (`deploy` — "already deployed" check, `update`)

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: The Lambda handler returns structured JSON responses for HTTP events (both v1 and v2 formats). The response includes `statusCode`, `headers`, `body`, and `isBase64Encoded` fields. CLI output is human-readable text with Click formatting. The `--json` flag on `status` command provides machine-readable output.
- **Implication**: HTTP responses are well-structured JSON. CLI output requires parsing unless `--json` is used.
- **Recommendation**: Add `--json` output support to all CLI commands for agent consumption.
- **Evidence**: `zappa/handler.py` (JSON response format), `zappa/cli.py` (`status` with `--json`)

### API-Q7: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: Zappa integrates with SNS for async task dispatch (`create_async_sns_topic`), CloudWatch Events for scheduled functions (`schedule_events`), and supports S3, DynamoDB Streams, Kinesis, and SQS as event sources. However, Zappa itself does not emit events for its own state changes (deployment completed, update started, rollback triggered).
- **Implication**: Agents cannot subscribe to deployment lifecycle events. Monitoring requires polling the `status` command.
- **Recommendation**: Add SNS notifications for deployment lifecycle events (deploy start/complete, update, rollback).
- **Evidence**: `zappa/core.py` (`create_async_sns_topic`, `schedule_events`), `zappa/utilities.py` (event source implementations)

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: API Gateway throttling is configurable via stage deployment settings but no rate limit headers (`X-RateLimit-Remaining`, `Retry-After`) are returned in responses. No `aws_api_gateway_usage_plan` is configured by Zappa. Rate limiting depends entirely on API Gateway defaults.
- **Implication**: Agents calling Zappa-deployed APIs cannot self-throttle based on rate limit headers.
- **Recommendation**: Add usage plan and rate limit header support to API Gateway configuration.
- **Evidence**: `zappa/core.py` (`deploy_api_gateway` — no usage plan), `zappa/handler.py` (no rate limit headers in responses)

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Zappa supports Lambda reserved concurrency via `lambda_concurrency` setting (`put_function_concurrency`). No optimistic locking, ETags, or version fields exist for deployment state. CloudFormation stack updates use `StackName` matching but no conditional updates.
- **Implication**: Relevant for future write-enabled scope — concurrent deployment operations could conflict.
- **Recommendation**: Consider adding deployment locking (e.g., DynamoDB-based lock) for concurrent access.
- **Evidence**: `zappa/core.py` (`put_function_concurrency`), `zappa/cli.py` (`lambda_concurrency`)

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits exist. Zappa operations are unbounded — a deployment affects all resources associated with a stage. No `max_records_per_operation` or similar limits exist.
- **Implication**: Relevant for future write-enabled scope — an agent could trigger unlimited deployments.
- **Recommendation**: Add rate limiting on deployment operations per time window.
- **Evidence**: `zappa/cli.py` (no transaction limit configuration)

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No draft or pending state exists. Deployments are committed immediately. The `package` command creates a zip without deploying, which is the closest to a "draft" concept.
- **Implication**: Relevant for future write-enabled scope — agents cannot propose deployments for human review.
- **Recommendation**: Add a `plan` command (similar to Terraform plan) that shows changes without applying them.
- **Evidence**: `zappa/cli.py` (`package` command, `deploy` — immediate execution)

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No approval gates exist. All CLI commands execute immediately. The `undeploy` command has a `--yes` flag to skip confirmation prompts, and `certify` also has confirmation, but these are interactive CLI prompts, not programmatic approval gates.
- **Implication**: Relevant for future write-enabled scope — no human approval step before destructive operations.
- **Recommendation**: Add approval workflow support for destructive operations (undeploy, rollback).
- **Evidence**: `zappa/cli.py` (`undeploy` — confirmation prompt, `certify` — confirmation prompt)

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Field names in `zappa_settings.json` are human-readable and semantically clear: `app_function`, `s3_bucket`, `aws_region`, `memory_size`, `timeout_seconds`, `vpc_config`, `environment_variables`, `binary_support`, `xray_tracing`. No legacy abbreviations or codes requiring a data dictionary.
- **Implication**: Settings are self-documenting, reducing the need for a data dictionary for agent tool definitions.
- **Recommendation**: No action needed — maintain current naming conventions.
- **Evidence**: `example/zappa_settings.json`, `test_settings.json`, `zappa/cli.py` (setting names)

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No data catalog or metadata layer exists. Documentation is in `README.md`, `docs/` directory (domain/SSL guides), and `CHANGELOG.md`. No AWS Glue Data Catalog, Collibra, Alation, or DataHub integration.
- **Implication**: Agent tool builders must read documentation manually to understand Zappa's data model.
- **Recommendation**: Consider adding a JSON Schema for zappa_settings.json as a lightweight metadata layer.
- **Evidence**: `README.md`, `docs/` directory, `CHANGELOG.md`

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: The `status` command retrieves Lambda invocation count and error rate from CloudWatch (`get_metric_statistics`). No custom business metrics are published. No `cloudwatch.put_metric_data` calls exist for deployment success rate, deployment duration, or other framework-level KPIs.
- **Implication**: No framework-level metrics for agent interaction quality monitoring.
- **Recommendation**: Add custom CloudWatch metrics for deployment operations (success/failure rate, duration).
- **Evidence**: `zappa/cli.py` (`status` — `get_metric_statistics`)

---

<!-- SECTION: DETAILED FINDINGS -->
## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: BLOCKER
- **Finding**: Zappa does not expose a network-accessible API. It is a CLI/library tool. Users interact via `zappa deploy`, `zappa update`, etc. The `Zappa` class in `core.py` is a Python SDK, not a REST API.
- **Gap**: No REST, GraphQL, or AsyncAPI interface exists for agent integration.
- **Recommendation**: Create a REST API wrapper around core Zappa operations with OpenAPI spec.
- **Evidence**: `zappa/cli.py`, `zappa/core.py`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, GraphQL schema, or machine-readable specification exists.
- **Gap**: No machine-readable spec for agent tool generation.
- **Recommendation**: Create an OpenAPI spec for the programmatic interface.
- **Evidence**: Absence of spec files in repository.

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: Error responses in `handler.py` return JSON with `statusCode` and `body` but lack structured error codes and retryable indicators.
- **Gap**: No consistent, machine-readable error format with error codes.
- **Recommendation**: Define structured error response schema.
- **Evidence**: `zappa/handler.py` (`_handle_request_exception`)

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Deployment operations are not idempotent. `deploy` fails if already deployed. `update` is partially idempotent for code.
- **Gap**: No idempotency keys or mechanisms.
- **Recommendation**: Add idempotency for future write-enabled scenarios.
- **Evidence**: `zappa/cli.py` (`deploy`, `update`)

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: HTTP responses are JSON. CLI output is human-readable text with optional `--json` on `status`.
- **Gap**: Most CLI commands lack machine-readable output.
- **Recommendation**: Add `--json` to all CLI commands.
- **Evidence**: `zappa/handler.py`, `zappa/cli.py` (`status --json`)

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `orchestrator`, agent_scope: `read-only`.
- **Trigger**: Service has operations >30s OR long-running workflows
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: Zappa integrates SNS, CloudWatch Events, S3, DynamoDB Streams, Kinesis, and SQS as event sources but does not emit events for its own lifecycle changes.
- **Gap**: No deployment lifecycle events for agent subscription.
- **Recommendation**: Add SNS notifications for deployment events.
- **Evidence**: `zappa/core.py` (`create_async_sns_topic`, `schedule_events`)

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit headers returned. No usage plans configured. Rate limiting depends on API Gateway defaults.
- **Gap**: No rate limit visibility for agents.
- **Recommendation**: Add usage plan and rate limit header support.
- **Evidence**: `zappa/core.py` (`deploy_api_gateway`)

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: RISK-QUALITY
- **Finding**: Zappa supports machine identity authentication via API Gateway API keys (`api_key_required`, `create_api_key`), IAM authorization (`iam_authorization`), TOKEN authorizers, and Cognito User Pool authorizers. These can authenticate machine/agent identities. However, the authenticated principal is not attributed in access logs — `common_log` records IP, method, path, status, and timing but not the identity of the caller.
- **Gap**: Authentication mechanisms exist but audit log attribution of authenticated principal is missing.
- **Recommendation**: Include the authenticated principal (from `REMOTE_USER`, `API_GATEWAY_AUTHORIZER`) in the Common Log Format output.
- **Evidence**: `zappa/core.py` (`create_api_key`, `create_authorizer`), `zappa/cli.py` (`api_key_required`, `iam_authorization`), `zappa/wsgi.py` (`common_log`)

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: Default IAM policy uses `*` wildcards extensively: `s3:*`, `dynamodb:*`, `sns:*`, `sqs:*`, `kinesis:*`, `logs:*`, `route53:*`.
- **Gap**: No least-privilege enforcement. Agent identity inherits all permissions.
- **Recommendation**: Replace wildcards with resource-scoped policies.
- **Evidence**: `zappa/policies/attach_policy.json`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: Coarse-grained authorization via API Gateway authorizers. No method-level allow/deny within Zappa configuration.
- **Gap**: Cannot restrict agent to read vs write at API method level.
- **Recommendation**: Add method-level authorization support.
- **Evidence**: `zappa/core.py` (`create_authorizer`), `example/authmodule.py`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: RISK-QUALITY
- **Finding**: Zappa passes `REMOTE_USER` from API Gateway authorizer context through to the WSGI environ (`wsgi.py`, `process_lambda_payload_v1/v2`). JWT token headers and `Authorization` headers are forwarded through the WSGI environ as `HTTP_AUTHORIZATION`. However, there is no explicit on-behalf-of flow, no token exchange pattern, and no distinction between agent-as-self vs agent-on-behalf-of-user.
- **Gap**: Identity propagation is basic (header passthrough). No explicit delegation or on-behalf-of flows.
- **Recommendation**: Document identity propagation patterns for agent use cases.
- **Evidence**: `zappa/wsgi.py` (`process_lambda_payload_v1` — `REMOTE_USER`, authorizer passthrough)

#### AUTH-Q5: Credential Management
- **Severity**: RISK-QUALITY
- **Finding**: Zappa loads AWS credentials from environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`), AWS profiles (`~/.aws/credentials`), or IAM roles. The `remote_env` feature loads secrets from S3. No Secrets Manager or Vault integration exists. No hardcoded credentials were found in the codebase. The `load_remote_settings` method in `handler.py` loads JSON from S3 into environment variables — this is a credentials-from-S3 pattern, not a secrets manager.
- **Gap**: No integration with AWS Secrets Manager or HashiCorp Vault. Credentials loaded from S3 JSON files without rotation support.
- **Recommendation**: Add AWS Secrets Manager integration for runtime secret loading. Document credential rotation patterns.
- **Evidence**: `zappa/core.py` (`load_credentials`), `zappa/handler.py` (`load_remote_settings`), `zappa/cli.py` (`remote_env`)

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No CloudTrail, immutable log storage, or audit-specific logging. Logs are plain text without principal attribution.
- **Gap**: No immutable audit logging with principal attribution.
- **Recommendation**: Add CloudTrail guidance. Include principal in access logs.
- **Evidence**: `zappa/wsgi.py` (`common_log`), `zappa/policies/attach_policy.json`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: API key deletion possible but no granular per-agent suspension.
- **Gap**: No per-agent identity suspension without affecting others.
- **Recommendation**: Add per-agent API key management.
- **Evidence**: `zappa/core.py` (`create_api_key`, `remove_api_key`)

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Lambda code rollback exists. No multi-step deployment rollback.
- **Gap**: Rollback limited to Lambda code only.
- **Recommendation**: Implement comprehensive rollback.
- **Evidence**: `zappa/core.py` (`rollback_lambda_function_version`)

#### STATE-Q2: Queryable Current State
- **Severity**: RISK-QUALITY
- **Finding**: The `status` command queries Lambda function state, API Gateway URL, scheduled events, error rates, and invocation counts. This provides queryable state for the deployment. However, it requires CLI invocation or Lambda API call — there is no dedicated status API endpoint.
- **Gap**: State is queryable via CLI/SDK but not via a dedicated API endpoint.
- **Recommendation**: Expose status information via a REST endpoint.
- **Evidence**: `zappa/cli.py` (`status`), `zappa/core.py` (`get_lambda_function`, `get_api_url`)

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Lambda concurrency limits supported. No deployment-level locking.
- **Gap**: No concurrent deployment protection.
- **Recommendation**: Add deployment locking for write scenarios.
- **Evidence**: `zappa/core.py` (`put_function_concurrency`)

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: Zappa makes extensive calls to 15+ AWS services but implements no circuit breaker, retry-with-backoff, or timeout patterns for its own service calls. Boto3 has default retry behavior, but Zappa does not configure custom retry policies, circuit breakers, or fallback mechanisms. The `long_config` in `core.py` sets `connect_timeout=5` and `read_timeout=900` for Lambda invocations but no circuit breaker wraps these calls. The `S3EventSource.add` method has a retry loop (4 attempts with backoff) for notification validation, but this is an isolated case.
- **Gap**: No circuit breakers, systematic retry logic, or timeout management for the 15+ downstream AWS service calls.
- **Compensating Controls**:
  - Rely on boto3 built-in retry behavior
  - Set appropriate timeout values in botocore config
- **Remediation Timeline**: 60 days
- **Recommendation**: Add configurable retry policies and circuit breaker patterns for critical AWS service calls.
- **Evidence**: `zappa/core.py` (`long_config` — timeout only), `zappa/utilities.py` (`S3EventSource.add` — isolated retry)

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: API Gateway has default throttling but Zappa does not configure custom throttling, usage plans, or rate limits. No application-level rate limiting middleware exists. No WAF rules are configured. The `cache_cluster_enabled`, `cache_cluster_size`, and `cache_cluster_ttl` settings exist for API Gateway caching but not for rate limiting.
- **Gap**: No explicit rate limiting configuration. Relies entirely on API Gateway defaults.
- **Compensating Controls**:
  - Configure API Gateway usage plans manually
  - Add WAF rate rules to the API Gateway
- **Remediation Timeline**: 30 days
- **Recommendation**: Add usage plan and throttling configuration to zappa_settings.json.
- **Evidence**: `zappa/core.py` (`deploy_api_gateway` — no usage plan), `zappa/cli.py` (no rate limit settings)

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits.
- **Gap**: No blast radius controls.
- **Recommendation**: Add deployment rate limits.
- **Evidence**: `zappa/cli.py`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `orchestrator`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No draft state. The `package` command is the closest concept.
- **Gap**: No draft/pending deployment state.
- **Recommendation**: Add `plan` command.
- **Evidence**: `zappa/cli.py` (`package`)

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Interactive confirmation prompts only (`--yes` flag). No programmatic approval gates.
- **Gap**: No configurable approval workflows.
- **Recommendation**: Add approval workflow support.
- **Evidence**: `zappa/cli.py` (`undeploy` confirmation)

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: Multi-stage deployment with `extends` but no local sandbox.
- **Gap**: No local testing environment with production-equivalent data.
- **Recommendation**: Add LocalStack support.
- **Evidence**: `example/zappa_settings.json`, `test_settings.json`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: No data classification for AWS credentials, secrets in environment variables, or deployment artifacts.
- **Gap**: No field-level data classification.
- **Recommendation**: Classify data types and tag sensitive fields.
- **Evidence**: `zappa/handler.py`, `zappa/policies/attach_policy.json`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Zappa deploys to user-specified AWS regions (`aws_region` setting). The ACM certificate region is hardcoded to `us-east-1`. No data residency documentation, GDPR compliance references, or cross-region data transfer controls exist.
- **Gap**: No data residency documentation or controls. Deployment artifacts may be stored in regions subject to different sovereignty requirements.
- **Recommendation**: Add data residency documentation and region-restriction configuration.
- **Evidence**: `zappa/core.py` (`AWS_REGIONS`, `ACM_CERTIFICATE_REGION = "us-east-1"`)

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
- **Severity**: RISK-QUALITY
- **Finding**: Lambda function metadata includes `LastModified` timestamp. CloudFormation stacks have timestamps. The `status` command reports the Lambda function's last modified time. However, there is no `created_at`, `updated_at`, or `event_time` standardization. No `Cache-Control` or data freshness headers are returned. No timezone normalization documentation.
- **Gap**: Basic timestamps exist in AWS metadata but no standardized temporal data in Zappa's own interfaces.
- **Recommendation**: Include deployment timestamps in status output with UTC normalization.
- **Evidence**: `zappa/cli.py` (`status` — `LastModified`)

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: No PII redaction. Full request paths, IP addresses, and debug-level secret logging.
- **Gap**: No log scrubbing.
- **Recommendation**: Add PII redaction middleware.
- **Evidence**: `zappa/wsgi.py`, `zappa/handler.py`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality scores, completeness metrics, or data profiling. Zappa operates on deployment artifacts and AWS service state, not business data.
- **Implication**: Not directly applicable to a deployment framework, but data quality awareness for deployment state (package integrity, configuration completeness) would be valuable.
- **Recommendation**: Add configuration validation with completeness checks.
- **Evidence**: No data quality mechanisms found.

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: Semantic versioning and CHANGELOG maintained. No formal schema versioning or breaking change detection.
- **Gap**: No schema versioning or breaking change detection in CI.
- **Recommendation**: Add JSON Schema for zappa_settings.json.
- **Evidence**: `zappa/__init__.py`, `CHANGELOG.md`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: All field names are human-readable: `app_function`, `s3_bucket`, `memory_size`, etc.
- **Implication**: Self-documenting settings reduce agent tool authoring effort.
- **Recommendation**: Maintain current conventions.
- **Evidence**: `example/zappa_settings.json`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No data catalog. Documentation in README.md and docs/.
- **Implication**: Manual documentation review needed for tool definition.
- **Recommendation**: Add JSON Schema as lightweight metadata.
- **Evidence**: `README.md`, `docs/`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: X-Ray supported but off by default. Logs are plain text, not structured JSON.
- **Gap**: No structured JSON logging. No correlation ID propagation.
- **Recommendation**: Default X-Ray on. Add structured logging.
- **Evidence**: `zappa/core.py` (`xray_tracing`), `zappa/wsgi.py` (`common_log`)

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: CloudWatch metrics queried but no alerting configured.
- **Gap**: No alerting thresholds.
- **Recommendation**: Add CloudWatch alarm configuration.
- **Evidence**: `zappa/cli.py` (`status`)

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: Basic Lambda metrics retrieved. No custom business metrics published.
- **Implication**: No visibility into framework-level KPIs.
- **Recommendation**: Add custom deployment metrics.
- **Evidence**: `zappa/cli.py` (`status`)

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance
- **Severity**: RISK-QUALITY
- **Finding**: CloudFormation generated but ephemeral. No PR review on infra changes. No drift detection.
- **Gap**: IaC is ephemeral, not version-controlled.
- **Recommendation**: Persist CF templates. Add drift detection.
- **Evidence**: `zappa/core.py` (`create_stack_template`, `update_stack`)

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: CI runs tests and linting. No API contract tests or breaking change detection.
- **Gap**: No contract tests in CI.
- **Recommendation**: Add contract tests.
- **Evidence**: `.github/workflows/ci.yml`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: Lambda code rollback only. No config or API Gateway rollback.
- **Gap**: Partial rollback capability.
- **Recommendation**: Extend rollback scope.
- **Evidence**: `zappa/core.py` (`rollback_lambda_function_version`)

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive unit tests with placebo mocking. No API contract tests.
- **Gap**: No contract tests for agent-facing interfaces.
- **Recommendation**: Add contract tests.
- **Evidence**: `tests/` directory, `Makefile`

#### ENG-Q5: Encryption at Rest
- **Severity**: RISK-QUALITY
- **Finding**: KMS support for Lambda env vars and EFS encryption. S3 bucket encryption not configured.
- **Gap**: S3 deployment artifacts unencrypted by default.
- **Recommendation**: Add S3 default encryption.
- **Evidence**: `zappa/core.py` (`KMSKeyArn`, `Encrypted=True` for EFS)

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| zappa/core.py | API-Q1, API-Q4, API-Q7, API-Q8, AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q2, STATE-Q4, STATE-Q5, OBS-Q1, ENG-Q1, ENG-Q3, ENG-Q5 |
| zappa/cli.py | API-Q1, API-Q4, API-Q5, AUTH-Q1, AUTH-Q3, AUTH-Q5, STATE-Q1, STATE-Q2, STATE-Q3, STATE-Q6, HITL-Q1, HITL-Q2, HITL-Q3, DATA-Q1, DATA-Q5, OBS-Q2, OBS-Q3, ENG-Q4 |
| zappa/handler.py | API-Q3, API-Q5, AUTH-Q5, DATA-Q1, DATA-Q6 |
| zappa/wsgi.py | AUTH-Q1, AUTH-Q4, AUTH-Q6, DATA-Q6, OBS-Q1 |
| zappa/utilities.py | DATA-Q6, STATE-Q4, OBS-Q1 |
| zappa/middleware.py | API-Q3 |
| zappa/asynchronous.py | API-Q7 |
| zappa/__init__.py | DISC-Q1 |

### IAM Policies
| File | Questions Referenced |
|------|---------------------|
| zappa/policies/attach_policy.json | AUTH-Q2, AUTH-Q6, DATA-Q1, OBS-Q1 |
| zappa/policies/assume_policy.json | AUTH-Q2 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| .github/workflows/ci.yml | ENG-Q2, ENG-Q4, HITL-Q3 |
| .github/workflows/cd.yml | ENG-Q2 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| example/zappa_settings.json | AUTH-Q3, HITL-Q3, DISC-Q2 |
| test_settings.json | HITL-Q3, ENG-Q4 |
| example/authmodule.py | AUTH-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| setup.py | DISC-Q1 |
| Pipfile | ENG-Q4 |
| Makefile | ENG-Q4 |

### Documentation
| File | Questions Referenced |
|------|---------------------|
| CHANGELOG.md | DISC-Q1 |
| README.md | DISC-Q3 |
