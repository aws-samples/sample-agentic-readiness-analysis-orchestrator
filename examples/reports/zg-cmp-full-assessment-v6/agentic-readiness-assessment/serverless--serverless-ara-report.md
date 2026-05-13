# Agentic Readiness Assessment Report

**Target**: /Users/lucasdu/Documents/AWS-MAC/2026-projects/sample-agentic-readiness-assessment/services/serverless--serverless
**Date**: 2025-05-08
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Service Archetype**: stateless-utility (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: javascript, serverless, iac, cli
**Context**: Serverless Framework CLI for building and deploying serverless apps.

**Archetype Justification**: This is a CLI tool and developer framework (npm package `serverless` / `@serverlessinc/sf-core`) that generates and deploys IaC to AWS. It does not own persistent state, does not expose a production HTTP API, and does not execute agent-invoked operations. The MCP server component is a local dev-time tool that runs on localhost for IDE integration.

**Surface flags**:
- has_persistent_data_store: false
- has_http_rpc_surface: false
- has_auth_surface: false
- has_write_operations: false
- has_logging_of_user_data: false

**Dev-Library-Application Override**: Applied. Service archetype is `stateless-utility` AND 5/5 surface flags are `false`. This repo functions as a developer tool/CLI — not a deployed service that agents would call in production. The `library` N/A mapping is applied for scoring purposes. The original `repo_type` value (`application`) is preserved.

---

## Readiness Profile: Agent-Ready

**BLOCKERs**: 0 | **RISK-SAFETY**: 0 | **RISK-QUALITY**: 0 | **INFOs**: 5

This repo has 0 High findings, 0 Medium findings, and 0 safety-impact Medium findings. The matched rule is "0 High, ≤1 Medium → Agent-Ready."

The V6 classification aligns with the V5 Readiness Profile: 0 BLOCKERs and 0 RISK-SAFETY findings → Agent-Ready. This CLI tool is not a target system that agents call — it IS a tool that agents use. The assessment reflects that distinction.

Cleared for autonomous operation. Instrument observability. Define scope explicitly. Run controlled pilot first.

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

**Core Questions Evaluated**: 10 (24 core minus 14 N/A by dev-library-application override)
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
- **Finding**: This is a CLI tool, not a deployed API service. The Serverless Framework exposes a command-line interface (via `yargs` in `packages/sf-core/bin/sf-core.js`), not a REST/GraphQL/AsyncAPI interface. The MCP server (`packages/mcp/src/server.js`) exposes 15 tools via the Model Context Protocol on localhost for IDE integration — this is a dev-time local tool, not a production API.
- **Implication**: Agents interact with this tool via CLI invocation or MCP protocol (stdio/SSE transport), not via HTTP APIs. The MCP tool definitions in `packages/mcp/src/tools-definition.js` serve as the agent integration surface.
- **Recommendation**: The MCP tool definitions are the de facto agent interface. Ensure they remain stable and versioned as the primary agent consumption surface.
- **Evidence**: `packages/sf-core/bin/sf-core.js`, `packages/mcp/src/server.js`, `packages/mcp/src/tools-definition.js`

### AUTH-Q6: Immutable Audit Logging ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity would be RISK-SAFETY, but dev-library-application override applies.
- **Finding**: System does not execute agent-invoked write operations — audit logging is a consumer responsibility. The CLI/framework is called by applications and developers that own the audit context. The tool itself logs diagnostics to stderr (`console.error`) for local debugging.
- **Implication**: Audit trails for agent actions belong in the AWS account where deployments happen (CloudTrail), not in the CLI tool itself.
- **Recommendation**: No action required for the tool itself. Consumers deploying via Serverless Framework inherit CloudTrail audit coverage from their AWS accounts.
- **Evidence**: `packages/mcp/src/server.js` (console.error logging), `packages/sf-core/bin/sf-core.js`

### AUTH-Q7: Agent Identity Suspension

- **Severity**: INFO
- **Finding**: System does not issue or enforce agent identities — suspension is a consumer responsibility. Libraries and utilities are invoked by applications that own identity lifecycle. The CLI authenticates to AWS using the caller's credentials (IAM roles, profiles configured via `@aws-sdk/credential-providers`).
- **Implication**: Agent identity suspension would be managed at the AWS IAM layer (revoking the IAM role or API key used by the agent), not within this CLI tool.
- **Recommendation**: No action required for the tool itself.
- **Evidence**: `packages/sf-core/package.json` (dependency on `@aws-sdk/credential-providers`, `jwt-decode`)

### DISC-Q1: Schema Versioning and API Contracts

- **Severity**: INFO
- **Finding**: The MCP tool definitions (`packages/mcp/src/tools-definition.js`) use Zod schemas for parameter validation, providing typed tool contracts. The framework is versioned via `package.json` (currently v4.33.2 for `@serverlessinc/sf-core`). GitHub Actions CI runs linting and tests on PRs. However, there is no formal breaking-change detection for MCP tool schemas.
- **Implication**: MCP tool consumers (AI agents) may experience silent breaking changes if tool parameters or return shapes change without notice.
- **Recommendation**: Consider adding schema snapshot tests for MCP tool definitions to detect breaking changes in CI. The Zod schemas in `tools-definition.js` could be exported and diffed against a baseline.
- **Evidence**: `packages/mcp/src/tools-definition.js`, `packages/sf-core/package.json`, `.github/workflows/ci-framework.yml`

### HITL-Q3: Sandbox/Staging Environment

- **Severity**: INFO
- **Finding**: Library/utility — does not own staging environments. The CI pipeline uses a `TEST_STAGE` environment variable for integration tests against a real AWS account (role: `arn:aws:iam::762003938904:role/GithubActionsDeploymentRole`). This serves as a CI testing environment.
- **Implication**: Consumers testing agents with the Serverless Framework would create their own sandbox AWS accounts. The tool itself provides `--stage` flag for multi-environment deployment.
- **Recommendation**: No action required for the tool itself.
- **Evidence**: `.github/workflows/ci-framework.yml` (TEST_STAGE env var, AWS role assumption)

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: This is a CLI tool/developer framework, not a deployed API service. The primary interface is the command line (`sf-core` binary) and the MCP protocol (15 tools via `@modelcontextprotocol/sdk`). No REST/GraphQL/AsyncAPI production endpoint exists.
- **Gap**: No formal API specification exists for the MCP tool surface — tool definitions are in code only.
- **Recommendation**: The MCP tool definitions serve as the agent interface. Consider generating documentation from the Zod schemas.
- **Evidence**: `packages/sf-core/bin/sf-core.js`, `packages/mcp/src/server.js`, `packages/mcp/src/tools-definition.js`

#### API-Q2: Machine-Readable API Specification
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — machine-readable spec is not applicable. The MCP server uses the `@modelcontextprotocol/sdk` which has its own discovery protocol. Tool schemas are defined via Zod in `packages/mcp/src/tools-definition.js`.
- **Gap**: N/A — MCP protocol provides built-in tool discovery.
- **Recommendation**: No action required.
- **Evidence**: `packages/mcp/src/tools-definition.js`, `packages/mcp/package.json`

#### API-Q3: Structured Error Responses
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — structured error responses are not applicable. The CLI uses structured error handling (`errorHandler` in `packages/sf-core/bin/sf-core.js`) and the MCP tools return structured results via the MCP protocol.
- **Gap**: N/A
- **Recommendation**: No action required.
- **Evidence**: `packages/sf-core/bin/sf-core.js`, `packages/mcp/src/tools-definition.js`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO.
- **Finding**: Read-only agent scope. The CLI itself is a deployment tool — idempotency of deployments is determined by the target AWS services (CloudFormation is inherently idempotent via stack updates). The MCP tools are read-only diagnostic tools.
- **Gap**: N/A for read-only scope.
- **Recommendation**: No action required.
- **Evidence**: `packages/mcp/src/tools-definition.js` (all 15 tools are read/query operations)

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
- **Severity**: N/A
- **Finding**: Dev-library-application override applied. This CLI tool delegates authentication entirely to the caller's AWS credentials (via `@aws-sdk/credential-providers`). It does not issue or validate machine identities itself. Agent identity is managed at the AWS IAM layer.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: N/A
- **Finding**: Dev-library-application override applied. The CLI tool uses whatever IAM permissions the caller provides. Scoped permissions are enforced by the AWS IAM policies attached to the caller's role/user, not by the tool itself.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### AUTH-Q3: Action-Level Authorization
- **Severity**: N/A
- **Finding**: Dev-library-application override applied. Action-level authorization is enforced by AWS IAM policies, not by this CLI tool.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Archetype calibration: stateless-utility → INFO (downgraded)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### AUTH-Q5: Credential Management
- **Severity**: N/A
- **Finding**: Dev-library-application override applied. The CLI uses `@aws-sdk/credential-providers` for credential resolution (profiles, environment variables, IAM roles). No credentials are hardcoded. Secrets like `SERVERLESS_LICENSE_KEY_DEV` are stored as GitHub Actions secrets, not in code.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity would be RISK-SAFETY, but dev-library-application surface-flag calibration applies: `has_auth_surface` is false AND `has_write_operations` is false.
- **Finding**: System does not execute agent-invoked write operations — audit logging is a consumer responsibility. The library/utility is called by applications that own the audit context.
- **Gap**: No gap — correct architecture.
- **Recommendation**: No action required.
- **Evidence**: `packages/mcp/src/server.js`, `packages/sf-core/bin/sf-core.js`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: INFO
- **Finding**: System does not issue or enforce agent identities — suspension is a consumer responsibility. Libraries and utilities are invoked by applications that own identity lifecycle.
- **Gap**: No gap — correct architecture.
- **Recommendation**: No action required.
- **Evidence**: `packages/sf-core/package.json`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — base severity would be RISK-SAFETY, but archetype calibration for `stateless-utility` applies, AND dev-library-application override.
- **Finding**: System exposes no write operations — compensation logic is not applicable. The CLI tool orchestrates CloudFormation deployments which have their own rollback mechanism (stack rollback on failure). The MCP tools are all read-only diagnostic queries.
- **Gap**: No gap.
- **Recommendation**: No action required.
- **Evidence**: `packages/mcp/src/tools-definition.js`, `packages/serverless/lib/plugins/aws/package/lib/core-cloudformation-template.json`

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
- **Finding**: System exposes no HTTP/RPC surface — API-layer rate limiting is not applicable. The MCP server runs on localhost for IDE integration. Libraries invoked by consuming applications inherit the consumer's rate limiting, not their own.
- **Gap**: No gap — correct architecture.
- **Recommendation**: No action required.
- **Evidence**: `packages/mcp/src/server.js` (localhost-only Express server)

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
- **Finding**: Library/utility — does not own staging environments. The CI pipeline uses `TEST_STAGE` environment variable for integration tests against a real AWS account. Consumers create their own sandbox environments using the tool's `--stage` flag.
- **Gap**: No gap — correct architecture.
- **Recommendation**: No action required.
- **Evidence**: `.github/workflows/ci-framework.yml`, `.github/workflows/release-framework.yml`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification ⚡
- **Severity**: INFO
- **Finding**: Dev-library-application override applied. Not a data-handling target — no PII/PHI/financial/credential data is stored, processed, or logged. The CLI tool processes serverless configuration files and deploys infrastructure. It does not own or persist user business data.
- **Gap**: No gap.
- **Recommendation**: No action required.
- **Evidence**: `packages/serverless/package.json`, `packages/sf-core/package.json`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — but dev-library-application override applies.
- **Finding**: No persistent data store and no user-data logging — residency requirements do not apply. The CLI tool deploys to whatever region the user specifies. Data residency is a property of the deployed infrastructure, not the deployment tool.
- **Gap**: No gap.
- **Recommendation**: No action required.
- **Evidence**: `packages/mcp/src/tools-definition.js` (regionParam defined for AWS region selection)

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
- **Finding**: System does not log user data and holds no user data — PII-in-logs risk is not applicable. The CLI logs diagnostic information to stderr (session IDs, connection events). No user-submitted PII flows through the logging pipeline.
- **Gap**: No gap.
- **Recommendation**: No action required.
- **Evidence**: `packages/mcp/src/server.js` (console.error for sessionId logging)

#### DATA-Q7: Data Quality Awareness
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Always evaluated as INFO
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: INFO
- **Finding**: The MCP tool definitions use Zod schemas for parameter validation (`packages/mcp/src/tools-definition.js`), providing typed tool contracts. The framework is versioned via semver in `package.json` (v4.33.2). CI runs tests on PRs. No formal breaking-change detection exists for MCP tool schemas specifically.
- **Gap**: No breaking-change detection for MCP tool parameter schemas.
- **Recommendation**: Consider adding schema snapshot tests for MCP tool definitions to detect breaking changes in CI.
- **Evidence**: `packages/mcp/src/tools-definition.js`, `packages/sf-core/package.json`, `.github/workflows/ci-framework.yml`

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
- **Finding**: Library/utility — tracing and correlation are consumer concerns. The CLI tool logs to stderr for local debugging. The MCP server logs connection/disconnection events. No OpenTelemetry or X-Ray instrumentation exists in the tool itself — this is expected for a CLI tool.
- **Gap**: No gap — correct architecture.
- **Recommendation**: No action required.
- **Evidence**: `packages/mcp/src/server.js`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: INFO
- **Finding**: Library/utility — alerting on error rates and latency is a consumer concern. The CLI does not expose a deployed API to monitor. Consumers deploying services with the framework define their own CloudWatch alarms (the framework even has an alerts plugin at `packages/serverless/lib/plugins/aws/alerts/`).
- **Gap**: No gap — correct architecture.
- **Recommendation**: No action required.
- **Evidence**: `packages/serverless/lib/plugins/aws/alerts/`

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
- **Finding**: This is a `library` (dev-library-application override). This question does not apply. The CLI tool does not own IaC for API gateways, IAM roles, or networking — its consumers do.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: N/A
- **Finding**: This is a `library` (dev-library-application override). This question does not apply. Library build pipelines validate package contracts (semver, typed exports), not API contracts.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q3: Rollback Capability
- **Severity**: N/A
- **Finding**: This is a `library` (dev-library-application override). This question does not apply. Library rollback is handled via package version pinning by consumers.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q4: API Test Coverage
- **Severity**: N/A
- **Finding**: This is a `library` (dev-library-application override). This question does not apply. The framework has extensive test coverage (Jest unit + integration tests across packages) but API test coverage in the ENG-Q4 sense is not applicable to a CLI tool.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: N/A
- **Finding**: This is a `library` (dev-library-application override). This question does not apply. The CLI tool does not own data stores.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `packages/sf-core/bin/sf-core.js` | API-Q1, API-Q3, AUTH-Q6 |
| `packages/mcp/src/server.js` | API-Q1, AUTH-Q6, STATE-Q1, STATE-Q5, DATA-Q6, OBS-Q1 |
| `packages/mcp/src/tools-definition.js` | API-Q1, API-Q2, API-Q3, API-Q4, STATE-Q1, DATA-Q2, DISC-Q1 |
| `packages/mcp/src/utils/analytics-utils.js` | API-Q1 |
| `packages/mcp/src/stdio-server.js` | API-Q1 |
| `packages/serverless/lib/plugins/aws/alerts/` | OBS-Q2 |
| `packages/serverless/lib/plugins/aws/package/lib/core-cloudformation-template.json` | STATE-Q1 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/ci-framework.yml` | DISC-Q1, HITL-Q3 |
| `.github/workflows/release-framework.yml` | HITL-Q3 |
| `.github/workflows/ci-engine.yml` | DISC-Q1 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `packages/mcp/package.json` | API-Q2 |
| `packages/serverless/package.json` | DATA-Q1 |
| `packages/sf-core/package.json` | AUTH-Q7, DISC-Q1 |
| `package.json` | DISC-Q1 |
