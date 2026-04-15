# Agentic Readiness Assessment Report

**Target**: ./services/microservices-demo/src/currencyservice
**Date**: 2026-04-15
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Agent Scope**: read-only
**Priority**: P1
**Tags**: cpp, grpc, utility
**Context**: C++ gRPC service converting between currencies. (Note: The actual implementation is Node.js/JavaScript, not C++. The user-provided context references C++ but the codebase uses Node.js with `@grpc/grpc-js`.)

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 2 | **RISKs**: 34 | **INFOs**: 13

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 2 |
| RISK | 34 |
| INFO | 13 |
| N/A | 0 |
| **Total** | **49** |

**Questions Evaluated**: 49
**Questions N/A (repo_type: application)**: 0

---

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: The gRPC server is started with `grpc.ServerCredentials.createInsecure()` in `server.js` (line ~153). There is no authentication mechanism of any kind — no OAuth2 client credentials flow, no API key authentication, no mTLS configuration. Any network-reachable client can invoke both `GetSupportedCurrencies` and `Convert` RPCs without presenting credentials. No audit logging of authenticated principals exists because there are no principals to authenticate.
- **Gap**: No machine identity authentication. No principal attribution in audit logs. No service account or API key authentication. The server accepts all connections without verifying caller identity.
- **Remediation**:
  - **Immediate**: Implement mTLS or gRPC interceptor-based authentication. For mTLS, replace `grpc.ServerCredentials.createInsecure()` with `grpc.ServerCredentials.createSsl()` using CA-signed certificates. Alternatively, add a gRPC metadata interceptor that validates bearer tokens (JWT) or API keys from incoming request metadata.
  - **Target State**: All gRPC calls are authenticated with a verifiable machine identity. Each request's authenticated principal is logged in structured logs with a `principal_id` field. Service accounts are defined per calling service/agent.
  - **Estimated Effort**: Medium (2–4 weeks including certificate infrastructure and interceptor implementation)
  - **Dependencies**: ENG-Q6 (Network Policies) — authentication and network security should be addressed together.
- **Evidence**: `server.js` line `grpc.ServerCredentials.createInsecure()`

### ENG-Q6: Cross-Origin and Network Policies

- **Severity**: BLOCKER
- **Finding**: The gRPC server binds to all interfaces (`[::]:${PORT}`) with insecure credentials in `server.js`. No security group rules, no network policies, no API gateway access policies, no WAF rules, and no firewall configurations are defined anywhere in the repository. No IaC files exist to define network security boundaries. The Dockerfile exposes port 7000 without any network security configuration.
- **Gap**: No network security configuration documented or defined. The service is exposed on all interfaces with no access controls. No security groups, no Kubernetes NetworkPolicies, no API gateway, no WAF rules. The entire network surface is open.
- **Remediation**:
  - **Immediate**: Define network policies as IaC (Terraform security groups or Kubernetes NetworkPolicies) that restrict ingress to the gRPC port to only known consumer services. Add an API gateway or service mesh (e.g., Istio, AWS App Mesh) in front of the gRPC service for traffic management and security enforcement.
  - **Target State**: Network policies defined as IaC, restricting access to the CurrencyService to authorized consumer services only. Security group or NetworkPolicy rules are peer-reviewed before deployment. Drift detection is active.
  - **Estimated Effort**: Medium (2–4 weeks including IaC authoring, testing, and deployment)
  - **Dependencies**: AUTH-Q1 (Machine Identity Authentication) — network policies and authentication are complementary controls.
- **Evidence**: `server.js` (bind to `[::]:${PORT}` with `createInsecure()`), `Dockerfile` (`EXPOSE 7000`), absence of any IaC files
## RISKs — Proceed with Compensating Controls

### API-Q3: Structured Error Responses

- **Severity**: RISK
- **Finding**: The `convert()` function in `server.js` has a try/catch block that passes `err.message` directly to the gRPC callback on failure. There are no structured error codes, no machine-readable error bodies, and no retryable indicators. The `getSupportedCurrencies()` function has no error handling at all. gRPC status codes are not explicitly set — the framework defaults are used.
- **Gap**: No structured error response format. No explicit gRPC status codes (e.g., `grpc.status.INVALID_ARGUMENT`). No retryable boolean or error category. Agents cannot distinguish retriable errors from terminal errors.
- **Compensating Controls**:
  - Implement gRPC error handling at the agent orchestration layer that maps generic gRPC status codes to retry/abort decisions.
  - Wrap agent tool calls with timeout and retry logic with exponential backoff for `UNAVAILABLE` and `DEADLINE_EXCEEDED` status codes.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add explicit gRPC status codes using `grpc.status` enum in error callbacks. Return structured error metadata using gRPC `Metadata` objects with fields for `error_code`, `error_message`, and `retryable`.
- **Evidence**: `server.js` — `convert()` function, `callback(err.message)` pattern

### API-Q5: API Versioning and Deprecation

- **Severity**: RISK
- **Finding**: The proto file uses `package hipstershop` with no version number. There are no `/v1/`, `/v2/` URL patterns (gRPC uses package names). No version annotations, no changelog files, and no deprecation notices. The `package.json` shows version `0.1.0` but this is not reflected in the gRPC service definition.
- **Gap**: No API versioning scheme. No deprecation policy. No downstream notification mechanism for breaking changes. Agent tool schemas could break silently when the proto definition changes.
- **Compensating Controls**:
  - Pin agent tool definitions to a specific proto file hash or commit SHA.
  - Monitor proto file changes in version control and trigger agent tool schema regeneration on changes.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Adopt proto package versioning (e.g., `hipstershop.v1.CurrencyService`). Maintain a `CHANGELOG.md` documenting API changes. Implement proto backward-compatibility checks in CI (e.g., `buf breaking`).
- **Evidence**: `proto/demo.proto` (`package hipstershop`), `package.json` (`version: 0.1.0`)

### API-Q7: Asynchronous Operation Support

- **Severity**: RISK
- **Finding**: Both RPCs (`GetSupportedCurrencies`, `Convert`) are synchronous unary calls. No gRPC streaming, no background job frameworks, no async/polling patterns, and no webhook callbacks are implemented. The operations are stateless computations that should complete in milliseconds.
- **Gap**: No async operation support. While current operations are fast, there is no infrastructure for adding longer-running operations in the future. No timeout configuration on the server side.
- **Compensating Controls**:
  - Set gRPC client-side deadlines for all agent-initiated calls (e.g., 5-second deadline).
  - Current operations are sub-second, so sync patterns are acceptable for the current API surface.
- **Remediation Timeline**: 60–90 days (if new operations are added that require async patterns)
- **Recommendation**: Add server-side deadline enforcement. If the service scope expands to include operations that take longer than 1 second, implement gRPC server streaming or a job submission pattern.
- **Evidence**: `server.js` — both RPC implementations are synchronous, `proto/demo.proto` — unary RPC definitions only

### AUTH-Q2: Scoped Permissions (Least Privilege)

- **Severity**: RISK
- **Finding**: No authorization model exists in the service. No IAM policies, no role definitions, no permission checks, and no middleware validating caller permissions. All callers who can reach the service have unrestricted access to both RPCs. No distinction between callers with different permission levels.
- **Gap**: No scoped permissions. No least-privilege enforcement. No ability to grant an agent read-only access to specific RPCs while denying others.
- **Compensating Controls**:
  - Enforce scoped permissions at the infrastructure layer (Kubernetes RBAC, service mesh authorization policies) rather than within the application.
  - Use network segmentation to restrict which services can reach the CurrencyService.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement gRPC interceptor-based authorization that validates caller identity against a permission matrix. Define per-RPC authorization rules (e.g., agent X can call `GetSupportedCurrencies` but not `Convert`).
- **Evidence**: `server.js` — no authorization middleware, no permission checks

### AUTH-Q3: Action-Level Authorization

- **Severity**: RISK
- **Finding**: No action-level authorization exists. Both RPCs are accessible to anyone who can connect. No middleware checks, no ABAC policies, no fine-grained RBAC. The `server.addService()` call registers handlers without any authorization layer.
- **Gap**: No ability to enforce action-level authorization (e.g., allow read of supported currencies but deny conversion requests for a specific caller).
- **Compensating Controls**:
  - Implement action-level controls at the service mesh or API gateway layer using method-level authorization policies.
  - For a read-only agent scope, both RPCs are read operations, so the immediate risk is lower.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add a gRPC interceptor that maps authenticated principals to allowed RPC methods. Use an authorization policy file or external authorization service (e.g., OPA/Rego).
- **Evidence**: `server.js` — `server.addService(shopProto.CurrencyService.service, {getSupportedCurrencies, convert})`

### AUTH-Q4: Identity Propagation

- **Severity**: RISK
- **Finding**: No JWT parsing, no OAuth2 flows, no token exchange mechanisms, and no user context headers in `server.js`. gRPC metadata is not inspected for user identity. No Cognito or Okta integration. The service has no concept of the originating user behind a request.
- **Gap**: No identity propagation. The service cannot personalize responses per user or enforce user-level access controls. When an agent acts on behalf of a user, the CurrencyService cannot know which user is involved.
- **Compensating Controls**:
  - For a currency conversion service processing public data, identity propagation is less critical than for services handling user-specific data.
  - Propagate user context in gRPC metadata at the orchestration layer for audit logging purposes.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add gRPC metadata extraction for user identity tokens. Log the originating user context alongside the calling service identity.
- **Evidence**: `server.js` — no metadata inspection, no JWT parsing

### AUTH-Q5: Agent-as-Self vs Agent-on-Behalf-of-User

- **Severity**: RISK
- **Finding**: No distinction between agent acting under its own identity and agent acting on behalf of a user. No separate IAM roles, no different auth flows, and no audit log fields distinguishing the two modes. The service has no authentication at all (AUTH-Q1), so this distinction cannot be made.
- **Gap**: Cannot distinguish agent-as-self from agent-on-behalf-of-user. No separate authorization paths for the two modes.
- **Compensating Controls**:
  - The CurrencyService returns public data (exchange rates) that is not user-specific, reducing the risk of this gap.
  - Implement the distinction at the orchestration layer by passing different gRPC metadata headers for each mode.
- **Remediation Timeline**: 90–120 days (depends on AUTH-Q1 resolution first)
- **Recommendation**: After implementing authentication (AUTH-Q1), define separate service accounts for agent-as-self and agent-on-behalf-of-user modes. Log the mode in structured logs.
- **Evidence**: `server.js` — no authentication, no identity distinction

### AUTH-Q6: Credential Management

- **Severity**: RISK
- **Finding**: No credentials are hardcoded in the codebase — no passwords, API keys, or secrets are found in `server.js`, `package.json`, or any configuration files. However, no secrets management integration exists either (no AWS Secrets Manager, no HashiCorp Vault). The service does not connect to external services requiring credentials (reads static JSON), but the Google Cloud Profiler configuration in `server.js` relies on implicit credentials.
- **Gap**: No secrets management system integration. No credential rotation capability. While no credentials are currently hardcoded, there is no framework for managing credentials when authentication is added (AUTH-Q1).
- **Compensating Controls**:
  - Current risk is low because the service has no external credential dependencies.
  - When authentication is added, ensure credentials are managed via a secrets manager from the start.
- **Remediation Timeline**: 30–60 days (aligned with AUTH-Q1 implementation)
- **Recommendation**: Integrate AWS Secrets Manager or HashiCorp Vault for credential management before adding authentication. Ensure rotation does not break agent continuity.
- **Evidence**: `server.js` — no hardcoded credentials, no secrets manager integration; `package.json` — `@google-cloud/profiler` dependency uses implicit credentials

### AUTH-Q7: Immutable Audit Logging ⚡

- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: Pino logger is configured in `server.js` with structured JSON output and severity levels. Logs are written to stdout. No CloudTrail configuration, no immutable log storage (S3 object lock), no log file validation, and no CloudWatch log retention policies. Logs are not tamper-evident. The logger does not record the authenticated principal (because AUTH-Q1 — no authentication exists).
- **Gap**: No immutable audit logging. Logs are ephemeral stdout streams with no persistence guarantees. No principal attribution in logs. No tamper-evidence.
- **Compensating Controls**:
  - Route stdout logs to a centralized logging system (CloudWatch Logs, ELK) with retention policies.
  - Enable CloudWatch Logs Insights for forensic queries.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Configure log shipping to CloudWatch Logs with a retention policy. Enable S3 export with object lock for immutability. Add principal identity fields to log entries after AUTH-Q1 is resolved.
- **Evidence**: `server.js` — Pino logger configuration, absence of CloudTrail or immutable log storage

### AUTH-Q8: Agent Identity Suspension

- **Severity**: RISK
- **Finding**: No mechanism to suspend or revoke individual agent identities. No API key revocation endpoints, no IAM role deactivation procedures, no service account disable mechanisms. The service has no authentication (AUTH-Q1), so there are no identities to suspend.
- **Gap**: Cannot isolate a misbehaving agent without taking down the service entirely. No per-identity suspension capability.
- **Compensating Controls**:
  - Use network-level controls (security group modifications, NetworkPolicy updates) to block specific agent source IPs.
  - Implement a deny-list at the service mesh or API gateway layer.
- **Remediation Timeline**: 90–120 days (depends on AUTH-Q1 resolution)
- **Recommendation**: After implementing authentication (AUTH-Q1), add API key or certificate revocation capability. Implement a per-identity deny-list that can be updated without service restart.
- **Evidence**: `server.js` — no authentication, no identity management

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: No multi-step operations exist in the service. Both RPCs are stateless: `GetSupportedCurrencies` reads from a static JSON file, and `Convert` performs an arithmetic calculation. No saga pattern, no two-phase commit, no undo endpoints, no Step Functions. The service has no persistent state to roll back.
- **Gap**: No compensation or rollback capability. While the service is currently stateless, there is no infrastructure for handling multi-step operations if the service scope expands.
- **Compensating Controls**:
  - The service is inherently safe for read-only agent operations because it has no mutable state.
  - No compensating controls needed for the current API surface.
- **Remediation Timeline**: Low priority — revisit if write operations are added
- **Recommendation**: If write operations are added in the future, implement compensation patterns. For the current read-only surface, this risk is mitigated by the service's stateless nature.
- **Evidence**: `server.js` — stateless RPC implementations, `data/currency_conversion.json` — static data

### STATE-Q2: Queryable Current State

- **Severity**: RISK
- **Finding**: The service exposes current state through `GetSupportedCurrencies` (returns all supported currency codes) and `Convert` (performs conversion with current rates). The currency data is loaded from `data/currency_conversion.json` and is queryable. However, the data is static (embedded JSON file) and there is no mechanism to query rate update timestamps or data version.
- **Gap**: No state versioning. No ability to query when rates were last updated. An agent cannot determine if the conversion rates are current.
- **Compensating Controls**:
  - Document the data staleness externally (e.g., in an agent tool definition noting rates are static/embedded).
  - Cross-reference conversion results with a live exchange rate API for validation.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a `GetRateMetadata` RPC that returns the data source, last update timestamp, and version. Alternatively, include metadata fields in the existing RPC responses.
- **Evidence**: `server.js` — `_getCurrencyData()` function, `data/currency_conversion.json` — 33 currencies with EUR-based rates

### STATE-Q3: Concurrency Controls

- **Severity**: RISK
- **Finding**: No concurrency controls are implemented. No optimistic locking, no ETags, no version fields, no conflict resolution logic. The service is stateless and read-only — it reads a static JSON file loaded into memory at startup. Multiple concurrent requests read the same in-memory data without mutation.
- **Gap**: No concurrency controls. While not needed for the current read-only, stateless design, there is no infrastructure for safe concurrent writes if the service scope expands.
- **Compensating Controls**:
  - The service is inherently safe for concurrent read operations because no data is mutated.
  - No compensating controls needed for the current API surface.
- **Remediation Timeline**: Low priority — revisit if mutable state is added
- **Recommendation**: If mutable state is added (e.g., custom rate overrides), implement optimistic locking with version fields.
- **Evidence**: `server.js` — `_getCurrencyData()` reads static JSON, no database writes

### STATE-Q4: Circuit Breakers and Resilience

- **Severity**: RISK
- **Finding**: No circuit breakers, no retry logic, no timeout configurations, and no resilience patterns are implemented. The service has no external dependency calls — it reads a local JSON file. However, there are no graceful degradation patterns, no health-check-based circuit breaking, and no backpressure mechanisms.
- **Gap**: No resilience patterns implemented. While the service has no external dependencies that would cascade failures, there is no protection against the service itself becoming overwhelmed.
- **Compensating Controls**:
  - The service's simplicity (static JSON, arithmetic only) reduces the likelihood of cascading failures.
  - Implement circuit breakers at the calling service or agent orchestration layer.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add gRPC server-side request limits (max concurrent streams). Implement a health check endpoint that can signal backpressure. Add graceful shutdown handling.
- **Evidence**: `server.js` — no resilience libraries, no timeout configuration; `package.json` — `async` dependency present but not used for resilience

### STATE-Q5: Rate Limiting and Throttling

- **Severity**: RISK
- **Finding**: No rate limiting at any layer. No API Gateway, no WAF, no application-level rate limiting middleware. The gRPC server accepts unlimited concurrent connections and requests. No `express-rate-limit` or equivalent gRPC rate limiting.
- **Gap**: No rate limiting. A runaway agent loop could overwhelm the service with requests at machine speed. No protection against agent-induced DDoS.
- **Compensating Controls**:
  - Implement rate limiting at the infrastructure layer (API gateway, service mesh, or load balancer).
  - Set gRPC client-side concurrency limits in agent tool definitions.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add gRPC server-side rate limiting via an interceptor or deploy behind an API gateway (e.g., AWS API Gateway with gRPC support, or Envoy proxy with rate limiting filter). Define per-client rate limits.
- **Evidence**: `server.js` — no rate limiting, absence of API Gateway or WAF configuration

### STATE-Q6: Blast Radius and Transaction Limits

- **Severity**: RISK
- **Finding**: No configurable transaction limits. No per-agent limits on request frequency or volume. The service is read-only, so blast radius from writes is not applicable. However, there are no limits preventing an agent from issuing thousands of conversion requests per second, potentially starving other consumers.
- **Gap**: No configurable limits on agent-initiated actions. No per-identity request caps.
- **Compensating Controls**:
  - Implement per-agent rate limits at the orchestration layer.
  - The read-only nature limits blast radius to availability impact only (no data corruption risk).
- **Remediation Timeline**: 60–90 days
- **Recommendation**: After implementing authentication (AUTH-Q1), add per-identity request quotas. Define `max_requests_per_minute` per agent identity.
- **Evidence**: `server.js` — no transaction limits, no per-client quotas

### STATE-Q7: Infrastructure Capacity for Agent Traffic

- **Severity**: RISK
- **Finding**: No load test results, no auto-scaling policies, and no capacity planning documentation. The Dockerfile runs a single Node.js process (`node server.js`) on Alpine Linux. No horizontal scaling configuration. No Kubernetes HPA (Horizontal Pod Autoscaler) definitions. No connection pool sizing.
- **Gap**: Unknown capacity limits. The service has not been load-tested for agent traffic patterns. A single Node.js process has known concurrency limits.
- **Compensating Controls**:
  - Node.js event loop handles concurrent I/O well for CPU-light operations like currency conversion.
  - Deploy multiple replicas behind a load balancer for redundancy.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Conduct load testing to establish baseline capacity. Define Kubernetes resource limits and HPA policies. Consider Node.js clustering or multiple replicas.
- **Evidence**: `Dockerfile` — single `node server.js` process, `EXPOSE 7000`, absence of scaling configuration

### HITL-Q1: Draft/Pending State

- **Severity**: RISK
- **Finding**: No draft or pending state concept exists. The service is stateless and read-only. Both RPCs return immediate results — there is no concept of creating a draft conversion or pending approval. No approval workflow endpoints, no status-based state machines.
- **Gap**: No draft/pending state for agent-proposed actions. For a read-only currency conversion service, this is a design limitation rather than a safety gap.
- **Compensating Controls**:
  - For read-only operations returning public data, draft states are less critical.
  - Implement draft/approval patterns at the orchestration layer if conversion results feed into downstream write operations.
- **Remediation Timeline**: Low priority for read-only service
- **Recommendation**: If conversion results are used as inputs to financial transactions, implement a confirmation pattern at the orchestration layer where a human approves the conversion before the downstream write is executed.
- **Evidence**: `server.js` — both RPCs return immediate results, no state management

### HITL-Q2: Configurable Approval Gates

- **Severity**: RISK
- **Finding**: No approval gates exist. No configurable operation-level flags. No Step Functions with human approval tasks. The service has no mechanism for requiring human approval before executing an operation.
- **Gap**: No ability to configure human approval gates for specific operations. While both RPCs are read-only, there is no framework for adding approval gates if the service scope expands.
- **Compensating Controls**:
  - Implement approval gates at the agent orchestration layer rather than within the service.
  - For read-only currency conversion, approval gates are less critical.
- **Remediation Timeline**: Low priority for read-only service
- **Recommendation**: Implement approval gates at the orchestration layer for any downstream actions that depend on conversion results (e.g., executing a payment after currency conversion).
- **Evidence**: `server.js` — no approval logic, no configurable flags

### HITL-Q3: Sandbox/Staging Environment

- **Severity**: RISK
- **Finding**: No separate environment configurations found. No Docker Compose for local testing. No seed data scripts. No synthetic data generators. No environment-specific IaC. The service reads a static JSON file, making local testing straightforward (`node server.js`), but no formal sandbox or staging environment is configured.
- **Gap**: No formal sandbox/staging environment definition. No production-equivalent test environment for agent validation.
- **Compensating Controls**:
  - The service's simplicity (static JSON, no database, no external dependencies) makes local testing trivial.
  - Agents can be tested against a locally-running instance of the service.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a Docker Compose file for local testing. Define environment-specific configurations (at minimum: local, staging, production) with different port bindings and logging levels.
- **Evidence**: `Dockerfile` — single environment definition, `data/currency_conversion.json` — static data file, absence of Docker Compose or environment configs

### DATA-Q2: Data Residency and Sovereignty ⚡

- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: No data residency requirements are documented. The currency conversion rates in `data/currency_conversion.json` are publicly available data from the European Central Bank. This data is not subject to GDPR, LGPD, HIPAA, or sector-specific data sovereignty requirements. No region-specific configurations found.
- **Gap**: No documented data residency policy. While the data is public and non-regulated, there is no explicit classification confirming this, which could cause confusion for compliance teams.
- **Compensating Controls**:
  - Document that the data is publicly available ECB exchange rates, not subject to residency constraints.
  - The data contains no PII, PHI, or confidential business data.
- **Remediation Timeline**: 30 days (documentation only)
- **Recommendation**: Add a `DATA_CLASSIFICATION.md` file documenting that the currency data is public, non-regulated European Central Bank reference data.
- **Evidence**: `data/currency_conversion.json` — public exchange rates, `server.js` — comment "Uses public data from European Central Bank"

### DATA-Q3: Selective Query Support

- **Severity**: RISK
- **Finding**: `GetSupportedCurrencies` returns all 33 currency codes in a single response — no pagination, no filtering, no sorting. `Convert` takes specific input parameters (`from` currency, `to_code`) and returns a single result. No `limit`, `offset`, or `cursor` parameters.
- **Gap**: No pagination or filtering on `GetSupportedCurrencies`. The result set is small (33 currencies), so this is a low-severity gap.
- **Compensating Controls**:
  - The result set is small enough (33 currency codes) to fit within any LLM context window.
  - `Convert` already accepts specific parameters, limiting results to a single conversion.
- **Remediation Timeline**: Low priority (result sets are small)
- **Recommendation**: If the currency list grows significantly, add filtering support. For the current 33-currency list, this is acceptable.
- **Evidence**: `proto/demo.proto` — `GetSupportedCurrenciesResponse` returns `repeated string currency_codes`, `data/currency_conversion.json` — 33 currencies

### DATA-Q4: System of Record Designations

- **Severity**: RISK
- **Finding**: No system-of-record designation documented. A code comment in `server.js` mentions "Uses public data from European Central Bank," but there is no formal data ownership documentation, no master data management references, and no conflict resolution logic.
- **Gap**: No formal system-of-record designation. No documentation of data provenance or ownership. No process for resolving conflicts if rates differ from other sources.
- **Compensating Controls**:
  - The ECB is a well-known authoritative source for EUR-based exchange rates.
  - Document the data source and update frequency in the service README.
- **Remediation Timeline**: 30 days (documentation only)
- **Recommendation**: Add data provenance documentation specifying that the European Central Bank is the authoritative source, the update frequency, and the process for refreshing rates.
- **Evidence**: `server.js` — comment "Uses public data from European Central Bank", `data/currency_conversion.json`

### DATA-Q5: Reliable Timestamps

- **Severity**: RISK
- **Finding**: No timestamps in the data or API responses. The `data/currency_conversion.json` file contains only currency-to-EUR conversion rates with no `updated_at`, `effective_date`, or `captured_at` field. The `Money` response message in `proto/demo.proto` contains only `currency_code`, `units`, and `nanos` — no temporal fields.
- **Gap**: No timestamps on currency rates. An agent cannot determine when the rates were captured or whether they are current. This is critical for a currency conversion service where rates change daily.
- **Compensating Controls**:
  - Document the rate capture date externally (e.g., in the agent tool definition).
  - Cross-reference conversion results with a live exchange rate API for time-critical operations.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add an `effective_date` or `last_updated` field to the currency data JSON. Include timestamp metadata in API responses (add a `rate_timestamp` field to the `Money` message or create a new response wrapper).
- **Evidence**: `data/currency_conversion.json` — no timestamp fields, `proto/demo.proto` — `Money` message has no temporal fields

### DATA-Q6: Data Freshness Signaling

- **Severity**: RISK
- **Finding**: No cache headers, no data age indicators, no `last-refreshed` timestamps, and no consistency guarantees. The static JSON file is loaded into memory via `require('./data/currency_conversion.json')` (Node.js module cache). The service cannot signal whether data is current, stale, or cached. An agent has no way to determine data freshness.
- **Gap**: No data freshness signaling. The service returns conversion results with no indication of when the underlying rates were captured. For a currency conversion service, rate staleness is a material risk.
- **Compensating Controls**:
  - Document the known data freshness characteristics in agent tool definitions.
  - Implement freshness checks at the orchestration layer by comparing results with a reference rate API.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a gRPC response metadata header (or response field) indicating `rate_effective_date` and `data_source_version`. Implement a periodic rate refresh mechanism.
- **Evidence**: `server.js` — `require('./data/currency_conversion.json')` cached by Node.js module loader, `data/currency_conversion.json` — no freshness metadata

### DATA-Q7: PII Redaction in Logs

- **Severity**: RISK
- **Finding**: The Pino logger logs conversion request success/failure messages. The data processed (currency codes and monetary amounts) is not PII. No PII redaction middleware is implemented, but the service does not handle PII — it processes only currency codes (e.g., "CHF", "EUR") and numerical amounts.
- **Gap**: No PII redaction framework. While the current data is non-PII, there is no protection if PII is inadvertently passed in request metadata or if the service scope expands to handle user-specific data.
- **Compensating Controls**:
  - Current data is non-PII (currency codes and amounts), reducing immediate risk.
  - Monitor log output to ensure no PII leakage if the service evolves.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add a log scrubbing middleware or Pino serializer that redacts sensitive patterns. This provides defense-in-depth even if the current data is non-PII.
- **Evidence**: `server.js` — Pino logger with `logger.info('conversion request successful')`, `logger.error()` patterns

### DISC-Q1: Schema Documentation and Versioning

- **Severity**: RISK
- **Finding**: `proto/demo.proto` provides schema documentation with proto3 syntax, typed message definitions, and inline comments (especially on the `Money` message). The schema is well-documented with field descriptions. However, there is no formal schema versioning — no `v1/v2` package directories, no schema registry, and no changelog. The proto file includes service definitions for 8 other services (CartService, RecommendationService, etc.) in addition to CurrencyService.
- **Gap**: No schema versioning. No changelog tracking schema changes. Schema changes could break agent tool definitions without warning.
- **Compensating Controls**:
  - Pin agent tool schemas to a specific proto file version (commit SHA).
  - Use `buf breaking` in CI to detect backward-incompatible schema changes.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement proto package versioning (e.g., `hipstershop.currency.v1`). Add `buf` for schema linting and breaking change detection. Maintain a schema changelog.
- **Evidence**: `proto/demo.proto` — `package hipstershop`, `syntax = "proto3"`, detailed comments on `Money` message

### OBS-Q1: Distributed Tracing and Structured Logging

- **Severity**: RISK
- **Finding**: OpenTelemetry SDK is configured in `server.js` with gRPC instrumentation (`@opentelemetry/instrumentation-grpc`, `@opentelemetry/sdk-node`). Tracing is conditional on `ENABLE_TRACING=1` environment variable and exports to an OTLP gRPC collector. Pino logger produces structured JSON logs with `severity` field and `message` key. However, no `correlation_id` or `request_id` field is present in log entries, and traces are not correlated with log entries.
- **Gap**: Tracing exists but is opt-in (disabled by default). Logs are structured JSON but lack `correlation_id`/`request_id` for linking related log entries. No trace-log correlation (trace IDs are not embedded in log entries).
- **Compensating Controls**:
  - Enable `ENABLE_TRACING=1` in deployment configuration.
  - OpenTelemetry gRPC instrumentation automatically propagates trace context headers.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Enable tracing by default (or at least in staging/production). Add `trace_id` and `request_id` fields to Pino log entries using OpenTelemetry context propagation. Set up trace-log correlation.
- **Evidence**: `server.js` — OpenTelemetry SDK configuration, `ENABLE_TRACING` env var, Pino logger setup; `package.json` — `@opentelemetry/*` dependencies

### OBS-Q2: Alerting on Error Rates and Latency

- **Severity**: RISK
- **Finding**: No alerting configuration found. No CloudWatch alarms, no anomaly detection, no PagerDuty or OpsGenie integration, no SLO-based alerting, and no composite alarms. Metrics are available via OpenTelemetry (if tracing is enabled) but no alerting thresholds are defined.
- **Gap**: No alerting on error rates or latency. Degradation of the CurrencyService would not be detected proactively.
- **Compensating Controls**:
  - Monitor the health check endpoint (`grpc.health.v1.Health/Check`) from an external monitoring system.
  - Set up infrastructure-level alerts (container restart count, CPU/memory) at the deployment layer.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure CloudWatch alarms (or equivalent) on gRPC error rates and P95 latency. Set up alerting thresholds: >1% error rate → warning, >5% error rate → critical. Integrate with PagerDuty or OpsGenie for on-call notification.
- **Evidence**: `server.js` — health check endpoint defined, absence of any alerting configuration

### ENG-Q1: Infrastructure Governance for Agent-Facing Surface

- **Severity**: RISK
- **Finding**: No IaC files found in the repository. No Terraform, CloudFormation, CDK, Helm, or Kustomize definitions. The only infrastructure artifact is the `Dockerfile`. The infrastructure exposing this service to agents — API gateways, IAM roles, secrets, network configurations — is not defined in this repository.
- **Gap**: No infrastructure-as-code governance. No peer review on infrastructure changes (because there is no IaC). No drift detection. The entire agent-facing surface is undefined from an IaC perspective.
- **Compensating Controls**:
  - Infrastructure may be defined in a separate IaC repository (common in microservices architectures).
  - The Dockerfile provides reproducible container builds.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Define the service's infrastructure as IaC — at minimum: Kubernetes Deployment, Service, NetworkPolicy, and HPA. Add PR review requirements for all IaC changes. Enable drift detection (AWS Config rules or equivalent).
- **Evidence**: Absence of IaC files (no `.tf`, `.cfn.yaml`, `cdk.json`, `Chart.yaml`, `kustomization.yaml`), `Dockerfile` present

### ENG-Q2: CI/CD with API Contract Testing

- **Severity**: RISK
- **Finding**: No CI/CD pipeline configuration found. No GitHub Actions workflows (`.github/workflows/`), no GitLab CI (`.gitlab-ci.yml`), no Jenkinsfile, no buildspec.yml. No contract tests, no schema validation in build, and no breaking change detection. The `package.json` test script outputs "Error: no test specified."
- **Gap**: No CI/CD pipeline. No automated testing of any kind. No API contract testing. Proto breaking changes are not detected before deployment.
- **Compensating Controls**:
  - CI/CD may be defined in a parent repository or shared pipeline configuration.
  - Manual testing via `client.js` provides basic smoke testing.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Create a CI/CD pipeline (GitHub Actions or equivalent). Add `buf breaking` for proto compatibility checking. Implement integration tests against the gRPC service. Add the pipeline to the repository.
- **Evidence**: Absence of CI/CD files, `package.json` — `"test": "echo \"Error: no test specified\" && exit 1"`, `client.js` — manual test client

### ENG-Q3: Rollback Capability

- **Severity**: RISK
- **Finding**: No deployment configuration found. No blue/green deployment, no canary deployment, no CodeDeploy rollback triggers, no Helm rollback, no feature flags, and no traffic shifting configuration. The Dockerfile enables building container images, but no deployment strategy is defined.
- **Gap**: No rollback capability defined in this repository. A broken deployment cannot be rolled back using artifacts in this repo.
- **Compensating Controls**:
  - Container image tags enable rolling back to a previous image version.
  - Deployment and rollback may be managed by a separate deployment pipeline or GitOps repository.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Define a deployment strategy (blue/green or canary) in IaC. Implement automatic rollback triggers based on health check failures. Target: rollback within 15 minutes.
- **Evidence**: `Dockerfile` — container image build only, absence of deployment configuration

### ENG-Q4: API Test Coverage

- **Severity**: RISK
- **Finding**: No test files found in the repository. The `package.json` test script is `"echo \"Error: no test specified\" && exit 1"` — explicitly indicating no tests exist. The `client.js` file is a manual test client but is excluded from the Docker image (`.dockerignore` lists `client.js`) and is not part of any automated test suite.
- **Gap**: Zero test coverage. No automated tests for either RPC. No input validation tests, no error response tests, no edge case tests (e.g., division by zero for unsupported currency codes, negative amounts, overflow).
- **Compensating Controls**:
  - `client.js` provides a manual smoke test for basic functionality.
  - The service's simplicity (two RPCs, arithmetic logic) reduces the likelihood of subtle bugs.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Write automated gRPC tests for both RPCs. Test: (1) valid conversion, (2) unsupported currency code, (3) zero amount, (4) negative amount, (5) very large amount (overflow), (6) GetSupportedCurrencies returns all expected currencies. Add tests to CI pipeline.
- **Evidence**: `package.json` — `"test": "echo \"Error: no test specified\" && exit 1"`, `client.js` — manual test client

### ENG-Q5: Encryption at Rest for Agent-Accessible Data

- **Severity**: RISK
- **Finding**: No encryption configuration found. No KMS keys, no encryption settings in Dockerfile or configuration. The data (`data/currency_conversion.json`) is embedded in the container image as a plain-text JSON file. No S3, RDS, DynamoDB, or EBS encryption configuration exists because there is no IaC.
- **Gap**: No encryption at rest configuration. While the data is public (ECB exchange rates), there is no framework for encryption if sensitive data is added. The container image contains unencrypted data.
- **Compensating Controls**:
  - The data is publicly available ECB exchange rates — not sensitive or confidential.
  - Encryption at rest is typically enforced at the infrastructure layer (encrypted EBS volumes, encrypted container registries).
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Define encryption-at-rest requirements in IaC. Ensure the container registry encrypts images at rest. If the service ever accesses a database, enforce KMS encryption.
- **Evidence**: `data/currency_conversion.json` — plain-text data file, `Dockerfile` — no encryption configuration, absence of IaC with encryption settings
## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO
- **Finding**: The service exposes a well-documented gRPC interface defined in `proto/demo.proto`. The `CurrencyService` declares two RPCs: `GetSupportedCurrencies(Empty) returns (GetSupportedCurrenciesResponse)` and `Convert(CurrencyConversionRequest) returns (Money)`. Both RPCs are implemented in `server.js`. The proto file is the authoritative interface definition — gRPC's proto-based contracts are equivalent to REST OpenAPI specifications. A health check endpoint is also defined via `proto/grpc/health/v1/health.proto`.
- **Implication**: The gRPC proto definition serves as the machine-readable contract for agent tool definition generation. Agent frameworks that support gRPC (or gRPC-to-REST transcoding) can consume this interface directly. For frameworks requiring REST, a gRPC-gateway or Envoy transcoding proxy may be needed.
- **Recommendation**: If REST-based agent frameworks are required, consider adding a gRPC-gateway or Envoy sidecar for HTTP/JSON transcoding of the gRPC service.
- **Evidence**: `proto/demo.proto` — `CurrencyService` definition, `server.js` — `server.addService(shopProto.CurrencyService.service, {getSupportedCurrencies, convert})`

### API-Q2: Machine-Readable API Specification

- **Severity**: INFO
- **Finding**: The `proto/demo.proto` file IS the machine-readable API specification. Protobuf definitions are strongly typed, self-documenting, and can be used to auto-generate client libraries and tool schemas. The specification is current with the implementation — `server.js` implements exactly the two RPCs defined in the proto. The `Money` message includes detailed inline comments explaining each field (e.g., currency_code is "The 3-letter currency code defined in ISO 4217").
- **Implication**: The proto file can be used to auto-generate gRPC client stubs for agent tools. The specification is well-maintained and matches the implementation.
- **Recommendation**: Consider generating OpenAPI documentation from the proto file (using tools like `protoc-gen-openapiv2`) for teams that need REST-compatible documentation.
- **Evidence**: `proto/demo.proto` — complete service, message, and field definitions; `server.js` — implements `getSupportedCurrencies` and `convert` matching proto exactly

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Both RPCs are inherently read-only operations. `GetSupportedCurrencies` returns a list of currency codes from static data. `Convert` performs a pure arithmetic calculation with no side effects. No write endpoints exist in the CurrencyService. There is no state mutation, no database writes, and no external system modifications.
- **Implication**: Idempotency is not a concern for the current API surface because all operations are stateless reads. If write operations are added in the future, idempotency patterns should be implemented.
- **Recommendation**: No action needed for the current read-only API surface. If write operations are added, implement idempotency keys.
- **Evidence**: `proto/demo.proto` — both RPCs return data without mutation, `server.js` — `convert()` and `getSupportedCurrencies()` are pure functions

### API-Q6: Structured Response Format

- **Severity**: INFO
- **Finding**: gRPC uses Protocol Buffers (protobuf) binary format with well-defined, strongly-typed message schemas. The `Money` message has typed fields: `string currency_code`, `int64 units`, `int32 nanos`. The `GetSupportedCurrenciesResponse` has `repeated string currency_codes`. All response types are defined in `proto/demo.proto` with explicit field types and documentation.
- **Implication**: Protobuf is structured and strongly typed — ideal for agent consumption. However, it is a binary format that requires a proto definition to deserialize. LLMs cannot directly parse protobuf binary data. Agent tool wrappers must deserialize protobuf responses to JSON/text before passing to an LLM.
- **Recommendation**: For LLM-based agents, implement a tool wrapper that deserializes protobuf responses to JSON. Consider gRPC-JSON transcoding for direct JSON responses.
- **Evidence**: `proto/demo.proto` — `Money` message, `GetSupportedCurrenciesResponse` message, `CurrencyConversionRequest` message

### API-Q8: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: No event emission mechanisms found. No webhook endpoints, no SNS/EventBridge/SQS integration, no Kafka topics, and no CDC pipelines. The service is a stateless computation service — it does not manage mutable state, so there are no state changes to emit events for.
- **Implication**: Event emission is not relevant for the current stateless design. Currency rates are static (embedded JSON). If the service evolves to support dynamic rate updates, event emission would become important (e.g., emitting a "rates updated" event).
- **Recommendation**: No action needed for the current stateless design. If dynamic rate updates are implemented, add EventBridge events for rate change notifications.
- **Evidence**: `server.js` — no event publishing, `data/currency_conversion.json` — static data

### API-Q9: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limiting configuration found. No API Gateway throttle settings, no WAF rate rules, no rate limiting middleware, and no `X-RateLimit-Remaining` or `Retry-After` headers. gRPC does not natively support HTTP-style rate limit headers — rate limit information would need to be conveyed via gRPC trailing metadata.
- **Implication**: Agents calling this service have no rate limit awareness. They will call at machine speed until they are rejected or the service becomes unavailable. This overlaps with STATE-Q5 (rate limiting enforcement).
- **Recommendation**: If rate limiting is implemented (STATE-Q5), expose rate limit information via gRPC trailing metadata (e.g., `x-ratelimit-remaining`, `x-ratelimit-reset`).
- **Evidence**: `server.js` — no rate limit headers or metadata, absence of API Gateway configuration

### API-Q10: API Latency Profile

- **Severity**: INFO
- **Finding**: No performance benchmarks, load test results, CloudWatch latency metrics, or APM dashboards found. The service performs in-memory JSON lookup and arithmetic calculations — both operations are computationally trivial. The currency data is loaded via `require('./data/currency_conversion.json')` which is cached by the Node.js module loader after the first call, making subsequent reads instant (in-memory).
- **Implication**: Expected latency is sub-millisecond for the computation itself, with gRPC serialization/network overhead adding microseconds to low-single-digit milliseconds. This is well within the sub-second ideal threshold for agent tool calls. Sequential agent workflows involving this service will not be bottlenecked by latency.
- **Recommendation**: Conduct baseline latency benchmarking to confirm expectations and establish P95/P99 baselines. Use OpenTelemetry metrics (once enabled) to track latency in production.
- **Evidence**: `server.js` — `_getCurrencyData()` uses `require()` (cached), `convert()` performs arithmetic, `data/currency_conversion.json` — 33-entry JSON object

### DATA-Q1: Sensitive Data Classification

- **Severity**: INFO
- **Finding**: The service handles currency conversion rates from `data/currency_conversion.json` containing 33 EUR-based exchange rates. This is publicly available data from the European Central Bank (referenced in a code comment in `server.js`). No PII, PHI, financial records, or credentials are stored or processed. The service does not access any database or external data store — only the embedded static JSON file.
- **Implication**: The data is inherently non-sensitive (public reference data). No field-level encryption, data classification tagging, or PII detection is needed for the current data. However, no formal data classification policy exists, which could cause confusion if the service scope expands.
- **Recommendation**: Add a data classification label (e.g., "PUBLIC" or "NON-SENSITIVE") to the service documentation. This prevents future misclassification when other teams assess the service.
- **Evidence**: `data/currency_conversion.json` — 33 public exchange rates, `server.js` — comment "Uses public data from European Central Bank"

### DATA-Q8: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality metrics, data profiling reports, null rate monitoring, duplicate detection, or data freshness SLAs found. The static JSON file contains 33 currency entries, all with non-null string values for exchange rates. The data quality is implicitly high (complete, no nulls, consistent format) but not monitored.
- **Implication**: For a static dataset of 33 entries, data quality issues are unlikely but unmonitored. If the data source is updated (from ECB feeds), quality monitoring would become important.
- **Recommendation**: Add basic data validation (e.g., all rates are positive numbers, all currencies are valid ISO 4217 codes) to the service startup or a CI check.
- **Evidence**: `data/currency_conversion.json` — 33 entries, all non-null

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Field names in `proto/demo.proto` are clear and semantically meaningful: `currency_code`, `units`, `nanos`, `from`, `to_code`. The `Money` message includes detailed comments explaining each field's semantics (e.g., "The 3-letter currency code defined in ISO 4217", "Number of nano (10^-9) units of the amount"). No legacy abbreviations or cryptic codes.
- **Implication**: Field names are LLM-friendly. An agent can reason about `currency_code` and `units` without a data dictionary. The proto documentation comments provide additional semantic context for tool definition authoring.
- **Recommendation**: No action needed. Field naming is already well-suited for agent consumption.
- **Evidence**: `proto/demo.proto` — `Money` message fields with documentation comments, `CurrencyConversionRequest` message

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No data catalog (AWS Glue, Collibra, Alation, DataHub) found. No metadata files beyond the proto definitions. The proto file serves as a de facto schema catalog for the gRPC service, but no broader data catalog describes what data the service holds or its semantic meaning outside the proto.
- **Implication**: For a single-purpose service (currency conversion), a full data catalog may be unnecessary. The proto file provides sufficient schema documentation. However, for portfolio-wide agent tool discovery, a catalog entry would help.
- **Recommendation**: Register the CurrencyService in a centralized API/service catalog if one exists in the organization. Include the proto file as the schema reference.
- **Evidence**: `proto/demo.proto` — service and message definitions, absence of data catalog configuration

### DISC-Q4: Data Lineage

- **Severity**: INFO
- **Finding**: No data lineage tools (AWS Glue DataBrew, Apache Atlas) found. No ETL pipeline documentation, no data flow diagrams, no transformation logs. A code comment in `server.js` mentions "Uses public data from European Central Bank" — this is the only provenance information. The `genproto.sh` script copies proto files from a shared `../../protos/` directory, providing some lineage for the proto definition.
- **Implication**: Data lineage is minimal but adequate for the current service. The data source (ECB) is documented informally. If an agent produces incorrect conversion results, the source can be traced to the static JSON file.
- **Recommendation**: Add a formal data lineage record in the README documenting: (1) data source (European Central Bank), (2) data capture date, (3) transformation applied (EUR-based rates), (4) update process.
- **Evidence**: `server.js` — comment "Uses public data from European Central Bank", `genproto.sh` — proto source lineage, `data/currency_conversion.json`

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No custom business metrics found. No `cloudwatch.put_metric_data`, no custom dashboards, no business KPI alarms. The service logs conversion request success/failure at the info/error level but does not publish metrics on conversion volume, error rates by currency pair, or request patterns.
- **Implication**: Without business metrics, there is no visibility into whether agent-initiated conversions produce correct results or whether specific currency pairs have higher error rates. Infrastructure metrics alone cannot answer business outcome questions.
- **Recommendation**: Add custom metrics for: (1) conversion request count by currency pair, (2) error rate by error type, (3) request volume over time. Publish to CloudWatch or OpenTelemetry metrics backend.
- **Evidence**: `server.js` — `logger.info('conversion request successful')` (log only, no metric), absence of metrics publishing
## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: The service exposes a well-documented gRPC interface defined in `proto/demo.proto`. The `CurrencyService` declares two RPCs: `GetSupportedCurrencies(Empty) returns (GetSupportedCurrenciesResponse)` and `Convert(CurrencyConversionRequest) returns (Money)`. Both are implemented in `server.js`. A health check endpoint is also available via `proto/grpc/health/v1/health.proto`. The interface is a documented, stable, machine-readable contract.
- **Gap**: gRPC may not be directly consumable by all agent frameworks — some require REST. This is a design consideration, not a gap.
- **Recommendation**: If REST-based agent frameworks are required, consider adding a gRPC-gateway or Envoy sidecar for HTTP/JSON transcoding.
- **Evidence**: `proto/demo.proto`, `server.js`

#### API-Q2: Machine-Readable API Specification
- **Severity**: INFO
- **Finding**: `proto/demo.proto` IS the machine-readable specification. It is strongly typed, self-documenting with inline comments, and current with the implementation. The `Money` message includes detailed field documentation (ISO 4217 currency codes, nano-precision amounts).
- **Gap**: No gap. The proto file is the specification.
- **Recommendation**: Consider generating OpenAPI docs from the proto using `protoc-gen-openapiv2` for broader tooling compatibility.
- **Evidence**: `proto/demo.proto`, `server.js`

#### API-Q3: Structured Error Responses
- **Severity**: RISK
- **Finding**: The `convert()` function has a try/catch that passes `err.message` to the gRPC callback. No explicit gRPC status codes, no structured error metadata, no retryable indicators. `getSupportedCurrencies()` has no error handling.
- **Gap**: No structured error codes. Agents cannot distinguish retriable from terminal errors.
- **Recommendation**: Add explicit gRPC status codes and structured error metadata using gRPC `Metadata` objects.
- **Evidence**: `server.js` — `callback(err.message)` in `convert()`, no error handling in `getSupportedCurrencies()`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Both RPCs are inherently read-only. `GetSupportedCurrencies` returns static data. `Convert` performs pure arithmetic with no side effects. No write endpoints exist.
- **Gap**: N/A — no write operations.
- **Recommendation**: No action needed. If write operations are added, implement idempotency keys.
- **Evidence**: `proto/demo.proto`, `server.js`

#### API-Q5: API Versioning and Deprecation
- **Severity**: RISK
- **Finding**: Proto package is `hipstershop` with no version number. No versioning scheme, no changelog, no deprecation notices. `package.json` version `0.1.0` is not reflected in the gRPC service definition.
- **Gap**: No API versioning. No deprecation policy.
- **Recommendation**: Adopt proto package versioning (e.g., `hipstershop.v1.CurrencyService`). Add `buf breaking` checks in CI.
- **Evidence**: `proto/demo.proto` — `package hipstershop`, `package.json` — `version: 0.1.0`

#### API-Q6: Structured Response Format
- **Severity**: INFO
- **Finding**: gRPC uses protobuf binary format with strongly-typed message schemas. `Money` has `string currency_code`, `int64 units`, `int32 nanos`. All types are well-defined in the proto.
- **Gap**: Protobuf binary requires deserialization before LLM consumption.
- **Recommendation**: Implement tool wrappers that deserialize protobuf to JSON for LLM agents.
- **Evidence**: `proto/demo.proto` — message definitions

#### API-Q7: Asynchronous Operation Support
- **Severity**: RISK
- **Finding**: Both RPCs are synchronous unary calls. No streaming, no async patterns, no webhook callbacks. Operations are sub-second stateless computations.
- **Gap**: No async support. Not needed for current operations but limits future extensibility.
- **Recommendation**: Add server-side deadline enforcement. Implement async patterns if longer-running operations are added.
- **Evidence**: `server.js`, `proto/demo.proto` — unary RPC definitions

#### API-Q8: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: No event emission. The service is stateless with no mutable state to emit events for.
- **Gap**: No event emission — not applicable for current stateless design.
- **Recommendation**: No action needed. Add events if dynamic rate updates are implemented.
- **Evidence**: `server.js`, `data/currency_conversion.json`

#### API-Q9: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit configuration or headers. gRPC does not natively support HTTP-style rate limit headers.
- **Gap**: No rate limit awareness for agent callers.
- **Recommendation**: Expose rate limit info via gRPC trailing metadata if rate limiting is implemented (STATE-Q5).
- **Evidence**: `server.js`

#### API-Q10: API Latency Profile
- **Severity**: INFO
- **Finding**: No benchmarks found. Service performs in-memory JSON lookup and arithmetic. Expected sub-millisecond computation latency. Node.js `require()` caches the JSON data.
- **Gap**: No documented latency profile.
- **Recommendation**: Conduct baseline latency benchmarking. Use OpenTelemetry metrics for production monitoring.
- **Evidence**: `server.js` — `_getCurrencyData()` uses `require()`, `data/currency_conversion.json` — 33 entries
### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: The gRPC server uses `grpc.ServerCredentials.createInsecure()` — no authentication of any kind. No OAuth2, no API key, no mTLS. Any network-reachable client can invoke all RPCs. No audit logging of authenticated principals.
- **Gap**: No machine identity authentication. No principal attribution.
- **Recommendation**: Implement mTLS (`grpc.ServerCredentials.createSsl()`) or gRPC interceptor-based JWT/API key authentication.
- **Evidence**: `server.js` — `grpc.ServerCredentials.createInsecure()`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK
- **Finding**: No authorization model. No IAM policies, no role definitions, no permission checks. All callers have unrestricted access to both RPCs.
- **Gap**: No scoped permissions. No least-privilege enforcement.
- **Recommendation**: Implement gRPC interceptor-based authorization with per-RPC permission rules.
- **Evidence**: `server.js` — no authorization middleware

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK
- **Finding**: No action-level authorization. Both RPCs are accessible to all callers. No ABAC, no fine-grained RBAC, no middleware checks.
- **Gap**: Cannot restrict specific RPCs per caller identity.
- **Recommendation**: Add gRPC interceptor mapping authenticated principals to allowed RPC methods.
- **Evidence**: `server.js` — `server.addService()` with no authorization layer

#### AUTH-Q4: Identity Propagation
- **Severity**: RISK
- **Finding**: No JWT parsing, no OAuth2 flows, no token exchange, no user context headers. gRPC metadata is not inspected for identity. No Cognito/Okta integration.
- **Gap**: No identity propagation. Service cannot know which user is behind an agent request.
- **Recommendation**: Add gRPC metadata extraction for user identity tokens.
- **Evidence**: `server.js` — no metadata inspection

#### AUTH-Q5: Agent-as-Self vs Agent-on-Behalf-of-User
- **Severity**: RISK
- **Finding**: No distinction between modes. No authentication exists (AUTH-Q1), so no identity distinction is possible.
- **Gap**: Cannot distinguish agent-as-self from agent-on-behalf-of-user.
- **Recommendation**: After AUTH-Q1, define separate service accounts for each mode.
- **Evidence**: `server.js` — no authentication, no identity distinction

#### AUTH-Q6: Credential Management
- **Severity**: RISK
- **Finding**: No hardcoded credentials found. No secrets management integration (no AWS Secrets Manager, no Vault). Service has no external credential dependencies currently. Google Cloud Profiler uses implicit credentials.
- **Gap**: No secrets management framework for when auth is added.
- **Recommendation**: Integrate secrets management before implementing AUTH-Q1.
- **Evidence**: `server.js` — no hardcoded credentials, `package.json` — `@google-cloud/profiler`

#### AUTH-Q7: Immutable Audit Logging ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: Pino logger configured with structured JSON output to stdout. No CloudTrail, no immutable log storage, no log validation, no principal attribution in logs.
- **Gap**: No immutable audit logging. Logs are ephemeral stdout with no persistence or tamper-evidence.
- **Recommendation**: Ship logs to CloudWatch Logs with retention policy. Enable S3 export with object lock.
- **Evidence**: `server.js` — Pino logger configuration

#### AUTH-Q8: Agent Identity Suspension
- **Severity**: RISK
- **Finding**: No mechanism to suspend agent identities. No API key revocation, no IAM deactivation. No authentication exists, so no identities to suspend.
- **Gap**: Cannot isolate a misbehaving agent without taking down the service.
- **Recommendation**: After AUTH-Q1, add per-identity revocation capability.
- **Evidence**: `server.js` — no authentication or identity management
### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: No multi-step operations exist. Service is stateless — reads static JSON and performs arithmetic. No saga pattern, no two-phase commit, no undo endpoints. No persistent state to roll back.
- **Gap**: No compensation/rollback capability. Mitigated by stateless, read-only design.
- **Recommendation**: Revisit if write operations are added.
- **Evidence**: `server.js` — stateless RPC implementations, `data/currency_conversion.json`

#### STATE-Q2: Queryable Current State
- **Severity**: RISK
- **Finding**: `GetSupportedCurrencies` returns all currency codes. `Convert` uses current rates. Data is queryable but static (embedded JSON). No state versioning or rate update timestamps.
- **Gap**: No ability to query when rates were last updated.
- **Recommendation**: Add a `GetRateMetadata` RPC returning data source, last update timestamp, and version.
- **Evidence**: `server.js` — `_getCurrencyData()`, `data/currency_conversion.json`

#### STATE-Q3: Concurrency Controls
- **Severity**: RISK
- **Finding**: No concurrency controls (no optimistic locking, ETags, or version fields). Service is stateless — reads in-memory cached JSON. Multiple concurrent requests are safe because no data mutation occurs.
- **Gap**: No concurrency controls. Not needed for current read-only design.
- **Recommendation**: Implement optimistic locking if mutable state is added.
- **Evidence**: `server.js` — `_getCurrencyData()` reads static JSON

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK
- **Finding**: No circuit breakers, retry logic, or timeout configurations. No external dependency calls (reads local JSON). No graceful degradation or backpressure.
- **Gap**: No resilience patterns. Low risk due to service simplicity.
- **Recommendation**: Add gRPC server-side request limits and graceful shutdown handling.
- **Evidence**: `server.js` — no resilience libraries, `package.json`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK
- **Finding**: No rate limiting at any layer. No API Gateway, no WAF, no application-level rate limiting. Server accepts unlimited connections.
- **Gap**: No protection against agent-induced DDoS.
- **Recommendation**: Deploy behind an API gateway with rate limiting or add gRPC interceptor-based rate limiting.
- **Evidence**: `server.js` — no rate limiting

#### STATE-Q6: Blast Radius and Transaction Limits
- **Severity**: RISK
- **Finding**: No configurable transaction limits. No per-agent request caps. Read-only service limits blast radius to availability impact.
- **Gap**: No per-identity request quotas.
- **Recommendation**: After AUTH-Q1, add per-identity request quotas.
- **Evidence**: `server.js` — no transaction limits

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: RISK
- **Finding**: No load tests, no auto-scaling, no capacity planning. Dockerfile runs single Node.js process. No HPA definitions.
- **Gap**: Unknown capacity limits. Single process has concurrency constraints.
- **Recommendation**: Conduct load testing. Define Kubernetes HPA policies. Consider multiple replicas.
- **Evidence**: `Dockerfile` — single `node server.js` process
### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State
- **Severity**: RISK
- **Finding**: No draft or pending state concept. Service is stateless and read-only. Both RPCs return immediate results. No approval workflows.
- **Gap**: No draft/pending state. Low impact for read-only service.
- **Recommendation**: Implement confirmation patterns at the orchestration layer if results feed into financial transactions.
- **Evidence**: `server.js` — immediate-response RPCs

#### HITL-Q2: Configurable Approval Gates
- **Severity**: RISK
- **Finding**: No approval gates. No configurable operation-level flags. No Step Functions with human approval tasks.
- **Gap**: No approval gate framework. Low priority for read-only operations.
- **Recommendation**: Implement approval gates at the orchestration layer for downstream write actions.
- **Evidence**: `server.js` — no approval logic

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK
- **Finding**: No separate environment configurations. No Docker Compose. No seed data scripts. Local testing is straightforward due to static JSON data.
- **Gap**: No formal sandbox/staging environment.
- **Recommendation**: Create Docker Compose for local testing. Define environment-specific configurations.
- **Evidence**: `Dockerfile` — single environment, absence of Docker Compose
### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO
- **Finding**: Service handles publicly available ECB currency conversion rates. No PII, PHI, financial records, or credentials stored or processed. Data is non-sensitive public reference data. No formal data classification tagging exists.
- **Gap**: No formal data classification policy. Data is inherently non-sensitive.
- **Recommendation**: Add a "PUBLIC" data classification label to service documentation.
- **Evidence**: `data/currency_conversion.json`, `server.js` — comment "Uses public data from European Central Bank"

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: No data residency requirements documented. Currency rates are public ECB data, not subject to GDPR/LGPD/HIPAA. No region-specific configurations.
- **Gap**: No documented data residency policy. Low risk for public data.
- **Recommendation**: Document that the data is public, non-regulated ECB reference data.
- **Evidence**: `data/currency_conversion.json`, `server.js`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK
- **Finding**: `GetSupportedCurrencies` returns all 33 currencies (no pagination/filtering). `Convert` accepts specific parameters for single conversion. Small result sets.
- **Gap**: No pagination on currency list. Acceptable for 33 entries.
- **Recommendation**: Add filtering if currency list grows significantly.
- **Evidence**: `proto/demo.proto`, `data/currency_conversion.json` — 33 currencies

#### DATA-Q4: System of Record Designations
- **Severity**: RISK
- **Finding**: No formal system-of-record designation. Code comment references ECB as source. No data ownership documentation or conflict resolution.
- **Gap**: No documented data provenance or ownership.
- **Recommendation**: Add data provenance documentation specifying ECB as authoritative source.
- **Evidence**: `server.js` — comment "Uses public data from European Central Bank"

#### DATA-Q5: Reliable Timestamps
- **Severity**: RISK
- **Finding**: No timestamps in data or API responses. JSON file has no `updated_at` or `effective_date`. `Money` message has no temporal fields. Critical gap for currency rates that change daily.
- **Gap**: No timestamps on currency rates. Agent cannot determine rate currency.
- **Recommendation**: Add `effective_date` field to currency data. Include timestamp metadata in API responses.
- **Evidence**: `data/currency_conversion.json`, `proto/demo.proto` — `Money` message

#### DATA-Q6: Data Freshness Signaling
- **Severity**: RISK
- **Finding**: No cache headers, data age indicators, or freshness metadata. Static JSON loaded via `require()` (cached by Node.js). Agent cannot determine data freshness.
- **Gap**: No data freshness signaling. Material risk for currency conversion.
- **Recommendation**: Add `rate_effective_date` response metadata. Implement periodic rate refresh.
- **Evidence**: `server.js` — `require('./data/currency_conversion.json')`, `data/currency_conversion.json`

#### DATA-Q7: PII Redaction in Logs
- **Severity**: RISK
- **Finding**: No PII redaction implemented. Service processes only currency codes and amounts (non-PII). Pino logs success/failure messages without sensitive data.
- **Gap**: No PII redaction framework. Low risk for current non-PII data.
- **Recommendation**: Add log scrubbing middleware for defense-in-depth.
- **Evidence**: `server.js` — Pino logger patterns

#### DATA-Q8: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics or monitoring. Static JSON has 33 entries, all non-null with consistent format. Quality is implicitly high but unmonitored.
- **Gap**: No data quality monitoring.
- **Recommendation**: Add basic data validation at startup (positive rates, valid ISO 4217 codes).
- **Evidence**: `data/currency_conversion.json` — 33 entries
### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Documentation and Versioning
- **Severity**: RISK
- **Finding**: `proto/demo.proto` provides schema documentation with proto3 syntax, typed messages, and inline comments. Well-documented `Money` message. No formal schema versioning (no v1/v2 directories), no schema registry, no changelog.
- **Gap**: No schema versioning. No changelog for schema changes.
- **Recommendation**: Implement proto package versioning. Add `buf` for breaking change detection. Maintain a schema changelog.
- **Evidence**: `proto/demo.proto` — `package hipstershop`, `syntax = "proto3"`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Field names are clear: `currency_code`, `units`, `nanos`, `from`, `to_code`. `Money` message has detailed documentation comments. No legacy abbreviations.
- **Gap**: No gap. Field names are LLM-friendly.
- **Recommendation**: No action needed.
- **Evidence**: `proto/demo.proto` — `Money` message, `CurrencyConversionRequest`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No data catalog (Glue, Collibra, DataHub). Proto file serves as de facto schema catalog. No broader metadata layer.
- **Gap**: No centralized catalog entry. Proto provides sufficient schema documentation for this service.
- **Recommendation**: Register CurrencyService in a centralized API catalog if available.
- **Evidence**: `proto/demo.proto`, absence of data catalog

#### DISC-Q4: Data Lineage
- **Severity**: INFO
- **Finding**: No data lineage tools. Code comment mentions ECB as data source. `genproto.sh` copies protos from shared directory (proto lineage). No formal lineage record.
- **Gap**: Minimal lineage. Adequate for current service.
- **Recommendation**: Add formal data lineage record documenting source, capture date, transformation, and update process.
- **Evidence**: `server.js` — ECB comment, `genproto.sh`, `data/currency_conversion.json`
### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK
- **Finding**: OpenTelemetry SDK configured with gRPC instrumentation (`@opentelemetry/instrumentation-grpc`, `@opentelemetry/sdk-node`). Tracing conditional on `ENABLE_TRACING=1`. Pino logger produces structured JSON with `severity` field. No `correlation_id`/`request_id` in logs. No trace-log correlation.
- **Gap**: Tracing is opt-in (disabled by default). Logs lack correlation IDs. No trace-log linkage.
- **Recommendation**: Enable tracing by default. Add `trace_id` and `request_id` to Pino log entries.
- **Evidence**: `server.js` — OpenTelemetry setup, Pino config; `package.json` — `@opentelemetry/*` dependencies

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK
- **Finding**: No alerting configuration. No CloudWatch alarms, no anomaly detection, no PagerDuty/OpsGenie. Metrics available via OpenTelemetry if enabled, but no thresholds defined.
- **Gap**: No alerting on error rates or latency. No proactive degradation detection.
- **Recommendation**: Configure alerting on gRPC error rates and P95 latency. Integrate with on-call notification.
- **Evidence**: `server.js` — health check endpoint, absence of alerting config

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics. Service logs success/failure but does not publish metrics on conversion volume, error rates by currency pair, or request patterns.
- **Gap**: No business outcome visibility.
- **Recommendation**: Add custom metrics for conversion count by currency pair, error rate by type, and request volume.
- **Evidence**: `server.js` — log-only observability
### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK
- **Finding**: No IaC files found (no Terraform, CloudFormation, CDK, Helm, Kustomize). Only a Dockerfile exists. Infrastructure for API gateways, IAM roles, secrets, and networking is not defined in this repository.
- **Gap**: No IaC governance. No peer review on infrastructure. No drift detection.
- **Recommendation**: Define Kubernetes Deployment, Service, NetworkPolicy, and HPA as IaC. Add PR review requirements. Enable drift detection.
- **Evidence**: Absence of IaC files, `Dockerfile` present

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK
- **Finding**: No CI/CD pipeline configuration. No GitHub Actions, GitLab CI, Jenkinsfile, or buildspec.yml. No contract tests. `package.json` test script outputs "Error: no test specified."
- **Gap**: No CI/CD. No contract testing. No breaking change detection.
- **Recommendation**: Create CI/CD pipeline. Add `buf breaking` for proto compatibility. Implement integration tests.
- **Evidence**: Absence of CI/CD files, `package.json` — test script placeholder

#### ENG-Q3: Rollback Capability
- **Severity**: RISK
- **Finding**: No deployment configuration. No blue/green, no canary, no CodeDeploy, no Helm rollback, no feature flags.
- **Gap**: No rollback capability in this repository.
- **Recommendation**: Define deployment strategy in IaC. Implement automatic rollback triggers.
- **Evidence**: `Dockerfile` only, absence of deployment configuration

#### ENG-Q4: API Test Coverage
- **Severity**: RISK
- **Finding**: Zero test coverage. `package.json` test script: `"echo \"Error: no test specified\" && exit 1"`. `client.js` is a manual test client excluded from Docker image.
- **Gap**: No automated tests. No input validation, error response, or edge case tests.
- **Recommendation**: Write automated gRPC tests for both RPCs covering valid, invalid, edge-case, and overflow scenarios. Add to CI.
- **Evidence**: `package.json` — test script, `client.js` — manual client, `.dockerignore` — excludes `client.js`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: RISK
- **Finding**: No encryption configuration. No KMS keys. Data embedded as plain-text JSON in container image. No IaC with encryption settings.
- **Gap**: No encryption at rest. Data is public (ECB rates), low sensitivity.
- **Recommendation**: Ensure container registry encrypts images. Enforce KMS encryption if database access is added.
- **Evidence**: `data/currency_conversion.json`, `Dockerfile`, absence of IaC

#### ENG-Q6: Cross-Origin and Network Policies
- **Severity**: BLOCKER
- **Finding**: gRPC server binds to `[::]:${PORT}` with `grpc.ServerCredentials.createInsecure()`. No security groups, no NetworkPolicies, no API gateway, no WAF, no firewall rules. No IaC defining network boundaries. Dockerfile exposes port 7000 without security controls.
- **Gap**: No network security configuration. Entire network surface is open.
- **Recommendation**: Define network policies as IaC restricting ingress to authorized consumers only. Add API gateway or service mesh.
- **Evidence**: `server.js` — `createInsecure()`, bind to `[::]:${PORT}`, `Dockerfile` — `EXPOSE 7000`
## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `server.js` | API-Q1, API-Q2, API-Q3, API-Q4, API-Q5, API-Q6, API-Q7, API-Q8, API-Q9, API-Q10, AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q6, AUTH-Q7, AUTH-Q8, STATE-Q1, STATE-Q2, STATE-Q3, STATE-Q4, STATE-Q5, STATE-Q6, HITL-Q1, HITL-Q2, DATA-Q1, DATA-Q2, DATA-Q4, DATA-Q5, DATA-Q6, DATA-Q7, DISC-Q4, OBS-Q1, OBS-Q2, OBS-Q3, ENG-Q6 |
| `client.js` | ENG-Q2, ENG-Q4 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `proto/demo.proto` | API-Q1, API-Q2, API-Q4, API-Q5, API-Q6, API-Q7, API-Q8, DATA-Q3, DATA-Q5, DISC-Q1, DISC-Q2, DISC-Q3 |
| `proto/grpc/health/v1/health.proto` | API-Q1 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `Dockerfile` | AUTH-Q6, STATE-Q7, HITL-Q3, ENG-Q1, ENG-Q3, ENG-Q5, ENG-Q6 |
| `.dockerignore` | ENG-Q4 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `package.json` | API-Q5, AUTH-Q6, STATE-Q4, OBS-Q1, ENG-Q2, ENG-Q4 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `data/currency_conversion.json` | API-Q8, API-Q10, STATE-Q1, STATE-Q2, DATA-Q1, DATA-Q2, DATA-Q3, DATA-Q5, DATA-Q6, DATA-Q8, DISC-Q4, ENG-Q5 |

### Scripts
| File | Questions Referenced |
|------|---------------------|
| `genproto.sh` | DISC-Q4 |
