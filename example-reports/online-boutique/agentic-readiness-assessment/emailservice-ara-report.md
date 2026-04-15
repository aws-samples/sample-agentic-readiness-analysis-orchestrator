# Agentic Readiness Assessment Report

**Target**: ./services/microservices-demo/src/emailservice
**Date**: 2026-04-15
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Agent Scope**: read-only
**Priority**: P2
**Tags**: python, grpc, notifications
**Context**: Python gRPC service sending order confirmation emails.

---

## Readiness Profile: Not Agent-Integrable

**BLOCKERs**: 3 | **RISKs**: 36 | **INFOs**: 10

Exclude from agent toolset or plan major remediation before re-evaluation.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 3 |
| RISK | 36 |
| INFO | 10 |
| N/A | 0 |
| **Total** | **49** |

**Questions Evaluated**: 49
**Questions N/A (repo_type: application)**: 0

---

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: The gRPC server in `email_server.py` uses `server.add_insecure_port('[::]:'+port)` — no TLS, no authentication interceptors, no OAuth2 client credentials flow, no API key validation, no mTLS. There is no authentication mechanism of any kind. Any network-reachable client can invoke `SendOrderConfirmation` without presenting credentials.
- **Gap**: No machine identity authentication exists. The service cannot identify which principal (human or agent) is making a call. No audit attribution is possible.
- **Remediation**:
  - **Immediate**: Add a gRPC server interceptor that validates an API key or OAuth2 bearer token on every incoming request. Use `server.add_secure_port()` with TLS certificates to replace `add_insecure_port()`.
  - **Target State**: All gRPC calls are authenticated via mTLS or OAuth2 client credentials flow. The authenticated principal identity is available in server context and logged for every request.
  - **Estimated Effort**: Medium
  - **Dependencies**: ENG-Q6 (network policies) — TLS is a prerequisite for secure authentication. AUTH-Q7 (audit logging) — authentication is required before meaningful audit trails.
- **Evidence**: `email_server.py` (line: `server.add_insecure_port('[::]:'+port)`)

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: The service handles email addresses (PII) via `request.email` and order data including shipping addresses (`street_address`, `city`, `country`, `zip_code`) through the `SendOrderConfirmationRequest` Protobuf message. The `DummyEmailService` logs the email address directly: `'A request to send order confirmation email to {} has been received.'.format(request.email)`. The `confirmation.html` template renders full order details including shipping address. No data classification tags, no field-level encryption, no access controls on PII fields exist anywhere in the codebase.
- **Gap**: Sensitive data (email addresses, shipping addresses) is not classified or tagged at the field level. No controls prevent an agent from retrieving PII without explicit authorization. PII flows through the system unprotected.
- **Remediation**:
  - **Immediate**: Classify the `email` field and `shipping_address` fields as PII in the Protobuf schema documentation. Implement field-level access controls or redaction for agent-facing interfaces.
  - **Target State**: All PII fields are classified and tagged. Access to PII requires explicit authorization. PII is redacted from logs (see also DATA-Q7).
  - **Estimated Effort**: Medium
  - **Dependencies**: AUTH-Q1 (machine identity) — you cannot enforce data access controls without knowing who is calling.
- **Evidence**: `email_server.py` (DummyEmailService.SendOrderConfirmation, EmailService.SendOrderConfirmation), `demo_pb2.py` (SendOrderConfirmationRequest, OrderResult, Address message definitions), `templates/confirmation.html`

### ENG-Q6: Cross-Origin and Network Policies

- **Severity**: BLOCKER
- **Finding**: The gRPC server binds to all interfaces on an insecure port: `server.add_insecure_port('[::]:'+port)`. No TLS is configured. No security group definitions, no network policies, no API gateway settings, no firewall rules, and no WAF configuration exist in this repository. The Dockerfile exposes port 8080 with no network restrictions. There is no IaC defining any network security controls.
- **Gap**: No network security configuration exists. The service is exposed on all interfaces without encryption or access control. No documentation or IaC defines the network topology or security boundaries.
- **Remediation**:
  - **Immediate**: Replace `add_insecure_port` with `add_secure_port` using TLS certificates. Define network policies (Kubernetes NetworkPolicy or security groups) that restrict access to only authorized callers.
  - **Target State**: gRPC server uses TLS. Network policies restrict inbound traffic to known service mesh or API gateway endpoints. All network security is defined as IaC, peer-reviewed, and monitored for drift.
  - **Estimated Effort**: Medium
  - **Dependencies**: AUTH-Q1 (machine identity) — TLS is a prerequisite for authentication. ENG-Q1 (IaC governance) — network policies should be defined as code.
- **Evidence**: `email_server.py` (line: `server.add_insecure_port('[::]:'+port)`), `Dockerfile` (EXPOSE 8080)
## RISKs — Proceed with Compensating Controls

### API-Q1: Documented API Interface

- **Severity**: RISK
- **Finding**: The application exposes a gRPC interface (`hipstershop.EmailService/SendOrderConfirmation`) defined via Protobuf. The interface is structured and typed — not direct database access, file-based exchange, or UI automation. However, the gRPC endpoint is not externally documented beyond the generated Python stubs (`demo_pb2_grpc.py`). The original `.proto` file is referenced externally (`../../protos/demo.proto` via `genproto.sh`) and is not present in this repository.
- **Gap**: While a proper API exists, there is no standalone API documentation for external consumers. The proto source is external to this repo.
- **Compensating Controls**:
  - Provide the `.proto` file alongside this service for agent tool builders to generate client stubs.
  - Create a README documenting the gRPC endpoint, request/response schema, and expected behavior.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Include the `demo.proto` file in this repository and add a service-level README documenting the `SendOrderConfirmation` RPC including request fields, response, error codes, and usage examples.
- **Evidence**: `demo_pb2_grpc.py` (EmailServiceServicer, EmailServiceStub), `genproto.sh` (references `../../protos/demo.proto`)

### API-Q2: Machine-Readable API Specification

- **Severity**: RISK
- **Finding**: The Protobuf-generated files (`demo_pb2.py`, `demo_pb2_grpc.py`) serve as a machine-readable schema for the gRPC interface. The `SendOrderConfirmationRequest` message is fully typed with `email` (string) and `order` (OrderResult). However, the original `.proto` file is not present in this repository — it is compiled from `../../protos/demo.proto` as shown in `genproto.sh`. No OpenAPI, AsyncAPI, or standalone Protobuf spec file is included.
- **Gap**: The machine-readable spec (`.proto` file) is external to this repository. Agent framework integration requires access to the original Protobuf definition, which is not self-contained here.
- **Compensating Controls**:
  - Reference the proto file from the parent repository for agent tool generation.
  - Use gRPC reflection to allow dynamic service discovery at runtime.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Include the `demo.proto` file directly in this repository or enable gRPC server reflection (`grpc_reflection.v1alpha`) so agent frameworks can introspect the service dynamically.
- **Evidence**: `demo_pb2.py`, `demo_pb2_grpc.py`, `genproto.sh`

### API-Q3: Structured Error Responses

- **Severity**: RISK
- **Finding**: The `EmailService.SendOrderConfirmation` method uses `context.set_code(grpc.StatusCode.INTERNAL)` and `context.set_details("An error occurred when preparing the confirmation mail.")` for template errors, and similar patterns for send errors. Error responses are limited to gRPC status codes and free-text detail strings. There is no structured error body, no error code enum, no retryable indicator, and no error category classification.
- **Gap**: Error responses lack structured error codes and machine-readable error bodies. Agents cannot distinguish retryable errors (transient mail server failure) from terminal errors (invalid email address) without parsing free-text strings.
- **Compensating Controls**:
  - Document the known error conditions and their retryability in a service README.
  - Use gRPC rich error model (`google.rpc.Status` with `google.rpc.ErrorInfo`) to provide structured error details.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Adopt the gRPC rich error model. Return structured error details including an application-specific error code, human-readable message, and retryable boolean for each error condition.
- **Evidence**: `email_server.py` (EmailService.SendOrderConfirmation — `context.set_code()`, `context.set_details()`)

### API-Q5: API Versioning and Deprecation

- **Severity**: RISK
- **Finding**: The Protobuf package is `hipstershop` with no version identifier. The service path is `/hipstershop.EmailService/SendOrderConfirmation` — no version segment. No changelog, no deprecation notices, no version annotations exist in the codebase.
- **Gap**: No API versioning strategy. Breaking changes to the Protobuf schema would silently break all consumers, including agent tool definitions.
- **Compensating Controls**:
  - Use Protobuf's built-in backward compatibility rules (additive-only changes) as an implicit versioning strategy.
  - Communicate schema changes through the parent repository's release process.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Adopt a versioned Protobuf package name (e.g., `hipstershop.email.v1`) and establish a deprecation policy that includes notification to downstream consumers before breaking changes.
- **Evidence**: `demo_pb2.py` (package `hipstershop` — no version), `demo_pb2_grpc.py`

### API-Q7: Asynchronous Operation Support

- **Severity**: RISK
- **Finding**: The `SendOrderConfirmation` RPC is synchronous — it renders the email template and sends the email (or logs in dummy mode) within the request handler, then returns `Empty`. No background job framework (Celery, SQS workers), no async/polling patterns, no job status APIs, and no webhook callback endpoints exist.
- **Gap**: No asynchronous operation support. If the email sending operation takes longer than expected (e.g., mail server latency), the gRPC call blocks until completion. No mechanism exists for long-running task handling.
- **Compensating Controls**:
  - The current operation (email sending) is typically fast enough for synchronous handling.
  - If latency increases, consider offloading to an SQS queue with a worker process.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Evaluate whether email sending latency warrants async patterns. If so, implement a message queue (SQS/SNS) for email dispatch with a status query endpoint.
- **Evidence**: `email_server.py` (EmailService.SendOrderConfirmation, DummyEmailService.SendOrderConfirmation — both synchronous)

### AUTH-Q2: Scoped Permissions (Least Privilege)

- **Severity**: RISK
- **Finding**: No IAM policies, role definitions, or permission scoping exist anywhere in the codebase. No IaC defines IAM roles for this service. The service has a single gRPC endpoint with no permission model — any caller can invoke any operation.
- **Gap**: No scoped permissions exist. An agent identity cannot be granted limited access (e.g., read-only) because the service has no authorization model.
- **Compensating Controls**:
  - Enforce scoped permissions at the infrastructure layer (API Gateway policies, Kubernetes NetworkPolicy) until application-level authorization is implemented.
  - Limit which agent identities have network access to this service.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Define IAM roles or API key scopes that restrict agent access to specific operations. Implement at minimum a gRPC interceptor that checks caller permissions.
- **Evidence**: `email_server.py` (no authorization checks in any method)

### AUTH-Q3: Action-Level Authorization

- **Severity**: RISK
- **Finding**: The service exposes a single RPC (`SendOrderConfirmation`) with no authorization middleware, no permission checks, no ABAC or RBAC implementation. The `Check` and `Watch` health endpoints are similarly unprotected.
- **Gap**: No action-level authorization. The service cannot distinguish between an agent that should be allowed to send emails vs. one that should not.
- **Compensating Controls**:
  - Rely on network-level access control to restrict which services can call the email service.
  - Implement action-level checks in a gRPC server interceptor.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add a gRPC server interceptor that validates caller permissions per RPC method. Use metadata headers to carry authorization context.
- **Evidence**: `email_server.py` (BaseEmailService, EmailService, DummyEmailService — no authorization checks)

### AUTH-Q4: Identity Propagation

- **Severity**: RISK
- **Finding**: No JWT parsing middleware, no OAuth2 on-behalf-of flows, no token exchange patterns exist. The service does not read any identity headers from incoming gRPC metadata. The `SendOrderConfirmation` method accesses `request.email` and `request.order` only — no user identity context.
- **Gap**: No identity propagation mechanism. The service cannot determine which end-user's order is being confirmed from an identity perspective — only from the request payload data.
- **Compensating Controls**:
  - Pass user identity as gRPC metadata from the calling service (checkout service) and log it for attribution.
  - Implement JWT validation in a gRPC interceptor.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement gRPC metadata propagation for user identity. Accept a JWT or user ID in metadata headers and validate it in a server interceptor.
- **Evidence**: `email_server.py` (SendOrderConfirmation — no metadata/identity reading)

### AUTH-Q5: Agent-as-Self vs Agent-on-Behalf-of-User

- **Severity**: RISK
- **Finding**: No identity differentiation mechanisms exist. There are no separate IAM roles or API keys for agent-as-self vs. agent-on-behalf-of-user. No audit log fields distinguish the two modes. The service cannot determine if a call comes from an agent acting autonomously or on behalf of a specific user.
- **Gap**: The service cannot distinguish between agent access modes. Both scenarios would appear identical in any future logging.
- **Compensating Controls**:
  - Define separate agent identities (API keys or service accounts) for different access modes at the infrastructure layer.
  - Include an `X-Agent-Mode` metadata header convention in gRPC calls.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Design an identity model that distinguishes agent-as-self from agent-on-behalf-of-user. Implement separate credentials and logging for each mode.
- **Evidence**: `email_server.py` (no identity handling)

### AUTH-Q6: Credential Management

- **Severity**: RISK
- **Finding**: No hardcoded credentials were found in the source code. The service uses environment variables for non-secret configuration: `PORT`, `GCP_PROJECT_ID`, `ENABLE_TRACING`, `COLLECTOR_SERVICE_ADDR`, `DISABLE_PROFILER`. The `EmailService` class (non-dummy) references `project_id`, `region`, `sender_id`, and `from_address` but these are undefined variables — the non-dummy implementation is incomplete and raises an exception in `__init__`. No Secrets Manager, Vault, or secret rotation mechanisms are configured.
- **Gap**: No secrets management system is in place. When the service moves beyond dummy mode, credentials for the mail provider will need to be managed securely. No rotation mechanism exists.
- **Compensating Controls**:
  - The current dummy mode does not require credentials — no immediate secret exposure risk.
  - When real email sending is implemented, use AWS Secrets Manager or Vault from the start.
- **Remediation Timeline**: 30–60 days (before non-dummy implementation)
- **Recommendation**: Implement AWS Secrets Manager integration for mail provider credentials before enabling non-dummy mode. Ensure secrets are not passed as environment variables.
- **Evidence**: `email_server.py` (EmailService.__init__, environment variable usage), `Dockerfile` (ENV variables)

### AUTH-Q7: Immutable Audit Logging ⚡

- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: JSON structured logging is implemented via `logger.py` using `pythonjsonlogger` with `timestamp` and `severity` fields. The `DummyEmailService` logs email send requests. However, logs do not include the authenticated principal (because no authentication exists — AUTH-Q1). No CloudTrail configuration, no immutable log storage (S3 with object lock), no log file validation. Logs are written to stdout and would be captured by container orchestration, but immutability is not guaranteed.
- **Gap**: No immutable audit logging. Logs lack principal attribution (who made the call), and there is no tamper-evident storage. Write operations (sending emails) are not auditable to a specific agent or user identity.
- **Compensating Controls**:
  - Route container stdout logs to a centralized logging service with retention policies.
  - Add request metadata to log entries for partial attribution.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: After implementing authentication (AUTH-Q1), add the authenticated principal to every log entry. Ship logs to an immutable store (S3 with object lock or CloudWatch Logs with retention policy).
- **Evidence**: `logger.py` (CustomJsonFormatter — timestamp and severity only), `email_server.py` (DummyEmailService logging)

### AUTH-Q8: Agent Identity Suspension

- **Severity**: RISK
- **Finding**: No API key revocation endpoints, no IAM role deactivation procedures, no service account disable mechanisms exist. Because no authentication exists (AUTH-Q1), there is no identity to suspend. There is no kill-switch mechanism to stop a specific agent from calling the service.
- **Gap**: No agent identity suspension capability. A misbehaving agent cannot be individually isolated without taking down the entire service or blocking at the network level.
- **Compensating Controls**:
  - Use network-level controls (Kubernetes NetworkPolicy, security group rules) to block a specific agent's IP or pod.
  - Implement a deny-list in a gRPC interceptor for rapid agent suspension.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: After implementing authentication (AUTH-Q1), add an agent identity suspension mechanism — either API key revocation, token blocklist, or IAM role deactivation.
- **Evidence**: `email_server.py` (no identity management)
### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: The service is a single-step operation — it receives a request, renders an email template, and sends the email. There is no multi-step workflow, no saga pattern, no two-phase commit, no explicit undo endpoints, and no Step Functions integration. Once an email is sent, it cannot be recalled.
- **Gap**: No compensation or rollback mechanism. Email sending is an irreversible operation. If an agent triggers email sends as part of a multi-step workflow and a later step fails, sent emails cannot be undone.
- **Compensating Controls**:
  - For read-only agent scope, this is less critical since agents would not directly trigger email sends.
  - Implement a "draft email" pattern where emails are queued but not sent until confirmed.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Consider implementing a two-phase approach: queue emails in a pending state, then confirm/send after upstream workflow completion.
- **Evidence**: `email_server.py` (single-step SendOrderConfirmation — no rollback logic)

### STATE-Q2: Queryable Current State

- **Severity**: RISK
- **Finding**: The service is entirely stateless. The `SendOrderConfirmation` RPC receives a request, processes it, and returns `Empty`. There are no GET endpoints, no status query APIs, and no persistent state to query. An agent cannot inspect whether an email has been sent for a given order.
- **Gap**: No queryable state. Agents cannot determine the current state of email delivery for a given order before deciding whether to re-trigger a send.
- **Compensating Controls**:
  - Track email send status in an external data store and expose a query endpoint.
  - Use distributed tracing (OBS-Q1) to verify past email sends.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add a lightweight state store (DynamoDB or Redis) tracking email send status per order ID. Expose a `GetEmailStatus` RPC for agents to query before deciding on actions.
- **Evidence**: `email_server.py` (no state storage, no query endpoints), `demo_pb2_grpc.py` (only SendOrderConfirmation RPC defined)

### STATE-Q3: Concurrency Controls

- **Severity**: RISK
- **Finding**: No optimistic locking, no ETags, no version fields, no conditional writes. The service is stateless — concurrent calls to `SendOrderConfirmation` with the same order would independently send duplicate emails. The `ThreadPoolExecutor(max_workers=10)` allows 10 concurrent requests but provides no deduplication.
- **Gap**: No concurrency controls. Multiple agent instances calling simultaneously could result in duplicate email sends for the same order.
- **Compensating Controls**:
  - Implement idempotency at the application level using order_id as a deduplication key.
  - Use a distributed lock (Redis, DynamoDB conditional write) before sending.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add an idempotency layer that tracks `order_id` to prevent duplicate email sends within a configurable time window.
- **Evidence**: `email_server.py` (no deduplication logic, `ThreadPoolExecutor(max_workers=10)`)

### STATE-Q4: Circuit Breakers and Resilience

- **Severity**: RISK
- **Finding**: No resilience libraries (Resilience4j, Polly, retry decorators), no exponential backoff, no circuit breaker annotations, and no timeout configurations on outbound calls. The `EmailService.send_email` method calls the mail API directly with no retry or circuit breaker logic. The `DummyEmailService` has no external dependencies. No `try/except` with retry logic exists for transient failures.
- **Gap**: No circuit breakers or resilience patterns. If the mail provider is down, the service will fail every request without self-protecting or providing graceful degradation.
- **Compensating Controls**:
  - The current dummy mode has no external dependencies, so no immediate resilience risk.
  - Add retry with exponential backoff for the mail provider call when implementing non-dummy mode.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement circuit breakers and retry with exponential backoff for the mail provider API call. Add timeout configuration on all outbound HTTP/gRPC calls.
- **Evidence**: `email_server.py` (EmailService.send_email — no retry/circuit breaker), `requirements.txt` (no resilience libraries)

### STATE-Q5: Rate Limiting and Throttling

- **Severity**: RISK
- **Finding**: No API Gateway throttling configuration, no WAF rate rules, no application-level rate limiting middleware. The gRPC server accepts requests up to its `ThreadPoolExecutor(max_workers=10)` concurrency limit but has no explicit rate limiting. No `aws_api_gateway_usage_plan` or equivalent configuration exists.
- **Gap**: No rate limiting. A runaway agent loop could send unlimited email requests at machine speed, potentially overwhelming the mail provider and the service itself.
- **Compensating Controls**:
  - The `max_workers=10` in ThreadPoolExecutor provides an implicit concurrency cap, but this is not rate limiting.
  - Add application-level rate limiting using a gRPC interceptor with token bucket or sliding window algorithm.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement rate limiting at the gRPC server level via a server interceptor. Define per-caller rate limits based on agent identity (after AUTH-Q1 is resolved).
- **Evidence**: `email_server.py` (`ThreadPoolExecutor(max_workers=10)` — implicit concurrency cap only)

### STATE-Q6: Blast Radius and Transaction Limits

- **Severity**: RISK
- **Finding**: No configurable limits on agent-initiated actions. No maximum emails per hour, no maximum recipients per session, no spend limits. The service will process every request it receives without business-level guardrails.
- **Gap**: No blast radius controls. An agent error could trigger thousands of confirmation emails in a loop with no automatic cutoff.
- **Compensating Controls**:
  - Implement a per-agent email send quota tracked in a shared data store.
  - Add a circuit breaker that trips after N emails within a time window.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add configurable transaction limits: `max_emails_per_hour`, `max_emails_per_order_id`. Enforce per-agent identity after authentication is implemented (AUTH-Q1).
- **Evidence**: `email_server.py` (no transaction limits)

### STATE-Q7: Infrastructure Capacity for Agent Traffic

- **Severity**: RISK
- **Finding**: The gRPC server uses a fixed `ThreadPoolExecutor(max_workers=10)` — handling at most 10 concurrent requests. The Dockerfile defines no resource limits (no `--memory`, no `--cpus`). No load test results, no auto-scaling policies, no capacity planning documentation exist. The service is designed for human-paced traffic from the checkout flow, not agent-speed traffic patterns.
- **Gap**: Infrastructure is not sized or tested for agent traffic. The fixed 10-worker thread pool would be exhausted quickly under agent-generated load, causing request queuing or rejection.
- **Compensating Controls**:
  - Run load tests to establish baseline capacity and breaking points.
  - Configure Kubernetes resource limits and HPA (Horizontal Pod Autoscaler) for the deployment.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Conduct load testing with agent-simulated traffic patterns. Increase `max_workers` or implement async processing. Define Kubernetes resource limits and autoscaling policies.
- **Evidence**: `email_server.py` (`ThreadPoolExecutor(max_workers=10)`), `Dockerfile` (no resource limits)

### HITL-Q1: Draft/Pending State

- **Severity**: RISK
- **Finding**: No draft or pending state concept exists. The `SendOrderConfirmation` RPC immediately sends the email (or logs in dummy mode). There is no two-step commit pattern, no approval workflow, no status field for "pending" or "draft". The response is `Empty` — there is no way to create a pending email and confirm it later.
- **Gap**: No draft/pending state. Agents cannot propose an email send for human review before committing.
- **Compensating Controls**:
  - Implement approval gates at the agent orchestration layer rather than in this service.
  - Add a `CreateDraftConfirmation` RPC that stores the email without sending.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add a two-phase email flow: `CreateDraftConfirmation` (returns a draft ID) followed by `ConfirmSend` (actually sends). This enables human approval between steps.
- **Evidence**: `email_server.py` (SendOrderConfirmation — immediate execution), `demo_pb2_grpc.py` (single RPC defined)

### HITL-Q2: Configurable Approval Gates

- **Severity**: RISK
- **Finding**: No approval mechanism, no human-in-the-loop gates, no configurable operation-level flags. The service has one operation (`SendOrderConfirmation`) that executes immediately with no approval step. No Step Functions with `waitForTaskToken` or equivalent pattern exists.
- **Gap**: No configurable approval gates. High-risk operations (e.g., sending emails to large recipient lists) cannot be gated for human approval.
- **Compensating Controls**:
  - Implement approval gates at the agent orchestration layer (e.g., in the agent framework or Step Functions).
  - Add a metadata flag in gRPC headers to indicate whether the request requires approval.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Integrate with an approval workflow system (Step Functions, or a lightweight approval queue) for operations above a configurable threshold.
- **Evidence**: `email_server.py` (no approval logic)

### HITL-Q3: Sandbox/Staging Environment

- **Severity**: RISK
- **Finding**: The service runs in "dummy mode" by default (`start(dummy_mode = True)`) where `DummyEmailService` logs email requests instead of sending them. This provides a built-in sandbox behavior for testing without sending real emails. However, there is no separate staging environment configuration, no docker-compose for local testing with dependencies, no seed data scripts, and no synthetic data generators. The non-dummy `EmailService` is unimplemented (raises exception in `__init__`).
- **Gap**: While dummy mode provides basic sandbox capability, there is no production-equivalent staging environment with realistic data shapes or multi-service testing capability.
- **Compensating Controls**:
  - Use dummy mode as a testing sandbox for agent integration testing.
  - Create a docker-compose file that spins up the email service with mock upstream services.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a docker-compose configuration for local multi-service testing. Add seed data scripts that provide realistic order data for agent testing against dummy mode.
- **Evidence**: `email_server.py` (`start(dummy_mode = True)`, `DummyEmailService` class)

### DATA-Q2: Data Residency and Sovereignty ⚡

- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: No data residency configuration, no GDPR/LGPD compliance references, no region-specific data storage configurations exist. The service processes transient data (email addresses, shipping addresses, order details) but does not persist it. The email address and order details pass through the service to the mail provider. No cross-region replication settings or data sovereignty policies are documented.
- **Gap**: No data residency controls or documentation. If an agent sends order data (containing PII) to an LLM endpoint in a different jurisdiction, this could create compliance exposure. The service has no controls preventing cross-region data transmission.
- **Compensating Controls**:
  - Document the data flow path and ensure the mail provider endpoint is in the same region as the deployment.
  - Configure agent orchestration to redact PII before sending to LLM endpoints.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document data residency requirements for this service. Implement data flow controls that prevent PII from being transmitted to LLM endpoints outside the deployment region.
- **Evidence**: `email_server.py` (transient data processing — no residency controls), `demo_pb2.py` (PII fields in message definitions)

### DATA-Q3: Selective Query Support

- **Severity**: RISK
- **Finding**: The gRPC interface accepts `SendOrderConfirmationRequest` (email string + OrderResult) and returns `Empty`. This is a command endpoint, not a query endpoint. No pagination parameters, no filter query parameters, no sorting options, no field selection, and no result size limits exist. The service does not expose any data retrieval APIs.
- **Gap**: No selective query support. The service is write-only (send email) — agents cannot query email status, filter by criteria, or paginate results.
- **Compensating Controls**:
  - If agents need to query email status, track it externally in a data store with query APIs.
  - The lack of query endpoints limits agent interaction to triggering email sends only.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add query endpoints (`GetEmailStatus`, `ListEmailsByOrder`) with pagination and filtering if agents need to inspect email delivery state.
- **Evidence**: `demo_pb2_grpc.py` (only SendOrderConfirmation defined), `demo_pb2.py` (SendOrderConfirmationRequest, Empty)

### DATA-Q4: System of Record Designations

- **Severity**: RISK
- **Finding**: No master data management references, no system-of-record designations, no data ownership definitions exist. The email service consumes order data from the upstream checkout service but there is no documentation of which service is the system of record for order data, email addresses, or shipping information.
- **Gap**: No system-of-record designations. An agent querying multiple services in this microservice architecture may encounter conflicting data with no clear authority.
- **Compensating Controls**:
  - Document the data ownership model at the platform level (checkout service owns order data, email service is a consumer).
  - Implement data validation at the service boundary.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document the data ownership model. Designate the checkout service as the system of record for order data and email addresses. The email service should be documented as a downstream consumer.
- **Evidence**: `email_server.py` (consumes order data from request — no ownership documentation)

### DATA-Q5: Reliable Timestamps

- **Severity**: RISK
- **Finding**: The `logger.py` CustomJsonFormatter adds timestamps via `record.created` (Python logging timestamp as a Unix epoch float). The Protobuf messages do not include timestamp fields — `OrderResult` has `order_id`, `shipping_tracking_id`, `shipping_cost`, `shipping_address`, and `items` but no `created_at`, `updated_at`, or `event_time` fields. No timezone handling or NTP configuration exists.
- **Gap**: No reliable timestamps on business data. The order data passed to this service has no temporal fields. Only log entries have timestamps, and these use Python's local `record.created` without explicit UTC normalization.
- **Compensating Controls**:
  - Rely on log timestamps for debugging and tracing.
  - Add timestamp fields to the Protobuf schema for order events.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `created_at` and `event_time` fields (as `google.protobuf.Timestamp`) to the `SendOrderConfirmationRequest` message. Normalize all timestamps to UTC.
- **Evidence**: `logger.py` (record.created), `demo_pb2.py` (OrderResult — no timestamp fields)

### DATA-Q6: Data Freshness Signaling

- **Severity**: RISK
- **Finding**: The gRPC service returns `Empty` responses with no metadata. No `Cache-Control` headers, no `X-Data-Age` headers, no `last_refreshed` field, no consistency level indicators. The service processes transient data — freshness signaling is not applicable to the response but is relevant to the input data (order data may be stale by the time email is triggered).
- **Gap**: No data freshness signaling. An agent cannot determine if the order data it provides is current or stale before triggering an email send.
- **Compensating Controls**:
  - Include a `data_retrieved_at` timestamp in the request metadata from the calling agent.
  - Validate order data freshness against a configurable threshold before processing.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Accept a `data_freshness` metadata field in gRPC headers. Reject requests where order data is older than a configurable threshold (e.g., 1 hour).
- **Evidence**: `email_server.py` (returns `demo_pb2.Empty()` — no metadata), `demo_pb2.py` (Empty message)

### DATA-Q7: PII Redaction in Logs

- **Severity**: RISK
- **Finding**: The `DummyEmailService.SendOrderConfirmation` logs the email address directly: `logger.info('A request to send order confirmation email to {} has been received.'.format(request.email))`. This writes PII (email addresses) into structured JSON logs without any redaction or masking. No log scrubbing middleware, no PII masking libraries, and no CloudWatch log filters exist.
- **Gap**: PII (email addresses) is logged in plaintext. If logs are shipped to centralized logging systems, LLM prompt/response pairs, or observability platforms, email addresses are exposed.
- **Compensating Controls**:
  - Implement a log filter that masks email addresses (e.g., `j***@example.com`).
  - Add PII detection rules in the log aggregation layer (CloudWatch Logs data protection).
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Replace `request.email` in log messages with a masked version. Implement a PII redaction utility that masks email addresses and other PII fields before logging.
- **Evidence**: `email_server.py` (line: `logger.info('A request to send order confirmation email to {} has been received.'.format(request.email))`)

### DISC-Q1: Schema Documentation and Versioning

- **Severity**: RISK
- **Finding**: The Protobuf definitions in `demo_pb2.py` define the schema — `SendOrderConfirmationRequest` with `email` (string) and `order` (OrderResult containing `order_id`, `shipping_tracking_id`, `shipping_cost`, `shipping_address`, and `items`). The schema is compiled from an external `.proto` file (`../../protos/demo.proto`). There is no schema versioning — no version field in the Protobuf package, no changelog, no schema registry.
- **Gap**: Schema is defined but not independently versioned. Changes to the `.proto` file are not tracked with version numbers or changelogs within this repository.
- **Compensating Controls**:
  - Use Protobuf backward compatibility rules to prevent breaking changes.
  - Track proto schema changes in the parent repository's version control.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add schema versioning to the Protobuf package. Maintain a CHANGELOG documenting schema evolution. Consider a schema registry for runtime validation.
- **Evidence**: `demo_pb2.py` (compiled Protobuf — no version), `genproto.sh` (references external proto)

### OBS-Q1: Distributed Tracing and Structured Logging

- **Severity**: RISK
- **Finding**: The service has OpenTelemetry instrumentation: `TracerProvider`, `BatchSpanProcessor`, `OTLPSpanExporter`, and `GrpcInstrumentorServer` in `email_server.py`. Tracing is conditional on `ENABLE_TRACING=1` environment variable and exports to `COLLECTOR_SERVICE_ADDR` (default `localhost:4317`). JSON structured logging is implemented via `logger.py` using `pythonjsonlogger` with `timestamp` and `severity` fields. However, logs do not include `trace_id`, `correlation_id`, or `request_id` fields. The gRPC instrumentor propagates trace context in spans but this context is not correlated with log entries.
- **Gap**: Distributed tracing exists but is optional (env-var gated) and disconnected from structured logs. Logs lack trace correlation IDs, making it difficult to link a log entry to its corresponding trace span.
- **Compensating Controls**:
  - Enable tracing by default in production deployments (set `ENABLE_TRACING=1`).
  - Add OpenTelemetry log instrumentation to inject trace_id into log records.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Inject `trace_id` and `span_id` from the OpenTelemetry context into the JSON log formatter. Enable tracing by default rather than requiring an environment variable opt-in.
- **Evidence**: `email_server.py` (OpenTelemetry setup, `ENABLE_TRACING` check), `logger.py` (CustomJsonFormatter — no trace_id field), `requirements.txt` (opentelemetry-* packages)

### OBS-Q2: Alerting on Error Rates and Latency

- **Severity**: RISK
- **Finding**: No CloudWatch alarms, no alerting configuration, no anomaly detection, no PagerDuty/OpsGenie integration found in the codebase. No composite alarms or SLO-based alerting. The service emits traces (when enabled) and logs, but no alerting thresholds are defined for error rates or latency on the `SendOrderConfirmation` RPC.
- **Gap**: No alerting configured. Target system degradation (e.g., mail provider failures, increased latency) would not trigger alerts. Agents would experience failures without operators being notified.
- **Compensating Controls**:
  - Configure alerting in the deployment infrastructure (CloudWatch alarms on error rate and P95 latency from OpenTelemetry metrics).
  - Set up basic log-based alerting on gRPC error status codes.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Define CloudWatch alarms or equivalent monitoring for: error rate > 1% on SendOrderConfirmation, P95 latency > 2 seconds. Integrate with PagerDuty or OpsGenie for on-call notification.
- **Evidence**: No alerting configuration found in any file. `email_server.py` (no metrics/alerting), `requirements.txt` (no alerting libraries)

### ENG-Q1: Infrastructure Governance for Agent-Facing Surface

- **Severity**: RISK
- **Finding**: No IaC files found in this repository — no Terraform, CloudFormation, CDK, Helm charts, or Kustomize definitions. The infrastructure that would expose this service to agents (API gateways, IAM roles, secrets, network configurations) is not defined as code in this repository. No drift detection configuration exists.
- **Gap**: The agent-facing integration surface is not governed as code within this repository. Infrastructure changes are not subject to peer review or drift detection within this service's scope.
- **Compensating Controls**:
  - Infrastructure may be defined in a separate IaC repository — verify and document the dependency.
  - Add at minimum a Kubernetes deployment manifest with resource limits and network policies.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Define the service's deployment infrastructure as code (Kubernetes manifests, Helm chart, or Terraform) within this repository or document the external IaC dependency. Enable drift detection.
- **Evidence**: No IaC files found. `Dockerfile` (only container build definition)

### ENG-Q2: CI/CD with API Contract Testing

- **Severity**: RISK
- **Finding**: No CI/CD pipeline definitions found — no GitHub Actions, no GitLab CI, no Jenkinsfile, no `buildspec.yml`. No API contract tests, no Pact consumer-driven testing, no OpenAPI spec validation, no Protobuf schema comparison tools. The repository contains no pipeline configuration of any kind.
- **Gap**: No CI/CD pipeline and no API contract testing. Changes to the Protobuf schema or service implementation could break agent-facing APIs without detection before production.
- **Compensating Controls**:
  - CI/CD may be defined at the monorepo level — verify and document.
  - Add at minimum a Protobuf backward compatibility check (e.g., `buf breaking`) in the build pipeline.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a CI/CD pipeline with: (1) Protobuf schema backward compatibility validation, (2) unit tests for the gRPC service, (3) contract tests validating the SendOrderConfirmation RPC behavior.
- **Evidence**: No CI/CD files found in repository.

### ENG-Q3: Rollback Capability

- **Severity**: RISK
- **Finding**: No deployment configuration exists — no blue/green deployment config, no CodeDeploy rollback triggers, no Helm rollback, no feature flags, no canary deployment with automatic rollback. The Dockerfile defines the image build but no deployment strategy. No traffic shifting configuration at API Gateway or ALB level.
- **Gap**: No rollback capability defined in this repository. If a deployment breaks the `SendOrderConfirmation` RPC, there is no documented mechanism to roll back to the previous known-good state.
- **Compensating Controls**:
  - Rollback may be handled at the orchestration level (Kubernetes rollout undo, ArgoCD).
  - Tag Docker images with version numbers to enable manual rollback.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Define a deployment strategy with automatic rollback triggers. Use Kubernetes rolling updates with health check-based rollback or implement blue/green deployment.
- **Evidence**: `Dockerfile` (image build only — no deployment strategy)

### ENG-Q4: API Test Coverage

- **Severity**: RISK
- **Finding**: No test files found anywhere in the repository. No `test_*.py`, no `*_test.py`, no `tests/` directory, no pytest configuration, no unittest files. No Postman/Newman collections, no integration tests, no contract tests. The `requirements.txt` does not include any test frameworks (pytest, unittest, mock, grpcio-testing).
- **Gap**: Zero test coverage. The `SendOrderConfirmation` RPC has no automated tests validating input handling, output format, error responses, or edge cases.
- **Compensating Controls**:
  - Add basic smoke tests using the `email_client.py` as a starting point.
  - Implement gRPC service tests using `grpcio-testing` library.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add comprehensive test coverage: (1) unit tests for `SendOrderConfirmation` with valid/invalid inputs, (2) error handling tests for template errors and send failures, (3) integration tests using `grpcio-testing`. Target >80% coverage.
- **Evidence**: No test files found. `requirements.txt` (no test framework dependencies). `email_client.py` (manual test client only)

### ENG-Q5: Encryption at Rest for Agent-Accessible Data

- **Severity**: RISK
- **Finding**: No KMS configuration, no encryption-at-rest settings exist. The service is stateless — it does not persist data to disk, database, or S3. However, there is no encryption configuration for log data that may contain PII (see DATA-Q7), and no guidance on encryption for any future persistent state.
- **Gap**: While the service is stateless (no data at rest), logs containing PII are written to stdout without encryption guarantees. No encryption-at-rest controls are defined for the container's filesystem or any transient data.
- **Compensating Controls**:
  - Ensure the container orchestration platform encrypts log storage at rest.
  - When the service adds persistent state, use KMS-encrypted storage from the start.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document the stateless architecture and confirm that log storage in the deployment environment uses encryption at rest (e.g., CloudWatch Logs with KMS, or encrypted EBS for container hosts).
- **Evidence**: No encryption configuration found. `email_server.py` (stateless processing), `Dockerfile` (no encryption settings)

---

## INFOs — Architecture and Design Inputs

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The `SendOrderConfirmation` RPC is a write operation (sends an email) with no idempotency key support. Calling the same RPC twice with the same order data would send two emails. The `DummyEmailService` would log two separate entries. There is no deduplication mechanism based on `order_id` or any other key.
- **Implication**: For the current read-only agent scope, this is informational. If the agent scope is later expanded to write-enabled, idempotency becomes a BLOCKER — agents retry on failure and LLM non-determinism can cause duplicate tool calls, leading to duplicate email sends.
- **Recommendation**: Before expanding to write-enabled agent scope, implement idempotency using `order_id` as a deduplication key with a time-based dedup window (e.g., 24 hours). Track sent emails in a lightweight store.
- **Evidence**: `email_server.py` (SendOrderConfirmation — no idempotency key), `demo_pb2.py` (SendOrderConfirmationRequest — no idempotency_key field)

### API-Q6: Structured Response Format

- **Severity**: INFO
- **Finding**: The service uses Protobuf (binary) for request/response serialization. The response is `Empty` (no data). The request accepts `SendOrderConfirmationRequest` with typed fields. Protobuf is a structured, strongly-typed binary format — not directly consumable by LLMs but excellent for machine-to-machine integration. gRPC client libraries handle serialization/deserialization transparently.
- **Implication**: Protobuf/gRPC is well-suited for agent tool integration through generated client stubs. Agent frameworks that generate tools from API specs can work with Protobuf definitions. The binary format does not pose an issue for agents using gRPC client libraries.
- **Recommendation**: No action required. Protobuf is a suitable format for agent integration. Ensure the `.proto` file is accessible for client stub generation.
- **Evidence**: `demo_pb2.py` (Protobuf message definitions), `demo_pb2_grpc.py` (gRPC service stubs)

### API-Q8: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: No webhook endpoints, no SNS/EventBridge/SQS integration, no Kafka topics, no CDC pipelines. The service does not emit events when an email is sent. The only output is the gRPC response (`Empty`) and log entries.
- **Implication**: Proactive agent patterns (reacting to email send events) are not possible with this service. Agents would need to poll or rely on upstream events (e.g., order placed events from the checkout service) rather than email-sent events.
- **Recommendation**: Consider emitting an "email_sent" event to SNS or EventBridge when an email is successfully dispatched. This enables downstream agents to react to email delivery status.
- **Evidence**: `email_server.py` (no event emission code)

### API-Q9: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limits are documented. No API Gateway throttle settings, no WAF rate rules, no rate limiting middleware. The gRPC server does not return rate limit headers (`X-RateLimit-Remaining`, `Retry-After` are HTTP concepts — gRPC uses metadata for equivalent functionality). No gRPC metadata with rate limit information is returned.
- **Implication**: Agents calling this service at machine speed have no signal to self-throttle. Without rate limit awareness, agents may overwhelm the service. This is currently INFO because the service has no published rate limits — STATE-Q5 covers the enforcement gap as a RISK.
- **Recommendation**: Define and document rate limits for the `SendOrderConfirmation` RPC. Return rate limit information in gRPC response metadata (e.g., `x-ratelimit-remaining`, `retry-after`).
- **Evidence**: `email_server.py` (no rate limit configuration or metadata)

### API-Q10: API Latency Profile

- **Severity**: INFO
- **Finding**: No performance benchmarks, load test results, CloudWatch latency metrics, or APM dashboards exist. The `DummyEmailService` is a simple log-and-return operation (sub-millisecond). The real `EmailService` (unimplemented) would depend on mail provider latency. No P95 response time data is available.
- **Implication**: Without latency profiles, agent orchestration cannot determine whether to use synchronous or asynchronous patterns. The dummy mode is effectively instant, but production email sending latency is unknown.
- **Recommendation**: Conduct load testing when non-dummy mode is implemented. Establish P95 latency baselines. If P95 exceeds 2 seconds, implement async patterns (see API-Q7).
- **Evidence**: `email_server.py` (DummyEmailService — trivial latency; EmailService — unimplemented)

### DATA-Q8: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality dashboards, data profiling reports, null rate monitoring, duplicate detection logic, data freshness SLAs, or data quality metrics exist. The service accepts whatever data is passed in the `SendOrderConfirmationRequest` with no validation of data quality or completeness.
- **Implication**: Agents acting on incomplete order data (e.g., missing email address, empty order items) would trigger email sends with malformed content. No quality gate prevents bad data from reaching email rendering.
- **Recommendation**: Add input validation for required fields (`email` must be non-empty and valid format, `order` must have at least one item). Log data quality issues (missing fields, invalid formats) for monitoring.
- **Evidence**: `email_server.py` (no input validation), `demo_pb2.py` (no field constraints in Protobuf)

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Protobuf field names are semantically meaningful and human-readable: `email`, `order`, `order_id`, `shipping_tracking_id`, `shipping_cost`, `shipping_address`, `street_address`, `city`, `country`, `zip_code`, `product_id`, `quantity`, `currency_code`, `units`, `nanos`. No legacy abbreviations or cryptic codes. The `confirmation.html` template uses the same clear field names.
- **Implication**: Good field naming supports LLM-based reasoning and agent tool generation. No data dictionary is needed to interpret field semantics.
- **Recommendation**: Maintain the current naming conventions. Document the semantic meaning of less obvious fields (e.g., `nanos` represents fractional currency units in billionths).
- **Evidence**: `demo_pb2.py` (message field definitions), `templates/confirmation.html` (template field references)

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No data catalog (AWS Glue Data Catalog, Collibra, Alation, DataHub), no metadata files, no data dictionaries, and no API catalogs exist. The service's data model is defined only in the compiled Protobuf definitions.
- **Implication**: Agent tool builders must reverse-engineer the data model from Protobuf definitions rather than discovering it through a catalog. This slows initial tool development but is manageable for a single-endpoint service.
- **Recommendation**: Add a data model section to the service README documenting the `SendOrderConfirmationRequest` and `OrderResult` message structures with field descriptions and examples.
- **Evidence**: `demo_pb2.py` (data model defined in compiled Protobuf only)

### DISC-Q4: Data Lineage

- **Severity**: INFO
- **Finding**: No data lineage tools (AWS Glue DataBrew, Apache Atlas), no ETL pipeline documentation, no data flow diagrams, no transformation logs, and no source-to-target mappings. The `genproto.sh` script shows the Protobuf source is `../../protos/demo.proto`, but there is no documentation of how order data flows from checkout service → email service → mail provider.
- **Implication**: When an agent produces incorrect output due to bad order data in an email, there is no lineage to trace whether the issue originated in the checkout service, cart service, or product catalog.
- **Recommendation**: Document the data flow: checkout service → email service (gRPC) → mail provider (API). Include a simple data flow diagram in the service README.
- **Evidence**: `genproto.sh` (proto source reference), `email_server.py` (data flow: request → template → email)

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No custom business metrics, no `cloudwatch.put_metric_data` calls, no business KPI tracking. The service logs basic operational messages ("listening on port", "A request to send order confirmation email") but does not track business outcomes such as email delivery success rate, bounce rate, or customer confirmation open rate.
- **Implication**: When agents consume this service, business metrics become the primary signal for whether agent-triggered emails produce good outcomes. Without them, the only signal is "did the gRPC call succeed" — not "did the email reach the customer."
- **Recommendation**: Add custom metrics: `emails_sent_total`, `emails_failed_total`, `email_delivery_latency_p95`. Publish to CloudWatch or Prometheus for dashboard and alerting integration.
- **Evidence**: `email_server.py` (no business metrics), `logger.py` (operational logging only)
## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: RISK
- **Finding**: The application exposes a gRPC interface (`hipstershop.EmailService/SendOrderConfirmation`) defined via Protobuf. The interface is structured and typed — not direct database access, file-based exchange, or UI automation. However, the gRPC endpoint is not externally documented beyond generated Python stubs. The original `.proto` file is external to this repository (`../../protos/demo.proto`).
- **Gap**: Proper API exists but lacks standalone documentation for external consumers. The proto source file is not self-contained in this repository.
- **Recommendation**: Include the `demo.proto` file in this repository and add API documentation (README with RPC descriptions, request/response examples, and error codes).
- **Evidence**: `demo_pb2_grpc.py`, `genproto.sh`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK
- **Finding**: Protobuf-generated files (`demo_pb2.py`, `demo_pb2_grpc.py`) provide a machine-readable schema. The original `.proto` file is not included — it must be compiled from `../../protos/demo.proto`. No OpenAPI, AsyncAPI, or standalone spec file is present.
- **Gap**: Machine-readable spec is external to this repository. Agent frameworks cannot self-discover the API from this repo alone.
- **Recommendation**: Include the `.proto` file directly or enable gRPC server reflection (`grpc_reflection.v1alpha`) for dynamic introspection.
- **Evidence**: `demo_pb2.py`, `demo_pb2_grpc.py`, `genproto.sh`

#### API-Q3: Structured Error Responses
- **Severity**: RISK
- **Finding**: Error handling uses `context.set_code(grpc.StatusCode.INTERNAL)` and `context.set_details()` with free-text messages. No structured error body, no error code enum, no retryable indicator.
- **Gap**: Agents cannot programmatically distinguish retryable from terminal errors.
- **Recommendation**: Adopt gRPC rich error model with `google.rpc.ErrorInfo` containing application error code, message, and retryable boolean.
- **Evidence**: `email_server.py` (EmailService.SendOrderConfirmation)

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: `SendOrderConfirmation` is a write operation with no idempotency key. Duplicate calls send duplicate emails. No deduplication mechanism exists.
- **Gap**: Non-idempotent write endpoint. Informational for read-only scope.
- **Recommendation**: Implement idempotency using `order_id` before expanding to write-enabled agent scope.
- **Evidence**: `email_server.py`, `demo_pb2.py`

#### API-Q5: API Versioning and Deprecation
- **Severity**: RISK
- **Finding**: Protobuf package `hipstershop` has no version identifier. Service path `/hipstershop.EmailService/SendOrderConfirmation` has no version segment. No changelog or deprecation policy.
- **Gap**: No versioning strategy. Schema changes break consumers silently.
- **Recommendation**: Adopt versioned Protobuf package name (e.g., `hipstershop.email.v1`) and establish a deprecation policy.
- **Evidence**: `demo_pb2.py`, `demo_pb2_grpc.py`

#### API-Q6: Structured Response Format
- **Severity**: INFO
- **Finding**: Protobuf (binary, structured, typed) for request/response. Response is `Empty`. Request uses fully typed `SendOrderConfirmationRequest`.
- **Gap**: N/A — Protobuf is a well-structured format suitable for agent integration.
- **Recommendation**: No action required. Ensure `.proto` file is accessible for client stub generation.
- **Evidence**: `demo_pb2.py`, `demo_pb2_grpc.py`

#### API-Q7: Asynchronous Operation Support
- **Severity**: RISK
- **Finding**: `SendOrderConfirmation` is synchronous. No background job framework, no polling endpoints, no webhook callbacks.
- **Gap**: No async support for potentially long-running email send operations.
- **Recommendation**: Evaluate mail send latency; implement message queue (SQS) for dispatch if needed.
- **Evidence**: `email_server.py`

#### API-Q8: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: No webhook endpoints, no SNS/EventBridge/SQS integration, no Kafka topics. No events emitted on email send.
- **Gap**: No event emission for proactive agent patterns.
- **Recommendation**: Consider emitting `email_sent` events to SNS or EventBridge.
- **Evidence**: `email_server.py`

#### API-Q9: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limits documented. No rate limit headers or gRPC metadata returned. No API Gateway or WAF configuration.
- **Gap**: Agents have no signal to self-throttle.
- **Recommendation**: Define and document rate limits; return rate limit info in gRPC response metadata.
- **Evidence**: `email_server.py`

#### API-Q10: API Latency Profile
- **Severity**: INFO
- **Finding**: No performance benchmarks or latency metrics. DummyEmailService is sub-millisecond. Real EmailService is unimplemented.
- **Gap**: No latency data available for agent orchestration planning.
- **Recommendation**: Establish P95 latency baselines when non-dummy mode is implemented.
- **Evidence**: `email_server.py`
### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: The gRPC server uses `server.add_insecure_port('[::]:'+port)` — no TLS, no auth interceptors, no OAuth2, no API key validation, no mTLS. No authentication mechanism exists.
- **Gap**: No machine identity authentication. Any network-reachable client can invoke RPCs without presenting credentials. No audit attribution possible.
- **Recommendation**: Add gRPC server interceptor for API key or OAuth2 bearer token validation. Replace `add_insecure_port` with `add_secure_port` using TLS.
- **Evidence**: `email_server.py` (line: `server.add_insecure_port('[::]:'+port)`)

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK
- **Finding**: No IAM policies, role definitions, or permission scoping in the codebase. No IaC defines IAM roles. Single gRPC endpoint with no permission model.
- **Gap**: No scoped permissions. Agent identities cannot be granted limited access.
- **Recommendation**: Define IAM roles or API key scopes. Implement gRPC interceptor for permission checks.
- **Evidence**: `email_server.py` (no authorization checks)

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK
- **Finding**: Single RPC with no authorization middleware, no ABAC/RBAC implementation.
- **Gap**: No action-level authorization. Cannot distinguish permitted from prohibited callers.
- **Recommendation**: Add gRPC server interceptor validating caller permissions per RPC method.
- **Evidence**: `email_server.py` (BaseEmailService, EmailService, DummyEmailService)

#### AUTH-Q4: Identity Propagation
- **Severity**: RISK
- **Finding**: No JWT parsing, no OAuth2 on-behalf-of flows, no token exchange. Service does not read identity headers from gRPC metadata.
- **Gap**: No identity propagation. Service cannot determine end-user context.
- **Recommendation**: Implement gRPC metadata propagation for user identity with JWT validation.
- **Evidence**: `email_server.py` (SendOrderConfirmation — no metadata reading)

#### AUTH-Q5: Agent-as-Self vs Agent-on-Behalf-of-User
- **Severity**: RISK
- **Finding**: No identity differentiation mechanisms. No separate roles/keys for different access modes. No audit log fields distinguish agent modes.
- **Gap**: Cannot distinguish agent access modes.
- **Recommendation**: Design identity model distinguishing agent-as-self from agent-on-behalf-of-user with separate credentials.
- **Evidence**: `email_server.py` (no identity handling)

#### AUTH-Q6: Credential Management
- **Severity**: RISK
- **Finding**: No hardcoded credentials found. Environment variables used for non-secret config only. No Secrets Manager or Vault integration. EmailService (non-dummy) references undefined variables for mail provider config.
- **Gap**: No secrets management system. Mail provider credentials will need secure management when non-dummy mode is implemented.
- **Recommendation**: Implement AWS Secrets Manager integration before enabling non-dummy mode.
- **Evidence**: `email_server.py` (EmailService.__init__, env vars), `Dockerfile` (ENV variables)

#### AUTH-Q7: Immutable Audit Logging ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: JSON structured logging via `logger.py` with timestamp and severity. No authenticated principal in logs (no auth exists). No CloudTrail, no immutable storage, no log file validation.
- **Gap**: No immutable audit logging. Logs lack principal attribution. No tamper-evident storage.
- **Recommendation**: After implementing auth (AUTH-Q1), add principal to log entries. Ship logs to immutable store.
- **Evidence**: `logger.py`, `email_server.py`

#### AUTH-Q8: Agent Identity Suspension
- **Severity**: RISK
- **Finding**: No API key revocation, no identity management, no kill-switch mechanism. No authentication exists to suspend.
- **Gap**: Cannot suspend individual agent identities without network-level intervention.
- **Recommendation**: After implementing auth (AUTH-Q1), add agent identity suspension mechanism.
- **Evidence**: `email_server.py` (no identity management)
### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: Single-step operation (send email). No saga pattern, no undo endpoints, no Step Functions. Email sending is irreversible.
- **Gap**: No compensation or rollback. Sent emails cannot be recalled.
- **Recommendation**: Implement two-phase approach: queue emails pending, then confirm/send after workflow completion.
- **Evidence**: `email_server.py` (SendOrderConfirmation — no rollback logic)

#### STATE-Q2: Queryable Current State
- **Severity**: RISK
- **Finding**: Service is entirely stateless. Returns `Empty`. No GET endpoints, no status query APIs, no persistent state.
- **Gap**: Agents cannot inspect email delivery state for an order.
- **Recommendation**: Add state store tracking email status per order ID. Expose `GetEmailStatus` RPC.
- **Evidence**: `email_server.py`, `demo_pb2_grpc.py`

#### STATE-Q3: Concurrency Controls
- **Severity**: RISK
- **Finding**: No optimistic locking, ETags, or deduplication. Concurrent calls with same order send duplicate emails. `ThreadPoolExecutor(max_workers=10)` allows 10 concurrent requests.
- **Gap**: No concurrency controls. Duplicate email sends possible.
- **Recommendation**: Add idempotency layer using `order_id` as deduplication key.
- **Evidence**: `email_server.py`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK
- **Finding**: No resilience libraries, no retry decorators, no circuit breakers, no timeout configurations on outbound calls.
- **Gap**: No resilience patterns. Mail provider failures cascade to callers.
- **Recommendation**: Implement circuit breakers and retry with exponential backoff for mail provider calls.
- **Evidence**: `email_server.py`, `requirements.txt`

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK
- **Finding**: No rate limiting middleware, no API Gateway throttling, no WAF rate rules. Only implicit concurrency cap from ThreadPoolExecutor.
- **Gap**: Runaway agent loops could overwhelm the service at machine speed.
- **Recommendation**: Implement rate limiting via gRPC server interceptor with per-caller limits.
- **Evidence**: `email_server.py`

#### STATE-Q6: Blast Radius and Transaction Limits
- **Severity**: RISK
- **Finding**: No configurable limits on agent-initiated actions. No max emails per hour, no max recipients per session.
- **Gap**: No blast radius controls. Agent error could trigger thousands of emails.
- **Recommendation**: Add `max_emails_per_hour`, `max_emails_per_order_id` limits enforced per agent identity.
- **Evidence**: `email_server.py`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: RISK
- **Finding**: Fixed `ThreadPoolExecutor(max_workers=10)`. No resource limits in Dockerfile. No load tests, no auto-scaling, no capacity planning.
- **Gap**: Not sized for agent traffic. 10-worker pool exhausted quickly under agent load.
- **Recommendation**: Load test with agent traffic patterns. Configure autoscaling and increase worker capacity.
- **Evidence**: `email_server.py`, `Dockerfile`
### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State
- **Severity**: RISK
- **Finding**: No draft or pending state concept. `SendOrderConfirmation` immediately sends (or logs in dummy mode). No two-step commit, no approval workflow, no "pending" status.
- **Gap**: Agents cannot propose email sends for human review before committing.
- **Recommendation**: Add two-phase flow: `CreateDraftConfirmation` followed by `ConfirmSend`.
- **Evidence**: `email_server.py`, `demo_pb2_grpc.py`

#### HITL-Q2: Configurable Approval Gates
- **Severity**: RISK
- **Finding**: No approval mechanism, no human-in-the-loop gates, no configurable operation-level flags. Single operation executes immediately.
- **Gap**: High-risk operations cannot be gated for human approval.
- **Recommendation**: Integrate with approval workflow system (Step Functions or lightweight approval queue).
- **Evidence**: `email_server.py`

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK
- **Finding**: Service runs in dummy mode by default (`start(dummy_mode = True)`) — `DummyEmailService` logs instead of sending. No separate staging environment config, no docker-compose, no seed data scripts.
- **Gap**: Dummy mode provides basic sandbox but no production-equivalent staging with realistic data shapes.
- **Recommendation**: Create docker-compose for local multi-service testing. Add seed data for agent testing.
- **Evidence**: `email_server.py` (`DummyEmailService`, `start(dummy_mode = True)`)
### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: Service handles email addresses (PII) via `request.email` and shipping addresses (`street_address`, `city`, `country`, `zip_code`). `DummyEmailService` logs email directly. `confirmation.html` renders full order details. No data classification, no field-level encryption, no PII access controls.
- **Gap**: PII is unclassified and unprotected. No controls prevent agents from accessing PII without authorization.
- **Recommendation**: Classify PII fields in schema documentation. Implement field-level access controls and PII redaction.
- **Evidence**: `email_server.py`, `demo_pb2.py`, `templates/confirmation.html`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: No data residency configuration, no GDPR/LGPD references, no region-specific storage config. Service processes transient PII data without persistence.
- **Gap**: No data residency controls. Cross-region PII transmission to LLM endpoints is uncontrolled.
- **Recommendation**: Document data residency requirements. Implement controls preventing PII transmission outside deployment region.
- **Evidence**: `email_server.py`, `demo_pb2.py`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK
- **Finding**: Command endpoint only (send email). Returns `Empty`. No pagination, filtering, sorting, or field selection.
- **Gap**: No query support. Agents cannot inspect email status or filter by criteria.
- **Recommendation**: Add query endpoints with pagination if agents need to inspect email delivery state.
- **Evidence**: `demo_pb2_grpc.py`, `demo_pb2.py`

#### DATA-Q4: System of Record Designations
- **Severity**: RISK
- **Finding**: No system-of-record designations, no data ownership definitions. Email service consumes order data from upstream checkout service with no documented ownership model.
- **Gap**: No system-of-record clarity. Agents querying multiple services may encounter conflicting data.
- **Recommendation**: Document data ownership model. Designate checkout service as system of record for order data.
- **Evidence**: `email_server.py`

#### DATA-Q5: Reliable Timestamps
- **Severity**: RISK
- **Finding**: Logger adds timestamps via `record.created`. Protobuf messages have no timestamp fields. No explicit UTC normalization or NTP configuration.
- **Gap**: No reliable timestamps on business data. Only log entries have timestamps.
- **Recommendation**: Add `created_at` and `event_time` fields as `google.protobuf.Timestamp` to request messages.
- **Evidence**: `logger.py`, `demo_pb2.py`

#### DATA-Q6: Data Freshness Signaling
- **Severity**: RISK
- **Finding**: Returns `Empty` with no metadata. No freshness headers, no consistency level indicators. Input order data may be stale.
- **Gap**: No data freshness signaling. Agents cannot assess if provided data is current.
- **Recommendation**: Accept `data_freshness` metadata in gRPC headers. Reject stale requests.
- **Evidence**: `email_server.py`, `demo_pb2.py`

#### DATA-Q7: PII Redaction in Logs
- **Severity**: RISK
- **Finding**: `DummyEmailService` logs `request.email` directly in plaintext: `'A request to send order confirmation email to {} has been received.'.format(request.email)`. No log scrubbing, no PII masking.
- **Gap**: Email addresses (PII) logged without redaction. Compliance risk if logs are centralized.
- **Recommendation**: Mask email addresses in logs. Implement PII redaction utility.
- **Evidence**: `email_server.py` (DummyEmailService.SendOrderConfirmation)

#### DATA-Q8: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics, profiling, or validation. Service accepts any input without completeness or format checks.
- **Gap**: No quality gates. Malformed data reaches email rendering without detection.
- **Recommendation**: Add input validation for required fields (email format, non-empty order items).
- **Evidence**: `email_server.py`, `demo_pb2.py`
### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Documentation and Versioning
- **Severity**: RISK
- **Finding**: Protobuf definitions in `demo_pb2.py` define the schema. Compiled from external `.proto` file. No schema versioning, no changelog, no schema registry.
- **Gap**: Schema not independently versioned. Changes not tracked with version numbers within this repo.
- **Recommendation**: Add schema versioning to Protobuf package. Maintain CHANGELOG for schema evolution.
- **Evidence**: `demo_pb2.py`, `genproto.sh`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Protobuf field names are clear and human-readable: `email`, `order`, `order_id`, `shipping_tracking_id`, `shipping_cost`, `shipping_address`, `street_address`, `city`, `country`, `zip_code`, `product_id`, `quantity`, `currency_code`, `units`, `nanos`. No legacy abbreviations.
- **Gap**: None. Field names are well-designed for agent consumption.
- **Recommendation**: Maintain naming conventions. Document `nanos` (fractional currency units in billionths).
- **Evidence**: `demo_pb2.py`, `templates/confirmation.html`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No data catalog, metadata files, data dictionaries, or API catalogs. Data model defined only in compiled Protobuf.
- **Gap**: Agent tool builders must reverse-engineer data model from Protobuf definitions.
- **Recommendation**: Add data model documentation to service README with field descriptions and examples.
- **Evidence**: `demo_pb2.py`

#### DISC-Q4: Data Lineage
- **Severity**: INFO
- **Finding**: No lineage tools, ETL documentation, or data flow diagrams. `genproto.sh` references external proto. No documentation of order data flow (checkout → email → mail provider).
- **Gap**: No lineage for tracing data issues back to source.
- **Recommendation**: Document data flow diagram in service README.
- **Evidence**: `genproto.sh`, `email_server.py`
### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK
- **Finding**: OpenTelemetry instrumentation present (TracerProvider, BatchSpanProcessor, OTLPSpanExporter, GrpcInstrumentorServer). Tracing conditional on `ENABLE_TRACING=1`. JSON structured logging via `pythonjsonlogger` with timestamp and severity. Logs lack trace_id, correlation_id, or request_id.
- **Gap**: Tracing is optional and disconnected from logs. Cannot link log entries to trace spans.
- **Recommendation**: Inject trace_id/span_id into log formatter. Enable tracing by default.
- **Evidence**: `email_server.py`, `logger.py`, `requirements.txt`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK
- **Finding**: No CloudWatch alarms, no alerting configuration, no PagerDuty/OpsGenie integration. No alerting thresholds for error rates or latency.
- **Gap**: No alerting. Target system degradation goes undetected.
- **Recommendation**: Define CloudWatch alarms for error rate >1% and P95 latency >2s. Integrate with on-call notification.
- **Evidence**: No alerting configuration found in any file.

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics, no `put_metric_data` calls. Service logs basic operational messages only.
- **Gap**: No business outcome tracking (email delivery success, bounce rate).
- **Recommendation**: Add `emails_sent_total`, `emails_failed_total`, `email_delivery_latency_p95` metrics.
- **Evidence**: `email_server.py`, `logger.py`
### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK
- **Finding**: No IaC files in this repository — no Terraform, CloudFormation, CDK, Helm, or Kustomize. Agent-facing infrastructure not defined as code. No drift detection.
- **Gap**: Integration surface not governed as code. Infrastructure changes not peer-reviewed.
- **Recommendation**: Define deployment infrastructure as code (Kubernetes manifests, Helm chart) in this repository or document external IaC dependency.
- **Evidence**: No IaC files found. `Dockerfile` (container build only)

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK
- **Finding**: No CI/CD pipeline definitions. No contract tests, no Pact, no Protobuf schema validation in build.
- **Gap**: No CI/CD and no contract testing. Schema or implementation changes could break agents undetected.
- **Recommendation**: Add CI/CD with Protobuf backward compatibility checks (e.g., `buf breaking`), unit tests, and contract tests.
- **Evidence**: No CI/CD files found.

#### ENG-Q3: Rollback Capability
- **Severity**: RISK
- **Finding**: No deployment configuration — no blue/green, no canary, no CodeDeploy, no feature flags, no rollback triggers. Dockerfile defines image build only.
- **Gap**: No rollback capability. Broken deployments cannot be automatically reverted.
- **Recommendation**: Define deployment strategy with automatic rollback triggers (Kubernetes rolling updates with health checks).
- **Evidence**: `Dockerfile`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK
- **Finding**: No test files in repository. No pytest, unittest, integration tests, or contract tests. No test frameworks in requirements.txt.
- **Gap**: Zero test coverage for the SendOrderConfirmation RPC.
- **Recommendation**: Add unit tests, error handling tests, and integration tests using `grpcio-testing`. Target >80% coverage.
- **Evidence**: No test files found. `requirements.txt` (no test dependencies). `email_client.py` (manual client only)

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: RISK
- **Finding**: No KMS configuration or encryption-at-rest settings. Service is stateless (no persistent data). Logs containing PII written to stdout without encryption guarantees.
- **Gap**: No encryption-at-rest controls defined. Log data with PII is unprotected.
- **Recommendation**: Confirm deployment environment encrypts log storage at rest. Use KMS-encrypted storage for any future persistent state.
- **Evidence**: No encryption configuration. `email_server.py` (stateless), `Dockerfile`

#### ENG-Q6: Cross-Origin and Network Policies
- **Severity**: BLOCKER
- **Finding**: gRPC server binds to all interfaces on insecure port: `server.add_insecure_port('[::]:'+port)`. No TLS, no security groups, no network policies, no API gateway, no firewall rules, no WAF.
- **Gap**: No network security configuration. Service exposed without encryption or access control.
- **Recommendation**: Replace `add_insecure_port` with `add_secure_port` using TLS. Define network policies restricting access to authorized callers.
- **Evidence**: `email_server.py`, `Dockerfile` (EXPOSE 8080)
---

## Evidence Index

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `email_server.py` | API-Q1, API-Q3, API-Q4, API-Q7, API-Q8, API-Q9, API-Q10, AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q6, AUTH-Q7, AUTH-Q8, STATE-Q1, STATE-Q2, STATE-Q3, STATE-Q4, STATE-Q5, STATE-Q6, STATE-Q7, HITL-Q1, HITL-Q2, HITL-Q3, DATA-Q1, DATA-Q2, DATA-Q3, DATA-Q4, DATA-Q6, DATA-Q7, DISC-Q4, OBS-Q1, OBS-Q3, ENG-Q5, ENG-Q6 |
| `email_client.py` | API-Q1, ENG-Q4 |
| `logger.py` | AUTH-Q7, DATA-Q5, OBS-Q1, OBS-Q3 |
| `demo_pb2.py` | API-Q1, API-Q2, API-Q4, API-Q5, API-Q6, DATA-Q1, DATA-Q2, DATA-Q3, DATA-Q5, DATA-Q6, DATA-Q8, DISC-Q1, DISC-Q2 |
| `demo_pb2_grpc.py` | API-Q1, API-Q2, API-Q5, API-Q6, STATE-Q2, HITL-Q1, DATA-Q3 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `Dockerfile` | AUTH-Q6, STATE-Q7, ENG-Q1, ENG-Q3, ENG-Q5, ENG-Q6 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `requirements.txt` | STATE-Q4, OBS-Q1, ENG-Q4 |
| `requirements.in` | OBS-Q1 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `templates/confirmation.html` | DATA-Q1, DISC-Q2 |

### Scripts
| File | Questions Referenced |
|------|---------------------|
| `genproto.sh` | API-Q1, API-Q2, DISC-Q1, DISC-Q4 |
