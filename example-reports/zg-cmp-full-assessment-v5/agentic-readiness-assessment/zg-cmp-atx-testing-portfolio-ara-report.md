# Portfolio Agentic Readiness Assessment Report

**Date**: 2026-04-30
**Services Assessed**: 34
**Portfolio Context**: 34 open-source project mirrors for ATX TD validation across multiple languages, architectures, and domains.
**Portfolio Name**: zg-cmp-atx-testing

---

## Executive Dashboard

### Readiness Distribution

| Profile | Services | Percentage | Description |
|---------|----------|------------|-------------|
| ✅ Agent-Ready | 14 | 41% | 0 blockers, 0 RISK-SAFETY — broad agent deployment |
| 🟡 Pilot-Ready | 1 | 3% | 0 blockers, 1–2 RISK-SAFETY — narrow pilot |
| 🟡 Pilot-Ready (Safety Concerns) | 6 | 18% | 0 blockers, 3+ RISK-SAFETY — supervised pilot, prioritize safety |
| 🟠 Remediation Required | 13 | 38% | 1–2 blockers — remediate before any agent deployment |
| ❌ Not Agent-Integrable | 0 | 0% | 3+ blockers — deferred or descoped |

> **Note (v5.1 update)**: The ARA DATA-Q1 question was revised from a binary BLOCKER (for any repo storing sensitive data without formal classification) to a tiered model evaluating three layers — B1: agent-facing API response scoping, B2: access control differentiation, B3: formal classification metadata. The highest layer that fires determines the overall severity. This eliminates false-positive BLOCKERs for applications that actually filter sensitive fields in their API responses (even without a formal classification schema) while preserving BLOCKERs for applications that genuinely leak credentials or PII through agent-facing APIs. Under the revised model, DATA-Q1 BLOCKERs dropped from 14 to 7 services; 5 services moved to DATA-Q1 = INFO, and 2 to DATA-Q1 = RISK-SAFETY. This is reflected in the readiness distribution above (Remediation Required 16 → 13, Pilot-Ready (Safety Concerns) 2 → 6, Not Agent-Integrable 1 → 0).

### Portfolio Summary

| Metric | Value |
|--------|-------|
| Total Services Assessed | 34 |
| Services Ready for Agents (Agent-Ready + Pilot-Ready) | 15 (44%) |
| Services Requiring Remediation (Remediation Required + Not Agent-Integrable) | 13 (38%) |
| Cross-Cutting BLOCKERs (same blocker in 2+ repos) | 3 |
| Cross-Cutting RISKs (same risk in 3+ repos) | 27 |
| Services with Write-Enabled Agent Scope | 0 (0%) |
| Services with Read-Only Agent Scope | 34 (100%) |
| Total BLOCKERs across portfolio | 20 |
| Total unique BLOCKER question IDs | 3 (API-Q1, AUTH-Q1, DATA-Q1) |
| Total RISK-SAFETY findings across portfolio | 133 |
| Total RISK-QUALITY findings across portfolio | 242 |

### Repo Type Distribution

| Repo Type | Count | Percentage |
|-----------|-------|------------|
| application | 16 | 47% |
| monorepo | 18 | 53% |
| infrastructure-only | 0 | 0% |
| deployment-config | 0 | 0% |
| library | 0 | 0% |

### Blocker Heatmap by Section

| Section | Repos Blocked | % of Applicable Repos | Top Blockers |
|---------|--------------|----------------------|--------------|
| AUTH | 11 of 34 | 32% | AUTH-Q1 |
| DATA | 7 of 34 | 21% | DATA-Q1 (tiered B1 — credential leakage in agent-facing APIs) |
| API | 2 of 34 | 6% | API-Q1 |
| STATE | 0 of 34 | 0% | — |
| HITL | 0 of 34 | 0% | — |
| DISC | 0 of 34 | 0% | — |
| OBS | 0 of 34 | 0% | — |
| ENG | 0 of 25 | 0% | — |

> **Key Insight (updated)**: After the DATA-Q1 rubric revision, AUTH (specifically AUTH-Q1: Machine Identity Authentication) is now the #1 BLOCKER category at 11/34 (32%). DATA section BLOCKERs dropped from 14 to 7 (21%) — the remaining 7 all have concrete B1 findings (credentials/PHI/access-tokens actually returned unmasked by agent-facing API endpoints): the four Servarr apps leak their master ApiKey via `GET /config/host`, ThingsBoard returns device credentials plaintext via `GET /device/{id}/credentials`, Druid serializes Kafka/Kinesis ingestion credentials in supervisor specs, and Conductor embeds HTTP-task Authorization headers in workflow task output. These are actionable, code-level gaps — not generic "classification framework absent" findings.

### Readiness Snapshot

| Metric | Value |
|--------|-------|
| assessment_date | 2026-04-30 |
| total_services | 34 |
| agent_ready | 14 |
| pilot_ready | 1 |
| pilot_ready_safety_concerns | 6 |
| remediation_required | 13 |
| not_integrable | 0 |
| total_blockers | 20 |
| total_risks | 375 |
| total_risk_safety | 133 |
| total_risk_quality | 242 |
| total_infos | 824 |
| cross_cutting_blockers | 3 |
| cross_cutting_risks | 27 |
| cross_cutting_risk_safety | 9 |
| cross_cutting_risk_quality | 18 |
| portfolio_level_blockers | 1 |
| portfolio_level_risks | 4 |
| write_enabled_services | 0 |
| read_only_services | 34 |

---

## Cross-Cutting BLOCKERs — Same Blocker in 2+ Repos

> These are BLOCKER-severity questions that appear in 2 or more repositories.
> They represent portfolio-wide agentic readiness gaps requiring coordinated remediation.
> Questions scored as N/A for a service do not count as gaps for that service.

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER in 11 of 34 applicable services
- **Affected Services**: conductor-oss--conductor, greenshot--greenshot, hapifhir--hapi-fhir, Lidarr--Lidarr, Netflix--eureka, openzipkin--zipkin, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, ToolJet--ToolJet, umami-software--umami
- **Common Finding**: These services either have no authentication mechanism at all (Conductor, Eureka, Zipkin, Greenshot) or use a single shared API key with no per-agent principal attribution (Lidarr, Prowlarr, Radarr, Sonarr — the *arr suite uses `ApiKeyAuthenticationHandler` with a single GUID key). ToolJet and Umami use human-only JWT auth with no M2M flow. HAPI FHIR provides interceptor hooks but ships with no built-in machine identity authentication.
- **Root Cause Pattern**: Open-source projects prioritize human user authentication (browser-based login, single API key) over machine-to-machine identity. No project implements OAuth2 client credentials, per-agent API keys with principal attribution, or mTLS for agent identification.
- **Portfolio-Level Remediation**:
  - **Approach**: Per-service fix — each project needs its own authentication integration. No shared infrastructure exists across these independent projects.
  - **Immediate Action**: For the *arr suite (Lidarr, Prowlarr, Radarr, Sonarr), implement multi-key API authentication where each agent receives a unique key mapped to a named principal. For services with no auth (Conductor, Eureka, Zipkin), deploy an API Gateway (AWS API Gateway, Kong, or Envoy) in front of the service with API key or OAuth2 authentication. For ToolJet and Umami, implement an API key or OAuth2 client credentials flow for M2M access.
  - **Target State**: Every agent-facing API request carries an authenticated machine identity. Audit logs attribute each request to a specific agent principal.
  - **Estimated Effort**: Medium (2–8 weeks per service depending on existing auth infrastructure)
  - **Priority**: Critical — affects 11 services (32% of portfolio). Identity is the foundation for all other security controls.
  - **Dependencies**: None — this is the foundational blocker that should be resolved first.

### DATA-Q1: Sensitive Data Classification ⚡ (Tiered)

- **Severity**: BLOCKER in 7 of 34 applicable services (down from 14 under the binary rubric)
- **Affected Services (BLOCKER)**: apache--druid, conductor-oss--conductor, Lidarr--Lidarr, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, thingsboard--thingsboard
- **Also Affected at Lower Severity (not counted toward BLOCKER threshold)**: FlowiseAI--Flowise and hapifhir--hapi-fhir resolve to **RISK-SAFETY** under the tiered model (B2 / framework-hook defaults). Alluxio--alluxio, Graylog2--graylog2-server, scality--cloudserver, umami-software--umami, ToolJet--ToolJet resolve to **INFO** (B1 and B2 CLEAR; only B3 formal classification metadata absent).
- **Common Finding (BLOCKER repos only)**: In every BLOCKER case the application's agent-facing API returns sensitive fields in plaintext through a specific endpoint:
  - **Servarr family (Lidarr, Prowlarr, Radarr, Sonarr)**: `GET /api/v{1,3}/config/host` returns the master `ApiKey`, admin `Password`, `SslCertPassword`, and `ProxyPassword` unmasked. Provider settings (indexers, download clients) ARE correctly masked via the `PrivacyLevel.ApiKey`/`PrivacyLevel.Password` + `SchemaBuilder` pipeline; `HostConfigResource` bypasses this masking because it uses plain C# properties rather than `FieldDefinition`-decorated fields.
  - **thingsboard**: `GET /api/device/{deviceId}/credentials` returns `DeviceCredentials.credentialsValue` (access tokens, MQTT passwords, X.509 PEM) plaintext to any CUSTOMER_USER — no `@JsonIgnore`.
  - **apache/druid**: `GET /druid/indexer/v1/supervisor?full=true` returns `KafkaIndexTaskIOConfig.consumerProperties` (SASL/SSL credentials) and Kinesis AWS credentials serialized verbatim; no `PasswordProvider`-style abstraction.
  - **conductor-oss/conductor**: `HttpTask.java:138` persists HTTP response headers (including `Authorization`) into task output via `task.addOutput("response", response.asMap())`; Workflow/Task REST endpoints return input/output payloads unredacted.
- **Root Cause Pattern**: These are **coverage gaps**, not missing frameworks. In several cases (Servarr family, Flowise, Graylog) a masking primitive already exists in the codebase but is not applied on every path. The remediation is localized code changes, not cross-cutting governance work.
- **Portfolio-Level Remediation**:
  - **Approach**: Per-service fix — most of these are small, targeted code changes (add `@JsonIgnore`, extend masking to non-provider resources, introduce a summary DTO for credentials endpoints).
  - **Servarr family (4 services)**: Single shared fix — extend `SchemaBuilder` masking (or a simple `[Sensitive]` attribute) to `HostConfigResource`. Remediation for one app applies directly to the other three.
  - **thingsboard**: Apply `@JsonIgnore` to `credentialsValue`; introduce a `DeviceCredentialsSummary` DTO; consider restricting credential-reveal endpoints to TENANT_ADMIN only.
  - **druid**: Filter sensitive keys from `consumerProperties` serialization (or introduce a filtered DTO); integrate with a secrets manager for inline credentials.
  - **conductor**: Mask sensitive HTTP headers in `HttpTask` before `addOutput`; apply response-level field redaction on Task/Workflow DTOs; enforce `maskedFields` at definition-validation time.
  - **Target State**: No agent-facing API endpoint returns credential values in plaintext. Sensitive-field masking is consistent across every code path that serializes domain objects.
  - **Estimated Effort**: Low-to-Medium per service (1–4 weeks). The Servarr-family shared fix is a single multi-repo change.
  - **Priority**: High — the remaining 7 DATA-Q1 BLOCKERs are credential-exfiltration paths. Remediation is localized and achievable in parallel with AUTH-Q1 work.
  - **Dependencies**: Independent of AUTH-Q1 (the masking fix is a code change, not an authorization change). AUTH-Q1 resolution strengthens overall posture but does not gate these fixes.

### API-Q1: Documented API Interface (Notable but Below Cross-Cutting Threshold for Most)

> **Note**: API-Q1 is a BLOCKER in only 2 services (greenshot--greenshot and ToolJet--ToolJet). It meets the 2+ repo threshold for cross-cutting.

- **Severity**: BLOCKER in 2 of 34 applicable services
- **Affected Services**: greenshot--greenshot, ToolJet--ToolJet
- **Common Finding**: Greenshot is a Windows desktop GUI application with no programmatic API — agents cannot interact with it without UI automation (RPA). ToolJet exposes a NestJS REST API via 50+ controller modules but has no OpenAPI/Swagger specification or machine-discoverable API documentation.
- **Root Cause Pattern**: Different root causes — Greenshot fundamentally lacks any API surface (desktop GUI), while ToolJet has an extensive API but no machine-readable documentation.
- **Portfolio-Level Remediation**:
  - **Approach**: Per-service fix
  - **Immediate Action**: For ToolJet, enable NestJS Swagger auto-generation (`@nestjs/swagger`) to produce an OpenAPI spec from existing controller decorators. For Greenshot, evaluate whether a CLI wrapper or local REST API around screenshot/annotation capabilities would provide agent-accessible functionality.
  - **Target State**: ToolJet has a published OpenAPI specification. Greenshot has a programmatic interface (CLI or local API) if agent integration is desired.
  - **Estimated Effort**: Low for ToolJet (1–2 weeks), High for Greenshot (requires architectural change)
  - **Priority**: Medium — affects only 2 services
  - **Dependencies**: None

---

## Cross-Cutting RISKs

### Cross-Cutting RISK-SAFETY — Same Safety Risk in 3+ Repos

> These are RISK-SAFETY questions that appear in 3 or more repositories.
> They represent portfolio-wide agent safety gaps requiring coordinated attention.
> Questions scored as N/A for a service do not count as gaps for that service.

#### AUTH-Q6: Immutable Audit Logging

- **Severity**: RISK-SAFETY in 17 of 34 applicable services
- **Affected Services**: Alluxio--alluxio, apache--druid, conductor-oss--conductor, FlowiseAI--Flowise, Graylog2--graylog2-server, hapifhir--hapi-fhir, Lidarr--Lidarr, Netflix--eureka, openzipkin--zipkin, Prowlarr--Prowlarr, Radarr--Radarr, scality--backbeat, scality--cloudserver, Sonarr--Sonarr, thingsboard--thingsboard, ToolJet--ToolJet, umami-software--umami
- **Common Finding**: Services lack immutable, tamper-evident audit logs for agent actions. Logging exists but is typically mutable (standard application logs in files or databases), not shipped to a centralized immutable store, and not structured for forensic analysis of agent behavior.
- **Compensating Controls**: Ship logs to CloudWatch Logs or S3 with object lock for immutability. Enable CloudTrail for AWS API calls.
- **Portfolio-Level Recommendation**: Implement a centralized audit logging pipeline — each service emits structured audit events to an immutable log store (e.g., CloudWatch Logs with retention lock, S3 with object lock). Standardize audit event schema across services.
- **Estimated Effort**: Medium

#### STATE-Q1: Compensation and Rollback

- **Severity**: RISK-SAFETY in 17 of 34 applicable services
- **Affected Services**: Alluxio--alluxio, apache--druid, conductor-oss--conductor, FlowiseAI--Flowise, Graylog2--graylog2-server, hapifhir--hapi-fhir, Lidarr--Lidarr, Netflix--eureka, openzipkin--zipkin, Prowlarr--Prowlarr, Radarr--Radarr, scality--backbeat, scality--cloudserver, Sonarr--Sonarr, thingsboard--thingsboard, ToolJet--ToolJet, umami-software--umami
- **Common Finding**: Services lack compensation or rollback mechanisms for agent-initiated state changes. Under read-only agent scope this is a safety concern rather than a blocker — agents are not performing write operations, but the absence of rollback means any future write-enabled agent integration would lack safety nets.
- **Compensating Controls**: Maintain read-only agent scope until rollback mechanisms are in place. Implement database-level point-in-time recovery (PostgreSQL PITR, MongoDB oplog).
- **Portfolio-Level Recommendation**: For each stateful service, implement at minimum database-level point-in-time recovery. For services that will eventually support write-enabled agents, implement application-level compensation (undo endpoints, soft-delete with restore).
- **Estimated Effort**: High

#### DATA-Q2: Data Residency and Sovereignty

- **Severity**: RISK-SAFETY in 16 of 34 applicable services
- **Affected Services**: Alluxio--alluxio, apache--druid, conductor-oss--conductor, FlowiseAI--Flowise, Graylog2--graylog2-server, hapifhir--hapi-fhir, Lidarr--Lidarr, openzipkin--zipkin, Prowlarr--Prowlarr, Radarr--Radarr, scality--backbeat, scality--cloudserver, Sonarr--Sonarr, thingsboard--thingsboard, ToolJet--ToolJet, umami-software--umami
- **Common Finding**: No data residency or sovereignty controls are implemented. Data can be stored in any region without enforcement. No geographic access restrictions for agent queries.
- **Compensating Controls**: Deploy to specific AWS regions. Use VPC endpoints to restrict data access to specific network boundaries.
- **Portfolio-Level Recommendation**: Define a data residency policy. For each service, configure deployment to enforce region-specific data storage using AWS region-locked S3 buckets, RDS regional deployment, and VPC-scoped access.
- **Estimated Effort**: Medium

#### AUTH-Q3: Action-Level Authorization

- **Severity**: RISK-SAFETY in 12 of 34 applicable services
- **Affected Services**: conductor-oss--conductor, greenshot--greenshot, hapifhir--hapi-fhir, Lidarr--Lidarr, Netflix--eureka, openzipkin--zipkin, Prowlarr--Prowlarr, Radarr--Radarr, scality--backbeat, Sonarr--Sonarr, ToolJet--ToolJet, umami-software--umami
- **Common Finding**: No action-level authorization model exists. Either all authenticated users have the same access (binary auth), or no authorization checks are performed at the endpoint/action level. Agents cannot be restricted to specific operations (e.g., read-only on certain resources).
- **Compensating Controls**: Restrict agent scope to read-only at the gateway level. Implement endpoint-level allow-lists for agent identities.
- **Portfolio-Level Recommendation**: Implement RBAC or ABAC with per-action authorization checks. Define agent roles with explicit action permissions (e.g., "agent-reader" can GET but not POST/PUT/DELETE).
- **Estimated Effort**: High

#### AUTH-Q2: Scoped Permissions (Least Privilege)

- **Severity**: RISK-SAFETY in 14 of 34 applicable services
- **Affected Services**: Alluxio--alluxio, conductor-oss--conductor, greenshot--greenshot, hapifhir--hapi-fhir, Lidarr--Lidarr, Netflix--eureka, openzipkin--zipkin, Prowlarr--Prowlarr, Radarr--Radarr, scality--backbeat, Sonarr--Sonarr, thingsboard--thingsboard, ToolJet--ToolJet, umami-software--umami
- **Common Finding**: Services lack fine-grained permission scoping for agent identities. Either no permission model exists (service is open), or permissions are binary (all-or-nothing API key), preventing least-privilege agent access.
- **Compensating Controls**: Use API Gateway resource policies to restrict agent access to specific endpoints. Implement read-only agent scope at the gateway level.
- **Portfolio-Level Recommendation**: Implement RBAC or ABAC in each service to support agent-specific permission scopes. Define a minimum agent role per service with only the permissions needed for the agent's use case.
- **Estimated Effort**: High

#### AUTH-Q7: Agent Identity Suspension

- **Severity**: RISK-SAFETY in 14 of 34 applicable services
- **Affected Services**: Alluxio--alluxio, conductor-oss--conductor, hapifhir--hapi-fhir, Lidarr--Lidarr, Netflix--eureka, openzipkin--zipkin, Prowlarr--Prowlarr, Radarr--Radarr, scality--backbeat, scality--cloudserver, serverless--serverless, Sonarr--Sonarr, ToolJet--ToolJet, umami-software--umami
- **Common Finding**: No mechanism to immediately suspend or revoke a specific agent's access. Services that use a single shared API key cannot revoke one agent without affecting all consumers.
- **Compensating Controls**: Deploy API Gateway with per-agent API keys that can be individually revoked. Maintain an agent identity registry with kill-switch capability.
- **Portfolio-Level Recommendation**: Implement per-agent credential issuance with individual revocation capability. This is a prerequisite for safe agent deployment.
- **Estimated Effort**: Medium

#### DATA-Q6: PII Redaction in Logs

- **Severity**: RISK-SAFETY in 14 of 34 applicable services
- **Affected Services**: Alluxio--alluxio, apache--druid, conductor-oss--conductor, Graylog2--graylog2-server, hapifhir--hapi-fhir, Lidarr--Lidarr, Prowlarr--Prowlarr, Radarr--Radarr, scality--backbeat, scality--cloudserver, Sonarr--Sonarr, thingsboard--thingsboard, ToolJet--ToolJet, umami-software--umami
- **Common Finding**: Services log user data (IP addresses, usernames, object keys, request paths containing identifiers) without PII redaction. Logs may expose sensitive data to agent systems that have log access.
- **Compensating Controls**: Restrict agent access to application logs. Implement log scrubbing before forwarding to agent-accessible systems.
- **Portfolio-Level Recommendation**: Implement PII redaction filters in each service's logging pipeline. Standardize a redaction library or log processor across the portfolio.
- **Estimated Effort**: Medium

#### STATE-Q4: Circuit Breakers and Resilience

- **Severity**: RISK-SAFETY in 14 of 25 applicable services (9 services have N/A)
- **Affected Services**: Alluxio--alluxio, apache--druid, FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, OpenAPITools--openapi-generator, Prowlarr--Prowlarr, Radarr--Radarr, scality--cloudserver, serverless--serverless, Sonarr--Sonarr, thingsboard--thingsboard, ToolJet--ToolJet, umami-software--umami
- **Common Finding**: No circuit breaker patterns implemented for downstream service calls. Agent-triggered cascading failures could propagate through service dependencies without protection.
- **Compensating Controls**: Implement rate limiting at the API gateway level. Use AWS Application Load Balancer health checks to detect service degradation.
- **Portfolio-Level Recommendation**: Add circuit breaker libraries (e.g., resilience4j for Java, opossum for Node.js) to services with downstream dependencies. Configure timeout and retry budgets for agent-invoked operations.
- **Estimated Effort**: Medium

#### STATE-Q5: Rate Limiting and Throttling

- **Severity**: RISK-SAFETY in 14 of 34 applicable services
- **Affected Services**: Alluxio--alluxio, conductor-oss--conductor, Graylog2--graylog2-server, hapifhir--hapi-fhir, Lidarr--Lidarr, Netflix--eureka, openzipkin--zipkin, Prowlarr--Prowlarr, Radarr--Radarr, scality--backbeat, serverless--serverless, Sonarr--Sonarr, ToolJet--ToolJet, umami-software--umami
- **Common Finding**: No rate limiting or throttling on API endpoints. Agent traffic storms could overwhelm services without protection.
- **Compensating Controls**: Deploy AWS API Gateway or WAF with rate limiting rules in front of each service. Configure per-client throttling limits.
- **Portfolio-Level Recommendation**: Implement application-level rate limiting or deploy API Gateway with usage plans. Define agent-specific rate limits separate from human user limits.
- **Estimated Effort**: Medium

### Cross-Cutting RISK-QUALITY — Same Quality Risk in 3+ Repos

> These are RISK-QUALITY questions that appear in 3 or more repositories.
> They represent portfolio-wide quality patterns to address as capacity allows.
> Questions scored as N/A for a service do not count as gaps for that service.

#### DISC-Q1: Schema Versioning and API Contracts

- **Severity**: RISK-QUALITY in 32 of 34 applicable services
- **Affected Services**: All services except getlift--lift and OBS-related (32 total — nearly universal)
- **Common Finding**: No formal schema versioning or breaking-change detection in CI. APIs may change without consumer notification. Agent tool bindings could break silently on library/API updates.
- **Portfolio-Level Recommendation**: Implement semantic versioning enforcement and breaking-change detection in CI for all services. For libraries, use consumer-driven contract testing. For APIs, implement OpenAPI diff checks in PR pipelines.
- **Estimated Effort**: Medium

#### OBS-Q1: Distributed Tracing and Structured Logging

- **Severity**: RISK-QUALITY in 18 of 34 applicable services
- **Affected Services**: Alluxio--alluxio, apache--druid, conductor-oss--conductor, FlowiseAI--Flowise, Graylog2--graylog2-server, hapifhir--hapi-fhir, Lidarr--Lidarr, Netflix--eureka, openzipkin--zipkin, Prowlarr--Prowlarr, Radarr--Radarr, scality--backbeat, scality--cloudserver, serverless--serverless, Sonarr--Sonarr, thingsboard--thingsboard, ToolJet--ToolJet, umami-software--umami
- **Common Finding**: Incomplete distributed tracing or unstructured logging. Services lack trace ID propagation, structured JSON logging, or integration with centralized observability platforms.
- **Portfolio-Level Recommendation**: Standardize on OpenTelemetry for distributed tracing. Implement structured JSON logging with consistent field names across all services.
- **Estimated Effort**: Medium

#### ENG-Q2: CI/CD with API Contract Testing

- **Severity**: RISK-QUALITY in 18 of 25 applicable services (9 N/A)
- **Affected Services**: Alluxio--alluxio, apache--druid, conductor-oss--conductor, FlowiseAI--Flowise, Graylog2--graylog2-server, hapifhir--hapi-fhir, Lidarr--Lidarr, Netflix--eureka, openzipkin--zipkin, Prowlarr--Prowlarr, Radarr--Radarr, scality--backbeat, scality--cloudserver, serverless--serverless, Sonarr--Sonarr, thingsboard--thingsboard, ToolJet--ToolJet, umami-software--umami
- **Common Finding**: CI/CD pipelines lack API contract testing. No automated verification that API changes don't break agent tool bindings.
- **Portfolio-Level Recommendation**: Add API contract testing (Pact, Schemathesis, or OpenAPI diff) to CI pipelines for all services with HTTP APIs.
- **Estimated Effort**: Medium

#### OBS-Q2: Alerting on Error Rates and Latency

- **Severity**: RISK-QUALITY in 17 of 34 applicable services
- **Affected Services**: Alluxio--alluxio, apache--druid, conductor-oss--conductor, FlowiseAI--Flowise, Graylog2--graylog2-server, hapifhir--hapi-fhir, Lidarr--Lidarr, Netflix--eureka, openzipkin--zipkin, Prowlarr--Prowlarr, Radarr--Radarr, scality--backbeat, serverless--serverless, Sonarr--Sonarr, thingsboard--thingsboard, ToolJet--ToolJet, umami-software--umami
- **Common Finding**: No alerting on API error rates or latency degradation. Agent-caused issues would go undetected until user impact.
- **Portfolio-Level Recommendation**: Implement CloudWatch alarms or equivalent for error rate and latency thresholds on agent-facing endpoints.
- **Estimated Effort**: Low

#### API-Q3: Structured Error Responses

- **Severity**: RISK-QUALITY in 16 of 34 applicable services
- **Affected Services**: Alluxio--alluxio, apache--druid, conductor-oss--conductor, FlowiseAI--Flowise, Graylog2--graylog2-server, hapifhir--hapi-fhir, Lidarr--Lidarr, Netflix--eureka, openzipkin--zipkin, Prowlarr--Prowlarr, Radarr--Radarr, scality--backbeat, serverless--serverless, Sonarr--Sonarr, ToolJet--ToolJet, umami-software--umami
- **Common Finding**: Error responses are inconsistent — mix of HTML error pages, unstructured text, and varying JSON formats. Agents cannot reliably parse error responses to determine retry vs. abort decisions.
- **Portfolio-Level Recommendation**: Standardize on RFC 7807 (Problem Details for HTTP APIs) or a consistent error JSON schema across all services.
- **Estimated Effort**: Medium

#### ENG-Q3: Rollback Capability

- **Severity**: RISK-QUALITY in 16 of 25 applicable services (9 N/A)
- **Affected Services**: Alluxio--alluxio, apache--druid, conductor-oss--conductor, FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, Netflix--eureka, openzipkin--zipkin, Prowlarr--Prowlarr, Radarr--Radarr, scality--backbeat, scality--cloudserver, Sonarr--Sonarr, thingsboard--thingsboard, ToolJet--ToolJet, umami-software--umami
- **Common Finding**: No automated rollback capability for deployments. If an agent-interacting version introduces a regression, manual intervention is required to restore service.
- **Portfolio-Level Recommendation**: Implement blue/green or canary deployments with automated rollback triggers based on health check failures.
- **Estimated Effort**: Medium

#### ENG-Q4: API Test Coverage

- **Severity**: RISK-QUALITY in 16 of 25 applicable services (9 N/A)
- **Affected Services**: Alluxio--alluxio, apache--druid, conductor-oss--conductor, FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, Netflix--eureka, OpenAPITools--openapi-generator, Prowlarr--Prowlarr, Radarr--Radarr, scality--backbeat, serverless--serverless, Sonarr--Sonarr, thingsboard--thingsboard, ToolJet--ToolJet, umami-software--umami
- **Common Finding**: Insufficient API test coverage for agent-facing endpoints. Critical API paths lack automated tests that would catch regressions before deployment.
- **Portfolio-Level Recommendation**: Establish minimum API test coverage targets (≥80%) for agent-facing endpoints. Prioritize testing of endpoints that agents will call most frequently.
- **Estimated Effort**: Medium

#### HITL-Q3: Sandbox/Staging Environment

- **Severity**: RISK-QUALITY in 16 of 34 applicable services
- **Affected Services**: Alluxio--alluxio, apache--druid, conductor-oss--conductor, FlowiseAI--Flowise, Graylog2--graylog2-server, Lidarr--Lidarr, Netflix--eureka, openzipkin--zipkin, Prowlarr--Prowlarr, Radarr--Radarr, scality--backbeat, serverless--serverless, Sonarr--Sonarr, thingsboard--thingsboard, ToolJet--ToolJet, umami-software--umami
- **Common Finding**: No sandbox or staging environment for agent testing. Agent behavior must be validated directly in production.
- **Portfolio-Level Recommendation**: Provision staging environments with synthetic data for agent testing. Use Docker Compose or Kubernetes namespaces for lightweight staging.
- **Estimated Effort**: Medium

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface

- **Severity**: RISK-QUALITY in 15 of 25 applicable services (9 N/A)
- **Affected Services**: Alluxio--alluxio, apache--druid, conductor-oss--conductor, FlowiseAI--Flowise, Graylog2--graylog2-server, Netflix--eureka, openzipkin--zipkin, Prowlarr--Prowlarr, Radarr--Radarr, scality--backbeat, scality--cloudserver, Sonarr--Sonarr, thingsboard--thingsboard, ToolJet--ToolJet, umami-software--umami
- **Common Finding**: No IaC governance for agent-facing infrastructure. Infrastructure is either manually configured or defined in non-validated IaC without drift detection.
- **Portfolio-Level Recommendation**: Implement IaC (Terraform/CDK) for all agent-facing infrastructure with drift detection and automated compliance checks.
- **Estimated Effort**: High

#### API-Q2: Machine-Readable API Specification

- **Severity**: RISK-QUALITY in 13 of 34 applicable services
- **Affected Services**: Alluxio--alluxio, apache--druid, conductor-oss--conductor, FlowiseAI--Flowise, hapifhir--hapi-fhir, Lidarr--Lidarr, Netflix--eureka, openzipkin--zipkin, scality--backbeat, scality--cloudserver, serverless--serverless, ToolJet--ToolJet, umami-software--umami
- **Common Finding**: No machine-readable API specification (OpenAPI, AsyncAPI, or GraphQL SDL) available for automated tool binding generation. Agents must rely on documentation or source code to discover endpoints.
- **Portfolio-Level Recommendation**: Generate OpenAPI specifications for all REST APIs. Publish specs as part of the build pipeline.
- **Estimated Effort**: Medium

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data

- **Severity**: RISK-QUALITY in 13 of 17 applicable services (17 N/A)
- **Affected Services**: Alluxio--alluxio, apache--druid, conductor-oss--conductor, Graylog2--graylog2-server, Lidarr--Lidarr, openzipkin--zipkin, Prowlarr--Prowlarr, Radarr--Radarr, scality--backbeat, Sonarr--Sonarr, thingsboard--thingsboard, ToolJet--ToolJet, umami-software--umami
- **Common Finding**: Data at rest is not encrypted by default. Databases (SQLite, PostgreSQL, MongoDB) used without encryption at rest configuration.
- **Portfolio-Level Recommendation**: Enable encryption at rest for all data stores. Use AWS KMS for key management. Configure RDS encryption, EBS encryption, and S3 default encryption.
- **Estimated Effort**: Low

#### DATA-Q5: Temporal Metadata and Freshness

- **Severity**: RISK-QUALITY in 12 of 19 applicable services (15 N/A)
- **Affected Services**: Alluxio--alluxio, Graylog2--graylog2-server, hapifhir--hapi-fhir, Lidarr--Lidarr, openzipkin--zipkin, Prowlarr--Prowlarr, Radarr--Radarr, scality--backbeat, Sonarr--Sonarr, thingsboard--thingsboard, ToolJet--ToolJet, umami-software--umami
- **Common Finding**: Insufficient temporal metadata (created_at, updated_at, version) on API responses. Agents cannot determine data freshness or detect stale reads.
- **Portfolio-Level Recommendation**: Add temporal metadata (timestamps, version headers) to all API responses. Implement ETags for cache validation.
- **Estimated Effort**: Low

#### AUTH-Q5: Credential Management

- **Severity**: RISK-QUALITY in 10 of 34 applicable services
- **Affected Services**: greenshot--greenshot, Lidarr--Lidarr, openzipkin--zipkin, Prowlarr--Prowlarr, Radarr--Radarr, scality--cloudserver, Sonarr--Sonarr, thingsboard--thingsboard, ToolJet--ToolJet, umami-software--umami
- **Common Finding**: Credentials stored in plaintext configuration files, environment variables without secrets management, or hardcoded in source code. No integration with secrets managers (AWS Secrets Manager, HashiCorp Vault).
- **Portfolio-Level Recommendation**: Migrate all credentials to a secrets management solution (AWS Secrets Manager or Parameter Store). Implement credential rotation policies.
- **Estimated Effort**: Medium

#### DATA-Q4: System of Record Designations

- **Severity**: RISK-QUALITY in 10 of 16 applicable services (18 N/A)
- **Affected Services**: Alluxio--alluxio, FlowiseAI--Flowise, Graylog2--graylog2-server, hapifhir--hapi-fhir, Lidarr--Lidarr, openzipkin--zipkin, Prowlarr--Prowlarr, thingsboard--thingsboard, ToolJet--ToolJet, umami-software--umami
- **Common Finding**: No clear system-of-record designations for data entities. Agents cannot determine which service is authoritative for a given data entity, risking stale or conflicting data.
- **Portfolio-Level Recommendation**: Document system-of-record designations for each data entity in a portfolio-level data catalog. Add source-of-truth indicators to API responses.
- **Estimated Effort**: Low

#### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: RISK-QUALITY in 8 of 34 applicable services
- **Affected Services**: Lidarr--Lidarr, openzipkin--zipkin, Prowlarr--Prowlarr, Radarr--Radarr, scality--cloudserver, Sonarr--Sonarr, thingsboard--thingsboard, ToolJet--ToolJet
- **Common Finding**: No identity propagation across service boundaries. When a service calls a downstream service on behalf of an agent, the agent's identity is lost.
- **Portfolio-Level Recommendation**: Implement identity propagation headers (e.g., `X-Agent-Id`, `X-Forwarded-For-Agent`) across service boundaries.
- **Estimated Effort**: Medium

#### DATA-Q3: Selective Query Support

- **Severity**: RISK-QUALITY in 7 of 18 applicable services (16 N/A)
- **Affected Services**: Alluxio--alluxio, FlowiseAI--Flowise, hapifhir--hapi-fhir, Lidarr--Lidarr, Netflix--eureka, ToolJet--ToolJet, umami-software--umami
- **Common Finding**: Limited ability for agents to request only the fields they need. APIs return full entity payloads, increasing data exposure and bandwidth.
- **Portfolio-Level Recommendation**: Implement field selection (GraphQL-style `fields` parameter or sparse fieldsets) on API endpoints to minimize data exposure for agent queries.
- **Estimated Effort**: Medium

#### API-Q6: Asynchronous Operation Support

- **Severity**: RISK-QUALITY in 4 of 16 applicable services (18 N/A)
- **Affected Services**: FlowiseAI--Flowise, Lidarr--Lidarr, scality--backbeat, scality--cloudserver
- **Common Finding**: Long-running operations (file processing, replication, media management) lack async operation patterns (request/poll, webhook callbacks). Agents must block waiting for completion.
- **Portfolio-Level Recommendation**: Implement async operation patterns with job IDs and polling endpoints for operations that take >5 seconds.
- **Estimated Effort**: Medium

#### STATE-Q2: Queryable Current State

- **Severity**: RISK-QUALITY in 4 of 17 applicable services (17 N/A)
- **Affected Services**: Alluxio--alluxio, Lidarr--Lidarr, ToolJet--ToolJet, umami-software--umami
- **Common Finding**: Limited ability to query current system state for agent decision-making.
- **Portfolio-Level Recommendation**: Implement health/status endpoints that expose queryable system state for agent consumption.
- **Estimated Effort**: Low

---

## Service Dependency Map

> This portfolio consists of 34 independent open-source project mirrors — they are NOT
> interconnected microservices within a single system. No `dependency_overrides` were
> provided in the portfolio configuration, and no inter-service dependencies were
> inferable from the individual ARA reports because each project is a standalone
> application with no runtime dependencies on other projects in the portfolio.

### Dependency Analysis Summary

- **Explicit dependencies provided**: None (no `dependency_overrides` in portfolio config)
- **Inferred dependencies**: None — each project is an independent open-source repository
- **Inter-service communication**: Not applicable — projects do not call each other
- **Shared data stores**: None identified across projects
- **Shared infrastructure**: None — each project has its own deployment model

### Observations

While no inter-service dependencies exist in this portfolio, several **technology family clusters** share common patterns:

1. **\*arr Suite** (Lidarr, Prowlarr, Radarr, Sonarr) — These 4 C# projects share the same codebase architecture, including `ApiKeyAuthenticationHandler`, SQLite/PostgreSQL persistence, and identical BLOCKER patterns (AUTH-Q1, DATA-Q1). Remediation patterns developed for one *arr application can likely be applied to all four with minimal adaptation.

2. **Scality Pair** (scality--backbeat, scality--cloudserver) — Both are JavaScript/Node.js storage services from the same organization. Backbeat depends on CloudServer in production, but that dependency is not visible in this portfolio's assessment since they are assessed as independent repositories.

3. **Frontend Templates** (akveo--ngx-admin, coreui--coreui-free-angular-admin-template, realworld-apps--angular-realworld-example-app) — All Angular frontend SPAs with Agent-Ready profiles and similar surface flag patterns (all false).

4. **Build Tools/Libraries** (gulpjs--gulp, webpack--webpack, tqdm--tqdm, arrow-py--arrow, iterative--dvc) — CLI tools and libraries with Agent-Ready profiles and dev-library-application overrides.

> **Recommendation for Production Portfolios**: For production microservice portfolios with
> inter-service dependencies, add `dependency_overrides` to the portfolio configuration to
> enable dependency-aware analysis — including identification of high-risk foundation services,
> transitive blocker propagation, and shared infrastructure impacts.

---

## Portfolio Remediation Guidance

> Portfolio context: 34 open-source project mirrors for ATX TD validation across multiple languages, architectures, and domains. Since these are independent open-source projects (not interconnected microservices), per-service remediation is more appropriate than platform-level fixes. However, remediation patterns can be shared across technology family clusters.

### Remediation Priority Order

Remediation of cross-cutting BLOCKERs should follow this general priority:

1. **Identity and Access** — Resolve AUTH-Q1 (Machine Identity Authentication) first. You cannot enforce any other security control without machine identity and scoped permissions.
2. **Data Integrity** — Resolve DATA-Q1 (Sensitive Data Classification — tiered B1/B2/B3) second for the 7 BLOCKER services. Remediation is localized: mask specific endpoints that leak credentials (Servarr `HostConfigResource`, thingsboard `DeviceCredentials`, druid supervisor specs, conductor HTTP-task output). The remaining 2 services at RISK-SAFETY (Flowise, hapi-fhir) need follow-up but not before pilot; the 5 INFO-level services require no immediate action.
3. **API Surface** — Resolve API-Q1 (Documented API Interface) third for the 2 affected services. Ensure a stable, documented integration surface for agent tools.

### Coordinated Remediation Plan

#### Group 1: Identity Foundation (AUTH-Q1)

**BLOCKERs addressed**: AUTH-Q1 (Machine Identity Authentication)
**Services affected**: conductor-oss--conductor, greenshot--greenshot, hapifhir--hapi-fhir, Lidarr--Lidarr, Netflix--eureka, openzipkin--zipkin, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, ToolJet--ToolJet, umami-software--umami (11 services)

- **What to do**:
  - **\*arr suite (Lidarr, Prowlarr, Radarr, Sonarr)**: Modify `ApiKeyAuthenticationHandler` to support multiple named API keys. Each agent gets a unique key mapped to a `ClaimsPrincipal` with identity claims (`agent_id`, `agent_name`). Estimated 2–4 weeks — pattern reusable across all 4 services.
  - **No-auth services (Conductor, Eureka, Zipkin)**: Deploy AWS API Gateway in front of each service with API key authentication and principal attribution via `X-Forwarded-Agent-Id` header. Estimated 2–4 weeks each.
  - **Human-only auth (ToolJet, Umami)**: Add OAuth2 client credentials flow or named API key system alongside existing JWT auth. Estimated 4–6 weeks each.
  - **Framework (HAPI FHIR)**: Implement a SMART on FHIR or OAuth2 bearer token authentication interceptor. Estimated 4–6 weeks.
  - **Desktop app (Greenshot)**: Requires architectural change — build a CLI or local REST API wrapper. Consider descoping from agent integration. Estimated 8–12 weeks if pursued.
- **Expected outcome**: All 11 services authenticate agents with unique, auditable machine identities.
- **Effort**: Medium per service (2–6 weeks), High cumulative (11 services)

#### Group 2: Data Protection (DATA-Q1)

**BLOCKERs addressed**: DATA-Q1 (Sensitive Data Classification) — tiered B1/B2/B3
**Services affected (BLOCKER, 7)**: apache--druid, conductor-oss--conductor, Lidarr--Lidarr, Prowlarr--Prowlarr, Radarr--Radarr, Sonarr--Sonarr, thingsboard--thingsboard
**Services affected at lower severity**: FlowiseAI--Flowise, hapifhir--hapi-fhir (RISK-SAFETY, not BLOCKER); Alluxio--alluxio, Graylog2--graylog2-server, scality--cloudserver, umami-software--umami, ToolJet--ToolJet (INFO)

- **What to do (BLOCKER remediation)**:
  - **Servarr family (Lidarr, Prowlarr, Radarr, Sonarr — single shared fix)**: Mask `ApiKey`, `Password`, `PasswordConfirmation`, `SslCertPassword`, `ProxyPassword` in `HostConfigResourceMapper.ToResource()`. The existing `SchemaBuilder`/`PrivacyLevel` masking pipeline (which correctly protects provider settings) needs to be extended to `HostConfigResource` (plain C# properties today). Estimated 1–2 weeks; pattern reusable across all 4 apps.
  - **thingsboard**: Apply `@JsonIgnore` to `DeviceCredentials.credentialsValue`; introduce a `DeviceCredentialsSummary` DTO that returns `credentialsType` only (no value). Gate any value-revealing endpoint behind TENANT_ADMIN + explicit "reveal" intent. 2–4 weeks.
  - **apache/druid**: Filter sensitive `consumerProperties` keys in Kafka/Kinesis supervisor spec serialization; annotate `awsAssumedRoleArn`/`awsExternalId` with `@JsonIgnore` on read paths. Longer-term: integrate with a secrets manager so supervisor specs reference secret names, not inline values. 3–6 weeks.
  - **conductor**: Mask sensitive HTTP headers (`Authorization`, `Cookie`, `X-Api-Key`, etc.) in `HttpTask.java:138` before `task.addOutput("response", ...)`. Apply response-level field redaction on `Task`/`Workflow` REST DTOs via a Jackson `@JsonFilter` or response-shaping hook. Enforce `WorkflowDef.maskedFields` at definition-validation time for known-sensitive patterns. 3–6 weeks.
- **What to do (RISK-SAFETY follow-up)**:
  - **Flowise**: Default `getCredentialById` to returning the encrypted blob; require `reveal=true` + additional auth to decrypt. Mask `apiKey` in list responses (return truncated prefix).
  - **hapi-fhir (deployer-level)**: Treat `AuthorizationInterceptor` registration as a required deployment step; configure `SearchNarrowingInterceptor` with compartment narrowing; apply `Meta.security` labels per HL7 confidentiality taxonomy.
- **Expected outcome**: No agent-facing API endpoint returns credential values or PHI in plaintext. Sensitive-field masking is consistent across every code path that serializes domain objects.
- **Effort**: Low-to-Medium per service (1–6 weeks). The Servarr-family fix is a single multi-repo change. Cumulative effort across all 7 BLOCKER repos: ~15–25 weeks of engineering time, parallelizable.

#### Group 3: API Documentation (API-Q1)

**BLOCKERs addressed**: API-Q1 (Documented API Interface)
**Services affected**: greenshot--greenshot, ToolJet--ToolJet (2 services)

- **What to do**:
  - **ToolJet**: Enable `@nestjs/swagger` module to auto-generate OpenAPI spec from existing controller decorators. Add `@ApiOperation`, `@ApiResponse` decorators to controllers. Publish spec at `/api/docs`.
  - **Greenshot**: Evaluate agent integration requirements. If agent access is needed, build a local REST API or CLI wrapper around screenshot/annotation capabilities. Otherwise, descope from agent integration.
- **Expected outcome**: ToolJet has machine-discoverable API documentation. Greenshot has a decision on agent integration path.
- **Effort**: Low for ToolJet (1–2 weeks), High for Greenshot (8–12 weeks if pursued)

---

## Agentic Program Recommendations

> These are engagement-level recommendations based on the portfolio's agentic readiness
> profile. Discuss with your AWS Solutions Architect to determine eligibility and timing.

| Program | Relevance | Trigger Findings | Suggested Timing | Next Step |
|---------|-----------|-----------------|------------------|-----------|
| AXE (Agentic Experience Workshop) | 15 services are Agent-Ready or Pilot-Ready | 14 Agent-Ready + 1 Pilot-Ready ≥ 3 threshold | After cross-cutting BLOCKER remediation | Request engagement via AWS SA |
| EBA on Agentic AI | Systemic cross-cutting blockers across 7–11 repos | AUTH-Q1 BLOCKER in 11 repos exceeds the 5-repo threshold; DATA-Q1 BLOCKER in 7 repos (down from 14) still exceeds the 5-repo threshold | After AXE engagement | Request EBA via AWS SA |
| AgentStorming | Portfolio context describes validation/testing, not a clear agent use case | No clear agent scope defined for "ATX TD validation" portfolio | Before AXE | Request workshop via AWS SA |

### Program Details

#### AgentStorming

- **Why triggered**: The portfolio context ("34 open-source project mirrors for ATX TD validation across multiple languages, architectures, and domains") describes a testing/validation objective rather than a clear agent use case. No specific agent integration scenarios are defined for individual services. AgentStorming would help identify which services should be prioritized for agent integration and what agent workflows would deliver the most value.
- **What it provides**: A structured workshop that identifies where agentic AI delivers real value versus traditional automation. Produces qualified, implementation-ready answers for "where should we use AI agents?"
- **Suggested timing**: Run before AXE to identify target services and agent workflows. This frames the subsequent AXE engagement with concrete use cases.
- **Recommended scope**: Focus on the 15 services that are Agent-Ready or Pilot-Ready to identify concrete agent integration opportunities.
- **Next step**: Request AgentStorming workshop via AWS Solutions Architect.

#### AXE (Agentic Experience Workshop)

- **Why triggered**: 15 services have Agent-Ready (14) or Pilot-Ready (1) profiles, exceeding the 3-service threshold. The portfolio has a substantial base of services ready for agent integration but lacks a technical implementation roadmap.
- **What it provides**: A six-phase strategic methodology for implementing agentic AI solutions, starting from desired customer/employee experience and working backwards to define AI agents and technical architecture. The Guardrails & Boundaries phase aligns with ARA findings.
- **Suggested timing**: Run after AgentStorming (if triggered) to design the agent experience for identified use cases. Can also run immediately if agent use cases are already defined.
- **Recommended scope**: Focus on the Agent-Ready services that have the most business value for agent integration.
- **Next step**: Request AXE engagement via AWS Solutions Architect.

#### EBA on Agentic AI (Experience-Based Acceleration)

- **Why triggered**: Two cross-cutting BLOCKERs exceed the 5-repository threshold: AUTH-Q1 (Machine Identity Authentication) affects 11 repositories, and DATA-Q1 (Sensitive Data Classification — tiered) affects 7 repositories (down from 14 under the revised rubric). These systemic gaps require coordinated architecture remediation that cannot be resolved through standard advisory alone.
- **What it provides**: An intensive, time-boxed engagement that accelerates the path from ARA findings to production agent deployment. Produces remediated systems, validated agent integrations, and a sequenced deployment roadmap.
- **Suggested timing**: Run after AXE to accelerate implementation of the identified agent experience design. The EBA would focus on remediating the 13 services that require remediation.
- **Recommended scope**: Prioritize the *arr suite (4 services with shared codebase) and high-value services (Conductor, ThingsBoard, ToolJet) for the EBA sprint.
- **Next step**: Request EBA engagement via AWS Solutions Architect. Executive sponsorship recommended given the scale of remediation.

---

## Portfolio-Level Findings

> These questions evaluate capabilities that can only be assessed by looking across
> multiple repos. They are distinct from cross-cutting analysis (which aggregates
> individual findings). Individual report findings are never overridden.

### PORT-ARA-Q1: Centralized Identity Plane

- **Severity**: BLOCKER
- **Finding**: No shared identity provider (IdP) exists across the portfolio. Each of the 34 repositories is an independent open-source project with its own authentication approach (or no authentication at all). No Cognito User Pools, shared Okta configurations, shared auth middleware, or centralized identity service was found referenced across any 2+ repositories. The *arr suite (Lidarr, Prowlarr, Radarr, Sonarr) shares a common `ApiKeyAuthenticationHandler` pattern, but each instance generates its own independent API key — there is no centralized key registry or shared IdP.
- **Evidence**: All 34 repositories assessed independently. AUTH-Q1 findings across 11 services confirm no shared identity mechanism. Portfolio config specifies no shared infrastructure.
- **Recommendation**: For production portfolios, deploy a centralized identity provider (Amazon Cognito, Okta, or AWS IAM Identity Center) that all agent-facing services integrate with. Issue per-agent client credentials from the centralized IdP. This is not applicable for this portfolio of independent open-source projects but is critical for production microservice deployments.
- **Affected Services**: All 34 services (no service has integration with a shared IdP)
- **Contextual Annotations**: 
  > **Portfolio Context**: PORT-ARA-Q1 confirms no centralized identity plane exists. This reinforces the AUTH-Q1 cross-cutting BLOCKER for the 11 services lacking machine identity authentication — each service must implement identity independently in the absence of a shared IdP.

### PORT-ARA-Q2: Cross-Service Audit Correlation

- **Severity**: RISK
- **Finding**: No cross-service audit correlation mechanism exists. Services log independently using diverse logging frameworks (SLF4J/Logback for Java, winston/werelogs for Node.js, Python logging, NLog for C#) with no shared trace ID propagation, no centralized audit trail, and no consistent log format. No shared CloudTrail trail, no shared CloudWatch Log Group, and no trace ID headers (X-Amzn-Trace-Id, traceparent) are propagated across service boundaries.
- **Evidence**: Individual report findings for OBS-Q1 across 18 services show RISK-QUALITY for distributed tracing. No cross-service trace correlation was identified in any report. Each project uses its own logging configuration.
- **Recommendation**: Implement OpenTelemetry-based distributed tracing with a shared trace context propagation standard (W3C traceparent). Ship all audit logs to a centralized log aggregation system (CloudWatch Logs or OpenSearch) with a common schema that includes agent identity, action type, and resource affected.
- **Affected Services**: All 34 services
- **Contextual Annotations**: None — this is a new portfolio-level finding that complements individual OBS-Q1 findings.

### PORT-ARA-Q3: Portfolio-Level Rate Limiting

- **Severity**: RISK
- **Finding**: No portfolio-level rate limiting exists. No shared WAF WebACL, shared API Gateway, or portfolio-level rate limiting rules were found across any repositories. Individual services have their own rate limiting (or lack thereof — STATE-Q5 is RISK-SAFETY in 14 services). Agent traffic storms would need to be handled at the individual service level.
- **Evidence**: STATE-Q5 findings across 14 services show no rate limiting. No shared WAF or API Gateway configuration found in any repository.
- **Recommendation**: For production portfolios, deploy a shared AWS WAF with rate-based rules protecting all agent-facing API endpoints. Configure per-agent rate limits at the shared API Gateway or WAF level. For this portfolio of independent projects, each service should implement its own rate limiting as noted in the STATE-Q5 RISK-SAFETY findings.
- **Affected Services**: All 34 services (none has portfolio-level protection)
- **Contextual Annotations**: None.

### PORT-ARA-Q4: Transitive Dependency Safety

- **Severity**: INFO
- **Finding**: No transitive dependency risks exist in this portfolio because the 34 services are independent open-source projects with no inter-service dependencies. There are no sync or async dependency chains that could create transitive agent safety risks. No service depends on another service in this portfolio.
- **Evidence**: No `dependency_overrides` provided. No inter-service dependencies inferred from individual reports. Portfolio consists of independent open-source project mirrors.
- **Recommendation**: No action needed for this portfolio. For production microservice portfolios, provide `dependency_overrides` to enable transitive dependency analysis. Monitor for cases where an Agent-Ready service synchronously depends on a Not Agent-Integrable service.
- **Affected Services**: None (no transitive dependencies exist)
- **Contextual Annotations**: None.

### PORT-ARA-Q5: Agent Identity Governance

- **Severity**: RISK
- **Finding**: No centralized mechanism to suspend or revoke agent identities across all services simultaneously. Each service manages authentication independently — there is no portfolio-wide agent identity registry, no centralized API key management, and no global kill-switch that could disable a compromised agent across all 34 services at once. The *arr suite's shared API key pattern means revoking access requires modifying each service's `config.xml` individually.
- **Evidence**: AUTH-Q7 (Agent Identity Suspension) is RISK-SAFETY in 14 services. No centralized identity registry found in any repository or portfolio configuration.
- **Recommendation**: Implement a centralized agent identity registry with a global suspension mechanism. For production deployments, use Amazon Cognito app client registry or AWS IAM with centralized policy management. Implement a "break glass" procedure that can disable all agent identities across the portfolio within minutes.
- **Affected Services**: All 34 services
- **Contextual Annotations**:
  > **Portfolio Context**: PORT-ARA-Q5 reinforces the AUTH-Q7 cross-cutting RISK-SAFETY finding. The lack of centralized agent identity governance means each service's individual suspension mechanism (if any) must be invoked separately — increasing response time during security incidents.

---

## Service-by-Service Summary

| Service | Repo Type | Agent Scope | Readiness Profile | BLOCKERs | RISKs | INFOs | N/A |
|---------|-----------|-------------|-------------------|----------|-------|-------|-----|
| ToolJet--ToolJet | monorepo | read-only | ❌ Not Agent-Integrable | 3 | 26 | 11 | 0 |
| Alluxio--alluxio | monorepo | read-only | 🟠 Remediation Required | 1 | 23 | 17 | 0 |
| apache--druid | monorepo | read-only | 🟠 Remediation Required | 1 | 16 | 25 | 0 |
| conductor-oss--conductor | monorepo | read-only | 🟠 Remediation Required | 2 | 19 | 20 | 0 |
| FlowiseAI--Flowise | monorepo | read-only | 🟠 Remediation Required | 1 | 17 | 21 | 0 |
| Graylog2--graylog2-server | monorepo | read-only | 🟠 Remediation Required | 1 | 18 | 20 | 0 |
| greenshot--greenshot | monorepo | read-only | 🟠 Remediation Required | 2 | 4 | 22 | 5 |
| hapifhir--hapi-fhir | monorepo | read-only | 🟠 Remediation Required | 2 | 17 | 22 | 0 |
| Lidarr--Lidarr | monorepo | read-only | 🟠 Remediation Required | 2 | 22 | 18 | 0 |
| Netflix--eureka | monorepo | read-only | 🟠 Remediation Required | 1 | 17 | 22 | 0 |
| openzipkin--zipkin | monorepo | read-only | 🟠 Remediation Required | 1 | 21 | 16 | 0 |
| Prowlarr--Prowlarr | monorepo | read-only | 🟠 Remediation Required | 2 | 23 | 17 | 0 |
| Radarr--Radarr | monorepo | read-only | 🟠 Remediation Required | 2 | 22 | 18 | 0 |
| scality--cloudserver | application | read-only | 🟠 Remediation Required | 1 | 15 | 26 | 0 |
| Sonarr--Sonarr | monorepo | read-only | 🟠 Remediation Required | 2 | 22 | 15 | 0 |
| thingsboard--thingsboard | monorepo | read-only | 🟠 Remediation Required | 1 | 19 | 21 | 0 |
| umami-software--umami | monorepo | read-only | 🟠 Remediation Required | 2 | 25 | 15 | 0 |
| scality--backbeat | application | read-only | 🟡 Pilot-Ready (Safety) | 0 | 21 | 20 | 0 |
| serverless--serverless | monorepo | read-only | 🟡 Pilot-Ready (Safety) | 0 | 11 | 22 | 0 |
| OpenAPITools--openapi-generator | application | read-only | 🟡 Pilot-Ready | 0 | 3 | 32 | 0 |
| akveo--ngx-admin | application | read-only | ✅ Agent-Ready | 0 | 0 | 33 | 5 |
| apache--flink-connector-aws | monorepo | read-only | ✅ Agent-Ready | 0 | 1 | 30 | 5 |
| arrow-py--arrow | application | read-only | ✅ Agent-Ready | 0 | 1 | 31 | 0 |
| coreui--coreui-free-angular-admin-template | application | read-only | ✅ Agent-Ready | 0 | 1 | 28 | 5 |
| dwyl--aws-sdk-mock | application | read-only | ✅ Agent-Ready | 0 | 1 | 27 | 5 |
| getlift--lift | application | read-only | ✅ Agent-Ready | 0 | 0 | 32 | 0 |
| getsentry--sentry-python | application | read-only | ✅ Agent-Ready | 0 | 1 | 27 | 5 |
| gulpjs--gulp | application | read-only | ✅ Agent-Ready | 0 | 1 | 31 | 0 |
| iterative--dvc | application | read-only | ✅ Agent-Ready | 0 | 1 | 32 | 0 |
| motdotla--node-lambda | application | read-only | ✅ Agent-Ready | 0 | 1 | 29 | 5 |
| realworld-apps--angular-realworld-example-app | application | read-only | ✅ Agent-Ready | 0 | 1 | 31 | 0 |
| tqdm--tqdm | application | read-only | ✅ Agent-Ready | 0 | 1 | 31 | 0 |
| webpack--webpack | application | read-only | ✅ Agent-Ready | 0 | 1 | 27 | 5 |
| zappa--Zappa | application | read-only | ✅ Agent-Ready | 0 | 1 | 28 | 5 |

### Individual Service Details

#### ToolJet--ToolJet (Remediation Required)

- **Readiness Profile**: 🟠 Remediation Required (was Not Agent-Integrable under binary DATA-Q1; now 2 BLOCKERs)
- **Repo Type**: monorepo | **Agent Scope**: read-only | **Priority**: P2
- **BLOCKERs** (2): API-Q1 (no OpenAPI spec), AUTH-Q1 (no M2M auth). DATA-Q1 = INFO under tiered model (B1 CLEAR: password excluded from User queries, credentials encrypted with `credential_id` indirection; B2 CLEAR: `organizationId` filtering + CASL/`FeatureAbilityGuard`/`PolicyGuard` RBAC; only B3 formal classification metadata absent).
- **RISKs** (26): 9 RISK-SAFETY, 17 RISK-QUALITY
- **Key Recommendations**: (1) Enable NestJS Swagger to generate OpenAPI spec, (2) Add OAuth2 client credentials for M2M auth, (3) (Aspirational) add schema-level classification decorators

#### conductor-oss--conductor (Remediation Required)

- **Readiness Profile**: 🟠 Remediation Required
- **Repo Type**: monorepo | **Agent Scope**: read-only | **Priority**: P2
- **BLOCKERs** (2): AUTH-Q1 (no authentication at all), DATA-Q1 (B1 BLOCKER: `HttpTask.java:138` persists `Authorization` headers into task output; `WorkflowResource`/`TaskResource` return full `input`/`output` payloads unredacted via `toWorkflow()`/`toTask()`)
- **RISKs** (19): 8 RISK-SAFETY, 11 RISK-QUALITY
- **Key Recommendations**: (1) Deploy API Gateway with auth in front of Conductor, (2) Mask sensitive headers in `HttpTask` before `addOutput`; apply response-level redaction on Task/Workflow DTOs; enforce `WorkflowDef.maskedFields` at validation time, (3) Implement audit logging

#### hapifhir--hapi-fhir (Remediation Required)

- **Readiness Profile**: 🟠 Remediation Required
- **Repo Type**: monorepo | **Agent Scope**: read-only | **Priority**: P2
- **BLOCKERs** (1): AUTH-Q1 (no built-in machine identity). DATA-Q1 = RISK-SAFETY under tiered model (framework provides `AuthorizationInterceptor`/`SearchNarrowingInterceptor` hooks, FHIR-native `Meta.security` classification; RISK-SAFETY reflects "if no interceptor is registered, PHI returns unfiltered" — a deployer-configuration concern, not a code defect).
- **RISKs** (17): 8 RISK-SAFETY, 9 RISK-QUALITY
- **Key Recommendations**: (1) Implement SMART on FHIR authentication interceptor, (2) Register `AuthorizationInterceptor` with default-deny + `SearchNarrowingInterceptor` with compartment narrowing, (3) Apply `Meta.security` labels per HL7 confidentiality taxonomy

#### Lidarr--Lidarr (Remediation Required)

- **Readiness Profile**: 🟠 Remediation Required
- **Repo Type**: monorepo | **Agent Scope**: read-only | **Priority**: P2
- **BLOCKERs** (2): AUTH-Q1 (single shared API key), DATA-Q1 (B1 BLOCKER: `GET /api/v1/config/host` returns master `ApiKey`, admin `Password`, `SslCertPassword`, `ProxyPassword` unmasked — provider settings are correctly masked via `PrivacyLevel`/`SchemaBuilder`)
- **RISKs** (22): 8 RISK-SAFETY, 14 RISK-QUALITY
- **Key Recommendations**: (1) Implement multi-key auth with principal attribution, (2) Mask credential fields in `HostConfigResourceMapper.ToResource()` using the existing `SchemaBuilder`/`PrivacyLevel` pattern

#### Prowlarr--Prowlarr (Remediation Required)

- **Readiness Profile**: 🟠 Remediation Required
- **Repo Type**: monorepo | **Agent Scope**: read-only | **Priority**: P2
- **BLOCKERs** (2): AUTH-Q1 (single shared API key), DATA-Q1 (B1 BLOCKER: same `HostConfigResource` leakage as Servarr family; compounded risk because Prowlarr's master key enables impersonation across every connected *arr application)
- **RISKs** (23): 9 RISK-SAFETY, 14 RISK-QUALITY
- **Key Recommendations**: (1) Multi-key auth (same pattern as Lidarr), (2) Mask credential fields in `HostConfigResourceMapper.ToResource()`; consider suppressing `Privacy` metadata in non-admin responses

#### Radarr--Radarr (Remediation Required)

- **Readiness Profile**: 🟠 Remediation Required
- **Repo Type**: monorepo | **Agent Scope**: read-only | **Priority**: P2
- **BLOCKERs** (2): AUTH-Q1 (single shared API key), DATA-Q1 (B1 BLOCKER: same `HostConfigResource` leakage pattern as Servarr family)
- **RISKs** (22): 9 RISK-SAFETY, 13 RISK-QUALITY
- **Key Recommendations**: (1) Multi-key auth (same pattern as Lidarr), (2) Mask credential fields in `HostConfigResourceMapper.ToResource()` using existing `PrivacyLevel` pattern

#### Sonarr--Sonarr (Remediation Required)

- **Readiness Profile**: 🟠 Remediation Required
- **Repo Type**: monorepo | **Agent Scope**: read-only | **Priority**: P2
- **BLOCKERs** (2): AUTH-Q1 (single shared API key), DATA-Q1 (B1 BLOCKER: same `HostConfigResource` leakage pattern as Servarr family)
- **RISKs** (22): 9 RISK-SAFETY, 13 RISK-QUALITY
- **Key Recommendations**: (1) Multi-key auth (same pattern as Lidarr), (2) Mask credential fields in `HostConfigResourceMapper.ToResource()` using existing `PrivacyLevel` pattern

#### umami-software--umami (Remediation Required)

- **Readiness Profile**: 🟠 Remediation Required
- **Repo Type**: monorepo | **Agent Scope**: read-only | **Priority**: P2
- **BLOCKERs** (1): AUTH-Q1 (human-only JWT auth). DATA-Q1 = INFO under tiered model (B1 CLEAR: `findUser()` uses `select: { password: includePassword }` defaulting false; B2 CLEAR: 7-role RBAC with team-scope checks; only B3 absent).
- **RISKs** (25): 9 RISK-SAFETY, 16 RISK-QUALITY
- **Key Recommendations**: (1) Add M2M auth flow, (2) Implement PII redaction in logs, (3) (Aspirational) add decorator-based classification tags

#### greenshot--greenshot (Remediation Required)

- **Readiness Profile**: 🟠 Remediation Required
- **Repo Type**: monorepo | **Agent Scope**: read-only | **Priority**: P2
- **BLOCKERs** (2): API-Q1 (no programmatic API — desktop GUI only), AUTH-Q1 (no auth surface)
- **RISKs** (4): 2 RISK-SAFETY (AUTH-Q2, AUTH-Q3), 2 RISK-QUALITY (AUTH-Q5, DISC-Q1)
- **Key Recommendations**: (1) Consider descoping from agent integration, or (2) Build CLI/API wrapper around screenshot capabilities

#### Alluxio--alluxio (Pilot-Ready, Safety Concerns)

- **Readiness Profile**: 🟡 Pilot-Ready (Safety Concerns) — promoted from Remediation Required after tiered DATA-Q1
- **Repo Type**: monorepo | **Agent Scope**: read-only | **Priority**: P2
- **BLOCKERs** (0). DATA-Q1 = INFO (B1 CLEAR: `DisplayType.CREDENTIALS` masks UFS credentials to `"******"` in config API; B2 CLEAR: POSIX permissions; only B3 path-level classification absent).
- **RISKs** (23): 8 RISK-SAFETY, 15 RISK-QUALITY
- **Key Recommendations**: (1) Prioritize RISK-SAFETY remediation before expanding scope, (2) (Aspirational) add xattr-based path classification

#### apache--druid (Remediation Required)

- **Readiness Profile**: 🟠 Remediation Required
- **Repo Type**: monorepo | **Agent Scope**: read-only | **Priority**: P2
- **BLOCKERs** (1): DATA-Q1 (B1 BLOCKER: `SupervisorResource` returns Kafka `consumerProperties`, Kinesis AWS credentials, and other ingestion-source secrets serialized verbatim via `@JsonProperty`; no `PasswordProvider`-style abstraction)
- **RISKs** (16): 5 RISK-SAFETY, 11 RISK-QUALITY
- **Key Recommendations**: (1) Add `@JsonIgnore` on sensitive `consumerProperties` keys (or introduce a filtered response DTO), (2) Integrate with a secrets manager so supervisor specs reference secret names not inline values

#### FlowiseAI--Flowise (Pilot-Ready, Safety Concerns)

- **Readiness Profile**: 🟡 Pilot-Ready (Safety Concerns) — promoted from Remediation Required after tiered DATA-Q1
- **Repo Type**: monorepo | **Agent Scope**: read-only | **Priority**: P2
- **BLOCKERs** (0). DATA-Q1 = RISK-SAFETY (B1 MIXED: list endpoints strip `encryptedData`; `getCredentialById` decrypts to plaintext for UI use; API keys list returns `apiKey` plaintext; B2 CLEAR: workspace scoping + permission-subset filtering; B3 INFO).
- **RISKs** (18): 5 RISK-SAFETY, 13 RISK-QUALITY
- **Key Recommendations**: (1) Default `getCredentialById` to encrypted blob; require explicit `reveal=true` parameter, (2) Mask `apiKey` in list responses (truncated prefix), (3) Continue RISK-SAFETY remediation

#### Graylog2--graylog2-server (Pilot-Ready, Safety Concerns)

- **Readiness Profile**: 🟡 Pilot-Ready (Safety Concerns) — promoted from Remediation Required after tiered DATA-Q1
- **Repo Type**: monorepo | **Agent Scope**: read-only | **Priority**: P2
- **BLOCKERs** (0). DATA-Q1 = INFO (B1 CLEAR: password excluded via `@DbEntity.readableFields`, `EncryptedValue` wraps LDAP/webhook secrets; B2 CLEAR: granular GRN-based RBAC with `STREAMS_READ` isolation; B3 INFO for log-field PII).
- **RISKs** (18): 6 RISK-SAFETY, 12 RISK-QUALITY
- **Key Recommendations**: (1) AUTH-Q6 immutable audit logging, (2) (Aspirational) add log-field PII classification index for MCP tools

#### Netflix--eureka (Remediation Required)

- **Readiness Profile**: 🟠 Remediation Required
- **Repo Type**: monorepo | **Agent Scope**: read-only | **Priority**: P2
- **BLOCKERs** (1): AUTH-Q1 (identity headers logged but not enforced)
- **RISKs** (17): 6 RISK-SAFETY, 11 RISK-QUALITY
- **Key Recommendations**: (1) Enforce authentication in ServerRequestAuthFilter, (2) Implement per-agent identity validation

#### openzipkin--zipkin (Remediation Required)

- **Readiness Profile**: 🟠 Remediation Required
- **Repo Type**: monorepo | **Agent Scope**: read-only | **Priority**: P2
- **BLOCKERs** (1): AUTH-Q1 (completely open — no authentication)
- **RISKs** (21): 7 RISK-SAFETY, 14 RISK-QUALITY
- **Key Recommendations**: (1) Deploy API Gateway with auth in front of Zipkin, (2) Implement rate limiting

#### scality--cloudserver (Pilot-Ready, Safety Concerns)

- **Readiness Profile**: 🟡 Pilot-Ready (Safety Concerns) — promoted from Remediation Required after tiered DATA-Q1
- **Repo Type**: application | **Agent Scope**: read-only | **Priority**: P2
- **BLOCKERs** (0). DATA-Q1 = INFO (B1 CLEAR: S3 API is content-agnostic, no credentials echoed; B2 CLEAR: Vault-backed IAM enforced on every request; B3 INFO: native S3 object tagging / SSE primitives).
- **RISKs** (15): 6 RISK-SAFETY, 9 RISK-QUALITY
- **Key Recommendations**: (1) Enable default bucket encryption globally, (2) (Aspirational) adopt object-tag classification conventions + Macie integration

#### thingsboard--thingsboard (Remediation Required)

- **Readiness Profile**: 🟠 Remediation Required
- **Repo Type**: monorepo | **Agent Scope**: read-only | **Priority**: P2
- **BLOCKERs** (1): DATA-Q1 (B1 BLOCKER: `GET /api/device/{id}/credentials` returns `DeviceCredentials.credentialsValue` — access tokens, MQTT passwords, X.509 PEM — plaintext to any CUSTOMER_USER; no `@JsonIgnore`)
- **RISKs** (19): 6 RISK-SAFETY, 13 RISK-QUALITY
- **Key Recommendations**: (1) Apply `@JsonIgnore` to `DeviceCredentials.credentialsValue`; introduce a `DeviceCredentialsSummary` DTO; gate value-revealing endpoint to TENANT_ADMIN only, (2) Consider out-of-band credential rotation flow

#### scality--backbeat (Pilot-Ready, Safety Concerns)

- **Readiness Profile**: 🟡 Pilot-Ready (Safety Concerns)
- **Repo Type**: application | **Agent Scope**: read-only | **Priority**: P2
- **BLOCKERs** (0)
- **RISKs** (21): 8 RISK-SAFETY, 13 RISK-QUALITY
- **Key Recommendations**: (1) Address RISK-SAFETY items before expanding agent scope, (2) Implement audit logging, (3) Add rate limiting

#### serverless--serverless (Pilot-Ready, Safety Concerns)

- **Readiness Profile**: 🟡 Pilot-Ready (Safety Concerns)
- **Repo Type**: monorepo | **Agent Scope**: read-only | **Priority**: P2
- **BLOCKERs** (0)
- **RISKs** (11): 3 RISK-SAFETY (STATE-Q4, STATE-Q5, AUTH-Q7), 8 RISK-QUALITY
- **Key Recommendations**: (1) Add circuit breaker for MCP server, (2) Implement rate limiting, (3) Add agent identity suspension capability

#### OpenAPITools--openapi-generator (Pilot-Ready)

- **Readiness Profile**: 🟡 Pilot-Ready
- **Repo Type**: application | **Agent Scope**: read-only | **Priority**: P2
- **BLOCKERs** (0)
- **RISKs** (3): 1 RISK-SAFETY (STATE-Q4), 2 RISK-QUALITY (DISC-Q1, ENG-Q4)
- **Key Recommendations**: (1) Add circuit breaker for code generation, (2) Improve API test coverage

#### Agent-Ready Services (14 services)

The following 14 services have Agent-Ready profiles with 0 BLOCKERs and 0 RISK-SAFETY:

| Service | RISK-QUALITY | INFOs | N/A | Note |
|---------|-------------|-------|-----|------|
| getlift--lift | 0 | 32 | 0 | Serverless Framework plugin — no agent surface |
| akveo--ngx-admin | 0 | 33 | 5 | Angular SPA template — no backend |
| apache--flink-connector-aws | 1 | 30 | 5 | Flink connector libraries — no agent surface |
| arrow-py--arrow | 1 | 31 | 0 | Python date/time library |
| coreui--coreui-free-angular-admin-template | 1 | 28 | 5 | Angular admin template — no backend |
| dwyl--aws-sdk-mock | 1 | 27 | 5 | AWS SDK mock library for testing |
| getsentry--sentry-python | 1 | 27 | 5 | Sentry Python SDK |
| gulpjs--gulp | 1 | 31 | 0 | JavaScript build toolkit |
| iterative--dvc | 1 | 32 | 0 | Data Version Control CLI |
| motdotla--node-lambda | 1 | 29 | 5 | Node.js Lambda deployment CLI |
| realworld-apps--angular-realworld-example-app | 1 | 31 | 0 | Angular RealWorld SPA |
| tqdm--tqdm | 1 | 31 | 0 | Python progress bar library |
| webpack--webpack | 1 | 27 | 5 | JavaScript module bundler |
| zappa--Zappa | 1 | 28 | 5 | Python Lambda deployment framework |

> **Note**: Most Agent-Ready services are libraries, CLI tools, or frontend templates with no backend agent-callable surface. Their Agent-Ready profile reflects the absence of blockers, not the presence of agent integration infrastructure. The single RISK-QUALITY in most is DISC-Q1 (Schema Versioning and API Contracts).

---

## Assessment Inventory

| # | Service | Report File | Assessment Date | Repo Type | Agent Scope |
|---|---------|-------------|-----------------|-----------|-------------|
| 1 | akveo--ngx-admin | services/akveo--ngx-admin/agentic-readiness-assessment/akveo--ngx-admin-ara-report.md | 2026-04-30 | application | read-only |
| 2 | Alluxio--alluxio | services/Alluxio--alluxio/agentic-readiness-assessment/Alluxio--alluxio-ara-report.md | 2026-04-30 | monorepo | read-only |
| 3 | apache--druid | services/apache--druid/agentic-readiness-assessment/apache--druid-ara-report.md | 2026-04-30 | monorepo | read-only |
| 4 | apache--flink-connector-aws | services/apache--flink-connector-aws/agentic-readiness-assessment/apache--flink-connector-aws-ara-report.md | 2026-04-30 | monorepo | read-only |
| 5 | arrow-py--arrow | services/arrow-py--arrow/agentic-readiness-assessment/arrow-py--arrow-ara-report.md | 2026-04-30 | application | read-only |
| 6 | conductor-oss--conductor | services/conductor-oss--conductor/agentic-readiness-assessment/conductor-oss--conductor-ara-report.md | 2026-04-30 | monorepo | read-only |
| 7 | coreui--coreui-free-angular-admin-template | services/coreui--coreui-free-angular-admin-template/agentic-readiness-assessment/coreui--coreui-free-angular-admin-template-ara-report.md | 2026-04-30 | application | read-only |
| 8 | dwyl--aws-sdk-mock | services/dwyl--aws-sdk-mock/agentic-readiness-assessment/dwyl--aws-sdk-mock-ara-report.md | 2026-04-30 | application | read-only |
| 9 | FlowiseAI--Flowise | services/FlowiseAI--Flowise/agentic-readiness-assessment/FlowiseAI--Flowise-ara-report.md | 2026-04-30 | monorepo | read-only |
| 10 | getlift--lift | services/getlift--lift/agentic-readiness-assessment/getlift--lift-ara-report.md | 2026-04-30 | application | read-only |
| 11 | getsentry--sentry-python | services/getsentry--sentry-python/agentic-readiness-assessment/getsentry--sentry-python-ara-report.md | 2025-07-18 | application | read-only |
| 12 | Graylog2--graylog2-server | services/Graylog2--graylog2-server/agentic-readiness-assessment/Graylog2--graylog2-server-ara-report.md | 2026-04-30 | monorepo | read-only |
| 13 | greenshot--greenshot | services/greenshot--greenshot/agentic-readiness-assessment/greenshot--greenshot-ara-report.md | 2026-04-30 | monorepo | read-only |
| 14 | gulpjs--gulp | services/gulpjs--gulp/agentic-readiness-assessment/gulpjs--gulp-ara-report.md | 2026-04-30 | application | read-only |
| 15 | hapifhir--hapi-fhir | services/hapifhir--hapi-fhir/agentic-readiness-assessment/hapifhir--hapi-fhir-ara-report.md | 2026-04-30 | monorepo | read-only |
| 16 | iterative--dvc | services/iterative--dvc/agentic-readiness-assessment/iterative--dvc-ara-report.md | 2026-04-30 | application | read-only |
| 17 | Lidarr--Lidarr | services/Lidarr--Lidarr/agentic-readiness-assessment/Lidarr--Lidarr-ara-report.md | 2026-04-30 | monorepo | read-only |
| 18 | motdotla--node-lambda | services/motdotla--node-lambda/agentic-readiness-assessment/motdotla--node-lambda-ara-report.md | 2026-04-30 | application | read-only |
| 19 | Netflix--eureka | services/Netflix--eureka/agentic-readiness-assessment/Netflix--eureka-ara-report.md | 2026-04-30 | monorepo | read-only |
| 20 | OpenAPITools--openapi-generator | services/OpenAPITools--openapi-generator/agentic-readiness-assessment/OpenAPITools--openapi-generator-ara-report.md | 2026-04-30 | application | read-only |
| 21 | openzipkin--zipkin | services/openzipkin--zipkin/agentic-readiness-assessment/openzipkin--zipkin-ara-report.md | 2026-04-30 | monorepo | read-only |
| 22 | Prowlarr--Prowlarr | services/Prowlarr--Prowlarr/agentic-readiness-assessment/Prowlarr--Prowlarr-ara-report.md | 2026-04-30 | monorepo | read-only |
| 23 | Radarr--Radarr | services/Radarr--Radarr/agentic-readiness-assessment/Radarr--Radarr-ara-report.md | 2026-04-30 | monorepo | read-only |
| 24 | realworld-apps--angular-realworld-example-app | services/realworld-apps--angular-realworld-example-app/agentic-readiness-assessment/realworld-apps--angular-realworld-example-app-ara-report.md | 2025-07-17 | application | read-only |
| 25 | scality--backbeat | services/scality--backbeat/agentic-readiness-assessment/scality--backbeat-ara-report.md | 2025-01-30 | application | read-only |
| 26 | scality--cloudserver | services/scality--cloudserver/agentic-readiness-assessment/scality--cloudserver-ara-report.md | 2025-07-14 | application | read-only |
| 27 | serverless--serverless | services/serverless--serverless/agentic-readiness-assessment/serverless--serverless-ara-report.md | 2026-04-30 | monorepo | read-only |
| 28 | Sonarr--Sonarr | services/Sonarr--Sonarr/agentic-readiness-assessment/Sonarr--Sonarr-ara-report.md | 2025-07-14 | monorepo | read-only |
| 29 | thingsboard--thingsboard | services/thingsboard--thingsboard/agentic-readiness-assessment/thingsboard--thingsboard-ara-report.md | 2026-04-30 | monorepo | read-only |
| 30 | ToolJet--ToolJet | services/ToolJet--ToolJet/agentic-readiness-assessment/ToolJet--ToolJet-ara-report.md | 2026-04-30 | monorepo | read-only |
| 31 | tqdm--tqdm | services/tqdm--tqdm/agentic-readiness-assessment/tqdm--tqdm-ara-report.md | 2026-04-30 | application | read-only |
| 32 | umami-software--umami | services/umami-software--umami/agentic-readiness-assessment/umami-software--umami-ara-report.md | 2026-04-30 | monorepo | read-only |
| 33 | webpack--webpack | services/webpack--webpack/agentic-readiness-assessment/webpack--webpack-ara-report.md | 2025-07-16 | application | read-only |
| 34 | zappa--Zappa | services/zappa--Zappa/agentic-readiness-assessment/zappa--Zappa-ara-report.md | 2025-07-16 | application | read-only |

---

*Report generated by AWS Transform Custom — Portfolio Agentic Readiness Assessment*
*Portfolio: zg-cmp-atx-testing | Services: 34 | Date: 2026-04-30*
