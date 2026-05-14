# Agentic Readiness Analysis Report

**Target**: dvc (Data Version Control)
**Date**: 2026-04-30
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**Repository Type**: application
**Service Archetype**: stateless-utility (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: python, ml, data
**Context**: Data Version Control: git-for-ML-data, models, and experiments.

**Archetype Justification**: DVC is a Python CLI tool with no HTTP/RPC server, no persistent data store, no authentication surface, no write endpoints, and no user-data logging. All five surface flags are `false`. It operates as a command-line utility that wraps remote storage operations for data versioning.

- **Surface flags**:
  - has_persistent_data_store: false
  - has_http_rpc_surface: false
  - has_auth_surface: false
  - has_write_operations: false
  - has_logging_of_user_data: false

> **INFO — Dev-Library-Application Override Applied**: This repository is classified as `repo_type: application` (has source code and an entry point at `dvc/cli/__init__.py:main()`), but its `service_archetype` is `stateless-utility` and all 5 surface flags are `false`. Per the ARA methodology, the **dev-library-application override** is applied: the `library` N/A mapping is used as the baseline for scoring (only ENG-Q1 through ENG-Q5 are non-N/A), then surface-flag downgrades are applied to any remaining questions. The original `repo_type: application` is preserved in the metadata above. DVC is a CLI tool / Python library distributed via PyPI — it does not own APIs, data stores, or auth surfaces that an agent would call.

---

## Readiness Profile: Agent-Ready

**BLOCKERs**: 0 | **RISK-SAFETY**: 0 | **RISK-QUALITY**: 1 | **INFOs**: 32

Cleared for autonomous operation. Instrument observability. Define scope explicitly. Run controlled pilot first.

> Note: The single RISK-QUALITY finding (DISC-Q1) relates to schema versioning for the Python API. DVC uses `setuptools_scm` for version management but lacks consumer-driven contract testing or breaking-change detection in CI for the `dvc.api` public interface. This does not affect agent safety.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 0 |
| RISK-SAFETY | 0 |
| RISK-QUALITY | 1 |
| INFO | 32 |
| N/A | 0 |
| Not Evaluated (extended) | 10 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 9
**Extended Questions Not Triggered**: 10
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

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: DVC uses `setuptools_scm` for semantic versioning (configured in `pyproject.toml`). The public Python API is defined in `dvc/api/__init__.py` with a clear `__all__` export list (`DVCFileSystem`, `all_branches`, `all_commits`, `all_tags`, `artifacts_show`, `exp_save`, `exp_show`, `get_dataset`, `get_url`, `metrics_show`, `open`, `params_show`, `read`). However, there is no automated breaking-change detection in CI for the `dvc.api` module. The CI pipeline (`tests.yaml`) runs comprehensive unit/functional tests and type-checking via mypy, but does not include consumer-driven contract tests (e.g., Pact) or API diff tooling that would detect breaking changes to the public Python API surface before release.
- **Gap**: No automated breaking-change detection or consumer-driven contract testing for the public `dvc.api` Python interface. Agent tool bindings wrapping `dvc.api` functions could break silently when DVC releases a new version with changed function signatures.
- **Compensating Controls**:
  - Pin DVC version in agent tool dependencies (e.g., `dvc>=3.0,<4.0`) to avoid unexpected breaking changes.
  - Monitor DVC release notes and changelogs for API changes before upgrading.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add API surface regression tests or a schema snapshot comparison (e.g., checking exported symbols and function signatures in `dvc/api/__init__.py`) to the CI pipeline.
- **Evidence**: `pyproject.toml` (setuptools_scm config), `dvc/api/__init__.py` (__all__ exports), `.github/workflows/tests.yaml` (CI pipeline without contract testing)

---

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: DVC exposes a documented Python API (`dvc.api` module) and CLI interface (`dvc` command), but no REST, GraphQL, or AsyncAPI HTTP interface. The Python API provides functions like `open()`, `read()`, `get_url()`, `params_show()`, `metrics_show()`, `exp_show()`, and `exp_save()`. Documentation is available at https://dvc.org/doc.
- **Implication**: An agent would interact with DVC via its Python API or CLI subprocess invocation, not via HTTP. Agent tool definitions would wrap `dvc.api` functions or `subprocess.run(["dvc", ...])` calls.
- **Recommendation**: If agent integration is planned, define agent tools wrapping `dvc.api` functions directly — this is more reliable than CLI subprocess invocation.
- **Evidence**: `dvc/api/__init__.py`, `dvc/cli/__init__.py`, `pyproject.toml` (`[project.scripts] dvc = "dvc.cli:main"`)

### API-Q2: Machine-Readable API Specification
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — machine-readable spec is not applicable. DVC has no OpenAPI, AsyncAPI, or Swagger specification. This is expected for a CLI/library tool. The Python API surface is defined via typed function signatures in `dvc/api/*.py`.
- **Implication**: Agent tool schemas would be authored manually from the `dvc.api` function signatures and docstrings, not auto-generated from an OpenAPI spec.
- **Recommendation**: No action needed. For libraries, API contracts are expressed via typed exports and docstrings, which DISC-Q1 evaluates.
- **Evidence**: No `openapi.yaml`, `swagger.yaml`, or `asyncapi.yaml` found in the repository.

### API-Q3: Structured Error Responses
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — structured error responses are not applicable. DVC has a rich exception hierarchy defined in `dvc/exceptions.py` with typed Python exceptions (`DvcException`, `InvalidArgumentError`, `FileMissingError`, `PathMissingError`, etc.). These are Python exceptions for CLI/library use, not HTTP error responses.
- **Implication**: Agent tools wrapping `dvc.api` would catch typed Python exceptions rather than parsing HTTP error codes.
- **Recommendation**: No action needed.
- **Evidence**: `dvc/exceptions.py`

### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No HTTP write endpoints exist. DVC is a CLI tool; write operations (`dvc add`, `dvc push`) are executed by the user via CLI, not via agent-callable HTTP endpoints. Additionally, `agent_scope` is read-only.
- **Implication**: Not applicable for read-only agent scope against a CLI/library tool.
- **Recommendation**: No action needed.
- **Evidence**: `dvc/api/__init__.py` (only `exp_save` is a write operation in the Python API)

### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: DVC CLI outputs text/table format by default with `--json` flag support for machine-readable output. The Python API (`dvc.api`) returns native Python objects (dicts, strings, lists). `dvc.api.metrics_show()` and `dvc.api.params_show()` return `dict`. `dvc.api.exp_show()` returns `list[dict]`.
- **Implication**: The Python API returns structured data natively, making it well-suited for agent consumption without additional parsing.
- **Recommendation**: Prefer `dvc.api` Python functions over CLI invocation for agent integration — structured Python objects are more reliable than parsing CLI text output.
- **Evidence**: `dvc/api/show.py`, `dvc/api/experiments.py`, `dvc/api/data.py`

### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No HTTP surface — rate limit headers are not applicable. DVC is a CLI tool with no inbound API surface to rate-limit.
- **Implication**: Rate limiting is not a concern for a locally-executed CLI tool. If DVC interacts with remote storage (S3, GCS), the rate limits of those underlying services apply.
- **Recommendation**: No action needed.
- **Evidence**: No HTTP server code found in repository.

### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: System does not issue or enforce agent identities — authentication is a consumer responsibility. DVC delegates all authentication to underlying storage providers (AWS credentials for S3, GCS service accounts, SSH keys). It reads credentials from environment variables (`DVC_STUDIO_TOKEN`) and config files (`.dvc/config`) but does not implement its own authentication system.
- **Implication**: An agent invoking DVC would authenticate to storage backends using its own configured credentials (e.g., AWS IAM role, GCS service account), not through DVC's authentication layer.
- **Recommendation**: No action needed. Ensure the agent's execution environment has properly scoped credentials for the remote storage backends DVC will access.
- **Evidence**: `dvc/env.py` (DVC_STUDIO_TOKEN), `dvc/config.py`, `dvc/data_cloud.py`

### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: INFO
- **Finding**: System does not enforce permissions — scoped permissions are a consumer responsibility. DVC inherits whatever permissions the underlying storage credentials provide. No permission model exists within DVC itself.
- **Implication**: Least-privilege for agent access to DVC-managed data is enforced at the storage provider layer (e.g., IAM policies for S3 buckets), not within DVC.
- **Recommendation**: No action needed.
- **Evidence**: `dvc/data_cloud.py`, `dvc/fs/__init__.py`

### AUTH-Q3: Action-Level Authorization
- **Severity**: INFO
- **Finding**: System does not enforce action-level authorization — this is a consumer responsibility. DVC has no authorization middleware or permission checks. All operations are available to any user with access to the repository and storage credentials.
- **Implication**: Action-level restrictions (e.g., read-only access to DVC data) must be enforced at the storage provider layer.
- **Recommendation**: No action needed.
- **Evidence**: `dvc/cli/__init__.py`, `dvc/commands/`

### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: Archetype calibration: stateless-utility → INFO. DVC does not propagate identity through service calls. It uses the local user's credentials directly when accessing remote storage.
- **Implication**: Not applicable for a CLI tool.
- **Recommendation**: No action needed.
- **Evidence**: `dvc/data_cloud.py`

### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: DVC references credentials via environment variables and configuration files, delegating actual credential management to storage provider libraries and the user's environment. Key credential references include `DVC_STUDIO_TOKEN` (env var in `dvc/env.py`), remote config paths for `gdrive_user_credentials_file`, `gdrive_service_account_json_file_path`, `credentialpath`, `keyfile`, `cert_path`, `key_path` (defined in `dvc/config.py` `_map_dirs`). No hardcoded credentials were found in the source code. The `# noqa: S105` annotation on `DVC_STUDIO_TOKEN` in `dvc/env.py` acknowledges the token variable name but it is not a hardcoded value.
- **Implication**: DVC's credential handling is appropriate for a CLI tool — it reads credentials from the environment and config files without storing them. An agent invoking DVC should use environment variables or IAM roles, not config files with embedded secrets.
- **Recommendation**: When configuring an agent to use DVC, prefer IAM role-based authentication (e.g., EC2 instance profiles, ECS task roles) over static credentials in environment variables.
- **Evidence**: `dvc/env.py`, `dvc/config.py` (`_map_dirs` method)

### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity would be RISK-SAFETY, but surface-flag calibration applies: has_auth_surface=false AND has_write_operations=false → INFO
- **Finding**: System does not execute agent-invoked write operations — audit logging is a consumer responsibility. The library/utility is called by applications that own the audit context. DVC has no CloudTrail integration, no audit log configuration, and no immutable log storage. This is expected for a client-side CLI tool.
- **Implication**: Audit logging for agent actions using DVC should be implemented at the agent orchestration layer, not within DVC itself.
- **Recommendation**: No action needed within DVC. The consuming agent platform should log all DVC operations invoked by agents.
- **Evidence**: No `aws_cloudtrail` or audit logging configuration found.

### AUTH-Q7: Agent Identity Suspension
- **Severity**: INFO
- **Finding**: System does not issue or enforce agent identities — suspension is a consumer responsibility. Libraries and utilities are invoked by applications that own identity lifecycle. DVC has no concept of agent identities, API keys, or identity management.
- **Implication**: Agent identity suspension would be handled at the storage provider layer (e.g., revoking IAM credentials) or at the agent orchestration layer.
- **Recommendation**: No action needed.
- **Evidence**: `dvc/env.py`, `dvc/config.py`

### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity would be RISK-SAFETY, but surface-flag calibration applies: has_write_operations=false AND has_http_rpc_surface=false → INFO. Additionally archetype is stateless-utility → INFO.
- **Finding**: System exposes no write operations — compensation logic is not applicable. DVC is a CLI tool; its write operations (data push, Git operations) are user-initiated, not agent-callable endpoints.
- **Implication**: Not applicable for a CLI/library tool.
- **Recommendation**: No action needed.
- **Evidence**: `dvc/api/__init__.py`, `dvc/data_cloud.py`

### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: DVC implements CLI-level file locking via `dvc/lock.py` (using `zc.lockfile` and `flufl.lock`) and read-write locking via `dvc/rwlock.py` for local file path operations. These are designed to prevent concurrent DVC CLI commands from corrupting local state, not as API-level concurrency controls for agents. Read-only scope means write concurrency controls are informational.
- **Implication**: If multiple agent instances run `dvc` commands concurrently in the same repository, DVC's built-in file locking will serialize access. This is a positive finding for CLI-based agent integration.
- **Recommendation**: No action needed.
- **Evidence**: `dvc/lock.py`, `dvc/rwlock.py`

### STATE-Q5: Rate Limiting and Throttling
- **Severity**: INFO
- **Finding**: System exposes no HTTP/RPC surface — API-layer rate limiting is not applicable. DVC is a CLI tool with no inbound API to rate-limit. Additionally, archetype is stateless-utility.
- **Implication**: Rate limiting for an agent invoking DVC would be managed at the agent orchestration layer or by the underlying storage provider's rate limits.
- **Recommendation**: No action needed.
- **Evidence**: No HTTP server or API Gateway configuration found.

### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Read-only agents cannot modify records, trigger spend, or delete data. Transaction limits for write operations are informational only.
- **Implication**: Not applicable for read-only scope.
- **Recommendation**: No action needed.
- **Evidence**: N/A

### HITL-Q3: Sandbox/Staging Environment
- **Severity**: INFO
- **Finding**: Library/utility — staging environment is a consumer concern. DVC has extensive test infrastructure: `tests/docker-compose.yml` (Git server for integration tests), comprehensive unit tests (`tests/unit/`), functional tests (`tests/func/`), and integration tests (`tests/integration/`). However, these serve DVC development, not agent testing against DVC-managed data.
- **Implication**: A sandbox for testing agent interactions with DVC-managed data would need to be created at the agent orchestration layer — a dedicated DVC remote pointing to a test S3 bucket, for example.
- **Recommendation**: No action needed within DVC. Create a test DVC remote for agent testing.
- **Evidence**: `tests/docker-compose.yml`, `tests/` directory structure

### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO
- **Finding**: Dev-library-application override applied. DVC does not own user data — it manages versioned data files and ML models that belong to the user's project. It is a version control tool, not a data store. The data sensitivity classification belongs to the ML project that uses DVC, not to DVC itself.
- **Implication**: Data classification requirements apply to the ML projects that use DVC, not to DVC as a tool.
- **Recommendation**: No action needed.
- **Evidence**: `dvc/api/__init__.py`, `dvc/data_cloud.py`

### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity would be RISK-SAFETY, but surface-flag calibration applies: has_persistent_data_store=false AND has_logging_of_user_data=false → INFO. Additionally archetype is stateless-utility → INFO.
- **Finding**: No persistent data store and no user-data logging — residency requirements do not apply. DVC is a CLI tool; the data it manages resides in user-configured remote storage (S3, GCS, Azure Blob), whose residency configuration is the user's responsibility.
- **Implication**: Data residency for DVC-managed data is configured at the storage provider level, not within DVC.
- **Recommendation**: No action needed.
- **Evidence**: `dvc/data_cloud.py`, `dvc/config.py`

### DATA-Q6: PII Redaction in Logs
- **Severity**: INFO
- **Finding**: System does not log user data and holds no user data — PII-in-logs risk is not applicable. DVC's logging (`dvc/logger.py`) is internal diagnostic logging (TRACE/DEBUG/INFO/WARNING/ERROR levels) about DVC operations. The analytics module (`dvc/analytics.py`) sends anonymous usage data: `cmd_class`, `cmd_return_code`, `dvc_version`, `is_binary`, `scm_class`, `system_info`, `user_id` (anonymous telemetry ID), `group_id`, `remotes` (remote type, not URLs), and `git_remote_hash` (hashed, not raw URL). No user PII is logged.
- **Implication**: DVC's logging is appropriately scoped for a CLI tool with no PII exposure.
- **Recommendation**: No action needed.
- **Evidence**: `dvc/logger.py`, `dvc/analytics.py`

### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: DVC provides data integrity features via content-addressable storage (hash-based deduplication and verification). Files are tracked by their hash (`md5`, `sha256`), enabling integrity verification on checkout/pull. However, there is no data quality scoring, completeness metrics, or freshness SLAs — these are properties of the user's ML data, not DVC itself.
- **Implication**: Data quality for DVC-managed datasets is the responsibility of the ML pipeline, not DVC. DVC provides integrity guarantees (hash verification), not quality guarantees.
- **Recommendation**: No action needed.
- **Evidence**: `dvc/data_cloud.py` (hash-based transfer), `dvc/schema.py` (CHECKSUMS_SCHEMA)

### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: DVC's Python API uses clear, semantically meaningful function and parameter names: `metrics_show()`, `params_show()`, `exp_show()`, `exp_save()`, `get_url()`, `open()`, `read()`. Parameters like `repo`, `rev`, `remote`, `mode`, `encoding`, `force`, `num`, `param_deps` are self-explanatory. Return values are standard Python dicts with human-readable keys. No legacy abbreviations or opaque codes found.
- **Implication**: Excellent for agent tool definition — function names and parameters can be directly exposed as tool schemas with minimal renaming.
- **Recommendation**: No action needed.
- **Evidence**: `dvc/api/__init__.py`, `dvc/api/data.py`, `dvc/api/show.py`, `dvc/api/experiments.py`

### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: DVC itself functions as a lightweight data catalog/metadata layer for ML projects. It tracks datasets, models, and experiments with metadata (`.dvc` files, `dvc.yaml`, `dvc.lock`). The `dvc.api` module provides programmatic access to this metadata via functions like `params_show()`, `metrics_show()`, and `exp_show()`. However, there is no centralized data catalog service (e.g., Glue Data Catalog, Collibra) — DVC is the catalog for its own tracked files.
- **Implication**: An agent can discover what data DVC tracks by calling `dvc.api` functions. This is sufficient for agent tool definition.
- **Recommendation**: No action needed.
- **Evidence**: `dvc/api/__init__.py`, `dvc/schema.py`, `dvc/dvcfile.py`

### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: INFO
- **Finding**: Library/utility — tracing and correlation are consumer concerns. DVC does not implement distributed tracing (no OpenTelemetry, no X-Ray). Its logging (`dvc/logger.py`) uses Python's standard `logging` module with custom levels (TRACE, DEBUG, INFO, WARNING, ERROR) and color formatting. Logs are human-readable, not structured JSON. There are no correlation IDs or request tracing.
- **Implication**: If an agent invokes DVC, tracing of DVC operations would need to be implemented at the agent orchestration layer.
- **Recommendation**: No action needed.
- **Evidence**: `dvc/logger.py`

### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: INFO
- **Finding**: Library/utility — alerting on error rates and latency is a consumer concern. No CloudWatch alarms, PagerDuty integration, or alerting configuration exists. This is expected for a client-side CLI tool.
- **Implication**: Alerting for agent failures when using DVC should be configured at the agent orchestration layer.
- **Recommendation**: No action needed.
- **Evidence**: No alerting configuration found.

### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: DVC sends anonymous usage analytics to `analytics.dvc.org` (configurable, opt-out via `DVC_NO_ANALYTICS` env var). The report includes `cmd_class`, `cmd_return_code`, `dvc_version`, `system_info`, anonymous `user_id`, `remotes` (type only), and `git_remote_hash`. This is product telemetry, not business outcome metrics. There are no custom business KPI metrics or dashboards.
- **Implication**: Business outcome metrics for agent interactions with DVC would be tracked at the agent orchestration layer.
- **Recommendation**: No action needed.
- **Evidence**: `dvc/analytics.py`

### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: INFO
- **Finding**: Library/utility — IaC governance is a consumer concern. DVC has no Terraform, CloudFormation, CDK, or Kubernetes manifests. It is distributed as a Python package via PyPI (`pip install dvc`). There is no infrastructure to govern because DVC is a client-side tool, not a deployed service.
- **Implication**: Infrastructure governance for agent environments using DVC is the responsibility of the agent platform team.
- **Recommendation**: No action needed.
- **Evidence**: No IaC files found in repository.

### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — API contract testing is not applicable. DVC has a mature CI/CD pipeline via GitHub Actions: `tests.yaml` (comprehensive multi-OS, multi-Python test matrix with pytest, coverage, parallel execution), `build.yaml` (package build, twine check, PyPI publish), `codeql.yml` (CodeQL security analysis), `plugin_tests.yaml` (remote plugin compatibility testing). Pre-commit hooks enforce ruff linting, mypy type-checking, and code formatting. Codecov integration tracks code coverage. Dependabot monitors dependencies daily. However, there is no HTTP API contract testing because there are no HTTP APIs.
- **Implication**: DVC's CI/CD is excellent for a Python library. Library contract stability is evaluated by DISC-Q1 (the one RISK-QUALITY finding).
- **Recommendation**: No action needed for contract testing of HTTP APIs. See DISC-Q1 recommendation for Python API stability.
- **Evidence**: `.github/workflows/tests.yaml`, `.github/workflows/build.yaml`, `.github/workflows/codeql.yml`, `.github/workflows/plugin_tests.yaml`, `.pre-commit-config.yaml`, `.github/codecov.yml`, `.github/dependabot.yml`

### ENG-Q3: Rollback Capability
- **Severity**: INFO
- **Finding**: No deployed HTTP/RPC surface — deployment rollback is a consumer concern. As a PyPI package, rollback is handled by consumer version pinning (`pip install dvc==X.Y.Z`). The release process uses GitHub releases triggering PyPI publish via `build.yaml`. Test PyPI uploads on main branch pushes provide pre-release validation.
- **Implication**: Rollback for an agent using DVC means pinning to a known-good version in the agent's dependency manifest.
- **Recommendation**: No action needed.
- **Evidence**: `.github/workflows/build.yaml`

### ENG-Q4: API Test Coverage
- **Severity**: INFO
- **Finding**: DVC has an extensive test suite with unit tests (`tests/unit/`), functional tests (`tests/func/`), and integration tests (`tests/integration/`). The Python API is tested in `tests/func/api/` (test_data.py, test_experiments.py, test_show.py, test_artifacts.py, test_scm.py). The CI runs tests across Python 3.9–3.14 on Ubuntu, macOS, and Windows with pytest, coverage reporting, and parallel execution. Codecov tracks coverage. Benchmarks are available in `dvc/testing/benchmarks/`. INFO for stateless-utility archetype.
- **Implication**: Strong test coverage provides confidence that agent tool bindings wrapping `dvc.api` will behave as documented.
- **Recommendation**: No action needed.
- **Evidence**: `tests/func/api/`, `.github/workflows/tests.yaml`, `.github/codecov.yml`, `pyproject.toml` (pytest config)

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: DVC exposes a documented Python API (`dvc.api` module with `__all__` exports) and CLI interface (`dvc` command entry point at `dvc.cli:main`), but no REST, GraphQL, or AsyncAPI HTTP interface. The Python API provides functions: `open()`, `read()`, `get_url()`, `params_show()`, `metrics_show()`, `exp_show()`, `exp_save()`, `artifacts_show()`, `get_dataset()`, `all_branches()`, `all_commits()`, `all_tags()`. Functions have comprehensive docstrings with examples. Dev-library-application override: `has_http_rpc_surface` is `false` — CLI/library tool, not a service with an HTTP API surface.
- **Gap**: No HTTP/RPC API surface exists for agents to call directly. Agent integration requires wrapping Python API or CLI commands.
- **Recommendation**: Define agent tools wrapping `dvc.api` functions directly for structured, typed access to DVC functionality.
- **Evidence**: `dvc/api/__init__.py`, `dvc/cli/__init__.py`, `pyproject.toml`

#### API-Q2: Machine-Readable API Specification
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — machine-readable spec is not applicable. No OpenAPI, AsyncAPI, or Swagger specifications exist. This is expected for a CLI/library. The Python API contracts are expressed via typed function signatures and docstrings in `dvc/api/*.py`.
- **Gap**: N/A — not applicable for CLI/library tools.
- **Recommendation**: No action needed.
- **Evidence**: No `openapi.yaml`, `swagger.yaml`, or `asyncapi.yaml` found.

#### API-Q3: Structured Error Responses
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — structured error responses are not applicable. DVC has a rich typed exception hierarchy in `dvc/exceptions.py`: `DvcException` (base), `InvalidArgumentError`, `FileMissingError`, `PathMissingError`, `OutputNotFoundError`, `OutputDuplicationError`, `CircularDependencyError`, `NotDvcRepoError`, `CyclicGraphError`, `ArtifactNotFoundError`, etc. These provide structured error communication for library consumers.
- **Gap**: N/A — Python exceptions serve the same purpose as HTTP structured errors for library APIs.
- **Recommendation**: No action needed.
- **Evidence**: `dvc/exceptions.py`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No HTTP write endpoints exist. `agent_scope` is read-only. DVC write operations (`dvc add`, `dvc push`, `exp_save`) are CLI/Python API calls, not HTTP endpoints. `has_http_rpc_surface` is `false`.
- **Gap**: N/A — read-only scope and no HTTP surface.
- **Recommendation**: No action needed.
- **Evidence**: `dvc/api/__init__.py`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: DVC CLI supports `--json` output flag. The Python API returns native Python objects: `metrics_show()` → `dict`, `params_show()` → `dict`, `exp_show()` → `list[dict]`, `get_url()` → `str`, `open()` → file object, `read()` → `str`. All structured and directly consumable.
- **Gap**: N/A
- **Recommendation**: Prefer Python API over CLI for agent integration.
- **Evidence**: `dvc/api/show.py`, `dvc/api/experiments.py`, `dvc/api/data.py`

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`. While DVC has long-running operations (data push/pull/fetch), these are CLI commands without an HTTP surface. The dev-library-application override applies.
- **Trigger**: Service has operations >30s OR long-running workflows.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`. DVC is a stateless-utility with no HTTP event emission surface.
- **Trigger**: Service has state changes (stateful-crud, orchestrator).
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No HTTP surface — rate limit headers are not applicable. DVC is a CLI tool with no inbound API surface. Underlying storage provider rate limits (S3, GCS) apply at the provider level.
- **Gap**: N/A
- **Recommendation**: No action needed.
- **Evidence**: No HTTP server code found.

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: DVC does not issue machine identities. It delegates all authentication to underlying storage providers (AWS credentials for S3 via `dvc-s3`, GCS service accounts via `dvc-gs`, SSH keys via `dvc-ssh`). Credentials are read from environment variables (e.g., `DVC_STUDIO_TOKEN`) and config files (`.dvc/config`). Dev-library-application override: `has_auth_surface` is `false`.
- **Gap**: N/A — libraries delegate auth to callers.
- **Recommendation**: Ensure the agent's execution environment has properly scoped credentials for storage backends.
- **Evidence**: `dvc/env.py`, `dvc/config.py`, `dvc/data_cloud.py`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: INFO
- **Finding**: DVC does not enforce permissions; it inherits whatever permissions the underlying storage credentials provide. No permission model exists within DVC. Dev-library-application override applies.
- **Gap**: N/A — scoped permissions are a consumer responsibility.
- **Recommendation**: No action needed.
- **Evidence**: `dvc/data_cloud.py`, `dvc/fs/__init__.py`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: INFO
- **Finding**: No authorization enforcement in DVC. All operations are available to any user with repository and storage access. Dev-library-application override applies.
- **Gap**: N/A — action-level auth is a consumer responsibility.
- **Recommendation**: No action needed.
- **Evidence**: `dvc/cli/__init__.py`, `dvc/commands/`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: Archetype calibration: stateless-utility → INFO. DVC does not propagate identity. It uses the local user's credentials directly when accessing remote storage. No JWT parsing, OAuth flows, or token exchange patterns exist.
- **Gap**: N/A — not applicable for stateless-utility CLI tools.
- **Recommendation**: No action needed.
- **Evidence**: `dvc/data_cloud.py`

#### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: DVC references credentials via environment variables and configuration files, delegating to storage provider libraries. Key credential references: `DVC_STUDIO_TOKEN` (env var in `dvc/env.py`), remote config paths (`gdrive_user_credentials_file`, `gdrive_service_account_json_file_path`, `credentialpath`, `keyfile`, `cert_path`, `key_path` in `dvc/config.py` `_map_dirs`). No hardcoded credentials found. The `# noqa: S105` on `DVC_STUDIO_TOKEN` acknowledges the variable name pattern but is not a hardcoded value.
- **Gap**: DVC does not integrate with a secrets management system (Secrets Manager, Vault) — it reads credentials from environment and config files. This is standard for CLI tools.
- **Recommendation**: When configuring an agent to use DVC, prefer IAM role-based auth over static credentials.
- **Evidence**: `dvc/env.py`, `dvc/config.py`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity RISK-SAFETY, but surface-flag calibration: has_auth_surface=false AND has_write_operations=false → INFO
- **Finding**: System does not execute agent-invoked write operations — audit logging is a consumer responsibility. No CloudTrail integration, no audit log configuration, no immutable log storage. Expected for a client-side CLI tool.
- **Gap**: N/A — audit context is owned by consuming applications.
- **Recommendation**: Implement audit logging at the agent orchestration layer.
- **Evidence**: No `aws_cloudtrail` or audit logging configuration found.

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: INFO
- **Finding**: System does not issue or enforce agent identities — suspension is a consumer responsibility. `has_auth_surface` is `false`. No API keys, service accounts, or identity management within DVC.
- **Gap**: N/A — identity lifecycle is owned by consuming applications.
- **Recommendation**: No action needed.
- **Evidence**: `dvc/env.py`, `dvc/config.py`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity RISK-SAFETY, but surface-flag calibration: has_write_operations=false AND has_http_rpc_surface=false → INFO. Archetype: stateless-utility → INFO.
- **Finding**: System exposes no write operations — compensation logic is not applicable. DVC write operations (push, add) are user-initiated CLI commands, not agent-callable endpoints. DVC does provide Git-based rollback for data versioning (via `git checkout` + `dvc checkout`), but this is version control, not transactional compensation.
- **Gap**: N/A
- **Recommendation**: No action needed.
- **Evidence**: `dvc/api/__init__.py`, `dvc/data_cloud.py`

#### STATE-Q2: Queryable Current State
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`. DVC has no persistent state to query. Note: DVC does provide `dvc status` and `dvc.api.exp_show()` for querying DVC pipeline/experiment state, but these are CLI/library features, not a stateful service query surface.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator).
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: DVC implements CLI-level file locking via `dvc/lock.py` using `zc.lockfile` (with retry logic, `DEFAULT_TIMEOUT=3` seconds, configurable wait) and `flufl.lock` for hardlink-based locking. Read-write locking via `dvc/rwlock.py` prevents concurrent CLI commands from corrupting local state — tracks reader/writer PIDs per file path with JSON-based lock file schema. These are robust for CLI-level serialization. Read-only scope means write concurrency is informational.
- **Gap**: N/A for read-only scope.
- **Recommendation**: No action needed.
- **Evidence**: `dvc/lock.py`, `dvc/rwlock.py`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`. While DVC calls external storage services (S3, GCS, Azure), the dev-library-application override means resilience for external calls is a consumer concern. DVC's storage interactions use `dvc-data` and `dvc-objects` libraries which handle retries internally.
- **Trigger**: Service has external dependencies (calls other services or external APIs).
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: INFO
- **Finding**: System exposes no HTTP/RPC surface — API-layer rate limiting is not applicable. `has_http_rpc_surface` is `false`. Archetype: stateless-utility without a persistent API surface → INFO.
- **Gap**: N/A
- **Recommendation**: No action needed.
- **Evidence**: No HTTP server or API Gateway configuration found.

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Read-only agents cannot modify records, trigger spend, or delete data. Transaction limits for write operations are informational only — relevant for future scope expansion planning.
- **Gap**: N/A for read-only scope.
- **Recommendation**: No action needed.
- **Evidence**: N/A

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Priority is P2, not P0. DVC is not on a critical path — it is a development-time tool, not a production service.
- **Trigger**: Service is P0 priority OR is on the critical path.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`. Trigger requires write-enabled scope.
- **Trigger**: agent_scope is write-enabled.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q2: Configurable Approval Gates
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`. Trigger requires write-enabled scope.
- **Trigger**: agent_scope is write-enabled.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: INFO
- **Finding**: Library/utility — `has_http_rpc_surface` is `false` AND `has_persistent_data_store` is `false` → INFO. DVC has extensive test infrastructure: `tests/docker-compose.yml` (Git server for SSH integration tests), comprehensive unit tests (`tests/unit/`), functional tests (`tests/func/`), integration tests (`tests/integration/`), and benchmarks (`dvc/testing/benchmarks/`). The CI runs tests on 3 OS platforms across 6 Python versions. However, these serve DVC development, not agent testing.
- **Gap**: No sandbox environment specifically for agent testing against DVC.
- **Recommendation**: Create a test DVC remote (e.g., dedicated S3 bucket) for agent testing at the orchestration layer.
- **Evidence**: `tests/docker-compose.yml`, `tests/` directory, `.github/workflows/tests.yaml`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO
- **Finding**: Dev-library-application override applied — skip to INFO. DVC does not own user data. It is a version control tool for ML data and models that belong to the user's project. The data sensitivity classification belongs to the ML project, not DVC. DVC manages pointers (`.dvc` files with hashes) to data stored in user-configured remote storage.
- **Gap**: N/A — DVC is not a data-handling target.
- **Recommendation**: No action needed.
- **Evidence**: `dvc/api/__init__.py`, `dvc/data_cloud.py`, `dvc/schema.py`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity RISK-SAFETY, but surface-flag calibration: has_persistent_data_store=false AND has_logging_of_user_data=false → INFO. Archetype: stateless-utility → INFO.
- **Finding**: No persistent data store and no user-data logging — residency requirements do not apply. Data managed by DVC resides in user-configured remote storage (S3 buckets in specific regions, GCS, Azure Blob). Residency configuration is the user's responsibility at the storage provider level.
- **Gap**: N/A
- **Recommendation**: No action needed within DVC.
- **Evidence**: `dvc/data_cloud.py`, `dvc/config.py`

#### DATA-Q3: Selective Query Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`. DVC has no HTTP list/query endpoints with potentially unbounded results.
- **Trigger**: Service has list/query endpoints with potentially unbounded results.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q4: System of Record Designations
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility` — no persistent state. DVC itself acts as the system of record for data version metadata (via `.dvc` files and `dvc.lock`), but this is a version control function, not a stateful-crud data ownership pattern.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway).
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: INFO
- **Finding**: Archetype calibration: stateless-utility → INFO. DVC tracks data versions via Git commits (which have timestamps) and `.dvc` file hashes. Data freshness is determined by the Git history and `dvc.lock` file state. No HTTP `Cache-Control` headers, `X-Data-Age` headers, or freshness signaling exists — these are not applicable for a CLI/library tool.
- **Gap**: N/A for stateless-utility with static/reference data characteristics.
- **Recommendation**: No action needed.
- **Evidence**: `dvc/schema.py` (CHECKSUMS_SCHEMA), `dvc/dvcfile.py`

#### DATA-Q6: PII Redaction in Logs
- **Severity**: INFO
- **Finding**: `has_logging_of_user_data` is `false` AND `has_persistent_data_store` is `false` — PII-in-logs risk is not applicable. Archetype: stateless-utility → INFO. DVC's logging (`dvc/logger.py`) outputs diagnostic messages about DVC operations. The analytics module (`dvc/analytics.py`) sends anonymized telemetry: `cmd_class`, `cmd_return_code`, `dvc_version`, `system_info`, anonymous `user_id`, `remotes` (type only), `git_remote_hash` (MD5 hash, not raw URL). No user PII is logged or transmitted.
- **Gap**: N/A
- **Recommendation**: No action needed.
- **Evidence**: `dvc/logger.py`, `dvc/analytics.py`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: DVC provides data integrity via content-addressable storage (hash-based deduplication and verification with `md5`, `sha256`). Files are tracked by hash, enabling verification on checkout/pull. No data quality scoring, completeness metrics, or freshness SLAs exist — these are properties of user's ML data, not DVC.
- **Gap**: N/A — DVC provides integrity, not quality guarantees.
- **Recommendation**: No action needed.
- **Evidence**: `dvc/data_cloud.py`, `dvc/schema.py`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: DVC uses `setuptools_scm` for semantic versioning (configured in `pyproject.toml`). The public Python API is defined in `dvc/api/__init__.py` with a clear `__all__` export list of 13 functions. Mypy type-checking is enforced in CI (`pre-commit-config.yaml`). However, there is no automated breaking-change detection for the public `dvc.api` module. The CI pipeline runs comprehensive tests but does not include consumer-driven contract tests (Pact), API diff tooling, or symbol/signature regression checks. No `/v1/`, `/v2/` URL patterns (no HTTP APIs). No `Accept-Version` headers. No schema comparison tools.
- **Gap**: No automated breaking-change detection or consumer-driven contract testing for the public `dvc.api` Python interface. Agent tool bindings wrapping these functions could break silently on DVC version upgrades.
- **Recommendation**: Add API surface regression tests — snapshot the `dvc.api.__all__` exports and function signatures, compare against previous releases in CI. Consider Pact-style contract tests for critical agent tool integrations.
- **Evidence**: `pyproject.toml` (setuptools_scm), `dvc/api/__init__.py`, `.github/workflows/tests.yaml`, `.pre-commit-config.yaml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: DVC uses clear, semantically meaningful names throughout. Python API function names (`metrics_show`, `params_show`, `exp_show`, `exp_save`, `get_url`, `get_dataset`) and parameter names (`repo`, `rev`, `remote`, `mode`, `encoding`, `force`, `num`, `param_deps`, `include_untracked`) are self-explanatory. Schema field names in `dvc/schema.py` use readable constants: `StageParams.PARAM_CMD`, `StageParams.PARAM_DEPS`, `StageParams.PARAM_OUTS`, `StageParams.PARAM_FROZEN`. No legacy abbreviations or opaque codes found.
- **Gap**: N/A
- **Recommendation**: No action needed. DVC's naming conventions are excellent for agent tool definition.
- **Evidence**: `dvc/api/__init__.py`, `dvc/api/data.py`, `dvc/api/show.py`, `dvc/api/experiments.py`, `dvc/schema.py`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: DVC itself functions as a lightweight data catalog for ML projects. It tracks datasets, models, experiments, and pipelines with metadata stored in `.dvc` files, `dvc.yaml`, and `dvc.lock`. The `dvc.api` module provides programmatic access: `params_show()` returns parameter metadata, `metrics_show()` returns metric metadata, `exp_show()` returns experiment metadata with all tracked metrics/params. No external data catalog (Glue, Collibra, DataHub) integration exists, but DVC is the catalog for its own domain.
- **Gap**: N/A — DVC is the data catalog for its managed files.
- **Recommendation**: No action needed. Agents can use `dvc.api` to discover tracked data.
- **Evidence**: `dvc/api/__init__.py`, `dvc/schema.py`, `dvc/dvcfile.py`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: INFO
- **Finding**: Library/utility — `has_http_rpc_surface` is `false` — tracing and correlation are consumer concerns. DVC does not implement distributed tracing (no OpenTelemetry SDK, no X-Ray instrumentation, no `traceparent` header propagation). Logging (`dvc/logger.py`) uses Python's standard `logging` module with custom levels: TRACE (below DEBUG), DEBUG, INFO, WARNING, ERROR. Output is human-readable colored text via `ColorFormatter`, not structured JSON. No correlation IDs or request tracing. The library's obligation is to propagate trace context if provided — DVC does not currently do this.
- **Gap**: No structured JSON logging, no trace propagation. Expected for a CLI tool.
- **Recommendation**: No action needed.
- **Evidence**: `dvc/logger.py`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: INFO
- **Finding**: Library/utility — `has_http_rpc_surface` is `false` — alerting is a consumer concern. No CloudWatch alarms, anomaly detection, PagerDuty/OpsGenie integration, or SLO-based alerting exists. DVC CI has Slack notifications on main branch test failures (via `rtCamp/action-slack-notify` in `tests.yaml`), but this is CI alerting, not runtime alerting.
- **Gap**: N/A — libraries expose error signals via return values and exceptions; consumers set alert thresholds.
- **Recommendation**: No action needed.
- **Evidence**: `.github/workflows/tests.yaml` (Slack notification for CI failures)

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: DVC sends anonymous usage analytics to `analytics.dvc.org` via `dvc/analytics.py`. The report includes: `cmd_class` (which command was run), `cmd_return_code`, `dvc_version`, `is_binary`, `scm_class`, `system_info` (OS, version), `user_id` (anonymous telemetry ID via `iterative_telemetry`), `group_id` (CI ID), `remotes` (remote types configured), `git_remote_hash` (MD5 of Git remote path). This is product telemetry for DVC's maintainers, not business outcome metrics. Analytics can be disabled via `DVC_NO_ANALYTICS` env var or `core.analytics=false` config.
- **Gap**: No business KPI metrics or dashboards. Expected for a CLI tool.
- **Recommendation**: No action needed.
- **Evidence**: `dvc/analytics.py`, `dvc/env.py` (DVC_NO_ANALYTICS)

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: INFO
- **Finding**: Library/utility — `has_http_rpc_surface` is `false` AND `has_auth_surface` is `false` → INFO. No Terraform, CloudFormation, CDK, Helm, Kustomize, or Ansible files found. DVC is distributed as a Python package via PyPI — there is no infrastructure to govern. The build/release pipeline (`build.yaml`) uses GitHub Actions with OIDC-based PyPI publishing (Trusted Publishers).
- **Gap**: N/A — CLI/library tools don't own infrastructure.
- **Recommendation**: No action needed.
- **Evidence**: No IaC files found. `.github/workflows/build.yaml` (PyPI publishing)

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: INFO
- **Finding**: `has_http_rpc_surface` is `false` — API contract testing is not applicable. DVC has a mature CI/CD pipeline: **tests.yaml** — multi-OS (Ubuntu, macOS, Windows), multi-Python (3.9–3.14) test matrix with pytest, parallel execution (`-n=logical --dist=worksteal`), 300s timeout, coverage reporting, Codecov upload. **build.yaml** — package build with `uv build`, twine check, Test PyPI + PyPI publish via OIDC. **codeql.yml** — CodeQL security analysis with `security-extended` queries. **plugin_tests.yaml** — cross-repo compatibility testing with `dvc-s3` plugin. **Pre-commit hooks** — ruff linting/formatting, codespell, mypy type-checking. **Dependabot** — daily pip and GitHub Actions dependency updates. Library contract stability is evaluated by DISC-Q1.
- **Gap**: No HTTP API contract testing (none needed).
- **Recommendation**: See DISC-Q1 for Python API stability recommendation.
- **Evidence**: `.github/workflows/tests.yaml`, `.github/workflows/build.yaml`, `.github/workflows/codeql.yml`, `.github/workflows/plugin_tests.yaml`, `.pre-commit-config.yaml`, `.github/codecov.yml`, `.github/dependabot.yml`

#### ENG-Q3: Rollback Capability
- **Severity**: INFO
- **Finding**: `has_http_rpc_surface` is `false` — deployment rollback is a consumer concern. DVC is distributed via PyPI. Rollback = consumer version pinning (`pip install dvc==X.Y.Z`). The release process: GitHub release event triggers `build.yaml` → builds package → publishes to PyPI via OIDC. Test PyPI uploads on main branch pushes provide pre-release validation. Previous versions remain available on PyPI indefinitely.
- **Gap**: N/A — library rollback is version pinning.
- **Recommendation**: No action needed.
- **Evidence**: `.github/workflows/build.yaml`

#### ENG-Q4: API Test Coverage
- **Severity**: INFO
- **Finding**: INFO for stateless-utility archetype. DVC has an extensive test suite: **Unit tests** (`tests/unit/`) — CLI commands, config, filesystem, output, repo operations, stage processing, utilities. **Functional tests** (`tests/func/`) — API tests (`tests/func/api/test_data.py`, `test_experiments.py`, `test_show.py`, `test_artifacts.py`, `test_scm.py`), data cloud operations, experiments, metrics, params, plots, parsing, repro. **Integration tests** (`tests/integration/`) — Studio live experiments, plots. **Benchmarks** (`dvc/testing/benchmarks/`) — CLI command benchmarks. CI configuration: `pytest-xdist` for parallel execution, `pytest-cov` for coverage (with branch coverage), `pytest-timeout` for hanging test detection, `pytest-rerunfailures` for flaky test handling, `pytest-mock` for test doubles, `pytest-docker` for container-based tests. Markers include `needs_internet`, `studio`, `vscode` for contract verification with external systems.
- **Gap**: N/A for stateless-utility.
- **Recommendation**: No action needed.
- **Evidence**: `tests/func/api/`, `tests/unit/`, `tests/integration/`, `.github/workflows/tests.yaml`, `pyproject.toml` (pytest config)

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. DVC does not own persistent data stores. Data encryption at rest is configured at the storage provider level (S3 bucket encryption, GCS encryption, Azure Blob encryption) — not within DVC.
- **Trigger**: Service has persistent data stores.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `dvc/__main__.py` | API-Q1 |
| `dvc/cli/__init__.py` | API-Q1, AUTH-Q3 |
| `dvc/api/__init__.py` | API-Q1, API-Q4, API-Q5, AUTH-Q1, DATA-Q1, DISC-Q1, DISC-Q2, DISC-Q3, STATE-Q1 |
| `dvc/api/data.py` | API-Q5, DISC-Q2 |
| `dvc/api/show.py` | API-Q5, DISC-Q2 |
| `dvc/api/experiments.py` | API-Q5, DISC-Q2 |
| `dvc/exceptions.py` | API-Q3 |
| `dvc/data_cloud.py` | AUTH-Q1, AUTH-Q2, AUTH-Q4, DATA-Q1, DATA-Q2, DATA-Q7, STATE-Q1 |
| `dvc/env.py` | AUTH-Q1, AUTH-Q5, AUTH-Q7, OBS-Q3 |
| `dvc/config.py` | AUTH-Q1, AUTH-Q5, AUTH-Q7, DATA-Q2 |
| `dvc/fs/__init__.py` | AUTH-Q2 |
| `dvc/lock.py` | STATE-Q3 |
| `dvc/rwlock.py` | STATE-Q3 |
| `dvc/logger.py` | DATA-Q6, OBS-Q1 |
| `dvc/analytics.py` | DATA-Q6, OBS-Q3 |
| `dvc/schema.py` | DATA-Q5, DATA-Q7, DISC-Q2, DISC-Q3 |
| `dvc/dvcfile.py` | DATA-Q5, DISC-Q3 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/tests.yaml` | DISC-Q1, ENG-Q2, ENG-Q4, HITL-Q3, OBS-Q2 |
| `.github/workflows/build.yaml` | ENG-Q1, ENG-Q2, ENG-Q3 |
| `.github/workflows/codeql.yml` | ENG-Q2 |
| `.github/workflows/plugin_tests.yaml` | ENG-Q2 |
| `.pre-commit-config.yaml` | DISC-Q1, ENG-Q2 |
| `.github/codecov.yml` | ENG-Q2, ENG-Q4 |
| `.github/dependabot.yml` | ENG-Q2 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `tests/docker-compose.yml` | HITL-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `pyproject.toml` | API-Q1, DISC-Q1, ENG-Q2, ENG-Q4 |
