# Agentic Readiness Analysis Report

**Target**: greenshot (https://github.com/greenshot/greenshot)
**Date**: 2026-04-30
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**TD Version**: agentic-readiness-analysis
**Repository Type**: monorepo (user-provided)
**Service Archetype**: stateless-utility (auto-detected)
**Agent Scope**: read-only (user-provided)
**Priority**: P2
**Tags**: csharp, desktop, windows
**Context**: Windows screenshot and annotation tool.

**Archetype Justification**: Greenshot is a Windows desktop WinForms application that performs screenshot capture and image manipulation. It has no HTTP server, no persistent database, no message queues, and no external API surface — matching the stateless-utility archetype (pure computation, no persistent state, no user-specific server-side data).

> **INFO — Dev-Library-Application Override Applied**: Although `repo_type` is `monorepo` and the application has a `Main()` entry point (`src/Greenshot/GreenshotMain.cs`, `OutputType: WinExe`), all 5 surface flags are `false` and `service_archetype` is `stateless-utility`. Per the ARA-TD Step 1.5 override, the `library` N/A mapping is applied as a baseline for scoring purposes (ENG-Q1 through ENG-Q5 become N/A). The original `repo_type: monorepo` is preserved in metadata. This override prevents false-positive findings for a desktop GUI application that has no server-side agent-integrable surface.

**Surface flags**:
- has_persistent_data_store: false
- has_http_rpc_surface: false
- has_auth_surface: false
- has_write_operations: false
- has_logging_of_user_data: false

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 2 | **RISK-SAFETY**: 2 | **RISK-QUALITY**: 2 | **INFOs**: 22

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days. The two BLOCKERs reflect the fundamental nature of Greenshot as a desktop GUI application: (1) API-Q1 — no programmatic API interface exists for agents to call, and (2) AUTH-Q1 — no machine identity authentication exists because there is no inbound request surface. Agent integration would require building a wrapper API or CLI around Greenshot's screenshot/annotation capabilities, which would then need machine identity support.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 2 |
| RISK-SAFETY | 2 |
| RISK-QUALITY | 2 |
| INFO | 22 |
| N/A | 5 |
| Not Evaluated (extended) | 10 |
| **Total** | **43** |

**Core Questions Evaluated**: 21 (24 core minus 3 N/A from dev-library-application override)
**Extended Questions Triggered**: 7 (API-Q5, API-Q8, STATE-Q4, DATA-Q7, DISC-Q2, DISC-Q3, OBS-Q3) — all as INFO
**Extended Questions Not Triggered**: 10 (API-Q6, API-Q7, STATE-Q2, STATE-Q3, STATE-Q7, HITL-Q1, HITL-Q2, DATA-Q3, DATA-Q4, DATA-Q5)
**Questions N/A (dev-library-application override from monorepo)**: 5 (ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4, ENG-Q5)
**Service Archetype**: stateless-utility (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### API-Q1: Documented API Interface

- **Severity**: BLOCKER
- **Finding**: Greenshot is a Windows desktop WinForms application (`src/Greenshot/Greenshot.csproj`, `OutputType: WinExe`). It does NOT expose any REST, GraphQL, AsyncAPI, or programmatic interface for external callers. The application's functionality (screenshot capture, annotation, upload to cloud services) is accessed exclusively through a Windows GUI — system tray icon, hotkeys, and WinForms dialogs. The only inter-process communication is Windows `WM_COPYDATA` messages (`src/Greenshot/Helpers/CopyData.cs`) used for single-instance coordination, not for API-style integration. For an agent to interact with Greenshot, it would require UI automation (RPA), which is fragile and unscalable.
- **Gap**: No programmatic API interface exists. The application is designed for human GUI interaction only.
- **Remediation**:
  - **Immediate**: Define a CLI or REST API wrapper around core Greenshot capabilities (screenshot capture, annotation, file export). The `System.CommandLine` package reference in `src/Greenshot/Greenshot.csproj` suggests CLI support may already be in development.
  - **Target State**: A documented, machine-readable API (CLI with structured JSON output or local REST API) that exposes screenshot capture, annotation, and export operations.
  - **Estimated Effort**: High — requires architectural changes to decouple core functionality from the WinForms GUI layer.
  - **Dependencies**: AUTH-Q1 (machine identity) must be addressed concurrently if an API surface is created.
- **Evidence**: `src/Greenshot/Greenshot.csproj` (WinExe output type), `src/Greenshot/GreenshotMain.cs` (WinForms Application.Run entry point), `src/Greenshot/Forms/MainForm.cs` (GUI-only interaction model)

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: Greenshot has no concept of authenticating inbound callers. There are no service accounts, API keys, mTLS configurations, or API Gateway authorizers. The application authenticates *outbound* to third-party services (OAuth2 flows for Box, Dropbox, Imgur via `src/Greenshot.Base/Core/OAuth/OAuth2Helper.cs`; Windows Credential Manager for Jira/Confluence via `src/Greenshot.Base/Core/CredentialsHelper.cs`), but these are client-side user-driven flows, not machine identity. There is no mechanism for an agent to identify itself when calling the application.
- **Gap**: No machine identity authentication mechanism exists because there is no inbound request surface to authenticate against.
- **Remediation**:
  - **Immediate**: If a programmatic API is created (per API-Q1 remediation), implement machine identity authentication from the start — API key or OAuth2 client credentials flow with principal attribution.
  - **Target State**: Any new API surface authenticates callers via API key or client credentials, with the authenticated principal recorded in logs.
  - **Estimated Effort**: Medium — straightforward to implement alongside a new API surface, but blocked by API-Q1.
  - **Dependencies**: API-Q1 (must have an API surface before authentication is meaningful)
- **Evidence**: `src/Greenshot.Base/Core/OAuth/OAuth2Helper.cs` (outbound-only OAuth2), `src/Greenshot.Base/Core/CredentialsHelper.cs` (Windows Credential Manager for user credentials), `src/Greenshot/GreenshotMain.cs` (no server/listener startup)

---

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Greenshot has no authorization model for inbound access. There are no IAM policies, no role definitions, no per-agent permission scoping. The OAuth2 tokens used for outbound plugin connections (Box, Dropbox, Imgur) have scopes defined by the third-party services, not by Greenshot. The application runs under the desktop user's Windows session with that user's full permissions — there is no mechanism to grant an agent read-only access to specific resources.
- **Gap**: No inbound authorization model exists. No mechanism for scoped, least-privilege agent access.
- **Compensating Controls**:
  - If a wrapper API is built, implement RBAC or ABAC from the start with per-agent permission profiles.
  - For a pilot, restrict agent access to a read-only subset of operations (e.g., screenshot retrieval only, no uploads).
- **Remediation Timeline**: 60–90 days (contingent on API-Q1 remediation)
- **Recommendation**: Design scoped permissions into any future API surface. Define role profiles: `read-only` (capture and retrieve screenshots), `annotate` (add annotations), `export` (upload to cloud services).
- **Evidence**: `src/Greenshot.Base/Core/OAuth/OAuth2Helper.cs` (outbound-only scoping), `src/Greenshot/GreenshotMain.cs` (runs under user session)

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: Greenshot has no action-level authorization — all operations are equally available to the desktop user. There is no enforcement of "can read but not delete" or "can capture but not upload." The plugin architecture (`src/Greenshot.Plugin.*`) separates functionality by destination (Box, Imgur, etc.) but does not enforce access controls between them.
- **Gap**: No fine-grained RBAC, no ABAC policies, no action-level checks. Any user or agent with access can perform any operation.
- **Compensating Controls**:
  - If a wrapper API is built, implement action-level authorization from the start (e.g., separate permissions for `screenshot:capture`, `screenshot:annotate`, `screenshot:export`).
  - For a pilot, restrict agent to a single action category via API design.
- **Remediation Timeline**: 60–90 days (contingent on API-Q1 remediation)
- **Recommendation**: When building an API surface, enforce action-level authorization. Map each API endpoint to a specific permission that can be granted or denied per agent identity.
- **Evidence**: `src/Greenshot/Destinations/` (all destinations equally accessible), `src/Greenshot/Helpers/CaptureHelper.cs` (capture logic has no access checks)

### RISK-QUALITY — Address as Capacity Allows

#### AUTH-Q5: Credential Management — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Plugin API credentials (client IDs and secrets for Box, Dropbox, Imgur) are managed through a build-time template substitution system. Credential templates (`src/Greenshot.Plugin.Box/Greenshot.Plugin.Box.Credentials.template`, `src/Greenshot.Plugin.Imgur/Greenshot.Plugin.Imgur.Credentials.template`, `src/Greenshot.Plugin.Dropbox/Greenshot.Plugin.Dropbox.Credentials.template`) contain placeholders like `${Box13_ClientId}` that are replaced during build from environment variables. In CI/CD, these values come from GitHub Actions secrets (`.github/workflows/release.yml`). OAuth tokens are persisted in the local user's INI configuration (`src/Greenshot.Base/IniFile/IniConfig.cs`), stored as plaintext in `%APPDATA%\Greenshot\Greenshot.ini`. No runtime secrets manager (AWS Secrets Manager, HashiCorp Vault) is used. No rotation mechanism exists.
- **Gap**: OAuth tokens stored as plaintext in local INI file. No secrets rotation mechanism. Build-time credential injection is sound for CI but local storage is unprotected.
- **Compensating Controls**:
  - The build-time template approach with GitHub Actions secrets is appropriate for CI/CD credential management.
  - For local storage, consider using Windows DPAPI or Credential Manager instead of plaintext INI.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Migrate OAuth token storage from plaintext INI to Windows DPAPI-protected storage or Windows Credential Manager (which `CredentialsHelper.cs` already wraps for Jira/Confluence). Apply consistently across all plugins.
- **Evidence**: `src/Greenshot.Plugin.Box/Greenshot.Plugin.Box.Credentials.template`, `src/Greenshot.Plugin.Imgur/Greenshot.Plugin.Imgur.Credentials.template`, `src/Greenshot.Plugin.Dropbox/Greenshot.Plugin.Dropbox.Credentials.template`, `src/Directory.Build.props` (token substitution), `.github/workflows/release.yml` (secrets usage), `src/Greenshot.Base/IniFile/IniConfig.cs` (plaintext storage)

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: Greenshot uses Nerdbank.GitVersioning (`src/version.json`, `src/Directory.Build.props` referencing `Nerdbank.GitVersioning 3.9.50`) for semantic versioning of releases. GitHub Actions release workflow (`.github/workflows/release.yml`) creates versioned tags and releases. However, there are no API contracts to version (no OpenAPI specs, no schema definitions, no consumer-driven contract tests) because there is no API surface. The application's "interface" is its GUI and file output format, neither of which has a formal schema or breaking-change detection mechanism.
- **Gap**: No API contracts exist to version or protect. No breaking-change detection in CI. The application version is managed but the interface contract is undefined.
- **Compensating Controls**:
  - Nerdbank.GitVersioning provides release versioning, which is a foundation to build on.
  - If an API is created, add OpenAPI spec with schema validation in CI.
- **Remediation Timeline**: 30–60 days (contingent on API creation)
- **Recommendation**: When building an API surface, define an OpenAPI spec and add breaking-change detection (e.g., `openapi-diff`) to the CI pipeline. Version the API from day one.
- **Evidence**: `src/version.json`, `src/Directory.Build.props` (Nerdbank.GitVersioning), `.github/workflows/release.yml` (versioned releases)

---

## INFOs — Architecture and Design Inputs

### API-Q2: Machine-Readable API Specification

- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — machine-readable spec is not applicable. Greenshot has no API endpoints to document.
- **Implication**: If an API is built in the future, an OpenAPI spec should be generated from the start.
- **Recommendation**: When creating a programmatic interface, auto-generate OpenAPI from code annotations (e.g., Swashbuckle for .NET).
- **Evidence**: No OpenAPI, AsyncAPI, GraphQL, or Smithy files found in the repository.

### API-Q3: Structured Error Responses

- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — structured error responses are not applicable. The application uses Windows dialog boxes and log4net logging for error reporting (`src/Greenshot/GreenshotMain.cs` — `BugReportForm`, `Application_ThreadException`).
- **Implication**: If an API is built, define a consistent error response format from the start.
- **Recommendation**: Design structured JSON error responses with error code, message, and retryable boolean for any future API.
- **Evidence**: `src/Greenshot/GreenshotMain.cs` (exception handlers display GUI dialogs)

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Read-only agents do not execute write operations. Greenshot's write operations (screenshot save, cloud upload) are user-initiated GUI actions, not API endpoints.
- **Implication**: If write-enabled agent scope is considered in the future, idempotency must be built into any API write endpoints.
- **Recommendation**: N/A for current read-only scope.
- **Evidence**: `src/Greenshot/Destinations/FileDestination.cs`, `src/Greenshot.Plugin.Imgur/ImgurUtils.cs`

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: Greenshot outputs screenshots as image files (PNG, JPEG, BMP, TIFF, GIF) configured via `CoreConfiguration.OutputFileFormat`. The application uses JSON internally for OAuth2 token responses (`src/Greenshot.Base/Core/JSONHelper.cs`) and XML for Imgur API responses. There is no structured response format for agent consumption because there is no API.
- **Implication**: If an API is built, JSON is the natural response format. Image data should be returned as file paths or base64-encoded payloads within JSON structures.
- **Recommendation**: Design API responses as JSON with metadata (capture timestamp, dimensions, format) alongside image data references.
- **Evidence**: `src/Greenshot.Base/Core/CoreConfiguration.cs` (OutputFileFormat), `src/Greenshot.Base/Core/JSONHelper.cs`

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No API surface exists to rate-limit. The application does not expose or document any rate limits. Outbound calls to third-party APIs (Imgur, Box, Dropbox) are subject to those services' rate limits, handled via HTTP status codes in `src/Greenshot.Base/Core/NetworkHelper.cs`.
- **Implication**: If an API is built, implement rate limiting and return standard headers (`X-RateLimit-Remaining`, `Retry-After`).
- **Recommendation**: Plan rate limiting architecture for any future API surface.
- **Evidence**: `src/Greenshot.Base/Core/NetworkHelper.cs` (handles HTTP errors from third-party APIs)

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: INFO
- **Finding**: Archetype calibration: stateless-utility → downgraded to INFO. Greenshot does not propagate identity through service calls. OAuth2 tokens for third-party services (Box, Dropbox, Imgur) are user-owned, not delegated. The `OAuth2Helper.AddOAuth2Credentials()` method adds Bearer tokens to outbound requests, but this is direct user authentication, not on-behalf-of flow.
- **Implication**: If Greenshot becomes an agent-callable service, identity propagation between the agent and Greenshot's downstream service calls would need design.
- **Recommendation**: Architectural consideration for future API design.
- **Evidence**: `src/Greenshot.Base/Core/OAuth/OAuth2Helper.cs` (AddOAuth2Credentials, CheckAndAuthenticateOrRefresh)

### AUTH-Q6: Immutable Audit Logging ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity RISK-SAFETY, but surface-flag calibration applies.
- **Finding**: System does not execute agent-invoked write operations — audit logging is a consumer responsibility. Greenshot uses log4net for local file-based diagnostic logging (`src/Greenshot/log4net-release.xml` — rolling file appender to `%LOCALAPPDATA%\Greenshot\Greenshot.log`, 1MB max, 3 backups). Logs record application events (startup, errors, HTTP responses) but do not capture authenticated principal identity or write-operation audit trails. The `has_auth_surface` and `has_write_operations` flags are both `false`.
- **Implication**: If an API is built with write operations, immutable audit logging with principal attribution is mandatory.
- **Recommendation**: Design audit logging into any future API surface from the start.
- **Evidence**: `src/Greenshot/log4net-release.xml`, `src/Greenshot/log4net-debug.xml`, `src/Greenshot.Base/Core/LogHelper.cs`

### AUTH-Q7: Agent Identity Suspension

- **Severity**: INFO
- **Finding**: System does not issue or enforce agent identities — suspension is a consumer responsibility. There is no inbound authentication surface (`has_auth_surface: false`). No API keys, service accounts, or agent identities exist to suspend.
- **Implication**: If an API with agent identity is built, include immediate suspension/revocation capability.
- **Recommendation**: Architectural consideration for future API design.
- **Evidence**: `src/Greenshot/GreenshotMain.cs` (no listener/server code)

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity RISK-SAFETY, but surface-flag calibration applies.
- **Finding**: System exposes no write operations — compensation logic is not applicable. Greenshot's write operations (file save, cloud upload) are GUI-initiated and not programmatically callable. The stateless-utility archetype and `has_write_operations: false` both indicate INFO.
- **Implication**: If write operations are exposed via API, compensation/rollback patterns should be built in.
- **Recommendation**: N/A for current scope.
- **Evidence**: `src/Greenshot/Destinations/FileDestination.cs`, `src/Greenshot.Plugin.Imgur/ImgurUtils.cs`

### STATE-Q4: Circuit Breakers and Resilience

- **Severity**: INFO
- **Finding**: Extended question triggered (service has external dependencies). Greenshot plugins call external APIs: Imgur (`src/Greenshot.Plugin.Imgur/ImgurUtils.cs`), Box (`src/Greenshot.Plugin.Box/BoxUtils.cs`), Dropbox (`src/Greenshot.Plugin.Dropbox/DropboxUtils.cs`), Jira (`src/Greenshot.Plugin.Jira/JiraConnector.cs`), Confluence (`src/Greenshot.Plugin.Confluence/Confluence.cs`). However, no circuit breaker, retry, or exponential backoff patterns are implemented. `NetworkHelper.cs` catches `WebException` and logs errors but does not implement resilience patterns (no Polly, no Resilience4j equivalent, no retry decorators). Timeout values are configurable (`CoreConfiguration.WebRequestTimeout = 100s`, `WebRequestReadWriteTimeout = 100s`). However, given the dev-library-application override and the desktop application context, this is downgraded to INFO — the resilience concern is for the desktop user experience, not agent-cascading failure.
- **Implication**: Outbound HTTP calls to third-party services could hang for up to 100 seconds with no circuit breaker. If Greenshot is wrapped in an API, these calls would need resilience patterns.
- **Recommendation**: Add Polly or equivalent resilience library for outbound HTTP calls, especially if plugin functionality is exposed via API.
- **Evidence**: `src/Greenshot.Base/Core/NetworkHelper.cs` (no retry/circuit breaker), `src/Greenshot.Base/Core/CoreConfiguration.cs` (WebRequestTimeout=100s)

### STATE-Q5: Rate Limiting and Throttling

- **Severity**: INFO
- **Finding**: System exposes no HTTP/RPC surface — API-layer rate limiting is not applicable. Greenshot is a desktop application that does not accept inbound network requests.
- **Implication**: If an API is built, rate limiting is essential to prevent agent traffic storms.
- **Recommendation**: Include rate limiting in any future API architecture.
- **Evidence**: `src/Greenshot/GreenshotMain.cs` (no server/listener)

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Read-only agents cannot modify records, trigger spend, or delete data. Transaction limits for write operations are informational only.
- **Implication**: N/A for current scope.
- **Recommendation**: N/A for current read-only scope.
- **Evidence**: No write-path API endpoints found.

### HITL-Q3: Sandbox/Staging Environment

- **Severity**: INFO
- **Finding**: `has_http_rpc_surface` is `false` AND `has_persistent_data_store` is `false` — sandbox/staging is not applicable. Greenshot is a desktop application that can be installed and tested locally without risk to any production system. Debug configuration exists (`src/Greenshot/log4net-debug.xml`) for development testing.
- **Implication**: If an API is built, a staging environment with test data should be created.
- **Recommendation**: The desktop application can be tested locally; no separate staging infrastructure is needed.
- **Evidence**: `src/Greenshot/log4net-debug.xml` (debug configuration), `src/Greenshot/Greenshot.csproj` (Debug/Release configurations)

### DATA-Q1: Sensitive Data Classification

- **Severity**: INFO
- **Finding**: Archetype calibration: stateless-utility → INFO. Stage A scope gate: Greenshot is a desktop screenshot tool that captures screen content (which could theoretically contain sensitive information displayed on screen) and stores it as image files on the local filesystem. However, the application itself does not own a database, does not store user PII in structured fields, and does not persist data beyond the user's local filesystem. OAuth tokens are stored in local INI configuration but are transient credentials, not business data. Screenshots are user-directed captures saved to user-specified locations. The application is not a data-handling target in the ARA sense.
- **Implication**: If screenshots are made accessible via API, data classification may become relevant (screenshots could capture PII on screen).
- **Recommendation**: If exposing screenshot content via API, consider implementing content classification or redaction capabilities.
- **Evidence**: `src/Greenshot.Base/Core/CoreConfiguration.cs` (OutputFilePath configuration), `src/Greenshot.Base/IniFile/IniConfig.cs` (local settings storage)

### DATA-Q2: Data Residency and Sovereignty ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity RISK-SAFETY, but surface-flag calibration applies.
- **Finding**: `has_persistent_data_store` is `false` AND `has_logging_of_user_data` is `false` — residency requirements do not apply. Greenshot stores screenshots locally on the user's filesystem. Cloud uploads (Imgur, Box, Dropbox) are user-initiated and subject to those services' data residency policies, not Greenshot's.
- **Implication**: If screenshots are transmitted through an agent pipeline to an LLM, residency of the screenshot content becomes relevant.
- **Recommendation**: Architectural consideration if agent-mediated screenshot sharing is implemented.
- **Evidence**: `src/Greenshot.Base/Core/CoreConfiguration.cs` (local OutputFilePath)

### DATA-Q6: PII Redaction in Logs

- **Severity**: INFO
- **Finding**: `has_logging_of_user_data` is `false` AND `has_persistent_data_store` is `false` — PII-in-logs risk is not applicable. log4net logs capture application diagnostics: timestamps, thread IDs, log levels, exception stack traces, and HTTP status codes from outbound API calls. The log pattern `%date{ISO8601} [%thread] %-5level - [%logger] %m%n%exception` does not include user-submitted content. `NetworkHelper.cs` logs response headers and error content from third-party APIs, which could theoretically include API error messages but not user PII.
- **Implication**: If an API is built that processes user data, PII redaction in logs becomes critical.
- **Recommendation**: Review log statements in `NetworkHelper.cs` that log full HTTP response content — these could leak third-party API data.
- **Evidence**: `src/Greenshot/log4net-release.xml` (log pattern), `src/Greenshot.Base/Core/NetworkHelper.cs` (response logging)

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: Always evaluated as INFO. Greenshot does not manage datasets — it captures screenshots and exports images. There are no data quality scores, completeness metrics, or freshness SLAs. Screenshot quality is determined by capture settings (format, JPEG quality percentage in `CoreConfiguration.OutputFileJpegQuality`, color reduction options).
- **Implication**: Not applicable for a screenshot tool. If screenshots are used as data in an agent pipeline, quality of the captured content is a function of screen resolution and capture settings.
- **Recommendation**: No action required.
- **Evidence**: `src/Greenshot.Base/Core/CoreConfiguration.cs` (OutputFileJpegQuality, OutputFileFormat)

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Always evaluated as INFO. Greenshot uses clear, human-readable naming conventions in its C# codebase. Configuration properties use descriptive names: `OutputFilePath`, `CaptureDelay`, `OutputFileFormat`, `WindowCaptureMode`. Class names are descriptive: `CaptureHelper`, `ClipboardDestination`, `ImgurUtils`, `OAuth2Helper`. No legacy abbreviations or opaque codes were found.
- **Implication**: Good naming practices would transfer well to any API design.
- **Recommendation**: Maintain current naming conventions if building an API.
- **Evidence**: `src/Greenshot.Base/Core/CoreConfiguration.cs` (descriptive property names), `src/Greenshot.Base/Core/NetworkHelper.cs` (clear method names)

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: Always evaluated as INFO. No data catalog or metadata layer exists. Greenshot is a desktop application, not a data service. There is no Glue Data Catalog, no metadata registry, no data dictionary.
- **Implication**: Not applicable for a desktop screenshot tool.
- **Recommendation**: No action required.
- **Evidence**: No data catalog files found in the repository.

### OBS-Q1: Distributed Tracing and Structured Logging

- **Severity**: INFO
- **Finding**: `has_http_rpc_surface` is `false` — tracing and correlation are consumer concerns. Greenshot uses log4net for local file-based logging with a text pattern layout (`%date{ISO8601} [%thread] %-5level - [%logger] %m%n%exception`). Logs are not structured JSON. There is no distributed tracing (no OpenTelemetry, no X-Ray, no traceparent header propagation). No correlation IDs link request chains. This is appropriate for a desktop application.
- **Implication**: If an API is built, implement structured JSON logging with OpenTelemetry from the start.
- **Recommendation**: Migrate from log4net text format to structured JSON logging if building a service layer.
- **Evidence**: `src/Greenshot/log4net-release.xml` (PatternLayout, not JSON), `src/Greenshot.Base/Core/LogHelper.cs`

### OBS-Q2: Alerting on Error Rates and Latency

- **Severity**: INFO
- **Finding**: `has_http_rpc_surface` is `false` — alerting on error rates and latency is a consumer concern. No CloudWatch alarms, no PagerDuty integration, no alerting thresholds configured. Appropriate for a desktop application.
- **Implication**: If an API is built, configure alerting on error rates and latency from the start.
- **Recommendation**: Include alerting architecture in any future service design.
- **Evidence**: No alerting configuration found in the repository.

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: Always evaluated as INFO. No business outcome metrics are published. No custom CloudWatch metrics, no dashboards, no KPI tracking. Appropriate for a desktop application — metrics are not centrally aggregated.
- **Implication**: If agent interactions are added, track business metrics (captures per agent session, upload success rates).
- **Recommendation**: Design business metrics into any future API surface.
- **Evidence**: No metrics publishing code found in the repository.

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: BLOCKER
- **Finding**: Greenshot is a Windows desktop WinForms application (`OutputType: WinExe`). No REST, GraphQL, AsyncAPI, or programmatic interface exists. All functionality is accessed through Windows GUI (system tray, hotkeys, WinForms dialogs). The only IPC is `WM_COPYDATA` for single-instance coordination. Agent integration would require UI automation (RPA).
- **Gap**: No programmatic API interface exists. Desktop-only GUI interaction model.
- **Recommendation**: Build a CLI or REST API wrapper around core screenshot/annotation capabilities. The `System.CommandLine` package reference suggests CLI support may be in development.
- **Evidence**: `src/Greenshot/Greenshot.csproj`, `src/Greenshot/GreenshotMain.cs`, `src/Greenshot/Forms/MainForm.cs`, `src/Greenshot/Helpers/CopyData.cs`

#### API-Q2: Machine-Readable API Specification
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — machine-readable spec is not applicable. No OpenAPI, AsyncAPI, GraphQL, or Smithy files found.
- **Gap**: N/A — no API surface to document.
- **Recommendation**: Auto-generate OpenAPI spec when building an API surface.
- **Evidence**: No API specification files in the repository.

#### API-Q3: Structured Error Responses
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — structured error responses are not applicable. Error handling uses WinForms dialogs (`BugReportForm`) and log4net logging.
- **Gap**: N/A — no API responses to structure.
- **Recommendation**: Design structured JSON error format for any future API.
- **Evidence**: `src/Greenshot/GreenshotMain.cs` (exception handlers)

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Read-only agent scope; write operations are user-initiated GUI actions, not API endpoints.
- **Gap**: N/A for read-only scope.
- **Recommendation**: Design idempotency into any future write API endpoints.
- **Evidence**: `src/Greenshot/Destinations/FileDestination.cs`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: Application outputs images (PNG, JPEG, BMP, TIFF, GIF). JSON used internally for OAuth2 token processing. No API response format exists.
- **Gap**: No API responses exist.
- **Recommendation**: Design JSON response format for any future API.
- **Evidence**: `src/Greenshot.Base/Core/CoreConfiguration.cs`, `src/Greenshot.Base/Core/JSONHelper.cs`

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`. Desktop application operations (screenshot capture) are synchronous GUI actions completing in milliseconds. Cloud uploads could be long-running but are user-initiated, not agent-callable.
- **Trigger**: Service has operations >30s OR long-running workflows
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`. Desktop application has no agent-observable state changes.
- **Trigger**: Service has state changes (stateful-crud, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No API surface exists to rate-limit or document. Third-party API rate limits are handled reactively in `NetworkHelper.cs`.
- **Gap**: No rate limiting documentation or headers.
- **Recommendation**: Implement rate limiting with standard headers for any future API.
- **Evidence**: `src/Greenshot.Base/Core/NetworkHelper.cs`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: No machine identity authentication exists. Greenshot authenticates outbound to third-party services via OAuth2 (`OAuth2Helper.cs`) and Windows Credential Manager (`CredentialsHelper.cs`), but has no mechanism for inbound caller authentication. No service accounts, API keys, mTLS, or API Gateway authorizers.
- **Gap**: No inbound authentication mechanism exists.
- **Recommendation**: Implement machine identity authentication alongside any new API surface.
- **Evidence**: `src/Greenshot.Base/Core/OAuth/OAuth2Helper.cs`, `src/Greenshot.Base/Core/CredentialsHelper.cs`, `src/Greenshot/GreenshotMain.cs`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY
- **Finding**: No inbound authorization model. No IAM policies, no role definitions. Application runs under desktop user session with full user permissions.
- **Gap**: No mechanism for scoped agent access.
- **Recommendation**: Design RBAC/ABAC into any future API surface with per-agent permission profiles.
- **Evidence**: `src/Greenshot.Base/Core/OAuth/OAuth2Helper.cs`, `src/Greenshot/GreenshotMain.cs`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY
- **Finding**: No action-level authorization. All operations equally available to the desktop user. Plugin architecture separates by destination but does not enforce access controls.
- **Gap**: No fine-grained authorization on operations.
- **Recommendation**: Implement action-level permissions for any future API.
- **Evidence**: `src/Greenshot/Destinations/`, `src/Greenshot/Helpers/CaptureHelper.cs`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: Archetype calibration: stateless-utility → INFO. Outbound OAuth2 tokens are user-owned, not delegated. No identity propagation architecture.
- **Gap**: No identity propagation mechanism.
- **Recommendation**: Architectural consideration for future API design.
- **Evidence**: `src/Greenshot.Base/Core/OAuth/OAuth2Helper.cs`

#### AUTH-Q5: Credential Management
- **Severity**: RISK-QUALITY
- **Finding**: Build-time template substitution from GitHub Actions secrets for API credentials. OAuth tokens stored as plaintext in local INI files. No secrets rotation mechanism. Windows Credential Manager used for Jira/Confluence but not for OAuth tokens.
- **Gap**: Plaintext OAuth token storage in INI files. No rotation mechanism.
- **Recommendation**: Migrate OAuth token storage to Windows DPAPI or Credential Manager. Apply consistently across all plugins.
- **Evidence**: `src/Greenshot.Plugin.Box/Greenshot.Plugin.Box.Credentials.template`, `src/Greenshot.Plugin.Imgur/Greenshot.Plugin.Imgur.Credentials.template`, `src/Directory.Build.props`, `.github/workflows/release.yml`, `src/Greenshot.Base/IniFile/IniConfig.cs`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity RISK-SAFETY, but surface-flag calibration: `has_auth_surface` is `false` AND `has_write_operations` is `false` → INFO.
- **Finding**: System does not execute agent-invoked write operations. log4net provides local file-based diagnostic logging. No audit trail with principal attribution.
- **Gap**: No audit logging — but not applicable for a desktop app with no inbound surface.
- **Recommendation**: Design audit logging into any future API surface.
- **Evidence**: `src/Greenshot/log4net-release.xml`, `src/Greenshot.Base/Core/LogHelper.cs`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: INFO
- **Finding**: `has_auth_surface` is `false` — suspension is a consumer responsibility. No agent identities exist to suspend.
- **Gap**: No identity lifecycle management.
- **Recommendation**: Include suspension/revocation capability in any future API identity system.
- **Evidence**: `src/Greenshot/GreenshotMain.cs`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity RISK-SAFETY. Surface-flag calibration: `has_write_operations` is `false` AND `has_http_rpc_surface` is `false` → INFO. Archetype calibration: stateless-utility → INFO.
- **Finding**: System exposes no write operations. No multi-step workflows to compensate.
- **Gap**: N/A for a desktop application with no programmatic write surface.
- **Recommendation**: N/A for current scope.
- **Evidence**: `src/Greenshot/Destinations/FileDestination.cs`, `src/Greenshot.Plugin.Imgur/ImgurUtils.cs`

#### STATE-Q2: Queryable Current State
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`. The extended trigger requires `agent_scope` to be `write-enabled` AND service to have persistent state. Neither condition is met.
- **Trigger**: agent_scope is write-enabled AND service has persistent state
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: INFO
- **Finding**: Extended question triggered (service has external dependencies via plugins). No circuit breakers, retry logic, or exponential backoff in outbound HTTP calls. `NetworkHelper.cs` has configurable timeouts (100s connect, 100s read/write) but no resilience patterns. Catches `WebException` with basic error logging. Given dev-library-application context, downgraded to INFO.
- **Gap**: No resilience patterns for outbound HTTP calls.
- **Recommendation**: Add Polly or equivalent resilience library, especially if plugin functionality is exposed via API.
- **Evidence**: `src/Greenshot.Base/Core/NetworkHelper.cs`, `src/Greenshot.Base/Core/CoreConfiguration.cs`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: INFO
- **Finding**: `has_http_rpc_surface` is `false` — API-layer rate limiting is not applicable. No inbound request surface to rate-limit.
- **Gap**: N/A — no API to protect.
- **Recommendation**: Include rate limiting in any future API design.
- **Evidence**: `src/Greenshot/GreenshotMain.cs`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Read-only scope; no write operations that could create blast radius.
- **Gap**: N/A for read-only scope.
- **Recommendation**: N/A for current scope.
- **Evidence**: No write-path API endpoints found.

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`. Priority is P2, not on the critical path.
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
- **Finding**: `has_http_rpc_surface` is `false` AND `has_persistent_data_store` is `false` — sandbox/staging is not applicable. Desktop application can be tested locally. Debug/Release build configurations exist.
- **Gap**: No server-side staging environment. Not applicable for a desktop application.
- **Recommendation**: No action required for desktop application testing.
- **Evidence**: `src/Greenshot/log4net-debug.xml`, `src/Greenshot/Greenshot.csproj`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO
- **Finding**: Archetype calibration: stateless-utility → INFO. Stage A scope gate: Greenshot captures screenshots (which could contain sensitive screen content), stores images on local filesystem, and uses OAuth tokens for cloud service authentication. However, the application is a local desktop utility — it does not own a database with user PII fields, does not store health/financial records, and does not persist credentials beyond the user's local machine. Not a data-handling target in the ARA sense.
- **Gap**: No data classification needed for a desktop screenshot tool that saves to local filesystem.
- **Recommendation**: If screenshots are exposed via API, consider content sensitivity classification.
- **Evidence**: `src/Greenshot.Base/Core/CoreConfiguration.cs`, `src/Greenshot.Base/IniFile/IniConfig.cs`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity RISK-SAFETY. Surface-flag calibration: `has_persistent_data_store` is `false` AND `has_logging_of_user_data` is `false` → INFO. Archetype calibration: stateless-utility → INFO.
- **Finding**: No persistent data store and no user-data logging. Screenshots stored on local filesystem; cloud uploads are user-directed to user-chosen services.
- **Gap**: Residency requirements do not apply to local desktop storage.
- **Recommendation**: Consider residency implications if agent-mediated screenshot sharing is implemented.
- **Evidence**: `src/Greenshot.Base/Core/CoreConfiguration.cs`

#### DATA-Q3: Selective Query Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`. No query endpoints exist.
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
- **Finding**: `has_logging_of_user_data` is `false` AND `has_persistent_data_store` is `false` — PII-in-logs risk is not applicable. log4net logs contain application diagnostics only. Archetype calibration: stateless-utility → INFO.
- **Gap**: N/A — no user PII in log pipeline.
- **Recommendation**: Review `NetworkHelper.cs` response logging if building an API that processes user data.
- **Evidence**: `src/Greenshot/log4net-release.xml`, `src/Greenshot.Base/Core/NetworkHelper.cs`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: Always evaluated as INFO. No data quality metrics applicable to a screenshot capture tool. Image quality is a function of capture settings (format, JPEG quality, color reduction).
- **Gap**: N/A for a screenshot tool.
- **Recommendation**: No action required.
- **Evidence**: `src/Greenshot.Base/Core/CoreConfiguration.cs`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: Nerdbank.GitVersioning provides semantic versioning for releases (`src/version.json`: version 1.4, `src/Directory.Build.props`: `Nerdbank.GitVersioning 3.9.50`). GitHub Actions creates versioned tags and releases. However, no API contracts exist to version (no OpenAPI, no schema files, no consumer-driven contract tests, no breaking-change detection in CI).
- **Gap**: No API contracts to version. No breaking-change detection in CI.
- **Recommendation**: When building an API, define OpenAPI spec and add breaking-change detection to CI.
- **Evidence**: `src/version.json`, `src/Directory.Build.props`, `.github/workflows/release.yml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Always evaluated as INFO. Greenshot uses clear, descriptive naming: `OutputFilePath`, `CaptureDelay`, `WindowCaptureMode`, `CaptureHelper`, `ClipboardDestination`, `OAuth2Helper`. No legacy abbreviations found.
- **Gap**: None — naming conventions are good.
- **Recommendation**: Maintain conventions in any future API.
- **Evidence**: `src/Greenshot.Base/Core/CoreConfiguration.cs`, `src/Greenshot.Base/Core/NetworkHelper.cs`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: Always evaluated as INFO. No data catalog, metadata layer, or data dictionary. Not applicable for a desktop screenshot tool.
- **Gap**: N/A.
- **Recommendation**: No action required.
- **Evidence**: No data catalog files found.

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: INFO
- **Finding**: `has_http_rpc_surface` is `false` — tracing is not applicable. log4net provides text-format local file logging. No OpenTelemetry, no X-Ray, no JSON structured logs, no correlation IDs.
- **Gap**: No distributed tracing or structured logging. Appropriate for a desktop app.
- **Recommendation**: Implement structured JSON logging with OpenTelemetry if building a service.
- **Evidence**: `src/Greenshot/log4net-release.xml`, `src/Greenshot.Base/Core/LogHelper.cs`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: INFO
- **Finding**: `has_http_rpc_surface` is `false` — alerting is not applicable. No CloudWatch alarms, no PagerDuty, no alerting thresholds.
- **Gap**: No alerting. Appropriate for a desktop app.
- **Recommendation**: Include alerting in any future service architecture.
- **Evidence**: No alerting configuration found.

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: Always evaluated as INFO. No business outcome metrics published. Appropriate for a desktop application.
- **Gap**: No metrics. Not applicable for a desktop app.
- **Recommendation**: Design business metrics into any future API.
- **Evidence**: No metrics publishing code found.

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: N/A
- **Finding**: This is assessed under the dev-library-application override (library N/A mapping). This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: N/A
- **Finding**: This is assessed under the dev-library-application override (library N/A mapping). This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q3: Rollback Capability
- **Severity**: N/A
- **Finding**: This is assessed under the dev-library-application override (library N/A mapping). This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q4: API Test Coverage
- **Severity**: N/A
- **Finding**: This is assessed under the dev-library-application override (library N/A mapping). This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: N/A
- **Finding**: This is assessed under the dev-library-application override (library N/A mapping). This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| src/Greenshot/GreenshotMain.cs | API-Q1, API-Q3, AUTH-Q1, AUTH-Q2, AUTH-Q6, AUTH-Q7, STATE-Q5 |
| src/Greenshot/Greenshot.csproj | API-Q1, API-Q5, HITL-Q3 |
| src/Greenshot/Forms/MainForm.cs | API-Q1 |
| src/Greenshot/Helpers/CopyData.cs | API-Q1 |
| src/Greenshot/Helpers/CaptureHelper.cs | AUTH-Q3 |
| src/Greenshot/Helpers/ResourceMutex.cs | STATE-Q3 |
| src/Greenshot/Destinations/FileDestination.cs | API-Q4, STATE-Q1 |
| src/Greenshot/Destinations/ (directory) | AUTH-Q3 |
| src/Greenshot.Base/Core/NetworkHelper.cs | API-Q8, AUTH-Q4, STATE-Q4, DATA-Q6, DISC-Q2 |
| src/Greenshot.Base/Core/CoreConfiguration.cs | API-Q5, STATE-Q4, DATA-Q1, DATA-Q2, DATA-Q7, DISC-Q2 |
| src/Greenshot.Base/Core/OAuth/OAuth2Helper.cs | AUTH-Q1, AUTH-Q2, AUTH-Q4 |
| src/Greenshot.Base/Core/CredentialsHelper.cs | AUTH-Q1, AUTH-Q5 |
| src/Greenshot.Base/Core/JSONHelper.cs | API-Q5 |
| src/Greenshot.Base/Core/LogHelper.cs | AUTH-Q6, OBS-Q1 |
| src/Greenshot.Base/IniFile/IniConfig.cs | AUTH-Q5, DATA-Q1 |
| src/Greenshot.Plugin.Imgur/ImgurUtils.cs | API-Q4, STATE-Q1 |
| src/Greenshot.Plugin.Box/BoxUtils.cs | STATE-Q4 |
| src/Greenshot.Plugin.Dropbox/DropboxUtils.cs | STATE-Q4 |
| src/Greenshot.Plugin.Jira/JiraConnector.cs | STATE-Q4 |
| src/Greenshot.Plugin.Confluence/Confluence.cs | STATE-Q4 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| .github/workflows/release.yml | AUTH-Q5, DISC-Q1 |
| .github/workflows/choco-publish.yml | (supporting evidence for CI/CD maturity) |
| .github/workflows/purge-cloudflare-cache.yml | (supporting evidence for CI/CD maturity) |
| .github/workflows/update-gh-pages.yml | (supporting evidence for CI/CD maturity) |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| src/Greenshot/log4net-release.xml | AUTH-Q6, DATA-Q6, OBS-Q1 |
| src/Greenshot/log4net-debug.xml | AUTH-Q6, HITL-Q3 |
| src/Greenshot.Plugin.Box/Greenshot.Plugin.Box.Credentials.template | AUTH-Q5 |
| src/Greenshot.Plugin.Imgur/Greenshot.Plugin.Imgur.Credentials.template | AUTH-Q5 |
| src/Greenshot.Plugin.Dropbox/Greenshot.Plugin.Dropbox.Credentials.template | AUTH-Q5 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| src/Directory.Build.props | AUTH-Q5, DISC-Q1 |
| src/version.json | DISC-Q1 |
