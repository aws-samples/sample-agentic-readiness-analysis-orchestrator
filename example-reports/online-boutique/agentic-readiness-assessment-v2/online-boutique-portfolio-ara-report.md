# Portfolio Agentic Readiness Assessment Report

**Date**: 2026-04-16
**Services Assessed**: 11
**Portfolio Context**: Cloud-native e-commerce platform with 11 microservices. Evaluating for autonomous AI agent integration (customer support agent for order tracking, product recommendations, and cart management).
**Agent Scope**: read-only
**Assessment Framework**: TD v2 — 43 questions, core/extended tiers, service archetypes
**Status**: Post-remediation (Istio mTLS, OTel, proto versioning, data classification, HPAs, monitoring alerts, rate-limit EnvoyFilter)

---

## Executive Dashboard

### Readiness Distribution

| Profile | Services | Percentage | Description |
|---------|----------|------------|-------------|
| ✅ Agent-Ready | 0 | 0% | 0 blockers, 0–2 risks — broad agent deployment |
| 🟡 Pilot-Ready | 10 | 91% | 0 blockers — narrow supervised pilot |
| 🟠 Remediation Required | 1 | 9% | 1+ blockers — remediate before any agent deployment |
| ❌ Not Agent-Integrable | 0 | 0% | 3+ blockers — deferred or descoped |

### Portfolio Summary

| Metric | Value |
|--------|-------|
| Total Services Assessed | 11 |
| Services Ready for Agents (Agent-Ready + Pilot-Ready) | 10 (91%) |
| Services Requiring Remediation | 1 (9%) |
| Total BLOCKERs across Portfolio | 1 (single service — frontend) |
| Total Unique BLOCKER Question IDs | 1 (API-Q1) |
| Total RISKs across Portfolio | 119 (sum across all services) |
| Cross-Cutting BLOCKERs (same blocker in 2+ repos) | 0 |
| Cross-Cutting RISKs (same risk in 3+ repos) | 8 |
| Services with Write-Enabled Agent Scope | 0 (0%) |
| Services with Read-Only Agent Scope | 11 (100%) |

### Repo Type Distribution

| Repo Type | Count | Percentage |
|-----------|-------|------------|
| application | 10 | 91% |
| infrastructure-only | 1 | 9% |

### Blocker Heatmap by Section

| Section | Repos Blocked | Applicable Repos | Percentage | Top Blocker Questions |
|---------|---------------|-------------------|------------|-----------------------|
| API | 1 | 10 | 10% | API-Q1 |
| AUTH | 0 | 11 | 0% | — |
| STATE | 0 | 10 | 0% | — |
| HITL | 0 | 10 | 0% | — |
| DATA | 0 | 10 | 0% | — |
| DISC | 0 | 10 | 0% | — |
| OBS | 0 | 11 | 0% | — |
| ENG | 0 | 11 | 0% | — |

> Only 1 section (API) has any BLOCKERs, and only in 1 service (frontend). All other sections are BLOCKER-free across the entire portfolio.

### Readiness Snapshot

```yaml
assessment_date: "2026-04-16"
total_services: 11
agent_ready: 0
pilot_ready: 10
remediation_required: 1
not_integrable: 0
total_blockers: 1
total_risks: 119
total_infos: 236
cross_cutting_blockers: 0
cross_cutting_risks: 8
portfolio_level_blockers: 0
portfolio_level_risks: 2
write_enabled_services: 0
read_only_services: 11
```

---

## Cross-Cutting BLOCKERs — Same Blocker in 2+ Repos

**None identified.**

The only BLOCKER in the portfolio is API-Q1 on `frontend` — the frontend serves HTML pages via Go templates with no machine-readable API. This is a single-service blocker, not a cross-cutting gap. All other 10 services expose gRPC APIs with `.proto` definitions and are BLOCKER-free.

---

## Cross-Cutting RISKs — Same Risk in 3+ Repos

> These are RISK-severity questions that appear in 3 or more repositories.
> They represent portfolio-wide patterns warranting coordinated attention.
> Questions scored as N/A for a service do not count as gaps for that service.


### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK in 6 of 11 applicable services

- **Affected Services**: frontend, cartservice, checkoutservice, paymentservice, shippingservice, platform-infra
- **Common Finding**: Istio AuthorizationPolicies provide service-to-service mTLS enforcement, but no agent-specific RBAC roles exist. Platform-infra has no GKE Workload Identity or agent-scoped Kubernetes RBAC bindings. Application services rely on Istio mesh-level identity but lack fine-grained per-agent permission scoping within the application layer.
- **Compensating Controls**: Istio mTLS + AuthorizationPolicies enforce service-level access. Agent scope is read-only, limiting blast radius. Define agent-specific Kubernetes RBAC roles during pilot.
- **Portfolio-Level Recommendation**: Define GKE Workload Identity bindings per service. Create agent-specific Kubernetes RBAC roles with read-only access scoped to specific namespaces and resources.
- **Estimated Effort**: Medium

### AUTH-Q5: Credential Management — RISK in 5 of 10 applicable services

- **Affected Services**: frontend, cartservice, checkoutservice, paymentservice, shippingservice
- **Common Finding**: Service credentials (Redis connection strings, gRPC endpoint addresses) are passed via environment variables in Kubernetes manifests without Secrets Manager integration. No automated credential rotation. Redis password for cartservice is a plaintext Kubernetes Secret.
- **Compensating Controls**: Kubernetes Secrets provide basic credential isolation. Istio mTLS encrypts all inter-service traffic. Read-only agent scope limits credential exposure risk.
- **Portfolio-Level Recommendation**: Migrate sensitive credentials to a secrets management solution (e.g., Kubernetes External Secrets with AWS Secrets Manager or GCP Secret Manager). Implement automated rotation for Redis and database credentials.
- **Estimated Effort**: Medium

### API-Q2: Machine-Readable API Specification — RISK in 4 of 10 applicable services

- **Affected Services**: cartservice, checkoutservice, paymentservice, shippingservice
- **Common Finding**: gRPC `.proto` files define the service contracts and are now versioned with `buf.yaml`, but no standalone OpenAPI or AsyncAPI specification exists for HTTP-layer consumers. Proto files serve as the machine-readable contract for gRPC clients but lack human-readable documentation annotations.
- **Compensating Controls**: Proto files with buf linting provide a versioned, machine-readable contract. gRPC reflection can be enabled for runtime discovery. Agent tooling can consume proto definitions directly.
- **Portfolio-Level Recommendation**: Add `buf generate` to CI to produce gRPC documentation. Consider gRPC-Gateway for services that need REST/JSON alongside gRPC.
- **Estimated Effort**: Low

### API-Q3: Structured Error Responses — RISK in 5 of 10 applicable services

- **Affected Services**: frontend, checkoutservice, currencyservice, shippingservice, cartservice
- **Common Finding**: gRPC services return standard gRPC status codes but lack structured error detail payloads with retryable indicators. Error messages are human-readable strings without machine-parseable error codes or retry guidance. Frontend returns HTTP error pages (HTML) with no structured JSON error body.
- **Compensating Controls**: gRPC status codes (UNAVAILABLE, DEADLINE_EXCEEDED, etc.) provide basic retry semantics. Agent tooling can map gRPC codes to retry behavior.
- **Portfolio-Level Recommendation**: Adopt `google.rpc.Status` with `google.rpc.ErrorInfo` detail messages across all gRPC services. Add `retryable` field to error metadata.
- **Estimated Effort**: Low

### AUTH-Q3: Action-Level Authorization — RISK in 4 of 11 applicable services

- **Affected Services**: checkoutservice, paymentservice, shippingservice, platform-infra
- **Common Finding**: Istio AuthorizationPolicies enforce which services can call which other services, but no per-RPC or per-method authorization exists within services. An authenticated caller can invoke any RPC on a service. Platform-infra lacks agent-specific Kubernetes RBAC differentiating read vs. write operations.
- **Compensating Controls**: Agent scope is read-only — write RPCs are not invoked. Istio policies restrict caller identity at the service level.
- **Portfolio-Level Recommendation**: Add per-RPC authorization checks in gRPC interceptors. Define method-level Istio AuthorizationPolicy rules for agent service accounts.
- **Estimated Effort**: Medium

### AUTH-Q8: Agent Identity Suspension — RISK in 4 of 10 applicable services

- **Affected Services**: frontend, checkoutservice, paymentservice, shippingservice
- **Common Finding**: No mechanism to suspend an individual agent identity at runtime. Istio mTLS certificates are service-level, not agent-level. Suspending an agent would require modifying Istio AuthorizationPolicies or revoking the agent's Kubernetes ServiceAccount — both require cluster-level changes.
- **Compensating Controls**: Istio AuthorizationPolicy can be updated to deny traffic from a specific source principal. Read-only scope limits the impact of a misbehaving agent.
- **Portfolio-Level Recommendation**: Implement an agent identity registry with instant revocation capability. Define a runbook for emergency agent suspension via Istio policy update.
- **Estimated Effort**: Low

### OBS-Q3: Agent-Specific Metrics — RISK in 8 of 10 applicable services

- **Affected Services**: frontend, cartservice, checkoutservice, paymentservice, shippingservice, currencyservice, recommendationservice, emailservice
- **Common Finding**: OTel Collector is deployed and collecting traces/metrics, but no agent-specific metrics (agent request rate, agent error rate, agent latency percentiles) are defined. Metrics are service-level, not segmented by caller identity. Monitoring alerts cover service health but not agent-specific behavior.
- **Compensating Controls**: OTel distributed tracing allows post-hoc filtering by caller. Istio telemetry can segment by source principal.
- **Portfolio-Level Recommendation**: Add agent identity labels to OTel spans and Istio telemetry. Create agent-specific Grafana dashboards segmenting traffic by caller principal.
- **Estimated Effort**: Low

### DISC-Q2: Contract Testing in CI — RISK in 6 of 10 applicable services

- **Affected Services**: frontend, cartservice, checkoutservice, paymentservice, shippingservice, currencyservice
- **Common Finding**: Proto files are versioned with `buf.yaml` and buf lint runs in CI, but no consumer-driven contract tests exist. Breaking proto changes are caught by buf breaking checks, but there is no verification that downstream consumers (including agents) can still parse responses correctly after schema evolution.
- **Compensating Controls**: Buf breaking change detection prevents backward-incompatible proto changes. Proto versioning provides a stable contract baseline.
- **Portfolio-Level Recommendation**: Add consumer-driven contract tests using buf breaking with wire-compatible checks. Implement agent integration smoke tests in CI.
- **Estimated Effort**: Medium

---

## Service Dependency Map

### Dependency Overview

> Dependencies inferred from individual ARA report findings (gRPC client calls observed in source code and report context).

| Source Service | Target Service | Type | Description |
|---------------|---------------|------|-------------|
| frontend | cartservice | sync | gRPC — manages shopping cart (AddItem, GetCart, EmptyCart) |
| frontend | productcatalogservice | sync | gRPC — product listing and detail (ListProducts, GetProduct) |
| frontend | currencyservice | sync | gRPC — currency conversion (GetSupportedCurrencies, Convert) |
| frontend | shippingservice | sync | gRPC — shipping cost quotes (GetQuote) |
| frontend | recommendationservice | sync | gRPC — product recommendations (ListRecommendations) |
| frontend | checkoutservice | sync | gRPC — checkout orchestration (PlaceOrder) |
| frontend | adservice | sync | gRPC — contextual ads (GetAds) |
| checkoutservice | cartservice | sync | gRPC — retrieve and empty cart during checkout |
| checkoutservice | productcatalogservice | sync | gRPC — look up product details for order |
| checkoutservice | currencyservice | sync | gRPC — convert prices during checkout |
| checkoutservice | shippingservice | sync | gRPC — get shipping cost and create shipment |
| checkoutservice | paymentservice | sync | gRPC — charge credit card |
| checkoutservice | emailservice | sync | gRPC — send order confirmation email |
| recommendationservice | productcatalogservice | sync | gRPC — fetch product catalog for filtering |
| cartservice | Redis | shared_db | Redis backing store for cart state |
| platform-infra | all services | shared_infra | Kubernetes manifests, Istio mesh, OTel Collector, Helm charts |

### Service Dependency Metrics

| Service | Fan-In | Fan-Out | Role | Readiness Profile |
|---------|--------|---------|------|-------------------|
| productcatalogservice | 3 | 0 | Foundation | 🟡 Pilot-Ready |
| currencyservice | 2 | 0 | Internal | 🟡 Pilot-Ready |
| cartservice | 2 | 1 | Internal | 🟡 Pilot-Ready |
| shippingservice | 2 | 0 | Internal | 🟡 Pilot-Ready |
| paymentservice | 1 | 0 | Leaf | 🟡 Pilot-Ready |
| emailservice | 1 | 0 | Leaf | 🟡 Pilot-Ready |
| adservice | 1 | 0 | Leaf | 🟡 Pilot-Ready |
| recommendationservice | 1 | 1 | Internal | 🟡 Pilot-Ready |
| checkoutservice | 1 | 6 | Orchestrator | 🟡 Pilot-Ready |
| frontend | 0 | 7 | Edge/Gateway | 🟠 Remediation Required |
| platform-infra | 0 | 0 | Shared Infra | 🟡 Pilot-Ready |

### Dependency-Aware Readiness Insights

1. **Foundation Service — productcatalogservice (Fan-In=3, Pilot-Ready)**
   - Depended on by: frontend, checkoutservice, recommendationservice
   - Status: Pilot-Ready with 0 BLOCKERs and only 5 RISKs — the lowest risk count of any application service
   - Assessment: Safe foundation for agent integration. No transitive blocker risk.

2. **Orchestrator — checkoutservice (Fan-Out=6, Pilot-Ready)**
   - Depends on: cartservice, productcatalogservice, currencyservice, shippingservice, paymentservice, emailservice
   - Status: Pilot-Ready. All 6 downstream services are also Pilot-Ready.
   - Assessment: Full checkout flow is agent-ready for supervised pilot. No transitive blockers in the dependency chain.

3. **Edge Gateway — frontend (Fan-Out=7, Remediation Required)**
   - The only service with a BLOCKER (API-Q1: HTML-only, no machine-readable API)
   - All 7 downstream services are Pilot-Ready
   - Assessment: Agents should bypass the frontend and call backend gRPC services directly. The frontend's BLOCKER does not propagate to backend services. For the customer support agent use case (order tracking, recommendations, cart management), direct gRPC calls to checkoutservice, cartservice, productcatalogservice, and recommendationservice are viable.

4. **Shared Infrastructure — platform-infra (Pilot-Ready)**
   - Provides: Kubernetes manifests, Istio mTLS, OTel Collector, Helm charts for all services
   - Status: Pilot-Ready with 0 BLOCKERs. Istio mTLS resolves AUTH-Q1 portfolio-wide. OTel Collector provides distributed tracing.
   - Assessment: Infrastructure layer is ready to support agent pilot deployment.

---

## Portfolio Remediation Guidance

> Portfolio context: Cloud-native e-commerce platform with 11 microservices. Evaluating for autonomous AI agent integration (customer support agent for order tracking, product recommendations, and cart management). Agent scope: read-only.

### Remediation Priority Order

With only 1 BLOCKER remaining in the entire portfolio, remediation is focused and targeted:

1. **API Surface** — Resolve the single remaining BLOCKER (frontend API-Q1)
2. **Cross-Cutting RISKs** — Address the 8 cross-cutting RISKs to move services from Pilot-Ready toward Agent-Ready

### Single Remaining BLOCKER: frontend API-Q1

**Question**: Documented API Interface — Does the service expose a machine-readable API?
**Severity**: BLOCKER
**Impact**: 1 of 11 services (frontend only)

- **Finding**: The frontend serves HTML pages via Go `html/template`. Routes (`/`, `/product/{id}`, `/cart`, `/cart/checkout`) return rendered HTML, not structured data. An agent cannot consume HTML responses as tool output. Two minor JSON endpoints exist (`/product-meta/{ids}`, `/bot`) but are internal UI helpers, not a documented API.
- **Root Cause**: The frontend was designed as a human-facing web UI, not a machine-consumable API gateway.
- **Remediation Options**:
  - **Option A (Recommended for agent use case)**: Bypass the frontend entirely. Direct the customer support agent to call backend gRPC services directly — `cartservice` for cart management, `productcatalogservice` for product lookups, `checkoutservice` for order tracking, `recommendationservice` for recommendations. This is viable because all backend services are Pilot-Ready with well-defined `.proto` contracts.
  - **Option B (Full remediation)**: Add a REST/JSON API layer to the frontend alongside the HTML UI. Expose endpoints like `GET /api/v1/products`, `GET /api/v1/cart`, `POST /api/v1/cart/items` that return JSON. Reuse existing gRPC client calls in `rpc.go`. Add an OpenAPI spec. Estimated effort: 60–90 days.
  - **Option C (Content negotiation)**: Add `Accept: application/json` support to existing routes. Return JSON when the agent requests it, HTML when a browser requests it. Lower effort than Option B but still requires response serialization work.
- **Estimated Effort**: Low (Option A — architectural decision, no code changes) / High (Option B — 60–90 days)
- **Priority**: Critical for frontend integration, but not blocking the agent pilot if Option A is adopted
- **Recommendation**: Adopt Option A for the initial pilot. The customer support agent can operate entirely through backend gRPC services. Schedule Option B as a follow-up to enable frontend-mediated agent workflows (currency conversion, cart aggregation, recommendation fetching in a single orchestrated call).

---

## Agentic Program Recommendations

> These are engagement-level recommendations based on the portfolio's agentic readiness
> profile. Discuss with your AWS Solutions Architect to determine eligibility and timing.

| Program | Relevance | Trigger Findings | Next Step |
|---------|-----------|-----------------|-----------|
| EBA-Agentic AI | ✅ TRIGGERED — 10 of 11 services are Pilot-Ready | 91% of the portfolio is ready for supervised agent pilot deployment. All backend gRPC services have 0 BLOCKERs. Istio mTLS provides machine identity. OTel provides distributed tracing. | Request EBA engagement via AWS Solutions Architect |

### Program Details

#### EBA-Agentic AI (Experience-Based Acceleration for Agentic AI)

- **Why triggered**: 10 of 11 services (91%) have readiness profile Pilot-Ready with 0 BLOCKERs. The portfolio has strong infrastructure foundations — Istio mTLS for machine identity, OTel for distributed tracing, proto-versioned APIs with buf linting, data classification labels, HPAs for capacity, and monitoring alerts. The customer support agent use case (order tracking, product recommendations, cart management) can be fully served by the 10 Pilot-Ready backend services.
- **What it provides**: Guided acceleration for agentic AI integration — architecture review, agent design patterns, tool definition authoring, pilot deployment playbook, and production readiness checklist.
- **Recommended scope**: Start with a read-only customer support agent pilot targeting `cartservice`, `productcatalogservice`, `checkoutservice`, and `recommendationservice` — the four services most relevant to the agent use case, all Pilot-Ready with low risk counts.
- **Next step**: Request EBA engagement via AWS Solutions Architect. Bring this portfolio ARA report and the individual service reports as input to the engagement kickoff.

---

## Service-by-Service Summary

| # | Service | Archetype | Repo Type | Agent Scope | Readiness Profile | BLOCKERs | RISKs | INFOs | N/A |
|---|---------|-----------|-----------|-------------|-------------------|----------|-------|-------|-----|
| 1 | frontend | orchestrator | application | read-only | 🟠 Remediation Required | 1 | 16 | 23 | 0 |
| 2 | cartservice | stateful-crud | application | read-only | 🟡 Pilot-Ready | 0 | 13 | 26 | 0 |
| 3 | checkoutservice | orchestrator | application | read-only | 🟡 Pilot-Ready | 0 | 17 | 20 | 0 |
| 4 | paymentservice | stateful-crud | application | read-only | 🟡 Pilot-Ready | 0 | 14 | 25 | 0 |
| 5 | shippingservice | stateful-crud | application | read-only | 🟡 Pilot-Ready | 0 | 13 | 20 | 0 |
| 6 | emailservice | event-processor | application | read-only | 🟡 Pilot-Ready | 0 | 7 | 24 | 0 |
| 7 | recommendationservice | data-gateway | application | read-only | 🟡 Pilot-Ready | 0 | 11 | 25 | 0 |
| 8 | productcatalogservice | stateless-utility | application | read-only | 🟡 Pilot-Ready | 0 | 5 | 27 | 0 |
| 9 | currencyservice | stateless-utility | application | read-only | 🟡 Pilot-Ready | 0 | 12 | 19 | 0 |
| 10 | adservice | stateless-utility | application | read-only | 🟡 Pilot-Ready | 0 | 5 | 26 | 0 |
| 11 | platform-infra | infrastructure-only | infrastructure-only | read-only | 🟡 Pilot-Ready | 0 | 6 | 8 | 29 |
| | **Portfolio Total** | | | | | **1** | **119** | **236** | **29** |

### Archetype Distribution

| Archetype | Count | Services |
|-----------|-------|----------|
| orchestrator | 2 | frontend, checkoutservice |
| stateful-crud | 3 | cartservice, paymentservice, shippingservice |
| stateless-utility | 3 | productcatalogservice, currencyservice, adservice |
| data-gateway | 1 | recommendationservice |
| event-processor | 1 | emailservice |
| infrastructure-only | 1 | platform-infra |

### Pilot Candidate Ranking

Services ranked by readiness for the customer support agent pilot (lowest risk count + highest relevance to use case):

| Rank | Service | RISKs | Relevance to Agent Use Case |
|------|---------|-------|-----------------------------|
| 1 | productcatalogservice | 5 | Product lookups for order tracking and recommendations |
| 2 | adservice | 5 | Contextual product suggestions |
| 3 | platform-infra | 6 | Infrastructure supporting all services |
| 4 | emailservice | 7 | Order confirmation status |
| 5 | recommendationservice | 11 | Product recommendations |
| 6 | currencyservice | 12 | Price conversion for multi-currency support |
| 7 | cartservice | 13 | Cart management (core agent use case) |
| 8 | shippingservice | 13 | Shipping cost and tracking |
| 9 | paymentservice | 14 | Payment status queries |
| 10 | checkoutservice | 17 | Order orchestration and tracking |

---

## Delta: Before vs. After Remediation

> Comparison of portfolio readiness before and after applying remediation changes
> (Istio mTLS, OTel + alerts, proto versioning + buf.yaml, data classification, HPAs, rate-limit EnvoyFilter).

### Readiness Profile Changes

| Profile | Before | After | Delta |
|---------|--------|-------|-------|
| ✅ Agent-Ready | 0 | 0 | — |
| 🟡 Pilot-Ready | 0 | 10 | +10 |
| 🟠 Remediation Required | 11 | 1 | −10 |
| ❌ Not Agent-Integrable | 0 | 0 | — |

### Key Metrics Delta

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Total BLOCKERs (sum) | ~55+ | 1 | −54 |
| Services with 0 BLOCKERs | 0 | 10 | +10 |
| Cross-Cutting BLOCKERs | 5+ | 0 | Eliminated |
| Services ready for pilot | 0 | 10 (91%) | +91% |
| EBA-Agentic AI triggered | No | Yes | ✅ |

### Remediation Actions and Impact

| Remediation Action | Questions Resolved | Services Impacted | Impact |
|--------------------|-------------------|-------------------|--------|
| Istio mTLS enabled | AUTH-Q1 (Machine Identity) | All 11 services | Eliminated the most widespread BLOCKER — every service now has machine identity via Istio mTLS certificates |
| OTel Collector deployed | OBS-Q1 (Distributed Tracing) | All 11 services | Distributed tracing and structured logging across the portfolio |
| Monitoring alerts added | OBS-Q2 (Alerting) | All 11 services | Error rate and latency alerting for all services |
| Proto versioned + buf.yaml | DISC-Q1 (Schema Versioning) | 10 application services | Versioned API contracts with breaking change detection |
| Data classification labels | DATA-Q1 (Sensitive Data) | 7 services | PII fields classified and tagged in data stores |
| HPAs configured | STATE-Q7 (Capacity) | 10 application services | Auto-scaling for agent traffic patterns |
| Rate-limit EnvoyFilter | STATE-Q5 (Rate Limiting), ENG-Q6 (Network Policies) | All 11 services | Portfolio-wide rate limiting at the mesh layer |

### Remaining Gap: frontend API-Q1

The single remaining BLOCKER (frontend API-Q1: HTML-only, no machine-readable API) was not resolved by the infrastructure-level remediations because it requires application-level changes to the frontend service. This is an architectural gap — the frontend was designed as a human-facing web UI — not a missing infrastructure control.

**Mitigation**: For the customer support agent pilot, bypass the frontend and call backend gRPC services directly. All 10 backend services are Pilot-Ready with well-defined proto contracts.

---

## Portfolio-Level Questions

### PORT-ARA-Q1: Centralized Identity Plane
- **Severity**: INFO
- **Finding**: Istio mTLS provides a shared identity plane across all 11 services. Every service has a unique SPIFFE identity via Istio's Citadel CA. AuthorizationPolicies enforce service-to-service access control using these identities. This is a strong centralized identity plane for the Kubernetes-native portfolio.
- **Gap**: None for service-to-service identity. Agent-specific identity (distinct from service identity) is not yet defined — agents would authenticate as the service they call through, not as a distinct principal.

### PORT-ARA-Q2: Cross-Service Audit Correlation
- **Severity**: RISK
- **Finding**: OTel Collector propagates trace IDs (W3C `traceparent` header) across all gRPC calls, enabling end-to-end trace correlation. However, no centralized immutable audit trail (e.g., CloudTrail equivalent) exists for compliance-grade audit logging. Traces are observability data, not audit records.
- **Gap**: Distributed tracing exists but immutable audit logging with principal attribution is not implemented at the portfolio level.

### PORT-ARA-Q3: Portfolio-Level Rate Limiting
- **Severity**: INFO
- **Finding**: Rate-limit EnvoyFilter is deployed at the Istio mesh layer, providing portfolio-wide rate limiting for all services. This is a shared infrastructure control that protects all services from agent traffic storms.
- **Gap**: None — portfolio-level rate limiting is in place.

### PORT-ARA-Q4: Transitive Dependency Safety
- **Severity**: INFO
- **Finding**: All 10 backend services are Pilot-Ready with 0 BLOCKERs. No transitive blocker propagation exists in the dependency chain. The only blocked service (frontend) is the edge gateway — its BLOCKER does not propagate to downstream services because agents can call backend services directly.

### PORT-ARA-Q5: Portfolio Governance and Change Coordination
- **Severity**: RISK
- **Finding**: Buf breaking change detection and proto versioning provide API contract governance. However, no portfolio-wide change coordination process exists for agent-impacting changes (e.g., a proto field rename that breaks agent tool definitions). No agent integration test suite runs across the portfolio.
- **Gap**: Per-service CI exists but no portfolio-level agent integration testing or change coordination process.

---

*Report generated by AWS Transform Custom — Portfolio Agentic Readiness Assessment*
*Framework: TD v2 — 43 questions, core/extended tiers, service archetypes*
*Post-remediation assessment — Istio mTLS, OTel, proto versioning, data classification, HPAs, monitoring alerts, rate-limit EnvoyFilter applied*
