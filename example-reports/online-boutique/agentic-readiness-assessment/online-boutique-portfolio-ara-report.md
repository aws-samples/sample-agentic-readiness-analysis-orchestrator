# Portfolio Agentic Readiness Assessment Report

**Date**: 2026-04-15
**Services Assessed**: 11
**Portfolio Context**: Cloud-native e-commerce platform with 11 microservices. Evaluating for autonomous AI agent integration (customer support agent for order tracking, product recommendations, and cart management) and modernization maturity.

---

## Executive Dashboard

### Readiness Distribution

| Profile | Services | Percentage | Description |
|---------|----------|------------|-------------|
| ✅ Agent-Ready | 0 | 0% | 0 blockers, 0–2 risks — broad agent deployment |
| 🟡 Pilot-Ready | 0 | 0% | 0 blockers, 3–5 risks — narrow pilot only |
| 🟠 Remediation Required | 4 | 36% | 1–2 blockers — remediate before any agent deployment |
| ❌ Not Agent-Integrable | 7 | 64% | 3+ blockers — deferred or descoped |

### Portfolio Summary

| Metric | Value |
|--------|-------|
| Total Services Assessed | 11 |
| Services Ready for Agents (Agent-Ready + Pilot-Ready) | 0 (0%) |
| Services Requiring Remediation | 11 (100%) |
| Total Unique BLOCKERs Across Portfolio | 3 (AUTH-Q1, DATA-Q1, ENG-Q6) |
| Total Unique RISKs Across Portfolio | 36 |
| Cross-Cutting BLOCKERs (same blocker in 2+ repos) | 3 |
| Cross-Cutting RISKs (same risk in 3+ repos) | 35 |
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
| AUTH | 10 | 91% (10 of 11) | AUTH-Q1 |
| ENG | 10 | 91% (10 of 11) | ENG-Q6 |
| DATA | 8 | 80% (8 of 10) | DATA-Q1 |
| API | 0 | 0% (0 of 10) | — |
| STATE | 0 | 0% (0 of 10) | — |
| HITL | 0 | 0% (0 of 10) | — |
| DISC | 0 | 0% (0 of 10) | — |
| OBS | 0 | 0% (0 of 11) | — |

### Readiness Snapshot

| Metric | Value |
|--------|-------|
| assessment_date | 2026-04-15 |
| total_services | 11 |
| agent_ready | 0 |
| pilot_ready | 0 |
| remediation_required | 4 |
| not_integrable | 7 |
| total_blockers | 28 |
| total_risks | 346 |
| total_infos | 131 |
| cross_cutting_blockers | 3 |
| cross_cutting_risks | 35 |
| portfolio_level_blockers | 1 |
| portfolio_level_risks | 4 |
| write_enabled_services | 0 |
| read_only_services | 11 |

---

## Cross-Cutting BLOCKERs — Same Blocker in 2+ Repos

> These are BLOCKER-severity questions that appear in 2 or more repositories.
> They represent portfolio-wide agentic readiness gaps requiring coordinated remediation.
> Questions scored as N/A for a service do not count as gaps for that service.

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER in 10 of 11 applicable services
- **Affected Services**: adservice, cartservice, checkoutservice, currencyservice, emailservice, frontend, paymentservice, productcatalogservice, recommendationservice, shippingservice
- **Non-Affected**: platform-infra (scored INFO — infrastructure repo has GCP IAM service account and Kubernetes ServiceAccounts defined)
- **Common Finding**: All 10 application services use insecure gRPC credentials with zero authentication. Go services use `insecure.NewCredentials()` (frontend, checkoutservice, productcatalogservice, shippingservice), Node.js services use `grpc.ServerCredentials.createInsecure()` (paymentservice, currencyservice), Python services use `server.add_insecure_port()` (emailservice, recommendationservice), C# cartservice has no `AddAuthentication()` middleware, and Java adservice uses `ServerBuilder.forPort(port)` with no auth interceptor. No service has OAuth2 client credentials, API keys, mTLS, or any form of caller identity verification. No audit log in any service attributes requests to an authenticated principal.
- **Root Cause Pattern**: The Online Boutique was designed as a demo/sample application where inter-service trust is assumed at the network level. No identity provider or authentication middleware was ever integrated. All gRPC connections are plaintext and unauthenticated.
- **Portfolio-Level Remediation**:
  - **Approach**: Platform-level fix via Istio service mesh mTLS enforcement. The infrastructure already includes Istio Gateway configs, Helm chart AuthorizationPolicy templates (disabled: `authorizationPolicies.create: false`), and per-service Sidecar templates. Enabling mTLS at the mesh level provides transport-level authentication for all 10 services without application code changes.
  - **Immediate Action**: Set `authorizationPolicies.create: true` and `sidecars.create: true` in `helm-chart/values.yaml`. Deploy Istio PeerAuthentication in STRICT mode for the namespace. This provides mutual TLS between all services with Kubernetes ServiceAccount-based identity.
  - **Target State**: All inter-service gRPC calls authenticated via mTLS with Istio-managed certificates. Each service has a unique Kubernetes ServiceAccount identity (already defined in manifests). Agent-specific service accounts are created and distinguishable in mesh-level audit logs. For the customer support agent use case, create dedicated ServiceAccounts for agent instances calling frontend, cartservice, and productcatalogservice.
  - **Estimated Effort**: Medium (2–4 weeks for mesh-level mTLS; additional 4–8 weeks if application-level JWT auth is also required for agent-specific attribution beyond mesh identity)
  - **Priority**: Critical — Identity is the foundation for all other security controls. Cannot enforce authorization, audit logging, or data access controls without it.
  - **Dependencies**: None — this is the first blocker to resolve. ENG-Q6 (network policies) should be enabled simultaneously.

> **Portfolio Context**: PORT-ARA-Q1 found no shared identity provider (Cognito, Okta) across the portfolio. Istio mTLS with Kubernetes ServiceAccounts is the nearest available identity plane. **Verify** that enabling Istio PeerAuthentication STRICT mode does not break existing service communication patterns.

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER in 8 of 10 applicable services
- **Affected Services**: adservice, cartservice, checkoutservice, emailservice, frontend, paymentservice, recommendationservice, shippingservice
- **Non-Affected (INFO)**: currencyservice (handles only public ECB currency rates — no PII/PCI data), productcatalogservice (handles only public product catalog data — no PII/PCI data)
- **N/A**: platform-infra (infrastructure-only repo — question not applicable)
- **Common Finding**: Services handling customer data, payment information, and PII have zero data classification. Specific unclassified sensitive data includes:
  - **PCI-DSS scope**: `credit_card_number`, `credit_card_cvv`, `credit_card_expiration_year/month` (checkoutservice, paymentservice, frontend)
  - **PII**: `email`, `street_address`, `city`, `state`, `country`, `zip_code` (checkoutservice, emailservice, frontend, shippingservice)
  - **User identifiers**: `userId` as plain string (cartservice, recommendationservice)
  - **Ad tracking data**: redirect URLs (adservice — lower sensitivity but still unclassified)
  - No field-level tags, no PII detection, no data classification framework, no access control policies tied to sensitivity levels
- **Root Cause Pattern**: The application was built without a data classification policy. Sensitive fields are defined in a shared `demo.proto` with no sensitivity annotations. Data flows through services without classification metadata, making it impossible for agents to programmatically determine what data they are authorized to access.
- **Portfolio-Level Remediation**:
  - **Approach**: Hybrid — portfolio-level data classification policy + per-service field tagging
  - **Immediate Action**: Define a portfolio-wide data classification policy with at least 4 tiers: Public, Internal, Confidential (PII), Restricted (PCI). Annotate the shared `demo.proto` file with field-level sensitivity comments or custom protobuf options. For the customer support agent, explicitly classify which fields the agent may read (e.g., order status, product names) vs. which it must never access (e.g., credit card numbers, CVV).
  - **Target State**: All proto message fields annotated with sensitivity classification. Runtime field-level access controls enforce classification (e.g., agent role can read order status but not credit card data). PII fields encrypted at rest and masked in logs.
  - **Estimated Effort**: High (4–8 weeks for classification policy and proto annotation; additional 8–12 weeks for runtime enforcement across 8 services)
  - **Priority**: High — Must protect data before enabling agent read access to customer information.
  - **Dependencies**: AUTH-Q1 (machine identity) — need identity to enforce data access controls per principal.

### ENG-Q6: Cross-Origin and Network Policies

- **Severity**: BLOCKER in 10 of 11 applicable services
- **Affected Services**: adservice, cartservice, checkoutservice, currencyservice, emailservice, frontend, paymentservice, productcatalogservice, shippingservice, platform-infra
- **Non-Affected (INFO)**: recommendationservice (has NetworkPolicy restricting ingress to frontend on port 8080 and Istio AuthorizationPolicy restricting to frontend ServiceAccount)
- **Common Finding**: Network policies exist in infrastructure-as-code but are **disabled by default**. Comprehensive NetworkPolicy definitions exist in `kustomize/components/network-policies/` (deny-all baseline + 13 per-service policies) and in the Helm chart (`networkPolicies.create: false`). Istio AuthorizationPolicies are also disabled (`authorizationPolicies.create: false`). The Istio Gateway accepts `hosts: ["*"]` on HTTP port 80 with no TLS. No CORS configuration exists. All gRPC servers bind with insecure credentials. The security infrastructure is already built — it just needs to be turned on.
- **Root Cause Pattern**: Security is opt-in rather than default-on. The demo application ships with all security features disabled for ease of initial deployment. Network policies, AuthorizationPolicies, and TLS are all available in IaC but commented out or set to `create: false`.
- **Portfolio-Level Remediation**:
  - **Approach**: Platform-level fix — enable existing security infrastructure
  - **Immediate Action**: (1) Uncomment `components/network-policies` in `kustomize/kustomization.yaml` OR set `networkPolicies.create: true` in Helm values. (2) Configure TLS on the Istio Gateway (replace HTTP port 80 with HTTPS port 443, add TLS certificate). (3) Set `authorizationPolicies.create: true` in Helm values. (4) Add CORS configuration for agent-facing endpoints.
  - **Target State**: Network policies enforced as mandatory baseline. Istio Gateway configured with TLS and specific host restrictions. AuthorizationPolicies restrict inter-service communication to declared patterns. CORS policy defined for agent-facing endpoints on the frontend.
  - **Estimated Effort**: Low (1–2 weeks — policies already exist, only need enablement and TLS/CORS additions)
  - **Priority**: High — Network security should be enabled simultaneously with authentication (AUTH-Q1).
  - **Dependencies**: AUTH-Q1 (deploy authentication and network policies together for defense in depth). AUTH-Q3 (Istio AuthorizationPolicies provide action-level authorization at mesh level).

## Cross-Cutting RISKs — Same Risk in 3+ Repos

> These are RISK-severity questions that appear in 3 or more repositories.
> They represent portfolio-wide patterns warranting coordinated attention.
> Questions scored as N/A for a service do not count as gaps for that service.
> 35 cross-cutting RISKs were identified. They are listed below ordered by number of affected services (most affected first).

### AUTH-Q2: Scoped Permissions (Least Privilege)

- **Severity**: RISK in 11 of 11 applicable services
- **Affected Services**: adservice, cartservice, checkoutservice, currencyservice, emailservice, frontend, paymentservice, productcatalogservice, recommendationservice, shippingservice, platform-infra
- **Common Finding**: No scoped permission model exists across any service. All callers have full access to all RPCs.
- **Compensating Controls**: Istio AuthorizationPolicies (disabled but defined) can restrict which ServiceAccounts can call which services. Network policies (disabled but defined) provide network-level access control.
- **Portfolio-Level Recommendation**: After resolving AUTH-Q1 (identity), implement role-based access control via Istio AuthorizationPolicies. Define agent-specific roles with least-privilege access to only the RPCs needed for the customer support use case.
- **Estimated Effort**: Medium

### AUTH-Q3: Action-Level Authorization

- **Severity**: RISK in 11 of 11 applicable services
- **Affected Services**: adservice, cartservice, checkoutservice, currencyservice, emailservice, frontend, paymentservice, productcatalogservice, recommendationservice, shippingservice, platform-infra
- **Common Finding**: No action-level authorization. Once a caller can reach a service, they can invoke any RPC.
- **Compensating Controls**: Istio AuthorizationPolicies can restrict by path/method at the mesh level.
- **Portfolio-Level Recommendation**: Implement Istio AuthorizationPolicies with per-RPC restrictions. For the customer support agent, restrict to read-only RPCs (GetCart, ListProducts, GetQuote) and block write RPCs (PlaceOrder, EmptyCart) until explicit write enablement.
- **Estimated Effort**: Medium

### AUTH-Q6: Credential Management

- **Severity**: RISK in 11 of 11 applicable services
- **Affected Services**: adservice, cartservice, checkoutservice, currencyservice, emailservice, frontend, paymentservice, productcatalogservice, recommendationservice, shippingservice, platform-infra
- **Common Finding**: No credential management infrastructure. No secrets rotation, no vault integration, no managed credential lifecycle.
- **Compensating Controls**: Kubernetes Secrets provide basic secret storage. GKE Workload Identity can bind to GCP IAM.
- **Portfolio-Level Recommendation**: Deploy a centralized secrets management solution (AWS Secrets Manager, HashiCorp Vault, or GCP Secret Manager). Establish credential rotation policy for agent service accounts.
- **Estimated Effort**: Medium

### AUTH-Q7: Immutable Audit Logging

- **Severity**: RISK in 11 of 11 applicable services
- **Affected Services**: adservice, cartservice, checkoutservice, currencyservice, emailservice, frontend, paymentservice, productcatalogservice, recommendationservice, shippingservice, platform-infra
- **Common Finding**: No immutable audit logging. Services log to stdout/stderr with no tamper-proof audit trail. No principal attribution in logs (because AUTH-Q1 has no identity).
- **Compensating Controls**: OpenTelemetry collector (disabled but defined in Helm chart) can export traces to Google Cloud Trace.
- **Portfolio-Level Recommendation**: After resolving AUTH-Q1, configure structured audit logging with authenticated principal, action, resource, and timestamp. Export to immutable storage (CloudWatch Logs with retention lock, S3 with Object Lock, or Google Cloud Logging with log sink to locked bucket).
- **Estimated Effort**: Medium

### AUTH-Q8: Agent Identity Suspension

- **Severity**: RISK in 11 of 11 applicable services
- **Affected Services**: adservice, cartservice, checkoutservice, currencyservice, emailservice, frontend, paymentservice, productcatalogservice, recommendationservice, shippingservice, platform-infra
- **Common Finding**: No mechanism to suspend or revoke an agent's access. Without authentication (AUTH-Q1), there is no identity to suspend.
- **Compensating Controls**: Kubernetes RBAC can delete ServiceAccounts. Network policies can block specific pods.
- **Portfolio-Level Recommendation**: After resolving AUTH-Q1, implement centralized agent identity registry with suspension capability. Istio AuthorizationPolicies can provide immediate revocation by removing a ServiceAccount from allowed principals.
- **Estimated Effort**: Medium

### OBS-Q1: Distributed Tracing and Structured Logging

- **Severity**: RISK in 11 of 11 applicable services
- **Affected Services**: adservice, cartservice, checkoutservice, currencyservice, emailservice, frontend, paymentservice, productcatalogservice, recommendationservice, shippingservice, platform-infra
- **Common Finding**: OpenTelemetry is integrated in most services for tracing, but audit-grade structured logging with principal attribution is absent. Traces exist but are not connected to an immutable audit trail.
- **Compensating Controls**: OpenTelemetry collector defined in Helm chart (disabled by default). Services have basic stdout logging.
- **Portfolio-Level Recommendation**: Enable OpenTelemetry collector (`opentelemetryCollector.create: true`). Add structured log fields for agent principal, action, and outcome. Implement consistent trace context propagation across all services.
- **Estimated Effort**: Medium

### OBS-Q2: Alerting on Error Rates and Latency

- **Severity**: RISK in 11 of 11 applicable services
- **Affected Services**: adservice, cartservice, checkoutservice, currencyservice, emailservice, frontend, paymentservice, productcatalogservice, recommendationservice, shippingservice, platform-infra
- **Common Finding**: No alerting configured on error rates, latency thresholds, or anomaly detection. No SLOs defined.
- **Compensating Controls**: Google Cloud Operations APIs enabled in Terraform (`monitoring.googleapis.com`, `cloudtrace.googleapis.com`).
- **Portfolio-Level Recommendation**: Define portfolio-wide SLOs and configure alerting. For agent integration, set alerts on: agent-specific error rates, latency p99, and request volume anomalies.
- **Estimated Effort**: Medium

### ENG-Q1: Infrastructure Governance for Agent-Facing Surface

- **Severity**: RISK in 11 of 11 applicable services
- **Affected Services**: adservice, cartservice, checkoutservice, currencyservice, emailservice, frontend, paymentservice, productcatalogservice, recommendationservice, shippingservice, platform-infra
- **Common Finding**: No infrastructure governance for agent-facing surfaces. No policy-as-code, no OPA/Gatekeeper, no compliance scanning.
- **Compensating Controls**: Kustomize and Helm provide declarative infrastructure. GitHub CI workflow exists.
- **Portfolio-Level Recommendation**: Implement OPA Gatekeeper or Kyverno policies to enforce agent-facing surface requirements (authentication required, TLS required, network policies required).
- **Estimated Effort**: Medium

### ENG-Q2: CI/CD with API Contract Testing

- **Severity**: RISK in 11 of 11 applicable services
- **Affected Services**: adservice, cartservice, checkoutservice, currencyservice, emailservice, frontend, paymentservice, productcatalogservice, recommendationservice, shippingservice, platform-infra
- **Common Finding**: CI/CD exists (GitHub Actions, Skaffold, Cloud Build) but no API contract testing. Proto changes are not validated against consumers.
- **Compensating Controls**: Shared `demo.proto` provides a single source of truth for API contracts.
- **Portfolio-Level Recommendation**: Add proto backward-compatibility checks (buf lint, buf breaking) to CI pipeline. Implement contract testing for agent tool definitions.
- **Estimated Effort**: Low

### ENG-Q3: Rollback Capability

- **Severity**: RISK in 11 of 11 applicable services
- **Affected Services**: adservice, cartservice, checkoutservice, currencyservice, emailservice, frontend, paymentservice, productcatalogservice, recommendationservice, shippingservice, platform-infra
- **Common Finding**: Kubernetes provides basic rollback (rollout undo) but no automated rollback on API contract violations or agent-observable failures.
- **Compensating Controls**: Kubernetes Deployment rollout history. Skaffold supports rollback.
- **Portfolio-Level Recommendation**: Implement automated rollback triggers based on error rate SLOs. For agent integration, define rollback criteria for API contract breakage.
- **Estimated Effort**: Low

### ENG-Q4: API Test Coverage

- **Severity**: RISK in 11 of 11 applicable services
- **Affected Services**: adservice, cartservice, checkoutservice, currencyservice, emailservice, frontend, paymentservice, productcatalogservice, recommendationservice, shippingservice, platform-infra
- **Common Finding**: Limited or no API test coverage. Unit tests exist in some services but integration tests and agent-specific scenario tests are absent.
- **Compensating Controls**: Some services have unit tests. Load generator exists for end-to-end testing.
- **Portfolio-Level Recommendation**: Add gRPC integration tests for all agent-facing RPCs. Implement agent scenario tests that validate the customer support agent workflow (get cart, list products, get recommendations).
- **Estimated Effort**: Medium

### ENG-Q5: Encryption at Rest for Agent-Accessible Data

- **Severity**: RISK in 10 of 11 applicable services
- **Affected Services**: adservice, cartservice, checkoutservice, currencyservice, emailservice, frontend, paymentservice, productcatalogservice, shippingservice, platform-infra
- **Common Finding**: No explicit encryption at rest. Redis used for cart storage with no encryption. Product catalog loaded from JSON file. No KMS integration.
- **Compensating Controls**: GKE Autopilot provides default encryption at rest for persistent volumes.
- **Portfolio-Level Recommendation**: Enable Memorystore Redis encryption at rest (already supported in Terraform config). Add KMS encryption for sensitive data stores.
- **Estimated Effort**: Low

### AUTH-Q4: Identity Propagation

- **Severity**: RISK in 10 of 10 applicable services
- **Affected Services**: adservice, cartservice, checkoutservice, currencyservice, emailservice, frontend, paymentservice, productcatalogservice, recommendationservice, shippingservice
- **Common Finding**: No identity propagation through service call chains. The `userId` is passed as a plain string parameter, not derived from authenticated identity.
- **Compensating Controls**: Istio can propagate SPIFFE identity through the service mesh.
- **Portfolio-Level Recommendation**: After enabling Istio mTLS, configure identity propagation headers. Map agent identities to the userId parameter or add separate agent-identity metadata to gRPC calls.
- **Estimated Effort**: Medium

### AUTH-Q5: Agent-as-Self vs Agent-on-Behalf-of-User

- **Severity**: RISK in 10 of 10 applicable services
- **Affected Services**: adservice, cartservice, checkoutservice, currencyservice, emailservice, frontend, paymentservice, productcatalogservice, recommendationservice, shippingservice
- **Common Finding**: No distinction between agent-as-self and agent-on-behalf-of-user patterns. No delegation model.
- **Compensating Controls**: None.
- **Portfolio-Level Recommendation**: For the customer support agent, define a delegation model where the agent acts on behalf of a user (with user consent). Implement token exchange or scope restriction for delegated access.
- **Estimated Effort**: High

### API-Q3: Structured Error Responses

- **Severity**: RISK in 10 of 10 applicable services
- **Affected Services**: adservice, cartservice, checkoutservice, currencyservice, emailservice, frontend, paymentservice, productcatalogservice, recommendationservice, shippingservice
- **Common Finding**: Services return gRPC status codes but no structured error details. Agents cannot distinguish retriable from terminal errors.
- **Compensating Controls**: gRPC status codes provide basic error categorization.
- **Portfolio-Level Recommendation**: Implement `google.rpc.Status` with `ErrorInfo` details including error code enum, message, and `retryable` boolean across all services.
- **Estimated Effort**: Medium

### API-Q5: API Versioning and Deprecation

- **Severity**: RISK in 10 of 10 applicable services
- **Affected Services**: adservice, cartservice, checkoutservice, currencyservice, emailservice, frontend, paymentservice, productcatalogservice, recommendationservice, shippingservice
- **Common Finding**: No API versioning. Proto package is `hipstershop` with no version prefix. No deprecation policy.
- **Compensating Controls**: Shared proto file provides a single API contract.
- **Portfolio-Level Recommendation**: Adopt package-level versioning (`hipstershop.v1`). Establish deprecation policy with minimum notice period for agent consumers.
- **Estimated Effort**: Low

### STATE-Q1: Compensation and Rollback

- **Severity**: RISK in 10 of 10 applicable services
- **Affected Services**: adservice, cartservice, checkoutservice, currencyservice, emailservice, frontend, paymentservice, productcatalogservice, recommendationservice, shippingservice
- **Common Finding**: No compensation or rollback patterns. Checkout is a multi-service saga with no compensating transactions if a step fails.
- **Compensating Controls**: Agent scope is read-only, limiting blast radius.
- **Portfolio-Level Recommendation**: Implement saga pattern with compensating transactions in checkoutservice. For read-only agent scope, this is lower priority but becomes critical if agent scope is elevated to write-enabled.
- **Estimated Effort**: High

### STATE-Q4: Circuit Breakers and Resilience

- **Severity**: RISK in 10 of 10 applicable services
- **Affected Services**: adservice, cartservice, checkoutservice, currencyservice, emailservice, frontend, paymentservice, productcatalogservice, recommendationservice, shippingservice
- **Common Finding**: No circuit breakers. Some services have basic timeout configuration but no circuit breaker pattern, no bulkhead isolation.
- **Compensating Controls**: Istio can provide circuit breaking at the mesh level.
- **Portfolio-Level Recommendation**: Configure Istio DestinationRules with circuit breaker settings for all services. For the customer support agent, set conservative circuit breaker thresholds on critical-path services (checkoutservice, cartservice).
- **Estimated Effort**: Low

### STATE-Q5: Rate Limiting and Throttling

- **Severity**: RISK in 10 of 10 applicable services
- **Affected Services**: adservice, cartservice, checkoutservice, currencyservice, emailservice, frontend, paymentservice, productcatalogservice, recommendationservice, shippingservice
- **Common Finding**: No rate limiting or throttling. Services accept unlimited requests.
- **Compensating Controls**: Istio can provide rate limiting via EnvoyFilter or Wasm plugins.
- **Portfolio-Level Recommendation**: Implement rate limiting at the Istio Gateway for agent traffic. Set per-agent rate limits based on expected customer support agent request patterns.
- **Estimated Effort**: Medium

### STATE-Q7: Infrastructure Capacity for Agent Traffic

- **Severity**: RISK in 10 of 10 applicable services
- **Affected Services**: adservice, cartservice, checkoutservice, currencyservice, emailservice, frontend, paymentservice, productcatalogservice, recommendationservice, shippingservice
- **Common Finding**: No capacity planning for agent traffic. Resource limits are set for normal human traffic patterns.
- **Compensating Controls**: GKE Autopilot provides auto-scaling.
- **Portfolio-Level Recommendation**: Estimate agent traffic patterns (customer support agent: request volume for order lookups, product queries, cart reads). Validate HPA settings can handle combined human + agent load.
- **Estimated Effort**: Low

### DATA-Q2: Data Residency and Sovereignty

- **Severity**: RISK in 10 of 10 applicable services
- **Affected Services**: adservice, cartservice, checkoutservice, currencyservice, emailservice, frontend, paymentservice, productcatalogservice, recommendationservice, shippingservice
- **Common Finding**: No data residency policy. No region restrictions on data storage or processing.
- **Compensating Controls**: GKE cluster is region-specific (configured in Terraform variables).
- **Portfolio-Level Recommendation**: Define data residency requirements for customer data. Ensure agent processing remains within designated regions.
- **Estimated Effort**: Low

### DATA-Q3: Selective Query Support

- **Severity**: RISK in 10 of 10 applicable services
- **Affected Services**: adservice, cartservice, checkoutservice, currencyservice, emailservice, frontend, paymentservice, productcatalogservice, recommendationservice, shippingservice
- **Common Finding**: No field-level filtering in gRPC responses. All fields are returned regardless of caller needs.
- **Compensating Controls**: Protobuf field masks can be implemented.
- **Portfolio-Level Recommendation**: Implement gRPC FieldMask support for agent-facing RPCs. Allow agents to request only the fields they need (e.g., order status without payment details).
- **Estimated Effort**: Medium

### DATA-Q5: Reliable Timestamps

- **Severity**: RISK in 10 of 10 applicable services
- **Affected Services**: adservice, cartservice, checkoutservice, currencyservice, emailservice, frontend, paymentservice, productcatalogservice, recommendationservice, shippingservice
- **Common Finding**: No consistent timestamping across services. Some use server time, others have no timestamps on data records.
- **Compensating Controls**: OpenTelemetry traces include timestamps.
- **Portfolio-Level Recommendation**: Standardize timestamps using google.protobuf.Timestamp in all proto messages. Ensure NTP synchronization across cluster nodes.
- **Estimated Effort**: Low

### DATA-Q6: Data Freshness Signaling

- **Severity**: RISK in 10 of 10 applicable services
- **Affected Services**: adservice, cartservice, checkoutservice, currencyservice, emailservice, frontend, paymentservice, productcatalogservice, recommendationservice, shippingservice
- **Common Finding**: No data freshness metadata. Agents cannot determine if data is stale.
- **Compensating Controls**: None.
- **Portfolio-Level Recommendation**: Add `last_updated` timestamps or ETags to responses. For the customer support agent, freshness is critical for order status (must be real-time, not cached).
- **Estimated Effort**: Low

### DISC-Q1: Schema Documentation and Versioning

- **Severity**: RISK in 10 of 10 applicable services
- **Affected Services**: adservice, cartservice, checkoutservice, currencyservice, emailservice, frontend, paymentservice, productcatalogservice, recommendationservice, shippingservice
- **Common Finding**: Shared `demo.proto` provides schema but no versioning, no changelog, no field-level documentation for agent consumers.
- **Compensating Controls**: Proto file is a single source of truth. gRPC reflection can be enabled.
- **Portfolio-Level Recommendation**: Add comprehensive proto comments describing field semantics, constraints, and agent-relevant behavior. Implement proto versioning with changelog.
- **Estimated Effort**: Low

### API-Q7: Asynchronous Operation Support

- **Severity**: RISK in 9 of 10 applicable services
- **Affected Services**: adservice, cartservice, checkoutservice, currencyservice, emailservice, frontend, paymentservice, productcatalogservice, shippingservice
- **Common Finding**: No async operation support. All RPCs are synchronous request/response.
- **Compensating Controls**: gRPC supports server streaming which could be leveraged.
- **Portfolio-Level Recommendation**: For the customer support agent, async operations may be needed for order placement (if elevated to write scope). Implement gRPC server streaming or polling for long-running operations.
- **Estimated Effort**: Medium

### API-Q2: Machine-Readable API Specification

- **Severity**: RISK in 8 of 10 applicable services
- **Affected Services**: adservice, cartservice, checkoutservice, emailservice, frontend, paymentservice, productcatalogservice, shippingservice
- **Common Finding**: `demo.proto` is a shared monolith containing all service definitions. No per-service standalone specs. Agent tool definitions must parse the full monolith.
- **Compensating Controls**: Proto file is machine-readable. gRPC reflection can expose per-service methods.
- **Portfolio-Level Recommendation**: Extract per-service proto files. Enable gRPC reflection service in all services for runtime API discovery.
- **Estimated Effort**: Low

### STATE-Q2: Queryable Current State

- **Severity**: RISK in 8 of 10 applicable services
- **Affected Services**: adservice, cartservice, checkoutservice, currencyservice, emailservice, frontend, paymentservice, shippingservice
- **Common Finding**: Limited queryable state. Cart has GetCart. Product catalog has ListProducts. But order status, payment status, and shipping status are not queryable after creation.
- **Compensating Controls**: Some services have read RPCs.
- **Portfolio-Level Recommendation**: For the customer support agent, add order status query endpoint to checkoutservice and shipping tracking endpoint to shippingservice.
- **Estimated Effort**: Medium

### STATE-Q3: Concurrency Controls

- **Severity**: RISK in 8 of 10 applicable services
- **Affected Services**: adservice, cartservice, checkoutservice, currencyservice, emailservice, frontend, paymentservice, shippingservice
- **Common Finding**: No optimistic concurrency controls. No ETags, version numbers, or conflict detection on state mutations.
- **Compensating Controls**: Read-only agent scope reduces concurrency risk.
- **Portfolio-Level Recommendation**: Implement optimistic concurrency (ETags or version fields) on cart operations and order state. Critical if agent scope is elevated to write-enabled.
- **Estimated Effort**: Medium

### STATE-Q6: Blast Radius and Transaction Limits

- **Severity**: RISK in 9 of 10 applicable services
- **Affected Services**: adservice, cartservice, checkoutservice, currencyservice, emailservice, frontend, paymentservice, productcatalogservice, shippingservice
- **Common Finding**: No transaction limits or blast radius controls. An agent could theoretically trigger unlimited operations.
- **Compensating Controls**: Read-only scope limits blast radius.
- **Portfolio-Level Recommendation**: Implement transaction limits per agent session/identity. For customer support agent: limit concurrent cart reads, rate-limit product queries.
- **Estimated Effort**: Low

### HITL-Q1: Draft/Pending State

- **Severity**: RISK in 8 of 10 applicable services
- **Affected Services**: adservice, cartservice, checkoutservice, currencyservice, emailservice, frontend, paymentservice, shippingservice
- **Common Finding**: No draft/pending state for agent actions. All operations are immediate with no review stage.
- **Compensating Controls**: Read-only scope means agents cannot make state changes.
- **Portfolio-Level Recommendation**: If agent scope is elevated to write-enabled, implement draft/pending states for checkout and cart modification operations.
- **Estimated Effort**: High

### HITL-Q2: Configurable Approval Gates

- **Severity**: RISK in 8 of 10 applicable services
- **Affected Services**: adservice, cartservice, checkoutservice, currencyservice, emailservice, frontend, paymentservice, shippingservice
- **Common Finding**: No approval gates. No human-in-the-loop workflow for sensitive operations.
- **Compensating Controls**: Read-only scope.
- **Portfolio-Level Recommendation**: Implement approval gates for write operations (order placement, cart modification) when agent scope is elevated.
- **Estimated Effort**: High

### HITL-Q3: Sandbox/Staging Environment

- **Severity**: RISK in 9 of 10 applicable services
- **Affected Services**: adservice, cartservice, checkoutservice, currencyservice, emailservice, frontend, paymentservice, productcatalogservice, shippingservice
- **Common Finding**: No dedicated sandbox or staging environment for agent testing. Skaffold profiles exist for different deployment targets but no isolated agent testing environment.
- **Compensating Controls**: Kustomize overlays can create separate environments.
- **Portfolio-Level Recommendation**: Create a dedicated agent testing environment using Kustomize overlays. Configure it with synthetic data and agent-specific monitoring.
- **Estimated Effort**: Low

### DATA-Q4: System of Record Designations

- **Severity**: RISK in 9 of 10 applicable services
- **Affected Services**: adservice, cartservice, checkoutservice, currencyservice, emailservice, frontend, paymentservice, productcatalogservice, shippingservice
- **Common Finding**: No system of record designations. Unclear which service is authoritative for each data entity.
- **Compensating Controls**: Microservice architecture implies ownership, but it's not documented.
- **Portfolio-Level Recommendation**: Document data ownership: cartservice owns cart data, productcatalogservice owns product data, etc. This helps agents understand which service to query for authoritative data.
- **Estimated Effort**: Low

### DATA-Q7: PII Redaction in Logs

- **Severity**: RISK in 8 of 10 applicable services
- **Affected Services**: adservice, cartservice, checkoutservice, currencyservice, emailservice, frontend, paymentservice, shippingservice
- **Common Finding**: PII appears in logs without redaction. Some services log full request/response including sensitive fields.
- **Compensating Controls**: None.
- **Portfolio-Level Recommendation**: Implement log redaction for PII fields (email, address, credit card). Configure at the OpenTelemetry collector level for portfolio-wide enforcement.
- **Estimated Effort**: Medium

## Service Dependency Map

> No dependency information was provided in the portfolio configuration. To enable
> dependency-aware analysis — including identification of high-risk foundation services,
> transitive blocker propagation, and shared infrastructure impacts — add
> `dependency_overrides` to the portfolio config.

### Observed Architecture Patterns

While explicit `dependency_overrides` were not provided, the individual ARA reports and service descriptions reveal a microservices architecture with the following patterns:

- **checkoutservice** is an orchestrator that calls cartservice, productcatalogservice, shippingservice, currencyservice, paymentservice, and emailservice — making it the highest fan-out service
- **frontend** calls all backend services via gRPC — it is the user-facing (and agent-facing) entry point
- **recommendationservice** depends on productcatalogservice for product data
- **cartservice** depends on Redis for state persistence

These patterns suggest that **checkoutservice** and **frontend** are high-risk nodes: if their blockers are not resolved, agent integration across the entire portfolio is effectively blocked. Conversely, **productcatalogservice** and **currencyservice** are potential foundation services — many other services depend on them.

**Recommendation**: Add explicit `dependency_overrides` to the portfolio configuration to enable:
- Fan-in/fan-out calculations
- Foundation service and leaf service identification
- Transitive blocker propagation analysis (PORT-ARA-Q4)
- Shared infrastructure impact assessment

Example configuration:
```yaml
dependency_overrides:
  - source: "frontend"
    target: "cartservice"
    type: "sync"
    description: "gRPC call to manage shopping cart"
  - source: "frontend"
    target: "productcatalogservice"
    type: "sync"
    description: "gRPC call to list/get products"
  - source: "frontend"
    target: "recommendationservice"
    type: "sync"
    description: "gRPC call to get product recommendations"
  - source: "frontend"
    target: "checkoutservice"
    type: "sync"
    description: "gRPC call to place orders"
  - source: "frontend"
    target: "currencyservice"
    type: "sync"
    description: "gRPC call to convert currencies"
  - source: "frontend"
    target: "shippingservice"
    type: "sync"
    description: "gRPC call to get shipping quotes"
  - source: "frontend"
    target: "adservice"
    type: "sync"
    description: "gRPC call to get contextual ads"
  - source: "checkoutservice"
    target: "cartservice"
    type: "sync"
    description: "Get and empty cart during checkout"
  - source: "checkoutservice"
    target: "productcatalogservice"
    type: "sync"
    description: "Get product details for order"
  - source: "checkoutservice"
    target: "currencyservice"
    type: "sync"
    description: "Convert currency for order total"
  - source: "checkoutservice"
    target: "shippingservice"
    type: "sync"
    description: "Get shipping cost for order"
  - source: "checkoutservice"
    target: "paymentservice"
    type: "sync"
    description: "Process payment for order"
  - source: "checkoutservice"
    target: "emailservice"
    type: "async"
    description: "Send order confirmation email"
  - source: "recommendationservice"
    target: "productcatalogservice"
    type: "sync"
    description: "List products for recommendation algorithm"
  - source: "cartservice"
    target: "redis-cart"
    type: "sync"
    description: "Cart state persistence"
```

## Portfolio Remediation Guidance

> Portfolio context: Cloud-native e-commerce platform with 11 microservices. Evaluating for autonomous AI agent integration (customer support agent for order tracking, product recommendations, and cart management) and modernization maturity.

### Remediation Priority Order

Remediation of cross-cutting BLOCKERs should follow this general priority:

1. **Identity and Access** — Resolve AUTH-section BLOCKERs first. You cannot enforce any other security control without machine identity and scoped permissions.
2. **Data Integrity** — Resolve STATE and DATA-section BLOCKERs second. Protect data before enabling agent write operations.
3. **API Surface** — Resolve API-section BLOCKERs third. Ensure a stable, documented integration surface for agent tools.
4. **Remaining BLOCKERs** — Address in order of affected service count (most affected first).

### Coordinated Remediation Plan

#### Group 1: Identity Foundation + Network Security

**BLOCKERs addressed**: AUTH-Q1, ENG-Q6
**Services affected**: 10 application services + platform-infra (all 11)

These two BLOCKERs should be resolved together because authentication without network security (and vice versa) provides incomplete protection.

- **What to do**:
  1. **Enable Istio mTLS** — Deploy PeerAuthentication in STRICT mode for the namespace. This provides mutual TLS between all services without application code changes. Each service already has a Kubernetes ServiceAccount defined.
  2. **Enable Network Policies** — Uncomment `components/network-policies` in `kustomize/kustomization.yaml` OR set `networkPolicies.create: true` in `helm-chart/values.yaml`. The deny-all baseline and 13 per-service policies are already defined.
  3. **Enable AuthorizationPolicies** — Set `authorizationPolicies.create: true` in Helm values. Per-service AuthorizationPolicy templates are already defined in the Helm chart.
  4. **Configure TLS on Istio Gateway** — Replace HTTP port 80 with HTTPS port 443 in `istio-manifests/frontend-gateway.yaml`. Add TLS certificate (cert-manager or manual).
  5. **Create agent-specific ServiceAccounts** — For the customer support agent, create dedicated Kubernetes ServiceAccounts (`customer-support-agent-reader`, etc.) and add them to AuthorizationPolicies for the services the agent needs to access (frontend, cartservice, productcatalogservice, recommendationservice).

- **Expected outcome**: All inter-service communication is authenticated via mTLS. Network policies restrict which services can communicate. The Istio Gateway is TLS-encrypted. Agent identities are distinguishable from service identities. This resolves AUTH-Q1 for all 10 application services and ENG-Q6 for all 10 services + platform-infra.

- **Impact on readiness profiles**: Resolving AUTH-Q1 + ENG-Q6 removes 2 BLOCKERs from:
  - 7 services currently "Not Agent-Integrable" (3 BLOCKERs) → drops to 1 BLOCKER (DATA-Q1) → moves to "Remediation Required"
  - currencyservice (2 BLOCKERs: AUTH-Q1 + ENG-Q6) → drops to 0 BLOCKERs → moves to "Pilot-Ready" or better
  - productcatalogservice (2 BLOCKERs: AUTH-Q1 + ENG-Q6) → drops to 0 BLOCKERs → moves to "Pilot-Ready" or better
  - recommendationservice (2 BLOCKERs: AUTH-Q1 + DATA-Q1) → drops to 1 BLOCKER (DATA-Q1) → stays "Remediation Required"
  - platform-infra (1 BLOCKER: ENG-Q6) → drops to 0 BLOCKERs → moves to "Pilot-Ready" or better

- **Effort**: Medium (2–4 weeks — the infrastructure is already built, it needs enablement and testing)

#### Group 2: Data Protection

**BLOCKERs addressed**: DATA-Q1
**Services affected**: adservice, cartservice, checkoutservice, emailservice, frontend, paymentservice, recommendationservice, shippingservice (8 services)

- **What to do**:
  1. **Define portfolio-wide data classification policy** — Create 4 tiers: Public, Internal, Confidential (PII), Restricted (PCI). Document which fields in `demo.proto` belong to which tier.
  2. **Annotate shared proto** — Add field-level sensitivity annotations to `demo.proto` (custom proto options or comments). Key classifications:
     - **Restricted (PCI)**: `CreditCardInfo.credit_card_number`, `CreditCardInfo.credit_card_cvv`
     - **Confidential (PII)**: `Address.street_address`, `Address.city`, `Address.state`, `Address.country`, `Address.zip_code`, `OrderResult.shipping_tracking_id`, `SendOrderConfirmationRequest.email`
     - **Internal**: `userId`, `orderId`, `productId`
     - **Public**: `Product.name`, `Product.description`, `Product.price_usd`, `Money.currency_code`
  3. **Define agent data access policy** — For the customer support agent (read-only): allow access to Public and Internal data. Require explicit authorization for Confidential (PII) data on a per-user-consent basis. Block all access to Restricted (PCI) data.
  4. **Implement runtime enforcement** — Add gRPC interceptors or field masks to enforce classification-based access control.

- **Expected outcome**: All data fields classified. Agent data access boundaries defined. PCI data protected from agent access. This resolves DATA-Q1 for all 8 affected services.

- **Impact on readiness profiles**: Resolving DATA-Q1 (after Group 1) removes the last BLOCKER from:
  - adservice, cartservice, checkoutservice, emailservice, frontend, paymentservice, shippingservice → 0 BLOCKERs → move to "Pilot-Ready" or better
  - recommendationservice → 0 BLOCKERs → moves to "Pilot-Ready" or better

- **Effort**: High (4–8 weeks for classification policy; additional 8–12 weeks for runtime enforcement)

### Post-Remediation Portfolio Projection

After resolving all 3 cross-cutting BLOCKERs:

| Profile | Current | Post-Group 1 | Post-Group 2 |
|---------|---------|-------------|-------------|
| Agent-Ready | 0 | 0 | 0* |
| Pilot-Ready | 0 | 3 (currencyservice, productcatalogservice, platform-infra) | Up to 11** |
| Remediation Required | 4 | 8 | 0 |
| Not Agent-Integrable | 7 | 0 | 0 |

\* *Whether services achieve Agent-Ready vs. Pilot-Ready depends on how many of the 24-36 RISKs per service are resolved alongside the BLOCKERs.*
\** *All 11 services would have 0 BLOCKERs. Actual profile depends on RISK count — most services have 30+ RISKs, which exceeds the Pilot-Ready threshold of 3-5 RISKs. Services would need further RISK remediation to reach Agent-Ready.*

## Agentic Program Recommendations

> These are engagement-level recommendations based on the portfolio's agentic readiness
> profile. Discuss with your AWS Solutions Architect to determine eligibility and timing.

> No specific agentic program recommendations based on current findings. Zero services
> are currently Agent-Ready or Pilot-Ready — the minimum trigger condition for
> EBA-Agentic AI is at least 1 service with Agent-Ready or Pilot-Ready profile.

| Program | Trigger Condition | Current Status | Triggered? |
|---------|-------------------|----------------|------------|
| EBA-Agentic AI | ≥1 service Agent-Ready or Pilot-Ready | 0 services (0%) | ❌ No |

### Path to Program Eligibility

After resolving **Group 1** (AUTH-Q1 + ENG-Q6) in the remediation plan:

- **currencyservice** drops from 2 BLOCKERs to 0 → potential Pilot-Ready
- **productcatalogservice** drops from 2 BLOCKERs to 0 → potential Pilot-Ready
- **platform-infra** drops from 1 BLOCKER to 0 → potential Pilot-Ready

This would trigger the **EBA-Agentic AI** program (3 services at Pilot-Ready or better).

**Recommended timing**: Re-assess portfolio readiness after completing Group 1 remediation. If 1+ services achieve Pilot-Ready, request EBA-Agentic AI engagement via your AWS Solutions Architect to accelerate agent integration for the customer support use case targeting currencyservice and productcatalogservice as initial pilot services.

### Program Details

#### EBA-Agentic AI (Experience-Based Acceleration for Agentic AI)

The EBA-Agentic AI program is not yet recommended because no services have achieved Pilot-Ready or Agent-Ready status. However, the portfolio's path to eligibility is clear: resolving the identity foundation (AUTH-Q1) and network security (ENG-Q6) BLOCKERs — which can be achieved through enabling existing Istio and Kustomize security infrastructure — would move 3 services to Pilot-Ready status within an estimated 2–4 weeks. At that point, the EBA-Agentic AI program would provide guided acceleration for integrating the customer support agent with the Online Boutique platform, focusing on the product catalog and currency conversion services as initial pilot targets.

## Portfolio-Level Findings

> These questions evaluate capabilities that can only be assessed by looking across
> multiple repos. They are distinct from cross-cutting analysis (which aggregates
> individual findings). Individual report findings are never overridden.

### PORT-ARA-Q1: Centralized Identity Plane

- **Severity**: BLOCKER
- **Finding**: No shared identity provider exists across the portfolio. There is no Cognito User Pool, Cognito Identity Pool, Okta configuration, or shared auth middleware referenced in any repo. The Helm chart defines Istio AuthorizationPolicies that reference Kubernetes ServiceAccount principals (`cluster.local/ns/{namespace}/sa/{service}`), but these are disabled by default (`authorizationPolicies.create: false`). Kubernetes ServiceAccounts exist per-service but are not configured for cross-service authentication — they are used only for pod-level RBAC. No IAM Roles for Service Accounts (IRSA) or GKE Workload Identity bindings exist for application services (only for the GKE cluster service account in `terraform/main.tf`).
- **Evidence**: `helm-chart/values.yaml` (`authorizationPolicies.create: false`, `sidecars.create: false`), `istio-manifests/frontend-gateway.yaml` (no auth config), `terraform/main.tf` (GKE cluster SA but no per-service identity), `kubernetes-manifests/*.yaml` (ServiceAccounts defined but with no IAM annotations). No Cognito, Okta, or auth middleware found in any service repo.
- **Recommendation**: Deploy Istio PeerAuthentication in STRICT mode as the portfolio-wide identity plane. This leverages existing Kubernetes ServiceAccounts (already defined per-service) with Istio-managed mTLS certificates. For agent-specific identity, create dedicated ServiceAccounts and add them to AuthorizationPolicies. For external agent callers (outside the mesh), deploy an API Gateway with OAuth2/JWT authentication at the Istio ingress gateway.
- **Affected Services**: All 11 services
- **Contextual Annotations**:
  > **Portfolio Context**: PORT-ARA-Q1 found no shared identity provider across the portfolio. Istio mTLS with Kubernetes ServiceAccounts (disabled but defined in Helm chart) is the most viable identity plane for this architecture. This provides context for AUTH-Q1 — **verify** that enabling Istio PeerAuthentication STRICT mode with existing ServiceAccounts provides sufficient identity attribution for agent audit requirements.

### PORT-ARA-Q2: Cross-Service Audit Correlation

- **Severity**: RISK
- **Finding**: OpenTelemetry integration exists across multiple services (Go services use `otelgrpc.NewServerHandler()`, Python services import `opentelemetry` packages, Java services have OTel agent). A centralized OpenTelemetry Collector is defined in the Helm chart (`helm-chart/templates/opentelemetry-collector.yaml`) that aggregates traces from all services and exports to Google Cloud Trace. However, the collector is disabled by default (`opentelemetryCollector.create: false`). When enabled, it provides trace correlation across services via OTLP protocol on port 4317. Google Cloud Operations APIs are enabled in Terraform (`cloudtrace.googleapis.com`). Despite trace infrastructure, **audit-grade log correlation is absent**: no immutable audit trail, no principal attribution in trace spans, and no centralized audit log aggregation with retention policies.
- **Evidence**: `helm-chart/values.yaml` (`opentelemetryCollector.create: false`, `googleCloudOperations.tracing: false`), `helm-chart/templates/opentelemetry-collector.yaml` (full OTel collector with ConfigMap), `terraform/main.tf` (`cloudtrace.googleapis.com` enabled). Individual service reports confirm OpenTelemetry SDK integration in most services.
- **Recommendation**: Enable OpenTelemetry Collector (`opentelemetryCollector.create: true`). Enable Google Cloud Operations tracing (`googleCloudOperations.tracing: true`). Add principal identity fields to trace spans after AUTH-Q1 is resolved. Implement a centralized audit log sink with immutable retention.
- **Affected Services**: All 11 services
- **Contextual Annotations**:
  > **Portfolio Context**: PORT-ARA-Q2 found OpenTelemetry infrastructure defined but disabled. Once enabled, it provides trace correlation across all services via a centralized collector. This provides context for AUTH-Q7 (Immutable Audit Logging) — **verify** that enabling the OTel collector with principal attribution in trace spans satisfies audit logging requirements.

### PORT-ARA-Q3: Portfolio-Level Rate Limiting

- **Severity**: RISK
- **Finding**: No portfolio-level rate limiting. The Istio Gateway (`istio-manifests/frontend-gateway.yaml`) accepts traffic on HTTP port 80 with wildcard hosts (`"*"`) and no rate limiting configuration. No WAF, no API Gateway usage plans, no EnvoyFilter rate limit rules. Individual services have no rate limiting either (STATE-Q5 is RISK in all 10 application services). The Helm chart does not include rate limiting configuration options. The only traffic control mechanism is the network policies (disabled by default) which restrict source/destination but not request rates.
- **Evidence**: `istio-manifests/frontend-gateway.yaml` (HTTP, wildcard hosts, no rate limiting), `helm-chart/values.yaml` (no rate limiting configuration), `kustomize/kustomization.yaml` (network-policies commented out). No WAF, API Gateway, or rate limiting middleware found in any repo.
- **Recommendation**: Implement portfolio-level rate limiting at the Istio ingress gateway using EnvoyFilter or Istio Wasm plugins. Set per-identity rate limits: higher limits for the customer support agent during normal operations, with circuit breaker thresholds for abnormal request patterns. Consider adding a shared WAF (AWS WAF or Google Cloud Armor) for the portfolio perimeter.
- **Affected Services**: All 11 services (any service accessible through the Istio Gateway)
- **Contextual Annotations**: None — this is a new finding not covered by individual service assessments.

### PORT-ARA-Q4: Transitive Dependency Safety

- **Severity**: RISK
- **Finding**: Limited analysis due to missing `dependency_overrides`. Based on observed architecture patterns (from individual ARA reports): checkoutservice depends synchronously on 6 other services. All 11 services are currently either "Not Agent-Integrable" (7) or "Remediation Required" (4) — **no service is currently Agent-Ready or Pilot-Ready**, so the BLOCKER condition (Agent-Ready service depending on Not Agent-Integrable service) is not met. However, after Group 1 remediation, currencyservice and productcatalogservice may achieve Pilot-Ready status. At that point, transitive dependency analysis becomes critical: if these services are consumed by checkoutservice (which will still be "Remediation Required" due to DATA-Q1), the dependency chain is safe because the blocker is on the caller, not the callee.
- **Evidence**: Individual ARA reports describe service dependencies. checkoutservice context: "Go gRPC service orchestrating the checkout workflow — calls cart, product, shipping, currency, payment, and email services." No explicit `dependency_overrides` provided.
- **Recommendation**: Provide `dependency_overrides` in the portfolio configuration to enable full transitive dependency analysis. After Group 1 remediation, re-run the portfolio assessment to evaluate transitive safety with accurate dependency data and updated readiness profiles.
- **Affected Services**: Primarily checkoutservice (highest fan-out), frontend (user/agent entry point)
- **Contextual Annotations**: None — requires dependency data for detailed annotations.

### PORT-ARA-Q5: Agent Identity Governance

- **Severity**: RISK
- **Finding**: No centralized mechanism to manage, suspend, or revoke agent identities across the portfolio. There is no agent identity registry, no centralized API key management, and no portfolio-level revocation mechanism. Kubernetes RBAC provides some capability (deleting a ServiceAccount suspends its pods), but this is not designed for agent identity governance and requires kubectl access. The Helm chart's AuthorizationPolicies (when enabled) provide per-service access control but no centralized kill switch. If an agent's credentials are compromised, there is no single action to revoke access across all 11 services simultaneously.
- **Evidence**: `helm-chart/values.yaml` (ServiceAccounts created per-service but no agent-specific accounts), `kubernetes-manifests/*.yaml` (per-service ServiceAccounts with no centralized management). No Cognito app client registry, no API key management system, no agent identity documentation.
- **Recommendation**: After resolving AUTH-Q1, establish a centralized agent identity registry. Options: (1) Dedicated Kubernetes namespace for agent ServiceAccounts with RBAC policies, (2) Cognito User Pool with app clients for agent identities, (3) API Gateway with centralized API key management. Implement a "kill switch" — a single AuthorizationPolicy or Kubernetes RBAC change that revokes all agent access portfolio-wide.
- **Affected Services**: All 11 services
- **Contextual Annotations**:
  > **Portfolio Context**: PORT-ARA-Q5 found no centralized agent identity governance mechanism. This provides context for AUTH-Q8 (Agent Identity Suspension) — **verify** that the identity governance solution chosen for PORT-ARA-Q5 provides individual service-level suspension in addition to portfolio-wide revocation.

## Service-by-Service Summary

| Service | Repo Type | Agent Scope | Readiness Profile | BLOCKERs | RISKs | INFOs | N/A |
|---------|-----------|-------------|-------------------|----------|-------|-------|-----|
| cartservice | application | read-only | ❌ Not Agent-Integrable | 3 | 35 | 11 | 0 |
| checkoutservice | application | read-only | ❌ Not Agent-Integrable | 3 | 35 | 11 | 0 |
| frontend | application | read-only | ❌ Not Agent-Integrable | 3 | 35 | 11 | 0 |
| paymentservice | application | read-only | ❌ Not Agent-Integrable | 3 | 35 | 11 | 0 |
| adservice | application | read-only | ❌ Not Agent-Integrable | 3 | 35 | 11 | 0 |
| emailservice | application | read-only | ❌ Not Agent-Integrable | 3 | 36 | 10 | 0 |
| shippingservice | application | read-only | ❌ Not Agent-Integrable | 3 | 35 | 11 | 0 |
| productcatalogservice | application | read-only | 🟠 Remediation Required | 2 | 30 | 17 | 0 |
| currencyservice | application | read-only | 🟠 Remediation Required | 2 | 34 | 13 | 0 |
| recommendationservice | application | read-only | 🟠 Remediation Required | 2 | 24 | 23 | 0 |
| platform-infra | infrastructure-only | read-only | 🟠 Remediation Required | 1 | 12 | 2 | 34 |

### Individual Service Details

#### cartservice

- **Readiness Profile**: ❌ Not Agent-Integrable
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P0
- **BLOCKERs** (3):
  - AUTH-Q1: No machine identity authentication — gRPC service has no `AddAuthentication()` or `UseAuthorization()` middleware
  - DATA-Q1: Sensitive data unclassified — `userId` (PII), cart items stored in Redis with no classification or access controls
  - ENG-Q6: No network policies — `AllowedHosts: "*"`, port 7070 exposed with no security groups or firewall rules
- **RISKs** (35): AUTH-Q2 through AUTH-Q8, API-Q2/Q3/Q5/Q7, STATE-Q1 through STATE-Q7, HITL-Q1 through HITL-Q3, DATA-Q2 through DATA-Q8, DISC-Q1, OBS-Q1/Q2, ENG-Q1 through ENG-Q5
- **Key Recommendations**:
  - Enable Istio mTLS for service mesh-level authentication
  - Classify `userId` as PII and implement field-level access controls
  - Enable network policies via Kustomize or Helm

#### checkoutservice

- **Readiness Profile**: ❌ Not Agent-Integrable
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P0
- **BLOCKERs** (3):
  - AUTH-Q1: No authentication — gRPC server with `grpc.NewServer()` and `insecure.NewCredentials()` for all downstream calls
  - DATA-Q1: Unclassified PCI-DSS data — CreditCardInfo (card number, CVV) flows through without classification
  - ENG-Q6: No network policies — gRPC on 0.0.0.0:5050 with insecure credentials
- **RISKs** (35): Full set of AUTH, API, STATE, HITL, DATA, DISC, OBS, and ENG RISKs
- **Key Recommendations**:
  - Highest priority for data classification due to PCI-DSS scope
  - Implement saga pattern for checkout workflow compensation
  - Enable mTLS and network policies

#### frontend

- **Readiness Profile**: ❌ Not Agent-Integrable
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P0
- **BLOCKERs** (3):
  - AUTH-Q1: Zero authentication — session identity is random UUID in unsigned cookie, `insecure.NewCredentials()` for all backend gRPC calls
  - DATA-Q1: PCI-relevant data (credit card) flows through `placeOrderHandler` without classification
  - ENG-Q6: Network policies disabled — frontend exposed to internet with no WAF, CORS, or restrictions
- **RISKs** (35): Full set across all sections
- **Key Recommendations**:
  - Primary agent entry point — implement API key or OAuth2 on agent-facing endpoints (`/product-meta/{ids}`, `/bot`)
  - Enable TLS on Istio Gateway
  - Add CORS configuration for agent callers

#### paymentservice

- **Readiness Profile**: ❌ Not Agent-Integrable
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P0
- **BLOCKERs** (3):
  - AUTH-Q1: No authentication — `grpc.ServerCredentials.createInsecure()` in Node.js
  - DATA-Q1: PCI-DSS data (`credit_card_number`, `credit_card_cvv`) processed and logged with zero classification
  - ENG-Q6: No TLS, no network policies, service open to any network-reachable client
- **RISKs** (35): Full set
- **Key Recommendations**:
  - Critical PCI-DSS scope — data classification is highest priority after identity
  - Agent should never have direct access to payment data (even read-only)
  - Implement field-level access controls blocking PCI data from agent callers

#### adservice

- **Readiness Profile**: ❌ Not Agent-Integrable
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (3):
  - AUTH-Q1: No authentication — Java `ServerBuilder.forPort(port)` with no interceptor
  - DATA-Q1: Ad data unclassified — redirect URLs and text without classification framework
  - ENG-Q6: No network security — port 9555 exposed without encryption
- **RISKs** (35): Full set
- **Key Recommendations**:
  - Lower sensitivity service — good candidate for early agent pilot after blocker remediation
  - Enable mTLS and network policies
  - Consider adding gRPC reflection for agent API discovery

#### emailservice

- **Readiness Profile**: ❌ Not Agent-Integrable
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (3):
  - AUTH-Q1: No authentication — Python `server.add_insecure_port()` with no interceptors
  - DATA-Q1: PII (email addresses, shipping addresses) processed without classification
  - ENG-Q6: gRPC on insecure port with no network security
- **RISKs** (36): Full set (highest RISK count — 36)
- **Key Recommendations**:
  - Classify email address and shipping address as Confidential (PII)
  - Agent read-only scope means agent should not trigger email sends
  - Enable mTLS and network policies

#### shippingservice

- **Readiness Profile**: ❌ Not Agent-Integrable
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P1
- **BLOCKERs** (3):
  - AUTH-Q1: No authentication — Go `grpc.NewServer()` with no interceptors
  - DATA-Q1: PII (address fields) processed without classification
  - ENG-Q6: Port 50051 with no TLS, no network restrictions
- **RISKs** (35): Full set
- **Key Recommendations**:
  - Agent use case: shipping quote queries and tracking — good candidate for agent tool
  - Classify address data as Confidential (PII)
  - Enable mTLS and network policies

#### productcatalogservice

- **Readiness Profile**: 🟠 Remediation Required
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P0
- **BLOCKERs** (2):
  - AUTH-Q1: No authentication — `grpc.NewServer()` with `insecure.NewCredentials()`
  - ENG-Q6: Network policies exist in Kustomize but disabled by default; no TLS on gRPC
- **RISKs** (30): 30 RISKs (lower than most — many questions scored INFO due to non-sensitive public data)
- **Key Recommendations**:
  - **Best candidate for early agent pilot** — only 2 BLOCKERs (no DATA-Q1 because data is non-sensitive public product info)
  - Resolving AUTH-Q1 + ENG-Q6 (Group 1) moves this to Pilot-Ready
  - Agent use case: product catalog queries for customer support recommendations

#### currencyservice

- **Readiness Profile**: 🟠 Remediation Required
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P1
- **BLOCKERs** (2):
  - AUTH-Q1: No authentication — Node.js `grpc.ServerCredentials.createInsecure()`
  - ENG-Q6: No network security configuration
- **RISKs** (34): Full set minus DATA-Q1 (public ECB rates — no sensitive data)
- **Key Recommendations**:
  - **Strong pilot candidate** — only 2 BLOCKERs, handles only public currency data
  - Resolving AUTH-Q1 + ENG-Q6 (Group 1) moves this to Pilot-Ready
  - Agent use case: currency conversion for international customer support

#### recommendationservice

- **Readiness Profile**: 🟠 Remediation Required
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P1
- **BLOCKERs** (2):
  - AUTH-Q1: No authentication — Python `grpc.insecure_channel()` and `server.add_insecure_port()`
  - DATA-Q1: `user_id` field unclassified PII
- **RISKs** (24): Lowest RISK count among application services (23 INFOs — many questions scored INFO)
- **Key Recommendations**:
  - Strongest readiness profile among services with DATA-Q1 BLOCKER (only 24 RISKs)
  - Has existing Istio AuthorizationPolicy and NetworkPolicy — only service with ENG-Q6 as INFO
  - Agent use case: product recommendations for customer support — primary pilot target
  - Classify `user_id` as PII and implement access control

#### platform-infra

- **Readiness Profile**: 🟠 Remediation Required
- **Repo Type**: infrastructure-only
- **Agent Scope**: read-only
- **Priority**: Not set
- **BLOCKERs** (1):
  - ENG-Q6: Network policies comprehensively defined but disabled by default; Istio Gateway permissive (HTTP, wildcard, no TLS)
- **RISKs** (12): AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7, AUTH-Q8, OBS-Q1, OBS-Q2, ENG-Q1 through ENG-Q5
- **N/A** (34): 34 questions not applicable to infrastructure-only repo
- **Key Recommendations**:
  - Enable network policies (uncomment `components/network-policies` in kustomization.yaml)
  - Enable AuthorizationPolicies and Sidecars in Helm values
  - Configure TLS on Istio Gateway
  - This single infrastructure change resolves ENG-Q6 for platform-infra and contributes to resolving it for all application services

## Assessment Inventory

| # | Service | Report File | Assessment Date | Repo Type | Agent Scope |
|---|---------|-------------|-----------------|-----------|-------------|
| 1 | frontend | ./services/microservices-demo/src/frontend/frontend-ara-report.md | 2026-04-15 | application | read-only |
| 2 | cartservice | ./services/microservices-demo/src/cartservice/cartservice-ara-report.md | 2025-07-15 | application | read-only |
| 3 | productcatalogservice | ./services/microservices-demo/src/productcatalogservice/productcatalogservice-ara-report.md | 2026-04-15 | application | read-only |
| 4 | checkoutservice | ./services/microservices-demo/src/checkoutservice/checkoutservice-ara-report.md | 2026-04-15 | application | read-only |
| 5 | paymentservice | ./services/microservices-demo/src/paymentservice/paymentservice-ara-report.md | 2025-07-15 | application | read-only |
| 6 | currencyservice | ./services/microservices-demo/src/currencyservice/currencyservice-ara-report.md | 2026-04-15 | application | read-only |
| 7 | shippingservice | ./services/microservices-demo/src/shippingservice/shippingservice-ara-report.md | 2026-04-15 | application | read-only |
| 8 | emailservice | ./services/microservices-demo/src/emailservice/emailservice-ara-report.md | 2026-04-15 | application | read-only |
| 9 | recommendationservice | ./services/microservices-demo/src/recommendationservice/recommendationservice-ara-report.md | 2026-04-15 | application | read-only |
| 10 | adservice | ./services/microservices-demo/src/adservice/adservice-ara-report.md | 2026-04-15 | application | read-only |
| 11 | platform-infra | ./services/microservices-demo/microservices-demo-ara-report.md | 2025-07-15 | infrastructure-only | read-only |

### Discovery Notes

- **Reports discovered**: 17 files matching `*-ara-report.md`
- **Reports included**: 11 (all under `./services/microservices-demo/`)
- **Reports excluded**: 6 (under `./example-reports/` — reference reports from other portfolios, not part of this assessment)
- **Excluded files**:
  - `./example-reports/v2-full-assessment/agentic-readiness-assessment/aws-microservices-ara-report.md`
  - `./example-reports/v2-full-assessment/agentic-readiness-assessment/books-api-ara-report.md`
  - `./example-reports/v2-full-assessment/agentic-readiness-assessment/ecommerce-platform-v2-portfolio-ara-report.md`
  - `./example-reports/v2-full-assessment/agentic-readiness-assessment/eks-saas-gitops-ara-report.md`
  - `./example-reports/v2-full-assessment/agentic-readiness-assessment/monolith-ara-report.md`
  - `./example-reports/v2-full-assessment/agentic-readiness-assessment/MonoToMicroLegacy-ara-report.md`
- **Service inventory cross-reference**: All 11 services from `service_inventory` in the portfolio configuration have matching ARA reports. No missing reports.
