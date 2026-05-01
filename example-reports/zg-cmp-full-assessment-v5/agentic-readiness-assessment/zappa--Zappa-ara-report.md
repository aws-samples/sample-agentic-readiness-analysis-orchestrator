# Agentic Readiness Assessment Report

**Target**: Zappa
**Date**: 2025-07-16
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**TD Version**: 3g1ipe93e5d2wb6n5d4yqaf9
**Repository Type**: application
**Service Archetype**: stateless-utility (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: python, serverless
**Context**: Python framework for deploying WSGI apps on AWS Lambda.

**Archetype Justification**: Zappa is a CLI tool and Lambda handler framework with no persistent data store, no HTTP server of its own, no database connections, and no user-specific data — all operations are deployment tooling or runtime handler wrapping for user applications.

- **Surface flags**:
  - has_persistent_data_store: false
  - has_http_rpc_surface: false
  - has_auth_surface: false
  - has_write_operations: false
  - has_logging_of_user_data: false

> **INFO — Dev-Library-Application Override Applied**: This repository is classified as `repo_type: application` (user-provided) but detected as `service_archetype: stateless-utility` with all five surface flags `false`. Per ARA Step 1.5, the **dev-library-application** override is applied: the `library` N/A mapping is used as the baseline (ENG-Q1 through ENG-Q5 are N/A), and surface-flag downgrades are applied to all remaining questions. The original `repo_type: application` is preserved in the metadata above. Zappa is a deployment CLI and Lambda handler framework — it does not expose an HTTP API, does not own a data store, and does not authenticate requests. Agents would interact with the user applications Zappa deploys, not with Zappa itself.

---

## Readiness Profile: Agent-Ready

**BLOCKERs**: 0 | **RISK-SAFETY**: 0 | **RISK-QUALITY**: 1 | **INFOs**: 28

Cleared for autonomous operation. Instrument observability. Define scope explicitly. Run controlled pilot first.

> **Profile Rationale**: Zappa is a deployment CLI and Lambda handler framework — not a target system that agents call. All 43 questions were evaluated, but the dev-library-application override and surface-flag downgrades correctly resolved nearly every question to INFO because the concerns they measure (API security, data residency, rate limiting, audit logging, etc.) apply to the user applications Zappa deploys, not to the Zappa package itself. The single RISK-QUALITY (DISC-Q1) reflects the absence of formal breaking-change detection in CI — a genuine library-level concern for consumers who build agent tools against Zappa's Python API.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 0 |
| RISK-SAFETY | 0 |
| RISK-QUALITY | 1 |
| INFO | 28 |
| N/A | 5 |
| Not Evaluated (extended) | 9 |
| **Total** | **43** |

**Core Questions Evaluated**: 24 (all applicable core questions evaluated; most resolved to INFO via surface-flag downgrades)
**Extended Questions Triggered**: 8 (API-Q5, API-Q8, STATE-Q3, STATE-Q4, DATA-Q7, DISC-Q2, DISC-Q3, OBS-Q3 — all resolved to INFO)
**Extended Questions Not Triggered**: 9 (STATE-Q2, STATE-Q7, HITL-Q1, HITL-Q2, DATA-Q3, DATA-Q4, DATA-Q5, API-Q6, API-Q7)
**Questions N/A (repo_type: application, dev-library-application override)**: 5 (ENG-Q1 through ENG-Q5)
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
- **Finding**: Zappa uses semantic versioning (`__version__ = "0.62.1"` in `zappa/__init__.py`) and maintains a detailed `CHANGELOG.md` with per-release notes. The CD pipeline (`cd.yml`) supports tagged releases via `mathieudutour/github-tag-action`. However, there is no automated breaking-change detection in CI — no schema comparison tools, no consumer-driven contract tests (Pact), and no typed API surface validation (e.g., `mypy --strict` on public exports). The `mypy` check in CI uses `--ignore-missing-imports` and `--no-site-packages`, which weakens type-level contract enforcement.
- **Gap**: No automated breaking-change detection for the Python API surface. Changes to public functions, class signatures, or configuration schema are not validated against consumer expectations in the CI pipeline.
- **Compensating Controls**:
  - The comprehensive CHANGELOG.md provides manual tracking of breaking changes.
  - Pre-commit hooks run `mypy`, `black`, `isort`, and `flake8` for code quality.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add typed public API surface validation (e.g., `mypy --strict` on `zappa/__init__.py` and key public modules) and consider a tool like `griffe` or `pyright` for Python API breakage detection in CI.
- **Evidence**: `zappa/__init__.py`, `CHANGELOG.md`, `.github/workflows/ci.yml`, `.github/workflows/cd.yml`, `.pre-commit-config.yaml`

---

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO
- **Finding**: Zappa does not expose a REST, GraphQL, or AsyncAPI interface. It is a CLI tool (`console_scripts: zappa=zappa.cli:handle` in `setup.py`) and a Lambda handler framework (`zappa/handler.py`). The CLI commands (`deploy`, `update`, `undeploy`, `rollback`, `tail`, `invoke`, `manage`, `certify`, `init`, `settings`, `status`, `package`, `template`) are documented in the README (~2217 lines). The `handler.py` wraps user WSGI/ASGI applications for Lambda execution — it is not Zappa's own API surface.
- **Implication**: Agents would not call Zappa via HTTP — they would either invoke Zappa's CLI commands or import Zappa's Python classes (`Zappa`, `ZappaCLI`) directly. The integration surface is the Python package API, not an HTTP API.
- **Recommendation**: If agent integration is planned, document the programmatic Python API (the `Zappa` class in `core.py` and `ZappaCLI` class in `cli.py`) separately from the CLI documentation.
- **Evidence**: `setup.py`, `zappa/cli.py`, `zappa/handler.py`, `README.md`

### API-Q2: Machine-Readable API Specification

- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — machine-readable spec is not applicable. Zappa is a CLI/library; its contract is expressed via Python package exports, typed function signatures, and documentation. No OpenAPI, AsyncAPI, or GraphQL schema files exist in the repository.
- **Implication**: For libraries, API contracts are expressed via package manifests and typed exports (Python type hints), which DISC-Q1 evaluates.
- **Recommendation**: Consider generating API documentation from Python docstrings and type hints using tools like `sphinx-autodoc` or `pdoc`.
- **Evidence**: No API spec files found — absence is itself a finding.

### API-Q3: Structured Error Responses

- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — structured error responses are not applicable. Zappa communicates failure via Python exceptions (`ClickException` in `cli.py`), exit codes, and print statements. The handler returns structured Lambda responses with `statusCode` and `body` fields, but these are for the user's application, not Zappa's own API.
- **Implication**: Libraries communicate failure via typed exceptions and error-return conventions, which is appropriate for Zappa's use case.
- **Recommendation**: No action needed for current scope.
- **Evidence**: `zappa/cli.py`, `zappa/handler.py`

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Read-only agents do not execute write operations. Zappa's CLI write operations (deploy, update, undeploy) are deployment tooling operations, not business write endpoints. The handler processes user application requests — idempotency is the user application's concern, not Zappa's.
- **Implication**: If agent_scope were elevated to write-enabled (e.g., an agent deploying Lambda functions via Zappa), idempotency of deployment operations would become relevant.
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: `zappa/cli.py`, `zappa/core.py`

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: Zappa's handler returns structured JSON responses to API Gateway/ALB (with `statusCode`, `headers`, `body`, `isBase64Encoded` fields in `handler.py`). CLI output is unstructured text to stdout. The framework supports binary response encoding via base64 when `BINARY_SUPPORT` is enabled.
- **Implication**: The Lambda response format is well-structured JSON, suitable for API Gateway consumption. CLI output would require parsing for agent consumption.
- **Recommendation**: If CLI-based agent integration is planned, consider adding `--json` output format to CLI commands.
- **Evidence**: `zappa/handler.py`, `zappa/cli.py`

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: Zappa supports configuring API Gateway throttling via `apigateway_throttle_rate` and `apigateway_throttle_burst` settings (in `core.py`). It also supports WAF configuration. However, these are features Zappa provisions for user applications — Zappa itself has no API surface requiring rate limit headers.
- **Implication**: Rate limiting is a concern for the applications Zappa deploys, not for Zappa itself.
- **Recommendation**: No action needed. Zappa's documentation covers API Gateway throttling configuration for deployed applications.
- **Evidence**: `zappa/core.py`, `README.md`

### AUTH-Q1: Machine Identity Authentication

- **Severity**: INFO
- **Finding**: Zappa generates IAM roles and policies for Lambda execution. The `assume_policy.json` allows `apigateway.amazonaws.com`, `lambda.amazonaws.com`, and `events.amazonaws.com` to assume the role. Zappa supports custom `role_name`, `role_arn`, `manage_roles: false`, and `authorizer` configuration for API Gateway. However, Zappa itself does not authenticate incoming requests — it provisions authentication mechanisms for user applications. With `has_auth_surface: false` (dev-library-application), machine identity authentication is a consumer responsibility.
- **Implication**: The IAM policy templates in `zappa/policies/` define the execution role for deployed Lambda functions, not for Zappa itself. An agent calling a Zappa-deployed application would authenticate against that application's auth surface, not against Zappa.
- **Recommendation**: No action needed for Zappa itself. Users deploying applications should configure appropriate authorizers.
- **Evidence**: `zappa/policies/assume_policy.json`, `zappa/policies/attach_policy.json`, `zappa/core.py`, `example/authmodule.py`

### AUTH-Q2: Scoped Permissions (Least Privilege)

- **Severity**: INFO
- **Finding**: The default `attach_policy.json` uses broad wildcards: `s3:*`, `kinesis:*`, `sns:*`, `sqs:*`, `dynamodb:*`, `route53:*`, `logs:*`, `lambda:InvokeFunction` on `Resource: "*"`. This is explicitly acknowledged as overly permissive. Zappa supports scoped-down permissions via `manage_roles: false` (bring your own role), `role_arn` (custom IAM role ARN), and `extra_permissions` (additive permissions). However, these are permissions for the deployed Lambda execution role, not for Zappa's own identity.
- **Implication**: The overly broad default policy is a known concern for deployed applications — Zappa's README warns users to customize permissions for production. For Zappa itself as a library, the scoped permissions concern applies to the consuming application's deployment.
- **Recommendation**: No action needed for Zappa itself. The documentation already advises users to scope down permissions.
- **Evidence**: `zappa/policies/attach_policy.json`, `zappa/core.py`, `README.md`

### AUTH-Q3: Action-Level Authorization

- **Severity**: INFO
- **Finding**: Zappa supports configuring API Gateway authorizers (Lambda authorizer, IAM authorization, Cognito User Pools, API Key required) for deployed applications. The `example/authmodule.py` demonstrates a Lambda authorizer with fine-grained Allow/Deny policy generation per HTTP verb and resource path. However, these are features Zappa provisions for user applications — Zappa itself does not enforce action-level authorization.
- **Implication**: Action-level authorization is the responsibility of the application deployed via Zappa, not of the Zappa framework.
- **Recommendation**: No action needed for Zappa itself.
- **Evidence**: `example/authmodule.py`, `zappa/core.py`, `zappa/handler.py`

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: INFO
- **Finding**: Zappa propagates API Gateway authorizer context to WSGI/ASGI applications via `API_GATEWAY_AUTHORIZER` environ variable and `REMOTE_USER` (extracted from `authorizer.principalId` or `identity.userArn`). This is visible in `wsgi.py` (`process_lambda_payload_v1`, `process_lambda_payload_v2`) and `asgi.py` (`create_asgi_scope`). The framework correctly distinguishes between Lambda authorizer, IAM authorizer, and Cognito authorizer contexts.
- **Implication**: Identity propagation through the handler layer is well-implemented. The user application receives the authenticated principal identity. For `stateless-utility` archetype, this is downgraded to INFO — Zappa serves as a pass-through for identity context.
- **Recommendation**: No action needed. Identity propagation is correctly implemented.
- **Evidence**: `zappa/wsgi.py`, `zappa/asgi.py`, `zappa/handler.py`

### AUTH-Q5: Credential Management

- **Severity**: INFO
- **Finding**: Zappa uses AWS profile-based credentials (boto3 default credential chain) — no hardcoded credentials found in the codebase. Zappa supports `remote_env` (S3-stored environment variables loaded at handler init), `aws_kms_key_arn` for KMS encryption of Lambda environment variables, and `aws_environment_variables` for setting environment variables. No `.env` files are committed to the repository. The `test_settings.json` references S3 URLs for remote environments but contains no actual credentials.
- **Implication**: Credential management is properly delegated to AWS credential chain and S3/KMS for secrets. No hardcoded secrets found.
- **Recommendation**: No action needed. The credential management approach is sound.
- **Evidence**: `zappa/handler.py` (load_remote_settings), `zappa/core.py`, `test_settings.json`, `test_settings.py`

### AUTH-Q6: Immutable Audit Logging ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity would be RISK-SAFETY, but surface-flag calibration applies
- **Finding**: System does not execute agent-invoked write operations — audit logging is a consumer responsibility. The library/utility is called by applications that own the audit context. Zappa does not configure CloudTrail, CloudWatch log file validation, or immutable log storage. The handler logs in Apache Common Log Format to CloudWatch via Python's `logging` module, but this is for user application request logging, not for audit attribution.
- **Implication**: Audit logging for agent-initiated actions is the responsibility of the application deployed via Zappa and the AWS account's CloudTrail configuration, not of the Zappa framework itself.
- **Recommendation**: No action needed for Zappa itself. Users should ensure CloudTrail is enabled in their AWS accounts.
- **Evidence**: `zappa/wsgi.py` (common_log), `zappa/handler.py`, `zappa/utilities.py` (ApacheNCSAFormatters)

### AUTH-Q7: Agent Identity Suspension

- **Severity**: INFO
- **Finding**: System does not issue or enforce agent identities — suspension is a consumer responsibility. Libraries and utilities are invoked by applications that own identity lifecycle. Zappa does not manage agent identities. IAM role management (create, delete) is a deployment-time concern handled by the CLI.
- **Implication**: Agent identity suspension would be managed at the AWS IAM level for the deployed application, not within Zappa.
- **Recommendation**: No action needed for Zappa itself.
- **Evidence**: `zappa/core.py`, `zappa/cli.py`

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity would be RISK-SAFETY, but surface-flag calibration and archetype calibration apply
- **Finding**: System exposes no write operations in an agent-consumable API — compensation logic is not applicable. Zappa's CLI has a `rollback` command for reverting Lambda deployments to a previous version, but this is a deployment tooling operation, not a business transaction rollback. The `stateless-utility` archetype has no multi-step write sequences requiring compensation.
- **Implication**: Rollback capability exists for deployment operations, which is appropriate for the tool's purpose.
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: `zappa/cli.py` (rollback command), `zappa/core.py`

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Read-only agents do not perform writes, so concurrency controls for write operations are informational only. Zappa supports configuring Lambda concurrency limits (`lambda_concurrency` setting) for deployed functions, but this is a deployment configuration feature.
- **Implication**: Concurrency controls are relevant for deployed applications, not for Zappa as a library.
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: `test_settings.json` (lambda_concurrency_enabled), `zappa/core.py`

### STATE-Q4: Circuit Breakers and Resilience

- **Severity**: INFO
- **Finding**: Zappa's CLI calls AWS APIs extensively via boto3 (S3, Lambda, API Gateway, IAM, CloudFormation, CloudWatch, Route53, etc.). No circuit breaker patterns, retry decorators, or resilience libraries (Resilience4j, tenacity) are used in the Zappa codebase. However, boto3 includes built-in retry logic with exponential backoff. The `S3EventSource.add()` in `utilities.py` implements a manual retry loop with `time.sleep(2**attempt)` for S3 notification validation propagation delays. The `letsencrypt.py` has polling loops with `time.sleep()` for DNS propagation and ACME challenge verification. These are deployment-time operations, not agent-consumable runtime paths.
- **Implication**: The absence of explicit circuit breakers is expected for a deployment CLI. boto3's built-in retry handles transient AWS API failures. This is not an agent-consumable runtime service.
- **Recommendation**: No action needed. The existing retry patterns are appropriate for deployment tooling.
- **Evidence**: `zappa/utilities.py` (S3EventSource.add retry loop), `zappa/letsencrypt.py` (polling loops), `zappa/core.py`

### STATE-Q5: Rate Limiting and Throttling

- **Severity**: INFO
- **Finding**: System exposes no HTTP/RPC surface — API-layer rate limiting is not applicable. Libraries invoked by consuming applications inherit the consumer's rate limiting, not their own. Zappa supports configuring API Gateway throttling for deployed applications via `apigateway_throttle_rate` and `apigateway_throttle_burst`.
- **Implication**: Rate limiting is a deployed-application concern, not a Zappa library concern.
- **Recommendation**: No action needed.
- **Evidence**: `zappa/core.py`

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Read-only agents cannot modify records, trigger spend, or delete data. Transaction limits for write operations are informational only. Zappa does not implement configurable transaction limits — this is appropriate for a deployment CLI/framework.
- **Implication**: Relevant for future scope expansion planning only.
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: `zappa/cli.py`, `zappa/core.py`

### HITL-Q3: Sandbox/Staging Environment

- **Severity**: INFO
- **Finding**: Library/utility — does not own staging environments. Zappa supports configuring multiple stages (e.g., `dev`, `staging`, `prod`) in `zappa_settings.json`. The `example/zappa_settings.json` demonstrates multi-stage configuration (`dev_event`, `dev_api`, `prod`). However, these are deployment targets for user applications, not test environments for the Zappa library itself. The CI pipeline (`.github/workflows/ci.yml`) runs tests across Python 3.9–3.14 with coverage, which serves as the library's own quality gate.
- **Implication**: Staging environments are a deployed-application concern. Zappa's CI/CD pipeline provides adequate testing for the library.
- **Recommendation**: No action needed.
- **Evidence**: `example/zappa_settings.json`, `.github/workflows/ci.yml`, `Makefile`

### DATA-Q1: Sensitive Data Classification

- **Severity**: INFO
- **Finding**: Not a data-handling target — no PII/PHI/financial/credential data is stored, processed, or logged by Zappa itself. Zappa is a deployment CLI and handler framework. It interacts with S3 (deployment artifacts), DynamoDB (optional async response table), and other AWS services for deployment purposes only. The handler passes through user application data without inspecting or storing it.
- **Implication**: Data classification is the responsibility of the user application deployed via Zappa, not of the Zappa framework.
- **Recommendation**: No action needed for Zappa itself.
- **Evidence**: `zappa/handler.py`, `zappa/asynchronous.py`, `zappa/core.py`

### DATA-Q2: Data Residency and Sovereignty ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity would be RISK-SAFETY, but surface-flag calibration applies
- **Finding**: No persistent data store and no user-data logging — residency requirements do not apply. Zappa deploys Lambda functions to a user-specified AWS region. Data residency for the deployed application is configured by the user via `aws_region` in `zappa_settings.json`.
- **Implication**: Data residency is the responsibility of the deployed application and its AWS region configuration.
- **Recommendation**: No action needed for Zappa itself.
- **Evidence**: `example/zappa_settings.json`, `zappa/core.py`

### DATA-Q6: PII Redaction in Logs

- **Severity**: INFO
- **Finding**: System does not log user data and holds no user data — PII-in-logs risk is not applicable. Zappa's handler logs in Apache Common Log Format: remote address, request method, path, query string, status code, content length, referer, and user agent (`zappa/utilities.py` — `ApacheNCSAFormatters`). It does not log request/response bodies. The handler does log environment variable loading at DEBUG level (`load_remote_settings` in `handler.py` — `"Adding {} -> {} to environment"`) which could expose sensitive values, but only when `LOG_LEVEL=DEBUG` — this is a user configuration choice, not a default behavior.
- **Implication**: The DEBUG-level environment variable logging in `load_remote_settings` is a potential concern if users store secrets in `remote_env` with DEBUG logging enabled, but this is a user misconfiguration, not a Zappa framework defect.
- **Recommendation**: Consider masking values in the DEBUG log for `load_remote_settings` (e.g., show only the key name, not the value).
- **Evidence**: `zappa/utilities.py` (ApacheNCSAFormatters), `zappa/handler.py` (load_remote_settings)

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: Zappa does not handle datasets with quality scores or completeness metrics. It is a deployment framework. No data quality dashboards, profiling reports, or freshness SLAs exist.
- **Implication**: Data quality is a deployed-application concern, not a Zappa framework concern.
- **Recommendation**: No action needed.
- **Evidence**: No evidence found — absence is itself a finding, but expected for this repo type.

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Zappa's Python API uses readable, semantically meaningful names. Configuration keys in `zappa_settings.json` are descriptive (`app_function`, `s3_bucket`, `aws_region`, `log_level`, `keep_warm`, `binary_support`, `environment_variables`). The codebase uses clear variable names (`lambda_function_name`, `api_stage`, `project_name`). No legacy abbreviations or opaque codes requiring a data dictionary were found.
- **Implication**: The naming conventions support LLM-based reasoning and agent tool generation without requiring a lookup table.
- **Recommendation**: No action needed. Naming is already clear and consistent.
- **Evidence**: `example/zappa_settings.json`, `test_settings.json`, `zappa/cli.py`, `zappa/core.py`

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No data catalog or metadata layer — expected for a deployment CLI/framework. Zappa does not hold data requiring cataloging. The README serves as the primary documentation for configuration options and features.
- **Implication**: Not applicable to this repository type.
- **Recommendation**: No action needed.
- **Evidence**: `README.md`

### OBS-Q1: Distributed Tracing and Structured Logging

- **Severity**: INFO
- **Finding**: Library/utility — tracing and correlation are consumer concerns. Zappa supports X-Ray tracing as a feature for user applications (`xray_tracing` setting configurable in `zappa_settings.json`, provisioned via `core.py`). The handler itself does not instrument its own code with OpenTelemetry or X-Ray SDK — it enables tracing at the Lambda function level for the user's application. Logging uses Python's `logging` module with `basicConfig()` — structured JSON logging is not implemented for Zappa's own logs.
- **Implication**: The library's obligation is to propagate trace context if provided, which it does by supporting `xray_tracing` configuration. Structured logging for the library itself would be a nice-to-have but is not required.
- **Recommendation**: No action needed for current scope.
- **Evidence**: `zappa/handler.py`, `zappa/core.py`, `zappa/utilities.py`

### OBS-Q2: Alerting on Error Rates and Latency

- **Severity**: INFO
- **Finding**: Library/utility — alerting on error rates and latency is a consumer concern. Zappa does not configure CloudWatch alarms, PagerDuty, or OpsGenie integrations for itself. It supports CloudWatch log group creation and retention configuration for deployed Lambda functions.
- **Implication**: Alerting is the responsibility of the deployed application's operational infrastructure.
- **Recommendation**: No action needed.
- **Evidence**: `zappa/core.py`

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No custom business metrics are published by Zappa. The framework does not call `cloudwatch.put_metric_data` for business events. Request logging in Apache CLF provides basic operational metrics (status codes, response times) for the deployed application.
- **Implication**: Business outcome metrics are the responsibility of the deployed application.
- **Recommendation**: No action needed.
- **Evidence**: `zappa/utilities.py` (ApacheNCSAFormatters), `zappa/handler.py`

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: Zappa does not expose a REST, GraphQL, or AsyncAPI interface. It is a CLI tool (`console_scripts: zappa=zappa.cli:handle` in `setup.py`) and a Lambda handler framework (`zappa/handler.py`). The CLI is documented in the README. The handler wraps user WSGI/ASGI applications — it is not Zappa's own API surface. Dev-library-application: no HTTP/RPC surface to document.
- **Gap**: No programmatic Python API documentation separate from README CLI docs.
- **Recommendation**: If agent integration is planned, document the `Zappa` class and `ZappaCLI` class programmatic APIs.
- **Evidence**: `setup.py`, `zappa/cli.py`, `zappa/handler.py`, `README.md`

#### API-Q2: Machine-Readable API Specification
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — machine-readable spec is not applicable. Zappa is a CLI/library; its contract is expressed via Python package exports and type hints. No OpenAPI, AsyncAPI, or GraphQL schema files exist.
- **Gap**: N/A — no HTTP API to specify.
- **Recommendation**: Consider generating API docs from Python type hints using `sphinx-autodoc` or `pdoc`.
- **Evidence**: No API spec files found — absence is itself a finding.

#### API-Q3: Structured Error Responses
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — structured error responses are not applicable. Zappa communicates failure via Python exceptions (`ClickException`) and exit codes. The handler returns structured Lambda responses for user applications.
- **Gap**: N/A — no HTTP API surface.
- **Recommendation**: No action needed.
- **Evidence**: `zappa/cli.py`, `zappa/handler.py`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Read-only agents do not execute write operations. Zappa's CLI write operations are deployment tooling, not business write endpoints.
- **Gap**: N/A for read-only scope.
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: `zappa/cli.py`, `zappa/core.py`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: Zappa's handler returns structured JSON responses to API Gateway/ALB (`statusCode`, `headers`, `body`, `isBase64Encoded`). CLI output is unstructured text.
- **Gap**: CLI lacks `--json` output format for machine consumption.
- **Recommendation**: Consider adding `--json` output format to CLI commands for agent consumption.
- **Evidence**: `zappa/handler.py`, `zappa/cli.py`

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has operations >30s OR long-running workflows.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has state changes (stateful-crud, orchestrator).
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: Zappa supports configuring API Gateway throttling via `apigateway_throttle_rate` and `apigateway_throttle_burst` for user applications. Zappa itself has no API surface requiring rate limit headers.
- **Gap**: N/A — no API surface.
- **Recommendation**: No action needed.
- **Evidence**: `zappa/core.py`, `README.md`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: Zappa generates IAM roles and policies for Lambda execution (`assume_policy.json`, `attach_policy.json`). Supports custom `role_name`, `role_arn`, `manage_roles: false`, and API Gateway authorizers. However, Zappa itself does not authenticate incoming requests — it provisions auth mechanisms for user applications. Dev-library-application with `has_auth_surface: false`.
- **Gap**: N/A — machine identity authentication is a consumer responsibility.
- **Recommendation**: No action needed for Zappa itself.
- **Evidence**: `zappa/policies/assume_policy.json`, `zappa/policies/attach_policy.json`, `zappa/core.py`, `example/authmodule.py`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: INFO
- **Finding**: Default `attach_policy.json` uses broad wildcards (`s3:*`, `kinesis:*`, `sns:*`, `sqs:*`, `dynamodb:*`, `route53:*`). Zappa supports scoped-down permissions via `manage_roles: false`, `role_arn`, and `extra_permissions`. These are permissions for deployed Lambda execution roles, not for Zappa's own identity.
- **Gap**: N/A — scoped permissions are a deployed-application concern.
- **Recommendation**: No action needed for Zappa itself. Documentation advises users to scope down permissions.
- **Evidence**: `zappa/policies/attach_policy.json`, `zappa/core.py`, `README.md`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: INFO
- **Finding**: Zappa supports API Gateway authorizers (Lambda, IAM, Cognito, API Key) for deployed applications. `example/authmodule.py` demonstrates fine-grained Allow/Deny per HTTP verb and resource. Zappa itself does not enforce action-level auth.
- **Gap**: N/A — authorization is a deployed-application concern.
- **Recommendation**: No action needed for Zappa itself.
- **Evidence**: `example/authmodule.py`, `zappa/core.py`, `zappa/handler.py`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: Zappa propagates authorizer context to WSGI/ASGI via `API_GATEWAY_AUTHORIZER` environ and `REMOTE_USER` (from `authorizer.principalId` or `identity.userArn`). Correctly distinguishes Lambda, IAM, and Cognito authorizer contexts in `wsgi.py` and `asgi.py`. Archetype calibration: `stateless-utility` → INFO.
- **Gap**: N/A — identity propagation is well-implemented for user applications.
- **Recommendation**: No action needed.
- **Evidence**: `zappa/wsgi.py`, `zappa/asgi.py`, `zappa/handler.py`

#### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: Uses AWS profile-based credentials (boto3 default credential chain). Supports `remote_env` (S3-stored secrets), `aws_kms_key_arn` for KMS encryption. No hardcoded credentials found. No `.env` files committed.
- **Gap**: N/A — credential management is properly delegated.
- **Recommendation**: No action needed.
- **Evidence**: `zappa/handler.py`, `zappa/core.py`, `test_settings.json`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity RISK-SAFETY; surface-flag calibration: `has_auth_surface` false AND `has_write_operations` false → INFO
- **Finding**: System does not execute agent-invoked write operations — audit logging is a consumer responsibility. Zappa does not configure CloudTrail or immutable log storage. Handler logs in Apache CLF format for user application request logging.
- **Gap**: N/A — audit logging is a consumer responsibility.
- **Recommendation**: Users should ensure CloudTrail is enabled in their AWS accounts.
- **Evidence**: `zappa/wsgi.py`, `zappa/handler.py`, `zappa/utilities.py`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: INFO
- **Finding**: System does not issue or enforce agent identities — suspension is a consumer responsibility. Zappa does not manage agent identities. IAM role management is a deployment-time concern.
- **Gap**: N/A — identity lifecycle is a consumer responsibility.
- **Recommendation**: No action needed for Zappa itself.
- **Evidence**: `zappa/core.py`, `zappa/cli.py`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity RISK-SAFETY; surface-flag: `has_write_operations` false AND `has_http_rpc_surface` false → INFO; archetype `stateless-utility` → INFO
- **Finding**: System exposes no write operations in an agent-consumable API — compensation logic is not applicable. Zappa's CLI has a `rollback` command for deployment versioning, but this is a tooling operation.
- **Gap**: N/A — no multi-step write sequences.
- **Recommendation**: No action needed for read-only scope.
- **Evidence**: `zappa/cli.py`, `zappa/core.py`

#### STATE-Q2: Queryable Current State
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator).
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Read-only agents do not perform writes. Zappa supports configuring Lambda concurrency limits (`lambda_concurrency`) for deployed functions.
- **Gap**: N/A for read-only scope.
- **Recommendation**: No action needed.
- **Evidence**: `test_settings.json`, `zappa/core.py`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: INFO
- **Finding**: Zappa CLI calls AWS APIs extensively via boto3. No explicit circuit breaker patterns found, but boto3 includes built-in retry. Manual retry in `S3EventSource.add()` with backoff (`time.sleep(2**attempt)`). `letsencrypt.py` has polling loops. These are deployment-time operations, not agent-consumable runtime paths. Dev-library-application: this is not a runtime agent-consumable service.
- **Gap**: No explicit circuit breaker library, but boto3 retries suffice for a deployment tool.
- **Recommendation**: No action needed.
- **Evidence**: `zappa/utilities.py`, `zappa/letsencrypt.py`, `zappa/core.py`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: INFO
- **Finding**: System exposes no HTTP/RPC surface — API-layer rate limiting is not applicable. Zappa supports configuring API Gateway throttling for deployed applications.
- **Gap**: N/A — no API surface.
- **Recommendation**: No action needed.
- **Evidence**: `zappa/core.py`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Read-only agents cannot modify records. Zappa does not implement configurable transaction limits — appropriate for a deployment CLI.
- **Gap**: N/A for read-only scope.
- **Recommendation**: No action needed.
- **Evidence**: `zappa/cli.py`, `zappa/core.py`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path. Priority is P2.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled. Scope is read-only.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled. Scope is read-only.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: INFO
- **Finding**: Library/utility — does not own staging environments. Zappa supports multi-stage deployment configuration (`dev`, `staging`, `prod`) in `zappa_settings.json`. CI pipeline runs tests across Python 3.9–3.14. `has_http_rpc_surface` false AND `has_persistent_data_store` false → INFO.
- **Gap**: N/A — staging is a deployed-application concern.
- **Recommendation**: No action needed.
- **Evidence**: `example/zappa_settings.json`, `.github/workflows/ci.yml`, `Makefile`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO
- **Finding**: Not a data-handling target — no PII/PHI/financial/credential data is stored, processed, or logged by Zappa. Dev-library-application override applied. Zappa is a deployment CLI/framework that passes through user application data without inspecting or storing it.
- **Gap**: N/A — no sensitive data handled.
- **Recommendation**: No action needed for Zappa itself.
- **Evidence**: `zappa/handler.py`, `zappa/asynchronous.py`, `zappa/core.py`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity RISK-SAFETY; surface-flag: `has_persistent_data_store` false AND `has_logging_of_user_data` false → INFO
- **Finding**: No persistent data store and no user-data logging — residency requirements do not apply. Zappa deploys to user-specified AWS regions via `aws_region` setting.
- **Gap**: N/A — residency is a deployed-application concern.
- **Recommendation**: No action needed for Zappa itself.
- **Evidence**: `example/zappa_settings.json`, `zappa/core.py`

#### DATA-Q3: Selective Query Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has list/query endpoints with potentially unbounded results.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q4: System of Record Designations
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway).
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator).
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q6: PII Redaction in Logs
- **Severity**: INFO
- **Finding**: System does not log user data and holds no user data — PII-in-logs risk is not applicable. Zappa logs in Apache CLF: remote addr, method, path, query, status, content length, referer, user agent. Does not log request/response bodies. DEBUG-level `load_remote_settings` logs env var key-value pairs, which could expose secrets if user enables DEBUG with `remote_env` containing secrets — but this is user misconfiguration.
- **Gap**: DEBUG-level logging in `load_remote_settings` could expose secret values.
- **Recommendation**: Consider masking values in the DEBUG log for `load_remote_settings`.
- **Evidence**: `zappa/utilities.py`, `zappa/handler.py`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: Zappa does not handle datasets. No data quality dashboards, profiling, or freshness SLAs. Expected for a deployment framework.
- **Gap**: N/A — not a data-handling system.
- **Recommendation**: No action needed.
- **Evidence**: No evidence found — absence expected for this repo type.

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: Zappa uses semantic versioning (`__version__ = "0.62.1"` in `zappa/__init__.py`) and maintains `CHANGELOG.md` (~604 lines). The CD pipeline supports tagged releases. However, no automated breaking-change detection exists in CI — no schema comparison tools, no consumer-driven contract tests, and `mypy` in CI uses `--ignore-missing-imports` which weakens type-level contract enforcement.
- **Gap**: No automated breaking-change detection for the Python API surface.
- **Recommendation**: Add Python API breakage detection (e.g., `griffe`) and stricter type checking to CI.
- **Evidence**: `zappa/__init__.py`, `CHANGELOG.md`, `.github/workflows/ci.yml`, `.github/workflows/cd.yml`, `.pre-commit-config.yaml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Zappa uses readable, semantically meaningful names throughout. Config keys: `app_function`, `s3_bucket`, `aws_region`, `log_level`, `keep_warm`, `binary_support`. Code variables: `lambda_function_name`, `api_stage`, `project_name`. No legacy abbreviations found.
- **Gap**: N/A — naming is clear and consistent.
- **Recommendation**: No action needed.
- **Evidence**: `example/zappa_settings.json`, `test_settings.json`, `zappa/cli.py`, `zappa/core.py`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No data catalog — expected for a deployment CLI/framework. README serves as primary documentation. No AWS Glue, Collibra, or similar metadata tools.
- **Gap**: N/A — not applicable to this repository type.
- **Recommendation**: No action needed.
- **Evidence**: `README.md`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: INFO
- **Finding**: Library/utility — tracing and correlation are consumer concerns. Zappa supports X-Ray tracing as a feature for user apps (`xray_tracing` setting provisioned via `core.py`). Handler does not instrument itself with OTel or X-Ray SDK. Logging uses Python `logging` with `basicConfig()` — no structured JSON logging.
- **Gap**: Library's own logging is unstructured, but this is typical for Python CLIs.
- **Recommendation**: No action needed for current scope.
- **Evidence**: `zappa/handler.py`, `zappa/core.py`, `zappa/utilities.py`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: INFO
- **Finding**: Library/utility — alerting is a consumer concern. No CloudWatch alarms, PagerDuty, or OpsGenie configured. Zappa supports CloudWatch log group creation for deployed functions.
- **Gap**: N/A — alerting is a deployed-application concern.
- **Recommendation**: No action needed.
- **Evidence**: `zappa/core.py`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics published. No `cloudwatch.put_metric_data` calls. Apache CLF logging provides basic operational metrics (status codes, response times) for deployed applications.
- **Gap**: N/A — business metrics are a deployed-application concern.
- **Recommendation**: No action needed.
- **Evidence**: `zappa/utilities.py`, `zappa/handler.py`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: N/A
- **Finding**: This is a `library` (dev-library-application override) repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: N/A
- **Finding**: This is a `library` (dev-library-application override) repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q3: Rollback Capability
- **Severity**: N/A
- **Finding**: This is a `library` (dev-library-application override) repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q4: API Test Coverage
- **Severity**: N/A
- **Finding**: This is a `library` (dev-library-application override) repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: N/A
- **Finding**: This is a `library` (dev-library-application override) repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `zappa/__init__.py` | DISC-Q1 |
| `zappa/cli.py` | API-Q1, API-Q3, API-Q4, API-Q5, AUTH-Q7, STATE-Q1, STATE-Q6 |
| `zappa/core.py` | API-Q4, API-Q8, AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q5, AUTH-Q7, DATA-Q1, DATA-Q2, STATE-Q1, STATE-Q3, STATE-Q4, STATE-Q5, STATE-Q6, OBS-Q1, OBS-Q2 |
| `zappa/handler.py` | API-Q1, API-Q3, API-Q5, AUTH-Q1, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q6, DATA-Q1, DATA-Q6, OBS-Q1, OBS-Q3 |
| `zappa/wsgi.py` | AUTH-Q4, AUTH-Q6 |
| `zappa/asgi.py` | AUTH-Q4 |
| `zappa/asynchronous.py` | DATA-Q1 |
| `zappa/utilities.py` | AUTH-Q6, DATA-Q6, STATE-Q4, OBS-Q1, OBS-Q3 |
| `zappa/letsencrypt.py` | STATE-Q4 |
| `zappa/middleware.py` | (supporting evidence for handler architecture) |
| `zappa/websocket.py` | (supporting evidence for handler architecture) |
| `zappa/ext/django_zappa.py` | (supporting evidence for handler architecture) |

### IAM Policy Templates
| File | Questions Referenced |
|------|---------------------|
| `zappa/policies/assume_policy.json` | AUTH-Q1 |
| `zappa/policies/attach_policy.json` | AUTH-Q1, AUTH-Q2 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/ci.yml` | DISC-Q1, HITL-Q3 |
| `.github/workflows/cd.yml` | DISC-Q1 |
| `.github/workflows/maintenance.yml` | (repo maintenance — not directly cited) |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `setup.py` | API-Q1 |
| `Pipfile` | (dependency inventory) |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `test_settings.json` | AUTH-Q5, STATE-Q3, DISC-Q2 |
| `test_settings.py` | AUTH-Q5 |
| `example/zappa_settings.json` | DATA-Q2, DISC-Q2, HITL-Q3 |
| `example/authmodule.py` | AUTH-Q1, AUTH-Q3 |
| `example/app.py` | (example Flask application) |
| `.pre-commit-config.yaml` | DISC-Q1 |
| `Makefile` | HITL-Q3 |

### Documentation
| File | Questions Referenced |
|------|---------------------|
| `README.md` | API-Q1, API-Q8, AUTH-Q2, DISC-Q3 |
| `CHANGELOG.md` | DISC-Q1 |
