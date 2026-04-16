# Portfolio Agentic Readiness Assessment Report

**Date**: 2026-04-16
**Services Assessed**: 11
**Portfolio Context**: Cloud-native e-commerce platform with 11 microservices. Evaluating for autonomous AI agent integration (customer support agent for order tracking, product recommendations, and cart management).

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
| Total Services Assessed | 11 |
| Services Ready for Agents (Agent-Ready + Pilot-Ready) | 0 (0%) |
| Services Requiring Remediation | 11 (100%) |
| Cross-Cutting BLOCKERs (same blocker in 2+ repos) | 2 |
| Cross-Cutting RISKs (same risk in 3+ repos) | 32 |
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
| AUTH | 11 | 100% | AUTH-Q1 |
| DATA | 7 | 70% | DATA-Q1 |
| API | 1 | 10% | API-Q1 |
| STATE | 0 | 0% | — |
| HITL | 0 | 0% | — |
| DISC | 0 | 0% | — |
| OBS | 0 | 0% | — |
| ENG | 0 | 0% | — |

### Readiness Snapshot

| Metric | Value |
|--------|-------|
| assessment_date | 2026-04-16 |
| total_services | 11 |
| agent_ready | 0 |
| pilot_ready | 0 |
| remediation_required | 10 |
| not_integrable | 1 |
| total_blockers | 19 |
| total_risks | 313 |
| total_infos | 192 |
| cross_cutting_blockers | 2 |
| cross_cutting_risks | 32 |
| portfolio_level_blockers | 1 |
| portfolio_level_risks | 4 |
| write_enabled_services | 0 |
| read_only_services | 11 |

## Cross-Cutting BLOCKERs — Same Blocker in 2+ Repos

> These are BLOCKER-severity questions that appear in 2 or more repositories.
> They represent portfolio-wide agentic readiness gaps requiring coordinated remediation.
> Questions scored as N/A for a service do not count as gaps for that service.

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER in 11 of 11 applicable services
- **Affected Services**: frontend, cartservice, productcatalogservice, checkoutservice, paymentservice, currencyservice, shippingservice, emailservice, recommendationservice, adservice, platform-infra
- **Common Finding**: Every service in the portfolio — all 10 application services and the infrastructure-only repo — lacks machine identity authentication. gRPC servers are created with insecure credentials (`grpc.NewServer()` in Go, `grpc.ServerCredentials.createInsecure()` in Node.js, `server.add_insecure_port` in Python, `ServerBuilder.forPort(port)` in Java, `MapGrpcService<T>()` with no auth middleware in C#). Kubernetes ServiceAccounts exist per service but provide pod-level identity only — no request-level authentication. The Istio service mesh has optional AuthorizationPolicies defined in Helm chart templates for each service, but these are **disabled by default** (`authorizationPolicies.create: false` in `helm-chart/values.yaml`). No OAuth2, API key, mTLS, Cognito, or API Gateway authorizers exist anywhere in the portfolio.
- **Root Cause Pattern**: The platform was designed for trusted in-cluster communication without external consumers. All services assume network-level trust (Kubernetes cluster boundary) rather than request-level identity verification. The Istio AuthorizationPolicy infrastructure exists but was never enabled.
- **Portfolio-Level Remediation**:
  - **Approach**: Hybrid — platform-level Istio enablement + per-service application-layer hardening
  - **Immediate Action**: Set `authorizationPolicies.create: true` in `helm-chart/values.yaml`. This single configuration change enables mTLS-based service identity authentication across all 11 services using existing Helm chart templates that already define per-service, per-operation authorization rules.
  - **Target State**: Every gRPC call between services is authenticated via mTLS with Kubernetes ServiceAccount principals. Agent-specific service accounts are created with scoped access. Authenticated principal is logged in audit trails for every request.
  - **Estimated Effort**: Low (Istio enablement: 1–2 weeks for platform change) + Medium (per-service application-layer auth: 2–4 weeks per service for defense-in-depth)
  - **Priority**: Critical — affects all 11 services. No other security control (permissions, audit logging, identity suspension) can be enforced without identity.
  - **Dependencies**: None — this is the foundation. All other AUTH-section remediations depend on this.

> **Portfolio Context**: PORT-ARA-Q1 found no shared identity provider across the portfolio. Kubernetes ServiceAccounts exist per service but are not integrated into a centralized identity plane for agent M2M authentication. Enabling Istio AuthorizationPolicies would establish a mesh-level identity plane — **verify** that mTLS is enforced (not permissive mode) and that agent-specific service accounts are created.

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER in 7 of 10 applicable services
- **Affected Services**: frontend, cartservice, checkoutservice, paymentservice, shippingservice, emailservice, recommendationservice
- **N/A**: platform-infra (infrastructure-only — N/A for this question)
- **Not Affected (INFO)**: productcatalogservice (catalog data is non-sensitive), currencyservice (exchange rates are public data), adservice (ad categories are non-sensitive)
- **Common Finding**: Services processing PII (email addresses, street addresses, phone numbers) and financial data (credit card numbers, CVV, expiration dates) have no data classification at any level. The `placeOrderHandler` in frontend and checkoutservice processes highly sensitive checkout data — `credit_card_number`, `credit_card_cvv`, `email`, `street_address` — with no classification tags, no field-level encryption, and no PII detection tools. The cartservice stores `userId` (potentially PII) in Redis without classification. The paymentservice handles credit card charge data. The emailservice processes email addresses and order confirmation details. No data classification policies exist anywhere in the portfolio.
- **Root Cause Pattern**: The platform was built as a demo/reference architecture without production data governance. No data classification taxonomy was established, and no field-level access controls were implemented. PII and financial data flow in plaintext over insecure gRPC connections.
- **Portfolio-Level Remediation**:
  - **Approach**: Hybrid — portfolio-level classification taxonomy + per-service field-level implementation
  - **Immediate Action**: Define a portfolio-wide data classification taxonomy with levels: `PUBLIC`, `INTERNAL`, `PII`, `PCI`, `SENSITIVE`. Classify the protobuf fields in `demo.proto` — specifically `CreditCardInfo` (PCI), `Address` (PII), `email` (PII), `userId` (PII-candidate). Document classifications in a shared data dictionary.
  - **Target State**: All PII and financial fields are classified, tagged in proto definitions, and protected by field-level access controls. Agent identities require explicit authorization to access classified fields. Credit card data is encrypted in transit (mTLS) and at rest (KMS).
  - **Estimated Effort**: Medium (classification taxonomy: 1–2 weeks) + High (field-level encryption and access controls: 4–8 weeks across 7 services)
  - **Priority**: High — affects 7 of 10 application services including all P0 services on the critical checkout path (frontend, cartservice, checkoutservice, paymentservice)
  - **Dependencies**: AUTH-Q1 must be resolved first — you need identity before you can enforce data access controls.

## Cross-Cutting RISKs — Same Risk in 3+ Repos

> These are RISK-severity questions that appear in 3 or more repositories.
> They represent portfolio-wide patterns warranting coordinated attention.
> Questions scored as N/A for a service do not count as gaps for that service.

### AUTH-Q2: Scoped Permissions (Least Privilege)

- **Severity**: RISK in 11 of 11 applicable services
- **Affected Services**: frontend, cartservice, productcatalogservice, checkoutservice, paymentservice, currencyservice, shippingservice, emailservice, recommendationservice, adservice, platform-infra
- **Common Finding**: No IAM policies or permission scoping for agent identities at any service. Once an identity has network access, it can call all RPCs without restriction. Istio AuthorizationPolicies define per-operation rules (when enabled) but are disabled by default.
- **Compensating Controls**: Enable Istio AuthorizationPolicies per service to restrict agents to specific RPC operations (e.g., `GetCart` only for read-only agents). Restrict agent tool definitions to read-only operations at the orchestration layer.
- **Portfolio-Level Recommendation**: After AUTH-Q1 is resolved, define agent-specific service accounts with per-operation Istio AuthorizationPolicy rules. Create a shared RBAC model across the portfolio.
- **Estimated Effort**: Medium

### AUTH-Q3: Action-Level Authorization

- **Severity**: RISK in 11 of 11 applicable services
- **Affected Services**: frontend, cartservice, productcatalogservice, checkoutservice, paymentservice, currencyservice, shippingservice, emailservice, recommendationservice, adservice, platform-infra
- **Common Finding**: No action-level authorization in any application code. No ABAC, no RBAC, no permission checks in middleware or gRPC interceptors. The Helm chart AuthorizationPolicies define per-operation paths when enabled but are infrastructure-level, not application-level.
- **Compensating Controls**: For read-only agent scope, restrict agent tool definitions to read operations. Enable Istio AuthorizationPolicy for mesh-level enforcement.
- **Portfolio-Level Recommendation**: Implement gRPC server interceptors across all services that validate operation-level permissions based on caller identity metadata. Adopt a shared authorization middleware pattern.
- **Estimated Effort**: Medium

### AUTH-Q4: Identity Propagation

- **Severity**: RISK in 10 of 10 applicable services
- **Affected Services**: frontend, cartservice, productcatalogservice, checkoutservice, paymentservice, currencyservice, shippingservice, emailservice, recommendationservice, adservice
- **Common Finding**: No JWT parsing, no OAuth2 token exchange, no identity propagation through the service chain. User identifiers (e.g., `userId` in cart and checkout) are plain strings passed without verification. No service can verify that a caller is authorized to act on behalf of a specific user.
- **Compensating Controls**: Restrict agent access to designated test user IDs. Enforce user ID allowlists at the orchestration layer.
- **Portfolio-Level Recommendation**: Implement JWT/OAuth2 token-based identity propagation through gRPC metadata. Standardize an `x-agent-identity` and `x-on-behalf-of` header pattern across all services.
- **Estimated Effort**: High

### AUTH-Q5: Agent-as-Self vs Agent-on-Behalf-of-User

- **Severity**: RISK in 10 of 10 applicable services
- **Affected Services**: frontend, cartservice, productcatalogservice, checkoutservice, paymentservice, currencyservice, shippingservice, emailservice, recommendationservice, adservice
- **Common Finding**: No distinction between service identity and delegated user identity in any application. All sessions are anonymous or use plain string identifiers. No dual authentication flows exist.
- **Compensating Controls**: Define separate API keys or client credentials for agent-as-self vs. agent-on-behalf-of-user at the API Gateway layer.
- **Portfolio-Level Recommendation**: Design a portfolio-wide agent identity model with distinct flows for autonomous agent actions vs. user-delegated actions.
- **Estimated Effort**: High

### AUTH-Q6: Credential Management

- **Severity**: RISK in 9 of 11 applicable services
- **Affected Services**: frontend, cartservice, productcatalogservice, checkoutservice, paymentservice, shippingservice, emailservice, recommendationservice, platform-infra
- **Common Finding**: gRPC connections use insecure credentials (`insecure.NewCredentials()` in Go, `grpc.ServerCredentials.createInsecure()` in Node.js, `grpc.insecure_channel()` in Python). Redis has no authentication. No secrets management system for credential rotation. AlloyDB connects as `postgres` superuser.
- **Compensating Controls**: Network policies restrict access when enabled. Service discovery addresses via environment variables is acceptable for in-cluster communication.
- **Portfolio-Level Recommendation**: Enable mTLS for all gRPC connections via Istio sidecar injection. Integrate with a secrets management system (GCP Secret Manager) for any new agent credentials. Enable Redis AUTH.
- **Estimated Effort**: Medium

### AUTH-Q7: Immutable Audit Logging

- **Severity**: RISK in 11 of 11 applicable services
- **Affected Services**: frontend, cartservice, productcatalogservice, checkoutservice, paymentservice, currencyservice, shippingservice, emailservice, recommendationservice, adservice, platform-infra
- **Common Finding**: No immutable audit logging exists across the portfolio. Frontend has structured JSON logging via logrus but without authenticated principal. Most services use `Console.WriteLine` (C#), `console.log` (Node.js), or basic `print`/`logging` (Python/Go) — unstructured, no immutable storage, no CloudTrail or equivalent. No tamper-evident log storage configured anywhere.
- **Compensating Controls**: Configure Kubernetes log forwarding to immutable storage (Cloud Logging with retention policy, or S3 with object lock). Enable Istio access logs for request-level audit trails.
- **Portfolio-Level Recommendation**: Implement a portfolio-wide structured logging standard (JSON format with `request_id`, `trace_id`, `authenticated_principal`, `timestamp`, `operation`, `user_id`). Configure GKE audit logging at the cluster level. Store logs in immutable destinations.
- **Estimated Effort**: Medium

### AUTH-Q8: Agent Identity Suspension

- **Severity**: RISK in 11 of 11 applicable services
- **Affected Services**: frontend, cartservice, productcatalogservice, checkoutservice, paymentservice, currencyservice, shippingservice, emailservice, recommendationservice, adservice, platform-infra
- **Common Finding**: No mechanism to suspend individual agent identities without broader platform impact. No API key revocation endpoints. Istio AuthorizationPolicy changes require Helm/Kubernetes deployment. No immediate kill switch for misbehaving agents.
- **Compensating Controls**: Network policies can block specific source pods. Agent orchestration layer can implement circuit breakers.
- **Portfolio-Level Recommendation**: Implement agent identity as distinct Kubernetes ServiceAccounts. Create a runbook for immediate suspension via `kubectl delete serviceaccount` or Istio AuthorizationPolicy update. Consider a centralized agent identity registry.
- **Estimated Effort**: Medium

### API-Q2: Machine-Readable API Specification

- **Severity**: RISK in 7 of 10 applicable services
- **Affected Services**: frontend, productcatalogservice, checkoutservice, paymentservice, shippingservice, emailservice, recommendationservice
- **Common Finding**: No OpenAPI, Swagger, or AsyncAPI specifications exist. gRPC services have proto files that serve as machine-readable specs, but the frontend's HTTP endpoints are undocumented. No schema registry for versioned consumption.
- **Compensating Controls**: Proto files provide machine-readable gRPC schemas. Agent tool definitions can be derived from proto files.
- **Portfolio-Level Recommendation**: Publish all proto files to a schema registry. Generate OpenAPI specs for any HTTP endpoints. Standardize on proto as the canonical API spec format.
- **Estimated Effort**: Low

### API-Q3: Structured Error Responses

- **Severity**: RISK in 10 of 10 applicable services
- **Affected Services**: frontend, cartservice, productcatalogservice, checkoutservice, paymentservice, currencyservice, shippingservice, emailservice, recommendationservice, adservice
- **Common Finding**: All services throw gRPC exceptions with generic status codes (`FailedPrecondition`, `Internal`) and string messages. No structured error codes, no retryable indicators, no error categorization distinguishing transient from permanent failures. Frontend returns HTML error pages even for JSON-expecting clients.
- **Compensating Controls**: Agent-side retry logic can treat 5xx/FailedPrecondition as retriable with exponential backoff.
- **Portfolio-Level Recommendation**: Define a portfolio-wide error response standard with structured error metadata in gRPC trailing metadata (`x-error-code`, `x-retryable`). Implement a shared gRPC interceptor pattern.
- **Estimated Effort**: Medium

### API-Q5: API Versioning and Deprecation

- **Severity**: RISK in 10 of 10 applicable services
- **Affected Services**: frontend, cartservice, productcatalogservice, checkoutservice, paymentservice, currencyservice, shippingservice, emailservice, recommendationservice, adservice
- **Common Finding**: No API versioning anywhere. Proto packages use `hipstershop` with no version qualifier. No deprecation policies, no changelogs. Breaking changes would silently break agent tool schemas.
- **Compensating Controls**: Pin agent tool definitions to specific proto schema versions. Add proto schema comparison to CI.
- **Portfolio-Level Recommendation**: Adopt proto package versioning (e.g., `hipstershop.cart.v1`). Implement `buf` for breaking change detection in CI across all services.
- **Estimated Effort**: Medium

### API-Q7: Asynchronous Operation Support

- **Severity**: RISK in 7 of 10 applicable services
- **Affected Services**: frontend, cartservice, productcatalogservice, checkoutservice, shippingservice, emailservice, recommendationservice
- **Common Finding**: All operations are synchronous request-response. No async patterns for long-running tasks. The checkout flow blocks on sequential gRPC calls to 6 backend services.
- **Compensating Controls**: For read-only agent scope, most read operations are fast. Set generous timeouts on agent tool definitions.
- **Portfolio-Level Recommendation**: Implement async patterns for the checkout flow (job submission + status polling). Consider event-driven patterns for multi-service orchestration.
- **Estimated Effort**: High

### STATE-Q1: Compensation and Rollback

- **Severity**: RISK in 10 of 10 applicable services
- **Affected Services**: frontend, cartservice, productcatalogservice, checkoutservice, paymentservice, currencyservice, shippingservice, emailservice, recommendationservice, adservice
- **Common Finding**: No saga pattern, compensation logic, or undo endpoints in any service. Multi-step operations leave partial state on failure. Cart `AddItem` is cumulative with no rollback; `EmptyCart` is destructive with no undo.
- **Compensating Controls**: For read-only agent scope, agents don't execute write workflows, reducing compensation risk.
- **Portfolio-Level Recommendation**: Implement compensation endpoints for critical write paths before expanding to write-enabled scope.
- **Estimated Effort**: High

### STATE-Q2: Queryable Current State

- **Severity**: RISK in 7 of 10 applicable services
- **Affected Services**: frontend, cartservice, checkoutservice, paymentservice, shippingservice, emailservice, recommendationservice
- **Common Finding**: State is queryable per entity (e.g., `GetCart` by userId, `GetProduct` by ID) but most responses are limited. Frontend returns HTML for most endpoints. No cross-entity query capabilities. No administrative query interfaces.
- **Compensating Controls**: gRPC `Get*` operations provide per-entity state queries. Agents can query individual entities by known IDs.
- **Portfolio-Level Recommendation**: Add JSON-returning endpoints where HTML is currently returned. Add list/search capabilities with pagination.
- **Estimated Effort**: Medium

### STATE-Q4: Circuit Breakers and Resilience

- **Severity**: RISK in 8 of 10 applicable services
- **Affected Services**: frontend, cartservice, productcatalogservice, checkoutservice, paymentservice, shippingservice, emailservice, recommendationservice
- **Common Finding**: No circuit breakers in any application code. No retry policies with exponential backoff. No Polly, Resilience4j, or equivalent libraries. Exceptions from dependencies cause cascading failures.
- **Compensating Controls**: Istio sidecar (if enabled) provides mesh-level circuit breaking. Agent-side circuit breakers can detect sustained failures.
- **Portfolio-Level Recommendation**: Implement circuit breaker patterns in all services using language-appropriate libraries (Polly for C#, resilience patterns for Go). Alternatively, enable Istio DestinationRules with circuit breaking.
- **Estimated Effort**: Medium

### STATE-Q5: Rate Limiting and Throttling

- **Severity**: RISK in 10 of 10 applicable services
- **Affected Services**: frontend, cartservice, productcatalogservice, checkoutservice, paymentservice, currencyservice, shippingservice, emailservice, recommendationservice, adservice
- **Common Finding**: No rate limiting at any level — no application middleware, no API Gateway throttling, no WAF rules. Services are exposed as ClusterIP services with no request-rate throttling. The frontend LoadBalancer exposes port 80 directly to the internet.
- **Compensating Controls**: Kubernetes resource limits prevent single-pod resource exhaustion. Agent orchestration layer can enforce per-tool rate limits.
- **Portfolio-Level Recommendation**: Deploy an API Gateway (Istio ingress or GKE Gateway API) with rate limiting for agent traffic. Implement per-service rate limiting middleware as defense-in-depth.
- **Estimated Effort**: Medium

### STATE-Q7: Infrastructure Capacity for Agent Traffic

- **Severity**: RISK in 10 of 10 applicable services
- **Affected Services**: frontend, cartservice, productcatalogservice, checkoutservice, paymentservice, currencyservice, shippingservice, emailservice, recommendationservice, adservice
- **Common Finding**: No load testing results or capacity planning. Static resource limits with no Horizontal Pod Autoscaler (HPA). CI smoke tests validate ~50 requests only. Infrastructure sized for human-paced interaction.
- **Compensating Controls**: GKE Autopilot provides node-level auto-scaling. Start with conservative agent request limits.
- **Portfolio-Level Recommendation**: Define HPAs for all services. Conduct load testing simulating agent traffic patterns (burst, concurrent, retry). Size backing stores (Redis) for agent-induced read volume.
- **Estimated Effort**: Medium

### DATA-Q2: Data Residency and Sovereignty

- **Severity**: RISK in 10 of 10 applicable services
- **Affected Services**: frontend, cartservice, productcatalogservice, checkoutservice, paymentservice, currencyservice, shippingservice, emailservice, recommendationservice, adservice
- **Common Finding**: No data residency requirements documented. Deployed to `us-central1` by default. No GDPR/LGPD compliance references. Services process PII and financial data with no residency controls.
- **Compensating Controls**: Ensure agent LLM endpoints are in the same region as data (`us-central1`). Document data residency posture.
- **Portfolio-Level Recommendation**: Conduct a portfolio-wide data residency assessment. Document whether customer data is subject to residency or sovereignty requirements. Configure agent LLM endpoints to respect boundaries.
- **Estimated Effort**: Medium

### DATA-Q3: Selective Query Support

- **Severity**: RISK in 8 of 10 applicable services
- **Affected Services**: frontend, cartservice, productcatalogservice, checkoutservice, paymentservice, shippingservice, emailservice, recommendationservice
- **Common Finding**: No pagination, filtering, or sorting on most query endpoints. `ListProducts` returns all products unbounded. `GetCart` returns all items. No cursor-based pagination or GraphQL field selection.
- **Compensating Controls**: Current datasets are small enough for unbounded retrieval. Agents can filter client-side.
- **Portfolio-Level Recommendation**: Add pagination parameters (`limit`, `offset` or cursor-based) to list/query endpoints across all services.
- **Estimated Effort**: Medium

### DATA-Q4: System of Record Designations

- **Severity**: RISK in 9 of 10 applicable services
- **Affected Services**: frontend, cartservice, productcatalogservice, checkoutservice, paymentservice, shippingservice, emailservice, recommendationservice, adservice
- **Common Finding**: No system-of-record designations or data ownership documentation. Microservice architecture implicitly designates each service as SOR for its domain, but this is not documented.
- **Compensating Controls**: Document implicit SOR designations based on microservice boundaries.
- **Portfolio-Level Recommendation**: Publish a data ownership matrix mapping each data domain to its authoritative service.
- **Estimated Effort**: Low

### DATA-Q5: Reliable Timestamps

- **Severity**: RISK in 10 of 10 applicable services
- **Affected Services**: frontend, cartservice, productcatalogservice, checkoutservice, paymentservice, currencyservice, shippingservice, emailservice, recommendationservice, adservice
- **Common Finding**: No `created_at` or `updated_at` timestamp fields on business entities. Protobuf messages for Product, Cart, Order have no temporal metadata. Log timestamps exist but entity-level timestamps are absent.
- **Compensating Controls**: Log timestamps provide request-level temporal context. Backend data is queried fresh per request.
- **Portfolio-Level Recommendation**: Add timestamp fields to all protobuf messages. Standardize on UTC with RFC3339 format.
- **Estimated Effort**: Medium

### DATA-Q6: Data Freshness Signaling

- **Severity**: RISK in 9 of 10 applicable services
- **Affected Services**: frontend, cartservice, productcatalogservice, checkoutservice, paymentservice, currencyservice, shippingservice, emailservice, recommendationservice
- **Common Finding**: No freshness signaling — no `Cache-Control` headers, no `X-Data-Age`, no consistency level indicators. Data is fetched fresh per request (no caching layer) but freshness is not communicated to consumers.
- **Compensating Controls**: Fresh-fetch behavior means data is implicitly current but not explicitly signaled.
- **Portfolio-Level Recommendation**: Add freshness metadata to gRPC response trailing metadata and HTTP headers.
- **Estimated Effort**: Low

### DATA-Q7: PII Redaction in Logs

- **Severity**: RISK in 8 of 10 applicable services
- **Affected Services**: frontend, cartservice, productcatalogservice, checkoutservice, paymentservice, shippingservice, emailservice, recommendationservice
- **Common Finding**: `Console.WriteLine` and basic logging statements log `userId` and potentially other PII in plaintext. No PII scrubbing middleware or masking libraries. Frontend's chatbot handler uses `fmt.Printf` to print response bodies to stdout.
- **Compensating Controls**: Middleware logging design avoids logging request bodies in most cases. Verify userId format (opaque UUID vs. PII).
- **Portfolio-Level Recommendation**: Implement a portfolio-wide structured logging standard with PII-safe logging wrappers. Replace unstructured logging with `ILogger<T>` (C#), structured loggers (Go/Python/Node.js), and configure PII redaction filters.
- **Estimated Effort**: Medium

### DISC-Q1: Schema Documentation and Versioning

- **Severity**: RISK in 10 of 10 applicable services
- **Affected Services**: frontend, cartservice, productcatalogservice, checkoutservice, paymentservice, currencyservice, shippingservice, emailservice, recommendationservice, adservice
- **Common Finding**: Proto files define typed schemas but are not versioned (package `hipstershop` with no version qualifier). No schema registry. No database migration files. No proto versioning or backward-compatibility validation.
- **Compensating Controls**: Proto3 provides implicit backward compatibility for additive changes. Pin agent tool definitions to proto file hashes.
- **Portfolio-Level Recommendation**: Adopt proto package versioning and publish to a schema registry. Implement `buf` for breaking change detection in CI.
- **Estimated Effort**: Medium

### OBS-Q1: Distributed Tracing and Structured Logging

- **Severity**: RISK in 11 of 11 applicable services
- **Affected Services**: frontend, cartservice, productcatalogservice, checkoutservice, paymentservice, currencyservice, shippingservice, emailservice, recommendationservice, adservice, platform-infra
- **Common Finding**: Tracing and structured logging maturity varies widely. Frontend has OpenTelemetry instrumentation (disabled by default). Some Go services have OTel. C# cartservice has no OTel. Most services use unstructured logging. Tracing is opt-in (`ENABLE_TRACING=1`) and disabled by default across the portfolio.
- **Compensating Controls**: Enable tracing by setting environment variables. Istio sidecar provides basic request-level tracing.
- **Portfolio-Level Recommendation**: Enable OpenTelemetry tracing by default across all services. Deploy the OpenTelemetry Collector (already defined in Helm chart). Standardize structured JSON logging with correlation IDs.
- **Estimated Effort**: Medium

### OBS-Q2: Alerting on Error Rates and Latency

- **Severity**: RISK in 11 of 11 applicable services
- **Affected Services**: frontend, cartservice, productcatalogservice, checkoutservice, paymentservice, currencyservice, shippingservice, emailservice, recommendationservice, adservice, platform-infra
- **Common Finding**: No alerting configuration anywhere. No Cloud Monitoring alerting policies, no PagerDuty/OpsGenie, no SLO-based alerting. gRPC health probes exist for Kubernetes liveness/readiness but not proactive alerting.
- **Compensating Controls**: Kubernetes health probes detect and restart unhealthy pods. Agent orchestration can implement health monitoring.
- **Portfolio-Level Recommendation**: Create portfolio-wide Cloud Monitoring alerting policies: gRPC error rate > 1%, P95 latency > 500ms, backing store failures. Configure notification channels.
- **Estimated Effort**: Medium

### ENG-Q1: Infrastructure Governance for Agent-Facing Surface

- **Severity**: RISK in 11 of 11 applicable services
- **Affected Services**: frontend, cartservice, productcatalogservice, checkoutservice, paymentservice, currencyservice, shippingservice, emailservice, recommendationservice, adservice, platform-infra
- **Common Finding**: Infrastructure defined as code (Terraform, K8s manifests, Helm). Terraform validation CI exists (syntax check only). No drift detection. No `terraform plan` review step. No enforced peer review for IaC changes.
- **Compensating Controls**: CI-triggered deployments enforce desired state. PR-based workflow provides opportunity for review.
- **Portfolio-Level Recommendation**: Add `terraform plan` to PR comments. Implement drift detection. Enforce required reviews for infrastructure changes.
- **Estimated Effort**: Medium

### ENG-Q2: CI/CD with API Contract Testing

- **Severity**: RISK in 11 of 11 applicable services
- **Affected Services**: frontend, cartservice, productcatalogservice, checkoutservice, paymentservice, currencyservice, shippingservice, emailservice, recommendationservice, adservice, platform-infra
- **Common Finding**: CI runs unit tests and deployment smoke tests. No API contract testing — no Pact, no proto breaking change detection, no consumer-driven contracts. Breaking changes to proto definitions are not caught until deployment.
- **Compensating Controls**: Unit tests validate basic API behavior. Smoke tests catch gross deployment failures.
- **Portfolio-Level Recommendation**: Add `buf` for proto linting and breaking change detection to the shared CI pipeline. Implement consumer-driven contract tests for critical agent-consumed APIs.
- **Estimated Effort**: Medium

### ENG-Q3: Rollback Capability

- **Severity**: RISK in 11 of 11 applicable services
- **Affected Services**: frontend, cartservice, productcatalogservice, checkoutservice, paymentservice, currencyservice, shippingservice, emailservice, recommendationservice, adservice, platform-infra
- **Common Finding**: Deployment uses Skaffold with `kubectl apply`. No automated rollback triggers. No blue/green or canary deployment. Manual `kubectl rollout undo` and `helm rollback` available.
- **Compensating Controls**: Kubernetes rolling deployment provides pod-level health verification. Helm supports one-command rollback.
- **Portfolio-Level Recommendation**: Implement automated rollback triggers based on error rate metrics. Consider canary deployment with Istio traffic shifting.
- **Estimated Effort**: Medium

### ENG-Q4: API Test Coverage

- **Severity**: RISK in 11 of 11 applicable services
- **Affected Services**: frontend, cartservice, productcatalogservice, checkoutservice, paymentservice, currencyservice, shippingservice, emailservice, recommendationservice, adservice, platform-infra
- **Common Finding**: Tests cover basic happy-path scenarios. No edge case tests, no error scenario tests, no concurrent access tests. No API contract tests. No load/performance tests. Coverage gaps are consistent across the portfolio.
- **Compensating Controls**: Existing tests cover core CRUD operations. Smoke tests validate end-to-end behavior.
- **Portfolio-Level Recommendation**: Establish a minimum test coverage standard for agent-consumed APIs: happy path, error scenarios, concurrent access, and contract compliance.
- **Estimated Effort**: High

### ENG-Q5: Encryption at Rest for Agent-Accessible Data

- **Severity**: RISK in 9 of 11 applicable services
- **Affected Services**: frontend, cartservice, productcatalogservice, checkoutservice, paymentservice, shippingservice, emailservice, recommendationservice, platform-infra
- **Common Finding**: No explicit encryption at rest configuration. Redis uses ephemeral `emptyDir` volume. Memorystore Redis has no CMEK. GCP-managed services use default Google-managed encryption. No customer-managed KMS keys.
- **Compensating Controls**: GKE Autopilot and GCP-managed services provide default encryption. In-cluster Redis `emptyDir` is ephemeral.
- **Portfolio-Level Recommendation**: Enable CMEK for Memorystore Redis and GCP-managed databases. Configure transit encryption for all data stores.
- **Estimated Effort**: Medium

### ENG-Q6: Cross-Origin and Network Policies

- **Severity**: RISK in 11 of 11 applicable services
- **Affected Services**: frontend, cartservice, productcatalogservice, checkoutservice, paymentservice, currencyservice, shippingservice, emailservice, recommendationservice, adservice, platform-infra
- **Common Finding**: Network policies, AuthorizationPolicies, and Sidecars are all **defined in Helm chart templates and Kustomize components but disabled by default** (`networkPolicies.create: false`, `authorizationPolicies.create: false`, `sidecars.create: false`). The default deployment has no network-level access controls. Frontend is exposed via LoadBalancer to the internet.
- **Compensating Controls**: Enable policies by setting Helm values. The Kustomize `network-policies` profile enables network policies when used.
- **Portfolio-Level Recommendation**: Enable NetworkPolicies and AuthorizationPolicies by default in all production deployments. The infrastructure is already built — it just needs to be turned on.
- **Estimated Effort**: Low

### HITL-Q3: Sandbox/Staging Environment

- **Severity**: RISK in 10 of 10 applicable services
- **Affected Services**: frontend, cartservice, productcatalogservice, checkoutservice, paymentservice, currencyservice, shippingservice, emailservice, recommendationservice, adservice
- **Common Finding**: CI creates ephemeral per-PR namespaces for staging. No permanent sandbox with production-equivalent data shape. No synthetic data generators or seed data scripts. No Docker Compose for local testing.
- **Compensating Controls**: Use PR-based environments for initial agent testing. Helm chart supports full environment deployment.
- **Portfolio-Level Recommendation**: Create a persistent agent-testing namespace with seed data. Add Docker Compose for self-contained local development. Create synthetic data generators.
- **Estimated Effort**: Medium

## Service Dependency Map

> Dependencies were inferred from individual ARA report findings and Kubernetes manifest environment variables (not explicitly provided via `dependency_overrides`). Inferred dependencies may be incomplete — they reflect only what was observable in the assessed code and report context. For authoritative dependency data, add `dependency_overrides` to the portfolio config.

### Dependency Overview

| Source Service | Target Service | Type | Description |
|---------------|---------------|------|-------------|
| frontend | productcatalogservice | sync | gRPC call to list/get products (`PRODUCT_CATALOG_SERVICE_ADDR`) |
| frontend | currencyservice | sync | gRPC call for currency conversion (`CURRENCY_SERVICE_ADDR`) |
| frontend | cartservice | sync | gRPC call to manage cart (`CART_SERVICE_ADDR`) |
| frontend | recommendationservice | sync | gRPC call for product recommendations (`RECOMMENDATION_SERVICE_ADDR`) |
| frontend | shippingservice | sync | gRPC call for shipping quotes (`SHIPPING_SERVICE_ADDR`) |
| frontend | checkoutservice | sync | gRPC call to place orders (`CHECKOUT_SERVICE_ADDR`) |
| frontend | adservice | sync | gRPC call for contextual ads (`AD_SERVICE_ADDR`) |
| checkoutservice | cartservice | sync | gRPC call to get/empty cart during checkout |
| checkoutservice | productcatalogservice | sync | gRPC call to look up product details |
| checkoutservice | shippingservice | sync | gRPC call for shipping cost and order shipment |
| checkoutservice | currencyservice | sync | gRPC call for currency conversion |
| checkoutservice | paymentservice | sync | gRPC call for payment processing |
| checkoutservice | emailservice | sync | gRPC call to send order confirmation email |
| recommendationservice | productcatalogservice | sync | gRPC call to get product catalog for recommendations |
| cartservice | redis-cart | shared_db | Redis backing store for cart data |
| All services | platform-infra | shared_infra | Shared GKE cluster, Helm chart, Istio mesh, CI/CD pipelines |

### Service Dependency Metrics

| Service | Fan-In | Fan-Out | Role | Readiness Profile |
|---------|--------|---------|------|-------------------|
| productcatalogservice | 3 | 0 | Foundation | Remediation Required (1B) |
| currencyservice | 2 | 0 | Foundation | Remediation Required (1B) |
| cartservice | 2 | 1 | Foundation | Remediation Required (2B) |
| paymentservice | 1 | 0 | Internal | Remediation Required (2B) |
| shippingservice | 2 | 0 | Internal | Remediation Required (2B) |
| emailservice | 1 | 0 | Internal | Remediation Required (2B) |
| adservice | 1 | 0 | Internal | Remediation Required (1B) |
| recommendationservice | 1 | 1 | Internal | Remediation Required (2B) |
| checkoutservice | 1 | 6 | Leaf / Orchestrator | Remediation Required (2B) |
| frontend | 0 | 7 | Leaf / Entry Point | Not Agent-Integrable (3B) |
| platform-infra | 11 | 0 | Foundation | Remediation Required (1B) |

### High-Risk Dependency Patterns

1. **Frontend is Not Agent-Integrable but is the primary entry point**
   - **Affected Services**: All backend services are reachable through frontend
   - **Risk**: The frontend (Not Agent-Integrable with 3 BLOCKERs: API-Q1, AUTH-Q1, DATA-Q1) is the web entry point. However, for agent integration, backend gRPC services can be accessed directly — agents do not need to go through the HTML-rendering frontend. The frontend's Not Agent-Integrable status does NOT block agent integration with backend services.
   - **Recommendation**: For the customer support agent use case (order tracking, product recommendations, cart management), bypass the frontend and connect agents directly to backend gRPC services (productcatalogservice, cartservice, checkoutservice, recommendationservice). This avoids the frontend's API-Q1 BLOCKER (HTML-only endpoints).

2. **productcatalogservice is a high fan-in Foundation service with 1 BLOCKER**
   - **Affected Services**: frontend, checkoutservice, recommendationservice (3 consumers)
   - **Risk**: productcatalogservice is depended on by 3 services and has only 1 BLOCKER (AUTH-Q1). It is the closest Foundation service to becoming agent-integrable.
   - **Recommendation**: Prioritize AUTH-Q1 remediation for productcatalogservice — resolving this single BLOCKER would make it eligible for Pilot-Ready (depending on RISK count), unlocking product query capabilities for the customer support agent.

3. **checkoutservice is a high fan-out Orchestrator with cascading dependencies**
   - **Affected Services**: cartservice, productcatalogservice, shippingservice, currencyservice, paymentservice, emailservice
   - **Risk**: checkoutservice depends synchronously on 6 backend services. If any dependency service is degraded, the entire checkout flow fails. All 6 dependencies have AUTH-Q1 BLOCKER. Checkout integration requires all dependencies to resolve AUTH-Q1 first.
   - **Recommendation**: Resolve AUTH-Q1 across all checkout path services before attempting agent-driven checkout. For the initial pilot, scope the agent to read-only operations (product queries, cart viewing) that do not require the full checkout dependency chain.

4. **platform-infra is the shared infrastructure Foundation with AUTH-Q1 BLOCKER**
   - **Affected Services**: All 10 application services
   - **Risk**: The infrastructure repo defines Kubernetes ServiceAccounts, Istio configs, and Terraform IaC for the entire platform. Its AUTH-Q1 BLOCKER (no agent-facing identity mechanism) cascades to all services — if the platform doesn't support agent identity, no individual service can authenticate agents.
   - **Recommendation**: Resolve platform-infra's AUTH-Q1 first by enabling Istio AuthorizationPolicies and creating agent-specific ServiceAccounts at the platform level. This unblocks AUTH-Q1 remediation for all application services.

## Portfolio Remediation Guidance

> Portfolio context: Cloud-native e-commerce platform with 11 microservices evaluating for autonomous AI agent integration — customer support agent for order tracking, product recommendations, and cart management.

### Remediation Priority Order

Remediation of cross-cutting BLOCKERs should follow this general priority:

1. **Identity and Access** — Resolve AUTH-section BLOCKERs first. You cannot enforce any other security control without machine identity and scoped permissions.
2. **Data Integrity** — Resolve STATE and DATA-section BLOCKERs second. Protect data before enabling agent write operations.
3. **API Surface** — Resolve API-section BLOCKERs third. Ensure a stable, documented integration surface for agent tools.
4. **Remaining BLOCKERs** — Address in order of affected service count (most affected first).

### Coordinated Remediation Plan

#### Identity Foundation

**BLOCKERs addressed**: AUTH-Q1
**Services affected**: All 11 services (frontend, cartservice, productcatalogservice, checkoutservice, paymentservice, currencyservice, shippingservice, emailservice, recommendationservice, adservice, platform-infra)

- **What to do**:
  1. **Platform-level (Week 1–2)**: Enable Istio AuthorizationPolicies by setting `authorizationPolicies.create: true` in `helm-chart/values.yaml`. This is a single configuration change that activates mTLS-based service identity authentication across all services using existing Helm chart templates. The templates already define per-service, per-operation authorization rules.
  2. **Platform-level (Week 2–3)**: Create agent-specific Kubernetes ServiceAccounts (e.g., `agent-reader-v1`) with Istio AuthorizationPolicy rules scoped to read-only operations (`GetCart`, `ListProducts`, `GetProduct`, `ListRecommendations`, `GetQuote`, `GetSupportedCurrencies`).
  3. **Per-service (Week 3–6)**: For defense-in-depth, add application-layer authentication interceptors in each service (gRPC interceptors in Go/Java/C#/Python/Node.js) that validate caller identity and log authenticated principal.
  4. **Validation**: Verify that unauthenticated gRPC calls are rejected with `codes.Unauthenticated`. Verify agent ServiceAccount can only call authorized operations.
- **Expected outcome**: Every service authenticates callers via mTLS. Agent identity is a distinct, auditable principal. Identity foundation enables all subsequent security controls (scoped permissions, audit logging, identity suspension).
- **Effort**: Low (platform enablement) + Medium (per-service hardening)

#### Data Protection

**BLOCKERs addressed**: DATA-Q1
**Services affected**: frontend, cartservice, checkoutservice, paymentservice, shippingservice, emailservice, recommendationservice (7 services)

- **What to do**:
  1. **Portfolio-level (Week 1)**: Define a data classification taxonomy: `PUBLIC` (product catalog, exchange rates, ads), `INTERNAL` (cart items, shipping quotes), `PII` (email, address, userId), `PCI` (credit card number, CVV, expiration). Document in a shared data dictionary.
  2. **Portfolio-level (Week 2)**: Annotate the shared `demo.proto` protobuf definitions with classification metadata (comments or custom options) for each message field.
  3. **Per-service (Week 3–8)**: Implement field-level access controls in services handling PII/PCI data. Ensure agents with read-only scope cannot access PCI fields (credit card data) even if they have network access to paymentservice or checkoutservice.
  4. **Per-service (Week 4–8)**: Implement field-level encryption for PCI data in transit (mTLS addresses transport encryption) and at rest (CMEK for Redis/databases).
- **Expected outcome**: All sensitive fields are classified and tagged. Agent identities require explicit authorization to access PII/PCI data. Credit card data is encrypted end-to-end.
- **Effort**: Medium (classification) + High (field-level access controls and encryption)

#### API Surface (Frontend-Specific)

**BLOCKERs addressed**: API-Q1 (frontend only — not cross-cutting)
**Services affected**: frontend

- **What to do**:
  - **Option A (Recommended for agent use case)**: Bypass the frontend entirely. Connect the customer support agent directly to backend gRPC services (productcatalogservice, cartservice, recommendationservice) via an API Gateway or gRPC proxy. The backend services already expose documented, typed gRPC interfaces suitable for agent tool binding.
  - **Option B**: Create a dedicated REST API layer on the frontend (`/api/v1/products`, `/api/v1/cart`, `/api/v1/checkout`) returning structured JSON, separate from the HTML-rendering endpoints.
- **Expected outcome**: Agents have a documented, programmatic API to bind tools against — either gRPC backends directly or a new REST layer on the frontend.
- **Effort**: Low (Option A — API Gateway configuration) or Medium (Option B — REST API development)

## Agentic Program Recommendations

> These are engagement-level recommendations based on the portfolio's agentic readiness
> profile. Discuss with your AWS Solutions Architect to determine eligibility and timing.

> No specific agentic program recommendations based on current findings. The portfolio has **0 Agent-Ready and 0 Pilot-Ready services** — the EBA-Agentic AI trigger condition (≥1 service at Agent-Ready or Pilot-Ready) is not met. As the portfolio's agentic readiness improves, re-assess to identify program eligibility.

### Path to EBA-Agentic AI Eligibility

The following services are **closest to Pilot-Ready** (fewest BLOCKERs):

| Service | BLOCKERs | BLOCKER Question(s) | Path to Pilot-Ready |
|---------|----------|---------------------|---------------------|
| productcatalogservice | 1 | AUTH-Q1 | Resolve AUTH-Q1 (enable Istio AuthorizationPolicy). With 32 RISKs, would need RISK reduction to ≤5 for Pilot-Ready. |
| currencyservice | 1 | AUTH-Q1 | Resolve AUTH-Q1. With 23 RISKs, would need RISK reduction to ≤5 for Pilot-Ready. |
| adservice | 1 | AUTH-Q1 | Resolve AUTH-Q1. With 23 RISKs, would need RISK reduction to ≤5 for Pilot-Ready. |

**Recommended approach**: Focus AUTH-Q1 remediation on **productcatalogservice** first (highest priority Foundation service with P0 priority and 3 consumers). Once AUTH-Q1 is resolved portfolio-wide via Istio enablement, productcatalogservice, currencyservice, and adservice become candidates for accelerated RISK remediation toward Pilot-Ready status.

Once any service reaches Pilot-Ready, the portfolio qualifies for **EBA-Agentic AI** engagement.

### Program Details

#### EBA-Agentic AI (Experience-Based Acceleration for Agentic AI)

**Not yet eligible.** This program provides guided acceleration for services ready to begin agent integration. The trigger condition requires ≥1 service at Agent-Ready or Pilot-Ready profile. Current portfolio status: 0 Agent-Ready, 0 Pilot-Ready, 10 Remediation Required, 1 Not Agent-Integrable.

**Suggested timing**: Re-assess after completing the Identity Foundation remediation (AUTH-Q1 across all services via Istio AuthorizationPolicy enablement). If productcatalogservice, currencyservice, or adservice achieve Pilot-Ready status, request EBA engagement to accelerate the initial agent pilot for product catalog queries.

## Portfolio-Level Findings

> These questions evaluate capabilities that can only be assessed by looking across
> multiple repos. They are distinct from cross-cutting analysis (which aggregates
> individual findings). Individual report findings are never overridden.

### PORT-ARA-Q1: Centralized Identity Plane

- **Severity**: BLOCKER
- **Finding**: No shared identity provider exists across the portfolio. Each service has a Kubernetes ServiceAccount (pod-level identity), and the platform-infra repo defines a GCP `google_service_account` for GKE cluster operations (`roles/monitoring.metricWriter`, `roles/logging.logWriter`, etc.). However, these are infrastructure identities — not an agent-facing identity plane. No Cognito User Pools, no Cognito Identity Pools, no Okta configurations, no shared OAuth2 authorization server, and no centralized API key management exist anywhere in the portfolio. The Istio service mesh could provide mTLS-based identity via Kubernetes ServiceAccount principals, but Istio AuthorizationPolicies are disabled by default (`authorizationPolicies.create: false`).
- **Evidence**: `helm-chart/values.yaml` (`authorizationPolicies.create: false`), `terraform/main.tf` (GCP service account for monitoring only), all 11 `kubernetes-manifests/*.yaml` files (ServiceAccount definitions without auth enforcement)
- **Recommendation**: Enable Istio as the centralized identity plane by setting `authorizationPolicies.create: true`. Create agent-specific Kubernetes ServiceAccounts with Istio AuthorizationPolicy rules. For external agent callers, deploy an API Gateway (GKE Gateway API or Istio Ingress Gateway) with OAuth2/API key authentication.
- **Affected Services**: All 11 services
- **Contextual Annotations**: This finding directly relates to the AUTH-Q1 cross-cutting BLOCKER. Enabling Istio AuthorizationPolicies would establish a mesh-level identity plane that addresses AUTH-Q1 for all services simultaneously — **verify** that mTLS strict mode is enforced and that agent ServiceAccounts are created with appropriate scoping.

### PORT-ARA-Q2: Cross-Service Audit Correlation

- **Severity**: RISK
- **Finding**: Cross-service audit correlation is partially supported but not consistently enabled. The frontend has OpenTelemetry SDK instrumentation (`otelhttp.NewHandler`, `otelgrpc.NewClientHandler()`) with trace context propagation (`propagation.TraceContext{}`, `propagation.Baggage{}`) — but tracing is disabled by default (`ENABLE_TRACING=1` opt-in, `googleCloudOperations.tracing: false`). Some Go services (checkoutservice, productcatalogservice, shippingservice) have similar OTel instrumentation. The C# cartservice has **no** OpenTelemetry SDK. The Helm chart defines an optional OpenTelemetry Collector (`opentelemetryCollector.create: false`). No shared CloudTrail trail, no centralized log aggregation with correlation IDs, and no consistent `traceparent` header propagation across all services. GKE provides cluster-level audit logging for Kubernetes API operations but not application-level agent action tracing.
- **Evidence**: `helm-chart/values.yaml` (`googleCloudOperations.tracing: false`, `opentelemetryCollector.create: false`), `src/frontend/main.go` (`ENABLE_TRACING` conditional), `src/cartservice/cartservice.csproj` (no OTel dependencies)
- **Recommendation**: Enable OpenTelemetry tracing by default across all services (`ENABLE_TRACING=1` or equivalent). Deploy the OpenTelemetry Collector (`opentelemetryCollector.create: true`). Add OTel SDK to cartservice (C#). Ensure consistent `traceparent` header propagation through all gRPC calls. Configure trace export to a centralized backend (Cloud Trace or Jaeger).
- **Affected Services**: All 11 services (varying levels of OTel maturity)
- **Contextual Annotations**: This finding provides context for the OBS-Q1 cross-cutting RISK. Enabling the OpenTelemetry Collector and tracing by default would address OBS-Q1 across all services — **verify** that trace context propagation works end-to-end through the checkout flow (frontend → checkoutservice → cartservice → paymentservice → emailservice).

### PORT-ARA-Q3: Portfolio-Level Rate Limiting

- **Severity**: RISK
- **Finding**: No shared WAF, API Gateway, or portfolio-level rate limiting exists. The frontend is exposed directly to the internet via a Kubernetes LoadBalancer service on port 80 with no rate limiting. Individual services have no application-level rate limiting middleware. No `WAF WebACL`, no API Gateway usage plans, no Istio rate limiting EnvoyFilters. Each service relies solely on Kubernetes resource limits (CPU/memory) for isolation — which prevents resource exhaustion but does not prevent request flooding.
- **Evidence**: `kubernetes-manifests/frontend.yaml` (LoadBalancer service, no rate limiting), `helm-chart/values.yaml` (no rate limit configuration), all service deployment manifests (no rate limiting middleware)
- **Recommendation**: Deploy an Istio Ingress Gateway or GKE Gateway API with rate limiting for the portfolio perimeter. Define per-identity rate limits for agent traffic. Implement per-service rate limiting as defense-in-depth. For immediate protection, configure agent-side rate limiting in the orchestration layer.
- **Affected Services**: All 11 services (frontend especially — internet-facing)
- **Contextual Annotations**: This finding provides context for the STATE-Q5 cross-cutting RISK. A portfolio-level API Gateway with rate limiting would address STATE-Q5 for agent-facing traffic at the perimeter — **verify** that rate limits are configured per agent identity and that rate limit headers are returned to agents for self-throttling.

### PORT-ARA-Q4: Transitive Dependency Safety

- **Severity**: RISK
- **Finding**: No services currently have Agent-Ready or Pilot-Ready profiles, so the BLOCKER trigger condition (Agent-Ready/Pilot-Ready service depending synchronously on a Not Agent-Integrable service) is not met. However, a RISK pattern exists: the frontend (Not Agent-Integrable) is the primary web entry point, and its 7 backend dependencies are all Remediation Required. If agents were to integrate through the frontend, the frontend's 3 BLOCKERs would cascade. Additionally, checkoutservice (Remediation Required) depends synchronously on 6 services that all have AUTH-Q1 BLOCKERs — resolving checkoutservice's own BLOCKERs would not make it usable until all 6 dependencies also resolve AUTH-Q1.
- **Evidence**: Dependency graph from Step 5; readiness profiles from Step 3; frontend (Not Agent-Integrable, 3B) depends on 7 services; checkoutservice depends on 6 services all with AUTH-Q1 BLOCKER
- **Recommendation**: For the customer support agent pilot, bypass the frontend and connect directly to backend gRPC services. Prioritize AUTH-Q1 remediation for Foundation services (productcatalogservice, currencyservice, cartservice) before attempting agent integration with orchestrator services (checkoutservice) that depend on them.
- **Affected Services**: frontend (Not Agent-Integrable), checkoutservice (depends on 6 services with AUTH-Q1 BLOCKER)
- **Contextual Annotations**: This finding provides context for the remediation prioritization. Resolving AUTH-Q1 at the platform level (Istio AuthorizationPolicy) addresses the transitive dependency chain for all services simultaneously — **verify** that after enablement, each service in the checkout chain correctly propagates identity through gRPC calls.

### PORT-ARA-Q5: Agent Identity Governance

- **Severity**: RISK
- **Finding**: No centralized mechanism exists to suspend or revoke agent identities across all services simultaneously. Each service manages identities independently — there is no shared Cognito app client registry, no centralized API key management, and no portfolio-level agent identity documentation. The Istio AuthorizationPolicy model (when enabled) binds identities to individual service policies, meaning suspending an agent would require updating AuthorizationPolicies across multiple services. No "kill switch" can revoke an agent's access to all services in a single action.
- **Evidence**: `helm-chart/values.yaml` (per-service AuthorizationPolicy templates), absence of centralized identity management infrastructure across all repos
- **Recommendation**: Create a centralized agent identity registry (a shared ConfigMap or dedicated identity service) that maps agent ServiceAccounts to their authorized services and scopes. Implement a portfolio-level suspension runbook: `kubectl delete serviceaccount agent-reader-v1 -n <namespace>` would revoke the agent's mTLS identity, effectively blocking it from all services simultaneously via Istio.
- **Affected Services**: All 11 services
- **Contextual Annotations**: This finding provides context for the AUTH-Q8 cross-cutting RISK (Agent Identity Suspension). Using Kubernetes ServiceAccount deletion as the kill switch mechanism works because Istio AuthorizationPolicies bind to ServiceAccount principals — **verify** that deleting the ServiceAccount immediately invalidates the mTLS certificate and blocks all in-flight requests.

## Service-by-Service Summary

| Service | Repo Type | Agent Scope | Readiness Profile | BLOCKERs | RISKs | INFOs | N/A |
|---------|-----------|-------------|-------------------|----------|-------|-------|-----|
| frontend | application | read-only | ❌ Not Agent-Integrable | 3 | 32 | 14 | 0 |
| cartservice | application | read-only | 🟠 Remediation Required | 2 | 31 | 16 | 0 |
| checkoutservice | application | read-only | 🟠 Remediation Required | 2 | 32 | 15 | 0 |
| paymentservice | application | read-only | 🟠 Remediation Required | 2 | 31 | 16 | 0 |
| productcatalogservice | application | read-only | 🟠 Remediation Required | 1 | 32 | 16 | 0 |
| shippingservice | application | read-only | 🟠 Remediation Required | 2 | 32 | 15 | 0 |
| recommendationservice | application | read-only | 🟠 Remediation Required | 2 | 32 | 15 | 0 |
| currencyservice | application | read-only | 🟠 Remediation Required | 1 | 23 | 25 | 0 |
| emailservice | application | read-only | 🟠 Remediation Required | 2 | 32 | 15 | 0 |
| adservice | application | read-only | 🟠 Remediation Required | 1 | 23 | 25 | 0 |
| platform-infra | infrastructure-only | read-only | 🟠 Remediation Required | 1 | 13 | 1 | 34 |

### Individual Service Details

#### frontend

- **Readiness Profile**: ❌ Not Agent-Integrable
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P0
- **BLOCKERs** (3):
  - API-Q1: No documented API interface — HTTP endpoints render HTML, not JSON. Only `/product-meta/{ids}` and `/bot` return JSON.
  - AUTH-Q1: No machine identity authentication — `ensureSessionID` assigns random UUID cookie, not authentication. gRPC uses `insecure.NewCredentials()`.
  - DATA-Q1: Sensitive data unclassified — `placeOrderHandler` processes PII and credit card data with no classification or field-level encryption.
- **RISKs** (32): API-Q2, API-Q3, API-Q5, API-Q7, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q6, AUTH-Q7, AUTH-Q8, STATE-Q1, STATE-Q2, STATE-Q4, STATE-Q5, STATE-Q7, HITL-Q3, DATA-Q2, DATA-Q3, DATA-Q4, DATA-Q5, DATA-Q6, DATA-Q7, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4, ENG-Q5, ENG-Q6
- **Key Recommendations**:
  - Bypass the frontend for agent integration — connect agents directly to backend gRPC services.
  - If frontend integration is needed, create a dedicated REST API layer returning JSON.
  - Resolve AUTH-Q1 via API Gateway with OAuth2 or API key authentication.
- **Depends On**: productcatalogservice, currencyservice, cartservice, recommendationservice, shippingservice, checkoutservice, adservice
- **Depended On By**: None (entry point)

#### cartservice

- **Readiness Profile**: 🟠 Remediation Required
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P0
- **BLOCKERs** (2):
  - AUTH-Q1: No authentication middleware — gRPC endpoints accept any connection on port 7070. Istio AuthorizationPolicy defined but disabled.
  - DATA-Q1: Cart data (`userId`, `productId`, `quantity`) unclassified — `userId` is potentially PII. No field-level encryption.
- **RISKs** (31): API-Q3, API-Q5, API-Q7, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q6, AUTH-Q7, AUTH-Q8, STATE-Q1, STATE-Q2, STATE-Q4, STATE-Q5, STATE-Q7, HITL-Q3, DATA-Q2, DATA-Q3, DATA-Q4, DATA-Q5, DATA-Q6, DATA-Q7, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4, ENG-Q5, ENG-Q6
- **Key Recommendations**:
  - Enable Istio AuthorizationPolicy (existing Helm chart templates already define per-operation rules).
  - Classify `userId` field — determine if it contains PII or is an opaque UUID.
  - Add OpenTelemetry SDK for distributed tracing.
- **Depends On**: redis-cart
- **Depended On By**: frontend, checkoutservice

#### checkoutservice

- **Readiness Profile**: 🟠 Remediation Required
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P0
- **BLOCKERs** (2):
  - AUTH-Q1: gRPC server created with no authentication interceptors, TLS, or mTLS. Uses `insecure.NewCredentials()` for all outbound connections.
  - DATA-Q1: Processes highly sensitive checkout data (email, address, credit card) with no classification or field-level encryption.
- **RISKs** (32): API-Q2, API-Q3, API-Q5, API-Q7, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q6, AUTH-Q7, AUTH-Q8, STATE-Q1, STATE-Q2, STATE-Q4, STATE-Q5, STATE-Q7, HITL-Q3, DATA-Q2, DATA-Q3, DATA-Q4, DATA-Q5, DATA-Q6, DATA-Q7, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4, ENG-Q5, ENG-Q6
- **Key Recommendations**:
  - Enable Istio AuthorizationPolicy and mTLS for all 6 outbound gRPC connections.
  - Classify and encrypt PCI data (credit card fields) in the checkout flow.
  - Implement async order processing with status polling for agent consumption.
- **Depends On**: cartservice, productcatalogservice, shippingservice, currencyservice, paymentservice, emailservice
- **Depended On By**: frontend

#### paymentservice

- **Readiness Profile**: 🟠 Remediation Required
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P0
- **BLOCKERs** (2):
  - AUTH-Q1: gRPC server uses `grpc.ServerCredentials.createInsecure()` — no authentication. Istio AuthorizationPolicy available but disabled.
  - DATA-Q1: Handles credit card charge data with no classification. Simulated payment processing but real data structures.
- **RISKs** (31): API-Q3, API-Q5, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q6, AUTH-Q7, AUTH-Q8, STATE-Q1, STATE-Q2, STATE-Q4, STATE-Q5, STATE-Q7, HITL-Q3, DATA-Q2, DATA-Q3, DATA-Q4, DATA-Q5, DATA-Q6, DATA-Q7, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4, ENG-Q5, ENG-Q6
- **Key Recommendations**:
  - Enable Istio AuthorizationPolicy restricting access to checkoutservice only.
  - Classify credit card data as PCI and implement field-level encryption.
  - Implement structured JSON logging to replace console.log.
- **Depends On**: None
- **Depended On By**: checkoutservice

#### productcatalogservice

- **Readiness Profile**: 🟠 Remediation Required
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P0
- **BLOCKERs** (1):
  - AUTH-Q1: gRPC server created with `grpc.NewServer()` — no authentication interceptors, TLS, or mTLS. Uses `insecure.NewCredentials()` for outbound.
- **RISKs** (32): API-Q2, API-Q3, API-Q5, API-Q7, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q6, AUTH-Q7, AUTH-Q8, STATE-Q1, STATE-Q2, STATE-Q4, STATE-Q5, STATE-Q7, HITL-Q3, DATA-Q2, DATA-Q3, DATA-Q4, DATA-Q5, DATA-Q6, DATA-Q7, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4, ENG-Q5, ENG-Q6
- **Key Recommendations**:
  - **Highest priority Foundation service** — resolve AUTH-Q1 first (fewest BLOCKERs, highest fan-in).
  - Enable Istio AuthorizationPolicy for mTLS-based authentication.
  - Product catalog data is non-sensitive (INFO for DATA-Q1) — no data classification blocker.
- **Depends On**: None
- **Depended On By**: frontend, checkoutservice, recommendationservice

#### shippingservice

- **Readiness Profile**: 🟠 Remediation Required
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P1
- **BLOCKERs** (2):
  - AUTH-Q1: gRPC server created with `grpc.NewServer()` — no authentication. No OAuth2, API key, or mTLS.
  - DATA-Q1: Shipping data includes address PII (street, city, state, country) with no classification.
- **RISKs** (32): API-Q2, API-Q3, API-Q5, API-Q7, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q6, AUTH-Q7, AUTH-Q8, STATE-Q1, STATE-Q2, STATE-Q4, STATE-Q5, STATE-Q7, HITL-Q3, DATA-Q2, DATA-Q3, DATA-Q4, DATA-Q5, DATA-Q6, DATA-Q7, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4, ENG-Q5, ENG-Q6
- **Key Recommendations**:
  - Enable Istio AuthorizationPolicy.
  - Classify address fields as PII in the shipping data model.
  - Add gRPC authentication interceptor for defense-in-depth.
- **Depends On**: None
- **Depended On By**: frontend, checkoutservice

#### recommendationservice

- **Readiness Profile**: 🟠 Remediation Required
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P1
- **BLOCKERs** (2):
  - AUTH-Q1: gRPC server uses `grpc.insecure_channel()` and `server.add_insecure_port()` — no authentication. Istio AuthorizationPolicy available but disabled.
  - DATA-Q1: Processes product recommendation data that may include user behavior data with no classification.
- **RISKs** (32): API-Q2, API-Q3, API-Q5, API-Q7, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q6, AUTH-Q7, AUTH-Q8, STATE-Q1, STATE-Q2, STATE-Q4, STATE-Q5, STATE-Q7, HITL-Q3, DATA-Q2, DATA-Q3, DATA-Q4, DATA-Q5, DATA-Q6, DATA-Q7, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4, ENG-Q5, ENG-Q6
- **Key Recommendations**:
  - Enable Istio AuthorizationPolicy.
  - Key service for customer support agent use case — prioritize for pilot after AUTH-Q1 resolution.
  - Add OpenTelemetry tracing for end-to-end recommendation query visibility.
- **Depends On**: productcatalogservice
- **Depended On By**: frontend

#### currencyservice

- **Readiness Profile**: 🟠 Remediation Required
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P1
- **BLOCKERs** (1):
  - AUTH-Q1: gRPC server uses `grpc.ServerCredentials.createInsecure()` — no authentication. Istio AuthorizationPolicy available but disabled.
- **RISKs** (23): API-Q3, API-Q5, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q7, AUTH-Q8, STATE-Q1, STATE-Q5, STATE-Q7, HITL-Q3, DATA-Q2, DATA-Q5, DATA-Q6, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4, ENG-Q6
- **Key Recommendations**:
  - Enable Istio AuthorizationPolicy (single BLOCKER — closest to Pilot-Ready alongside productcatalogservice and adservice).
  - Currency exchange rates are public data (INFO for DATA-Q1) — no data classification blocker.
  - Low-risk Foundation service — good candidate for early pilot.
- **Depends On**: None
- **Depended On By**: frontend, checkoutservice

#### emailservice

- **Readiness Profile**: 🟠 Remediation Required
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (2):
  - AUTH-Q1: gRPC server uses `server.add_insecure_port()` — no authentication.
  - DATA-Q1: Processes email addresses and order confirmation details with no data classification.
- **RISKs** (32): API-Q2, API-Q3, API-Q5, API-Q7, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q6, AUTH-Q7, AUTH-Q8, STATE-Q1, STATE-Q2, STATE-Q4, STATE-Q5, STATE-Q7, HITL-Q3, DATA-Q2, DATA-Q3, DATA-Q4, DATA-Q5, DATA-Q6, DATA-Q7, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4, ENG-Q5, ENG-Q6
- **Key Recommendations**:
  - Enable Istio AuthorizationPolicy restricting access to checkoutservice only.
  - Classify email addresses as PII.
  - Lower priority for agent integration (P2, downstream notification service).
- **Depends On**: None
- **Depended On By**: checkoutservice

#### adservice

- **Readiness Profile**: 🟠 Remediation Required
- **Repo Type**: application
- **Agent Scope**: read-only
- **Priority**: P2
- **BLOCKERs** (1):
  - AUTH-Q1: gRPC server uses `ServerBuilder.forPort(port)` with no authentication interceptors. No TLS, mTLS, OAuth2, or API key.
- **RISKs** (23): API-Q3, API-Q5, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q7, AUTH-Q8, STATE-Q1, STATE-Q5, STATE-Q7, HITL-Q3, DATA-Q2, DATA-Q4, DATA-Q5, DATA-Q6, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4, ENG-Q6
- **Key Recommendations**:
  - Enable Istio AuthorizationPolicy (single BLOCKER — candidate for early remediation).
  - Ad data is non-sensitive (INFO for DATA-Q1) — no data classification blocker.
  - Lower priority for customer support agent use case (P2, ads are tangential).
- **Depends On**: None
- **Depended On By**: frontend

#### platform-infra

- **Readiness Profile**: 🟠 Remediation Required
- **Repo Type**: infrastructure-only
- **Agent Scope**: read-only
- **Priority**: Not set
- **BLOCKERs** (1):
  - AUTH-Q1: No agent-facing authentication mechanism in infrastructure. Kubernetes ServiceAccounts provide pod-level identity only. No external agent identity support.
- **RISKs** (13): AUTH-Q2, AUTH-Q3, AUTH-Q6, AUTH-Q7, AUTH-Q8, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4, ENG-Q5, ENG-Q6
- **N/A** (34): 34 questions not applicable to infrastructure-only repos (API surface, state management, HITL, data accessibility questions)
- **Key Recommendations**:
  - **Top priority**: Enable Istio AuthorizationPolicies (`authorizationPolicies.create: true`) — this single platform change addresses AUTH-Q1 for all 11 services.
  - Enable NetworkPolicies (`networkPolicies.create: true`) for defense-in-depth.
  - Deploy the OpenTelemetry Collector (`opentelemetryCollector.create: true`) for portfolio-wide tracing.
- **Depends On**: None
- **Depended On By**: All 10 application services

## Assessment Inventory

| # | Service | Report File | Assessment Date | Repo Type | Agent Scope |
|---|---------|-------------|-----------------|-----------|-------------|
| 1 | frontend | ./services/microservices-demo/src/frontend/frontend-ara-report.md | 2026-04-16 | application | read-only |
| 2 | cartservice | ./services/microservices-demo/src/cartservice/cartservice-ara-report.md | 2026-04-16 | application | read-only |
| 3 | productcatalogservice | ./services/microservices-demo/src/productcatalogservice/productcatalogservice-ara-report.md | 2026-04-16 | application | read-only |
| 4 | checkoutservice | ./services/microservices-demo/src/checkoutservice/checkoutservice-ara-report.md | 2026-04-16 | application | read-only |
| 5 | paymentservice | ./services/microservices-demo/src/paymentservice/paymentservice-ara-report.md | 2025-07-16 | application | read-only |
| 6 | currencyservice | ./services/microservices-demo/src/currencyservice/currencyservice-ara-report.md | 2026-04-16 | application | read-only |
| 7 | shippingservice | ./services/microservices-demo/src/shippingservice/shippingservice-ara-report.md | 2026-04-16 | application | read-only |
| 8 | emailservice | ./services/microservices-demo/src/emailservice/emailservice-ara-report.md | 2026-04-16 | application | read-only |
| 9 | recommendationservice | ./services/microservices-demo/src/recommendationservice/recommendationservice-ara-report.md | 2026-04-16 | application | read-only |
| 10 | adservice | ./services/microservices-demo/src/adservice/adservice-ara-report.md | 2025-07-16 | application | read-only |
| 11 | platform-infra | ./services/microservices-demo/microservices-demo-ara-report.md | 2026-04-16 | infrastructure-only | read-only |
