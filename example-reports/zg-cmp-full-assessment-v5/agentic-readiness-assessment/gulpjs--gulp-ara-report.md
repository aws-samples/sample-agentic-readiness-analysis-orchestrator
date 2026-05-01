# Agentic Readiness Assessment Report

**Target**: gulp (gulpjs/gulp)
**Date**: 2026-04-30
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**TD Version**: 3g1ipe93e5d2wb6n5d4yqaf9
**Repository Type**: application
**Service Archetype**: stateless-utility (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: javascript, build-tool
**Context**: Streaming JavaScript build-system toolkit.

**Archetype Justification**: Gulp is a local filesystem streaming build tool with no database connections, no HTTP server, no message queue consumers, and no user-specific context. All operations (src, dest, watch, series, parallel) are local file transformations and task orchestration — pure-function build automation with no persistent state.

**Surface flags**:
- has_persistent_data_store: false
- has_http_rpc_surface: false
- has_auth_surface: false
- has_write_operations: false
- has_logging_of_user_data: false

> **INFO — Dev-Library-Application Override Applied**: This repository is classified as `repo_type: application` but functions as a build-system toolkit (library/CLI). The `service_archetype` is `stateless-utility` and all 5 surface flags are `false`. Per the ARA dev-library-application override, surface-flag downgrades are applied throughout the assessment. The original `repo_type` value (`application`) is preserved; this override affects scoring only.

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
**Extended Questions Triggered**: 8 (all resolved to INFO)
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
- **Finding**: Gulp follows semver versioning (currently v5.0.1 per `package.json`). The `CHANGELOG.md` documents breaking changes extensively (e.g., v5.0.0 lists 15+ breaking changes under "⚠ BREAKING CHANGES"). The `release-please` GitHub Action (`.github/workflows/release.yml`) automates release versioning. However, no TypeScript type declarations are published (no `.d.ts` files, no `types` field in `package.json`), and no automated breaking-change detection tool (e.g., `arethetypeswrong`, API-extractor, or consumer-driven contract tests like Pact) runs in CI.
- **Gap**: No automated breaking-change detection in CI pipeline. No TypeScript type declarations for typed consumption. Agent tool bindings based on the gulp API could break silently if a minor release inadvertently changes export signatures.
- **Compensating Controls**:
  - Semver discipline and release-please automation provide manual-but-reliable version gating — consumers can pin to `^5.0.0` and review CHANGELOG before upgrading.
  - The API surface is small and stable (10 exported functions unchanged since v4).
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add TypeScript declaration files (`.d.ts`) to enable typed consumption and consider adding an API snapshot test or `api-extractor` to CI to detect unintended export changes.
- **Evidence**: `package.json` (version field, exports field — no `types`), `CHANGELOG.md` (breaking changes documented), `.github/workflows/release.yml` (release-please automation), `index.js` (10 exports), `index.mjs` (ESM re-exports)

---

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO
- **Finding**: Gulp exposes a well-documented programmatic JavaScript API with 10 functions (`src`, `dest`, `symlink`, `watch`, `task`, `series`, `parallel`, `lastRun`, `tree`, `registry`) exported from `index.js` and `index.mjs`. Comprehensive API documentation exists in `docs/api/` with individual pages for each function. However, there is no REST, GraphQL, or AsyncAPI interface — this is a local build tool invoked programmatically or via CLI, not a network-callable service.
- **Implication**: Agents would consume gulp as a programmatic dependency (imported in a gulpfile), not as a network API. Agent tool bindings would wrap CLI invocations (`gulp <task>`) rather than HTTP calls. The well-documented API surface is a strength for tool definition.
- **Recommendation**: No action needed. The programmatic API is well-documented for its use case.
- **Evidence**: `index.js`, `index.mjs`, `docs/api/README.md`, `docs/api/src.md`, `docs/api/dest.md`, `docs/api/watch.md`

### API-Q2: Machine-Readable API Specification

- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — machine-readable spec is not applicable. Gulp has no OpenAPI, AsyncAPI, or GraphQL schema because it is not a network service. The API contract is expressed through CommonJS/ESM exports in `index.js`/`index.mjs` and human-readable Markdown documentation in `docs/api/`.
- **Implication**: Agent tool definitions would be authored manually from documentation rather than auto-generated from a spec. For a build tool consumed as a dependency, this is standard practice.
- **Recommendation**: No action needed. DISC-Q1 evaluates the package-level contract stability that matters for library consumers.
- **Evidence**: `index.js`, `index.mjs`, `docs/api/README.md`

### API-Q3: Structured Error Responses

- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — structured error responses are not applicable. Gulp communicates errors via JavaScript exceptions (e.g., `throw new Error('watching ' + glob + ': watch task has to be...')` in `index.js` line 33). Error messages are descriptive strings, not structured error objects with codes.
- **Implication**: Libraries communicate failure via thrown exceptions, which is the standard pattern for JavaScript packages. Consuming applications handle these errors in their own error handling layer.
- **Recommendation**: No action needed for ARA purposes.
- **Evidence**: `index.js` (error throw pattern in watch method)

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Read-only agent scope — idempotency of write operations is informational only. Gulp's `dest()` function writes files to the filesystem, which is inherently idempotent (overwriting produces the same result). The `overwrite` option in `dest()` controls this behavior.
- **Implication**: For read-only agent operations, idempotency is not a concern. If agent scope were expanded to write-enabled, gulp's file-based writes are naturally idempotent.
- **Recommendation**: No action needed.
- **Evidence**: `index.js`, `docs/api/dest.md` (overwrite option)

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: Gulp operates on Node.js streams of Vinyl file objects — a structured, typed in-memory format with `path`, `contents`, `stat`, `cwd`, `base` properties. This is not JSON/XML over HTTP; it is an in-process streaming data model well-suited for programmatic consumption.
- **Implication**: Agents consuming gulp would work with Vinyl stream objects, not HTTP response bodies. The structured nature of Vinyl objects is a strength for programmatic integration.
- **Recommendation**: No action needed.
- **Evidence**: `index.js`, `docs/api/vinyl.md`, `docs/api/concepts.md`

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — API rate limiting is not applicable. Gulp is a local build tool with no network API layer. Execution speed is bounded by local filesystem I/O and CPU, not rate limits.
- **Implication**: When agents invoke gulp tasks, throughput is limited by the local machine's resources, not by rate limiting infrastructure.
- **Recommendation**: No action needed.
- **Evidence**: `index.js`, `bin/gulp.js`

### AUTH-Q1: Machine Identity Authentication

- **Severity**: INFO
- **Finding**: System does not execute agent-invoked operations over a network — authentication is a consumer responsibility. Gulp is a local build tool with no authentication mechanism. It runs under the identity of the local user or CI/CD runner that invokes it. No OAuth, API key, mTLS, or service account patterns exist in the codebase.
- **Implication**: Authentication for agent-initiated gulp invocations would be handled at the CI/CD or orchestration layer (e.g., GitHub Actions runner identity, AWS CodeBuild role), not by gulp itself.
- **Recommendation**: No action needed for the library. Consumer applications that orchestrate gulp should ensure proper identity attribution.
- **Evidence**: `index.js`, `bin/gulp.js`, `package.json` (no auth dependencies)

### AUTH-Q2: Scoped Permissions (Least Privilege)

- **Severity**: INFO
- **Finding**: System does not enforce authorization — permission scoping is a consumer responsibility. Gulp has no authorization model. It operates with whatever filesystem permissions the invoking process has. No IAM policies, role definitions, or permission checks exist in the codebase.
- **Implication**: Scoped permissions for agent access to gulp would be enforced at the OS/container level (filesystem permissions) or CI/CD level (runner role), not by gulp itself.
- **Recommendation**: No action needed for the library.
- **Evidence**: `index.js`, `package.json`

### AUTH-Q3: Action-Level Authorization

- **Severity**: INFO
- **Finding**: System does not enforce action-level authorization — this is a consumer responsibility. Gulp exposes all functions (`src`, `dest`, `watch`, `series`, `parallel`, `task`) without any permission checks. Any caller can invoke any function.
- **Implication**: If an agent should only read files (via `src`) but not write (via `dest`), this restriction must be enforced at the orchestration layer, not by gulp.
- **Recommendation**: No action needed for the library.
- **Evidence**: `index.js`, `index.mjs`

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: INFO
- **Finding**: Archetype calibration: stateless-utility — identity propagation is not applicable. Gulp does not make network calls to downstream services and does not process user-specific data. There is no identity context to propagate.
- **Implication**: No identity propagation concerns for a local build tool.
- **Recommendation**: No action needed.
- **Evidence**: `index.js`, `package.json` (no HTTP client dependencies)

### AUTH-Q5: Credential Management

- **Severity**: INFO
- **Finding**: No hardcoded credentials found in source code. Searched all source files (`index.js`, `index.mjs`, `bin/gulp.js`) and configuration files (`.npmrc`, `.editorconfig`, `eslint.config.js`) — no patterns matching `password=`, `secret=`, `api_key=`, `token=` were found. The `.npmrc` contains only `package-lock=false`. CI/CD workflows reference `secrets.GITHUB_TOKEN` (standard GitHub Actions), `secrets.ATXCI_API_URL`, and `secrets.ATXCI_API_KEY` via GitHub Secrets — not hardcoded.
- **Implication**: No credential management concerns for the library itself. CI/CD credentials are properly managed via GitHub Secrets.
- **Recommendation**: No action needed. Good practice observed.
- **Evidence**: `.npmrc`, `.github/workflows/dev.yml` (secrets references), `index.js`, `bin/gulp.js`

### AUTH-Q6: Immutable Audit Logging ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity RISK-SAFETY, but dev-library-application override applied
- **Finding**: System does not execute agent-invoked write operations — audit logging is a consumer responsibility. The library/utility is called by applications that own the audit context. Gulp has no audit logging mechanism — it is a local build tool that writes build output to the filesystem. No CloudTrail, CloudWatch, or structured audit log configuration exists.
- **Implication**: Audit logging for agent-initiated build operations would be handled by the CI/CD platform (GitHub Actions audit logs, AWS CloudTrail for CodeBuild), not by gulp itself.
- **Recommendation**: No action needed for the library.
- **Evidence**: `index.js`, `package.json`, `.github/workflows/dev.yml`

### AUTH-Q7: Agent Identity Suspension

- **Severity**: INFO
- **Finding**: System does not issue or enforce agent identities — suspension is a consumer responsibility. Libraries and utilities are invoked by applications that own identity lifecycle. Gulp has no identity management — there are no API keys, service accounts, or identity tokens to suspend.
- **Implication**: If an agent's access to gulp needs to be revoked, this would be done at the CI/CD or orchestration layer (revoking runner permissions, removing the agent's access to the build environment).
- **Recommendation**: No action needed for the library.
- **Evidence**: `index.js`, `package.json`

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity RISK-SAFETY, but surface-flag and archetype calibration applied
- **Finding**: System exposes no write operations — compensation logic is not applicable. Gulp is a stateless-utility with no multi-step write sequences. File writes via `dest()` are simple filesystem operations. Gulp tasks can be re-run to regenerate output — the build process itself is inherently idempotent.
- **Implication**: No compensation or rollback concerns for a build tool. Re-running the build produces a fresh result.
- **Recommendation**: No action needed.
- **Evidence**: `index.js`, `docs/api/dest.md`

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Read-only agent scope — concurrency controls for write operations are informational only. Gulp provides `series()` and `parallel()` for task orchestration, which handle task-level concurrency. The `watch()` function has a `queue: true` option that prevents overlapping task executions when the task is already running.
- **Implication**: Gulp's built-in task sequencing (`series`/`parallel`) and watch queue mechanism provide concurrency control at the task level, which is appropriate for a build tool.
- **Recommendation**: No action needed.
- **Evidence**: `index.js` (series, parallel bindings), `docs/api/watch.md` (queue option)

### STATE-Q5: Rate Limiting and Throttling

- **Severity**: INFO
- **Finding**: System exposes no HTTP/RPC surface — API-layer rate limiting is not applicable. Gulp is a local build tool. Execution throughput is bounded by local filesystem I/O and CPU, not by rate limiting infrastructure. The `watch()` function has a built-in `delay` option (default 200ms) that throttles task execution on file changes.
- **Implication**: No rate limiting concerns for a local build tool. The watch delay provides natural throttling for filesystem-triggered task execution.
- **Recommendation**: No action needed.
- **Evidence**: `docs/api/watch.md` (delay option), `index.js`

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Read-only agents cannot modify records, trigger spend, or delete data. Transaction limits for write operations are informational only. Gulp operations are scoped to local filesystem directories and configured globs — the blast radius is inherently limited to the working directory.
- **Implication**: No blast radius concerns for a read-only agent invoking a local build tool.
- **Recommendation**: No action needed.
- **Evidence**: `index.js`, `docs/api/src.md` (cwd option)

### HITL-Q3: Sandbox/Staging Environment

- **Severity**: INFO
- **Finding**: Libraries, CLIs, and scaffolds do not own staging environments — their consumers do. Gulp does provide a strong local testing story: the CI matrix tests across Node 22 and 24 on Ubuntu, Windows, and macOS. Developers can run `npm test` locally to validate behavior. No dedicated staging environment exists (nor is one expected for a build tool library).
- **Implication**: Agent testing with gulp would be done in a local development environment or CI pipeline sandbox, not in a gulp-owned staging environment.
- **Recommendation**: No action needed.
- **Evidence**: `.github/workflows/dev.yml` (matrix testing), `package.json` (test scripts)

### DATA-Q1: Sensitive Data Classification

- **Severity**: INFO
- **Finding**: Dev-library-application override — skip Stage A/B. Gulp is a build tool that processes local source files (JavaScript, CSS, images). It does not store, process, or transmit PII, PHI, financial records, or credentials. The data it handles consists of developer source code and build artifacts.
- **Implication**: No sensitive data classification concerns for a build tool.
- **Recommendation**: No action needed.
- **Evidence**: `index.js`, `package.json`

### DATA-Q2: Data Residency and Sovereignty ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity RISK-SAFETY, but surface-flag calibration applied
- **Finding**: No persistent data store and no user-data logging — residency requirements do not apply. Gulp operates on local filesystem data (source code, build artifacts) that remains on the developer's machine or CI runner. No data is transmitted to external services.
- **Implication**: No data residency concerns for a local build tool.
- **Recommendation**: No action needed.
- **Evidence**: `index.js`, `package.json`

### DATA-Q6: PII Redaction in Logs

- **Severity**: INFO
- **Finding**: System does not log user data and holds no user data — PII-in-logs risk is not applicable. Gulp logs consist of task names, file paths, and execution timing — all developer-facing build telemetry with no user PII. Logging is handled by the `gulplog` dependency (referenced in `CHANGELOG.md`), which emits task execution messages.
- **Implication**: No PII-in-logs risk for a build tool.
- **Recommendation**: No action needed.
- **Evidence**: `index.js`, `CHANGELOG.md` (gulplog reference)

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality metrics apply. Gulp processes local files — data quality (file existence, format validity) is the responsibility of the developer's source code and plugin ecosystem.
- **Implication**: Not relevant for a build tool.
- **Recommendation**: No action needed.
- **Evidence**: `index.js`, `docs/api/src.md` (allowEmpty option for missing files)

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Gulp's API method names are concise and semantically meaningful: `src` (source files), `dest` (destination/output), `watch` (file watching), `series` (sequential execution), `parallel` (parallel execution), `task` (task registration), `lastRun` (last execution timestamp), `tree` (task dependency tree), `registry` (task registry), `symlink` (symbolic links). The Vinyl file object properties (`path`, `contents`, `stat`, `cwd`, `base`) are equally clear. No legacy codes or opaque abbreviations.
- **Implication**: Agent tool descriptions derived from gulp's API would be immediately understandable to both LLMs and human reviewers.
- **Recommendation**: No action needed. Excellent naming conventions.
- **Evidence**: `index.js` (export names), `index.mjs` (named exports), `docs/api/README.md`

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: Gulp maintains comprehensive API documentation in `docs/api/` with 15 pages covering all public functions, the Vinyl file object, and core concepts. The `docs/` directory also includes getting-started guides, recipes (25 recipe files), FAQ, and CLI documentation. No formal data catalog exists (not applicable for a build tool), but the documentation serves as a complete metadata layer for the library's API surface.
- **Implication**: The extensive documentation in `docs/api/` would accelerate agent tool definition authoring.
- **Recommendation**: No action needed. Documentation quality is high.
- **Evidence**: `docs/api/README.md`, `docs/api/src.md`, `docs/api/dest.md`, `docs/api/watch.md`, `docs/recipes/README.md`

### OBS-Q1: Distributed Tracing and Structured Logging

- **Severity**: INFO
- **Finding**: Library/utility — tracing and correlation are consumer concerns. Gulp does not include OpenTelemetry, X-Ray, or structured logging instrumentation. Logging is delegated to the `gulplog` library (an event-based logger using `sparkles` for namespacing). Gulp does not produce JSON-structured logs — output is human-readable console text.
- **Implication**: If an agent orchestration layer needs to trace gulp task execution, instrumentation would be added at the CI/CD runner or wrapper script level, not within gulp itself.
- **Recommendation**: No action needed for the library. The library's obligation is to propagate trace context if provided, which is a future consideration for the gulplog ecosystem.
- **Evidence**: `index.js`, `package.json`, `CHANGELOG.md` (gulplog v2 reference)

### OBS-Q2: Alerting on Error Rates and Latency

- **Severity**: INFO
- **Finding**: Library/utility — alerting on error rates and latency is a consumer concern. Gulp has no alerting configuration. Build failures are surfaced through exit codes and console output, which CI/CD systems (GitHub Actions) report via their own notification mechanisms.
- **Implication**: Alerting for agent-initiated build failures would be configured in the CI/CD platform, not in gulp.
- **Recommendation**: No action needed for the library.
- **Evidence**: `bin/gulp.js`, `.github/workflows/dev.yml`

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No custom business metrics are published. Gulp provides build-time metrics (task duration via gulplog) but no CloudWatch, Prometheus, or custom metrics emission. Build success/failure rates are tracked by CI/CD platforms. Code coverage metrics are published to Coveralls via the dev workflow.
- **Implication**: Build outcome metrics (success rate, duration trends) would be derived from CI/CD platform telemetry, not from gulp itself.
- **Recommendation**: No action needed.
- **Evidence**: `.github/workflows/dev.yml` (Coveralls integration), `package.json` (nyc coverage config)

### ENG-Q1: Infrastructure Governance for Agent-Facing Surface

- **Severity**: INFO
- **Finding**: Library/utility — infrastructure governance is a consumer concern. No IaC files exist in the repository (no Terraform, CloudFormation, CDK, Helm, or Kustomize). This is expected — gulp is an npm package published to the npm registry, not a deployed service. Infrastructure governance applies to the consuming application's deployment, not to the library.
- **Implication**: No IaC governance concerns for a build tool library.
- **Recommendation**: No action needed.
- **Evidence**: Repository root (absence of `*.tf`, `template.yaml`, `cdk.json`, `Chart.yaml`)

### ENG-Q2: CI/CD with API Contract Testing

- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — API contract testing is not applicable. Library contract stability is evaluated by DISC-Q1. Gulp has a comprehensive CI/CD pipeline: GitHub Actions with matrix testing across Node.js 22 and 24 on ubuntu-latest, windows-latest, and macos-13. The pipeline runs linting (`eslint`), tests (`mocha`), and code coverage (`nyc` + Coveralls). However, no consumer-driven contract tests (Pact) or API schema validation runs in CI.
- **Implication**: Library contract stability relies on semver discipline and test coverage rather than automated contract testing. This is standard for npm packages.
- **Recommendation**: No action needed for ARA purposes. DISC-Q1 addresses the contract versioning concern.
- **Evidence**: `.github/workflows/dev.yml` (CI matrix), `package.json` (test scripts)

### ENG-Q3: Rollback Capability

- **Severity**: INFO
- **Finding**: No deployed HTTP/RPC surface — deployment rollback is a consumer concern. Library rollback is handled via package version pinning by consumers. Gulp publishes to npm with semver versioning and release-please automation. Consumers can pin to specific versions (`"gulp": "5.0.1"`) and roll back by changing the version in their `package.json`. npm's `npm unpublish` policy also provides a window for removing bad releases.
- **Implication**: Rollback for an agent consuming gulp is trivially accomplished by version pinning in the consumer's dependency manifest.
- **Recommendation**: No action needed.
- **Evidence**: `package.json` (version 5.0.1), `.github/workflows/release.yml` (release-please)

### ENG-Q4: API Test Coverage

- **Severity**: INFO
- **Finding**: Gulp has a test suite covering all core API functions: `test/index.test.js` (10 hasOwnProperty checks for all exports + CLI integration tests for `.cjs` and `.mjs` gulpfiles), `test/src.js` (8 tests covering stream creation, flat/deep globs, negation, read/buffer options), `test/dest.js` (8 tests covering file writing, streaming, directories, read-false), `test/watch.js` (12 tests covering file change detection, parallel tasks, destructuring, options, Japanese characters, negated globs, series composition). Code coverage is collected via `nyc` and reported to Coveralls. Tests run in CI across 6 platform configurations. However, this is INFO for a stateless-utility — the test suite validates the library's programmatic API, not an HTTP API that agents would call directly.
- **Implication**: Strong test coverage for the library API reduces the risk of behavioral regression that could affect agent tool bindings wrapping gulp.
- **Recommendation**: No action needed. The test suite is comprehensive for a build tool library.
- **Evidence**: `test/index.test.js`, `test/src.js`, `test/dest.js`, `test/watch.js`, `.github/workflows/dev.yml` (test matrix), `package.json` (nyc config)

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: Gulp exposes a well-documented programmatic JavaScript API (`src`, `dest`, `symlink`, `watch`, `task`, `series`, `parallel`, `lastRun`, `tree`, `registry`) via `index.js` and `index.mjs`. Comprehensive Markdown documentation exists in `docs/api/` (15 pages). No REST, GraphQL, or AsyncAPI interface exists — this is a local build tool, not a network service. Dev-library-application override: the programmatic API is the integration surface, not an HTTP endpoint.
- **Gap**: No network-callable API interface (expected for a build tool).
- **Recommendation**: No action needed. Agents would consume gulp via CLI invocation or programmatic import.
- **Evidence**: `index.js`, `index.mjs`, `docs/api/README.md`, `docs/api/src.md`, `docs/api/dest.md`, `docs/api/watch.md`

#### API-Q2: Machine-Readable API Specification
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — machine-readable spec is not applicable. The API contract is expressed through CommonJS/ESM exports and Markdown documentation.
- **Gap**: N/A — no HTTP/RPC surface to describe with OpenAPI/AsyncAPI.
- **Recommendation**: No action needed.
- **Evidence**: `index.js`, `index.mjs`, `docs/api/README.md`

#### API-Q3: Structured Error Responses
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — structured error responses are not applicable. Errors are thrown as JavaScript exceptions with descriptive messages.
- **Gap**: N/A — no HTTP/RPC surface.
- **Recommendation**: No action needed.
- **Evidence**: `index.js` (watch method error throw)

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Read-only agent scope. Gulp's `dest()` writes are inherently idempotent (file overwrite). The `overwrite` option controls behavior.
- **Gap**: N/A — read-only scope.
- **Recommendation**: No action needed.
- **Evidence**: `index.js`, `docs/api/dest.md`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: Gulp operates on Node.js streams of Vinyl file objects — structured, typed, in-memory objects (`path`, `contents`, `stat`, `cwd`, `base`). Not JSON/XML over HTTP.
- **Gap**: N/A.
- **Recommendation**: No action needed.
- **Evidence**: `index.js`, `docs/api/vinyl.md`

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has operations >30s OR long-running workflows. Gulp tasks execute locally and complete within seconds for typical builds. No long-running network operations.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has state changes (stateful-crud, orchestrator). Gulp is stateless-utility — no persistent state changes to emit events for.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — rate limiting is not applicable. Local build tool throughput is bounded by filesystem I/O and CPU.
- **Gap**: N/A.
- **Recommendation**: No action needed.
- **Evidence**: `index.js`, `bin/gulp.js`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: Dev-library-application — no network-callable surface exists. Gulp runs under the local user's or CI runner's identity. No OAuth, API key, mTLS, or service account patterns found.
- **Gap**: No machine identity mechanism (expected for a local build tool).
- **Recommendation**: Consumer applications should ensure proper identity attribution when orchestrating gulp.
- **Evidence**: `index.js`, `bin/gulp.js`, `package.json`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: INFO
- **Finding**: Dev-library-application — no authorization model exists. Gulp operates with the invoking process's filesystem permissions.
- **Gap**: No authorization model (expected for a local build tool).
- **Recommendation**: Enforce scoped permissions at the OS/container or CI/CD level.
- **Evidence**: `index.js`, `package.json`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: INFO
- **Finding**: Dev-library-application — no action-level authorization. All functions are callable by any invoker.
- **Gap**: No action-level authorization (expected for a local build tool).
- **Recommendation**: If restricting agent operations (e.g., `src` only, not `dest`), enforce at the orchestration layer.
- **Evidence**: `index.js`, `index.mjs`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: Archetype calibration: stateless-utility — downgraded to INFO. Gulp makes no network calls and processes no user-specific data. No identity context to propagate.
- **Gap**: N/A.
- **Recommendation**: No action needed.
- **Evidence**: `index.js`, `package.json`

#### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: No hardcoded credentials in source code. `.npmrc` contains only `package-lock=false`. CI/CD workflows use GitHub Secrets for `GITHUB_TOKEN`, `ATXCI_API_URL`, `ATXCI_API_KEY` — proper secrets management.
- **Gap**: None — credentials are properly managed.
- **Recommendation**: No action needed.
- **Evidence**: `.npmrc`, `.github/workflows/dev.yml`, `index.js`, `bin/gulp.js`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity RISK-SAFETY, but dev-library-application override applied (has_auth_surface=false AND has_write_operations=false)
- **Finding**: System does not execute agent-invoked write operations — audit logging is a consumer responsibility. No CloudTrail, CloudWatch, or audit log configuration exists. This is expected for a build tool library.
- **Gap**: No audit logging (expected — consumer responsibility).
- **Recommendation**: No action needed for the library.
- **Evidence**: `index.js`, `package.json`, `.github/workflows/dev.yml`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: INFO
- **Finding**: Dev-library-application override: has_auth_surface=false. System does not issue or enforce agent identities — suspension is a consumer responsibility. No API keys, service accounts, or identity tokens to suspend.
- **Gap**: No identity management (expected — consumer responsibility).
- **Recommendation**: No action needed for the library.
- **Evidence**: `index.js`, `package.json`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity RISK-SAFETY, but surface-flag calibration applied (has_write_operations=false AND has_http_rpc_surface=false). Archetype calibration: stateless-utility → INFO.
- **Finding**: System exposes no write operations — compensation logic is not applicable. Build tasks are inherently idempotent — re-running produces fresh output.
- **Gap**: N/A.
- **Recommendation**: No action needed.
- **Evidence**: `index.js`, `docs/api/dest.md`

#### STATE-Q2: Queryable Current State
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator). Gulp has no persistent state.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Gulp provides `series()` and `parallel()` for task-level concurrency control. The `watch()` function has `queue: true` (default) preventing overlapping task executions.
- **Gap**: N/A — read-only scope.
- **Recommendation**: No action needed.
- **Evidence**: `index.js`, `docs/api/watch.md`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has external dependencies (calls other services or external APIs). Gulp has no external service dependencies — all operations are local filesystem.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — API-layer rate limiting is not applicable. Stateless-utility archetype → INFO. The `watch()` delay option (200ms default) provides natural throttling.
- **Gap**: N/A.
- **Recommendation**: No action needed.
- **Evidence**: `docs/api/watch.md`, `index.js`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Read-only agents cannot modify records. Gulp operations are scoped to local filesystem directories and configured globs.
- **Gap**: N/A — read-only scope.
- **Recommendation**: No action needed.
- **Evidence**: `index.js`, `docs/api/src.md`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path. This repository is P2 priority and is not on the critical path.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled. Current scope is read-only.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q2: Configurable Approval Gates
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled. Current scope is read-only.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: INFO
- **Finding**: Dev-library-application override (has_http_rpc_surface=false AND has_persistent_data_store=false). Libraries do not own staging environments — consumers do. Gulp provides local testing via `npm test` and CI matrix testing across 6 platform configurations.
- **Gap**: No staging environment (expected — consumer responsibility).
- **Recommendation**: No action needed.
- **Evidence**: `.github/workflows/dev.yml`, `package.json`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO
- **Finding**: Dev-library-application override — skip Stage A/B. Gulp processes local source files and build artifacts. No PII, PHI, financial records, or credentials are stored, processed, or transmitted.
- **Gap**: N/A — not a data-handling target.
- **Recommendation**: No action needed.
- **Evidence**: `index.js`, `package.json`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity RISK-SAFETY, but surface-flag calibration applied (has_persistent_data_store=false AND has_logging_of_user_data=false). Archetype: stateless-utility → INFO.
- **Finding**: No persistent data store and no user-data logging — residency requirements do not apply. All data remains local.
- **Gap**: N/A.
- **Recommendation**: No action needed.
- **Evidence**: `index.js`, `package.json`

#### DATA-Q3: Selective Query Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has list/query endpoints with potentially unbounded results. Gulp has no query endpoints.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q4: System of Record Designations
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway). Gulp has no persistent state.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator). Gulp has no persistent state. Archetype stateless-utility → INFO even if triggered.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q6: PII Redaction in Logs
- **Severity**: INFO
- **Finding**: Surface-flag calibration: has_logging_of_user_data=false AND has_persistent_data_store=false — PII-in-logs risk is not applicable. Archetype stateless-utility → INFO. Gulp logs contain only task names, file paths, and execution timing.
- **Gap**: N/A.
- **Recommendation**: No action needed.
- **Evidence**: `index.js`, `CHANGELOG.md`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics apply. Gulp processes local files; data quality is the developer's responsibility.
- **Gap**: N/A.
- **Recommendation**: No action needed.
- **Evidence**: `index.js`, `docs/api/src.md`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: Gulp follows semver (v5.0.1). `CHANGELOG.md` documents breaking changes extensively. `release-please` automates versioning in `.github/workflows/release.yml`. ESM and CJS exports are defined in `package.json` `exports` field. However, no TypeScript type declarations are published, and no automated breaking-change detection tool runs in CI.
- **Gap**: No TypeScript declarations for typed consumption. No automated breaking-change detection in CI (e.g., api-extractor, arethetypeswrong, Pact).
- **Recommendation**: Add TypeScript `.d.ts` declarations and consider API snapshot testing in CI.
- **Evidence**: `package.json`, `CHANGELOG.md`, `.github/workflows/release.yml`, `index.js`, `index.mjs`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: API method names are concise and meaningful: `src`, `dest`, `watch`, `series`, `parallel`, `task`, `lastRun`, `tree`, `registry`, `symlink`. Vinyl properties are equally clear: `path`, `contents`, `stat`, `cwd`, `base`. No legacy codes.
- **Gap**: N/A — excellent naming.
- **Recommendation**: No action needed.
- **Evidence**: `index.js`, `index.mjs`, `docs/api/README.md`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: Comprehensive API documentation in `docs/api/` (15 pages) plus getting-started guides, recipes (25 files), FAQ, and CLI docs. Serves as the metadata layer for the library's API surface.
- **Gap**: N/A — documentation is thorough.
- **Recommendation**: No action needed.
- **Evidence**: `docs/api/README.md`, `docs/api/src.md`, `docs/api/dest.md`, `docs/api/watch.md`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: INFO
- **Finding**: Dev-library-application override (has_http_rpc_surface=false). Library/utility — tracing and correlation are consumer concerns. No OpenTelemetry, X-Ray, or JSON-structured logging. Logging via `gulplog` produces human-readable console output.
- **Gap**: No structured logging or trace propagation (expected — consumer responsibility).
- **Recommendation**: No action needed for the library.
- **Evidence**: `index.js`, `package.json`, `CHANGELOG.md`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: INFO
- **Finding**: Dev-library-application override (has_http_rpc_surface=false). Library/utility — alerting is a consumer concern. Build failures surface via exit codes; CI/CD platforms handle notifications.
- **Gap**: No alerting (expected — consumer responsibility).
- **Recommendation**: No action needed for the library.
- **Evidence**: `bin/gulp.js`, `.github/workflows/dev.yml`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics published. Build-time metrics (task duration) via gulplog. Code coverage reported to Coveralls in CI.
- **Gap**: N/A.
- **Recommendation**: No action needed.
- **Evidence**: `.github/workflows/dev.yml`, `package.json`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: INFO
- **Finding**: Dev-library-application override (has_http_rpc_surface=false AND has_auth_surface=false). No IaC files in the repository — expected for an npm package library. Infrastructure governance is the consumer's concern.
- **Gap**: No IaC (expected for a library).
- **Recommendation**: No action needed.
- **Evidence**: Repository root (no `.tf`, `template.yaml`, `cdk.json`, `Chart.yaml` files)

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: INFO
- **Finding**: Surface-flag calibration: has_http_rpc_surface=false — API contract testing is not applicable. Gulp has a comprehensive CI/CD pipeline: GitHub Actions matrix (Node 22, 24 × ubuntu, windows, macos), linting (eslint), testing (mocha), coverage (nyc + Coveralls). No consumer-driven contract tests or API schema validation in CI.
- **Gap**: No automated contract testing (addressed by DISC-Q1).
- **Recommendation**: No action needed for ARA purposes.
- **Evidence**: `.github/workflows/dev.yml`, `package.json`

#### ENG-Q3: Rollback Capability
- **Severity**: INFO
- **Finding**: Surface-flag calibration: has_http_rpc_surface=false — deployment rollback is a consumer concern. Library rollback via npm version pinning. Release-please automation in `.github/workflows/release.yml`.
- **Gap**: N/A — library rollback is inherent in package management.
- **Recommendation**: No action needed.
- **Evidence**: `package.json`, `.github/workflows/release.yml`

#### ENG-Q4: API Test Coverage
- **Severity**: INFO
- **Finding**: Comprehensive test suite: `test/index.test.js` (12 tests: 10 export checks + 2 CLI integration), `test/src.js` (8 stream/glob tests), `test/dest.js` (8 file write tests), `test/watch.js` (12 file watching tests). Coverage via nyc reported to Coveralls. Tests run across 6 CI configurations. INFO for stateless-utility — validates programmatic API, not HTTP API.
- **Gap**: No TypeScript integration tests. No explicit edge-case boundary tests for glob patterns.
- **Recommendation**: Strong coverage. Consider adding TypeScript consumption tests if `.d.ts` declarations are added (per DISC-Q1).
- **Evidence**: `test/index.test.js`, `test/src.js`, `test/dest.js`, `test/watch.js`, `.github/workflows/dev.yml`, `package.json`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent data stores. Gulp has no persistent data stores.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `index.js` | API-Q1, API-Q2, API-Q3, API-Q4, API-Q5, API-Q8, AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q3, STATE-Q5, STATE-Q6, DATA-Q1, DATA-Q2, DATA-Q6, DISC-Q1, DISC-Q2, OBS-Q1 |
| `index.mjs` | API-Q1, API-Q2, AUTH-Q3, DISC-Q1, DISC-Q2 |
| `bin/gulp.js` | API-Q8, AUTH-Q1, AUTH-Q5, OBS-Q2 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/dev.yml` | AUTH-Q5, AUTH-Q6, HITL-Q3, OBS-Q2, OBS-Q3, ENG-Q2, ENG-Q4 |
| `.github/workflows/release.yml` | DISC-Q1, ENG-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `package.json` | API-Q1, AUTH-Q1, AUTH-Q2, AUTH-Q4, AUTH-Q5, AUTH-Q6, AUTH-Q7, DATA-Q1, DATA-Q2, DISC-Q1, OBS-Q1, OBS-Q3, HITL-Q3, ENG-Q2, ENG-Q3, ENG-Q4 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `.npmrc` | AUTH-Q5 |
| `eslint.config.js` | AUTH-Q5 |

### Documentation
| File | Questions Referenced |
|------|---------------------|
| `docs/api/README.md` | API-Q1, API-Q2, DISC-Q2, DISC-Q3 |
| `docs/api/src.md` | API-Q1, STATE-Q6, DATA-Q7, DISC-Q3 |
| `docs/api/dest.md` | API-Q1, API-Q4, STATE-Q1, DISC-Q3 |
| `docs/api/watch.md` | API-Q1, STATE-Q3, STATE-Q5, DISC-Q3 |
| `docs/api/vinyl.md` | API-Q5 |
| `CHANGELOG.md` | DATA-Q6, DISC-Q1, OBS-Q1 |

### Test Files
| File | Questions Referenced |
|------|---------------------|
| `test/index.test.js` | ENG-Q4 |
| `test/src.js` | ENG-Q4 |
| `test/dest.js` | ENG-Q4 |
| `test/watch.js` | ENG-Q4 |

