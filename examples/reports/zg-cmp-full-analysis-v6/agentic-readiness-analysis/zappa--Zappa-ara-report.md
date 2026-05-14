# Agentic Readiness Analysis Report

**Target**: /Users/lucasdu/Documents/AWS-MAC/2026-projects/sample-agentic-readiness-analysis/services/zappa--Zappa
**Date**: 2025-05-08
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**TD Version**: agentic-readiness-analysis
**Repository Type**: application
**Service Archetype**: stateless-utility (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: python, serverless
**Context**: Python framework for deploying WSGI apps on AWS Lambda.

**Archetype Justification**: Zappa is a CLI tool and Lambda runtime library with no persistent data store, no HTTP API surface of its own, no authentication enforcement surface, and no write operations — it deploys user applications to AWS but does not itself serve requests, manage state, or process user data.

**Surface flags**:
  - has_persistent_data_store: false
  - has_http_rpc_surface: false
  - has_auth_surface: false
  - has_write_operations: false
  - has_logging_of_user_data: false

**INFO Note — Dev-Library-Application Override**: This repository classifies as `application` (has source code and a console-script entry point) but functions as a CLI tool/library. The `stateless-utility` archetype is detected AND all five surface flags are `false`. Per Step 1.5, the `library` N/A mapping is applied for scoring (ENG-Q1 through ENG-Q5 are N/A). The original `repo_type` value `application` is preserved. Surface-flag downgrades apply to remaining questions.

---

## Readiness Profile: Agent-Ready

**BLOCKERs**: 0 | **RISK-SAFETY**: 0 | **RISK-QUALITY**: 0 | **INFOs**: 38

Cleared for autonomous operation. Instrument observability. Define scope explicitly. Run controlled pilot first.

### V6 Classification Rationale

This repo has 0 High findings, 0 Medium findings, and 0 safety-impact Medium findings. Rule matched: "0 High, ≤1 Medium → Agent-Ready." The V6 classification aligns with the V5 Readiness Profile: 0 BLOCKERs and 0 RISK-SAFETY findings yields Agent-Ready under both frameworks. All 38 evaluated questions resolve to INFO due to the dev-library-application override and surface-flag downgrades — Zappa is a deployment tool with no agent-callable runtime surface.

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

**Core Questions Evaluated**: 19 (24 minus 5 N/A from library mapping)
**Extended Questions Triggered**: 19 (all triggered as INFO per dev-library-application override)
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

All 38 evaluated questions resolve to INFO due to the dev-library-application classification. Zappa is a CLI tool and runtime library — it has no agent-callable API surface, no persistent data store, no authentication surface, and no write operations of its own. The system that agents would interact with is not Zappa itself, but the user applications that Zappa deploys.

Key architectural observations for agent integration planning:

- **API Surface**: Zappa exposes no HTTP/RPC surface — it is invoked via CLI (`zappa deploy`, `zappa update`). API Gateway resources are created for user applications, not for Zappa itself.
- **Authentication**: Zappa relies on AWS IAM credentials (boto3 session) for its operations. It does not implement or enforce authentication/authorization — it delegates entirely to AWS IAM.
- **State Management**: Zappa is stateless. It reads `zappa_settings.json` and interacts with AWS APIs. No persistent state is owned by the tool.
- **Data**: No user data is stored, processed, or logged by Zappa. The Lambda handler routes requests to user applications which own their data.
- **Observability**: Zappa supports X-Ray tracing as a pass-through for deployed applications but has no observability infrastructure of its own.
- **Engineering Maturity**: Strong CI/CD with GitHub Actions (multi-version Python testing, automated PyPI publishing), comprehensive test suite (8,400+ lines), and pre-commit linting.

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: Zappa exposes no HTTP/RPC surface of its own. It is a CLI tool (`zappa deploy`, `zappa update`, `zappa tail`) that creates API Gateway resources for user applications. The tool itself has no API that an agent would call directly.
- **Gap**: No API surface exists to document — this is expected for a CLI/library tool.
- **Recommendation**: If agent integration is desired, consider wrapping Zappa CLI commands in a task-based API or using AWS SDK calls directly. The deployed user applications (not Zappa) are the agent-callable surfaces.
- **Evidence**: `setup.py` (console_scripts entry point), `zappa/cli.py` (CLI class)

#### API-Q2: Machine-Readable API Specification
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — machine-readable spec is not applicable. Zappa is a CLI tool; its interface is command-line arguments, not an API spec.
- **Gap**: N/A — no API surface to specify.
- **Recommendation**: The `zappa template` command outputs CloudFormation JSON for deployed API Gateway resources — this is the closest to a machine-readable API description, but it describes the user's application, not Zappa itself.
- **Evidence**: No openapi.yaml, swagger.json, or equivalent found in repository.

#### API-Q3: Structured Error Responses
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — structured error responses are not applicable. The Lambda handler (`zappa/handler.py`) does return structured JSON error responses (status code 500 with message body) for user applications, but this is pass-through behavior, not Zappa's own API.
- **Gap**: N/A — no API surface.
- **Recommendation**: None needed for Zappa itself. User applications should implement structured errors.
- **Evidence**: `zappa/handler.py` (lines 326-347: `_handle_request_exception` returns `{"statusCode": 500, "body": ...}`)

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Agent scope is read-only. Additionally, Zappa has no write API endpoints — it is a CLI tool. Write operations (deploy, update, undeploy) are user-initiated CLI commands, not agent-callable endpoints.
- **Gap**: No write API endpoints exist.
- **Recommendation**: None needed.
- **Evidence**: `zappa/cli.py` (CLI commands are user-invoked, not API-exposed)

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: Zappa's Lambda handler returns JSON responses to API Gateway for user applications. The CLI itself outputs text to stdout. No agent-consumable API responses exist from Zappa itself.
- **Gap**: N/A — CLI tool output.
- **Recommendation**: None needed.
- **Evidence**: `zappa/handler.py` (JSON response construction), `zappa/cli.py` (print-based output)

#### API-Q6: Asynchronous Operation Support
- **Severity**: INFO
- **Finding**: Zappa supports async task execution via Lambda/SNS (`@task` decorator in `zappa/asynchronous.py`) for user applications. As a CLI tool, Zappa's own operations (deploy, update) are synchronous CLI processes. No agent-callable async patterns exist.
- **Gap**: N/A — no agent-callable surface.
- **Recommendation**: None needed for Zappa itself.
- **Evidence**: `zappa/asynchronous.py` (async task framework for user apps)

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: Zappa supports SNS, SQS, DynamoDB Streams, Kinesis, and EventBridge as event sources for user applications. Zappa itself does not emit events for its own state changes (deployments, updates).
- **Gap**: N/A — CLI tool state changes are not event-emitting.
- **Recommendation**: None needed.
- **Evidence**: `zappa/core.py` (event source configuration), `zappa/utilities.py` (`add_event_source`, `remove_event_source`)

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: Zappa creates API Gateway usage plans and throttling for user applications. It has no API surface of its own that would require rate limit headers. The `aws_api_gateway_usage_plan` equivalent is created programmatically via troposphere/CloudFormation.
- **Gap**: N/A — no API surface.
- **Recommendation**: None needed.
- **Evidence**: `zappa/core.py` (API Gateway resource creation)

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: Zappa delegates all authentication to AWS IAM via boto3 sessions. It does not implement or enforce machine identity authentication itself — it consumes AWS credentials from the environment (AWS CLI profile, environment variables, or instance metadata). The deployed Lambda functions assume IAM roles defined by `assume_policy.json`.
- **Gap**: System does not issue or enforce agent identities — authentication is a consumer/platform responsibility. Zappa is a deployment tool that uses the caller's AWS credentials.
- **Recommendation**: Agent identity for Zappa-deployed applications should be configured at the API Gateway / Lambda level (IAM authorizers, Cognito, custom authorizers), not within Zappa itself.
- **Evidence**: `zappa/policies/assume_policy.json`, `zappa/core.py` (boto3 session usage)

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: INFO
- **Finding**: Zappa provides IAM policy templates (`attach_policy.json`, `deploy.json`) that use broad wildcards (`"Action": ["logs:*"]`, `"Action": ["s3:*"]`, `"Resource": "*"`). However, these are *default* policies for user convenience — users can (and should) override them with scoped custom policies via `attach_policy` and `extra_permissions` settings. Zappa does not enforce permissions itself.
- **Gap**: Default policies are overly broad, but this is documented and overridable. Zappa is a tool, not a target system.
- **Recommendation**: Document best practices for least-privilege policies when deploying agent-facing applications via Zappa. The `example/policy/deploy.json` shows more scoped permissions as a reference.
- **Evidence**: `zappa/policies/attach_policy.json` (broad wildcards), `example/policy/deploy.json` (scoped example)

#### AUTH-Q3: Action-Level Authorization
- **Severity**: INFO
- **Finding**: Zappa does not implement action-level authorization. It delegates to AWS IAM which natively supports action-level controls (specific Lambda actions, API Gateway method-level auth). The CLI itself does not check permissions — AWS API calls either succeed or fail based on IAM policies.
- **Gap**: System does not enforce action-level auth — it's a consumer/platform responsibility.
- **Recommendation**: None needed for Zappa itself. User applications should configure API Gateway method-level authorization.
- **Evidence**: `zappa/core.py` (AWS API calls without internal auth checks)

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: Zappa's Lambda handler passes through `requestContext` (which includes authorizer context, Cognito identity, and IAM caller identity) to the user's WSGI/ASGI application via the `environ` or `scope` dictionaries. Identity propagation is handled by API Gateway and Lambda, not by Zappa code. Downgraded to INFO for `stateless-utility` archetype.
- **Gap**: N/A — pass-through behavior.
- **Recommendation**: None needed.
- **Evidence**: `zappa/handler.py` (context passed via `environ["lambda.context"]` and `environ["lambda.event"]`)

#### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: Zappa supports loading secrets from S3 via `REMOTE_ENV` setting (a JSON file in S3 loaded at Lambda cold start). No hardcoded credentials found in source code. AWS credentials are consumed from the standard boto3 credential chain (environment variables, AWS profiles, instance metadata). No Secrets Manager or Vault integration for runtime secrets, but S3-based remote env is a reasonable alternative for Lambda.
- **Gap**: No formal secrets rotation mechanism — S3-based secrets require manual rotation.
- **Recommendation**: For agent-deployed applications, consider recommending AWS Secrets Manager integration over S3-based REMOTE_ENV for automatic rotation.
- **Evidence**: `zappa/handler.py` (`load_remote_settings` method), no hardcoded credentials in source

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY normally, but downgraded to INFO because `has_auth_surface` is false AND `has_write_operations` is false. System does not execute agent-invoked write operations — audit logging is a consumer responsibility. The library/utility is called by applications that own the audit context.
- **Finding**: Zappa does not implement audit logging. It relies on AWS CloudTrail (for API calls made by the deployed Lambda) and CloudWatch Logs (for application logging). No CloudTrail configuration is managed by Zappa itself.
- **Gap**: N/A — audit logging is a platform/consumer concern for this tool.
- **Recommendation**: User applications deployed via Zappa should configure CloudTrail and structured logging independently.
- **Evidence**: No CloudTrail or audit logging configuration in repository.

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: INFO
- **Finding**: System does not issue or enforce agent identities — suspension is a consumer responsibility. Libraries and utilities are invoked by applications that own identity lifecycle. Agent identity suspension for Zappa-deployed apps would be handled via IAM role deactivation or API Gateway API key deletion at the AWS platform level.
- **Gap**: N/A — Zappa does not manage agent identities.
- **Recommendation**: None needed.
- **Evidence**: No identity management code in repository.

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY normally, but downgraded to INFO because system exposes no write operations and is a `stateless-utility`. Stateless utilities have no multi-step write sequences.
- **Finding**: Zappa's CLI supports `zappa rollback <n>` to revert to previous Lambda versions. However, this is a user-initiated CLI operation, not an agent-callable API. The tool itself has no multi-step write workflows that require compensation.
- **Gap**: N/A — no agent-callable write operations.
- **Recommendation**: None needed.
- **Evidence**: `zappa/cli.py` (rollback command), `zappa/core.py` (Lambda version management)

#### STATE-Q2: Queryable Current State
- **Severity**: INFO
- **Finding**: Zappa's CLI provides `zappa status` to query the current state of a deployment (Lambda function config, API Gateway endpoint, last update time). This is a CLI command, not a queryable API. The Lambda handler itself is stateless.
- **Gap**: N/A — CLI tool with no agent-queryable state surface.
- **Recommendation**: None needed.
- **Evidence**: `zappa/cli.py` (status command)

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Zappa is stateless. No concurrent write operations exist. Lambda concurrency is managed at the AWS platform level (reserved concurrency, provisioned concurrency), configurable via `zappa_settings.json`.
- **Gap**: N/A — no concurrent write operations.
- **Recommendation**: None needed.
- **Evidence**: `zappa/core.py` (concurrency configuration pass-through to Lambda)

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: INFO
- **Finding**: Zappa does not implement circuit breakers, retry logic, or timeout configurations for external dependencies. Its Lambda handler directly invokes the user's WSGI/ASGI application. The CLI uses boto3's built-in retry logic for AWS API calls. No resilience patterns (Resilience4j, Polly equivalent) are present — which is expected for a CLI tool.
- **Gap**: N/A — CLI tool without runtime resilience requirements.
- **Recommendation**: User applications should implement their own resilience patterns. Zappa inherits boto3's built-in exponential backoff for AWS calls.
- **Evidence**: `zappa/core.py` (boto3 client calls without explicit retry configuration)

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: INFO
- **Finding**: System exposes no HTTP/RPC surface — API-layer rate limiting is not applicable. Zappa creates API Gateway throttling for user applications but has no API surface of its own. Libraries invoked by consuming applications inherit the consumer's rate limiting, not their own.
- **Gap**: N/A — no API surface.
- **Recommendation**: None needed.
- **Evidence**: No rate limiting middleware in source code.

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Read-only agents cannot modify records, trigger spend, or delete data. Zappa has no transaction limit mechanism because it has no agent-callable write operations.
- **Gap**: N/A — no write operations.
- **Recommendation**: None needed.
- **Evidence**: No transaction limit configuration in repository.

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: INFO
- **Finding**: Zappa-deployed Lambda functions auto-scale via AWS Lambda's concurrency model. Zappa does not own or manage infrastructure capacity — it delegates to AWS Lambda and API Gateway scaling. No load tests exist for Zappa itself because it is a CLI tool, not a service.
- **Gap**: N/A — CLI tool with no runtime capacity concerns.
- **Recommendation**: None needed for Zappa itself. User applications should configure Lambda reserved/provisioned concurrency appropriately.
- **Evidence**: `zappa/core.py` (Lambda concurrency configuration)

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Zappa has no draft/pending state mechanism. It is a CLI tool — commands either execute immediately (deploy, update) or are dry-run capable via the CD workflow's `dry-run` input. No agent-callable approval workflow exists.
- **Gap**: N/A — CLI tool with no agent-callable state changes.
- **Recommendation**: None needed.
- **Evidence**: `.github/workflows/cd.yml` (dry-run parameter for releases)

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable approval gates exist within Zappa. The CD workflow uses GitHub's `environment` protection rules (`protected` and `publish` environments) for release approvals, but this is for Zappa's own release process, not for user applications.
- **Gap**: N/A — CLI tool.
- **Recommendation**: None needed.
- **Evidence**: `.github/workflows/cd.yml` (environment: protected, environment: publish)

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: INFO
- **Finding**: Library/utility — staging environments are consumer concerns. Zappa supports multi-stage deployments (dev, staging, production) via `zappa_settings.json` stage definitions, enabling user applications to have separate environments. Zappa itself has no staging environment because it is a library/CLI tool — its test suite uses mocked AWS calls (placebo).
- **Gap**: N/A — library/CLI tool.
- **Recommendation**: None needed.
- **Evidence**: `example/zappa_settings.json` (stage definitions), `tests/placebo/` (mocked AWS responses)

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification ⚡
- **Severity**: INFO
- **Conditional**: Stage A = No. Not a data-handling target — no PII/PHI/financial/credential data is stored, processed, or logged by Zappa. Zappa is a deployment tool that creates AWS resources for user applications. It does not store user data itself.
- **Finding**: Zappa does not store, process, or transmit sensitive data. It handles deployment artifacts (zip files of user code) temporarily in S3 and passes environment variables to Lambda, but does not own or persist user data. The `REMOTE_ENV` feature loads secrets from S3 into Lambda environment variables at cold start — these are transient and not logged.
- **Gap**: N/A — not a data-handling target.
- **Recommendation**: None needed.
- **Evidence**: `zappa/handler.py` (`load_remote_settings` — loads then discards S3 JSON), `zappa/core.py` (S3 upload of deployment zip)

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — normally RISK-SAFETY, but downgraded to INFO because `has_persistent_data_store` is false AND `has_logging_of_user_data` is false. No persistent data store and no user-data logging — residency requirements do not apply.
- **Finding**: Zappa deploys to user-specified AWS regions (configurable via `aws_region` in `zappa_settings.json`). It does not hold data subject to residency constraints itself.
- **Gap**: N/A — no data residency concern for the tool.
- **Recommendation**: None needed.
- **Evidence**: `zappa/core.py` (AWS_REGIONS list, region configuration)

#### DATA-Q3: Selective Query Support
- **Severity**: INFO
- **Finding**: Zappa has no query API. It is a CLI tool. The Lambda handler passes requests through to user applications which implement their own query capabilities.
- **Gap**: N/A — no query surface.
- **Recommendation**: None needed.
- **Evidence**: No query/pagination code for Zappa's own data (it has none).

#### DATA-Q4: System of Record Designations
- **Severity**: INFO
- **Finding**: Zappa owns no persistent data and has no system-of-record concern. Deployment state is stored in AWS (CloudFormation stacks, Lambda versions, S3 buckets) — AWS is the system of record for deployment state.
- **Gap**: N/A — no data ownership.
- **Recommendation**: None needed.
- **Evidence**: `zappa/core.py` (all state is in AWS services)

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: INFO
- **Finding**: Zappa is stateless and does not manage temporal data. Deployed Lambda functions inherit AWS timestamps (last modified, version). Downgraded to INFO for `stateless-utility` archetype — stateless services with static/reference data have fixed temporal characteristics.
- **Gap**: N/A — no temporal data concerns.
- **Recommendation**: None needed.
- **Evidence**: No timestamp management in Zappa's own data model.

#### DATA-Q6: PII Redaction in Logs
- **Severity**: INFO
- **Finding**: System does not log user data and holds no user data — PII-in-logs risk is not applicable. Zappa's Lambda handler uses `common_log` (Apache Common Log Format) which logs request method, path, status code, and response size — not request/response bodies. The CLI logs deployment progress messages. No PII passes through Zappa's own logging.
- **Gap**: N/A — no PII in Zappa's logging surface.
- **Recommendation**: None needed. Note: if `DEBUG` mode is enabled, the handler logs the raw Lambda event which could contain user request data from the upstream application. This is a debug-only behavior.
- **Evidence**: `zappa/handler.py` (`common_log` call, DEBUG event logging), `zappa/wsgi.py` (common_log implementation)

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: Zappa owns no datasets. No data quality metrics exist because there is no data to measure.
- **Gap**: N/A — no data.
- **Recommendation**: None needed.
- **Evidence**: No data quality tooling in repository.

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: INFO
- **Finding**: Zappa is a Python package published to PyPI with semantic versioning (v0.62.1). The CLI interface is versioned implicitly via the package version. No formal API contract or schema versioning exists — which is expected for a CLI tool. The `CHANGELOG.md` documents breaking changes between versions.
- **Gap**: No formal contract testing for CLI interface stability. However, the comprehensive test suite (8,400+ lines) serves as implicit contract validation.
- **Recommendation**: Consider documenting CLI interface stability guarantees (which commands/options are stable vs experimental) if agents will wrap CLI commands.
- **Evidence**: `CHANGELOG.md`, `setup.py` (version from `__version__`), `tests/test_core.py` (4,447 lines of contract-like tests)

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Zappa's configuration keys in `zappa_settings.json` use clear, descriptive names (`app_function`, `aws_region`, `s3_bucket`, `django_settings`, `keep_warm`, `timeout_seconds`). Code uses readable variable names. No legacy abbreviations or opaque codes.
- **Gap**: None — naming is already clear.
- **Recommendation**: None needed.
- **Evidence**: `example/zappa_settings.json`, `zappa/cli.py` (CUSTOM_SETTINGS list with clear names)

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No data catalog exists — which is expected for a CLI tool/library with no data. The README serves as the primary documentation for configuration options.
- **Gap**: N/A — no data to catalog.
- **Recommendation**: None needed.
- **Evidence**: `README.md` (extensive configuration documentation)

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: INFO
- **Finding**: Library/utility — tracing and correlation are consumer concerns. Zappa supports AWS X-Ray tracing as a pass-through configuration for deployed applications (`xray_tracing` setting). The library itself does not implement OpenTelemetry or structured JSON logging — it uses Python's standard `logging` module with basic format. This is appropriate for a CLI tool.
- **Gap**: N/A — library/CLI tool. Tracing is a consumer concern.
- **Recommendation**: None needed.
- **Evidence**: `zappa/core.py` (X-Ray configuration support), `zappa/handler.py` (basic logging.basicConfig)

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: INFO
- **Finding**: Library/utility — alerting on error rates and latency is a consumer concern. Zappa does not configure CloudWatch alarms for deployed applications. Users must set up alerting independently for their deployed Lambda functions.
- **Gap**: N/A — CLI tool.
- **Recommendation**: None needed.
- **Evidence**: No CloudWatch alarm configuration in source code.

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: Zappa is a deployment tool with no business outcomes to measure. Deployed user applications should define their own business metrics.
- **Gap**: N/A — no business operations.
- **Recommendation**: None needed.
- **Evidence**: No custom metrics publishing in source code.

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: N/A
- **Finding**: This is a `application` repository with `library` N/A mapping applied (dev-library-application override). This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: N/A
- **Finding**: This is a `application` repository with `library` N/A mapping applied (dev-library-application override). This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q3: Rollback Capability
- **Severity**: N/A
- **Finding**: This is a `application` repository with `library` N/A mapping applied (dev-library-application override). This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q4: API Test Coverage
- **Severity**: N/A
- **Finding**: This is a `application` repository with `library` N/A mapping applied (dev-library-application override). This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: N/A
- **Finding**: This is a `application` repository with `library` N/A mapping applied (dev-library-application override). This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| zappa/cli.py | API-Q1, API-Q4, API-Q5, AUTH-Q3, STATE-Q1, STATE-Q2, HITL-Q1, DISC-Q2 |
| zappa/core.py | API-Q1, API-Q7, API-Q8, AUTH-Q1, AUTH-Q2, AUTH-Q5, STATE-Q1, STATE-Q3, STATE-Q4, STATE-Q5, STATE-Q7, DATA-Q2, OBS-Q1 |
| zappa/handler.py | API-Q3, API-Q5, AUTH-Q4, AUTH-Q6, DATA-Q1, DATA-Q6, OBS-Q1 |
| zappa/utilities.py | API-Q7 |
| zappa/asynchronous.py | API-Q6 |
| zappa/wsgi.py | DATA-Q6 |

### Infrastructure as Code
| File | Questions Referenced |
|------|---------------------|
| zappa/policies/assume_policy.json | AUTH-Q1 |
| zappa/policies/attach_policy.json | AUTH-Q2 |
| example/policy/deploy.json | AUTH-Q2 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| .github/workflows/ci.yml | HITL-Q3 |
| .github/workflows/cd.yml | HITL-Q1, HITL-Q2 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| setup.py | API-Q1, DISC-Q1 |
| Pipfile | DISC-Q1 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| example/zappa_settings.json | HITL-Q3, DISC-Q2 |
| CHANGELOG.md | DISC-Q1 |
| README.md | DISC-Q3 |

### Test Files
| File | Questions Referenced |
|------|---------------------|
| tests/test_core.py | DISC-Q1 |
| tests/placebo/ | HITL-Q3 |
