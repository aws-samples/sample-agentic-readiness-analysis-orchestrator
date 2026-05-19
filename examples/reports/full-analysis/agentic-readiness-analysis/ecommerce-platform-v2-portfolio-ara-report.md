# Portfolio Agentic Readiness Assessment Report

**Date**: 2026-05-18
**Services Assessed**: 5
**Portfolio Context**: Evaluating the e-commerce platform portfolio for both autonomous AI agent integration and cloud-native modernization. The team is building a customer support agent that handles order inquiries, processes returns, and manages inventory restocking — while simultaneously modernizing legacy monoliths into containerized microservices on EKS.

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
| Total Services Assessed | 5 |
| Services Ready for Agents (Agent-Ready + Pilot-Ready) | 0 (0%) |
| Services Requiring Remediation | 4 (80%) |
| Cross-Cutting BLOCKERs (same blocker in 2+ repos) | 1 |
| Cross-Cutting RISKs (same risk at-or-above scaling threshold) | 22 |
| Services with Write-Enabled Agent Scope | 0 (0%) |
| Services with Read-Only Agent Scope | 5 (100%) |

### Repo Type Distribution

| Repo Type | Count | Percentage |
|-----------|-------|------------|
| application | 4 | 80% |
| infrastructure-only | 1 | 20% |

### Blocker Heatmap by Section

| Section | Repos Blocked | % of Applicable Repos | Top Blockers |
|---------|--------------|----------------------|--------------|
| Authentication & Authorization | 4 | 80% | AUTH-Q1 |
| API Surface | 0 | 0% | — |
| State Management | 0 | 0% | — |
| Human-in-the-Loop | 0 | 0% | — |
| Data Accessibility | 0 | 0% | — |
| Discovery & Documentation | 0 | 0% | — |
| Observability | 0 | 0% | — |
| Engineering Maturity | 0 | 0% | — |

### Readiness Snapshot

| Metric | Value |
|--------|-------|
| assessment_date | 2026-05-18 |
| total_services | 5 |
| agent_ready | 0 |
| pilot_ready | 0 |
| pilot_ready_safety_concerns | 1 |
| remediation_required | 4 |
| not_integrable | 0 |
| total_blockers | 4 |
| total_risks | 94 |
| total_risk_safety | 37 |
| total_risk_quality | 57 |
| total_infos | 50 |
| cross_cutting_blockers | 1 |
| cross_cutting_risks | 22 |
| cross_cutting_risk_safety | 9 |
| cross_cutting_risk_quality | 13 |
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
- **Cross-cutting basis**: BLOCKER in 2+ repos
- **Affected Services**: local-monolith, unishop-monolith, books-api, aws-microservices
- **Common Finding**: No machine identity authentication exists across affected services. All lack OAuth2 client credentials, API keys with principal attribution, or mTLS for M2M authentication.
- **Root Cause Pattern**: Services were designed for human browser-based access only. No M2M authentication pattern was implemented during original development.
- **Portfolio-Level Remediation**:
  - **Approach**: Hybrid — deploy shared identity infrastructure (Cognito/IAM) with per-service integration
  - **Immediate Action**: Deploy a shared Cognito User Pool with resource server and client_credentials grant, or implement API Gateway with IAM authorization
  - **Target State**: Every agent API call authenticated with machine-identifiable credential logged with principal attribution
  - **Estimated Effort**: Medium
  - **Priority**: Critical
  - **Dependencies**: None

## Cross-Cutting RISKs

### Cross-Cutting RISK-SAFETY — Recurring Safety Risks Across Portfolio

> These are RISK-SAFETY questions that appear in at least **max(3, 33% of applicable repos)**.
> They represent portfolio-wide agent safety gaps requiring coordinated attention.
> Questions scored as N/A for a service do not count as gaps for that service.

#### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: RISK-SAFETY in 4 of 4 applicable services
- **Affected Services**: local-monolith, unishop-monolith, books-api, aws-microservices
- **Common Finding**: No identity propagation mechanism exists. No JWT parsing, no OAuth2 on-behalf-of flows, no token exchange patterns. All requests authenticated via PHP sessions with no distinction between agent-as-sel
- **Portfolio-Level Recommendation**: Implement JWT-based auth with token exchange support for delegated identity.
- **Estimated Effort**: High

#### AUTH-Q5: Credential Management

- **Severity**: RISK-SAFETY in 3 of 5 applicable services
- **Affected Services**: local-monolith, unishop-monolith, eks-saas-gitops
- **Common Finding**: Database credentials are passed directly as environment variables with hardcoded fallbacks. No AWS Secrets Manager, no HashiCorp Vault, no credential rotation mechanism.
- **Portfolio-Level Recommendation**: Migrate database credentials to AWS Secrets Manager with automatic rotation. Use RDS IAM authentication (already enabled on the RDS instance).
- **Estimated Effort**: Low

#### AUTH-Q6: Immutable Audit Logging

- **Severity**: RISK-SAFETY in 4 of 5 applicable services
- **Affected Services**: local-monolith, unishop-monolith, eks-saas-gitops, books-api
- **Common Finding**: No immutable audit logging exists. order_status_history table records changes but is mutable database storage. No CloudTrail configuration in IaC. VPC Flow Logs capture network traffic only.
- **Portfolio-Level Recommendation**: Add CloudTrail configuration. Implement structured application-level audit logging to CloudWatch Logs with immutable storage.
- **Estimated Effort**: Medium

#### AUTH-Q7: Agent Identity Suspension

- **Severity**: RISK-SAFETY in 5 of 5 applicable services
- **Affected Services**: local-monolith, unishop-monolith, eks-saas-gitops, books-api, aws-microservices
- **Common Finding**: No mechanism exists to suspend or revoke individual agent identities without affecting other users. Session-based auth only — no API keys to revoke, no service accounts to disable.
- **Portfolio-Level Recommendation**: Implement API key-based auth with per-key revocation. Add admin endpoint to disable individual service accounts.
- **Estimated Effort**: Medium

#### DATA-Q1: Sensitive Data Classification

- **Severity**: RISK-SAFETY in 3 of 4 applicable services
- **Affected Services**: local-monolith, unishop-monolith, aws-microservices
- **Common Finding**: System stores customer PII (names, emails, addresses, payment records). Order endpoints return customer PII (email, name, shipping_address) without scoping. Password IS properly excluded.
- **Portfolio-Level Recommendation**: Create agent-specific endpoints or response DTOs that exclude customer PII. For restocking, agent only needs product_id, stock_quantity, warehouse_location.
- **Estimated Effort**: Low

#### DATA-Q2: Data Residency and Sovereignty

- **Severity**: RISK-SAFETY in 3 of 4 applicable services
- **Affected Services**: local-monolith, unishop-monolith, aws-microservices
- **Common Finding**: System stores customer PII and payment data with no data residency documentation or policy. No controls preventing cross-region data transmission to LLM providers.
- **Portfolio-Level Recommendation**: Document data residency requirements. Configure agent to use region-local Bedrock endpoints. Add data classification tags.
- **Estimated Effort**: Medium

#### DATA-Q6: PII Redaction in Logs

- **Severity**: RISK-SAFETY in 3 of 4 applicable services
- **Affected Services**: local-monolith, unishop-monolith, aws-microservices
- **Common Finding**: No PII redaction in logs. PHP error logging enabled without scrubbing. Customer data in exceptions could be logged without redaction.
- **Portfolio-Level Recommendation**: Implement structured logging with PII field exclusion. Add CloudWatch Logs data protection policies.
- **Estimated Effort**: Medium

#### STATE-Q1: Compensation and Rollback

- **Severity**: RISK-SAFETY in 3 of 4 applicable services
- **Affected Services**: local-monolith, unishop-monolith, books-api
- **Common Finding**: Database transactions with rollback exist for individual operations (order creation, return approval). However, the 7-step fulfillment workflow has no saga pattern or compensating actions if a downstr
- **Portfolio-Level Recommendation**: Implement saga pattern for fulfillment workflow with explicit compensating actions for each step.
- **Estimated Effort**: High

#### STATE-Q5: Rate Limiting and Throttling

- **Severity**: RISK-SAFETY in 4 of 4 applicable services
- **Affected Services**: local-monolith, unishop-monolith, books-api, aws-microservices
- **Common Finding**: No rate limiting at application level. WAF provides IP whitelisting only (no rate-based rules). App Runner MaxConcurrency (100) is a resource limit, not rate limiting.
- **Portfolio-Level Recommendation**: Add WAF rate-based rules. Implement application-level rate limiting middleware or add API Gateway with usage plans.
- **Estimated Effort**: Low

### Cross-Cutting RISK-QUALITY — Recurring Quality Risks Across Portfolio

> These are RISK-QUALITY questions that appear in at least **max(3, 33% of applicable repos)**.
> They represent portfolio-wide quality patterns to address as capacity allows.
> Questions scored as N/A for a service do not count as gaps for that service.

#### API-Q2: Machine-Readable API Specification

- **Severity**: RISK-QUALITY in 4 of 4 applicable services
- **Affected Services**: local-monolith, unishop-monolith, books-api, aws-microservices
- **Common Finding**: No OpenAPI, AsyncAPI, GraphQL schema, or machine-readable spec exists. 26+ REST endpoints defined only in PHP source code.
- **Portfolio-Level Recommendation**: Generate OpenAPI 3.0 specification documenting all endpoints, request/response schemas, and error codes.
- **Estimated Effort**: Medium

#### API-Q3: Structured Error Responses

- **Severity**: RISK-QUALITY in 4 of 4 applicable services
- **Affected Services**: local-monolith, unishop-monolith, books-api, aws-microservices
- **Common Finding**: Error format is {"error": "message"} with HTTP status codes. No error codes, no retryable field, no field-level validation detail.
- **Portfolio-Level Recommendation**: Implement structured error codes with retryable indicators and field-level detail.
- **Estimated Effort**: Low

#### DATA-Q3: Selective Query Support

- **Severity**: RISK-QUALITY in 4 of 4 applicable services
- **Affected Services**: local-monolith, unishop-monolith, books-api, aws-microservices
- **Common Finding**: All query endpoints return complete result sets. No LIMIT, OFFSET, cursor, or filter parameters on list endpoints.
- **Portfolio-Level Recommendation**: Add pagination parameters (?limit=50&offset=0) and filter support to list endpoints.
- **Estimated Effort**: Low

#### DATA-Q4: Input Validation and Schema Enforcement

- **Severity**: RISK-QUALITY in 4 of 4 applicable services
- **Affected Services**: local-monolith, unishop-monolith, books-api, aws-microservices
- **Common Finding**: Some required field checks and stock validation exist, but no systematic validation framework. No input length limits, no format validation, no type checking. Validation errors are unstructured.
- **Portfolio-Level Recommendation**: Add validation layer with structured error responses including field name and constraint violated.
- **Estimated Effort**: Medium

#### DATA-Q5: Temporal Metadata and Freshness

- **Severity**: RISK-QUALITY in 4 of 4 applicable services
- **Affected Services**: local-monolith, unishop-monolith, books-api, aws-microservices
- **Common Finding**: Database tables have created_at/updated_at fields. No Cache-Control headers, no freshness/staleness signaling in API responses.
- **Portfolio-Level Recommendation**: Add Last-Modified or X-Data-Freshness headers. Store timestamps in explicit UTC.
- **Estimated Effort**: Low

#### DISC-Q1: Schema Versioning and API Contracts

- **Severity**: RISK-QUALITY in 4 of 4 applicable services
- **Affected Services**: local-monolith, unishop-monolith, books-api, aws-microservices
- **Common Finding**: No API versioning, no schema files, no database migrations, no changelog, no breaking change detection, no contract tests.
- **Portfolio-Level Recommendation**: Add API version prefix (/v1/). Generate and commit OpenAPI spec. Add schema diff in CI.
- **Estimated Effort**: Medium

#### ENG-Q1: Infrastructure Governance

- **Severity**: RISK-QUALITY in 4 of 5 applicable services
- **Affected Services**: local-monolith, unishop-monolith, eks-saas-gitops, aws-microservices
- **Common Finding**: CloudFormation IaC exists but no CI/CD enforces review before deployment. No drift detection. Manual deployment via deploy.sh.
- **Portfolio-Level Recommendation**: Add CI/CD pipeline with required PR approval. Enable CloudFormation drift detection.
- **Estimated Effort**: Medium

#### ENG-Q2: CI/CD with API Contract Testing

- **Severity**: RISK-QUALITY in 5 of 5 applicable services
- **Affected Services**: local-monolith, unishop-monolith, eks-saas-gitops, books-api, aws-microservices
- **Common Finding**: No CI/CD pipeline. No GitHub Actions, GitLab CI, Jenkinsfile, or buildspec.yml. Deployment is manual via deploy.sh.
- **Portfolio-Level Recommendation**: Create CI/CD pipeline with API contract testing and schema validation.
- **Estimated Effort**: Medium

#### ENG-Q3: Rollback Capability

- **Severity**: RISK-QUALITY in 3 of 5 applicable services
- **Affected Services**: local-monolith, unishop-monolith, aws-microservices
- **Common Finding**: No automated rollback capability. ECR immutable tags allow manual previous-image deployment. No automatic rollback triggers.
- **Portfolio-Level Recommendation**: Configure App Runner auto-rollback on health check failure or add CodeDeploy with rollback triggers.
- **Estimated Effort**: Medium

#### ENG-Q4: API Test Coverage

- **Severity**: RISK-QUALITY in 5 of 5 applicable services
- **Affected Services**: local-monolith, unishop-monolith, eks-saas-gitops, books-api, aws-microservices
- **Common Finding**: No test files exist. No PHPUnit, no API test suites, no integration tests, no contract tests. Zero test infrastructure.
- **Portfolio-Level Recommendation**: Add PHPUnit integration tests for agent-facing endpoints (GET /api/products, GET /api/orders/{id}/validation-data).
- **Estimated Effort**: High

#### OBS-Q1: Distributed Tracing and Structured Logging

- **Severity**: RISK-QUALITY in 5 of 5 applicable services
- **Affected Services**: local-monolith, unishop-monolith, eks-saas-gitops, books-api, aws-microservices
- **Common Finding**: No OpenTelemetry, no X-Ray, no structured logging. Only PHP error_log() producing unstructured text. No correlation IDs or request IDs.
- **Portfolio-Level Recommendation**: Add AWS X-Ray SDK and structured JSON logging with request_id per request.
- **Estimated Effort**: Medium

#### OBS-Q2: Alerting on Error Rates and Latency

- **Severity**: RISK-QUALITY in 5 of 5 applicable services
- **Affected Services**: local-monolith, unishop-monolith, eks-saas-gitops, books-api, aws-microservices
- **Common Finding**: No CloudWatch Alarms in CloudFormation. WAF metrics enabled but no alarms trigger. No PagerDuty/OpsGenie integration.
- **Portfolio-Level Recommendation**: Add CloudWatch Alarms for HTTP 5xx rate, P99 latency, WAF blocked request spikes.
- **Estimated Effort**: Low

#### STATE-Q7: Graceful Degradation Signaling

- **Severity**: RISK-QUALITY in 3 of 4 applicable services
- **Affected Services**: local-monolith, unishop-monolith, aws-microservices
- **Common Finding**: No degraded mode signaling. No health headers, no X-Degraded, no Cache-Control, no Retry-After. Health checks detect only complete failure.
- **Portfolio-Level Recommendation**: Add response headers for data freshness and implement granular health endpoint.
- **Estimated Effort**: Medium

## Service Dependency Map

> Dependencies were inferred from individual ARA report findings and portfolio context (not explicitly provided via `dependency_overrides`).
> Inferred dependencies may be incomplete. For authoritative dependency data, add `dependency_overrides` to the portfolio config.

### Dependency Overview

| Source Service | Target Service | Type | Description |
|---------------|---------------|------|-------------|
| aws-microservices | eks-saas-gitops | shared_infra | Microservices planned to run on EKS platform |
| unishop-monolith | eks-saas-gitops | shared_infra | Decomposed services target EKS deployment |

### Service Dependency Metrics

| Service | Fan-In | Fan-Out | Role | Readiness Profile |
|---------|--------|---------|------|-------------------|
| local-monolith | 0 | 0 | Internal | Remediation Required |
| unishop-monolith | 0 | 1 | Leaf | Remediation Required |
| eks-saas-gitops | 2 | 0 | Foundation | Pilot-Ready (Safety Concerns) |
| books-api | 0 | 0 | Internal | Remediation Required |
| aws-microservices | 0 | 1 | Leaf | Remediation Required |

### High-Risk Dependency Patterns

1. **Foundation Service with Safety Concerns**: eks-saas-gitops is the EKS infrastructure platform (fan-in=2) with profile "Pilot-Ready (Safety Concerns)". Services deployed on this platform inherit its safety gaps (missing audit logging, no immediate identity suspension).
   - **Affected Services**: aws-microservices, unishop-monolith (planned EKS deployment)
   - **Risk**: Agent workloads deployed on EKS will lack immutable audit logging and immediate identity suspension until eks-saas-gitops resolves AUTH-Q6 and AUTH-Q7
   - **Recommendation**: Prioritize eks-saas-gitops RISK-SAFETY remediation before deploying agent-enabled workloads on the cluster

## Portfolio Remediation Guidance

> Portfolio context: Evaluating the e-commerce platform portfolio for autonomous AI agent integration and cloud-native modernization.

### Remediation Priority Order

Remediation of cross-cutting BLOCKERs should follow this general priority:

1. **Identity and Access** — Resolve AUTH-section BLOCKERs first. You cannot enforce any other security control without machine identity and scoped permissions.
2. **Data Integrity** — Resolve STATE and DATA-section BLOCKERs second. Protect data before enabling agent write operations.
3. **API Surface** — Resolve API-section BLOCKERs third. Ensure a stable, documented integration surface for agent tools.
4. **Remaining BLOCKERs** — Address in order of affected service count (most affected first).

### Coordinated Remediation Plan

#### Identity Foundation

**BLOCKERs addressed**: AUTH-Q1
**Services affected**: local-monolith, unishop-monolith, books-api, aws-microservices

- **What to do**: Deploy a shared Cognito User Pool with resource server and custom scopes (e.g., `orders/read`, `inventory/read`, `books/read`). Add client_credentials grant type for agent app clients. Configure API Gateway authorizers (or in-app auth middleware) in each service to validate tokens from the shared pool.
- **Expected outcome**: All four services authenticate agent callers with machine-readable principal identity. Enables per-agent suspension, audit attribution, and scoped access control.
- **Effort**: Medium

## Recommended Actions

### Agentic Program Recommendations

> These are engagement-level recommendations based on the portfolio's agentic readiness
> profile. Discuss with your AWS Solutions Architect to determine eligibility and timing.

| Program | Relevance | Trigger Findings | Suggested Timing | Next Step |
|---------|-----------|-----------------|------------------|-----------|
| AI DLC | Engineering maturity gaps across portfolio | 80% ENG-Q1, 100% ENG-Q2 RISK-QUALITY | Run first | Request workshop via AWS SA |
| AXE | Experience-level goals defined without technical roadmap | Portfolio context describes customer support agent goals | After AI DLC | Request engagement via AWS SA |

### Program Details

#### AI Driven Development Lifecycle (AI DLC)

- **Why triggered**: 80% of services have RISK-QUALITY findings on ENG-Q1 (Infrastructure Governance), 100% on ENG-Q2 (CI/CD with API Contract Testing), indicating manual development workflows that would benefit from AI-driven automation practices.
- **What it provides**: Workshop for adopting AI-driven development lifecycle emphasizing AI Powered Execution with Human Oversight and Dynamic Team Collaboration.
- **Suggested timing**: Run first to establish AI-driven development practices before agentic integration work
- **Recommended scope**: Focus on CI/CD automation, infrastructure governance, and contract testing across all 5 services
- **Next step**: Request workshop via AWS Solutions Architect

#### Agent Experience Engagement (AXE)

- **Why triggered**: Portfolio context describes experience-level goals (customer support agent for order inquiries, returns processing, inventory restocking) without a corresponding technical implementation roadmap.
- **What it provides**: Strategic methodology helping enterprises implement agentic AI solutions by starting with desired customer/employee experience and working backwards to define AI agents and technical architecture.
- **Suggested timing**: After AI DLC workshop to design the agent experience and implementation roadmap
- **Recommended scope**: Customer support agent use case spanning order inquiries (aws-microservices), returns processing (local-monolith, unishop-monolith), and inventory restocking (local-monolith)
- **Next step**: Request engagement via AWS Solutions Architect

## Portfolio-Level Findings

> These questions evaluate capabilities that can only be assessed by looking across
> multiple repos. They are distinct from cross-cutting analysis (which aggregates
> individual findings). Individual report findings are never overridden.

### PORT-ARA-Q1: Centralized Identity Plane

- **Severity**: BLOCKER
- **Finding**: No shared identity provider detected across the portfolio. books-api uses Cognito for human users but no client_credentials flow for M2M. eks-saas-gitops uses IRSA for in-cluster workloads but this is not shared by other services. No common IdP or shared auth mechanism spans multiple repositories.
- **Evidence**: books-api: template.yml (Cognito UserPool for human auth only); eks-saas-gitops: terraform/modules/gitops-saas-infra/main.tf (IRSA roles); other services: no auth configured
- **Recommendation**: Deploy a shared Cognito User Pool with a resource server and custom scopes (or a shared API Gateway with IAM authorization) that all services reference for agent M2M authentication.
- **Affected Services**: local-monolith, unishop-monolith, eks-saas-gitops, books-api, aws-microservices

> **Portfolio Context**: PORT-ARA-Q1 found no shared identity provider across the portfolio.
> This reinforces the AUTH-Q1 cross-cutting BLOCKER — resolving AUTH-Q1 should include
> deploying a *shared* identity plane rather than per-service implementations.

### PORT-ARA-Q2: Cross-Service Audit Correlation

- **Severity**: RISK
- **Finding**: No shared trace ID propagation or centralized audit trail detected across the portfolio. books-api has X-Ray tracing enabled. No other service has distributed tracing. No shared CloudTrail trail configuration. No consistent correlation ID headers across services.
- **Evidence**: books-api: template.yml (X-Ray tracing on Lambda/API Gateway); all others: no tracing configured
- **Recommendation**: Deploy a shared CloudTrail trail covering all accounts/services. Standardize on X-Amzn-Trace-Id header propagation. Deploy OpenTelemetry Collector on EKS for services migrating there.
- **Affected Services**: local-monolith, unishop-monolith, eks-saas-gitops, books-api, aws-microservices

### PORT-ARA-Q3: Portfolio-Level Rate Limiting

- **Severity**: INFO
- **Finding**: No shared WAF or API gateway protecting the portfolio perimeter. local-monolith has its own WAF configuration. Individual services have varying levels of rate limiting (books-api relies on API Gateway defaults, aws-microservices has no explicit rate limiting). Rate limiting exists only at individual service level.
- **Evidence**: local-monolith: infrastructure/monolith-apprunner.yaml (WAF WebACL); books-api: API Gateway default throttling; others: no rate limiting
- **Recommendation**: For agent-at-scale scenarios, implement a shared WAF WebACL or API Gateway with usage plans that protects all agent-facing endpoints with consistent rate limits.
- **Affected Services**: local-monolith, unishop-monolith, eks-saas-gitops, books-api, aws-microservices

### PORT-ARA-Q4: Transitive Dependency Safety

- **Severity**: RISK
- **Finding**: No explicit dependency overrides provided. Based on portfolio context, services running on the EKS platform (eks-saas-gitops) depend on its infrastructure readiness. Since eks-saas-gitops is Pilot-Ready (Safety Concerns) and not Agent-Ready, services deployed on it inherit its safety constraints. However, no service in the portfolio is currently Agent-Ready or Pilot-Ready without safety concerns, so transitive blocking is not immediately actionable.
- **Evidence**: eks-saas-gitops: Pilot-Ready (Safety Concerns); all application services: Remediation Required
- **Recommendation**: Add dependency_overrides to portfolio config to enable precise transitive analysis. Prioritize resolving eks-saas-gitops safety concerns before deploying agent-enabled workloads on the cluster.
- **Affected Services**: local-monolith, unishop-monolith, eks-saas-gitops, books-api, aws-microservices

### PORT-ARA-Q5: Agent Identity Governance

- **Severity**: RISK
- **Finding**: No centralized mechanism to suspend or revoke agent identities across all services simultaneously. Each service manages identity independently (or has no identity management at all). No shared Cognito app client registry, no centralized API key management, no portfolio-level agent identity kill switch.
- **Evidence**: books-api: Cognito (human auth only, no M2M); eks-saas-gitops: IRSA (cluster-scoped only); others: no auth mechanism
- **Recommendation**: Implement a centralized agent identity registry (Cognito app clients with resource servers, or a shared API key management system) with an emergency revocation mechanism (e.g., Lambda function that disables all agent app clients or rotates all API keys).
- **Affected Services**: local-monolith, unishop-monolith, eks-saas-gitops, books-api, aws-microservices

## Service-by-Service Summary

| Service | Repo Type | Agent Scope | Readiness Profile | BLOCKERs | RISKs | INFOs |
|---------|-----------|-------------|-------------------|----------|-------|-------|
| local-monolith | application | read-only | Remediation Required | 1 | 22 | 12 |
| unishop-monolith | application | read-only | Remediation Required | 1 | 26 | 11 |
| aws-microservices | application | read-only | Remediation Required | 1 | 22 | 12 |
| books-api | application | read-only | Remediation Required | 1 | 16 | 14 |
| eks-saas-gitops | infrastructure-only | read-only | Pilot-Ready (Safety Concerns) | 0 | 8 | 1 |

### Individual Service Details

#### local-monolith

- **Readiness Profile**: Remediation Required
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P0
- **BLOCKERs** (1):
  - AUTH-Q1: No Machine Identity Authentication
- **RISKs** (22):
  - AUTH-Q4: No Identity Propagation or Delegation
  - AUTH-Q5: No Secrets Management System
  - AUTH-Q6: No Immutable Audit Logging
  - AUTH-Q7: No Agent Identity Suspension Mechanism
  - STATE-Q1: No Workflow-Level Compensation
  - ... and 17 more
- **Key Recommendations**:
  - Implement API key authentication with principal attribution alongside existing session auth. Add Aut
  - Implement JWT-based auth with token exchange support for delegated identity.
  - Add CloudTrail configuration. Implement structured application-level audit logging to CloudWatch Log

#### unishop-monolith

- **Readiness Profile**: Remediation Required
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P0
- **BLOCKERs** (1):
  - AUTH-Q1: No Machine Identity Authentication
- **RISKs** (26):
  - AUTH-Q2: No Scoped Permissions
  - AUTH-Q3: No Action-Level Authorization
  - AUTH-Q4: No Identity Propagation
  - AUTH-Q5: Hardcoded Database Credentials
  - AUTH-Q6: No Audit Logging
  - ... and 21 more
- **Key Recommendations**:
  - Implement API Gateway with IAM/Cognito authorizers or OAuth2 client credentials flow with principal 
  - Implement RBAC with read-only and read-write roles enforced at Spring Security or API Gateway level.
  - Implement method-level security annotations or API Gateway method-level auth.
- **Depends On**: eks-saas-gitops (shared_infra)

#### aws-microservices

- **Readiness Profile**: Remediation Required
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P0
- **BLOCKERs** (1):
  - AUTH-Q1: No Machine Identity Authentication
- **RISKs** (23):
  - AUTH-Q2: No Scoped Permissions for Agent Identity
  - AUTH-Q3: No Action-Level Authorization
  - AUTH-Q4: No Identity Propagation or Delegation
  - AUTH-Q7: No Agent Identity Suspension Capability
  - STATE-Q4: No Circuit Breakers or Resilience Patterns
  - ... and 18 more
- **Key Recommendations**:
  - Implement API Gateway authorization (IAM SigV4, Cognito, or API keys with usage plans) on all method
  - Implement per-method IAM authorization that differentiates read vs write access.
  - Implement IAM authorization with per-method policy conditions on execute-api:method.
- **Depends On**: eks-saas-gitops (shared_infra)

#### books-api

- **Readiness Profile**: Remediation Required
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P1
- **BLOCKERs** (1):
  - AUTH-Q1: No Machine Identity Authentication
- **RISKs** (16):
  - AUTH-Q4: No Identity Propagation or Delegation Mechanism
  - AUTH-Q6: No Immutable Audit Logging
  - AUTH-Q7: Cannot Suspend Agent Identity on Unauthenticated Endpoint
  - STATE-Q1: No Compensation or Rollback for Write Operations
  - STATE-Q5: No Explicit Rate Limiting Configuration
  - ... and 11 more
- **Key Recommendations**:
  - Add a Cognito App Client with client_credentials grant type and configure a resource server with cus
  - Design token model with acting_as claim to distinguish self-service vs delegated calls when implemen
  - Add AWS::CloudTrail::Trail with EnableLogFileValidation and S3 bucket with object lock for log stora

#### eks-saas-gitops

- **Readiness Profile**: Pilot-Ready (Safety Concerns)
- **Repo Type**: infrastructure-only
- **Agent Scope**: read-only
- **Priority**: P1
- **BLOCKERs** (0):
- **RISKs** (8):
  - AUTH-Q5: Credential Management — No Rotation Configured
  - AUTH-Q6: Immutable Audit Logging — Not Configured
  - AUTH-Q7: Agent Identity Suspension — No Immediate Mechanism
  - OBS-Q1: Distributed Tracing and Structured Logging — Not Configured
  - OBS-Q2: Alerting on Error Rates and Latency — Not Configured
  - ... and 3 more
- **Key Recommendations**:
  - Add aws_cloudtrail resource with S3 bucket (Object Lock enabled), CloudTrail log file validation, an
  - Implement automation (Lambda + EventBridge) that can immediately attach a deny-all inline policy to 
- **Depended On By**: aws-microservices, unishop-monolith

## Assessment Inventory

| # | Service | Report File | Assessment Date | Repo Type | Agent Scope |
|---|---------|-------------|-----------------|-----------|-------------|
| 1 | local-monolith | monolith/agentic-readiness-analysis/local-monolith-ara-report.json | 2026-05-18 | application | read-only |
| 2 | unishop-monolith | services/unishop-monolith-to-microservices/MonoToMicroLegacy/agentic-readiness-analysis/unishop-monolith-ara-report.json | 2026-05-18 | application | read-only |
| 3 | eks-saas-gitops | services/eks-saas-gitops/agentic-readiness-analysis/eks-saas-gitops-ara-report.json | 2026-05-18 | infrastructure-only | read-only |
| 4 | books-api | services/books-api/agentic-readiness-analysis/books-api-ara-report.json | 2026-05-18 | application | read-only |
| 5 | aws-microservices | services/aws-microservices/agentic-readiness-analysis/aws-microservices-ara-report.json | 2026-05-18 | application | read-only |
