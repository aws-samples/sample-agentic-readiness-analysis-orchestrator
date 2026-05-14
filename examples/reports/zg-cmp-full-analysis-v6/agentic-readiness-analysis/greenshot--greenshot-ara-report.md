# Agentic Readiness Analysis Report

**Target**: /Users/lucasdu/Documents/AWS-MAC/2026-projects/sample-agentic-readiness-analysis/services/greenshot--greenshot
**Date**: 2026-05-08
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**Repository Type**: application
**Service Archetype**: stateless-utility (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: csharp, desktop, windows
**Context**: Windows screenshot and annotation tool.

**Archetype Justification**: Greenshot is a native Windows desktop application that captures and annotates screenshots locally. It has no persistent data store, no HTTP/RPC server surface, no authentication surface for external callers, and no write operations exposed to agents. It operates entirely on local user-initiated actions.

**Surface flags**:
- has_persistent_data_store: false
- has_http_rpc_surface: false
- has_auth_surface: false
- has_write_operations: false
- has_logging_of_user_data: false

**Dev-Library-Application Override**: Applied. Service archetype is `stateless-utility` AND all five surface flags are `false`. This repository functions as a desktop end-user tool with no agent-callable surface. The `library` N/A mapping is applied for scoring purposes. Original `repo_type` (`application`) is preserved.

---

## Readiness Profile: Agent-Ready

**BLOCKERs**: 0 | **RISK-SAFETY**: 0 | **RISK-QUALITY**: 0 | **INFOs**: 5

Cleared for autonomous operation. Instrument observability. Define scope explicitly. Run controlled pilot first.

**Classification Rationale**: This repo has 0 High findings, 0 Medium findings, and 0 safety-impact Medium findings. The matched rule is "0 High, ≤1 Medium → Agent-Ready." The V6 classification aligns with the V5 Readiness Profile — zero BLOCKERs and zero RISK-SAFETY findings. The dev-library-application override correctly downgrades most questions to INFO or N/A because Greenshot is a desktop application with no agent-callable surface (no HTTP API, no data store, no authentication surface). An agent cannot call Greenshot — it is an end-user tool. Agent-Ready reflects that no remediation is blocking, not that the system is a useful agent integration target.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 0 |
| RISK-SAFETY | 0 |
| RISK-QUALITY | 0 |
| INFO | 5 |
| N/A | 5 |
| Not Evaluated (extended) | 33 |
| **Total** | **43** |

**Core Questions Evaluated**: 10 (dev-library-application override applies library N/A mapping — ENG-Q1 through ENG-Q5 are N/A; remaining core questions evaluated with surface-flag downgrades)
**Extended Questions Triggered**: 0
**Extended Questions Not Triggered**: 33
**Questions N/A (repo_type: application, dev-library-application override)**: 5
**Service Archetype**: stateless-utility (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

No BLOCKERs identified.

---

## RISKs

No RISKs identified.

---

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO
- **Finding**: Greenshot is a native Windows desktop application. It does not expose any REST, GraphQL, or AsyncAPI interface. It is not a web service and has no agent-callable API surface. Users interact via system tray, hotkeys, and WinForms UI.
- **Implication**: An agent cannot integrate with Greenshot via API calls. If agent-driven screenshot capture is needed, a wrapper service or CLI adapter would need to be built. The application does support command-line arguments via `System.CommandLine` (preview), but these launch the desktop app — they do not expose a programmatic interface.
- **Recommendation**: If agent integration is required, consider building a lightweight HTTP wrapper around Greenshot's capture logic, or evaluate headless screenshot tools (e.g., Puppeteer, Playwright) that expose programmatic APIs natively.
- **Evidence**: `src/Greenshot/GreenshotMain.cs` (entry point — WinForms application, no HTTP listener); no OpenAPI/Swagger/AsyncAPI files found in repository.

### AUTH-Q1: Machine Identity Authentication

- **Severity**: INFO
- **Finding**: Greenshot has no authentication surface for external callers. It is a desktop application that runs under the logged-in Windows user context. OAuth2 flows exist only for outbound calls to third-party services (Box, Dropbox, Imgur) where Greenshot acts as an OAuth client — not as a server accepting authenticated requests.
- **Implication**: No machine identity mechanism is needed because no agent can call Greenshot as a service. If Greenshot were wrapped in an API adapter, machine identity would need to be implemented in the wrapper.
- **Recommendation**: No action required unless Greenshot is repackaged as a service.
- **Evidence**: `src/Greenshot.Base/Core/OAuth/OAuth2Helper.cs`, `src/Greenshot.Base/Core/OAuth/OAuth2Settings.cs` — OAuth2 client flows only; no server-side auth middleware.

### AUTH-Q6: Immutable Audit Logging ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO (surface-flag downgrade applied)
- **Finding**: System does not execute agent-invoked write operations — audit logging is a consumer responsibility. Greenshot logs to local file via log4net (`%LocalApplicationData%\Greenshot\Greenshot.log`) but this is end-user diagnostic logging, not an immutable audit trail.
- **Implication**: No audit logging concern exists because no agent interacts with this system.
- **Recommendation**: No action required.
- **Evidence**: `src/Greenshot/log4net-release.xml` — RollingFileAppender to local filesystem.

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO (surface-flag downgrade applied)
- **Finding**: System exposes no write operations — compensation logic is not applicable. Greenshot is a desktop screenshot tool; its operations (capture, annotate, save) are user-initiated and local.
- **Implication**: No multi-step agent-initiated workflows exist that could require rollback.
- **Recommendation**: No action required.
- **Evidence**: `src/Greenshot/GreenshotMain.cs`, `src/Greenshot/Forms/MainForm.cs` — user-initiated workflows only.

### DATA-Q1: Sensitive Data Classification ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO (dev-library-application override, Stage A = No)
- **Finding**: Not a data-handling target — no PII/PHI/financial/credential data is stored, processed, or logged by the system in an agent-accessible manner. Greenshot captures screenshots locally on the user's machine and saves them to local disk. OAuth tokens for third-party services are stored encrypted in local INI files, but these are end-user credentials for the desktop app, not data exposed to or accessible by agents.
- **Implication**: No data classification concern for agent integration.
- **Recommendation**: No action required.
- **Evidence**: `src/Greenshot.Base/Core/CoreConfiguration.cs`, `src/Greenshot.Plugin.Box/BoxConfiguration.cs` (encrypted token storage is user-local).

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: Greenshot is a native Windows desktop application (WinExe output type, .NET Framework 4.8). It does not expose any REST, GraphQL, gRPC, or AsyncAPI interface. The application is launched via system tray and interacts with users through WinForms/WPF UI and hotkeys. No HTTP listener or server component exists.
- **Gap**: No API surface exists for agent consumption. Integration requires UI automation or building a wrapper.
- **Recommendation**: If agent integration is desired, build a lightweight API wrapper or evaluate headless alternatives.
- **Evidence**: `src/Greenshot/Greenshot.csproj` (OutputType: WinExe), `src/Greenshot/GreenshotMain.cs` (WinForms entry point), no API spec files in repository.

#### API-Q2: Machine-Readable API Specification
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — machine-readable spec is not applicable. Greenshot is a desktop application with no server-side API.
- **Gap**: N/A — no API surface exists to describe.
- **Recommendation**: No action required unless the application is repackaged as a service.
- **Evidence**: No OpenAPI, AsyncAPI, GraphQL, or Smithy files found in repository.

#### API-Q3: Structured Error Responses
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — structured error responses are not applicable. Error handling exists for internal exceptions (log4net logging, BugReportForm dialog), but there are no API responses to structure.
- **Gap**: N/A — no API surface exists.
- **Recommendation**: No action required.
- **Evidence**: `src/Greenshot/GreenshotMain.cs` (exception handlers display UI dialogs).

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Read-only agent scope; no write operations are exposed to agents. The application saves screenshots to local disk at user direction.
- **Gap**: No agent-accessible write endpoints exist.
- **Recommendation**: No action required.
- **Evidence**: `src/Greenshot/GreenshotMain.cs`, `src/Greenshot/Destinations/` (local save destinations, not HTTP endpoints).

#### API-Q5: Structured Response Format
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Always evaluated as INFO
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

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
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Always evaluated as INFO
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: INFO
- **Finding**: Greenshot has no authentication surface for external callers. It is a desktop application running under local Windows user context. OAuth2 client flows exist for outbound calls to Box, Dropbox, and Imgur APIs, but no inbound authentication is implemented — no agent can authenticate to Greenshot as a service.
- **Gap**: No machine identity mechanism exists because no agent-callable surface exists.
- **Recommendation**: No action required. If repackaged as a service, implement machine identity (OAuth2 client credentials or API keys with principal attribution).
- **Evidence**: `src/Greenshot.Base/Core/OAuth/OAuth2Helper.cs` (outbound OAuth2 client only), `src/Greenshot.Plugin.Imgur/ImgurUtils.cs` (Client-ID header for outbound calls).

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: INFO
- **Finding**: No agent-callable surface exists. The application runs with the permissions of the logged-in Windows user. No IAM policies, role-based access, or scoped permissions are relevant because no external entity can invoke the application programmatically.
- **Gap**: No authorization model exists for external callers because none is needed.
- **Recommendation**: No action required.
- **Evidence**: No IAM, RBAC, or permission enforcement code for inbound requests found.

#### AUTH-Q3: Action-Level Authorization
- **Severity**: INFO
- **Finding**: No agent-callable surface exists. The application does not enforce action-level authorization because it is a single-user desktop tool.
- **Gap**: No action-level authorization needed for a desktop application.
- **Recommendation**: No action required.
- **Evidence**: No authorization middleware or permission checks for inbound requests found.

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Archetype calibration downgrades to INFO for stateless-utility
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### AUTH-Q5: Credential Management
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Not a core question for dev-library-application override
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO (surface-flag downgrade)
- **Finding**: System does not execute agent-invoked write operations — audit logging is a consumer responsibility. The library/utility is called by applications that own the audit context. Greenshot uses log4net for local diagnostic logging (RollingFileAppender, 1MB max, 3 backups) but this is not an immutable audit trail and is not relevant to agent operations.
- **Gap**: No immutable audit logging — expected for a desktop application.
- **Recommendation**: No action required.
- **Evidence**: `src/Greenshot/log4net-release.xml`, `src/Greenshot.Base/log4net-embedded.xml`.

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: INFO
- **Finding**: System does not issue or enforce agent identities — suspension is a consumer responsibility. Libraries and utilities are invoked by applications that own identity lifecycle. Greenshot is a desktop application; no agent identities exist to suspend.
- **Gap**: No agent identity mechanism exists because none is needed.
- **Recommendation**: No action required.
- **Evidence**: No identity management or suspension mechanisms found.

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO (surface-flag downgrade)
- **Finding**: System exposes no write operations — compensation logic is not applicable. Greenshot is a desktop screenshot tool; user-initiated operations (capture, annotate, save to file) are local and do not require multi-step compensation.
- **Gap**: No agent-initiated write workflows exist.
- **Recommendation**: No action required.
- **Evidence**: `src/Greenshot/Destinations/` (file save, clipboard, printer — all local user actions).

#### STATE-Q2: Queryable Current State
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q3: Concurrency Controls ⚡
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
- **Severity**: INFO
- **Finding**: System exposes no HTTP/RPC surface — API-layer rate limiting is not applicable. Greenshot is a desktop application; no API endpoint exists that could be rate-limited.
- **Gap**: No rate limiting needed for a desktop application.
- **Recommendation**: No action required.
- **Evidence**: No HTTP listener or API framework found in source code.

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: INFO
- **Finding**: Library/utility — tracing and correlation are consumer concerns. Greenshot is a desktop application; it does not own a staging environment. Build-time testing is done via GitHub Actions on `windows-latest` runners, but this is CI — not a staging environment for agent testing.
- **Gap**: No staging environment for agent testing — expected for a desktop application.
- **Recommendation**: No action required.
- **Evidence**: `.github/workflows/release.yml` (CI build only, no deployment environment).

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO (dev-library-application override)
- **Finding**: Not a data-handling target — no PII/PHI/financial/credential data is stored, processed, or logged by the system in an agent-accessible manner. Greenshot captures screenshots locally on the user's machine. OAuth tokens for Box/Dropbox/Imgur are stored encrypted in local INI files, but these are end-user credentials for the desktop app, not data exposed to agents.
- **Gap**: No data classification concern for agent integration.
- **Recommendation**: No action required.
- **Evidence**: `src/Greenshot.Base/Core/CoreConfiguration.cs`, `src/Greenshot.Plugin.Box/BoxConfiguration.cs`.

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO (surface-flag downgrade)
- **Finding**: No persistent data store and no user-data logging — residency requirements do not apply. Greenshot stores screenshots and configuration locally on the user's Windows machine. No cloud data storage is owned by the application.
- **Gap**: No data residency concern for a local desktop application.
- **Recommendation**: No action required.
- **Evidence**: `src/Greenshot.Base/Core/CoreConfiguration.cs` (OutputFilePath is local filesystem path).

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
- **Finding**: System does not log user data and holds no user data — PII-in-logs risk is not applicable. Greenshot's log4net configuration logs diagnostic messages (thread, level, logger, message, exception) to local files. No user-submitted content or PII is logged — log entries contain application operational data only.
- **Gap**: No PII logging concern for a local diagnostic logger.
- **Recommendation**: No action required.
- **Evidence**: `src/Greenshot/log4net-release.xml` (pattern: `%date{ISO8601} [%thread] %-5level - [%logger] %m%n%exception`).

#### DATA-Q7: Data Quality Awareness
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Always evaluated as INFO
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Core question but dev-library-application override applies library N/A behavior
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Always evaluated as INFO
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Always evaluated as INFO
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: INFO
- **Finding**: Library/utility — tracing and correlation are consumer concerns. Greenshot uses log4net for local file-based logging with ISO8601 timestamps and thread correlation. No distributed tracing (OpenTelemetry, X-Ray) exists because there is no distributed system — the application runs locally on a single machine. No agent-initiated request path exists to trace.
- **Gap**: No distributed tracing — expected for a standalone desktop application.
- **Recommendation**: No action required.
- **Evidence**: `src/Greenshot/log4net-release.xml`, `src/Greenshot.Base/log4net-embedded.xml`.

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: INFO
- **Finding**: Library/utility — alerting on error rates and latency is a consumer concern. Greenshot is a desktop application with no server-side API. There are no error rates or latency metrics to alert on because no requests are served.
- **Gap**: No alerting — expected for a desktop application.
- **Recommendation**: No action required.
- **Evidence**: No CloudWatch, PagerDuty, or monitoring configuration found.

#### OBS-Q3: Business Outcome Metrics
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Always evaluated as INFO
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: N/A
- **Finding**: This is an `application` repository with the dev-library-application override applied (library N/A mapping for ENG questions). This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: N/A
- **Finding**: This is an `application` repository with the dev-library-application override applied (library N/A mapping for ENG questions). This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q3: Rollback Capability
- **Severity**: N/A
- **Finding**: This is an `application` repository with the dev-library-application override applied (library N/A mapping for ENG questions). This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q4: API Test Coverage
- **Severity**: N/A
- **Finding**: This is an `application` repository with the dev-library-application override applied (library N/A mapping for ENG questions). This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: N/A
- **Finding**: This is an `application` repository with the dev-library-application override applied (library N/A mapping for ENG questions). This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| src/Greenshot/GreenshotMain.cs | API-Q1, API-Q3, API-Q4, STATE-Q1 |
| src/Greenshot/Greenshot.csproj | API-Q1 |
| src/Greenshot/Forms/MainForm.cs | STATE-Q1 |
| src/Greenshot/Destinations/ | API-Q4, STATE-Q1 |
| src/Greenshot.Base/Core/OAuth/OAuth2Helper.cs | AUTH-Q1 |
| src/Greenshot.Base/Core/OAuth/OAuth2Settings.cs | AUTH-Q1 |
| src/Greenshot.Plugin.Imgur/ImgurUtils.cs | AUTH-Q1 |
| src/Greenshot.Base/Core/CoreConfiguration.cs | DATA-Q1, DATA-Q2 |
| src/Greenshot.Plugin.Box/BoxConfiguration.cs | DATA-Q1 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| .github/workflows/release.yml | HITL-Q3 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| src/Greenshot/log4net-release.xml | AUTH-Q6, DATA-Q6, OBS-Q1 |
| src/Greenshot.Base/log4net-embedded.xml | AUTH-Q6, OBS-Q1 |
