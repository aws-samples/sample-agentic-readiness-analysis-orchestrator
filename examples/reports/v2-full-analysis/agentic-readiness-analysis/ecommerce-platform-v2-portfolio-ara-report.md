# Portfolio Agentic Readiness Analysis Report

**Date**: 2026-04-17
**Services Analyzed**: 5
**Portfolio Context**: Evaluating the e-commerce platform portfolio for both autonomous AI agent integration and cloud-native modernization. The team is building a customer support agent that handles order inquiries, processes returns, and manages inventory restocking — while simultaneously modernizing legacy monoliths into containerized microservices on EKS.

---

## Executive Dashboard

### Readiness Distribution

| Profile | Services | Percentage | Description |
|---------|----------|------------|-------------|
| ✅ Agent-Ready | 0 | 0% | 0 blockers, 0 RISK-SAFETY — broad agent deployment |
| 🟡 Pilot-Ready | 0 | 0% | 0 blockers, 1–2 RISK-SAFETY — narrow pilot |
| 🟡 Pilot-Ready (Safety Concerns) | 1 | 20% | 0 blockers, 3+ RISK-SAFETY — supervised pilot, prioritize safety |
| 🟠 Remediation Required | 4 | 80% | 1–2 blockers — remediate before any agent deployment |
| ❌ Not Agent-Integrable | 0 | 0% | 3+ blockers — deferred or descoped |

### Portfolio Summary

| Metric | Value |
|--------|-------|
| Total Services Analyzed | 5 |
| Services Ready for Agents (Agent-Ready + Pilot-Ready) | 0 (0%) |
| Services Requiring Remediation | 4 (80%) |
| Cross-Cutting BLOCKERs (same blocker in 2+ repos) | 2 |
| Cross-Cutting RISKs (same risk in 3+ repos) | 22 |
| Services with Write-Enabled Agent Scope | 0 (0%) |
| Services with Read-Only Agent Scope | 5 (100%) |

### Repo Type Distribution

| Repo Type | Count | Percentage |
|-----------|-------|------------|
| application | 4 | 80% |
| infrastructure-only | 1 | 20% |
| deployment-config | 0 | 0% |
| monorepo | 0 | 0% |
| library | 0 | 0% |

### Blocker Heatmap by Section

| Section | Repos Blocked | % of Applicable Repos | Top Blockers |
|---------|--------------|----------------------|--------------|
| AUTH | 4 | 80% (4 of 5 applicable) | AUTH-Q1 |
| DATA | 4 | 100% (4 of 4 applicable) | DATA-Q1 |
| API | 0 | 0% | — |
| STATE | 0 | 0% | — |
| HITL | 0 | 0% | — |
| DISC | 0 | 0% | — |
| OBS | 0 | 0% | — |
| ENG | 0 | 0% | — |

### Readiness Snapshot

| Metric | Value |
|--------|-------|
| analysis_date | 2026-04-17 |
| total_services | 5 |
| agent_ready | 0 |
| pilot_ready | 0 |
| pilot_ready_safety_concerns | 1 |
| remediation_required | 4 |
| not_integrable | 0 |
| total_blockers | 8 |
| total_risks | 105 |
| total_risk_safety | 37 |
| total_risk_quality | 68 |
| total_infos | 59 |
| cross_cutting_blockers | 2 |
| cross_cutting_risks | 22 |
| cross_cutting_risk_safety | 8 |
| cross_cutting_risk_quality | 14 |
| portfolio_level_blockers | 1 |
| portfolio_level_risks | 3 |
| write_enabled_services | 0 |
| read_only_services | 5 |

## Cross-Cutting BLOCKERs — Same Blocker in 2+ Repos

> These are BLOCKER-severity questions that appear in 2 or more repositories.
> They represent portfolio-wide agentic readiness gaps requiring coordinated remediation.
> Questions scored as N/A for a service do not count as gaps for that service.

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER in 4 of 5 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api
- **Common Finding**: None of the 4 application services have machine identity authentication. unishop-monolith has Spring Security OAuth2 present as a dependency but entirely disabled (`permitAll()`). aws-microservices has 3 completely open API Gateway REST APIs with no authorizer. local-monolith uses PHP session-based authentication only (`$_SESSION`). books-api has Amazon Cognito User Pool but only with OAuth2 implicit flow for human users — no client_credentials grant for machine-to-machine auth. eks-saas-gitops (RISK-QUALITY, not BLOCKER) has a robust IRSA pattern but no agent-specific role.
- **Root Cause Pattern**: All 4 application services were designed for human-only interaction. Authentication mechanisms are either absent (aws-microservices), disabled (unishop-monolith), browser-session-based (local-monolith), or human-flow-only (books-api). No service has a programmatic authentication path suitable for autonomous agent callers.
- **Portfolio-Level Remediation**:
  - **Approach**: HYBRID — platform-level Cognito setup shared across services + per-service integration
  - **Immediate Action**: Provision a shared Amazon Cognito User Pool with resource servers and custom scopes (e.g., `orders/read`, `inventory/read`, `catalog/read`). Create per-agent App Clients with `client_credentials` grant type. The eks-saas-gitops IRSA pattern can serve as the template for Kubernetes-hosted services.
  - **Target State**: All API endpoints require a valid OAuth2 Bearer token or API key with principal attribution. Each agent identity has a unique `client_id` that appears in audit logs and CloudTrail. books-api extends its existing Cognito with `client_credentials` flow. aws-microservices adds API Gateway authorizers. unishop-monolith enables its existing Spring Security OAuth2. local-monolith adds API key or OAuth2 middleware.
  - **Estimated Effort**: High (platform setup: 2 weeks; per-service integration: 2–4 weeks each)
  - **Priority**: Critical — affects 4/5 services, prerequisite for all other security controls (AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7)
  - **Dependencies**: None — this is the first blocker to resolve

> **Portfolio Context**: PORT-ARA-Q1 found no shared identity provider across the portfolio.
> books-api has its own Cognito User Pool and eks-saas-gitops has IRSA, but no shared IdP exists.
> Resolving AUTH-Q1 with a shared Cognito pool would simultaneously address PORT-ARA-Q1 — **verify**
> that each service integrates with the shared Cognito pool after provisioning.

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER in 4 of 4 applicable services (eks-saas-gitops is N/A for this question)
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api
- **Common Finding**: All 4 application services store data without classification tags, field-level encryption, or Amazon Macie integration. unishop-monolith has user PII (`email`, `first_name`, `last_name`) in MySQL exposed in API responses via `@JsonInclude`. aws-microservices has PII **and** payment card information (`firstName`, `lastName`, `email`, `address`, `cardInfo`) in DynamoDB with no field-level encryption. local-monolith has customer PII (`customer_name`, `customer_email`, `shipping_address`) across 9 MySQL tables returned unfiltered by admin APIs. books-api has catalog/reference data (`isbn`, `title`, `author`) with no PII but no classification tags to prove it.
- **Root Cause Pattern**: No data classification policy exists at the portfolio level. Each service stores data without explicit sensitivity labeling — even books-api, which stores only non-sensitive reference data, lacks classification tags. Without classification, agents cannot programmatically verify whether data they access is safe to process, cache, or transmit to LLM endpoints.
- **Portfolio-Level Remediation**:
  - **Approach**: HYBRID — portfolio-wide classification policy + per-service tagging and response filtering
  - **Immediate Action**: Create a portfolio-wide data classification policy document defining levels: Public, Internal, Confidential, Restricted. Tag each data store in each service with its classification level. For books-api, add `data-classification: public` and `contains-pii: false` tags to the DynamoDB table (low effort — hours). For the other 3 services, classify each field and implement API response filtering to exclude PII from agent-facing endpoints.
  - **Target State**: All data stores have explicit classification tags. API responses to agents exclude or mask PII unless explicitly authorized. Amazon Macie scans DynamoDB tables and S3 for PII detection. Field-level encryption protects Confidential/Restricted fields (especially `cardInfo` in aws-microservices).
  - **Estimated Effort**: Medium (policy: 1 week; books-api tagging: hours; per-service field classification and response filtering: 1–4 weeks each; Macie + field-level encryption: 4–8 weeks)
  - **Priority**: Critical — affects all 4 application services, required before agents can safely access data
  - **Dependencies**: AUTH-Q1 should be resolved first — field-level access controls require identity to enforce per-caller data access scoping

## Cross-Cutting RISKs

### Cross-Cutting RISK-SAFETY — Same Safety Risk in 3+ Repos

> These are RISK-SAFETY questions that appear in 3 or more repositories.
> They represent portfolio-wide agent safety gaps requiring coordinated attention.
> Questions scored as N/A for a service do not count as gaps for that service.

#### AUTH-Q2: Scoped Permissions (Least Privilege)

- **Severity**: RISK-SAFETY in 5 of 5 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops
- **Common Finding**: All services lack agent-specific scoped permissions. Application services use coarse-grained authorization (permitAll, binary admin/customer roles, or public endpoints). eks-saas-gitops has AdministratorAccess on IRSA roles for Argo Workflows and TF Controller.
- **Compensating Controls**: Deploy read-only API Gateway stages for agents; use tenant-level IRSA roles (properly scoped) on eks-saas-gitops; restrict agent API keys to GET methods only.
- **Portfolio-Level Recommendation**: After AUTH-Q1 remediation, define a shared RBAC model with at least 3 roles per service (human-reader, agent-reader, admin). Use Cognito custom scopes for per-service permission boundaries.
- **Estimated Effort**: Medium

#### AUTH-Q3: Action-Level Authorization

- **Severity**: RISK-SAFETY in 5 of 5 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops
- **Common Finding**: No action-level authorization across the portfolio. Application services cannot restrict agents to read-only at the application layer. eks-saas-gitops has wildcard Kubernetes ClusterRoles granting all verbs on all resources.
- **Compensating Controls**: Separate read-only API Gateway stages for agents; method-level API Gateway restrictions; Kubernetes namespace-scoped Roles.
- **Portfolio-Level Recommendation**: Implement action-level authorization middleware in each service after AUTH-Q1 remediation. For Java (unishop-monolith): Spring Security `@PreAuthorize` with read/write roles. For Node.js (aws-microservices): Lambda authorizer middleware. For PHP (local-monolith): route-based middleware. For SAM (books-api): Cognito Resource Server scopes per endpoint.
- **Estimated Effort**: Medium

#### AUTH-Q6: Immutable Audit Logging

- **Severity**: RISK-SAFETY in 5 of 5 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops
- **Common Finding**: No immutable, tamper-evident audit trail across the portfolio. unishop-monolith has only `System.out.println` and `e.printStackTrace()`. aws-microservices has unstructured `console.log` with no retention policies. local-monolith has mutable `order_status_history` in MySQL. books-api has API Gateway logging at INFO but no CloudTrail. eks-saas-gitops has no CloudTrail and no EKS control plane audit logging.
- **Compensating Controls**: Enable account-level CloudTrail (shared across all services); configure CloudWatch Logs retention policies; add structured JSON logging to each service.
- **Portfolio-Level Recommendation**: Deploy a shared CloudTrail trail with S3 bucket (object lock enabled) covering all services. This is a single platform-level investment that addresses AUTH-Q6 for the entire portfolio. Then add application-level structured logging per service.
- **Estimated Effort**: Medium (shared CloudTrail: 1 week; per-service structured logging: 1–2 weeks each)

#### AUTH-Q7: Agent Identity Suspension

- **Severity**: RISK-SAFETY in 5 of 5 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops
- **Common Finding**: No agent identity suspension mechanism exists in any service. Application services have no identity concept to suspend (no auth = no identity). eks-saas-gitops has IRSA roles but suspension requires Terraform code changes and `terraform apply` — too slow for incident response.
- **Compensating Controls**: Network-level blocks (security groups, WAF rules) as emergency kill switches; pre-create IAM deny-all policy for eks-saas-gitops.
- **Portfolio-Level Recommendation**: When implementing the shared Cognito pool (AUTH-Q1 remediation), each agent gets a unique App Client. Suspension = disable the App Client in Cognito (seconds, no code change). For eks-saas-gitops, create a pre-provisioned "agent-emergency-deny" IAM policy and a Lambda-backed API for immediate attachment.
- **Estimated Effort**: Low (built into AUTH-Q1 remediation for application services; 1–2 weeks for eks-saas-gitops kill switch)

#### STATE-Q1: Compensation and Rollback

- **Severity**: RISK-SAFETY in 4 of 4 applicable services (eks-saas-gitops is N/A)
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api
- **Common Finding**: No saga patterns, compensating transactions, or undo endpoints across any application service. local-monolith has MySQL transactions for atomic operations but no compensation for multi-step fulfillment workflow. aws-microservices has EventBridge→SQS→ordering checkout with no rollback if partial failure occurs. unishop-monolith and books-api have simple INSERT/DELETE with no multi-step coordination.
- **Compensating Controls**: Agent is scoped to read-only, eliminating the need for write rollback in current scope. For future write-enabled scope, implement compensation at agent orchestration layer.
- **Portfolio-Level Recommendation**: Document compensating transaction patterns as a portfolio standard before expanding any service to write-enabled agent scope. Prioritize aws-microservices (checkout flow) and local-monolith (fulfillment workflow) for saga pattern implementation.
- **Estimated Effort**: High (60–90 days per service for saga implementation)

#### STATE-Q5: Rate Limiting and Throttling

- **Severity**: RISK-SAFETY in 4 of 4 applicable services (eks-saas-gitops is N/A)
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api
- **Common Finding**: No rate limiting at any layer across any application service. unishop-monolith runs directly on EC2 port 8080 with no API Gateway or WAF. aws-microservices has no API Gateway throttling or usage plans. local-monolith has a WAF but with no rate-based rules. books-api has no usage plan on API Gateway. A runaway agent loop could overwhelm any service at machine speed.
- **Compensating Controls**: AWS account-level API Gateway throttling (10,000 RPS) provides minimal protection for aws-microservices and books-api. App Runner MaxConcurrency:100 provides partial back-pressure for local-monolith.
- **Portfolio-Level Recommendation**: Deploy API Gateway with usage plans and per-agent-key throttling for all services. This is a prerequisite for safe agent traffic. For unishop-monolith: add API Gateway in front of EC2. For aws-microservices: add usage plans. For local-monolith: add WAF rate-based rules. For books-api: add usage plan to existing API Gateway.
- **Estimated Effort**: Low–Medium (7–30 days per service)

#### DATA-Q2: Data Residency and Sovereignty

- **Severity**: RISK-SAFETY in 4 of 4 applicable services (eks-saas-gitops is N/A)
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api
- **Common Finding**: No data residency documentation or controls exist in any application service. aws-microservices has CDK env commented out (environment-agnostic deployment). All services store data with no documented region constraints or compliance references (GDPR, LGPD, HIPAA). books-api data is non-sensitive reference data with low regulatory risk.
- **Compensating Controls**: books-api catalog data has no PII and low residency risk. For PII-containing services, ensure agent-LLM communication stays within the same AWS region.
- **Portfolio-Level Recommendation**: Document a portfolio-wide data residency policy. Classify each service's data residency requirements. For services with PII (unishop-monolith, aws-microservices, local-monolith), ensure deployment regions are pinned and agents use same-region Amazon Bedrock endpoints.
- **Estimated Effort**: Low (documentation: 1 week; enforcement via CDK/CloudFormation: 1–2 weeks)

#### DATA-Q6: PII Redaction in Logs

- **Severity**: RISK-SAFETY in 4 of 4 applicable services (eks-saas-gitops is N/A)
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api
- **Common Finding**: PII is not redacted from logs in any application service. aws-microservices logs full checkout payloads including `firstName`, `lastName`, `email`, `address`, `cardInfo` via `console.log`. local-monolith has `die()` with `$e->getMessage()` that may contain SQL with customer data. unishop-monolith has `e.printStackTrace()` that may dump email addresses. books-api pre-traffic hook logs full DynamoDB items (low risk as data is non-PII catalog data).
- **Compensating Controls**: Implement centralized error handlers returning sanitized messages; add CloudWatch log metric filters to detect PII patterns; restrict log access.
- **Portfolio-Level Recommendation**: Adopt a portfolio-wide structured logging standard with field-level allowlists (log only explicitly permitted fields). For Java (unishop-monolith): SLF4J/Logback with PII masking patterns. For Node.js (aws-microservices): `@aws-lambda-powertools/logger`. For PHP (local-monolith): centralized error handler with log scrubbing. For TypeScript (books-api): structured logging library.
- **Estimated Effort**: Low–Medium (14–30 days per service)

### Cross-Cutting RISK-QUALITY — Same Quality Risk in 3+ Repos

> These are RISK-QUALITY questions that appear in 3 or more repositories.
> They represent portfolio-wide quality patterns to address as capacity allows.
> Questions scored as N/A for a service do not count as gaps for that service.

#### API-Q2: Machine-Readable API Specification

- **Severity**: RISK-QUALITY in 4 of 4 applicable services (eks-saas-gitops is N/A)
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api
- **Common Finding**: No OpenAPI, AsyncAPI, or machine-readable API specification exists in any application service. API surfaces are defined only in source code (Java annotations, CDK constructs, PHP regex patterns, SAM events).
- **Portfolio-Level Recommendation**: Generate OpenAPI 3.0 specifications for all application services. For unishop-monolith: add `springdoc-openapi-ui`. For aws-microservices: export from deployed API Gateway. For local-monolith: manual generation from PHP routes. For books-api: use SAM `DefinitionBody`.
- **Estimated Effort**: Low (7–14 days per service)

#### API-Q3: Structured Error Responses

- **Severity**: RISK-QUALITY in 4 of 4 applicable services (eks-saas-gitops is N/A)
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api
- **Common Finding**: No structured error responses across the portfolio. unishop-monolith returns empty bodies with HTTP status codes. aws-microservices returns error stacks in production. local-monolith returns raw exception messages. books-api returns empty bodies on error.
- **Portfolio-Level Recommendation**: Define a portfolio-wide error response schema: `{"error_code": "...", "message": "...", "retryable": true/false}`. Implement per service.
- **Estimated Effort**: Low (7–14 days per service)

#### HITL-Q3: Sandbox/Staging Environment

- **Severity**: RISK-QUALITY in 4 of 4 applicable services (eks-saas-gitops is N/A)
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api
- **Common Finding**: No agent-testing-focused staging environments. local-monolith has docker-compose for local dev. books-api has a staging environment in the CI/CD pipeline. aws-microservices and unishop-monolith have no staging at all. None have agent-specific test data or documented agent testing processes.
- **Portfolio-Level Recommendation**: Create a portfolio-wide staging environment strategy with agent test data scripts and documented agent testing processes for each service.
- **Estimated Effort**: Medium (14–30 days per service)

#### DATA-Q3: Selective Query Support

- **Severity**: RISK-QUALITY in 4 of 4 applicable services (eks-saas-gitops is N/A)
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api
- **Common Finding**: All application services return unbounded result sets. `SELECT *` without LIMIT/OFFSET in MySQL services. DynamoDB `ScanCommand` without pagination in serverless services. No filtering or sorting parameters accepted on any list endpoint.
- **Portfolio-Level Recommendation**: Add pagination (limit/offset/cursor) to all list endpoints across the portfolio. Default to `limit=50` if no parameter provided.
- **Estimated Effort**: Low (7–14 days per service)

#### DATA-Q4: System of Record Designations

- **Severity**: RISK-QUALITY in 4 of 4 applicable services (eks-saas-gitops is N/A)
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api
- **Common Finding**: No formal system-of-record designations in any service. Each database is the de facto SoR but this is not documented.
- **Portfolio-Level Recommendation**: Create a portfolio-wide data ownership document mapping each domain to its authoritative service.
- **Estimated Effort**: Low (7–14 days — documentation only)

#### DATA-Q5: Temporal Metadata and Freshness

- **Severity**: RISK-QUALITY in 4 of 4 applicable services (eks-saas-gitops is N/A)
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api
- **Common Finding**: Incomplete or hidden temporal metadata. unishop-monolith has `creation_date`/`last_modified_date` columns but they are `@JsonIgnore` — hidden from API responses. aws-microservices has `orderDate` only on orders; products and baskets have no timestamps. local-monolith has timestamps on orders but not on inventory. books-api has no temporal fields at all. None return `Cache-Control` or freshness headers.
- **Portfolio-Level Recommendation**: Add `created_at`/`updated_at` (ISO 8601 UTC) to all entities. Expose in API responses. Return `Cache-Control` and `Last-Modified` headers.
- **Estimated Effort**: Low (7–14 days per service)

#### DISC-Q1: Schema Versioning and API Contracts

- **Severity**: RISK-QUALITY in 4 of 4 applicable services (eks-saas-gitops is N/A)
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api
- **Common Finding**: No API versioning, no schema versioning, no breaking change detection in any service. API paths have no version prefix. No database migration tooling (only inline CREATE TABLE in local-monolith and DDL scripts in unishop-monolith).
- **Portfolio-Level Recommendation**: Add `/v1/` prefix to all API paths. Generate and commit OpenAPI specs. Add breaking change detection to CI pipelines.
- **Estimated Effort**: Medium (14–30 days per service)

#### OBS-Q1: Distributed Tracing and Structured Logging

- **Severity**: RISK-QUALITY in 5 of 5 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops
- **Common Finding**: Limited or no distributed tracing. books-api has X-Ray tracing enabled but no structured application logging. All others have no tracing. Logging is unstructured across the portfolio: `System.out.println` (unishop-monolith), `console.log` (aws-microservices), PHP `error_log` (local-monolith), no EKS control plane logging (eks-saas-gitops).
- **Portfolio-Level Recommendation**: Deploy a shared observability stack: enable X-Ray tracing for all Lambda-based services, add OpenTelemetry for EKS workloads, and adopt structured JSON logging across the portfolio.
- **Estimated Effort**: Medium (14–30 days per service)

#### OBS-Q2: Alerting on Error Rates and Latency

- **Severity**: RISK-QUALITY in 5 of 5 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops
- **Common Finding**: No operational alerting across the portfolio. books-api has deployment-time error alarms (tied to CodeDeploy rollback) but no operational alerting. All others have zero CloudWatch alarms. No PagerDuty/OpsGenie/SNS integration anywhere.
- **Portfolio-Level Recommendation**: Define CloudWatch alarms in IaC for each service: 5xx error rate, P99 latency, CPU/memory utilization. Configure a shared SNS topic for operator notifications.
- **Estimated Effort**: Low (7–14 days per service)

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface

- **Severity**: RISK-QUALITY in 5 of 5 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops
- **Common Finding**: Inconsistent infrastructure governance. unishop-monolith has no IaC at all. aws-microservices has CDK but no peer review or drift detection. local-monolith has CloudFormation but manual deployment. books-api has SAM + CDK pipeline with manual approval (best in portfolio). eks-saas-gitops has comprehensive Terraform but `--auto-approve` and no drift detection.
- **Portfolio-Level Recommendation**: Require IaC for all services. Enable branch protection and PR reviews. Add AWS Config drift detection rules.
- **Estimated Effort**: Medium (14–30 days for unishop-monolith IaC creation; 7–14 days for governance improvements on others)

#### ENG-Q2: CI/CD with API Contract Testing

- **Severity**: RISK-QUALITY in 5 of 5 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops
- **Common Finding**: No API contract testing in any CI pipeline. books-api has the most mature CI/CD (build → test → staging → production with manual approval) but still lacks contract tests. unishop-monolith, aws-microservices, and local-monolith have no CI/CD pipeline at all. eks-saas-gitops has build-and-push CI with no testing.
- **Portfolio-Level Recommendation**: Implement CI/CD pipelines for all services with API contract validation using OpenAPI spec diffs.
- **Estimated Effort**: High (30–60 days per service without CI/CD; 14 days to add contract tests for books-api)

#### ENG-Q3: Rollback Capability

- **Severity**: RISK-QUALITY in 5 of 5 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops
- **Common Finding**: Limited rollback capability. books-api has excellent rollback (Linear10PercentEvery1Minute with CloudWatch alarm-based automatic rollback via CodeDeploy). eks-saas-gitops has Flux GitOps reconciliation (git revert triggers rollback) but no automated triggers. unishop-monolith, aws-microservices, and local-monolith have no automated rollback.
- **Portfolio-Level Recommendation**: Implement automated rollback for all services. Leverage CodeDeploy for EC2 services, Lambda aliases with traffic shifting for serverless, and Flagger for EKS.
- **Estimated Effort**: Medium–High (14–60 days per service)

#### ENG-Q4: API Test Coverage

- **Severity**: RISK-QUALITY in 5 of 5 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops
- **Common Finding**: Low or zero test coverage. books-api has unit tests (6 tests) and e2e tests (4 tests) — best in portfolio. aws-microservices has a test file but all tests are commented out. unishop-monolith, local-monolith, and eks-saas-gitops have zero test files.
- **Portfolio-Level Recommendation**: Establish minimum test coverage requirements for agent-facing endpoints. Prioritize API integration tests for endpoints agents will consume.
- **Estimated Effort**: Medium–High (30–60 days per service)

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data

- **Severity**: RISK-QUALITY in 5 of 5 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops
- **Common Finding**: Encryption at rest varies widely. local-monolith has comprehensive KMS encryption (RDS, ECR, VPC Flow Logs). books-api has DynamoDB SSE with AWS-managed keys. aws-microservices uses default DynamoDB encryption only. unishop-monolith has no demonstrated encryption. eks-saas-gitops uses service-managed encryption with no customer-managed KMS keys.
- **Portfolio-Level Recommendation**: Define a portfolio-wide encryption standard requiring customer-managed KMS keys for all data stores containing PII or Confidential data. Minimum: AWS-managed SSE for all other data stores.
- **Estimated Effort**: Medium (14–30 days per service)

## Service Dependency Map

> Dependencies were inferred from individual ARA report findings (not explicitly provided via `dependency_overrides`). Inferred dependencies may be incomplete — they reflect only what was observable in the assessed code and report context. For authoritative dependency data, add `dependency_overrides` to the portfolio config.

### Dependency Overview

| Source Service | Target Service | Type | Description | Inferred |
|---------------|---------------|------|-------------|----------|
| unishop-monolith | eks-saas-gitops | shared_infra | EKS is the target platform for monolith decomposition into containerized microservices (per portfolio context: "modernizing legacy monoliths into containerized microservices on EKS") | Yes |
| local-monolith | eks-saas-gitops | shared_infra | EKS is the centralized platform for non-serverless workloads (per portfolio config context: "everything that is not serverless will run here") | Yes |

### Service Dependency Metrics

| Service | Fan-In | Fan-Out | Role | Readiness Profile |
|---------|--------|---------|------|-------------------|
| eks-saas-gitops | 2 | 0 | Foundation | Pilot-Ready (Safety Concerns) |
| unishop-monolith | 0 | 1 | Leaf | Remediation Required |
| local-monolith | 0 | 1 | Leaf | Remediation Required |
| aws-microservices | 0 | 0 | Independent | Remediation Required |
| books-api | 0 | 0 | Independent | Remediation Required |

### High-Risk Dependency Patterns

1. **Foundation Service with RISK-SAFETY Findings**: eks-saas-gitops is the foundation service (fan-in: 2, fan-out: 0) with 4 RISK-SAFETY findings including AUTH-Q2 (AdministratorAccess on IRSA roles). All services that will deploy on this platform inherit the platform's security posture.
   - **Affected Services**: unishop-monolith, local-monolith (and potentially all containerized services post-decomposition)
   - **Risk**: If Argo Workflows or TF Controller IRSA roles are compromised, all workloads on the EKS cluster are affected. The `AdministratorAccess` policy and wildcard Kubernetes ClusterRoles create maximum blast radius.
   - **Recommendation**: Prioritize replacing `AdministratorAccess` with scoped policies on eks-saas-gitops before onboarding monolith workloads to EKS. Create a dedicated agent IRSA role with minimum required permissions.

2. **No Transitive BLOCKER Propagation**: eks-saas-gitops (foundation) has 0 BLOCKERs, so its Pilot-Ready (Safety Concerns) profile does not hard-block dependent services. However, the 4 RISK-SAFETY findings should be remediated before expanding agent operations on the platform.
   - **Affected Services**: unishop-monolith, local-monolith
   - **Risk**: Low (no hard blocks). Medium for safety — platform-level RISK-SAFETY findings affect all hosted workloads.
   - **Recommendation**: Remediate eks-saas-gitops RISK-SAFETY findings (especially AUTH-Q2) before deploying agent-integrated workloads on EKS.

3. **Independent Serverless Services**: aws-microservices and books-api are self-contained serverless services with no inferred dependencies on other portfolio services. Their readiness can be improved independently.
   - **Affected Services**: aws-microservices, books-api
   - **Risk**: None (no dependency-related risk)
   - **Recommendation**: These services can begin AUTH-Q1 and DATA-Q1 remediation independently without coordination.

## Portfolio Remediation Guidance

> Portfolio context: Evaluating the e-commerce platform portfolio for both autonomous AI agent integration and cloud-native modernization. The team is building a customer support agent that handles order inquiries, processes returns, and manages inventory restocking — while simultaneously modernizing legacy monoliths into containerized microservices on EKS.

### Remediation Priority Order

Remediation of cross-cutting BLOCKERs should follow this general priority:

1. **Identity and Access** — Resolve AUTH-section BLOCKERs first. You cannot enforce any other security control without machine identity and scoped permissions.
2. **Data Integrity** — Resolve STATE and DATA-section BLOCKERs second. Protect data before enabling agent write operations.
3. **API Surface** — Resolve API-section BLOCKERs third. Ensure a stable, documented integration surface for agent tools.
4. **Remaining BLOCKERs** — Address in order of affected service count (most affected first).

### Coordinated Remediation Plan

#### Identity Foundation

**BLOCKERs addressed**: AUTH-Q1
**Services affected**: unishop-monolith, aws-microservices, local-monolith, books-api

- **What to do**:
  1. Provision a shared Amazon Cognito User Pool with resource servers and custom scopes for the portfolio
  2. Create per-agent App Clients with `client_credentials` grant — each agent identity gets unique credentials
  3. Integrate each service with the shared Cognito pool:
     - **books-api** (lowest effort): Add `client_credentials` flow to existing Cognito User Pool, or migrate to the shared pool
     - **aws-microservices**: Add Cognito authorizer to all 3 API Gateway REST APIs in CDK
     - **unishop-monolith**: Enable existing Spring Security OAuth2 resource server (framework already present, just disabled)
     - **local-monolith**: Add API key authentication middleware or OAuth2 bearer token validation
  4. Use the eks-saas-gitops IRSA pattern as template for Kubernetes-hosted services post-decomposition
- **Expected outcome**: All API endpoints require authentication. Each agent call is attributable by client_id. AUTH-Q2, AUTH-Q3, AUTH-Q6, and AUTH-Q7 remediation is unblocked.
- **Effort**: High (platform: 2 weeks; per-service: 2–4 weeks each)

#### Data Classification and Protection

**BLOCKERs addressed**: DATA-Q1
**Services affected**: unishop-monolith, aws-microservices, local-monolith, books-api

- **What to do**:
  1. Create a portfolio-wide data classification policy (Public / Internal / Confidential / Restricted)
  2. Classify each service's data stores:
     - **books-api**: Public (isbn, title, author — non-PII catalog data). Tag DynamoDB table with `data-classification: public`. Effort: hours.
     - **aws-microservices**: Confidential (order table has firstName, lastName, email, address, cardInfo). Tag tables. Implement field-level encryption for `cardInfo` and `email` with KMS. Effort: 4–8 weeks.
     - **local-monolith**: Confidential (customer_name, customer_email, shipping_address across 9 tables). Implement API response filtering for agent endpoints. Effort: 2–4 weeks.
     - **unishop-monolith**: Confidential (email, first_name, last_name in unicorn_user). Add `@JsonIgnore` on PII fields for agent-facing DTOs. Effort: 1–2 weeks.
  3. Deploy Amazon Macie for automated PII detection across DynamoDB and S3
- **Expected outcome**: All data stores have classification tags. Agent-facing endpoints return only non-PII data (or explicitly authorized PII with audit logging). Agents can programmatically verify data safety.
- **Effort**: Medium (policy: 1 week; per-service: hours to 8 weeks depending on PII complexity)

## Agentic Program Recommendations

> These are engagement-level recommendations based on the portfolio's agentic readiness
> profile. Discuss with your AWS Solutions Architect to determine eligibility and timing.

| Program | Relevance | Trigger Findings | Suggested Timing | Next Step |
|---------|-----------|-----------------|------------------|-----------|
| AI DLC | Portfolio shows manual development workflows and lack of CI/CD across 3 of 5 services | 3/4 application services have no CI/CD (ENG-Q2); all 5 services have ENG RISK-QUALITY findings; zero or minimal test coverage across portfolio | Run first — before agentic work | Request engagement via AWS Solutions Architect |
| AgentStorming | 80% of services require remediation despite clear agent use cases — structured agent opportunity identification would help prioritize which services to remediate first | 4/5 services are Remediation Required; portfolio context describes specific agent use cases but all target services have BLOCKERs | Run after AI DLC, before remediation begins | Request engagement via AWS Solutions Architect |

### Program Details

#### AI DLC (AI Driven Development Lifecycle)

- **Why triggered**: The portfolio demonstrates predominantly manual development workflows. 3 of 4 application services (unishop-monolith, aws-microservices, local-monolith) have no CI/CD pipeline. All 5 services have RISK-QUALITY findings in the Engineering category (ENG-Q1 through ENG-Q5). Test coverage is near-zero across the portfolio. These findings indicate teams that would benefit from adopting AI-driven development practices to accelerate remediation and modernization.
- **What it provides**: Workshop for adopting the AI Driven Development Lifecycle, emphasizing AI Powered Execution with Human Oversight and Dynamic Team Collaboration. AI creates detailed work plans, seeks clarification, and defers critical decisions to humans. Teams unite in collaborative spaces for real-time problem solving and rapid decision-making.
- **Suggested timing**: Run first — before beginning agentic readiness remediation. Establishing AI-assisted development practices will accelerate the AUTH-Q1 and DATA-Q1 remediation across all 4 affected services.
- **Recommended scope**: All 5 services. Focus on the 3 services without CI/CD (unishop-monolith, aws-microservices, local-monolith) for the highest impact.
- **Next step**: Request AI DLC engagement via AWS Solutions Architect.

#### AgentStorming

- **Why triggered**: Despite a clear portfolio context describing specific agent use cases (customer support agent handling order inquiries, returns, inventory restocking), 80% of services (4/5) are Remediation Required. The gap between the defined agent vision and the current readiness state suggests benefit from structured agent opportunity identification to prioritize which services to remediate first and which agent capabilities to target initially.
- **What it provides**: A workshop format that builds on EventStorming by adding Cognitive Complexity Analysis and Agentic Workflow Design. Pinpoints where agentic AI delivers real value versus traditional automation. Gives the team a structured, repeatable path from "where should we use AI?" to a qualified, implementation-ready answer.
- **Suggested timing**: Run after AI DLC, before beginning remediation. AgentStorming output will inform which services to prioritize for AUTH-Q1/DATA-Q1 remediation and which agent capabilities to target in the initial pilot.
- **Recommended scope**: Focus on the customer support agent use case across the 3 P0 services (unishop-monolith, aws-microservices, local-monolith) and the P1 books-api. Identify which agent tools map to which service endpoints and prioritize remediation accordingly.
- **Next step**: Request AgentStorming engagement via AWS Solutions Architect.

#### AXE (Agentic Experience Workshop)

> Not triggered. Fewer than 3 services in Pilot-Ready or Agent-Ready state (only 1: eks-saas-gitops at Pilot-Ready Safety Concerns). Re-assess after remediating AUTH-Q1 and DATA-Q1 — resolving these 2 BLOCKERs across the 4 application services could move multiple services to Pilot-Ready, triggering AXE eligibility.

#### EBA on Agentic AI (Experience-Based Acceleration)

> Not triggered. No single cross-cutting BLOCKER affects 5 or more repositories. AUTH-Q1 and DATA-Q1 each affect 4 repos (not 5). If the portfolio grows to 5+ application services and the same BLOCKERs persist, EBA may be triggered.

## Portfolio-Level Findings

> These questions evaluate capabilities that can only be assessed by looking across
> multiple repos. They are distinct from cross-cutting analysis (which aggregates
> individual findings). Individual report findings are never overridden.

### PORT-ARA-Q1: Centralized Identity Plane

- **Severity**: BLOCKER
- **Finding**: No shared identity provider exists across the portfolio. books-api has its own Amazon Cognito User Pool (`CognitoUserPool` in `template.yml`) with OAuth2 implicit flow and `COGNITO` identity provider, but no other service references it. eks-saas-gitops uses IRSA (IAM Roles for Service Accounts) with OIDC federation for Kubernetes workload identity — this is a machine identity mechanism but scoped to the EKS cluster and not accessible to application-level services. unishop-monolith has a disabled Spring Security OAuth2 framework with no provider configured. aws-microservices and local-monolith have no identity provider at all. The two identity mechanisms (Cognito in books-api, IRSA in eks-saas-gitops) are completely independent with no cross-service integration.
- **Evidence**: `services/books-api/template.yml` (CognitoUserPool, UserPoolClient, UserPoolDomain), `services/eks-saas-gitops/terraform/modules/gitops-saas-infra/main.tf` (7 IRSA roles with OIDC), absence of shared Cognito references in other services
- **Recommendation**: Provision a portfolio-wide Amazon Cognito User Pool with resource servers for each service. Create per-agent App Clients with `client_credentials` grant. Either extend the books-api Cognito as the shared pool or create a new centralized pool. Integrate all 4 application services. For eks-saas-gitops, the existing IRSA mechanism covers Kubernetes workloads; bridge to Cognito if agents need to interact with both application APIs and the EKS control plane.
- **Affected Services**: All 5 services
- **Contextual Annotations**: This finding directly relates to the AUTH-Q1 cross-cutting BLOCKER. Provisioning a shared Cognito User Pool resolves both PORT-ARA-Q1 and AUTH-Q1 simultaneously.

### PORT-ARA-Q2: Cross-Service Audit Correlation

- **Severity**: RISK
- **Finding**: No cross-service audit correlation mechanism exists. books-api has X-Ray tracing enabled (`Tracing: Active`, `TracingEnabled: true`, `aws-xray-sdk-core`) — the only service with distributed tracing. However, no other service has X-Ray or any tracing instrumentation. No shared CloudTrail trail is defined in any repository. No consistent trace ID headers (`X-Amzn-Trace-Id`, `traceparent`) are propagated across services. No centralized log aggregation (no shared CloudWatch Log Group, no S3 audit bucket) is configured. Each service logs independently with no correlation mechanism.
- **Evidence**: `services/books-api/template.yml` (Tracing: Active, TracingEnabled: true), all other service reports (no tracing configuration), absence of CloudTrail resources in any repository
- **Recommendation**: Enable X-Ray tracing across all Lambda-based services (aws-microservices, books-api). Add OpenTelemetry instrumentation for EC2/EKS services (unishop-monolith, local-monolith, eks-saas-gitops). Deploy a shared CloudTrail trail at the account level with S3 bucket (object lock enabled). Establish a standard trace ID header propagation convention across all services.
- **Affected Services**: All 5 services
- **Contextual Annotations**: This finding provides context for the AUTH-Q6 cross-cutting RISK-SAFETY. A shared CloudTrail trail would partially mitigate AUTH-Q6 for all services — **verify** that each service's API calls are captured by the trail.

### PORT-ARA-Q3: Portfolio-Level Rate Limiting

- **Severity**: RISK
- **Finding**: No shared API gateway, WAF, or rate limiting configuration protects the portfolio perimeter. local-monolith has its own WAF Web ACL but with no rate-based rules — it has IP whitelisting and AWS Managed Rules only. books-api and aws-microservices have API Gateway but no usage plans or throttling configuration. unishop-monolith runs directly on EC2 port 8080 with no gateway layer. eks-saas-gitops has no WAF or API Gateway. Each service manages (or fails to manage) its own rate limiting independently. There is no portfolio-level protection against agent traffic storms that could span multiple services simultaneously.
- **Evidence**: `monolith/infrastructure/monolith-apprunner.yaml` (WebACL with no rate rules), `services/aws-microservices/lib/apigateway.ts` (no usage plans), `services/books-api/template.yml` (no UsagePlan), absence of shared WAF or API Gateway resources
- **Recommendation**: Deploy a shared AWS WAF WebACL with rate-based rules covering all public-facing services. Configure per-agent rate limits across the portfolio. For the customer support agent use case, define a portfolio-wide rate limit (e.g., 500 requests/minute per agent identity) enforced at the shared WAF level.
- **Affected Services**: All application services (unishop-monolith, aws-microservices, local-monolith, books-api)
- **Contextual Annotations**: This finding provides context for the STATE-Q5 cross-cutting RISK-SAFETY. A shared WAF with rate-based rules would partially mitigate STATE-Q5 for all services — **verify** that per-agent throttling is configured at both the portfolio and service level.

### PORT-ARA-Q4: Transitive Dependency Safety

- **Severity**: INFO
- **Finding**: Using the inferred dependency graph and readiness profiles: eks-saas-gitops (Pilot-Ready Safety Concerns, 0 BLOCKERs) is the sole foundation service. unishop-monolith and local-monolith have inferred `shared_infra` dependencies on eks-saas-gitops. No service with profile Agent-Ready or Pilot-Ready depends synchronously on a service with profile Not Agent-Integrable (no services are Not Agent-Integrable). The 4 Remediation Required services are independent of each other — their BLOCKERs (AUTH-Q1, DATA-Q1) are individual, not caused by transitive dependencies. The foundation service (eks-saas-gitops) has 0 BLOCKERs, so it does not propagate blockers to dependent services.
- **Evidence**: Inferred dependency graph (Step 5), readiness profiles from all 5 services
- **Recommendation**: No transitive dependency safety issues at current state. Monitor as services are decomposed — if unishop-monolith is split into microservices on EKS, the dependency on eks-saas-gitops becomes a sync dependency, and any BLOCKERs on eks-saas-gitops would propagate.
- **Affected Services**: unishop-monolith, local-monolith (via dependency on eks-saas-gitops)
- **Contextual Annotations**: None — no transitive blocker propagation detected.

### PORT-ARA-Q5: Agent Identity Governance

- **Severity**: RISK
- **Finding**: No centralized mechanism exists to suspend or revoke agent identities across all services simultaneously. books-api's Cognito supports `adminDisableUser` but only for its own User Pool. eks-saas-gitops IRSA roles can be deactivated by modifying Terraform, but this is slow (minutes to hours). unishop-monolith, aws-microservices, and local-monolith have no identity mechanism at all (no Cognito, no API keys, no service accounts). There is no portfolio-wide agent identity registry, no centralized kill switch, and no operational runbook for revoking all agent access in an emergency.
- **Evidence**: `services/books-api/template.yml` (CognitoUserPool — single-service scope), `services/eks-saas-gitops/terraform/modules/gitops-saas-infra/main.tf` (IRSA roles — Terraform-managed), absence of centralized identity management in other services
- **Recommendation**: When implementing the shared Cognito User Pool (AUTH-Q1 remediation), design a centralized agent identity governance layer: (1) all agent App Clients are registered in the shared pool, (2) a "kill all agents" Lambda function can disable all agent App Clients within seconds, (3) an operational runbook documents the agent suspension procedure, (4) for eks-saas-gitops, pre-provision an IAM deny-all policy that can be attached to agent IRSA roles via CLI.
- **Affected Services**: All 5 services
- **Contextual Annotations**: This finding provides context for the AUTH-Q7 cross-cutting RISK-SAFETY. A shared Cognito pool with centralized governance would mitigate AUTH-Q7 for all application services — **verify** that each service's agent identity is managed through the shared pool after implementation.

## Service-by-Service Summary

| Service | Repo Type | Agent Scope | Readiness Profile | BLOCKERs | RISKs | INFOs | N/A |
|---------|-----------|-------------|-------------------|----------|-------|-------|-----|
| unishop-monolith | application | read-only | 🟠 Remediation Required | 2 | 22 | 13 | 0 |
| aws-microservices | application | read-only | 🟠 Remediation Required | 2 | 25 | 16 | 0 |
| local-monolith | application | read-only | 🟠 Remediation Required | 2 | 22 | 17 | 0 |
| books-api | application | read-only | 🟠 Remediation Required | 2 | 23 | 12 | 0 |
| eks-saas-gitops | infrastructure-only | read-only | 🟡 Pilot-Ready (Safety Concerns) | 0 | 13 | 1 | 29 |

### Individual Service Details

#### unishop-monolith

- **Readiness Profile**: Remediation Required
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P0
- **BLOCKERs** (2):
  - AUTH-Q1: Spring Security OAuth2 present but entirely disabled (`permitAll()` on all endpoints) — no machine identity
  - DATA-Q1: PII (email, first_name, last_name) in `unicorn_user` table exposed in API responses without classification
- **RISKs** (22):
  - RISK-SAFETY (8): AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q5, DATA-Q2, DATA-Q6
  - RISK-QUALITY (14): API-Q2, API-Q3, HITL-Q3, DATA-Q3, DATA-Q4, DATA-Q5, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4, ENG-Q5
- **Key Recommendations**:
  - Enable existing Spring Security OAuth2 resource server with Cognito provider (AUTH-Q1)
  - Classify PII fields and implement response filtering for agent endpoints (DATA-Q1)
  - Create IaC (CloudFormation/CDK) for the EC2 infrastructure (ENG-Q1)
- **Depends On**: eks-saas-gitops (shared_infra — target EKS platform for decomposition)
- **Depended On By**: None

#### aws-microservices

- **Readiness Profile**: Remediation Required
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P0
- **BLOCKERs** (2):
  - AUTH-Q1: All 3 API Gateway REST APIs completely open — no authorizer, no API keys, no IAM auth
  - DATA-Q1: Order DynamoDB table stores PII and payment card info (`cardInfo`) without classification or field-level encryption
- **RISKs** (25):
  - RISK-SAFETY (9): AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q4, STATE-Q5, DATA-Q2, DATA-Q6
  - RISK-QUALITY (16): API-Q2, API-Q3, API-Q6, HITL-Q3, DATA-Q3, DATA-Q4, DATA-Q5, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4, ENG-Q5, STATE-Q7
- **Key Recommendations**:
  - Add API Gateway API key authentication with usage plans to all 3 REST APIs (AUTH-Q1)
  - Implement field-level encryption for `cardInfo` and `email` in DynamoDB with KMS (DATA-Q1)
  - Add circuit breakers and resilience patterns to AWS SDK clients (STATE-Q4 — unique to this service)
- **Depends On**: None (self-contained serverless)
- **Depended On By**: None

#### local-monolith

- **Readiness Profile**: Remediation Required
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P0
- **BLOCKERs** (2):
  - AUTH-Q1: PHP session-based authentication only — no OAuth2, no API keys, no machine identity
  - DATA-Q1: Customer PII (names, emails, addresses) across 9 MySQL tables with no classification or access controls
- **RISKs** (22):
  - RISK-SAFETY (8): AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q5, DATA-Q2, DATA-Q6
  - RISK-QUALITY (14): API-Q2, API-Q3, HITL-Q3, DATA-Q3, DATA-Q5, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4, STATE-Q2, STATE-Q7
- **Key Recommendations**:
  - Add API key authentication middleware as parallel auth path alongside PHP sessions (AUTH-Q1)
  - Create data classification inventory for all 9 tables and implement API response filtering (DATA-Q1)
  - Add WAF rate-based rules to existing WAF configuration (STATE-Q5 — quick win)
- **Depends On**: eks-saas-gitops (shared_infra — centralized EKS platform)
- **Depended On By**: None

#### books-api

- **Readiness Profile**: Remediation Required
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P1
- **BLOCKERs** (2):
  - AUTH-Q1: Cognito User Pool exists but only with implicit flow for humans — no client_credentials for agents
  - DATA-Q1: DynamoDB table lacks classification tags (data is non-PII catalog data but no auditable proof)
- **RISKs** (23):
  - RISK-SAFETY (8): AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q5, DATA-Q2, DATA-Q6
  - RISK-QUALITY (15): API-Q2, API-Q3, HITL-Q3, DATA-Q3, DATA-Q4, DATA-Q5, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4, ENG-Q5, STATE-Q2
- **Key Recommendations**:
  - Add Cognito App Client with `client_credentials` flow (AUTH-Q1 — lowest effort in portfolio: 1–2 days)
  - Add `data-classification: public` and `contains-pii: false` tags to DynamoDB table (DATA-Q1 — hours)
  - Add GET /books/{isbn} endpoint for targeted agent lookups (STATE-Q2)
- **Depends On**: None (self-contained serverless)
- **Depended On By**: None

#### eks-saas-gitops

- **Readiness Profile**: Pilot-Ready (Safety Concerns)
- **Repo Type**: infrastructure-only
- **Agent Scope**: read-only
- **Priority**: P1
- **BLOCKERs** (0): None
- **RISKs** (13):
  - RISK-SAFETY (4): AUTH-Q2 (AdministratorAccess on IRSA roles), AUTH-Q3 (wildcard Kubernetes ClusterRoles), AUTH-Q6 (no CloudTrail or EKS audit logging), AUTH-Q7 (no automated agent identity suspension)
  - RISK-QUALITY (9): AUTH-Q1 (no agent-specific IRSA role), AUTH-Q5 (SSM credentials with no rotation, hardcoded test password), OBS-Q1 (no distributed tracing), OBS-Q2 (no alerting), ENG-Q1 (`--auto-approve`, no drift detection), ENG-Q2 (no testing in CI), ENG-Q3 (no automated rollback triggers), ENG-Q4 (zero test coverage), ENG-Q5 (no customer-managed KMS)
- **Key Recommendations**:
  - Replace `AdministratorAccess` on Argo Workflows and TF Controller IRSA roles with scoped policies (AUTH-Q2 — highest priority)
  - Enable EKS control plane audit logging via `cluster_enabled_log_types` (AUTH-Q6 — quick win)
  - Create a dedicated agent IRSA role following existing patterns (AUTH-Q1 — RISK-QUALITY)
- **Depends On**: None (foundation service)
- **Depended On By**: unishop-monolith, local-monolith

## Analysis Inventory

| # | Service | Report File | Analysis Date | Repo Type | Agent Scope |
|---|---------|-------------|-----------------|-----------|-------------|
| 1 | unishop-monolith | `./services/unishop-monolith-to-microservices/MonoToMicroLegacy/MonoToMicroLegacy-ara-report.md` | 2026-04-17 | application | read-only |
| 2 | aws-microservices | `./services/aws-microservices/aws-microservices-ara-report.md` | 2026-04-17 | application | read-only |
| 3 | local-monolith | `./monolith/monolith-ara-report.md` | 2025-07-17 | application | read-only |
| 4 | books-api | `./services/books-api/books-api-ara-report.md` | 2026-04-17 | application | read-only |
| 5 | eks-saas-gitops | `./services/eks-saas-gitops/eks-saas-gitops-ara-report.md` | 2026-04-17 | infrastructure-only | read-only |

---

*End of Portfolio Agentic Readiness Analysis Report*
