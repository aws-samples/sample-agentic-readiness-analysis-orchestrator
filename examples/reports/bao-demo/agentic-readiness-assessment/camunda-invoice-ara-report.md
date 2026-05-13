# Agentic Readiness Assessment Report

**Target**: camunda-invoice (examples/invoice within Camunda Platform 7 monorepo)
**Date**: 2025-07-14
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: monorepo
**Service Archetype**: orchestrator (auto-detected)
**Agent Scope**: read-only
**Priority**: P0
**Tags**: camunda-c7, finance, invoice
**Context**: Camunda 7 invoice receipt process with Java delegate service tasks, DMN business rules, data store references, and call activities.

**Archetype Justification**: The invoice process coordinates a multi-step workflow across three lanes (Team Assistant, Approver, Accountant), invoking a business rule task (DMN), multiple user tasks, a call activity (ReviewInvoice subprocess), and two Java delegate service tasks (NotifyCreditorService, ArchiveInvoiceService). This multi-participant coordination pattern with persistent state via the Camunda engine's database layer matches the orchestrator archetype.

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 1 | **RISK-SAFETY**: 6 | **RISK-QUALITY**: 17 | **INFOs**: 12

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days. The single BLOCKER (DATA-Q1: Sensitive Data Classification) must be resolved before any agent can safely read invoice process data. Once the BLOCKER is resolved, the 6 RISK-SAFETY findings place this service at **Pilot-Ready (Safety Concerns)**, requiring supervised pilot with elevated safety oversight.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 1 |
| RISK-SAFETY | 6 |
| RISK-QUALITY | 17 |
| INFO | 12 |
| N/A | 0 |
| Not Evaluated (extended) | 0 |
| **Total (with gaps)** | **36** |
| **PASS (no gap found)** | **7** |
| **Grand Total** | **43** |

*Note: 7 questions were evaluated at their designated severity level but no gap was found (API-Q1, AUTH-Q1, AUTH-Q2, AUTH-Q3, STATE-Q2, STATE-Q4, DATA-Q3). These PASS findings are excluded from BLOCKER and RISK counts that determine the readiness profile. 12 questions resolved to INFO either because they are inherently INFO-severity or because `agent_scope=read-only` downgraded conditional BLOCKERs/RISKs to INFO.*

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 19
**Extended Questions Not Triggered**: 0
**Questions N/A (repo_type: monorepo)**: 0
**Service Archetype**: orchestrator (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: The invoice process handles sensitive business data including creditor names (e.g., "Great Pizza for Everyone Inc."), invoice amounts (monetary values), invoice numbers (business identifiers), uploaded invoice documents (PDF files), and user personal data (emails like `demo@camunda.org`, first/last names). The `DemoDataGenerator.java` creates users with emails and passwords. The `start-form.html` collects creditor, amount, invoiceCategory, invoiceNumber, and invoiceDocument. None of this data is classified at the field level. No data classification tags exist on any Camunda engine database tables, process variables, or API responses. No Amazon Macie or equivalent PII detection is configured.
- **Gap**: No field-level data classification exists for any invoice process data. Sensitive fields (creditor names — potentially business PII, invoice amounts — financial data, user emails — personal data) are stored and transmitted without classification metadata. An agent reading process variables would have no signal about data sensitivity.
- **Remediation**:
  - **Immediate**: Create a data classification inventory for all process variables (creditor=Business-Confidential, amount=Financial, invoiceNumber=Business-Identifier, invoiceDocument=Business-Confidential, user emails=PII). Document in a classification manifest.
  - **Target State**: All process variables and API response fields have classification metadata. Access controls enforce classification-based restrictions (e.g., PII fields require elevated permissions).
  - **Estimated Effort**: Medium (30–60 days)
  - **Dependencies**: AUTH-Q2 (scoped permissions needed to enforce classification-based access controls)
- **Evidence**: `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/DemoDataGenerator.java` (user PII creation), `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/InvoiceApplicationHelper.java` (process variable values), `examples/invoice/src/main/webapp/forms/start-form.html` (data collection fields), `examples/invoice/src/main/resources/invoice.v2.bpmn` (process variable definitions)

---

## RISKs

### RISK-SAFETY — Must Address for Agent Safety

#### AUTH-Q6: Immutable Audit Logging ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No immutable, tamper-evident audit logging configuration found in the repository. The Camunda engine provides a built-in User Operation Log (history) that records user actions, but this log is stored in the same database as process data and is not immutable — it can be modified or deleted. No AWS CloudTrail configuration, no S3 bucket with object lock for logs, no CloudWatch log retention policies, and no external immutable log storage are configured. The `Jenkinsfile` and CI/CD configs contain no audit log infrastructure.
- **Gap**: Audit logs are not immutable or tamper-evident. An attacker (or misconfigured agent) could potentially modify or delete operation history. No compliance-grade audit trail exists for agent-initiated actions.
- **Compensating Controls**:
  - Export Camunda User Operation Log to an append-only external store (e.g., S3 with Object Lock, CloudWatch Logs with retention policy) on a scheduled basis.
  - Enable database audit logging at the infrastructure layer (e.g., RDS audit logs) as a compensating control.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure CloudTrail for API-level audit. Export Camunda engine operation logs to immutable storage (S3 with Object Lock or CloudWatch Logs Insights). Ensure agent identity is captured in every log entry.
- **Evidence**: No audit configuration files found. `examples/invoice/src/test/resources/camunda.cfg.xml` (engine config without audit settings), `Jenkinsfile` (no audit infrastructure)

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: The Camunda Identity Service supports user creation, modification, and deletion via API (`identityService.saveUser()`, `identityService.deleteUser()`). A service account user could be deleted or its password changed to effectively suspend it. However, there is no automated suspension mechanism — no API key revocation endpoint, no automated anomaly-based suspension, and no immediate credential invalidation without restarting sessions. The `DemoDataGenerator.java` demonstrates user management capabilities but no suspension workflow.
- **Gap**: While manual user deletion/disabling is possible through the Camunda API, there is no automated, immediate suspension mechanism for agent identities. If an agent misbehaves, an operator must manually intervene through the Camunda admin interface or API. No circuit-breaker or anomaly-triggered suspension exists.
- **Compensating Controls**:
  - Implement an API Gateway layer in front of the Camunda REST API with API key management and instant revocation capability.
  - Use network-level controls (security group rules) to immediately block agent IP/identity if needed.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement an API Gateway (e.g., AWS API Gateway) in front of the Camunda REST API with API key-based authentication. This enables instant key revocation without modifying the Camunda user store.
- **Evidence**: `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/DemoDataGenerator.java` (user management via IdentityService)

#### STATE-Q1: Compensation and Rollback ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: The BPMN process definitions (`invoice.v2.bpmn`, `invoice.v1.bpmn`, `reviewInvoice.bpmn`) do not include BPMN compensation handlers, compensation boundary events, or explicit rollback logic. The `ArchiveInvoiceService.java` has a `shouldFail` variable that triggers a `ProcessEngineException`, but there is no compensating action defined — the exception simply halts the process. The Camunda engine provides database-level transaction management (commit/rollback at the persistence layer), but no application-level compensation or saga pattern is implemented. The call activity to `ReviewInvoice` passes variables in/out but has no error boundary event or compensation handler.
- **Gap**: No compensation or rollback capability exists at the process level. If the "Archive Invoice" service task fails after "Prepare Bank Transfer" is completed, there is no automated way to reverse the bank transfer preparation. The process remains in a failed state with no compensating action.
- **Compensating Controls**:
  - For read-only agent scope, this risk is mitigated because agents will only query state, not initiate write operations.
  - Camunda's job retry mechanism (configured via `camunda:async="true"` on ArchiveInvoiceService) provides retry capability for failed service tasks.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add BPMN compensation boundary events and compensation handlers for critical service tasks. Define explicit undo endpoints for reversible operations. Implement a saga pattern for the invoice approval workflow.
- **Evidence**: `examples/invoice/src/main/resources/invoice.v2.bpmn` (no compensation events), `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/service/ArchiveInvoiceService.java` (exception without compensation)

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: No rate limiting or throttling configuration found anywhere in the repository. No API Gateway with throttle settings, no WAF rate rules, no application-level rate limiting middleware, no `aws_api_gateway_usage_plan` in IaC (no IaC exists). The Camunda REST API is exposed directly without any traffic management layer. The `Jenkinsfile` and CI/CD configurations contain no infrastructure provisioning for rate limiting. No `.env` or configuration files reference rate limits.
- **Gap**: A runaway agent loop calling the Camunda REST API at machine speed could overwhelm the process engine, exhaust database connections, and cause cascading failures affecting all users and processes — not just the invoice process.
- **Compensating Controls**:
  - Deploy an API Gateway (AWS API Gateway, nginx, or HAProxy) in front of the Camunda REST API with per-client rate limits.
  - Configure application server (Tomcat/WildFly) thread pool limits as a coarse-grained defense.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Deploy an API Gateway with rate limiting before exposing the Camunda REST API to any agent. Configure per-identity throttling (e.g., 100 requests/minute for agent service accounts).
- **Evidence**: No rate limiting configuration found in any file. No IaC files exist. No API Gateway definitions found.

#### DATA-Q2: Data Residency and Sovereignty ⚡ — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No data residency or sovereignty configuration found in the repository. No GDPR, LGPD, or HIPAA compliance references in code or configuration. No region-specific data storage configurations. No cross-region replication settings. The invoice process handles European business data (Camunda Services GmbH is Germany-based), creditor information, and financial records that may be subject to GDPR and EU data residency requirements. The `SECURITY.md` links to Camunda's security guide but contains no residency-specific guidance.
- **Gap**: No explicit data residency controls exist. If an agent transmits invoice data (creditor names, amounts, financial records) to an LLM endpoint outside the EU, this could violate GDPR data transfer rules. The finance domain context and P0 priority elevate this concern.
- **Compensating Controls**:
  - Restrict agent LLM calls to EU-region endpoints (e.g., Amazon Bedrock in eu-west-1).
  - Implement a data filtering proxy that strips or anonymizes sensitive fields before they reach the LLM.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Document data residency requirements for invoice process data. Configure infrastructure to ensure data stays within required jurisdictions. Implement data residency metadata on API responses.
- **Evidence**: `SECURITY.md` (generic security link, no residency guidance), no IaC with region configurations

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

- **Severity**: RISK-SAFETY
- **Finding**: PII is logged directly without redaction. `NotifyCreditorService.java` logs the creditor name directly: `LOGGER.info("... Now notifying creditor " + execution.getVariable("creditor"))`. `ArchiveInvoiceService.java` logs the invoice number and filename: `LOGGER.info("... Now archiving invoice " + execution.getVariable("invoiceNumber") + ", filename: " + invoiceDocumentVar.getFilename())`. `InvoiceApplicationHelper.java` creates process instances with creditor names, amounts, and invoice numbers that flow through the engine's standard logging. No log scrubbing middleware, no PII masking libraries, no CloudWatch log filters, and no Amazon Macie integration are configured.
- **Gap**: Creditor names (business PII) and invoice numbers (business identifiers) are logged in plaintext. If agent operations generate additional log entries, PII leakage into observable surfaces increases. No log redaction or masking exists anywhere in the codebase.
- **Compensating Controls**:
  - Implement a custom Camunda logging filter that masks process variable values in log output.
  - Restrict log access to authorized personnel and configure log retention policies.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Implement a logging wrapper that masks PII fields (creditor names, emails, invoice numbers) in log output. Add a PII scrubbing filter to the logging pipeline. Audit all `LOGGER.info()` calls for sensitive data exposure.
- **Evidence**: `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/service/NotifyCreditorService.java` (line: `execution.getVariable("creditor")`), `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/service/ArchiveInvoiceService.java` (line: `execution.getVariable("invoiceNumber")`)

### RISK-QUALITY — Address as Capacity Allows

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The Camunda Platform REST API has an OpenAPI 3.0.2 specification defined via FreeMarker templates in `engine-rest/engine-rest-openapi/src/main/templates/main.ftl`. The spec covers 51 API tag categories including Process Instance, Task, Decision Definition, Deployment, Authorization, and more. The spec is versioned with `${cambpmVersion}` and is auto-generated from templates during the build process. However, the spec is not a static OpenAPI JSON/YAML file — it requires FreeMarker template processing to produce the final spec. The OpenAPI validation schema exists at `engine-rest/engine-rest-openapi/src/main/openapi/schema.json`.
- **Gap**: The OpenAPI spec is template-based, not directly consumable as a static file from the repository. An agent framework attempting to auto-generate tool definitions would need to first build the project to produce the final OpenAPI JSON. The generated spec is comprehensive but requires a build step to materialize.
- **Compensating Controls**:
  - Generate and commit the final OpenAPI JSON/YAML as a build artifact in the repository.
  - Publish the generated spec to a registry (e.g., SwaggerHub, API catalog) for direct consumption.
- **Remediation Timeline**: 7–14 days
- **Recommendation**: Add a CI step that generates the final OpenAPI spec and publishes it as a static artifact. Consider committing the generated spec to the repository for direct agent framework consumption.
- **Evidence**: `engine-rest/engine-rest-openapi/src/main/templates/main.ftl` (OpenAPI 3.0.2 template), `engine-rest/engine-rest-openapi/src/main/openapi/schema.json` (validation schema)

#### API-Q3: Structured Error Responses — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The Camunda REST API defines structured error responses in the OpenAPI spec templates. The `ExceptionDto` model is referenced across error responses (4xx, 5xx). Error responses include `type` (exception class name), `message` (human-readable description), and `code` fields. However, in the invoice application code, `ArchiveInvoiceService.java` throws a generic `ProcessEngineException("Could not archive invoice...")` without structured error codes or retryable categorization. The engine translates this to a standard HTTP error response.
- **Gap**: While the REST API provides structured error DTOs, there is no `retryable` boolean or error category field in the error response. Agents cannot programmatically distinguish between retriable errors (timeout, rate limit) and terminal errors (invalid input, permission denied) without parsing error messages.
- **Compensating Controls**:
  - Document error codes and their retryable status in agent tool definitions.
  - Implement agent-side error classification based on HTTP status codes (5xx = retry, 4xx = terminal).
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Extend the Camunda REST API error response DTO with a `retryable` boolean and an error `category` enum (validation, authorization, internal, timeout). Map all exception types to these categories.
- **Evidence**: `engine-rest/engine-rest-openapi/src/main/templates/main.ftl` (error response schemas), `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/service/ArchiveInvoiceService.java` (generic exception)

#### API-Q6: Asynchronous Operation Support — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Trigger**: Service has operations >30s OR long-running workflows (orchestrator archetype)
- **Finding**: The invoice process is inherently long-running — it involves human tasks (Approve Invoice, Prepare Bank Transfer, Assign Reviewer, Review Invoice) that may take hours or days. The Camunda REST API supports asynchronous patterns: process instances are started via POST and return immediately with a process instance ID. Task completion is a separate API call. The `ArchiveInvoiceService` is configured with `camunda:async="true"` making it a job executed asynchronously. The REST API provides job query and execution endpoints for monitoring async work. However, there is no webhook callback mechanism for task/process completion notifications.
- **Gap**: While the REST API supports polling-based async patterns (start process → poll task list → complete task), there is no webhook or push notification mechanism. An agent must poll for task state changes, which is inefficient for long-running human tasks that may take days.
- **Compensating Controls**:
  - Implement polling with exponential backoff for monitoring long-running process instances.
  - Use Camunda's external task pattern for service tasks that need async completion signaling.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement webhook endpoints or configure SNS/EventBridge notifications for process state changes (task creation, task completion, process completion). This enables event-driven agent workflows instead of polling.
- **Evidence**: `examples/invoice/src/main/resources/invoice.v2.bpmn` (async service task, human user tasks), `engine-rest/engine-rest-openapi/src/main/templates/main.ftl` (async API endpoints)

#### AUTH-Q4: Identity Propagation and Delegation — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The Camunda engine supports setting authenticated user context via `identityService.setAuthentication("demo", Arrays.asList(Groups.CAMUNDA_ADMIN))` and `identityService.setAuthenticatedUserId("mary")` as demonstrated in `InvoiceApplicationHelper.java`. The REST API uses basic auth, and the authenticated user is associated with operations. However, there is no JWT token exchange, no OAuth2 on-behalf-of flow, and no mechanism to distinguish between an agent acting under its own identity vs. acting on behalf of a specific user. The basic auth credential is the only identity context.
- **Gap**: No identity propagation through service calls. No distinction between agent-as-self and agent-on-behalf-of-user. If an agent completes a task on behalf of a user, the audit log shows the agent's identity, not the delegating user.
- **Compensating Controls**:
  - Include user context in process variables (e.g., `delegatedBy` variable) when an agent acts on behalf of a user.
  - Implement an API Gateway layer that maps agent tokens to Camunda user contexts.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement an authentication proxy or API Gateway that supports JWT/OAuth2 with user delegation claims. Map delegated identity to Camunda's authenticated user context so audit logs reflect both the agent and the delegating user.
- **Evidence**: `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/InvoiceApplicationHelper.java` (setAuthentication, setAuthenticatedUserId), `engine-rest/engine-rest-openapi/src/main/templates/main.ftl` (basicAuth security scheme only)

#### AUTH-Q5: Credential Management — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The `DemoDataGenerator.java` contains hardcoded credentials: user "demo" with password "demo", user "john" with password "john", user "mary" with password "mary", user "peter" with password "peter". These are demo credentials intended for showcase purposes only (as stated in the class javadoc: "Creates demo credentials to be used in the invoice showcase"). The Jenkinsfile uses HashiCorp Vault for CI/CD secrets (`withVault` for HERODEVS registry credentials). However, no secrets management integration exists for application-level credentials. No `.env` files are committed. No `aws_secretsmanager` references found.
- **Gap**: Demo credentials are hardcoded in source code. While these are clearly labeled as demo data, there is no production credential management pattern. No Secrets Manager, Vault, or SSM Parameter Store integration exists for application-level authentication. The Vault usage in CI/CD does not extend to application runtime secrets.
- **Compensating Controls**:
  - Ensure demo credentials are never used in production deployments.
  - Implement environment-variable-based credential injection for production.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Integrate AWS Secrets Manager or HashiCorp Vault for production credential management. Remove hardcoded demo credentials from the production deployment path. Implement secret rotation for agent service account credentials.
- **Evidence**: `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/DemoDataGenerator.java` (hardcoded passwords), `Jenkinsfile` (Vault usage for CI/CD only)

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The test configuration at `camunda.cfg.xml` uses `StandaloneInMemProcessEngineConfiguration` — a fully in-memory process engine suitable for unit/integration testing. The `DemoDataGenerator.java` creates seed data (users, groups, authorizations, filters). The `InvoiceTestCase.java` provides 4 test scenarios (happy path V1/V2, non-successful path, approval assignment) that exercise the full process lifecycle. However, no dedicated staging or sandbox environment configuration exists. No Docker Compose file for local testing. No separate environment-specific configuration files (staging.yml, sandbox.properties). No synthetic data generators beyond the demo data.
- **Gap**: While in-memory testing infrastructure exists, there is no production-equivalent staging or sandbox environment where an agent can be tested against realistic data shapes and volumes without risk to live systems. The in-memory engine is suitable for unit tests but not for agent integration testing.
- **Compensating Controls**:
  - Use the in-memory engine configuration with DemoDataGenerator as a lightweight sandbox for initial agent testing.
  - Deploy a dedicated Camunda instance with the invoice process for agent staging tests.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Create a Docker Compose configuration that stands up a Camunda Platform instance with PostgreSQL, deploys the invoice process, and seeds demo data. This serves as a repeatable sandbox for agent integration testing.
- **Evidence**: `examples/invoice/src/test/resources/camunda.cfg.xml` (in-memory engine), `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/DemoDataGenerator.java` (seed data), `examples/invoice/src/test/java/org/camunda/bpm/example/invoice/InvoiceTestCase.java` (test scenarios)

#### STATE-Q7: Infrastructure Capacity for Agent Traffic — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Trigger**: Service is P0 priority
- **Finding**: No load test results, configurations, or capacity planning documentation found in the repository. No auto-scaling policies defined (no IaC exists). No performance benchmarks for the Camunda REST API or the invoice process. The CI pipeline includes integration tests on various application servers (Tomcat, WildFly) but no performance or load testing stages. No circuit breakers isolating agent traffic from human user traffic.
- **Gap**: The infrastructure has not been validated for agent-generated traffic patterns, which are typically more bursty, exploratory, and concurrent than human-paced interactions. For a P0 priority service, capacity risk is elevated.
- **Compensating Controls**:
  - Start agent integration with conservative rate limits (STATE-Q5 remediation) to cap agent traffic.
  - Monitor Camunda engine metrics during pilot to establish baseline.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Conduct load testing of the Camunda REST API with agent-like traffic patterns (rapid task queries, concurrent process instance queries). Define auto-scaling policies. Establish capacity thresholds.
- **Evidence**: `Jenkinsfile` (no load test stages), no IaC files, no performance configuration

#### DATA-Q4: System of Record Designations — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Trigger**: Orchestrator has persistent state
- **Finding**: The BPMN process references a "Financial Accounting System" data store (`DataStoreReference_1` in `invoice.v2.bpmn` and `invoice.v1.bpmn`) as a data input for the "Prepare Bank Transfer" task. However, no system-of-record designation exists for key entities (invoices, creditors, financial accounts). No master data management references, no data ownership definitions, and no conflict resolution logic are documented. The Camunda engine acts as the system of record for process state but not for business entities.
- **Gap**: No explicit system-of-record designations. An agent querying invoice data from Camunda would not know whether Camunda is the authoritative source or whether the Financial Accounting System holds the golden record.
- **Compensating Controls**:
  - Document system-of-record designations in agent tool definitions (e.g., "Camunda = SoR for process state; Financial Accounting System = SoR for financial records").
- **Remediation Timeline**: 7–14 days
- **Recommendation**: Document system-of-record designations for all key business entities that cross the invoice process boundary.
- **Evidence**: `examples/invoice/src/main/resources/invoice.v2.bpmn` (FinancialAccountingSystem data store reference)

#### DATA-Q5: Temporal Metadata and Freshness — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Trigger**: Orchestrator has persistent state
- **Finding**: The Camunda engine internally tracks timestamps for all process instances, tasks, and history entries (start time, end time, duration). The `InvoiceApplicationHelper.java` manipulates clock time for demo purposes using `ClockUtil.setCurrentTime()`, demonstrating that temporal data is engine-managed. The REST API exposes these timestamps in query results. However, no explicit `Cache-Control` headers, `X-Data-Age` headers, or `consistency_level` fields are present in API responses to signal data freshness to consumers. No timezone normalization documentation exists.
- **Gap**: While the engine maintains accurate timestamps, the API does not signal data freshness or consistency level to consumers. An agent cannot determine if a task query result is real-time or cached.
- **Compensating Controls**:
  - Assume Camunda REST API responses are real-time (strong consistency from the database) unless documented otherwise.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add `Cache-Control` and `X-Data-Freshness` headers to Camunda REST API responses. Document the consistency model for process data queries.
- **Evidence**: `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/InvoiceApplicationHelper.java` (ClockUtil usage, timestamp management)

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The BPMN process definitions use `camunda:versionTag` for versioning (V1.0, V2.0). The OpenAPI spec is versioned with `${cambpmVersion}`. The Jenkinsfile includes an `engine-api-compatibility` stage that runs `verify -Pcheck-api-compatibility`, indicating API compatibility checking in CI. The repository uses Renovate for dependency updates with auto-merge for patches and manual approval for major/minor versions. However, no consumer-driven contract tests (Pact), no OpenAPI diff tools, and no explicit breaking change detection exist for the REST API itself. The API compatibility check appears to be for the Java engine API, not the REST API.
- **Gap**: API compatibility checking exists for the Java engine API but not specifically for the REST API that agents would consume. No consumer-driven contract testing. No automated OpenAPI spec diff in CI to detect breaking changes.
- **Compensating Controls**:
  - Pin the OpenAPI spec version in agent tool definitions and validate against the spec before deployment.
  - Monitor the Camunda release notes for REST API breaking changes.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenAPI spec diff checking to the CI pipeline. Implement consumer-driven contract tests (Pact) for the agent-facing API surface. Automate breaking change detection for the REST API.
- **Evidence**: `examples/invoice/src/main/resources/invoice.v2.bpmn` (versionTag V2.0), `engine-rest/engine-rest-openapi/src/main/templates/main.ftl` (cambpmVersion), `Jenkinsfile` (engine-api-compatibility stage)

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The invoice service tasks use `java.util.logging.Logger` with unstructured, human-readable log messages. `NotifyCreditorService.java`: `LOGGER.info("\n\n  ... Now notifying creditor " + creditor + "\n\n")`. `ArchiveInvoiceService.java`: `LOGGER.info("\n\n  ... Now archiving invoice " + invoiceNumber + ", filename: " + filename + " \n\n")`. No OpenTelemetry SDK, no AWS X-Ray instrumentation, no `traceparent` header propagation, no JSON log formatting, and no `request_id` or `correlation_id` fields. The `Jenkinsfile` post-always block calls `cambpmWithSpanAttributes()`, suggesting CI/CD-level telemetry but no application-level tracing.
- **Gap**: No distributed tracing and no structured logging. Agent-initiated requests through the REST API cannot be traced end-to-end through the process engine. Failed operations produce unstructured log messages that are difficult to correlate.
- **Compensating Controls**:
  - Use Camunda process instance IDs as correlation identifiers for agent-initiated requests.
  - Implement a logging proxy that captures structured request/response pairs at the API Gateway level.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Integrate OpenTelemetry SDK into the Camunda engine deployment. Configure JSON structured logging. Propagate trace IDs through the REST API to service task execution. Add correlation IDs to all log entries.
- **Evidence**: `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/service/NotifyCreditorService.java` (unstructured logging), `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/service/ArchiveInvoiceService.java` (unstructured logging), `Jenkinsfile` (cambpmWithSpanAttributes for CI only)

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No alerting configuration found in the repository. No CloudWatch alarms, no anomaly detection, no PagerDuty/OpsGenie integration, no composite alarms, and no SLO-based alerting. The CI pipeline includes test result publishing but no production monitoring or alerting setup. No IaC files define monitoring resources.
- **Gap**: No alerting exists for the APIs agents will consume. If the Camunda REST API experiences elevated error rates or latency, there is no automated detection or notification. Degradation would be discovered only through agent failures.
- **Compensating Controls**:
  - Monitor the Camunda engine's built-in metrics (dbMetricsReporter) for anomalies during pilot.
  - Implement API Gateway-level monitoring with alerting thresholds.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Deploy CloudWatch alarms on the Camunda REST API for error rate (>5% 5xx responses), latency (p99 > 5s), and availability. Configure PagerDuty or SNS notifications for threshold breaches.
- **Evidence**: No alerting configuration files found anywhere in the repository

#### ENG-Q1: Infrastructure Governance — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No Infrastructure as Code (IaC) found in the repository. No Terraform, CloudFormation, CDK, Helm, Kustomize, or Ansible files exist. The repository is a Java application with Maven-based builds. Infrastructure provisioning (API Gateways, IAM roles, secrets, network configurations) is not defined in code. The CI pipeline (Jenkinsfile) builds and deploys artifacts to Nexus but does not provision infrastructure. No drift detection configuration exists.
- **Gap**: The agent-facing integration surface (Camunda REST API, database, network configuration) is not defined as code, not subject to automated peer review, and not monitored for drift. Infrastructure changes are manual and unaudited.
- **Compensating Controls**:
  - Document the current infrastructure configuration manually.
  - Use AWS Config rules to detect infrastructure drift at the platform level.
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Define the Camunda Platform deployment infrastructure as code (Terraform or CDK). Include API Gateway, IAM roles, database, and network configuration. Enable drift detection via AWS Config.
- **Evidence**: No IaC files found. `Jenkinsfile` (build and deploy to Nexus only, no infrastructure provisioning)

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: The Jenkinsfile defines a comprehensive CI/CD pipeline with: assembly and deployment, unit tests (H2, history levels, Quarkus), engine integration tests (Tomcat, WildFly with PostgreSQL, XA transactions), webapp integration tests, engine REST unit tests, database-specific unit tests, and miscellaneous tests including `engine-api-compatibility`. GitHub Actions include CodeQL security scanning and dependency checking. Renovate manages dependency updates. The `.snyk` file tracks security vulnerability policies. However, no consumer-driven contract tests (Pact), no OpenAPI spec validation in the build, no schema comparison tools, and no explicit breaking change detection for the REST API.
- **Gap**: CI/CD is mature for Java engine API compatibility but lacks explicit REST API contract testing. Agent tool bindings depend on the REST API contract, and breaking changes could go undetected.
- **Compensating Controls**:
  - The `engine-api-compatibility` check provides partial protection for the underlying Java API.
  - CodeQL and Snyk provide security coverage.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add OpenAPI spec generation and diff checking to the CI pipeline. Implement Pact contract tests for agent-facing API endpoints.
- **Evidence**: `Jenkinsfile` (comprehensive CI/CD), `.github/workflows/codeql.yml` (CodeQL), `.github/workflows/java-dependency-check.yml`, `.github/renovate.json5`, `.snyk`

#### ENG-Q3: Rollback Capability — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: No rollback capability is visible in the repository. No blue/green deployment configuration, no CodeDeploy rollback triggers, no Helm rollback, no feature flags, no canary deployment with automatic rollback, and no traffic shifting at API Gateway or ALB. The CI pipeline deploys artifacts to Nexus (Maven repository manager) but no production deployment or rollback mechanism is defined. The Jenkinsfile builds, tests, and publishes artifacts but does not manage production deployments.
- **Gap**: If a Camunda Platform deployment breaks agent-facing APIs, there is no defined mechanism to roll back to a known-good state. Rollback is undefined and likely manual.
- **Compensating Controls**:
  - Maintain previous artifact versions in Nexus for manual rollback.
  - Implement deployment at the infrastructure level (outside this repo) with rollback capability.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement blue/green or canary deployments for the Camunda Platform. Define rollback procedures in IaC. Configure automated rollback triggers based on health checks.
- **Evidence**: `Jenkinsfile` (build and publish to Nexus, no production deployment/rollback)

#### ENG-Q4: API Test Coverage — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Finding**: `InvoiceTestCase.java` provides 4 test methods: `testHappyPathV1()` (V1 process end-to-end), `testHappyPathV2()` (V2 process end-to-end), `testApproveInvoiceAssignment()` (task assignment), and `testNonSuccessfulPath()` (rejection and review flow). These tests exercise process logic through the Java API (not the REST API). The engine-rest module has its own test directories. However, no REST API-level tests exist for the invoice process specifically — the tests use `runtimeService`, `taskService`, and `managementService` Java APIs directly, not HTTP endpoints.
- **Gap**: Test coverage exists for process logic but not for the REST API surface that agents will consume. Input handling, output format, and error responses at the HTTP level are not tested for the invoice-specific workflow.
- **Compensating Controls**:
  - The engine-rest module has its own REST API tests that cover general endpoint behavior.
  - Process logic tests provide confidence in business rule correctness.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Add REST API integration tests that exercise the invoice process through HTTP endpoints: POST to start process, GET to query tasks, POST to complete tasks, GET to query process variables. Validate JSON response format and error handling.
- **Evidence**: `examples/invoice/src/test/java/org/camunda/bpm/example/invoice/InvoiceTestCase.java` (4 test methods, Java API only)

#### ENG-Q5: Encryption at Rest — RISK-QUALITY

- **Severity**: RISK-QUALITY
- **Trigger**: Orchestrator has persistent data stores
- **Finding**: No encryption at rest configuration found in the repository. No KMS key references, no encryption configuration for database storage, no customer-managed encryption keys. The Camunda engine persists process state, variables (including invoice documents as binary data), and history to a database (H2 for development, PostgreSQL for integration tests per the Jenkinsfile). No IaC exists to define encrypted storage resources. The test configuration (`camunda.cfg.xml`) uses in-memory storage which is inherently transient.
- **Gap**: Process data including invoice documents (PDF), creditor names, financial amounts, and user information is persisted to database storage without any encryption-at-rest configuration defined in this repository. Encryption may be configured at the infrastructure level but is not governed by this codebase.
- **Compensating Controls**:
  - Configure encryption at rest at the database level (e.g., RDS encryption, EBS encryption) outside this repository.
  - Use field-level encryption for sensitive process variables.
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Define database encryption configuration in IaC. Enable RDS encryption with KMS customer-managed keys. Consider field-level encryption for PII process variables.
- **Evidence**: `examples/invoice/src/test/resources/camunda.cfg.xml` (no encryption config), `Jenkinsfile` (PostgreSQL for integration tests, no encryption mentioned)

---

## INFOs — Architecture and Design Inputs

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No idempotency key support found in write endpoints. The Camunda REST API does not support idempotency keys for process instance creation or task completion. Duplicate POST requests would create duplicate process instances. However, since agent_scope is read-only, write idempotency is informational only.
- **Implication**: If agent scope expands to write-enabled in the future, idempotency must be addressed before agents can safely start process instances or complete tasks. This would become a BLOCKER.
- **Recommendation**: Plan for idempotency key support on write endpoints (process instance creation, task completion) if write-enabled agent scope is anticipated.
- **Evidence**: `engine-rest/engine-rest-openapi/src/main/templates/main.ftl` (no idempotency key parameters in API spec)

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: The Camunda REST API returns structured JSON responses. The OpenAPI spec defines JSON content types for all endpoints. Process variables, task data, and decision results are all serialized as JSON. Binary content (invoice PDF documents) is handled via multipart form data. The REST API also supports XML for some endpoints but JSON is the primary format.
- **Implication**: JSON format is well-suited for LLM consumption. Agent tools can consume REST API responses directly. Binary content (PDFs) requires separate handling in agent pipelines.
- **Recommendation**: No immediate action needed. Consider providing a summarization endpoint for binary invoice documents to make them LLM-consumable.
- **Evidence**: `engine-rest/engine-rest-openapi/src/main/templates/main.ftl` (JSON content types throughout)

### API-Q7: Event Emission for State Changes

- **Severity**: INFO
- **Trigger**: Orchestrator has state changes
- **Finding**: The Camunda engine supports event subscriptions (message events, signal events) as shown by the "Event Subscription" tag in the OpenAPI spec. The engine can correlate messages to process instances. However, there is no webhook endpoint, no SNS/EventBridge integration, no Kafka topic, and no CDC pipeline for pushing state change notifications to external consumers. The invoice process uses a message start event (`foxMessage_en`) but this is for triggering process instances, not for emitting state change events.
- **Implication**: Agents must poll for process state changes rather than receiving push notifications. For the invoice process, this means polling the task API to detect new approval tasks or process completions. This is viable but inefficient for long-running human tasks.
- **Recommendation**: Consider implementing a Camunda task listener or execution listener that publishes events to SNS or EventBridge when key state transitions occur (invoice approved, bank transfer prepared, invoice archived).
- **Evidence**: `examples/invoice/src/main/resources/invoice.v2.bpmn` (message event), `engine-rest/engine-rest-openapi/src/main/templates/main.ftl` (Event Subscription tag)

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limit documentation or headers found. The Camunda REST API does not return `X-RateLimit-Remaining` or `Retry-After` headers. No API Gateway throttle settings, WAF rate rules, or usage plans are configured (no IaC exists). No rate limiting middleware is present in the application.
- **Implication**: Agents have no programmatic signal about rate limits and cannot self-throttle. Without rate limit headers, agents must rely on external configuration to manage request rates.
- **Recommendation**: When implementing rate limiting (STATE-Q5 remediation), also configure rate limit response headers (`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After`) so agents can self-throttle.
- **Evidence**: No rate limit configuration found in any file

### STATE-Q3: Concurrency Controls ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The Camunda engine uses optimistic locking internally for all database operations. Concurrent updates to the same process instance or task are detected and rejected with an `OptimisticLockingException`. The `InvoiceTestCase.java` exercises concurrent-safe patterns through the standard engine APIs. However, no ETag or `If-Match` header support exists in the REST API for client-side concurrency control.
- **Implication**: For read-only agents, concurrency is not a concern. If scope expands to write-enabled, the engine's internal optimistic locking provides base-level protection, but REST API-level concurrency controls (ETags) would improve agent safety.
- **Recommendation**: No immediate action for read-only scope. Plan for ETag support on task completion endpoints if write-enabled scope is anticipated.
- **Evidence**: `examples/invoice/src/test/resources/camunda.cfg.xml` (engine configuration with implicit optimistic locking)

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits found. No maximum records per operation, no maximum spend per hour, and no per-agent operation limits are configured. The Camunda engine does not natively support agent-specific transaction limits.
- **Implication**: For read-only agents, blast radius is limited to query load (addressed by STATE-Q5/STATE-Q7). If scope expands to write-enabled, transaction limits become critical to prevent an agent from starting thousands of process instances or completing tasks in bulk.
- **Recommendation**: No immediate action for read-only scope. Plan for per-agent transaction limits at the API Gateway level if write scope is anticipated.
- **Evidence**: No transaction limit configuration found in any file

### HITL-Q1: Draft/Pending State ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The invoice process inherently supports pending/draft states through its BPMN user tasks. The "Approve Invoice" user task creates a pending state where the invoice awaits human approval before proceeding to bank transfer. The "Assign Reviewer" and "Review Invoice" tasks in the `ReviewInvoice` subprocess create additional approval gates. The `approved` variable (Boolean) explicitly controls whether the invoice proceeds or is sent for review. This is a robust human-in-the-loop pattern implemented via BPMN semantics.
- **Implication**: The invoice process already has strong HITL patterns. An agent reading task state can observe pending approvals. If write scope is enabled, an agent could create draft process instances and leave them for human approval.
- **Recommendation**: Document the existing HITL patterns as agent-ready capabilities. Consider exposing a "task recommendations" endpoint where an agent can suggest approval decisions that a human confirms.
- **Evidence**: `examples/invoice/src/main/resources/invoice.v2.bpmn` (approveInvoice user task, approved variable, review subprocess call activity)

### HITL-Q2: Configurable Approval Gates ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The BPMN process definition includes explicit, configurable approval gates. The "Approve Invoice" user task has candidate groups determined dynamically by the DMN business rule (`invoice-assign-approver`). The DMN decision table (`invoiceBusinessDecisions.dmn`) routes approvals based on invoice classification: day-to-day expenses go to accounting/sales, budget/exceptional items go to management. The `approved` variable controls flow direction. The `ReviewInvoice` call activity with `clarified` variable provides a secondary review gate. These gates are configurable via the DMN decision table without code changes.
- **Implication**: Approval gates are already configurable via DMN business rules. The rules-based routing (by invoice category and amount) could be extended to add agent-specific approval requirements (e.g., all agent-initiated changes require management approval).
- **Recommendation**: No immediate action. Consider adding an "agent-initiated" flag to the DMN decision table that routes all agent-triggered operations through mandatory human approval.
- **Evidence**: `examples/invoice/src/main/resources/invoiceBusinessDecisions.dmn` (approval routing rules), `examples/invoice/src/main/resources/invoice.v2.bpmn` (approval user tasks)

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Process variables use clear, human-readable, semantically meaningful names: `creditor`, `amount`, `invoiceCategory`, `invoiceNumber`, `invoiceDocument`, `approved`, `clarified`, `approverGroups`, `reviewer`. The `DemoDataGenerator.java` defines variable labels for task list display: `"amount" → "Invoice Amount"`, `"invoiceNumber" → "Invoice Number"`, `"creditor" → "Creditor"`, `"approver" → "Approver"`. The DMN decision table uses descriptive labels: "Invoice Amount", "Invoice Category", "Classification", "Approver Group". No legacy codes or abbreviations requiring a data dictionary.
- **Implication**: Field names are LLM-friendly and self-documenting. Agent tool definitions can use field names directly without translation. This accelerates agent tool authoring.
- **Recommendation**: No action needed. Maintain the current naming conventions for new process variables.
- **Evidence**: `examples/invoice/src/main/resources/invoice.v2.bpmn` (variable names), `examples/invoice/src/main/resources/invoiceBusinessDecisions.dmn` (decision table labels), `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/DemoDataGenerator.java` (variable labels)

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No formal data catalog or metadata layer exists. No AWS Glue Data Catalog, no Collibra/Alation/DataHub integration. The BPMN and DMN files serve as implicit metadata — the process definition documents what data flows through the system, and the DMN tables document business rule inputs/outputs. The OpenAPI spec templates document the REST API schema. However, no centralized metadata registry describes what data the invoice system holds and what it means.
- **Implication**: Agent tool builders must reverse-engineer data semantics from BPMN definitions, DMN tables, and the REST API spec. There is no single-pane-of-glass for data discovery.
- **Recommendation**: Consider publishing a data dictionary extracted from the BPMN/DMN definitions and process variable schemas. The BPMN data store reference ("Financial Accounting System") hints at integration points that should be documented.
- **Evidence**: `examples/invoice/src/main/resources/invoice.v2.bpmn` (process variable definitions), `examples/invoice/src/main/resources/invoiceBusinessDecisions.dmn` (decision input/output definitions)

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: The `InvoiceApplicationHelper.java` enables the Camunda engine's built-in metrics reporter: `processEngineConfiguration.setDbMetricsReporterActivate(true)` with reporter ID "REPORTER". The engine tracks operational metrics (job executions, decision evaluations, process instance starts). However, no custom business outcome metrics are published — no invoice approval rates, no average processing time, no rejection rate tracking, and no financial totals. No custom dashboards or KPI monitoring.
- **Implication**: The engine provides operational telemetry but not business intelligence. An agent's impact on invoice processing outcomes (faster approvals, different approval rates) would not be measurable with current metrics.
- **Recommendation**: Implement custom metrics for business outcomes: invoice approval rate, average time-to-approval, rejection rate, and average invoice amount. Publish to CloudWatch or a metrics service for agent impact measurement.
- **Evidence**: `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/InvoiceApplicationHelper.java` (dbMetricsReporter activation)

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality scores, completeness metrics, or data profiling exists. No null rate monitoring, no duplicate detection logic, no data freshness SLAs. The `start-form.html` enforces basic input validation (required fields, type checking for Double amount), but no server-side data quality validation exists beyond BPMN process variable types. The demo data in `InvoiceApplicationHelper.java` uses sample values that may not represent real-world data quality challenges.
- **Implication**: An agent reading invoice data has no signal about data completeness or quality. Incomplete process variables could lead to agent reasoning errors.
- **Recommendation**: Implement process variable validation in service tasks. Track data quality metrics (null rates, format compliance) for key process variables.
- **Evidence**: `examples/invoice/src/main/webapp/forms/start-form.html` (client-side validation), `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/InvoiceApplicationHelper.java` (demo data values)

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: BLOCKER (PASS — no gap found)
- **Finding**: The Camunda Platform 7 exposes a comprehensive REST API via the `engine-rest` module. The OpenAPI 3.0.2 specification template (`main.ftl`) defines 51 API tag categories covering all engine capabilities: Process Instance, Task, Decision Definition, Deployment, Authorization, Group, User, Variable Instance, Execution, External Task, Filter, Job, Message, Metrics, Migration, and more. The invoice process is fully consumable via this REST API — agents can start process instances, query tasks, read process variables, and monitor process state through standard HTTP endpoints. No direct database access, file-based exchange, or UI automation is required.
- **Gap**: No gap. The REST API provides a documented, stable integration surface.
- **Recommendation**: No remediation needed. Document the specific REST API endpoints relevant to the invoice process for agent tool definitions.
- **Evidence**: `engine-rest/engine-rest-openapi/src/main/templates/main.ftl` (comprehensive REST API with 51 tags), `examples/invoice/src/main/resources/invoice.v2.bpmn` (process definition consumable via REST API)

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK-QUALITY
- **Finding**: OpenAPI 3.0.2 specification exists as FreeMarker templates requiring a build step to produce the final spec. Comprehensive but not directly consumable.
- **Gap**: Spec requires build to materialize. Not available as a static file for agent framework auto-generation.
- **Recommendation**: Generate and publish the final OpenAPI JSON as a static artifact.
- **Evidence**: `engine-rest/engine-rest-openapi/src/main/templates/main.ftl`, `engine-rest/engine-rest-openapi/src/main/openapi/schema.json`

#### API-Q3: Structured Error Responses
- **Severity**: RISK-QUALITY
- **Finding**: REST API defines ExceptionDto with type, message, and code fields. No retryable boolean or error category.
- **Gap**: Agents cannot programmatically distinguish retriable vs terminal errors.
- **Recommendation**: Add retryable boolean and error category enum to error DTOs.
- **Evidence**: `engine-rest/engine-rest-openapi/src/main/templates/main.ftl` (error schemas), `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/service/ArchiveInvoiceService.java` (generic exception)

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No idempotency key support in write endpoints. Duplicate POSTs would create duplicate process instances.
- **Gap**: No idempotency mechanism exists. Informational for read-only scope.
- **Recommendation**: Plan for idempotency keys on write endpoints if write scope is anticipated.
- **Evidence**: `engine-rest/engine-rest-openapi/src/main/templates/main.ftl`

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: JSON responses throughout the REST API. Binary content via multipart form data.
- **Gap**: No gap. JSON is well-suited for agent consumption.
- **Recommendation**: Consider summarization endpoint for binary invoice documents.
- **Evidence**: `engine-rest/engine-rest-openapi/src/main/templates/main.ftl`

#### API-Q6: Asynchronous Operation Support
- **Severity**: RISK-QUALITY
- **Trigger**: Orchestrator with long-running workflows
- **Finding**: Long-running human tasks. REST API supports polling-based async (start → poll → complete). ArchiveInvoiceService is async-capable (`camunda:async="true"`). No webhook or push notification mechanism.
- **Gap**: No push notification for state changes. Polling only.
- **Recommendation**: Implement webhook/SNS notifications for process state transitions.
- **Evidence**: `examples/invoice/src/main/resources/invoice.v2.bpmn`, `engine-rest/engine-rest-openapi/src/main/templates/main.ftl`

#### API-Q7: Event Emission for State Changes
- **Severity**: INFO
- **Trigger**: Orchestrator has state changes
- **Finding**: Engine supports event subscriptions and message correlation. No webhook/SNS/EventBridge integration for push notifications.
- **Gap**: No event emission to external consumers. Polling required.
- **Recommendation**: Implement task/execution listeners that publish events to SNS/EventBridge.
- **Evidence**: `examples/invoice/src/main/resources/invoice.v2.bpmn`, `engine-rest/engine-rest-openapi/src/main/templates/main.ftl`

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit documentation or headers. No API Gateway throttle settings.
- **Gap**: Agents cannot self-throttle without external rate limit signals.
- **Recommendation**: Configure rate limit response headers when implementing STATE-Q5 remediation.
- **Evidence**: No rate limit configuration found

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER (PASS — basic auth meets minimum)
- **Finding**: The Camunda REST API supports basic HTTP authentication as defined in the OpenAPI spec security scheme (`"basicAuth": {"type": "http", "scheme": "basic"}`). A dedicated service user (e.g., "agent-service") can be created via the Identity API and used for machine-to-machine authentication. The authenticated principal (username) is attributed in the Camunda User Operation Log for all operations. While not as robust as OAuth 2.0 client credentials or mTLS, basic auth with a dedicated service account does provide machine identity with principal attribution.
- **Gap**: No gap for minimum requirement. Basic auth with dedicated service user provides attributable machine identity. However, basic auth transmits credentials in every request (base64-encoded, not encrypted without TLS) and does not support token expiration or rotation without password changes.
- **Recommendation**: Upgrade to OAuth 2.0 client credentials or API key authentication via an API Gateway for production agent deployments. Enforce TLS to protect basic auth credentials in transit.
- **Evidence**: `engine-rest/engine-rest-openapi/src/main/templates/main.ftl` (basicAuth security scheme), `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/DemoDataGenerator.java` (user creation via Identity API)

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK-SAFETY (PASS — scoped permissions exist)
- **Finding**: The Camunda authorization model supports fine-grained scoped permissions. `DemoDataGenerator.java` demonstrates: group-based authorization (sales, accounting, management), resource-type restrictions (PROCESS_DEFINITION, APPLICATION, FILTER, TASK, USER), resource-instance restrictions (e.g., `salesReadProcessDefinition.setResourceId("invoice")` restricts sales group to the invoice process definition only), and action-level permissions (READ, READ_HISTORY, ACCESS, UPDATE, ALL). An agent service account can be created with read-only permissions on specific process definitions.
- **Gap**: No gap for the base requirement. The authorization model supports least-privilege scoping. However, the camunda-admin group has `ALL` permissions on all resources — any agent identity in this group would have unrestricted access.
- **Recommendation**: Create a dedicated agent group with read-only permissions on the invoice process definition. Never assign agent identities to the camunda-admin group.
- **Evidence**: `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/DemoDataGenerator.java` (scoped permissions)

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK-SAFETY (PASS — action-level auth exists)
- **Finding**: The authorization model explicitly supports action-level permissions. `DemoDataGenerator.java` shows: READ permission (read process definitions), READ_HISTORY permission (view process history), ACCESS permission (access applications), UPDATE permission (modify tasks), and ALL permission (unrestricted). These are granular — an agent can be granted READ without UPDATE, effectively creating a read-only identity at the authorization level.
- **Gap**: No gap. Action-level authorization is a core capability of the Camunda authorization framework.
- **Recommendation**: Define an "agent-reader" authorization template that grants only READ and READ_HISTORY on the invoice process definition and related resources.
- **Evidence**: `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/DemoDataGenerator.java` (action-level permissions)

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: RISK-QUALITY
- **Finding**: Basic auth only. `setAuthentication()` and `setAuthenticatedUserId()` exist but no JWT/OAuth2 delegation. No distinction between agent-as-self vs agent-on-behalf-of-user.
- **Gap**: No identity propagation or delegation capability.
- **Recommendation**: Implement API Gateway with JWT/OAuth2 supporting user delegation claims.
- **Evidence**: `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/InvoiceApplicationHelper.java`, `engine-rest/engine-rest-openapi/src/main/templates/main.ftl`

#### AUTH-Q5: Credential Management
- **Severity**: RISK-QUALITY
- **Finding**: Hardcoded demo credentials in DemoDataGenerator. Vault used in CI/CD only. No production secrets management.
- **Gap**: No secrets management for application credentials.
- **Recommendation**: Integrate AWS Secrets Manager or HashiCorp Vault for production credentials.
- **Evidence**: `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/DemoDataGenerator.java`, `Jenkinsfile`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: Camunda User Operation Log exists but is mutable. No CloudTrail, no immutable log storage.
- **Gap**: Audit logs are not immutable or tamper-evident.
- **Recommendation**: Export operation logs to immutable storage (S3 with Object Lock).
- **Evidence**: `examples/invoice/src/test/resources/camunda.cfg.xml`, `Jenkinsfile`

---

## Evidence Index

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `engine-rest/engine-rest-openapi/src/main/templates/main.ftl` | API-Q1, API-Q2, API-Q3, API-Q4, API-Q5, API-Q6, API-Q7, API-Q8, AUTH-Q1, AUTH-Q4, DISC-Q1, STATE-Q2, DATA-Q3 |
| `engine-rest/engine-rest-openapi/src/main/openapi/schema.json` | API-Q2 |

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/DemoDataGenerator.java` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q5, AUTH-Q7, DATA-Q1, DISC-Q2 |
| `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/InvoiceApplicationHelper.java` | AUTH-Q4, DATA-Q1, DATA-Q5, DATA-Q7, OBS-Q3 |
| `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/InvoiceProcessApplication.java` | API-Q1 |
| `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/service/NotifyCreditorService.java` | API-Q3, DATA-Q6, OBS-Q1 |
| `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/service/ArchiveInvoiceService.java` | API-Q3, STATE-Q1, STATE-Q4, DATA-Q6, OBS-Q1 |
| `examples/invoice/src/test/java/org/camunda/bpm/example/invoice/InvoiceTestCase.java` | ENG-Q4 |

### Process Definitions (BPMN/DMN)
| File | Questions Referenced |
|------|---------------------|
| `examples/invoice/src/main/resources/invoice.v2.bpmn` | API-Q1, API-Q6, API-Q7, STATE-Q1, STATE-Q4, HITL-Q1, HITL-Q2, DATA-Q1, DATA-Q4, DISC-Q1, DISC-Q2 |
| `examples/invoice/src/main/resources/invoice.v1.bpmn` | API-Q1, DISC-Q1 |
| `examples/invoice/src/main/resources/reviewInvoice.bpmn` | HITL-Q1 |
| `examples/invoice/src/main/resources/invoiceBusinessDecisions.dmn` | HITL-Q2, DISC-Q2, DISC-Q3 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `Jenkinsfile` | AUTH-Q5, AUTH-Q6, STATE-Q7, OBS-Q1, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4, ENG-Q5, DISC-Q1 |
| `.github/workflows/codeql.yml` | ENG-Q2 |
| `.github/workflows/java-dependency-check.yml` | ENG-Q2 |
| `.github/renovate.json5` | ENG-Q2 |
| `.snyk` | ENG-Q2 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `examples/invoice/src/test/resources/camunda.cfg.xml` | AUTH-Q6, STATE-Q3, HITL-Q3, ENG-Q5 |
| `examples/invoice/src/main/resources/META-INF/processes.xml` | API-Q1 |
| `examples/invoice/pom.xml` | API-Q1 |

### Web Resources
| File | Questions Referenced |
|------|---------------------|
| `examples/invoice/src/main/webapp/forms/start-form.html` | DATA-Q1, DATA-Q7 |
| `examples/invoice/src/main/webapp/forms/approve-invoice.html` | HITL-Q1 |

### Security and Documentation
| File | Questions Referenced |
|------|---------------------|
| `SECURITY.md` | DATA-Q2 |

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK-SAFETY
- **Finding**: User deletion/disabling possible via Camunda Identity API. No automated suspension mechanism.
- **Gap**: No automated or immediate suspension capability.
- **Recommendation**: Implement API Gateway with API key management for instant revocation.
- **Evidence**: `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/DemoDataGenerator.java`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No BPMN compensation handlers. No explicit rollback logic. ArchiveInvoiceService has shouldFail but no compensating action.
- **Gap**: No compensation or rollback for failed multi-step operations.
- **Recommendation**: Add BPMN compensation boundary events. Implement saga pattern.
- **Evidence**: `examples/invoice/src/main/resources/invoice.v2.bpmn`, `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/service/ArchiveInvoiceService.java`

#### STATE-Q2: Queryable Current State
- **Severity**: RISK-QUALITY (PASS)
- **Trigger**: Orchestrator has persistent state
- **Finding**: The Camunda REST API provides comprehensive state query capabilities: process instance queries (by key, ID, variables), task queries (by assignee, candidate groups, process instance), variable queries, history queries, and job queries. All process state is queryable through well-documented REST endpoints. An agent can inspect the current state of any invoice process instance before taking action.
- **Gap**: No gap. State is fully queryable via the REST API.
- **Recommendation**: No remediation needed. Document the most relevant query endpoints for agent tool definitions.
- **Evidence**: `engine-rest/engine-rest-openapi/src/main/templates/main.ftl` (Process Instance, Task, Variable Instance tags)

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Camunda engine uses optimistic locking internally. No REST API-level ETags.
- **Gap**: Informational for read-only scope. Engine-level optimistic locking provides base protection.
- **Recommendation**: Plan for ETag support if write scope is anticipated.
- **Evidence**: `examples/invoice/src/test/resources/camunda.cfg.xml`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK-SAFETY (PASS — limited external dependencies)
- **Trigger**: Orchestrator with external dependencies (call activity)
- **Finding**: The invoice service tasks (`NotifyCreditorService`, `ArchiveInvoiceService`) are simple Java delegates that log messages — they do not make external HTTP calls or connect to external services. The `ReviewInvoice` call activity is an internal subprocess within the same engine instance, not an external service call. The BPMN data store reference "Financial Accounting System" is a modeling element — no actual external system integration exists in the code. Therefore, circuit breakers are not needed for the current implementation.
- **Gap**: No gap for current implementation. However, the service task stubs suggest future integration points (notify creditor, archive invoice) that would require resilience patterns when connected to real external services.
- **Recommendation**: When implementing actual external service integrations in NotifyCreditorService and ArchiveInvoiceService, add circuit breakers, retry logic with exponential backoff, and timeout configurations.
- **Evidence**: `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/service/NotifyCreditorService.java` (stub), `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/service/ArchiveInvoiceService.java` (stub), `examples/invoice/src/main/resources/invoice.v2.bpmn` (call activity to internal subprocess)

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK-SAFETY
- **Finding**: No rate limiting found. No API Gateway, no WAF, no application-level rate limiting.
- **Gap**: No protection against runaway agent loops.
- **Recommendation**: Deploy API Gateway with per-identity rate limits.
- **Evidence**: No rate limiting configuration found

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits. No per-agent operation limits.
- **Gap**: Informational for read-only scope.
- **Recommendation**: Plan for per-agent transaction limits if write scope is anticipated.
- **Evidence**: No transaction limit configuration found

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: RISK-QUALITY
- **Trigger**: P0 priority service
- **Finding**: No load testing, no auto-scaling, no capacity planning documentation.
- **Gap**: Infrastructure not validated for agent traffic patterns.
- **Recommendation**: Conduct load testing with agent-like traffic patterns.
- **Evidence**: `Jenkinsfile` (no load test stages)

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: BPMN user tasks provide inherent pending/draft states. Approve Invoice task creates approval gate.
- **Gap**: Informational. Strong HITL patterns already exist.
- **Recommendation**: Document existing HITL patterns as agent-ready capabilities.
- **Evidence**: `examples/invoice/src/main/resources/invoice.v2.bpmn`

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: DMN business rules configure approval routing. Gates are configurable without code changes.
- **Gap**: Informational. Approval gates are already configurable.
- **Recommendation**: Consider adding agent-specific routing rules to DMN table.
- **Evidence**: `examples/invoice/src/main/resources/invoiceBusinessDecisions.dmn`, `examples/invoice/src/main/resources/invoice.v2.bpmn`

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK-QUALITY
- **Finding**: In-memory engine for testing, DemoDataGenerator for seed data. No dedicated staging environment.
- **Gap**: No production-equivalent sandbox for agent integration testing.
- **Recommendation**: Create Docker Compose configuration for repeatable sandbox.
- **Evidence**: `examples/invoice/src/test/resources/camunda.cfg.xml`, `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/DemoDataGenerator.java`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: Invoice data (creditor names, amounts, invoice numbers, PDF documents, user emails) is not classified at field level. No data classification tags, no Macie integration.
- **Gap**: No field-level data classification for any invoice process data.
- **Recommendation**: Create data classification inventory. Implement classification-based access controls.
- **Evidence**: `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/DemoDataGenerator.java`, `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/InvoiceApplicationHelper.java`, `examples/invoice/src/main/webapp/forms/start-form.html`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK-SAFETY
- **Conditional**: agent_scope is "read-only" — evaluated as RISK-SAFETY
- **Finding**: No data residency configuration. European business data (Camunda GmbH is Germany-based) with potential GDPR implications.
- **Gap**: No explicit data residency controls.
- **Recommendation**: Document data residency requirements. Restrict agent LLM calls to EU-region endpoints.
- **Evidence**: `SECURITY.md`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK-QUALITY (PASS)
- **Trigger**: Orchestrator with query endpoints
- **Finding**: The Camunda REST API supports comprehensive query capabilities: pagination (`firstResult`, `maxResults`), filtering (by process definition key, assignee, candidate groups, variable values), and sorting (`sortBy`, `sortOrder`). Task queries, process instance queries, and history queries all support these parameters. The OpenAPI spec documents these parameters across all query endpoints. An agent can request exactly the data it needs without retrieving unbounded result sets.
- **Gap**: No gap. Selective query support is comprehensive.
- **Recommendation**: No remediation needed. Document recommended query parameters for agent tool definitions (e.g., always set maxResults).
- **Evidence**: `engine-rest/engine-rest-openapi/src/main/templates/main.ftl` (pagination and filter parameters)

#### DATA-Q4: System of Record Designations
- **Severity**: RISK-QUALITY
- **Trigger**: Orchestrator has persistent state
- **Finding**: "Financial Accounting System" data store referenced but no SoR designations. Camunda is SoR for process state only.
- **Gap**: No explicit system-of-record designations.
- **Recommendation**: Document SoR designations for all key business entities.
- **Evidence**: `examples/invoice/src/main/resources/invoice.v2.bpmn`

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: RISK-QUALITY
- **Trigger**: Orchestrator has persistent state
- **Finding**: Engine tracks timestamps internally. No Cache-Control or freshness headers in API responses.
- **Gap**: API does not signal data freshness to consumers.
- **Recommendation**: Add Cache-Control and freshness headers to REST API responses.
- **Evidence**: `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/InvoiceApplicationHelper.java`

#### DATA-Q6: PII Redaction in Logs
- **Severity**: RISK-SAFETY
- **Finding**: Creditor names and invoice numbers logged in plaintext without redaction.
- **Gap**: PII leaks into logs.
- **Recommendation**: Implement logging wrapper that masks PII fields.
- **Evidence**: `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/service/NotifyCreditorService.java`, `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/service/ArchiveInvoiceService.java`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality scores or completeness metrics. Basic client-side validation only.
- **Gap**: No data quality signaling.
- **Recommendation**: Implement process variable validation and quality metrics.
- **Evidence**: `examples/invoice/src/main/webapp/forms/start-form.html`, `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/InvoiceApplicationHelper.java`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK-QUALITY
- **Finding**: BPMN versionTag (V1.0, V2.0), OpenAPI versioned with cambpmVersion, engine-api-compatibility check in CI. No consumer-driven contract tests or OpenAPI diff.
- **Gap**: API compatibility checking exists for Java API but not REST API. No breaking change detection for agent-facing endpoints.
- **Recommendation**: Add OpenAPI spec diff to CI. Implement Pact contract tests.
- **Evidence**: `examples/invoice/src/main/resources/invoice.v2.bpmn`, `engine-rest/engine-rest-openapi/src/main/templates/main.ftl`, `Jenkinsfile`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: All variable names are human-readable and semantically meaningful. DMN labels are descriptive. No legacy codes.
- **Gap**: No gap. Field names are LLM-friendly.
- **Recommendation**: Maintain current naming conventions.
- **Evidence**: `examples/invoice/src/main/resources/invoice.v2.bpmn`, `examples/invoice/src/main/resources/invoiceBusinessDecisions.dmn`, `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/DemoDataGenerator.java`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal data catalog. BPMN/DMN files serve as implicit metadata.
- **Gap**: No centralized data discovery mechanism.
- **Recommendation**: Publish data dictionary from BPMN/DMN definitions.
- **Evidence**: `examples/invoice/src/main/resources/invoice.v2.bpmn`, `examples/invoice/src/main/resources/invoiceBusinessDecisions.dmn`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK-QUALITY
- **Finding**: java.util.logging with unstructured messages. No OpenTelemetry, no X-Ray, no JSON logs, no correlation IDs.
- **Gap**: Agent-initiated requests cannot be traced end-to-end.
- **Recommendation**: Integrate OpenTelemetry. Configure JSON structured logging.
- **Evidence**: `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/service/NotifyCreditorService.java`, `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/service/ArchiveInvoiceService.java`, `Jenkinsfile`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK-QUALITY
- **Finding**: No alerting configuration found. No CloudWatch alarms, no PagerDuty/OpsGenie.
- **Gap**: No automated detection of API degradation.
- **Recommendation**: Deploy CloudWatch alarms on REST API error rate and latency.
- **Evidence**: No alerting configuration found

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: dbMetricsReporter provides operational metrics. No custom business outcome metrics.
- **Gap**: No business outcome visibility for measuring agent impact.
- **Recommendation**: Implement custom metrics for invoice processing outcomes.
- **Evidence**: `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/InvoiceApplicationHelper.java`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance
- **Severity**: RISK-QUALITY
- **Finding**: No IaC found. Infrastructure not defined as code, not peer-reviewed, not monitored for drift.
- **Gap**: Agent-facing integration surface is not governed by code.
- **Recommendation**: Define Camunda Platform deployment infrastructure as IaC.
- **Evidence**: No IaC files found, `Jenkinsfile`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK-QUALITY
- **Finding**: Comprehensive CI/CD with engine-api-compatibility, CodeQL, Renovate. No REST API contract testing.
- **Gap**: No breaking change detection for REST API.
- **Recommendation**: Add OpenAPI spec diff and Pact contract tests.
- **Evidence**: `Jenkinsfile`, `.github/workflows/codeql.yml`, `.github/workflows/java-dependency-check.yml`, `.github/renovate.json5`, `.snyk`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK-QUALITY
- **Finding**: No blue/green, no canary, no feature flags, no rollback mechanism. Deploys to Nexus only.
- **Gap**: No defined rollback capability for production deployments.
- **Recommendation**: Implement blue/green or canary deployments with automated rollback.
- **Evidence**: `Jenkinsfile`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK-QUALITY
- **Finding**: 4 process test methods in InvoiceTestCase.java (Java API only). No REST API-level tests for invoice workflow.
- **Gap**: No REST API test coverage for agent-facing endpoints.
- **Recommendation**: Add REST API integration tests for the invoice process.
- **Evidence**: `examples/invoice/src/test/java/org/camunda/bpm/example/invoice/InvoiceTestCase.java`

#### ENG-Q5: Encryption at Rest
- **Severity**: RISK-QUALITY
- **Trigger**: Orchestrator has persistent data stores
- **Finding**: No encryption at rest configuration. Process data persisted to database without encryption config in this repo.
- **Gap**: No encryption-at-rest governance in this codebase.
- **Recommendation**: Define database encryption in IaC. Enable RDS encryption with KMS.
- **Evidence**: `examples/invoice/src/test/resources/camunda.cfg.xml`, `Jenkinsfile`

---

## Evidence Index

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `engine-rest/engine-rest-openapi/src/main/templates/main.ftl` | API-Q1, API-Q2, API-Q3, API-Q4, API-Q5, API-Q6, API-Q7, API-Q8, AUTH-Q1, AUTH-Q4, DISC-Q1, STATE-Q2, DATA-Q3 |
| `engine-rest/engine-rest-openapi/src/main/openapi/schema.json` | API-Q2 |

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/DemoDataGenerator.java` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q5, AUTH-Q7, DATA-Q1, DISC-Q2 |
| `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/InvoiceApplicationHelper.java` | AUTH-Q4, DATA-Q1, DATA-Q5, DATA-Q7, OBS-Q3 |
| `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/InvoiceProcessApplication.java` | API-Q1 |
| `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/service/NotifyCreditorService.java` | API-Q3, DATA-Q6, OBS-Q1 |
| `examples/invoice/src/main/java/org/camunda/bpm/example/invoice/service/ArchiveInvoiceService.java` | API-Q3, STATE-Q1, STATE-Q4, DATA-Q6, OBS-Q1 |
| `examples/invoice/src/test/java/org/camunda/bpm/example/invoice/InvoiceTestCase.java` | ENG-Q4 |

### Process Definitions (BPMN/DMN)
| File | Questions Referenced |
|------|---------------------|
| `examples/invoice/src/main/resources/invoice.v2.bpmn` | API-Q1, API-Q6, API-Q7, STATE-Q1, STATE-Q4, HITL-Q1, HITL-Q2, DATA-Q1, DATA-Q4, DISC-Q1, DISC-Q2 |
| `examples/invoice/src/main/resources/invoice.v1.bpmn` | API-Q1, DISC-Q1 |
| `examples/invoice/src/main/resources/reviewInvoice.bpmn` | HITL-Q1 |
| `examples/invoice/src/main/resources/invoiceBusinessDecisions.dmn` | HITL-Q2, DISC-Q2, DISC-Q3 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `Jenkinsfile` | AUTH-Q5, AUTH-Q6, STATE-Q7, OBS-Q1, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4, ENG-Q5, DISC-Q1 |
| `.github/workflows/codeql.yml` | ENG-Q2 |
| `.github/workflows/java-dependency-check.yml` | ENG-Q2 |
| `.github/renovate.json5` | ENG-Q2 |
| `.snyk` | ENG-Q2 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `examples/invoice/src/test/resources/camunda.cfg.xml` | AUTH-Q6, STATE-Q3, HITL-Q3, ENG-Q5 |
| `examples/invoice/src/main/resources/META-INF/processes.xml` | API-Q1 |
| `examples/invoice/pom.xml` | API-Q1 |

### Web Resources
| File | Questions Referenced |
|------|---------------------|
| `examples/invoice/src/main/webapp/forms/start-form.html` | DATA-Q1, DATA-Q7 |
| `examples/invoice/src/main/webapp/forms/approve-invoice.html` | HITL-Q1 |

### Security and Documentation
| File | Questions Referenced |
|------|---------------------|
| `SECURITY.md` | DATA-Q2 |
