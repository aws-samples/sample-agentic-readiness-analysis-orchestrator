# Portfolio Agentic Readiness Analysis Report

**Date**: 2025-07-17
**Services Analyzed**: 5
**Portfolio Context**: Demonstrating BPMN agentic opportunity analysis across official open source process repositories covering invoice processing, order management, and BPMN interchange test cases.

---

## Executive Dashboard

### Readiness Distribution

| Profile | Services | Percentage | Description |
|---------|----------|------------|-------------|
| ✅ Agent-Ready | 0 | 0% | 0 blockers, 0 RISK-SAFETY — broad agent deployment |
| 🟡 Pilot-Ready | 0 | 0% | 0 blockers, 1–2 RISK-SAFETY — narrow pilot |
| 🟡 Pilot-Ready (Safety Concerns) | 0 | 0% | 0 blockers, 3+ RISK-SAFETY — supervised pilot, prioritize safety |
| 🟠 Remediation Required | 2 | 40% | 1–2 blockers — remediate before any agent deployment |
| ❌ Not Agent-Integrable | 3 | 60% | 3+ blockers — deferred or descoped |

### Portfolio Summary

| Metric | Value |
|--------|-------|
| Total Services Analyzed | 5 |
| Services Ready for Agents (Agent-Ready + Pilot-Ready) | 0 (0%) |
| Services Requiring Remediation | 5 (100%) |
| Cross-Cutting BLOCKERs (same blocker in 2+ repos) | 3 |
| Cross-Cutting RISKs (same risk in 3+ repos) | 22 |
| Services with Write-Enabled Agent Scope | 0 (0%) |
| Services with Read-Only Agent Scope | 5 (100%) |

### Repo Type Distribution

| Repo Type | Count | Percentage |
|-----------|-------|------------|
| application | 3 | 60% |
| monorepo | 2 | 40% |
| infrastructure-only | 0 | 0% |
| deployment-config | 0 | 0% |
| library | 0 | 0% |

### Blocker Heatmap by Section

| Section | Repos Blocked | % of Applicable Repos | Top Blockers |
|---------|--------------|----------------------|--------------|
| DATA | 5 / 5 | 100% | DATA-Q1 |
| AUTH | 4 / 5 | 80% | AUTH-Q1 |
| API | 3 / 5 | 60% | API-Q1 |
| STATE | 0 / 5 | 0% | — |
| HITL | 0 / 5 | 0% | — |
| DISC | 0 / 5 | 0% | — |
| OBS | 0 / 5 | 0% | — |
| ENG | 0 / 5 | 0% | — |

### Readiness Snapshot

| Metric | Value |
|--------|-------|
| analysis_date | 2025-07-17 |
| total_services | 5 |
| agent_ready | 0 |
| pilot_ready | 0 |
| pilot_ready_safety_concerns | 0 |
| remediation_required | 2 |
| not_integrable | 3 |
| total_blockers | 12 |
| total_risks | 113 |
| total_risk_safety | 41 |
| total_risk_quality | 72 |
| total_infos | 61 |
| cross_cutting_blockers | 3 |
| cross_cutting_risks | 22 |
| cross_cutting_risk_safety | 8 |
| cross_cutting_risk_quality | 14 |
| portfolio_level_blockers | 1 |
| portfolio_level_risks | 4 |
| write_enabled_services | 0 |
| read_only_services | 5 |
## Cross-Cutting BLOCKERs — Same Blocker in 2+ Repos

> These are BLOCKER-severity questions that appear in 2 or more repositories.
> They represent portfolio-wide agentic readiness gaps requiring coordinated remediation.
> Questions scored as N/A for a service do not count as gaps for that service.

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER in 4 of 5 applicable services
- **Affected Services**: camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples
- **Common Finding**: None of the 4 affected services have machine identity authentication for inbound agent requests. camunda8-order-process and bpmn-miwg-test-suite have no API surface at all (no inbound auth possible). camunda-rest-service and camunda-bpm-examples use hardcoded shared credentials (`demo:demo`) with no principal attribution. camunda-invoice (not affected) has basic auth via the Camunda REST API security scheme that meets the minimum requirement.
- **Root Cause Pattern**: These are open-source example/demo repositories not designed for production deployment. No identity provider (Cognito, Okta) is integrated in any service. Two services have no API surface to authenticate against, and two use demo-grade shared credentials.
- **Portfolio-Level Remediation**:
  - **Approach**: Hybrid — deploy a centralized identity provider (platform-level), then integrate each service (per-service)
  - **Immediate Action**: Deploy a shared Cognito User Pool or Okta tenant for the portfolio. Create per-agent OAuth2 client credentials.
  - **Target State**: Each agent authenticates via unique OAuth2 client credentials. Audit logs record the specific agent principal for every request across all services.
  - **Estimated Effort**: High
  - **Priority**: Critical — identity is the foundation for all other security controls (AUTH-Q2, AUTH-Q6, AUTH-Q7 all depend on this)
  - **Dependencies**: None — this is the first thing to fix. API-Q1 must be resolved concurrently for services that lack an API surface (camunda8-order-process, bpmn-miwg-test-suite).

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER in 5 of 5 applicable services
- **Affected Services**: camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples
- **Common Finding**: No data classification scheme exists in any service. camunda-invoice handles creditor names, invoice amounts, and user emails without classification. camunda8-order-process has PII (email addresses) hardcoded in DMN tables and plaintext credentials in config. camunda-rest-service stores process variables (GitHub repo data, user inputs) in H2 without classification. bpmn-miwg-test-suite contains maintainer email addresses in JSON files without classification tags. camunda-bpm-examples stores invoice data, approval data, and tenant-specific process variables without classification metadata.
- **Root Cause Pattern**: None of the repositories were designed with data governance in mind. Data classification is absent at every level — no field-level tags, no data dictionaries, no PII detection tools, no classification policies. Data flows from user inputs and external APIs into process engines and databases with zero sensitivity awareness.
- **Portfolio-Level Remediation**:
  - **Approach**: Hybrid — establish a portfolio-wide data classification taxonomy (platform-level), then apply field-level classification per service (per-service)
  - **Immediate Action**: Create a shared data classification taxonomy (Public, Internal, Confidential, Restricted). Inventory all data fields across all 5 services and assign classifications.
  - **Target State**: Every process variable, API response field, and stored data element has classification metadata. Access controls enforce classification-based restrictions (e.g., Confidential fields require elevated permissions).
  - **Estimated Effort**: Medium
  - **Priority**: Critical — affects all 5 services. Required before agents can safely read any process data.
  - **Dependencies**: AUTH-Q2 (scoped permissions needed to enforce classification-based access controls)

### API-Q1: Documented API Interface

- **Severity**: BLOCKER in 3 of 5 applicable services
- **Affected Services**: camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite
- **Common Finding**: Three services lack a documented, addressable API surface for agent integration. camunda8-order-process is a Zeebe job worker with no HTTP endpoints — it only pulls jobs from the Camunda 8 engine. camunda-rest-service exposes the generic Camunda engine REST API at `/engine-rest` but has no business-specific API facade. bpmn-miwg-test-suite is a static data archive with no application runtime. camunda-invoice (not affected) has a comprehensive REST API via the engine-rest module with OpenAPI templates. camunda-bpm-examples (not affected — INFO) exposes the Camunda REST API via Spring Boot starters.
- **Root Cause Pattern**: Two services (camunda8-order-process, bpmn-miwg-test-suite) are architecturally not designed as API services — one is a job worker, the other is a data archive. camunda-rest-service has an API but it's the generic Camunda platform API, not a business-specific interface.
- **Portfolio-Level Remediation**:
  - **Approach**: Per-service — each service needs a different API strategy based on its architecture
  - **Immediate Action**: For camunda8-order-process: expose a thin REST API layer wrapping key Zeebe operations. For camunda-rest-service: create a business facade REST API abstracting Camunda internals. For bpmn-miwg-test-suite: build a read-only API service over the BPMN reference data if agentic access is needed.
  - **Target State**: Each service exposes a documented, versioned REST API with business-meaningful endpoints and OpenAPI specification.
  - **Estimated Effort**: High (each service needs API development)
  - **Priority**: High
  - **Dependencies**: AUTH-Q1 (new API surfaces need machine identity authentication from the start)
## Cross-Cutting RISKs

### Cross-Cutting RISK-SAFETY — Same Safety Risk in 3+ Repos

> These are RISK-SAFETY questions that appear in 3 or more repositories.
> They represent portfolio-wide agent safety gaps requiring coordinated attention.
> Questions scored as N/A for a service do not count as gaps for that service.

#### AUTH-Q2: Scoped Permissions (Least Privilege)

- **Severity**: RISK-SAFETY in 5 of 5 applicable services
- **Affected Services**: camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples
- **Common Finding**: No scoped permission model exists in any service. Services use either single shared credentials with full access or have no authentication at all. No IAM policies, role definitions, or resource-level access restrictions.
- **Compensating Controls**: Deploy API Gateways restricting agent access to GET-only endpoints. Configure Camunda's built-in authorization service (where applicable) with agent-specific read-only roles.
- **Portfolio-Level Recommendation**: Establish a portfolio-wide RBAC standard for agent identities. Define an "agent-reader" role template with read-only permissions that can be deployed consistently across all Camunda-based services.
- **Estimated Effort**: Medium

#### AUTH-Q3: Action-Level Authorization

- **Severity**: RISK-SAFETY in 5 of 5 applicable services
- **Affected Services**: camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples
- **Common Finding**: No action-level authorization (ABAC or fine-grained RBAC) implemented in any service. No method-level authorization checks in source code. No middleware enforcing read/write/delete distinctions.
- **Compensating Controls**: Restrict agent access to specific API Gateway routes (GET endpoints only). Use Camunda authorization API to define permission grants per resource type and action.
- **Portfolio-Level Recommendation**: Implement Camunda authorization templates with action-level grants (READ, CREATE, UPDATE, DELETE) per resource type. Apply consistently across all Camunda 7 services.
- **Estimated Effort**: Medium

#### AUTH-Q6: Immutable Audit Logging

- **Severity**: RISK-SAFETY in 5 of 5 applicable services
- **Affected Services**: camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples
- **Common Finding**: No immutable audit logging in any service. No CloudTrail, no S3 with Object Lock, no CloudWatch log retention policies. Camunda engine history (where applicable) uses the same mutable database. bpmn-miwg-test-suite has no application runtime to log.
- **Compensating Controls**: Export Camunda User Operation Logs to immutable external stores. Enable Git audit logs at the organization level for bpmn-miwg-test-suite.
- **Portfolio-Level Recommendation**: Deploy a centralized immutable log aggregation system (CloudWatch Logs with retention lock or S3 with Object Lock) shared across all services. Standardize structured audit log format with principal, action, resource, and timestamp fields.
- **Estimated Effort**: Medium

#### AUTH-Q7: Agent Identity Suspension

- **Severity**: RISK-SAFETY in 5 of 5 applicable services
- **Affected Services**: camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples
- **Common Finding**: No mechanism to suspend or revoke individual agent identities in any service. All services either have no identity management at all or use a single shared credential.
- **Compensating Controls**: Implement API Gateway with per-agent API keys that can be individually revoked. Use network-level controls (security groups) to block agent access if needed.
- **Portfolio-Level Recommendation**: Implement a centralized agent identity registry (Cognito User Pool or API key management) with portfolio-wide suspension capability. This depends on AUTH-Q1 resolution.
- **Estimated Effort**: Medium

#### STATE-Q1: Compensation and Rollback

- **Severity**: RISK-SAFETY in 5 of 5 applicable services
- **Affected Services**: camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples
- **Common Finding**: No compensation or rollback mechanisms in any service. All services are read-only scope (conditional BLOCKER resolved as RISK-SAFETY). Camunda engine provides some BPMN-level error handling but no application-level compensation. bpmn-miwg-test-suite has no runtime to compensate.
- **Compensating Controls**: Read-only agent scope limits rollback risk. Camunda's job retry mechanism provides partial recovery for engine-managed operations.
- **Portfolio-Level Recommendation**: For read-only scope, this is lower priority. If any service upgrades to write-enabled scope, implement BPMN compensation events and saga patterns before expanding.
- **Estimated Effort**: High

#### STATE-Q5: Rate Limiting and Throttling

- **Severity**: RISK-SAFETY in 5 of 5 applicable services
- **Affected Services**: camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples
- **Common Finding**: No rate limiting at any layer in any service. No API Gateway, no WAF, no application-level rate limiting middleware. Camunda REST APIs are exposed directly without throttling protection.
- **Compensating Controls**: Deploy API Gateways with per-client rate limits in front of all Camunda REST APIs. Configure Zeebe worker `maxJobsActive` for camunda8-order-process.
- **Portfolio-Level Recommendation**: Deploy a shared API Gateway (AWS API Gateway or Kong) across the portfolio with standardized rate limiting policies. Define per-agent throttling tiers (e.g., 100 requests/minute for agent service accounts).
- **Estimated Effort**: Low

#### DATA-Q2: Data Residency and Sovereignty

- **Severity**: RISK-SAFETY in 5 of 5 applicable services
- **Affected Services**: camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples
- **Common Finding**: No data residency controls in any service. All services are read-only scope (conditional BLOCKER resolved as RISK-SAFETY). Data includes European PII (Camunda GmbH is Germany-based), email addresses of EU-based maintainers, and process variables that could be subject to GDPR.
- **Compensating Controls**: Restrict agent LLM calls to EU-region endpoints (e.g., Amazon Bedrock in eu-west-1). Implement data filtering proxies that strip sensitive fields before LLM transmission.
- **Portfolio-Level Recommendation**: Conduct a portfolio-wide data residency analysis. Document jurisdictional constraints for each service's data. Configure all agent LLM interactions to use GDPR-compliant endpoints.
- **Estimated Effort**: Medium

#### DATA-Q6: PII Redaction in Logs

- **Severity**: RISK-SAFETY in 5 of 5 applicable services
- **Affected Services**: camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples
- **Common Finding**: No PII redaction in any service. camunda-invoice logs creditor names and invoice numbers in plaintext. camunda8-order-process uses `System.out.println` with no masking. camunda-rest-service logs full API response bodies and has DEBUG-level HTTP wire logging. bpmn-miwg-test-suite has unmasked email addresses in data files. camunda-bpm-examples uses standard SLF4J/Logback with no PII filtering.
- **Compensating Controls**: Implement logging filters that mask known PII patterns. Restrict log access to authorized personnel. Disable DEBUG-level HTTP wire logging in production.
- **Portfolio-Level Recommendation**: Implement a shared PII redaction library (Logback TurboFilter or custom MDC filter) that can be deployed across all Java-based services. Define PII field patterns (email, name, financial amounts) for consistent masking.
- **Estimated Effort**: Low

### Cross-Cutting RISK-QUALITY — Same Quality Risk in 3+ Repos

> These are RISK-QUALITY questions that appear in 3 or more repositories.
> They represent portfolio-wide quality patterns to address as capacity allows.
> Questions scored as N/A for a service do not count as gaps for that service.

#### API-Q2: Machine-Readable API Specification

- **Severity**: RISK-QUALITY in 5 of 5 applicable services
- **Affected Services**: camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples
- **Common Finding**: No directly consumable machine-readable API specification in any repository. camunda-invoice has OpenAPI templates requiring a build step. The other 4 services have no specification at all.
- **Portfolio-Level Recommendation**: Standardize on OpenAPI 3.0+ specifications co-located with each service. Use springdoc-openapi for Spring Boot modules, smallrye-open-api for Quarkus modules.
- **Estimated Effort**: Low

#### API-Q3: Structured Error Responses

- **Severity**: RISK-QUALITY in 5 of 5 applicable services
- **Affected Services**: camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples
- **Common Finding**: Error handling is inconsistent and unstructured across all services. No service provides a `retryable` boolean or error category field. Errors are generic exceptions, BPMN errors, or plain text.
- **Portfolio-Level Recommendation**: Define a portfolio-wide structured error response format: `{ "error_code": "...", "error_message": "...", "retryable": true/false, "category": "..." }`. Implement as a shared library.
- **Estimated Effort**: Low

#### DISC-Q1: Schema Versioning and API Contracts

- **Severity**: RISK-QUALITY in 5 of 5 applicable services
- **Affected Services**: camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples
- **Common Finding**: No consumer-driven contract tests, no OpenAPI spec diff tools, and no explicit breaking change detection in any service. BPMN/DMN models have no formal version management beyond Git.
- **Portfolio-Level Recommendation**: Implement schema validation in CI across all services. Add Pact contract tests for agent-facing API surfaces. Automate OpenAPI spec diff checking.
- **Estimated Effort**: Medium

#### OBS-Q1: Distributed Tracing and Structured Logging

- **Severity**: RISK-QUALITY in 5 of 5 applicable services
- **Affected Services**: camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples
- **Common Finding**: No distributed tracing or structured logging in any service. Services use `System.out.println`, `java.util.logging`, or basic SLF4J with unstructured text patterns. No OpenTelemetry, no X-Ray, no correlation IDs.
- **Portfolio-Level Recommendation**: Deploy OpenTelemetry as a portfolio standard. Standardize on JSON structured logging with correlation IDs. Configure centralized log aggregation.
- **Estimated Effort**: Medium

#### OBS-Q2: Alerting on Error Rates and Latency

- **Severity**: RISK-QUALITY in 5 of 5 applicable services
- **Affected Services**: camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples
- **Common Finding**: No alerting configuration in any service. No CloudWatch alarms, no PagerDuty/OpsGenie, no SLO-based alerting. Camunda metrics are explicitly disabled in some services.
- **Portfolio-Level Recommendation**: Deploy a shared monitoring stack (CloudWatch + Prometheus/Grafana) across the portfolio. Define standard alerting thresholds for error rates (>5% 5xx) and latency (p99 > 5s).
- **Estimated Effort**: Medium

#### ENG-Q1: Infrastructure Governance

- **Severity**: RISK-QUALITY in 5 of 5 applicable services
- **Affected Services**: camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples
- **Common Finding**: No Infrastructure as Code in any service. No Terraform, CloudFormation, CDK, Helm, or Kustomize files. Infrastructure is undefined and manual.
- **Portfolio-Level Recommendation**: Define a shared IaC template (Terraform or CDK) for Camunda platform deployments including API Gateway, IAM roles, database, and networking. Apply across all services.
- **Estimated Effort**: High

#### ENG-Q2: CI/CD with API Contract Testing

- **Severity**: RISK-QUALITY in 5 of 5 applicable services
- **Affected Services**: camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples
- **Common Finding**: CI/CD maturity varies widely. camunda-invoice has a comprehensive Jenkins pipeline but no REST API contract tests. bpmn-miwg-test-suite has GitHub Actions CI but no API tests. The other 3 services have no CI/CD at all or only version-bumping workflows.
- **Portfolio-Level Recommendation**: Establish a minimum CI/CD standard: build, test, BPMN validation, and API contract testing. Create reusable GitHub Actions workflow templates for the portfolio.
- **Estimated Effort**: Medium

#### ENG-Q3: Rollback Capability

- **Severity**: RISK-QUALITY in 5 of 5 applicable services
- **Affected Services**: camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples
- **Common Finding**: No automated rollback capability in any service. No blue/green, no canary, no CodeDeploy rollback triggers, no feature flags. Deployment strategies are undefined or manual.
- **Portfolio-Level Recommendation**: Implement container-based deployments (Docker + ECS/EKS) with blue/green or canary strategies and automated rollback triggers for all services.
- **Estimated Effort**: High

#### HITL-Q3: Sandbox/Staging Environment

- **Severity**: RISK-QUALITY in 5 of 5 applicable services
- **Affected Services**: camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples
- **Common Finding**: No dedicated sandbox or staging environments in any service. Services use H2 in-memory databases for testing or have no test infrastructure. No Docker Compose configurations, no synthetic data generators, no production-equivalent environments.
- **Portfolio-Level Recommendation**: Create Docker Compose-based staging environments for each service. Build a shared seed data framework for Camunda process engines. Standardize on environment-specific configuration profiles.
- **Estimated Effort**: Medium

#### API-Q6: Asynchronous Operation Support

- **Severity**: RISK-QUALITY in 4 of 4 applicable services (bpmn-miwg-test-suite: Not Evaluated)
- **Affected Services**: camunda-invoice, camunda8-order-process, camunda-rest-service, camunda-bpm-examples
- **Common Finding**: BPMN processes are inherently long-running with human tasks that may take hours or days. All services support async patterns internally (Camunda async continuation, Zeebe job worker protocol) but none expose business-level polling endpoints or webhook callbacks for external consumers.
- **Portfolio-Level Recommendation**: Implement webhook/SNS notification patterns for process state changes. Expose standardized status polling endpoints across all Camunda services.
- **Estimated Effort**: Medium

#### ENG-Q4: API Test Coverage

- **Severity**: RISK-QUALITY in 3 of 5 applicable services (camunda8-order-process: INFO, bpmn-miwg-test-suite: INFO)
- **Affected Services**: camunda-invoice, camunda-rest-service, camunda-bpm-examples
- **Common Finding**: Tests validate process logic through Java APIs but not through REST API endpoints. No API-level tests, no contract tests, no edge case coverage for agent consumption patterns.
- **Portfolio-Level Recommendation**: Add REST API integration tests covering agent consumption patterns: start process, query tasks, complete tasks, and validate error handling.
- **Estimated Effort**: Medium

#### ENG-Q5: Encryption at Rest

- **Severity**: RISK-QUALITY in 3 of 3 applicable services (camunda8-order-process: Not Evaluated, bpmn-miwg-test-suite: Not Evaluated)
- **Affected Services**: camunda-invoice, camunda-rest-service, camunda-bpm-examples
- **Common Finding**: Process data stored in H2 file databases without encryption. No KMS keys, no encryption configuration.
- **Portfolio-Level Recommendation**: Migrate all services to managed databases (RDS PostgreSQL or Aurora) with KMS-managed encryption at rest for production deployments.
- **Estimated Effort**: Medium

#### DATA-Q4: System of Record Designations

- **Severity**: RISK-QUALITY in 3 of 3 applicable services (camunda8-order-process: Not Evaluated, bpmn-miwg-test-suite: Not Evaluated)
- **Affected Services**: camunda-invoice, camunda-rest-service, camunda-bpm-examples
- **Common Finding**: No system-of-record designations exist in any service. camunda-invoice references a "Financial Accounting System" data store in BPMN but has no formal SoR designation for invoices, creditors, or financial accounts. camunda-rest-service uses GitHub API as the de facto source of truth for repository data while Camunda H2 stores execution-time snapshots with no documentation of which is authoritative. camunda-bpm-examples has each module operating independently with its own H2 database and no master data management or conflict resolution logic.
- **Compensating Controls**: Document system-of-record designations in agent tool definitions (e.g., "Camunda = SoR for process state; external systems = SoR for business entities"). Limit agent access to a single engine instance per domain to reduce conflict risk.
- **Portfolio-Level Recommendation**: Establish a portfolio-wide data ownership framework documenting the authoritative source for each key business entity. For each service, map which data elements are owned by Camunda (process state) vs. external systems (business data). Include SoR designations in agent tool metadata so agents know where to query for golden records.
- **Estimated Effort**: Low

#### DATA-Q5: Temporal Metadata and Freshness

- **Severity**: RISK-QUALITY in 3 of 3 applicable services (camunda8-order-process: Not Evaluated, bpmn-miwg-test-suite: Not Evaluated)
- **Affected Services**: camunda-invoice, camunda-rest-service, camunda-bpm-examples
- **Common Finding**: All 3 services use Camunda engines that internally track timestamps for process instances, tasks, and history entries. However, none expose temporal metadata in API responses — no `Cache-Control` headers, no `X-Data-Age` headers, no `last_refreshed` indicators. camunda-invoice manipulates clock time for demo purposes with no freshness signaling. camunda-rest-service stores GitHub API data as process variables without fetch timestamps, so agents cannot determine data staleness. camunda-bpm-examples has no timezone normalization or freshness signaling on REST responses.
- **Compensating Controls**: Use Camunda history service timestamps as a proxy for data freshness. Add `fetchedAt` process variables when storing data from external API calls. Assume Camunda REST API responses are real-time (strong consistency from database) unless documented otherwise.
- **Portfolio-Level Recommendation**: Add `Cache-Control` and `Last-Modified` response headers to all Camunda REST API responses and custom endpoints across the portfolio. Standardize on including `fetchedAt` timestamp process variables when storing external API data. Document the consistency model for process data queries in agent tool definitions.
- **Estimated Effort**: Low

## Service Dependency Map

> Dependencies were inferred from individual ARA report findings (not explicitly provided via `dependency_overrides`). Inferred dependencies may be incomplete — they reflect only what was observable in the assessed code and report context. For authoritative dependency data, add `dependency_overrides` to the portfolio config.

### Dependency Overview

| Source Service | Target Service | Type | Description | Inferred |
|---------------|---------------|------|-------------|----------|
| camunda-invoice | Camunda 7 Platform | shared_infra | Uses Camunda Platform 7 REST API and engine | Yes |
| camunda-rest-service | Camunda 7 Platform | shared_infra | Uses Camunda Platform 7 REST API (`camunda-bpm-spring-boot-starter-rest` 7.16.0) | Yes |
| camunda-rest-service | api.github.com | sync | REST calls to GitHub API (search repo, contributors, community profile, languages) | Yes |
| camunda-bpm-examples | Camunda 7 Platform | shared_infra | Uses Camunda Platform 7 REST API and engine (7.24.0) | Yes |
| camunda8-order-process | Camunda 8 SaaS (Zeebe) | sync | Zeebe job worker connecting to Camunda 8 SaaS cluster in bru-2 region | Yes |
| bpmn-miwg-test-suite | — | — | No runtime dependencies. Static data archive. | Yes |

### Service Dependency Metrics

| Service | Fan-In | Fan-Out | Role | Readiness Profile |
|---------|--------|---------|------|-------------------|
| camunda-invoice | 0 | 1 | Leaf | Remediation Required |
| camunda8-order-process | 0 | 1 | Leaf | Not Agent-Integrable |
| camunda-rest-service | 0 | 2 | Leaf | Not Agent-Integrable |
| bpmn-miwg-test-suite | 0 | 0 | Isolated | Not Agent-Integrable |
| camunda-bpm-examples | 0 | 1 | Leaf | Remediation Required |
| Camunda 7 Platform (inferred) | 3 | 0 | Foundation | Not assessed (external) |
| Camunda 8 SaaS (inferred) | 1 | 0 | Foundation | Not assessed (external) |
| api.github.com (inferred) | 1 | 0 | Foundation | Not assessed (external) |

### High-Risk Dependency Patterns

1. **Shared Camunda 7 Platform Dependency**: 3 portfolio services (camunda-invoice, camunda-rest-service, camunda-bpm-examples) share the Camunda 7 Platform as a foundation dependency. If the Camunda 7 REST API has security blockers (e.g., AUTH-Q1 — no machine identity on the shared auth system), all three services are affected. Currently, camunda-rest-service and camunda-bpm-examples have AUTH-Q1 as BLOCKER, indicating the shared platform lacks adequate authentication.
   - **Affected Services**: camunda-invoice, camunda-rest-service, camunda-bpm-examples
   - **Risk**: A platform-level authentication fix would benefit all 3 services simultaneously. Conversely, a platform-level vulnerability affects all 3.
   - **Recommendation**: Prioritize deploying a centralized identity provider integrated with the Camunda 7 REST API. This single platform investment resolves AUTH-Q1 for camunda-rest-service and camunda-bpm-examples and strengthens camunda-invoice's existing basic auth.

2. **External API Dependency Without Resilience**: camunda-rest-service depends synchronously on api.github.com with no circuit breaker, timeout, or retry logic (STATE-Q4: RISK-SAFETY). A GitHub API outage would cascade into the Camunda engine, blocking process instances.
   - **Affected Services**: camunda-rest-service
   - **Risk**: Agent-initiated process instances could amplify cascading failures from GitHub API degradation.
   - **Recommendation**: Add Resilience4j circuit breaker and timeout configuration to GitHub API HTTP clients before enabling agent access.

3. **Isolated Services with No Dependencies**: bpmn-miwg-test-suite has no runtime dependencies and no inbound callers. Its 3 BLOCKERs (API-Q1, AUTH-Q1, DATA-Q1) do not cascade to other services but represent a standalone remediation effort that is independent of the rest of the portfolio.
## Portfolio Remediation Guidance

> Portfolio context: Demonstrating BPMN agentic opportunity analysis across official open source process repositories covering invoice processing, order management, and BPMN interchange test cases.

### Remediation Priority Order

Remediation of cross-cutting BLOCKERs should follow this general priority:

1. **Identity and Access** — Resolve AUTH-Q1 first. You cannot enforce any other security control without machine identity and scoped permissions.
2. **Data Integrity** — Resolve DATA-Q1 second. Classify data before enabling agent read access to process variables.
3. **API Surface** — Resolve API-Q1 third. Ensure a stable, documented integration surface for agent tools.

### Coordinated Remediation Plan

#### 1. Identity Foundation

**BLOCKERs addressed**: AUTH-Q1
**Services affected**: camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples

- **What to do**: Deploy a centralized identity provider (Amazon Cognito or Okta) shared by the portfolio. Create per-agent OAuth2 client credentials with principal attribution. For Camunda 7 services (camunda-rest-service, camunda-bpm-examples), configure Spring Security with OAuth2 resource server or add an API Gateway with Cognito authorizer. For camunda8-order-process, implement auth as part of the new REST API layer (concurrent with API-Q1). For bpmn-miwg-test-suite, implement auth in the new API service.
- **Expected outcome**: Every agent authenticates with a unique identity. Audit logs attribute every request to a specific agent principal. AUTH-Q2, AUTH-Q6, and AUTH-Q7 remediation becomes possible.
- **Effort**: High

#### 2. Data Classification Framework

**BLOCKERs addressed**: DATA-Q1
**Services affected**: camunda-invoice, camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite, camunda-bpm-examples

- **What to do**: Establish a portfolio-wide data classification taxonomy (Public, Internal, Confidential, Restricted). Conduct per-service data inventory: classify all process variables, API response fields, database columns, and data files. For camunda-invoice: classify creditor names (Business-Confidential), amounts (Financial), user emails (PII). For camunda8-order-process: remove PII from DMN tables, rotate and externalize credentials. For bpmn-miwg-test-suite: classify maintainer emails as PII, create redacted views for agent consumption. Document classifications in per-service data dictionaries.
- **Expected outcome**: Every data field has a sensitivity classification. Agents have visibility into data sensitivity before accessing process data. Foundation for field-level access controls.
- **Effort**: Medium

#### 3. API Surface Development

**BLOCKERs addressed**: API-Q1
**Services affected**: camunda8-order-process, camunda-rest-service, bpmn-miwg-test-suite

- **What to do**: For camunda8-order-process: add a Spring `@RestController` wrapping key Zeebe operations (start process, query status, send messages) with OpenAPI specification. For camunda-rest-service: create a business facade REST API (e.g., `POST /api/repos/{owner}/{name}/check-popularity`) that abstracts Camunda engine internals. For bpmn-miwg-test-suite: evaluate whether agentic access is needed; if so, build a read-only REST API over the BPMN reference models and test results. Include OpenAPI specs from the start.
- **Expected outcome**: All services expose documented, agent-consumable REST APIs with OpenAPI specifications. Agent tools can be auto-generated from specifications.
- **Effort**: High
## Agentic Program Recommendations

> These are engagement-level recommendations based on the portfolio's agentic readiness
> profile. Discuss with your AWS Solutions Architect to determine eligibility and timing.

| Program | Relevance | Trigger Findings | Suggested Timing | Next Step |
|---------|-----------|-----------------|------------------|-----------|
| AI DLC | Teams lack AI-driven development practices; all 5 services have no CI/CD or inadequate CI | 5/5 services (100%) have ENG-Q2 as RISK-QUALITY — no CI/CD or no API contract testing | Run first — establish AI-driven dev practices before agentic work | Request AI DLC workshop via AWS SA |
| AgentStorming | Portfolio is exploratory ("Demonstrating BPMN agentic opportunity analysis") — agent use cases not yet defined per-service | 3/5 services are Not Agent-Integrable with no clear agent integration path; context is exploratory | Run after AI DLC — identify where agents should operate | Request AgentStorming workshop via AWS SA |
| EBA on Agentic AI | DATA-Q1 BLOCKER affects all 5 repos — systemic cross-cutting blocker requiring coordinated architecture remediation | DATA-Q1 (Sensitive Data Classification) is BLOCKER in 5 repos ≥ 5 threshold | Run after AgentStorming — accelerate systemic remediation | Request EBA engagement via AWS SA |

### Program Details

#### AI DLC (AI Driven Development Lifecycle)

- **Why triggered**: All 5 services (100%) have ENG-Q2 as RISK-QUALITY, indicating missing or inadequate CI/CD pipelines. camunda8-order-process, camunda-rest-service, and camunda-bpm-examples have no CI/CD at all. camunda-invoice has a comprehensive Jenkins pipeline but lacks API contract testing. bpmn-miwg-test-suite has basic GitHub Actions CI but no API tests. This demonstrates a portfolio-wide gap in AI-driven development practices.
- **What it provides**: Workshop for adopting the AI Driven Development Lifecycle, emphasizing AI Powered Execution with Human Oversight (AI creates detailed work plans, seeks clarification, defers critical decisions to humans) and Dynamic Team Collaboration (teams unite in collaborative spaces for real-time problem solving as AI handles routine tasks).
- **Suggested timing**: Run first — before AgentStorming or EBA. Establishing AI-driven development practices improves the team's ability to execute subsequent agentic remediation work efficiently.
- **Recommended scope**: Focus on the 3 services without CI/CD (camunda8-order-process, camunda-rest-service, camunda-bpm-examples). Use the workshop to establish CI/CD pipelines as a foundation for automated API contract testing and agentic tooling.
- **Next step**: Request AI DLC workshop engagement via your AWS Solutions Architect.

#### AgentStorming

- **Why triggered**: The portfolio context is exploratory — "Demonstrating BPMN agentic opportunity analysis" — without per-service agent use case definitions. 3 of 5 services (60%) are Not Agent-Integrable with no clear agent integration path. Agent scope is read-only across the entire portfolio with no defined progression to write-enabled. The portfolio would benefit from a structured process to identify where agentic AI delivers real value versus traditional automation.
- **What it provides**: A workshop format building on EventStorming with Cognitive Complexity Analysis and Agentic Workflow Design to pinpoint where agentic AI delivers real value. Produces a qualified, implementation-ready answer to "where should we use AI agents?"
- **Suggested timing**: Run after AI DLC — once development practices are improved, use AgentStorming to map the business processes (invoice processing, order management, BPMN interchange) and identify which tasks are candidates for agentic automation vs. deterministic automation.
- **Recommended scope**: Focus on the 3 Camunda 7 services (camunda-invoice, camunda-rest-service, camunda-bpm-examples) that have existing process definitions suitable for analysis. Include camunda8-order-process for Camunda 8 / Zeebe patterns.
- **Next step**: Request AgentStorming workshop engagement via your AWS Solutions Architect.

#### EBA on Agentic AI (Experience-Based Acceleration)

- **Why triggered**: DATA-Q1 (Sensitive Data Classification) is a BLOCKER in all 5 repositories — this is a systemic cross-cutting blocker that exceeds the EBA threshold of 5+ repositories. Additionally, AUTH-Q1 is a BLOCKER in 4 repositories. These are portfolio-level architectural gaps that cannot be resolved through standard advisory alone — they require coordinated data governance and identity infrastructure investments across the entire portfolio.
- **What it provides**: An intensive, time-boxed engagement that accelerates the path from agentic readiness analysis to production deployment. Embeds AWS expertise to compress multi-quarter remediation cycles into a focused sprint, producing remediated systems, validated agent integrations, and a sequenced deployment roadmap.
- **Suggested timing**: Run after AgentStorming — once agent use cases are identified, use EBA to accelerate the systemic remediation (DATA-Q1 across 5 repos, AUTH-Q1 across 4 repos, API-Q1 across 3 repos) required to unblock agent deployment.
- **Recommended scope**: Focus on the 3 cross-cutting BLOCKERs: (1) DATA-Q1 across all 5 services, (2) AUTH-Q1 across 4 services, (3) API-Q1 across 3 services. The EBA engagement should produce a portfolio-wide data classification framework, a centralized identity provider, and API surface designs for the 3 services lacking APIs.
- **Next step**: Request EBA on Agentic AI engagement via your AWS Solutions Architect.
## Portfolio-Level Findings

> These questions evaluate capabilities that can only be assessed by looking across
> multiple repos. They are distinct from cross-cutting analysis (which aggregates
> individual findings). Individual report findings are never overridden.

### PORT-ARA-Q1: Centralized Identity Plane

- **Severity**: BLOCKER
- **Finding**: No shared identity provider detected across any repository. camunda-invoice uses basic auth via the Camunda engine's built-in authentication (not a shared IdP). camunda8-order-process uses OAuth2 client credentials to authenticate outbound to Camunda 8 SaaS (not shared inbound auth). camunda-rest-service and camunda-bpm-examples use hardcoded `demo:demo` credentials (not an identity provider). bpmn-miwg-test-suite has no authentication mechanism at all. No Cognito User Pool, Cognito Identity Pool, Okta configuration, or shared auth middleware is referenced in any repository. No common IdP resource (ARN, name, or config reference) appears in 2+ repos.
- **Evidence**: camunda-invoice `engine-rest/engine-rest-openapi/src/main/templates/main.ftl` (basicAuth only), camunda8-order-process `src/main/resources/application.yml` (outbound Zeebe OAuth2 only), camunda-rest-service `CamundaApplication/src/main/resources/application.yaml` (hardcoded demo:demo), camunda-bpm-examples `spring-boot-starter/example-web/src/main/resources/application.yml` (hardcoded demo:demo), bpmn-miwg-test-suite (no auth code or config)
- **Recommendation**: Deploy a centralized identity provider (Amazon Cognito User Pool or Okta) that all 5 services use for agent M2M authentication. Create per-agent OAuth2 client credentials. Configure each service's API Gateway or Spring Security to validate tokens against the shared IdP.
- **Affected Services**: All 5 services
- **Contextual Annotations**:

> **Portfolio Context**: PORT-ARA-Q1 found no shared identity provider across the portfolio.
> This confirms the AUTH-Q1 cross-cutting BLOCKER — a centralized identity plane would
> resolve AUTH-Q1 for all 4 affected services simultaneously — **verify** that the chosen
> IdP supports the Camunda 7 REST API's authentication filter and can be integrated with
> the Camunda 8 Zeebe client SDK.

### PORT-ARA-Q2: Cross-Service Audit Correlation

- **Severity**: RISK
- **Finding**: No shared trace ID propagation or centralized audit trail detected across any service. No shared CloudTrail trail covering multiple services. No consistent trace ID headers (`X-Amzn-Trace-Id`, `traceparent`) propagated across repos. No centralized log aggregation (no shared CloudWatch Log Groups, no shared S3 audit bucket). Each service logs independently with different patterns — camunda-invoice uses `java.util.logging`, camunda8-order-process uses `System.out.println`, camunda-rest-service uses logback with plain-text, camunda-bpm-examples uses SLF4J default, bpmn-miwg-test-suite has no logging.
- **Evidence**: All 5 reports confirm no distributed tracing (OBS-Q1: RISK-QUALITY in all 5). No shared correlation mechanism found in any repository.
- **Recommendation**: Deploy a portfolio-wide observability solution: (1) standardize on OpenTelemetry for all Java services, (2) configure centralized log aggregation in CloudWatch Logs with a shared log group prefix, (3) propagate `traceparent` headers through all inter-service calls, (4) implement a shared audit log format with `agent_principal`, `action`, `resource`, `timestamp`, and `trace_id` fields.
- **Affected Services**: All 5 services

### PORT-ARA-Q3: Portfolio-Level Rate Limiting

- **Severity**: RISK
- **Finding**: No shared API Gateway or WAF protecting the portfolio perimeter from agent traffic storms. No shared WAF WebACL referenced across repos. No shared API Gateway with usage plans. Each service either has no rate limiting at all (STATE-Q5: RISK-SAFETY in all 5) or relies on platform-level limits (GitHub API rate limits for camunda-rest-service, Camunda 8 SaaS limits for camunda8-order-process).
- **Evidence**: All 5 reports confirm no rate limiting (STATE-Q5: RISK-SAFETY in all 5). No API Gateway or WAF configuration found in any repository.
- **Recommendation**: Deploy a shared API Gateway (AWS API Gateway) at the portfolio perimeter with: (1) per-agent usage plans and API keys, (2) portfolio-level WAF rules for agent traffic patterns, (3) burst and steady-state rate limits per agent identity. Individual services can have additional per-service rate limits behind the shared gateway.
- **Affected Services**: All 5 services

### PORT-ARA-Q4: Transitive Dependency Safety

- **Severity**: RISK
- **Finding**: Limited dependency graph available (inferred from report findings, not explicitly configured). The 3 Camunda 7 services (camunda-invoice, camunda-rest-service, camunda-bpm-examples) share the Camunda 7 Platform as a foundation dependency. camunda-rest-service (Not Agent-Integrable, 3 BLOCKERs) shares this platform with camunda-invoice (Remediation Required, 1 BLOCKER). While these are shared_infra dependencies (not direct sync dependencies), the shared platform means that platform-level blockers affect all dependent services. camunda-rest-service also has a sync dependency on api.github.com with no circuit breaker (STATE-Q4: RISK-SAFETY). No direct sync dependencies exist between portfolio services that would create hard transitive blocks.
- **Evidence**: Dependency graph inferred from ARA reports: 3 services share Camunda 7 Platform, camunda-rest-service calls api.github.com. No direct inter-service sync dependencies detected.
- **Recommendation**: (1) Assess and document the Camunda 7 Platform's agentic readiness separately — its blockers cascade to 3 services. (2) Add `dependency_overrides` to the portfolio config for authoritative dependency mapping. (3) Add circuit breakers to camunda-rest-service's GitHub API calls (STATE-Q4 remediation) to prevent cascading failures.
- **Affected Services**: camunda-invoice, camunda-rest-service, camunda-bpm-examples (shared Camunda 7 platform)

### PORT-ARA-Q5: Agent Identity Governance

- **Severity**: RISK
- **Finding**: No portfolio-wide agent identity registry or centralized revocation mechanism detected. No shared Cognito app client registry. No centralized API key management. No portfolio-level agent identity documentation. Each service manages identities independently — camunda-invoice has per-user identity via the Camunda Identity Service, the other services either have no identity management or use a single shared credential. There is no "kill switch" capability to suspend all agent identities across the portfolio simultaneously.
- **Evidence**: AUTH-Q7 (Agent Identity Suspension) is RISK-SAFETY in all 5 services. No shared identity management found across any repository.
- **Recommendation**: Implement a centralized agent identity registry: (1) deploy a shared Cognito User Pool with per-agent app clients, (2) implement a portfolio-level "kill switch" API that can revoke all agent tokens simultaneously, (3) define agent identity lifecycle procedures (creation, rotation, suspension, revocation) as a portfolio standard.
- **Affected Services**: All 5 services
## Service-by-Service Summary

| Service | Repo Type | Agent Scope | Readiness Profile | BLOCKERs | RISKs | INFOs | N/A |
|---------|-----------|-------------|-------------------|----------|-------|-------|-----|
| camunda8-order-process | application | read-only | ❌ Not Agent-Integrable | 3 | 20 | 11 | 9 (Not Evaluated) |
| camunda-rest-service | application | read-only | ❌ Not Agent-Integrable | 3 | 27 | 12 | 1 (Not Evaluated) |
| bpmn-miwg-test-suite | application | read-only | ❌ Not Agent-Integrable | 3 | 18 | 11 | 11 (Not Evaluated) |
| camunda-invoice | monorepo | read-only | 🟠 Remediation Required | 1 | 23 | 12 | 0 |
| camunda-bpm-examples | monorepo | read-only | 🟠 Remediation Required | 2 | 25 | 15 | 1 (Not Evaluated) |

### Individual Service Details

#### camunda8-order-process

- **Readiness Profile**: ❌ Not Agent-Integrable
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P0
- **BLOCKERs** (3):
  - API-Q1: No REST, GraphQL, or AsyncAPI interface — Zeebe job worker only, no addressable API surface
  - AUTH-Q1: No inbound machine identity authentication — worker connects outbound to Camunda 8 SaaS only
  - DATA-Q1: PII (email) hardcoded in DMN table, plaintext Zeebe credentials in `application.yml`
- **RISKs** (20):
  - RISK-SAFETY (9): AUTH-Q2, AUTH-Q3, AUTH-Q5 (CRITICAL — plaintext credentials in Git), AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q5, DATA-Q2, DATA-Q6
  - RISK-QUALITY (11): API-Q2, API-Q3, API-Q6, STATE-Q7, HITL-Q3, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3
- **Key Recommendations**:
  - Immediately rotate exposed Zeebe client credentials and remove from Git history
  - Expose a REST API layer wrapping key Zeebe operations with OpenAPI spec
  - Implement OAuth2 resource server authentication on the new API surface
- **Depends On**: Camunda 8 SaaS (Zeebe) cluster in bru-2 region

#### camunda-rest-service

- **Readiness Profile**: ❌ Not Agent-Integrable
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P1
- **BLOCKERs** (3):
  - API-Q1: No business-specific API — only generic Camunda engine REST API at `/engine-rest`
  - AUTH-Q1: No machine identity auth — hardcoded `demo:demo` credentials with full admin privileges
  - DATA-Q1: No data classification on process variables, H2 database, or GitHub API response data
- **RISKs** (27):
  - RISK-SAFETY (9): AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q4 (no circuit breakers on GitHub API), STATE-Q5, DATA-Q2, DATA-Q6
  - RISK-QUALITY (18): API-Q2, API-Q3, API-Q6, AUTH-Q4, AUTH-Q5, STATE-Q2, HITL-Q3, DATA-Q3, DATA-Q4, DATA-Q5, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4, ENG-Q5
- **Key Recommendations**:
  - Create a business facade REST API abstracting Camunda engine internals
  - Add Resilience4j circuit breaker to GitHub API calls (STATE-Q4)
  - Remove hardcoded credentials; implement Spring Security with OAuth2
- **Depends On**: Camunda 7 Platform (shared_infra), api.github.com (sync)

#### bpmn-miwg-test-suite

- **Readiness Profile**: ❌ Not Agent-Integrable
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P1
- **BLOCKERs** (3):
  - API-Q1: No application source code, no API surface — static data archive of BPMN 2.0 reference models
  - AUTH-Q1: No authentication mechanism — no application runtime to authenticate against
  - DATA-Q1: PII (maintainer email addresses) in `tools-tested-by-miwg.json` without classification
- **RISKs** (18):
  - RISK-SAFETY (8): AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q5, DATA-Q2, DATA-Q6
  - RISK-QUALITY (10): API-Q2, API-Q3, AUTH-Q5, HITL-Q3, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3
- **Key Recommendations**:
  - Evaluate whether agentic access to BPMN test data is needed before investing in API development
  - Create redacted version of `tools-tested-by-miwg.json` stripping maintainer PII
  - If API is needed, build a lightweight read-only service with auth from the start
- **Depends On**: No runtime dependencies (isolated static data archive)

#### camunda-invoice

- **Readiness Profile**: 🟠 Remediation Required
- **Repo Type**: monorepo
- **Agent Scope**: read-only
- **Priority**: P0
- **BLOCKERs** (1):
  - DATA-Q1: Invoice data (creditor names, amounts, invoice numbers, PDF documents, user emails) not classified at field level
- **RISKs** (23):
  - RISK-SAFETY (6): AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q5, DATA-Q2, DATA-Q6
  - RISK-QUALITY (17): API-Q2, API-Q3, API-Q6, AUTH-Q4, AUTH-Q5, HITL-Q3, STATE-Q7, DATA-Q4, DATA-Q5, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4, ENG-Q5
- **Key Recommendations**:
  - Create data classification inventory for all process variables (creditor=Business-Confidential, amount=Financial, user emails=PII)
  - Implement PII redaction in log output for NotifyCreditorService and ArchiveInvoiceService
  - Deploy API Gateway with rate limiting in front of Camunda REST API
- **Depends On**: Camunda 7 Platform (shared_infra)

#### camunda-bpm-examples

- **Readiness Profile**: 🟠 Remediation Required
- **Repo Type**: monorepo
- **Agent Scope**: read-only
- **Priority**: P1
- **BLOCKERs** (2):
  - AUTH-Q1: No machine identity auth — only hardcoded basic auth (`demo:demo`) across all Spring Boot examples
  - DATA-Q1: No data classification for process variables (invoice data, approval data, tenant-specific data)
- **RISKs** (25):
  - RISK-SAFETY (9): AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q4, STATE-Q5, DATA-Q2, DATA-Q6
  - RISK-QUALITY (16): API-Q2, API-Q3, API-Q6, STATE-Q2, HITL-Q3, DATA-Q3, DATA-Q4, DATA-Q5, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4, ENG-Q5
- **Key Recommendations**:
  - Implement OAuth2 client credentials or API key auth via Spring Security configuration
  - Inventory and classify all process variables across 53 BPMN definitions
  - Add Resilience4j circuit breakers to external HTTP clients
- **Depends On**: Camunda 7 Platform (shared_infra)
## Analysis Inventory

| # | Service | Report File | Analysis Date | Repo Type | Agent Scope |
|---|---------|-------------|-----------------|-----------|-------------|
| 1 | camunda-invoice | ./example-reports/bao-demo/repos/camunda-invoice/camunda-invoice-ara-report.md | 2025-07-14 | monorepo | read-only |
| 2 | camunda8-order-process | ./example-reports/bao-demo/repos/camunda8-order-process/camunda8-order-process-ara-report.md | 2025-07-15 | application | read-only |
| 3 | camunda-rest-service | ./example-reports/bao-demo/repos/camunda-rest-service/camunda-rest-service-ara-report.md | 2025-07-14 | application | read-only |
| 4 | bpmn-miwg-test-suite | ./example-reports/bao-demo/repos/bpmn-miwg-test-suite/bpmn-miwg-test-suite-ara-report.md | 2025-07-14 | application | read-only |
| 5 | camunda-bpm-examples | ./example-reports/bao-demo/repos/camunda-bpm-examples/camunda-bpm-examples-ara-report.md | 2025-07-17 | monorepo | read-only |
