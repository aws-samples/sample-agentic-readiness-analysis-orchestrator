# Agentic Readiness Assessment Report

**Target**: arrow (repository root)
**Date**: 2026-04-30
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**TD Version**: agentic-readiness-assessment
**Repository Type**: application
**Service Archetype**: stateless-utility (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: python, library
**Context**: Python library for human-friendly date and time handling.

**Archetype Justification**: Arrow is a pure Python library with no database connections, no HTTP server, no message queue consumers, no write endpoints, and no persistent state. All operations are deterministic date/time computations returning Python objects.

**Surface flags**:
- has_persistent_data_store: false
- has_http_rpc_surface: false
- has_auth_surface: false
- has_write_operations: false
- has_logging_of_user_data: false

> **INFO — Dev-Library-Application Override Applied**: This repository has `repo_type=application` and `service_archetype=stateless-utility`, with all 5 surface flags `false` (≥3 required). Per Step 1.5, the library N/A mapping is applied for scoring purposes. The original `repo_type` value (`application`) is preserved above. This override reflects the fact that Arrow is a computational library — it exposes no HTTP surface, holds no data, enforces no auth, performs no write operations, and logs no user data. Questions that evaluate infrastructure, deployment, or runtime controls are downgraded to INFO because those concerns belong to the consuming applications, not the library itself.

---

## Readiness Profile: Agent-Ready

**BLOCKERs**: 0 | **RISK-SAFETY**: 0 | **RISK-QUALITY**: 1 | **INFOs**: 31

Cleared for autonomous operation. Instrument observability. Define scope explicitly. Run controlled pilot first.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 0 |
| RISK-SAFETY | 0 |
| RISK-QUALITY | 1 |
| INFO | 31 |
| N/A | 0 |
| Not Evaluated (extended) | 11 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 8 (API-Q5, API-Q8, STATE-Q3, DATA-Q7, DISC-Q2, DISC-Q3, OBS-Q3, ENG-Q4 — all INFO)
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

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Arrow uses semantic versioning (`__version__ = "1.4.0"` in `arrow/_version.py`) and maintains a detailed `CHANGELOG.rst` with categorized entries ([ADDED], [CHANGED], [FIXED], [INTERNAL]). The library ships a `py.typed` marker file and uses comprehensive type annotations enforced by mypy in strict mode (`setup.cfg`). However, there is no automated breaking-change detection in the CI pipeline — no schema comparison tool, no consumer-driven contract tests (e.g., Pact), and no automated validation that the public API surface (`arrow/__init__.py` `__all__` exports) has not changed unexpectedly between versions.
- **Gap**: No automated breaking-change detection in CI. Breaking changes to the public API (e.g., removing an export from `__all__`, changing a function signature, altering error types) would not be caught until downstream consumers upgrade.
- **Compensating Controls**:
  - The strict mypy configuration and comprehensive test suite (99%+ coverage threshold) reduce the likelihood of accidental signature changes.
  - The `CHANGELOG.rst` documents breaking changes manually (e.g., "Dropped support for Python 3.6 and 3.7" in 1.3.0).
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a CI step that compares the public API surface (`__all__` exports, function signatures) against the previous release. Tools like `griffe` (Python API diff) or custom scripts comparing exported symbols can automate this. Consider adopting consumer-driven contract tests if downstream agent-tool integrations are planned.
- **Evidence**: `arrow/_version.py`, `CHANGELOG.rst`, `arrow/__init__.py` (`__all__`), `setup.cfg` (mypy config), `.pre-commit-config.yaml` (mypy hook), `tox.ini` (`--cov-fail-under=99`)

---

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO
- **Finding**: Arrow exposes a well-documented Python API (not HTTP). The library provides `arrow.get()`, `arrow.now()`, `arrow.utcnow()` as module-level functions, and the `Arrow` class with rich methods (`shift()`, `format()`, `humanize()`, `to()`, `span()`, `range()`). All functions have docstrings with usage examples. The `docs/api-guide.rst` auto-generates API documentation via Sphinx `automodule`. ReadTheDocs hosts the full documentation at `arrow.readthedocs.io`.
- **Implication**: Agents consuming Arrow do so via Python import, not HTTP — the "documented interface" is the Python API, which is comprehensively documented. An MCP server wrapping Arrow would need to define tool schemas from the Python function signatures. The type-annotated API (`py.typed` marker + mypy strict) makes automated tool generation straightforward.
- **Recommendation**: No action required. The Python API is well-documented and type-annotated. For agent tool generation, the typed signatures in `arrow/api.py` and `arrow/arrow.py` serve as the machine-readable contract.
- **Evidence**: `arrow/api.py`, `arrow/arrow.py`, `arrow/__init__.py`, `docs/api-guide.rst`, `README.rst`

### API-Q2: Machine-Readable API Specification

- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — machine-readable spec is not applicable. Arrow is a Python library consumed via `import arrow`. The library equivalent of a machine-readable spec is its typed exports: `py.typed` marker, comprehensive type annotations enforced by mypy strict mode, and `__all__` export lists in `arrow/__init__.py` and submodules.
- **Implication**: Agent tool definitions would be generated from Python function signatures and type hints, not from an OpenAPI spec. This is the expected pattern for library integration.
- **Recommendation**: No action required.
- **Evidence**: `arrow/py.typed`, `arrow/__init__.py`, `setup.cfg` (mypy config)

### API-Q3: Structured Error Responses

- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — structured error responses are not applicable. Arrow communicates errors via Python's native exception hierarchy: `ParserError` (inherits `ValueError`) for parsing failures, `ParserMatchError` (inherits `ParserError`) for format matching failures, `TypeError` for invalid argument types, and `ValueError` for out-of-range inputs. Error messages are descriptive and include the invalid input value.
- **Implication**: Agent tool wrappers would catch specific exception types to distinguish error categories — this is the library-native equivalent of structured error codes.
- **Recommendation**: No action required. The exception hierarchy is well-structured.
- **Evidence**: `arrow/parser.py` (`ParserError`, `ParserMatchError`), `arrow/arrow.py` (ValueError, TypeError raises), `arrow/util.py` (validation errors)

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Arrow is a pure computation library with no write operations. All operations return new `Arrow` objects — there are no state-mutating endpoints. The `shift()`, `replace()`, `to()` methods all return new instances (immutable pattern). No database writes, no file writes, no side effects.
- **Implication**: Idempotency is inherently satisfied — calling `arrow.get('2024-01-01')` returns the same result every time. No agent retry risk.
- **Recommendation**: No action required.
- **Evidence**: `arrow/arrow.py` (all methods return new Arrow instances), `arrow/api.py`

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: Arrow returns native Python objects (`Arrow` instances, `datetime` objects, `str` from `format()`, `float` from `timestamp()`). These are inherently structured and serializable — `Arrow.__repr__()` produces `<Arrow [2013-05-05T12:30:45+00:00]>`, `for_json()` produces ISO 8601 strings, and `isoformat()` produces standard datetime strings. The `simplejson` protocol is supported via `for_json()`.
- **Implication**: For agent consumption, Arrow's output is easily serializable to JSON. MCP tool responses would serialize Arrow objects to ISO 8601 strings.
- **Recommendation**: No action required.
- **Evidence**: `arrow/arrow.py` (`__repr__`, `__str__`, `for_json`, `isoformat` methods)

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — API rate limits are not applicable. Arrow is a computation library with no network calls. There are no rate limits to document or headers to return.
- **Implication**: Rate limiting for agent access to Arrow's functionality would be handled at the MCP server or agent orchestration layer, not within the library.
- **Recommendation**: No action required.
- **Evidence**: `arrow/api.py`, `arrow/arrow.py` (no network calls), `requirements/requirements.txt` (no HTTP client dependencies)

### AUTH-Q1: Machine Identity Authentication

- **Severity**: INFO
- **Finding**: Arrow is a computation library with no auth surface. It does not authenticate callers, issue tokens, or validate credentials. The library exposes pure Python functions that perform date/time computations — there is no concept of a "caller" or "principal" at the library level. Authentication is the responsibility of consuming applications.
- **Implication**: When an agent consumes Arrow (e.g., via an MCP tool), authentication is enforced at the MCP server or application layer, not by the library. This is the expected architecture for library integration.
- **Recommendation**: No action required. Consuming applications must implement their own machine identity authentication.
- **Evidence**: `arrow/api.py`, `arrow/arrow.py`, `arrow/factory.py` (no auth imports, no token validation, no credential handling)

### AUTH-Q2: Scoped Permissions (Least Privilege)

- **Severity**: INFO
- **Finding**: Arrow has no authorization model — all functions are publicly accessible to any Python caller. This is appropriate for a computation library that performs no sensitive operations. There are no IAM policies, no role definitions, and no permission checks because the library has no resources to protect.
- **Implication**: Scoped permissions for agent access to Arrow's functionality would be implemented at the MCP server or agent orchestration layer.
- **Recommendation**: No action required.
- **Evidence**: `arrow/__init__.py` (`__all__` exports all public symbols without access restrictions)

### AUTH-Q3: Action-Level Authorization

- **Severity**: INFO
- **Finding**: No action-level authorization exists or is needed. Arrow functions are pure computations — there is no distinction between "read" and "write" actions because no operations modify persistent state. All Arrow methods return new objects without side effects.
- **Implication**: Action-level authorization for agent use would be handled at the tool definition layer (e.g., exposing only `arrow.get` and `arrow.format` tools, not `arrow.shift`).
- **Recommendation**: No action required.
- **Evidence**: `arrow/arrow.py` (immutable pattern — `shift()`, `replace()`, `to()` return new instances)

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: INFO
- **Finding**: Arrow does not propagate identity — it has no concept of caller identity, tokens, or delegation. The library receives Python arguments and returns Python objects. There is no JWT parsing, no OAuth flow, no user context.
- **Implication**: Identity propagation would be handled at the application layer consuming Arrow. The library is not a participant in the identity chain.
- **Recommendation**: No action required.
- **Evidence**: `arrow/api.py`, `arrow/factory.py` (no auth-related imports or parameters)

### AUTH-Q5: Credential Management

- **Severity**: INFO
- **Finding**: Arrow manages no credentials. The library has no API keys, no database connection strings, no secrets. The only credentials in the repository are CI/CD secrets (`PYPI_API_TOKEN`, `CODECOV_TOKEN`) referenced as GitHub Actions secrets — these are stored in GitHub's encrypted secrets store, not in the codebase. No `.env` files are committed. No hardcoded credentials were found.
- **Implication**: No credential management concerns for agent integration.
- **Recommendation**: No action required. CI/CD secrets are properly managed via GitHub Actions secrets.
- **Evidence**: `.github/workflows/release.yml` (`secrets.PYPI_API_TOKEN`), `.github/workflows/continuous_integration.yml` (`secrets.CODECOV_TOKEN`), `.gitignore` (no `.env` files committed)

### AUTH-Q6: Immutable Audit Logging ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY, then downgraded to INFO via surface-flag calibration
- **Finding**: System does not execute agent-invoked write operations — audit logging is a consumer responsibility. The library/utility is called by applications that own the audit context. Arrow has no logging, no CloudTrail integration, no audit trail — because it is a computation library that performs no operations requiring audit.
- **Implication**: Audit logging for agent interactions with Arrow would be implemented at the MCP server or application layer.
- **Recommendation**: No action required.
- **Evidence**: `arrow/` (no logging imports, no audit trail code across all source files)

### AUTH-Q7: Agent Identity Suspension

- **Severity**: INFO
- **Finding**: System does not issue or enforce agent identities — suspension is a consumer responsibility. Libraries and utilities are invoked by applications that own identity lifecycle. Arrow has no concept of agent identities, API keys, or service accounts.
- **Implication**: Agent identity suspension would be implemented at the platform layer (API Gateway, MCP server, IAM).
- **Recommendation**: No action required.
- **Evidence**: `arrow/` (no identity management code)

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY, then downgraded to INFO via surface-flag calibration
- **Finding**: System exposes no write operations — compensation logic is not applicable. Arrow is a pure computation library. All operations return new `Arrow` objects without modifying any persistent state. There are no multi-step write sequences to roll back.
- **Implication**: No compensation or rollback capability is needed for a stateless computation library.
- **Recommendation**: No action required.
- **Evidence**: `arrow/arrow.py` (immutable object pattern), `arrow/api.py` (stateless factory functions)

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Arrow has no write operations, so concurrency controls for write operations are not applicable. The library's functions are pure — they accept arguments and return new objects without shared mutable state. Multiple concurrent callers produce independent results without interference.
- **Implication**: Arrow is inherently safe for concurrent agent use.
- **Recommendation**: No action required.
- **Evidence**: `arrow/arrow.py` (no shared mutable state, no class-level write operations)

### STATE-Q5: Rate Limiting and Throttling

- **Severity**: INFO
- **Finding**: System exposes no HTTP/RPC surface — API-layer rate limiting is not applicable. Arrow is a computation library invoked via Python import. Libraries invoked by consuming applications inherit the consumer's rate limiting, not their own.
- **Implication**: Rate limiting for agent consumption of Arrow would be implemented at the MCP server or API Gateway layer.
- **Recommendation**: No action required.
- **Evidence**: `arrow/api.py` (no network server), `requirements/requirements.txt` (no HTTP server dependencies)

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Read-only agents cannot modify records, trigger spend, or delete data. Arrow performs only computation — there are no transactions, no record modifications, no spend-incurring operations. Transaction limits are not applicable.
- **Implication**: Blast radius for Arrow operations is inherently zero — the worst case is a computation returning an incorrect date/time, which has no persistent effect.
- **Recommendation**: No action required.
- **Evidence**: `arrow/arrow.py` (no persistent state mutations)

### HITL-Q3: Sandbox/Staging Environment

- **Severity**: INFO
- **Finding**: Arrow has no deployed HTTP surface or persistent data store — staging environments are a consumer concern. However, the library provides excellent local testing capabilities: `tox` for multi-version testing, `docker-compose` is not needed (pure Python), and consumers can `pip install arrow` in any virtual environment for testing. The CI pipeline (`continuous_integration.yml`) tests across 8 Python versions and 3 operating systems.
- **Implication**: Agents consuming Arrow can test in any Python environment. No staging infrastructure is needed for a computation library.
- **Recommendation**: No action required.
- **Evidence**: `tox.ini`, `.github/workflows/continuous_integration.yml`

### DATA-Q1: Sensitive Data Classification

- **Severity**: INFO
- **Finding**: Not a data-handling target — no PII/PHI/financial/credential data is stored, processed, or logged. Arrow is a date/time computation library. It receives datetime strings, timestamps, and timezone identifiers as input and returns `Arrow` objects. None of these inputs or outputs constitute sensitive data. The library has no database, no file storage, no user data model.
- **Implication**: No data classification controls are needed.
- **Recommendation**: No action required.
- **Evidence**: `arrow/api.py`, `arrow/factory.py`, `arrow/arrow.py` (function signatures accept datetime/string/int, no user-specific fields)

### DATA-Q2: Data Residency and Sovereignty ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY, then downgraded to INFO via surface-flag calibration
- **Finding**: No persistent data store and no user-data logging — residency requirements do not apply. Arrow holds no data. It is a pure computation library that processes datetime values in-memory and returns results. No data crosses network boundaries.
- **Implication**: Data residency is a non-concern for Arrow itself. The consuming application is responsible for data residency of any datetime values it processes.
- **Recommendation**: No action required.
- **Evidence**: `requirements/requirements.txt` (no database drivers, no storage SDKs)

### DATA-Q6: PII Redaction in Logs

- **Severity**: INFO
- **Finding**: System does not log user data and holds no user data — PII-in-logs risk is not applicable. Arrow has no logging statements in its source code. The library outputs no log files, emits no telemetry, and has no observability pipeline. The `print()` function is not called anywhere in the library code.
- **Implication**: No PII leakage risk from the library itself. Consuming applications must ensure they do not log sensitive datetime values if those values are derived from PII (e.g., birth dates).
- **Recommendation**: No action required.
- **Evidence**: `arrow/` (no `logging` imports, no `print()` calls in library code)

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality metrics applicable to a computation library. Arrow does not own or manage datasets. It processes individual datetime values deterministically. Data quality is a property of the inputs provided by the caller.
- **Implication**: Data quality awareness for agent consumption of Arrow is a concern of the upstream data source, not the library.
- **Recommendation**: No action required.
- **Evidence**: `arrow/factory.py` (validates inputs but does not track quality metrics)

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Arrow uses clear, Pythonic naming conventions throughout. Class names are descriptive: `Arrow`, `ArrowFactory`, `DateTimeParser`, `DateTimeFormatter`, `TzinfoParser`, `ParserError`, `ParserMatchError`. Method names follow Python conventions: `humanize()`, `dehumanize()`, `shift()`, `replace()`, `format()`, `to()`, `span()`, `range()`. Constants use UPPER_SNAKE_CASE: `DEFAULT_LOCALE`, `MAX_TIMESTAMP`, `FORMAT_RFC3339`. No legacy abbreviations or cryptic codes found.
- **Implication**: Agent tool definitions derived from Arrow's API will have self-documenting parameter and method names — no data dictionary required.
- **Recommendation**: No action required. Naming quality is excellent.
- **Evidence**: `arrow/arrow.py` (class/method names), `arrow/constants.py` (constant names), `arrow/parser.py` (ParserError, DateTimeParser), `arrow/formatter.py` (DateTimeFormatter)

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: Arrow provides comprehensive documentation via ReadTheDocs (`arrow.readthedocs.io`), configured in `.readthedocs.yaml`. The Sphinx documentation auto-generates API reference from docstrings (`docs/api-guide.rst` using `automodule`). The `README.rst` provides quick-start examples. `CHANGELOG.rst` provides a detailed release history. No formal data catalog exists, but the library's metadata layer (docstrings, type hints, Sphinx docs) serves the same purpose for agent tool discovery.
- **Implication**: Agent developers can reference ReadTheDocs and the typed API to build tool definitions. The auto-generated API reference from Sphinx serves as the authoritative metadata layer.
- **Recommendation**: No action required.
- **Evidence**: `.readthedocs.yaml`, `docs/api-guide.rst`, `docs/index.rst`, `README.rst`, `CHANGELOG.rst`

### OBS-Q1: Distributed Tracing and Structured Logging

- **Severity**: INFO
- **Finding**: Library/utility — tracing and correlation are consumer concerns. Arrow has no telemetry, no OpenTelemetry SDK, no X-Ray instrumentation, no logging framework. This is appropriate for a pure Python computation library. The library's obligation is to propagate trace context if provided — Arrow does not make network calls, so there is no trace context to propagate.
- **Implication**: Consuming applications that wrap Arrow in MCP tools should instrument the tool wrapper, not Arrow itself.
- **Recommendation**: No action required.
- **Evidence**: `requirements/requirements.txt` (no telemetry dependencies), `arrow/` (no logging or tracing imports)

### OBS-Q2: Alerting on Error Rates and Latency

- **Severity**: INFO
- **Finding**: Library/utility — alerting on error rates and latency is a consumer concern. Arrow exposes no deployed API surface. Libraries expose error and timing signals via return values, exceptions, or structured metrics; consumers decide the alert thresholds.
- **Implication**: Alert thresholds for Arrow-wrapped MCP tools should be configured at the MCP server or application layer.
- **Recommendation**: No action required.
- **Evidence**: `arrow/` (no alerting configuration), `requirements/requirements.txt` (no monitoring dependencies)

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No business outcome metrics applicable to a computation library. Arrow does not track resolution rates, conversion, or satisfaction — these are application-level concerns. The library computes datetime values deterministically.
- **Implication**: Business outcome metrics for agent interactions involving Arrow would be tracked at the application or agent orchestration layer.
- **Recommendation**: No action required.
- **Evidence**: `arrow/` (no metrics publishing code)

### ENG-Q1: Infrastructure Governance for Agent-Facing Surface

- **Severity**: INFO
- **Finding**: Arrow does not own IaC for API gateways, IAM roles, or networking. It is a Python library published to PyPI. The library has no Terraform, CloudFormation, CDK, or Kubernetes configurations. The only infrastructure is the GitHub Actions CI/CD pipeline, which is defined as code (`.github/workflows/*.yml`). PR review is enforced by GitHub's branch protection (the CI runs on all pull requests per `continuous_integration.yml`).
- **Implication**: Infrastructure governance for agent-facing surfaces would be defined by the consuming application's IaC, not by the library.
- **Recommendation**: No action required.
- **Evidence**: `.github/workflows/continuous_integration.yml`, `.github/workflows/release.yml` (CI/CD as code)

### ENG-Q2: CI/CD with API Contract Testing

- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — API contract testing is not applicable. Library contract stability is evaluated by DISC-Q1. However, Arrow has an excellent CI/CD pipeline: GitHub Actions runs `tox` across 8 Python versions (3.8–3.14 + PyPy) on 3 operating systems (Ubuntu, macOS, Windows). Pre-commit hooks enforce code quality (flake8, black, isort, mypy, pyupgrade). Linting and documentation are tested in CI. Codecov integration tracks coverage.
- **Implication**: The CI pipeline catches regressions but does not specifically detect breaking changes to the public API surface (see DISC-Q1 RISK-QUALITY finding).
- **Recommendation**: See DISC-Q1 recommendation for adding automated API surface comparison.
- **Evidence**: `.github/workflows/continuous_integration.yml`, `tox.ini`, `.pre-commit-config.yaml`

### ENG-Q3: Rollback Capability

- **Severity**: INFO
- **Finding**: No deployed HTTP/RPC surface — deployment rollback is a consumer concern. Library rollback is handled via package version pinning by consumers (`pip install arrow==1.3.0`). The release pipeline (`.github/workflows/release.yml`) publishes to PyPI via `flit publish` on tag push. PyPI supports version-specific installation, enabling consumers to pin or roll back to any published version.
- **Implication**: Consumers control their Arrow version via dependency pinning. No deployment rollback mechanism is needed within the library.
- **Recommendation**: No action required. Consider adding a PyPI "yank" procedure documentation for emergency releases.
- **Evidence**: `.github/workflows/release.yml`, `pyproject.toml` (flit build system), `arrow/_version.py`

### ENG-Q4: API Test Coverage

- **Severity**: INFO
- **Finding**: Arrow has exemplary test coverage for a stateless-utility library. The pytest configuration enforces `--cov-fail-under=99` (99% minimum branch coverage). The test suite spans 9,168+ lines across 8 test files: `test_arrow.py` (3,100 lines), `test_parser.py` (1,608 lines), `test_locales.py` (3,785 lines), `test_factory.py` (396 lines), `test_formatter.py` (279 lines), plus `test_api.py`, `test_util.py`, and `conftest.py`. Tests cover input validation, error handling, edge cases (DST transitions, leap years, timestamp boundaries), and locale support.
- **Implication**: The test suite provides high confidence that Arrow's behavior is well-specified and regression-resistant. Agent tool definitions based on Arrow's API can rely on stable, well-tested behavior.
- **Recommendation**: No action required. Test coverage is excellent.
- **Evidence**: `tox.ini` (`--cov-fail-under=99`), `tests/test_arrow.py`, `tests/test_parser.py`, `tests/test_factory.py`, `tests/test_formatter.py`, `tests/test_locales.py`

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: Arrow exposes a well-documented Python API via `import arrow`. Module-level functions (`get()`, `now()`, `utcnow()`) and the `Arrow` class with rich methods (`shift()`, `format()`, `humanize()`, `to()`, `span()`, `range()`) are fully documented with docstrings and usage examples. The library has no HTTP/REST/GraphQL interface — it is consumed as a Python import. The `docs/api-guide.rst` auto-generates Sphinx documentation. ReadTheDocs hosts the full documentation. The `py.typed` marker and comprehensive type annotations (enforced by mypy strict mode) provide machine-readable interface metadata. The dev-library-application override recognizes that the "API" is the Python module interface, not an HTTP surface.
- **Gap**: No HTTP API exists; this is by design for a library. The Python API is the integration surface.
- **Recommendation**: No action required. For MCP tool generation, use the typed function signatures from `arrow/api.py` and `arrow/arrow.py`.
- **Evidence**: `arrow/api.py`, `arrow/arrow.py`, `arrow/__init__.py`, `docs/api-guide.rst`, `README.rst`, `arrow/py.typed`

#### API-Q2: Machine-Readable API Specification
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — machine-readable spec is not applicable. The library equivalent is its typed exports: `py.typed` marker, comprehensive type annotations enforced by mypy strict mode, and `__all__` export lists. For libraries, API contracts are expressed via package manifests and typed exports, not as OpenAPI specs.
- **Gap**: N/A — not applicable for a library without HTTP surface.
- **Recommendation**: No action required.
- **Evidence**: `arrow/py.typed`, `arrow/__init__.py`, `setup.cfg` (mypy config)

#### API-Q3: Structured Error Responses
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — structured error responses are not applicable. Arrow communicates errors via Python exceptions: `ParserError` (inherits `ValueError`), `ParserMatchError` (inherits `ParserError`), `TypeError`, and `ValueError`. Error messages include the invalid input value (e.g., `f"Failed to match {fmt!r} when parsing {datetime_string!r}."`).
- **Gap**: N/A — libraries communicate failure via exceptions, not HTTP error bodies.
- **Recommendation**: No action required.
- **Evidence**: `arrow/parser.py` (`ParserError`, `ParserMatchError`), `arrow/arrow.py`, `arrow/util.py`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Arrow has no write operations. All methods return new `Arrow` objects (immutable pattern). No database writes, no file writes, no side effects. Idempotency is inherently satisfied.
- **Gap**: None — no write operations exist.
- **Recommendation**: No action required.
- **Evidence**: `arrow/arrow.py` (`shift()`, `replace()`, `to()` all return new instances), `arrow/api.py`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: Arrow returns native Python objects: `Arrow` instances, `datetime` objects, `str` (from `format()`), `float` (from `timestamp()`). ISO 8601 output via `isoformat()` and `for_json()` (simplejson protocol). All outputs are JSON-serializable.
- **Gap**: None.
- **Recommendation**: No action required.
- **Evidence**: `arrow/arrow.py` (`__repr__`, `__str__`, `for_json`, `isoformat`)

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
- **Finding**: No HTTP/RPC surface — API rate limits are not applicable. Arrow is a computation library with no network calls. There are no rate limits to document or headers to return.
- **Gap**: None — not applicable for a library.
- **Recommendation**: No action required.
- **Evidence**: `arrow/api.py`, `requirements/requirements.txt`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: Arrow is a computation library with no auth surface. It does not authenticate callers, issue tokens, or validate credentials. The library exposes pure Python functions — there is no concept of a "caller" or "principal." Authentication is the responsibility of consuming applications.
- **Gap**: No auth mechanism exists — expected for a computation library.
- **Recommendation**: No action required. Consuming applications own machine identity authentication.
- **Evidence**: `arrow/api.py`, `arrow/arrow.py`, `arrow/factory.py` (no auth imports or credential handling)

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: INFO
- **Finding**: Arrow has no authorization model — all functions are publicly accessible. This is appropriate for a computation library with no sensitive operations or resources to protect.
- **Gap**: No authorization model exists — expected for a computation library.
- **Recommendation**: No action required. Scoped permissions are an MCP server / orchestration layer concern.
- **Evidence**: `arrow/__init__.py` (`__all__` exports all public symbols)

#### AUTH-Q3: Action-Level Authorization
- **Severity**: INFO
- **Finding**: No action-level authorization exists or is needed. All Arrow operations are pure computations returning new objects without side effects. No distinction between "read" and "write" actions is meaningful.
- **Gap**: None — not applicable.
- **Recommendation**: No action required.
- **Evidence**: `arrow/arrow.py` (immutable pattern)

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: Arrow does not propagate identity. No JWT parsing, no OAuth flows, no user context. Archetype calibration: `stateless-utility` → downgraded to INFO. The library is not a participant in the identity chain.
- **Gap**: None — not applicable.
- **Recommendation**: No action required.
- **Evidence**: `arrow/api.py`, `arrow/factory.py` (no auth-related imports)

#### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: Arrow manages no credentials. No API keys, database connections, or secrets exist in the library. CI/CD secrets (`PYPI_API_TOKEN`, `CODECOV_TOKEN`) are stored in GitHub Actions encrypted secrets store. No `.env` files committed. No hardcoded credentials found in any source file.
- **Gap**: None.
- **Recommendation**: No action required.
- **Evidence**: `.github/workflows/release.yml`, `.github/workflows/continuous_integration.yml`, `arrow/` (no credential patterns)

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY, then downgraded to INFO via surface-flag calibration (`has_auth_surface=false` AND `has_write_operations=false`)
- **Finding**: System does not execute agent-invoked write operations — audit logging is a consumer responsibility. Arrow has no logging, no CloudTrail integration, no audit trail. This is expected for a computation library.
- **Gap**: None — audit logging is a consumer concern.
- **Recommendation**: No action required.
- **Evidence**: `arrow/` (no logging imports across all source files)

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: INFO
- **Finding**: System does not issue or enforce agent identities — suspension is a consumer responsibility. Arrow has no concept of agent identities, API keys, or service accounts. `has_auth_surface=false` → downgraded to INFO per dev-library-application override.
- **Gap**: None — identity lifecycle is a consumer concern.
- **Recommendation**: No action required.
- **Evidence**: `arrow/` (no identity management code)

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY, then downgraded to INFO via surface-flag calibration (`has_write_operations=false` AND `has_http_rpc_surface=false`). Archetype: `stateless-utility` → INFO.
- **Finding**: System exposes no write operations — compensation logic is not applicable. Arrow is a pure computation library. All operations return new `Arrow` objects without modifying persistent state.
- **Gap**: None — not applicable for a stateless computation library.
- **Recommendation**: No action required.
- **Evidence**: `arrow/arrow.py` (immutable pattern), `arrow/api.py` (stateless factory functions)

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
- **Finding**: Arrow has no write operations — concurrency controls are not applicable. All functions are pure computations with no shared mutable state. Multiple concurrent callers produce independent results without interference.
- **Gap**: None — inherently safe for concurrent access.
- **Recommendation**: No action required.
- **Evidence**: `arrow/arrow.py` (no shared mutable state)

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has external dependencies (calls other services or external APIs)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: INFO
- **Finding**: System exposes no HTTP/RPC surface — API-layer rate limiting is not applicable. Arrow is a computation library invoked via Python import. Archetype: `stateless-utility` without persistent API surface → INFO.
- **Gap**: None — rate limiting is a consumer concern.
- **Recommendation**: No action required.
- **Evidence**: `arrow/api.py`, `requirements/requirements.txt` (no HTTP server dependencies)

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Read-only agents cannot modify records, trigger spend, or delete data. Arrow performs only computation — no transactions, no record modifications, no spend-incurring operations.
- **Gap**: None — blast radius is inherently zero.
- **Recommendation**: No action required.
- **Evidence**: `arrow/arrow.py` (no persistent state mutations)

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`. Priority is P2, not P0; library is not on the critical path.
- **Trigger**: Service is P0 priority OR is on the critical path
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q2: Configurable Approval Gates
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: INFO
- **Finding**: Arrow has no deployed HTTP surface or persistent data store — staging environments are a consumer concern. The library provides excellent local testing: `tox` for multi-Python-version testing, `pip install arrow` in any virtualenv. CI tests across 8 Python versions and 3 OS platforms. Dev-library-application override applies (`has_http_rpc_surface=false` AND `has_persistent_data_store=false`).
- **Gap**: None — staging is a consumer concern for libraries.
- **Recommendation**: No action required.
- **Evidence**: `tox.ini`, `.github/workflows/continuous_integration.yml`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO
- **Finding**: Not a data-handling target — no PII/PHI/financial/credential data is stored, processed, or logged. Dev-library-application override applied: library does not own data. Arrow receives datetime strings, timestamps, and timezone identifiers and returns `Arrow` objects. None of these constitute sensitive data. No database, no file storage, no user data model.
- **Gap**: None — data classification is not applicable.
- **Recommendation**: No action required.
- **Evidence**: `arrow/api.py`, `arrow/factory.py`, `arrow/arrow.py` (function signatures accept datetime/string/int)

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY, then downgraded to INFO via surface-flag calibration (`has_persistent_data_store=false` AND `has_logging_of_user_data=false`)
- **Finding**: No persistent data store and no user-data logging — residency requirements do not apply. Arrow holds no data. Pure computation library processing datetime values in-memory.
- **Gap**: None — not applicable.
- **Recommendation**: No action required.
- **Evidence**: `requirements/requirements.txt` (no database drivers, no storage SDKs)

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
- **Finding**: System does not log user data and holds no user data — PII-in-logs risk is not applicable. Arrow has no logging statements in source code (`has_logging_of_user_data=false` AND `has_persistent_data_store=false`). Archetype `stateless-utility` → INFO.
- **Gap**: None — no PII leakage risk.
- **Recommendation**: No action required.
- **Evidence**: `arrow/` (no `logging` imports, no `print()` calls in library code)

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics applicable to a computation library. Arrow processes individual datetime values deterministically. Data quality is a property of inputs provided by the caller. The library validates inputs (e.g., `validate_ordinal()`, `is_timestamp()`, `ParserError` on invalid formats) but does not track quality metrics.
- **Gap**: None — not applicable.
- **Recommendation**: No action required.
- **Evidence**: `arrow/factory.py`, `arrow/util.py` (input validation functions)

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: Arrow uses semantic versioning (`__version__ = "1.4.0"` in `arrow/_version.py`) and maintains a detailed `CHANGELOG.rst` (794 lines) with categorized entries ([ADDED], [CHANGED], [FIXED], [INTERNAL]). The library ships a `py.typed` marker and comprehensive type annotations enforced by mypy strict mode (`setup.cfg`). The `__all__` list in `arrow/__init__.py` explicitly defines the public API surface. However, there is no automated breaking-change detection in CI — no schema comparison tool, no consumer-driven contract tests (Pact), and no validation that `__all__` exports have not changed unexpectedly.
- **Gap**: No automated breaking-change detection in CI. Changes to public API (`__all__`, function signatures, exception types) are not machine-validated between releases.
- **Recommendation**: Add a CI step using `griffe` or a custom script to compare the public API surface against the previous release tag. This would catch accidental breaking changes before they reach consumers.
- **Evidence**: `arrow/_version.py`, `CHANGELOG.rst`, `arrow/__init__.py`, `setup.cfg`, `.pre-commit-config.yaml`, `tox.ini`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Arrow uses clear, Pythonic naming. Class names: `Arrow`, `ArrowFactory`, `DateTimeParser`, `DateTimeFormatter`, `TzinfoParser`, `ParserError`, `ParserMatchError`. Methods: `humanize()`, `dehumanize()`, `shift()`, `replace()`, `format()`, `to()`, `span()`, `range()`, `is_between()`. Constants: `DEFAULT_LOCALE`, `MAX_TIMESTAMP`, `FORMAT_RFC3339`. No legacy abbreviations or cryptic codes.
- **Gap**: None.
- **Recommendation**: No action required.
- **Evidence**: `arrow/arrow.py`, `arrow/constants.py`, `arrow/parser.py`, `arrow/formatter.py`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: Arrow provides comprehensive documentation via ReadTheDocs (`arrow.readthedocs.io`). Sphinx auto-generates API reference from docstrings (`docs/api-guide.rst` using `automodule`). `README.rst` has quick-start examples. `CHANGELOG.rst` has detailed release history. The library's metadata layer (docstrings, type hints, Sphinx docs) serves the purpose of a data catalog for agent tool discovery.
- **Gap**: None.
- **Recommendation**: No action required.
- **Evidence**: `.readthedocs.yaml`, `docs/api-guide.rst`, `docs/index.rst`, `README.rst`, `CHANGELOG.rst`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: INFO
- **Finding**: Library/utility — tracing and correlation are consumer concerns. Arrow has no telemetry, no OpenTelemetry SDK, no X-Ray instrumentation, no logging framework. This is appropriate for a pure Python computation library. Arrow does not make network calls, so there is no trace context to propagate.
- **Gap**: None — tracing is a consumer concern.
- **Recommendation**: No action required.
- **Evidence**: `requirements/requirements.txt` (no telemetry dependencies), `arrow/` (no logging or tracing imports)

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: INFO
- **Finding**: Library/utility — alerting is a consumer concern. Arrow exposes no deployed API surface. Libraries expose error signals via exceptions; consumers decide alert thresholds.
- **Gap**: None — alerting is a consumer concern.
- **Recommendation**: No action required.
- **Evidence**: `arrow/` (no alerting configuration), `requirements/requirements.txt` (no monitoring dependencies)

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No business outcome metrics applicable to a computation library. Arrow computes datetime values deterministically. Business metrics are application-level concerns.
- **Gap**: None — not applicable.
- **Recommendation**: No action required.
- **Evidence**: `arrow/` (no metrics publishing code)

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: INFO
- **Finding**: Arrow does not own IaC for API gateways, IAM roles, or networking (`has_http_rpc_surface=false` AND `has_auth_surface=false`). It is a Python library published to PyPI. No Terraform, CloudFormation, CDK, or Kubernetes configurations exist. The GitHub Actions CI/CD pipeline is defined as code. PR review is enforced by CI running on all pull requests.
- **Gap**: None — IaC governance is a consumer concern.
- **Recommendation**: No action required.
- **Evidence**: `.github/workflows/continuous_integration.yml`, `.github/workflows/release.yml`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — API contract testing is not applicable (`has_http_rpc_surface=false`). Library contract stability is evaluated by DISC-Q1. Arrow has an excellent CI/CD pipeline: GitHub Actions with `tox` across 8 Python versions (3.8–3.14 + PyPy) on 3 OS platforms (Ubuntu, macOS, Windows). Pre-commit hooks enforce linting (flake8 with bugbear + annotations plugins), formatting (black, isort), type checking (mypy strict), and code quality (pyupgrade, debug-statements check). Codecov tracks coverage. Documentation builds are verified in CI (`tox -e docs`).
- **Gap**: No automated API surface comparison between versions (see DISC-Q1).
- **Recommendation**: See DISC-Q1 recommendation.
- **Evidence**: `.github/workflows/continuous_integration.yml`, `tox.ini`, `.pre-commit-config.yaml`

#### ENG-Q3: Rollback Capability
- **Severity**: INFO
- **Finding**: No deployed HTTP/RPC surface — deployment rollback is a consumer concern (`has_http_rpc_surface=false`). Library rollback is via package version pinning (`pip install arrow==1.3.0`). Release pipeline publishes to PyPI via `flit publish` on tag push. PyPI supports version-specific installation. Semver versioning enables consumers to set upper bounds on versions (`arrow>=1.3.0,<2.0.0`).
- **Gap**: None — rollback is consumer-controlled.
- **Recommendation**: No action required.
- **Evidence**: `.github/workflows/release.yml`, `pyproject.toml`, `arrow/_version.py`

#### ENG-Q4: API Test Coverage
- **Severity**: INFO
- **Finding**: Arrow has exemplary test coverage. Pytest enforces `--cov-fail-under=99` (99% minimum branch coverage). Test suite: `test_arrow.py` (3,100 lines), `test_parser.py` (1,608 lines), `test_locales.py` (3,785 lines), `test_factory.py` (396 lines), `test_formatter.py` (279 lines), plus `test_api.py`, `test_util.py`, `conftest.py`, and `utils.py`. Tests cover init, parsing, formatting, timezone conversion, humanization, dehumanization, DST transitions, leap years, timestamp boundaries, locale validation, and edge cases. CI runs tests across 8 Python versions × 3 OS = 24 matrix combinations. Evaluated as INFO for `stateless-utility` archetype.
- **Gap**: None — coverage is excellent.
- **Recommendation**: No action required. Test coverage exceeds most industry benchmarks.
- **Evidence**: `tox.ini` (`--cov-fail-under=99`), `tests/test_arrow.py`, `tests/test_parser.py`, `tests/test_factory.py`, `tests/test_formatter.py`, `tests/test_locales.py`, `.github/workflows/continuous_integration.yml`

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
| `arrow/__init__.py` | API-Q1, API-Q2, AUTH-Q2, DISC-Q1 |
| `arrow/api.py` | API-Q1, API-Q4, API-Q5, API-Q8, AUTH-Q1, AUTH-Q4, STATE-Q1, STATE-Q5, DATA-Q1 |
| `arrow/arrow.py` | API-Q1, API-Q3, API-Q4, API-Q5, AUTH-Q1, AUTH-Q3, STATE-Q1, STATE-Q3, STATE-Q6, DATA-Q1, DISC-Q2 |
| `arrow/factory.py` | AUTH-Q1, AUTH-Q4, DATA-Q1, DATA-Q7 |
| `arrow/parser.py` | API-Q3, DISC-Q2 |
| `arrow/formatter.py` | DISC-Q2 |
| `arrow/constants.py` | DISC-Q2 |
| `arrow/util.py` | API-Q3, DATA-Q7 |
| `arrow/_version.py` | DISC-Q1, ENG-Q3 |
| `arrow/py.typed` | API-Q2, DISC-Q1 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/continuous_integration.yml` | AUTH-Q5, HITL-Q3, ENG-Q1, ENG-Q2, ENG-Q4 |
| `.github/workflows/release.yml` | AUTH-Q5, ENG-Q1, ENG-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `pyproject.toml` | DISC-Q1, ENG-Q3 |
| `requirements/requirements.txt` | API-Q8, STATE-Q5, DATA-Q2, OBS-Q1, OBS-Q2 |
| `requirements/requirements-tests.txt` | ENG-Q4 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `tox.ini` | HITL-Q3, DISC-Q1, ENG-Q2, ENG-Q4 |
| `setup.cfg` | API-Q2, DISC-Q1 |
| `.pre-commit-config.yaml` | DISC-Q1, ENG-Q2 |
| `.readthedocs.yaml` | DISC-Q3 |

### Documentation
| File | Questions Referenced |
|------|---------------------|
| `README.rst` | API-Q1, DISC-Q3 |
| `CHANGELOG.rst` | DISC-Q1, DISC-Q3 |
| `docs/api-guide.rst` | API-Q1, DISC-Q3 |
| `docs/index.rst` | DISC-Q3 |

### Test Files
| File | Questions Referenced |
|------|---------------------|
| `tests/test_arrow.py` | ENG-Q4 |
| `tests/test_parser.py` | ENG-Q4 |
| `tests/test_factory.py` | ENG-Q4 |
| `tests/test_formatter.py` | ENG-Q4 |
| `tests/test_locales.py` | ENG-Q4 |
