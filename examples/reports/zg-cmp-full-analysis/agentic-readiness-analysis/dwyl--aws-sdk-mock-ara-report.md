# Agentic Readiness Analysis Report

**Target**: aws-sdk-mock
**Date**: 2026-04-29
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**Repository Type**: library
**Service Archetype**: stateless-utility (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: typescript, testing, aws-sdk
**Context**: Mock library for the AWS SDK, used in JS/TS test suites.

**Archetype Justification**: Pure testing utility library providing mock/stub functionality for AWS SDK v3 clients using sinon.js. No database connections, no persistent state, no message queue consumers, no downstream service calls at runtime, and no write operations against external systems.

---

## Readiness Profile: Pilot-Ready (Safety Concerns)

**BLOCKERs**: 0 | **RISK-SAFETY**: 5 | **RISK-QUALITY**: 6 | **INFOs**: 16

Supervised pilot with elevated safety oversight: (1) all Pilot-Ready controls apply, (2) prioritize RISK-SAFETY remediation before expanding agent scope, (3) dedicated safety review cadence, (4) agent restricted to lowest-blast-radius operations until RISK-SAFETY count drops below 3.

> **Library Context Note**: Many RISK-SAFETY findings (AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7, STATE-Q5) reflect controls that are architecturally absent by design in an in-process npm library. These gaps are inherent to the library form factor — libraries do not typically enforce authorization, audit logging, identity management, or rate limiting on their own API. Remediation for these controls should occur at the consuming application or platform layer, not within the library itself.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 0 |
| RISK-SAFETY | 5 |
| RISK-QUALITY | 6 |
| INFO | 16 |
| N/A | 5 |
| Not Evaluated (extended) | 11 |
| **Total** | **43** |

**Core Questions Evaluated**: 21 (24 core minus 3 N/A for library: ENG-Q1, ENG-Q2, ENG-Q3)
**Extended Questions Triggered**: 6 (API-Q5, API-Q8, DATA-Q7, DISC-Q2, DISC-Q3, OBS-Q3)
**Extended Questions Not Triggered**: 11 (API-Q6, API-Q7, STATE-Q2, STATE-Q3, STATE-Q4, STATE-Q7, HITL-Q1, HITL-Q2, DATA-Q3, DATA-Q4, DATA-Q5)
**Questions N/A (repo_type: library)**: 5 (ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4, ENG-Q5)
**Service Archetype**: stateless-utility (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

No BLOCKERs identified.

All three potential BLOCKER questions resolved favorably:
- **API-Q1**: The library exposes a documented programmatic API (mock, remock, restore, setSDK, setSDKInstance) with comprehensive README documentation and TypeScript type definitions.
- **AUTH-Q1**: The library transparently passes through AWS SDK constructor arguments, preserving authentication configuration. As an in-process library, no separate machine identity is required.
- **DATA-Q1**: The library does not store, process, or access sensitive data. Mock data is provided by the test consumer.

---

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The library's API design supports method-level granularity via `mock(service, method, replace)`, which enables scoped usage patterns. However, the library has no authorization model — any in-process caller can invoke any exported function (`mock`, `remock`, `restore`, `setSDK`, `setSDKInstance`) without restriction. There is no mechanism to grant an agent read-only access to specific services while preventing access to others.
- **Gap**: No permission enforcement on the library API. Any caller can mock any AWS service and method.
- **Compensating Controls**:
  - Wrap library calls in a facade layer in the consuming application that enforces scoped access per agent identity.
  - Use the consuming application's IAM/RBAC layer to restrict which agent tools can invoke library functions.
- **Remediation Timeline**: 30–60 days (at the consuming application layer)
- **Recommendation**: Build a thin wrapper around `aws-sdk-mock` that restricts which services and methods a given agent identity is permitted to mock. Enforce at the integration layer, not within the library.
- **Evidence**: `src/index.ts` — `mock()` function accepts any service name string with no authorization check.

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The library supports action-level granularity — `mock('SNS', 'publish', replace)` targets a specific service and method. However, no enforcement mechanism exists to prevent an agent from calling `mock('DynamoDB', 'deleteItem', ...)` when only `mock('DynamoDB', 'getItem', ...)` should be permitted.
- **Gap**: No action-level authorization enforcement. The library cannot distinguish between read and write mock operations.
- **Compensating Controls**:
  - Implement an allowlist of permitted service+method combinations at the agent orchestration layer.
  - Use TypeScript's type system in the consuming application to restrict the allowed service/method pairs at compile time.
- **Remediation Timeline**: 30–60 days (at the consuming application layer)
- **Recommendation**: Create a typed wrapper that restricts the `service` and `method` parameters to an approved allowlist for each agent identity.
- **Evidence**: `src/index.ts` — `mock()`, `remock()`, and `restore()` accept unconstrained string parameters for service and method names. `src/types.ts` — `ClientName` and `MethodName` are typed as `string`.

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The library has no audit logging infrastructure. Two `console.log` calls exist in `restoreService()` and `restoreMethod()` for warning messages when restoring non-existent services/methods, but these are informational warnings, not audit logs. No logging captures which mock operations were performed, by whom, or when.
- **Gap**: No audit trail for mock/remock/restore operations. If an agent calls `mock()` or `restore()`, there is no record of the action.
- **Compensating Controls**:
  - Wrap library calls in a logging middleware at the consuming application layer that records all mock operations with caller identity and timestamp.
  - Use the agent orchestration framework's built-in audit logging to capture tool invocations.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add optional structured logging (e.g., a configurable logger callback) to the library that emits audit events for `mock()`, `remock()`, and `restore()` operations. Alternatively, implement logging in the consuming application's wrapper layer.
- **Evidence**: `src/index.ts` — `restoreService()` line: `console.log('Service ' + service + ' was never instantiated yet you try to restore it.')`. `restoreMethod()` line: `console.log('Method ' + service + ' was never instantiated yet you try to restore it.')`. No other logging exists.

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The library has no concept of agent identity and no mechanism to suspend or revoke access for a specific caller. As an in-process npm library, it does not manage identities — any code that imports the module can call any exported function.
- **Gap**: No identity suspension mechanism. A misbehaving agent cannot be isolated without stopping the entire host process.
- **Compensating Controls**:
  - Implement identity-based access control at the consuming application layer with a kill-switch per agent identity.
  - Use process-level isolation (separate Node.js processes per agent) to enable per-agent suspension.
- **Remediation Timeline**: 60–90 days (architectural change at the consuming application layer)
- **Recommendation**: This gap is inherent to the in-process library form factor. Remediation requires implementing agent identity management at the platform or orchestration layer, not within the library itself.
- **Evidence**: `src/index.ts` — Exported `AWS` object provides unrestricted access to `mock`, `remock`, `restore`, `setSDK`, `setSDKInstance`. No identity or access control logic exists.

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The library has no rate limiting or throttling mechanism. A runaway agent loop could call `mock()` or `restore()` thousands of times per second, consuming memory through unbounded accumulation of mock stubs in the `services` object and `_clientRegistry`.
- **Gap**: No rate limiting on library API calls. The `services` object grows without bounds as mocks are added.
- **Compensating Controls**:
  - Implement rate limiting at the agent orchestration layer to cap the frequency of mock/restore operations.
  - Use `restore()` (which clears accumulated state) between test cycles to prevent unbounded growth.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add an optional configurable limit on the number of active mocks (e.g., `maxMocks` option) that throws an error when exceeded. Alternatively, implement rate limiting in the consuming application's wrapper.
- **Evidence**: `src/index.ts` — `services` object (line: `const services: SERVICES = {};`) accumulates entries without limit. `_clientRegistry` is mutated on each `mockService()` call.

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The library generates TypeScript declaration files (`dist/index.d.ts`) via `tsup` with `dts: true`, and `src/types.ts` exports comprehensive type definitions including `ClientName`, `MethodName`, `ReplaceFn`, `Service`, and `Replace`. These serve as machine-readable interface specifications for TypeScript consumers. However, no formal OpenAPI, AsyncAPI, or standalone API specification file exists.
- **Gap**: No formal API specification beyond TypeScript declarations. Non-TypeScript consumers (or agent frameworks that expect OpenAPI) cannot auto-generate tool definitions from the library's types.
- **Compensating Controls**:
  - Use the TypeScript `.d.ts` files as the primary machine-readable spec for agent tool generation.
  - Manually author tool definitions based on the README documentation.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: For a library, TypeScript declarations are a valid machine-readable specification. Consider adding JSDoc annotations to the exported functions for broader tooling compatibility.
- **Evidence**: `tsup.config.ts` — `dts: true` generates declaration files. `src/types.ts` — exports all type definitions. `package.json` — `"types": "dist/index.d.ts"`.

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The library throws plain `Error` objects with string messages. In `mock()`, an unrecognized service produces `throw new Error('Service ${service} is not recognized. Register it via setSDKInstance().')`. No structured error codes, no error categorization (retriable vs. terminal), and no machine-readable error format.
- **Gap**: No structured error codes or error categorization. An agent consuming this library cannot programmatically distinguish between different error types.
- **Compensating Controls**:
  - Wrap library calls in try/catch at the consuming application layer and classify errors based on message string matching.
  - Document known error messages in the README for agent tool authors.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create custom error classes (e.g., `ServiceNotFoundError`, `MethodNotMockedError`) with error codes and a `retryable` boolean property. This enables agents to handle errors programmatically.
- **Evidence**: `src/index.ts` — `throw new Error('Service ${service} is not recognized. Register it via setSDKInstance().')` in `mock()` function.

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The library has a CI test matrix running across Node.js 18.x, 20.x, and 21.x on Ubuntu, Windows, and macOS via GitHub Actions. Tests can be run locally via `npm test` (Mocha + nyc). Code coverage is enforced at 100% line coverage and 80% branch coverage (`.nycrc`). However, there is no dedicated sandbox/staging environment configuration, no Docker-compose for isolated local testing, and no synthetic data generators.
- **Gap**: No isolated sandbox or staging environment for testing agent interactions with the library. Testing is limited to unit tests in the CI matrix and local development.
- **Compensating Controls**:
  - Use `npm test` locally as a de facto sandbox — the library's test suite validates all mock/restore operations.
  - The library IS a testing tool, so its entire purpose is to enable sandbox-like testing of AWS SDK interactions.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a Docker-compose configuration or a dev container definition for reproducible local testing. Consider adding integration test examples showing how agents interact with the library.
- **Evidence**: `.github/workflows/ci.yml` — CI matrix with 3 Node versions × 3 OSes. `package.json` — `"test": "nyc mocha --require ts-node/register test/**/*.spec.ts && tsd"`. `.nycrc` — 100% line coverage, 80% branch coverage.

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The library uses semantic versioning (`"version": "6.2.2"` in `package.json`). TypeScript type definitions in `src/types.ts` define the API contract. However, there is no CHANGELOG file, no breaking change detection in CI, no consumer-driven contract tests, and no formal deprecation process for API changes.
- **Gap**: No automated breaking change detection. No CHANGELOG. TypeScript types provide implicit versioning but breaking changes to the `mock()`/`restore()` API could silently break agent tool definitions.
- **Compensating Controls**:
  - Rely on semver major version bumps to signal breaking changes.
  - Pin to a specific library version in agent tool dependencies to avoid surprise breakage.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a CHANGELOG.md file. Consider adding a breaking change detection step in CI (e.g., `api-extractor` for TypeScript libraries) that fails the build when public API signatures change.
- **Evidence**: `package.json` — `"version": "6.2.2"`. `src/types.ts` — type definitions for all exported APIs. No CHANGELOG file found. `.github/workflows/ci.yml` — no breaking change detection step.

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The library has no distributed tracing instrumentation (no OpenTelemetry, no X-Ray SDK) and no structured logging. The only logging is two `console.log` calls that output unstructured warning messages when restoring non-existent services. No correlation IDs, no JSON log format, no trace ID propagation.
- **Gap**: No tracing or structured logging. When an agent-initiated mock operation fails, there is no diagnostic trail beyond the thrown error.
- **Compensating Controls**:
  - Implement structured logging in the consuming application's wrapper layer that captures all library interactions.
  - Use the agent orchestration framework's tracing to capture tool invocation context.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add an optional logger interface that consumers can plug in (e.g., `setLogger(logger)`). Emit structured log events for mock/remock/restore operations with correlation ID support.
- **Evidence**: `src/index.ts` — Two `console.log` calls in `restoreService()` and `restoreMethod()`. No OpenTelemetry, X-Ray, or structured logging imports.

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The library has no alerting configuration. As an in-process npm library, it does not have its own monitoring infrastructure. Error rates and latency of mock operations are not tracked or alertable.
- **Gap**: No alerting on library operation failures. Degradation (e.g., slow mock setup due to registry growth) would go undetected.
- **Compensating Controls**:
  - Implement monitoring at the consuming application layer that tracks mock operation latency and error rates.
  - Use npm package health monitoring (Snyk, Codecov badges are already present).
- **Remediation Timeline**: 60–90 days
- **Recommendation**: This gap is inherent to the library form factor. Alerting should be implemented at the consuming application or agent orchestration layer. The library could expose metrics hooks for consumers to instrument.
- **Evidence**: No monitoring or alerting configuration found in any repository file. `.github/workflows/ci.yml` — Codecov integration exists for test coverage only.

---

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO
- **Finding**: The library exposes a well-documented programmatic API through five exported functions: `mock(service, method, replace)`, `remock(service, method, replace)`, `restore(service?, method?)`, `setSDK(path)`, and `setSDKInstance(sdk)`. The `README.md` provides comprehensive documentation with parameter tables, usage examples (JavaScript, TypeScript, Sinon), and behavioral notes. TypeScript type definitions in `src/types.ts` provide programmatic interface documentation. This is a programmatic API (not REST/GraphQL), which is the correct interface pattern for an npm library.
- **Implication**: Agents consuming this library can bind to a stable, well-documented interface. Tool definitions can be generated from the README documentation and TypeScript declarations.
- **Recommendation**: No action required. The documented interface is comprehensive for the library form factor.
- **Evidence**: `README.md` — API documentation with parameter tables for all 5 exported functions. `src/types.ts` — full type definitions. `src/index.ts` — exports `AWS` object with all functions.

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The library's `mock()` function is partially idempotent: calling `mock('SNS', 'publish', fn1)` then `mock('SNS', 'publish', fn2)` does NOT replace the first mock — the second call is ignored for the method (though the service stub remains). `restore()` followed by `mock()` is the correct re-mock pattern, or `remock()` should be used. The `restore()` function is idempotent — calling it multiple times on already-restored services produces only a console warning.
- **Implication**: Agent tool authors should use `remock()` for updating existing mocks and `restore()` before re-mocking. The partial idempotency of `mock()` could cause confusion if not documented in tool definitions.
- **Recommendation**: Document the idempotency behavior in agent tool definitions. Prefer `remock()` for update operations.
- **Evidence**: `src/index.ts` — `mock()` function: `if (!serviceObj.methodMocks[methodName])` guard prevents re-registration. `remock()` function explicitly restores then re-mocks. `test/index.spec.ts` — "method is not re-mocked if a mock already exists" test validates this behavior.

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: Library functions return JavaScript objects. `mock()` returns a `Replace` object containing `{ replace: ReplaceFn, stub?: SinonStub }`. `remock()` returns the same structure. `restore()` returns `void`. `setSDK()` returns `Promise<void>`. `setSDKInstance()` returns `void`. All return types are defined in `src/types.ts`.
- **Implication**: Return types are well-defined TypeScript objects — ideal for agent consumption. No serialization/deserialization overhead since the library is consumed in-process.
- **Recommendation**: No action required. In-process JavaScript objects are the optimal response format for a library.
- **Evidence**: `src/types.ts` — `Replace` type definition. `src/index.ts` — function signatures with return types.

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: The library has no rate limits, which is expected for an in-process npm testing utility. There are no network calls, no HTTP headers, and no throttling configuration.
- **Implication**: Agents can call library functions at any frequency without rate limit concerns. However, unbounded `mock()` calls accumulate state in the `services` object (see STATE-Q5).
- **Recommendation**: Document that the library has no rate limits but that callers should call `restore()` between test cycles to prevent memory accumulation.
- **Evidence**: `src/index.ts` — no rate limiting logic. `package.json` — no rate limiting dependencies.

### AUTH-Q1: Machine Identity Authentication

- **Severity**: INFO
- **Finding**: The library transparently passes through AWS SDK constructor arguments to the underlying client constructors. When `mock('SNS', 'publish', replace)` is called and a new `SNSClient` is instantiated, the constructor arguments (including credentials, region, endpoint) are forwarded to the real `SNSClient` constructor via `new OriginalConstructor(...args)`. The library does not add, remove, or modify authentication configuration.
- **Implication**: Machine identity authentication is handled by the AWS SDK itself, not the library. This is the correct architecture — the library delegates auth to the SDK layer.
- **Recommendation**: No action required. The pass-through pattern preserves the consuming application's auth configuration.
- **Evidence**: `src/index.ts` — `mockService()` function: `const client = new OriginalConstructor(...args)` passes through all constructor arguments. `defaultClientRegistry` maps service names to real AWS SDK v3 client classes.

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: INFO
- **Scope-Calibrated**: Archetype `stateless-utility` — downgraded to INFO
- **Finding**: The library does not handle identity propagation. It operates in-process and does not make network calls or propagate tokens. The mocked AWS SDK clients inherit whatever identity context the consuming application provides.
- **Implication**: Identity propagation is not applicable to this library's function. The consuming application is responsible for managing identity context.
- **Recommendation**: No action required for the library. Ensure identity propagation is handled at the consuming application layer.
- **Evidence**: `src/index.ts` — no JWT parsing, no token exchange, no identity headers. Library operates entirely in-process.

### AUTH-Q5: Credential Management

- **Severity**: INFO
- **Finding**: No hardcoded credentials, API keys, passwords, or secrets were found in any repository file. The library's source code contains no credential patterns (`password=`, `secret=`, `api_key=`). No `.env` files exist. The `.gitignore` properly excludes `node_modules/`, `dist/`, and `.nyc_output`. The only secret reference is `${{ secrets.CODECOV_TOKEN }}` in the CI workflow, which uses GitHub Actions' built-in secrets management.
- **Implication**: The library follows good credential hygiene. No remediation needed.
- **Recommendation**: No action required. Continue using GitHub Actions secrets for CI tokens.
- **Evidence**: `src/index.ts` — no credential patterns. `.gitignore` — excludes sensitive directories. `.github/workflows/ci.yml` — uses `${{ secrets.CODECOV_TOKEN }}` (proper secrets management).

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY, but control is present → INFO
- **Finding**: The library provides robust compensation/rollback through the `restore()` function. `restore()` can roll back a single method mock, an entire service's mocks, or all mocks across all services. The `restoreMethod()` function calls `mockedClientMethod.restore()` on sinon stubs and removes the method from `methodMocks`. The `restoreService()` function restores the original client constructor in `_clientRegistry` and deletes the service from `services`. This is a comprehensive rollback mechanism.
- **Implication**: Agents can safely call `restore()` to undo any mock operations. The rollback is granular (method-level, service-level, or global).
- **Recommendation**: No action required. The `restore()` API provides excellent compensation capability. Document the rollback granularity in agent tool definitions.
- **Evidence**: `src/index.ts` — `restore()`, `restoreService()`, `restoreAllMethods()`, `restoreMethod()` functions. `test/index.spec.ts` — multiple tests validate restore behavior at all granularity levels.

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The library has no configurable transaction limits. As a testing utility consumed in read-only agent scope, blast radius concerns are minimal — the library modifies only in-process mock state, not external systems.
- **Implication**: For read-only scope, transaction limits are not a concern. If scope expands to write-enabled, consider adding limits on the number of concurrent mocks.
- **Recommendation**: No action required for read-only scope.
- **Evidence**: `src/index.ts` — no transaction limit logic. `services` object grows without limit.

### DATA-Q1: Sensitive Data Classification

- **Severity**: INFO
- **Finding**: The library does not store, process, or access sensitive data (PII, PHI, financial records, credentials). It provides mock/stub functionality — the mock data is entirely provided by the test consumer via the `replace` parameter in `mock(service, method, replace)`. The library holds mock stubs in memory during test execution and clears them on `restore()`.
- **Implication**: No data classification controls are needed within the library itself. The consuming application is responsible for ensuring test data does not contain real PII.
- **Recommendation**: Add a note in documentation advising consumers not to use real sensitive data as mock replacement values.
- **Evidence**: `src/index.ts` — `mock()` accepts a `replace` parameter provided by the caller. The library stores this value in `services[service].methodMocks[method].replace` — it does not generate, fetch, or classify data.

### DATA-Q2: Data Residency and Sovereignty ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY, but no gap exists → INFO
- **Finding**: The library operates entirely in-process within the host Node.js runtime. It does not transmit data to external services, does not make network calls, and does not store data outside of the process memory. No data residency or sovereignty concerns exist.
- **Implication**: No data residency controls are needed. The library's data scope is confined to the host process memory.
- **Recommendation**: No action required.
- **Evidence**: `src/index.ts` — no HTTP clients, no network calls, no external data transmission. All state is held in `services` and `_clientRegistry` in-process objects.

### DATA-Q6: PII Redaction in Logs

- **Severity**: INFO
- **Finding**: The library has exactly two `console.log` statements, both in error-path warning messages: (1) `restoreService()`: `'Service ' + service + ' was never instantiated yet you try to restore it.'` (2) `restoreMethod()`: `'Method ' + service + ' was never instantiated yet you try to restore it.'` The `service` parameter is a service name string (e.g., "SNS", "DynamoDB") — not user data or PII. No other logging exists. No PII can leak through these log statements.
- **Implication**: PII redaction is effectively handled — no PII is present in any log output. The library's logging is minimal and safe.
- **Recommendation**: No action required. Consider replacing `console.log` with an optional structured logger for consistency, but PII risk is negligible.
- **Evidence**: `src/index.ts` — `restoreService()`: `console.log('Service ' + service + ' was never instantiated...')`. `restoreMethod()`: `console.log('Method ' + service + ' was never instantiated...')`. No other logging found.

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: The library does not manage datasets and has no data quality metrics. Mock data quality is determined entirely by the test consumer. The library enforces type safety through TypeScript types but does not validate the semantic quality of mock data provided via the `replace` parameter.
- **Implication**: Data quality is the consuming application's responsibility. Agent tool definitions should document expected data formats for mock replacement values.
- **Recommendation**: No action required for the library. Consider adding runtime type validation for the `replace` parameter to catch common misuse patterns.
- **Evidence**: `src/types.ts` — `ReplaceFn` type allows `function | string | object` — broad type acceptance with no runtime validation.

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: The library uses clear, semantically meaningful names throughout. Exported API function names (`mock`, `remock`, `restore`, `setSDK`, `setSDKInstance`) are self-descriptive. Type names in `src/types.ts` are human-readable: `ClientName`, `MethodName`, `ReplaceFn`, `AWSCallback`, `AWSRequest`, `Service`, `Replace`, `MethodMock`. Internal variables use descriptive names: `_clientRegistry`, `defaultClientRegistry`, `services`, `methodMocks`.
- **Implication**: Agent tool definitions can use the library's naming directly without translation. No data dictionary is needed.
- **Recommendation**: No action required. Naming conventions are excellent.
- **Evidence**: `src/types.ts` — all type names are semantically meaningful. `src/index.ts` — function names (`mock`, `remock`, `restore`) and variable names (`services`, `_clientRegistry`, `methodMocks`) are self-descriptive.

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: The library has no formal data catalog or metadata layer. `README.md` provides comprehensive usage documentation with parameter tables for all exported functions. `src/types.ts` serves as the type catalog. No AWS Glue Data Catalog, DataHub, or other metadata systems are present (expected for a library).
- **Implication**: Documentation is adequate for agent tool definition. The README and TypeScript types together provide sufficient metadata for tool generation.
- **Recommendation**: No action required. Consider adding a `TYPES.md` or API reference documentation for complex type definitions.
- **Evidence**: `README.md` — parameter tables for all 5 functions. `src/types.ts` — comprehensive type definitions.

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: The library has no business outcome metrics. As a testing utility library, business metrics are not applicable — the library's "business outcome" is enabling test mocking, which is measured by test pass/fail rates in the consuming application. Codecov coverage reporting exists in CI.
- **Implication**: Agent effectiveness when using this library should be measured at the consuming application layer (e.g., test coverage improvement, test execution time).
- **Recommendation**: No action required. Consider publishing npm download metrics or usage telemetry as library health indicators.
- **Evidence**: `.github/workflows/ci.yml` — Codecov coverage upload. `.nycrc` — coverage thresholds (100% lines, 80% branches).

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: The library exposes a documented programmatic API with five functions: `mock(service, method, replace)`, `remock(service, method, replace)`, `restore(service?, method?)`, `setSDK(path)`, and `setSDKInstance(sdk)`. README.md provides comprehensive documentation with parameter tables, usage examples in JavaScript and TypeScript, and behavioral notes. TypeScript declarations are generated via tsup (`dts: true`). This is a programmatic API (in-process npm module), which is the correct integration pattern for a library.
- **Gap**: No gap. The documented interface is comprehensive.
- **Recommendation**: No action required.
- **Evidence**: `README.md`, `src/index.ts`, `src/types.ts`, `tsup.config.ts`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: TypeScript declaration files (`dist/index.d.ts`) are generated by tsup with `dts: true`. `src/types.ts` exports comprehensive type definitions. However, no formal OpenAPI, AsyncAPI, or standalone specification file exists. For a library, `.d.ts` files serve as the primary machine-readable spec.
- **Gap**: No formal API specification file beyond TypeScript declarations. Non-TypeScript agent frameworks cannot auto-discover the API.
- **Recommendation**: Add JSDoc annotations to all exported functions. Consider generating API documentation from types using TypeDoc.
- **Evidence**: `tsup.config.ts` — `dts: true`. `src/types.ts` — type exports. `package.json` — `"types": "dist/index.d.ts"`.

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: The library throws plain `Error` objects: `throw new Error('Service ${service} is not recognized. Register it via setSDKInstance().')`. No structured error codes, no error categorization (retriable vs. terminal), no machine-readable error format.
- **Gap**: No structured error codes or categories. Agents cannot programmatically distinguish error types.
- **Recommendation**: Create custom error classes (`ServiceNotFoundError`, `MethodNotMockedError`) with `code` and `retryable` properties.
- **Evidence**: `src/index.ts` — `mock()` function throws plain `Error`.

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: `mock()` is partially idempotent — re-mocking the same service+method is silently ignored. `restore()` is idempotent — restoring already-restored services produces a console warning. `remock()` is the designed pattern for updating existing mocks.
- **Gap**: N/A for read-only scope.
- **Recommendation**: Document idempotency behavior in agent tool definitions.
- **Evidence**: `src/index.ts` — `mock()` guard: `if (!serviceObj.methodMocks[methodName])`. `test/index.spec.ts` — "method is not re-mocked if a mock already exists".

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: Functions return JavaScript objects (`Replace` type with `replace` and `stub` fields), `void`, or `Promise<void>`. All types defined in `src/types.ts`. In-process consumption means no serialization overhead.
- **Gap**: No gap for in-process library consumption.
- **Recommendation**: No action required.
- **Evidence**: `src/types.ts` — `Replace` type. `src/index.ts` — function return types.

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
- **Finding**: Library has no rate limits (expected for an in-process testing utility). No HTTP headers, no throttling configuration.
- **Gap**: No rate limit documentation, but none is needed for an in-process library.
- **Recommendation**: Document that callers should use `restore()` between test cycles to manage memory.
- **Evidence**: `src/index.ts` — no rate limiting logic. `package.json` — no rate limiting dependencies.

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: The library transparently passes through AWS SDK constructor arguments to real client constructors via `new OriginalConstructor(...args)` in `mockService()`. Authentication configuration (credentials, region, endpoint) is preserved. As an in-process library, no separate machine identity is required — the library delegates auth to the AWS SDK layer.
- **Gap**: No gap. Pass-through authentication is the correct pattern for an in-process library.
- **Recommendation**: No action required.
- **Evidence**: `src/index.ts` — `mockService()`: `const client = new OriginalConstructor(...args)`. `defaultClientRegistry` maps to real AWS SDK v3 clients.

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: The library supports method-level granularity (`mock(service, method, replace)`) but has no authorization model. Any in-process caller can invoke any exported function without restriction.
- **Gap**: No permission enforcement on the library API.
- **Recommendation**: Build a wrapper that restricts which services/methods agents can mock.
- **Evidence**: `src/index.ts` — `mock()` accepts any service name. `src/types.ts` — `ClientName = string` (unconstrained).

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: `mock(service, method, replace)` supports action-level granularity, but no enforcement prevents calling `mock('DynamoDB', 'deleteItem', ...)` when only read operations should be permitted.
- **Gap**: No action-level authorization enforcement.
- **Recommendation**: Implement an allowlist wrapper for permitted service+method combinations.
- **Evidence**: `src/index.ts` — `mock()`, `remock()`, `restore()` accept unconstrained strings. `src/types.ts` — `MethodName = string`.

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Scope-Calibrated**: Archetype `stateless-utility` — downgraded to INFO
- **Finding**: Library operates in-process. No identity propagation, no token exchange, no network calls.
- **Gap**: Not applicable for in-process library.
- **Recommendation**: No action required.
- **Evidence**: `src/index.ts` — no JWT, no OAuth, no token handling.

#### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: No hardcoded credentials found in any source file. No `.env` files. CI uses GitHub Actions secrets (`${{ secrets.CODECOV_TOKEN }}`). `.gitignore` excludes `node_modules/`, `dist/`, `.nyc_output`.
- **Gap**: No gap. Credential hygiene is good.
- **Recommendation**: No action required.
- **Evidence**: `src/index.ts`, `.gitignore`, `.github/workflows/ci.yml` — `${{ secrets.CODECOV_TOKEN }}`.

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No audit logging. Two `console.log` calls output warnings when restoring non-existent services. No logging captures mock/remock/restore operations.
- **Gap**: No audit trail for library operations.
- **Recommendation**: Add optional structured logging or a logger callback for mock operations.
- **Evidence**: `src/index.ts` — `console.log` in `restoreService()` and `restoreMethod()` only.

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: No identity management. Any code importing the module can call any function. No suspension/revocation mechanism.
- **Gap**: No identity suspension capability.
- **Recommendation**: Implement identity-based access control at the consuming application layer.
- **Evidence**: `src/index.ts` — exported `AWS` object provides unrestricted access.

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY; control present → INFO
- **Finding**: `restore()` provides comprehensive rollback: method-level (`restore('SNS', 'publish')`), service-level (`restore('SNS')`), and global (`restore()`). `restoreMethod()` calls `mockedClientMethod.restore()` on sinon stubs. `restoreService()` restores original constructors in `_clientRegistry`.
- **Gap**: No gap. Compensation mechanism is robust and well-tested.
- **Recommendation**: No action required.
- **Evidence**: `src/index.ts` — `restore()`, `restoreService()`, `restoreAllMethods()`, `restoreMethod()`. `test/index.spec.ts` — extensive restore tests.

#### STATE-Q2: Queryable Current State
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q3: Concurrency Controls
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled AND service has persistent state
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has external dependencies (calls other services or external APIs)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No rate limiting or throttling. The `services` object and `_clientRegistry` grow without bounds as mocks are added. A runaway agent loop could accumulate thousands of mock entries.
- **Gap**: No rate limiting on library API calls.
- **Recommendation**: Add optional `maxMocks` configuration. Implement rate limiting at the wrapper layer.
- **Evidence**: `src/index.ts` — `services` object grows without limit. No rate limiting logic.

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits. Blast radius is limited to in-process mock state.
- **Gap**: No gap for read-only scope.
- **Recommendation**: No action required for read-only scope.
- **Evidence**: `src/index.ts` — no transaction limit logic.

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
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
- **Severity**: RISK-QUALITY
- **Finding**: CI matrix tests across 3 Node.js versions (18.x, 20.x, 21.x) and 3 OSes (Ubuntu, Windows, macOS). Local testing via `npm test`. Coverage enforced at 100% lines, 80% branches. No dedicated sandbox/staging environment or Docker-compose.
- **Gap**: No isolated sandbox for agent interaction testing.
- **Recommendation**: Add Docker-compose or dev container for reproducible testing. Add agent integration test examples.
- **Evidence**: `.github/workflows/ci.yml`, `package.json` — test scripts, `.nycrc` — coverage thresholds.

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO
- **Finding**: The library does not handle sensitive data. Mock data is entirely provided by test consumers via the `replace` parameter. The library holds mock stubs in memory and clears them on `restore()`.
- **Gap**: No gap. No sensitive data is processed.
- **Recommendation**: Document that consumers should not use real PII as mock values.
- **Evidence**: `src/index.ts` — `mock()` `replace` parameter is caller-provided. `src/types.ts` — `ReplaceFn` type.

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY; no gap exists → INFO
- **Finding**: Library operates in-process. No data transmission, no external service calls, no cross-region data movement.
- **Gap**: No gap. No data residency concerns.
- **Recommendation**: No action required.
- **Evidence**: `src/index.ts` — no HTTP clients, no network calls.

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
- **Finding**: Two `console.log` calls output service names only (e.g., "Service SNS was never instantiated..."). No PII, user data, or sensitive information is logged. No other logging exists.
- **Gap**: No gap. No PII is present in logs.
- **Recommendation**: Consider replacing `console.log` with an optional structured logger.
- **Evidence**: `src/index.ts` — `restoreService()` and `restoreMethod()` console.log calls.

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics. Mock data quality is determined by the test consumer. TypeScript types provide compile-time type safety for the `replace` parameter.
- **Gap**: No runtime data quality validation.
- **Recommendation**: Consider adding runtime type validation for the `replace` parameter.
- **Evidence**: `src/types.ts` — `ReplaceFn` type.

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: Semantic versioning in `package.json` (v6.2.2). TypeScript types define API contracts. No CHANGELOG, no breaking change detection in CI, no consumer-driven contract tests.
- **Gap**: No automated breaking change detection. No CHANGELOG.
- **Recommendation**: Add CHANGELOG.md. Add `api-extractor` to CI for TypeScript API surface change detection.
- **Evidence**: `package.json` — `"version": "6.2.2"`. `src/types.ts`. `.github/workflows/ci.yml` — no breaking change step.

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: All names are semantically meaningful: `mock`, `remock`, `restore`, `setSDK`, `setSDKInstance`, `ClientName`, `MethodName`, `ReplaceFn`, `Service`, `Replace`, `MethodMock`.
- **Gap**: No gap.
- **Recommendation**: No action required.
- **Evidence**: `src/types.ts`, `src/index.ts`.

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: README.md provides comprehensive documentation. `src/types.ts` serves as type catalog. No formal metadata system (expected for library).
- **Gap**: No formal data catalog.
- **Recommendation**: Consider generating API docs with TypeDoc.
- **Evidence**: `README.md`, `src/types.ts`.

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: No OpenTelemetry, no X-Ray, no structured logging. Two `console.log` calls output unstructured warning messages. No correlation IDs, no JSON log format.
- **Gap**: No tracing or structured logging.
- **Recommendation**: Add optional logger interface (`setLogger(logger)`) with structured event emission.
- **Evidence**: `src/index.ts` — `console.log` in `restoreService()` and `restoreMethod()`. No tracing imports.

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: No alerting configuration. Library has no monitoring infrastructure (expected for in-process library).
- **Gap**: No alerting on library operation failures.
- **Recommendation**: Implement monitoring at the consuming application layer. Library could expose metrics hooks.
- **Evidence**: No monitoring configuration found. `.github/workflows/ci.yml` — Codecov for coverage only.

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No business metrics. Codecov coverage reporting in CI. Library's "business outcome" is enabling test mocking.
- **Gap**: No business metrics (acceptable for library).
- **Recommendation**: No action required.
- **Evidence**: `.github/workflows/ci.yml` — Codecov upload. `.nycrc` — coverage thresholds.

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: N/A
- **Finding**: This is a `library` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: N/A
- **Finding**: This is a `library` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q3: Rollback Capability
- **Severity**: N/A
- **Finding**: This is a `library` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q4: API Test Coverage
- **Severity**: N/A
- **Finding**: This is a `library` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: N/A
- **Finding**: This is a `library` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `src/index.ts` | API-Q1, API-Q2, API-Q3, API-Q4, API-Q5, API-Q8, AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q5, STATE-Q6, DATA-Q1, DATA-Q2, DATA-Q6, DISC-Q2, OBS-Q1 |
| `src/types.ts` | API-Q1, API-Q2, API-Q5, AUTH-Q2, AUTH-Q3, DATA-Q1, DATA-Q7, DISC-Q1, DISC-Q2, DISC-Q3 |
| `test/index.spec.ts` | API-Q4, STATE-Q1 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/ci.yml` | AUTH-Q5, HITL-Q3, DISC-Q1, OBS-Q2, OBS-Q3 |
| `.github/dependabot.yml` | (referenced in discovery; no direct question citation) |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `package.json` | API-Q1, API-Q2, API-Q8, AUTH-Q5, HITL-Q3, DISC-Q1 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `tsup.config.ts` | API-Q2 |
| `.nycrc` | HITL-Q3, OBS-Q3 |
| `tsconfig.json` | (referenced in discovery; TypeScript configuration context) |
| `.eslintrc.json` | (referenced in discovery; code quality context) |
| `.gitignore` | AUTH-Q5 |

### Documentation
| File | Questions Referenced |
|------|---------------------|
| `README.md` | API-Q1, DISC-Q3 |
