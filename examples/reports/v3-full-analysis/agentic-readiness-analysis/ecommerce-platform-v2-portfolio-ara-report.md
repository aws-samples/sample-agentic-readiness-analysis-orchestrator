# Portfolio Agentic Readiness Analysis Report

**Date**: 2026-04-27
**Services Analyzed**: 5
**Portfolio Context**: Evaluating the e-commerce platform portfolio for both autonomous AI agent integration and cloud-native modernization. The team is building a customer support agent that handles order inquiries, processes returns, and manages inventory restocking — while simultaneously modernizing legacy monoliths into containerized microservices on EKS.

---

## Executive Dashboard

### Readiness Distribution

| Profile | Services | Percentage | Description |
|---------|----------|------------|-------------|
| ✅ Agent-Ready | 0 | 0% | 0 blockers, 0 RISK-SAFETY — broad agent deployment |
| 🟡 Pilot-Ready | 0 | 0% | 0 blockers, 1–2 RISK-SAFETY — narrow pilot |
| 🟡 Pilot-Ready (Safety Concerns) | 0 | 0% | 0 blockers, 3+ RISK-SAFETY — supervised pilot, prioritize safety |
| 🟠 Remediation Required | 5 | 100% | 1–2 blockers — remediate before any agent deployment |
| ❌ Not Agent-Integrable | 0 | 0% | 3+ blockers — deferred or descoped |

### Portfolio Summary

| Metric | Value |
|--------|-------|
| Total Services Analyzed | 5 |
| Services Ready for Agents (Agent-Ready + Pilot-Ready) | 0 (0%) |
| Services Requiring Remediation | 5 (100%) |
| Cross-Cutting BLOCKERs (same blocker in 2+ repos) | 2 |
| Cross-Cutting RISKs (same risk in 3+ repos) | 26 |
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
| AUTH | 5 | 100% (5 of 5) | AUTH-Q1 |
| DATA | 4 | 100% (4 of 4) | DATA-Q1 |
| API | 0 | 0% | — |
| STATE | 0 | 0% | — |
| HITL | 0 | 0% | — |
| DISC | 0 | 0% | — |
| OBS | 0 | 0% | — |
| ENG | 0 | 0% | — |

### Readiness Snapshot

| Metric | Value |
|--------|-------|
| analysis_date | 2026-04-27 |
| total_services | 5 |
| agent_ready | 0 |
| pilot_ready | 0 |
| pilot_ready_safety_concerns | 0 |
| remediation_required | 5 |
| not_integrable | 0 |
| total_blockers | 9 |
| total_risks | 112 |
| total_risk_safety | 38 |
| total_risk_quality | 74 |
| total_infos | 54 |
| cross_cutting_blockers | 2 |
| cross_cutting_risks | 26 |
| cross_cutting_risk_safety | 8 |
| cross_cutting_risk_quality | 18 |
| portfolio_level_blockers | 1 |
| portfolio_level_risks | 4 |
| write_enabled_services | 0 |
| read_only_services | 5 |

---

## Cross-Cutting BLOCKERs — Same Blocker in 2+ Repos

> These are BLOCKER-severity questions that appear in 2 or more repositories.
> They represent portfolio-wide agentic readiness gaps requiring coordinated remediation.
> Questions scored as N/A for a service do not count as gaps for that service.

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER in 5 of 5 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops
- **Common Finding**: No machine identity authentication exists across the entire portfolio. Each service uses a different (and insufficient) approach: OAuth2 with `permitAll()` disabling all auth (unishop-monolith), no API Gateway authorizers at all (aws-microservices), session-based `$_SESSION` auth only (local-monolith), Cognito configured for human users only with GET endpoints unauthenticated (books-api), and IRSA roles for infrastructure controllers only with no agent identity mechanism (eks-saas-gitops). None of the 5 services can authenticate an autonomous AI agent as a distinct, auditable machine principal.
- **Root Cause Pattern**: The portfolio was developed without any consideration for machine-to-machine authentication. Authentication mechanisms — where they exist — are designed exclusively for human users (browser sessions, email/password Cognito). The concept of a machine principal with its own identity, credentials, and audit trail does not exist in any service.
- **Portfolio-Level Remediation**:
  - **Approach**: Hybrid — platform-level identity provider + per-service integration
  - **Immediate Action**: Deploy a centralized Amazon Cognito User Pool with a Resource Server and `client_credentials` OAuth2 flow for agent M2M authentication. Create dedicated Cognito App Clients per agent identity with scoped permissions. For the EKS platform (eks-saas-gitops), create dedicated IRSA roles for agent service accounts.
  - **Target State**: Every service requires authenticated agent identity on all endpoints. Agent identities are distinguishable from human users in audit logs. Each agent has scoped credentials that can be individually revoked.
  - **Estimated Effort**: High
  - **Priority**: Critical — affects ALL 5 services; prerequisite for AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7, and DATA-Q1 remediation
  - **Dependencies**: None — this is the foundation. All other security remediations depend on identity existing first.

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER in 4 of 4 applicable services (N/A in eks-saas-gitops — infrastructure-only)
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api
- **Common Finding**: No data classification policy, tagging, or field-level access controls exist across the 4 application services. PII is stored and transmitted without classification: unishop-monolith stores email, first_name, last_name in `unicorn_user` table with no tags; aws-microservices stores firstName, lastName, email, address, cardInfo in DynamoDB order table with no classification tags; local-monolith stores customer_name, customer_email, shipping_address in MySQL without classification; books-api stores book catalog data (isbn, title, author) without formal classification confirming it as non-PII. An agent querying any of these services would receive raw PII/payment data with no filtering or redaction.
- **Root Cause Pattern**: The portfolio has no data classification policy or taxonomy. PII (customer names, emails, addresses) and payment data (cardInfo, paymentMethod) are stored and transmitted without any classification, tagging, or field-level access controls. This is a portfolio-wide governance gap, not a per-service technical issue.
- **Portfolio-Level Remediation**:
  - **Approach**: Hybrid — portfolio-wide classification policy + per-service tagging and filtering
  - **Immediate Action**: Establish a portfolio-wide data classification taxonomy (Public, Internal, Confidential, Restricted). Conduct a data inventory across all 4 application services mapping every PII and payment data field. Deploy Amazon Macie for automated PII detection across data stores.
  - **Target State**: All data stores have classification tags. API responses to agent callers include only fields authorized for the agent's scope and classification level. PII is masked or excluded by default for agent identities. Payment card data (cardInfo) is never returned to agents.
  - **Estimated Effort**: Medium
  - **Priority**: Critical — affects all 4 application services; the customer support agent will handle order data containing PII
  - **Dependencies**: AUTH-Q1 must be resolved first — cannot enforce field-level access controls without knowing which principal is calling

## Cross-Cutting RISKs

### Cross-Cutting RISK-SAFETY — Same Safety Risk in 3+ Repos

> These are RISK-SAFETY questions that appear in 3 or more repositories.
> They represent portfolio-wide agent safety gaps requiring coordinated attention.
> Questions scored as N/A for a service do not count as gaps for that service.

#### AUTH-Q2: Scoped Permissions (Least Privilege)

- **Severity**: RISK-SAFETY in 5 of 5 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops
- **Common Finding**: No agent-specific scoped permissions exist across the portfolio. Application services use either no authorization (permitAll), coarse binary roles (admin/customer), or Lambda-level IAM policies not scoped to agent identities. The infrastructure repo has two IRSA roles with AdministratorAccess.
- **Compensating Controls**: Deploy API Gateway in front of each service with resource-level IAM policies restricting agent identities to GET methods only.
- **Portfolio-Level Recommendation**: Create a centralized agent IAM role strategy with least-privilege policies per service. Define agent permission templates (read-only catalog, read-only orders, etc.) as reusable IAM policy patterns.
- **Estimated Effort**: Medium

#### AUTH-Q3: Action-Level Authorization

- **Severity**: RISK-SAFETY in 5 of 5 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops
- **Common Finding**: No action-level authorization exists in any service. All endpoints within a role are accessible without read/write/delete distinctions. Two Kubernetes ClusterRoles in eks-saas-gitops grant full wildcard permissions.
- **Compensating Controls**: Use API Gateway method-level authorization (allow GET, deny POST/PUT/DELETE for agent roles).
- **Portfolio-Level Recommendation**: Implement action-level authorization at the API Gateway layer for all services. Define HTTP method restrictions per agent role. For EKS, replace wildcard ClusterRoles with scoped roles.
- **Estimated Effort**: Medium

#### AUTH-Q6: Immutable Audit Logging

- **Severity**: RISK-SAFETY in 5 of 5 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops
- **Common Finding**: No immutable audit trail exists across the portfolio. Logging approaches vary: System.out.println (unishop-monolith), console.log (aws-microservices, books-api), PHP error logging (local-monolith), and no audit logging at all (eks-saas-gitops). No CloudTrail configuration in any repository IaC. books-api has API Gateway logging (mutable CloudWatch), local-monolith has order_status_history in a mutable database.
- **Compensating Controls**: Enable CloudTrail at the AWS account level covering all services. Configure API Gateway access logging where applicable.
- **Portfolio-Level Recommendation**: Deploy a shared CloudTrail trail with S3 bucket (object lock enabled) covering all AWS accounts in the portfolio. Enable EKS control plane audit logging. Implement structured JSON logging across all services with a common schema.
- **Estimated Effort**: Medium

#### AUTH-Q7: Agent Identity Suspension

- **Severity**: RISK-SAFETY in 5 of 5 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops
- **Common Finding**: No agent identity suspension mechanism exists in any service. Since no machine identity authentication exists (AUTH-Q1 BLOCKER), there is no identity to suspend. The only recourse to stop a misbehaving agent is network-level blocking or shutting down the service entirely.
- **Compensating Controls**: When AUTH-Q1 is resolved, ensure the chosen mechanism supports individual credential revocation (API key deletion, Cognito app client disable, IAM policy attachment).
- **Portfolio-Level Recommendation**: As part of AUTH-Q1 remediation, implement a centralized agent identity registry with a kill switch capability — the ability to revoke all agent access across the portfolio within minutes.
- **Estimated Effort**: Medium

#### STATE-Q1: Compensation and Rollback

- **Severity**: RISK-SAFETY in 4 of 4 applicable services (N/A in eks-saas-gitops)
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api
- **Common Finding**: No saga pattern, Step Functions, or compensating transactions exist in any application service. unishop-monolith has @Transactional for single-operation atomicity only. aws-microservices has a 3-step checkout flow without compensation (EventBridge → SQS → DynamoDB). local-monolith has database transactions but no multi-step compensation. books-api has simple putItem with no rollback.
- **Compensating Controls**: Current read-only agent scope mitigates this risk — agents will not execute write operations requiring rollback.
- **Portfolio-Level Recommendation**: Before expanding to write-enabled agent scope on any service, implement compensation logic. Prioritize the aws-microservices checkout flow (highest risk of inconsistent state).
- **Estimated Effort**: High

#### STATE-Q5: Rate Limiting and Throttling

- **Severity**: RISK-SAFETY in 4 of 4 applicable services (N/A in eks-saas-gitops)
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api
- **Common Finding**: No explicit rate limiting exists in any application service. unishop-monolith runs directly on EC2 port 8080 with no traffic management. aws-microservices has no API Gateway throttling or usage plans. local-monolith has a WAF but no rate-based rules. books-api relies on default API Gateway account-level limits only.
- **Compensating Controls**: Deploy API Gateway with usage plans in front of all services as part of AUTH-Q1 remediation — this addresses both authentication and rate limiting simultaneously.
- **Portfolio-Level Recommendation**: Implement rate limiting at the API Gateway layer for all services with per-agent-identity throttle settings. Start with the WAF rate-based rule on local-monolith (quick win) and API Gateway usage plans on aws-microservices and books-api.
- **Estimated Effort**: Low

#### DATA-Q2: Data Residency and Sovereignty

- **Severity**: RISK-SAFETY in 4 of 4 applicable services (N/A in eks-saas-gitops)
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api
- **Common Finding**: No data residency documentation or controls exist in any application service. Database deployment regions are either environment variables (unishop-monolith), commented-out CDK env (aws-microservices), CloudFormation ${AWS::Region} (local-monolith), or SAM deploy region (books-api). Customer PII may be subject to GDPR/CCPA requirements with no documented compliance posture.
- **Compensating Controls**: Document data residency requirements for the portfolio. Configure agents to use Amazon Bedrock in the same region as data stores.
- **Portfolio-Level Recommendation**: Conduct a portfolio-wide data residency analysis. Document which regulatory frameworks apply to customer PII. Establish a policy requiring all agent LLM endpoints to be co-located with data sources.
- **Estimated Effort**: Medium

#### DATA-Q6: PII Redaction in Logs

- **Severity**: RISK-SAFETY in 4 of 4 applicable services (N/A in eks-saas-gitops)
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api
- **Common Finding**: No PII redaction exists in any application service's logging. unishop-monolith uses System.out.println and e.printStackTrace. aws-microservices logs full request payloads with PII/payment data via console.log. local-monolith includes $e->getMessage() with potential PII in error responses. books-api logs full DynamoDB items in the pre-traffic hook. PCI DSS compliance is at risk in aws-microservices where cardInfo is logged.
- **Compensating Controls**: Implement a structured logging library with PII redaction patterns across all services. Set CloudWatch Logs retention to short periods as an interim measure.
- **Portfolio-Level Recommendation**: Establish a portfolio-wide structured logging standard with mandatory PII redaction. Deploy CloudWatch Logs data protection policies across all accounts. Priority: aws-microservices (payment card data in logs — PCI DSS violation risk).
- **Estimated Effort**: Low

### Cross-Cutting RISK-QUALITY — Same Quality Risk in 3+ Repos

> These are RISK-QUALITY questions that appear in 3 or more repositories.
> They represent portfolio-wide quality patterns to address as capacity allows.
> Questions scored as N/A for a service do not count as gaps for that service.

#### API-Q2: Machine-Readable API Specification

- **Severity**: RISK-QUALITY in 4 of 4 applicable services (N/A in eks-saas-gitops)
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api
- **Common Finding**: No OpenAPI, Swagger, AsyncAPI, or other machine-readable API spec exists in any application service. API surfaces are defined only in source code (Spring annotations, CDK constructs, PHP route patterns, SAM events).
- **Portfolio-Level Recommendation**: Generate OpenAPI 3.0 specifications for all 4 application services. Prioritize services the agent will consume: aws-microservices (order lookups) and local-monolith (inventory queries).
- **Estimated Effort**: Low

#### API-Q3: Structured Error Responses

- **Severity**: RISK-QUALITY in 4 of 4 applicable services (N/A in eks-saas-gitops)
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api
- **Common Finding**: Error responses vary and lack structure: bare HTTP status codes with no body (unishop-monolith), HTTP 500 with stack traces in response body (aws-microservices), JSON error messages without error codes (local-monolith), and HTTP 500 with empty body (books-api). No service returns structured error codes or retryable indicators.
- **Portfolio-Level Recommendation**: Define a portfolio-wide error response standard: `{error_code, message, retryable}`. Implement across all services before agent integration.
- **Estimated Effort**: Low

#### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: RISK-QUALITY in 4 of 4 applicable services (N/A in eks-saas-gitops)
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api
- **Common Finding**: No identity propagation exists in any application service. No JWT parsing, no on-behalf-of flows, no token exchange patterns. Services cannot distinguish between agent-as-self and agent-on-behalf-of-user.
- **Portfolio-Level Recommendation**: Implement JWT-based identity propagation as part of AUTH-Q1 remediation. Define actor/subject claims in the token to distinguish agent identity from delegated user identity.
- **Estimated Effort**: Medium

#### AUTH-Q5: Credential Management

- **Severity**: RISK-QUALITY in 5 of 5 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops
- **Common Finding**: Credential management practices vary: hardcoded plaintext DB credentials in source control (unishop-monolith), no secrets management pattern (aws-microservices), hardcoded fallback credentials in code (local-monolith), no secrets management infrastructure (books-api), and SSM without rotation plus GIT_TOKEN exposed in workflow parameters (eks-saas-gitops). No service uses AWS Secrets Manager with rotation.
- **Portfolio-Level Recommendation**: Establish AWS Secrets Manager as the portfolio standard for all credentials. Migrate existing hardcoded/plaintext credentials immediately. Enable automatic rotation. Use External Secrets Operator for Kubernetes workloads.
- **Estimated Effort**: Medium

#### DATA-Q3: Selective Query Support

- **Severity**: RISK-QUALITY in 4 of 4 applicable services (N/A in eks-saas-gitops)
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api
- **Common Finding**: All application services return unbounded result sets. SELECT * FROM unicorns with no LIMIT (unishop-monolith), DynamoDB ScanCommand with no Limit parameter (aws-microservices, books-api), and SELECT * FROM inventory without pagination (local-monolith).
- **Portfolio-Level Recommendation**: Add pagination (limit/offset or cursor-based) and filtering parameters to all list endpoints across the portfolio. This is critical for agent integration — unbounded results exhaust LLM context windows.
- **Estimated Effort**: Low

#### DATA-Q4: System of Record Designations

- **Severity**: RISK-QUALITY in 4 of 4 applicable services (N/A in eks-saas-gitops)
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api
- **Common Finding**: No formal system-of-record designations exist in any application service. Each service is a de facto SoR for its entities, but this is undocumented. Product pricing may exist in multiple services with no authority defined.
- **Portfolio-Level Recommendation**: Create a portfolio-wide data ownership matrix. This is critical for the customer support agent — it needs to know which service is authoritative for order data, product catalogs, and inventory levels.
- **Estimated Effort**: Low

#### DATA-Q5: Temporal Metadata and Freshness

- **Severity**: RISK-QUALITY in 4 of 4 applicable services (N/A in eks-saas-gitops)
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api
- **Common Finding**: Temporal metadata is inconsistent. unishop-monolith has timestamps but hides them with @JsonIgnore. aws-microservices has orderDate on orders but no timestamps on products/baskets. local-monolith has created_at/updated_at without UTC normalization. books-api has no temporal fields at all. No service returns Cache-Control or Last-Modified headers.
- **Portfolio-Level Recommendation**: Establish a portfolio standard for temporal metadata: all entities include created_at and updated_at (ISO 8601 UTC). All GET responses include Cache-Control headers. Agents need freshness signals to reason about data currency.
- **Estimated Effort**: Low

#### DISC-Q1: Schema Versioning and API Contracts

- **Severity**: RISK-QUALITY in 4 of 4 applicable services (N/A in eks-saas-gitops)
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api
- **Common Finding**: No API versioning (no /v1/ URL patterns), no schema registries, no migration tools (except inline SQL), no breaking change detection, and no consumer-driven contract tests in any application service.
- **Portfolio-Level Recommendation**: Implement URL-based API versioning (/v1/) and OpenAPI spec diffing in CI for all services before agent integration. Agent tool bindings break silently on API changes.
- **Estimated Effort**: Medium

#### OBS-Q1: Distributed Tracing and Structured Logging

- **Severity**: RISK-QUALITY in 5 of 5 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops
- **Common Finding**: books-api is the only service with X-Ray tracing enabled. All other services have no tracing. Logging is unstructured across the portfolio: System.out.println (unishop-monolith), console.log (aws-microservices), PHP error logging (local-monolith), and no application logging infrastructure in eks-saas-gitops. No service has correlation IDs linking logs to traces.
- **Portfolio-Level Recommendation**: Deploy a portfolio-wide observability stack: X-Ray/OpenTelemetry for tracing, structured JSON logging with correlation IDs for all services, and centralized log aggregation. This is essential for debugging agent-initiated request chains across services.
- **Estimated Effort**: Medium

#### OBS-Q2: Alerting on Error Rates and Latency

- **Severity**: RISK-QUALITY in 5 of 5 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops
- **Common Finding**: No operational alerting exists in any service. books-api has deployment-scoped CloudWatch alarms (rollback triggers only). local-monolith has WAF metrics collected but no alarms. No service has latency, error rate, or anomaly detection alerting.
- **Portfolio-Level Recommendation**: Configure CloudWatch alarms for all services: HTTP 5xx rate, p99 latency, and database/Lambda errors. Set up centralized SNS notification topics. This enables detection of agent-caused degradation.
- **Estimated Effort**: Low

#### ENG-Q1: Infrastructure Governance

- **Severity**: RISK-QUALITY in 5 of 5 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops
- **Common Finding**: IaC exists in 4 of 5 services (absent in unishop-monolith). No service has all three governance sub-checks passing (IaC + peer review + drift detection). No branch protection or PR review requirements are enforced in any repository.
- **Portfolio-Level Recommendation**: Enforce branch protection with required reviews across all repositories. Enable CloudFormation drift detection. Deploy AWS Config rules for critical resources.
- **Estimated Effort**: Low

#### ENG-Q2: CI/CD with API Contract Testing

- **Severity**: RISK-QUALITY in 5 of 5 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops
- **Common Finding**: books-api is the only service with a full CI/CD pipeline (unit tests, e2e tests, staging deploy, manual approval). All other services have no CI/CD pipeline — deployment is manual (cdk deploy, docker-compose, shell scripts, terraform apply --auto-approve). No service has API contract testing.
- **Portfolio-Level Recommendation**: Establish CI/CD pipelines for all services with mandatory API contract testing before agent integration. Prioritize services the agent will consume directly.
- **Estimated Effort**: High

#### ENG-Q3: Rollback Capability

- **Severity**: RISK-QUALITY in 3 of 5 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, eks-saas-gitops
- **Common Finding**: No automated rollback capability in the 3 affected services. unishop-monolith deploys manually via JAR copy. aws-microservices deploys via manual cdk deploy. eks-saas-gitops has GitOps rollback for K8s but manual Terraform rollback.
- **Portfolio-Level Recommendation**: Implement automated deployment with rollback triggers for all services. books-api's Linear10PercentEvery1Minute with alarm-triggered rollback is the gold standard to replicate.
- **Estimated Effort**: Medium

#### ENG-Q4: API Test Coverage

- **Severity**: RISK-QUALITY in 5 of 5 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops
- **Common Finding**: unishop-monolith has zero test files. aws-microservices has fully commented-out tests. local-monolith has zero test files. eks-saas-gitops has only a basic Helm connectivity test. books-api has unit and e2e tests (best in portfolio) but no contract tests. No service has consumer-driven contract tests for agent consumers.
- **Portfolio-Level Recommendation**: Prioritize writing API tests for agent-facing endpoints across all services. Implement consumer-driven contract tests (Pact) for agent tool bindings before agent deployment.
- **Estimated Effort**: High

#### ENG-Q5: Encryption at Rest

- **Severity**: RISK-QUALITY in 3 of 5 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, eks-saas-gitops
- **Common Finding**: unishop-monolith has no encryption configuration (no IaC to verify). aws-microservices uses DynamoDB default AWS-owned key encryption (no CMK). eks-saas-gitops explicitly skips KMS encryption on DynamoDB and S3, and EKS secrets are not envelope-encrypted.
- **Portfolio-Level Recommendation**: Create a portfolio-wide KMS key strategy. Enable customer-managed KMS keys for all data stores containing PII. Enable EKS envelope encryption for Kubernetes secrets.
- **Estimated Effort**: Medium

#### HITL-Q3: Sandbox/Staging Environment

- **Severity**: RISK-QUALITY in 3 of 4 applicable services (N/A in eks-saas-gitops)
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith
- **Common Finding**: No separate staging/sandbox environment exists in the 3 affected services. unishop-monolith has a single application.properties with no profiles. aws-microservices has a single CDK stack with commented-out environment config. local-monolith has docker-compose for local dev but no staging CloudFormation.
- **Portfolio-Level Recommendation**: Create staging environments for all services before agent testing. books-api's staging pipeline is the model to follow.
- **Estimated Effort**: Medium

#### STATE-Q2: Queryable Current State

- **Severity**: RISK-QUALITY in 3 of 4 applicable services (N/A in eks-saas-gitops)
- **Affected Services**: unishop-monolith, aws-microservices, books-api
- **Common Finding**: Queryability gaps exist: unishop-monolith has no order/return endpoints (the agent's primary data need). aws-microservices has order queries that require both userName and orderDate. books-api has no single-item GET /books/{isbn} endpoint.
- **Portfolio-Level Recommendation**: Add missing query endpoints aligned with agent use cases: order history (unishop-monolith), flexible order queries (aws-microservices), and single-item lookup (books-api).
- **Estimated Effort**: Medium

#### STATE-Q7: Infrastructure Capacity for Agent Traffic

- **Severity**: RISK-QUALITY in 3 of 3 applicable services
- **Affected Services**: unishop-monolith, aws-microservices, local-monolith
- **Common Finding**: unishop-monolith runs on a single EC2 instance with no auto-scaling. aws-microservices has unbounded Lambda concurrency and no load testing. local-monolith has App Runner min=1/max=3 with db.t3.micro RDS.
- **Portfolio-Level Recommendation**: Conduct load testing simulating agent traffic patterns (burst reads, rapid sequential queries) for all P0 services before agent deployment. Upgrade database tiers and configure auto-scaling.
- **Estimated Effort**: Medium

## Service Dependency Map

> Dependencies were inferred from individual ARA report findings (not explicitly provided via `dependency_overrides`). Inferred dependencies may be incomplete — they reflect only what was observable in the assessed code and report context. For authoritative dependency data, add `dependency_overrides` to the portfolio config.

### Dependency Overview

| Source Service | Target Service | Type | Description | Inferred |
|---------------|---------------|------|-------------|----------|
| unishop-monolith | eks-saas-gitops | shared_infra | EKS platform target for non-serverless workloads; context states "everything that is not serverless will run here" and unishop-monolith is a decomposition target for containerized microservices | Yes |
| local-monolith | eks-saas-gitops | shared_infra | Containerized PHP monolith (Docker, App Runner) may migrate to EKS as part of modernization | Yes |

### Service Dependency Metrics

| Service | Fan-In | Fan-Out | Role | Readiness Profile |
|---------|--------|---------|------|-------------------|
| eks-saas-gitops | 2 | 0 | Foundation | Remediation Required |
| unishop-monolith | 0 | 1 | Leaf | Remediation Required |
| local-monolith | 0 | 1 | Leaf | Remediation Required |
| aws-microservices | 0 | 0 | Independent (serverless) | Remediation Required |
| books-api | 0 | 0 | Independent (serverless) | Remediation Required |

### High-Risk Dependency Patterns

1. **Foundation Service with Remediation Required**: eks-saas-gitops is the shared EKS infrastructure platform (fan-in = 2) and has a Remediation Required readiness profile with 1 BLOCKER (AUTH-Q1). Its AUTH-Q1 BLOCKER (no agent identity mechanism) could cascade to all non-serverless services deployed on the platform. If agent identity cannot be established at the platform level, services running on EKS cannot authenticate agents through the platform's identity mechanisms.
   - **Affected Services**: unishop-monolith, local-monolith (direct dependents); potentially all services that may leverage the EKS platform for shared authentication
   - **Risk**: Platform-level identity gap prevents coordinated agent authentication for EKS-hosted workloads
   - **Recommendation**: Prioritize AUTH-Q1 remediation on eks-saas-gitops — establish agent IRSA roles and namespace-scoped service accounts as the platform-level identity mechanism for agent authentication on EKS workloads

2. **No Transitive BLOCKER Propagation**: Since no Agent-Ready or Pilot-Ready services exist in the portfolio, there are no cases where a ready service depends (sync) on a blocked service. All 5 services are Remediation Required. The transitive dependency risk will become relevant as services are remediated — when the first service achieves Pilot-Ready status, verify its dependency chain does not include a blocked service.

---

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
**Services affected**: unishop-monolith, aws-microservices, local-monolith, books-api, eks-saas-gitops (5 of 5)

- **What to do**: Deploy a centralized Amazon Cognito User Pool with a Resource Server configured for `client_credentials` OAuth2 flow. Create dedicated Cognito App Clients per agent identity with custom scopes (e.g., `orders:read`, `inventory:read`, `catalog:read`). For the EKS platform, create dedicated IRSA roles with OIDC bindings scoped to agent-specific namespaces and service accounts. Each of the 5 services must integrate with the centralized identity provider:
  - **unishop-monolith**: Configure the existing (but disabled) OAuth2 Resource Server to validate Cognito tokens. Add API Gateway in front of EC2 with Cognito authorizer.
  - **aws-microservices**: Add IAM authorization or Cognito authorizer to all API Gateway LambdaRestApi constructs in CDK.
  - **local-monolith**: Add API key or Cognito token validation as a parallel auth path alongside session-based auth in PHP.
  - **books-api**: Extend the existing Cognito User Pool with a Resource Server and client_credentials flow. Add auth to GET /books (currently unauthenticated).
  - **eks-saas-gitops**: Create dedicated agent IRSA roles with namespace-scoped service account bindings. Change Argo Workflows from `--auth-mode=server` to SSO/client mode.
- **Expected outcome**: Every API call from the customer support agent requires authenticated machine identity. Agent actions are attributable in audit logs. Individual agent identities can be revoked without affecting other consumers.
- **Effort**: High (8–12 weeks across all 5 services)

#### Data Classification and Protection

**BLOCKERs addressed**: DATA-Q1
**Services affected**: unishop-monolith, aws-microservices, local-monolith, books-api (4 of 4 application services)

- **What to do**: Establish a portfolio-wide data classification policy defining 4 levels: Public, Internal, Confidential, Restricted. Conduct a data inventory across all 4 application services, classifying every field storing PII or payment data. Deploy Amazon Macie for automated PII discovery. Implement field-level response filtering per service:
  - **unishop-monolith**: Tag email, first_name, last_name as Confidential in unicorn_user table. Create agent-facing DTOs that exclude PII by default.
  - **aws-microservices**: Tag firstName, lastName, email, address as Confidential. Tag cardInfo, paymentMethod as Restricted. Implement DynamoDB projection expressions to exclude payment data from agent responses.
  - **local-monolith**: Tag customer_name, customer_email, shipping_address as Confidential. Add field-level filtering middleware for agent identities.
  - **books-api**: Formally classify book catalog data (isbn, title, author) as Public. Add classification tags to DynamoDB table.
- **Expected outcome**: All data stores have classification tags. The customer support agent can access order status and product information without receiving raw PII or payment card data. Sensitive fields are masked or excluded based on the agent's authorization scope.
- **Effort**: Medium (4–6 weeks across 4 services)

---

## Agentic Program Recommendations

> These are engagement-level recommendations based on the portfolio's agentic readiness
> profile. Discuss with your AWS Solutions Architect to determine eligibility and timing.

| Program | Relevance | Trigger Findings | Suggested Timing | Next Step |
|---------|-----------|-----------------|------------------|-----------|
| AI DLC | Teams lack AI-assisted development practices; engineering maturity is low across the portfolio | ENG-Q2 RISK-QUALITY in 5/5 services; ENG-Q4 RISK-QUALITY in 5/5 services; no CI/CD in 4/5 services | Run first — establish AI-driven development practices before agentic work | Request AI DLC workshop via AWS Solutions Architect |
| AgentStorming | All 5 services are Remediation Required with no clear agent integration path established | 100% of services Remediation Required; 0% have clear agent integration path; customer support agent use case defined but not mapped to service capabilities | Run after AI DLC — identify where agents should operate before remediating | Request AgentStorming workshop via AWS Solutions Architect |
| EBA on Agentic AI | AUTH-Q1 cross-cutting BLOCKER affects all 5 repositories — systemic identity gap requiring coordinated architecture remediation | AUTH-Q1 BLOCKER in 5/5 repos (exceeds 5-repo threshold); portfolio-wide identity gap cannot be resolved through standard advisory | Run after AgentStorming — accelerate coordinated remediation | Request Agentic EBA engagement via AWS Solutions Architect |

### Program Details

#### AI DLC (AI Driven Development Lifecycle)

- **Why triggered**: The portfolio demonstrates low engineering maturity across all 5 services: ENG-Q2 (CI/CD) is RISK-QUALITY in all 5 services with only books-api having a pipeline; ENG-Q4 (test coverage) is RISK-QUALITY in all 5 services with near-zero automated testing; ENG-Q3 (rollback) is RISK-QUALITY in 3 services. These findings indicate teams operating with manual development workflows that could significantly benefit from AI-driven automation.
- **What it provides**: Workshop for adopting the AI Driven Development Lifecycle, emphasizing (1) AI Powered Execution with Human Oversight — AI creates detailed work plans, seeks clarification, and defers critical decisions to humans, and (2) Dynamic Team Collaboration — as AI handles routine tasks, teams unite in collaborative spaces for real-time problem solving and rapid decision-making.
- **Suggested timing**: Run first, before other programs. Establishing AI-driven development practices accelerates all subsequent remediation work (CI/CD pipeline creation, test writing, security controls implementation).
- **Recommended scope**: Focus on the 3 P0 services (unishop-monolith, aws-microservices, local-monolith) where engineering maturity gaps are most critical.
- **Next step**: Request engagement via AWS Solutions Architect.

#### AgentStorming

- **Why triggered**: While the portfolio context clearly defines the agent use case (customer support agent for order inquiries, returns, and inventory restocking), 100% of services are Remediation Required with no established agent integration path. The gap between the defined use case and current system readiness requires a structured workshop to map specific agent workflows to service capabilities and prioritize remediation.
- **What it provides**: A workshop format building on EventStorming by adding Cognitive Complexity Analysis and Agentic Workflow Design. Gives the team a structured path from "where should we use AI?" to a qualified, implementation-ready answer. Maps the customer support agent's workflows (order lookup, return processing, inventory restocking) to specific service endpoints and identifies which remediation items are on the critical path.
- **Suggested timing**: Run after AI DLC but before beginning remediation. AgentStorming output will prioritize which services and which blockers to remediate first for the customer support agent use case.
- **Recommended scope**: Focus on the 3 agent workflows defined in the portfolio context: (1) order inquiries → aws-microservices + unishop-monolith, (2) return processing → local-monolith, (3) inventory restocking → local-monolith + books-api.
- **Next step**: Request engagement via AWS Solutions Architect.

#### EBA on Agentic AI (Experience-Based Acceleration)

- **Why triggered**: AUTH-Q1 (Machine Identity Authentication) is a cross-cutting BLOCKER affecting all 5 repositories in the portfolio. This single systemic gap exceeds the 5-repository threshold for EBA recommendation. The identity gap cannot be resolved through individual service-level remediation — it requires a coordinated, architecture-level intervention deploying a centralized identity provider and integrating all 5 services.
- **What it provides**: An intensive, time-boxed engagement embedding AWS expertise to compress multi-quarter remediation cycles into a focused sprint. Produces working outcomes: remediated identity infrastructure, validated agent integrations, and a sequenced deployment roadmap. Specifically for this portfolio: deploy the centralized Cognito identity plane, integrate all 5 services with M2M authentication, and establish the data classification framework.
- **Suggested timing**: Run after AgentStorming. The AgentStorming output prioritizes which services are on the critical path for the customer support agent, focusing the EBA sprint on the highest-impact remediation.
- **Recommended scope**: Identity foundation (AUTH-Q1 across all 5 services) and data classification (DATA-Q1 across 4 application services) as the primary EBA workstreams. Secondary: rate limiting and audit logging infrastructure.
- **Next step**: Request Agentic EBA engagement via AWS Solutions Architect.

---

## Portfolio-Level Findings

> These questions evaluate capabilities that can only be assessed by looking across
> multiple repos. They are distinct from cross-cutting analysis (which aggregates
> individual findings). Individual report findings are never overridden.

### PORT-ARA-Q1: Centralized Identity Plane

- **Severity**: BLOCKER
- **Finding**: No shared identity provider exists for agent M2M authentication across the portfolio. books-api has a Cognito User Pool (`CognitoUserPool` in template.yml) but it is configured exclusively for human users with email/password authentication (`ALLOW_USER_PASSWORD_AUTH`) — it does not support `client_credentials` flow for machine identities and is not referenced by any other service. eks-saas-gitops has multiple IRSA roles for infrastructure controllers but these are purpose-built for Kubernetes workloads and cannot serve as a shared agent identity plane. No common Cognito instance, API Gateway, or IAM identity mechanism is shared across any 2+ repositories.
- **Evidence**: books-api `template.yml` (CognitoUserPool — human-only, not shared); eks-saas-gitops `terraform/modules/gitops-saas-infra/main.tf` (IRSA roles — controller-only); no shared identity resource found across repositories
- **Recommendation**: Deploy a centralized Cognito User Pool with a Resource Server supporting `client_credentials` flow. Create a shared infrastructure module (Terraform or CDK) that all services reference for agent authentication. Consider deploying this as part of the eks-saas-gitops platform infrastructure.
- **Affected Services**: All 5 services
- **Contextual Annotations**:
  > **Portfolio Context**: PORT-ARA-Q1 found no shared identity provider across the portfolio. This confirms AUTH-Q1 as a systemic portfolio-level gap — each service independently lacks identity, and no centralized solution exists to address it. Resolving AUTH-Q1 for all 5 services should be done through a shared centralized identity plane rather than 5 independent implementations.

### PORT-ARA-Q2: Cross-Service Audit Correlation

- **Severity**: RISK
- **Finding**: No shared audit correlation mechanism exists. books-api is the only service with X-Ray tracing enabled (`Tracing: Active`, `TracingEnabled: true`, `AWSXRay.captureAWS`). The other 4 services have no tracing. No shared CloudTrail trail is defined in any repository's IaC. No consistent trace ID headers (X-Amzn-Trace-Id, traceparent) are propagated across services. No centralized log aggregation with cross-service correlation exists. An agent-initiated request that spans multiple services (e.g., query orders from aws-microservices then check inventory in local-monolith) cannot be traced end-to-end.
- **Evidence**: books-api `template.yml` (Tracing: Active — single service only); all other services (no tracing); no shared CloudTrail in any IaC
- **Recommendation**: Deploy a shared CloudTrail trail covering all services. Establish X-Ray or OpenTelemetry tracing as a portfolio standard. Require all services to propagate trace ID headers. Create a centralized CloudWatch Log Group or S3-based log lake for cross-service correlation.
- **Affected Services**: All 5 services (only books-api has partial tracing)
- **Contextual Annotations**: None — this finding provides new information not captured in individual reports.

### PORT-ARA-Q3: Portfolio-Level Rate Limiting

- **Severity**: RISK
- **Finding**: No shared API Gateway, WAF, or portfolio-level rate limiting exists. local-monolith has its own WAF (`AWS::WAFv2::WebACL` in CloudFormation) but it has no rate-based rules — only IP whitelist and input filtering. Each service manages rate limiting independently (and most have none). No shared usage plan or throttle configuration limits total agent traffic across the portfolio. A customer support agent making rapid queries across multiple services could overwhelm individual services without hitting any aggregate limit.
- **Evidence**: local-monolith `infrastructure/monolith-apprunner.yaml` (WAF with no rate-based rules); all other services (no WAF, no shared rate limiting infrastructure)
- **Recommendation**: Deploy a shared API Gateway with usage plans that enforce portfolio-level agent traffic quotas. Alternatively, deploy AWS WAF with rate-based rules at the account level covering all public-facing services. Define per-agent-identity rate limits that span the entire portfolio.
- **Affected Services**: All 5 services
- **Contextual Annotations**: None — this finding provides portfolio-level context for individual STATE-Q5 findings.

### PORT-ARA-Q4: Transitive Dependency Safety

- **Severity**: RISK
- **Finding**: All 5 services have the Remediation Required readiness profile. No Agent-Ready or Pilot-Ready services exist that could create a transitive dependency risk (where a ready service depends on a blocked service). However, eks-saas-gitops (Remediation Required, 1 BLOCKER) is the inferred shared infrastructure platform for non-serverless workloads. If unishop-monolith or local-monolith achieve Pilot-Ready status through remediation, their dependency on the EKS platform means their effective readiness is capped by eks-saas-gitops's readiness.
- **Evidence**: Inferred dependency graph (Step 5): unishop-monolith → eks-saas-gitops (shared_infra), local-monolith → eks-saas-gitops (shared_infra). All services: Remediation Required profile.
- **Recommendation**: When remediating services toward Pilot-Ready status, always verify the dependency chain. Remediate eks-saas-gitops's AUTH-Q1 BLOCKER before or in parallel with non-serverless service remediation to prevent transitive blocking.
- **Affected Services**: unishop-monolith, local-monolith (dependent on eks-saas-gitops)
- **Contextual Annotations**: None — no individual blockers to annotate since no transitive propagation currently exists.

### PORT-ARA-Q5: Agent Identity Governance

- **Severity**: RISK
- **Finding**: No centralized mechanism exists to suspend or revoke agent identities across all services simultaneously. No portfolio-wide agent identity registry, no centralized API key management, and no shared Cognito app client registry exists. Each service manages identities independently — and most have no identity at all (AUTH-Q1 BLOCKER). If a centralized identity provider is deployed (per PORT-ARA-Q1 recommendation), a kill switch capability must be built to revoke all agent access across the portfolio within minutes.
- **Evidence**: All 5 repositories (no shared identity management infrastructure); books-api (Cognito exists but human-only); eks-saas-gitops (IRSA roles with no suspension automation)
- **Recommendation**: As part of the centralized identity plane deployment (PORT-ARA-Q1), implement a portfolio-level agent identity governance mechanism: (1) a registry of all active agent identities, (2) a kill switch that disables all agent Cognito app clients or revokes all agent API keys within minutes, (3) alerting on anomalous agent behavior that triggers automatic suspension.
- **Affected Services**: All 5 services
- **Contextual Annotations**:
  > **Portfolio Context**: PORT-ARA-Q5 confirms that AUTH-Q7 (Agent Identity Suspension) cannot be resolved at the individual service level without a centralized governance mechanism. Individual suspension mechanisms are necessary but insufficient — portfolio-level governance is required.

---

## Service-by-Service Summary

| Service | Repo Type | Agent Scope | Readiness Profile | BLOCKERs | RISKs | INFOs | N/A |
|---------|-----------|-------------|-------------------|----------|-------|-------|-----|
| unishop-monolith | application | read-only | 🟠 Remediation Required | 2 | 27 | 10 | 0 |
| aws-microservices | application | read-only | 🟠 Remediation Required | 2 | 28 | 13 | 0 |
| local-monolith | application | read-only | 🟠 Remediation Required | 2 | 24 | 15 | 0 |
| books-api | application | read-only | 🟠 Remediation Required | 2 | 21 | 15 | 0 |
| eks-saas-gitops | infrastructure-only | read-only | 🟠 Remediation Required | 1 | 12 | 1 | 29 |

### Individual Service Details

#### unishop-monolith (MonoToMicroLegacy)

- **Readiness Profile**: Remediation Required
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P0
- **BLOCKERs** (2):
  - AUTH-Q1: OAuth2 Resource Server configured with permitAll() — effectively disables all authentication
  - DATA-Q1: PII (email, first_name, last_name) in unicorn_user table with no classification or field-level access controls
- **RISKs** (27):
  - RISK-SAFETY (9): AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q4, STATE-Q5, DATA-Q2, DATA-Q6
  - RISK-QUALITY (18): API-Q2, API-Q3, AUTH-Q4, AUTH-Q5, STATE-Q2, STATE-Q7, HITL-Q3, DATA-Q3, DATA-Q4, DATA-Q5, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4, ENG-Q5
- **Key Recommendations**:
  - Implement OAuth2 authentication using the existing Spring Security framework (AUTH-Q1)
  - Classify PII in unicorn_user table and create agent-facing DTOs (DATA-Q1)
  - Add springdoc-openapi for API specification generation (API-Q2)
- **Depends On**: eks-saas-gitops (shared_infra — EKS platform for containerized deployment)

#### aws-microservices

- **Readiness Profile**: Remediation Required
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P0
- **BLOCKERs** (2):
  - AUTH-Q1: API Gateway has no authorizers — all endpoints publicly accessible
  - DATA-Q1: Order DynamoDB table stores PII and payment data (cardInfo) without classification
- **RISKs** (28):
  - RISK-SAFETY (9): AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q4, STATE-Q5, DATA-Q2, DATA-Q6
  - RISK-QUALITY (19): API-Q2, API-Q3, API-Q6, AUTH-Q4, AUTH-Q5, STATE-Q2, STATE-Q7, HITL-Q3, DATA-Q3, DATA-Q4, DATA-Q5, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4, ENG-Q5
- **Key Recommendations**:
  - Add IAM authorization or Cognito authorizer to CDK API Gateway constructs (AUTH-Q1)
  - Add data classification tags to DynamoDB tables; implement field-level filtering to exclude cardInfo from responses (DATA-Q1)
  - Refactor checkout flow to use Step Functions with compensation (STATE-Q1)

#### local-monolith

- **Readiness Profile**: Remediation Required
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P0
- **BLOCKERs** (2):
  - AUTH-Q1: Session-based authentication only — no machine identity mechanism
  - DATA-Q1: Customer PII (names, emails, addresses) in MySQL tables without classification
- **RISKs** (24):
  - RISK-SAFETY (8): AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q5, DATA-Q2, DATA-Q6
  - RISK-QUALITY (16): API-Q2, API-Q3, AUTH-Q4, AUTH-Q5, STATE-Q7, HITL-Q3, DATA-Q3, DATA-Q4, DATA-Q5, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4
- **Key Recommendations**:
  - Add API key or Cognito token validation as parallel auth path alongside session auth (AUTH-Q1)
  - Classify PII fields and implement field-level filtering for agent responses (DATA-Q1)
  - Add WAF rate-based rule immediately (STATE-Q5 — quick win)
- **Depends On**: eks-saas-gitops (shared_infra — potential EKS migration target)

#### books-api

- **Readiness Profile**: Remediation Required
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P1
- **BLOCKERs** (2):
  - AUTH-Q1: Cognito configured for human users only; GET /books is completely unauthenticated
  - DATA-Q1: DynamoDB table has no data classification tags (book data is likely Public but unconfirmed)
- **RISKs** (21):
  - RISK-SAFETY (8): AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q5, DATA-Q2, DATA-Q6
  - RISK-QUALITY (13): API-Q2, API-Q3, AUTH-Q4, AUTH-Q5, STATE-Q2, DATA-Q3, DATA-Q4, DATA-Q5, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2
- **Key Recommendations**:
  - Extend existing Cognito with Resource Server and client_credentials flow for agent auth (AUTH-Q1)
  - Add data classification tags to DynamoDB table confirming Public classification (DATA-Q1)
  - Add GET /books/{isbn} endpoint for single-item queries (STATE-Q2)

#### eks-saas-gitops

- **Readiness Profile**: Remediation Required
- **Repo Type**: infrastructure-only
- **Agent Scope**: read-only
- **Priority**: P1
- **BLOCKERs** (1):
  - AUTH-Q1: No dedicated agent identity mechanism — existing IRSA roles serve infrastructure controllers only
- **RISKs** (12):
  - RISK-SAFETY (4): AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7
  - RISK-QUALITY (8): AUTH-Q5, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4, ENG-Q5
- **Key Recommendations**:
  - Create dedicated agent IRSA roles with namespace-scoped service account bindings (AUTH-Q1)
  - Replace AdministratorAccess on argo_workflows and tf_controller IRSA roles (AUTH-Q2)
  - Change Argo Workflows from --auth-mode=server to SSO/client mode (AUTH-Q7)
- **Depended On By**: unishop-monolith, local-monolith (shared infrastructure platform)

---

## Analysis Inventory

| # | Service | Report File | Analysis Date | Repo Type | Agent Scope |
|---|---------|-------------|-----------------|-----------|-------------|
| 1 | unishop-monolith | ./services/unishop-monolith-to-microservices/MonoToMicroLegacy/MonoToMicroLegacy-ara-report.md | 2026-04-27 | application | read-only |
| 2 | aws-microservices | ./services/aws-microservices/aws-microservices-ara-report.md | 2026-04-27 | application | read-only |
| 3 | local-monolith | ./monolith/monolith-ara-report.md | 2026-04-27 | application | read-only |
| 4 | books-api | ./services/books-api/books-api-ara-report.md | 2026-04-27 | application | read-only |
| 5 | eks-saas-gitops | ./services/eks-saas-gitops/eks-saas-gitops-ara-report.md | 2025-07-14 | infrastructure-only | read-only |

---

*End of Portfolio Agentic Readiness Analysis Report*
