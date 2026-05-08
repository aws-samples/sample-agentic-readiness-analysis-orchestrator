# Portfolio Agentic Readiness Assessment Report

**Date**: 2026-05-08
**Services Assessed**: 34
**Portfolio Context**: Portfolio of 34 open-source project mirrors validating ATX TDs across Java, Python, JS/TS, C# — monolith, microservices, serverless, CLI, frontend, data platform — observability, storage, IoT, AI/LLM, analytics, healthcare.

## Executive Dashboard

### Readiness Distribution

| Profile | Services | Percentage | Description |
|---------|----------|------------|-------------|
| ✅ Agent-Ready | 15 | 44% | 0 blockers, 0 RISK-SAFETY — broad agent deployment |
| 🟡 Pilot-Ready | 0 | 0% | 0 blockers, 1–2 RISK-SAFETY — narrow pilot |
| 🟡 Pilot-Ready (Safety Concerns) | 3 | 9% | 0 blockers, 3+ RISK-SAFETY — supervised pilot, prioritize safety |
| 🟠 Remediation Required | 16 | 47% | 1–2 blockers — remediate before any agent deployment |
| ❌ Not Agent-Integrable | 0 | 0% | 3+ blockers — deferred or descoped |

### Portfolio Summary

| Metric | Value |
|--------|-------|
| Total Services Assessed | 34 |
| Services Ready for Agents (Agent-Ready + Pilot-Ready) | 15 (44%) |
| Services Requiring Remediation | 16 (47%) |
| Cross-Cutting BLOCKERs (same blocker in 2+ repos) | 2 |
| Cross-Cutting RISKs (same risk in 3+ repos) | 22 |
| Services with Write-Enabled Agent Scope | 0 (0%) |
| Services with Read-Only Agent Scope | 34 (100%) |

### Repo Type Distribution

| Repo Type | Count | Percentage |
|-----------|-------|------------|
| application | 28 | 82% |
| library | 6 | 18% |

### Blocker Heatmap by Section

| Section | Repos Blocked | % of Applicable Repos | Top Blockers |
|---------|--------------|----------------------|--------------|
| Authentication & Authorization | 16 | 52% | AUTH-Q1, AUTH-Q6 |
| API Surface | 2 | 6% | API-Q1 |
| State Management | 0 | 0% | — |
| Human-in-the-Loop | 0 | 0% | — |
| Data Accessibility | 0 | 0% | — |
| Discovery & Documentation | 0 | 0% | — |
| Observability | 0 | 0% | — |
| Engineering Maturity | 0 | 0% | — |

### Readiness Snapshot

| Metric | Value |
|--------|-------|
| assessment_date | 2026-05-08 |
| total_services | 34 |
| agent_ready | 15 |
| pilot_ready | 0 |
| pilot_ready_safety_concerns | 3 |
| remediation_required | 16 |
| not_integrable | 0 |
| total_blockers | 15 |
| total_risks | 249 |
| total_risk_safety | 95 |
| total_risk_quality | 154 |
| total_infos | 556 |
| cross_cutting_blockers | 2 |
| cross_cutting_risks | 22 |
| cross_cutting_risk_safety | 9 |
| cross_cutting_risk_quality | 13 |
| portfolio_level_blockers | 1 |
| portfolio_level_risks | 4 |
| write_enabled_services | 0 |
| read_only_services | 34 |

## Cross-Cutting BLOCKERs — Same Blocker in 2+ Repos

> These are BLOCKER-severity questions that appear in 2 or more repositories.
> They represent portfolio-wide agentic readiness gaps requiring coordinated remediation.
> Questions scored as N/A for a service do not count as gaps for that service.

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER in 15 of 27 applicable services
- **Affected Services**: Alluxio--alluxio, FlowiseAI--Flowise, Lidarr--Lidarr, Netflix--eureka, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, ToolJet--ToolJet, apache--druid, conductor-oss--conductor, openzipkin--zipkin, scality--backbeat, scality--cloudserver, thingsboard--thingsboard, umami-software--umami
- **Common Finding**: Services lack machine identity authentication suitable for agent principals. Authentication mechanisms are either absent (no auth), use shared/single API keys without principal attribution, or rely on trust-based/IP-based access control. Agents cannot be individually identified, attributed, or audited.
- **Root Cause Pattern**: No OAuth2 client credentials, per-agent API keys, or mTLS configured. Services rely on shared secrets, single API keys, or basic auth without individual machine identity.
- **Portfolio-Level Remediation**:
  - **Approach**: Hybrid — deploy a centralized identity provider (Cognito, Okta) for the portfolio, then integrate each service
  - **Immediate Action**: Deploy a shared OAuth2 authorization server (e.g., Amazon Cognito User Pool) with client credentials grant for M2M authentication
  - **Target State**: Every service authenticates agent requests via OAuth2 tokens or per-agent API keys with principal attribution in request context and audit logs
  - **Estimated Effort**: High
  - **Priority**: Critical
  - **Dependencies**: None — this is the foundation for all other AUTH controls

### API-Q1: Formal API Interface

- **Severity**: BLOCKER in 2 of 15 applicable services
- **Affected Services**: scality--backbeat, umami-software--umami
- **Common Finding**: Services expose HTTP APIs programmatically without formal, versioned documentation. Agents cannot reliably discover or bind to undocumented interfaces.
- **Root Cause Pattern**: APIs are defined in code (routes files) but no OpenAPI/Swagger specification or formal contract documentation is maintained alongside the code.
- **Portfolio-Level Remediation**:
  - **Approach**: Per-service fix — each service must create and maintain an API specification
  - **Immediate Action**: Generate OpenAPI specifications from existing route definitions for each affected service
  - **Target State**: Every service with an HTTP API has a versioned OpenAPI spec maintained in the repo, with breaking-change detection in CI
  - **Estimated Effort**: Medium
  - **Priority**: High
  - **Dependencies**: None

## Cross-Cutting RISKs

### Cross-Cutting RISK-SAFETY — Same Safety Risk in 3+ Repos

> These are RISK-SAFETY questions that appear in 3 or more repositories.
> They represent portfolio-wide agent safety gaps requiring coordinated attention.
> Questions scored as N/A for a service do not count as gaps for that service.

### AUTH-Q2: Scoped Permissions

- **Severity**: RISK-SAFETY in 19 of 29 applicable services
- **Affected Services**: Alluxio--alluxio, FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, Netflix--eureka, OpenAPITools--openapi-generator, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, ToolJet--ToolJet, apache--druid, conductor-oss--conductor, getsentry--sentry-python, hapifhir--hapi-fhir, openzipkin--zipkin, scality--backbeat, scality--cloudserver, thingsboard--thingsboard, umami-software--umami
- **Common Finding**: Services lack fine-grained, scoped permission models for agent access. Permissions are either all-or-nothing (admin-level API keys) or role-based without agent-specific scoping.
- **Compensating Controls**: Read-only agent scope limits blast radius; existing role-based access provides coarse containment
- **Portfolio-Level Recommendation**: Implement attribute-based access control (ABAC) or fine-grained IAM policies per agent identity, limiting each agent to the minimum permissions required for its task
- **Estimated Effort**: Medium

### STATE-Q5: Disaster Recovery

- **Severity**: RISK-SAFETY in 19 of 30 applicable services
- **Affected Services**: Alluxio--alluxio, FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, Netflix--eureka, OpenAPITools--openapi-generator, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, ToolJet--ToolJet, apache--druid, conductor-oss--conductor, getsentry--sentry-python, hapifhir--hapi-fhir, openzipkin--zipkin, scality--backbeat, scality--cloudserver, thingsboard--thingsboard, umami-software--umami
- **Common Finding**: No formal disaster recovery plan addresses agent-induced state corruption. Backup/restore mechanisms exist but are not designed to isolate and recover from autonomous agent actions.
- **Compensating Controls**: Read-only agent scope eliminates risk of agent-induced state corruption; existing backup mechanisms provide general recovery
- **Portfolio-Level Recommendation**: Define agent-aware DR procedures including point-in-time recovery, agent action replay logs, and isolation boundaries for agent-modified state
- **Estimated Effort**: High

### AUTH-Q7: Revocation Mechanism

- **Severity**: RISK-SAFETY in 18 of 29 applicable services
- **Affected Services**: Alluxio--alluxio, FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, Netflix--eureka, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, ToolJet--ToolJet, apache--druid, conductor-oss--conductor, getsentry--sentry-python, hapifhir--hapi-fhir, openzipkin--zipkin, scality--backbeat, scality--cloudserver, thingsboard--thingsboard, umami-software--umami
- **Common Finding**: No mechanism exists to instantly revoke a specific agent's access. API keys are shared or long-lived with no per-agent revocation capability.
- **Compensating Controls**: Read-only scope limits damage from compromised credentials; manual server restart can invalidate all sessions
- **Portfolio-Level Recommendation**: Implement short-lived OAuth2 tokens with centralized revocation list, or per-agent API key management with instant revocation capability
- **Estimated Effort**: Medium

### AUTH-Q3: Credential Rotation

- **Severity**: RISK-SAFETY in 16 of 26 applicable services
- **Affected Services**: Alluxio--alluxio, Graylog2--graylog2-server, Lidarr--Lidarr, Netflix--eureka, OpenAPITools--openapi-generator, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, ToolJet--ToolJet, conductor-oss--conductor, getsentry--sentry-python, openzipkin--zipkin, scality--backbeat, scality--cloudserver, thingsboard--thingsboard, umami-software--umami
- **Common Finding**: Credentials used for API access are static/long-lived with no automated rotation mechanism. API keys and secrets persist indefinitely.
- **Compensating Controls**: Read-only agent scope limits exposure window; network-level controls restrict access surface
- **Portfolio-Level Recommendation**: Implement automated credential rotation via AWS Secrets Manager or similar, with rotation periods ≤ 90 days for all agent credentials
- **Estimated Effort**: Medium

### AUTH-Q6: Agent Action Audit Trail

- **Severity**: RISK-SAFETY in 15 of 29 applicable services
- **Affected Services**: Alluxio--alluxio, FlowiseAI--Flowise, Lidarr--Lidarr, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, ToolJet--ToolJet, apache--druid, conductor-oss--conductor, hapifhir--hapi-fhir, openzipkin--zipkin, scality--backbeat, scality--cloudserver, thingsboard--thingsboard, umami-software--umami
- **Common Finding**: No dedicated audit trail captures agent-initiated actions with principal attribution. Logging exists but does not distinguish human from agent actions or identify which agent performed an action.
- **Compensating Controls**: Read-only scope means no state-changing actions to audit; existing application logs capture request metadata
- **Portfolio-Level Recommendation**: Instrument structured audit logging that captures agent identity, action type, target resource, and timestamp for every agent-initiated API call
- **Estimated Effort**: Medium

### DATA-Q6: Data Retention / Expiry

- **Severity**: RISK-SAFETY in 15 of 27 applicable services
- **Affected Services**: FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, ToolJet--ToolJet, apache--druid, conductor-oss--conductor, hapifhir--hapi-fhir, openzipkin--zipkin, scality--backbeat, scality--cloudserver, thingsboard--thingsboard, umami-software--umami
- **Common Finding**: Data retention and expiry policies are not enforced or not defined. Agent-accessed data may persist indefinitely without lifecycle management.
- **Compensating Controls**: Read-only agent scope prevents agent-created data accumulation; existing infrastructure provides some storage lifecycle
- **Portfolio-Level Recommendation**: Define and enforce data retention policies with automated expiry, ensuring agent-accessed data follows organizational data lifecycle requirements
- **Estimated Effort**: Medium

### STATE-Q4: State Versioning

- **Severity**: RISK-SAFETY in 6 of 14 applicable services
- **Affected Services**: Alluxio--alluxio, Sonarr--Sonarr, ToolJet--ToolJet, conductor-oss--conductor, hapifhir--hapi-fhir, scality--cloudserver
- **Common Finding**: State changes lack version tracking that would allow agent actions to be traced, audited, or rolled back to a specific version boundary.
- **Compensating Controls**: Read-only agent scope prevents state modifications; existing database transaction logs provide some recoverability
- **Portfolio-Level Recommendation**: Implement event sourcing or state versioning that captures every state mutation with the acting principal (human or agent) and enables targeted rollback
- **Estimated Effort**: High

### DATA-Q1: Data Classification & Scoping

- **Severity**: RISK-SAFETY in 6 of 22 applicable services
- **Affected Services**: Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, scality--cloudserver, thingsboard--thingsboard, umami-software--umami
- **Common Finding**: No formal data classification metadata or API response scoping exists to limit what data agents can access. Agent queries may return unfiltered data sets including sensitive information.
- **Compensating Controls**: Read-only scope prevents data exfiltration through write channels; existing role-based access provides coarse filtering
- **Portfolio-Level Recommendation**: Implement data classification labels and API response scoping to ensure agents receive only the data classification levels appropriate to their authorization
- **Estimated Effort**: High

### DATA-Q2: PII/Sensitive Data Handling

- **Severity**: RISK-SAFETY in 6 of 25 applicable services
- **Affected Services**: Lidarr--Lidarr, Netflix--eureka, ToolJet--ToolJet, apache--druid, hapifhir--hapi-fhir, scality--cloudserver
- **Common Finding**: PII and sensitive data handling lacks agent-specific controls. No automated PII detection, masking, or field-level access control exists for agent consumers.
- **Compensating Controls**: Read-only agent scope; existing application-level access controls apply uniformly
- **Portfolio-Level Recommendation**: Deploy PII detection and masking middleware for agent-facing API responses; implement field-level access control based on agent authorization level
- **Estimated Effort**: High

### Cross-Cutting RISK-QUALITY — Same Quality Risk in 3+ Repos

> These are RISK-QUALITY questions that appear in 3 or more repositories.
> They represent portfolio-wide quality patterns to address as capacity allows.
> Questions scored as N/A for a service do not count as gaps for that service.

### DISC-Q1: Service Discovery Metadata

- **Severity**: RISK-QUALITY in 21 of 29 applicable services
- **Affected Services**: Alluxio--alluxio, FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, Netflix--eureka, OpenAPITools--openapi-generator, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, ToolJet--ToolJet, apache--druid, apache--flink-connector-aws, conductor-oss--conductor, getsentry--sentry-python, hapifhir--hapi-fhir, openzipkin--zipkin, scality--backbeat, scality--cloudserver, thingsboard--thingsboard, tqdm--tqdm, umami-software--umami
- **Common Finding**: No machine-readable service discovery metadata (health endpoints, capability advertisements, or service registry entries) is exposed for agent discovery.
- **Portfolio-Level Recommendation**: Implement standardized service discovery metadata (e.g., well-known URIs, health endpoints, capability manifests) across all services
- **Estimated Effort**: Low

### OBS-Q1: Structured Logging

- **Severity**: RISK-QUALITY in 20 of 29 applicable services
- **Affected Services**: Alluxio--alluxio, FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, Netflix--eureka, OpenAPITools--openapi-generator, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, ToolJet--ToolJet, apache--druid, apache--flink-connector-aws, conductor-oss--conductor, getsentry--sentry-python, hapifhir--hapi-fhir, openzipkin--zipkin, scality--backbeat, scality--cloudserver, thingsboard--thingsboard, umami-software--umami
- **Common Finding**: Logging lacks structured format (JSON) with consistent field schemas. Logs are text-based, making programmatic analysis by agents difficult.
- **Portfolio-Level Recommendation**: Standardize on structured JSON logging across all services with consistent field schemas (timestamp, level, service, trace_id, message)
- **Estimated Effort**: Low

### OBS-Q2: Distributed Tracing

- **Severity**: RISK-QUALITY in 19 of 29 applicable services
- **Affected Services**: Alluxio--alluxio, FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, Netflix--eureka, OpenAPITools--openapi-generator, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, ToolJet--ToolJet, apache--druid, apache--flink-connector-aws, conductor-oss--conductor, hapifhir--hapi-fhir, openzipkin--zipkin, scality--backbeat, scality--cloudserver, thingsboard--thingsboard, umami-software--umami
- **Common Finding**: No distributed tracing instrumentation (OpenTelemetry, X-Ray, Zipkin). Agent actions cannot be correlated across service boundaries.
- **Portfolio-Level Recommendation**: Instrument OpenTelemetry across the portfolio with trace context propagation, enabling end-to-end agent action tracing
- **Estimated Effort**: Medium

### API-Q3: Rate Limiting / Throttling

- **Severity**: RISK-QUALITY in 18 of 29 applicable services
- **Affected Services**: Alluxio--alluxio, FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, Netflix--eureka, OpenAPITools--openapi-generator, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, ToolJet--ToolJet, apache--druid, conductor-oss--conductor, hapifhir--hapi-fhir, openzipkin--zipkin, scality--backbeat, scality--cloudserver, thingsboard--thingsboard, umami-software--umami
- **Common Finding**: No rate limiting or throttling mechanism protects APIs from agent traffic storms. Services lack per-client or per-agent rate limiting.
- **Portfolio-Level Recommendation**: Deploy API Gateway with usage plans and rate limiting per agent identity, or implement application-level rate limiting middleware
- **Estimated Effort**: Medium

### API-Q2: Structured Error Responses

- **Severity**: RISK-QUALITY in 17 of 28 applicable services
- **Affected Services**: Alluxio--alluxio, FlowiseAI--Flowise, Graylog2--graylog2-server, Netflix--eureka, OpenAPITools--openapi-generator, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, ToolJet--ToolJet, apache--druid, conductor-oss--conductor, hapifhir--hapi-fhir, openzipkin--zipkin, scality--backbeat, scality--cloudserver, thingsboard--thingsboard, umami-software--umami
- **Common Finding**: Error responses lack structured, machine-parseable format. Errors are returned as plain text, HTML, or inconsistent JSON without standard error codes.
- **Portfolio-Level Recommendation**: Adopt RFC 7807 Problem Details for HTTP APIs across the portfolio, providing structured error responses with type, title, status, detail, and instance fields
- **Estimated Effort**: Low

### ENG-Q1: Infrastructure as Code

- **Severity**: RISK-QUALITY in 17 of 19 applicable services
- **Affected Services**: Alluxio--alluxio, FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, Netflix--eureka, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, ToolJet--ToolJet, apache--druid, conductor-oss--conductor, hapifhir--hapi-fhir, openzipkin--zipkin, scality--backbeat, scality--cloudserver, thingsboard--thingsboard, umami-software--umami
- **Common Finding**: Infrastructure is not defined as code (Terraform, CDK, CloudFormation). Deployment infrastructure is configured manually or via ad-hoc scripts.
- **Portfolio-Level Recommendation**: Adopt Infrastructure as Code (Terraform or AWS CDK) for all deployment infrastructure, enabling reproducible and auditable agent execution environments
- **Estimated Effort**: High

### ENG-Q2: CI/CD Pipeline

- **Severity**: RISK-QUALITY in 17 of 19 applicable services
- **Affected Services**: Alluxio--alluxio, FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, Netflix--eureka, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, ToolJet--ToolJet, apache--druid, conductor-oss--conductor, hapifhir--hapi-fhir, openzipkin--zipkin, scality--backbeat, scality--cloudserver, thingsboard--thingsboard, umami-software--umami
- **Common Finding**: CI/CD pipelines are absent, incomplete, or lack automated testing gates. Deployments are manual or semi-automated without quality gates.
- **Portfolio-Level Recommendation**: Implement CI/CD pipelines with automated testing, security scanning, and deployment gates for all services
- **Estimated Effort**: Medium

### ENG-Q3: Automated Testing

- **Severity**: RISK-QUALITY in 17 of 19 applicable services
- **Affected Services**: Alluxio--alluxio, FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, Netflix--eureka, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, ToolJet--ToolJet, apache--druid, conductor-oss--conductor, hapifhir--hapi-fhir, openzipkin--zipkin, scality--backbeat, scality--cloudserver, thingsboard--thingsboard, umami-software--umami
- **Common Finding**: Automated test coverage is insufficient. Unit tests may exist but integration and end-to-end tests are lacking, making it unsafe for agents to trigger deployments.
- **Portfolio-Level Recommendation**: Establish minimum test coverage standards (unit + integration) with coverage gates in CI/CD pipelines
- **Estimated Effort**: High

### HITL-Q3: Override Mechanism

- **Severity**: RISK-QUALITY in 12 of 28 applicable services
- **Affected Services**: Alluxio--alluxio, Graylog2--graylog2-server, Lidarr--Lidarr, Radarr--Radarr, apache--druid, conductor-oss--conductor, hapifhir--hapi-fhir, scality--backbeat, scality--cloudserver, thingsboard--thingsboard, tqdm--tqdm, umami-software--umami
- **Common Finding**: No mechanism exists for humans to override or halt agent actions in progress. Agent operations run to completion without intervention points.
- **Portfolio-Level Recommendation**: Implement circuit-breaker patterns and human override mechanisms (kill switches) for agent-initiated operations
- **Estimated Effort**: Medium

### ENG-Q5: Security Scanning

- **Severity**: RISK-QUALITY in 9 of 12 applicable services
- **Affected Services**: Alluxio--alluxio, Lidarr--Lidarr, Prowlarr--Prowlarr, Sonarr--Sonarr, ToolJet--ToolJet, conductor-oss--conductor, hapifhir--hapi-fhir, thingsboard--thingsboard, umami-software--umami
- **Common Finding**: No automated security scanning (SAST, DAST, dependency vulnerability scanning) is integrated into the development workflow.
- **Portfolio-Level Recommendation**: Integrate dependency vulnerability scanning (Dependabot, Snyk) and SAST tools into CI/CD pipelines across the portfolio
- **Estimated Effort**: Low

### AUTH-Q5: Rate Limiting per Identity

- **Severity**: RISK-QUALITY in 5 of 21 applicable services
- **Affected Services**: Lidarr--Lidarr, Sonarr--Sonarr, getsentry--sentry-python, hapifhir--hapi-fhir, umami-software--umami
- **Common Finding**: No per-identity rate limiting exists to prevent a single agent from overwhelming service resources.
- **Portfolio-Level Recommendation**: Implement per-identity rate limiting at the API gateway level, with configurable limits per agent principal
- **Estimated Effort**: Medium

### DATA-Q3: Data Pagination

- **Severity**: RISK-QUALITY in 4 of 11 applicable services
- **Affected Services**: Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, apache--druid
- **Common Finding**: APIs return unbounded result sets without pagination. Agent queries may trigger expensive full-table scans or receive overwhelming response payloads.
- **Portfolio-Level Recommendation**: Implement cursor-based or offset pagination on all list/query endpoints with configurable page sizes and reasonable defaults
- **Estimated Effort**: Medium

### DATA-Q4: Filtering Capability

- **Severity**: RISK-QUALITY in 3 of 10 applicable services
- **Affected Services**: Alluxio--alluxio, Sonarr--Sonarr, hapifhir--hapi-fhir
- **Common Finding**: APIs lack filtering capabilities, requiring agents to retrieve full data sets and filter client-side, increasing latency and resource consumption.
- **Portfolio-Level Recommendation**: Add server-side filtering parameters to query endpoints, enabling agents to request only the data they need
- **Estimated Effort**: Medium

## Service Dependency Map

> No explicit dependency information was provided in the portfolio configuration (`dependency_overrides`).
> Dependencies were not inferrable from individual ARA report findings for this portfolio of
> independent open-source mirrors that do not interact with each other.
>
> To enable dependency-aware analysis — including identification of high-risk foundation services,
> transitive blocker propagation, and shared infrastructure impacts — add `dependency_overrides`
> to the portfolio config.

## Portfolio Remediation Guidance

> Portfolio context: Portfolio of 34 open-source project mirrors validating ATX TDs across Java, Python, JS/TS, C# — monolith, microservices, serverless, CLI, frontend, data platform — observability, storage, IoT, AI/LLM, analytics, healthcare.

### Remediation Priority Order

Remediation of cross-cutting BLOCKERs should follow this general priority:

1. **Identity and Access** — Resolve AUTH-section BLOCKERs first. You cannot enforce any other security control without machine identity and scoped permissions.
2. **Data Integrity** — Resolve STATE and DATA-section BLOCKERs second. Protect data before enabling agent write operations.
3. **API Surface** — Resolve API-section BLOCKERs third. Ensure a stable, documented integration surface for agent tools.
4. **Remaining BLOCKERs** — Address in order of affected service count (most affected first).

### Coordinated Remediation Plan

#### Identity Foundation

**BLOCKERs addressed**: AUTH-Q1
**Services affected**: Alluxio--alluxio, FlowiseAI--Flowise, Lidarr--Lidarr, Netflix--eureka, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, ToolJet--ToolJet, apache--druid, conductor-oss--conductor, openzipkin--zipkin, scality--backbeat, scality--cloudserver, thingsboard--thingsboard, umami-software--umami

- **What to do**: Deploy a shared OAuth2 authorization server (Amazon Cognito or equivalent) for M2M authentication. Issue per-agent client credentials. Integrate each affected service's API layer to validate tokens and extract principal identity from the token claims.
- **Expected outcome**: Every agent is individually identifiable. API requests carry principal attribution. Audit logs can trace actions to specific agents. Downstream AUTH controls (scoped permissions, credential rotation, revocation) become implementable.
- **Effort**: High

#### API Documentation

**BLOCKERs addressed**: API-Q1
**Services affected**: scality--backbeat, umami-software--umami

- **What to do**: Generate OpenAPI specifications from existing route definitions. Document request/response schemas, error codes, and authentication requirements. Add breaking-change detection to CI.
- **Expected outcome**: Agents can discover and reliably bind to documented API interfaces. Contract changes are detected before deployment.
- **Effort**: Medium

## Remediation Roadmap

### Phase 1 — BLOCKER Resolution

#### Phase 1 — Machine Identity Authentication (AUTH-Q1)

| Service | Evidence | Agent Scope | Resolution Reasoning |
|---------|----------|-------------|---------------------|
| Alluxio--alluxio | core/common/src/main/java/alluxio/security/authentication/AuthType.java | read-only | No M2M identity; shared/absent credentials |
| FlowiseAI--Flowise | packages/server/src/utils/validateKey.ts | read-only | No M2M identity; shared/absent credentials |
| Lidarr--Lidarr | src/Lidarr.Http/Authentication/ApiKeyAuthenticationHandler.cs | read-only | No M2M identity; shared/absent credentials |
| Netflix--eureka | eureka-core/src/main/java/com/netflix/eureka/ServerRequestAuthFilter.java | read-only | No M2M identity; shared/absent credentials |
| Prowlarr--Prowlarr | src/Prowlarr.Http/Authentication/ApiKeyAuthenticationHandler.cs | read-only | No M2M identity; shared/absent credentials |
| Radarr--Radarr | src/Radarr.Http/Authentication/ApiKeyAuthenticationHandler.cs | read-only | No M2M identity; shared/absent credentials |
| Sonarr--Sonarr | src/Sonarr.Http/Authentication/ApiKeyAuthenticationHandler.cs | read-only | No M2M identity; shared/absent credentials |
| ToolJet--ToolJet | server/src/modules/auth/controller.ts | read-only | No M2M identity; shared/absent credentials |
| apache--druid | server/src/main/java/org/apache/druid/server/security/Authenticator.java | read-only | No M2M identity; shared/absent credentials |
| conductor-oss--conductor | rest/build.gradle | read-only | No M2M identity; shared/absent credentials |
| openzipkin--zipkin | zipkin-server/src/main/java/zipkin2/server/internal/ZipkinQueryApiV2.java | read-only | No M2M identity; shared/absent credentials |
| scality--backbeat | lib/api/BackbeatServer.js:57-62 | read-only | No M2M identity; shared/absent credentials |
| scality--cloudserver | lib/auth/vault.js | read-only | No M2M identity; shared/absent credentials |
| thingsboard--thingsboard | application/src/main/java/org/thingsboard/server/service/security/model/token/JwtTokenFactory.java | read-only | No M2M identity; shared/absent credentials |
| umami-software--umami | src/lib/auth.ts | read-only | No M2M identity; shared/absent credentials |

#### Phase 1 — Formal API Interface (API-Q1)

| Service | Evidence | Agent Scope | Resolution Reasoning |
|---------|----------|-------------|---------------------|
| scality--backbeat | lib/api/routes.js | read-only | No documented API contract for agent binding |
| umami-software--umami | src/app/api/ | read-only | No documented API contract for agent binding |

### Phase 2 — RISK-SAFETY Hardening

Address the 9 cross-cutting RISK-SAFETY findings affecting authentication, state management, and data safety controls. Priority order:

1. AUTH-Q2 (Scoped Permissions) — 14 services
2. AUTH-Q7 (Revocation Mechanism) — 14 services
3. STATE-Q5 (Disaster Recovery) — 14 services
4. AUTH-Q3 (Credential Rotation) — 11 services
5. AUTH-Q6 (Agent Action Audit Trail) — 11 services
6. DATA-Q6 (Data Retention / Expiry) — 11 services
7. DATA-Q1 (Data Classification & Scoping) — 5 services
8. STATE-Q4 (State Versioning) — 4 services
9. DATA-Q2 (PII/Sensitive Data Handling) — 4 services

### Phase 3 — RISK-QUALITY Improvements

Address the 13 cross-cutting RISK-QUALITY findings affecting API surface quality, observability, discovery, and engineering maturity. Priority order:

1. DISC-Q1 (Service Discovery Metadata) — 14 services
2. OBS-Q1 (Structured Logging) — 14 services
3. API-Q2 (Structured Error Responses) — 13 services
4. API-Q3 (Rate Limiting / Throttling) — 13 services
5. OBS-Q2 (Distributed Tracing) — 13 services
6. ENG-Q1 (Infrastructure as Code) — 13 services
7. ENG-Q2 (CI/CD Pipeline) — 13 services
8. ENG-Q3 (Automated Testing) — 13 services
9. HITL-Q3 (Override Mechanism) — 10 services
10. ENG-Q5 (Security Scanning) — 7 services
11. AUTH-Q5 (Rate Limiting per Identity) — 5 services
12. DATA-Q3 (Data Pagination) — 4 services
13. DATA-Q4 (Filtering Capability) — 3 services

## Recommended Actions

> These are engagement-level recommendations based on the portfolio's agentic readiness
> profile. Discuss with your AWS Solutions Architect to determine eligibility and timing.

| Program | Relevance | Trigger Findings | Suggested Timing | Next Step |
|---------|-----------|-----------------|------------------|-----------|
| AI DLC | Engineering maturity gaps across 72% of applicable repos | ENG-Q1/Q2/Q3 RISK-QUALITY in 13/18 repos | Run first | Request workshop via AWS SA |
| AgentStorming | No defined agent use cases; all read-only scope | No write-enabled services; testing portfolio context | After AI DLC | Request workshop via AWS SA |
| AXE | 15 services at Agent-Ready profile | Agent-Ready count ≥ 3 | After AgentStorming | Request engagement via AWS SA |
| EBA on Agentic AI | AUTH-Q1 BLOCKER in 15 repos | Single cross-cutting BLOCKER ≥ 5 repos | After AXE | Request engagement via AWS SA |

### Program Details

#### AI Driven Development Lifecycle (AI DLC)

- **Why triggered**: Engineering maturity gaps across the portfolio — ENG-Q1, ENG-Q2, and ENG-Q3 each show RISK-QUALITY in 13 of 18 applicable repos (72%). The portfolio shows manual development workflows that would benefit from AI-driven automation.
- **What it provides**: Workshop for adopting the AI Driven Development Lifecycle, emphasizing AI-powered execution with human oversight and dynamic team collaboration.
- **Suggested timing**: Run first to establish AI-driven development practices before agentic integration work
- **Recommended scope**: All 18 services with engineering maturity findings
- **Next step**: Request workshop engagement via AWS Solutions Architect

#### AgentStorming

- **Why triggered**: Portfolio context describes validation/testing of open-source mirrors without a defined production agent use case. No services have write-enabled agent scope. Agent integration paths are not identified.
- **What it provides**: Structured workshop using Cognitive Complexity Analysis and Agentic Workflow Design to identify where AI agents deliver value vs. traditional automation.
- **Suggested timing**: Run after AI DLC to identify where agents should operate
- **Recommended scope**: Full portfolio — identify which services would benefit most from agentic integration
- **Next step**: Request workshop engagement via AWS Solutions Architect

#### Agent Experience Engagement (AXE)

- **Why triggered**: 15 services at Agent-Ready profile (threshold: 3+). Portfolio is positioned for structured agent experience design.
- **What it provides**: Strategic methodology for implementing agentic AI — business process mapping, task identification, evaluation metrics, data architecture, governance, and guardrails.
- **Suggested timing**: Run after AgentStorming to design the agent experience for identified use cases
- **Recommended scope**: The 15 Agent-Ready services as initial integration targets
- **Next step**: Request engagement via AWS Solutions Architect

#### EBA on Agentic AI

- **Why triggered**: AUTH-Q1 (Machine Identity Authentication) is a cross-cutting BLOCKER in 15 repositories (threshold: 5+). This systemic identity gap requires coordinated architecture remediation that cannot be addressed through standard advisory.
- **What it provides**: Intensive, time-boxed engagement embedding AWS expertise to compress multi-quarter remediation into a focused sprint — producing remediated systems, validated agent integrations, and a sequenced deployment roadmap.
- **Suggested timing**: Run after AXE to accelerate implementation of identity foundation
- **Recommended scope**: The 15 AUTH-Q1-blocked services requiring machine identity implementation
- **Next step**: Request engagement via AWS Solutions Architect

## Portfolio-Level Findings

> These questions evaluate capabilities that can only be assessed by looking across
> multiple repos. They are distinct from cross-cutting analysis (which aggregates
> individual findings). Individual report findings are never overridden.

### PORT-ARA-Q1: Centralized Identity Plane

- **Severity**: BLOCKER
- **Finding**: No shared identity provider detected across any repository. Each service that has authentication uses its own independent mechanism (custom API keys, basic auth, IP-based ACLs). No Cognito, Okta, or shared auth middleware is referenced across multiple repos.
- **Evidence**: 15 services have AUTH-Q1 BLOCKER (no machine identity); remaining authenticated services use disparate, service-specific mechanisms with no shared IdP resource (by ARN, name, or config reference) appearing in 2+ repos.
- **Recommendation**: Deploy a centralized identity provider (Amazon Cognito User Pool with client credentials grant) serving all services in the portfolio. Issue per-agent credentials from this single plane.
- **Affected Services**: All 34 services (none have shared IdP integration)
- **Contextual Annotations**: This finding provides context for AUTH-Q1 cross-cutting BLOCKER — a shared IdP would resolve machine identity for all 15 affected services simultaneously.

### PORT-ARA-Q2: Cross-Service Audit Correlation

- **Severity**: RISK
- **Finding**: No shared trace ID propagation or centralized audit trail detected across the portfolio. Services log independently with no correlation mechanism. No shared CloudTrail trail, no consistent trace headers (X-Amzn-Trace-Id, traceparent), no centralized log aggregation visible in configs.
- **Evidence**: OBS-Q2 (Distributed Tracing) is RISK-QUALITY in 13 services; no OpenTelemetry, X-Ray, or shared tracing configuration found across repos.
- **Recommendation**: Deploy centralized observability (AWS X-Ray or OpenTelemetry Collector) with trace context propagation headers enforced at the API gateway level, enabling end-to-end agent action correlation.
- **Affected Services**: All services with HTTP APIs (27 applicable)
- **Contextual Annotations**: Resolving this would mitigate AUTH-Q6 (audit trail) findings for services that gain trace-correlated logging.

### PORT-ARA-Q3: Portfolio-Level Rate Limiting

- **Severity**: RISK
- **Finding**: No shared API gateway, WAF, or portfolio-level rate limiting mechanism detected. API-Q3 (Rate Limiting) is RISK-QUALITY in 13 services, each lacking its own rate limiting. No shared WAF WebACL or API Gateway usage plans are configured across the portfolio.
- **Evidence**: No AWS WAF, API Gateway, or shared rate limiting middleware configuration found in any repo that covers multiple services.
- **Recommendation**: Deploy a shared API Gateway (Amazon API Gateway) with WAF and usage plans providing portfolio-level rate limiting for agent traffic. Supplement with per-service application-level rate limiting.
- **Affected Services**: All 27 services with HTTP API surfaces
- **Contextual Annotations**: Portfolio-level rate limiting would partially mitigate API-Q3 and AUTH-Q5 findings across affected services — **verify** per-service configuration after gateway deployment.

### PORT-ARA-Q4: Transitive Dependency Safety

- **Severity**: INFO
- **Finding**: No explicit service dependencies are declared in this portfolio of independent open-source mirrors. Services do not depend on each other synchronously or asynchronously. No Agent-Ready service depends on a Not-Agent-Integrable service.
- **Evidence**: No `dependency_overrides` provided; no inter-service dependencies inferable from individual ARA reports (each repo is an independent open-source project mirror).
- **Recommendation**: No action required for transitive dependency safety in this independent-service portfolio. If services are deployed as an integrated system in the future, map dependencies and re-assess.
- **Affected Services**: None (no transitive dependency chains identified)
- **Contextual Annotations**: N/A

### PORT-ARA-Q5: Agent Identity Governance

- **Severity**: RISK
- **Finding**: No centralized mechanism exists to suspend or revoke agent identities across all services simultaneously. Each service manages authentication independently. There is no portfolio-wide agent identity registry, centralized API key management, or shared revocation mechanism.
- **Evidence**: AUTH-Q7 (Revocation Mechanism) is RISK-SAFETY in 14 services; no centralized identity governance tool, Cognito app client registry, or API key management system detected across the portfolio.
- **Recommendation**: Implement centralized agent identity governance — a single control plane (e.g., Cognito Identity Pool with app clients, or API Gateway API key registry) where all agent identities are registered and can be suspended or revoked globally with a single action.
- **Affected Services**: All 34 services
- **Contextual Annotations**: Resolving PORT-ARA-Q1 (centralized identity plane) is a prerequisite — you need centralized identity before you can govern it centrally.

## Service-by-Service Summary

| Service | Repo Type | Agent Scope | Readiness Profile | BLOCKERs | RISKs | INFOs | N/A |
|---------|-----------|-------------|-------------------|----------|-------|-------|-----|
| Alluxio--alluxio | application | read-only | Remediation Required | 1 | 18 | 18 | 0 |
| FlowiseAI--Flowise | application | read-only | Remediation Required | 1 | 13 | 10 | 0 |
| Graylog2--graylog2-server | application | read-only | Remediation Required | 1 | 14 | 17 | 0 |
| Lidarr--Lidarr | application | read-only | Remediation Required | 1 | 17 | 12 | 0 |
| Netflix--eureka | application | read-only | Remediation Required | 1 | 13 | 10 | 0 |
| Prowlarr--Prowlarr | application | read-only | Remediation Required | 1 | 17 | 10 | 0 |
| Radarr--Radarr | application | read-only | Remediation Required | 1 | 17 | 13 | 0 |
| Sonarr--Sonarr | application | read-only | Remediation Required | 0 | 0 | 0 | 1 |
| ToolJet--ToolJet | application | read-only | Remediation Required | 1 | 18 | 10 | 0 |
| apache--druid | application | read-only | Remediation Required | 0 | 0 | 0 | 2 |
| conductor-oss--conductor | application | read-only | Remediation Required | 1 | 17 | 11 | 0 |
| openzipkin--zipkin | application | read-only | Remediation Required | 1 | 14 | 9 | 0 |
| scality--backbeat | application | read-only | Remediation Required | 2 | 15 | 20 | 0 |
| scality--cloudserver | application | read-only | Remediation Required | 0 | 0 | 0 | 1 |
| thingsboard--thingsboard | application | read-only | Remediation Required | 1 | 15 | 11 | 0 |
| umami-software--umami | application | read-only | Remediation Required | 2 | 20 | 13 | 0 |
| OpenAPITools--openapi-generator | application | read-only | Pilot-Ready (Safety Concerns) | 0 | 8 | 16 | 5 |
| getsentry--sentry-python | library | read-only | Pilot-Ready (Safety Concerns) | 0 | 9 | 15 | 5 |
| hapifhir--hapi-fhir | application | read-only | Pilot-Ready (Safety Concerns) | 0 | 19 | 10 | 0 |
| akveo--ngx-admin | application | read-only | Agent-Ready | 0 | 0 | 5 | 38 |
| apache--flink-connector-aws | application | read-only | Agent-Ready | 0 | 3 | 23 | 5 |
| arrow-py--arrow | library | read-only | Agent-Ready | 0 | 0 | 33 | 5 |
| coreui--coreui-free-angular-admin-template | application | read-only | Agent-Ready | 0 | 0 | 38 | 5 |
| dwyl--aws-sdk-mock | application | read-only | Agent-Ready | 0 | 0 | 13 | 5 |
| getlift--lift | library | read-only | Agent-Ready | 0 | 0 | 38 | 5 |
| greenshot--greenshot | application | read-only | Agent-Ready | 0 | 0 | 5 | 5 |
| gulpjs--gulp | library | read-only | Agent-Ready | 0 | 0 | 33 | 5 |
| iterative--dvc | application | read-only | Agent-Ready | 0 | 0 | 5 | 38 |
| motdotla--node-lambda | application | read-only | Agent-Ready | 0 | 0 | 38 | 5 |
| realworld-apps--angular-realworld-example-app | application | read-only | Agent-Ready | 0 | 0 | 8 | 5 |
| serverless--serverless | application | read-only | Agent-Ready | 0 | 0 | 5 | 5 |
| tqdm--tqdm | library | read-only | Agent-Ready | 0 | 2 | 31 | 5 |
| webpack--webpack | library | read-only | Agent-Ready | 0 | 0 | 38 | 5 |
| zappa--Zappa | application | read-only | Agent-Ready | 0 | 0 | 38 | 5 |

### Individual Service Details

#### Alluxio--alluxio

- **Readiness Profile**: Remediation Required
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (1):
  - AUTH-Q1: No machine identity authentication suitable for agent principals
- **RISKs** (18):
  - AUTH-Q2: Coarse-grained permissions — no fine-grained RBAC/ABAC
  - AUTH-Q3: No action-level authorization beyond file permission bits
  - AUTH-Q6: Audit logging disabled by default and not immutable
  - AUTH-Q7: No mechanism to suspend individual agent identities
  - API-Q2: No committed machine-readable API specification for REST surface
  - ... and 13 more
- **Key Recommendations**:
  - Enable S3 REST authentication and implement a CUSTOM AuthenticationProvider that validates agent credentials and maps th
  - Deploy an API gateway in front of the Alluxio proxy that enforces operation-level access control per agent identity.
  - Implement ABAC or fine-grained RBAC at the proxy/gateway layer to enforce action-level controls.

#### FlowiseAI--Flowise

- **Readiness Profile**: Remediation Required
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (1):
  - AUTH-Q1: Machine Identity Authentication — No Principal Attribution
- **RISKs** (13):
  - AUTH-Q2: Scoped Permissions — Non-Enterprise Keys Lack Granularity
  - AUTH-Q6: Immutable Audit Logging — Login Events Only
  - AUTH-Q7: Agent Identity Suspension — Delete Only, No Suspend
  - STATE-Q5: Rate Limiting — Prediction Endpoints Only
  - DATA-Q6: PII Redaction in Logs — Opt-In Only
  - ... and 8 more
- **Key Recommendations**:
  - Extend the ApiKey entity to include a principalName or agentIdentity field. Log the API key ID alongside every write ope
  - Extend API key permission enforcement to non-enterprise tier. Allow API keys to be scoped to specific operations.
  - Implement operation-level audit logging that records the authenticated principal, action performed, resource affected, a

#### Graylog2--graylog2-server

- **Readiness Profile**: Remediation Required
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (1):
  - AUTH-Q6: No Audit Logging in Open-Source Edition
- **RISKs** (14):
  - AUTH-Q2: No Pre-Built Agent Role Template for Least Privilege
  - AUTH-Q3: Admin Bypass Circumvents Action-Level Authorization
  - AUTH-Q7: No Single-Operation Agent Identity Suspension
  - STATE-Q5: No API-Layer Rate Limiting
  - DATA-Q6: No PII Redaction in Application Logs
  - ... and 9 more
- **Key Recommendations**:
  - Implement a MongoAuditEventSender that persists audit events to a dedicated MongoDB collection. The framework already de
  - Define and document a least-privilege agent role template that restricts agent tokens to only the API operations require
  - Enforce that agent tokens cannot inherit admin privileges regardless of the creating user's role. Add token-level permis

#### Lidarr--Lidarr

- **Readiness Profile**: Remediation Required
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (1):
  - AUTH-Q1: No Machine Identity Authentication
- **RISKs** (18):
  - AUTH-Q2: No Scoped Permissions
  - AUTH-Q3: No Action-Level Authorization
  - AUTH-Q6: No Immutable Audit Logging
  - AUTH-Q7: No Agent Identity Suspension Mechanism
  - STATE-Q5: No Inbound Rate Limiting
  - ... and 13 more
- **Key Recommendations**:
  - Introduce per-agent API key generation with unique principal identifiers. Add a ClientId field to the authentication tic
  - Implement role-based access control with at minimum a read-only role that excludes POST/PUT/DELETE operations. Support s
  - Introduce action-level authorization attributes on controllers with granular permissions.

#### Netflix--eureka

- **Readiness Profile**: Remediation Required
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (1):
  - AUTH-Q1: No Machine Identity Authentication
- **RISKs** (13):
  - AUTH-Q2: No Scoped Permissions (Least Privilege)
  - AUTH-Q3: No Action-Level Authorization
  - AUTH-Q7: No Agent Identity Suspension Mechanism
  - STATE-Q5: Rate Limiting Disabled by Default
  - DATA-Q2: No Data Residency Controls
  - ... and 8 more
- **Key Recommendations**:
  - Implement API Gateway or service mesh authentication in front of Eureka server endpoints. Add JWT or mTLS validation to 
  - After implementing machine identity (AUTH-Q1), add method-level authorization using IAM policies or API Gateway resource
  - Implement fine-grained RBAC or ABAC in the servlet filter chain or via API Gateway method-level authorization.

#### Prowlarr--Prowlarr

- **Readiness Profile**: Remediation Required
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (1):
  - AUTH-Q1: No machine identity authentication — single shared API key
- **RISKs** (17):
  - AUTH-Q2: No scoped permissions — binary access model
  - AUTH-Q3: No action-level authorization
  - AUTH-Q6: No immutable audit logging for API operations
  - AUTH-Q7: No per-agent identity suspension capability
  - STATE-Q5: No server-side rate limiting on API endpoints
  - ... and 12 more
- **Key Recommendations**:
  - Implement multiple API key support with principal labels. Each agent or integration gets its own key that is logged with
  - Implement role-based access control (RBAC) with at least read-only and admin roles. Add scope claims to API keys.
  - Introduce an authorization policy that distinguishes read (GET) from write (POST/PUT/DELETE) operations, enforceable per

#### Radarr--Radarr

- **Readiness Profile**: Remediation Required
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (1):
  - AUTH-Q1: No Machine Identity Authentication
- **RISKs** (17):
  - AUTH-Q2: No Scoped Permissions (Least Privilege)
  - AUTH-Q3: No Action-Level Authorization
  - AUTH-Q6: No Immutable Audit Logging
  - AUTH-Q7: No Agent Identity Suspension Mechanism
  - STATE-Q5: No Inbound API Rate Limiting
  - ... and 12 more
- **Key Recommendations**:
  - Implement per-client API key issuance with a principal field stored alongside each key. Add principal to request context
  - Introduce role-based API keys (read-only, media-management, admin) mapping to allowed endpoint sets.
  - Add authorization policies per HTTP method/endpoint group using ASP.NET Core policy-based authorization.

#### Sonarr--Sonarr

- **Readiness Profile**: Remediation Required
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (1):
  - AUTH-Q1: No Machine Identity Authentication
- **RISKs** (21):
  - AUTH-Q2: No Scoped Permissions (Least Privilege)
  - AUTH-Q3: No Action-Level Authorization
  - AUTH-Q6: No Immutable Audit Logging
  - AUTH-Q7: No Agent Identity Suspension Mechanism
  - STATE-Q4: No Circuit Breakers for External Dependencies
  - ... and 16 more
- **Key Recommendations**:
  - Implement support for multiple API keys with distinct identity labels, or add OAuth 2.0 client credentials flow via an A
  - Implement RBAC or scoped API key permissions that differentiate read vs write access per resource type.
  - Add action-level authorization attributes or ABAC/fine-grained RBAC model.

#### ToolJet--ToolJet

- **Readiness Profile**: Remediation Required
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (1):
  - AUTH-Q1: No machine identity authentication for agents
- **RISKs** (18):
  - AUTH-Q2: Coarse-grained permissions lack resource-instance scoping
  - AUTH-Q3: Action-level authorization coupled to human role hierarchy
  - AUTH-Q6: Audit logs stored in mutable database without immutability guarantees
  - AUTH-Q7: No independent agent identity suspension mechanism
  - STATE-Q4: No circuit breaker protection for external dependency calls
  - ... and 13 more
- **Key Recommendations**:
  - Implement an API key authentication strategy that creates independent machine principals with attribution logged in audi
  - Implement resource-instance-level permissions in the CASL ability factory to allow agent identities to be scoped to spec
  - Extend the CASL ability factory to support per-principal action overrides, allowing machine identities to have custom ac

#### apache--druid

- **Readiness Profile**: Remediation Required
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (1):
  - AUTH-Q1: No Machine Identity Authentication for Agent Principals
- **RISKs** (16):
  - AUTH-Q2: Coarse-Grained Permission Scoping
  - AUTH-Q6: Audit Logs Not Tamper-Evident
  - AUTH-Q7: No Immediate Agent Identity Suspension
  - STATE-Q5: No HTTP-Level Rate Limiting
  - DATA-Q6: No PII Redaction in Logs
  - ... and 11 more
- **Key Recommendations**:
  - Implement an Authenticator extension supporting OAuth2 client_credentials or API key-based machine identity with per-age
  - Create dedicated authorization roles for agent identities with minimal resource-regex patterns. Consider extending the A
  - Implement an AuditManager extension that writes to an immutable store (S3 with Object Lock) or integrate with AWS CloudT

#### conductor-oss--conductor

- **Readiness Profile**: Remediation Required
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (1):
  - AUTH-Q1: No Machine Identity Authentication
- **RISKs** (17):
  - AUTH-Q2: No Scoped Permissions
  - AUTH-Q3: No Action-Level Authorization
  - AUTH-Q6: No Immutable Audit Logging
  - AUTH-Q7: No Agent Identity Suspension Capability
  - STATE-Q4: No Circuit Breakers on External Calls
  - ... and 12 more
- **Key Recommendations**:
  - Add spring-boot-starter-security and configure a SecurityFilterChain with OAuth2 resource server (JWT) or API key authen
  - After implementing AUTH-Q1, define scoped permissions per agent identity (e.g., workflow:read, workflow:execute, metadat
  - Implement method-level authorization using Spring Security @PreAuthorize with fine-grained roles.

#### openzipkin--zipkin

- **Readiness Profile**: Remediation Required
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (1):
  - AUTH-Q1: No Machine Identity Authentication
- **RISKs** (14):
  - AUTH-Q2: No Scoped Permissions
  - AUTH-Q3: No Action-Level Authorization
  - AUTH-Q6: No Immutable Audit Logging
  - AUTH-Q7: No Agent Identity Suspension Mechanism
  - STATE-Q5: No API-Layer Rate Limiting for Query Endpoints
  - ... and 9 more
- **Key Recommendations**:
  - Deploy an API Gateway or reverse proxy in front of Zipkin that enforces API key or OAuth2 client credentials authenticat
  - Implement API Gateway resource policies that separate read (GET) and write (POST) operations with different authorizatio
  - Implement authorization at the platform layer (API Gateway or service mesh) with per-method policies.

#### scality--backbeat

- **Readiness Profile**: Remediation Required
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (2):
  - AUTH-Q1: No machine identity authentication on management API
  - API-Q1: No documented API interface for agent tool binding
- **RISKs** (15):
  - AUTH-Q2: No per-identity permission scoping at API layer
  - AUTH-Q3: No action-level authorization
  - AUTH-Q6: No immutable audit logging of authenticated principals
  - AUTH-Q7: No agent identity suspension capability
  - STATE-Q5: No API-layer rate limiting
  - ... and 10 more
- **Key Recommendations**:
  - Deploy an API Gateway with OAuth2 or API key authentication that attributes each request to a specific principal.
  - Create an OpenAPI specification documenting all routes, request/response schemas, error codes, and authentication requir
  - Implement token-based authentication with per-identity route-level permissions.

#### scality--cloudserver

- **Readiness Profile**: Remediation Required
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (1):
  - AUTH-Q1: No machine identity authentication with principal attribution
- **RISKs** (18):
  - AUTH-Q2: Scoped permissions incomplete — IAM integration pending
  - AUTH-Q3: Action-level authorization depends on incomplete IAM
  - AUTH-Q6: Audit logging exists but is file-based, mutable, and disabled by default
  - AUTH-Q7: No immediate agent identity suspension mechanism
  - STATE-Q4: No circuit breakers or resilience patterns for external dependencies
  - ... and 13 more
- **Key Recommendations**:
  - Create dedicated IAM-style accounts per agent in the Vault backend with distinct access keys. Ensure the server access l
  - Complete IAM integration and ensure agent identities are never classified as service users.
  - Ensure bucket policies are applied to all agent-accessible buckets with explicit action-level allow/deny.

#### thingsboard--thingsboard

- **Readiness Profile**: Remediation Required
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (1):
  - AUTH-Q1: No dedicated machine identity authentication mechanism
- **RISKs** (17):
  - AUTH-Q2: Coarse-grained permission model lacks per-identity scoping
  - AUTH-Q3: Action-level authorization exists but is not configurable per identity
  - AUTH-Q6: Audit logs not stored in immutable/tamper-evident storage
  - AUTH-Q7: No independent agent identity suspension mechanism
  - STATE-Q5: Rate limiting has SYS_ADMIN exemption and no per-identity limits
  - ... and 12 more
- **Key Recommendations**:
  - Create a dedicated service account user type with a machine-identity flag that appears in audit log entries. Extend the 
  - Introduce a custom permission system or API key scope mechanism that allows per-resource-type and per-operation permissi
  - Make the permission matrix configurable per user/service account, allowing per-identity (Resource, Operation) overrides 

#### umami-software--umami

- **Readiness Profile**: Remediation Required
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (2):
  - API-Q1: No Documented API Interface
  - AUTH-Q1: No Machine Identity Authentication
- **RISKs** (19):
  - AUTH-Q2: Coarse-Grained Permissions
  - AUTH-Q3: Limited Action-Level Authorization for Agent Identities
  - AUTH-Q6: No Immutable Audit Logging
  - AUTH-Q7: No Agent Identity Suspension Mechanism
  - STATE-Q5: No Rate Limiting or Throttling
  - ... and 14 more
- **Key Recommendations**:
  - Generate an OpenAPI 3.x specification from existing routes and Zod schemas using tools like zod-to-openapi or next-swagg
  - Implement API key authentication with per-key principal attribution, or add an OAuth2 client credentials flow for machin
  - Create a dedicated agent role with minimal permissions or leverage existing view-only role for read-only agent access.

#### OpenAPITools--openapi-generator

- **Readiness Profile**: Pilot-Ready (Safety Concerns)
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P2
- **RISKs** (8):
  - AUTH-Q2: No scoped permissions — all endpoints publicly accessible
  - AUTH-Q3: No action-level authorization — GET and POST equally accessible
  - STATE-Q5: No rate limiting — CPU-intensive endpoints unprotected
  - API-Q2: No static machine-readable API specification committed
  - API-Q3: No structured error responses with retryable classification
  - ... and 3 more
- **Key Recommendations**:
  - Deploy behind AWS API Gateway with resource-level IAM policies that restrict agent identities to specific endpoints (e.g
  - Add API Gateway method-level authorization or Spring Security configuration to differentiate read (GET) from write (POST
  - Deploy behind AWS API Gateway with usage plans that enforce rate limits (low burst for POST code-generation endpoints, h

#### getsentry--sentry-python

- **Readiness Profile**: Pilot-Ready (Safety Concerns)
- **Repo Type**: library
- **Agent Scope**: read-only
- **Priority**: P2
- **RISKs** (9):
  - API-Q1: Library API documented via type annotations but no formal machine-readable spec
  - AUTH-Q1: DSN-based authentication lacks principal attribution
  - AUTH-Q2: No scoped permission model within SDK
  - AUTH-Q3: No action-level authorization within SDK
  - AUTH-Q5: No secrets management integration for DSN
  - ... and 4 more
- **Key Recommendations**:
  - Continue maintaining comprehensive type annotations. Consider generating a machine-readable API manifest for agent tool 
  - Document patterns for agent identity attribution via tags and separate DSNs per agent identity.
  - Document recommended patterns for agent consumers: create dedicated Sentry projects per agent identity with separate DSN

#### hapifhir--hapi-fhir

- **Readiness Profile**: Pilot-Ready (Safety Concerns)
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P2
- **RISKs** (19):
  - AUTH-Q2: Scoped Permissions (Least Privilege) — Framework-level support only
  - AUTH-Q6: Immutable Audit Logging — Audit events stored in mutable datastore
  - AUTH-Q7: Agent Identity Suspension — No built-in revocation mechanism
  - STATE-Q4: Circuit Breakers and Resilience — Retry only, no circuit breaker
  - STATE-Q5: Rate Limiting and Throttling — No production rate limiter
  - ... and 14 more
- **Key Recommendations**:
  - Create deployment templates (IaC) defining agent-specific IAM roles with explicit action-level permissions integrated wi
  - Implement an IAuditDataStore that writes to an immutable external store (S3 with Object Lock or CloudWatch Logs with ret
  - Integrate with an external identity provider supporting immediate per-client credential revocation.

#### akveo--ngx-admin

- **Readiness Profile**: Agent-Ready
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P2

#### apache--flink-connector-aws

- **Readiness Profile**: Agent-Ready
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P2
- **RISKs** (3):
  - DISC-Q1: No automated API contract breaking-change detection in CI
  - OBS-Q1: No structured logging or distributed tracing hooks
  - OBS-Q2: No recommended alerting thresholds documented
- **Key Recommendations**:
  - Add japicmp-maven-plugin or revapi-maven-plugin to CI for binary compatibility checks on public API classes.
  - Add MDC context propagation for trace IDs in key connector operations (source reads, sink writes) to allow consuming Fli
  - Add a Monitoring & Alerting section to connector documentation recommending specific Flink metrics to alert on (e.g., nu

#### arrow-py--arrow

- **Readiness Profile**: Agent-Ready
- **Repo Type**: library
- **Agent Scope**: read-only
- **Priority**: P2

#### coreui--coreui-free-angular-admin-template

- **Readiness Profile**: Agent-Ready
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P2

#### dwyl--aws-sdk-mock

- **Readiness Profile**: Agent-Ready
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P2

#### getlift--lift

- **Readiness Profile**: Agent-Ready
- **Repo Type**: library
- **Agent Scope**: read-only
- **Priority**: P2

#### greenshot--greenshot

- **Readiness Profile**: Agent-Ready
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P2

#### gulpjs--gulp

- **Readiness Profile**: Agent-Ready
- **Repo Type**: library
- **Agent Scope**: read-only
- **Priority**: P2

#### iterative--dvc

- **Readiness Profile**: Agent-Ready
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P2

#### motdotla--node-lambda

- **Readiness Profile**: Agent-Ready
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P2

#### realworld-apps--angular-realworld-example-app

- **Readiness Profile**: Agent-Ready
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P2

#### serverless--serverless

- **Readiness Profile**: Agent-Ready
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P2

#### tqdm--tqdm

- **Readiness Profile**: Agent-Ready
- **Repo Type**: library
- **Agent Scope**: read-only
- **Priority**: P2
- **RISKs** (2):
  - DISC-Q1: No automated breaking-change detection in CI
  - HITL-Q3: No dedicated sandbox/staging for agent testing
- **Key Recommendations**:
  - Add a CI step that compares the public API surface (exports in __init__.py, function signatures in std.py) between the P
  - Document a recommended virtualenv-based testing pattern for agent integrations. Low priority given the library's nature.

#### webpack--webpack

- **Readiness Profile**: Agent-Ready
- **Repo Type**: library
- **Agent Scope**: read-only
- **Priority**: P2

#### zappa--Zappa

- **Readiness Profile**: Agent-Ready
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P2

## Assessment Inventory

| # | Service | Report File | Assessment Date | Repo Type | Agent Scope |
|---|---------|-------------|-----------------|-----------|-------------|
| 1 | Alluxio--alluxio | Alluxio--alluxio/agentic-readiness-assessment/Alluxio--alluxio-ara-report.json | 2025-05-07 | application | read-only |
| 2 | FlowiseAI--Flowise | FlowiseAI--Flowise/agentic-readiness-assessment/FlowiseAI--Flowise-ara-report.json | 2025-05-08 | application | read-only |
| 3 | Graylog2--graylog2-server | Graylog2--graylog2-server/agentic-readiness-assessment/Graylog2--graylog2-server-ara-report.json | 2025-05-08 | application | read-only |
| 4 | Lidarr--Lidarr | Lidarr--Lidarr/agentic-readiness-assessment/Lidarr--Lidarr-ara-report.json | 2025-05-08 | application | read-only |
| 5 | Netflix--eureka | Netflix--eureka/agentic-readiness-assessment/Netflix--eureka-ara-report.json | 2025-05-08 | application | read-only |
| 6 | OpenAPITools--openapi-generator | OpenAPITools--openapi-generator/agentic-readiness-assessment/OpenAPITools--openapi-generator-ara-report.json | 2026-05-08 | application | read-only |
| 7 | Prowlarr--Prowlarr | Prowlarr--Prowlarr/agentic-readiness-assessment/Prowlarr--Prowlarr-ara-report.json | 2025-05-08 | application | read-only |
| 8 | Radarr--Radarr | Radarr--Radarr/agentic-readiness-assessment/Radarr--Radarr-ara-report.json | 2025-05-08 | application | read-only |
| 9 | Sonarr--Sonarr | Sonarr--Sonarr/agentic-readiness-assessment/Sonarr--Sonarr-ara-report.json | 2025-05-08 | application | read-only |
| 10 | ToolJet--ToolJet | ToolJet--ToolJet/agentic-readiness-assessment/ToolJet--ToolJet-ara-report.json | 2026-05-08 | application | read-only |
| 11 | akveo--ngx-admin | akveo--ngx-admin/agentic-readiness-assessment/akveo--ngx-admin-ara-report.json | 2026-05-07 | application | read-only |
| 12 | apache--druid | apache--druid/agentic-readiness-assessment/apache--druid-ara-report.json | 2025-05-07 | application | read-only |
| 13 | apache--flink-connector-aws | apache--flink-connector-aws/agentic-readiness-assessment/apache--flink-connector-aws-ara-report.json | 2026-05-07 | application | read-only |
| 14 | arrow-py--arrow | arrow-py--arrow/agentic-readiness-assessment/arrow-py--arrow-ara-report.json | 2026-05-07 | library | read-only |
| 15 | conductor-oss--conductor | conductor-oss--conductor/agentic-readiness-assessment/conductor-oss--conductor-ara-report.json | 2026-05-08 | application | read-only |
| 16 | coreui--coreui-free-angular-admin-template | coreui--coreui-free-angular-admin-template/agentic-readiness-assessment/coreui--coreui-free-angular-admin-template-ara-report.json | 2026-05-07 | application | read-only |
| 17 | dwyl--aws-sdk-mock | dwyl--aws-sdk-mock/agentic-readiness-assessment/dwyl--aws-sdk-mock-ara-report.json | 2026-05-07 | application | read-only |
| 18 | getlift--lift | getlift--lift/agentic-readiness-assessment/getlift--lift-ara-report.json | 2025-05-08 | library | read-only |
| 19 | getsentry--sentry-python | getsentry--sentry-python/agentic-readiness-assessment/getsentry--sentry-python-ara-report.json | 2026-05-08 | library | read-only |
| 20 | greenshot--greenshot | greenshot--greenshot/agentic-readiness-assessment/greenshot--greenshot-ara-report.json | 2026-05-08 | application | read-only |
| 21 | gulpjs--gulp | gulpjs--gulp/agentic-readiness-assessment/gulpjs--gulp-ara-report.json | 2026-05-08 | library | read-only |
| 22 | hapifhir--hapi-fhir | hapifhir--hapi-fhir/agentic-readiness-assessment/hapifhir--hapi-fhir-ara-report.json | 2026-05-08 | application | read-only |
| 23 | iterative--dvc | iterative--dvc/agentic-readiness-assessment/iterative--dvc-ara-report.json | 2026-05-08 | application | read-only |
| 24 | motdotla--node-lambda | motdotla--node-lambda/agentic-readiness-assessment/motdotla--node-lambda-ara-report.json | 2025-05-08 | application | read-only |
| 25 | openzipkin--zipkin | openzipkin--zipkin/agentic-readiness-assessment/openzipkin--zipkin-ara-report.json | 2026-05-08 | application | read-only |
| 26 | realworld-apps--angular-realworld-example-app | realworld-apps--angular-realworld-example-app/agentic-readiness-assessment/realworld-apps--angular-realworld-example-app-ara-report.json | 2025-05-08 | application | read-only |
| 27 | scality--backbeat | scality--backbeat/agentic-readiness-assessment/scality--backbeat-ara-report.json | 2025-05-08 | application | read-only |
| 28 | scality--cloudserver | scality--cloudserver/agentic-readiness-assessment/scality--cloudserver-ara-report.json | 2025-01-08 | application | read-only |
| 29 | serverless--serverless | serverless--serverless/agentic-readiness-assessment/serverless--serverless-ara-report.json | 2025-05-08 | application | read-only |
| 30 | thingsboard--thingsboard | thingsboard--thingsboard/agentic-readiness-assessment/thingsboard--thingsboard-ara-report.json | 2025-05-08 | application | read-only |
| 31 | tqdm--tqdm | tqdm--tqdm/agentic-readiness-assessment/tqdm--tqdm-ara-report.json | 2025-05-08 | library | read-only |
| 32 | umami-software--umami | umami-software--umami/agentic-readiness-assessment/umami-software--umami-ara-report.json | 2025-01-08 | application | read-only |
| 33 | webpack--webpack | webpack--webpack/agentic-readiness-assessment/webpack--webpack-ara-report.json | 2025-01-08 | library | read-only |
| 34 | zappa--Zappa | zappa--Zappa/agentic-readiness-assessment/zappa--Zappa-ara-report.json | 2025-05-08 | application | read-only |
