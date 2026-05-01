# Portfolio Agentic Readiness Assessment Report

**Date**: 2026-04-30
**Services Assessed**: 34
**Portfolio Context**: 34 open-source project mirrors for ATX TD validation across multiple languages, architectures, and domains.

---

## Executive Dashboard

### Readiness Distribution

| Profile | Services | Percentage | Description |
|---------|----------|------------|-------------|
| ✅ Agent-Ready | 0 | 0% | 0 blockers, 0 RISK-SAFETY — broad agent deployment |
| 🟡 Pilot-Ready | 0 | 0% | 0 blockers, 1–2 RISK-SAFETY — narrow pilot |
| 🟡 Pilot-Ready (Safety Concerns) | 4 | 12% | 0 blockers, 3+ RISK-SAFETY — supervised pilot, prioritize safety |
| 🟠 Remediation Required | 22 | 65% | 1–2 blockers — remediate before any agent deployment |
| ❌ Not Agent-Integrable | 8 | 24% | 3+ blockers — deferred or descoped |

### Portfolio Summary

| Metric | Value |
|--------|-------|
| Total Services Assessed | 34 |
| Services Ready for Agents (Agent-Ready + Pilot-Ready) | 0 (0%) |
| Services Requiring Remediation | 30 (88%) |
| Cross-Cutting BLOCKERs (same blocker in 2+ repos) | 3 |
| Cross-Cutting RISKs (same risk in 3+ repos) | 27 |
| Services with Write-Enabled Agent Scope | 0 (0%) |
| Services with Read-Only Agent Scope | 34 (100%) |

### Repo Type Distribution

| Repo Type | Count | Percentage |
|-----------|-------|------------|
| monorepo | 18 | 53% |
| application | 15 | 44% |
| library | 1 | 3% |

### Blocker Heatmap by Section

| Section | Repos Blocked | % of Applicable Repos | Top Blockers |
|---------|--------------|----------------------|--------------|
| DATA | 30 | 88% | DATA-Q1 |
| AUTH | 21 | 62% | AUTH-Q1 |
| API | 12 | 35% | API-Q1 |
| STATE | 0 | 0% | — |
| HITL | 0 | 0% | — |
| DISC | 0 | 0% | — |
| OBS | 0 | 0% | — |
| ENG | 0 | 0% | — |

### Readiness Snapshot

| Metric | Value |
|--------|-------|
| assessment_date | 2026-04-30 |
| total_services | 34 |
| agent_ready | 0 |
| pilot_ready | 0 |
| pilot_ready_safety_concerns | 4 |
| remediation_required | 22 |
| not_integrable | 8 |
| total_blockers | 63 |
| total_risks | 708 |
| total_risk_safety | 268 |
| total_risk_quality | 440 |
| total_infos | 498 |
| cross_cutting_blockers | 3 |
| cross_cutting_risks | 27 |
| cross_cutting_risk_safety | 9 |
| cross_cutting_risk_quality | 18 |
| portfolio_level_blockers | 1 |
| portfolio_level_risks | 3 |
| write_enabled_services | 0 |
| read_only_services | 34 |

---

## Cross-Cutting BLOCKERs — Same Blocker in 2+ Repos

> These are BLOCKER-severity questions that appear in 2 or more repositories.
> They represent portfolio-wide agentic readiness gaps requiring coordinated remediation.
> Questions scored as N/A for a service do not count as gaps for that service.
> Note: All 34 services have agent_scope=read-only. Conditional BLOCKER questions (API-Q4, STATE-Q1, AUTH-Q6, DATA-Q2) resolve to INFO or RISK-SAFETY for read-only scope and therefore do not appear as cross-cutting BLOCKERs.

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER in 21 of 34 applicable services
- **Affected Services**: Alluxio--alluxio, Lidarr--Lidarr, Netflix--eureka, OpenAPITools--openapi-generator, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, akveo--ngx-admin, conductor-oss--conductor, coreui--coreui-free-angular-admin-template, greenshot--greenshot, gulpjs--gulp, iterative--dvc, motdotla--node-lambda, openzipkin--zipkin, realworld-apps--angular-realworld-example-app, scality--backbeat, serverless--serverless, tqdm--tqdm, umami-software--umami, webpack--webpack
- **Common Finding**: No machine identity authentication mechanism exists. Services either have no authentication at all (open endpoints), use human-style credentials (username/password, shared API keys without principal attribution), or have authentication that cannot distinguish individual agent callers. Many are CLI tools, libraries, or desktop applications that were never designed for M2M authentication.
- **Root Cause Pattern**: These open-source projects were designed for human users (developers, operators), not for autonomous agent callers. Authentication, where present, is user-centric (browser sessions, shared API keys) without support for service accounts, OAuth2 client credentials, or mTLS.
- **Portfolio-Level Remediation**:
  - **Approach**: Hybrid — deploy a centralized identity provider (platform-level) and integrate each service individually (per-service)
  - **Immediate Action**: Deploy a centralized identity provider (e.g., Amazon Cognito, Okta) with machine-to-machine client credentials flow. Define a service account provisioning pattern.
  - **Target State**: Every service that exposes a network API authenticates agent callers via OAuth2 client credentials or mTLS with per-agent principal attribution.
  - **Estimated Effort**: High
  - **Priority**: Critical — affects 62% of services; identity is the foundation for all other security controls
  - **Dependencies**: None — resolve first

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER in 30 of 34 applicable services
- **Affected Services**: Alluxio--alluxio, FlowiseAI--Flowise, Lidarr--Lidarr, Netflix--eureka, OpenAPITools--openapi-generator, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, ToolJet--ToolJet, akveo--ngx-admin, apache--druid, apache--flink-connector-aws, conductor-oss--conductor, coreui--coreui-free-angular-admin-template, getlift--lift, getsentry--sentry-python, greenshot--greenshot, gulpjs--gulp, iterative--dvc, motdotla--node-lambda, openzipkin--zipkin, realworld-apps--angular-realworld-example-app, scality--backbeat, scality--cloudserver, serverless--serverless, thingsboard--thingsboard, tqdm--tqdm, umami-software--umami, webpack--webpack, zappa--Zappa
- **Common Finding**: No sensitive data classification system exists. Services handle credentials, PII (email, names, phone numbers), API keys, tokens, and other sensitive data without field-level classification tags, access controls, or data masking. Data flows through systems without any mechanism to distinguish sensitive from non-sensitive fields.
- **Root Cause Pattern**: Open-source projects prioritize functionality over data governance. Data models store sensitive fields (credentials, PII) alongside non-sensitive fields with no classification metadata, no field-level encryption, and no access control policies that would prevent an agent from reading sensitive data.
- **Portfolio-Level Remediation**:
  - **Approach**: Hybrid — establish a portfolio-wide data classification taxonomy (platform-level) and apply field-level tags per service (per-service)
  - **Immediate Action**: Define a portfolio-wide data classification taxonomy (PUBLIC, INTERNAL, CONFIDENTIAL, PII, CREDENTIAL). Create a classification inventory template for each service to map data fields to sensitivity levels.
  - **Target State**: Every service has a data classification inventory with field-level sensitivity tags. API responses enforce classification-aware filtering — agent identities with read-only scope cannot retrieve CREDENTIAL or PII fields without explicit authorization.
  - **Estimated Effort**: High
  - **Priority**: Critical — affects 88% of services; data classification is the foundation for safe agent data access
  - **Dependencies**: AUTH-Q1 should be resolved first (need identity to enforce classification-based access controls)

### API-Q1: Documented API Interface

- **Severity**: BLOCKER in 12 of 34 applicable services
- **Affected Services**: akveo--ngx-admin, apache--flink-connector-aws, coreui--coreui-free-angular-admin-template, getlift--lift, getsentry--sentry-python, greenshot--greenshot, gulpjs--gulp, iterative--dvc, motdotla--node-lambda, realworld-apps--angular-realworld-example-app, tqdm--tqdm, zappa--Zappa
- **Common Finding**: No network-accessible API exists. These services are frontend SPAs (no backend), CLI tools, desktop applications, libraries consumed in-process, or build tools that expose programmatic APIs (function calls) but no REST/GraphQL/AsyncAPI endpoint that an agent could call over HTTP.
- **Root Cause Pattern**: These projects are not API-first services. They are libraries (tqdm, arrow, gulp, webpack), CLI tools (node-lambda, zappa, dvc), frontend SPAs (ngx-admin, coreui, angular-realworld), desktop applications (greenshot), or framework plugins (getlift--lift). They were designed for in-process consumption or human CLI interaction, not for remote agent integration via network APIs.
- **Portfolio-Level Remediation**:
  - **Approach**: Per-service — each service needs an API wrapper or must be descoped from agent integration
  - **Immediate Action**: Categorize affected services: (a) services that could benefit from an API wrapper (e.g., CLI tools that could expose REST endpoints), (b) services that should be descoped from agent integration (pure frontend templates, desktop apps).
  - **Target State**: Services targeted for agent integration expose at least one documented, machine-readable API endpoint. Services not suited for API exposure are marked as "not agent-integrable" in the portfolio inventory.
  - **Estimated Effort**: High (varies per service — some need full API layer development)
  - **Priority**: High — affects 35% of services; however, many of these may be correctly descoped as not requiring agent integration
  - **Dependencies**: None

---

## Cross-Cutting RISKs

### Cross-Cutting RISK-SAFETY — Same Safety Risk in 3+ Repos

> These are RISK-SAFETY questions that appear in 3 or more repositories.
> They represent portfolio-wide agent safety gaps requiring coordinated attention.
> Questions scored as N/A for a service do not count as gaps for that service.

#### AUTH-Q6: Write-Path Authorization Controls

- **Severity**: RISK-SAFETY in 34 of 34 applicable services
- **Affected Services**: All 34 services
- **Common Finding**: No write-path authorization controls exist. Since all services are assessed at read-only agent scope, this conditional question resolves to RISK-SAFETY rather than BLOCKER. If agent scope were escalated to write-enabled, this would become a BLOCKER for all services.
- **Compensating Controls**: Read-only agent scope limits blast radius. Write operations are not authorized for agents.
- **Portfolio-Level Recommendation**: Before escalating any service to write-enabled agent scope, implement role-based write-path authorization with approval workflows. Design a standard authorization pattern that can be adopted across services.
- **Estimated Effort**: High

#### DATA-Q2: Read/Write Access Control on Sensitive Data

- **Severity**: RISK-SAFETY in 32 of 34 applicable services
- **Affected Services**: 32 services (all except dwyl--aws-sdk-mock, scality--backbeat which are N/A for this question)
- **Common Finding**: No field-level read/write access controls on sensitive data. Since all services are read-only scope, this conditional resolves to RISK-SAFETY. Agents can read all data including sensitive fields without restriction.
- **Compensating Controls**: Read-only scope prevents data modification. Data classification (DATA-Q1) remediation will enable field-level access controls.
- **Portfolio-Level Recommendation**: After resolving DATA-Q1 (classification), implement field-level access controls that filter sensitive data from agent responses based on agent identity and authorization level.
- **Estimated Effort**: High

#### STATE-Q1: Atomic State Transitions

- **Severity**: RISK-SAFETY in 31 of 34 applicable services
- **Affected Services**: 31 services (all except conductor-oss--conductor, dwyl--aws-sdk-mock, scality--backbeat which are N/A)
- **Common Finding**: State transitions lack atomicity guarantees suitable for agent operations. Since all services are read-only scope, this conditional resolves to RISK-SAFETY. Non-atomic state changes could lead to inconsistent reads.
- **Compensating Controls**: Read-only scope prevents state modification. Eventual consistency is acceptable for read operations in most cases.
- **Portfolio-Level Recommendation**: Before enabling write operations, implement atomic state transition patterns (database transactions, optimistic concurrency) across services that manage mutable state.
- **Estimated Effort**: Medium

#### AUTH-Q2: Scoped Permissions

- **Severity**: RISK-SAFETY in 30 of 34 applicable services
- **Affected Services**: 30 services (excludes arrow-py--arrow, dwyl--aws-sdk-mock and 2 others where the question is N/A or INFO)
- **Common Finding**: No scoped permissions for agent callers. Services either have no permission system or use coarse-grained roles (admin/user) that cannot restrict agent access to specific resources or operations.
- **Compensating Controls**: Read-only agent scope inherently limits the scope of operations.
- **Portfolio-Level Recommendation**: Implement fine-grained, resource-level permissions that can be assigned per agent identity. Define a standard permission model (e.g., RBAC with resource scoping) adoptable across the portfolio.
- **Estimated Effort**: High

#### AUTH-Q7: Sensitive Operation Re-Authentication

- **Severity**: RISK-SAFETY in 29 of 34 applicable services
- **Affected Services**: 29 services
- **Common Finding**: No re-authentication or step-up authentication for sensitive operations. Even for read-only scope, accessing sensitive data (PII, credentials, configuration secrets) does not require additional authentication beyond initial session establishment.
- **Compensating Controls**: Read-only scope limits the set of sensitive operations. Data classification enforcement (once implemented) can gate access to sensitive reads.
- **Portfolio-Level Recommendation**: Implement step-up authentication for accessing classified data (PII, CREDENTIAL sensitivity levels). Design a challenge/response pattern for sensitive data access requests.
- **Estimated Effort**: Medium

#### DATA-Q6: Data Integrity Validation

- **Severity**: RISK-SAFETY in 31 of 34 applicable services
- **Affected Services**: 31 services
- **Common Finding**: No data integrity validation mechanisms for agent-accessible data. No checksums, version stamps, or integrity verification on data returned to agents. Data could be corrupted or tampered with between read and consumption.
- **Compensating Controls**: Read-only scope limits integrity risk to data consumption (not modification). Application-level validation in agent logic can compensate.
- **Portfolio-Level Recommendation**: Implement data integrity markers (ETags, content hashes, version timestamps) on API responses. Enable agents to verify data freshness and integrity before acting on it.
- **Estimated Effort**: Medium

#### STATE-Q5: Transaction Boundary Definition

- **Severity**: RISK-SAFETY in 29 of 34 applicable services
- **Affected Services**: 29 services
- **Common Finding**: Transaction boundaries are not clearly defined for agent-consumable operations. Multi-step operations lack explicit transaction demarcation, making it unclear which operations are atomic and which may leave partial state.
- **Compensating Controls**: Read-only scope reduces transaction boundary concerns (reads are generally non-transactional). However, complex read operations spanning multiple resources may return inconsistent snapshots.
- **Portfolio-Level Recommendation**: Document transaction boundaries for all API operations. For read operations, implement snapshot isolation or consistent read patterns where multiple resources are queried together.
- **Estimated Effort**: Medium

#### AUTH-Q3: Short-Lived Credentials

- **Severity**: RISK-SAFETY in 26 of 34 applicable services
- **Affected Services**: 26 services
- **Common Finding**: Long-lived or non-expiring credentials used for authentication. API keys, static tokens, and password-based sessions do not have automatic rotation or expiration. Compromised credentials remain valid indefinitely.
- **Compensating Controls**: Read-only scope limits the damage from credential compromise to data exposure (not modification).
- **Portfolio-Level Recommendation**: Migrate to short-lived credential patterns: OAuth2 access tokens with 1-hour expiry, STS temporary credentials, or mTLS certificates with automated rotation. Implement credential rotation policies portfolio-wide.
- **Estimated Effort**: Medium

#### STATE-Q4: State Validation Before Commit

- **Severity**: RISK-SAFETY in 25 of 25 applicable services
- **Affected Services**: 25 services (9 services have this question as N/A)
- **Common Finding**: No pre-commit state validation for agent-initiated operations. State changes are applied without validating preconditions, business rules, or data consistency constraints before committing.
- **Compensating Controls**: Read-only scope means agents cannot commit state changes. Validation is relevant only for future write-enabled scope.
- **Portfolio-Level Recommendation**: Implement pre-commit validation hooks that verify business rules and data consistency before any state change is persisted. Design a validation middleware pattern adoptable across services.
- **Estimated Effort**: Medium

### Cross-Cutting RISK-QUALITY — Same Quality Risk in 3+ Repos

> These are RISK-QUALITY questions that appear in 3 or more repositories.
> They represent portfolio-wide quality patterns to address as capacity allows.
> Questions scored as N/A for a service do not count as gaps for that service.

#### DISC-Q1: Service Discovery / Registry

- **Severity**: RISK-QUALITY in 34 of 34 applicable services
- **Affected Services**: All 34 services
- **Common Finding**: No service discovery or registry mechanism for agent tooling. Services are not registered in a catalog that agents could query to discover available tools, endpoints, or capabilities.
- **Portfolio-Level Recommendation**: Implement a service catalog or tool registry (e.g., MCP server registry, API Gateway service map) that agents can query to discover available services and their capabilities.
- **Estimated Effort**: Medium

#### ENG-Q2: CI/CD Pipeline

- **Severity**: RISK-QUALITY in 33 of 33 applicable services
- **Affected Services**: 33 services (1 N/A)
- **Common Finding**: CI/CD pipelines exist but lack agent-aware quality gates — no automated ARA regression checks, no agent integration test stages, no canary deployment patterns for agent-accessed services.
- **Portfolio-Level Recommendation**: Add agent-readiness quality gates to CI/CD pipelines: automated ARA checks on PR, agent integration test stages, and canary deployment patterns for services in the agent integration path.
- **Estimated Effort**: Medium

#### HITL-Q3: Human Override / Kill Switch

- **Severity**: RISK-QUALITY in 32 of 34 applicable services
- **Affected Services**: 32 services
- **Common Finding**: No human override or kill switch mechanism for agent operations. No circuit breaker, emergency stop, or admin override that could immediately halt all agent activity on a service.
- **Portfolio-Level Recommendation**: Implement a portfolio-wide agent kill switch (e.g., feature flag, API Gateway policy, Cognito app client disable) that can suspend all agent access across services. Add per-service circuit breakers for granular control.
- **Estimated Effort**: Medium

#### OBS-Q2: Distributed Tracing

- **Severity**: RISK-QUALITY in 32 of 34 applicable services
- **Affected Services**: 32 services
- **Common Finding**: No distributed tracing instrumentation. Services lack trace context propagation (W3C Trace Context, X-Amzn-Trace-Id) that would enable end-to-end visibility of agent request flows across services.
- **Portfolio-Level Recommendation**: Instrument all services with distributed tracing (AWS X-Ray, OpenTelemetry). Ensure trace context propagation in all inter-service calls and agent-initiated requests.
- **Estimated Effort**: Medium

#### OBS-Q1: Structured Logging

- **Severity**: RISK-QUALITY in 32 of 34 applicable services
- **Affected Services**: 32 services
- **Common Finding**: Logging exists but is not structured (JSON format) or lacks agent-relevant fields (caller identity, action type, resource accessed). Logs cannot be easily correlated with agent actions.
- **Portfolio-Level Recommendation**: Standardize structured JSON logging across all services with required fields: timestamp, level, caller_id, action, resource, trace_id. Centralize log aggregation in CloudWatch Logs or OpenSearch.
- **Estimated Effort**: Medium

#### API-Q2: Consistent Error Handling

- **Severity**: RISK-QUALITY in 31 of 34 applicable services
- **Affected Services**: 31 services
- **Common Finding**: Error responses are inconsistent across endpoints — mix of plain text, HTML, and JSON error formats. No standard error envelope (error code, message, details) that agents can parse reliably.
- **Portfolio-Level Recommendation**: Adopt a standard error response format (RFC 7807 Problem Details or equivalent) across all API-exposing services. Implement error middleware/interceptors that enforce the standard format.
- **Estimated Effort**: Low

#### API-Q3: Input Validation

- **Severity**: RISK-QUALITY in 30 of 34 applicable services
- **Affected Services**: 30 services
- **Common Finding**: Input validation exists but is inconsistent — some endpoints validate, others accept arbitrary input. No standard validation framework or consistent error messages for validation failures that agents can interpret.
- **Portfolio-Level Recommendation**: Implement schema-based input validation on all API endpoints (JSON Schema, OpenAPI request validation). Return machine-readable validation error messages.
- **Estimated Effort**: Medium

#### ENG-Q1: Automated Testing Coverage

- **Severity**: RISK-QUALITY in 29 of 32 applicable services
- **Affected Services**: 29 services
- **Common Finding**: Test suites exist but do not include agent integration scenarios — no tests for M2M authentication flows, no tests for agent-specific rate limits, no tests for data classification enforcement.
- **Portfolio-Level Recommendation**: Add agent integration test templates to the portfolio's testing standards. Include M2M auth flow tests, rate limit tests, and data access control tests in CI/CD pipelines.
- **Estimated Effort**: Medium

#### ENG-Q3: Infrastructure as Code

- **Severity**: RISK-QUALITY in 29 of 32 applicable services
- **Affected Services**: 29 services
- **Common Finding**: Infrastructure is partially or not codified. Manual deployment steps, undocumented infrastructure requirements, or Docker-only deployments without cloud-native IaC (CloudFormation, Terraform, CDK).
- **Portfolio-Level Recommendation**: Standardize on IaC tooling (CDK, Terraform) for all services. Include agent infrastructure requirements (Cognito app clients, API Gateway usage plans, WAF rules) in IaC templates.
- **Estimated Effort**: High

#### ENG-Q4: Environment Parity

- **Severity**: RISK-QUALITY in 22 of 33 applicable services
- **Affected Services**: 22 services
- **Common Finding**: Significant environment parity gaps between development and production. Docker Compose for local development does not match production deployment patterns. Agent behavior may differ across environments.
- **Portfolio-Level Recommendation**: Implement environment parity standards: containerized deployments matching production, shared configuration management, environment-specific agent scope controls.
- **Estimated Effort**: Medium

#### AUTH-Q5: Credential Management

- **Severity**: RISK-QUALITY in 21 of 34 applicable services
- **Affected Services**: 21 services
- **Common Finding**: Credentials managed via environment variables, configuration files, or hardcoded values. No secrets management integration (AWS Secrets Manager, Parameter Store). Credential rotation is manual or nonexistent.
- **Portfolio-Level Recommendation**: Migrate all credential storage to AWS Secrets Manager or Parameter Store. Implement automated rotation policies. Remove hardcoded credentials from configuration files.
- **Estimated Effort**: Medium

#### DATA-Q3: PII Handling

- **Severity**: RISK-QUALITY in 18 of 22 applicable services
- **Affected Services**: 18 services
- **Common Finding**: PII fields (email, name, phone, IP address) are stored and returned in API responses without masking, encryption, or access controls. No PII-specific handling policies.
- **Portfolio-Level Recommendation**: Implement PII handling standards: field-level encryption at rest, masking in API responses for non-privileged callers, PII access audit logging.
- **Estimated Effort**: Medium

#### API-Q6: Rate-Limiting / Throttling

- **Severity**: RISK-QUALITY in 18 of 22 applicable services
- **Affected Services**: 18 services
- **Common Finding**: No rate limiting or throttling on API endpoints. Agent traffic storms could overwhelm services. Some services have internal connection limits but no per-caller rate limiting.
- **Portfolio-Level Recommendation**: Deploy API Gateway or WAF-based rate limiting for all agent-accessible services. Define per-agent rate limit tiers based on service criticality.
- **Estimated Effort**: Medium

#### DATA-Q5: Data Masking for Agent Visibility

- **Severity**: RISK-QUALITY in 18 of 21 applicable services
- **Affected Services**: 18 services
- **Common Finding**: No data masking for agent visibility. Sensitive fields are returned in full to all callers. No mechanism to return masked/redacted versions of sensitive data to agents.
- **Portfolio-Level Recommendation**: Implement field-level data masking middleware that redacts sensitive fields for agent callers based on their authorization level and the data classification taxonomy.
- **Estimated Effort**: Medium

#### ENG-Q5: Dependency Management

- **Severity**: RISK-QUALITY in 17 of 19 applicable services
- **Affected Services**: 17 services
- **Common Finding**: Dependencies are declared but not actively managed for security. No automated vulnerability scanning, no dependency update policies, no SBOM generation.
- **Portfolio-Level Recommendation**: Implement automated dependency scanning (Dependabot, Snyk) across all repositories. Generate SBOMs and enforce vulnerability remediation SLAs.
- **Estimated Effort**: Low

#### DATA-Q4: Data Retention / Lifecycle Policies

- **Severity**: RISK-QUALITY in 15 of 17 applicable services
- **Affected Services**: 15 services
- **Common Finding**: No data retention or lifecycle policies. Data persists indefinitely without TTL, archival, or deletion schedules. Agent-accessed audit logs and operational data accumulate without bounds.
- **Portfolio-Level Recommendation**: Define portfolio-wide data retention policies. Implement TTL-based data lifecycle management for operational data, audit logs, and agent interaction records.
- **Estimated Effort**: Medium

#### AUTH-Q4: Agent Action Audit Trail

- **Severity**: RISK-QUALITY in 15 of 34 applicable services
- **Affected Services**: 15 services
- **Common Finding**: No dedicated agent action audit trail. Application logs exist but do not capture agent-specific metadata (agent identity, action intent, tool invocation context). Cannot reconstruct what an agent did or why.
- **Portfolio-Level Recommendation**: Implement a structured agent audit log format capturing: agent_id, action, resource, timestamp, intent, result. Centralize in a dedicated audit trail (CloudWatch Logs, S3 audit bucket).
- **Estimated Effort**: Medium

#### STATE-Q2: Concurrency Control

- **Severity**: RISK-QUALITY in 11 of 20 applicable services
- **Affected Services**: 11 services
- **Common Finding**: No concurrency control mechanisms (optimistic locking, ETags, version stamps). Concurrent agent and human operations could cause lost updates or inconsistent state.
- **Portfolio-Level Recommendation**: Implement optimistic concurrency control (ETag/If-Match headers, version columns) on all mutable resources. Return conflict errors (HTTP 409) with current state for retry.
- **Estimated Effort**: Medium

---

## Service Dependency Map

> Dependencies were inferred from individual ARA report findings (not explicitly provided via `dependency_overrides`). Inferred dependencies may be incomplete — they reflect only what was observable in the assessed code and report context. For authoritative dependency data, add `dependency_overrides` to the portfolio config.

### Inferred Dependencies

The following inter-service references were detected by scanning individual ARA report findings for mentions of other services in the portfolio:

| Source Service | Target Service | Type | Description | Inferred |
|---------------|---------------|------|-------------|----------|
| scality--backbeat | scality--cloudserver | sync | Backbeat orchestrates replication/lifecycle tasks and calls CloudServer (S3-compatible API) as a downstream service | Yes |
| scality--cloudserver | scality--backbeat | async | CloudServer references Backbeat for background replication and lifecycle workflows | Yes |
| Prowlarr--Prowlarr | Sonarr--Sonarr | sync | Prowlarr acts as an indexer manager/proxy for Sonarr | Yes |
| Prowlarr--Prowlarr | Radarr--Radarr | sync | Prowlarr acts as an indexer manager/proxy for Radarr | Yes |
| Prowlarr--Prowlarr | Lidarr--Lidarr | sync | Prowlarr acts as an indexer manager/proxy for Lidarr | Yes |
| Radarr--Radarr | Sonarr--Sonarr | shared_infra | *arr suite shared architecture patterns and Prowlarr integration | Yes |
| Radarr--Radarr | Lidarr--Lidarr | shared_infra | *arr suite shared architecture patterns | Yes |

### Service Dependency Metrics

| Service | Fan-In | Fan-Out | Role | Readiness Profile |
|---------|--------|---------|------|-------------------|
| Sonarr--Sonarr | 2 | 0 | Foundation | Remediation Required |
| Radarr--Radarr | 1 | 2 | Internal | Remediation Required |
| Lidarr--Lidarr | 2 | 0 | Foundation | Remediation Required |
| Prowlarr--Prowlarr | 0 | 3 | Leaf | Remediation Required |
| scality--backbeat | 1 | 1 | Internal | Remediation Required |
| scality--cloudserver | 1 | 1 | Internal | Remediation Required |

> Note: The remaining 28 services have no detected inter-service dependencies (fan-in = 0, fan-out = 0). This is expected as they are independent open-source projects, not microservices in a single platform.

### Dependency-Aware Readiness Insights

1. ***arr Suite Dependency Chain**: Prowlarr depends on Sonarr, Radarr, and Lidarr for indexer proxy functionality. All four services are "Remediation Required" with 2 BLOCKERs each (AUTH-Q1, DATA-Q1). Coordinated remediation across the *arr suite would resolve the shared architecture blockers simultaneously.
   - **Affected Services**: Prowlarr--Prowlarr, Sonarr--Sonarr, Radarr--Radarr, Lidarr--Lidarr
   - **Risk**: Shared authentication pattern (single API key) means AUTH-Q1 remediation must be coordinated across all 4 services.
   - **Recommendation**: Implement a shared identity provider for the *arr suite. Migrate from single shared API key to per-agent OAuth2 client credentials.

2. **Scality Backbeat ↔ CloudServer**: Bidirectional dependency between Backbeat (orchestrator) and CloudServer (S3-compatible storage). Both are "Remediation Required." Backbeat calls CloudServer for S3 operations, and CloudServer triggers Backbeat for replication workflows.
   - **Affected Services**: scality--backbeat, scality--cloudserver
   - **Risk**: Backbeat's AUTH-Q1 BLOCKER (IP allowlist-only authentication) means CloudServer's agent integration is also affected — agents accessing CloudServer may trigger Backbeat workflows without proper identity propagation.
   - **Recommendation**: Implement M2M authentication between Backbeat and CloudServer. Ensure agent identity propagation across the Backbeat ↔ CloudServer boundary.

3. **No High-Risk Foundation Services**: No service with fan-in ≥ 3 and "Not Agent-Integrable" profile was detected. The *arr suite's Sonarr and Lidarr (fan-in = 2) are "Remediation Required" but not "Not Agent-Integrable," so transitive blocker propagation is limited.

---

## Portfolio Remediation Guidance

> Portfolio context: 34 open-source project mirrors for ATX TD validation across multiple languages, architectures, and domains. Remediation guidance below is illustrative for this validation portfolio. Real customer portfolios with interconnected microservices would have more targeted, coordinated remediation paths.

### Remediation Priority Order

Remediation of cross-cutting BLOCKERs should follow this general priority:

1. **Identity and Access** — Resolve AUTH-section BLOCKERs first. You cannot enforce any other security control without machine identity and scoped permissions.
2. **Data Integrity** — Resolve STATE and DATA-section BLOCKERs second. Protect data before enabling agent write operations.
3. **API Surface** — Resolve API-section BLOCKERs third. Ensure a stable, documented integration surface for agent tools.
4. **Remaining BLOCKERs** — Address in order of affected service count (most affected first).

### Coordinated Remediation Plan

#### Workstream 1: Identity Foundation

**BLOCKERs addressed**: AUTH-Q1 (Machine Identity Authentication)
**Services affected**: 21 services (62%)

- **What to do**:
  1. Deploy a centralized identity provider (Amazon Cognito User Pool or equivalent) with OAuth2 client credentials grant support.
  2. Define an agent identity provisioning workflow: each agent receives a unique client_id/client_secret pair with scoped permissions.
  3. For each service with a network API: integrate the IdP as an authentication middleware (API Gateway Cognito authorizer, Spring Security OAuth2 resource server, Express.js passport-oauth2, etc.).
  4. For services without network APIs (CLI tools, libraries): these are correctly classified as "Not Agent-Integrable" and do not require identity integration — descope them from the agent toolset.
- **Expected outcome**: Every network-accessible service authenticates agent callers via OAuth2 client credentials with per-agent principal attribution in audit logs. Agent actions are traceable to individual agent identities.
- **Effort**: High — estimated 2–4 weeks for platform setup, 1–2 weeks per service for integration.

#### Workstream 2: Data Classification & Protection

**BLOCKERs addressed**: DATA-Q1 (Sensitive Data Classification)
**Services affected**: 30 services (88%)

- **What to do**:
  1. Define a portfolio-wide data classification taxonomy: PUBLIC, INTERNAL, CONFIDENTIAL, PII, CREDENTIAL.
  2. Create a data classification inventory template (spreadsheet or structured YAML) mapping each service's data model fields to sensitivity levels.
  3. For each service: complete the classification inventory by reviewing database schemas, API response payloads, and configuration files.
  4. Implement classification-aware API middleware that enforces field-level access controls based on caller identity and sensitivity level (depends on Workstream 1 completion).
- **Expected outcome**: Every service has a data classification inventory. API responses enforce classification-based filtering — agent identities cannot access CREDENTIAL or PII fields without explicit authorization.
- **Effort**: High — estimated 1–2 weeks per service for inventory, 2–4 weeks for enforcement middleware.

#### Workstream 3: API Surface Enablement

**BLOCKERs addressed**: API-Q1 (Documented API Interface)
**Services affected**: 12 services (35%)

- **What to do**:
  1. Categorize affected services into two groups:
     - **Descope**: Pure frontend templates (ngx-admin, coreui, angular-realworld), desktop apps (greenshot), and libraries with no remote integration need (tqdm, gulp) — mark as "Not Agent-Integrable" in portfolio inventory.
     - **API Wrap**: CLI tools and services that could benefit from an API wrapper (node-lambda, zappa, dvc, getlift--lift, getsentry--sentry-python, apache--flink-connector-aws) — implement thin REST API wrappers or MCP tool adapters.
  2. For services requiring API wrappers: implement OpenAPI-documented REST endpoints exposing key functionality.
- **Expected outcome**: Services targeted for agent integration have documented, machine-readable API endpoints. Services not suited for API exposure are formally descoped.
- **Effort**: High (varies) — 1–4 weeks per service depending on complexity.

---

## Agentic Program Recommendations

> These are engagement-level recommendations based on the portfolio's agentic readiness
> profile. Discuss with your AWS Solutions Architect to determine eligibility and timing.

| Program | Relevance | Trigger Findings | Suggested Timing | Next Step |
|---------|-----------|-----------------|------------------|-----------|
| AI DLC | ENG-Q2 RISK-QUALITY in 33/33 services indicates CI/CD maturity gaps | 97% of services lack agent-aware CI/CD quality gates | Run first — establish AI-driven development practices | Request engagement via AWS Solutions Architect |
| AgentStorming | Portfolio context is "ATX TD validation" — no defined agent use cases for production | No clear agent scope or production use case defined in portfolio context | Run after AI DLC to identify agent opportunities | Request workshop via AWS Solutions Architect |
| EBA on Agentic AI | DATA-Q1 BLOCKER in 30 repos, AUTH-Q1 BLOCKER in 21 repos | 2 cross-cutting BLOCKERs each affect 5+ repositories | Run after AXE to accelerate implementation | Request engagement via AWS Solutions Architect |

> Note: AXE (Agentic Experience Workshop) is **not triggered** for this portfolio. AXE requires 3+ services in Agent-Ready or Pilot-Ready profile. This portfolio has 0 Agent-Ready and 0 Pilot-Ready services (only 4 Pilot-Ready with Safety Concerns). Revisit after remediation progresses.

### Program Details

#### AI DLC (AI Driven Development Lifecycle)

- **Why triggered**: ENG-Q2 (CI/CD Pipeline) is RISK-QUALITY in 33 of 33 applicable services — indicating that while CI/CD pipelines exist, none include agent-aware quality gates, automated ARA regression checks, or agent integration test stages. The portfolio's engineering maturity for agentic development is uniformly low across all 34 services.
- **What it provides**: Workshop for adopting the AI Driven Development Lifecycle, emphasizing: (1) AI Powered Execution with Human Oversight — AI creates detailed work plans, seeks clarification, and defers critical decisions to humans; (2) Dynamic Team Collaboration — teams unite in collaborative spaces for real-time problem solving as AI handles routine tasks.
- **Suggested timing**: Run first, before other programs. Establishing AI-driven development practices creates the foundation for subsequent agentic work.
- **Recommended scope**: Focus on the 4 Pilot-Ready (Safety Concerns) services (arrow-py--arrow, dwyl--aws-sdk-mock, Graylog2--graylog2-server, hapifhir--hapi-fhir) as initial candidates for AI-assisted development workflows.
- **Next step**: Request engagement via AWS Solutions Architect.

#### AgentStorming

- **Why triggered**: The portfolio context describes "ATX TD validation" — a testing/validation use case without defined production agent use cases. The assessment was run across 34 independent open-source projects without a clear agent scope or business process mapping. AgentStorming would help identify where agents should operate before investing in remediation.
- **What it provides**: A workshop format that builds on EventStorming by adding Cognitive Complexity Analysis and Agentic Workflow Design to pinpoint where agentic AI delivers real value versus traditional automation. Provides a structured path from "where should we use AI?" to implementation-ready answers.
- **Suggested timing**: Run after AI DLC. Use AgentStorming output to prioritize which services in the portfolio should be remediated for agent integration versus descoped.
- **Recommended scope**: Focus on services with existing API surfaces (monorepos with REST APIs) — these are the most likely candidates for agent integration. Deprioritize libraries, CLI tools, and frontend templates.
- **Next step**: Request workshop via AWS Solutions Architect.

#### EBA on Agentic AI (Experience-Based Acceleration)

- **Why triggered**: Two cross-cutting BLOCKERs affect 5+ repositories: DATA-Q1 (Sensitive Data Classification) affects 30 repositories, and AUTH-Q1 (Machine Identity Authentication) affects 21 repositories. These systemic, portfolio-wide gaps require coordinated architecture remediation that cannot be resolved through individual service fixes alone.
- **What it provides**: An intensive, time-boxed engagement that accelerates the path from ARA findings to production deployment of autonomous AI agents. Embeds AWS expertise to compress multi-quarter remediation cycles into a focused sprint, producing remediated systems, validated agent integrations, and a sequenced deployment roadmap.
- **Suggested timing**: Run after AgentStorming and AXE (if applicable). Use EBA to execute the remediation workstreams identified in this portfolio assessment — particularly the Identity Foundation and Data Classification workstreams.
- **Recommended scope**: Focus on the top-priority remediation workstreams: (1) Deploy centralized identity provider for AUTH-Q1 remediation across 21 services, (2) Implement data classification taxonomy and field-level controls for DATA-Q1 remediation across 30 services.
- **Next step**: Request engagement via AWS Solutions Architect.

---

## Portfolio-Level Findings

> These questions evaluate capabilities that can only be assessed by looking across
> multiple repos. They are distinct from cross-cutting analysis (which aggregates
> individual findings). Individual report findings are never overridden.

### PORT-ARA-Q1: Centralized Identity Plane

- **Severity**: BLOCKER
- **Finding**: No shared identity provider exists across any of the 34 repositories. Each service that implements authentication does so independently: some use API keys (Sonarr, Radarr, Lidarr, Prowlarr), some use username/password login (umami, ToolJet), some use OAuth2 outbound only (greenshot), and 21 services have no authentication at all. There is no Cognito User Pool, Okta configuration, shared auth middleware, or centralized identity service referenced across multiple repositories.
- **Evidence**: Scanned all 34 repositories for shared IdP references (Cognito, Okta, Auth0, Keycloak, shared JWT issuer). No shared identity resource (ARN, name, or config reference) appears in 2+ repos. Each service manages identity independently.
- **Recommendation**: Deploy a centralized identity provider (Amazon Cognito User Pool with machine-to-machine app clients) that all agent-facing services integrate with. Define a standard authentication middleware pattern for each language/framework in the portfolio (Java Spring Security, Node.js Express, Python Flask/Django, C# ASP.NET Core).
- **Affected Services**: All 34 services — none have centralized identity integration.
- **Contextual Annotations**:
  > **Portfolio Context**: PORT-ARA-Q1 confirms the absence of a centralized identity plane. This directly reinforces AUTH-Q1 (cross-cutting BLOCKER in 21 services) — even services that have some authentication do not share an identity provider, making coordinated agent identity management impossible without platform-level remediation.

### PORT-ARA-Q2: Cross-Service Audit Correlation

- **Severity**: RISK
- **Finding**: No cross-service audit correlation mechanism exists. Services log independently with different formats (structured JSON, plain text, Log4j, console.log). No shared CloudTrail trail, no consistent trace ID headers (X-Amzn-Trace-Id, traceparent), and no centralized log aggregation covering multiple services. Agent actions across services cannot be correlated end-to-end.
- **Evidence**: Scanned all 34 repos for shared trace context propagation, centralized log aggregation configuration, or CloudTrail integration. Found distributed tracing libraries in some services (OpenTelemetry in openzipkin, Spring Cloud Sleuth in Netflix--eureka) but no shared tracing infrastructure across the portfolio.
- **Recommendation**: Implement centralized log aggregation (CloudWatch Logs with shared retention policies or OpenSearch). Standardize trace context propagation (W3C Trace Context or X-Amzn-Trace-Id) across all services. Define a common log schema that includes agent_id, trace_id, and action fields.
- **Affected Services**: All 34 services.
- **Contextual Annotations**: None — this is a new finding not directly related to individual cross-cutting BLOCKERs.

### PORT-ARA-Q3: Portfolio-Level Rate Limiting

- **Severity**: RISK
- **Finding**: No shared API gateway, WAF, or portfolio-level rate limiting exists. Each service handles traffic independently. No shared WAF WebACL, no centralized API Gateway with usage plans, and no portfolio-level protection against agent traffic storms.
- **Evidence**: Scanned all 34 repos for shared WAF configurations, API Gateway references, or centralized rate limiting. Some individual services have internal rate limiting (e.g., Graylog's internal rate limiters), but no portfolio-perimeter protection exists.
- **Recommendation**: Deploy a portfolio-level API Gateway (Amazon API Gateway) or WAF with rate limiting rules for agent traffic. Define per-agent usage plans with throttling tiers based on service criticality.
- **Affected Services**: All services with network APIs (approximately 22 services).
- **Contextual Annotations**: None.

### PORT-ARA-Q4: Transitive Dependency Safety

- **Severity**: INFO
- **Finding**: No transitive agent safety risks detected. The inferred dependency graph shows limited inter-service dependencies (7 edges among 6 services). No service with Agent-Ready or Pilot-Ready profile depends synchronously on a Not Agent-Integrable service. The *arr suite services (all Remediation Required) have inter-dependencies but no service in the chain is Not Agent-Integrable. The Scality pair (backbeat ↔ cloudserver) are both Remediation Required.
- **Evidence**: Dependency graph from Step 6. No Agent-Ready or Pilot-Ready services exist in the portfolio (0 + 0 = 0), so transitive dependency risk is moot — no service is ready for agent deployment. The 4 Pilot-Ready (Safety Concerns) services (arrow-py--arrow, dwyl--aws-sdk-mock, Graylog2--graylog2-server, hapifhir--hapi-fhir) have no detected dependencies on other portfolio services.
- **Recommendation**: Re-evaluate transitive dependency safety after remediation progresses and services achieve Pilot-Ready or Agent-Ready profiles. For the *arr suite, ensure coordinated remediation so that Prowlarr's agent integration is not blocked by downstream Sonarr/Radarr/Lidarr readiness.
- **Affected Services**: Prowlarr--Prowlarr (depends on Sonarr, Radarr, Lidarr), scality--backbeat (depends on scality--cloudserver).
- **Contextual Annotations**: None.

### PORT-ARA-Q5: Agent Identity Governance

- **Severity**: RISK
- **Finding**: No centralized mechanism exists to suspend or revoke agent identities across all services simultaneously. Each service manages agent access independently — some via API keys (which must be rotated per-service), some via username/password (per-service), and most with no agent identity concept at all. There is no centralized agent identity registry, no portfolio-wide kill switch, and no coordinated revocation mechanism.
- **Evidence**: Scanned all 34 repos for centralized identity registries, shared Cognito app client configurations, or coordinated key management. No such mechanisms exist. The *arr suite shares an API key pattern but each instance maintains its own key independently.
- **Recommendation**: Implement a centralized agent identity registry (Cognito app client registry or equivalent) with the ability to disable all agent app clients simultaneously. Design a portfolio-wide agent kill switch that can be activated in an emergency to revoke all agent access within minutes.
- **Affected Services**: All 34 services.
- **Contextual Annotations**:
  > **Portfolio Context**: PORT-ARA-Q5 reinforces AUTH-Q1 findings — without centralized identity, there is no centralized revocation. Resolving AUTH-Q1 with a shared IdP (Workstream 1 in Remediation Guidance) automatically enables centralized agent identity governance through the IdP's app client management.

---

## Service-by-Service Summary

| Service | Repo Type | Agent Scope | Readiness Profile | BLOCKERs | RISKs | INFOs | N/A |
|---------|-----------|-------------|-------------------|----------|-------|-------|-----|
| akveo--ngx-admin | application | read-only | ❌ Not Agent-Integrable | 3 | 17 | 11 | 12 |
| coreui--coreui-free-angular-admin-template | application | read-only | ❌ Not Agent-Integrable | 3 | 18 | 10 | 12 |
| greenshot--greenshot | monorepo | read-only | ❌ Not Agent-Integrable | 3 | 26 | 11 | 3 |
| gulpjs--gulp | application | read-only | ❌ Not Agent-Integrable | 3 | 20 | 10 | 10 |
| iterative--dvc | application | read-only | ❌ Not Agent-Integrable | 3 | 27 | 12 | 1 |
| motdotla--node-lambda | application | read-only | ❌ Not Agent-Integrable | 3 | 20 | 13 | 7 |
| realworld-apps--angular-realworld-example-app | application | read-only | ❌ Not Agent-Integrable | 3 | 20 | 11 | 9 |
| tqdm--tqdm | application | read-only | ❌ Not Agent-Integrable | 3 | 17 | 14 | 9 |
| Alluxio--alluxio | monorepo | read-only | 🟠 Remediation Required | 2 | 22 | 15 | 4 |
| apache--druid | monorepo | read-only | 🟠 Remediation Required | 1 | 24 | 12 | 1 |
| apache--flink-connector-aws | monorepo | read-only | 🟠 Remediation Required | 2 | 15 | 17 | 11 |
| conductor-oss--conductor | monorepo | read-only | 🟠 Remediation Required | 2 | 24 | 16 | 1 |
| FlowiseAI--Flowise | monorepo | read-only | 🟠 Remediation Required | 1 | 21 | 20 | 1 |
| getlift--lift | application | read-only | 🟠 Remediation Required | 2 | 14 | 19 | 8 |
| getsentry--sentry-python | application | read-only | 🟠 Remediation Required | 2 | 17 | 16 | 8 |
| Lidarr--Lidarr | monorepo | read-only | 🟠 Remediation Required | 2 | 22 | 18 | 1 |
| Netflix--eureka | monorepo | read-only | 🟠 Remediation Required | 2 | 25 | 15 | 1 |
| OpenAPITools--openapi-generator | application | read-only | 🟠 Remediation Required | 2 | 19 | 15 | 7 |
| openzipkin--zipkin | monorepo | read-only | 🟠 Remediation Required | 2 | 24 | 15 | 2 |
| Prowlarr--Prowlarr | monorepo | read-only | 🟠 Remediation Required | 2 | 27 | 13 | 1 |
| Radarr--Radarr | monorepo | read-only | 🟠 Remediation Required | 2 | 26 | 14 | 1 |
| scality--backbeat | application | read-only | 🟠 Remediation Required | 2 | 24 | 15 | 2 |
| scality--cloudserver | application | read-only | 🟠 Remediation Required | 1 | 16 | 9 | 4 |
| serverless--serverless | monorepo | read-only | 🟠 Remediation Required | 2 | 20 | 12 | 9 |
| Sonarr--Sonarr | monorepo | read-only | 🟠 Remediation Required | 2 | 25 | 15 | 1 |
| thingsboard--thingsboard | monorepo | read-only | 🟠 Remediation Required | 1 | 22 | 19 | 1 |
| ToolJet--ToolJet | monorepo | read-only | 🟠 Remediation Required | 1 | 26 | 15 | 1 |
| umami-software--umami | monorepo | read-only | 🟠 Remediation Required | 2 | 24 | 16 | 1 |
| webpack--webpack | application | read-only | 🟠 Remediation Required | 2 | 18 | 12 | 11 |
| zappa--Zappa | application | read-only | 🟠 Remediation Required | 2 | 25 | 12 | 4 |
| arrow-py--arrow | application | read-only | 🟡 Pilot-Ready (Safety Concerns) | 0 | 6 | 25 | 12 |
| dwyl--aws-sdk-mock | library | read-only | 🟡 Pilot-Ready (Safety Concerns) | 0 | 11 | 16 | 16 |
| Graylog2--graylog2-server | monorepo | read-only | 🟡 Pilot-Ready (Safety Concerns) | 0 | 26 | 12 | 1 |
| hapifhir--hapi-fhir | monorepo | read-only | 🟡 Pilot-Ready (Safety Concerns) | 0 | 20 | 23 | 0 |

### Individual Service Details

#### akveo--ngx-admin

- **Readiness Profile**: Not Agent-Integrable
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (3):
  - API-Q1 (Documented API Interface): This is a pure client-side Angular SPA with no server-side API. All routes in `src/app/app-routing.module.ts` and `src/a...
  - AUTH-Q1 (Machine Identity Authentication): Uses `NbDummyAuthStrategy` — a mock auth strategy that accepts any credentials with a 3-second simulated delay. Configur...
  - DATA-Q1 (Sensitive Data Classification): Mock data with PII-like fields (firstName, lastName, email, username, age) hardcoded in `src/app/@core/mock/smart-table....
- **RISKs** (17):
  - RISK-SAFETY (8): AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q5, DATA-Q2, DATA-Q6
  - RISK-QUALITY (9): API-Q2, API-Q3, HITL-Q3, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3
- **Key Recommendations**:
  - [API-Q1] Build a companion backend API service with documented REST/GraphQL endpoints as the agent integration target.
  - [AUTH-Q1] Replace NbDummyAuthStrategy with a production identity provider (AWS Cognito, Auth0) supporting machine identity.
  - [DATA-Q1] Classify all data fields by sensitivity level. Tag PII fields. Implement field-level access controls in the backend.

#### coreui--coreui-free-angular-admin-template

- **Readiness Profile**: Not Agent-Integrable
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (3):
  - API-Q1 (Documented API Interface): No API interface exists. The repository is a pure frontend Angular SPA template with client-side routing only. No REST e...
  - AUTH-Q1 (Machine Identity Authentication): No authentication mechanism exists. Login/register pages are visual-only templates with empty component classes. No guar...
  - DATA-Q1 (Sensitive Data Classification): No data classification system exists. The template contains only hardcoded mock data: fictional user names, sample payme...
- **RISKs** (18):
  - RISK-SAFETY (8): AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q5, DATA-Q2, DATA-Q6
  - RISK-QUALITY (10): API-Q2, API-Q3, AUTH-Q5, HITL-Q3, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3
- **Key Recommendations**:
  - [API-Q1] Implement a backend API (REST or GraphQL) exposing the data and operations currently hardcoded in the frontend.
  - [AUTH-Q1] Implement managed identity provider (Cognito, Auth0) with OAuth 2.0 client credentials flow.
  - [DATA-Q1] Establish data classification policy (public/internal/confidential/restricted) and tag all data fields when implementing backend data stores.

#### greenshot--greenshot

- **Readiness Profile**: Not Agent-Integrable
- **Repo Type**: monorepo
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (3):
  - API-Q1 (Documented API Interface): Greenshot is a Windows desktop GUI application with no programmatic API surface. Interaction is via system tray, hotkeys...
  - AUTH-Q1 (Machine Identity Authentication): No machine identity authentication for inbound calls. OAuth2 is outbound-only for cloud service plugins.
  - DATA-Q1 (Sensitive Data Classification): No data classification. Screenshots may contain any sensitive data. No tagging, no access controls.
- **RISKs** (26):
  - RISK-SAFETY (9): AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q4, STATE-Q5, DATA-Q2, DATA-Q6
  - RISK-QUALITY (17): API-Q2, API-Q3, API-Q6, AUTH-Q5, STATE-Q2, HITL-Q3, DATA-Q3, DATA-Q4, DATA-Q5, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4, ENG-Q5
- **Key Recommendations**:
  - [API-Q1] Build a local REST or gRPC API exposing core screenshot/annotation operations.
  - [AUTH-Q1] Implement API key or OAuth2 client credentials for inbound agent calls.
  - [DATA-Q1] Implement metadata tagging for screenshot sensitivity.

#### gulpjs--gulp

- **Readiness Profile**: Not Agent-Integrable
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (3):
  - API-Q1 (Documented API Interface): gulp exposes a programmatic Node.js API via CommonJS (`index.js`) and ESM (`index.mjs`) module exports, providing `src()...
  - AUTH-Q1 (Machine Identity Authentication): gulp has no authentication mechanism. The library is imported in-process via `require('gulp')` or ESM import. There is n...
  - DATA-Q1 (Sensitive Data Classification): gulp does not classify, tag, or protect sensitive data. It reads and writes files as specified by the user's gulpfile — ...
- **RISKs** (20):
  - RISK-SAFETY (8): AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q5, DATA-Q2, DATA-Q6
  - RISK-QUALITY (12): API-Q2, API-Q3, API-Q6, AUTH-Q5, HITL-Q3, DATA-Q3, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3
- **Key Recommendations**:
  - [API-Q1] Create a thin HTTP wrapper service that exposes gulp's functionality via REST endpoints if agent integration is required.
  - [AUTH-Q1] Implement machine identity authentication (OAuth2 client credentials or API keys) in any service wrapper.
  - [DATA-Q1] Implement data classification and path-based access controls in any service wrapper.

#### iterative--dvc

- **Readiness Profile**: Not Agent-Integrable
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (3):
  - API-Q1 (Documented API Interface): DVC exposes a Python programmatic API (`dvc.api` module: `open`, `read`, `get_url`, `metrics_show`, `params_show`, `exp_...
  - AUTH-Q1 (Machine Identity Authentication): DVC does not implement authentication. Auth is delegated to remote storage providers (S3 IAM, GCS service accounts, Azur...
  - DATA-Q1 (Sensitive Data Classification): DVC manages arbitrary data files without data classification or sensitivity tagging. `.dvc` files contain hash checksums...
- **RISKs** (27):
  - RISK-SAFETY (9): AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q4, STATE-Q5, DATA-Q2, DATA-Q6
  - RISK-QUALITY (18): API-Q2, API-Q3, API-Q6, AUTH-Q4, AUTH-Q5, STATE-Q2, HITL-Q3, DATA-Q3, DATA-Q4, DATA-Q5, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4, ENG-Q5
- **Key Recommendations**:
  - [API-Q1] Build an HTTP API wrapper around `dvc.api` with OpenAPI specification.
  - [AUTH-Q1] Implement OAuth2 client credentials or API key authentication on the API wrapper service.
  - [DATA-Q1] Inventory and classify all DVC-tracked datasets. Implement classification-aware access controls in the API wrapper.

#### motdotla--node-lambda

- **Readiness Profile**: Not Agent-Integrable
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (3):
  - API-Q1 (Documented API Interface): The application is a CLI tool built with `commander.js`. It exposes four CLI commands (`setup`, `run`, `package`, `deplo...
  - AUTH-Q1 (Machine Identity Authentication): Uses human-style AWS credentials (access key/secret key, profile, session token) via CLI args and env vars. No OAuth2 cl...
  - DATA-Q1 (Sensitive Data Classification): Handles AWS credentials, IAM role ARNs, KMS key ARNs, VPC IDs, and deployment secrets (`deploy.env`). No field-level cla...
- **RISKs** (20):
  - RISK-SAFETY (9): AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q4, STATE-Q5, DATA-Q2, DATA-Q6
  - RISK-QUALITY (11): API-Q2, API-Q3, API-Q6, AUTH-Q5, HITL-Q3, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3
- **Key Recommendations**:
  - [API-Q1] Build a REST API wrapper around core Lambda class methods or create a well-documented programmatic SDK with typed interfaces.
  - [AUTH-Q1] Add IAM role assumption with session name tagging for agent identity attribution.
  - [DATA-Q1] Classify credential fields as sensitive; implement masking; integrate with Secrets Manager.

#### realworld-apps--angular-realworld-example-app

- **Readiness Profile**: Not Agent-Integrable
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (3):
  - API-Q1 (Documented API Interface): This Angular SPA exposes no programmatic API. It is a browser-based frontend that consumes an external REST API at `http...
  - AUTH-Q1 (Machine Identity Authentication): Only user-based JWT authentication via email/password login. JWT stored in localStorage, attached as `Authorization: Tok...
  - DATA-Q1 (Sensitive Data Classification): `User` model has `email` (PII) and `token` (credential). No data classification tags, no field-level encryption, no acce...
- **RISKs** (20):
  - RISK-SAFETY (9): AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q4, STATE-Q5, DATA-Q2, DATA-Q6
  - RISK-QUALITY (11): API-Q2, API-Q3, AUTH-Q5, HITL-Q3, DATA-Q3, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3
- **Key Recommendations**:
  - [API-Q1] Redirect agent integration to the backend API. If this frontend must be agent-accessible, implement a BFF layer.
  - [AUTH-Q1] Target the backend API directly for agent auth. Implement OAuth 2.0 client credentials if a BFF is added.
  - [DATA-Q1] Document data classification taxonomy. Apply at backend API level.

#### tqdm--tqdm

- **Readiness Profile**: Not Agent-Integrable
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (3):
  - API-Q1 (Documented API Interface): tqdm provides a Python API (classes/functions) and a CLI, but no REST/GraphQL/AsyncAPI network interface. The Python API...
  - AUTH-Q1 (Machine Identity Authentication): tqdm is a local Python library with no authentication mechanism. No service account, OAuth 2.0 client credentials flow, ...
  - DATA-Q1 (Sensitive Data Classification): No data classification framework exists. tqdm does not inherently handle sensitive data, but user-provided `desc`/`postf...
- **RISKs** (17):
  - RISK-SAFETY (8): AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q5, DATA-Q2, DATA-Q6
  - RISK-QUALITY (9): API-Q2, API-Q3, HITL-Q3, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3
- **Key Recommendations**:
  - [API-Q1] Wrap tqdm in a service or use as a Python import within the agent runtime.
  - [AUTH-Q1] Implement machine identity authentication at the agent platform or service wrapper layer.
  - [DATA-Q1] Document data handling policy for contrib modules; consider optional PII scrubbing.

#### Alluxio--alluxio

- **Readiness Profile**: Remediation Required
- **Repo Type**: monorepo
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (2):
  - AUTH-Q1 (Machine Identity Authentication): See BLOCKERs section above.
  - DATA-Q1 (Sensitive Data Classification): See BLOCKERs section above.
- **RISKs** (22):
  - RISK-SAFETY (9): AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q4, STATE-Q5, DATA-Q2, DATA-Q6
  - RISK-QUALITY (13): API-Q2, API-Q3, STATE-Q2, HITL-Q3, DATA-Q3, DATA-Q5, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4
- **Key Recommendations**:
  - [AUTH-Q1] Implement CUSTOM auth provider for agent credentials.
  - [DATA-Q1] Implement path-level classification.
  - [AUTH-Q2] Create a dedicated Alluxio user per agent identity with POSIX permissions restricted to only the mount paths the agent needs. Use Alluxio's extended A...

#### FlowiseAI--Flowise

- **Readiness Profile**: Remediation Required
- **Repo Type**: monorepo
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (1):
  - DATA-Q1 (Sensitive Data Classification): The Flowise database contains PII and sensitive data without field-level classification or tagging. The `Lead` entity (`...
- **RISKs** (21):
  - RISK-SAFETY (5): AUTH-Q6, STATE-Q1, STATE-Q4, DATA-Q2, DATA-Q6
  - RISK-QUALITY (16): API-Q2, API-Q3, AUTH-Q4, AUTH-Q5, HITL-Q3, DATA-Q3, DATA-Q4, DATA-Q5, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4, ENG-Q5
- **Key Recommendations**:
  - [DATA-Q1] Create a data classification inventory mapping each entity field to a sensitivity level (PUBLIC, INTERNAL, CONFIDENTIAL, PII). Implement field-level a...
  - [AUTH-Q6] Implement audit logging middleware recording the authenticated principal for every API operation, with logs shipped to immutable storage.
  - [STATE-Q1] Wrap multi-step write operations in TypeORM transactions.

#### Lidarr--Lidarr

- **Readiness Profile**: Remediation Required
- **Repo Type**: monorepo
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (2):
  - AUTH-Q1 (Machine Identity Authentication): Single shared API key with no principal attribution. Claim is `ApiKey=true` only.
  - DATA-Q1 (Sensitive Data Classification): User credentials, API keys, and service credentials stored without classification or field-level access controls.
- **RISKs** (22):
  - RISK-SAFETY (8): AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q4, STATE-Q5, DATA-Q6
  - RISK-QUALITY (14): API-Q3, API-Q6, AUTH-Q4, AUTH-Q5, HITL-Q3, DATA-Q5, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4, ENG-Q5
- **Key Recommendations**:
  - [AUTH-Q1] Implement multi-key auth with named principals.
  - [DATA-Q1] Create data classification inventory; implement field-level filtering.
  - [AUTH-Q2] Implement role-based API key scoping — at minimum, a read-only role that restricts access to GET endpoints only.
- **Depended On By**: Prowlarr--Prowlarr, Radarr--Radarr

#### Netflix--eureka

- **Readiness Profile**: Remediation Required
- **Repo Type**: monorepo
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (2):
  - AUTH-Q1 (Machine Identity Authentication): Header-based client identification only (DiscoveryIdentity-Name). No credential verification, no OAuth2, no mTLS.
  - DATA-Q1 (Sensitive Data Classification): Eureka stores service instance metadata: hostnames, IP addresses, ports, VIP addresses, health check URLs, AWS metadata ...
- **RISKs** (25):
  - RISK-SAFETY (9): AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q4, STATE-Q5, DATA-Q2, DATA-Q6
  - RISK-QUALITY (16): API-Q2, API-Q3, API-Q6, AUTH-Q4, AUTH-Q5, HITL-Q3, DATA-Q3, DATA-Q4, DATA-Q5, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4
- **Key Recommendations**:
  - [AUTH-Q1] Deploy behind API Gateway with OAuth2 client credentials or API key authentication.
  - [DATA-Q1] Classify infrastructure metadata fields and document sensitivity levels. While Eureka primarily stores operational infrastructure metadata (not PII/PH...
  - [AUTH-Q2] Implement API Gateway method-level authorization: agent identities should only have access to GET /apps, GET /apps/{appId}, GET /apps/{appId}/{instanc...

#### OpenAPITools--openapi-generator

- **Readiness Profile**: Remediation Required
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (2):
  - AUTH-Q1 (Machine Identity Authentication): Zero authentication. No Spring Security, no OAuth2, no API keys, no mTLS. CORS allows all origins. All endpoints complet...
  - DATA-Q1 (Sensitive Data Classification): `GeneratorInput.java` accepts `AuthorizationValue` containing API keys/tokens/credentials. No data classification, no fi...
- **RISKs** (19):
  - RISK-SAFETY (9): AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q4, STATE-Q5, DATA-Q2, DATA-Q6
  - RISK-QUALITY (10): API-Q2, API-Q3, API-Q6, HITL-Q3, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3
- **Key Recommendations**:
  - [AUTH-Q1] Add Spring Security with API key authentication as minimum viable control.
  - [DATA-Q1] Classify `AuthorizationValue` as SENSITIVE/CREDENTIAL. Prevent credential echo in responses. Add log redaction.
  - [AUTH-Q2] After implementing AUTH-Q1, define role-based access where agent identities can be scoped to specific endpoint groups (read-only vs. code-generation).

#### Prowlarr--Prowlarr

- **Readiness Profile**: Remediation Required
- **Repo Type**: monorepo
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (2):
  - AUTH-Q1 (Machine Identity Authentication): Single shared API key per instance. No per-agent identity. Claim is only `ApiKey=true`.
  - DATA-Q1 (Sensitive Data Classification): Sensitive credentials stored unclassified in database Settings columns. No field-level encryption or classification.
- **RISKs** (27):
  - RISK-SAFETY (9): AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q4, STATE-Q5, DATA-Q2, DATA-Q6
  - RISK-QUALITY (18): API-Q2, API-Q3, API-Q6, AUTH-Q4, AUTH-Q5, STATE-Q2, HITL-Q3, DATA-Q3, DATA-Q4, DATA-Q5, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4, ENG-Q5
- **Key Recommendations**:
  - [AUTH-Q1] Implement multi-key support with named principals.
  - [DATA-Q1] Classify sensitive fields. Implement field-level encryption.
  - [AUTH-Q2] Introduce role-based API keys (e.g., `read-only`, `read-write`, `admin`) with method-level enforcement in the authorization pipeline.
- **Depends On**: Sonarr--Sonarr, Radarr--Radarr, Lidarr--Lidarr

#### Radarr--Radarr

- **Readiness Profile**: Remediation Required
- **Repo Type**: monorepo
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (2):
  - AUTH-Q1 (Machine Identity Authentication): Single shared API key via `X-Api-Key` header or `apikey` query parameter. No per-principal attribution. Generic `ClaimsI...
  - DATA-Q1 (Sensitive Data Classification): User credentials, API keys, download client passwords, indexer tokens, notification tokens stored without field-level cl...
- **RISKs** (26):
  - RISK-SAFETY (8): AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7, STATE-Q4, STATE-Q5, DATA-Q2, DATA-Q6
  - RISK-QUALITY (18): API-Q2, API-Q3, API-Q6, AUTH-Q4, AUTH-Q5, STATE-Q2, HITL-Q3, DATA-Q3, DATA-Q4, DATA-Q5, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4, ENG-Q5
- **Key Recommendations**:
  - [AUTH-Q1] Implement multiple named API keys.
  - [DATA-Q1] Classify and redact sensitive fields from API responses.
  - [AUTH-Q2] Implement role-based API key support — at minimum distinguish "read-only" and "admin" roles.
- **Depends On**: Sonarr--Sonarr, Lidarr--Lidarr
- **Depended On By**: Prowlarr--Prowlarr

#### Sonarr--Sonarr

- **Readiness Profile**: Remediation Required
- **Repo Type**: monorepo
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (2):
  - AUTH-Q1 (Machine Identity Authentication): Single shared API key via `X-Api-Key` header. No per-principal attribution. All API key users get identical claim (`ApiK...
  - DATA-Q1 (Sensitive Data Classification): Sensitive data (credentials, API keys, tokens) stored without field-level classification. No tagging system. `CleanseLog...
- **RISKs** (25):
  - RISK-SAFETY (9): AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q4, STATE-Q5, DATA-Q2, DATA-Q6
  - RISK-QUALITY (16): API-Q3, API-Q6, AUTH-Q4, AUTH-Q5, HITL-Q3, DATA-Q3, DATA-Q4, DATA-Q5, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4, ENG-Q5
- **Key Recommendations**:
  - [AUTH-Q1] Implement multi-key registry with named principals.
  - [DATA-Q1] Implement field-level classification attributes and response-level redaction for agent API keys.
  - [AUTH-Q2] Implement role-based API key scoping — at minimum, distinguish between "read-only" and "admin" API key tiers. This can be achieved by extending `ApiKe...
- **Depended On By**: Prowlarr--Prowlarr, Radarr--Radarr

#### ToolJet--ToolJet

- **Readiness Profile**: Remediation Required
- **Repo Type**: monorepo
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (1):
  - DATA-Q1 (Sensitive Data Classification): Extensive PII stored. Application-level encryption for credentials. No field-level classification.
- **RISKs** (26):
  - RISK-SAFETY (9): AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q4, STATE-Q5, DATA-Q2, DATA-Q6
  - RISK-QUALITY (17): API-Q2, API-Q3, API-Q6, AUTH-Q4, AUTH-Q5, STATE-Q2, HITL-Q3, DATA-Q3, DATA-Q4, DATA-Q5, DISC-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4, ENG-Q5
- **Key Recommendations**:
  - [DATA-Q1] Implement field-level data classification.
  - [AUTH-Q2] Define an agent-specific CASL role with least-privilege permissions (read-only access to app metadata, no access to user PII or credential data).
  - [AUTH-Q3] Extend the existing CASL framework to define agent-specific ability sets with explicit action allowlists.

#### apache--druid

- **Readiness Profile**: Remediation Required
- **Repo Type**: monorepo
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (1):
  - DATA-Q1 (Sensitive Data Classification): No data classification tags, field-level encryption, or PII detection tooling. Druid stores arbitrary user-provided data...
- **RISKs** (25):
  - RISK-SAFETY (7): AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q4, STATE-Q5, DATA-Q2, DATA-Q6
  - RISK-QUALITY (18): API-Q2, API-Q3, API-Q6, AUTH-Q4, AUTH-Q5, STATE-Q2, HITL-Q3, DATA-Q3, DATA-Q4, DATA-Q5, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4, ENG-Q5
- **Key Recommendations**:
  - [DATA-Q1] Audit datasources for PII. Implement field-level classification and access controls using VIEWs.
  - [AUTH-Q6] Enable request logging (`druid.request.logging.type=slf4j` or `emitter`), route audit entries to an immutable store. Configure the emitter to send aud...
  - [AUTH-Q7] Configure cache notification push for immediate credential propagation. Document a runbook for agent identity revocation that includes both Druid user...

#### apache--flink-connector-aws

- **Readiness Profile**: Remediation Required
- **Repo Type**: monorepo
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (2):
  - API-Q1 (Documented API Interface): The connectors expose programmatic Java APIs (builder patterns: `KinesisStreamsSinkBuilder`, `DynamoDbSinkBuilder`, `Sqs...
  - DATA-Q1 (Sensitive Data Classification): No data classification, field-level encryption, or PII detection. Connectors pass data through (serialize/deserialize) w...
- **RISKs** (13):
  - RISK-SAFETY (5): AUTH-Q2, AUTH-Q3, AUTH-Q6, STATE-Q1, DATA-Q2
  - RISK-QUALITY (8): API-Q2, API-Q3, HITL-Q3, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q2, ENG-Q4
- **Key Recommendations**:
  - [API-Q1] Build a REST/MCP wrapper around the connector libraries to expose agent-consumable endpoints.
  - [DATA-Q1] Document data classification requirements. Provide hooks for data classification.
  - [AUTH-Q2] Document IAM policy templates for common connector use cases (e.g., Kinesis read-only, DynamoDB write-only) to guide consumers in configuring least-pr...

#### conductor-oss--conductor

- **Readiness Profile**: Remediation Required
- **Repo Type**: monorepo
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (2):
  - AUTH-Q1 (Machine Identity Authentication): No authentication exists. REST API is open/unauthenticated by default. No Spring Security, OAuth2, JWT, API key, or mTLS...
  - DATA-Q1 (Sensitive Data Classification): No data classification. Workflow/task payloads are arbitrary JSON that may contain sensitive data. `maskedFields` in Wor...
- **RISKs** (24):
  - RISK-SAFETY (8): AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7, STATE-Q4, STATE-Q5, DATA-Q2, DATA-Q6
  - RISK-QUALITY (16): API-Q2, API-Q3, AUTH-Q4, AUTH-Q5, HITL-Q3, DATA-Q3, DATA-Q4, DATA-Q5, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4, ENG-Q5
- **Key Recommendations**:
  - [AUTH-Q1] Add `spring-boot-starter-security` with OAuth2 resource server or API key authentication.
  - [DATA-Q1] Audit workflows for sensitive data. Enforce `maskedFields`. Implement classification framework.
  - [AUTH-Q2] Implement RBAC with predefined roles (e.g., `workflow-reader`, `workflow-admin`, `task-worker`) using Spring Security method-level annotations (`@PreA...

#### getlift--lift

- **Readiness Profile**: Remediation Required
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (2):
  - API-Q1 (Documented API Interface): The plugin does not expose a REST, GraphQL, or AsyncAPI interface. Its interface is a Serverless Framework plugin config...
  - DATA-Q1 (Sensitive Data Classification): No data classification tags on generated resources. Storage construct has encryption (S3_MANAGED or KMS_MANAGED) and `Bl...
- **RISKs** (14):
  - RISK-SAFETY (7): AUTH-Q2, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q5, DATA-Q2, DATA-Q6
  - RISK-QUALITY (7): API-Q2, AUTH-Q5, HITL-Q3, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q2
- **Key Recommendations**:
  - [API-Q1] Define a wrapper API or MCP server that exposes the plugin's capabilities as callable endpoints with documented input/output schemas.
  - [DATA-Q1] Add `classification` configuration option and propagate as AWS resource tags.
  - [AUTH-Q2] Implement per-function permission scoping. Allow constructs to declare which functions should receive their permissions (e.g., `permissions: [myFuncti...

#### getsentry--sentry-python

- **Readiness Profile**: Remediation Required
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (2):
  - API-Q1 (Documented API Interface): The SDK exposes a Python programmatic API via `sentry_sdk/api.py` and `sentry_sdk/__init__.py` with functions like `init...
  - DATA-Q1 (Sensitive Data Classification): EventScrubber with DEFAULT_DENYLIST (31 fields) and DEFAULT_PII_DENYLIST (4 fields). send_default_pii option. Pattern-ba...
- **RISKs** (17):
  - RISK-SAFETY (9): AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q4, STATE-Q5, DATA-Q2, DATA-Q6
  - RISK-QUALITY (8): API-Q2, API-Q3, HITL-Q3, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q2, ENG-Q4
- **Key Recommendations**:
  - [API-Q1] Build a thin REST or MCP wrapper service exposing the SDK's public API.
  - [DATA-Q1] Extend denylist; implement field-level classification.
  - [AUTH-Q2] Create dedicated Sentry DSN keys for agent identities with restricted project-level scopes via Sentry's platform settings.

#### openzipkin--zipkin

- **Readiness Profile**: Remediation Required
- **Repo Type**: monorepo
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (2):
  - AUTH-Q1 (Machine Identity Authentication): No authentication mechanism. Server accepts all requests without identity verification. TLS supported but is transport e...
  - DATA-Q1 (Sensitive Data Classification): No data classification. Span tags may contain PII. No field-level encryption. No PII detection tools.
- **RISKs** (24):
  - RISK-SAFETY (9): AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q4, STATE-Q5, DATA-Q2, DATA-Q6
  - RISK-QUALITY (15): API-Q2, API-Q3, STATE-Q2, HITL-Q3, DATA-Q3, DATA-Q4, DATA-Q5, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4, ENG-Q5
- **Key Recommendations**:
  - [AUTH-Q1] Deploy API Gateway with API key or OAuth2 authentication.
  - [DATA-Q1] Audit span tags for PII. Implement field-level classification and redaction.
  - [AUTH-Q2] Implement API Gateway with method-level authorization when resolving AUTH-Q1. Define separate API keys for read-only agents vs. instrumentation client...

#### scality--backbeat

- **Readiness Profile**: Remediation Required
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (2):
  - AUTH-Q1 (Machine Identity Authentication): API authenticates via IP allowlist only. No OAuth2, API key, mTLS, or service account authentication for API callers.
  - DATA-Q1 (Sensitive Data Classification): No data classification tags, field-level encryption, or PII detection. Object metadata processed without classification.
- **RISKs** (24):
  - RISK-SAFETY (9): AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q4, STATE-Q5, DATA-Q2, DATA-Q6
  - RISK-QUALITY (15): API-Q2, API-Q3, AUTH-Q4, AUTH-Q5, HITL-Q3, DATA-Q3, DATA-Q5, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4, ENG-Q5
- **Key Recommendations**:
  - [AUTH-Q1] Add API key or bearer token authentication with principal attribution.
  - [DATA-Q1] Classify data fields. Implement field-level access controls.
  - [AUTH-Q2] Implement route-level authorization on the Backbeat API, allowing different agent identities to access different endpoint groups (e.g., read-only metr...
- **Depends On**: scality--cloudserver
- **Depended On By**: scality--cloudserver

#### scality--cloudserver

- **Readiness Profile**: Remediation Required
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (1):
  - DATA-Q1 (Sensitive Data Classification): KMS encryption exists but no field-level data classification.
- **RISKs** (16):
  - RISK-SAFETY (6): AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q4, DATA-Q2, DATA-Q6
  - RISK-QUALITY (10): API-Q2, API-Q6, AUTH-Q4, AUTH-Q5, DATA-Q4, DISC-Q1, OBS-Q1, ENG-Q1, ENG-Q2, ENG-Q3
- **Key Recommendations**:
  - [DATA-Q1] Implement object tagging for data classification.
  - [AUTH-Q6] Integrate log shipping to an immutable store (S3 with Object Lock or CloudWatch Logs with mandatory retention). Add log integrity verification (file c...
  - [AUTH-Q7] When deploying with agent identities, use the external Vault service (not in-memory) and ensure Vault's account disable/key revocation APIs are access...
- **Depends On**: scality--backbeat
- **Depended On By**: scality--backbeat

#### serverless--serverless

- **Readiness Profile**: Remediation Required
- **Repo Type**: monorepo
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (2):
  - AUTH-Q1 (Machine Identity Authentication): The MCP SSE server (`packages/mcp/src/server.js`) has **no authentication mechanism**. The Express server exposes `/sse`...
  - DATA-Q1 (Sensitive Data Classification): The MCP `aws-lambda-info` tool returns Lambda function configuration including **environment variables**, which commonly...
- **RISKs** (20):
  - RISK-SAFETY (9): AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q4, STATE-Q5, DATA-Q2, DATA-Q6
  - RISK-QUALITY (11): API-Q3, API-Q6, HITL-Q3, DATA-Q3, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4
- **Key Recommendations**:
  - [AUTH-Q1] Add API key or bearer token authentication middleware to the Express SSE server. Validate an `Authorization` header before establishing SSE connection...
  - [DATA-Q1] Apply the existing `obfuscateSensitiveData` function (or a similar redaction layer) to MCP tool responses before returning them to agents. At minimum,...
  - [AUTH-Q2] Implement tool-level access control lists (ACLs) in the MCP server, configurable per API key or identity.

#### thingsboard--thingsboard

- **Readiness Profile**: Remediation Required
- **Repo Type**: monorepo
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (1):
  - DATA-Q1 (Sensitive Data Classification): See BLOCKERs section above (DATA-Q1).
- **RISKs** (22):
  - RISK-SAFETY (6): AUTH-Q2, AUTH-Q6, STATE-Q1, STATE-Q4, DATA-Q2, DATA-Q6
  - RISK-QUALITY (16): API-Q2, API-Q6, AUTH-Q4, AUTH-Q5, STATE-Q2, HITL-Q3, DATA-Q4, DATA-Q5, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4, ENG-Q5
- **Key Recommendations**:
  - [DATA-Q1] Create data classification inventory.
  - [AUTH-Q2] Introduce custom role definitions with granular permission sets per resource type and operation. Allow API keys to be scoped to specific resources and...
  - [AUTH-Q6] Enable the Elasticsearch audit log sink and configure write-once indices. Alternatively, forward audit logs to an immutable log storage service (e.g.,...

#### umami-software--umami

- **Readiness Profile**: Remediation Required
- **Repo Type**: monorepo
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (2):
  - AUTH-Q1 (Machine Identity Authentication): Username/password login only. No OAuth2 client credentials, no API keys, no service accounts, no mTLS. Agent cannot be a...
  - DATA-Q1 (Sensitive Data Classification): No data classification tags, no field-level encryption, no PII detection tooling. Session data (country, region, city, b...
- **RISKs** (24):
  - RISK-SAFETY (9): AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q4, STATE-Q5, DATA-Q2, DATA-Q6
  - RISK-QUALITY (15): API-Q2, API-Q3, API-Q6, HITL-Q3, DATA-Q3, DATA-Q4, DATA-Q5, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4, ENG-Q5
- **Key Recommendations**:
  - [AUTH-Q1] Implement API key authentication with principal attribution.
  - [DATA-Q1] Create data classification document. Implement field-level access controls.
  - [AUTH-Q2] Extend the permission model to support resource-level scoping — allow API keys or service accounts to be bound to specific website IDs, with configura...

#### webpack--webpack

- **Readiness Profile**: Remediation Required
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (2):
  - AUTH-Q1 (Machine Identity Authentication): No machine identity authentication. No OAuth, API keys, mTLS, or service accounts. Runs under OS process permissions.
  - DATA-Q1 (Sensitive Data Classification): No sensitive data classification. webpack processes source code, `.env` files (via `DotenvPlugin`), and environment vari...
- **RISKs** (18):
  - RISK-SAFETY (9): AUTH-Q2, AUTH-Q3, AUTH-Q5, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q5, DATA-Q2, DATA-Q6
  - RISK-QUALITY (9): API-Q2, API-Q3, HITL-Q3, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3
- **Key Recommendations**:
  - [AUTH-Q1] Wrap in authenticated build service.
  - [DATA-Q1] Implement pre-build sensitive data scanning.
  - [AUTH-Q2] Wrap webpack in a build service that enforces agent-specific permission policies (allowed plugins, allowed output paths, allowed input paths).

#### zappa--Zappa

- **Readiness Profile**: Remediation Required
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (2):
  - API-Q1 (Documented API Interface): Zappa does not expose a network-accessible API. It is a CLI/library tool. Users interact via `zappa deploy`, `zappa upda...
  - DATA-Q1 (Sensitive Data Classification): No data classification for AWS credentials, secrets in environment variables, or deployment artifacts.
- **RISKs** (25):
  - RISK-SAFETY (9): AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q4, STATE-Q5, DATA-Q2, DATA-Q6
  - RISK-QUALITY (16): API-Q2, API-Q3, AUTH-Q1, AUTH-Q4, AUTH-Q5, STATE-Q2, HITL-Q3, DATA-Q5, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4, ENG-Q5
- **Key Recommendations**:
  - [API-Q1] Create a REST API wrapper around core Zappa operations with OpenAPI spec.
  - [DATA-Q1] Classify data types and tag sensitive fields.
  - [AUTH-Q2] Replace wildcard policies with resource-scoped policies. Document a least-privilege policy template for agent use cases.

#### Graylog2--graylog2-server

- **Readiness Profile**: Pilot-Ready (Safety Concerns)
- **Repo Type**: monorepo
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (0):
  - None
- **RISKs** (26):
  - RISK-SAFETY (7): AUTH-Q2, AUTH-Q6, STATE-Q1, STATE-Q4, STATE-Q5, DATA-Q2, DATA-Q6
  - RISK-QUALITY (19): API-Q2, API-Q3, API-Q6, AUTH-Q4, AUTH-Q5, STATE-Q2, HITL-Q3, DATA-Q1, DATA-Q3, DATA-Q4, DATA-Q5, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4, ENG-Q5
- **Key Recommendations**:
  - [AUTH-Q2] Create a dedicated "Agent Reader" built-in role with minimal read-only permissions. Document agent identity setup in deployment guides.
  - [AUTH-Q6] Configure a dedicated Graylog output to forward audit events to an immutable storage backend. Enable MongoDB audit logging with write-once storage.
  - [STATE-Q1] Implement content pack versioning with rollback capability for multi-resource operations.

#### arrow-py--arrow

- **Readiness Profile**: Pilot-Ready (Safety Concerns)
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (0):
  - None
- **RISKs** (6):
  - RISK-SAFETY (3): AUTH-Q6, STATE-Q1, DATA-Q2
  - RISK-QUALITY (3): API-Q2, DISC-Q1, ENG-Q2
- **Key Recommendations**:
  - [AUTH-Q6] Implement audit logging in the agent tool wrapper, not in the library itself. Log agent identity, operation, parameters, and result for every Arrow to...
  - [STATE-Q1] No action required within Arrow. Consuming applications that embed Arrow in multi-step agent workflows should implement saga patterns or compensation ...
  - [DATA-Q2] No action required within Arrow. Consuming applications should ensure data residency compliance at the application layer, particularly when Arrow date...

#### dwyl--aws-sdk-mock

- **Readiness Profile**: Pilot-Ready (Safety Concerns)
- **Repo Type**: library
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (0):
  - None
- **RISKs** (11):
  - RISK-SAFETY (5): AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7, STATE-Q5
  - RISK-QUALITY (6): API-Q2, API-Q3, HITL-Q3, DISC-Q1, OBS-Q1, OBS-Q2
- **Key Recommendations**:
  - [AUTH-Q2] Build a thin wrapper around `aws-sdk-mock` that restricts which services and methods a given agent identity is permitted to mock. Enforce at the integ...
  - [AUTH-Q3] Create a typed wrapper that restricts the `service` and `method` parameters to an approved allowlist for each agent identity.
  - [AUTH-Q6] Add optional structured logging (e.g., a configurable logger callback) to the library that emits audit events for `mock()`, `remock()`, and `restore()...

#### hapifhir--hapi-fhir

- **Readiness Profile**: Pilot-Ready (Safety Concerns)
- **Repo Type**: monorepo
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (0):
  - None
- **RISKs** (20):
  - RISK-SAFETY (8): AUTH-Q2, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q4, STATE-Q5, DATA-Q2, DATA-Q6
  - RISK-QUALITY (12): API-Q2, API-Q3, API-Q6, HITL-Q3, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4, ENG-Q5
- **Key Recommendations**:
  - [AUTH-Q2] Document a reference `AuthorizationInterceptor` configuration for agent identities with read-only access scoped to specific resource types.
  - [AUTH-Q6] Deploy BalpAuditCaptureInterceptor with an `IBalpAuditEventSink` implementation that writes to immutable storage. Document the audit architecture for ...
  - [AUTH-Q7] Implement an identity deny-list interceptor that can be updated at runtime without redeployment. Integrate with the deployer's identity provider for r...


## Assessment Inventory

| # | Service | Report File | Assessment Date | Repo Type | Agent Scope |
|---|---------|-------------|-----------------|-----------|-------------|
| 1 | akveo--ngx-admin | services/akveo--ngx-admin/agentic-readiness-assessment/akveo--ngx-admin-ara-report.md | 2026-04-29 | application | read-only |
| 2 | Alluxio--alluxio | services/Alluxio--alluxio/agentic-readiness-assessment/Alluxio--alluxio-ara-report.md | 2026-04-29 | monorepo | read-only |
| 3 | apache--druid | services/apache--druid/agentic-readiness-assessment/apache--druid-ara-report.md | 2026-04-29 | monorepo | read-only |
| 4 | apache--flink-connector-aws | services/apache--flink-connector-aws/agentic-readiness-assessment/apache--flink-connector-aws-ara-report.md | 2026-04-29 | monorepo | read-only |
| 5 | arrow-py--arrow | services/arrow-py--arrow/agentic-readiness-assessment/arrow-py--arrow-ara-report.md | 2026-04-29 | application | read-only |
| 6 | conductor-oss--conductor | services/conductor-oss--conductor/agentic-readiness-assessment/conductor-oss--conductor-ara-report.md | 2026-04-29 | monorepo | read-only |
| 7 | coreui--coreui-free-angular-admin-template | services/coreui--coreui-free-angular-admin-template/agentic-readiness-assessment/coreui--coreui-free-angular-admin-template-ara-report.md | 2026-04-29 | application | read-only |
| 8 | dwyl--aws-sdk-mock | services/dwyl--aws-sdk-mock/agentic-readiness-assessment/dwyl--aws-sdk-mock-ara-report.md | 2026-04-29 | library | read-only |
| 9 | FlowiseAI--Flowise | services/FlowiseAI--Flowise/agentic-readiness-assessment/FlowiseAI--Flowise-ara-report.md | 2025-07-21 | monorepo | read-only |
| 10 | getlift--lift | services/getlift--lift/agentic-readiness-assessment/getlift--lift-ara-report.md | 2026-04-29 | application | read-only |
| 11 | getsentry--sentry-python | services/getsentry--sentry-python/agentic-readiness-assessment/getsentry--sentry-python-ara-report.md | 2026-04-29 | application | read-only |
| 12 | Graylog2--graylog2-server | services/Graylog2--graylog2-server/agentic-readiness-assessment/Graylog2--graylog2-server-ara-report.md | 2025-07-14 | monorepo | read-only |
| 13 | greenshot--greenshot | services/greenshot--greenshot/agentic-readiness-assessment/greenshot--greenshot-ara-report.md | 2026-04-29 | monorepo | read-only |
| 14 | gulpjs--gulp | services/gulpjs--gulp/agentic-readiness-assessment/gulpjs--gulp-ara-report.md | 2026-04-29 | application | read-only |
| 15 | hapifhir--hapi-fhir | services/hapifhir--hapi-fhir/agentic-readiness-assessment/hapifhir--hapi-fhir-ara-report.md | 2026-04-29 | monorepo | read-only |
| 16 | iterative--dvc | services/iterative--dvc/agentic-readiness-assessment/iterative--dvc-ara-report.md | 2026-04-29 | application | read-only |
| 17 | Lidarr--Lidarr | services/Lidarr--Lidarr/agentic-readiness-assessment/Lidarr--Lidarr-ara-report.md | 2025-07-17 | monorepo | read-only |
| 18 | motdotla--node-lambda | services/motdotla--node-lambda/agentic-readiness-assessment/motdotla--node-lambda-ara-report.md | 2026-04-29 | application | read-only |
| 19 | Netflix--eureka | services/Netflix--eureka/agentic-readiness-assessment/Netflix--eureka-ara-report.md | 2026-04-29 | monorepo | read-only |
| 20 | OpenAPITools--openapi-generator | services/OpenAPITools--openapi-generator/agentic-readiness-assessment/OpenAPITools--openapi-generator-ara-report.md | 2026-04-29 | application | read-only |
| 21 | openzipkin--zipkin | services/openzipkin--zipkin/agentic-readiness-assessment/openzipkin--zipkin-ara-report.md | 2026-04-29 | monorepo | read-only |
| 22 | Prowlarr--Prowlarr | services/Prowlarr--Prowlarr/agentic-readiness-assessment/Prowlarr--Prowlarr-ara-report.md | 2026-04-29 | monorepo | read-only |
| 23 | Radarr--Radarr | services/Radarr--Radarr/agentic-readiness-assessment/Radarr--Radarr-ara-report.md | 2026-04-29 | monorepo | read-only |
| 24 | realworld-apps--angular-realworld-example-app | services/realworld-apps--angular-realworld-example-app/agentic-readiness-assessment/realworld-apps--angular-realworld-example-app-ara-report.md | 2025-07-16 | application | read-only |
| 25 | scality--backbeat | services/scality--backbeat/agentic-readiness-assessment/scality--backbeat-ara-report.md | 2026-04-29 | application | read-only |
| 26 | scality--cloudserver | services/scality--cloudserver/agentic-readiness-assessment/scality--cloudserver-ara-report.md | 2026-04-29 | application | read-only |
| 27 | serverless--serverless | services/serverless--serverless/agentic-readiness-assessment/serverless--serverless-ara-report.md | 2026-04-29 | monorepo | read-only |
| 28 | Sonarr--Sonarr | services/Sonarr--Sonarr/agentic-readiness-assessment/Sonarr--Sonarr-ara-report.md | 2026-04-29 | monorepo | read-only |
| 29 | thingsboard--thingsboard | services/thingsboard--thingsboard/agentic-readiness-assessment/thingsboard--thingsboard-ara-report.md | 2026-04-29 | monorepo | read-only |
| 30 | ToolJet--ToolJet | services/ToolJet--ToolJet/agentic-readiness-assessment/ToolJet--ToolJet-ara-report.md | 2025-07-11 | monorepo | read-only |
| 31 | tqdm--tqdm | services/tqdm--tqdm/agentic-readiness-assessment/tqdm--tqdm-ara-report.md | 2026-04-29 | application | read-only |
| 32 | umami-software--umami | services/umami-software--umami/agentic-readiness-assessment/umami-software--umami-ara-report.md | 2026-04-29 | monorepo | read-only |
| 33 | webpack--webpack | services/webpack--webpack/agentic-readiness-assessment/webpack--webpack-ara-report.md | 2025-07-24 | application | read-only |
| 34 | zappa--Zappa | services/zappa--Zappa/agentic-readiness-assessment/zappa--Zappa-ara-report.md | 2026-04-29 | application | read-only |
