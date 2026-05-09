# Agentic Readiness Assessment Report

**Target**: realworld-apps--angular-realworld-example-app
**Date**: 2025-05-08
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Service Archetype**: stateless-utility (auto-detected)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: typescript, frontend, angular
**Context**: Angular reference implementation of the RealWorld spec.

**Archetype Justification**: Pure frontend SPA (Angular 21) with no backend code, no database, no server-side runtime. All data operations are delegated to an external API (`https://api.realworld.show/api`). The repository contains only client-side rendering logic and build tooling.

**INFO — Dev-Library-Application Override Applied**: This repository is classified as `application` (repo_type) with `stateless-utility` archetype, and all 5 surface flags are `false`. Per Step 1.5, this triggers the dev-library-application override — the `library` N/A mapping is applied as baseline for scoring purposes. The repo functions as a frontend scaffold/template that does not hold data, does not expose a server-side API, and does not execute agent-invoked operations. Original `repo_type` preserved as `application`.

**Surface flags**:
- has_persistent_data_store: false
- has_http_rpc_surface: false
- has_auth_surface: false
- has_write_operations: false
- has_logging_of_user_data: false

---

## Readiness Profile: Agent-Ready

**BLOCKERs**: 0 | **RISK-SAFETY**: 0 | **RISK-QUALITY**: 0 | **INFOs**: 8

Cleared for autonomous operation. Instrument observability. Define scope explicitly. Run controlled pilot first.

### V6 Classification Rationale

This repo has 0 High findings, 0 Medium findings, and 0 safety-impact Medium findings. The matched rule is: "0 High, ≤1 Medium → Agent-Ready." The V6 classification aligns with the V5 Readiness Profile — both yield Agent-Ready. This is expected for a frontend SPA that delegates all data, auth, and API concerns to an external backend.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 0 |
| RISK-SAFETY | 0 |
| RISK-QUALITY | 0 |
| INFO | 8 |
| N/A | 5 |
| Not Evaluated (extended) | 30 |
| **Total** | **43** |

**Core Questions Evaluated**: 8 (dev-library-application override applies library N/A mapping; most questions resolve to INFO via surface-flag downgrade)
**Extended Questions Triggered**: 0
**Extended Questions Not Triggered**: 30
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
- **Finding**: This is a pure frontend SPA that does not expose any server-side API. It consumes an external backend API at `https://api.realworld.show/api`. The RealWorld spec provides an OpenAPI 3.1.0 specification in `realworld/specs/api/openapi.yml`, but this describes the external backend — not an API exposed by this repository.
- **Implication**: If an agent needs to interact with this application, it would do so via browser automation (fragile) or by calling the backend API directly (which is a separate system). This repo is not an agent integration target.
- **Recommendation**: No action required for this repo. Assess the backend API service (`api.realworld.show`) separately if agent integration with the data layer is intended.
- **Evidence**: `src/app/core/interceptors/api.interceptor.ts` (hardcoded API URL), `realworld/specs/api/openapi.yml` (external API spec)

### AUTH-Q1: Machine Identity Authentication

- **Severity**: INFO
- **Finding**: System does not issue or enforce machine identities — it is a browser SPA that authenticates human users via JWT tokens against an external API. Authentication is delegated entirely to the backend.
- **Implication**: Machine identity for agent access would need to be implemented at the backend API layer, not in this frontend application.
- **Recommendation**: No action required for this repo. Machine identity controls belong on the backend service.
- **Evidence**: `src/app/core/auth/services/jwt.service.ts`, `src/app/core/interceptors/token.interceptor.ts`

### AUTH-Q6: Immutable Audit Logging ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — but further downgraded to INFO because `has_auth_surface` is `false` AND `has_write_operations` is `false`. System does not execute agent-invoked write operations — audit logging is a consumer responsibility.
- **Finding**: No audit logging exists in this frontend SPA. There is no server-side code, no CloudTrail configuration, and no structured logging of any kind.
- **Implication**: Audit logging for agent actions must be implemented at the backend API layer that this SPA consumes.
- **Recommendation**: No action required for this repo. The backend API service should implement immutable audit logging.
- **Evidence**: No logging code found in any source file. No IaC or observability configuration present.

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — but further downgraded to INFO because `has_write_operations` is `false`. System exposes no write operations — compensation logic is not applicable.
- **Finding**: This is a frontend SPA with no server-side write operations. All mutations (article creation, user updates, etc.) are HTTP calls to the external backend API.
- **Implication**: Compensation/rollback for multi-step operations is a backend concern, not a frontend concern.
- **Recommendation**: No action required for this repo.
- **Evidence**: `src/app/features/article/services/articles.service.ts` (all writes delegated to external API)

### STATE-Q5: Rate Limiting and Throttling

- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — API-layer rate limiting is not applicable. This is a browser SPA that does not accept inbound requests from agents or services.
- **Implication**: Rate limiting for agent traffic must be enforced at the backend API layer that this SPA consumes.
- **Recommendation**: No action required for this repo.
- **Evidence**: No rate limiting middleware or configuration found. No server-side code present.

### DATA-Q1: Sensitive Data Classification ⚡

- **Severity**: INFO
- **Finding**: Dev-library-application override applied — this frontend scaffold does not own the data that the consuming backend stores. The SPA handles JWT tokens in localStorage and displays user data received from the API, but it does not persist, classify, or scope data access itself.
- **Implication**: Data classification and scoping must be implemented at the backend API layer. The SPA's exposure of user tokens in localStorage is a client-side security concern (XSS risk), not a data classification concern.
- **Recommendation**: No action required for this repo from an ARA perspective. The backend API should implement field-level scoping for agent-facing responses.
- **Evidence**: `src/app/core/auth/user.model.ts` (User interface with email, token, username, bio, image), `src/app/core/auth/services/jwt.service.ts` (localStorage token storage)

### DATA-Q2: Data Residency and Sovereignty ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — but further downgraded to INFO because `has_persistent_data_store` is `false` AND `has_logging_of_user_data` is `false`. No persistent data store and no user-data logging — residency requirements do not apply.
- **Finding**: This frontend SPA does not store data persistently. All data is fetched from and stored at the external backend API.
- **Implication**: Data residency constraints apply to the backend service and its data stores, not to this frontend.
- **Recommendation**: No action required for this repo.
- **Evidence**: No database connections, no persistent storage configuration found.

### HITL-Q3: Sandbox/Staging Environment

- **Severity**: INFO
- **Finding**: Dev-library-application override applied — frontend SPAs and scaffolds do not own staging environments. The application can be run locally via `ng serve` for development purposes, and E2E tests use mocked API responses via Playwright route interception.
- **Implication**: Testing agent interactions with the data layer requires a staging instance of the backend API, not a staging frontend.
- **Recommendation**: No action required for this repo.
- **Evidence**: `playwright.config.ts`, `e2e/helpers/api.ts` (Playwright API mocking)

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: This is a pure frontend SPA that does not expose any server-side API. It consumes an external backend API at `https://api.realworld.show/api`. An OpenAPI 3.1.0 spec exists at `realworld/specs/api/openapi.yml` but describes the external backend, not this repo.
- **Gap**: No API is exposed by this repository — it is a browser application, not a service.
- **Recommendation**: No action required. Assess the backend API separately.
- **Evidence**: `src/app/core/interceptors/api.interceptor.ts`, `realworld/specs/api/openapi.yml`

#### API-Q2: Machine-Readable API Specification
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — machine-readable spec is not applicable. This is a frontend SPA with no server-side API to describe.
- **Gap**: N/A — no API surface exists to document.
- **Recommendation**: No action required.
- **Evidence**: No server-side code or API endpoint definitions found.

#### API-Q3: Structured Error Responses
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — structured error responses are not applicable. The SPA does implement client-side error normalization via `error.interceptor.ts` for display purposes, but it does not serve error responses to callers.
- **Gap**: N/A — no API surface exists.
- **Recommendation**: No action required.
- **Evidence**: `src/app/core/interceptors/error.interceptor.ts`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO. Read-only agents do not execute write operations.
- **Finding**: This SPA delegates all write operations to the external backend API. The frontend does not implement or enforce idempotency — that responsibility lies with the backend.
- **Gap**: N/A for read-only scope.
- **Recommendation**: No action required for this repo.
- **Evidence**: `src/app/features/article/services/articles.service.ts` (POST/PUT/DELETE calls to external API)

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
- **Finding**: System does not issue or enforce machine identities. It is a browser SPA that authenticates human users via JWT tokens against an external API. The token interceptor attaches a JWT `Authorization: Token <jwt>` header to outbound requests but does not validate inbound identities.
- **Gap**: No machine identity mechanism exists — but this is expected for a frontend SPA.
- **Recommendation**: No action required. Machine identity belongs on the backend.
- **Evidence**: `src/app/core/auth/services/jwt.service.ts`, `src/app/core/interceptors/token.interceptor.ts`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: INFO
- **Finding**: System does not enforce permissions — it is a UI layer. Route guards (`requireAuth`) control UI navigation but do not enforce data access. The external API enforces authorization.
- **Gap**: No permission enforcement in this repo — expected for a frontend.
- **Recommendation**: No action required.
- **Evidence**: `src/app/app.routes.ts` (route guards), `src/app/core/auth/if-authenticated.directive.ts`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: INFO
- **Finding**: System does not enforce action-level authorization — it renders UI conditionally based on auth state but delegates all authorization enforcement to the backend API.
- **Gap**: No authorization enforcement — expected for a frontend.
- **Recommendation**: No action required.
- **Evidence**: `src/app/app.routes.ts`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Archetype calibration downgrades to INFO for stateless-utility
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### AUTH-Q5: Credential Management
- **Severity**: INFO
- **Finding**: The SPA stores JWT tokens in `window.localStorage['jwtToken']`. No secrets management system is used — but this is expected for a browser application where localStorage is the standard client-side storage mechanism. No hardcoded secrets, API keys, or credentials were found in the source code. The CI/CD pipeline uses GitHub Secrets for AWS credentials.
- **Gap**: No server-side secrets management — but none is applicable for a frontend SPA.
- **Recommendation**: No action required for this repo. The debug interface (`window.__conduit_debug__`) exposes auth state and should be disabled in production builds.
- **Evidence**: `src/app/core/auth/services/jwt.service.ts`, `.github/workflows/deploy.yml` (uses `secrets.AWS_ACCESS_KEY_ID`)

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — further downgraded to INFO because `has_auth_surface` is `false` AND `has_write_operations` is `false`. System does not execute agent-invoked write operations — audit logging is a consumer responsibility.
- **Finding**: No audit logging exists in this frontend SPA. No server-side code, no CloudTrail, no structured logging.
- **Gap**: No audit logging — but not applicable for a frontend SPA.
- **Recommendation**: No action required.
- **Evidence**: No logging code found in source files.

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: INFO
- **Finding**: System does not issue or enforce agent identities — suspension is a consumer responsibility. Libraries and utilities are invoked by applications that own identity lifecycle. This SPA does not manage any agent identities.
- **Gap**: No identity management — expected for a frontend.
- **Recommendation**: No action required.
- **Evidence**: No identity management code found.

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — further downgraded to INFO because `has_write_operations` is `false`. System exposes no write operations — compensation logic is not applicable.
- **Finding**: Frontend SPA with no server-side write operations. All mutations delegated to external API.
- **Gap**: Not applicable.
- **Recommendation**: No action required.
- **Evidence**: `src/app/features/article/services/articles.service.ts`

#### STATE-Q2: Queryable Current State
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO.
- **Finding**: Read-only agents do not perform writes. This SPA has no server-side concurrency concerns.
- **Gap**: Not applicable for read-only frontend.
- **Recommendation**: No action required.
- **Evidence**: No concurrency control code found — expected for a frontend SPA.

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has external dependencies (calls other services or external APIs)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: INFO
- **Finding**: No HTTP/RPC surface — API-layer rate limiting is not applicable. This SPA does not accept inbound requests.
- **Gap**: Not applicable for a frontend SPA.
- **Recommendation**: No action required.
- **Evidence**: No server-side code present.

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO. Read-only agents cannot modify records, trigger spend, or delete data.
- **Finding**: No write operations exist in this frontend SPA. Transaction limits are not applicable.
- **Gap**: Not applicable.
- **Recommendation**: No action required.
- **Evidence**: No server-side write operations.

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
- **Finding**: Dev-library-application override applied. The application runs locally via `ng serve` and E2E tests use Playwright API mocking. No dedicated staging environment with production-equivalent backend data exists.
- **Gap**: No staging environment — but not applicable for a frontend scaffold.
- **Recommendation**: No action required.
- **Evidence**: `playwright.config.ts`, `e2e/helpers/api.ts`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification ⚡
- **Severity**: INFO
- **Finding**: Dev-library-application override applied. This frontend scaffold does not own data. JWT tokens are stored in localStorage and user data is displayed from API responses, but the SPA does not classify, persist, or scope data access.
- **Gap**: Not applicable — data classification is a backend concern.
- **Recommendation**: No action required.
- **Evidence**: `src/app/core/auth/user.model.ts`, `src/app/core/auth/services/jwt.service.ts`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — further downgraded to INFO because `has_persistent_data_store` is `false` AND `has_logging_of_user_data` is `false`.
- **Finding**: No persistent data store and no user-data logging — residency requirements do not apply.
- **Gap**: Not applicable.
- **Recommendation**: No action required.
- **Evidence**: No database connections or persistent storage found.

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
- **Finding**: System does not log user data and holds no user data — PII-in-logs risk is not applicable. No logging framework or structured logging exists in this SPA.
- **Gap**: Not applicable.
- **Recommendation**: No action required.
- **Evidence**: No logging code found in any source file.

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
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`. Dev-library-application override applied — library contract stability is expressed via typed exports (TypeScript interfaces) and package versioning.
- **Trigger**: Always evaluated for core — but dev-library-application override applies library N/A mapping
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
- **Finding**: Library/utility — tracing and correlation are consumer concerns. This frontend SPA has no server-side request processing to trace. No OpenTelemetry, X-Ray, or structured logging is present — which is expected for a browser application.
- **Gap**: Not applicable for a frontend SPA.
- **Recommendation**: No action required.
- **Evidence**: No tracing or logging libraries in `package.json`.

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: INFO
- **Finding**: Library/utility — alerting on error rates and latency is a consumer concern. This frontend SPA does not serve API requests and has no CloudWatch, PagerDuty, or alerting configuration.
- **Gap**: Not applicable for a frontend SPA.
- **Recommendation**: No action required.
- **Evidence**: No monitoring or alerting configuration found.

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
- **Finding**: This is a `application` repository with dev-library-application override (library N/A mapping applied). ENG-Q1 through ENG-Q5 are N/A under the library N/A mapping.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: N/A
- **Finding**: This is a `application` repository with dev-library-application override (library N/A mapping applied). ENG-Q1 through ENG-Q5 are N/A under the library N/A mapping.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q3: Rollback Capability
- **Severity**: N/A
- **Finding**: This is a `application` repository with dev-library-application override (library N/A mapping applied). ENG-Q1 through ENG-Q5 are N/A under the library N/A mapping.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q4: API Test Coverage
- **Severity**: N/A
- **Finding**: This is a `application` repository with dev-library-application override (library N/A mapping applied). ENG-Q1 through ENG-Q5 are N/A under the library N/A mapping.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: N/A
- **Finding**: This is a `application` repository with dev-library-application override (library N/A mapping applied). ENG-Q1 through ENG-Q5 are N/A under the library N/A mapping.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A

---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `src/app/core/interceptors/api.interceptor.ts` | API-Q1 |
| `src/app/core/interceptors/error.interceptor.ts` | API-Q3 |
| `src/app/core/interceptors/token.interceptor.ts` | AUTH-Q1 |
| `src/app/core/auth/services/jwt.service.ts` | AUTH-Q1, AUTH-Q5, DATA-Q1 |
| `src/app/core/auth/services/user.service.ts` | AUTH-Q1 |
| `src/app/core/auth/user.model.ts` | DATA-Q1 |
| `src/app/core/auth/if-authenticated.directive.ts` | AUTH-Q2 |
| `src/app/app.routes.ts` | AUTH-Q2, AUTH-Q3 |
| `src/app/features/article/services/articles.service.ts` | API-Q4, STATE-Q1 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `realworld/specs/api/openapi.yml` | API-Q1 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/deploy.yml` | AUTH-Q5 |
| `.github/workflows/playwright.yml` | HITL-Q3 |
| `.github/workflows/security-tests.yml` | HITL-Q3 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `playwright.config.ts` | HITL-Q3 |
| `package.json` | OBS-Q1 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `package.json` | OBS-Q1 |
