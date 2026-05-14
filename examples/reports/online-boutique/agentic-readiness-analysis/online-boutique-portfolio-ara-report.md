# Portfolio Agentic Readiness Analysis Report

**Date**: 2026-04-16
**Services Analyzed**: 11
**Portfolio Context**: Cloud-native e-commerce platform with 11 microservices. Evaluating for autonomous AI agent integration (customer support agent for order tracking, product recommendations, and cart management).
**Agent Scope**: read-only

---

## Executive Dashboard

### Readiness Distribution

| Profile | Services | Percentage | Description |
|---------|----------|------------|-------------|
| ✅ Agent-Ready | 0 | 0% | 0 blockers, 0–2 risks — broad agent deployment |
| 🟡 Pilot-Ready | 0 | 0% | 0 blockers, 3–5 risks — narrow pilot only |
| 🟠 Remediation Required | 10 | 91% | 1–2 blockers — remediate before any agent deployment |
| ❌ Not Agent-Integrable | 1 | 9% | 3+ blockers — deferred or descoped |

### Portfolio Summary

| Metric | Value |
|--------|-------|
| Total Services Analyzed | 11 |
| Services Ready for Agents (Agent-Ready + Pilot-Ready) | 0 (0%) |
| Services Requiring Remediation | 11 (100%) |
| Total Unique BLOCKERs across Portfolio | 3 distinct question IDs (API-Q1, AUTH-Q1, DATA-Q1) |
| Total Unique RISKs across Portfolio | See cross-cutting RISKs below |
| Cross-Cutting BLOCKERs (same blocker in 2+ repos) | 2 (AUTH-Q1, DATA-Q1) |
| Cross-Cutting RISKs (same risk in 3+ repos) | See cross-cutting RISKs section |
| Services with Write-Enabled Agent Scope | 0 (0%) |
| Services with Read-Only Agent Scope | 11 (100%) |

### Repo Type Distribution

| Repo Type | Count | Percentage |
|-----------|-------|------------|
| application | 10 | 91% |
| infrastructure-only | 1 | 9% |
| deployment-config | 0 | 0% |
| monorepo | 0 | 0% |
| library | 0 | 0% |

### Blocker Heatmap by Section

| Section | Repos Blocked | % of Applicable Repos | Top Blockers |
|---------|--------------|----------------------|--------------|
| AUTH | 11 | 100% (11/11) | AUTH-Q1 |
| DATA | 7 | 70% (7/10 app services) | DATA-Q1 |
| API | 1 | 9% (1/11) | API-Q1 (frontend only) |
| STATE | 0 | 0% | — |
| HITL | 0 | 0% | — |
| DISC | 0 | 0% | — |
| OBS | 0 | 0% | — |
| ENG | 0 | 0% | — |

### Readiness Snapshot

```yaml
analysis_date: "2026-04-16"
total_services: 11
agent_ready: 0
pilot_ready: 0
remediation_required: 10
not_integrable: 1
total_blockers: 19
total_risks: 181
total_infos: 143
cross_cutting_blockers: 2
cross_cutting_risks: 24
portfolio_level_blockers: 1
portfolio_level_risks: 4
write_enabled_services: 0
read_only_services: 11
```

---

## Cross-Cutting BLOCKERs — Same Blocker in 2+ Repos

> These are BLOCKER-severity questions that appear in 2 or more repositories.
> They represent portfolio-wide agentic readiness gaps requiring coordinated remediation.
> Questions scored as N/A for a service do not count as gaps for that service.

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER in 11 of 11 applicable services
- **Affected Services**: frontend, cartservice, checkoutservice, paymentservice, shippingservice, emailservice, recommendationservice, productcatalogservice, currencyservice, adservice, platform-infra
- **Common Finding**: Every service in the portfolio lacks machine identity authentication. gRPC servers bind with insecure credentials across all languages — `grpc.NewServer()` (Go), `grpc.ServerCredentials.createInsecure()` (Node.js), `server.add_insecure_port()` (Python), `ServerBuilder.forPort(port)` (Java), `MapGrpcService<T>()` with no auth middleware (C#). Kubernetes ServiceAccounts exist per service but provide pod-level identity only, not request-level authentication. Istio AuthorizationPolicies are defined in Helm chart templates for every service with fine-grained per-operation rules, but are **disabled by default** (`authorizationPolicies.create: false` in `helm-chart/values.yaml`). NetworkPolicies and Sidecars are also disabled. No OAuth2, API key, mTLS, or API Gateway authorizers exist anywhere in the portfolio.
- **Root Cause Pattern**: The platform was designed for trusted in-cluster communication. All services assume network-level trust (Kubernetes cluster boundary) rather than request-level identity verification. The Istio AuthorizationPolicy infrastructure exists but was never enabled.
- **Portfolio-Level Remediation**:
  - **Approach**: Hybrid — platform-level Istio enablement + per-service application-layer hardening
  - **Immediate Action**: Set `authorizationPolicies.create: true` in `helm-chart/values.yaml`. This single configuration change enables mTLS-based service identity authentication across all 11 services using existing Helm chart templates.
  - **Target State**: Every gRPC call authenticated via mTLS with Kubernetes ServiceAccount principals. Agent-specific service accounts created with scoped access. Authenticated principal logged in audit trails.
  - **Estimated Effort**: Low (Istio enablement: 1–2 weeks) + Medium (per-service application-layer auth: 2–4 weeks per service)
  - **Priority**: Critical — affects all 11 services. No other security control can be enforced without identity.
  - **Dependencies**: None — this is the foundation.

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER in 7 of 10 applicable application services
- **Affected Services**: frontend, cartservice, checkoutservice, paymentservice, shippingservice, emailservice, recommendationservice
- **N/A**: platform-infra (infrastructure-only — N/A for this question)
- **Not Affected (INFO)**: productcatalogservice (catalog data is non-sensitive), currencyservice (exchange rates are public data), adservice (ad categories are non-sensitive)
- **Common Finding**: Services processing PII (email addresses, street addresses, phone numbers) and financial data (credit card numbers, CVV, expiration dates) have no data classification at any level. The `placeOrderHandler` in frontend and checkoutservice processes `credit_card_number`, `credit_card_cvv`, `email`, `street_address` with no classification tags, no field-level encryption, and no PII detection. The cartservice stores `userId` (potentially PII) in Redis without classification. The paymentservice handles credit card charge data. The emailservice processes email addresses and order details. No data classification policies exist anywhere in the portfolio.
- **Root Cause Pattern**: The platform was built as a demo/reference architecture without production data governance. No data classification taxonomy was established. PII and financial data flow in plaintext over insecure gRPC connections.
- **Portfolio-Level Remediation**:
  - **Approach**: Hybrid — portfolio-level classification taxonomy + per-service field-level implementation
  - **Immediate Action**: Define a portfolio-wide data classification taxonomy (`PUBLIC`, `INTERNAL`, `PII`, `PCI`, `SENSITIVE`). Classify the protobuf fields in `demo.proto` — specifically `CreditCardInfo` (PCI), `Address` (PII), `email` (PII), `userId` (PII-candidate).
  - **Target State**: All PII and financial fields classified, tagged in proto definitions, and protected by field-level access controls. Agent identities require explicit authorization to access classified fields.
  - **Estimated Effort**: Medium (classification taxonomy: 1–2 weeks) + High (field-level encryption and access controls: 4–8 weeks across 7 services)
  - **Priority**: High — affects 7 of 10 application services including all P0 services on the critical checkout path
  - **Dependencies**: AUTH-Q1 must be resolved first — identity is required before data access controls can be enforced.

---

## Cross-Cutting RISKs — Same Risk in 3+ Repos

> These are RISK-severity questions that appear in 3 or more repositories.
> They represent portfolio-wide patterns warranting coordinated attention.
> Questions scored as N/A for a service do not count as gaps for that service.

### AUTH-Q2: Scoped Permissions (Least Privilege)

- **Severity**: RISK in 11 of 11 applicable services
- **Affected Services**: All 11 services
- **Common Finding**: No IAM policies or permission scoping for agent identities. Once an identity has network access, it can call all RPCs without restriction. Istio AuthorizationPolicies define per-operation rules when enabled but are disabled by default.
- **Portfolio-Level Recommendation**: After AUTH-Q1 is resolved, define agent-specific service accounts with per-operation Istio AuthorizationPolicy rules. Create a shared RBAC model across the portfolio.

### AUTH-Q3: Action-Level Authorization

- **Severity**: RISK in 11 of 11 applicable services
- **Affected Services**: All 11 services
- **Common Finding**: No action-level authorization in any application code. No ABAC, RBAC, or permission checks in middleware or gRPC interceptors.
- **Portfolio-Level Recommendation**: Implement gRPC server interceptors across all services that validate operation-level permissions based on caller identity metadata.

### AUTH-Q4: Identity Propagation

- **Severity**: RISK in 10 of 10 applicable application services
- **Affected Services**: All 10 application services
- **Common Finding**: No JWT parsing, no OAuth2 token exchange, no identity propagation through the service chain. User identifiers (e.g., `userId`) are plain strings passed without verification.
- **Portfolio-Level Recommendation**: Implement JWT/OAuth2 token-based identity propagation through gRPC metadata. Standardize `x-agent-identity` and `x-on-behalf-of` header patterns.

### AUTH-Q5: Agent-as-Self vs Agent-on-Behalf-of-User

- **Severity**: RISK in 10 of 10 applicable application services
- **Affected Services**: All 10 application services
- **Common Finding**: No distinction between service identity and delegated user identity. All sessions are anonymous or use plain string identifiers. No dual authentication flows.
- **Portfolio-Level Recommendation**: Design a portfolio-wide agent identity model with distinct flows for autonomous agent actions vs. user-delegated actions.

### AUTH-Q6: Credential Management

- **Severity**: RISK in 9 of 11 applicable services
- **Affected Services**: frontend, cartservice, productcatalogservice, checkoutservice, paymentservice, shippingservice, emailservice, recommendationservice, platform-infra
- **Common Finding**: gRPC connections use insecure credentials across all languages. Redis has no authentication. No secrets management system for credential rotation.
- **Portfolio-Level Recommendation**: Enable mTLS for all gRPC connections via Istio sidecar injection. Integrate with a secrets management system for agent credentials. Enable Redis AUTH.

### AUTH-Q7: Immutable Audit Logging

- **Severity**: RISK in 11 of 11 applicable services
- **Affected Services**: All 11 services
- **Common Finding**: No immutable audit logging. Frontend has structured JSON logging via logrus but without authenticated principal. Most services use unstructured logging (`Console.WriteLine`, `console.log`, `print`/`logging`). No tamper-evident log storage.
- **Portfolio-Level Recommendation**: Implement a portfolio-wide structured logging standard (JSON with `request_id`, `trace_id`, `authenticated_principal`, `timestamp`, `operation`). Configure log forwarding to immutable storage.

### AUTH-Q8: Agent Identity Suspension

- **Severity**: RISK in 11 of 11 applicable services
- **Affected Services**: All 11 services
- **Common Finding**: No mechanism to suspend individual agent identities without broader platform impact. No API key revocation endpoints. Istio AuthorizationPolicy changes require Helm/Kubernetes deployment.
- **Portfolio-Level Recommendation**: Implement agent identity as distinct Kubernetes ServiceAccounts. Create a runbook for immediate suspension via `kubectl delete serviceaccount` or Istio AuthorizationPolicy update.

### API-Q2: Machine-Readable API Specification

- **Severity**: RISK in 7 of 10 applicable application services
- **Affected Services**: frontend, productcatalogservice, checkoutservice, paymentservice, shippingservice, emailservice, recommendationservice
- **Common Finding**: No OpenAPI or AsyncAPI specifications. gRPC services have proto files as machine-readable specs, but the frontend's HTTP endpoints are undocumented. No schema registry.
- **Portfolio-Level Recommendation**: Publish all proto files to a schema registry. Generate OpenAPI specs for HTTP endpoints.

### API-Q3: Structured Error Responses

- **Severity**: RISK in 10 of 10 applicable application services
- **Affected Services**: All 10 application services
- **Common Finding**: All services throw gRPC exceptions with generic status codes and string messages. No structured error codes, no retryable indicators, no error categorization.
- **Portfolio-Level Recommendation**: Define a portfolio-wide error response standard with structured error metadata in gRPC trailing metadata.

### API-Q5: API Versioning and Deprecation

- **Severity**: RISK in 10 of 10 applicable application services
- **Affected Services**: All 10 application services
- **Common Finding**: No API versioning. Proto packages use `hipstershop` with no version qualifier. No deprecation policies or changelogs.
- **Portfolio-Level Recommendation**: Adopt proto package versioning (e.g., `hipstershop.cart.v1`). Implement `buf` for breaking change detection in CI.

### API-Q7: Asynchronous Operation Support

- **Severity**: RISK in 7 of 10 applicable application services
- **Affected Services**: frontend, cartservice, productcatalogservice, checkoutservice, shippingservice, emailservice, recommendationservice
- **Common Finding**: All operations are synchronous request-response. No async patterns for long-running tasks. The checkout flow blocks on sequential gRPC calls to 6 backend services.
- **Portfolio-Level Recommendation**: Implement async patterns for the checkout flow (job submission + status polling).

### STATE-Q1: Compensation and Rollback

- **Severity**: RISK in 10 of 10 applicable application services
- **Affected Services**: All 10 application services
- **Common Finding**: No saga pattern, compensation logic, or undo endpoints. Multi-step operations leave partial state on failure.
- **Portfolio-Level Recommendation**: Implement compensation endpoints for critical write paths before expanding to write-enabled scope.

### STATE-Q2: Queryable Current State

- **Severity**: RISK in 7 of 10 applicable application services
- **Affected Services**: frontend, cartservice, checkoutservice, paymentservice, shippingservice, emailservice, recommendationservice
- **Common Finding**: State is queryable per entity but responses are limited. Frontend returns HTML. No cross-entity query capabilities.
- **Portfolio-Level Recommendation**: Add JSON-returning endpoints where HTML is currently returned. Add list/search capabilities with pagination.

### STATE-Q4: Circuit Breakers and Resilience

- **Severity**: RISK in 8 of 10 applicable application services
- **Affected Services**: frontend, cartservice, productcatalogservice, checkoutservice, paymentservice, shippingservice, emailservice, recommendationservice
- **Common Finding**: No circuit breakers in any application code. No retry policies with exponential backoff. Exceptions from dependencies cause cascading failures.
- **Portfolio-Level Recommendation**: Implement circuit breaker patterns using language-appropriate libraries. Alternatively, enable Istio DestinationRules with circuit breaking.

### STATE-Q5: Rate Limiting and Throttling

- **Severity**: RISK in 10 of 10 applicable application services
- **Affected Services**: All 10 application services
- **Common Finding**: No rate limiting at any level. Services are exposed as ClusterIP services with no request-rate throttling. Frontend LoadBalancer exposes port 80 directly to the internet.
- **Portfolio-Level Recommendation**: Deploy an API Gateway with rate limiting for agent traffic. Implement per-service rate limiting middleware as defense-in-depth.

### STATE-Q7: Infrastructure Capacity for Agent Traffic

- **Severity**: RISK in 10 of 10 applicable application services
- **Affected Services**: All 10 application services
- **Common Finding**: No load testing results or capacity planning. Static resource limits with no HPA. Infrastructure sized for human-paced interaction.
- **Portfolio-Level Recommendation**: Define HPAs for all services. Conduct load testing simulating agent traffic patterns.

### DATA-Q2: Data Residency and Sovereignty

- **Severity**: RISK in 10 of 10 applicable application services
- **Affected Services**: All 10 application services
- **Common Finding**: No data residency requirements documented. Deployed to `us-central1` by default. No GDPR/LGPD compliance references.
- **Portfolio-Level Recommendation**: Conduct a portfolio-wide data residency analysis. Configure agent LLM endpoints to respect data boundaries.

### DATA-Q3: Selective Query Support

- **Severity**: RISK in 8 of 10 applicable application services
- **Affected Services**: frontend, cartservice, productcatalogservice, checkoutservice, paymentservice, shippingservice, emailservice, recommendationservice
- **Common Finding**: No pagination, filtering, or sorting on most query endpoints. `ListProducts` returns all products unbounded.
- **Portfolio-Level Recommendation**: Add pagination parameters to list/query endpoints across all services.

### DATA-Q4: System of Record Designations

- **Severity**: RISK in 9 of 10 applicable application services
- **Affected Services**: frontend, cartservice, productcatalogservice, checkoutservice, paymentservice, shippingservice, emailservice, recommendationservice, adservice
- **Common Finding**: No system-of-record designations or data ownership documentation.
- **Portfolio-Level Recommendation**: Publish a data ownership matrix mapping each data domain to its authoritative service.

### DATA-Q5: Reliable Timestamps

- **Severity**: RISK in 10 of 10 applicable application services
- **Affected Services**: All 10 application services
- **Common Finding**: No `created_at` or `updated_at` timestamp fields on business entities. Protobuf messages have no temporal metadata.
- **Portfolio-Level Recommendation**: Add timestamp fields to all protobuf messages. Standardize on UTC with RFC3339 format.

### DATA-Q6: Data Freshness Signaling

- **Severity**: RISK in 9 of 10 applicable application services
- **Affected Services**: frontend, cartservice, productcatalogservice, checkoutservice, paymentservice, currencyservice, shippingservice, emailservice, recommendationservice
- **Common Finding**: No freshness signaling — no `Cache-Control` headers, no `X-Data-Age`, no consistency level indicators.
- **Portfolio-Level Recommendation**: Add freshness metadata to gRPC response trailing metadata and HTTP headers.

### DATA-Q7: PII Redaction in Logs

- **Severity**: RISK in 8 of 10 applicable application services
- **Affected Services**: frontend, cartservice, productcatalogservice, checkoutservice, paymentservice, shippingservice, emailservice, recommendationservice
- **Common Finding**: Logging statements log `userId` and potentially other PII in plaintext. No PII scrubbing middleware or masking libraries.
- **Portfolio-Level Recommendation**: Implement a portfolio-wide structured logging standard with PII-safe logging wrappers and redaction filters.

### DISC-Q1: Schema Documentation and Versioning

- **Severity**: RISK in 10 of 10 applicable application services
- **Affected Services**: All 10 application services
- **Common Finding**: Proto files define typed schemas but are not versioned (package `hipstershop` with no version qualifier). No schema registry. No proto versioning or backward-compatibility validation.
- **Portfolio-Level Recommendation**: Adopt proto package versioning and publish to a schema registry. Implement `buf` for breaking change detection in CI.

### OBS-Q1: Distributed Tracing and Structured Logging

- **Severity**: RISK in 11 of 11 applicable services
- **Affected Services**: All 11 services
- **Common Finding**: Tracing maturity varies widely. Some Go services have OpenTelemetry instrumentation (disabled by default via `ENABLE_TRACING=1`). C# cartservice has no OTel. Most services use unstructured logging. The OpenTelemetry Collector is defined in Helm but disabled (`opentelemetryCollector.create: false`).
- **Portfolio-Level Recommendation**: Enable OpenTelemetry tracing by default across all services. Deploy the OpenTelemetry Collector. Standardize structured JSON logging.

### OBS-Q2: Alerting on Error Rates and Latency

- **Severity**: RISK in 11 of 11 applicable services
- **Affected Services**: All 11 services
- **Common Finding**: No alerting configuration anywhere. No Cloud Monitoring alerting policies, no PagerDuty/OpsGenie, no SLO-based alerting.
- **Portfolio-Level Recommendation**: Create portfolio-wide alerting policies: gRPC error rate > 1%, P95 latency > 500ms, backing store failures.

### ENG-Q1: Infrastructure Governance for Agent-Facing Surface

- **Severity**: RISK in 11 of 11 applicable services
- **Affected Services**: All 11 services
- **Common Finding**: Infrastructure defined as code (Terraform, K8s manifests, Helm). Terraform validation CI exists (syntax check only). No drift detection. No `terraform plan` review step.
- **Portfolio-Level Recommendation**: Add `terraform plan` to PR comments. Implement drift detection. Enforce required reviews for infrastructure changes.

### ENG-Q2: CI/CD with API Contract Testing

- **Severity**: RISK in 11 of 11 applicable services
- **Affected Services**: All 11 services
- **Common Finding**: CI runs unit tests and deployment smoke tests. No API contract testing — no Pact, no proto breaking change detection, no consumer-driven contracts.
- **Portfolio-Level Recommendation**: Add `buf` for proto linting and breaking change detection to the shared CI pipeline.

### ENG-Q3: Rollback Capability

- **Severity**: RISK in 11 of 11 applicable services
- **Affected Services**: All 11 services
- **Common Finding**: Deployment uses Skaffold with `kubectl apply`. No automated rollback triggers. No blue/green or canary deployment.
- **Portfolio-Level Recommendation**: Implement automated rollback triggers based on error rate metrics. Consider canary deployment with Istio traffic shifting.

### ENG-Q4: API Test Coverage

- **Severity**: RISK in 11 of 11 applicable services
- **Affected Services**: All 11 services
- **Common Finding**: Tests cover basic happy-path scenarios. No edge case tests, error scenario tests, concurrent access tests, or API contract tests.
- **Portfolio-Level Recommendation**: Establish a minimum test coverage standard for agent-consumed APIs: happy path, error scenarios, concurrent access, and contract compliance.

### ENG-Q5: Encryption at Rest for Agent-Accessible Data

- **Severity**: RISK in 9 of 11 applicable services
- **Affected Services**: frontend, cartservice, productcatalogservice, checkoutservice, paymentservice, shippingservice, emailservice, recommendationservice, platform-infra
- **Common Finding**: No explicit encryption at rest configuration. Redis uses ephemeral `emptyDir` volume. No customer-managed KMS keys.
- **Portfolio-Level Recommendation**: Enable CMEK for managed databases. Configure transit encryption for all data stores.

### ENG-Q6: Cross-Origin and Network Policies

- **Severity**: RISK in 11 of 11 applicable services
- **Affected Services**: All 11 services
- **Common Finding**: Network policies, AuthorizationPolicies, and Sidecars are all defined in Helm chart templates but **disabled by default**. The default deployment has no network-level access controls. Frontend is exposed via LoadBalancer to the internet.
- **Portfolio-Level Recommendation**: Enable NetworkPolicies and AuthorizationPolicies by default. The infrastructure is already built — it just needs to be turned on.

### HITL-Q3: Sandbox/Staging Environment

- **Severity**: RISK in 10 of 10 applicable application services
- **Affected Services**: All 10 application services
- **Common Finding**: CI creates ephemeral per-PR namespaces for staging. No permanent sandbox with production-equivalent data shape. No synthetic data generators.
- **Portfolio-Level Recommendation**: Create a persistent agent-testing namespace with seed data. Add Docker Compose for local development. Create synthetic data generators.

---

## Service Dependency Map

> Dependencies were inferred from individual ARA report findings and Kubernetes manifest environment variables (not explicitly provided via `dependency_overrides`). Inferred dependencies may be incomplete — they reflect only what was observable in the assessed code and report context.

### Dependency Graph

```
                    ┌─────────────┐
                    │  frontend   │ (Not Agent-Integrable, 3B)
                    │ orchestrator│
                    └──────┬──────┘
           ┌───────┬───────┼───────┬────────┬────────┐
           ▼       ▼       ▼       ▼        ▼        ▼
      ┌────────┐┌──────┐┌──────┐┌──────┐┌───────┐┌──────┐
      │product ││cart  ││recomm││ship  ││checkout││ ad   │
      │catalog ││svc   ││svc   ││svc   ││svc     ││svc   │
      │(1B)    ││(2B)  ││(2B)  ││(2B)  ││(2B)    ││(1B)  │
      └────────┘└──┬───┘└──┬───┘└──────┘└───┬────┘└──────┘
                   │       │        ┌───────┼────────┐
                   ▼       ▼        ▼       ▼        ▼
              ┌────────┐┌──────┐┌──────┐┌───────┐┌──────┐
              │ redis  ││product││cart  ││payment││email │
              │ cart   ││catalog││svc   ││svc    ││svc   │
              └────────┘└──────┘└──────┘│(2B)   ││(2B)  │
                                        └───────┘└──────┘
                        checkoutservice also calls:
                        shippingservice, currencyservice
```

### Dependency Table

| Source Service | Target Service | Type | Description |
|---------------|---------------|------|-------------|
| frontend | productcatalogservice | sync | gRPC: list/get products |
| frontend | currencyservice | sync | gRPC: currency conversion |
| frontend | cartservice | sync | gRPC: cart management |
| frontend | recommendationservice | sync | gRPC: product recommendations |
| frontend | shippingservice | sync | gRPC: shipping quotes |
| frontend | checkoutservice | sync | gRPC: place orders |
| frontend | adservice | sync | gRPC: contextual ads |
| checkoutservice | cartservice | sync | gRPC: get/empty cart during checkout |
| checkoutservice | productcatalogservice | sync | gRPC: product detail lookup |
| checkoutservice | shippingservice | sync | gRPC: shipping cost and shipment |
| checkoutservice | currencyservice | sync | gRPC: currency conversion |
| checkoutservice | paymentservice | sync | gRPC: payment processing |
| checkoutservice | emailservice | sync | gRPC: order confirmation email |
| recommendationservice | productcatalogservice | sync | gRPC: product catalog for recommendations |
| cartservice | redis-cart | shared_db | Redis backing store for cart data |
| All services | platform-infra | shared_infra | Shared GKE cluster, Helm chart, Istio mesh, CI/CD |

### Service Dependency Metrics

| Service | Fan-In | Fan-Out | Role | Readiness Profile |
|---------|--------|---------|------|-------------------|
| platform-infra | 11 | 0 | Foundation | 🟠 Remediation Required (1B) |
| productcatalogservice | 3 | 0 | Foundation | 🟠 Remediation Required (1B) |
| currencyservice | 2 | 0 | Foundation | 🟠 Remediation Required (1B) |
| cartservice | 2 | 1 | Foundation | 🟠 Remediation Required (2B) |
| shippingservice | 2 | 0 | Internal | 🟠 Remediation Required (2B) |
| paymentservice | 1 | 0 | Internal | 🟠 Remediation Required (2B) |
| emailservice | 1 | 0 | Internal | 🟠 Remediation Required (2B) |
| adservice | 1 | 0 | Internal | 🟠 Remediation Required (1B) |
| recommendationservice | 1 | 1 | Internal | 🟠 Remediation Required (2B) |
| checkoutservice | 1 | 6 | Leaf / Orchestrator | 🟠 Remediation Required (2B) |
| frontend | 0 | 7 | Leaf / Entry Point | ❌ Not Agent-Integrable (3B) |

### High-Risk Dependency Patterns

1. **Frontend is Not Agent-Integrable but is the primary entry point** — The frontend (3 BLOCKERs: API-Q1, AUTH-Q1, DATA-Q1) renders HTML, not JSON. For agent integration, bypass the frontend and connect agents directly to backend gRPC services. The frontend's status does NOT block agent integration with backend services.

2. **platform-infra is the shared infrastructure Foundation** — All 10 application services depend on it. Its AUTH-Q1 BLOCKER (Istio AuthorizationPolicies disabled) cascades to all services. Resolving platform-infra's AUTH-Q1 first (single Helm value change) unblocks AUTH-Q1 remediation for all application services.

3. **checkoutservice is a high fan-out Orchestrator** — Depends synchronously on 6 backend services. All 6 dependencies have AUTH-Q1 BLOCKER. Agent-driven checkout requires all dependencies to resolve AUTH-Q1 first. For the initial pilot, scope the agent to read-only operations that do not require the full checkout chain.

4. **productcatalogservice is the highest-priority Foundation service** — 3 consumers (frontend, checkoutservice, recommendationservice), only 1 BLOCKER (AUTH-Q1). Closest Foundation service to becoming agent-integrable.

---

## Portfolio Remediation Guidance

> Portfolio context: Cloud-native e-commerce platform with 11 microservices evaluating for autonomous AI agent integration — customer support agent for order tracking, product recommendations, and cart management. Agent scope: read-only.

### Remediation Priority Order

1. **Identity and Access** (AUTH) — Resolve AUTH-Q1 first. No other security control can be enforced without machine identity.
2. **Data Integrity** (DATA) — Resolve DATA-Q1 second. Classify and protect sensitive data before any agent access.
3. **API Surface** (API) — Resolve API-Q1 third (frontend-specific). Ensure stable integration surface for agent tools.
4. **Remaining BLOCKERs** — Address in order of affected service count.

### Coordinated Remediation Plan

#### Phase 1: Identity Foundation (Weeks 1–6)

**BLOCKERs addressed**: AUTH-Q1 (all 11 services)

1. **Platform-level (Week 1–2)**: Set `authorizationPolicies.create: true` in `helm-chart/values.yaml`. This single change deploys AuthorizationPolicies for all services, enforcing mTLS-based caller identity via Istio service account principals. Also enable `sidecars.create: true` and `networkPolicies.create: true`.
2. **Platform-level (Week 2–3)**: Create agent-specific Kubernetes ServiceAccounts (e.g., `agent-reader-v1`) with Istio AuthorizationPolicy rules scoped to read-only operations (`GetCart`, `ListProducts`, `GetProduct`, `ListRecommendations`, `GetQuote`, `GetSupportedCurrencies`).
3. **Per-service (Week 3–6)**: Add application-layer authentication interceptors in each service for defense-in-depth. Validate caller identity and log authenticated principal.
4. **Validation**: Verify unauthenticated gRPC calls are rejected with `codes.Unauthenticated`. Verify agent ServiceAccount can only call authorized operations.

**Effort**: Low (platform enablement) + Medium (per-service hardening)

#### Phase 2: Data Protection (Weeks 3–10)

**BLOCKERs addressed**: DATA-Q1 (7 services)

1. **Portfolio-level (Week 3)**: Define data classification taxonomy: `PUBLIC` (product catalog, exchange rates, ads), `INTERNAL` (cart items, shipping quotes), `PII` (email, address, userId), `PCI` (credit card number, CVV, expiration).
2. **Portfolio-level (Week 4)**: Annotate shared `demo.proto` protobuf definitions with classification metadata for each message field.
3. **Per-service (Week 5–10)**: Implement field-level access controls in services handling PII/PCI data. Ensure read-only agents cannot access PCI fields.

**Effort**: Medium (classification) + High (field-level controls)

#### Phase 3: API Surface (Weeks 4–6)

**BLOCKERs addressed**: API-Q1 (frontend only — not cross-cutting)

- **Recommended approach**: Bypass the frontend for agent integration. Connect the customer support agent directly to backend gRPC services via an API Gateway or gRPC proxy. Backend services already expose documented, typed gRPC interfaces.
- **Alternative**: Create a dedicated REST API layer on the frontend returning JSON.

**Effort**: Low (API Gateway configuration)

---

## Service-by-Service Summary

| # | Service | Archetype | Repo Type | Agent Scope | Readiness Profile | BLOCKERs | RISKs | INFOs |
|---|---------|-----------|-----------|-------------|-------------------|----------|-------|-------|
| 1 | frontend | orchestrator | application | read-only | ❌ Not Agent-Integrable | 3 | 18 | 11 |
| 2 | cartservice | stateful-crud | application | read-only | 🟠 Remediation Required | 2 | 27 | 10 |
| 3 | checkoutservice | orchestrator | application | read-only | 🟠 Remediation Required | 2 | 25 | 11 |
| 4 | paymentservice | stateful-crud | application | read-only | 🟠 Remediation Required | 2 | 18 | 12 |
| 5 | shippingservice | stateful-crud | application | read-only | 🟠 Remediation Required | 2 | 17 | 13 |
| 6 | emailservice | event-processor | application | read-only | 🟠 Remediation Required | 2 | 10 | 19 |
| 7 | recommendationservice | data-gateway | application | read-only | 🟠 Remediation Required | 2 | 17 | 13 |
| 8 | productcatalogservice | stateless-utility | application | read-only | 🟠 Remediation Required | 1 | 12 | 18 |
| 9 | currencyservice | stateless-utility | application | read-only | 🟠 Remediation Required | 1 | 16 | 14 |
| 10 | adservice | stateless-utility | application | read-only | 🟠 Remediation Required | 1 | 12 | 18 |
| 11 | platform-infra | infrastructure-only | infrastructure-only | read-only | 🟠 Remediation Required | 1 | 9 | 4 |

**Portfolio Totals**: 19 BLOCKERs | 181 RISKs | 143 INFOs across 11 services

---

## Portfolio-Level Findings

> These questions evaluate capabilities that can only be assessed by looking across multiple repos. Individual report findings are never overridden.

### PORT-ARA-Q1: Centralized Identity Plane

- **Severity**: BLOCKER
- **Finding**: No shared identity provider exists across the portfolio. Each service has a Kubernetes ServiceAccount (pod-level identity) and the platform-infra repo defines a GCP `google_service_account` for cluster operations. However, these are infrastructure identities — not an agent-facing identity plane. No Cognito, Okta, or centralized OAuth2 authorization server exists. Istio could provide mTLS-based identity via ServiceAccount principals, but AuthorizationPolicies are disabled.
- **Recommendation**: Enable Istio as the centralized identity plane by setting `authorizationPolicies.create: true`. Create agent-specific Kubernetes ServiceAccounts with scoped AuthorizationPolicy rules. For external agent callers, deploy an API Gateway with OAuth2/API key authentication.

### PORT-ARA-Q2: Cross-Service Audit Correlation

- **Severity**: RISK
- **Finding**: Cross-service audit correlation is partially supported but not consistently enabled. Frontend and some Go services have OpenTelemetry instrumentation (disabled by default). C# cartservice has no OTel. The Helm chart defines an optional OpenTelemetry Collector (`opentelemetryCollector.create: false`). No centralized log aggregation with correlation IDs.
- **Recommendation**: Enable OpenTelemetry tracing by default. Deploy the OpenTelemetry Collector. Add OTel SDK to cartservice. Ensure consistent `traceparent` header propagation.

### PORT-ARA-Q3: Portfolio-Level Rate Limiting

- **Severity**: RISK
- **Finding**: No shared WAF, API Gateway, or portfolio-level rate limiting. Frontend is exposed directly to the internet via LoadBalancer on port 80 with no rate limiting. Individual services have no application-level rate limiting.
- **Recommendation**: Deploy an Istio Ingress Gateway or GKE Gateway API with rate limiting. Define per-identity rate limits for agent traffic.

### PORT-ARA-Q4: Transitive Dependency Safety

- **Severity**: RISK
- **Finding**: No services currently have Agent-Ready or Pilot-Ready profiles, so the BLOCKER trigger is not met. However, the frontend (Not Agent-Integrable, 3B) is the web entry point with 7 backend dependencies. checkoutservice depends synchronously on 6 services that all have AUTH-Q1 BLOCKERs — resolving checkoutservice's own BLOCKERs would not make it usable until all 6 dependencies also resolve AUTH-Q1.
- **Recommendation**: Bypass the frontend for agent integration. Prioritize AUTH-Q1 remediation for Foundation services before attempting agent integration with orchestrator services.

### PORT-ARA-Q5: Agent Identity Governance

- **Severity**: RISK
- **Finding**: No centralized mechanism to suspend or revoke agent identities across all services simultaneously. Istio AuthorizationPolicy changes require per-service Helm/Kubernetes deployment. No portfolio-level kill switch.
- **Recommendation**: Create a centralized agent identity registry. Implement suspension via `kubectl delete serviceaccount` which revokes the agent's mTLS identity across all services simultaneously.

---

## Agentic Program Recommendations

> No specific agentic program recommendations based on current findings. The portfolio has **0 Agent-Ready and 0 Pilot-Ready services** — the EBA-Agentic AI trigger condition (≥1 service at Agent-Ready or Pilot-Ready) is not met.

### Path to EBA-Agentic AI Eligibility

The following services are closest to Pilot-Ready (fewest BLOCKERs):

| Service | BLOCKERs | Blocker(s) | Path to Pilot-Ready |
|---------|----------|------------|---------------------|
| productcatalogservice | 1 | AUTH-Q1 | Resolve AUTH-Q1 via Istio enablement. 12 RISKs — needs RISK reduction to ≤5 for Pilot-Ready. |
| currencyservice | 1 | AUTH-Q1 | Resolve AUTH-Q1. 16 RISKs — needs RISK reduction to ≤5 for Pilot-Ready. |
| adservice | 1 | AUTH-Q1 | Resolve AUTH-Q1. 12 RISKs — needs RISK reduction to ≤5 for Pilot-Ready. |

**Recommended approach**: Focus AUTH-Q1 remediation on productcatalogservice first (highest-priority Foundation service, P0, 3 consumers). Once AUTH-Q1 is resolved portfolio-wide via Istio enablement, productcatalogservice, currencyservice, and adservice become candidates for accelerated RISK remediation toward Pilot-Ready status.

Once any service reaches Pilot-Ready, the portfolio qualifies for **EBA-Agentic AI** engagement. Contact your AWS Solutions Architect to discuss timing.

**Suggested timing**: Re-assess after completing the Identity Foundation remediation (Phase 1). If productcatalogservice or adservice achieve Pilot-Ready status, request EBA engagement to accelerate the initial agent pilot for product catalog queries.
