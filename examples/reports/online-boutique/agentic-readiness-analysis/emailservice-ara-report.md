# Agentic Readiness Analysis Report

**Target**: ./services/microservices-demo/src/emailservice
**Date**: 2026-04-16
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**Repository Type**: application
**Service Archetype**: event-processor (user-provided)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: python, grpc, notifications
**Context**: Python gRPC service sending order confirmation emails.

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 2 | **RISKs**: 10 | **INFOs**: 19

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 2 |
| RISK | 10 |
| INFO | 19 |
| N/A | 0 |
| Not Evaluated (extended) | 12 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 7
**Extended Questions Not Triggered**: 12
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: event-processor (user-provided)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: The gRPC server binds on an insecure port (`server.add_insecure_port('[::]:'+port)` in `email_server.py` `start()` function). No authentication mechanism exists — no OAuth2 client credentials flow, no API key authentication, no mTLS configuration, and no gRPC interceptors for auth validation. A Kubernetes ServiceAccount (`emailservice`) is defined in the Helm chart, but this only provides Kubernetes-level identity — no application-level authentication is enforced. The Helm chart has `authorizationPolicies.create: false`, so Istio AuthorizationPolicies are not deployed. Any pod within the cluster network can call `SendOrderConfirmation` without presenting credentials.
- **Gap**: No machine identity authentication at the application layer. Agents (or any caller) cannot be identified or attributed in logs. The service accepts all incoming gRPC requests without verifying the caller's identity.
- **Remediation**:
  - **Immediate**: Add a gRPC server interceptor that validates an authentication token (API key, JWT, or mTLS certificate) on every incoming request. Alternatively, set `authorizationPolicies.create: true` in Helm values to enable Istio mTLS enforcement.
  - **Target State**: Every gRPC call to the emailservice is authenticated with a machine identity (service account or API key) that is logged and attributable in audit records.
  - **Estimated Effort**: Medium
  - **Dependencies**: AUTH-Q6 (audit logging must capture the machine identity principal)
- **Evidence**: `src/emailservice/email_server.py` (insecure port binding), `helm-chart/templates/emailservice.yaml` (ServiceAccount without auth enforcement), `helm-chart/values.yaml` (`authorizationPolicies.create: false`)

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: The `SendOrderConfirmationRequest` message in `protos/demo.proto` contains an `email` field (PII — email address) and an `OrderResult` message containing `shipping_address` (PII — physical address with `street_address`, `city`, `state`, `country`, `zip_code`). None of these fields have sensitivity classification, field-level encryption, or access controls. The `DummyEmailService.SendOrderConfirmation` method in `email_server.py` directly logs the email address: `logger.info('A request to send order confirmation email to {} has been received.'.format(request.email))`. No PII detection or data classification tags are present anywhere in the codebase or IaC.
- **Gap**: Sensitive data (email addresses, physical addresses) is unclassified and unprotected. No field-level access controls prevent an agent from retrieving PII without explicit authorization. PII is logged to stdout without masking.
- **Remediation**:
  - **Immediate**: Classify the `email` and `shipping_address` fields as PII in a data classification document or proto annotation. Implement PII masking in log output (replace `request.email` with a masked value like `****@domain.com`).
  - **Target State**: All PII fields are classified and tagged. Field-level access controls prevent unauthorized retrieval. Logs do not contain unmasked PII.
  - **Estimated Effort**: Medium
  - **Dependencies**: DATA-Q6 (PII redaction in logs) — resolving DATA-Q1 should include log masking as part of the remediation.
- **Evidence**: `protos/demo.proto` (`SendOrderConfirmationRequest.email`, `OrderResult.shipping_address`), `src/emailservice/email_server.py` (PII logged directly in `DummyEmailService.SendOrderConfirmation`)

## RISKs — Proceed with Compensating Controls

### API-Q2: Machine-Readable API Specification

- **Severity**: RISK
- **Finding**: The `protos/demo.proto` file serves as a machine-readable specification for the EmailService gRPC interface. It defines the `EmailService` with `SendOrderConfirmation` RPC, along with typed request/response messages. Generated Python stubs (`demo_pb2.py`, `demo_pb2_grpc.py`) are committed to the repository.
- **Gap**: Generated code is committed rather than generated at build time, creating spec-implementation drift risk. No CI step validates that generated code matches the proto definition.
- **Compensating Controls**:
  - Use the committed proto file as the canonical spec for agent tool generation.
  - Add a CI step to regenerate proto stubs and fail if they differ from committed code.
- **Remediation Timeline**: 30 days
- **Recommendation**: Add a CI job that runs `genproto.sh` and diffs the output against committed files, failing on mismatch.
- **Evidence**: `protos/demo.proto`, `src/emailservice/demo_pb2.py`, `src/emailservice/demo_pb2_grpc.py`

### API-Q3: Structured Error Responses

- **Severity**: RISK
- **Finding**: The `EmailService.SendOrderConfirmation` method uses gRPC status codes (`grpc.StatusCode.INTERNAL`) and detail strings for error reporting. Both template errors and send errors return the same `INTERNAL` status code with human-readable strings, making them indistinguishable to an agent.
- **Gap**: No structured error body with machine-readable error codes or retryable flags. An agent cannot determine if an error is retryable without parsing the detail string.
- **Compensating Controls**:
  - Map gRPC status codes to retry logic at the agent orchestration layer.
  - Log error types server-side and correlate via trace IDs.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add structured error metadata using gRPC trailing metadata or a custom error proto message that includes error_code, retryable flag, and category.
- **Evidence**: `src/emailservice/email_server.py` (`EmailService.SendOrderConfirmation` error handling)

### AUTH-Q2: Scoped Permissions (Least Privilege)

- **Severity**: RISK
- **Finding**: The Kubernetes ServiceAccount `emailservice` is defined with no associated RoleBinding or ClusterRoleBinding. The application code has no permission model. The gRPC service has a single RPC (`SendOrderConfirmation`) with no permission differentiation.
- **Gap**: No scoped permission model exists. No IAM policies, RBAC definitions, or application-level permission checks allow restricting an agent to read-only access.
- **Compensating Controls**:
  - Use Kubernetes NetworkPolicy (defined in Helm chart when `networkPolicies.create: true`) to restrict which pods can call the emailservice.
  - Scope agent access at the orchestration layer by not including `SendOrderConfirmation` in the agent's tool set.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Define Kubernetes RBAC roles specific to emailservice and implement gRPC authorization interceptors that validate caller permissions.
- **Evidence**: `helm-chart/templates/emailservice.yaml` (ServiceAccount with no RBAC)

### AUTH-Q3: Action-Level Authorization

- **Severity**: RISK
- **Finding**: No authorization checks in `email_server.py`. The `SendOrderConfirmation` method processes any incoming gRPC request without validating caller permissions. The Helm chart supports Istio AuthorizationPolicies but `authorizationPolicies.create` is `false`.
- **Gap**: No action-level authorization. Cannot enforce "agent can read order status but not send confirmation emails" at the application layer.
- **Compensating Controls**:
  - Restrict access at the Kubernetes network layer using NetworkPolicies (ingress restricted to checkoutservice).
  - Enable Istio AuthorizationPolicies by setting `authorizationPolicies.create: true`.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Enable Istio AuthorizationPolicies or add a gRPC interceptor that checks caller identity against an allow-list.
- **Evidence**: `src/emailservice/email_server.py` (no auth checks), `helm-chart/values.yaml` (`authorizationPolicies.create: false`)

### AUTH-Q5: Credential Management

- **Severity**: RISK
- **Finding**: In the current `DummyEmailService` mode, no credentials are used. The `EmailService` class references undefined variables (`project_id`, `region`, `sender_id`, `from_address`) in `send_email()`, suggesting these would be configuration values. No secrets management integration exists. No hardcoded credentials found.
- **Gap**: No secrets management system integrated. When transitioning from dummy mode to production, credentials for the email provider would need to be managed.
- **Compensating Controls**:
  - Dummy mode avoids credential exposure in the current state.
  - Kubernetes Secrets can provide basic secret injection for the transition.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Integrate a secrets management system for email provider credentials with automatic rotation.
- **Evidence**: `src/emailservice/email_server.py` (`EmailService.send_email()` — undefined credential variables)

### AUTH-Q6: Immutable Audit Logging ⚡

- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: JSON structured logging is implemented via `python-json-logger` in `logger.py` with `CustomJsonFormatter` adding `timestamp` and `severity` fields. Logs are written to stdout. No CloudTrail, Cloud Audit Logs, or immutable log storage configuration exists. No log retention policies configured.
- **Gap**: Logs are not immutable or tamper-evident. Stdout logs in Kubernetes can be rotated, deleted, or modified. No authenticated principal is logged per request.
- **Compensating Controls**:
  - GKE Autopilot automatically ships container stdout logs to Cloud Logging, which provides some retention.
  - Enable Cloud Audit Logs for the GKE cluster as a compensating control.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure Cloud Audit Logs with immutable retention. Add caller identity to structured log output.
- **Evidence**: `src/emailservice/logger.py` (stdout logging, no immutability)

### AUTH-Q7: Agent Identity Suspension

- **Severity**: RISK
- **Finding**: No API key revocation, IAM role deactivation, or agent identity suspension mechanism exists. Deleting the Kubernetes ServiceAccount would take down the service entirely. No individual agent identity management or kill-switch capability.
- **Gap**: Cannot suspend a specific agent's access without affecting all callers.
- **Compensating Controls**:
  - Use Kubernetes NetworkPolicy to block specific source pods/namespaces.
  - Implement an agent allow-list in a ConfigMap that can be updated without redeployment.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement per-agent API keys or tokens that can be individually revoked via a gRPC interceptor checking an agent allow-list.
- **Evidence**: `helm-chart/templates/emailservice.yaml` (single ServiceAccount, no revocation mechanism)

### OBS-Q1: Distributed Tracing and Structured Logging

- **Severity**: RISK
- **Finding**: OpenTelemetry tracing configured in `email_server.py` with `TracerProvider`, `BatchSpanProcessor`, and `OTLPSpanExporter`. `GrpcInstrumentorServer` instruments gRPC calls. Tracing is conditional on `ENABLE_TRACING=1`. Helm chart has `googleCloudOperations.tracing: false`, so `ENABLE_TRACING` env var is not set. JSON structured logging via `python-json-logger` with `timestamp` and `severity` fields. No `correlation_id` or `request_id` field linking logs to traces.
- **Gap**: Tracing disabled by default (Helm `tracing: false`). No log-trace correlation. Without correlation IDs, logs and traces cannot be joined for agent-initiated requests.
- **Compensating Controls**:
  - Enable tracing by setting `googleCloudOperations.tracing: true` in Helm values.
  - Use OpenTelemetry's log-trace correlation to auto-inject trace IDs.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Set `tracing: true` in Helm values. Add trace ID injection to the JSON logger. Add `request_id` field to all log entries.
- **Evidence**: `src/emailservice/email_server.py`, `src/emailservice/logger.py`, `helm-chart/values.yaml` (`tracing: false`), `src/emailservice/requirements.txt`

### OBS-Q2: Alerting on Error Rates and Latency

- **Severity**: RISK
- **Finding**: No alerting configuration for the emailservice. Kubernetes `livenessProbe` and `readinessProbe` (gRPC health checks on port 8080) restart unhealthy pods but do not alert on error rates or latency. No SLO-based alerting.
- **Gap**: Service degradation not detectable before agent cascading failures.
- **Compensating Controls**:
  - Enable OpenTelemetry metrics export and create alerting policies based on span error rates.
  - GKE provides basic cluster-level monitoring.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create alerting policies for gRPC error rate > 1%, P95 latency > 1s, and pod restart count > 2 in 10 minutes.
- **Evidence**: `helm-chart/templates/emailservice.yaml` (health probes only)

### ENG-Q4: API Test Coverage

- **Severity**: RISK
- **Finding**: Zero automated tests for the emailservice. No test files in `src/emailservice/`. CI pipelines do not run any Python tests. No Postman/Newman collections, pytest API tests, or contract tests.
- **Gap**: Complete absence of automated test coverage for the agent-facing API. Input validation, error responses, edge cases, and happy paths are untested.
- **Compensating Controls**:
  - Loadgenerator smoke tests validate end-to-end flow at integration level.
  - Manual testing during development provides some coverage.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create pytest test suite covering: successful send in dummy mode, error handling paths, health check responses, invalid request handling. Add to CI.
- **Evidence**: No test files in `src/emailservice/`, `.github/workflows/ci-pr.yaml`

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO
- **Finding**: The emailservice exposes a documented gRPC interface defined in `protos/demo.proto`. The `EmailService` service definition includes one RPC: `SendOrderConfirmation(SendOrderConfirmationRequest) returns (Empty)`. Implemented via `DummyEmailService` and `EmailService` classes. Generated typed stubs provide strongly-typed client/server code. This is a documented, typed interface — not direct database access, file-based exchange, or UI automation.
- **Implication**: The gRPC interface is suitable for agent tool binding. Agent tool definitions can be generated from the proto file.
- **Recommendation**: Continue maintaining the proto file as the canonical API definition.
- **Evidence**: `protos/demo.proto`, `src/emailservice/email_server.py`, `src/emailservice/demo_pb2_grpc.py`

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: `SendOrderConfirmation` is a write operation (sends an email) with no idempotency key support. Calling the RPC twice with the same order data will send two emails. No idempotency middleware, unique constraint enforcement, or deduplication logic exists.
- **Implication**: In a read-only agent scope, this is informational. If the agent scope expands to write-enabled, this becomes a BLOCKER.
- **Recommendation**: Plan for idempotency before expanding to write-enabled scope. Add an idempotency key field to `SendOrderConfirmationRequest`.
- **Evidence**: `protos/demo.proto`, `src/emailservice/email_server.py`

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: gRPC with Protocol Buffers — strongly-typed binary serialization. All messages defined with explicit field types. Response for `SendOrderConfirmation` is `Empty`.
- **Implication**: Protocol Buffers are agent-friendly. The `Empty` response limits agent insight. gRPC requires specific client libraries.
- **Recommendation**: Consider JSON transcoding proxy if agents need REST/JSON access.
- **Evidence**: `protos/demo.proto`, `src/emailservice/demo_pb2.py`

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limit documentation or headers. Implicit capacity limit of 10 concurrent workers not documented or exposed to callers.
- **Implication**: Agents cannot self-throttle based on server-provided rate information.
- **Recommendation**: Document effective capacity (10 concurrent requests). Return rate limit metadata in gRPC headers if rate limiting is added.
- **Evidence**: `src/emailservice/email_server.py`

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: INFO
- **Finding**: No JWT parsing, OAuth2 flows, or token exchange mechanisms. Request contains only `email` and `order` — no user context or identity headers. No distinction between agent-as-self and agent-on-behalf-of-user modes. Downgraded to INFO for event-processor archetype — notification sender where caller identity context has minimal security impact.
- **Implication**: For an event-processor with read-only scope, identity propagation is informational.
- **Recommendation**: Propagate user identity token via gRPC metadata from checkoutservice.
- **Evidence**: `protos/demo.proto`, `src/emailservice/email_client.py`

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Fire-and-forget email sender. No saga pattern, compensating transaction, undo endpoint, or Step Functions. Once an email is sent, it cannot be recalled. For an event-processor archetype, fire-and-forget is the expected behavioral pattern — compensation is architecturally atypical for notification senders.
- **Implication**: For read-only agents interacting with an event-processor, compensation is informational. If scope expands to write-enabled, this upgrades to BLOCKER.
- **Recommendation**: If expanding to write-enabled scope, implement a queued email pattern with configurable delay and cancellation RPC.
- **Evidence**: `src/emailservice/email_server.py`

### STATE-Q5: Rate Limiting and Throttling

- **Severity**: INFO
- **Finding**: No rate limiting at the application layer. The `ThreadPoolExecutor(max_workers=10)` provides implicit capacity limiting but is not configurable rate limiting. The Kubernetes ClusterIP service provides no throttling. NetworkPolicy restricts callers to only checkoutservice, limiting blast radius. For a read-only agent scope against an event-processor, the agent does not directly call the service at machine speed.
- **Implication**: Rate limiting is informational for read-only agents. The NetworkPolicy already restricts the caller surface. Becomes RISK when agent scope expands to write-enabled.
- **Recommendation**: Add gRPC rate limiting interceptor before expanding to write-enabled scope.
- **Evidence**: `src/emailservice/email_server.py`, `helm-chart/templates/emailservice.yaml` (NetworkPolicy)

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits. No limits on emails per hour, per session, per agent, or per order.
- **Implication**: For read-only agents, transaction limits are informational. If scope expands to write-enabled, a runaway agent could send thousands of emails.
- **Recommendation**: Define transaction limits before write-enabled scope expansion.
- **Evidence**: `src/emailservice/email_server.py`

### DATA-Q2: Data Residency and Sovereignty ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No data residency requirements documented. No GDPR, LGPD, or HIPAA compliance references. Email addresses (PII) pass through the service transiently but are not persisted. For a read-only agent scope against an event-processor handling transient PII, the residency risk is informational.
- **Implication**: Data residency is informational for read-only agents. If scope expands to write-enabled, this upgrades to BLOCKER.
- **Recommendation**: Document data residency requirements for PII before expanding agent scope.
- **Evidence**: `protos/demo.proto` (email, shipping_address fields)

### DATA-Q6: PII Redaction in Logs

- **Severity**: INFO
- **Finding**: `DummyEmailService.SendOrderConfirmation` logs the email address directly: `logger.info('A request to send order confirmation email to {} has been received.'.format(request.email))`. No PII masking or log scrubbing. `logger.py` uses `python-json-logger` with no PII filtering. For an event-processor with read-only agent scope, PII in logs is an operational concern but not a deployment gate — the agent does not read logs.
- **Implication**: PII in logs is a compliance concern but does not directly gate read-only agent deployment. Becomes RISK if agents gain log access or scope expands.
- **Recommendation**: Implement log masking utility that redacts PII before logging.
- **Evidence**: `src/emailservice/email_server.py`, `src/emailservice/logger.py`

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality dashboards or metrics. Service is a stateless consumer of upstream data. No input validation.
- **Implication**: If upstream data quality degrades, the emailservice will silently send incorrect confirmation emails.
- **Recommendation**: Add input validation for required fields (email format, order_id presence).
- **Evidence**: `src/emailservice/email_server.py`, `protos/demo.proto`

### HITL-Q3: Sandbox/Staging Environment

- **Severity**: INFO
- **Finding**: Skaffold supports local development. Dummy mode always active (`start(dummy_mode = True)`), providing a safe sandbox where no real emails are sent. No dedicated staging with production-equivalent configuration. For an event-processor with read-only scope, dummy mode serves as an adequate sandbox for initial agent testing.
- **Implication**: Dummy mode provides a safe testing surface for read-only agents. Becomes RISK when transitioning to production email sending or write-enabled scope.
- **Recommendation**: Create persistent staging with test email provider before expanding scope.
- **Evidence**: `skaffold.yaml`, `src/emailservice/email_server.py`

### DISC-Q1: Schema Versioning and API Contracts

- **Severity**: INFO
- **Finding**: Proto file uses `proto3` syntax with `hipstershop` package — no version indicator. No changelog or version metadata. Generated code committed. For an event-processor with a single stable RPC, schema churn risk is low.
- **Implication**: Single-RPC interface has low schema change frequency. Protobuf backward compatibility rules provide implicit protection.
- **Recommendation**: Add version metadata (e.g., `hipstershop.email.v1`). Implement buf breaking in CI when the service evolves.
- **Evidence**: `protos/demo.proto` (package `hipstershop` with no version), `src/emailservice/demo_pb2.py`

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Protobuf field names are human-readable and semantically clear: `email`, `order`, `order_id`, `shipping_tracking_id`, `shipping_cost`, `currency_code`, `street_address`, `city`, `state`, `country`, `zip_code`. No legacy abbreviations.
- **Implication**: LLM-based agents can interpret field names without a data dictionary. Tool definitions will be self-documenting.
- **Recommendation**: Maintain clear naming conventions.
- **Evidence**: `protos/demo.proto`, `src/emailservice/templates/confirmation.html`

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No data catalog (no AWS Glue, Collibra, DataHub). Proto file is the sole schema reference. No service registry.
- **Implication**: Building agent tools requires reading the proto file directly. No self-service discovery.
- **Recommendation**: Register the emailservice in a service catalog (e.g., Backstage).
- **Evidence**: `protos/demo.proto`

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No custom business metrics. Only operational logs via `python-json-logger`.
- **Implication**: Cannot measure whether agent-initiated emails produce good outcomes.
- **Recommendation**: Add custom metrics: emails_sent_total, email_delivery_status, template_render_latency.
- **Evidence**: `src/emailservice/email_server.py`, `src/emailservice/logger.py`

### ENG-Q1: Infrastructure Governance for Agent-Facing Surface

- **Severity**: INFO
- **Finding**: IaC defined (Kubernetes manifests, Helm chart). PR review enforced via GitHub Actions. No drift detection. Two of three governance sub-checks pass. For a P2 event-processor with read-only scope, the governance gap is informational.
- **Implication**: Drift detection gap is a long-term concern but does not gate read-only agent deployment for a P2 event-processor.
- **Recommendation**: Enable drift detection when expanding agent scope or priority.
- **Evidence**: `helm-chart/templates/emailservice.yaml`, `helm-chart/values.yaml`

### ENG-Q2: CI/CD with API Contract Testing

- **Severity**: INFO
- **Finding**: CI runs Go/C# tests but zero Python tests for the emailservice. No contract testing or proto breaking change detection. For an event-processor with a single stable RPC and read-only scope, the contract testing gap is informational.
- **Implication**: Low schema churn risk for a single-RPC event-processor. Becomes RISK when the service evolves or scope expands.
- **Recommendation**: Add pytest tests and `buf breaking` in CI when the service evolves.
- **Evidence**: `.github/workflows/ci-pr.yaml`, `.github/workflows/ci-main.yaml`

### ENG-Q3: Rollback Capability

- **Severity**: INFO
- **Finding**: Skaffold-based deployment with default `RollingUpdate`. No automated rollback triggers, blue/green, canary, or feature flags. For a P2 event-processor with read-only scope, the rollback gap is informational.
- **Implication**: Manual rollback is acceptable for a P2 non-critical event-processor. Becomes RISK when priority increases or scope expands.
- **Recommendation**: Implement automated rollback triggers when expanding scope or priority.
- **Evidence**: `skaffold.yaml`, `helm-chart/templates/emailservice.yaml`

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: gRPC interface defined in `protos/demo.proto` with `EmailService` service and `SendOrderConfirmation` RPC. Implemented via `DummyEmailService` and `EmailService` classes. Generated typed stubs committed. Documented, typed interface.
- **Gap**: N/A — requirement met.
- **Recommendation**: Continue maintaining the proto file as the canonical API definition.
- **Evidence**: `protos/demo.proto`, `src/emailservice/email_server.py`, `src/emailservice/demo_pb2_grpc.py`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK
- **Finding**: `protos/demo.proto` is a machine-readable protobuf specification. Generated stubs committed rather than generated at build time. No CI validation of spec-implementation consistency.
- **Gap**: Spec-implementation drift risk from committed generated code.
- **Recommendation**: Add CI job to regenerate stubs and diff against committed files.
- **Evidence**: `protos/demo.proto`, `src/emailservice/demo_pb2.py`, `src/emailservice/genproto.sh`

#### API-Q3: Structured Error Responses
- **Severity**: RISK
- **Finding**: Two error paths both return `grpc.StatusCode.INTERNAL` with human-readable detail strings. No structured error body, no retryable flags.
- **Gap**: Errors indistinguishable to agents. No machine-readable error codes.
- **Recommendation**: Add structured error metadata via gRPC trailing metadata or custom error proto.
- **Evidence**: `src/emailservice/email_server.py`

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: `SendOrderConfirmation` has no idempotency key. Duplicate calls send duplicate emails. No deduplication logic.
- **Gap**: No idempotency support on write operation.
- **Recommendation**: Add idempotency key field before expanding to write-enabled scope.
- **Evidence**: `protos/demo.proto`, `src/emailservice/email_server.py`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: gRPC with Protocol Buffers — strongly-typed binary serialization. Response is `Empty` (no data returned).
- **Gap**: `Empty` response limits agent insight into operation result.
- **Recommendation**: Consider JSON transcoding proxy for REST/JSON agent access.
- **Evidence**: `protos/demo.proto`, `src/emailservice/demo_pb2.py`

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `event-processor`, agent_scope: `read-only`.
- **Trigger**: Service has operations >30s OR long-running workflows.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `event-processor`, agent_scope: `read-only`.
- **Trigger**: Service has state changes (stateful-crud, orchestrator).
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit documentation or headers. Implicit capacity limit of 10 concurrent workers not documented.
- **Gap**: Agents cannot self-throttle based on server-provided rate information.
- **Recommendation**: Document effective capacity; return rate limit metadata in gRPC headers if rate limiting is added.
- **Evidence**: `src/emailservice/email_server.py`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: Insecure port binding (`server.add_insecure_port`). No OAuth2, API key, mTLS, or gRPC auth interceptors. `authorizationPolicies.create: false` in Helm. Any pod can call `SendOrderConfirmation` without credentials.
- **Gap**: No machine identity authentication at the application layer.
- **Recommendation**: Add gRPC auth interceptor or enable Istio AuthorizationPolicies.
- **Evidence**: `src/emailservice/email_server.py`, `helm-chart/templates/emailservice.yaml`, `helm-chart/values.yaml`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK
- **Finding**: ServiceAccount with no RBAC. Single RPC with no permission differentiation. No application-level permission model.
- **Gap**: No scoped permission model for agent access restriction.
- **Recommendation**: Define RBAC roles and gRPC authorization interceptors.
- **Evidence**: `helm-chart/templates/emailservice.yaml`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK
- **Finding**: No authorization checks in code. `authorizationPolicies.create: false`. Single RPC accepts all callers equally.
- **Gap**: No action-level authorization enforcement.
- **Recommendation**: Enable Istio AuthorizationPolicies or add gRPC interceptor with allow-list.
- **Evidence**: `src/emailservice/email_server.py`, `helm-chart/values.yaml`

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: No JWT parsing, OAuth2 flows, or token exchange. Request contains only `email` and `order` — no user context or identity headers. No dual-mode distinction. Downgraded to INFO for event-processor archetype.
- **Gap**: No identity propagation or dual-mode distinction.
- **Recommendation**: Propagate user identity token via gRPC metadata from checkoutservice.
- **Evidence**: `protos/demo.proto`, `src/emailservice/email_client.py`

#### AUTH-Q5: Credential Management
- **Severity**: RISK
- **Finding**: Dummy mode uses no credentials. `EmailService.send_email()` references undefined variables for production config. No secrets management integration. No hardcoded credentials found.
- **Gap**: No secrets management for future production credentials.
- **Recommendation**: Integrate secrets management system with automatic rotation.
- **Evidence**: `src/emailservice/email_server.py`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: JSON structured logging to stdout. No immutable log storage, no CloudTrail, no caller identity in logs.
- **Gap**: Logs not immutable or tamper-evident. No authenticated principal logged per request.
- **Recommendation**: Configure immutable log storage; add caller identity to logs.
- **Evidence**: `src/emailservice/logger.py`

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK
- **Finding**: No API key revocation or agent identity suspension mechanism. Deleting ServiceAccount would take down the entire service.
- **Gap**: Cannot suspend individual agent access without affecting all callers.
- **Recommendation**: Implement per-agent tokens with individual revocation capability.
- **Evidence**: `helm-chart/templates/emailservice.yaml`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Fire-and-forget email sending. No saga pattern, undo endpoint, or compensation logic. Expected pattern for event-processor archetype.
- **Gap**: Sent emails are irreversible. No rollback capability.
- **Recommendation**: Implement queued email pattern with cancellation before expanding to write-enabled scope.
- **Evidence**: `src/emailservice/email_server.py`

#### STATE-Q2: Queryable Current State
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `event-processor`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator).
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q3: Concurrency Controls
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `event-processor`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled AND service has persistent state.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `event-processor`, agent_scope: `read-only`.
- **Trigger**: Service has external dependencies (calls other services or external APIs).
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: INFO
- **Finding**: No rate limiting at application or infrastructure layer. Implicit limit of 10 concurrent workers. NetworkPolicy restricts callers to checkoutservice. For read-only agent scope, the agent does not directly call the service at machine speed.
- **Gap**: No configurable rate limiting. Informational for read-only scope.
- **Recommendation**: Add gRPC rate limiting interceptor before expanding to write-enabled scope.
- **Evidence**: `src/emailservice/email_server.py`, `helm-chart/templates/emailservice.yaml`

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits. No per-agent or per-session volume constraints.
- **Gap**: No safety valve for high-volume agent operations.
- **Recommendation**: Define transaction limits before write-enabled scope expansion.
- **Evidence**: `src/emailservice/email_server.py`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `event-processor`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `event-processor`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q2: Configurable Approval Gates
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `event-processor`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: INFO
- **Finding**: Skaffold for local dev. Dummy mode always active, providing safe sandbox. No persistent staging with production-equivalent data.
- **Gap**: No persistent staging environment. Dummy mode serves as adequate sandbox for read-only agent testing.
- **Recommendation**: Create persistent staging with test email provider before expanding scope.
- **Evidence**: `skaffold.yaml`, `src/emailservice/email_server.py`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: Email addresses and shipping addresses (PII) handled without classification, field-level encryption, or access controls. PII logged directly to stdout.
- **Gap**: Sensitive data unclassified and unprotected. No field-level access controls.
- **Recommendation**: Classify PII fields; implement log masking; add field-level access controls.
- **Evidence**: `protos/demo.proto`, `src/emailservice/email_server.py`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No data residency documentation or controls. PII passes through transiently but is not persisted.
- **Gap**: No data residency controls for PII. Informational for read-only scope.
- **Recommendation**: Document residency requirements before expanding agent scope.
- **Evidence**: `protos/demo.proto`

#### DATA-Q3: Selective Query Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `event-processor`, agent_scope: `read-only`.
- **Trigger**: Service has list/query endpoints with potentially unbounded results.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q4: System of Record Designations
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `event-processor`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway).
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `event-processor`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator).
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q6: PII Redaction in Logs
- **Severity**: INFO
- **Finding**: Email address logged directly in `DummyEmailService.SendOrderConfirmation`. No PII masking or log scrubbing. For read-only agent scope, PII in logs is an operational concern but not a deployment gate.
- **Gap**: PII in plain text in stdout logs. Informational for read-only scope.
- **Recommendation**: Implement log masking utility for PII redaction.
- **Evidence**: `src/emailservice/email_server.py`, `src/emailservice/logger.py`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality dashboards or metrics. Stateless consumer of upstream data. No input validation.
- **Gap**: No data quality monitoring or input validation.
- **Recommendation**: Add input validation for required fields (email format, order_id).
- **Evidence**: `src/emailservice/email_server.py`, `protos/demo.proto`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: INFO
- **Finding**: Proto file uses `proto3` with `hipstershop` package — no version indicator. No changelog. Generated code committed. Single stable RPC with low schema churn risk.
- **Gap**: No schema versioning. Low risk for single-RPC event-processor.
- **Recommendation**: Add version metadata; implement buf breaking in CI when the service evolves.
- **Evidence**: `protos/demo.proto`, `src/emailservice/demo_pb2.py`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Field names are human-readable and semantically clear. No legacy abbreviations.
- **Gap**: N/A — requirement met.
- **Recommendation**: Maintain clear naming conventions.
- **Evidence**: `protos/demo.proto`, `src/emailservice/templates/confirmation.html`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No data catalog or metadata layer. Proto file is the sole schema reference.
- **Gap**: No self-service discovery mechanism.
- **Recommendation**: Register the emailservice in a service catalog (e.g., Backstage).
- **Evidence**: `protos/demo.proto`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK
- **Finding**: OpenTelemetry tracing configured but disabled (Helm `tracing: false`). JSON structured logging via `python-json-logger`. No correlation ID linking logs to traces.
- **Gap**: Tracing disabled by default. No log-trace correlation.
- **Recommendation**: Set `tracing: true` in Helm values; add trace ID injection to logger.
- **Evidence**: `src/emailservice/email_server.py`, `src/emailservice/logger.py`, `helm-chart/values.yaml`, `src/emailservice/requirements.txt`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK
- **Finding**: No alerting configuration. Health probes exist but no error rate or latency alerting.
- **Gap**: Service degradation not detectable before agent cascading failures.
- **Recommendation**: Create alerting policies for error rate, latency, and pod restarts.
- **Evidence**: `helm-chart/templates/emailservice.yaml`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics. Only operational logs.
- **Gap**: Cannot measure whether agent-initiated emails produce good outcomes.
- **Recommendation**: Add custom metrics: emails_sent_total, email_delivery_status, template_render_latency.
- **Evidence**: `src/emailservice/email_server.py`, `src/emailservice/logger.py`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: INFO
- **Finding**: IaC defined (Helm chart). PR review enforced. No drift detection. Two of three governance sub-checks pass. Informational for P2 event-processor.
- **Gap**: Drift detection missing. Informational for read-only scope.
- **Recommendation**: Enable drift detection when expanding scope or priority.
- **Evidence**: `helm-chart/templates/emailservice.yaml`, `helm-chart/values.yaml`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: INFO
- **Finding**: CI runs Go/C# tests but zero Python tests for emailservice. No contract testing. Informational for single stable RPC with read-only scope.
- **Gap**: No automated API contract validation. Low risk for single-RPC event-processor.
- **Recommendation**: Add pytest tests and `buf breaking` in CI when the service evolves.
- **Evidence**: `.github/workflows/ci-pr.yaml`, `.github/workflows/ci-main.yaml`

#### ENG-Q3: Rollback Capability
- **Severity**: INFO
- **Finding**: Skaffold with default `RollingUpdate`. No automated rollback. Informational for P2 event-processor.
- **Gap**: Manual rollback only. Acceptable for P2 non-critical service.
- **Recommendation**: Implement automated rollback when expanding scope or priority.
- **Evidence**: `skaffold.yaml`, `helm-chart/templates/emailservice.yaml`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK
- **Finding**: Zero automated tests for the emailservice. No test files. CI does not run Python tests.
- **Gap**: Complete absence of test coverage for agent-facing API.
- **Recommendation**: Create pytest test suite; add to CI pipeline.
- **Evidence**: No test files in `src/emailservice/`, `.github/workflows/ci-pr.yaml`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `event-processor`, agent_scope: `read-only`.
- **Trigger**: Service has persistent data stores.
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

---

## Evidence Index

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `protos/demo.proto` | API-Q1, API-Q2, API-Q4, API-Q5, API-Q8, AUTH-Q4, DATA-Q1, DATA-Q2, DATA-Q7, DISC-Q1, DISC-Q2 |

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `src/emailservice/email_server.py` | API-Q1, API-Q3, API-Q4, API-Q8, AUTH-Q1, AUTH-Q3, AUTH-Q5, STATE-Q1, STATE-Q5, STATE-Q6, HITL-Q3, DATA-Q1, DATA-Q6, DATA-Q7, OBS-Q1, OBS-Q3 |
| `src/emailservice/email_client.py` | AUTH-Q4 |
| `src/emailservice/logger.py` | AUTH-Q6, DATA-Q6, OBS-Q1, OBS-Q3 |
| `src/emailservice/demo_pb2.py` | API-Q2, API-Q5, DISC-Q1 |
| `src/emailservice/demo_pb2_grpc.py` | API-Q1 |
| `src/emailservice/genproto.sh` | API-Q2 |

### Infrastructure as Code
| File | Questions Referenced |
|------|---------------------|
| `helm-chart/templates/emailservice.yaml` | AUTH-Q1, AUTH-Q2, AUTH-Q7, STATE-Q5, OBS-Q2, ENG-Q1, ENG-Q3 |
| `helm-chart/values.yaml` | AUTH-Q1, AUTH-Q3, OBS-Q1, ENG-Q1 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/ci-pr.yaml` | ENG-Q2, ENG-Q4 |
| `.github/workflows/ci-main.yaml` | ENG-Q2 |
| `skaffold.yaml` | HITL-Q3, ENG-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `src/emailservice/requirements.txt` | OBS-Q1 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `src/emailservice/templates/confirmation.html` | DISC-Q2 |

### Notable Absences — Files Not Found
| Expected Artifact | Impact |
|-------------------|--------|
| OpenAPI/Swagger specification file | API-Q2, DISC-Q1, ENG-Q2 |
| CloudTrail / Cloud Audit Logs configuration | AUTH-Q6 |
| Secrets Manager resources | AUTH-Q5 |
| Data classification documentation | DATA-Q1, DATA-Q2 |
| Test files for emailservice | ENG-Q4 |
| Load test results | STATE-Q7 |
| Alerting configuration | OBS-Q2 |
| Drift detection configuration | ENG-Q1 |

---

*End of Agentic Readiness Analysis Report*