# Agentic Readiness Assessment Report

**Target**: sentry-python (Official Sentry SDK for Python)
**Date**: 2026-04-29
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Service Archetype**: stateless-utility (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: python, observability, sdk
**Context**: Official Sentry SDK for Python applications.

**Archetype Justification**: SDK library with no persistent state, no API server endpoints, and no write operations. All functionality is client-side instrumentation that sends telemetry data to a remote Sentry server via HTTP transport. No database connections, no message queue consumers, no downstream service fan-out.

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 2 | **RISK-SAFETY**: 9 | **RISK-QUALITY**: 8 | **INFOs**: 16

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days. The two BLOCKERs (API-Q1: no agent-callable API interface; DATA-Q1: incomplete field-level sensitive data classification) must be resolved before this SDK can be safely consumed by autonomous agents.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 2 |
| RISK-SAFETY | 9 |
| RISK-QUALITY | 8 |
| INFO | 16 |
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
- **Finding**: The Sentry Python SDK exposes a **Python programmatic API** via `sentry_sdk/api.py` and `sentry_sdk/__init__.py` — functions like `sentry_sdk.init()`, `capture_event()`, `capture_exception()`, `capture_message()`, `start_span()`, etc. This is a Python library API (function calls), **not** a REST, GraphQL, or AsyncAPI interface. There is no HTTP server, no REST endpoints, no GraphQL schema. Integration requires importing the Python package directly. An agent cannot call this SDK over the network without a custom wrapper service.
- **Gap**: No network-accessible API interface (REST, GraphQL, AsyncAPI, or gRPC) exists. Agents using HTTP-based tool calling patterns cannot consume this SDK directly.
- **Remediation**:
  - **Immediate**: Build a thin REST or MCP server wrapper around the SDK's public API surface (`init`, `capture_event`, `capture_exception`, `capture_message`, `flush`) to expose it as an agent-callable service.
  - **Target State**: A documented REST/MCP API endpoint that agents can call over HTTP to send telemetry to Sentry, with an OpenAPI spec describing the interface.
  - **Estimated Effort**: Medium (2–4 weeks for a basic wrapper + spec)
  - **Dependencies**: Resolving this unblocks API-Q2 (machine-readable spec) and API-Q8 (rate limit headers)
- **Evidence**: `sentry_sdk/api.py`, `sentry_sdk/__init__.py`, `sentry_sdk/consts.py` (ClientConstructor)

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: The SDK includes an `EventScrubber` in `sentry_sdk/scrubber.py` with `DEFAULT_DENYLIST` (31 fields including password, secret, api_key, token, authorization, cookie) and `DEFAULT_PII_DENYLIST` (4 fields: x_forwarded_for, x_real_ip, ip_address, remote_addr). The `send_default_pii` option (default: `None`, treated as `False`) controls whether PII like user IP, request headers, and cookies are included. However, **sensitive data classification is not enforced at the field level** — it relies on denylist string matching against field names. There is no data classification tagging system, no field-level encryption, and no mechanism to prevent an agent from retrieving sensitive data that happens to use non-denylisted field names. Custom fields containing sensitive data (e.g., `ssn`, `credit_card_number`, `date_of_birth`) are not scrubbed unless explicitly added to the denylist.
- **Gap**: Classification is pattern-based (denylist), not field-level. Custom sensitive fields are not automatically detected or tagged. No field-level access controls exist to prevent agent retrieval of specific sensitive fields.
- **Remediation**:
  - **Immediate**: Extend the `EventScrubber` denylist to include common sensitive field names (`ssn`, `social_security`, `credit_card`, `dob`, `date_of_birth`, `bank_account`). Enable `recursive=True` by default. Document the comprehensive list of scrubbed fields.
  - **Target State**: Field-level classification with tagging (e.g., PII, PHI, financial) and configurable access controls per classification level. Consider integrating with AWS Macie or similar classification tools at the platform layer.
  - **Estimated Effort**: Medium (denylist extension: 1 week; field-level classification: 4–8 weeks)
  - **Dependencies**: Interacts with DATA-Q6 (PII redaction) — both address PII handling.
- **Evidence**: `sentry_sdk/scrubber.py` (DEFAULT_DENYLIST, DEFAULT_PII_DENYLIST, EventScrubber), `sentry_sdk/client.py` (send_default_pii option, EventScrubber initialization)

---

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The SDK authenticates via a DSN (Data Source Name), which grants **project-level access**. A DSN encodes the protocol, public key, host, and project ID. All SDK instances using the same DSN have identical permissions — there is no mechanism within the SDK to scope an agent identity to read-only access to specific resources while denying write access. The Sentry platform supports project-level DSN keys with different permissions, but the SDK itself does not enforce or expose permission scoping.
- **Gap**: No SDK-level scoped permission model. All callers with the same DSN have identical access. Cannot grant an agent read-only access to specific resources without a separate DSN per scope.
- **Compensating Controls**:
  - Create separate Sentry projects or DSN keys with different permission levels for agent vs. human use
  - Implement permission enforcement at the wrapper API layer (if API-Q1 is resolved)
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create dedicated Sentry DSN keys for agent identities with restricted project-level scopes via Sentry's platform settings.
- **Evidence**: `sentry_sdk/transport.py` (DSN parsing, `self._auth`), `sentry_sdk/client.py` (DSN configuration), `sentry_sdk/consts.py` (ClientConstructor dsn parameter)

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The SDK has no action-level authorization. Any caller with a valid DSN can invoke `capture_event()`, `capture_exception()`, `capture_message()`, `start_span()`, `flush()`, and all other public API methods without distinction. There are no RBAC roles, no ABAC policies, no permission checks in middleware. The `before_send` and `before_send_transaction` callbacks can filter events but are not authorization mechanisms — they are data transformation hooks.
- **Gap**: No action-level authorization exists. An agent calling the SDK can perform any operation the SDK supports.
- **Compensating Controls**:
  - Implement authorization at the wrapper API layer (API-Q1 remediation)
  - Use `before_send` to filter/reject events based on custom authorization logic
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Build authorization into the wrapper service rather than modifying the SDK itself, since the SDK is a client library designed for direct embedding.
- **Evidence**: `sentry_sdk/api.py` (all public functions lack authorization), `sentry_sdk/client.py` (no permission checks in capture_event)

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The SDK logs internal diagnostic information via Python's standard `logging` module (`sentry_sdk/utils.py` defines a `logger` instance). These logs include debug messages about event sending, sampling decisions, and transport status. However, there is **no immutable audit logging** — no CloudTrail integration, no tamper-evident log storage, no structured audit trail that records which principal performed which action. The SDK's logging is debug-level diagnostic output, not an audit system.
- **Gap**: No immutable, tamper-evident audit logging. No principal attribution in logs. No structured audit trail for agent-initiated actions.
- **Compensating Controls**:
  - Implement audit logging at the wrapper service layer with CloudWatch Logs and log file validation
  - Enable CloudTrail for any AWS API calls made by the wrapper service
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add structured audit logging at the wrapper service layer that records the authenticated principal, action, timestamp, and outcome for every agent-initiated SDK call.
- **Evidence**: `sentry_sdk/utils.py` (logger definition), `sentry_sdk/transport.py` (debug-level logging only), `sentry_sdk/client.py` (no audit logging in capture_event)

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The SDK provides no mechanism to suspend or revoke an individual agent identity. DSN keys can be revoked at the Sentry platform level, but this is an all-or-nothing operation — revoking a DSN affects all SDK instances using that key. There is no SDK-level concept of agent identity, no per-instance credential, and no suspension API.
- **Gap**: No granular identity suspension mechanism. Cannot revoke a single agent's access without affecting all other SDK instances using the same DSN.
- **Compensating Controls**:
  - Create per-agent DSN keys on the Sentry platform, allowing individual revocation
  - Implement agent identity and suspension at the wrapper service layer
- **Remediation Timeline**: 30–60 days
- **Recommendation**: When building the wrapper service (API-Q1), implement per-agent API key management with individual suspension/revocation capabilities.
- **Evidence**: `sentry_sdk/transport.py` (single DSN per client instance), `sentry_sdk/client.py` (no identity management)

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The SDK calls Sentry's ingestion API (external dependency). The transport handles HTTP errors with status-code-based logic and implements rate-limit-based backoff. The `Monitor` class implements health checks and backpressure-based downsampling. However, there is **no formal circuit breaker pattern** — the SDK continues attempting to send events even when the server is returning persistent errors (non-429).
- **Gap**: No formal circuit breaker implementation.
- **Compensating Controls**:
  - Rate limit handling via `_disabled_until` provides partial circuit-breaking for rate-limited categories
  - `Monitor.check_health()` detects unhealthy transport and downsamples
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement a formal circuit breaker for the transport layer.
- **Evidence**: `sentry_sdk/transport.py`, `sentry_sdk/monitor.py`, `sentry_sdk/spotlight.py`

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The SDK implements server-side rate limit compliance but has **no client-side rate limiting**. A runaway agent could overwhelm the SDK's queue. Transport queue size (100) provides backpressure by dropping events when full, but this is overflow handling, not rate limiting.
- **Gap**: No client-side rate limiting on API calls.
- **Compensating Controls**:
  - Transport queue size limits in-flight events
  - Monitor-based downsampling reduces traffic under backpressure
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add client-side rate limiting at the wrapper layer.
- **Evidence**: `sentry_sdk/transport.py`, `sentry_sdk/consts.py`, `sentry_sdk/_batcher.py`, `sentry_sdk/monitor.py`


#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The SDK includes a comprehensive PII scrubbing system: `EventScrubber` in `sentry_sdk/scrubber.py` scrubs requests, extras, user data, breadcrumbs, frames, and spans. The `send_default_pii` option (default False) controls inclusion of IP addresses, cookies, and user-agent headers. The `before_send` callback allows custom PII stripping. However, PII redaction from the SDK's own **diagnostic logs** (Python logging output) is not guaranteed — debug logs may contain DSN strings, request headers, and error details that include PII. The `EventScrubber` only scrubs event payloads sent to Sentry, not the SDK's own log output to stdout/stderr.
- **Gap**: PII is scrubbed from event payloads but may leak into the SDK's own diagnostic log output (Python logging). DSN strings (which contain secrets) appear in debug logs. No log scrubbing middleware for the SDK's own logger.
- **Compensating Controls**:
  - Set `debug=False` (default) in production to minimize diagnostic log output
  - Configure log filters on the Python logging handler for the `sentry_sdk` logger
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a log scrubber that filters PII patterns from the SDK's own diagnostic logging output, similar to how `EventScrubber` works for event payloads.
- **Evidence**: `sentry_sdk/scrubber.py` (EventScrubber, DEFAULT_DENYLIST, DEFAULT_PII_DENYLIST), `sentry_sdk/client.py` (send_default_pii, before_send), `sentry_sdk/utils.py` (logger)

#### STATE-Q1: Compensation and Rollback ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The SDK's operations are inherently **append-only** — `capture_event`, `capture_exception`, and `capture_message` send events to Sentry's ingestion endpoint. There is no concept of "rolling back" a sent event. The `before_send` callback can filter events before sending, and events can be dropped by `DedupeIntegration`, `sample_rate`, or `error_sampler`. However, once an event is sent, it cannot be recalled. No compensation or rollback mechanisms exist for multi-step operations.
- **Gap**: No compensation or rollback capability exists. Events are fire-and-forget with no undo mechanism. While operations are append-only telemetry, the absence of compensation capability is a system maturity concern.
- **Compensating Controls**:
  - Use `before_send` callback to implement pre-send validation and filtering as a preventive measure
  - Implement compensation logic at the wrapper service layer if write operations are exposed
- **Remediation Timeline**: 30–60 days
- **Recommendation**: If building a wrapper service (API-Q1), implement compensation patterns at the wrapper layer — including event deduplication, idempotency keys, and a staged-send pattern where events are buffered before final delivery.
- **Evidence**: `sentry_sdk/client.py` (capture_event, before_send), `sentry_sdk/transport.py` (fire-and-forget envelope sending)

#### DATA-Q2: Data Residency and Sovereignty ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The SDK sends telemetry data to the endpoint specified in the DSN. The DSN encodes the host (e.g., `o1.ingest.sentry.io` for US, `o1.ingest.de.sentry.io` for EU). Data residency is controlled by choosing the appropriate Sentry organization region. The SDK itself does not enforce or validate data residency — it sends data wherever the DSN points. There is no region check, no cross-region protection, no GDPR-specific configuration in the SDK.
- **Gap**: No SDK-level data residency enforcement. The SDK does not validate that the DSN host matches a required region. An agent misconfigured with the wrong DSN could send regulated data to an incorrect region.
- **Compensating Controls**:
  - Configure DSN at the platform/infrastructure level to ensure correct regional routing
  - Add DSN host validation at the wrapper service layer to enforce allowed regions
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document the DSN-to-region mapping for agents. Add DSN host validation at the wrapper service layer that rejects DSNs pointing to non-approved regions. Ensure agents are configured with region-appropriate DSNs via platform-level configuration management.
- **Evidence**: `sentry_sdk/transport.py` (DSN host resolution, _auth.get_api_url), `sentry_sdk/client.py` (DSN configuration)

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, GraphQL schema, or Smithy model exists. The SDK's API is defined in Python code with comprehensive type hints (`sentry_sdk/py.typed` marker present, strict mypy configuration in `pyproject.toml`). Sphinx-based API documentation is generated from docstrings (`docs/api.rst`, `docs/apidocs.rst`). The `ClientConstructor` class in `sentry_sdk/consts.py` provides type-annotated parameter documentation for `init()`. However, none of this constitutes a machine-readable API specification that agent frameworks can consume to auto-generate tool definitions.
- **Gap**: No machine-readable API specification (OpenAPI, AsyncAPI, etc.). Type hints exist but are not in a format agent frameworks can consume directly.
- **Compensating Controls**:
  - Use the `py.typed` package and type stubs to generate tool definitions manually
  - Build an OpenAPI spec alongside the wrapper service (API-Q1 remediation)
- **Remediation Timeline**: 30–60 days (concurrent with API-Q1 wrapper)
- **Recommendation**: Generate an OpenAPI specification for the wrapper service API and keep it synchronized with the SDK's public surface using automated spec generation.
- **Evidence**: `sentry_sdk/py.typed`, `pyproject.toml` (mypy config), `sentry_sdk/consts.py` (ClientConstructor), `docs/api.rst`

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The SDK uses Python exceptions for error handling rather than structured error responses. Internal errors are caught via `capture_internal_exceptions()` in `sentry_sdk/utils.py` and logged rather than raised. Transport errors in `sentry_sdk/transport.py` differentiate HTTP 413 (payload too large), 429 (rate limited), and other status codes, logging structured messages. However, there is no consistent error response format with error codes, categories, or retryable booleans — errors are either silently swallowed or raised as Python exceptions.
- **Gap**: No structured error response format with error codes, messages, and retryable indicators. Errors are Python exceptions or silently logged, not structured responses.
- **Compensating Controls**:
  - The wrapper service (API-Q1) can translate SDK exceptions into structured HTTP error responses
  - The `transport.py` HTTP status handling provides a pattern for structured error categorization
- **Remediation Timeline**: 30–60 days (concurrent with API-Q1)
- **Recommendation**: Define a structured error response schema for the wrapper service API that maps SDK exceptions to error codes with retryable indicators.
- **Evidence**: `sentry_sdk/transport.py` (HTTP 413, 429, status code handling), `sentry_sdk/utils.py` (capture_internal_exceptions), `sentry_sdk/client.py` (before_send error handling)

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The SDK uses semantic versioning (VERSION = "2.56.0" in `sentry_sdk/consts.py`). A comprehensive `CHANGELOG.md` (4926 lines) documents every release. A `MIGRATION_GUIDE.md` covers the 1.x to 2.x migration. Deprecation warnings are used extensively (e.g., `configure_scope`, `push_scope`, `set_measurement` in `api.py`). The `.craft.yml` release process automates PyPI publishing. However, there is **no automated breaking-change detection** in CI — no consumer-driven contract tests (Pact), no OpenAPI diff, no `buf breaking` equivalent for the Python API. Breaking changes are documented manually in changelogs.
- **Gap**: No automated breaking-change detection in CI pipeline. Schema versioning relies on manual changelog updates and deprecation warnings rather than automated contract testing.
- **Compensating Controls**:
  - Semantic versioning and comprehensive changelogs provide manual change tracking
  - Deprecation warnings give consumers advance notice of breaking changes
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add automated API contract testing to CI that detects removed public functions, changed signatures, or modified return types between versions.
- **Evidence**: `sentry_sdk/consts.py` (VERSION = "2.56.0"), `CHANGELOG.md`, `MIGRATION_GUIDE.md`, `.craft.yml`, `sentry_sdk/api.py` (DeprecationWarning usage)

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The SDK **is** an observability SDK — it provides distributed tracing, OpenTelemetry integration (`sentry_sdk/integrations/opentelemetry/`), trace propagation (`sentry_sdk/tracing.py` with `sentry-trace` and `baggage` headers), and structured logging (`sentry_sdk/logger.py` with OTel severity levels). However, the SDK's **own internal observability** is limited — its diagnostic logging uses Python's standard `logging` module with unstructured text messages, not JSON structured logs with correlation IDs. The SDK's own transport health is monitored (`sentry_sdk/monitor.py`) but there is no trace ID propagation for the SDK's own internal operations.
- **Gap**: The SDK provides excellent observability capabilities for instrumented applications, but its own internal operations lack structured logging with correlation IDs and distributed tracing.
- **Compensating Controls**:
  - The SDK's tracing infrastructure can be used to instrument the wrapper service
  - Python logging can be configured with JSON formatters externally
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add structured JSON logging to the SDK's internal logger with request/correlation IDs for debugging agent-initiated operations.
- **Evidence**: `sentry_sdk/tracing.py`, `sentry_sdk/integrations/opentelemetry/`, `sentry_sdk/logger.py`, `sentry_sdk/monitor.py`, `sentry_sdk/utils.py` (logger)

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The SDK includes a `Monitor` class (`sentry_sdk/monitor.py`) that performs health checks on the transport layer every 10 seconds, checking if the transport is rate-limited or if the worker queue is full. When unhealthy, it implements backpressure by downsampling the traces sample rate (up to a factor of 2^10). However, there are **no alerting thresholds** — the monitor adjusts behavior silently. There are no CloudWatch alarms, no PagerDuty integration, no SLO-based alerting configured.
- **Gap**: No alerting thresholds configured for error rates or latency. The Monitor class detects unhealthy states but does not emit alerts — it silently adjusts sampling rates.
- **Compensating Controls**:
  - Configure alerting on the Sentry platform (server-side) for dropped events and error spikes
  - Add CloudWatch custom metrics at the wrapper service layer
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Expose health check metrics from the Monitor class as custom metrics that can be consumed by alerting systems.
- **Evidence**: `sentry_sdk/monitor.py` (Monitor class, check_health, set_downsample_factor), `sentry_sdk/transport.py` (is_healthy)

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The SDK provides a comprehensive testing infrastructure: `tox.ini` with 1080 lines defining test environments across Python 3.6–3.14 for 70+ integrations, `tests/` directory with extensive test files, `conftest.py` with test fixtures, and GitHub Actions workflows for CI. The SDK includes **Spotlight** (`sentry_sdk/spotlight.py`) — a local development tool that receives and displays Sentry events at `http://localhost:8969/stream` without sending data to Sentry's production servers. However, there is no pre-built staging environment with production-equivalent data shape, no seed data scripts, and no synthetic data generator for realistic testing.
- **Gap**: No staging environment with production-equivalent data shape. Spotlight provides local testing but not production-equivalent conditions.
- **Compensating Controls**:
  - Spotlight provides a zero-risk local testing environment for SDK functionality
  - tox + pytest provides comprehensive automated testing across Python versions
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a Docker-based staging environment with a mock Sentry ingest endpoint that validates event schemas against production contracts.
- **Evidence**: `sentry_sdk/spotlight.py` (SpotlightClient), `tox.ini`, `tests/conftest.py`, `.github/workflows/test-integrations-common.yml`, `Makefile`

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The SDK has extensive CI/CD: 24 GitHub Actions workflows including `ci.yml` (lint, build, docs), 13+ `test-integrations-*.yml` workflows testing against 70+ integrations across Python 3.6–3.14. Mypy strict type checking is configured in `pyproject.toml`. Codecov tracks coverage with a 10% threshold. The `.craft.yml` automates releases to PyPI. However, there is **no API contract testing** — no consumer-driven contract tests (Pact), no OpenAPI spec validation, no schema comparison between versions in CI.
- **Gap**: No API contract testing in CI pipeline. No automated detection of breaking API changes before release.
- **Compensating Controls**:
  - Mypy strict type checking catches type signature changes
  - Extensive integration test matrix catches behavioral regressions
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add API surface snapshot testing to CI that fails on removal of public functions or signature changes.
- **Evidence**: `.github/workflows/ci.yml`, `.github/workflows/test-integrations-common.yml`, `pyproject.toml` (mypy config), `codecov.yml`, `.craft.yml`

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The SDK has extensive test coverage: `tests/` directory with 30+ test files covering API (`test_api.py`), client (`test_client.py`), transport (`test_transport.py`), scrubber (`test_scrubber.py`), serializer (`test_serializer.py`), scope (`test_scope.py`), tracing (`tracing/` directory), and more. Integration tests cover 70+ frameworks across Python 3.6–3.14. Codecov is configured with a 10% drop threshold (informational). However, the coverage status is set to `informational: true` in `codecov.yml`, meaning coverage drops do not block PRs.
- **Gap**: Coverage is tracked but not enforced as a gate — drops are informational only. No specific API contract coverage metrics.
- **Compensating Controls**:
  - Comprehensive test matrix across Python versions provides broad behavioral coverage
  - Informational coverage reporting still tracks trends
- **Remediation Timeline**: 30 days
- **Recommendation**: Set `informational: false` in codecov.yml to enforce coverage thresholds as a PR gate.
- **Evidence**: `tests/test_api.py`, `tests/test_client.py`, `tests/test_transport.py`, `tests/test_scrubber.py`, `codecov.yml` (informational: true), `pyproject.toml` (pytest config with --cov)

---

## INFOs — Architecture and Design Inputs

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The SDK's primary operations (`capture_event`, `capture_exception`, `capture_message`) are **inherently idempotent from the caller's perspective** — each call generates a unique `event_id` (UUID4) in `client.py`. Duplicate calls with different event IDs produce separate events (by design — each event is unique). There is no idempotency key mechanism because the SDK generates unique identifiers for each event.
- **Implication**: In a write-enabled scope, duplicate event submission is by-design behavior, not a data integrity risk. However, if an agent wrapper exposes write operations, idempotency keys should be added at the wrapper layer.
- **Recommendation**: If building a wrapper service, implement idempotency keys at the API layer for write operations.
- **Evidence**: `sentry_sdk/client.py` (uuid.uuid4().hex event_id generation)

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: The SDK serializes events as JSON via `sentry_sdk/serializer.py` and transmits them as `application/x-sentry-envelope` (a Sentry-specific envelope format) via `sentry_sdk/transport.py`. The envelope format is text-based and structured. Internal SDK responses are Python objects (strings, None, dicts), not HTTP responses.
- **Implication**: The envelope format is machine-readable but Sentry-specific. A wrapper service should expose standard JSON responses to agents.
- **Recommendation**: The wrapper service should return standard JSON responses, not raw envelope format.
- **Evidence**: `sentry_sdk/serializer.py`, `sentry_sdk/transport.py` (Content-Type: application/x-sentry-envelope), `sentry_sdk/envelope.py`

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: The SDK handles rate limits from the Sentry server: `transport.py` parses `x-sentry-rate-limits` and `Retry-After` headers, implements per-category rate limiting (`_disabled_until` dict), and silently drops events when rate-limited. The `Monitor` class implements backpressure-based downsampling. However, the SDK does not **emit** rate limit headers to its callers — it is a client library, not a server. Rate limit behavior is internal and not exposed to consumers.
- **Implication**: An agent calling the SDK has no visibility into rate limit status. The wrapper service should expose rate limit headers to agents.
- **Recommendation**: The wrapper service should expose `X-RateLimit-Remaining` and `Retry-After` headers based on the SDK's internal `_disabled_until` state.
- **Evidence**: `sentry_sdk/transport.py` (_update_rate_limits, _disabled_until, _parse_rate_limits), `sentry_sdk/monitor.py` (backpressure)

### AUTH-Q1: Machine Identity Authentication

- **Severity**: INFO
- **Finding**: The SDK authenticates via DSN (Data Source Name) which encodes a public key and project ID. In `transport.py`, the DSN is parsed into an auth object (`self._auth = self.parsed_dsn.to_auth()`) and included as `X-Sentry-Auth` header on every request. The DSN can be provided via `sentry_sdk.init(dsn=...)` or the `SENTRY_DSN` environment variable. This constitutes machine-credential authentication (API key with principal attribution at the project level). However, the DSN identifies the project but not the specific agent instance.
- **Implication**: DSN provides project-level authentication but not per-agent-instance attribution. Multiple agents using the same DSN are indistinguishable in audit logs.
- **Recommendation**: Create a dedicated DSN per agent instance to enable attribution. Embed agent identity metadata in event tags.
- **Evidence**: `sentry_sdk/transport.py` (DSN auth, X-Sentry-Auth header), `sentry_sdk/client.py` (DSN from SENTRY_DSN env var or init parameter)

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: INFO
- **Finding**: The SDK supports trace context propagation via `sentry-trace` and `baggage` headers (`sentry_sdk/tracing.py`, `sentry_sdk/tracing_utils.py`). It propagates trace IDs, span IDs, and sampling decisions across service boundaries. However, there is no user/agent identity propagation — the SDK propagates observability context, not authorization context. No JWT parsing, no OAuth2 on-behalf-of flows, no token exchange.
- **Implication**: For a stateless-utility archetype, identity propagation has minimal security impact. The SDK's trace propagation infrastructure could be extended to carry agent identity context.
- **Recommendation**: If building an agent integration, embed agent identity (agent_id, acting_as) in the SDK's custom context or tags for audit purposes.
- **Evidence**: `sentry_sdk/tracing.py` (sentry-trace header, baggage), `sentry_sdk/tracing_utils.py` (Baggage, extract_sentrytrace_data)

### AUTH-Q5: Credential Management

- **Severity**: INFO
- **Finding**: The DSN is the primary credential. The SDK reads it from the `dsn` parameter in `init()` or the `SENTRY_DSN` environment variable. No hardcoded credentials were found in the codebase. The `DEFAULT_DENYLIST` in `scrubber.py` includes "api_key", "secret", "token", "credentials", "password" — ensuring these are scrubbed from event payloads. However, the DSN itself may appear in debug logs when `debug=True`. There is no integration with AWS Secrets Manager, HashiCorp Vault, or other secrets management systems — the SDK is credential-store-agnostic.
- **Implication**: The SDK's credential management is minimal by design (DSN from env var). Secrets management integration belongs at the application/platform layer, not the SDK itself.
- **Recommendation**: Store the DSN in a secrets management system (AWS Secrets Manager) and inject it via environment variable. Ensure `debug=False` in production to prevent DSN leakage in logs.
- **Evidence**: `sentry_sdk/client.py` (os.environ.get("SENTRY_DSN")), `sentry_sdk/scrubber.py` (DEFAULT_DENYLIST), `sentry_sdk/transport.py` (DSN parsing)

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The SDK uses thread-safe data structures: `BackgroundWorker` in `worker.py` uses `threading.Lock` and a thread-safe `Queue`. The `Batcher` classes use `threading.Lock` for buffer access. The `Monitor` uses `threading.Lock`. However, there are no optimistic locking patterns (ETags, version fields) because the SDK doesn't manage persistent state — it sends events asynchronously via a background thread.
- **Implication**: Concurrency controls for write operations are irrelevant for this read-only SDK. The SDK's internal thread safety is adequate for its purpose.
- **Recommendation**: N/A for read-only scope.
- **Evidence**: `sentry_sdk/worker.py` (threading.Lock, Queue), `sentry_sdk/_batcher.py` (threading.Lock), `sentry_sdk/monitor.py` (threading.Lock)

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The SDK has built-in limits: `DEFAULT_QUEUE_SIZE = 100` (transport queue), `MAX_BEFORE_FLUSH = 100` and `MAX_BEFORE_DROP = 1000` in `_batcher.py`, `DEFAULT_MAX_BREADCRUMBS = 100`, `MAX_EVENT_BYTES = 10^6` in `serializer.py`. These limit the blast radius of the SDK itself. However, there are no configurable per-agent transaction limits because the SDK has no concept of agent identity.
- **Implication**: The SDK's built-in limits prevent runaway resource consumption. For read-only scope, blast radius is minimal.
- **Recommendation**: N/A for read-only scope.
- **Evidence**: `sentry_sdk/consts.py` (DEFAULT_QUEUE_SIZE), `sentry_sdk/_batcher.py` (MAX_BEFORE_FLUSH, MAX_BEFORE_DROP), `sentry_sdk/serializer.py` (MAX_EVENT_BYTES)

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The SDK has no draft/pending state concept. Events are either sent or dropped — there is no intermediate state. The `before_send` callback provides a pre-send review hook, and `Spotlight` enables local-only sending for development. However, there is no built-in mechanism for an agent to propose events that a human reviews before they are sent to Sentry.
- **Implication**: For read-only agent scope, draft states are irrelevant. If write-enabled scope is needed, the wrapper service should implement a pending/approval queue.
- **Recommendation**: N/A for read-only scope.
- **Evidence**: `sentry_sdk/client.py` (before_send), `sentry_sdk/spotlight.py` (SpotlightClient)

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The SDK has no configurable approval gates. The closest mechanisms are `before_send` (which can conditionally drop events) and `ignore_errors` (which filters specific exception types). These are configuration hooks, not human-approval workflows.
- **Implication**: For read-only scope, approval gates are irrelevant. If write-enabled scope is added via wrapper, implement approval gates at the wrapper layer.
- **Recommendation**: N/A for read-only scope.
- **Evidence**: `sentry_sdk/client.py` (before_send, before_send_transaction, ignore_errors)

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: The SDK includes data quality mechanisms: `serializer.py` enforces `MAX_DATABAG_DEPTH`, `MAX_DATABAG_BREADTH`, `MAX_EVENT_BYTES`, and `MAX_VALUE_LENGTH` limits. The `_meta` field annotates truncated data. The SDK tracks discarded events via `record_lost_event` with reasons (sample_rate, before_send, network_error, queue_overflow, ratelimit_backoff). Client reports are sent to Sentry periodically. However, there is no data quality score, no completeness metric, and no freshness SLA.
- **Implication**: The SDK has operational data quality tracking (discarded events, truncation metadata) but no business-level data quality metrics.
- **Recommendation**: Expose discarded event counts and reasons as observable metrics for data quality monitoring.
- **Evidence**: `sentry_sdk/serializer.py` (MAX_DATABAG_DEPTH, _annotate), `sentry_sdk/transport.py` (record_lost_event, _fetch_pending_client_report)

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: The SDK uses highly semantic, human-readable field names throughout. The `SPANDATA` class in `sentry_sdk/consts.py` defines ~100+ constants following OpenTelemetry semantic conventions: `gen_ai.usage.input_tokens`, `http.response.status_code`, `db.system`, `messaging.destination.name`, `mcp.tool.name`, etc. Each constant includes a docstring with description and example. No legacy abbreviations or codes are used.
- **Implication**: Field names are immediately interpretable by LLMs. No data dictionary lookup required. Agents can reason about span data attributes without translation.
- **Recommendation**: Continue following OpenTelemetry semantic conventions for new attributes.
- **Evidence**: `sentry_sdk/consts.py` (SPANDATA class with ~100+ documented constants)

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: The SDK provides multiple metadata layers: `py.typed` marker for PEP 561 compliance, Sphinx API documentation (`docs/`), extensive docstrings in `consts.py` (ClientConstructor with 2000+ lines of parameter documentation), `README.md` with setup instructions, and `CHANGELOG.md` with release history. The `_types.py` file defines TypedDicts for Event, Hint, Breadcrumb, and other data structures. However, there is no formal data catalog (AWS Glue, Collibra, etc.).
- **Implication**: The SDK's documentation is comprehensive for human developers. For agent consumption, the type definitions and docstrings provide sufficient semantic information.
- **Recommendation**: Consider generating a machine-readable schema document from the TypedDict definitions for agent tool generation.
- **Evidence**: `sentry_sdk/py.typed`, `sentry_sdk/_types.py`, `sentry_sdk/consts.py` (ClientConstructor docstrings), `docs/`, `README.md`

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: The SDK provides a metrics API (`sentry_sdk/metrics.py`) supporting count, gauge, and distribution metrics with custom attributes. The `MetricsBatcher` in `_metrics_batcher.py` batches and sends metrics. The SDK also emits client reports tracking discarded events by reason (sample_rate, before_send, network_error, queue_overflow). However, these are infrastructure metrics, not business outcome metrics.
- **Implication**: The SDK can be used to emit business metrics (via `sentry_sdk.metrics.count()`, etc.), but it does not emit business outcome metrics about its own operations.
- **Recommendation**: Use the metrics API to emit agent-specific business metrics (e.g., agent events captured, agent errors detected) through the wrapper service.
- **Evidence**: `sentry_sdk/metrics.py` (count, gauge, distribution), `sentry_sdk/_metrics_batcher.py`

### ENG-Q1: Infrastructure Governance for Agent-Facing Surface

- **Severity**: INFO
- **Finding**: This is a library published to PyPI, not infrastructure. There are no IaC files (no Terraform, CloudFormation, CDK, Helm, or Kubernetes manifests). The `.craft.yml` governs the release process (PyPI, GitHub, AWS Lambda layer publishing). GitHub Actions workflows are pinned to specific commit SHAs (e.g., `actions/checkout@de0fac2e...`), providing supply chain security. PR reviews are enforced via GitHub branch protection (inferred from workflow permissions and PR-triggered workflows). No drift detection is applicable since there is no infrastructure.
- **Implication**: Infrastructure governance is not applicable to a library. However, the release pipeline (PyPI publishing) is the equivalent "infrastructure" for a library, and it is well-governed via `.craft.yml` and pinned actions.
- **Recommendation**: N/A for library — release governance is adequate.
- **Evidence**: `.craft.yml`, `.github/workflows/ci.yml` (pinned action SHAs), `.github/workflows/release.yml`

### ENG-Q3: Rollback Capability

- **Severity**: INFO
- **Finding**: As a PyPI-published library, rollback is accomplished by consumers pinning to a previous version (`pip install sentry-sdk==2.55.0`). The SDK follows semantic versioning, and all versions remain available on PyPI. The release process via `.craft.yml` and `release.yml` uses GitHub's release mechanism. There is no blue/green deployment or canary release — consumers control which version they use via dependency management.
- **Implication**: Rollback is consumer-controlled via version pinning. The SDK cannot be "rolled back" at the server level because it runs in the consumer's process.
- **Recommendation**: Document recommended version pinning strategies for agent deployments.
- **Evidence**: `setup.py` (version="2.56.0"), `.craft.yml` (PyPI target), `CHANGELOG.md`

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: BLOCKER
- **Finding**: The SDK exposes a Python programmatic API via `sentry_sdk/api.py` and `sentry_sdk/__init__.py` with functions like `init()`, `capture_event()`, `capture_exception()`, `capture_message()`, `start_span()`, etc. No REST, GraphQL, or AsyncAPI interface exists. Integration requires Python import, not HTTP calls.
- **Gap**: No network-accessible API interface for agent consumption.
- **Recommendation**: Build a thin REST or MCP wrapper service exposing the SDK's public API.
- **Evidence**: `sentry_sdk/api.py`, `sentry_sdk/__init__.py`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: No OpenAPI, AsyncAPI, GraphQL schema, or Smithy model. API defined in Python code with type hints (`py.typed`). Sphinx docs generated from docstrings.
- **Gap**: No machine-readable API spec for agent tool generation.
- **Recommendation**: Generate OpenAPI spec alongside wrapper service.
- **Evidence**: `sentry_sdk/py.typed`, `pyproject.toml`, `docs/api.rst`

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: SDK uses Python exceptions and internal logging. Transport differentiates HTTP status codes (413, 429). No consistent structured error format with error codes and retryable indicators.
- **Gap**: No structured error response format.
- **Recommendation**: Define structured error schema for wrapper service.
- **Evidence**: `sentry_sdk/transport.py`, `sentry_sdk/utils.py`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Each event gets a unique UUID4 event_id. Operations are append-only by design.
- **Gap**: N/A for read-only scope.
- **Recommendation**: Add idempotency keys at wrapper layer if write operations are exposed.
- **Evidence**: `sentry_sdk/client.py` (uuid.uuid4().hex)

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: Events serialized as JSON within Sentry envelope format (`application/x-sentry-envelope`). Internal responses are Python objects.
- **Implication**: Wrapper should expose standard JSON responses.
- **Recommendation**: Use standard JSON in wrapper API.
- **Evidence**: `sentry_sdk/serializer.py`, `sentry_sdk/transport.py`, `sentry_sdk/envelope.py`

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has operations >30s OR long-running workflows. The SDK's operations (event capture, flush) complete within seconds. Background workers handle async sending but operations return immediately.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has state changes (stateful-crud, orchestrator). The SDK is stateless-utility.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: SDK parses `x-sentry-rate-limits` and `Retry-After` from Sentry server. Does not emit rate limit headers to callers. Internal rate limiting via `_disabled_until`.
- **Implication**: Agents have no visibility into rate limit status without wrapper.
- **Recommendation**: Expose rate limit headers at wrapper layer.
- **Evidence**: `sentry_sdk/transport.py` (_update_rate_limits, _parse_rate_limits)

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: SDK authenticates via DSN (Data Source Name) with `X-Sentry-Auth` header. DSN provides project-level machine identity authentication. Per-agent-instance attribution requires dedicated DSN keys.
- **Implication**: Machine identity auth exists via DSN. Granularity is project-level, not per-agent-instance.
- **Recommendation**: Create dedicated DSN per agent instance; embed agent identity in event tags.
- **Evidence**: `sentry_sdk/transport.py`, `sentry_sdk/client.py`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: DSN grants project-level access. No SDK-level scoped permission model.
- **Gap**: Cannot scope agent to specific resources.
- **Recommendation**: Create separate DSN keys with restricted project-level scopes.
- **Evidence**: `sentry_sdk/transport.py`, `sentry_sdk/client.py`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization. Any caller with DSN can invoke all API methods.
- **Gap**: No RBAC/ABAC for SDK operations.
- **Recommendation**: Implement authorization at wrapper layer.
- **Evidence**: `sentry_sdk/api.py`, `sentry_sdk/client.py`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: SDK propagates trace context (sentry-trace, baggage headers) but not authorization context. No JWT parsing, no OAuth2 flows. Downgraded to INFO for stateless-utility archetype.
- **Implication**: Minimal security impact for stateless-utility. Trace propagation can carry agent identity metadata.
- **Recommendation**: Embed agent identity in custom context or tags.
- **Evidence**: `sentry_sdk/tracing.py`, `sentry_sdk/tracing_utils.py`

#### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: DSN read from `SENTRY_DSN` env var or `init()` parameter. No hardcoded credentials. Denylist scrubs credential-like fields from events. No Secrets Manager integration (by design — SDK is credential-store-agnostic).
- **Implication**: Credential management belongs at the platform layer.
- **Recommendation**: Store DSN in AWS Secrets Manager; set debug=False in production.
- **Evidence**: `sentry_sdk/client.py`, `sentry_sdk/scrubber.py`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No immutable audit logging. SDK uses Python logging for diagnostics only.
- **Gap**: No tamper-evident audit trail.
- **Recommendation**: Implement audit logging at wrapper layer.
- **Evidence**: `sentry_sdk/utils.py`, `sentry_sdk/transport.py`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: No per-agent identity suspension. DSN revocation is all-or-nothing.
- **Gap**: Cannot revoke individual agent access.
- **Recommendation**: Implement per-agent API key management at wrapper layer.
- **Evidence**: `sentry_sdk/transport.py`, `sentry_sdk/client.py`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: SDK operations are fire-and-forget. Events cannot be recalled once sent. No compensation or rollback mechanisms exist. Operations are append-only telemetry with no persistent state to roll back.
- **Gap**: No compensation or rollback capability. Events are fire-and-forget with no undo mechanism.
- **Recommendation**: Implement compensation patterns at the wrapper service layer if write operations are exposed.
- **Evidence**: `sentry_sdk/client.py`, `sentry_sdk/transport.py`

#### STATE-Q2: Queryable Current State
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator). SDK has no persistent state.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: SDK uses thread-safe primitives (threading.Lock, Queue) throughout. No optimistic locking needed — no persistent state.
- **Gap**: N/A for read-only scope.
- **Recommendation**: N/A.
- **Evidence**: `sentry_sdk/worker.py`, `sentry_sdk/_batcher.py`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY
- **Finding**: The SDK calls Sentry's ingestion API (external dependency). The transport handles HTTP errors with status-code-based logic (413, 429, 3xx, 5xx) and implements rate-limit-based backoff. The `Monitor` class implements health checks and backpressure-based downsampling. The `SpotlightClient` implements exponential backoff. However, there is **no formal circuit breaker pattern** — the SDK continues attempting to send events even when the server is returning persistent errors (non-429). The queue-based transport (`BackgroundWorker`) drops events on queue overflow but does not circuit-break.
- **Gap**: No formal circuit breaker implementation. Rate limiting is reactive (based on Sentry's headers) but does not proactively circuit-break on persistent failures.
- **Compensating Controls**:
  - Rate limit handling via `_disabled_until` provides partial circuit-breaking for rate-limited categories
  - `Monitor.check_health()` detects unhealthy transport and downsamples
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement a formal circuit breaker for the transport layer that opens after consecutive failures and half-opens after a configurable delay.
- **Evidence**: `sentry_sdk/transport.py` (_update_rate_limits, on_dropped_event), `sentry_sdk/monitor.py` (check_health, set_downsample_factor), `sentry_sdk/spotlight.py` (exponential backoff)

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: The SDK implements **server-side rate limit compliance** — it parses `x-sentry-rate-limits` and `Retry-After` headers from Sentry's response and stops sending events for rate-limited categories. The `_disabled_until` dict tracks per-category rate limits. The `Monitor` downsamples traces when the transport is unhealthy. However, there is **no client-side rate limiting** — the SDK does not limit how fast callers can invoke `capture_event()`. The transport queue (`DEFAULT_QUEUE_SIZE = 100`) provides backpressure by dropping events when full, but this is overflow handling, not rate limiting.
- **Gap**: No client-side rate limiting on API calls. A runaway agent could overwhelm the SDK's queue. Server-side rate limits are respected but not proactively enforced client-side.
- **Compensating Controls**:
  - Transport queue size (`DEFAULT_QUEUE_SIZE = 100`) limits in-flight events
  - `Batcher.MAX_BEFORE_DROP = 1000` limits buffered items
  - Monitor-based downsampling reduces traffic under backpressure
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add client-side rate limiting at the wrapper layer to prevent agent traffic storms.
- **Evidence**: `sentry_sdk/transport.py` (_disabled_until, _update_rate_limits), `sentry_sdk/consts.py` (DEFAULT_QUEUE_SIZE = 100), `sentry_sdk/_batcher.py` (MAX_BEFORE_DROP), `sentry_sdk/monitor.py`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Built-in limits exist (queue size, batcher limits, event byte limits) but no per-agent configurable transaction limits.
- **Gap**: N/A for read-only scope.
- **Recommendation**: N/A.
- **Evidence**: `sentry_sdk/consts.py`, `sentry_sdk/_batcher.py`, `sentry_sdk/serializer.py`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path. This service is P2 priority.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No draft/pending state. Events are sent or dropped.
- **Gap**: N/A for read-only scope.
- **Recommendation**: N/A.
- **Evidence**: `sentry_sdk/client.py`

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No approval gates. `before_send` provides pre-send filtering but not human approval.
- **Gap**: N/A for read-only scope.
- **Recommendation**: N/A.
- **Evidence**: `sentry_sdk/client.py`

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: Spotlight provides local testing. tox.ini defines comprehensive test environments. No staging environment with production-equivalent data shape.
- **Gap**: No staging environment with realistic data.
- **Recommendation**: Create Docker-based staging with mock Sentry ingest.
- **Evidence**: `sentry_sdk/spotlight.py`, `tox.ini`, `tests/conftest.py`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: EventScrubber with DEFAULT_DENYLIST (31 fields) and DEFAULT_PII_DENYLIST (4 fields). send_default_pii option. Pattern-based, not field-level classification.
- **Gap**: No field-level classification or tagging.
- **Recommendation**: Extend denylist; implement field-level classification.
- **Evidence**: `sentry_sdk/scrubber.py`, `sentry_sdk/client.py`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Data destination controlled by DSN host. SDK does not enforce or validate data residency — it sends data wherever the DSN points. No region check, no cross-region protection, no GDPR-specific configuration.
- **Gap**: No SDK-level residency enforcement. An agent misconfigured with the wrong DSN could send regulated data to an incorrect region.
- **Recommendation**: Document DSN-to-region mapping for agents. Add DSN host validation at wrapper service layer.
- **Evidence**: `sentry_sdk/transport.py`, `sentry_sdk/client.py`

#### DATA-Q3: Selective Query Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has list/query endpoints with potentially unbounded results. SDK is a write-only telemetry client.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q4: System of Record Designations
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway). SDK has no persistent state.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator). Downgraded to INFO for stateless-utility, and since stateless-utility with static/reference data has fixed temporal characteristics, not triggered.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: EventScrubber scrubs event payloads. PII may leak into SDK's own diagnostic logs.
- **Gap**: SDK's own log output not scrubbed for PII.
- **Recommendation**: Add log scrubber for SDK diagnostic output.
- **Evidence**: `sentry_sdk/scrubber.py`, `sentry_sdk/client.py`, `sentry_sdk/utils.py`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: Discarded event tracking, truncation metadata, client reports. No business-level quality metrics.
- **Implication**: Operational quality tracking exists.
- **Recommendation**: Expose discarded event metrics for monitoring.
- **Evidence**: `sentry_sdk/serializer.py`, `sentry_sdk/transport.py`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: Semantic versioning (2.56.0). CHANGELOG.md, MIGRATION_GUIDE.md. Deprecation warnings. No automated breaking-change detection in CI.
- **Gap**: No automated contract testing.
- **Recommendation**: Add API surface snapshot testing.
- **Evidence**: `sentry_sdk/consts.py`, `CHANGELOG.md`, `MIGRATION_GUIDE.md`, `.craft.yml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: ~100+ SPANDATA constants following OpenTelemetry semantic conventions. Fully documented with examples. No legacy abbreviations.
- **Implication**: Excellent for LLM-based reasoning.
- **Recommendation**: Continue following OTel conventions.
- **Evidence**: `sentry_sdk/consts.py` (SPANDATA)

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: py.typed, Sphinx docs, extensive docstrings, TypedDict definitions. No formal data catalog.
- **Implication**: Comprehensive developer documentation. TypedDicts provide machine-readable schema.
- **Recommendation**: Generate machine-readable schema from TypedDicts.
- **Evidence**: `sentry_sdk/py.typed`, `sentry_sdk/_types.py`, `docs/`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: SDK provides distributed tracing and OTel integration for instrumented apps. SDK's own internal logging is unstructured.
- **Gap**: SDK's own internal operations lack structured logging.
- **Recommendation**: Add JSON structured logging to SDK internals.
- **Evidence**: `sentry_sdk/tracing.py`, `sentry_sdk/integrations/opentelemetry/`, `sentry_sdk/logger.py`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: Monitor class detects unhealthy states and adjusts sampling. No alerting thresholds.
- **Gap**: No alerting configured.
- **Recommendation**: Expose health metrics for alerting systems.
- **Evidence**: `sentry_sdk/monitor.py`, `sentry_sdk/transport.py`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: Metrics API (count, gauge, distribution). Client reports for discarded events. No business outcome metrics.
- **Implication**: SDK can emit custom metrics; doesn't emit business metrics about its own operations.
- **Recommendation**: Use metrics API for agent-specific business metrics.
- **Evidence**: `sentry_sdk/metrics.py`, `sentry_sdk/_metrics_batcher.py`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: INFO
- **Finding**: Library published to PyPI, no IaC. Release governance via .craft.yml. Pinned action SHAs.
- **Implication**: N/A for library — release governance is adequate.
- **Recommendation**: N/A.
- **Evidence**: `.craft.yml`, `.github/workflows/ci.yml`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: 24 GitHub Actions workflows. Mypy strict type checking. Codecov. No API contract testing.
- **Gap**: No automated breaking-change detection.
- **Recommendation**: Add API surface snapshot testing.
- **Evidence**: `.github/workflows/ci.yml`, `pyproject.toml`, `codecov.yml`

#### ENG-Q3: Rollback Capability
- **Severity**: INFO
- **Finding**: Consumer-controlled rollback via version pinning. All versions on PyPI.
- **Implication**: Rollback is straightforward.
- **Recommendation**: Document version pinning strategies.
- **Evidence**: `setup.py`, `.craft.yml`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: Extensive test suite (30+ test files, 70+ integration test environments). Coverage informational only.
- **Gap**: Coverage not enforced as PR gate.
- **Recommendation**: Set informational: false in codecov.yml.
- **Evidence**: `tests/`, `codecov.yml`, `pyproject.toml`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent data stores. SDK has no persistent data stores.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `sentry_sdk/__init__.py` | API-Q1 |
| `sentry_sdk/api.py` | API-Q1, API-Q2, AUTH-Q3, DISC-Q1 |
| `sentry_sdk/client.py` | API-Q1, API-Q4, AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q5, AUTH-Q6, AUTH-Q7, DATA-Q1, DATA-Q2, DATA-Q6, STATE-Q1, HITL-Q1, HITL-Q2 |
| `sentry_sdk/transport.py` | API-Q3, API-Q5, API-Q8, AUTH-Q1, AUTH-Q2, AUTH-Q5, AUTH-Q6, AUTH-Q7, DATA-Q2, DATA-Q7, STATE-Q1, STATE-Q4, STATE-Q5, OBS-Q2 |
| `sentry_sdk/consts.py` | API-Q1, API-Q2, AUTH-Q2, DISC-Q1, DISC-Q2, STATE-Q5, STATE-Q6 |
| `sentry_sdk/scrubber.py` | DATA-Q1, DATA-Q6, AUTH-Q5 |
| `sentry_sdk/serializer.py` | API-Q5, DATA-Q7, STATE-Q6 |
| `sentry_sdk/tracing.py` | AUTH-Q4, OBS-Q1 |
| `sentry_sdk/tracing_utils.py` | AUTH-Q4 |
| `sentry_sdk/logger.py` | OBS-Q1 |
| `sentry_sdk/monitor.py` | OBS-Q2, STATE-Q4, STATE-Q5 |
| `sentry_sdk/metrics.py` | OBS-Q3 |
| `sentry_sdk/_batcher.py` | STATE-Q5, STATE-Q6 |
| `sentry_sdk/_metrics_batcher.py` | OBS-Q3 |
| `sentry_sdk/worker.py` | STATE-Q3 |
| `sentry_sdk/spotlight.py` | HITL-Q3, STATE-Q4 |
| `sentry_sdk/envelope.py` | API-Q5 |
| `sentry_sdk/utils.py` | API-Q3, AUTH-Q6, DATA-Q6 |
| `sentry_sdk/_types.py` | DISC-Q3 |
| `sentry_sdk/integrations/opentelemetry/` | OBS-Q1 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/ci.yml` | ENG-Q1, ENG-Q2, ENG-Q4 |
| `.github/workflows/release.yml` | ENG-Q1, ENG-Q3 |
| `.github/workflows/test-integrations-common.yml` | ENG-Q2, ENG-Q4, HITL-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `setup.py` | API-Q1, ENG-Q3 |
| `pyproject.toml` | API-Q2, ENG-Q2, ENG-Q4 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `.craft.yml` | DISC-Q1, ENG-Q1, ENG-Q3 |
| `codecov.yml` | ENG-Q4 |
| `tox.ini` | HITL-Q3, ENG-Q2 |
| `sentry_sdk/py.typed` | API-Q2, DISC-Q3 |

### Documentation
| File | Questions Referenced |
|------|---------------------|
| `CHANGELOG.md` | DISC-Q1 |
| `MIGRATION_GUIDE.md` | DISC-Q1 |
| `README.md` | DISC-Q3 |
| `docs/api.rst` | API-Q2, DISC-Q3 |
