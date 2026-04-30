# Agentic Readiness Assessment Report

**Target**: arrow (arrow-py/arrow)
**Date**: 2026-04-29
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application (user-provided)
**Service Archetype**: stateless-utility (auto-detected)
**Agent Scope**: read-only (user-provided)
**Priority**: P2
**Tags**: python, library
**Context**: Python library for human-friendly date and time handling.

**Archetype Justification**: Arrow is a pure utility library with no database connections, no cache writes, no message queues, no HTTP/REST endpoints, and no persistent state. All operations are pure functions on datetime objects that return new immutable Arrow instances. This matches the stateless-utility archetype definition exactly.

> **Important Note**: Arrow is a Python library (not a deployed service). It is consumed via `import arrow` by applications, not called over a network. Many assessment questions about deployed infrastructure (authentication, rate limiting, audit logging, observability) are the responsibility of the **consuming application**, not the library itself. Findings reflect this architectural reality. For agent integration, Arrow would be wrapped as a tool function within an agent framework — the library's readiness depends on its API clarity, type safety, and documentation quality.

---

## Readiness Profile: Pilot-Ready (Safety Concerns)

**BLOCKERs**: 0 | **RISK-SAFETY**: 3 | **RISK-QUALITY**: 3 | **INFOs**: 25

Supervised pilot with elevated safety oversight: (1) all Pilot-Ready controls apply, (2) prioritize RISK-SAFETY remediation before expanding agent scope, (3) dedicated safety review cadence, (4) agent restricted to lowest-blast-radius operations until RISK-SAFETY count drops below 3.

Arrow is a mature, well-documented Python library with 99% test coverage, comprehensive type hints, and extensive documentation. As a stateless utility library operating in a read-only agent scope, it presents no blockers for agent integration. The three RISK-SAFETY findings (AUTH-Q6, STATE-Q1, DATA-Q2) are structural — they reflect the conditional BLOCKER rules mandated by the assessment framework for read-only agent scope, regardless of whether the library itself has gaps in these areas. The three RISK-QUALITY findings relate to the absence of a formal machine-readable API spec (OpenAPI equivalent), breaking change detection in CI, and formal API contract testing.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 0 |
| RISK-SAFETY | 3 |
| RISK-QUALITY | 3 |
| INFO | 25 |
| N/A | 0 |
| Not Evaluated (extended) | 12 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 7
**Extended Questions Not Triggered**: 12
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: stateless-utility (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

No BLOCKERs identified.

---

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q6: Immutable Audit Logging — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Arrow is a pure computation library with no logging functionality, no file I/O, and no write operations. There is nothing to audit at the library level — audit logging for agent-initiated operations must be implemented in the consuming application or agent framework. The conditional BLOCKER rule mandates RISK-SAFETY severity for read-only agent scope regardless of whether a gap exists in the library itself.
- **Gap**: No audit logging capability exists within the library. The consuming application or agent framework must provide immutable audit trails for agent-initiated operations that use Arrow.
- **Compensating Controls**:
  - Implement audit logging in the agent tool wrapper that calls Arrow, logging each tool invocation with agent identity, timestamp, parameters, and result
  - Use the agent framework's built-in observability (e.g., LangSmith, AgentOps) to capture all Arrow tool invocations with immutable trace records
- **Remediation Timeline**: 30–60 days (at consuming application layer)
- **Recommendation**: Implement audit logging in the agent tool wrapper, not in the library itself. Log agent identity, operation, parameters, and result for every Arrow tool invocation. Store logs in an immutable store (CloudWatch Logs with retention policy, S3 with object lock).
- **Evidence**: No logging code in `arrow/` source directory. No `import logging` statements in library code.

#### STATE-Q1: Compensation and Rollback — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Arrow operations are pure functions returning new immutable objects. `Arrow.shift()` returns a new `Arrow`. `Arrow.replace()` returns a new `Arrow`. `Arrow.to()` returns a new `Arrow`. The original object is never modified. There is no state to roll back and no multi-step transactions. The conditional BLOCKER rule mandates RISK-SAFETY severity for read-only agent scope regardless of whether a gap exists in the library itself.
- **Gap**: No compensation or rollback mechanism exists within the library. For a pure-function library this is architecturally expected — rollback is not applicable to stateless computations. However, consuming applications that use Arrow in multi-step workflows must implement their own compensation logic.
- **Compensating Controls**:
  - Arrow's immutability means operations are inherently safe — no state is modified, so there is nothing to roll back
  - Consuming applications should implement compensation/rollback at the workflow level, not the library level
- **Remediation Timeline**: 30–60 days (at consuming application layer, if applicable)
- **Recommendation**: No action required within Arrow. Consuming applications that embed Arrow in multi-step agent workflows should implement saga patterns or compensation logic at the workflow orchestration layer.
- **Evidence**: `arrow/arrow.py` — all mutation methods (`shift`, `replace`, `to`, `clone`) return new objects.

#### DATA-Q2: Data Residency and Sovereignty — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Arrow does not store, transmit, or persist any data. It performs in-memory datetime calculations only. Timezone data comes from the system's `zoneinfo` or `tzdata` package (IANA timezone database — public reference data). No regulated data (GDPR, LGPD, HIPAA) is processed or stored by the library. The conditional BLOCKER rule mandates RISK-SAFETY severity for read-only agent scope regardless of whether a gap exists in the library itself.
- **Gap**: No data residency controls exist within the library. The consuming application must ensure that any data processed alongside Arrow datetime operations complies with applicable residency and sovereignty requirements.
- **Compensating Controls**:
  - Arrow processes only temporal data (dates, times, timezones) — no PII, PHI, or regulated business data flows through the library
  - Consuming applications should implement data residency controls at the application/platform layer for any regulated data used alongside Arrow
- **Remediation Timeline**: 30–60 days (at consuming application layer, if applicable)
- **Recommendation**: No action required within Arrow. Consuming applications should ensure data residency compliance at the application layer, particularly when Arrow datetime outputs are combined with regulated data before transmission to LLM providers.
- **Evidence**: `requirements/requirements.txt` (tzdata dependency — public reference data), `arrow/parser.py` (ZoneInfo — system timezone data).

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Arrow does not have an OpenAPI, AsyncAPI, or GraphQL specification. As a Python library, Arrow provides a `py.typed` marker file, comprehensive PEP 484 type hints throughout all modules, and auto-generated Sphinx documentation on ReadTheDocs. These serve as the library equivalent of a machine-readable spec — Python tooling (mypy, IDEs, documentation generators) can introspect the API surface programmatically.
- **Gap**: No standard machine-readable API specification in OpenAPI/AsyncAPI/GraphQL format. Agent frameworks that auto-generate tool definitions from OpenAPI specs cannot directly consume Arrow's API definition. Tool definitions must be authored manually or generated from type hints.
- **Compensating Controls**:
  - Use Arrow's type hints and docstrings to auto-generate tool schemas via Python introspection (e.g., `inspect.signature()`, `typing.get_type_hints()`)
  - Agent frameworks like LangChain and CrewAI support Python function-based tool definitions that can leverage Arrow's type annotations directly
- **Remediation Timeline**: 30–60 days (optional)
- **Recommendation**: Consider generating a tool definition manifest (JSON Schema) from Arrow's public API using the existing type hints. This would enable automated tool registration in agent frameworks without requiring OpenAPI.
- **Evidence**: `arrow/py.typed`, `arrow/api.py` (type-annotated function signatures), `arrow/arrow.py` (comprehensive type hints), `docs/api-guide.rst`

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Arrow uses Semantic Versioning with a comprehensive CHANGELOG.rst documenting every release. The latest version is 1.4.0. Version bumps follow SemVer conventions (major for breaking changes, minor for features, patch for fixes). However, there is no automated breaking change detection in CI — no tools like `buf breaking`, OpenAPI diff, or consumer-driven contract tests (Pact). The pre-commit hooks include mypy type checking which provides some interface stability enforcement, but this only catches type-level changes, not behavioral contract changes.
- **Gap**: No automated breaking change detection in CI pipeline. Schema/API changes could inadvertently break agent tool bindings without being caught before release.
- **Compensating Controls**:
  - Arrow's 99% test coverage threshold provides strong regression detection
  - Mypy strict mode enforced in pre-commit catches type signature changes
  - SemVer discipline and detailed CHANGELOG provide manual change tracking
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a CI step that compares the public API surface (exported symbols, function signatures, type annotations) between the current branch and the latest release. Tools like `griffe` (Python API diff) or `pyright` can detect breaking changes in Python libraries.
- **Evidence**: `CHANGELOG.rst`, `pyproject.toml` (version management), `.pre-commit-config.yaml` (mypy), `.github/workflows/continuous_integration.yml`

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Arrow has a comprehensive CI/CD pipeline via GitHub Actions. The `continuous_integration.yml` workflow runs unit tests across Python 3.8–3.14 and PyPy on three operating systems (Ubuntu, macOS, Windows) via tox. Code coverage is enforced at 99% with `--cov-fail-under=99`. Linting includes black, flake8, isort, pyupgrade, and mypy with strict settings. The release pipeline publishes to PyPI via flit on tag push. However, there is no formal API contract testing (Pact, consumer-driven contracts) or explicit API surface comparison between releases.
- **Gap**: No consumer-driven contract tests. No explicit mechanism to detect that a change will break an agent tool definition that depends on Arrow's API surface.
- **Compensating Controls**:
  - 99% test coverage threshold enforced in CI catches most regressions
  - Mypy strict mode catches type signature changes
  - Multi-Python-version testing ensures broad compatibility
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a public API surface snapshot test that compares exported symbols and their signatures against a baseline. This is lighter-weight than Pact and appropriate for a library context.
- **Evidence**: `.github/workflows/continuous_integration.yml`, `.github/workflows/release.yml`, `tox.ini` (pytest config with 99% coverage), `.pre-commit-config.yaml`

---

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO
- **Finding**: Arrow exposes a well-documented Python API (not REST/GraphQL/AsyncAPI). The library is consumed via `import arrow` with a module-level API (`arrow.get()`, `arrow.now()`, `arrow.utcnow()`) and a class-based API (`Arrow` class with methods like `shift()`, `format()`, `humanize()`, `to()`). Documentation is comprehensive: extensive docstrings with usage examples in every public method, Sphinx auto-generated API reference on ReadTheDocs, a User's Guide with code examples, and a detailed README.
- **Implication**: For agent integration, Arrow's Python API would be wrapped as tool functions. The documented interface is clear and stable. An agent framework would define tool functions that call Arrow methods directly — no REST adapter needed.
- **Recommendation**: When building agent tools around Arrow, expose the most common functions (`arrow.get()`, `Arrow.format()`, `Arrow.shift()`, `Arrow.humanize()`, `Arrow.to()`) as individual tool definitions with parameter descriptions derived from Arrow's docstrings.
- **Evidence**: `arrow/api.py`, `arrow/arrow.py`, `arrow/__init__.py`, `docs/api-guide.rst`, `docs/guide.rst`, `README.rst`

### API-Q3: Structured Error Responses

- **Severity**: INFO
- **Finding**: Arrow uses typed Python exceptions with descriptive messages. `ParserError` (subclass of `ValueError`) is raised for parsing failures with messages like "Could not match input '...' to any of the following formats: ...". `ParserMatchError` (subclass of `ParserError`) distinguishes match-level failures. Standard `ValueError` and `TypeError` are raised for invalid arguments. All exceptions include descriptive messages explaining what went wrong.
- **Implication**: Agent tool wrappers can catch specific exception types to determine error category. `ParserError` → bad input (terminal), `TypeError` → wrong argument type (terminal), `ValueError` → out-of-range value (terminal). No retriable errors exist because Arrow is a pure computation library with no network calls.
- **Recommendation**: When wrapping Arrow as an agent tool, map Python exception types to structured error responses: `ParserError` → "invalid_input", `TypeError` → "type_error", `ValueError` → "value_error". All are terminal (non-retriable).
- **Evidence**: `arrow/parser.py` (ParserError, ParserMatchError classes), `arrow/arrow.py` (ValueError raises), `arrow/util.py` (ValueError, TypeError raises)

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Arrow has no write operations. All operations are pure functions that return new immutable `Arrow` objects. `arrow.get()` creates a new Arrow from input. `Arrow.shift()` returns a new Arrow. `Arrow.replace()` returns a new Arrow. `Arrow.to()` returns a new Arrow. The original object is never mutated. Idempotency is inherent — calling the same function with the same arguments always produces the same result.
- **Implication**: No idempotency concerns for agent integration. Arrow operations are inherently idempotent and side-effect-free.
- **Recommendation**: No action required.
- **Evidence**: `arrow/arrow.py` (all methods return new Arrow objects)

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: Arrow returns Python objects: `Arrow` instances (rich datetime replacement), `datetime.datetime`, `datetime.date`, `datetime.time`, `str` (from `format()`), `float` (from `timestamp()`), `int` (from `int_timestamp`), `bool` (from `is_between()`), `tuple` (from `span()`), and generators (from `range()`). The `Arrow` class supports JSON serialization via `for_json()` method (returns ISO 8601 string) and `isoformat()`.
- **Implication**: Arrow's return types are well-typed and easily serializable. For agent tool responses, Arrow objects can be converted to ISO 8601 strings via `str(arrow_obj)` or `arrow_obj.isoformat()`. The `for_json()` method enables direct JSON serialization via simplejson.
- **Recommendation**: Use `Arrow.isoformat()` or `Arrow.format()` to serialize Arrow objects into agent-consumable string responses.
- **Evidence**: `arrow/arrow.py` (return types, `for_json()`, `isoformat()`)

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: Arrow is a Python library with no HTTP endpoints, no API gateway, and no rate limiting. Rate limits are not applicable — the library executes in-process at the speed of the calling code.
- **Implication**: No rate limiting concerns for agent integration. If rate limiting is needed, it must be implemented in the agent framework or consuming application.
- **Recommendation**: No action required at the library level.
- **Evidence**: No HTTP endpoints found in `arrow/` source directory.

### AUTH-Q1: Machine Identity Authentication

- **Severity**: INFO
- **Finding**: Arrow is a Python library imported via `import arrow`. It does not expose network endpoints and does not require authentication. There are no IAM roles, OAuth flows, API keys, or service accounts because the library operates in-process within the calling application's security context. Authentication is the responsibility of the consuming application, not the library.
- **Implication**: When building agent tools around Arrow, authentication is handled at the agent framework layer or the consuming application layer. Arrow itself does not need to authenticate callers.
- **Recommendation**: No action required at the library level. Ensure the consuming application that wraps Arrow as an agent tool implements appropriate authentication.
- **Evidence**: `arrow/api.py`, `arrow/__init__.py` — no network, auth, or credential code present.

### AUTH-Q2: Scoped Permissions (Least Privilege)

- **Severity**: INFO
- **Finding**: Arrow has no permission model. All public functions are available to any caller — this is by design for a utility library. The library operates within the permissions of the calling process. There is no concept of "agent permissions" at the library level.
- **Implication**: Permission scoping for agent access to Arrow must be implemented at the agent framework or application layer — e.g., exposing only specific Arrow functions as agent tools rather than the entire API.
- **Recommendation**: When defining agent tools, expose only the Arrow functions relevant to the agent's use case (e.g., `arrow.get()` and `Arrow.format()` for date formatting tasks, but not `Arrow.shift()` if time manipulation is out of scope).
- **Evidence**: `arrow/api.py`, `arrow/__init__.py` — all exports are public, no access controls.

### AUTH-Q3: Action-Level Authorization

- **Severity**: INFO
- **Finding**: Arrow has no authorization model. All functions are accessible to any caller by design. For a stateless utility library that performs datetime calculations, action-level authorization is not applicable at the library level.
- **Implication**: Action-level authorization must be implemented in the agent tool wrapper — controlling which Arrow operations the agent can invoke.
- **Recommendation**: No action required at the library level. Implement tool-level authorization in the agent framework.
- **Evidence**: `arrow/api.py`, `arrow/arrow.py` — no authorization checks in any function.

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: INFO
- **Conditional**: Archetype calibration: stateless-utility → INFO
- **Finding**: Arrow does not propagate identity. It is a pure computation library that operates on datetime objects without any concept of caller identity, user context, or delegation. No JWT parsing, OAuth flows, or user context headers exist.
- **Implication**: Identity propagation is not relevant for a stateless utility library. The consuming application is responsible for identity management.
- **Recommendation**: No action required.
- **Evidence**: No identity-related code found in `arrow/` source directory.

### AUTH-Q5: Credential Management

- **Severity**: INFO
- **Finding**: Arrow does not handle credentials. No secrets, API keys, passwords, or connection strings exist in the codebase. The release pipeline (`release.yml`) uses `FLIT_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}` — the PyPI token is stored in GitHub Secrets (proper management), never committed to code. A search for patterns like `password=`, `secret=`, `api_key=` in the codebase returned zero results.
- **Implication**: No credential management concerns for agent integration.
- **Recommendation**: No action required.
- **Evidence**: `.github/workflows/release.yml` (secrets reference), search across all `arrow/` source files returned no credential patterns.

### AUTH-Q7: Agent Identity Suspension

- **Severity**: INFO
- **Finding**: Arrow has no identity management capabilities. It is a library that does not manage agent identities, API keys, or service accounts. Identity suspension must be handled at the infrastructure level (API Gateway, IAM, agent framework).
- **Implication**: Agent identity suspension is the responsibility of the agent framework or platform layer.
- **Recommendation**: No action required at the library level.
- **Evidence**: No identity management code found in `arrow/` source directory.

### STATE-Q5: Rate Limiting and Throttling

- **Severity**: INFO
- **Finding**: Arrow is a Python library with no API layer. Rate limiting is not applicable at the library level — it executes in-process at the speed of the calling code. If agent traffic management is needed, it must be implemented in the agent framework.
- **Implication**: Rate limiting is the responsibility of the agent framework or consuming application.
- **Recommendation**: No action required at the library level.
- **Evidence**: No HTTP endpoints or API layer found in `arrow/` source directory.

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Arrow has no write operations and no state mutations. There is no blast radius from Arrow operations — each call returns a new immutable object with no side effects.
- **Implication**: No blast radius concerns for agent integration.
- **Recommendation**: No action required.
- **Evidence**: `arrow/arrow.py` — all operations are pure functions.

### HITL-Q3: Sandbox/Staging Environment

- **Severity**: INFO
- **Finding**: Arrow can be trivially installed in any isolated Python virtual environment (`python -m venv test_env; pip install arrow`). This provides a sandbox with zero risk to production systems. The library has no external service dependencies, no database connections, and no configuration that differs between environments.
- **Implication**: Sandbox testing of Arrow-based agent tools is straightforward — create a virtualenv, install Arrow, and test tool functions.
- **Recommendation**: No action required. Arrow's sandboxing is inherent in Python's virtual environment mechanism.
- **Evidence**: `pyproject.toml` (pip-installable via flit), `Makefile` (virtualenv-based development setup).

### DATA-Q1: Sensitive Data Classification

- **Severity**: INFO
- **Finding**: Arrow processes datetime objects only — years, months, days, hours, minutes, seconds, timezones, and locale strings. It does not process PII, PHI, financial records, credentials, or any other sensitive data categories. The data flowing through Arrow is inherently non-sensitive (temporal information).
- **Implication**: No data classification concerns for agent integration.
- **Recommendation**: No action required.
- **Evidence**: `arrow/arrow.py` (operates on datetime components), `arrow/parser.py` (parses date strings), `arrow/formatter.py` (formats datetime to strings).

### DATA-Q6: PII Redaction in Logs

- **Severity**: INFO
- **Finding**: Arrow has no logging functionality. The library does not use Python's `logging` module, does not write to files, and does not emit any observable output beyond return values and exceptions. No PII can leak into logs because no logs are produced.
- **Implication**: No PII logging concerns for agent integration. The consuming application is responsible for log redaction.
- **Recommendation**: No action required at the library level.
- **Evidence**: No `import logging` statements found in `arrow/` source files. No file I/O operations in library code.

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: Arrow operates on datetime objects with deterministic behavior. Data quality issues (null rates, duplicates, staleness) do not apply to a computation library. Input validation is rigorous — `ParserError` is raised for malformed input, `ValueError` for out-of-range values, `TypeError` for wrong argument types. The library guarantees output correctness for valid inputs.
- **Implication**: Arrow provides inherent data quality guarantees through input validation and deterministic computation.
- **Recommendation**: No action required.
- **Evidence**: `arrow/parser.py` (comprehensive input validation), `arrow/util.py` (validate_ordinal, validate_bounds).

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Arrow uses clear, human-readable, semantically meaningful names throughout its API. Public methods: `get()`, `now()`, `utcnow()`, `shift()`, `replace()`, `format()`, `humanize()`, `dehumanize()`, `to()`, `span()`, `range()`, `floor()`, `ceil()`, `is_between()`. Properties: `year`, `month`, `day`, `hour`, `minute`, `second`, `microsecond`, `timestamp`, `naive`, `datetime`, `tzinfo`, `fold`, `ambiguous`, `imaginary`. No legacy abbreviations or obscure codes.
- **Implication**: Arrow's API is immediately understandable by LLM-based agents. Method names clearly convey intent, reducing the need for extensive tool descriptions.
- **Recommendation**: No action required.
- **Evidence**: `arrow/arrow.py` (method and property names), `arrow/api.py` (module API names).

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: Arrow has comprehensive Sphinx documentation hosted on ReadTheDocs (https://arrow.readthedocs.io). The `docs/api-guide.rst` auto-generates API documentation from docstrings using `sphinx-autodoc-typehints`. The User's Guide (`docs/guide.rst`) provides usage examples for all major features. The CHANGELOG.rst documents every release with categorized changes.
- **Implication**: Arrow's documentation serves as a metadata catalog for agent tool builders. The API guide provides complete information about available functions, parameters, and return types.
- **Recommendation**: No action required.
- **Evidence**: `docs/api-guide.rst`, `docs/guide.rst`, `.readthedocs.yaml`, `CHANGELOG.rst`.

### OBS-Q1: Distributed Tracing and Structured Logging

- **Severity**: INFO
- **Finding**: Arrow has no tracing instrumentation (no OpenTelemetry, no X-Ray, no structured logging). This is by design — utility libraries should not impose tracing overhead on consumers. Tracing is the responsibility of the consuming application.
- **Implication**: When wrapping Arrow as an agent tool, implement tracing at the tool wrapper level to capture tool invocations, latency, and error rates.
- **Recommendation**: Add trace spans in the agent tool wrapper, not in the library itself.
- **Evidence**: No OpenTelemetry, X-Ray, or logging imports found in `arrow/` source directory.

### OBS-Q2: Alerting on Error Rates and Latency

- **Severity**: INFO
- **Finding**: Arrow has no alerting capabilities — it is a library, not a deployed service. Alerting on error rates and latency for Arrow-based agent tools must be configured in the consuming application's observability stack.
- **Implication**: Alerting is the responsibility of the agent framework or application layer.
- **Recommendation**: Configure alerts on the agent tool wrapper for Arrow-related exceptions (ParserError rate) and latency.
- **Evidence**: No alerting configuration found in repository.

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: Arrow has no business metrics. As a utility library, business outcomes are measured at the application level. Arrow enables temporal reasoning — the business value is measured by the consuming agent's outcomes (e.g., correct scheduling, accurate time display).
- **Implication**: Business metrics for Arrow usage should be tracked at the agent framework level.
- **Recommendation**: No action required at the library level.
- **Evidence**: No custom metrics code found in `arrow/` source directory.

### ENG-Q1: Infrastructure Governance for Agent-Facing Surface

- **Severity**: INFO
- **Finding**: Arrow has no infrastructure to govern. It is a library distributed via PyPI (`pip install arrow`). There is no API Gateway, no IAM roles, no network configuration, and no secrets management infrastructure. The "deployment" is a PyPI package upload via `flit publish` in the release pipeline.
- **Implication**: Infrastructure governance is the responsibility of the application that consumes Arrow.
- **Recommendation**: No action required at the library level.
- **Evidence**: `.github/workflows/release.yml` (PyPI publish only), `pyproject.toml` (flit packaging).

### ENG-Q3: Rollback Capability

- **Severity**: INFO
- **Finding**: Arrow's rollback mechanism is PyPI version pinning. Consuming applications specify `arrow==1.4.0` in their requirements. If a new version introduces issues, consumers pin to the previous version. PyPI retains all published versions. This is the standard rollback mechanism for Python libraries.
- **Implication**: Rollback for Arrow-based agent tools is straightforward — pin to a known-good version.
- **Recommendation**: Pin Arrow version in agent tool requirements to prevent unexpected breaking changes. Use `arrow==1.4.0` rather than `arrow>=1.4.0`.
- **Evidence**: `pyproject.toml` (versioned releases), `CHANGELOG.rst` (release history), `arrow/_version.py` (`__version__ = "1.4.0"`).

### ENG-Q4: API Test Coverage

- **Severity**: INFO
- **Finding**: Arrow has exceptional test coverage — 99% minimum enforced in CI via `--cov-fail-under=99`. Tests cover all major modules: `tests/test_api.py` (module API), `tests/test_arrow.py` (3,100 lines of Arrow class tests), `tests/test_factory.py` (factory methods), `tests/test_formatter.py` (formatting), `tests/test_parser.py` (parsing), `tests/test_locales.py` (locale support), `tests/test_util.py` (utilities). Tests run across Python 3.8–3.14 and PyPy on three OS platforms.
- **Implication**: Arrow's test suite provides high confidence that agent tool wrappers built on Arrow will behave correctly. Edge cases (timezone transitions, DST, leap years, locales) are extensively tested.
- **Recommendation**: No action required. Arrow's test coverage exceeds typical standards.
- **Evidence**: `tox.ini` (`--cov-fail-under=99`), `.github/workflows/continuous_integration.yml` (multi-platform testing), `tests/` directory (7 test files).

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: Arrow exposes a well-documented Python API consumed via `import arrow`. The module-level API (`arrow.get()`, `arrow.now()`, `arrow.utcnow()`) and class-based API (`Arrow` class) are comprehensively documented via docstrings with usage examples, Sphinx auto-generated API reference on ReadTheDocs, a User's Guide, and a detailed README. Arrow is not a REST/GraphQL/AsyncAPI service — it is a library, so the Python API IS the documented interface. No direct database access, file-based exchange, or UI automation is required.
- **Gap**: No REST/GraphQL endpoint — but this is by design for a library. The Python API is the appropriate integration surface.
- **Recommendation**: Wrap Arrow functions as agent tool definitions. The documented Python API provides all necessary information for tool authoring.
- **Evidence**: `arrow/api.py`, `arrow/arrow.py`, `arrow/__init__.py`, `docs/api-guide.rst`, `docs/guide.rst`, `README.rst`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, or GraphQL specification exists. Arrow provides `py.typed` marker, comprehensive PEP 484 type hints, and Sphinx documentation as the library equivalent. Python tooling can introspect the API surface programmatically via type hints.
- **Gap**: No standard machine-readable API spec format (OpenAPI/AsyncAPI/GraphQL). Agent frameworks that auto-generate tool definitions from OpenAPI cannot directly consume Arrow's API.
- **Recommendation**: Generate a tool definition manifest (JSON Schema) from Arrow's public API using existing type hints, enabling automated tool registration.
- **Evidence**: `arrow/py.typed`, `arrow/api.py`, `arrow/arrow.py`, `docs/api-guide.rst`

#### API-Q3: Structured Error Responses
- **Severity**: INFO
- **Finding**: Arrow uses typed Python exceptions: `ParserError` (parsing failures), `ParserMatchError` (match failures), `ValueError` (out-of-range), `TypeError` (wrong types). All exceptions include descriptive messages. No HTTP status codes exist because Arrow is a library, not an API.
- **Gap**: No gap for a library context. Python exceptions with typed hierarchy serve the same purpose as structured error responses.
- **Recommendation**: Map exception types to error categories in agent tool wrappers.
- **Evidence**: `arrow/parser.py`, `arrow/arrow.py`, `arrow/util.py`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Arrow has no write operations. All operations are pure functions returning new immutable `Arrow` objects. Idempotency is inherent.
- **Gap**: No gap. All operations are pure and idempotent by design.
- **Recommendation**: No action required.
- **Evidence**: `arrow/arrow.py`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: Returns typed Python objects (`Arrow`, `datetime`, `str`, `float`, `int`, `bool`, `tuple`, generators). `Arrow` supports JSON serialization via `for_json()` and `isoformat()`.
- **Gap**: No gap.
- **Recommendation**: Use `Arrow.isoformat()` for agent-consumable serialization.
- **Evidence**: `arrow/arrow.py`

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has operations >30s OR long-running workflows — Arrow is a library with sub-millisecond operations.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has state changes (stateful-crud, orchestrator) — Arrow has no state changes.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: Arrow is a library with no HTTP endpoints. Rate limits are not applicable.
- **Gap**: No gap for a library context.
- **Recommendation**: No action required.
- **Evidence**: No HTTP endpoints in `arrow/` source directory.

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: Arrow is a library imported via `import arrow`. No network endpoints, no authentication required. Operates in-process within the calling application's security context.
- **Gap**: No gap for a library context. Authentication is the consuming application's responsibility.
- **Recommendation**: Implement authentication in the agent framework wrapping Arrow.
- **Evidence**: `arrow/api.py`, `arrow/__init__.py`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: INFO
- **Finding**: Arrow has no permission model. All functions available to any caller by design. Library operates within calling process permissions.
- **Gap**: No gap for a library context. Permission scoping is the consuming application's responsibility.
- **Recommendation**: Expose only relevant Arrow functions as agent tools.
- **Evidence**: `arrow/api.py`, `arrow/__init__.py`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: INFO
- **Finding**: Arrow has no authorization model. All functions accessible to any caller. Not applicable to a utility library.
- **Gap**: No gap for a library context.
- **Recommendation**: Implement tool-level authorization in the agent framework.
- **Evidence**: `arrow/api.py`, `arrow/arrow.py`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Conditional**: Archetype calibration: stateless-utility → INFO
- **Finding**: Arrow does not propagate identity. Pure computation library with no caller identity concept.
- **Gap**: No gap for a stateless utility library.
- **Recommendation**: No action required.
- **Evidence**: No identity-related code in `arrow/` source directory.

#### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: Arrow does not handle credentials. No secrets in codebase. PyPI release token stored in GitHub Secrets (proper management). Search for `password=`, `secret=`, `api_key=` returned zero results.
- **Gap**: No gap. Credentials are properly managed.
- **Recommendation**: No action required.
- **Evidence**: `.github/workflows/release.yml`, `arrow/` source files (no credential patterns).

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Arrow is a pure computation library with no logging functionality, no file I/O, no write operations. Nothing to audit at the library level. The conditional BLOCKER rule mandates RISK-SAFETY severity for read-only agent scope.
- **Gap**: No audit logging capability exists within the library. The consuming application or agent framework must provide immutable audit trails.
- **Recommendation**: Implement audit logging in agent tool wrappers. Log agent identity, operation, parameters, and result for every Arrow tool invocation.
- **Evidence**: No logging code in `arrow/` source directory.

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: INFO
- **Finding**: Arrow has no identity management. Library does not manage agent identities, API keys, or service accounts.
- **Gap**: No gap for a library context. Identity suspension handled at infrastructure level.
- **Recommendation**: No action required at library level.
- **Evidence**: No identity management code in `arrow/` source directory.

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: All Arrow operations are pure functions returning new immutable objects. No state to roll back, no multi-step transactions. The conditional BLOCKER rule mandates RISK-SAFETY severity for read-only agent scope.
- **Gap**: No compensation or rollback mechanism exists within the library. Consuming applications that use Arrow in multi-step workflows must implement their own compensation logic.
- **Recommendation**: Consuming applications that embed Arrow in multi-step agent workflows should implement saga patterns or compensation logic at the workflow orchestration layer.
- **Evidence**: `arrow/arrow.py` — `shift`, `replace`, `to`, `clone` all return new objects.

#### STATE-Q2: Queryable Current State
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator) — Arrow has no persistent state.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled AND service has persistent state — neither condition is met.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has external dependencies (calls other services or external APIs) — Arrow has no external runtime dependencies.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: INFO
- **Finding**: Arrow is a library with no API layer. Rate limiting not applicable at library level.
- **Gap**: No gap for a library context.
- **Recommendation**: No action required.
- **Evidence**: No API layer in `arrow/` source directory.

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No write operations, no state mutations, no side effects. No blast radius possible.
- **Gap**: No gap.
- **Recommendation**: No action required.
- **Evidence**: `arrow/arrow.py` — all operations are pure functions.

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path — Arrow is P2.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled — read-only scope means this question is not triggered.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled — read-only scope means this question is not triggered.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: INFO
- **Finding**: Arrow can be installed in any isolated Python virtualenv. Zero risk to production systems. No external dependencies, no database connections, no environment-specific configuration.
- **Gap**: No gap. Sandboxing is inherent via Python virtual environments.
- **Recommendation**: No action required.
- **Evidence**: `pyproject.toml`, `Makefile`.

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO
- **Finding**: Arrow processes datetime objects only (years, months, days, hours, timezones, locale strings). No PII, PHI, financial records, or credentials.
- **Gap**: No gap. No sensitive data processed.
- **Recommendation**: No action required.
- **Evidence**: `arrow/arrow.py`, `arrow/parser.py`, `arrow/formatter.py`.

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Arrow does not store, transmit, or persist any data. In-memory datetime calculations only. Timezone data from `tzdata` (IANA — public reference data). The conditional BLOCKER rule mandates RISK-SAFETY severity for read-only agent scope.
- **Gap**: No data residency controls exist within the library. The consuming application must ensure compliance with applicable residency and sovereignty requirements.
- **Recommendation**: Consuming applications should ensure data residency compliance at the application layer, particularly when Arrow datetime outputs are combined with regulated data.
- **Evidence**: `requirements/requirements.txt`, `arrow/parser.py`.

#### DATA-Q3: Selective Query Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has list/query endpoints with potentially unbounded results — Arrow has no query endpoints.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q4: System of Record Designations
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway) — Arrow has no persistent state.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator) — stateless-utility archetype has no persistent state.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q6: PII Redaction in Logs
- **Severity**: INFO
- **Finding**: Arrow has no logging functionality. No PII processed or logged.
- **Gap**: No gap. No logs produced.
- **Recommendation**: No action required.
- **Evidence**: No `import logging` in `arrow/` source files.

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: Arrow operates deterministically on datetime objects. Rigorous input validation via `ParserError`, `ValueError`, `TypeError`. Data quality issues (null rates, staleness) not applicable.
- **Gap**: No gap.
- **Recommendation**: No action required.
- **Evidence**: `arrow/parser.py`, `arrow/util.py`.

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: Arrow uses Semantic Versioning (1.4.0) with comprehensive CHANGELOG.rst. Pre-commit includes mypy strict mode. However, no automated breaking change detection in CI (no `buf breaking`, `griffe`, or Pact).
- **Gap**: No automated breaking change detection in CI pipeline.
- **Recommendation**: Add a CI step comparing public API surface between branches using `griffe` or similar Python API diff tools.
- **Evidence**: `CHANGELOG.rst`, `pyproject.toml`, `.pre-commit-config.yaml`, `.github/workflows/continuous_integration.yml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Arrow uses clear, semantically meaningful names: `get()`, `now()`, `shift()`, `format()`, `humanize()`, `year`, `month`, `day`, `timestamp`, `naive`, `ambiguous`. No legacy abbreviations.
- **Gap**: No gap.
- **Recommendation**: No action required.
- **Evidence**: `arrow/arrow.py`, `arrow/api.py`.

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: Sphinx documentation on ReadTheDocs with auto-generated API reference. CHANGELOG documents all releases.
- **Gap**: No gap.
- **Recommendation**: No action required.
- **Evidence**: `docs/api-guide.rst`, `docs/guide.rst`, `.readthedocs.yaml`, `CHANGELOG.rst`.

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: INFO
- **Finding**: No tracing instrumentation — by design for utility libraries. Tracing is the consuming application's responsibility.
- **Gap**: No gap for a library context.
- **Recommendation**: Add trace spans in agent tool wrappers, not in the library.
- **Evidence**: No tracing imports in `arrow/` source directory.

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: INFO
- **Finding**: No alerting capabilities — library, not a deployed service.
- **Gap**: No gap for a library context.
- **Recommendation**: Configure alerts at the agent tool wrapper level.
- **Evidence**: No alerting configuration in repository.

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No business metrics. Business outcomes measured at application level.
- **Gap**: No gap for a library context.
- **Recommendation**: No action required.
- **Evidence**: No custom metrics code in `arrow/` source directory.

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: INFO
- **Finding**: No infrastructure to govern. Library distributed via PyPI. No API Gateway, IAM, or network config.
- **Gap**: No gap for a library context.
- **Recommendation**: No action required.
- **Evidence**: `.github/workflows/release.yml`, `pyproject.toml`.

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive CI/CD: GitHub Actions, tox, pytest 99% coverage, multi-Python/multi-OS testing, mypy strict mode, pre-commit (black, flake8, isort). Release via flit to PyPI. No formal API contract testing (Pact) or breaking change detection.
- **Gap**: No consumer-driven contract tests or API surface comparison between releases.
- **Recommendation**: Add public API surface snapshot tests comparing exported symbols and signatures against a baseline.
- **Evidence**: `.github/workflows/continuous_integration.yml`, `.github/workflows/release.yml`, `tox.ini`, `.pre-commit-config.yaml`

#### ENG-Q3: Rollback Capability
- **Severity**: INFO
- **Finding**: Rollback via PyPI version pinning. All versions retained on PyPI. Standard rollback for Python libraries.
- **Gap**: No gap. Version pinning provides reliable rollback.
- **Recommendation**: Pin Arrow version in agent tool requirements.
- **Evidence**: `pyproject.toml`, `CHANGELOG.rst`, `arrow/_version.py`.

#### ENG-Q4: API Test Coverage
- **Severity**: INFO
- **Finding**: 99% test coverage enforced in CI. Seven test files covering all modules. Multi-platform, multi-Python-version testing.
- **Gap**: No gap. Exceptional test coverage.
- **Recommendation**: No action required.
- **Evidence**: `tox.ini`, `.github/workflows/continuous_integration.yml`, `tests/` directory.

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent data stores — Arrow has no data stores.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `arrow/__init__.py` | API-Q1, AUTH-Q1, AUTH-Q2 |
| `arrow/api.py` | API-Q1, API-Q2, AUTH-Q1, AUTH-Q2, AUTH-Q3 |
| `arrow/arrow.py` | API-Q1, API-Q2, API-Q3, API-Q4, API-Q5, AUTH-Q3, STATE-Q1, STATE-Q3, STATE-Q6, DATA-Q1, DATA-Q5, DISC-Q2 |
| `arrow/factory.py` | API-Q1 |
| `arrow/parser.py` | API-Q3, DATA-Q1, DATA-Q2, DATA-Q7, STATE-Q4 |
| `arrow/formatter.py` | DATA-Q1 |
| `arrow/util.py` | API-Q3, DATA-Q7 |
| `arrow/constants.py` | (referenced during discovery, supports locale/timezone features) |
| `arrow/locales.py` | (referenced during discovery, 60+ locale support) |
| `arrow/_version.py` | ENG-Q3 |
| `arrow/py.typed` | API-Q2 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/continuous_integration.yml` | DISC-Q1, ENG-Q2, ENG-Q4 |
| `.github/workflows/release.yml` | AUTH-Q5, ENG-Q1, ENG-Q2 |
| `tox.ini` | ENG-Q2, ENG-Q4 |
| `.pre-commit-config.yaml` | DISC-Q1, ENG-Q2 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `pyproject.toml` | API-Q2, ENG-Q1, ENG-Q3, HITL-Q3 |
| `requirements/requirements.txt` | STATE-Q4, DATA-Q2 |
| `requirements/requirements-tests.txt` | (referenced during discovery) |
| `requirements/requirements-docs.txt` | (referenced during discovery) |

### Documentation
| File | Questions Referenced |
|------|---------------------|
| `README.rst` | API-Q1 |
| `docs/api-guide.rst` | API-Q1, API-Q2, DISC-Q3 |
| `docs/guide.rst` | API-Q1, DISC-Q3 |
| `CHANGELOG.rst` | DISC-Q1, DISC-Q3, ENG-Q3 |
| `.readthedocs.yaml` | DISC-Q3 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `setup.cfg` | (mypy configuration, referenced during discovery) |
| `Makefile` | HITL-Q3 |
| `.github/dependabot.yml` | (referenced during discovery) |
